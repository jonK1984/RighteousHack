#!/usr/bin/env python3
"""The Riding Blanket may keep the hero seated when an attack throws him."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STEED = (ROOT / "src" / "steed.c").read_text()
UHITM = (ROOT / "src" / "uhitm.c").read_text()
MHITU = (ROOT / "src" / "mhitu.c").read_text()
DOGMOVE = (ROOT / "src" / "dogmove.c").read_text()
EXTERN = (ROOT / "include" / "extern.h").read_text()
PATCH = (ROOT / "include" / "patchlevel.h").read_text()

HELD = "The blanket holdeth thee fast."

# These dismounts are not attacks. The helper must not be named here.
LEFT_ALONE = (
    "src/mon.c",       # steed dies or is genocided
    "src/polyself.c",  # hero polymorph
    "src/worn.c",      # saddle taken off, or the steed's shape
    "src/eat.c",       # hero mimics a pile of gold
    "src/bones.c",     # death
    "src/do.c",        # falling down stairs
    "src/hack.c",      # pool or lava
    "src/trap.c",      # traps, drowning, levitation
    "src/artifact.c",  # an untouchable saddle
    "src/timeout.c",   # fumbling
    "src/dog.c",       # a life-saved steed goes feral, or is left behind
)


def func_body(src, signature, end):
    return src.split(signature, 1)[1].split(end, 1)[0]


class BlanketSeat(unittest.TestCase):
    def test_one_helper_and_the_new_line(self):
        self.assertEqual(STEED.count("blanket_keeps_seat(void)"), 1)
        self.assertIn("extern boolean blanket_keeps_seat(void);", EXTERN)
        body = func_body(STEED, "blanket_keeps_seat(void)", "dismount_steed(")
        self.assertIn("which_armor(u.usteed, W_SADDLE)", body)
        self.assertIn("is_blanket_of_the_heavenly_host(saddle)", body)
        self.assertIn("if (!u.usteed)", body)
        self.assertLess(body.index("if (!u.usteed)"), body.index("which_armor"))
        self.assertIn("rn2(100) >= chance", body)
        self.assertIn(HELD, body)
        self.assertNotIn("\u2014", HELD)
        self.assertNotIn("\u2014", body)
        # The save line is after the roll, so a failed roll stays silent.
        self.assertLess(body.index("rn2(100)"), body.index(HELD))

    def test_the_riding_chances(self):
        body = func_body(STEED, "blanket_keeps_seat(void)", "dismount_steed(")
        self.assertIn("skill <= P_UNSKILLED", body)
        self.assertIn("chance = 10", body)
        self.assertIn("skill == P_BASIC", body)
        self.assertIn("chance = 25", body)
        self.assertIn("skill == P_SKILLED", body)
        self.assertIn("chance = 60", body)
        self.assertIn("chance = 98", body)
        # Restricted is below unskilled, so it shares the 10 percent.
        self.assertLess(body.index("P_UNSKILLED"), body.index("P_BASIC"))
        self.assertLess(body.index("P_BASIC"), body.index("P_SKILLED"))
        self.assertLess(body.index("chance = 60"), body.index("chance = 98"))
        self.assertIn("#define EDITLEVEL 20", PATCH)

    def test_attack_dismounts_ask_the_blanket(self):
        knock = func_body(UHITM, "boolean\nmhitm_knockback(", "hmonas(")
        self.assertLess(
            knock.index("dismount && blanket_keeps_seat()"),
            knock.index("dismount_steed(DISMOUNT_KNOCKED)"))
        # The "out of your saddle" line is the dismount that was refused.
        self.assertLess(
            knock.index("blanket_keeps_seat()"),
            knock.index("out of your saddle"))

        gulp = MHITU.split(
            "gulpmu(struct monst *mtmp, struct attack *mattk)", 1)[1]
        gulp = gulp.split("explmu(", 1)[0]
        self.assertLess(
            gulp.index("u.usteed && blanket_keeps_seat()"),
            gulp.index("dismount_steed(DISMOUNT_ENGULFED)"))
        self.assertLess(
            gulp.index("blanket_keeps_seat()"),
            gulp.index("place_monster(mtmp, u.ux, u.uy)"))

        conflict = func_body(DOGMOVE, "dog_move(", "newdogpos")
        self.assertIn("blanket_keeps_seat()", conflict)
        self.assertLess(
            conflict.index("blanket_keeps_seat()"),
            conflict.index("dismount_steed(DISMOUNT_THROWN)"))
        self.assertIn("Conflict && !resist_conflict(mtmp)", conflict)

        kick = func_body(STEED, "kick_steed(void)", "landing_spot(")
        untame, buck = kick.split("Still tame, but the kick makes it buck.", 1)
        self.assertNotIn("blanket_keeps_seat", untame)
        self.assertIn("dismount_steed(DISMOUNT_THROWN)", untame)
        self.assertIn("!u.usteed->mtame", untame)
        self.assertIn("blanket_keeps_seat()", buck)
        self.assertLess(
            buck.index("blanket_keeps_seat()"),
            buck.index("dismount_steed(DISMOUNT_THROWN)"))

    def test_other_dismounts_are_left_alone(self):
        for rel in LEFT_ALONE:
            text = (ROOT / rel).read_text()
            self.assertNotIn("blanket_keeps_seat", text, rel)
        ride = func_body(STEED, "doride(void)", "kick_steed(")
        self.assertIn("dismount_steed(DISMOUNT_BYCHOICE)", ride)
        self.assertNotIn("blanket_keeps_seat", ride)


if __name__ == "__main__":
    unittest.main()
