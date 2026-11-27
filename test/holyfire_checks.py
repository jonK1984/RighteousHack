#!/usr/bin/env python3
"""Altar light and Lucifer destroyed follow the mockup clock."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The approved mockup clock. Played delays are seven tenths of these,
# rounded to the nearest millisecond (halves round up).
MOCK_ALTAR = [
    400, 300,
    130, 130, 130,
    95, 95, 95, 95, 95, 95, 95,
    250, 900,
]
MOCK_STRIKE = [110, 110, 70]
MOCK_LUCIFER = [
    450, 250,
    90,
    90, 140,
    105, 105, 105, 105, 105, 105, 105, 105, 105, 105,
    70, 70, 70, 70, 70, 70, 70, 90,
    95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95,
    110, 110,
    120, 90, 80, 80,
    350, 900,
]


def scale_ms(ms):
    return int(ms * 0.7 + 0.5)


def read(rel):
    return (ROOT / rel).read_text()


def c_ints(src, name):
    body = src.split(name, 1)[1]
    body = body.split("{", 1)[1].split("}", 1)[0]
    return [int(n) for n in re.findall(r"\d+", body)]


class HolyFire(unittest.TestCase):
    def test_timing_lists_match_the_mockup(self):
        src = read("src/endcut.c")
        altar = c_ints(src, "endcut_altar_ms[]")
        strike = c_ints(src, "endcut_strike_ms[]")
        lucifer = c_ints(src, "endcut_lucifer_ms[]")
        self.assertEqual(altar, [scale_ms(n) for n in MOCK_ALTAR])
        self.assertEqual(strike, [scale_ms(n) for n in MOCK_STRIKE])
        self.assertEqual(lucifer, [scale_ms(n) for n in MOCK_LUCIFER])
        self.assertEqual(strike, [77, 77, 49])
        # Nine strikes is the mockup's own count. The scene strikes every
        # hostile, so the played time grows by one strike per extra enemy.
        self.assertEqual(sum(altar), 2037)
        self.assertEqual(sum(strike), 203)
        self.assertEqual(sum(altar) + 9 * sum(strike), 3864)
        self.assertEqual(sum(lucifer), 4019)
        self.assertEqual(len(lucifer), 44)

    def test_exact_wait_is_used_for_these_sequences(self):
        src = read("src/endcut.c")
        wait = src.split("endcut_wait_ms(int ms)", 1)[1]
        wait = wait.split("\nint\nrh_text_cols", 1)[0]
        self.assertIn("nanosleep", wait)
        self.assertIn("Delay(", wait)
        self.assertNotIn("nh_delay_output", wait)
        altar = src.split("endcut_altar_scene(boolean harm)", 1)[1].split(
            "endcut_stamp_lucifer", 1)[0]
        lucifer = src.split("endcut_lucifer_at(coordxy x", 1)[1].split(
            "endcut_win_map", 1)[0]
        self.assertIn("endcut_wait_ms(endcut_altar_ms[", altar)
        self.assertIn("endcut_wait_ms(endcut_strike_ms[", altar)
        self.assertNotIn("endcut_wait(", altar)
        self.assertIn("endcut_wait_ms(endcut_lucifer_ms[", lucifer)
        self.assertNotIn("endcut_wait(", lucifer)

    def test_every_hostile_is_struck(self):
        src = read("src/endcut.c")
        host = src.split("endcut_hostiles(coordxy ax", 1)[1].split(
            "endcut_kill_from", 1)[0]
        self.assertNotIn("256", host)
        self.assertIn("is_lucifer(mtmp)", host)
        self.assertIn("heaven_lords_host(mtmp)", host)
        self.assertIn("mtmp->mpeaceful", host)
        self.assertIn("mtmp->mtame", host)
        scene = src.split("endcut_altar_scene(boolean harm)", 1)[1].split(
            "endcut_stamp_lucifer", 1)[0]
        self.assertIn("endcut_hostiles(ax, ay, &n)", scene)
        self.assertIn("for (i = 0; i < n; i++)", scene)
        self.assertIn("endcut_beam(ax, ay, x, y)", scene)
        self.assertIn("endcut_flash_mon(list[i])", scene)
        self.assertIn("endcut_sparks(x, y)", scene)
        self.assertIn("endcut_ov_put(1, x, y, '%'", scene)
        self.assertEqual(scene.count("endcut_wait_ms(endcut_strike_ms["), 3)

    def test_sprite_is_centered_and_clipped(self):
        src = read("src/endcut.c")
        self.assertIn("18 by 11", src)
        place = src.split("endcut_at_lucifer(int lx", 1)[1].split(
            "endcut_redraw_map", 1)[0]
        self.assertIn("MOCK_LUC_X", place)
        self.assertIn("MOCK_LUC_Y", place)
        self.assertIn("cell_y < MOCK_LUC_Y", place)
        self.assertIn("if (!isok(x, y))", place)
        self.assertIn("return FALSE", place)
        stamp = src.split("endcut_stamp_lucifer(coordxy lx", 1)[1].split(
            "endcut_wash", 1)[0]
        self.assertIn("endcut_at_lucifer", stamp)

    def test_overlays_are_not_wiped_by_docrt(self):
        src = read("src/endcut.c")
        compose = src.split("endcut_compose(int shx", 1)[1].split(
            "endcut_restore_burst", 1)[0]
        self.assertNotIn("docrt()", compose)
        self.assertIn("flush_screen(0)", src)
        altar = src.split("endcut_altar_scene(boolean harm)", 1)[1].split(
            "endcut_stamp_lucifer", 1)[0]
        lucifer = src.split("endcut_lucifer_at(coordxy x", 1)[1].split(
            "endcut_win_map", 1)[0]
        self.assertIn("endcut_reveal()", altar)
        self.assertIn("endcut_show();", altar[-120:])
        self.assertIn("endcut_reveal()", lucifer)
        self.assertIn("endcut_show();", lucifer)


if __name__ == "__main__":
    unittest.main()
