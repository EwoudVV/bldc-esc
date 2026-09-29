import argparse
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from capture import patch
from kicad_sexpr import child
from placement_geometry import ROOT,read_board,rotate

parser=argparse.ArgumentParser()
parser.add_argument('--board',default='bldc-esc.kicad_pcb')
parser.add_argument('--drc',default='work/qa/drc-placement.json')
parser.add_argument('--netlist',default='work/qa/bldc-esc.xml')
parser.add_argument('--patch',action='store_true')
args=parser.parse_args()
tree,parts=read_board(ROOT/args.board)
plan=json.loads((ROOT/'engineering/placement.json').read_text())
bom={r['reference']:r for r in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open())}
netlist=ET.parse(ROOT/args.netlist).getroot()
expected={(p.get('ref'),p.get('pin')):n.get('name') for n in netlist.findall('./nets/net') for p in n.findall('node')}
errors=[]
if set(parts)!=set(bom):errors.append(['COMPONENT_SET_MISMATCH'])
for ref,p in parts.items():
    target=plan['components'][ref]
    if any(abs(p[k]-target[k])>1e-5 for k in ['x','y','angle']):errors.append(['PLACEMENT_MISMATCH',ref])
    if p['layer']!='F.Cu':errors.append(['UNEXPECTED_SIDE',ref])
    for pad in p['pads']:
        if pad['number'] and pad['net']!=expected.get((ref,pad['number']),''):
            errors.append(['PAD_NET',ref,pad['number'],pad['net'],expected.get((ref,pad['number']),'')])

def pad(ref,number):
    p=parts[ref];q=next(q for q in p['pads'] if q['number']==str(number))
    x,y=rotate(q['x'],q['y'],p['angle'])
    return (p['x']+x,p['y']+y)

def distance(a,b):
    pa,pb=pad(*a),pad(*b)
    return round(math.hypot(pa[0]-pb[0],pa[1]-pb[1]),3)

phase=[]
for i,name in enumerate('ABC'):
    b=210+20*i;hi='Q'+str(201+2*i);lo='Q'+str(202+2*i);sh='R'+str(b+4);amp='U'+str(202+i)
    row={'phase':name,'HS_gate_resistor_to_gate_mm':distance(('R'+str(b),2),(hi,4)),
         'LS_gate_resistor_to_gate_mm':distance(('R'+str(b+2),2),(lo,4)),
         'Kelvin_positive_pad_centres_mm':distance((sh,2),(amp,8)),
         'Kelvin_negative_pad_centres_mm':distance((sh,3),(amp,1)),
         'LS_source_to_shunt_pad_centres_mm':min(distance((lo,p),(sh,1)) for p in [1,2,3]),
         'driver_to_HS_gate_resistor_mm':distance(('U201',[6,15,16][i]),('R'+str(b),1)),
         'driver_to_LS_gate_resistor_mm':distance(('U201',[8,13,18][i]),('R'+str(b+2),1))}
    phase.append(row)
    if max(row['HS_gate_resistor_to_gate_mm'],row['LS_gate_resistor_to_gate_mm'])>5:errors.append(['GATE_RESISTOR_TOO_FAR',name])
    if max(row['Kelvin_positive_pad_centres_mm'],row['Kelvin_negative_pad_centres_mm'])>7:errors.append(['KELVIN_PAIR_TOO_FAR',name])
counts=Counter(str(n[0]) for n in tree if isinstance(n,list) and n)
if counts['segment'] or counts['via'] or counts['zone']:errors.append(['ROUTING_OR_ZONE_PRESENT'])
drc=json.loads((ROOT/args.drc).read_text())
violations=Counter(v['type'] for v in drc['violations'])
for v in drc['violations']:
    accepted=v['type']=='silk_edge_clearance' and any('J101' in x.get('description','') for x in v['items'])
    if not accepted:errors.append(['DRC',v['type'],v['description']])
parity=drc.get('schematic_parity',[])
if parity:errors.append(['SCHEMATIC_PARITY',len(parity)])
result={'passed':not errors,'stage':'placement_review_not_routing_or_fabrication_release','date':'2026-09-29',
        'board_size_mm':[plan['outline'][2]-plan['outline'][0],plan['outline'][3]-plan['outline'][1]],
        'footprints':len(parts),'front_components':sum(p['layer']=='F.Cu' for p in parts.values()),'back_components':0,
        'tracks':counts['segment'],'vias':counts['via'],'zones':counts['zone'],'outline_segments':counts['gr_line'],
        'schematic_parity_issues':len(parity),'drc_counts':dict(violations),'unconnected_items_reported':len(drc['unconnected_items']),
        'accepted_placement_findings':['J101_factory_silkscreen_overhangs_board_edge_not_copper'],
        'phase_geometry':phase,'geometry_scope':'straight_line_pad_centre_distances_not_routed_lengths_or_inductance',
        'reference_fields':plan['reference_fields'],'bench_validated':False,
        'pending':['routing','exact_fabrication_stackup','copper_and_thermal_review','mounting_hole_and_cable_strain_relief_details','final_silkscreen','fresh_editor_update_round_trip','bench_bringup'],
        'errors':errors,'file_sha256':{args.board:hashlib.sha256((ROOT/args.board).read_bytes()).hexdigest(),
            'engineering/placement.json':hashlib.sha256((ROOT/'engineering/placement.json').read_bytes()).hexdigest()}}
if args.patch:print('*** Begin Patch\n'+patch('engineering/placement-checks.json',json.dumps(result,indent=2)+'\n')+'*** End Patch')
else:print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
