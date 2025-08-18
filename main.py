import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

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

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    params = {"status": status}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def notify(streams, prefix=""):
    now = datetime.now(timezone.utc)
    one_hour_later = now + timedelta(hours=1)

    for s in streams:
        channel_id = s["channel"]["id"]
        stream_id = s["id"]

        # 篩選收藏頻道 + 未通知過
        if channel_id not in CHANNELS or stream_id in notified:
            continue

        # 如果是 upcoming，篩選 1 小時內
        if prefix == "即將開台":
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00"))
            if not (now <= start_time <= one_hour_later):
                continue
            time_str = f"🕒 {start_time.strftime('%H:%M UTC')}"
        else:
            time_str = ""

        msg = (
            f"🎉 {s['channel']['name']} {prefix}！\n"
            f"{s['title']}\n"
            f"{time_str}\n"
            f"🔗 https://youtu.be/{stream_id}"
        )
        requests.post(WEBHOOK_URL, json={"content": msg})
        notified.add(stream_id)

def main():
    # 先抓正在直播
    live_streams = fetch_live("live")
    notify(live_streams, prefix="正在開台")

    # 再抓即將開台
    upcoming_streams = fetch_live("upcoming")
    notify(upcoming_streams, prefix="即將開台")

    # 儲存通知過的直播
    save_cache()

if __name__ == "__main__":
    main()
