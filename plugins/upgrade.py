#  Telegram MTProto API Client Library for Pyrogram
#  Copyright (C) 2017-present DigitalBotz <https://github.com/DigitalBotz>
#  I am a telegram bot, I created it using pyrogram library. https://github.com/pyrogram
"""
Apache License 2.0
Copyright (c) 2022 @Digital_Botz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Telegram Link : https://t.me/Digital_Botz 
Repo Link : https://github.com/DigitalBotz/Digital-Rename-Bot
License Link : https://github.com/DigitalBotz/Digital-Rename-Bot/blob/main/LICENSE
"""

__name__ = "Digital-Rename-Bot"
__version__ = "3.0.8"
__license__ = " Apache License, Version 2.0"
__copyright__ = "Copyright (C) 2022-present Digital Botz <https://github.com/DigitalBotz>"
__programer__ = "<a href=https://github.com/DigitalBotz/Digital-Rename-Bot>Digital Botz</a>"
__library__ = "<a href=https://github.com/pyrogram>Pyʀᴏɢʀᴀᴍ</a>"
__language__ = "<a href=https://www.python.org/>Pyᴛʜᴏɴ 3</a>"
__database__ = "<a href=https://cloud.mongodb.com/>Mᴏɴɢᴏ DB</a>"
__developer__ = "<a href=https://t.me/Digital_Botz>Digital Botz</a>"
__maindeveloper__ = "<a href=https://t.me/RknDeveloper>RknDeveloper</a>"

import os
import sys
import string
import random

from time import time
from urllib.parse import quote
from urllib3 import disable_warnings

from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from cloudscraper import create_scraper
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

DATABASE_URL = Config.DB_URL

verify_dict = {}

# CONFIG VARIABLES 😄
VERIFY_PHOTO = os.environ.get('VERIFY_PHOTO', 'https://graph.org/file/7d728ffd7c3fa4fbf8799-7e75443ac1704c776a.jpg')  # YOUR VERIFY PHOTO LINK
SHORTLINK_SITE = os.environ.get('SHORTLINK_SITE', 'shortxlinks.com') # YOUR SHORTLINK URL LIKE:- site.com
SHORTLINK_API = os.environ.get('SHORTLINK_API', '32b97a6d89bf4fbe47e14d4b7674d28cc02a422f') # YOUR SHORTLINK API LIKE:- ma82owowjd9hw6_js7
VERIFY_EXPIRE = os.environ.get('VERIFY_EXPIRE', 43200) # VERIFY EXPIRE TIME IN SECONDS. LIKE:- 0 (ZERO) TO OFF VERIFICATION 
VERIFY_TUTORIAL = os.environ.get('VERIFY_TUTORIAL', 'https://t.me/How_to_download_Sitaratoons/4') # LINK OF TUTORIAL TO VERIFY 
DATABASE_URL = os.environ.get('DATABASE_URL', 'mongodb+srv://MovieClub:MovieClub@cluster0.dau2bnj.mongodb.net/MovieClub?retryWrites=true&w=majority&appName=Cluster0') # MONGODB DATABASE URL To Store Verifications 
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'File_rename')   # Collection Name For MongoDB 
PREMIUM_USERS = list(map(int, os.environ.get('PREMIUM_USERS', '6692613520').split()))

missing = [v for v in ["COLLECTION_NAME", "VERIFY_PHOTO", "SHORTLINK_SITE", "SHORTLINK_API", "VERIFY_TUTORIAL"] if not v]; sys.exit(f"Missing: {', '.join(missing)}") if missing else None 

# DATABASE
class VerifyDB():
    def __init__(self):
        try:
            self._dbclient = AsyncIOMotorClient(DATABASE_URL)
            self._db = self._dbclient['verify-db']
            self._verifydb = self._db[COLLECTION_NAME]  
            print('Database Comnected ✅')
        except Exception as e:
            print(f'Failed To Connect To Database ❌. \nError: {str(e)}')
    
    async def get_verify_status(self, user_id):
        if status := await self._verifydb.find_one({'id': user_id}):
            return status.get('verify_status', 0)
        return 0

    async def update_verify_status(self, user_id):
        await self._verifydb.update_one({'id': user_id}, {'$set': {'verify_status': time()}}, upsert=True)

# GLOBAL VERIFY FUNCTION 
async def token_system_filter(_, __, message):
    if is_verified := await is_user_verified(message.from_user.id):
        return False
    return True 
    
@Client.on_message((filters.private|filters.group) & filters.incoming & filters.create(token_system_filter) & ~filters.bot)
async def global_verify_function(client, message):
    if message.text:
        cmd = message.text.split()
        if len(cmd) == 2:
            data = cmd[1]
            if data.startswith("verify"):
                await validate_token(client, message, data)
                return
    await send_verification(client, message)
        
# FUNCTIONS
async def is_user_verified(user_id):
    if not VERIFY_EXPIRE or (user_id in PREMIUM_USERS):
        return True
    isveri = await verifydb.get_verify_status(user_id)
    if not isveri or (time() - isveri) >= float(VERIFY_EXPIRE):
        return False
    return True    
    
