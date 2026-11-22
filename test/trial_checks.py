#!/usr/bin/env python3
"""Static checks for the Road's separate trial branches.

These do not boot NetHack. Host selection is the same rule the
game uses: ordinary Gehennom levels, an ordinary level between
every pair, drawn in a random order and stored on the hero.
"""

import pathlib
import random
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WAYSIDE = (ROOT / "src" / "wayside.c").read_text()
DO = (ROOT / "src" / "do.c").read_text()
DUNGEON = (ROOT / "dat" / "dungeon.lua").read_text()
YOU = (ROOT / "include" / "you.h").read_text()
STONY = (ROOT / "src" / "stony.c").read_text()


def ordinary(depth, specials, branches, bottom):
    if depth <= 1 or depth >= bottom - 1:
        return False
    if depth in specials or depth in branches:
        return False
    return True


def choose(candidates, count, rng):
    """Draw `count` hosts. Each pair has an ordinary level between."""
    picked = []
    guard = 0
    while len(picked) < count and guard < 500 and candidates:
        guard += 1
        c = candidates[rng.randrange(len(candidates))]
        ok = True
        for prev in picked:
            if c == prev:
                ok = False
                break
            lo, hi = min(c, prev), max(c, prev)
            if not any(d in candidates for d in range(lo + 1, hi)):
                ok = False
                break
        if ok:
            picked.append(c)
    return picked


class Hosts(unittest.TestCase):
    def test_spacing_and_ordinary_levels(self):
        specials = {1, 4, 8, 12, 24}
        branches = {9}
        bottom = 24
        cand = [d for d in range(1, bottom + 1)
                if ordinary(d, specials, branches, bottom)]
        self.assertNotIn(1, cand)
        self.assertNotIn(23, cand)
        self.assertNotIn(24, cand)
        self.assertNotIn(4, cand)
        self.assertNotIn(9, cand)
        rng = random.Random(7)
        for _ in range(30):
            hosts = choose(cand, 2, rng)
            self.assertEqual(len(hosts), 2)
            lo, hi = sorted(hosts)
            self.assertTrue(any(d in cand for d in range(lo + 1, hi)))

    def test_the_choice_is_saved_on_the_hero(self):
        self.assertIn("xint16 host[4]", YOU)
        choose = WAYSIDE.split("trial_choose(void)", 1)[1].split(
            "trial_receive", 1)[0]
        self.assertIn("hosts_chosen()", choose)
        self.assertIn("u.uwayside.host[i]", choose)
        self.assertIn("rn2", choose)
        begin = WAYSIDE.split("wayside_begin(void)", 1)[1].split(
            "name_house", 1)[0]
        self.assertIn("trial_choose()", begin)


class Stairs(unittest.TestCase):
    def test_down_does_not_enter(self):
        down = WAYSIDE.split("wayside_take_down(void)", 1)[1].split(
            "wayside_blocks_levelport", 1)[0]
        self.assertIn("return FALSE", down)
        self.assertNotIn("goto_level", down)

    def test_up_enters_until_the_trial_is_done(self):
        up = WAYSIDE.split("wayside_take_up(void)", 1)[1].split(
            "wayside_take_down", 1)[0]
        self.assertIn("hosting(&u.uz)", up)
        self.assertIn("trial_list[i].done()", up)
        self.assertIn("goto_level(&dest, TRUE, FALSE, FALSE)", up)
        self.assertIn("sanctum_ascent_open()", up)
        self.assertIn("sanctum_ascent_refused()", up)
        self.assertLess(up.index("trial_list[i].done()"),
                        up.index("sanctum_ascent_refused()"))
        self.assertLess(up.index("sanctum_ascent_refused()"),
                        up.index("goto_level"))
        self.assertLess(up.index("The way on is shut."), up.index("hosting"))
        self.assertIn(
            "A voice whispers: Put on the helmet of salvation. You cannot face what lies ahead with your mind unguarded.",
            (ROOT / "src" / "hack.c").read_text(),
        )

    def test_exit_and_back_stairs(self):
        link = WAYSIDE.split("trial_link(", 1)[1].split("trials_left", 1)[0]
        self.assertIn("back->dlevel = u.uwayside.host[i]", link)
        self.assertIn("back->dlevel - 1", link)
        wayside = WAYSIDE.split("fix_stairs(void)", 1)[1].split(
            "seal_walls", 1)[0]
        self.assertIn('trial_link("wayside"', wayside)
        self.assertIn("aim_one(ux, uy, TRUE, &onward)", wayside)
        self.assertIn("aim_one(dx, dy, FALSE, &back)", wayside)
        stony = STONY.split("aim_stairs(void)", 1)[1].split("apply_reset", 1)[0]
        self.assertIn('trial_link("stony"', stony)
        self.assertIn("plant_one(START_X, START_Y, FALSE, &back)", stony)
        self.assertIn("plant_one(EXIT_X, EXIT_Y, TRUE, &onward)", stony)

    def test_each_trial_is_its_own_branch(self):
        self.assertIn('name = "The Wayside"', DUNGEON)
        self.assertIn('name = "The Stony Ground"', DUNGEON)
        self.assertIn("unconnected", DUNGEON)
        self.assertNotIn('name = "The Road to Salvation"', DUNGEON)
        self.assertNotIn("Thorns", DUNGEON)
        self.assertNotIn("Good Ground", DUNGEON)


class Depth(unittest.TestCase):
    def test_unconnected_is_not_a_missing_branch(self):
        dgn = (ROOT / "src" / "dungeon.c").read_text()
        body = dgn.split("builds_up(d_level *lev)", 1)[1].split(
            "next_level", 1)[0]
        self.assertLess(body.index("flags.unconnected"),
                        body.index("can't find branch"))
        self.assertLess(body.index("return FALSE;"),
                        body.index("can't find branch"))

    def test_overview_and_dlvl_use_the_host_depth(self):
        body = WAYSIDE.split("trial_set_depths(void)", 1)[1].split(
            "trial_receive", 1)[0]
        self.assertIn("depth_start = depth(&host)", body)
        self.assertIn("host.dlevel = u.uwayside.host[i]", body)
        choose = WAYSIDE.split("trial_choose(void)", 1)[1].split(
            "trial_set_depths(void)", 1)[0]
        self.assertIn("trial_set_depths()", choose)
        restore = (ROOT / "src" / "restore.c").read_text()
        self.assertIn("trial_set_depths()", restore)


class Seals(unittest.TestCase):
    def test_the_pull_skips_every_trial_branch(self):
        self.assertIn("!on_trial(&u.uz)", DO)
        body = WAYSIDE.split("on_trial(", 1)[1].split("hosting", 1)[0]
        self.assertIn("trial_index(lev)", body)

    def test_levelport_counts_what_remains(self):
        block = WAYSIDE.split("wayside_blocks_levelport(void)", 1)[1]
        self.assertIn("trials_left()", block)
        self.assertIn("1 trial remains.", block)
        self.assertIn("%d trials remain.", block)
        self.assertNotIn("two trials are still to come", WAYSIDE)


if __name__ == "__main__":
    unittest.main()
