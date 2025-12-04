import time, datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import find_one
from helper.progress import humanbytes
from helper.date import check_expi
from helper.database import uploadlimit, usertype


@Client.on_message(filters.private & filters.command(["myplan"]))
async def start(client, message):
    _newus = find_one(message.from_user.id)
    used = _newus.get("used_limit", 0)
    limit = int(_newus.get("uploadlimit", 0))  # convention: 0 = Unlimited
    user = _newus.get("usertype", "Free")
    ends = _newus.get("prexdate")

    # If subscription expired, downgrade to Free and set default uploadlimit if you want
    if ends:
        pre_check = check_expi(ends)
        if pre_check == False:
            uploadlimit(message.from_user.id, 2147483652)  # keep this or change to 0 for unlimited
            usertype(message.from_user.id, "Free")

    # Prepare readable fields
    if limit == 0:
        daily_text = "Unlimited"
        remain_text = "Unlimited"
    else:
        daily_text = humanbytes(limit)
        remain = max(0, limit - int(used))
        remain_text = humanbytes(remain)

    # Build message text — removed the "Daily Upload" limit if unlimited
    if ends is None:
        text = (
            f"<b>User ID :</b> <code>{message.from_user.id}</code> \n"
            f"<b>Name :</b> {message.from_user.mention} \n\n"
            f"<b>🏷 Plan :</b> {user} \n\n"
            f"✓ Upload 2GB Files \n"
            f"✓ Daily Upload : {daily_text} \n"
            f"✓ Today Used : {humanbytes(used)} \n"
            f"✓ Remain : {remain_text} \n"
            f"✓ Timeout : 2 Minutes \n"
            f"✓ Parallel process : Unlimited \n"
            f"✓ Time Gap : Yes \n\n"
            f"<b>Validity :</b> Lifetime"
        )
    else:
        normal_date = datetime.datetime.fromtimestamp(ends).strftime('%Y-%m-%d')
        text = (
            f"<b>User ID :</b> <code>{message.from_user.id}</code> \n"
            f"<b>Name :</b> {message.from_user.mention} \n\n"
            f"<b>🏷 Plan :</b> {user} \n\n"
            f"✓ High Priority \n"
            f"✓ Upload 4GB Files \n"
            f"✓ Daily Upload : {daily_text} \n"
            f"✓ Today Used : {humanbytes(used)} \n"
            f"✓ Remain : {remain_text} \n"
            f"✓ Timeout : 0 Second \n"
            f"✓ Parallel process : Unlimited \n"
            f"✓ Time Gap : Yes \n\n"
            f"<b>Your Plan Ends On :</b> {normal_date}"
        )

    if user == "Free":
        await message.reply(
            text,
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💳 Upgrade", callback_data="upgrade"),
                  InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]]
            ),
        )
    else:
        await message.reply(
            text,
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✖️ Cancel ✖️", callback_data="cancel")]]
            ),
        )
