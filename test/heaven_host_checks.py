#!/usr/bin/env python3
"""Both hosts on the Plane of Heaven. No new monster kind."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def c_text(src, marker):
    """Join the C string literals that follow marker, honouring \\n and \\"."""
    body = src.split(marker, 1)[1]
    out = []
    i = 0
    in_lit = False
    while i < len(body):
        c = body[i]
        if not in_lit:
            if c == ";":
                break
            if c == '"':
                in_lit = True
            i += 1
            continue
        if c == "\\":
            n = body[i + 1]
            out.append("\n" if n == "n" else n)
            i += 2
            continue
        if c == '"':
            in_lit = False
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


ARCHANGEL_TEXT = (
    '"And there was war in heaven: Michael and his angels fought against '
    'the dragon; and the dragon fought and his angels."\n'
    "\n"
    "In the midst of the battle the heavens are rent asunder, and the sound "
    "of a trumpet pierceth the air. Four mighty archangels descend upon the "
    "field of war, clothed in white and girded with gold, their armour "
    "shining as the sun and their swords as flames of fire.\n"
    "\n"
    "Michael, the great captain of the host, set over the best of mankind "
    "and over chaos.\n"
    "Gabriel, set over Paradise, and over the serpents, and over the "
    "Cherubim.\n"
    "Raphael, set over the spirits of men.\n"
    "Uriel, set over the world and over Tartarus.\n"
    "\n"
    "Where they set their feet the host of the Great Dragon trembleth, for "
    "they are come to execute the righteous judgment of the Lord upon all "
    "that wage war against heaven."
)


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
        self.assertIn('{ "Michael", 45, 240 }', heaven)
        self.assertIn('{ "Gabriel", 24, 160 }', heaven)
        self.assertIn('{ "Raphael", 24, 160 }', heaven)
        self.assertIn('{ "Uriel", 24, 160 }', heaven)
        self.assertIn("heaven_host_arrived()", heaven)
        self.assertIn("petra_step |= 2", heaven)
        shown = c_text(heaven, "heaven_host_text[]")
        self.assertEqual(shown, ARCHANGEL_TEXT)
        self.assertNotIn("PLACEHOLDER", heaven)
        self.assertNotIn("\u2014", shown)
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
        spared = read("src/endcut.c").split("endcut_hostiles(", 1)[1].split(
            "endcut_kill_from", 1)[0]
        self.assertIn("heaven_lords_host(mtmp)", spared)
        display = read("src/display.c")
        self.assertIn("CLR_BRIGHT_BLUE", display)
        self.assertIn("CLR_YELLOW", display)
        self.assertIn("CLR_WHITE", display)
        self.assertIn("CLR_RED", display)
        self.assertIn("CLR_GRAY", display)


if __name__ == "__main__":
    unittest.main()
