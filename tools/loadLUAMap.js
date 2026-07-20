// loadLUAMap.js
// Loader for NetHack .lua des files into the map editor
// Only deterministic top-level des. calls are processed.
// Uses allMonsters, allObjects, allTerrains, and the features array (from feature_def.js) for accurate symbol lookup.

// Grid size comes from map_edit.html: COLS=80, ROWS=21 (NetHack COLNO/ROWNO)

// Lookup maps built dynamically from the definition files

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
/*Object.assign(symToTerrain, {
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
});*/

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

// ---------------------------------------------------------------
// New inventory parsing helpers
// ---------------------------------------------------------------

/**
 * Reusable helper: normalize a Lua value node into a plain JS value
 * or a { variable: "name" } object if it's an Identifier.
 *
 * Supports the common types we see in .des files:
 *   - Identifier      → { variable: "loc" }
 *   - StringLiteral   → dequoted string
 *   - NumericLiteral  → number
 *   - BooleanLiteral  → true/false
 *   - FunctionDeclaration → returned unchanged (for contents, etc.)
 *
 * @param {Object} valNode - the AST node for the field value
 * @returns {any} normalized value
 */
function parseValueNode(valNode) {
    if (!valNode) return undefined;

    if (valNode.type === "Identifier") {
        return { variable: valNode.name };
    } else if (valNode.type === "StringLiteral") {
        return dequote(valNode.raw);
    } else if (valNode.type === "NumericLiteral") {
        return valNode.value;
    } else if (valNode.type === "BooleanLiteral") {
        return valNode.value;
    } else if (valNode.type === "FunctionDeclaration") {
        return valNode; // preserve for contents/inventory
    } else if (valNode.type === "TableConstructorExpression") {
        // Special handling for coord tables
        const fields = valNode.fields;
        if (fields.length === 2 &&
            fields[0].type === "TableValue" && fields[0].value.type === "NumericLiteral" &&
            fields[1].type === "TableValue" && fields[1].value.type === "NumericLiteral") {
            // Array form {09, 07}
            return [fields[0].value.value, fields[1].value.value];
        }

        // Keyed form {x=45, y=02} – check for x and y keys
        let x, y;
        for (const field of fields) {
            if (field.type === "TableKeyString") {
                if (field.key.name === "x" && field.value.type === "NumericLiteral") {
                    x = field.value.value;
                } else if (field.key.name === "y" && field.value.type === "NumericLiteral") {
                    y = field.value.value;
                }
            }
        }
        if (x !== undefined && y !== undefined) {
            return { x, y };
        }

        // Fallback for other tables – return undefined (caller keeps raw)
        return undefined;
    }

    return undefined;
}

/**
 * Parse ANY des.monster(...) call and return a monster brush.
 * Mirrors getObjectBrushFromLUAObj exactly:
 * - Root: Lua-round-trip properties (id, class, peaceful, align, coord,
 *         appear_as, asleep, inventory, x, y)
 * - internal: { symbol, color, random, brushMode }
 */
function getMonsterBrushFromLUAObj(callNode) {
    if (!callNode || callNode.type !== "CallExpression" || !callNode.arguments) {
        return null;
    }

    const args = callNode.arguments;
    const brush = {};

    brush.internal = {
        symbol: '♣',
        color: 'CLR_WHITE',
        random: true,
        brushMode: 'simple',
        type: 'monster'
    };

    // ------------------------------------------------------------------
    // Case 1: Table → complex mode
    // ------------------------------------------------------------------
    if (args.length === 1 && args[0].type === "TableConstructorExpression") {
        brush.internal.brushMode = 'complex';

        const table = args[0];
        const fields = {};

        for (const field of table.fields) {
            if (field.type !== "TableKeyString") continue;
            const key = field.key.name;
            const rawVal = field.value;

            const parsed = parseValueNode(rawVal);
            if (parsed !== undefined) {
                fields[key] = parsed;
            } else {
                fields[key] = rawVal; // inventory function
            }
        }

        // ID resolution (lookup symbol/color)
        if (fields.id && typeof fields.id === "string") {
            const mon = getMonsterById(fields.id);
            if (mon) {
                brush.internal.symbol = mon.symbol;
                brush.internal.color = mon.color;
                brush.internal.random = false;
            }
            brush.id = fields.id;
        }

        // Class fallback
        if (fields.class && typeof fields.class === "string" && !brush.id) {
            brush.internal.symbol = fields.class;
            brush.internal.random = false;
            brush.class = fields.class;
        }

        // Round-trip properties from table
        if (fields.peaceful !== undefined) brush.peaceful = fields.peaceful;
        if (fields.align !== undefined) brush.align = fields.align;
        if (fields.coord !== undefined) brush.coord = fields.coord;
        if (fields.appear_as !== undefined) brush.appear_as = fields.appear_as;
        if (fields.asleep !== undefined) brush.asleep = fields.asleep;

        // x,y from table (common in complex)
        if (fields.x !== undefined) brush.x = fields.x;
        if (fields.y !== undefined) brush.y = fields.y;

        // Inventory – recursive objects
        if (fields.inventory && fields.inventory.type === "FunctionDeclaration" && fields.inventory.body) {
            brush.inventory = [];
            for (const stmt of fields.inventory.body) {
                if (stmt.type !== "CallStatement") continue;
                const expr = stmt.expression;
                if (expr.type !== "CallExpression") continue;

                if (!expr.base ||
                    expr.base.type !== "MemberExpression" ||
                    expr.base.identifier.name !== "object" ||
                    !expr.base.base ||
                    expr.base.base.name !== "des") {
                    continue;
                }

                const objBrush = getObjectBrushFromLUAObj(expr);
                if (objBrush) {
                    brush.inventory.push(objBrush);
                }
            }
        }

        return brush;
    }

    // ------------------------------------------------------------------
    // Case 2: Simple positional
    // ------------------------------------------------------------------
    let argIdx = 0;

    if (args.length > argIdx) {
        const firstArg = args[argIdx];

        // Variable reference (mons[...], monster[...])
        if (firstArg.type === "IndexExpression" ||
            (firstArg.type === "CallExpression" && firstArg.base?.type === "IndexExpression")) {
            brush.name = { variable: reconstructVariableRef(firstArg) };
            brush.internal.random = false;
            argIdx++;
        }
        // String literal id or class
        else if (firstArg.type === "StringLiteral") {
            const str = dequote(firstArg.raw);
            const mon = getMonsterById(str);
            if (mon) {
                brush.internal.symbol = mon.symbol;
                brush.internal.color = mon.color;
                brush.internal.random = false;
                brush.id = str;
            } else {
                brush.internal.symbol = str;
                brush.internal.random = false;
                brush.class = str;
            }
            argIdx++;
        }
    }

    // x,y coords (positional in simple)
    if (args.length - argIdx === 2 &&
        args[argIdx].type === "NumericLiteral" &&
        args[argIdx + 1].type === "NumericLiteral") {
        brush.x = args[argIdx].value;
        brush.y = args[argIdx + 1].value;
    }

    if (argIdx === 0) {
        brush.internal.symbol = 'm'; // generic monster
    }

    return brush;
}

// Monster lookup (case-insensitive, like objects)
function getMonsterById(monID) {
    if (typeof monID !== 'string') return null;
    const lower = monID.toLowerCase();
    return allMonsters[lower] || null;
}

// Approximate variable ref string (for simple mode display)
function reconstructVariableRef(node) {
    if (node.type === "IndexExpression") {
        const base = node.base.name || '';
        const index = node.index.raw || node.index.value || '';
        return `${base}[${index}]`;
    }
    if (node.type === "CallExpression" && node.base?.type === "IndexExpression") {
        // e.g., mons[math.random(1, #mons)]
        return reconstructVariableRef(node.base);
    }
    return 'unknown_variable';
}

