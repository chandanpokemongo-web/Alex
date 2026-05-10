"""
handlers/tools.py — 40+ utility, fun, info, and creative commands.
All APIs used here are free with no key required.
"""

import asyncio
import base64
import hashlib
import random
import re
import uuid as uuid_lib
from datetime import datetime
from io import BytesIO
from urllib.parse import quote, unquote, quote_plus

import httpx
from telegram import Update
from telegram.ext import ContextTypes

# ── Local data ────────────────────────────────────────────────────────────────

_MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/',
}

_BOLD_MAP   = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                             '𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵')
_ITALIC_MAP = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                             '𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻')

_COMPLIMENTS = [
    "You have an amazing presence — people light up when you walk in!",
    "Your creativity is genuinely inspiring.",
    "You make everything more fun just by being there.",
    "You have a heart of gold and everyone notices.",
    "You're stronger than you realise, and it shows.",
    "You make the world a better place just by being in it.",
    "Your laugh is contagious — keep spreading it!",
    "You have a rare ability to make people feel heard.",
    "You're genuinely funny without even trying.",
    "Honestly? Pretty amazing. Just saying.",
]

_ROASTS = [
    "You're like a cloud. When you disappear, it's a beautiful day.",
    "I'd roast you harder but my mom said I shouldn't burn trash.",
    "You're not stupid — you just have bad luck thinking.",
    "You're the reason they put instructions on shampoo.",
    "Your secrets are safe with me. I never listen to what you say anyway.",
    "If I had a dollar for every time you said something smart, I'd be broke.",
    "You bring everyone so much joy... when you leave the room.",
    "I'd agree with you, but then we'd both be wrong.",
    "Not all heroes wear capes. And clearly, not all villains do either.",
    "You have something on your chin... no, the third one down.",
]

_INSULTS = [
    "You're as sharp as a marble.",
    "You'd lose a debate with a parking meter.",
    "You're the human equivalent of a pop-up ad.",
    "Even autocorrect gave up trying to fix you.",
    "You're proof that even DNA can have a typo.",
    "Your birth certificate is an apology letter from the hospital.",
    "You bring nothing to the table — and yet somehow you're still annoying.",
    "If brains were petrol, you couldn't fuel a matchbox car.",
]

_MOTIVATIONS = [
    "Every expert was once a beginner. Keep going.",
    "The only way out is through. You've got this.",
    "Small steps every day add up to massive results.",
    "Don't stop when you're tired. Stop when you're done.",
    "You are braver than you believe, stronger than you seem.",
    "Your future self is cheering you on right now.",
    "Do something today that your future self will thank you for.",
    "Progress, not perfection. That's all that matters.",
    "One day or day one — you decide.",
    "The comeback is always greater than the setback.",
]

_SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐", "7️⃣", "🔔"]

_TIMEZONES = {
    "ist": ("Asia/Kolkata", "India Standard Time"),
    "india": ("Asia/Kolkata", "India Standard Time"),
    "gmt": ("GMT", "Greenwich Mean Time"),
    "utc": ("UTC", "Coordinated Universal Time"),
    "est": ("America/New_York", "Eastern Standard Time"),
    "cst": ("America/Chicago", "Central Standard Time"),
    "mst": ("America/Denver", "Mountain Standard Time"),
    "pst": ("America/Los_Angeles", "Pacific Standard Time"),
    "bst": ("Europe/London", "British Summer Time"),
    "cet": ("Europe/Paris", "Central European Time"),
    "jst": ("Asia/Tokyo", "Japan Standard Time"),
    "cst_china": ("Asia/Shanghai", "China Standard Time"),
    "aest": ("Australia/Sydney", "Australian Eastern Time"),
    "gst": ("Asia/Dubai", "Gulf Standard Time"),
    "pkt": ("Asia/Karachi", "Pakistan Standard Time"),
    "bdt": ("Asia/Dhaka", "Bangladesh Standard Time"),
    "sgt": ("Asia/Singapore", "Singapore Time"),
    "cat": ("Africa/Lagos", "West Africa Time"),
    "eat": ("Africa/Nairobi", "East Africa Time"),
    "sast": ("Africa/Johannesburg", "South Africa Standard Time"),
    "msk": ("Europe/Moscow", "Moscow Standard Time"),
    "idt": ("Asia/Jerusalem", "Israel Daylight Time"),
    "aedt": ("Australia/Melbourne", "Australian Eastern Daylight Time"),
}

