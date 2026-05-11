"""
handlers/movies.py — 35 movie commands.
Uses OMDB API (optional key OMDB_API_KEY in config/env) with rich static fallback.
"""

import os
import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes

_OMDB = "https://www.omdbapi.com/"
_OMDB_KEY = os.environ.get("OMDB_API_KEY", "")

# ── Static curated data ───────────────────────────────────────────────────────

_MOVIE_QUOTES = [
    ("The Godfather", "Leave the gun. Take the cannoli."),
    ("Forrest Gump", "Life is like a box of chocolates. You never know what you gonna get."),
    ("The Dark Knight", "Why so serious?"),
    ("Titanic", "I'm the king of the world!"),
    ("Inception", "You mustn't be afraid to dream a little bigger, darling."),
    ("Interstellar", "Do not go gentle into that good night."),
    ("Pulp Fiction", "English, motherf***er, do you speak it?"),
    ("The Matrix", "There is no spoon."),
    ("Star Wars", "May the Force be with you."),
    ("The Lion King", "Hakuna Matata — it means no worries."),
    ("Avengers: Endgame", "Whatever it takes."),
    ("Gladiator", "What we do in life echoes in eternity."),
    ("Joker", "The worst part of having a mental illness is people expect you to behave as if you don't."),
    ("Shawshank Redemption", "Get busy living, or get busy dying."),
    ("Good Will Hunting", "It's not your fault."),
    ("Fight Club", "The first rule of Fight Club is: you do not talk about Fight Club."),
    ("Schindler's List", "Whoever saves one life, saves the world entire."),
    ("The Social Network", "A million dollars isn't cool. You know what's cool? A billion dollars."),
    ("Braveheart", "They may take our lives, but they'll never take our FREEDOM!"),
    ("Rocky", "It ain't about how hard you hit. It's about how hard you can get hit and keep moving forward."),
]

_MOVIE_FACTS = [
    "The original Star Wars (1977) had a budget of $11 million but grossed over $775 million worldwide.",
    "The iconic shower scene in Psycho (1960) took 7 days to film and used 70 camera setups for 45 seconds.",
    "Titanic (1997) cost more to make than the actual Titanic ship when adjusted for inflation.",
    "The role of Jack in Titanic was almost played by Matt Damon or Chris O'Donnell.",
    "Heath Ledger's Joker makeup was designed by Ledger himself using a white face paint base.",
    "The 'F' word appears 569 times in The Wolf of Wall Street — a record.",
    "Toy Story (1995) was the first fully computer-animated feature film ever made.",
    "The sound of the T-Rex roar in Jurassic Park was a baby elephant combined with an alligator and a tiger.",
    "Leonardo DiCaprio wasn't the first choice for The Revenant — Tom Hardy was originally cast as Hugh Glass.",
    "The entire Lord of the Rings trilogy was filmed simultaneously over 438 days.",
    "Audrey Hepburn's iconic little black dress in Breakfast at Tiffany's sold for $467,000 at auction.",
    "The 'Inception' horn sound is actually a slowed-down version of Édith Piaf's song 'Non, je ne regrette rien'.",
    "James Cameron spent more time researching the Titanic wreck than the actual ship was in service.",
    "Avengers: Endgame overtook Avatar as the highest-grossing film of all time with $2.797 billion.",
    "The famous 'Here's Johnny!' scene in The Shining required 127 takes to film.",
]

_BOLLYWOOD = [
    ("Dilwale Dulhania Le Jayenge", 1995, "Romance", "Shah Rukh Khan, Kajol"),
    ("3 Idiots", 2009, "Comedy/Drama", "Aamir Khan, R. Madhavan"),
    ("Dangal", 2016, "Sports Drama", "Aamir Khan, Fatima Sana Shaikh"),
    ("Lagaan", 2001, "Period Drama", "Aamir Khan, Gracy Singh"),
    ("Dil Chahta Hai", 2001, "Comedy", "Aamir Khan, Saif Ali Khan"),
    ("Zindagi Na Milegi Dobara", 2011, "Drama", "Hrithik Roshan, Farhan Akhtar"),
    ("Queen", 2014, "Drama", "Kangana Ranaut"),
    ("PK", 2014, "Comedy/Drama", "Aamir Khan, Anushka Sharma"),
    ("Bajrangi Bhaijaan", 2015, "Drama", "Salman Khan, Harshaali Malhotra"),
    ("Kabhi Khushi Kabhie Gham", 2001, "Family Drama", "Amitabh Bachchan, Shah Rukh Khan"),
    ("Mughal-E-Azam", 1960, "Historical", "Prithviraj Kapoor, Dilip Kumar"),
    ("Sholay", 1975, "Action", "Amitabh Bachchan, Dharmendra"),
    ("Taare Zameen Par", 2007, "Drama", "Aamir Khan, Darsheel Safary"),
    ("Gangs of Wasseypur", 2012, "Crime Drama", "Manoj Bajpayee, Nawazuddin Siddiqui"),
    ("Andhadhun", 2018, "Thriller", "Ayushmann Khurrana, Tabu"),
]

