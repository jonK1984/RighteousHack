#!/usr/bin/env python3
"""Source checks for the Wayside gate dissipation. No message."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WAYSIDE = (ROOT / "src" / "wayside.c").read_text()


def body_of(name, until):
    return WAYSIDE.split(name, 1)[1].split(until, 1)[0]


class Gate(unittest.TestCase):
    def test_only_the_last_answer_plays_it(self):
        ask = body_of("ask_riddle(struct monst *mtmp)", "wayside_chat")
        self.assertIn("confirm_answer(which);", ask)
        self.assertLess(ask.index("confirm_answer(which);"),
                        ask.index("dissipate_gate()"))
        self.assertIn("if (trial_done())", ask)
        setup = body_of("wayside_setup(void)", "floor_ok")
        tick = body_of("wayside_tick(void)", "wayside_take_up")
        self.assertIn("open_gate();", setup)
        self.assertIn("open_gate();", tick)
        self.assertNotIn("dissipate_gate", setup)
        self.assertNotIn("dissipate_gate", tick)
        self.assertEqual(WAYSIDE.count("dissipate_gate()"), 1)

    def test_the_burst_matches_the_reference(self):
        burst = WAYSIDE.split("gate_can_play(void)", 1)[1].split(
            "forget_stair", 1)[0]
        self.assertNotIn("pline(", burst)
        self.assertIn("tty", burst)
        self.assertIn("curses", burst)
        self.assertIn("iflags.wc_tiled_map", burst)
        self.assertIn("rn2_on_display_rng", burst)
        self.assertNotIn("rn2(", burst.replace("rn2_on_display_rng", ""))
        self.assertIn("flags.nap", burst)
        self.assertIn("gg.gbuf", burst)
        self.assertIn("for (frame = 0; frame < 10; frame++)", burst)
        self.assertIn("for (frame = 0; frame < 9; frame++)", burst)
        self.assertIn("GATE_X - 1", burst)
        self.assertIn("GATE_X + 1", burst)
        for ch in ("'#', '*', '+'", "'*'", "'+'", "'.'"):
            self.assertIn(ch, burst)
        for color in ("CLR_BRIGHT_CYAN", "CLR_BRIGHT_BLUE", "CLR_CYAN",
                      "CLR_WHITE", "CLR_BLUE", "CLR_GRAY"):
            self.assertIn(color, burst)
        self.assertIn("frame == 3", burst)
        self.assertIn("open_gate();", burst)
        self.assertLess(burst.index("frame < 10"), burst.index("frame < 9"))
        self.assertLess(burst.index("frame == 3"),
                        burst.index("fade_ch[step]"))
        self.assertIn("typ == ROOM || typ == CORR", burst)
        self.assertNotIn("\u2014", burst)


if __name__ == "__main__":
    unittest.main()
