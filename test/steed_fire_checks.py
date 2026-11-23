#!/usr/bin/env python3
"""Source checks for the Fiery Steed's ring of holy fire."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIRE = (ROOT / "src" / "steedfire.c").read_text()
CHAT = (ROOT / "src" / "sounds.c").read_text()
YOU = (ROOT / "include" / "you.h").read_text()
PATCH = (ROOT / "include" / "patchlevel.h").read_text()

PROMPT = "Bid thy steed loose its fire?"
BURST = "Thy steed breatheth forth a ring of holy fire!"
COOL = "Thy steed's fire is not yet rekindled."
READY = "Thou feelest the fire rekindle within thy steed."


class Text(unittest.TestCase):
    def test_the_approved_lines(self):
        for line in (PROMPT, BURST, COOL, READY):
            self.assertIn(line, FIRE)
        self.assertNotIn("\u2014", FIRE)
        self.assertIn('y_n("Bid thy steed loose its fire?")', FIRE)

    def test_self_chat_is_the_trigger(self):
        body = CHAT.split("u.dx == 0 && u.dy == 0", 1)[1].split(
            "Talking to yourself", 1)[0]
        self.assertIn("steed_loose_fire()", body)
        self.assertLess(body.index("steed_loose_fire()"),
                        body.index("fired < 0"))


class Rules(unittest.TestCase):
    def test_damage_cooldown_and_who_is_spared(self):
        scorch = FIRE.split("scorch_one(", 1)[1].split("loose_the_fire", 1)[0]
        self.assertIn("d(6, 6)", scorch)
        self.assertIn("resists_fire(mtmp)", scorch)
        self.assertIn("shieldeff(mtmp->mx, mtmp->my)", scorch)
        self.assertIn("destroy_items(mtmp, AD_FIRE, blast)", scorch)
        ring = FIRE.split("loose_the_fire(void)", 1)[1].split(
            "steed_loose_fire", 1)[0]
        self.assertIn("mtmp->mtame || mtmp->mpeaceful", ring)
        self.assertLess(ring.index("mtmp->mtame"), ring.index("scorch_one"))
        self.assertIn("burn_floor_objects", ring)
        self.assertIn("EXPL_FIERY", FIRE)
        self.assertIn("CLR_YELLOW", FIRE)
        self.assertIn("CLR_ORANGE", FIRE)
        self.assertIn("CLR_RED", FIRE)
        # Knockback follows the resist check and is not inside it.
        self.assertIn("mhurtle(hit[i], dxs[i], dys[i], 1)", ring)
        self.assertGreater(ring.index("mhurtle("), ring.index("scorch_one"))
        self.assertNotIn("mhurtle", scorch)
        self.assertIn("u.ufirewait = 300 + rnd(100)", FIRE)
        tick = FIRE.split("steed_fire_tick(void)", 1)[1]
        self.assertIn(READY, tick)
        self.assertIn("--u.ufirewait == 0", tick)

    def test_the_wait_is_saved(self):
        self.assertIn("#define EDITLEVEL 19", PATCH)
        self.assertIn("int ufirewait;", YOU)
        self.assertIn("steed_fire_tick();",
                      (ROOT / "src" / "allmain.c").read_text())


if __name__ == "__main__":
    unittest.main()
