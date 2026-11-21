/* RighteousHack: the Stony Ground, the second trial on the Road.
   State lives on the hero (u.ustony) and is saved with struct you.
   EDITLEVEL 14. Nothing here is written into bones. */

#include "hack.h"

/* Map column 0 is level x = 1. Rows are unchanged. */
#define MX(c) ((coordxy) ((c) + 1))
#define MY(r) ((coordxy) (r))

#define START_X MX(0)
#define START_Y MY(19)
#define EXIT_X MX(20)
#define EXIT_Y MY(2)
#define CHEST_X MX(48)
#define CHEST_Y MY(13)

#define SG_DONE_OLD   0x00000001UL
#define SG_DONE_YOUNG 0x00000002UL
#define SG_DONE_MOTH  0x00000004UL
#define SG_DONE_ALL   (SG_DONE_OLD | SG_DONE_YOUNG | SG_DONE_MOTH)
#define SG_HEALED     0x00000008UL
#define SG_CALMED     0x00000010UL
#define SG_RING       0x00000020UL
#define SG_PRAY_M     0x00000040UL
#define SG_SICK       0x00000080UL
#define SG_WARN_Y     0x00000100UL
#define SG_FRESH      0x00000200UL /* sick timer skips this turn */
#define SG_CALLED     0x00000400UL
#define SG_RESET      0x00000800UL
#define SG_CHAT       0x00001000UL /* young believer's first line has been said */
/* Permanent summit vitality. Survives apply_reset. One bit each. */
#define SG_HP_OLD     0x00002000UL
#define SG_HP_YOUNG   0x00004000UL
#define SG_HP_MOTH    0x00008000UL
#define SG_HP_ALL     (SG_HP_OLD | SG_HP_YOUNG | SG_HP_MOTH)
#define SG_ESC_SHIFT  16

#define SG_OLD   1
#define SG_YOUNG 2
#define SG_MOTH  3

static const char *const sg_name[3] = {
    "old man", "young believer", "mother"
};

/* Map coordinates. The four dark bands are in the order the path
   climbs them, bridge first and summit last. */
static const coord sg_ss[] = { {47, 5}, {48, 5} };
static const coord sg_w[] = { {35, 1}, {35, 2}, {35, 3} };
static const coord sg_x[] = { {27, 1}, {27, 2}, {27, 3} };
static const coord sg_b0[] = {
    {44, 4}, {45, 4}, {46, 4}, {47, 4}, {48, 4}, {49, 4}, {50, 4}, {51, 4}
};
static const coord sg_b1[] = { {41, 3} };
static const coord sg_b2[] = { {31, 1}, {31, 2} };
static const coord sg_b3[] = { {22, 1}, {22, 2}, {22, 3} };

static const coord *const sg_band[] = { sg_b0, sg_b1, sg_b2, sg_b3 };
static const int sg_band_n[] = {
    (int) SIZE(sg_b0), (int) SIZE(sg_b1),
    (int) SIZE(sg_b2), (int) SIZE(sg_b3)
};

static boolean
stony_level(d_level *lev)
{
    s_level *slev = find_level("stony");

    return (boolean) (slev && lev && on_level(lev, &slev->dlevel));
}

boolean
stony_here(void)
{
    return stony_level(&u.uz);
}

static unsigned long
sg_bits(void)
{
    return u.ustony.bits;
}

static void
sg_set(unsigned long bits)
{
    u.ustony.bits = bits;
}

static void grant_summit_hp(int);

static int
escort_of(void)
{
    return (int) ((sg_bits() >> SG_ESC_SHIFT) & 3);
}

static void
set_escort(int who)
{
    unsigned long bits = sg_bits() & ~(3UL << SG_ESC_SHIFT);

    if (who)
        bits |= ((unsigned long) who) << SG_ESC_SHIFT;
    sg_set(bits);
}

static int
name_who(struct monst *mtmp)
{
    int i;

    if (!mtmp || !has_mgivenname(mtmp))
        return 0;
    for (i = 0; i < 3; i++)
        if (!strcmp(MGIVENNAME(mtmp), sg_name[i]))
            return i + 1;
    return 0;
}

