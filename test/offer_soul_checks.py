#!/usr/bin/env python3
"""#offer must be able to choose the soul."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EAT = (ROOT / "src" / "eat.c").read_text()


def between(src, start, end):
    return src.split(start, 1)[1].split(end, 1)[0]


class OfferSoul(unittest.TestCase):
    def test_offer_ok_accepts_the_soul(self):
        body = between(EAT, "offer_ok(struct obj *obj)", "tin_ok(")
        soul = body.split("obj->otyp == PLAYER_SOUL", 1)[1]
        klass = body.index("obj->oclass != FOOD_CLASS")
        self.assertLess(body.index("obj->otyp == PLAYER_SOUL"), klass)
        self.assertIn("Is_astralevel(&u.uz) ? GETOBJ_SUGGEST", soul)
        self.assertIn("GETOBJ_DOWNPLAY", soul)
        self.assertNotIn("\u2014", "Is_astralevel(&u.uz) ? GETOBJ_SUGGEST")

    def test_floorfood_offers_a_soul_on_the_square(self):
        body = between(EAT, "floorfood(", "vomit(")
        floor = body.split("svl.level.objects[u.ux][u.uy]", 1)[1]
        self.assertLess(floor.index("offering && otmp->otyp == PLAYER_SOUL"),
                        floor.index("otmp->otyp == CORPSE"))
        guard = body.split("if (otmp && corpsecheck", 1)[1]
        self.assertIn("otmp->otyp == PLAYER_SOUL", guard.split("{", 1)[0])

    def test_the_prompt_asks_what_to_offer(self):
        invent = (ROOT / "src" / "invent.c").read_text()
        self.assertEqual(invent.count('"What do you wish to offer?"'), 2)
        self.assertIn('getobj("sacrifice", offer_ok, GETOBJ_NOFLAGS)', EAT)
        self.assertNotIn("\u2014", "What do you wish to offer?")


if __name__ == "__main__":
    unittest.main()
