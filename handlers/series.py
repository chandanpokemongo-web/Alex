"""
handlers/series.py — 25 TV series commands.
Uses TVmaze free API (no key required) + static curated data.
"""

import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes

_TVMAZE = "https://api.tvmaze.com"

# ── Helper ────────────────────────────────────────────────────────────────────

async def _tvmaze(endpoint: str, params: dict = None) -> dict | list | None:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{_TVMAZE}/{endpoint}", params=params or {})
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text or "")[:300]


# ── Static data ───────────────────────────────────────────────────────────────

_TOP_SERIES = [
    ("Breaking Bad", 2008, "Drama/Crime", "A chemistry teacher turns to cooking meth after a terminal diagnosis."),
    ("The Wire", 2002, "Drama/Crime", "An unflinching look at drug trade, law enforcement, and systemic failure in Baltimore."),
    ("The Sopranos", 1999, "Drama/Crime", "A mob boss balances family life with leading a criminal empire."),
    ("Game of Thrones", 2011, "Fantasy/Drama", "Noble families fight for the Iron Throne of the Seven Kingdoms."),
    ("Chernobyl", 2019, "Drama/Mini", "The true story of one of the worst man-made disasters in history."),
    ("True Detective (S1)", 2014, "Crime/Mystery", "Two detectives hunt a serial killer across 17 years."),
    ("Band of Brothers", 2001, "War/Drama", "Easy Company's journey from D-Day to the end of WWII."),
    ("The Office (US)", 2005, "Comedy", "The daily lives of Dunder Mifflin paper company employees."),
    ("Fargo (S1)", 2014, "Crime/Dark Comedy", "A brutal crime spree in small-town Minnesota."),
    ("Sherlock", 2010, "Crime/Mystery", "A modern adaptation of Conan Doyle's detective stories."),
]

_NETFLIX_HITS = [
    ("Squid Game", 2021, "Korean thriller where contestants play deadly children's games for prize money."),
    ("Stranger Things", 2016, "Kids investigate supernatural events in 1980s Indiana."),
    ("Ozark", 2017, "A financial advisor launders money for a drug cartel in the Ozarks."),
    ("The Crown", 2016, "The reign of Queen Elizabeth II from the 1940s to 2000s."),
    ("Money Heist", 2017, "A gang of thieves executes the most daring heist in history."),
    ("Dark", 2017, "A German sci-fi thriller involving time travel across four generations."),
    ("Mindhunter", 2017, "FBI agents interview serial killers to solve cold cases."),
    ("The Witcher", 2019, "A mutated monster-hunter navigates a world where humans are often the true monsters."),
    ("Wednesday", 2022, "The iconic Addams Family character navigates a new school for outcasts."),
    ("Bridgerton", 2020, "A family of wealthy siblings navigate Regency-era London's high society."),
]

_HBO_HITS = [
    ("The Wire", 2002, "Arguably the greatest TV show ever made. Masterpiece of systemic storytelling."),
    ("The Sopranos", 1999, "Defined prestige television. Tony Soprano is one of TV's greatest characters."),
    ("Game of Thrones", 2011, "The most-watched TV series globally (Seasons 1-6 are perfect)."),
    ("Chernobyl", 2019, "Best reviewed miniseries of all time (9.4/10 on IMDb)."),
    ("True Detective S1", 2014, "McConaughey and Harrelson deliver career-best performances."),
    ("Euphoria", 2019, "A raw and visually stunning look at teenage life and addiction."),
    ("Succession", 2018, "A billionaire media family fights over who will inherit the empire."),
    ("The Last of Us", 2023, "Post-apocalyptic drama based on the acclaimed video game."),
    ("Westworld S1", 2016, "A futuristic theme park where androids begin to gain consciousness."),
    ("Band of Brothers", 2001, "Steven Spielberg and Tom Hanks produced this WWII masterpiece."),
]

_CRIME_SHOWS = [
    ("True Detective S1", "Rust Cohle and Marty Hart hunt a serial killer across Louisiana."),
    ("Mindhunter", "FBI profilers develop criminal psychology by interviewing killers."),
    ("Ozark", "A Missouri family launders drug money to survive in the Ozarks."),
    ("Fargo", "Coen Brothers-inspired anthology series of crime in the Midwest."),
    ("The Wire", "The most realistic portrayal of urban crime and policing ever made."),
    ("Narcos", "The true story of Colombian drug lord Pablo Escobar."),
    ("Peaky Blinders", "A gang in post-WWI Birmingham led by the Shelby family."),
    ("Sherlock", "Benedict Cumberbatch as a brilliant modern-day Sherlock Holmes."),
    ("Luther", "DCI John Luther navigates complex cases and a brilliant criminal mind."),
]

