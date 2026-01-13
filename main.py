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

def fetch_mentions(status):
    """獲取提到追蹤頻道的直播（聯動）"""
    all_mentions = []
    for channel_id in CHANNELS:
        r = requests.get(
            "https://holodex.net/api/v2/live",
            headers={"X-APIKEY": API_KEY},
            params={
                "status": status,
                "mentioned_channel_id": channel_id
            }
        )
        mentions = r.json()
        # 過濾掉已經在 CHANNELS 列表中的頻道（避免重複）
        mentions = [s for s in mentions if s["channel"]["id"] not in CHANNELS]
        all_mentions.extend(mentions)
    
    # 去重（同一個直播可能提到多個追蹤的頻道）
    seen = set()
    unique_mentions = []
    for s in all_mentions:
        if s["id"] not in seen:
            seen.add(s["id"])
            unique_mentions.append(s)
    
    return unique_mentions

def build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions):
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

    # 直播中的聯動（提到追蹤頻道）
    for s in live_mentions:
        stream_id = s["id"]
        # 獲取被提到的追蹤頻道名稱
        mentioned_names = [m["name"] for m in s.get("mentions", []) if m["id"] in CHANNELS]
        mention_text = f" 👥 聯動: {', '.join(mentioned_names)}" if mentioned_names else " 👥 聯動"
        
        embeds.append({
            "title": s["channel"]["name"] + mention_text,
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFFD700,  # 金色表示聯動
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

    # 一小時後開播的聯動
    for s in upcoming_mentions:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            stream_id = s["id"]
            mentioned_names = [m["name"] for m in s.get("mentions", []) if m["id"] in CHANNELS]
            mention_text = f" 👥 聯動: {', '.join(mentioned_names)}" if mentioned_names else " 👥 聯動"
            
            embeds.append({
                "title": s["channel"]["name"] + mention_text,
                "description": f"[{s['title']}](https://youtu.be/{stream_id})",
                "color": 0x90EE90,  # 淺綠色表示即將開始的聯動
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
    
    # 獲取提到追蹤頻道的直播
    live_mentions = fetch_mentions("live")
    upcoming_mentions = fetch_mentions("upcoming")
    
    embeds = build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions)
    
    if embeds:  # 只在有內容時才發送
        send_discord(live_streams, embeds)

if __name__ == "__main__":
    main()
