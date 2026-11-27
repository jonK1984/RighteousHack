#!/usr/bin/env python3
"""#invoke on the Lamp of God's Word. Seven verbatim bearings."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

NOT_HELL = (
    "The flame of the lamp leaneth low toward the deep. Thou must storm "
    "the gates of Gehennom, and the Lord's light shall shine forth in the "
    "darkness; thy path lieth there."
)
FAR = (
    "The flame bendeth hard downward. Thou must go much further down, "
    "for the way is yet long."
)
NEAR = (
    "The flame burneth brighter. Only a little further, but downward still."
)
ONE = (
    "The flame trembleth and pointeth straight down. Only one more level "
    "downward."
)
SQUARE = (
    "The entrance to the great Sanctum of evil is within thy reach! "
    "It is hidden, but the light of the Lord will show thee the way."
)
SANCTUM = (
    "Make thy way to the altar of evil. A great choice lieth before thee."
)
ROAD = (
    "Make thy way to the top of this great cave. The throne of heaven "
    "awaiteth thee!"
)


def read(rel):
    return (ROOT / rel).read_text()


class LampInvokeTests(unittest.TestCase):
    def test_seven_states_and_the_wayside_burst(self):
        apply = read("src/apply.c")
        art = read("src/artifact.c")
        wayside = read("src/wayside.c")
        chunk = apply.split("lamp_levels_above_invocation(void)", 1)[1]
        chunk = chunk.split("light_cocktail", 1)[0]
        body = chunk.split("invoke_word_lamp(struct obj *obj)", 1)[1]
        for line in (NOT_HELL, FAR, NEAR, ONE, SQUARE, SANCTUM, ROAD):
            self.assertIn(line, body)
            self.assertNotIn("\u2014", line)
        self.assertLess(body.index("wayside_road()"), body.index("Is_sanctum"))
        self.assertLess(body.index("Is_sanctum"), body.index("!Inhell"))
        self.assertLess(body.index("!Inhell"), body.index("Invocation_lev"))
        self.assertLess(body.index("Invocation_lev"), body.index("above > 5"))
        self.assertLess(body.index("above > 5"), body.index("above >= 2"))
        self.assertLess(body.index("above >= 2"), body.index("above == 1"))
        self.assertIn(
            "wayside_entrance_burst(svi.inv_pos.x, svi.inv_pos.y)", body)
        self.assertLess(body.index(SQUARE),
                        body.index("wayside_entrance_burst"))
        self.assertNotIn("open_gate", body)
        self.assertNotIn("obj->age", body)
        self.assertIn("sanctum_level.dlevel - 1", chunk)
        ok = art.split("invoke_ok(struct obj *obj)", 1)[1]
        ok = ok.split("doinvoke", 1)[0]
        self.assertIn("LAMP_OF_GODS_WORD", ok)
        invoke = art.split("arti_invoke(struct obj *obj)", 1)[1]
        invoke = invoke.split("It's a special power", 1)[0]
        self.assertIn("return invoke_word_lamp(obj);", invoke)
        burst = wayside.split("wayside_entrance_burst(coordxy x, coordxy y)", 1)[1]
        burst = burst.split("forget_stair", 1)[0]
        self.assertIn("play_gate_burst(x, y, FALSE)", burst)
        self.assertNotIn("open_gate", burst)
        shared = wayside.split("play_gate_burst(coordxy cx", 1)[1]
        shared = shared.split("dissipate_gate", 1)[0]
        self.assertIn("if (open_center && frame == 3)", shared)
        self.assertIn("flush_screen(1)", shared)
        self.assertIn("nh_delay_output", shared)
        self.assertIn("flags.nap", shared)


if __name__ == "__main__":
    unittest.main()