/**
 * Resolve a local name used as coord (e.g. loc from place:rndcoord) to a
 * deterministic preview {x,y}. Map-relative selection points are returned
 * without map origin applied — caller adds lastMapOrigin when placing.
 *
 * @param {string} name
 * @returns {{x:number,y:number,source:string}|null}
 */
function resolveCoordVariable(name) {
    if (!name || typeof name !== 'string') return null;
    const def = (typeof luaLocals !== 'undefined') ? luaLocals[name] : null;
    if (!def) return null;

    if (def.kind === 'rndcoord_ref') {
        const sel = luaLocals[def.from];
        if (sel && sel.kind === 'selection' && Array.isArray(sel.points) && sel.points.length) {
            return { x: sel.points[0][0], y: sel.points[0][1], source: name };
        }
        return null;
    }
    if (def.kind === 'selection' && Array.isArray(def.points) && def.points.length) {
        return { x: def.points[0][0], y: def.points[0][1], source: name };
    }
    if (def.kind === 'coord_list' && Array.isArray(def.values) && def.values.length) {
        return { x: def.values[0][0], y: def.values[0][1], source: name };
    }
    return null;
}

/**
 * Extract x,y from a brush's .coord property.
 * Fixed tables → numbers. Variable refs → preview resolve when possible.
 *
 * @param {Object} brush
 * @param {{resolveVariable?: boolean}} opts  default resolveVariable true
 * @returns {{x: number, y: number, variable?: string}|null}
 */
function getXYFromCoord(brush, opts = {}) {
    if (!brush || !brush.coord) {
        return null;
    }

    const resolveVariable = opts.resolveVariable !== false;
    const coord = brush.coord;

    // Variable reference → try deterministic preview from luaLocals
    if (coord.variable) {
        if (!resolveVariable) return null;
        const resolved = resolveCoordVariable(coord.variable);
        if (!resolved) return null;
        return { x: resolved.x, y: resolved.y, variable: coord.variable };
    }

    // Expect array of exactly two numbers (from {09,07} table)
    if (Array.isArray(coord) && coord.length === 2 &&
        typeof coord[0] === 'number' && typeof coord[1] === 'number') {
        return { x: coord[0], y: coord[1] };
    }

    // Fallback for rare {x=..., y=...} table form (if we ever support it)
    if (typeof coord === 'object' && coord.x !== undefined && coord.y !== undefined &&
        typeof coord.x === 'number' && typeof coord.y === 'number') {
        return { x: coord.x, y: coord.y };
    }

    // Anything else (invalid, string, etc.) → null
    return null;
}

/**
 * Place object/monster brush on grid or RND, handling variable coords.
 * Map-relative preview coords get lastMapOrigin applied.
 */
function placeBrushWithCoords(brush, layerKind /* 'object'|'monster' */) {
    if (!brush) return;

    let x = brush.x != null ? brush.x : null;
    let y = brush.y != null ? brush.y : null;
    const fromCoord = getXYFromCoord(brush);
    if (fromCoord) {
        x = fromCoord.x;
        y = fromCoord.y;
        // des.object/monster coord (fixed table or variable) is map-relative after des.map
        if (lastMapOrigin) {
            x += (lastMapOrigin.x || 0);
            y += (lastMapOrigin.y || 0);
        }
        if (brush.internal) {
            brush.internal.previewX = x;
            brush.internal.previewY = y;
        }
    }

    // Fixed x,y from brush may already include map origin via applyMapOriginToBrush

    const grid = layerKind === 'monster' ? layers.monster : layers.object;
    const rnd = layerKind === 'monster' ? layers.monsterRND : layers.objectRND;

    if (y != null && x != null && y >= 0 && y < ROWS && x >= 0 && x < COLS) {
        // If slot occupied and this is a variable-coord secondary object, keep in RND with coord.variable
        if (grid[y][x] && brush.coord && brush.coord.variable) {
            rnd.push(brush);
        } else {
            grid[y][x] = brush;
        }
    } else {
        rnd.push(brush);
    }
}

/**
 * Parse ANY des.object(...) call (simple or complex) and return a brush.
 * Brush structure:
 *   - Root level: Lua-round-trip properties (id, class, trapped, locked, buc,
 *                 spe, name, montype, historic, quantity, coord, contents, x, y)
 *   - internal: { symbol, color, random, brushMode } – editor-only
 */
function getObjectBrushFromLUAObj(callNode) {
    if (!callNode || callNode.type !== "CallExpression" || !callNode.arguments) {
        return null;
    }

    const args = callNode.arguments;
    const brush = {};

    // Editor-internal data
    brush.internal = {
        symbol: '§',
        color: 'CLR_WHITE',
        random: true,
        brushMode: 'simple',   // default; overridden below for complex case
        type: 'object'
    };

    // ------------------------------------------------------------------
    // Case 1: Table argument → COMPLEX mode
    // ------------------------------------------------------------------
    if (args.length === 1 && args[0].type === "TableConstructorExpression") {
        brush.internal.brushMode = 'complex';

        const table = args[0];
        const fields = {};

        for (const field of table.fields) {
            if (field.type !== "TableKeyString") continue;
            const key = field.key.name;
            const rawVal = field.value;

            const parsed = parseValueNode(rawVal);
            if (parsed !== undefined) {
                fields[key] = parsed;
            } else {
                fields[key] = rawVal; // e.g., contents function
            }
        }

        // ID → resolve symbol/color internally
        if (fields.id && typeof fields.id === "string") {
            const obj = getObjectById(fields.id);
            if (obj) {
                brush.internal.symbol = obj.symbol;
                brush.internal.color = obj.color;
                brush.internal.random = false;
            }
            brush.id = fields.id;
        }

        // Class → use as symbol internally
        if (fields.class && typeof fields.class === "string" && !brush.id) {
            brush.internal.symbol = fields.class;
            brush.internal.random = false;
            brush.class = fields.class;
        }

        // Direct round-trip properties
        if (fields.spe !== undefined) brush.spe = fields.spe;
        if (fields.buc !== undefined) brush.buc = fields.buc;
        if (fields.name !== undefined) brush.name = fields.name;
        if (fields.montype !== undefined) brush.montype = fields.montype;
        if (fields.historic !== undefined) brush.historic = fields.historic;
        if (fields.quantity !== undefined) brush.quantity = fields.quantity;
        if (fields.trapped !== undefined) brush.trapped = fields.trapped;
        if (fields.locked !== undefined) brush.locked = fields.locked;

        // x,y from table (common in complex)
        if (fields.x !== undefined) brush.x = fields.x;
        if (fields.y !== undefined) brush.y = fields.y;

        // Coord
        if (fields.coord !== undefined) brush.coord = fields.coord;

        // Contents – recursive (contents = function() des.object(...) end)
        const contentsNode = fields.contents;
        if (contentsNode) {
            const bodyStmts = Array.isArray(contentsNode.body)
                ? contentsNode.body
                : (contentsNode.body && Array.isArray(contentsNode.body.body)
                    ? contentsNode.body.body
                    : null);
            if (bodyStmts) {
                brush.contents = [];
                for (const stmt of bodyStmts) {
                    if (stmt.type !== "CallStatement") continue;
                    const expr = stmt.expression;
                    if (!expr || expr.type !== "CallExpression") continue;

                    // des.object(...)
                    if (!expr.base ||
                        expr.base.type !== "MemberExpression" ||
                        expr.base.identifier?.name !== "object" ||
                        !expr.base.base ||
                        expr.base.base.name !== "des") {
                        continue;
                    }

                    const innerBrush = getObjectBrushFromLUAObj(expr);
                    if (innerBrush) {
                        brush.contents.push(innerBrush);
                    }
                }
            }
        }

        return brush;
    }

    // ------------------------------------------------------------------
    // Case 2: Positional arguments → SIMPLE mode (already default)
    // ------------------------------------------------------------------
    let argIdx = 0;

    if (args.length > argIdx) {
        const firstArg = args[argIdx];

        // localvar[N] reference (e.g. object[1], objclass[2])
        if (firstArg.type === "IndexExpression" ||
            (firstArg.type === "CallExpression" && firstArg.base?.type === "IndexExpression")) {
            brush.name = { variable: reconstructVariableRef(firstArg) };
            brush.internal.random = false;
            argIdx++;
        }
        // String literal (id, class char, or free name e.g. artifact)
        else if (firstArg.type === "StringLiteral") {
            const str = dequote(firstArg.raw);
            const obj = getObjectById(str);
            if (obj) {
                brush.internal.symbol = obj.symbol;
                brush.internal.color = obj.color;
                brush.internal.random = false;
                brush.id = str;
            } else if (str.length === 1 && typeof isValidObjectClass === 'function' && isValidObjectClass(str)) {
                brush.internal.symbol = str;
                brush.internal.random = false;
                brush.class = str;
            } else {
                // Named object not in allObjects (e.g. "ask and ye shall receive")
                brush.id = str;
                brush.internal.symbol = (str && str.charAt(0)) || '?';
                brush.internal.random = false;
            }
            argIdx++;
        }
    }

    // x,y coordinates (round-trip)
    if (args.length - argIdx === 2 &&
        args[argIdx].type === "NumericLiteral" &&
        args[argIdx + 1].type === "NumericLiteral") {
        brush.x = args[argIdx].value;
        brush.y = args[argIdx + 1].value;
    }

    // Fully random (no args)
    if (argIdx === 0) {
        brush.internal.symbol = '*';
    }

    return brush;
}

