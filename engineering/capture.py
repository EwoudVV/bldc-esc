import copy
import csv
import difflib
import io
import json
import math
import re
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

from kicad_sexpr import Atom as A, child, dump, parse, pins, symbol, tag, walk

ROOT = Path(__file__).resolve().parent.parent
ROOT_ID = '10000000-0000-4000-8000-000000000000'
SHEETS = ['01_dc_link', '02_bridge', '03_regen', '04_power_usb', '05_mcu', '06_sensors', '07_io_can', '08_analog_inputs', '09_safety']
FP_ROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
parts = []
custom = {}
notes = defaultdict(list)


def uid(value):
    return str(uuid.uuid5(uuid.UUID(ROOT_ID), value))


def effect(size=1.0, justify=None, hide=False):
    value = tag('effects', tag('font', tag('size', size, size)))
    if justify:
        value.append(tag('justify', *[A(v) for v in justify.split()]))
    if hide:
        value.append(tag('hide', A('yes')))
    return value


def box_symbol(name, left, right, width=30.48, spacing=2.54):
    height = (max(len(left), len(right)) + 1) * spacing
    node = tag('symbol', name,
        tag('pin_names', tag('offset', 0.508)),
        tag('exclude_from_sim', A('no')), tag('in_bom', A('yes')), tag('on_board', A('yes')),
        tag('property', 'Reference', 'U', tag('at', 0, height / 2 + 5.08, 0), effect(1.27)),
        tag('property', 'Value', name, tag('at', 0, height / 2 + 2.54, 0), effect(1.0)),
        tag('property', 'Footprint', '', tag('at', 0, 0, 0), effect(hide=True)),
        tag('property', 'Datasheet', '', tag('at', 0, 0, 0), effect(hide=True)))
    graphics = tag('symbol', name + '_0_1', tag('rectangle', tag('start', -width / 2, height / 2),
        tag('end', width / 2, -height / 2), tag('stroke', tag('width', 0.254), tag('type', A('default'))), tag('fill', tag('type', A('background')))))
    pin_section = tag('symbol', name + '_1_1')
    for side, entries in ((-1, left), (1, right)):
        for index, (number, pin_name, pin_type) in enumerate(entries):
            x = side * (width / 2 + 3.81)
            y = height / 2 - (index + 1) * spacing
            pin_section.append(tag('pin', A(pin_type), A('line'), tag('at', x, y, 0 if side < 0 else 180),
                tag('length', 3.81), tag('name', pin_name, effect(1.0)), tag('number', str(number), effect(0.9))))
    node.extend([graphics, pin_section, tag('embedded_fonts', A('no'))])
    custom[name] = node
    return 'bldc-esc:' + name


