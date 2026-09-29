import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from placement_geometry import ROOT,read_board,rotate

BASE=ROOT/'bldc-esc.kicad_pcb'
OUTLINE=(0,0,116,112)
ORIGIN=(50,50)
_,PARTS=read_board(BASE)
BOM={r['reference']:r for r in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open())}
PLACED={}
RESERVES=[(0,0,8,8),(108,0,116,8),(0,104,8,112),(108,104,116,112)]
AUTO_KEEPOUT=[]

def box(ref,x,y,angle):
    b=PARTS[ref]['courtyard']
    p=[rotate(xx,yy,angle) for xx in (b[0],b[2]) for yy in (b[1],b[3])]
    return (x+min(q[0] for q in p),y+min(q[1] for q in p),x+max(q[0] for q in p),y+max(q[1] for q in p))

def put(ref,x,y,angle=0,group=None):
    assert ref in PARTS,ref
    assert ref not in PLACED,ref
    PLACED[ref]={'x':x,'y':y,'angle':angle,'side':'F.Cu','group':group or BOM[ref]['sheet'],'fixed':True}

def fixed():
    # A mirrored capacitor bank leaves a central ground-return channel.
    for col,refs in enumerate([['C101','C102','C103','C104','C105'],['C106','C107','C108','C115','C116']]):
        for row,ref in enumerate(refs):put(ref,25+14*col,15+14*row,0 if col==0 else 180,'DC_LINK')
    put('J101',14,32,90,'DC_INPUT');put('D101',14.5,42,270,'DC_INPUT')
    put('J102',89,6,180,'MOTOR_OUTPUT')
    # C, B, A from left to right match the DRV8353 outputs after a 180-degree rotation.
    for i,(phase,hsx) in enumerate([('A',92.5),('B',71),('C',49.5)]):
        lsx=hsx+7;b=210+20*i
        put('Q'+str(201+2*i),hsx,25,270,'PHASE_'+phase)
        put('Q'+str(202+2*i),lsx,25,90,'PHASE_'+phase)
        put('R'+str(b+4),lsx+.85,37.5,270,'PHASE_'+phase)
        put('U'+str(202+i),lsx+8,37.5,90,'CURRENT_'+phase)
        put('R'+str(b),hsx-4.1,22.175,0,'GATE_'+phase)
        put('R'+str(b+1),hsx-1.905,19.0,90,'GATE_'+phase)
        put('R'+str(b+2),lsx+1.905,30.0,90,'GATE_'+phase)
        put('R'+str(b+3),lsx+4.7,30.0,90,'GATE_'+phase)
        put('C'+str(b),hsx,34.0,0,'BYPASS_'+phase)
        put('C'+str(b+1),hsx,37.3,0,'BYPASS_'+phase)
        put('C'+str(b+2),lsx+8.5,32.7,90,'CURRENT_'+phase)
    put('U201',75,46,180,'GATE_DRIVER')
    put('C203',80,51,90,'GATE_DRIVER');put('C204',80.7,42,90,'GATE_DRIVER')
    put('C202',81,47.3,90,'GATE_DRIVER');put('C205',76.5,51,0,'GATE_DRIVER')
    put('C206',73,51,0,'GATE_DRIVER');put('C207',69.8,46,90,'GATE_DRIVER')
    put('C201',61,44,0,'GATE_DRIVER')
    # Independent brake power stage, away from the precision reference.
    put('J301',7,61,270,'BRAKE_POWER');put('Q301',14,69,180,'BRAKE_POWER')
    put('R310',16,79,270,'BRAKE_POWER');put('D301',15.75,61,270,'BRAKE_POWER')
    put('U302',12,74,180,'BRAKE_GATE');put('U303',21,79,270,'BRAKE_SENSE')
    put('U301',46,45,0,'BRAKE_CONTROL');put('U308',48,53,0,'BRAKE_CONTROL')
    put('U304',46,62,0,'BRAKE_CONTROL');put('U305',47,70,0,'BRAKE_CONTROL')
    put('U306',53,70,0,'BRAKE_CONTROL');put('U307',53,78,0,'BRAKE_CONTROL')
    put('Q302',48,38,0,'BRAKE_CONTROL')
    # Switching supply sits at the bus edge; low-voltage rails leave towards logic.
    put('U401',15,87,0,'BUCK');put('L401',27.25,86,0,'BUCK')
    put('C401',10,85,90,'BUCK');put('C402',6,85,90,'BUCK')
    put('C403',19.75,85.75,90,'BUCK');put('C404',37,86,0,'BUCK');put('C405',37,90,0,'BUCK')
    put('U402',43,91,0,'RAILS');put('U403',50,91,0,'RAILS')
    # TIM1/ADC pins face the bridge. Crystal and reference stay on the analog side.
    put('U501',83,70.5,180,'MCU')
    put('Y501',96.5,70.5,90,'CLOCK');put('U502',96,59.5,0,'REFERENCE')
    put('FB501',93,51,0,'REFERENCE');put('U503',78,85,0,'EEPROM')
    put('U706',75.5,57,180,'PWM_BUFFER')
    put('U703',55,48,0,'INTERLOCK');put('U711',60,48,0,'INTERLOCK');put('U704',65,48,0,'INTERLOCK')
    put('U705',67,55,0,'INTERLOCK');put('U707',56,56,0,'INTERLOCK')
    put('U712',57,62,0,'INTERLOCK');put('U708',68,63,0,'INTERLOCK')
    put('U701',66,71,0,'SUPERVISION');put('U702',60,68,0,'SUPERVISION');put('U710',60,74,0,'SUPERVISION')
    put('U101',104,45,0,'CURRENT_TRIP');put('U102',104,53,0,'CURRENT_TRIP')
    put('U801',104,66,0,'VOLTAGE_SENSE')
    put('U803',94,92,180,'ANALOG_INPUT');put('U804',104,77,0,'TEMPERATURE')
    put('U601',49,95,180,'HALL');put('U602',62,95,180,'ENCODER')
    put('U603',62,86,0,'HALL');put('U604',69,91,0,'ENCODER');put('U802',82,93,0,'CONTROL_INPUT')
    put('U709',103,90,0,'CAN');put('U404',11,95,0,'USB')
    # Connectors leave the perimeter accessible; no cable needs to pass over a hot FET.
    put('J401',3.5,95,270,'USB');put('J103',10,104,0,'CHASSIS')
    put('J501',64,81,0,'DEBUG');put('JP501',73,80,0,'DEBUG')
    put('JP704',53,86,0,'DEBUG');put('J703',17,105,0,'DEBUG')
    put('SW501',47,82,0,'DEBUG');put('SW502',84,83,0,'DEBUG')
    for ref,x in [('J702',36),('J601',49),('J602',62),('J803',76),('J801',89),('J802',101)]:put(ref,x,106,180,'CONNECTORS')
    for ref,y in [('J805',67),('J806',77),('J701',89),('J804',99)]:put(ref,112,y,270,'CONNECTORS')
    # Pull the switching cells toward the motor edge, opening the controller routing band.
    for ref,p in PLACED.items():
        if p['group'].startswith(('PHASE_','GATE_','BYPASS_','CURRENT_')) and p['group']!='CURRENT_TRIP':
            p['x']+=4.5;p['y']-=10
    for ref in ['R211','R231','R251']:
        p=PLACED[ref];p['x']-=4.095;p['y']+=5.7
    for ref in ['U706','U703','U711','U704','U705','U707','U712','U708','U101','U102']:
        PLACED[ref]['y']-=8
    for ref in ['U501','Y501','U502','FB501','U701','U702','U710']:
        PLACED[ref]['y']-=6
    for hs in [54,75.5,97]:
        ls=hs+7
        AUTO_KEEPOUT.extend([(hs-3,8.5,ls+3.2,11.9),
            (ls-2.6,18.8,ls+.75,23.2),(hs-1.9,18.3,hs+.2,22.5)])
    put('R101',8.5,42,270,'DC_INPUT')
    for i,hs in enumerate([97,75.5,54]):
        ls=hs+7;b=210+20*i
        PLACED['R'+str(b+3)]['angle']=270
        put('R'+str(b+7),ls+5.9,11.5,270,'SNUBBER')
        put('C'+str(b+5),ls+5.9,15.5,270,'SNUBBER')
        put('R'+str(811+10*i),ls+8.5,19.5,270,'PHASE_DIVIDER')
    put('R801',43.2,78.5,270,'BUS_DIVIDER')
    for p in PLACED.values():
        if p['group']=='GATE_DRIVER':p['x']-=4;p['y']-=2

