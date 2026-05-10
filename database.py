"""
MongoDB-backed database layer.
All functions are synchronous wrappers around pymongo calls.
"""
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from config import MONGO_URL, MONGO_DB_NAME

_client = None
_db     = None


def _get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
        _db     = _client[MONGO_DB_NAME]
    return _db


def init_db():
    db = _get_db()
    db.warns.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    db.rankings.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    db.daily_rankings.create_index([("user_id", 1), ("chat_id", 1), ("date", 1)], unique=True)
    db.weekly_rankings.create_index([("user_id", 1), ("chat_id", 1), ("week", 1)], unique=True)
    db.rules.create_index("chat_id", unique=True)
    db.welcome.create_index("chat_id", unique=True)
    db.goodbye.create_index("chat_id", unique=True)
    db.game_scores.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    db.afk.create_index("user_id", unique=True)
    db.seen_members.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    db.known_chats.create_index("chat_id", unique=True)
    db.known_users.create_index("user_id", unique=True)
    db.collection.create_index(
        [("user_id", 1), ("item_type", 1), ("item_name", 1)], unique=True)
    db.rb_coins.create_index("user_id", unique=True)
    db.user_languages.create_index("user_id", unique=True)


# ── Warns ──────────────────────────────────────────────────────────────────────

def add_warn(user_id: int, chat_id: int) -> int:
    db  = _get_db()
    res = db.warns.find_one_and_update(
        {"user_id": user_id, "chat_id": chat_id},
        {"$inc": {"warn_count": 1}},
        upsert=True,
        return_document=True,
    )
    return res["warn_count"] if res else 1


def get_warns(user_id: int, chat_id: int) -> int:
    db  = _get_db()
    doc = db.warns.find_one({"user_id": user_id, "chat_id": chat_id})
    return doc["warn_count"] if doc else 0


def reset_warns(user_id: int, chat_id: int):
    _get_db().warns.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$set": {"warn_count": 0}},
    )


# ── Rankings ───────────────────────────────────────────────────────────────────

def increment_message_count(user_id: int, chat_id: int, username: str, first_name: str):
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    week_str  = now.strftime("%Y-%W")
    db = _get_db()

    db.rankings.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$inc": {"message_count": 1},
         "$set": {"username": username, "first_name": first_name}},
        upsert=True,
    )
    db.daily_rankings.update_one(
        {"user_id": user_id, "chat_id": chat_id, "date": today_str},
        {"$inc": {"count": 1},
         "$set": {"username": username, "first_name": first_name}},
        upsert=True,
    )
    db.weekly_rankings.update_one(
        {"user_id": user_id, "chat_id": chat_id, "week": week_str},
        {"$inc": {"count": 1},
         "$set": {"username": username, "first_name": first_name}},
        upsert=True,
    )


def get_ranking(chat_id: int, limit: int = 10):
    db   = _get_db()
    docs = list(
        db.rankings.find({"chat_id": chat_id})
        .sort("message_count", DESCENDING)
        .limit(limit)
    )
    return docs


def get_ranking_today(chat_id: int, limit: int = 10):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    db = _get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id, "date": today_str}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return list(db.daily_rankings.aggregate(pipeline))


def get_ranking_week(chat_id: int, limit: int = 10):
    week_str = datetime.utcnow().strftime("%Y-%W")
    db = _get_db()
    pipeline = [
        {"$match": {"chat_id": chat_id, "week": week_str}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return list(db.weekly_rankings.aggregate(pipeline))


# ── Admin logs ─────────────────────────────────────────────────────────────────

def log_admin_action(chat_id: int, admin_id: int, admin_name: str,
                     action: str, target_user: str = ""):
    _get_db().admin_logs.insert_one({
        "chat_id":     chat_id,
        "admin_id":    admin_id,
        "admin_name":  admin_name,
        "action":      action,
        "target_user": target_user,
        "timestamp":   datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    })


def get_recent_logs(chat_id: int, limit: int = 10):
    db   = _get_db()
    docs = list(
        db.admin_logs.find({"chat_id": chat_id})
        .sort("_id", DESCENDING)
        .limit(limit)
    )
    return docs


# ── Rules / Welcome / Goodbye ──────────────────────────────────────────────────

def set_rules(chat_id: int, text: str):
    _get_db().rules.update_one(
        {"chat_id": chat_id},
        {"$set": {"rules_text": text}},
        upsert=True,
    )


def get_rules(chat_id: int):
    doc = _get_db().rules.find_one({"chat_id": chat_id})
    return doc["rules_text"] if doc else None


def set_welcome(chat_id: int, text: str):
    _get_db().welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"welcome_text": text}},
        upsert=True,
    )


def get_welcome(chat_id: int):
    doc = _get_db().welcome.find_one({"chat_id": chat_id})
    return doc["welcome_text"] if doc else None


def set_goodbye(chat_id: int, text: str):
    _get_db().goodbye.update_one(
        {"chat_id": chat_id},
        {"$set": {"goodbye_text": text}},
        upsert=True,
    )


