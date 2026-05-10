"""50 anime commands — reactions, info, fun, social, games.
All in /help → 🎌 Anime. NOT added to ALL_COMMANDS (already at 100 limit)."""

import asyncio
import random
import logging
from io import BytesIO
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

JIKAN     = "https://api.jikan.moe/v4"
NEKOS     = "https://nekos.best/api/v2"
WAIFU_IM  = "https://api.waifu.im/search"

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get(url: str, params: dict = None) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as c:
            r = await c.get(url, params=params)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.warning(f"anime _get {url}: {e}")
    return None


async def _send_gif(update: Update, context, endpoint: str,
                    caption: str) -> None:
    """Fetch a GIF from nekos.best and send it."""
    data = await _get(f"{NEKOS}/{endpoint}")
    gif_url = None
    if data and data.get("results"):
        gif_url = data["results"][0].get("url")

    if not gif_url:
        await update.message.reply_text(caption, parse_mode="HTML")
        return

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
            r = await c.get(gif_url)
            if r.status_code == 200:
                f = BytesIO(r.content)
                f.name = "anime.gif"
                await update.message.reply_animation(
                    animation=f, caption=caption, parse_mode="HTML")
                return
    except Exception as e:
        logger.warning(f"GIF send failed: {e}")

    await update.message.reply_text(caption, parse_mode="HTML")


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def _target_mention(update) -> str | None:
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        u = update.message.reply_to_message.from_user
        return f'<a href="tg://user?id={u.id}">{u.first_name}</a>'
    return None


# ══════════════════════════════════════════════════════════════════════════════
# ── 1. ANIME / MANGA INFO COMMANDS ───────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

async def anime_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/anime [title] — search anime info."""
    if not context.args:
        await update.message.reply_text(
            "🎌 Usage: <code>/anime Naruto</code>", parse_mode="HTML")
        return
    q = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Searching for <b>{q}</b>…", parse_mode="HTML")
    data = await _get(f"{JIKAN}/anime", {"q": q, "limit": 1, "sfw": True})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Anime not found. Try another title.")
        return
    a = data["data"][0]
    score   = a.get("score") or "N/A"
    eps     = a.get("episodes") or "?"
    status  = a.get("status", "Unknown")
    genres  = ", ".join(g["name"] for g in a.get("genres", [])[:4]) or "N/A"
    year    = a.get("year") or (a.get("aired", {}) or {}).get("prop", {}).get("from", {}).get("year", "?")
    rating  = a.get("rating", "N/A")
    synopsis= (a.get("synopsis") or "No synopsis available.")[:300]
    url     = a.get("url", "")
    img     = (a.get("images", {}).get("jpg", {}) or {}).get("image_url", "")
    title   = a.get("title_english") or a.get("title", q)

    text = (
        f"🎌 <b>{title}</b>  (<i>{a.get('title_japanese', '')}</i>)\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ Score: <b>{score}/10</b>  |  📺 Episodes: <b>{eps}</b>\n"
        f"📅 Year: <b>{year}</b>  |  Status: <b>{status}</b>\n"
        f"🎭 Genres: {genres}\n"
        f"🔞 Rating: {rating}\n\n"
        f"📖 <i>{synopsis}…</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 MAL Page", url=url)]]) if url else None
    try:
        await msg.delete()
        if img:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(img)
                if r.status_code == 200:
                    f = BytesIO(r.content); f.name = "anime.jpg"
                    await update.message.reply_photo(photo=f, caption=text,
                                                     parse_mode="HTML", reply_markup=kb)
                    return
    except Exception:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb,
                                     disable_web_page_preview=True)


async def manga_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/manga [title] — search manga info."""
    if not context.args:
        await update.message.reply_text("📚 Usage: <code>/manga One Piece</code>", parse_mode="HTML")
        return
    q = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Searching manga <b>{q}</b>…", parse_mode="HTML")
    data = await _get(f"{JIKAN}/manga", {"q": q, "limit": 1, "sfw": True})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Manga not found. Try another title.")
        return
    a = data["data"][0]
    score   = a.get("score") or "N/A"
    chs     = a.get("chapters") or "?"
    status  = a.get("status", "Unknown")
    genres  = ", ".join(g["name"] for g in a.get("genres", [])[:4]) or "N/A"
    synopsis= (a.get("synopsis") or "No synopsis available.")[:300]
    url     = a.get("url", "")
    img     = (a.get("images", {}).get("jpg", {}) or {}).get("image_url", "")
    title   = a.get("title_english") or a.get("title", q)

    text = (
        f"📚 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ Score: <b>{score}/10</b>  |  📖 Chapters: <b>{chs}</b>\n"
        f"Status: <b>{status}</b>  |  Genres: {genres}\n\n"
        f"📖 <i>{synopsis}…</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 MAL Page", url=url)]]) if url else None
    try:
        await msg.delete()
        if img:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(img)
                if r.status_code == 200:
                    f = BytesIO(r.content); f.name = "manga.jpg"
                    await update.message.reply_photo(photo=f, caption=text,
                                                     parse_mode="HTML", reply_markup=kb)
                    return
    except Exception:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb,
                                     disable_web_page_preview=True)


