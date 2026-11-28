#!/usr/bin/env python3
"""Wilderness food that may still be on the floor is not useup()'d."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class WildernessEatTests(unittest.TestCase):
    def test_floor_food_is_useupf(self):
        eat = (ROOT / "src/eat.c").read_text()
        loaf = eat.split('ONAME(otmp), "loaf of bread"', 1)[1]
        loaf = loaf.split("in_wilderness()", 1)[0]
        ash = eat.split("in_wilderness() && dunlev(&u.uz) == 2", 1)[1]
        ash = ash.split("check_capacity", 1)[0]
        self.assertIn(
            "The bread turns to dust in your mouth. You are hungrier than before.",
            loaf,
        )
        self.assertIn("The food turns to ash.", ash)
        for body in (loaf, ash):
            self.assertLess(body.find("if (carried(otmp))"), body.find("useup(otmp)"))
            self.assertLess(body.find("useup(otmp)"), body.find("useupf(otmp, 1L)"))
            self.assertIn("else", body[body.find("useup(otmp)") : body.find("useupf")])

    def test_fig_and_salt_do_not_useup(self):
        eat = (ROOT / "src/eat.c").read_text()
        fig = (ROOT / "src/goodground.c").read_text()
        fig = fig.split("goodground_eat_fig(void)", 1)[1].split("number_list", 1)[0]
        self.assertNotIn("useup(", fig)
        salt = eat.split("lots_wife_statue(otmp)", 1)[1].split("loaf of bread", 1)[0]
        self.assertNotIn("useup(", salt)


if __name__ == "__main__":
    unittest.main()
