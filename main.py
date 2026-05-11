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
from handlers import tag as tag_handler
from handlers import movies as movies_handler
from handlers import sports as sports_handler
from handlers import series as series_handler
from handlers import kdramas as kdramas_handler
from handlers import cdramas as cdramas_handler
from handlers import news as news_handler
from handlers import voice as voice_handler

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
    app.add_handler(CommandHandler("rankings",    ranking.rankings))
    app.add_handler(CommandHandler("topgame",     ranking.topgame))
    app.add_handler(CommandHandler("topusers",    ranking.topusers))
    app.add_handler(CommandHandler("topgroups",   ranking.topgroups))
    app.add_handler(CommandHandler("profile",     ranking.profile))
    app.add_handler(CommandHandler("mygifts",     ranking.mygifts))
    app.add_handler(CommandHandler("mytop",       ranking.mytop))
    app.add_handler(CommandHandler("groupstats",  ranking.groupstats))
    app.add_handler(CommandHandler("stophangman", ranking.stophangman))
    app.add_handler(CommandHandler("settings",    ranking.settings))
    app.add_handler(CallbackQueryHandler(ranking.ranking_callback, pattern=r"^rank_"))

    # ── Tag / Call ────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("all",         tag_handler.all_cmd))
    app.add_handler(CommandHandler("callall",     tag_handler.all_cmd))
    app.add_handler(CommandHandler("admins",      tag_handler.admins_cmd))
    app.add_handler(CommandHandler("calladmins",  tag_handler.admins_cmd))
    app.add_handler(CommandHandler("callone",     tag_handler.callone))
    app.add_handler(CommandHandler("tagone",      tag_handler.callone))
    app.add_handler(CommandHandler("allone",      tag_handler.callone))
    app.add_handler(CommandHandler("callpm",      tag_handler.callpm))
    app.add_handler(CommandHandler("allpm",       tag_handler.callpm))
    app.add_handler(CommandHandler("anybody",     tag_handler.anybody))
    app.add_handler(CommandHandler("anybodies",   tag_handler.anybody))
    app.add_handler(CommandHandler("stopcall",    tag_handler.stopcall))
    app.add_handler(CommandHandler("stop_call",   tag_handler.stopcall))
    app.add_handler(CommandHandler("call",        tag_handler.call_cmd))
    app.add_handler(CommandHandler("callactive",  tag_handler.call_cmd))

    # ── Movies ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("movie",         movies_handler.movie))
    app.add_handler(CommandHandler("moviefact",     movies_handler.moviefact))
    app.add_handler(CommandHandler("moviequote",    movies_handler.moviequote))
    app.add_handler(CommandHandler("movieline",     movies_handler.movieline))
    app.add_handler(CommandHandler("bollywood",     movies_handler.bollywood))
    app.add_handler(CommandHandler("bollywood_top", movies_handler.bollywood_top))
    app.add_handler(CommandHandler("hollywood",     movies_handler.hollywood))
    app.add_handler(CommandHandler("hollywood_top", movies_handler.hollywood_top))
    app.add_handler(CommandHandler("kollywood",     movies_handler.kollywood))
    app.add_handler(CommandHandler("tollywood",     movies_handler.tollywood))
    app.add_handler(CommandHandler("horrorfilm",    movies_handler.horrorfilm))
    app.add_handler(CommandHandler("comedyfilm",    movies_handler.comedyfilm))
    app.add_handler(CommandHandler("actionfilm",    movies_handler.actionfilm))
    app.add_handler(CommandHandler("scififilm",     movies_handler.scififilm))
    app.add_handler(CommandHandler("thrillerfilm",  movies_handler.thrillerfilm))
    app.add_handler(CommandHandler("romancefilm",   movies_handler.romancefilm))
    app.add_handler(CommandHandler("animationfilm", movies_handler.animationfilm))
    app.add_handler(CommandHandler("docfilm",       movies_handler.docfilm))
    app.add_handler(CommandHandler("classicfilm",   movies_handler.classicfilm))
    app.add_handler(CommandHandler("movierec",      movies_handler.movierec))
    app.add_handler(CommandHandler("marvelorder",   movies_handler.marvelorder))
    app.add_handler(CommandHandler("dcorder",       movies_handler.dcorder))
    app.add_handler(CommandHandler("movieguess",    movies_handler.movieguess))
    app.add_handler(CommandHandler("filmschool",    movies_handler.filmschool))
    app.add_handler(CommandHandler("filmoscar",     movies_handler.filmoscar))
    app.add_handler(CommandHandler("filmscore",     movies_handler.filmscore))
    app.add_handler(CommandHandler("filmtrend",     movies_handler.filmtrend))
    app.add_handler(CommandHandler("actorinfo",     movies_handler.actorinfo))
    app.add_handler(CommandHandler("moviedb",       movies_handler.moviedb))
    app.add_handler(CommandHandler("movieyear",     movies_handler.movieyear))
    app.add_handler(CommandHandler("filmgenre",     movies_handler.filmgenre))

    # ── Sports ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("football",       sports_handler.football))
    app.add_handler(CommandHandler("footballfact",   sports_handler.footballfact))
    app.add_handler(CommandHandler("footballquote",  sports_handler.footballquote))
    app.add_handler(CommandHandler("epl",            sports_handler.epl))
    app.add_handler(CommandHandler("laliga",         sports_handler.laliga))
    app.add_handler(CommandHandler("bundesliga",     sports_handler.bundesliga))
    app.add_handler(CommandHandler("seriea_league",  sports_handler.seriea_league))
    app.add_handler(CommandHandler("ucl",            sports_handler.ucl))
    app.add_handler(CommandHandler("topscorer",      sports_handler.topscorer))
    app.add_handler(CommandHandler("transfernews",   sports_handler.transfernews))
    app.add_handler(CommandHandler("worldcupfact",   sports_handler.worldcupfact))
    app.add_handler(CommandHandler("fifafact",       sports_handler.fifafact))
    app.add_handler(CommandHandler("footballquiz",   sports_handler.footballquiz))
    app.add_handler(CommandHandler("cricketfact",    sports_handler.cricketfact))
    app.add_handler(CommandHandler("t20record",      sports_handler.t20record))
    app.add_handler(CommandHandler("ipl",            sports_handler.ipl))
    app.add_handler(CommandHandler("testcricket",    sports_handler.testcricket))
    app.add_handler(CommandHandler("odifact",        sports_handler.odifact))
    app.add_handler(CommandHandler("cricketstats",   sports_handler.cricketstats))
    app.add_handler(CommandHandler("worldcup_cricket", sports_handler.worldcup_cricket))
    app.add_handler(CommandHandler("tennis",         sports_handler.tennis))
    app.add_handler(CommandHandler("tennisnews",     sports_handler.tennisnews))
    app.add_handler(CommandHandler("grandslam",      sports_handler.grandslam))
    app.add_handler(CommandHandler("tennisrank",     sports_handler.tennisrank))
    app.add_handler(CommandHandler("f1",             sports_handler.f1))
    app.add_handler(CommandHandler("f1fact",         sports_handler.f1fact))
    app.add_handler(CommandHandler("f1driver",       sports_handler.f1driver))
    app.add_handler(CommandHandler("nba",            sports_handler.nba))
    app.add_handler(CommandHandler("basketballfact", sports_handler.basketballfact))
    app.add_handler(CommandHandler("boxing",         sports_handler.boxing))
    app.add_handler(CommandHandler("boxingfact",     sports_handler.boxingfact))
    app.add_handler(CommandHandler("ufc",            sports_handler.ufc))
    app.add_handler(CommandHandler("olympicfact",    sports_handler.olympicfact))
    app.add_handler(CommandHandler("olympicrecord",  sports_handler.olympicrecord))
    app.add_handler(CommandHandler("sportquote",     sports_handler.sportquote))
    app.add_handler(CommandHandler("sportfact",      sports_handler.sportfact))
    app.add_handler(CommandHandler("golfnews",       sports_handler.golfnews))
    app.add_handler(CommandHandler("swimfact",       sports_handler.swimfact))
    app.add_handler(CommandHandler("athleticsfact",  sports_handler.athleticsfact))
    app.add_handler(CommandHandler("sport_birthday", sports_handler.sport_birthday))
    app.add_handler(CommandHandler("rugbyfact",      sports_handler.rugbyfact))
    app.add_handler(CommandHandler("wwe",            sports_handler.wwe))

    # ── Series ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("series",         series_handler.series_search))
    app.add_handler(CommandHandler("topseries",      series_handler.topseries))
    app.add_handler(CommandHandler("netflixseries",  series_handler.netflixseries))
    app.add_handler(CommandHandler("hboseries",      series_handler.hboseries))
    app.add_handler(CommandHandler("amazonseries",   series_handler.amazonseries))
    app.add_handler(CommandHandler("disneyseries",   series_handler.disneyseries))
    app.add_handler(CommandHandler("seriesrec",      series_handler.seriesrec))
    app.add_handler(CommandHandler("seriesgenre",    series_handler.seriesgenre))
    app.add_handler(CommandHandler("crimeshow",      series_handler.crimeshow))
    app.add_handler(CommandHandler("comedyshow",     series_handler.comedyshow))
    app.add_handler(CommandHandler("scifishow",      series_handler.scifishow))
    app.add_handler(CommandHandler("tvfact",         series_handler.tvfact))
    app.add_handler(CommandHandler("tvquote",        series_handler.tvquote))
    app.add_handler(CommandHandler("tvquiz",         series_handler.tvquiz))
    app.add_handler(CommandHandler("miniseries",     series_handler.miniseries))
    app.add_handler(CommandHandler("docuseries",     series_handler.docuseries))
    app.add_handler(CommandHandler("animatedseries", series_handler.animatedseries))
    app.add_handler(CommandHandler("trendingseries", series_handler.trendingseries))
    app.add_handler(CommandHandler("classicseries",  series_handler.classicseries))
    app.add_handler(CommandHandler("britishseries",  series_handler.britishseries))
    app.add_handler(CommandHandler("fantasyshow",    series_handler.fantasyshow))
    app.add_handler(CommandHandler("horrorseries",   series_handler.horrorseries))

    # ── K-Dramas ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("kdrama",          kdramas_handler.kdrama))
    app.add_handler(CommandHandler("topkdrama",       kdramas_handler.topkdrama))
    app.add_handler(CommandHandler("kdramarec",       kdramas_handler.kdramarec))
    app.add_handler(CommandHandler("romantickdrama",  kdramas_handler.romantickdrama))
    app.add_handler(CommandHandler("actionkdrama",    kdramas_handler.actionkdrama))
    app.add_handler(CommandHandler("historicalkdrama",kdramas_handler.historicalkdrama))
    app.add_handler(CommandHandler("schoolkdrama",    kdramas_handler.schoolkdrama))
    app.add_handler(CommandHandler("netflixkdrama",   kdramas_handler.netflixkdrama))
    app.add_handler(CommandHandler("kdramaoss",       kdramas_handler.kdramaoss))
    app.add_handler(CommandHandler("kdramafact",      kdramas_handler.kdramafact))
    app.add_handler(CommandHandler("kdramaquote",     kdramas_handler.kdramaquote))
    app.add_handler(CommandHandler("kpop",            kdramas_handler.kpop))
    app.add_handler(CommandHandler("kpopfact",        kdramas_handler.kpopfact))
    app.add_handler(CommandHandler("kpopchart",       kdramas_handler.kpopchart))
    app.add_handler(CommandHandler("kdramaactor",     kdramas_handler.kdramaactor))
    app.add_handler(CommandHandler("webdrama",        kdramas_handler.webdrama))
    app.add_handler(CommandHandler("kdramamood",      kdramas_handler.kdramamood))
    app.add_handler(CommandHandler("kdramawatch",     kdramas_handler.kdramawatch))
    app.add_handler(CommandHandler("koreafact",       kdramas_handler.koreafact))
    app.add_handler(CommandHandler("kdramaquiz",      kdramas_handler.kdramaquiz))

    # ── C-Dramas ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("cdrama",         cdramas_handler.cdrama))
    app.add_handler(CommandHandler("topcdrama",      cdramas_handler.topcdrama))
    app.add_handler(CommandHandler("cdramarec",      cdramas_handler.cdramarec))
    app.add_handler(CommandHandler("xianxia",        cdramas_handler.xianxia))
    app.add_handler(CommandHandler("wuxia",          cdramas_handler.wuxia))
    app.add_handler(CommandHandler("chistory",       cdramas_handler.chistory))
    app.add_handler(CommandHandler("cmodern",        cdramas_handler.cmodern))
    app.add_handler(CommandHandler("cdramaactor",    cdramas_handler.cdramaactor))
    app.add_handler(CommandHandler("cdramafact",     cdramas_handler.cdramafact))
    app.add_handler(CommandHandler("cdramaquote",    cdramas_handler.cdramaquote))
    app.add_handler(CommandHandler("cpop",           cdramas_handler.cpop))
    app.add_handler(CommandHandler("cdramaoss",      cdramas_handler.cdramaoss))
    app.add_handler(CommandHandler("cdramawatch",    cdramas_handler.cdramawatch))
    app.add_handler(CommandHandler("xuxian",         cdramas_handler.xuxian))
    app.add_handler(CommandHandler("wuxiafact",      cdramas_handler.wuxiafact))
    app.add_handler(CommandHandler("chinafilm",      cdramas_handler.chinafilm))
    app.add_handler(CommandHandler("cdramamood",     cdramas_handler.cdramamood))
    app.add_handler(CommandHandler("cdramagenre",    cdramas_handler.cdramagenre))
    app.add_handler(CommandHandler("cdramaquiz",     cdramas_handler.cdramaquiz))
    app.add_handler(CommandHandler("chinafact",      cdramas_handler.chinafact))

    # ── News ──────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("news",             news_handler.news))
    app.add_handler(CommandHandler("technews",         news_handler.technews))
    app.add_handler(CommandHandler("sportnews",        news_handler.sportnews))
    app.add_handler(CommandHandler("entertainmentnews",news_handler.entertainmentnews))
    app.add_handler(CommandHandler("sciencenews",      news_handler.sciencenews))
    app.add_handler(CommandHandler("healthnews",       news_handler.healthnews))
    app.add_handler(CommandHandler("businessnews",     news_handler.businessnews))
    app.add_handler(CommandHandler("cryptonews",       news_handler.cryptonews))
    app.add_handler(CommandHandler("gamernews",        news_handler.gamernews))
    app.add_handler(CommandHandler("movienews",        news_handler.movienews))
    app.add_handler(CommandHandler("animenews",        news_handler.animenews))
    app.add_handler(CommandHandler("kpopnews",         news_handler.kpopnews))
    app.add_handler(CommandHandler("worldnews",        news_handler.worldnews))
    app.add_handler(CommandHandler("breakingnews",     news_handler.breakingnews))
    app.add_handler(CommandHandler("indianews",        news_handler.indianews))
    app.add_handler(CommandHandler("spacenews",        news_handler.spacenews))
    app.add_handler(CommandHandler("politicsnews",     news_handler.politicsnews))
    app.add_handler(CommandHandler("environmentnews",  news_handler.environmentnews))
    app.add_handler(CommandHandler("foodnews",         news_handler.foodnews))

    # ── Voice / TTS ───────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("tts",       voice_handler.tts))
    app.add_handler(CommandHandler("vcjoin",    voice_handler.vcjoin))
    app.add_handler(CommandHandler("vcleave",   voice_handler.vcleave))
    app.add_handler(CommandHandler("vcplay",    voice_handler.vcplay))
    app.add_handler(CommandHandler("vcpause",   voice_handler.vcpause))
    app.add_handler(CommandHandler("vcresume",  voice_handler.vcresume))
    app.add_handler(CommandHandler("vcstop",    voice_handler.vcstop))
    app.add_handler(CommandHandler("vcskip",    voice_handler.vcskip))
    app.add_handler(CommandHandler("vcqueue",   voice_handler.vcqueue_cmd))
    app.add_handler(CommandHandler("vcnow",     voice_handler.vcnow))
    app.add_handler(CommandHandler("vcvolume",  voice_handler.vcvolume))
    app.add_handler(CommandHandler("vcmute",    voice_handler.vcmute))
    app.add_handler(CommandHandler("vcunmute",  voice_handler.vcunmute))
    app.add_handler(CommandHandler("vcstatus",  voice_handler.vcstatus))
    app.add_handler(CommandHandler("vctrack",   voice_handler.vctrack))

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
    if chat_id in fun.active_cricket:
        await fun.cricket_answer(update, context)
        return

    # Extra games (40 new games quiz engine)
    await games_extra.check_game_answer(update, context)


if __name__ == "__main__":
    main()
