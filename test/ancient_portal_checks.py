#!/usr/bin/env python3
"""The portal the player sees is an ancient portal.

The level script still says type = "magic portal". That word is how a
map asks for the trap. It is not printed. MAGIC_PORTAL and
S_magic_portal stay the internal names. EDITLEVEL stays 20.
"""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PHRASE = "magic portal"


def read(rel):
    return (ROOT / rel).read_text()


def strip_c_comments(src):
    """Drop /* */ and // comments. Leave string literals in place."""
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


def strip_lua_comments(src):
    lines = []
    for line in src.splitlines(True):
        out = []
        i = 0
        quote = None
        while i < len(line):
            c = line[i]
            if quote:
                out.append(c)
                if c == "\\" and i + 1 < len(line):
                    out.append(line[i + 1])
                    i += 2
                    continue
                if c == quote:
                    quote = None
                i += 1
                continue
            if c in ("'", '"'):
                quote = c
                out.append(c)
                i += 1
                continue
            if line.startswith("--", i):
                break
            out.append(c)
            i += 1
        lines.append("".join(out))
    return "".join(lines)


class AncientPortal(unittest.TestCase):
    def test_the_name_the_player_reads(self):
        sym = read("include/defsym.h")
        self.assertIn(
            'PCHAR( 65, \'^\',  S_magic_portal, "ancient portal", CLR_BRIGHT_MAGENTA)',
            sym)
        self.assertNotIn('"magic portal"', sym)
        tele = read("src/teleport.c")
        self.assertIn('You("activated an ancient portal!");', tele)
        self.assertNotIn("activated a magic portal", tele)
        self.assertIn("MAGIC_PORTAL = 17", read("include/trap.h"))
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))

    def test_articles(self):
        """ancient starts with a vowel, so the article is an."""
        tele = read("src/teleport.c")
        self.assertIn('You("activated an ancient portal!");', tele)
        self.assertNotIn("a ancient portal", tele)
        # A wizard wish names the trap through an(), which sees the vowel.
        wish = read("src/objnam.c")
        self.assertIn('pline("%s%s.", An(tname),', wish)
        self.assertIn('(trap != MAGIC_PORTAL) ? "" : " to nowhere"', wish)
        blob = "\n".join(
            read(rel) for rel in (
                "src/teleport.c",
                "include/defsym.h",
                "dat/quest.lua",
                "dat/tut-1.lua",
                "doc/Guidebook.txt",
                "VERSION_CHANGES.txt",
            )
        )
        self.assertNotIn("a ancient", blob)

    def test_quest_and_tutorial_speech(self):
        for rel in ("dat/quest.lua", "dat/quest_BAK.lua"):
            text = read(rel)
            self.assertNotIn(PHRASE, text.lower())
            self.assertIn("ancient portal", text)
        tut = read("dat/tut-1.lua")
        self.assertIn(
            "You can leave the tutorial via the ancient portal.", tut)
        self.assertIn(
            "Now you know the very basics. You can leave the tutorial via the ancient portal.",
            tut)
        self.assertIn(
            "Another ancient portal, a way to leave this tutorial", tut)
        self.assertNotIn("via the magic portal", tut)
        self.assertNotIn("Another magic portal", tut)

    def test_help_text(self):
        for rel in (
            "doc/Guidebook.txt",
            "doc/Guidebook.mn",
            "doc/Guidebook.tex",
        ):
            text = read(rel)
            self.assertIn("Ancient portals", text)
            self.assertIn("(ancient portal)", text)
            self.assertNotIn(PHRASE, text.lower())
        changes = read("VERSION_CHANGES.txt")
        self.assertIn("An ancient portal", changes)
        self.assertNotIn(PHRASE, changes.lower())

    def test_the_level_keyword_is_unchanged(self):
        table = read("src/sp_lev.c")
        self.assertIn('{ "magic portal", MAGIC_PORTAL }', table)
        for rel in (
            "dat/tut-1.lua",
            "dat/tut-2.lua",
            "dat/jacob.lua",
        ):
            self.assertIn('type = "magic portal"', read(rel))

    def test_no_player_visible_magic_portal_remains(self):
        leftovers = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(".git/") or "/.git/" in rel:
                continue
            if path.suffix not in (
                ".c", ".h", ".lua", ".txt", ".mn", ".tex", ".js",
            ):
                continue
            text = path.read_text(errors="replace")
            if PHRASE not in text.lower():
                continue
            if rel.startswith("doc/fixes"):
                continue
            if rel.startswith("src/tile"):
                continue
            if rel == "win/share/other.txt":
                continue
            if rel == "tools/feature_def.js":
                # The editor writes this string into a level as the trap
                # type. It has to match the compiler keyword.
                continue
            if path.suffix in (".c", ".h"):
                stripped = strip_c_comments(text)
                stripped = stripped.replace(
                    '{ "magic portal", MAGIC_PORTAL }', "")
                if PHRASE in stripped.lower():
                    leftovers.append(rel)
                continue
            if path.suffix == ".lua":
                stripped = strip_lua_comments(text)
                stripped = stripped.replace('type = "magic portal"', "")
                stripped = stripped.replace('type="magic portal"', "")
                if PHRASE in stripped.lower():
                    leftovers.append(rel)
                continue
            leftovers.append(rel)
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
