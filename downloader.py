"""
/download — download video from any platform (YouTube, Instagram, TikTok, Twitter, etc.)
/sdownload — download audio/song as MP3
"""

import os
import asyncio
import tempfile
from pathlib import Path

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ── Pending download state (user_id -> {url, chat_id}) ───────────────────────
_pending: dict = {}

QUALITY_OPTIONS = [
    ("🎯 Best Available", "best"),
    ("🔵 4K  (2160p)",    "2160"),
    ("🟣 1080p",          "1080"),
    ("🟢 720p",           "720"),
    ("🟡 480p",           "480"),
    ("🔴 360p",           "360"),
]


def _quality_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = []
    for label, q in QUALITY_OPTIONS:
        rows.append([InlineKeyboardButton(label, callback_data=f"dlq_{q}_{user_id}")])
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"dlq_cancel_{user_id}")])
    return InlineKeyboardMarkup(rows)


def _sizeof(path: str) -> int:
    return os.path.getsize(path)


def _mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


# ── /download ─────────────────────────────────────────────────────────────────

async def download_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📥 <b>Video Downloader</b>\n\n"
            "Usage:\n"
            "<code>/download https://youtube.com/watch?v=...</code>\n\n"
            "✅ Supports: YouTube, Instagram, Twitter/X, TikTok, Facebook, "
            "Dailymotion, Vimeo and 1000+ other sites.\n\n"
            "⚠️ Max file size Telegram allows is <b>50 MB</b>. "
            "Use 360p/480p for longer videos.",
            parse_mode="HTML",
        )
        return

    url = context.args[0].strip()
    user_id = update.effective_user.id
    _pending[user_id] = {"url": url, "chat_id": update.effective_chat.id}

    display_url = url[:55] + "…" if len(url) > 55 else url
    await update.message.reply_text(
        f"📥 <b>Select Video Quality</b>\n\n"
        f"🔗 <code>{display_url}</code>\n\n"
        f"⚠️ <i>Files over 50 MB cannot be sent via Telegram.\n"
        f"For long videos use 360p or 480p.</i>",
        parse_mode="HTML",
        reply_markup=_quality_keyboard(user_id),
    )


