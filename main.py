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

def build_embeds(live_streams, upcoming_streams):
    embeds = []

    # 🎥 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    for s in live_filtered:
        stream_id = s["id"]
        embeds.append({
            "title": s["channel"]["name"],
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFF69B4,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"},
            "channel_photo": s["channel"]["photo"]  # 暫存用
        })

    # ⏰ 一小時後開播
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)
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
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"},
                "channel_photo": s["channel"]["photo"]  # 暫存用
            })

    return embeds

def send_discord(embeds):
    # 找最新正在直播的主播頭像作為 webhook avatar
    live_embeds = [e for e in embeds if e["color"] == 0xFF69B4]
    webhook_avatar = live_embeds[-1]["channel_photo"] if live_embeds else "https://i.imgur.com/your-default-avatar.png"

    # 移除暫存用的 channel_photo
    for e in embeds:
        e.pop("channel_photo", None)

    payload = {
        "username": "Holodex Notifier",
        "avatar_url": webhook_avatar,
        "embeds": embeds
    }
    requests.post(WEBHOOK_URL, json=payload)

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    embeds = build_embeds(live_streams, upcoming_streams)
    send_discord(embeds)

if __name__ == "__main__":
    main()
