import requests, json, os
from datetime import datetime, timedelta, timezone

# --- 設定 ---
API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# 收藏頻道 ID
with open("channels.json") as f:
    CHANNELS = json.load(f)

# 台灣時間 UTC+8
TWTZ = timezone(timedelta(hours=8))

# --- 抓取直播 ---
def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    params = {"status": status}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

# --- 發送 embed 通知 ---
def notify_embed(streams, prefix=""):
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    for s in streams:
        channel_id = s["channel"]["id"]
        stream_id = s["id"]

        if channel_id not in CHANNELS:
            continue

        # upcoming 篩選 1 小時內
        time_str = ""
        if prefix == "即將開台":
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if not (now <= start_time <= one_hour_later):
                continue
            time_str = f"🕒 {start_time.strftime('%Y-%m-%d %H:%M')} 台灣時間"

        # embed 訊息
        embed = {
            "username": "Holodex Notifier",
            "avatar_url": s["channel"]["photo"],
            "embeds": [
                {
                    "title": f"{s['channel']['name']} {prefix}！",
                    "description": f"**{s['title']}**\n{time_str}\n🔗 https://youtu.be/{stream_id}",
                    "color": 0xFF69B4 if prefix=="正在開台" else 0x00BFFF  # 粉紅=live, 藍=upcoming
                }
            ]
        }

        requests.post(WEBHOOK_URL, json=embed)

# --- 主程式 ---
def main():
    # 先抓正在直播
    live_streams = fetch_live("live")
    notify_embed(live_streams, prefix="正在開台")

    # 再抓即將開台
    upcoming_streams = fetch_live("upcoming")
    notify_embed(upcoming_streams, prefix="即將開台")

if __name__ == "__main__":
    main()
