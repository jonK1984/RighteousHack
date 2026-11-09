/* RighteousHack: the Wayside, the first trial on the return ascent.
   Progress lives on the hero (u.uwayside), which is saved with
   struct you. It does not live on the soul's corpsenm: mksobj()
   sets that field to NON_PM (-1), which would turn every flag on. */

#include "hack.h"

#define WS_SOLVED   0x0000003fUL
#define WS_INTRO    0x00000040UL
#define WS_PUNISH   0x00000080UL
#define WS_MINO     0x00000100UL
#define WS_GIANT    0x00000200UL
#define WS_ROAD     0x00000400UL
#define WS_TOLD     0x00000800UL

#define WS_MODE_LEVEL   1 /* an unvisited ordinary Gehennom level */
#define WS_MODE_INSERT  2 /* new level between the square and the next */

static const char *const ws_name[6] = {
    "Confused villager",
    "Bewildered villager",
    "Perplexed villager",
    "Puzzled villager",
    "Baffled villager",
    "Befuddled villager",
};
static const char *const ws_answer[6] = {
    "Forgiveness",
    "Repentance",
    "Grace",
    "Faith",
    "Truth",
    "Justice",
};
static const char *const ws_body[6] = {
    "I settle a score by refusing to even it.\nI release a debt without receiving payment.\nI lose what I am owed, yet call it no loss.",
    "I change your course without moving your feet.\nI cannot undo a wrong, but I can refuse it another turn.\nYou cannot move forward with me until you turn around.",
    "If given, I am free;\nTry to purchase, you cannot afford.\nI come without price, yet cost the highest of prices.",
    "I am possessed by a child.\nYou can lose me without misplacing me.\nMy power is strongest when you are at your weakest.",
    "I'm easy for the simple.\nBut hard for most to hear.\nTry to hide me, I do not disappear.",
    "I am blind, yet see through evil,\nIf purchased, my value goes to none.\nA servant may have me, but a king is not above me.",
};

/* Map column 0 is level x = 1. Rows are unchanged. */
#define WX(c) ((coordxy) ((c) + 1))
#define GATE_X WX(70)
#define GATE_Y 6
#define RET_X WX(10)
#define RET_Y 16
#define SPA_X1 WX(8)
#define SPA_X2 WX(12)
#define SPA_Y 16

static unsigned long
ws_bits(void)
{
    return u.uwayside.bits;
}

static void
ws_set(unsigned long bits)
{
    u.uwayside.bits = bits;
}

boolean
wayside_road(void)
{
    return (boolean) ((ws_bits() & WS_ROAD) != 0);
}

static boolean
trial_done(void)
{
    return (boolean) ((ws_bits() & WS_SOLVED) == WS_SOLVED);
}

static int
gehennom_depth(void)
{
    return svd.dungeons[sanctum_level.dnum].num_dunlevs;
}

static boolean
on_wayside(void)
{
    if (u.uwayside.mode == WS_MODE_LEVEL && u.uwayside.target > 0
        && u.uz.dnum == sanctum_level.dnum
        && u.uz.dlevel == u.uwayside.target)
        return TRUE;
    {
        s_level *slev = find_level("wayside");

        return (boolean) (slev && on_level(&u.uz, &slev->dlevel));
    }
}

boolean
wayside_generate_here(void)
{
    return (boolean) (wayside_road()
                      && u.uwayside.mode == WS_MODE_LEVEL
                      && u.uwayside.target > 0
                      && u.uz.dnum == sanctum_level.dnum
                      && u.uz.dlevel == u.uwayside.target);
}

static boolean
wayside_dest(d_level *dest)
{
    if (u.uwayside.mode == WS_MODE_LEVEL && u.uwayside.target > 0) {
        dest->dnum = sanctum_level.dnum;
        dest->dlevel = u.uwayside.target;
        return TRUE;
    }
    if (u.uwayside.mode == WS_MODE_INSERT) {
        s_level *slev = find_level("wayside");

        if (!slev)
            return FALSE;
        *dest = slev->dlevel;
        return TRUE;
    }
    return FALSE;
}

