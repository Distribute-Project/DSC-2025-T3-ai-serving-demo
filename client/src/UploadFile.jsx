import React, { useState } from "react";

function UploadFile() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState("");
  const [modelId, setModelId] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${import.meta.env.VITE_HOST}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setJobId(data.jobId);
      setModelId(data.fileId);
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  return (
    <div>
      <input type="file" accept=".pt" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {jobId && <p>Job ID: {jobId}</p>}
      {/* {modelId && <p>Model ID: {modelId}</p>} */}
    </div>
  );
}

export default UploadFile;
