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

def build_embed(live_streams, upcoming_streams):
    description = ""

    # 🎥 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    if live_filtered:
        description += "🎥 直播中\n"
        for s in live_filtered:
            stream_id = s["id"]
            description += f"[{s['channel']['name']}](https://youtu.be/{stream_id}) - {s['title']}\n"
        description += "\n"

    # ⏰ 一小時後開播
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)
    upcoming_filtered = []
    for s in upcoming_streams:
        if s["channel"]["id"] not in CHANNELS:
            continue
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            upcoming_filtered.append(s)

    if upcoming_filtered:
        description += "⏰ 一小時後開播\n"
        for s in upcoming_filtered:
            stream_id = s["id"]
            description += f"[{s['channel']['name']}](https://youtu.be/{stream_id}) - {s['title']}\n"

    payload = {
        "username": "Holodex Notifier",
        "avatar_url": "https://i.imgur.com/your-default-avatar.png",
        "embeds": [
            {
                "title": "📢 VTuber 直播通知",
                "description": description.strip(),
                "color": 0xFF69B4
            }
        ]
    }
    return payload

def send_discord(embed):
    requests.post(WEBHOOK_URL, json=embed)

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    embed_payload = build_embed(live_streams, upcoming_streams)
    send_discord(embed_payload)

if __name__ == "__main__":
    main()
