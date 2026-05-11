"""
handlers/sports.py — 40 sports commands.
Uses TheSportsDB free API (demo key "3") + rich static data.
"""

import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes

_TSDB = "https://www.thesportsdb.com/api/v1/json/3"

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _tsdb(endpoint: str, params: dict = None) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{_TSDB}/{endpoint}", params=params or {})
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None

# ── Static data ───────────────────────────────────────────────────────────────

_FOOTBALL_FACTS = [
    "The first official international football match was played between Scotland and England in 1872, ending 0-0.",
    "Cristiano Ronaldo and Lionel Messi have won 12 Ballon d'Or awards between them.",
    "Brazil is the only team to have played in every FIFA World Cup tournament since 1930.",
    "The fastest ever World Cup goal was scored by Hakan Sukur of Turkey in 10.8 seconds in 2002.",
    "Manchester United's Old Trafford stadium is nicknamed 'The Theatre of Dreams'.",
    "The 2010 FIFA World Cup in South Africa was the first held on the African continent.",
    "Pelé was the youngest player to score in a World Cup final, aged 17 in 1958.",
    "Bayern Munich is the most successful club in Bundesliga history with 32+ titles.",
    "The UEFA Champions League was founded in 1955 as the European Cup.",
    "Real Madrid has won the Champions League / European Cup more than any other club (14 times).",
    "The offside rule in football was first established in 1863.",
    "Messi's debut for Barcelona at age 16 lasted only 7 minutes before he was booked.",
]

_FOOTBALL_QUOTES = [
    ("Zinedine Zidane", "Football is simple, but it's difficult to play simple."),
    ("Johan Cruyff", "Playing football is very simple, but playing simple football is the hardest thing there is."),
    ("Pele", "The more difficult the victory, the greater the happiness in winning."),
    ("Bill Shankly", "Football is not a matter of life and death — it's much more important than that."),
    ("Alex Ferguson", "The best teams lose and then bounce back and sometimes win the league."),
    ("Jurgen Klopp", "Normal people can achieve extraordinary things."),
    ("Lionel Messi", "I start early, and I stay late, day after day, year after year."),
    ("Cristiano Ronaldo", "Your love makes me strong; your hate makes me unstoppable."),
    ("Arsene Wenger", "The target is always to win, and if you can't win, don't lose."),
    ("Thierry Henry", "When you do something beautiful in football, you feel pleasure."),
]

_EPL_CLUBS = [
    ("Manchester City", "Sky Blues", "Etihad Stadium"),
    ("Arsenal", "The Gunners", "Emirates Stadium"),
    ("Liverpool", "The Reds", "Anfield"),
    ("Chelsea", "The Blues", "Stamford Bridge"),
    ("Manchester United", "The Red Devils", "Old Trafford"),
    ("Tottenham Hotspur", "Spurs", "Tottenham Hotspur Stadium"),
    ("Newcastle United", "The Magpies", "St. James' Park"),
    ("Aston Villa", "The Villans", "Villa Park"),
]

_CRICKET_FACTS = [
    "Sachin Tendulkar holds the record for the most international centuries — 100 in total.",
    "The longest Test match ever played was between England and South Africa in 1939 — it lasted 14 days but was abandoned.",
    "Brian Lara holds the record for the highest individual Test score: 400* vs England in 2004.",
    "The first Cricket World Cup was held in England in 1975 and won by the West Indies.",
    "Jim Laker took 19 wickets in a single Test match against Australia in 1956 — still the record.",
    "MS Dhoni is the only captain to win all three major ICC trophies: World Cup, Champions Trophy, and World Twenty20.",
    "The Ashes series between England and Australia dates back to 1882.",
    "Muttiah Muralitharan holds the record for most Test wickets — 800.",
    "The highest team total in Test cricket is 952/6 by Sri Lanka vs India in 1997.",
    "Shane Warne's 'Ball of the Century' to Mike Gatting in 1993 is considered the greatest delivery ever bowled.",
]

