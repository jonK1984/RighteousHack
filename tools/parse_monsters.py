import re
import sys
from pathlib import Path

def parse_defsym(defsym_path: str) -> dict:
    """
    Parse defsym.h to extract monster class macros (S_XXX), their symbol char,
    and class description (split into class1 and class2 on ' or ').
    """
    sym_dict = {}
    # Updated regex: skips the BASENAME argument (e.g., ANT in MONSYM(1, 'a', ANT, S_ANT, "..."))
    #monsym_pattern = re.compile(
    #    r'MONSYM\s*\(\s*\d+\s*,\s*\'(.)\'\s*,\s*\w+\s*,\s*(S_\w+)\s*,\s*"([^"]+)"'
    #)
    monsym_pattern = re.compile(
        r'MONSYM\s*\(\s*\d+\s*,\s*\'(?:\\)?(.)\'\s*,\s*\w+\s*,\s*(S_\w+)\s*,\s*"([^"]+)"'
    )
    with open(defsym_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = monsym_pattern.search(line)
            if match:
                symbol = match.group(1)
                macro = match.group(2)
                desc = match.group(3).strip()

                # Split description on " or " for class1/class2
                if ' or ' in desc:
                    class1, class2 = desc.split(' or ', 1)
                    class1 = class1.strip().lower()
                    class2 = class2.strip().lower()
                else:
                    class1 = desc.strip().lower()
                    class2 = ""

                sym_dict[macro] = {
                    'symbol': symbol,
                    'class1': class1,
                    'class2': class2
                }

    if not sym_dict:
        print("Warning: No MONSYM lines found in defsym.h – check if the monster block exists.", file=sys.stderr)

    return sym_dict


def parse_monsters(monsters_path: str, sym_dict: dict) -> dict:
    """
    Parse monsters.h handling both MON("name", S_XXX, ...) and MON(NAM("name"), S_XXX, ...)

    The color is the 13th argument of the MON macro (col).
    We use a greedy middle skip (.*) so that the regex prefers the *last* matching
    ", <difficulty>, <color>, <bn>)" sequence before the closing parenthesis.
    This reliably lands on the final difficulty / color / bn triple even though
    there are many commas and numbers earlier in LVL(), A(), SIZ(), etc.
    """
    all_monsters = {}
    content = Path(monsters_path).read_text(encoding='utf-8')
    
    # Updated regex:
    #   group 1 → raw monster name inside the quotes
    #   group 2 → S_XXX symbol macro
    #   group 3 → difficulty (the number just before color)
    #   group 4 → color token (CLR_…, HI_…, or occasionally a raw number)
    #   group 5 → bn (the PM_ suffix, e.g. APPRENTICE, BABY_GRAY_DRAGON)
    mon_pattern = re.compile(
        r'MON\s*\(\s*'                     # MON(
        r'(?:NAM\s*\(\s*)?'                # optional NAM(
        r'"([^"]+)"'                       # "monster name" → group 1
        r'\s*(?:\s*\))?'                   # optional ) for NAM
        r',\s*'
        r'(S_\w+)'                         # S_XXX → group 2
        r'\s*,'
        r'.*?'                             # ← NON-GREEDY: stop at the soonest real color token
        r',\s*'
        r'(\d+)'                           # difficulty → group 3
        r'\s*,\s*'
        r'(CLR_[A-Z_]+|HI_[A-Z_]+|DRAGON_SILVER|)'  # color token → group 4
        r'\s*,\s*'
        r'([A-Z_0-9]+)'                    # bn → group 5
        r'\s*\)'                           # closing )
        r'(?:,\s*)?',                      # optional trailing comma/newline
        re.DOTALL
    )
    
    for match in mon_pattern.finditer(content):
        raw_name = match.group(1).strip()
        macro = match.group(2)
        color_token = match.group(4)       # ← this is now reliably the col argument
        bn = match.group(5)

        name = raw_name.lower()
        
        if macro not in sym_dict:
            print(f"Warning: No symbol definition found for {macro} (used by \"{raw_name}\")", file=sys.stderr)
            continue

        info = sym_dict[macro]
        all_monsters[name] = {
            'id': name,
            'class1': info['class1'],
            'class2': info['class2'],
            'symbol': info['symbol'],
            'raw_name': raw_name,
            'color': color_token,         # e.g. "HI_DOMESTIC" or "CLR_GRAY"
            'bn': bn                      # optional, if you need the enum suffix
        }

    mon_pattern2 = re.compile(
        r'MON\s*\(\s*'                          # MON(
        r'(?:NAMS\s*\(\s*)?'                    # optional NAMS(
        r'"([^"]+)"'                            # first name (male or single) → group 1
        r'(?:\s*,\s*"([^"]+)"'                  # optional second name (female) → group 2
        r'\s*,\s*"([^"]+)"'                     # optional third name (neutral) → group 3
        r'\s*\))?'                              # optional closing ) for NAMS
        r'\s*,\s*'
        r'(S_\w+)'                              # monster class symbol → group 4
        r'.*?'                                  # skip everything in between (non-greedy)
        r',\s*'
        r'(\d+)'                                # difficulty → group 5
        r'\s*,\s*'
        r'(CLR_[A-Z_]+|HI_[A-Z_]+|DRAGON_SILVER|NO_COLOR|)'  # color → group 6 (optional empty)
        r'\s*,\s*'
        r'([A-Z_0-9]+)'                         # final enum name → group 7
        r'\s*\)'                                # closing )
        , re.DOTALL
    )
    
    for match in mon_pattern2.finditer(content):
        
        
        raw_names = [match.group(1), match.group(2), match.group(3)]
       

        macro    = match.group(4)
        bn = match.group(7)
        color_token      = match.group(6) or "NO_COLOR"

               # from your existing parse_defsym()
        
        # Create one entry for each name (exactly what you asked for)
        for raw_name in raw_names:
            name = raw_name.lower()
            if macro not in sym_dict:
                print(f"Warning: No symbol definition found for {macro} (used by \"{raw_name}\")", file=sys.stderr)
                continue
            info = sym_dict[macro] 
            all_monsters[name] = {
                'id': name,
                'class1': info['class1'],
                'class2': info['class2'],
                'symbol': info['symbol'],
                'raw_name': raw_name,
                'color': color_token,         # e.g. "HI_DOMESTIC" or "CLR_GRAY"
                'bn': bn                      # optional, if you need the enum suffix
            }

    return all_monsters




def output_js(monsters: dict, output_path: str):
    """
    Write the JavaScript const allMonsters = { ... } to a file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('const allMonsters = {\n')
        for name in sorted(monsters.keys()):
            m = monsters[name]
            f.write(f'    "{m["id"]}": {{\n')
            f.write(f'        id: "{m["raw_name"]}",\n')
            f.write(f'        class1: "{m["class1"]}",\n')
            f.write(f'        class2: "{m["class2"]}",\n')
            f.write(f'        symbol: "{m["symbol"]}",\n')
            f.write(f'        color: "{m["color"]}"\n')   # ← NEW
            f.write('    },\n')
        f.write('};\n')

    print(f"Generated {output_path} with {len(monsters)} monsters.")

if __name__ == '__main__':
    #if len(sys.argv) != 4:
    #    print("Usage: python generate_allMonsters.py <defsym.h> <monsters.h> <output.js>")
     #   sys.exit(1)

    defsym_file = './include/defsym.h'
    monsters_file = './include/monsters.h'
    output_file = 'monster_def.js'

    symbols = parse_defsym(defsym_file)
    monsters = parse_monsters(monsters_file, symbols)
    output_js(monsters, output_file)