def overlap(a,b,gap=.25):
    return a[0]<b[2]+gap and a[2]>b[0]-gap and a[1]<b[3]+gap and a[3]>b[1]-gap

def inside(ref,b):
    # Only connector housings may project beyond the outline; all pads stay inside.
    allow=ref in ['J101','J401']
    margin=-3.5 if allow else .8
    return b[0]>=margin and b[1]>=margin and b[2]<=OUTLINE[2]-margin and b[3]<=OUTLINE[3]-margin

def world_pads(ref,p):
    result=[]
    for pad in PARTS[ref]['pads']:
        if not pad['number']:continue
        x,y=rotate(pad['x'],pad['y'],p['angle'])
        result.append(dict(pad,x=p['x']+x,y=p['y']+y))
    return result

def legalize():
    original=dict(PLACED);PLACED.clear();moves=[]
    order=sorted(original,key=lambda r:(0 if r in ['J101','J102','J401'] or r.startswith('Q2') or original[r]['group'].startswith(('PHASE_','BYPASS_','DC_LINK')) else 1 if r.startswith('J') else 2 if r.startswith('U5') else 3))
    occupied=[]
    for ref in order:
        p=original[ref];best=None
        for radius in range(0,33):
            step=.25
            offsets=[(0,0)] if radius==0 else [(ix*step,iy*step) for ix in range(-radius,radius+1) for iy in range(-radius,radius+1) if max(abs(ix),abs(iy))==radius]
            candidates=[]
            for dx,dy in offsets:
                if ref in ['J101','J102','J401'] and radius:continue
                x,y=p['x']+dx,p['y']+dy;b=box(ref,x,y,p['angle'])
                if not inside(ref,b) or any(overlap(b,v) for v in [*occupied,*RESERVES]):continue
                candidates.append((dx*dx+dy*dy,x,y,b))
            if candidates:
                best=min(candidates);break
        if best is None:raise RuntimeError(('ANCHOR_NO_ROOM',ref,p))
        _,x,y,b=best;PLACED[ref]=dict(p,x=x,y=y);occupied.append(b)
        if (x,y)!=(p['x'],p['y']):moves.append([ref,p['x'],p['y'],x,y])
    return moves

