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
    """Same fold as rh_putstr. A space before a newline is not a blank
    line. An empty piece, from a blank line in the source, stays one
    blank. Trailing spaces are not shown."""
    lines = []
    for raw in text.split("\n"):
        para = raw.rstrip(" ")
        if not para:
            if raw == "":
                lines.append("")
            continue
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
            "For a moment there is silence in heaven.",
            "Then the voice of a trumpet soundeth, exceeding loud, and all of heaven trembleth at the sound thereof.",
            "The fallen angels are smitten where they stand; their weapons fall from their hands, and they are made still as stone, and cannot flee.",
            "Lucifer, that old serpent, called the Devil and Satan, which deceiveth the whole world, lifteth up his voice in rage, but it availeth him nothing.",
            "The spiritual chains that bound thy soul in the Sanctum of the Great Dragon break asunder, and are rendered as dust.",
            "Well done, thou good and faithful servant. Thou hast been faithful over a few things; I will make thee ruler over many things. Enter thou into the joy of thy Lord.",
            "Thy soul is free. Thou art redeemed, and thou art home.",
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
        # Windows tty does not link the Unix helper. Only the VMS
        # branch may name it.
        self.assertNotIn("msleep", src.split("#elif defined(VMS)", 1)[0])
        self.assertIn("Delay(", src)
        self.assertIn("nanosleep", src)
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

    def test_altar_card_has_three_paragraphs(self):
        text = c_text(read("src/endcut.c"), "win_a_rest[]")
        paras = text.split("\n\n")
        self.assertEqual(paras, [
            "For a moment there is silence in heaven.",
            "Then the voice of a trumpet soundeth, exceeding loud, and all of heaven trembleth at the sound thereof. And the altar is filled with the glory of the Lord, and a sound goeth forth from the throne as of a mighty thunder, and the whole field of heaven is shaken. A great and terrible light breaketh out from the presence of the Lord, as a fire that consumeth, and it goeth forth over all the host of the Great Dragon.",
            "The fallen angels are smitten where they stand; their weapons fall from their hands, and they are made still as stone, and cannot flee. And slowly, before thine eyes, they are turned to dust, and the wind of the Lord carrieth them away, and their place is found no more.",
        ])
        self.assertNotIn(" \n", text)
        self.assertFalse(any(p.endswith(" ") or p.startswith(" ") for p in paras))
        shown = wrap_card(text, 79)
        blanks = [i for i, line in enumerate(shown) if line == ""]
        self.assertEqual(len(blanks), 2)
        self.assertGreater(blanks[1], blanks[0] + 1)
        self.assertTrue(all(line == line.rstrip(" ") for line in shown))
        # A space before a newline does not become its own blank line.
        spaced = wrap_card("mouth \nof an ancient cave.", 40)
        self.assertEqual(spaced, ["mouth", "of an ancient cave."])
        self.assertEqual(
            wrap_card("One sentence.\n\nTwo sentences.", 40),
            ["One sentence.", "", "Two sentences."])

    def test_ascension_title_is_the_faithful(self):
        end = read("src/end.c")
        farewell = end.split("Goodbye(), svp.plname", 1)[1]
        farewell = farewell.split("dump_forward_putstr", 1)[0]
        self.assertIn('"Faithful"', farewell)
        self.assertNotIn("Demigod", farewell)
        self.assertNotIn("Demigoddess", farewell)
        # The same line is what the dumplog receives.
        self.assertIn("dump_forward_putstr(endwin, 0, pbuf", end)
        topten = read("src/topten.c")
        self.assertIn("ascended as the Faithful", topten)
        self.assertNotIn("demigod", topten)
        self.assertNotIn("Demigod", topten)
        pray = read("src/pray.c")
        self.assertEqual(pray.count("ascend to the status of the Faithful"), 2)
        self.assertNotIn("Demigod", pray)
        self.assertNotIn("demigod-hood", pray)
        self.assertIn("udemigod", pray)

    def test_dragon_card_has_three_paragraphs(self):
        text = c_text(read("src/endcut.c"), "dragon_text[]")
        self.assertTrue(text.startswith('"') and text.endswith('"'))
        paras = text[1:-1].split("\n\n")
        self.assertEqual(paras, [
            "Thou foolishly layest thy soul upon the altar of the Great Dragon. The stone of the altar groweth cold beneath thy hand, and the light of heaven beginneth to dim.",
            "Lucifer, that old serpent, called the Devil and Satan, the deceiver which deceiveth the whole world, laugheth, and thou feelest the chains from the floor rising up to close upon thy soul once more.",
            "Thou art pulled down into outer darkness, where there is weeping and gnashing of teeth.",
        ])
        self.assertNotIn(" \n", text)
        self.assertNotIn("\u2014", text)
        shown = wrap_card(text, 79)
        blanks = [i for i, line in enumerate(shown) if line == ""]
        self.assertEqual(len(blanks), 2)
        self.assertGreater(blanks[1], blanks[0] + 1)
        self.assertTrue(all(line == line.rstrip(" ") for line in shown))

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
        scene = src.split("endcut_altar_scene(boolean harm)", 1)[1].split(
            "endcut_stamp_lucifer", 1)[0]
        self.assertIn("endcut_reveal()", scene)
        self.assertIn("endcut_show()", scene)
        self.assertIn("endcut_wait_ms(", scene)
        compose = src.split("endcut_compose(int shx", 1)[1].split(
            "endcut_restore_burst", 1)[0]
        self.assertNotIn("docrt()", compose)


if __name__ == "__main__":
    unittest.main()
