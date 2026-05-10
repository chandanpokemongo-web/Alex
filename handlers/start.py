from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

BANNER_TEXT = (
    "🤖 <b>Shinobi Management Bot</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "The most powerful group management &amp; entertainment bot.\n\n"
    "<b>What I can do:</b>\n"
    "  🛡️ Full admin moderation suite\n"
    "  🎮 Games: Trivia, Hangman, TicTacToe, Cricket\n"
    "  🃏 Anime &amp; Cricket character collection\n"
    "  🔧 50+ utility &amp; info tools\n"
    "  🎨 AI image generation\n"
    "  🎵 Music player in voice chat\n"
    "  📥 Video &amp; song downloader\n\n"
    "<i>Add me to your group and make me admin to get started.</i>"
)

GROUP_HELP = (
    "👥 <b>Group Help</b> — Useful commands for group members\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Activity &amp; Ranking</b>\n"
    "/ranking — Show most active message senders\n"
    "/top — Top trivia scorers in this group\n"
    "/stats — Group activity statistics\n\n"
    "<b>Tag Members</b>\n"
    "/utag — Tag all group members at once (admin only)\n"
    "/cancletag — Cancel an active /utag operation\n\n"
    "<b>AFK (Away From Keyboard)</b>\n"
    "/afk [reason] — Set yourself as away\n"
    "/unafk — Remove your AFK status manually\n"
    "  ↳ AFK is also removed automatically when you send a message\n"
    "  ↳ Others are notified when they mention an AFK user\n\n"
    "<b>Group Info &amp; Rules</b>\n"
    "/rules — View the group rules\n"
    "/id — Get your Telegram user ID\n"
    "/info [user] — See user details and warnings\n"
    "/report — Alert admins about a message (reply to it)\n"
    "/ping — Check bot response time\n\n"
    "<b>Pinned Messages</b>\n"
    "/pinned — Show the current pinned message\n"
    "/pin — Pin a message (admin only)\n"
    "/unpin — Remove pinned message (admin only)\n\n"
    "<b>Notes</b>\n"
    "/notes — List all saved notes\n"
    "/get [name] — Get a saved note\n"
    "#notename — Shortcut to get a note\n\n"
    "<b>Slow Mode (admin only)</b>\n"
    "/slowmode [seconds] — Set message delay for all users\n\n"
    "<b>Welcome &amp; Goodbye (admin only)</b>\n"
    "/setwelcome [text] — Set a welcome message for new members\n"
    "/setgoodbye [text] — Set a goodbye message\n\n"
    "<i>Use /help to browse all command categories.</i>"
)

ADMIN_HELP = (
    "🛡️ <b>Admin &amp; Moderation</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/promote [user] — Give admin rights\n"
    "/demote [user] — Remove admin rights\n"
    "/adminlist — Show all admins in this group\n"
    "/admincache — Refresh and reload the admin list\n"
    "/anonadmin — Ignore anonymous admin permissions\n"
    "/adminerror — Toggle error messages for admins\n"
    "/disableadmin — Disable a command for admins too\n"
)

ANTIFLOOD_HELP = (
    "🌊 <b>Antiflood</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setflood [num] — Set max messages before flood action\n"
    "/setfloodtimer [sec] — Limit message frequency in seconds\n"
    "/floodmode [action] — Set flood punishment\n"
    "  Actions: kick / ban / mute / tban / tmute\n"
    "/clearflood — Delete all flood messages from a user\n"
    "/silentactions — Toggle quiet moderation\n\n"
    "<i>Use /setflood 0 to disable flood protection.</i>"
)

ANTIRAID_HELP = (
    "⚔️ <b>AntiRaid</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/antiraid — Enable or disable raid protection\n"
    "/autoantiraid — Automate raid detection\n"
    "/raidtime [sec] — Set how long a raid is active\n"
    "/raidactiontime [sec] — Set temporary ban length during raid\n\n"
    "<i>AntiRaid stops mass joins and auto-bans new users during a raid.</i>"
)

