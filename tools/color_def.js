// Dictionary that maps room type strings to a NetHack color constant from colorTable
const roomDitherColors = {
    "ordinary":          "CLR_GRAY",          // standard stone/dungeon room
    "themed":            "CLR_BROWN",         // generic themed rooms
    "throne":            "CLR_YELLOW",        // royal/gold feel
    "swamp":             "CLR_GREEN",         // marshy
    "vault":             "CLR_GRAY",          // stone vault
    "beehive":           "CLR_YELLOW",        // honey-themed
    "morgue":            "CLR_BLACK",         // dark/deathly
    "barracks":          "CLR_RED",           // military
    "zoo":               "CLR_GREEN",         // animals/nature
    "delphi":            "CLR_CYAN",          // oracular/watery
    "temple":            "CLR_WHITE",         // holy/bright (fits RighteousHack theme)
    "anthole":           "CLR_BROWN",         // earth/dirt
    "cocknest":          "CLR_RED",           // dangerous creature nest
    "leprehall":         "CLR_GREEN",         // classic leprechaun green
    "shop":              "CLR_CYAN",          // generic shop tint

    // specific shop types
    "armor shop":        "HI_METAL",          // metallic
    "scroll shop":       "HI_PAPER",          // parchment/white
    "potion shop":       "CLR_BLUE",          // classic potion color (anointing oil in RighteousHack)
    "weapon shop":       "HI_METAL",          // weapons are metal
    "food shop":         "CLR_BROWN",         // food/organic
    "ring shop":         "CLR_YELLOW",        // gold rings
    "rod shop":          "CLR_MAGENTA",       // rod/wand-like items (distinct magic-y feel)
    "tool shop":         "CLR_GRAY",          // utilitarian
    "book shop":         "HI_PAPER",          // books/parchment
    "health food shop":  "CLR_BRIGHT_GREEN",  // healthy/vegetal
    "candle shop":       "CLR_YELLOW"         // candle flame/light
};

/**
 * Sets the dither color for a brush based on its room type.
 * 
 * @param {Object} brush - The brush object that has .type and .internal
 * @returns {string} The chosen color constant (e.g. "CLR_RED")
 */
function setRoomDitherColor(brush) {
    if (!brush || typeof brush.type !== "string") {
        // safety fallback
        const fallback = "CLR_GRAY";
        if (brush?.internal) brush.internal.ditherColor = fallback;
        return fallback;
    }

    // Look up the exact room type string; fall back to ordinary gray if unknown
    const color = roomDitherColors[brush.type] || "CLR_GRAY";

    if (brush.internal) {
        brush.internal.ditherColor = color;
    }

    return color;
}

