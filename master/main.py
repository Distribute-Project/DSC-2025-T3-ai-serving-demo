import time
import json
import pika
import pymysql
import random
import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build

master_id = ''

config = {}

def get_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
        # print(config)
    return config

def msg_decode(body):
    try:
        msg = json.loads(body.decode('utf-8'))
        return msg
    except json.JSONDecodeError as e:
        print(f"❌ JSON 디코딩 오류: {e}")
        return None

def connect_and_consume(channel,master_id,curs):
    """RabbitMQ에 연결하고 메시지 소비 시작"""

    def save_req(job_id,worker_num,curs):  # 복구 시나리오 적용 완료
        # job_id로 검색하여 데이터 조회
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        # print(job_info)
        data = json.loads(job_info['data'])
        # print(data)
        model_id = 0
        if 'model_id' in data.keys():
            model_id = data['model_id']
        else:
            # ai_model 테이블에 model_id에 없는 랜덤숫자 생성 Unsigned BigInt 범위에서 
            model_id = random.randint(1,9007199254740991)
            while True:
                sql = "SELECT model_id FROM ai_model WHERE model_id = %s"
                curs.execute(sql, (model_id,))
                row = curs.fetchone()
                if row is None:
                    break
                model_id = random.randint(1, 9007199254740991)
            print('model_id : ',model_id)

            data['model_id'] = model_id
            sql = f'UPDATE job SET data = \'{json.dumps(data)}\' WHERE id = {job_id};'
            curs.execute(sql)
            conn.commit()

        sql = f'SELECT id FROM ai_model WHERE model_id = {model_id};'
        curs.execute(sql)
        rows = curs.fetchall()
        for i in range(worker_num-len(rows)):
            sql = f'INSERT INTO ai_model (model_id) VALUES ({model_id});'
            curs.execute(sql)
            conn.commit()

        if job_info['worker'] is None:

            sql = "SELECT * FROM worker WHERE is_online = 1 AND free_space > %s ORDER BY free_space DESC LIMIT %s"
            curs.execute(sql, (data['size'], worker_num))
            rows = curs.fetchall()
            
            if len(rows) < worker_num:
                # 할당할 수 있는 worker가 부족하면 job state 0(실패)로 변경
                result = "할당할 수 있는 worker가 부족합니다."
                print('job_id : ',job_id,result)

                # ai_model 테이블에서 model_id 삭제
                sql = f'DELETE FROM ai_model WHERE model_id = {model_id};'
                curs.execute(sql)
                sql = f'UPDATE job SET result = \'{{"message":"{result}"}}\', state = 0 WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
                
            else:
                workers = {}
                for i in range(worker_num):
                    workers[f'worker{rows[i]["id"]}'] = -2
                print(workers)
                sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                curs.execute(sql)
                conn.commit()
                for i in range(worker_num):
                    # rabbitmq에 worker_id로 임시파일 id 전송 // 구현 해야됨 
                    print(f"worker{rows[i]['id']} 저장 명령 전송") 
                    
                    channel.basic_publish(
                        exchange='save',
                        routing_key=f"worker{rows[i]['id']}.save.req",
                        body=f'{{"job_id":{job_id}}}'
                    )
                    workers[f'worker{rows[i]["id"]}'] = -1
                    print(workers)
                    sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                    curs.execute(sql)
                    conn.commit()

        else:
            workers = json.loads(job_info['worker'])
            for worker, val in workers.items():
                if val == -2:
                    channel.basic_publish(
                        exchange='save',
                        routing_key=f"{worker}.save.req",
                    body=f'{{"job_id":{job_id}}}'
                    )
                    workers[worker] = -1
                    sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
                    curs.execute(sql)
                    conn.commit()

    def compute_req(job_id,worker_num,curs):  # 복구 시나리오 적용 완료
        # job_id로 검색하여 데이터 조회
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        # print(job_info)
        data = json.loads(job_info['data'])
        # print(data)

        if job_info['worker'] is None:
            # 모델 아이디로 검색하여 worker_id 조회 하고 worker 테이블에서 검색하여 온라인 상태인 worker 중 가장 큐가 적은 워커에게 전달
            sql = "SELECT w.id, w.queue FROM worker w, ai_model a WHERE w.id = a.worker_id and model_id = %s order by w.queue LIMIT %s;"
            curs.execute(sql, (data['model_id'],worker_num)) 
            conn.commit()
            rows = curs.fetchall()
            # print(rows)

            if len(rows) == 0:
                # 모델 아이디로 검색하여 존재하는 모델이 없으면 job state 0(실패)로 변경
                result = "할당할 수 있는 worker가 부족합니다."
                print('job_id : ',job_id,result)
                sql = f'UPDATE job SET result = \'{{"message":"{result}"}}\', state = 0 WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
                
            else:
                workers = {}
                for row in rows:
                    workers[f'worker{row["id"]}'] = -2
                print(workers)
                sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                print(sql)
                curs.execute(sql)
                conn.commit()
                for row in rows:
                    print(f"worker{row['id']} 계산 명령 전송")
                    channel.basic_publish(
                        exchange='compute',
                        routing_key=f"worker{row['id']}.compute.req",
                        body=f'{{"job_id":{job_id}}}'
                    )
                    workers[f'worker{row["id"]}'] = -1
                    print(workers)
                    sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                    curs.execute(sql)
                    conn.commit()
        else:
            workers = json.loads(job_info['worker'])
            for worker, val in workers.items():
                if val == -2:
                    channel.basic_publish(
                        exchange='compute',
                        routing_key=f"{worker}.compute.req",
                        body=f'{{"job_id":{job_id}}}'
                    )
                    workers[f'worker{row["id"]}'] = -1
                    print(workers)
                    sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                    print(sql)
                    curs.execute(sql)
                    conn.commit()

    def delete_req(job_id, curs):
        # job_id로 검색하여 데이터 조회
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        if job_info is None or job_info['state'] != -1:
            return
        # print(job_info)
        data = json.loads(job_info['data'])
        # print(data)

        # ai_model 테이블에서 model_id 를 갖고 있는 worker_id 조회
        sql = "SELECT worker_id FROM ai_model WHERE model_id = %s;"
        curs.execute(sql, (data['model_id'],))
        rows = curs.fetchall()
        if len(rows) == 0:
            print(f'job_id {job_id} not found in ai_model')
            return
        worker_ids = [row['worker_id'] for row in rows]
        print(f'worker_ids : {worker_ids}')

        # 워커 온라인 여부 조회
        sql = "SELECT id FROM worker WHERE is_online = 0 AND id IN %s;"
        curs.execute(sql, (tuple(worker_ids),))
        rows = curs.fetchall()
        if len(rows) != 0:
            print(f'worker_ids {worker_ids} are not online')
            # job state 0(실패)로 변경
            result = "할당할 수 있는 worker가 부족합니다."
            print('job_id : ',job_id,result)
            sql = f'UPDATE job SET result = \'{{"message":"{result}"}}\', state = 0 WHERE id = {job_id};'
            curs.execute(sql)
            conn.commit()
            return
        # 워커가 모두 온라인 상태인 경우
        workers = {}
        if job_info['worker'] is None:
            for worker_id in worker_ids:
                workers[f'worker{worker_id}'] = -2
            print(workers)
            sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
            curs.execute(sql)
            conn.commit()
        else:
            workers = json.loads(job_info['worker'])

        for worker,state in workers.items():
            print(f"{worker} 상태 : {state}")
            if state == -2:
                print(f"{worker} 삭제 명령 전송")
                channel.basic_publish(
                    exchange='delete',
                    routing_key=f"{worker}.delete.req",
                    body=f'{{"job_id":{job_id}}}'
                )
                workers[f'{worker}'] = -1
                print(workers)
                sql = f"UPDATE job SET worker ='{json.dumps(workers)}'  WHERE id = {job_id};"
                curs.execute(sql)
                conn.commit()


        

    def save_res(job_id,worker_id,result, curs): # 복구 시나리오 적용 완료
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        if job_info is None or job_info['state'] != -1:
            return
        # print(job_info)
        data = json.loads(job_info['data'])
        # print(data)
        workers = json.loads(job_info['worker'])

        if f'worker{worker_id}' not in workers.keys():
            print('worker_id not in data["worker"].keys()')
            return
        elif workers[f'worker{worker_id}'] == 1:
            sql = f'SELECT * FROM ai_model WHERE model_id = {data["model_id"]} and worker_id = {worker_id};' # 이미 배정된 worker 가 있는지 ai_model 에서 검색
            curs.execute(sql)
            rows = curs.fetchall()
            if len(rows) == 0: # 이미 배정된 worker 가 없으면 ai_model 테이블에서 model_id 업데이트
                # ai_model 테이블에서 model_id 업데이트
                sql = f'UPDATE ai_model SET worker_id = {worker_id} WHERE model_id = {data["model_id"]} and worker_id is null limit 1;'
                curs.execute(sql)
                conn.commit()
            print('worker_id already in data["worker"].keys()')
            return
        elif -2 in workers.values():
            # workers에서 value 가 2인 worker 찾아내기
            for worker, val in workers.items():
                if val == -2:
                    channel.basic_publish(  
                        exchange='save',
                        routing_key=f"{worker}.save.req",
                        body=f'{{"job_id":{job_id}}}'
                    )
                    workers[worker] = -1
                    sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
                    curs.execute(sql)
                    conn.commit()
                    break

        # 워커 상태 업데이트
        workers[f'worker{worker_id}'] = result
        sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
        curs.execute(sql)
        conn.commit()
        
        # 작업이 끝났는지 여부 체크
        if result == 1:
            sql = f'SELECT * FROM ai_model WHERE model_id = {data["model_id"]} and worker_id = {worker_id};'
            curs.execute(sql)
            rows = curs.fetchall()
            if len(rows) == 0:
                # ai_model 테이블에서 model_id 업데이트
                sql = f'UPDATE ai_model SET worker_id = {worker_id} WHERE model_id = {data["model_id"]} and worker_id is null limit 1;'
                curs.execute(sql)
                conn.commit()

            sql = f'SELECT * FROM ai_model WHERE model_id = {data["model_id"]} and worker_id is null;'
            curs.execute(sql)
            rows = curs.fetchall()
            if len(rows) == 0:
                sql = f'UPDATE job SET result = \'{{"result":{data["model_id"]}, "message":"저장 완료"}}\', state = 1 WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
        else: # 저장 실패 시 다른 워커에게 작업 전달
            # 새로운 워커로 변경하는 코드 작성

            worker_num = len(workers)
            # 다시 검색
            sql = "SELECT id FROM worker WHERE is_online = 1 AND free_space > %s ORDER BY free_space DESC LIMIT %s"
            curs.execute(sql, (data['size'], worker_num+1))
            rows = []

            # rows 에서 workers에 있는 워커 제외
            for row in curs.fetchall():
                if f'worker{row["id"]}' not in workers.keys():
                    rows.append(row)

            print('rows : ',rows)
            print('workers : ',workers)

            if len(rows) == 0:
                result = "할당할 수 있는 worker가 부족합니다."
                sql = f'DELETE FROM ai_model WHERE model_id = {data["model_id"]};'
                curs.execute(sql)
                print('job_id : ',job_id,result)
                sql = f'UPDATE job SET result = \'{{"message":"{result}"}}\', state = 0 WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
            else:
                row=rows[0]
                workers[f'worker{row["id"]}'] = -2
                sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
                channel.basic_publish(  
                    exchange='save',
                    routing_key=f"worker{row['id']}.save.req",
                    body=f'{{"job_id":{job_id}}}'
                )
                workers[f'worker{row["id"]}'] = -1
                sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
    
    def compute_res(job_id,worker_id,result, curs):  # 복구 시나리오 적용 완료
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        # print(job_info)
        if job_info['worker'] is None or job_info['state'] != -1:
            print('이미 완료된 작업')
            return
        data = json.loads(job_info['data'])
        # print(data)

        # 워커 상태 업데이트
        workers = json.loads(job_info['worker'])
        if f'worker{worker_id}' not in workers.keys():
            print('worker_id not in data["worker"].keys()')
            return
        elif workers[f'worker{worker_id}'] != -1:
            print('이미 완료된 작업')
            return
        if result is None:
            workers[f'worker{worker_id}'] = 0
        else:
            workers[f'worker{worker_id}'] = 1
        
        sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
        curs.execute(sql)
        conn.commit()
        
        # 작업이 끝났는지 여부 체크
        if result is not None:
            sql = f'UPDATE job SET result = \'{{"result":{result}, "message":"계산 완료"}}\', state = 1 WHERE id = {job_id};'
            curs.execute(sql)
            conn.commit()
            print('job_id : ',job_id,'계산 요청 성공')
        else: # 계산 실패 시 다른 워커에게 작업 전달
            # workers.values() 가 전부 0 이면 실패 처리
            fail = True
            for val in workers.values():
                if val != 0:
                    fail = False
                    break
            if fail:
                sql = f'UPDATE job SET result = \'{{"message":"계산 실패"}}\', state = 0 WHERE id = {job_id};'
                curs.execute(sql)
                conn.commit()
                print('job_id : ',job_id,'계산 요청 실패')
    
    def delete_res(job_id,worker_id,result, curs):  # 복구 시나리오 적용 완료
        sql = "SELECT * FROM job WHERE id = %s"
        curs.execute(sql, (job_id,))
        job_info = curs.fetchone()
        if job_info is None or job_info['state'] != -1:
            return
        workers = json.loads(job_info['worker'])
        if f'worker{worker_id}' not in workers.keys():
            print('worker_id not in data["worker"].keys()')
            return
        elif workers[f'worker{worker_id}'] != -1:
            print('이미 완료된 작업')
            return
        if result == 0:
            workers[f'worker{worker_id}'] = 0
            sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
            curs.execute(sql)
            sql = f'UPDATE job SET result = \'{{"message":"삭제 실패"}}\', state = 0 WHERE id = {job_id};'
            curs.execute(sql)
            conn.commit()
            print('job_id : ',job_id,'삭제 요청 실패')
            return
        elif result == 1:
            is_end = True
            workers[f'worker{worker_id}'] = 1
            # workers.values() 가 전부 1 이면 삭제 완료
            for val in workers.values():
                if val != 1:
                    is_end = False
                    break
            if is_end:
                sql = f'UPDATE job SET result = \'{{"message":"삭제 완료"}}\', state = 1 WHERE id = {job_id};'
                curs.execute(sql)
            sql = f'UPDATE job SET worker = \'{json.dumps(workers)}\' WHERE id = {job_id};'
            curs.execute(sql)
            model_id = json.loads(job_info['data'])['model_id']
            # ai_model_table에서 model_id가 job_info['data']['model_id']이고 worker_id가 worker_id인 레코드 삭제
            sql = f'DELETE FROM ai_model WHERE model_id = {model_id} and worker_id = {worker_id};'
            curs.execute(sql)
            conn.commit()
            

    def call_back(ch, method, properties, body):
        global temp
        msg = msg_decode(body)
        print(msg)
        print(method.routing_key)
        if msg is None:
            ch.basic_nack(delivery_tag=method.delivery_tag)
            print("router 에게 저장실패 메세지 전송")
        else:
            if method.routing_key.endswith(".save.req"):
                # 저장 요청 처리
                print('저장 요청 처리')
                save_req(msg['job_id'], config['worker_num'], curs)

            elif method.routing_key.endswith(".compute.req"):
                # 계산 요청 처리
                print('계산 요청 처리')
                compute_req(msg['job_id'], config['worker_num'], curs)
            elif method.routing_key.endswith(".delete.req"):
                # 삭제 요청 처리
                print('삭제 요청 처리')
                delete_req(msg['job_id'], curs)
            elif method.routing_key.endswith(".save.res"):
                # 저장 결과 처리
                print('저장 결과 처리')
                save_res(msg['job_id'],msg['worker_id'],msg['result'] ,curs)
            elif method.routing_key.endswith(".compute.res"):
                # 계산 결과 처리
                print('계산 결과 처리')
                compute_res(msg['job_id'],msg['worker_id'],msg['result'] ,curs)
            elif method.routing_key.endswith(".delete.res"):
                # 삭제 결과 처리
                print('삭제 결과 처리')
                delete_res(msg['job_id'],msg['worker_id'],msg['result'], curs)
        print('===============================================')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    channel.basic_consume(queue=master_id,
                          on_message_callback=call_back,
                          auto_ack=False)
    

    print(f" [*] 연결됨: {config['rabbitmq_address']} — 메시지 수신 대기 중...")
    channel.start_consuming()

