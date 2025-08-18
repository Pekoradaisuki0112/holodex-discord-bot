import requests, json, os
from datetime import datetime, timedelta

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# 讀取收藏頻道
with open("channels.json") as f:
    CHANNELS = json.load(f)

def main():
    if not CHANNELS:
        print("收藏頻道清單是空的喔～")
        return

    url = "https://holodex.net/api/v2/live"
    params = {
        "channels": ",".join(CHANNELS),
        "status": "upcoming"
    }
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    streams = r.json()

    if not streams:
        print("目前沒有即將開台的直播～")
        return

    now = datetime.utcnow()
    one_hour_later = now + timedelta(hours=1)

    for s in streams:
        # Holodex API 回傳的時間格式是 ISO 8601
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z", "+00:00"))

        # 只抓一小時內的直播
        if now <= start_time <= one_hour_later:
            msg = f"🎉 {s['channel']['name']} 一小時內要開台囉！\n{s['title']}\n🕒 {start_time}\n🔗 https://youtu.be/{s['id']}"
            requests.post(WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    main()
