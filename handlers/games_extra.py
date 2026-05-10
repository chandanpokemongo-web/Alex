"""40 extra game commands — registered in main.py but NOT in ALL_COMMANDS (already at 100 limit).
Visible to users via /help → 🎮 Games."""

import asyncio
import random
import time
import operator
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ── Shared game state ─────────────────────────────────────────────────────────
_active_games: dict[int, dict] = {}   # chat_id → quiz game state
_word_chain: dict[int, dict]   = {}   # chat_id → word chain state
_type_race:  dict[int, dict]   = {}   # chat_id → type race state

# ── Shared quiz engine ────────────────────────────────────────────────────────

async def _start_quiz(update: Update, context, question: str,
                      answer: str, accepted: list[str],
                      timeout: int = 30, hint: str = "") -> None:
    chat_id = update.effective_chat.id
    if chat_id in _active_games:
        await update.message.reply_text("⚠️ A game is already running! Finish it first.")
        return
    text = f"❓ <b>{question}</b>"
    if hint:
        text += f"\n<i>{hint}</i>"
    text += f"\n\n⏱ You have <b>{timeout} seconds</b> to answer!"
    msg = await update.message.reply_text(text, parse_mode="HTML")

    async def _timeout():
        await asyncio.sleep(timeout)
        if chat_id in _active_games:
            del _active_games[chat_id]
            try:
                await context.bot.send_message(
                    chat_id, f"⏰ Time's up! The answer was: <b>{answer}</b>",
                    parse_mode="HTML")
            except Exception:
                pass

    task = asyncio.create_task(_timeout())
    _active_games[chat_id] = {
        "answer": answer, "accepted": accepted,
        "task": task, "msg_id": msg.message_id,
    }


