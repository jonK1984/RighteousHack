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

function getFeatureBrushByName(name) {
    return allFeatures.find(feature => feature.name === name);
}

function getFeatureDefByType(type) {
    
    //return allFeatureMenuOptions.find(feature => feature.internal.type === type);
    const featureArray = Object.values(allFeatureMenuOptions);
    const featLen = featureArray.length;
    return featureArray.slice(1, featLen).find(
        feature => feature.internal.type === type
        );
}

function getTrapTypeByName(name) {
    return trapTypes.find(trap => trap.name === name);
}

/**
 * Configure the internal display properties of a trap brush.
 * @param {Object} brush - The brush object to configure.
 * @returns {boolean} true if the trap type was found and internals were set,
 *                    false otherwise (type missing, not found, etc.).
 */
function setTrapInternals(brush) {
    // Basic validation
    if (!brush || typeof brush !== "object") return false;
    if (!brush.internal || typeof brush.internal !== "object") return false;
    if (typeof brush.type !== "string") return false;

    // Find the matching trap definition
    const trapDef = trapTypes.find(t => t.type === brush.type);

    if (!trapDef) {
        // No matching trap type found
        return false;
    }

    // Apply the symbol and color from the definition
    brush.internal.symbol = trapDef.sym;
    brush.internal.color  = trapDef.color;

    return true;
}

/**
 * Configure the internal display properties of a feature brush.
 * @param {Object} brush - The brush object to configure.
 * @returns {boolean} true if the feature type was found and internals were set,
 *                    false otherwise (type missing, not found, etc.).
 */
function setFeatureInternals(brush) {
    // Basic validation
    if (!brush || typeof brush !== "object") return false;
    if (!brush.internal || typeof brush.internal !== "object") return false;
    if (typeof brush.type !== "string") return false;

    // Find the matching feature definition
    const featDef = featureDef.find(f => f.type === brush.type);

    if (!featDef) {
        // No matching feature type found
        return false;
    }

    // Apply the symbol and color from the definition
    brush.internal.symbol = featDef.sym;
    brush.internal.color  = featDef.color;

    return true;
}

/**
 * Get formatted info for a feature brush (for UI display, tooltips, etc.)
 * Handles concrete traps/features, random, and unknown cases.
 *
 * @param {Object|null} brush - The feature brush (or null/undefined)
 * @returns {Object}
 */
function getFeatureInfo(brush) {
    if (!brush) {
        return {
            symbol: 'Ø',
            type: 'unknown',
            description: 'Invalid Feature',
            color: 'CLR_WHITE',
            options: null
        };
    }

    const info = {
        symbol: brush.sym || brush.internal?.symbol || '?',
        type: 'feature',
        description: brush.name || 'Unnamed Feature',
        color: brush.color || brush.internal?.color || 'CLR_WHITE',
        options: null
    };

    // Trap detection
    if (brush.trapType !== undefined) {
        info.type = 'trap';
        const t = trapTypes.find(tt => tt.type === brush.trapType);
        if (t) {
            info.symbol = t.sym;
            info.color = t.color;
            info.description = t.name;
        } else {
            info.description = `Unknown Trap (${brush.trapType})`;
        }

        info.options = info.options || [];
    }

    // General .options (if present on brush)
    if (brush.options && typeof brush.options === 'object') {
        info.options = info.options || [];
        for (const key in brush.options) {
            if (brush.options.hasOwnProperty(key)) {
                const val = brush.options[key];
                info.options.push(`${key}: ${val}`);
            }
        }
    }

    // Random/unknown overrides
    if (brush.internal?.random) {
        info.description = 'Random Feature';
        if (info.type === 'trap') {
            info.description = 'Random Trap';
        }
    }

    return info;
}


