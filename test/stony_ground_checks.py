#!/usr/bin/env python3
"""Static checks for the Stony Ground.

The BFS walks the special-level map. Blocking each trigger set must
make the summit unreachable from the foot of the pass.
"""

import pathlib
import re
import sys
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / "src" / "stony.c").read_text()
LUA = (ROOT / "dat" / "stony.lua").read_text()
HINNOM = (ROOT / "src" / "hinnom.c").read_text()
MAKEMON = (ROOT / "src" / "makemon.c").read_text()
DOG = (ROOT / "src" / "dog.c").read_text()
BONES = (ROOT / "src" / "bones.c").read_text()
WAYSIDE = (ROOT / "src" / "wayside.c").read_text()
DUNGEON = (ROOT / "dat" / "dungeon.lua").read_text()
MONMOVE = (ROOT / "src" / "monmove.c").read_text()

LOCKED = [
    "The old man sinketh to his knees, pale and trembling. 'My strength faileth me! Pray for me, or lay hands upon me, for I shall not last long!'",
    "The old man riseth, and his strength is renewed. 'Bless thee, my child.'",
    "The old man's breath faileth, and he slumpeth upon the stones.\n"
    "\n"
    "Thou didst not lay hands upon him in his hour of need.\n"
    "\n"
    "The old man hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The old man leaneth upon thy shoulder and smileth. 'I have fought a good fight, I have finished my course, I have kept the faith. I could not have climbed alone. Bless thee, my child.'",
    "The young believer paceth restlessly. 'Why do we wait? I could be at the summit already! I cannot abide this slowness, my heart burneth within me!'",
    "'Make haste, make haste! The LORD is up there, and I will not tarry for anyone. Mine eyes are fixed upon the summit, and my feet will not be still!'",
    "The young believer's breathing slows. 'Forgive me. I was hasty. I will walk beside thee.'",
    "The young believer's eyes burn with zeal. 'I can wait no longer! If thou wilt not hasten, I shall go on without thee!'",
    "The young believer rusheth ahead, heedless of thy cry.\n"
    "\n"
    "From among the rocks the persecutors fall upon him, and he is overcome. His zeal had no root.\n"
    "\n"
    "The young believer hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The young believer turneth to thee with tears in his eyes. 'I would have perished in my haste. But let patience have her perfect work, that ye may be perfect and entire, wanting nothing. Thou hast taught me patience, and now my faith hath taken root. I thank thee, friend.'",
    "The mother clutcheth her child and trembleth. 'They will take my child! I cannot go on, I must turn back!'",
    "The darkness closeth about the mother, and her heart melteth for fear.\n"
    "\n"
    "She turneth and fleeth down the mountain with her child, and the persecutors pursue her.\n"
    "\n"
    "The mother hath not made it. Thou art returned to the foot of the pass, to begin again.",
    "The mother lifteth her child toward the light. 'The LORD is my light and my salvation; whom shall I fear? Thou didst not leave us in the darkness. God bless thee, friend.'",
]


def c_text(src):
    parts = []

    def take(match):
        parts.append(bytes(match.group(1), "utf-8").decode("unicode_escape"))
        return ""

    re.sub(r'"((?:\\.|[^"\\])*)"', take, src)
    return "".join(parts)


def map_rows():
    start = LUA.index("[[\n") + 3
    block = LUA[start:LUA.index("\n]]")]
    rows = block.split("\n")
    assert rows and all(len(r) == len(rows[0]) for r in rows)
    return rows


def walkable(rows):
    cells = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in " L":
                cells.add((x, y))
    return cells


def reaches(walk, blocked, start, goal):
    if start in blocked or start not in walk:
        return False
    q = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if nxt in walk and nxt not in seen and nxt not in blocked:
                seen.add(nxt)
                q.append(nxt)
    return False


def cells_of(name):
    """Pull a C coord array named sg_<name> as map coordinates."""
    body = SRC.split("sg_%s[]" % name, 1)[1].split("};", 1)[0]
    pairs = re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", body)
    return {(int(x), int(y)) for x, y in pairs}


class Text(unittest.TestCase):
    def test_locked_lines(self):
        seen = c_text(SRC)
        for line in LOCKED:
            self.assertIn(line, seen)

    def test_no_em_dash(self):
        self.assertNotIn("\u2014", SRC)
        self.assertNotIn("\u2014", LUA)