_TENNIS_FACTS = [
    "Novak Djokovic holds the record for most Grand Slam singles titles with 24.",
    "Serena Williams won 23 Grand Slam singles titles, the most by any player in the Open Era.",
    "The first Wimbledon Championship was played in 1877 with only 22 players.",
    "Rafael Nadal won the French Open 14 times — an unmatched record at a single Grand Slam.",
    "The longest Wimbledon match lasted 11 hours and 5 minutes (Isner vs Mahut, 2010).",
    "Roger Federer spent 310 weeks at number one in the ATP rankings.",
    "Tennis was originally called 'lawn tennis' when it was introduced in England in the 1870s.",
    "Margaret Court holds the all-time record for Grand Slam titles with 24.",
]

_F1_FACTS = [
    "Michael Schumacher and Lewis Hamilton share the record for most F1 World Championships — 7 each.",
    "The first Formula 1 World Championship race was held at Silverstone, UK in May 1950.",
    "Ayrton Senna is considered the greatest Formula 1 driver of all time by many fans and experts.",
    "The Monaco Grand Prix is the slowest circuit on the F1 calendar but the most prestigious.",
    "Red Bull Racing holds the record for the most consecutive Constructor Championship wins (2010-2013, 2022-2023).",
    "The fastest pit stop in F1 history is 1.80 seconds, set by Red Bull Racing in 2023.",
    "Nigel Mansell set the record for most points scored in a single F1 season (without winning the championship) in 1991.",
    "The F1 car can accelerate from 0 to 160 km/h and brake back to 0 within 5 seconds.",
]

_NBA_FACTS = [
    "Michael Jordan is widely considered the greatest basketball player of all time — 6 NBA titles, 6 Finals MVPs.",
    "LeBron James holds the record for most career points in NBA history with over 38,000 points.",
    "The Boston Celtics have won the most NBA Championships with 17 titles.",
    "Wilt Chamberlain scored 100 points in a single NBA game on March 2, 1962.",
    "The NBA was founded in New York City on June 6, 1946 as the BAA (Basketball Association of America).",
    "Stephen Curry holds the record for most three-pointers made in a single season.",
    "Kareem Abdul-Jabbar held the all-time NBA scoring record for 38 years before LeBron surpassed it.",
]

_SPORT_QUOTES = [
    ("Muhammad Ali", "Float like a butterfly, sting like a bee."),
    ("Michael Jordan", "I can accept failure. Everyone fails at something. But I can't accept not trying."),
    ("Serena Williams", "A champion is defined not by their wins but by how they can recover when they fall."),
    ("Usain Bolt", "Easy is not a option... No days off... Never Quit... Be Fearless."),
    ("Roger Federer", "There is no way around the hard work. Embrace it."),
    ("Tiger Woods", "No matter how good you get, you can always get better. And that's the exciting part."),
    ("Sachin Tendulkar", "Cricket is my religion and winning is my god."),
    ("Ayrton Senna", "To survive in grand prix racing, you need to be afraid. Fear is an important feeling."),
    ("Mia Hamm", "Somewhere behind the athlete you've become is the little girl who fell in love with the game."),
    ("Vince Lombardi", "Winning isn't everything, it's the only thing."),
]

_SPORT_FACTS = [
    "The Olympic Games originated in ancient Greece around 776 BC as a religious festival.",
    "The Tour de France cycling race covers approximately 3,500 km over 21 stages.",
    "A standard marathon is 26.2 miles (42.195 km) — based on a Greek soldier's legendary run.",
    "Golf is the only sport to have been played on the Moon (by Alan Shepard in 1971).",
    "The first modern Olympic Games were held in Athens, Greece in 1896.",
    "Boxing has been an Olympic sport since 688 BC at the ancient Games.",
    "Synchronized swimming was introduced to the Olympics in 1984.",
    "The javelin was originally a weapon used in warfare before becoming a competitive sport.",
    "Table tennis was invented in England in the 1880s as an after-dinner parlour game.",
    "Archery was removed from the Olympics for 52 years and returned in 1972.",
]

