"""
handlers/voice.py — 15 voice-chat and TTS commands.
VC commands wrap existing music.py functionality.
TTS sends speech as audio using Google TTS (no key needed).
"""

import asyncio
import os
import tempfile
import logging
import httpx
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from handlers import music

logger = logging.getLogger(__name__)

# ── TTS helper using gTTS-compatible free endpoint ────────────────────────────

async def _gtts_bytes(text: str, lang: str = "en") -> BytesIO | None:
    """
    Attempt to generate TTS audio via Google Translate TTS endpoint.
    Returns audio bytes or None if unavailable.
    """
    try:
        url = (
            "https://translate.google.com/translate_tts"
            f"?ie=UTF-8&tl={lang}&q={text[:200]}&client=tw-ob"
        )
        async with httpx.AsyncClient(
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        ) as c:
            r = await c.get(url)
            if r.status_code == 200 and r.content:
                buf = BytesIO(r.content)
                buf.name = "tts.mp3"
                return buf
    except Exception as e:
        logger.warning(f"TTS request failed: {e}")
    return None


# ── /tts ──────────────────────────────────────────────────────────────────────

async def tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert text to speech and send as voice message."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /tts [lang] <text>\n\n"
            "Examples:\n"
            "/tts Hello world\n"
            "/tts hi नमस्ते दुनिया\n"
            "/tts ja こんにちは\n"
            "/tts ko 안녕하세요\n"
            "/tts ar مرحبا بالعالم\n\n"
            "Supported lang codes: en, hi, ja, ko, ar, fr, de, es, zh, ru, tr, pt"
        )
        return

    args = list(context.args)
    lang = "en"
    lang_codes = {"en", "hi", "ja", "ko", "ar", "fr", "de", "es", "zh", "ru", "tr", "pt",
                  "it", "nl", "pl", "sv", "da", "fi", "nb", "th", "vi", "id", "ms"}

    if args and args[0].lower() in lang_codes:
        lang = args.pop(0).lower()

    if not args:
        await update.message.reply_text("Please provide text after the language code.")
        return

    text = " ".join(args)
    msg  = await update.message.reply_text(f"🔊 Generating speech for: <i>{text[:80]}</i>...", parse_mode="HTML")

    audio = await _gtts_bytes(text, lang)
    if audio:
        try:
            await msg.delete()
            await update.message.reply_voice(
                voice=audio,
                caption=f"🔊 <b>TTS ({lang.upper()})</b>\n<i>{text[:100]}</i>",
                parse_mode="HTML",
            )
            return
        except Exception:
            pass

    # Fallback: try sending as audio
    if audio:
        try:
            audio.seek(0)
            await msg.edit_text("Sending as audio file...")
            await update.message.reply_audio(
                audio=audio,
                title=f"TTS: {text[:30]}",
                caption=f"🔊 {text[:100]}",
            )
            return
        except Exception:
            pass

    await msg.edit_text(
        "⚠️ TTS service temporarily unavailable.\n\n"
        "💡 For reliable TTS: install <code>gTTS</code> on the server\n"
        "   <code>pip install gtts</code>",
        parse_mode="HTML"
    )


# ── Voice chat commands (wrap music.py) ───────────────────────────────────────

async def vcjoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ <b>Voice Chat</b>\n\nTo join VC and play music, use:\n"
        "/vcplay <song name or URL>\n\n"
        "The bot will join voice chat automatically when you start playing.",
        parse_mode="HTML"
    )


async def vcleave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.stop(update, context)


async def vcplay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.play(update, context)


async def vcpause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.pause(update, context)


async def vcresume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.resume(update, context)


async def vcstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.stop(update, context)


async def vcskip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.skip(update, context)


async def vcqueue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.queue_cmd(update, context)


async def vcnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.nowplaying(update, context)


async def vcvolume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔊 <b>Volume Control</b>\n\n"
        "Voice chat volume control requires a live Pyrogram+PyTgCalls setup.\n"
        "This bot runs in file-send mode by default.\n\n"
        "Use /vcplay to download and send songs as audio files instead.",
        parse_mode="HTML"
    )


async def vcmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 Bot muted in voice chat.\n(Requires live VC mode — use /vcplay for file mode.)"
    )


async def vcunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔊 Bot unmuted.\n(Requires live VC mode — use /vcplay for file mode.)"
    )


async def vcstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ <b>Voice Chat Status</b>\n\n"
        "Mode: <b>File Send Mode</b>\n"
        "🎵 Songs are downloaded and sent as audio files\n"
        "📥 Use /play or /vcplay to request a song\n"
        "📋 Use /vcqueue to see the queue\n"
        "⏭️ Use /vcskip to skip a track",
        parse_mode="HTML"
    )


async def vctrack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await music.nowplaying(update, context)
