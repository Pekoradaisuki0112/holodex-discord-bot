import requests, json, os
from datetime import datetime, timedelta, timezone

# 驗證環境變數
try:
    API_KEY = os.environ["HOLODEX_API_KEY"]
    WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
except KeyError as e:
    raise ValueError(f"缺少環境變數: {e}")

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_live(status, mentioned_channel_id=None):
    try:
        params = {"status": status}
        if mentioned_channel_id:
            params["mentioned_channel_id"] = mentioned_channel_id
        r = requests.get(
            "https://holodex.net/api/v2/live",
            headers={"X-APIKEY": API_KEY},
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"API 請求失敗: {e}")
        return []

def build_embeds(live_streams, upcoming_streams, mentioned_live_streams, mentioned_upcoming_streams):
    embeds = []

    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    # 直播中 - 主頻道
    for s in live_streams:
        if s["channel"]["id"] in CHANNELS:
            stream_id = s["id"]
            embeds.append({
                "title": s["channel"]["name"],
                "description": f"[{s['title']}](https://youtu.be/{stream_id})",
                "color": 0xFF69B4,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    # 直播中 - 被提及的頻道
    for s in mentioned_live_streams:
        stream_id = s["id"]
        embeds.append({
            "title": f"{s['channel']['name']} (提及)",
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFFB6C1,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
        })

    # 一小時後開播 - 主頻道
    for s in upcoming_streams:
        if s["channel"]["id"] in CHANNELS:
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if now <= start_time <= one_hour_later:
                stream_id = s["id"]
                time_str = start_time.strftime("%H:%M")
                embeds.append({
                    "title": s["channel"]["name"],
                    "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                    "color": 0x00BFFF,
                    "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
                })

    # 一小時後開播 - 被提及的頻道
    for s in mentioned_upcoming_streams:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            stream_id = s["id"]
            time_str = start_time.strftime("%H:%M")
            embeds.append({
                "title": f"{s['channel']['name']} (提及)",
                "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                "color": 0xADD8E6,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def send_discord(live_streams, embeds):
    if not embeds:
        print("沒有新的直播或即將開播的串流")
        return

    # webhook avatar 取最新正在直播的主播頭像
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    avatar_url = live_filtered[-1]["channel"]["photo"] if live_filtered else "https://i.imgur.com/your-default-avatar.png"

    payload = {
        "username": "Holodex Notifier",
        "avatar_url": avatar_url,
        "embeds": embeds
    }
    
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Discord webhook 發送失敗: {e}")

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    
    # 查詢被提及我們頻道的串流
    mentioned_live_streams = []
    mentioned_upcoming_streams = []
    for channel_id in CHANNELS:
        mentioned_live_streams.extend(fetch_live("live", mentioned_channel_id=channel_id))
        mentioned_upcoming_streams.extend(fetch_live("upcoming", mentioned_channel_id=channel_id))
    
    embeds = build_embeds(live_streams, upcoming_streams, mentioned_live_streams, mentioned_upcoming_streams)
    send_discord(live_streams, embeds)

if __name__ == "__main__":
    main()
