#!/usr/bin/env python3
"""Custom strategy bits do not share a bit with each other or with stock."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

STOCK = {
    "STRAT_GOAL": 0x000000FF,
    "STRAT_PLAYER": 0x01000000,
    "STRAT_MONSTR": 0x02000000,
    "STRAT_GROUND": 0x04000000,
    "STRAT_HEAL": 0x08000000,
    "STRAT_CLOSE": 0x10000000,
    "STRAT_WAITFORU": 0x20000000,
    "STRAT_ARRIVE": 0x40000000,
    "STRAT_APPEARMSG": 0x80000000,
}

# Bits 8 through 19. Moloch's counter is the two high ones.
CUSTOM = {
    "STRAT_HINNOM_RELEASED": 0x00000100,
    "STRAT_HINNOM_THRONE": 0x00000200,
    "STRAT_LUCIFER": 0x00000400,
    "STRAT_LUCIFER_WAIT": 0x00000800,
    "STRAT_HEAVEN_LORD": 0x00001000,
    "STRAT_HEAVEN_FALLEN": 0x00002000,
    "STRAT_HEAVEN_CHERUB": 0x00004000,
    "STRAT_HEAVEN_SERAPH": 0x00008000,
    "STRAT_HEAVEN_ARCH": 0x00010000,
    "STRAT_HEAVEN_PRIEST": 0x00020000,
    "MOLOCH_HIT_MASK": 0x000C0000,
}


def defines(text):
    found = {}
    for name, value in re.findall(
            r"#define\s+([A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+)", text):
        found[name] = int(value, 16)
    return found


def fix_strategy(is_dragon, is_moloch, strat):
    """Same move as rh_fix_strategy."""
    old = 0x00000C00
    new = 0x000C0000
    if not is_dragon and (strat & (0x400 | 0x800)):
        if is_moloch:
            hits = (strat & old) >> 10
            strat &= ~old
            strat = (strat & ~new) | (hits << 18)
        else:
            strat &= ~(0x400 | 0x800)
    if not is_moloch:
        strat &= ~new
    return strat


class StrategyBits(unittest.TestCase):
    def test_the_map_does_not_overlap(self):
        text = (ROOT / "include" / "monst.h").read_text()
        got = defines(text)
        for name, value in STOCK.items():
            self.assertEqual(got[name], value, name)
        for name, value in CUSTOM.items():
            self.assertEqual(got[name], value, name)
        self.assertEqual(got["MOLOCH_HIT_OLD_MASK"], 0x00000C00)
        used = 0
        for value in list(STOCK.values()) + list(CUSTOM.values()):
            self.assertEqual(used & value, 0, hex(value))
            used |= value
        self.assertNotIn("#define MOLOCH_HIT_MASK",
                         (ROOT / "src" / "hinnom.c").read_text())
        self.assertIn("rh_strat_bits_overlap", text)
        self.assertIn("#define EDITLEVEL 20",
                      (ROOT / "include" / "patchlevel.h").read_text())

    def test_two_blows_do_not_make_moloch_lucifer(self):
        # The old counter stored 2 in bits 10-11, which is Lucifer's wait bit.
        two = 2 << 10
        self.assertEqual(two & 0x800, 0x800)
        fixed = fix_strategy(False, True, two)
        self.assertEqual(fixed & (0x400 | 0x800), 0)
        self.assertEqual((fixed & 0x000C0000) >> 18, 2)
        one = fix_strategy(False, True, 1 << 10)
        self.assertEqual((one & 0x000C0000) >> 18, 1)
        self.assertEqual(one & 0x400, 0)
        # A real Lucifer keeps his bit. A bystander loses a stray one.
        self.assertEqual(fix_strategy(True, False, 0x400), 0x400)
        self.assertEqual(fix_strategy(False, False, 0x400 | 0x800), 0)

    def test_the_guards_and_the_restore(self):
        head = (ROOT / "include" / "monst.h").read_text()
        restore = (ROOT / "src" / "restore.c").read_text()
        wizard = (ROOT / "src" / "wizard.c").read_text()
        self.assertIn("data == &mons[PM_RED_DRAGON]", head)
        self.assertIn("PM_KI_RIN", head)
        self.assertIn("PM_ARCHON", head)
        self.assertIn("PM_ALIGNED_CLERIC", head)
        self.assertIn("PM_ANGEL", head)
        self.assertIn("rh_fix_strategy(mtmp)", restore)
        self.assertIn("MOLOCH_HIT_OLD_MASK", restore)
        self.assertIn("STRAT_RH_KEEP", wizard)


if __name__ == "__main__":
    unittest.main()