_OLYMPIC_FACTS = [
    "Usain Bolt set the 100m world record of 9.58 seconds at the 2009 Berlin World Championships.",
    "Michael Phelps has won more Olympic medals than any athlete in history — 28 total (23 gold).",
    "The Olympic torch relay tradition started at the 1936 Berlin Olympics.",
    "The Olympic rings represent the five continents of the world — Africa, Americas, Asia, Europe, Oceania.",
    "Paris has hosted the Olympics three times: 1900, 1924, and 2024.",
    "The Olympic Games were cancelled in 1916, 1940, and 1944 due to World Wars.",
    "Jesse Owens won 4 gold medals at the 1936 Berlin Olympics, undermining Hitler's Aryan supremacy claims.",
    "Simone Biles is considered the greatest gymnast of all time with 37 Olympic and World Championship medals.",
]

_BOXING_FACTS = [
    "Muhammad Ali vs Joe Frazier's 'Thrilla in Manila' (1975) is considered the greatest boxing match ever.",
    "Floyd Mayweather Jr. retired with a perfect 50-0 record.",
    "Mike Tyson became the youngest heavyweight world champion at age 20 in 1986.",
    "The Marquess of Queensberry rules, which govern modern boxing, were established in 1867.",
    "Manny Pacquiao is the only boxer to win world championship titles in eight different weight divisions.",
]

# ── Commands ──────────────────────────────────────────────────────────────────

async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ <b>Football Hub</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "Commands:\n"
        "/footballfact — Football trivia\n"
        "/footballquote — Famous quote\n"
        "/epl — English Premier League\n"
        "/laliga — La Liga info\n"
        "/bundesliga — Bundesliga info\n"
        "/seriea_league — Serie A info\n"
        "/ucl — Champions League\n"
        "/topscorer — Top scorers all time\n"
        "/transfernews — Transfer window info\n"
        "/worldcupfact — World Cup trivia\n"
        "/footballquiz — Test your knowledge",
        parse_mode="HTML"
    )


async def footballfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"⚽ <b>Football Fact</b>\n\n{random.choice(_FOOTBALL_FACTS)}", parse_mode="HTML")


async def footballquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    person, quote = random.choice(_FOOTBALL_QUOTES)
    await update.message.reply_text(f"⚽ <b>Football Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{person}</b>", parse_mode="HTML")


