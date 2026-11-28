#!/usr/bin/env python3
"""Peter's tome cutscene: two 32-frame scenes, then the rest of the text."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PeterCutsceneTests(unittest.TestCase):
    def test_frame_tables(self):
        frames = (ROOT / "src/peterframes.c").read_text()
        self.assertIn("#define PETER_READ_FRAMES 32", frames)
        self.assertIn("#define PETER_PRAY_FRAMES 32", frames)
        self.assertIn("static const int peter_read_off[33]", frames)
        self.assertIn("static const int peter_pray_off[33]", frames)
        self.assertIn("peter_read_blob", frames)
        self.assertIn("peter_pray_blob", frames)
        # Magenta and bright magenta are not frame colors.
        self.assertNotIn("CLR_MAGENTA", frames)
        self.assertNotIn("CLR_BRIGHT_MAGENTA", frames)

    def test_sequence(self):
        endcut = (ROOT / "src/endcut.c").read_text()
        body = endcut.split("peter_dim_color(int color, int step)", 1)[1]
        body = body.split("endcut_play_frames", 1)[0]
        play = body.split("peter_tome_cutscene(void)", 1)
        self.assertEqual(len(play), 2)
        seq = play[1]
        read_a = seq.find("peter_play_scene(PETER_SCENE_READ, 150)")
        fade_to_pray = seq.find("peter_fade(PETER_SCENE_READ, PETER_SCENE_PRAY)")
        pray = seq.find("peter_play_scene(PETER_SCENE_PRAY, 200)")
        fade_back = seq.find("peter_fade(PETER_SCENE_PRAY, PETER_SCENE_READ)")
        read_b = seq.find("peter_play_scene(PETER_SCENE_READ, 150)", read_a + 1)
        self.assertGreaterEqual(read_a, 0)
        self.assertLess(read_a, fade_to_pray)
        self.assertLess(fade_to_pray, pray)
        self.assertLess(pray, fade_back)
        self.assertLess(fade_back, read_b)
        self.assertEqual(seq.count("loop < 2"), 2)
        self.assertIn("endcut_begin_scene()", seq)
        self.assertIn("endcut_wait(ms)", play[0])
        self.assertIn("tty_endcut_flush()", play[0])
        self.assertIn("endcut_flush_keys", endcut)
        self.assertNotIn("CLR_MAGENTA", body)
        self.assertNotIn("CLR_BRIGHT_MAGENTA", body)

    def test_between_paragraphs(self):
        sounds = (ROOT / "src/sounds.c").read_text()
        night = "and oft thou hearest him praying in the night."
        seventh = "On the seventh day he cometh to thee, and his look is grave."
        call = "peter_tome_cutscene();"
        self.assertLess(sounds.find(night), sounds.find(call))
        self.assertLess(sounds.find(call), sounds.find(seventh))
        # The call is inside the grimoire chat, before the book is used up.
        block = sounds.split("carrying(GRAND_GRIMOIRE)", 1)[1]
        block = block.split("goodground_trial_done()", 1)[0]
        self.assertLess(block.find(night), block.find(call))
        self.assertLess(block.find(call), block.find(seventh))
        self.assertIn(seventh, block)
        self.assertIn("useup(book)", block)


if __name__ == "__main__":
    unittest.main()
