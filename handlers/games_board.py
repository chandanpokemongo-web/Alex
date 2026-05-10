"""
Board games:
  /snake  — Snake & Ladders PvP  (2 players, real PIL board image)
  /ludo   — Ludo 2–4 players     (4 tokens each, all 4 must reach home to win)

BUGS FIXED:
  - snl_callback / ludo_callback: removed premature query.answer() at top level;
    each branch now answers the query exactly once.
  - Ludo: "no movable tokens" branch now shows the PREVIOUS player's name in the
    event text before advancing the turn.
  - Ludo: pending_move is properly cleared on turn change for no-movable case.
"""
import random
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from handlers.board_image import (
    draw_snl_board, draw_ludo_board,
    SNL_SNAKES, SNL_LADDERS,
    LUDO_PATH, LUDO_ENTRY_IDX, LUDO_HS, LUDO_SAFE_IDX,
)

# ─────────────────────────────────────────────────────────────────────────────
#  SNAKE & LADDERS
# ─────────────────────────────────────────────────────────────────────────────

active_snl: dict = {}


def _snl_roll_kb(chat_id: int, player_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎲 Roll Dice",
                             callback_data=f"snl_roll_{chat_id}_{player_id}")
    ]])


async def _snl_send_board(context, chat_id: int, game: dict,
                          caption: str, next_id: int):
    """Send or edit the board photo with updated state."""
    pos  = game["positions"]
    p0   = game["players"][0]
    p1   = game["players"][1]
    n0   = game["names"][p0]
    n1   = game["names"][p1]
    kb   = _snl_roll_kb(chat_id, next_id)
    mid  = game.get("board_msg_id")

    if mid:
        try:
            img2 = draw_snl_board(pos[p0], pos[p1], n0, n1)
            await context.bot.edit_message_media(
                chat_id=chat_id, message_id=mid,
                media=InputMediaPhoto(media=img2, caption=caption, parse_mode="HTML"),
                reply_markup=kb,
            )
            return
        except Exception:
            pass

    img = draw_snl_board(pos[p0], pos[p1], n0, n1)
    msg = await context.bot.send_photo(
        chat_id, photo=img, caption=caption,
        parse_mode="HTML", reply_markup=kb,
    )
    game["board_msg_id"] = msg.message_id


async def snake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user    = update.effective_user

    if update.effective_chat.type == "private":
        await update.message.reply_text("🎲 Use /snake @username in a group!")
        return
    if chat_id in active_snl:
        await update.message.reply_text("A Snake & Ladders game is already running!")
        return

    target = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        t = update.message.reply_to_message.from_user
        if not t.is_bot and t.id != user.id:
            target = t
    if not target and context.args:
        try:
            member = await context.bot.get_chat_member(chat_id, context.args[0].lstrip("@"))
            if not member.user.is_bot and member.user.id != user.id:
                target = member.user
        except Exception:
            pass
    if not target:
        await update.message.reply_text(
            "Usage: /snake @username  or reply to someone's message.")
        return

    active_snl[chat_id] = {
        "players":      [user.id, target.id],
        "names":        {user.id: user.first_name, target.id: target.first_name},
        "positions":    {user.id: 0, target.id: 0},
        "turn":         0,
        "board_msg_id": None,
    }
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept",
                             callback_data=f"snl_accept_{chat_id}_{target.id}"),
        InlineKeyboardButton("❌ Decline",
                             callback_data=f"snl_decline_{chat_id}_{target.id}"),
    ]])
    await update.message.reply_text(
        f"🎲 <b>Snake &amp; Ladders Challenge!</b>\n\n"
        f"🔴 {user.first_name}  vs  🔵 {target.first_name}\n\n"
        f"{target.first_name}, do you accept?",
        parse_mode="HTML", reply_markup=kb,
    )


