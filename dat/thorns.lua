-- The Thorns, a Road trial. The city is revealed and lit on arrival.
-- Placeholder letters in the design map are floor here.
des.level_init({ style = "solidfill", fg = " " })
des.level_flags("mazelevel", "nomongen", "noteleport", "hardfloor", "noflip", "premapped")
des.map({ halign = "left", map = [[
---------------------------------------------------------------------------
|.........|.........|.........|......<......|.........|.........|.........|
|.........|.........|.........|..{.......{..|.........|.........|.........|
|.........|.........|.........|....T...T....|.........|.........|.........|
-----+---------+---------+-----.............-----+---------+---------+-----
|..T...T...T...T...T...T...T...T...T...T...T...T...T...T...T...T...T...T..|
-------------.................................................-------------
|...........|....T...T...T..---------+---------..T...T...T....|...........|
|...........+...T...T...T...|.................|...T...T...T...+...........|
|...........|..T.-------....|..{...........{..|....-------.T..|...........|
-------------.T..|.....|..T.|.................|.T..|.....|..T.-------------
|...........|....|.....|.T..|..{...........{..|..T.|.....|....|...........|
|...........+...T---+---T...|.................|...T---+---T...+...........|
|...........|..T...T...T....---------+---------....T...T...T..|...........|
-------------.................................................-------------
|..............T...T...T...T...T...T...T...T...T...T...T...T..............|
-------+-------------+-------.................-------+-------------+-------
|.............|.............|.T.............T.|.............|.............|
|.............|.............|...{.........{...|.............|.............|
|.............|.............|.T......>......T.|.............|.............|
---------------------------------------------------------------------------
]] });
des.wallify()
des.stair("up", 37, 1)
des.stair("down", 37, 19)
des.door("open", 5, 4)
des.door("open", 15, 4)
des.door("open", 25, 4)
des.door("open", 49, 4)
des.door("open", 59, 4)
des.door("open", 69, 4)
des.door("open", 37, 7)
des.door("open", 12, 8)
des.door("open", 62, 8)
des.door("open", 12, 12)
des.door("open", 20, 12)
des.door("open", 54, 12)
des.door("open", 62, 12)
des.door("open", 37, 13)
des.door("open", 7, 16)
des.door("open", 21, 16)
des.door("open", 53, 16)
des.door("open", 67, 16)
des.region({ region = {0, 0, 74, 20}, lit = 1, type = "ordinary" })
des.engraving({ x=5, y=5, type="verse", degrade=false, text="The Golden Scales" })
des.engraving({ x=16, y=5, type="verse", degrade=false, text="The Gilded Calf" })
des.engraving({ x=25, y=5, type="verse", degrade=false, text="Purple and Fine Linen" })
des.engraving({ x=49, y=5, type="verse", degrade=false, text="The Receipt of Custom" })
des.engraving({ x=58, y=5, type="verse", degrade=false, text="The Neverending Hour" })
des.engraving({ x=69, y=5, type="verse", degrade=false, text="Pearls of Great Price" })
des.engraving({ x=13, y=8, type="verse", degrade=false, text="Eat, Drink, and Be Merry" })
des.engraving({ x=61, y=8, type="verse", degrade=false, text="Scales of the Dragon" })
des.engraving({ x=13, y=12, type="verse", degrade=false, text="The Lot and the Lucky Throw" })
des.engraving({ x=61, y=12, type="verse", degrade=false, text="Balm of Gilead" })
des.engraving({ x=7, y=15, type="verse", degrade=false, text="The Overflowing Cup" })
des.engraving({ x=21, y=15, type="verse", degrade=false, text="Nothing Ventured" })
des.engraving({ x=53, y=15, type="verse", degrade=false, text="The Book of the Living" })
des.engraving({ x=67, y=15, type="verse", degrade=false, text="The Sharpened Edge" })
des.engraving({ x=20, y=13, type="verse", degrade=false, text="The Fountain of Youth" })
des.engraving({ x=54, y=13, type="verse", degrade=false, text="The Lance and Pennant" })
des.engraving({ x=37, y=6, type="verse", degrade=false, text="The House of All Desires" })
des.engraving({ x=37, y=14, type="verse", degrade=false, text="The House of All Desires" })
des.monster({ id = "tempter", name = "Moneychanger", x = 5, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Goldsmith", x = 15, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Silk merchant", x = 25, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Tax collector", x = 49, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Jeweler", x = 59, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Gem cutter", x = 69, y = 2, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Banquet host", x = 6, y = 8, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Armorer", x = 68, y = 8, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Gambling hall dealer", x = 6, y = 12, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Physician", x = 68, y = 12, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Wine merchant", x = 7, y = 18, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Pawnbroker", x = 21, y = 18, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Scribe", x = 53, y = 18, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Weaponsmith", x = 67, y = 18, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Bathhouse keeper", x = 20, y = 10, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "Knight-errant armsman", x = 54, y = 10, peaceful = 1, waiting = 1 })
des.monster({ id = "tempter", name = "The Prince of the city", x = 37, y = 10, peaceful = 1, waiting = 1 })
