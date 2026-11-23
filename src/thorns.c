/* RighteousHack: the Thorns, a Road trial.
   State lives on the hero (u.uthorns) and is saved with struct you.
   EDITLEVEL 18. Nothing here is written into bones. */

#include "hack.h"

/* Map column 0 is level x = 1. Rows are unchanged. */
#define TX(c) ((coordxy) ((c) + 1))

#define TH_N 17
/* Bits 0..16 are the tempters. This spare bit records the intro. */
#define TH_INTRO 0x80000000UL

#define TH_GOLD   1
#define TH_DOUBLE 2
#define TH_SELL   3
#define TH_GIFT   4
#define TH_LIFE   5

#define TF_PROOF  0x01
#define TF_GEMS   0x02

struct thorn_def {
    const char *name;
    const char *line;
    const char *offer;
    coordxy mx, my;
    int kind;
    int amount; /* gold, sell multiple, object type, or life */
    int spe;
    int quan;
    unsigned flags;
};

/* Spot order matches the approved offer table. */
static const struct thorn_def thorns[TH_N] = {
    { "Wine merchant",
      "Come, weary one, and drink. Fifteen hundred pieces of gold for the asking, and the cup never runneth dry in this city.",
      "Fifteen hundred pieces of gold.",
      7, 18, TH_GOLD, 1500, 0, 1, 0 },
    { "Moneychanger",
      "The scales are balanced in thy favor today, friend. Three thousand gold, weighed out freely. What could it cost thee?",
      "Three thousand pieces of gold.",
      5, 2, TH_GOLD, 3000, 0, 1, 0 },
    { "Silk merchant",
      "Thou art clothed in rags of iron and blood. Take five thousand gold and walk in purple and fine linen, as a man of worth.",
      "Five thousand pieces of gold.",
      25, 2, TH_GOLD, 5000, 0, 1, 0 },
    { "Tax collector",
      "I have gathered the tribute of a hundred cities. Eight thousand pieces of it are thine. Render unto thyself, for once.",
      "Eight thousand pieces of gold.",
      49, 2, TH_GOLD, 8000, 0, 1, 0 },
    { "Gambling hall dealer",
      "Cast the lot! Whatever gold thou bearest, I shall double it. Fortune smileth on the bold, and thou art very bold.",
      "I shall double whatever gold thou carriest.",
      6, 12, TH_DOUBLE, 0, 0, 1, 0 },
    { "Pawnbroker",
      "Everything thou carriest is worth more than thou knowest. I shall pay five times its price, and ask no questions.",
      "I shall buy any thing at five times its price.",
      21, 18, TH_SELL, 5, 0, 1, 0 },
    { "Goldsmith",
      "Ten times the worth of thy goods, paid in pure gold. Did not Aaron's calf shine fairer than any stone tablet?",
      "I shall buy any thing at ten times its price.",
      15, 2, TH_SELL, 10, 0, 1, 0 },
    { "Gem cutter",
      "Pearls of great price, thou sayest? I shall pay twenty times it. Sell what thou hast, and be rich indeed.",
      "I shall buy gems at twenty times their price.",
      69, 2, TH_SELL, 20, 0, 1, TF_GEMS },
    { "Banquet host",
      "Sit, eat, and be merry! Take this horn, and thou shalt never hunger again. Tomorrow is a long way off.",
      "A blessed horn of plenty, fully charged.",
      6, 8, TH_GIFT, HORN_OF_PLENTY, 20, 1, 0 },
    { "Physician",
      "Thy wounds are many. Here is balm enough to make thee whole three times over. Why suffer, when healing is so near?",
      "Three blessed oils of full healing.",
      68, 12, TH_GIFT, ANO_FULL_HEALING, 0, 3, 0 },
    { "Scribe",
      "This verse of judgement was copied by my own hand. Speak it, and the wicked shall be cut off from the earth. Such power, and so light to carry.",
      "A blessed verse of judgement to the wicked.",
      53, 18, TH_GIFT, SCR_GENOCIDE, 0, 1, 0 },
    { "Jeweler",
      "Wear this, and death itself shall pass thee by. Is there any treasure greater than a life that cannot end?",
      "A blessed amulet of life saving.",
      59, 2, TH_GIFT, AMULET_OF_LIFE_SAVING, 0, 1, 0 },
    { "Weaponsmith",
      "Silver, sharpened and blessed, that no foul thing can abide. Take it, warrior. Thy enemies will tremble.",
      "A blessed +5 rustproof silver saber.",
      67, 18, TH_GIFT, SILVER_SABER, 5, 1, TF_PROOF },
    { "Armorer",
      "The scales of a silver dragon, forged to turn every blow. Thou shalt walk through fire and ray unharmed.",
      "Blessed +5 silver dragon scale mail.",
      68, 8, TH_GIFT, SILVER_DRAGON_SCALE_MAIL, 5, 1, 0 },
    { "Bathhouse keeper",
      "Step into the waters, and thy strength shall be renewed. Twenty measures of life, poured into thy bones.",
      "Twenty measures of life.",
      20, 10, TH_LIFE, 20, 0, 1, 0 },
    { "Knight-errant armsman",
      "A knight should never ride to battle unarmed! Behold this lance, true and rustproof. Couch it, and charge.",
      "A blessed +5 rustproof lance.",
      54, 10, TH_GIFT, LANCE, 5, 1, TF_PROOF },
    { "The Prince of the city",
      "All these things will I give thee. Name thy desire, and it shall be done. One word, and the world is thine.",
      "A wand of wishing with one charge.",
      37, 10, TH_GIFT, WAN_WISHING, 1, 1, 0 },
};