static struct monst *
traveler_by(int who)
{
    struct monst *mtmp;
    unsigned id;

    if (who < 1 || who > 3)
        return (struct monst *) 0;
    id = u.ustony.id[who - 1];
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp))
            continue;
        if (id && mtmp->m_id == id)
            return mtmp;
        if (!id && name_who(mtmp) == who)
            return mtmp;
    }
    return (struct monst *) 0;
}

boolean
stony_is_traveler(struct monst *mtmp)
{
    if (!mtmp || DEADMONSTER(mtmp))
        return FALSE;
    if (mtmp->data != &mons[PM_TRAVELER])
        return FALSE;
    return (boolean) (name_who(mtmp) != 0);
}

static boolean
on_list(const coord *cells, int n, coordxy x, coordxy y)
{
    int i;

    for (i = 0; i < n; i++)
        if (MX(cells[i].x) == x && MY(cells[i].y) == y)
            return TRUE;
    return FALSE;
}

static boolean
mother_safe(void)
{
    return (boolean) ((sg_bits() & (SG_RING | SG_PRAY_M)) != 0);
}

static boolean
all_delivered(void)
{
    return (boolean) ((sg_bits() & SG_DONE_ALL) == SG_DONE_ALL);
}

static boolean
square_lit(coordxy x, coordxy y)
{
    light_source *ls;

    if (!isok(x, y))
        return FALSE;
    if (levl[x][y].lit)
        return TRUE;
    for (ls = gl.light_base; ls; ls = ls->next) {
        if (ls->range <= 0)
            continue;
        if (dist2(ls->x, ls->y, x, y) <= ls->range * ls->range)
            return TRUE;
    }
    return FALSE;
}

static boolean
band_lit(int band)
{
    int i;

    for (i = 0; i < sg_band_n[band]; i++)
        if (!square_lit(MX(sg_band[band][i].x), MY(sg_band[band][i].y)))
            return FALSE;
    return TRUE;
}

static int
first_unlit(void)
{
    int i;

    for (i = 0; i < 4; i++)
        if (!band_lit(i))
            return i;
    return -1;
}

static boolean
passable(coordxy x, coordxy y)
{
    schar typ;

    if (!isok(x, y))
        return FALSE;
    typ = levl[x][y].typ;
    if (IS_STWALL(typ) || typ == STONE || IS_LAVA(typ)
        || typ == LAVAPOOL || typ == MOAT || typ == POOL)
        return FALSE;
    if (typ == ROOM || typ == CORR || typ == STAIRS || typ == FOUNTAIN
        || IS_DRAWBRIDGE(typ))
        return TRUE;
    return FALSE;
}

static void
fail_screen(int who)
{
    const char *text = 0;

    if (who == SG_OLD)
        text = "The old man's breath faileth, and he slumpeth upon the stones.\n"
               "\n"
               "Thou didst not lay hands upon him in his hour of need.\n"
               "\n"
               "The old man hath not made it. Thou art returned to the foot of the pass, to begin again.";
    else if (who == SG_YOUNG)
        text = "The young believer rusheth ahead, heedless of thy cry.\n"
               "\n"
               "From among the rocks the persecutors fall upon him, and he is overcome. His zeal had no root.\n"
               "\n"
               "The young believer hath not made it. Thou art returned to the foot of the pass, to begin again.";
    else if (who == SG_MOTH)
        text = "The darkness closeth about the mother, and her heart melteth for fear.\n"
               "\n"
               "She turneth and fleeth down the mountain with her child, and the persecutors pursue her.\n"
               "\n"
               "The mother hath not made it. Thou art returned to the foot of the pass, to begin again.";
    if (text)
        wayside_screen(text);
    sg_set(sg_bits() | SG_RESET);
}

static void
light_camp(void)
{
    coordxy x, y;

    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            if (!passable(x, y))
                continue;
            /* Camp is the lit bowl on rows 10 through 14. */
            levl[x][y].lit = (y >= 10 && y <= 14) ? 1 : 0;
        }
}

static void
make_bridge(void)
{
    coordxy x, y;

    for (y = 5; y <= 9; y++)
        for (x = 47; x <= 48; x++) {
            coordxy lx = MX(x), ly = MY(y);

            if (!isok(lx, ly))
                continue;
            levl[lx][ly].typ = DRAWBRIDGE_DOWN;
            levl[lx][ly].drawbridgemask = (unsigned char) (DB_LAVA | DB_NORTH);
            levl[lx][ly].lit = 0;
        }
}

