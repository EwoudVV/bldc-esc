import csv
import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent.parent
evidence=json.loads((ROOT/'engineering/bom_evidence.json').read_text())
parts=list(csv.DictReader((ROOT/'engineering/schematic_bom.csv').open()))
groups=defaultdict(list)
for part in parts:
    if part['exclude_from_BOM']=='false':groups[part['MPN']].append(part)
failures=[];report=[]
pdf_text={}


def nominal(s):
    s=s.split()[0].replace(',','')
    scale={'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'M':1e6}
    return float(s[:-1])*scale[s[-1]] if s[-1] in scale else float(s)


def clean(text):
    return text.replace('\u200b','').replace('\ufeff','')


for mpn,instances in sorted(groups.items()):
    part=instances[0]
    errors=[]
    source=evidence.get(mpn)
    if source is None:
        failures.append(['MISSING_EVIDENCE',mpn]);continue
    if not part['manufacturer']:errors.append('manufacturer_missing')
    for p in instances:
        if p['footprint']!=part['footprint']:errors.append('inconsistent_footprint')
    if source.get('pdf'):
        path=ROOT/'work/datasheets'/source['pdf']
        if not path.exists():errors.append('source_cache_missing')
        else:
            if path not in pdf_text:
                reader=PdfReader(path)
                pdf_text[path]=clean('\n'.join(p.extract_text() for p in reader.pages))
            text=pdf_text[path]
            compact=''.join(text.split())
            key=source.get('search_key',mpn)
            if key not in compact:errors.append('order_code_not_in_source')
            if mpn.startswith(('RC','RT','C0603C','C0805C','C1206C')):
                if mpn.startswith(('RC','RT')):
                    match=re.search(r'Resistance\s+([\d.,]+)\s*(mOhms|kOhms|MOhms|Ohms)',text)
                    factors={'Ohms':1,'mOhms':1e-3,'kOhms':1e3,'MOhms':1e6}
                else:
                    match=re.search(r'Capacitance\s+([\d.,]+)\s*(pF|nF|uF|µF|μF)',text)
                    factors={'pF':1e-12,'nF':1e-9,'uF':1e-6,'µF':1e-6,'μF':1e-6}
                if match:
                    actual=float(match[1].replace(',',''))*factors[match[2]]
                    for p in instances:
                        if not math.isclose(nominal(p['value']),actual,rel_tol=1e-7,abs_tol=1e-15):errors.append('nominal_value_mismatch_'+p['reference'])
                else:errors.append('nominal_value_not_parsed')
                code=mpn[2:6] if mpn.startswith(('RC','RT')) else mpn[1:5]
                if code not in compact or code not in part['footprint']:errors.append('case_size_mismatch')
                if mpn.startswith('C'):
                    match=re.search(r'Voltage DC\s+([\d,]+)\s*VDC',text)
                    if match:
                        rating=float(match[1].replace(',',''))
                        for p in instances:
                            asked=nominal(p['value'].split()[1].removesuffix('V'))
                            if rating<asked:errors.append('voltage_rating_mismatch_'+p['reference'])
                    else:errors.append('voltage_not_parsed')
    for error in errors:failures.append([mpn,error])
    report.append({'MPN':mpn,'manufacturer':part['manufacturer'],'quantity_fitted':sum(p['DNP']=='false' for p in instances),
        'quantity_optional':sum(p['DNP']=='true' for p in instances),'references':' '.join(p['reference'] for p in instances),
        'value':part['value'],'footprint':part['footprint'],'source_url':source['url'],
        'basis':source['basis'],'status':'failed' if errors else 'part_spec_checked','checked_date':'2026-09-28'})

if '--csv' in sys.argv:
    out=csv.DictWriter(sys.stdout,fieldnames=list(report[0]),lineterminator='\n');out.writeheader();out.writerows(report)
else:
    print(json.dumps({'passed':not failures,'unique_order_codes':len(groups),'evidence_rows':len(report),
        'scope':'part_identity_values_ratings_and_package_selection_not_stock_reservation_or_board_validation',
        'failures':failures},indent=2))
raise SystemExit(bool(failures))
