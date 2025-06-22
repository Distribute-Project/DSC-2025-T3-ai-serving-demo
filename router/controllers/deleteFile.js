const retry = require("../utils/dbRetry");
const { getLeastMasterId } = require("../services/getLeastMasterId");
const { insertToDb } = require("../services/insertToDb");
const { sendMessage } = require("../services/sendMessage");

async function deleteFile(req, res) {
  try {
    const { file_id } = req.body;
    const masterId = await retry(() => getLeastMasterId());
    const data = { type: "delete", model_id: Number(file_id) };

    const jobId = await retry(() => insertToDb(masterId, data));
    await sendMessage(jobId, masterId, "d");
    res.json({ success: true, jobId });
  } catch (e) {
    console.error("삭제 요청 실패 : ", e);
    res.status(500).json({ success: false, error: "삭제 요청 실패" });
  }
}

module.exports = deleteFile;