def update_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_master_id():
    # 랜덤 master_id 생성 및 중복 확인
    while True:
        # Unsigned BigInt 범위에서 랜덤 ID 생성
        random_id = random.randint(1, 9007199254740991)
        
        # master 테이블에서 ID 존재 여부 확인
        sql = "SELECT id FROM master WHERE id = %s"
        curs.execute(sql, (random_id,))
        row = curs.fetchone()
        
        # ID가 존재하지 않으면
        if row is None:
            # 새 master 레코드 추가
            sql = "INSERT INTO master (id,is_online,queue) VALUES (%s,%s,%s)"
            curs.execute(sql, (random_id,1,0))
            conn.commit()                
            return 'master'+str(random_id)


config = get_config()
# ====================  db 설정 ====================
conn = None
curs = None
while True:
    try:
        conn = pymysql.connect(host=config['mysql_address'].split(':')[0], user=config['mysql_user'],password=config['mysql_password'], db=config['db'])
        curs = conn.cursor(pymysql.cursors.DictCursor)
        curs.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        break
    except pymysql.MySQLError as e:
        print(f"⚠️ MySQL 연결 오류: {e}")
        print("⏳ 5초 후 다시 연결 시도...")
        time.sleep(5)
    
# ====================  master_id 설정 ====================
master_id = config['master_id']