def get_goodbye(chat_id: int):
    doc = _get_db().goodbye.find_one({"chat_id": chat_id})
    return doc["goodbye_text"] if doc else None


# ── Game scores ────────────────────────────────────────────────────────────────

def add_trivia_score(user_id: int, chat_id: int, username: str):
    _get_db().game_scores.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$inc": {"trivia_score": 1}, "$set": {"username": username}},
        upsert=True,
    )


def get_top_scores(chat_id: int, limit: int = 10):
    db   = _get_db()
    docs = list(
        db.game_scores.find({"chat_id": chat_id})
        .sort("trivia_score", DESCENDING)
        .limit(limit)
    )
    return docs


# ── AFK ────────────────────────────────────────────────────────────────────────

def set_afk(user_id: int, reason: str):
    _get_db().afk.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason,
                  "since": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}},
        upsert=True,
    )


def get_afk(user_id: int):
    return _get_db().afk.find_one({"user_id": user_id})


def remove_afk(user_id: int):
    _get_db().afk.delete_one({"user_id": user_id})


# ── Reminders ──────────────────────────────────────────────────────────────────

def add_reminder(user_id: int, chat_id: int, message_id: int,
                 text: str, fire_at: datetime):
    res = _get_db().reminders.insert_one({
        "user_id":    user_id,
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       text,
        "fire_at":    fire_at.strftime("%Y-%m-%d %H:%M:%S"),
        "done":       False,
    })
    return str(res.inserted_id)


def get_due_reminders():
    now  = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    docs = list(_get_db().reminders.find({"fire_at": {"$lte": now}, "done": False}))
    return docs


def mark_reminder_done(rid):
    from bson import ObjectId
    _get_db().reminders.update_one(
        {"_id": ObjectId(str(rid))},
        {"$set": {"done": True}},
    )


# ── Seen members ───────────────────────────────────────────────────────────────

def upsert_seen_member(chat_id: int, user_id: int, username: str, first_name: str):
    _get_db().seen_members.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$set": {"username": username, "first_name": first_name}},
        upsert=True,
    )


def get_seen_members(chat_id: int):
    return list(_get_db().seen_members.find({"chat_id": chat_id}))


# ── Broadcast tracking ────────────────────────────────────────────────────────

def track_chat(chat_id: int, chat_type: str, title: str = ""):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    _get_db().known_chats.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_type": chat_type, "title": title, "last_seen": now}},
        upsert=True,
    )


def track_user(user_id: int, username: str, first_name: str):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    _get_db().known_users.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "first_name": first_name, "last_seen": now}},
        upsert=True,
    )


def get_all_chat_ids() -> list:
    docs = _get_db().known_chats.find({}, {"chat_id": 1})
    return [d["chat_id"] for d in docs]


def get_all_user_ids() -> list:
    docs = _get_db().known_users.find({}, {"user_id": 1})
    return [d["user_id"] for d in docs]


# ── Collection ─────────────────────────────────────────────────────────────────

def add_to_collection(user_id: int, item_type: str, item_name: str,
                      rarity: str = "Common", source: str = ""):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    _get_db().collection.update_one(
        {"user_id": user_id, "item_type": item_type, "item_name": item_name},
        {"$inc": {"count": 1},
         "$set": {"collected_at": now, "rarity": rarity, "source": source}},
        upsert=True,
    )


def get_collection(user_id: int) -> list:
    docs = list(
        _get_db().collection.find({"user_id": user_id})
        .sort([("item_type", 1), ("source", 1), ("item_name", 1)])
    )
    result = []
    for d in docs:
        result.append({
            "item_type":    d["item_type"],
            "item_name":    d["item_name"],
            "collected_at": d.get("collected_at", ""),
            "count":        d.get("count", 1),
            "rarity":       d.get("rarity", "Common"),
            "source":       d.get("source", ""),
        })
    return result


def get_collection_count_by_source(user_id: int, source: str) -> int:
    """Count user's characters from a specific anime/source."""
    return _get_db().collection.count_documents(
        {"user_id": user_id, "item_type": "anime", "source": source}
    )


# ── RB Coins ───────────────────────────────────────────────────────────────────

def add_rb_coins(user_id: int, amount: int) -> int:
    """Add RB coins to a user and return the new total."""
    res = _get_db().rb_coins.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True,
        return_document=True,
    )
    return res["coins"] if res else amount


def get_rb_coins(user_id: int) -> int:
    doc = _get_db().rb_coins.find_one({"user_id": user_id})
    return doc["coins"] if doc else 0


def get_rb_leaderboard(limit: int = 10) -> list:
    docs = list(
        _get_db().rb_coins.find()
        .sort("coins", DESCENDING)
        .limit(limit)
    )
    return docs


# ── User Language ─────────────────────────────────────────────────────────────

def set_user_language(user_id: int, lang: str):
    _get_db().user_languages.update_one(
        {"user_id": user_id},
        {"$set": {"lang": lang}},
        upsert=True,
    )


def get_user_language(user_id: int) -> str:
    doc = _get_db().user_languages.find_one({"user_id": user_id})
    return doc["lang"] if doc else "en"