/**
 * Parse an entire "inventory" table key node and return an array
 * of object brushes for everything inside the inventory function.
 *
 * @param {Object} inventoryNode - the full TableKeyString node for "inventory"
 * @returns {Array<Object>} array of object brushes
 */
function parseInventory(inventoryNode) {
    const brushes = [];

    // Safety checks
    if (!inventoryNode ||
        inventoryNode.type !== "TableKeyString" ||
        inventoryNode.key.name !== "inventory" ||
        !inventoryNode.value) {
        return brushes;
    }

    const func = inventoryNode.value;
    if (func.type !== "FunctionDeclaration" || !func.body) {
        return brushes;
    }

    for (const stmt of func.body) {
        if (stmt.type !== "CallStatement") continue;

        const expr = stmt.expression;
        if (expr.type !== "CallExpression") continue;

        // Must be des.object
        if (!expr.base ||
            expr.base.type !== "MemberExpression" ||
            expr.base.identifier.name !== "object" ||
            !expr.base.base ||
            expr.base.base.name !== "des") {
            continue;
        }

        const brush = getObjectBrushFromLUAObj(expr);
        if (brush) brushes.push(brush);
    }

    return brushes;
}



/**
 * Reconstruct original Lua source code from a luaparse AST node.
 * Handles all your examples accurately, including:
 *   - hells[hellno]()
 *   - #hells length operator
 *   - elseif
 *   - Large array tables with anonymous functions + blank lines
 * Preserves .raw, indentation, commas.
 * Adds ';' after CallStatements to match common .des style.
 */
function getCodeStringFromLUAStmt(node, indent = '') {
    if (!node) return '';

    // Helper: reconstruct expression recursively
    function exprToString(expr, exprIndent = indent) {
        if (!expr) return '';

        switch (expr.type) {
            case 'Identifier':
                return expr.name;

            case 'StringLiteral':
                return expr.raw || `"${expr.value.replace(/"/g, '\\"')}"`;

            case 'NumericLiteral':
                return expr.raw || String(expr.value);

            case 'BooleanLiteral':
                return expr.raw || (expr.value ? 'true' : 'false');

            case 'UnaryExpression':
                if (expr.operator === '#') {
                    return '#' + exprToString(expr.argument, exprIndent);
                }
                return expr.operator + exprToString(expr.argument, exprIndent);

            case 'IndexExpression':
                {
                    const base = exprToString(expr.base, exprIndent);
                    const index = exprToString(expr.index, exprIndent);
                    return `${base}[${index}]`;
                }

            case 'TableConstructorExpression':
                let lines = ['{'];
                let innerIndent = exprIndent + '   ';

                for (let i = 0; i < expr.fields.length; i++) {
                    const field = expr.fields[i];
                    let fieldStr = innerIndent;

                    if (field.type === 'TableKeyString') {
                        fieldStr += `${field.key.name} = ${exprToString(field.value, innerIndent)}`;
                    } else if (field.type === 'TableValue') {
                        const valStr = exprToString(field.value, innerIndent);
                        if (field.value.type === 'FunctionDeclaration') {
                            if (i > 0) lines.push('');
                            fieldStr += valStr;
                        } else {
                            fieldStr += valStr;
                        }
                    }

                    if (i < expr.fields.length - 1) {
                        fieldStr += ',';
                    }
                    lines.push(fieldStr);
                }

                if (expr.fields.length > 0 && expr.fields[expr.fields.length - 1].value?.type === 'FunctionDeclaration') {
                    lines.push('');
                }

                lines.push(exprIndent + '}');
                return lines.join('\n');

            case 'FunctionDeclaration':
                let funcLines = ['function()'];
                let bodyIndent = exprIndent + '   ';

                for (const bodyNode of expr.body || []) {
                    funcLines.push(getCodeStringFromLUAStmt(bodyNode, bodyIndent));
                }

                funcLines.push(exprIndent + 'end');
                return funcLines.join('\n');

            case 'MemberExpression':
                {
                    const base = exprToString(expr.base, exprIndent);
                    const indexer = expr.indexer;
                    const id = expr.identifier.name;
                    return `${base}${indexer}${id}`;
                }

            case 'CallExpression':
                const callBase = exprToString(expr.base, exprIndent);
                let args = [];
                for (const arg of expr.arguments) {
                    args.push(exprToString(arg, exprIndent));
                }
                return `${callBase}(${args.join(', ')})`;

            case 'BinaryExpression':
                const left = exprToString(expr.left, exprIndent);
                const right = exprToString(expr.right, exprIndent);
                return `${left} ${expr.operator} ${right}`;

            default:
                return '';
        }
    }

    let outputLines = [];

    {
        switch (node.type) {
            case 'FunctionDeclaration':
                let header = indent;
                if (node.identifier) {
                    header += `function ${node.identifier.name}()`;
                } else {
                    header += 'function()';
                }
                outputLines.push(header);

                let bodyIndent = indent + '   ';
                for (const bodyNode of node.body || []) {
                    outputLines.push(getCodeStringFromLUAStmt(bodyNode, bodyIndent));
                }
                outputLines.push(indent + 'end');
                break;

            case 'LocalStatement':
                let vars = [];
                for (const v of node.variables) {
                    vars.push(v.name);
                }
                let localLine = indent + `local ${vars.join(', ')}`;
                if (node.init && node.init.length) {
                    localLine += ' = ' + exprToString(node.init[0], indent);
                }
                outputLines.push(localLine);
                break;

            case 'AssignmentStatement':
                let left = [];
                for (const v of node.variables) {
                    left.push(exprToString(v, indent));
                }
                let assignLine = indent + left.join(', ') + ' = ';
                if (node.init && node.init.length) {
                    assignLine += exprToString(node.init[0], indent);
                }
                outputLines.push(assignLine);
                break;

            case 'CallStatement':
                // Add ';' to match common .des style (des calls almost always end with ;)
                outputLines.push(indent + exprToString(node.expression, indent) + ';');
                break;

            case 'ForNumericStatement':
                const varible = node.variable.name;
                const start = exprToString(node.start, indent);
                const endVal = exprToString(node.end, indent);
                let step = '';
                if (node.step) {
                    step = ', ' + exprToString(node.step, indent);
                }
                outputLines.push(indent + `for ${varible} = ${start}, ${endVal}${step} do`);

                let forBodyIndent = indent + '   ';
                for (const bodyNode of node.body || []) {
                    outputLines.push(getCodeStringFromLUAStmt(bodyNode, forBodyIndent));
                }
                outputLines.push(indent + 'end');
                break;

            case 'IfStatement':
                for (let i = 0; i < node.clauses.length; i++) {
                    const clause = node.clauses[i];
                    if (clause.type === 'IfClause') {
                        const condition = exprToString(clause.condition, indent);
                        outputLines.push(indent + `if (${condition}) then`);
                    } else if (clause.type === 'ElseifClause') {
                        const condition = exprToString(clause.condition, indent);
                        outputLines.push(indent + `elseif (${condition}) then`);
                    } else if (clause.type === 'ElseClause') {
                        outputLines.push(indent + 'else');
                    }

                    let clauseIndent = indent + '   ';
                    for (const bodyNode of clause.body || []) {
                        outputLines.push(getCodeStringFromLUAStmt(bodyNode, clauseIndent));
                    }
                }
                outputLines.push(indent + 'end');
                break;

            default:
                outputLines.push('');
        }
    }

    return outputLines.join('\n');
}