async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_", 2)   # dlq_<quality>_<user_id>
    if len(parts) < 3:
        return

    _, quality, uid_str = parts
    try:
        user_id = int(uid_str)
    except ValueError:
        return

    if query.from_user.id != user_id:
        await query.answer("❌ This is not your download!", show_alert=True)
        return

    if quality == "cancel":
        _pending.pop(user_id, None)
        await query.edit_message_text("❌ Download cancelled.")
        return

    pending = _pending.pop(user_id, None)
    if not pending:
        await query.edit_message_text(
            "❌ Session expired. Please use /download again.")
        return

    url     = pending["url"]
    chat_id = pending["chat_id"]

    # Build yt-dlp format string
    if quality == "best":
        fmt   = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        label = "Best Available"
    elif quality == "2160":
        fmt   = "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]"
        label = "4K (2160p)"
    else:
        h     = int(quality)
        fmt   = (f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                 f"/bestvideo[height<={h}]+bestaudio/best[height<={h}]")
        label = f"{h}p"

    await query.edit_message_text(
        f"⬇️ <b>Downloading…</b>\n\n"
        f"📊 Quality: <b>{label}</b>\n"
        f"<i>Please wait, this may take a moment for large videos.</i>",
        parse_mode="HTML",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = os.path.join(tmpdir, "video.%(ext)s")
        ydl_opts = {
            "format": fmt,
            "outtmpl": outpath,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        loop = asyncio.get_event_loop()
        info = None

        def _do_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            info = await loop.run_in_executor(None, _do_download)
        except Exception as e:
            err = str(e)[:300]
            await context.bot.send_message(
                chat_id,
                f"❌ <b>Download failed</b>\n\n<code>{err}</code>\n\n"
                "<i>Try a lower quality or check the URL.</i>",
                parse_mode="HTML",
            )
            try:
                await query.delete_message()
            except Exception:
                pass
            return

        files = list(Path(tmpdir).glob("video.*"))
        if not files:
            await context.bot.send_message(
                chat_id, "❌ Download finished but no file was created. Try again.")
            return

        filepath = str(files[0])
        size     = _sizeof(filepath)

        if size > 50 * 1024 * 1024:
            await context.bot.send_message(
                chat_id,
                f"❌ <b>File too large</b> ({_mb(size)})\n\n"
                "Telegram's bot limit is 50 MB.\n"
                "Please try a lower quality like 480p or 360p.",
                parse_mode="HTML",
            )
            try:
                await query.delete_message()
            except Exception:
                pass
            return

        title    = (info.get("title",    "video")    if info else "video")
        duration = (info.get("duration", None)       if info else None)

        await query.edit_message_text(
            f"📤 <b>Uploading…</b> ({_mb(size)})", parse_mode="HTML")

        with open(filepath, "rb") as fh:
            await context.bot.send_video(
                chat_id,
                video=fh,
                caption=(
                    f"🎬 <b>{title[:200]}</b>\n"
                    f"📊 {label} | 📦 {_mb(size)}"
                ),
                parse_mode="HTML",
                duration=duration,
                supports_streaming=True,
            )

        try:
            await query.delete_message()
        except Exception:
            pass


# ── /sdownload ────────────────────────────────────────────────────────────────

async def sdownload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎵 <b>Song Downloader</b>\n\n"
            "Usage:\n"
            "<code>/sdownload https://youtube.com/watch?v=...</code>\n"
            "<code>/sdownload Shape of You Ed Sheeran</code>\n"
            "<code>/sdownload Kesariya Bollywood</code>\n\n"
            "Downloads audio as MP3 and sends it here.",
            parse_mode="HTML",
        )
        return

    query_str = " ".join(context.args).strip()
    is_url    = query_str.startswith("http://") or query_str.startswith("https://")
    search    = query_str if is_url else f"ytsearch1:{query_str}"

    msg = await update.message.reply_text(
        f"🔍 <b>Searching…</b>\n<code>{query_str[:60]}</code>",
        parse_mode="HTML",
    )

    chat_id = update.effective_chat.id

    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outpath,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        loop = asyncio.get_event_loop()
        info = None

        def _do_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search, download=True)
                if result and "entries" in result:
                    result = result["entries"][0]
                return result

        try:
            await msg.edit_text("⬇️ <b>Downloading song…</b>", parse_mode="HTML")
            info = await loop.run_in_executor(None, _do_download)
        except Exception as e:
            await msg.edit_text(
                f"❌ <b>Failed to download</b>\n\n<code>{str(e)[:200]}</code>",
                parse_mode="HTML",
            )
            return

        mp3_files = list(Path(tmpdir).glob("*.mp3"))
        if not mp3_files:
            all_files = list(Path(tmpdir).glob("*"))
            mp3_files = all_files

        if not mp3_files:
            await msg.edit_text("❌ Could not find the downloaded audio file.")
            return

        filepath = str(mp3_files[0])
        size     = _sizeof(filepath)

        if size > 50 * 1024 * 1024:
            await msg.edit_text(
                f"❌ <b>Audio file too large</b> ({_mb(size)})\n"
                "Telegram's limit is 50 MB. Try a shorter track.",
                parse_mode="HTML",
            )
            return

        title    = (info.get("title",    "song")    if info else "song")
        artist   = (info.get("uploader", "Unknown") if info else "Unknown")
        duration = (info.get("duration", None)      if info else None)
        thumb    = (info.get("thumbnail", None)     if info else None)

        await msg.edit_text("📤 <b>Uploading…</b>", parse_mode="HTML")

        with open(filepath, "rb") as fh:
            await context.bot.send_audio(
                chat_id,
                audio=fh,
                caption=f"🎵 <b>{title[:200]}</b>\n👤 {artist}",
                parse_mode="HTML",
                duration=duration,
                title=title[:64],
                performer=artist[:64],
            )

        try:
            await msg.delete()
        except Exception:
            pass