static boolean dying = FALSE;

static boolean
thorns_level(d_level *lev)
{
    s_level *slev = find_level("thorns");

    return (boolean) (lev && slev && on_level(lev, &slev->dlevel));
}

static boolean
thorns_here(void)
{
    return thorns_level(&u.uz);
}

boolean
thorns_trial_done(void)
{
    return (boolean) (u.uthorns.done != 0);
}

boolean
thorns_fatal(void)
{
    return dying;
}

boolean
thorns_is_tempter(struct monst *mtmp)
{
    return (boolean) (mtmp && mtmp->data == &mons[PM_TEMPTER]);
}

static int
which_tempter(struct monst *mtmp)
{
    int i;
    unsigned id;

    if (!thorns_is_tempter(mtmp))
        return -1;
    id = mtmp->m_id;
    for (i = 0; i < TH_N; i++)
        if (u.uthorns.id[i] && u.uthorns.id[i] == id)
            return i;
    if (!has_mgivenname(mtmp))
        return -1;
    for (i = 0; i < TH_N; i++)
        if (!strcmp(MGIVENNAME(mtmp), thorns[i].name)) {
            u.uthorns.id[i] = id;
            return i;
        }
    return -1;
}

static struct monst *
tempter_by(int who)
{
    struct monst *mtmp;
    unsigned id;

    if (who < 0 || who >= TH_N)
        return (struct monst *) 0;
    id = u.uthorns.id[who];
    if (!id)
        return (struct monst *) 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon)
        if (!DEADMONSTER(mtmp) && mtmp->m_id == id)
            return mtmp;
    return (struct monst *) 0;
}

static void
calm_tempter(struct monst *mtmp)
{
    mtmp->mpeaceful = 1;
    mtmp->mtame = 0;
    mtmp->mflee = 0;
    mtmp->msleeping = 0;
    mtmp->mstrategy = STRAT_WAITFORU;
    if (mtmp->mhp < mtmp->mhpmax)
        mtmp->mhp = mtmp->mhpmax;
}