/* A move that would pass the trial without landing on it. */
static boolean
crosses_wayside(d_level *from, d_level *to)
{
    d_level ws;
    int lo, hi;

    if (!wayside_road() || trial_done())
        return FALSE;
    if (!wayside_dest(&ws))
        return FALSE;
    if (on_level(to, &ws) || on_level(from, &ws))
        return FALSE;
    if (from->dnum != sanctum_level.dnum || to->dnum != sanctum_level.dnum)
        return FALSE;
    lo = min(from->dlevel, to->dlevel);
    hi = max(from->dlevel, to->dlevel);
    if (u.uwayside.mode == WS_MODE_LEVEL)
        return (boolean) (lo < u.uwayside.target && hi > u.uwayside.target);
    /* Inserted level sits between the vibrating square and the
       level directly above it. */
    {
        int n = gehennom_depth();

        return (boolean) (lo <= n - 2 && hi >= n - 1);
    }
}

/* TRUE: caller must abort the level change.
   FALSE: *newlevel may have been rewritten onto the Wayside. */
boolean
wayside_steer(d_level *newlevel)
{
    d_level ws;

    if (!newlevel || !crosses_wayside(&u.uz, newlevel))
        return FALSE;
    if (!cap_of_salvation_worn()) {
        pline("The Road to Salvation is not yet open.");
        return TRUE;
    }
    if (!wayside_dest(&ws))
        return FALSE;
    *newlevel = ws;
    return FALSE;
}

static void
wayside_choose(void)
{
    s_level *orc;
    int od, vd, n, d;
    int cand[32];
    d_level lev;

    if (u.uwayside.mode != 0)
        return;
    orc = find_level("orcus");
    vd = (sanctum_level.dlevel > 1) ? sanctum_level.dlevel - 1 : 1;
    od = (orc && orc->dlevel.dnum == sanctum_level.dnum)
             ? orc->dlevel.dlevel : 0;
    n = 0;
    /* Strictly between Orcustown and the vibrating square.
       Endpoints are not candidates. */
    if (od > 0 && od < vd) {
        for (d = od + 1; d < vd && n < (int) SIZE(cand); d++) {
            int ledger;

            lev.dnum = sanctum_level.dnum;
            lev.dlevel = (xint16) d;
            if (Is_special(&lev) || Is_branchlev(&lev))
                continue;
            ledger = ledger_no(&lev);
            if (ledger <= 0)
                continue;
            /* A visited or already-written level is not regenerated. */
            if (svl.level_info[ledger].flags & (VISITED | LFILE_EXISTS))
                continue;
            cand[n++] = d;
        }
    }
    if (n > 0) {
        u.uwayside.mode = WS_MODE_LEVEL;
        u.uwayside.target = (xint16) cand[rn2(n)];
        return;
    }
    /* Approved fallback: a new level on the ascent. This is not a
       stand-in for the random draw; the draw found nobody. */
    u.uwayside.mode = WS_MODE_INSERT;
    u.uwayside.target = 0;
    if (!(ws_bits() & WS_TOLD)) {
        ws_set(ws_bits() | WS_TOLD);
        /* New wording, not locked text. */
        if (od > 0 && od < vd)
            pline("Every ordinary level between Orcustown and the vibrating square has already been walked. The Wayside is set into the ascent between the vibrating square and the level above it.");
        else
            pline("Orcustown is not between you and the vibrating square, so the Wayside is set into the ascent between the vibrating square and the level above it.");
    }
}

void
wayside_begin(void)
{
    if (!carried_player_soul())
        return;
    if (ws_bits() & WS_ROAD) {
        wayside_choose();
        return;
    }
    ws_set(ws_bits() | WS_ROAD);
    wayside_choose();
}

static int
name_house(struct monst *mtmp)
{
    int i;

    if (!mtmp || !has_mgivenname(mtmp))
        return -1;
    for (i = 0; i < 6; i++)
        if (!strcmp(MGIVENNAME(mtmp), ws_name[i]))
            return i;
    return -1;
}

boolean
wayside_is_villager(struct monst *mtmp)
{
    int i, house;

    if (!mtmp || DEADMONSTER(mtmp) || !on_wayside())
        return FALSE;
    for (i = 0; i < 6; i++)
        if (u.uwayside.vid[i] && mtmp->m_id == u.uwayside.vid[i])
            return TRUE;
    house = name_house(mtmp);
    if (house < 0)
        return FALSE;
    /* First sight of the placed actor. Later renames do not matter. */
    if (!u.uwayside.vid[house])
        u.uwayside.vid[house] = mtmp->m_id;
    return TRUE;
}

