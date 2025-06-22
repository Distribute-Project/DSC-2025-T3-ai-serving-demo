# Master Node - 분산 처리 시스템

분산 처리 시스템의 Master Node 구현입니다. RabbitMQ와 MySQL을 사용하여 워커 노드들과 통신하고 작업을 관리합니다.

## 환경 요구사항

- Python 3.12.8
- RabbitMQ Server
- MySQL Server

## 설치 및 설정

### 1. Python 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 구성

[config.json](config.json) 파일을 프로젝트 요구사항에 맞게 수정하세요:

```json
{
    "master_id": "master1",
    "rabbitmq_address": "127.0.0.1:5672",
    "rabbitmq_manager_address": "127.0.0.1:15672",
    "rabbitmq_id": "testuser",
    "rabbitmq_password": "testuserpw",
    "mysql_address": "127.0.0.1",
    "mysql_port": "3306",
    "mysql_user": "testuser",
    "mysql_password": "testuserpw",
    "db": "db",
    "worker_num": 2 
}
```

#### 설정 항목 설명

- `master_id`: 마스터 노드의 고유 식별자
- `rabbitmq_address`: RabbitMQ 서버 주소 (host:port)
- `rabbitmq_manager_address`: RabbitMQ 관리 인터페이스 주소
- `rabbitmq_id`: RabbitMQ 사용자명
- `rabbitmq_password`: RabbitMQ 비밀번호
- `mysql_address`: MySQL 서버 주소
- `mysql_port`: MySQL 포트 (기본값: 3306)
- `mysql_user`: MySQL 사용자명
- `mysql_password`: MySQL 비밀번호
- `db`: 사용할 데이터베이스 이름
- `worker_num`: 작업당 할당할 워커 수(실제로 실행하려면 설정한 워커 수 이상으로 워커노드를 실행시켜야합니다.)

## 실행 방법

### 1. 메인 프로세스 실행

```bash
python main.py
```

[main.py](main.py)는 다음 기능을 수행합니다:
- RabbitMQ 연결 및 메시지 처리
- 작업 요청 처리 (저장, 계산, 삭제)
- 워커 노드와의 통신 관리
- 데이터베이스 상태 관리

### 2. 정보 업데이트 프로세스 실행

별도 터미널에서:

```bash
python update_info.py
```

[update_info.py](update_info.py)는 다음 기능을 수행합니다:
- 주기적으로 RabbitMQ 큐 상태 모니터링
- 마스터 노드의 온라인 상태 및 큐 정보 업데이트
- 5초 간격으로 실행
