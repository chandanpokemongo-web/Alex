"""
PIL board image generators.
  draw_snl_board(pos0, pos1, name0, name1) -> BytesIO  (PNG)
  draw_ludo_board(game)                   -> BytesIO  (PNG)
"""
import math
from io import BytesIO

from PIL import Image, ImageDraw

# ─────────────────────────────────────────────────────────────────────────────
#  SNAKE & LADDERS
# ─────────────────────────────────────────────────────────────────────────────

SNL_SNAKES  = {99:78, 95:75, 93:73, 87:24, 64:60, 62:19, 56:53, 49:11, 47:26, 16:6}
SNL_LADDERS = {4:14,  9:31, 20:38, 28:84, 40:59, 51:67, 63:81, 71:91}

_CELL   = 54
_PAD    = 8
_LEG    = 52
_SW     = _CELL * 10 + _PAD * 2
_SH     = _CELL * 10 + _PAD * 2 + _LEG

_C_EVEN  = (255, 250, 220)
_C_ODD   = (220, 235, 255)
_C_SNAKE = (255, 195, 195)
_C_LADR  = (195, 255, 195)
_C_GOLD  = (255, 215,  50)
_C_BG    = (30,  30,  55)
_P_COLORS = [(220, 50, 50), (50, 100, 220)]   # red, blue


def _snl_xy(n: int):
    rn  = (n - 1) // 10
    sr  = 9 - rn
    col = (n - 1) % 10 if rn % 2 == 0 else 9 - (n - 1) % 10
    return _PAD + col * _CELL, _PAD + sr * _CELL


def _snl_cx(n: int):
    x, y = _snl_xy(n)
    return x + _CELL // 2, y + _CELL // 2


def _draw_ladder_snl(d: ImageDraw.ImageDraw, n1: int, n2: int):
    x1, y1 = _snl_cx(n1)
    x2, y2 = _snl_cx(n2)
    dx, dy  = x2 - x1, y2 - y1
    ln      = math.hypot(dx, dy) or 1
    px, py  = -dy / ln * 5, dx / ln * 5
    for sign in (1, -1):
        d.line([(x1 + px * sign, y1 + py * sign),
                (x2 + px * sign, y2 + py * sign)],
               fill=(160, 110, 20), width=3)
    steps = max(2, int(ln // 22))
    for i in range(1, steps):
        t  = i / steps
        rx = int(x1 + dx * t);  ry = int(y1 + dy * t)
        d.line([(rx + int(px * 1.5), ry + int(py * 1.5)),
                (rx - int(px * 1.5), ry - int(py * 1.5))],
               fill=(210, 150, 40), width=2)


def _draw_snake_snl(d: ImageDraw.ImageDraw, head: int, tail: int):
    hx, hy = _snl_cx(head)
    tx, ty = _snl_cx(tail)
    dx, dy  = tx - hx, ty - hy
    ln      = math.hypot(dx, dy) or 1
    mx = (hx + tx) // 2 + int(-dy / ln * 22)
    my = (hy + ty) // 2 + int( dx / ln * 22)
    pts = []
    for i in range(21):
        t  = i / 20
        x  = int((1-t)**2 * hx + 2*(1-t)*t * mx + t**2 * tx)
        y  = int((1-t)**2 * hy + 2*(1-t)*t * my + t**2 * ty)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i+1]], fill=(190, 20, 20), width=4)
    r = 8
    d.ellipse([hx-r, hy-r, hx+r, hy+r], fill=(210, 0, 0), outline=(100, 0, 0), width=1)
    for ox in (-3, 2):
        d.ellipse([hx+ox, hy-5, hx+ox+3, hy-2], fill=(255, 255, 255))


