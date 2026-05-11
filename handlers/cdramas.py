"""
handlers/cdramas.py — 20 C-drama commands.
Static curated data for Chinese dramas, C-pop, and cinema.
"""

import random
from telegram import Update
from telegram.ext import ContextTypes

_TOP_CDRAMAS = [
    ("The Story of Ming Lan", 2018, "Romance/Historical", "A smart but low-born girl navigates the Song dynasty aristocracy."),
    ("The Untamed", 2019, "Xianxia/BL", "Two powerful cultivators fight evil together — iconic bromance."),
    ("Word of Honor", 2021, "Wuxia/BL", "A top assassin and a carefree sect leader become unlikely partners."),
    ("Nirvana in Fire", 2015, "Political/Historical", "A disgraced general returns in disguise to reclaim justice."),
    ("Love and Redemption", 2020, "Xianxia", "A heaven-and-hell romance across lifetimes."),
    ("The Long Ballad", 2021, "Historical/Action", "A princess flees her destroyed dynasty and finds love and purpose."),
    ("Ashes of Love", 2018, "Xianxia", "A flower fairy falls for a god of the nine heavens."),
    ("Arsenal Military Academy", 2019, "Military/Romance", "A girl disguises herself as a boy to attend military school."),
    ("The Story of Yanxi Palace", 2018, "Historical", "A maid rises to power in the Qianlong Emperor's harem."),
    ("Go Ahead", 2020, "Family Drama", "Three children from broken families form an unconventional family."),
    ("Nothing But You", 2023, "Modern Romance", "A CEO falls for an ambitious coffee shop owner."),
    ("A Dream of Splendor", 2022, "Historical/Romance", "Three women pursue their dreams in a Song dynasty teahouse."),
    ("Meteor Garden", 2018, "Modern Romance", "Poor girl enters elite university and falls for the leader of F4."),
    ("Ancient Love Poetry", 2021, "Xianxia", "The love story of an ancient god and a girl across three lifetimes."),
    ("Lost You Forever", 2023, "Xianxia", "A woman with lost memories returns to find herself between three men."),
]

_XIANXIA = [
    ("The Untamed", 2019, "Mo Dao Zu Shi adaptation — two cultivators battle supernatural evil."),
    ("Ashes of Love", 2018, "A flower fairy and the phoenix fire deity fall in love."),
    ("The Eternal Love", 2017, "A modern soul inhabits a historical body and falls for the eighth prince."),
    ("Love and Redemption", 2020, "A goddess and a demon king navigate fate and rebirth."),
    ("Three Lives Three Worlds, Ten Miles of Peach Blossoms", 2017, "An immortal's love story across lifetimes."),
    ("Ancient Love Poetry", 2021, "The love story of an ancient god across three lifetimes."),
    ("Immortality", 2022, "Adaptation of the second Mo Dao Zu Shi prequel."),
    ("The Blood of Youth", 2022, "Young heroes in a jianghu world seek strength and justice."),
]

_WUXIA = [
    ("Nirvana in Fire", 2015, "A strategist disguised as an invalid rebuilds his family's honour."),
    ("Word of Honor", 2021, "A top killer and an unruly hero travel the jianghu together."),
    ("The Long Ballad", 2021, "A princess learns to fight and find herself."),
    ("Sword Snow Stride", 2021, "A martial arts legend's son seeks to be better than his father."),
    ("The Longest Day in Chang'an", 2019, "A city official investigates a terrorist plot in ancient Chang'an."),
    ("Joy of Life", 2019, "A reincarnated man from the future navigates a corrupt court."),
    ("The Legend of Shen Li", 2024, "A war god reborn in human form falls in love."),
]

_HISTORICAL_CDRAMAS = [
    ("The Story of Yanxi Palace", 2018, "A sharp palace maid climbs the imperial ranks in the Qing dynasty."),
    ("Nirvana in Fire", 2015, "A prince's strategist orchestrates justice from the shadows."),
    ("The Story of Ming Lan", 2018, "A clever woman navigates arranged marriage and Song-dynasty politics."),
    ("The Glory of Tang Dynasty", 2017, "The Tang dynasty's power politics through a princess's eyes."),
    ("The Ideal City", 2021, "A young architect navigates corruption in a modern city."),
    ("Scarlet Heart", 2011, "A modern woman travels to the Qing dynasty and falls for princes."),
]

