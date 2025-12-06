import os
import json
import asyncio
from typing import Optional, Dict, Any

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)

import motor.motor_asyncio

# ---------- Compatibility shim for filters.edited ----------
# Some pyrogram installations provide `filters.edited`; older/newer ones may not.
# Create a safe fallback that checks message.edit_date if needed.
try:
    edited_filter = filters.edited
except Exception:
    def _is_edited(*args, **kwargs):
        # `filters.create` passes (client, message) or similar; take last positional arg as message
        if args:
            message = args[-1]
        else:
            message = kwargs.get("message")
        return getattr(message, "edit_date", None) is not None

    edited_filter = filters.create(_is_edited)

# ---------- Config / Mongo ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://MovieClub:MovieClub@cluster0.dau2bnj.mongodb.net/MovieClub?retryWrites=true&w=majority&appName=Cluster0")  # set this in your environment
MONGO_DB = os.getenv("MONGO_DB_NAME", "MovieClub")
META_COLL = "metadata"       # stores saved metadata per user
SESS_COLL = "meta_sessions"  # stores temp awaiting states per user

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is required for metadata plugin")

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo_client[MONGO_DB]
meta_coll = db[META_COLL]
sess_coll = db[SESS_COLL]

# ---------- Metadata fields (customize if you want) ----------
FIELDS = [
    ("title", "Title"),
    ("author", "Author"),
    ("artist", "Artist"),
    ("audio", "Audio"),
    ("video", "Video"),
    ("subtitle", "Subtitle"),
]

# ---------- Helpers ----------
def mk_btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def main_menu_kb():
    return InlineKeyboardMarkup(
        [
            [mk_btn("📝 Set Metadata", "md_set"), mk_btn("🔍 View Metadata", "md_view")],
            [mk_btn("💡 Metadata Mode", "md_toggle")],
            [mk_btn("↩️ Back", "md_back"), mk_btn("❌ Close", "md_close")],
        ]
    )


def set_menu_kb():
    # build buttons 2 per row like screenshot
    rows = []
    for i in range(0, len(FIELDS), 2):
        row = []
        row.append(mk_btn(FIELDS[i][1], f"md_field:{FIELDS[i][0]}"))
        if i + 1 < len(FIELDS):
            row.append(mk_btn(FIELDS[i+1][1], f"md_field:{FIELDS[i+1][0]}"))
        rows.append(row)
    rows.append([mk_btn("↩️ Back", "md_back"), mk_btn("❌ Close", "md_close")])
    return InlineKeyboardMarkup(rows)


def view_back_kb():
    return InlineKeyboardMarkup([[mk_btn("↩️ Back", "md_back"), mk_btn("❌ Close", "md_close")]])


async def get_user_meta(user_id: int) -> Dict[str, Any]:
    doc = await meta_coll.find_one({"user_id": user_id})
    return doc["meta"] if doc else {}


async def set_user_meta_field(user_id: int, field: str, value: str):
    await meta_coll.update_one(
        {"user_id": user_id},
        {"$set": {f"meta.{field}": value}},
        upsert=True
    )


async def reset_user_meta_field(user_id: int, field: str):
    await meta_coll.update_one({"user_id": user_id}, {"$unset": {f"meta.{field}": ""}})


async def clear_user_meta(user_id: int):
    await meta_coll.delete_one({"user_id": user_id})


async def set_session(user_id: int, data: dict):
    await sess_coll.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)


async def get_session(user_id: int) -> Optional[dict]:
    doc = await sess_coll.find_one({"user_id": user_id})
    return doc["data"] if doc else None


async def clear_session(user_id: int):
    await sess_coll.delete_one({"user_id": user_id})


# ---------- Command Handler ----------
@Client.on_message(filters.command("metadata") & ~edited_filter)
async def metadata_cmd(c: Client, m: Message):
    text = (
        "📦 /metadata\n\n"
        "Hey RDX\n\n"
        "Customize Metadata:\n\n"
        "➥ You can set custom metadata for your media by selecting fields below.\n"
        "➥ Use View to preview saved values."
    )
    await m.reply_text(text, reply_markup=main_menu_kb())


