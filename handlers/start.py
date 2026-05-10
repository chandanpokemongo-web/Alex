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

# ═══════════════════════════════════════════════════════════
#  MANAGEMENT HELP TEXTS
# ═══════════════════════════════════════════════════════════

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
    "/silentactions — Toggle quiet moderation (no reply messages)\n\n"
    "<i>Use /setflood 0 to disable flood protection.</i>"
)

ANTIRAID_HELP = (
    "⚔️ <b>AntiRaid</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/antiraid — Enable or disable raid protection\n"
    "/autoantiraid — Automate raid detection and protection\n"
    "/raidtime [sec] — Set how long a raid is considered active\n"
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
    "/unban [user] — Remove a user from the ban list\n"
    "/tban [user] [time] — Temporarily ban (e.g. 1h, 30m, 2d)\n"
    "/dban [user] — Ban and delete the replied message\n"
    "/sban [user] — Ban user silently (no notification)\n"
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
    "/rmallowlist [item] — Remove item from the allow list\n\n"
    "<i>Blocked words are automatically actioned when sent in the chat.</i>"
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
    "/cleanservice — Delete Telegram system alerts (join/leave/pin)\n"
    "/cleanservicetypes — List which service message types are cleaned\n"
    "/keepservice — Stop deleting service alerts\n"
    "/nocleanservice — Same as keepservice\n\n"
    "<b>Clean Bot Commands</b>\n"
    "/cleancommand — Auto-delete bot command messages after responding\n"
    "/keepcommand — Keep bot command messages (don't auto-delete)\n"
    "/disableable — List all commands that can be toggled off\n"
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
    "<i>Connect lets you manage your group directly from your DMs with the bot.</i>"
)

DISABLING_HELP = (
    "🔕 <b>Disabling</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/disable [command] — Turn off a specific command in this chat\n"
    "/enable [command] — Re-enable a disabled command\n"
    "/disableable — List all commands that can be disabled\n"
    "/disabled — Show all currently disabled commands\n"
    "/disableadmin — Disable a command for admin users too\n"
    "/disabledel — Delete messages that trigger a disabled command\n\n"
    "<i>Disabling a command makes the bot ignore it in this chat.</i>"
)

FEDERATIONS_HELP = (
    "🌐 <b>Federations (Global Bans)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Setup</b>\n"
    "/newfed [name] — Create a new federation\n"
    "/joinfed [fed_id] — Connect your chat to a federation\n"
    "/subfed [fed_id] — Subscribe to another federation's bans\n"
    "/unsubfed [fed_id] — Unsubscribe from a federation\n"
    "/delfed — Delete your federation\n\n"
    "<b>Banning</b>\n"
    "/fban [user] [reason] — Federation-wide ban across all joined chats\n"
    "/unfban [user] — Remove a federation ban\n"
    "/fedstat [user] — Check if a user is federation banned\n\n"
    "<b>Management</b>\n"
    "/fedinfo — View federation details\n"
    "/fedadmins — List federation staff\n"
    "/fedsubs — View subscribed federations\n"
    "/fedpromote [user] — Add a federation admin\n"
    "/feddemote [user] — Remove a federation admin\n"
    "/fedexport — Export the federation ban list\n"
    "/fedimport — Upload and import a ban list\n\n"
    "<b>Ownership</b>\n"
    "/renamefed [name] — Rename your federation\n"
    "/fedtransfer [@user] — Transfer federation ownership\n"
    "/fednotif — Toggle private message alerts for fed bans\n"
    "/fedreason — Require a reason for federation bans\n"
    "/setfedlog [channel] — Log federation events to a channel\n"
    "/unsetfedlog — Stop federation logging\n"
    "/setfedlang [lang] — Set federation log language\n"
)

FILTERS_HELP = (
    "🔍 <b>Filters</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/filter [word] [reply] — Auto-reply when a keyword is detected\n"
    "/stop [word] — Remove a specific word filter\n"
    "/stopall — Delete all active filters in this chat\n"
    "/filters — List all active filters in this chat\n\n"
    "<i>Filters trigger an automatic reply whenever the keyword appears in chat.\n"
    "You can include buttons in filter replies using [Label](url) format.</i>"
)

