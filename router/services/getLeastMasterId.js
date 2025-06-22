const pool = require("../db/db");

async function getLeastMasterId() {
  // let connection;
  try {
    // connection = await mysql.createConnection({
    //   host: process.env.DB_HOST,
    //   user: process.env.DB_USER,
    //   password: process.env.DB_PW,
    //   database: process.env.DB_NAME,
    // });

    // const [rows] = await connection.execute(
    //   "SELECT id FROM master WHERE is_online = 1 and queue = (SELECT MIN(queue) FROM master WHERE is_online = 1)"
    // );
    const [rows] = await pool.execute(
      "SELECT id FROM master WHERE is_online = 1 and queue = (SELECT MIN(queue) FROM master WHERE is_online = 1)"
    );
    if (rows.length === 0) {
      throw new Error("online 상태 master 없음");
    }
    return rows[0].id;
  } catch (e) {
    console.error("Master ID 값 가져오기 실패" + e);
    throw e;
  }
}

module.exports = { getLeastMasterId };