APPROVAL_HELP = (
    "✅ <b>Approval</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/approve [user] — Exempt a user from locks and filters\n"
    "/unapprove [user] — Remove a user's exemption\n"
    "/approved — List all currently exempt users\n\n"
    "<i>Approved users bypass flood protection, locks, and blocklists.</i>"
)

BANS_HELP = (
    "🔨 <b>Bans</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/ban [user] — Permanently ban a user\n"
    "/unban [user] — Remove from ban list\n"
    "/tban [user] [time] — Temporarily ban (e.g. 1h, 30m, 2d)\n"
    "/dban [user] — Ban and delete the replied message\n"
    "/sban [user] — Ban user silently\n"
    "/kick [user] — Remove from group (can rejoin)\n"
    "/dkick [user] — Kick and delete the replied message\n"
    "/skick [user] — Kick user silently\n\n"
    "<i>Admins only. Use /tban 1d to ban for 1 day.</i>"
)

BLOCKLISTS_HELP = (
    "🚫 <b>Blocklists</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/addblocklist [word/phrase] — Add a word to the block list\n"
    "/blocklistmode [action] — Set punishment for blocked words\n"
    "  Actions: delete / warn / mute / kick / ban / tban / tmute\n"
    "/allowlist [item] — Exempt a word or user from locks\n"
    "/rmallowlist [item] — Remove from allow list\n\n"
    "<i>Blocked words are automatically actioned when sent in chat.</i>"
)

CAPTCHA_HELP = (
    "🤖 <b>CAPTCHA</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/captcha — Enable or disable CAPTCHA for new members\n"
    "/captchamode [type] — Change verification type\n"
    "  Types: button / math / text\n"
    "/captcharules — Force users to read rules before passing\n"
    "/captchamutetime [time] — Set unmute delay after passing\n"
    "/captchakick — Toggle kicking users who fail CAPTCHA\n"
    "/captchakicktime [sec] — Set kick delay for failed CAPTCHA\n"
    "/setcaptchatext [text] — Customize the verify button text\n"
    "/resetcaptchatext — Restore default CAPTCHA button text\n\n"
    "<i>CAPTCHA verifies that new members are human before they can chat.</i>"
)

CLEAN_HELP = (
    "🧹 <b>Clean Commands &amp; Service</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Clean Service Messages</b>\n"
    "/cleanservice — Delete Telegram system alerts\n"
    "/cleanservicetypes — List which service types are cleaned\n"
    "/keepservice — Stop deleting service alerts\n"
    "/nocleanservice — Same as keepservice\n\n"
    "<b>Clean Bot Commands</b>\n"
    "/cleancommand — Auto-delete bot command messages\n"
    "/keepcommand — Keep bot command messages\n"
    "/disableable — List all commands that can be toggled\n"
    "/disabled — View all currently disabled commands\n"
    "/disabledel — Delete messages that trigger disabled commands\n"
)

CONNECTIONS_HELP = (
    "🔗 <b>Connections</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/connect [chat_id] — Remotely manage a group from private chat\n"
    "/disconnect — End the remote management session\n"
    "/reconnect — Resume the last remote session\n"
    "/connection — View currently linked chat\n\n"
    "<i>Connect lets you manage your group directly from your DMs.</i>"
)

DISABLING_HELP = (
    "🔕 <b>Disabling</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/disable [command] — Turn off a command in this chat\n"
    "/enable [command] — Re-enable a disabled command\n"
    "/disableable — List all commands that can be disabled\n"
    "/disabled — Show all currently disabled commands\n"
    "/disableadmin — Disable a command for admins too\n"
    "/disabledel — Delete messages that trigger a disabled command\n\n"
    "<i>Disabling a command makes the bot ignore it in this chat.</i>"
)