static void
plant_one(coordxy x, coordxy y, boolean up, d_level *dest)
{
    stairway *st;
    schar want = up ? LA_UP : LA_DOWN;

    if (!isok(x, y))
        return;
    if (levl[x][y].typ != STAIRS || levl[x][y].ladder != want) {
        levl[x][y].typ = STAIRS;
        levl[x][y].ladder = want;
        if (!gi.in_mklev)
            newsym(x, y);
    }
    st = stairway_at(x, y);
    if (!st)
        stairway_add(x, y, up, FALSE, dest);
    else {
        st->up = up;
        st->isladder = FALSE;
        assign_level(&st->tolev, dest);
    }
}

/* Down at the entry, up at the exit. A one-level branch cannot
   grow either stair toward Gehennom by itself. */
static void
aim_stairs(void)
{
    d_level back, onward;

    if (!trial_link("thorns", &back, &onward)) {
        back = valley_level;
        onward = valley_level;
    }
    plant_one(TX(37), 19, FALSE, &back);
    plant_one(TX(37), 1, TRUE, &onward);
}

static void
place_tempter(int who)
{
    struct monst *mtmp;
    coordxy x = TX(thorns[who].mx), y = thorns[who].my;

    mtmp = tempter_by(who);
    if (mtmp) {
        calm_tempter(mtmp);
        if ((mtmp->mx != x || mtmp->my != y) && !u_at(x, y)
            && !MON_AT(x, y)) {
            coordxy ox = mtmp->mx, oy = mtmp->my;

            remove_monster(ox, oy);
            place_monster(mtmp, x, y);
            newsym(ox, oy);
            newsym(x, y);
        }
        return;
    }
    if (u_at(x, y) || MON_AT(x, y))
        return;
    mtmp = makemon(&mons[PM_TEMPTER], x, y, MM_NOWAIT);
    if (!mtmp)
        return;
    mtmp = christen_monst(mtmp, thorns[who].name);
    if (!mtmp)
        return;
    u.uthorns.id[who] = mtmp->m_id;
    calm_tempter(mtmp);
}

static void
tag_tempters(void)
{
    struct monst *mtmp;
    int i;

    for (i = 0; i < TH_N; i++)
        u.uthorns.id[i] = 0;
    for (mtmp = fmon; mtmp; mtmp = mtmp->nmon) {
        i = which_tempter(mtmp);
        if (i >= 0)
            calm_tempter(mtmp);
    }
}

void
thorns_setup(void)
{
    if (!thorns_here())
        return;
    tag_tempters();
    aim_stairs();
    vision_reset();
    vision_recalc(0);
}

void
thorns_tick(void)
{
    int i;

    if (!thorns_here())
        return;
    if (!(u.uthorns.given & TH_INTRO)) {
        wayside_screen(
            "Behold, a gilded city! Its towers flash like fire in the sun, and its streets shine with gold.\n"
            "\n"
            "Merchants in fine robes beckon from every doorway, each holding out a gift fit for a king. Music and laughter drift from the banquet halls, and nothing here is denied thee.\n"
            "\n"
            "Here is everything a weary pilgrim could desire. Riches without labor. Healing without suffering. Power without price.");
        u.uthorns.given |= TH_INTRO;
    }
    for (i = 0; i < TH_N; i++)
        place_tempter(i);
}

/* Leaving by the up stair, alive, finishes the trial.
   The down stair is a retreat and does not. */
void
thorns_note_ascent(void)
{
    if (!thorns_here())
        return;
    if (Upolyd ? (u.mh <= 0) : (u.uhp <= 0))
        return;
    u.uthorns.done = 1;
}

static const char *
strike_whom(struct monst *mtmp)
{
    if (mtmp->female || is_female(mtmp->data))
        return "her";
    if (is_male(mtmp->data))
        return "him";
    return "it";
}

boolean
thorns_unharmed(struct monst *mtmp)
{
    if (!thorns_is_tempter(mtmp))
        return FALSE;
    pline("Thou canst not bring thyself to strike %s.", strike_whom(mtmp));
    mtmp->mpeaceful = 1;
    return TRUE;
}

