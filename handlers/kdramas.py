"""
handlers/kdramas.py — 20 K-drama commands.
Uses curated static data + optional TVmaze lookups.
"""

import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes

_TVMAZE = "https://api.tvmaze.com"

_TOP_KDRAMAS = [
    ("My Mister", 2018, "IU, Lee Sun-kyun", "A depressed middle-aged man and a cold young woman help heal each other."),
    ("Signal", 2016, "Lee Je-hoon, Kim Hye-soo", "A detective communicates through a walkie-talkie across time to solve cold cases."),
    ("Misaeng: Incomplete Life", 2014, "Im Si-wan", "A former Go prodigy navigates corporate life as an intern."),
    ("Reply 1988", 2015, "Hyeri, Park Bo-gum", "Five friends grow up in a 1988 Seoul neighbourhood — nostalgic masterpiece."),
    ("Crash Landing on You", 2019, "Hyun Bin, Son Ye-jin", "A South Korean heiress accidentally paraglides into North Korea."),
    ("Goblin", 2016, "Gong Yoo, Lee Dong-wook", "An immortal goblin seeks a human bride to end his curse."),
    ("Vincenzo", 2021, "Song Joong-ki", "An Italian-Korean mafia lawyer returns to Korea and fights corruption."),
    ("Kingdom", 2019, "Ju Ji-hoon, Bae Doona", "A Joseon-era prince investigates a plague that turns people into zombies."),
    ("Itaewon Class", 2020, "Park Seo-jun", "A man builds a restaurant empire to take revenge on the conglomerate that ruined his family."),
    ("Squid Game", 2021, "Lee Jung-jae, Park Hae-soo", "456 contestants play deadly children's games for a prize of 45.6 billion won."),
    ("Extraordinary Attorney Woo", 2022, "Park Eun-bin", "A brilliant autistic lawyer navigates complex cases and social challenges."),
    ("My Liberation Notes", 2022, "Lee El, Kim Ji-won", "Three siblings in a suburb of Seoul each struggle to find meaning in life."),
    ("Juvenile Justice", 2022, "Kim Hye-soo", "A strict judge joins a juvenile court and confronts complex cases."),
    ("All of Us Are Dead", 2022, "Cho Yi-hyun", "High school students fight to survive a zombie outbreak."),
    ("Sweet Home", 2020, "Song Kang", "Residents of an apartment complex fight monsters that come from human desires."),
]

_ROMANTIC_KDRAMAS = [
    ("Crash Landing on You", 2019, "South Korean heiress meets North Korean officer."),
    ("Goblin", 2016, "Immortal goblin and his human bride across centuries."),
    ("What's Wrong with Secretary Kim", 2018, "A narcissistic boss falls for his efficient secretary."),
    ("Weightlifting Fairy Kim Bok-joo", 2016, "A weightlifting student finds friendship and first love."),
    ("Strong Woman Do Bong-soon", 2017, "A woman with superhuman strength is hired as a bodyguard by a playboy CEO."),
    ("She Was Pretty", 2015, "Childhood friends reconnect as adults — both have changed."),
    ("Because This Is My First Life", 2017, "Two strangers enter a contract marriage for practical reasons."),
    ("My Love from the Star", 2013, "An alien who came to Earth 400 years ago falls for a modern actress."),
    ("Boys Over Flowers", 2009, "A working-class girl enters an elite school filled with F4."),
    ("The King: Eternal Monarch", 2020, "A parallel universe story — Korean emperor falls for a detective."),
]

_ACTION_KDRAMAS = [
    ("Vincenzo", 2021, "Mafia lawyer takes on Korean conglomerates with style and violence."),
    ("Kingdom", 2019, "Historical zombie thriller set in Joseon Korea."),
    ("Rugal", 2020, "A detective gets cybernetic eyes and hunts down criminals."),
    ("Vagabond", 2019, "A stuntman uncovers a national corruption scandal after a plane crash."),
    ("Bad Guys", 2014, "Police use criminals to catch criminals."),
    ("The K2", 2016, "Former military bodyguard protects a presidential candidate's secret daughter."),
    ("Black", 2017, "A grim reaper inhabits a police officer's body to solve murders."),
    ("Voice", 2017, "A dispatch team tracks serial killers in real time."),
    ("Stranger", 2017, "A prosecutor with no emotions uncovers a vast corruption network."),
    ("Mouse", 2021, "A police officer hunts a serial killer — identity is the core mystery."),
]

