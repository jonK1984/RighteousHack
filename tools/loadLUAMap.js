// loadLUAMap.js
// Loader for NetHack .lua des files into the map editor
// Only deterministic top-level des. calls are processed.
// Uses allMonsters, allObjects, allTerrains, and the features array (from feature_def.js) for accurate symbol lookup.

//const COLS = 80;
//const ROWS = 21;

// Lookup maps built dynamically from the definition files
const monsterSymMap = {};
const objectSymMap = {};
const featureSymMap = {};

// Add this to buildLookups() in loadLUAMap.js (inside the existing function)

const symToTerrain = {};

// Reverse lookup: lua symbol → terrain key (e.g. " " → "stone", "." → "room")
if (typeof allTerrains !== 'undefined') {
    Object.keys(allTerrains).forEach(key => {
        const t = allTerrains[key];
        // Some entries use "\0" for boulder – treat as special case
        if (t.lua === '\0') {
            symToTerrain['\0'] = key;
        } else if (t.lua) {
            symToTerrain[t.lua] = key;
        }
    });
}

// Safety overrides for the most common symbols (in case allTerrains is incomplete)
Object.assign(symToTerrain, {
    ' ': 'stone',
    '.': 'room',
    '#': 'corr',
    '-': 'hwall',
    '|': 'vwall',
    '+': 'door',
    '<': 'upstair',
    '>': 'downstair',
    '{': 'pool',
    '}': 'lava',
    '^': 'tree',     // arboreal levels use ^ for trees
    '_': 'altar',
    '`': 'grave'
});

function buildLookups() {
    // Monsters
    if (typeof allMonsters !== 'undefined') {
        Object.keys(allMonsters).forEach(key => {
            const mon = allMonsters[key];
            const lowerKey = key.toLowerCase();
            monsterSymMap[lowerKey] = mon.symbol;
            if (mon.id && mon.id.toLowerCase() !== lowerKey) {
                monsterSymMap[mon.id.toLowerCase()] = mon.symbol;
            }
        });
    }

    // Objects
    if (typeof allObjects !== 'undefined') {
        Object.keys(allObjects).forEach(key => {
            const obj = allObjects[key];
            const lowerKey = key.toLowerCase();
            objectSymMap[lowerKey] = obj.symbol;
            if (obj.id && obj.id.toLowerCase() !== lowerKey) {
                objectSymMap[obj.id.toLowerCase()] = obj.symbol;
            }
        });
    }

    // Features – leverage both feature_def.js array and allTerrains
    // Assume the features/traps/specials array in feature_def.js is exposed as a global `allFeatures`
    // (common pattern in the editor). If not present, fall back to sensible defaults.
    if (typeof allFeatures !== 'undefined' && Array.isArray(allFeatures)) {
        allFeatures.forEach(item => {
            if (item.name && item.sym) {
                featureSymMap[item.name.toLowerCase()] = item.sym;
            }
        });
    }

    // Add/override with terrain symbols from allTerrains (e.g., tree, pool, lava, ice, etc.)
    if (typeof allTerrains !== 'undefined') {
        Object.keys(allTerrains).forEach(key => {
            const t = allTerrains[key];
            if (t.lua && t.lua !== ' ' && t.lua !== '\0') {
                featureSymMap[key.toLowerCase()] = t.lua;
            }
        });
    }

    // Hard-coded safety net for the most common placed features (fountain, sink, throne, grave, altar)
    // These are not always in allTerrains and guarantee correct visible symbols.
    const specials = {
        "fountain": "{",
        "sink": "}",
        "throne": "A",
        "grave": "`",
        "altar": "_"
    };
    Object.assign(featureSymMap, specials);
}

function getMonsterSym(name) {
    if (!name) return null;
    name = name.trim();
    if (name.length === 1) return name; // class letter
    const lower = name.toLowerCase();
    return monsterSymMap[lower] || name.charAt(0).toUpperCase();
}

function getObjectSym(name) {
    if (!name) return null;
    const lower = name.toLowerCase();
    return objectSymMap[lower] || '*';
}

function getFeatureSym(type) {
    if (!type) return '^';
    const lower = type.toLowerCase();
    return featureSymMap[lower] || '^'; // default to generic trap/feature glyph
}

