/* RighteousHack: the Good Ground, the last Road trial.
   State lives on the hero (u.ugood) and is saved with struct you.
   EDITLEVEL 20. Nothing here is written into bones. */

#include "hack.h"

/* Map column 0 is level x = 1. Rows are unchanged. */
#define GX(c) ((coordxy) ((c) + 1))

#define GG_INTRO 0x00000001UL
#define GG_GATE  0x00000002UL
#define GG_GAME  0x00000004UL
#define GG_GUESS 0x00000008UL
#define GG_DONE  0x00000010UL
#define GG_FIG   5 /* bits 5..15, one per fig square */

static const coord sheep_at[13] = {
    { 1, 1 }, { 15, 1 }, { 73, 1 }, { 59, 6 }, { 1, 19 }, { 73, 19 },
    { 19, 12 }, { 55, 10 }, { 37, 1 }, { 11, 19 }, { 25, 5 },
    { 49, 15 }, { 37, 8 }
};

static const coord fig_at[11] = {
    { 36, 9 }, { 37, 9 }, { 38, 9 },
    { 35, 10 }, { 36, 10 }, { 37, 10 }, { 38, 10 }, { 39, 10 },
    { 36, 11 }, { 37, 11 }, { 38, 11 }
};

static const char intro_text[] =
    "The darkness of the pit is behind thee. Thou standest in a wide green field beneath a gentle sky, and the air is sweet with grass and blossom.\n"
    "\n"
    "Furrows of rich dark earth stretch before thee, heavy with grain. Sheep graze quietly upon the hillsides, and somewhere a bell tinkleth on a lamb's neck.\n"
    "\n"
    "At the heart of the land standeth a walled garden, and above its wall riseth the crown of a great fig tree, green and laden with fruit. Before the gate a shepherd waiteth, leaning upon his staff, and within the garden another keepeth watch over the flock.\n"
    "\n"
    "This is the good ground, where the seed bringeth forth fruit, some an hundredfold, some sixtyfold, some thirtyfold. Rest here, pilgrim. Thy labor hath not been in vain.";

static const char done_text[] =
    "The last trial is behind thee. The seed that was sown in thee hath fallen upon good ground, and it hath borne fruit.\n"
    "\n"
    "The Road to Salvation is finished. Thou hast heard the Word, and endured, and refused the riches of the world, and now thou bearest fruit with patience.\n"
    "\n"
    "Yet thy journey is not ended. Keep thy soul close and the Cap of Salvation upon thy head, and climb ever upward. When thou passest out of the very top of the dungeon, the heavens shall open before thee, and thou shalt pass through the four Planes unto the Throne of the Most High.";

static const char lamb_text[] =
    "Thou hast shed innocent blood upon the good ground!\n"
    "\n"
    "The field falleth silent. The shepherds bow their heads, and the earth crieth out against thee.\n"
    "\n"
    "The way of salvation is closed to the hand that slayeth the lamb.";

static const char leave_ready[] =
    "Thou climbest the last stair, and the dungeon falleth away beneath thee.\n"
    "\n"
    "Upon thy head the Cap of Salvation shineth like the morning, and within thy hands thy soul burneth bright and clean, redeemed from the pit. The hordes of darkness gather at the edge of the world, yet they cannot draw near, for thou art covered.\n"
    "\n"
    "The heavens open before thee. Beyond lie the four Planes, earth and air, fire and water, and beyond them all the Throne of the Most High. There thou shalt lay thy soul upon the altar, and give it back unto Him who made it.\n"
    "\n"
    "Be strong and of a good courage. (Joshua 1:9) The end of thy journey is at hand.";

static const char leave_unfinished[] =
    "Thou climbest out into the open air, and for a moment the light is upon thy face.\n"
    "\n"
    "Then the sky darkeneth. From every side the hordes of darkness come forth, a numberless host, and they descend upon thy soul.\n"
    "\n"
    "Thou hast fled the dungeon, but thou hast not been saved. There is no escape apart from the Road.";

static const char leave_strayed[] =
    "Thou climbest out into the open air, and thou rememberest the Road thou didst once walk.\n"
    "\n"
    "Thou wast upon the path of salvation, yet thou didst turn aside from it. The hordes of darkness have waited for this hour, and now they rise up and descend upon thee.\n"
    "\n"
    "No man, having put his hand to the plough, and looking back, is fit for the kingdom of God. (Luke 9:62)";

static boolean lamb_dying = FALSE;

static boolean
goodground_level(d_level *lev)
{
    s_level *slev = find_level("goodground");

    return (boolean) (lev && slev && on_level(lev, &slev->dlevel));
}

boolean
goodground_here(void)
{
    return goodground_level(&u.uz);
}

boolean
goodground_trial_done(void)
{
    return (boolean) ((u.ugood.bits & GG_DONE) != 0);
}

