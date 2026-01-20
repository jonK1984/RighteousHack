const brushOptionDefs = {
    monster: {
        id:          { label: "Monster ID", input_type: "text",   no_coexist: ["class"] },
        class:       { label: "Monster class", input_type: "text",   no_coexist: ["id"] },
        peaceful:    { label: "Peaceful",             input_type: "bool" },
        asleep:      { label: "Asleep",               input_type: "bool" },
        name:        { label: "Custom name",          input_type: "text" },
        female:      { label: "Female",               input_type: "bool" },
        invisible:   { label: "Invisible",            input_type: "bool" },
        cancelled:   { label: "Cancelled",            input_type: "bool" },
        revived:     { label: "Revived",              input_type: "bool" },
        avenge:      { label: "Avenge",               input_type: "bool" },
        fleeing:     { label: "Fleeing (turns)",      input_type: "number", min: 0 },
        blinded:     { label: "Blinded (turns)",      input_type: "number", min: 0 },
        paralyzed:   { label: "Paralyzed (turns)",    input_type: "number", min: 0 },
        stunned:     { label: "Stunned",              input_type: "bool" },
        confused:    { label: "Confused",             input_type: "bool" },
        waiting:     { label: "Waiting",              input_type: "bool" },
        ignorewater: { label: "Ignore water",         input_type: "bool" },
        countbirth:  { label: "Count birth",          input_type: "bool" },
        appear_as:   { label: "Appear as (string)",   input_type: "text" }
    },

    object: {
        id:          { label: "Object ID",            input_type: "text",   no_coexist: ["class"] },
        class:       { label: "Object Class",         input_type: "text",   no_coexist: ["id"] },
        quantity:    { label: "Quantity",             input_type: "number", min: -1 }, // -1 = random
        spe:         { label: "Charges",              input_type: "number" },
        buc:         { label: "BUC State",            input_type: "combo", combo_options: [ "uncursed", "blessed",  "cursed", "not-cursed"] },  // e.g. "blessed", "uncursed", "cursed"
        name:        { label: "Custom Name",          input_type: "text" },
        buried:      { label: "Buried",               input_type: "bool" },
        lit:         { label: "Lit (lamp, etc.)",     input_type: "bool" },
        eroded:      { label: "Eroded Level",         input_type: "number", min: 0 },
        locked:      { label: "Locked",               input_type: "number", min: -1 }, // -1 = random, 0 = no, 1 = yes
        trapped:     { label: "Trapped",              input_type: "number", min: -1 }, // -1 = random, 0 = no, 1 = yes
        trap_known:  { label: "Trap Known",           input_type: "number", min: -1 }, // -1 = random, 0 = no, 1 = yes
        recharged:   { label: "Recharged Count",      input_type: "number", min: 0 },
        greased:     { label: "Greased",              input_type: "bool" },
        broken:      { label: "Broken",               input_type: "bool" },
        achievement: { label: "Achievement Tracker",  input_type: "bool" },

        // Corpse / statue specific flags
        corpsenm:    { label: "Corpse Monster ID",    input_type: "text" },  // monster ID if this object is a corpse/statue
        historic:    { label: "Historic (statue)",    input_type: "bool" },
        male:        { label: "Male (statue)",        input_type: "bool" },
        female:      { label: "Female (statue)",      input_type: "bool" }
    }
    
    // inventory is handled separately
};

function buildMonsterOptionsForm() {
    const form = document.getElementById("monster-options-form");
    form.innerHTML = "";
    const monsterOptionDefs = brushOptionDefs['monster'];

    for (const [key, def] of Object.entries(monsterOptionDefs)) {
        const row = document.createElement("div");
        row.className = "option-row";

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.id = `monopt-cb-${key}`;
        cb.dataset.key = key;

        const label = document.createElement("label");
        label.htmlFor = cb.id;
        label.textContent = def.label + ":";

        row.appendChild(cb);
        row.appendChild(label);

        let input = null;
        if (def.input_type === "text") {
            input = document.createElement("input");
            input.type = "text";
        } else if (def.input_type === "number") {
            input = document.createElement("input");
            input.type = "number";
            input.min = def.min || 0;
            input.value = 1; // sensible default
        }
        // bool fields need no extra input

        if (input) {
            input.id = `monopt-inp-${key}`;
            input.disabled = true; // disabled until checkbox is checked
            row.appendChild(input);
        }

        // Mutual exclusion handling (id ↔ class)
        if (def.no_coexist) {
            cb.addEventListener("change", () => {
                if (cb.checked) {
                    def.no_coexist.forEach(other => {
                        const otherCb = document.getElementById(`monopt-cb-${other}`);
                        
                        if (otherCb) {
                            otherCb.checked = false;
                            const otherInp = document.getElementById(`monopt-inp-${other}`);
                            if (otherInp) otherInp.disabled = true;
                        }
                    });
                }
                if (input) input.disabled = !cb.checked;
                if( key == 'id' || key == 'class'){
                    currentMonsterMode = key;
                    const inputHNDL = document.getElementById(`monopt-inp-${key}`);  
                    def.no_coexist.forEach(other => {
                        const otherInputHNDL = document.getElementById(`monopt-inp-${other}`);
                        otherInputHNDL.value = '';
                    });
                    populateMonsterList( inputHNDL?.value || '' );
                    inputHNDL.addEventListener('input', (e) => {
                        const filter = e.target.value.trim();
                        populateMonsterList( filter );
                    });
                    //Clear the value in the other one
                    
                    inputHNDL.focus();
                    inputHNDL.select();
                }
            });
        } else {
            cb.addEventListener("change", () => {
                if (input) input.disabled = !cb.checked;
            });
        }

        // Initial state: if checkbox unchecked, disable input
        if (input) input.disabled = true;

        form.appendChild(row);
    }
}

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