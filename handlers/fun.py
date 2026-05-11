import asyncio
import random
import httpx
from io import BytesIO
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent,
)
from telegram.ext import ContextTypes
import database as db
from config import (
    TRIVIA_QUESTIONS, TRUTH_QUESTIONS, DARE_CHALLENGES,
    MAGIC_8_BALL_ANSWERS, JOKES, HANGMAN_WORDS, HANGMAN_STAGES,
    FALLBACK_ANIME, JIKAN_API, CRICKETERS,
    RB_COINS_MIN, RB_COINS_MAX,
    RARITY_EMOJI, RARITY_WEIGHTS, ANIME_SERIES_TOTALS,
    get_cricketer_rarity,
)

# ── Active game state ─────────────────────────────────────────────────────────
active_trivia       = {}
active_hangman      = {}
active_tictactoe    = {}
active_cricket      = {}
active_pick         = {}
active_playcricket  = {}   # {chat_id: game_state}

_anime_cache: list = []

# ── Image lookup maps ─────────────────────────────────────────────────────────
_ANIME_IMAGE_MAP: dict = {c["name"]: c["image"] for c in FALLBACK_ANIME}
_CRICKETERS_WIKI_MAP: dict = {c["name"]: c["wiki_title"] for c in CRICKETERS}
_CRICKET_IMAGE_CACHE: dict = {}  # name -> url, populated lazily
_CARD_FILE_IDS: dict = {}         # item_name -> telegram file_id (from sent photos)

_COLLECTION_PAGE_SIZE = 8  # characters shown as buttons per page

# playcricket run photos: run_count (or "out") → cricketer name whose wiki photo is used
_PLAYCRICKET_RUN_PICS: dict = {
    1:     "MS Dhoni",           # singles master / running between wickets
    2:     "Rohit Sharma",       # two runs - stroke play
    3:     "Virat Kohli",        # three - aggressive running
    4:     "Sachin Tendulkar",   # classic boundary shot
    5:     "Brian Lara",         # five — Lara was good for rare runs
    6:     "Chris Gayle",        # six — sixer king
    "out": "Jasprit Bumrah",     # wicket — premier bowler
}


# ── Anime pool ────────────────────────────────────────────────────────────────
async def _fetch_anime_pool():
    global _anime_cache
    if _anime_cache:
        return _anime_cache
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            characters = []
            for page in range(1, 3):
                resp = await client.get(
                    f"{JIKAN_API}/top/characters",
                    params={"page": page, "limit": 25}
                )
                if resp.status_code != 200:
                    break
                for c in resp.json().get("data", []):
                    img  = c.get("images", {}).get("jpg", {}).get("image_url", "")
                    name = c.get("name", "")
                    if not (img and name and "questionmark" not in img):
                        continue
                    # Try to extract anime source from Jikan API response
                    anime_list = c.get("anime", [])
                    anime_src  = ""
                    if anime_list and isinstance(anime_list, list):
                        first = anime_list[0]
                        if isinstance(first, dict):
                            anime_src = first.get("anime", {}).get("title", "") or \
                                        first.get("title", "")
                    # Assign random rarity weighted toward Common
                    import random as _r
                    rarity = _r.choice(RARITY_WEIGHTS)
                    characters.append({
                        "name": name, "image": img,
                        "anime": anime_src or "Unknown Anime",
                        "rarity": rarity,
                    })
                await asyncio.sleep(0.4)
            if characters:
                _anime_cache = characters
                return _anime_cache
    except Exception:
        pass
    _anime_cache = list(FALLBACK_ANIME)
    return _anime_cache


# ── Photo helper: download image bytes and send reliably ─────────────────────
import logging as _logging
_photo_log = _logging.getLogger(__name__)

async def _send_photo_safe(context, chat_id: int, url: str, caption: str,
                           parse_mode: str = "HTML", reply_markup=None) -> bool:
    """Download image via httpx and send as bytes — avoids Telegram URL blocks. Retries once."""
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                )
                if resp.status_code == 200 and len(resp.content) > 500:
                    img = BytesIO(resp.content)
                    img.name = "photo.jpg"
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=img,
                        caption=caption,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                    )
                    return True
                else:
                    _photo_log.warning(f"Photo fetch failed (attempt {attempt+1}): status={resp.status_code} size={len(resp.content)} url={url[:80]}")
        except Exception as e:
            _photo_log.warning(f"Photo send error (attempt {attempt+1}): {e} url={url[:80]}")
        if attempt == 0:
            await asyncio.sleep(1)
    return False


# ── /dice  — animated Telegram dice 🎲 ───────────────────────────────────────
async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice_msg = await context.bot.send_dice(update.effective_chat.id, emoji="🎲")
    value = dice_msg.dice.value
    label = "🎉 Lucky six!" if value == 6 else ("Nice!" if value >= 4 else "")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Roll again", callback_data="dice_roll")]])
    await asyncio.sleep(3)
    await context.bot.send_message(
        update.effective_chat.id,
        f"You rolled a <b>{value}</b>! {label}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dice_msg = await context.bot.send_dice(query.message.chat_id, emoji="🎲")
    value = dice_msg.dice.value
    label = "🎉 Lucky six!" if value == 6 else ("Nice!" if value >= 4 else "")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Roll again", callback_data="dice_roll")]])
    await asyncio.sleep(3)
    await context.bot.send_message(
        query.message.chat_id,
        f"You rolled a <b>{value}</b>! {label}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ── /coinflip  — animated basketball 🏀 ──────────────────────────────────────
async def coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice_msg = await context.bot.send_dice(update.effective_chat.id, emoji="🏀")
    value = dice_msg.dice.value
    result = "🪙 Heads!" if value >= 4 else "🪙 Tails!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏀 Flip again", callback_data="coin_flip")]])
    await asyncio.sleep(3)
    await context.bot.send_message(
        update.effective_chat.id,
        f"<b>{result}</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def coin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dice_msg = await context.bot.send_dice(query.message.chat_id, emoji="🏀")
    value = dice_msg.dice.value
    result = "🪙 Heads!" if value >= 4 else "🪙 Tails!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏀 Flip again", callback_data="coin_flip")]])
    await asyncio.sleep(3)
    await context.bot.send_message(
        query.message.chat_id,
        f"<b>{result}</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ── /truth / /dare / /joke ────────────────────────────────────────────────────
async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(TRUTH_QUESTIONS)
    name = update.effective_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another one 🔄", callback_data="truth_new")]])
    await update.message.reply_text(
        f"🎭 <b>Truth for {name}</b>\n\n{question}",
        parse_mode="HTML", reply_markup=keyboard)


async def truth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    question = random.choice(TRUTH_QUESTIONS)
    name = query.from_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another one 🔄", callback_data="truth_new")]])
    await query.edit_message_text(
        f"🎭 <b>Truth for {name}</b>\n\n{question}",
        parse_mode="HTML", reply_markup=keyboard)


async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenge = random.choice(DARE_CHALLENGES)
    name = update.effective_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another one 🔄", callback_data="dare_new")]])
    await update.message.reply_text(
        f"🔥 <b>Dare for {name}</b>\n\n{challenge}",
        parse_mode="HTML", reply_markup=keyboard)


async def dare_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    challenge = random.choice(DARE_CHALLENGES)
    name = query.from_user.first_name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another one 🔄", callback_data="dare_new")]])
    await query.edit_message_text(
        f"🔥 <b>Dare for {name}</b>\n\n{challenge}",
        parse_mode="HTML", reply_markup=keyboard)


async def eight_ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎱 Ask me a yes/no question!\n<i>Usage: /8ball will I win today?</i>",
            parse_mode="HTML")
        return
    question = " ".join(context.args)
    answer = random.choice(MAGIC_8_BALL_ANSWERS)
    await update.message.reply_text(
        f"🎱 <b>Question:</b> {question}\n\n<b>Magic 8-Ball says:</b>\n<i>{answer}</i>",
        parse_mode="HTML")


async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    j = random.choice(JOKES)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another joke 😂", callback_data="joke_new")]])
    await update.message.reply_text(j, parse_mode="HTML", reply_markup=keyboard)


async def joke_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    j = random.choice(JOKES)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another joke 😂", callback_data="joke_new")]])
    await query.edit_message_text(j, parse_mode="HTML", reply_markup=keyboard)