static long
add_cap(long a, long b)
{
    if (b <= 0)
        return a;
    if (a > LONG_MAX - b)
        return LONG_MAX;
    return a + b;
}

/* Loose gold plus gold inside carried containers. Not the floor. */
static long
carried_gold(void)
{
    struct obj *otmp;
    long n = money_cnt(gi.invent);

    for (otmp = gi.invent; otmp; otmp = otmp->nobj)
        if (Has_contents(otmp))
            n = add_cap(n, contained_gold(otmp, TRUE));
    return n;
}

static void
give_gold(long amount)
{
    struct obj *gold;
    long have, room;

    if (amount <= 0L)
        return;
    have = money_cnt(gi.invent);
    room = (have >= LONG_MAX) ? 0L : LONG_MAX - have;
    if (amount > room)
        amount = room;
    if (amount <= 0L)
        return;
    gold = mksobj(GOLD_PIECE, FALSE, FALSE);
    if (!gold)
        return;
    gold->quan = amount;
    gold->owt = weight(gold);
    gold->dknown = gold->known = 1;
    (void) hold_another_object(gold, "Oops!  %s to the floor!",
                               The(aobjnam(gold, "slip")),
                               (const char *) 0);
}

static void
give_obj(int otyp, int quan, int spe, boolean blessed, boolean proof)
{
    struct obj *otmp = mksobj(otyp, FALSE, FALSE);

    if (!otmp)
        return;
    otmp->quan = quan;
    if (blessed)
        bless(otmp);
    else
        uncurse(otmp);
    otmp->spe = spe;
    if (proof)
        otmp->oerodeproof = 1;
    otmp->known = otmp->dknown = otmp->bknown = 1;
    otmp->owt = weight(otmp);
    pline("Thou receivest %s.", doname(otmp));
    (void) hold_another_object(otmp, "Oops!  %s to the floor!",
                               The(aobjnam(otmp, "slip")),
                               (const char *) 0);
}

/* First through third thorns drain, and never kill.
   Polymorph uses the same numbers on both bodies. */
static void
drain_life(int n)
{
    int umax = u.uhpmax - n;
    int ucur = u.uhp - n;

    if (umax < 1)
        umax = 1;
    if (ucur < 1)
        ucur = 1;
    if (ucur > umax)
        ucur = umax;
    u.uhpmax = umax;
    u.uhp = ucur;
    if (Upolyd) {
        int pmax = u.mhmax - n;
        int pcur = u.mh - n;

        if (pmax < 1)
            pmax = 1;
        if (pcur < 1)
            pcur = 1;
        if (pcur > pmax)
            pcur = pmax;
        u.mhmax = pmax;
        u.mh = pcur;
    }
    disp.botl = TRUE;
}

static void
grant_life(int n)
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
choke(void)
{
    dying = TRUE;
    svk.killer.format = NO_KILLER_PREFIX;
    Strcpy(svk.killer.name, "Choked by the thorns of this world.");
    done(DIED);
    /* Wizard or explore mode answered the Die? prompt. */
    dying = FALSE;
}

static boolean
refused_ware(struct obj *otmp)
{
    if (otmp->oartifact || objects[otmp->otyp].oc_unique
        || otmp->otyp == AMULET_OF_YENDOR) {
        pline("I will not buy that.");
        return TRUE;
    }
    if (otmp->unpaid) {
        pline("That is not thine to sell.");
        return TRUE;
    }
    return FALSE;
}

static void
spill_contents(struct obj *otmp)
{
    while (Has_contents(otmp)) {
        struct obj *inner = otmp->cobj;

        obj_extract_self(inner);
        (void) hold_another_object(inner, "Oops!  %s to the floor!",
                                   The(aobjnam(inner, "slip")),
                                   (const char *) 0);
    }
}