_COMEDY_SHOWS = [
    ("The Office US", "The definitive mockumentary workplace comedy."),
    ("Arrested Development", "A wealthy dysfunctional family loses everything."),
    ("It's Always Sunny in Philadelphia", "5 terrible friends run a bar in Philadelphia."),
    ("Parks and Recreation", "The optimistic bureaucracy of Pawnee, Indiana."),
    ("Brooklyn Nine-Nine", "A diverse group of detectives in a New York police precinct."),
    ("Schitt's Creek", "A wealthy family moves to a small town they once bought as a joke."),
    ("Fleabag", "A quick-witted woman navigates life in London with dark humour."),
    ("Ted Lasso", "An American college football coach manages an English soccer team."),
    ("What We Do in the Shadows", "Vampire flatmates try to adjust to modern Staten Island life."),
]

_SCIFI_SHOWS = [
    ("Black Mirror", "Near-future anthology episodes about technology and human nature."),
    ("Westworld", "A futuristic theme park becomes a battleground for consciousness."),
    ("Battlestar Galactica", "Survivors of a robot attack flee to find Earth."),
    ("Dark", "Time travel mystery spanning four generations in a German town."),
    ("Fringe", "A FBI agent investigates fringe science with a mad scientist."),
    ("Severance", "Office workers have their memories severed between work and home life."),
    ("Shogun (2024)", "A feudal Japan epic — best reviewed show of 2024."),
    ("Andor", "A gritty Star Wars prequel following a rebel spy's journey."),
    ("The Expanse", "Humanity has colonised the solar system — a conspiracy unfolds."),
]

_TV_QUOTES = [
    ("Breaking Bad", "I am the one who knocks."),
    ("The Office", "That's what she said."),
    ("Game of Thrones", "Chaos isn't a pit. Chaos is a ladder."),
    ("The Sopranos", "Remember when is the lowest form of conversation."),
    ("Friends", "We were on a break!"),
    ("The Wire", "A man's got to have a code."),
    ("Succession", "L to the OG"),
    ("Ted Lasso", "Believe."),
    ("Fleabag", "This is a love story."),
    ("Black Mirror", "I fucking knew it."),
]

_TV_FACTS = [
    "Breaking Bad is the highest-rated show on IMDb with an average of 9.5/10.",
    "The Sopranos effectively invented the golden age of TV drama in 1999.",
    "Game of Thrones became the most pirated TV show in history.",
    "The Office (US) ran for 9 seasons and 201 episodes.",
    "Friends generated over $1 billion in syndication revenue annually.",
    "Squid Game was Netflix's most-watched show ever, viewed in 111 million households.",
    "The Wire creator David Simon was a journalist before writing TV.",
    "Seinfeld was pitched to NBC as 'a show about nothing' — they almost rejected it.",
    "The average Game of Thrones episode from season 6 onwards cost $10 million to produce.",
    "Frasier won the Emmy for Outstanding Comedy Series 5 years in a row (1994-1998).",
]

_BRITISH_SHOWS = [
    ("Peaky Blinders", "Crime drama set in 1920s Birmingham, starring Cillian Murphy."),
    ("Sherlock", "Benedict Cumberbatch as a modern Sherlock Holmes."),
    ("Doctor Who", "The longest-running sci-fi series — since 1963."),
    ("Downton Abbey", "The lives of the aristocratic Crawley family from 1912-1926."),
    ("Black Mirror", "Charlie Brooker's dark technology anthology."),
    ("The Crown", "The reign of Queen Elizabeth II dramatised with stunning production."),
    ("Fleabag", "Phoebe Waller-Bridge's award-winning dark comedy."),
    ("Luther", "Idris Elba as a brilliant but emotionally compromised detective."),
    ("It's a Sin", "Five friends navigate the AIDS crisis in 1980s London."),
    ("Happy Valley", "A Yorkshire police sergeant faces a drug lord connected to her past."),
]

