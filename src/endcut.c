/* RighteousHack: Plane of Heaven endings.
   Full-screen frames live in endframes.c. The altar light and the
   destruction of Lucifer are drawn on the level that is actually in
   memory, at the real coordinates of the altar and of each monster.

   Prophet mode #proanimate 1, 2, and 4 borrow the current level:
     1. The whole level is written to a scratch file and freed from
        memory (savelev with WRITING|FREEING). The scratch file is not
        a save-file level, and level_info is not given a new heaven.
     2. astral.lua is loaded in its place, then Lucifer and the Son of
        Perdition are placed the same way a new Plane of Heaven is.
     3. The cutscene runs. Monsters removed here exist only on that
        temporary map.
     4. The temporary map is freed (savelev with FREEING only, so
        nothing is written). The scratch file is read back with getlev
        and then unlinked. The hero's coordinates, steed, ball, and
        the saved random-number state, monster tallies, and discovery
        flags are put back. Nothing is left in the save.
        The scratch file is named through fqname() in the level
        directory (LEVELPREFIX), not a hard-coded /tmp path.
 */

#include "hack.h"
#include <fcntl.h>
#include <time.h>
#if !defined(MICRO) && !defined(WIN32)
#include <sys/select.h>
#endif
#ifdef WIN32
#include <io.h>
#endif
#ifndef O_BINARY
#define O_BINARY 0
#endif
#ifdef TTY_GRAPHICS
#include "wintty.h"
#endif

boolean endcut_testing = FALSE;
/* While the battle is on screen, vision must not shrink the map
   back to the hero's sight. The Plane of Heaven does not remember
   the map, and the hero's sight is short. */
boolean endcut_omniscient = FALSE;

static boolean endcut_stone = FALSE;
static boolean endcut_from_dragon = FALSE;
static unsigned endcut_steed_id, endcut_stuck_id, endcut_ball_id,
    endcut_chain_id;
static char endcut_scratch[FQN_MAX_FILENAME];

static void endcut_give_back(coordxy, coordxy);
static void endcut_show(void);
static boolean endcut_borrow(coordxy *, coordxy *);
void endcut_memorial(winid, time_t);

#define ENDCUT_WIN 0
#define ENDCUT_DRAGON 1
#define ENDCUT_DEATH 2

/* Locked verbatim. */
static const char win_a_lead[] =
    "Thou offerest thy soul up to the Lord... a heart submitted to the will of God Most High...";
static const char win_a_rest[] =
    "For a moment there is silence in heaven. Then the voice of a trumpet soundeth, exceeding loud, and all of heaven trembleth at the sound thereof. And the altar is filled with the glory of the Lord, and a sound goeth forth from the throne as of a mighty thunder, and the whole field of heaven is shaken. A great and terrible light breaketh out from the presence of the Lord, as a fire that consumeth, and it goeth forth over all the host of the Great Dragon. The fallen angels are smitten where they stand; their weapons fall from their hands, and they are made still as stone, and cannot flee. And slowly, before thine eyes, they are turned to dust, and the wind of the Lord carrieth them away, and their place is found no more.";
static const char win_c_text[] =
    "Lucifer, that old serpent, called the Devil and Satan, which deceiveth the whole world, lifteth up his voice in rage, but it availeth him nothing. The brightness of the Lord's coming falleth upon him, and he is cast down, bound in chains of darkness, and the war in heaven is ended.";
static const char win_e_text[] =
    "The chains that bound thee in the Sanctum of the Great Dragon break asunder, and fall as dust about thy feet.\n"
    "\n"
    "Thou didst walk the Narrow Way when the broad road called thee. Thou didst hear the Word in the Wayside amid the voices of deceit. Thou didst bear the thorns, and set thy face toward Zion, and kept the faith when thy strength was gone. Thou hast run with patience the race that was set before thee. Thou hast fought a good fight, thou hast finished thy course, thou hast kept the faith. Henceforth there is laid up for thee a crown of righteousness.\n"
    "\n"
    "And a voice, as the sound of many waters, saith unto thee:\n"
    "\n"
    "Well done, thou good and faithful servant. Thou hast been faithful over a few things; I will make thee ruler over many things. Enter thou into the joy of thy Lord.\n"
    "\n"
    "Strong hands lift thee up. Thy wounds are healed, and every tear is wiped from thine eyes. There is no more death, neither sorrow, nor crying, neither any more pain, for the former things are passed away.\n"
    "\n"
    "Thy soul is thine again. Thou art redeemed, and thou art home.";
static const char dragon_voice[] =
    "A voice from heaven booms: \"Woe unto thee, for thou hast made the gravest of errors.\"";