def define_symbols():
    drv = [(3,'VM','power_in'),(4,'VDRAIN','input'),(24,'VREF','power_in'),(31,'ENABLE','input'),
           (32,'INHA','input'),(33,'INLA','input'),(34,'INHB','input'),(35,'INLB','input'),
           (36,'INHC','input'),(37,'INLC','input'),(30,'nSCS','input'),(29,'SCLK','input'),
           (28,'SDI','input'),(27,'SDO','open_collector'),(26,'nFAULT','open_collector'),
           (25,'AGND','power_in'),(39,'GND','power_in'),(41,'EP','passive')]
    out = [(1,'CPL','passive'),(2,'CPH','passive'),(5,'VCP','power_out'),(40,'VGLS','power_out'),
           (38,'DVDD','power_out'),(6,'GHA','output'),(7,'SHA','input'),(8,'GLA','output'),
           (9,'SPA','input'),(10,'SNA','input'),(15,'GHB','output'),(14,'SHB','input'),
           (13,'GLB','output'),(12,'SPB','input'),(11,'SNB','input'),(16,'GHC','output'),
           (17,'SHC','input'),(18,'GLC','output'),(19,'SPC','input'),(20,'SNC','input'),
           (23,'SOA','output'),(22,'SOB','output'),(21,'SOC','output')]
    box_symbol('DRV8353S', drv, out, 35.56)
    box_symbol('TLV9024', [(3,'V+','power_in'),(5,'IN1+','input'),(4,'IN1-','input'),
        (7,'IN2+','input'),(6,'IN2-','input'),(9,'IN3+','input'),(8,'IN3-','input'),
        (11,'IN4+','input'),(10,'IN4-','input')], [(2,'OUT1','open_collector'),(1,'OUT2','open_collector'),
        (14,'OUT3','open_collector'),(13,'OUT4','open_collector'),(12,'V-','power_in')])
    box_symbol('SN74LVC1G74', [(8,'VCC','power_in'),(2,'D','input'),(1,'CLK','input'),
        (6,'nCLR','input'),(7,'nPRE','input')], [(5,'Q','output'),(3,'nQ','output'),(4,'GND','power_in')],20.32)
    box_symbol('SN74LVC244A', [(20,'VCC','power_in'),(1,'nOE1','input'),(19,'nOE2','input'),
        (2,'A1','input'),(4,'A2','input'),(6,'A3','input'),(8,'A4','input'),
        (11,'A5','input'),(13,'A6','input'),(15,'A7','input'),(17,'A8','input')],
        [(18,'Y1','tri_state'),(16,'Y2','tri_state'),(14,'Y3','tri_state'),(12,'Y4','tri_state'),
         (9,'Y5','tri_state'),(7,'Y6','tri_state'),(5,'Y7','tri_state'),(3,'Y8','tri_state'),(10,'GND','power_in')])
    box_symbol('TPS3431', [(1,'VDD','power_in'),(2,'CWD','input'),(3,'EN','input'),(5,'SET1','input'),(6,'WDI','input')],
        [(7,'nWDO','open_collector'),(8,'ENOUT','open_collector'),(4,'GND','power_in'),(9,'EP','passive')],20.32)
    box_symbol('TPS3808Gxx', [(6,'VDD','power_in'),(5,'SENSE','input'),(3,'nMR','input'),(4,'CT','passive')],
        [(1,'nRESET','open_collector'),(2,'GND','power_in')],20.32)
    box_symbol('TLV3011B', [(6,'V+','power_in'),(3,'IN+','input'),(4,'IN-','input')],
        [(1,'OUT','open_collector'),(5,'REF','output'),(2,'V-','power_in')],20.32)
    box_symbol('TPS2553_1', [(1,'IN','power_in'),(3,'EN','input'),(5,'ILIM','passive')],
        [(6,'OUT','power_out'),(4,'nFAULT','open_collector'),(2,'GND','power_in')],20.32)
    box_symbol('TCAN3403', [(3,'VCC','power_in'),(5,'VIO','power_in'),(1,'TXD','input'),(8,'STB','input')],
        [(7,'CANH','bidirectional'),(6,'CANL','bidirectional'),(4,'RXD','output'),(2,'GND','power_in')],20.32)
    box_symbol('SN74LVC3G17', [(8,'VCC','power_in'),(1,'A1','input'),(3,'A2','input'),(6,'A3','input')],
        [(7,'Y1','output'),(5,'Y2','output'),(2,'Y3','output'),(4,'GND','power_in')],20.32)
    box_symbol('M24C64_R', [(8,'VCC','power_in'),(1,'E0','input'),(2,'E1','input'),(3,'E2','input'),(7,'WC','input')],
        [(6,'SCL','input'),(5,'SDA','bidirectional'),(4,'VSS','power_in')],20.32)
    box_symbol('TLV9064',[(4,'V+','power_in'),(3,'IN1+','input'),(2,'IN1-','input'),(5,'IN2+','input'),(6,'IN2-','input'),
        (10,'IN3+','input'),(9,'IN3-','input'),(12,'IN4+','input'),(13,'IN4-','input')],
        [(1,'OUT1','output'),(7,'OUT2','output'),(8,'OUT3','output'),(14,'OUT4','output'),(11,'V-','power_in')])
    box_symbol('TLV3201',[(5,'V+','power_in'),(3,'IN+','input'),(4,'IN-','input')],[(1,'OUT','output'),(2,'V-','power_in')],20.32)
    box_symbol('PESD2CANFD24V_T',[(1,'CANH','passive'),(2,'CANL','passive')],[(3,'GND','passive')],15.24)
    fet = symbol('Transistor_FET:Q_NMOS_GDS')
    old_name = fet[1]
    fet[1] = 'ISC011N06LM5'
    for section in fet:
        if isinstance(section,list) and section[0]=='symbol':
            section[1] = 'ISC011N06LM5' + section[1][len(old_name):]
            extra=[]
            for pin in section:
                if isinstance(pin,list) and pin[0]=='pin':
                    number=child(pin,'number')
                    old=str(number[1])
                    number[1]={'1':'4','2':'5','3':'1'}[old]
                    if old=='3':
                        for n in ['2','3']:
                            duplicate=copy.deepcopy(pin)
                            child(duplicate,'number')[1]=n
                            duplicate.append(tag('hide',A('yes')))
                            extra.append(duplicate)
            section.extend(extra)
    custom['ISC011N06LM5']=fet


