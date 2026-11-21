#!/usr/bin/env python3
"""The Sanctum soul lies on the altar, and the high priestess starts at peace."""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HACK = (ROOT / "src" / "hack.c").read_text()
PRIEST = (ROOT / "src" / "priest.c").read_text()
PICKUP = (ROOT / "src" / "pickup.c").read_text()
KICK = (ROOT / "src" / "dokick.c").read_text()
ZAP = (ROOT / "src" / "zap.c").read_text()

REVEAL = (
    "You peer inside, and horror grips you. There, bound in chains within "
    "the Sanctum of the Great Dragon, is your own soul. At last it all makes sense."
)
CONFESS = (
    "Dost thou confess with thy mouth the Lord Jesus, and believe in thine "
    "heart that God hath raised him from the dead?"
)
WELCOME = (
    "Welcome, we have long awaited thee. Look thou within the chest, "
    "and receive thy reward."
)


class AltarSoul(unittest.TestCase):
    def test_soul_is_placed_on_the_altar_without_a_chest(self):
        body = HACK.split("place_altar_soul", 1)[1].split("spawn_hosts", 1)[0]
        self.assertIn("mksobj(PLAYER_SOUL, FALSE, FALSE)", body)
        self.assertIn("place_object(soul, ax, ay)", body)
        self.assertNotIn("mksobj_at(CHEST", body)
        self.assertNotIn("A chest sits on the altar.", HACK)
        # A leftover chest is emptied onto the altar and removed.
        self.assertIn("box_holds_soul(obj)", body)
        self.assertIn("obfree(obj, (struct obj *) 0)", body)

    def test_locked_reveal_and_welcome_remain(self):
        self.assertIn(REVEAL, HACK)
        self.assertIn(CONFESS, HACK)
        self.assertIn(WELCOME, PRIEST)

    def test_priestess_starts_peaceful(self):
        ini = PRIEST.split("priestini(", 1)[1].split("mon_aligntyp", 1)[0]
        self.assertIn("if (sanctum)", ini)
        self.assertIn("priest->female = 1", ini)
        self.assertIn("priest->mpeaceful = 1", ini)

    def test_taking_the_soul_uses_the_ordinary_anger_path(self):
        disturb = HACK.split("sanctum_disturb_soul", 1)[1].split(
            "pacify_sanctum_priest", 1)[0]
        self.assertIn("soul_on_sanctum_altar(obj)", disturb)
        self.assertIn("setmangry(priest, FALSE)", disturb)
        self.assertIn("sanctum_reveal()", disturb)
        self.assertIn("svc.context.mon_moving", disturb)
        self.assertIn("sanctum_disturb_soul(obj)", PICKUP)
        self.assertIn("sanctum_disturb_soul(gk.kickedobj)", KICK)
        self.assertIn("sanctum_disturb_soul(obj)", ZAP)
        self.assertIn("sanctum_disturb_soul(otmp)", HACK)
        # No new anger sentence. The existing setmangry line is the one.
        self.assertNotIn("gets angry", disturb)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
