#!/usr/bin/env python3
"""The plane the player reads is the Plane of Heaven.

The level key stays "astral", so a save already on that plane still
loads. EDITLEVEL stays 20.
"""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PHRASE = "astral plane"


def read(rel):
    return (ROOT / rel).read_text()


def strip_c_comments(src):
    out = []
    i = 0
    n = len(src)
    while i < n:
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src[i] == '"':
            out.append(src[i])
            i += 1
            while i < n and src[i] != '"':
                if src[i] == "\\" and i + 1 < n:
                    out.append(src[i:i + 2])
                    i += 2
                    continue
                out.append(src[i])
                i += 1
            if i < n:
                out.append(src[i])
                i += 1
            continue
        out.append(src[i])
        i += 1
    return "".join(out)


class HeavenPlane(unittest.TestCase):
    def test_the_name_the_player_reads(self):
        dgn = read("src/dungeon.c")
        self.assertIn('Strcpy(outbuf, "Plane of Heaven");', dgn)
        self.assertNotIn('"Astral Plane"', strip_c_comments(dgn))
        self.assertIn('if (!strcmp(proto, "astral"))', dgn)
        self.assertIn('return "Plane of Heaven";', dgn)
        # The loader key is still the word the level file uses.
        self.assertIn('{ "astral", &astral_level }', dgn)
        self.assertIn('name = "astral"', read("dat/dungeon.lua"))
        self.assertIn('name="astral"', read("dat/water.lua"))
        self.assertIn("#define Is_astralevel(x)", read("include/dungeon.h"))
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))

    def test_status_keeps_the_full_name(self):
        botl = read("src/botl.c")
        self.assertIn('strcmp(buf, "Plane of Heaven")', botl)
        self.assertLess(
            botl.index("endgamelevelname(buf, depth(&u.uz))"),
            botl.index('strcmp(buf, "Plane of Heaven")'))
        self.assertLess(
            botl.index('strcmp(buf, "Plane of Heaven")'),
            botl.index('strsubst(buf, "Plane of ", "")'))

    def test_arrival_death_and_records(self):
        lua = read("dat/astral.lua")
        self.assertIn(
            'des.message("You arrive on the Plane of Heaven!")', lua)
        self.assertIn(
            'des.message("Here the High Temple of %d is located.")', lua)
        self.assertIn(
            'des.message("You sense alarm, hostility, and excitement in the air!")',
            lua)
        self.assertIn('where = "The Plane of Heaven";', read("src/end.c"))
        insight = read("src/insight.c")
        self.assertIn('"entered the Plane of Heaven"', insight)
        self.assertIn('"reached the Plane of Heaven"', insight)
        self.assertIn('return "plane of heaven";', read("src/music.c"))
        score = read("src/topten.c")
        self.assertIn('arg = "Heaven";', score)
        self.assertNotIn('arg = "Astral"', score)
        # The record-file token is not the words on the screen.
        self.assertIn('"entered_astral_plane"', score)
        for rel in ("dat/quest.lua", "dat/quest_BAK.lua",
                    "doc/Guidebook.txt", "doc/Guidebook.mn",
                    "doc/Guidebook.tex", "dat/data.base",
                    "dat/engrave.txt", "VERSION_CHANGES.txt"):
            self.assertNotIn(PHRASE, read(rel).lower(), rel)
        self.assertIn("Reached the Plane of Heaven level.",
                      read("doc/Guidebook.txt"))
        self.assertNotIn("\u2014", "You arrive on the Plane of Heaven!")
        self.assertNotIn("\u2014", "The Plane of Heaven")

    def test_no_player_visible_astral_plane_remains(self):
        leftovers = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(".git/") or "/.git/" in rel:
                continue
            if path.suffix not in (
                ".c", ".h", ".lua", ".txt", ".mn", ".tex", ".base",
            ):
                continue
            text = path.read_text(errors="replace")
            if PHRASE not in text.lower():
                continue
            if rel.startswith("doc/fixes") or rel.startswith("outdated/"):
                continue
            if path.suffix in (".c", ".h"):
                if PHRASE in strip_c_comments(text).lower():
                    leftovers.append(rel)
                continue
            leftovers.append(rel)
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
