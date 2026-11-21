#!/usr/bin/env python3
"""Static checks for the Son of Perdition batch.

These do not boot NetHack. They pin the locked sentences and the
rules that decide theft, the pull down, the key, and the gate word.
"""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WAYSIDE = (ROOT / "src" / "wayside.c").read_text()
DO = (ROOT / "src" / "do.c").read_text()
STEAL = (ROOT / "src" / "steal.c").read_text()
WIZARD = (ROOT / "src" / "wizard.c").read_text()
HINNOM_C = (ROOT / "src" / "hinnom.c").read_text()
HINNOM = (ROOT / "dat" / "hinnom.lua").read_text()
BERACHAH = (ROOT / "dat" / "berachah.lua").read_text()
WIZ1 = (ROOT / "dat" / "wizard1.lua").read_text()
MONSTERS = (ROOT / "include" / "monsters.h").read_text()
ZAP = (ROOT / "src" / "zap.c").read_text()
MON = (ROOT / "src" / "mon.c").read_text()

DONE = (
    "Thou hast heard, and thou hast understood.\n"
    "\n"
    "A great stillness falleth upon the Wayside, and from the northeast "
    "thou hearest a gate swing wide upon its hinges.\n"
    "\n"
    "Go forth, for the road to salvation continueth before thee."
)
SOUL = (
    "Thou hast cast off the helmet of thy salvation, and the Son of "
    "Perdition hath seized upon thy soul!\n"
    "\n"
    "He fleeth with it into the darkness, laughing.\n"
    "\n"
    "Make haste and pursue him, for what shall a man give in exchange "
    "for his soul?"
)
PULL = (
    "The spirit indeed is willing, but the flesh is weak. Behold, the "
    "tempter draweth thee backward, and thou losest the ground thou "
    "hadst gained."
)
def joined_c_strings(src):
    """Turn adjacent C string literals into the text the player sees."""
    parts = []

    def take(match):
        parts.append(bytes(match.group(1), "utf-8").decode("unicode_escape"))
        return ""

    re.sub(r'"((?:\\.|[^"\\])*)"', take, src)
    return "".join(parts)


ARTS = (
    "ART_SHOES_GOSPEL_OF_PEACE",
    "ART_PLATE_OF_RIGHTEOUSNESS",
    "ART_BELT_OF_TRUTH",
    "ART_HELMET_OF_SALVATION",
    "ART_SHIELD_OF_FAITH",
    "ART_SWORD_OF_THE_SPIRIT",
)


class Text(unittest.TestCase):
    def test_sixth_answer_blackout_follows_the_count(self):
        seen = joined_c_strings(WAYSIDE)
        self.assertIn(DONE, seen)
        confirm = WAYSIDE.split("confirm_answer", 1)[1].split(
            "wayside_sanctum_key_dropped", 1)[0]
        self.assertIn('pline("%s", line);', confirm)
        self.assertLess(confirm.index('pline("%s", line);'),
                        confirm.index("Thou hast heard, and thou hast understood."))
        self.assertIn('if (riddles_left() == 0)', confirm)
        self.assertIn('Sprintf(buf, "(%d riddles remain.)", left);', WAYSIDE)

    def test_soul_theft_blackout(self):
        self.assertEqual(joined_c_strings(STEAL).count(SOUL), 2)

    def test_pull_down_sentence(self):
        self.assertIn(PULL, joined_c_strings(DO))
        self.assertNotIn(
            "A mysterious force momentarily surrounds you...", DO)


class Gate(unittest.TestCase):
    def test_onward_gate_is_northeast_of_the_map_center(self):
        """Map column 0 is level x 1. The gate cell is map (70, 6).

        The drawn map is 79 columns by 21 rows. Its center is about
        (39, 10). Row numbers grow south, so a smaller row is north.
        """
        self.assertRegex(WAYSIDE, r"#define GATE_X WX\(70\)")
        self.assertRegex(WAYSIDE, r"#define GATE_Y 6")
        lua = (ROOT / "dat" / "wayside.lua").read_text()
        start = lua.index("map = [[") + len("map = [[")
        block = lua[start:].split("]]", 1)[0]
        map_rows = [line for line in block.splitlines() if line]
        self.assertGreaterEqual(len(map_rows), 21)
        width = len(map_rows[0])
        height = len(map_rows)
        for row in map_rows:
            self.assertEqual(len(row), width)
        # Map column 70, row 6. Center of a 79 by 21 map is (39, 10).
        gx, gy = 70, 6
        cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
        self.assertEqual(width, 79)
        self.assertEqual(height, 21)
        self.assertGreater(gx, cx)
        self.assertLess(gy, cy)
        self.assertIn("northeast", DONE)