FEDERATIONS_HELP = (
    "🌐 <b>Federations (Global Bans)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Setup</b>\n"
    "/newfed [name] — Create a new federation\n"
    "/joinfed [fed_id] — Connect your chat to a federation\n"
    "/subfed [fed_id] — Subscribe to another federation\n"
    "/unsubfed [fed_id] — Unsubscribe from a federation\n"
    "/delfed — Delete your federation\n\n"
    "<b>Banning</b>\n"
    "/fban [user] [reason] — Federation-wide ban\n"
    "/unfban [user] — Remove a federation ban\n"
    "/fedstat [user] — Check if a user is fed-banned\n\n"
    "<b>Management</b>\n"
    "/fedinfo /fedadmins /fedsubs /fedpromote /feddemote\n"
    "/fedexport /fedimport /renamefed /fedtransfer\n"
    "/fednotif /fedreason /setfedlog /unsetfedlog /setfedlang\n"
)

FILTERS_HELP = (
    "🔍 <b>Filters</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/filter [word] [reply] — Auto-reply when a keyword is detected\n"
    "/stop [word] — Remove a specific word filter\n"
    "/stopall — Delete all active filters\n"
    "/filters — List all active filters\n\n"
    "<i>Filters trigger an automatic reply whenever the keyword appears.\n"
    "Add buttons with [Label](url) syntax inside filter replies.</i>"
)

GREETINGS_HELP = (
    "👋 <b>Greetings</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setwelcome [text] — Set a welcome message for new members\n"
    "/setgoodbye [text] — Set a goodbye message for leaving members\n"
    "/resetwelcome — Restore the default welcome message\n"
    "/resetgoodbye — Restore the default goodbye message\n\n"
    "<b>Variables:</b>\n"
    "  {first} {last} {username} {mention} {id} {chatname}\n\n"
    "<i>Attach a photo to /setwelcome and add buttons with [Label](url).</i>"
)

IMPORTEXPORT_HELP = (
    "📦 <b>Import / Export</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/export — Back up all chat settings to a file\n"
    "/import — Restore chat settings from an exported file\n"
    "/reset — Wipe all bot settings for this chat\n\n"
    "<i>Export saves rules, welcome, filters, notes, locks, and more.</i>"
)

LANGUAGES_HELP = (
    "🌍 <b>Languages</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setlang [code] — Change the bot language for this chat\n\n"
    "<b>Available codes:</b> en hi ar ur es fr\n\n"
    "<i>The bot will respond in the selected language for supported messages.</i>"
)

LOCKS_HELP = (
    "🔒 <b>Locks</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/lock [type] — Restrict specific content in this chat\n"
    "/unlock [type] — Remove a content restriction\n"
    "/locks — View all currently active locks\n"
    "/locktypes — List all available lock types\n"
    "/lockwarns — Toggle warnings when locked content is sent\n"
    "/allowlist [item] — Exempt a user or item from locks\n"
    "/rmallowlist [item] — Remove an allowlist exemption\n\n"
    "<b>Lockable types:</b>\n"
    "  sticker, gif, photo, video, document, audio,\n"
    "  voice, contact, location, poll, url, bots, all\n"
)

LOGCHANNELS_HELP = (
    "📋 <b>Log Channels</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setlog [channel] — Set a channel to receive moderation logs\n"
    "/log [categories] — Enable specific log categories\n"
    "/logchannel — View the current logging destination\n\n"
    "<b>Log categories:</b>\n"
    "  ban, kick, mute, warn, promote, demote,\n"
    "  filter, lock, welcome, note, settings\n\n"
    "<i>Make the bot an admin in your log channel to post there.</i>"
)

MISC_HELP = (
    "⚙️ <b>Miscellaneous</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/id — Get your Telegram user ID\n"
    "/info [user] — See user details\n"
    "/runs — Random escape string\n"
    "/donate — Support the bot creator\n"
    "/markdownhelp — Formatting guide\n"
    "/limits — Show bot constraints\n"
    "/pinned — Get current pinned message\n"
    "/unpinall — Clear all pinned messages\n"
    "/antichannelpin — Block automatic channel pins\n"
    "/cleanlinked — Delete forwarded channel posts\n"
    "/ping — Check bot response time\n"
    "/stats — Group activity statistics\n"
)