async def snl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    parts  = query.data.split("_")
    action = parts[1]

    if action == "accept":
        chat_id   = int(parts[2])
        target_id = int(parts[3])
        if query.from_user.id != target_id:
            await query.answer("Only the challenged player can accept!", show_alert=True)
            return
        if chat_id not in active_snl:
            await query.answer()
            await query.edit_message_text("This game no longer exists.")
            return
        await query.answer("✅ Challenge accepted!")
        game  = active_snl[chat_id]
        first = game["players"][0]
        name0 = game["names"][game["players"][0]]
        await query.edit_message_text("✅ Challenge accepted! Board incoming…")
        await _snl_send_board(
            context, chat_id, game,
            caption=(f"🎲 <b>Snake &amp; Ladders</b>\n"
                     f"🔴 {game['names'][game['players'][0]]}: sq.0  "
                     f"🔵 {game['names'][game['players'][1]]}: sq.0\n\n"
                     f"<b>{name0}</b>'s turn! Roll the dice ▼"),
            next_id=first,
        )

    elif action == "decline":
        chat_id   = int(parts[2])
        target_id = int(parts[3])
        if query.from_user.id != target_id:
            await query.answer("Only the challenged player can decline!", show_alert=True)
            return
        await query.answer("❌ Declined.")
        active_snl.pop(chat_id, None)
        await query.edit_message_text("❌ Challenge declined.")

    elif action == "roll":
        chat_id   = int(parts[2])
        player_id = int(parts[3])
        if chat_id not in active_snl:
            await query.answer("Game no longer exists!", show_alert=True)
            return
        game    = active_snl[chat_id]
        p_ids   = game["players"]
        names   = game["names"]
        pos     = game["positions"]
        turn_i  = game["turn"]

        if query.from_user.id != p_ids[turn_i]:
            await query.answer("It's not your turn!", show_alert=True)
            return

        await query.answer()

        roll    = random.randint(1, 6)
        cur_id  = p_ids[turn_i]
        new_pos = pos[cur_id] + roll
        event   = f"🎲 {names[cur_id]} rolled <b>{roll}</b>"

        if new_pos > 100:
            new_pos = 100 - (new_pos - 100)
            event  += f"\n↩️ Bounced back to {new_pos}!"
        elif new_pos in SNL_SNAKES:
            tail    = SNL_SNAKES[new_pos]
            event  += f"\n🐍 Snake! {new_pos} → {tail}"
            new_pos = tail
        elif new_pos in SNL_LADDERS:
            top     = SNL_LADDERS[new_pos]
            event  += f"\n🪜 Ladder! {new_pos} → {top}"
            new_pos = top

        pos[cur_id] = new_pos

        if new_pos == 100:
            del active_snl[chat_id]
            img = draw_snl_board(
                pos[p_ids[0]], pos[p_ids[1]],
                names[p_ids[0]], names[p_ids[1]],
            )
            mid = game.get("board_msg_id")
            win_cap = event + f"\n\n🏆 <b>{names[cur_id]} wins Snake &amp; Ladders!</b> 🎉"
            if mid:
                try:
                    await context.bot.edit_message_media(
                        chat_id=chat_id, message_id=mid,
                        media=InputMediaPhoto(media=img, caption=win_cap, parse_mode="HTML"),
                    )
                    return
                except Exception:
                    pass
            await context.bot.send_photo(chat_id, photo=img, caption=win_cap, parse_mode="HTML")
            return

        game["turn"] = (turn_i + 1) % 2
        next_id      = p_ids[game["turn"]]
        next_name    = names[next_id]
        caption = (
            f"{event}\n\n"
            f"🔴 {names[p_ids[0]]}: sq.{pos[p_ids[0]]}  "
            f"🔵 {names[p_ids[1]]}: sq.{pos[p_ids[1]]}\n\n"
            f"<b>{next_name}</b>'s turn!"
        )
        await _snl_send_board(context, chat_id, game, caption, next_id)

    else:
        await query.answer()


# ─────────────────────────────────────────────────────────────────────────────
#  LUDO  (2–4 players, 4 tokens each, all 4 must reach home to win)
# ─────────────────────────────────────────────────────────────────────────────

LUDO_EMOJIS    = ["🔴", "🔵", "🟢", "🟡"]
LUDO_COLORNAME = ["Red", "Blue", "Green", "Yellow"]
LUDO_HOME      = 58   # pos >= 58 → token is home
LUDO_TOKENS    = 4    # tokens per player

