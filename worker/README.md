# Distributed ML Worker

분산 머신러닝 시스템의 워커 노드입니다. RabbitMQ를 통해 작업을 수신하고, PyTorch 모델을 사용하여 추론을 수행합니다.

## 시스템 요구사항

- **Python**: 3.11
- **CUDA**: 12.4
- **GPU**: NVIDIA GPU (권장)
- **운영체제**: Windows/Linux/macOS

## 설치 방법

### 1. 저장소 클론
```bash
git clone <repository-url>
cd worker
```

### 2. Python 가상환경 생성 (권장)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 의존성 설치

#### 일반 패키지 설치
```bash
pip install pika PyMySQL gdown
```

#### PyTorch 설치 (CUDA 12.4)
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
```

### 4. 설정 파일 생성
프로젝트 루트에 `config.json` 파일을 작성하세요:

```json
{
    "rabbitmq": {
        "host": "your-rabbitmq-host",
        "port": 5672,
        "user": "testuser",
        "password": "testuserpw"
    },
    "mysql": {
        "host": "your-mysql-host",
        "port": 3306,
        "user": "your-username",
        "password": "testuser",
        "database": "testuserpw"
    },
    "worker": {
        "id": 1,
        "status_update_interval": 10,
        "model_dir": "models",
        "max_cached_models": 3
    }
}
```

## 실행 방법

```bash
python main.py
```

## 주요 기능

- **모델 저장**: Google Drive에서 PyTorch 모델 다운로드
- **추론 수행**: 캐시된 모델을 사용하여 빠른 추론
- **상태 관리**: 워커 상태를 데이터베이스에 업데이트
- **자동 복구**: 연결 실패 시 자동 재시도
- **GPU 지원**: CUDA/MPS 자동 감지 및 활용

## 디렉토리 구조

```
worker/
├── main.py              # 메인 워커 애플리케이션
├── config.json          # 설정 파일
├── requirements.txt     # Python 의존성
├── models/             # 다운로드된 모델 저장소
└── README.md           # 이 파일
```

## 설정 옵션

### Worker 설정
- `id`: 워커 고유 식별자
- `status_update_interval`: 상태 업데이트 간격 (초)
- `model_dir`: 모델 파일 저장 디렉토리
- `max_cached_models`: 메모리에 캐시할 최대 모델 수

### 연결 설정
- RabbitMQ와 MySQL 연결 정보 설정
- 자동 재연결 및 에러 처리 지원

## 문제 해결

### CUDA 관련 문제
```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 지원 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 연결 문제
- RabbitMQ와 MySQL 서버가 실행 중인지 확인
- 방화벽 설정 확인
- 설정 파일의 연결 정보 확인

### 메모리 부족
- `max_cached_models` 값을 줄여보세요
- GPU 메모리가 부족한 경우 더 작은 배치 크기 사용

## 로그 확인

워커는 다음과 같은 로그를 출력합니다:
- `[ALERT]`: 연결 실패 및 재시도
- `[ERROR]`: 오류 발생
- `[OFFLINE]`: 워커 종료 시
- `[RESULT]`: 추론 결과

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.