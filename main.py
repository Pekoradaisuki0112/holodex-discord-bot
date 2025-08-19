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
        channel_id = s["channel"]["id"]
        embeds.append({
            "title": s["channel"]["name"],  # 主播名字
            "url": f"https://www.youtube.com/channel/{channel_id}",  # 跳到頻道首頁
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",  # 標題點擊跳直播
            "color": 0xFF69B4,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/maxresdefault.jpg"},
            "footer": {"text": "🎥 直播中"}
        })

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

    for s in upcoming_filtered:
        stream_id = s["id"]
        channel_id = s["channel"]["id"]
        embeds.append({
            "title": s["channel"]["name"],
            "url": f"https://www.youtube.com/channel/{channel_id}",
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0x00BFFF,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/maxresdefault.jpg"},
            "footer": {"text": "⏰ 一小時後開播"}
        })

    return embeds

def send_discord(embeds):
    payload = {
        "username": "Holodex Notifier",
        "avatar_url": "https://i.imgur.com/your-default-avatar.png",
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