async def epl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await _tsdb("search_all_leagues.php", {"c": "England", "s": "Soccer"})
    name, nick, stad = random.choice(_EPL_CLUBS)
    await update.message.reply_text(
        f"🏴 <b>English Premier League</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Random Club Spotlight:\n"
        f"🏟️ <b>{name}</b> ({nick})\n"
        f"📍 Stadium: {stad}\n\n"
        "For live tables: <a href='https://www.premierleague.com/tables'>premierleague.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def laliga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clubs = [
        ("Real Madrid", "Santiago Bernabéu", "14x Champions League"),
        ("FC Barcelona", "Camp Nou / Estadi Olímpic", "27x La Liga titles"),
        ("Atletico Madrid", "Wanda Metropolitano", "11x La Liga titles"),
        ("Sevilla FC", "Ramón Sánchez-Pizjuán", "7x UEFA Europa League"),
    ]
    name, stad, note = random.choice(clubs)
    await update.message.reply_text(
        f"🇪🇸 <b>La Liga Spotlight</b>\n\n<b>{name}</b>\n🏟️ {stad}\n🏆 {note}\n\n"
        "Live tables: <a href='https://www.laliga.com/en-GB/laliga-santander/standing'>laliga.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def bundesliga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇩🇪 <b>Bundesliga</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Most titles: <b>Bayern Munich</b> (32+)\n"
        "⚡ Highest scoring league in Europe\n"
        "🎯 Borussia Dortmund — fierce rivals of Bayern\n"
        "🔴 Bayer Leverkusen — 2023/24 unbeaten champions!\n\n"
        "Live table: <a href='https://www.bundesliga.com/en/bundesliga/table'>bundesliga.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def seriea_league(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇮🇹 <b>Serie A</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Most titles: <b>Juventus</b> (36)\n"
        "🏟️ Top clubs: Juventus, Inter Milan, AC Milan, Napoli, Roma, Lazio\n"
        "⚽ Best seasons: Ronaldo (34 goals, 2020-21), Lautaro Martinez\n\n"
        "Live table: <a href='https://www.legaseriea.it/en/serie-a/classifica'>legaseriea.it</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def ucl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 <b>UEFA Champions League</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "Most wins:\n"
        "1. 🇪🇸 Real Madrid — 14 titles\n"
        "2. 🇩🇪 AC Milan — 7 titles\n"
        "3. 🇬🇧 Liverpool — 6 titles\n"
        "4. 🇩🇪 Bayern Munich — 6 titles\n"
        "5. 🇩🇪 Barcelona — 5 titles\n\n"
        "Official: <a href='https://www.uefa.com/uefachampionsleague/'>uefa.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def topscorer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scorers = [
        ("Cristiano Ronaldo", "900+ goals", "across all competitions"),
        ("Lionel Messi", "850+ goals", "across all competitions"),
        ("Romario", "1000 goals", "claimed in career total"),
        ("Pelé", "1279 goals", "in all official matches"),
        ("Josef Bican", "805 goals", "official records"),
        ("Robert Lewandowski", "600+ goals", "across all competitions"),
        ("Gerd Muller", "735 goals", "across all competitions"),
        ("Eusébio", "733 goals", "across all competitions"),
    ]
    name, count, note = random.choice(scorers)
    await update.message.reply_text(
        f"⚽ <b>Top Scorer Spotlight</b>\n\n<b>{name}</b>\n📊 {count} ({note})",
        parse_mode="HTML"
    )


async def transfernews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 <b>Transfer Window</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "For live transfer news and rumours:\n"
        "🔗 <a href='https://www.transfermarkt.com/'>Transfermarkt</a>\n"
        "🔗 <a href='https://www.skysports.com/football/transfer-centre'>Sky Sports Transfer Centre</a>\n"
        "🔗 <a href='https://fabrizio-romano.com/'>Fabrizio Romano (Official)</a>\n\n"
        "🗓️ Transfer windows: Jan (winter) & Jun-Aug (summer)",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def worldcupfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "Brazil is the most successful team in World Cup history with 5 titles (1958, 62, 70, 94, 2002).",
        "Germany and Italy both have 4 World Cup titles each.",
        "The 1966 World Cup in England saw the trophy stolen and later found by a dog named Pickles.",
        "Just Fontaine scored 13 goals at the 1958 World Cup — still the single-tournament record.",
        "The 2014 World Cup in Brazil saw Germany defeat Brazil 7-1 in the semi-final.",
        "Uruguay won the first ever World Cup in 1930, beating Argentina 4-2 in the final.",
        "France won consecutive World Cups in 1998 (hosting) and almost in 2022 (lost to Argentina on penalties).",
    ]
    await update.message.reply_text(f"🌍 <b>World Cup Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def footballquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qas = [
        ("Which country has won the most FIFA World Cups?", "Brazil (5 titles)"),
        ("Who has scored the most Champions League goals?", "Cristiano Ronaldo (140+)"),
        ("Which stadium is known as the 'Theatre of Dreams'?", "Old Trafford, Manchester United"),
        ("What is the maximum number of players on a football pitch per side?", "11 players"),
        ("Who won the first Ballon d'Or?", "Stanley Matthews in 1956"),
        ("What year was FIFA founded?", "1904"),
        ("Which club has won the most Premier League titles?", "Manchester United (20)"),
        ("Who is the top scorer in World Cup history?", "Miroslav Klose (16 goals)"),
    ]
    q, a = random.choice(qas)
    await update.message.reply_text(
        f"⚽ <b>Football Quiz</b>\n\n❓ {q}\n\n<tg-spoiler>✅ {a}</tg-spoiler>",
        parse_mode="HTML"
    )


