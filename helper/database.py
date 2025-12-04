import pymongo
import os
from helper.date import add_date
from config import *

# Mongo Setup
mongo = pymongo.MongoClient(DB_URL)
db = mongo[DB_NAME]
dbcol = db["user"]


# ===============================
# TOTAL USER COUNT
# ===============================
def total_user():
    return dbcol.count_documents({})


# ===============================
# BOT DATA (Rename Counts, etc.)
# ===============================
def botdata(chat_id):
    bot_id = int(chat_id)
    try:
        bot_data = {"_id": bot_id, "total_rename": 0, "total_size": 0}
        dbcol.insert_one(bot_data)
    except:
        pass


def total_rename(chat_id, renamed_file):
    now = int(renamed_file) + 1
    dbcol.update_one({"_id": chat_id}, {"$set": {"total_rename": str(now)}})


def total_size(chat_id, total_size, now_file_size):
    now = int(total_size) + now_file_size
    dbcol.update_one({"_id": chat_id}, {"$set": {"total_size": str(now)}})


# ===============================
# INSERT NEW USER (DEFAULTS)
# ===============================
# uploadlimit = 0  →  UNLIMITED DAILY UPLOAD
def insert(chat_id):
    user_id = int(chat_id)
    user_det = {
        "_id": user_id,
        "file_id": None,
        "caption": None,

        # Daily system removed → kept fields for compatibility
        "daily": 0,
        "date": 0,

        # 0 = Unlimited daily upload
        "uploadlimit": 0,
        "used_limit": 0,

        "usertype": "Free",
        "prexdate": None
    }
    try:
        dbcol.insert_one(user_det)
    except:
        return True


# ===============================
# THUMBNAIL / CAPTION SYSTEM
# ===============================
def addthumb(chat_id, file_id):
    dbcol.update_one({"_id": chat_id}, {"$set": {"file_id": file_id}})


def delthumb(chat_id):
    dbcol.update_one({"_id": chat_id}, {"$set": {"file_id": None}})


def addcaption(chat_id, caption):
    dbcol.update_one({"_id": chat_id}, {"$set": {"caption": caption}})


def delcaption(chat_id):
    dbcol.update_one({"_id": chat_id}, {"$set": {"caption": None}})


# ===============================
# PREMIUM SYSTEM
# ===============================
def dateupdate(chat_id, date):
    dbcol.update_one({"_id": chat_id}, {"$set": {"date": date}})


def used_limit(chat_id, used):
    dbcol.update_one({"_id": chat_id}, {"$set": {"used_limit": used}})


def usertype(chat_id, type):
    dbcol.update_one({"_id": chat_id}, {"$set": {"usertype": type}})


def uploadlimit(chat_id, limit):
    # limit = 0 → unlimited daily upload
    dbcol.update_one({"_id": chat_id}, {"$set": {"uploadlimit": limit}})


def addpre(chat_id):
    # save premium expiry timestamp
    date = add_date()
    dbcol.update_one({"_id": chat_id}, {"$set": {"prexdate": date[0]}})


def addpredata(chat_id):
    dbcol.update_one({"_id": chat_id}, {"$set": {"prexdate": None}})


# ===============================
# DAILY SYSTEM (no longer used)
# kept only to avoid crashes in your project
# ===============================
def daily(chat_id, date):
    dbcol.update_one({"_id": chat_id}, {"$set": {"daily": date}})


# ===============================
# FIND USER DATA
# ===============================
def find(chat_id):
    x = dbcol.find({"_id": chat_id})
    for i in x:
        file = i.get("file_id")
        caption = i.get("caption", None)
        return [file, caption]


def find_one(id):
    return dbcol.find_one({"_id": id})


# ===============================
# GET ALL USER IDs
# ===============================
def getid():
    values = []
    for key in dbcol.find():
        values.append(key["_id"])
    return values


# ===============================
# DELETE USER
# ===============================
def delete(id):
    dbcol.delete_one(id)