static void
seal_stone(void)
{
    coordxy x, y;

    svl.level.flags.rndmongen = 0;
    svl.level.flags.hardfloor = 1;
    for (x = 0; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            if (IS_STWALL(levl[x][y].typ))
                levl[x][y].wall_info |= (W_NONDIGGABLE | W_NONPASSWALL);
        }
}

static struct obj *
camp_chest(boolean create)
{
    struct obj *obj;

    if (isok(CHEST_X, CHEST_Y))
        for (obj = svl.level.objects[CHEST_X][CHEST_Y]; obj; obj = obj->nexthere)
            if (obj->otyp == CHEST)
                return obj;
    if (!create)
        return (struct obj *) 0;
    obj = mksobj(CHEST, FALSE, FALSE);
    if (!obj)
        return (struct obj *) 0;
    obj->olocked = 0;
    place_object(obj, CHEST_X, CHEST_Y);
    return obj;
}

static void
identify_trial(struct obj *obj)
{
    if (!obj)
        return;
    obj->dknown = obj->known = obj->bknown = obj->rknown = 1;
    makeknown(obj->otyp);
}

static struct obj *
fresh_trial_obj(int which)
{
    struct obj *obj = 0;

    if (which == 0)
        obj = mksobj(WAN_SLEEP, TRUE, FALSE);          /* rod of tranquility */
    else if (which == 1)
        obj = mksobj(SPE_HEALING, TRUE, FALSE);        /* prophetic book of healing */
    else {
        obj = mksobj(RIN_PROTECTION, TRUE, FALSE);
        if (obj) {
            obj->spe = 5;
            bless(obj);
        }
    }
    identify_trial(obj);
    return obj;
}

static void
remember_contents(struct obj *chest)
{
    struct obj *obj;
    int i;

    for (i = 0; i < 3; i++)
        u.ustony.oid[i] = 0;
    if (!chest)
        return;
    for (obj = chest->cobj; obj; obj = obj->nobj) {
        identify_trial(obj);
        if (obj->otyp == WAN_SLEEP)
            u.ustony.oid[0] = obj->o_id;
        else if (obj->otyp == SPE_HEALING)
            u.ustony.oid[1] = obj->o_id;
        else if (obj->otyp == RIN_PROTECTION)
            u.ustony.oid[2] = obj->o_id;
    }
}

static void
pull_into(struct obj *chest, unsigned id, int which)
{
    struct obj *obj;

    if (!chest)
        return;
    obj = id ? find_oid(id) : 0;
    if (obj) {
        if (obj->owornmask)
            remove_worn_item(obj, FALSE);
        obj_extract_self(obj);
    } else {
        obj = fresh_trial_obj(which);
    }
    if (!obj)
        return;
    identify_trial(obj);
    (void) add_to_container(chest, obj);
    u.ustony.oid[which] = obj->o_id;
}

static void
restock_chest(void)
{
    struct obj *chest = camp_chest(TRUE);

    if (!chest)
        return;
    chest->olocked = 0;
    pull_into(chest, u.ustony.oid[0], 0);
    pull_into(chest, u.ustony.oid[1], 1);
    pull_into(chest, u.ustony.oid[2], 2);
    chest->owt = weight(chest);
}

static void
tag_travelers(void)
{
    struct monst *mtmp;
    int who;

    for (who = 0; who < 3; who++)
        u.ustony.id[who] = 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        who = name_who(mtmp);
        if (!who)
            continue;
        u.ustony.id[who - 1] = mtmp->m_id;
        mtmp->mpeaceful = 1;
        mtmp->mtame = 0;
        mtmp->mstrategy |= STRAT_WAITFORU;
        mtmp->msleeping = 0;
    }
}

