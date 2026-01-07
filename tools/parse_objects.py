import re
from pathlib import Path

# Color tokens used in base objects (only CLR_ and HI_)
BASE_COLOR_PATTERN = r'(CLR_[A-Z_]+|HI_[A-Z_]+)'

# Color tokens used in artifacts (adds NO_COLOR, which appears frequently)
ARTI_COLOR_PATTERN = r'(NO_COLOR|CLR_[A-Z_]+|HI_[A-Z_]+)'

def remove_block_comments(text: str) -> str:
    """
    Remove all C-style block comments (/* ... */) from the input string.
    Everything else (code, whitespace, newlines outside comments) is preserved exactly.
    Does NOT handle // line comments (only block comments as requested).
    Assumes no /* or */ inside string literals (safe for NetHack headers).
    If a comment is unclosed, everything from /* to the end of the string is removed.
    """
    result = []
    i = 0
    length = len(text)

    while i < length:
        # Look for start of block comment
        if text[i:i+2] == '/*':
            # Skip the entire comment (including /* and */ delimiters)
            i += 2
            while i < length and text[i:i+2] != '*/':
                i += 1
            if i < length:
                i += 2  # skip past the closing */
            # Do NOT append anything for the comment (removes it completely)
        else:
            # Normal character — copy it unchanged
            result.append(text[i])
            i += 1

    return ''.join(result)

def parse_object_classes(defsym_path):
    """
    Parse defsym.h for OBJCLASS and OBJCLASS2 lines (object classes).
    Returns dict: base_macro.lower() -> {'symbol': sym_char, 'class1': desc1, 'class2': desc2}
    Handles:
    - Symbol as 'X', 0xED, or decimal
    - Optional extra argument in OBJCLASS2
    - Optional second description
    - Skips commented-out lines
    """
    class_dict = {}
    # Anchor to line start to avoid matching inside comments
    pattern = re.compile(
        r'^\s*OBJCLASS(?:2)?\s*\(\s*\d+\s*,\s*'
        r'(?:\'(.)\'|0x([0-9A-Fa-f]+)|(\d+))\s*,\s*'
        r'(\w+)\s*(?:\s*,\s*\w+\s*)?\s*,\s*S_\w+\s*,\s*'
        r'"([^"]+)"\s*(?:,\s*"([^"]*)")?\s*\)',
        re.MULTILINE
    )

    content = Path(defsym_path).read_text(encoding='utf-8')
    for match in pattern.finditer(content):
        sym_char = match.group(1)
        sym_hex = match.group(2)
        sym_dec = match.group(3)
        macro = match.group(4)
        class1 = match.group(5)
        class2 = match.group(6) if match.group(6) else ""

        if sym_char:
            sym = sym_char
        elif sym_hex:
            sym = bytes([int(sym_hex, 16)]).decode('cp437')
        elif sym_dec:
            sym = bytes([int(sym_hex)]).decode('cp437')
        else:
            continue  # skip if no symbol found

        class_dict[macro.lower()] = {
            'symbol': sym,
            'class1': class1,
            'class2': class2
        }

    return class_dict

