import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

def fetch_live(status):
    try:
        r = requests.get(
            "https://holodex.net/api/v2/live",
            headers={"X-APIKEY": API_KEY},
            params={"status": status},
            timeout=10
        )
        
        # 印出除錯資訊
        print(f"[{status}] Status Code: {r.status_code}")
        
        # 檢查狀態碼
        if r.status_code != 200:
            print(f"[{status}] API 請求失敗: {r.status_code}")
            print(f"[{status}] Response: {r.text[:500]}")
            return []
        
        # 檢查回應是否為空
        if not r.text or r.text.strip() == "":
            print(f"[{status}] API 回應為空")
            return []
        
        return r.json()
    
    except requests.exceptions.JSONDecodeError as e:
        print(f"[{status}] JSON 解析錯誤: {e}")
        print(f"[{status}] 原始回應: {r.text[:500]}")
        return []
    except requests.exceptions.Timeout:
        print(f"[{status}] 請求超時")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[{status}] 請求錯誤: {e}")
        return []
    except Exception as e:
        print(f"[{status}] 未預期的錯誤: {e}")
        return []

def fetch_mentions(status):
    """獲取提到追蹤頻道的直播(聯動)"""
    all_mentions = []
    for channel_id in CHANNELS.keys():
        try:
            r = requests.get(
                "https://holodex.net/api/v2/live",
                headers={"X-APIKEY": API_KEY},
                params={
                    "status": status,
                    "mentioned_channel_id": channel_id
                },
                timeout=10
            )
            
            if r.status_code != 200:
                print(f"[mentions-{channel_id}] 請求失敗: {r.status_code}")
                continue
            
            if not r.text or r.text.strip() == "":
                continue
            
            mentions = r.json()
            # 過濾掉已經在 CHANNELS 列表中的頻道(避免重複)
            filtered = [(s, CHANNELS[channel_id]) for s in mentions if s["channel"]["id"] not in CHANNELS.keys()]
            all_mentions.extend(filtered)
        
        except Exception as e:
            print(f"[mentions-{channel_id}] 錯誤: {e}")
            continue
    
    # 去重
    seen = {}
    for s, nickname in all_mentions:
        if s["id"] not in seen:
            seen[s["id"]] = (s, [nickname])
        else:
            seen[s["id"]][1].append(nickname)
    
    return [(s, nicknames) for s, nicknames in seen.values()]

def build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions):
    embeds = []

    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)

    # 直播中
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS.keys()]
    for s in live_filtered:
        stream_id = s["id"]
        embeds.append({
            "title": s["channel"]["name"],
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFF69B4,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
        })

    # 直播中的聯動
    for s, mentioned_nicknames in live_mentions:
        stream_id = s["id"]
        embeds.append({
            "title": f"{s['channel']['name']} 👥 {', '.join(mentioned_nicknames)}",
            "description": f"[{s['title']}](https://youtu.be/{stream_id})",
            "color": 0xFFB6C1,
            "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
        })

    # 一小時後開播
    for s in upcoming_streams:
        if s["channel"]["id"] not in CHANNELS.keys():
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
    for s, mentioned_nicknames in upcoming_mentions:
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            stream_id = s["id"]
            embeds.append({
                "title": f"{s['channel']['name']} 👥 {', '.join(mentioned_nicknames)}",
                "description": f"[{s['title']}](https://youtu.be/{stream_id})",
                "color": 0xADD8E6,
                "thumbnail": {"url": f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"}
            })

    return embeds

def send_discord(live_streams, live_mentions, embeds):
    if not embeds:
        return
    
    # 優先使用主頻道直播的頭像
    live_filtered = [s for s in live_streams if s["channel"]["id"] in CHANNELS.keys()]
    
    if live_filtered:
        # 有主頻道正在直播,用主頻道頭像
        channel_id = live_filtered[-1]["channel"]["id"]
        avatar_url = f"https://holodex.net/statics/channelImg/{channel_id}/100.png"
    elif live_mentions:
        # 只有聯動直播,用被提及的頻道頭像
        _, mentioned_nicknames = live_mentions[-1]
        # 從暱稱找回 channel_id
        channel_id = [k for k, v in CHANNELS.items() if v == mentioned_nicknames[0]][0]
        avatar_url = f"https://holodex.net/statics/channelImg/{channel_id}/100.png"
    else:
        # 都沒有,用預設頭像
        avatar_url = "https://i.imgur.com/your-default-avatar.png"
    
    payload = {
        "username": "Holodex Notifier",
        "avatar_url": avatar_url,
        "embeds": embeds
    }
    
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 204:
            print("Discord 通知發送成功")
        else:
            print(f"Discord 通知發送失敗: {r.status_code}")
    except Exception as e:
        print(f"Discord 通知發送錯誤: {e}")

def main():
    print(f"=== 開始執行 {datetime.now(TWTZ).strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    live_streams = fetch_live("live")
    print(f"找到 {len(live_streams)} 個直播中的串流")
    
    upcoming_streams = fetch_live("upcoming")
    print(f"找到 {len(upcoming_streams)} 個即將開始的串流")
    
    live_mentions = fetch_mentions("live")
    print(f"找到 {len(live_mentions)} 個直播中的聯動")
    
    upcoming_mentions = fetch_mentions("upcoming")
    print(f"找到 {len(upcoming_mentions)} 個即將開始的聯動")
    
    embeds = build_embeds(live_streams, upcoming_streams, live_mentions, upcoming_mentions)
    print(f"建立了 {len(embeds)} 個通知")
    
    if embeds:
        send_discord(live_streams, live_mentions, embeds)
    else:
        print("沒有需要發送的通知")
    
    print("=== 執行完成 ===")

if __name__ == "__main__":
    main()