/**
 * Helper: determine if a CallExpression is a "des." call
 * (e.g., des.object, des.monster, des.trap, des.region, etc.)
 *
 * @param {Object} expr - the expression node (usually from CallStatement.expression)
 * @returns {boolean} true if this is a des.* call
 */
function isDesCall(expr) {
    if (!expr || expr.type !== "CallExpression") {
        return false;
    }

    const base = expr.base;

    // Must be des.something
    if (!base ||
        base.type !== "MemberExpression" ||
        !base.base ||
        base.base.type !== "Identifier" ||
        base.base.name !== "des") {
        return false;
    }

    // Optional: whitelist known des functions to be extra safe
    // (commented out – currently we accept any des.*)
    /*
    const knownDesFuncs = new Set([
        'object', 'monster', 'trap', 'region', 'door', 'stair',
        'ladder', 'altar', 'gold', 'engraving', 'level',
        // add more as needed
    ]);
    if (!knownDesFuncs.has(base.identifier.name)) {
        return false;
    }
    */

    return true;
}

function parseLUAtoBrush(args, type)
{
    if (args[0]?.type !== 'TableConstructorExpression') return null;
    let luaBrush = {};
    const internal = getFeatureDefByType(type)?.internal || { type, stroke: 'point' };
    luaBrush['internal'] = {...internal};

    args[0].fields.forEach(arg => {

        if (arg?.type == 'TableKeyString' && arg?.key?.name == 'region')
        {
            const x1  = arg.value.fields[0].value.value;
            const y1 = arg.value.fields[1].value.value;
            const x2 = arg.value.fields[2].value.value;
            const y2 = arg.value.fields[3].value.value;
            luaBrush['x'] = x1;
            luaBrush['y'] = y1;
            luaBrush['w'] = Math.abs(x1 - x2) + 1;
            luaBrush['h'] = Math.abs(y1 - y2) + 1;
        }
        else if (arg?.type == 'TableKeyString')
        {
            const key = arg.key.name;
            const parsed = parseValueNode(arg.value);
            if (parsed !== undefined) {
                luaBrush[key] = parsed;
            } else if (arg.value?.raw) {
                let val = dequote(arg.value.raw);
                if (key == 'x' || key == 'y') val = parseInt(val, 10);
                luaBrush[key] = val;
            }
        }
    });

    // Resolve coord = loc (or fixed coord table) to preview x,y for rendering
    applyFeatureCoordPreview(luaBrush);
    return luaBrush;
}

/**
 * If feature brush has coord (fixed or variable), set x,y for map display.
 * Keeps coord.variable for export. Applies lastMapOrigin for variable/map-relative.
 */
function applyFeatureCoordPreview(brush) {
    if (!brush) return;
    const fromCoord = getXYFromCoord(brush);
    if (!fromCoord) return;

    let x = fromCoord.x;
    let y = fromCoord.y;
    if (fromCoord.variable && lastMapOrigin) {
        x += (lastMapOrigin.x || 0);
        y += (lastMapOrigin.y || 0);
    } else if (!fromCoord.variable && lastMapOrigin &&
               brush.coord && !brush.region_islev) {
        // fixed coord table in map-relative des calls also need origin when
        // placed after des.map — applyMapOriginToBrush handles numeric x,y;
        // coord tables need it here if we set x,y from coord only
        x += (lastMapOrigin.x || 0);
        y += (lastMapOrigin.y || 0);
    }
    brush.x = x;
    brush.y = y;
    if (brush.internal) {
        brush.internal.previewX = x;
        brush.internal.previewY = y;
    }
}

// ---------------------------------------------------------------------------
// des.map placement — mirrors NetHack src/sp_lev.c lspo_map()
// Bare des.map([[...]]) defaults to halign/valign = center.
// Map-relative des.* coords are then offset by lastMapOrigin.
// ---------------------------------------------------------------------------

/** @type {{x:number,y:number,w:number,h:number,halign:string,valign:string}} */
let lastMapOrigin = { x: 0, y: 0, w: 0, h: 0, halign: 'none', valign: 'none' };

/**
 * Split a des.map long-string into rows (drop leading/trailing blank from [[ ]]).
 */
function parseMapLines(mapContent) {
    if (mapContent == null) return [];
    let text = String(mapContent);
    // If raw still includes long-bracket delimiters, strip them
    if (text.startsWith('[[')) {
        text = text.replace(/^\[\[/, '').replace(/\]\]$/, '');
    }
    let lines = text.split(/\r?\n/);
    if (lines.length && lines[0] === '') lines = lines.slice(1);
    if (lines.length && lines[lines.length - 1] === '') lines = lines.slice(0, -1);
    return lines.filter(l => l !== '[[' && l !== ']]');
}

/**
 * Compute map origin like NetHack (maze max + odd-adjust).
 * @param {number} mapW
 * @param {number} mapH
 * @param {{x?:number,y?:number,halign?:string,valign?:string}} opts
 */
function computeMapOrigin(mapW, mapH, opts = {}) {
    const x_maze_max = (COLS - 1) & ~1; // NetHack: (COLNO-1) & ~1 → 78
    const y_maze_max = (ROWS - 1) & ~1; // NetHack: (ROWNO-1) & ~1 → 20

    // Explicit coord wins
    if (opts.x != null && opts.y != null) {
        return {
            x: opts.x,
            y: opts.y,
            w: mapW,
            h: mapH,
            halign: 'none',
            valign: 'none'
        };
    }

    // String-form des.map defaults both to center (sp_lev.c)
    const ha = opts.halign != null ? opts.halign : 'center';
    const va = opts.valign != null ? opts.valign : 'center';

    let ox = 0;
    let oy = 0;

    // Assume level_init already ran (splev_init_present) → left starts at 1
    switch (ha) {
        case 'left':
            ox = 1;
            break;
        case 'half-left':
            ox = 2 + Math.floor((x_maze_max - 2 - mapW) / 4);
            break;
        case 'center':
            ox = 2 + Math.floor((x_maze_max - 2 - mapW) / 2);
            break;
        case 'half-right':
            ox = 2 + Math.floor(((x_maze_max - 2 - mapW) * 3) / 4);
            break;
        case 'right':
            ox = x_maze_max - mapW - 1;
            break;
        default:
            ox = 0;
            break;
    }
    switch (va) {
        case 'top':
            oy = 3;
            break;
        case 'center':
            oy = 2 + Math.floor((y_maze_max - 2 - mapH) / 2);
            break;
        case 'bottom':
            oy = y_maze_max - mapH - 1;
            break;
        default:
            oy = 0;
            break;
    }

    // NetHack forces odd start when using alignment
    if (ha !== 'none' && (ox % 2) === 0) ox++;
    if (va !== 'none' && (oy % 2) === 0) oy++;

    if (oy < 0 || oy + mapH > ROWS) {
        if (mapH >= ROWS) oy = 0;
        else if (oy < 0 || oy + mapH > ROWS) oy = 0;
    }
    if (ox < 0) ox = 0;

    return { x: ox, y: oy, w: mapW, h: mapH, halign: ha, valign: va };
}

