#!/usr/bin/env python3
"""Static checks for the Thorns trial. These do not boot NetHack."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
THORNS = (ROOT / "src" / "thorns.c").read_text()
LUA = (ROOT / "dat" / "thorns.lua").read_text()
END = (ROOT / "src" / "end.c").read_text()
DO = (ROOT / "src" / "do.c").read_text()
HACK = (ROOT / "src" / "hack.c").read_text()
PATCH = (ROOT / "include" / "patchlevel.h").read_text()

LINES = [
    "Come, weary one, and drink. Fifteen hundred pieces of gold for the asking, and the cup never runneth dry in this city.",
    "The scales are balanced in thy favor today, friend. Three thousand gold, weighed out freely. What could it cost thee?",
    "Thou art clothed in rags of iron and blood. Take five thousand gold and walk in purple and fine linen, as a man of worth.",
    "I have gathered the tribute of a hundred cities. Eight thousand pieces of it are thine. Render unto thyself, for once.",
    "Cast the lot! Whatever gold thou bearest, I shall double it. Fortune smileth on the bold, and thou art very bold.",
    "Everything thou carriest is worth more than thou knowest. I shall pay five times its price, and ask no questions.",
    "Ten times the worth of thy goods, paid in pure gold. Did not Aaron's calf shine fairer than any stone tablet?",
    "Pearls of great price, thou sayest? I shall pay twenty times it. Sell what thou hast, and be rich indeed.",
    "Sit, eat, and be merry! Take this horn, and thou shalt never hunger again. Tomorrow is a long way off.",
    "Thy wounds are many. Here is balm enough to make thee whole three times over. Why suffer, when healing is so near?",
    "This verse of judgement was copied by my own hand. Speak it, and the wicked shall be cut off from the earth. Such power, and so light to carry.",
    "Wear this, and death itself shall pass thee by. Is there any treasure greater than a life that cannot end?",
    "Silver, sharpened and blessed, that no foul thing can abide. Take it, warrior. Thy enemies will tremble.",
    "The scales of a silver dragon, forged to turn every blow. Thou shalt walk through fire and ray unharmed.",
    "Step into the waters, and thy strength shall be renewed. Twenty measures of life, poured into thy bones.",
    "A knight should never ride to battle unarmed! Behold this lance, true and rustproof. Couch it, and charge.",
    "All these things will I give thee. Name thy desire, and it shall be done. One word, and the world is thine.",
]

SIGNS = [
    "The Overflowing Cup",
    "The Golden Scales",
    "Purple and Fine Linen",
    "The Receipt of Custom",
    "The Lot and the Lucky Throw",
    "Nothing Ventured",
    "The Gilded Calf",
    "Pearls of Great Price",
    "Eat, Drink, and Be Merry",
    "Balm of Gilead",
    "The Book of the Living",
    "The Neverending Hour",
    "The Sharpened Edge",
    "Scales of the Dragon",
    "The Fountain of Youth",
    "The Lance and Pennant",
    "The House of All Desires",
]

DRAIN = "Thorns spring up around thee and tighten. Thou feelest life drain from thee."
DEATH = "The thorns close over thy heart. Thou art choked by the cares of this world."
REASON = "Choked by the thorns of this world."


def map_lines():
    body = LUA.split("map = [[", 1)[1].split("]]", 1)[0]
    return [line for line in body.splitlines() if line]


class Text(unittest.TestCase):
    def test_every_approved_line_is_verbatim(self):
        for line in LINES:
            self.assertIn(line, THORNS)
        self.assertIn(DRAIN, THORNS)
        self.assertIn(DEATH, THORNS)
        self.assertIn(REASON, THORNS)
        for sign in SIGNS:
            self.assertIn(sign, LUA)
        self.assertEqual(LUA.count("The House of All Desires"), 2)
        self.assertNotIn("\u2014", THORNS + LUA)

    def test_flagged_wording(self):
        self.assertIn("I have already given thee my gift.", THORNS)
        self.assertIn("Wilt thou accept this gift?", THORNS)
        self.assertIn("What wilt thou sell?", THORNS)
        self.assertIn("Wilt thou sell another?", THORNS)
        self.assertIn("Thou canst not bring thyself to strike", THORNS)


class Rules(unittest.TestCase):
    def test_fourth_thorn_is_not_life_saved(self):
        body = END.split("thorns_fatal()", 1)[1].split("explore and wizard", 1)[0]
        self.assertLess(END.index("thorns_fatal()"), END.index("if (Lifesaved"))
        self.assertIn("amulet of life saving", body)
        self.assertIn("Die?", END[END.index("thorns_fatal()"):])

    def test_only_the_up_stair_finishes_the_trial(self):
        note = THORNS.split("thorns_note_ascent(void)", 1)[1].split(
            "strike_whom", 1)[0]
        self.assertIn("u.uthorns.done = 1", note)
        up = DO.split("doup(void)", 1)[1].split("currentlevel_rewrite", 1)[0]
        down = DO.split("dodown(void)", 1)[1].split("doup(void)", 1)[0]
        self.assertIn("thorns_note_ascent()", up)
        self.assertNotIn("thorns_note_ascent()", down)

    def test_the_drain_cannot_kill(self):
        body = THORNS.split("drain_life(int n)", 1)[1].split("grant_life", 1)[0]
        self.assertIn("if (umax < 1)", body)
        self.assertIn("if (ucur < 1)", body)
        self.assertIn("u.mhmax", body)
        self.assertIn("u.uhpmax", body)
        chat = THORNS.split("thorns_chat(", 1)[1]
        self.assertLess(chat.index("grant(def)"), chat.index("drain_life"))
        self.assertLess(chat.index("drain_life"), chat.index(DRAIN))
        self.assertLess(chat.index("accepts >= 3"), chat.index("grant(def)"))

    def test_the_dungeon_table_can_hold_the_thorns(self):
        cap = 0
        for line in (ROOT / "include" / "global.h").read_text().splitlines():
            if line.startswith("#define MAXDUNGEON "):
                cap = int(line.split()[2])
        # init_dungeons panics when the lua array length is >= MAXDUNGEON.
        n = sum(1 for line in (ROOT / "dat" / "dungeon.lua").read_text().splitlines()
                if line == "   {")
        self.assertGreaterEqual(n, 16)
        self.assertGreater(cap, n)

    def test_the_overview_names_the_gilded_city(self):
        dgn = (ROOT / "src" / "dungeon.c").read_text()
        seen = dgn.split("print_mapseen(", 1)[1]
        self.assertIn('"%sA Gilded City."', seen)
        self.assertIn("find_level(\"thorns\")", seen)
        self.assertIn("OF_INTEREST(mptr->feat) && !gilded_city", seen)
        self.assertLess(seen.index("!gilded_city"),
                        seen.index('"%sA Gilded City."'))

    def test_editlevel_and_save_struct(self):
        you = (ROOT / "include" / "you.h").read_text()
        self.assertIn("The Thorns, the third trial. EDITLEVEL 18.", you)
        self.assertIn("#define EDITLEVEL", PATCH)
        self.assertIn("} uthorns;", you)
        self.assertIn("unsigned id[17]", you)
        self.assertIn("xint16 host[4]", you)

    def test_verses_are_not_wilderness_only(self):
        body = HACK.split("wilderness_check(void)", 1)[1].split(
            "pride_touch_mirror", 1)[0]
        self.assertIn("show_verse();", body)
        early = body.split("if (!in_wilderness())", 1)[1].split(
            "dunlev(&u.uz) == 4", 1)[0]
        self.assertIn("show_verse();", early)


class Map(unittest.TestCase):
    def test_city_geometry(self):
        rows = map_lines()
        self.assertEqual(len(rows), 21)
        self.assertTrue(all(len(row) == 75 for row in rows))
        self.assertEqual(rows[1][37], "<")
        self.assertEqual(rows[19][37], ">")
        # F and G were placeholders. Those cells are floor.
        self.assertEqual(rows[10][20], ".")
        self.assertEqual(rows[10][54], ".")
        # Door on the south of the knight's tent.
        self.assertEqual(rows[12][54], "+")
        self.assertNotIn("{", rows[10][51:57])
        self.assertNotIn("{", rows[11][51:57])
        for ch in "123456789ABCDEFGP":
            for row in rows:
                self.assertNotIn(ch, row)
        self.assertIn('des.stair("up", 37, 1)', LUA)
        self.assertIn('des.stair("down", 37, 19)', LUA)
        self.assertIn("premapped", LUA)
        self.assertIn('name = "The Prince of the city"', LUA)
        self.assertIn('name = "Knight-errant armsman"', LUA)


if __name__ == "__main__":
    unittest.main()
