import re
from pathlib import Path

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

def parse_defsym(defsym_path: str) -> dict:
    """Parse defsym.h for monster symbols and descriptions."""
    sym_dict = {}
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

                class1 = desc
                class2 = ""
                if ' or ' in desc:
                    parts = desc.split(' or ')
                    class1 = parts[0].strip()
                    class2 = parts[-1].strip()

                sym_dict[macro] = {
                    "symbol": symbol,
                    "desc": desc,
                    "class1": class1,
                    "class2": class2
                }
    return sym_dict


def split_macro_args(mon_line: str):
    """Split the contents of a MON(... ) macro into 14 arguments, respecting nested parens and quotes."""
    start = mon_line.find('(') + 1
    end = mon_line.rfind(')')
    content = mon_line[start:end]

    args = []
    current = ""
    level = 0
    in_quote = False

    i = 0
    while i < len(content):
        c = content[i]

        if c == '"':
            in_quote = not in_quote
            current += c
        elif in_quote:
            current += c
        elif c == '(':
            level += 1
            current += c
        elif c == ')':
            level -= 1
            current += c
        elif c == ',' and level == 0:
            args.append(current.strip())
            current = ""
        else:
            current += c
        i += 1

    if current:
        args.append(current.strip())

    return args


def parse_monsters(monsters_path: str, symbols: dict) -> dict:
    monsters = {}

    with open(monsters_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find every MON(...) block
    for match in re.finditer(r'(MON\([^;]*\))', content, re.DOTALL):
        mon_line = match.group(1)

        args = split_macro_args(mon_line)
        if len(args) != 14:
            print(f"Warning: unexpected arg count in {mon_line[:60]}...")
            continue

        name_arg = args[0]
        s_class = args[1].strip()
        color = args[12].strip()      # CLR_... or HI_...
        enum_name = args[13].strip()  # e.g. GNOME_LEADER

        if s_class not in symbols:
            print(f"Warning: unknown symbol class {s_class}")
            continue

        sym_info = symbols[s_class]
        symbol = sym_info["symbol"]
        class1 = sym_info["class1"]
        class2 = sym_info["class2"]

        # ---------- Extract names ----------
        names = []
        if name_arg.startswith('NAMS('):
            inner = name_arg[len('NAMS('):-1]  # strip NAMS( and )
            # Split on commas outside quotes
            part = ""
            in_quote = False
            for c in inner:
                if c == '"':
                    in_quote = not in_quote
                    part += c
                elif c == ',' and not in_quote:
                    cleaned = part.strip()
                    if cleaned.startswith('"') and cleaned.endswith('"'):
                        names.append(cleaned[1:-1])
                    part = ""
                else:
                    part += c
            # last part
            cleaned = part.strip()
            if cleaned.startswith('"') and cleaned.endswith('"'):
                names.append(cleaned[1:-1])
        else:
            # Single name case (NAM("...") or plain "...")
            cleaned = name_arg.strip()
            if cleaned.startswith(('NAM(', '"')):
                cleaned = cleaned.split('(', 1)[1] if cleaned.startswith('NAM(') else cleaned
                cleaned = cleaned.rsplit(')', 1)[0] if ')' in cleaned else cleaned
            if cleaned.startswith('"') and cleaned.endswith('"'):
                names.append(cleaned[1:-1])

        if not names:
            print(f"Warning: no names parsed from {name_arg}")
            continue

        # ---------- Create an entry for each name ----------
        for name in names:
            slug = name.lower().replace(' ', '_').replace('-', '_')
            if slug in monsters:
                print(f"Warning: duplicate slug {slug}, skipping second occurrence")
                continue

            monsters[slug] = {
                "raw_name": name,
                "base_id": enum_name,   # original permonst enum
                "class1": class1,
                "class2": class2,
                "symbol": symbol,
                "color": color
            }

    return monsters


def output_js(monsters: dict, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('const allMonsters = {\n')
        for slug in sorted(monsters.keys()):
            m = monsters[slug]
            f.write(f'    "{slug}": {{\n')
            f.write(f'        name: "{m["raw_name"]}",\n')
            f.write(f'        base_id: "{m["base_id"]}",\n')
            f.write(f'        class1: "{m["class1"]}",\n')
            f.write(f'        class2: "{m["class2"]}",\n')
            f.write(f'        symbol: "{m["symbol"]}",\n')
            f.write(f'        color: "{m["color"]}"\n')
            f.write('    },\n')
        f.write('};\n')

    print(f"Generated {output_path} with {len(monsters)} monster entries.")


if __name__ == '__main__':
    defsym_file = './include/defsym.h'
    monsters_file = './include/monsters.h'
    output_file = 'monster_def.js'

    symbols = parse_defsym(defsym_file)
    monsters = parse_monsters(monsters_file, symbols)
    output_js(monsters, output_file)