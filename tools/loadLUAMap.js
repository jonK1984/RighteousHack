// loadLUAMap.js
// Loader for NetHack .lua des files into the map editor
// Only deterministic top-level des. calls are processed.
// Uses allMonsters, allObjects, allTerrains, and the features array (from feature_def.js) for accurate symbol lookup.

//const COLS = 80;
//const ROWS = 21;

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
 * Extract fixed x,y coordinates from a brush's .coord property.
 * Returns { x: number, y: number } if coord is a fixed array/table of two numbers.
 * Returns null if coord is missing, a variable reference, or invalid format.
 *
 * @param {Object} brush - the monster or object brush
 * @returns {{x: number, y: number}|null}
 */
function getXYFromCoord(brush) {
    if (!brush || !brush.coord) {
        return null;
    }

    const coord = brush.coord;

    // Variable reference → cannot resolve to fixed coords
    if (coord.variable) {
        return null;
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

        // Contents – recursive
        if (fields.contents && fields.contents.type === "FunctionDeclaration" && fields.contents.body) {
            brush.contents = [];
            for (const stmt of fields.contents.body) {
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
                    brush.contents.push(innerBrush);
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

        // object[N] reference
        if (firstArg.type === "IndexExpression" &&
            firstArg.base && firstArg.base.name === "object" &&
            firstArg.index && firstArg.index.type === "NumericLiteral") {

            const varRef = `object[${firstArg.index.value}]`;
            brush.name = { variable: varRef };
            brush.internal.random = false;
            argIdx++;
        }
        // String literal (id or class)
        else if (firstArg.type === "StringLiteral") {
            const str = dequote(firstArg.raw);
            const obj = getObjectById(str);
            if (obj) {
                brush.internal.symbol = obj.symbol;
                brush.internal.color = obj.color;
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
    const internal = getFeatureDefByType(type).internal;
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
        else if (arg?.type == 'TableKeyString' && arg?.value?.raw)
        {
            const key = arg.key.name;
            let val = dequote(arg?.value?.raw);
            if( key == 'x' || key == 'y') val = parseInt(val);
            luaBrush[key] = val
            
        }
    });
    return luaBrush;

}

function parseLUAtoBrushSimple(args, type)
{
    let luaBrush = {};
    const internal = getFeatureDefByType(type).internal;
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

function loadLUAMap(luaText) {
    if (!luaText) return;

    // Initialize layers with default 'stone' terrain
    layers.terrain = Array.from({length: ROWS}, () => Array(COLS).fill('stone'));
    layers.monster = Array.from({length: ROWS}, () => Array(COLS).fill(null));
    layers.lighting = [];
    layers.features = [];
    layers.code = [];
    layers.objectRND = [];
    layers.monsterRND = [];

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

            //Handle if it's a line of code we can't process
            if (stmt.type !== 'CallStatement') {
                const codeLine = getCodeStringFromLUAStmt(stmt);
                layers.code.push(codeLine);
                continue;
            }
            if (stmt.type === "CallStatement") {
                const expr = stmt.expression;
                if (!isDesCall(expr)) {
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
                        })
                        
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
                    if (args[0]?.type === 'StringLiteral' && args[0].raw.startsWith('[[')) {
                        const mapContent = dequote(args[0].raw); // Clean content without [[ ]]
                        const lines = mapContent.split(/\r?\n/);

                        let y = 0;
                        for (let line of lines) {
                            if( line == '[[' || line == ']]') continue;
                            if (y >= ROWS) break;
                            //line = line.replace(/^\|?/, ''); // Optional leading |
                            for (let x = 0; x < COLS; x++) {
                                const ch = x < line.length ? line[x] : ' ';
                                layers.terrain[y][x] = symToTerrain[ch] || 'stone';
                            }
                            y++;
                        }
                    }
                    break;

                case 'region':
                    {
                        if (args[0]?.type == 'TableConstructorExpression')
                        {
                            const luaBrush = parseLUAtoBrush( args, method );
                        
                            if( luaBrush.internal.type == 'region')
                            {
                                setRoomDitherColor(luaBrush);
                            }

                            layers.features.push(luaBrush);
                            break;
                        }
                        else if (args[0]?.type == 'CallExpression')
                        {
                            const luaBrush = parseLUAtoBrushSimple( args, method );
                            layers.lighting.push(luaBrush);
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
                        
                        const roomInternal = getFeatureDefByType('room').internal;
                        let luaBrush = {};
                        let contents = {};
                        luaBrush['internal'] = structuredClone(roomInternal);


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
                        
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        setFeatureInternals(luaBrush);
                        layers.features.push(luaBrush);

                        break;
                    }
                    
                case 'ladder':
                case 'stair':
                    {
                        if ( args[0].type != 'StringLiteral' ) return;
                        const luaBrush = parseLUAtoBrushSimple(args, method);
                        layers.features.push(luaBrush);
                        break;
                    }

                case 'altar':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }


                case 'door':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }

                case 'object':
                    {
                        const luaBrush = getObjectBrushFromLUAObj(call);
                        
                        if (luaBrush.y < ROWS && luaBrush.x < COLS) 
                        {
                            const x = luaBrush.x;
                            const y = luaBrush.y;
                            layers.object[y][x] = luaBrush;
                        }
                        else
                        {
                            layers.objectRND.push(luaBrush);
                        }
                    }
                    
                    break;

                case 'monster':

                    {


                        let luaBrush = getMonsterBrushFromLUAObj( call );
                        const fixedCoords = getXYFromCoord( luaBrush );
                        const x = fixedCoords?.x != null ? fixedCoords.x : ( luaBrush?.x != null ? luaBrush.x : null );
                        const y = fixedCoords?.y != null ? fixedCoords.y : ( luaBrush?.y != null ? luaBrush.y : null );

                        if (y < ROWS && x < COLS && x != null && y != null) 
                        {
                        
                            layers.monster[y][x] = luaBrush;
                        }
                        else
                        {
                            layers.monsterRND.push(luaBrush);
                        }
                    }
                    
                    break;
                case 'trap':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        setTrapInternals(luaBrush);
                        layers.features.push(luaBrush);
                        break;
                    }
                    
                case 'gold':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'engraving':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'grave':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'teleport_region':
                    {
                        if (args[0]?.type !== 'TableConstructorExpression') break;
                        const luaBrush = parseLUAtoBrush( args, method );
                        layers.features.push(luaBrush);
                        break;
                    }
                case 'non_diggable':
                    {
                        if (args[0]?.type !== 'CallExpression') break;
                        const luaBrush = parseLUAtoBrushSimple( args, method );
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