NOTES_HELP = (
    "📝 <b>Notes</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/save [name] [content] — Create and save a note\n"
    "/get [name] — Retrieve a saved note\n"
    "#notename — Retrieve a note by hashtag\n"
    "/clear [name] — Delete a specific note\n"
    "/notes — List all saved notes\n"
    "/clearall — Delete every note in this chat\n"
    "/privatenotes — Send notes privately via DM\n\n"
    "<i>Notes can contain text, photos, and buttons.\n"
    "Add buttons with [Label](url) syntax.</i>"
)

PIN_HELP = (
    "📌 <b>Pin</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/pin — Pin the replied-to message\n"
    "/unpin — Remove the current pinned message\n"
    "/unpinall — Clear all pinned messages\n"
    "/pinned — Show the currently pinned message\n"
    "/antichannelpin — Block automatic channel post pins\n\n"
    "<i>Reply to a message then use /pin to pin it.</i>"
)

PRIVACY_HELP = (
    "🔐 <b>Privacy</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/privacy — Manage your personal data stored by the bot\n\n"
    "<b>Data stored:</b> User ID, username, first name,\n"
    "message count, warning records.\n\n"
    "<i>You can request deletion of your data at any time.</i>"
)

PURGES_HELP = (
    "🗑️ <b>Purges</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/purge — Delete all messages from replied message to now\n"
    "/del — Delete a single replied-to message\n"
    "/spurge — Silent mass deletion\n"
    "/purgefrom — Set the start point for ranged deletion\n"
    "/purgeto — Set the end point for ranged deletion\n\n"
    "<i>Reply to the first message you want deleted, then /purge.</i>"
)

REPORTS_HELP = (
    "🚨 <b>Reports</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/report — Alert all group admins about a replied message\n"
    "@admin — Also triggers a report to admins\n"
    "/reports — Toggle whether users can use /report\n\n"
    "<i>All online admins receive a notification with a link to the message.</i>"
)

RULES_HELP = (
    "📜 <b>Rules</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setrules [text] — Define and save group rules\n"
    "/rules — View the current group rules\n"
    "/resetrules — Reset rules to default\n"
    "/privaterules — Send rules privately via DM\n"
    "/setrulesbutton [text] — Customize the rules button label\n\n"
    "<i>Rules are shown when members use /rules or via the welcome message.</i>"
)

TOPICS_HELP = (
    "💬 <b>Topics (Forum Groups)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/newtopic [name] — Create a new forum topic\n"
    "/renametopic [name] — Rename the current topic\n"
    "/closetopic — Close the current topic\n"
    "/reopentopic — Reopen a closed topic\n"
    "/deletetopic — Delete the current topic\n"
    "/actiontopic — Get the default action topic\n"
    "/setactiontopic — Set the default topic for mod actions\n\n"
    "<i>Only works in forum-style supergroups with topics enabled.</i>"
)

WARNINGS_HELP = (
    "⚠️ <b>Warnings</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Giving Warnings</b>\n"
    "/warn [user] — Give a formal warning\n"
    "/dwarn [user] — Warn and delete the replied message\n"
    "/swarn [user] — Warn user silently\n\n"
    "<b>Checking &amp; Removing</b>\n"
    "/warns [user] — Check a user's warning count\n"
    "/rmwarn [user] — Remove the user's latest warning\n"
    "/resetwarn [user] — Clear all warnings for a user\n"
    "/resetallwarns — Clear all warnings in this chat\n\n"
    "<b>Configuration</b>\n"
    "/warnlimit [num] — Set the warning threshold (default: 3)\n"
    "/warntime [time] — Set warning expiration (e.g. 7d, 1h)\n"
    "/warnmode [action] — Set punishment at limit\n"
    "  Actions: ban / kick / mute / tban / tmute\n\n"
    "<i>Reaching the warn limit triggers the configured punishment.</i>"
)