DECAP={
 'C501':('U501','6'),'C502':('U501','24'),'C503':('U501','49'),'C504':('U501','64'),
 'C505':('U501','75'),'C517':('U501','100'),'C506':('U501','100'),
 'C507':('U501','37'),'C508':('U501','37'),'C509':('U502','4'),'C510':('U502','5'),
 'C511':('U501','36'),'C512':('U502','1'),'C516':('U503','8'),
 'C113':('U101','3'),'C114':('U102','3'),'C304':('U302','1'),'C305':('U302','1'),
 'C306':('U303','5'),'C307':('U304','5'),'C309':('U305','6'),'C311':('U307','8'),
 'C313':('U308','4'),'C314':('U308','5'),'C408':('U402','3'),'C409':('U402','6'),
 'C410':('U402','2'),'C411':('U403','6'),'C412':('U403','1'),
 'C601':('U601','1'),'C602':('U601','6'),'C603':('U602','1'),'C604':('U602','6'),
 'C605':('U603','8'),'C606':('U604','8'),'C701':('U701','4'),'C703':('U702','1'),
 'C704':('U709','3'),'C706':('U709','5'),'C711':('U703','5'),'C712':('U704','5'),
 'C713':('U705','8'),'C714':('U706','20'),'C715':('U707','5'),'C716':('U708','5'),
 'C717':('U710','5'),'C718':('JP704','2'),'C719':('U711','5'),'C720':('U712','5'),
 'C840':('U801','4'),'C845':('U802','8'),'C847':('U803','8'),'C848':('U804','8'),
}
PORT_ESD={'D610':('J601','3'),'D611':('J601','4'),'D612':('J601','5'),
 'D613':('J602','3'),'D614':('J602','4'),'D615':('J602','5'),'D703':('J701','2'),
 'D704':('J703','1'),'D852':('J801','3'),'D857':('J802','3'),'D865':('J803','3'),
 'D868':('J804','2'),'D871':('J804','3'),'D888':('J805','1'),'D891':('J806','1')}
HOSTS={
 '01_dc_link':['J103','J101'],'12_gate_driver':['U201'],'02_bridge':['U202','U203','U204'],
 '04_power_usb':['U401','U402','U403'],'13_usb_status':['J401','U501'],
 '05_mcu':['U501','U502','U503'],'03_regen':['U301','U302','U303','U308'],
 '15_regen_safety':['U304','U305','U306','U307'],'06_sensors':['U601','U602','U603','U604'],
 '16_supervisor':['U701','U702','U710'],'09_safety':['U703','U704','U705','U706','U707','U708','U711','U712'],
 '07_io_can':['U709'],'11_current_protection':['U101','U102'],
 '10_voltage_sensing':['U801'],'08_analog_inputs':['U802','U803'],'14_temperature':['U804','U501']}