class Cuts(unittest.TestCase):
    def test_triggers_block_the_summit(self):
        rows = map_rows()
        walk = walkable(rows)
        start = (0, 19)
        summit = (20, 2)
        self.assertTrue(reaches(walk, set(), start, summit))
        sets = {
            "ss": cells_of("ss"),
            "w": cells_of("w"),
            "x": cells_of("x"),
            "b0": cells_of("b0"),
            "b1": cells_of("b1"),
            "b2": cells_of("b2"),
            "b3": cells_of("b3"),
        }
        for name, cells in sets.items():
            self.assertTrue(cells, name)
            self.assertTrue(cells <= walk, name)
            self.assertFalse(reaches(walk, cells, start, summit), name)

    def test_the_persecutor_hits_harder(self):
        mons = (ROOT / "include" / "monsters.h").read_text()
        block = mons.split('NAM("persecutor")', 1)[1].split("PERSECUTOR)", 1)[0]
        comment = mons.split('NAM("persecutor")', 1)[0].rsplit("/*", 1)[1]
        self.assertIn("LVL(10, 12, 4, 0, -3)", block)
        self.assertIn("ATTK(AT_WEAP, AD_PHYS, 3, 4)", block)
        self.assertIn("G_NOGEN", block)
        self.assertIn("M2_NOPOLY | M2_HUMAN | M2_HOSTILE | M2_STALK", block)
        self.assertIn("M3_INFRAVISIBLE", block)
        self.assertRegex(block, r"\n\s+11, CLR_YELLOW")
        self.assertIn("CLR_YELLOW is not used by any other '@'", comment)
        self.assertNotIn("weak", comment)

    def test_camp_is_not_a_spawn_row(self):
        self.assertIn("y >= 10 && y <= 14", SRC)
        self.assertIn("PM_PERSECUTOR", SRC)
        # The camp bowl is those rows. The spring and the travelers sit there.
        self.assertIn('name = "young believer", x = 42, y = 11', LUA)
        self.assertIn('name = "old man", x = 48, y = 11', LUA)
        self.assertIn('name = "mother", x = 54, y = 11', LUA)
        self.assertIn('x = 71, y = 18', LUA)
        self.assertNotIn('x = 48, y = 13', LUA)

    def test_the_hidden_trail_reaches_the_chest(self):
        rows = map_rows()
        self.assertEqual(len(rows), 21)
        self.assertTrue(all(len(row) == 75 for row in rows))
        self.assertEqual(rows[12][59], "S")
        self.assertEqual(rows[12][60:65], "#####")
        self.assertEqual(rows[13][64], "#")
        self.assertEqual(rows[14][64], "#")
        self.assertEqual(rows[15][64:68], "####")
        for y in range(16, 20):
            self.assertEqual(rows[y][66:73], ".......", y)
        self.assertEqual(rows[18][71], ".")
        for y in range(5, 10):
            self.assertEqual(rows[y][47:49], "##", y)
        self.assertIn('des.door("secret", 59, 12)', LUA)
        self.assertIn('"nomongen"', LUA)
        self.assertIn('"hardfloor"', LUA)
        self.assertIn('"noflip"', LUA)
        self.assertIn("#define CHEST_X MX(71)", SRC)
        self.assertIn("#define CHEST_Y MY(18)", SRC)
        walk = walkable(rows)
        camp = (48, 12)
        door = (59, 12)
        chest = (71, 18)
        self.assertIn(camp, walk)
        self.assertTrue(reaches(walk, set(), camp, door))
        self.assertTrue(reaches(walk, set(), door, chest))
        self.assertFalse(reaches(walk, {door}, camp, chest))


