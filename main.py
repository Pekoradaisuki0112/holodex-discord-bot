import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_streams(status):
    url = "https://holodex.net/api/v2/live"
    params = {"status": status}
    headers = {"X-APIKEY": API_KEY}
    return requests.get(url, headers=headers, params=params).json()

def notify(streams, label):
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)
    messages = []

    for s in streams:
        if s["channel"]["id"] not in CHANNELS:
            continue

        time_str = ""
        if label == "即將開台":
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if not (now <= start_time <= one_hour_later):
                continue
            time_str = f"🕒 {start_time.strftime('%Y-%m-%d %H:%M')} 台灣時間"

        msg = f"🎉 {s['channel']['name']} {label}！\n**{s['title']}**\n{time_str}\n🔗 https://youtu.be/{s['id']}"
        messages.append(msg)

    if messages:
        content = f"=== {label} ===\n" + "\n".join(messages)
        requests.post(WEBHOOK_URL, json={"content": content})

def main():
    live_streams = fetch_streams("live")
    notify(live_streams, "正在開台")

    upcoming_streams = fetch_streams("upcoming")
    notify(upcoming_streams, "即將開台")

if __name__ == "__main__":
    main()