static void
place_traveler(int who, coordxy x, coordxy y)
{
    struct monst *mtmp = traveler_by(who);

    if (mtmp) {
        if (mtmp->mx != x || mtmp->my != y) {
            remove_monster(mtmp->mx, mtmp->my);
            place_monster(mtmp, x, y);
        }
        mtmp->mhp = mtmp->mhpmax;
        mtmp->mpeaceful = 1;
        mtmp->mtame = 0;
        mtmp->mstrategy |= STRAT_WAITFORU;
        newsym(x, y);
        return;
    }
    mtmp = makemon(&mons[PM_TRAVELER], x, y, MM_NOWAIT);
    if (!mtmp)
        return;
    mtmp = christen_monst(mtmp, sg_name[who - 1]);
    if (!mtmp)
        return;
    u.ustony.id[who - 1] = mtmp->m_id;
    mtmp->mpeaceful = 1;
    mtmp->mtame = 0;
    mtmp->mstrategy |= STRAT_WAITFORU;
}

static void
clear_persecutors(void)
{
    struct monst *mtmp, *nmt;

    for (mtmp = fmon; mtmp; mtmp = nmt) {
        nmt = mtmp->nmon;
        if (!DEADMONSTER(mtmp) && mtmp->data == &mons[PM_PERSECUTOR])
            mongone(mtmp);
    }
}

static void
aim_stairs(void)
{
    stairway *st;
    d_level back, onward;

    if (u.uz0.dnum || u.uz0.dlevel)
        back = u.uz0;
    else if (find_level("wayside"))
        back = find_level("wayside")->dlevel;
    else
        back = valley_level;
    if (stony_level(&back))
        back = find_level("wayside") ? find_level("wayside")->dlevel
                                     : valley_level;

    wayside_ascent_level(&onward);

    for (st = gs.stairs; st; st = st->next) {
        if (st->sx == START_X && st->sy == START_Y) {
            st->up = TRUE;
            assign_level(&st->tolev, &back);
            levl[st->sx][st->sy].ladder = LA_UP;
        } else if (st->sx == EXIT_X && st->sy == EXIT_Y) {
            st->up = FALSE;
            assign_level(&st->tolev, &onward);
            levl[st->sx][st->sy].ladder = LA_DOWN;
        }
    }
}

static void
apply_reset(void)
{
    /* The summit vitality stays. A second escort does not grant it again. */
    sg_set(sg_bits() & SG_HP_ALL);
    u.ustony.sick = 0;
    clear_persecutors();
    place_traveler(SG_YOUNG, MX(42), MY(11));
    place_traveler(SG_OLD, MX(48), MY(11));
    place_traveler(SG_MOTH, MX(54), MY(11));
    light_camp();
    make_bridge();
    restock_chest();
    if (u.ustuck)
        set_ustuck((struct monst *) 0);
    u_on_newpos(START_X, START_Y);
    vision_reset();
    vision_recalc(0);
    docrt();
    /* The blackout already said why. */
}

void
stony_setup(void)
{
    if (!stony_here())
        return;
    seal_stone();
    make_bridge();
    light_camp();
    tag_travelers();
    remember_contents(camp_chest(FALSE));
    if (!u.ustony.oid[0] || !u.ustony.oid[1] || !u.ustony.oid[2])
        restock_chest();
    aim_stairs();
    vision_reset();
    vision_recalc(0);
}

static void
step_toward(struct monst *mtmp)
{
    coordxy ox = mtmp->mx, oy = mtmp->my;
    coordxy bestx = ox, besty = oy;
    int bestd = dist2(ox, oy, u.ux, u.uy);
    coordxy dx, dy;

    for (dx = -1; dx <= 1; dx++)
        for (dy = -1; dy <= 1; dy++) {
            coordxy nx = ox + dx, ny = oy + dy;
            int d;

            if (!dx && !dy)
                continue;
            if (!passable(nx, ny) || u_at(nx, ny) || MON_AT(nx, ny))
                continue;
            d = dist2(nx, ny, u.ux, u.uy);
            if (d < bestd) {
                bestd = d;
                bestx = nx;
                besty = ny;
            }
        }
    if (bestx == ox && besty == oy)
        return;
    remove_monster(ox, oy);
    place_monster(mtmp, bestx, besty);
    newsym(ox, oy);
    newsym(bestx, besty);
}