_MODERN_CDRAMAS = [
    ("Go Ahead", 2020, "Three children from broken families become an unconventional family."),
    ("Start-Up", 2020, "Young entrepreneurs battle in Silicon Valley-style startup world."),
    ("Nothing But You", 2023, "A CEO and an ambitious woman fall in love."),
    ("The Bad Kids", 2020, "Three children witness a murder — a dark psychological thriller."),
    ("Reset", 2022, "A woman is stuck in a time loop involving a bus explosion."),
    ("My Heroine Academia", 2021, "A college girl navigates modern relationships."),
]

_CDRAMA_OST = [
    ("The Untamed", "Wu Ji — Xiao Zhan & Wang Yibo"),
    ("Ashes of Love", "Falling Into Your Smile — OST"),
    ("Three Lives Three Worlds", "Pillow Book Theme"),
    ("Nirvana in Fire", "Langya Bang Main Theme"),
    ("The Story of Yanxi Palace", "Pearl Theme"),
    ("Word of Honor", "Dong Fang Wai Ji — Zhou Shen"),
    ("Love and Redemption", "Chenguang — Xiao Zhan"),
]

_CDRAMA_QUOTES = [
    ("Nirvana in Fire", "The mountains and rivers remain, but the people are gone. How can one not grieve?"),
    ("The Untamed", "No matter what you become, I will not be afraid."),
    ("The Story of Ming Lan", "A woman who knows herself is invincible."),
    ("Go Ahead", "Family doesn't have to mean blood. It means the people who choose you."),
    ("The Bad Kids", "Some things, if you think about them too much, become unbearable."),
    ("Word of Honor", "The wind stops, the clouds scatter, and what remains is just us."),
]

_CDRAMA_FACTS = [
    "China produces the most TV dramas in the world — over 15,000 episodes annually.",
    "'The Story of Yanxi Palace' was the most-searched drama globally on Google in 2018.",
    "The Untamed (based on Mo Dao Zu Shi) has a massive international fandom, especially in Southeast Asia.",
    "Chinese xianxia dramas are based on 'cultivation' fantasy novels — a uniquely Chinese genre.",
    "The budget for some top Chinese dramas rivals Hollywood productions — costing $30M+ per show.",
    "WeTV and iQIYI are the two biggest streaming platforms for C-dramas in Asia.",
    "Nirvana in Fire is considered by many critics to be the greatest Chinese TV drama ever made.",
    "Chinese dramas can run for 40-80 episodes per season — much longer than Korean or Western shows.",
]

_CPOP_ARTISTS = [
    ("Jay Chou", "Qilixiang, Nunchaku, Blue and White Porcelain — the 'King of Mandopop'"),
    ("G.E.M.", "One, Rare, Light Years Away — Hong Kong pop icon"),
    ("Hua Chenyu", "Silence — complex artsy pop and rock"),
    ("Xiao Zhan", "Dandelion's Promise — known from The Untamed"),
    ("Wang Yibo", "Seven — known from The Untamed"),
    ("Zhou Shen", "Ocean — known for his extraordinary vocal range"),
    ("Lay Zhang", "Sheep, K-Bop — EXO member and solo C-pop star"),
    ("CPN", "Various genres — indie and underground C-pop"),
]

_CHINA_FACTS = [
    "China has the world's largest population at 1.4 billion people.",
    "The Great Wall of China stretches over 21,000 km in total.",
    "Mandarin Chinese is the most-spoken native language in the world.",
    "China invented paper, printing, gunpowder, and the compass — the 'Four Great Inventions'.",
    "The Forbidden City in Beijing has 9,999 rooms and was built between 1406-1420.",
    "China has the world's largest high-speed rail network — over 40,000 km.",
    "The word 'China' is derived from the Qin dynasty (221–206 BC).",
    "China produces 80% of the world's garlic and 60% of the world's pigs.",
]

_WUXIA_FACTS = [
    "The word 'wuxia' (武侠) literally means 'martial heroes' in Chinese.",
    "Jin Yong (Louis Cha) is considered the greatest wuxia novelist of all time.",
    "Crouching Tiger, Hidden Dragon won 4 Academy Awards and popularised wuxia globally.",
    "Wuxia stories date back to ancient Chinese literature over 2,000 years ago.",
    "The term 'jianghu' (江湖) in wuxia means the martial world — literally 'rivers and lakes'.",
]