class Theft(unittest.TestCase):
    def test_armor_and_sword_are_barred_by_artifact_id(self):
        body = STEAL.split("obj_theft_barred", 1)[1].split("int\nsteal", 1)[0]
        for art in ARTS:
            self.assertIn(art, body)
        self.assertIn("otmp->otyp == PLAYER_SOUL", body)
        self.assertIn("mtmp->iswiz && !cap_of_salvation_worn()", body)

    def test_only_he_may_take_the_soul_and_he_prefers_it(self):
        amulet = STEAL.split("stealamulet", 1)[1]
        self.assertIn(
            "if (mtmp->iswiz && !cap_of_salvation_worn())\n"
            "        otmp = carried_player_soul();",
            amulet)
        self.assertIn("obj_theft_barred", STEAL)
        self.assertIn("obj_theft_barred", MON)
        self.assertIn("obj_theft_barred",
                      (ROOT / "src" / "uhitm.c").read_text())
        self.assertIn("obj_theft_barred",
                      (ROOT / "src" / "dogmove.c").read_text())
        # He keeps a stolen soul across a level change. Death still drops it.
        special = STEAL.split("mdrop_special_objs", 1)[1]
        self.assertIn("obj->otyp == PLAYER_SOUL && mon->iswiz", special)
        resists = ZAP.split("obj_resists(struct obj *obj,", 1)[1][:500]
        self.assertIn("PLAYER_SOUL", resists)
        self.assertIn("KEY_TO_SANCTUM", resists)


class KeyAndAltar(unittest.TestCase):
    def test_old_key_sources_are_gone(self):
        self.assertNotIn('des.object("Key to the Sanctum")', HINNOM)
        self.assertNotIn('des.object("Key to the Sanctum")', BERACHAH)

    def test_key_drops_once_inside_his_tower(self):
        self.assertIn('des.monster({ id = "Son of Perdition"', WIZ1)
        self.assertNotIn("Wizard of Yendor", WIZ1)
        fn = WIZARD.split("perdition_leave_sanctum_key", 1)[1]
        self.assertIn("wayside_sanctum_key_dropped()", fn)
        self.assertIn("On_W_tower_level(&u.uz)", fn)
        self.assertIn("In_W_tower(x, y, &u.uz)", fn)
        self.assertIn("mksobj(KEY_TO_SANCTUM", fn)
        self.assertIn("wayside_mark_sanctum_key()", fn)
        self.assertIn("perdition_leave_sanctum_key(mtmp, mx, my)", MON)
        self.assertIn("#define WS_SKEY", WAYSIDE)

    def test_razing_the_altar_is_the_way_down(self):
        clamp = HINNOM_C.split("hinnom_dest_clamp", 1)[1].split(
            "hinnom_begin_swap", 1)[0]
        self.assertIn("!u.uevent.hinnom_razed", clamp)
        self.assertNotIn("PM_MOLOCH].died", clamp)
        self.assertIn(
            "The way down stays shut while the altar of evil stands.",
            clamp)


class Pull(unittest.TestCase):
    def test_soul_uses_the_amulet_odds(self):
        block = DO.split("carried_player_soul() && !newdungeon", 1)[0]
        # The condition itself is the trigger. The odds sit just after it.
        after = DO.split("carried_player_soul() && !newdungeon", 1)[1][:1600]
        self.assertIn("Inhell && up && carried_player_soul()", DO)
        self.assertIn("!rn2(4 + svc.context.mysteryforce)", after)
        self.assertIn("dunlev(&u.uz) < dunlevs_in_dungeon(&u.uz) - 3", DO)
        self.assertIn(PULL, joined_c_strings(after))
        self.assertNotIn("u.uhave.amulet && !newdungeon && !portal", block[-400:])


class Name(unittest.TestCase):
    def test_player_facing_name_and_bright_red(self):
        self.assertIn('NAM("Son of Perdition")', MONSTERS)
        self.assertNotIn('NAM("Wizard of Yendor")', MONSTERS)
        self.assertIn("CLR_ORANGE, WIZARD_OF_YENDOR", MONSTERS)
        self.assertIn("MG_INVERSE", (ROOT / "include" / "display.h").read_text())
        tty = (ROOT / "win" / "tty" / "wintty.c").read_text()
        curses = (ROOT / "win" / "curses" / "cursmain.c").read_text()
        self.assertIn("MG_INVERSE", tty)
        self.assertIn("MG_INVERSE", curses)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