async def achar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/achar [name] — anime character search."""
    if not context.args:
        await update.message.reply_text("🎭 Usage: <code>/achar Naruto</code>", parse_mode="HTML")
        return
    q = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Searching character <b>{q}</b>…", parse_mode="HTML")
    data = await _get(f"{JIKAN}/characters", {"q": q, "limit": 1})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Character not found.")
        return
    c = data["data"][0]
    name    = c.get("name", q)
    name_jp = c.get("name_kanji", "")
    favs    = c.get("favorites", 0)
    desc    = (c.get("about") or "No info available.")[:350]
    img     = (c.get("images", {}).get("jpg", {}) or {}).get("image_url", "")
    url     = c.get("url", "")
    animes  = [a.get("anime", {}).get("title", "") for a in c.get("anime", [])[:3] if a.get("anime")]
    anime_line = " • ".join(filter(None, animes)) or "Unknown"

    text = (
        f"🎭 <b>{name}</b>  <i>{name_jp}</i>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📺 Appears in: {anime_line}\n"
        f"❤️ Favorites: <b>{favs:,}</b>\n\n"
        f"📖 <i>{desc}…</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 MAL Page", url=url)]]) if url else None
    try:
        await msg.delete()
        if img:
            async with httpx.AsyncClient(timeout=10) as c2:
                r = await c2.get(img)
                if r.status_code == 200:
                    f = BytesIO(r.content); f.name = "char.jpg"
                    await update.message.reply_photo(photo=f, caption=text,
                                                     parse_mode="HTML", reply_markup=kb)
                    return
    except Exception:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb,
                                     disable_web_page_preview=True)


async def topanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/topanime — top 10 anime by score."""
    msg = await update.message.reply_text("📊 Fetching top anime…")
    data = await _get(f"{JIKAN}/top/anime", {"limit": 10, "filter": "bypopularity"})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch top anime right now.")
        return
    lines = ["🏆 <b>Top 10 Anime (by popularity)</b>\n━━━━━━━━━━━━━━━━"]
    for i, a in enumerate(data["data"][:10], 1):
        title = a.get("title_english") or a.get("title", "?")
        score = a.get("score") or "N/A"
        lines.append(f"{i}. <b>{title}</b> — ⭐ {score}")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def seasonal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/seasonal — current season anime."""
    msg = await update.message.reply_text("🌸 Fetching seasonal anime…")
    data = await _get(f"{JIKAN}/seasons/now", {"limit": 10})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch seasonal anime right now.")
        return
    lines = ["🌸 <b>This Season's Anime</b>\n━━━━━━━━━━━━━━━━"]
    for a in data["data"][:10]:
        title = a.get("title_english") or a.get("title", "?")
        score = a.get("score") or "?"
        eps   = a.get("episodes") or "?"
        lines.append(f"▸ <b>{title}</b>  ⭐{score}  📺{eps}ep")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def randomanim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/randomanim — random anime recommendation."""
    msg = await update.message.reply_text("🎲 Getting a random anime for you…")
    data = await _get(f"{JIKAN}/random/anime")
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch a random anime right now.")
        return
    a = data["data"]
    title   = a.get("title_english") or a.get("title", "?")
    score   = a.get("score") or "N/A"
    eps     = a.get("episodes") or "?"
    genres  = ", ".join(g["name"] for g in a.get("genres", [])[:4]) or "N/A"
    synopsis= (a.get("synopsis") or "No synopsis.")[:250]
    img     = (a.get("images", {}).get("jpg", {}) or {}).get("image_url", "")
    url     = a.get("url", "")
    text = (
        f"🎲 <b>Random Pick:</b> <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ Score: {score}  |  📺 Episodes: {eps}\n"
        f"🎭 Genres: {genres}\n\n"
        f"📖 <i>{synopsis}…</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 More Info", url=url)]]) if url else None
    try:
        await msg.delete()
        if img:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(img)
                if r.status_code == 200:
                    f = BytesIO(r.content); f.name = "anime.jpg"
                    await update.message.reply_photo(photo=f, caption=text,
                                                     parse_mode="HTML", reply_markup=kb)
                    return
    except Exception:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb,
                                     disable_web_page_preview=True)


