import logging
from telegram import Update, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, InlineQueryHandler, filters,
)
from config import BOT_TOKEN
import database as db
from handlers import admin, fun, ranking, extras
from handlers import start as start_handler
from handlers import music
from handlers import downloader
from handlers import games_board
from handlers import tools
from handlers import games_extra
from handlers import anime as anime_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ALL_COMMANDS = [
    BotCommand("start",        "Show bot info and add-to-group button"),
    BotCommand("help",         "Browse all commands by category"),
]


async def post_init(app):
    db.init_db()
    await fun._fetch_anime_pool()
    await app.bot.set_my_commands(ALL_COMMANDS)
    await app.bot.set_my_commands(ALL_COMMANDS, scope=BotCommandScopeAllGroupChats())
    await app.bot.set_my_commands(ALL_COMMANDS, scope=BotCommandScopeAllPrivateChats())
    await music.start_tgcalls()
    if music.VOICE_CHAT_MODE:
        logger.info("Voice chat mode ENABLED (pyrogram + pytgcalls ready).")
    else:
        logger.info("Voice chat mode disabled — running in file-send mode.")
    logger.info("Bot is running and commands registered.")


async def post_shutdown(app):
    await music.stop_tgcalls()


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── Start / Help ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",       start_handler.start))
    app.add_handler(CommandHandler("help",        start_handler.help_cmd))
    app.add_handler(CallbackQueryHandler(start_handler.help_callback, pattern=r"^help_"))

    # ── Admin ─────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("ban",         admin.ban))
    app.add_handler(CommandHandler("unban",       admin.unban))
    app.add_handler(CommandHandler("kick",        admin.kick))
    app.add_handler(CommandHandler("mute",        admin.mute))
    app.add_handler(CommandHandler("unmute",      admin.unmute))
    app.add_handler(CommandHandler("warn",        admin.warn))
    app.add_handler(CommandHandler("resetwarns",  admin.resetwarns))
    app.add_handler(CommandHandler("promote",     admin.promote))
    app.add_handler(CommandHandler("demote",      admin.demote))
    app.add_handler(CommandHandler("pin",         admin.pin))
    app.add_handler(CommandHandler("unpin",       admin.unpin))
    app.add_handler(CommandHandler("purge",       admin.purge))
    app.add_handler(CommandHandler("setrules",    admin.setrules))
    app.add_handler(CommandHandler("rules",       admin.rules))
    app.add_handler(CommandHandler("lock",        admin.lock))
    app.add_handler(CommandHandler("unlock",      admin.unlock))
    app.add_handler(CommandHandler("setwelcome",  admin.setwelcome))
    app.add_handler(CommandHandler("setgoodbye",  admin.setgoodbye))
    app.add_handler(CommandHandler("slowmode",    admin.slowmode))
    app.add_handler(CommandHandler("report",      admin.report))
    app.add_handler(CommandHandler("info",        admin.info))
    app.add_handler(CommandHandler("log",         admin.log))
    app.add_handler(CommandHandler("utag",        admin.utag))
    app.add_handler(CommandHandler("cancletage",  admin.cancletage))
    app.add_handler(CommandHandler("lag",         admin.lag))
    app.add_handler(CommandHandler("broadcast",   admin.broadcast))
    app.add_handler(CallbackQueryHandler(admin.lock_callback,     pattern=r"^lock_"))
    app.add_handler(CallbackQueryHandler(admin.slowmode_callback, pattern=r"^slow_"))
    app.add_handler(CallbackQueryHandler(admin.lang_callback,     pattern=r"^lang_"))

    # ── Extras ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("afk",         extras.afk))
    app.add_handler(CommandHandler("unafk",       extras.unafk))
    app.add_handler(CommandHandler("calc",        extras.calc))
    app.add_handler(CommandHandler("quote",       extras.quote))
    app.add_handler(CommandHandler("id",          extras.user_id))
    app.add_handler(CommandHandler("ping",        extras.ping))
    app.add_handler(CommandHandler("remind",      extras.remind))
    app.add_handler(CommandHandler("choose",      extras.choose))
    app.add_handler(CommandHandler("flip",        extras.flip))
    app.add_handler(CommandHandler("stats",       extras.stats))
    app.add_handler(CommandHandler("weather",     extras.weather))
    app.add_handler(CommandHandler("define",      extras.define))
    app.add_handler(CommandHandler("fact",        extras.fact))
    app.add_handler(CommandHandler("bmi",         extras.bmi))
    app.add_handler(CommandHandler("age",         extras.age))
    app.add_handler(CommandHandler("countdown",   extras.countdown))
    app.add_handler(CommandHandler("password",    extras.password))
    app.add_handler(CommandHandler("number",      extras.number))
    app.add_handler(CommandHandler("roll",        extras.roll))
    app.add_handler(CommandHandler("qr",          extras.qr))
    app.add_handler(CallbackQueryHandler(extras.quote_callback, pattern=r"^quote_new$"))

    # ── Tools (new 40+ commands) ───────────────────────────────────────────────
    # Info & lookup
    app.add_handler(CommandHandler("crypto",       tools.crypto))
    app.add_handler(CommandHandler("ip",           tools.ip_lookup))
    app.add_handler(CommandHandler("urban",        tools.urban))
    app.add_handler(CommandHandler("translate",    tools.translate))
    app.add_handler(CommandHandler("lyrics",       tools.lyrics))
    app.add_handler(CommandHandler("shorturl",     tools.shorturl))
    # Unit converters
    app.add_handler(CommandHandler("temp",         tools.temp))
    app.add_handler(CommandHandler("length",       tools.length))
    app.add_handler(CommandHandler("weight",       tools.weight))
    app.add_handler(CommandHandler("speed",        tools.speed))
    app.add_handler(CommandHandler("currency",     tools.currency))
    app.add_handler(CommandHandler("percent",      tools.percentage))
    app.add_handler(CommandHandler("time",         tools.time_cmd))
    app.add_handler(CommandHandler("color",        tools.color_cmd))
    # AI image
    app.add_handler(CommandHandler("image",        tools.image_cmd))
    app.add_handler(CommandHandler("link",         tools.link_cmd))
    # Anime image
    app.add_handler(CommandHandler("waifu",        tools.waifu))
    app.add_handler(CommandHandler("animepic",     tools.animepic))
    # Fun
    app.add_handler(CommandHandler("chuck",        tools.chuck))
    app.add_handler(CommandHandler("dadjoke",      tools.dadjoke))
    app.add_handler(CommandHandler("compliment",   tools.compliment))
    app.add_handler(CommandHandler("roast",        tools.roast))
    app.add_handler(CommandHandler("insult",       tools.insult))
    app.add_handler(CommandHandler("motivation",   tools.motivation))
    app.add_handler(CommandHandler("slot",         tools.slot))
    app.add_handler(CommandHandler("toss",         tools.toss))
    app.add_handler(CommandHandler("rate",         tools.rate))
    app.add_handler(CommandHandler("randomnum",    tools.randomnum))
    # Text transform
    app.add_handler(CommandHandler("reverse",      tools.reverse))
    app.add_handler(CommandHandler("mock",         tools.mock))
    app.add_handler(CommandHandler("aesthetic",    tools.aesthetic))
    app.add_handler(CommandHandler("bold",         tools.bold2))
    app.add_handler(CommandHandler("italic",       tools.italic2))
    app.add_handler(CommandHandler("binary",       tools.binary))
    app.add_handler(CommandHandler("morse",        tools.morse))
    app.add_handler(CommandHandler("base64e",      tools.base64e))
    app.add_handler(CommandHandler("base64d",      tools.base64d))
    app.add_handler(CommandHandler("sha256",       tools.sha256))
    app.add_handler(CommandHandler("md5",          tools.md5))
    app.add_handler(CommandHandler("uuid",         tools.uuid_cmd))
    app.add_handler(CommandHandler("wordcount",    tools.wordcount))
    app.add_handler(CommandHandler("clap",         tools.clap))
    app.add_handler(CommandHandler("spoiler",      tools.spoilertext))
    app.add_handler(CommandHandler("urlencode",    tools.encode_url))
    app.add_handler(CommandHandler("urldecode",    tools.decode_url))
    app.add_handler(CommandHandler("anagram",      tools.anagram))
    app.add_handler(CommandHandler("emojify",      tools.emojify))
    app.add_handler(CommandHandler("piglatin",     tools.piglatin))

    # ── Downloads ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("download",    downloader.download_cmd))
    app.add_handler(CommandHandler("sdownload",   downloader.sdownload_cmd))
    app.add_handler(CallbackQueryHandler(downloader.download_callback, pattern=r"^dlq_"))

    # ── Music ─────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("play",        music.play))
    app.add_handler(CommandHandler("pause",       music.pause))
    app.add_handler(CommandHandler("resume",      music.resume))
    app.add_handler(CommandHandler("skip",        music.skip))
    app.add_handler(CommandHandler("stop",        music.stop))
    app.add_handler(CommandHandler("queue",       music.queue_cmd))
    app.add_handler(CommandHandler("nowplaying",  music.nowplaying))
    app.add_handler(CallbackQueryHandler(music.music_callback, pattern=r"^music_"))

    # ── Fun / Games ───────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("dice",        fun.dice_cmd))
    app.add_handler(CommandHandler("coinflip",    fun.coinflip))
    app.add_handler(CommandHandler("truth",       fun.truth))
    app.add_handler(CommandHandler("dare",        fun.dare))
    app.add_handler(CommandHandler("8ball",       fun.eight_ball))
    app.add_handler(CommandHandler("joke",        fun.joke))
    app.add_handler(CommandHandler("love",        fun.love))
    app.add_handler(CommandHandler("meme",        fun.meme))
    app.add_handler(CommandHandler("poll",        fun.poll_cmd))
    app.add_handler(CommandHandler("top",         fun.top))
    app.add_handler(CommandHandler("trivia",      fun.trivia))
    app.add_handler(CommandHandler("hangman",     fun.hangman))
    app.add_handler(CommandHandler("wordmaster",  fun.wordmaster))
    app.add_handler(CommandHandler("tictactoe",   fun.tictactoe))
    app.add_handler(CommandHandler("rps",         fun.rps))
    app.add_handler(CommandHandler("pick",        fun.pick))
    app.add_handler(CommandHandler("cricket",     fun.cricket))
    app.add_handler(CommandHandler("playcricket", fun.playcricket))
    app.add_handler(CommandHandler("collection",     fun.collection))
    app.add_handler(CommandHandler("harem",          fun.harem))
    app.add_handler(CommandHandler("coins",          fun.coins))
    app.add_handler(CommandHandler("rb_leaderboard", fun.rb_leaderboard))
    app.add_handler(CallbackQueryHandler(fun.ttt_callback,        pattern=r"^ttt_"))
    app.add_handler(CallbackQueryHandler(fun.rps_callback,        pattern=r"^rps_"))
    app.add_handler(CallbackQueryHandler(fun.pick_callback,       pattern=r"^pick_"))
    app.add_handler(CallbackQueryHandler(fun.cg_callback,         pattern=r"^cg_"))
    app.add_handler(CallbackQueryHandler(fun.dice_callback,       pattern=r"^dice_roll$"))
    app.add_handler(CallbackQueryHandler(fun.coin_callback,       pattern=r"^coin_flip$"))
    app.add_handler(CallbackQueryHandler(fun.truth_callback,      pattern=r"^truth_new$"))
    app.add_handler(CallbackQueryHandler(fun.dare_callback,       pattern=r"^dare_new$"))
    app.add_handler(CallbackQueryHandler(fun.joke_callback,       pattern=r"^joke_new$"))
    app.add_handler(CallbackQueryHandler(fun.harem_callback,      pattern=r"^harem_"))
    app.add_handler(CallbackQueryHandler(fun.col_card_callback,   pattern=r"^col_show_"))
    app.add_handler(CallbackQueryHandler(fun.col_page_callback,   pattern=r"^col_pg_"))
    app.add_handler(InlineQueryHandler(fun.inline_query))

    # ── Extra Games (40 new — in /help only, not in command list) ────────────
    app.add_handler(CommandHandler("mathquiz",     games_extra.mathquiz))
    app.add_handler(CommandHandler("scramble",     games_extra.scramble))
    app.add_handler(CommandHandler("riddle",       games_extra.riddle))
    app.add_handler(CommandHandler("flag",         games_extra.flag))
    app.add_handler(CommandHandler("capital",      games_extra.capital))
    app.add_handler(CommandHandler("emoji_movie",  games_extra.emoji_movie))
    app.add_handler(CommandHandler("fill",         games_extra.fill))
    app.add_handler(CommandHandler("oddoneout",    games_extra.oddoneout))
    app.add_handler(CommandHandler("missing",      games_extra.missing))
    app.add_handler(CommandHandler("sport_quiz",   games_extra.sport_quiz))
    app.add_handler(CommandHandler("science_quiz", games_extra.science_quiz))
    app.add_handler(CommandHandler("geo_quiz",     games_extra.geo_quiz))
    app.add_handler(CommandHandler("history_quiz", games_extra.history_quiz))
    app.add_handler(CommandHandler("music_quiz",   games_extra.music_quiz))
    app.add_handler(CommandHandler("food_quiz",    games_extra.food_quiz))
    app.add_handler(CommandHandler("movie_quiz",   games_extra.movie_quiz))
    app.add_handler(CommandHandler("coding_quiz",  games_extra.coding_quiz))
    app.add_handler(CommandHandler("anime_quiz",   games_extra.anime_quiz))
    app.add_handler(CommandHandler("cricket_quiz", games_extra.cricket_quiz))
    app.add_handler(CommandHandler("whoami",       games_extra.whoami))
    app.add_handler(CommandHandler("lyric_guess",  games_extra.lyric_guess))
    app.add_handler(CommandHandler("emoji_riddle", games_extra.emoji_riddle))
    app.add_handler(CommandHandler("countryguess", games_extra.countryguess))
    app.add_handler(CommandHandler("decode",       games_extra.decode))
    app.add_handler(CommandHandler("wordchain",    games_extra.wordchain))
    app.add_handler(CommandHandler("lastletter",   games_extra.lastletter))
    app.add_handler(CommandHandler("typerace",     games_extra.typerace))
    app.add_handler(CommandHandler("rhyme_game",   games_extra.rhyme_game))
    app.add_handler(CommandHandler("synonym_game", games_extra.synonym_game))
    app.add_handler(CommandHandler("antonym_game", games_extra.antonym_game))
    app.add_handler(CommandHandler("anagram_game", games_extra.anagram_game))
    app.add_handler(CommandHandler("category_game",games_extra.category_game))
    app.add_handler(CommandHandler("fast_math",    games_extra.fast_math))
    app.add_handler(CommandHandler("prime",        games_extra.prime))
    app.add_handler(CommandHandler("numberbomb",   games_extra.numberbomb))
    app.add_handler(CommandHandler("mixword",      games_extra.mixword))
    app.add_handler(CommandHandler("would_you",    games_extra.would_you))
    app.add_handler(CommandHandler("versus",       games_extra.versus))
    app.add_handler(CommandHandler("neverhave",    games_extra.neverhave))
    app.add_handler(CommandHandler("zodiac",       games_extra.zodiac_compat))
    app.add_handler(CallbackQueryHandler(games_extra.would_you_callback,  pattern=r"^wr_"))
    app.add_handler(CallbackQueryHandler(games_extra.versus_callback,     pattern=r"^vs_"))
    app.add_handler(CallbackQueryHandler(games_extra.neverhave_callback,  pattern=r"^nh_"))

    # ── Anime (50 commands — in /help → 🎌 Anime, not in command list) ─────────
    # Info
    app.add_handler(CommandHandler("anime",       anime_handler.anime_search))
    app.add_handler(CommandHandler("manga",       anime_handler.manga_search))
    app.add_handler(CommandHandler("achar",       anime_handler.achar))
    app.add_handler(CommandHandler("topanime",    anime_handler.topanime))
    app.add_handler(CommandHandler("seasonal",    anime_handler.seasonal))
    app.add_handler(CommandHandler("randomanim",  anime_handler.randomanim))
    app.add_handler(CommandHandler("upcoming",    anime_handler.upcoming))
    app.add_handler(CommandHandler("popular",     anime_handler.popular))
    app.add_handler(CommandHandler("airing",      anime_handler.airing))
    app.add_handler(CommandHandler("animegenre",  anime_handler.animegenre))
    app.add_handler(CommandHandler("animerec",    anime_handler.animerec))
    # Fun & Social
    app.add_handler(CommandHandler("animequote",  anime_handler.animequote))
    app.add_handler(CommandHandler("animefact2",  anime_handler.animefact2))
    app.add_handler(CommandHandler("animefight",  anime_handler.animefight))
    app.add_handler(CommandHandler("animeship",   anime_handler.animeship))
    app.add_handler(CommandHandler("animematch",  anime_handler.animematch))
    app.add_handler(CommandHandler("animepower",  anime_handler.animepower))
    app.add_handler(CommandHandler("animeclan",   anime_handler.animeclan))
    app.add_handler(CommandHandler("animeaura",   anime_handler.animeaura))
    app.add_handler(CommandHandler("animesensei", anime_handler.animesensei))
    app.add_handler(CommandHandler("animewho",    anime_handler.animewho))
    # Reaction GIFs
    app.add_handler(CommandHandler("pat",         anime_handler.pat))
    app.add_handler(CommandHandler("hug",         anime_handler.hug))
    app.add_handler(CommandHandler("kiss",        anime_handler.kiss))
    app.add_handler(CommandHandler("slap",        anime_handler.slap))
    app.add_handler(CommandHandler("poke",        anime_handler.poke))
    app.add_handler(CommandHandler("cuddle",      anime_handler.cuddle))
    app.add_handler(CommandHandler("bonk",        anime_handler.bonk))
    app.add_handler(CommandHandler("punch",       anime_handler.punch))
    app.add_handler(CommandHandler("adance",      anime_handler.adance))
    app.add_handler(CommandHandler("wave",        anime_handler.wave))
    app.add_handler(CommandHandler("blush",       anime_handler.blush))
    app.add_handler(CommandHandler("cryanime",    anime_handler.cryanime))
    app.add_handler(CommandHandler("laugh",       anime_handler.laugh))
    app.add_handler(CommandHandler("smug",        anime_handler.smug))
    app.add_handler(CommandHandler("nom",         anime_handler.nom))
    app.add_handler(CommandHandler("wink",        anime_handler.wink))
    app.add_handler(CommandHandler("bite",        anime_handler.bite))
    app.add_handler(CommandHandler("kick",        anime_handler.kick))
    app.add_handler(CommandHandler("yeet",        anime_handler.yeet))
    app.add_handler(CommandHandler("baka",        anime_handler.baka))
    app.add_handler(CommandHandler("highfive",    anime_handler.highfive))
    app.add_handler(CommandHandler("handshake",   anime_handler.handshake))
    app.add_handler(CommandHandler("nod",         anime_handler.nod_anim))
    app.add_handler(CommandHandler("asleep",      anime_handler.asleep))
    app.add_handler(CommandHandler("stare",       anime_handler.stare))
    # Profile / Watchlist
    app.add_handler(CommandHandler("aniprofile",  anime_handler.aniprofile))
    app.add_handler(CommandHandler("addwatch",    anime_handler.addwatch))
    app.add_handler(CommandHandler("myanilist",   anime_handler.myanilist))

    # ── Board Games ───────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("snake",       games_board.snake))
    app.add_handler(CommandHandler("ludo",        games_board.ludo))
    app.add_handler(CallbackQueryHandler(games_board.snl_callback,  pattern=r"^snl_"))
    app.add_handler(CallbackQueryHandler(games_board.ludo_callback, pattern=r"^ludo_"))

    # ── Ranking ───────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("ranking",     ranking.ranking))
    app.add_handler(CallbackQueryHandler(ranking.ranking_callback, pattern=r"^rank_"))

    # ── Member join / leave ───────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, admin.welcome_new_member))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, admin.goodbye_member))

    # ── Passive text + photo caption handler ──────────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, _combined_text_handler))
    app.add_handler(MessageHandler(
        filters.PHOTO & filters.CAPTION & filters.Regex(r"(?i)^/setwelcome"),
        admin.setwelcome))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def _combined_text_handler(update: Update, context):
    if not update.message or not update.effective_user:
        return
    # Link-lock: delete messages with URLs if enabled for this chat
    await admin.check_link_lock(update, context)

    msg  = update.message
    user = update.effective_user
    chat = update.effective_chat

    if user and not user.is_bot:
        db.track_user(user.id, user.username or "", user.first_name or "")

    if chat and chat.type != "private":
        db.track_chat(chat.id, chat.type, chat.title or "")
        db.upsert_seen_member(
            chat.id, user.id,
            user.username or "", user.first_name or "",
        )

    await ranking.count_message(update, context)
    await extras.check_afk_on_message(update, context)

    chat_id = chat.id

    if chat_id in fun.active_trivia:
        await fun.trivia_answer(update, context)
        return
    if chat_id in fun.active_hangman:
        text = msg.text.strip()
        if len(text) == 1 and text.isalpha():
            await fun.hangman_guess(update, context)
            return
    if chat_id in fun.active_guess:
        await fun.guess_answer(update, context)
        return
    if chat_id in fun.active_cricket:
        await fun.cricket_answer(update, context)
        return

    # Extra games (40 new games quiz engine)
    await games_extra.check_game_answer(update, context)


if __name__ == "__main__":
    main()
