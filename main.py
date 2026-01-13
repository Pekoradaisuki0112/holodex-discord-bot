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
    three_hours_later = now + timedelta(hours=3)

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
            "color": 0xFF69B4,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
        })

    # 三小時後開播 - 主頻道
    for s in upcoming_streams:
        if s["channel"]["id"] in CHANNELS:
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if now <= start_time <= three_hours_later:
                stream_id = s["id"]
                time_str = start_time.strftime("%H:%M")
                embeds.append({
                    "title": s["channel"]["name"],
                    "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                    "color": 0x00BFFF,
                    "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
                })

    # 三小時後開播 - 被提及的頻道
    for s in mentioned_upcoming_streams:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= three_hours_later:
            stream_id = s["id"]
            time_str = start_time.strftime("%H:%M")
            embeds.append({
                "title": f"{s['channel']['name']} (提及)",
                "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                "color": 0x00BFFF,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def get_avatar_url(live_streams, mentioned_live_streams):
    """決定 webhook 的頭像"""
    # 優先使用主頻道直播
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    if live_filtered:
        return live_filtered[-1]["channel"]["photo"]
    
    # 如果沒有主頻道直播，使用被提及頻道中的主頻道頭像
    if mentioned_live_streams:
        # 從 mentioned_live_streams 找出被提及的主頻道 ID
        for s in mentioned_live_streams:
            mentions = s.get("mentions", [])
            for mention in mentions:
                if mention in CHANNELS:
                    # 直接用 channel ID 組頭像 URL
                    return f"https://holodex.net/statics/channelImg/{mention}/100.png"
    
    # 預設頭像
    return "https://i.imgur.com/your-default-avatar.png"

def send_discord(live_streams, mentioned_live_streams, embeds):
    if not embeds:
        print("沒有新的直播或即將開播的串流")
        return

    # 判斷最新正在直播的是主頻道還是被提及
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    
    if live_filtered:
        # 最新是主頻道直播，用主頻道頭像
        channel_id = live_filtered[-1]["channel"]["id"]
    elif mentioned_live_streams:
        # 最新是被提及的直播，用被提及的主頻道頭像
        # 從 mentions 中找出我們追隨的頻道
        last_stream = mentioned_live_streams[-1]
        mentioned_ids = [m["id"] for m in last_stream.get("mentions", [])]
        # 找出在我們 CHANNELS 列表中的頻道
        our_channel = next((cid for cid in mentioned_ids if cid in CHANNELS), None)
        channel_id = our_channel if our_channel else list(CHANNELS)[0]  # fallback 到第一個主頻道
    else:
        channel_id = None
    
    avatar_url = f"https://holodex.net/statics/channelImg/{channel_id}/100.png" if channel_id else "https://i.imgur.com/your-default-avatar.png"

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
    send_discord(live_streams, mentioned_live_streams, embeds)  # 多傳一個參數

if __name__ == "__main__":
    main()
