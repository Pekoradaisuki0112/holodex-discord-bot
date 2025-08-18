import requests, json, os

API_KEY = os.environ["HOLODEX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

with open("channels.json") as f:
    CHANNELS = json.load(f)

def main():
    url = "https://holodex.net/api/v2/live"
    params = {"channels": ",".join(CHANNELS), "status": "upcoming"}
    headers = {"X-APIKEY": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    for s in r.json():
        msg = f"🎉 {s['channel']['name']} 即將開台！\n{s['title']}\n🔗 https://youtu.be/{s['id']}"
        requests.post(WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    main()
Add main.py script
