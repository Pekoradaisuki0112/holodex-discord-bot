import requests, json, os
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

TWTZ = timezone(timedelta(hours=8))

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 調整成你的系統字體
FONT_SIZE = 24

def fetch_live(status):
    url = "https://holodex.net/api/v2/live"
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params={"status": status})
    return r.json()

def create_composite_image(streams, title):
    # 設定圖片寬高
    width, height_per_item = 600, 120
    height = height_per_item * len(streams) + 50  # 額外留空間放區塊標題
    image = Image.new("RGB", (width, height), color=(30,30,30))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # 區塊標題
    draw.text((10, 10), title, fill=(255,255,255), font=font)

    y_offset = 50
    for s in streams:
        # 畫文字
        draw.text((10, y_offset), s['channel']['name'], fill=(255,255,255), font=font)
        draw.text((10, y_offset+30), s['title'], fill=(200,200,200), font=font)

        # 抓封面縮圖
        stream_id = s['id']
        thumb_url = f"https://img.youtube.com/vi/{stream_id}/mqdefault.jpg"
        resp = requests.get(thumb_url)
        thumb = Image.open(BytesIO(resp.content)).convert("RGB")
        thumb = thumb.resize((100, 100))
        image.paste(thumb, (480, y_offset))

        y_offset += height_per_item

    # 存成 BytesIO
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output

def send_discord_image(img_bytes):
    files = {"file": ("streams.png", img_bytes, "image/png")}
    data = {
        "username": "Holodex Notifier",
        "avatar_url": "https://i.imgur.com/your-default-avatar.png"
    }
    requests.post(WEBHOOK_URL, data=data, files=files)

def main():
    live_streams = [s for s in fetch_live("live") if s["channel"]["id"] in CHANNELS]
    upcoming_streams = []
    now = datetime.now(TWTZ)
    one_hour_later = now + timedelta(hours=1)
    for s in fetch_live("upcoming"):
        if s["channel"]["id"] not in CHANNELS:
            continue
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00")).astimezone(TWTZ)
        if now <= start_time <= one_hour_later:
            upcoming_streams.append(s)

    # 直播中
    if live_streams:
        img_live = create_composite_image(live_streams, "🎥 直播中")
        send_discord_image(img_live)

    # 一小時後
    if upcoming_streams:
        img_upcoming = create_composite_image(upcoming_streams, "⏰ 一小時後開播")
        send_discord_image(img_upcoming)

if __name__ == "__main__":
    main()