async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/upcoming — upcoming anime."""
    msg = await update.message.reply_text("📅 Fetching upcoming anime…")
    data = await _get(f"{JIKAN}/top/anime", {"limit": 10, "filter": "upcoming"})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch upcoming anime.")
        return
    lines = ["📅 <b>Upcoming Anime</b>\n━━━━━━━━━━━━━━━━"]
    for i, a in enumerate(data["data"][:10], 1):
        title = a.get("title_english") or a.get("title", "?")
        year  = (a.get("aired", {}) or {}).get("prop", {}).get("from", {}).get("year", "?")
        lines.append(f"{i}. <b>{title}</b>  (📅 {year})")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def popular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/popular — most popular anime."""
    msg = await update.message.reply_text("🔥 Fetching popular anime…")
    data = await _get(f"{JIKAN}/top/anime", {"limit": 10, "filter": "airing"})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch popular anime.")
        return
    lines = ["🔥 <b>Popular Airing Anime</b>\n━━━━━━━━━━━━━━━━"]
    for i, a in enumerate(data["data"][:10], 1):
        title = a.get("title_english") or a.get("title", "?")
        score = a.get("score") or "?"
        lines.append(f"{i}. <b>{title}</b>  ⭐ {score}")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def airing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/airing — currently airing anime."""
    msg = await update.message.reply_text("📡 Fetching currently airing anime…")
    data = await _get(f"{JIKAN}/seasons/now", {"limit": 12})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch airing anime.")
        return
    lines = ["📡 <b>Currently Airing</b>\n━━━━━━━━━━━━━━━━"]
    for a in data["data"][:12]:
        title = a.get("title_english") or a.get("title", "?")
        score = a.get("score") or "?"
        lines.append(f"▸ <b>{title}</b>  ⭐{score}")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def animegenre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/animegenre [genre] — anime by genre."""
    _GENRES = {
        "action": 1, "adventure": 2, "comedy": 4, "drama": 8, "fantasy": 10,
        "horror": 14, "mystery": 7, "romance": 22, "scifi": 24, "sports": 30,
        "supernatural": 37, "thriller": 41, "slice of life": 36, "mecha": 18,
        "music": 19, "school": 23, "shounen": 27, "shoujo": 25, "seinen": 42,
        "isekai": 62, "psychological": 40,
    }
    if not context.args:
        genres_list = ", ".join(f"<code>{g}</code>" for g in _GENRES)
        await update.message.reply_text(
            f"🎭 Usage: <code>/animegenre action</code>\n\nAvailable: {genres_list}",
            parse_mode="HTML")
        return
    genre_name = " ".join(context.args).lower().strip()
    genre_id   = _GENRES.get(genre_name)
    if not genre_id:
        await update.message.reply_text(
            f"❌ Unknown genre. Try: action, romance, horror, fantasy, isekai, comedy, etc.")
        return
    msg  = await update.message.reply_text(f"🎭 Fetching {genre_name} anime…")
    data = await _get(f"{JIKAN}/anime", {"genres": genre_id, "limit": 8,
                                          "order_by": "score", "sort": "desc", "sfw": True})
    if not data or not data.get("data"):
        await msg.edit_text("❌ Could not fetch anime for that genre.")
        return
    lines = [f"🎭 <b>{genre_name.title()} Anime</b>\n━━━━━━━━━━━━━━━━"]
    for i, a in enumerate(data["data"][:8], 1):
        title = a.get("title_english") or a.get("title", "?")
        score = a.get("score") or "?"
        lines.append(f"{i}. <b>{title}</b>  ⭐{score}")
    await msg.edit_text("\n".join(lines), parse_mode="HTML")


