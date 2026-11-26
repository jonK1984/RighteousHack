/* RighteousHack: the war on the Plane of Heaven.
   Lucifer is not a new monster kind. A new kind would lengthen the
   saved mvitals list and an old save would not load. He is a red
   dragon marked with STRAT_LUCIFER. His return is a migrating
   monster whose mlstmv is already saved. EDITLEVEL stays 20. */

#include "hack.h"

#define LUCIFER_HP 250
#define LUCIFER_WAIT 15
#define LUCIFER_NAME "Lucifer"

static void lucifer_mark(struct monst *);
static void lucifer_disguise(struct monst *);
static void lucifer_reveal(struct monst *);
static boolean lucifer_waiting(void);
static void lucifer_park(struct monst *);
static void lucifer_rise(struct monst *);
static void heaven_factions(void);
static void heaven_ensure(void);
static boolean lucifer_tail(struct monst *);
static boolean lucifer_flood(struct monst *);
static void lucifer_accuse(struct monst *);
static boolean lucifer_summon(struct monst *);

static void
lucifer_mark(struct monst *mtmp)
{
    mtmp->mstrategy |= STRAT_LUCIFER;
    mtmp->mstrategy &= ~STRAT_LUCIFER_WAIT;
    mtmp->mpeaceful = 0;
    mtmp->mtame = 0;
    mtmp->mhp = mtmp->mhpmax = LUCIFER_HP;
    mtmp->m_lev = 50;
    mtmp->mspeed = MFAST;
    (void) christen_monst(mtmp, LUCIFER_NAME);
    set_malign(mtmp);
}

static void
lucifer_disguise(struct monst *mtmp)
{
    mtmp->m_ap_type = M_AP_MONSTER;
    mtmp->mappearance = PM_ANGEL;
    newsym(mtmp->mx, mtmp->my);
}

static void heaven_archangels(struct monst *);

static void
lucifer_reveal(struct monst *mtmp)
{
    if (M_AP_TYPE(mtmp) == M_AP_NOTHING)
        return;
    mtmp->m_ap_type = M_AP_NOTHING;
    newsym(mtmp->mx, mtmp->my);
    if (!Deaf)
        pline("Lucifer casteth off the likeness of an angel of light.");
    /* A rehearsal must not stop for the blackout. */
    if (!endcut_testing)
        heaven_archangels(mtmp);
}

static boolean
lucifer_waiting(void)
{
    struct monst *mtmp;

    for (mtmp = gm.migrating_mons; mtmp; mtmp = mtmp->nmon)
        if (is_lucifer(mtmp) && (mtmp->mstrategy & STRAT_LUCIFER_WAIT))
            return TRUE;
    return FALSE;
}

/* Take him off the map. mlstmv holds the turn he fell. */
static void
lucifer_park(struct monst *mtmp)
{
    lucifer_mark(mtmp);
    mtmp->mstrategy |= STRAT_LUCIFER_WAIT;
    mtmp->m_ap_type = M_AP_NOTHING;
    mtmp->mlstmv = svm.moves;
    relmon(mtmp, &gm.migrating_mons);
    mtmp->mx = mtmp->my = 0;
    mtmp->mux = mtmp->muy = 0;
    mtmp->mtrack[0].x = 0;
    mtmp->mstate = MON_MIGRATING;
}

static void
lucifer_rise(struct monst *mtmp)
{
    mtmp->mstrategy &= ~STRAT_LUCIFER_WAIT;
    lucifer_mark(mtmp);
    mon_arrive(mtmp, -1);
    if (!mtmp->mx)
        return;
    lucifer_disguise(mtmp);
    pline("Lucifer is risen again, and the war in heaven is not ended.");
}

void
lucifer_on_death(struct monst *mtmp)
{
    struct monst *neu;

    if (!is_lucifer(mtmp) || (mtmp->mstrategy & STRAT_LUCIFER_WAIT))
        return;
    if (lucifer_waiting())
        return;
    pline("Lucifer is cast down. He shall not rise for a little season.");
    neu = makemon(&mons[PM_RED_DRAGON], 0, 0,
                  MM_NOWAIT | MM_NOCOUNTBIRTH | MM_NOMSG | MM_ANGRY);
    if (!neu)
        return;
    lucifer_park(neu);
}