active_ludo: dict = {}


def _ludo_abs_idx(rel_pos: int, ci: int) -> int:
    """Relative position 1-52 → absolute LUDO_PATH index (0-51)."""
    return (LUDO_ENTRY_IDX[ci] + rel_pos - 1) % 52


def _ludo_physical(rel_pos: int, ci: int):
    """Returns (row, col) of a token on shared path, or None."""
    if rel_pos <= 0 or rel_pos > 52:
        return None
    return LUDO_PATH[_ludo_abs_idx(rel_pos, ci)]


def _ludo_setup_text(game: dict) -> str:
    lines = []
    for i, pid in enumerate(game["players"]):
        lines.append(f"{LUDO_EMOJIS[i]} {LUDO_COLORNAME[i]}: {game['names'][pid]}")
    for i in range(len(game["players"]), 4):
        lines.append(f"{LUDO_EMOJIS[i]} {LUDO_COLORNAME[i]}: waiting…")
    return "\n".join(lines)


def _ludo_board_text(game: dict) -> str:
    lines = []
    for idx, pid in enumerate(game["players"]):
        t  = game["tokens"][pid]
        ci = game["colors"][idx]
        def lbl(p):
            if p == 0:           return "🏠"
            if p >= LUDO_HOME:   return "🏁"
            if p >= 53:          return f"HS{p-52}"
            return f"p{p}"
        tstr = "  ".join(f"T{i+1}:{lbl(t[i])}" for i in range(LUDO_TOKENS))
        lines.append(f"{LUDO_EMOJIS[ci]} {game['names'][pid]}: {tstr}")
    return "\n".join(lines)


def _ludo_status(game: dict, extra: str = "") -> str:
    turn_pid = game["players"][game["turn"]]
    ci       = game["colors"][game["turn"]]
    board    = _ludo_board_text(game)
    ev       = f"\n{extra}" if extra else ""
    return (
        f"🎮 <b>Ludo</b>\n━━━━━━━━━━━━━━━━\n"
        f"{board}{ev}\n\n"
        f"Turn: {LUDO_EMOJIS[ci]} <b>{game['names'][turn_pid]}</b>"
    ).strip()


def _ludo_roll_kb(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎲 Roll Dice", callback_data=f"ludo_roll_{chat_id}")
    ]])


def _ludo_token_kb(chat_id: int, pid: int, opts: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"Token {i+1}",
                             callback_data=f"ludo_tok_{chat_id}_{pid}_{i}")
        for i in opts
    ]])


def _ludo_setup_kb(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🙋 Join Game",  callback_data=f"ludo_join_{chat_id}")],
        [InlineKeyboardButton("▶️ Start Game", callback_data=f"ludo_start_{chat_id}")],
    ])


async def _ludo_send_board(context, chat_id: int, game: dict,
                            caption: str, roll_kb: InlineKeyboardMarkup | None = None):
    """Send or edit the Ludo board photo."""
    img = draw_ludo_board(game)
    kb  = roll_kb or _ludo_roll_kb(chat_id)
    mid = game.get("board_msg_id")

    if mid:
        try:
            img2 = draw_ludo_board(game)
            await context.bot.edit_message_media(
                chat_id=chat_id, message_id=mid,
                media=InputMediaPhoto(media=img2, caption=caption, parse_mode="HTML"),
                reply_markup=kb,
            )
            return
        except Exception:
            pass

    msg = await context.bot.send_photo(
        chat_id, photo=img, caption=caption,
        parse_mode="HTML", reply_markup=kb,
    )
    game["board_msg_id"] = msg.message_id


