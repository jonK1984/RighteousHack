#!/usr/bin/env python3
"""Peter's pebble, the Smooth Stone, and the Grand Grimoire."""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

NET = (
    'Peter taketh his net and casteth it over his shoulder. "Thou hast done well. '
    "Here is the key to the palace of Babylon; the great city lieth far below. "
    "And take this pebble from the rock of Gibraltar. When thou art weary of the deep, "
    'call upon it, and it shall bring thee home to Capernaum."'
)
PEBBLE_HOME = (
    "The pebble groweth warm in thy hand, and thou art carried home to Capernaum."
)
PEBBLE_COLD = (
    "The pebble lieth cold in thy hand. It will not carry thee from this place."
)
PEBBLE_ROAD = "The pebble lieth cold in thy hand. Thy road is not yet finished."
STONE_WARM = "The stone groweth warm in thy hand, and thou art carried to %s."
STONE_COLD = (
    "The stone lieth cold in thy hand. It will not carry thee from this place."
)
STONE_ROAD = "The stone lieth cold in thy hand. Thy road is not yet finished."
MICHAEL = (
    'Michael taketh the pebble and turneth it in his hand, and it is made smooth. '
    '"Now this stone shall carry thee to any place thou hast trodden."'
)
MICHAEL_ROAD = (
    '"But it will not carry thee until thy road to salvation is finished."'
)
RENEW = (
    'Peter embraceth thee. "Thou hast walked the narrow way and come home. '
    '"But they that wait upon the LORD shall renew their strength; they shall mount up '
    "with wings as eagles; they shall run, and not be weary; and they shall walk, "
    'and not faint." (Isaiah 40:31)"'
)
RENEW_FEEL = "Thou feelest thy spirit grow mighty within thee."
TOUCH = [
    "As thy fingers close upon the book, a cold like the grave runneth up thine arm, and the light about thee groweth dim. It is bound in the hide of a red dragon, and the hide is warm, as a thing that yet liveth.",
    "Thou openest it. The pages are written in an ancient tongue of Babylon, wedge-shaped marks pressed as into clay, yet they writhe upon the page like serpents. Between them are runes older than the flood, inked in what is surely blood. Thou canst not read them, yet they whisper to thee in a voice that is not thine own.",
    "A great evil presseth upon thy soul, as a hand upon thy throat. Thy heart faileth thee for fear, and every shadow seemeth to lean toward thee.",
    "Thou must show this to Peter.",
]
READ = [
    "Peter taketh the book from thy hand, and his face groweth grim. He setteth it upon the table and will not touch it again with his bare hand, for he senseth the evil within it.",
    'Peter layeth his hand upon thy shoulder, and his voice is urgent. "I pray thee, tarry with me. Leave me not alone with this thing until I have searched out its mystery. I beseech thee, stay." Seeing the fear in his eyes, thou consentest, and abidest with him.',
    "For seven days Peter poreth over the book by lamplight, night and day, searching out every dark word and every hidden purpose. He eateth little and sleepeth less, and oft thou hearest him praying in the night.",
    "On the seventh day he cometh to thee, and his look is grave.",
    '"This is the Grand Grimoire: The Red Dragon. It was written by the hand of Lucifer himself. Herein he hath set down his counsel: to gather the hosts of darkness out of the deep, to bind the souls of men as his ransom, and to make war upon the Throne of Heaven itself. The souls of men are but tools in his hand, to be used against the Lord."',
    'Peter\'s voice falleth low. "But there is one soul he shall not have. It lieth bound deep in a foul temple, in the very bowels of Gehennom." He looketh upon thee long and strangely, as one who knoweth more than he will say. "Thou must go down and rescue that soul. Thy path is clear."',
    'Together ye carry the book out to the shore and cast it upon a fire. Peter lifteth up his voice against it: "Back to the pit that spawned thee, thou foul thing of darkness! Thy master\'s counsel shall not stand!" The red hide shrieketh as it burneth, and a foul black smoke goeth up, and then it is ash.',
    'Peter goeth into his house and returneth with a small chest, bound in iron and covered in dust. He openeth it slowly, and taketh out a heavy iron key. "I had hoped never to bring this forth, not in all my days. But the hour is nigh." He putteth it into thine hand. "This is the Key to the Gates of Hell. Thou must go down into the deep and redeem what was once lost, for the battle for heaven is at hand."',
]
SITES = [
    "Capernaum",
    "Mines' End",
    "the top of Sokoban",
    "the prophet level",
    "the Cave of Gibeon",
    "the Quest home level",
    "Tyre",
    "Babylon's Palace",
    "the Valley of the Dead",
    "the Valley of Berachah",
    "Orcustown",
    "the Entrance to the Sanctum",
]


