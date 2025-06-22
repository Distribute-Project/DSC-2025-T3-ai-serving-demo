const { drive } = require("../controllers/uploadFile");

async function deleteDriveFile(fileId) {
  try {
    await drive.files.delete({
      fileId,
    });
    console.log(fileId);
    const res = await drive.files.list({
      pageSize: 10,
      fields: "files(id, name)",
    });
    console.log("서비스 계정 드라이브에 있는 파일들:", res.data.files);
  } catch (e) {
    console.error("임시저장소 파일 삭제 실패 : " + e);
  }
}

module.exports = deleteDriveFile;