RAILS={'GND','VBUS','3V3','3V3_A','5V_BUS','5V_SYS','USB_5V','VREF_2V5','VBIAS_1V25','5V_HALL','5V_ENCODER'}

def explicit_target(ref):
    testpoints={
        'TP101':('J101','2'),'TP102':('J101','1'),
        'TP103':('Q201','1'),'TP104':('Q203','1'),'TP105':('Q205','1'),
        'TP220':('Q201','4'),'TP221':('Q202','4'),'TP222':('Q202','1'),
        'TP240':('Q203','4'),'TP241':('Q204','4'),'TP242':('Q204','1'),
        'TP260':('Q205','4'),'TP261':('Q206','4'),'TP262':('Q206','1'),
        'TP210':('U501','21'),'TP211':('U501','29'),'TP212':('U501','32'),
        'TP301':('U303','1'),'TP401':('C404','1'),'TP402':('U402','2'),
        'TP403':('U403','1'),'TP404':('U403','3'),'TP501':('U502','5'),
        'TP502':('U502','1'),'TP503':('U501','37'),
    }
    if ref in ['TP504','TP505','TP506']:
        net=next(p['net'] for p in PARTS[ref]['pads'] if p['number'])
        pin=next(p['number'] for p in PARTS['U501']['pads'] if p['number'] and p['net']==net)
        testpoints[ref]=('U501',pin)
    if ref in testpoints:
        host,pin=testpoints[ref];pad=next(p for p in world_pads(host,PLACED[host]) if p['number']==pin)
        return host,(pad['x'],pad['y']),False
    pair=DECAP.get(ref) or PORT_ESD.get(ref)
    if pair:
        host,pin=pair
        pad=next(p for p in world_pads(host,PLACED[host]) if p['number']==pin)
        return host,(pad['x'],pad['y']),True
    overrides={
       'C513':('U501','12'),'C514':('U501','13'),'R502':('U501','13'),
       'R413':('U501','73'),'R414':('U501','72'),
       'R215':('U501','21'),'C213':('U501','21'),'R235':('U501','29'),'C233':('U501','29'),
       'R255':('U501','32'),'C253':('U501','32'),
       'R216':('U501','33'),'C214':('U501','33'),'R236':('U501','31'),'C234':('U501','31'),
       'R256':('U501','34'),'C254':('U501','34'),
    }
    if ref in overrides:
        host,pin=overrides[ref];pad=next(p for p in world_pads(host,PLACED[host]) if p['number']==pin)
        return host,(pad['x'],pad['y']),True
    if ref=='TH801':return 'Q204',(80.5,17),True
    if ref=='TH802':return 'U501',(89,83),True
    if ref in ['R102','R103','C109']:return 'J103',(11,101),True
    if ref in ['D511','D512','D513','R511','R512','R513']:return 'J401',(17,101),False
    if ref in ['R201','R202','R203','R204','R205']:
        p=PLACED['U201'];return 'U201',(p['x'],p['y']),False
    if ref in ['R417','R418']:return 'U403',(50,91),True
    nets={p['net'] for p in PARTS[ref]['pads'] if p['number'] and p['net'].split('/')[-1] not in RAILS}
    hosts=HOSTS[BOM[ref]['sheet']]
    score=[]
    for host in hosts:
        hp=world_pads(host,PLACED[host]);matching=[p for p in hp if p['net'] in nets]
        if matching:score.append((len(matching),host,matching))
    if score:
        _,host,matching=max(score,key=lambda v:v[0])
        return host,(sum(p['x'] for p in matching)/len(matching),sum(p['y'] for p in matching)/len(matching)),False
    host=hosts[0];p=PLACED[host]
    return host,(p['x'],p['y']),False

