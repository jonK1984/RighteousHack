const allLVLFlags = [
    { flag: "noteleport",   desc: "Prevents teleporting" },
    { flag: "hardfloor",    desc: "Prevents digging down" },
    { flag: "nommap",       desc: "Prevents magic mapping" },
    { flag: "shortsighted", desc: "Prevents monsters from seeing the hero from far away" },
    { flag: "arboreal",     desc: "Notionally an outdoor map; replaces solid stone with trees" },
    { flag: "mazelevel",    desc: "" },
    { flag: "shroud",       desc: "Unseen locations are not remembered (blank instead of dark glyphs)" },
    { flag: "graveyard",    desc: "Treats the level as a graveyard (sounds, undead corpse chance)" },
    { flag: "icedpools",    desc: "Ice becomes frozen pools instead of moats" },
    { flag: "corrmaze",     desc: "" },
    { flag: "premapped",    desc: "Map, traps and boulders revealed on entrance" },
    { flag: "sokoban",      desc: "Level has special Sokoban rules" },
    { flag: "solidify",     desc: "Areas outside the map are undiggable/unphaseable" },
    { flag: "inaccessibles",desc: "Connect generated inaccessible areas to the accessible part" },
    { flag: "noflip",       desc: "Prevent flipping the level" },
    { flag: "noflipx",      desc: "Prevent horizontal flipping" },
    { flag: "noflipy",      desc: "Prevent vertical flipping" },
    { flag: "nomongen",     desc: "Prevents random monster generation" },
    { flag: "nodeathdrops", desc: "Monsters do not drop corpses or random death drops" },
    { flag: "fumaroles",    desc: "Lava emits poison gas clouds" },
    { flag: "stormy",       desc: "Clouds create random lightning bolts" }
    // hot / cold / temperate are handled separately with radios
];

const allFeatures = [
    {
        name: "Eraser",
        stroke: "point",
        isEraser: true,               // simple flag so we can detect it everywhere
        // no symbol, color, options, or lua needed
    },
    {
        name: "Altar",
        stroke: "point",
        symbol: "_",
        color: "CLR_GRAY",
        options: {
            type: ["altar", "shrine", "sanctum"],
            align: ["1", "2", "3"]
        },
        lua: (f) => `des.altar({ x=${f.x}, y=${f.y}, align=align[${f.align}], type="${f.type}" })`
    },
    {
        name: "Door",
        stroke: "point",
        symbol: "+",
        color: "CLR_BROWN",
        options: {
            state: ["secret", "closed", "locked", "open"]
        },
        lua: (f) => `des.door({ coord = { ${f.x},${f.y} }, state = "${f.state}" });`
    },
    {
        name: "Drawbridge",
        stroke: "point",
        symbol: "#",
        color: "CLR_BROWN",
        options: {
            dir: ["north", "south", "east", "west"],
            state: ["random", "open", "closed"]
        },
        lua: (f) => `des.drawbridge({ x=${f.x}, y=${f.y}, dir="${f.dir}", state="${f.state}" })`
    },
    {
        name: "Engraving",
        stroke: "point",
        symbol: "ε",
        color: "CLR_BRIGHT_BLUE",
        options: { text: "" },
        lua: (f) => `des.engraving({ type="engrave", x=${f.x}, y=${f.y}, text="${f.text}" })`
    },
    {
        name: "Ladder Down",
        stroke: "point",
        symbol: ">",
        color: "CLR_GRAY",
        lua: (f) => `des.ladder("down", ${f.x},${f.y})`
    },
    {
        name: "Ladder Up",
        stroke: "point",
        symbol: "<",
        color: "CLR_GRAY",
        lua: (f) => `des.ladder("up", ${f.x},${f.y})`
    },
    {
        name: "Level Region",
        stroke: "rectangle",
        dither: "horizontal-dash",   // distinct pattern
        ditherColor: "CLR_MAGENTA",
        options: {
            type: ["stair-up", "stair-down", "branch", "portal"],
            name: "",
            region_islev: false,
            exclude: "",
            exclude_islev: false,
            wholeMap: false
        },
        lua: (f) => {
            let parts = [`region = {${f.area}}`];
            if (f.region_islev) parts.push("region_islev=1");
            if (f.type) parts.push(`type="${f.type}"`);
            if (f.name) parts.push(`name="${f.name}"`);
            if (f.exclude) parts.push(`exclude={${f.exclude}}`);
            if (f.exclude_islev) parts.push("exclude_islev=1");
            return `des.levregion({ ${parts.join(", ")} })`;
        }
    },
    {
        name: "Mazewalk",
        stroke: "rectangle",
        dither: "sparse-dots",       // distinct from others
        ditherColor: "CLR_BLUE",
        options: { dir: ["north", "south", "east", "west"] },
        lua: (f) => `des.mazewalk(${f.area.split(',').slice(0,2).join(',')},"${f.dir}")`
    },
    {
        name: "Non-Diggable Region",
        stroke: "rectangle",
        dither: "dense-dots",
        ditherColor: "CLR_BROWN",
        lua: (f) => `des.non_diggable(selection.area(${f.area}))`
    },
    {
        name: "Room",
        stroke: "rectangle",
        dither: "crosshatch",        // distinct pattern
        ditherColor: "CLR_GREEN",
        options: {
            type: ["ordinary","themed","throne","swamp","vault","beehive","morgue","barracks","zoo","delphi","temple","anthole","cocknest","leprehall","shop","armor shop","scroll shop","potion shop","weapon shop","food shop","ring shop","rod shop","tool shop","book shop","health food shop","candle shop"],
            lit: ["lit","unlit"],
            contents: ""
        },
        lua: (f) => {
            let parts = [`type="${f.type}"`, `lit=${f.lit === "lit" ? 1 : 0}`, `x=${f.area.split(',')[0]},y=${f.area.split(',')[1]}, w=${f.w},h=${f.h}`];
            if (f.contents) parts.push(`contents = function()\n${f.contents}\nend`);
            return `des.room({ ${parts.join(", ")} })`;
        }
    },
    {
        name: "Stairs Down",
        stroke: "point",
        symbol: ">",
        color: "CLR_GRAY",
        lua: (f) => `des.stair("down", ${f.x},${f.y})`
    },
    {
        name: "Stairs Up",
        stroke: "point",
        symbol: "<",
        color: "CLR_GRAY",
        lua: (f) => `des.stair("up", ${f.x},${f.y})`
    },
    {
        name: "Teleport Region",
        stroke: "rectangle",
        dither: "diagonal",          // distinct pattern
        ditherColor: "CLR_YELLOW",
        options: {
            region_islev: false,
            exclude: "",
            exclude_islev: false
        },
        lua: (f) => {
            let parts = [`region = {${f.area}}`];
            if (f.region_islev) parts.push("region_islev=1");
            if (f.exclude) parts.push(`exclude={${f.exclude}}`);
            if (f.exclude_islev) parts.push("exclude_islev=1");
            return `des.teleport_region({ ${parts.join(", ")} })`;
        }
    },
    {
        name: "Trap",
        stroke: "point",
        trapList: true,              // flag for special handling
        lua: (f) => `des.trap("${f.trapType}",${f.x},${f.y})`
    }
];

