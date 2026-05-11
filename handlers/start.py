from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

BANNER_TEXT = (
    "🤖 <b>Shinobi Management Bot</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "The most powerful group management &amp; entertainment bot.\n\n"
    "<b>What I can do:</b>\n"
    "  🛡️ Full admin moderation suite\n"
    "  🎮 Games: Trivia, Hangman, TicTacToe, Cricket &amp; 40 more\n"
    "  🃏 Anime &amp; Cricket character collection\n"
    "  🔧 50+ utility &amp; info tools\n"
    "  🎨 AI image generation\n"
    "  🎵 Music player &amp; voice tools\n"
    "  🎬 Movies, 📺 Series, 🇰🇷 K-Dramas, 🇨🇳 C-Dramas\n"
    "  ⚽ Sports, 📰 News, 🏷️ Tag/Call system\n"
    "  📊 Rankings, profiles &amp; group stats\n\n"
    "<i>Add me to your group and make me admin to get started.</i>"
)

# ── Help text sections ────────────────────────────────────────────────────────

ADMIN_HELP = (
    "🛡️ <b>Admin Commands</b> — Group admins only\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Member Control</b>\n"
    "/ban [user] — Permanently ban a user\n"
    "/unban [user] — Remove from ban list\n"
    "/kick [user] — Kick (can rejoin)\n"
    "/mute [user] [time] — Mute for duration (1h, 30m)\n"
    "/unmute [user] — Restore ability to talk\n\n"
    "<b>Warning System</b>\n"
    "/warn [user] — Add strike (3 = auto-ban)\n"
    "/resetwarns [user] — Clear all warnings\n"
    "/info [user] — View ID, status, warnings\n\n"
    "<b>Roles</b>\n"
    "/promote [user] — Grant admin rights\n"
    "/demote [user] — Remove admin rights\n\n"
    "<b>Chat Control</b>\n"
    "/pin — Pin replied message\n"
    "/unpin — Remove pinned message\n"
    "/purge — Delete messages (reply to start)\n"
    "/lock — Lock stickers/polls/media/links/all\n"
    "/unlock — Remove all locks\n"
    "/slowmode [s] — Set slowmode delay\n\n"
    "<b>Config</b>\n"
    "/setrules [text] — Save group rules\n"
    "/rules — Show rules\n"
    "/setwelcome [text] — Set welcome message\n"
    "/setgoodbye [text] — Set goodbye message\n"
    "/report — Alert admins\n"
    "/log — View recent admin actions\n"
    "/stats — Group activity statistics\n"
    "/settings — Group bot settings [admin]\n"
    "/groupstats — Full group statistics [admin]\n"
    "/stophangman — Stop active hangman game [admin]"
)

GAMES_HELP = (
    "🎮 <b>Games</b> — Everyone can play\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Guessing Games</b>\n"
    "/pick — Tap a button to guess the character\n"
    "/cricket — Guess the cricketer from their photo\n"
    "/trivia — Answer first and win points\n"
    "/hangman — Guess the hidden word letter by letter\n"
    "/wordmaster — Set a secret word for others to guess\n\n"
    "<b>vs Bot / PvP</b>\n"
    "/tictactoe — Tic-Tac-Toe with inline buttons\n"
    "/rps — Rock Paper Scissors with buttons\n"
    "/playcricket — Hand cricket PvP vs another user\n"
    "/snake — Snake &amp; Ladders PvP (2 players)\n"
    "/ludo — Ludo with 2–4 players\n\n"
    "<b>Random Fun</b>\n"
    "/dice — Roll a dice (1–6)\n"
    "/roll [NdN] — Dice roller, e.g. /roll 2d6\n"
    "/coinflip — Heads or Tails\n"
    "/8ball [question] — Magic 8-ball\n"
    "/truth — Random truth question\n"
    "/dare — Random dare challenge\n"
    "/joke — Random joke\n"
    "/love [user] — Love calculator\n"
    "/choose [a] [b] ... — Bot picks an option\n"
    "/flip [a] [b] — Random decision\n"
    "/meme — Trending meme\n"
    "/poll [question] — Group poll\n\n"
    "<b>Scores</b>\n"
    "/top — Top trivia scorers\n"
    "/ranking — Most active members\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🆕 <b>40 New Games</b> (type to play)\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Quiz Games</b>\n"
    "/mathquiz /scramble /riddle /flag /capital\n"
    "/emoji_movie /fill /oddoneout /missing\n"
    "/sport_quiz /science_quiz /geo_quiz\n"
    "/history_quiz /music_quiz /food_quiz\n"
    "/movie_quiz /coding_quiz /anime_quiz\n"
    "/cricket_quiz /whoami /lyric_guess\n"
    "/emoji_riddle /countryguess /decode\n\n"
    "<b>Word Games</b>\n"
    "/wordchain /lastletter /typerace\n"
    "/rhyme_game /synonym_game /antonym_game\n"
    "/anagram_game /category_game\n\n"
    "<b>Number &amp; Logic</b>\n"
    "/fast_math /prime /numberbomb /mixword\n\n"
    "<b>Fun &amp; Social</b>\n"
    "/would_you /versus /neverhave /zodiac [sign]"
)

