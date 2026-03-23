-- NetHack Royal Historian His-home.lua
-- The Great Library of Alexandria - Main Hall (Quest Home Level)
-- Royal Historian quest home level for RighteousHack.
-- The player arrives via the quest portal on a dock outside the library.
-- The building is surrounded by water (Nile harbor influence).
-- Inside: grand hall with columns, bookshelves filled with prophetic books,
-- a few trees/plants, the quest leader (Zenodotus), guardians, and stairs
-- up to the spire and down to the basement.

des.level_flags("noteleport", "hardfloor", "solidify", "noflip", "nomongen")

des.level_init({ style = "solidfill", fg = "}", bg = "W" })


-- Overall map: water around a central island/building with dock
--map size must be 76x20
-- TERRAIN LAYER --
des.map([[
|----|}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
|.LS.|}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
|--|.|}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
|....|}}}}}}}}}}}}}}}}}}}}}}--------------------------------------------|}}}
|-S--|}}}}}}}}}}}}}}}}}}}}}.|...|..|...|...|...+.|....S.................|}}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}.|-.-|-.--.---.-|-.-|.|....|+-+-S-+-S-+-+-S-+|}}}
}}}}}}}}}}}}}}}}}}}}}}}}....|..................|.S.|--|.|.|.|.|.|.|.|.|.|}}}
}}}}}}}}}}}}}}}}}}}}}}......--------+-+--------------|------------------|}}}
}}}}}}}}}}}}}}}}}}}T.................................|..................+.}}
}}}}}}}}}}}}}}}}}TTT.................................|...T..{...{...T...|.}}
}}}}}}}}}}}}}}}}}....................................+..TTT...{....TTT..|.}}
}}}}}}}}}}}}}}}}}TTT......T....--------+-+--------...|...T..........T...|.}}
}}}}}}}}}}}}}}}}}}}T.....TTT...|.||.||.....||.||.|...|......{...{.......+.}}
}}}}}}}}}}}}}}}}}}}}}}....T....|.................|...|...T..........T...|.}}
}}}}}}}}}}}}}}}}}}}}}}}}.......|.................|...+..TTT...{....TTT..|.}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}....|.||.||.|.|.||.||.|...|...T..........T...|.}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}}}-----------+------------|......{...{.......+.}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}................---+-----++-----+---.}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}....}}}}}}}}}}}......................}}
}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
]]);

-- Outer area becomes water (harbor around the library island)
--des.replace_terrain({ region = {00,00,75,19}, fromterrain = ".", toterrain = "W" })

-- Library interior: lit stone floor
--des.region({ region = {21,03,66,18}, lit = 1, type = "ordinary" })

-- Dungeon Description
-- LIGHTING LAYER --
-- Lighting regions
des.region(selection.area(00,00,07,06), "unlit")
des.region(selection.area(17,03,28,16), "lit")
des.region(selection.area(08,08,16,12), "lit")
des.region(selection.area(53,08,73,18), "lit")
des.region(selection.area(29,03,73,18), "lit")
des.region(selection.area(50,04,53,05), "unlit")
des.region(selection.area(47,04,48,06), "unlit")

-- Portal arrival point
des.levregion({ region = {26,8,26,8}, type="branch" })

-- Wooden dock extending north into the water
--des.terrain({ region = {37,02,40,02}, typ = "-" })  -- dock planks

-- Main entrance door (north side)
-- Grand marble columns inside the hall

-- Decorative trees for scholarly garden atmosphere

-- Bookshelves along the walls (non-diggable walls with objects)
--des.non_diggable({ region = {23,04,69,21} })

-- Place prophetic books on shelves (randomly scattered inside)



-- Quest leader: Zenodotus, the Chief Librarian (peaceful human)
des.monster({ id = "Zenodotus", x = 62, y = 12, peaceful = true, historic = true, name = "Zenodotus Chief Librarian" })

-- NPC LAYER --
des.monster({ id = "watchman", x = 20, y = 08, peaceful = true })
des.monster({ id = "high cleric", x = 70, y = 08, peaceful = true })
des.monster({ id = "lieutenant", x = 24, y = 09, peaceful = true })
des.monster({ id = "watch captain", x = 28, y = 09, peaceful = true })
des.monster({ id = "high cleric", x = 55, y = 09, peaceful = true })
des.monster({ id = "watchman", x = 20, y = 12, peaceful = true })
des.monster({ id = "watchman", x = 58, y = 12, peaceful = true })
des.monster({ id = "watchman", x = 66, y = 12, peaceful = true })
des.monster({ id = "high cleric", x = 55, y = 13, peaceful = true })
des.monster({ id = "high cleric", x = 70, y = 15, peaceful = true })





-- Gold and minor objects scattered
des.gold({ amount = math.random(4000,8000), x=71, y=6 })
-- OBJECT LAYER --
des.object({ id = "chest", x = 01, y = 00, locked = 1, contents = function()
   des.object({ id = "verse of spiritual armor", buc = "blessed", quantity = 10 })
end})
des.object({ id = "verse of former things forgotten", x = 29, y = 04, buc = "blessed" })
des.object({ id = "verse of light", x = 31, y = 04, buc = "blessed" })
des.object({ id = "verse of discernment", x = 33, y = 04, buc = "blessed" })
des.object({ id = "verse of render unto caesar", x = 36, y = 04, buc = "blessed" })
des.object({ id = "verse of subdue beast", x = 38, y = 04, buc = "blessed" })
des.object({ id = "verse of dove wings", x = 40, y = 04, buc = "blessed" })
des.object({ id = "verse of reveal mana", x = 42, y = 04, buc = "blessed" })
des.object({ id = "verse of blank paper", x = 44, y = 04, buc = "blessed" })
des.object({ id = "verse of blank paper", x = 29, y = 06, buc = "blessed" })
des.object({ id = "verse of blank paper", x = 46, y = 06, buc = "blessed" })
des.object({ id = "prophetic book of resist evil", x = 32, y = 12, buc = "blessed" })
des.object({ id = "prophetic book of fiery tempest", x = 35, y = 12, buc = "blessed" })
des.object({ id = "prophetic book of banishment", x = 45, y = 12, buc = "blessed" })
des.object({ id = "prophetic book of angelic help", x = 48, y = 12, buc = "blessed" })
des.object({ id = "prophetic book of door shall be open", x = 32, y = 15, buc = "blessed" })
des.object({ id = "prophetic book of angelic help", x = 35, y = 15, buc = "blessed" })
des.object({ id = "prophetic book of quickening", x = 45, y = 15, buc = "blessed" })
des.object({ id = "prophetic book of render unto caesar", x = 48, y = 15, buc = "blessed" })
des.object({ id = "gold piece", x = 55, y = 06, quantity = math.random(500,1200) })
des.object({ id = "gold piece", x = 59, y = 06, quantity = math.random(500,1200) })
des.object({ id = "gold piece", x = 63, y = 06, quantity = math.random(500,1200) })
des.object({ id = "gold piece", x = 67, y = 06, quantity = math.random(500,1200) })
des.object({ id = "gold piece", x = 71, y = 06, quantity = math.random(500,1200) })

des.stair("down", 1,1)