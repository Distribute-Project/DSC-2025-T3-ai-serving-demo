const mysql = require("mysql2/promise");
const pool = require("../db/db");

async function getResult(job_id) {
  try {
    const [rows] = await pool.query("SELECT result FROM job WHERE id=?", [
      job_id,
    ]);
    const result = rows[0]?.result; // {result: 51511}
    console.log(result.result);
    return result.result;
  } catch (e) {
    console.error("결과값 가져오기 실패" + e);
  }
}

async function checkResult(req, res) {
  try {
    const { job_id } = req.body;
    let status = "";
    let result = 0;
    try {
      const [state] = await pool.query("SELECT state FROM job WHERE id=?", [
        job_id,
      ]);
      if (state[0].state === -1) {
        status = "진행 중";
      } else if (state[0].state === 0) {
        status = "실패";
      } else if (state[0].state === 1) {
        status = "성공";
        result = await getResult(job_id);
        console.log(result);
      }

      res.json({ state: status, result });
    } catch (e) {
      console.error("해당 id 없음", e);
      res.status(500).json({ state: "해당 id 없음" });
    }
  } catch (e) {
    console.error("상태 확인 실패:", e);
    res.status(500).json({ error: "상태 확인 요청 실패" });
  }
}

module.exports = { checkResult };
