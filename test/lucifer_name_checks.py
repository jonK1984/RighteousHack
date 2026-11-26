#!/usr/bin/env python3
"""Lucifer is a proper name, not a red dragon with a calling."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def between(src, start, end):
    return src.split(start, 1)[1].split(end, 1)[0]


class LuciferName(unittest.TestCase):
    def test_looking_and_combat_use_different_names(self):
        body = between(read("src/do_name.c"),
                       "x_monnam(", "l_monnam(")
        arm = between(body, "else if (is_lucifer(mtmp))",
                      "else if (do_name && has_mgivenname(mtmp))")
        self.assertLess(body.index("is_lucifer(mtmp)"),
                        body.index('"%s called %s"'))
        self.assertIn('called ? "Lucifer (The Great Dragon)" : "Lucifer"',
                      arm)
        self.assertNotIn("called %s", arm)
        self.assertNotIn("red dragon", arm)
        self.assertIn("name_at_start = TRUE", arm)

    def test_death_does_not_call_him_a_dragon(self):
        body = between(read("src/end.c"), "done_in_by(", "svk.killer.name")
        arm = between(body, "if (is_lucifer(mtmp))", "else if (imitator)")
        self.assertIn('Strcat(buf, "Lucifer")', arm)
        self.assertIn("svk.killer.format = KILLED_BY", arm)
        self.assertNotIn("called", arm)
        self.assertLess(body.index("is_lucifer(mtmp)"),
                        body.index('"called"'))

    def test_the_stored_name_is_lucifer(self):
        heaven = read("src/heaven.c")
        self.assertIn('#define LUCIFER_NAME "Lucifer"', heaven)
        self.assertNotIn("Lucifer (The Great Dragon)", heaven)
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))
        self.assertIn("Angel of the Lord", read("src/do_name.c"))


if __name__ == "__main__":
    unittest.main()
