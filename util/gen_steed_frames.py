#!/usr/bin/env python3
"""gen_steed_frames.py: RighteousHack Easter egg, the winged fiery steed
flies into the sunset. Standalone (Python 3 standard library only).

Builds the 71 approved frames (80x24, NetHack tty colors) and writes the
C RLE data for src/endframes.c as seq ENDCUT_STEED (5).

  python3 gen_steed_frames.py [--base N] [-o steed_frames.inc] [--json out.json]

--base N  index of the first steed run inside end_runs[] (the count of
          runs already there). Default 0, so frame starts are relative.
Runs are split at 255 because struct endrun stores n as unsigned char.
Every frame time is a multiple of 50 ms (the endcut_wait tick).
Cell encoding matches endcut_play: ch = ASCII code, col = tty color,
inv = 1 for inverse. An empty cell is {ch 32, col 0, inv 0}.
"""
import math, random, sys, json, argparse

"""Shared helpers for the RighteousHack animation previews.
Colors use NetHack tty color numbers (0-15), stored as one hex char per cell.
' ' with no color means an empty (black) cell."""

W, H = 80, 24

# NetHack tty color numbers -> Windows Terminal default (Campbell) palette.
# 0 = CLR_BLACK drawn as dark gray (use_darkgray), 8 (NO_COLOR) unused.
PALETTE = {
    0: ("black/dark gray", "#767676"),
    1: ("red", "#C50F1F"),
    2: ("green", "#13A10E"),
    3: ("brown", "#C19C00"),
    4: ("blue", "#0037DA"),
    5: ("magenta", "#881798"),
    6: ("cyan", "#3A96DD"),
    7: ("gray", "#CCCCCC"),
    8: ("no color", "#CCCCCC"),
    9: ("orange (bright red)", "#E74856"),
    10: ("bright green", "#16C60C"),
    11: ("yellow", "#F9F1A5"),
    12: ("bright blue", "#3B78FF"),
    13: ("bright magenta", "#B4009E"),
    14: ("bright cyan", "#61D6D6"),
    15: ("white", "#F2F2F2"),
}
BG = "#0C0C0C"
BLK, RED, GRN, BRN, BLU, MAG, CYN, GRY = 0, 1, 2, 3, 4, 5, 6, 7
BRED, BGRN, YEL, BBLU, BMAG, BCYN, WHT = 9, 10, 11, 12, 13, 14, 15
HEX = "0123456789abcdef"


class Canvas:
    def __init__(self):
        self.ch = [[" "] * W for _ in range(H)]
        self.co = [[GRY] * W for _ in range(H)]
        self.iv = [[0] * W for _ in range(H)]

    def copy(self):
        c = Canvas()
        c.ch = [r[:] for r in self.ch]
        c.co = [r[:] for r in self.co]
        c.iv = [r[:] for r in self.iv]
        return c

    def clear_rect(self, x0, y0, x1, y1):
        for y in range(max(0, y0), min(H, y1 + 1)):
            for x in range(max(0, x0), min(W, x1 + 1)):
                self.ch[y][x] = " "; self.co[y][x] = GRY; self.iv[y][x] = 0

    def set(self, x, y, c, col, inv=0):
        if 0 <= x < W and 0 <= y < H:
            self.ch[y][x] = c
            self.co[y][x] = col
            self.iv[y][x] = inv

    def get(self, x, y):
        return self.ch[y][x]

    def put(self, x, y, s, col, inv=0, trans=True):
        for i, c in enumerate(s):
            if trans and c == " ":
                continue
            self.set(x + i, y, c, col, inv)

    def sprite(self, x, y, lines, col, inv=0, trans=True):
        """col may be an int or a function (ch, dx, dy) -> int or None."""
        for dy, line in enumerate(lines):
            for dx, c in enumerate(line):
                if trans and c == " ":
                    continue
                cc = col(c, dx, dy) if callable(col) else col
                if cc is None:
                    continue
                self.set(x + dx, y + dy, c, cc, inv)

    def center(self, y, s, col, inv=0):
        x = (W - len(s)) // 2
        self.put(x, y, s, col, inv, trans=False)

    def recolor(self, fn):
        """fn(ch, col, x, y) -> new col"""
        for y in range(H):
            for x in range(W):
                if self.ch[y][x] != " ":
                    self.co[y][x] = fn(self.ch[y][x], self.co[y][x], x, y)

    def to_frame(self, ms, note=""):
        lines, fg, inv = [], [], []
        anyinv = False
        for y in range(H):
            lines.append("".join(self.ch[y]))
            fg.append("".join(HEX[self.co[y][x]] if self.ch[y][x] != " " or self.iv[y][x] else "." for x in range(W)))
            row = "".join("1" if self.iv[y][x] else "0" for x in range(W))
            anyinv |= "1" in row
            inv.append(row)
        f = {"ms": ms, "lines": lines, "fg": fg}
        if anyinv:
            f["inv"] = inv
        if note:
            f["note"] = note
        return f



