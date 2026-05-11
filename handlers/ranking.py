import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _build_ranking_image(rows: list, title: str = "LEADERBOARD") -> io.BytesIO | None:
    """Generate a simple bar chart leaderboard image."""
    if not PIL_AVAILABLE or not rows:
        return None
    try:
        W, H = 700, 40 + len(rows) * 44 + 20
        img = Image.new("RGB", (W, H), color=(15, 20, 40))
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_name  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_score = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except Exception:
            font_title = ImageFont.load_default()
            font_name  = ImageFont.load_default()
            font_score = ImageFont.load_default()

        draw.text((W // 2, 10), title, font=font_title, fill=(255, 255, 255), anchor="mt")

        max_val = max(r.get("message_count", r.get("count", 1)) for r in rows) or 1
        bar_area_w = W - 200
        bar_h = 24
        y_start = 44

        for i, row in enumerate(rows):
            y = y_start + i * 44
            name  = (row.get("first_name") or row.get("username") or f"User{row.get('user_id','')}") [:22]
            score = row.get("message_count", row.get("count", 0))
            ratio = score / max_val
            bar_w = max(4, int(bar_area_w * ratio))

            bar_color = (41, 121, 255) if i > 0 else (255, 200, 0)
            draw.rounded_rectangle(
                [140, y, 140 + bar_w, y + bar_h],
                radius=5, fill=bar_color
            )
            rank_label = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            draw.text((10, y + bar_h // 2), f"{rank_label} {name}", font=font_name,
                      fill=(220, 220, 220), anchor="lm")
            draw.text((140 + bar_w + 6, y + bar_h // 2), f"{score:,}",
                      font=font_score, fill=(255, 255, 255), anchor="lm")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception:
        return None


def _build_ranking_text(rows: list, mode: str = "overall") -> str:
    if not rows:
        return "No data yet for this period."
    medals = ["🥇", "🥈", "🥉"]
    key = "message_count" if mode == "overall" else "count"
    lines = []
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name  = row.get("first_name") or row.get("username") or f"User{row.get('user_id','')}"
        score = row.get(key, 0)
        lines.append(f"{medal} <b>{name}</b> — {score:,} msg{'s' if score != 1 else ''}")
    return "\n".join(lines)


def _rank_keyboard(current: str, chat_id: int) -> InlineKeyboardMarkup:
    def btn(label: str, mode: str) -> InlineKeyboardButton:
        check = " ✅" if mode == current else ""
        return InlineKeyboardButton(f"⚪ {label}{check}", callback_data=f"rank_{mode}_{chat_id}")
    return InlineKeyboardMarkup([
        [btn("Overall", "overall"), btn("Today", "today"), btn("Week", "week")],
        [InlineKeyboardButton("📊 View complete leaderboard", callback_data=f"rank_full_{chat_id}")],
    ])


async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user = update.effective_user
    if user.is_bot:
        return
    db.increment_message_count(
        user.id,
        update.effective_chat.id,
        user.username or "",
        user.first_name or ""
    )


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = db.get_ranking(chat_id, limit=10)
    if not rows:
        await update.message.reply_text(
            "No messages counted yet.\n"
            "Every message in this group is tracked automatically."
        )
        return

    text = (
        f"📊 <b>Leaderboard</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{_build_ranking_text(rows, 'overall')}"
    )
    kb = _rank_keyboard("overall", chat_id)
    img_buf = _build_ranking_image(rows)
    if img_buf:
        await update.message.reply_photo(
            photo=img_buf,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def ranking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split("_")
    if len(parts) < 3:
        return

    mode    = parts[1]
    chat_id = int(parts[2])

    if mode == "full":
        rows = db.get_ranking(chat_id, limit=50)
        if not rows:
            await query.answer("No data yet!", show_alert=True)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = ["📊 <b>Full Leaderboard</b>\n━━━━━━━━━━━━━━━━\n"]
        for i, row in enumerate(rows):
            medal = medals[i] if i < 3 else f"{i+1}."
            name  = row.get("first_name") or row.get("username") or f"User{row['user_id']}"
            score = row.get("message_count", 0)
            lines.append(f"{medal} <b>{name}</b> — {score:,} msgs")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3990] + "\n…"
        await query.message.reply_text(text, parse_mode="HTML")
        return

    if mode == "overall":
        rows = db.get_ranking(chat_id, limit=10)
        label = "Overall"
    elif mode == "today":
        rows = db.get_ranking_today(chat_id, limit=10)
        label = "Today"
    elif mode == "week":
        rows = db.get_ranking_week(chat_id, limit=10)
        label = "This Week"
    else:
        return

    if not rows:
        await query.answer(f"No data for {label} yet!", show_alert=True)
        return

    text = (
        f"📊 <b>Leaderboard — {label}</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{_build_ranking_text(rows, mode)}"
    )
    kb = _rank_keyboard(mode, chat_id)
    img_buf = _build_ranking_image(rows, title=f"LEADERBOARD – {label.upper()}")

    try:
        if img_buf:
            from telegram import InputMediaPhoto
            await query.edit_message_media(
                media=InputMediaPhoto(media=img_buf, caption=text, parse_mode="HTML"),
                reply_markup=kb,
            )
        else:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        if img_buf:
            img_buf.seek(0)
            await query.message.reply_photo(
                photo=img_buf, caption=text,
                parse_mode="HTML", reply_markup=kb
            )
        else:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


# ── New ranking commands ───────────────────────────────────────────────────────

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for /ranking."""
    await ranking(update, context)


async def topgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = db.get_top_scores(chat_id, limit=10)
    if not rows:
        await update.message.reply_text("No game scores yet. Play /trivia to earn points!")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, row in enumerate(rows):
        m    = medals[i] if i < 3 else f"{i+1}."
        name = row.get("first_name") or row.get("username") or f"User{row.get('user_id','')}"
        pts  = row.get("count", row.get("score", 0))
        lines.append(f"{m} <b>{name}</b> — {pts} pts")
    await update.message.reply_text(
        f"🎮 <b>Game Leaderboard</b>\n━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def topusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        all_ids = db.get_all_user_ids()
        await update.message.reply_text(
            f"👥 <b>Global Users</b>\n\nTotal registered users: <b>{len(all_ids):,}</b>\n\n"
            "Use /ranking to see this group's top members.",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text(
            "👥 <b>Global Users</b>\n\nUse /ranking for this group's leaderboard.",
            parse_mode="HTML"
        )


async def topgroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        all_chats = db.get_all_chat_ids()
        await update.message.reply_text(
            f"🌐 <b>Global Groups</b>\n\nBot is active in <b>{len(all_chats):,}</b> chats.\n\n"
            "Use /groupstats for this group's stats.",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text(
            "🌐 <b>Global Groups</b>\n\nCould not fetch global stats.",
            parse_mode="HTML"
        )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    uid     = user.id
    name    = user.first_name or user.username or f"User{uid}"

    # Get message count for this chat
    rows = db.get_ranking(chat_id, limit=500)
    rank = None
    msgs = 0
    for i, row in enumerate(rows):
        if row.get("user_id") == uid:
            rank = i + 1
            msgs = row.get("message_count", 0)
            break

    # Get trivia score
    score_rows = db.get_top_scores(chat_id, limit=500)
    trivia_pts = 0
    trivia_rank = None
    for i, row in enumerate(score_rows):
        if row.get("user_id") == uid:
            trivia_pts  = row.get("count", row.get("score", 0))
            trivia_rank = i + 1
            break

    # Get collection count
    try:
        collection = db.get_collection(uid)
        col_count  = len(collection) if collection else 0
    except Exception:
        col_count = 0

    # Get coin balance
    try:
        coins = db.add_rb_coins(uid, 0)
    except Exception:
        coins = 0

    rank_str   = f"#{rank}" if rank else "Unranked"
    t_rank_str = f"#{trivia_rank}" if trivia_rank else "Unranked"

    await update.message.reply_text(
        f"👤 <b>Profile: {name}</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"💬 Messages in group: <b>{msgs:,}</b> (Rank {rank_str})\n"
        f"🎮 Trivia points: <b>{trivia_pts}</b> (Rank {t_rank_str})\n"
        f"🃏 Collection cards: <b>{col_count}</b>\n"
        f"💰 RB Coins: <b>{coins:,}</b>",
        parse_mode="HTML"
    )


async def mygifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id
    try:
        collection = db.get_collection(uid)
        if not collection:
            await update.message.reply_text(
                "🎁 You have no gifts yet.\n\nPlay /cricket or /pick to earn character cards!"
            )
            return
        # Show last 10 received as "gifts"
        recent = collection[-10:]
        lines  = []
        for item in reversed(recent):
            name   = item.get("item_name", "Unknown")
            source = item.get("source", "?")
            rarity = item.get("rarity", "")
            lines.append(f"🎁 <b>{name}</b> [{source}] {rarity}")
        await update.message.reply_text(
            f"🎁 <b>Your Recent Gifts</b>\n━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text("Could not fetch your gifts. Try /collection instead.")


async def mytop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id
    name = user.first_name or user.username or f"User{uid}"
    try:
        coin_balance = db.add_rb_coins(uid, 0)
        await update.message.reply_text(
            f"📊 <b>{name}'s Global Rank</b>\n\n"
            f"💰 RB Coins: <b>{coin_balance:,}</b>\n"
            f"🎮 Use /profile for full stats in this group.\n"
            f"🏆 Use /topgame for the game leaderboard.",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text(
            f"📊 <b>{name}'s Stats</b>\n\nUse /profile for your full stats.",
            parse_mode="HTML"
        )


async def groupstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("⚠️ This command is for admins only.")
            return
    except Exception:
        pass

    chat    = update.effective_chat
    chat_id = chat.id

    rows = db.get_ranking(chat_id, limit=1000)
    total_members = len(rows)
    total_msgs    = sum(r.get("message_count", 0) for r in rows)
    top_user      = rows[0] if rows else None

    score_rows = db.get_top_scores(chat_id, limit=10)
    top_gamer  = score_rows[0] if score_rows else None

    text = (
        f"📊 <b>Group Stats: {chat.title}</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👥 Tracked members: <b>{total_members:,}</b>\n"
        f"💬 Total messages: <b>{total_msgs:,}</b>\n"
    )
    if top_user:
        tname = top_user.get("first_name") or top_user.get("username") or "Unknown"
        text += f"🏆 Top chatter: <b>{tname}</b> ({top_user.get('message_count', 0):,} msgs)\n"
    if top_gamer:
        gname = top_gamer.get("first_name") or top_gamer.get("username") or "Unknown"
        text += f"🎮 Top gamer: <b>{gname}</b> ({top_gamer.get('count', 0)} pts)\n"
    await update.message.reply_text(text, parse_mode="HTML")


async def stophangman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("⚠️ Admins only.")
            return
    except Exception:
        pass
    from handlers import fun as fun_module
    chat_id = update.effective_chat.id
    if chat_id in fun_module.active_hangman:
        del fun_module.active_hangman[chat_id]
        await update.message.reply_text("✅ Hangman game stopped by admin.")
    else:
        await update.message.reply_text("No active hangman game in this chat.")


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("⚠️ Admins only.")
            return
    except Exception:
        pass
    chat = update.effective_chat
    try:
        rules = db.get_rules(chat.id)
    except Exception:
        rules = None
    try:
        welcome = db.get_welcome(chat.id)
    except Exception:
        welcome = None
    await update.message.reply_text(
        f"⚙️ <b>Settings: {chat.title}</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"📋 Rules: {'✅ Set' if rules else '❌ Not set'}\n"
        f"👋 Welcome: {'✅ Set' if welcome else '❌ Not set'}\n\n"
        f"<b>Config commands:</b>\n"
        f"/setrules — Set group rules\n"
        f"/setwelcome — Set welcome message\n"
        f"/setgoodbye — Set goodbye message\n"
        f"/lock — Lock message types\n"
        f"/slowmode [seconds] — Set slow mode",
        parse_mode="HTML"
    )
