import re
import time
import random
import string
import httpx
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

QUOTES = [
    "The secret of getting ahead is getting started. — Mark Twain",
    "It does not matter how slowly you go as long as you do not stop. — Confucius",
    "Success is not final, failure is not fatal: It is the courage to continue that counts. — Churchill",
    "Believe you can and you're halfway there. — Theodore Roosevelt",
    "The only way to do great work is to love what you do. — Steve Jobs",
    "Life is what happens when you're busy making other plans. — John Lennon",
    "In the middle of every difficulty lies opportunity. — Albert Einstein",
    "It always seems impossible until it's done. — Nelson Mandela",
    "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
    "You miss 100% of the shots you don't take. — Wayne Gretzky",
    "Whether you think you can or think you can't, you're right. — Henry Ford",
    "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
    "Hardships often prepare ordinary people for an extraordinary destiny. — C.S. Lewis",
    "Do what you can, with what you have, where you are. — Theodore Roosevelt",
    "Dream big and dare to fail. — Norman Vaughan",
    "Act as if what you do makes a difference. It does. — William James",
    "What we think, we become. — Buddha",
    "The best time to plant a tree was 20 years ago. The second best time is now. — Chinese Proverb",
    "Your time is limited, don't waste it living someone else's life. — Steve Jobs",
    "Strive not to be a success, but rather to be of value. — Albert Einstein",
]


def _parse_time_delta(s: str):
    """Parse strings like 10s, 5m, 2h, 1d into a timedelta."""
    match = re.fullmatch(r"(\d+)([smhd])", s.lower().strip())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    return timedelta(seconds={"s": 1, "m": 60, "h": 3600, "d": 86400}[unit] * val)


