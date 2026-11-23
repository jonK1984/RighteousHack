/* RighteousHack: the Fiery Steed of the Heavenly Host breathes a
   ring of holy fire. The wait is saved on the hero. EDITLEVEL 19. */

#include "hack.h"

/* Column first, matching explode()'s 3x3 frame. The center is the hero. */
static const int ring_piece[3][3] = {
    { S_expl_tl, S_expl_ml, S_expl_bl },
    { S_expl_tc, S_expl_mc, S_expl_bc },
    { S_expl_tr, S_expl_mr, S_expl_br }
};

static boolean
riding_fiery_steed(void)
{
    return (boolean) (u.usteed
                      && u.usteed->data == &mons[PM_FIERY_STEED_OF_HEAVEN]);
}

/* Yellow, then orange, then red, on the eight squares around the hero. */
static void
holy_fire_ring(void)
{
    static const int hue[3] = { CLR_YELLOW, CLR_ORANGE, CLR_RED };
    coordxy xs[8], ys[8];
    int glyph[8];
    int n = 0, i, j, f, k;

    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++) {
            coordxy x = u.ux + i - 1, y = u.uy + j - 1;

            if (i == 1 && j == 1)
                continue;
            if (!isok(x, y))
                continue;
            xs[n] = x;
            ys[n] = y;
            glyph[n] = explosion_to_glyph(EXPL_FIERY, ring_piece[i][j]);
            n++;
        }
    if (!n)
        return;
    for (f = 0; f < 3; f++) {
        set_fiery_expl_color(hue[f]);
        for (k = 0; k < n; k++) {
            if (f == 0 && k == 0)
                tmp_at(DISP_ALL, glyph[k]);
            else
                tmp_at(DISP_CHANGE, glyph[k]);
            tmp_at(xs[k], ys[k]);
        }
        curs_on_u();
        nh_delay_output();
    }
    set_fiery_expl_color(-1);
    tmp_at(DISP_END, 0);
}

/* One hostile neighbor. Fire resistance blocks the hit points, not
   the knockback and not the burning of what it carries. */
static void
scorch_one(struct monst *mtmp)
{
    int blast, extra;

    if (!mtmp || DEADMONSTER(mtmp))
        return;
    blast = d(6, 6);
    if (resists_fire(mtmp) || defended(mtmp, AD_FIRE)) {
        if (!Blind)
            pline_The("fire doesn't heat %s!", mon_nam(mtmp));
        golemeffects(mtmp, AD_FIRE, blast);
        shieldeff(mtmp->mx, mtmp->my);
        (void) destroy_items(mtmp, AD_FIRE, blast);
        (void) burnarmor(mtmp);
        ignite_items(mtmp->minvent);
        return;
    }
    if (completelyburns(mtmp->data)) {
        if (!Blind)
            pline("%s %s!", Monnam(mtmp),
                  !mlifesaver(mtmp) ? "burns completely"
                                    : "is totally engulfed in flames");
        xkilled(mtmp, XKILL_NOMSG | XKILL_NOCORPSE);
        return;
    }
    extra = destroy_items(mtmp, AD_FIRE, blast);
    (void) burnarmor(mtmp);
    ignite_items(mtmp->minvent);
    mtmp->mhp -= blast + extra;
    if (mtmp->mhp <= 0) {
        int xkflg = completelyburns(mtmp->data) ? XKILL_NOCORPSE : 0;

        xkilled(mtmp, XKILL_GIVEMSG | xkflg);
    } else {
        setmangry(mtmp, TRUE);
    }
}

static void
loose_the_fire(void)
{
    struct monst *hit[8];
    int dxs[8], dys[8];
    int n = 0, i, dx, dy;

    pline("Thy steed breatheth forth a ring of holy fire!");
    holy_fire_ring();
    for (dx = -1; dx <= 1; dx++)
        for (dy = -1; dy <= 1; dy++) {
            struct monst *mtmp;
            coordxy x, y;

            if (!dx && !dy)
                continue;
            x = u.ux + dx;
            y = u.uy + dy;
            if (!isok(x, y))
                continue;
            /* Floor goods burn on every square. A pet or a peaceful
               keeps its own pack. */
            if (OBJ_AT(x, y))
                (void) burn_floor_objects(x, y, cansee(x, y), TRUE);
            mtmp = m_at(x, y);
            if (!mtmp || DEADMONSTER(mtmp))
                continue;
            if (mtmp->mtame || mtmp->mpeaceful)
                continue;
            scorch_one(mtmp);
            if (DEADMONSTER(mtmp))
                continue;
            hit[n] = mtmp;
            dxs[n] = dx;
            dys[n] = dy;
            n++;
        }
    /* Resistance does not stop the shove. One square, straight away. */
    for (i = 0; i < n; i++)
        if (!DEADMONSTER(hit[i]))
            mhurtle(hit[i], dxs[i], dys[i], 1);
    u.ufirewait = 300 + rnd(100);
}

/* -1: this chat is not the steed. Otherwise an ECMD_ result.
   Declining, or a steed whose fire is still out, costs no time. */
int
steed_loose_fire(void)
{
    if (!riding_fiery_steed())
        return -1;
    if (u.ufirewait > 0) {
        pline("Thy steed's fire is not yet rekindled.");
        return ECMD_OK;
    }
    if (y_n("Bid thy steed loose its fire?") != 'y')
        return ECMD_OK;
    loose_the_fire();
    return ECMD_TIME;
}

void
steed_fire_tick(void)
{
    if (u.ufirewait > 0 && --u.ufirewait == 0)
        pline("Thou feelest the fire rekindle within thy steed.");
}