# ── ─────────────────────────────────────────────────────── Text tools ─────────

def _require_text(context, example: str) -> str | None:
    return " ".join(context.args) if context.args else None


async def reverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /reverse [text]\nExample: /reverse hello world")
        return
    await update.message.reply_text(f"🔄 <code>{text[:500][::-1]}</code>", parse_mode="HTML")


async def mock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /mock [text]\nExample: /mock hello world")
        return
    result = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text[:300]))
    await update.message.reply_text(f"🧽 <code>{result}</code>", parse_mode="HTML")


async def aesthetic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /aesthetic [text]")
        return
    out = []
    for ch in text[:200]:
        if 'A' <= ch <= 'Z':
            out.append(chr(ord(ch) + 0xFF21 - 0x41))
        elif 'a' <= ch <= 'z':
            out.append(chr(ord(ch) + 0xFF41 - 0x61))
        elif '0' <= ch <= '9':
            out.append(chr(ord(ch) + 0xFF10 - 0x30))
        elif ch == ' ':
            out.append('  ')
        else:
            out.append(ch)
    await update.message.reply_text("".join(out))


async def bold2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /bold [text]\nExample: /bold hello world")
        return
    await update.message.reply_text(text[:300].translate(_BOLD_MAP))


async def italic2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /italic [text]")
        return
    await update.message.reply_text(text[:300].translate(_ITALIC_MAP))


async def binary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hi")
    if not text:
        await update.message.reply_text("Usage: /binary [text]\nExample: /binary Hi")
        return
    result = " ".join(format(ord(c), "08b") for c in text[:50])
    await update.message.reply_text(f"💻 <code>{result}</code>", parse_mode="HTML")


async def morse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "sos")
    if not text:
        await update.message.reply_text("Usage: /morse [text]\nExample: /morse SOS")
        return
    result = " ".join(_MORSE.get(c.upper(), "?") for c in text[:100])
    await update.message.reply_text(f"📡 <code>{result}</code>", parse_mode="HTML")