_HORROR = [
    ("The Shining", 1980, "A family heads to an isolated hotel where supernatural forces possess the father."),
    ("Get Out", 2017, "A young Black man uncovers a disturbing secret when visiting his girlfriend's family."),
    ("Hereditary", 2018, "A family is haunted by a terrifying presence after the death of their secretive grandmother."),
    ("A Quiet Place", 2018, "A family struggles to survive in a post-apocalyptic world inhabited by blind monsters."),
    ("It", 2017, "A shape-shifting entity preys on the children of Derry, Maine."),
    ("The Conjuring", 2013, "Paranormal investigators help a family terrorised by a dark presence in their home."),
    ("Midsommar", 2019, "A couple travels to Sweden for a festival that takes a sinister turn."),
    ("The Babadook", 2014, "A single mother discovers a mysterious book about a malevolent entity — the Babadook."),
    ("Sinister", 2012, "A true crime writer discovers a disturbing box of home movies in his new house."),
    ("Annihilation", 2018, "A biologist signs up for a secret expedition into a mysterious quarantined zone."),
]

_ACTION = [
    ("Mad Max: Fury Road", 2015, "A high-octane post-apocalyptic chase across a barren wasteland."),
    ("John Wick", 2014, "A retired hitman seeks vengeance against those who wronged him."),
    ("The Dark Knight", 2008, "Batman faces the Joker, a criminal mastermind who plunges Gotham into anarchy."),
    ("Mission: Impossible – Fallout", 2018, "Ethan Hunt races to prevent a nuclear catastrophe."),
    ("Top Gun: Maverick", 2022, "A legendary aviator returns to train a new squad of elite pilots."),
    ("Die Hard", 1988, "A cop battles terrorists in a Los Angeles skyscraper on Christmas Eve."),
    ("The Raid: Redemption", 2011, "A SWAT team is trapped in a building controlled by a ruthless crime lord."),
    ("Speed", 1994, "A bus wired with a bomb must stay above 50 mph or it explodes."),
    ("Point Break", 1991, "An FBI agent goes undercover to catch a gang of surfer bank robbers."),
    ("Crouching Tiger, Hidden Dragon", 2000, "Two warriors pursue a stolen sword and a fugitive young woman."),
]

_SCIFI = [
    ("Interstellar", 2014, "Astronauts travel through a wormhole near Saturn to find a new home for humanity."),
    ("Blade Runner 2049", 2017, "A blade runner discovers a secret that threatens what's left of society."),
    ("Arrival", 2016, "A linguist works to communicate with aliens that have arrived on Earth."),
    ("The Martian", 2015, "An astronaut is stranded on Mars and must use science to survive."),
    ("2001: A Space Odyssey", 1968, "A voyage to Jupiter turns eerie when the AI controlling the ship malfunctions."),
    ("Ex Machina", 2014, "A programmer is invited to evaluate a humanoid robot with artificial intelligence."),
    ("District 9", 2009, "Aliens forced to live in slum-like conditions band together to find a way back home."),
    ("Children of Men", 2006, "In a dystopian future, a man fights to transport a miraculously pregnant woman."),
    ("Dune", 2021, "A noble family becomes embroiled in a war for a desert planet's resources."),
    ("Everything Everywhere All at Once", 2022, "A laundromat owner battles across parallel universes."),
]

_COMEDY = [
    ("The Grand Budapest Hotel", 2014, "A concierge gets caught up in the theft of a painting and a murder mystery."),
    ("Superbad", 2007, "Two best friends attempt to buy alcohol before a party — with chaotic results."),
    ("Bridesmaids", 2011, "A maid of honour spirals as her best friend's wedding approaches."),
    ("Game Night", 2018, "A group of friends' game night turns into a real murder mystery."),
    ("The Nice Guys", 2016, "A mismatched pair investigate a missing girl in 1970s Los Angeles."),
    ("Knives Out", 2019, "A detective investigates the death of a wealthy crime novelist."),
    ("What We Do in the Shadows", 2014, "A documentary crew follows vampire flatmates in New Zealand."),
    ("Hot Fuzz", 2007, "A top London cop is transferred to a seemingly perfect English village."),
    ("Shaun of the Dead", 2004, "A man and his friends face a zombie apocalypse in London."),
    ("The Big Lebowski", 1998, "A case of mistaken identity drags 'The Dude' into a madcap adventure."),
]

