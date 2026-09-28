import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_sexpr import child, parse

ROOT=Path(__file__).resolve().parent.parent
FP_ROOT=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
rows={r['reference']:r for r in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open())}
xml=ET.parse(ROOT/'work/qa/bldc-esc.xml').getroot()
nets={(p.get('ref'),p.get('pin')):n.get('name').split('/')[-1]
      for n in xml.findall('./nets/net') for p in n.findall('node')}
errors=[]


def require(ok,name):
    if not ok:errors.append(name)


def footprint(ref):
    lib,name=rows[ref]['footprint'].split(':')
    p=(ROOT/'bldc-esc.pretty' if lib=='bldc-esc' else FP_ROOT/(lib+'.pretty'))/(name+'.kicad_mod')
    return parse(p.read_text())


def pads(tree):
    return [p for p in tree if isinstance(p,list) and p and p[0]=='pad' and p[1]]


# Use the polarity marks in the actual assigned XT60 footprint as a second source.
xt=footprint('J101');xtpads=pads(xt)
marks=set()
for item in xt:
    if isinstance(item,list) and item[:2]==['fp_text','user'] and item[2] in ('+','-'):
        marks.add(item[2])
        x,y=map(float,child(item,'at')[1:3])
        nearest=min(xtpads,key=lambda p:math.hypot(float(child(p,'at')[1])-x,float(child(p,'at')[2])-y))
        expected='VBUS' if item[2]=='+' else 'GND'
        require(nets.get(('J101',nearest[1]))==expected,'XT60_MARK_'+item[2])
require(marks=={'+','-'},'XT60_BOTH_POLARITY_MARKS_PRESENT')

swd=footprint('J501');sp=pads(swd)
require({p[1] for p in sp}=={'1','2','3','4','5','6','8','9','10'},'SWD_PIN7_OMITTED')
require(rows['J501']['MPN']=='FTSH-105-01-L-DV-007-K','SWD_ORDER_CODE')
for p in sp:
    num=int(p[1]);x,y=map(float,child(p,'at')[1:3]);w,h=map(float,child(p,'size')[1:3])
    require(abs(x-(-2.032 if num%2 else 2.032))<1e-5,'SWD_X_'+str(num))
    require(abs(y-(-2.54+1.27*((num-1)//2)))<1e-5,'SWD_Y_'+str(num))
    require(abs(w-2.794)<1e-5 and abs(h-.7366)<1e-5,'SWD_PAD_'+str(num))

f=pads(footprint('F401'))
require(rows['F401']['MPN']=='MF-PSMF050X-2','USB_FUSE_MPN')
for p in f:
    require(list(map(float,child(p,'size')[1:3]))==[1.,1.5],'USB_FUSE_PAD')
    require(abs(float(child(p,'at')[1]))==1.1,'USB_FUSE_POSITION')

for ref in ['J601','J602','J701','J702','J801','J802','J803','J804','J805','J806']:
    pp=[p for p in pads(footprint(ref)) if p[1].isdigit()]
    pp.sort(key=lambda p:int(p[1]))
    for a,b in zip(pp,pp[1:]):
        require(abs(float(child(b,'at')[1])-float(child(a,'at')[1])-1.25)<1e-6,'GH_PITCH_'+ref)
    for p in pp:
        require(list(map(float,child(p,'size')[1:3]))==[.6,1.7],'GH_PAD_'+ref)

require(nets[('J601','1')]=='5V_HALL' and nets[('J601','2')]=='GND','HALL_SUPPLY_PIN_ORDER')
require(nets[('J602','1')]=='5V_ENCODER' and nets[('J602','2')]=='GND','ENCODER_SUPPLY_PIN_ORDER')
require(nets[('J301','1')]=='VBUS' and nets[('J301','2')]=='DUMP_SW','BRAKE_RESISTOR_PIN_ORDER')
print(json.dumps({'passed':not errors,'scope':'schematic_nets_and_assigned_footprint_geometry_not_physical_mating_test','errors':errors},indent=2))
raise SystemExit(bool(errors))