static const char dragon_text[] =
    "\"Thou foolishly layest thy soul upon the altar of the Great Dragon. The stone of the altar groweth cold beneath thy hand, and the light of heaven beginneth to dim. Lucifer, that old serpent, called the Devil and Satan, the deceiver which deceiveth the whole world, laugheth, and thou feelest the chains from the floor rising up to close upon thy soul once more. Thou art pulled down into outer darkness, where there is weeping and gnashing of teeth.\"";
static const char heaven_death_text[] =
    "Thou fallest upon the field of heaven, and the war goeth on without thee. The Great Dragon setteth his foot upon thy soul and beareth it away. Thy race is ended, though the crown was within thy reach.";

static const char win_reason[] = "went up by a whirlwind into heaven";
static const char dragon_reason[] =
    "offered thy soul upon the altar of evil";
static const char heaven_death_reason[] = "fell upon the field of heaven";

extern void endcut_frame_at(int, int *, int *, int *, int *);
extern int endcut_run_at(int, int *, int *, int *, int *);
extern int endcut_nframes(void);

static boolean
endcut_tty(void)
{
#ifdef TTY_GRAPHICS
    return (boolean) (windowprocs.wp_id == wp_tty && tty_endcut_ok());
#else
    return FALSE;
#endif
}

/* True if a key is already waiting. Does not block. */
static boolean
endcut_key_ready(void)
{
#if defined(MICRO) || defined(WIN32)
    return (boolean) kbhit();
#else
    fd_set fds;
    struct timeval tv;

    FD_ZERO(&fds);
    FD_SET(0, &fds);
    tv.tv_sec = 0;
    tv.tv_usec = 0;
    return (boolean) (select(1, &fds, (fd_set *) 0, (fd_set *) 0, &tv) > 0);
#endif
}

/* nh_delay_output is the window port's own pause (about 50 ms on tty).
   The Windows console implements that with Sleep, which this file
   does not call by name. */
static boolean
endcut_wait(int ms)
{
    int ticks;

    if (ms < 1)
        ms = 1;
    ticks = (ms + 49) / 50;
    if (ticks < 1)
        ticks = 1;
    while (ticks-- > 0) {
        if (endcut_key_ready()) {
            (void) nhgetch();
            return TRUE;
        }
        nh_delay_output();
    }
    return FALSE;
}

/* One less than the tty width, and never past the putstr buffer.
   Anywhere else, 79. */
int
rh_text_cols(void)
{
    int cols = 79;

#ifdef TTY_GRAPHICS
    if (windowprocs.wp_id == wp_tty && CO > 1)
        cols = CO - 1;
#endif
    if (cols < 20)
        cols = 79;
    if (cols > BUFSZ - 1)
        cols = BUFSZ - 1;
    return cols;
}

/* Fold one paragraph on a space. A word longer than the screen
   stays whole. */
static void
rh_put_para(winid win, int attr, const char *line, size_t len, int cols)
{
    if (!len) {
        putstr(win, attr, "");
        return;
    }
    while (len > 0) {
        int n = (int) len;
        char buf[BUFSZ];

        if (n > cols) {
            n = cols;
            while (n > 0 && line[n] != ' ')
                n--;
            if (n <= 0) {
                n = 0;
                while ((size_t) n < len && line[n] && line[n] != ' ')
                    n++;
                if (!n)
                    return;
            }
        }
        if (n >= BUFSZ)
            n = BUFSZ - 1;
        (void) strncpy(buf, line, (size_t) n);
        buf[n] = '\0';
        putstr(win, attr, buf);
        line += n;
        len -= (size_t) n;
        if (len && *line == ' ') {
            line++;
            len--;
        }
    }
}

/* Newlines stay paragraph breaks. Each paragraph is folded. */
void
rh_putstr(winid win, int attr, const char *text)
{
    const char *p = text ? text : "";
    int cols = rh_text_cols();

    while (*p) {
        const char *nl = strchr(p, '\n');
        size_t len = nl ? (size_t) (nl - p) : strlen(p);

        rh_put_para(win, attr, p, len, cols);
        if (!nl)
            break;
        p = nl + 1;
    }
}

/* Full-screen text. display_nhwindow pages with --More--. */
void
rh_text_window(const char *text)
{
    winid win = create_nhwindow(NHW_TEXT);

    rh_putstr(win, 0, text ? text : "");
    display_nhwindow(win, TRUE);
    destroy_nhwindow(win);
}

void
endcut_card(const char *text)
{
    rh_text_window(text);
}

