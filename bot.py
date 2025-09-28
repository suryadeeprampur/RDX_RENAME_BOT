from pyrogram import Client, idle
from config import *
import pyrogram.utils
import asyncio
from aiohttp import web

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

# -------------------------------
# Main Bot Client
# -------------------------------
bot = Client(
    "RenamerBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    plugins=dict(root="plugins")
)

# -------------------------------
# Web server (optional, for health checks)
# -------------------------------
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is running fine!")

    app = web.Application()
    app.router.add_get("/", handle)
    return app

async def start_web():
    runner = web.AppRunner(await web_server())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

# -------------------------------
# Run Bot
# -------------------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_web())
    bot.start()
    idle()
    bot.stop()