async def check_game_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Call from _combined_text_handler. Returns True if message was consumed."""
    if not update.message or not update.effective_user:
        return False
    chat_id  = update.effective_chat.id
    text     = (update.message.text or "").strip()
    user     = update.effective_user

    # ── Quiz answer ───────────────────────────────────────────────────────────
    game = _active_games.get(chat_id)
    if game:
        accepted = game.get("accepted", [game.get("answer", "")])
        if text.lower() in [a.lower() for a in accepted]:
            task = game.get("task")
            if task:
                task.cancel()
            del _active_games[chat_id]
            answer = game["answer"]
            await update.message.reply_text(
                f"✅ <b>{user.first_name}</b> got it!\nAnswer: <b>{answer}</b> 🎉",
                parse_mode="HTML",
            )
            return True

    # ── Word chain ────────────────────────────────────────────────────────────
    wc = _word_chain.get(chat_id)
    if wc and wc.get("active"):
        word = text.lower().strip()
        if not word.isalpha():
            return False
        last_char = wc["last_char"]
        if word[0] != last_char:
            return False  # quietly ignore wrong-start words
        used = wc["used"]
        if word in used:
            await update.message.reply_text(f'❌ "<b>{word}</b>" already used!', parse_mode="HTML")
            return True
        used.add(word)
        wc["last_char"] = word[-1]
        wc["last_user"] = user.first_name
        await update.message.reply_text(
            f"✅ <b>{user.first_name}</b>: {word}\n➡️ Next word must start with <b>{word[-1].upper()}</b>",
            parse_mode="HTML",
        )
        return True

    # ── Type race ─────────────────────────────────────────────────────────────
    tr = _type_race.get(chat_id)
    if tr and tr.get("active"):
        if text == tr["phrase"]:
            elapsed = round(time.time() - tr["start_ts"], 2)
            task = tr.get("task")
            if task:
                task.cancel()
            del _type_race[chat_id]
            await update.message.reply_text(
                f"🏁 <b>{user.first_name}</b> wins the Type Race in <b>{elapsed}s</b>! ⌨️🏆",
                parse_mode="HTML",
            )
            return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# QUESTION BANKS
# ═══════════════════════════════════════════════════════════════════════════════

_RIDDLES = [
    ("I have cities, but no houses live there. I have mountains, but no trees grow there. I have water, but no fish swim there. I have roads, but no cars drive there. What am I?", "map", ["map", "a map"]),
    ("The more you take, the more you leave behind. What am I?", "footsteps", ["footsteps", "steps", "foot steps"]),
    ("I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?", "echo", ["echo", "an echo"]),
    ("What has hands but can't clap?", "clock", ["clock", "a clock", "watch", "a watch"]),
    ("What gets wetter as it dries?", "towel", ["towel", "a towel"]),
    ("I have a head and a tail but no body. What am I?", "coin", ["coin", "a coin"]),
    ("What has teeth but can't bite?", "comb", ["comb", "a comb", "zip", "zipper"]),
    ("What runs but never walks?", "river", ["river", "a river", "water"]),
    ("What can you catch but not throw?", "cold", ["cold", "a cold"]),
    ("I'm light as a feather, yet the strongest man can't hold me for 5 minutes. What am I?", "breath", ["breath", "air", "your breath"]),
    ("What has 13 hearts but no other organs?", "deck of cards", ["deck of cards", "deck", "cards", "a deck of cards"]),
    ("What goes up but never comes down?", "age", ["age", "your age"]),
    ("What can fill a room but takes up no space?", "light", ["light", "sound"]),
    ("What has one eye but can't see?", "needle", ["needle", "a needle"]),
    ("What is always in front of you but can't be seen?", "future", ["future", "the future"]),
]

_FLAGS = [
    ("🇮🇳", "india", ["india"]),
    ("🇯🇵", "japan", ["japan"]),
    ("🇧🇷", "brazil", ["brazil"]),
    ("🇫🇷", "france", ["france"]),
    ("🇩🇪", "germany", ["germany"]),
    ("🇨🇳", "china", ["china"]),
    ("🇺🇸", "united states", ["usa", "united states", "america", "us"]),
    ("🇬🇧", "united kingdom", ["uk", "united kingdom", "britain", "england"]),
    ("🇰🇷", "south korea", ["south korea", "korea"]),
    ("🇷🇺", "russia", ["russia"]),
    ("🇮🇹", "italy", ["italy"]),
    ("🇦🇺", "australia", ["australia"]),
    ("🇨🇦", "canada", ["canada"]),
    ("🇲🇽", "mexico", ["mexico"]),
    ("🇸🇦", "saudi arabia", ["saudi arabia", "saudi"]),
    ("🇵🇰", "pakistan", ["pakistan"]),
    ("🇧🇩", "bangladesh", ["bangladesh"]),
    ("🇦🇷", "argentina", ["argentina"]),
    ("🇳🇬", "nigeria", ["nigeria"]),
    ("🇪🇬", "egypt", ["egypt"]),
    ("🇹🇭", "thailand", ["thailand"]),
    ("🇳🇱", "netherlands", ["netherlands", "holland"]),
    ("🇸🇪", "sweden", ["sweden"]),
    ("🇳🇴", "norway", ["norway"]),
    ("🇵🇭", "philippines", ["philippines"]),
]

_CAPITALS = [
    ("France", "paris", ["paris"]),
    ("Japan", "tokyo", ["tokyo"]),
    ("Germany", "berlin", ["berlin"]),
    ("Australia", "canberra", ["canberra"]),
    ("Brazil", "brasilia", ["brasilia", "brasília"]),
    ("Canada", "ottawa", ["ottawa"]),
    ("India", "new delhi", ["new delhi", "delhi"]),
    ("China", "beijing", ["beijing"]),
    ("Russia", "moscow", ["moscow"]),
    ("USA", "washington dc", ["washington dc", "washington d.c.", "washington"]),
    ("UK", "london", ["london"]),
    ("Italy", "rome", ["rome"]),
    ("Spain", "madrid", ["madrid"]),
    ("South Korea", "seoul", ["seoul"]),
    ("Pakistan", "islamabad", ["islamabad"]),
    ("Bangladesh", "dhaka", ["dhaka"]),
    ("Argentina", "buenos aires", ["buenos aires"]),
    ("Egypt", "cairo", ["cairo"]),
    ("Nigeria", "abuja", ["abuja"]),
    ("Thailand", "bangkok", ["bangkok"]),
    ("Netherlands", "amsterdam", ["amsterdam"]),
    ("Sweden", "stockholm", ["stockholm"]),
    ("Norway", "oslo", ["oslo"]),
    ("Philippines", "manila", ["manila"]),
    ("Mexico", "mexico city", ["mexico city"]),
    ("Turkey", "ankara", ["ankara"]),
    ("Iran", "tehran", ["tehran"]),
    ("Indonesia", "jakarta", ["jakarta"]),
    ("Vietnam", "hanoi", ["hanoi"]),
    ("UAE", "abu dhabi", ["abu dhabi"]),
]

_EMOJI_MOVIES = [
    ("🦁👑", "The Lion King", ["lion king", "the lion king"]),
    ("🕷️🕸️👨", "Spider-Man", ["spider man", "spiderman", "spider-man"]),
    ("🧊👸❄️", "Frozen", ["frozen"]),
    ("🚗⚡🏁", "Cars", ["cars"]),
    ("🐟🔵🐠", "Finding Nemo", ["finding nemo", "nemo"]),
    ("🧙‍♂️💍🏔️", "Lord of the Rings", ["lord of the rings", "lotr"]),
    ("⭐🚀👽🌌", "Star Wars", ["star wars"]),
    ("🦸‍♂️🦸‍♀️🌩️🛡️", "Avengers", ["avengers"]),
    ("🎭🃏😂💚", "Joker", ["joker"]),
    ("🦇🌃🦸‍♂️", "Batman", ["batman"]),
    ("🐉🔥👸", "How to Train Your Dragon", ["how to train your dragon", "httyd"]),
    ("🧜‍♀️🌊🐠", "The Little Mermaid", ["little mermaid", "the little mermaid"]),
    ("🤖💛🚗", "Transformers", ["transformers"]),
    ("🦍🗽🌆", "King Kong", ["king kong"]),
    ("🌊🦈😱", "Jaws", ["jaws"]),
]

_FILL_BLANKS = [
    ("To be or not to be, that is the ___", "question", ["question"]),
    ("All that glitters is not ___", "gold", ["gold"]),
    ("The pen is mightier than the ___", "sword", ["sword"]),
    ("Actions speak louder than ___", "words", ["words"]),
    ("Every cloud has a silver ___", "lining", ["lining"]),
    ("Better late than ___", "never", ["never"]),
    ("Two wrongs don't make a ___", "right", ["right"]),
    ("The early bird catches the ___", "worm", ["worm"]),
    ("Where there's smoke, there's ___", "fire", ["fire"]),
    ("Don't judge a book by its ___", "cover", ["cover"]),
    ("Time is ___", "money", ["money"]),
    ("Practice makes ___", "perfect", ["perfect"]),
    ("An apple a day keeps the doctor ___", "away", ["away"]),
    ("Look before you ___", "leap", ["leap"]),
    ("The customer is always ___", "right", ["right"]),
]

_SPORT_QUIZ = [
    ("How many players are in a cricket team?", "11", ["11", "eleven"]),
    ("How many periods are in an ice hockey game?", "3", ["3", "three"]),
    ("What sport is played at Wimbledon?", "tennis", ["tennis"]),
    ("How many holes are in a standard golf course?", "18", ["18", "eighteen"]),
    ("How many players are in a basketball team on court?", "5", ["5", "five"]),
    ("Which country invented basketball?", "usa", ["usa", "united states", "america"]),
    ("How many balls in a standard cricket over?", "6", ["6", "six"]),
    ("What is the highest score in bowling?", "300", ["300"]),
    ("How long is a marathon in km?", "42.195", ["42.195", "42", "42km"]),
    ("Which country has won the most FIFA World Cups?", "brazil", ["brazil"]),
    ("How many gold medals did Usain Bolt win in the Olympics?", "8", ["8", "eight"]),
    ("What sport uses a shuttlecock?", "badminton", ["badminton"]),
    ("How many rings are on the Olympic flag?", "5", ["5", "five"]),
    ("In which sport do you do a slam dunk?", "basketball", ["basketball"]),
    ("What is the fastest serve speed in tennis called?", "ace", ["ace"]),
]

_SCIENCE_QUIZ = [
    ("What planet is closest to the Sun?", "mercury", ["mercury"]),
    ("What is the chemical symbol for gold?", "au", ["au"]),
    ("What is the chemical symbol for water?", "h2o", ["h2o"]),
    ("How many bones are in the adult human body?", "206", ["206"]),
    ("What is the speed of light in km/s (approx)?", "300000", ["300000", "300,000", "3×10^5"]),
    ("What gas do plants absorb from the air?", "carbon dioxide", ["carbon dioxide", "co2"]),
    ("What is the hardest natural substance on Earth?", "diamond", ["diamond"]),
    ("How many chromosomes do humans have?", "46", ["46"]),
    ("What is the powerhouse of the cell?", "mitochondria", ["mitochondria"]),
    ("What force keeps planets in orbit?", "gravity", ["gravity"]),
    ("What is the atomic number of oxygen?", "8", ["8", "eight"]),
    ("What is the most abundant gas in Earth's atmosphere?", "nitrogen", ["nitrogen"]),
    ("What organ produces insulin?", "pancreas", ["pancreas"]),
    ("What is the boiling point of water in Celsius?", "100", ["100", "100 degrees", "100°c"]),
    ("What type of energy does the Sun primarily produce?", "nuclear", ["nuclear", "nuclear energy", "fusion"]),
]

_GEO_QUIZ = [
    ("What is the largest continent?", "asia", ["asia"]),
    ("What is the longest river in the world?", "nile", ["nile", "nile river"]),
    ("What is the tallest mountain in the world?", "mount everest", ["everest", "mount everest"]),
    ("What is the largest ocean?", "pacific", ["pacific", "pacific ocean"]),
    ("How many continents are on Earth?", "7", ["7", "seven"]),
    ("What is the smallest country in the world?", "vatican", ["vatican", "vatican city"]),
    ("What is the largest country by area?", "russia", ["russia"]),
    ("What is the most populous country?", "india", ["india"]),
    ("What is the Sahara?", "desert", ["desert", "a desert"]),
    ("Which country has the most natural lakes?", "canada", ["canada"]),
    ("What is the capital of Australia?", "canberra", ["canberra"]),
    ("Which is the largest rainforest?", "amazon", ["amazon", "amazon rainforest"]),
    ("What is the deepest lake in the world?", "baikal", ["baikal", "lake baikal"]),
    ("What river flows through Egypt?", "nile", ["nile"]),
    ("What is the highest plateau in the world?", "tibetan plateau", ["tibet", "tibetan plateau"]),
]

_HISTORY_QUIZ = [
    ("In which year did World War 2 end?", "1945", ["1945"]),
    ("Who was the first President of the United States?", "george washington", ["george washington", "washington"]),
    ("In which year did India gain independence?", "1947", ["1947"]),
    ("Who invented the telephone?", "alexander graham bell", ["alexander graham bell", "graham bell", "bell"]),
    ("In which year did man first land on the Moon?", "1969", ["1969"]),
    ("Who was Napoleon Bonaparte?", "french emperor", ["french emperor", "emperor", "general"]),
    ("What year did the Berlin Wall fall?", "1989", ["1989"]),
    ("Who was the first female Prime Minister of the UK?", "margaret thatcher", ["thatcher", "margaret thatcher"]),
    ("In which city was the Titanic built?", "belfast", ["belfast"]),
    ("Who wrote the Communist Manifesto?", "karl marx", ["marx", "karl marx", "marx and engels"]),
    ("In which country did the Renaissance begin?", "italy", ["italy"]),
    ("Who was the last pharaoh of Egypt?", "cleopatra", ["cleopatra"]),
    ("In which year was the Eiffel Tower built?", "1889", ["1889"]),
    ("Who discovered penicillin?", "alexander fleming", ["fleming", "alexander fleming"]),
    ("What was the name of the first satellite in space?", "sputnik", ["sputnik"]),
]

_MUSIC_QUIZ = [
    ("Who is known as the 'King of Pop'?", "michael jackson", ["michael jackson", "mj", "jackson"]),
    ("Which band sang 'Bohemian Rhapsody'?", "queen", ["queen"]),
    ("Who sang 'Shape of You'?", "ed sheeran", ["ed sheeran", "sheeran"]),
    ("Who is the 'Queen of Pop'?", "madonna", ["madonna"]),
    ("Which instrument has 88 keys?", "piano", ["piano"]),
    ("Who sang 'Hello'?", "adele", ["adele"]),
    ("How many strings does a standard guitar have?", "6", ["6", "six"]),
    ("Who sang 'Blinding Lights'?", "the weeknd", ["the weeknd", "weeknd"]),
    ("What is the best-selling album of all time?", "thriller", ["thriller"]),
    ("Who sang 'Bad Guy'?", "billie eilish", ["billie eilish", "billie"]),
    ("Which country does BTS come from?", "south korea", ["south korea", "korea"]),
    ("Who sang 'Despacito'?", "luis fonsi", ["luis fonsi", "fonsi", "daddy yankee"]),
    ("What note is A in Hertz (approx)?", "440", ["440", "440hz"]),
    ("Who is known as 'Piano Man'?", "billy joel", ["billy joel", "joel"]),
    ("Which band sang 'Hotel California'?", "eagles", ["eagles", "the eagles"]),
]

_FOOD_QUIZ = [
    ("What is the main ingredient in guacamole?", "avocado", ["avocado"]),
    ("Which country invented sushi?", "japan", ["japan"]),
    ("What is tofu made from?", "soybeans", ["soybeans", "soy beans", "soya", "soy"]),
    ("What is the spiciest chili in the world?", "carolina reaper", ["carolina reaper", "reaper"]),
    ("What fruit is known as the 'king of fruits'?", "durian", ["durian"]),
    ("Which nut is used to make marzipan?", "almond", ["almond", "almonds"]),
    ("What is the main spice in a traditional curry?", "turmeric", ["turmeric", "cumin"]),
    ("What type of pastry is used for eclairs?", "choux", ["choux", "choux pastry"]),
    ("What fruit is 60% water and 40% sugar?", "date", ["date", "dates"]),
    ("Which country is famous for inventing pizza?", "italy", ["italy"]),
    ("What is the Italian word for 'cheese'?", "formaggio", ["formaggio", "cheese"]),
    ("What is wasabi made from?", "horseradish", ["horseradish", "wasabi plant"]),
    ("How many calories in a gram of fat?", "9", ["9", "nine"]),
    ("Which fruit contains the most vitamin C?", "kiwi", ["kiwi", "kiwifruit", "acerola"]),
    ("What is the main ingredient in hummus?", "chickpeas", ["chickpeas", "chickpea", "garbanzo"]),
]

_MOVIE_QUIZ = [
    ("Who directed Jurassic Park?", "steven spielberg", ["spielberg", "steven spielberg"]),
    ("What year was the first Iron Man released?", "2008", ["2008"]),
    ("Who played Tony Stark in the MCU?", "robert downey jr", ["robert downey jr", "rdj", "downey"]),
    ("What is the highest-grossing film of all time?", "avatar", ["avatar"]),
    ("What film features the quote 'I'll be back'?", "the terminator", ["terminator", "the terminator"]),
    ("Who played Forrest Gump?", "tom hanks", ["tom hanks", "hanks"]),
    ("In which film does the line 'You can't handle the truth' appear?", "a few good men", ["a few good men", "few good men"]),
    ("What studio produced Toy Story?", "pixar", ["pixar"]),
    ("Who directed the Dark Knight trilogy?", "christopher nolan", ["nolan", "christopher nolan"]),
    ("In what year was the original Star Wars released?", "1977", ["1977"]),
    ("Who played Jack in Titanic?", "leonardo dicaprio", ["leo", "dicaprio", "leonardo dicaprio"]),
    ("What is the name of the toy cowboy in Toy Story?", "woody", ["woody"]),
    ("What is the name of the fictional African country in Black Panther?", "wakanda", ["wakanda"]),
    ("Which film won the first Academy Award for Best Picture?", "wings", ["wings"]),
    ("Who voiced Simba in The Lion King (1994)?", "matthew broderick", ["matthew broderick", "broderick"]),
]

_CODING_QUIZ = [
    ("What does CPU stand for?", "central processing unit", ["central processing unit", "cpu"]),
    ("What language does Python's name come from?", "monty python", ["monty python", "monty python's flying circus"]),
    ("What does HTML stand for?", "hypertext markup language", ["hypertext markup language", "html"]),
    ("What symbol is used for comments in Python?", "#", ["#", "hash", "hashtag"]),
    ("What is the file extension for Python files?", ".py", [".py", "py"]),
    ("What does RAM stand for?", "random access memory", ["random access memory"]),
    ("What does 'OOP' stand for?", "object oriented programming", ["object oriented programming", "oop"]),
    ("What is the index of the first element in most languages?", "0", ["0", "zero"]),
    ("What does SQL stand for?", "structured query language", ["structured query language"]),
    ("What is the result of 2**10 in Python?", "1024", ["1024"]),
    ("What does CSS stand for?", "cascading style sheets", ["cascading style sheets"]),
    ("Which language is known as the 'language of the web'?", "javascript", ["javascript", "js"]),
    ("What does API stand for?", "application programming interface", ["application programming interface"]),
    ("What is the most starred project on GitHub?", "freeCodeCamp", ["freecodecamp", "freecodecamps"]),
    ("What does IDE stand for?", "integrated development environment", ["integrated development environment"]),
]

_ANIME_QUIZ = [
    ("Who is the main character in Naruto?", "naruto uzumaki", ["naruto", "naruto uzumaki"]),
    ("What is the final form of Vegeta's saiyan transformation?", "ultra ego", ["ultra ego", "super saiyan", "ssj"]),
    ("Who killed Kaido in One Piece?", "luffy", ["luffy", "monkey d luffy"]),
    ("What is the name of the Titan-shifting power in Attack on Titan?", "founding titan", ["founding titan", "titan"]),
    ("What school does Izuku Midoriya attend?", "ua high", ["ua high", "ua", "u.a."]),
    ("What is Goku's real Saiyan name?", "kakarot", ["kakarot", "kakarotto"]),
    ("Who is the Demon King in Seven Deadly Sins?", "zeldris", ["zeldris", "meliodas"]),
    ("What is the name of Light Yagami's notebook?", "death note", ["death note"]),
    ("Which anime features the Quinx Squad?", "tokyo ghoul", ["tokyo ghoul", "tokyo ghoul:re"]),
    ("Who is the captain of Squad 6 in Bleach?", "byakuya kuchiki", ["byakuya", "byakuya kuchiki"]),
    ("What is Luffy's Devil Fruit?", "gomu gomu no mi", ["gomu gomu", "gomu gomu no mi", "rubber fruit"]),
    ("Who is Sasuke's brother?", "itachi", ["itachi", "itachi uchiha"]),
    ("What is the name of the main female character in Sword Art Online?", "asuna", ["asuna", "asuna yuuki"]),
    ("Who is the protagonist of Fullmetal Alchemist?", "edward elric", ["edward", "edward elric", "ed"]),
    ("In Demon Slayer, what is the name of Tanjiro's sister?", "nezuko", ["nezuko", "nezuko kamado"]),
]

_CRICKET_QUIZ = [
    ("Who has scored the most international centuries?", "sachin tendulkar", ["sachin", "tendulkar", "sachin tendulkar"]),
    ("What is the highest possible score in cricket?", "6", ["6", "six"]),
    ("How many stumps are in a cricket wicket?", "3", ["3", "three"]),
    ("Which country won the first Cricket World Cup in 1975?", "west indies", ["west indies", "windies"]),
    ("What does LBW stand for?", "leg before wicket", ["leg before wicket", "lbw"]),
    ("Who holds the record for fastest Test century?", "brendon mccullum", ["mccullum", "brendon mccullum"]),
    ("How many overs in a T20 innings per team?", "20", ["20", "twenty"]),
    ("Who is known as the 'God of Cricket'?", "sachin tendulkar", ["sachin", "tendulkar"]),
    ("Which bowler has taken most ODI wickets?", "muttiah muralitharan", ["murali", "muralitharan"]),
    ("What is the name of cricket's governing body?", "icc", ["icc", "international cricket council"]),
    ("In cricket, what is a 'duck'?", "zero runs", ["zero", "zero runs", "0", "no runs"]),
    ("How long is a cricket pitch?", "22 yards", ["22 yards", "22", "22 yard"]),
    ("Which country invented cricket?", "england", ["england", "britain", "uk"]),
    ("Who has hit the most sixes in international cricket?", "chris gayle", ["gayle", "chris gayle"]),
    ("What is the term for 5 wickets in an innings?", "five-for", ["five-for", "fifer", "five wickets"]),
]

_WHOAMI_CLUES = [
    (["I was born in India 🇮🇳", "I am a cricketer", "I scored 100 international centuries", "I retired in 2013"], "sachin tendulkar", ["sachin", "tendulkar"]),
    (["I was born in the UK", "I invented the telephone", "My name has 3 words", "I was born in 1847"], "alexander graham bell", ["bell", "graham bell", "alexander graham bell"]),
    (["I was a German physicist", "I developed the theory of relativity", "My equation is E=mc²", "I died in 1955"], "albert einstein", ["einstein", "albert einstein"]),
    (["I am a footballer ⚽", "I play for Argentina 🇦🇷", "I have won the Ballon d'Or 8 times", "My first name starts with L"], "lionel messi", ["messi", "lionel messi"]),
    (["I am a singer", "I am from the UK", "I sang 'Hello' and 'Someone Like You'", "I won 4 Grammys in one night"], "adele", ["adele"]),
    (["I am a tech founder", "I co-founded Apple", "I was born in 1955", "I died in 2011"], "steve jobs", ["steve jobs", "jobs"]),
    (["I am a scientist", "I discovered gravity from an apple", "I was born in England", "My last name has 6 letters"], "isaac newton", ["newton", "isaac newton"]),
    (["I am a painter", "I painted the Mona Lisa", "I was Italian", "I was also a sculptor and inventor"], "leonardo da vinci", ["da vinci", "leonardo da vinci", "leonardo"]),
]

_ODD_ONE_OUT = [
    ("🍎 Apple | 🍊 Orange | 🥕 Carrot | 🍇 Grapes", "carrot", ["carrot"], "Which is NOT a fruit?"),
    ("🏏 Cricket | ⚽ Football | 🎵 Music | 🎾 Tennis", "music", ["music"], "Which is NOT a sport?"),
    ("🌍 Earth | 🪐 Saturn | ☀️ Sun | 🌕 Moon", "sun", ["sun"], "Which is NOT a planet?"),
    ("🐕 Dog | 🐈 Cat | 🦅 Eagle | 🐠 Fish", "eagle", ["eagle"], "Which does NOT live on land primarily?"),
    ("🇫🇷 French | 🇩🇪 German | 🌍 Swahili | 🗼 Eiffel", "eiffel", ["eiffel"], "Which is NOT a language?"),
    ("🔴 Red | 🔵 Blue | 💎 Diamond | 🟡 Yellow", "diamond", ["diamond"], "Which is NOT a color?"),
    ("Python | Java | HTML | C++", "html", ["html"], "Which is NOT a programming language?"),
    ("🎹 Piano | 🎸 Guitar | 🎤 Microphone | 🥁 Drums", "microphone", ["microphone"], "Which is NOT a musical instrument?"),
]

_MISSING_SEQS = [
    ([2, 4, 6, 8, "?"], "10", ["10"]),
    ([1, 3, 6, 10, "?"], "15", ["15"]),
    ([5, 10, 20, 40, "?"], "80", ["80"]),
    ([1, 1, 2, 3, 5, 8, "?"], "13", ["13"]),
    ([100, 90, 80, 70, "?"], "60", ["60"]),
    ([2, 6, 18, 54, "?"], "162", ["162"]),
    ([1, 4, 9, 16, 25, "?"], "36", ["36"]),
    ([7, 14, 21, 28, "?"], "35", ["35"]),
    ([3, 6, 12, 24, "?"], "48", ["48"]),
    ([50, 45, 40, 35, "?"], "30", ["30"]),
]

_LYRICS = [
    ("🎵 'Is this the real life? Is this just ___?' (Queen)", "fantasy", ["fantasy"]),
    ("🎵 'Hello from the other ___' (Adele)", "side", ["side"]),
    ("🎵 'Never gonna give you up, never gonna let you ___' (Rick Astley)", "down", ["down"]),
    ("🎵 'We will, we will ___ you' (Queen)", "rock", ["rock"]),
    ("🎵 'Sweet dreams are made of ___, who am I to disagree?' (Eurythmics)", "this", ["this"]),
    ("🎵 'I want to break ___' (Queen)", "free", ["free"]),
    ("🎵 'Don't stop ___ in' (Journey)", "believin", ["believin", "believin'", "believing"]),
    ("🎵 'Baby I was born to ___' (Springsteen)", "run", ["run"]),
    ("🎵 'Every ___ you make, every move you make' (The Police)", "breath", ["breath"]),
    ("🎵 'Eye of the ___, rising up to the challenge' (Survivor)", "tiger", ["tiger"]),
]

_EMOJI_RIDDLES = [
    ("👸❄️🏔️", "frozen", ["frozen"]),
    ("🕷️🦸", "spiderman", ["spiderman", "spider-man", "spider man"]),
    ("🦁👑", "lion king", ["lion king", "the lion king"]),
    ("🔥💃🌹🇪🇸", "flamenco", ["flamenco", "spanish dance", "salsa"]),
    ("🍎💻📱", "apple", ["apple"]),
    ("🐍🔑🔓", "python key", ["python"]),
    ("⚡🔨🪬🛡️", "thor", ["thor"]),
    ("🌙🦇🦸‍♂️🌃", "batman", ["batman"]),
    ("🧙‍♂️⚡⚡", "harry potter", ["harry potter", "potter"]),
    ("🚀🌕👨‍🚀", "apollo", ["apollo", "moon landing", "astronaut"]),
]

_COUNTRY_HINTS = [
    (["I am in South Asia 🌏", "My population is 1.4 billion", "I have the Taj Mahal", "I love cricket 🏏"], "india", ["india"]),
    (["I am an island nation 🏝️", "I am in East Asia", "I am famous for anime", "Mount Fuji is in me"], "japan", ["japan"]),
    (["I have the Amazon rainforest 🌳", "I speak Portuguese", "I am in South America", "I love football ⚽"], "brazil", ["brazil"]),
    (["I have the Great Wall 🧱", "I have 1.4 billion people", "My capital is Beijing", "I am in East Asia"], "china", ["china"]),
    (["I have the Eiffel Tower 🗼", "I speak French", "I am in Western Europe", "I am famous for wine"], "france", ["france"]),
    (["I discovered America 🗽", "I have 50 states", "My capital is Washington DC", "English is my main language"], "usa", ["usa", "united states", "america"]),
    (["I created cricket 🏏", "I am an island 🏝️", "I speak English", "My capital is London"], "england", ["england", "uk", "britain"]),
    (["I have the Sahara Desert", "I have pyramids 🔺", "I have the Nile River", "My capital is Cairo"], "egypt", ["egypt"]),
    (["I am the largest country 🌍", "My capital is Moscow", "I span 11 time zones", "I love vodka 🍶"], "russia", ["russia"]),
    (["I have kangaroos 🦘", "I am a continent and country", "I speak English", "My capital is Canberra"], "australia", ["australia"]),
]

_WOULD_YOU_RATHER = [
    ("Would you rather: Have the ability to fly ✈️ or Be invisible 👻?", "fly", "invisible"),
    ("Would you rather: Live in the future 🚀 or Live in the past 🏰?", "future", "past"),
    ("Would you rather: Never eat again 🍽️ or Never sleep again 😴?", "never eat", "never sleep"),
    ("Would you rather: Be 3 feet tall 🧍 or 10 feet tall 🦒?", "3 feet", "10 feet"),
    ("Would you rather: Only be able to whisper 🤫 or Only be able to shout 📢?", "whisper", "shout"),
    ("Would you rather: Have no internet 📵 or No phone calls ever 📵?", "no internet", "no calls"),
    ("Would you rather: Know how you'll die 💀 or Know when you'll die 📅?", "how", "when"),
    ("Would you rather: Be famous 🌟 or Be extremely rich 💰?", "famous", "rich"),
    ("Would you rather: Only eat pizza 🍕 or Only eat sushi 🍱 forever?", "pizza", "sushi"),
    ("Would you rather: Speak every language 🌐 or Play every instrument 🎵?", "every language", "every instrument"),
    ("Would you rather: Have a pause button ⏸️ or A rewind button ⏪ for life?", "pause", "rewind"),
    ("Would you rather: Meet your ancestors 👴 or Your descendants 👶?", "ancestors", "descendants"),
]

_VERSUS = [
    ("⚔️ Messi 🇦🇷 vs Ronaldo 🇵🇹 — Who is the GOAT?", "Messi 🇦🇷", "Ronaldo 🇵🇹"),
    ("⚔️ Marvel vs DC — Which universe is better?", "Marvel 🦸", "DC 🦇"),
    ("⚔️ Tea ☕ vs Coffee ☕ — Which is better?", "Tea ☕", "Coffee ☕"),
    ("⚔️ Mountains 🏔️ vs Beach 🏖️ — Preferred vacation?", "Mountains 🏔️", "Beach 🏖️"),
    ("⚔️ Night Owl 🦉 vs Early Bird 🐦 — Which are you?", "Night Owl 🦉", "Early Bird 🐦"),
    ("⚔️ Dogs 🐕 vs Cats 🐈 — Best pet?", "Dogs 🐕", "Cats 🐈"),
    ("⚔️ iOS 🍎 vs Android 🤖 — Which is better?", "iOS 🍎", "Android 🤖"),
    ("⚔️ Summer ☀️ vs Winter ❄️ — Favourite season?", "Summer ☀️", "Winter ❄️"),
    ("⚔️ Books 📚 vs Movies 🎬 — Better storytelling?", "Books 📚", "Movies 🎬"),
    ("⚔️ Pizza 🍕 vs Burger 🍔 — Best fast food?", "Pizza 🍕", "Burger 🍔"),
]

_NEVER_HAVE = [
    "Never have I ever gone skydiving 🪂",
    "Never have I ever eaten sushi 🍱",
    "Never have I ever stayed awake for 24+ hours 😴",
    "Never have I ever broken a bone 💀",
    "Never have I ever been on a cruise 🚢",
    "Never have I ever met a celebrity 🌟",
    "Never have I ever learned a musical instrument 🎸",
    "Never have I ever gone scuba diving 🤿",
    "Never have I ever ridden a horse 🐎",
    "Never have I ever sent a message to the wrong person 😅",
    "Never have I ever pulled an all-nighter for fun 🌙",
    "Never have I ever been to another country ✈️",
    "Never have I ever eaten something I deeply regretted 🤢",
    "Never have I ever won a competition 🏆",
    "Never have I ever dyed my hair 🎨",
]

_TYPE_RACE_PHRASES = [
    "The quick brown fox jumps over the lazy dog",
    "Typing fast is a skill that takes practice every day",
    "Telegram bots are fun to build and even more fun to use",
    "In the beginning there was nothing and then it exploded",
    "The greatest glory is not in never falling but in rising every time",
    "Success is not final failure is not fatal it is the courage to continue",
    "Not all those who wander are lost in the vast world of possibilities",
    "With great power comes great responsibility always remember that",
    "Cricket is a game of glorious uncertainties played by gentlemen",
    "The only way to do great work is to love what you do every day",
]

_ZODIAC = {
    "aries": ("Mar 21 – Apr 19", "♈", "Brave, direct, and adventurous. A natural leader!"),
    "taurus": ("Apr 20 – May 20", "♉", "Reliable, patient, and stubborn in the best way."),
    "gemini": ("May 21 – Jun 20", "♊", "Curious, clever, and charming — two sides!"),
    "cancer": ("Jun 21 – Jul 22", "♋", "Emotional, nurturing, and deeply intuitive."),
    "leo": ("Jul 23 – Aug 22", "♌", "Confident, generous, and loves the spotlight."),
    "virgo": ("Aug 23 – Sep 22", "♍", "Analytical, practical, and a total perfectionist."),
    "libra": ("Sep 23 – Oct 22", "♎", "Diplomatic, fair, and charming in every way."),
    "scorpio": ("Oct 23 – Nov 21", "♏", "Intense, passionate, and deeply resourceful."),
    "sagittarius": ("Nov 22 – Dec 21", "♐", "Optimistic, adventurous, and brutally honest."),
    "capricorn": ("Dec 22 – Jan 19", "♑", "Disciplined, ambitious, and extremely patient."),
    "aquarius": ("Jan 20 – Feb 18", "♒", "Original, independent, and deeply humanitarian."),
    "pisces": ("Feb 19 – Mar 20", "♓", "Creative, compassionate, and deeply empathetic."),
}

_CATEGORIES = [
    ("name a country in Asia", ["india", "china", "japan", "pakistan", "bangladesh", "korea", "vietnam", "thailand", "indonesia", "malaysia", "iran", "iraq", "saudi arabia", "turkey", "nepal", "myanmar", "cambodia", "laos", "mongolia", "philippines"]),
    ("name a sport played with a ball", ["cricket", "football", "soccer", "basketball", "tennis", "baseball", "golf", "rugby", "volleyball", "handball", "bowling", "polo", "lacrosse", "billiards", "snooker"]),
    ("name a planet in our solar system", ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]),
    ("name an animal that can fly", ["eagle", "hawk", "owl", "parrot", "pigeon", "dove", "sparrow", "bat", "hummingbird", "penguin" ]),
    ("name a programming language", ["python", "java", "c", "c++", "javascript", "typescript", "go", "rust", "ruby", "swift", "kotlin", "php", "scala", "perl", "r"]),
    ("name something you find in a kitchen", ["fridge", "oven", "microwave", "sink", "counter", "knife", "pan", "pot", "spatula", "blender", "toaster", "plate", "bowl", "cup", "spoon", "fork"]),
    ("name a type of music genre", ["rock", "pop", "jazz", "classical", "blues", "hip hop", "rap", "reggae", "country", "metal", "punk", "r&b", "soul", "folk", "electronic"]),
    ("name a fruit that is red", ["apple", "strawberry", "cherry", "watermelon", "pomegranate", "raspberry", "cranberry", "red grape"]),
]

_WORD_LIST = [
    "cricket", "python", "telegram", "sunset", "mountain", "galaxy", "thunder",
    "jungle", "diamond", "penguin", "starfish", "keyboard", "tropical", "horizon",
    "lightning", "butterfly", "champion", "universe", "paradise", "symphony",
    "glacier", "tsunami", "elephant", "flamingo", "volcano", "crystal",
    "ocean", "noble", "energy", "flute", "typhoon", "dragon", "cactus",
    "rainbow", "rocket", "dolphin", "lantern", "mystery", "frozen", "jasmine",
    "bamboo", "castle", "mirror", "silver", "copper", "falcon", "garden",
    "harbor", "island", "jungle", "kitten", "lemon", "marble", "nectar",
]

_CAESAR_CIPHERS = [
    (3, "khoor zruog", "hello world"),
    (5, "kfyj xfhw", "flip hack"),  
    (7, "aophu", "think"),
    (3, "zlhqfh", "science"),
    (4, "qmec lsvo", "mike love"),
    (3, "whvw brxu eudlq", "test your brain"),
    (6, "znk yge", "the sea"),
    (3, "frgh", "code"),
    (3, "zhofrph wr whohjudp", "welcome to telegram"),
    (5, "btz hfq itsj ny", "you can done it"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# QUIZ COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

async def mathquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Random arithmetic quiz."""
    ops = [("+", operator.add), ("-", operator.sub), ("×", operator.mul)]
    sym, fn = random.choice(ops)
    if sym == "×":
        a, b = random.randint(2, 12), random.randint(2, 12)
    else:
        a, b = random.randint(10, 100), random.randint(1, 50)
    ans = fn(a, b)
    await _start_quiz(update, context,
        question=f"🔢 What is {a} {sym} {b}?",
        answer=str(ans), accepted=[str(ans)], timeout=20)


