#!/usr/bin/env python3
"""Wish-name checks for the Helmet of Salvation.

The live game's wish parser is large, so this file repeats the two
rules that decide these strings and checks that the sources still
implement them:

* a full artifact name is accepted before any armor type is chosen
* "helmet" is rewritten to "helm" without calling itself on the
  same text, including when the user capitalizes Helmet
"""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
OBJNAM = (ROOT / "src" / "objnam.c").read_text()
ARTI = (ROOT / "include" / "artilist.h").read_text()
OBJECTS = (ROOT / "include" / "objects.h").read_text()
HACK = (ROOT / "src" / "hack.c").read_text()

ART = "Helmet of Salvation"
ORDINARY = [
    "helmet",
    "helm of brilliance",
    "helm of telepathy",
    "helm of opposite alignment",
    "dwarvish iron helm",
    "crystal helmet",
    "plumed helmet",
    "crested helmet",
    "visored helmet",
    "etched helmet",
]


def fuzzymatch(s1, s2):
    i = j = 0
    ignore = set(" -")
    while True:
        while i < len(s1) and s1[i] in ignore:
            i += 1
        while j < len(s2) and s2[j] in ignore:
            j += 1
        if i >= len(s1) or j >= len(s2):
            break
        if s1[i].lower() != s2[j].lower():
            return False
        i += 1
        j += 1
    return i >= len(s1) and j >= len(s2)


def rewrite_helmet(user):
    low = user.lower()
    at = low.find("helmet")
    if at < 0:
        return user
    return user[:at] + "helm" + user[at + len("helmet"):]


def wishymatch(user, catalog, inverted=True, depth=0):
    """The helm half of wishymatch(), including the guarded rewrite."""
    if depth > 4:
        raise AssertionError("wishymatch recursed on an unchanged helmet string")
    if fuzzymatch(user, catalog):
        return True
    if "helm" in catalog.lower() and "helmet" in user.lower():
        rewritten = rewrite_helmet(user)
        if rewritten != user:
            return wishymatch(rewritten, catalog, True, depth + 1)
    if inverted:
        u_of = user.lower().find(" of ")
        o_of = catalog.lower().find(" of ")
        if u_of >= 0 and o_of < 0:
            flipped = user[u_of + 4:] + " " + user[:u_of]
            if fuzzymatch(flipped, catalog):
                return True
        elif o_of >= 0 and u_of < 0:
            flipped = catalog[o_of + 4:] + " " + catalog[:o_of]
            if fuzzymatch(user, flipped):
                return True
    return False


def artifact_wish(text):
    """Stock prefix stripping, then a full-string artifact match."""
    name = " ".join(text.split())
    while True:
        low = name.lower()
        cut = None
        for prefix in (
            "the ", "a ", "an ", "blessed ", "cursed ", "uncursed ",
            "holy ", "unholy ",
        ):
            if low.startswith(prefix):
                cut = len(prefix)
                break
        if cut is None and name[:1] in "+-" and len(name) > 1 and name[1].isdigit():
            i = 1
            while i < len(name) and name[i].isdigit():
                i += 1
            while i < len(name) and name[i] == " ":
                i += 1
            name = name[i:]
            continue
        if cut is None:
            break
        name = name[cut:]
    return fuzzymatch(name, ART)


class HelmetWishTests(unittest.TestCase):
    def test_artifact_name_and_base_type(self):
        self.assertIn('A("Helmet of Salvation", DIVINE_COVERING,', ARTI)
        self.assertNotIn("Cap of Salvation", ARTI)
        self.assertNotIn("cap of salvation", (ROOT / "dat" / "Kni-strt.lua").read_text())
        self.assertIn('name = "Helmet of Salvation"', (ROOT / "dat" / "Kni-strt.lua").read_text())
        self.assertIn("uarmh->oartifact == ART_HELMET_OF_SALVATION", HACK)
        self.assertIn('HELM("helmet", "plumed helmet"', OBJECTS)
        self.assertIn('HELM("helm of brilliance"', OBJECTS)
        self.assertIn('HELM("helm of telepathy"', OBJECTS)
        self.assertIn('HELM("helm of opposite alignment"', OBJECTS)
        self.assertIn('HELM("dwarvish iron helm"', OBJECTS)
        self.assertIn('HELM("divine covering"', OBJECTS)

    def test_artifact_is_matched_before_object_type(self):
        body = OBJNAM.split("readobjnam_postparse3(", 1)[1]
        self.assertLess(body.index("artifact_name"), body.index("rnd_otyp_by_namedesc"))
        rewrite = OBJNAM.split('strstri(o_str, "helm")', 1)[1][:800]
        self.assertIn("strstri(buf, \"helmet\")", rewrite)
        self.assertIn("if (strcmp(buf, u_str))", rewrite)

    def test_full_artifact_wish_is_not_a_normal_helm(self):
        wishes = [
            "Helmet of Salvation",
            "helmet of salvation",
            "HELMET OF SALVATION",
            "the Helmet of Salvation",
            "blessed Helmet of Salvation",
            "+2 Helmet of Salvation",
            "blessed +2 the Helmet of Salvation",
        ]
        for wish in wishes:
            self.assertTrue(artifact_wish(wish), wish)
            bare = wish
            for prefix in ("blessed +2 the ", "blessed ", "the ", "+2 "):
                if bare.lower().startswith(prefix):
                    bare = bare[len(prefix):]
            for catalog in ORDINARY:
                self.assertFalse(
                    wishymatch(bare, catalog),
                    "%s must not be %s" % (wish, catalog),
                )

    def test_ordinary_helm_wishes_stay_ordinary(self):
        pairs = [
            ("helmet", "helmet"),
            ("Helmet", "helmet"),
            ("helmet of brilliance", "helm of brilliance"),
            ("Helmet of brilliance", "helm of brilliance"),
            ("helm of brilliance", "helm of brilliance"),
            ("helm of telepathy", "helm of telepathy"),
            ("helmet of telepathy", "helm of telepathy"),
            ("helm of opposite alignment", "helm of opposite alignment"),
            ("helmet of opposite alignment", "helm of opposite alignment"),
            ("dwarvish iron helm", "dwarvish iron helm"),
            ("crystal helmet", "crystal helmet"),
        ]
        for user, catalog in pairs:
            self.assertTrue(wishymatch(user, catalog), "%s -> %s" % (user, catalog))
            self.assertFalse(artifact_wish(user), user)
        self.assertFalse(wishymatch("helmet", "helm of brilliance"))
        self.assertFalse(wishymatch("helm of brilliance", "helm of telepathy"))
        self.assertFalse(wishymatch("helmet", "Helmet of Salvation"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HelmetWishTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
