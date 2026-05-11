"""
handlers/tag.py — Tag / mass-call commands for groups.

/all [text]            — mention all tracked members (5 per message)
/admins [text]         — call all group admins
/callone [n] [text]    — mention members one-by-one (1 per message)
/callpm [n] [text]     — DM tracked members who started the bot
/anybody [text]        — mention one random member
/stopcall              — stop any active mass-call
/call [n] [per] [text] — advanced: count, per-message, optional text

aliases: /callall → /all  /anybodies → /anybody  /tagone → /callone  /allpm → /callpm
"""

import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db

# chat_id -> True (active call flag)
_active_calls: dict = {}


# ── helpers ───────────────────────────────────────────────────────────────────

def _mention(user_id: int, name: str) -> str:
    safe = (name or f"User{user_id}")[:24]
    return f'<a href="tg://user?id={user_id}">{safe}</a>'


def _row_mention(row: dict) -> str:
    uid  = row.get("user_id", 0)
    name = row.get("first_name") or row.get("username") or f"User{uid}"
    return _mention(uid, name)


async def _is_admin(update: Update) -> bool:
    try:
        m = await update.effective_chat.get_member(update.effective_user.id)
        return m.status in ("administrator", "creator")
    except Exception:
        return False


async def _get_members(chat_id: int, limit: int = 200) -> list:
    try:
        rows = db.get_ranking(chat_id, limit=limit)
        if rows:
            return rows
    except Exception:
        pass
    try:
        rows = db.get_seen_members(chat_id)
        return rows[:limit] if rows else []
    except Exception:
        return []


# ── /all  (alias: /callall) ───────────────────────────────────────────────────

async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ Only admins can use this command.")
        return
    text    = " ".join(context.args) if context.args else ""
    chat_id = update.effective_chat.id
    rows    = await _get_members(chat_id)
    if not rows:
        await update.message.reply_text(
            "No tracked members yet. Members are tracked once they send a message.")
        return

    _active_calls[chat_id] = True
    header = f"📢 {text}\n\n" if text else "📢 <b>Calling all members!</b>\n\n"
    chunk: list = []

    for row in rows:
        if not _active_calls.get(chat_id):
            break
        chunk.append(_row_mention(row))
        if len(chunk) == 5:
            await update.message.reply_text(header + " ".join(chunk), parse_mode="HTML")
            chunk.clear()
            await asyncio.sleep(1.5)

    if chunk and _active_calls.get(chat_id):
        await update.message.reply_text(header + " ".join(chunk), parse_mode="HTML")

    _active_calls.pop(chat_id, None)


# ── /admins  (alias: /calladmins) ─────────────────────────────────────────────

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    try:
        admins = await update.effective_chat.get_administrators()
    except Exception:
        await update.message.reply_text("Could not fetch admin list.")
        return

    mentions = [
        _mention(a.user.id, a.user.first_name or a.user.username or "Admin")
        for a in admins
        if not a.user.is_bot
    ]
    if not mentions:
        await update.message.reply_text("No human admins found.")
        return

    header = f"🛡️ {text}\n\n" if text else "🛡️ <b>Calling all admins!</b>\n\n"
    await update.message.reply_text(header + " ".join(mentions), parse_mode="HTML")


# ── /callone  (alias: /tagone  /allone  /anybodies as alias call) ─────────────

async def callone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ Only admins can use this command.")
        return
    args  = context.args or []
    count = 10
    text  = ""
    if args and args[0].isdigit():
        count = min(int(args[0]), 200)
        text  = " ".join(args[1:])
    else:
        text = " ".join(args)

    chat_id = update.effective_chat.id
    rows    = (await _get_members(chat_id))[:count]
    if not rows:
        await update.message.reply_text("No tracked members yet.")
        return

    _active_calls[chat_id] = True
    footer = f"\n{text}" if text else ""

    for row in rows:
        if not _active_calls.get(chat_id):
            break
        await update.message.reply_text(
            f"👤 {_row_mention(row)}{footer}", parse_mode="HTML"
        )
        await asyncio.sleep(2)

    _active_calls.pop(chat_id, None)


# ── /callpm  (alias: /allpm) ──────────────────────────────────────────────────

async def callpm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ Only admins can use this command.")
        return
    args  = context.args or []
    count = 50
    text  = ""
    if args and args[0].isdigit():
        count = min(int(args[0]), 200)
        text  = " ".join(args[1:])
    else:
        text = " ".join(args)

    chat_id   = update.effective_chat.id
    chat_name = update.effective_chat.title or "your group"
    rows      = (await _get_members(chat_id))[:count]

    msg  = (
        f"📨 <b>Message from {chat_name}:</b>\n\n{text}"
        if text else
        f"📨 <b>You have been called from {chat_name}!</b>"
    )
    sent = failed = 0

    for row in rows:
        try:
            await context.bot.send_message(row["user_id"], msg, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ Sent PM to <b>{sent}</b> members.\n"
        f"⚠️ {failed} could not be reached (bot not started in PM).",
        parse_mode="HTML",
    )


# ── /anybody ──────────────────────────────────────────────────────────────────

async def anybody(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text    = " ".join(context.args) if context.args else ""
    chat_id = update.effective_chat.id
    rows    = await _get_members(chat_id, limit=100)
    if not rows:
        await update.message.reply_text("No tracked members yet.")
        return
    row    = random.choice(rows)
    footer = f"\n{text}" if text else ""
    await update.message.reply_text(
        f"👋 Hey {_row_mention(row)}!{footer}", parse_mode="HTML"
    )


# ── /stopcall  (alias: /stop_call) ────────────────────────────────────────────

async def stopcall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ Only admins can use this command.")
        return
    chat_id = update.effective_chat.id
    if chat_id in _active_calls:
        _active_calls.pop(chat_id)
        await update.message.reply_text("✅ Mass call stopped.")
    else:
        await update.message.reply_text("No active call running in this chat.")


# ── /call  (alias: /callactive  /active) ──────────────────────────────────────
#  /call [how_many] [per_message] [text]

async def call_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ Only admins can use this command.")
        return
    args    = list(context.args or [])
    count   = 100
    per_msg = 5
    text    = ""

    ptr = 0
    if ptr < len(args) and args[ptr].isdigit():
        count = min(int(args[ptr]), 500);  ptr += 1
    if ptr < len(args) and args[ptr].isdigit():
        per_msg = min(max(int(args[ptr]), 1), 20);  ptr += 1
    text = " ".join(args[ptr:])

    chat_id = update.effective_chat.id
    rows    = (await _get_members(chat_id))[:count]
    if not rows:
        await update.message.reply_text("No tracked members yet.")
        return

    _active_calls[chat_id] = True
    header  = f"📢 {text}\n\n" if text else "📢\n\n"
    chunk: list = []

    for row in rows:
        if not _active_calls.get(chat_id):
            break
        chunk.append(_row_mention(row))
        if len(chunk) == per_msg:
            await update.message.reply_text(header + " ".join(chunk), parse_mode="HTML")
            chunk.clear()
            await asyncio.sleep(1.5)

    if chunk and _active_calls.get(chat_id):
        await update.message.reply_text(header + " ".join(chunk), parse_mode="HTML")

    _active_calls.pop(chat_id, None)
