import { useState } from "react";

function Compute() {
  const [fileId, setFileId] = useState("");
  const [inputData, setInputData] = useState("");
  const [requestId, setRequestId] = useState(null);
  const [isInputError, setIsInputError] = useState(false);

  const handleRun = () => {
    setIsInputError(false);
    try {
      JSON.parse(inputData);
    } catch {
      setIsInputError(true);
      return;
    }
    fetch(`${import.meta.env.VITE_HOST}/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_id: Number(fileId),
        input_data: JSON.parse(inputData),
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setFileId("");
        setInputData("");
        console.log("연산 요청 ID:", data.jobId);
        setRequestId(data.jobId);
      })
      .catch((e) => console.error(e));
  };

  return (
    <div>
      <h2>모델 연산 요청</h2>
      <input
        type="text"
        placeholder="모델 ID 입력"
        value={fileId}
        onChange={(e) => setFileId(e.target.value)}
      />
      <br />
      <textarea
        placeholder="ex)[1, 2, 3, 4]"
        value={inputData}
        onChange={(e) => setInputData(e.target.value)}
      />
      {isInputError && <p>입력값을 다시 확인하십시오</p>}
      <br />
      <button onClick={handleRun}>연산 요청</button>
      {requestId && <p>요청 ID: {requestId}</p>}
    </div>
  );
}

export default Compute;