"""RighteousHack Easter egg: the winged fiery steed flies into the sunset.
Plays after the Redeemed memorial stone when the hero rode the fiery
steed of the Heavenly Host through the gate. No words on screen."""
import math, random

TEXT = ""
HZ = 16                    # horizon row
SUNX, SUNY = 57, 16        # sun center, sitting on the horizon
RX, RY = 10.0, 5.0         # sun radii in cells (cells are 1:2)
frames = []


def S(block):
    return [l[1:] for l in block.strip("\n").split("\n")]

# ---------------------------------------------------------------- steed art
# Each size: body lines, wing frames {name: (dx, dy, lines)}, tail point,
# where the anchor (0, 0) is the top-left of the body.
BODY_L = S(r"""
|                       /\/\
|                   ~~ _/ o  \
|          ____.---~~''  ,___)
|  ~~~~.-''              /
| ~~~~(                 (
|  ~~~ `.  .______.  /\  \
|       / /        \ \ `. \
|     _/ /          `-'  `-'
|    `--'
""")
# (dx, dy, lines, in_front)
WING_L = {
    "up": (5, -5, S(r"""
|  .
|  |`.
|  | \`.
|   \ \\`.
|    \ \\\`.
|     \_\\\\`.
"""), False),
    "mid": (-1, -1, S(r"""
|            __..--'`.
|     _..--''//////.'
|   <'-==//////__.'
"""), True),
    "down": (8, 2, S(r"""
|  ________
|  \\\\\\\/
|   \\\\\/
|    \\\/
|     \/
"""), True),
}
BODY_M = S(r"""
|              /\/\
|            ~_/o  \
|   ~~~.--~~'  ,__)
|  ~~~(        (
|   ~~ `. .__./\ \
|       //    `' `'
""")
WING_M = {
    "up": (4, -2, S(r"""
| .
| |`.
|  \\`.
|   \\\`.
"""), False),
    "mid": (1, 0, S(r"""
|     _.-'`.
|  <'=///_.'
"""), True),
    "down": (6, 2, S(r"""
| ____
| \\\/
|  \/
"""), True),
}
BODY_S = S(r"""
| ~~.__./o>
|   /'  `\
""")
WING_S = {
    "up": (3, -2, S(r"""
| .
| \`.
"""), False),
    "mid": (2, -1, S(r"""
| <=='.
"""), True),
    "down": (4, 0, S(r"""
|  __
|  \/
"""), True),
}
BODY_XS = S(r"""
|~=v>
""")
WING_XS = {"up": (2, -1, ["\\"], False), "mid": (1, 0, [], True), "down": (2, 1, ["/"], True)}

SIZES = {
    "L": (BODY_L, WING_L),
    "M": (BODY_M, WING_M),
    "S": (BODY_S, WING_S),
    "XS": (BODY_XS, WING_XS),
}
FLAP = ["up", "mid", "down", "mid"]
FIRE = [YEL, BRED, RED, BRED, YEL, WHT]


def body_color(ch, dx, dy, t):
    if ch in "~=":
        return FIRE[(dx * 3 + dy * 5 + t) % 5]
    if ch == "o":
        return YEL
    return BRED                       # CLR_ORANGE, the steed's own color