static void
endcut_play(int seq)
{
#ifdef TTY_GRAPHICS
    int i, n, total;

    if (!endcut_tty())
        return;
    total = endcut_nframes();
    tty_endcut_begin();
    for (i = 0; i < total; i++) {
        int ms, which, start, nruns, r;
        int pos;
        uchar ch[24][80], col[24][80], inv[24][80];

        endcut_frame_at(i, &ms, &which, &start, &nruns);
        if (which != seq)
            continue;
        memset(ch, ' ', sizeof ch);
        memset(col, 0, sizeof col);
        memset(inv, 0, sizeof inv);
        pos = 0;
        for (r = 0; r < nruns; r++) {
            int rn, rch, rcol, rinv, k;

            if (!endcut_run_at(start + r, &rn, &rch, &rcol, &rinv))
                break;
            for (k = 0; k < rn && pos < 24 * 80; k++, pos++) {
                ch[pos / 80][pos % 80] = (uchar) rch;
                col[pos / 80][pos % 80] = (uchar) rcol;
                inv[pos / 80][pos % 80] = (uchar) rinv;
            }
        }
        for (n = 0; n < 24 * 80; n++)
            tty_endcut_cell(n % 80, n / 80, ch[n / 80][n % 80],
                            col[n / 80][n % 80], inv[n / 80][n % 80]);
        tty_endcut_flush();
        if (endcut_wait(ms))
            break;
    }
    tty_endcut_end();
    docrt();
#else
    (void) seq;
#endif
}

static void
endcut_spark(coordxy x, coordxy y, int dx, int dy, int kind)
{
#ifdef TTY_GRAPHICS
    static const char glyph[] = { '*', '*', '/', '\\', '\'', ',' };
    int color;

    if (!endcut_tty() || !isok(x, y))
        return;
    color = (kind & 1) ? CLR_WHITE : CLR_YELLOW;
    if (kind & 2)
        color = CLR_BROWN;
    tty_endcut_mapcell(x, y, glyph[(dx + dy + kind) & 5], color, 0);
#else
    (void) x; (void) y; (void) dx; (void) dy; (void) kind;
#endif
}

static void
endcut_ring(coordxy x, coordxy y, int radius)
{
    int dx, dy;

    for (dy = -radius; dy <= radius; dy++)
        for (dx = -radius; dx <= radius; dx++) {
            if (distmin(x, y, x + dx, y + dy) != radius)
                continue;
            if (!isok(x + dx, y + dy))
                continue;
            endcut_spark(x + dx, y + dy, dx, dy, radius);
        }
#ifdef TTY_GRAPHICS
    if (endcut_tty())
        tty_endcut_flush();
#endif
}

static boolean
endcut_burst(coordxy x, coordxy y, int rings)
{
    int r;

    for (r = 1; r <= rings; r++) {
        endcut_ring(x, y, r);
        if (endcut_wait(80))
            return TRUE;
        endcut_show();
    }
    return FALSE;
}

static long endcut_save_det;
static boolean endcut_det_saved = FALSE;

static void
endcut_show(void)
{
    gv.vision_full_recalc = 1;
    docrt();
    flush_screen(1);
}

static void
endcut_sight_off(void)
{
    endcut_omniscient = FALSE;
    if (!endcut_det_saved)
        return;
    EDetect_monsters = endcut_save_det;
    endcut_det_saved = FALSE;
}

/* Light and map the whole level, then show every monster, so the
   battlefield is on screen under the sparks. Detection is put back
   by endcut_sight_off before a saved level is read again. */
static void
endcut_reveal(void)
{
    coordxy x, y;
    struct monst *mtmp;

    endcut_omniscient = TRUE;
    if (!endcut_det_saved) {
        endcut_save_det = EDetect_monsters;
        endcut_det_saved = TRUE;
    }
    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            struct obj *obj;

            levl[x][y].lit = 1;
            levl[x][y].waslit = 1;
            levl[x][y].seenv = SVALL;
            obj = vobj_at(x, y);
            if (obj && !covers_objects(x, y))
                map_object(obj, 0);
            else
                magic_map_background(x, y, 1);
        }
    EDetect_monsters |= I_SPECIAL;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp))
            continue;
        mtmp->mundetected = 0;
        newsym(mtmp->mx, mtmp->my);
    }
    /* The text card cleared the screen. Draw the whole battlefield
       and push it out before any spark is painted. */
    endcut_show();
}

static boolean
endcut_find_altar(coordxy *ax, coordxy *ay)
{
    coordxy x, y;

    for (x = 1; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            if (levl[x][y].typ != ALTAR)
                continue;
            if (!(levl[x][y].altarmask & AM_SANCTUM))
                continue;
            if (Amask2align(levl[x][y].altarmask & AM_MASK) != A_LAWFUL)
                continue;
            *ax = x;
            *ay = y;
            return TRUE;
        }
    *ax = u.ux;
    *ay = u.uy;
    return FALSE;
}