/**
 * Offset map-relative x/y (and coord) by lastMapOrigin.
 * Level-absolute brushes (region_islev) are left alone.
 */
function applyMapOriginToBrush(brush) {
    if (!brush) return brush;
    const isLev =
        brush.region_islev === 1 ||
        brush.region_islev === '1' ||
        brush.region_islev === true;
    if (isLev) return brush;

    // Already finalized by applyFeatureCoordPreview (coord → x,y + origin)
    if (brush.internal && brush.internal.previewX != null) return brush;

    const ox = lastMapOrigin.x || 0;
    const oy = lastMapOrigin.y || 0;
    if (!ox && !oy) return brush;

    if (brush.x != null && typeof brush.x === 'number') brush.x += ox;
    if (brush.y != null && typeof brush.y === 'number') brush.y += oy;

    // Do not mutate coord.variable; only fixed numeric coord tables
    if (Array.isArray(brush.coord) && brush.coord.length === 2) {
        if (typeof brush.coord[0] === 'number') brush.coord[0] += ox;
        if (typeof brush.coord[1] === 'number') brush.coord[1] += oy;
    } else if (brush.coord && typeof brush.coord === 'object' &&
               brush.coord.x != null && brush.coord.y != null &&
               !brush.coord.variable) {
        brush.coord.x += ox;
        brush.coord.y += oy;
    }

    // Lighting-style absolute corners if present without region_islev
    if (brush.x1 != null && typeof brush.x1 === 'number') {
        brush.x1 += ox;
        brush.x2 += ox;
        brush.y1 += oy;
        brush.y2 += oy;
    }

    return brush;
}

/**
 * Place map lines into layers.terrain at origin; update lastMapOrigin.
 */
function placeMapContent(lines, originOpts = {}) {
    if (!lines || !lines.length) return;

    const mapH = lines.length;
    const mapW = Math.max(...lines.map(l => l.length), 0);
    const origin = computeMapOrigin(mapW, mapH, originOpts);
    lastMapOrigin = origin;

    for (let ly = 0; ly < mapH; ly++) {
        const gy = origin.y + ly;
        if (gy < 0 || gy >= ROWS) continue;
        const line = lines[ly];
        for (let lx = 0; lx < mapW; lx++) {
            const gx = origin.x + lx;
            if (gx < 0 || gx >= COLS) continue;
            const ch = lx < line.length ? line[lx] : ' ';
            layers.terrain[gy][gx] = symToTerrain[ch] || 'stone';
        }
    }
}

/**
 * Extract map string + placement options from a des.map call's AST args.
 */
function getMapCallSpec(args) {
    if (!args || !args.length) return null;

    // des.map([[...]])  → default center,center
    if (args[0].type === 'StringLiteral') {
        const content = (args[0].value != null)
            ? args[0].value
            : dequote(args[0].raw);
        return {
            lines: parseMapLines(content),
            opts: { halign: 'center', valign: 'center' }
        };
    }

    // des.map({ map=[[...]], x=, y=, coord=, halign=, valign= })
    if (args[0].type === 'TableConstructorExpression') {
        let content = null;
        const opts = { halign: 'none', valign: 'none' };
        let hasAlign = false;
        let hasXY = false;

        for (const field of args[0].fields) {
            if (field.type !== 'TableKeyString') continue;
            const key = field.key.name;
            const val = field.value;

            if (key === 'map' && val.type === 'StringLiteral') {
                content = (val.value != null) ? val.value : dequote(val.raw);
            } else if (key === 'halign' && val.type === 'StringLiteral') {
                opts.halign = dequote(val.raw);
                hasAlign = true;
            } else if (key === 'valign' && val.type === 'StringLiteral') {
                opts.valign = dequote(val.raw);
                hasAlign = true;
            } else if (key === 'x' && val.type === 'NumericLiteral') {
                opts.x = val.value;
                hasXY = true;
            } else if (key === 'y' && val.type === 'NumericLiteral') {
                opts.y = val.value;
                hasXY = true;
            } else if (key === 'coord' && val.type === 'TableConstructorExpression') {
                const nums = val.fields
                    .filter(f => f.type === 'TableValue' && f.value?.type === 'NumericLiteral')
                    .map(f => f.value.value);
                if (nums.length >= 2) {
                    opts.x = nums[0];
                    opts.y = nums[1];
                    hasXY = true;
                }
            }
        }

        if (content == null) return null;
        // Table form with neither xy nor align is invalid in engine; fall back to 0,0
        if (!hasAlign && !hasXY) {
            opts.x = 0;
            opts.y = 0;
            opts.halign = 'none';
            opts.valign = 'none';
        } else if (hasAlign && !hasXY) {
            // keep halign/valign; clear any partial xy
            delete opts.x;
            delete opts.y;
        }
        return { lines: parseMapLines(content), opts };
    }

    return null;
}

function parseLUAtoBrushSimple(args, type)
{
    let luaBrush = {};
    const def = (typeof getFeatureDefByType === 'function') ? getFeatureDefByType(type) : null;
    const internal = def?.internal || {
        type: type || 'feature',
        stroke: 'point',
        brushMode: 'simple',
        des_code: type ? `des.${type}` : 'des.feature'
    };
    luaBrush['internal'] = {...internal};
    luaBrush['internal'].brushMode = "simple";

    if( type == 'stair' || type == 'ladder')
    {
        if( args[0].type != 'StringLiteral' ) return;
        luaBrush['dir'] = dequote(args[0].raw);
        luaBrush['x'] = parseInt(args[1].value);
        luaBrush['y'] = parseInt(args[2].value);
        setStairInternals(luaBrush);
        
    }
    if( (type == 'region' || type == 'non_diggable' ) && args[0].base.base.name == 'selection' && args[0].type == 'CallExpression' )
    {
        const x1 = args[0].arguments[0].value;
        const y1 = args[0].arguments[1].value;
        const x2 = args[0].arguments[2].value;
        const y2 = args[0].arguments[3].value;

        luaBrush['x'] = x1;
        luaBrush['y'] = y1;
        luaBrush['w'] = Math.abs(x1 - x2) + 1;
        luaBrush['h'] = Math.abs(y1 - y2) + 1;

        if( args[1] ?? false )
        {
            const isLit = dequote(args[1].raw);
            luaBrush['x1'] = x1;
            luaBrush['x2'] = x2;
            luaBrush['y1'] = y1;
            luaBrush['y2'] = y2;
            luaBrush['lit'] = isLit == 'lit' ? true : false;
            luaBrush['overlayColor'] = isLit == 'lit' ? LIGHTING_OVERLAY.light : LIGHTING_OVERLAY.dark;
            
        }
        /*layers.lighting.push({
            x1: x1,
            y1: y1,
            x2: x2,
            y2: y2,
            lit: isLit,                                 // boolean for internal use
            overlayColor: isLit ? LIGHTING_OVERLAY.light : LIGHTING_OVERLAY.dark
        });*/
    }
    
    if( type == 'message' )
    {
        if( args[0].type != 'StringLiteral' ) return;
        luaBrush['text'] = dequote(args[0].raw);
        setStairInternals(luaBrush);
        
    }
    return luaBrush;
}

// ---------------------------------------------------------------------------
// Lua locals (level script variables) — shared with map_edit.html
// ---------------------------------------------------------------------------

/** @type {Object.<string, object>} */
let luaLocals = {};
/** @type {Array<object>} ordered ops / opaque snippets for re-export */
let luaOps = [];
let _luaLocalExportOrder = 0;

