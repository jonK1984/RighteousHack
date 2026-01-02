import re
import json
from pathlib import Path

def parse_color_defines(color_h_path):
    """
    Parse color.h for #define CLR_*/HI_*/DRAGON_SILVER/NO_COLOR
    Returns dict: const_name -> final numeric index (resolved aliases)
    """
    content = Path(color_h_path).read_text(encoding='utf-8')
    defines = {}
    # #define CONST value (value can be number or another CONST)
    pat = re.compile(r'#define\s+(CLR_\w+|HI_\w+|DRAGON_SILVER|NO_COLOR)\s+([0-9]+|CLR_\w+|HI_\w+)')
    for m in pat.finditer(content):
        const = m.group(1)
        val = m.group(2)
        defines[const] = val

    # Resolve aliases to final number
    def resolve(c):
        if c.isdigit():
            return int(c)
        return resolve(defines[c]) if c in defines else -1

    resolved = {}
    for c, v in defines.items():
        idx = resolve(v)
        if idx != -1:
            resolved[c] = idx

    return resolved, defines

def parse_colornames(coloratt_path):
    """
    Parse primary color descriptions from colornames[] (before null terminator)
    Returns dict: index -> hyphenated lowercase description
    """
    content = Path(coloratt_path).read_text(encoding='utf-8')
    desc_map = {}
    in_array = False
    for line in content.splitlines():
        if 'static const struct color_names colornames[] = {' in line:
            in_array = True
            continue
        if in_array:
            m = re.search(r'\{\s*"([^"]+)"\s*,\s*(CLR_\w+|NO_COLOR)\s*\}', line)
            if m:
                raw_desc = m.group(1)
                const = m.group(2)
                desc = raw_desc.lower().replace(' ', '-')
                # Will map via index later
            # Stop at null terminator
            if '(const char *) 0' in line or '0, CLR_BLACK' in line:
                break
    return desc_map  # We'll fill via index in main
'''
def parse_colortable(coloratt_path):
    """
    Parse colortable[] for RGB and hex – robust to extra prefix fields (colortyp, tableindex, rgbindex)
    Returns list[index] = {'desc': base_desc (from name string), 'RGB': {...}, 'hex': hex}
    Assumes array is defined in sequential index order 0 to CLR_MAX-1
    """
    content = Path(coloratt_path).read_text(encoding='utf-8')
    table = []
    # Skip first 3 fields (nh_color, index, rgbindex or similar), capture name, hex, r, g, b
    pat = re.compile(r'{\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*[},]')
    
    for m in pat.finditer(content):
        base_desc = m.group(1).lower().replace(' ', '-')
        hexv = m.group(2)
        r, g, b = int(m.group(3)), int(m.group(4)), int(m.group(5))
        table.append({
            'desc': base_desc,
            'RGB': {'r': r, 'g': g, 'b': b},
            'hex': hexv
        })
    
    return table
'''
def parse_colortable(coloratt_path):
    """
    Parse colortable[] handling both nh_color (empty hex) and rgb_color (with hex)
    Returns list[index] = {'desc': base_desc_from_name, 'RGB': {...}, 'hex': hex ("" if none)}
    Assumes sequential order starting from index 0
    """
    content = Path(coloratt_path).read_text(encoding='utf-8')
    table = []
    # Skip first 3 fields (colortyp, tableindex, rgbindex)
    # Capture: "name", "hex" (can be ""), r, g, b
    pat = re.compile(
        r'{\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*[},]'
    )
    
    for m in pat.finditer(content):
        base_desc = m.group(1).lower().replace(' ', '-')
        hexv = m.group(2)  # "" for nh_color, "#RRGGBB" for rgb_color
        r, g, b = int(m.group(3)), int(m.group(4)), int(m.group(5))
        table.append({
            'desc': base_desc,
            'RGB': {'r': r, 'g': g, 'b': b},
            'hex': hexv
        })
    
    return table

def extract_color_table(color_h_path, coloratt_path):
    resolved_map, _ = parse_color_defines(color_h_path)  # const -> index

    # Primary descriptions from colornames (map index -> desc)
    primary_desc = {}
    content = Path(coloratt_path).read_text(encoding='utf-8')
    in_array = False
    for line in content.splitlines():
        if 'static const struct color_names colornames[] = {' in line:
            in_array = True
            continue
        if in_array:
            m = re.search(r'\{\s*"([^"]+)"\s*,\s*(CLR_\w+|NO_COLOR)\s*\}', line)
            if m:
                raw_desc = m.group(1)
                const = m.group(2)
                if const in resolved_map:
                    idx = resolved_map[const]
                    desc = raw_desc.lower().replace(' ', '-')
                    primary_desc[idx] = desc
            if '(const char *) 0' in line or '0, CLR_BLACK' in line:
                break

    colortable = parse_colortable(coloratt_path)

    colorTable = {}
    for const, idx in resolved_map.items():
        if idx < len(colortable):
            entry = colortable[idx].copy()
            # Prefer primary description from colornames
            if idx in primary_desc:
                entry['desc'] = primary_desc[idx]
            colorTable[const] = entry

    return colorTable


def output_js(colorTable: dict, output_path: str):
    """
    Write the JavaScript const colorTable = { ... } to a file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('const colorTable = ' + json.dumps(colorTable, indent=4) + ';')
        

    
    print(f"Generated {output_path} with {len(colorTable)} colors.")


if __name__ == '__main__':
    color_h = '.\include\color.h'          # adjust paths if needed
    coloratt_c = '.\src\coloratt.c'
    output_file = 'color_def.js'

    colorTable = extract_color_table(color_h, coloratt_c)
    output_js( colorTable, output_file)
    #print('const colorTable = ' + json.dumps(colorTable, indent=4) + ';')