_MINISERIES = [
    ("Chernobyl", 5, "The catastrophic 1986 nuclear disaster in vivid detail."),
    ("Band of Brothers", 10, "Easy Company's journey through WWII."),
    ("The Pacific", 10, "American Marines fight in the Pacific theatre of WWII."),
    ("Sharp Objects", 8, "A reporter returns to her hometown to cover a murder."),
    ("Olive Kitteridge", 4, "Frances McDormand in a quiet, devastating New England drama."),
    ("Station Eleven", 10, "A theatre company survives 20 years after a flu pandemic."),
    ("Shogun", 10, "A feudal Japan saga — Emmys 2024 sweep."),
    ("The Undoing", 6, "Nicole Kidman in a NYC murder mystery thriller."),
    ("Mare of Easttown", 7, "Kate Winslet as a small-town detective investigating a murder."),
    ("Scenes from a Marriage", 5, "A couple's relationship over decades."),
]

_FANTASY_SHOWS = [
    ("Game of Thrones", "The original prestige fantasy epic."),
    ("House of the Dragon", "Fire and blood — the Targaryen civil war."),
    ("The Witcher", "A monster hunter in a medieval dark fantasy world."),
    ("The Lord of the Rings: Rings of Power", "The Second Age of Middle-earth."),
    ("Wheel of Time", "An epic fantasy based on Robert Jordan's book series."),
    ("Shadow and Bone", "A Netflix adaptation of Leigh Bardugo's Grishaverse."),
    ("Merlin", "The young Merlin and Prince Arthur in Camelot."),
    ("Once Upon a Time", "Fairy tale characters transported to modern-day Maine."),
]

# ── Commands ──────────────────────────────────────────────────────────────────

async def series_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /series <title>\nExample: /series Breaking Bad")
        return
    query = " ".join(context.args)
    msg   = await update.message.reply_text(f"🔍 Searching for <b>{query}</b>...", parse_mode="HTML")
    data  = await _tvmaze(f"singlesearch/shows", {"q": query})
    if data:
        show = data
        name    = show.get("name", "N/A")
        year    = (show.get("premiered") or "?")[:4]
        genres  = ", ".join(show.get("genres", ["N/A"]))
        status  = show.get("status", "N/A")
        rating  = show.get("rating", {}).get("average") or "N/A"
        runtime = show.get("runtime") or "N/A"
        summary = _strip_html(show.get("summary", ""))
        network = (show.get("network") or {}).get("name") or (show.get("webChannel") or {}).get("name") or "N/A"
        text = (
            f"📺 <b>{name}</b> ({year})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎭 Genre: {genres}\n"
            f"📡 Network: {network}\n"
            f"⭐ Rating: {rating}/10\n"
            f"⏱️ Episode: {runtime} min\n"
            f"📊 Status: {status}\n\n"
            f"📖 {summary}"
        )
        await msg.edit_text(text, parse_mode="HTML")
    else:
        await msg.edit_text(f"No results found for <b>{query}</b>.", parse_mode="HTML")