static void
endcut_quake(coordxy ax, coordxy ay)
{
    int step, dx, dy;
    static const int shiftx[] = { 1, -1, 2, -2, 1, 0, -1, 0 };
    static const int shifty[] = { 0, 1, -1, 1, -1, 1, 0, -1 };

    for (step = 0; step < 8; step++) {
        int radius = 2 + step;

        endcut_show();
        for (dy = -radius; dy <= radius; dy++)
            for (dx = -radius; dx <= radius; dx++) {
                coordxy x = ax + dx + shiftx[step];
                coordxy y = ay + dy + shifty[step];

                if (((dx + dy + step) & 3) != 0)
                    continue;
                if (!isok(x, y))
                    continue;
                if (distmin(ax, ay, ax + dx, ay + dy) > radius)
                    continue;
                endcut_spark(x, y, dx, dy, step);
            }
#ifdef TTY_GRAPHICS
        if (endcut_tty())
            tty_endcut_flush();
#endif
        if (endcut_wait(70))
            break;
    }
    endcut_show();
}

static int
endcut_dist(struct monst *mtmp, coordxy ax, coordxy ay)
{
    int dx = mtmp->mx - ax, dy = mtmp->my - ay;

    return dx * dx + dy * dy;
}

static void
endcut_smite(coordxy ax, coordxy ay, boolean harm)
{
    struct monst *mtmp, *list[256];
    int n, i, j;

    n = 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        if (DEADMONSTER(mtmp) || is_lucifer(mtmp))
            continue;
        /* The Lord's host stays. Dragon priests and fallen angels
           are hostile, so the light takes them with the rest. */
        if (mtmp->mpeaceful || mtmp->mtame || heaven_lords_host(mtmp))
            continue;
        if (n < (int) SIZE(list))
            list[n++] = mtmp;
    }
    for (i = 1; i < n; i++) {
        struct monst *key = list[i];
        int keyd = endcut_dist(key, ax, ay);

        j = i;
        while (j > 0 && endcut_dist(list[j - 1], ax, ay) > keyd) {
            list[j] = list[j - 1];
            j--;
        }
        list[j] = key;
    }
    for (i = 0; i < n; i++) {
        coordxy x = list[i]->mx, y = list[i]->my;

        if (endcut_burst(x, y, 3))
            break;
        if (harm && !DEADMONSTER(list[i])) {
            mongone(list[i]);
            newsym(x, y);
        }
    }
    endcut_show();
}

static coordxy
endcut_beside(coordxy *y)
{
    static const coordxy dxs[] = { 1, -1, 0, 0, 1, -1, 1, -1 };
    static const coordxy dys[] = { 0, 0, 1, -1, 1, 1, -1, -1 };
    int i;

    for (i = 0; i < (int) SIZE(dxs); i++) {
        coordxy x = u.ux + dxs[i], yy = u.uy + dys[i];

        if (isok(x, yy) && accessible(x, yy)) {
            *y = yy;
            return x;
        }
    }
    *y = u.uy;
    return u.ux;
}

static void
endcut_lucifer_at(coordxy x, coordxy y, boolean harm)
{
    struct monst *mtmp, *found = 0;
    int step;

    endcut_reveal();
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && is_lucifer(mtmp))
            found = mtmp;
    if (found) {
        x = found->mx;
        y = found->my;
        found->m_ap_type = M_AP_NOTHING;
        newsym(x, y);
    }
    for (step = 4; step >= 1; step--) {
        endcut_show();
        endcut_ring(x, y, step);
#ifdef TTY_GRAPHICS
        if (endcut_tty()) {
            tty_endcut_mapcell(x, y, 1, (step & 1) ? CLR_RED : CLR_WHITE, 1);
            tty_endcut_flush();
        }
#endif
        if (endcut_wait(120))
            break;
    }
    endcut_show();
    (void) endcut_burst(x, y, 2);
    if (harm && found && !DEADMONSTER(found)) {
        mongone(found);
        newsym(x, y);
    }
    endcut_show();
}

static void
endcut_altar_scene(boolean harm)
{
    coordxy ax, ay;

    endcut_reveal();
    (void) endcut_find_altar(&ax, &ay);
    endcut_quake(ax, ay);
    if (endcut_burst(ax, ay, 6))
        return;
    endcut_smite(ax, ay, harm);
}

static void
endcut_win_map(boolean harm)
{
    /* A rehearsal must not pull the hero's own waiting Lucifer off
       the migrating list. The temporary map already has its own. */
    if (!endcut_testing)
        heaven_wake_lucifer();
    endcut_altar_scene(harm);
}

