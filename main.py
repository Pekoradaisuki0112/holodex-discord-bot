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
    live_info = []  # 記錄正在直播的資訊,用來決定頭像

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
        live_info.append({
            "type": "direct",
            "channel_id": s["channel"]["id"]
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
        live_info.append({
            "type": "mentioned",
            "mentioned_channel_id": mentioned_ids[0]
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

    return embeds, live_info

def send_discord(embeds, live_info):
    if not embeds:
        return
    
    # 根據最新的「正在直播」決定頭像
    if live_info:
        latest_live = live_info[-1]
        if latest_live["type"] == "direct":
            avatar_url = f"https://holodex.net/statics/channelImg/{latest_live['channel_id']}/100.png"
        else:  # mentioned
            avatar_url = f"https://holodex.net/statics/channelImg/{latest_live['mentioned_channel_id']}/100.png"
    else:
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
    
    embeds, live_info = build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions)
    
    if embeds:
        send_discord(embeds, live_info)

if __name__ == "__main__":
    main()