def _time_ago(since_str: str) -> str:
    try:
        since = datetime.strptime(since_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.utcnow() - since
        secs = int(diff.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        elif secs < 3600:
            return f"{secs // 60}m ago"
        elif secs < 86400:
            return f"{secs // 3600}h ago"
        else:
            return f"{secs // 86400}d ago"
    except Exception:
        return "a while ago"


# ── /afk ──────────────────────────────────────────────────────────────────────

async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args) if context.args else "No reason given"
    db.set_afk(user.id, reason)
    await update.message.reply_text(
        f'<a href="tg://user?id={user.id}">{user.first_name}</a> is now <b>AFK</b>\n'
        f'Reason: <i>{reason}</i>\n\n'
        f'<i>I will notify others when they mention you. Send any message to return.</i>',
        parse_mode="HTML"
    )


async def unafk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    afk_data = db.get_afk(user.id)
    if not afk_data:
        await update.message.reply_text("You are not AFK.")
        return
    db.remove_afk(user.id)
    ago = _time_ago(afk_data["since"])
    await update.message.reply_text(
        f'Welcome back, <a href="tg://user?id={user.id}">{user.first_name}</a>!\n'
        f'You were AFK for <b>{ago}</b>.',
        parse_mode="HTML"
    )


async def check_afk_on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called on every text message. Handles two things:
    1. If sender is AFK → remove AFK and welcome back.
    2. If sender mentions/replies to an AFK user → notify."""
    if not update.message or not update.effective_user:
        return

    sender = update.effective_user

    # Auto-remove AFK when the AFK user speaks
    sender_afk = db.get_afk(sender.id)
    if sender_afk:
        db.remove_afk(sender.id)
        ago = _time_ago(sender_afk["since"])
        try:
            await update.message.reply_text(
                f'Welcome back, <a href="tg://user?id={sender.id}">{sender.first_name}</a>! '
                f'You were AFK for <b>{ago}</b>.',
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # Check if replying to an AFK user
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
        if target.id != sender.id:
            afk_data = db.get_afk(target.id)
            if afk_data:
                ago = _time_ago(afk_data["since"])
                reason = afk_data["reason"]
                try:
                    await update.message.reply_text(
                        f'<a href="tg://user?id={target.id}">{target.first_name}</a> is AFK '
                        f'(<b>{ago}</b>)\nReason: <i>{reason}</i>',
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    # Check if any @username mentioned is AFK
    msg_text = update.message.text or ""
    mentions = re.findall(r"@(\w+)", msg_text)
    for username in mentions:
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, username)
            target = member.user
            if target.id == sender.id:
                continue
            afk_data = db.get_afk(target.id)
            if afk_data:
                ago = _time_ago(afk_data["since"])
                await update.message.reply_text(
                    f'<a href="tg://user?id={target.id}">{target.first_name}</a> is AFK '
                    f'(<b>{ago}</b>)\nReason: <i>{afk_data["reason"]}</i>',
                    parse_mode="HTML"
                )
        except Exception:
            pass


# ── /id ───────────────────────────────────────────────────────────────────────

async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
    lines = [
        f"<b>User Info</b>",
        f"Name: {target.first_name}",
        f"User ID: <code>{target.id}</code>",
        f"Username: @{target.username or 'none'}",
    ]
    if chat.type != "private":
        lines.append(f"Chat ID: <code>{chat.id}</code>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── /ping ─────────────────────────────────────────────────────────────────────

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.monotonic()
    msg = await update.message.reply_text("Pinging...")
    elapsed = int((time.monotonic() - start) * 1000)
    await msg.edit_text(f"Pong! Response time: <b>{elapsed}ms</b>", parse_mode="HTML")


# ── /calc ─────────────────────────────────────────────────────────────────────

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /calc [expression]\nExample: /calc 25 * 4 + 10")
        return
    expr = " ".join(context.args)
    allowed = re.fullmatch(r"[\d\s\+\-\*\/\(\)\.\%\^]+", expr)
    if not allowed:
        await update.message.reply_text(
            "Only numbers and operators (+, -, *, /, %, ^, brackets) are allowed.")
        return
    try:
        safe_expr = expr.replace("^", "**")
        result = eval(safe_expr, {"__builtins__": {}}, {})
        if isinstance(result, float) and result == int(result):
            result = int(result)
        await update.message.reply_text(
            f"<code>{expr}</code>  =  <b>{result}</b>", parse_mode="HTML")
    except ZeroDivisionError:
        await update.message.reply_text("Cannot divide by zero.")
    except Exception:
        await update.message.reply_text("Could not calculate that expression.")


# ── /quote ────────────────────────────────────────────────────────────────────

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(QUOTES)
    parts = q.rsplit(" — ", 1)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another quote", callback_data="quote_new")]])
    if len(parts) == 2:
        text = f'<i>"{parts[0]}"</i>\n\n— <b>{parts[1]}</b>'
    else:
        text = f"<i>{q}</i>"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def quote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    q = random.choice(QUOTES)
    parts = q.rsplit(" — ", 1)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another quote", callback_data="quote_new")]])
    if len(parts) == 2:
        text = f'<i>"{parts[0]}"</i>\n\n— <b>{parts[1]}</b>'
    else:
        text = f"<i>{q}</i>"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


# ── /choose ───────────────────────────────────────────────────────────────────

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Give me at least 2 options!\nUsage: /choose pizza burger sushi")
        return
    options = context.args
    picked = random.choice(options)
    await update.message.reply_text(
        f"I choose: <b>{picked}</b>", parse_mode="HTML")


# ── /flip (decision) ─────────────────────────────────────────────────────────

async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) >= 2:
        a, b = context.args[0], context.args[1]
        result = random.choice([a, b])
        await update.message.reply_text(
            f"<b>{result}</b> wins the flip!", parse_mode="HTML")
    else:
        result = random.choice(["Heads", "Tails"])
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Flip again", callback_data="coin_flip")]])
        await update.message.reply_text(
            f"<b>{result}!</b>", parse_mode="HTML", reply_markup=keyboard)


# ── /remind ───────────────────────────────────────────────────────────────────

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /remind [time] [message]\n"
            "Examples:\n"
            "  /remind 10m check the oven\n"
            "  /remind 2h team meeting\n"
            "  /remind 1d pay rent\n\n"
            "Time units: s (seconds), m (minutes), h (hours), d (days)"
        )
        return
    delta = _parse_time_delta(context.args[0])
    if not delta:
        await update.message.reply_text(
            "Invalid time format. Use: 10s, 5m, 2h, 1d")
        return
    if delta.total_seconds() < 10:
        await update.message.reply_text("Minimum reminder time is 10 seconds.")
        return
    if delta.total_seconds() > 7 * 86400:
        await update.message.reply_text("Maximum reminder time is 7 days.")
        return

    text = " ".join(context.args[1:])
    fire_at = datetime.utcnow() + delta
    user = update.effective_user

    rid = db.add_reminder(
        user.id, update.effective_chat.id,
        update.message.message_id, text, fire_at
    )

    # Format readable time
    secs = int(delta.total_seconds())
    if secs < 3600:
        readable = f"{secs // 60} minute{'s' if secs // 60 != 1 else ''}"
    elif secs < 86400:
        readable = f"{secs // 3600} hour{'s' if secs // 3600 != 1 else ''}"
    else:
        readable = f"{secs // 86400} day{'s' if secs // 86400 != 1 else ''}"

    await update.message.reply_text(
        f"Reminder set! I will remind you in <b>{readable}</b>.\n"
        f'Message: <i>"{text}"</i>',
        parse_mode="HTML"
    )

    # Schedule the reminder using job queue
    context.job_queue.run_once(
        _fire_reminder,
        when=delta,
        data={"rid": rid, "user_id": user.id, "chat_id": update.effective_chat.id,
              "text": text, "name": user.first_name},
        name=f"reminder_{rid}"
    )


async def _fire_reminder(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    db.mark_reminder_done(data["rid"])
    try:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text=(
                f'<a href="tg://user?id={data["user_id"]}">{data["name"]}</a>, '
                f'here is your reminder!\n\n'
                f'<b>{data["text"]}</b>'
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


# ── /stats ────────────────────────────────────────────────────────────────────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    rows = db.get_ranking(chat.id, limit=100)
    total_msgs = sum(r["message_count"] for r in rows)
    total_members = len(rows)
    top = rows[0] if rows else None
    top_name = top["first_name"] or top["username"] if top else "Nobody"
    top_count = top["message_count"] if top else 0

    scores = db.get_top_scores(chat.id, limit=100)
    total_trivia = sum(r["trivia_score"] for r in scores)

    await update.message.reply_text(
        f"<b>Group Stats</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Total messages tracked: <b>{total_msgs:,}</b>\n"
        f"Active members: <b>{total_members}</b>\n"
        f"Most active: <b>{top_name}</b> ({top_count:,} msgs)\n"
        f"Total trivia points given: <b>{total_trivia}</b>",
        parse_mode="HTML"
    )


# ── /weather ──────────────────────────────────────────────────────────────────

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /weather [city]\nExample: /weather Mumbai")
        return
    city = " ".join(context.args)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://wttr.in/{city}?format=4",
                headers={"User-Agent": "curl/7.68.0"}
            )
            resp2 = await client.get(
                f"https://wttr.in/{city}?format=%l:+%c+%t,+Humidity:+%h,+Wind:+%w",
                headers={"User-Agent": "curl/7.68.0"}
            )
        if resp.status_code == 200 and resp.text.strip():
            main_line = resp.text.strip()
            detail = resp2.text.strip() if resp2.status_code == 200 else ""
            reply = f"🌤 <b>Weather — {city.title()}</b>\n━━━━━━━━━━━━━━━━\n<code>{main_line}</code>"
            if detail and detail != main_line:
                reply += f"\n\n{detail}"
            await update.message.reply_text(reply, parse_mode="HTML")
        else:
            await update.message.reply_text(
                f"Could not find weather for <b>{city}</b>. Check the city name.",
                parse_mode="HTML"
            )
    except Exception:
        await update.message.reply_text("Weather service unavailable right now. Try again later.")


# ── /define ───────────────────────────────────────────────────────────────────

async def define(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /define [word]\nExample: /define serendipity")
        return
    word = context.args[0].lower().strip()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            await update.message.reply_text(f"No definition found for <b>{word}</b>.", parse_mode="HTML")
            return
        data = resp.json()
        entry = data[0]
        phonetic = entry.get("phonetic", "")
        meanings = entry.get("meanings", [])[:2]
        lines = [f"📖 <b>{word}</b>  {phonetic}\n"]
        for meaning in meanings:
            part = meaning.get("partOfSpeech", "")
            defs = meaning.get("definitions", [])[:2]
            lines.append(f"<i>{part}</i>")
            for i, d in enumerate(defs, 1):
                definition = d.get("definition", "")
                example = d.get("example", "")
                lines.append(f"  {i}. {definition}")
                if example:
                    lines.append(f"     <i>e.g. \"{example}\"</i>")
            lines.append("")
        await update.message.reply_text("\n".join(lines).strip(), parse_mode="HTML")
    except Exception:
        await update.message.reply_text("Dictionary service unavailable right now.")


# ── /fact ─────────────────────────────────────────────────────────────────────

async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
                headers={"Accept": "application/json"}
            )
        if resp.status_code == 200:
            text = resp.json().get("text", "")
            if text:
                await update.message.reply_text(f"💡 <b>Random Fact</b>\n\n{text}", parse_mode="HTML")
                return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch a fact right now. Try again!")


# ── /bmi ──────────────────────────────────────────────────────────────────────

async def bmi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /bmi [weight kg] [height cm]\nExample: /bmi 70 175")
        return
    try:
        weight = float(context.args[0])
        height_cm = float(context.args[1])
        height_m = height_cm / 100
        bmi_val = weight / (height_m ** 2)
        if bmi_val < 18.5:
            category, icon = "Underweight", "🟡"
        elif bmi_val < 25:
            category, icon = "Normal weight", "🟢"
        elif bmi_val < 30:
            category, icon = "Overweight", "🟠"
        else:
            category, icon = "Obese", "🔴"
        await update.message.reply_text(
            f"⚖️ <b>BMI Calculator</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Weight: <b>{weight} kg</b>\n"
            f"Height: <b>{height_cm} cm</b>\n"
            f"BMI: <b>{bmi_val:.1f}</b>\n"
            f"Category: {icon} <b>{category}</b>",
            parse_mode="HTML"
        )
    except (ValueError, ZeroDivisionError):
        await update.message.reply_text("Please enter valid numbers. Example: /bmi 70 175")


# ── /age ──────────────────────────────────────────────────────────────────────

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /age [DD/MM/YYYY]\nExample: /age 15/08/2000")
        return
    try:
        dob = datetime.strptime(context.args[0], "%d/%m/%Y")
        today = datetime.today()
        if dob > today:
            await update.message.reply_text("That date is in the future!")
            return
        years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        next_bday = dob.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        days_left = (next_bday - today).days
        await update.message.reply_text(
            f"🎂 <b>Age Calculator</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Date of birth: <b>{dob.strftime('%d %b %Y')}</b>\n"
            f"Age: <b>{years} years old</b>\n"
            f"Next birthday: <b>{days_left} day{'s' if days_left != 1 else ''} away</b> 🎉",
            parse_mode="HTML"
        )
    except ValueError:
        await update.message.reply_text("Invalid date! Use DD/MM/YYYY format. Example: /age 15/08/2000")


# ── /countdown ────────────────────────────────────────────────────────────────

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /countdown [DD/MM/YYYY]\nExample: /countdown 31/12/2025")
        return
    try:
        target = datetime.strptime(context.args[0], "%d/%m/%Y")
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (target - today).days
        if delta < 0:
            await update.message.reply_text(
                f"⏳ <b>{target.strftime('%d %b %Y')}</b> was <b>{abs(delta)} days ago</b>.",
                parse_mode="HTML"
            )
        elif delta == 0:
            await update.message.reply_text(f"🎉 <b>Today is {target.strftime('%d %b %Y')}!</b>", parse_mode="HTML")
        else:
            await update.message.reply_text(
                f"⏳ <b>Countdown to {target.strftime('%d %b %Y')}</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"<b>{delta} day{'s' if delta != 1 else ''}</b> remaining! ⏰",
                parse_mode="HTML"
            )
    except ValueError:
        await update.message.reply_text("Invalid date! Use DD/MM/YYYY. Example: /countdown 31/12/2025")


# ── /password ─────────────────────────────────────────────────────────────────

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 16
    if context.args:
        try:
            length = int(context.args[0])
            length = max(6, min(64, length))
        except ValueError:
            pass
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = "".join(random.choices(chars, k=length))
    await update.message.reply_text(
        f"🔐 <b>Generated Password</b> ({length} chars)\n"
        f"<code>{pwd}</code>\n\n"
        f"<i>Copy it quickly — delete this message after saving!</i>",
        parse_mode="HTML"
    )


# ── /number ───────────────────────────────────────────────────────────────────

async def number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 9999)
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            pass
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"http://numbersapi.com/{n}?json")
        if resp.status_code == 200:
            fact_text = resp.json().get("text", "")
            if fact_text:
                await update.message.reply_text(
                    f"🔢 <b>Number {n}</b>\n\n{fact_text}", parse_mode="HTML")
                return
    except Exception:
        pass
    await update.message.reply_text(f"Could not fetch a fact for {n}. Try again!")


# ── /roll ─────────────────────────────────────────────────────────────────────

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notation = context.args[0] if context.args else "1d6"
    match = re.fullmatch(r"(\d{1,2})d(\d{1,4})", notation.lower())
    if not match:
        await update.message.reply_text("Usage: /roll [NdN]\nExamples: /roll 2d6  /roll 1d20  /roll 3d8")
        return
    num_dice, sides = int(match.group(1)), int(match.group(2))
    num_dice = max(1, min(20, num_dice))
    sides = max(2, min(1000, sides))
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    total = sum(rolls)
    rolls_str = " + ".join(str(r) for r in rolls) if num_dice > 1 else str(rolls[0])
    result_line = f"= <b>{total}</b>" if num_dice > 1 else f"→ <b>{total}</b>"
    await update.message.reply_text(
        f"🎲 <b>Roll {notation}</b>\n{rolls_str} {result_line}",
        parse_mode="HTML"
    )


# ── /qr ───────────────────────────────────────────────────────────────────────

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /qr [text or URL]\nExample: /qr https://t.me/yourgroupname")
        return
    text = " ".join(context.args)
    if len(text) > 500:
        await update.message.reply_text("Text too long! Maximum 500 characters.")
        return
    import urllib.parse
    encoded = urllib.parse.quote(text)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(qr_url)
        if resp.status_code == 200:
            from io import BytesIO
            img = BytesIO(resp.content)
            img.name = "qr.png"
            await update.message.reply_photo(
                photo=img,
                caption=f"📱 QR Code for:\n<code>{text[:100]}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("Could not generate QR code. Try again!")
    except Exception:
        await update.message.reply_text("QR service unavailable. Try again later.")