GAMES_HELP = (
    "🎮 <b>Games</b> — Everyone can play\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Guessing Games</b>\n"
    "/guess — Guess the anime character from photo\n"
    "/pick — Tap a button to guess the character\n"
    "/cricket — Guess the cricketer from their photo\n"
    "/trivia — Answer first and win points\n"
    "/hangman — Guess the hidden word letter by letter\n"
    "/wordmaster — Set a secret word for others to guess\n\n"
    "<b>vs Bot / PvP</b>\n"
    "/tictactoe /rps /playcricket /snake /ludo\n\n"
    "<b>Random Fun</b>\n"
    "/dice /roll /coinflip /8ball /truth /dare\n"
    "/joke /love /choose /flip /meme /poll\n\n"
    "<b>Scores</b>\n"
    "/top — Top trivia scorers\n"
    "/ranking — Most active members\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🆕 <b>40 New Games</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Quiz:</b> /mathquiz /scramble /riddle /flag /capital\n"
    "/emoji_movie /fill /oddoneout /missing\n"
    "/sport_quiz /science_quiz /geo_quiz /history_quiz\n"
    "/music_quiz /food_quiz /movie_quiz /coding_quiz\n"
    "/anime_quiz /cricket_quiz /whoami /lyric_guess\n"
    "/emoji_riddle /countryguess /decode\n\n"
    "<b>Word:</b> /wordchain /lastletter /typerace\n"
    "/rhyme_game /synonym_game /antonym_game\n"
    "/anagram_game /category_game\n\n"
    "<b>Logic:</b> /fast_math /prime /numberbomb /mixword\n\n"
    "<b>Social:</b> /would_you /versus /neverhave /zodiac\n"
)

COLLECTION_HELP = (
    "🃏 <b>Collection</b> — Collect &amp; show off your cards\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/collection — View your collected characters\n"
    "/harem — View your harem collection\n"
    "/coins — Check your RB coin balance\n"
    "/rb_leaderboard — Top RB coin earners\n\n"
    "<b>How to collect:</b>\n"
    "Play /cricket, /guess, or /pick — answer correctly to earn a card!\n"
    "Rarities: 🔵 Common → 🟢 Uncommon → 🟠 Rare → 🟣 Epic → ⭐ Legendary"
)

TOOLS_HELP = (
    "🔧 <b>Tools</b> — Info, Calculators &amp; Converters\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Info &amp; Search</b>\n"
    "/weather /define /fact /number /crypto /ip\n"
    "/urban /translate /lyrics /shorturl\n\n"
    "<b>Calculators</b>\n"
    "/calc /bmi /age /countdown /percent\n\n"
    "<b>Unit Converters</b>\n"
    "/temp /length /weight /speed /currency\n\n"
    "<b>Generators</b>\n"
    "/password /uuid /qr\n\n"
    "<b>Time, Color &amp; AFK</b>\n"
    "/time /color /afk /unafk\n\n"
    "<b>Other</b>\n"
    "/quote /remind /id /ping /stats"
)

CREATIVE_HELP = (
    "🎨 <b>Creative &amp; Image Tools</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>AI Images:</b> /image [prompt] /link [prompt]\n"
    "<b>Anime:</b> /waifu /animepic\n\n"
    "<b>Text Transform</b>\n"
    "/reverse /mock /aesthetic /bold /italic\n"
    "/binary /morse /base64e /base64d\n"
    "/sha256 /md5 /clap /spoiler /urlencode\n"
    "/urldecode /anagram /emojify /piglatin /wordcount"
)

FUN_HELP = (
    "😂 <b>Fun Commands</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Jokes:</b> /chuck /dadjoke /insult\n\n"
    "<b>Social:</b> /compliment /roast /motivation /rate\n\n"
    "<b>Games:</b> /slot /toss /randomnum\n\n"
    "<b>Also in Games tab:</b>\n"
    "/truth /dare /8ball /dice /coinflip /rps\n"
    "/joke /love /meme /trivia /hangman"
)

