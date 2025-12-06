# rename_bot_handlers_unlimited.py
# Modified handler: daily upload limit removed (unlimited).
# Keeps an optional single-file safety check (2 GiB).
# Handles channel posts safely (won't crash on message.from_user == None).

from datetime import date as date_
import datetime
import os, time, asyncio
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import humanize
from pyrogram.file_id import FileId

# Keep imports from your helper module; some functions may be unused but harmless.
from helper.database import (
    insert, find_one, used_limit, usertype,
    uploadlimit, addpredata, total_rename, total_size, daily as daily_, botdata
)
from helper.date import check_expi
from config import *

bot_username = BOT_USERNAME
log_channel = LOG_CHANNEL
botid = BOT_TOKEN.split(":")[0]

# single-file safety limit (keep or increase/remove as needed)
MAX_SINGLE_FILE = 2 * 1024 * 1024 * 1024  # 2 GiB


@Client.on_message(filters.private & filters.command(["start"]))
async def start(client, message):
    user_id = message.chat.id
    insert(int(user_id))  # Ensure user exists in DB

    # optional loading sticker (ignore errors)
    try:
        loading_msg = await message.reply_sticker("CAACAgIAAxkBAALmzGXSSt3ppnOsSl_spnAP8wHC26jpAAJEGQACCOHZSVKp6_XqghKoHgQ")
        await asyncio.sleep(2)
        await loading_msg.delete()
    except Exception:
        pass

    txt = f"""Hello {message.from_user.mention} 

➻ This Is An Advanced And Yet Powerful Rename Bot.
➻ Using This Bot You Can Rename And Change Thumbnail Of Your Files.
➻ You Can Also Convert Video To File And File To Video.
➻ This Bot Also Supports Custom Thumbnail And Custom Caption.

<b>Bot Is Made By @Madflix_Bots</b>"""
    
    await message.reply_photo(
        photo=BOT_PIC,
        caption=txt,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates", url="https://t.me/Madflix_Bots"),
             InlineKeyboardButton("💬 Support", url="https://t.me/MadflixBots_Support")],
            [InlineKeyboardButton("🛠️ Help", callback_data='help'),
             InlineKeyboardButton("❤️‍🩹 About", callback_data='about')],
            [InlineKeyboardButton("🧑‍💻 Developer 🧑‍💻", url="https://t.me/CallAdminRobot")]
        ])
    )


@Client.on_message((filters.private & (filters.document | filters.audio | filters.video)) |
                   (filters.channel & (filters.document | filters.audio | filters.video)))
async def send_doc(client, message):
    """
    Handles incoming files (private and channel). Daily upload limit removed (unlimited).
    Keeps single-file safety check (2 GiB). Flood control default here is 0 seconds (no wait).
    """

    # Determine a safe user identifier. For channel posts message.from_user may be None.
    if message.from_user:
        user_id = message.from_user.id
    else:
        # fallback to chat id for channels/groups (safe placeholder)
        user_id = message.chat.id

    update_channel = FORCE_SUBS

    # If forcing subscription, only check when we have a real user (message.from_user present).
    if update_channel and message.from_user:
        try:
            await client.get_chat_member(update_channel, user_id)
        except UserNotParticipant:
            _newus = find_one(user_id) or {}
            user_plan = _newus.get("usertype", "Free")
            await message.reply_text(
                "<b>Hello Dear \n\nYou Need To Join In My Channel To Use Me\n\nKindly Please Join Channel</b>",
                reply_to_message_id=message.id,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔺 Update Channel 🔺", url=f"https://t.me/{update_channel}")]]
                )
            )
            # send admin log (safe attribute access)
            try:
                first = message.from_user.first_name if message.from_user else ""
                last = message.from_user.last_name if message.from_user else ""
                username = f"@{message.from_user.username}" if (message.from_user and message.from_user.username) else "N/A"
                mention = message.from_user.mention if message.from_user else "N/A"
                await client.send_message(
                    log_channel,
                    f"<b><u>New User Started The Bot</u></b>\n\n"
                    f"<b>User ID</b> : `{user_id}`\n"
                    f"<b>First Name</b> : {first}\n"
                    f"<b>Last Name</b> : {last}\n"
                    f"<b>User Name</b> : {username}\n"
                    f"<b>User Mention</b> : {mention}\n"
                    f"<b>User Plan</b> : {user_plan}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔺 Restrict User (PM) 🔺", callback_data="ceasepower")]]
                    )
                )
            except Exception:
                pass
            return

    # Update bot stats (non-blocking)
    try:
        botdata(int(botid))
    except Exception:
        pass

    bot_info = find_one(int(botid)) or {}
    prrename = bot_info.get('total_rename', 0)
    prsize = bot_info.get('total_size', 0)

    # Load user data safely (avoid None)
    user_data = find_one(user_id) or {}
    used_date = user_data.get("date", 0)
    buy_date = user_data.get("prexdate", None)
    daily = user_data.get("daily", 0)
    user_type = user_data.get("usertype", "Free")

    # Flood control effectively off (LIMIT = 0 for Free)
    c_time = time.time()
    LIMIT = 0 if user_type == "Free" else 10
    then = used_date + LIMIT
    left = round(then - c_time)
    ltime = str(datetime.timedelta(seconds=max(left, 0)))

    if left > 0:
        await message.reply_text(
            f"<b>Sorry! Flood Control Active. Please Wait For {ltime}.</b>",
            reply_to_message_id=message.id
        )
        return

    # Process file
    media = await client.get_messages(message.chat.id, message.id)
    file = media.document or media.video or media.audio
    if not file:
        await message.reply_text("No file found.", reply_to_message_id=message.id)
        return

    try:
        dcid = FileId.decode(file.file_id).dc_id
    except Exception:
        dcid = "N/A"

    filename = getattr(file, "file_name", "unknown")
    file_size = getattr(file, "file_size", 0)
    file_id = file.file_id

    # --- DAILY QUOTA REMOVED ---
    # Previously you had per-day quota checks here. Those are removed so uploads are unlimited per day.
    # If other handlers expect uploadlimit/used_limit/daily, ensure they handle missing values gracefully.

    # Optional single-file safety check (kept)
    if file_size > MAX_SINGLE_FILE:
        await message.reply_text(
            "You Can't Upload More Than 2GB File.\nAdjust server/storage limits if you need larger files.",
            reply_to_message_id=message.id
        )
        return

    # Update stats (non-blocking)
    try:
        total_rename(int(botid), prrename)
        total_size(int(botid), prsize, file_size)
    except Exception:
        pass

    # Reply with options (no "Upgrade" button or message anywhere)
    await message.reply_text(
        f"__What Do You Want Me To Do With This File?__\n\n"
        f"**File Name** :- `{filename}`\n"
        f"**File Size** :- {humanize.naturalsize(file_size)}\n"
        f"**DC ID** :- {dcid}",
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Rename", callback_data="rename"),
             InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
        ])
)
