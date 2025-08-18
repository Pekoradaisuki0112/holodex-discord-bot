import requests, json, os
from datetime import datetime, timedelta

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

def main():
    if not CHANNELS:
        print("收藏頻道清單是空的～")
        return

    url = "https://holodex.net/api/v2/live"
    params = {"channels": ",".join(CHANNELS), "status": "upcoming"}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    
    try:
        streams = r.json()
    except Exception as e:
        print("JSON 解析失敗:", e)
        return

    if not isinstance(streams, list):
        print("API 回傳非列表資料:", streams)
        return

    now = datetime.utcnow()
    one_hour_later = now + timedelta(hours=1)

    for s in streams:
        try:
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z", "+00:00"))
        except Exception as e:
            print("解析時間失敗:", s.get("start_scheduled"), e)
            continue

        if now <= start_time <= one_hour_later:
            msg = f"🎉 {s['channel']['name']} 一小時內要開台囉！\n{s['title']}\n🕒 {start_time}\n🔗 https://youtu.be/{s['id']}"
            requests.post(WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    main()
