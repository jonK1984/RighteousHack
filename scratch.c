
/* determine prayer results in advance; also used for enlightenment */
boolean
can_pray(boolean praying) /* false means no messages should be given */
{
    int alignment;

    gp.p_aligntyp = on_altar() ? a_align(u.ux, u.uy) : u.ualign.type;
    gp.p_trouble = in_trouble();


    if (praying)
        You("begin praying to %s.", align_gname(gp.p_aligntyp));

    

    if (gp.p_aligntyp == A_NONE) /* alter of evil */ {
        pline("Underneath this altar of great evil, you sense a soul trapped beneath. You must smash it to pieces!");
        return FALSE;
    }
    else if ((gp.p_trouble > 0) ? (u.ublesscnt > 200)   /* big trouble */
             : (gp.p_trouble < 0) ? (u.ublesscnt > 100) /* minor difficulty */
               : (u.ublesscnt > 0))                     /* not in trouble */
        gp.p_type = 0;                     /* too soon... */
    else if ((int) Luck < 0 || u.ugangr || alignment < 0)
        gp.p_type = 1; /* too naughty... */
    else /* alignment >= 0 */ {
        if (on_altar() && u.ualign.type != gp.p_aligntyp)
            gp.p_type = 2;
        else
            gp.p_type = 3;
    }

    
    /* Note:  when !praying, the random factor for neutrals makes the
       return value a non-deterministic approximation for enlightenment.
       This case should be uncommon enough to live with... */

    //return !praying ? (boolean) (gp.p_type == 3 && !Inhell) : TRUE;
    return TRUE;
}


staticfn int
prayer_done(void) /* M. Stephenson (1.0.3b) */
{
    aligntyp alignment = gp.p_aligntyp;

    u.uinvulnerable = FALSE;
    
    if (Inhell) {
        pline("And the light shineth in darkness; and the darkness comprehended it not. (John 1:5)");
    }

    if (gp.p_type == 0) {
        if (on_altar() && u.ualign.type != alignment)
            (void) water_prayer(FALSE);
        u.ublesscnt += rnz(250);
        change_luck(-3);
        
    } else if (gp.p_type == 1) {
        if (on_altar() && u.ualign.type != alignment)
            (void) water_prayer(FALSE);
        pline("placeholder for angrygods() deletion");
    } else if (gp.p_type == 2) {
        if (water_prayer(FALSE)) {
            /* attempted water prayer on a non-coaligned altar */
            u.ublesscnt += rnz(250);
            change_luck(-3);
            
        } else
            pleased(alignment);
    } else {
        /* coaligned */
        if (on_altar()) {
            (void) pray_revive();
            (void) water_prayer(TRUE);
        }
        pleased(alignment); /* nice */
    }
    return 1;
}