# db에 마스터 아이디가 있는지 확인
if master_id == '':
    master_id = get_master_id()
    print(master_id)
    config['master_id'] = master_id
    update_config(config)
else:
    sql = "SELECT id FROM master WHERE id = %s"
    curs.execute(sql, (int(master_id[6:]),))
    row = curs.fetchone()
    if row is None:
        sql = "INSERT INTO master (id,is_online,queue) VALUES (%s,%s,%s)"
        curs.execute(sql, (int(master_id[6:]),1,0))
        conn.commit()
sql = f"UPDATE master SET is_online = 1 WHERE id = {master_id[6:]};"
curs.execute(sql)
conn.commit()

temp = 0
# ====================================================================

credentials = pika.PlainCredentials(config['rabbitmq_id'], config['rabbitmq_password'])
host, port = config['rabbitmq_address'].split(':')
parameters = pika.ConnectionParameters(
    host=host,
    port=port,
    virtual_host='/',
    credentials=credentials,
    heartbeat=0,
    blocked_connection_timeout=30
)

connection = None
channel = None
while True:
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # channel.exchange_declare(exchange='amq.topic', exchange_type='topic')
        channel.queue_declare(queue=master_id,durable=True)
        channel.queue_bind(exchange='save', queue=master_id, routing_key=f"{master_id}.save.req")
        channel.queue_bind(exchange='compute', queue=master_id, routing_key=f"{master_id}.compute.req")
        channel.queue_bind(exchange='delete', queue=master_id, routing_key=f"{master_id}.delete.req")
        channel.queue_bind(exchange='save', queue=master_id, routing_key=f"{master_id}.save.res")
        channel.queue_bind(exchange='compute', queue=master_id, routing_key=f"{master_id}.compute.res")
        channel.queue_bind(exchange='delete', queue=master_id, routing_key=f"{master_id}.delete.res")
        print(f"✅ RabbitMQ 연결 성공: {config['rabbitmq_address']}")
        break
    except pika.exceptions.AMQPConnectionError as e:
        print(f"⚠️ RabbitMQ 연결 오류: {e}")
        print("⏳ 5초 후 다시 연결 시도...")
        time.sleep(5)
    
