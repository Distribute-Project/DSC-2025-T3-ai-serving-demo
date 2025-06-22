async function retry(func) {
  for (let i = 1; i > 0; i++) {
    try {
      return await func();
    } catch (e) {
      console.error(e);
      const isRetryable =
        e.message.includes("ECONNREFUSED") ||
        e.message.includes("ETIMEDOUT") ||
        e.message.includes("Connection lost") ||
        e.code === "PROTOCOL_CONNECTION_LOST";

      if (!isRetryable) {
        console.error("조치 필요");
        throw e;
      }
      const delay = i < 4 ? 1000 * Math.pow(2, i) : 10000;
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

module.exports = retry;
