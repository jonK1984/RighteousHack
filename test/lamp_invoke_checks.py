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
        body = body.split("word_lamp_ac_bonus", 1)[0]
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

    def test_apply_toggles_like_a_magic_lamp(self):
        apply = read("src/apply.c")
        body = apply.split("use_word_lamp(struct obj *obj)", 1)[1]
        body = body.split("lamp_levels_above_invocation", 1)[0]
        self.assertNotIn("The lamp stays lit", apply)
        self.assertLess(body.index("obj->lamplit"), body.index("Underwater"))
        off = body.split("if (obj->lamplit)", 1)[1].split("Underwater", 1)[0]
        self.assertIn('pline("%s is now off.", Yname2(obj));', off)
        self.assertIn("end_burn(obj, TRUE);", off)
        self.assertLess(off.index("is now off."), off.index("end_burn"))
        self.assertLess(off.index("end_burn"), off.index("return ECMD_TIME;"))
        self.assertNotIn("lamp_verse", off)
        self.assertNotIn("word_lamp_bearing", off)
        self.assertIn('pline("%s is now on.", Yname2(obj));', body)
        self.assertLess(body.index("is now on."), body.index("lamp_verse"))
        self.assertLess(body.index("lamp_verse"),
                        body.index("word_lamp_bearing()"))
        invoke = apply.split("invoke_word_lamp(struct obj *obj)", 1)[1]
        invoke = invoke.split("word_lamp_ac_bonus", 1)[0]
        self.assertNotIn("lamplit", invoke)

    def test_word_lamp_light_radius_is_four(self):
        timeout = read("src/timeout.c")
        burn = timeout.split("begin_burn(struct obj *obj", 1)[1]
        burn = burn.split("end_burn(struct obj *obj", 1)[0]
        self.assertIn("int radius = 3;", burn)
        word = burn.split("case LAMP_OF_GODS_WORD:", 1)[1]
        word = word.split("case ", 1)[0]
        self.assertIn("radius = 4", word)
        magic = burn.split("case MAGIC_LAMP:", 1)[1]
        magic = magic.split("case ", 1)[0]
        self.assertNotIn("radius =", magic)
        light = read("src/light.c")
        split = light.split("obj_split_light_source(", 1)[1]
        split = split.split("obj_merge_light_sources(", 1)[0]
        self.assertIn("src->otyp == LAMP_OF_GODS_WORD", split)
        self.assertIn("ls->range = 4", split)
        self.assertIn("new_ls->range = 4", split)
        merge = light.split("obj_merge_light_sources(", 1)[1]
        merge = merge.split("obj_adjust_light_radius(", 1)[0]
        self.assertIn("dest->otyp == LAMP_OF_GODS_WORD", merge)
        self.assertIn("ls->range = 4", merge)
        relink = light.split("relink_light_sources(", 1)[1]
        relink = relink.split("maybe_write_ls", 1)[0]
        self.assertIn("ls->id.a_obj->otyp == LAMP_OF_GODS_WORD", relink)
        self.assertIn("ls->range = 4", relink)

    def test_lit_lamp_worsens_hostile_ac(self):
        apply = read("src/apply.c")
        bonus = apply.split("word_lamp_ac_bonus(struct monst *mdef)", 1)[1]
        bonus = bonus.split("gibraltar_blocked", 1)[0]
        self.assertIn("LAMP_OF_GODS_WORD", bonus)
        self.assertIn("otmp->lamplit", bonus)
        self.assertIn("gi.invent", bonus)
        self.assertIn("mdef->mpeaceful", bonus)
        self.assertIn("gl.light_base", bonus)
        self.assertIn("ls->id.a_obj == otmp", bonus)
        self.assertIn("circle_ptr(range)", bonus)
        self.assertIn("couldsee(mdef->mx, mdef->my)", bonus)
        self.assertIn("return (u.ulevel + 9) / 10;", bonus)
        self.assertNotIn("pline(", bonus)
        hit = read("src/uhitm.c").split("find_roll_to_hit(", 1)[1]
        hit = hit.split("return tmp;", 1)[0]
        self.assertIn("tmp += word_lamp_ac_bonus(mtmp);", hit)
        thrown = read("src/dothrow.c").split("thitmonst(", 1)[1]
        thrown = thrown.split("dieroll = rnd(20);", 1)[0]
        self.assertIn("tmp += word_lamp_ac_bonus(mon);", thrown)
        pets = read("src/mhitm.c").split("mattackm(", 1)[1]
        pets = pets.split("mdef->mconf", 1)[0]
        self.assertIn("if (magr->mtame)", pets)
        self.assertLess(pets.index("if (magr->mtame)"),
                        pets.index("word_lamp_ac_bonus(mdef)"))


if __name__ == "__main__":
    unittest.main()