def part(sheet, ref, lib_id, value, x, y, nets, footprint='', mpn='', manufacturer='', angle=0, dnp=False):
    node=copy.deepcopy(custom[lib_id.split(':')[1]]) if lib_id.startswith('bldc-esc:') else symbol(lib_id)
    if not footprint:
        footprint=next((v[2] for v in node if isinstance(v,list) and v[0]=='property' and v[1]=='Footprint'),'')
    numbers={str(child(p,'number')[1]) for p in pins(node)}
    nets={str(k):v for k,v in nets.items()}
    if set(nets)!=numbers:
        raise ValueError((ref,lib_id,sorted(numbers-set(nets)),sorted(set(nets)-numbers)))
    urls={'DRV8353S':'https://www.ti.com/lit/ds/symlink/drv8353.pdf',
        'TLV9024':'https://www.ti.com/lit/ds/symlink/tlv9024.pdf',
        'SN74LVC1G74':'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf',
        'SN74LVC244A':'https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf',
        'TPS3431':'https://www.ti.com/lit/ds/symlink/tps3431.pdf',
        'TPS3808Gxx':'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
        'TLV3011B':'https://www.ti.com/lit/ds/symlink/tlv3012.pdf',
        'TPS2553_1':'https://www.ti.com/lit/ds/symlink/tps2553.pdf',
        'TCAN3403':'https://www.ti.com/lit/ds/symlink/tcan3403-q1.pdf',
        'SN74LVC3G17':'https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf',
        'M24C64_R':'https://www.st.com/en/memories/m24c64-r.html',
        'TLV9064':'https://www.ti.com/lit/ds/symlink/tlv9064.pdf',
        'TLV9062':'https://www.ti.com/lit/ds/symlink/tlv9064.pdf',
        'TLV3201':'https://www.ti.com/lit/ds/symlink/tlv3201.pdf',
        'PESD2CANFD24V_T':'https://assets.nexperia.com/documents/data-sheet/PESD2CANFD24V-T.pdf',
        'ISC011N06LM5':'https://www.infineon.com/part/ISC011N06LM5',
        'USB_C_16P':'https://gct.co/connector/usb4105'}
    name=lib_id.split(':')[1]
    if (mpn or value).startswith('BAV199'):urls[name]='https://assets.nexperia.com/documents/data-sheet/BAV199.pdf'
    if value=='STPS5H100AF':urls[name]='https://www.st.com/resource/en/datasheet/stps5h100af.pdf'
    if mpn.startswith('ABM3-'):urls[name]='https://abracon.com/Resonators/ABM3.pdf'
    if mpn=='EEUFC1J220':urls[name]='https://industrial.panasonic.com/sa/products/pt/aluminum-cap-lead/models/EEUFC1J220'
    if mpn=='MSAST32MSB7226KPNB25':
        urls[name]='https://ds.yuden.co.jp/TYCOMPAS/ap/detail?pn=MSAST32MSB7226KPNB25&u=M'
        manufacturer='Taiyo Yuden'
    if name in urls and lib_id.startswith('bldc-esc:'):
        for prop in node:
            if isinstance(prop,list) and prop[0]=='property' and prop[1]=='Datasheet':prop[2]=urls[name]
        if name in custom:custom[name]=copy.deepcopy(node)
    p={'sheet':sheet,'ref':ref,'lib_id':lib_id,'node':node,'value':value,'x':x,'y':y,'nets':nets,
       'footprint':footprint,'mpn':mpn or value,'manufacturer':manufacturer,'angle':angle,'dnp':dnp,
       'datasheet':urls.get(name,next((v[2] for v in node if isinstance(v,list) and v[0]=='property' and v[1]=='Datasheet'),''))}
    parts.append(p)
    return p