COLLECTION_HELP = (
    "🃏 <b>Collection</b> — Collect &amp; show off your cards\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>View Collection</b>\n"
    "/collection — View your collected characters\n"
    "  ↳ Tap any card button to see their photo\n"
    "  ↳ Use ⬅️ Prev / ➡️ Next to page through\n"
    "  ↳ Tap 🌐 View Cards Inline to share as photo grid\n\n"
    "/harem — View your harem collection\n\n"
    "<b>Coins</b>\n"
    "/coins — Check your RB coin balance\n"
    "/rb_leaderboard — Top RB coin earners globally\n\n"
    "<b>How to collect</b>\n"
    "Play /cricket or /pick games.\n"
    "Answer correctly → earn a random character card!\n"
    "Rarities: 🔵 Common → 🟢 Uncommon → 🟠 Rare → 🟣 Epic → ⭐ Legendary"
)

TOOLS_HELP = (
    "🔧 <b>Tools</b> — Info, Calculators &amp; Converters\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Info &amp; Search</b>\n"
    "/weather [city] — Current weather\n"
    "/define [word] — Dictionary definition\n"
    "/fact — Random interesting fact\n"
    "/number [n] — Fun fact about a number\n"
    "/crypto [sym] — Crypto price (BTC/ETH etc.)\n"
    "/ip [ip] — IP geolocation\n"
    "/urban [word] — Urban Dictionary\n"
    "/translate [lang] [text] — Translate text\n"
    "/lyrics [artist] - [song] — Get lyrics\n"
    "/shorturl [url] — Shorten any URL\n\n"
    "<b>Calculators</b>\n"
    "/calc [expr] — Calculator\n"
    "/bmi [weight] [height] — BMI calculator\n"
    "/age [DD/MM/YYYY] — Age from birthdate\n"
    "/countdown [date] — Days until a date\n"
    "/percent [value] [total] — Percentage\n\n"
    "<b>Unit Converters</b>\n"
    "/temp /length /weight /speed /currency\n\n"
    "<b>Generators</b>\n"
    "/password [length] /uuid /qr [text]\n\n"
    "<b>Time &amp; Color</b>\n"
    "/time [tz] — Current time in timezone\n"
    "/color [hex] — Color info &amp; preview\n\n"
    "<b>AFK System</b>\n"
    "/afk [reason] /unafk\n\n"
    "<b>Other</b>\n"
    "/quote /remind [time] [msg] /id /ping /stats"
)

CREATIVE_HELP = (
    "🎨 <b>Creative &amp; Image Tools</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>AI Image Generation</b>\n"
    "/image [prompt] — Generate AI image\n"
    "/link [prompt] — Get a direct image URL\n\n"
    "<b>Anime Images</b>\n"
    "/waifu — Random anime waifu image\n"
    "/animepic — Random anime character image\n\n"
    "<b>Text Transform</b>\n"
    "/reverse /mock /aesthetic /bold /italic\n"
    "/binary /morse /base64e /base64d\n"
    "/sha256 /md5 /clap /spoiler\n"
    "/urlencode /urldecode /anagram\n"
    "/emojify /piglatin /wordcount"
)

FUN_HELP = (
    "😂 <b>Fun Commands</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Jokes</b>\n"
    "/chuck — Random Chuck Norris fact\n"
    "/dadjoke — Groan-worthy dad joke\n"
    "/insult — Random funny insult\n\n"
    "<b>Social</b>\n"
    "/compliment [@user] — Compliment someone\n"
    "/roast [reply] — Roast someone\n"
    "/motivation — Motivational message\n"
    "/rate [@user] — Rate someone\n\n"
    "<b>Games</b>\n"
    "/slot — 🎰 Slot machine\n"
    "/toss — 🪙 Simple coin toss\n"
    "/randomnum [min] [max] — Random number\n\n"
    "<b>Also in 🎮 Games tab:</b>\n"
    "/truth, /dare, /8ball, /dice, /coinflip,\n"
    "/joke, /love, /meme, /trivia, /hangman"
)

