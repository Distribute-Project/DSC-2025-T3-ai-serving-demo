const amqp = require("amqplib");

// rabbitmq 끊기 전 딜레이 유발
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let connection;
let channel;
let retries = 0;
let isConnecting = false;
let serverDown = false; // 서버 동작 중 여부

process.on("SIGINT", async () => {
  console.log("서버 종료 중... RabbitMQ 연결 종료 중");
  serverDown = true;
  if (connection) await connection.close();
  process.exit();
});

async function getChannel() {
  if (channel) return channel;
  if (isConnecting) {
    while (isConnecting) await delay(100);
    return channel;
  }

  isConnecting = true;

  try {
    if (!connection) {
      connection = await amqp.connect(
        `amqp://${process.env.RABBITMQ_ID}:${process.env.RABBITMQ_PWD}@${process.env.RABBITMQ_HOST}:${process.env.RABBITMQ_PORT}`
      );

      connection.on("error", (err) => {
        console.error("RabbitMQ 연결 오류:", err.message);
      });

      connection.on("close", async () => {
        console.warn("RabbitMQ 연결이 끊어졌습니다. 재연결 시도 중...");
        connection = null;
        channel = null;
        await reconnect();
      });
    }
    channel = await connection.createChannel();
    retries = 0;
    return channel;
  } finally {
    isConnecting = false;
  }
}

async function reconnect() {
  if (serverDown) return;
  const delay = Math.min(1000 * Math.pow(2, retries), 10000);
  retries++;
  await new Promise((r) => setTimeout(r, delay));
  return getChannel();
}

// RabbitMQ 연결 설정
async function sendMessage(jobId, masterId, mode) {
  try {
    const ch = await getChannel();

    // RabbitMQ 교환기 name
    let exchange = "";
    if (mode === "s") {
      exchange = "save";
    } else if (mode === "c") {
      exchange = "compute";
    } else {
      exchange = "delete";
    }
    // RabbitMQ 라우팅 키
    let routingKey = "";
    if (mode === "s") {
      routingKey = `master${masterId}.save.req`;
    } else if (mode === "c") {
      routingKey = `master${masterId}.compute.req`;
    } else {
      routingKey = `master${masterId}.delete.req`;
    }
    const msg = JSON.stringify({ job_id: jobId });

    // 교환기 생성
    await ch.assertExchange(exchange, "direct", { durable: true });

    // 메세지 발행
    const ok = ch.publish(exchange, routingKey, Buffer.from(msg), {
      persistent: true,
    });
    if (!ok) {
      throw new Error("메세지 발행 실패");
    }
  } catch (e) {
    console.error(e);
    throw e;
  }
}

module.exports = { sendMessage };
