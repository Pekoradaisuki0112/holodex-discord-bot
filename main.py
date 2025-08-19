import requests, json, os
from datetime import datetime, timedelta, timezone

# --- 設定 ---
API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# 收藏頻道 ID
with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    headers = {"X-APIKEY": API_KEY}
    params = {"status": status}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def build_embeds(live_streams, upcoming_streams):
    embeds = []

    # 🎥 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    if live_filtered:
        embeds.append({
            "title": "🎥 直播中",
            "color": 0xFF69B4
        })
        for s in live_filtered:
            stream_id = s["id"]
            embeds.append({
                "title": s["channel"]["name"],
                "url": f"https://youtu.be/{stream_id}",
                "description": s["title"],
                "image": {"url": f"https://img.youtube.com/vi/{stream_id}/maxresdefault.jpg"},
                "color": 0xFF69B4
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

    if upcoming_filtered:
        embeds.append({
            "title": "⏰ 一小時後開播",
            "color": 0x00BFFF
        })
        for s in upcoming_filtered:
            stream_id = s["id"]
            embeds.append({
                "title": s["channel"]["name"],
                "url": f"https://youtu.be/{stream_id}",
                "description": s["title"],
                "image": {"url": f"https://img.youtube.com/vi/{stream_id}/maxresdefault.jpg"},
                "color": 0x00BFFF
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
