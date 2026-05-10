import json
import re
import asyncio
from datetime import datetime, timedelta

from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import database as db
from config import WARN_LIMIT, OWNER_ID

# ── Global: track active utag operations per chat ────────────────────────────
active_utag: dict = {}   # {chat_id: True/False (True = running)}

# ── Supported languages ───────────────────────────────────────────────────────
BOT_LANGUAGES = {
    "en": ("🇬🇧", "English"),
    "hi": ("🇮🇳", "Hindi"),
    "ar": ("🇸🇦", "Arabic"),
    "ur": ("🇵🇰", "Urdu"),
    "es": ("🇪🇸", "Spanish"),
    "fr": ("🇫🇷", "French"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_time(time_str: str):
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def time_label(time_str: str) -> str:
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return time_str
    value, unit = match.group(1), match.group(2)
    label = {"s": "second", "m": "minute", "h": "hour", "d": "day"}[unit]
    return f"{value} {label}{'s' if int(value) != 1 else ''}"


def user_link(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def no_permission_msg():
    return "You need to be a group admin to use this command."


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    if context.args:
        username = context.args[0].lstrip("@")
        for lookup in [username, int(username) if username.isdigit() else None]:
            if lookup is None:
                continue
            try:
                cm = await context.bot.get_chat_member(update.effective_chat.id, lookup)
                return cm.user
            except Exception:
                pass
    return None


# ── Welcome button parser ─────────────────────────────────────────────────────

_BTN_RE = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')


def parse_welcome_buttons(text: str):
    """Return (clean_text, InlineKeyboardMarkup | None).
    Lines that contain [Label](url) become button rows.
    Multiple buttons on one line separated by | appear side by side.
    """
    rows = []
    clean_lines = []
    for line in text.split("\n"):
        buttons = _BTN_RE.findall(line)
        if buttons:
            row = [InlineKeyboardButton(label, url=url) for label, url in buttons]
            rows.append(row)
        else:
            clean_lines.append(line)
    clean_text = "\n".join(clean_lines).strip()
    keyboard = InlineKeyboardMarkup(rows) if rows else None
    return clean_text, keyboard


async def _send_welcome_preview(update, welcome_data, name, chat_title):
    text = welcome_data.get("text", "")
    photo_id = welcome_data.get("photo_id")
    text = text.replace("{name}", f"<b>{name}</b>").replace("{chat}", f"<b>{chat_title}</b>")
    clean_text, keyboard = parse_welcome_buttons(text)

    if photo_id:
        try:
            await update.message.reply_photo(
                photo=photo_id, caption=clean_text,
                parse_mode="HTML", reply_markup=keyboard)
            return
        except Exception:
            pass
    await update.message.reply_text(clean_text, parse_mode="HTML", reply_markup=keyboard)


# ── Member commands ───────────────────────────────────────────────────────────

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to ban.")
        return
    if target.id == update.effective_user.id:
        await update.message.reply_text("You cannot ban yourself.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"🔨 Banned {user_link(target)} permanently.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "BAN", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not ban: {e}")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to unban.")
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"✅ Unbanned {user_link(target)}. They can now rejoin.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "UNBAN", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not unban: {e}")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to kick.")
        return
    if target.id == update.effective_user.id:
        await update.message.reply_text("You cannot kick yourself.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"👢 Kicked {user_link(target)}. They can rejoin via invite link.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "KICK", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not kick: {e}")


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to mute.")
        return
    duration = None
    duration_str = "indefinitely"
    for arg in (context.args or []):
        s = parse_time(arg)
        if s:
            duration = datetime.utcnow() + timedelta(seconds=s)
            duration_str = f"for {time_label(arg)}"
            break
    try:
        perms = ChatPermissions(
            can_send_messages=False, can_send_audios=False,
            can_send_documents=False, can_send_photos=False,
            can_send_videos=False, can_send_video_notes=False,
            can_send_voice_notes=False, can_send_polls=False,
            can_send_other_messages=False,
        )
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id, perms, until_date=duration)
        await update.message.reply_text(
            f"🔇 Muted {user_link(target)} {duration_str}.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name,
                            f"MUTE ({duration_str})", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not mute: {e}")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to unmute.")
        return
    try:
        perms = ChatPermissions(
            can_send_messages=True, can_send_audios=True,
            can_send_documents=True, can_send_photos=True,
            can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True,
            can_send_other_messages=True,
        )
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, perms)
        await update.message.reply_text(
            f"🔊 Unmuted {user_link(target)}.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "UNMUTE", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not unmute: {e}")


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to warn.")
        return
    if target.id == update.effective_user.id:
        await update.message.reply_text("You cannot warn yourself.")
        return
    count = db.add_warn(target.id, update.effective_chat.id)
    db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                        update.effective_user.first_name,
                        f"WARN ({count}/{WARN_LIMIT})", target.first_name)
    if count >= WARN_LIMIT:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            db.reset_warns(target.id, update.effective_chat.id)
            await update.message.reply_text(
                f"🚫 {user_link(target)} reached <b>{WARN_LIMIT} warnings</b> and was automatically banned.",
                parse_mode="HTML")
        except BadRequest as e:
            await update.message.reply_text(
                f"Warning {count}/{WARN_LIMIT} for {user_link(target)} — auto-ban failed: {e}",
                parse_mode="HTML")
    else:
        bar = "🔴" * count + "⚪" * (WARN_LIMIT - count)
        await update.message.reply_text(
            f"⚠️ Warning issued to {user_link(target)}\n{bar} <b>{count}/{WARN_LIMIT}</b>",
            parse_mode="HTML")