static void
show_text(const char *text)
{
    winid win;
    char buf[BUFSZ];
    const char *p, *nl;

    win = create_nhwindow(NHW_TEXT);
    p = text;
    while (p && *p) {
        nl = strchr(p, '\n');
        if (!nl) {
            putstr(win, 0, p);
            break;
        }
        if (nl == p)
            putstr(win, 0, "");
        else {
            size_t len = (size_t) (nl - p);

            if (len >= sizeof buf)
                len = sizeof buf - 1;
            (void) strncpy(buf, p, len);
            buf[len] = '\0';
            putstr(win, 0, buf);
        }
        p = nl + 1;
    }
    display_nhwindow(win, TRUE);
    destroy_nhwindow(win);
}

static void
show_intro(void)
{
    show_text(
        "You have come to the Wayside, where many hear, but few understand.\n"
        "\n"
        "Six homes stand beside the road. Within each waits a troubled villager, holding a riddle whose answer has slipped beyond their grasp.\n"
        "\n"
        "Help them recover what they have lost, and the way before you shall open. But weigh your answers carefully. An error will cast you back to the courtyard, where more than questions await you.\n"
        "\n"
        "Listen closely. Consider well. Then answer.");
}

static void
open_gate(void)
{
    if (!on_wayside() || !isok(GATE_X, GATE_Y))
        return;
    if (levl[GATE_X][GATE_Y].typ == DOOR
        && (levl[GATE_X][GATE_Y].doormask & D_NODOOR))
        return;
    levl[GATE_X][GATE_Y].typ = DOOR;
    levl[GATE_X][GATE_Y].doormask = D_NODOOR;
    levl[GATE_X][GATE_Y].wall_info = 0;
    newsym(GATE_X, GATE_Y);
}

static void
forget_stair(stairway *gone)
{
    stairway **pp;

    for (pp = &gs.stairs; *pp; pp = &(*pp)->next)
        if (*pp == gone) {
            *pp = gone->next;
            if (isok(gone->sx, gone->sy) && levl[gone->sx][gone->sy].typ == STAIRS)
                levl[gone->sx][gone->sy].typ = ROOM;
            free(gone);
            return;
        }
}

static void
put_stair(coordxy x, coordxy y, boolean up, d_level *dest)
{
    if (!isok(x, y))
        return;
    levl[x][y].typ = STAIRS;
    levl[x][y].ladder = up ? LA_UP : LA_DOWN;
    stairway_add(x, y, up, FALSE, dest);
}

static void
fix_stairs(void)
{
    stairway *st, *nxt;
    d_level down, up;
    int n = gehennom_depth();
    coordxy ux = WX(72), uy = 3, dx = WX(5), dy = 18;

    down.dnum = up.dnum = sanctum_level.dnum;
    if (u.uwayside.mode == WS_MODE_LEVEL && u.uwayside.target > 1) {
        up.dlevel = (xint16) (u.uwayside.target - 1);
        down.dlevel = (xint16) (u.uwayside.target + 1);
        if (down.dlevel > n)
            down.dlevel = (xint16) n;
    } else {
        down.dlevel = (xint16) (n - 1); /* vibrating square */
        up.dlevel = (xint16) (n - 2);   /* one level above it */
        if (up.dlevel < 1)
            up.dlevel = 1;
    }
    for (st = gs.stairs; st; st = nxt) {
        nxt = st->next;
        if (!((st->up && st->sx == ux && st->sy == uy)
              || (!st->up && st->sx == dx && st->sy == dy)))
            forget_stair(st);
    }
    if (!stairway_at(ux, uy))
        put_stair(ux, uy, TRUE, &up);
    else
        assign_level(&stairway_at(ux, uy)->tolev, &up);
    if (!stairway_at(dx, dy))
        put_stair(dx, dy, FALSE, &down);
    else
        assign_level(&stairway_at(dx, dy)->tolev, &down);
}

