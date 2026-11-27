#!/usr/bin/env python3
"""Locked endgame lines, and prophet-mode gating for #proanimate."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def c_text(src, marker):
    body = src.split(marker, 1)[1]
    out = []
    i = 0
    in_lit = False
    while i < len(body):
        c = body[i]
        if not in_lit:
            if c == ";":
                break
            if c == '"':
                in_lit = True
            i += 1
            continue
        if c == "\\":
            n = body[i + 1]
            out.append("\n" if n == "n" else n)
            i += 2
            continue
        if c == '"':
            in_lit = False
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def wrap_card(text, cols):
    """Same fold as endcut_put_wrapped: spaces only, blank lines kept."""
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


class Endcut(unittest.TestCase):
    def test_locked_lines(self):
        src = read("src/endcut.c")
        lines = (
            "Thou offerest thy soul up to the Lord... a heart submitted to the will of God Most High...",
            "For a moment there is silence in heaven. Then the voice of a trumpet soundeth, exceeding loud, and all of heaven trembleth at the sound thereof.",
            "Lucifer, that old serpent, called the Devil and Satan, which deceiveth the whole world, lifteth up his voice in rage, but it availeth him nothing.",
            "The chains that bound thee in the Sanctum of the Great Dragon break asunder, and fall as dust about thy feet.",
            "Well done, thou good and faithful servant. Thou hast been faithful over a few things; I will make thee ruler over many things. Enter thou into the joy of thy Lord.",
            "Thy soul is thine again. Thou art redeemed, and thou art home.",
            "Woe unto thee, for thou hast made the gravest of errors.",
            "Thou foolishly layest thy soul upon the altar of the Great Dragon.",
            "Thou fallest upon the field of heaven, and the war goeth on without thee.",
            "went up by a whirlwind into heaven",
            "offered thy soul upon the altar of evil",
            "fell upon the field of heaven",
        )
        for line in lines:
            self.assertIn(line, src)
            self.assertNotIn("\u2014", line)
        self.assertNotIn(
            "Thou layest thy soul upon the altar of the Lord.", src)
        self.assertNotIn("a heart truly submitted", src)

    def test_proanimate_is_prophet_only(self):
        cmd = read("src/cmd.c")
        src = read("src/endcut.c")
        self.assertIn('"proanimate"', cmd)
        self.assertIn("do_proanimate", cmd)
        self.assertIn("WIZMODECMD", cmd[cmd.index('"proanimate"'):
                                        cmd.index('"proanimate"') + 240])
        self.assertIn("if (!wizard)", src)
        self.assertIn("endcut_borrow", src)
        self.assertIn("getlev", src)
        self.assertIn("unlink(endcut_scratch)", src)
        self.assertIn("endcut_testing", src)
        self.assertIn("nh_delay_output", src)
        self.assertIn("fqname(base, LEVELPREFIX, 1)", src)
        self.assertNotIn("msleep", src)
        self.assertNotIn("/tmp/", src)
        self.assertNotIn("getpid", src)
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))

    def test_frames_are_embedded(self):
        frames = read("src/endframes.c")
        self.assertIn("ENDCUT_WIN 0", frames)
        self.assertIn("ENDCUT_DRAGON 1", frames)
        self.assertIn("ENDCUT_DEATH 2", frames)
        self.assertIn("endcut_frame_at", frames)

    def test_cards_wrap_to_the_screen(self):
        src = read("src/endcut.c")
        heaven = read("src/heaven.c")
        cols = 79
        names = (
            "win_a_lead[]",
            "win_a_rest[]",
            "win_c_text[]",
            "win_e_text[]",
            "dragon_voice[]",
            "dragon_text[]",
            "heaven_death_text[]",
        )
        card = src.split("rh_text_window(const char *text)", 1)[1].split(
            "endcut_card(", 1)[0]
        self.assertIn("rh_putstr", card)
        self.assertIn("display_nhwindow(win, TRUE)", card)
        self.assertIn("rh_text_window(text)", src.split(
            "endcut_card(const char *text)", 1)[1][:80])
        self.assertIn("cols = 79", src)
        self.assertIn("CO - 1", src)
        self.assertIn("endcut_card(text)", heaven)
        for name in names:
            text = c_text(src, name)
            shown = wrap_card(text, cols)
            self.assertGreater(len(text), 0)
            for line in shown:
                self.assertLessEqual(len(line), cols, name)
            self.assertEqual("\n".join(shown).split(), text.split())
        host = c_text(heaven, "heaven_host_text[]")
        shown = wrap_card(host, cols)
        for line in shown:
            self.assertLessEqual(len(line), cols)
        self.assertEqual("\n".join(shown).split(), host.split())
        self.assertGreater(len(c_text(src, "win_a_rest[]")), 254)

    def test_the_battlefield_is_shown_before_the_sparks(self):
        src = read("src/endcut.c")
        reveal = src.split("endcut_reveal(void)", 1)[1].split(
            "endcut_find_altar", 1)[0]
        self.assertIn("levl[x][y].lit = 1", reveal)
        self.assertIn("levl[x][y].waslit = 1", reveal)
        self.assertIn("levl[x][y].seenv = SVALL", reveal)
        self.assertIn("endcut_omniscient = TRUE", reveal)
        self.assertIn("map_object(obj, 0)", reveal)
        self.assertIn("magic_map_background(x, y, 1)", reveal)
        self.assertIn("EDetect_monsters |= I_SPECIAL", reveal)
        self.assertIn("mtmp->mundetected = 0", reveal)
        self.assertIn("endcut_show()", reveal)
        show = src.split("endcut_show(void)", 1)[1].split(
            "endcut_sight_off", 1)[0]
        self.assertIn("docrt()", show)
        self.assertIn("flush_screen(1)", show)
        vision = read("src/vision.c")
        self.assertIn("endcut_omniscient && control != 2", vision)
        self.assertIn("IN_SIGHT | COULD_SEE", vision)
        back = src.split("endcut_give_back(coordxy ox", 1)[1].split(
            "struct endcut_keep", 1)[0]
        self.assertIn("endcut_sight_off()", back)
        self.assertIn("endcut_omniscient = FALSE", src)
        self.assertIn("EDetect_monsters = endcut_save_det", src)
        self.assertIn("vision_reset()", back)
        self.assertIn('load_special("astral.lua")', src)
        burst = src.split("endcut_burst(coordxy x", 1)[1].split(
            "endcut_save_det", 1)[0]
        self.assertIn("endcut_show()", burst)
        quake = src.split("endcut_quake(coordxy ax", 1)[1].split(
            "endcut_dist", 1)[0]
        self.assertGreaterEqual(quake.count("endcut_show()"), 2)


if __name__ == "__main__":
    unittest.main()