GREETINGS_HELP = (
    "👋 <b>Greetings</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setwelcome [text] — Set a welcome message for new members\n"
    "/setgoodbye [text] — Set a goodbye message for leaving members\n"
    "/resetwelcome — Restore the default welcome message\n"
    "/resetgoodbye — Restore the default goodbye message\n\n"
    "<b>Variables you can use in messages:</b>\n"
    "  {first} — User's first name\n"
    "  {last} — User's last name\n"
    "  {username} — User's @username\n"
    "  {mention} — Clickable mention link\n"
    "  {id} — User's Telegram ID\n"
    "  {chatname} — Group name\n\n"
    "<i>You can attach a photo to /setwelcome and add buttons with [Label](url).</i>"
)

IMPORTEXPORT_HELP = (
    "📦 <b>Import / Export</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/export — Back up all chat settings to a file\n"
    "/import — Restore chat settings from an exported file\n"
    "/reset — Wipe all bot settings for this chat\n\n"
    "<i>Export saves rules, welcome messages, filters, notes, locks, and more.\n"
    "Import restores everything from a previously exported backup file.</i>"
)

LANGUAGES_HELP = (
    "🌍 <b>Languages</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setlang [code] — Change the bot language for this chat\n\n"
    "<b>Available language codes:</b>\n"
    "  en — English\n"
    "  hi — Hindi\n"
    "  ar — Arabic\n"
    "  ur — Urdu\n"
    "  es — Spanish\n"
    "  fr — French\n\n"
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
    "/allowlist [item] — Exempt a specific user or item from locks\n"
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
    "<b>Available log categories:</b>\n"
    "  ban, kick, mute, warn, promote, demote,\n"
    "  filter, lock, welcome, note, settings\n\n"
    "<i>Make the bot an admin in your log channel so it can post there.</i>"
)

MISC_HELP = (
    "⚙️ <b>Miscellaneous</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/id — Get your Telegram user ID\n"
    "/info [user] — See user details (ID, status, warnings)\n"
    "/runs — Get a random escape string\n"
    "/donate — Support the bot creator\n"
    "/markdownhelp — Formatting guide and syntax reference\n"
    "/limits — Show bot usage constraints\n"
    "/pinned — Get the current pinned message\n"
    "/unpinall — Clear all pinned messages\n"
    "/antichannelpin — Block automatic channel pins in the chat\n"
    "/cleanlinked — Delete forwarded channel posts\n"
    "/ping — Check bot response time\n"
    "/stats — View group activity statistics\n"
)

NOTES_HELP = (
    "📝 <b>Notes</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/save [name] [content] — Create and save a custom note\n"
    "/get [name] — Retrieve a saved note\n"
    "#notename — Retrieve a note using a hashtag shortcut\n"
    "/clear [name] — Delete a specific note\n"
    "/notes — List all saved notes in this chat\n"
    "/clearall — Delete every note in this chat\n"
    "/privatenotes — Send notes privately via DM\n\n"
    "<i>Notes can contain text, photos, and buttons.\n"
    "Add buttons with [Label](url) syntax inside the note content.</i>"
)

PIN_HELP = (
    "📌 <b>Pin</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/pin — Pin the replied-to message (notifies all members)\n"
    "/unpin — Remove the current pinned message\n"
    "/unpinall — Clear all pinned messages in this chat\n"
    "/pinned — Show the currently pinned message\n"
    "/antichannelpin — Block automatic channel post pins\n\n"
    "<i>Reply to a message then use /pin to pin it.\n"
    "The bot must have Pin Messages permission in the group.</i>"
)

PRIVACY_HELP = (
    "🔐 <b>Privacy</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/privacy — Manage and view your personal data stored by the bot\n\n"
    "<b>Data the bot stores:</b>\n"
    "  - User ID and username\n"
    "  - First name\n"
    "  - Message count\n"
    "  - Warning records\n\n"
    "<i>You can request deletion of your data at any time using /privacy.</i>"
)