static void
maybe_call(struct monst *mtmp, int who)
{
    int gap = distmin(mtmp->mx, mtmp->my, u.ux, u.uy);

    if (gap > 5) {
        if (!(sg_bits() & SG_CALLED)) {
            pline("The %s calleth after thee, 'Wait for me!'", sg_name[who - 1]);
            sg_set(sg_bits() | SG_CALLED);
        }
        return;
    }
    if (gap <= 3)
        sg_set(sg_bits() & ~SG_CALLED);
    if (gap > 1)
        step_toward(mtmp);
}

static void
deliver(int who)
{
    unsigned long bit = (who == SG_OLD) ? SG_DONE_OLD
                        : (who == SG_YOUNG) ? SG_DONE_YOUNG
                                            : SG_DONE_MOTH;
    const char *line = 0;

    set_escort(0);
    sg_set((sg_bits() & ~SG_CALLED) | bit);
    if (who == SG_OLD)
        line = "The old man leaneth upon thy shoulder and smileth. 'I have fought a good fight, I have finished my course, I have kept the faith. I could not have climbed alone. Bless thee, my child.'";
    else if (who == SG_YOUNG)
        line = "The young believer turneth to thee with tears in his eyes. 'I would have perished in my haste. But let patience have her perfect work, that ye may be perfect and entire, wanting nothing. Thou hast taught me patience, and now my faith hath taken root. I thank thee, friend.'";
    else
        line = "The mother lifteth her child toward the light. 'The LORD is my light and my salvation; whom shall I fear? Thou didst not leave us in the darkness. God bless thee, friend.'";
    pline("%s", line);
    /* Once per traveler, for the whole game. A later sentence could
       be added here, after the summit speech. */
    grant_summit_hp(who);
}

/* +10 permanent maximum, and +10 current, in this form and in the
   hero's own body. The bit is what stops a reset from paying twice. */
static void
grant_summit_hp(int who)
{
    unsigned long bit = (who == SG_OLD) ? SG_HP_OLD
                        : (who == SG_YOUNG) ? SG_HP_YOUNG
                                            : SG_HP_MOTH;

    if (sg_bits() & bit)
        return;
    sg_set(sg_bits() | bit);
    u.uhp += 10;
    setuhpmax(u.uhpmax + 10, TRUE);
    if (Upolyd) {
        u.mh += 10;
        setuhpmax(u.mhmax + 10, FALSE);
    }
}

static void
check_triggers(struct monst *mtmp, int who)
{
    coordxy x = mtmp->mx, y = mtmp->my;

    if (who == SG_OLD && !(sg_bits() & (SG_HEALED | SG_SICK))
        && on_list(sg_ss, (int) SIZE(sg_ss), x, y)) {
        pline("The old man sinketh to his knees, pale and trembling. 'My strength faileth me! Pray for me, or lay hands upon me, for I shall not last long!'");
        u.ustony.sick = 2;
        sg_set(sg_bits() | SG_SICK | SG_FRESH);
        return;
    }
    if (who == SG_YOUNG && !(sg_bits() & SG_CALMED)) {
        if (!(sg_bits() & SG_WARN_Y) && on_list(sg_w, (int) SIZE(sg_w), x, y)) {
            pline("The young believer's eyes burn with zeal. 'I can wait no longer! If thou wilt not hasten, I shall go on without thee!'");
            sg_set(sg_bits() | SG_WARN_Y);
            return;
        }
        if (on_list(sg_x, (int) SIZE(sg_x), x, y)) {
            fail_screen(SG_YOUNG);
            return;
        }
    }
    if (who == SG_MOTH && !mother_safe()) {
        int unlit = first_unlit();
        int i, warned;

        if (unlit < 0)
            return;
        warned = (int) ((sg_bits() >> 18) & 7);
        if (warned != unlit + 1
            && ((unlit == 0 && on_list(sg_ss, (int) SIZE(sg_ss), x, y))
                || (unlit > 0
                    && on_list(sg_band[unlit - 1], sg_band_n[unlit - 1], x, y)))) {
            sg_set((sg_bits() & ~(7UL << 18)) | ((unsigned long) (unlit + 1) << 18));
            pline("The mother clutcheth her child and trembleth. 'They will take my child! I cannot go on, I must turn back!'");
        }
        for (i = 0; i < 4; i++) {
            if (band_lit(i))
                continue;
            if (on_list(sg_band[i], sg_band_n[i], x, y)) {
                fail_screen(SG_MOTH);
                return;
            }
        }
    }
}