class Rules(unittest.TestCase):
    def test_son_of_perdition_is_blocked(self):
        self.assertIn("PM_WIZARD_OF_YENDOR] && trial_bars_son()", MAKEMON)
        self.assertIn("mtmp->iswiz && trial_bars_son()", DOG)

    def test_reset_restores_chest_and_travelers(self):
        reset = SRC.split("apply_reset", 1)[1].split("stony_setup", 1)[0]
        self.assertIn("place_traveler(SG_YOUNG", reset)
        self.assertIn("place_traveler(SG_OLD", reset)
        self.assertIn("place_traveler(SG_MOTH", reset)
        self.assertIn("restock_chest()", reset)
        self.assertIn("clear_persecutors()", reset)
        self.assertIn("u_on_newpos(START_X, START_Y)", reset)
        self.assertIn("pull_into(chest, u.ustony.oid[0]", SRC)
        self.assertIn("pull_into(chest, u.ustony.oid[2]", SRC)

    def test_bones_and_spring_and_gate(self):
        self.assertIn('find_level("stony")', BONES)
        self.assertIn("if (stony_here())", HINNOM)
        self.assertIn('"stony", stony_trial_done', WAYSIDE)
        self.assertIn('trial_link("wayside"', WAYSIDE)

    def test_summit_vitality_is_once_and_survives_reset(self):
        self.assertIn("#define SG_HP_OLD", SRC)
        self.assertIn("#define SG_HP_YOUNG", SRC)
        self.assertIn("#define SG_HP_MOTH", SRC)
        reset = SRC.split("apply_reset", 1)[1].split("stony_setup", 1)[0]
        self.assertIn("sg_set(sg_bits() & SG_HP_ALL)", reset)
        grant = SRC.split("grant_summit_hp", 1)[1].split("check_triggers", 1)[0]
        self.assertIn("u.uhp += 10", grant)
        self.assertIn("setuhpmax(u.uhpmax + 10, TRUE)", grant)
        self.assertIn("setuhpmax(u.mhmax + 10, FALSE)", grant)
        self.assertIn("if (Upolyd)", grant)
        deliver = SRC.split("deliver(int who)", 1)[1].split(
            "grant_summit_hp(int who)", 1)[0]
        self.assertIn("grant_summit_hp(who)", deliver)

    def test_the_summit_stair_is_up_and_left_clear(self):
        rows = map_rows()
        # Map column 0 is level x 1. The exit cell is map (20, 2).
        self.assertEqual(rows[2][20], "<")
        self.assertEqual(rows[19][0], ">")
        self.assertIn('des.stair("up", 20, 2)', LUA)
        self.assertIn('des.stair("down", 0, 19)', LUA)
        self.assertNotIn('des.stair("down", 20, 2)', LUA)
        self.assertNotIn('des.stair("up", 0, 19)', LUA)
        self.assertIn('name = "The Stony Ground"', DUNGEON)
        self.assertIn('{ name = "stony", base = 1 }', DUNGEON)
        self.assertIn("unconnected", DUNGEON)
        self.assertNotIn('name = "The Road to Salvation"', DUNGEON)
        self.assertIn('trial_link("stony"', SRC)
        setup = SRC.split("stony_setup", 1)[1].split("step_toward", 1)[0]
        self.assertIn("aim_stairs()", setup)
        aim = SRC.split("aim_stairs(void)", 1)[1].split("apply_reset", 1)[0]
        self.assertIn("plant_one(START_X, START_Y, FALSE, &back)", aim)
        self.assertIn("plant_one(EXIT_X, EXIT_Y, TRUE, &onward)", aim)
        plant = SRC.split("plant_one(", 1)[1].split("aim_stairs(void)", 1)[0]
        self.assertIn("levl[x][y].typ = STAIRS", plant)
        self.assertIn("stairway_add(x, y, up, FALSE, dest)", plant)
        tick = SRC.split("stony_tick(void)", 1)[1].split("give_ring", 1)[0]
        self.assertIn("aim_stairs()", tick)
        gate = SRC.split("stony_block_stairs", 1)[1].split("stony.c", 1)[0]
        self.assertIn("if (!stony_here() || !up)", gate)
        self.assertIn(
            "The summit stair is shut until all three have reached the top.",
            gate,
        )
        body = SRC.split("sg_berth[3]", 1)[1].split("};", 1)[0]
        berths = [(int(x), int(y)) for x, y in re.findall(
            r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", body)]
        self.assertEqual(len(berths), 3)
        self.assertEqual(len(set(berths)), 3)
        stair = (20, 2)
        neighbors = {(20, 1), (20, 3), (19, 2), (21, 2)}
        for cell in berths:
            self.assertNotEqual(cell, stair)
            self.assertNotIn(cell, neighbors)
            self.assertEqual(rows[cell[1]][cell[0]], ".", cell)
        deliver = SRC.split("deliver(int who)", 1)[1].split(
            "grant_summit_hp(int who)", 1)[0]
        self.assertIn("settle_traveler(who)", deliver)
        self.assertIn("settle_traveler(who)", tick)
        step = SRC.split("step_toward", 1)[1].split("maybe_call", 1)[0]
        self.assertIn("nx == EXIT_X && ny == EXIT_Y", step)
        self.assertIn("if (stony_traveler_settled(mtmp))", MONMOVE)
        self.assertIn("return 0;", MONMOVE.split(
            "stony_traveler_settled(mtmp)", 1)[1][:200])

    def test_arrival_from_the_wayside_is_the_foot(self):
        do = (ROOT / "src" / "do.c").read_text()
        placed = do.split("trap door or level_tele", 1)[1].split(
            "if (Punished)", 1)[0]
        self.assertIn("trial_receive(&u.uz0)", placed)
        wayside = (ROOT / "src" / "wayside.c").read_text()
        recv = wayside.split("trial_receive(", 1)[1].split(
            "on_wayside(void)", 1)[0]
        # From the host, stand on the down stair. From the level
        # above the host, stand on the up stair.
        self.assertLess(
            recv.index("stairway_find_dir(FALSE)"),
            recv.index("stairway_find_dir(TRUE)"),
        )
        self.assertIn("u.uwayside.host[here]", recv)

    def test_the_sleep_ray_reaches_the_calm(self):
        zap = (ROOT / "src" / "zap.c").read_text()
        hit = zap.split("zap_hit(find_mac(mon), spell_type)", 1)[1]
        hit = hit.split("zhitm(mon, type, nd, &otmp)", 1)[0]
        self.assertIn("stony_absorb_zap(mon, zobj)", hit)
        self.assertIn(
            "The young believer's breathing slows. 'Forgive me. I was hasty. I will walk beside thee.'",
            SRC,
        )
        rods = (ROOT / "include" / "objects.h").read_text()
        self.assertIn(
            'ROD("tranquility",               "runed",      50, 175, 1, RAY,       IRON,    HI_METAL,     WAN_SLEEP),',
            rods,
        )
        spell = (ROOT / "src" / "spell.c").read_text()
        self.assertIn('You("begin to %s the prophecy.",', spell)
        self.assertNotIn("the runes.", spell.split("begin to", 1)[1][:80])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
