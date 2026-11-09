/* RighteousHack: the Wayside, the first trial on the return ascent.
   State lives on the PLAYER_SOUL object, which is already saved.
   The level is a one-level branch. It is not written over a
   Gehennom level the hero already walked on the way down. */

#include "hack.h"

/* corpsenm on the carried soul */
#define WS_SOLVED  0x0000003f
#define WS_INTRO   0x00000040
#define WS_PUNISH  0x00000080
#define WS_MINO    0x00000100
#define WS_GIANT   0x00000200
#define WS_ROAD    0x01000000

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

static struct obj *
ws_soul(void)
{
    return carried_player_soul();
}

static int
ws_bits(void)
{
    struct obj *soul = ws_soul();

    return soul ? soul->corpsenm : 0;
}

static void
ws_set(int bits)
{
    struct obj *soul = ws_soul();

    if (soul)
        soul->corpsenm = bits;
}

boolean
wayside_road(void)
{
    return (boolean) ((ws_bits() & WS_ROAD) != 0);
}

void
wayside_begin(void)
{
    struct obj *soul = ws_soul();

    if (!soul)
        return;
    soul->corpsenm |= WS_ROAD;
}

static boolean
on_wayside(void)
{
    s_level *slev = find_level("wayside");

    return (boolean) (slev && on_level(&u.uz, &slev->dlevel));
}

static int
villager_no(struct monst *mtmp)
{
    int i;

    if (!mtmp || !has_mgivenname(mtmp))
        return -1;
    for (i = 0; i < 6; i++)
        if (!strcmp(MGIVENNAME(mtmp), ws_name[i]))
            return i;
    return -1;
}

static boolean
is_villager(struct monst *mtmp)
{
    /* The given name is the riddle. Do not also require the level
       id, or a missed level match makes every villager mute. */
    return (boolean) (villager_no(mtmp) >= 0);
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
            (void) strncpy(buf, p, (size_t) (nl - p));
            buf[nl - p] = '\0';
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

static boolean
gate_open(void)
{
    return (boolean) ((ws_bits() & WS_SOLVED) == WS_SOLVED);
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
    int n = svd.dungeons[sanctum_level.dnum].num_dunlevs;
    coordxy ux = WX(72), uy = 3, dx = WX(5), dy = 18;

    down.dnum = up.dnum = sanctum_level.dnum;
    down.dlevel = (xint16) (n - 1); /* vibrating square */
    up.dlevel = (xint16) (n - 2);   /* one level above it */
    if (up.dlevel < 1)
        up.dlevel = 1;
    /* The branch placer drops an extra stair on whatever square it
       finds, including a wall. Keep only the courtyard and the court. */
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

    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++)
            if (IS_WALL(levl[x][y].typ))
                levl[x][y].wall_info |= (W_NONDIGGABLE | W_NONPASSWALL);
}

void
wayside_setup(void)
{
    seal_walls();
    fix_stairs();
    if (gate_open())
        open_gate();
}

static void
spawn_punishment(void)
{
    struct monst *m;

    if (ws_bits() & WS_PUNISH)
        return;
    ws_set(ws_bits() | WS_PUNISH);
    ws_set(ws_bits() & ~(WS_MINO | WS_GIANT));
    m = makemon(&mons[PM_MINOTAUR], SPA_X1, SPA_Y, NO_MM_FLAGS);
    if (m)
        m->mpeaceful = 0;
    m = makemon(&mons[PM_STORM_GIANT], SPA_X2, SPA_Y, NO_MM_FLAGS);
    if (m)
        m->mpeaceful = 0;
    teleds(RET_X, RET_Y, 0);
}

static void
clear_punishment(void)
{
    int bits = ws_bits();

    if ((bits & (WS_MINO | WS_GIANT)) != (WS_MINO | WS_GIANT))
        return;
    bits &= ~(WS_PUNISH | WS_MINO | WS_GIANT);
    ws_set(bits);
}