async def fifafact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "FIFA was founded on May 21, 1904 in Paris, France with just 7 member nations.",
        "FIFA now has 211 member associations — more than the United Nations.",
        "The FIFA World Cup is the most-watched sporting event on Earth, with 3.5+ billion viewers.",
        "FIFA introduced goal-line technology at the 2014 World Cup.",
        "The first FIFA Women's World Cup was held in 1991 in China.",
        "FIFA's Video Assistant Referee (VAR) system was introduced in 2016.",
    ]
    await update.message.reply_text(f"🌍 <b>FIFA Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def cricketfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏏 <b>Cricket Fact</b>\n\n{random.choice(_CRICKET_FACTS)}", parse_mode="HTML")


async def t20record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = [
        ("Highest individual score (T20I)", "172* by Aaron Finch, Australia vs Zimbabwe, 2018"),
        ("Highest team total (T20I)", "278/3 by Afghanistan vs Ireland, 2019"),
        ("Most T20I wickets", "Shaheen Afridi / Tim Southee — 150+"),
        ("Most T20I runs", "Virat Kohli — 4000+"),
        ("Most T20I sixes", "Chris Gayle — 550+"),
        ("Fastest T20I hundred", "David Miller — 35 balls vs Bangladesh, 2023"),
        ("Fastest T20I fifty", "Yuvraj Singh — 12 balls vs England, 2007"),
        ("Best bowling figures", "5/2 by several bowlers"),
        ("Most T20 World Cup wins", "West Indies (2), England (2)"),
    ]
    record, detail = random.choice(records)
    await update.message.reply_text(f"🏏 <b>T20 Record</b>\n\n📌 {record}\n✅ {detail}", parse_mode="HTML")


async def ipl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏏 <b>Indian Premier League (IPL)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Most titles:\n"
        "1. Mumbai Indians — 5 titles\n"
        "2. Chennai Super Kings — 5 titles\n"
        "3. Kolkata Knight Riders — 3 titles\n\n"
        "⚡ Most runs: Virat Kohli (7000+)\n"
        "🎯 Most wickets: Yuzvendra Chahal (180+)\n"
        "💰 Most expensive buy: Sam Curran — ₹18.5 crore (2023)\n\n"
        "Official: <a href='https://www.iplt20.com/'>iplt20.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def testcricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏏 <b>Test Cricket Records</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 Highest individual score: 400* — Brian Lara (2004)\n"
        "🎯 Most wickets: 800 — Muttiah Muralitharan\n"
        "🏆 Most runs: 15,921 — Sachin Tendulkar\n"
        "📍 Most 100s: 51 — Sachin Tendulkar\n"
        "🏟️ Most Tests: 168 — Sachin Tendulkar\n"
        "💥 Best bowling: 10/53 — Jim Laker vs Australia, 1956",
        parse_mode="HTML"
    )