def draw_snl_board(pos0: int, pos1: int, name0: str, name1: str) -> BytesIO:
    img = Image.new("RGB", (_SW, _SH), _C_BG)
    d   = ImageDraw.Draw(img)

    for n in range(1, 101):
        x, y    = _snl_xy(n)
        rn, col = (n-1)//10, (n-1)%10
        if n == 100:
            fill = _C_GOLD
        elif n in SNL_SNAKES:
            fill = _C_SNAKE
        elif n in SNL_LADDERS:
            fill = _C_LADR
        else:
            fill = _C_EVEN if (rn + col) % 2 == 0 else _C_ODD
        d.rectangle([x, y, x+_CELL-1, y+_CELL-1], fill=fill, outline=(140, 140, 165))
        d.text((x + 3, y + 2), str(n), fill=(70, 70, 90))

    for b, t in SNL_LADDERS.items():
        _draw_ladder_snl(d, b, t)
    for h, t in SNL_SNAKES.items():
        _draw_snake_snl(d, h, t)

    for pi, (pos, pc, nm) in enumerate([(pos0, _P_COLORS[0], name0),
                                         (pos1, _P_COLORS[1], name1)]):
        if pos > 0:
            cx, cy = _snl_cx(pos)
            if pos0 == pos1:
                cx += -7 if pi == 0 else 7
            r = 10
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=pc, outline=(255, 255, 255), width=2)
            d.text((cx - 4, cy - 5), (nm[0] if nm else "?").upper(), fill=(255, 255, 255))

    ly = _PAD + _CELL * 10 + 10
    for pi, (pc, nm) in enumerate([(_P_COLORS[0], name0), (_P_COLORS[1], name1)]):
        ox = _PAD if pi == 0 else _SW // 2
        d.rectangle([ox, ly, ox+16, ly+16], fill=pc, outline=(200, 200, 200))
        d.text((ox + 20, ly + 2), nm[:14], fill=(200, 200, 220))

    d.text((_PAD, ly + 22), "🐍 Snake  🪜 Ladder  ⭐ WIN (100)", fill=(170, 170, 195))

    out = BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  LUDO
# ─────────────────────────────────────────────────────────────────────────────

_LC   = 36          # cell size in pixels
_LP   = 8           # outer padding
_LLEG = 72          # legend height
_LW   = _LC * 15 + _LP * 2
_LH   = _LC * 15 + _LP * 2 + _LLEG

# 52-cell shared path (row, col on 15×15 grid, 0-indexed)
LUDO_PATH = [
    (6,1),(6,2),(6,3),(6,4),(6,5),
    (5,6),(4,6),(3,6),(2,6),(1,6),(0,6),(0,7),(0,8),
    (1,8),(2,8),(3,8),(4,8),(5,8),
    (6,9),(6,10),(6,11),(6,12),(6,13),(6,14),
    (7,14),(8,14),
    (8,13),(8,12),(8,11),(8,10),(8,9),
    (9,8),(10,8),(11,8),(12,8),(13,8),(14,8),
    (14,7),(14,6),
    (13,6),(12,6),(11,6),(10,6),(9,6),
    (8,5),(8,4),(8,3),(8,2),(8,1),
    (7,0),(6,0),(5,0),
]
# entry abs-indices:  Red=0=(6,1)  Blue=13=(1,8)  Green=26=(8,13)  Yellow=39=(13,6)
LUDO_ENTRY_IDX = [0, 13, 26, 39]

# home-stretch cells per colour (5 cells → WIN at centre)
LUDO_HS = [
    [(1,7),(2,7),(3,7),(4,7),(5,7)],      # Red:    col 7 rows 1→5
    [(7,13),(7,12),(7,11),(7,10),(7,9)],  # Blue:   row 7 cols 13→9
    [(13,7),(12,7),(11,7),(10,7),(9,7)],  # Green:  col 7 rows 13→9
    [(7,1),(7,2),(7,3),(7,4),(7,5)],      # Yellow: row 7 cols 1→5
]

LUDO_SAFE_IDX = {0, 6, 13, 19, 26, 32, 39, 45}

# home-corner top-left (row, col) for each colour
_HOME_CORNERS = [(0,0), (0,9), (9,9), (9,0)]
# token base slots inside each home corner (absolute row, col)
_HOME_SLOTS   = [
    [(1,1),(1,3),(3,1),(3,3)],
    [(1,10),(1,12),(3,10),(3,12)],
    [(10,10),(10,12),(12,10),(12,12)],
    [(10,1),(10,3),(12,1),(12,3)],
]

_LUDO_MAIN   = [(220, 40, 40), (40, 80, 220), (40, 180, 40), (220, 180, 0)]
_LUDO_LIGHT  = [(255, 175, 175), (175, 200, 255), (175, 245, 175), (255, 240, 145)]
_LUDO_NAMES  = ["Red", "Blue", "Green", "Yellow"]


def _lc(r: int, c: int):
    return _LP + c * _LC, _LP + r * _LC


def _lcx(r: int, c: int):
    x, y = _lc(r, c)
    return x + _LC // 2, y + _LC // 2


def _token_board_pos(pos: int, ci: int):
    """(row, col) of token on the 15×15 grid. Returns None if won."""
    if pos == 0:
        return None  # caller uses home slot
    if pos >= 58:
        return None  # won — don't draw
    if pos >= 53:
        return LUDO_HS[ci][min(pos - 53, 4)]
    abs_idx = (LUDO_ENTRY_IDX[ci] + pos - 1) % 52
    return LUDO_PATH[abs_idx]