/* One sale. Returns TRUE when the visit should end. */
static boolean
sell_one(const struct thorn_def *def)
{
    char buf[BUFSZ];
    char *p;
    long cnt = 0;
    struct obj *otmp;
    long price, unit;

    if (!gi.invent) {
        pline("Thou hast nothing to sell.");
        return TRUE;
    }
    (void) display_inventory((char *) 0, FALSE);
    buf[0] = '\0';
    getlin("What wilt thou sell?", buf);
    if (buf[0] == '\033' || buf[0] == '\0')
        return TRUE;
    p = buf;
    while (*p == ' ')
        p++;
    if (digit(*p)) {
        cnt = atol(p);
        while (digit(*p))
            p++;
    }
    for (otmp = gi.invent; otmp; otmp = otmp->nobj)
        if (otmp->invlet == *p)
            break;
    if (!otmp) {
        pline("Thou hast no such thing.");
        return FALSE;
    }
    if ((def->flags & TF_GEMS) && otmp->oclass != GEM_CLASS) {
        pline("I buy gems only.");
        return FALSE;
    }
    if (refused_ware(otmp))
        return FALSE;
    if (otmp->owornmask) {
        if (y_n("Thou wearest it. Wilt thou take it off and sell it?") != 'y')
            return FALSE;
        remove_worn_item(otmp, FALSE);
        if (otmp->owornmask) {
            pline("It will not leave thee.");
            return FALSE;
        }
        cnt = 0; /* the whole piece, now unworn */
    }
    if (cnt > 0L && cnt < otmp->quan)
        otmp = splitobj(otmp, cnt);
    unit = (long) objects[otmp->otyp].oc_cost * (long) def->amount;
    if (otmp->quan > 1L && unit > LONG_MAX / otmp->quan)
        price = LONG_MAX;
    else
        price = unit * otmp->quan;
    give_gold(price);
    pline("Thou art paid %ld gold pieces.", price);
    spill_contents(otmp);
    obj_extract_self(otmp);
    obfree(otmp, (struct obj *) 0);
    return (boolean) (y_n("Wilt thou sell another?") != 'y');
}

static void
sell_visit(const struct thorn_def *def)
{
    /* The thorn is already spent. They may sell nothing. */
    while (!sell_one(def))
        ;
}

static void
grant(const struct thorn_def *def)
{
    switch (def->kind) {
    case TH_GOLD:
        give_gold((long) def->amount);
        break;
    case TH_DOUBLE:
        /* No gold carried: the thorn is still spent. */
        give_gold(carried_gold());
        break;
    case TH_LIFE:
        grant_life(def->amount);
        break;
    case TH_GIFT:
        /* The prince's rod is not blessed. Every other gift is. */
        give_obj(def->amount, def->quan, def->spe,
                 (boolean) (def->amount != WAN_WISHING),
                 (boolean) ((def->flags & TF_PROOF) != 0));
        break;
    default:
        break;
    }
}

boolean
thorns_chat(struct monst *mtmp)
{
    int who;
    const struct thorn_def *def;
    int before;

    who = which_tempter(mtmp);
    if (who < 0)
        return FALSE;
    calm_tempter(mtmp);
    def = &thorns[who];
    pline("%s", def->line);
    if (u.uthorns.given & (1UL << who)) {
        pline("I have already given thee my gift.");
        return TRUE;
    }
    pline("%s", def->offer);
    if (y_n("Wilt thou accept this gift?") != 'y')
        return TRUE; /* browsing is free */
    if (u.uthorns.accepts >= 3) {
        pline("The thorns close over thy heart. Thou art choked by the cares of this world.");
        u.uthorns.accepts = 4;
        choke();
        u.uthorns.accepts = 3;
        return TRUE;
    }
    before = (int) u.uthorns.accepts;
    grant(def);
    drain_life(10 * (before + 1));
    pline("Thorns spring up around thee and tighten. Thou feelest life drain from thee.");
    u.uthorns.given |= (1UL << who);
    u.uthorns.accepts = (xint16) (before + 1);
    if (def->kind == TH_SELL)
        sell_visit(def);
    return TRUE;
}