# ── /love ─────────────────────────────────────────────────────────────────────
async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "💘 Usage: /love @username\nOr reply to someone's message.")
        return
    user1 = update.effective_user.first_name
    if update.message.reply_to_message:
        user2 = update.message.reply_to_message.from_user.first_name
    else:
        user2 = context.args[0].lstrip("@")
    pct = random.randint(1, 100)
    filled = int(pct / 10)
    bar = "❤️" * filled + "🖤" * (10 - filled)
    if pct >= 80:
        verdict = "Perfect match! 💑"
    elif pct >= 60:
        verdict = "Good chemistry! 💕"
    elif pct >= 40:
        verdict = "There's potential. 💞"
    else:
        verdict = "Maybe just friends. 🤝"
    await update.message.reply_text(
        f"💘 <b>Love Calculator</b>\n\n"
        f"{user1} + {user2}\n\n"
        f"{bar}\n\n"
        f"<b>{pct}%</b> — {verdict}",
        parse_mode="HTML")


# ── /meme ─────────────────────────────────────────────────────────────────────
async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get("https://meme-api.com/gimme")
            data = resp.json()
            url = data.get("url", "")
            title = data.get("title", "Meme")
            if url:
                await update.message.reply_photo(
                    photo=url, caption=f"😂 <b>{title}</b>", parse_mode="HTML")
                return
    except Exception:
        pass
    await update.message.reply_text("Could not fetch a meme right now. Try again!")


# ── /poll ─────────────────────────────────────────────────────────────────────
async def poll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /poll [your question]\nExample: /poll Best anime?")
        return
    question = " ".join(context.args)
    if len(question) > 300:
        await update.message.reply_text("Question is too long (max 300 characters).")
        return
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=["Yes ✅", "No ❌", "Maybe 🤔"],
        is_anonymous=False,
    )


# ── /top ──────────────────────────────────────────────────────────────────────
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = db.get_top_scores(update.effective_chat.id)
    if not scores:
        await update.message.reply_text("No trivia scores yet.\nStart a game with /trivia!")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["<b>Top Trivia Players</b>\n━━━━━━━━━━━━━━━━\n"]
    for i, row in enumerate(scores):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["username"] or f"User{row['user_id']}"
        lines.append(f"{medal} {name} — <b>{row['trivia_score']}</b> pts")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── /trivia ───────────────────────────────────────────────────────────────────
async def trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_trivia:
        item = active_trivia[chat_id]
        await update.message.reply_text(
            f"A trivia game is already active!\n\n<b>Question:</b> {item['q']}",
            parse_mode="HTML")
        return
    item = random.choice(TRIVIA_QUESTIONS)
    active_trivia[chat_id] = item
    await update.message.reply_text(
        f"🧠 <b>Trivia Time!</b>\n━━━━━━━━━━━━━━━━\n\n{item['q']}\n\n"
        f"<i>First correct answer wins a point!</i>",
        parse_mode="HTML")


async def trivia_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in active_trivia:
        return
    user_answer = update.message.text.strip().lower()
    correct = active_trivia[chat_id]["a"].lower()
    if user_answer == correct or correct in user_answer:
        user = update.effective_user
        username = user.username or user.first_name
        db.add_trivia_score(user.id, chat_id, username)
        del active_trivia[chat_id]
        await update.message.reply_text(
            f"✅ Correct! <a href='tg://user?id={user.id}'>{user.first_name}</a> got it "
            f"and earned <b>1 point</b>!\nAnswer: <b>{correct.title()}</b>",
            parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Wrong! Keep trying...")


# ── /hangman ─────────────────────────────────────────────────────────────────
async def hangman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_hangman:
        game = active_hangman[chat_id]
        display = " ".join([c if c in game["guessed"] else "_" for c in game["word"]])
        stage = HANGMAN_STAGES[game["wrong"]]
        letters = ", ".join(sorted(game["guessed"])) or "none"
        setter_info = f"\nWord set by: <b>{game['setter_name']}</b>" if game.get("setter_name") else ""
        await update.message.reply_text(
            f"<b>Hangman</b> — game in progress{setter_info}\n\n"
            f"{stage}\n"
            f"Word: <code>{display}</code>\n"
            f"Wrong: <b>{game['wrong']}/6</b>\n"
            f"Tried: {letters}",
            parse_mode="HTML")
        return
    word = random.choice(HANGMAN_WORDS)
    active_hangman[chat_id] = {
        "word": word, "guessed": set(), "wrong": 0,
        "setter_id": None, "setter_name": None
    }
    display = " ".join(["_"] * len(word))
    await update.message.reply_text(
        f"🪢 <b>Hangman started!</b>\n\n"
        f"{HANGMAN_STAGES[0]}\n"
        f"Word: <code>{display}</code> ({len(word)} letters)\n\n"
        f"<i>Type a single letter to guess!</i>",
        parse_mode="HTML")


async def hangman_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in active_hangman:
        return
    text = update.message.text.strip().lower()
    if len(text) != 1 or not text.isalpha():
        return
    game = active_hangman[chat_id]
    user = update.effective_user

    if game.get("setter_id") and user.id == game["setter_id"]:
        await update.message.reply_text("You set this word — you cannot guess it! 😄")
        return

    letter = text
    if letter in game["guessed"]:
        await update.message.reply_text(
            f"<code>{letter}</code> was already guessed!", parse_mode="HTML")
        return

    game["guessed"].add(letter)
    correct_guess = letter in game["word"]
    if not correct_guess:
        game["wrong"] += 1

    display = " ".join([c if c in game["guessed"] else "_" for c in game["word"]])
    stage = HANGMAN_STAGES[min(game["wrong"], 6)]
    letters = ", ".join(sorted(game["guessed"]))

    if "_" not in display:
        del active_hangman[chat_id]
        await update.message.reply_text(
            f"🎉 <b>You won!</b> The word was: <code>{game['word']}</code>\n"
            f"Well done, {user.first_name}!",
            parse_mode="HTML")
        return
    if game["wrong"] >= 6:
        word = game["word"]
        del active_hangman[chat_id]
        await update.message.reply_text(
            f"{HANGMAN_STAGES[6]}\n\n💀 <b>Game over!</b> The word was: <code>{word}</code>",
            parse_mode="HTML")
        return

    result = "✅ Correct!" if correct_guess else f"❌ <code>{letter}</code> is not in the word."
    await update.message.reply_text(
        f"{stage}\n"
        f"{result}\n"
        f"Word: <code>{display}</code>\n"
        f"Wrong: <b>{game['wrong']}/6</b>\n"
        f"Tried: {letters}",
        parse_mode="HTML")


# ── /wordmaster ───────────────────────────────────────────────────────────────
async def wordmaster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Use /wordmaster in a group. You set a secret word and others guess it!")
        return
    if chat_id in active_hangman:
        await update.message.reply_text(
            "A hangman game is already running. Finish it first with /hangman.")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /wordmaster [secret word]\nExample: /wordmaster PYTHON",
            parse_mode="HTML")
        return

    word = context.args[0].lower()
    if not word.isalpha():
        await update.message.reply_text("Please use a single word with letters only.")
        return
    if len(word) < 2 or len(word) > 25:
        await update.message.reply_text("Word must be between 2 and 25 letters.")
        return

    setter = update.effective_user
    try:
        await update.message.delete()
    except Exception:
        pass

    active_hangman[chat_id] = {
        "word": word, "guessed": set(), "wrong": 0,
        "setter_id": setter.id, "setter_name": setter.first_name
    }
    display = " ".join(["_"] * len(word))
    await context.bot.send_message(
        chat_id,
        f"🧩 <b>Word Master!</b>\n\n"
        f"<a href='tg://user?id={setter.id}'>{setter.first_name}</a> set a secret word!\n\n"
        f"{HANGMAN_STAGES[0]}\n"
        f"Word: <code>{display}</code> ({len(word)} letters)\n\n"
        f"<i>Type a single letter to guess! The setter cannot guess their own word.</i>",
        parse_mode="HTML")


# ── /tictactoe ────────────────────────────────────────────────────────────────
def _build_ttt_keyboard(board):
    symbols = {"X": "✖️", "O": "⭕", " ": " "}
    cells = []
    for i, cell in enumerate(board):
        label = symbols.get(cell, " ") if cell != " " else str(i + 1)
        cells.append(InlineKeyboardButton(label, callback_data=f"ttt_{i}"))
    return InlineKeyboardMarkup([cells[0:3], cells[3:6], cells[6:9]])


def _check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] != " ":
            return board[a]
    if " " not in board:
        return "draw"
    return None


