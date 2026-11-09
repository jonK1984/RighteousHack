#!/usr/bin/env python3
"""Static checks for the Wayside trial.

These do not boot NetHack. They compare the locked text and map in
the sources with the approved literals, and they check that the
control flow for pets, hero attacks, soul identity, and placement
is the one the specification requires.
"""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WAYSIDE_C = (ROOT / "src" / "wayside.c").read_text()
WAYSIDE_LUA = (ROOT / "dat" / "wayside.lua").read_text()
OBJECTS_H = (ROOT / "include" / "objects.h").read_text()
DO_C = (ROOT / "src" / "do.c").read_text()
MHITM_C = (ROOT / "src" / "mhitm.c").read_text()
MON_C = (ROOT / "src" / "mon.c").read_text()
DOGMOVE_C = (ROOT / "src" / "dogmove.c").read_text()
UHITM_C = (ROOT / "src" / "uhitm.c").read_text()

INTRO = (
    "You have come to the Wayside, where seeing, they see not; and hearing, they hear not, neither do they understand.\n"
    "\n"
    "Six homes stand beside the road. Within each waits a troubled villager, "
    "holding a riddle whose answer has slipped beyond their grasp.\n"
    "\n"
    "Help them recover what they have lost, and the way before you shall open. "
    "But weigh your answers carefully. An error will cast you back to the "
    "courtyard, where more than questions await you.\n"
    "\n"
    "Listen closely. Consider well. Then answer."
)

BODIES = [
    "I settle a score by refusing to even it.\n"
    "I release a debt without receiving payment.\n"
    "I lose what I am owed, yet call it no loss.",
    "I change your course without moving your feet.\n"
    "I cannot undo a wrong, but I can refuse it another turn.\n"
    "You cannot move forward with me until you turn around.",
    "If given, I am free;\n"
    "Try to purchase, you cannot afford.\n"
    "I come without price, yet cost the highest of prices.",
    "I am possessed by a child.\n"
    "You can lose me without misplacing me.\n"
    "My power is strongest when you are at your weakest.",
    "I'm easy for the simple.\n"
    "But hard for most to hear.\n"
    "Try to hide me, I do not disappear.",
    "I am blind, yet see through evil,\n"
    "If purchased, my value goes to none.\n"
    "A servant may have me, but a king is not above me.",
]
NAMES = [
    "Confused villager",
    "Bewildered villager",
    "Perplexed villager",
    "Puzzled villager",
    "Baffled villager",
    "Befuddled villager",
]
ANSWERS = [
    "Forgiveness",
    "Repentance",
    "Grace",
    "Faith",
    "Truth",
    "Justice",
]

SPEC_MAP = """\
###############################################################################
#..################...............................##############.#            #
#..#              #........#################......#            #.#            #
#..#    1         #........#               #......#     3      #.#      <     #
#..#              #........#       2       #......#            #.#            #
#..#              #........#               #......#            #.#            #
#..#        #######........########+########......######+#######.#####G########
#..########+#.................................................................#
#..TTTTTTT...TTTTTTTTTTTTTTTTTTTTT...TTTTTTTTTTTTTTTTTT...TTTTTTTTTTT...TTTTT.#
#.............................................................................#
#.............................................................................#
#.............................................................................#
#..TTTT........TTTTTTTTTTT...TTTTTTTTTTTTTTTT...TTTTTTTTTTTTTTTTT...TTTTTTTTT.#
#######........####...........................................................#
#.................#..######+#######....#######+##..........#######+########...#
#.................#..#            #....#        #..........#              #...#
#.......m.R.m.....#..#            #....#        #######....#              #...#
#.................#..#     4      #....#    5         #....#      6       #...#
#....>............#..#            #....#              #....#              #...#
#.................#..##############....################....################...#
###############################################################################
""".splitlines()


