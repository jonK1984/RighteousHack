#!/usr/bin/env python3
"""Each archangel speaks his own lines."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

SETS = {
    "michael_speech": (
        '"Take thy place beside me, and let the dragon see that the Lord\'s host lacketh not for warriors."',
        '"Stand fast, soldier of the Lord. The dragon\'s host breaketh upon us as the sea upon the rock."',
        '"I cast him down once from these courts. By the Lord\'s hand I shall cast him down again."',
        '"Who is like unto God? Not the dragon, nor any of his host."',
    ),
    "gabriel_speech": (
        '"I am Gabriel, that stand in the presence of God."',
        '"For with God nothing shall be impossible."',
        '"I have borne good tidings to the lowly. Now I bear the sword against the serpent."',
        '"Fear not. The trumpet that hath sounded this day shall sound again at the last."',
    ),
    "raphael_speech": (
        '"I am but a servant of the Most High. Give thanks unto Him, for He hath kept thee unto this hour."',
        '"Thy wounds are seen, mortal. Endure, for healing cometh in the morning."',
        '"Many have fallen on the road thou hast walked. Thou art still standing, and that is the Lord\'s doing."',
        '"Be of good courage, mortal. No wound the dragon giveth can reach the soul the Lord hath kept."',
        '"Thy soul was bought at a great price. Let not the dragon steal it back."',
    ),
    "uriel_speech": (
        '"I have kept the deep and the chains thereof. There is room yet in Tartarus for the dragon\'s host."',
        '"I watched over thee in the world below. Now behold the war thou wast made for."',
        '"The light of God shineth here, and no darkness may hide from it."',
        '"Lift thine eyes, mortal. The end of thy road is at hand."',
    ),
}


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


class ArchangelSpeech(unittest.TestCase):
    def test_each_set_is_verbatim(self):
        quest = (ROOT / "dat" / "quest.lua").read_text()
        for key, lines in SETS.items():
            block = quest.split(key + " = {", 1)[1].split("},", 1)[0]
            spoken = [s for s in lua_strings(block) if s.startswith('"')]
            self.assertEqual(spoken, list(lines), key)
            for line in spoken:
                self.assertNotIn("\u2014", line, key)

    def test_they_are_named_archangels_and_the_callers_use_them(self):
        heaven = (ROOT / "src" / "heaven.c").read_text()
        speech = heaven.split("archangel_speech(struct monst *mtmp)", 1)[1]
        self.assertIn("is_heaven_arch(mtmp)", speech)
        self.assertIn("has_mgivenname(mtmp)", speech)
        for name, key in (
            ("Michael", "michael_speech"),
            ("Gabriel", "gabriel_speech"),
            ("Raphael", "raphael_speech"),
            ("Uriel", "uriel_speech"),
        ):
            self.assertIn('"%s"' % name, heaven)
            self.assertIn('return "%s"' % key, speech)
        self.assertIn("STRAT_HEAVEN_ARCH", heaven)
        self.assertIn("MGIVENNAME(mtmp)", (ROOT / "src" / "save.c").read_text())
        wizard = (ROOT / "src" / "wizard.c").read_text()
        cuss = wizard.split("cuss(struct monst *mtmp)", 1)[1]
        self.assertLess(cuss.index("archangel_speech(mtmp)"),
                        cuss.index('com_pager("angel_cuss")'))
        self.assertLess(cuss.index("archangel_speech(mtmp)"),
                        cuss.index('com_pager("fallen_angel_cuss")'))
        sounds = (ROOT / "src" / "sounds.c").read_text()
        chat = sounds.split("case MS_CUSS:", 1)[1].split(
            "case MS_SPELL:", 1)[0]
        self.assertLess(chat.index("archangel_speech(mtmp)"),
                        chat.index('"It\'s not too late."'))


if __name__ == "__main__":
    unittest.main()
