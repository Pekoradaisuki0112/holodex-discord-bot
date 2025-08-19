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

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    params = {"status": status}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def create_embed(live_streams, upcoming_streams):
    from discord_webhook import DiscordWebhook, DiscordEmbed

    webhook = DiscordWebhook(url=WEBHOOK_URL)

    embed = DiscordEmbed(title="📢 VTuber 直播通知", color=0xFF69B4)

    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    description = ""

    # 🎥 直播中
    if live_streams:
        description += "🎥 **直播中**\n"
        for s in live_streams:
            if s["channel"]["id"] not in CHANNELS:
                continue
            description += f"[{s['channel']['name']} - {s['title']}]({s['id']})\n"
            description += f"https://img.youtube.com/vi/{s['id']}/maxresdefault.jpg\n\n"

    # ⏰ 一小時後開播
    if upcoming_streams:
        description += "⏰ **一小時後開播**\n"
        for s in upcoming_streams:
            if s["channel"]["id"] not in CHANNELS:
                continue
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if not (now <= start_time <= one_hour_later):
                continue
            description += f"[{s['channel']['name']} - {s['title']}]({s['id']})\n"
            description += f"https://img.youtube.com/vi/{s['id']}/maxresdefault.jpg\n\n"

    embed.set_description(description)
    webhook.add_embed(embed)
    webhook.execute()

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    create_embed(live_streams, upcoming_streams)

if __name__ == "__main__":
    main()