MUSIC_HELP = (
    "🎵 <b>Music</b> — Download &amp; play songs\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/play [song or URL] — Search YouTube &amp; send audio\n"
    "/sdownload [song/url] — Download as MP3\n"
    "/download [url] — Download video\n"
    "/queue — View the song queue\n"
    "/nowplaying — Currently playing song\n"
    "/pause /resume /skip /stop — VC controls\n\n"
    "<i>💡 /play sends the audio as a Telegram file you can save.</i>"
)

ANIME_HELP = (
    "🎌 <b>Anime</b> — 50 anime commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/anime /manga /achar /topanime /seasonal\n"
    "/randomanim /upcoming /popular /airing\n"
    "/animegenre /animerec\n\n"
    "<b>Anime Fun</b>\n"
    "/animequote /animefact2 /animefight /animeship\n"
    "/animematch /animepower /animeclan /animeaura\n"
    "/animesensei /animewho\n\n"
    "<b>Reaction GIFs</b>\n"
    "/pat /hug /kiss /slap /poke /cuddle /bonk /punch\n"
    "/adance /wave /blush /cryanime /laugh /smug /nom\n"
    "/wink /bite /kick /yeet /baka /highfive /handshake\n"
    "/nod /asleep /stare\n\n"
    "<b>Profile:</b> /aniprofile /addwatch /myanilist"
)

DOWNLOADS_HELP = (
    "📥 <b>Downloads</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/download [url] — Download video from any platform\n"
    "  ↳ YouTube, Instagram, Twitter, TikTok &amp; more\n\n"
    "/sdownload [url or song name] — Download as MP3\n\n"
    "<i>Files are sent directly to the chat.</i>"
)

# ═══════════════════════════════════════════════════════════
#  KEYBOARDS  (no emojis on buttons)
# ═══════════════════════════════════════════════════════════

def _build_kb(include_add_btn=False, bot_username=""):
    rows = []
    if include_add_btn:
        rows.append([InlineKeyboardButton(
            "Add me to your group",
            url=(
                f"https://t.me/{bot_username}?startgroup=true"
                "&admin=restrict_members+ban_users+delete_messages+pin_messages+invite_users"
            )
        )])
    rows += [
        # Management
        [
            InlineKeyboardButton("Admin",          callback_data="help_admin"),
            InlineKeyboardButton("Antiflood",      callback_data="help_antiflood"),
            InlineKeyboardButton("AntiRaid",       callback_data="help_antiraid"),
        ],
        [
            InlineKeyboardButton("Approval",       callback_data="help_approval"),
            InlineKeyboardButton("Bans",           callback_data="help_bans"),
            InlineKeyboardButton("Blocklists",     callback_data="help_blocklists"),
        ],
        [
            InlineKeyboardButton("CAPTCHA",        callback_data="help_captcha"),
            InlineKeyboardButton("Clean Commands", callback_data="help_clean"),
            InlineKeyboardButton("Clean Service",  callback_data="help_clean"),
        ],
        [
            InlineKeyboardButton("Connections",    callback_data="help_connections"),
            InlineKeyboardButton("Disabling",      callback_data="help_disabling"),
            InlineKeyboardButton("Federations",    callback_data="help_federations"),
        ],
        [
            InlineKeyboardButton("Filters",        callback_data="help_filters"),
            InlineKeyboardButton("Greetings",      callback_data="help_greetings"),
            InlineKeyboardButton("Import/Export",  callback_data="help_importexport"),
        ],
        [
            InlineKeyboardButton("Languages",      callback_data="help_languages"),
            InlineKeyboardButton("Locks",          callback_data="help_locks"),
            InlineKeyboardButton("Log Channels",   callback_data="help_logchannels"),
        ],
        [
            InlineKeyboardButton("Misc",           callback_data="help_misc"),
            InlineKeyboardButton("Notes",          callback_data="help_notes"),
            InlineKeyboardButton("Pin",            callback_data="help_pin"),
        ],
        [
            InlineKeyboardButton("Privacy",        callback_data="help_privacy"),
            InlineKeyboardButton("Purges",         callback_data="help_purges"),
            InlineKeyboardButton("Reports",        callback_data="help_reports"),
        ],
        [
            InlineKeyboardButton("Rules",          callback_data="help_rules"),
            InlineKeyboardButton("Topics",         callback_data="help_topics"),
            InlineKeyboardButton("Warnings",       callback_data="help_warnings"),
        ],
        # Entertainment + Group Help
        [
            InlineKeyboardButton("Games",          callback_data="help_games"),
            InlineKeyboardButton("Collection",     callback_data="help_collection"),
            InlineKeyboardButton("Anime",          callback_data="help_anime"),
        ],
        [
            InlineKeyboardButton("Tools",          callback_data="help_tools"),
            InlineKeyboardButton("Creative",       callback_data="help_creative"),
            InlineKeyboardButton("Fun",            callback_data="help_fun"),
        ],
        [
            InlineKeyboardButton("Music",          callback_data="help_music"),
            InlineKeyboardButton("Downloads",      callback_data="help_downloads"),
            InlineKeyboardButton("Group Help",     callback_data="help_group"),
        ],
    ]
    return InlineKeyboardMarkup(rows)