def wing_color(ch, dx, dy, t):
    if ch in ".`,'" or ch == "<":
        return WHT
    return YEL if (dx + dy + t // 2) % 3 else BRN

# ---------------------------------------------------------------- sky
random.seed(77)
STARS = [(random.randrange(80), random.randrange(0, 4)) for _ in range(26)]
# Thin wisps of cloud, lit from below: (row, x, shape, color, drift)
WISPS = [
    (3, 6, "_.--~~~--._", BLU, 0.05), (4, 44, "_.-~~-._", BLU, 0.05),
    (6, 22, ".-~~~~~~~-.__", RED, 0.07), (7, 64, "_.-~~~~-._", RED, 0.07),
    (5, 74, "-~~-.", BLU, 0.05),
    (9, 2, "__.--~~~~~~--.._", RED, 0.09), (10, 36, "_.-~~~~-._", RED, 0.09),
    (8, 50, ".-~~-.", RED, 0.09),
    (12, 14, "_..--~~~~~~~~~--.._", BRED, 0.11), (11, 68, "_.-~~~-._", BRED, 0.11),
    (14, 0, "__..---~~~~~~~~---..__", BRN, 0.13), (13, 34, "_.--~~--._", BRN, 0.13),
    (15, 70, "_.-~~~-.", BRN, 0.13), (15, 28, "_.-~-._", YEL, 0.13),
]


def sun_r(x, y, grow=1.0):
    return math.hypot((x - SUNX) / (RX * grow), (y - SUNY) / (RY * grow))


def sun_cell(x, y, grow=1.0, flash=0.0):
    """Return (ch, col, inv) for a sun cell or None. Only rows <= HZ."""
    if y > HZ:
        return None
    r = sun_r(x, y, grow)
    core = 0.45 + 0.4 * flash
    if r < core:
        return (" ", WHT if flash > 0.25 else YEL, 1)
    if r < 0.78:
        return (" ", YEL, 1)
    if r < 1.0:
        return (" ", BRN, 1)
    hsh = (x * 31 + y * 17) % 7
    if r < 1.16:
        return (":" if hsh < 2 else ".", BRN, 0) if hsh != 6 else None
    if r < 1.34:
        return (".", BRED, 0) if hsh in (0, 2, 4) else None
    return None


def draw_sky(c, t, grow=1.0, flash=0.0, rays=0.0):
    # stars twinkle
    for i, (x, y) in enumerate(STARS):
        k = (i * 7 + t) % 11
        if k == 0:
            continue
        c.set(x, y, "*" if k == 5 else ".", WHT if k in (4, 5, 6) else GRY if i % 2 else BLU)
    # the warm glow of the sky, densest near the horizon (fixed dither)
    for y in range(4, HZ):
        dens = [0, 0, 0, 0, .02, .03, .04, .05, .06, .07, .09, .12, .15, .19, .24, .30][y]
        col = BLU if y < 6 else RED if y < 9 else BRED if y < 13 else BRN
        for x in range(80):
            hsh = (x * 7919 + y * 104729) % 1000 / 1000.0
            near = max(0.0, 1.0 - abs(x - SUNX) / 45.0)
            if hsh < dens * (0.6 + 0.8 * near):
                c.set(x, y, "." if hsh < dens * 0.8 else "-", col)
    # wisps drift slowly left
    for y, x0, shape, col, sp in WISPS:
        x = int(round((x0 - sp * t) % 100)) - 10
        c.put(x, y, shape, col)
    # horizon
    for x in range(80):
        c.set(x, HZ, "_", BRED if abs(x - SUNX) < 30 else RED)
    # sun rays (only in the flash)
    if rays > 0:
        L = 2 + 14 * rays                     # length in rows
        top = SUNY - RY * grow                # sun top row
        for k, ch in ((0, "|"), (1, "/"), (-1, "\\"), (2.6, "."), (-2.6, "."), (5.5, "."), (-5.5, ".")):
            for j in range(1, int(L) + 1):
                fy = SUNY - (RY * grow * 0.75 if k else RY * grow) - j
                y = int(round(fy))
                if y < 0:
                    break
                x = int(round(SUNX + k * (SUNY - fy) * (1.0 if abs(k) < 2 else 1.0)))
                x0 = int(round(SUNX + (k * RX * 0.55 if k else 0)))
                x = x0 + int(round(k * j))
                if not (0 <= x < W) or (j + t) % 4 == 0:
                    continue
                c.set(x, y, ch, WHT if j < L * 0.45 else YEL)
    # the sun
    for y in range(0, HZ + 1):
        for x in range(80):
            sc = sun_cell(x, y, grow, flash)
            if sc:
                ch, col, inv = sc
                if y == HZ and not inv:
                    continue
                c.set(x, y, ch, col, inv)
    # the sea, with the sun's shimmering road
    rnd = random.Random(t * 131)
    for y in range(HZ + 1, H):
        depth = y - HZ
        half = 5 + depth * 2.2
        for x in range(80):
            d = abs(x - SUNX)
            if d < half * grow:
                v = rnd.random()
                f = d / (half * grow)
                if v < 0.55 - f * 0.25:
                    col = WHT if (flash > 0.3 and f < 0.4) else YEL if f < 0.35 else BRN if f < 0.7 else BRED
                    c.set(x, y, rnd.choice("~-=") if f < 0.5 else rnd.choice("~-"), col)
            elif rnd.random() < 0.10:
                c.set(x, y, "~", RED if (x + y) % 3 else BLU)


# ---------------------------------------------------------------- steed
TRAIL = []        # [x, y, age]


def put_cell(c, x, y, ch, col):
    """Over the sun the steed is a dark silhouette (inverse on sun color)."""
    if not (0 <= x < W and 0 <= y < H):
        return
    if c.iv[y][x]:
        c.set(x, y, ch, c.co[y][x], 1)
    else:
        c.set(x, y, ch, col)


def draw_steed(c, size, ax, ay, t):
    body, wings = SIZES[size]
    flap = FLAP[(t // 1) % 4]
    wdx, wdy, wl, front = wings[flap]
    layers = []
    if front:
        layers = [("b", 0, 0, body), ("w", wdx, wdy, wl)]
    else:
        layers = [("w", wdx, wdy, wl), ("b", 0, 0, body)]
    for kind, ox, oy, lines in layers:
        for dy, line in enumerate(lines):
            st = len(line) - len(line.lstrip())
            en = len(line.rstrip())
            for dx in range(st, en):
                x, y = ax + ox + dx, ay + oy + dy
                if 0 <= x < W and 0 <= y < H and not c.iv[y][x]:
                    c.set(x, y, " ", GRY)
        for dy, line in enumerate(lines):
            for dx, ch in enumerate(line):
                if ch == " ":
                    continue
                col = body_color(ch, dx, dy, t) if kind == "b" else wing_color(ch, dx, dy, t)
                put_cell(c, ax + ox + dx, ay + oy + dy, ch, col)


def tail_point(size, ax, ay):
    return {"L": (ax, ay + 4), "M": (ax + 1, ay + 3), "S": (ax, ay), "XS": (ax - 1, ay)}[size]


def draw_trail(c, t):
    for p in TRAIL:
        x, y, age = p
        if age > 6:
            continue
        ch = "*+~~.. "[age]
        col = [YEL, YEL, BRED, BRED, RED, RED, RED][age]
        if ch != " ":
            put_cell(c, int(x), int(y), ch, col)


def step_trail(rnd):
    for p in TRAIL:
        p[0] -= rnd.choice((0, 1, 1))
        p[1] += rnd.choice((-1, 0, 0, 0, 1)) * 0.5
        p[2] += 1
    TRAIL[:] = [p for p in TRAIL if p[2] <= 6]


# ---------------------------------------------------------------- build
def build():
    frames.clear()
    TRAIL.clear()
    rnd = random.Random(5)
    t = 0
    # 1. the empty sunset
    for i in range(4):
        c = Canvas(); draw_sky(c, t); frames.append(c.to_frame(150)); t += 1
    # 2. the flight
    NA, NB = 18, 34
    W_ = {"L": 29, "M": 18, "S": 10, "XS": 4, "dot": 1}
    Hh = {"L": 9, "M": 6, "S": 2, "XS": 1, "dot": 1}
    EX, EY = SUNX, SUNY - 3          # the heart of the sun
    path = []
    for i in range(NA):              # sweeps in large across the sky
        u = i / (NA - 1)
        cx = -14 + 42 * (1 - (1 - u) ** 2)
        cy = 9.5 - 1.0 * math.sin(math.pi * u)
        path.append(("L", cx, cy))
    for i in range(1, NB + 1):       # and goes away toward the sun
        u = i / NB
        e = 1 - (1 - u) ** 1.6
        cx = 28 + (EX - 28) * e
        cy = 9.5 + (EY - 9.5) * (e ** 1.5) - 1.5 * math.sin(math.pi * e)
        size = "M" if u < 0.30 else "S" if u < 0.58 else "XS" if u < 0.82 else "dot"
        path.append((size, cx, cy))
    for size, cx, cy in path:
        ax = int(round(cx - W_[size] / 2))
        ay = int(round(cy - Hh[size] / 2))
        c = Canvas(); draw_sky(c, t)
        if size not in ("dot",):
            tx, ty = tail_point(size, ax, ay)
            n_sp = {"L": 3, "M": 2, "S": 1, "XS": 1}[size]
            for _ in range(n_sp):
                TRAIL.append([tx - rnd.randint(0, 2), ty + rnd.choice((-1, 0, 0, 1)), 0])
        draw_trail(c, t)
        if size == "dot":
            put_cell(c, int(round(cx)), int(round(cy)), "v" if t % 2 else "-", YEL)
        else:
            draw_steed(c, size, ax, ay, t)
        step_trail(rnd)
        frames.append(c.to_frame(100)); t += 1
    # 3. into the sun: it flares
    flare = [(1.03, 0.5, 0.15), (1.08, 0.9, 0.35), (1.12, 1.0, 0.6), (1.14, 1.0, 0.85),
             (1.12, 0.9, 1.0), (1.09, 0.7, 0.8), (1.06, 0.5, 0.55), (1.04, 0.35, 0.3)]
    for g, f, r in flare:
        c = Canvas(); draw_sky(c, t, grow=g, flash=f, rays=r)
        draw_trail(c, t); step_trail(rnd)
        frames.append(c.to_frame(100)); t += 1
    # 4. the glow settles
    for k in range(6):
        g = 1.035 - 0.005 * k
        c = Canvas(); draw_sky(c, t, grow=g, flash=0.4 - 0.015 * k, rays=0.22 - 0.02 * k)
        frames.append(c.to_frame(150)); t += 1
    c = Canvas(); draw_sky(c, t, grow=1.0, flash=0.3, rays=0.16)
    frames.append(c.to_frame(1200))


# ---------------------------------------------------------------- C output
ENDCUT_STEED = 5


def frame_cells(fr):
    inv = fr.get("inv")
    for y in range(H):
        for x in range(W):
            ch = fr["lines"][y][x]
            f = fr["fg"][y][x]
            iv = 1 if inv and inv[y][x] == "1" else 0
            col = 0 if f == "." else int(f, 16)
            if ch == " " and not iv:
                col = 0
            yield (ord(ch), col, iv)


def rle(fr):
    runs = []
    for cell in frame_cells(fr):
        if runs and tuple(runs[-1][1:]) == cell and runs[-1][0] < 255:
            runs[-1][0] += 1
        else:
            runs.append([1, cell[0], cell[1], cell[2]])
    assert sum(r[0] for r in runs) == W * H
    return runs


def emit_c(frames_, base=0):
    allruns, table = [], []
    for fr in frames_:
        assert fr["ms"] % 50 == 0 and fr["ms"] <= 65535
        r = rle(fr)
        table.append((fr["ms"], ENDCUT_STEED, base + len(allruns), len(r)))
        allruns.extend(r)
    out = []
    out.append("/* Generated by gen_steed_frames.py. Do not edit by hand.")
    out.append("   ENDCUT_STEED: the winged fiery steed flies into the sunset.")
    out.append("   %d frames, %d ms, %d runs, first run index %d. */"
               % (len(table), sum(t[0] for t in table), len(allruns), base))
    out.append("#define ENDCUT_STEED 5")
    out.append("#define ENDCUT_STEED_NFRAMES %d" % len(table))
    out.append("#define ENDCUT_STEED_NRUNS %d" % len(allruns))
    out.append("")
    out.append("/* Append these to end_runs[]. */")
    out.append("#ifdef ENDCUT_STEED_RUNS")
    line = []
    for r in allruns:
        line.append("{%d,%d,%d,%d}," % tuple(r))
        if len(line) == 8:
            out.append("    " + "".join(line)); line = []
    if line:
        out.append("    " + "".join(line))
    out.append("#endif /* ENDCUT_STEED_RUNS */")
    out.append("")
    out.append("/* Append these to end_frames[]: {ms, seq, start, nruns}. */")
    out.append("#ifdef ENDCUT_STEED_FRAMES")
    for t in table:
        out.append("    {%d,%d,%d,%d}," % t)
    out.append("#endif /* ENDCUT_STEED_FRAMES */")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=int, default=0)
    ap.add_argument("-o", "--out", default="steed_frames.inc")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    build()
    for i, fr in enumerate(frames):
        assert len(fr["lines"]) == H and all(len(l) == W for l in fr["lines"]), i
        for l in fr["lines"]:
            assert all(32 <= ord(ch) < 127 for ch in l), (i, l)
    with open(a.out, "w", newline="\n") as f:
        f.write(emit_c(frames, a.base))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(frames, f, separators=(",", ":"))
    print("%d frames, %d ms -> %s" % (len(frames), sum(f["ms"] for f in frames), a.out))


if __name__ == "__main__":
    main()