def _smart_bot_move(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for mark in ["O", "X"]:
        for a, b, c in wins:
            cells = [board[a], board[b], board[c]]
            empty = [x for x, v in zip([a,b,c], cells) if v == " "]
            if cells.count(mark) == 2 and len(empty) == 1:
                return empty[0]
    if board[4] == " ":
        return 4
    corners = [i for i in [0, 2, 6, 8] if board[i] == " "]
    if corners:
        return random.choice(corners)
    return random.choice([i for i, v in enumerate(board) if v == " "])


async def tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in active_tictactoe:
        await update.message.reply_text("A Tic-Tac-Toe game is already running! Finish it first.")
        return

    target = None
    if update.message.reply_to_message and not update.message.reply_to_message.from_user.is_bot:
        target = update.message.reply_to_message.from_user
    elif context.args:
        uname = context.args[0].lstrip("@")
        try:
            m = await context.bot.get_chat_member(chat_id, uname)
            if not m.user.is_bot:
                target = m.user
        except Exception:
            pass

    if target and target.id == user.id:
        target = None

    if target:
        active_tictactoe[chat_id] = {
            "mode": "pending",
            "board": [" "] * 9,
            "player1_id": user.id,
            "player1_name": user.first_name,
            "player2_id": target.id,
            "player2_name": target.first_name,
            "current_turn": 1,
        }
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Accept", callback_data="ttt_accept"),
            InlineKeyboardButton("❌ Decline", callback_data="ttt_decline"),
        ]])
        await update.message.reply_text(
            f"⚔️ <b>Tic-Tac-Toe Challenge!</b>\n\n"
            f"<a href='tg://user?id={user.id}'>{user.first_name}</a> challenges "
            f"<a href='tg://user?id={target.id}'>{target.first_name}</a>!\n\n"
            f"<a href='tg://user?id={target.id}'>{target.first_name}</a>, do you accept?",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        board = [" "] * 9
        active_tictactoe[chat_id] = {
            "mode": "bot",
            "board": board,
            "player1_id": user.id,
            "player1_name": user.first_name,
            "player2_id": None,
            "player2_name": "Bot",
            "current_turn": 1,
        }
        await update.message.reply_text(
            f"✖️ <b>Tic-Tac-Toe</b>\n"
            f"{user.first_name} (✖️) vs Bot (⭕)\n\nYour turn — tap a cell!",
            parse_mode="HTML",
            reply_markup=_build_ttt_keyboard(board))


async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    clicker = query.from_user
    data = query.data

    if chat_id not in active_tictactoe:
        await query.answer("No active game.", show_alert=True)
        return

    game = active_tictactoe[chat_id]

    if data == "ttt_accept":
        if clicker.id != game["player2_id"]:
            await query.answer("This challenge is not for you!", show_alert=True)
            return
        game["mode"] = "pvp"
        board = game["board"]
        p1_id   = game["player1_id"]
        p1_name = game["player1_name"]
        p2_id   = game["player2_id"]
        p2_name = game["player2_name"]
        await query.edit_message_text(
            f"✖️ <b>Tic-Tac-Toe — Player vs Player</b>\n\n"
            f"<a href='tg://user?id={p1_id}'>{p1_name}</a> (✖️) vs "
            f"<a href='tg://user?id={p2_id}'>{p2_name}</a> (⭕)\n\n"
            f"<b>{p1_name}</b>'s turn (✖️) — tap a cell!",
            parse_mode="HTML",
            reply_markup=_build_ttt_keyboard(board))
        return

    if data == "ttt_decline":
        if clicker.id != game["player2_id"]:
            await query.answer("This challenge is not for you!", show_alert=True)
            return
        del active_tictactoe[chat_id]
        await query.edit_message_text(f"❌ <b>{game['player2_name']}</b> declined the challenge.")
        return

    await query.answer()
    if game["mode"] == "pending":
        await query.answer("Waiting for the challenge to be accepted!", show_alert=True)
        return

    idx = int(data.split("_")[1])
    board = game["board"]
    if board[idx] != " ":
        await query.answer("That cell is already taken!", show_alert=True)
        return

    mode = game["mode"]
    turn = game["current_turn"]

    if mode == "bot":
        if clicker.id != game["player1_id"]:
            await query.answer("This is not your game!", show_alert=True)
            return
        board[idx] = "X"
        winner = _check_winner(board)
        if winner:
            del active_tictactoe[chat_id]
            msg = (f"🎉 <b>You win!</b> Well played, {game['player1_name']}!"
                   if winner == "X" else "🤝 <b>It's a draw!</b>")
            await query.edit_message_text(msg, parse_mode="HTML",
                                          reply_markup=_build_ttt_keyboard(board))
            return
        bot_move = _smart_bot_move(board)
        board[bot_move] = "O"
        winner = _check_winner(board)
        if winner:
            del active_tictactoe[chat_id]
            msg = ("🤖 <b>Bot wins!</b> Better luck next time."
                   if winner == "O" else "🤝 <b>It's a draw!</b>")
            await query.edit_message_text(msg, parse_mode="HTML",
                                          reply_markup=_build_ttt_keyboard(board))
            return
        await query.edit_message_text(
            f"✖️ <b>Tic-Tac-Toe</b>\n"
            f"{game['player1_name']} (✖️) vs Bot (⭕)\n\nYour turn!",
            parse_mode="HTML",
            reply_markup=_build_ttt_keyboard(board))
    else:
        if turn == 1 and clicker.id != game["player1_id"]:
            await query.answer(f"It's {game['player1_name']}'s turn (✖️)!", show_alert=True)
            return
        if turn == 2 and clicker.id != game["player2_id"]:
            await query.answer(f"It's {game['player2_name']}'s turn (⭕)!", show_alert=True)
            return

        mark = "X" if turn == 1 else "O"
        board[idx] = mark
        winner = _check_winner(board)
        p1_id   = game["player1_id"]
        p1_name = game["player1_name"]
        p2_id   = game["player2_id"]
        p2_name = game["player2_name"]
        if winner:
            del active_tictactoe[chat_id]
            if winner == "draw":
                msg = "🤝 <b>It's a draw!</b>"
            elif winner == "X":
                msg = f"🎉 <a href='tg://user?id={p1_id}'>{p1_name}</a> wins! (✖️)"
            else:
                msg = f"🎉 <a href='tg://user?id={p2_id}'>{p2_name}</a> wins! (⭕)"
            await query.edit_message_text(msg, parse_mode="HTML",
                                          reply_markup=_build_ttt_keyboard(board))
            return

        game["current_turn"] = 2 if turn == 1 else 1
        next_id   = p2_id   if turn == 1 else p1_id
        next_name = p2_name if turn == 1 else p1_name
        next_mark = "⭕" if turn == 1 else "✖️"
        await query.edit_message_text(
            f"✖️ <b>Tic-Tac-Toe — PvP</b>\n\n"
            f"<a href='tg://user?id={p1_id}'>{p1_name}</a> (✖️) vs "
            f"<a href='tg://user?id={p2_id}'>{p2_name}</a> (⭕)\n\n"
            f"<a href='tg://user?id={next_id}'>{next_name}</a>'s turn ({next_mark})",
            parse_mode="HTML",
            reply_markup=_build_ttt_keyboard(board))


# ── /rps ──────────────────────────────────────────────────────────────────────
async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🪨 Rock",     callback_data="rps_rock"),
        InlineKeyboardButton("📄 Paper",    callback_data="rps_paper"),
        InlineKeyboardButton("✂️ Scissors", callback_data="rps_scissors"),
    ]])
    if context.args:
        move = context.args[0].lower()
        if move in ("rock", "paper", "scissors"):
            await _resolve_rps(update.message, move, update.effective_user.first_name)
            return
    await update.message.reply_text(
        "🎮 <b>Rock Paper Scissors</b>\nChoose your move!",
        parse_mode="HTML", reply_markup=keyboard)


async def rps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    move = query.data.replace("rps_", "")
    await _resolve_rps(query.message, move, query.from_user.first_name, edit=True)


async def _resolve_rps(message, move, name, edit=False):
    bot_move = random.choice(["rock", "paper", "scissors"])
    icons = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    outcomes = {
        ("rock", "scissors"): "win", ("paper", "rock"): "win",
        ("scissors", "paper"): "win", ("rock", "paper"): "lose",
        ("paper", "scissors"): "lose", ("scissors", "rock"): "lose",
    }
    result = outcomes.get((move, bot_move), "draw")
    result_text = {"win": "🎉 <b>You win!</b>",
                   "lose": "🤖 <b>Bot wins!</b>",
                   "draw": "🤝 <b>It's a draw!</b>"}[result]
    text = (
        f"🎮 <b>Rock Paper Scissors</b>\n\n"
        f"You: {icons[move]} {move.title()}\n"
        f"Bot: {icons[bot_move]} {bot_move.title()}\n\n"
        f"{result_text}"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🪨", callback_data="rps_rock"),
        InlineKeyboardButton("📄", callback_data="rps_paper"),
        InlineKeyboardButton("✂️", callback_data="rps_scissors"),
    ]])
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


# ── /cricket — guess the cricketer ───────────────────────────────────────────