_MAIN_KB = _build_kb()
_BACK_KB  = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="help_back")]])

# ═══════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot          = await context.bot.get_me()
    add_btn      = _build_kb(include_add_btn=True, bot_username=bot.username)
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

    mapping = {
        # Management
        "help_admin":        ADMIN_HELP,
        "help_antiflood":    ANTIFLOOD_HELP,
        "help_antiraid":     ANTIRAID_HELP,
        "help_approval":     APPROVAL_HELP,
        "help_bans":         BANS_HELP,
        "help_blocklists":   BLOCKLISTS_HELP,
        "help_captcha":      CAPTCHA_HELP,
        "help_clean":        CLEAN_HELP,
        "help_connections":  CONNECTIONS_HELP,
        "help_disabling":    DISABLING_HELP,
        "help_federations":  FEDERATIONS_HELP,
        "help_filters":      FILTERS_HELP,
        "help_greetings":    GREETINGS_HELP,
        "help_importexport": IMPORTEXPORT_HELP,
        "help_languages":    LANGUAGES_HELP,
        "help_locks":        LOCKS_HELP,
        "help_logchannels":  LOGCHANNELS_HELP,
        "help_misc":         MISC_HELP,
        "help_notes":        NOTES_HELP,
        "help_pin":          PIN_HELP,
        "help_privacy":      PRIVACY_HELP,
        "help_purges":       PURGES_HELP,
        "help_reports":      REPORTS_HELP,
        "help_rules":        RULES_HELP,
        "help_topics":       TOPICS_HELP,
        "help_warnings":     WARNINGS_HELP,
        # Entertainment
        "help_games":        GAMES_HELP,
        "help_collection":   COLLECTION_HELP,
        "help_tools":        TOOLS_HELP,
        "help_creative":     CREATIVE_HELP,
        "help_fun":          FUN_HELP,
        "help_music":        MUSIC_HELP,
        "help_downloads":    DOWNLOADS_HELP,
        "help_anime":        ANIME_HELP,
        # Group Help
        "help_group":        GROUP_HELP,
    }

    if query.data in mapping:
        text = mapping[query.data]
        if len(text) > 4000:
            text = text[:4000] + "\n\n<i>...</i>"
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=_BACK_KB
        )
    elif query.data == "help_back":
        await query.edit_message_text(
            "📖 <b>Choose a help category:</b>",
            parse_mode="HTML",
            reply_markup=_MAIN_KB,
        )