async def odifact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "Rohit Sharma holds the record for highest ODI score: 264 vs Sri Lanka in 2014.",
        "Sachin Tendulkar is the only player to score 100 centuries in international cricket.",
        "Martin Guptill scored 237* against the West Indies in the 2015 World Cup quarter-final.",
        "The first Cricket World Cup was held in England in 1975 — won by the West Indies.",
        "India won the 2011 ODI World Cup at home, defeating Sri Lanka in the final.",
        "Pakistan is the only team to win the World Cup after being sent to bat first.",
    ]
    await update.message.reply_text(f"🏏 <b>ODI Cricket Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def cricketstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏏 <b>All-Time Cricket Stats</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Most International Runs:</b> Sachin Tendulkar — 34,357\n"
        "<b>Most International Wickets:</b> Muttiah Muralitharan — 1,347\n"
        "<b>Best Win %:</b> Australia (Test history)\n"
        "<b>Most ODI wins in a row:</b> Australia — 21 consecutive\n"
        "<b>Fastest 100 (ODI):</b> AB de Villiers — 31 balls\n"
        "<b>Highest partnership:</b> 624 — Mahela Jayawardene & Kumar Sangakkara",
        parse_mode="HTML"
    )


async def worldcup_cricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    winners = [
        (1975, "West Indies"), (1979, "West Indies"), (1983, "India"),
        (1987, "Australia"), (1992, "Pakistan"), (1996, "Sri Lanka"),
        (1999, "Australia"), (2003, "Australia"), (2007, "Australia"),
        (2011, "India"), (2015, "Australia"), (2019, "England"),
        (2023, "Australia"),
    ]
    lines = [f"🏆 <b>{y}</b> — {w}" for y, w in winners]
    await update.message.reply_text(
        "🏏 <b>Cricket World Cup Winners</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def tennis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎾 <b>Tennis Hub</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 <b>Grand Slams:</b>\n"
        "• Australian Open — Jan (hard court)\n"
        "• French Open — May/Jun (clay)\n"
        "• Wimbledon — Jun/Jul (grass)\n"
        "• US Open — Aug/Sep (hard court)\n\n"
        "👑 Most Titles:\n"
        "Men: Novak Djokovic (24) | Rafael Nadal (22) | Roger Federer (20)\n"
        "Women: Serena Williams (23) | Steffi Graf (22) | Margaret Court (24)",
        parse_mode="HTML"
    )


async def tennisnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎾 <b>Tennis News</b>\n\nFor latest tennis scores and news:\n"
        "🔗 <a href='https://www.atptour.com/'>ATP Tour</a>\n"
        "🔗 <a href='https://www.wtatennis.com/'>WTA Tour</a>\n"
        "🔗 <a href='https://www.itftennis.com/en/'>ITF</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def grandslam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slams = {
        "Australian Open": ("Novak Djokovic (10)", "Serena Williams (7)"),
        "French Open": ("Rafael Nadal (14)", "Chris Evert / Steffi Graf (7 each)"),
        "Wimbledon": ("Roger Federer (8)", "Martina Navratilova (9)"),
        "US Open": ("Jimmy Connors (5)", "Serena Williams (6)"),
    }
    slam, (m_rec, w_rec) = random.choice(list(slams.items()))
    await update.message.reply_text(
        f"🎾 <b>{slam} Records</b>\n\n"
        f"Men's record: {m_rec}\n"
        f"Women's record: {w_rec}",
        parse_mode="HTML"
    )


async def tennisrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎾 <b>ATP/WTA Rankings</b>\n\nFor live rankings:\n"
        "🔗 <a href='https://www.atptour.com/en/rankings/singles'>ATP Singles</a>\n"
        "🔗 <a href='https://www.wtatennis.com/rankings/singles'>WTA Singles</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def f1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏎️ <b>Formula 1</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Most Championships:\n"
        "7x: Michael Schumacher, Lewis Hamilton\n"
        "4x: Sebastian Vettel\n"
        "3x: Ayrton Senna, Jack Brabham, Niki Lauda, Nelson Piquet, Alain Prost\n\n"
        "🏎️ Most wins: Lewis Hamilton (103+)\n"
        "🎯 Most poles: Lewis Hamilton (100+)\n\n"
        "Live standings: <a href='https://www.formula1.com/en/results.html'>formula1.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def f1fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏎️ <b>F1 Fact</b>\n\n{random.choice(_F1_FACTS)}", parse_mode="HTML")


