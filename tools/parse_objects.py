import re
from pathlib import Path

# Color tokens used in base objects (only CLR_ and HI_)
BASE_COLOR_PATTERN = r'(CLR_[A-Z_]+|HI_[A-Z_]+)'

# Color tokens used in artifacts (adds NO_COLOR, which appears frequently)
ARTI_COLOR_PATTERN = r'(NO_COLOR|CLR_[A-Z_]+|HI_[A-Z_]+)'

def parse_object_classes(defsym_path):
    """
    Parse defsym.h for OBJCLASS lines (object classes).
    Returns dict: base_macro.lower() -> {'symbol': sym, 'class1': desc1, 'class2': desc2}
    """
    class_dict = {}
    # Handles OBJCLASS(num, 'sym', MACRO, S_macro, "desc1"[, "desc2"])
    pattern = re.compile(r'OBJCLASS\s*\(\s*\d+\s*,\s*\'(.)\'\s*,\s*(\w+)\s*,\s*S_\w+\s*,\s*"([^"]+)"\s*(?:,\s*"([^"]*)")?\s*\)')

    content = Path(defsym_path).read_text(encoding='utf-8')
    for match in pattern.finditer(content):
        sym = match.group(1)
        macro = match.group(2).lower()
        desc1 = match.group(3).lower()
        desc2 = (match.group(4) or "").lower()

        class_dict[macro] = {
            'symbol': sym,
            'class1': desc1,
            'class2': desc2
        }

    return class_dict

def parse_base_objects(objects_path, class_dict):
    all_objects = {}
    sn_to_class_key = {}

    content = Path(objects_path).read_text(encoding='utf-8')

    patterns = [
    # ROD → wand (name in group 1, color in group 2, sn in group 3)
    (r'ROD\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'wand'),  # added color group index (3rd position in tuple)

    # ANOINTING → potion (name 1, color 2, sn 3)
    (r'ANOINTING\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'potion'),

    # PROJECTILE → weapon (name 1, color 2, sn 3)
    (r'PROJECTILE\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'weapon'),

    # WEAPON → weapon (name 1, color 2, sn 3)
    (r'WEAPON\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'weapon'),

    # BOW → weapon (name 1, color 2, sn 3)
    (r'BOW\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'weapon'),

    # Armor family (macro in 1, name in 2, color in 3, sn in 4)
    (r'(HELM|ARMOR|DRGN_ARMR|CLOAK|SHIELD|GLOVES|BOOTS)\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     2, 4, 3, 'armor'),

    # RING → ring (name 1, color 2, sn 3)
    (r'RING\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'ring'),

    # AMULET → amulet (color is hardcoded HI_METAL in the macro—no variable color arg)
    # Optional color group (may be None); keep original but make color capture optional
    (r'AMULET\s*\(\s*"([^"]+)"\s*,.*?\s*(?:,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*)?,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'amulet'),  # color group 2 is now optional

    # TOOL family (macro in 1, name in 2, color in 3, sn in 4)
    (r'(TOOL|CONTAINER|EYEWEAR|WEPTOOL)\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     2, 4, 3, 'tool'),

    # FOOD → food (name 1, color 2, sn 3)
    (r'FOOD\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'food'),

    # SCROLL → scroll (color is hardcoded HI_PAPER in the macro—no variable)
    (r'SCROLL\s*\(\s*"([^"]+)"\s*,.*?\s*(?:,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*)?,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'scroll'),

    # PBOOK → spbook (assume similar to SCROLL/TOOL; adjust if needed)
    (r'PBOOK\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'spbook'),

    # GEM → gem (name 1, color 2, sn 3)
    (r'GEM\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'gem'),

    # ROCK → rock (name 1, color 2, sn 3)
    (r'ROCK\s*\(\s*"([^"]+)"\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 3, 2, 'rock'),

    # Direct OBJECT (nested OBJ; name 1, class skipped, color 3, sn 4)
    # This is trickier due to nesting—captures color before final sn
    (r'OBJECT\s*\(\s*OBJ\s*\(\s*"([^"]+)"\s*,[^\)]*\)\s*,.*?\s*,\s*(CLR_[A-Z_]+|HI_[A-Z_]+|NO_COLOR)\s*,\s*([A-Z_0-9_]+)\s*\)', 
     1, 4, 3, None),
    ]

    for regex, name_g, sn_g, item_color_indx, class_key_fixed in patterns:
        for match in re.finditer(regex, content):
            name = match.group(name_g).strip().lower()
            sn = match.group(sn_g)
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

            all_objects[name] = {
                'id': name,
                'symbol': sym,
                'class1': c1,
                'class2': c2,
                'item_class_str': class_key_fixed,
                'is_artifact': False,
                'color': color_token
            }

            sn_to_class_key[sn] = class_key

    return all_objects, sn_to_class_key

def parse_artifacts(artilist_file, sn_to_class_key, class_dict):
    artifacts = {}

    content = Path(artilist_file).read_text(encoding='utf-8')

    arti_pattern = re.compile(
        r'A\s*\(\s*"([^"]+)"'              # artifact name → group 1
        r'.*?'                             # non-greedy skip
        r',\s*' + ARTI_COLOR_PATTERN + r'\s*,'  # clr → group 2
        r'\s*([A-Z_0-9_]+)\s*\)'            # bn/sn → group 3
        , re.DOTALL
    )

    for match in arti_pattern.finditer(content):
        raw_name = match.group(1).strip()
        color_token = match.group(2)
        sn = match.group(3)

        name = raw_name.lower()

        # Class resolution same as base objects
        class_key = sn_to_class_key.get(sn, "unknown")
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
            f.write(f'    "{esc_id}": {{\n')
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