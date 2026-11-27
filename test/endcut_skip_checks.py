#!/usr/bin/env python3
"""A key left over from a text card must not skip the next cutscene."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def body_after(src, signature, stop):
    return src.split(signature, 1)[1].split(stop, 1)[0]


class EndcutSkip(unittest.TestCase):
    def test_every_scene_flushes_before_it_waits(self):
        src = read("src/endcut.c")
        self.assertIn("endcut_flush_keys();", body_after(
            src, "endcut_begin_scene(void)", "endcut_wait(int ms)"))
        for signature, stop in (
            ("endcut_play(int seq)", "endcut_frame_at"),
            ("endcut_altar_scene(boolean harm)", "endcut_reveal"),
            ("endcut_lucifer_at(coordxy x", "endcut_reveal"),
            ("endcut_memorial(winid extra", "TTY_GRAPHICS"),
        ):
            part = body_after(src, signature, stop)
            self.assertIn("endcut_begin_scene()", part, signature)
        wait = body_after(src, "endcut_wait(int ms)", "endcut_wait_ms")
        exact = body_after(src, "endcut_wait_ms(int ms)", "rh_text_cols")
        self.assertIn("endcut_key_ready()", wait)
        self.assertIn("endcut_key_ready()", exact)

    def test_windows_ignores_keyup_and_nonkeys(self):
        src = read("src/endcut.c")
        ready = body_after(src, "endcut_key_ready(void)", "endcut_flush_keys")
        self.assertIn("win32_key_pending()", ready)
        self.assertNotIn("kbhit()", ready.split("#elif defined(MICRO)", 1)[0])
        flush = body_after(src, "endcut_flush_keys(void)", "endcut_begin_scene")
        self.assertIn("win32_flush_keys()", flush)
        self.assertIn("tcflush(fd, TCIFLUSH)", flush)
        win = read("sys/windows/windsys.c")
        pending = body_after(win, "win32_key_pending(void)", "win32_abort")
        real = body_after(win, "win32_is_real_key(", "win32_key_pending")
        self.assertIn("FlushConsoleInputBuffer", win)
        self.assertIn("!key->bKeyDown", real)
        self.assertIn("ir.EventType == KEY_EVENT", pending)
        self.assertIn("ReadConsoleInput", pending)
        self.assertIn("#define EDITLEVEL 20", read("include/patchlevel.h"))


if __name__ == "__main__":
    unittest.main()
