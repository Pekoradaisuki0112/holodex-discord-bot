import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params={"status": status})
    return r.json()

def build_message(live_streams, upcoming_streams):
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    message = ""

    # 🎥 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    if live_filtered:
        message += "🎥 直播中\n"
        for s in live_filtered:
            stream_id = s["id"]
            message += f"[{s['channel']['name']}](https://youtu.be/{stream_id})\n"
        message += "\n"

    # ⏰ 一小時後開播
    upcoming_filtered = []
    for s in upcoming_streams:
        if s["channel"]["id"] not in CHANNELS:
            continue
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            upcoming_filtered.append(s)

    if upcoming_filtered:
        message += "⏰ 一小時後開播\n"
        for s in upcoming_filtered:
            stream_id = s["id"]
            message += f"[{s['channel']['name']}](https://youtu.be/{stream_id})\n"

    return message.strip()

def send_discord(text):
    payload = {
        "username": "Holodex Notifier",
        "avatar_url": "https://i.imgur.com/your-default-avatar.png",
        "content": text
    }
    requests.post(WEBHOOK_URL, json=payload)

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    message = build_message(live_streams, upcoming_streams)
    if message:
        send_discord(message)

if __name__ == "__main__":
    main()
