#!/usr/bin/env python3
"""The fiery Gibraltar pebble, Peter's forge, and the Luke prayer."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

FORGE = (
    "Peter seeth the pebble from the rock of Gibraltar in thine hand, "
    "and taketh it, and casteth it into the fire of coals. When he draweth "
    "it forth, it gloweth as an ember, yet it burneth thee not. "
    '"Now it shall bring thee home to Capernaum, or unto the palace of '
    'Babylon, whither thou wilt."'
)
LUKE = (
    'Peter graspeth thine arm. "Once my Master said unto me, "Simon, Simon, '
    "behold, Satan hath desired to have you, that he may sift you as wheat: "
    'But I have prayed for thee, that thy faith fail not." '
    "Now I say the same unto thee. Every night I pray for thee. Go down, "
    'and bring that soul home."'
)
MICHAEL_FIRE = (
    "Michael taketh the fiery pebble and turneth it in his hand, and the "
    'fire goeth out of it, and it is made smooth. "Now this stone shall '
    'carry thee to any place thou hast trodden."'
)
MICHAEL_PLAIN = (
    "Michael taketh the pebble and turneth it in his hand, and it is made "
    'smooth. "Now this stone shall carry thee to any place thou hast trodden."'
)
CAPERNAUM = (
    "The pebble burneth bright in thy hand, and thou art carried home to "
    "Capernaum."
)
BABYLON = (
    "The pebble burneth bright in thy hand, and thou art carried unto the "
    "palace of Babylon."
)
GENERIC = (
    "The Master gave me a new name, and on it He said He would build. "
    "Remember my name, and the floor will hold you."
)


def shown(src):
    return src.replace('\\"', '"').replace("\\'", "'")


class FieryPebbleTests(unittest.TestCase):
    def test_object_beside_the_others(self):
        objects = (ROOT / "include/objects.h").read_text()
        pebble = objects.find("PEBBLE_FROM_GIBRALTAR")
        fiery = objects.find("FIERY_PEBBLE_FROM_GIBRALTAR")
        stone = objects.find("SMOOTH_STONE_FROM_GIBRALTAR")
        self.assertLess(pebble, fiery)
        self.assertLess(fiery, stone)
        self.assertIn('OBJ("fiery pebble from the rock of Gibraltar"', objects)
        block = objects.split("fiery pebble from the rock of Gibraltar", 1)[1]
        block = block.split("SMOOTH_STONE_FROM_GIBRALTAR", 1)[0]
        self.assertIn("TOOL_CLASS", block)
        zap = (ROOT / "src/zap.c").read_text()
        self.assertIn("FIERY_PEBBLE_FROM_GIBRALTAR", zap)

    def test_invoke_menu(self):
        apply = (ROOT / "src/apply.c").read_text()
        body = apply.split("invoke_gibraltar_fiery(", 1)[1]
        body = body.split("invoke_gibraltar_stone(", 1)[0]
        self.assertLess(body.find("gibraltar_blocked(FALSE)"), body.find("create_nhwindow"))
        self.assertIn("Whither shall the pebble carry thee?", body)
        self.assertIn('"Capernaum"', body)
        self.assertIn('"Babylon\'s Palace"', body)
        self.assertIn("stronghold_level", body)
        self.assertIn(CAPERNAUM, body)
        self.assertIn(BABYLON, body)
        self.assertIn("ECMD_CANCEL", body)
        art = (ROOT / "src/artifact.c").read_text()
        self.assertIn("invoke_gibraltar_fiery", art)

    def test_peter_and_michael(self):
        sounds = shown((ROOT / "src/sounds.c").read_text())
        self.assertIn(FORGE, sounds)
        self.assertIn(LUKE, sounds)
        self.assertIn(GENERIC, sounds)
        chat = sounds.split("u.uevent.peter_grimoire = 1", 1)[1]
        chat = chat.split(GENERIC, 1)[0]
        self.assertLess(chat.find("peter_forge_pebble()"), chat.find("goodground_trial_done()"))
        bless = chat.find("goodground_trial_done()")
        luke = chat.find("peter_grimoire && !u.uevent.peter_renewed")
        self.assertLess(bless, luke)
        self.assertLess(luke, chat.find(LUKE))
        sea = (
            'Peter looketh out toward the sea. "I toiled all the night and '
            'caught nothing, until He said, "Cast the net on the right side '
            'of the ship, and ye shall find.""'
        )
        self.assertIn(sea, sounds)
        self.assertLess(sounds.find(sea), sounds.find(GENERIC))
        self.assertLess(
            chat.find(LUKE),
            chat.find("peter_rewarded && !u.uevent.peter_grimoire"),
        )
        hinnom = shown((ROOT / "src/hinnom.c").read_text())
        self.assertIn(MICHAEL_FIRE, hinnom)
        self.assertIn(MICHAEL_PLAIN, hinnom)
        self.assertIn(
            '"But it will not carry thee until thy road to salvation is finished."',
            hinnom,
        )
        self.assertIn(
            "carrying(FIERY_PEBBLE_FROM_GIBRALTAR)\n"
            "                || carrying(PEBBLE_FROM_GIBRALTAR)",
            hinnom,
        )
        self.assertLess(hinnom.find(MICHAEL_FIRE), hinnom.find(MICHAEL_PLAIN))


if __name__ == "__main__":
    unittest.main()