static void
seal_walls(void)
{
    coordxy x, y;

    svl.level.flags.rndmongen = 0;
    svl.level.flags.noteleport = 1;
    svl.level.flags.hardfloor = 1;
    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            if (IS_WALL(levl[x][y].typ) || IS_TREE(levl[x][y].typ))
                levl[x][y].wall_info |= (W_NONDIGGABLE | W_NONPASSWALL);
        }
}

static void
tag_villagers(void)
{
    struct monst *mtmp;

    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        int house;

        if (DEADMONSTER(mtmp))
            continue;
        house = name_house(mtmp);
        if (house >= 0 && !u.uwayside.vid[house])
            u.uwayside.vid[house] = mtmp->m_id;
    }
}

void
wayside_setup(void)
{
    seal_walls();
    fix_stairs();
    tag_villagers();
    if (trial_done())
        open_gate();
}

static boolean
floor_ok(coordxy x, coordxy y)
{
    schar typ;

    if (!isok(x, y) || u_at(x, y))
        return FALSE;
    typ = levl[x][y].typ;
    if (typ != ROOM && typ != CORR)
        return FALSE;
    if (MON_AT(x, y))
        return FALSE;
    return TRUE;
}

/* Prefer the marked tile. Otherwise any courtyard floor.
   Never covers the hero or a monster. */
static boolean
reserve_tile(coordxy px, coordxy py, coordxy ax, coordxy ay,
             coordxy *ox, coordxy *oy)
{
    coordxy x, y;

    if (floor_ok(px, py) && !(px == ax && py == ay)) {
        *ox = px;
        *oy = py;
        return TRUE;
    }
    for (y = 14; y <= 19; y++)
        for (x = WX(1); x <= WX(17); x++)
            if (floor_ok(x, y) && !(x == ax && y == ay)) {
                *ox = x;
                *oy = y;
                return TRUE;
            }
    return FALSE;
}

static struct monst *
mon_here(unsigned id)
{
    struct monst *mtmp;

    if (!id)
        return (struct monst *) 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && mtmp->m_id == id)
            return mtmp;
    return (struct monst *) 0;
}

static struct monst *
make_one(int pm, coordxy x, coordxy y)
{
    unsigned save;
    struct monst *mtmp;

    save = svm.mvitals[pm].mvflags;
    svm.mvitals[pm].mvflags &= ~(unsigned) G_GENOD;
    mtmp = makemon(&mons[pm], x, y, NO_MM_FLAGS | MM_NOGRP | NO_MINVENT);
    svm.mvitals[pm].mvflags = save;
    if (mtmp)
        mtmp->mpeaceful = 0;
    return mtmp;
}

static void
return_hero(void)
{
    coordxy rx = 0, ry = 0;

    if (!on_wayside())
        return;
    /* Already back from an earlier hit in this same action. */
    if ((ws_bits() & WS_PUNISH)
        && u.ux >= WX(1) && u.ux <= WX(17)
        && u.uy >= 14 && u.uy <= 19)
        return;
    if (!reserve_tile(RET_X, RET_Y, 0, 0, &rx, &ry))
        return;
    if (u_at(rx, ry))
        return;
    teleds(rx, ry, 0);
}

static void
start_punishment(void)
{
    coordxy x1 = 0, y1 = 0, x2 = 0, y2 = 0;
    struct monst *mino, *giant;

    if (ws_bits() & WS_PUNISH) {
        /* Same pair. Do not create another. */
        return_hero();
        return;
    }
    if (!reserve_tile(SPA_X1, SPA_Y, 0, 0, &x1, &y1)
        || !reserve_tile(SPA_X2, SPA_Y, x1, y1, &x2, &y2)) {
        /* New wording. The penalty is not abandoned silently:
           the riddle is not locked, because there is nowhere
           to put the pair. */
        pline("There is no open ground in the courtyard for the penalty.");
        return;
    }
    mino = make_one(PM_MINOTAUR, x1, y1);
    giant = make_one(PM_STORM_GIANT, x2, y2);
    if (!mino || !giant) {
        if (mino)
            mongone(mino);
        if (giant)
            mongone(giant);
        pline("There is no open ground in the courtyard for the penalty.");
        return;
    }
    ws_set((ws_bits() | WS_PUNISH) & ~(WS_MINO | WS_GIANT));
    u.uwayside.mino_id = mino->m_id;
    u.uwayside.giant_id = giant->m_id;
    return_hero();
}