_THRILLER = [
    ("Parasite", 2019, "A poor family schemes to embed itself in a wealthy household."),
    ("Gone Girl", 2014, "A man becomes the prime suspect when his wife mysteriously disappears."),
    ("Prisoners", 2013, "A father takes matters into his own hands when his daughter goes missing."),
    ("Zodiac", 2007, "Investigators hunt the Zodiac Killer across San Francisco."),
    ("Memento", 2000, "A man with short-term memory loss hunts his wife's murderer."),
    ("Seven", 1995, "Two detectives track a serial killer using the seven deadly sins as his motif."),
    ("Nightcrawler", 2014, "A driven man becomes a freelance crime journalist in Los Angeles."),
    ("The Girl with the Dragon Tattoo", 2011, "A journalist investigates a decades-old disappearance."),
    ("Sicario", 2015, "An FBI agent is recruited to an elite government task force targeting a drug cartel."),
    ("No Country for Old Men", 2007, "A hunter stumbles upon a drug deal gone wrong — and a hitman on his trail."),
]

_ROMANCE = [
    ("Before Sunrise", 1995, "Two strangers spend a magical night together in Vienna."),
    ("Eternal Sunshine of the Spotless Mind", 2004, "A couple erase each other from their memories."),
    ("La La Land", 2016, "A jazz musician and an aspiring actress fall in love in Los Angeles."),
    ("500 Days of Summer", 2009, "A man reflects on his relationship with a woman who did not believe in love."),
    ("Pride and Prejudice", 2005, "Elizabeth Bennet navigates love and society in Regency England."),
    ("About Time", 2013, "A man who can travel in time uses his ability to find love."),
    ("When Harry Met Sally", 1989, "Two friends question whether men and women can just be friends."),
    ("Notting Hill", 1999, "A bookshop owner falls for a world-famous film star."),
    ("Crazy, Rich Asians", 2018, "An American-born professor meets her boyfriend's impossibly wealthy family."),
    ("Call Me by Your Name", 2017, "A passionate summer romance unfolds in 1980s northern Italy."),
]

_ANIMATION = [
    ("Spider-Man: Into the Spider-Verse", 2018, "A teen discovers he is not the only Spider-Man."),
    ("Spirited Away", 2001, "A young girl wanders into a world ruled by gods, witches and spirits."),
    ("Coco", 2017, "A young boy travels to the Land of the Dead to meet his musician ancestor."),
    ("WALL-E", 2008, "A lone robot on a post-apocalyptic Earth falls in love."),
    ("The Incredibles", 2004, "A family of superheroes struggles to live a normal suburban life."),
    ("Encanto", 2021, "A young Colombian woman must save her magical family."),
    ("Soul", 2020, "A musician has a near-death experience and questions his life's purpose."),
    ("Princess Mononoke", 1997, "A young prince becomes caught in a conflict between forest gods and humans."),
    ("Your Name", 2016, "Two teenagers discover they are inexplicably linked by swapping bodies."),
    ("Klaus", 2019, "A postman discovers a reclusive toymaker in a bleak Scandinavian town."),
]

_DOCUMENTARY = [
    ("Free Solo", 2018, "Alex Honnold attempts to free solo climb Yosemite's 3,000-foot El Capitan wall."),
    ("Won't You Be My Neighbor?", 2018, "The life and legacy of TV icon Fred Rogers."),
    ("13th", 2016, "An exploration of race, justice and mass incarceration in the United States."),
    ("Searching for Sugar Man", 2012, "Two South Africans search for a mysterious 1970s American musician."),
    ("Planet Earth II", 2016, "A landmark nature documentary series by Sir David Attenborough."),
    ("The Act of Killing", 2012, "Former Indonesian death squad leaders re-enact their mass killings."),
    ("Icarus", 2017, "A filmmaker uncovers a vast doping scandal in Russian sports."),
    ("Amy", 2015, "An intimate portrait of the life and career of Amy Winehouse."),
    ("Man on Wire", 2008, "Philippe Petit's thrilling wire-walk between the Twin Towers in 1974."),
    ("Jiro Dreams of Sushi", 2011, "An 85-year-old sushi master dedicates his life to perfection."),
]