_HISTORICAL_KDRAMAS = [
    ("Mr. Sunshine", 2018, "A joseon man becomes a US marine and returns to Korea in 1871."),
    ("Empress Ki", 2013, "A Korean woman becomes an empress of the Yuan dynasty."),
    ("My Country: The New Age", 2019, "Two friends become rivals during the founding of the Joseon dynasty."),
    ("Six Flying Dragons", 2015, "The founding of the Joseon dynasty from the perspective of six revolutionaries."),
    ("Jewel in the Palace", 2003, "The true story of Korea's first female royal physician."),
    ("Hwarang", 2016, "Elite warriors of the Silla dynasty — starring Park Hyung-sik and BTS' V."),
    ("The Red Sleeve", 2021, "A royal court lady and a crown prince fall in love."),
    ("Under the Queen's Umbrella", 2022, "A queen fights to secure her sons' place in the royal succession."),
]

_KDRAMA_OST = [
    ("My Love from the Star", "My Destiny — Lyn"),
    ("Goblin", "Stay With Me — Chanyeol & Punch, Sentimental — SHINee"),
    ("Crash Landing on You", "Flower — Yoon Mi-rae"),
    ("Descendants of the Sun", "Always — Yoon Mi-rae, You Are My Everything — Gummy"),
    ("Hotel del Luna", "Done for Me — Paul Kim"),
    ("It's Okay to Not Be Okay", "Breath — Heize"),
    ("Signal", "I Miss You — Kim Chang-wan"),
    ("Twenty-Five Twenty-One", "Sudenly — BOL4"),
    ("Extraordinary Attorney Woo", "Be Brave — Lee Seok-hoon"),
    ("Weightlifting Fairy Kim Bok-joo", "True Love — Jung Joon-young"),
]

_KDRAMA_QUOTES = [
    ("Goblin", "You've endured, and you have overcome. Our choices create our fate."),
    ("Crash Landing on You", "Don't go. Don't disappear from my sight. Stay by my side forever."),
    ("My Mister", "I'm happy. I'm sad. Either way, I'm alive."),
    ("Misaeng", "I haven't finished it yet. As long as I'm alive, I haven't lost."),
    ("Reply 1988", "Adults were once children too. They just forgot."),
    ("Itaewon Class", "The time you enjoy wasting is not wasted time."),
    ("Vincenzo", "If the law can't provide justice, I'll deliver it my way."),
]

_KDRAMA_FACTS = [
    "Squid Game became Netflix's most-watched show ever, viewed in 111 million households in its first month.",
    "South Korea's film and drama industry earns the country over $12 billion annually.",
    "The Korean Wave (Hallyu) has spread K-drama, K-pop, and Korean culture globally since the 1990s.",
    "K-dramas are typically 16 episodes long — allowing tight, satisfying storylines.",
    "Crash Landing on You drew the second highest ratings in tvN cable channel history.",
    "Korean actors often film 14+ hour days back-to-back while series are still airing.",
    "The first K-drama to win a Daytime Emmy Award was Jewel in the Palace (Dae Jang Geum).",
    "BTS (the K-pop group) has starred in K-dramas — V (Kim Taehyung) in Hwarang.",
    "Netflix invested over $700 million in Korean content between 2021-2022.",
]

_KPOP_GROUPS = [
    ("BTS", "HYBE", "Boy with Luv, Dynamite, Butter, DNA"),
    ("BLACKPINK", "YG Entertainment", "DDU-DU DDU-DU, Kill This Love, Lovesick Girls"),
    ("EXO", "SM Entertainment", "Growl, Call Me Baby, Love Shot"),
    ("TWICE", "JYP Entertainment", "Cheer Up, Fancy, What is Love?"),
    ("Stray Kids", "JYP Entertainment", "God's Menu, MIROH, Thunderous"),
    ("ITZY", "JYP Entertainment", "DALLA DALLA, ICY, Not Shy"),
    ("aespa", "SM Entertainment", "Black Mamba, Next Level, Savage"),
    ("NewJeans", "HYBE/ADOR", "Attention, Hype Boy, OMG"),
    ("IVE", "Starship Entertainment", "ELEVEN, Love Dive, After LIKE"),
    ("G-Dragon", "YG Entertainment", "Fantastic Baby, Crooked, Coup D'état"),
]

# ── Commands ──────────────────────────────────────────────────────────────────

async def kdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kdrama <title>\nExample: /kdrama Goblin")
        return
    query = " ".join(context.args)
    msg   = await update.message.reply_text(f"🔍 Searching for <b>{query}</b>...", parse_mode="HTML")
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{_TVMAZE}/singlesearch/shows", params={"q": query})
            if r.status_code == 200:
                show = r.json()
                import re
                name    = show.get("name", "N/A")
                year    = (show.get("premiered") or "?")[:4]
                rating  = (show.get("rating") or {}).get("average") or "N/A"
                summary = re.sub(r"<[^>]+>", "", show.get("summary") or "")[:300]
                await msg.edit_text(
                    f"🇰🇷 <b>{name}</b> ({year})\n⭐ Rating: {rating}/10\n\n{summary}",
                    parse_mode="HTML"
                )
                return
    except Exception:
        pass
    # fallback: search static list
    matches = [d for d in _TOP_KDRAMAS if query.lower() in d[0].lower()]
    if matches:
        t, y, cast, desc = matches[0]
        await msg.edit_text(
            f"🇰🇷 <b>{t}</b> ({y})\n👥 Cast: {cast}\n\n{desc}", parse_mode="HTML"
        )
    else:
        await msg.edit_text(f"No results found for <b>{query}</b>.", parse_mode="HTML")