async def scramble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unscramble a word."""
    word = random.choice(_WORD_LIST)
    chars = list(word)
    random.shuffle(chars)
    jumbled = "".join(chars)
    while jumbled == word:
        random.shuffle(chars)
        jumbled = "".join(chars)
    await _start_quiz(update, context,
        question=f"🔀 Unscramble this word: <b>{jumbled.upper()}</b>",
        answer=word, accepted=[word], timeout=30,
        hint=f"💡 Hint: {len(word)} letters")


async def riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_RIDDLES)
    await _start_quiz(update, context, question=q, answer=ans, accepted=acc, timeout=45)


async def flag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji, country, acc = random.choice(_FLAGS)
    await _start_quiz(update, context,
        question=f"🌍 Which country does this flag belong to?\n\n{emoji}",
        answer=country, accepted=acc, timeout=30)


async def capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country, cap, acc = random.choice(_CAPITALS)
    await _start_quiz(update, context,
        question=f"🏙️ What is the capital of <b>{country}</b>?",
        answer=cap, accepted=acc, timeout=30)


async def emoji_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojis, movie, acc = random.choice(_EMOJI_MOVIES)
    await _start_quiz(update, context,
        question=f"🎬 Guess the movie from the emojis!\n\n<b>{emojis}</b>",
        answer=movie, accepted=acc, timeout=40)


async def fill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sentence, ans, acc = random.choice(_FILL_BLANKS)
    await _start_quiz(update, context,
        question=f"✍️ Fill in the blank:\n\n<i>{sentence}</i>",
        answer=ans, accepted=acc, timeout=30)


async def sport_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_SPORT_QUIZ)
    await _start_quiz(update, context, question=f"🏅 {q}", answer=ans, accepted=acc, timeout=30)


async def science_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_SCIENCE_QUIZ)
    await _start_quiz(update, context, question=f"🔬 {q}", answer=ans, accepted=acc, timeout=30)


async def geo_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_GEO_QUIZ)
    await _start_quiz(update, context, question=f"🗺️ {q}", answer=ans, accepted=acc, timeout=30)


async def history_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_HISTORY_QUIZ)
    await _start_quiz(update, context, question=f"📜 {q}", answer=ans, accepted=acc, timeout=35)


async def music_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_MUSIC_QUIZ)
    await _start_quiz(update, context, question=f"🎵 {q}", answer=ans, accepted=acc, timeout=30)


async def food_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_FOOD_QUIZ)
    await _start_quiz(update, context, question=f"🍽️ {q}", answer=ans, accepted=acc, timeout=30)


async def movie_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_MOVIE_QUIZ)
    await _start_quiz(update, context, question=f"🎬 {q}", answer=ans, accepted=acc, timeout=30)


async def coding_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_CODING_QUIZ)
    await _start_quiz(update, context, question=f"💻 {q}", answer=ans, accepted=acc, timeout=30)


async def anime_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_ANIME_QUIZ)
    await _start_quiz(update, context, question=f"🎭 {q}", answer=ans, accepted=acc, timeout=30)


async def cricket_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, ans, acc = random.choice(_CRICKET_QUIZ)
    await _start_quiz(update, context, question=f"🏏 {q}", answer=ans, accepted=acc, timeout=30)


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clues, ans, acc = random.choice(_WHOAMI_CLUES)
    clue_text = "\n".join(f"  • {c}" for c in clues)
    await _start_quiz(update, context,
        question=f"🕵️ Guess who I am!\n{clue_text}",
        answer=ans, accepted=acc, timeout=45)


async def oddoneout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options, ans, acc, hint = random.choice(_ODD_ONE_OUT)
    await _start_quiz(update, context,
        question=f"🔍 Odd One Out:\n<b>{options}</b>\n<i>{hint}</i>",
        answer=ans, accepted=acc, timeout=25)


async def missing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    seq, ans, acc = random.choice(_MISSING_SEQS)
    seq_str = " → ".join(str(x) for x in seq)
    await _start_quiz(update, context,
        question=f"🔢 What is the missing number?\n<b>{seq_str}</b>",
        answer=ans, accepted=acc, timeout=25)


async def lyric_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clue, ans, acc = random.choice(_LYRICS)
    await _start_quiz(update, context,
        question=f"🎤 Complete the lyric:\n<i>{clue}</i>",
        answer=ans, accepted=acc, timeout=30)


async def emoji_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojis, ans, acc = random.choice(_EMOJI_RIDDLES)
    await _start_quiz(update, context,
        question=f"🤔 What do these emojis represent?\n\n<b>{emojis}</b>",
        answer=ans, accepted=acc, timeout=35)


async def countryguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hints, ans, acc = random.choice(_COUNTRY_HINTS)
    hint_text = "\n".join(f"  🔹 {h}" for h in hints)
    await _start_quiz(update, context,
        question=f"🌍 Guess the country from these clues:\n{hint_text}",
        answer=ans, accepted=acc, timeout=45)


async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shift, cipher, plain = random.choice(_CAESAR_CIPHERS)
    await _start_quiz(update, context,
        question=f"🔐 Decode this Caesar cipher (shift={shift}):\n<code>{cipher}</code>",
        answer=plain, accepted=[plain], timeout=40,
        hint="Hint: Shift each letter back by the given number")


# ═══════════════════════════════════════════════════════════════════════════════
# WORD / GROUP GAMES
# ═══════════════════════════════════════════════════════════════════════════════

async def wordchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in _word_chain:
        _word_chain[chat_id]["active"] = False
        del _word_chain[chat_id]
        await update.message.reply_text("🛑 Word chain game stopped.")
        return
    start_word = random.choice(_WORD_LIST)
    _word_chain[chat_id] = {
        "active": True,
        "last_char": start_word[-1],
        "used": {start_word},
        "last_user": update.effective_user.first_name,
    }
    await update.message.reply_text(
        f"🔗 <b>Word Chain Game started!</b>\n\n"
        f"Starting word: <b>{start_word}</b>\n"
        f"Next word must start with: <b>{start_word[-1].upper()}</b>\n\n"
        f"<i>Type /wordchain again to stop the game.</i>",
        parse_mode="HTML",
    )


async def lastletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for wordchain with cleaner name."""
    await wordchain(update, context)