async def _cricket_timeout(context) -> None:
    """Job: fire when 60 s passes with no correct answer."""
    data    = context.job.data
    chat_id = data["chat_id"]
    display = data["display"]
    if chat_id in active_cricket:
        del active_cricket[chat_id]
        try:
            await context.bot.send_message(
                chat_id,
                f"⏱ <b>Time's up!</b> Nobody guessed it in 60 seconds.\n"
                f"The cricketer was: <b>{display}</b> 🏏",
                parse_mode="HTML",
            )
        except Exception:
            pass


async def _fetch_wiki_image(wiki_title: str) -> str | None:
    """Fetch the thumbnail image URL for a Wikipedia page via REST API."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}",
                headers={"User-Agent": "TelegramBot/1.0 (cricket-game)"}
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("originalimage", {}).get("source") or \
                       data.get("thumbnail", {}).get("source")
    except Exception:
        pass
    return None


async def cricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_cricket:
        item = active_cricket[chat_id]
        words = item["display"].split()
        hint  = "  ".join(w[0].upper() + " " + "_ " * (len(w) - 1) for w in words)
        await update.message.reply_text(
            f"🏏 A cricket game is already active!\n"
            f"Hint: <code>{hint.strip()}</code>\n\n"
            f"<i>Type the player's name to answer!  ⏱ 60 s per round.</i>",
            parse_mode="HTML")
        return

    player = random.choice(CRICKETERS)
    active_cricket[chat_id] = {
        "answer":  player["name"].lower(),
        "display": player["name"],
    }

    words       = player["name"].split()
    hint        = "  ".join(w[0].upper() + " " + "_ " * (len(w) - 1) for w in words)
    num_letters = sum(len(w) for w in words)

    caption = (
        f"🏏 <b>Guess the Cricketer!</b>\n\n"
        f"🔤 Hint: <code>{hint.strip()}</code>\n"
        f"📝 {len(words)} word(s) · {num_letters} letters total\n"
        f"⏱ <i>60 seconds to answer!</i>\n\n"
        f"<i>Type the player's name in chat!</i>"
    )

    # Fetch live image from Wikipedia REST API
    image_url = await _fetch_wiki_image(player["wiki_title"])
    sent = False
    if image_url:
        sent = await _send_photo_safe(context, chat_id, image_url, caption)

    if not sent:
        await update.message.reply_text(caption, parse_mode="HTML")

    # Schedule 60-second timeout
    job_name = f"cricket_timeout_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(job_name):
        j.schedule_removal()
    context.job_queue.run_once(
        _cricket_timeout,
        when=60,
        data={"chat_id": chat_id, "display": player["name"]},
        name=job_name,
    )


async def cricket_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in active_cricket:
        return
    user_answer = update.message.text.strip().lower()
    correct     = active_cricket[chat_id]["answer"]
    display     = active_cricket[chat_id]["display"]
    user        = update.effective_user
    name        = user.first_name

    correct_parts = correct.split()
    match = (
        user_answer == correct
        or correct in user_answer
        or user_answer in correct
        or any(user_answer == part for part in correct_parts)
    )
    if match:
        del active_cricket[chat_id]
        # Cancel timeout job
        for j in context.job_queue.get_jobs_by_name(f"cricket_timeout_{chat_id}"):
            j.schedule_removal()
        # Award RB coins (3–5 randomly)
        coins_earned = random.randint(RB_COINS_MIN, RB_COINS_MAX)
        total_coins  = db.add_rb_coins(user.id, coins_earned)
        # Determine rarity
        rarity      = get_cricketer_rarity(display)
        rarity_icon = RARITY_EMOJI.get(rarity, "🔵")
        # Add cricketer to collection with rarity
        db.add_to_collection(user.id, "cricketer", display, rarity=rarity, source="Cricket")
        await update.message.reply_text(
            f"<a href='tg://user?id={user.id}'>{name}</a>, ʏᴏᴜ ɢᴏᴛ ᴀ ɴᴇᴡ ᴄʀɪᴄᴋᴇᴛᴇʀ!\n\n"
            f"🏏 Nᴀᴍᴇ: <b>{display}</b>\n"
            f"{rarity_icon} 𝙍𝘼𝙍𝙄𝙏𝙔: <b>{rarity}</b>\n"
            f"🌍 Sᴘᴏʀᴛ: <b>Cricket</b>\n\n"
            f"🪙 +{coins_earned} RB Coins! (Total: <b>{total_coins}</b>)\n\n"
            f"❄️ ᴄʜᴇᴄᴋ ʏᴏᴜʀ /harem!",
            parse_mode="HTML",
        )
    elif len(user_answer) > 1:
        await update.message.reply_text("❌ Wrong! Keep guessing...")


# ── /coins ────────────────────────────────────────────────────────────────────

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a user's RB coin balance."""
    user = update.effective_user

    # If replied to someone or @mentioned, show their balance
    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            uname  = context.args[0].lstrip("@")
            member = await context.bot.get_chat_member(update.effective_chat.id, uname)
            target = member.user
        except Exception:
            pass

    if not target:
        target = user

    balance  = db.get_rb_coins(target.id)
    is_self  = target.id == user.id
    name_str = "You have" if is_self else f"{target.first_name} has"

    await update.message.reply_text(
        f"🪙 <b>RB Coins</b>\n\n"
        f"{name_str} <b>{balance}</b> RB coin{'s' if balance != 1 else ''}.\n\n"
        f"<i>Earn coins by guessing cricketers correctly with /cricket!</i>",
        parse_mode="HTML",
    )


# ── /rb_leaderboard ───────────────────────────────────────────────────────────