async def ludo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user    = update.effective_user

    if update.effective_chat.type == "private":
        await update.message.reply_text("🎮 Use /ludo in a group to play with others!")
        return
    if chat_id in active_ludo:
        g = active_ludo[chat_id]
        msg = "A Ludo lobby is open — press Join!" if not g.get("started") \
              else "A Ludo game is already in progress!"
        await update.message.reply_text(msg)
        return

    game = {
        "players":      [user.id],
        "names":        {user.id: user.first_name},
        "colors":       {0: 0},
        "tokens":       {user.id: [0] * LUDO_TOKENS},
        "turn":         0,
        "started":      False,
        "pending_move": None,
        "board_msg_id": None,
    }
    active_ludo[chat_id] = game

    await update.message.reply_text(
        f"🎮 <b>Ludo</b> (4 tokens each — get all 4 home to win!)\n\n"
        f"{_ludo_setup_text(game)}\n\n"
        f"2–4 players. Press <b>Join</b> then <b>Start</b>!",
        parse_mode="HTML",
        reply_markup=_ludo_setup_kb(chat_id),
    )


async def ludo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    parts  = query.data.split("_")
    action = parts[1]

    # ── join ──────────────────────────────────────────────────────────────────
    if action == "join":
        chat_id = int(parts[2])
        user    = query.from_user
        if chat_id not in active_ludo:
            await query.answer("Game not found!", show_alert=True)
            return
        game = active_ludo[chat_id]
        if game.get("started"):
            await query.answer("Game already started!", show_alert=True)
            return
        if user.id in game["players"]:
            await query.answer("You already joined!", show_alert=True)
            return
        if len(game["players"]) >= 4:
            await query.answer("Game is full (max 4)!", show_alert=True)
            return
        await query.answer("✅ Joined!")
        idx = len(game["players"])
        game["players"].append(user.id)
        game["names"][user.id]  = user.first_name
        game["colors"][idx]     = idx
        game["tokens"][user.id] = [0] * LUDO_TOKENS
        await query.edit_message_text(
            f"🎮 <b>Ludo</b> (4 tokens — all home = WIN)\n\n"
            f"{_ludo_setup_text(game)}\n\n"
            f"Press <b>Start</b> when ready (min 2)!",
            parse_mode="HTML",
            reply_markup=_ludo_setup_kb(chat_id),
        )

    # ── start ─────────────────────────────────────────────────────────────────
    elif action == "start":
        chat_id = int(parts[2])
        if chat_id not in active_ludo:
            await query.answer("Game not found!", show_alert=True)
            return
        game = active_ludo[chat_id]
        if query.from_user.id != game["players"][0]:
            await query.answer("Only the host can start!", show_alert=True)
            return
        if len(game["players"]) < 2:
            await query.answer("Need at least 2 players!", show_alert=True)
            return
        await query.answer("🎮 Starting!")
        game["started"] = True
        await query.edit_message_text("🎮 Ludo started! Board incoming…")
        await _ludo_send_board(
            context, chat_id, game,
            caption=_ludo_status(game, "🎲 Game on! Roll the dice to begin."),
        )

    # ── roll ──────────────────────────────────────────────────────────────────
    elif action == "roll":
        chat_id = int(parts[2])
        if chat_id not in active_ludo:
            await query.answer("Game not found!", show_alert=True)
            return
        game    = active_ludo[chat_id]
        players = game["players"]
        turn_i  = game["turn"]
        cur_pid = players[turn_i]

        if query.from_user.id != cur_pid:
            await query.answer("It's not your turn!", show_alert=True)
            return

        await query.answer()

        roll   = random.randint(1, 6)
        tokens = game["tokens"][cur_pid]
        ci     = game["colors"][turn_i]
        cur_name = game["names"][cur_pid]

        movable = []
        for ti, pos in enumerate(tokens):
            if pos >= LUDO_HOME:
                continue
            if pos == 0 and roll == 6:
                movable.append(ti)
            elif pos > 0 and pos + roll <= LUDO_HOME:
                movable.append(ti)

        if not movable:
            # No valid move — advance turn AFTER building the message
            event_txt = (
                f"🎲 {cur_name} rolled <b>{roll}</b> — no valid move!"
            )
            game["turn"] = (turn_i + 1) % len(players)
            game["pending_move"] = None
            await _ludo_send_board(
                context, chat_id, game,
                caption=_ludo_status(game, event_txt),
            )
            return

        if len(movable) == 1:
            await _ludo_apply_move(
                query, context, chat_id, game, cur_pid, turn_i, roll, movable[0])
        else:
            game["pending_move"] = {"player_id": cur_pid, "roll": roll}
            await _ludo_send_board(
                context, chat_id, game,
                caption=_ludo_status(
                    game,
                    f"🎲 {cur_name} rolled <b>{roll}</b> — choose a token!"),
                roll_kb=_ludo_token_kb(chat_id, cur_pid, movable),
            )

    # ── tok ───────────────────────────────────────────────────────────────────
    elif action == "tok":
        chat_id   = int(parts[2])
        player_id = int(parts[3])
        token_idx = int(parts[4])
        if chat_id not in active_ludo:
            await query.answer("Game not found!", show_alert=True)
            return
        game = active_ludo[chat_id]
        if query.from_user.id != player_id:
            await query.answer("Not your token!", show_alert=True)
            return
        pm = game.get("pending_move")
        if not pm or pm["player_id"] != player_id:
            await query.answer("No pending move!", show_alert=True)
            return
        await query.answer()
        roll   = pm["roll"]
        turn_i = game["turn"]
        game["pending_move"] = None
        await _ludo_apply_move(
            query, context, chat_id, game, player_id, turn_i, roll, token_idx)

    else:
        await query.answer()


