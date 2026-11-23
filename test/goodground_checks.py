#!/usr/bin/env python3
"""Static checks for the Good Ground, the ending, and the backlog fixes."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GG = (ROOT / "src" / "goodground.c").read_text()
LUA = (ROOT / "dat" / "goodground.lua").read_text()
WAYS = (ROOT / "src" / "wayside.c").read_text()
PATCH = (ROOT / "include" / "patchlevel.h").read_text()
HACK = (ROOT / "src" / "hack.c").read_text()
PRAY = (ROOT / "src" / "pray.c").read_text()
OBJ = (ROOT / "src" / "objnam.c").read_text()
THORNS = (ROOT / "src" / "thorns.c").read_text()

INTRO = (
    "The darkness of the pit is behind thee. Thou standest in a wide green field beneath a gentle sky, and the air is sweet with grass and blossom.\n"
    "\n"
    "Furrows of rich dark earth stretch before thee, heavy with grain. Sheep graze quietly upon the hillsides, and somewhere a bell tinkleth on a lamb's neck.\n"
    "\n"
    "At the heart of the land standeth a walled garden, and above its wall riseth the crown of a great fig tree, green and laden with fruit. Before the gate a shepherd waiteth, leaning upon his staff, and within the garden another keepeth watch over the flock.\n"
    "\n"
    "This is the good ground, where the seed bringeth forth fruit, some an hundredfold, some sixtyfold, some thirtyfold. Rest here, pilgrim. Thy labor hath not been in vain."
)


def map_lines():
    body = LUA.split("map = [[", 1)[1].split("]]", 1)[0]
    return [line for line in body.splitlines() if line]


def reachable(rows):
    """Walls block. Secret doors, figs (floor), and water do not.
    A door, secret or ordinary, is entered only on the orthogonal."""
    height, width = len(rows), len(rows[0])
    walk = set(".+<>{}S")
    start = None
    for y, row in enumerate(rows):
        if ">" in row:
            start = (row.index(">"), y)
            break
    seen = set()
    stack = [start]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        if rows[y][x] not in walk and rows[y][x] != "T":
            # Trees are not walls. The approved check reaches every
            # non-wall square, so a tree square can be entered.
            if rows[y][x] in "-|":
                continue
        if rows[y][x] in "-|":
            continue
        seen.add((x, y))
        for dx, dy in (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ):
            nx, ny = x + dx, y + dy
            if dx and dy:
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if rows[y][x] in "+S" or rows[ny][nx] in "+S":
                    continue
            stack.append((nx, ny))
    return seen


class Text(unittest.TestCase):
    def test_approved_lines_are_verbatim(self):
        paras = [p for p in INTRO.split("\n\n")]
        cursor = 0
        for para in paras:
            at = GG.find(para, cursor)
            self.assertGreaterEqual(at, 0, para[:40])
            cursor = at + len(para)
        self.assertGreaterEqual(GG.count('"\\n"'), 3)
        self.assertIn("The gate standeth open. Go in peace.", GG)
        self.assertIn("Go in peace, faithful one.", GG)
        self.assertIn("There is a fig here. Eat it?", GG)
        self.assertIn(
            "Thou eatest a ripe fig. It is sweet, and thou feelest renewed.",
            GG)
        self.assertIn("The figs here have all been gathered.", GG)
        self.assertIn("slew a lamb of the good ground", GG)
        self.assertIn("devoured by the hordes of darkness", GG)
        self.assertIn("strayed from the straight and narrow path", GG)
        self.assertIn(
            "Beyond lieth the open world, and thou art not ready. Wilt thou truly leave the dungeon?",
            GG)
        self.assertIn(
            "Wilt thou sit upon the throne of this city?", THORNS)
        self.assertNotIn("\u2014", GG + LUA + THORNS)

    def test_the_sanctum_line_and_the_soul_article(self):
        self.assertIn(
            'pline("The way back up is the Road to Salvation.");', HACK)
        self.assertNotIn("It has not been opened.", HACK)
        self.assertIn('!strncmpi(str, "your ", 5)', OBJ)
        self.assertIn('Strcpy(buf, "evil high altar");',
                      (ROOT / "src" / "pager.c").read_text())
        self.assertIn("offer your soul to %s...", PRAY)
        self.assertNotIn("gains dominion", PRAY)


class Map(unittest.TestCase):
    def test_geometry_and_reachability(self):
        rows = map_lines()
        self.assertEqual(len(rows), 21)
        self.assertTrue(all(len(row) == 75 for row in rows))
        self.assertEqual(rows[6][37], "<")
        self.assertEqual(rows[10][4], ">")
        self.assertEqual(rows[16][37], "+")
        self.assertEqual(rows[17][37], ".")
        self.assertEqual(rows[12][39], ".")
        self.assertEqual(rows[3][13], "S")
        self.assertEqual(rows[3][69], "S")
        for ch in "abcdefghijklm@&F":
            for row in rows:
                self.assertNotIn(ch, row)
        reached = reachable(rows)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch not in "-|":
                    self.assertIn((x, y), reached, (x, y, ch))
        self.assertIn('des.door("locked", 37, 16)', LUA)
        self.assertIn('name = "The Good Ground"',
                      (ROOT / "dat" / "dungeon.lua").read_text())
        self.assertIn(
            '{ "The Good Ground", "goodground", goodground_trial_done }',
            WAYS)

    def test_editlevel(self):
        self.assertIn("#define EDITLEVEL 20", PATCH)
        you = (ROOT / "include" / "you.h").read_text()
        self.assertIn("} ugood;", you)
        self.assertIn("hostdnum[4]", you)


class Markers(unittest.TestCase):
    def test_exact_placeholder_markers_are_gone(self):
        for folder in ("src", "dat", "include"):
            for path in (ROOT / folder).rglob("*"):
                if path.suffix not in {".c", ".h", ".lua"}:
                    continue
                self.assertNotIn("/* PLACEHOLDER */", path.read_text(
                    errors="replace"), str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