function resetLuaLocals() {
    luaLocals = {};
    luaOps = [];
    _luaLocalExportOrder = 0;
}

/**
 * Lua is 1-based for array indexes. values is JS 0-based.
 */
function resolveLocalIndex(name, luaIndex) {
    const def = luaLocals[name];
    if (!def || (def.kind !== 'string_list' && def.kind !== 'coord_list')) return null;
    if (typeof luaIndex !== 'number' || !Number.isFinite(luaIndex)) return null;
    const i = luaIndex - 1;
    if (!def.values || i < 0 || i >= def.values.length) return null;
    return def.values[i];
}

/**
 * Parse "monster[1]" / "object[10]" → { name, index } or null.
 */
function parseVariableIndexRef(varStr) {
    if (!varStr || typeof varStr !== 'string') return null;
    const m = varStr.match(/^([A-Za-z_]\w*)\[(\d+)\]$/);
    if (!m) return null;
    return { name: m[1], index: parseInt(m[2], 10) };
}

/**
 * Apply resolved local value onto a monster/object brush for WYSIWYG display.
 * Keeps name.variable for round-trip.
 */
function applyLocalResolveToBrush(brush, kindHint /* 'monster'|'object' */) {
    if (!brush) return brush;
    const varRef = brush.name && typeof brush.name === 'object' ? brush.name.variable : null;
    if (!varRef) return brush;

    const parsed = parseVariableIndexRef(varRef);
    if (!parsed) return brush;

    const val = resolveLocalIndex(parsed.name, parsed.index);
    if (val == null) return brush;

    if (typeof val === 'string') {
        // Single-char → class; multi-char → id
        if (val.length === 1) {
            brush.class = val;
            brush.internal = brush.internal || {};
            brush.internal.symbol = val;
            brush.internal.random = false;
            brush.internal.resolvedFrom = varRef;
            if (kindHint === 'monster' && typeof getMonsterById === 'function') {
                // class char — try optional color from first matching mon if available later
            }
        } else {
            brush.id = val;
            brush.internal = brush.internal || {};
            brush.internal.random = false;
            brush.internal.resolvedFrom = varRef;
            if (kindHint === 'monster' && typeof getMonsterById === 'function') {
                const mon = getMonsterById(val);
                if (mon) {
                    brush.internal.symbol = mon.symbol;
                    brush.internal.color = mon.color;
                }
            } else if (kindHint === 'object' && typeof getObjectById === 'function') {
                const obj = getObjectById(val);
                if (obj) {
                    brush.internal.symbol = obj.symbol;
                    brush.internal.color = obj.color;
                }
            } else {
                brush.internal.symbol = val.charAt(0);
            }
        }
    } else if (Array.isArray(val) && val.length === 2) {
        // coord pair from coord_list — rarely used as monster id, store for info
        brush.internal = brush.internal || {};
        brush.internal.resolvedCoord = val;
        brush.internal.resolvedFrom = varRef;
    }
    return brush;
}

/**
 * Try to classify a TableConstructorExpression into string_list or coord_list.
 * Returns { kind, values } or null.
 */
function classifyLocalTable(tableNode) {
    if (!tableNode || tableNode.type !== 'TableConstructorExpression') return null;
    const fields = tableNode.fields || [];
    if (!fields.length) return { kind: 'string_list', values: [] };

    const stringVals = [];
    const coordVals = [];
    let allString = true;
    let allCoord = true;

    for (const f of fields) {
        if (f.type === 'TableValue') {
            const v = f.value;
            if (v.type === 'StringLiteral') {
                stringVals.push(dequote(v.raw));
                allCoord = false;
            } else if (v.type === 'NumericLiteral') {
                stringVals.push(String(v.value));
                allCoord = false;
            } else if (v.type === 'TableConstructorExpression') {
                allString = false;
                const nums = (v.fields || [])
                    .filter(ff => ff.type === 'TableValue' && ff.value?.type === 'NumericLiteral')
                    .map(ff => ff.value.value);
                if (nums.length >= 2) {
                    coordVals.push([nums[0], nums[1]]);
                } else {
                    allCoord = false;
                }
            } else {
                allString = false;
                allCoord = false;
            }
        } else {
            allString = false;
            allCoord = false;
        }
    }

    if (allString && stringVals.length === fields.length) {
        return { kind: 'string_list', values: stringVals };
    }
    if (allCoord && coordVals.length === fields.length) {
        return { kind: 'coord_list', values: coordVals };
    }
    return null;
}

function registerLuaLocal(name, def) {
    def.name = name;
    def.exportOrder = _luaLocalExportOrder++;
    if (def.shuffled == null) def.shuffled = false;
    luaLocals[name] = def;
    luaOps.push({ type: 'local', name });
}

/**
 * Handle LocalStatement — returns true if consumed.
 */
function ingestLocalStatement(stmt) {
    if (!stmt || stmt.type !== 'LocalStatement') return false;
    const vars = stmt.variables || [];
    const inits = stmt.init || [];

    // Only handle simple one-name locals for structured kinds; multi → opaque
    if (vars.length !== 1) {
        const src = getCodeStringFromLUAStmt(stmt);
        registerLuaLocal(vars.map(v => v.name).join('_'), {
            kind: 'opaque',
            source: src,
            shuffled: false
        });
        return true;
    }

    const name = vars[0].name;
    const init = inits[0];

    if (!init) {
        registerLuaLocal(name, { kind: 'opaque', source: `local ${name}`, shuffled: false });
        return true;
    }

    // selection.new()
    if (init.type === 'CallExpression' &&
        init.base?.type === 'MemberExpression' &&
        init.base.base?.name === 'selection' &&
        init.base.identifier?.name === 'new') {
        registerLuaLocal(name, {
            kind: 'selection',
            points: [],
            methods: [],
            shuffled: false
        });
        return true;
    }

    // place:rndcoord(N) → structured link to selection for preview
    if (init.type === 'CallExpression' &&
        init.base?.type === 'MemberExpression' &&
        init.base.indexer === ':' &&
        init.base.identifier?.name === 'rndcoord' &&
        init.base.base?.type === 'Identifier') {
        const from = init.base.base.name;
        let n = 1;
        if (init.arguments?.[0]?.type === 'NumericLiteral') {
            n = init.arguments[0].value;
        }
        registerLuaLocal(name, {
            kind: 'rndcoord_ref',
            from,
            n,
            shuffled: false
        });
        return true;
    }

    // other method calls → opaque
    if (init.type === 'CallExpression' && init.base?.type === 'MemberExpression') {
        const src = getCodeStringFromLUAStmt(stmt);
        registerLuaLocal(name, { kind: 'opaque', source: src, shuffled: false });
        return true;
    }

    // Table literals
    if (init.type === 'TableConstructorExpression') {
        const classified = classifyLocalTable(init);
        if (classified) {
            registerLuaLocal(name, {
                kind: classified.kind,
                values: classified.values,
                shuffled: false
            });
            return true;
        }
        const src = getCodeStringFromLUAStmt(stmt);
        registerLuaLocal(name, { kind: 'opaque', source: src, shuffled: false });
        return true;
    }

    // String / number literals
    if (init.type === 'StringLiteral') {
        registerLuaLocal(name, { kind: 'string', value: dequote(init.raw), shuffled: false });
        return true;
    }
    if (init.type === 'NumericLiteral') {
        registerLuaLocal(name, { kind: 'number', value: init.value, shuffled: false });
        return true;
    }

    // Fallback opaque
    const src = getCodeStringFromLUAStmt(stmt);
    registerLuaLocal(name, { kind: 'opaque', source: src, shuffled: false });
    return true;
}

/**
 * Handle non-des CallStatement: shuffle(x), place:set(...), etc.
 * Returns true if consumed (should not go to layers.code as generic).
 */