async def animerec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/animerec — random anime recommendation from different genres."""
    _RECS = [
        ("Action/Shonen", ["Demon Slayer", "Jujutsu Kaisen", "My Hero Academia", "Hunter x Hunter", "Fullmetal Alchemist: Brotherhood"]),
        ("Romance", ["Your Lie in April", "Toradora", "Clannad", "Fruits Basket", "Kaguya-sama: Love Is War"]),
        ("Isekai", ["Re:Zero", "Sword Art Online", "That Time I Got Reincarnated as a Slime", "Overlord", "No Game No Life"]),
        ("Mystery/Thriller", ["Death Note", "Monster", "Ergo Proxy", "Promised Neverland", "91 Days"]),
        ("Sci-Fi/Mecha", ["Neon Genesis Evangelion", "Code Geass", "Gurren Lagann", "Steins;Gate", "Darling in the FranXX"]),
        ("Slice of Life", ["Anohana", "March Comes In Like a Lion", "Barakamon", "Non Non Biyori", "Yotsuba"]),
        ("Sports", ["Haikyuu!!", "Kuroko no Basket", "Slam Dunk", "Yuri on Ice", "Captain Tsubasa"]),
        ("Horror", ["Elfen Lied", "Parasyte", "Another", "Shiki", "Made in Abyss"]),
    ]
    genre, recs = random.choice(_RECS)
    pick = random.choice(recs)
    await update.message.reply_text(
        f"🎌 <b>Anime Recommendation!</b>\n\n"
        f"Genre: <b>{genre}</b>\n"
        f"Watch: <b>{pick}</b>\n\n"
        f"Other great picks in this genre:\n" +
        "\n".join(f"  • {r}" for r in recs if r != pick),
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════════════════════
# ── 2. ANIME QUOTES, FACTS, FUN ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

_ANIME_QUOTES = [
    ('"People\'s lives don\'t end when they die. It ends when they lose faith."', "Itachi Uchiha", "Naruto"),
    ('"Hard work is worthless for those that don\'t believe in themselves."', "Naruto Uzumaki", "Naruto"),
    ('"Power comes in response to a need, not a desire."', "Goku", "Dragon Ball Z"),
    ('"A dropout will beat a genius through hard work."', "Rock Lee", "Naruto"),
    ('"If you don\'t take risks, you can\'t create a future."', "Monkey D. Luffy", "One Piece"),
    ('"The world is not perfect, but it\'s there for us, doing the best it can."', "Roy Mustang", "FMA Brotherhood"),
    ('"Whatever you lose, you\'ll find it again. But what you throw away you\'ll never get back."', "Himura Kenshin", "Rurouni Kenshin"),
    ('"I am the hope of the universe."', "Goku", "Dragon Ball Z"),
    ('"Fear is not evil. It tells you what your weakness is."', "Gildarts Clive", "Fairy Tail"),
    ('"Even if I am the worst... I\'ll definitely become the King of Pirates!"', "Monkey D. Luffy", "One Piece"),
    ('"A person grows up when he\'s able to overcome hardships."', "Pain", "Naruto"),
    ('"The moment you give up is the moment you let someone else win."', "Koro-sensei", "Assassination Classroom"),
    ('"Being lonely is more painful than getting hurt."', "Monkey D. Luffy", "One Piece"),
    ('"No matter how hard or impossible it is, never lose sight of your goal."', "Monkey D. Luffy", "One Piece"),
    ('"I refuse to let my fear control me anymore."', "Maka Albarn", "Soul Eater"),
    ('"A lesson without pain is meaningless."', "Edward Elric", "Fullmetal Alchemist"),
    ('"Not giving up on yourself is what truly makes you a winner."', "Deku", "My Hero Academia"),
    ('"I want to be strong enough so that I\'m able to protect the things I care for."', "Ichigo Kurosaki", "Bleach"),
    ('"All living creatures want to stand at the top."', "Madara Uchiha", "Naruto"),
    ('"Knowing what it feels to be in pain, is exactly why we try to be kind to others."', "Jiraiya", "Naruto"),
]

_ANIME_FACTS = [
    "The word 'anime' is derived from the French word 'animé', meaning animated! 🎌",
    "Dragon Ball Z was so popular in France that it aired before Japan sometimes! 🇫🇷",
    "Hayao Miyazaki hand-drew many of the frames in his movies frame by frame! ✍️",
    "One Piece has been running since 1997 and has over 1000+ manga chapters! 📚",
    "The original Pokémon anime was meant to have 250 episodes and then end. Now it has 1000+! 🎮",
    "Naruto's creator, Masashi Kishimoto, drew 70+ pages of manga per week! ✏️",
    "Attack on Titan's author Hajime Isayama started drawing it when he was 20 years old! 🏗️",
    "The voice of Pikachu, Ikue Ōtani, has voiced the character since 1997! 🎙️",
    "Death Note was originally rejected by Jump editors before being published! 📝",
    "Dragon Ball's Goku was inspired by the Chinese legend of the Monkey King (Sun Wukong)! 🐒",
    "Spirited Away won an Academy Award for Best Animated Feature in 2003! 🏆",
    "One Punch Man's author (ONE) drew the original webcomic in MS Paint! 🖱️",
    "The art style of anime was heavily influenced by Walt Disney cartoons in the 1950s! 🎨",
    "Jujutsu Kaisen sold more manga copies than One Piece in 2021! 📖",
    "The longest running anime is 'Sazae-san', airing since 1969 with 7500+ episodes! 📺",
    "Demon Slayer's movie 'Mugen Train' became Japan's highest-grossing film ever! 🎬",
    "The Studio Ghibli museum in Japan has a giant Totoro made of cats! 🐱",
    "My Hero Academia was originally going to be a live-action show, not anime! 🦸",
    "Sailor Moon introduced many Western viewers to anime in the 1990s! 🌙",
    "The anime industry earns over $25 billion globally every year! 💰",
]

_ANIME_POWERS = [
    ("Sharingan", "You possess the Sharingan! You can see chakra, copy techniques, and predict movements!", "🔴"),
    ("Haki", "You wield Conqueror's Haki! Your willpower alone can knock out weaker opponents!", "👑"),
    ("Devil Fruit", "You've eaten a Logia-type Devil Fruit! You can transform into a natural element!", "🍎"),
    ("Alchemy", "Full Metal Alchemist! You can transmute matter without a circle!", "⚗️"),
    ("Titan Power", "You hold the power of the Attack Titan! You can see future memories of your successors!", "⚔️"),
    ("Quirk", "Your Quirk is 'Overpower' — you can copy any ability you see used against you!", "💥"),
    ("Bankai", "You've unlocked Bankai! Your sword transforms into its ultimate form!", "⚡"),
    ("Cursed Energy", "You produce the rarest inverse cursed energy — healing everything you touch!", "💚"),
    ("Ki", "You've mastered Ultra Instinct! Your body moves before your mind even thinks!", "🌀"),
    ("Breathing Style", "You've mastered the Sun Breathing — the most powerful form among all Demon Slayers!", "☀️"),
    ("Magic", "Your Grimoire reveals you have Star Magic — one of the rarest in the Clover Kingdom!", "⭐"),
    ("Nen", "Your Nen type is Specialization — you can master abilities that don't fit any category!", "🌟"),
]

_ANIME_CLANS = [
    ("Uchiha Clan 🔴", "Naruto", "Elite warriors with Sharingan. Powerful but cursed with hatred."),
    ("Senju Clan 🌿", "Naruto", "Founders of the Hidden Leaf. Known for life force and Wood Release."),
    ("Elric Brothers 🧡", "Fullmetal Alchemist", "Alchemist prodigies on a quest for the Philosopher's Stone."),
    ("Straw Hat Pirates 🏴‍☠️", "One Piece", "A crew of dreamers sailing toward the Grand Line!"),
    ("Survey Corps ⚔️", "Attack on Titan", "Brave soldiers who fight Titans beyond the walls."),
    ("Hashira 🌊", "Demon Slayer", "The nine pillars of the Demon Slayer Corps. Elite fighters."),
    ("Class 1-A 💚", "My Hero Academia", "The most talented young hero students at UA High."),
    ("Konoha Shinobi 🍃", "Naruto", "Protectors of the Hidden Leaf Village. Strong and loyal."),
    ("Yorozuya ⚡", "Gintama", "Jack-of-all-trades trio doing odd jobs in Edo."),
    ("Fairy Tail Guild ✨", "Fairy Tail", "The most chaotic and powerful guild in Fiore Kingdom."),
]

_ANIME_AURA = [
    ("🔴 Crimson Aura — Power & Dominance", "Your aura radiates raw power. You're born to lead and dominate."),
    ("💙 Azure Aura — Wisdom & Calm", "You're the smart one. Strategy and intelligence define you."),
    ("💚 Emerald Aura — Life & Healing", "You have the power to heal and protect those you love."),
    ("🌟 Golden Aura — Rarity & Strength", "The rarest of all auras. You're destined for greatness."),
    ("🟣 Violet Aura — Mystery & Intelligence", "You keep secrets and know things others don't."),
    ("🌸 Sakura Aura — Heart & Emotion", "Your heart is your greatest weapon. Empathy is your power."),
    ("⚫ Void Aura — Chaos & Darkness", "You control the shadows. Chaos bends to your will."),
    ("🌊 Ocean Aura — Freedom & Adaptability", "Like water, you adapt to any situation effortlessly."),
    ("🔥 Flame Aura — Passion & Intensity", "Your passion burns bright. You never give up, ever."),
    ("❄️ Ice Aura — Precision & Control", "Cool under pressure. Your precision is unmatched."),
]

_ANIME_SENSEI = [
    ("Kakashi Hatake", "Naruto", "The Copy Ninja. Cool, laid-back, but absolutely deadly when needed."),
    ("Master Roshi", "Dragon Ball", "The Turtle Hermit. Ancient wisdom wrapped in...interesting packaging."),
    ("Jiraiya", "Naruto", "The Pervy Sage. Secretly one of the greatest shinobi of all time."),
    ("Koro-sensei", "Assassination Classroom", "The most caring teacher in the universe — and the most dangerous."),
    ("Gildarts Clive", "Fairy Tail", "The Ace of Fairy Tail. Absolute power with a gentle heart."),
    ("Roy Mustang", "FMA Brotherhood", "The Flame Alchemist. A leader who will burn down the heavens for his people."),
    ("Erwin Smith", "Attack on Titan", "Commander of the Survey Corps. He sacrifices everything for humanity."),
    ("All Might", "My Hero Academia", "The Symbol of Peace. His presence alone inspires courage in everyone."),
    ("Kisuke Urahara", "Bleach", "The mysterious shopkeeper who's actually a genius in disguise."),
    ("Gojo Satoru", "Jujutsu Kaisen", "The strongest sorcerer in history. Infinity itself is your shield."),
]

_ANIME_SHIPS = [
    ("Naruto ✕ Hinata", "Naruto — They were meant for each other from day one! NaruHina forever! 💞"),
    ("Goku ✕ Chi-Chi", "Dragon Ball — Despite everything, Chi-Chi stuck with Goku through it all! ❤️"),
    ("Edward ✕ Winry", "FMA Brotherhood — He'd cross the entire world for her. Iconic couple! ⚙️❤️"),
    ("Luffy ✕ Nami", "One Piece — The captain and navigator. An unbeatable combo! 🏴‍☠️"),
    ("Ichigo ✕ Orihime", "Bleach — He protects her. She heals him. Perfect balance! ⚡💛"),
    ("Deku ✕ Uraraka", "My Hero Academia — The pure-hearted hero duo. Your ship is sailing! 💚🩷"),
    ("Kirito ✕ Asuna", "Sword Art Online — They found each other in a game and fell in love in real life! ⚔️"),
    ("Spike ✕ Faye", "Cowboy Bebop — Two lost souls bouncing off each other through space! 🚀"),
    ("Holo ✕ Lawrence", "Spice and Wolf — The merchant and the wolf goddess. Timeless! 🐺"),
    ("Simon ✕ Nia", "Gurren Lagann — He drilled through the heavens for her! 💫"),
]

_ANIME_FIGHT_CHARS = [
    ("Goku", "Dragon Ball Z", "Ultra Instinct", 99, "🌀"),
    ("Saitama", "One Punch Man", "One Punch", 100, "👊"),
    ("Naruto", "Naruto", "Nine-Tails Chakra Mode", 95, "🍃"),
    ("Ichigo", "Bleach", "Getsuga Tenshō", 93, "⚡"),
    ("Meliodas", "Seven Deadly Sins", "Full Counter", 92, "🗡️"),
    ("Gojo Satoru", "Jujutsu Kaisen", "Infinity", 97, "💜"),
    ("Madara Uchiha", "Naruto", "Infinite Tsukuyomi", 96, "🔴"),
    ("All Might", "My Hero Academia", "United States of Smash", 91, "💪"),
    ("Alucard", "Hellsing", "Restriction Zero", 98, "🧛"),
    ("Erza Scarlet", "Fairy Tail", "Armadura Fairy", 88, "⚔️"),
    ("Edward Elric", "FMA Brotherhood", "Philosopher's Stone", 85, "⚗️"),
    ("Killua", "Hunter x Hunter", "Godspeed", 90, "⚡"),
    ("Levi Ackerman", "Attack on Titan", "Ackerman Instinct", 87, "🔱"),
    ("Rimuru Tempest", "TenSura", "Raphael Lord of Wisdom", 94, "🌊"),
    ("Reinhard", "Re:Zero", "Divine Protection of the Sun", 89, "☀️"),
]

async def animequote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, char, show = random.choice(_ANIME_QUOTES)
    await update.message.reply_text(
        f"💬 <b>Anime Quote</b>\n\n{q}\n\n— <b>{char}</b> (<i>{show}</i>)",
        parse_mode="HTML",
    )


async def animefact2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fact = random.choice(_ANIME_FACTS)
    await update.message.reply_text(
        f"🎌 <b>Anime Fact</b>\n\n{fact}", parse_mode="HTML")


async def animefight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c1, c2 = random.sample(_ANIME_FIGHT_CHARS, 2)
    name1, show1, skill1, power1, em1 = c1
    name2, show2, skill2, power2, em2 = c2
    # Weighted random winner
    total = power1 + power2
    winner = c1 if random.random() < (power1 / total) else c2
    w_name, w_show, w_skill, _, w_em = winner
    l_name = name2 if winner is c1 else name1
    margin = random.randint(1, 25)

    await update.message.reply_text(
        f"⚔️ <b>ANIME FIGHT!</b>\n\n"
        f"{em1} <b>{name1}</b> ({show1})\n"
        f"  Power: {power1}/100  |  Skill: {skill1}\n\n"
        f"  VS\n\n"
        f"{em2} <b>{name2}</b> ({show2})\n"
        f"  Power: {power2}/100  |  Skill: {skill2}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>{w_name}</b> wins by {margin} power points!\n"
        f"<i>'{w_skill}' overwhelmed {l_name}!</i>",
        parse_mode="HTML",
    )


async def animeship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = _target_mention(update)
    ship = random.choice(_ANIME_SHIPS)
    ship_name, desc = ship
    pct = random.randint(60, 100)
    if target:
        await update.message.reply_text(
            f"💕 <b>Anime Ship!</b>\n\n"
            f"{_mention(user)} × {target}\n\n"
            f"You're like: <b>{ship_name}</b>\n"
            f"<i>{desc}</i>\n\n"
            f"❤️ Ship compatibility: <b>{pct}%</b>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"💕 Reply to someone to ship them!\n\n"
            f"Random ship today: <b>{ship_name}</b>\n<i>{desc}</i>",
            parse_mode="HTML",
        )


async def animematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char_name, show, skill, power, em = random.choice(_ANIME_FIGHT_CHARS)
    pct = random.randint(65, 100)
    await update.message.reply_text(
        f"{em} <b>Anime Character Match!</b>\n\n"
        f"{_mention(user)}, you match <b>{pct}%</b> with:\n\n"
        f"<b>{char_name}</b> from <i>{show}</i>!\n"
        f"Your shared power: <b>{skill}</b>",
        parse_mode="HTML",
    )


async def animepower(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    power_name, desc, em = random.choice(_ANIME_POWERS)
    level = random.randint(70, 9999)
    await update.message.reply_text(
        f"{em} <b>Your Anime Power!</b>\n\n"
        f"{_mention(user)}, your power is:\n\n"
        f"<b>{power_name}</b>\n"
        f"<i>{desc}</i>\n\n"
        f"⚡ Power Level: <b>{level:,}</b>",
        parse_mode="HTML",
    )


async def animeclan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clan_name, show, desc = random.choice(_ANIME_CLANS)
    await update.message.reply_text(
        f"🏯 <b>Your Anime Clan!</b>\n\n"
        f"{_mention(user)}, you belong to the:\n\n"
        f"<b>{clan_name}</b> ({show})\n"
        f"<i>{desc}</i>",
        parse_mode="HTML",
    )


async def animeaura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    aura, desc = random.choice(_ANIME_AURA)
    await update.message.reply_text(
        f"✨ <b>Your Anime Aura!</b>\n\n"
        f"{_mention(user)}, your aura is:\n\n"
        f"<b>{aura}</b>\n"
        f"<i>{desc}</i>",
        parse_mode="HTML",
    )


async def animesensei(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name, show, desc = random.choice(_ANIME_SENSEI)
    await update.message.reply_text(
        f"🎓 <b>Your Anime Sensei!</b>\n\n"
        f"{_mention(user)}, your sensei is:\n\n"
        f"<b>{name}</b> from <i>{show}</i>!\n"
        f"<i>{desc}</i>",
        parse_mode="HTML",
    )


async def animewho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descriptions = [
        ("I protect my nakama above all else. I ate a Devil Fruit and my body stretches!", "Monkey D. Luffy", "One Piece"),
        ("I am the strongest. My eyes can see through everything with Infinity.", "Gojo Satoru", "Jujutsu Kaisen"),
        ("I failed my entrance exam but inherited the greatest power ever known.", "Izuku Midoriya", "My Hero Academia"),
        ("I am the Shadow of Death. I erase existences with my Sharingan.", "Itachi Uchiha", "Naruto"),
        ("I carry the weight of my brother's mistake on my right arm of metal.", "Edward Elric", "FMA: Brotherhood"),
        ("I am humanity's strongest soldier. I never give up.", "Levi Ackerman", "Attack on Titan"),
        ("I became a Demon Slayer to avenge my family and cure my sister.", "Tanjiro Kamado", "Demon Slayer"),
        ("I died and revived 408 times. My power is Death itself.", "Rimuru Tempest", "TenSura"),
    ]
    desc, answer, show = random.choice(descriptions)
    from handlers.games_extra import _active_games, _start_quiz
    await _start_quiz(update, context,
        question=f"🕵️ <b>Guess the Anime Character!</b>\n\n<i>{desc}</i>",
        answer=answer.lower(), accepted=[answer.lower(), answer.split()[0].lower()],
        timeout=40)


# ══════════════════════════════════════════════════════════════════════════════
# ── 3. REACTION GIF COMMANDS ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _reaction(endpoint: str, self_tmpl: str, target_tmpl: str):
    """Factory: returns an async handler for a reaction command."""
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user   = update.effective_user
        target = _target_mention(update)
        caption = target_tmpl.format(user=_mention(user), target=target) if target \
                  else self_tmpl.format(user=_mention(user))
        await _send_gif(update, context, endpoint, caption)
    return handler

pat       = _reaction("pat",       "{user} pats themselves 🤷",    "{user} pats {target} 🥺👋")
hug       = _reaction("hug",       "{user} hugs the air 🤗",       "{user} hugs {target} tight! 🤗💕")
kiss      = _reaction("kiss",      "{user} blows a kiss 😘",       "{user} kisses {target}! 😘💋")
slap      = _reaction("slap",      "{user} slaps themselves 😅",   "{user} slaps {target}! 💢👋")
poke      = _reaction("poke",      "{user} pokes the void 👉",     "{user} pokes {target}! 👉😄")
cuddle    = _reaction("cuddle",    "{user} cuddles a pillow 🛋️",   "{user} cuddles {target}! 🥰")
bonk      = _reaction("bonk",      "{user} bonks their own head!", "{user} bonks {target}! 🔨")
punch     = _reaction("punch",     "{user} punches the air! 👊",   "{user} punches {target}! 👊💥")
adance    = _reaction("dance",     "{user} breaks into a dance! 💃🕺", "{user} dances with {target}! 💃🕺")
wave      = _reaction("wave",      "{user} waves hello! 👋",        "{user} waves at {target}! 👋😊")
blush     = _reaction("blush",     "{user} is blushing! 😳",        "{user} blushes at {target}! 😳💕")
cryanime  = _reaction("cry",       "{user} is crying! 😭",          "{user} cries because of {target}! 😭")
laugh     = _reaction("laugh",     "{user} bursts out laughing! 😂","{user} laughs at {target}! 😂")
smug      = _reaction("smug",      "{user} has a smug face 😏",     "{user} looks smugly at {target} 😏")
nom       = _reaction("nom",       "{user} noms on a snack 😋",     "{user} noms on {target}! 😋")
wink      = _reaction("wink",      "{user} winks mysteriously 😉",  "{user} winks at {target}! 😉")
bite      = _reaction("bite",      "{user} bites their own arm 😅", "{user} bites {target}! 🦷")
kick      = _reaction("kick",      "{user} kicks the air! 🦵",      "{user} kicks {target}! 🦵💥")
yeet      = _reaction("yeet",      "{user} yeeted something! 🚀",   "{user} yeets {target}! 🚀")
baka      = _reaction("baka",      "{user} calls themselves baka! 🤦", "{user} calls {target} BAKA! 🤦💢")
highfive  = _reaction("highfive",  "{user} high-fives the air ✋",   "{user} high-fives {target}! ✋🙌")
handshake = _reaction("handshake", "{user} offers a handshake 🤝",  "{user} shakes hands with {target}! 🤝")
nod_anim  = _reaction("nod",       "{user} nods thoughtfully 🤔",   "{user} nods at {target} 🤔")
asleep    = _reaction("sleep",     "{user} falls asleep 😴💤",       "{user} falls asleep near {target}! 😴💤")
stare     = _reaction("stare",     "{user} stares into the void 👀","{user} stares at {target}! 👀")


# ══════════════════════════════════════════════════════════════════════════════
# ── 4. ANIME PROFILE / WATCHLIST (in-memory) ─────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

_watchlists: dict[int, list] = {}   # user_id → [anime titles]
_anime_ratings: dict[int, dict] = {}  # user_id → {title: score}

async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/addwatch [title] — add anime to your watchlist."""
    if not context.args:
        await update.message.reply_text("📋 Usage: <code>/addwatch Demon Slayer</code>", parse_mode="HTML")
        return
    uid   = update.effective_user.id
    title = " ".join(context.args).strip()
    lst   = _watchlists.setdefault(uid, [])
    if title.lower() in [t.lower() for t in lst]:
        await update.message.reply_text(f"ℹ️ <b>{title}</b> is already in your watchlist!", parse_mode="HTML")
        return
    lst.append(title)
    await update.message.reply_text(
        f"✅ Added <b>{title}</b> to your watchlist!\n<i>Total: {len(lst)} anime</i>",
        parse_mode="HTML",
    )