def R(sheet, ref, value, x, y, n1, n2, package='0603', precision=False, dnp=False, angle=0, mpn=''):
    code=value.upper().replace('OHM','R')
    code=re.sub(r'(\d+)\.(\d+)([KMR]?)',lambda m:m[1]+(m[3] or 'R')+m[2],code)
    if not any(k in code for k in ('K','M','R')): code+='R'
    return part(sheet,ref,'Device:R',value+(' 0.1%' if precision else ''),x,y,{1:n1,2:n2},
        'Resistor_SMD:R_'+package+'_'+{'0603':'1608','0805':'2012','1206':'3216','2512':'6332'}[package]+'Metric',
        mpn or (('RT' if precision else 'RC')+package+('BRD07' if precision else 'JR-07' if value=='0' else 'FR-07')+code+'L'),'Yageo',angle,dnp)


def C(sheet, ref, value, x, y, n1, n2='GND', package='0603', mpn='', dnp=False):
    return part(sheet,ref,'Device:C',value,x,y,{1:n1,2:n2},
        'Capacitor_SMD:C_'+package+'_'+{'0603':'1608','0805':'2012','1206':'3216','1210':'3225'}[package]+'Metric',
        mpn or ('GRM188R71H104KA93D' if value=='100n 50V' else ''),'Murata' if not mpn else '',dnp=dnp)


def D(sheet, ref, value, x, y, anode, cathode, footprint='Diode_SMD:D_SOD-123', lib='Device:D', dnp=False):
    maker='Nexperia' if value.startswith(('PESD','BAT','PMEG')) else 'STMicroelectronics' if value.startswith('STPS') else ''
    return part(sheet,ref,lib,value,x,y,{1:cathode,2:anode},footprint,value,maker,angle=90,dnp=dnp)


def TP(sheet, ref, net, x, y):
    return part(sheet,ref,'Connector:TestPoint',net,x,y,{1:net},'TestPoint:TestPoint_Pad_D1.5mm', 'TESTPOINT')


def CON(sheet,ref,value,x,y,nets,footprint=None,mpn=None):
    n=len(nets)
    fp=footprint or ('Connector_JST:JST_GH_BM%02dB-GHS-TBT_1x%02d-1MP_P1.25mm_Vertical'%(n,n))
    return part(sheet,ref,'Connector_Generic:Conn_01x%02d'%n,value,x,y,dict(enumerate(nets,1)),fp,mpn or ('BM%02dB-GHS-TBT(LF)(SN)'%n),'JST' if footprint is None else '')


def label_node(net, x,y,direction,global_net):
    if global_net:
        angle=180 if direction=='left' else 0
        return tag('global_label',net,tag('shape',A('bidirectional')),tag('at',round(x,4),round(y,4),angle),
            effect(0.95,'right' if angle==180 else 'left'),tag('uuid',uid('label:'+net+':'+str(x)+':'+str(y)+':'+str(global_net))))
    return tag('label',net,tag('at',round(x,4),round(y,4),0),effect(0.95,'right bottom' if direction=='left' else 'left bottom'),
        tag('uuid',uid('label:'+net+':'+str(x)+':'+str(y))))


def pin_position(part, number):
    pin=next(p for p in pins(part['node']) if str(child(p,'number')[1])==str(number))
    at=child(pin,'at');lx,ly=float(at[1]),float(at[2]);theta=math.radians(part['angle'])
    return (round(part['x']+lx*math.cos(theta)-ly*math.sin(theta),4),
            round(part['y']-lx*math.sin(theta)-ly*math.cos(theta),4))


def wire_node(start,end,key):
    return tag('wire',tag('pts',tag('xy',*start),tag('xy',*end)),tag('stroke',tag('width',0),tag('type',A('default'))),tag('uuid',uid(key)))