async def resetwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to reset warnings.")
        return
    db.reset_warns(target.id, update.effective_chat.id)
    await update.message.reply_text(
        f"✅ All warnings cleared for {user_link(target)}.", parse_mode="HTML")
    db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                        update.effective_user.first_name, "RESETWARNS", target.first_name)


async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to promote.")
        return
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, target.id,
            can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_pin_messages=True,
            can_invite_users=True,
        )
        await update.message.reply_text(
            f"⭐ {user_link(target)} has been promoted to admin.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "PROMOTE", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not promote: {e}")


async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or mention them to demote.")
        return
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, target.id,
            can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False,
            can_invite_users=False,
        )
        await update.message.reply_text(
            f"🔽 {user_link(target)} has been demoted.", parse_mode="HTML")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "DEMOTE", target.first_name)
    except BadRequest as e:
        await update.message.reply_text(f"Could not demote: {e}")


async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to pin it.")
        return
    try:
        await context.bot.pin_chat_message(
            update.effective_chat.id,
            update.message.reply_to_message.message_id,
            disable_notification=False)
        await update.message.reply_text("📌 Message pinned.")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "PIN", "")
    except BadRequest as e:
        await update.message.reply_text(f"Could not pin: {e}")


async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    try:
        await context.bot.unpin_chat_message(update.effective_chat.id)
        await update.message.reply_text("📌 Pinned message removed.")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "UNPIN", "")
    except BadRequest as e:
        await update.message.reply_text(f"Could not unpin: {e}")


async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the first message you want to start purging from.")
        return
    from_id = update.message.reply_to_message.message_id
    to_id   = update.message.message_id
    deleted = 0
    for msg_id in range(from_id, to_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            deleted += 1
        except Exception:
            pass
    confirm = await update.effective_chat.send_message(
        f"🗑 Purged <b>{deleted}</b> messages.", parse_mode="HTML")
    db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                        update.effective_user.first_name, f"PURGE ({deleted} msgs)", "")
    await asyncio.sleep(3)
    try:
        await context.bot.delete_message(update.effective_chat.id, confirm.message_id)
    except Exception:
        pass


# ── Rules ─────────────────────────────────────────────────────────────────────

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    if not context.args:
        await update.message.reply_text("Usage: /setrules [your rules text]")
        return
    text = " ".join(context.args)
    db.set_rules(update.effective_chat.id, text)
    await update.message.reply_text("✅ Group rules saved. Use /rules to display them.")


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = db.get_rules(update.effective_chat.id)
    if text:
        await update.message.reply_text(
            f"📋 <b>Group Rules</b>\n━━━━━━━━━━━━━━━━\n\n{text}", parse_mode="HTML")
    else:
        await update.message.reply_text("No rules set yet. Admins can use /setrules [text].")


# ── Welcome ───────────────────────────────────────────────────────────────────

