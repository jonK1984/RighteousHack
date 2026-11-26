#!/usr/bin/env python3
"""The Road seals every level change once it has begun."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DO = (ROOT / "src" / "do.c").read_text()
HACK = (ROOT / "src" / "hack.c").read_text()
TRAP = (ROOT / "src" / "trap.c").read_text()
DIG = (ROOT / "src" / "dig.c").read_text()
POTION = (ROOT / "src" / "potion.c").read_text()
WIZ = (ROOT / "src" / "wizcmds.c").read_text()
YOU = (ROOT / "include" / "you.h").read_text()
GG = (ROOT / "src" / "goodground.c").read_text()


def body(src, start, end):
    return src.split(start, 1)[1].split(end, 1)[0]


class RoadExit(unittest.TestCase):
    def test_the_three_refusal_lines_are_unchanged(self):
        refused = body(HACK, "sanctum_ascent_refused(void)", "road_set_wizport")
        self.assertIn(
            "The stairs will not receive you. You cannot walk the road while leaving your soul behind.",
            refused)
        self.assertIn(
            "A voice whispers: Put on the helmet of salvation. You cannot face what lies ahead with your mind unguarded.",
            refused)
        self.assertIn(
            "A voice whispers: You come empty handed and bare headed. Recover your soul and put on the helmet of salvation.",
            refused)
        bars = body(HACK, "road_bars_leave(", "box_holds_soul")
        self.assertIn("wayside_road()", bars)
        self.assertIn("sanctum_ascent_open()", bars)
        self.assertIn("sanctum_ascent_refused()", bars)
        self.assertIn("dest->dlevel <= 0", bars)
        self.assertNotIn("\u2014", HACK)

    def test_every_departure_calls_the_guard(self):
        goto = body(DO, "goto_level(", "wildhome =")
        self.assertLess(goto.index("road_bars_leave(newlevel)"),
                        goto.index("wayside_begin();") if "wayside_begin();" in goto
                        else goto.index("wilderness_sealed"))
        self.assertIn("UTOTYPE_WIZPORT", goto)
        sched = body(DO, "schedule_goto(", "deferred_goto(void)")
        self.assertIn("road_bars_leave(tolev)", sched)
        self.assertIn("UTOTYPE_WIZPORT", sched)
        self.assertLess(sched.index("road_bars_leave(tolev)"),
                        sched.index("assign_level(&u.utolev"))
        doup = body(DO, "doup(void)", "currentlevel_rewrite")
        self.assertIn("road_bars_leave((d_level *) 0)", doup)
        self.assertIn("!u.uz.dnum && u.uz.dlevel == 1", doup)
        dodown = body(DO, "dodown(void)", "doup(void)")
        self.assertIn("road_bars_leave((d_level *) 0)", dodown)
        fall = body(TRAP, "fall_through(", "animate_statue")
        self.assertLess(fall.index("road_bars_leave((d_level *) 0)"),
                        fall.index("schedule_goto"))
        self.assertLess(fall.index('dont_fall = "don\'t fall in."'),
                        fall.index("road_bars_leave((d_level *) 0)"))
        self.assertIn("road_bars_leave(&newlevel)", DIG)
        self.assertLess(DIG.index("if (road_bars_leave(&newlevel))"),
                        DIG.index('You("fall through...")'))
        gain = body(POTION, "peffect_gain_level(struct obj *otmp)",
                    "peffect_healing(struct obj *otmp)")
        self.assertLess(gain.index("road_bars_leave(&newlevel)"),
                        gain.index("goto_level(&newlevel"))
        wiz = body(WIZ, "wiz_level_tele(void)", "wiz_flip_level")
        self.assertIn("road_set_wizport(TRUE)", wiz)
        self.assertLess(wiz.index("road_set_wizport(TRUE)"),
                        wiz.index("level_tele()"))
        self.assertLess(wiz.index("level_tele()"),
                        wiz.index("road_set_wizport(FALSE)"))
        self.assertIn("UTOTYPE_WIZPORT", YOU)

    def test_the_dungeon_top_keeps_its_own_leaving(self):
        climb = GG.split("salvation_climb(", 1)[1]
        self.assertIn("wayside_screen(leave_ready)", climb)
        self.assertIn("salvation_ready()", climb)
        self.assertIn("devoured by the hordes of darkness", GG)
        self.assertIn("strayed from the straight and narrow path", GG)
        prev = (ROOT / "src" / "dungeon.c").read_text()
        self.assertIn("salvation_climb(stway)", prev)


if __name__ == "__main__":
    unittest.main()
