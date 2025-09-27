# PREMIUM POWER MODE @JISHUDEVELOPER

@Client.on_callback_query(filters.regex('vip1'))
async def vip1(bot, update):
    try:
        if not update.message.reply_to_message:
            await update.answer("⚠️ Please reply to a user ID message!", show_alert=True)
            return

        # Extract user_id
        user_id = update.message.reply_to_message.text.replace("/addpremium", "").strip()

        if not user_id.isdigit():
            await update.answer("❌ Invalid user ID!", show_alert=True)
            return

        inlimit = 21474836500  # 20GB
        uploadlimit(int(user_id), inlimit)
        usertype(int(user_id), "🪙 Basic")
        addpre(int(user_id))

        await update.message.edit("✅ Added Successfully To Premium Upload Limit **20 GB**")
        await bot.send_message(int(user_id),
                               "🎉 Hey! You are upgraded to **Basic Plan**.\nCheck your plan with /myplan")
    except Exception as e:
        await update.message.reply(f"⚠️ Error: {e}")


@Client.on_callback_query(filters.regex('vip2'))
async def vip2(bot, update):
    try:
        if not update.message.reply_to_message:
            await update.answer("⚠️ Please reply to a user ID message!", show_alert=True)
            return

        user_id = update.message.reply_to_message.text.replace("/addpremium", "").strip()

        if not user_id.isdigit():
            await update.answer("❌ Invalid user ID!", show_alert=True)
            return

        inlimit = 53687091200  # 50GB
        uploadlimit(int(user_id), inlimit)
        usertype(int(user_id), "⚡ Standard")
        addpre(int(user_id))

        await update.message.edit("✅ Added Successfully To Premium Upload Limit **50 GB**")
        await bot.send_message(int(user_id),
                               "🎉 Hey! You are upgraded to **Standard Plan**.\nCheck your plan with /myplan")
    except Exception as e:
        await update.message.reply(f"⚠️ Error: {e}")


@Client.on_callback_query(filters.regex('vip3'))
async def vip3(bot, update):
    try:
        if not update.message.reply_to_message:
            await update.answer("⚠️ Please reply to a user ID message!", show_alert=True)
            return

        user_id = update.message.reply_to_message.text.replace("/addpremium", "").strip()

        if not user_id.isdigit():
            await update.answer("❌ Invalid user ID!", show_alert=True)
            return

        inlimit = 107374182400  # 100GB
        uploadlimit(int(user_id), inlimit)
        usertype(int(user_id), "💎 Pro")
        addpre(int(user_id))

        await update.message.edit("✅ Added Successfully To Premium Upload Limit **100 GB**")
        await bot.send_message(int(user_id),
                               "🎉 Hey! You are upgraded to **Pro Plan**.\nCheck your plan with /myplan")
    except Exception as e:
        await update.message.reply(f"⚠️ Error: {e}")
	