_CLASSIC = [
    ("Casablanca", 1942, "Romance/Drama", "A nightclub owner must choose between love and virtue."),
    ("Citizen Kane", 1941, "Drama", "A reporter investigates the life of a media tycoon after his death."),
    ("Singin' in the Rain", 1952, "Musical", "Hollywood transitions from silent films to 'talkies'."),
    ("Rear Window", 1954, "Thriller", "A photographer believes he witnessed a murder from his apartment."),
    ("Sunset Boulevard", 1950, "Drama", "A faded silent-film star hopes to return to the big screen."),
    ("12 Angry Men", 1957, "Drama", "Twelve jurors deliberate the fate of a young man on trial for murder."),
    ("Vertigo", 1958, "Thriller", "A detective with a fear of heights is hired to follow a woman."),
    ("Some Like It Hot", 1959, "Comedy", "Two musicians witness a murder and flee disguised as women."),
    ("The Bridge on the River Kwai", 1957, "War", "British POWs build a railway bridge for their Japanese captors."),
    ("Ben-Hur", 1959, "Epic", "A Jewish prince seeks revenge against his childhood friend, now a Roman official."),
]

_MARVEL_ORDER = [
    "1. Iron Man (2008)", "2. The Incredible Hulk (2008)", "3. Iron Man 2 (2010)",
    "4. Thor (2011)", "5. Captain America: The First Avenger (2011)", "6. The Avengers (2012)",
    "7. Iron Man 3 (2013)", "8. Thor: The Dark World (2013)", "9. Captain America: The Winter Soldier (2014)",
    "10. Guardians of the Galaxy (2014)", "11. Avengers: Age of Ultron (2015)", "12. Ant-Man (2015)",
    "13. Captain America: Civil War (2016)", "14. Doctor Strange (2016)", "15. Guardians of the Galaxy Vol. 2 (2017)",
    "16. Spider-Man: Homecoming (2017)", "17. Thor: Ragnarok (2017)", "18. Black Panther (2018)",
    "19. Avengers: Infinity War (2018)", "20. Ant-Man and the Wasp (2018)", "21. Captain Marvel (2019)",
    "22. Avengers: Endgame (2019)", "23. Spider-Man: Far From Home (2019)",
    "24. Black Widow (2021)", "25. Shang-Chi (2021)", "26. Eternals (2021)",
    "27. Spider-Man: No Way Home (2021)", "28. Doctor Strange in the Multiverse of Madness (2022)",
    "29. Thor: Love and Thunder (2022)", "30. Black Panther: Wakanda Forever (2022)",
    "31. Guardians of the Galaxy Vol. 3 (2023)", "32. The Marvels (2023)",
]

_DC_ORDER = [
    "1. Man of Steel (2013)", "2. Batman v Superman: Dawn of Justice (2016)",
    "3. Suicide Squad (2016)", "4. Wonder Woman (2017)", "5. Justice League (2017)",
    "6. Aquaman (2018)", "7. Shazam! (2019)", "8. Birds of Prey (2020)",
    "9. Wonder Woman 1984 (2020)", "10. Zack Snyder's Justice League (2021)",
    "11. The Suicide Squad (2021)", "12. Black Adam (2022)", "13. Shazam! Fury of the Gods (2023)",
    "14. The Flash (2023)", "15. Blue Beetle (2023)", "16. Aquaman and the Lost Kingdom (2023)",
    "17. Superman (2025 — DCU reboot)",
]

_EMOJI_MOVIES = [
    ("🦁👑", "The Lion King"),
    ("🕷️👦🏙️", "Spider-Man"),
    ("🧊👸❄️", "Frozen"),
    ("🚢💔🌊", "Titanic"),
    ("🌌⭐🚀", "Star Wars"),
    ("🦇🃏🌃", "The Dark Knight"),
    ("🔫💼🧳🚗", "Pulp Fiction"),
    ("🧙‍♂️💍🌋", "The Lord of the Rings"),
    ("🐟🔵💙", "Finding Nemo"),
    ("👻🏡🔦", "Ghostbusters"),
    ("🦍🏙️✈️", "King Kong"),
    ("🧠💊🔴🔵", "The Matrix"),
    ("🎭🃏😂", "Joker"),
    ("🏝️🦕🦖", "Jurassic Park"),
    ("👨‍🚀🌎🔴🌍", "Interstellar"),
]

