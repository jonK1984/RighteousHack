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
/* The Sanctum key has already dropped from his first tower defeat.
   Stored in the existing bits word, so the save layout does not grow. */
#define WS_SKEY     0x00001000UL

/* Saved host slots. Four trials fill the slots. */
#define TRIAL_SLOTS 4

static const char *const ws_name[6] = {
    "Confused villager",
    "Bewildered villager",
    "Perplexed villager",
    "Puzzled villager",
    "Baffled villager",
    "Befuddled villager",
};
static const char *const ws_adj[6] = {
    "confused",
    "bewildered",
    "perplexed",
    "puzzled",
    "baffled",
    "befuddled",
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

static int gehennom_depth(void);
static boolean wayside_is_solved(void);
static void trial_choose(void);

/* To add a trial: a one-level unconnected dungeon, its level file,
   and one row here. Do not add a row until the level file exists. */
struct trial_def {
    const char *dname;
    const char *proto;
    boolean (*done)(void);
};

static const struct trial_def trial_list[] = {
    { "The Wayside", "wayside", wayside_is_solved },
    { "The Stony Ground", "stony", stony_trial_done },
    { "The Thorns", "thorns", thorns_trial_done },
    { "The Good Ground", "goodground", goodground_trial_done },
};
#define N_TRIALS ((int) SIZE(trial_list))

boolean
wayside_road(void)
{
    return (boolean) ((ws_bits() & WS_ROAD) != 0);
}

static boolean
wayside_is_solved(void)
{
    return (boolean) ((ws_bits() & WS_SOLVED) == WS_SOLVED);
}

static boolean
trial_done(void)
{
    return wayside_is_solved();
}

static int
gehennom_depth(void)
{
    return svd.dungeons[sanctum_level.dnum].num_dunlevs;
}

boolean
wayside_at(d_level *lev)
{
    s_level *slev;

    if (!lev)
        return FALSE;
    slev = find_level("wayside");
    return (boolean) (slev && on_level(lev, &slev->dlevel));
}

static boolean
gehennom_ordinary(int dlev)
{
    d_level lev;
    int n = gehennom_depth();

    /* The valley is 1. The gateway and the Sanctum are the bottom two. */
    if (dlev <= 1 || dlev >= n - 1)
        return FALSE;
    lev.dnum = sanctum_level.dnum;
    lev.dlevel = (xint16) dlev;
    if (Is_special(&lev) || Is_branchlev(&lev))
        return FALSE;
    return TRUE;
}

static int
trial_index(d_level *lev)
{
    int i;

    if (!lev)
        return -1;
    for (i = 0; i < N_TRIALS; i++) {
        s_level *slev = find_level(trial_list[i].proto);

        if (slev && on_level(lev, &slev->dlevel))
            return i;
    }
    return -1;
}

boolean
on_trial(d_level *lev)
{
    return (boolean) (trial_index(lev) >= 0);
}

/* hostdnum 0 is the Dungeons of Doom, a real dungeon, so an unset
   host is told by host[i] == 0 rather than by the dnum. */
static void
host_of(int i, d_level *lev)
{
    lev->dlevel = u.uwayside.host[i];
    lev->dnum = u.uwayside.hostdnum[i];
    if (lev->dnum < 0 || lev->dnum >= svn.n_dgns)
        lev->dnum = sanctum_level.dnum;
}

static int
hosting(d_level *lev)
{
    int i;
    d_level host;

    if (!lev)
        return -1;
    for (i = 0; i < N_TRIALS; i++) {
        if (!u.uwayside.host[i])
            continue;
        host_of(i, &host);
        if (on_level(lev, &host))
            return i;
    }
    return -1;
}

/* Foot stair returns to the host. Exit stair climbs to the level
   that host's own up stair would have reached. */
boolean
trial_link(const char *proto, d_level *back, d_level *onward)
{
    int i;

    if (!proto || !back || !onward)
        return FALSE;
    for (i = 0; i < N_TRIALS; i++)
        if (!strcmp(trial_list[i].proto, proto))
            break;
    if (i >= N_TRIALS || !u.uwayside.host[i])
        return FALSE;
    host_of(i, back);
    *onward = *back;
    onward->dlevel = (xint16) (back->dlevel > 1 ? back->dlevel - 1 : 1);
    return TRUE;
}

static int
trials_left(void)
{
    int i, n = 0;

    for (i = 0; i < N_TRIALS; i++)
        if (!trial_list[i].done())
            n++;
    return n;
}

static boolean
hosts_chosen(void)
{
    int i;

    for (i = 0; i < N_TRIALS && i < TRIAL_SLOTS; i++)
        if (u.uwayside.host[i])
            return TRUE;
    return FALSE;
}

/* The Good Ground is hosted in the Dungeons of Doom, strictly
   between Sodom and Tyre and the prophet, and nowhere else. */
static s_level *
placed_medusa(void)
{
    s_level *slev = find_level("medusa");

    if (slev)
        return slev;
    for (slev = svs.sp_levchn; slev; slev = slev->next)
        if (slev->proto && !strncmp(slev->proto, "medusa", 6))
            return slev;
    return (s_level *) 0;
}

static boolean
doom_ordinary(int dlev)
{
    s_level *med = placed_medusa();
    s_level *pro = find_level("prophet");
    d_level lev;
    int lo, hi;

    if (!med || !pro || med->dlevel.dnum != pro->dlevel.dnum)
        return FALSE;
    lo = min(med->dlevel.dlevel, pro->dlevel.dlevel);
    hi = max(med->dlevel.dlevel, pro->dlevel.dlevel);
    if (dlev <= lo || dlev >= hi)
        return FALSE;
    lev.dnum = med->dlevel.dnum;
    lev.dlevel = (xint16) dlev;
    if (Is_special(&lev) || Is_branchlev(&lev))
        return FALSE;
    return TRUE;
}

/* Ordinary Gehennom levels only, with an ordinary level between
   every pair. The Good Ground draws its host from the Dungeons. */
static void
trial_choose(void)
{
    int cand[64];
    int pick[TRIAL_SLOTS];
    int n = 0, got = 0, guard = 0, i, geh = 0, gslot = -1;

    if (hosts_chosen()) {
        trial_set_depths();
        return;
    }
    for (i = 0; i < N_TRIALS; i++) {
        if (!strcmp(trial_list[i].proto, "goodground"))
            gslot = i;
        else
            geh++;
    }
    for (i = 1; i <= gehennom_depth() && n < (int) SIZE(cand); i++)
        if (gehennom_ordinary(i))
            cand[n++] = i;
    while (got < geh && got < TRIAL_SLOTS && guard++ < 500 && n > 0) {
        int c = cand[rn2(n)];
        boolean ok = TRUE;
        int j;

        for (j = 0; j < got; j++) {
            int lo = min(c, pick[j]);
            int hi = max(c, pick[j]);
            int ord = 0, d;

            if (c == pick[j]) {
                ok = FALSE;
                break;
            }
            for (d = lo + 1; d < hi; d++)
                if (gehennom_ordinary(d))
                    ord++;
            if (ord < 1)
                ok = FALSE;
        }
        if (ok)
            pick[got++] = c;
    }
    {
        int k = 0;

        for (i = 0; i < N_TRIALS && i < TRIAL_SLOTS; i++) {
            if (i == gslot)
                continue;
            if (k < got) {
                u.uwayside.host[i] = (xint16) pick[k++];
                u.uwayside.hostdnum[i] = sanctum_level.dnum;
            }
        }
    }
    if (gslot >= 0 && gslot < TRIAL_SLOTS) {
        s_level *med = placed_medusa();
        int dcand[64], nd = 0, c, depth;

        if (med) {
            depth = svd.dungeons[med->dlevel.dnum].num_dunlevs;
            for (i = 1; i <= depth && nd < (int) SIZE(dcand); i++)
                if (doom_ordinary(i))
                    dcand[nd++] = i;
            if (nd > 0) {
                c = dcand[rn2(nd)];
                u.uwayside.host[gslot] = (xint16) c;
                u.uwayside.hostdnum[gslot] = med->dlevel.dnum;
            }
        }
    }
    trial_set_depths();
}

/* Dlvl and the overview both use depth_start. A trial is not
   dungeon level 1; it sits at the depth of its Gehennom host. */
void
trial_set_depths(void)
{
    int i;

    for (i = 0; i < N_TRIALS && i < TRIAL_SLOTS; i++) {
        s_level *slev;
        d_level host;

        if (!u.uwayside.host[i])
            continue;
        slev = find_level(trial_list[i].proto);
        if (!slev || slev->dlevel.dnum < 0 || slev->dlevel.dnum >= svn.n_dgns)
            continue;
        host_of(i, &host);
        svd.dungeons[slev->dlevel.dnum].depth_start = depth(&host);
    }
}

/* Arrival in either direction. The generic stair search does not
   know that a trial stair and a Gehennom stair point at each other. */
void
trial_receive(d_level *from)
{
    int here, src;
    stairway *st;

    if (!from)
        return;
    here = trial_index(&u.uz);
    src = trial_index(from);
    if (here >= 0 && u.uwayside.host[here]) {
        d_level host, above;

        host_of(here, &host);
        above = host;
        if (above.dlevel > 1)
            above.dlevel--;
        if (on_level(from, &host)) {
            st = stairway_find_dir(FALSE);
            if (st)
                u_on_newpos(st->sx, st->sy);
        } else if (on_level(from, &above)) {
            st = stairway_find_dir(TRUE);
            if (st)
                u_on_newpos(st->sx, st->sy);
        }
        return;
    }
    if (src >= 0 && u.uwayside.host[src]) {
        d_level host, above;

        host_of(src, &host);
        above = host;
        if (above.dlevel > 1)
            above.dlevel--;
        if (on_level(&u.uz, &host)) {
            st = stairway_find_dir(TRUE);
            if (st)
                u_on_newpos(st->sx, st->sy);
        } else if (on_level(&u.uz, &above)) {
            st = stairway_find_dir(FALSE);
            if (st)
                u_on_newpos(st->sx, st->sy);
        }
    }
}

static boolean
on_wayside(void)
{
    return wayside_at(&u.uz);
}

void
wayside_begin(void)
{
    if (!carried_player_soul())
        return;
    if (!(ws_bits() & WS_ROAD))
        ws_set(ws_bits() | WS_ROAD);
    trial_choose();
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

void
wayside_screen(const char *text)
{
    rh_text_window(text);
}

static void
show_intro(void)
{
    wayside_screen(
        "You have come to the Wayside, where seeing, they see not; and hearing, they hear not, neither do they understand.\n"
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

/* tty and curses can paint a character and a standard color, then
   wait. A tiled port, or a port with no delay, is left alone. */
static boolean
gate_can_play(void)
{
    const char *port;

    if (iflags.debug_fuzzer || !iflags.window_inited || !u.ux)
        return FALSE;
    if (WIN_MAP == WIN_ERR)
        return FALSE;
    if (!windowprocs.win_print_glyph || !windowprocs.win_delay_output)
        return FALSE;
    if (iflags.wc_tiled_map)
        return FALSE;
    port = windowprocs.name;
    if (!port)
        return FALSE;
    return (boolean) (!strcmp(port, "tty") || !strcmp(port, "curses"));
}

static void
gate_put(coordxy x, coordxy y, char ch, int color)
{
    glyph_info *cell;

    if (!isok(x, y))
        return;
    cell = &gg.gbuf[y][x].glyphinfo;

    *cell = nul_glyphinfo;
    cell->glyph = cmap_to_glyph(S_room);
    cell->ttychar = (int) ch;
    cell->gm.sym.color = color;
    cell->gm.glyphflags = 0;
    cell->gm.customcolor = 0;
#ifdef ENHANCED_SYMBOLS
    cell->gm.u = (struct unicode_representation *) 0;
#endif
    gg.gbuf[y][x].gnew = 1;
}

static void
gate_copy(coordxy x, coordxy y, const glyph_info *src)
{
    gg.gbuf[y][x].glyphinfo = *src;
    gg.gbuf[y][x].gnew = 1;
}

/* The port naps 50 ms. Two naps are about a tenth of a second,
   near the 90 ms shimmer and the 110 ms drift. */
static void
gate_show(int naps)
{
    coordxy y;
    int i;

    for (y = 0; y < ROWNO; y++) {
        gg.gbuf_start[y] = 1;
        gg.gbuf_stop[y] = COLNO - 1;
    }
    flush_screen(1);
    for (i = 0; i < naps; i++)
        nh_delay_output();
}

static void
gate_restore(glyph_info *snap)
{
    coordxy x, y;

    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            gate_copy(x, y, &snap[y * COLNO + x]);
}

static void
gate_shimmer(coordxy x, coordxy y)
{
    static const char chs[3] = { '#', '*', '+' };
    static const int cols[4] = {
        CLR_BRIGHT_CYAN, CLR_BRIGHT_BLUE, CLR_CYAN, CLR_WHITE
    };

    gate_put(x, y, chs[rn2_on_display_rng(3)], cols[rn2_on_display_rng(4)]);
}

static boolean
gate_floor(coordxy x, coordxy y, coordxy cx, coordxy cy)
{
    schar typ;

    if (!isok(x, y) || u_at(x, y))
        return FALSE;
    if (x == cx && y == cy)
        return FALSE;
    typ = levl[x][y].typ;
    return (boolean) (typ == ROOM || typ == CORR);
}

/* The wall is still shut. Ten frames of shimmer, then nine of
   sparkles drifting onto the floor. When open_center is set, the
   doorway appears after the first three of those. No message.
   Sparkles use the display RNG. The caller has already decided
   the port can play this. */
static void
play_gate_burst(coordxy cx, coordxy cy, boolean open_center)
{
    glyph_info *snap;
    boolean save_nap, opened;
    coordxy x, y;
    int frame, i;
    struct {
        int x, y, dx, dy;
    } spark[9];
    static const char fade_ch[4] = { '*', '+', '.', '.' };
    static const int fade_co[4] = {
        CLR_BRIGHT_CYAN, CLR_BRIGHT_BLUE, CLR_BLUE, CLR_GRAY
    };

    snap = (glyph_info *) alloc((unsigned) (COLNO * ROWNO * sizeof *snap));
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            snap[y * COLNO + x] = gg.gbuf[y][x].glyphinfo;

    for (i = 0; i < 9; i++) {
        spark[i].x = (int) cx + rn2_on_display_rng(3) - 1;
        spark[i].y = (int) cy;
        spark[i].dy = rn2_on_display_rng(2) ? 1 : -1;
        spark[i].dx = rn2_on_display_rng(3) - 1;
    }

    /* curses skips nh_delay_output when timed_delay is off. Hold the
       option on for this burst and put it back. */
    save_nap = flags.nap;
    flags.nap = TRUE;
    opened = FALSE;

    for (frame = 0; frame < 10; frame++) {
        gate_restore(snap);
        if (isok(cx, cy) && !u_at(cx, cy))
            gate_shimmer(cx, cy);
        if (isok(cx - 1, cy) && !u_at(cx - 1, cy)
            && rn2_on_display_rng(5) < 3)
            gate_shimmer(cx - 1, cy);
        if (isok(cx + 1, cy) && !u_at(cx + 1, cy)
            && rn2_on_display_rng(5) < 3)
            gate_shimmer(cx + 1, cy);
        gate_show(2);
    }

    for (frame = 0; frame < 9; frame++) {
        int step = frame / 2;

        if (open_center && frame == 3) {
            open_gate();
            opened = TRUE;
            snap[cy * COLNO + cx] = gg.gbuf[cy][cx].glyphinfo;
        }
        gate_restore(snap);
        if (frame < 3 && isok(cx, cy) && !u_at(cx, cy))
            gate_put(cx, cy,
                     rn2_on_display_rng(2) ? '*' : '+', CLR_BRIGHT_CYAN);
        if (step > 3)
            step = 3;
        for (i = 0; i < 9; i++) {
            if (frame % 2 == 1) {
                spark[i].x += spark[i].dx;
                spark[i].y += spark[i].dy;
            }
            if (!gate_floor((coordxy) spark[i].x, (coordxy) spark[i].y,
                            cx, cy))
                continue;
            gate_put((coordxy) spark[i].x, (coordxy) spark[i].y,
                     fade_ch[step], fade_co[step]);
        }
        gate_show(2);
    }

    if (open_center && !opened) {
        open_gate();
        snap[cy * COLNO + cx] = gg.gbuf[cy][cx].glyphinfo;
    }
    gate_restore(snap);
    for (y = 0; y < ROWNO; y++) {
        gg.gbuf_start[y] = 1;
        gg.gbuf_stop[y] = COLNO - 1;
    }
    flush_screen(1);
    flags.nap = save_nap;
    free((genericptr_t) snap);
}

static void
dissipate_gate(void)
{
    if (!gate_can_play()) {
        open_gate();
        return;
    }
    play_gate_burst(GATE_X, GATE_Y, TRUE);
}

/* The same burst, centered on a square, without opening a door.
   The map underneath is put back when the frames end. */
void
wayside_entrance_burst(coordxy x, coordxy y)
{
    if (!isok(x, y) || !gate_can_play())
        return;
    play_gate_burst(x, y, FALSE);
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
aim_one(coordxy x, coordxy y, boolean up, d_level *dest)
{
    stairway *st;

    if (!isok(x, y))
        return;
    st = stairway_at(x, y);
    if (!st)
        put_stair(x, y, up, dest);
    else {
        st->up = up;
        st->isladder = FALSE;
        assign_level(&st->tolev, dest);
        levl[x][y].typ = STAIRS;
        levl[x][y].ladder = up ? LA_UP : LA_DOWN;
    }
}

static void
fix_stairs(void)
{
    stairway *st, *nxt;
    d_level back, onward;
    coordxy ux = WX(72), uy = 3, dx = WX(5), dy = 18;

    /* Up leaves the trial for the level above the host.
       Down returns to the host itself. */
    if (!trial_link("wayside", &back, &onward)) {
        back = valley_level;
        onward = valley_level;
    }
    for (st = gs.stairs; st; st = nxt) {
        nxt = st->next;
        if (!((st->sx == ux && st->sy == uy)
              || (st->sx == dx && st->sy == dy)))
            forget_stair(st);
    }
    aim_one(ux, uy, TRUE, &onward);
    aim_one(dx, dy, FALSE, &back);
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
remaining_tail(int left, char *buf)
{
    if (left == 1)
        Strcpy(buf, "(1 riddle remains.)");
    else
        Sprintf(buf, "(%d riddles remain.)", left);
}

static int
riddles_left(void)
{
    int i, left = 0;

    for (i = 0; i < 6; i++)
        if (!(ws_bits() & (1UL << i)))
            left++;
    return left;
}

static void
confirm_answer(int which)
{
    char tail[BUFSZ], line[BUFSZ];
    int pick;

    remaining_tail(riddles_left(), tail);
    pick = rn2(3);
    if (pick == 0)
        Sprintf(line,
                "The %s villager's eyes brighten. '%s! Yes, that was it. Thank you, friend.' %s",
                ws_adj[which], ws_answer[which], tail);
    else if (pick == 1)
        Sprintf(line,
                "Understanding dawns on the %s villager's face. '%s. How could I have forgotten?' The burden lifts from this house. %s",
                ws_adj[which], ws_answer[which], tail);
    else
        Sprintf(line,
                "'%s,' the %s villager repeats softly. 'I hear it now, and I understand.' %s",
                ws_answer[which], ws_adj[which], tail);
    wayside_screen(line);
    /* The count is in the screen above, including
       "(0 riddles remain.)" for the last answer. The blackout follows. */
    if (riddles_left() == 0)
        wayside_screen(
            "Thou hast heard, and thou hast understood.\n"
            "\n"
            "A great stillness falleth upon the Wayside, and from the northeast thou hearest a gate swing wide upon its hinges.\n"
            "\n"
            "Go forth, for the road to salvation continueth before thee.");
}

boolean
wayside_sanctum_key_dropped(void)
{
    return (boolean) ((ws_bits() & WS_SKEY) != 0);
}

void
wayside_mark_sanctum_key(void)
{
    ws_set(ws_bits() | WS_SKEY);
}

static void
halve_current_hp(void)
{
    int *hp = Upolyd ? &u.mh : &u.uhp;

    *hp /= 2;
    if (*hp < 1)
        *hp = 1;
    disp.botl = TRUE;
}

static void
folly_death(int which)
{
    char text[BUFSZ];

    Sprintf(text,
            "Thou hast heard, yet thou hast not understood.\n"
            "\n"
            "The answer was %s.\n"
            "\n"
            "The way of a fool is right in his own eyes.",
            ws_answer[which]);
    wayside_screen(text);
    /* The hero's own foolishness, not a blow from God. */
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, "Undone by folly at the Wayside.");
    done(DIED);
}

/* Wrong riddle answers only. A villager attack does not call this. */
static void
note_wrong_answer(int which)
{
    int n;

    u.uwayside.wrongs++;
    n = (int) u.uwayside.wrongs;
    /* PLACEHOLDER: no locked line for a wrong answer. */
    pline("That is not the answer.");
    if (n >= 6) {
        folly_death(which);
        return;
    }
    if (n == 4)
        wayside_screen("Thy folly multiplieth, and thy footing groweth unsure. The fool walketh in darkness; twice more mayest thou err, and then thy foolishness shall be thine undoing.");
    if (n == 5) {
        halve_current_hp();
        wayside_screen("Thy strength faileth thee, for thine own folly hath wounded thee. Pride goeth before destruction. One error more, and thou shalt fall by thine own hand.");
    }
    start_punishment();
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
       
        verbalize("You already have that answer.");
        return;
    }
    wayside_screen(ws_body[which]);
    getlin("What am I?", buf);
    if (blank_answer(buf))
        return;
    if (answer_ok(which, buf)) {
        ws_set(ws_bits() | (1UL << which));
        confirm_answer(which);
        if (trial_done())
            dissipate_gate();
    } else {
        note_wrong_answer(which);
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

boolean
wayside_take_up(void)
{
    int i;
    s_level *slev;
    d_level dest;

    /* Inside the Wayside, the exit stays shut until the riddles are done. */
    if (on_wayside() && !trial_done()) {
        pline("The way on is shut.");
        return TRUE;
    }
    /* Before the Road is open, every up stair is ordinary. */
    if (!wayside_road())
        return FALSE;
    i = hosting(&u.uz);
    /* A finished trial, or a level that hosts none, climbs normally. */
    if (i < 0 || trial_list[i].done())
        return FALSE;
    /* Unfinished host. doup() is the only climb, so every up stair
       and ladder on this level stops here. The cap and the soul. */
    if (!sanctum_ascent_open()) {
        sanctum_ascent_refused();
        return TRUE;
    }
    slev = find_level(trial_list[i].proto);
    if (!slev)
        return FALSE;
    dest = slev->dlevel;
    goto_level(&dest, TRUE, FALSE, FALSE);
    return TRUE;
}

boolean
wayside_take_down(void)
{
    /* The way down through Gehennom never enters a trial. */
    return FALSE;
}

boolean
wayside_blocks_levelport(void)
{
    int left;

    if (!wayside_road())
        return FALSE;
    left = trials_left();
    if (left <= 0)
        return FALSE;
    if (left == 1)
        pline("The Road to Salvation is unfinished, so level teleport is sealed. 1 trial remains.");
    else
        pline("The Road to Salvation is unfinished, so level teleport is sealed. %d trials remain.",
              left);
    return TRUE;
}
