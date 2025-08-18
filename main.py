import discord
import asyncio
import requests
from discord.ext import tasks

TOKEN = "你的DISCORD_BOT_TOKEN"
CHANNEL_ID = 1234567890  # 改成你的頻道ID
API_KEY = "你的YOUTUBE_API_KEY"
VTUBER_IDS = ["UCxxxxxxx", "UCyyyyyyy"]  # 追蹤的VTuber channel IDs

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def fetch_live(status="live"):
    """抓直播資料：status 可選 live 或 upcoming"""
    streams = []
    for cid in VTUBER_IDS:
        url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={cid}&type=video&eventType={status}&key={API_KEY}"
        )
        resp = requests.get(url).json()
        if "items" in resp:
            for item in resp["items"]:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                channel_name = item["snippet"]["channelTitle"]
                thumbnail = item["snippet"]["thumbnails"].get("maxres") or \
                            item["snippet"]["thumbnails"].get("high") or \
                            item["snippet"]["thumbnails"].get("default")
                streams.append({
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": channel_name,
                    "thumbnail": thumbnail["url"]
                })
    return streams

async def notify(streams, prefix, channel):
    if not streams:
        return
    # 分開段落
    await channel.send("━━━━━━━━━━━━━━━━━━━━━━━")

    for stream in streams:
        embed = discord.Embed(
            title=f"{prefix}：{stream['title']}",
            url=stream["url"],
            description=f"頻道：{stream['channel']}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=stream["thumbnail"])  # 小圖設直播封面
        await channel.send(embed=embed)

@tasks.loop(minutes=20)
async def check_streams():
    channel = client.get_channel(CHANNEL_ID)

    # 先抓正在直播
    live_streams = fetch_live("live")
    await notify(live_streams, prefix="正在開台", channel=channel)

    # 空一大段
    await channel.send("\n\n")

    # 再抓即將開台
    upcoming_streams = fetch_live("upcoming")
    await notify(upcoming_streams, prefix="即將開台", channel=channel)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_streams.start()

client.run(TOKEN)
