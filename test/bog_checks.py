#!/usr/bin/env python3
"""Bog terrain: walkable marsh ground shown as water, brown, called bog."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def symsets():
    sets = {}
    name = None
    for line in read("dat/symbols").splitlines():
        line = line.strip()
        if line.startswith("start:"):
            name = line.split(":", 1)[1].strip()
            sets[name] = {}
        elif line.startswith("finish"):
            name = None
        elif name:
            m = re.match(r"(S_\w+):\s*('.'|\S+)", line)
            if m:
                sets[name][m.group(1)] = m.group(2)
    return sets


class BogTerrainTests(unittest.TestCase):
    def test_terrain_type(self):
        rm = read("include/rm.h")
        self.assertIn("    CLOUD     = 36,\n    BOG       = 37,", rm)
        self.assertIn("MAX_TYPE  = 38,", rm)
        self.assertIn("#define IS_BOG(typ) ((typ) == BOG)", rm)
        # BOG sits above ROOM, so ACCESSIBLE() and IS_ROOM() hold and
        # IS_POOL() does not: everyone can walk on it
        self.assertIn("#define ACCESSIBLE(typ) ((typ) >= DOOR)", rm)
        self.assertIn("#define IS_POOL(typ) ((typ) >= POOL && (typ) <= DRAWBRIDGE_UP)",
                      rm)
        cmd = read("src/cmd.c")
        self.assertIn('"air", "cloud", "bog",', cmd)
        botl = read("src/botl.c")
        self.assertIn('"Cloud",         /* [part of] a cloud or Air level */\n'
                      '/*37*/ "Bog",', botl)
        self.assertIn('"CLOUD", "BOG"', read("src/display.c"))

    def test_symbol(self):
        ds = read("include/defsym.h")
        self.assertIn("PCHAR( 49, '}',  S_bog,    \"bog\", CLR_BROWN)", ds)
        self.assertLess(ds.index("S_water,"), ds.index("S_bog,"))
        self.assertLess(ds.index("S_bog,"), ds.index("S_arrow_trap,"))
        self.assertIn("#define MAXDCHARS (S_bog - S_stone + 1)",
                      read("include/sym.h"))
        disp = read("src/display.c")
        self.assertEqual(disp.count("case BOG:"), 2)
        self.assertIn("idx = S_bog;", disp)
        self.assertIn("case S_bog:\n        typ = BOG;", read("src/mkroom.c"))
        self.assertIn("cmap = S_bog; /* \"bog\" */", read("src/invent.c"))

    def test_every_symset_matches_pool(self):
        sets = symsets()
        self.assertIn("DECgraphics", sets)
        self.assertIn("IBMgraphics", sets)
        self.assertIn("curses", sets)
        self.assertIn("Enhanced1", sets)
        self.assertIn("Enhanced2", sets)
        for name, syms in sets.items():
            self.assertEqual(syms.get("S_bog"), syms.get("S_pool"),
                             "symset %s" % name)

    def test_tile(self):
        other = read("win/share/other.txt")
        water = other.index(" (water)\n")
        bog = other.index(" (bog)\n")
        self.assertLess(water, bog)
        self.assertLess(bog, other.index(" (arrow trap)\n"))
        nums = [int(n) for n in re.findall(r"^# tile (\d+) ", other, re.M)]
        self.assertEqual(nums, list(range(len(nums))))

    def test_lua_map_character(self):
        lua = read("src/nhlua.c")
        self.assertIn("{ 'b', BOG },", lua)
        self.assertLess(lua.index("{ 'b', BOG },"),
                        lua.index("{ 'x', MAX_TYPE },"))
        self.assertIn('| `"b"`     | bog', read("doc/lua.adoc"))

    def test_step_effects(self):
        hack = read("src/hack.c")
        body = hack.split("bog_step(void)\n{", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("if (u.usteed) {", body)
        self.assertIn("if (!u.uevent.bog_ridden) {", body)
        self.assertIn("u.uevent.bog_ridden = 1;", body)
        self.assertIn('pline("Thy steed beareth thee lightly over the bog.");',
                      body)
        self.assertIn("} else if (!rn2(20)) {", body)
        self.assertIn('pline("Thy feet sink into the bog.");', body)
        self.assertIn("nomul(-2);", body)
        self.assertIn('gn.nomovemsg = "";', body)
        self.assertNotIn("multi_reason", body)
        move = hack.split("domove_core(void)\n{", 1)[1]
        move = move.split("runmode_delay_output(void)", 1)[0]
        self.assertIn("boolean onbog = IS_BOG(levl[u.ux][u.uy].typ);", move)
        self.assertLess(move.index("spoteffects(TRUE);"),
                        move.index("bog_step();"))
        you = read("include/you.h")
        self.assertIn("Bitfield(bog_ridden, 1);", you)
        self.assertIn("#define EDITLEVEL 20 ", read("include/patchlevel.h"))

    def test_not_placed_yet(self):
        for lua in (ROOT / "dat").glob("*.lua"):
            text = lua.read_text(encoding="utf-8")
            for blk in re.findall(r"\[\[(.*?)\]\]", text, re.S):
                rows = [r for r in blk.split("\n") if r.strip()]
                mapish = [r for r in rows if re.fullmatch(
                    r"[ #.\-|+ACSH{\\K}PLZIWTFxBwb<>^_]*", r)]
                if mapish and len(mapish) >= len(rows) // 2:
                    self.assertFalse(any("b" in r for r in mapish), lua.name)


if __name__ == "__main__":
    unittest.main()