async def base64e(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /base64e [text]  (encode)")
        return
    encoded = base64.b64encode(text[:500].encode()).decode()
    await update.message.reply_text(f"🔐 <code>{encoded}</code>", parse_mode="HTML")


async def base64d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "aGVsbG8=")
    if not text:
        await update.message.reply_text("Usage: /base64d [encoded text]  (decode)")
        return
    try:
        decoded = base64.b64decode(text.strip()).decode("utf-8", errors="replace")
        await update.message.reply_text(f"🔓 <code>{decoded[:500]}</code>", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("Invalid Base64 string.")


async def sha256(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /sha256 [text]")
        return
    h = hashlib.sha256(text.encode()).hexdigest()
    await update.message.reply_text(f"🔏 SHA-256:\n<code>{h}</code>", parse_mode="HTML")


async def md5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /md5 [text]")
        return
    h = hashlib.md5(text.encode()).hexdigest()
    await update.message.reply_text(f"🔏 MD5:\n<code>{h}</code>", parse_mode="HTML")


async def uuid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = str(uuid_lib.uuid4())
    await update.message.reply_text(f"🆔 UUID:\n<code>{u}</code>", parse_mode="HTML")


async def wordcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello world")
    if not text and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""
    if not text:
        await update.message.reply_text("Usage: /wordcount [text]  or reply to a message")
        return
    words = len(text.split())
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    await update.message.reply_text(
        f"📊 <b>Word Count</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Words: <b>{words}</b>\n"
        f"Characters: <b>{chars}</b>\n"
        f"Characters (no spaces): <b>{chars_no_space}</b>\n"
        f"Sentences (approx): <b>{sentences}</b>",
        parse_mode="HTML"
    )


async def clap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello world")
    if not text:
        await update.message.reply_text("Usage: /clap [text]\nExample: /clap hello world")
        return
    result = "👏" + "👏".join(text[:200].split()) + "👏"
    await update.message.reply_text(result)


async def encode_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello world")
    if not text:
        await update.message.reply_text("Usage: /urlencode [text]")
        return
    await update.message.reply_text(f"🔗 <code>{quote_plus(text[:500])}</code>", parse_mode="HTML")


async def decode_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello+world")
    if not text:
        await update.message.reply_text("Usage: /urldecode [text]")
        return
    await update.message.reply_text(f"🔗 <code>{unquote(text[:500])}</code>", parse_mode="HTML")


async def spoilertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "secret")
    if not text:
        await update.message.reply_text("Usage: /spoiler [text]")
        return
    await update.message.reply_text(f"<tg-spoiler>{text[:500]}</tg-spoiler>", parse_mode="HTML")


# ── Fun commands ────────────────────────────────────────────────────────────

async def chuck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://api.chucknorris.io/jokes/random")
        if r.status_code == 200:
            joke = r.json().get("value", "")
            await update.message.reply_text(f"💪 <b>Chuck Norris Fact</b>\n\n{joke}", parse_mode="HTML")
            return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch a Chuck Norris fact. Try again!")


async def dadjoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
        if r.status_code == 200:
            joke = r.json().get("joke", "")
            await update.message.reply_text(f"👨 <b>Dad Joke</b>\n\n<i>{joke}</i>", parse_mode="HTML")
            return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch a dad joke. Try again!")


async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
    elif context.args:
        name = " ".join(context.args).lstrip("@")
        try:
            m = await context.bot.get_chat_member(update.effective_chat.id, name)
            target = m.user
        except Exception:
            pass

    c_text = random.choice(_COMPLIMENTS)
    if target and target.id != user.id:
        await update.message.reply_text(
            f"💐 <a href='tg://user?id={target.id}'>{target.first_name}</a>, {c_text}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"💐 {c_text}")


async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user

    r_text = random.choice(_ROASTS)
    if target and target.id != user.id:
        await update.message.reply_text(
            f"🔥 <a href='tg://user?id={target.id}'>{target.first_name}</a>, {r_text}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"🔥 {r_text}")


async def insult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"😈 {random.choice(_INSULTS)}")


async def motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🌟 {random.choice(_MOTIVATIONS)}")


async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s1, s2, s3 = [random.choice(_SLOT_SYMBOLS) for _ in range(3)]
    if s1 == s2 == s3:
        result = "🎉 <b>JACKPOT! You win!</b> 🎰"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        result = "✨ <b>Two of a kind — so close!</b>"
    else:
        result = "😢 No match this time. Try again!"
    await update.message.reply_text(
        f"🎰 <b>Slot Machine</b>\n\n[ {s1} | {s2} | {s3} ]\n\n{result}",
        parse_mode="HTML"
    )


async def waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://nekos.best/api/v2/waifu")
        if r.status_code == 200:
            data = r.json()
            url = data["results"][0]["url"]
            name = data["results"][0].get("anime_name", "")
            caption = f"🌸 <b>Random Waifu</b>" + (f"\n<i>{name}</i>" if name else "")
            await update.message.reply_photo(photo=url, caption=caption, parse_mode="HTML")
            return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch a waifu image. Try again!")


async def animepic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = ["neko", "kitsune", "husbando", "shinobu"]
    cat = random.choice(categories)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://nekos.best/api/v2/{cat}")
        if r.status_code == 200:
            data = r.json()
            url = data["results"][0]["url"]
            anime = data["results"][0].get("anime_name", "")
            caption = f"🎭 <b>Random Anime</b>" + (f"\n<i>{anime}</i>" if anime else "")
            await update.message.reply_photo(photo=url, caption=caption, parse_mode="HTML")
            return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch an anime image. Try again!")


# ── Info & lookup ─────────────────────────────────────────────────────────────

async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /crypto [symbol]\nExamples: /crypto BTC   /crypto ETH   /crypto SOL")
        return
    sym = context.args[0].upper()
    ids_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
        "DOGE": "dogecoin", "DOT": "polkadot", "AVAX": "avalanche-2",
        "MATIC": "matic-network", "SHIB": "shiba-inu", "LTC": "litecoin",
        "TRX": "tron", "LINK": "chainlink", "UNI": "uniswap",
    }
    coin_id = ids_map.get(sym, sym.lower())
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd,inr", "include_24hr_change": "true"}
            )
        if r.status_code == 200:
            data = r.json()
            if coin_id in data:
                info = data[coin_id]
                usd = info.get("usd", "N/A")
                inr = info.get("inr", "N/A")
                change = info.get("usd_24h_change", 0)
                arrow = "🟢 ▲" if change >= 0 else "🔴 ▼"
                await update.message.reply_text(
                    f"₿ <b>{sym}</b> Price\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"USD: <b>${usd:,.2f}</b>\n"
                    f"INR: <b>₹{inr:,.0f}</b>\n"
                    f"24h: {arrow} <b>{change:.2f}%</b>",
                    parse_mode="HTML"
                )
                return
        await update.message.reply_text(f"Could not find price for <b>{sym}</b>.", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("Crypto service unavailable. Try again later.")


async def ip_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ip [IP address]\nExample: /ip 8.8.8.8")
        return
    ip = context.args[0].strip()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://ipapi.co/{ip}/json/")
        if r.status_code == 200:
            d = r.json()
            if d.get("error"):
                await update.message.reply_text(f"Invalid IP address: {ip}")
                return
            await update.message.reply_text(
                f"🌐 <b>IP Lookup: {ip}</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Country: <b>{d.get('country_name', 'N/A')}</b> {d.get('country_code', '')}\n"
                f"Region: <b>{d.get('region', 'N/A')}</b>\n"
                f"City: <b>{d.get('city', 'N/A')}</b>\n"
                f"ISP: <b>{d.get('org', 'N/A')}</b>\n"
                f"Timezone: <b>{d.get('timezone', 'N/A')}</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("Could not look up that IP.")
    except Exception:
        await update.message.reply_text("IP lookup service unavailable.")


async def urban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /urban [word]\nExample: /urban slay")
        return
    word = " ".join(context.args)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://api.urbandictionary.com/v0/define?term={quote(word)}")
        if r.status_code == 200:
            entries = r.json().get("list", [])
            if not entries:
                await update.message.reply_text(f"No Urban Dictionary entry for <b>{word}</b>.", parse_mode="HTML")
                return
            top = entries[0]
            definition = top.get("definition", "")[:600].replace("[", "").replace("]", "")
            example = top.get("example", "")[:300].replace("[", "").replace("]", "")
            thumbs_up = top.get("thumbs_up", 0)
            await update.message.reply_text(
                f"📖 <b>{word}</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"{definition}\n\n"
                + (f"<i>e.g. {example}</i>\n\n" if example else "")
                + f"👍 {thumbs_up}",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("Could not fetch definition.")
    except Exception:
        await update.message.reply_text("Urban Dictionary unavailable. Try again later.")


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /translate [lang] [text]\n"
            "Examples:\n"
            "  /translate hi Hello how are you\n"
            "  /translate es Good morning\n"
            "  /translate ar I love cricket\n\n"
            "Common codes: hi=Hindi, es=Spanish, fr=French, ar=Arabic,\n"
            "de=German, ja=Japanese, ko=Korean, pt=Portuguese, ru=Russian"
        )
        return
    lang = context.args[0].lower()
    text = " ".join(context.args[1:])
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text[:500], "langpair": f"en|{lang}"}
            )
        if r.status_code == 200:
            data = r.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and translated.lower() != text.lower():
                await update.message.reply_text(
                    f"🌍 <b>Translation → {lang.upper()}</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Original: <i>{text[:300]}</i>\n"
                    f"Translated: <b>{translated[:600]}</b>",
                    parse_mode="HTML"
                )
                return
        await update.message.reply_text("Translation failed. Check the language code and try again.")
    except Exception:
        await update.message.reply_text("Translation service unavailable.")


