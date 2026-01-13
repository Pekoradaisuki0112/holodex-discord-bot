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
        filtered = [(s, channel_id) for s in mentions if s["channel"]["id"] not in CHANNELS]
        all_mentions.extend(filtered)
    
    # 去重
    seen = {}
    for s, ch_id in all_mentions:
        if s["id"] not in seen:
            seen[s["id"]] = (s, [ch_id])
        else:
            seen[s["id"]][1].append(ch_id)
    
    return [(s, ch_ids) for s, ch_ids in seen.values()]

def build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions):
    embeds = []

    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=3)

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

    # 直播中的聯動
    for s, mentioned_ids in live_mentions:
        stream_id = s["id"]
        embeds.append({
            "title": f"{s['channel']['name']} 👥 {', '.join(mentioned_ids)}",
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFFD700,
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
    for s, mentioned_ids in upcoming_mentions:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            stream_id = s["id"]
            embeds.append({
                "title": f"{s['channel']['name']} 👥 {', '.join(mentioned_ids)}",
                "description": f"[{s['title']}](https://youtu.be/{stream_id})",
                "color": 0x90EE90,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def send_discord(live_streams, live_mentions, embeds):
    if not embeds:
        return
    
    # 優先使用主頻道直播的頭像
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    
    if live_filtered:
        # 有主頻道正在直播,用主頻道頭像
        channel_id = live_filtered[-1]["channel"]["id"]
        avatar_url = f"https://holodex.net/statics/channelImg/{channel_id}/100.png"
    elif live_mentions:
        # 只有聯動直播,用被提及的頻道頭像
        _, mentioned_ids = live_mentions[-1]
        avatar_url = f"https://holodex.net/statics/channelImg/{mentioned_ids[0]}/100.png"
    else:
        # 都沒有,用預設頭像
        avatar_url = "https://i.imgur.com/your-default-avatar.png"
    
    payload = {
        "username": "Holodex Notifier",
        "avatar_url": avatar_url,
        "embeds": embeds
    }
    requests.post(WEBHOOK_URL, json=payload)

def main():
    live_streams = fetch_live("live")
    upcoming_streams = fetch_live("upcoming")
    
    live_mentions = fetch_mentions("live")
    upcoming_mentions = fetch_mentions("upcoming")
    
    embeds = build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions)
    
    if embeds:
        send_discord(live_streams, live_mentions, embeds)

if __name__ == "__main__":
    main()