MUSIC_HELP = (
    "🎵 <b>Music</b> — Download &amp; play songs\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/play [song name or URL] — Search YouTube, download &amp; send\n"
    "/queue — View the current song queue\n"
    "/nowplaying — Show the current song\n"
    "/pause /resume /skip /stop — Playback control\n"
    "/sdownload [song/url] — Download as MP3\n"
    "/download [url] — Download video (YT/IG/TikTok etc.)\n\n"
    "🎙️ <b>Voice / TTS</b>\n"
    "/tts [text] — Text to speech (sends audio)\n"
    "/vcplay /vcpause /vcresume /vcstop /vcskip\n"
    "/vcqueue /vcnow /vcstatus /vctrack\n"
    "/vcjoin /vcleave /vcvolume /vcmute /vcunmute"
)

ANIME_HELP = (
    "🎌 <b>Anime</b> — 50 anime commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>🔍 Search &amp; Info</b>\n"
    "/anime [title] /manga [title] /achar [name]\n"
    "/topanime /seasonal /randomanim\n"
    "/upcoming /popular /airing\n"
    "/animegenre [genre] /animerec\n\n"
    "<b>🎲 Anime Fun</b>\n"
    "/animequote /animefact2 /animefight\n"
    "/animeship /animematch /animepower\n"
    "/animeclan /animeaura /animesensei /animewho\n\n"
    "<b>💕 Reaction GIFs</b>\n"
    "/pat /hug /kiss /slap /poke /cuddle\n"
    "/bonk /punch /adance /wave /blush\n"
    "/cryanime /laugh /smug /nom /wink\n"
    "/bite /kick /yeet /baka /highfive\n"
    "/handshake /nod /asleep /stare\n\n"
    "<b>📋 Anime Profile</b>\n"
    "/aniprofile /addwatch /myanilist"
)

DOWNLOADS_HELP = (
    "📥 <b>Downloads</b> — Download videos &amp; songs\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/download [url] — Download video from any platform\n"
    "  ↳ YouTube, Instagram, Twitter, TikTok &amp; more\n"
    "  ↳ Up to 4K quality\n\n"
    "/sdownload [url or song name] — Download as MP3\n"
    "  ↳ Extracts audio from any video URL\n\n"
    "<i>Files are sent directly to the chat.</i>"
)

MOVIES_HELP = (
    "🎬 <b>Movies</b> — 35 movie commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/movie [title] — Movie info (set OMDB_API_KEY for live data)\n"
    "/moviedb [title] — Full database lookup\n"
    "/actorinfo [name] — Actor filmography\n"
    "/movieyear [year] — Best movies from a year\n"
    "/filmgenre [genre] — Films by genre\n\n"
    "<b>Genre Picks</b>\n"
    "/horrorfilm /comedyfilm /actionfilm /scififilm\n"
    "/thrillerfilm /romancefilm /animationfilm /docfilm\n"
    "/classicfilm /movierec\n\n"
    "<b>Regional Cinema</b>\n"
    "/bollywood /bollywood_top — Bollywood picks\n"
    "/hollywood /hollywood_top — Hollywood picks\n"
    "/kollywood — Tamil cinema\n"
    "/tollywood — Telugu cinema\n\n"
    "<b>Lists &amp; Info</b>\n"
    "/marvelorder — MCU watch order\n"
    "/dcorder — DC universe order\n"
    "/filmoscar — Recent Oscar winners\n"
    "/filmscore — Legendary film composers\n"
    "/filmtrend — Trending now (links)\n\n"
    "<b>Fun</b>\n"
    "/moviefact /moviequote /movieline\n"
    "/movieguess — Guess movie from emojis\n"
    "/filmschool — Filmmaking trivia"
)