async def rb_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the global RB coins leaderboard."""
    rows = db.get_rb_leaderboard(limit=10)
    if not rows:
        await update.message.reply_text(
            "🪙 No one has earned RB coins yet!\n\n"
            "Be the first — guess a cricketer with /cricket!",
        )
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = ["🪙 <b>RB Coins Leaderboard</b>", "━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        uid   = row["user_id"]
        # Try to get a display name from the known_users collection if available
        uname = f"User {uid}"
        try:
            from database import _get_db
            udoc = _get_db().known_users.find_one({"user_id": uid})
            if udoc:
                uname = udoc.get("first_name") or udoc.get("username") or uname
        except Exception:
            pass
        lines.append(f"{medal} {uname} — <b>{row['coins']}</b> coins")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── /pick ─────────────────────────────────────────────────────────────────────
async def pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_pick:
        await update.message.reply_text("A pick game is already active! Finish it first.")
        return

    pool = await _fetch_anime_pool()
    if len(pool) < 4:
        await update.message.reply_text("Not enough characters loaded. Try again in a moment.")
        return

    char = random.choice(pool)
    wrong_pool = [c for c in pool if c["name"] != char["name"]]
    wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
    options = [char["name"]] + [w["name"] for w in wrong]
    random.shuffle(options)
    correct_idx = options.index(char["name"])
    active_pick[chat_id] = {"answer": char["name"], "correct_idx": correct_idx, "options": options}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(options[0], callback_data="pick_0"),
         InlineKeyboardButton(options[1], callback_data="pick_1")],
        [InlineKeyboardButton(options[2], callback_data="pick_2"),
         InlineKeyboardButton(options[3], callback_data="pick_3")],
    ])
    sent = await _send_photo_safe(
        context, chat_id, char["image"],
        caption="👆 <b>Who is this character?</b>\nTap the correct name below!",
        reply_markup=keyboard
    )
    if not sent:
        await update.message.reply_text(
            "👆 <b>Who is this character?</b>\nTap the correct name below!",
            parse_mode="HTML",
            reply_markup=keyboard)


async def pick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id

    if chat_id not in active_pick:
        await query.answer("This game has already ended.", show_alert=True)
        return

    game = active_pick[chat_id]
    idx = int(query.data.replace("pick_", ""))
    chosen  = game["options"][idx]
    correct = game["answer"]
    name    = query.from_user.first_name

    del active_pick[chat_id]

    if chosen == correct:
        db.add_to_collection(query.from_user.id, "anime", correct)
        await query.answer("✅ Correct!", show_alert=False)
        try:
            await query.edit_message_caption(
                f"✅ Correct! <a href='tg://user?id={query.from_user.id}'>{name}</a> got it!\n"
                f"The character was: <b>{correct}</b>\n<i>Added to your collection!</i>",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await query.answer(f"❌ Wrong! It was {correct}", show_alert=True)
        try:
            await query.edit_message_caption(
                f"❌ <b>{name}</b> guessed wrong.\nThe character was: <b>{correct}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# /playcricket — Full Hand Cricket PvP Game
# ══════════════════════════════════════════════════════════════════════════════
#
# HOW TO PLAY:
#   1. /playcricket @username  →  sends a challenge with Accept / Decline buttons
#   2. Challenged player accepts
#   3. Toss is done automatically — winner sees Bat / Bowl buttons
#   4. Once choice is made, the BATSMAN sees 1–6 number buttons
#   5. After batsman picks, the BOWLER sees 1–6 number buttons
#   6. Same number = OUT (innings ends)
#   7. Different = batsman scores that many runs
#   8. After 1st innings, swap roles for 2nd innings
#   9. Chase the target to win. If OUT before reaching target, you lose!

def _cg_bat_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    row1 = [InlineKeyboardButton(str(n), callback_data=f"cg_bp_{n}_{chat_id}") for n in range(1, 4)]
    row2 = [InlineKeyboardButton(str(n), callback_data=f"cg_bp_{n}_{chat_id}") for n in range(4, 7)]
    return InlineKeyboardMarkup([row1, row2])


def _cg_bowl_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    row1 = [InlineKeyboardButton(str(n), callback_data=f"cg_wbp_{n}_{chat_id}") for n in range(1, 4)]
    row2 = [InlineKeyboardButton(str(n), callback_data=f"cg_wbp_{n}_{chat_id}") for n in range(4, 7)]
    return InlineKeyboardMarkup([row1, row2])


def _cg_scorecard(game: dict) -> str:
    p1_id   = game["player1_id"]
    p2_id   = game["player2_id"]
    p1_name = game["player1_name"]
    p2_name = game["player2_name"]
    s1 = game["score"][p1_id]
    s2 = game["score"][p2_id]
    b1 = game["balls_faced"][p1_id]
    b2 = game["balls_faced"][p2_id]
    o1 = "⚡ OUT" if game["out"][p1_id] else f"{b1} balls"
    o2 = "⚡ OUT" if game["out"][p2_id] else f"{b2} balls"
    return (
        f"📊 <b>Score</b>\n"
        f"🏏 <a href='tg://user?id={p1_id}'>{p1_name}</a>: <b>{s1}</b> ({o1})\n"
        f"🏏 <a href='tg://user?id={p2_id}'>{p2_name}</a>: <b>{s2}</b> ({o2})\n"
    )


async def playcricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user    = update.effective_user

    if update.effective_chat.type == "private":
        await update.message.reply_text("🏏 Use /playcricket in a group to challenge another player!")
        return

    if chat_id in active_playcricket:
        await update.message.reply_text("🏏 A cricket match is already in progress! Finish it first.")
        return

    target = None
    if update.message.reply_to_message and not update.message.reply_to_message.from_user.is_bot:
        target = update.message.reply_to_message.from_user
    elif context.args:
        uname = context.args[0].lstrip("@")
        try:
            m = await context.bot.get_chat_member(chat_id, uname)
            if not m.user.is_bot:
                target = m.user
        except Exception:
            pass

    if not target or target.id == user.id:
        await update.message.reply_text(
            "🏏 <b>Hand Cricket</b>\n\n"
            "Challenge another player!\n"
            "Usage: <code>/playcricket @username</code>\n"
            "Or reply to someone's message with /playcricket",
            parse_mode="HTML"
        )
        return

    active_playcricket[chat_id] = {
        "phase":        "pending",
        "player1_id":   user.id,
        "player1_name": user.first_name,
        "player2_id":   target.id,
        "player2_name": target.first_name,
        "toss_winner":  None,
        "batter_id":    None,
        "bowler_id":    None,
        "innings":      1,
        "score":        {user.id: 0, target.id: 0},
        "out":          {user.id: False, target.id: False},
        "balls_faced":  {user.id: 0, target.id: 0},
        "bat_pick":     None,
        "bowl_pick":    None,
        "target":       None,
    }

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"cg_acc_{chat_id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"cg_dec_{chat_id}"),
    ]])
    await update.message.reply_text(
        f"🏏 <b>Hand Cricket Challenge!</b>\n\n"
        f"<a href='tg://user?id={user.id}'>{user.first_name}</a> has challenged "
        f"<a href='tg://user?id={target.id}'>{target.first_name}</a> to a match!\n\n"
        f"<a href='tg://user?id={target.id}'>{target.first_name}</a>, do you accept? 🎯",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def cg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    clicker = query.from_user
    data    = query.data
    chat_id = query.message.chat_id

    if chat_id not in active_playcricket:
        await query.answer("This game has already ended.", show_alert=True)
        return

    game    = active_playcricket[chat_id]
    p1_id   = game["player1_id"]
    p1_name = game["player1_name"]
    p2_id   = game["player2_id"]
    p2_name = game["player2_name"]

    # ── Accept / Decline ──────────────────────────────────────────────────────
    if data == f"cg_acc_{chat_id}":
        if clicker.id != p2_id:
            await query.answer("This challenge is not for you!", show_alert=True)
            return
        await query.answer("Game on! 🏏")
        toss_winner_id   = random.choice([p1_id, p2_id])
        toss_winner_name = p1_name if toss_winner_id == p1_id else p2_name
        game["phase"]       = "toss"
        game["toss_winner"] = toss_winner_id

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏏 Bat", callback_data=f"cg_bat_{chat_id}"),
            InlineKeyboardButton("🎳 Bowl", callback_data=f"cg_bowl_{chat_id}"),
        ]])
        await query.edit_message_text(
            f"🏏 <b>Hand Cricket — Match Started!</b>\n\n"
            f"🪙 <b>Toss Result:</b> "
            f"<a href='tg://user?id={toss_winner_id}'>{toss_winner_name}</a> won the toss!\n\n"
            f"<a href='tg://user?id={toss_winner_id}'>{toss_winner_name}</a>, choose to Bat or Bowl:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    if data == f"cg_dec_{chat_id}":
        if clicker.id != p2_id:
            await query.answer("This challenge is not for you!", show_alert=True)
            return
        del active_playcricket[chat_id]
        await query.edit_message_text(f"❌ <b>{p2_name}</b> declined the cricket challenge.")
        return

    # ── Bat / Bowl choice after toss ─────────────────────────────────────────
    if data == f"cg_bat_{chat_id}":
        if clicker.id != game.get("toss_winner"):
            await query.answer("Only the toss winner can choose!", show_alert=True)
            return
        tw = game["toss_winner"]
        game["batter_id"] = tw
        game["bowler_id"] = p1_id if tw == p2_id else p2_id
        game["phase"] = "batting_pick"
        await _send_batting_prompt(query, context, chat_id, game, edited=True)
        return

    if data == f"cg_bowl_{chat_id}":
        if clicker.id != game.get("toss_winner"):
            await query.answer("Only the toss winner can choose!", show_alert=True)
            return
        tw = game["toss_winner"]
        game["bowler_id"] = tw
        game["batter_id"] = p1_id if tw == p2_id else p2_id
        game["phase"] = "batting_pick"
        await _send_batting_prompt(query, context, chat_id, game, edited=True)
        return

    # ── Batsman picks 1–6 ─────────────────────────────────────────────────────
    if data.startswith("cg_bp_") and f"_{chat_id}" in data:
        batter_id = game.get("batter_id")
        if clicker.id != batter_id:
            batter_name = p1_name if batter_id == p1_id else p2_name
            await query.answer(f"Only the batsman ({batter_name}) picks here!", show_alert=True)
            return
        if game["phase"] != "batting_pick":
            await query.answer("Not your pick right now.", show_alert=True)
            return
        # parse number from "cg_bp_<n>_<chat_id>"
        parts = data[len("cg_bp_"):].split("_")
        n = int(parts[0])
        game["bat_pick"] = n
        game["phase"] = "bowling_pick"
        await query.answer(f"You picked {n}! 🤫 Waiting for the bowler…")

        batter_name = p1_name if batter_id == p1_id else p2_name
        bowler_id   = game["bowler_id"]
        bowler_name = p1_name if bowler_id == p1_id else p2_name
        ball_num    = game["balls_faced"][batter_id] + 1

        await query.edit_message_text(
            f"🏏 <b>Ball {ball_num}</b>\n\n"
            f"Batsman <b>{batter_name}</b> has chosen! 🤫\n\n"
            f"Now <a href='tg://user?id={bowler_id}'>{bowler_name}</a> "
            f"(🎳 Bowler), pick your delivery:",
            parse_mode="HTML",
            reply_markup=_cg_bowl_keyboard(chat_id),
        )
        return

    # ── Bowler picks 1–6 ──────────────────────────────────────────────────────
    if data.startswith("cg_wbp_") and f"_{chat_id}" in data:
        bowler_id = game.get("bowler_id")
        if clicker.id != bowler_id:
            bowler_name = p1_name if bowler_id == p1_id else p2_name
            await query.answer(f"Only the bowler ({bowler_name}) picks here!", show_alert=True)
            return
        if game["phase"] != "bowling_pick":
            await query.answer("Not your pick right now.", show_alert=True)
            return
        parts = data[len("cg_wbp_"):].split("_")
        n = int(parts[0])
        game["bowl_pick"] = n
        await query.answer(f"You bowled {n}!")
        await _process_ball(query, context, chat_id, game)
        return

    await query.answer()


async def _send_batting_prompt(query_or_msg, context, chat_id: int, game: dict, edited: bool = False):
    batter_id   = game["batter_id"]
    batter_name = game["player1_name"] if batter_id == game["player1_id"] else game["player2_name"]
    bowler_id   = game["bowler_id"]
    bowler_name = game["player1_name"] if bowler_id == game["player1_id"] else game["player2_name"]
    innings_label = "1st Innings" if game["innings"] == 1 else "2nd Innings"
    target_line = ""
    if game["innings"] == 2 and game["target"] is not None:
        target_line = f"\n🎯 <b>Target:</b> {game['target']} runs"

    text = (
        f"🏏 <b>Hand Cricket — {innings_label}</b>{target_line}\n\n"
        f"🏃 Batsman: <a href='tg://user?id={batter_id}'>{batter_name}</a>\n"
        f"🎳 Bowler:  <a href='tg://user?id={bowler_id}'>{bowler_name}</a>\n\n"
        f"<a href='tg://user?id={batter_id}'>{batter_name}</a>, pick your shot (1–6) 👇"
    )
    keyboard = _cg_bat_keyboard(chat_id)

    if edited and hasattr(query_or_msg, "edit_message_text"):
        await query_or_msg.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)


_CRICKET_CHANNEL_PHOTOS: dict = {
    "out": ("@PokeParadoxgroupoffical", 5093),
    4:     ("@PokeParadoxgroupoffical", 5094),
    6:     ("@PokeParadoxgroupoffical", 5096),
    3:     ("@PokeParadoxgroupoffical", 5097),
    5:     ("@PokeParadoxgroupoffical", 5097),
    1:     ("@hexaempire", 154729),
    2:     ("@hexaempire", 154729),
}

async def _send_playcricket_photo(context, chat_id: int, run_key) -> None:
    """Send a cricket action photo via copy_message from source channels."""
    captions = {
        1:     "🏃 <b>Single!</b> Running hard between the wickets",
        2:     "2️⃣ <b>Two runs!</b> Great calling and running",
        3:     "3️⃣ <b>Three!</b> Brilliant running — outstanding effort",
        4:     "🏏 <b>FOUR!</b> Ball races to the boundary! 🎯",
        5:     "5️⃣ <b>Five runs!</b> Extremely rare — incredible hit!",
        6:     "🚀 <b>SIX!</b> Maximum! Ball is out of the ground! 💥🎆",
        "out": "💥 <b>WICKET!</b> Bowler celebrates — batter walks back!",
    }
    caption = captions.get(run_key, "🏏")
    source = _CRICKET_CHANNEL_PHOTOS.get(run_key)
    if not source:
        return
    from_chat, msg_id = source
    try:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=from_chat,
            message_id=msg_id,
            caption=caption,
            parse_mode="HTML",
        )
    except Exception as e:
        _photo_log.warning(f"playcricket copy_message failed for run {run_key}: {e}")
        # fallback: send wiki photo
        name = _PLAYCRICKET_RUN_PICS.get(run_key)
        if name:
            img_url = _CRICKET_IMAGE_CACHE.get(name)
            if not img_url:
                wiki_title = _CRICKETERS_WIKI_MAP.get(name)
                if wiki_title:
                    try:
                        img_url = await _fetch_wiki_image(wiki_title)
                        if img_url:
                            _CRICKET_IMAGE_CACHE[name] = img_url
                    except Exception:
                        pass
            if img_url:
                try:
                    await _send_photo_safe(context, chat_id, img_url, caption)
                except Exception:
                    pass


async def _process_ball(query, context, chat_id: int, game: dict):
    bat  = game["bat_pick"]
    bowl = game["bowl_pick"]

    batter_id   = game["batter_id"]
    batter_name = game["player1_name"] if batter_id == game["player1_id"] else game["player2_name"]
    bowler_id   = game["bowler_id"]

    game["balls_faced"][batter_id] += 1
    ball_num = game["balls_faced"][batter_id]

    p1_id   = game["player1_id"]
    p2_id   = game["player2_id"]
    p1_name = game["player1_name"]
    p2_name = game["player2_name"]

    if bat == bowl:
        # ── OUT! ──────────────────────────────────────────────────────────────
        game["out"][batter_id] = True
        await _send_playcricket_photo(context, chat_id, "out")
        score = game["score"][batter_id]

        out_text = (
            f"💥 <b>WICKET!</b>\n\n"
            f"Ball {ball_num}: Bat <b>{bat}</b> | Bowl <b>{bowl}</b> — SAME NUMBER!\n\n"
            f"🚨 <b>{batter_name}</b> is OUT for <b>{score}</b> runs off {ball_num} balls!\n\n"
            f"{_cg_scorecard(game)}"
        )

        if game["innings"] == 1:
            # Innings 2 — swap roles
            game["innings"] = 2
            game["target"]  = score + 1
            game["batter_id"] = bowler_id
            game["bowler_id"] = batter_id
            game["phase"]     = "batting_pick"
            game["bat_pick"]  = None
            game["bowl_pick"] = None
            new_batter_name = p1_name if game["batter_id"] == p1_id else p2_name

            new_batter_id = game["batter_id"]
            out_text += (
                f"\n🔄 <b>2nd Innings!</b>\n"
                f"<a href='tg://user?id={new_batter_id}'>{new_batter_name}</a> "
                f"needs <b>{game['target']}</b> runs to win!"
            )
            await query.edit_message_text(out_text, parse_mode="HTML")
            await asyncio.sleep(1)
            await _send_batting_prompt(None, context, chat_id, game, edited=False)
        else:
            # Match over
            del active_playcricket[chat_id]
            s1 = game["score"][p1_id]
            s2 = game["score"][p2_id]

            if s1 > s2:
                result = f"🏆 <b>{p1_name}</b> wins by <b>{s1 - s2}</b> runs!"
            elif s2 > s1:
                result = f"🏆 <b>{p2_name}</b> wins by <b>{s2 - s1}</b> runs!"
            else:
                result = "🤝 <b>It's a tie!</b>"

            await query.edit_message_text(
                f"{out_text}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🏁 <b>Match Over!</b>\n\n"
                f"{result}\n\n"
                f"<a href='tg://user?id={p1_id}'>{p1_name}</a>: <b>{s1}</b> runs\n"
                f"<a href='tg://user?id={p2_id}'>{p2_name}</a>: <b>{s2}</b> runs",
                parse_mode="HTML"
            )
    else:
        # ── Runs scored ───────────────────────────────────────────────────────
        runs = bat
        game["score"][batter_id] += runs
        total = game["score"][batter_id]

        run_labels = {
            1: "1️⃣ <b>Single!</b>",
            2: "2️⃣ <b>Two runs!</b>",
            3: "3️⃣ <b>Three!</b>",
            4: "🏃 <b>FOUR!</b> 🎯",
            5: "5️⃣ <b>Five!</b>",
            6: "🚀 <b>SIX!</b> 💥🎆",
        }
        run_label = run_labels.get(runs, f"<b>{runs} runs</b>")
        await _send_playcricket_photo(context, chat_id, runs)

        # Check win condition in 2nd innings
        if game["innings"] == 2 and game["target"] is not None and total >= game["target"]:
            del active_playcricket[chat_id]
            s1 = game["score"][p1_id]
            s2 = game["score"][p2_id]
            winner_name = p1_name if s1 > s2 else p2_name
            diff = abs(s1 - s2)
            result = f"🏆 <b>{winner_name}</b> wins by <b>{diff}</b> {'run' if diff == 1 else 'runs'}!"

            await query.edit_message_text(
                f"⚡ Ball {ball_num}: Bat <b>{bat}</b> | Bowl <b>{bowl}</b>\n"
                f"{run_label} — <b>{batter_name}</b> total: <b>{total}</b>\n\n"
                f"{_cg_scorecard(game)}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🏁 <b>Match Over!</b>\n\n"
                f"{result}\n\n"
                f"<a href='tg://user?id={p1_id}'>{p1_name}</a>: <b>{s1}</b> runs\n"
                f"<a href='tg://user?id={p2_id}'>{p2_name}</a>: <b>{s2}</b> runs",
                parse_mode="HTML"
            )
            return

        # Continue batting
        target_line = ""
        if game["innings"] == 2 and game["target"] is not None:
            needed = game["target"] - total
            target_line = f"\n🎯 Need <b>{needed}</b> more to win"

        game["phase"]     = "batting_pick"
        game["bat_pick"]  = None
        game["bowl_pick"] = None

        await query.edit_message_text(
            f"⚡ Ball {ball_num}: Bat <b>{bat}</b> | Bowl <b>{bowl}</b>\n"
            f"{run_label} — <b>{batter_name}</b> total: <b>{total}</b>{target_line}\n\n"
            f"{_cg_scorecard(game)}\n"
            f"<a href='tg://user?id={batter_id}'>{batter_name}</a>, pick your next shot 👇",
            parse_mode="HTML",
            reply_markup=_cg_bat_keyboard(chat_id),
        )


# ── /collection ───────────────────────────────────────────────────────────────

async def _get_item_image(item: dict) -> str | None:
    """Return the image URL for a collected item (anime or cricketer)."""
    name = item["item_name"]
    item_type = item["item_type"]
    if item_type == "anime":
        url = _ANIME_IMAGE_MAP.get(name)
        if not url:
            for c in _anime_cache:
                if c["name"] == name:
                    url = c.get("image")
                    break
        return url
    else:  # cricketer
        if name in _CRICKET_IMAGE_CACHE:
            return _CRICKET_IMAGE_CACHE[name]
        wiki_title = _CRICKETERS_WIKI_MAP.get(name)
        if wiki_title:
            url = await _fetch_wiki_image(wiki_title)
            if url:
                _CRICKET_IMAGE_CACHE[name] = url
            return url
    return None


def _build_collection_keyboard(items: list, uid: int, page: int) -> InlineKeyboardMarkup:
    """Build the inline keyboard for the collection page."""
    total_pages = max(1, (len(items) + _COLLECTION_PAGE_SIZE - 1) // _COLLECTION_PAGE_SIZE)
    start = page * _COLLECTION_PAGE_SIZE
    page_items = items[start: start + _COLLECTION_PAGE_SIZE]

    buttons = []
    for i, item in enumerate(page_items):
        global_idx = start + i
        rarity_icon = RARITY_EMOJI.get(item.get("rarity", "Common"), "🔵")
        type_icon = "🏏" if item["item_type"] == "cricketer" else "🎭"
        label = f"{rarity_icon} {type_icon} #{global_idx + 1} {item['item_name']}"
        if len(label) > 50:
            label = label[:49] + "…"
        buttons.append([InlineKeyboardButton(label, callback_data=f"col_show_{uid}_{global_idx}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"col_pg_{uid}_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️ Next", callback_data=f"col_pg_{uid}_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(
        "🌐 View Cards Inline",
        switch_inline_query_current_chat=f"mycards_{uid}",
    )])
    return InlineKeyboardMarkup(buttons)


def _build_collection_text(items: list, uid: int, page: int, name_label: str) -> str:
    """Build the text header for the collection page."""
    cricketers = [i for i in items if i["item_type"] == "cricketer"]
    anime_items = [i for i in items if i["item_type"] == "anime"]
    total_pages = max(1, (len(items) + _COLLECTION_PAGE_SIZE - 1) // _COLLECTION_PAGE_SIZE)

    lines = [
        f"🔥 <b>{name_label} Shinobi Collection</b> 🔥",
        f"📄 Page {page + 1}/{total_pages}",
        "━━━━━━━━━━━━━━━━",
    ]
    if cricketers:
        total_c = sum(i.get("count", 1) for i in cricketers)
        lines.append(f"🏏 <b>Cricketers:</b> {len(cricketers)} unique · {total_c} total")
    if anime_items:
        total_a = sum(i.get("count", 1) for i in anime_items)
        lines.append(f"🎭 <b>Anime:</b> {len(anime_items)} unique · {total_a} total")
    lines.append(f"\n<i>Tap a card below to view its photo!</i>")
    return "\n".join(lines)


async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            uname = context.args[0].lstrip("@")
            member = await context.bot.get_chat_member(update.effective_chat.id, uname)
            target = member.user
        except Exception:
            pass

    if not target:
        target = user

    items = db.get_collection(target.id)
    is_self = target.id == user.id
    name_label = "Your" if is_self else f"{target.first_name}'s"

    if not items:
        await update.message.reply_text(
            f"{'You have' if is_self else target.first_name + ' has'} no collection yet!\n\n"
            f"Play <b>/cricket</b>, <b>/guess</b>, or <b>/pick</b> and answer correctly to collect characters.",
            parse_mode="HTML"
        )
        return

    # Cache items for callbacks
    context.bot_data[f"col_{target.id}"] = items

    all_items = (
        [i for i in items if i["item_type"] == "cricketer"] +
        [i for i in items if i["item_type"] == "anime"]
    )

    text = _build_collection_text(all_items, target.id, 0, name_label)
    kb = _build_collection_keyboard(all_items, target.id, 0)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def col_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Prev/Next page navigation in /collection."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")   # col_pg_{uid}_{page}
    uid  = int(parts[2])
    page = int(parts[3])

    items = context.bot_data.get(f"col_{uid}")
    if not items:
        items = db.get_collection(uid)
        context.bot_data[f"col_{uid}"] = items

    if not items:
        await query.answer("Collection not found!", show_alert=True)
        return

    all_items = (
        [i for i in items if i["item_type"] == "cricketer"] +
        [i for i in items if i["item_type"] == "anime"]
    )

    is_self = query.from_user.id == uid
    name_label = "Your" if is_self else "Their"
    try:
        member = await context.bot.get_chat_member(query.message.chat_id, uid)
        name_label = "Your" if is_self else f"{member.user.first_name}'s"
    except Exception:
        pass

    text = _build_collection_text(all_items, uid, page, name_label)
    kb = _build_collection_keyboard(all_items, uid, page)
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass


async def _send_and_cache_photo(context, chat_id: int, name: str, url: str, caption: str) -> bool:
    """Download image, send as bytes, and cache the returned Telegram file_id."""
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                if resp.status_code == 200 and len(resp.content) > 500:
                    img = BytesIO(resp.content)
                    img.name = "photo.jpg"
                    msg = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=img,
                        caption=caption,
                        parse_mode="HTML",
                    )
                    if msg and msg.photo:
                        _CARD_FILE_IDS[name] = msg.photo[-1].file_id
                    return True
        except Exception as e:
            _photo_log.warning(f"_send_and_cache_photo attempt {attempt+1}: {e}")
        if attempt == 0:
            await asyncio.sleep(1)
    return False


async def col_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the photo for a tapped card in /collection."""
    query = update.callback_query
    await query.answer("Loading photo… 📸")
    parts = query.data.split("_")   # col_show_{uid}_{idx}
    uid = int(parts[2])
    idx = int(parts[3])

    items = context.bot_data.get(f"col_{uid}")
    if not items:
        items = db.get_collection(uid)
        context.bot_data[f"col_{uid}"] = items

    all_items = (
        [i for i in items if i["item_type"] == "cricketer"] +
        [i for i in items if i["item_type"] == "anime"]
    )

    if idx >= len(all_items):
        await context.bot.send_message(query.message.chat_id, "Card not found!", parse_mode="HTML")
        return

    item = all_items[idx]
    name = item["item_name"]
    item_type = item["item_type"]
    rarity = item.get("rarity", "Common")
    rarity_icon = RARITY_EMOJI.get(rarity, "🔵")
    count = item.get("count", 1)
    src = item.get("source", "")

    if item_type == "anime":
        type_line = f"📺 Anime: <b>{src or 'Unknown'}</b>"
    else:
        type_line = "🌍 Sport: <b>Cricket</b>"

    caption = (
        f"{'🎭' if item_type == 'anime' else '🏏'} <b>{name}</b>\n"
        f"{rarity_icon} Rarity: <b>{rarity}</b>\n"
        f"{type_line}\n"
        f"📦 Owned: <b>×{count}</b>"
    )

    # Use cached file_id first (instant & free), else download and cache
    cached_fid = _CARD_FILE_IDS.get(name)
    if cached_fid:
        try:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=cached_fid,
                caption=caption,
                parse_mode="HTML",
            )
            return
        except Exception:
            del _CARD_FILE_IDS[name]  # stale — re-fetch below

    image_url = await _get_item_image(item)
    if image_url:
        sent = await _send_and_cache_photo(context, query.message.chat_id, name, image_url, caption)
        if not sent:
            await context.bot.send_message(query.message.chat_id, caption, parse_mode="HTML")
    else:
        await context.bot.send_message(query.message.chat_id, caption, parse_mode="HTML")


