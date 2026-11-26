#!/usr/bin/env python3
"""A tame monster has an edog, except the guardian angel."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


class PetRecord(unittest.TestCase):
    def test_the_host_gets_a_pet_record(self):
        heaven = read("src/heaven.c")
        ally = heaven.split(
            "heaven_ally(struct monst *mtmp, unsigned extra)", 1)[1].split(
            "heaven_enemy(", 1)[0]
        self.assertIn("mtmp->mtame = max(mtmp->mtame, 10);", ally)
        self.assertIn("rh_attach_edog(mtmp);", ally)
        self.assertLess(ally.index("mtmp->mtame"), ally.index("rh_attach_edog"))
        self.assertIn("The guardian angel is already a tame minion", heaven)
        self.assertIn("mtmp->isminion || has_emin(mtmp)", heaven)
        self.assertIn("rh_attach_edog(mtmp);", heaven)
        dog = read("src/dog.c")
        attach = dog.split("rh_attach_edog(struct monst *mtmp)", 1)[1].split(
            "free_edog(", 1)[0]
        self.assertIn("mtmp->isminion", attach)
        self.assertIn("has_edog(mtmp)", attach)
        self.assertIn("newedog(mtmp)", attach)
        self.assertNotIn("uconduct.pets", attach)
        restore = read("src/restore.c")
        fix = restore.split("rh_fix_strategy(struct monst *mtmp)", 1)[1].split(
            "restmon(", 1)[0]
        self.assertIn("rh_fix_tame(mtmp);", fix)
        tame = dog.split("rh_fix_tame(struct monst *mtmp)", 1)[1].split(
            "rh_attach_edog(struct monst *mtmp)", 1)[0]
        self.assertIn("mtmp->isminion = 1", tame)
        self.assertIn("has_emin(mtmp)", tame)
        move = read("src/dogmove.c")
        self.assertLess(move.index("rh_fix_tame(mtmp);"),
                        move.index('impossible("dog_move for non-pet?")'))
        self.assertIn("!mtmp->isminion", move)
        # The stock guardian stays a minion and is not given an edog.
        minion = read("src/minion.c")
        guard = minion.split("gain_guardian_angel(", 1)[1].split(
            "/*minion.c*/", 1)[0]
        self.assertIn("mk_roamer(", guard)
        self.assertNotIn("rh_attach_edog", guard)
        self.assertIn("mtmp->isminion = 1;", guard)
        self.assertIn("isminion = 1", read("src/priest.c"))
        # A steed is a tame non-minion, so it needs the same pet record.
        self.assertIn("!mtmp->mtame || mtmp->isminion", read("src/steed.c"))
        self.assertIn("#define EDITLEVEL 20",
                      read("include/patchlevel.h"))


if __name__ == "__main__":
    unittest.main()