async def typerace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in _type_race:
        await update.message.reply_text("⚠️ A type race is already running!")
        return
    phrase = random.choice(_TYPE_RACE_PHRASES)

    async def _timeout():
        await asyncio.sleep(45)
        if chat_id in _type_race:
            del _type_race[chat_id]
            try:
                await context.bot.send_message(
                    chat_id,
                    f"⏰ Time's up! Nobody finished the type race.\n"
                    f"The phrase was: <i>{phrase}</i>",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    task = asyncio.create_task(_timeout())
    _type_race[chat_id] = {
        "active": True,
        "phrase": phrase,
        "start_ts": time.time(),
        "task": task,
    }
    await update.message.reply_text(
        f"⌨️ <b>Type Race!</b>\n\n"
        f"Type the following sentence <b>exactly</b> (first one wins):\n\n"
        f"<code>{phrase}</code>\n\n"
        f"⏱ You have <b>45 seconds</b>! Go!",
        parse_mode="HTML",
    )


async def category_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hint, valid = random.choice(_CATEGORIES)
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"📂 <b>Category Game!</b>\n\n"
        f"Can you <b>{hint}</b>?\n\n"
        f"<i>First person to type a correct valid answer wins!</i>",
        parse_mode="HTML",
    )
    await _start_quiz(update, context,
        question=f"📂 Quick! {hint.capitalize()}!",
        answer=valid[0], accepted=valid, timeout=30)


