"""
Music handler — two modes:
  FILE MODE (default): searches YouTube, downloads audio, sends as Telegram audio file
                       with a rich thumbnail card + progress bar.
  VOICE CHAT MODE:     enabled when API_ID + API_HASH are set in config.py.
                       Uses pyrogram + pytgcalls to stream into a voice chat.
"""

import asyncio
import logging
import os
import tempfile
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path

import httpx
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import API_ID, API_HASH, BOT_TOKEN

logger = logging.getLogger(__name__)

# ── Voice-chat mode (optional) ────────────────────────────────────────────────
VOICE_CHAT_MODE = False
_pyrogram_client = None
_group_calls: dict = {}
_tempfiles: dict   = {}

# ── Voice-chat note ───────────────────────────────────────────────────────────
# Bot tokens (bot_token=...) CANNOT join Telegram group voice chats via MTProto.
# Only user-account sessions can do that. To enable VC mode you would need to
# create a Pyrogram session with a real phone number and store the SESSION_STRING.
# Until then, FILE MODE is the default and works perfectly.
# ─────────────────────────────────────────────────────────────────────────────
if False and API_ID and API_HASH:          # disabled — bot token can't join VC
    try:
        from pyrogram import Client
        from pytgcalls import GroupCallFactory

        _pyrogram_client = Client(
            "music_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workdir="/tmp",
        )
        VOICE_CHAT_MODE = True
        logger.info("Voice chat mode: pyrogram + pytgcalls loaded OK.")
    except Exception as _vc_err:
        logger.warning(f"Voice chat mode unavailable: {_vc_err}")
        VOICE_CHAT_MODE = False

# ── State ─────────────────────────────────────────────────────────────────────
_queues: dict          = defaultdict(list)
_now_playing: dict     = {}
_paused: dict          = {}
_play_messages: dict   = {}       # {chat_id: message} — the now-playing card
_play_start_times: dict = {}      # {chat_id: datetime}


# ── Rich Play Card helpers ────────────────────────────────────────────────────

def _fmt_dur(seconds: int) -> str:
    if not seconds:
        return "?:??"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _progress_bar(elapsed: int, total: int) -> str:
    width = 16
    if total <= 0:
        return f"0:00 {'─' * width} ?:??"
    pct  = min(elapsed / total, 1.0)
    pos  = int(width * pct)
    bar  = "─" * pos + "●" + "─" * max(0, width - pos - 1)
    rem  = max(0, total - elapsed)
    return f"{_fmt_dur(elapsed)} {bar} -{_fmt_dur(rem)}"


def _play_card_caption(song: dict, elapsed: int = 0) -> str:
    title     = song.get("title", "Unknown")[:80]
    uploader  = song.get("uploader", "")
    duration  = song.get("duration", 0)
    requester = song.get("requested_by", "?")
    dur_str   = f"{_fmt_dur(duration)}" if duration else "unknown"
    bar       = _progress_bar(elapsed, duration)
    status    = "📥 Downloading…" if elapsed == 0 else "✅ Sending audio file…"

    return (
        f"🎵 <b>{status}</b>\n\n"
        f"🎶  <b>{title}</b>\n"
        f"👤  Artist: {uploader or 'Unknown'}\n"
        f"⏱  Duration: {dur_str}\n"
        f"🙋  Requested by: {requester}\n\n"
        f"<code>{bar}</code>\n"
        f"<i>Audio file will be sent shortly…</i>"
    )


def _play_card_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    paused = _paused.get(chat_id, False)
    pp_cb  = f"music_resume_{chat_id}" if paused else f"music_pause_{chat_id}"
    pp_btn = "▶" if paused else "⏸"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(pp_btn, callback_data=pp_cb),
        InlineKeyboardButton("⏭",   callback_data=f"music_skip_{chat_id}"),
        InlineKeyboardButton("⏹",   callback_data=f"music_stop_{chat_id}"),
        InlineKeyboardButton("📋",   callback_data=f"music_queue_{chat_id}"),
    ]])


