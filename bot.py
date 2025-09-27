from pyrogram import Client, idle
from plugins.cb_data import app as Client2
from config import *
import pyrogram.utils
import asyncio
from aiohttp import web

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

bot = Client(
    "Renamer",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    plugins=dict(root="plugins")
)


async def start_web():
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()


if STRING:
    apps = [Client2, bot]
    for app in apps:
        app.start()
    asyncio.get_event_loop().run_until_complete(start_web())
    idle()
    for app in apps:
        app.stop()
else:
    bot.run()

# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
