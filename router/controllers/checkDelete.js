const pool = require("../db/db");

async function checkDelete(req, res) {
  try {
    const { job_id } = req.body;
    let status = "";
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
      } else {
        status = "해당 값 비어있음";
      }
      res.json({ state: status });
    } catch (e) {
      console.error("해당 ID 없음", e);
      res.status(500).json({ state: "해당 ID 없음" });
    }
  } catch (e) {
    console.error("상태 확인 실패: ", e);
    res.status(500).json({ error: "싱태 확인 요청 실패" });
  }
}

module.exports = checkDelete;