static void
maybe_deliver(struct monst *mtmp, int who)
{
    unsigned long bit = (who == SG_OLD) ? SG_DONE_OLD
                        : (who == SG_YOUNG) ? SG_DONE_YOUNG
                                            : SG_DONE_MOTH;

    if (sg_bits() & bit)
        return;
    if (distmin(mtmp->mx, mtmp->my, EXIT_X, EXIT_Y) > 1)
        return;
    if (distmin(u.ux, u.uy, EXIT_X, EXIT_Y) > 2)
        return;
    deliver(who);
}

static void
spawn_persecutor(void)
{
    struct monst *mtmp;
    int n = 0, tries;
    coordxy x, y;

    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && mtmp->data == &mons[PM_PERSECUTOR])
            n++;
    if (n >= 4 || rn2(30))
        return;
    for (tries = 0; tries < 40; tries++) {
        x = (coordxy) rn2(COLNO);
        y = (coordxy) rn2(ROWNO);
        if (y >= 10 && y <= 14)
            continue;
        if (!passable(x, y) || MON_AT(x, y) || u_at(x, y))
            continue;
        if (levl[x][y].typ == STAIRS)
            continue;
        (void) makemon(&mons[PM_PERSECUTOR], x, y, MM_NOWAIT);
        return;
    }
}

void
stony_tick(void)
{
    struct monst *mtmp;
    int who;

    if (!stony_here())
        return;
    if (sg_bits() & SG_RESET) {
        apply_reset();
        return;
    }
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (!stony_is_traveler(mtmp))
            continue;
        mtmp->mpeaceful = 1;
        mtmp->mtame = 0;
        mtmp->mstrategy |= STRAT_WAITFORU;
        mtmp->msleeping = 0;
    }
    who = escort_of();
    if (who && !(sg_bits() & (SG_DONE_OLD << (who - 1)))) {
        mtmp = traveler_by(who);
        if (mtmp) {
            maybe_call(mtmp, who);
            if (!(sg_bits() & SG_RESET))
                check_triggers(mtmp, who);
            if (!(sg_bits() & SG_RESET) && escort_of() == who)
                maybe_deliver(mtmp, who);
        }
    }
    if (sg_bits() & SG_RESET) {
        apply_reset();
        return;
    }
    if ((sg_bits() & SG_SICK) && u.ustony.sick > 0) {
        if (sg_bits() & SG_FRESH) {
            sg_set(sg_bits() & ~SG_FRESH);
        } else {
            u.ustony.sick--;
            if (u.ustony.sick <= 0)
                fail_screen(SG_OLD);
        }
    }
    if (sg_bits() & SG_RESET) {
        apply_reset();
        return;
    }
    spawn_persecutor();
}

static boolean
give_ring(struct monst *mtmp)
{
    struct obj *obj, *best = 0;

    for (obj = gi.invent; obj; obj = obj->nobj)
        if (obj->otyp == RIN_PROTECTION && obj->spe >= 5)
            best = obj;
    if (!best)
        return FALSE;
    if (y_n("Give the mother the ring of protection?") != 'y')
        return TRUE;
    if (best->owornmask)
        remove_worn_item(best, FALSE);
    freeinv(best);
    (void) mpickobj(mtmp, best);
    sg_set(sg_bits() | SG_RING);
    pline("The mother taketh the ring of protection.");
    return TRUE;
}