boolean
goodground_fatal(void)
{
    return lamb_dying;
}

static boolean
gate_open(void)
{
    return (boolean) ((u.ugood.bits & GG_GATE) != 0);
}

static boolean
in_garden(coordxy x, coordxy y)
{
    return (boolean) (x >= GX(25) && x <= GX(49) && y >= 5 && y <= 15);
}

static boolean
is_gate(coordxy x, coordxy y)
{
    return (boolean) (x == GX(37) && y == 16);
}

boolean
goodground_gate_closed(coordxy x, coordxy y)
{
    return (boolean) (goodground_here() && !gate_open() && is_gate(x, y));
}

boolean
goodground_gate_blocks(coordxy x, coordxy y)
{
    if (!goodground_gate_closed(x, y))
        return FALSE;
    pline("The gate is shut.");
    return TRUE;
}

/* Closed garden: no walking in from outside. Already inside is free. */
boolean
goodground_bars_from(coordxy fx, coordxy fy, coordxy x, coordxy y)
{
    if (!goodground_here() || gate_open())
        return FALSE;
    if (is_gate(x, y))
        return TRUE;
    if (!in_garden(x, y))
        return FALSE;
    if (in_garden(fx, fy))
        return FALSE;
    return TRUE;
}

/* A teleport or a phase may not land in the closed garden. */
boolean
goodground_no_landing(coordxy x, coordxy y)
{
    return (boolean) (goodground_here() && !gate_open()
                      && (in_garden(x, y) || is_gate(x, y)));
}

int
goodground_fig(coordxy x, coordxy y)
{
    int i;

    if (!goodground_here())
        return -1;
    for (i = 0; i < 11; i++)
        if (x == GX(fig_at[i].x) && y == fig_at[i].y)
            return i;
    return -1;
}

static void
grant_hp(int n)
{
    u.uhpmax += n;
    u.uhp += n;
    if (u.uhp > u.uhpmax)
        u.uhp = u.uhpmax;
    if (u.uhpmax > u.uhppeak)
        u.uhppeak = u.uhpmax;
    if (Upolyd) {
        u.mhmax += n;
        u.mh += n;
        if (u.mh > u.mhmax)
            u.mh = u.mhmax;
    }
    disp.botl = TRUE;
}

static void
seal_level(void)
{
    coordxy x, y;

    svl.level.flags.rndmongen = 0;
    svl.level.flags.noteleport = 1;
    svl.level.flags.hardfloor = 1;
    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++)
            if (IS_WALL(levl[x][y].typ) || IS_TREE(levl[x][y].typ))
                levl[x][y].wall_info |= (W_NONDIGGABLE | W_NONPASSWALL);
}

static void
open_gate(void)
{
    coordxy x = GX(37), y = 16;

    if (!isok(x, y))
        return;
    if (levl[x][y].typ != DOOR)
        levl[x][y].typ = DOOR;
    if (levl[x][y].doormask & D_ISOPEN)
        return;
    levl[x][y].doormask = D_ISOPEN;
    unblock_point(x, y);
    newsym(x, y);
}

static void
choose_flock(void)
{
    int spot[13], i, j, n;
    unsigned short mask = 0;

    if (u.ugood.sheep)
        return;
    for (i = 0; i < 13; i++)
        spot[i] = i;
    for (i = 12; i > 0; i--) {
        int t;

        j = rn2(i + 1);
        t = spot[i];
        spot[i] = spot[j];
        spot[j] = t;
    }
    n = rn1(6, 5); /* 5..10 */
    for (i = 0; i < n; i++)
        mask |= (unsigned short) (1U << spot[i]);
    u.ugood.sheep = (xint16) n;
    u.ugood.flock = mask;
}

static void
calm_one(struct monst *mtmp)
{
    mtmp->mpeaceful = 1;
    mtmp->mtame = 0;
    mtmp->mflee = 0;
    mtmp->msleeping = 0;
    mtmp->mstrategy |= STRAT_WAITFORU;
    if (mtmp->mhp < mtmp->mhpmax)
        mtmp->mhp = mtmp->mhpmax;
}

static struct monst *
standing_at(struct permonst *pm, coordxy x, coordxy y)
{
    struct monst *mtmp;

    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && mtmp->data == pm
            && mtmp->mx == x && mtmp->my == y)
            return mtmp;
    return (struct monst *) 0;
}

static void
put_back(struct monst *mtmp, coordxy x, coordxy y)
{
    if (!mtmp || (mtmp->mx == x && mtmp->my == y))
        return;
    if (u_at(x, y) || MON_AT(x, y))
        return;
    remove_monster(mtmp->mx, mtmp->my);
    place_monster(mtmp, x, y);
    newsym(mtmp->mx, mtmp->my);
}

