#!/usr/bin/env python3
"""Both hosts on the Plane of Heaven. No new monster kind."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


class HeavenHost(unittest.TestCase):
    def test_save_layout_stays(self):
        monsters = read("include/monsters.h")
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))
        for name in ("Cherub", "Seraph", "Gabriel", "Raphael", "Uriel"):
            self.assertNotIn('NAM("%s' % name, monsters)
            self.assertNotIn("NAMS(\"%s" % name, monsters)
        bits = read("include/monst.h")
        for bit in ("STRAT_HEAVEN_CHERUB", "STRAT_HEAVEN_SERAPH",
                    "STRAT_HEAVEN_ARCH", "STRAT_HEAVEN_PRIEST"):
            self.assertIn(bit, bits)
        self.assertIn("petra_step & 2", bits)

    def test_the_level_drops_the_stock_host(self):
        lua = read("dat/astral.lua")
        self.assertNotIn('id = "Angel"', lua)
        self.assertNotIn('id="Angel"', lua)
        self.assertNotIn("aligned cleric", lua)
        self.assertIn('id = "Death"', lua)
        self.assertIn('id = "Pestilence"', lua)
        self.assertIn('id = "Famine"', lua)
        self.assertIn('class = "L"', lua)
        self.assertIn('class = "V"', lua)
        self.assertIn('class = "D"', lua)
        self.assertIn("des.heaven_host()", lua)
        self.assertIn("lspo_heaven_host", read("src/sp_lev.c"))

    def test_the_cast_and_the_blackout(self):
        heaven = read("src/heaven.c")
        self.assertIn("PM_KI_RIN", heaven)
        self.assertIn("PM_ARCHON", heaven)
        self.assertIn("PM_ANGEL", heaven)
        self.assertIn("PM_ALIGNED_CLERIC", heaven)
        self.assertIn("lords < 3", heaven)
        self.assertIn("fallen < 3", heaven)
        self.assertIn("priestxy[12]", heaven)
        self.assertIn("n < 2", heaven)
        self.assertIn('{ "Michael", 30, 220 }', heaven)
        self.assertIn('{ "Gabriel", 24, 160 }', heaven)
        self.assertIn('{ "Raphael", 24, 160 }', heaven)
        self.assertIn('{ "Uriel", 24, 160 }', heaven)
        self.assertIn("heaven_host_arrived()", heaven)
        self.assertIn("petra_step |= 2", heaven)
        verse = (
            "And there was war in heaven: Michael and his angels "
            "fought against the dragon; and the dragon fought and "
            "his angels."
        )
        self.assertIn('\\"' + verse + '\\"', heaven)
        self.assertIn("PLACEHOLDER", heaven)
        self.assertNotIn("\u2014", verse)
        self.assertIn("if (!endcut_testing)", heaven)
        self.assertNotIn("priestini(", heaven)

    def test_names_and_the_sword(self):
        naming = read("src/do_name.c")
        arm = naming.split("is_heaven_arch(mtmp)", 1)[1].split(
            "else if (do_name && has_mgivenname(mtmp))", 1)[0]
        self.assertIn("MGIVENNAME(mtmp)", arm)
        self.assertIn('Strcat(buf, "cherub")', arm)
        self.assertIn('Strcat(buf, "seraph")', arm)
        self.assertNotIn("called %s", arm)
        priest = read("src/priest.c")
        self.assertIn("priestess", priest)
        self.assertIn(" of the Great Dragon", priest)
        attack = read("src/mhitu.c")
        sword = attack.split("is_heaven_cherub(magr)", 1)[1].split(
            "is_heaven_seraph(magr)", 1)[0]
        self.assertIn("AT_WEAP", sword)
        self.assertIn("AD_FIRE", sword)
        self.assertIn("alt_attk_buf->adtyp = AD_FIRE", attack)
        smite = read("src/endcut.c").split("endcut_smite(", 1)[1].split(
            "for (i = 1;", 1)[0]
        self.assertIn("heaven_lords_host(mtmp)", smite)
        display = read("src/display.c")
        self.assertIn("CLR_BRIGHT_BLUE", display)
        self.assertIn("CLR_YELLOW", display)
        self.assertIn("CLR_WHITE", display)
        self.assertIn("CLR_RED", display)
        self.assertIn("CLR_GRAY", display)


if __name__ == "__main__":
    unittest.main()