async def send_verification(client, message, text=None, buttons=None):
    username = (await client.get_me()).username
    if done := await is_user_verified(message.from_user.id):
        text = f'<b>Hi 👋 {message.from_user.mention},\nYou Are Already Verified Enjoy 😄</b>'
    else:
        verify_token = await get_verify_token(client, message.from_user.id, f"https://telegram.me/{username}?start=")
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton('Vᴇʀɪꜰʏ ✅', url=verify_token)],
            [InlineKeyboardButton('Hᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ ❓', url=VERIFY_TUTORIAL)]
        ])
    if not text:
        text = f"""<b>Hi 👋 {message.from_user.mention}, 
<blockquote expandable>\nYour Ads Token Has Been Expired, Kindly Get A New Token To Continue Using This Bot.
         ㅤㅤㅤㅤㅤ   - Thank You 
\nआपका विज्ञापन टोकन समाप्त हो गया है, बॉट को फिर से उपयोग करने के लिए नया टोकन लें!
         ㅤㅤㅤㅤㅤㅤㅤ- धन्यवाद
\nValidity: {get_readable_time(VERIFY_EXPIRE)}
\n#Verification...⌛</blockquote></b>"""
    message = message if isinstance(message, Message) else message.message
    await client.send_photo(
        chat_id=message.chat.id,
        photo=VERIFY_PHOTO,
        caption=text,
        reply_markup=buttons,
        reply_to_message_id=message.id,
    )
 
async def get_verify_token(bot, userid, link):
    vdict = verify_dict.setdefault(userid, {})
    short_url = vdict.get('short_url')
    if not short_url:
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        long_link = f"{link}verify-{userid}-{token}"
        short_url = await get_short_url(long_link)
        vdict.update({'token': token, 'short_url': short_url})
    return short_url

async def get_short_url(longurl, shortener_site = SHORTLINK_SITE, shortener_api = SHORTLINK_API):
    cget = create_scraper().request
    disable_warnings()
    try:
        url = f'https://{shortener_site}/api'
        params = {'api': shortener_api,
                  'url': longurl,
                  'format': 'text',
                 }
        res = cget('GET', url, params=params)
        if res.status_code == 200 and res.text:
            return res.text
        else:
            params['format'] = 'json'
            res = cget('GET', url, params=params)
            res = res.json()
            if res.status_code == 200:
                return res.get('shortenedUrl', long_url)
    except Exception as e:
        print(e)
        return longurl

async def validate_token(client, message, data):
    user_id = message.from_user.id
    vdict = verify_dict.setdefault(user_id, {})
    dict_token = vdict.get('token', None)
    if await is_user_verified(user_id):
        return await message.reply("<b>Sɪʀ, Yᴏᴜ Aʀᴇ Aʟʀᴇᴀᴅʏ Vᴇʀɪғɪᴇᴅ 🤓...</b>")
    if not dict_token:
        return await send_verification(client, message, text="<b>Tʜᴀᴛ's Nᴏᴛ Yᴏᴜʀ Vᴇʀɪғʏ Tᴏᴋᴇɴ 🥲...\n\n\nTᴀᴘ Oɴ Vᴇʀɪғʏ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Yᴏᴜʀs...</b>")  
    _, uid, token = data.split("-")
    if uid != str(user_id):
        return await send_verification(client, message, text="<b>Vᴇʀɪғʏ Tᴏᴋᴇɴ Dɪᴅ Nᴏᴛ Mᴀᴛᴄʜᴇᴅ 😕...\n\n\nTᴀᴘ Oɴ Vᴇʀɪғʏ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Aɢᴀɪɴ...</b>")
    elif dict_token != token:
        return await send_verification(client, message, text="<b>Iɴᴠᴀʟɪᴅ Oʀ Exᴘɪʀᴇᴅ Tᴏᴋᴇɴ 🔗...</b>")
    verify_dict.pop(user_id, None)
    await verifydb.update_verify_status(user_id)
    await client.send_photo(chat_id=message.from_user.id,
                            photo=VERIFY_PHOTO,
                            caption=f'<b>Wᴇʟᴄᴏᴍᴇ Bᴀᴄᴋ 😁, Nᴏᴡ Yᴏᴜ Cᴀɴ Usᴇ Mᴇ Fᴏʀ {get_readable_time(VERIFY_EXPIRE)}.\n\n\nEɴᴊᴏʏʏʏ...❤️</b>',
                            reply_to_message_id=message.id,
                            )
    
def get_readable_time(seconds):
    periods = [('ᴅ', 86400), ('ʜ', 3600), ('ᴍ', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

verifydb = VerifyDB()
    
# main copyright herders (©️)
# I have been working on this repo since 2022


# main working files 
# - bot.py
# - web_support.py
# - plugins/
# - start_&_cb.py
# - Force_Sub.py
# - admin_panel.py
# - file_rename.py
# - metadata.py
# - prefix_&_suffix.py
# - thumb_&_cap.py
# - config.py
# - utils.py
# - database.py

# bot run files
# - bot.py
# - Procfile
# - Dockerfile
# - requirements.txt
# - runtime.txt



# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