def schematic(sheet):
    index=SHEETS.index(sheet)+1
    groups=defaultdict(set)
    for p in parts:
        for net in p['nets'].values():
            if net: groups[net].add(p['sheet'])
    subset=[p for p in parts if p['sheet']==sheet]
    library={}
    for p in subset:
        node=copy.deepcopy(p['node']);node[1]=p['lib_id'];library[p['lib_id']]=node
    out=tag('kicad_sch',tag('version',20260306),tag('generator','bldc-esc'),
        tag('uuid','20000000-0000-4000-8000-%012d'%index),tag('paper','A4' if sheet=='07_io_can' else 'A1' if sheet in ('08_analog_inputs','09_safety') else 'A2'),
        tag('title_block',tag('title',sheet),tag('rev','v1-draft')),tag('lib_symbols',*library.values()))
    out.append(tag('text',sheet+' / v1',tag('at',25.4,20.32,0),effect(2.0,'left'),tag('uuid',uid(sheet+':heading'))))
    for x,y,text in notes[sheet]:
        out.append(tag('text',text,tag('at',x,y,0),effect(1.15,'left'),tag('uuid',uid(sheet+':'+text))))
    for p in subset:
        x,y=p['x'],p['y']; theta=math.radians(p['angle']); node=p['node']
        inst=tag('symbol',tag('lib_id',p['lib_id']),tag('at',x,y,p['angle']),tag('unit',1),
            tag('exclude_from_sim',A('no')),tag('in_bom',A('no') if p['ref'].startswith(('#','TP')) else A('yes')),
            tag('on_board',A('no') if p['ref'].startswith('#') else A('yes')),tag('dnp',A('yes' if p['dnp'] else 'no')),
            tag('uuid',uid(p['ref'])))
        if p['ref'].startswith('TP'):inst.append(tag('in_pos_files',A('no')))
        entries=pins(node)
        pts=[]
        for pin in entries:
            at=child(pin,'at');lx,ly=float(at[1]),float(at[2])
            px=x+lx*math.cos(theta)-ly*math.sin(theta)
            py=y-lx*math.sin(theta)-ly*math.cos(theta)
            pts.append((px,py))
        if len(entries)<=4:
            rx,ry=x+4.2,y-2
        else:
            rx,ry=x,min(z[1] for z in pts)-13.97
        if p['lib_id']=='Device:R_Shunt':rx,ry=x-21,y-2
        if p['lib_id']=='Diode:BAT54S' or (p['lib_id'].startswith('bldc-esc:') and len(entries)<=4):
            rx,ry=x,min(z[1] for z in pts)-13.97
        if p['lib_id']=='Transistor_FET:2N7002':rx,ry=x+8.89,y-3.81
        if p['angle']==90 and len(entries)<=4:rx,ry=x-3.81,y+5.08
        for key,value,px,py,hidden in [('Reference',p['ref'],rx,ry,False),('Value',p['value'],rx,ry+2.5,False),
            ('Footprint',p['footprint'],x,y,True),('Datasheet',{'Reference_Voltage:REF2030':'https://www.ti.com/lit/gpn/REF20','Amplifier_Current:INA241A2xDGK':'https://www.ti.com/lit/ds/symlink/ina241a.pdf','Regulator_Switching:LM5164DDA':'https://www.ti.com/lit/ds/symlink/lm5164.pdf'}.get(p['lib_id'],next((n[2] for n in node if isinstance(n,list) and n[0]=='property' and n[1]=='Datasheet'),'')),x,y,True),
            ('MPN',p['mpn'],x,y,True),('Manufacturer',p['manufacturer'],x,y,True)]:
            prop=tag('property',key,value,tag('at',round(px,4),round(py,4),p['angle']),effect(1.0 if key=='Value' else 1.15,'left' if len(entries)<=4 else None))
            if hidden:prop.append(tag('hide',A('yes')))
            if p['ref'].startswith('#') and key in ('Reference','Value'):prop.append(tag('hide',A('yes')))
            inst.append(prop)
        inst.append(tag('instances',tag('project','bldc-esc',tag('path','/'+ROOT_ID+'/10000000-0000-4000-8000-%012d'%index,
            tag('reference',p['ref']),tag('unit',1)))))
        out.append(inst)
        seen={}
        label_sites=[]
        for pin in entries:
            number=str(child(pin,'number')[1]);net=p['nets'][number]
            at=child(pin,'at');lx,ly=float(at[1]),float(at[2]);a=math.radians(float(at[3])+p['angle'])
            px=round(x+lx*math.cos(theta)-ly*math.sin(theta),4)
            py=round(y-lx*math.sin(theta)-ly*math.cos(theta),4)
            if (px,py) in seen:
                if seen[(px,py)]!=net:raise ValueError(('STACKED_PIN_NET',p['ref'],number))
                continue
            seen[(px,py)]=net
            if net is None:
                out.append(tag('no_connect',tag('at',px,py),tag('uuid',uid(p['ref']+':NC:'+number))))
                continue
            dx=-math.cos(a);dy=math.sin(a)
            ex=round(px+dx*5.08,4);ey=round(py+dy*5.08,4)
            out.append(tag('wire',tag('pts',tag('xy',px,py),tag('xy',ex,ey)),tag('stroke',tag('width',0),tag('type',A('default'))),tag('uuid',uid(p['ref']+':W:'+number))))
            direction='left' if dx < -0.5 or (abs(dy)>0.5 and net=='GND') else 'right'
            label_sites.append((net,ex,ey,direction,number,abs(dy)>0.5))
        grouped=defaultdict(list)
        for item in label_sites:
            key=(item[0],item[2]) if item[5] else (item[0],item[4])
            grouped[key].append(item)
        for items in grouped.values():
            first=min(items,key=lambda q:q[1]);last=max(items,key=lambda q:q[1])
            if len(items)>1 and not any(z[0]!=first[0] and z[2]==first[2] and first[1]<=z[1]<=last[1] for z in label_sites):
                out.append(wire_node((first[1],first[2]),(last[1],last[2]),p['ref']+':bus:'+first[0]))
                for item in items:
                    out.append(tag('junction',tag('at',item[1],item[2]),tag('diameter',0),tag('color',0,0,0,0),tag('uuid',uid(p['ref']+':J:'+item[4]))))
                chosen=first if first[3]=='left' else last
                labels=[chosen]
            else:labels=items
            for net,ex,ey,direction,number,_ in labels:
                label=label_node(net,ex,ey,direction,len(groups[net])>1)
                child(label,'uuid')[1]=uid(p['ref']+':L:'+number)
                out.append(label)
    if sheet=='02_bridge':
        byref={p['ref']:p for p in subset}
        for i in range(3):
            hi=byref['Q'+str(201+2*i)];lo=byref['Q'+str(202+2*i)]
            shunt=byref['R'+str(214+20*i)]
            start,end=pin_position(hi,1),pin_position(lo,5)
            out.append(wire_node(start,end,'phase-wire:'+str(i)))
            start,end=pin_position(lo,1),pin_position(shunt,1)
            bend=(start[0],end[1]-5.08);bend2=(end[0],end[1]-5.08)
            for j,(a,b) in enumerate(zip([start,bend,bend2],[bend,bend2,end])):
                if a!=b:out.append(wire_node(a,b,'source-wire:'+str(i)+':'+str(j)))
            for j,fet in enumerate((hi,lo)):
                gate=byref['R'+str(210+20*i+2*j)]
                out.append(wire_node(pin_position(gate,2),pin_position(fet,4),'gate-wire:'+str(i)+':'+str(j)))
    out.append(tag('embedded_fonts',A('no')))
    return dump(out)+'\n'