// Call once at load time
buildLookups();

// loadLUAMap.js - Fully rewritten using luaparse for robust, future-proof parsing

// Ensure luaparse is loaded before this script:
// <script src="https://cdn.jsdelivr.net/npm/luaparse@0.3.1/luaparse.min.js"></script>


function dequote(str) {
    // Remove surrounding single or double quotes if present
    if (typeof str === 'string' && (
        (str.startsWith('"') && str.endsWith('"')) ||
        (str.startsWith("'") && str.endsWith("'"))
    )) {
        return str.slice(1, -1);
    }
    return str; // Return unchanged if no quotes
}

function loadLUAMap(luaText) {
    if (!luaText) return;

    // Initialize layers with default 'stone' terrain
    layers.terrain = Array.from({length: ROWS}, () => Array(COLS).fill('stone'));
    layers.lighting = Array.from({length: ROWS}, () => Array(COLS).fill(''));
    layers.monster = Array.from({length: ROWS}, () => Array(COLS).fill(null));
    layers.features = Array.from({length: ROWS}, () => Array(COLS).fill(null));

    initState = {
        style: "",
        fg: " ",
        flags: [],
        other: ""
    };

    try {
        const ast = luaparse.parse(luaText, {
            luaVersion: '5.3',
            comments: false,      // We don't need comments
            locations: true       // Helpful for debugging if needed
        });

        // Traverse top-level statements
        for (const stmt of ast.body) {
            if (stmt.type !== 'CallStatement') continue;

            const call = stmt.expression;
            if (call.base.type !== 'MemberExpression' || call.base.base.name !== 'des') continue;

            const method = call.base.identifier.name;
            const args = call.arguments || [];

            switch (method) {
                case 'level_init':
                    if (args[0]?.type === 'TableConstructorExpression') {
                        const table = args[0];
                        let solidfill = false;
                        let fgChar = ' ';
                        let wholeLit = false;

                        for (const field of table.fields) {
                            const key = field.key.name || field.key.value;
                            const val = field.value;
                            const value = dequote( val.raw );
                            if (key === 'style' && value === 'solidfill') solidfill = true;
                            if (key === 'fg' && val.type === 'StringLiteral') fgChar = value;
                            if (key === 'lit' && int(value) === 1) wholeLit = true;
                        }

                        if (solidfill) {
                            const fgKey = symToTerrain[fgChar] || 'stone';
                            initState.fg = fgKey;
                            for (let y = 0; y < ROWS; y++)
                                for (let x = 0; x < COLS; x++)
                                    layers.terrain[y][x] = fgKey;
                        }
                        if (wholeLit) {
                            for (let y = 0; y < ROWS; y++)
                                for (let x = 0; x < COLS; x++)
                                    layers.lighting[y][x] = 'lit';
                        }
                    }
                    break;

                case 'level_flags':
                    if (args[0]?.type === 'StringLiteral') {
                        initState.flags = dequote(args[0].raw)
                            .split(',')
                            .map(s => s.trim())
                            .filter(Boolean);
                    }
                    break;

                case 'map':
                    if (args[0]?.type === 'StringLiteral' && args[0].raw.startsWith('[[')) {
                        const mapContent = args[0].value; // Clean content without [[ ]]
                        const lines = mapContent.split(/\r?\n/);

                        let y = 0;
                        for (let line of lines) {
                            if (y >= ROWS) break;
                            line = line.replace(/^\|?/, ''); // Optional leading |
                            for (let x = 0; x < COLS; x++) {
                                const ch = x < line.length ? line[x] : ' ';
                                layers.terrain[y][x] = symToTerrain[ch] || 'stone';
                            }
                            y++;
                        }
                    }
                    break;

                case 'region':
                    let litVal = '';
                    let rx1, ry1, rx2, ry2;

                    // lit/unlit flag
                    if (args[args.length - 1]?.type === 'StringLiteral') {
                        const last = args[args.length - 1].value;
                        if (last === 'lit') litVal = 'lit';
                        if (last === 'unlit') litVal = 'unlit';
                    }

                    // Extract coordinates
                    if (args[0]?.type === 'CallExpression' && args[0].base?.name === 'selection' && args[0].indexer?.value === 'area') {
                        const a = args[0].arguments;
                        if (a.length === 4) {
                            rx1 = a[0].value; ry1 = a[1].value;
                            rx2 = a[2].value; ry2 = a[3].value;
                        }
                    } else if (args[0]?.type === 'TableConstructorExpression') {
                        for (const field of args[0].fields) {
                            if (field.key.name === 'region' && field.value.type === 'TableConstructorExpression') {
                                const r = field.value.fields;
                                if (r.length === 4) {
                                    rx1 = r[0].value.value; ry1 = r[1].value.value;
                                    rx2 = r[2].value.value; ry2 = r[3].value.value;
                                }
                            }
                            if (field.key.name === 'lit' && field.value.value === 1) litVal = 'lit';
                        }
                    }

                    if (litVal && typeof rx1 === 'number') {
                        for (let yy = ry1; yy <= ry2 && yy < ROWS; yy++) {
                            for (let xx = rx1; xx <= rx2 && xx < COLS; xx++) {
                                layers.lighting[yy][xx] = litVal;
                            }
                        }
                    }
                    break;

                case 'room':
                    if (args[0]?.type !== 'TableConstructorExpression') break;

                    const room = args[0];
                    let lit = false;
                    let roomX1, roomY1, roomX2, roomY2;

                    let roomW = 0, roomH = 0, roomX = 0, roomY = 0;
                    let xAlign = '', yAlign = '';

                    for (const field of room.fields) {
                        const key = field.key.name;
                        const val = field.value;

                        if (key === 'lit' && val.value === 1) lit = true;
                        if (key === 'region' && val.type === 'TableConstructorExpression' && val.fields.length === 4) {
                            roomX1 = val.fields[0].value.value;
                            roomY1 = val.fields[1].value.value;
                            roomX2 = val.fields[2].value.value;
                            roomY2 = val.fields[3].value.value;
                        }
                        if (key === 'x') roomX = val.value;
                        if (key === 'y') roomY = val.value;
                        if (key === 'w') roomW = val.value;
                        if (key === 'h') roomH = val.value;
                        if (key === 'xalign') xAlign = val.value;
                        if (key === 'yalign') yAlign = val.value;
                    }

                    // Resolve coordinates
                    if (typeof roomX1 !== 'number') {
                        if (roomW && roomH) {
                            roomX1 = roomX;
                            roomY1 = roomY;
                            if (xAlign === 'center') roomX1 = Math.floor((COLS - roomW) / 2);
                            if (yAlign === 'center') roomY1 = Math.floor((ROWS - roomH) / 2);
                            roomX2 = roomX1 + roomW - 1;
                            roomY2 = roomY1 + roomH - 1;
                        } else break;
                    }

                    // Draw using terrain keys
                    const floorKey = symToTerrain['.'] || 'room';
                    const hwallKey = symToTerrain['-'] || 'hwall';
                    const vwallKey = symToTerrain['|'] || 'vwall';
                    const cornerKey = symToTerrain['+'] || 'hwall'; // Corners are walls

                    // Floor
                    for (let yy = roomY1 + 1; yy < roomY2; yy++)
                        for (let xx = roomX1 + 1; xx < roomX2; xx++)
                            if (yy < ROWS && xx < COLS) layers.terrain[yy][xx] = floorKey;

                    // Top/bottom walls
                    for (let xx = roomX1 + 1; xx < roomX2; xx++) {
                        if (roomY1 < ROWS && xx < COLS) layers.terrain[roomY1][xx] = hwallKey;
                        if (roomY2 < ROWS && xx < COLS) layers.terrain[roomY2][xx] = hwallKey;
                    }

                    // Side walls
                    for (let yy = roomY1 + 1; yy < roomY2; yy++) {
                        if (yy < ROWS && roomX1 < COLS) layers.terrain[yy][roomX1] = vwallKey;
                        if (yy < ROWS && roomX2 < COLS) layers.terrain[yy][roomX2] = vwallKey;
                    }

                    // Corners
                    if (roomY1 < ROWS && roomX1 < COLS) layers.terrain[roomY1][roomX1] = cornerKey;
                    if (roomY1 < ROWS && roomX2 < COLS) layers.terrain[roomY1][roomX2] = cornerKey;
                    if (roomY2 < ROWS && roomX1 < COLS) layers.terrain[roomY2][roomX1] = cornerKey;
                    if (roomY2 < ROWS && roomX2 < COLS) layers.terrain[roomY2][roomX2] = cornerKey;

                    if (lit) {
                        for (let yy = roomY1; yy <= roomY2 && yy < ROWS; yy++)
                            for (let xx = roomX1; xx <= roomX2 && xx < COLS; xx++)
                                layers.lighting[yy][xx] = 'lit';
                    }
                    break;

                case 'feature':
                    if (args.length === 3 && args[0].type === 'StringLiteral' &&
                        args[1].type === 'NumericLiteral' && args[2].type === 'NumericLiteral') {
                        const type = args[0].value;
                        const x = args[1].value;
                        const y = args[2].value;
                        const sym = getFeatureSym(type);
                        const key = symToTerrain[sym] || 'room'; // Assume placed on floor
                        if (y < ROWS && x < COLS) layers.terrain[y][x] = key;
                    }
                    break;

                case 'stair':
                    if (args.length === 3 && args[0].type === 'StringLiteral' &&
                        args[1].type === 'NumericLiteral' && args[2].type === 'NumericLiteral') {
                        const dir = args[0].value;
                        const x = args[1].value;
                        const y = args[2].value;
                        const sym = dir === 'up' ? '<' : '>';
                        const key = symToTerrain[sym] || 'room';
                        if (y < ROWS && x < COLS) layers.terrain[y][x] = key;
                    }
                    break;

                case 'altar':
                    if (args[0]?.type === 'TableConstructorExpression') {
                        let ax, ay;
                        for (const f of args[0].fields) {
                            if (f.key.name === 'x') ax = f.value.value;
                            if (f.key.name === 'y') ay = f.value.value;
                        }
                        if (typeof ax === 'number' && typeof ay === 'number') {
                            const key = symToTerrain['_'] || 'altar';
                            if (ay < ROWS && ax < COLS) layers.terrain[ay][ax] = key;
                        }
                    }
                    break;

                case 'door':
                    if (args[0]?.type === 'TableConstructorExpression') {
                        let dx, dy;
                        for (const f of args[0].fields) {
                            if (f.key.name === 'x') dx = f.value.value;
                            if (f.key.name === 'y') dy = f.value.value;
                        }
                        if (typeof dx === 'number' && typeof dy === 'number') {
                            const key = symToTerrain['+'] || 'door';
                            if (dy < ROWS && dx < COLS) layers.terrain[dy][dx] = key;
                        }
                    }
                    break;

                case 'object':
                    if (args.length === 3 && args[0].type === 'StringLiteral' &&
                        args[1].type === 'NumericLiteral' && args[2].type === 'NumericLiteral') {
                        const id = args[0].value;
                        const x = args[1].value;
                        const y = args[2].value;
                        const sym = getObjectSym(id);
                        const key = symToTerrain[sym] || 'room';
                        if (y < ROWS && x < COLS) layers.terrain[y][x] = key;
                    }
                    break;

                case 'monster':
                    let monSym = null;
                    let mx = null, my = null;

                    if (args[0]?.type === 'TableConstructorExpression') {
                        for (const f of args[0].fields) {
                            if (f.key.name === 'id' && f.value.type === 'StringLiteral')
                                monSym = getMonsterSym(f.value.value);
                            if (f.key.name === 'x') mx = f.value.value;
                            if (f.key.name === 'y') my = f.value.value;
                        }
                    } else if (args.length >= 3) {
                        const firstArg = args[0];
                        const firstVal = firstArg.type === 'StringLiteral' ? firstArg.value : String(firstArg.value);
                        monSym = getMonsterSym(firstVal);
                        mx = args[1].value;
                        my = args[2].value;
                    }

                    if (monSym && typeof mx === 'number' && typeof my === 'number' &&
                        my < ROWS && mx < COLS) {
                        layers.monster[my][mx] = monSym;
                    }
                    break;

                // Add more cases here if new deterministic des. calls appear in levels
            }
        }

        updateText(true);
        renderLayers();

    } catch (err) {
        console.error('Lua parsing failed:', err);
        alert('Failed to load Lua map: ' + err.message);
    }
}