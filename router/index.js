require("dotenv").config();
const express = require("express");
const multer = require("multer");
const cors = require("cors");
const { uploadFile } = require("./controllers/uploadFile");
const { computeFile } = require("./controllers/computeFile");
const { checkStatus } = require("./controllers/checkStatus");
const { checkResult } = require("./controllers/checkResult");
const deleteFile = require("./controllers/deleteFile");
const checkDelete = require("./controllers/checkDelete");

const app = express();
const PORT = 4000;

// app.use(express.json());
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ limit: "50mb", extended: true }));
app.use(cors());

// 파일 로컬 업로드
const storage = multer.diskStorage({
  destination: "uploads/",
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  },
});
const upload = multer({ storage });

// upload
app.post("/upload", upload.single("file"), uploadFile);

// compute
app.post("/compute", computeFile);

// delete
app.post("/delete", deleteFile);

// check status(save)
app.post("/check/upload", checkStatus);

// check status(compute)
app.post("/check/compute", checkResult);

// check status(delete)
app.post("/check/delete", checkDelete);

// 서버 시작
app.listen(PORT, () => {
  console.log(`📡 API Gateway running at http://localhost:${PORT}`);
});