async def lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /lyrics [artist] - [song]\n"
            "Example: /lyrics Ed Sheeran - Shape of You"
        )
        return
    q = " ".join(context.args)
    if " - " in q:
        artist, title = q.split(" - ", 1)
    else:
        await update.message.reply_text("Format: /lyrics [artist] - [song title]")
        return
    try:
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(f"https://lyrics.ovh/v1/{quote(artist.strip())}/{quote(title.strip())}")
        if r.status_code == 200:
            lyr = r.json().get("lyrics", "")
            if lyr:
                lyr = lyr[:3000]
                await update.message.reply_text(
                    f"🎵 <b>{artist.strip()} — {title.strip()}</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"<pre>{lyr}</pre>",
                    parse_mode="HTML"
                )
                return
        await update.message.reply_text(f"Lyrics not found for <b>{title.strip()}</b> by {artist.strip()}.", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("Lyrics service unavailable. Try again later.")


async def shorturl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /shorturl [URL]\nExample: /shorturl https://example.com/very/long/url")
        return
    url = context.args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://is.gd/create.php?format=simple&url={quote(url)}")
        if r.status_code == 200 and r.text.startswith("http"):
            await update.message.reply_text(
                f"🔗 <b>Shortened URL</b>\n\n"
                f"Original: <code>{url[:100]}</code>\n"
                f"Short: <b>{r.text.strip()}</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("Could not shorten URL. Make sure it's a valid URL.")
    except Exception:
        await update.message.reply_text("URL shortener unavailable. Try again later.")


# ── Unit converters ───────────────────────────────────────────────────────────

async def temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /temp [value] [from] [to]\n"
            "Units: C  F  K\n"
            "Example: /temp 100 C F")
        return
    try:
        val = float(context.args[0])
        frm = context.args[1].upper()
        to  = context.args[2].upper()
        if frm == "C":
            kelvin = val + 273.15
        elif frm == "F":
            kelvin = (val - 32) * 5/9 + 273.15
        elif frm == "K":
            kelvin = val
        else:
            raise ValueError("Unknown unit")
        if to == "C":
            result = kelvin - 273.15
        elif to == "F":
            result = (kelvin - 273.15) * 9/5 + 32
        elif to == "K":
            result = kelvin
        else:
            raise ValueError("Unknown unit")
        await update.message.reply_text(
            f"🌡 <b>{val} °{frm} = {result:.2f} °{to}</b>", parse_mode="HTML")
    except ValueError as e:
        if "Unknown unit" in str(e):
            await update.message.reply_text("Valid units: C, F, K")
        else:
            await update.message.reply_text("Please enter a valid number.")


async def length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    UNITS = {
        "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001,
        "mile": 1609.344, "miles": 1609.344, "ft": 0.3048, "feet": 0.3048,
        "in": 0.0254, "inch": 0.0254, "yd": 0.9144, "yard": 0.9144,
        "nm": 1852.0, "ly": 9.461e15,
    }
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /length [value] [from] [to]\n"
            "Units: m km cm mm mile ft in yd\n"
            "Example: /length 5 km miles")
        return
    try:
        val = float(context.args[0])
        frm = context.args[1].lower()
        to  = context.args[2].lower()
        if frm not in UNITS or to not in UNITS:
            await update.message.reply_text(f"Unknown unit. Valid: {', '.join(UNITS)}")
            return
        result = val * UNITS[frm] / UNITS[to]
        await update.message.reply_text(
            f"📏 <b>{val} {frm} = {result:.4g} {to}</b>", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")


async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    UNITS = {
        "kg": 1.0, "g": 0.001, "mg": 1e-6, "lb": 0.453592, "lbs": 0.453592,
        "oz": 0.0283495, "ton": 1000.0, "tonne": 1000.0, "st": 6.35029,
    }
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /weight [value] [from] [to]\n"
            "Units: kg g mg lb oz ton st\n"
            "Example: /weight 10 kg lb")
        return
    try:
        val = float(context.args[0])
        frm = context.args[1].lower()
        to  = context.args[2].lower()
        if frm not in UNITS or to not in UNITS:
            await update.message.reply_text(f"Unknown unit. Valid: {', '.join(UNITS)}")
            return
        result = val * UNITS[frm] / UNITS[to]
        await update.message.reply_text(
            f"⚖️ <b>{val} {frm} = {result:.4g} {to}</b>", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")


async def speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    UNITS = {
        "ms": 1.0, "m/s": 1.0, "kph": 1/3.6, "kmh": 1/3.6, "km/h": 1/3.6,
        "mph": 0.44704, "knots": 0.514444, "knot": 0.514444, "fps": 0.3048,
        "mach": 340.29,
    }
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /speed [value] [from] [to]\n"
            "Units: ms kph mph knots mach fps\n"
            "Example: /speed 100 kph mph")
        return
    try:
        val = float(context.args[0])
        frm = context.args[1].lower()
        to  = context.args[2].lower()
        if frm not in UNITS or to not in UNITS:
            await update.message.reply_text(f"Unknown unit. Valid: {', '.join(UNITS)}")
            return
        result = val * UNITS[frm] / UNITS[to]
        await update.message.reply_text(
            f"🚀 <b>{val} {frm} = {result:.4g} {to}</b>", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")


async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /currency [amount] [from] [to]\n"
            "Example: /currency 100 USD INR\n"
            "Example: /currency 50 EUR GBP")
        return
    try:
        amt = float(context.args[0])
        frm = context.args[1].upper()
        to  = context.args[2].upper()
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://open.er-api.com/v6/latest/{frm}")
        if r.status_code == 200:
            data = r.json()
            if data.get("result") == "success":
                rates = data.get("rates", {})
                if to not in rates:
                    await update.message.reply_text(f"Unknown currency: {to}")
                    return
                result = amt * rates[to]
                await update.message.reply_text(
                    f"💱 <b>{amt:,.2f} {frm} = {result:,.2f} {to}</b>\n"
                    f"<i>Rate: 1 {frm} = {rates[to]:.4f} {to}</i>",
                    parse_mode="HTML"
                )
                return
        await update.message.reply_text("Currency conversion failed. Check your currency codes.")
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
    except Exception:
        await update.message.reply_text("Currency service unavailable. Try again later.")


