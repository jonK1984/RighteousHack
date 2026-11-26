#!/usr/bin/env python3
"""Player-visible text no longer says atheist or genocide.

The scroll stays 'judgement to the wicked'. The save still has
u.uconduct.gnostic. The disclose g key stays. The command is #banished.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Whole string literals that are file-format or command names, not prose.
ALLOW = {
    "atheist",
    "genocideless",
    "genocided",
    "is_genocided",
}


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
        out.append(src[i])
        i += 1
    return "".join(out)


def c_strings(src):
    found = []
    i = 0
    n = len(src)
    while i < n:
        if src[i] != '"':
            i += 1
            continue
        i += 1
        chars = []
        while i < n:
            c = src[i]
            if c == "\\":
                chars.append(src[i:i + 2])
                i += 2
                continue
            if c == '"':
                i += 1
                break
            chars.append(c)
            i += 1
        found.append("".join(chars))
    return found


class Wording(unittest.TestCase):
    def test_no_player_visible_atheist_or_genocide(self):
        bad = []
        for path in (ROOT / "src").glob("*.c"):
            text = strip_c_comments(path.read_text(errors="replace"))
            for lit in c_strings(text):
                low = lit.lower()
                if "genocid" not in low and "atheist" not in low:
                    continue
                if lit in ALLOW:
                    continue
                bad.append("%s: %s" % (path.name, lit))
        for path in (ROOT / "dat").glob("*"):
            if path.suffix == ".txt":
                low = path.read_text(errors="replace").lower()
                if "genocid" in low or "atheist" in low:
                    bad.append(path.name)
            elif path.suffix in (".lua", ".base"):
                for lit in c_strings(path.read_text(errors="replace")):
                    low = lit.lower()
                    if "genocid" in low or "atheist" in low:
                        bad.append("%s: %s" % (path.name, lit))
        self.assertEqual(bad, [])

    def test_the_scroll_name_and_the_save_field_stay(self):
        objects = (ROOT / "include" / "objects.h").read_text()
        self.assertIn(
            'SCROLL("judgement to the wicked"', objects)
        you = (ROOT / "include" / "you.h").read_text()
        self.assertIn("long gnostic;", you)
        self.assertIn("#define EDITLEVEL 20",
                      (ROOT / "include" / "patchlevel.h").read_text())
        self.assertNotIn("\u2014", "You never banished any monsters")
        self.assertNotIn("\u2014", "What monster do you want to banish?")

    def test_the_command_is_banished(self):
        cmd = (ROOT / "src" / "cmd.c").read_text()
        self.assertIn(
            '"banished",\n'
            '              "list monsters that have been banished or become extinct"',
            cmd)
        self.assertNotIn('"genocided"', cmd)
        hh = (ROOT / "dat" / "hh").read_text()
        self.assertIn(
            "M-g   banished  list monsters that have been banished or become extinct",
            hh)
        self.assertNotIn("genocided", hh)
        self.assertIn(
            'const char disclosure_options[] = "iavgco";',
            (ROOT / "src" / "decl.c").read_text())


if __name__ == "__main__":
    unittest.main()
