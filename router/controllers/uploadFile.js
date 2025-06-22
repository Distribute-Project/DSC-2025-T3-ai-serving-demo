require("dotenv").config();
const fs = require("fs");
const { google } = require("googleapis");
const { sendMessage } = require("../services/sendMessage");
const { insertToDb } = require("../services/insertToDb");
const { getLeastMasterId } = require("../services/getLeastMasterId");
const retry = require("../utils/dbRetry");

// 구글 드라이브 auth
const auth = new google.auth.GoogleAuth({
  keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
  scopes: ["https://www.googleapis.com/auth/drive"],
});
const drive = google.drive({ version: "v3", auth });

// 구글 드라이브 업로드
async function uploadToDrive(filePath, fileName) {
  const fileMetadata = { name: fileName };
  try {
    const media = {
      mimeType: "application/octet-stream",
      body: fs.createReadStream(filePath),
    };
    media.body.on("error", (err) => {
      console.error("파일 스트림 에러:", err);
    });
    const file = await drive.files.create({
      requestBody: fileMetadata,
      media,
      fields: "id, size",
    });

    // 링크 공유 설정
    try {
      await drive.permissions.create({
        fileId: file.data.id,
        requestBody: {
          type: "anyone",
          role: "reader",
        },
      });
    } catch (e) {
      console.log("링크 공유 옵션 설정 실패 : " + e);
    }

    const downloadUrl = `https://drive.google.com/uc?id=${file.data.id}`;
    return {
      fileId: file.data.id,
      fileUrl: downloadUrl,
      fileSize: file.data.size,
    };
  } catch (e) {
    console.error("구글 드라이브 업로드 실패 : " + e);
    throw e;
  }
}

// code for dev
async function deleteDrive() {
  await drive.files.delete({
    fileId: "1dywX8RQ6fVknFhyVkrjh66iylFajpQE5",
  });
  const res = await drive.files.list({
    pageSize: 10,
    fields: "files(id, name)",
  });
  console.log("서비스 계정 드라이브에 있는 파일들:", res.data.files);
}

async function uploadFile(req, res) {
  try {
    const localPath = req.file.path;
    const originalName = req.file.originalname;

    let uploadResult;
    const maxRetries = 3;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        uploadResult = await uploadToDrive(localPath, originalName);
        break;
      } catch (e) {
        // 일시적 에러 확인
        const isRetryable = checkIfRetryableError(e);
        if (!isRetryable) {
          console.error(`조치 필요`);
          throw e;
        }

        console.error("업로드에 실패하였습니다.");
        if (attempt === maxRetries) {
          console.error("재연결 시도 횟수 초과");
          throw e;
        }

        // 3초 기다렸다가 실행
        await new Promise((r) => setTimeout(r, 3000));
      }
    }
    const { fileId, fileUrl, fileSize } = uploadResult;
    // await deleteDrive();

    // 로컬 파일 삭제
    try {
      fs.unlinkSync(localPath);
    } catch (e) {
      console.warn("로컬 파일 삭제 실패:", e.message);
    }

    let masterId;
    masterId = await retry(() => getLeastMasterId());

    const data = { size: Number(fileSize), type: "save", file_url: fileUrl };
    const jobId = await retry(() => insertToDb(masterId, data));
    await sendMessage(jobId, masterId, "s");

    res.json({ success: true, jobId, fileId });
  } catch (err) {
    console.error("Upload failed:", err);
    res.status(500).json({ success: false, error: "파일 업로드 실패" });
  }
}

// 일시적 에러 여부 판단
function checkIfRetryableError(err) {
  // 네트워크 에러, 5xx 서버 에러 등
  if (err.message.includes("ECONNRESET") || err.message.includes("ETIMEDOUT")) {
    return true;
  }
  if (err.response && err.response.status >= 500) {
    return true;
  }
  return false;
}

module.exports = { uploadFile, drive };