async def _send_play_card(chat_id: int, song: dict,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send thumbnail photo + rich caption card. Stores message in _play_messages."""
    caption   = _play_card_caption(song)
    kb        = _play_card_keyboard(chat_id)
    thumbnail = song.get("thumbnail", "")

    if thumbnail:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
                r = await c.get(thumbnail, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 500:
                    img      = BytesIO(r.content)
                    img.name = "thumb.jpg"
                    msg = await context.bot.send_photo(
                        chat_id, photo=img, caption=caption,
                        parse_mode="HTML", reply_markup=kb,
                    )
                    _play_messages[chat_id]    = msg
                    _play_start_times[chat_id] = datetime.utcnow()
                    return
        except Exception as e:
            logger.warning(f"Thumbnail card failed: {e}")

    # Fallback — text card
    msg = await context.bot.send_message(
        chat_id, caption, parse_mode="HTML", reply_markup=kb)
    _play_messages[chat_id]    = msg
    _play_start_times[chat_id] = datetime.utcnow()


async def _update_play_card(chat_id: int, song: dict, elapsed: int = 0) -> None:
    msg = _play_messages.get(chat_id)
    if not msg:
        return
    try:
        cap = _play_card_caption(song, elapsed)
        kb  = _play_card_keyboard(chat_id)
        if msg.photo:
            await msg.edit_caption(cap, parse_mode="HTML", reply_markup=kb)
        else:
            await msg.edit_text(cap, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass


# ── Job-queue progress bar ────────────────────────────────────────────────────

async def _progress_job(context) -> None:
    chat_id = context.job.data["chat_id"]
    if chat_id not in _now_playing or _paused.get(chat_id):
        return
    song  = _now_playing[chat_id]
    start = _play_start_times.get(chat_id)
    if not start:
        return
    elapsed = int((datetime.utcnow() - start).total_seconds())
    total   = song.get("duration", 0)
    if total > 0 and elapsed >= total + 10:
        context.job.schedule_removal()
        return
    await _update_play_card(chat_id, song, elapsed)


def _start_progress_job(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = f"progress_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(name):
        j.schedule_removal()
    context.job_queue.run_repeating(
        _progress_job, interval=15, first=15,
        data={"chat_id": chat_id}, name=name,
    )


def _stop_progress_job(chat_id: int, context) -> None:
    if context and hasattr(context, "job_queue"):
        for j in context.job_queue.get_jobs_by_name(f"progress_{chat_id}"):
            j.schedule_removal()


# ── Search / Download ─────────────────────────────────────────────────────────

async def _search_info(query: str) -> dict | None:
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch1",
        "extract_flat": False,
    }
    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return {
                "title":     info.get("title", query),
                "url":       info.get("url", ""),
                "webpage":   info.get("webpage_url", ""),
                "duration":  info.get("duration", 0),
                "uploader":  info.get("uploader", ""),
                "thumbnail": info.get("thumbnail", ""),
            }

    try:
        result = await loop.run_in_executor(None, _run)
        return result if result["url"] else None
    except Exception:
        return None


async def _download_mp3(song: dict) -> str | None:
    tmpdir  = tempfile.mkdtemp(prefix="tgbot_music_")
    outpath = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outpath,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{"key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3", "preferredquality": "128"}],
    }
    loop = asyncio.get_event_loop()

    def _do():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(song["webpage"] or song["url"], download=True)

    try:
        await loop.run_in_executor(None, _do)
    except Exception as e:
        logger.warning(f"MP3 download failed: {e}")
        return None

    files = list(Path(tmpdir).glob("*.mp3")) or list(Path(tmpdir).glob("*"))
    return str(files[0]) if files else None


def _cleanup_temp(chat_id: int) -> None:
    path = _tempfiles.pop(chat_id, None)
    if path and os.path.exists(path):
        try:
            os.remove(path)
            parent = os.path.dirname(path)
            if os.path.isdir(parent):
                os.rmdir(parent)
        except Exception:
            pass


# ── File mode ─────────────────────────────────────────────────────────────────

async def _download_and_send(chat_id: int, song: dict,
                              context: ContextTypes.DEFAULT_TYPE,
                              status_msg=None) -> None:
    """Download and send audio file. Updates the status message when done."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outpath  = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outpath,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{"key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3", "preferredquality": "192"}],
        }
        loop = asyncio.get_event_loop()

        def _do():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(song["webpage"] or song["url"], download=True)

        try:
            await loop.run_in_executor(None, _do)
        except Exception as e:
            await context.bot.send_message(
                chat_id,
                f"❌ Download failed: <code>{str(e)[:200]}</code>",
                parse_mode="HTML",
            )
            return

        mp3s = list(Path(tmpdir).glob("*.mp3")) or list(Path(tmpdir).glob("*"))
        if not mp3s:
            if status_msg:
                try: await status_msg.edit_text("❌ No audio file found after download.")
                except Exception: pass
            else:
                await context.bot.send_message(chat_id, "❌ No audio file found after download.")
            return

        filepath = str(mp3s[0])
        if os.path.getsize(filepath) > 50 * 1024 * 1024:
            if status_msg:
                try: await status_msg.edit_text("❌ Song too large (>50 MB). Try a shorter song.")
                except Exception: pass
            else:
                await context.bot.send_message(chat_id, "❌ Song too large (>50 MB).")
            return

        title    = song.get("title", "song")
        artist   = song.get("uploader", "Unknown")
        duration = song.get("duration")

        # Update status: sending
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"📤 <b>Sending audio…</b>\n\n"
                    f"🎶 <b>{title[:80]}</b>\n👤 {artist}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        with open(filepath, "rb") as fh:
            await context.bot.send_audio(
                chat_id, audio=fh,
                caption=f"🎵 <b>{title[:200]}</b>\n👤 {artist}",
                parse_mode="HTML",
                duration=duration,
                title=title[:64],
                performer=artist[:64],
            )

        # Mark status as done
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"✅ <b>Done!</b> Audio sent above.\n\n"
                    f"🎶 <b>{title[:80]}</b>\n👤 {artist}",
                    parse_mode="HTML",
                )
            except Exception:
                pass


