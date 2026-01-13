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
    three_hours_later = now + timedelta(hours=3)  # 改成3小時

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

    # 3小時後開播 - 主頻道
    for s in upcoming_streams:
        if s["channel"]["id"] in CHANNELS:
            start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
            if now <= start_time <= three_hours_later:  # 改成3小時
                stream_id = s["id"]
                time_str = start_time.strftime("%H:%M")
                embeds.append({
                    "title": s["channel"]["name"],
                    "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                    "color": 0x00BFFF,
                    "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
                })

    # 3小時後開播 - 被提及的頻道
    for s in mentioned_upcoming_streams:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= three_hours_later:  # 改成3小時
            stream_id = s["id"]
            time_str = start_time.strftime("%H:%M")
            embeds.append({
                "title": f"{s['channel']['name']} (提及)",
                "description": f"[{s['title']}](https://youtu.be/{stream_id})\n預計開播時間: {time_str}",
                "color": 0xADD8E6,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def send_discord(live_streams, mentioned_live_streams, embeds):
    if not embeds:
        print("沒有新的直播或即將開播的串流")
        return

    # 優先使用主頻道的頭像
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS]
    
    if live_filtered:
        # 有主頻道直播，用主頻道頭像
        avatar_url = live_filtered[-1]["channel"]["photo"]
    else:
        # 沒有主頻道直播，找出被提及的主頻道ID
        avatar_url = "https://i.imgur.com/your-default-avatar.png"
        mentioned_channel_id = None
        
        for s in mentioned_live_streams:
            if "mentions" in s:
                for mention in s["mentions"]:
                    if mention["id"] in CHANNELS:
                        mentioned_channel_id = mention["id"]
                        break
            if mentioned_channel_id:
                break
        
        # 用 API 抓被提及的主頻道頭像
        if mentioned_channel_id:
            try:
                r = requests.get(
                    f"https://holodex.net/api/v2/channels/{mentioned_channel_id}",
                    headers={"X-APIKEY": API_KEY},
                    timeout=10
                )
                r.raise_for_status()
                channel_data = r.json()
                avatar_url = channel_data.get("photo", avatar_url)
            except requests.RequestException as e:
                print(f"無法獲取頻道頭像: {e}")

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
    send_discord(live_streams, mentioned_live_streams, embeds)

if __name__ == "__main__":
    main()