async def _ludo_apply_move(query, context, chat_id: int, game: dict,
                            pid: int, turn_i: int, roll: int, token_idx: int):
    players = game["players"]
    names   = game["names"]
    colors  = game["colors"]
    tokens  = game["tokens"]
    ci      = colors[turn_i]

    old_pos = tokens[pid][token_idx]
    new_pos = 1 if old_pos == 0 else old_pos + roll
    tokens[pid][token_idx] = new_pos

    event = ""

    # kill check (main path only, non-safe cells)
    if 1 <= new_pos <= 52:
        abs_idx = _ludo_abs_idx(new_pos, ci)
        if abs_idx not in LUDO_SAFE_IDX:
            my_cell = LUDO_PATH[abs_idx]
            for oi, opid in enumerate(players):
                if opid == pid:
                    continue
                for oti, opos in enumerate(tokens[opid]):
                    if 1 <= opos <= 52:
                        oabs = _ludo_abs_idx(opos, colors[oi])
                        if LUDO_PATH[oabs] == my_cell:
                            tokens[opid][oti] = 0
                            event += f"\n💥 {names[opid]}'s T{oti+1} back to base!"

    em    = LUDO_EMOJIS[ci]
    p_lbl = "🏁 HOME!" if new_pos >= LUDO_HOME else \
            (f"HS{new_pos-52}" if new_pos >= 53 else f"step {new_pos}")
    move_txt = (
        f"{em} {names[pid]} entered the board with T{token_idx+1}!"
        if old_pos == 0
        else f"{em} {names[pid]} T{token_idx+1} → {p_lbl}"
    )
    if event:
        move_txt += event

    # win check — all 4 tokens home
    if all(t >= LUDO_HOME for t in tokens[pid]):
        del active_ludo[chat_id]
        img = draw_ludo_board(game)
        mid = game.get("board_msg_id")
        win_cap = (
            f"{move_txt}\n\n"
            f"🏆 <b>{names[pid]} wins Ludo!</b> All 4 tokens home! 🎉"
        )
        if mid:
            try:
                await context.bot.edit_message_media(
                    chat_id=chat_id, message_id=mid,
                    media=InputMediaPhoto(media=img, caption=win_cap, parse_mode="HTML"),
                )
                return
            except Exception:
                pass
        await context.bot.send_photo(chat_id, photo=img,
                                      caption=win_cap, parse_mode="HTML")
        return

    # extra turn on 6
    if roll == 6:
        move_txt += "\n🎲 Rolled 6 — extra turn!"
    else:
        game["turn"] = (turn_i + 1) % len(players)

    await _ludo_send_board(
        context, chat_id, game,
        caption=_ludo_status(game, move_txt),
    )