/* One special, then his ordinary dragon attacks wait until next turn. */
int
lucifer_act(struct monst *mtmp)
{
    int which;

    if (!is_lucifer(mtmp) || DEADMONSTER(mtmp))
        return 0;
    if (mtmp->mstrategy & STRAT_LUCIFER_WAIT)
        return 0;
    if (helpless(mtmp))
        return 0;

    which = rn2(4);
    if (distmin(mtmp->mx, mtmp->my, u.ux, u.uy) <= 1 && rn2(2))
        which = 0;
    lucifer_reveal(mtmp);
    switch (which) {
    case 0:
        if (lucifer_tail(mtmp))
            return 1;
        break;
    case 1:
        if (lucifer_flood(mtmp))
            return 1;
        break;
    case 2:
        if (canseemon(mtmp) || m_canseeu(mtmp)) {
            lucifer_accuse(mtmp);
            return 1;
        }
        break;
    default:
        return lucifer_summon(mtmp) ? 1 : 0;
    }
    return 0;
}

static boolean
lucifer_tail(struct monst *mtmp)
{
    struct monst *m2, *nmon;
    boolean any = FALSE;

    for (m2 = fmon; m2; m2 = nmon) {
        nmon = m2->nmon;
        if (m2 == mtmp || DEADMONSTER(m2))
            continue;
        if (distmin(mtmp->mx, mtmp->my, m2->mx, m2->my) > 1)
            continue;
        any = TRUE;
        m2->mhp -= d(3, 6);
        if (m2->mhp < 1) {
            pline("%s is smitten by the tail.", Monnam(m2));
            mondead(m2);
        }
    }
    if (distmin(mtmp->mx, mtmp->my, u.ux, u.uy) <= 1) {
        any = TRUE;
        pline("The tail of the Great Dragon sweepeth, and striketh thee.");
        losehp(d(3, 8), "the sweep of the tail", KILLED_BY);
        if (u.usteed && !blanket_keeps_seat())
            dismount_steed(DISMOUNT_THROWN);
    } else if (any) {
        pline("The tail of the Great Dragon sweepeth round about.");
    }
    return any;
}

static boolean
lucifer_flood(struct monst *mtmp)
{
    int dx, dy, ax, ay, step, range;
    struct obj *obj, *nxt;

    if (!m_canseeu(mtmp))
        return FALSE;
    dx = u.ux - mtmp->mx;
    dy = u.uy - mtmp->my;
    ax = abs(dx);
    ay = abs(dy);
    if (!dx && !dy)
        return FALSE;
    if (ax && ay && ax != ay)
        return FALSE;
    range = max(ax, ay);
    if (range > 8)
        return FALSE;
    dx = sgn(dx);
    dy = sgn(dy);
    for (step = 1; step < range; step++)
        if (!isok(mtmp->mx + dx * step, mtmp->my + dy * step)
            || !ZAP_POS(levl[mtmp->mx + dx * step][mtmp->my + dy * step].typ))
            return FALSE;

    pline("The dragon casteth out of his mouth water as a flood.");
    losehp(d(4, 6), "the flood from the dragon's mouth", KILLED_BY);
    hurtle(dx, dy, rnd(2) + 1, TRUE);
    for (obj = gi.invent; obj; obj = nxt) {
        nxt = obj->nobj;
        (void) water_damage(obj, (const char *) 0, TRUE);
    }
    return TRUE;
}

static void
lucifer_accuse(struct monst *mtmp)
{
    (void) mtmp;
    if (rn2(2)) {
        u.ublesscnt += rnz(50);
        pline("The accuser of the brethren speaketh against thee, and thy prayer is put off.");
    } else {
        change_luck(-1);
        pline("The accuser of the brethren speaketh against thee, and thy fortune faileth.");
    }
}

