# DSC-2025-T3-ai-serving-demo
2025 분산시스템 및 컴퓨팅 프로젝트 

# 분산 프로젝트 실행가이드

## 1. RabbitMQ 설정
Docker를 이용하여 서버를 구성

docker run -d --hostname rabbit --name rabbitmq -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=adminpw -e RABBITMQ_DEFAULT_VHOST=/ rabbitmq:3.9-management

1.1 호스트 pc에서 127.0.0.1:15672 접속 후 admin / adminpw 로 로그인 (RabbitMQ 관리자 페이지)

1.2 Admin 탭에서 testuser 생성(Monitoring 태그 추가) 생성한 testuser에 Permissions, Topic Permissions 설정

1.3 Exchanges 탭에서 save, compute, delete 교환소 추가 (type: direct / Durability: Durable)

## 2. MySQL 설정
Docker를 이용하여 서버를 구성

docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=rootpwd -e MYSQL_DATABASE=db -e MYSQL_USER=testuser -e MYSQL_PASSWORD=testuserpw -p 3306:3306 mysql:8.0

2.1 DBMS를 이용하여 root / rootpwd 로그인

2.2 db_config 의 sql 쿼리 실행 (필요한 테이블 생성)

## 3. 구글 서비스 계정 생성

1. **Google Cloud 프로젝트 생성**  
   1.1. [Google Cloud Console](https://console.cloud.google.com/)에 접속  
   1.2. 새 프로젝트를 생성하거나 기존 프로젝트 선택  

2. **Drive API 활성화**  
   2.1. 좌측 메뉴에서 **API 및 서비스 ▶︎ 라이브러리** 클릭  
   2.2. “Google Drive API” 검색 후 **사용** 버튼 클릭  

3. **서비스 계정 생성 & 키 다운로드**  
   3.1. **API 및 서비스 ▶︎ 서비스 계정** 이동  
   3.2. **서비스 계정 만들기** 클릭  
   3.3. 이름 입력 → **완료**  
   3.4. 생성된 서비스 계정 클릭 → **키(Key)** 탭  
   3.5. **키 추가 ▶︎ 새 키 만들기** 클릭  
   3.6. **JSON** 형식 선택 후 **만들기** → `service_account.json` 파일 다운로드  

4. **공유할 폴더 생성 및 서비스 계정에 권한 부여**  
   4.1. [Google Drive](https://drive.google.com/) 접속  
   4.2. 왼쪽 상단 **새로 만들기 ▶︎ 폴더** 클릭 → 폴더명 입력 후 생성  
   4.3. 생성된 폴더 우클릭 ▶︎ **공유**  
   4.4. “사용자 및 그룹 추가”에 서비스 계정 이메일(예: `your-service-account@your-project.iam.gserviceaccount.com`) 입력  
   4.5. 권한을 **관리자(편집자)** 또는 **뷰어**로 설정 ▶︎ **보내기** 클릭  

## 4. 클라이언트 구성
client 폴더내 README.md 참조

## 5. 라우터 구성
router 폴더내 README.md 참조

## 6. 마스터 구성
master 폴더내 README.md 참조

## 7. 워커 구성
worker 폴더내 README.md 참조