_FILM_FACTS = [
    "The first feature-length film ever made was 'The Story of the Kelly Gang' (1906) from Australia.",
    "More than 50,000 films have been produced worldwide in cinema history.",
    "The average Hollywood blockbuster takes about 3 years from concept to release.",
    "The Hollywood sign originally read 'HOLLYWOODLAND' — an advertisement for a real estate development.",
    "Charlie Chaplin once lost a Charlie Chaplin look-alike contest.",
    "The Wilhelm Scream has appeared in over 400 films and TV shows since 1951.",
    "Pixar almost deleted Toy Story 2 during production — a backup saved the film.",
    "The sound of lightsabers in Star Wars was created by combining a TV's idle hum with a film projector motor.",
    "Stanley Kubrick famously used real starlight for candlelit scenes in Barry Lyndon (1975).",
    "The most Oscars ever won by a single film is 11 — tied by Ben-Hur, Titanic, and The Lord of the Rings.",
]


# ── OMDB helper ───────────────────────────────────────────────────────────────

async def _omdb(params: dict) -> dict | None:
    if not _OMDB_KEY:
        return None
    try:
        params["apikey"] = _OMDB_KEY
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(_OMDB, params=params)
            if r.status_code == 200:
                data = r.json()
                if data.get("Response") == "True":
                    return data
    except Exception:
        pass
    return None


def _movie_card(d: dict) -> str:
    return (
        f"🎬 <b>{d.get('Title', 'N/A')}</b> ({d.get('Year', 'N/A')})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎭 <b>Genre:</b> {d.get('Genre', 'N/A')}\n"
        f"⭐ <b>IMDb:</b> {d.get('imdbRating', 'N/A')}/10  ({d.get('imdbVotes', 'N/A')} votes)\n"
        f"🏆 <b>Awards:</b> {d.get('Awards', 'N/A')}\n"
        f"🎥 <b>Director:</b> {d.get('Director', 'N/A')}\n"
        f"🎭 <b>Cast:</b> {d.get('Actors', 'N/A')}\n"
        f"⏱️ <b>Runtime:</b> {d.get('Runtime', 'N/A')}\n\n"
        f"📖 {d.get('Plot', 'No synopsis available.')}"
    )


# ── Commands ──────────────────────────────────────────────────────────────────

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <title>\nExample: /movie Inception")
        return
    title = " ".join(context.args)
    msg   = await update.message.reply_text(f"🔍 Searching for <b>{title}</b>...", parse_mode="HTML")
    data  = await _omdb({"t": title, "plot": "full", "type": "movie"})
    if data:
        poster = data.get("Poster", "")
        card   = _movie_card(data)
        if poster and poster != "N/A":
            try:
                await msg.delete()
                await update.message.reply_photo(photo=poster, caption=card, parse_mode="HTML")
                return
            except Exception:
                pass
        await msg.edit_text(card, parse_mode="HTML")
    else:
        await msg.edit_text(
            f"🎬 Could not find <b>{title}</b>.\n\n"
            "💡 Tip: Set <code>OMDB_API_KEY</code> in config for live movie search.\n"
            "Get a free key at <a href='https://www.omdbapi.com/apikey.aspx'>omdbapi.com</a>",
            parse_mode="HTML", disable_web_page_preview=True
        )


async def moviefact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎬 <b>Movie Fact</b>\n\n{random.choice(_MOVIE_FACTS)}", parse_mode="HTML")


async def moviequote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    film, quote = random.choice(_MOVIE_QUOTES)
    await update.message.reply_text(f"🎬 <b>Famous Movie Quote</b>\n\n<i>"{quote}"</i>\n\n— <b>{film}</b>", parse_mode="HTML")


async def movieline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    film, quote = random.choice(_MOVIE_QUOTES)
    await update.message.reply_text(f"🗣️ <b>Iconic Line</b>\n\n<i>"{quote}"</i>\n— <b>{film}</b>", parse_mode="HTML")


async def bollywood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, g, cast = random.choice(_BOLLYWOOD)
    await update.message.reply_text(
        f"🎬 <b>Bollywood Pick</b>\n\n<b>{t}</b> ({y})\n🎭 Genre: {g}\n👥 Cast: {cast}",
        parse_mode="HTML"
    )


async def bollywood_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"{i+1}. <b>{t}</b> ({y}) — {g}" for i, (t, y, g, _) in enumerate(_BOLLYWOOD[:10])]
    await update.message.reply_text(
        "🎬 <b>Top 10 Bollywood Films</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def hollywood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hits = [
        ("Shawshank Redemption", 1994, "Drama"),("Forrest Gump", 1994, "Drama"),
        ("The Silence of the Lambs", 1991, "Thriller"),("Schindler's List", 1993, "Drama"),
        ("Pulp Fiction", 1994, "Crime"),("Goodfellas", 1990, "Crime"),
        ("Fight Club", 1999, "Drama"),("The Matrix", 1999, "Sci-Fi"),
        ("American Beauty", 1999, "Drama"),("The Sixth Sense", 1999, "Thriller"),
    ]
    t, y, g = random.choice(hits)
    await update.message.reply_text(f"🎬 <b>Hollywood Pick</b>\n\n<b>{t}</b> ({y})\n🎭 Genre: {g}", parse_mode="HTML")


