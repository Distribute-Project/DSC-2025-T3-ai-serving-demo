const mysql = require("mysql2/promise");
const pool = require("../db/db");
const deleteDriveFile = require("../services/deleteDriveFile");

async function checkStatus(req, res) {
  try {
    const { job_id } = req.body;
    let status = "";
    let model_id = null;
    try {
      const [rows] = await pool.query(
        "SELECT state, data FROM job WHERE id=?",
        [job_id]
      );
      if (rows[0]?.state === -1) {
        status = "진행 중";
      } else if (rows[0]?.state === 0) {
        status = "실패";
      } else if (rows[0]?.state === 1) {
        status = "성공";
        model_id = rows[0]?.data.model_id;
        const fileId = rows[0]?.data.file_url.split("=")[1];
        console.log(fileId);
        await deleteDriveFile(fileId);
      } else {
        status = "해당 값 비어있음";
      }

      res.json({ state: status, ...(model_id && { model_id }) });
    } catch (e) {
      console.error("해당 id 없음", e);
      res.status(500).json({ state: "해당 id 없음" });
    }
  } catch (e) {
    console.error("상태 확인 실패:", e);
    res.status(500).json({ error: "상태 확인 요청 실패" });
  }
}

module.exports = { checkStatus };
