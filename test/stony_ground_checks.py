#!/usr/bin/env python3
"""Static checks for the Stony Ground.

The BFS walks the special-level map. Blocking each trigger set must
make the summit unreachable from the foot of the pass.
"""

import pathlib
import re
import sys
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / "src" / "stony.c").read_text()
LUA = (ROOT / "dat" / "stony.lua").read_text()
HINNOM = (ROOT / "src" / "hinnom.c").read_text()
MAKEMON = (ROOT / "src" / "makemon.c").read_text()
DOG = (ROOT / "src" / "dog.c").read_text()
BONES = (ROOT / "src" / "bones.c").read_text()
WAYSIDE = (ROOT / "src" / "wayside.c").read_text()

LOCKED = [
    "The old man sinketh to his knees, pale and trembling. 'My strength faileth me! Pray for me, or lay hands upon me, for I shall not last long!'",
    "The old man riseth, and his strength is renewed. 'Bless thee, my child.'",
    "The old man's breath faileth, and he slumpeth upon the stones.\n"
    "\n"
    "Thou didst not lay hands upon him in his hour of need.\n"
    "\n"
    "The old man hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The old man leaneth upon thy shoulder and smileth. 'I have fought a good fight, I have finished my course, I have kept the faith. I could not have climbed alone. Bless thee, my child.'",
    "The young believer paceth restlessly. 'Why do we wait? I could be at the summit already! I cannot abide this slowness, my heart burneth within me!'",
    "'Make haste, make haste! The LORD is up there, and I will not tarry for anyone. Mine eyes are fixed upon the summit, and my feet will not be still!'",
    "The young believer's breathing slows. 'Forgive me. I was hasty. I will walk beside thee.'",
    "The young believer's eyes burn with zeal. 'I can wait no longer! If thou wilt not hasten, I shall go on without thee!'",
    "The young believer rusheth ahead, heedless of thy cry.\n"
    "\n"
    "From among the rocks the persecutors fall upon him, and he is overcome. His zeal had no root.\n"
    "\n"
    "The young believer hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The young believer turneth to thee with tears in his eyes. 'I would have perished in my haste. But let patience have her perfect work, that ye may be perfect and entire, wanting nothing. Thou hast taught me patience, and now my faith hath taken root. I thank thee, friend.'",
    "The mother clutcheth her child and trembleth. 'They will take my child! I cannot go on, I must turn back!'",
    "The darkness closeth about the mother, and her heart melteth for fear.\n"
    "\n"
    "She turneth and fleeth down the mountain with her child, and the persecutors pursue her.\n"
    "\n"
    "The mother hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The mother lifteth her child toward the light. 'The LORD is my light and my salvation; whom shall I fear? Thou didst not leave us in the darkness. God bless thee, friend.'",
]


def c_text(src):
    parts = []

    def take(match):
        parts.append(bytes(match.group(1), "utf-8").decode("unicode_escape"))
        return ""

    re.sub(r'"((?:\\.|[^"\\])*)"', take, src)
    return "".join(parts)


def map_rows():
    start = LUA.index("[[\n") + 3
    block = LUA[start:LUA.index("\n]]")]
    rows = block.split("\n")
    assert rows and all(len(r) == len(rows[0]) for r in rows)
    return rows


def walkable(rows):
    cells = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in " L":
                cells.add((x, y))
    return cells


def reaches(walk, blocked, start, goal):
    if start in blocked or start not in walk:
        return False
    q = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if nxt in walk and nxt not in seen and nxt not in blocked:
                seen.add(nxt)
                q.append(nxt)
    return False


def cells_of(name):
    """Pull a C coord array named sg_<name> as map coordinates."""
    body = SRC.split("sg_%s[]" % name, 1)[1].split("};", 1)[0]
    pairs = re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", body)
    return {(int(x), int(y)) for x, y in pairs}


class Text(unittest.TestCase):
    def test_locked_lines(self):
        seen = c_text(SRC)
        for line in LOCKED:
            self.assertIn(line, seen)

    def test_no_em_dash(self):
        self.assertNotIn("\u2014", SRC)
        self.assertNotIn("\u2014", LUA)


class Cuts(unittest.TestCase):
    def test_triggers_block_the_summit(self):
        rows = map_rows()
        walk = walkable(rows)
        start = (0, 19)
        summit = (20, 2)
        self.assertTrue(reaches(walk, set(), start, summit))
        sets = {
            "ss": cells_of("ss"),
            "w": cells_of("w"),
            "x": cells_of("x"),
            "b0": cells_of("b0"),
            "b1": cells_of("b1"),
            "b2": cells_of("b2"),
            "b3": cells_of("b3"),
        }
        for name, cells in sets.items():
            self.assertTrue(cells, name)
            self.assertTrue(cells <= walk, name)
            self.assertFalse(reaches(walk, cells, start, summit), name)

    def test_camp_is_not_a_spawn_row(self):
        self.assertIn("y >= 10 && y <= 14", SRC)
        self.assertIn("PM_PERSECUTOR", SRC)
        # The camp bowl is those rows. The spring and the travelers sit there.
        self.assertIn('name = "young believer", x = 42, y = 11', LUA)
        self.assertIn('name = "old man", x = 48, y = 11', LUA)
        self.assertIn('name = "mother", x = 54, y = 11', LUA)
        self.assertIn('x = 48, y = 13', LUA)


class Rules(unittest.TestCase):
    def test_son_of_perdition_is_blocked(self):
        self.assertIn("PM_WIZARD_OF_YENDOR] && trial_bars_son()", MAKEMON)
        self.assertIn("mtmp->iswiz && trial_bars_son()", DOG)

    def test_reset_restores_chest_and_travelers(self):
        reset = SRC.split("apply_reset", 1)[1].split("stony_setup", 1)[0]
        self.assertIn("place_traveler(SG_YOUNG", reset)
        self.assertIn("place_traveler(SG_OLD", reset)
        self.assertIn("place_traveler(SG_MOTH", reset)
        self.assertIn("restock_chest()", reset)
        self.assertIn("clear_persecutors()", reset)
        self.assertIn("u_on_newpos(START_X, START_Y)", reset)
        self.assertIn("pull_into(chest, u.ustony.oid[0]", SRC)
        self.assertIn("pull_into(chest, u.ustony.oid[2]", SRC)

    def test_bones_and_spring_and_gate(self):
        self.assertIn('find_level("stony")', BONES)
        self.assertIn("if (stony_here())", HINNOM)
        self.assertIn('find_level("stony")', WAYSIDE)
        self.assertIn("up = stony->dlevel", WAYSIDE)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