async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return

    USAGE = (
        "<b>Set Welcome Message</b>\n\n"
        "📝 <b>Text only:</b>\n"
        "<code>/setwelcome Welcome {name} to {chat}!</code>\n\n"
        "📸 <b>With photo:</b>\n"
        "Send a photo with <code>/setwelcome Your text</code> as the caption.\n"
        "<i>— or —</i>\n"
        "Reply to any photo with <code>/setwelcome Your text</code>\n\n"
        "🔘 <b>Add buttons</b> (on their own line):\n"
        "<code>[Button Label](https://t.me/...)</code>\n\n"
        "<b>Variables:</b> {name} = member name, {chat} = group name\n\n"
        "<b>Example:</b>\n"
        "<code>/setwelcome 👋 Welcome {name}!\n"
        "[Our Rules](https://t.me/...)\n"
        "[Support](https://t.me/...)</code>"
    )

    # ── Get photo file_id ──
    photo_id = None
    if update.message.photo:
        # Command sent as photo caption
        photo_id = update.message.photo[-1].file_id
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        # Replied to a photo
        photo_id = update.message.reply_to_message.photo[-1].file_id

    # ── Get text ──
    if context.args:
        text = " ".join(context.args)
    elif (update.message.reply_to_message
          and update.message.reply_to_message.caption
          and not update.message.photo):
        text = update.message.reply_to_message.caption
    else:
        if not context.args and not photo_id:
            await update.message.reply_text(USAGE, parse_mode="HTML")
            return
        text = ""

    if not text and not photo_id:
        await update.message.reply_text(USAGE, parse_mode="HTML")
        return

    # ── Save ──
    welcome_data = {"text": text, "photo_id": photo_id}
    db.set_welcome(update.effective_chat.id, json.dumps(welcome_data))

    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text("✅ Welcome message saved! Here's a preview:")
    await _send_welcome_preview(
        update, welcome_data,
        name=user.first_name,
        chat_title=chat.title or "Group"
    )


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    raw = db.get_welcome(chat_id)

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        name = member.first_name
        chat_title = update.effective_chat.title or "Group"

        if raw:
            # Try JSON format first, fall back to plain text
            try:
                welcome_data = json.loads(raw)
            except Exception:
                welcome_data = {"text": raw, "photo_id": None}

            text = welcome_data.get("text", "")
            photo_id = welcome_data.get("photo_id")
            text = text.replace("{name}", f"<b>{name}</b>").replace(
                "{chat}", f"<b>{chat_title}</b>")
            clean_text, keyboard = parse_welcome_buttons(text)

            try:
                if photo_id:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_id,
                        caption=clean_text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=clean_text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"👋 Welcome, <b>{name}</b>!",
                    parse_mode="HTML",
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"👋 Welcome, <b>{name}</b> to <b>{chat_title}</b>!",
                parse_mode="HTML",
            )


# ── Lock / Unlock ─────────────────────────────────────────────────────────────

_LINK_LOCKED_CHATS: set = set()   # chat_ids where links are deleted by the bot


def is_link_locked(chat_id: int) -> bool:
    return chat_id in _LINK_LOCKED_CHATS