async def hollywood_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hits = [
        ("The Shawshank Redemption", 1994),("The Godfather", 1972),
        ("The Dark Knight", 2008),("The Godfather Part II", 1974),
        ("12 Angry Men", 1957),("Schindler's List", 1993),
        ("The Lord of the Rings: The Return of the King", 2003),("Pulp Fiction", 1994),
        ("The Good, the Bad and the Ugly", 1966),("Fight Club", 1999),
    ]
    lines = [f"{i+1}. <b>{t}</b> ({y})" for i, (t, y) in enumerate(hits)]
    await update.message.reply_text(
        "🎬 <b>Top 10 Hollywood Films (IMDb)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def kollywood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    films = [
        ("Vikram", 2022, "Kamal Haasan, Fahadh Faasil"),
        ("Enthiran", 2010, "Rajinikanth, Aishwarya Rai"),
        ("Baahubali: The Beginning", 2015, "Prabhas, Rana Daggubati"),
        ("Jai Bhim", 2021, "Suriya, Lijomol Jose"),
        ("Vada Chennai", 2018, "Dhanush, Aishwarya Rajesh"),
        ("96", 2018, "Vijay Sethupathi, Trisha"),
        ("Kaithi", 2019, "Karthi"),
        ("Super Deluxe", 2019, "Vijay Sethupathi, Fahadh Faasil"),
        ("Roja", 1992, "Arvind Swamy, Madhoo"),
        ("Anniyan", 2005, "Vikram, Sadha"),
    ]
    t, y, c = random.choice(films)
    await update.message.reply_text(f"🎬 <b>Kollywood (Tamil) Pick</b>\n\n<b>{t}</b> ({y})\n👥 Cast: {c}", parse_mode="HTML")


async def tollywood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    films = [
        ("Baahubali 2: The Conclusion", 2017, "Prabhas"),
        ("RRR", 2022, "NT Rama Rao Jr., Ram Charan"),
        ("Arjun Reddy", 2017, "Vijay Deverakonda"),
        ("Pushpa: The Rise", 2021, "Allu Arjun"),
        ("Magadheera", 2009, "Ram Charan, Kajal Aggarwal"),
        ("Khaleja", 2010, "Mahesh Babu"),
        ("Eega", 2012, "Nani, Samantha Ruth Prabhu"),
        ("Oh! Baby", 2019, "Samantha Ruth Prabhu"),
        ("Mahanati", 2018, "Keerthy Suresh"),
        ("Sye Raa Narasimha Reddy", 2019, "Chiranjeevi"),
    ]
    t, y, c = random.choice(films)
    await update.message.reply_text(f"🎬 <b>Tollywood (Telugu) Pick</b>\n\n<b>{t}</b> ({y})\n👥 Cast: {c}", parse_mode="HTML")


