const brushOptionDefs = {
    monster: {
        id:          { label: "Monster ID",           input_type: "text",   data_type: "string", no_coexist: ["class"],  desc: "Monster ID" },
        class:       { label: "Monster class",        input_type: "text",   data_type: "string", no_coexist: ["id"],  desc: "Monster Class" },
        peaceful:    { label: "Peaceful",             input_type: "combo",  data_type: "int", combo_options: [0,1],  desc: "Peaceful" },
        asleep:      { label: "Asleep",               input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Asleep" },
        name:        { label: "Custom name",          input_type: "text",  data_type: "string", desc: "Custom name" },
        female:      { label: "Female",               input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Female" },
        invisible:   { label: "Invisible",            input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Invisible" },
        cancelled:   { label: "Cancelled",            input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Cancelled" },
        revived:     { label: "Revived",              input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Revived" },
        avenge:      { label: "Avenge",               input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Avenge" },
        fleeing:     { label: "Fleeing (turns)",      input_type: "number", data_type: "int", desc: "Fleeing (turns)", min: 0 },
        blinded:     { label: "Blinded (turns)",      input_type: "number", data_type: "int", desc: "Blinded (turns)",min: 0 },
        paralyzed:   { label: "Paralyzed (turns)",    input_type: "number", data_type: "int", desc: "Paralyzed (turns)",min: 0 },
        stunned:     { label: "Stunned",              input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Stunned" },
        confused:    { label: "Confused",             input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Confused" },
        waiting:     { label: "Waiting",              input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Waiting" },
        ignorewater: { label: "Ignore water",         input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Ignore water" },
        countbirth:  { label: "Count birth",          input_type: "combo", data_type: "int", combo_options: ["0","1"],  desc: "Count birth" },
        appear_as:   { label: "Appear as (string)",   input_type: "text", data_type: "string",  desc: "Appear as" }
    },

    object: {
        id:          { label: "Object ID",            input_type: "text",   data_type: "string", no_coexist: ["class"] },
        class:       { label: "Object Class",         input_type: "text",   data_type: "string", no_coexist: ["id"] },
        quantity:    { label: "Quantity",             input_type: "number", data_type: "int", min: -1 }, // -1 = random
        spe:         { label: "Charges",              input_type: "number", data_type: "int" },
        buc:         { label: "BUC State",            input_type: "combo", data_type: "string", combo_options: [ "uncursed", "blessed",  "cursed", "not-cursed"] },  // e.g. "blessed", "uncursed", "cursed"
        name:        { label: "Custom Name",          input_type: "text", data_type: "string" },
        buried:      { label: "Buried",               input_type: "combo", data_type: "int", combo_options: ["0","1"] },
        lit:         { label: "Lit (lamp, etc.)",     input_type: "combo", data_type: "int", combo_options: ["0","1"] },
        eroded:      { label: "Eroded Level",         input_type: "number", data_type: "int", min: 0 },
        locked:      { label: "Locked",               input_type: "number", data_type: "int", min: -1 }, // -1 = random, 0 = no, 1 = yes
        trapped:     { label: "Trapped",              input_type: "number", data_type: "int", min: -1 }, // -1 = random, 0 = no, 1 = yes
        trap_known:  { label: "Trap Known",           input_type: "number", data_type: "int", min: -1 }, // -1 = random, 0 = no, 1 = yes
        recharged:   { label: "Recharged Count",      input_type: "number",data_type: "int",  min: 0 },
        greased:     { label: "Greased",              input_type: "combo", data_type: "int", combo_options: ["0","1"] },
        broken:      { label: "Broken",               input_type: "combo", data_type: "bool", combo_options: ["true","false"] },
        achievement: { label: "Achievement Tracker",  input_type: "combo", data_type: "int", combo_options: ["0","1"] },

        // Corpse / statue specific flags
        corpsenm:    { label: "Corpse Monster ID",    input_type: "text",  data_type: "string"},  // monster ID if this object is a corpse/statue
        historic:    { label: "Historic (statue)",    input_type: "combo", data_type: "bool",  combo_options: ["true","false"] },
        male:        { label: "Male (statue)",        input_type: "combo", data_type: "int", combo_options: ["0","1"] },
        female:      { label: "Female (statue)",      input_type: "combo", data_type: "int", combo_options: ["0","1"] }
    },

    level: {
        tabs: [
            { desc: "Level Initialization", key: "level_init" },
            { desc: "Level Flags", key: "level_flags" }
        ],

        level_init: {
            style:     { label: "style",     input_type: "combo", data_type: "string", combo_options: ["solidfill","mazegrid","maze","rogue","mines","swamp"], desc: "Map generation style" },
            fg:        { label: "fg",        input_type: "combo", data_type: "string", combo_options: terrainLuaSymbols, desc: "Foreground terrain symbol" },
            bg:        { label: "bg",        input_type: "combo", data_type: "string", combo_options: terrainLuaSymbols, desc: "Background terrain symbol" },
            smoothed:  { label: "smoothed",  input_type: "combo", data_type: "bool", combo_options: ["true","false"], desc: "Smooth corners" },
            joined:    { label: "joined",    input_type: "combo", data_type: "bool", combo_options: ["true","false"], desc: "Join rooms to corridors" },
            lit:       { label: "lit",       input_type: "combo", data_type: "int", combo_options: ["0","1"], desc: "0 = unlit, 1 = lit" },
            walled:    { label: "walled",    input_type: "combo", data_type: "bool", combo_options: ["true","false"], desc: "Surround with walls" },
            corrwid:   { label: "corrwid",   input_type: "combo", data_type: "int", combo_options: [1,2,3,4,5,6], desc: "Corridor width" },
            wallthick: { label: "wallthick", input_type: "combo", data_type: "int", combo_options: [1,2,3,4,5,6], desc: "Wall thickness" },
            deadends:  { label: "deadends",  input_type: "combo", data_type: "bool", combo_options: ["true","false"], desc: "Allow dead-end corridors" }
        },

        level_flags: {
            noteleport:    { label: "noteleport",    input_type: "check", data_type: "exist", desc: "Prevents teleporting" },
            hardfloor:     { label: "hardfloor",     input_type: "check", data_type: "exist", desc: "Prevents digging down" },
            nommap:        { label: "nommap",        input_type: "check", data_type: "exist", desc: "Prevents magic mapping" },
            shortsighted:  { label: "shortsighted",  input_type: "check", data_type: "exist", desc: "Monsters have limited sight" },
            arboreal:      { label: "arboreal",      input_type: "check", data_type: "exist", desc: "Outdoor map (stone → trees)" },
            mazelevel:     { label: "mazelevel",     input_type: "check", data_type: "exist", desc: "Treat as maze level" },
            shroud:        { label: "shroud",        input_type: "check", data_type: "exist", desc: "Unseen areas stay blank" },
            graveyard:     { label: "graveyard",     input_type: "check", data_type: "exist", desc: "Graveyard effects" },
            icedpools:     { label: "icedpools",     input_type: "check", data_type: "exist", desc: "Ice → frozen pools" },
            corrmaze:      { label: "corrmaze",      input_type: "check", data_type: "exist", desc: "Corridor maze style" },
            premapped:     { label: "premapped",     input_type: "check", data_type: "exist", desc: "Reveal map on entry" },
            sokoban:       { label: "sokoban",       input_type: "check", data_type: "exist", desc: "Sokoban rules" },
            solidify:      { label: "solidify",      input_type: "check", data_type: "exist", desc: "Outside map undiggable" },
            inaccessibles: { label: "inaccessibles", input_type: "check", data_type: "exist", desc: "Connect inaccessible areas" },
            noflip:        { label: "noflip",        input_type: "check", data_type: "exist", desc: "Prevent any flipping" },
            noflipx:       { label: "noflipx",       input_type: "check", data_type: "exist", desc: "Prevent horizontal flip" },
            noflipy:       { label: "noflipy",       input_type: "check", data_type: "exist", desc: "Prevent vertical flip" },
            nomongen:      { label: "nomongen",      input_type: "check", data_type: "exist", desc: "No random monster generation" },
            nodeathdrops:  { label: "nodeathdrops",  input_type: "check", data_type: "exist", desc: "Monsters drop no corpses/items" },
            fumaroles:     { label: "fumaroles",     input_type: "check", data_type: "exist", desc: "Lava emits poison gas" },
            stormy:        { label: "stormy",        input_type: "check", data_type: "exist", desc: "Clouds generate lightning" }
        }
    },

    features: allFeatureMenuOptions
    
    
    // inventory is handled separately
};

document.getElementById("monster-inventory-list").innerHTML = "";
/*
document.getElementById("show-inventory-btn").onclick = () => {
    // reuse the existing object popup logic
    openObjectPopup((objBrush) => {
        currentMonsterInventory.push(objBrush);
        renderMonsterInventoryList();
    });
};*/

function renderMonsterInventoryList() {
    const list = document.getElementById("monster-inventory-list");
    list.innerHTML = "";

    currentMonsterInventory.forEach((inv, idx) => {
        const item = document.createElement("div");
        item.className = "inventory-item";

        const symSpan = document.createElement("span");
        symSpan.className = "sym";
        symSpan.textContent = inv.internal.symbol || "?";
        if (inv.internal.color && colorTable[inv.internal.color]) {
            symSpan.style.color = colorTable[inv.internal.color].desc;
        }

        const nameSpan = document.createElement("span");
        nameSpan.textContent = inv.id || inv.class || "unknown object";

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remove";
        removeBtn.onclick = () => {
            currentMonsterInventory.splice(idx, 1);
            renderMonsterInventoryList();
        };

        item.appendChild(symSpan);
        item.appendChild(nameSpan);
        item.appendChild(removeBtn);
        list.appendChild(item);
    });
}

//OPTIONS CODE for Popups
/*
function buildOptionsForm( type ) {
    
    let mainIDPre = type;
    let optIDPre = type.slice(0, 3);
   
    const form = document.getElementById(`${mainIDPre}-options-form`);
    form.innerHTML = "";

    for (const [key, def] of Object.entries(brushOptionDefs[mainIDPre])) {
        const row = document.createElement("div");
        row.className = `option-row`;

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.id = `${optIDPre}-cb-${key}`;
        cb.dataset.key = key;

        const label = document.createElement("label");
        label.htmlFor = cb.id;
        label.textContent = def.label + ":";

        row.appendChild(cb);
        row.appendChild(label);

        let control = null; // renamed from "input" to "control" for clarity (text, number, or select)

        if (def.input_type === "text") {
            control = document.createElement("input");
            control.type = "text";
        } else if (def.input_type === "number") {
            control = document.createElement("input");
            control.type = "number";
            control.min = def.min || 0;
            control.value = 1; // sensible default
        } else if (def.input_type === "combo") {
            control = document.createElement("select");
            if (def.combo_options && Array.isArray(def.combo_options) && def.combo_options.length > 0) {
                def.combo_options.forEach(opt => {
                    const option = document.createElement("option");
                    option.value = opt;
                    option.textContent = opt;
                    control.appendChild(option);
                });
                // Pre-select the first option as a reasonable default
                control.selectedIndex = 0;
            }
        }
        // bool fields need no extra control

        if (control) {
            control.id = `${optIDPre}-inp-${key}`;
            control.disabled = true; // disabled until checkbox is checked
            row.appendChild(control);
        }

        // Mutual exclusion handling (id ↔ class, or any future no_coexist pairs)
        if (def.no_coexist) {
            cb.addEventListener("change", () => {
                if (cb.checked) {
                    def.no_coexist.forEach(other => {
                        const otherCb = document.getElementById(`${optIDPre}-cb-${other}`);
                        if (otherCb) {
                            otherCb.checked = false;
                            const otherCtrl = document.getElementById(`${optIDPre}-inp-${other}`);
                            if (otherCtrl) {
                                otherCtrl.disabled = true;
                                // Optional: reset value when disabling the conflicting option
                                if (otherCtrl.tagName === "SELECT") {
                                    otherCtrl.selectedIndex = 0;
                                } else {
                                    otherCtrl.value = '';
                                }
                            }
                        }
                    });
                }
                if (control) control.disabled = !cb.checked;

                // Special handling for id/class (text filtering + list population)
                if (key === 'id' || key === 'class') {
                    currentMonsterMode = key;
                    const inputHNDL = document.getElementById(`${optIDPre}-inp-${key}`);
                    
                    // Clear the conflicting input
                    def.no_coexist.forEach(other => {
                        const otherInputHNDL = document.getElementById(`${optIDPre}-inp-${other}`);
                        if (otherInputHNDL) otherInputHNDL.value = '';
                    });

                    if (type === 'monster') {
                        populateMonsterList(inputHNDL?.value || '');
                        inputHNDL.addEventListener('input', (e) => {
                            const filter = e.target.value.trim();
                            populateMonsterList(filter);
                        });
                    } else if (type === 'object') {
                        populateObjectList(inputHNDL?.value || '');
                        inputHNDL.addEventListener('input', (e) => {
                            const filter = e.target.value.trim();
                            populateObjectList(filter);
                        });
                    }
                    
                    inputHNDL.focus();
                    inputHNDL.select();
                }
            });
        } else {
            cb.addEventListener("change", () => {
                if (control) control.disabled = !cb.checked;
            });
        }

        // Initial disabled state
        if (control) control.disabled = true;

        form.appendChild(row);
    }
}*/

function restorePanelOptions( panelName )
    {
        const definition = brushOptionDefs[panelName] || brushOptionDefs['level'][panelName];
        const stored = currentBrushGlobal[panelName];
        //Load in existing options
        Object.keys(definition).forEach(key => {
            const opt = definition[key];
            const fieldId = panelName + '_' + key;

            if( panelName == "level_flags"){
                console.log('test')    
            }

            if (opt.input_type !== 'check') {
                // Fields with "include" checkbox + value input
                const includeCb = document.getElementById('include_' + fieldId);
                const valueElem = document.getElementById(fieldId + '_value');

                const hasValue = stored && stored.hasOwnProperty(key);
                if (includeCb) includeCb.checked = hasValue;

                if (includeCb) valueElem.disabled = !hasValue;

                if (hasValue && valueElem) {
                    let val = stored[key];
                    // Convert stored type to string for <select>
                    if (typeof val === 'boolean' || typeof val === 'number') val = val.toString();
                    valueElem.value = val;
                }
            } else {
                // Pure checkbox flags
                const cb = document.getElementById('include_' + fieldId);
                if (cb) {
                    cb.checked = Array.isArray(stored) && stored.includes(key);
                }
            }

            

        });

    }

function buildOptionsForm(type) {
    const defs = brushOptionDefs[type];
    if (!defs) return;

    // Determine which popup and content area to use
    const popupId = (type === 'init') ? 'level-popup' : `${type}-popup`;
    const popup = document.getElementById(popupId);
    if (!popup) return;

    const contentArea = popup.querySelector('.popup-content') || popup.querySelector('#' + type + '-options-form');
    if (!contentArea) return;

    // Clear previous tabs/panels
    popup.querySelectorAll('.popup-tabs, .popup-panels').forEach(el => el.remove());
    contentArea.innerHTML = '';

    // Helper to build a single panel from field definitions

    function attachPanelListners(panelElem, fields, prefix = ''  )
    {
        Object.keys(fields).forEach(key => {

            const fieldId = prefix + "_" + key;

            //Uncheck boxes that can't coexist
            const cbHNDL = document.getElementById(`include_${fieldId}`);
            const inputHNDL = document.getElementById(fieldId + '_value');

            
            
            cbHNDL.addEventListener("change", () => {
                const checked = cbHNDL.checked;
                if( inputHNDL) inputHNDL.disabled = !checked;

                if (fields[key].no_coexist) {
                    if (checked) {
                        fields[key].no_coexist.forEach(other => {
                            const otherFieldId = prefix + "_" + other;
                            const otherCb = document.getElementById(`include_${otherFieldId}`);
                            if (otherCb) {
                                otherCb.checked = false;
                                const otherCtrl = document.getElementById(otherFieldId + '_value');
                                if (otherCtrl) {
                                    otherCtrl.disabled = true;
                                    // Optional: reset value when disabling the conflicting option
                                    if (otherCtrl.tagName === "SELECT") {
                                        otherCtrl.selectedIndex = 0;
                                    } else {
                                        otherCtrl.value = '';
                                    }
                                }
                            }
                        });
                    }
                }
                
                if ( (key === 'id' || key === 'class') && checked) {
                    if (prefix == 'monster') {
                        currentMonsterMode = key;
                        populateMonsterList(inputHNDL?.value || '');
                        inputHNDL.addEventListener('input', (e) => {
                            const filter = e.target.value.trim();
                            populateMonsterList(filter);
                        });
                    }
                    if (prefix == 'object') {
                        currentObjectMode = key;
                        populateObjectList(inputHNDL?.value || '');
                        inputHNDL.addEventListener('input', (e) => {
                            const filter = e.target.value.trim();
                            populateObjectList(filter);
                        });
                        
                    }
                    
                }
                if( checked )
                {
                    inputHNDL.focus();
                    if( inputHNDL.select) inputHNDL.select();
                }
            });
            

            //Attach Autocomplete for id/class list population boxes
            /*
            if (key === 'id' || key === 'class') {
                   
                    // Clear the conflicting input
                    fields[key].no_coexist.forEach(other => {
                        const otherId = prefix + "_" + other + '_value';
                        const otherInputHNDL = document.getElementById(otherId);
                        if (otherInputHNDL) otherInputHNDL.value = '';
                    });

                    
                }*/
            });
    }

    function buildPanel(panelElem, fields, prefix = '') {
        Object.keys(fields).forEach(key => {  // sort for consistent order
            const opt = fields[key];

            const row = document.createElement('div');
            row.className = 'option-row';

            let includeCb = null;
            const fieldId = prefix + "_" + key;

            // "Include" checkbox for non-pure-check fields
            if (opt.input_type !== 'check') {
                includeCb = document.createElement('input');
                includeCb.type = 'checkbox';
                includeCb.id = 'include_' + fieldId;
                includeCb.checked = true;
                row.appendChild(includeCb);
            }

            // Label with tooltip
            const label = document.createElement('label');
            label.textContent = opt.label;
            if (opt.desc) label.title = opt.desc;

            // Input element
            if (opt.input_type === 'combo') {
                const sel = document.createElement('select');
                sel.id = fieldId + '_value';
                opt.combo_options.forEach(val => {
                    const o = document.createElement('option');
                    o.value = val;
                    o.textContent = (val === ' ') ? '[space]' : val; // make space visible
                    sel.appendChild(o);
                });
                sel.selectedIndex = 0;
                label.htmlFor = sel.id;
                row.appendChild(label);
                row.appendChild(sel);
            } else if (opt.input_type === 'check') {
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.id = 'include_' + fieldId;
                label.htmlFor = cb.id;
                row.appendChild(label);
                row.appendChild(cb);
            } else if (opt.input_type === 'text' || opt.input_type === 'number') {
                const input = document.createElement('input');
                input.type = opt.input_type === 'number' ? 'number' : 'text';
                input.id = fieldId + '_value';
                label.htmlFor = input.id;
                row.appendChild(label);
                row.appendChild(input);
            } // add more input_types here if needed later

            if (includeCb) row.insertBefore(includeCb, row.firstChild);

            

            panelElem.appendChild(row);
        });

        
    }

    

    if (defs.tabs) {
        // ---------- MULTI-TAB LAYOUT ----------
        const tabBar = document.createElement('div');
        tabBar.className = 'popup-tabs';

        const panelsContainer = document.createElement('div');
        panelsContainer.className = 'popup-panels';

        defs.tabs.forEach((tab, idx) => {
            

            // Tab button
            const btn = document.createElement('button');
            btn.textContent = tab.desc;
            btn.dataset.key = tab.key;
            btn.className = idx === 0 ? 'active' : '';
            btn.onclick = () => {
                tabBar.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                panelsContainer.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
                document.getElementById(type + '-' + tab.key + '-panel').classList.add('active');
            };
            tabBar.appendChild(btn);

            // Tab panel
            const panel = document.createElement('div');
            panel.id = type + '-' + tab.key + '-panel';
            panel.className = 'tab-panel' + (idx === 0 ? ' active' : '');
            buildPanel(panel, defs[tab.key], tab.key );
            panelsContainer.appendChild(panel);

            popup.insertBefore(tabBar, contentArea);
            contentArea.appendChild(panelsContainer);

        });

        
        defs.tabs.forEach((tab, idx) => {
            // Existing Brush Handle
            const subBrushName = tab.key;                     // e.g. "level_init" or "level_flags"
            const stored = currentBrushGlobal[subBrushName] || (Array.isArray(currentBrushGlobal[subBrushName]) ? [] : {});

            const panel = document.getElementById( type + '-' + tab.key + '-panel');
            restorePanelOptions( subBrushName );

            attachPanelListners(panel, defs[subBrushName], subBrushName);
        });

    } else {
        // ---------- SINGLE PANEL (monster / object) ----------
        buildPanel(contentArea, defs, type);
        restorePanelOptions( type );
        attachPanelListners(contentArea, defs, type);
    }
}


//MONSTER INVENTORY SELECTION CODE
function updateInventoryDisplay() {
    const list = document.getElementById('monster-inventory-list');
    list.innerHTML = '';
    currentMonPopupInventory.forEach((item, i) => {
        const li = document.createElement('li');
        li.dataset.index = i;
        li.style.padding = '6px';
        li.style.background = (i === selectedInventoryIndex) ? '#1da1f2' : '#222';
        li.style.cursor = 'pointer';
        li.style.marginBottom = '2px';
        li.textContent = `${item.internal.symbol || '?'}  ${item.id}`;   // simple readable description
        li.addEventListener('click', () => {
            selectedInventoryIndex = i;
            updateInventoryDisplay();
            document.getElementById('delete-inventory-btn').disabled = false;
        });
        list.appendChild(li);
    });

    // disable delete button if nothing selected
    document.getElementById('delete-inventory-btn').disabled = (selectedInventoryIndex < 0);
}

//MONSTER INVENTORY SELECTION CODE
function updateContentsDisplay() {
    const list = document.getElementById('object-contents-list');
    list.innerHTML = '';
    currentObjPopupContents.forEach((item, i) => {
        const li = document.createElement('li');
        li.dataset.index = i;
        li.style.padding = '6px';
        li.style.background = (i === selectedContentsIndex) ? '#1da1f2' : '#222';
        li.style.cursor = 'pointer';
        li.style.marginBottom = '2px';
        li.textContent = `${item.internal.symbol || '?'}  ${item.id}`;   // simple readable description
        li.addEventListener('click', () => {
            selectedContentsIndex = i;
            updateContentsDisplay();
            document.getElementById('delete-contents-btn').disabled = false;
        });
        list.appendChild(li);
    });

    // disable delete button if nothing selected
    document.getElementById('delete-contents-btn').disabled = (selectedContentsIndex < 0);
}

document.getElementById('show-inventory-btn').addEventListener('click', () => {
    setObjectPopupTarget = "inventory";

    // Full list on open
    populateObjectList('');

    // Show the object popup (assume it is hidden by display:none)
    document.getElementById('object-popup').style.display = 'flex';   // or 'block' depending on your CSS
    document.getElementById('object-ok-btn').textContent = 'Add to Monster Inventory';
    // Optional: clear the object form for a fresh entry
    const idInput = document.querySelector('#object-popup input[type="text"]'); // adjust selector if needed
    if (idInput) idInput.value = '';
    // clear other inputs if you have them (quantity, etc.)
});

document.getElementById('delete-inventory-btn').addEventListener('click', () => {
    if (selectedInventoryIndex >= 0) {
        currentMonPopupInventory.splice(selectedInventoryIndex, 1);
        selectedInventoryIndex = -1;
        updateInventoryDisplay();
    }
});

document.getElementById('delete-contents-btn').addEventListener('click', () => {
    if (selectedContentsIndex >= 0) {
        currentObjPopupContents.splice(selectedContentsIndex, 1);
        selectedContentsIndex = -1;
        updateContentsDisplay();
    }
});