async def rhyme_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = [
        ("cat", ["bat", "hat", "mat", "rat", "sat", "fat", "pat", "vat"]),
        ("day", ["say", "pay", "way", "bay", "may", "ray", "hay", "lay", "play", "stay"]),
        ("night", ["light", "right", "might", "sight", "tight", "fight", "bright", "flight"]),
        ("fire", ["hire", "tire", "wire", "desire", "inspire", "aspire", "expire", "admire"]),
        ("star", ["bar", "car", "far", "jar", "tar", "war", "guitar", "bizarre"]),
        ("blue", ["true", "few", "dew", "clue", "crew", "drew", "flew", "grew", "knew", "new"]),
        ("moon", ["tune", "soon", "boon", "noon", "spoon", "balloon", "cartoon", "buffoon"]),
        ("rain", ["train", "pain", "main", "gain", "brain", "chain", "plain", "spain", "claim"]),
    ]
    word, rhymes = random.choice(pairs)
    await _start_quiz(update, context,
        question=f"🎵 Give a word that RHYMES with: <b>{word.upper()}</b>",
        answer=rhymes[0], accepted=rhymes, timeout=20,
        hint=f"💡 Any word that sounds like '{word}'")


async def synonym_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = [
        ("happy", ["glad", "joyful", "cheerful", "pleased", "content", "elated", "delighted", "merry"]),
        ("sad", ["unhappy", "sorrowful", "melancholy", "gloomy", "depressed", "miserable", "dejected"]),
        ("big", ["large", "huge", "enormous", "gigantic", "vast", "massive", "great", "immense"]),
        ("fast", ["quick", "rapid", "swift", "speedy", "brisk", "hasty", "fleet"]),
        ("clever", ["smart", "intelligent", "bright", "sharp", "witty", "shrewd", "astute"]),
        ("beautiful", ["pretty", "lovely", "gorgeous", "stunning", "attractive", "elegant", "ravishing"]),
        ("brave", ["courageous", "fearless", "bold", "daring", "valiant", "heroic", "gallant"]),
        ("angry", ["furious", "mad", "irate", "enraged", "livid", "infuriated", "wrathful"]),
    ]
    word, syns = random.choice(data)
    await _start_quiz(update, context,
        question=f"📝 Give a SYNONYM for: <b>{word.upper()}</b>",
        answer=syns[0], accepted=syns, timeout=20,
        hint="💡 A word with a similar meaning")