static boolean
endcut_stand_near(coordxy ax, coordxy ay)
{
    int dx, dy;

    if (isok(ax, ay) && accessible(ax, ay) && !m_at(ax, ay)) {
        u.ux = ax;
        u.uy = ay;
        return TRUE;
    }
    for (dy = -1; dy <= 1; dy++)
        for (dx = -1; dx <= 1; dx++) {
            coordxy x = ax + dx, y = ay + dy;

            if (isok(x, y) && accessible(x, y) && !m_at(x, y)) {
                u.ux = x;
                u.uy = y;
                return TRUE;
            }
        }
    return FALSE;
}

static NHFILE *
endcut_open_scratch(boolean writing)
{
    NHFILE *nhfp = (NHFILE *) alloc(sizeof *nhfp);
    int fd;

    memset(nhfp, 0, sizeof *nhfp);
    init_nhfile(nhfp);
    if (writing)
        fd = open(endcut_scratch, O_WRONLY | O_CREAT | O_TRUNC | O_BINARY,
                  FCMASK);
    else
        fd = open(endcut_scratch, O_RDONLY | O_BINARY, 0);
    if (fd < 0) {
        free((genericptr_t) nhfp);
        return (NHFILE *) 0;
    }
    nhfp->fd = fd;
    nhfp->mode = writing ? (WRITING | FREEING) : READING;
    nhfp->structlevel = TRUE;
    nhfp->fieldlevel = FALSE;
    nhfp->ftype = NHF_LEVELFILE;
    nhfp->fnidx = historical;
    nhfp->style.binary = TRUE;
    return nhfp;
}

static boolean
endcut_borrow(coordxy *ox, coordxy *oy)
{
    NHFILE *nhfp;
    unsigned steed_id = 0, stuck_id = 0, ball_id = 0, chain_id = 0;
    coordxy ax, ay;
    xint8 lev;

    {
        char base[32];
        const char *fq;

        /* Level directory, same place as the other per-user level files.
           hackpid is the process id recorded at startup on every port. */
        Sprintf(base, "rhend%d", svh.hackpid);
        fq = fqname(base, LEVELPREFIX, 1);
        if (!fq || !*fq)
            fq = base;
        (void) strncpy(endcut_scratch, fq, sizeof endcut_scratch - 1);
        endcut_scratch[sizeof endcut_scratch - 1] = '\0';
    }
    *ox = u.ux;
    *oy = u.uy;
    if (u.usteed)
        steed_id = u.usteed->m_id;
    if (u.ustuck)
        stuck_id = u.ustuck->m_id;
    if (uball)
        ball_id = uball->o_id;
    if (uchain)
        chain_id = uchain->o_id;
    nhfp = endcut_open_scratch(TRUE);
    if (!nhfp)
        return FALSE;
    if (nhfp->structlevel)
        bufon(nhfp->fd);
    lev = (xint8) ledger_no(&u.uz);
    savelev(nhfp, lev);
    close_nhfile(nhfp);
    /* The level's monsters and objects were freed with the write. */
    u.usteed = u.ustuck = 0;
    u.uswallow = 0;
    uball = uchain = 0;

    gi.in_mklev = TRUE;
    (void) lspo_reset_level((lua_State *) 0);
    if (!load_special("astral.lua")) {
        gi.in_mklev = FALSE;
        endcut_steed_id = steed_id;
        endcut_stuck_id = stuck_id;
        endcut_ball_id = ball_id;
        endcut_chain_id = chain_id;
        endcut_give_back(*ox, *oy);
        return FALSE;
    }
    (void) lspo_finalize_level((lua_State *) 0);
    gi.in_mklev = FALSE;
    endcut_steed_id = steed_id;
    endcut_stuck_id = stuck_id;
    endcut_ball_id = ball_id;
    endcut_chain_id = chain_id;
    heaven_ready_host();
    (void) endcut_find_altar(&ax, &ay);
    if (!endcut_stand_near(ax, ay)) {
        u.ux = ax;
        u.uy = ay;
    }
    vision_reset();
    docrt();
    return TRUE;
}

static struct monst *
endcut_mon_by_id(unsigned id)
{
    struct monst *mtmp;

    if (!id)
        return (struct monst *) 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (mtmp->m_id == id)
            return mtmp;
    return (struct monst *) 0;
}

static struct obj *
endcut_obj_by_id(unsigned id)
{
    struct obj *obj;

    if (!id)
        return (struct obj *) 0;
    for (obj = fobj; obj; obj = obj->nobj)
        if (obj->o_id == id)
            return obj;
    for (obj = gi.invent; obj; obj = obj->nobj)
        if (obj->o_id == id)
            return obj;
    return (struct obj *) 0;
}