# ── Commands ──────────────────────────────────────────────────────────────────

async def cdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /cdrama <title>\nExample: /cdrama The Untamed")
        return
    query   = " ".join(context.args).lower()
    matches = [d for d in _TOP_CDRAMAS if query in d[0].lower()]
    if matches:
        t, y, genre, desc = matches[0]
        await update.message.reply_text(
            f"🇨🇳 <b>{t}</b> ({y})\n🎭 Genre: {genre}\n\n{desc}", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"No data found for <b>{query}</b>. Try /topcdrama for a curated list.",
            parse_mode="HTML"
        )


async def topcdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"{i+1}. <b>{t}</b> ({y}) — {g}" for i, (t, y, g, _) in enumerate(_TOP_CDRAMAS[:10])]
    await update.message.reply_text(
        "🇨🇳 <b>Top C-Dramas</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def cdramarec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, genre, desc = random.choice(_TOP_CDRAMAS)
    await update.message.reply_text(
        f"🇨🇳 <b>C-Drama Recommendation</b>\n\n<b>{t}</b> ({y})\n🎭 {genre}\n\n{desc}",
        parse_mode="HTML"
    )


async def xianxia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_XIANXIA)
    await update.message.reply_text(f"🌸 <b>Xianxia C-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def wuxia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_WUXIA)
    await update.message.reply_text(f"⚔️ <b>Wuxia C-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def chistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_HISTORICAL_CDRAMAS)
    await update.message.reply_text(f"🏯 <b>Historical C-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def cmodern(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, desc = random.choice(_MODERN_CDRAMAS)
    await update.message.reply_text(f"🏙️ <b>Modern C-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def cdramaactor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /cdramaactor <name>\nExample: /cdramaactor Xiao Zhan")
        return
    name  = " ".join(context.args)
    known = {
        "xiao zhan": "The Untamed, The Oath of Love, Jade Dynasty",
        "wang yibo": "The Untamed, Born to Fly, Battle at Lake Changjin",
        "zhao liying": "Story of Minglan, Nirvana in Fire 2, Eternal Love",
        "yang zi": "Ashes of Love, Go Ahead, Sweet Dreams",
        "chen feiyu": "Ancient Love Poetry, The Long Ballad",
        "dilraba dilmurat": "The Long Ballad, The Bad Kids, Pretty Li Hui Zhen",
    }
    info = known.get(name.lower(), f"Notable Chinese actor. Search {name} on iQIYI or WeTV.")
    await update.message.reply_text(f"🇨🇳 <b>{name}</b>\n\nNotable dramas: {info}", parse_mode="HTML")


async def cdramafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🇨🇳 <b>C-Drama Fact</b>\n\n{random.choice(_CDRAMA_FACTS)}", parse_mode="HTML")


async def cdramaquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show, quote = random.choice(_CDRAMA_QUOTES)
    await update.message.reply_text(f'🇨🇳 <b>C-Drama Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{show}</b>', parse_mode="HTML")


async def cpop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    artist, info = random.choice(_CPOP_ARTISTS)
    await update.message.reply_text(f"🎵 <b>C-Pop Artist</b>\n\n<b>{artist}</b>\n{info}", parse_mode="HTML")


async def cdramaoss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show, song = random.choice(_CDRAMA_OST)
    await update.message.reply_text(f"🎵 <b>Famous C-Drama OST</b>\n\n📺 {show}\n🎵 {song}", parse_mode="HTML")


async def cdramawatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📺 <b>Where to Watch C-Dramas</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 <a href='https://www.iq.com/'>iQIYI International</a>\n"
        "🔗 <a href='https://wetv.vip/'>WeTV</a>\n"
        "🔗 <a href='https://www.youtube.com/@CdramaBase'>YouTube CdramaBase</a>\n"
        "🔗 <a href='https://www.netflix.com/'>Netflix</a> (limited selection)\n"
        "🔗 <a href='https://www.viki.com/'>Viki</a> — free with fan subs",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def xuxian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Three Lives Three Worlds, Ten Miles of Peach Blossoms", 2017),
        ("Ashes of Love", 2018), ("Love and Redemption", 2020),
        ("Ancient Love Poetry", 2021), ("Lost You Forever", 2023),
    ]
    t, y = random.choice(shows)
    await update.message.reply_text(f"💕 <b>Romance C-Drama</b>\n\n<b>{t}</b> ({y})", parse_mode="HTML")


async def wuxiafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"⚔️ <b>Wuxia Fact</b>\n\n{random.choice(_WUXIA_FACTS)}", parse_mode="HTML")


async def chinafilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    films = [
        ("Farewell My Concubine", 1993, "Two Peking opera stars navigate friendship and politics."),
        ("Raise the Red Lantern", 1991, "A woman becomes the fourth wife of a powerful lord."),
        ("Hero", 2002, "A nameless warrior recounts his fights with assassins to the emperor."),
        ("Crouching Tiger Hidden Dragon", 2000, "Warriors pursue a stolen sword across China."),
        ("Ip Man", 2008, "The life of Bruce Lee's Wing Chun teacher."),
        ("The Battle at Lake Changjin", 2021, "Chinese soldiers fight in the Korean War — highest-grossing Chinese film."),
        ("Ne Zha", 2019, "An animated retelling of the mythical demon boy's origin."),
    ]
    t, y, desc = random.choice(films)
    await update.message.reply_text(f"🎬 <b>Chinese Cinema</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def cdramamood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /cdramamood <mood>\nOptions: happy, sad, action, romance, thriller, historical")
        return
    mood = context.args[0].lower()
    mapping = {
        "happy": ("Go Ahead", 2020, "Warm family drama about three children finding home in each other."),
        "sad": ("Nirvana in Fire", 2015, "A man's quiet sacrifice to restore justice — deeply moving."),
        "action": ("Word of Honor", 2021, "Martial arts adventure with incredible fight choreography."),
        "romance": ("The Story of Ming Lan", 2018, "Slow-burn romance in a beautifully realised Song dynasty setting."),
        "thriller": ("The Bad Kids", 2020, "Children accidentally witness a murder — dark psychological thriller."),
        "historical": ("The Story of Yanxi Palace", 2018, "Palace intrigue and a fiercely intelligent heroine."),
    }
    if mood in mapping:
        t, y, desc = mapping[mood]
        await update.message.reply_text(f"🎭 <b>C-Drama for {mood.title()} mood</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")
    else:
        await update.message.reply_text("Unknown mood. Try: happy, sad, action, romance, thriller, historical")


async def cdramagenre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /cdramagenre <genre>\nOptions: xianxia, wuxia, historical, modern, romance")
        return
    genre = context.args[0].lower()
    if genre == "xianxia":
        t, y, desc = random.choice(_XIANXIA)
    elif genre == "wuxia":
        t, y, desc = random.choice(_WUXIA)
    elif genre == "historical":
        t, y, desc = random.choice(_HISTORICAL_CDRAMAS)
    elif genre == "modern":
        t, y, desc = random.choice(_MODERN_CDRAMAS)
    elif genre == "romance":
        t, y, desc = random.choice([d for d in _XIANXIA])
    else:
        await update.message.reply_text("Unknown genre. Try: xianxia, wuxia, historical, modern, romance")
        return
    await update.message.reply_text(f"🇨🇳 <b>{genre.title()} C-Drama</b>\n\n<b>{t}</b> ({y})\n\n{desc}", parse_mode="HTML")


async def cdramaquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qas = [
        ("Which novel is 'The Untamed' based on?", "Mo Dao Zu Shi by MXTX"),
        ("Who plays Wei Wuxian in The Untamed?", "Xiao Zhan"),
        ("What dynasty is The Story of Yanxi Palace set in?", "Qing Dynasty"),
        ("What does 'xianxia' mean?", "Immortal heroes (仙侠)"),
        ("Which Chinese drama was most-searched on Google in 2018?", "The Story of Yanxi Palace"),
        ("What streaming platforms mainly host C-dramas?", "iQIYI, WeTV, and YouTube"),
        ("What is Nirvana in Fire about?", "A disgraced general returns as a strategist to restore his family's honour"),
    ]
    q, a = random.choice(qas)
    await update.message.reply_text(
        f"🇨🇳 <b>C-Drama Quiz</b>\n\n❓ {q}\n\n<tg-spoiler>✅ {a}</tg-spoiler>",
        parse_mode="HTML"
    )


async def chinafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🇨🇳 <b>China Fun Fact</b>\n\n{random.choice(_CHINA_FACTS)}", parse_mode="HTML")