boolean
stony_chat(struct monst *mtmp)
{
    int who, esc;

    if (!stony_is_traveler(mtmp))
        return FALSE;
    who = name_who(mtmp);
    esc = escort_of();
    if (sg_bits() & (SG_DONE_OLD << (who - 1))) {
        pline("The %s remaineth at the summit.", sg_name[who - 1]);
        return TRUE;
    }
    if (who == SG_YOUNG) {
        if (!(sg_bits() & SG_CHAT)) {
            pline("The young believer paceth restlessly. 'Why do we wait? I could be at the summit already! I cannot abide this slowness, my heart burneth within me!'");
            sg_set(sg_bits() | SG_CHAT);
        } else if (rn2(2)) {
            pline("'Make haste, make haste! The LORD is up there, and I will not tarry for anyone. Mine eyes are fixed upon the summit, and my feet will not be still!'");
        } else {
            pline("The young believer paceth restlessly. 'Why do we wait? I could be at the summit already! I cannot abide this slowness, my heart burneth within me!'");
        }
    }
    if (esc && esc != who) {
        pline("Thou art already walking with another.");
        return TRUE;
    }
    if (!esc) {
        set_escort(who);
        pline("The %s walketh with thee.", sg_name[who - 1]);
    }
    if (who == SG_MOTH)
        (void) give_ring(mtmp);
    return TRUE;
}

static void
heal_old(void)
{
    if (!(sg_bits() & SG_SICK) || (sg_bits() & SG_HEALED))
        return;
    if (escort_of() != SG_OLD)
        return;
    u.ustony.sick = 0;
    sg_set((sg_bits() & ~(SG_SICK | SG_FRESH)) | SG_HEALED);
    pline("The old man riseth, and his strength is renewed. 'Bless thee, my child.'");
}

static void
calm_young(boolean must_escort)
{
    if (sg_bits() & SG_CALMED)
        return;
    if (must_escort && escort_of() != SG_YOUNG)
        return;
    sg_set(sg_bits() | SG_CALMED);
    pline("The young believer's breathing slows. 'Forgive me. I was hasty. I will walk beside thee.'");
}

static void
cover_mother(void)
{
    if (mother_safe())
        return;
    if (escort_of() != SG_MOTH)
        return;
    sg_set(sg_bits() | SG_PRAY_M);
}

void
stony_prayer(void)
{
    int who;

    if (!stony_here())
        return;
    who = escort_of();
    if (who == SG_OLD)
        heal_old();
    else if (who == SG_YOUNG)
        calm_young(TRUE);
    else if (who == SG_MOTH)
        cover_mother();
}

void
stony_read_healing(void)
{
    struct monst *mtmp;

    if (!stony_here() || escort_of() != SG_OLD)
        return;
    if (!(sg_bits() & SG_SICK))
        return;
    mtmp = traveler_by(SG_OLD);
    if (!mtmp || distmin(u.ux, u.uy, mtmp->mx, mtmp->my) > 1)
        return;
    heal_old();
}

boolean
stony_absorb_zap(struct monst *mtmp, struct obj *otmp)
{
    int otyp;

    if (!stony_is_traveler(mtmp) || !otmp)
        return FALSE;
    otyp = otmp->otyp;
    if (name_who(mtmp) == SG_YOUNG
        && (otyp == WAN_SLEEP || otyp == SPE_SLEEP
            || otyp == WAN_SLOW_MONSTER || otyp == SPE_SLOW_MONSTER)) {
        makeknown(otyp);
        calm_young(FALSE);
        return TRUE;
    }
    if (name_who(mtmp) == SG_OLD
        && (otyp == SPE_HEALING || otyp == SPE_EXTRA_HEALING)) {
        makeknown(otyp);
        heal_old();
        return TRUE;
    }
    return TRUE; /* a traveler is never harmed by a zap */
}

boolean
stony_unharmed(struct monst *mtmp)
{
    int who;

    if (!stony_is_traveler(mtmp))
        return FALSE;
    who = name_who(mtmp);
    if (who)
        pline("The %s is not thine enemy.", sg_name[who - 1]);
    return TRUE;
}

boolean
stony_traveler_fell(struct monst *mtmp)
{
    int who;

    if (!stony_is_traveler(mtmp))
        return FALSE;
    who = name_who(mtmp);
    mtmp->mhp = mtmp->mhpmax;
    /* Only the one walking with the hero. The others stay in camp. */
    if (who && escort_of() == who)
        fail_screen(who);
    return TRUE;
}

boolean
stony_block_stairs(boolean up)
{
    if (!stony_here() || up)
        return FALSE;
    if (u.ux != EXIT_X || u.uy != EXIT_Y)
        return FALSE;
    if (all_delivered())
        return FALSE;
    pline("The summit stair is shut until all three have reached the top.");
    return TRUE;
}

/*stony.c*/
