-- NetHack Royal Historian His-home.lua
-- The Great Library of Alexandria - Main Hall (Quest Home Level)
-- Royal Historian quest home level for RighteousHack.
-- The player arrives via the quest portal on a dock outside the library.
-- The building is surrounded by water (Nile harbor influence).
-- Inside: grand hall with columns, bookshelves filled with prophetic books,
-- a few trees/plants, the quest leader (Zenodotus), guardians, and stairs
-- up to the spire and down to the basement.

des.level_flags("noteleport", "hardfloor", "solidify")

des.level_init({ style = "solidfill", fg = " " })


-- Overall map: water around a central island/building with dock
--map size must be 76x20
des.map([[
|--------------------------------------------------------------------------|
|..........................|........................|......................|
|..........................|........................|......................|
|........LLLLL.............|........................|......................|
|........LLLLL.............|........................|......................|
|........LLLLL.............|........................|.........LLLLL........|
|........LLLLL.............|........LLLLLLL.........|.........LLLLL........|
|........LLLLL.............|........LLLLLLL.........|.........LLLLL........|
|........LLLLL.............|........LLLLLLL.........|.........LLLLL........|
|........LLLLL.............|........LLLLLLL.........|.........LLLLL........|
|..........................|........LLLLLLL.........|.........LLLLL........|
|..........................|........LLLLLLL.........|.........LLLLL........|
|..........................|........................|......................|
|..........................|........................|......................|
|..........................|........................|......................|
|..........................|........................|......................|
|..........................|........................|......................|
|..........................|........................|......................|
|..........................|........................|......................|
|--------------------------------------------------------------------------|
]]);

-- Outer area becomes water (harbor around the library island)
--des.replace_terrain({ region = {00,00,75,19}, fromterrain = ".", toterrain = "W" })

-- Library interior: lit stone floor
--des.region({ region = {21,03,66,18}, lit = 1, type = "ordinary" })

-- Dungeon Description
des.region(selection.area(00,00,49,15), "lit")
des.region(selection.area(04,04,45,11), "unlit")
des.region({ region={06,06,22,09}, lit=1, type="throne", filled=2 })
des.region(selection.area(27,06,43,09), "lit")
-- Portal arrival point
des.levregion({ region = {20,14,20,14}, type="branch" })

-- Wooden dock extending north into the water
--des.terrain({ region = {37,02,40,02}, typ = "-" })  -- dock planks

-- Main entrance door (north side)
des.door("open", 38, 04)

-- Quest portal / arrival point on the dock
des.stair("up", 38, 02)

-- Grand marble columns inside the hall

-- Decorative trees for scholarly garden atmosphere
des.feature("tree", 25, 06)
des.feature("tree", 25, 13)
des.feature("tree", 62, 06)
des.feature("tree", 62, 13)
des.feature("tree", 43, 10)

-- Bookshelves along the walls (non-diggable walls with objects)
--des.non_diggable({ region = {23,04,69,21} })

-- Place prophetic books on shelves (randomly scattered inside)


-- Quest leader: Zenodotus, the Chief Librarian (peaceful human)
des.monster({
    id = "Zenodotus",
    x = 46, y = 12,
    peaceful = true,
    historic = true,
    female = false
})

-- Quest guardians: peaceful scholars/librarians (human archeologists/priests analog)
des.monster({ class = "@", peaceful = true, x=40, y=10 })
des.monster({ class = "@", peaceful = true, x=42, y=14 })
des.monster({ class = "@", peaceful = true, x=50, y=10 })
des.monster({ class = "@", peaceful = true, x=52, y=14 })
des.monster({ class = "@", peaceful = true, x=48, y=18 })

-- Stairs up to the Spire (next quest level)
des.stair("up", 60, 12)

-- Stairs down to the Basement (lower quest level)
des.stair("down", 32, 12)



-- A few minor hostile creatures lurking (thieves or vandals)

des.monster("hill orc", 67, 15)

-- Gold and minor objects scattered
des.gold({ amount = math.random(200,500), x=45, y=18 })
des.object({ class = "%", x=48, y=15 })  -- food for atmosphere