PURGES_HELP = (
    "🗑️ <b>Purges</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/purge — Delete all messages from replied message up to now\n"
    "/del — Delete a single replied-to message\n"
    "/spurge — Silent mass deletion (no confirmation message)\n"
    "/purgefrom — Set the start point for a ranged deletion\n"
    "/purgeto — Set the end point for a ranged deletion\n\n"
    "<i>Reply to the first message you want deleted, then use /purge.\n"
    "Requires Delete Messages permission in the group.</i>"
)

REPORTS_HELP = (
    "🚨 <b>Reports</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/report — Alert all group admins about a replied message\n"
    "@admin — Also triggers an admin report\n"
    "/reports — Toggle whether users can use /report in this chat\n\n"
    "<i>When a user sends /report, all online admins receive a notification\n"
    "with a link to the reported message.</i>"
)

RULES_HELP = (
    "📜 <b>Rules</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/setrules [text] — Define and save the group rules\n"
    "/rules — View the current group rules\n"
    "/resetrules — Reset rules back to default\n"
    "/privaterules — Send rules to the user privately via DM\n"
    "/setrulesbutton [text] — Customize the rules button label\n\n"
    "<i>Rules are shown to members who use /rules or via the welcome message.</i>"
)

TOPICS_HELP = (
    "💬 <b>Topics (Forum Groups)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/newtopic [name] — Create a new forum topic\n"
    "/renametopic [name] — Rename the current topic\n"
    "/closetopic — Close the current topic\n"
    "/reopentopic — Reopen a closed topic\n"
    "/deletetopic — Permanently delete the current topic\n"
    "/actiontopic — Get the default action topic\n"
    "/setactiontopic — Set the default topic for mod actions\n\n"
    "<i>These commands only work in forum-style supergroups with topics enabled.</i>"
)

WARNINGS_HELP = (
    "⚠️ <b>Warnings</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Giving Warnings</b>\n"
    "/warn [user] — Give a formal warning\n"
    "/dwarn [user] — Warn and delete the replied message\n"
    "/swarn [user] — Warn user silently (no public message)\n\n"
    "<b>Checking &amp; Removing</b>\n"
    "/warns [user] — Check a user's current warning count\n"
    "/rmwarn [user] — Remove the user's latest warning\n"
    "/resetwarn [user] — Clear all warnings for a user\n"
    "/resetallwarns — Clear all warnings in this entire chat\n\n"
    "<b>Configuration</b>\n"
    "/warnlimit [num] — Set the warning threshold (default: 3)\n"
    "/warntime [time] — Set warning expiration (e.g. 7d, 1h)\n"
    "/warnmode [action] — Set punishment at limit\n"
    "  Actions: ban / kick / mute / tban / tmute\n\n"
    "<i>Reaching the warn limit triggers the configured punishment automatically.</i>"
)

# ═══════════════════════════════════════════════════════════
#  ENTERTAINMENT HELP TEXTS
# ═══════════════════════════════════════════════════════════

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
    "/flip [a] [b] — Random decision between two\n"
    "/meme — Trending meme\n"
    "/poll [question] — Group poll\n\n"
    "<b>Scores</b>\n"
    "/top — Top trivia scorers\n"
    "/ranking — Most active members\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🆕 <b>40 New Games</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Quiz Games</b>\n"
    "/mathquiz /scramble /riddle /flag /capital\n"
    "/emoji_movie /fill /oddoneout /missing\n"
    "/sport_quiz /science_quiz /geo_quiz /history_quiz\n"
    "/music_quiz /food_quiz /movie_quiz /coding_quiz\n"
    "/anime_quiz /cricket_quiz /whoami /lyric_guess\n"
    "/emoji_riddle /countryguess /decode\n\n"
    "<b>Word &amp; Language</b>\n"
    "/wordchain /lastletter /typerace /rhyme_game\n"
    "/synonym_game /antonym_game /anagram_game /category_game\n\n"
    "<b>Number &amp; Logic</b>\n"
    "/fast_math /prime /numberbomb /mixword\n\n"
    "<b>Fun &amp; Social</b>\n"
    "/would_you /versus /neverhave /zodiac [sign]\n"
)

