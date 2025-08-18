const fetch = require("node-fetch");

const API_URL = "https://holodex.net/api/v2/live";
const CHANNELS = [   // 換成你追隨的頻道 ID
  "UCMwGHR0BTZuLsmjY_NT5Pwg",
  "UC8NZiqKx6fsDT3AVcMiVFyA"
];

async function main() {
  const res = await fetch(API_URL);
  const data = await res.json();

  const now = new Date();
  const nowTW = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Taipei" }));

  const live = [];
  const upcoming = [];

  for (const stream of data) {
    if (!CHANNELS.includes(stream.channel.id)) continue;

    const startTime = new Date(stream.start_scheduled);
    const startTW = new Date(startTime.toLocaleString("en-US", { timeZone: "Asia/Taipei" }));

    if (stream.status === "live") {
      live.push(`🔴 ${stream.channel.name} 正在開台 (${startTW.toLocaleString("zh-TW")})`);
    } else if (stream.status === "upcoming") {
      const diff = (startTime - now) / (1000 * 60); // 分鐘
      if (diff <= 60) {
        upcoming.push(`⏰ ${stream.channel.name} 將於 ${startTW.toLocaleString("zh-TW")} 開台`);
      }
    }
  }

  console.log("===== 正在開台 =====");
  if (live.length > 0) {
    console.log(live.join("\n"));
  } else {
    console.log("目前沒有人開台");
  }

  console.log("\n===== 一小時內將開台 =====");
  if (upcoming.length > 0) {
    console.log(upcoming.join("\n"));
  } else {
    console.log("目前沒有即將開台的頻道");
  }
}

main().catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
