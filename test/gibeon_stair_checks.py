#!/usr/bin/env python3
"""The Prophet level has one stair up into the Cave of Gibeon."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


class GibeonStairTests(unittest.TestCase):
    def test_oracle_skips_the_generic_branch_stair(self):
        src = read("src/mkmaze.c")
        self.assertNotIn(
            "Oracle already places one branch (Sokoban is the next level down).",
            src)
        note = src.split("gibeon_stair_ok(coordxy x, coordxy y)", 1)[0]
        note = note.rsplit("/*", 1)[1]
        self.assertIn("base 0", note)
        self.assertIn("base 1", note)
        self.assertIn("only one", note)
        fix = src.split("fixup_special(void)", 1)[1]
        fix = fix.split("Is_medusa_level", 1)[0]
        gate = fix.split("place_lregion(0, 0, 0, 0, 0, 0, 0, 0, LR_BRANCH", 1)[0]
        self.assertIn("!Is_oracle_level(&u.uz)", gate)
        self.assertIn("!added_branch && Is_branchlev(&u.uz)", gate)
        self.assertIn("if (Is_oracle_level(&u.uz))\n        place_gibeon_stair();",
                      fix)
        placed = src.split("place_gibeon_at(branch *br, coordxy x, coordxy y)", 1)[1]
        placed = placed.split("place_gibeon_stair(void)", 1)[0]
        self.assertIn("stairway_add(x, y, br->end1_up, FALSE, &br->end2)", placed)

    def test_no_other_oracle_branch_placement(self):
        prophet = read("dat/prophet.lua")
        self.assertNotIn('type = "branch"', prophet)
        self.assertNotIn("type=\"branch\"", prophet)
        sp = read("src/sp_lev.c")
        self.assertNotIn("place_branch(", sp)
        mklev = read("src/mklev.c")
        make = mklev.split("makelevel(void)\n{", 1)[1]
        make = make.split("water_has_kelp(coordxy x", 1)[0]
        special = make.split("if (slev && !Is_rogue_level(&u.uz))", 1)[1]
        special = special.split("} else if", 1)[0]
        self.assertNotIn("place_branch(", special)
        regular = make.split('it\'s a "regular" level.', 1)[1]
        self.assertIn("place_branch(branchp, 0, 0)", regular)
        maze = read("src/mkmaze.c")
        fallback = maze.split("if (load_special(protofile))", 1)[1]
        fallback = fallback.split("populate_maze", 1)[0]
        self.assertLess(fallback.index("return;"), fallback.index("place_branch("))
        arrive = read("src/do.c").split("} else if (at_stairs", 1)[1]
        arrive = arrive.split("You(\"fall down the", 1)[0]
        self.assertEqual(arrive.count("stairway_find_from(&u.uz0, ga.at_ladder)"), 2)


if __name__ == "__main__":
    unittest.main()