async def myanilist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/myanilist — view your watchlist."""
    uid = update.effective_user.id
    lst = _watchlists.get(uid, [])
    if not lst:
        await update.message.reply_text(
            "📋 Your watchlist is empty!\nUse <code>/addwatch Anime Name</code> to add some.",
            parse_mode="HTML",
        )
        return
    lines = [f"📋 <b>Your Watchlist</b> ({len(lst)} anime)\n━━━━━━━━━━━━━━━━"]
    for i, title in enumerate(lst, 1):
        score = _anime_ratings.get(uid, {}).get(title.lower())
        s_str = f"  ⭐{score}/10" if score else ""
        lines.append(f"{i}. {title}{s_str}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def aniprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/aniprofile — view your anime profile."""
    user = update.effective_user
    uid  = user.id
    lst  = _watchlists.get(uid, [])
    rats = _anime_ratings.get(uid, {})
    avg_score = round(sum(rats.values()) / len(rats), 1) if rats else "N/A"
    power_name, _, em = random.choice(_ANIME_POWERS)
    aura_str, _ = random.choice(_ANIME_AURA)
    await update.message.reply_text(
        f"🎌 <b>Anime Profile</b>\n━━━━━━━━━━━━━━━━\n"
        f"👤 Name: {_mention(user)}\n"
        f"📋 Watchlist: <b>{len(lst)}</b> anime\n"
        f"⭐ Avg Rating: <b>{avg_score}</b>\n"
        f"⚡ Power: <b>{power_name}</b> {em}\n"
        f"✨ Aura: <b>{aura_str.split('—')[0].strip()}</b>\n",
        parse_mode="HTML",
    )