# ── Inline query — @bot mycards_{uid} shows all collected cards as a photo grid ─

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_obj = update.inline_query
    query_text = query_obj.query.strip()
    requester_id = query_obj.from_user.id

    target_uid = requester_id
    if query_text.startswith("mycards_"):
        try:
            target_uid = int(query_text[len("mycards_"):].strip())
        except ValueError:
            target_uid = requester_id
    elif query_text not in ("mycards", ""):
        await query_obj.answer([], cache_time=1)
        return

    items = db.get_collection(target_uid)
    if not items:
        await query_obj.answer(
            [InlineQueryResultArticle(
                id="no_cards",
                title="No collection yet!",
                description="Play /cricket, /guess, or /pick to collect characters.",
                input_message_content=InputTextMessageContent(
                    "No cards collected yet! Play /cricket, /guess, or /pick to start your collection."
                ),
            )],
            cache_time=5,
        )
        return

    all_items = (
        [i for i in items if i["item_type"] == "cricketer"] +
        [i for i in items if i["item_type"] == "anime"]
    )[:50]  # Telegram inline limit

    from telegram import InlineQueryResultCachedPhoto, InlineQueryResultPhoto
    results = []
    for i, item in enumerate(all_items):
        name = item["item_name"]
        item_type = item["item_type"]
        rarity = item.get("rarity", "Common")
        rarity_icon = RARITY_EMOJI.get(rarity, "🔵")
        count = item.get("count", 1)
        src = item.get("source", "")

        type_line = f"📺 {src or 'Unknown'}" if item_type == "anime" else "🌍 Cricket"
        caption = (
            f"{'🎭' if item_type == 'anime' else '🏏'} <b>{name}</b>\n"
            f"{rarity_icon} <b>{rarity}</b>  |  {type_line}\n"
            f"📦 ×{count}"
        )

        # Priority 1: cached Telegram file_id (always works, instant)
        cached_fid = _CARD_FILE_IDS.get(name)
        if cached_fid:
            results.append(InlineQueryResultCachedPhoto(
                id=str(i),
                photo_file_id=cached_fid,
                title=name,
                description=f"{rarity_icon} {rarity}  |  {type_line}",
                caption=caption,
                parse_mode="HTML",
            ))
            continue

        # Priority 2: get direct image URL from cache and use InlineQueryResultPhoto
        img_url = None
        if item_type == "anime":
            img_url = _ANIME_IMAGE_MAP.get(name)
            if not img_url:
                for c in _anime_cache:
                    if c.get("name") == name:
                        img_url = c.get("image")
                        break
        else:
            img_url = _CRICKET_IMAGE_CACHE.get(name)

        if img_url:
            try:
                results.append(InlineQueryResultPhoto(
                    id=str(i),
                    photo_url=img_url,
                    thumbnail_url=img_url,
                    title=name,
                    description=f"{rarity_icon} {rarity}  |  {type_line}",
                    caption=caption,
                    parse_mode="HTML",
                ))
                continue
            except Exception:
                pass

        # Priority 3: fallback text article (no photo available yet)
        results.append(InlineQueryResultArticle(
            id=str(i),
            title=f"{'🎭' if item_type == 'anime' else '🏏'} {name}",
            description=f"{rarity_icon} {rarity}  |  {type_line}  — tap card in /collection to load photo",
            input_message_content=InputTextMessageContent(
                f"{'🎭' if item_type == 'anime' else '🏏'} <b>{name}</b>\n"
                f"{rarity_icon} <b>{rarity}</b>  |  {type_line}\n"
                f"📦 ×{count}\n\n"
                f"<i>Tap the card button in /collection first to load its photo!</i>",
                parse_mode="HTML",
            ),
        ))

    await query_obj.answer(results, cache_time=5)


