import requests, json, os
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

def main():
    url = "https://holodex.net/api/v2/live"
    params = {"channels": ",".join(CHANNELS), "status": "upcoming"}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    now = datetime.now(timezone.utc)
    one_hour_later = now + timedelta(hours=1)

    for s in r.json():
        start_time = datetime.fromisoformat(s["start_scheduled"].replace("Z","+00:00"))
        if now <= start_time <= one_hour_later:
            msg = (
                f"🎉 {s['channel']['name']} 即將開台！\n"
                f"{s['title']}\n"
                f"🕒 {start_time.strftime('%H:%M UTC')}\n"
                f"🔗 https://youtu.be/{s['id']}"
            )
            requests.post(WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    main()