# ---------- Callback Query Handler ----------
@Client.on_callback_query(filters.regex(r"^md_"))
async def metadata_callback(c: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    data = cq.data  # e.g. md_set, md_view, md_field:title, md_edit_confirm...
    # basic navigation
    if data == "md_close":
        await cq.message.delete()
        await cq.answer()
        return

    if data == "md_back":
        await cq.message.edit(
            "📦 /metadata\n\nChoose an action:",
            reply_markup=main_menu_kb()
        )
        await cq.answer()
        return

    if data == "md_toggle":
        # toggle mode flag in user meta (simple on/off)
        user_meta = await get_user_meta(user_id)
        cur = user_meta.get("_mode", False)
        new = not cur
        await set_user_meta_field(user_id, "_mode", new)
        await cq.answer("Metadata Mode: ON" if new else "Metadata Mode: OFF", show_alert=False)
        # update message to reflect change
        await cq.message.edit(f"Metadata mode is now: {'✅' if new else '❌'}", reply_markup=main_menu_kb())
        return

    if data == "md_set":
        await cq.message.edit("Custom Metadata | Page: 1/1", reply_markup=set_menu_kb())
        await cq.answer()
        return

    if data == "md_view":
        meta = await get_user_meta(user_id)
        if not meta:
            await cq.answer("No metadata set yet.", show_alert=False)
            await cq.message.edit("No metadata saved yet. Use Set Metadata to add values.", reply_markup=set_menu_kb())
            return
        # format metadata nicely
        out = "📂 <b>Saved Metadata</b>\n\n"
        for key, label in FIELDS:
            val = meta.get(key, None)
            out += f"• <b>{label}:</b> {val}\n" if val else f"• <b>{label}:</b> <i>—</i>\n"
        out += "\nYou can edit a field by pressing Set Metadata → field."
        await cq.message.edit(out, reply_markup=view_back_kb())
        await cq.answer()
        return

    # handle field button like md_field:title
    if data.startswith("md_field:"):
        _, field = data.split(":", 1)
        # present options: Edit / Reset / Cancel
        keyboard = InlineKeyboardMarkup(
            [
                [mk_btn("✏️ Edit", f"md_edit:{field}"), mk_btn("♻️ Reset", f"md_reset:{field}")],
                [mk_btn("↩️ Back", "md_set"), mk_btn("❌ Close", "md_close")],
            ]
        )
        # show current value
        meta = await get_user_meta(user_id)
        cur_val = meta.get(field, "<not set>")
        label = next((lbl for k, lbl in FIELDS if k == field), field)
        await cq.message.edit(f"<b>Variable : {label}</b>\n\nCurrent Value : {cur_val}", reply_markup=keyboard)
        await cq.answer()
        return

    # edit flow - ask user to send the new value (create session)
    if data.startswith("md_edit:"):
        _, field = data.split(":", 1)
        await set_session(user_id, {"action": "editing", "field": field})
        label = next((lbl for k, lbl in FIELDS if k == field), field)
        await cq.message.edit(f"✏️ Send the new value for <b>{label}</b> (reply in this chat).", reply_markup=InlineKeyboardMarkup([[mk_btn("Cancel", "md_back")]]))
        await cq.answer("Send the new text now.")
        return

    # reset flow - remove field from db
    if data.startswith("md_reset:"):
        _, field = data.split(":", 1)
        await reset_user_meta_field(user_id, field)
        await cq.answer("Field reset.", show_alert=False)
        # show set menu again
        await cq.message.edit("Field reset successfully.", reply_markup=set_menu_kb())
        return

    # fallback
    await cq.answer()


# ---------- Message Handler for capturing user's input when editing ----------
@Client.on_message(filters.private & ~edited_filter)
async def metadata_text_listener(c: Client, m: Message):
    user_id = m.from_user.id
    session = await get_session(user_id)
    if not session:
        return  # not in edit session — ignore

    # Expecting editing action
    if session.get("action") == "editing":
        field = session.get("field")
        if not field:
            await m.reply_text("Session error. Please try again.")
            await clear_session(user_id)
            return

        # The new value will be the message text or caption (if media has caption)
        new_value = m.text or m.caption or ""
        if not new_value:
            await m.reply_text("Empty value. Send some text to set.")
            return

        # save to mongo
        await set_user_meta_field(user_id, field, new_value)
        await clear_session(user_id)

        label = next((lbl for k, lbl in FIELDS if k == field), field)
        await m.reply_text(f"✅ Saved {label} value.", reply_markup=main_menu_kb())
        return


# ---------- Optional admin command to export/import user metadata ----------
@Client.on_message(filters.command(["export_meta"]) & filters.user( [int(os.getenv("OWNER_ID"))] ) )
async def export_meta(c: Client, m: Message):
    # OWNER only (set OWNER_ID env var)
    cursor = meta_coll.find({})
    docs = []
    async for d in cursor:
        docs.append(d)
    path = "/tmp/metadata_export.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(docs, f, default=str, ensure_ascii=False, indent=2)
    await m.reply_document(path, caption="Metadata export")
    os.remove(path)
