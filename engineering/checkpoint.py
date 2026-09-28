import argparse
import csv
import datetime
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from capture import patch
from kicad_sexpr import child, parse

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',required=True)
parser.add_argument('--visual-reviewed',action='store_true')
parser.add_argument('--patch',action='store_true')
args=parser.parse_args()

def run(name):
    return json.loads(subprocess.check_output([sys.executable,str(ROOT/'engineering'/name)],text=True))

checks={name:run(name) for name in ['check_project.py','audit_m02.py','audit_m03.py','reference_checks.py','audit_connectors.py']}
generated=json.loads(subprocess.check_output([sys.executable,str(ROOT/'engineering/capture.py'),'--check'],text=True))
assert all(v['passed'] for v in checks.values())
assert not generated['mismatches']
drc=json.loads((ROOT/'work/qa/drc-staging.json').read_text())
baseline=subprocess.check_output(['git','rev-parse',args.baseline],cwd=ROOT,text=True).strip()
old=parse(subprocess.check_output(['git','show',baseline+':bldc-esc.kicad_pcb'],cwd=ROOT,text=True))
board=parse((ROOT/'bldc-esc.kicad_pcb').read_text())

def footprints(tree):
    return {next(p[2] for p in f if isinstance(p,list) and p[:2]==['property','Reference']):f
            for f in tree if isinstance(f,list) and f and f[0]=='footprint'}

before=footprints(old);after=footprints(board)
position=lambda f:tuple(float(x) for x in child(f,'at')[1:])
moved=[ref for ref in before.keys() & after.keys() if position(before[ref])!=position(after[ref])]
assert not moved,moved
assert not (before.keys()-after.keys())
xml=ET.parse(ROOT/'work/qa/bldc-esc.xml').getroot()
expected={(n.get('ref'),n.get('pin')):net.get('name') for net in xml.findall('./nets/net') for n in net.findall('node')}
errors=[];connected=0;pad_count=0
for ref,fp in after.items():
    for pad in fp:
        if not isinstance(pad,list) or not pad or pad[0]!='pad' or not pad[1]:continue
        pad_count+=1
        net=child(pad,'net')
        name=net[-1] if net else ''
        connected+=bool(name)
        if name!=expected.get((ref,pad[1]),''):errors.append([ref,pad[1],name,expected.get((ref,pad[1]),'')])
assert not errors,errors
assert not drc.get('schematic_parity',[])
counts=Counter(v['type'] for v in drc['violations'])
assert not (counts.keys()-{'invalid_outline','silk_overlap'}),counts
metrics=json.loads((ROOT/'engineering/schematic_drawing_metrics.json').read_text())
audit=checks['audit_m02.py'];independent=checks['audit_m03.py']
part_audit=list(csv.DictReader((ROOT/'engineering/bom_audit.csv').open()))
assert len(part_audit)==len({p['MPN'] for p in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open()) if p['exclude_from_BOM']=='false'})
assert all(p['status']=='part_spec_checked' for p in part_audit)
snapshot={
    'milestone':'M03_CLOSEOUT','devlog':'04','state':'freeze_candidate_pending_user_review','date':datetime.date.today().isoformat(),
    'kicad_version':'10.0.4',
    'schematic':{
        'sheets':17,'child_sheets':16,'physical_footprints':len(after),
        'erc_errors':audit['erc_errors'],'erc_warnings':audit['erc_warnings'],
        'intended_pin_connections':audit['intended_connections'],'netlist_pin_connections':audit['netlist_connections'],
        'nets':audit['nets'],'netlist_mismatches':len(audit['errors']),
        'independent_pin_contracts':independent['independent_pin_contracts'],'logic_cases':independent['logic_cases'],
        'generated_files_match':True,'hardware_signoff':False,
        'presentation':'native_PDF_render_reviewed' if args.visual_reviewed else 'visual_review_pending',
        'page_formats':dict(Counter(v['paper_after'] for v in metrics.values())),
    },
    'pcb':{
        'native_reload':'passed','copper_layers':4,'footprints':len(after),'numbered_pads':pad_count,
        'connected_pads':connected,'pad_net_mismatches':len(errors),'schematic_parity_issues':len(drc.get('schematic_parity',[])),
        'tracks':0,'zones':0,'outline':'absent','placement':'staging_grid_only','fabricator':'PCBWay',
        'fabrication_stackup':'2oz_outer_1oz_inner_exact_dielectrics_pending','drc_counts':dict(counts),
        'unconnected_items_reported':len(drc['unconnected_items']),'placement_changes':len(moved),
        'baseline_footprints_preserved':len(before),'removed_footprints':[],
        'new_footprints':sorted(after.keys()-before.keys()),
    },
    'BOM':{'unique_order_codes':len(part_audit),'part_spec_audit':'passed','physical_fit_tested':False,'stock_reserved':False},
    'reference':{'static_budget_checks':len(checks['reference_checks.py']['checks']),'passed':True,'bench_validated':False},
    'connector_audit':checks['audit_connectors.py'],
    'critical_correction':'J101_pad1_GND_pad2_VBUS_old_dcad1e4_must_not_be_manufactured',
    'pending':['user_schematic_review','exact_fabrication_stackup','user_placement_and_routing','layout_review_and_DRC',
               'purchase_stock_refresh','physical_connector_fit','reference_and_reset_transient_tests','thermal_validation',
               'motor_OEM_pinout','firmware','physical_bringup'],
    'bench_measurements':'none','git_action':'no_stage_commit_or_push','baseline_commit':baseline,
    'exports':{'schematic_pdf':'engineering/exports/schematic-review.pdf','BOM':'engineering/schematic_bom.csv','BOM_audit':'engineering/bom_audit.csv'},
}
paths=[ROOT/'bldc-esc.kicad_sch',ROOT/'bldc-esc.kicad_pcb',ROOT/'bldc-esc.kicad_pro',ROOT/'bldc-esc.kicad_sym',
       ROOT/'engineering/exports/schematic-review.pdf',ROOT/'engineering/schematic_bom.csv',ROOT/'engineering/reference_checks.json',
       *sorted((ROOT/'schematic').glob('*.kicad_sch'))]
snapshot['file_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
content=json.dumps(snapshot,indent=2)+'\n'
if args.patch:
    print('*** Begin Patch\n'+patch('engineering/verification.json',content)+'*** End Patch')
else:print(content,end='')
