import requests
import time
from datetime import datetime, timedelta, timezone

API_URL = "https://holodex.net/api/v2/users/live"
API_KEY = "你的API_KEY"
HEADERS = {"X-APIKEY": API_KEY}

# 台灣時區 (UTC+8)
taiwan_tz = timezone(timedelta(hours=8))

def fetch_lives():
    try:
        res = requests.get(API_URL, headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("抓取資料失敗:", e)
        return []

def display_lives():
    lives = fetch_lives()
    if not lives:
        print("目前沒有資料")
        return

    now = datetime.now(timezone.utc)
    one_hour_later = now + timedelta(hours=1)

    live_now = []
    live_soon = []

    for live in lives:
        if live.get("status") == "live":
            live_now.append(live["channel"]["name"])
        elif live.get("status") == "upcoming":
            start_at_str = live.get("start_scheduled")
            if start_at_str:
                start_at = datetime.fromisoformat(start_at_str.replace("Z", "+00:00"))
                if now <= start_at <= one_hour_later:
                    taiwan_time = start_at.astimezone(taiwan_tz).strftime("%H:%M")
                    live_soon.append(f'{live["channel"]["name"]} ({taiwan_time})')

    print("=== 正在開台 ===")
    if live_now:
        for name in live_now:
            print("-", name)
    else:
        print("（無）")

    print("\n=== 一小時內會開台 ===")
    if live_soon:
        for name in live_soon:
            print("-", name)
    else:
        print("（無）")

if __name__ == "__main__":
    while True:
        print("\n更新時間:", datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S"))
        display_lives()
        time.sleep(20 * 60)  # 20 分鐘

