#!/usr/bin/env python3
"""A hero attack on Peter draws one rebuke per turn."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINE = (
    'A voice cometh out of the clouds, saying, "Touch not mine anointed, '
    'and do my prophets no harm."'
)


def shown(src):
    return src.replace('\\"', '"')


class PeterRebukeTests(unittest.TestCase):
    def test_once_per_turn(self):
        mon = shown((ROOT / "src/mon.c").read_text())
        body = mon.split("peter_hero_rebuke(void)", 1)[1]
        body = body.split("mondead(", 1)[0]
        self.assertIn(LINE, body)
        self.assertLess(body.find("svm.moves"), body.find("pline("))
        self.assertIn('losehp(5, "rebuked by the LORD", KILLED_BY)', body)
        self.assertIn("%s is unharmed.", (ROOT / "src/uhitm.c").read_text())
        wait = (ROOT / "src/monmove.c").read_text().split("is_peter(mtmp)", 1)[1]
        wait = wait.split("is_sodom_dweller", 1)[0]
        self.assertNotIn("peter_hero_rebuke", wait)
        self.assertIn("peter_hero_rebuke()", (ROOT / "src/uhitm.c").read_text())
        self.assertIn("peter_hero_rebuke()", (ROOT / "src/zap.c").read_text())


if __name__ == "__main__":
    unittest.main()
