#!/usr/bin/env python3
"""objects.h classes stay contiguous and in the defsym class order.

Startup panics with "objects[N] class #C not in order!" when a later
class is followed by an earlier one. The Gibraltar stones and the
Grand Grimoire are tools and must sit in the tool section.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def strip_comments(src):
    out = []
    i = 0
    n = len(src)
    while i < n:
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                break
            out.append(" ")
            i = j + 2
        elif src.startswith("//", i):
            j = src.find("\n", i)
            out.append("\n" if j >= 0 else "")
            i = n if j < 0 else j
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i : j + 1])
            i = j + 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def class_order():
    text = (ROOT / "include/defsym.h").read_text()
    order = {}
    pat = re.compile(
        r"OBJCLASS2?\(\s*(\d+)\s*,\s*(?:'[^']*'|0x[0-9A-Fa-f]+|\d+)\s*,\s*([A-Za-z0-9_]+)"
    )
    for match in pat.finditer(text):
        order[match.group(2) + "_CLASS"] = int(match.group(1))
    return order


def macro_classes(text):
    """Map an object-defining macro to the class it emits."""
    direct = {}
    calls = {}
    for match in re.finditer(
        r"(?m)^#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(.*)$", text
    ):
        name, body = match.group(1), match.group(3)
        found = re.findall(r"\b([A-Z][A-Z0-9_]*_CLASS)\b", body)
        if len(set(found)) == 1:
            direct[name] = found[0]
        calls[name] = re.findall(r"\b([A-Z][A-Z0-9_]*)\s*\(", body)
    resolved = dict(direct)
    changed = True
    while changed:
        changed = False
        for name, callees in calls.items():
            if name in resolved:
                continue
            for callee in callees:
                if callee in resolved:
                    resolved[name] = resolved[callee]
                    changed = True
                    break
    return resolved


def split_args(argtext):
    args = []
    depth = 0
    cur = []
    for ch in argtext:
        if ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        args.append("".join(cur).strip())
    return args


def object_classes(text, known):
    """Classes of top-level object entries, fencepost excluded."""
    # The terminator is only in the init arrays. It is not a real object.
    text = re.sub(
        r"#if defined\(OBJECTS_DESCR_INIT\) \|\| defined\(OBJECTS_INIT\).*?#endif",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(r"(?m)^#define\s+.*$", "", text)
    classes = []
    i = 0
    depth = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        if ch == "(" and depth == 0:
            j = i - 1
            while j >= 0 and text[j].isspace():
                j -= 1
            k = j
            while k >= 0 and (text[k].isalnum() or text[k] == "_"):
                k -= 1
            name = text[k + 1 : j + 1]
            end = match_paren(text, i)
            args = split_args(text[i + 1 : end])
            if name == "OBJECT" and len(args) >= 4:
                classes.append(args[3].strip())
            elif name == "GENERIC" and len(args) >= 2:
                classes.append(args[1].strip())
            elif name in known:
                classes.append(known[name])
            i = end + 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        i += 1
    return classes


def match_paren(text, open_at):
    depth = 0
    i = open_at
    while i < len(text):
        if text[i] == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise AssertionError("unbalanced parenthesis in objects.h")


class ObjectOrderTests(unittest.TestCase):
    def test_classes_are_contiguous_and_in_order(self):
        order = class_order()
        self.assertEqual(order["TOOL_CLASS"], 6)
        self.assertLess(order["TOOL_CLASS"], order["FOOD_CLASS"])
        self.assertLess(order["ROCK_CLASS"], order["ANOINTING_CLASS"])
        raw = strip_comments((ROOT / "include/objects.h").read_text())
        raw = raw.replace("\\\n", " ")
        known = macro_classes(raw)
        classes = object_classes(raw, known)
        self.assertGreater(len(classes), 100)
        for name in classes:
            self.assertIn(name, order, name)
        # Slots 1..18 are the generic object for that class. Slot 0 is
        # the strange object. init_objects checks order only after those.
        self.assertEqual(classes[0], "ILLOBJ_CLASS")
        for idx in range(1, 19):
            self.assertEqual(order[classes[idx]], idx, classes[idx])
        real = classes[19:]
        numbers = [order[name] for name in real]
        for prev, this in zip(numbers, numbers[1:]):
            self.assertGreaterEqual(this, prev)
        # One run per class: leaving a class means it does not return.
        seen = set()
        current = None
        for name in real:
            if name != current:
                self.assertNotIn(name, seen)
                if current is not None:
                    seen.add(current)
                current = name

    def test_branch_tools_stay_in_the_tool_section(self):
        text = (ROOT / "include/objects.h").read_text()
        section = text.split("#define TOOL(", 1)[1].split("#undef TOOL", 1)[0]
        for name in (
            "LAMP_OF_GODS_WORD",
            "PEBBLE_FROM_GIBRALTAR",
            "FIERY_PEBBLE_FROM_GIBRALTAR",
            "SMOOTH_STONE_FROM_GIBRALTAR",
            "GRAND_GRIMOIRE",
        ):
            self.assertIn(name, section)
        after = text.split("#undef TOOL", 1)[1]
        for name in (
            "PEBBLE_FROM_GIBRALTAR",
            "FIERY_PEBBLE_FROM_GIBRALTAR",
            "SMOOTH_STONE_FROM_GIBRALTAR",
            "GRAND_GRIMOIRE",
            "LAMP_OF_GODS_WORD",
        ):
            self.assertNotIn(name, after)


if __name__ == "__main__":
    unittest.main()
