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
des.map([[
............................................................................
............................................................................
............................................................................
.....................-----------------------------------------------........
.....................|.............................................|........
.....................|.............................................|........
.....................|...............wwwwwwwwwwwwwww...............|........
.....................|.............ww-----------------ww...........|........
.....................|............w---|...............|---w.........|........
.....................|...........w----|.................|----w.......|........
.....................|..........w-----|...................|-----w.....|........
.....................|.........w------|---------------------|------w....|........
.....................|........w-------|.....................|-------w...|........
.....................|.......w--------|.....................|--------w..|........
.....................|......w---------|.....................|---------w.|........
.....................|.....w----------|-----------------------|---------w|........
.....................|....w-----------|.......................|----------|........
.....................|...w------------|.......................|----------|........
.....................|..w-------------|-------------------------|--------|........
.....................|ww--------------|---------------------------|------|........
.....................|w---------------------------------------------|------|........
.....................|-----------------------------------------------|........
.....................----------------------------------------------------....
............................................................................
............................................................................
]]);

-- Fill the outer area with water
des.replace_terrain({ region = {00,00,75,25}, fromterrain = ".", toterrain = "W" })

-- Building interior: stone floor
des.region({ region = {22,03,70,22}, lit = 1, type = "ordinary", irregular = true })

-- Dock (arrival point) - wooden pier extending into water
des.terrain({ x=30, y=04, typ = "-" })  -- bridge-like dock
des.terrain({ x=31, y=04, typ = "-" })
des.terrain({ x=32, y=04, typ = "-" })
des.terrain({ x=33, y=04, typ = "-" })

-- Entrance door to the library
des.door("open", 33, 05)

-- Quest portal location (player arrives here)
des.stair("up", 32, 04)  -- treated as portal in quest setup

-- Grand columns inside the hall (stone pillars)
local columns = {
    {35,08}, {35,15}, {45,08}, {45,15},
    {55,08}, {55,15}, {65,08}, {65,15}
}
for _, col in ipairs(columns) do
    des.terrain(col[1], col[2], "|")  -- vertical pillar
end

-- Trees/plants for atmosphere
des.feature("tree", 28, 10)
des.feature("tree", 28, 18)
des.feature("tree", 68, 10)
des.feature("tree", 68, 18)

-- Bookshelves along the walls (non-diggable walls with objects)
des.non_diggable({ region = {23,04,69,21} })

-- Place prophetic books on shelves (randomly scattered inside)
for i = 1, 30 do
    local x = math.random(25, 68)
    local y = math.random(06, 20)
    des.object("prophetic book of move mountains", x, y)  -- in RighteousHack, scrolls can be themed as prophetic writings
end

-- Quest leader: Zenodotus, the Chief Librarian (peaceful human)
des.monster({
    id = "Zenodotus",
    x = 46, y = 12,
    peaceful = true,
    historic = true,
    female = false,
    name = "Zenodotus"
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

-- Some random traps and minor monsters for flavor (guarding knowledge)
des.trap("spiked pit", 38, 12)
des.trap("dart", 50, 16)
des.trap("magic", 58, 10)

-- A few minor hostile creatures lurking (thieves or vandals)
des.monster("thief", 25, 08)
des.monster("hill orc", 67, 15)

-- Gold and minor objects scattered
des.gold({ amount = math.random(200,500), x=45, y=18 })
des.object({ class = "%", x=48, y=15 })  -- food for atmosphere