SPORTS_HELP = (
    "⚽ <b>Sports</b> — 40 sports commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Football</b>\n"
    "/football /footballfact /footballquote\n"
    "/epl /laliga /bundesliga /seriea_league\n"
    "/ucl /topscorer /transfernews\n"
    "/worldcupfact /fifafact /footballquiz\n\n"
    "<b>Cricket</b>\n"
    "/cricketfact /t20record /ipl\n"
    "/testcricket /odifact /cricketstats\n"
    "/worldcup_cricket\n\n"
    "<b>Tennis</b>\n"
    "/tennis /tennisnews /grandslam /tennisrank\n\n"
    "<b>Formula 1</b>\n"
    "/f1 /f1fact /f1driver\n\n"
    "<b>Basketball &amp; Boxing</b>\n"
    "/nba /basketballfact /boxing /boxingfact /ufc\n\n"
    "<b>Olympics &amp; More</b>\n"
    "/olympicfact /olympicrecord /sport_birthday\n"
    "/sportquote /sportfact /golfnews\n"
    "/swimfact /athleticsfact /rugbyfact /wwe"
)

SERIES_HELP = (
    "📺 <b>Series / TV Shows</b> — 25 commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/series [title] — TV series info (free TVmaze API)\n"
    "/topseries — All-time top series\n\n"
    "<b>By Platform</b>\n"
    "/netflixseries /hboseries /amazonseries /disneyseries\n\n"
    "<b>By Genre</b>\n"
    "/crimeshow /comedyshow /scifishow\n"
    "/fantasyshow /horrorseries /britishseries\n"
    "/classicseries /animatedseries /docuseries\n"
    "/miniseries /seriesrec /seriesgenre [genre]\n\n"
    "<b>Fun &amp; Trivia</b>\n"
    "/tvfact /tvquote /tvquiz /trendingseries"
)

KDRAMAS_HELP = (
    "🇰🇷 <b>K-Dramas</b> — 20 commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/kdrama [title] — K-drama search\n"
    "/topkdrama /kdramarec /kdramaactor [name]\n"
    "/kdramawatch — Where to watch\n\n"
    "<b>By Genre / Mood</b>\n"
    "/romantickdrama /actionkdrama\n"
    "/historicalkdrama /schoolkdrama\n"
    "/netflixkdrama /webdrama\n"
    "/kdramamood [mood] — By mood\n\n"
    "<b>K-Pop</b>\n"
    "/kpop /kpopfact /kpopchart\n\n"
    "<b>Fun</b>\n"
    "/kdramaoss /kdramafact /kdramaquote\n"
    "/koreafact /kdramaquiz"
)

CDRAMAS_HELP = (
    "🇨🇳 <b>C-Dramas</b> — 20 commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/cdrama [title] — C-drama info\n"
    "/topcdrama /cdramarec /cdramaactor [name]\n"
    "/cdramawatch — Where to watch\n\n"
    "<b>By Genre</b>\n"
    "/xianxia — Cultivation fantasy dramas\n"
    "/wuxia — Martial arts dramas\n"
    "/chistory — Historical C-dramas\n"
    "/cmodern — Modern C-dramas\n"
    "/xuxian — Romance dramas\n"
    "/cdramamood [mood] /cdramagenre [genre]\n\n"
    "<b>Chinese Culture</b>\n"
    "/cpop /chinafilm /wuxiafact /chinafact\n\n"
    "<b>Fun</b>\n"
    "/cdramaoss /cdramafact /cdramaquote /cdramaquiz"
)

NEWS_HELP = (
    "📰 <b>News</b> — 20 news commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "💡 Set <code>NEWS_API_KEY</code> (GNews free) for live headlines.\n"
    "Without it, commands show trusted news source links.\n\n"
    "<b>Categories</b>\n"
    "/news — Top headlines\n"
    "/worldnews /breakingnews /politicsnews\n"
    "/technews /sciencenews /spacenews\n"
    "/healthnews /businessnews /environmentnews\n"
    "/sportnews /entertainmentnews /foodnews\n"
    "/cryptonews /gamernews /movienews\n"
    "/animenews /kpopnews /indianews"
)

VOICE_HELP = (
    "🎙️ <b>Voice &amp; TTS</b> — 15 commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Text to Speech</b>\n"
    "/tts [lang] [text] — Convert text to speech\n"
    "  ↳ /tts Hello world\n"
    "  ↳ /tts ko 안녕하세요\n"
    "  ↳ /tts hi नमस्ते\n"
    "  Supported: en hi ja ko ar fr de es zh ru tr pt\n\n"
    "<b>Voice Chat</b>\n"
    "/vcplay [song] — Play song in VC (downloads &amp; sends)\n"
    "/vcpause /vcresume /vcstop /vcskip\n"
    "/vcqueue /vcnow — Queue &amp; current track\n"
    "/vcstatus — Voice chat status\n"
    "/vctrack — Track info\n"
    "/vcjoin /vcleave — Join/leave VC\n"
    "/vcvolume /vcmute /vcunmute"
)

