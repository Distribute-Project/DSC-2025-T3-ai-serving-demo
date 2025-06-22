import { useState } from "react";

function DeleteFile() {
  const [fileId, setFileId] = useState("");
  const [requestId, setRequestId] = useState(null);

  const handleDelete = () => {
    fetch(`${import.meta.env.VITE_HOST}/delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_id: fileId,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setFileId("");
        setRequestId(data.jobId);
      })
      .catch((e) => {
        console.error(e);
      });
  };

  return (
    <div>
      <input
        type="text"
        placeholder="model id 입력"
        value={fileId}
        onChange={(e) => {
          setFileId(e.target.value);
        }}
      />
      <button onClick={handleDelete}>확인</button>
      {requestId && <p>요청 ID: {requestId}</p>}
    </div>
  );
}

export default DeleteFile;
