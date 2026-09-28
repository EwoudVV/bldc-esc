import copy
import json
import re
from pathlib import Path


class Atom(str):
    pass


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)

    def read(index):
        if tokens[index] != "(":
            value = tokens[index]
            return (json.loads(value) if value.startswith('"') else Atom(value)), index + 1
        value = []
        index += 1
        while tokens[index] != ")":
            child, index = read(index)
            value.append(child)
        return value, index + 1

    return read(0)[0]


def dump(node, depth=0):
    if isinstance(node, Atom):
        return str(node)
    if isinstance(node, str):
        return json.dumps(node, ensure_ascii=False)
    if not isinstance(node, list):
        return str(node)
    if not any(isinstance(x, list) for x in node):
        return "(" + " ".join(dump(x) for x in node) + ")"
    start = []
    children = []
    for item in node:
        if isinstance(item, list) or children:
            children.append(item)
        else:
            start.append(item)
    return "(" + " ".join(dump(x) for x in start) + "\n" + "\n".join("  " * (depth + 1) + dump(x, depth + 1) for x in children) + "\n" + "  " * depth + ")"


def tag(name, *items):
    return [Atom(name), *items]


def child(node, name, default=None):
    return next((x for x in node if isinstance(x, list) and x and x[0] == name), default)


def walk(node):
    if isinstance(node, list):
        yield node
        for item in node:
            yield from walk(item)


library_root = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
cache = {}


def symbol(lib_id):
    if lib_id in cache:
        return copy.deepcopy(cache[lib_id])
    library, name = lib_id.split(":")
    source = (library_root / (library + ".kicad_sym")).read_text()
    node = parse(source[source.index('(symbol "' + name + '"'):])
    extends = child(node, "extends")
    if extends:
        inherited = symbol(library + ":" + extends[1])
        base_name = inherited[1]
        for override in node[2:]:
            if not isinstance(override, list) or override[0] in ("extends", "symbol"):
                continue
            key = tuple(override[:2]) if override[0] == "property" else (override[0],)
            found = False
            for index, item in enumerate(inherited):
                if isinstance(item, list):
                    item_key = tuple(item[:2]) if item[0] == "property" else (item[0],)
                    if item_key == key:
                        inherited[index] = copy.deepcopy(override)
                        found = True
                        break
            if not found:
                inherited.append(copy.deepcopy(override))
        node = inherited
        for item in node:
            if isinstance(item, list) and item[0] == "symbol":
                item[1] = name + item[1][len(base_name):]
        node[1] = name
    cache[lib_id] = copy.deepcopy(node)
    return node


def pins(node, unit=1):
    output = []
    for section in node:
        if not isinstance(section, list) or section[0] != "symbol":
            continue
        part = int(section[1].rsplit("_", 2)[1])
        if part not in (0, unit):
            continue
        for entry in section:
            if isinstance(entry, list) and entry[0] == "pin":
                output.append(entry)
    return output


if __name__ == "__main__":
    import sys
    for lib_id in sys.argv[1:]:
        node = symbol(lib_id)
        output = []
        for entry in walk(node):
            if entry and entry[0] == "pin":
                output.append({"number": child(entry, "number")[1], "name": child(entry, "name")[1], "at": child(entry, "at")[1:], "type": entry[1]})
        print(json.dumps({"lib_id": lib_id, "footprint": child(node, "property"), "pins": output}))