# ── AI Image generation ────────────────────────────────────────────────────────

async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /image [prompt]\n"
            "Example: /image a sunset over Mumbai with cricket players"
        )
        return
    prompt = " ".join(context.args)
    if len(prompt) > 500:
        await update.message.reply_text("Prompt too long! Max 500 characters.")
        return

    msg = await update.message.reply_text("🎨 Generating image… this may take up to 30 seconds…")
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=768&height=768&nologo=true&model=flux"

    try:
        async with httpx.AsyncClient(timeout=60) as c:
            resp = await c.get(url)
        if resp.status_code == 200 and len(resp.content) > 1000:
            img = BytesIO(resp.content)
            img.name = "image.jpg"
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img,
                caption=f"🎨 <b>AI Generated Image</b>\n<i>{prompt[:200]}</i>",
                parse_mode="HTML",
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Image generation failed. Try a different prompt!")
    except Exception:
        await msg.edit_text("❌ Image service timed out. Try again with a simpler prompt.")


async def link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /link [prompt]\n"
            "Returns a direct image URL you can use anywhere.\n"
            "Example: /link a beautiful anime girl with blue hair"
        )
        return
    prompt = " ".join(context.args)
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=512&height=512&nologo=true&model=flux"
    await update.message.reply_text(
        f"🔗 <b>AI Image URL</b>\n"
        f"<i>Prompt: {prompt[:200]}</i>\n\n"
        f"<code>{url}</code>\n\n"
        f"<i>This link generates a new image each time it's opened.</i>",
        parse_mode="HTML"
    )


