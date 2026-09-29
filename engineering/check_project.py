import csv
import io
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
engineering = root / "engineering"
library = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/MCU_ST_STM32G4.kicad_sym")
failures = []
tables = {}


def check(condition, identifier):
    if not condition:
        failures.append(identifier)


def parse_one(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)

    def read(index):
        if tokens[index] != "(":
            token = tokens[index]
            return json.loads(token) if token.startswith('"') else token, index + 1
        node = []
        index += 1
        while tokens[index] != ")":
            value, index = read(index)
            node.append(value)
        return node, index + 1

    return read(0)[0]


def walk(node):
    if not isinstance(node, list):
        return
    yield node
    for item in node:
        if isinstance(item, list):
            yield from walk(item)


for path in sorted(engineering.glob("*.csv")):
    reader = csv.DictReader(io.StringIO(path.read_text()))
    rows = list(reader)
    check(bool(reader.fieldnames), "CSV_HEADER_" + path.name)
    for index, row in enumerate(rows, 2):
        check(None not in row and all(v is not None for v in row.values()), "CSV_WIDTH_" + path.name + "_" + str(index))
    tables[path.stem] = rows

sources = {row["id"] for row in tables["sources"]}
for name, rows in tables.items():
    if rows and "source_id" in rows[0]:
        for row in rows:
            check(row["source_id"] in sources, "SOURCE_" + name + "_" + str(row))
    if rows and "id" in rows[0]:
        check(len({row["id"] for row in rows}) == len(rows), "UNIQUE_ID_" + name)

pins = tables["pinmap"]
check({int(row["pin"]) for row in pins} == set(range(1, 101)), "MCU_PIN_COVERAGE")
check(len(pins) == 100, "MCU_PIN_DUPLICATES")
text = library.read_text()
symbol = parse_one(text[text.index('(symbol "STM32G474V_B-C-E_Tx"'):])
definitions = {}
for node in walk(symbol):
    if node and node[0] == "pin":
        fields = {item[0]: item[1] for item in node if isinstance(item, list) and len(item) > 1 and item[0] in ("name", "number")}
        definitions[fields["number"]] = (fields["name"], {item[1] for item in node if isinstance(item, list) and item and item[0] == "alternate"})
skip_functions = {"POWER", "NC", "GPIO_IN", "GPIO_OUT", "RESET"}
for row in pins:
    pin = row["pin"]
    check(pin in definitions and definitions[pin][0] == row["pad_name"], "MCU_PIN_NAME_" + pin)
    for field in ("function", "secondary_function"):
        value = row[field]
        if value and value not in skip_functions:
            check(value in definitions[pin][1], "MCU_FUNCTION_" + pin + "_" + value)
assigned = [row["function"] for row in pins if row["function"] not in skip_functions]
check(len(assigned) == len(set(assigned)), "PERIPHERAL_CHANNEL_DUPLICATE")
check({row["function"] for row in pins if row["net"] in ("I_PHASE_A", "I_PHASE_B", "I_PHASE_C") and row["function"].startswith("ADC")} == {"ADC1_IN2", "ADC2_IN4", "ADC3_IN12"}, "CURRENT_ADC_PARTITION")

computed = subprocess.check_output([sys.executable, str(engineering / "calculations.py")], text=True)
check(computed.strip() == (engineering / "calculations.csv").read_text().strip(), "CALCULATIONS_REPRODUCIBLE")
computed = subprocess.check_output([sys.executable, str(engineering / "electrical_checks.py")], text=True)
check(computed.strip() == (engineering / "electrical_checks.csv").read_text().strip(), "ELECTRICAL_CHECKS_REPRODUCIBLE")
computed = subprocess.check_output([sys.executable, str(engineering / "reference_checks.py")], text=True)
check(json.loads(computed) == json.loads((engineering / "reference_checks.json").read_text()), "REFERENCE_CHECKS_REPRODUCIBLE")
requirements = {row["id"]: row for row in tables["requirements"]}
check(float(requirements["R001"]["max"]) < float(requirements["R007"]["target"]), "BUS_FET_RATING")
check(float(requirements["R028"]["target"]) < float(requirements["R030"]["target"]), "ADC_VREF_VDDA_MARGIN")
check(float(requirements["R029"]["target"]) > 3, "DRV_VREF_MIN_MARGIN")

sch_paths = [root / "bldc-esc.kicad_sch", *sorted((root / "schematic").glob("*.kicad_sch"))]
check(len(sch_paths) == 17, "SCHEMATIC_SHEET_COUNT")
uuids = []
root_sch = parse_one(sch_paths[0].read_text())
for path in sch_paths:
    tree = parse_one(path.read_text())
    check(tree[0] == "kicad_sch", "SCHEMATIC_PARSE_" + path.name)
    for item in tree:
        if isinstance(item, list) and item and item[0] == "uuid":
            uuids.append(item[1])
for node in walk(root_sch):
    if node and node[0] == "property" and node[1] == "Sheetfile":
        check((root / node[2]).exists(), "SHEET_PATH_" + node[2])
check(len(set(uuids)) == 17, "SCHEMATIC_UUID_UNIQUE")
pcb = parse_one((root / "bldc-esc.kicad_pcb").read_text())
for item in pcb:
    if isinstance(item, list) and item:
        forbidden=("segment", "via", "zone") if '--placement' in sys.argv else ("segment", "via", "zone", "gr_line", "gr_rect", "gr_arc")
        check(item[0] not in forbidden, "PCB_STAGE_CONSTRAINT_" + item[0])
check(sum(isinstance(x,list) and x and x[0]=='footprint' for x in pcb)==len(tables['schematic_bom']), "PCB_STAGED_FOOTPRINT_COUNT")

print(json.dumps({"passed": not failures, "csv_files": len(tables), "pin_rows": len(pins), "schematic_sheets": len(sch_paths), "failures": failures}, indent=2))
sys.exit(bool(failures))
