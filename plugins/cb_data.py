# rename_handlers.py
from helper.progress import progress_for_pyrogram, humanbytes
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.database import *
import os
import random
from PIL import Image
import time
from datetime import timedelta
from helper.ffmpeg import take_screen_shot, fix_thumb
from helper.set import escape_invalid_curly_brackets
from config import *
from plugins.metadata import get_user_meta  # new import to pull saved metadata

log_channel = LOG_CHANNEL
app = Client("test", api_id=API_ID, api_hash=API_HASH, session_string=STRING)


# -------------------------
# Cancel callback
# -------------------------
@app.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
    except:
        return


# -------------------------
# Rename start (asks for new filename)
# -------------------------
@app.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    date_fa = str(update.message.date)
    pattern = '%Y-%m-%d %H:%M:%S'
    try:
        date = int(time.mktime(time.strptime(date_fa, pattern)))
    except:
        date = int(time.time())
    chat_id = update.message.chat.id
    id = update.message.reply_to_message_id
    try:
        await update.message.delete()
    except:
        pass
    await update.message.reply_text(
        "__Please Enter The New Filename...__\n\nNote:- Extension Not Required",
        reply_to_message_id=id,
        reply_markup=ForceReply(True)
    )
    # update usage/date tracking if you have this helper
    try:
        dateupdate(chat_id, date)
    except:
        pass