async def topkdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"{i+1}. <b>{t}</b> ({y}) — {c}" for i, (t, y, c, _) in enumerate(_TOP_KDRAMAS[:10])]
    await update.message.reply_text(
        "🇰🇷 <b>Top K-Dramas</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def kdramarec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, cast, desc = random.choice(_TOP_KDRAMAS)
    await update.message.reply_text(
        f"🇰🇷 <b>K-Drama Recommendation</b>\n\n<b>{t}</b> ({y})\n👥 {cast}\n\n{desc}",
        parse_mode="HTML"
    )


async def romantickdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_ROMANTIC_KDRAMAS)
    await update.message.reply_text(f"💕 <b>Romantic K-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def actionkdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_ACTION_KDRAMAS)
    await update.message.reply_text(f"💥 <b>Action K-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def historicalkdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_HISTORICAL_KDRAMAS)
    await update.message.reply_text(f"🏯 <b>Historical K-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def schoolkdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Weightlifting Fairy Kim Bok-joo", 2016, "A university weightlifter finds first love."),
        ("School 2015: Who Are You?", 2015, "Twin sisters swap lives."),
        ("Cheese in the Trap", 2016, "A college student unravels the psychology of a perfect sunbae."),
        ("A-Teen", 2018, "Web drama about high school friendships and first loves."),
        ("True Beauty", 2020, "A girl who transforms herself with makeup faces first love."),
        ("School 2021", 2021, "Teenagers navigate vocational school and dreams."),
    ]
    t, y, desc = random.choice(shows)
    await update.message.reply_text(f"📚 <b>School K-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def netflixkdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Squid Game", 2021), ("Kingdom", 2019), ("Sweet Home", 2020),
        ("All of Us Are Dead", 2022), ("Extraordinary Attorney Woo", 2022),
        ("My Liberation Notes", 2022), ("D.P.", 2021), ("Juvenile Justice", 2022),
    ]
    t, y = random.choice(shows)
    await update.message.reply_text(
        f"📺 <b>K-Drama on Netflix</b>\n\n<b>{t}</b> ({y})\n\nSearch on Netflix to watch!",
        parse_mode="HTML"
    )


async def kdramaoss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show, song = random.choice(_KDRAMA_OST)
    await update.message.reply_text(f"🎵 <b>Famous K-Drama OST</b>\n\n📺 {show}\n🎵 {song}", parse_mode="HTML")


async def kdramafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🇰🇷 <b>K-Drama Fact</b>\n\n{random.choice(_KDRAMA_FACTS)}", parse_mode="HTML")


async def kdramaquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show, quote = random.choice(_KDRAMA_QUOTES)
    await update.message.reply_text(f'🇰🇷 <b>K-Drama Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{show}</b>', parse_mode="HTML")


async def kpop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group, company, songs = random.choice(_KPOP_GROUPS)
    await update.message.reply_text(
        f"🎤 <b>K-Pop Group</b>\n\n<b>{group}</b>\n🏢 Label: {company}\n🎵 Famous songs: {songs}",
        parse_mode="HTML"
    )