async def f1driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drivers = [
        ("Max Verstappen", "Red Bull", "3x World Champion (2021-2023)"),
        ("Lewis Hamilton", "Mercedes/Ferrari", "7x World Champion, 103+ wins"),
        ("Charles Leclerc", "Ferrari", "2x Grand Prix winner, 2019-"),
        ("Lando Norris", "McLaren", "First win: Miami 2024"),
        ("Fernando Alonso", "Aston Martin", "2x World Champion (2005-2006)"),
        ("Carlos Sainz", "Williams", "Multiple race wins"),
        ("George Russell", "Mercedes", "British driver, consistent podiums"),
        ("Sergio Perez", "Red Bull", "2022-2023 World Championship runner-up"),
    ]
    name, team, note = random.choice(drivers)
    await update.message.reply_text(
        f"🏎️ <b>F1 Driver Spotlight</b>\n\n<b>{name}</b>\n🏎️ Team: {team}\n📊 {note}",
        parse_mode="HTML"
    )


async def nba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏀 <b>NBA</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Most Championships:\n"
        "17x: Boston Celtics\n"
        "17x: Los Angeles Lakers\n"
        "6x: Chicago Bulls (all with Michael Jordan)\n\n"
        "👑 All-time leaders:\n"
        "Points: LeBron James (38,000+)\n"
        "Assists: John Stockton (15,806)\n"
        "Rebounds: Wilt Chamberlain (23,924)\n\n"
        "Live scores: <a href='https://www.nba.com/'>nba.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def basketballfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏀 <b>Basketball Fact</b>\n\n{random.choice(_NBA_FACTS)}", parse_mode="HTML")


async def boxing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥊 <b>Boxing</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏆 Legends: Muhammad Ali, Mike Tyson, Floyd Mayweather, Manny Pacquiao, Sugar Ray Leonard\n\n"
        "/boxingfact — Boxing trivia\n\n"
        "Live news: <a href='https://www.espn.com/boxing/'>ESPN Boxing</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def boxingfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🥊 <b>Boxing Fact</b>\n\n{random.choice(_BOXING_FACTS)}", parse_mode="HTML")


async def ufc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥋 <b>UFC / MMA</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "👑 Legends: Conor McGregor, Khabib Nurmagomedov, Jon Jones, Georges St-Pierre, Amanda Nunes\n\n"
        "Most title defences: Jon Jones (14)\n"
        "Most wins: Jim Miller, Donald Cerrone (36+)\n\n"
        "Official: <a href='https://www.ufc.com/'>ufc.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def olympicfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏅 <b>Olympic Fact</b>\n\n{random.choice(_OLYMPIC_FACTS)}", parse_mode="HTML")


