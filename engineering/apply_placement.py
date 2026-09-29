import argparse
import hashlib
import json
import math
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from capture import patch
from kicad_sexpr import Atom as A,child,dump,parse,tag
from placement_geometry import ROOT,ref,rotate

parser=argparse.ArgumentParser()
parser.add_argument('--input',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--plan')
parser.add_argument('--netlist',required=True)
parser.add_argument('--remove-provisional-zone',action='store_true')
args=parser.parse_args()
if (ROOT/args.output).resolve()==(ROOT/'bldc-esc.kicad_pcb').resolve():
    current=(ROOT/args.output).read_bytes()
    allowed=current==(ROOT/args.input).read_bytes()
    report=ROOT/'engineering/placement-checks.json'
    if report.exists():
        old=json.loads(report.read_text()).get('file_sha256',{}).get('bldc-esc.kicad_pcb')
        allowed|=hashlib.sha256(current).hexdigest()==old
    if not allowed:raise RuntimeError('The canonical board has changed since the placement check; preserve and review those edits first')
    target=parse(current.decode())
    if any(isinstance(n,list) and n and n[0] in ('segment','via','zone') for n in target) and current!=(ROOT/args.input).read_bytes():
        raise RuntimeError('Do not overwrite routing or copper with a placement rebuild')
tree=parse((ROOT/args.input).read_text())
assert not any(isinstance(v,list) and v[0] in ('segment','via') for v in tree)
source=ET.parse(ROOT/args.netlist).getroot()
expected={(p.get('ref'),p.get('pin')):n.get('name') for n in source.findall('./nets/net') for p in n.findall('node')}
footprints=[f for f in tree if isinstance(f,list) and f[0]=='footprint']
assert len(footprints)==449 and len({ref(f) for f in footprints})==449
plan=json.loads((ROOT/args.plan).read_text()) if args.plan else None
if plan:assert set(plan['components'])=={ref(f) for f in footprints}
corrected=[]
for fp in footprints:
    name=ref(fp);at=child(fp,'at');oldangle=float(at[3]) if len(at)>3 else 0
    for pad in fp:
        if not isinstance(pad,list) or not pad or pad[0]!='pad' or not pad[1]:continue
        want=expected.get((name,pad[1]),'');net=child(pad,'net')
        if (net[-1] if net else '')!=want:
            corrected.append([name,pad[1],net[-1] if net else '',want])
            if net:pad.remove(net)
            if want:pad.append(tag('net',want))
    if not plan:continue
    p=plan['components'][name];angle=p['angle'];delta=angle-oldangle
    assert p['side']=='F.Cu' and child(fp,'layer')[1]=='F.Cu'
    at[1:]=[p['x'],p['y'],angle]
    for item in fp:
        if not isinstance(item,list) or not item:continue
        if item[0]=='pad':
            pos=child(item,'at')
            old=float(pos[3]) if len(pos)>3 else 0
            pos[3:]=[(old+delta)%360]
        elif item[0] in ('property','fp_text'):
            pos=child(item,'at')
            if pos:
                old=float(pos[3]) if len(pos)>3 else 0
                pos[3:]=[(old+delta)%360]
    reference=next(q for q in fp if isinstance(q,list) and q[:2]==['property','Reference'])
    px,py=rotate(p['ref_x']-p['x'],p['ref_y']-p['y'],-angle)
    child(reference,'at')[1:]=[round(px,6),round(py,6),p.get('ref_angle',0)]
    child(reference,'layer')[1]=p.get('ref_layer','F.SilkS')
    effects=child(reference,'effects')
    justify=child(effects,'justify')
    if justify:effects.remove(justify)
    if p.get('ref_layer')=='B.SilkS':effects.append(tag('justify',A('mirror')))
    font=child(child(reference,'effects'),'font')
    child(font,'size')[1:]=[.8,.8]
    thickness=child(font,'thickness')
    if thickness:thickness[1]=.12
    else:font.append(tag('thickness',.12))
    value=next(q for q in fp if isinstance(q,list) and q[:2]==['property','Value'])
    if not child(value,'hide'):value.append(tag('hide',A('yes')))
zones=[z for z in tree if isinstance(z,list) and z[0]=='zone']
for zone in zones:
    if args.remove_provisional_zone:
        assert child(zone,'uuid')[1]=='14944603-a409-4ec0-86d8-8c9d10c1da87'
        tree.remove(zone)
    else:
        zone[:]=[z for z in zone if not(isinstance(z,list) and z[0] in ('filled_polygon','filled_areas_thickness'))]
if plan:
    assert not any(isinstance(d,list) and str(d[0]).startswith('gr_') and child(d,'layer',[None,''])[1]=='Edge.Cuts' for d in tree)
    x0,y0,x1,y1=plan['outline']
    for i,(start,end) in enumerate([((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]):
        tree.append(tag('gr_line',tag('start',*start),tag('end',*end),tag('stroke',tag('width',.05),tag('type',A('default'))),
            tag('layer','Edge.Cuts'),tag('uuid',str(uuid.uuid5(uuid.NAMESPACE_URL,'bldc-esc-placement-outline-'+str(i))))))
    for i,label in enumerate(plan.get('legends',[])):
        tree.append(tag('gr_text',label['text'],tag('at',label['x'],label['y'],label['angle']),tag('layer','F.SilkS'),
            tag('uuid',str(uuid.uuid5(uuid.NAMESPACE_URL,'bldc-esc-placement-legend-'+str(i)))),
            tag('effects',tag('font',tag('size',label['size'],label['size']),tag('thickness',.12)))))
content=dump(tree)+'\n'
print('*** Begin Patch\n'+patch(args.output,content)+'*** End Patch')