def footprint(name,pads,bounds):
    x,y=bounds
    out=tag('footprint',name,tag('version',20260206),tag('generator','bldc-esc'),tag('layer','F.Cu'),tag('attr',A('smd')),
        tag('property','Reference','REF**',tag('at',0,-y-1.5,0),tag('layer','F.SilkS'),effect()),
        tag('property','Value',name,tag('at',0,y+1.5,0),tag('layer','F.Fab'),effect()))
    for layer,extra,width in [('F.Fab',0,0.1),('F.CrtYd',0.25,0.05)]:
        out.append(tag('fp_rect',tag('start',-x-extra,-y-extra),tag('end',x+extra,y+extra),tag('stroke',tag('width',width),tag('type',A('default'))),tag('fill',A('none')),tag('layer',layer)))
    for number,px,py,sx,sy,kind in pads:
        layers=['F.Cu','F.Paste','F.Mask'] if kind=='smd' else ['F.Paste']
        out.append(tag('pad',str(number),A('smd'),A('rect'),tag('at',px,py),tag('size',sx,sy),tag('layers',*layers)))
    return out


def footprints():
    output={}
    usb=parse((FP_ROOT/'Connector_USB.pretty/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod').read_text())
    usb[1]='USB4105_PCBWay'
    for node in usb:
        if isinstance(node,list) and node and node[0]=='pad' and node[1] in ('A1','A12','B1','B12'):
            child(node,'roundrect_rratio')[1]=0.5
    usb.append(tag('property','Source','KiCad10:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',tag('at',0,0,0),tag('layer','F.Fab'),tag('hide',A('yes')),effect()))
    usb.append(tag('property','Modification','GND pad corner radius 0.30mm; holes and pad extents unchanged',tag('at',0,0,0),tag('layer','F.Fab'),tag('hide',A('yes')),effect()))
    output['bldc-esc.pretty/USB4105_PCBWay.kicad_mod']=dump(usb)+'\n'
    pads=[]
    for i in range(10):
        pads.extend([(i+1,-2.9,-2.25+0.5*i,0.6,0.22,'smd'),(i+11,-2.25+0.5*i,2.9,0.22,0.6,'smd'),
            (i+21,2.9,2.25-0.5*i,0.6,0.22,'smd'),(i+31,2.25-0.5*i,-2.9,0.22,0.6,'smd')])
    n=footprint('DRV8353_RTA0040B',pads,(3.25,3.25))
    n.append(tag('pad','41',A('smd'),A('rect'),tag('at',0,0),tag('size',4.15,4.15),tag('layers','F.Cu','F.Mask')))
    for px in (-1.37,0,1.37):
        for py in (-1.37,0,1.37):n.append(tag('pad','',A('smd'),A('rect'),tag('at',px,py),tag('size',1.17,1.17),tag('layers','F.Paste')))
    n.append(tag('fp_circle',tag('center',-3.3,-2.8),tag('end',-3.12,-2.8),tag('stroke',tag('width',0.12),tag('type',A('default'))),tag('fill',A('none')),tag('layer','F.SilkS')))
    output['bldc-esc.pretty/DRV8353_RTA0040B.kicad_mod']=dump(n)+'\n'
    n=footprint('CSS4J_4026',[(1,-4.025,0.85,2.55,5.6,'smd'),(2,-4.025,-3.25,2.55,0.8,'smd'),
        (3,4.025,-3.25,2.55,0.8,'smd'),(4,4.025,0.85,2.55,5.6,'smd')],(5.55,3.9))
    output['bldc-esc.pretty/CSS4J_4026.kicad_mod']=dump(n)+'\n'
    n=tag('footprint','MT60_Pigtail_12AWG',tag('version',20260206),tag('generator','bldc-esc'),tag('layer','F.Cu'),tag('attr',A('through_hole')),
        tag('property','Reference','REF**',tag('at',10,-5,0),tag('layer','F.SilkS'),effect()),
        tag('property','Value','MT60_Pigtail_12AWG',tag('at',10,5,0),tag('layer','F.Fab'),effect()))
    for i in range(3):n.append(tag('pad',str(i+1),A('thru_hole'),A('circle'),tag('at',i*10,0),tag('size',6,6),tag('drill',3),tag('layers','*.Cu','*.Mask')))
    n.append(tag('fp_rect',tag('start',-3.5,-3.5),tag('end',23.5,3.5),tag('stroke',tag('width',0.05),tag('type',A('default'))),tag('fill',A('none')),tag('layer','F.CrtYd')))
    output['bldc-esc.pretty/MT60_Pigtail_12AWG.kicad_mod']=dump(n)+'\n'
    return output


