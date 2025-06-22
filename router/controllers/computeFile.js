const { getLeastMasterId } = require("../services/getLeastMasterId");
const { insertToDb } = require("../services/insertToDb");
const { sendMessage } = require("../services/sendMessage");
const retry = require("../utils/dbRetry");

async function computeFile(req, res) {
  try {
    const { file_id, input_data } = req.body;

    if (!input_data) {
      return res.status(400).json({ error: "input data가 필요합니다." });
    }

    const masterId = await retry(() => getLeastMasterId());
    const data = { type: "compute", input: input_data, model_id: file_id };

    const jobId = await retry(() => insertToDb(masterId, data));
    await sendMessage(jobId, masterId, "c");

    res.json({ success: true, jobId });
  } catch (err) {
    console.error("연산 요청 실패:", err);
    res.status(500).json({ success: false, error: "연산 요청 실패" });
  }
}

module.exports = { computeFile };