# ── VC mode ───────────────────────────────────────────────────────────────────

async def _vc_play_song(chat_id: int, song: dict,
                        context: ContextTypes.DEFAULT_TYPE,
                        status_msg=None) -> bool:
    if status_msg:
        try:
            await status_msg.edit_text(
                f"⬇️ <b>Downloading…</b>\n{song['title'][:60]}", parse_mode="HTML")
        except Exception:
            pass

    filepath = await _download_mp3(song)
    if not filepath:
        if status_msg:
            await status_msg.edit_text("❌ Download failed.")
        return False

    _cleanup_temp(chat_id)
    _tempfiles[chat_id] = filepath

    try:
        gc = _group_calls.get(chat_id)
        if gc is None:
            from pytgcalls import GroupCallFactory
            factory = GroupCallFactory(_pyrogram_client)
            gc = factory.get_file_group_call(input_filename=filepath, play_on_repeat=False)
            _group_calls[chat_id] = gc
            await gc.start(chat_id)
        else:
            gc.input_filename = filepath

        _now_playing[chat_id] = song
        _paused[chat_id]      = False

        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        await _send_play_card(chat_id, song, context)
        _start_progress_job(chat_id, context)
        return True

    except Exception as e:
        _cleanup_temp(chat_id)
        _group_calls.pop(chat_id, None)
        err = str(e)
        hint = ("\n\n<i>Tip: Start a Voice Chat in this group first, then /play.</i>"
                if "GROUPCALL" in err or "not found" in err.lower()
                else f"\n<code>{err[:200]}</code>")
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"❌ Could not join voice chat.{hint}", parse_mode="HTML")
            except Exception:
                pass
        return False


