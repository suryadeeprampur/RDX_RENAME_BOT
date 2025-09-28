from datetime import date as date_
import datetime
import os, time, asyncio
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import humanize
from pyrogram.file_id import FileId
from helper.database import (insert, find_one, used_limit, usertype,
                             uploadlimit, addpredata, total_rename, total_size, daily as daily_)
from helper.date import check_expi
from config import *

bot_username = BOT_USERNAME
log_channel = LOG_CHANNEL
botid = BOT_TOKEN.split(":")[0]


@Client.on_message(filters.private & filters.command(["start"]))
async def start(client, message):
    user_id = message.chat.id
    insert(int(user_id))  # Ensure user exists in DB

    loading_msg = await message.reply_sticker("CAACAgIAAxkBAALmzGXSSt3ppnOsSl_spnAP8wHC26jpAAJEGQACCOHZSVKp6_XqghKoHgQ")
    await asyncio.sleep(2)
    await loading_msg.delete()

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
    user_id = message.from_user.id
    update_channel = FORCE_SUBS

    # Check if user joined update channel
    if update_channel:
        try:
            await client.get_chat_member(update_channel, user_id)
        except UserNotParticipant:
            _newus = find_one(user_id)
            user_plan = _newus.get("usertype", "Free")
            await message.reply_text(
                "<b>Hello Dear \n\nYou Need To Join In My Channel To Use Me\n\nKindly Please Join Channel</b>",
                reply_to_message_id=message.id,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔺 Update Channel 🔺", url=f"https://t.me/{update_channel}")]]
                )
            )
            await client.send_message(
                log_channel,
                f"<b><u>New User Started The Bot</u></b>\n\n"
                f"<b>User ID</b> : `{user_id}`\n"
                f"<b>First Name</b> : {message.from_user.first_name}\n"
                f"<b>Last Name</b> : {message.from_user.last_name}\n"
                f"<b>User Name</b> : @{message.from_user.username}\n"
                f"<b>User Mention</b> : {message.from_user.mention}\n"
                f"<b>User Plan</b> : {user_plan}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔺 Restrict User (PM) 🔺", callback_data="ceasepower")]]
                )
            )
            return

    # Bot stats
    botdata(int(botid))
    bot_info = find_one(int(botid))
    prrename = bot_info.get('total_rename', 0)
    prsize = bot_info.get('total_size', 0)

    # User stats (with safe defaults)
    user_data = find_one(user_id)
    used_date = user_data.get("date", 0)
    buy_date = user_data.get("prexdate", None)
    daily = user_data.get("daily", 0)
    user_type = user_data.get("usertype", "Free")

    c_time = time.time()
    LIMIT = 120 if user_type == "Free" else 10
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
    dcid = FileId.decode(file.file_id).dc_id
    filename = file.file_name
    file_size = file.file_size
    file_id = file.file_id

    # Daily limit handling
    user_used = user_data.get("used_limit", 0)
    user_limit = user_data.get("uploadlimit", 2147483648)
    today_epoch = int(time.mktime(time.strptime(str(date_.today()), '%Y-%m-%d')))
    expi = daily - today_epoch

    if expi != 0:
        daily_(user_id, today_epoch)
        used_limit(user_id, 0)

    remain = user_limit - user_used
    if remain < file_size:
        await message.reply_text(
            f"100% Of Daily {humanize.naturalsize(user_limit)} Data Quota Exhausted.\n\n"
            f"<b>File Size Detected :</b> {humanize.naturalsize(file_size)}\n"
            f"<b>Used Daily Limit :</b> {humanize.naturalsize(user_used)}\n\n"
            f"You Have Only <b>{humanize.naturalsize(remain)}</b> Left.\n\n"
            f"If You Want To Rename Large File Upgrade Your Plan",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Upgrade", callback_data="upgrade")]])
        )
        return

    # File size check > 2GB
    if file_size > 2147483648:
        await message.reply_text(
            "You Can't Upload More Than 2GB File\nUpgrade Your Plan To Rename Files Larger Than 2GB"
        )
        return

    # Update stats
    total_rename(int(botid), prrename)
    total_size(int(botid), prsize, file_size)

    # Reply with options
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
