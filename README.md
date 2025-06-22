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


## 3. 클라이언트 구성
client 폴더내 README.md 참조

## 4. 라우터 구성
router 폴더내 README.md 참조

## 5. 마스터 구성
master 폴더내 README.md 참조

## 6. 워커 구성
worker 폴더내 README.md 참조