async def antonym_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = [
        ("hot", ["cold", "cool", "chilly", "freezing", "icy"]),
        ("fast", ["slow", "sluggish", "leisurely"]),
        ("happy", ["sad", "unhappy", "miserable", "depressed"]),
        ("big", ["small", "tiny", "little", "miniature", "petite"]),
        ("light", ["dark", "heavy"]),
        ("old", ["new", "young", "fresh"]),
        ("strong", ["weak", "feeble", "frail"]),
        ("brave", ["cowardly", "timid", "fearful", "scared"]),
    ]
    word, ants = random.choice(data)
    await _start_quiz(update, context,
        question=f"📝 Give an ANTONYM for: <b>{word.upper()}</b>",
        answer=ants[0], accepted=ants, timeout=20,
        hint="💡 A word with the opposite meaning")


async def anagram_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = [
        ("listen", ["silent", "enlist", "tinsel", "inlets"]),
        ("earth", ["heart", "hater", "rathe"]),
        ("race", ["care", "acre", "acer"]),
        ("night", ["thing"]),
        ("stare", ["tears", "rates", "aster"]),
        ("dusty", ["study", "dusty"]),
        ("angel", ["glean", "angle", "lange"]),
        ("below", ["elbow", "bowel"]),
        ("spare", ["reaps", "pears", "parse", "rapes"]),
        ("least", ["tales", "slate", "steal", "stale"]),
    ]
    word, anagrams = random.choice(pairs)
    await _start_quiz(update, context,
        question=f"🔤 Find an anagram of: <b>{word.upper()}</b>\n<i>(Use all the same letters in a different order)</i>",
        answer=anagrams[0], accepted=anagrams, timeout=30)


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANT / SOCIAL GAMES (no quiz engine needed)
# ═══════════════════════════════════════════════════════════════════════════════