COLLECTION_HELP = (
    "🃏 <b>Collection</b> — Collect &amp; show off your cards\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>View Collection</b>\n"
    "/collection — View your collected characters\n"
    "  ↳ Tap any card to see their photo\n"
    "  ↳ Use Prev / Next to page through\n"
    "  ↳ Tap View Cards Inline to share as a photo grid\n\n"
    "/harem — View your harem collection (anime + cricketers)\n\n"
    "<b>Coins</b>\n"
    "/coins — Check your RB coin balance\n"
    "/rb_leaderboard — Top RB coin earners globally\n\n"
    "<b>How to collect</b>\n"
    "Play /cricket, /guess, or /pick games.\n"
    "Answer correctly → earn a random character card!\n"
    "Rarities: 🔵 Common → 🟢 Uncommon → 🟠 Rare → 🟣 Epic → ⭐ Legendary"
)

TOOLS_HELP = (
    "🔧 <b>Tools</b> — Info, Calculators &amp; Converters\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Info &amp; Search</b>\n"
    "/weather [city] — Current weather for any city\n"
    "/define [word] — Dictionary definition\n"
    "/fact — Random interesting fact\n"
    "/number [n] — Fun fact about any number\n"
    "/crypto [sym] — Crypto price (BTC/ETH/SOL)\n"
    "/ip [ip] — IP address geolocation\n"
    "/urban [word] — Urban Dictionary definition\n"
    "/translate [lang] [text] — Translate to any language\n"
    "/lyrics [artist] - [song] — Get song lyrics\n"
    "/shorturl [url] — Shorten any URL\n\n"
    "<b>Calculators</b>\n"
    "/calc [expr] — Calculator (e.g. 25*4+10)\n"
    "/bmi [weight kg] [height cm] — BMI calculator\n"
    "/age [DD/MM/YYYY] — Age from birthdate\n"
    "/countdown [DD/MM/YYYY] — Days until a date\n"
    "/percent [value] [total] — Percentage calculator\n\n"
    "<b>Unit Converters</b>\n"
    "/temp [val] [from] [to] — Temperature (C/F/K)\n"
    "/length [val] [from] [to] — Length (m/km/ft/miles)\n"
    "/weight [val] [from] [to] — Weight (kg/lb/oz)\n"
    "/speed [val] [from] [to] — Speed (kph/mph/knots)\n"
    "/currency [amt] [from] [to] — Currency convert\n\n"
    "<b>Generators</b>\n"
    "/password [length] — Secure random password\n"
    "/uuid — Generate a random UUID\n"
    "/qr [text] — Generate a QR code image\n\n"
    "<b>Time, Color &amp; AFK</b>\n"
    "/time [tz] — Current time (IST/UTC/EST/JST)\n"
    "/color [hex] — Color info + preview\n"
    "/afk [reason] — Set yourself as Away\n"
    "/unafk — Remove AFK status\n\n"
    "<b>Other</b>\n"
    "/quote — Random motivational quote\n"
    "/remind [time] [msg] — Set a reminder\n"
    "/id — Your Telegram user ID\n"
    "/ping — Check bot response time\n"
    "/stats — Group activity statistics"
)

CREATIVE_HELP = (
    "🎨 <b>Creative &amp; Image Tools</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>AI Image Generation</b>\n"
    "/image [prompt] — Generate AI image from any prompt\n"
    "/link [prompt] — Get a direct shareable image URL\n\n"
    "<b>Anime Images</b>\n"
    "/waifu — Random anime waifu image\n"
    "/animepic — Random anime character image\n\n"
    "<b>Text Transform</b>\n"
    "/reverse [text] — Reverse your text\n"
    "/mock [text] — SpOnGeBoB mOcKiNg CaSe\n"
    "/aesthetic [text] — ａｅｓｔｈｅｔｉｃ text\n"
    "/bold [text] — 𝗕𝗼𝗹𝗱 Unicode text\n"
    "/italic [text] — 𝘐𝘵𝘢𝘭𝘪𝘤 Unicode text\n"
    "/binary [text] — Text to binary\n"
    "/morse [text] — Text to Morse code\n"
    "/base64e [text] — Base64 encode\n"
    "/base64d [text] — Base64 decode\n"
    "/sha256 [text] — SHA-256 hash\n"
    "/md5 [text] — MD5 hash\n"
    "/clap [text] — c👏l👏a👏p text\n"
    "/spoiler [text] — ||hide as spoiler||\n"
    "/urlencode [text] — URL encode\n"
    "/urldecode [text] — URL decode\n"
    "/anagram [text] — Shuffle letters\n"
    "/emojify [text] — Add emojis after each word\n"
    "/piglatin [text] — Pig Latin\n"
    "/wordcount [text] — Word &amp; character count"
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
    "/rate [@user] — Rate someone's personality\n\n"
    "<b>Games</b>\n"
    "/slot — 🎰 Slot machine\n"
    "/toss — 🪙 Simple coin toss\n"
    "/randomnum [min] [max] — Random number in range\n\n"
    "<b>Also in Games tab:</b>\n"
    "/truth, /dare, /8ball, /dice, /coinflip, /rps,\n"
    "/joke, /love, /meme, /trivia, /hangman"
)