static void
ensure_pair(void)
{
    coordxy x = 0, y = 0;
    struct monst *mtmp;

    if (!(ws_bits() & WS_PUNISH) || !on_wayside())
        return;
    if (u.uwayside.mino_id && !(ws_bits() & WS_MINO)
        && !mon_here(u.uwayside.mino_id)) {
        if (reserve_tile(SPA_X1, SPA_Y, 0, 0, &x, &y)) {
            mtmp = make_one(PM_MINOTAUR, x, y);
            if (mtmp)
                u.uwayside.mino_id = mtmp->m_id;
        }
    }
    x = y = 0;
    if (u.uwayside.giant_id && !(ws_bits() & WS_GIANT)
        && !mon_here(u.uwayside.giant_id)) {
        if (reserve_tile(SPA_X2, SPA_Y, 0, 0, &x, &y)) {
            mtmp = make_one(PM_STORM_GIANT, x, y);
            if (mtmp)
                u.uwayside.giant_id = mtmp->m_id;
        }
    }
}

static boolean
blank_answer(const char *guess)
{
    const char *p;

    if (!guess || !*guess || *guess == '\033')
        return TRUE;
    for (p = guess; *p == ' ' || *p == '\t'; p++)
        ;
    return (boolean) (*p == '\0');
}

static boolean
answer_ok(int which, const char *guess)
{
    char la[BUFSZ], lb[BUFSZ];
    char *p, *q, *s;

    if (blank_answer(guess))
        return FALSE;
    for (p = (char *) guess; *p == ' ' || *p == '\t'; p++)
        ;
    Strcpy(la, p);
    for (q = eos(la); q > la && (q[-1] == ' ' || q[-1] == '\t'); q--)
        ;
    *q = '\0';
    Strcpy(lb, ws_answer[which]);
    for (s = la; *s; s++)
        *s = (char) lowc(*s);
    for (s = lb; *s; s++)
        *s = (char) lowc(*s);
    return (boolean) !strcmp(la, lb);
}

static void
ask_riddle(struct monst *mtmp)
{
    int which;
    char buf[BUFSZ];

    which = -1;
    {
        int i;

        for (i = 0; i < 6; i++)
            if (u.uwayside.vid[i] && mtmp->m_id == u.uwayside.vid[i])
                which = i;
    }
    if (which < 0)
        which = name_house(mtmp);
    if (which < 0)
        return;
    if (ws_bits() & WS_PUNISH) {
        /* New wording, not locked text. */
        pline("The courtyard is not clear.");
        return;
    }
    if (ws_bits() & (1UL << which)) {
        /* PLACEHOLDER */
        verbalize("You already have that answer.");
        return;
    }
    show_text(ws_body[which]);
    getlin("What am I?", buf);
    if (blank_answer(buf))
        return;
    if (answer_ok(which, buf)) {
        ws_set(ws_bits() | (1UL << which));
        if (trial_done()) {
            open_gate();
            /* PLACEHOLDER */
            pline("The gate opens.");
        }
    } else {
        /* PLACEHOLDER: no locked line for a wrong answer. */
        pline("That is not the answer.");
        start_punishment();
    }
}

boolean
wayside_chat(struct monst *mtmp)
{
    if (!wayside_is_villager(mtmp))
        return FALSE;
    mtmp->msleeping = 0;
    mtmp->mcanmove = 1;
    mtmp->mpeaceful = 1;
    if (ws_bits() & WS_PUNISH) {
        pline("The courtyard is not clear.");
        return TRUE;
    }
    ask_riddle(mtmp);
    return TRUE;
}

/* Death was reached anyway. The villager stays. This is not the
   hero-attack penalty; that is wayside_hero_strikes(). */
boolean
wayside_villager_stands(struct monst *mtmp)
{
    if (!wayside_is_villager(mtmp))
        return FALSE;
    mtmp->mhp = mtmp->mhpmax;
    mtmp->mpeaceful = 1;
    mtmp->mtame = 0;
    return TRUE;
}

void
wayside_hero_strikes(struct monst *mtmp)
{
    if (!wayside_is_villager(mtmp))
        return;
    mtmp->mhp = mtmp->mhpmax;
    mtmp->mpeaceful = 1;
    mtmp->mtame = 0;
    start_punishment();
}

