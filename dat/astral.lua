-- NetHack endgame astral.lua	$NHDT-Date: 1652196020 2022/05/10 15:20:20 $  $NHDT-Branch: NetHack-3.7 $:$NHDT-Revision: 1.7 $
--	Copyright (c) 1989 by Jean-Christophe Collet
--	Copyright (c) 1992,1993 by Izchak Miller, David Cohrs,
--                      and Timo Hakulinen
-- NetHack may be freely redistributed.  See license for details.
--
des.level_init({ style = "solidfill", fg = " " });

des.level_flags("mazelevel", "noteleport", "hardfloor", "nommap", "shortsighted", "solidify")
des.message("You arrive on the Plane of Heaven!")
des.message("Here stand the high altar of the Lord and the high altar of the Great Dragon.")
des.message("You sense alarm, hostility, and excitement in the air!")
des.map([[
                              ---------------                              
                              |.............|                              
                              |..---------..|                              
                              |..|.......|..|                              
---------------               |..|.......|..|               ---------------
|.............|               |..|.......|..|               |.............|
|..---------..-|   |-------|  |..|.......|..|  |-------|   |-..---------..|
|..|.......|...-| |-.......-| |..|.......|..| |-.......-| |-...|.......|..|
|..|.......|....-|-.........-||..----+----..||-.........-|-....|.......|..|
|..|.......+.....+...........||.............||...........+.....+.......|..|
|..|.......|....-|-.........-|--|.........|--|-.........-|-....|.......|..|
|..|.......|...-| |-.......-|   -|---+---|-   |-.......-| |-...|.......|..|
|..---------..-|   |---+---|    |-.......-|    |---+---|   |-..---------..|
|.............|      |...|-----|-.........-|-----|...|      |.............|
---------------      |.........|...........|.........|      ---------------
                     -------...|-.........-|...-------                     
                           |....|-.......-|....|                           
                           ---...|---+---|...---                           
                             |...............|                             
                             -----------------                             
]]);

-- chance to alter above map and turn the wings of the bottom-center into
-- a pair of big (5x15) rooms
for i = 1, 2 do
   -- 3.6.[01]: 75% chance that both sides opened up, 25% that neither did;
   -- 3.6.2: 60% twice == 36% chance that both sides open up, 24% left side
   -- only, 24% right side only, 16% that neither side opens up
   local hall;
   if percent(60) then
     if i == 1 then
        des.terrain(selection.area(17,14, 30,18),".")
        des.wallify()
        -- temporarily close off the area to be filled so that it doesn't cover
        -- the entire entry area
        des.terrain(33,18, "|")
        hall = selection.floodfill(30,16)
        -- re-connect the opened wing with the rest of the map
        des.terrain(33,18, ".")
     else
        des.terrain(selection.area(44,14, 57,18),".")
        des.wallify()
        des.terrain(41,18, "|")
        hall = selection.floodfill(44,16)
        des.terrain(41,18, ".")
     end
     -- extra monsters; was [6 + 3d4] when both wings were opened up at once
     for j = 1, math.random(4,9) do
        if percent(50) then
           des.monster({ coord = hall:rndcoord(1), peaceful=0 })
        end
     end
   end
end

-- Rider locations
local place = selection.new();
place:set(23,9);
place:set(37,14);
place:set(51,9);

-- Where the player will land on arrival
des.teleport_region({ region = {29,15,45,15}, exclude = {30,15,44,15} })
-- Lit courts
des.region({ region={01,05,16,14},lit=1,type="ordinary",irregular=1 })
des.region({ region={31,01,44,10},lit=1,type="ordinary",irregular=1 })
des.region({ region={61,05,74,14},lit=1,type="ordinary",irregular=1 })
-- Three temple rooms. des.heaven_temples() puts the Lord's altar,
-- the Great Dragon's altar, and the chest into them at random.
des.region({ region={04,07,10,11},lit=1,type="temple",filled=2 })
des.region({ region={34,03,40,07},lit=1,type="temple",filled=2 })
des.region({ region={64,07,70,11},lit=1,type="temple",filled=2 })

des.heaven_temples()
-- Doors
des.door("closed",11,09)
des.door("closed",17,09)
des.door("locked",23,12)
des.door("locked",37,08)
des.door("closed",37,11)
des.door("closed",37,17)
des.door("locked",51,12)
des.door("locked",57,09)
des.door("closed",63,09)
-- Non diggable and phazeable everywhere
des.non_diggable(selection.area(00,00,74,19))
des.non_passwall(selection.area(00,00,74,19))
-- The three Riders stay on the Dragon's side.
des.monster({ id = "Pestilence", coord = place:rndcoord(1), peaceful=0 })
des.monster({ id = "Death", coord = place:rndcoord(1), peaceful=0 })
des.monster({ id = "Famine", coord = place:rndcoord(1), peaceful=0 })
--
-- Assorted nasties
des.monster({ class = "L", peaceful=0 })
des.monster({ class = "L", peaceful=0 })
des.monster({ class = "L", peaceful=0 })
des.monster({ class = "V", peaceful=0 })
des.monster({ class = "V", peaceful=0 })
des.monster({ class = "V", peaceful=0 })
des.monster({ class = "D", peaceful=0 })
des.monster({ class = "D", peaceful=0 })
des.monster({ class = "D", peaceful=0 })
-- Both hosts. The chest room is whichever temple has no altar.
des.heaven_host()