# ── /harem ────────────────────────────────────────────────────────────────────

def _build_harem_text(items: list, mode: str, target_name: str) -> str:
    """Build harem display text for Cricket or Anime tab."""
    medals = {
        "Legendary": "⭐", "Epic": "🟣", "Rare": "🟠",
        "Uncommon": "🟢", "Common": "🔵",
    }
    if mode == "cricket":
        cricket_items = [i for i in items if i["item_type"] == "cricketer"]
        if not cricket_items:
            return (
                f"🏏 <b>{target_name} Cricket Collection</b>\n\n"
                f"<i>No cricketers collected yet! Play /cricket to get some.</i>"
            )
        lines = [f"🏏 <b>{target_name} Cricket Collection</b>", "━━━━━━━━━━━━━━━━\n"]
        for idx, item in enumerate(cricket_items, 1):
            rarity = item.get("rarity", "Common")
            icon   = medals.get(rarity, "🔵")
            cnt    = item.get("count", 1)
            nm     = item["item_name"]
            lines.append(f"➥ {idx:03d} | {icon} | {nm}{' ×' + str(cnt) if cnt > 1 else ''}")
        total_c = sum(i.get("count", 1) for i in cricket_items)
        lines.append(f"\n<i>{len(cricket_items)} unique · {total_c} total</i>")
        return "\n".join(lines)
    else:  # anime
        anime_items = [i for i in items if i["item_type"] == "anime"]
        if not anime_items:
            return (
                f"🔰 <b>{target_name} Harem</b>\n\n"
                f"<i>No anime characters collected yet! Play /guess or /pick to get some.</i>"
            )
        from collections import defaultdict
        grouped: dict = defaultdict(list)
        for item in anime_items:
            src = item.get("source") or "Unknown Anime"
            grouped[src].append(item)

        lines = [f"🔰 <b>{target_name} Harem</b>", "━━━━━━━━━━━━━━━━\n"]
        global_idx = 1
        for src in sorted(grouped.keys()):
            group      = grouped[src]
            user_count = len(group)
            total_src  = ANIME_SERIES_TOTALS.get(src, 50)
            lines.append(f"↳ <b>{src}</b> {user_count}/{total_src}")
            lines.append("─" * 28)
            for item in group:
                rarity = item.get("rarity", "Common")
                icon   = medals.get(rarity, "🔵")
                cnt    = item.get("count", 1)
                nm     = item["item_name"]
                lines.append(
                    f"  ➥ {global_idx:03d} | {icon} | {nm}"
                    f"{' ×' + str(cnt) if cnt > 1 else ''}"
                )
                global_idx += 1
            lines.append("")
        total_a = sum(i.get("count", 1) for i in anime_items)
        lines.append(f"<i>{len(anime_items)} unique · {total_a} total</i>")
        return "\n".join(lines)


