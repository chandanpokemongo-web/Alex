"""
handlers/news.py — 20 news commands.
Uses GNews free API (optional NEWS_API_KEY) + curated static news context.
Set NEWS_API_KEY in environment for live news. Without it, shows category links.
"""

import os
import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes

_NEWS_KEY = os.environ.get("NEWS_API_KEY", "")
_GNEWS    = "https://gnews.io/api/v4"
_NEWSAPI  = "https://newsapi.org/v2"

# ── Helper ─────────────────────────────────────────────────────────────────────

async def _gnews(topic: str, lang: str = "en", max_results: int = 5) -> list:
    if not _NEWS_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{_GNEWS}/top-headlines",
                params={"topic": topic, "lang": lang, "max": max_results, "token": _NEWS_KEY}
            )
            if r.status_code == 200:
                return r.json().get("articles", [])
    except Exception:
        pass
    return []


async def _gnews_search(query: str, max_results: int = 5) -> list:
    if not _NEWS_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{_GNEWS}/search",
                params={"q": query, "lang": "en", "max": max_results, "token": _NEWS_KEY}
            )
            if r.status_code == 200:
                return r.json().get("articles", [])
    except Exception:
        pass
    return []


def _format_articles(articles: list, title: str) -> str:
    if not articles:
        return ""
    lines = [f"📰 <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for a in articles[:5]:
        t   = a.get("title", "No title")
        src = a.get("source", {}).get("name", "")
        url = a.get("url", "")
        lines.append(f"• <a href='{url}'>{t}</a> — <i>{src}</i>")
    return "\n".join(lines)


def _no_key_msg(category: str, links: list[tuple]) -> str:
    lines = [f"📰 <b>{category}</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    lines.append("💡 Set <code>NEWS_API_KEY</code> (GNews free tier) for live headlines.\n")
    lines.append("Browse live news:")
    for label, url in links:
        lines.append(f"🔗 <a href='{url}'>{label}</a>")
    return "\n".join(lines)


# ── Commands ──────────────────────────────────────────────────────────────────

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("breaking-news")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Top Headlines"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Top Headlines", [
                ("Google News", "https://news.google.com/"),
                ("BBC News", "https://www.bbc.com/news"),
                ("Reuters", "https://www.reuters.com/"),
                ("AP News", "https://apnews.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def technews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("technology")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Tech News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Tech News", [
                ("TechCrunch", "https://techcrunch.com/"),
                ("The Verge", "https://www.theverge.com/"),
                ("Ars Technica", "https://arstechnica.com/"),
                ("Wired", "https://www.wired.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def sportnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("sports")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Sports News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Sports News", [
                ("ESPN", "https://www.espn.com/"),
                ("Sky Sports", "https://www.skysports.com/"),
                ("BBC Sport", "https://www.bbc.com/sport"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def entertainmentnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("entertainment")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Entertainment News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Entertainment News", [
                ("Variety", "https://variety.com/"),
                ("Hollywood Reporter", "https://www.hollywoodreporter.com/"),
                ("Entertainment Weekly", "https://ew.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def sciencenews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("science")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Science News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Science News", [
                ("Science Daily", "https://www.sciencedaily.com/"),
                ("New Scientist", "https://www.newscientist.com/"),
                ("NASA News", "https://www.nasa.gov/news/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def healthnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("health")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Health News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Health News", [
                ("WebMD", "https://www.webmd.com/news/"),
                ("WHO News", "https://www.who.int/news/"),
                ("Healthline", "https://www.healthline.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def businessnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("business")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Business News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Business News", [
                ("Bloomberg", "https://www.bloomberg.com/"),
                ("Financial Times", "https://www.ft.com/"),
                ("Forbes", "https://www.forbes.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def cryptonews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("cryptocurrency bitcoin ethereum")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Crypto News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Crypto News", [
                ("CoinDesk", "https://www.coindesk.com/"),
                ("CoinTelegraph", "https://cointelegraph.com/"),
                ("CryptoSlate", "https://cryptoslate.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def gamernews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("video games gaming")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Gaming News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Gaming News", [
                ("IGN", "https://www.ign.com/"),
                ("GameSpot", "https://www.gamespot.com/"),
                ("Kotaku", "https://kotaku.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def movienews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("movies cinema box office")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Movie News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Movie News", [
                ("Screen Rant", "https://screenrant.com/"),
                ("Variety Films", "https://variety.com/v/film/"),
                ("IMDb News", "https://www.imdb.com/news/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def animenews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("anime manga new release")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Anime News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Anime News", [
                ("Anime News Network", "https://www.animenewsnetwork.com/"),
                ("MyAnimeList News", "https://myanimelist.net/news"),
                ("Crunchyroll News", "https://www.crunchyroll.com/news"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def kpopnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("kpop korean pop music")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "K-Pop News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("K-Pop News", [
                ("Soompi", "https://www.soompi.com/"),
                ("Allkpop", "https://www.allkpop.com/"),
                ("Koreaboo", "https://www.koreaboo.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def worldnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("world")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "World News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("World News", [
                ("BBC World", "https://www.bbc.com/news/world"),
                ("Al Jazeera", "https://www.aljazeera.com/"),
                ("Reuters World", "https://www.reuters.com/world/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def breakingnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("breaking-news")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Breaking News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Breaking News", [
                ("BBC Breaking", "https://www.bbc.com/news"),
                ("CNN Breaking", "https://edition.cnn.com/"),
                ("Sky News", "https://news.sky.com/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def indianews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("India latest news")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "India News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("India News", [
                ("NDTV", "https://www.ndtv.com/"),
                ("The Hindu", "https://www.thehindu.com/"),
                ("Times of India", "https://timesofindia.indiatimes.com/"),
                ("India Today", "https://www.indiatoday.in/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def spacenews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("space NASA SpaceX astronomy")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Space & Science News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        facts = [
            "NASA's James Webb Space Telescope has discovered galaxies dating back 13.6 billion years.",
            "SpaceX Starship is the largest rocket ever built — taller than the Statue of Liberty.",
            "India's Chandrayaan-3 became the first mission to land near the lunar south pole in 2023.",
            "The Parker Solar Probe has become the fastest human-made object — 430,000+ mph.",
            "NASA's Artemis program aims to return humans to the Moon by 2026.",
        ]
        await update.message.reply_text(
            f"🚀 <b>Space News / Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML"
        )


async def politicsnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews("politics")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Politics News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Politics News", [
                ("Reuters Politics", "https://www.reuters.com/news/politics/"),
                ("Politico", "https://www.politico.com/"),
                ("The Guardian Politics", "https://www.theguardian.com/politics"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def environmentnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("climate change environment")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Environment News"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            _no_key_msg("Environment News", [
                ("Guardian Environment", "https://www.theguardian.com/environment"),
                ("Carbon Brief", "https://www.carbonbrief.org/"),
                ("Inside Climate News", "https://insideclimatenews.org/"),
            ]),
            parse_mode="HTML", disable_web_page_preview=True
        )


async def foodnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await _gnews_search("food culinary restaurant")
    if articles:
        await update.message.reply_text(
            _format_articles(articles, "Food & Lifestyle"),
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        facts = [
            "In 2023, Penicillin cocktail (whisky, honey, lemon) was named the cocktail of the decade.",
            "A single strand of saffron is worth more than gold by weight.",
            "The world's most expensive coffee is Kopi Luwak — made from civet-digested coffee beans.",
            "Italy has more UNESCO-protected food traditions than any other country.",
            "The world's oldest restaurant still operating is Sobrino de Botín in Madrid, open since 1725.",
        ]
        await update.message.reply_text(f"🍽️ <b>Food Fact</b>\n\n{random.choice(facts)}", parse_mode="HTML")
