import pika
import json
import pymysql.cursors
import torch
import os
import threading
import time
import shutil
import pymysql
import gdown
import sys
import gc
import signal
from datetime import datetime

# ========== CONFIG LOADING ==========
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] config.json file not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in config.json: {e}")
        sys.exit(1)

config = load_config()
# ========== CONFIG ==========
RABBITMQ_HOST = config["rabbitmq"]["host"]
RABBITMQ_PORT = config["rabbitmq"]["port"]
RABBITMQ_USER = config["rabbitmq"]["user"]
RABBITMQ_PASS = config["rabbitmq"]["password"]

MYSQL_USER = config["mysql"]["user"]
MYSQL_PASS = config["mysql"]["password"]
MYSQL_HOST = config["mysql"]["host"]
MYSQL_PORT = config["mysql"]["port"]
MYSQL_DB = config["mysql"]["database"]

STATUS_UPDATE_INTERVAL = config["worker"]["status_update_interval"]
MODEL_DIR = config["worker"]["model_dir"]
MAX_CACHED_MODELS = config["worker"]["max_cached_models"]
WORKER_ID = config["worker"]["id"]
os.makedirs(MODEL_DIR, exist_ok=True)

device = None
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

MODELS = {} #for GPU cashing
QUEUE_NAME = f"worker{WORKER_ID}"
    
# ========== HEALTH ALERT ==========
def check_and_alert(component):
    print(f"[ALERT] {component} connection failed. Retrying...")

# ========== DB CONNECTION ==========
def get_db_connection():
    while True:
        try:
            return pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        except Exception as e:
            check_and_alert("MySQL")
            time.sleep(5)
    
# ========== CLEANUP ==========
def mark_worker_offline():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE worker SET is_online = 0 WHERE id = %s", (WORKER_ID,))
        conn.close()
        print(f"[OFFLINE] Worker {WORKER_ID} marked offline in DB")
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")

def handle_exit(signum, frame):
    mark_worker_offline()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# ========== HELPER FUNCTIONS ==========
def get_one_sample(x):
    while isinstance(x, (list, tuple)) and len(x) > 0:
        x = x[0]
    return x

def get_disk_info():
    disk = shutil.disk_usage("/")
    return disk.total, disk.free