TAG_HELP = (
    "🏷️ <b>Tag &amp; Call</b> — Mass mention commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Admin-only commands</b>\n"
    "/all [text] — Mention all tracked members\n"
    "  alias: /callall\n"
    "/admins [text] — Call all group admins\n"
    "/callone [n] [text] — Mention n members one-by-one\n"
    "  alias: /tagone\n"
    "/callpm [n] [text] — DM members who started the bot\n"
    "  alias: /allpm\n"
    "/call [n] [per] [text] — Full control mass call\n"
    "  alias: /callactive\n"
    "/stopcall — Stop an active mass call\n\n"
    "<b>Everyone</b>\n"
    "/anybody [text] — Ping a random member\n"
    "  alias: /anybodies\n\n"
    "<b>Existing admin tag:</b>\n"
    "/utag — Tag all members (original)\n"
    "/cancletage — Cancel active /utag call"
)

RANKING_HELP = (
    "📊 <b>Rankings &amp; Profile</b> — 11 commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Leaderboards</b>\n"
    "/ranking — This group's message leaderboard\n"
    "/rankings — Same as /ranking\n"
    "/topgame — Top game point earners\n"
    "/topusers — Top users globally\n"
    "/topgroups — Top groups globally\n\n"
    "<b>Your Stats</b>\n"
    "/profile — Your personal stats\n"
    "/mygifts — Your gifts &amp; rewards\n"
    "/mytop — Your rank across all groups\n\n"
    "<b>Group</b>\n"
    "/groupstats — Full group statistics [admin]\n\n"
    "<b>Settings</b>\n"
    "/settings — Bot settings for this group [admin]\n"
    "/stophangman — Force stop hangman [admin]"
)

GROUP_HELP = (
    "🏘️ <b>Group Setup Guide</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Step 1 — Add bot to group</b>\n"
    "Click the ➕ Add me to your group button above.\n\n"
    "<b>Step 2 — Make bot admin</b>\n"
    "The bot needs these permissions:\n"
    "• Delete messages\n"
    "• Ban users\n"
    "• Pin messages\n"
    "• Invite users\n"
    "• Restrict members\n\n"
    "<b>Step 3 — Configure (optional)</b>\n"
    "/setrules — Set group rules\n"
    "/setwelcome — Set welcome message\n"
    "/setgoodbye — Set goodbye message\n"
    "/settings — Bot settings\n\n"
    "<b>Optional API Keys</b>\n"
    "Set these in environment for enhanced features:\n"
    "• <code>OMDB_API_KEY</code> — Live movie search\n"
    "• <code>NEWS_API_KEY</code> — Live news headlines\n"
    "Get free keys at omdbapi.com and gnews.io"
)

# ── Keyboards ─────────────────────────────────────────────────────────────────

_MAIN_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🛡️ Admin",      callback_data="help_admin"),
        InlineKeyboardButton("🎮 Games",      callback_data="help_games"),
        InlineKeyboardButton("🃏 Collection", callback_data="help_collection"),
    ],
    [
        InlineKeyboardButton("🔧 Tools",      callback_data="help_tools"),
        InlineKeyboardButton("🎨 Creative",   callback_data="help_creative"),
        InlineKeyboardButton("😂 Fun",        callback_data="help_fun"),
    ],
    [
        InlineKeyboardButton("🎵 Music",      callback_data="help_music"),
        InlineKeyboardButton("📥 Downloads",  callback_data="help_downloads"),
        InlineKeyboardButton("🎌 Anime",      callback_data="help_anime"),
    ],
    [
        InlineKeyboardButton("🎬 Movies",     callback_data="help_movies"),
        InlineKeyboardButton("⚽ Sports",     callback_data="help_sports"),
        InlineKeyboardButton("📺 Series",     callback_data="help_series"),
    ],
    [
        InlineKeyboardButton("🇰🇷 K-Dramas",  callback_data="help_kdramas"),
        InlineKeyboardButton("🇨🇳 C-Dramas",  callback_data="help_cdramas"),
        InlineKeyboardButton("📰 News",       callback_data="help_news"),
    ],
    [
        InlineKeyboardButton("🎙️ Voice/TTS",  callback_data="help_voice"),
        InlineKeyboardButton("🏷️ Tag/Call",   callback_data="help_tag"),
        InlineKeyboardButton("📊 Rankings",   callback_data="help_ranking"),
    ],
    [
        InlineKeyboardButton("🏘️ Group Setup Guide", callback_data="help_group"),
    ],
])

_BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="help_back")]])

_HELP_MAPPING = {
    "help_admin":      ADMIN_HELP,
    "help_games":      GAMES_HELP,
    "help_collection": COLLECTION_HELP,
    "help_tools":      TOOLS_HELP,
    "help_creative":   CREATIVE_HELP,
    "help_fun":        FUN_HELP,
    "help_music":      MUSIC_HELP,
    "help_downloads":  DOWNLOADS_HELP,
    "help_anime":      ANIME_HELP,
    "help_movies":     MOVIES_HELP,
    "help_sports":     SPORTS_HELP,
    "help_series":     SERIES_HELP,
    "help_kdramas":    KDRAMAS_HELP,
    "help_cdramas":    CDRAMAS_HELP,
    "help_news":       NEWS_HELP,
    "help_voice":      VOICE_HELP,
    "help_tag":        TAG_HELP,
    "help_ranking":    RANKING_HELP,
    "help_group":      GROUP_HELP,
}


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = await context.bot.get_me()
    bot_username = bot.username
    add_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "➕  Add me to your group",
            url=(
                f"https://t.me/{bot_username}?startgroup=true"
                "&admin=restrict_members+ban_users+delete_messages+pin_messages+invite_users"
            )
        )],
        [
            InlineKeyboardButton("🛡️ Admin",      callback_data="help_admin"),
            InlineKeyboardButton("🎮 Games",      callback_data="help_games"),
            InlineKeyboardButton("🃏 Collection", callback_data="help_collection"),
        ],
        [
            InlineKeyboardButton("🔧 Tools",      callback_data="help_tools"),
            InlineKeyboardButton("🎨 Creative",   callback_data="help_creative"),
            InlineKeyboardButton("😂 Fun",        callback_data="help_fun"),
        ],
        [
            InlineKeyboardButton("🎵 Music",      callback_data="help_music"),
            InlineKeyboardButton("📥 Downloads",  callback_data="help_downloads"),
            InlineKeyboardButton("🎌 Anime",      callback_data="help_anime"),
        ],
        [
            InlineKeyboardButton("🎬 Movies",     callback_data="help_movies"),
            InlineKeyboardButton("⚽ Sports",     callback_data="help_sports"),
            InlineKeyboardButton("📺 Series",     callback_data="help_series"),
        ],
        [
            InlineKeyboardButton("🇰🇷 K-Dramas",  callback_data="help_kdramas"),
            InlineKeyboardButton("🇨🇳 C-Dramas",  callback_data="help_cdramas"),
            InlineKeyboardButton("📰 News",       callback_data="help_news"),
        ],
        [
            InlineKeyboardButton("🎙️ Voice/TTS",  callback_data="help_voice"),
            InlineKeyboardButton("🏷️ Tag/Call",   callback_data="help_tag"),
            InlineKeyboardButton("📊 Rankings",   callback_data="help_ranking"),
        ],
        [
            InlineKeyboardButton("🏘️ Group Setup Guide", callback_data="help_group"),
        ],
    ])
    try:
        await update.message.reply_photo(
            photo="https://telegra.ph/file/dfdb7e59bf5a1dc1d4e26.jpg",
            caption=BANNER_TEXT,
            parse_mode="HTML",
            reply_markup=add_btn,
        )
    except Exception:
        await update.message.reply_text(
            BANNER_TEXT,
            parse_mode="HTML",
            reply_markup=add_btn,
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Choose a help category:</b>",
        parse_mode="HTML",
        reply_markup=_MAIN_KB,
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in _HELP_MAPPING:
        text = _HELP_MAPPING[query.data]
        # Truncate if too long for Telegram (4096 char limit)
        if len(text) > 4000:
            text = text[:3990] + "\n…"
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=_BACK_KB
        )
    elif query.data == "help_back":
        await query.edit_message_text(
            "📖 <b>Choose a help category:</b>",
            parse_mode="HTML",
            reply_markup=_MAIN_KB,
        )