static void
endcut_give_back(coordxy ox, coordxy oy)
{
    NHFILE *nhfp, *dead;
    xint8 lev = (xint8) ledger_no(&u.uz);

    endcut_sight_off();
    dead = get_freeing_nhfile();
    if (dead) {
        savelev(dead, lev);
        close_nhfile(dead);
    }
    nhfp = endcut_open_scratch(FALSE);
    if (nhfp) {
        getlev(nhfp, svh.hackpid, lev);
        close_nhfile(nhfp);
    }
    (void) unlink(endcut_scratch);
    u.ux = ox;
    u.uy = oy;
    u.usteed = endcut_mon_by_id(endcut_steed_id);
    u.ustuck = endcut_mon_by_id(endcut_stuck_id);
    if (u.ustuck && u.ustuck->mundetected)
        u.uswallow = 0;
    uball = endcut_obj_by_id(endcut_ball_id);
    uchain = endcut_obj_by_id(endcut_chain_id);
    vision_reset();
    docrt();
}

struct endcut_keep {
    struct mvitals vitals[NUMMONS];
    struct u_event event;
    struct u_conduct conduct;
    long exp, moves;
    int blesscnt, wizards;
    schar luck;
    struct monst *migrating;
    uchar *known, *seen;
};

static void
endcut_keep_save(struct endcut_keep *k)
{
    int i;

    memcpy(k->vitals, svm.mvitals, sizeof k->vitals);
    k->event = u.uevent;
    k->conduct = u.uconduct;
    k->exp = u.urexp;
    k->moves = svm.moves;
    k->wizards = svc.context.no_of_wizards;
    k->blesscnt = u.ublesscnt;
    k->luck = u.uluck;
    k->migrating = gm.migrating_mons;
    k->known = (uchar *) alloc(NUM_OBJECTS);
    k->seen = (uchar *) alloc(NUM_OBJECTS);
    for (i = 0; i < NUM_OBJECTS; i++) {
        k->known[i] = (uchar) objects[i].oc_name_known;
        k->seen[i] = (uchar) objects[i].oc_encountered;
    }
}

static void
endcut_keep_restore(struct endcut_keep *k)
{
    int i;

    memcpy(svm.mvitals, k->vitals, sizeof k->vitals);
    u.uevent = k->event;
    u.uconduct = k->conduct;
    u.urexp = k->exp;
    svm.moves = k->moves;
    svc.context.no_of_wizards = k->wizards;
    u.ublesscnt = k->blesscnt;
    u.uluck = k->luck;
    while (gm.migrating_mons && gm.migrating_mons != k->migrating) {
        struct monst *nxt = gm.migrating_mons->nmon;

        dealloc_monst(gm.migrating_mons);
        gm.migrating_mons = nxt;
    }
    gm.migrating_mons = k->migrating;
    for (i = 0; i < NUM_OBJECTS; i++) {
        objects[i].oc_name_known = k->known[i];
        objects[i].oc_encountered = k->seen[i];
    }
    free((genericptr_t) k->known);
    free((genericptr_t) k->seen);
}

static boolean
endcut_rehearse(int which)
{
    struct endcut_keep keep;
    coordxy ox, oy, lx, ly;
    boolean ok;

    rng_save();
    endcut_keep_save(&keep);
    endcut_testing = TRUE;
    ok = endcut_borrow(&ox, &oy);
    if (!ok) {
        endcut_testing = FALSE;
        endcut_keep_restore(&keep);
        rng_restore();
        pline("The temporary heaven could not be opened.");
        return FALSE;
    }
    if (which == 1 || which == 4) {
        endcut_card(win_a_lead);
        endcut_card(win_a_rest);
        endcut_win_map(TRUE);
    }
    if (which == 2 || which == 4) {
        endcut_card(win_c_text);
        lx = u.ux;
        ly = u.uy;
        if (!m_at(u.ux, u.uy))
            lx = endcut_beside(&ly);
        endcut_lucifer_at(lx, ly, TRUE);
    }
    if (which == 4) {
        endcut_card(win_e_text);
        endcut_play(ENDCUT_WIN);
        endcut_memorial(WIN_ERR, 0);
    }
    endcut_give_back(ox, oy);
    endcut_testing = FALSE;
    endcut_keep_restore(&keep);
    rng_restore();
    docrt();
    return TRUE;
}

static const char *const endcut_menu_line[] = {
    "1 Win: altar light and earthquake",
    "2 Win: Lucifer destroyed",
    "3 Win: ascension",
    "4 Win: full sequence",
    "5 Dragon's altar",
    "6 Death on the Plane of Heaven",
    "7 Victory memorial stone"
};