async def horrorfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_HORROR)
    await update.message.reply_text(f"👻 <b>Horror Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def comedyfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_COMEDY)
    await update.message.reply_text(f"😂 <b>Comedy Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def actionfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_ACTION)
    await update.message.reply_text(f"💥 <b>Action Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def scififilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_SCIFI)
    await update.message.reply_text(f"🚀 <b>Sci-Fi Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def thrillerfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_THRILLER)
    await update.message.reply_text(f"🔪 <b>Thriller Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def romancefilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_ROMANCE)
    await update.message.reply_text(f"💕 <b>Romance Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def animationfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_ANIMATION)
    await update.message.reply_text(f"🎨 <b>Animation Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def docfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, p = random.choice(_DOCUMENTARY)
    await update.message.reply_text(f"📽️ <b>Documentary Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def classicfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t, y, g, p = random.choice(_CLASSIC)
    await update.message.reply_text(f"🎞️ <b>Classic Film</b>\n\n<b>{t}</b> ({y})\n🎭 Genre: {g}\n\n{p}", parse_mode="HTML")


async def movierec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_films = _ACTION + _SCIFI + _THRILLER + _COMEDY + _ROMANCE + _ANIMATION
    t, y, p = random.choice(all_films)
    await update.message.reply_text(f"🎬 <b>Movie Recommendation</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")


async def marvelorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chunk1 = "\n".join(_MARVEL_ORDER[:16])
    await update.message.reply_text(
        f"🦸 <b>Marvel MCU Watch Order (Part 1)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{chunk1}",
        parse_mode="HTML"
    )
    chunk2 = "\n".join(_MARVEL_ORDER[16:])
    await update.message.reply_text(
        f"🦸 <b>Marvel MCU Watch Order (Part 2)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{chunk2}",
        parse_mode="HTML"
    )


async def dcorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = "\n".join(_DC_ORDER)
    await update.message.reply_text(
        f"🦇 <b>DC Extended Universe Watch Order</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{lines}",
        parse_mode="HTML"
    )


async def movieguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojis, answer = random.choice(_EMOJI_MOVIES)
    await update.message.reply_text(
        f"🎬 <b>Guess the Movie!</b>\n\n{emojis}\n\n<i>Type the movie name to answer!</i>\n\n"
        f"<tg-spoiler>Answer: {answer}</tg-spoiler>",
        parse_mode="HTML"
    )


async def filmschool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tips = [
        "The '180-degree rule' keeps subjects on consistent sides in scenes — breaking it creates jarring cuts.",
        "The 'rule of thirds' places key subjects at intersections of imaginary lines dividing the frame.",
        "Motivated lighting means every light source in a scene should have an in-scene justification.",
        "Foley artists create the sound effects you hear in movies using everyday objects.",
        "The 'golden ratio' is used in composition to create naturally pleasing visual balance.",
        "J-cuts and L-cuts overlap audio and video across edit points for seamless transitions.",
        "A 'dolly zoom' (Hitchcock zoom) changes focal length while moving the camera — creating a dreamlike effect.",
        "Non-diegetic sound is music/effects only the audience hears — not the characters.",
        "Three-act structure: setup (25%), confrontation (50%), resolution (25%).",
        "The 'mise-en-scène' refers to everything visible in the frame — set, lighting, actors, costumes.",
    ]
    await update.message.reply_text(f"🎓 <b>Film School Tip</b>\n\n{random.choice(tips)}", parse_mode="HTML")


async def filmoscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    winners = [
        ("2024", "Oppenheimer", "Christopher Nolan"),
        ("2023", "Everything Everywhere All at Once", "Daniel Kwan & Daniel Scheinert"),
        ("2022", "CODA", "Sian Heder"),
        ("2021", "Nomadland", "Chloe Zhao"),
        ("2020", "Parasite", "Bong Joon-ho"),
        ("2019", "Green Book", "Peter Farrelly"),
        ("2018", "The Shape of Water", "Guillermo del Toro"),
        ("2017", "Moonlight", "Barry Jenkins"),
        ("2016", "Spotlight", "Tom McCarthy"),
        ("2015", "Birdman", "Alejandro G. Inarritu"),
    ]
    lines = [f"🏆 <b>{y}</b> — {f} <i>({d})</i>" for y, f, d in winners]
    await update.message.reply_text(
        "🏆 <b>Recent Best Picture Oscar Winners</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


async def filmscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = [
        ("Hans Zimmer", "Inception, Interstellar, The Dark Knight, Gladiator"),
        ("John Williams", "Star Wars, Indiana Jones, Schindler's List, Jurassic Park"),
        ("Ennio Morricone", "The Good the Bad and the Ugly, Cinema Paradiso"),
        ("Howard Shore", "The Lord of the Rings trilogy"),
        ("Bernard Herrmann", "Psycho, Vertigo, Taxi Driver"),
        ("Jonny Greenwood", "There Will Be Blood, Spencer, The Power of the Dog"),
        ("Michael Giacchino", "Up, Coco, Doctor Strange"),
        ("Alexandre Desplat", "The Shape of Water, The Grand Budapest Hotel"),
        ("Ryuichi Sakamoto", "Merry Christmas Mr. Lawrence, The Last Emperor"),
        ("Jerry Goldsmith", "Planet of the Apes, Chinatown, Alien"),
    ]
    composer, films = random.choice(scores)
    await update.message.reply_text(
        f"🎵 <b>Legendary Film Composer</b>\n\n<b>{composer}</b>\n\nKnown for: {films}",
        parse_mode="HTML"
    )


async def filmtrend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 <b>Trending in Cinema</b>\n\nFor live box office and trending data:\n"
        "🔗 <a href='https://www.boxofficemojo.com/'>Box Office Mojo</a>\n"
        "🔗 <a href='https://www.rottentomatoes.com/browse/movies_in_theaters/'>Rotten Tomatoes</a>\n"
        "🔗 <a href='https://letterboxd.com/films/popular/this/week/'>Letterboxd Weekly</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )


async def actorinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /actorinfo <name>\nExample: /actorinfo Tom Hanks")
        return
    name = " ".join(context.args)
    msg  = await update.message.reply_text(f"🔍 Searching for <b>{name}</b>...", parse_mode="HTML")
    data = await _omdb({"s": name, "type": "movie"})
    if data and data.get("Search"):
        films = data["Search"][:5]
        lines = [f"• {f['Title']} ({f['Year']})" for f in films]
        await msg.edit_text(
            f"🎭 <b>{name}</b>\n\nMovies found:\n" + "\n".join(lines),
            parse_mode="HTML"
        )
    else:
        known = {
            "tom hanks": "Forrest Gump, Cast Away, Philadelphia, Saving Private Ryan, The Terminal",
            "leonardo dicaprio": "Titanic, Inception, The Revenant, The Wolf of Wall Street, Shutter Island",
            "meryl streep": "The Devil Wears Prada, Sophie's Choice, Kramer vs. Kramer, The Iron Lady",
            "denzel washington": "Training Day, Malcolm X, Glory, Man on Fire, The Equalizer",
        }
        info = known.get(name.lower(), "Set OMDB_API_KEY for live actor data.")
        await msg.edit_text(f"🎭 <b>{name}</b>\n\nNotable films: {info}", parse_mode="HTML")


async def moviedb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /moviedb <title>")
        return
    title = " ".join(context.args)
    data  = await _omdb({"t": title, "plot": "full"})
    if data:
        await update.message.reply_text(_movie_card(data), parse_mode="HTML")
    else:
        await update.message.reply_text(
            f"No data found for <b>{title}</b>. Try setting <code>OMDB_API_KEY</code>.",
            parse_mode="HTML"
        )


async def movieyear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /movieyear <year>\nExample: /movieyear 1994")
        return
    year = context.args[0]
    picks = {
        "1994": ["The Shawshank Redemption", "Pulp Fiction", "Forrest Gump", "The Lion King", "Speed"],
        "1999": ["Fight Club", "The Matrix", "American Beauty", "The Sixth Sense", "The Green Mile"],
        "2008": ["The Dark Knight", "WALL-E", "Slumdog Millionaire", "Iron Man", "Gran Torino"],
        "2010": ["Inception", "The Social Network", "Toy Story 3", "Black Swan", "The King's Speech"],
        "2019": ["Parasite", "Joker", "1917", "Avengers: Endgame", "Once Upon a Time in Hollywood"],
    }
    films = picks.get(year, [])
    if films:
        lines = "\n".join(f"• <b>{f}</b>" for f in films)
        await update.message.reply_text(f"🎬 <b>Best of {year}</b>\n\n{lines}", parse_mode="HTML")
    else:
        data = await _omdb({"s": "movie", "y": year, "type": "movie"})
        if data and data.get("Search"):
            lines = "\n".join(f"• <b>{f['Title']}</b>" for f in data["Search"][:5])
            await update.message.reply_text(f"🎬 <b>Movies from {year}</b>\n\n{lines}", parse_mode="HTML")
        else:
            await update.message.reply_text(f"No curated list for {year}. Try a popular year like 1994, 1999, 2008.")


async def filmgenre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /filmgenre <genre>\n\nAvailable: horror, comedy, action, scifi, thriller, romance, animation, documentary, classic"
        )
        return
    genre = context.args[0].lower()
    mapping = {
        "horror": _HORROR, "comedy": _COMEDY, "action": _ACTION,
        "scifi": _SCIFI, "sci-fi": _SCIFI, "thriller": _THRILLER,
        "romance": _ROMANCE, "animation": _ANIMATION, "documentary": _DOCUMENTARY,
    }
    picks = mapping.get(genre)
    if picks:
        t, y, p = random.choice(picks)
        await update.message.reply_text(f"🎬 <b>{genre.title()} Pick</b>\n\n<b>{t}</b> ({y})\n\n{p}", parse_mode="HTML")
    elif genre == "classic":
        t, y, g, p = random.choice(_CLASSIC)
        await update.message.reply_text(f"🎞️ <b>Classic Film</b>\n\n<b>{t}</b> ({y})\n🎭 {g}\n\n{p}", parse_mode="HTML")
    else:
        await update.message.reply_text(f"Unknown genre '{genre}'. Try: horror, comedy, action, scifi, thriller, romance, animation, documentary, classic")