function ingestNonDesCall(expr) {
    if (!expr || expr.type !== 'CallExpression') return false;

    // shuffle(ident)
    if (expr.base?.type === 'Identifier' && expr.base.name === 'shuffle') {
        const arg = expr.arguments?.[0];
        if (arg?.type === 'Identifier' && luaLocals[arg.name]) {
            luaLocals[arg.name].shuffled = true;
            luaOps.push({ type: 'shuffle', name: arg.name });
            return true;
        }
        // unknown shuffle — still record
        if (arg?.type === 'Identifier') {
            luaOps.push({ type: 'shuffle', name: arg.name });
            return true;
        }
        return false;
    }

    // place:set(x, y)  MemberExpression with indexer :
    if (expr.base?.type === 'MemberExpression' &&
        expr.base.indexer === ':' &&
        expr.base.identifier?.name === 'set' &&
        expr.base.base?.type === 'Identifier') {
        const selName = expr.base.base.name;
        const def = luaLocals[selName];
        if (def && def.kind === 'selection') {
            const a0 = expr.arguments?.[0];
            const a1 = expr.arguments?.[1];
            if (a0?.type === 'NumericLiteral' && a1?.type === 'NumericLiteral') {
                def.points.push([a0.value, a1.value]);
                def.methods.push({ op: 'set', args: [a0.value, a1.value] });
                luaOps.push({ type: 'method', name: selName, op: 'set', args: [a0.value, a1.value] });
                return true;
            }
        }
    }

    return false;
}

/**
 * Emit Lua source for all tracked locals + ops (for save / luadef).
 */
function generateLocalsLua() {
    const lines = [];
    const emitted = new Set();

    // Prefer export order from luaOps for interleaving shuffle/methods with locals
    for (const op of luaOps) {
        if (op.type === 'local') {
            const def = luaLocals[op.name];
            if (!def || emitted.has(op.name)) continue;
            emitted.add(op.name);
            lines.push(formatLocalDefLua(def));
        } else if (op.type === 'shuffle') {
            lines.push(`shuffle(${op.name})`);
        } else if (op.type === 'method' && op.op === 'set') {
            const [x, y] = op.args;
            lines.push(`${op.name}:set(${String(x).padStart(2, '0')},${String(y).padStart(2, '0')});`);
        }
    }

    // Any locals not in luaOps
    Object.keys(luaLocals).forEach(name => {
        if (emitted.has(name)) return;
        lines.push(formatLocalDefLua(luaLocals[name]));
        if (luaLocals[name].shuffled) lines.push(`shuffle(${name})`);
    });

    return lines.filter(Boolean).join('\n');
}

function formatLocalDefLua(def) {
    if (!def) return '';
    if (def.kind === 'opaque' && def.source) {
        return def.source.endsWith(';') ? def.source : def.source;
    }
    if (def.kind === 'string_list') {
        const body = (def.values || []).map(v => {
            if (typeof v !== 'string') return String(v);
            // escape quotes
            const esc = v.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
            return `"${esc}"`;
        }).join(', ');
        return `local ${def.name} = { ${body} };`;
    }
    if (def.kind === 'coord_list') {
        const body = (def.values || []).map(pair => {
            const x = String(pair[0]).padStart(2, '0');
            const y = String(pair[1]).padStart(2, '0');
            return `{${x},${y}}`;
        }).join(',');
        return `local ${def.name} = { ${body} };`;
    }
    if (def.kind === 'selection') {
        return `local ${def.name} = selection.new();`;
    }
    if (def.kind === 'rndcoord_ref') {
        const n = def.n != null ? def.n : 1;
        return `local ${def.name} = ${def.from}:rndcoord(${n});`;
    }
    if (def.kind === 'string') {
        const esc = String(def.value).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
        return `local ${def.name} = "${esc}";`;
    }
    if (def.kind === 'number') {
        return `local ${def.name} = ${def.value};`;
    }
    return def.source || `local ${def.name};`;
}

