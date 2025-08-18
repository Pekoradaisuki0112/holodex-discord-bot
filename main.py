import requests, json, os
from datetime import datetime, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

# 紀錄已通知過的直播 ID
CACHE_FILE = "notified.json"
try:
    with open(CACHE_FILE) as f:
        notified = set(json.load(f))
except:
    notified = set()

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(list(notified), f)

def main():
    url = "https://holodex.net/api/v2/live"
    params = {"status": "live"}  # 直接抓正在直播
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)

    for s in r.json():
        channel_id = s["channel"]["id"]
        stream_id = s["id"]

        if channel_id in CHANNELS and stream_id not in notified:
            msg = (
                f"🎉 {s['channel']['name']} 正在開台！\n"
                f"{s['title']}\n"
                f"🔗 https://youtu.be/{stream_id}"
            )
            requests.post(WEBHOOK_URL, json={"content": msg})
            notified.add(stream_id)

    save_cache()

if __name__ == "__main__":
    main()