static void
plant_flock(void)
{
    struct monst *mtmp, *loose;
    int i;
    coordxy x, y;

    choose_flock();
    for (i = 0; i < 13; i++) {
        if (!(u.ugood.flock & (1U << i)))
            continue;
        x = GX(sheep_at[i].x);
        y = sheep_at[i].y;
        mtmp = standing_at(&mons[PM_SHEEP], x, y);
        if (mtmp) {
            calm_one(mtmp);
            continue;
        }
        loose = (struct monst *) 0;
        for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
            int s;

            if (DEADMONSTER(mtmp) || mtmp->data != &mons[PM_SHEEP])
                continue;
            for (s = 0; s < 13; s++)
                if (mtmp->mx == GX(sheep_at[s].x)
                    && mtmp->my == sheep_at[s].y)
                    break;
            if (s >= 13) {
                loose = mtmp;
                break;
            }
        }
        if (loose) {
            put_back(loose, x, y);
            calm_one(loose);
            continue;
        }
        if (u_at(x, y) || MON_AT(x, y))
            continue;
        mtmp = makemon(&mons[PM_SHEEP], x, y, MM_NOWAIT);
        if (mtmp)
            calm_one(mtmp);
    }
    for (i = 0; i < 2; i++) {
        x = GX(i ? 39 : 37);
        y = i ? 12 : 17;
        mtmp = standing_at(&mons[PM_SHEPHERD], x, y);
        if (mtmp) {
            calm_one(mtmp);
            continue;
        }
        loose = (struct monst *) 0;
        for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
            if (DEADMONSTER(mtmp) || mtmp->data != &mons[PM_SHEPHERD])
                continue;
            if ((mtmp->mx == GX(37) && mtmp->my == 17)
                || (mtmp->mx == GX(39) && mtmp->my == 12))
                continue;
            loose = mtmp;
            break;
        }
        if (loose) {
            put_back(loose, x, y);
            calm_one(loose);
            continue;
        }
        if (u_at(x, y) || MON_AT(x, y))
            continue;
        mtmp = makemon(&mons[PM_SHEPHERD], x, y, MM_NOWAIT);
        if (mtmp)
            calm_one(mtmp);
    }
}

static void
aim_stairs(void)
{
    d_level back, onward;
    stairway *st;

    if (!trial_link("goodground", &back, &onward)) {
        back = valley_level;
        onward = valley_level;
    }
    /* Down at the foot, up at the exit. */
    for (st = gs.stairs; st; st = st->next) {
        if (st->sx == GX(4) && st->sy == 10) {
            st->up = FALSE;
            assign_level(&st->tolev, &back);
        } else if (st->sx == GX(37) && st->sy == 6) {
            st->up = TRUE;
            assign_level(&st->tolev, &onward);
        }
    }
}

void
goodground_setup(void)
{
    if (!goodground_here())
        return;
    seal_level();
    aim_stairs();
    plant_flock();
    if (gate_open())
        open_gate();
}

void
goodground_tick(void)
{
    if (!goodground_here())
        return;
    if (!(u.ugood.bits & GG_INTRO)) {
        wayside_screen(intro_text);
        u.ugood.bits |= GG_INTRO;
    }
    seal_level();
    plant_flock();
    if (gate_open())
        open_gate();
}

void
goodground_note_ascent(void)
{
    if (!goodground_here() || (u.ugood.bits & GG_DONE))
        return;
    wayside_screen(done_text);
    u.ugood.bits |= GG_DONE;
}

void
goodground_sheep_died(struct monst *mtmp)
{
    if (lamb_dying || svc.context.mon_moving)
        return;
    if (!mtmp || mtmp->data != &mons[PM_SHEEP] || !goodground_here())
        return;
    lamb_dying = TRUE;
    wayside_screen(lamb_text);
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, "slew a lamb of the good ground");
    done(DIED);
    lamb_dying = FALSE;
}

int
goodground_eat_fig(void)
{
    int fig = goodground_fig(u.ux, u.uy);

    if (fig < 0)
        return -1;
    if (u.ugood.bits & (1UL << (GG_FIG + fig))) {
        pline("The figs here have all been gathered.");
        return -1;
    }
    if (y_n("There is a fig here. Eat it?") != 'y')
        return -1;
    pline("Thou eatest a ripe fig. It is sweet, and thou feelest renewed.");
    grant_hp(1);
    u.ugood.bits |= (1UL << (GG_FIG + fig));
    return ECMD_TIME;
}

static void
number_list(char *buf, int first, int count)
{
    int i;

    buf[0] = '\0';
    for (i = 0; i < count; i++) {
        if (i)
            Strcat(buf, ", ");
        Sprintf(eos(buf), "%d", first + i);
    }
}