class PeterGibraltarTests(unittest.TestCase):
    def test_approved_text(self):
        def shown(src):
            return src.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")

        sounds = shown((ROOT / "src/sounds.c").read_text())
        apply = shown((ROOT / "src/apply.c").read_text())
        hinnom = shown((ROOT / "src/hinnom.c").read_text())
        for line in (NET, RENEW, RENEW_FEEL, *TOUCH, *READ):
            self.assertIn(line, sounds)
        for line in (PEBBLE_HOME, PEBBLE_COLD, PEBBLE_ROAD, STONE_WARM, STONE_COLD, STONE_ROAD):
            self.assertIn(line, apply)
        for site in SITES:
            self.assertIn('"%s"' % site, apply)
        self.assertIn(MICHAEL, hinnom)
        self.assertIn(MICHAEL_ROAD, hinnom)

    def test_gates_key_moved(self):
        sounds = (ROOT / "src/sounds.c").read_text()
        reward = sounds.split("carrying(PETER_NET)", 1)[1].split(
            "carrying(GRAND_GRIMOIRE)", 1
        )[0]
        self.assertNotIn("KEY_TO_GATES", reward)
        self.assertNotIn("Matthew", reward)
        self.assertNotIn("gates of hell shall not prevail", reward)
        self.assertIn("KEY_TO_BABYLON", reward)
        self.assertIn("PEBBLE_FROM_GIBRALTAR", reward)
        read = sounds.split("carrying(GRAND_GRIMOIRE)", 1)[1].split(
            "goodground_trial_done()", 1
        )[0]
        self.assertIn("KEY_TO_GATES", read)
        self.assertIn("useup(book)", read)
        self.assertIn("peter_grimoire", read)
        lock = (ROOT / "src/lock.c").read_text()
        self.assertIn("gates of hell shall not prevail against it", lock)
        do = (ROOT / "src/do.c").read_text()
        self.assertIn("carrying(KEY_TO_GATES)", do)

    def test_blocks_and_once(self):
        apply = (ROOT / "src/apply.c").read_text()
        body = apply.split("gibraltar_blocked", 1)[1].split("gibraltar_seen", 1)[0]
        self.assertLess(body.find("wayside_road()"), body.find("noteleport_level"))
        self.assertIn("goodground_trial_done()", body)
        self.assertIn("UTOTYPE_WIZPORT", apply)
        self.assertIn("VISITED", apply)
        art = (ROOT / "src/artifact.c").read_text()
        self.assertLess(
            art.find("obj->otyp == GRAND_GRIMOIRE"),
            art.find("objects[obj->otyp].oc_unique"),
        )
        self.assertIn("invoke_gibraltar_pebble", art)
        self.assertIn("invoke_gibraltar_stone", art)
        you = (ROOT / "include/you.h").read_text()
        self.assertIn("tome_dread", you)
        self.assertIn("peter_renewed", you)
        self.assertIn("u.uenmax += 30", (ROOT / "src/sounds.c").read_text())

    def test_objects_and_chest(self):
        objects = (ROOT / "include/objects.h").read_text()
        fence = objects.rfind("#if defined(OBJECTS_DESCR_INIT)")
        tail = objects[objects.find("PEBBLE_FROM_GIBRALTAR") :]
        self.assertLess(objects.find("PEBBLE_FROM_GIBRALTAR"), fence)
        self.assertIn('OBJ("pebble from the rock of Gibraltar"', objects)
        self.assertIn('OBJ("Smooth Stone from the rock of Gibraltar"', objects)
        self.assertIn('"tome bound in red dragon hide"', objects)
        self.assertIn("GRAND_GRIMOIRE", tail)
        castle = (ROOT / "dat/castle.lua").read_text()
        self.assertIn("Grand Grimoire: The Red Dragon", castle)
        zap = (ROOT / "src/zap.c").read_text()
        self.assertIn("GRAND_GRIMOIRE", zap)
        self.assertIn("PEBBLE_FROM_GIBRALTAR", zap)
        self.assertIn("SMOOTH_STONE_FROM_GIBRALTAR", zap)

    def test_read_grimoire(self):
        msg = (
            "The book is written in a tongue strange unto thee, and the evil "
            "written therein is too unspeakable to read. Thou must show this "
            "to Peter."
        )
        read = (ROOT / "src/read.c").read_text()
        self.assertIn(msg, read)
        hook = read.split("read_ok(struct obj *obj)", 1)[1].split(
            "doread(void)", 1
        )[0]
        self.assertIn("obj->otyp == GRAND_GRIMOIRE", hook)
        self.assertLess(
            hook.find("obj->otyp == GRAND_GRIMOIRE"),
            hook.find("return GETOBJ_SUGGEST"),
        )
        body = read.split("otyp == GRAND_GRIMOIRE", 1)[1].split(
            "FORTUNE_COOKIE", 1
        )[0]
        self.assertIn("pline(", body)
        self.assertNotIn("useup", body)
        self.assertNotIn("discover", body)


if __name__ == "__main__":
    unittest.main()