def get_job_info(job_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT data, master FROM job WHERE id = %s", (job_id,))
        row = cursor.fetchone()
    if not row:
        raise ValueError(f"Job ID {job_id} not found")

    data = row['data']
    if isinstance(data, str):
        data = json.loads(data)
    
    master_raw = row['master']
    if isinstance(master_raw, str):
        master_data = json.loads(master_raw)
        master_id = master_data.get('master')
    elif isinstance(master_raw, dict):
        master_id = master_raw.get('master')
    else:
        master_id = master_raw  # assume int
        
    return data, master_id
            
def insert_or_update_worker():
    while True:
        try:
            total, free = get_disk_info()
            gpu_count = torch.mps.device_count() if hasattr(torch, 'mps') else 0
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO worker (id, is_online, queue, gpu, storage, free_space, created_at, updated_at)
                    VALUES (%s, 1, 0, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        is_online = 1,
                        queue = 0,
                        gpu = VALUES(gpu),
                        storage = VALUES(storage),
                        free_space = VALUES(free_space),
                        updated_at = VALUES(updated_at);
                """, (WORKER_ID, gpu_count, total, free, now, now))
            conn.close()
            break
        except Exception:
            check_and_alert("DB Insert Worker")
            time.sleep(5)

def send_result_to_master(exchange, routing_key, job_id, result):
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
                heartbeat=30
            ))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)
            body = json.dumps({"job_id": job_id, "result": result, "worker_id": WORKER_ID})
            channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body)
            connection.close()
            break
        except Exception:
            check_and_alert("RabbitMQ Send")
            time.sleep(5)

# ========== INFERENCE ==========
def run_inference(ai_model_id, input_data):
    error_count = 0
    while True:
        try:            
            if ai_model_id in MODELS.keys():
                MODELS[ai_model_id].eval()
                 
                sample = get_one_sample(input_data)
                print(type(sample))
                
                tensor_input = torch.tensor(input_data).to(device)
                
                if isinstance(sample, float):
                    tensor_input.to(dtype=torch.float32)
                elif isinstance(sample, int):
                    tensor_input.to(dtype=torch.int8)
                else:
                    raise TypeError(f"지원하지 않는 타입: {type(sample)}")
                
                with torch.no_grad():
                    output = MODELS[ai_model_id](tensor_input)
                    if isinstance(output, tuple):
                        output = [o.cpu().tolist() if isinstance(o, torch.Tensor) else o for o in output]
                    elif isinstance(output, torch.Tensor):
                        output = output.cpu().tolist()
            else:    
                path = os.path.join(MODEL_DIR, f"{ai_model_id}.pt")
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Model {ai_model_id} not found")
                
                if len(MODELS.items()) > MAX_CACHED_MODELS:
                    del MODELS.keys()[-1]
                    gc.collect()
                    torch.cuda.empty_cache()
                    
                MODELS[ai_model_id] = torch.jit.load(path, map_location=device)
                MODELS[ai_model_id].eval()
                
                sample = get_one_sample(input_data)
                tensor_input = torch.tensor(input_data).to(device)
                
                if isinstance(sample, float):
                    tensor_input.to(dtype=torch.float32)
                elif isinstance(sample, int):
                    tensor_input.to(dtype=torch.int8)
                else:
                    raise TypeError(f"지원하지 않는 타입: {type(sample)}")
                
                with torch.no_grad():
                    output = MODELS[ai_model_id](tensor_input)
                    if isinstance(output, tuple):
                        output = [o.cpu().tolist() if isinstance(o, torch.Tensor) else o for o in output]
                    elif isinstance(output, torch.Tensor):
                        output = output.cpu().tolist()

            return output
        
        except Exception as e:
            print(e)
            error_count += 1
            check_and_alert("Inference")
            if error_count >= 3:
                return 0
            time.sleep(5)

# ========== JOB HANDLERS ==========
def handle_save_request(job_id):
    try:
        data, master_id = get_job_info(job_id)
            
        url = data['file_url']
        size = data['size']
        model_id = data['model_id']
        free = get_disk_info()[1]

        if size > free:
            print(f"[ERROR] Not enough disk space: required {size}, available {free}")
            send_result_to_master("save", f"master{master_id}.save.res", job_id, 0)
            return 0

        time.sleep(5)
        save_path = os.path.join(MODEL_DIR, f"{model_id}.pt")
        gdown.download(url, save_path, quiet=False)
    
        send_result_to_master("save", f"master{master_id}.save.res", job_id, 1)
        return 1
    
    except Exception as e:
        check_and_alert("Handle Save Request")
        print(f"[ERROR] Save request failed: {e}")
        send_result_to_master("save", f"master{master_id}.save.res", job_id, 0)
        time.sleep(5)
        return 0

def handle_compute_request(job_id):
    try:
        data, master_id = get_job_info(job_id)

        model_id = data['model_id']
        input_data = data['input']
        
        try:
            result = run_inference(model_id, input_data)
            if result == 0: 
                print("[ERROR] Inference failed, sending None result")
                send_result_to_master("compute", f"master{master_id}.compute.res", job_id, None)
                return 0
            print(f"[RESULT] Inference result: {result}")
            send_result_to_master("compute", f"master{master_id}.compute.res", job_id, result)
            return 1
        
        except Exception as e:
            check_and_alert("Handle Compute Request")
            print(f"[ERROR] Inference failed: {e}")
            send_result_to_master("compute", f"master{master_id}.compute.res", job_id, None)
            time.sleep(5)
            return 0

    except Exception as e:
        check_and_alert("Handle Compute Request")
        print(f"[ERROR] Compute request failed: {e}")
        send_result_to_master("compute", f"master{master_id}.compute.res", job_id, None)
        time.sleep(5)
        return 0

def handle_delete_request(job_id):
    try:
        data, master_id = get_job_info(job_id)
        
        model_id = data.get("model_id")
        file_path = os.path.join(MODEL_DIR, f"{model_id}.pt")
        
        #이미 없는 파일을 요청받아도 성공 처리하는 걸로
        os.remove(file_path)
        send_result_to_master("delete", f"master{master_id}.delete.res", job_id, 1)
        return 1
    except FileNotFoundError:
        print(f"[WARN] File not found for deletion: {file_path}")
        send_result_to_master("delete", f"master{master_id}.delete.res", job_id, 1)
        return 1
    except Exception as e:
        print(e)
        check_and_alert("Handle Delete Request")
        send_result_to_master("delete", f"master{master_id}.delete.res", job_id, 0)
        time.sleep(5)
        return 0
     
# ========== STATUS REPORTING ==========
def start_status_reporting():
    def report():
        while True:
            try:
                total, free = get_disk_info()
                gpu_count = torch.mps.device_count() if hasattr(torch, 'mps') else 0
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE worker SET
                            is_online = 1,
                            free_space = %s,
                            storage = %s,
                            gpu = %s,
                            updated_at = %s
                        WHERE id = %s
                    """, (free, total, gpu_count, now, WORKER_ID))
                conn.close()
                print(f"[STATUS] Updated: worker_id={WORKER_ID}, free_space={free // (1024*1024)}MB, storage={total}, gpu={gpu_count}, updated_at={now}")
            except Exception as e:
                print(f"[ERROR] Status update failed: {e}")
            time.sleep(STATUS_UPDATE_INTERVAL)

    threading.Thread(target=report, daemon=True).start()

# ========== CONSUMER ==========
def start_worker_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=0
    ))
    channel = connection.channel()
    channel.exchange_declare(exchange='save', exchange_type='direct', durable=True)
    channel.exchange_declare(exchange='compute', exchange_type='direct', durable=True)
    channel.exchange_declare(exchange='delete', exchange_type='direct', durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(queue=QUEUE_NAME, exchange='save', routing_key=f"worker{WORKER_ID}.save.req")
    channel.queue_bind(queue=QUEUE_NAME, exchange='compute', routing_key=f"worker{WORKER_ID}.compute.req")
    channel.queue_bind(queue=QUEUE_NAME, exchange='delete', routing_key=f"worker{WORKER_ID}.delete.req")
    print(f"[*] Listening on queue: {QUEUE_NAME}")

    def callback(ch, method, properties, body):
        try:
            result = -1
            job_id = json.loads(body).get("job_id")
            routing_key = method.routing_key
            print(job_id, routing_key)
            if ".save." in routing_key:
                result = handle_save_request(job_id)
                print("handle save reuslt : ", result)
            elif ".compute." in routing_key:
                result = handle_compute_request(job_id)
                print("handle compute reuslt : ", result)
            elif ".delete." in routing_key:
                result = handle_delete_request(job_id)
                print("delete request result : ", result)
            else:
                print(f"[WARN] Unknown routing key: {routing_key}")
        except Exception as e:
            print(f"[ERROR] Message handling failed: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, auto_ack=False, on_message_callback=callback)
    channel.start_consuming()

# ========== MAIN ==========
if __name__ == "__main__":
    insert_or_update_worker()
    start_status_reporting()
    start_worker_consumer()