void
wayside_monster_died(struct monst *mtmp)
{
    unsigned long bits;

    if (!mtmp)
        return;
    bits = ws_bits();
    if (!(bits & WS_PUNISH))
        return;
    if (u.uwayside.mino_id && mtmp->m_id == u.uwayside.mino_id)
        bits |= WS_MINO;
    else if (u.uwayside.giant_id && mtmp->m_id == u.uwayside.giant_id)
        bits |= WS_GIANT;
    else
        return;
    if ((bits & (WS_MINO | WS_GIANT)) == (WS_MINO | WS_GIANT)) {
        bits &= ~(WS_PUNISH | WS_MINO | WS_GIANT);
        u.uwayside.mino_id = 0;
        u.uwayside.giant_id = 0;
    }
    ws_set(bits);
}

void
wayside_tick(void)
{
    struct monst *mtmp;

    if (!on_wayside())
        return;
    if (wayside_road() && !(ws_bits() & WS_INTRO)) {
        show_intro();
        ws_set(ws_bits() | WS_INTRO);
    }
    if (trial_done())
        open_gate();
    tag_villagers();
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (!wayside_is_villager(mtmp))
            continue;
        mtmp->mpeaceful = 1;
        mtmp->mtame = 0;
        mtmp->msleeping = 0;
        mtmp->mcanmove = 1;
        mtmp->mhp = mtmp->mhpmax;
        mtmp->mstrategy &= ~STRAT_CLOSE;
        mtmp->mstrategy |= STRAT_WAITFORU;
    }
    ensure_pair();
}

static boolean
go_wayside(void)
{
    d_level dest;

    if (!wayside_dest(&dest))
        return FALSE;
    goto_level(&dest, TRUE, FALSE, FALSE);
    return TRUE;
}

static boolean
cap_still_worn(void)
{
    if (trial_done())
        return TRUE;
    if (cap_of_salvation_worn())
        return TRUE;
    pline("The Road to Salvation is not yet open.");
    return FALSE;
}

static boolean
entering_inserted(boolean up)
{
    int n, edge;

    if (!wayside_road() || u.uwayside.mode != WS_MODE_INSERT)
        return FALSE;
    if (!In_hell(&u.uz))
        return FALSE;
    n = gehennom_depth();
    if (up)
        return (boolean) Invocation_lev(&u.uz);
    edge = n - 2;
    return (boolean) (u.uz.dlevel == edge);
}

static boolean
entering_replaced(boolean up)
{
    if (!wayside_road() || u.uwayside.mode != WS_MODE_LEVEL)
        return FALSE;
    if (u.uz.dnum != sanctum_level.dnum || u.uwayside.target <= 0)
        return FALSE;
    if (up)
        return (boolean) (u.uz.dlevel == u.uwayside.target + 1);
    return (boolean) (u.uz.dlevel == u.uwayside.target - 1);
}

boolean
wayside_take_up(void)
{
    if (!wayside_road())
        return FALSE;
    if (on_wayside() && !trial_done()) {
        /* PLACEHOLDER */
        pline("The way on is shut.");
        return TRUE;
    }
    if (entering_inserted(TRUE) || entering_replaced(TRUE)) {
        if (!cap_still_worn())
            return TRUE;
        if (u.uwayside.mode == WS_MODE_INSERT)
            return go_wayside();
        return FALSE; /* ordinary stair into the chosen level */
    }
    return FALSE;
}

boolean
wayside_take_down(void)
{
    if (!wayside_road())
        return FALSE;
    if (entering_inserted(FALSE) || entering_replaced(FALSE)) {
        if (!cap_still_worn())
            return TRUE;
        if (u.uwayside.mode == WS_MODE_INSERT)
            return go_wayside();
        return FALSE;
    }
    return FALSE;
}

boolean
wayside_blocks_levelport(void)
{
    /* The other three trials are not in this patch, so the lock
       stays on once the Road has begun. Nothing here marks them done. */
    if (!wayside_road())
        return FALSE;
    /* New wording, not locked text. The road is actually unfinished. */
    pline("The Road to Salvation is unfinished, so level teleport is sealed. Only the Wayside has been appointed; three trials are still to come.");
    return TRUE;
}
