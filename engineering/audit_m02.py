import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from kicad_sexpr import child, parse, pins, walk

root=Path(__file__).resolve().parent.parent
errors=[]


def fail(kind,*data):
    errors.append([kind,*data])


expected={(r['reference'],r['pin']):r['net'] for r in csv.DictReader((root/'engineering/connection_matrix.csv').open()) if not r['reference'].startswith('#')}
netlist=ET.parse(root/'work/qa/bldc-esc.xml').getroot()
actual={}
actual_partitions=defaultdict(set)
for net in netlist.findall('./nets/net'):
    full=net.get('name')
    for node in net.findall('node'):
        key=(node.get('ref'),node.get('pin'))
        actual[key]=full.split('/')[-1]
        if key in expected:actual_partitions[full].add(expected[key])
for key,net in expected.items():
    if actual.get(key)!=net:fail('PIN_NET',key,net,actual.get(key))
for net,names in actual_partitions.items():
    if len(names)>1:fail('MERGED_NETS',net,sorted(names))

erc=json.loads((root/'work/qa/erc-m02.json').read_text())
violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
for violation in violations:fail('ERC',violation['severity'],violation['description'])

local_library=parse((root/'bldc-esc.kicad_sym').read_text())
local_names={n[1] for n in local_library if isinstance(n,list) and n and n[0]=='symbol'}
bom=list(csv.DictReader((root/'engineering/schematic_bom.csv').open()))
fp_base=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
for part in bom:
    library,name=part['footprint'].split(':')
    path=(root/'bldc-esc.pretty' if library=='bldc-esc' else fp_base/(library+'.pretty'))/(name+'.kicad_mod')
    if not path.exists():fail('FOOTPRINT',part['reference'],str(path))

byref={r['reference']:r for r in bom}
for reference,pin,net in [('U201','5','DRV_VCP'),('C204','1','DRV_VCP'),('C204','2','VBUS'),
    ('C203','1','DRV_CPH'),('C203','2','DRV_CPL'),('U201','24','3V3_A'),('U501','36','VREF_3V0'),
    ('U501','95','BOOT0'),('U501','78','I2C_SCL'),('U705','5','nFAULT_LATCH'),
    ('U705','3','nPWM_ENABLE'),('U706','1','nPWM_ENABLE'),('U706','19','nPWM_ENABLE'),
    ('U301','6','5V_BUS'),('U302','5','nDUMP_REQUEST'),('U302','6','BRK_ARMED'),
    ('U302','4','DUMP_SOURCE'),('U307','6','BRK_CLEAR'),('U303','3','DUMP_SOURCE'),
    ('U303','4','GND'),('J401','SH','CHASSIS')]:
    if actual.get((reference,pin))!=net:fail('CRITICAL_CONNECTION',reference,pin,net)
for i,phase in enumerate('ABC'):
    high='Q'+str(201+2*i);low='Q'+str(202+2*i);shunt='R'+str(214+20*i)
    for ref,pin,net in [(high,'5','VBUS'),(high,'1','PHASE_'+phase),(low,'5','PHASE_'+phase),
        (low,'1','SOURCE_'+phase),(shunt,'1','SOURCE_'+phase),(shunt,'2','KS_'+phase+'_P'),
        (shunt,'3','KS_'+phase+'_N'),(shunt,'4','GND')]:
        if actual.get((ref,pin))!=net:fail('BRIDGE_CONNECTION',ref,pin,net)

q=0;previous_clock=0
for safe,clock,expected_q in [(0,0,0),(1,0,0),(1,1,1),(0,1,0),(1,1,0),(1,0,0),(1,1,1)]:
    if not safe:q=0
    elif clock and not previous_clock:q=1
    if q!=expected_q:fail('ARM_LATCH_SEQUENCE',safe,clock)
    previous_clock=clock

for ref,pin,net in [('U702','5','WD_RUN'),('U711','1','SYSTEM_GOOD_PRE'),('U711','2','WD_RUN'),
    ('U711','4','SYSTEM_GOOD'),('U712','1','DRV_ENABLE_PRE'),('U712','2','WD_RUN'),('U712','4','DRV_ENABLE')]:
    if actual.get((ref,pin))!=net:fail('SERVICE_INTERLOCK',ref,pin,net)

for sheet in sorted((root/'schematic').glob('*.kicad_sch')):
    data=parse(sheet.read_text())
    libs={n[1]:n for n in child(data,'lib_symbols')[1:]}
    counts=defaultdict(list)
    for item in data:
        if not isinstance(item,list) or not item or item[0]!='symbol':continue
        reference=next(x[2] for x in item if isinstance(x,list) and x[0]=='property' and x[1]=='Reference')
        lib=libs[child(item,'lib_id')[1]]
        at=child(item,'at');x,y,a=map(float,at[1:]);angle=math.radians(a)
        for pin in pins(lib,int(child(item,'unit')[1])):
            number=str(child(pin,'number')[1]);net=expected.get((reference,number))
            if net is None:continue
            p=child(pin,'at');px,py=map(float,p[1:3])
            position=(round(x+px*math.cos(angle)-py*math.sin(angle),4),round(y-px*math.sin(angle)-py*math.cos(angle),4))
            counts[position].append((reference,number,net))
    for position,entries in counts.items():
        if len({x[2] for x in entries})>1:fail('PIN_COLLISION',sheet.name,position,entries)

output={'passed':not errors,'physical_components':len(bom),'intended_connections':len(expected),
        'netlist_connections':len(actual),'nets':len(netlist.findall('./nets/net')),
        'erc_errors':sum(v['severity']=='error' for v in violations),
        'erc_warnings':sum(v['severity']=='warning' for v in violations),'custom_symbols':len(local_names),
        'errors':errors}
print(json.dumps(output,indent=2))
sys.exit(bool(errors))