static boolean
lucifer_summon(struct monst *mtmp)
{
    struct monst *angel;
    int n;

    n = 0;
    for (angel = fmon; angel; angel = angel->nmon)
        if (!DEADMONSTER(angel) && (angel->mstrategy & STRAT_HEAVEN_FALLEN))
            n++;
    if (n >= 8)
        return FALSE;
    angel = makemon(&mons[PM_ANGEL], mtmp->mx, mtmp->my,
                    MM_ADJACENTOK | MM_ANGRY | MM_NOMSG);
    if (!angel)
        return FALSE;
    angel->mpeaceful = 0;
    angel->mtame = 0;
    angel->mstrategy |= STRAT_HEAVEN_FALLEN;
    angel->mstrategy &= ~STRAT_HEAVEN_LORD;
    set_malign(angel);
    pline("The Great Dragon calleth, and a fallen angel answereth.");
    newsym(angel->mx, angel->my);
    return TRUE;
}

static void
heaven_factions(void)
{
    struct monst *mtmp;

    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp) || mtmp->data != &mons[PM_ANGEL])
            continue;
        /* The guardian angel is already a tame minion with no edog.
           Leave it that way. dog_move() allows that one case. */
        if (mtmp->isminion || has_emin(mtmp))
            continue;
        if (mtmp->mstrategy & (STRAT_HEAVEN_LORD | STRAT_HEAVEN_FALLEN))
            continue;
        if (mtmp->mtame || mtmp->mpeaceful) {
            mtmp->mstrategy |= STRAT_HEAVEN_LORD;
            mtmp->mtame = max(mtmp->mtame, 10);
            mtmp->mpeaceful = 1;
            /* A guardian angel stays a minion. Anyone else needs edog. */
            rh_attach_edog(mtmp);
        } else {
            mtmp->mstrategy |= STRAT_HEAVEN_FALLEN;
            mtmp->mtame = 0;
            mtmp->mpeaceful = 0;
        }
        set_malign(mtmp);
    }
}

static void
heaven_ensure(void)
{
    struct monst *mtmp, **mprev;
    boolean here;

    here = FALSE;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && is_lucifer(mtmp)
            && !(mtmp->mstrategy & STRAT_LUCIFER_WAIT))
            here = TRUE;
    if (!here && !lucifer_waiting()) {
        mtmp = makemon(&mons[PM_RED_DRAGON], 0, 0,
                       MM_NOWAIT | MM_ANGRY | MM_NOMSG);
        if (mtmp) {
            lucifer_mark(mtmp);
            lucifer_disguise(mtmp);
        }
    }

    if (perdition_forever())
        return;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && mtmp->iswiz)
            return;
    for (mprev = &gm.migrating_mons; (mtmp = *mprev) != 0; ) {
        if (mtmp->iswiz) {
            *mprev = mtmp->nmon;
            mon_arrive(mtmp, -1);
            return;
        }
        mprev = &mtmp->nmon;
    }
    /* None here and none on the way. Another may still live on a
       different level. This plane still gets its own. */
    (void) makemon(&mons[PM_WIZARD_OF_YENDOR], 0, 0, MM_NOWAIT | MM_ANGRY);
}

static void
heaven_raise(void)
{
    struct monst *mtmp, **mprev;

    for (mprev = &gm.migrating_mons; (mtmp = *mprev) != 0; ) {
        if (is_lucifer(mtmp) && (mtmp->mstrategy & STRAT_LUCIFER_WAIT)
            && svm.moves - mtmp->mlstmv >= LUCIFER_WAIT) {
            *mprev = mtmp->nmon;
            lucifer_rise(mtmp);
            return;
        }
        mprev = &mtmp->nmon;
    }
}

void
heaven_tick(void)
{
    if (!Is_astralevel(&u.uz))
        return;
    heaven_factions();
    heaven_raise();
    heaven_ensure();
}

/* Jon edits this table. A new Plane of Heaven draws 7 to 10
   distinct rows. spe_set forces spe (an enchantment, or charges).
   A rod with spe_set 0 keeps an ordinary charge roll, 4 to 8.
   blessed calls bless(). quanlo and quanhi are the stack.
   Both 0 means one object.
   The names in the comments are the words the player reads. */
struct heaven_gift {
    int otyp;
    int spe;
    int spe_set;
    int blessed;
    int quanlo;
    int quanhi;
};

static const struct heaven_gift heaven_chest[] = {
    /* gauntlets of power */
    { GAUNTLETS_OF_POWER, 0, 0, 0, 0, 0 },
    /* ring of free action */
    { RIN_FREE_ACTION, 0, 0, 0, 0, 0 },
    /* ring of conflict */
    { RIN_CONFLICT, 0, 0, 0, 0, 0 },
    /* verse of judgement to the wicked (vanilla scroll of genocide) */
    { SCR_GENOCIDE, 0, 0, 0, 0, 0 },
    /* amulet of life saving */
    { AMULET_OF_LIFE_SAVING, 0, 0, 0, 0, 0 },
    /* rod of final judgement (vanilla wand of death) */
    { WAN_DEATH, 0, 0, 0, 0, 0 },
    /* rod of move mountains (vanilla wand of digging) */
    { WAN_DIGGING, 0, 0, 0, 0, 0 },
    /* blessed anointing oil of full healing, 3 to 6 */
    { ANO_FULL_HEALING, 0, 0, 1, 3, 6 },
    /* blessed writing tablet, 80 charges */
    { MAGIC_MARKER, 80, 1, 1, 0, 0 },
    /* prophetic book of finger of judgement */
    { SPE_FINGER_OF_DEATH, 0, 0, 0, 0, 0 },
    /* elixer of holy water, 5 to 8 */
    { POT_WATER, 0, 0, 1, 5, 8 },
    /* blessed +5 unicorn horn */
    { UNICORN_HORN, 5, 1, 1, 0, 0 },
    /* blessed bag of holding */
    { BAG_OF_HOLDING, 0, 0, 1, 0, 0 },
    /* anointing oil of monster detection, quantity 3 */
    { ANO_MONSTER_DETECTION, 0, 0, 0, 3, 3 },
};

#define HEAVEN_DRAW_MIN 7
#define HEAVEN_DRAW_MAX 10
#define HEAVEN_CHEST_NAME "a gold chest set with every precious stone"

static void
heaven_altar(coordxy x, coordxy y, unsigned amask)
{
    /* No stock high cleric. The Dragon's priests stand in front
       of the temples, and the Lord's host stands inside. */
    levl[x][y].typ = ALTAR;
    levl[x][y].altarmask = (uchar) (amask | AM_SHRINE | AM_SANCTUM);
    svl.level.flags.has_temple = TRUE;
}

boolean
is_heaven_chest(struct obj *obj)
{
    return (boolean) (obj && obj->otyp == CHEST && has_oname(obj)
                      && !strcmp(ONAME(obj), HEAVEN_CHEST_NAME));
}

static void
heaven_fill_chest(struct obj *box)
{
    int i, n, k, pick[SIZE(heaven_chest)];
    const struct heaven_gift *gift;
    struct obj *obj;

    n = SIZE(heaven_chest);
    for (i = 0; i < n; i++)
        pick[i] = i;
    for (i = n - 1; i > 0; i--) {
        k = rn2(i + 1);
        if (k != i) {
            int tmp = pick[i];

            pick[i] = pick[k];
            pick[k] = tmp;
        }
    }
    n = rn1(HEAVEN_DRAW_MAX - HEAVEN_DRAW_MIN + 1, HEAVEN_DRAW_MIN);
    if (n > SIZE(heaven_chest))
        n = SIZE(heaven_chest);
    for (i = 0; i < n; i++) {
        gift = &heaven_chest[pick[i]];
        /* init stays off so a bag of holding is not filled for us */
        obj = mksobj(gift->otyp, FALSE, FALSE);
        if (!obj)
            continue;
        if (gift->spe_set)
            obj->spe = gift->spe;
        else if (obj->oclass == WAND_CLASS)
            obj->spe = rn1(5, (objects[obj->otyp].oc_dir == NODIR) ? 11 : 4);
        if (gift->blessed)
            bless(obj);
        if (gift->quanhi > 0 && gift->quanhi >= gift->quanlo)
            obj->quan = (long) rn1(gift->quanhi - gift->quanlo + 1,
                                    gift->quanlo);
        obj->known = obj->dknown = obj->bknown = 1;
        /* A prophet-mode rehearsal must not teach the hero the gifts. */
        if (!endcut_testing)
            discover_object(obj->otyp, TRUE, TRUE, FALSE);
        obj->owt = weight(obj);
        (void) add_to_container(box, obj);
    }
    box->owt = weight(box);
}

/* Locked. The verse is quoted. The rest is not. A blank line
   separates the paragraphs. Each archangel is its own line. */
static const char heaven_host_text[] =
    "\"And there was war in heaven: Michael and his angels fought against the dragon; and the dragon fought and his angels.\"\n"
    "\n"
    "In the midst of the battle the heavens are rent asunder, and the sound of a trumpet pierceth the air. Four mighty archangels descend upon the field of war, clothed in white and girded with gold, their armour shining as the sun and their swords as flames of fire.\n"
    "\n"
    "Michael, the great captain of the host, set over the best of mankind and over chaos.\n"
    "Gabriel, set over Paradise, and over the serpents, and over the Cherubim.\n"
    "Raphael, set over the spirits of men.\n"
    "Uriel, set over the world and over Tartarus.\n"
    "\n"
    "Where they set their feet the host of the Great Dragon trembleth, for they are come to execute the righteous judgment of the Lord upon all that wage war against heaven.";

static void
heaven_blackout(const char *text)
{
    endcut_card(text);
}

static void
heaven_ally(struct monst *mtmp, unsigned extra)
{
    if (!mtmp)
        return;
    mtmp->mstrategy |= STRAT_HEAVEN_LORD | extra;
    mtmp->mstrategy &= ~STRAT_HEAVEN_FALLEN;
    mtmp->mpeaceful = 1;
    mtmp->mtame = max(mtmp->mtame, 10);
    /* Tame without edog is sent to dog_move and panics. */
    rh_attach_edog(mtmp);
    set_malign(mtmp);
    newsym(mtmp->mx, mtmp->my);
}

static void
heaven_enemy(struct monst *mtmp, unsigned extra)
{
    if (!mtmp)
        return;
    mtmp->mstrategy |= extra;
    mtmp->mstrategy &= ~(STRAT_HEAVEN_LORD | STRAT_HEAVEN_CHERUB
                         | STRAT_HEAVEN_SERAPH | STRAT_HEAVEN_ARCH);
    mtmp->mpeaceful = 0;
    mtmp->mtame = 0;
    set_malign(mtmp);
    newsym(mtmp->mx, mtmp->my);
}

static struct monst *
heaven_at(struct permonst *pm, coordxy x, coordxy y)
{
    if (!isok(x, y) || m_at(x, y))
        return (struct monst *) 0;
    if (levl[x][y].typ != ROOM)
        return (struct monst *) 0;
    return makemon(pm, x, y, MM_NOWAIT | MM_NOMSG);
}

/* Floor inside one temple, skipping the altar square. */
static int
heaven_room_floors(coordxy ax, coordxy ay, coordxy spots[][2], int maxs)
{
    static const coordxy box[3][4] = {
        { 5, 8, 9, 10 },
        { 35, 4, 39, 6 },
        { 65, 8, 69, 10 },
    };
    int n = 0, t, x, y;

    for (t = 0; t < 3; t++) {
        if (ax < box[t][0] || ax > box[t][2]
            || ay < box[t][1] || ay > box[t][3])
            continue;
        for (y = box[t][1]; y <= box[t][3]; y++)
            for (x = box[t][0]; x <= box[t][2]; x++) {
                if (x == ax && y == ay)
                    continue;
                if (levl[x][y].typ != ROOM || m_at(x, y))
                    continue;
                if (n < maxs) {
                    spots[n][0] = (coordxy) x;
                    spots[n][1] = (coordxy) y;
                    n++;
                }
            }
        break;
    }
    return n;
}

static void
heaven_cherubim(coordxy ax, coordxy ay)
{
    static const coordxy near8[8][2] = {
        { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 },
        { 1, 1 }, { 1, -1 }, { -1, 1 }, { -1, -1 },
    };
    int i, n;

    n = 0;
    for (i = 0; i < 8 && n < 2; i++) {
        struct monst *mtmp = heaven_at(&mons[PM_KI_RIN],
                                        ax + near8[i][0], ay + near8[i][1]);

        if (!mtmp)
            continue;
        heaven_ally(mtmp, STRAT_HEAVEN_CHERUB);
        n++;
    }
}

static void
heaven_altar_host(coordxy ax, coordxy ay, int align)
{
    coordxy spots[16][2];
    int n, i, lords, fallen;
    struct monst *mtmp;

    if (align != A_LAWFUL && align != A_NONE)
        return;
    if (align == A_LAWFUL)
        heaven_cherubim(ax, ay);
    n = heaven_room_floors(ax, ay, spots, 16);
    lords = fallen = 0;
    for (i = 0; i < n; i++) {
        if (lords < 3) {
            mtmp = heaven_at(&mons[PM_ANGEL], spots[i][0], spots[i][1]);
            if (mtmp) {
                heaven_ally(mtmp, 0);
                lords++;
            }
        } else if (fallen < 3) {
            mtmp = heaven_at(&mons[PM_ANGEL], spots[i][0], spots[i][1]);
            if (mtmp) {
                heaven_enemy(mtmp, STRAT_HEAVEN_FALLEN);
                fallen++;
            }
        }
    }
}

static void
heaven_archangels(struct monst *lucifer)
{
    static const struct {
        const char *name;
        int lev;
        int hp;
    } four[] = {
        { "Michael", 45, 240 },
        { "Gabriel", 24, 160 },
        { "Raphael", 24, 160 },
        { "Uriel", 24, 160 },
    };
    int i;

    if (heaven_host_arrived())
        return;
    u.uevent.petra_step |= 2;
    heaven_blackout(heaven_host_text);
    for (i = 0; i < 4; i++) {
        struct monst *mtmp;
        coordxy x = lucifer ? lucifer->mx : u.ux;
        coordxy y = lucifer ? lucifer->my : u.uy;

        mtmp = makemon(&mons[PM_ARCHON], x, y,
                       MM_ADJACENTOK | MM_NOWAIT | MM_NOMSG);
        if (!mtmp)
            mtmp = makemon(&mons[PM_ARCHON], u.ux, u.uy,
                           MM_ADJACENTOK | MM_NOWAIT | MM_NOMSG);
        if (!mtmp)
            continue;
        mtmp->m_lev = four[i].lev;
        mtmp->mhp = mtmp->mhpmax = four[i].hp;
        if (i == 0)
            mtmp->mspeed = MFAST;
        (void) christen_monst(mtmp, four[i].name);
        heaven_ally(mtmp, STRAT_HEAVEN_ARCH);
    }
}

/* Called from des.heaven_host() after the Riders and the random
   monsters, so these squares stay theirs. A save that already has
   the level is not rebuilt. */
void
heaven_place_host(void)
{
    static const coordxy altarx[3] = { 7, 37, 67 };
    static const coordxy altary[3] = { 9, 5, 9 };
    static const coordxy priestxy[12][2] = {
        { 18, 9 }, { 19, 8 }, { 19, 9 }, { 19, 10 },
        { 36, 12 }, { 37, 12 }, { 38, 12 }, { 36, 13 },
        { 56, 9 }, { 55, 8 }, { 55, 9 }, { 55, 10 },
    };
    static const coordxy seraphxy[2][2] = { { 32, 9 }, { 42, 9 } };
    int i;

    for (i = 0; i < 3; i++) {
        int align = -1;

        if (IS_ALTAR(levl[altarx[i]][altary[i]].typ))
            align = Amask2align(levl[altarx[i]][altary[i]].altarmask
                                 & AM_MASK);
        heaven_altar_host(altarx[i], altary[i], align);
    }
    for (i = 0; i < 12; i++) {
        struct monst *mtmp = heaven_at(&mons[PM_ALIGNED_CLERIC],
                                        priestxy[i][0], priestxy[i][1]);

        if (!mtmp)
            continue;
        mtmp->female = (i & 1) ? 1 : 0;
        heaven_enemy(mtmp, STRAT_HEAVEN_PRIEST);
    }
    for (i = 0; i < 2; i++) {
        struct monst *mtmp = heaven_at(&mons[PM_ARCHON],
                                        seraphxy[i][0], seraphxy[i][1]);

        heaven_ally(mtmp, STRAT_HEAVEN_SERAPH);
    }
}

/* Called from des.heaven_temples() while a new Plane of Heaven is built.
   A save that already has the level keeps its old temples. */
void
heaven_place_temples(void)
{
    static const coordxy sx[3] = { 7, 37, 67 };
    static const coordxy sy[3] = { 9, 5, 9 };
    int order[3] = { 0, 1, 2 };
    int i, k, tmp;
    struct obj *box;

    for (i = 2; i > 0; i--) {
        k = rn2(i + 1);
        tmp = order[i];
        order[i] = order[k];
        order[k] = tmp;
    }
    heaven_altar(sx[order[0]], sy[order[0]], AM_LAWFUL);
    heaven_altar(sx[order[1]], sy[order[1]], AM_NONE);
    box = mksobj(CHEST, FALSE, FALSE);
    if (!box)
        return;
    bless(box);
    box->olocked = 0;
    box = oname(box, HEAVEN_CHEST_NAME, ONAME_NO_FLAGS);
    heaven_fill_chest(box);
    place_object(box, sx[order[2]], sy[order[2]]);
}

void
heaven_wake_lucifer(void)
{
    struct monst *mtmp, **mprev;

    for (mprev = &gm.migrating_mons; (mtmp = *mprev) != 0; ) {
        if (is_lucifer(mtmp) && (mtmp->mstrategy & STRAT_LUCIFER_WAIT)) {
            *mprev = mtmp->nmon;
            mtmp->nmon = 0;
            mtmp->mstrategy &= ~STRAT_LUCIFER_WAIT;
            lucifer_mark(mtmp);
            mon_arrive(mtmp, -1);
            if (mtmp->mx) {
                mtmp->m_ap_type = M_AP_NOTHING;
                newsym(mtmp->mx, mtmp->my);
            }
            return;
        }
        mprev = &mtmp->nmon;
    }
}

void
heaven_ready_host(void)
{
    struct monst *mtmp;
    boolean has_lucifer, has_son;

    heaven_factions();
    has_lucifer = has_son = FALSE;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp))
            continue;
        if (is_lucifer(mtmp))
            has_lucifer = TRUE;
        if (mtmp->iswiz)
            has_son = TRUE;
    }
    if (!has_lucifer) {
        mtmp = makemon(&mons[PM_RED_DRAGON], 0, 0,
                       MM_NOWAIT | MM_ANGRY | MM_NOMSG | MM_NOCOUNTBIRTH);
        if (mtmp) {
            lucifer_mark(mtmp);
            mtmp->m_ap_type = M_AP_NOTHING;
        }
    }
    if (!has_son)
        (void) makemon(&mons[PM_WIZARD_OF_YENDOR], 0, 0,
                       MM_NOWAIT | MM_ANGRY | MM_NOMSG | MM_NOCOUNTBIRTH);
}

void
heaven_dragon_end(void)
{
    endcut_dragon();
}

void
heaven_prayer(void)
{
    struct monst *mtmp;
    boolean held;

    if (!Is_astralevel(&u.uz))
        return;
    held = FALSE;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp))
            continue;
        if (!is_lucifer(mtmp) && !mtmp->iswiz)
            continue;
        if (mtmp->mstrategy & STRAT_LUCIFER_WAIT)
            continue;
        mtmp->mfrozen = 15;
        mtmp->mcanmove = 0;
        held = TRUE;
    }
    if (held)
        pline("At thy prayer, Lucifer and the Son of Perdition are holden still.");
}
