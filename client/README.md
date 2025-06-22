# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# 실행방법
### Requirement
For building and running the application you need
- Node.js
- Npm

### Installation and Running
1. Clone the repository
    ```Bash
    $ git clone https://github.com/Distribute-Project/client.git
    ```
2. Install NPM packages
    ```bash
    $ npm i
    ```
3. Enter the environment variables in ```.env```
    ```bash
    VITE_HOST = {server address}
    # VITE_NGROK_HASH = {ngrok 16 hash code in url}  # ngrok을 사용해서 실행 시
    ```
4. 프로그램 실행
    ```Bash
    $ npm run dev
    ```