async def olympicrecord(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = [
        ("Most Olympic gold medals", "Michael Phelps — 23 gold medals"),
        ("Most Olympic medals total", "Michael Phelps — 28 medals"),
        ("Fastest 100m (Olympic)", "Usain Bolt — 9.63s (London 2012)"),
        ("Highest pole vault", "Armand Duplantis — 6.25m (2024)"),
        ("Longest long jump", "Bob Beamon — 8.90m (Mexico 1968, stood for 23 years)"),
        ("Most Gymnastics medals", "Larissa Latynina — 18 medals (1956-1964)"),
        ("Youngest Olympic champion", "Marjorie Gestring — 13 years old (1936)"),
        ("Most Olympic host cities", "Paris — 3 times (1900, 1924, 2024)"),
    ]
    record, holder = random.choice(records)
    await update.message.reply_text(f"🏅 <b>Olympic Record</b>\n\n📌 {record}\n✅ {holder}", parse_mode="HTML")


async def sportquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    person, quote = random.choice(_SPORT_QUOTES)
    await update.message.reply_text(f"🏅 <b>Sports Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{person}</b>", parse_mode="HTML")


async def sportfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏅 <b>Sports Fact</b>\n\n{random.choice(_SPORT_FACTS)}", parse_mode="HTML")


async def golfnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "Tiger Woods won 15 major championships, 2nd only to Jack Nicklaus (18).",
        "A golf ball has between 300 and 500 dimples — they reduce air drag and help the ball fly further.",
        "The Masters Tournament has been played at Augusta National since 1934.",
        "St Andrews Old Course in Scotland is considered the 'home of golf' — dating back to 1552.",
        "Rory McIlroy won his first major at the 2011 US Open, setting a record score of -16.",
    ]
    await update.message.reply_text(f"⛳ <b>Golf</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def swimfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "Michael Phelps won 8 gold medals at the 2008 Beijing Olympics — the most in a single Games.",
        "Caeleb Dressel broke Phelps's record with 5 gold medals at the 2020 Tokyo Olympics.",
        "The 50m freestyle is the fastest swimming race — averaging about 21 mph.",
        "Katie Ledecky is the most decorated female swimmer in World Championship history.",
        "Swimming became an Olympic sport at the first modern Olympics in Athens, 1896.",
    ]
    await update.message.reply_text(f"🏊 <b>Swimming Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def athleticsfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "Usain Bolt's 9.58s world record for 100m has stood since the 2009 Berlin World Championships.",
        "Eliud Kipchoge ran a marathon in 1:59:40 in 2019 — breaking the 2-hour barrier unofficially.",
        "Florence Griffith-Joyner (Flo-Jo) set the women's 100m world record of 10.49s in 1988.",
        "The decathlon combines 10 events over two days: 100m, long jump, shot put, high jump, 400m, 110m hurdles, discus, pole vault, javelin, 1500m.",
        "Wayde van Niekerk ran a 400m world record of 43.03s at the 2016 Rio Olympics.",
    ]
    await update.message.reply_text(f"🏃 <b>Athletics Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def sport_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    birthdays = [
        ("Cristiano Ronaldo", "February 5, 1985", "Portugal"),
        ("Lionel Messi", "June 24, 1987", "Argentina"),
        ("Sachin Tendulkar", "April 24, 1973", "India"),
        ("Serena Williams", "September 26, 1981", "USA"),
        ("Usain Bolt", "August 21, 1986", "Jamaica"),
        ("Michael Jordan", "February 17, 1963", "USA"),
        ("Roger Federer", "August 8, 1981", "Switzerland"),
        ("Muhammad Ali", "January 17, 1942", "USA"),
        ("Tiger Woods", "December 30, 1975", "USA"),
        ("Lewis Hamilton", "January 7, 1985", "UK"),
    ]
    name, birthday, country = random.choice(birthdays)
    await update.message.reply_text(
        f"🎂 <b>Sports Birthday</b>\n\n<b>{name}</b>\n📅 {birthday}\n🌍 {country}",
        parse_mode="HTML"
    )


async def rugbyfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "New Zealand's All Blacks are the most successful rugby team in history with an 80%+ win rate.",
        "The Haka performed by the All Blacks is a traditional Maori war dance.",
        "Rugby was invented at Rugby School, England in 1823 when William Webb Ellis picked up the ball and ran.",
        "The Rugby World Cup trophy is named the 'Webb Ellis Cup' after the sport's legendary founder.",
        "South Africa has won the Rugby World Cup 4 times — a record (2023).",
    ]
    await update.message.reply_text(f"🏉 <b>Rugby Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")


async def wwe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💪 <b>WWE / Pro Wrestling</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "👑 Legends: The Rock, Stone Cold Steve Austin, John Cena, The Undertaker, Hulk Hogan\n\n"
        "Most WWE title reigns: John Cena (16) | Ric Flair (16)\n"
        "Longest title reign: Bob Backlund — 2,135 days (1978-1983)\n"
        "Most WrestleMania appearances: The Undertaker\n\n"
        "Official: <a href='https://www.wwe.com/'>wwe.com</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )
