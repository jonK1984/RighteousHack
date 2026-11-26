/* RighteousHack: the war on the Plane of Heaven.
   Lucifer is not a new monster kind. A new kind would lengthen the
   saved mvitals list and an old save would not load. He is a red
   dragon marked with STRAT_LUCIFER. His return is a migrating
   monster whose mlstmv is already saved. EDITLEVEL stays 20. */

#include "hack.h"

#define LUCIFER_HP 250
#define LUCIFER_WAIT 15
#define LUCIFER_NAME "Lucifer (The Great Dragon)"

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

static void
lucifer_reveal(struct monst *mtmp)
{
    if (M_AP_TYPE(mtmp) == M_AP_NOTHING)
        return;
    mtmp->m_ap_type = M_AP_NOTHING;
    newsym(mtmp->mx, mtmp->my);
    if (!Deaf)
        pline("Lucifer casteth off the likeness of an angel of light.");
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
        if (mtmp->mstrategy & (STRAT_HEAVEN_LORD | STRAT_HEAVEN_FALLEN))
            continue;
        if (mtmp->mtame || mtmp->mpeaceful) {
            mtmp->mstrategy |= STRAT_HEAVEN_LORD;
            mtmp->mtame = max(mtmp->mtame, 10);
            mtmp->mpeaceful = 1;
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

/* Jon can edit this table. Eight ordinary gifts are drawn each game.
   The rod of wishing is the rare line: one charge, and only one game
   in five adds it. */
struct heaven_gift {
    int otyp;
    int spe;
    int rare;
};

static const struct heaven_gift heaven_chest[] = {
    { SILVER_DRAGON_SCALE_MAIL, 5, 0 },
    { CRYSTAL_PLATE_MAIL, 5, 0 },
    { SPEED_BOOTS, 5, 0 },
    { GAUNTLETS_OF_POWER, 5, 0 },
    { SHIELD_OF_REFLECTION, 3, 0 },
    { CLOAK_OF_MAGIC_RESISTANCE, 5, 0 },
    { HELM_OF_BRILLIANCE, 5, 0 },
    { RIN_PROTECTION, 5, 0 },
    { RIN_INCREASE_ACCURACY, 5, 0 },
    { RIN_INCREASE_DAMAGE, 5, 0 },
    { AMULET_OF_LIFE_SAVING, 0, 0 },
    { WAN_DEATH, 3, 0 },
    { SCR_CHARGING, 0, 0 },
    { MAGIC_MARKER, 40, 0 },
    { WAN_WISHING, 1, 1 },
};

#define HEAVEN_DRAW 8

static void
heaven_altar(coordxy x, coordxy y, unsigned amask)
{
    schar rno;
    struct mkroom *croom = 0;

    levl[x][y].typ = ALTAR;
    levl[x][y].altarmask = (uchar) (amask | AM_SHRINE | AM_SANCTUM);
    rno = (schar) *in_rooms(x, y, TEMPLE);
    if (rno > 0)
        croom = &svr.rooms[rno - ROOMOFFSET];
    if (croom)
        priestini(&u.uz, croom, (int) x, (int) y, TRUE);
    svl.level.flags.has_temple = TRUE;
}

static void
heaven_fill_chest(struct obj *box)
{
    int i, n, k, pick[SIZE(heaven_chest)];
    struct obj *obj;

    n = 0;
    for (i = 0; i < SIZE(heaven_chest); i++)
        if (!heaven_chest[i].rare)
            pick[n++] = i;
    for (i = n - 1; i > 0; i--) {
        k = rn2(i + 1);
        if (k != i) {
            int tmp = pick[i];

            pick[i] = pick[k];
            pick[k] = tmp;
        }
    }
    if (n > HEAVEN_DRAW)
        n = HEAVEN_DRAW;
    for (i = 0; i < n; i++) {
        obj = mksobj(heaven_chest[pick[i]].otyp, FALSE, FALSE);
        if (!obj)
            continue;
        bless(obj);
        obj->spe = heaven_chest[pick[i]].spe;
        obj->known = obj->dknown = obj->bknown = 1;
        (void) add_to_container(box, obj);
    }
    if (!rn2(5)) {
        obj = mksobj(WAN_WISHING, FALSE, FALSE);
        if (obj) {
            bless(obj);
            obj->spe = 1;
            obj->known = obj->dknown = obj->bknown = 1;
            (void) add_to_container(box, obj);
        }
    }
    box->owt = weight(box);
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
    heaven_fill_chest(box);
    place_object(box, sx[order[2]], sy[order[2]]);
}

void
heaven_dragon_end(void)
{
    pline("Darkness covereth thee. Thou hast offered unto the Great Dragon, and the light of the Lord is gone out from thee.");
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, "offered unto the Great Dragon");
    done(DIED);
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