static void
endcut_run_number(int n)
{
    switch (n) {
    case 1:
    case 2:
    case 4:
        (void) endcut_rehearse(n);
        break;
    case 3:
        endcut_card(win_e_text);
        endcut_play(ENDCUT_WIN);
        break;
    case 5:
        endcut_play(ENDCUT_DRAGON);
        endcut_card(dragon_voice);
        endcut_card(dragon_text);
        break;
    case 6:
        endcut_play(ENDCUT_DEATH);
        endcut_card(heaven_death_text);
        break;
    case 7:
        endcut_memorial(WIN_ERR, 0);
        break;
    default:
        pline("The number is from 1 to 7.");
        break;
    }
    docrt();
}

int
do_proanimate(void)
{
    char buf[BUFSZ];
    winid win;
    anything any;
    menu_item *pick;
    int i, n;

    if (!wizard) {
        pline("Prophet mode is required.");
        return ECMD_OK;
    }
    buf[0] = '\0';
    getlin("Cutscene number, or ? for the list:", buf);
    if (buf[0] == '\033')
        return ECMD_OK;
    if (buf[0] == '\0' || buf[0] == '?') {
        win = create_nhwindow(NHW_MENU);
        start_menu(win, MENU_BEHAVE_STANDARD);
        for (i = 0; i < (int) SIZE(endcut_menu_line); i++) {
            any = cg.zeroany;
            any.a_int = i + 1;
            add_menu(win, &nul_glyphinfo, &any, '1' + i, 0, ATR_NONE,
                     NO_COLOR, endcut_menu_line[i], MENU_ITEMFLAGS_NONE);
        }
        end_menu(win, "Which cutscene?");
        n = select_menu(win, PICK_ONE, &pick);
        destroy_nhwindow(win);
        if (n > 0) {
            i = pick[0].item.a_int;
            free((genericptr_t) pick);
            endcut_run_number(i);
        }
        return ECMD_OK;
    }
    endcut_run_number(atoi(buf));
    return ECMD_OK;
}

void
endcut_ascend(void)
{
    char lead[BUFSZ];

    Sprintf(lead, "%s", win_a_lead);
    endcut_card(lead);
    endcut_card(win_a_rest);
    endcut_win_map(TRUE);
    endcut_card(win_c_text);
    endcut_lucifer_at(u.ux, u.uy, TRUE);
    endcut_card(win_e_text);
    endcut_play(ENDCUT_WIN);
    u.uevent.ascended = 1;
    endcut_stone = TRUE;
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, win_reason);
    done(ASCENDED);
}

void
endcut_dragon(void)
{
    endcut_play(ENDCUT_DRAGON);
    endcut_card(dragon_voice);
    endcut_card(dragon_text);
    endcut_from_dragon = TRUE;
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, dragon_reason);
    done(DIED);
}

void
endcut_heaven_death(void)
{
    if (endcut_from_dragon || endcut_testing)
        return;
    if (!Is_astralevel(&u.uz))
        return;
    endcut_play(ENDCUT_DEATH);
    endcut_card(heaven_death_text);
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, heaven_death_reason);
}

boolean
endcut_replace_tomb(void)
{
    return endcut_stone;
}

static void
endcut_center(char *dst, int width, const char *text)
{
    int len = (int) strlen(text);
    int pad;

    if (len > width)
        len = width;
    pad = (width - len) / 2;
    memset(dst, ' ', (size_t) width);
    memcpy(dst + pad, text, (size_t) len);
    dst[width] = '\0';
}

void
endcut_memorial(winid extra, time_t when)
{
    static const char *const months[] = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    };
    char name[40], date[40], clock[20], body[40];
    struct tm *lt;
    time_t now = when ? when : getnow();
    int hour, i;
    const char *rows[8];

    lt = localtime(&now);
    if (!lt)
        lt = localtime(&now);
    (void) strncpy(name, svp.plname, 36);
    name[36] = '\0';
    if (lt) {
        Sprintf(date, "%s %d, %d", months[lt->tm_mon], lt->tm_mday,
                lt->tm_year + 1900);
        hour = lt->tm_hour % 12;
        if (!hour)
            hour = 12;
        Sprintf(clock, "%d:%02d %s", hour, lt->tm_min,
                lt->tm_hour >= 12 ? "PM" : "AM");
    } else {
        Strcpy(date, "a day");
        Strcpy(clock, "an hour");
    }
    rows[0] = name;
    rows[1] = "went up by a";
    rows[2] = "whirlwind";
    rows[3] = "into heaven";
    rows[4] = "Enter thou into";
    rows[5] = "the joy of thy";
    rows[6] = "Lord";
    rows[7] = "Redeemed on";

