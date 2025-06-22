import { useState } from "react";

function CheckStatus() {
  const [jobId, setJobId] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState("upload");
  const [result, setResult] = useState("");
  const [modelId, setModelId] = useState("");

  const handleCheck = () => {
    setResult("");
    setModelId("");
    setStatus("");
    fetch(`${import.meta.env.VITE_HOST}/check/${selected}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: Number(jobId),
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setStatus(data.state);
        if (data.result) {
          console.log(data.result);
          setResult(JSON.stringify(data.result));
        }
        if (data.model_id) {
          setModelId(data.model_id);
        }
      })
      .catch((e) => console.error(e));
  };
  return (
    <div>
      <div>
        <label htmlFor="">
          <input
            type="radio"
            name="check"
            value="upload"
            checked={selected === "upload"}
            onChange={(e) => {
              setSelected(e.target.value);
            }}
          />
          저장 확인
        </label>
        <label htmlFor="">
          <input
            type="radio"
            name="check"
            value="compute"
            checked={selected === "compute"}
            onChange={(e) => {
              setSelected(e.target.value);
            }}
          />
          연산 확인
        </label>
        <label htmlFor="">
          <input
            type="radio"
            name="check"
            value="delete"
            checked={selected === "delete"}
            onChange={(e) => {
              setSelected(e.target.value);
            }}
          />
          삭제 확인
        </label>
      </div>
      <input
        type="number"
        placeholder="job id 입력"
        value={jobId}
        onChange={(e) => {
          setJobId(e.target.value);
        }}
      />
      <button onClick={handleCheck}>확인</button>
      {status && <p>진행상태 : {status}</p>}
      {modelId && <p>모델 ID : {modelId}</p>}
      {result && (
        <p
          style={{
            width: "100%",
            overflow: "hidden",
            overflowWrap: "break-word",
          }}
        >
          연산결과 : {result}
        </p>
      )}
    </div>
  );
}

export default CheckStatus;