def draw_ludo_board(game: dict) -> BytesIO:
    img = Image.new("RGB", (_LW, _LH), (35, 25, 50))
    d   = ImageDraw.Draw(img)

    # board background
    d.rectangle([_LP, _LP, _LP + _LC*15 - 1, _LP + _LC*15 - 1], fill=(240, 235, 225))

    # coloured home corners (6×6 each)
    for ci, (r0, c0) in enumerate(_HOME_CORNERS):
        x1, y1 = _LP + c0*_LC, _LP + r0*_LC
        x2, y2 = x1 + 6*_LC - 1, y1 + 6*_LC - 1
        d.rectangle([x1, y1, x2, y2], fill=_LUDO_MAIN[ci])
        pad = _LC // 2
        d.rectangle([x1+pad, y1+pad, x2-pad, y2-pad], fill=(255, 255, 255))

    # home-stretch lanes
    path_set = set(LUDO_PATH)
    for ci, cells in enumerate(LUDO_HS):
        for r, c in cells:
            x, y = _lc(r, c)
            d.rectangle([x, y, x+_LC-1, y+_LC-1], fill=_LUDO_LIGHT[ci], outline=(200,200,200))

    # main-path cells
    for idx, (r, c) in enumerate(LUDO_PATH):
        x, y = _lc(r, c)
        if idx in {0, 13, 26, 39}:
            ci   = [0,13,26,39].index(idx)
            fill = _LUDO_LIGHT[ci]
        elif idx in LUDO_SAFE_IDX:
            fill = (255, 255, 180)
        else:
            fill = (250, 250, 250)
        d.rectangle([x, y, x+_LC-1, y+_LC-1], fill=fill, outline=(175, 175, 175))
        if idx in LUDO_SAFE_IDX:
            cx, cy = _lcx(r, c)
            d.text((cx-4, cy-5), "★", fill=(200, 155, 0))

    # remaining corridor cells (cross) not covered above
    hs_set   = {rc for cells in LUDO_HS for rc in cells}
    for r in range(15):
        for c in range(15):
            in_corner = (
                (r < 6 and c < 6) or (r < 6 and c >= 9) or
                (r >= 9 and c < 6) or (r >= 9 and c >= 9)
            )
            if in_corner or (r, c) in path_set or (r, c) in hs_set:
                continue
            x, y = _lc(r, c)
            d.rectangle([x, y, x+_LC-1, y+_LC-1], fill=(245, 245, 245), outline=(180,180,180))

    # centre finish triangle (4 coloured triangles meeting at centre)
    cx0, cy0 = _LP + 7*_LC, _LP + 7*_LC
    cxm, cym = cx0 + _LC//2, cy0 + _LC//2   # actual pixel centre
    corners  = [(cx0, cy0), (cx0+_LC, cy0), (cx0+_LC, cy0+_LC), (cx0, cy0+_LC)]
    for ci, (px, py) in enumerate(corners):
        nxt = corners[(ci+1) % 4]
        d.polygon([(cxm, cym), (px, py), nxt], fill=_LUDO_MAIN[ci])

    # tokens
    players = game["players"]
    names   = game["names"]
    colors  = game["colors"]
    tokens  = game["tokens"]

    for pi, pid in enumerate(players):
        ci   = colors[pi]
        tkns = tokens[pid]
        for ti, pos in enumerate(tkns):
            if pos >= 58:
                continue
            if pos == 0:
                r, c = _HOME_SLOTS[ci][ti]
            else:
                rc = _token_board_pos(pos, ci)
                if rc is None:
                    continue
                r, c = rc

            cx, cy = _lcx(r, c)
            ox = (-5 if ti % 2 == 0 else 5)
            oy = (-4 if ti < 2      else 4)
            rt = 7
            d.ellipse([cx+ox-rt, cy+oy-rt, cx+ox+rt, cy+oy+rt],
                      fill=_LUDO_MAIN[ci], outline=(255,255,255), width=1)
            d.text((cx+ox-3, cy+oy-5), str(ti+1), fill=(255,255,255))

    # legend
    ly   = _LP + _LC*15 + 8
    x_off = _LP
    for pi, pid in enumerate(players):
        ci   = colors[pi]
        tkns = tokens[pid]
        home_n = sum(1 for t in tkns if t >= 58)
        path_n = sum(1 for t in tkns if 0 < t < 58)
        nm     = names[pid][:9]
        d.rectangle([x_off, ly, x_off+13, ly+13], fill=_LUDO_MAIN[ci])
        d.text((x_off+17, ly+1), f"{nm} 🏁{home_n} ▶{path_n}", fill=(200,200,220))
        x_off += (_LW - _LP*2) // len(players) + _LP

    d.text((_LP, ly + 20), "★ = safe  enter w/ 🎲6  all 4 home = WIN", fill=(165,165,190))

    out = BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out
