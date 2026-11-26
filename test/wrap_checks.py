#!/usr/bin/env python3
"""Long RighteousHack text is folded, not cut off at the buffer."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

CUSTOM = (
    "src/wayside.c",
    "src/goodground.c",
    "src/stony.c",
    "src/thorns.c",
    "src/steal.c",
    "src/heaven.c",
    "src/endcut.c",
    "src/hinnom.c",
    "src/pray.c",
    "src/artifact.c",
)

WRAP_NEAR = (
    "wayside_screen",
    "rh_text_window",
    "endcut_card",
    "rh_putstr",
    "hinnom_screen",
    "pline",
    "You(",
    "verbalize",
)


def c_literals(src):
    """Yield (start_index, decoded_text) for each C string literal."""
    i = 0
    n = len(src)
    while i < n:
        if src[i] != '"':
            i += 1
            continue
        start = i
        i += 1
        chars = []
        while i < n:
            if src[i] == "\\":
                nxt = src[i + 1] if i + 1 < n else ""
                chars.append("\n" if nxt == "n" else nxt)
                i += 2
                continue
            if src[i] == '"':
                i += 1
                break
            chars.append(src[i])
            i += 1
        yield start, "".join(chars)


def const_name(src, pos):
    """Name of a const char array whose literal begins at pos."""
    i = pos
    while i > 0:
        while i > 0 and src[i - 1] in " \t\n\r":
            i -= 1
        if i > 0 and src[i - 1] == '"':
            i -= 1
            while i > 0 and not (src[i - 1] == '"' and src[i - 2:i - 1] != "\\"):
                i -= 1
            if i > 0:
                i -= 1
            continue
        break
    head = src[max(0, i - 100):i]
    match = re.search(r"(\w+)\s*\[\s*\]\s*=\s*$", head)
    return match.group(1) if match else ""


def take_folded(text, width):
    """Same fold as questpgr.c take_folded. A space before a newline
    is not a blank line. A blank line in the source stays one blank."""
    lines = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\n":
            lines.append("")
            i += 1
            continue
        end = i
        while end < n and text[end] != "\n" and end - i < width:
            end += 1
        cut = end
        if end < n and text[end] != "\n":
            while cut > i and text[cut] != " ":
                cut -= 1
            if cut <= i:
                cut = end
        while cut > i and text[cut - 1] == " ":
            cut -= 1
        if cut <= i:
            cut = end if end > i else i + 1
        if cut - i > width:
            cut = i + width
        lines.append(text[i:cut])
        i = cut
        while i < n and text[i] == " ":
            i += 1
        if i < n and text[i] == "\n":
            i += 1
    return lines


def wrap_para(text, cols):
    lines = []
    for para in text.split("\n"):
        while len(para) > cols:
            n = cols
            while n > 0 and para[n] != " ":
                n -= 1
            if n <= 0:
                n = para.find(" ")
                if n < 0:
                    n = len(para)
            lines.append(para[:n])
            para = para[n:]
            if para.startswith(" "):
                para = para[1:]
        lines.append(para)
    return lines


class Wrap(unittest.TestCase):
    def test_fold_keeps_every_word(self):
        believer = (
            "The young believer turneth to thee with tears in his eyes. "
            "'I would have perished in my haste. But let patience have her "
            "perfect work, that ye may be perfect and entire, wanting "
            "nothing. Thou hast taught me patience, and now my faith hath "
            "taken root. I thank thee, friend.'"
        )
        self.assertGreater(len(believer), 254)
        shown = wrap_para(believer, 79)
        for line in shown:
            self.assertLessEqual(len(line), 79)
            self.assertFalse(line.endswith(" ") and line[:-1].endswith(" "))
        self.assertEqual(" ".join(shown).split(), believer.split())
        self.assertIn("I thank thee, friend.", " ".join(shown))

    def test_a_space_before_a_newline_is_not_a_blank_line(self):
        intro = (
            "As you wander the windswept hills, you come upon the mouth \n"
            "of an ancient cave. The entrance is hewn smooth, as though "
            "by no human hand, \n"
            "and upon the rock above the opening these words are engraved."
        )
        shown = take_folded(intro, 100)
        self.assertEqual(shown, [
            "As you wander the windswept hills, you come upon the mouth",
            "of an ancient cave. The entrance is hewn smooth, as though "
            "by no human hand,",
            "and upon the rock above the opening these words are engraved.",
        ])
        self.assertNotIn("", shown)
        # A real paragraph break stays a single blank line.
        self.assertEqual(
            take_folded("One sentence.\n\nTwo sentences.", 80),
            ["One sentence.", "", "Two sentences."])
        # A long line folds on a space and does not invent a blank.
        long = ("bretheren " * 12).strip()
        folded = take_folded(long, 30)
        self.assertTrue(all(folded))
        self.assertTrue(all(len(line) <= 30 for line in folded))
        quest = (ROOT / "src" / "questpgr.c").read_text()
        folder = quest.split("take_folded(", 1)[1].split(
            "deliver_by_pline(", 1)[0]
        self.assertIn("while (*s == ' ')", folder)
        self.assertIn("if (*s == '\\n')", folder)
        self.assertNotIn("if (*s == ' ' || *s == '\\n')", folder)
        endcut = (ROOT / "src" / "endcut.c").read_text()
        self.assertIn("cols = CO - 1", endcut)
        tty = (ROOT / "win" / "tty" / "wintty.c").read_text()
        self.assertIn("(CO > 20) ? CO - 1 : 79", tty)

    def test_the_display_paths_fold(self):
        endcut = (ROOT / "src" / "endcut.c").read_text()
        wayside = (ROOT / "src" / "wayside.c").read_text()
        hinnom = (ROOT / "src" / "hinnom.c").read_text()
        pline = (ROOT / "src" / "pline.c").read_text()
        tty = (ROOT / "win" / "tty" / "wintty.c").read_text()
        quest = (ROOT / "src" / "questpgr.c").read_text()
        self.assertIn("rh_text_window(text)", wayside)
        self.assertIn("rh_text_window(text)", endcut)
        self.assertIn("rh_putstr(win, 0, para[i])", hinnom)
        self.assertIn("Fold at a space into successive messages", pline)
        self.assertNotIn("extremely l...ext", pline)
        self.assertIn("cw->type == NHW_TEXT || cw->type == NHW_MENU", tty)
        self.assertLess(
            tty.index("cw->type == NHW_TEXT || cw->type == NHW_MENU"),
            tty.index("str = compress_str(str)"))
        self.assertIn("take_folded", quest)

    def test_long_custom_text_uses_a_wrapping_call(self):
        missed = []
        for rel in CUSTOM:
            src = (ROOT / rel).read_text()
            for pos, text in c_literals(src):
                if len(text) <= 200:
                    continue
                window = src[max(0, pos - 400):pos + 1800]
                if any(name in window for name in WRAP_NEAR):
                    continue
                name = const_name(src, pos)
                if name and (
                    ("endcut_card(" + name) in src
                    or ("wayside_screen(" + name) in src
                    or ("rh_text_window(" + name) in src
                    or ("hinnom_screen(" in src)
                ):
                    continue
                missed.append("%s (%d chars): %s"
                              % (rel, len(text), text[:60].replace("\n", " ")))
        self.assertEqual(missed, [])


if __name__ == "__main__":
    unittest.main()
