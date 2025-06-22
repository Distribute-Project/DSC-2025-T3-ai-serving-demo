# Guide
### Requirement
For building and running the application you need
- Node.js
- Npm

### Installation and Running
1. Clone the repository
    ```Bash
    $ git clone https://github.com/Distribute-Project/router.git
    ```
2. Install NPM packages
    ```bash
    $ npm i
    ```
3. Enter the environment variables in ```.env```
    ```bash
    # rabbitMQ
    RABBITMQ_ID = {testuser}
    RABBITMQ_PWD = {testuserpw}
    RABBITMQ_HOST = {your rabbitmq host}
    RABBITMQ_PORT = {your rabbitmq port}

    # Google Drive
    GOOGLE_APPLICATION_CREDENTIALS = {path of service_account.js}

    #DB (MySql)
    DB_HOST = {Database Host}
    DB_USER = {testuser}
    DB_PW = {testuserpw}
    DB_NAME = {db}
    ```
4. Run Program
    ```Bash
    # pm2 사용 시
    $ npx pm2 run index  # pm2로 라우터 실행
    $ npx pm2 log  # 로그 보기
    $ npx pm2 kill  # pm2로 실행 중인 작업 kill

    # pm2 없이 실행
    $ node index.js
    ```
