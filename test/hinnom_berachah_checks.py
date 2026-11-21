#!/usr/bin/env python3
"""Berachah children stay off the doors, the fiery steed is orange,
and the Hinnom field breaks on the real bar ring."""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BERACHAH = (ROOT / "dat" / "berachah.lua").read_text()
HINNOM_LUA = (ROOT / "dat" / "hinnom.lua").read_text()
HINNOM = (ROOT / "src" / "hinnom.c").read_text()
MONSTERS = (ROOT / "include" / "monsters.h").read_text()

FIELD_LINE = (
    "The air shudders. With a sound like a great sheet of glass shattering, "
    "the unholy field around the fortress flickers, cracks, and vanishes."
)


def map_lines(src):
    raw = src[src.index("[[") + 2:src.index("]]")].strip("\n")
    return raw.split("\n")


def flood_room(lines, doors, start):
    walls = set("-|")
    height, width = len(lines), len(lines[0])
    seen = set()
    stack = [start]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or (x, y) in doors:
            continue
        if not (0 <= x < width and 0 <= y < height):
            continue
        if lines[y][x] in walls:
            continue
        seen.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return seen


class BerachahChildren(unittest.TestCase):
    def test_no_child_stands_on_or_beside_a_door(self):
        lines = map_lines(BERACHAH)
        doors = {
            (int(x), int(y))
            for _, x, y in re.findall(
                r'des\.door\("(\w+)",\s*(\d+),\s*(\d+)\)', BERACHAH)
        }
        children = [
            (int(x), int(y))
            for x, y in re.findall(
                r'id = "child", x = (\d+), y = (\d+)', BERACHAH)
        ]
        self.assertEqual(len(children), 6)
        self.assertEqual(len(set(children)), 6)
        for cx, cy in children:
            self.assertNotIn((cx, cy), doors, (cx, cy))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.assertNotIn((cx + dx, cy + dy), doors, (cx, cy))
            self.assertEqual(lines[cy][cx], ".")
        throne = flood_room(lines, doors, (69, 10))
        for child in children:
            self.assertIn(child, throne, child)


class FierySteed(unittest.TestCase):
    def test_color_is_orange(self):
        body = MONSTERS.split(
            'NAM("fiery steed of the Heavenly Host")', 1)[1].split(
                "FIERY_STEED_OF_HEAVEN", 1)[0]
        self.assertIn("CLR_ORANGE", body)
        self.assertNotIn("CLR_WHITE", body)


class HinnomField(unittest.TestCase):
    def test_burst_uses_the_real_bars_before_the_locked_text(self):
        down = HINNOM.split("hinnom_field_down", 1)[1].split(
            "hinnom_pull_lever", 1)[0]
        self.assertLess(down.index("hinnom_field_burst()"),
                        down.index(FIELD_LINE))
        self.assertLess(down.index("docrt()"), down.index(FIELD_LINE))
        burst = HINNOM.split("field_can_play", 1)[1].split(
            "hinnom_field_down", 1)[0]
        layer = HINNOM.split("field_layer", 1)[1].split(
            "field_outward", 1)[0]
        self.assertIn("levl[x][y].typ != IRONBARS", burst)
        self.assertIn("outside > 1", layer)
        self.assertIn("inside > 1", layer)
        self.assertIn("nh_delay_output()", burst)
        self.assertIn("rn2_on_display_rng(", burst)
        self.assertNotIn("rn2(", burst)
        self.assertNotIn("pline(", burst)
        self.assertIn('!strcmp(port, "tty")', HINNOM)
        self.assertIn('!strcmp(port, "curses")', HINNOM)
        self.assertIn("flags.nap = save_nap", burst)
        self.assertNotIn("\u2014", burst)

    def test_map_bars_are_the_fortress_rectangle(self):
        lines = map_lines(HINNOM_LUA)
        bars = [(x, y) for y, line in enumerate(lines)
                for x, ch in enumerate(line) if ch == "F"]
        xs = [x for x, _ in bars]
        ys = [y for _, y in bars]
        self.assertEqual((min(xs), max(xs), min(ys), max(ys)), (41, 77, 1, 19))
        self.assertGreater(len(bars), 100)


MOLOCH_FALL = (
    "The voice of Michael the archangel soundeth across the valley like a trumpet.",
    "'Moloch is fallen! The abomination of the children of Ammon is cast down, and his fire shall devour the innocent no more.",
    "Make haste! Throw down his altar and break his image in pieces, that no man may make his son or his daughter to pass through the fire unto Moloch ever again. Raze it to the ground, for the LORD hath delivered this place into thine hand.'",
)


class MolochFallen(unittest.TestCase):
    def test_the_trumpet_is_exact_and_once(self):
        body = HINNOM.split("hinnom_moloch_died", 1)[1].split(
            "michael_briefing", 1)[0]
        for line in MOLOCH_FALL:
            self.assertIn(line, body)
        self.assertIn("u.uevent.hinnom_fallen", body)
        self.assertIn("Is_hinnom_level", body)
        mon = (ROOT / "src" / "mon.c").read_text()
        dead = mon.split("void\nmondead(", 1)[1].split("mvitals", 1)[0]
        self.assertIn("hinnom_moloch_died(mtmp)", dead)
        self.assertLess(dead.index("lifesaved_monster(mtmp)"),
                        dead.index("hinnom_moloch_died(mtmp)"))
        self.assertLess(dead.index("if (!DEADMONSTER(mtmp))"),
                        dead.index("hinnom_moloch_died(mtmp)"))
        you = (ROOT / "include" / "you.h").read_text()
        self.assertIn("Bitfield(hinnom_fallen, 1)", you)
        level = int(re.search(
            r"#define EDITLEVEL (\d+)",
            (ROOT / "include" / "patchlevel.h").read_text()).group(1))
        self.assertGreaterEqual(level, 15)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
