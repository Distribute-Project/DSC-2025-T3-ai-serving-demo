import "./App.css";
import UploadFile from "./UploadFile";
import Compute from "./Compute";
import CheckStatus from "./CheckStatus";
import DeleteFile from "./DeleteFile";

function App() {
  return (
    <div>
      <h1>파일 저장</h1>
      <UploadFile />
      <h1>연산</h1>
      <Compute />
      <h1>파일 삭제</h1>
      <DeleteFile />
      <h1>결과 확인</h1>
      <CheckStatus />
    </div>
  );
}

export default App;