async def kpopfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "BTS became the first Korean act to top the Billboard Hot 100 with 'Dynamite' in 2020.",
        "BLACKPINK is the most-subscribed music act on YouTube with 90+ million subscribers.",
        "K-pop trainees typically train for 2-7 years before debuting.",
        "PSY's 'Gangnam Style' was the first YouTube video to reach 1 billion views in 2012.",
        "The Korean music industry generated over $5 billion in revenue in 2022.",
        "BTS' ARMY fandom is considered the most powerful music fan base in the world.",
        "South Korea has won Eurovision Song Contest categories despite not being in Europe.",
    ]
    await update.message.reply_text(f"🎤 <b>K-Pop Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def kpopchart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 <b>K-Pop Charts</b>\n\nFor live charts:\n"
        "🔗 <a href='https://www.melon.com/'>Melon Chart</a>\n"
        "🔗 <a href='https://www.gaon.co.kr/'>Gaon Chart</a>\n"
        "🔗 <a href='https://www.billboard.com/charts/hot-100/'>Billboard Hot 100</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def kdramaactor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kdramaactor <name>\nExample: /kdramaactor Hyun Bin")
        return
    name  = " ".join(context.args)
    known = {
        "hyun bin": "Crash Landing on You, Secret Garden, Hyde Jekyll Me",
        "son ye jin": "Crash Landing on You, A Moment to Remember, Summer Scent",
        "lee min ho": "Boys Over Flowers, City Hunter, The Heirs, Legend of the Blue Sea",
        "park seo jun": "Itaewon Class, Her Private Life, What's Wrong with Secretary Kim",
        "gong yoo": "Goblin, Coffee Prince, Train to Busan",
        "iu": "Hotel del Luna, My Mister, Moon Lovers",
        "song joong ki": "Vincenzo, Descendants of the Sun, Arthdal Chronicles",
    }
    info = known.get(name.lower(), f"Notable Korean actor. Search for {name}'s dramas on MyDramaList.")
    await update.message.reply_text(f"🇰🇷 <b>{name}</b>\n\nNotable dramas: {info}", parse_mode="HTML")


async def webdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Love with Flaws", 2019, "Short-format comedy-romance."),
        ("A-Teen", 2018, "High school life in short episodes."),
        ("To Be Continued", 2015, "EXO members in a romantic webdrama."),
        ("Seven First Kisses", 2016, "A woman goes on dates with 7 Korean stars."),
        ("Seventeen's One Fine Day", 2014, "Idol group survival webdrama."),
    ]
    t, y, desc = random.choice(shows)
    await update.message.reply_text(f"📱 <b>K-Web Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def kdramamood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /kdramamood <mood>\nOptions: happy, sad, thriller, romance, action, historical"
        )
        return
    mood = context.args[0].lower()
    mapping = {
        "happy": ("Reply 1988", 2015, "A heartwarming nostalgic drama about five friends in 1988 Seoul."),
        "sad": ("My Mister", 2018, "A quiet, deeply moving story of two broken souls helping each other."),
        "thriller": ("Signal", 2016, "A detective communicates across time to solve cold cases."),
        "romance": ("Crash Landing on You", 2019, "North-South Korea love story — swoony and dramatic."),
        "action": ("Vincenzo", 2021, "Mafia lawyer serves cold revenge with style."),
        "historical": ("Mr. Sunshine", 2018, "Love and revolution in 1900s Korea."),
    }
    if mood in mapping:
        t, y, desc = mapping[mood]
        await update.message.reply_text(f"🎭 <b>K-Drama for {mood.title()} mood</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")
    else:
        await update.message.reply_text("Unknown mood. Try: happy, sad, thriller, romance, action, historical")


async def kdramawatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📺 <b>Where to Watch K-Dramas</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 <a href='https://www.netflix.com/'>Netflix</a> — large library\n"
        "🔗 <a href='https://www.kocowa.com/'>Kocowa</a> — same-day subs\n"
        "🔗 <a href='https://www.viki.com/'>Viki</a> — free with ads\n"
        "🔗 <a href='https://www.vlive.tv/'>VLive</a> — fan-subbed content\n"
        "🔗 <a href='https://www.dramacool.com.pa/'>DramaCool</a> — free streaming",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def koreafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "South Korea has one of the fastest internet speeds in the world.",
        "Kimchi, a fermented vegetable dish, is eaten at virtually every meal in Korea.",
        "Korea has the world's highest plastic surgery rate per capita.",
        "South Korea is one of the world's largest exporters of cosmetics and beauty products.",
        "The Korean alphabet (Hangul) was invented by King Sejong in the 15th century.",
        "Korea has the world's longest pedestrian bridge — the Moonlight Rainbow Fountain Bridge in Seoul.",
        "Soju is the world's best-selling spirit — made by Jinro in South Korea.",
    ]
    await update.message.reply_text(f"🇰🇷 <b>Korea Fun Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def kdramaquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qas = [
        ("Which K-drama became Netflix's most-watched show of all time?", "Squid Game (2021)"),
        ("Who plays the male lead in Crash Landing on You?", "Hyun Bin"),
        ("What year did Boys Over Flowers air?", "2009"),
        ("In Goblin, what is the goblin's name?", "Kim Shin"),
        ("Which network produces most popular K-dramas?", "tvN and KBS"),
        ("Who plays Park Saeroyi in Itaewon Class?", "Park Seo-jun"),
        ("What is the name of the squid game host character?", "Oh Il-nam (001)"),
    ]
    q, a = random.choice(qas)
    await update.message.reply_text(
        f"🇰🇷 <b>K-Drama Quiz</b>\n\n❓ {q}\n\n<tg-spoiler>✅ {a}</tg-spoiler>",
        parse_mode="HTML"
    )
