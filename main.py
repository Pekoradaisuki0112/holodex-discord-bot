import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_live(status):
    r = requests.get(
        "https://holodex.net/api/v2/live",
        headers={"X-APIKEY": API_KEY},
        params={"status": status}
    )
    return r.json()

def build_embeds(live_streams, upcoming_streams):
    embeds = []

    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    # 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    for s in live_filtered:
        stream_id = s["id"]
        embeds.append({
            "title": s["channel"]["name"],
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFF69B4,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
        })

    # 一小時後開播
    for s in upcoming_streams:
        if s["channel"]["id"] not in CHANNELS:
            continue
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            stream_id = s["id"]
            embeds.append({
                "title": s["channel"]["name"],
                "description": f"[{s['title']}](https://youtu.be/{stream_id})",
                "color": 0x00BFFF,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def send_discord(live_streams, embeds):
    # webhook avatar 取最新正在直播的主播頭像
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    avatar_url = live_filtered[-1]["channel"]["photo"] if live_filtered else "https://i.imgur.com/your-default-avatar.png"

    payload = {
        "username": "Holodex Notifier",
        "avatar_url": avatar_url,
        "embeds": embeds
    }
    requests.post(WEBHOOK_URL, json=payload)

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    embeds = build_embeds(live_streams, upcoming_streams)
    send_discord(live_streams, embeds)

if __name__ == "__main__":
    main()