async def would_you(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a, b = random.choice(_WOULD_YOU_RATHER)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ {a}", callback_data=f"wr_A_{update.message.message_id}"),
        InlineKeyboardButton(f"✅ {b}", callback_data=f"wr_B_{update.message.message_id}"),
    ]])
    await update.message.reply_text(
        f"🤔 <b>Would You Rather?</b>\n\n{q}",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def would_you_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Voted! ✅", show_alert=False)


async def versus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a, b = random.choice(_VERSUS)
    msg_id = update.message.message_id
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{a}", callback_data=f"vs_A_{msg_id}"),
        InlineKeyboardButton(f"{b}", callback_data=f"vs_B_{msg_id}"),
    ]])
    await update.message.reply_text(
        f"⚔️ <b>VERSUS!</b>\n\n{q}\n\nVote now!",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def versus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    side = "A" if "_A_" in query.data else "B"
    await query.answer(f"You voted! ✅", show_alert=False)


async def neverhave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stmt = random.choice(_NEVER_HAVE)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ I have!", callback_data="nh_have"),
        InlineKeyboardButton("❌ Never!", callback_data="nh_never"),
    ]])
    await update.message.reply_text(
        f"🙋 <b>Never Have I Ever</b>\n\n{stmt}\n\nReact honestly!",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def neverhave_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "nh_have":
        await query.answer("Interesting! You have! 😏", show_alert=False)
    else:
        await query.answer("Never! Clean record 😇", show_alert=False)


async def zodiac_compat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        signs = "\n".join(f"  {v[1]} {k.capitalize()} ({v[0]})" for k, v in _ZODIAC.items())
        await update.message.reply_text(
            f"♈ <b>Zodiac Command</b>\n\n"
            f"Usage: /zodiac [sign]\nExample: /zodiac scorpio\n\n"
            f"<b>All signs:</b>\n{signs}",
            parse_mode="HTML",
        )
        return
    sign = args[0].lower()
    if sign not in _ZODIAC:
        await update.message.reply_text("❌ Unknown zodiac sign. Try: aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces")
        return
    dates, emoji, desc = _ZODIAC[sign]
    compat = random.choice([k for k in _ZODIAC if k != sign])
    compat_emoji = _ZODIAC[compat][1]
    score = random.randint(60, 99)
    await update.message.reply_text(
        f"{emoji} <b>{sign.capitalize()}</b> ({dates})\n\n"
        f"<i>{desc}</i>\n\n"
        f"💕 <b>Today's Compatibility:</b>\n"
        f"{emoji} {sign.capitalize()} + {compat_emoji} {compat.capitalize()} = <b>{score}% match!</b>",
        parse_mode="HTML",
    )


async def numberbomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    bomb_num = random.randint(1, 15)
    max_n = 20
    picked = set()

    lines = [f"💣 <b>Number Bomb!</b>\n\nPick a number 1–{max_n}. One number is the BOMB 💥\nEveryone pick a number (type it)!"]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    await _start_quiz(update, context,
        question=f"💣 Type a number 1–{max_n} to defuse... or hit the bomb!",
        answer=str(bomb_num),
        accepted=[str(i) for i in range(1, max_n + 1) if i != bomb_num],
        timeout=30,
    )


async def fast_math(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a, b = random.randint(1, 20), random.randint(1, 20)
    ops = [("+", a + b), ("-", abs(a - b)), ("×", a * b)]
    sym, ans = random.choice(ops)
    await _start_quiz(update, context,
        question=f"⚡ <b>SPEED MATH!</b> First to answer wins!\n\n{a} {sym} {b} = ?",
        answer=str(ans), accepted=[str(ans)], timeout=10)


async def prime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    n = random.choice([i for i in range(2, 100)])
    result = "yes" if is_prime(n) else "no"
    await _start_quiz(update, context,
        question=f"🔢 Is <b>{n}</b> a prime number? Answer <b>yes</b> or <b>no</b>",
        answer=result, accepted=[result, "yes" if result == "yes" else "no",
                                   "y" if result == "yes" else "n"],
        timeout=15)


async def mixword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = random.choice(_WORD_LIST)
    chars = list(word)
    while chars == list(word):
        random.shuffle(chars)
    jumbled = " ".join(c.upper() for c in chars)
    await _start_quiz(update, context,
        question=f"🔤 Arrange these letters into a word:\n\n<b>{jumbled}</b>",
        answer=word, accepted=[word], timeout=35,
        hint=f"💡 Hint: It's {len(word)} letters long")