# 자동 재연결 루프
while True:
    try:

        connect_and_consume(channel,master_id,curs)
        
    except (pika.exceptions.AMQPConnectionError) as e:
        print(f"⚠️ 연결 끊김 또는 오류 발생: {e}")
        print("⏳ 5초 후 다시 연결 시도...")
        time.sleep(5)
        config = get_config()
    except pymysql.MySQLError as e:
        print(f"⚠️ MySQL 오류 발생: {e}")
        print("⏳ 5초 후 다시 연결 시도...")
        time.sleep(5)
        config = get_config()
        conn = pymysql.connect(host=config['mysql_address'].split(':')[0], user=config['mysql_user'],password=config['mysql_password'], db=config['db'])
        curs = conn.cursor(pymysql.cursors.DictCursor)
        curs.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    except KeyboardInterrupt as e:
        print("프로그램 종료")
        break
    except Exception as e:
        print(traceback.format_exc())
        print(f"⚠️ 예기치 않은 오류 발생: {e}")
        break

# is_online 상태 업데이트
sql = f"UPDATE master SET is_online = 0 WHERE id = {master_id[6:]};"
curs.execute(sql)
conn.commit()
# RabbitMQ 연결 종료
channel.stop_consuming()
channel.close()
connection.close()
# MySQL 연결 종료
curs.close()
conn.close()