MUSIC_HELP = (
    "🎵 <b>Music</b> — Download &amp; play songs\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/play [song name or URL] — Search YouTube &amp; send audio\n"
    "/sdownload [song/url] — Download song as MP3\n"
    "/download [url] — Download video (YouTube, IG, TikTok)\n"
    "/queue — View the current song queue\n"
    "/nowplaying — Show the currently playing song\n"
    "/pause — Pause voice chat playback\n"
    "/resume — Resume voice chat playback\n"
    "/skip — Skip to the next song\n"
    "/stop — Stop music and leave voice chat\n\n"
    "<i>💡 /play downloads audio and sends it as a Telegram file.\n"
    "   Listen right in chat or save it to your phone.</i>"
)

ANIME_HELP = (
    "🎌 <b>Anime</b> — 50 anime commands\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Search &amp; Info</b>\n"
    "/anime [title] /manga [title] /achar [name]\n"
    "/topanime /seasonal /randomanim /upcoming\n"
    "/popular /airing /animegenre [genre] /animerec\n\n"
    "<b>Anime Fun &amp; Games</b>\n"
    "/animequote /animefact2 /animefight /animeship\n"
    "/animematch /animepower /animeclan /animeaura\n"
    "/animesensei /animewho\n\n"
    "<b>Reaction GIFs</b> (reply to a user or use alone)\n"
    "/pat /hug /kiss /slap /poke /cuddle /bonk /punch\n"
    "/adance /wave /blush /cryanime /laugh /smug /nom\n"
    "/wink /bite /kick /yeet /baka /highfive /handshake\n"
    "/nod /asleep /stare\n\n"
    "<b>Anime Profile</b>\n"
    "/aniprofile — Your anime profile\n"
    "/addwatch [title] — Add to watchlist\n"
    "/myanilist — View your watchlist\n"
)

DOWNLOADS_HELP = (
    "📥 <b>Downloads</b> — Download videos &amp; songs\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "/download [url] — Download video from any platform\n"
    "  ↳ Supports YouTube, Instagram, Twitter, TikTok &amp; more\n"
    "  ↳ Up to 4K quality with quality selector\n\n"
    "/sdownload [url or song name] — Download as MP3 audio\n"
    "  ↳ Extracts audio from any video URL\n"
    "  ↳ Or search by song name\n\n"
    "<i>Files are sent directly to the chat.</i>"
)

# ═══════════════════════════════════════════════════════════
#  KEYBOARDS  (no emojis on buttons)
# ═══════════════════════════════════════════════════════════

_MAIN_KB = InlineKeyboardMarkup([
    # ── Management ──────────────────────────────────────────
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
    # ── Entertainment ────────────────────────────────────────
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
    ],
])

_BACK_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("Back", callback_data="help_back")]
])

# ═══════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = await context.bot.get_me()
    bot_username = bot.username

    add_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "Add me to your group",
            url=(
                f"https://t.me/{bot_username}?startgroup=true"
                "&admin=restrict_members+ban_users+delete_messages+pin_messages+invite_users"
            )
        )],
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
        # Entertainment
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
    }

    if query.data in mapping:
        text = mapping[query.data]
        # Telegram max message length guard
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
