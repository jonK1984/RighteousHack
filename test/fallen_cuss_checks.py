#!/usr/bin/env python3
"""Fallen angels do not speak the faithful angel lines."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

LINES = (
    '"Ye shall not surely die."',
    '"I will ascend above the heights of the clouds; I will be like the most High."',
    '"Fall down before the Dragon, and rise up a king."',
    '"What profit hath thy faithfulness brought thee? Kneel, and know true power."',
    '"We have beheld His face, and we chose otherwise."',
    '"Why serve when thou mightest reign?"',
    '"We kept not our first estate, and we repent not of it."',
    '"The Dragon hath promised us thrones. What hath thy Lord promised thee?"',
    '"Thou art but dust, and unto dust thou shalt return. We are flame."',
    '"We were cast down once. We shall not be cast down again."',
)


def lua_strings(block):
    out = []
    i = 0
    while i < len(block):
        if block[i] != '"':
            i += 1
            continue
        i += 1
        chars = []
        while i < len(block):
            if block[i] == "\\":
                nxt = block[i + 1] if i + 1 < len(block) else ""
                chars.append(nxt)
                i += 2
                continue
            if block[i] == '"':
                i += 1
                break
            chars.append(block[i])
            i += 1
        out.append("".join(chars))
    return out


class FallenCuss(unittest.TestCase):
    def test_the_fallen_lines_are_verbatim(self):
        quest = (ROOT / "dat" / "quest.lua").read_text()
        block = quest.split("fallen_angel_cuss = {", 1)[1].split(
            "michael_speech = {", 1)[0]
        spoken = [s for s in lua_strings(block) if s.startswith('"')]
        self.assertEqual(spoken, list(LINES))
        for line in spoken:
            self.assertNotIn("\u2014", line)
        faithful = quest.split("angel_cuss = {", 1)[1].split(
            "fallen_angel_cuss", 1)[0]
        self.assertIn(
            "the gift of God is eternal life through Christ Jesus our Lord.",
            faithful)
        self.assertNotIn("enternal", faithful)
        self.assertNotIn("fallen_angel_cuss", faithful)

    def test_the_callers_choose_the_fallen_set(self):
        wizard = (ROOT / "src" / "wizard.c").read_text()
        cuss = wizard.split("cuss(struct monst *mtmp)", 1)[1].split(
            "/*wizard.c*/", 1)[0]
        self.assertLess(cuss.index('com_pager("fallen_angel_cuss")'),
                        cuss.index('com_pager("angel_cuss")'))
        self.assertIn("speaks_as_fallen(mtmp)", cuss)
        sounds = (ROOT / "src" / "sounds.c").read_text()
        chat = sounds.split("case MS_CUSS:", 1)[1].split(
            "case MS_SPELL:", 1)[0]
        self.assertIn("speaks_as_fallen(mtmp)", chat)
        self.assertLess(chat.index("speaks_as_fallen(mtmp)"),
                        chat.index('"It\'s not too late."'))
        head = (ROOT / "include" / "monst.h").read_text()
        self.assertIn("is_heaven_fallen(mon)", head)
        self.assertIn("EMIN(mon)->renegade", head)


if __name__ == "__main__":
    unittest.main()
