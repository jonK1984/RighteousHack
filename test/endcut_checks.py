#!/usr/bin/env python3
"""Locked endgame lines, and prophet-mode gating for #proanimate."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


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


if __name__ == "__main__":
    unittest.main()