def populate():
    import numpy as np
    occupied=[box(r,p['x'],p['y'],p['angle']) for r,p in PLACED.items()]+RESERVES
    remaining=set(PARTS)-set(PLACED)
    order=sorted(remaining,key=lambda r:(0 if r in DECAP or r.startswith('TH') else 1 if r in PORT_ESD or r.startswith('TP2') or r in ['TP103','TP104','TP105'] else 2 if r.startswith(('C51','R413','R414')) else 4 if r.startswith('TP') else 3,
        -(PARTS[r]['courtyard'][2]-PARTS[r]['courtyard'][0])*(PARTS[r]['courtyard'][3]-PARTS[r]['courtyard'][1]),r))
    distances=[]
    for index,ref in enumerate(order):
        if index%40==0:print('Supporting placement: '+str(index)+'/'+str(len(order)),file=sys.stderr)
        host,(tx,ty),critical=explicit_target(ref)
        best=None
        others={}
        own=[p for p in PARTS[ref]['pads'] if p['number']]
        ownnets={p['net'] for p in own if p['net'].split('/')[-1] not in RAILS}
        for r,p in PLACED.items():
            for pad in world_pads(r,p):
                if pad['net'] in ownnets:others.setdefault(pad['net'],[]).append((pad['x'],pad['y']))
        for radius in ([6,9,12,16] if critical else [10,15,22,32,45]):
            xs=np.arange(max(1,math.floor((tx-radius)*2)/2),min(115,tx+radius)+.01,.5)
            ys=np.arange(max(1,math.floor((ty-radius)*2)/2),min(111,ty+radius)+.01,.5)
            xx,yy=np.meshgrid(xs,ys);xx=xx.ravel();yy=yy.ravel()
            for angle in [0,90,180,270]:
                bb=box(ref,0,0,angle)
                mask=(xx+bb[0]>=.8)&(yy+bb[1]>=.8)&(xx+bb[2]<=115.2)&(yy+bb[3]<=111.2)
                exclusion=occupied+AUTO_KEEPOUT
                if not critical and not ref.startswith('TP'):
                    m=PLACED['U501'];mb=box('U501',m['x'],m['y'],m['angle'])
                    exclusion=exclusion+[(mb[0]-1.5,mb[1]-1.5,mb[2]+1.5,mb[3]+1.5)]
                for b in exclusion:mask&=~((xx+bb[0]<b[2]+.3)&(xx+bb[2]>b[0]-.3)&(yy+bb[1]<b[3]+.3)&(yy+bb[3]>b[1]-.3))
                if not mask.any():continue
                x=xx[mask];y=yy[mask]
                cost=(6 if critical else 2.5)*(abs(x-tx)+abs(y-ty))
                for pad in own:
                    matches=others.get(pad['net'])
                    if not matches:continue
                    ox,oy=rotate(pad['x'],pad['y'],angle)
                    distance=np.min(np.array([abs(x+ox-px)+abs(y+oy-py) for px,py in matches]),axis=0)
                    cost+=distance*(1.5 if len(matches)<5 else .6)
                if critical:
                    pad=next((p for p in own if p['net'].split('/')[-1]!='GND'),own[0])
                    ox,oy=rotate(pad['x'],pad['y'],angle);cost+=4*(abs(x+ox-tx)+abs(y+oy-ty))
                k=int(np.argmin(cost));candidate=(float(cost[k]),float(x[k]),float(y[k]),angle)
                if best is None or candidate<best:best=candidate
            if best is not None:break
        if best is None:raise RuntimeError(('NO_ROOM',ref,host,tx,ty))
        _,x,y,angle=best
        PLACED[ref]={'x':x,'y':y,'angle':angle,'side':'F.Cu','group':BOM[ref]['sheet'],'fixed':False,'host':host}
        occupied.append(box(ref,x,y,angle))
        distances.append((ref,host,round(math.hypot(x-tx,y-ty),2),critical))
    return distances

def export():
    from capture import patch
    # Local coordinates remain easy to edit; the board uses a positive drawing origin.
    plan={'outline':[OUTLINE[0]+ORIGIN[0],OUTLINE[1]+ORIGIN[1],OUTLINE[2]+ORIGIN[0],OUTLINE[3]+ORIGIN[1]],
          'origin':ORIGIN,'units':'mm','components':{}}
    for ref,p in PLACED.items():
        q=dict(p,x=round(p['x']+ORIGIN[0],4),y=round(p['y']+ORIGIN[1],4))
        b=box(ref,p['x'],p['y'],p['angle'])
        q['ref_x']=round((b[0]+b[2])/2+ORIGIN[0],4);q['ref_y']=round(b[1]-.65+ORIGIN[1],4)
        plan['components'][ref]=q
    print('*** Begin Patch\n'+patch('engineering/placement.json',json.dumps(plan,indent=2)+'\n')+'*** End Patch')

if __name__=='__main__':
    import sys
    fixed()
    changes=legalize()
    if '--anchors' in sys.argv:print(json.dumps({'count':len(PLACED),'legalized':changes,'placed':PLACED},indent=2))
    else:
        distances=populate()
        if '--patch' in sys.argv:export()
        else:print(json.dumps({'placed':len(PLACED),'legalized':changes,'largest_distances':sorted(distances,key=lambda v:-v[2])[:25]},indent=2))