def parse_base_objects(objects_path, class_dict):
    all_objects = {}
    sn_to_class_key = {}

    content = Path(objects_path).read_text(encoding='utf-8')
    content = remove_block_comments( content )
    patterns = [
    # ROD → wand (name in group 1, color in group 2, sn in group 3)
    (r'ROD\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'wand', 'rod'),  # added color group index (3rd position in tuple)

    # ANOINTING → potion (name 1, color 2, sn 3)
    (r'ANOINTING\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'anointing', 'anointing oil'),

    # ANOINTING → potion (name 1, color 2, sn 3)
    (r'POTION\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'potion', 'elixer'),

    # Projectile family (handles second param as quoted string or NoDes + multi-line params)
    (r'PROJECTILE\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'weapon', ''),

    # WEAPON → weapon (name 1, color 2, sn 3)
    (r'WEAPON\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR|HI_[A-Z_]+)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'weapon', ''),

    # BOW → weapon (name 1, color 2, sn 3)
    (r'BOW\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'weapon', ''),

    # ARMOR family (handles two quoted strings + multi-line params)
    (r'ARMOR\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Boots family only (handles two quoted strings + multi-line params)
    (r'BOOTS\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Gloves family only (handles two quoted strings + multi-line params)
    (r'GLOVES\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Shield family only (handles two quoted strings + multi-line params)
    (r'SHIELD\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Cloak family only (handles second param as quoted string or NoDes + multi-line params)
    (r'CLOAK\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Helm family only (handles two quoted strings + multi-line params)
    (r'HELM\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'armor', ''),

    # Armor family (macro in 1, name in 2, color in 3, sn in 4)
    (r'(DRGN_ARMR)\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     2, 4, 3, 'armor', ''),

    # Ring family (handles second param as quoted string or potential NoDes + multi-line params)
    (r'RING\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'ring', 'ring'),

    # AMULET → amulet (color is hardcoded HI_METAL in the macro—no variable color arg)
    # Optional color group (may be None); keep original but make color capture optional
    (r'AMULET\s*\(\s*"([^"]+)"\s*,.*?\s*(?:,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*)?,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'amulet', 'amulet'),  # color group 2 is now optional

    # TOOL family (macro in 1, name in 2, color in 3, sn in 4)
    (r'(TOOL|CONTAINER|EYEWEAR|WEPTOOL)\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     2, 4, 3, 'tool', ''),

    # FOOD → food (name 1, color 2, sn 3)
    (r'FOOD\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'food', ''),

    # Scroll family (second param is Bible verse appearance; no color param — hardcoded HI_PAPER)
    (r'SCROLL\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 2, 'HI_PAPER', 'scroll', 'verse'),


    # PBOOK family (second param is appearance string + trailing comment; color is variable)
    (r'PBOOK\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, 'spbook', 'prophetic book'),

    # GEM → gem (name 1, color 2, sn 3)
    (r'GEM\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'gem', ''),

    # ROCK → rock (name 1, color 2, sn 3)
    (r'ROCK\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'rock', ''),

    # Direct OBJECT (nested OBJ; name 1, class skipped, color 3, sn 4)
    # This is trickier due to nesting—captures color before final sn
    # OBJECT family (handles inner OBJ("name", NoDes|"appearance") + multi-line params + variable color)
    (r'OBJECT\s*\(\s*OBJ\s*\(\s*"([^"]+)"\s*,[\s\S]*?\)\s*,[\s\S]*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 3, 2, None, ''),

    # Coin family (hardcoded color HI_GOLD; no color param in macro)
    (r'COIN\s*\(\s*"([^"]+)"\s*,[\s\S]*?\s*,\s*([A-Z_0-9_]+)\s*\)', 
    1, 2, 'HI_GOLD', 'coin', ''),

    ]

    for regex, name_g, sn_g, item_color_indx, class_key_fixed, name_prefix in patterns:
        if class_key_fixed == 'coin':
            print('coin')
        for match in re.finditer(regex, content):
            name = match.group(name_g).strip().lower()
            sn = match.group(sn_g)
            if name_prefix == 'verse':
                color_token = item_color_indx
            elif sn == 'GOLD_PIECE':
                color_token = item_color_indx
            else:
                color_token = match.group(item_color_indx)
            
            if class_key_fixed is not None:
                class_key = class_key_fixed
            else:
                # Direct OBJECT case – group 2 is the full XXX_CLASS
                class_full = match.group(2)
                class_key = class_full.replace('_CLASS', '').lower()

            if class_key in class_dict:
                info = class_dict[class_key]
                sym = info['symbol']
                c1 = info['class1']
                c2 = info['class2']
            else:
                sym = '?'
                c1 = class_key
                c2 = ''
            if name_prefix != '': 
                reference = name_prefix + ' of ' + name
            else:
                reference = name
                    
            all_objects[reference] = {
                'id': name,
                'symbol': sym,
                'class1': c1,
                'class2': c2,
                'item_class_str': class_key_fixed,
                'sn': sn,
                'is_artifact': False,
                'color': color_token
            }

            sn_to_class_key[sn] = class_key

    return all_objects, sn_to_class_key

def get_class_info(class_dict: dict, class_key: str) -> dict:
    """
    Look up the full class entry by matching class_key to the 'sn' field.
    Returns the matching entry if found, otherwise a safe default.
    Assumes class_dict values are dicts containing at least 'sn'.
    """
    for entry in class_dict.values():
        if entry.get('sn') == class_key:
            return entry
    # Default fallback if no match
    return {'symbol': '?', 'class1': 'unknown', 'class2': ''}

def parse_artifacts(artilist_file, sn_to_class_key, class_dict):
    artifacts = {}

    content = Path(artilist_file).read_text(encoding='utf-8')

    # Updated pattern:
    # Group 1 → artifact name ("Belt of Truth")
    # Group 2 → base object macro (BELT, DIVINE_COVERING, ANCIENT_SHIELD, etc.)
    # Group 3 → color token (NO_COLOR, CLR_..., HI_...)
    # Group 4 → unique artifact macro (BELT_OF_TRUTH, HELMET_OF_SALVATION, etc.)
    arti_pattern = re.compile(
        r'A\s*\(\s*"([^"]+)"\s*,\s*([A-Z_0-9_]+)\s*,[\s\S]*?'  # name + base macro + skip everything in between
        r',\s*' + ARTI_COLOR_PATTERN + r'\s*,\s*([A-Z_0-9_]+)\s*\)',  # color + final artifact macro
        re.DOTALL
    )
    '''
    arti_pattern = re.compile(
        r'A\s*\(\s*"([^"]+)"'              # artifact name → group 1
        r'.*?'                             # non-greedy skip
        r',\s*' + ARTI_COLOR_PATTERN + r'\s*,'  # clr → group 2
        r'\s*([A-Z_0-9_]+)\s*\)'            # bn/sn → group 3
        , re.DOTALL
    )
    '''

    for match in arti_pattern.finditer(content):
        raw_name = match.group(1).strip()
        base_name = match.group(2)
        color_token = match.group(3)
        sn = match.group(3)

        name = raw_name.lower()

        # Class resolution same as base objects
        class_key = sn_to_class_key.get(base_name, "unknown")
       
        class_info = class_dict.get(class_key, {'symbol': '?', 'class1': 'unknown', 'class2': ''})

        artifacts[name] = {
            'id': name,
            'symbol': class_info['symbol'],
            'class1': class_info['class1'],
            'class2': class_info['class2'],
            'raw_name': raw_name,
            'color': color_token,       # ← NEW: e.g. "NO_COLOR", "CLR_BRIGHT_BLUE", "CLR_MAGENTA"
            'is_artifact': True,
            'sn': sn
        }

    return artifacts

def output_js(all_objs, output_path):
    def js_escape(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('const allObjects = {\n')
        for name in sorted(all_objs.keys()):
            o = all_objs[name]
            esc_id = js_escape(o['id'])
            esc_sym = js_escape(o['symbol'])
            esc_c1 = js_escape(o['class1'])
            esc_c2 = js_escape(o['class2'])
            f.write(f'    "{name}": {{\n')
            f.write(f'        id: "{esc_id}",\n')
            f.write(f'        symbol: "{esc_sym}",\n')
            f.write(f'        class1: "{esc_c1}",\n')
            f.write(f'        class2: "{esc_c2}",\n')
            f.write(f'        is_artifact: {str(o["is_artifact"]).lower()},\n')
            f.write(f'        color: "{o["color"]}",\n')
            f.write('    },\n')
        f.write('};\n')

    print(f"Generated {output_path} with {len(all_objs)} objects (base + artifacts).")

if __name__ == '__main__':
    defsym_file = './include/defsym.h'
    objects_file = './include/objects.h'
    artilist_file = './include/artilist.h'
    output_file = 'allObjects.js'

    class_dict = parse_object_classes(defsym_file)
    base_objects, sn_to_class_key = parse_base_objects(objects_file, class_dict)
    artifacts = parse_artifacts(artilist_file, sn_to_class_key, class_dict)

    all_objects = {**base_objects, **artifacts}

    output_js(all_objects, output_file)