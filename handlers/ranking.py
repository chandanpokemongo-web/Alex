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