function loadLUAMap(luaText) {
    if (!luaText) return;

    // Initialize layers with default 'stone' terrain
    layers.terrain = Array.from({length: ROWS}, () => Array(COLS).fill('stone'));
    layers.monster = Array.from({length: ROWS}, () => Array(COLS).fill(null));
    layers.object = Array.from({length: ROWS}, () => Array(COLS).fill(null));
    layers.lighting = [];
    layers.features = [];
    layers.code = [];
    layers.objectRND = [];
    layers.monsterRND = [];

    // Reset map origin — updated by des.map (bare string form centers like NetHack)
    lastMapOrigin = { x: 0, y: 0, w: 0, h: 0, halign: 'none', valign: 'none' };
    resetLuaLocals();

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

            // Local variables
            if (stmt.type === 'LocalStatement') {
                ingestLocalStatement(stmt);
                continue;
            }

            //Handle if it's a line of code we can't process
            if (stmt.type !== 'CallStatement') {
                const codeLine = getCodeStringFromLUAStmt(stmt);
                layers.code.push(codeLine);
                continue;
            }
            if (stmt.type === "CallStatement") {
                const expr = stmt.expression;
                if (!isDesCall(expr)) {
                    // shuffle / selection methods / etc.
                    if (ingestNonDesCall(expr)) continue;
                    const codeLine = getCodeStringFromLUAStmt(stmt);
                    layers.code.push(codeLine);
                    continue;
                } 
            }

            const call = stmt.expression;
            if (call.base.type !== 'MemberExpression' || call.base.base.name !== 'des') continue;

            const method = call.base.identifier.name;
            const args = call.arguments || [];

            switch (method) {
                case 'level_init':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const initDefs = brushOptionDefs.level.level_init;
                        currentBrushGlobal['level_init'] = {};

                        args[0].fields.forEach(  field => {
                            
                            const key = field.key.name;
                            const raw = dequote(field.value.raw);
                            const def = initDefs[key];
                            const dataType = def.data_type ? def.data_type : 'null';
                            let value = null;

                            if (dataType == "int") 
                            {
                                value = parseInt(raw, 10);
                            } 
                            else if ( dataType == "bool" )
                            {
                                value = Boolean(raw);
                            }
                            else if ( dataType == "string" )
                            {
                                value = String(raw);
                            }

                            currentBrushGlobal['level_init'][key] = value;
                        });

                        // Prefill whole level with bg (e.g. mazegrid "-") so centered
                        // maps sit on the correct backdrop like in-game.
                        const bgSym = currentBrushGlobal['level_init'].bg;
                        if (bgSym != null && bgSym !== '') {
                            const terrKey = symToTerrain[bgSym] || symToTerrain[String(bgSym)] || null;
                            if (terrKey) {
                                for (let y = 0; y < ROWS; y++) {
                                    for (let x = 0; x < COLS; x++) {
                                        layers.terrain[y][x] = terrKey;
                                    }
                                }
                            }
                        }
                        
                        break;
                    }
                    

                case 'level_flags':
                    {
                        currentBrushGlobal['level_flags'] = [];
                        args.forEach( arg => {
                            if (arg?.type === 'StringLiteral') {
                                key = dequote(arg.raw);
                                currentBrushGlobal['level_flags'].push(key);
                                //initState.flags[key] = true;
                        }

                        });
                        
                        break;
                    }

                case 'map':
                    {
                        const spec = getMapCallSpec(args);
                        if (spec && spec.lines.length) {
                            placeMapContent(spec.lines, spec.opts);
                        }
                        break;
                    }

                case 'region':
                    {
                        if (args[0]?.type == 'TableConstructorExpression')
                        {
                            const luaBrush = parseLUAtoBrush( args, method );
                        
                            if( luaBrush.internal.type == 'region')
                            {
                                setRoomDitherColor(luaBrush);
                            }

                            applyMapOriginToBrush(luaBrush);
                            layers.features.push(luaBrush);
                            break;
                        }
                        else if (args[0]?.type == 'CallExpression')
                        {
                            const luaBrush = parseLUAtoBrushSimple( args, method );
                            applyMapOriginToBrush(luaBrush);
                            // lighting rects use x1/y1/x2/y2 after apply
                            if (luaBrush.x1 != null) {
                                layers.lighting.push(luaBrush);
                            } else {
                                layers.features.push(luaBrush);
                            }
                        }
                        break;
                        
                    }

                case 'room':
                    if (args[0]?.type !== 'TableConstructorExpression') break;
                    
                    {
                        const room = args[0];
                        let lit = false;
                        let roomX1, roomY1, roomX2, roomY2;

                        let roomW = 0, roomH = 0, roomX = 0, roomY = 0;
                        let xAlign = '', yAlign = '', roomType = '';
                        
                        // getFeatureDefByType('room') may be missing — Room menu entry
                        // often uses internal.type 'feature', not 'room'
                        const roomDef = (typeof getFeatureDefByType === 'function')
                            ? getFeatureDefByType('room')
                            : null;
                        const roomInternal = structuredClone(roomDef?.internal || {
                            type: 'room',
                            des_code: 'des.room',
                            stroke: 'rectangle',
                            brushMode: 'complex',
                            color: 'CLR_GREEN',
                            dither: 'crosshatch',
                            ditherColor: 'CLR_GREEN',
                            is_xy_possible: true,
                            is_rnd_possible: false
                        });
                        roomInternal.type = 'room';
                        roomInternal.des_code = roomInternal.des_code || 'des.room';
                        let luaBrush = {};
                        let contents = {};
                        luaBrush['internal'] = roomInternal;


                        for (const field of room.fields) {
                            const key = field.key.name;
                            const val = field.value;

                            if (key === 'lit' && val.value === 1) luaBrush['lit'] = true;
                            if (key === 'region' && val.type === 'TableConstructorExpression' && val.fields.length === 4) {
                                roomX1 = val.fields[0].value.value;
                                roomY1 = val.fields[1].value.value;
                                roomX2 = val.fields[2].value.value;
                                roomY2 = val.fields[3].value.value;
                                luaBrush['x'] = roomX1;
                                luaBrush['y'] = roomX1;
                                luaBrush['w'] = roomX1 - roomX2;
                                luaBrush['h'] = roomY1 - roomY2;

                            }
                            if (key === 'x') luaBrush['x'] = val.value;
                            if (key === 'y') luaBrush['y'] = val.value;
                            if (key === 'w') luaBrush['w'] = val.value;
                            if (key === 'h') luaBrush['h'] = val.value;
                            if (key === 'xalign') luaBrush['xalign'] = dequote(val.raw);
                            if (key === 'yalign') luaBrush['yalign'] = dequote(val.raw);
                            if (key === 'type')  luaBrush['type'] = dequote(val.raw);
                            if (key === 'contents')  contents = field.value;
                        }

                        if (contents && contents.type === "FunctionDeclaration" && contents.body) {
                            luaBrush.contents = [];
                            for (const stmt of contents.body) {
                                if (stmt.type !== "CallStatement") continue;
                                const expr = stmt.expression;
                                if (expr.type !== "CallExpression") continue;

                                if (!expr.base ||
                                    expr.base.type !== "MemberExpression" ||
                                    expr.base.identifier.name !== "object" ||
                                    !expr.base.base ||
                                    expr.base.base.name !== "des") {
                                    continue;
                                }

                                const innerBrush = getObjectBrushFromLUAObj(expr);
                                if (innerBrush) {
                                    luaBrush.contents.push(innerBrush);
                                }
                            }
                        }

                        

                        if(luaBrush) layers.features.push(luaBrush);
                        
                        break;
                    }
                case 'feature':
                    {
                        // Table form: des.feature({ type=..., x=..., y=... })
                        if (args[0]?.type === 'TableConstructorExpression') {
                            const luaBrush = parseLUAtoBrush( args, method );
                            setFeatureInternals(luaBrush);
                            applyMapOriginToBrush(luaBrush);
                            layers.features.push(luaBrush);
                            break;
                        }
                        // Simple form: des.feature("fountain", 10, 08)
                        if (args[0]?.type === 'StringLiteral' &&
                            args[1]?.type === 'NumericLiteral' &&
                            args[2]?.type === 'NumericLiteral') {
                            const featType = dequote(args[0].raw);
                            let luaBrush = {
                                type: featType,
                                x: args[1].value,
                                y: args[2].value,
                                internal: structuredClone(
                                    (typeof getFeatureDefByType === 'function' && getFeatureDefByType(featType)?.internal) ||
                                    (typeof getFeatureDefByType === 'function' && getFeatureDefByType('feature')?.internal) ||
                                    { type: 'feature', stroke: 'point', symbol: '{', color: 'CLR_BLUE' }
                                )
                            };
                            if (typeof setFeatureInternals === 'function') setFeatureInternals(luaBrush);
                            applyMapOriginToBrush(luaBrush);
                            layers.features.push(luaBrush);
                        }
                        break;
                    }
                    
                case 'ladder':
                case 'stair':
                    {
                        if ( args[0].type != 'StringLiteral' ) return;
                        const luaBrush = parseLUAtoBrushSimple(args, method);
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }

                case 'altar':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }


                case 'door':
                    {
                        // Table form
                        if (args[0]?.type === 'TableConstructorExpression') {
                            const luaBrush = parseLUAtoBrush( args, method );
                            applyMapOriginToBrush(luaBrush);
                            layers.features.push(luaBrush);
                            break;
                        }
                        // Simple form: des.door("closed", 07, 03)
                        if (args[0]?.type === 'StringLiteral' &&
                            args[1]?.type === 'NumericLiteral' &&
                            args[2]?.type === 'NumericLiteral') {
                            const doorInternal =
                                (typeof getFeatureDefByType === 'function' && getFeatureDefByType('door')?.internal) ||
                                { type: 'door', stroke: 'point', symbol: '+', color: 'CLR_BROWN', des_code: 'des.door' };
                            const luaBrush = {
                                state: dequote(args[0].raw),
                                x: args[1].value,
                                y: args[2].value,
                                internal: structuredClone(doorInternal)
                            };
                            applyMapOriginToBrush(luaBrush);
                            layers.features.push(luaBrush);
                        }
                        break;
                    }

                case 'object':
                    {
                        const luaBrush = getObjectBrushFromLUAObj(call);
                        if (!luaBrush) break;
                        applyLocalResolveToBrush(luaBrush, 'object');
                        // Fixed x,y get map origin; variable coords resolved in placeBrushWithCoords
                        if (!(luaBrush.coord && luaBrush.coord.variable)) {
                            applyMapOriginToBrush(luaBrush);
                        }
                        placeBrushWithCoords(luaBrush, 'object');
                    }
                    
                    break;

                case 'monster':

                    {
                        let luaBrush = getMonsterBrushFromLUAObj( call );
                        if (!luaBrush) break;
                        applyLocalResolveToBrush(luaBrush, 'monster');
                        if (!(luaBrush.coord && luaBrush.coord.variable)) {
                            applyMapOriginToBrush(luaBrush);
                        }
                        placeBrushWithCoords(luaBrush, 'monster');
                    }
                    
                    break;
                case 'trap':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        setTrapInternals(luaBrush);
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                    
                case 'gold':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'engraving':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        // applyFeatureCoordPreview already set x,y (+ origin) when coord present
                        if (!luaBrush.coord) {
                            applyMapOriginToBrush(luaBrush);
                        }
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'grave':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'teleport_region':
                    {
                        // Usually region_islev=1 → level-absolute; applyMapOriginToBrush no-ops then
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'non_diggable':
                    {
                        if (args[0]?.type !== 'CallExpression') break;
                        const luaBrush = parseLUAtoBrushSimple( args, method );
                        applyMapOriginToBrush(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'message':
                    {
                        if (args[0]?.type !== 'StringLiteral') break;
                        
                        const luaBrush = parseLUAtoBrushSimple( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }
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