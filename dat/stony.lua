-- The Stony Ground, trial 2 of the Road to Salvation.
-- Mountains are stone (space). L is lava. The ## in rows 5-9 is the
-- iron drawbridge, turned into a fixed open bridge by stony_setup().
-- The other # marks are a hidden corridor east of camp. S at (59, 12)
-- is a secret door. < is the summit exit. > is the foot stair.
des.level_init({ style = "solidfill", fg = " " });
des.level_flags("mazelevel", "nomongen", "hardfloor", "noflip")
des.map({ halign = "left", map = [[
                                                                           
                ......................                                     
                ....<....................                                  
                ..............   ..............                            
                                            ........                       
                                    LLLLLLLLLLL##LLLLLLLLLLLLLL            
                                  L LLLLLLLLLLL##LLLLLLLLLLLLL L           
                                    LLLLLLLLLLL##LLLLLLLLLLLLL             
                                   LLLLLLLLLLLL##LLLLLLLLLLLLL             
                                  LLLLLLLLLLLLL##LLLLLLLLLLLLLL            
                                      ..................{..                
                                      .....................                
                                      .....................S#####          
                                      .....................     #          
                                 ..........................     #          
                           ........                             ####       
                     ........                                     .......  
               ........                                           .......  
         ........                                                 .......  
>..........                                                       .......  
                                                                           
]] });
des.stair("down", 0, 19)
des.stair("up", 20, 2)
des.door("secret", 59, 12)
des.monster({ id = "traveler", name = "young believer", x = 42, y = 11, peaceful = 1, waiting = 1 })
des.monster({ id = "traveler", name = "old man", x = 48, y = 11, peaceful = 1, waiting = 1 })
des.monster({ id = "traveler", name = "mother", x = 54, y = 11, peaceful = 1, waiting = 1 })
des.object({ id = "chest", x = 71, y = 18, contents = function()
    des.object({ id = "tranquility", class = "/", spe = 3 })
    des.object({ id = "healing", class = "+", spe = 1 })
    des.object({ id = "protection", class = "=", spe = 5, buc = "blessed" })
end })