allFeatureMenuOptions = {
        tabs: [
            { desc: "Altar",          key: "altar" },
            { desc: "Door",           key: "door" },
            { desc: "Drawbridge",     key: "drawbridge" },
            { desc: "Engraving",      key: "engraving" },    
            { desc: "Grave",          key: "grave" },
            { desc: "Stair",          key: "stair" },
            { desc: "Ladder",         key: "ladder" },
            { desc: "Region",         key: "region" },
            { desc: "Trap",           key: "trap" },
            { desc: "Feature",        key: "feature" },
            { desc: "Gold",           key: "gold" },
            { desc: "Message",        key: "message" },
            { desc: "Mineralize",     key: "mineralize" },
            { desc: "Reset Level",    key: "reset_level" },
            { desc: "Finalize Level", key: "finalize_level" },
            { desc: "Teleport Region", key: "teleport_region" },
            { desc: "Non-Diggable Region", key: "non_diggable" }
        ],

        // ───── Point-placeable features (is_xy_possible: true) ─────

        altar: {
            align: {
                label: "Altar alignment",
                input_type: "combo",
                data_type: "string",
                combo_options: ["noalign", "law", "neutral", "chaos", "coaligned", "noncoaligned", "random"],
                desc: "Altar alignment"
            },
            type: {
                label: "Altar type",
                input_type: "combo",
                data_type: "string",
                combo_options: ["altar", "shrine", "sanctum"],
                desc: "Altar type"
            },
            internal: {
                lua: null,
                des_code: "des.altar",
                type: "altar",
                color: "CLR_GRAY",
                symbol: "_",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        door: {
            state: {
                label: "State of door",
                input_type: "combo",
                data_type: "string",
                combo_options: ["random", "open", "closed", "locked", "nodoor", "broken", "secret"],
                desc: "State of door"
            },
            wall: {
                label: "Wall direction",
                input_type: "combo",
                data_type: "string",
                combo_options: ["all", "random", "north", "west", "east", "south"],
                desc: "Wall direction"
            },
            pos: {
                label: "Door position (secret doors only)",
                input_type: "combo",
                data_type: "int",
                combo_options: [0, 1, 2, 3],
                desc: "Door position"
            },
            internal: {
                lua: null,
                des_code: "des.door",
                type: "door",
                color: "CLR_BROWN",
                symbol: "+",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: false
            }
        },

        drawbridge: {
            dir: {
                label: "Direction",
                input_type: "combo",
                data_type: "string",
                combo_options: ["north", "east", "south", "west"],
                desc: "Drawbridge direction"
            },
            state: {
                label: "Initial state",
                input_type: "combo",
                data_type: "string",
                combo_options: ["open", "closed"],
                desc: "Drawbridge state"
            },
            internal: {
                lua: null,
                des_code: "des.drawbridge",
                type: "drawbridge",
                color: "CLR_BROWN",
                symbol: "#",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        engraving: {
            type: {
                label: "Engraving type",
                input_type: "combo",
                data_type: "string",
                combo_options: ["dust", "engrave", "burn", "random"],
                desc: "Engraving type"
            },
            text: {
                label: "Engraving text",
                input_type: "text",
                data_type: "string",
                desc: "Engraving text (optional if random)"
            },
            internal: {
                lua: null,
                des_code: "des.engraving",
                type: "engraving",
                color: "CLR_BRIGHT_BLUE",
                symbol: "ε",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        region: {
            type: {
                label: "Region type",
                input_type: "combo",
                data_type: "string",
                combo_options: ["ordinary","themed","throne","swamp","vault","beehive","morgue","barracks","zoo","delphi","temple","anthole","cocknest","leprehall","shop","armor shop","scroll shop","potion shop","weapon shop","food shop","ring shop","rod shop","tool shop","book shop","health food shop","candle shop"],
                desc: "Region type"
            },
            chance: {
                label: "Probability of room generation",
                input_type: "text",
                data_type: "int",
                desc: "Probability of room generation"
            },
            lit: {
                label: "Room lighting",
                input_type: "combo",
                data_type: "int",
                combo_options: ["0","1"],
                desc: "Room lighting"
            },
            xalign: {
                label: "X-Align",
                input_type: "combo",
                data_type: "string",
                combo_options: ["left", "half-left", "center", "half-right", "right", "none", "random"],
                desc: "Room alignment accross the X-axis"
            },
            yalign: {
                label: "Y-Align",
                input_type: "combo",
                data_type: "string",
                combo_options: ["top", "center", "bottom", "none", "random"],
                desc: "Room alignment accross the Y-axis"
            },
            filled:     { label: "Filled",          input_type: "combo", data_type: "int", combo_options: ["0","1"], desc: "Room is Filleds" },
            joined:      { label: "Joined",         input_type: "combo", data_type: "bool", combo_options: ["true","false"], desc: "Room is Joined to Something" },
            internal: {
                lua: null,
                des_code: "des.region",
                type: "region",
                color: "CLR_ORANGE",
                dither: "crosshatch",        // distinct pattern
                ditherColor: "CLR_GREEN",
                symbol: null,
                random: false,
                brushMode: "complex",
                stroke: "rectangle",
                is_xy_possible: true,
                is_rnd_possible: false
            }
            
        },

        grave: {
            text: {
                label: "Epitaph text (optional)",
                input_type: "text",
                data_type: "string",
                desc: "Text on grave"
            },
            internal: {
                lua: null,
                des_code: "des.grave",
                type: "grave",
                color: "CLR_GRAY",
                symbol: "`",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },


        stair: {
            dir: {
                label: "Direction",
                input_type: "combo",
                data_type: "string",
                combo_options: ["up", "down"],
                desc: "Up or down stair"
            },
            internal: {
                lua: null,
                des_code: "des.stair",
                type: "stair",
                color: "CLR_GRAY",
                symbol: "<",
                random: false,
                brushMode: "simple",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        ladder: {
            dir: {
                label: "Direction",
                input_type: "combo",
                data_type: "string",
                combo_options: ["up", "down"],
                desc: "Up or down ladder"
            },
            internal: {
                lua: null,
                des_code: "des.ladder",
                type: "ladder",
                color: "CLR_GRAY",
                symbol: "<",
                random: false,
                brushMode: "simple",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },
        trap: {
            type: {
                label: "Trap type",
                input_type: "combo",
                data_type: "string",
                combo_options: [
                    "random",
                    "arrow",
                    "dart",
                    "falling rock",
                    "squeaky board",
                    "bear",
                    "land mine",
                    "rolling boulder",
                    "sleeping gas",
                    "rust",
                    "fire",
                    "pit",
                    "spiked pit",
                    "hole",
                    "trap door",
                    "teleport",
                    "level teleport",
                    "magic",
                    "anti-magic",
                    "polymorph",
                    "web",
                    "statue",
                    "magic portal",
                    "vibrating square"
                ],
                desc: "Trap type"
            },
            internal: {
                lua: null,
                des_code: "des.trap",
                type: "trap",
                color: "CLR_RED",
                symbol: "^",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        feature: {
            type: {
                label: "Feature type",
                input_type: "combo",
                data_type: "string",
                combo_options: ["fountain", "sink", "pool", "throne", "tree"]
            },
            internal: {
                lua: null,
                des_code: "des.feature",
                type: "feature",
                color: "CLR_RED",
                symbol: "#",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        gold: {
            amount: {
                label: "Gold amount",
                input_type: "text",
                data_type: "string",
                desc: "Amount: number, dice (e.g. 10d20), or 'random'"
            },
            internal: {
                lua: null,
                des_code: "des.gold",
                type: "gold",
                color: "CLR_YELLOW",
                symbol: "$",
                random: false,
                brushMode: "complex",
                stroke: "point",
                is_xy_possible: true,
                is_rnd_possible: true
            }
        },

        // ───── Level-wide / non-spatial commands (is_xy_possible: false) ─────

        message: {
            text: {
                label: "Message text",
                input_type: "text",
                data_type: "string",
                desc: "Level message shown when hero enters"
            },
            internal: {
                lua: null,
                des_code: "des.message",
                type: "message",
                color: null,
                symbol: null,
                random: false,
                brushMode: "level",
                stroke: null,
                is_xy_possible: false,
                is_rnd_possible: true
            }
        },

        mineralize: {
            gold_prob: {
                label: "Fill with gold",
                input_type: "combo",
                data_type: "int",
                combo_options: [-1, 0, 25, 50, 75, 100],
                desc: "Replace some stone with gold veins"
            },
            gem_prob: {
                label: "Fill with gems",
                input_type: "combo",
                data_type: "int",
                combo_options: [-1, 0, 25, 50, 75, 100],
                desc: "Replace some stone with gems"
            },
            kelp_moat: {
                label: "Fill with kelp (moat, etc.)",
                input_type: "combo",
                data_type: "int",
                combo_options:  [-1, 0, 25, 50, 75, 100],
                desc: "Other kelp replacements"
            },
            kelp_pool: {
                label: "Fill with kelp (pool, etc.)",
                input_type: "combo",
                data_type: "int",
                combo_options:  [-1, 0, 25, 50, 75, 100],
                desc: "Other kelp replacements"
            },

            internal: {
                lua: null,
                des_code: "des.mineralize",
                type: "mineralize",
                color: null,
                symbol: null,
                random: false,
                brushMode: "level",
                stroke: null,
                is_xy_possible: false,
                is_rnd_possible: true
            }
        },

        reset_level: {
            internal: {
                lua: null,
                des_code: "des.reset_level",
                type: "reset_level",
                color: null,
                symbol: null,
                random: false,
                brushMode: "level",
                stroke: null,
                is_xy_possible: false,
                is_rnd_possible: false
            }
        },

        finalize_level: {
            internal: {
                lua: null,
                des_code: "des.finalize_level",
                type: "finalize_level",
                color: null,
                symbol: null,
                random: false,
                brushMode: "level",
                stroke: null,
                is_xy_possible: false,
                is_rnd_possible: false
            }
        },

        teleport_region: {
            region_islev: {
                label: "Region Is Level",
                input_type: "combo",
                data_type: "int",
                combo_options: ["0", "1"],
                desc: "Region Is Level"
            },
            exclude_islev: {
                label: "Excluded Region Is Level",
                input_type: "combo",
                data_type: "int",
                combo_options: ["0", "1"],
                desc: "Excluded Region Is Level"
            },
            dir: {
                label: "Direction",
                input_type: "combo",
                data_type: "string",
                combo_options: ["up", "down"],
                desc: "Up or down"
            },
            internal: {
                lua: null,
                des_code: "des.teleport_region",
                type: "teleport_region",
                color: "CLR_YELLOW",
                dither: "sparse-dots",        // distinct pattern
                ditherColor: "CLR_YELLOW",
                symbol: null,
                random: false,
                brushMode: "complex",
                stroke: "rectangle",
                is_xy_possible: true,
                is_rnd_possible: false
            }
        },

        non_diggable: {
            
            internal: {
                lua: null,
                des_code: "des.non_diggable",
                type: "non_diggable",
                color: "CLR_ORANGE",
                dither: "horizontal-dash",        // distinct pattern
                ditherColor: "CLR_MAGENTA",
                symbol: null,
                random: false,
                brushMode: "simple",
                stroke: "rectangle",
                is_xy_possible: true,
                is_rnd_possible: false
            }
        },
    }

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
        internal: { type: 'feature'},
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
        internal: { type: 'feature'},
        options: {
            state: ["secret", "closed", "locked", "open"]
        },
        lua: (f) => `des.door({ coord = { ${f.x},${f.y} }, state = "${f.options.state}" });`
    },
    {
        name: "Drawbridge",
        stroke: "point",
        symbol: "#",
        color: "CLR_BROWN",
        internal: { type: 'feature'},
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
        internal: { type: 'feature'},
        options: { text: "" },
        lua: (f) => `des.engraving({ type="engrave", x=${f.x}, y=${f.y}, text="${f.text}" })`
    },
    {
        name: "Ladder Down",
        stroke: "point",
        symbol: ">",
        color: "CLR_GRAY",
        internal: { type: 'feature'},
        lua: (f) => `des.ladder("down", ${f.x},${f.y})`
    },
    {
        name: "Ladder Up",
        stroke: "point",
        symbol: "<",
        color: "CLR_GRAY",
        internal: { type: 'feature'},
        lua: (f) => `des.ladder("up", ${f.x},${f.y})`
    },
    {
        name: "Level Region",
        stroke: "rectangle",
        dither: "horizontal-dash",   // distinct pattern
        ditherColor: "CLR_MAGENTA",
        internal: { type: 'feature'},
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
        internal: { type: 'feature'},
        lua: (f) => `des.mazewalk(${f.area.split(',').slice(0,2).join(',')},"${f.dir}")`
    },
    {
        name: "Non-Diggable Region",
        stroke: "rectangle",
        dither: "dense-dots",
        ditherColor: "CLR_BROWN",
        internal: { type: 'feature'},
        lua: (f) => `des.non_diggable(selection.area(${f.area}))`
    },
    {
        name: "Room",
        stroke: "rectangle",
        dither: "crosshatch",        // distinct pattern
        ditherColor: "CLR_GREEN",
        internal: { type: 'feature'},
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
        internal: { type: 'feature'},
        lua: (f) => `des.stair("down", ${f.x},${f.y})`
    },
    {
        name: "Stairs Up",
        stroke: "point",
        symbol: "<",
        color: "CLR_GRAY",
        internal: { type: 'feature'},
        lua: (f) => `des.stair("up", ${f.x},${f.y})`
    },
    {
        name: "Tree",
        stroke: "point",
        symbol: "#",
        color: "CLR_GREEN",
        internal: { type: 'feature'},
        lua: (f) => `des.feature("tree", ${f.x},${f.y})`
    },
    {
        name: "Fountain",
        stroke: "point",
        symbol: "{",
        color: "CLR_BRIGHT_BLUE",
        internal: { type: 'feature'},
        lua: (f) => `des.feature("fountain", ${f.x},${f.y})`
    },
    {
        name: "Sink",
        stroke: "point",
        symbol: "{",
        color: "CLR_WHITE",
        internal: { type: 'feature'},
        lua: (f) => `des.feature("sink", ${f.x},${f.y})`
    },
    {
        name: "Teleport Region",
        stroke: "rectangle",
        dither: "diagonal",          // distinct pattern
        ditherColor: "CLR_YELLOW",
        internal: { type: 'feature'},
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
        internal: { type: 'feature'},
        trapList: true,              // flag for special handling
        lua: (f) => `des.trap(${
            [
            f.trapType ? `"${f.trapType}"` : '',
            f.x !== undefined && f.y !== undefined ? `${f.x},${f.y}` : ''
            ]
            .filter(Boolean)
            .join(', ')
        })`
        
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

const featureDef = [
    { name: "fountain",  type: "fountain",  sym: "{",  color: "CLR_BRIGHT_CYAN" },
    { name: "sink",      type: "sink",      sym: "}",  color: "CLR_GRAY" },
    { name: "pool",      type: "pool",      sym: "}",  color: "CLR_BLUE" },
    { name: "throne",    type: "throne",    sym: "\\", color: "CLR_YELLOW" },
    { name: "tree",      type: "tree",      sym: "#",  color: "CLR_GREEN" }
];