static void
play_twenty_one(void)
{
    int cur = 0;
    char list[80];

    pline("We shall count by turns unto one and twenty. In thy turn thou mayest say one, two, or three numbers. Whosoever must say twenty and one loseth. I shall begin.");
    while (cur < 21) {
        int legal = 21 - cur;
        int n, ch;
        char choices[5];
        int i;

        if (legal > 3)
            legal = 3;
        n = rnd(legal);
        number_list(list, cur + 1, n);
        pline("The shepherd saith %s.", list);
        cur += n;
        if (cur >= 21) {
            pline("The shepherd laugheth, for twenty and one falleth to him. 'Well counted! Thy patience hath borne fruit.' Thou feelest much stronger!");
            grant_hp(20);
            break;
        }
        legal = 21 - cur;
        if (legal > 3)
            legal = 3;
        choices[0] = '\0';
        for (i = 1; i <= legal; i++) {
            choices[i - 1] = (char) ('0' + i);
            choices[i] = '\0';
        }
        ch = 0;
        while (ch < '1' || ch >= '1' + legal) {
            ch = yn_function("How many numbers wilt thou say?",
                             choices, '1', TRUE);
            if (ch == '\033')
                ch = 0;
        }
        n = ch - '0';
        number_list(list, cur + 1, n);
        pline("Thou sayest %s.", list);
        cur += n;
        if (cur >= 21) {
            pline("'Twenty and one is thine to say. Fear not, friend, no gate was ever barred for a game.' The shepherd unlocketh the gate.");
            break;
        }
    }
    u.ugood.bits |= (GG_GAME | GG_GATE);
    open_gate();
}

static int
which_shepherd(struct monst *mtmp)
{
    if (!mtmp || mtmp->data != &mons[PM_SHEPHERD])
        return -1;
    if (mtmp->mx == GX(37) && mtmp->my == 17)
        return 0;
    if (mtmp->mx == GX(39) && mtmp->my == 12)
        return 1;
    return -1;
}

static void
count_sheep(void)
{
    char buf[BUFSZ];
    int num = 0;

    getlin("How many sheep are in the flock?", buf);
    if (buf[0] == '\033' || buf[0] == '\0') {
        /* The question was accepted. A blank answer spends the guess. */
        pline("'Nay, that is not the number. Yet be at peace, for the flock is safe.'");
        u.ugood.bits |= GG_GUESS;
        return;
    }
    if (sscanf(buf, "%d", &num) != 1 || num != (int) u.ugood.sheep)
        pline("'Nay, that is not the number. Yet be at peace, for the flock is safe.'");
    else {
        pline("'Thou hast numbered them truly, and not one is lost.' Thou feelest much stronger!");
        grant_hp(20);
    }
    u.ugood.bits |= GG_GUESS;
}

boolean
goodground_chat(struct monst *mtmp)
{
    int who;

    who = which_shepherd(mtmp);
    if (who < 0)
        return FALSE;
    calm_one(mtmp);
    if (who == 0) {
        if (u.ugood.bits & GG_GAME) {
            pline("The gate standeth open. Go in peace.");
            return TRUE;
        }
        if (y_n("Peace be unto thee, pilgrim. The hard roads are behind thee now. Beyond this gate groweth the fig tree of the good ground. Wilt thou sit with me a while and play at counting?") != 'y')
            return TRUE;
        play_twenty_one();
        return TRUE;
    }
    if (u.ugood.bits & GG_GUESS) {
        pline("Go in peace, faithful one.");
        return TRUE;
    }
    if (y_n("Welcome to the good ground, where the seed bringeth forth an hundredfold. I keep the flock upon this land. Canst thou tell me how many of my sheep graze here? Count well, both near and far, for some are hidden. Wilt thou answer?") != 'y')
        return TRUE;
    count_sheep();
    return TRUE;
}

boolean
salvation_ready(void)
{
    return (boolean) (cap_of_salvation_worn() && carried_player_soul()
                      && goodground_trial_done());
}

boolean
salvation_climb(stairway *stway)
{
    d_level dest;

    if (salvation_ready()) {
        wayside_screen(leave_ready);
        if (!stway)
            return TRUE;
        dest = stway->tolev;
        goto_level(&dest, TRUE, FALSE, FALSE);
        return TRUE;
    }
    if (y_n("Beyond lieth the open world, and thou art not ready. Wilt thou truly leave the dungeon?") != 'y')
        return TRUE;
    if (goodground_trial_done()) {
        wayside_screen(leave_strayed);
        svk.killer.format = NO_KILLER_PREFIX;
        Strcpy(svk.killer.name, "strayed from the straight and narrow path");
    } else {
        wayside_screen(leave_unfinished);
        svk.killer.format = NO_KILLER_PREFIX;
        Strcpy(svk.killer.name, "devoured by the hordes of darkness");
    }
    done(DIED);
    return TRUE;
}