const trapTypes = [
    { name: "arrow",             type: "arrow",             sym: "^", color: "HI_METAL" },
    { name: "dart",              type: "dart",              sym: "^", color: "HI_METAL" },
    { name: "falling rock",      type: "falling rock",      sym: "^", color: "CLR_GRAY" },
    { name: "board",             type: "board",             sym: "^", color: "CLR_BROWN" },
    { name: "bear",              type: "bear",              sym: "^", color: "HI_METAL" },
    { name: "land mine",         type: "land mine",         sym: "^", color: "CLR_RED" },
    { name: "rolling boulder",   type: "rolling boulder",   sym: "^", color: "CLR_GRAY" },
    { name: "sleep gas",         type: "sleep gas",         sym: "^", color: "HI_ZAP" },
    { name: "rust",              type: "rust",              sym: "^", color: "CLR_BLUE" },
    { name: "fire",              type: "fire",              sym: "^", color: "CLR_ORANGE" },
    { name: "pit",               type: "pit",               sym: "^", color: "CLR_BLACK" },
    { name: "spiked pit",        type: "spiked pit",        sym: "^", color: "CLR_BLACK" },
    { name: "hole",              type: "hole",              sym: "^", color: "CLR_BROWN" },
    { name: "trap door",         type: "trap door",         sym: "^", color: "CLR_BROWN" },
    { name: "teleport",          type: "teleport",          sym: "^", color: "CLR_MAGENTA" },
    { name: "level teleport",    type: "level teleport",    sym: "^", color: "CLR_MAGENTA" },
    { name: "magic portal",      type: "magic portal",      sym: "^", color: "CLR_BRIGHT_MAGENTA" },
    { name: "web",               type: "web",               sym: "\"", color: "CLR_GRAY" },
    { name: "statue",            type: "statue",            sym: "^", color: "CLR_GRAY" },
    { name: "magic",             type: "magic",             sym: "^", color: "HI_ZAP" },
    { name: "anti magic",        type: "anti magic",        sym: "^", color: "HI_ZAP" },
    { name: "polymorph",         type: "polymorph",         sym: "^", color: "CLR_BRIGHT_GREEN" },
    { name: "vibrating square",  type: "vibrating square",  sym: "~", color: "CLR_MAGENTA" },
    { name: "random",            type: "random",            sym: "^", color: "CLR_WHITE" }
];