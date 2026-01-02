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
        # ROD → wand
        (r'ROD\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'wand'),

        # ANOINTING → potion
        (r'ANOINTING\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'potion'),

        # PROJECTILE → weapon
        (r'PROJECTILE\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'weapon'),

        # WEAPON → weapon (covers athame, runesword, battle-axe, etc.)
        (r'WEAPON\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'weapon'),

        # BOW → weapon
        (r'BOW\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'weapon'),

        # Armor family – now reliably captures gleaming armor → PLATE_OF_RIGHT, etc.
        (r'(HELM|ARMOR|DRGN_ARMR|CLOAK|SHIELD|GLOVES|BOOTS)\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 2, 3, 'armor'),

        # RING → ring
        (r'RING\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'ring'),

        # AMULET → amulet
        (r'AMULET\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'amulet'),

        # TOOL family (includes magic markers, lamps, etc.)
        (r'(TOOL|CONTAINER|EYEWEAR|WEPTOOL)\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 2, 3, 'tool'),

        # FOOD → food
        (r'FOOD\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'food'),

        # SCROLL → scroll
        (r'SCROLL\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'scroll'),

        # PBOOK → spbook
        (r'PBOOK\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'spbook'),

        # GEM → gem
        (r'GEM\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'gem'),

        # ROCK → rock
        (r'ROCK\s*\(\s*"([^"]+)"\s*,[^\)]*,\s*(\w+)\s*\)', 1, 2, 'rock'),

        # Direct OBJECT (boulder, etc.)
        (r'OBJECT\s*\(\s*OBJ\s*\(\s*"([^"]+)"\s*,[^\)]*\)\s*,[^\)]*,\s*(\w+_CLASS)\s*,[^\)]*,\s*(\w+)\s*\)', 1, 3, None),
    ]

    for regex, name_g, sn_g, class_key_fixed in patterns:
        for match in re.finditer(regex, content):
            name = match.group(name_g).strip().lower()
            sn = match.group(sn_g)

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
                'is_artifact': False
            }

            sn_to_class_key[sn] = class_key

    return all_objects, sn_to_class_key

def parse_artifacts(artilist_path, sn_to_class_key, class_dict):
    artifacts = {}

    content = Path(artilist_path).read_text(encoding='utf-8')

    pattern = re.compile(r'A\s*\(\s*"([^"]+)"\s*,\s*(\w+)\s*,')
    for match in pattern.finditer(content):
        name = match.group(1).strip().lower()
        base_sn = match.group(2)

        if base_sn in sn_to_class_key:
            class_key = sn_to_class_key[base_sn]
            if class_key in class_dict:
                info = class_dict[class_key]
                sym = info['symbol']
                c1 = info['class1']
                c2 = info['class2']
            else:
                sym = '?'
                c1 = class_key
                c2 = ''
        else:
            sym = '?'
            c1 = 'unknown'
            c2 = ''

        artifacts[name] = {
            'id': name,
            'symbol': sym,
            'class1': c1,
            'class2': c2,
            'is_artifact': True
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
            f.write(f'        is_artifact: {str(o["is_artifact"]).lower()}\n')
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