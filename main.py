import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# 收藏頻道
with open("channels.json") as f:
    CHANNELS = json.load(f)

CACHE_FILE = "notified.json"

# 載入已通知過的直播 ID
try:
    with open(CACHE_FILE) as f:
        notified = set(json.load(f))
except:
    notified = set()

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(list(notified), f)

# 台灣時間 UTC+8
TWTZ = timezone(timedelta(hours=8))

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    params = {"status": status}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def notify(streams, prefix=""):
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    for s in streams:
        channel_id = s["channel"]["id"]
        stream_id = s["id"]

        if channel_id not in CHANNELS or stream_id in notified:
            continue

        # upcoming 篩選 1 小時內
        time_str = ""
        if prefix == "即將開台":
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if not (now <= start_time <= one_hour_later):
                continue
            time_str = f"🕒 {start_time.strftime('%Y-%m-%d %H:%M')} 台灣時間"

        # Discord 訊息格式
        msg = {
            "content": f"🎉 {s['channel']['name']} {prefix}！\n**{s['title']}**\n{time_str}\n🔗 https://youtu.be/{stream_id}",
            "username": "Holodex Notifier",
            "avatar_url": s["channel"]["photo"]  # 頻道頭像
        }

        requests.post(WEBHOOK_URL, json=msg)
        notified.add(stream_id)

def main():
    # 先抓正在直播
    live_streams = fetch_live("live")
    notify(live_streams, prefix="正在開台")

    # 再抓即將開台
    upcoming_streams = fetch_live("upcoming")
    notify(upcoming_streams, prefix="即將開台")

    # 儲存已通知直播
    save_cache()

if __name__ == "__main__":
    main()