def c_decode(text):
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            n = text[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"'}.get(n, n))
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def c_strings(block):
    return [c_decode(s) for s in re.findall(r'"((?:\\.|[^"\\])*)"', block)]


def array_block(source, name):
    match = re.search(
        rf"static const char \*const {name}\[6\] = \{{(.*?)\n\}};",
        source,
        re.S,
    )
    if not match:
        raise AssertionError(f"missing {name}")
    return "".join(c_strings(match.group(1)))


def lua_map_rows():
    rows = []
    grab = False
    for line in WAYSIDE_LUA.splitlines():
        if "map = [[" in line:
            grab = True
            continue
        if grab:
            if line.strip().startswith("]]"):
                break
            rows.append(line)
    return rows


def spec_class(ch):
    if ch == "#":
        return "WALL"
    if ch in ". 123456mR<>":
        return "FLOOR"
    if ch == "T":
        return "TREE"
    if ch == "+":
        return "DOOR"
    if ch == "G":
        return "GATE"
    return "OTHER"


def lua_class(ch):
    if ch in "-|":
        return "WALL"
    if ch == ".":
        return "FLOOR"
    if ch == "T":
        return "TREE"
    if ch == "+":
        return "DOOR"
    if ch == " ":
        return "STONE"
    if ch == "#":
        return "CORR"
    return "OTHER"


def walkable(ch):
    return ch in ".+"


def wall_gaps(rows):
    """Walls that meet only at a corner leave a disconnected segment."""
    height, width = len(rows), len(rows[0])
    gaps = []
    wall = set("-|")
    for y in range(height - 1):
        for x in range(width - 1):
            a, b = rows[y][x], rows[y][x + 1]
            c, d = rows[y + 1][x], rows[y + 1][x + 1]

            def openish(ch):
                return ch not in wall and ch != "+"

            if a in wall and d in wall and openish(b) and openish(c):
                gaps.append(((x, y), (x + 1, y + 1)))
            if b in wall and c in wall and openish(a) and openish(d):
                gaps.append(((x + 1, y), (x, y + 1)))
    return gaps


def room_leaks(rows, sx, sy):
    """Floor inside a house, treating doors as walls, must not reach the road."""
    height, width = len(rows), len(rows[0])

    def flood_at(x0, y0):
        seen = set()
        stack = [(x0, y0)]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
                continue
            if rows[y][x] in "-|+" :
                continue
            seen.add((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((x + dx, y + dy))
        return seen

    return flood_at(sx, sy) & flood_at(5, 10)


def flood(rows, sx, sy, gate_open=False):
    height, width = len(rows), len(rows[0])
    seen = set()
    stack = [(sx, sy)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < width and 0 <= y < height) or (x, y) in seen:
            continue
        ch = rows[y][x]
        if gate_open and (x, y) == (70, 6):
            ch = "."
        if not walkable(ch):
            continue
        seen.add((x, y))
        for dx, dy in (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ):
            stack.append((x + dx, y + dy))
    return seen


def eligible(orcus, vibrating, specials, branches, visited, written, nlevels):
    """The placement rule: strictly between the two endpoints."""
    found = []
    if not (0 < orcus < vibrating):
        return found
    for depth in range(orcus + 1, vibrating):
        if depth < 1 or depth > nlevels:
            continue
        if depth in specials or depth in branches:
            continue
        if depth in visited or depth in written:
            continue
        found.append(depth)
    return found


def step(n):
    if n >= 6:
        return "die"
    if n == 5:
        return "half+punish"
    if n == 4:
        return "warn4+punish"
    return "punish"


def halve(hp):
    hp //= 2
    return 1 if hp < 1 else hp


def remain_words(left):
    if left == 1:
        return "(1 riddle remains.)"
    return "(%d riddles remain.)" % left


def blank_answer(guess):
    if guess is None or guess == "" or guess == "\033":
        return True
    return guess.strip(" \t") == ""


def answer_ok(canonical, guess):
    if blank_answer(guess):
        return False
    return guess.strip(" \t").lower() == canonical.lower()


class WaysideSourceTests(unittest.TestCase):
    def test_locked_text(self):
        intro = "".join(c_strings(re.search(
            r"show_intro\(void\)\s*\{(.*?)\n\}", WAYSIDE_C, re.S
        ).group(1)))
        self.assertEqual(intro, INTRO)
        bodies = c_strings(re.search(
            r"static const char \*const ws_body\[6\] = \{(.*?)\n\};",
            WAYSIDE_C, re.S,
        ).group(1))
        self.assertEqual(bodies, BODIES)
        for body in bodies:
            self.assertEqual(body.count("\n"), 2)
            self.assertNotIn("What am I?", body)
        names = c_strings(re.search(
            r"static const char \*const ws_name\[6\] = \{(.*?)\n\};",
            WAYSIDE_C, re.S,
        ).group(1))
        answers = c_strings(re.search(
            r"static const char \*const ws_answer\[6\] = \{(.*?)\n\};",
            WAYSIDE_C, re.S,
        ).group(1))
        self.assertEqual(names, NAMES)
        self.assertEqual(answers, ANSWERS)
        self.assertEqual(WAYSIDE_C.count('"What am I?"'), 1)
        self.assertNotIn("yet I see through evil", WAYSIDE_C)
        self.assertNotIn("When purchased", WAYSIDE_C)

    def test_answer_rules(self):
        # Mirrors ask_riddle: blank input returns before punishment.
        ask = WAYSIDE_C.split("ask_riddle(struct monst *mtmp)", 1)[1].split(
            "wayside_chat(", 1
        )[0]
        self.assertLess(ask.index("blank_answer"), ask.index("note_wrong_answer"))
        self.assertNotIn("wayside_hero_strikes", WAYSIDE_C.split("note_wrong_answer", 1)[0][-400:] + "")
        self.assertNotIn("u.uwayside.wrongs", WAYSIDE_C.split("wayside_hero_strikes", 1)[1][:500])
        self.assertTrue(blank_answer(""))
        self.assertTrue(blank_answer("   "))
        self.assertTrue(blank_answer("\t"))
        self.assertTrue(blank_answer("\033"))
        self.assertFalse(blank_answer("no"))
        self.assertTrue(answer_ok("Faith", "faith"))
        self.assertTrue(answer_ok("Faith", " FAITH "))
        self.assertFalse(answer_ok("Faith", "faithfulness"))
        self.assertFalse(answer_ok("Faith", "   "))

    def test_map_geometry(self):
        rows = lua_map_rows()
        self.assertEqual(len(rows), 21)
        self.assertEqual(len(SPEC_MAP), 21)
        for y, (spec, lua) in enumerate(zip(SPEC_MAP, rows)):
            self.assertEqual(len(spec), 79, y)
            self.assertEqual(len(lua), 79, y)
            for x, (sc, lc) in enumerate(zip(spec, lua)):
                got = lua_class(lc)
                want = spec_class(sc)
                if want == "GATE":
                    self.assertEqual(got, "WALL", (x, y))
                else:
                    self.assertEqual(got, want, (x, y, sc, lc))
        reached = flood(rows, 5, 18, gate_open=False)
        for house in ((8, 3), (35, 4), (56, 3), (27, 17), (44, 17), (66, 17)):
            self.assertIn(house, reached)
        for door in ((11, 7), (35, 6), (56, 6), (27, 14), (46, 14), (66, 14)):
            self.assertIn(door, reached)
        self.assertNotIn((72, 3), reached)
        self.assertIn((72, 3), flood(rows, 5, 18, gate_open=True))
        self.assertEqual(rows[6][70], "-")
        self.assertEqual(wall_gaps(rows), [])
        for sx, sy in ((8, 3), (35, 4), (56, 3), (27, 17), (44, 17), (66, 17)):
            self.assertEqual(room_leaks(rows, sx, sy), set())

    def test_soul_is_not_a_gem_and_state_is_not_corpsenm(self):
        soul = re.search(r'TOOL\("your soul".*PLAYER_SOUL\)', OBJECTS_H, re.S)
        self.assertIsNotNone(soul)
        self.assertNotIn("GEMSTONE", soul.group(0))
        self.assertNotIn("bound soul", OBJECTS_H)
        self.assertNotIn("chained relic", OBJECTS_H)
        self.assertNotIn("->corpsenm", WAYSIDE_C)
        self.assertIn("u.uwayside.bits", WAYSIDE_C)

    def test_sanctum_block_is_immediate(self):
        self.assertIn("sanctum_ascent_open()", DO_C)
        # The stair command no longer waits for the hosts to freeze.
        doup = DO_C.split("doup(void)", 1)[1].split("currentlevel_rewrite", 1)[0]
        self.assertIn("sanctum_ascent_open()", doup)
        self.assertNotIn("sanctum_frozen", doup)
        before_begin = DO_C.split("wayside_begin();", 1)[0]
        self.assertIn("sanctum_ascent_open()", before_begin)

    def test_placement_rule(self):
        choose = re.search(
            r"wayside_choose\(void\)\s*\{(.*?)\n\}", WAYSIDE_C, re.S
        ).group(1)
        self.assertIn("Is_special", choose)
        self.assertIn("Is_branchlev", choose)
        self.assertIn("VISITED", choose)
        self.assertIn("LFILE_EXISTS", choose)
        self.assertIn("rn2", choose)
        self.assertIn("WS_MODE_INSERT", choose)
        self.assertIn("WS_MODE_LEVEL", choose)
        # Endpoints 10 and 24 are outside. 12 is special. 14 is a branch.
        # 16 was visited. 18 was already written. The rest of the span remains.
        self.assertEqual(
            eligible(10, 24, {12}, {14}, {16}, {18}, 25),
            [11, 13, 15, 17, 19, 20, 21, 22, 23],
        )
        self.assertEqual(eligible(10, 24, set(), set(), set(range(11, 24)), set(), 25), [])
        self.assertNotIn(10, eligible(10, 24, set(), set(), set(), set(), 25))
        self.assertNotIn(24, eligible(10, 24, set(), set(), set(), set(), 25))

    def test_pets_are_stopped_before_damage(self):
        plot = MON_C.split("is_plot_npc(struct monst *mtmp)", 1)[1].split(
            "peter_unhurt", 1
        )[0]
        self.assertLess(plot.index("wayside_is_villager"), plot.index("has_mgivenname"))
        attack = MHITM_C.split("mattackm(", 1)[1]
        self.assertLess(attack.index("wayside_is_villager"), attack.index("find_mac"))
        displace = MHITM_C.split("mdisplacem(", 1)[1]
        self.assertLess(displace.index("wayside_is_villager"), displace.index("pa = magr"))
        self.assertIn("wayside_is_villager(mtmp2)", DOGMOVE_C)
        self.assertIn("is_plot_npc(mtarg)", DOGMOVE_C)
        self.assertIn("is_plot_npc(mtmp2)", DOGMOVE_C)
        self.assertIn("even when confused or in conflict", DOGMOVE_C)

    def test_hero_attack_is_immediate(self):
        attack = UHITM_C.split("do_attack(struct monst *mtmp)", 1)[1][:8000]
        self.assertLess(attack.index("attack_checks"), attack.index("wayside_hero_strikes"))
        self.assertLess(
            attack.index("wayside_hero_strikes"),
            attack.index("(void) hitum"),
        )
        hmon = UHITM_C.split("\nhmon(", 1)[1]
        self.assertLess(hmon.index("wayside_hero_strikes"), hmon.index("hmon_hitmon"))

    def test_jon_exact_lines(self):
        hack = (ROOT / "src" / "hack.c").read_text()
        self.assertIn(
            "The stairs will not receive you. You cannot walk the road while leaving your soul behind.",
            hack,
        )
        self.assertIn(
            "A voice whispers: Put on the helmet of salvation. You cannot face what lies ahead with your mind unguarded.",
            hack,
        )
        self.assertIn(
            "A voice whispers: You come empty handed and bare headed. Recover your soul and put on the helmet of salvation.",
            hack,
        )
        self.assertIn("sanctum_ascent_refused()", (ROOT / "src" / "do.c").read_text())
        self.assertIn(
            "The %s villager's eyes brighten. '%s! Yes, that was it. Thank you, friend.' %s",
            WAYSIDE_C,
        )
        self.assertIn(
            "Understanding dawns on the %s villager's face. '%s. How could I have forgotten?' The burden lifts from this house. %s",
            WAYSIDE_C,
        )
        self.assertIn(
            "'%s,' the %s villager repeats softly. 'I hear it now, and I understand.' %s",
            WAYSIDE_C,
        )
        self.assertIn("(1 riddle remains.)", WAYSIDE_C)
        self.assertIn("(%d riddles remain.)", WAYSIDE_C)
        self.assertNotIn("The gate opens.", WAYSIDE_C)
        self.assertNotIn(" of 6", WAYSIDE_C)
        self.assertIn(
            "Thy folly multiplieth, and thy footing groweth unsure. The fool walketh in darkness; twice more mayest thou err, and then thy foolishness shall be thine undoing.",
            WAYSIDE_C,
        )
        self.assertIn(
            "Thy strength faileth thee, for thine own folly hath wounded thee. Pride goeth before destruction. One error more, and thou shalt fall by thine own hand.",
            WAYSIDE_C,
        )
        self.assertIn("Thou hast heard, yet thou hast not understood.", WAYSIDE_C)
        self.assertIn("The answer was %s.", WAYSIDE_C)
        self.assertIn("The way of a fool is right in his own eyes.", WAYSIDE_C)
        self.assertIn("Undone by folly at the Wayside.", WAYSIDE_C)
        self.assertIn("xint16 wrongs", (ROOT / "include" / "you.h").read_text())
        self.assertIn("EDITLEVEL 13", (ROOT / "include" / "patchlevel.h").read_text())
        # Counter: only wrong answers. 4 warns, 5 halves, 6 dies, no reset.
        self.assertEqual([step(i) for i in range(1, 8)], [
            "punish", "punish", "punish", "warn4+punish",
            "half+punish", "die", "die",
        ])
        self.assertEqual(halve(5), 2)
        self.assertEqual(halve(1), 1)
        self.assertEqual(halve(4), 2)
        self.assertEqual(remain_words(0), "(0 riddles remain.)")
        self.assertEqual(remain_words(1), "(1 riddle remains.)")
        self.assertEqual(remain_words(5), "(5 riddles remain.)")

    def test_levelport_does_not_complete_later_trials(self):
        block = re.search(
            r"wayside_blocks_levelport\(.*?^\}", WAYSIDE_C, re.S | re.M
        ).group(0)
        self.assertIn("three trials", block)
        self.assertNotIn("WS_TRIAL2", WAYSIDE_C)
        self.assertNotIn("trial2", WAYSIDE_C.lower())
        self.assertIn("wayside_blocks_levelport()", (ROOT / "src" / "sit.c").read_text())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WaysideSourceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
