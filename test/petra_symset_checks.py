#!/usr/bin/env python3
"""PETRA letters and fig trees survive Unicode and DEC symsets."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


class PetraSymsetTests(unittest.TestCase):
    def test_letter_clears_unicode(self):
        display = read("src/display.c")
        body = display.split("petra_map_letter(x, y)", 1)[1]
        body = body.split("glyphinfo->glyph = glyph", 1)[0]
        self.assertIn("glyphinfo->ttychar = letter", body)
        self.assertNotIn("| 0x80", body)
        self.assertNotIn("|0x80", body)
        self.assertIn("glyphinfo->gm.u = (struct unicode_representation *) 0", body)

    def test_fig_tree_uses_tree_unicode(self):
        display = read("src/display.c")
        fig = display.split("goodground_fig(x, y)", 1)[1]
        fig = fig.split("petra_map_letter", 1)[0]
        self.assertIn("S_tree + SYM_OFF_P", fig)
        self.assertIn("gs.showsyms[glyphinfo->gm.sym.symidx]", fig)
        self.assertIn("glyphinfo->gm.u = glyphmap[cmap_to_glyph(S_tree)].u", fig)

    def test_ports_prefer_unicode_then_ttychar(self):
        tty = read("win/tty/wintty.c")
        draw = tty.split("tty_print_glyph(", 1)[1].split("g_putch(ch)", 1)[0]
        self.assertIn("glyphinfo->gm.u->utf8str", draw)
        self.assertIn("g_pututf8(glyphinfo->gm.u->utf8str)", draw)
        console = read("sys/windows/consoletty.c")
        self.assertIn("void\ng_pututf8(uint8 *sequence)", console)
        self.assertIn("console_g_putch(int in_ch)", console)
        curses = read("win/curses/cursmain.c")
        put = curses.split("curses_print_glyph(", 1)[1].split("curses_raw_print(", 1)[0]
        self.assertLess(
            put.find("curses_convert_glyph(ch, glyph)"),
            put.find("curses_putch("),
        )
        self.assertIn("glyphinfo->gm.u : NULL", put)
        convert = read("win/curses/cursmisc.c").split("curses_convert_glyph(", 1)[1]
        convert = convert.split("ch &= 0xff", 1)[1].split("return ch", 1)[0]
        self.assertIn("!(ch & 0x80)", convert)


if __name__ == "__main__":
    unittest.main()
