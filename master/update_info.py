import time
import pymysql
import requests
from requests.auth import HTTPBasicAuth
import json

TIME_INTERVAL = 5

# 설정 파일 로드
config = {}


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

while True:
    config = load_config()  
    master_id = config['master_id']
    if master_id != '':
        break
    print('waiting for master_id')
    time.sleep(TIME_INTERVAL)

# 데이터베이스 연결
conn = pymysql.connect(
    host=config['mysql_address'].split(':')[0],
    user=config['mysql_user'],
    password=config['mysql_password'],
    db=config['db']
)       

# 커서 생성
curs = conn.cursor(pymysql.cursors.DictCursor)

# 큐 확인
def check_queue(queue_name, vhost='/', user='guest', pwd='guest'):
    url = f'http://{config["rabbitmq_manager_address"]}/api/queues/{requests.utils.quote(vhost, safe="")}/{queue_name}'
    resp = requests.get(url, auth=HTTPBasicAuth(user, pwd))
    resp.raise_for_status()
    data = resp.json()
    count = data['messages_unacknowledged'] + data['messages_ready']
    print(f"Queue {queue_name} has {count} messages")
    return count

def update_db(master_id, count):
    only_id = int(master_id.split('master')[1])
    sql = "UPDATE master SET queue = %s, is_online = 1 WHERE id = %s;"
    curs.execute(sql, (count, only_id))
    print(f"Updated {master_id} queue count to {count}")
    conn.commit()



while True:
    try:
        count = check_queue(config['master_id'],user=config["rabbitmq_id"],pwd=config["rabbitmq_password"])
        update_db(config['master_id'], count)
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(TIME_INTERVAL)

curs.close()
conn.close()








