const mysql = require("mysql2/promise");
const pool = require("../db/db");

async function insertToDb(masterId, data) {
  try {
    const [jobInfo] = await pool.query(
      "INSERT INTO job (state, master, data) VALUES (?, ?, ?)",
      [-1, JSON.stringify({ master: masterId }), JSON.stringify(data)]
    );
    return jobInfo.insertId;
  } catch (e) {
    console.error("Job 생성 실패 : " + e);
    throw e;
  }
}

module.exports = { insertToDb };