# ── /play ─────────────────────────────────────────────────────────────────────

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎵 <b>Play a Song</b>\n\n"
            "Usage:\n"
            "<code>/play Kesariya</code>\n"
            "<code>/play https://youtube.com/watch?v=...</code>\n\n"
            "📥 Bot searches YouTube, downloads the audio and sends it as a file in the chat.\n\n"
            "<i>💡 Tip: Use /sdownload to save any song as an MP3 to your phone.</i>",
            parse_mode="HTML")
        return

    query   = " ".join(context.args)
    chat_id = update.effective_chat.id
    user    = update.effective_user

    searching = await update.message.reply_text(
        f"🔍 <b>Searching…</b> <code>{query[:60]}</code>", parse_mode="HTML")

    song = await _search_info(query)
    if not song:
        await searching.edit_text("❌ Could not find that song on YouTube. Try a different search.")
        return

    song["requested_by"] = user.first_name

    if VOICE_CHAT_MODE:
        if chat_id in _now_playing:
            _queues[chat_id].append(song)
            pos = len(_queues[chat_id])
            await searching.edit_text(
                f"➕ <b>Added to queue</b> (#{pos})\n<b>{song['title']}</b>\n"
                f"Requested by {user.first_name}", parse_mode="HTML")
            return
        await _vc_play_song(chat_id, song, context, status_msg=searching)
    else:
        # FILE MODE — show a "downloading" card, then send the audio file
        try:
            await searching.edit_text(
                f"📥 <b>Found!</b> Downloading now…\n\n"
                f"🎶 <b>{song['title'][:80]}</b>\n"
                f"👤 {song.get('uploader', 'Unknown')}\n"
                f"⏱ {_fmt_dur(song.get('duration', 0))}\n\n"
                f"<i>Audio will be sent in a moment…</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        _now_playing[chat_id] = song
        await _download_and_send(chat_id, song, context, status_msg=searching)
        _now_playing.pop(chat_id, None)


# ── /pause /resume /skip /stop ────────────────────────────────────────────────

async def _vc_only(update: Update, action: str) -> bool:
    if not VOICE_CHAT_MODE:
        await update.message.reply_text(
            f"ℹ️ <b>{action}</b> is only available in voice-chat mode.\n"
            "To download a song use: <code>/sdownload &lt;name&gt;</code>",
            parse_mode="HTML")
        return False
    return True


async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _vc_only(update, "Pause"):
        return
    chat_id = update.effective_chat.id
    gc = _group_calls.get(chat_id)
    if not gc or chat_id not in _now_playing:
        await update.message.reply_text("Nothing is playing right now.")
        return
    try:
        gc.set_pause(True)
        _paused[chat_id] = True
        await _update_play_card(chat_id, _now_playing[chat_id])
        await update.message.reply_text(
            f"⏸ Paused: <b>{_now_playing[chat_id]['title']}</b>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Could not pause: {e}")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _vc_only(update, "Resume"):
        return
    chat_id = update.effective_chat.id
    gc = _group_calls.get(chat_id)
    if not gc or chat_id not in _now_playing:
        await update.message.reply_text("Nothing is paused right now.")
        return
    try:
        gc.set_pause(False)
        _paused[chat_id] = False
        await _update_play_card(chat_id, _now_playing[chat_id])
        await update.message.reply_text(
            f"▶️ Resumed: <b>{_now_playing[chat_id]['title']}</b>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Could not resume: {e}")


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _vc_only(update, "Skip"):
        return
    chat_id = update.effective_chat.id
    if chat_id not in _now_playing:
        await update.message.reply_text("Nothing is playing right now.")
        return
    skipped = _now_playing.pop(chat_id, None)
    _paused.pop(chat_id, None)
    _play_messages.pop(chat_id, None)
    _stop_progress_job(chat_id, context)

    if not _queues[chat_id]:
        await _leave_vc(chat_id)
        await update.message.reply_text(
            f"⏭ Skipped <b>{skipped['title'] if skipped else 'song'}</b>. Queue is empty.",
            parse_mode="HTML")
        return

    next_song = _queues[chat_id].pop(0)
    await _vc_play_song(chat_id, next_song, context)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _vc_only(update, "Stop"):
        return
    chat_id = update.effective_chat.id
    _queues[chat_id].clear()
    _now_playing.pop(chat_id, None)
    _paused.pop(chat_id, None)
    _play_messages.pop(chat_id, None)
    _stop_progress_job(chat_id, context)
    await _leave_vc(chat_id)
    await update.message.reply_text("⏹ Stopped and left the voice chat.")


async def _leave_vc(chat_id: int) -> None:
    gc = _group_calls.pop(chat_id, None)
    if gc:
        try:
            await gc.stop()
        except Exception:
            pass
    _cleanup_temp(chat_id)


# ── /queue ────────────────────────────────────────────────────────────────────

async def queue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = _now_playing.get(chat_id)
    q   = _queues.get(chat_id, [])

    if not now and not q:
        await update.message.reply_text(
            "🎵 Queue is empty.\nUse <code>/play &lt;song&gt;</code> to add music!",
            parse_mode="HTML")
        return

    lines = ["<b>🎶 Music Queue</b>\n━━━━━━━━━━━━━━━━\n"]
    if now:
        tag = " (paused)" if _paused.get(chat_id) else ""
        lines.append(f"▶️ Now{tag}:\n<b>{now['title']}</b> — {now.get('requested_by','?')}\n")
    if q:
        lines.append("Up next:")
        for i, s in enumerate(q, 1):
            lines.append(f"{i}. {s['title']} — {s.get('requested_by','?')}")
    else:
        lines.append("<i>No more songs queued.</i>")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=_play_card_keyboard(chat_id) if now and VOICE_CHAT_MODE else None,
    )