async def topseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"{i+1}. <b>{t}</b> ({y}) — {g}" for i, (t, y, g, _) in enumerate(_TOP_SERIES)]
    await update.message.reply_text(
        "📺 <b>All-Time Top TV Series</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def netflixseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"• <b>{t}</b> ({y}) — {d}" for t, y, d in _NETFLIX_HITS[:5]]
    await update.message.reply_text(
        "📺 <b>Top Netflix Series</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def hboseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"• <b>{t}</b> ({y}) — {d}" for t, y, d in _HBO_HITS[:5]]
    await update.message.reply_text(
        "📺 <b>Top HBO Series</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def amazonseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("The Boys", 2019, "Superheroes are corrupted by power and fame — dark satire."),
        ("Reacher", 2022, "Jack Reacher drifts into a small town and uncovers corruption."),
        ("The Marvelous Mrs. Maisel", 2017, "A 1950s housewife becomes a stand-up comedian."),
        ("Rings of Power", 2022, "Epic prequel to Lord of the Rings in the Second Age."),
        ("Fleabag", 2016, "Phoebe Waller-Bridge's award-winning dark British comedy."),
        ("Invincible", 2021, "An animated superhero series based on Robert Kirkman's comics."),
    ]
    t, y, d = random.choice(shows)
    await update.message.reply_text(f"📺 <b>Amazon Prime Pick</b>\n\n<b>{t}</b> ({y})\n\n{d}", parse_mode="HTML")


async def disneyseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("The Mandalorian", 2019, "A lone bounty hunter protects 'Baby Yoda' across the galaxy."),
        ("Andor", 2022, "A gritty prequel series following rebel spy Cassian Andor."),
        ("Loki", 2021, "The God of Mischief navigates the TVA and multiple timelines."),
        ("WandaVision", 2021, "Wanda and Vision live in an idyllic suburb — something is wrong."),
        ("Obi-Wan Kenobi", 2022, "Ewan McGregor returns as the iconic Jedi Master."),
        ("Shogun", 2024, "Emmy-sweeping feudal Japan epic."),
        ("What If...?", 2021, "Animated Marvel anthology exploring alternate timelines."),
    ]
    t, y, d = random.choice(shows)
    await update.message.reply_text(f"📺 <b>Disney+ Pick</b>\n\n<b>{t}</b> ({y})\n\n{d}", parse_mode="HTML")


async def seriesrec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_shows = _TOP_SERIES + [(t, y, "Mixed", d) for t, y, d in _NETFLIX_HITS]
    pick = random.choice(all_shows)
    t, y = pick[0], pick[1]
    d = pick[-1]
    await update.message.reply_text(f"📺 <b>Series Recommendation</b>\n\n<b>{t}</b> ({y})\n\n{d}", parse_mode="HTML")


async def seriesgenre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /seriesgenre <genre>\nAvailable: crime, comedy, scifi, fantasy, thriller, horror, british, drama"
        )
        return
    genre = context.args[0].lower()
    mapping = {
        "crime": _CRIME_SHOWS, "comedy": _COMEDY_SHOWS, "scifi": _SCIFI_SHOWS,
        "sci-fi": _SCIFI_SHOWS, "fantasy": None, "british": _BRITISH_SHOWS,
    }
    if genre in ("crime",):
        t, d = random.choice(_CRIME_SHOWS)
    elif genre in ("comedy",):
        t, d = random.choice(_COMEDY_SHOWS)
    elif genre in ("scifi", "sci-fi"):
        t, d = random.choice(_SCIFI_SHOWS)
    elif genre in ("fantasy",):
        t, d = random.choice(_FANTASY_SHOWS)
    elif genre == "british":
        t, d = random.choice(_BRITISH_SHOWS)
    else:
        await update.message.reply_text("Unknown genre. Try: crime, comedy, scifi, fantasy, british")
        return
    await update.message.reply_text(f"📺 <b>{genre.title()} Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def crimeshow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, d = random.choice(_CRIME_SHOWS)
    await update.message.reply_text(f"🔪 <b>Crime Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def comedyshow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, d = random.choice(_COMEDY_SHOWS)
    await update.message.reply_text(f"😂 <b>Comedy Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def scifishow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, d = random.choice(_SCIFI_SHOWS)
    await update.message.reply_text(f"🚀 <b>Sci-Fi Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def tvfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📺 <b>TV Fact</b>\n\n{random.choice(_TV_FACTS)}", parse_mode="HTML")


async def tvquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show, quote = random.choice(_TV_QUOTES)
    await update.message.reply_text(f"📺 <b>Famous TV Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{show}</b>", parse_mode="HTML")


async def tvquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qas = [
        ("Which show has the highest IMDb rating?", "Breaking Bad (9.5/10)"),
        ("How many seasons does Game of Thrones have?", "8 seasons (2011-2019)"),
        ("Who plays Walter White in Breaking Bad?", "Bryan Cranston"),
        ("What year did The Sopranos premiere?", "1999"),
        ("Which Netflix show set viewership records in 111 countries?", "Squid Game (2021)"),
        ("In which US city is The Wire set?", "Baltimore, Maryland"),
        ("Who created Black Mirror?", "Charlie Brooker"),
        ("What is the fictional paper company in The Office?", "Dunder Mifflin"),
    ]
    q, a = random.choice(qas)
    await update.message.reply_text(
        f"📺 <b>TV Quiz</b>\n\n❓ {q}\n\n<tg-spoiler>✅ {a}</tg-spoiler>",
        parse_mode="HTML"
    )


async def miniseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, ep, d = random.choice(_MINISERIES)
    await update.message.reply_text(f"📺 <b>Limited Series Pick</b>\n\n<b>{t}</b> ({ep} episodes)\n\n{d}", parse_mode="HTML")


async def docuseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Making a Murderer", "Steven Avery's wrongful conviction and retrial."),
        ("Tiger King", "The bizarre world of big cat breeding in America."),
        ("The Jinx", "Robert Durst's chilling confessions across multiple episodes."),
        ("Wild Wild Country", "The rise and fall of Bhagwan Shree Rajneesh in Oregon."),
        ("The Last Dance", "Michael Jordan and the 1997-98 Chicago Bulls championship season."),
        ("Allen v. Farrow", "The sexual abuse allegations against Woody Allen."),
        ("Don't F**k with Cats", "Internet sleuths track down an animal killer on Facebook."),
        ("Crime Scene: The Vanishing at Cecil Hotel", "The mysterious death at the infamous Los Angeles hotel."),
    ]
    t, d = random.choice(shows)
    await update.message.reply_text(f"📽️ <b>Documentary Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def animatedseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("Avatar: The Last Airbender", "A young boy must master all four elements to save the world."),
        ("BoJack Horseman", "A washed-up celebrity horse grapples with depression and addiction."),
        ("Rick and Morty", "A genius scientist and his grandson travel across universes."),
        ("Arcane", "The origin story of League of Legends champions Vi and Jinx."),
        ("Invincible", "A teenager discovers his father is the world's greatest superhero."),
        ("Attack on Titan", "Humanity fights for survival against giant humanoid creatures."),
        ("Fullmetal Alchemist: Brotherhood", "Two brothers search for the philosopher's stone."),
        ("The Simpsons", "The longest-running American animated series — 35+ seasons."),
    ]
    t, d = random.choice(shows)
    await update.message.reply_text(f"🎨 <b>Animated Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def trendingseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 <b>Trending Series</b>\n\nFor live trending shows:\n"
        "🔗 <a href='https://www.imdb.com/chart/tvmeter/'>IMDb TV Meter</a>\n"
        "🔗 <a href='https://www.rottentomatoes.com/browse/tv_series_browse/sort:popular'>Rotten Tomatoes</a>\n"
        "🔗 <a href='https://www.reelgood.com/'>Reelgood.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def classicseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("The X-Files", 1993, "FBI agents investigate supernatural cases."),
        ("Twin Peaks", 1990, "An FBI agent investigates a murder in a strange Pacific Northwest town."),
        ("Seinfeld", 1989, "A comedian navigates daily life in NYC with his neurotic friends."),
        ("The Twilight Zone", 1959, "Anthology of science fiction, fantasy, and horror."),
        ("MASH", 1972, "Surgeons cope with the horrors of the Korean War with dark humour."),
        ("Cheers", 1982, "Where everybody knows your name — a Boston bar comedy."),
        ("Star Trek: The Next Generation", 1987, "The Enterprise crew explores the galaxy in the 24th century."),
    ]
    t, y, d = random.choice(shows)
    await update.message.reply_text(f"📺 <b>Classic Series</b>\n\n<b>{t}</b> ({y})\n\n{d}", parse_mode="HTML")


async def britishseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, d = random.choice(_BRITISH_SHOWS)
    await update.message.reply_text(f"🇬🇧 <b>British Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def fantasyshow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, d = random.choice(_FANTASY_SHOWS)
    await update.message.reply_text(f"🧙 <b>Fantasy Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")


async def horrorseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shows = [
        ("The Haunting of Hill House", "A family is terrorised by ghosts in a haunted mansion."),
        ("American Horror Story", "Anthology series of terrifying scenarios in the USA."),
        ("Hannibal", "The story of cannibal psychiatrist Dr Hannibal Lecter."),
        ("Penny Dreadful", "Victorian London is plagued by supernatural creatures."),
        ("The Walking Dead", "Survivors of a zombie apocalypse fight to stay human."),
        ("Midnight Mass", "A remote island community is visited by a mysterious priest."),
        ("Archive 81", "An archivist restores damaged tapes and uncovers a dark cult."),
    ]
    t, d = random.choice(shows)
    await update.message.reply_text(f"👻 <b>Horror Series Pick</b>\n\n<b>{t}</b>\n\n{d}", parse_mode="HTML")