const colorTable = {
    "CLR_BLACK": {
        "desc": "black",
        "RGB": {
            "r": 0,
            "g": 0,
            "b": 0
        },
        "hex": ""
    },
    "CLR_RED": {
        "desc": "red",
        "RGB": {
            "r": 255,
            "g": 0,
            "b": 0
        },
        "hex": ""
    },
    "CLR_GREEN": {
        "desc": "green",
        "RGB": {
            "r": 34,
            "g": 139,
            "b": 34
        },
        "hex": ""
    },
    "CLR_BROWN": {
        "desc": "brown",
        "RGB": {
            "r": 165,
            "g": 42,
            "b": 42
        },
        "hex": ""
    },
    "CLR_BLUE": {
        "desc": "blue",
        "RGB": {
            "r": 0,
            "g": 0,
            "b": 255
        },
        "hex": ""
    },
    "CLR_MAGENTA": {
        "desc": "magenta",
        "RGB": {
            "r": 255,
            "g": 0,
            "b": 255
        },
        "hex": ""
    },
    "CLR_CYAN": {
        "desc": "cyan",
        "RGB": {
            "r": 0,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "CLR_GRAY": {
        "desc": "gray",
        "RGB": {
            "r": 128,
            "g": 128,
            "b": 128
        },
        "hex": ""
    },
    "NO_COLOR": {
        "desc": "no-color",
        "RGB": {
            "r": 0,
            "g": 0,
            "b": 0
        },
        "hex": ""
    },
    "CLR_ORANGE": {
        "desc": "orange",
        "RGB": {
            "r": 255,
            "g": 165,
            "b": 0
        },
        "hex": ""
    },
    "CLR_BRIGHT_GREEN": {
        "desc": "light-green",
        "RGB": {
            "r": 0,
            "g": 128,
            "b": 0
        },
        "hex": ""
    },
    "CLR_YELLOW": {
        "desc": "yellow",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 0
        },
        "hex": ""
    },
    "CLR_BRIGHT_BLUE": {
        "desc": "light-blue",
        "RGB": {
            "r": 173,
            "g": 216,
            "b": 230
        },
        "hex": ""
    },
    "CLR_BRIGHT_MAGENTA": {
        "desc": "light-magenta",
        "RGB": {
            "r": 147,
            "g": 112,
            "b": 219
        },
        "hex": ""
    },
    "CLR_BRIGHT_CYAN": {
        "desc": "light-cyan",
        "RGB": {
            "r": 224,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "CLR_WHITE": {
        "desc": "white",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "CLR_MAX": {
        "desc": "maroon",
        "RGB": {
            "r": 128,
            "g": 0,
            "b": 0
        },
        "hex": "#800000"
    },
    "HI_DOMESTIC": {
        "desc": "white",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "HI_LORD": {
        "desc": "magenta",
        "RGB": {
            "r": 255,
            "g": 0,
            "b": 255
        },
        "hex": ""
    },
    "HI_OVERLORD": {
        "desc": "light-magenta",
        "RGB": {
            "r": 147,
            "g": 112,
            "b": 219
        },
        "hex": ""
    },
    "HI_OBJ": {
        "desc": "magenta",
        "RGB": {
            "r": 255,
            "g": 0,
            "b": 255
        },
        "hex": ""
    },
    "HI_METAL": {
        "desc": "cyan",
        "RGB": {
            "r": 0,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "HI_COPPER": {
        "desc": "yellow",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 0
        },
        "hex": ""
    },
    "HI_SILVER": {
        "desc": "gray",
        "RGB": {
            "r": 128,
            "g": 128,
            "b": 128
        },
        "hex": ""
    },
    "HI_GOLD": {
        "desc": "yellow",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 0
        },
        "hex": ""
    },
    "HI_LEATHER": {
        "desc": "brown",
        "RGB": {
            "r": 165,
            "g": 42,
            "b": 42
        },
        "hex": ""
    },
    "HI_CLOTH": {
        "desc": "brown",
        "RGB": {
            "r": 165,
            "g": 42,
            "b": 42
        },
        "hex": ""
    },
    "HI_ORGANIC": {
        "desc": "brown",
        "RGB": {
            "r": 165,
            "g": 42,
            "b": 42
        },
        "hex": ""
    },
    "HI_WOOD": {
        "desc": "brown",
        "RGB": {
            "r": 165,
            "g": 42,
            "b": 42
        },
        "hex": ""
    },
    "HI_PAPER": {
        "desc": "white",
        "RGB": {
            "r": 255,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "HI_GLASS": {
        "desc": "light-cyan",
        "RGB": {
            "r": 224,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "HI_MINERAL": {
        "desc": "gray",
        "RGB": {
            "r": 128,
            "g": 128,
            "b": 128
        },
        "hex": ""
    },
    "DRAGON_SILVER": {
        "desc": "light-cyan",
        "RGB": {
            "r": 224,
            "g": 255,
            "b": 255
        },
        "hex": ""
    },
    "HI_ZAP": {
        "desc": "light-blue",
        "RGB": {
            "r": 173,
            "g": 216,
            "b": 230
        },
        "hex": ""
    }
};