# ── Other tools ────────────────────────────────────────────────────────────────

async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /time [timezone]\n"
            "Examples: /time IST   /time UTC   /time PST   /time JST\n"
            "Available: IST, UTC, GMT, EST, CST, MST, PST, BST, CET, JST, AEST, GST, PKT, BDT, SGT, MSK"
        )
        return
    tz_key = context.args[0].lower()
    tz_info = _TIMEZONES.get(tz_key)
    if not tz_info:
        await update.message.reply_text(f"Unknown timezone: {context.args[0]}\nTry: IST, UTC, EST, PST, JST etc.")
        return
    try:
        import pytz
        tz = pytz.timezone(tz_info[0])
        now = datetime.now(tz)
        await update.message.reply_text(
            f"🕐 <b>Current Time — {tz_info[1]}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"<b>{now.strftime('%I:%M %p')}</b>\n"
            f"{now.strftime('%A, %d %B %Y')}",
            parse_mode="HTML"
        )
    except Exception:
        now = datetime.utcnow()
        await update.message.reply_text(
            f"🕐 <b>UTC Time</b>\n<b>{now.strftime('%I:%M %p')}</b>\n{now.strftime('%A, %d %B %Y')}",
            parse_mode="HTML"
        )


async def color_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /color [hex code]\nExample: /color FF5733")
        return
    hex_code = context.args[0].lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", hex_code):
        await update.message.reply_text("Invalid hex color! Use 6 hex digits.\nExample: /color FF5733")
        return
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    # Brightness
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    tone = "Light" if brightness > 128 else "Dark"
    # Generate a color preview image via colornames.org or just send info
    try:
        img_url = f"https://singlecolorimage.com/get/{hex_code}/200x200"
        async with httpx.AsyncClient(timeout=8) as c:
            resp = await c.get(img_url)
        if resp.status_code == 200 and len(resp.content) > 100:
            img = BytesIO(resp.content)
            img.name = "color.png"
            await update.message.reply_photo(
                photo=img,
                caption=(
                    f"🎨 <b>Color #{hex_code}</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"RGB: <b>({r}, {g}, {b})</b>\n"
                    f"HEX: <b>#{hex_code}</b>\n"
                    f"Tone: <b>{tone}</b>"
                ),
                parse_mode="HTML"
            )
            return
    except Exception:
        pass
    await update.message.reply_text(
        f"🎨 <b>Color #{hex_code}</b>\n"
        f"RGB: <b>({r}, {g}, {b})</b>\n"
        f"Tone: <b>{tone}</b>",
        parse_mode="HTML"
    )