# -------------------------
# Document handler (send as document with metadata caption)
# -------------------------
@app.on_callback_query(filters.regex("doc"))
async def doc(bot, update):
    # new_name is the message text that contains "something:-newfilename"
    new_name = update.message.text or ""
    used_ = find_one(update.from_user.id)
    used = used_.get("used_limit", 0) if used_ else 0
    # name format expected: something:-<filename>
    name = new_name.split(":-")
    if len(name) < 2:
        await update.message.edit("Invalid name format.")
        return
    new_filename = name[1].strip()
    file_path = f"downloads/{new_filename}"

    message = update.message.reply_to_message
    file = message.document or message.video or message.audio
    ms = await update.message.edit("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅ`")

    # usage accounting - compute total, then set
    try:
        total_used = used + int(file.file_size)
        used_limit(update.from_user.id, total_used)
    except Exception:
        pass

    c_time = time.time()
    try:
        path = await bot.download_media(
            message=file,
            progress=progress_for_pyrogram,
            progress_args=("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....`", ms, c_time)
        )
    except Exception as e:
        # revert usage on failure
        try:
            used_limit(update.from_user.id, used)
        except:
            pass
        await ms.edit(str(e))
        return

    # move to desired file name
    try:
        splitpath = path.split("/downloads/")
        dow_file_name = splitpath[1]
    except Exception:
        dow_file_name = os.path.basename(path)
    old_file_name = f"downloads/{dow_file_name}"
    try:
        os.rename(old_file_name, file_path)
    except Exception:
        # if rename fails, fall back to original path
        file_path = path

    user_id = int(update.message.chat.id)
    data = find(user_id)
    c_caption = None
    thumb = None
    try:
        c_caption = data[1]
        thumb = data[0]
    except Exception:
        pass

    # --- build caption, enriched by metadata mode if enabled ---
    meta = {}
    try:
        meta = await get_user_meta(update.from_user.id)
    except Exception:
        meta = {}
    meta_mode = meta.get("_mode", False)

    if c_caption:
        doc_list = ["filename", "filesize"]
        new_tex = escape_invalid_curly_brackets(c_caption, doc_list)
        try:
            caption = new_tex.format(filename=new_filename, filesize=humanbytes(file.file_size))
        except Exception:
            caption = f"**{new_filename}**"
    else:
        caption = f"**{new_filename}**"

    # if metadata mode is enabled, prepend stored meta fields to caption
    if meta_mode:
        meta_parts = []
        if meta.get("title"):
            meta_parts.append(f"Title: {meta['title']}")
        if meta.get("author"):
            meta_parts.append(f"Author: {meta['author']}")
        if meta.get("artist"):
            meta_parts.append(f"Artist: {meta['artist']}")
        if meta.get("subtitle"):
            meta_parts.append(f"Subtitle: {meta['subtitle']}")
        if meta_parts:
            caption = "**Metadata**\n" + "\n".join(meta_parts) + "\n\n" + caption

    # prepare thumbnail if present
    ph_path = None
    if thumb:
        try:
            ph_path = await bot.download_media(thumb)
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img = img.resize((320, 320))
            img.save(ph_path, "JPEG")
        except Exception:
            ph_path = None

    # big-file / logging logic
    value = 2090000000
    if value < file.file_size:
        await ms.edit("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅ`")
        try:
            filw = await app.send_document(
                log_channel,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅɪɴɢ....`", ms, c_time)
            )
            from_chat = filw.chat.id
            mg_id = filw.id
            # give Telegram a moment
            time.sleep(2)
            await bot.copy_message(update.from_user.id, from_chat, mg_id)
            await ms.delete()
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
        except Exception as e:
            # revert usage on failure
            try:
                used_limit(update.from_user.id, used)
            except:
                pass
            await ms.edit(str(e))
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
            return
    else:
        await ms.edit("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅ`")
        c_time = time.time()
        try:
            await bot.send_document(
                update.from_user.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅɪɴɢ....`", ms, c_time)
            )
            await ms.delete()
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
        except Exception as e:
            try:
                used_limit(update.from_user.id, used)
            except:
                pass
            await ms.edit(str(e))
            try:
                os.remove(file_path)
            except:
                pass
            return


# -------------------------
# Video handler (send as video with metadata + thumbnail)
# -------------------------
@app.on_callback_query(filters.regex("vid"))
async def vid(bot, update):
    new_name = update.message.text or ""
    used_ = find_one(update.from_user.id)
    used = used_.get("used_limit", 0) if used_ else 0
    name = new_name.split(":-")
    if len(name) < 2:
        await update.message.edit("Invalid name format.")
        return
    new_filename = name[1].strip()
    file_path = f"downloads/{new_filename}"
    message = update.message.reply_to_message
    file = message.document or message.video or message.audio
    ms = await update.message.edit("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅ`")

    # usage accounting
    try:
        total_used = used + int(file.file_size)
        used_limit(update.from_user.id, total_used)
    except:
        pass

    c_time = time.time()
    try:
        path = await bot.download_media(
            message=file,
            progress=progress_for_pyrogram,
            progress_args=("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....`", ms, c_time)
        )
    except Exception as e:
        try:
            used_limit(update.from_user.id, used)
        except:
            pass
        await ms.edit(str(e))
        return

    try:
        splitpath = path.split("/downloads/")
        dow_file_name = splitpath[1]
    except Exception:
        dow_file_name = os.path.basename(path)
    old_file_name = f"downloads/{dow_file_name}"
    try:
        os.rename(old_file_name, file_path)
    except Exception:
        file_path = path

    user_id = int(update.message.chat.id)
    data = find(user_id)
    c_caption = None
    thumb = None
    try:
        c_caption = data[1]
        thumb = data[0]
    except Exception:
        pass

    # --- duration and caption ---
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
    except Exception:
        metadata = None
    if metadata and metadata.has("duration"):
        duration = metadata.get('duration').seconds

    if c_caption:
        vid_list = ["filename", "filesize", "duration"]
        new_tex = escape_invalid_curly_brackets(c_caption, vid_list)
        try:
            caption = new_tex.format(
                filename=new_filename,
                filesize=humanbytes(file.file_size),
                duration=timedelta(seconds=duration)
            )
        except Exception:
            caption = f"**{new_filename}**"
    else:
        caption = f"**{new_filename}**"

    # load meta and apply mode
    try:
        meta = await get_user_meta(update.from_user.id)
    except Exception:
        meta = {}
    meta_mode = meta.get("_mode", False)
    if meta_mode:
        meta_parts = []
        if meta.get("title"):
            meta_parts.append(f"Title: {meta['title']}")
        if meta.get("author"):
            meta_parts.append(f"Author: {meta['author']}")
        if meta.get("artist"):
            meta_parts.append(f"Artist: {meta['artist']}")
        if meta.get("subtitle"):
            meta_parts.append(f"Subtitle: {meta['subtitle']}")
        if meta_parts:
            caption = "**Metadata**\n" + "\n".join(meta_parts) + "\n\n" + caption

    # --- prepare thumbnail (try saved thumb else take screenshot if duration > 0) ---
    ph_path = None
    if thumb:
        try:
            ph_path = await bot.download_media(thumb)
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img = img.resize((320, 320))
            img.save(ph_path, "JPEG")
        except Exception:
            ph_path = None
    else:
        # attempt screenshot only if duration is at least 1
        try:
            if duration and duration > 1:
                ph_path_ = await take_screen_shot(
                    file_path,
                    os.path.dirname(os.path.abspath(file_path)),
                    random.randint(0, max(0, duration - 1))
                )
                width, height, ph_path = await fix_thumb(ph_path_)
            else:
                ph_path = None
        except Exception as e:
            ph_path = None
            print("thumbnail error:", e)

    # big-file / logging logic
    value = 2090000000
    if value < file.file_size:
        await ms.edit("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅ`")
        try:
            filw = await app.send_video(
                log_channel,
                video=file_path,
                thumb=ph_path,
                duration=duration,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅɪɴɢ....`", ms, c_time)
            )
            from_chat = filw.chat.id
            mg_id = filw.id
            time.sleep(2)
            await bot.copy_message(update.from_user.id, from_chat, mg_id)
            await ms.delete()
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
        except Exception as e:
            try:
                used_limit(update.from_user.id, used)
            except:
                pass
            await ms.edit(str(e))
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
            return
    else:
        await ms.edit("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅ`")
        c_time = time.time()
        try:
            await bot.send_video(
                update.from_user.id,
                video=file_path,
                thumb=ph_path,
                duration=duration,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅɪɴɢ....`", ms, c_time)
            )
            await ms.delete()
            try:
                os.remove(file_path)
            except:
                pass
            try:
                if ph_path:
                    os.remove(ph_path)
            except:
                pass
        except Exception as e:
            try:
                used_limit(update.from_user.id, used)
            except:
                pass
            await ms.edit(str(e))
            try:
                os.remove(file_path)
            except:
                pass
            return


# -------------------------
# Audio handler (send as audio with title/performer when metadata enabled)
# -------------------------
@app.on_callback_query(filters.regex("aud"))
async def aud(bot, update):
    new_name = update.message.text or ""
    used_ = find_one(update.from_user.id)
    used = used_.get("used_limit", 0) if used_ else 0
    name = new_name.split(":-")
    if len(name) < 2:
        await update.message.edit("Invalid name format.")
        return
    new_filename = name[1].strip()
    file_path = f"downloads/{new_filename}"
    message = update.message.reply_to_message
    file = message.document or message.video or message.audio

    # usage accounting
    try:
        total_used = used + int(file.file_size)
        used_limit(update.from_user.id, total_used)
    except:
        pass

    ms = await update.message.edit("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅ`")
    c_time = time.time()
    try:
        path = await bot.download_media(
            message=file,
            progress=progress_for_pyrogram,
            progress_args=("`Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....`", ms, c_time)
        )
    except Exception as e:
        try:
            used_limit(update.from_user.id, used)
        except:
            pass
        await ms.edit(str(e))
        return

    try:
        splitpath = path.split("/downloads/")
        dow_file_name = splitpath[1]
    except Exception:
        dow_file_name = os.path.basename(path)
    old_file_name = f"downloads/{dow_file_name}"
    try:
        os.rename(old_file_name, file_path)
    except Exception:
        file_path = path

    # duration
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
    except Exception:
        metadata = None
    if metadata and metadata.has("duration"):
        duration = metadata.get('duration').seconds

    user_id = int(update.message.chat.id)
    data = find(user_id)
    c_caption = None
    thumb = None
    try:
        c_caption = data[1]
        thumb = data[0]
    except Exception:
        pass

    if c_caption:
        aud_list = ["filename", "filesize", "duration"]
        new_tex = escape_invalid_curly_brackets(c_caption, aud_list)
        try:
            caption = new_tex.format(
                filename=new_filename,
                filesize=humanbytes(file.file_size),
                duration=timedelta(seconds=duration)
            )
        except Exception:
            caption = f"**{new_filename}**"
    else:
        caption = f"**{new_filename}**"

    # metadata injection and audio-specific fields
    try:
        meta = await get_user_meta(update.from_user.id)
    except Exception:
        meta = {}
    meta_mode = meta.get("_mode", False)
    audio_title = None
    audio_performer = None
    if meta_mode:
        audio_title = meta.get("title") or new_filename
        audio_performer = meta.get("artist") or meta.get("author")
        meta_parts = []
        if meta.get("title"):
            meta_parts.append(f"Title: {meta['title']}")
        if meta.get("author"):
            meta_parts.append(f"Author: {meta['author']}")
        if meta.get("artist"):
            meta_parts.append(f"Artist: {meta['artist']}")
        if meta.get("subtitle"):
            meta_parts.append(f"Subtitle: {meta['subtitle']}")
        if meta_parts:
            caption = "**Metadata**\n" + "\n".join(meta_parts) + "\n\n" + caption

    # thumbnail processing
    ph_path = None
    if thumb:
        try:
            ph_path = await bot.download_media(thumb)
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img = img.resize((320, 320))
            img.save(ph_path, "JPEG")
        except Exception:
            ph_path = None

    await ms.edit("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅ`")
    c_time = time.time()
    try:
        await bot.send_audio(
            update.message.chat.id,
            audio=file_path,
            caption=caption,
            thumb=ph_path,
            duration=duration,
            title=audio_title,
            performer=audio_performer,
            progress=progress_for_pyrogram,
            progress_args=("`Tʀyɪɴɢ Tᴏ Uᴘʟᴏᴀᴅɪɴɢ....`", ms, c_time),
        )
        await ms.delete()
        try:
            os.remove(file_path)
        except:
            pass
        try:
            if ph_path:
                os.remove(ph_path)
        except:
            pass
    except Exception as e:
        try:
            used_limit(update.from_user.id, used)
        except:
            pass
        await ms.edit(str(e))
        try:
            os.remove(file_path)
        except:
            pass
        try:
            if ph_path:
                os.remove(ph_path)
        except:
            pass
        return


# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