async def check_link_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message handler that deletes messages containing URLs when link-lock is on."""
    if not update.message or not update.message.text:
        return
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return
    if not is_link_locked(chat.id):
        return
    user = update.effective_user
    if not user:
        return
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        return
    import re
    if re.search(r'https?://|www\.', update.message.text, re.IGNORECASE):
        try:
            await update.message.delete()
        except Exception:
            pass


async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    if not context.args:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Stickers", callback_data="lock_stickers"),
             InlineKeyboardButton("GIFs",     callback_data="lock_gifs")],
            [InlineKeyboardButton("Polls",    callback_data="lock_polls"),
             InlineKeyboardButton("Media",    callback_data="lock_media")],
            [InlineKeyboardButton("🔗 Links", callback_data="lock_links"),
             InlineKeyboardButton("All messages", callback_data="lock_all")],
        ])
        await update.message.reply_text("🔒 What do you want to lock?", reply_markup=keyboard)
        return
    await _do_lock(update, context, context.args[0].lower())


async def lock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    member = await context.bot.get_chat_member(query.message.chat_id, query.from_user.id)
    if member.status not in ("administrator", "creator"):
        await query.answer("You need to be an admin.", show_alert=True)
        return
    lock_type = query.data.replace("lock_", "")
    await _do_lock_direct(query.message.chat_id, lock_type, context)
    await query.edit_message_text(f"🔒 Locked: <b>{lock_type}</b>", parse_mode="HTML")
    db.log_admin_action(query.message.chat_id, query.from_user.id,
                        query.from_user.first_name, f"LOCK ({lock_type})", "")


async def _do_lock(update, context, lock_type):
    await _do_lock_direct(update.effective_chat.id, lock_type, context)
    await update.message.reply_text(f"🔒 Locked: <b>{lock_type}</b>", parse_mode="HTML")
    db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                        update.effective_user.first_name, f"LOCK ({lock_type})", "")


async def _do_lock_direct(chat_id, lock_type, context):
    if lock_type == "links":
        _LINK_LOCKED_CHATS.add(chat_id)
        return
    perms_map = {
        "stickers": ChatPermissions(can_send_other_messages=False),
        "gifs":     ChatPermissions(can_send_other_messages=False),
        "polls":    ChatPermissions(can_send_polls=False),
        "media":    ChatPermissions(can_send_photos=False, can_send_videos=False,
                                    can_send_audios=False, can_send_documents=False),
        "all":      ChatPermissions(can_send_messages=False),
    }
    if lock_type in perms_map:
        await context.bot.set_chat_permissions(chat_id, perms_map[lock_type])


async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    try:
        chat_id = update.effective_chat.id
        _LINK_LOCKED_CHATS.discard(chat_id)
        perms = ChatPermissions(
            can_send_messages=True, can_send_audios=True,
            can_send_documents=True, can_send_photos=True,
            can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True,
            can_send_other_messages=True,
        )
        await context.bot.set_chat_permissions(chat_id, perms)
        await update.message.reply_text("🔓 All restrictions removed. Chat is fully open.")
        db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                            update.effective_user.first_name, "UNLOCK", "")
    except BadRequest as e:
        await update.message.reply_text(f"Could not unlock: {e}")


# ── Slowmode ──────────────────────────────────────────────────────────────────

async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return
    if not context.args:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("5s",    callback_data="slow_5"),
             InlineKeyboardButton("10s",   callback_data="slow_10"),
             InlineKeyboardButton("30s",   callback_data="slow_30")],
            [InlineKeyboardButton("1 min", callback_data="slow_60"),
             InlineKeyboardButton("5 min", callback_data="slow_300"),
             InlineKeyboardButton("Off",   callback_data="slow_0")],
        ])
        await update.message.reply_text("🐢 Choose slow mode delay:", reply_markup=keyboard)
        return
    arg = context.args[0].lower()
    seconds = 0 if arg == "off" else (int(arg) if arg.isdigit() else None)
    if seconds is None:
        await update.message.reply_text("Usage: /slowmode [seconds] or /slowmode off")
        return
    await _set_slowmode(update.effective_chat.id, seconds, context)
    msg = "⚡ Slow mode disabled." if seconds == 0 else f"🐢 Slow mode set to {seconds} seconds."
    await update.message.reply_text(msg)
    db.log_admin_action(update.effective_chat.id, update.effective_user.id,
                        update.effective_user.first_name, f"SLOWMODE ({seconds}s)", "")


async def slowmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    member = await context.bot.get_chat_member(query.message.chat_id, query.from_user.id)
    if member.status not in ("administrator", "creator"):
        await query.answer("You need to be an admin.", show_alert=True)
        return
    seconds = int(query.data.replace("slow_", ""))
    await _set_slowmode(query.message.chat_id, seconds, context)
    msg = "⚡ Slow mode disabled." if seconds == 0 else f"🐢 Slow mode set to {seconds} seconds."
    await query.edit_message_text(msg)
    db.log_admin_action(query.message.chat_id, query.from_user.id,
                        query.from_user.first_name, f"SLOWMODE ({seconds}s)", "")


async def _set_slowmode(chat_id, seconds, context):
    try:
        await context.bot.set_chat_slow_mode_delay(chat_id, seconds)
    except BadRequest:
        pass


# ── Report ────────────────────────────────────────────────────────────────────

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to report it to the admins.")
        return
    reporter = update.effective_user.first_name
    reported_msg  = update.message.reply_to_message
    reported_user = reported_msg.from_user.first_name if reported_msg.from_user else "Unknown"
    try:
        admins = await update.effective_chat.get_administrators()
        mentions = " ".join(
            f'<a href="tg://user?id={a.user.id}">{a.user.first_name}</a>'
            for a in admins if not a.user.is_bot
        )
        await update.message.reply_text(
            f"🚨 <b>Report</b>\nFrom: {reporter}\nAbout: {reported_user}\n\n"
            f"Admins notified:\n{mentions}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"Could not fetch admins: {e}")


# ── Info ──────────────────────────────────────────────────────────────────────

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context) or update.effective_user
    warns = db.get_warns(target.id, update.effective_chat.id)
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, target.id)
        status = member.status.capitalize()
    except Exception:
        status = "Unknown"
    bar = "🔴" * warns + "⚪" * max(0, WARN_LIMIT - warns)
    await update.message.reply_text(
        f"👤 <b>User Info</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Name: {user_link(target)}\n"
        f"User ID: <code>{target.id}</code>\n"
        f"Username: @{target.username or 'none'}\n"
        f"Status: {status}\n"
        f"Warnings: {bar} <b>{warns}/{WARN_LIMIT}</b>",
        parse_mode="HTML",
    )


# ── Log ───────────────────────────────────────────────────────────────────────

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_recent_logs(update.effective_chat.id)
    if not rows:
        await update.message.reply_text("No admin actions logged yet.")
        return
    lines = ["📋 <b>Recent Admin Actions</b>\n━━━━━━━━━━━━━━━━\n"]
    for row in rows:
        target = f" → {row['target_user']}" if row["target_user"] else ""
        lines.append(
            f"[{row['timestamp']}] <b>{row['admin_name']}</b>: "
            f"{row['action']}{target}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── /utag — tag all seen members ──────────────────────────────────────────────

async def utag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("This command only works in groups.")
        return

    members = db.get_seen_members(chat.id)
    if not members:
        await update.message.reply_text(
            "⚠️ No members tracked yet.\n"
            "Members are tracked once they send a message in this group."
        )
        return

    extra_msg = " ".join(context.args) if context.args else ""
    header = f"📢 <b>Tag All</b>{chr(10) + extra_msg if extra_msg else ''}\n\n"

    # Build mention list — split into chunks of ≤4096 chars
    mentions = []
    for row in members:
        uid  = row["user_id"]
        name = (row["first_name"] or row["username"] or str(uid))[:30]
        mentions.append(f'<a href="tg://user?id={uid}">{name}</a>')

    # Send in chunks of 50 mentions per message to avoid length limits
    chunk_size = 50
    chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]

    active_utag[chat.id] = True
    total_sent = 0
    for idx, chunk in enumerate(chunks):
        # Check if cancelled
        if not active_utag.get(chat.id, False):
            await update.message.reply_text(
                f"🛑 Tag operation cancelled after tagging <b>{total_sent}</b> member(s).",
                parse_mode="HTML"
            )
            active_utag.pop(chat.id, None)
            return
        text = (header if idx == 0 else "") + " ".join(chunk)
        if len(text) > 4096:
            text = text[:4090] + "…"
        await update.message.reply_text(text, parse_mode="HTML")
        total_sent += len(chunk)
        await asyncio.sleep(0.3)

    active_utag.pop(chat.id, None)
    total = len(members)
    await update.message.reply_text(
        f"✅ Tagged <b>{total}</b> member{'s' if total != 1 else ''}.",
        parse_mode="HTML"
    )


# ── /broadcast — owner only: send message to all users and groups ─────────────

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the bot owner.")
        return

    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📢 <b>Broadcast</b>\n\n"
            "Usage: <code>/broadcast Your message here</code>\n"
            "Or reply to a message with /broadcast to forward it.\n\n"
            "Sends to all known users and groups.",
            parse_mode="HTML"
        )
        return

    if update.message.reply_to_message:
        text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    else:
        text = " ".join(context.args)

    if not text.strip():
        await update.message.reply_text("❌ Cannot broadcast an empty message.")
        return

    status_msg = await update.message.reply_text("📤 Broadcasting…")

    all_chats = db.get_all_chat_ids()
    all_users = db.get_all_user_ids()

    # Combine and deduplicate
    targets = list(set(all_chats + all_users))

    sent = 0
    failed = 0
    for target_id in targets:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"📢 <b>Broadcast from Admin</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent += 1
            await asyncio.sleep(0.05)  # Respect rate limits
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast complete!</b>\n\n"
        f"Sent: <b>{sent}</b>\n"
        f"Failed: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ── /setgoodbye ───────────────────────────────────────────────────────────────

async def setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(no_permission_msg())
        return

    USAGE = (
        "<b>Set Goodbye Message</b>\n\n"
        "Usage: <code>/setgoodbye Goodbye {name}, we'll miss you!</code>\n\n"
        "<b>Variables:</b>\n"
        "  {name} — member's first name\n"
        "  {username} — @username\n"
        "  {mention} — clickable mention\n\n"
        "<b>Example:</b>\n"
        "<code>/setgoodbye 👋 {mention} has left the group. Bye!</code>"
    )

    if not context.args:
        await update.message.reply_text(USAGE, parse_mode="HTML")
        return

    text = " ".join(context.args)
    db.set_goodbye(update.effective_chat.id, text)

    user = update.effective_user
    preview = (
        text
        .replace("{name}", user.first_name)
        .replace("{username}", f"@{user.username}" if user.username else user.first_name)
        .replace("{mention}", f'<a href="tg://user?id={user.id}">{user.first_name}</a>')
    )
    await update.message.reply_text(
        f"✅ Goodbye message saved!\n\n<b>Preview:</b>\n{preview}",
        parse_mode="HTML"
    )


# ── Goodbye when member leaves ────────────────────────────────────────────────

async def goodbye_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    left_user = update.message.left_chat_member
    if not left_user or left_user.is_bot:
        return
    chat_id = update.effective_chat.id
    text    = db.get_goodbye(chat_id)
    if not text:
        return
    name     = left_user.first_name or ""
    username = f"@{left_user.username}" if left_user.username else name
    mention  = f'<a href="tg://user?id={left_user.id}">{name}</a>'
    text = (
        text
        .replace("{name}", name)
        .replace("{first_name}", name)
        .replace("{username}", username)
        .replace("{mention}", mention)
    )
    try:
        await context.bot.send_message(chat_id, text, parse_mode="HTML")
    except Exception:
        pass


# ── /cancletage — cancel a running /utag ─────────────────────────────────────

async def cancletage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel an in-progress /utag operation in this chat."""
    chat    = update.effective_chat
    user    = update.effective_user

    member = await chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await update.message.reply_text("❌ Only admins can cancel tagging.")
        return

    if active_utag.get(chat.id):
        active_utag[chat.id] = False
        await update.message.reply_text("🛑 Stopping the tag operation… please wait.")
    else:
        await update.message.reply_text("ℹ️ No active tagging operation to cancel.")