async def toss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["Heads 🪙", "Tails 🦅"])
    await update.message.reply_text(f"🪙 <b>{result}!</b>", parse_mode="HTML")


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
    elif context.args:
        uname = context.args[0].lstrip("@")
        try:
            m = await context.bot.get_chat_member(update.effective_chat.id, uname)
            target = m.user
        except Exception:
            pass
    if not target:
        target = user

    traits = ["Funny", "Smart", "Kind", "Cool", "Creative", "Honest", "Loyal", "Chill"]
    selected = random.sample(traits, 3)
    score = random.randint(1, 10)
    bar = "⭐" * score + "☆" * (10 - score)
    await update.message.reply_text(
        f"📊 <b>Rating: {target.first_name}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Score: {bar} <b>{score}/10</b>\n"
        f"Traits: {', '.join(selected)}",
        parse_mode="HTML"
    )


async def percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /percent [value] [total]\n"
            "Example: /percent 45 200\n"
            "Or: /percent 20% of 500"
        )
        return
    try:
        val = float(context.args[0])
        total = float(context.args[1])
        if total == 0:
            await update.message.reply_text("Total cannot be zero!")
            return
        pct = (val / total) * 100
        await update.message.reply_text(
            f"📊 <b>{val}</b> out of <b>{total}</b> = <b>{pct:.2f}%</b>",
            parse_mode="HTML"
        )
    except ValueError:
        await update.message.reply_text("Please enter valid numbers.")


async def randomnum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lo, hi = 1, 100
    if context.args and len(context.args) >= 2:
        try:
            lo, hi = int(context.args[0]), int(context.args[1])
        except ValueError:
            pass
    elif context.args:
        try:
            hi = int(context.args[0])
        except ValueError:
            pass
    if lo > hi:
        lo, hi = hi, lo
    n = random.randint(lo, hi)
    await update.message.reply_text(
        f"🎲 Random number between <b>{lo}</b> and <b>{hi}</b>: <b>{n}</b>",
        parse_mode="HTML"
    )


async def anagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = _require_text(context, "hello")
    if not text:
        await update.message.reply_text("Usage: /anagram [word or phrase]")
        return
    lst = list(text.replace(" ", ""))
    random.shuffle(lst)
    await update.message.reply_text(
        f"🔀 Anagram of <b>{text[:100]}</b>:\n<code>{''.join(lst)}</code>",
        parse_mode="HTML"
    )


async def emojify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /emojify [text]\nAdds an emoji after each word")
        return
    emojis = ["😎", "🔥", "💫", "⭐", "🎯", "🚀", "💥", "✨", "🌟", "🎉", "🏆", "💪"]
    words = " ".join(context.args).split()
    result = " ".join(f"{w}{random.choice(emojis)}" for w in words[:30])
    await update.message.reply_text(result)


async def typetext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /type [text]\nMakes text look like it was typed slowly")
        return
    text = " ".join(context.args)[:100]
    result = " ".join(f"`{c}`" if c != " " else " " for c in text)
    await update.message.reply_text(result[:2000])


async def piglatin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /piglatin [text]\nExample: /piglatin hello world")
        return
    def to_pig(word):
        vowels = "aeiouAEIOU"
        if not word.isalpha():
            return word
        if word[0] in vowels:
            return word + "way"
        for i, c in enumerate(word):
            if c in vowels:
                return word[i:] + word[:i] + "ay"
        return word + "ay"
    words = " ".join(context.args).split()
    result = " ".join(to_pig(w) for w in words[:50])
    await update.message.reply_text(f"🐷 <code>{result}</code>", parse_mode="HTML")