def patch(path,content):
    target=ROOT/path
    if target.exists():
        old=target.read_text()
        if old==content:return ''
        diff=list(difflib.unified_diff(old.splitlines(),content.splitlines(),n=max(len(old.splitlines()),len(content.splitlines()))+1))[2:]
        diff=['@@' if line.startswith('@@') else line for line in diff]
        return '*** Update File: '+str(target)+'\n'+'\n'.join(diff)+'\n'
    return '*** Add File: '+str(target)+'\n'+'\n'.join('+'+line for line in content.splitlines())+'\n'


def files():
    from drawing import render
    drawings=render(sys.modules[__name__])
    result={}
    root=tag('kicad_sch',tag('version',20260306),tag('generator','bldc-esc'),tag('uuid',ROOT_ID),tag('paper','A3'),tag('lib_symbols'))
    root.append(tag('text','BLDC-ESC / v1 / schematic draft',tag('at',35,22,0),effect(2,'left'),tag('uuid',uid('root:heading'))))
    captions=['XT60 / DC-link / TVS / MT60','MOSFETs / shunts / INA241','Bus clamp / dump switch','Buck / power mux / 3V3',
              'STM32G474 / reference / SWD','Hall / encoder / sensor power','CAN FD / UART','Throttle / RC PWM / digital I/O',
              'Arm latch / PWM buffer / interlocks','Bus and phase ADC buffers','Hardware current and bus windows','DRV8353 / gate supplies / SPI',
              'USB-C / ESD / status LEDs','NTCs / analog rail monitor','Chopper OCP / latch / telemetry','Reset / watchdog / service mode']
    for i,name in enumerate(SHEETS):
        x=25+94*(i%4);y=40+51*(i//4)
        root.append(tag('sheet',tag('at',x,y),tag('size',82,38),tag('stroke',tag('width',0.254),tag('type',A('default'))),
            tag('fill',tag('color',0,0,0,0)),tag('uuid','10000000-0000-4000-8000-%012d'%(i+1)),
            tag('property','Sheetname',name,tag('at',x,y-1,0),effect(1.27,'left bottom')),
            tag('property','Sheetfile','schematic/'+name+'.kicad_sch',tag('at',x,y+39,0),effect(1.0,'left top')),
            tag('instances',tag('project','bldc-esc',tag('path','/'+ROOT_ID,tag('page',str(i+2)))))))
        root.append(tag('text',captions[i],tag('at',x+5,y+17,0),effect(1.45,'left'),tag('uuid',uid('root:caption:'+name))))
    root.extend([tag('sheet_instances',tag('path','/',tag('page','1'))),tag('embedded_fonts',A('no'))])
    root.append(tag('text','X = DNP / not fitted. v1 draft; electrical review and bench validation pending.',tag('at',25,279,0),effect(1.27,'left'),tag('uuid',uid('root:dnp-key'))))
    result['bldc-esc.kicad_sch']=dump(root)+'\n'
    for name in SHEETS:
        result['schematic/'+name+'.kicad_sch']=drawings[name]
    result['bldc-esc.kicad_sym']=dump(tag('kicad_symbol_lib',tag('version',20241209),tag('generator','bldc-esc'),*custom.values()))+'\n'
    result['sym-lib-table']='(sym_lib_table\n  (version 7)\n  (lib (name "bldc-esc")(type "KiCad")(uri "${KIPRJMOD}/bldc-esc.kicad_sym")(options "")(descr ""))\n)\n'
    result['fp-lib-table']='(fp_lib_table\n  (version 7)\n  (lib (name "bldc-esc")(type "KiCad")(uri "${KIPRJMOD}/bldc-esc.pretty")(options "")(descr ""))\n)\n'
    result.update(footprints())
    out=io.StringIO();writer=csv.writer(out,lineterminator='\n');writer.writerow(['reference','sheet','value','MPN','manufacturer','footprint','DNP','exclude_from_BOM'])
    for p in parts:
        if not p['ref'].startswith('#'):writer.writerow([p['ref'],p['sheet'],p['value'],p['mpn'],p['manufacturer'],p['footprint'],str(p['dnp']).lower(),str(p['ref'].startswith('TP')).lower()])
    result['engineering/schematic_bom.csv']=out.getvalue()
    out=io.StringIO();writer=csv.writer(out,lineterminator='\n');writer.writerow(['reference','pin','net'])
    for p in parts:
        for pin,net in p['nets'].items():
            if net is not None:writer.writerow([p['ref'],pin,net])
    result['engineering/connection_matrix.csv']=out.getvalue()
    result['engineering/schematic_drawing_metrics.json']=json.dumps(drawing_metrics,indent=2)+'\n'
    return result


def main():
    define_symbols()
    from circuits import build
    build(sys.modules[__name__])
    for p in parts:
        p['x']=round(round(p['x']/1.27)*1.27,4)
        p['y']=round(round(p['y']/1.27)*1.27,4)
    refs=[p['ref'] for p in parts]
    if len(refs)!=len(set(refs)):raise ValueError('DUPLICATE_REFERENCES')
    generated=files()
    if len(sys.argv)==1:
        print(json.dumps({'parts':len(parts),'files':{k:len(v) for k,v in generated.items()}},indent=2));return
    if sys.argv[1]=='--patch':
        selected=sys.argv[2:] or list(generated)
        print('*** Begin Patch')
        for name in selected:print(patch(name,generated[name]),end='')
        print('*** End Patch')
    elif sys.argv[1]=='--check':
        mismatch=[name for name,value in generated.items() if not (ROOT/name).exists() or (ROOT/name).read_text()!=value]
        print(json.dumps({'generated_files':len(generated),'mismatches':mismatch},indent=2))
        sys.exit(bool(mismatch))
    elif sys.argv[1]=='--inventory':
        print(json.dumps([{k:v for k,v in p.items() if k!='node'} for p in parts]))


if __name__=='__main__':main()
