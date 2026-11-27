"""The Plane of Heaven stays peaceful after Lucifer falls.

The state is bit 2 of u.uevent.petra_step, a field that already
exists, so EDITLEVEL stays 20 and an old save still loads.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MICHAEL = (
    "The dragon is cast down, and his host is no more. "
    "The battle was the Lord's, and thou hast stood in it.",
    "Lay down thy sword, soldier of the Lord. "
    "There is no more war in heaven.",
)
GABRIEL = (
    "I bring thee good tidings once more: the enemy is fallen, "
    "and thou art found faithful.",
    "Go in peace. The way before thee is open.",
)
RAPHAEL = (
    "Rest now, mortal. The long road is behind thee, "
    "and no wound shall trouble thee here.",
    "Give thanks unto the Lord, for He hath brought thee through the fire.",
)
URIEL = (
    "Look upon the field, mortal. Where darkness stood, there is only light.",
    "The way is opened before thee. Enter when thou art ready.",
)
CHERUBIM = (
    "We kept the way of the tree of life. Now the way is opened unto thee.",
    "The flaming sword is sheathed. Pass in peace, mortal.",
    "We have guarded the holy places since the beginning. Rest thou here a while.",
)
SERAPHIM = (
    "Holy, holy, holy is the Lord of hosts.",
    "We cover our faces before the throne. Lift thou thy voice in praise with us.",
    "The fire that burned the dragon's host burneth in us, and it is the Lord's.",
)
ANGELS = (
    "Well fought, child of dust. Give glory to God.",
    "The host of the dragon is no more. Rejoice!",
    "We sing praise unto the Lord this day, and thou art among us.",
    "Rest a while, mortal. Nothing here shall harm thee now.",
    "Thou art welcome among the host of the Lord.",
)
GATE = (
    "A gate of light openeth upon the field of heaven, "
    "and a voice saith: Come up hither."
)
NORTH = (
    "Strait is the gate, and narrow is the way, which leadeth unto life "
    "(Matthew 7:14)"
)
EAST = (
    "I am the way, the truth, and the life: no man cometh unto the Father, "
    "but by me. (John 14:6)"
)
SOUTH = "This is the way, walk ye in it (Isaiah 30:21)"
WEST = (
    "And God shall wipe away all tears from their eyes; and there shall be "
    "no more death (Revelation 21:4)"
)
PROMPT = "Art thou ready to go up? (This ends the game.)"


def src(name):
    return (ROOT / "src" / name).read_text()


def lua_strings(block):
    out = []
    i = 0
    while i < len(block):
        if block[i] != '"':
            i += 1
            continue
        i += 1
        buf = []
        while i < len(block):
            ch = block[i]
            if ch == "\\":
                buf.append(block[i + 1])
                i += 2
                continue
            if ch == '"':
                i += 1
                break
            buf.append(ch)
            i += 1
        out.append("".join(buf))
    return out


def spoken(key):
    quest = (ROOT / "dat" / "quest.lua").read_text()
    block = quest.split(key + " = {", 1)[1].split("},", 1)[0]
    lines = []
    for raw in lua_strings(block):
        text = raw
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        lines.append(text)
    return lines


class HeavenPeace(unittest.TestCase):
    def test_the_bit_is_saved_and_old_saves_still_load(self):
        you = (ROOT / "include" / "you.h").read_text()
        field = you.split("petra_step", 1)[1].split(";", 1)[0]
        self.assertIn("3", field)
        monst = (ROOT / "include" / "monst.h").read_text()
        macro = monst.split("heaven_peace()", 1)[1].split("\n\n", 1)[0]
        self.assertIn("petra_step & 4", macro)
        self.assertIn("Is_astralevel", macro)
        patch = (ROOT / "include" / "patchlevel.h").read_text()
        self.assertIn("#define EDITLEVEL 20", patch)

    def test_nothing_is_generated(self):
        makemon = src("makemon.c").split(
            "makemon(\n    struct permonst *ptr", 1)[1]
        guard = makemon.split("debug_mongen", 1)[0]
        self.assertIn("heaven_peace()", guard)
        tick = src("heaven.c").split("heaven_tick(void)", 1)[1]
        tick = tick.split("heaven_factions();", 1)[0]
        self.assertIn("heaven_peace()", tick)
        arrive = src("dog.c").split("mon_arrive(", 1)[1]
        arrive = arrive.split("xlocale", 1)[0]
        self.assertIn("heaven_bars_arrival(mtmp)", arrive)
        self.assertLess(arrive.index("heaven_bars_arrival(mtmp)"),
                        arrive.index("dealloc_monst(mtmp)"))

    def test_death_and_damage_stop_only_during_the_peace(self):
        losehp = src("hack.c").split("losehp(int n", 1)[1].split(
            "disp.botl", 1)[0]
        self.assertIn("heaven_peace()", losehp)
        done = src("end.c").split("done(int how)", 1)[1]
        guard = done.split("u.umortality++;", 1)[0]
        self.assertIn("heaven_peace()", guard)
        self.assertIn("how != ASCENDED", guard)
        self.assertIn("how != QUIT", guard)
        self.assertIn("heaven_spare_hero()", guard)
        eat = src("eat.c")
        starve = eat.split("You(\"die from starvation.\");", 1)[0]
        starve = starve.split("u.uhunger < -(100", 1)[1]
        self.assertIn("heaven_peace()", starve)
        timeout = src("timeout.c")
        body = timeout.split("nh_timeout(void)", 1)[1]
        self.assertLess(body.index("heaven_spare_hero()"),
                        body.index("case STONED:"))
        for kind in ("STONED", "SLIMED", "SICK", "STRANGLED"):
            case = body.split("case %s:" % kind, 1)[1].split("break;", 1)[0]
            self.assertIn("heaven_peace()", case, kind)
        losestr = src("attrib.c").split("losestr(", 1)[1]
        losestr = losestr.split("ABASE(A_STR) < ATTRMIN", 1)[0]
        self.assertIn("heaven_peace()", losestr)
        drain = src("exper.c").split("losexp(", 1)[1]
        drain = drain.split("resists_drli", 1)[0]
        self.assertIn("heaven_peace()", drain)
        hit = src("mhitu.c").split("mdamageu(", 1)[1]
        hit = hit.split("n < 0", 1)[0]
        self.assertIn("heaven_peace()", hit)
        blast = src("explode.c").split("Invulnerable || fear_protected()", 1)[1]
        blast = blast.split("burnarmor", 1)[0]
        self.assertIn("heaven_peace()", blast)

    def test_the_lines_are_verbatim_and_replace_battle_speech(self):
        sets = {
            "michael_peace": MICHAEL,
            "gabriel_peace": GABRIEL,
            "raphael_peace": RAPHAEL,
            "uriel_peace": URIEL,
        }
        for key, lines in sets.items():
            got = spoken(key)
            self.assertEqual(tuple(got), lines, key)
            for line in got:
                self.assertNotIn("\u2014", line, key)
                self.assertNotIn("--", line, key)
        heaven = src("heaven.c")
        speech = heaven.split("archangel_speech(struct monst *mtmp)", 1)[1]
        speech = speech.split("heaven_archangels", 1)[0]
        peace = speech.split("if (heaven_peace())", 1)[1]
        peace = peace.split("if (!strcmp(nm, \"Michael\"))", 1)[0]
        # The peace keys are chosen inside the peace block, before
        # the battle keys.
        block = speech.split("if (heaven_peace())", 1)[1]
        battle = block.split("return (const char *) 0;", 1)[1]
        for key in sets:
            self.assertIn('return "%s"' % key, block.split(
                "return (const char *) 0;", 1)[0])
            self.assertNotIn(key, battle)
        angel = heaven.split("heaven_peace_angel(void)", 1)[1]
        angel = angel.split("return lines", 1)[0]
        for line in ANGELS:
            self.assertIn('"%s"' % line, angel)
            self.assertNotIn("\u2014", line)
        sounds = src("sounds.c").split("case MS_CUSS:", 1)[1]
        sounds = sounds.split("case MS_SPELL:", 1)[0]
        self.assertLess(sounds.index("heaven_peace()"),
                        sounds.index("heaven_peace_angel()"))
        self.assertLess(sounds.index("is_heaven_lord(mtmp)"),
                        sounds.index('"It\'s not too late."'))
        self.assertLess(sounds.index("archangel_speech(mtmp)"),
                        sounds.index("heaven_peace_angel()"))
        chat = src("sounds.c").split("domonnoise(struct monst *mtmp)", 1)[1]
        early = chat.split("case MS_SPELL:", 1)[0]
        self.assertLess(early.index("heaven_peace_chat(mtmp)"),
                        early.index("case MS_CUSS:"))

    def test_cherubim_and_seraphim_peace_lines(self):
        heaven = src("heaven.c")
        for name, lines in (("cherub", CHERUBIM), ("seraph", SERAPHIM)):
            block = heaven.split("heaven_peace_%s(void)" % name, 1)[1]
            block = block.split("\n}\n", 1)[0]
            for line in lines:
                self.assertIn('"%s"' % line, block)
                self.assertNotIn("\u2014", line)
                self.assertNotIn("--", line)
            self.assertIn("rn2(SIZE(lines))", block)
        talk = heaven.split("heaven_peace_chat(struct monst *mtmp)", 1)[1]
        talk = talk.split("Jon edits this table", 1)[0]
        self.assertLess(talk.index("heaven_peace()"),
                        talk.index("is_heaven_cherub(mtmp)"))
        self.assertLess(talk.index("!mtmp->mpeaceful"),
                        talk.index("heaven_peace_cherub()"))
        self.assertLess(talk.index("is_heaven_cherub(mtmp)"),
                        talk.index("is_heaven_seraph(mtmp)"))
        self.assertIn("verbalize(\"%s\", line)", talk)
        sounds = src("sounds.c")
        self.assertIn("heaven_peace_chat(mtmp)", sounds)

    def test_the_portal_is_in_the_temple_and_the_prompt_defaults_to_no(self):
        heaven = src("heaven.c")
        altar = heaven.split("heaven_find_altar(coordxy *ax", 1)[1]
        altar = altar.split("heaven_altar_room", 1)[0]
        self.assertIn("AM_SANCTUM", altar)
        self.assertIn("A_LAWFUL", altar)
        center = heaven.split("heaven_room_center(coordxy ax", 1)[1]
        center = center.split("heaven_portal_square", 1)[0]
        self.assertIn("(minx + maxx) / 2", center)
        self.assertIn("(miny + maxy) / 2", center)
        spot = heaven.split("heaven_portal_square(coordxy ax", 1)[1]
        spot = spot.split("North, east, south, west", 1)[0]
        self.assertIn("cx != ax || cy != ay", spot)
        self.assertIn("IS_ALTAR", spot)
        self.assertIn("heaven_spare_spot", spot)
        begin = heaven.split("heaven_begin_peace(void)", 1)[1]
        begin = begin.split("heaven_gate_enter", 1)[0]
        self.assertIn("heaven_find_altar(&ax, &ay)", begin)
        self.assertIn("heaven_portal_square(ax, ay, &px, &py)", begin)
        self.assertNotIn("maketrap(ax, ay, MAGIC_PORTAL)", begin)
        self.assertIn("maketrap(px, py, MAGIC_PORTAL)", begin)
        self.assertIn("heaven_lay_verses(px, py)", begin)
        self.assertNotIn("heaven_lay_verses(ax, ay)", begin)
        self.assertIn(GATE, begin)
        self.assertNotIn("\u2014", GATE)
        gate = heaven.split("heaven_gate_enter(void)", 1)[1]
        gate = gate.split("heaven_peace_angel", 1)[0]
        self.assertIn('y_n("%s")' % PROMPT, gate)
        self.assertIn("== 'y'", gate)
        self.assertNotIn("endcut_finish_ascent", gate.split("== 'y'", 1)[0])
        hack = (ROOT / "include" / "hack.h").read_text()
        self.assertIn(
            "#define y_n(query) yn_function(query, ynchars, 'n', TRUE)",
            hack)
        trap = src("trap.c")
        furniture = trap.split("IS_FURNITURE(lev->typ)", 1)[1]
        furniture = furniture.split("return (struct trap *) 0;", 1)[0]
        self.assertIn("typ == MAGIC_PORTAL && lev->typ == ALTAR", furniture)
        display = src("display.c")
        color = display.split("The gate is the ordinary magic-portal", 1)[1]
        color = color.split("Fig trees", 1)[0]
        self.assertIn("CLR_YELLOW", color)
        self.assertIn("glyph_is_trap", color)
        self.assertIn("MAGIC_PORTAL", color)
        symbols = (ROOT / "include" / "defsym.h").read_text()
        portal = symbols.split("S_magic_portal", 1)[0].rsplit("PCHAR", 1)[1]
        self.assertIn("'^'", portal)

    def test_ascension_waits_for_the_gate(self):
        endcut = src("endcut.c")
        ascend = endcut.split("endcut_ascend(void)", 1)[1]
        ascend = ascend.split("endcut_finish_ascent", 1)[0]
        self.assertIn("heaven_begin_peace()", ascend)
        self.assertNotIn("endcut_play(ENDCUT_WIN)", ascend)
        self.assertNotIn("done(ASCENDED)", ascend)
        finish = endcut.split("endcut_finish_ascent(void)", 1)[1]
        finish = finish.split("endcut_dragon", 1)[0]
        self.assertIn("endcut_play(ENDCUT_WIN)", finish)
        self.assertIn("done(ASCENDED)", finish)
        self.assertLess(finish.index("endcut_play(ENDCUT_WIN)"),
                        finish.index("done(ASCENDED)"))
        menu = endcut.split("endcut_menu_line[]", 1)[1].split("};", 1)[0]
        self.assertIn("8 Peace on the Plane of Heaven", menu)
        run = endcut.split("case 8:", 1)[1].split("default:", 1)[0]
        self.assertIn("heaven_begin_peace()", run)
        self.assertIn("Is_astralevel", run)

    def test_items_can_be_taken(self):
        stolen = src("shk.c").split("stolen_value(", 1)[1]
        stolen = stolen.split("find_objowner", 1)[0]
        self.assertIn("heaven_peace()", stolen)
        self.assertIn("return 0L", stolen)
        pickup = src("pickup.c").split(
            "pickup_object(\n    struct obj *obj", 1)[1]
        pickup = pickup.split("obj->otyp == SCR_SCARE_MONSTER", 1)[0]
        self.assertIn("!heaven_peace() && obj->oartifact", pickup)
        self.assertIn("!heaven_peace() && obj->otyp == CORPSE", pickup)
        angry = src("mon.c").split(
            "setmangry(struct monst *mtmp, boolean via_attack)", 1)[1]
        angry = angry.split("via_attack &&", 1)[0]
        self.assertIn("heaven_peace()", angry)

    def test_four_verses_are_burned_around_the_portal(self):
        heaven = src("heaven.c")
        block = heaven.split("heaven_verses[]", 1)[1].split("};", 1)[0]
        texts = (NORTH, EAST, SOUTH, WEST)
        offsets = ("{ 0, -1,", "{ 1, 0,", "{ 0, 1,", "{ -1, 0,")
        at = 0
        for off, text in zip(offsets, texts):
            pos = block.index(off, at)
            words = block.index(text, pos)
            self.assertLess(pos, words)
            at = words
            self.assertNotIn("\u2014", text)
            self.assertNotIn("--", text)
            # Shorter than the read buffer, and long enough that an
            # 80-column Windows tty must fold it rather than cut it.
            self.assertLess(len(text), 200)
        self.assertGreater(len(EAST), 78)
        lay = heaven.split("heaven_lay_verses(coordxy ax", 1)[1]
        lay = lay.split("heaven_begin_peace", 1)[0]
        self.assertIn("heaven_verse_spot", lay)
        self.assertIn("heaven_spare_spot", lay)
        self.assertIn("BURN", lay)
        self.assertIn("nowipeout = 1", lay)
        self.assertIn("lit = 1", lay)
        self.assertIn("waslit = 1", lay)
        begin = heaven.split("heaven_begin_peace(void)", 1)[1]
        begin = begin.split("docrt();", 1)[0]
        self.assertLess(begin.index("maketrap(px, py, MAGIC_PORTAL)"),
                        begin.index("heaven_lay_verses(px, py)"))
        read = src("engrave.c").split("read_engr_at(", 1)[1]
        read = read.split("maxelen", 1)[0]
        self.assertIn("heaven_is_altar_verse", read)
        self.assertIn("rh_text_window(ep->engr_txt[actual_text])", read)
        wipe = src("engrave.c").split("wipe_engr_at(", 1)[1]
        wipe = wipe.split("wipeout_text", 1)[0]
        self.assertIn("nowipeout", wipe)
        gone = src("engrave.c").split("del_engr_at(", 1)[1]
        gone = gone.split("del_engr(ep)", 1)[0]
        self.assertIn("heaven_is_altar_verse", gone)
        wand = src("zap.c").split("e->engr_type != VERSE", 1)[1]
        wand = wand.split("WAN_POLYMORPH", 1)[0]
        self.assertIn("heaven_is_altar_verse", wand)
        color = src("display.c").split(
            "The four burned verses", 1)[1].split("Fig trees", 1)[0]
        self.assertIn("CLR_WHITE", color)
        self.assertIn("S_engroom", color)
        save = src("engrave.c")
        self.assertIn("engraving-actual_text", save)
        patch = (ROOT / "include" / "patchlevel.h").read_text()
        self.assertIn("#define EDITLEVEL 20", patch)


if __name__ == "__main__":
    unittest.main()