# ── /nowplaying ───────────────────────────────────────────────────────────────

async def nowplaying(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = _now_playing.get(chat_id)
    if not now:
        await update.message.reply_text(
            "Nothing is playing right now. Use <code>/play</code>!", parse_mode="HTML")
        return
    start   = _play_start_times.get(chat_id)
    elapsed = int((datetime.utcnow() - start).total_seconds()) if start else 0
    await update.message.reply_text(
        _play_card_caption(now, elapsed),
        parse_mode="HTML",
        reply_markup=_play_card_keyboard(chat_id),
    )


# ── Callback buttons ──────────────────────────────────────────────────────────

async def music_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    if len(parts) < 3:
        return
    action  = parts[1]
    chat_id = int(parts[2])

    class _FakeUpdate:
        effective_chat = type("C", (), {"id": chat_id})()
        effective_user = query.from_user
        message        = query.message

    fake = _FakeUpdate()
    if action == "pause":
        await pause(fake, context)
    elif action == "resume":
        await resume(fake, context)
    elif action == "skip":
        await skip(fake, context)
    elif action == "stop":
        await stop(fake, context)
    elif action == "queue":
        q   = _queues.get(chat_id, [])
        now = _now_playing.get(chat_id)
        if not now and not q:
            await query.answer("Queue is empty!", show_alert=True)
        else:
            lines = []
            if now:
                lines.append(f"▶️ {now['title']}")
            for i, s in enumerate(q, 1):
                lines.append(f"{i}. {s['title']}")
            await query.answer("\n".join(lines) or "Empty", show_alert=True)


# ── Startup / shutdown ────────────────────────────────────────────────────────

async def start_tgcalls():
    if VOICE_CHAT_MODE and _pyrogram_client:
        try:
            await _pyrogram_client.start()
            logger.info("Pyrogram client started for voice chat mode.")
        except Exception as e:
            logger.error(f"Could not start pyrogram: {e}")


async def stop_tgcalls():
    if VOICE_CHAT_MODE and _pyrogram_client:
        try:
            await _pyrogram_client.stop()
        except Exception:
            pass