def _harem_keyboard(mode: str, user_id: int) -> InlineKeyboardMarkup:
    cricket_btn = InlineKeyboardButton(
        "🏏 Cricket ✅" if mode == "cricket" else "🏏 Cricket",
        callback_data=f"harem_cricket_{user_id}",
    )
    anime_btn = InlineKeyboardButton(
        "🎭 Anime ✅" if mode == "anime" else "🎭 Anime",
        callback_data=f"harem_anime_{user_id}",
    )
    return InlineKeyboardMarkup([[cricket_btn, anime_btn]])


async def harem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user's harem — anime collection grouped by series + cricket tab."""
    user = update.effective_user

    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            uname  = context.args[0].lstrip("@")
            member = await context.bot.get_chat_member(update.effective_chat.id, uname)
            target = member.user
        except Exception:
            pass
    if not target:
        target = user

    items = db.get_collection(target.id)
    is_self    = target.id == user.id
    name_label = "Your" if is_self else f"{target.first_name}'s"

    if not items:
        await update.message.reply_text(
            f"{'You have' if is_self else target.first_name + ' has'} no collection yet!\n\n"
            f"Play <b>/cricket</b>, <b>/guess</b>, or <b>/pick</b> to start your harem.",
            parse_mode="HTML",
        )
        return

    text = _build_harem_text(items, "anime", name_label)
    kb   = _harem_keyboard("anime", target.id)
    if len(text) > 4096:
        text = text[:4090] + "\n…"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def harem_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    data   = query.data
    parts  = data.split("_")   # harem_<mode>_<user_id>
    if len(parts) < 3:
        await query.answer()
        return

    mode       = parts[1]         # "cricket" or "anime"
    target_uid = int(parts[2])

    items = db.get_collection(target_uid)
    if not items:
        await query.answer("This user has no collection yet!", show_alert=True)
        return

    try:
        member = await context.bot.get_chat_member(query.message.chat_id, target_uid)
        tname  = member.user.first_name
    except Exception:
        tname = f"User {target_uid}"

    is_self    = query.from_user.id == target_uid
    name_label = "Your" if is_self else f"{tname}'s"

    text = _build_harem_text(items, mode, name_label)
    kb   = _harem_keyboard(mode, target_uid)
    if len(text) > 4096:
        text = text[:4090] + "\n…"

    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
    except Exception:
        await query.answer()
