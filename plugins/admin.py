from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from pyrogram import Client, filters
from helper.date import add_date
from helper.database import uploadlimit, usertype, addpre


# WARN USER
@Client.on_message(filters.private & filters.user(OWNER) & filters.command(["warn"]))
async def warn(c, m):
    if len(m.command) >= 3:
        try:
            user_id = m.text.split(' ', 2)[1]
            reason = m.text.split(' ', 2)[2]
            await m.reply_text("✅ User Notified Successfully")
            await c.send_message(chat_id=int(user_id), text=reason)
        except:
            await m.reply_text("❌ Failed to notify user")
    else:
        await m.reply_text("⚠️ Usage: /warn <user_id> <reason>")


# ADD PREMIUM MENU
@Client.on_message(filters.private & filters.user(OWNER) & filters.command(["addpremium"]))
async def buypremium(bot, message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a user's message with /addpremium to upgrade them.")
        return

    user_id = message.reply_to_message.from_user.id

    await message.reply_text(
        "🦋 Select Plan To Upgrade...",
        quote=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 Basic", callback_data=f"vip1:{user_id}")],
            [InlineKeyboardButton("⚡ Standard", callback_data=f"vip2:{user_id}")],
            [InlineKeyboardButton("💎 Pro", callback_data=f"vip3:{user_id}")],
            [InlineKeyboardButton("✖️ Cancel ✖️", callback_data="cancel")]
        ])
    )


# CEASE POWER MENU
@Client.on_message(filters.private & filters.user(OWNER) & filters.command(["ceasepower"]))
async def ceasepremium(bot, message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a user's message with /ceasepower to downgrade them.")
        return

    user_id = message.reply_to_message.from_user.id

    await message.reply_text(
        "😁 Power Cease Mode...",
        quote=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Limit 1GB", callback_data=f"cp1:{user_id}")],
            [InlineKeyboardButton("All Power Cease", callback_data=f"cp2:{user_id}")],
            [InlineKeyboardButton("✖️ Cancel ✖️", callback_data="cancel")]
        ])
    )


# RESET POWER MENU
@Client.on_message(filters.private & filters.user(OWNER) & filters.command(["resetpower"]))
async def resetpower(bot, message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a user's message with /resetpower.")
        return

    user_id = message.reply_to_message.from_user.id

    await message.reply_text(
        text="Do you really want to reset daily limit to default (2GB)?",
        quote=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• Yes ! Set As Default •", callback_data=f"dft:{user_id}")],
            [InlineKeyboardButton("❌ Cancel ❌", callback_data="cancel")]
        ])
    )


# PREMIUM POWER MODE
@Client.on_callback_query(filters.regex(r'vip1:(\d+)'))
async def vip1(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 21474836500)
    usertype(user_id, "🪙 Basic")
    addpre(user_id)
    await update.message.edit("✅ Added Successfully To Premium Upload Limit 20 GB")
    await bot.send_message(user_id, "🎉 You are upgraded to Basic. Check your plan here /myplan")


@Client.on_callback_query(filters.regex(r'vip2:(\d+)'))
async def vip2(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 53687091200)
    usertype(user_id, "⚡ Standard")
    addpre(user_id)
    await update.message.edit("✅ Added Successfully To Premium Upload Limit 50 GB")
    await bot.send_message(user_id, "🎉 You are upgraded to Standard. Check your plan here /myplan")


@Client.on_callback_query(filters.regex(r'vip3:(\d+)'))
async def vip3(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 107374182400)
    usertype(user_id, "💎 Pro")
    addpre(user_id)
    await update.message.edit("✅ Added Successfully To Premium Upload Limit 100 GB")
    await bot.send_message(user_id, "🎉 You are upgraded to Pro. Check your plan here /myplan")


# CEASE POWER MODE
@Client.on_callback_query(filters.regex(r'cp1:(\d+)'))
async def cp1(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 2147483652)
    usertype(user_id, "⚠️ Account Downgraded")
    addpre(user_id)
    await update.message.edit("✅ Added Successfully To Upload Limit 2GB")
    await bot.send_message(user_id, "⚠️ You are downgraded to 2GB. Check your plan here /myplan\n\n**Contact Admin :** @calladminrobot")


@Client.on_callback_query(filters.regex(r'cp2:(\d+)'))
async def cp2(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 0)
    usertype(user_id, "⚠️ Account Downgraded")
    addpre(user_id)
    await update.message.edit("✅ Added Successfully To Upload Limit 0GB")
    await bot.send_message(user_id, "⚠️ You are downgraded to 0GB. Check your plan here /myplan\n\n**Contact Admin :** @calladminrobot")


# RESET POWER MODE
@Client.on_callback_query(filters.regex(r'dft:(\d+)'))
async def dft(bot, update):
    user_id = int(update.data.split(":")[1])
    uploadlimit(user_id, 2147483652)
    usertype(user_id, "🆓 Free")
    addpre(user_id)
    await update.message.edit("✅ Daily Data Limit Has Been Reset Successfully (2GB)")
    await bot.send_message(
        user_id,
        "✅ Your Daily Data Limit Has Been Reset to 2GB.\n\nCheck your plan here /myplan\n\n**Contact Admin :** @CallAdminRobot"
	)
	