#ifdef TTY_GRAPHICS
    if (endcut_tty()) {
        int r, c;
        char stone[23][80];
        int color[23][80];

        memset(stone, ' ', sizeof stone);
        for (r = 0; r < 23; r++)
            stone[r][79] = '\0';
        for (r = 0; r < 23; r++)
            for (c = 0; c < 80; c++)
                color[r][c] = CLR_BLACK;
        /* Rays and stars, then the gold frame, then the white words.
           Layout follows stone.py: inner width 36, left margin 16. */
        {
            const char *top1 = "      *     .     \\   |   /     .     *";
            const char *top2 = "          .      \\  |  /      .";
            int left = 16;

            memcpy(stone[0] + left + 6, top1, strlen(top1));
            memcpy(stone[1] + left + 10, top2, strlen(top2));
            memset(stone[2] + left + 4, '_', 30);
            stone[3][left + 2] = '/';
            memset(stone[3] + left + 3, ' ', 32);
            stone[3][left + 35] = '\\';
            stone[4][left + 1] = '/';
            endcut_center(body, 34, "+    REDEEMED    +");
            memcpy(stone[4] + left + 2, body, 34);
            stone[4][left + 36] = '\\';
            for (i = 0; i < 15; i++) {
                const char *word = "";

                stone[5 + i][left] = '|';
                stone[5 + i][left + 37] = '|';
                if (i == 1)
                    word = rows[0];
                else if (i == 3)
                    word = rows[1];
                else if (i == 4)
                    word = rows[2];
                else if (i == 5)
                    word = rows[3];
                else if (i == 7)
                    word = rows[4];
                else if (i == 8)
                    word = rows[5];
                else if (i == 9)
                    word = rows[6];
                else if (i == 11)
                    word = rows[7];
                else if (i == 12)
                    word = date;
                else if (i == 13)
                    word = clock;
                if (*word) {
                    endcut_center(body, 36, word);
                    memcpy(stone[5 + i] + left + 1, body, 36);
                }
            }
            memcpy(stone[20] + left - 5, "*    |", 6);
            memset(stone[20] + left + 1, '_', 36);
            memcpy(stone[20] + left + 37, "|    *", 6);
            memcpy(stone[21] + left - 8, "________|", 9);
            memset(stone[21] + left + 1, ' ', 36);
            memcpy(stone[21] + left + 37, "|________", 9);
            stone[22][left - 9] = '/';
            memset(stone[22] + left - 8, '_', 54);
            stone[22][left + 46] = '\\';
        }
        tty_endcut_begin();
        for (r = 0; r < 23; r++)
            for (c = 0; c < 80; c++) {
                char ch = stone[r][c];
                int colr = CLR_BLACK;

                if (ch == ' ' || ch == '\0')
                    continue;
                if (r < 2 || ch == '*' || ch == '.')
                    colr = CLR_YELLOW;
                else if (r == 4 && (ch == '+' || (ch >= 'A' && ch <= 'Z')))
                    colr = CLR_YELLOW;
                else if (r >= 5 && r <= 19 && ch != '|')
                    colr = CLR_WHITE;
                else
                    colr = CLR_YELLOW;
                tty_endcut_cell(c, r, ch, colr, 0);
            }
        tty_endcut_flush();
        while (!endcut_wait(500))
            ;
        tty_endcut_end();
    }
#endif
    if (extra != WIN_ERR) {
        putstr(extra, 0, "+ REDEEMED +");
        putstr(extra, 0, "");
        for (i = 0; i < 8; i++) {
            putstr(extra, 0, rows[i]);
            if (i == 0 || i == 3 || i == 6)
                putstr(extra, 0, "");
        }
        putstr(extra, 0, date);
        putstr(extra, 0, clock);
    } else if (!endcut_tty()) {
        winid win = create_nhwindow(NHW_TEXT);

        putstr(win, 0, "+ REDEEMED +");
        putstr(win, 0, name);
        putstr(win, 0, "went up by a");
        putstr(win, 0, "whirlwind");
        putstr(win, 0, "into heaven");
        putstr(win, 0, "");
        putstr(win, 0, "Enter thou into");
        putstr(win, 0, "the joy of thy");
        putstr(win, 0, "Lord");
        putstr(win, 0, "");
        putstr(win, 0, "Redeemed on");
        putstr(win, 0, date);
        putstr(win, 0, clock);
        display_nhwindow(win, TRUE);
        destroy_nhwindow(win);
    }
}

/*endcut.c*/