static boolean
answer_ok(int which, const char *guess)
{
    char la[BUFSZ], lb[BUFSZ];
    char *p, *q, *s;

    if (!guess || !*guess || *guess == '\033')
        return FALSE;
    for (p = (char *) guess; *p == ' '; p++)
        ;
    Strcpy(la, p);
    for (q = eos(la); q > la && q[-1] == ' '; q--)
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
    int which, bits;
    char buf[BUFSZ];

    which = villager_no(mtmp);
    if (which < 0)
        return;
    bits = ws_bits();
    if (bits & WS_PUNISH)
        return;
    if (bits & (1 << which)) {
        /* PLACEHOLDER */
        verbalize("You already have that answer.");
        return;
    }
    show_text(ws_body[which]);
    getlin("What am I?", buf);
    if (!*buf || *buf == '\033')
        return;
    if (answer_ok(which, buf)) {
        ws_set(ws_bits() | (1 << which));
        if (gate_open()) {
            open_gate();
            /* PLACEHOLDER */
            pline("The gate opens.");
        }
    } else {
        /* PLACEHOLDER: no locked line for a wrong answer. */
        pline("That is not the answer.");
        spawn_punishment();
    }
}

boolean
wayside_chat(struct monst *mtmp)
{
    if (!is_villager(mtmp))
        return FALSE;
    mtmp->mstrategy &= ~STRAT_WAITMASK;
    mtmp->msleeping = 0;
    mtmp->mcanmove = 1;
    if (ws_bits() & WS_PUNISH)
        return TRUE;
    ask_riddle(mtmp);
    return TRUE;
}

boolean
wayside_villager_stands(struct monst *mtmp)
{
    if (!is_villager(mtmp))
        return FALSE;
    mtmp->mhp = mtmp->mhpmax;
    mtmp->mpeaceful = 1;
    spawn_punishment();
    return TRUE;
}

void
wayside_monster_died(struct monst *mtmp)
{
    if (!on_wayside() || !mtmp || !mtmp->data)
        return;
    if (mtmp->data == &mons[PM_MINOTAUR])
        ws_set(ws_bits() | WS_MINO);
    else if (mtmp->data == &mons[PM_STORM_GIANT])
        ws_set(ws_bits() | WS_GIANT);
    clear_punishment();
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
    if (gate_open())
        open_gate();
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (!is_villager(mtmp))
            continue;
        mtmp->mpeaceful = 1;
        mtmp->msleeping = 0;
        mtmp->mcanmove = 1;
    }
}

static boolean
go_wayside(void)
{
    s_level *slev = find_level("wayside");

    if (!slev)
        return FALSE;
    goto_level(&slev->dlevel, TRUE, FALSE, FALSE);
    return TRUE;
}

/* The Cap is checked again here, not only on the Sanctum stairs. */
static boolean
cap_still_worn(void)
{
    if (cap_of_salvation_worn())
        return TRUE;
    pline("The Road to Salvation is not yet open.");
    return FALSE;
}

boolean
wayside_take_up(void)
{
    if (!wayside_road())
        return FALSE;
    if (Invocation_lev(&u.uz)) {
        if (!cap_still_worn())
            return TRUE;
        return go_wayside();
    }
    if (on_wayside() && !gate_open()) {
        /* PLACEHOLDER */
        pline("The way on is shut.");
        return TRUE;
    }
    return FALSE;
}

boolean
wayside_take_down(void)
{
    int above;

    if (!wayside_road() || !In_hell(&u.uz))
        return FALSE;
    above = svd.dungeons[u.uz.dnum].num_dunlevs - 2;
    if (u.uz.dlevel != above)
        return FALSE;
    if (!cap_still_worn())
        return TRUE;
    return go_wayside();
}

boolean
wayside_blocks_levelport(void)
{
    /* The other three trials are not in this patch, so the lock
       stays on once the Road has begun. */
    if (!wayside_road())
        return FALSE;
    /* PLACEHOLDER */
    You_feel("very disoriented for a moment.");
    return TRUE;
}