# ── /lag — language switcher ──────────────────────────────────────────────────

async def lag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection buttons."""
    user    = update.effective_user
    current = db.get_user_language(user.id) or "en"

    buttons = []
    row: list = []
    for code, (flag, label) in BOT_LANGUAGES.items():
        mark = " ✅" if code == current else ""
        row.append(InlineKeyboardButton(
            f"{flag} {label}{mark}",
            callback_data=f"lang_{code}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await update.message.reply_text(
        f"🌐 <b>Select your language</b>\n"
        f"Current: <b>{BOT_LANGUAGES.get(current, ('', 'English'))[1]}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection button press."""
    query = update.callback_query
    code  = query.data.replace("lang_", "")
    user  = query.from_user

    if code not in BOT_LANGUAGES:
        await query.answer("Unknown language.", show_alert=True)
        return

    db.set_user_language(user.id, code)
    flag, label = BOT_LANGUAGES[code]

    # Rebuild keyboard with new selection marked
    buttons = []
    row: list = []
    for c, (f, lbl) in BOT_LANGUAGES.items():
        mark = " ✅" if c == code else ""
        row.append(InlineKeyboardButton(f"{f} {lbl}{mark}", callback_data=f"lang_{c}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await query.edit_message_text(
        f"🌐 <b>Select your language</b>\n"
        f"Current: <b>{label}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    await query.answer(f"{flag} Language set to {label}!")
