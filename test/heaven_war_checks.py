#!/usr/bin/env python3
"""The war and the two altars on the Plane of Heaven.

Lucifer is not a new monster kind. That would lengthen the saved
mvitals list. EDITLEVEL stays 20.
"""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


class HeavenWar(unittest.TestCase):
    def test_save_layout_is_unchanged(self):
        monsters = read("include/monsters.h")
        self.assertNotIn('NAM("Lucifer', monsters)
        self.assertNotIn('NAM("Fallen Angel', monsters)
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))
        self.assertIn("STRAT_LUCIFER", read("include/monst.h"))
        self.assertIn("perdition_forever()", read("include/monst.h"))
        self.assertIn("petra_step |= 1", read("src/wizard.c"))
        self.assertIn("if (perdition_forever())", read("src/wizard.c"))
        self.assertIn("!perdition_forever()", read("src/allmain.c"))

    def test_the_two_altars_and_the_chest_table(self):
        heaven = read("src/heaven.c")
        lua = read("dat/astral.lua")
        self.assertIn("des.heaven_temples()", lua)
        self.assertNotIn('align=align[', lua)
        self.assertIn("AM_LAWFUL", heaven)
        self.assertIn("AM_NONE", heaven)
        self.assertIn("AM_SANCTUM", heaven)
        self.assertIn("HEAVEN_DRAW 8", heaven)
        self.assertIn("{ WAN_WISHING, 1, 1 }", heaven)
        self.assertIn("!rn2(5)", heaven)
        for gift in (
            "SILVER_DRAGON_SCALE_MAIL",
            "CRYSTAL_PLATE_MAIL",
            "SPEED_BOOTS",
            "GAUNTLETS_OF_POWER",
            "SHIELD_OF_REFLECTION",
            "CLOAK_OF_MAGIC_RESISTANCE",
            "HELM_OF_BRILLIANCE",
            "RIN_PROTECTION",
            "RIN_INCREASE_ACCURACY",
            "RIN_INCREASE_DAMAGE",
            "AMULET_OF_LIFE_SAVING",
            "WAN_DEATH",
            "SCR_CHARGING",
            "MAGIC_MARKER",
        ):
            self.assertIn(gift, heaven)
        self.assertIn("sx[3] = { 7, 37, 67 }", heaven)
        self.assertIn("sy[3] = { 9, 5, 9 }", heaven)

    def test_the_offering(self):
        pray = read("src/pray.c")
        soul = pray.split("otmp->otyp == PLAYER_SOUL", 1)[1].split(
            "AMULET_OF_YENDOR", 1)[0]
        self.assertLess(pray.index("heaven_dragon_end()"),
                        pray.index("otmp->otyp == PLAYER_SOUL"))
        self.assertIn("altaralign == A_NONE", pray)
        self.assertIn("Is_astralevel(&u.uz) && altaralign == A_LAWFUL", soul)
        self.assertIn("!cap_of_salvation_worn()", soul)
        self.assertLess(soul.index("!cap_of_salvation_worn()"),
                        soul.index("useup(otmp)"))
        self.assertIn(
            "Nothing happens. Without the helmet of salvation, thou canst not offer thy soul.",
            pray)
        self.assertIn(
            "Darkness covereth thee. Thou hast offered unto the Great Dragon, and the light of the Lord is gone out from thee.",
            read("src/heaven.c"))
        self.assertIn('Strcpy(svk.killer.name, "offered unto the Great Dragon")',
                      read("src/heaven.c"))
        for line in (
            "Nothing happens. Without the helmet of salvation, thou canst not offer thy soul.",
            "Darkness covereth thee. Thou hast offered unto the Great Dragon, and the light of the Lord is gone out from thee.",
            "The tail of the Great Dragon sweepeth, and striketh thee.",
            "The dragon casteth out of his mouth water as a flood.",
            "The accuser of the brethren speaketh against thee, and thy prayer is put off.",
            "The accuser of the brethren speaketh against thee, and thy fortune faileth.",
            "The Great Dragon calleth, and a fallen angel answereth.",
            "Lucifer is cast down. He shall not rise for a little season.",
            "Lucifer is risen again, and the war in heaven is not ended.",
            "Lucifer casteth off the likeness of an angel of light.",
            "At thy prayer, Lucifer and the Son of Perdition are holden still.",
            "The Son of Perdition is cast down, and shall rise up no more.",
            "Here stand the high altar of the Lord and the high altar of the Great Dragon.",
        ):
            self.assertNotIn("\u2014", line)

    def test_lucifer_and_the_angels(self):
        heaven = read("src/heaven.c")
        self.assertIn("LUCIFER_HP 250", heaven)
        self.assertIn("LUCIFER_WAIT 15", heaven)
        self.assertIn("blanket_keeps_seat()", heaven)
        self.assertLess(heaven.index("blanket_keeps_seat()"),
                        heaven.index("dismount_steed(DISMOUNT_THROWN)"))
        self.assertIn("mfrozen = 15", heaven)
        self.assertIn("Fallen Angel of the Great Dragon", read("src/priest.c"))
        self.assertIn("Angel of the Lord", read("src/priest.c"))
        self.assertIn("STRAT_HEAVEN_FALLEN", heaven)
        self.assertIn("STRAT_HEAVEN_LORD", heaven)
        self.assertIn("PM_WIZARD_OF_YENDOR", heaven)
        display = read("src/display.c")
        self.assertIn("MG_INVERSE", display)
        self.assertIn("glyphinfo->ttychar = 'D'", display)
        self.assertIn("0x03A8", display)
        self.assertIn("0xCE, 0xA8", display)
        self.assertIn("CLR_RED", display)
        self.assertIn("SYMHANDLING(H_UTF8)", display)


if __name__ == "__main__":
    unittest.main()
