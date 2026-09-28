import copy
import math
from collections import defaultdict

from kicad_sexpr import Atom as A, child, dump, pins, symbol, tag


G = 2.54
RAILS = {'GND', 'VBUS', '3V3', '3V3_A', '5V_BUS', '5V_SYS', 'USB_5V',
         '5V_HALL', '5V_ENCODER'}


def xy(x, y):
    return round(x * G, 4), round(y * G, 4)


def replace_units(c):
    for name, source in [('TLV9024', 'Comparator:LM339'),
                         ('TLV9064', 'Amplifier_Operational:TLV9064'),
                         ('TLV9062', 'Amplifier_Operational:TLV9062'),
                         ('SN74LVC3G17', '74xGxx:74LVC3G17')]:
        old = c.custom[name]
        node = symbol(source)
        stem = node[1]
        node[1] = name
        for section in node:
            if isinstance(section, list) and section[0] == 'symbol':
                section[1] = name + section[1][len(stem):]
        for prop in node:
            if isinstance(prop, list) and prop[0] == 'property' and prop[1] == 'Datasheet':
                prop[2] = next(p[2] for p in old if isinstance(p, list) and p[0] == 'property' and p[1] == 'Datasheet')
        c.custom[name] = node
        for p in c.parts:
            if p['lib_id'] == 'bldc-esc:' + name:
                p['node'] = copy.deepcopy(node)


class Drawing:
    def __init__(self, c, sheet, title, paper='A3'):
        self.c, self.sheet, self.title, self.paper = c, sheet, title, paper
        self.parts = {p['ref']:p for p in c.parts if p['sheet'] == sheet}
        self.inst, self.at, self.handled = {}, {}, set()
        self.segments, self.labels, self.texts = [], [], []
        self.fields, self.power_sites = {}, []
        self.groups = defaultdict(set)
        for p in c.parts:
            for net in p['nets'].values():
                if net: self.groups[net].add(p['sheet'])

    def put(self, ref, x, y, angle=0, unit=1):
        p = self.parts[ref]
        q = dict(p, x=xy(x,y)[0], y=xy(x,y)[1], angle=angle, unit=unit)
        self.inst[(ref,unit)] = q
        theta = math.radians(angle)
        for pin in pins(q['node'], unit):
            num = str(child(pin,'number')[1]); a = child(pin,'at')
            px, py = float(a[1]), float(a[2])
            self.at[(ref,num)] = (round(q['x']+px*math.cos(theta)-py*math.sin(theta),4),
                                  round(q['y']-px*math.sin(theta)-py*math.cos(theta),4))
        return q

    def field(self, ref, x, y, unit=1):
        self.fields[(ref,unit)] = xy(x,y)

    def point(self, value):
        if isinstance(value,str):
            ref,pin=value.split('.')
            return self.at[(ref,pin)]
        return xy(*value)

    def net(self, value):
        ref,pin=value.split('.')
        return self.parts[ref]['nets'][pin]

    def line(self, net, points):
        for a,b in zip(points,points[1:]):
            if a == b: continue
            if a[0] != b[0] and a[1] != b[1]:
                mid=(b[0],a[1])
                self.segments.extend([(net,a,mid),(net,mid,b)])
            else:self.segments.append((net,a,b))

    def wire(self, *values, label=False):
        terminals=[v for v in values if isinstance(v,str)]
        nets={self.net(v) for v in terminals}
        if len(nets)!=1 or None in nets: raise ValueError(('WIRE_NET',values,nets))
        net=next(iter(nets)); points=[self.point(v) for v in values]
        self.line(net,points)
        self.handled.update(tuple(v.split('.')) for v in terminals)
        if label:
            a,b=max(zip(points,points[1:]),key=lambda v:abs(v[1][0]-v[0][0])+abs(v[1][1]-v[0][1]))
            pos=(round((a[0]+b[0])/2,4),round((a[1]+b[1])/2,4)) if a[0]==b[0] or a[1]==b[1] else points[0]
            self.labels.append((net,pos,'left'))

    def bus(self, terminals, axis='h', level=None, label=False):
        nets={self.net(v) for v in terminals}
        if len(nets)!=1: raise ValueError(('BUS_NET',terminals,nets))
        net=next(iter(nets)); pts=[self.point(v) for v in terminals]
        k=1 if axis=='h' else 0
        target=round(level*G,4) if level is not None else pts[0][k]
        ends=[]
        for value,pt in zip(terminals,pts):
            end=(pt[0],target) if axis=='h' else (target,pt[1])
            self.line(net,[pt,end]);ends.append(end)
            self.handled.add(tuple(value.split('.')))
        ends=sorted(set(ends),key=lambda p:p[1-k])
        self.line(net,ends)
        if label: self.labels.append((net,ends[-1] if len(self.groups[net])>1 else ends[0],'left'))

    def label(self, terminal, direction=None, length=2):
        ref,num=terminal.split('.');p=self.parts[ref]
        inst=next(q for (r,u),q in self.inst.items() if r==ref and any(str(child(n,'number')[1])==num for n in pins(q['node'],u)))
        pin=next(n for n in pins(inst['node'],inst['unit']) if str(child(n,'number')[1])==num)
        a=math.radians(float(child(pin,'at')[3])+inst['angle'])
        dx,dy=-round(math.cos(a)),round(math.sin(a))
        if direction: dx,dy={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}[direction]
        start=self.point(terminal);end=(round(start[0]+dx*length*G,4),round(start[1]+dy*length*G,4))
        net=self.net(terminal)
        self.line(net,[start,end]);self.handled.add((ref,num))
        if net in RAILS:
            self.power_sites.append((net,end,180 if net!='GND' and dy>0 else 0))
        else:self.labels.append((net,end,'right' if dx<0 else 'left'))

    def note(self,x,y,text,size=1.15):
        self.texts.append((xy(x,y),text,size))

    def heading(self,x,y,text): self.note(x,y,text,1.6)

    def decap(self, ref, x, y, supply=None):
        self.put(ref,x,y)
        self.label(ref+'.1','u');self.label(ref+'.2','d')

    def rc(self, r, cap, x, y, output=None):
        self.put(r,x,y,90);self.put(cap,x+7,y+5)
        self.wire(r+'.2',(x+7,y),cap+'.1',label=True)
        self.label(r+'.1','l');self.label(cap+'.2','d')

    def divider(self, top, bottom, cap, x, y):
        self.put(top,x,y);self.put(bottom,x,y+10)
        self.wire(top+'.2',bottom+'.1',label=True)
        self.label(top+'.1','u');self.label(bottom+'.2','d')
        if cap:
            self.put(cap,x+10,y+10)
            self.bus([top+'.2',cap+'.1'],level=y+5)
            self.label(cap+'.2','d')

    def finish(self):
        c=self.c; index=c.SHEETS.index(self.sheet)+1
        missing=[]
        for ref,p in self.parts.items():
            nums=set(self.atkey(ref))
            if nums!=set(p['nets']):missing.append((ref,sorted(set(p['nets'])-nums)))
        if missing:raise ValueError(('UNPLACED',self.sheet,missing))
        # Consolidate adjacent supply pins into a single rail connection.
        for (ref,unit),q in self.inst.items():
            candidates=defaultdict(list)
            for pin in pins(q['node'],unit):
                num=str(child(pin,'number')[1]);net=q['nets'][num]
                if net not in RAILS or (ref,num) in self.handled:continue
                a=(float(child(pin,'at')[3])+q['angle'])%360
                if a in (0,180):candidates[(net,a,self.at[(ref,num)][0])].append(ref+'.'+num)
            for (net,a,x),terms in candidates.items():
                if len(terms)<2:continue
                ys=[self.point(t)[1] for t in terms]
                if any(r==ref and pos[0]==x and min(ys)<pos[1]<max(ys) and q['nets'][num]!=net for (r,num),pos in self.at.items()):continue
                busx=x/G+(-2 if a==0 else 2)
                self.bus(terms,axis='v',level=busx)
                edge=max(ys)/G if net=='GND' else min(ys)/G
                outer=busx+(-1.5 if a==0 else 1.5)
                end=xy(outer,edge+2 if net=='GND' else edge-2)
                self.line(net,[xy(busx,edge),xy(outer,edge),end])
                self.power_sites.append((net,end,0))
        seen={}
        ncs=[]
        for (ref,num),pt in self.at.items():
            net=self.parts[ref]['nets'][num]
            if pt in seen:
                if seen[pt]!=net:raise ValueError(('PIN_COLLISION',self.sheet,ref,num,pt,net,seen[pt]))
                self.handled.add((ref,num));continue
            seen[pt]=net
            if net is None:ncs.append((ref,num,pt));continue
            if (ref,num) not in self.handled:self.label(ref+'.'+num)
        libraries={}
        for p in self.parts.values():
            node=copy.deepcopy(p['node']);node[1]=p['lib_id'];libraries[p['lib_id']]=node
        for power in ('GND','VCC'):
            node=symbol('power:'+power);node[1]='power:'+power;libraries[node[1]]=node
        out=tag('kicad_sch',tag('version',20260306),tag('generator','eeschema'),
                tag('uuid','20000000-0000-4000-8000-%012d'%index),tag('paper',self.paper),
                tag('title_block',tag('title',self.title),tag('rev','v1-draft')),
                tag('lib_symbols',*libraries.values()))
        texts=[(xy(8,8),self.title,2.0),*self.texts]
        for i,(pos,text,size) in enumerate(texts):
            out.append(tag('text',text,tag('at',*pos,0),c.effect(size,'left'),tag('uuid',c.uid(self.sheet+':text:'+str(i)))))
        for (ref,unit),p in self.inst.items():
            n=tag('symbol',tag('lib_id',p['lib_id']),tag('at',p['x'],p['y'],p['angle']),tag('unit',unit),
                tag('exclude_from_sim',A('no')),tag('in_bom',A('no' if ref.startswith(('#','TP')) else 'yes')),
                tag('on_board',A('no' if ref.startswith('#') else 'yes')),tag('dnp',A('yes' if p['dnp'] else 'no')),
                tag('uuid',c.uid(ref if unit==1 else ref+':unit:'+str(unit))))
            if ref.startswith('TP'):n.append(tag('in_pos_files',A('no')))
            count=len(pins(p['node'],unit));x,y=p['x'],p['y']
            if (ref,unit) in self.fields:tx,ty=self.fields[(ref,unit)]
            elif count<=4:
                tx,ty=(x-4,y-8.89) if p['angle']==90 else (x+3.81,y-2.54)
            else:tx,ty=x,min(self.at[(ref,str(child(pin,'number')[1]))][1] for pin in pins(p['node'],unit))-7.62
            if ref.startswith('U') and count<=3:tx,ty=x,y-10.16
            if ref.startswith('U') and 4<=count<=8 and p['lib_id'].startswith(('Amplifier_','74xGxx:')) and (ref,unit) not in self.fields:tx,ty=x+8.89,y-8.89
            if ref.startswith('Q'):tx,ty=x+6.35,y-5.08
            if p['lib_id']=='Device:R_Shunt':tx,ty=x-15.24,y-2.54
            value=p['value']
            ds=p.get('datasheet',next((v[2] for v in p['node'] if isinstance(v,list) and v[0]=='property' and v[1]=='Datasheet'),''))
            for key,value,hidden in [('Reference',ref,False),('Value',value,False),('Footprint',p['footprint'],True),
                ('Datasheet',ds,True),('MPN',p['mpn'],True),('Manufacturer',p['manufacturer'],True)]:
                px,py=(tx,ty+(2.0 if key=='Value' else 0)) if not hidden else (x,y)
                prop=tag('property',key,value,tag('at',round(px,4),round(py,4),p['angle']%180),c.effect(1.15,'left' if count<=4 and not ref.startswith('U') else None))
                if hidden or ref.startswith('#'):prop.append(tag('hide',A('yes')))
                n.append(prop)
            n.append(tag('instances',tag('project','bldc-esc',tag('path','/'+c.ROOT_ID+'/10000000-0000-4000-8000-%012d'%index,tag('reference',ref),tag('unit',unit)))))
            out.append(n)
        for i,(net,pos,angle) in enumerate(self.power_sites):
            ref='#PWR%02d%04d'%(index,i+1)
            node=tag('symbol',tag('lib_id','power:GND' if net=='GND' else 'power:VCC'),tag('at',*pos,angle),tag('unit',1),
                tag('exclude_from_sim',A('no')),tag('in_bom',A('no')),tag('on_board',A('yes')),tag('dnp',A('no')),
                tag('uuid',c.uid(self.sheet+':power:'+str(i))),
                tag('property','Reference',ref,tag('at',*pos,0),c.effect(hide=True)),
                tag('property','Value',net,tag('at',pos[0],round(pos[1]+(4.0 if net=='GND' or angle else -4.0),4),0),c.effect(1.0)),
                tag('instances',tag('project','bldc-esc',tag('path','/'+c.ROOT_ID+'/10000000-0000-4000-8000-%012d'%index,tag('reference',ref),tag('unit',1)))))
            out.append(node)
        # Explicit wire paths define circuit topology; labels name one connected node.
        vertices=defaultdict(set)
        for net,a,b in self.segments:vertices[net].update((a,b))
        for key,pos in self.at.items():
            net=self.parts[key[0]]['nets'][key[1]]
            if net:vertices[net].add(pos)
        def on(p,a,b):
            return min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1])
        unique=set(); degree=defaultdict(int)
        for net,a,b in self.segments:
            pts=sorted([p for p in vertices[net] if on(p,a,b)])
            for start,end in zip(pts,pts[1:]):
                key=(net,start,end)
                if start!=end and key not in unique:
                    unique.add(key);degree[(net,start)]+=1;degree[(net,end)]+=1
        for i,(net,a,b) in enumerate(sorted(unique)):
            out.append(c.wire_node(a,b,self.sheet+':wire:'+str(i)))
        for (net,pos),count in degree.items():
            if count>=3:out.append(tag('junction',tag('at',*pos),tag('diameter',0),tag('color',0,0,0,0),tag('uuid',c.uid(self.sheet+':junction:'+net+str(pos)))))
        for i,(net,pos,justify) in enumerate(dict.fromkeys(self.labels)):
            label=c.label_node(net,*pos,'left' if justify=='right' else 'right',len(self.groups[net])>1)
            child(label,'uuid')[1]=c.uid(self.sheet+':label:'+str(i));out.append(label)
        for ref,num,pos in ncs:out.append(tag('no_connect',tag('at',*pos),tag('uuid',c.uid(ref+':NC:'+num))))
        out.append(tag('embedded_fonts',A('no')))
        from compact_drawing import compact_blocks
        c.drawing_metrics[self.sheet]=compact_blocks(out,self.sheet)
        return dump(out)+'\n'

    def atkey(self,ref):
        return (num for r,num in self.at if r==ref)


def dc_link(d):
    d.heading(10,18,'DC input and local energy storage')
    d.put('J101',18,33)
    d.put('D101',28,36,90)
    d.field('D101',29,27)
    caps=['C'+str(n) for n in [101,102,103,104,105,106,107,108,115,116]]
    for i,r in enumerate(caps):d.put(r,40+10*i,36)
    d.put('R101',144,36)
    d.bus(['J101.1','D101.1','R101.1']+[r+'.1' for r in caps],level=29,label=True)
    d.bus(['J101.2','D101.2','R101.2']+[r+'.2' for r in caps],level=43)
    d.power_sites.append(('GND',xy(144,43),0))
    d.note(10,52,'12-30 V operating bus. External DC-rated fuse required close to the source. No electronic reverse-polarity protection.')
    d.note(10,57,'C101-C108, C115-C116: 10 x 100 uF / 63 V hybrid, 1,000 uF total. Bulk bank does not absorb sustained regeneration.')
    d.heading(10,72,'Shield / chassis connection')
    d.put('J103',18,84);d.put('R102',34,86);d.put('C109',48,86);d.put('R103',62,86)
    d.bus(['J103.1','R102.1','C109.1','R103.1'],level=80,label=True)
    d.bus(['J103.2','R102.2','C109.2','R103.2'],level=93)
    d.power_sites.append(('GND',xy(62,93),0))
    d.note(10,102,'R103 is DNP. Select the chassis bond after enclosure and EMI review.')
    d.heading(91,72,'Motor cable / test points')
    d.put('J102',111,79)
    for i,r in enumerate(['TP101','TP102','TP103','TP104','TP105']):d.put(r,92+13*i,92)
    d.put('#FLG101',146,65);d.put('#FLG102',152,65)
    d.note(91,98,'MT60 pigtail: 1=A, 2=B, 3=C. Provide strain relief.')


def gate_driver(d):
    d.heading(10,17,'Gate driver / charge pump')
    d.put('U201',35,55)
    d.label('U201.3','l',length=11)
    d.label('U201.4','l',length=8)
    d.label('U201.24','l',length=5)
    d.put('R201',17,24,90);d.put('C201',26,30);d.put('C202',34,30)
    d.wire('R201.2',(26,24),'C201.1',label=True)
    d.bus(['C201.1','C202.1'],level=24)
    d.put('C203',60,27);d.put('C204',70,36);d.put('C205',61,47);d.put('C206',61,60)
    d.put('C207',18,53)
    d.put('R202',12,67);d.put('R203',24,67);d.put('R204',36,82);d.put('R205',48,82)
    d.put('#FLG201',18,35)
    for r in ['C201','C202','C205','C206','C207']:d.label(r+'.2','d')
    # Short local pump wiring; high-current return labels remain explicit.
    for i,(term,cap,pin) in enumerate([('U201.1','C203','2'),('U201.2','C203','1'),('U201.5','C204','1'),('U201.40','C205','1'),('U201.38','C206','1')]):
        a=d.point(term);b=d.point(cap+'.'+pin);x=(50+2*i)*G
        d.wire(term,(x/G,a[1]/G),(x/G,b[1]/G),cap+'.'+pin,label=True)
    d.note(10,99,'VM filter and pump capacitors belong next to U201. VCP reservoir returns to VBUS, not GND.')
    d.note(10,106,'SPx returns directly to each low-side source. SNx / CSA inputs use Kelvin shunt sense pads.')
    d.note(10,113,'Six PWM inputs arrive through the hardware arm interlock. ENABLE is separate for driver setup.')


def bridge(d):
    for i,phase in enumerate('ABC'):
        x=96+42*i;b=210+20*i;hi='Q'+str(201+2*i);lo='Q'+str(202+2*i);sh='R'+str(b+4)
        d.heading(x-13,17,'Phase '+phase)
        d.put(hi,x,30);d.put(lo,x,44);d.put(sh,x+1,57)
        d.put('R'+str(b),x-13,30,90);d.put('R'+str(b+2),x-13,44,90)
        d.put('R'+str(b+1),x-5,32.5);d.put('R'+str(b+3),x-5,46.5)
        for offset,y,fet in [(0,27,hi),(1,41,lo)]:
            tp='TP'+str(220+20*i+offset)
            d.put(tp,x-5,y)
            d.wire(tp+'.1',(x-5,d.point(fet+'.4')[1]/G),fet+'.4')
        tp='TP'+str(222+20*i)
        d.put(tp,x+11,52)
        d.wire(lo+'.1',(x+1,52),tp+'.1')
        d.wire(hi+'.1',lo+'.5',label=True);d.wire(lo+'.1',sh+'.1',label=True)
        for r,fet,pulldown in [('R'+str(b),hi,'R'+str(b+1)),('R'+str(b+2),lo,'R'+str(b+3))]:
            d.wire(r+'.2',fet+'.4',label=True)
            gp=d.point(fet+'.4');d.bus([r+'.2',pulldown+'.1'],level=gp[1]/G)
            sp=d.point(fet+'.1');d.bus([pulldown+'.2',fet+'.1'],level=sp[1]/G+3)
        d.put('C'+str(b),x+11,25);d.put('C'+str(b+1),x+22,25)
        d.bus([hi+'.5','C'+str(b)+'.1','C'+str(b+1)+'.1'],level=21,label=True)
        d.bus(['C'+str(b)+'.2','C'+str(b+1)+'.2'],level=30)
        d.power_sites.append(('GND',xy(x+22,30),0))
        d.put('R'+str(b+7),x+19,42);d.put('C'+str(b+5),x+19,50)
        d.wire('R'+str(b+7)+'.2','C'+str(b+5)+'.1',label=True)
        d.label('R'+str(b+7)+'.1','u');d.label('C'+str(b+5)+'.2','d')
        d.label(sh+'.4','d')
        amp='U'+str(202+i)
        d.put(amp,x+7,70);d.put('C'+str(b+2),x-10,65)
        # Kelvin sense pair is drawn from the shunt to the amplifier inputs.
        a=d.point(sh+'.2');e=d.point(amp+'.8')
        d.wire(sh+'.2',(x+4,a[1]/G),(x+4,e[1]/G),amp+'.8',label=True)
        a=d.point(sh+'.3');e=d.point(amp+'.1')
        d.wire(sh+'.3',(x-1,a[1]/G),(x-1,e[1]/G),amp+'.1',label=True)
        d.bus([amp+'.3',amp+'.7'],level=76,label=True)
        d.rc('R'+str(b+5),'C'+str(b+3),x+12,82)
        d.put('TP'+str(210+i),x+23,82)
        d.wire('R'+str(b+5)+'.2','TP'+str(210+i)+'.1')
        out=d.point(amp+'.5');r=d.point('R'+str(b+5)+'.1')
        d.wire(amp+'.5',(x+12,out[1]/G),(x+12,77),(r[0]/G,77),'R'+str(b+5)+'.1')
        d.rc('R'+str(b+6),'C'+str(b+4),x+9,94)
        if i==0:d.note(x-13,109,'Main CSA: 1.5 V zero, 20 mV/A\nGate probes need local source returns.\nHigh-side VGS: differential probe only.',1.1)


def power_usb(d):
    d.heading(8,17,'Bus supply / LM5164, nominal 5 V')
    d.put('U401',43,34)
    d.put('C401',13,34);d.put('C402',22,34)
    d.bus(['U401.2','C401.1','C402.1'],level=27,label=True)
    d.bus(['C401.2','C402.2'],level=40);d.power_sites.append(('GND',xy(13,40),0))
    d.divider('R401','R402',None,30,43)
    p=d.point('U401.3');d.wire('U401.3',(34,p[1]/G),(34,48),(30,48),'R401.2')
    d.put('R403',38,52)
    a=d.point('U401.4');d.wire('U401.4',(36,a[1]/G),(36,48),(38,48),'R403.1',label=True)
    d.put('C403',54,31)
    d.wire('U401.7',(52,31),(52,29.5),'C403.1',label=True)
    d.put('L401',65,33,90)
    d.field('L401',69,25)
    d.field('C403',54,23)
    d.bus(['U401.8','L401.1','C403.2'],level=33,label=True)
    d.put('C404',77,39);d.put('C405',87,39)
    d.bus(['L401.2','C404.1','C405.1'],level=33,label=True)
    d.bus(['C404.2','C405.2'],level=46);d.power_sites.append(('GND',xy(87,46),0))
    d.divider('R404','R405',None,77,55)
    d.put('R406',56,45);d.put('C406',65,50);d.put('C407',60,61,90)
    d.field('C406',68,50)
    d.bus(['R406.1','L401.1'],axis='v',level=56,label=True)
    d.bus(['R406.2','C406.1'],level=50,label=True)
    d.wire('C406.1',(60,47),'C407.1')
    d.label('C406.2','d')
    d.bus(['U401.5','R404.2','C407.2'],level=60,label=True)
    d.put('R407',88,59)
    d.note(8,72,'68 uH / about 300 kHz. R406, C406, C407 provide type-3 ripple injection. Verify startup and load transients.')
    d.heading(102,17,'Bus / USB selection and 3.3 V')
    d.put('U402',122,31);d.put('C408',104,29);d.put('C409',103,43)
    d.divider('R408','R409',None,112,40)
    d.put('C410',139,36);d.put('R410',139,49)
    d.wire('U402.2',(139,29),'C410.1',label=True)
    d.wire('U402.3',(115,29),'C408.1',label=True)
    d.wire('U402.4',(115,30),(115,45),(112,45),'R408.2',label=True)
    d.put('U403',122,64);d.put('C411',110,69);d.put('C412',137,69)
    d.bus(['U403.6','U403.4','C411.1'],axis='v',level=115,label=True)
    d.bus(['U403.1','C412.1'],level=63,label=True)
    d.note(102,79,'USB-only operation: bridge disarmed;\nsensor supplies disabled at boot.')


def usb_status(d):
    d.heading(8,83,'USB-C device port')
    d.put('J401',23,101)
    d.put('R411',9,104);d.put('R412',9,115)
    d.put('F401',44,84,90);d.put('C413',36,90)
    d.put('U404',53,102)
    d.put('R413',65,102,90);d.put('R414',77,103,90)
    d.wire('U404.6','R413.1',label=True)
    d.wire('U404.4','R414.1',label=True)
    d.divider('R415','R416',None,87,89)
    d.heading(102,88,'Status / probe points')
    for i in range(3):
        r='R'+str(511+i);led='D'+str(511+i);x=105+15*i
        d.put(r,x,98);d.put(led,x,109,90)
        d.wire(r+'.2',led+'.2',label=True)
    for i,r in enumerate(['TP401','TP402','TP403','TP404']):d.put(r,103+13*i,121)
    for i,r in enumerate(['#FLG401','#FLG402','#FLG403']):d.put(r,15+18*i,125)
    d.note(8,133,'USB shield bonds to CHASSIS. D+/D- protection belongs close to the connector; 22 ohm resistors belong near the MCU.')


def mcu(d):
    d.heading(8,17,'STM32G474VET6 / TIM1 bridge control')
    d.put('U501',58,61)
    d.field('U501',48,24)
    vdd=['U501.'+str(n) for n in [6,24,49,64,75,100]]
    d.bus(vdd,level=29,label=True)
    d.bus(['U501.23','U501.35'],level=92)
    d.power_sites.append(('GND',xy(58,92),0))
    d.heading(88,17,'VDDA and reference')
    d.put('FB501',100,26,90);d.put('C507',113,32);d.put('C508',125,32)
    d.bus(['FB501.2','C507.1','C508.1'],level=26,label=True)
    d.put('U502',112,49);d.put('C509',97,45)
    d.field('U502',118,39)
    d.put('C510',128,47);d.put('C511',139,47);d.put('R501',150,47)
    d.bus(['U502.5','C510.1','C511.1','R501.1'],level=42,label=True)
    d.put('D501',143,32,90)
    d.put('C512',126,60)
    d.wire('U502.1',(126,50),'C512.1',label=True)
    d.heading(8,99,'MCU bypass capacitors')
    for i,r in enumerate(['C501','C502','C503','C504','C505','C517','C506']):d.put(r,12+11*i,109)
    d.bus([r+'.1' for r in ['C501','C502','C503','C504','C505','C517','C506']],level=104,label=True)
    d.bus([r+'.2' for r in ['C501','C502','C503','C504','C505','C517','C506']],level=115)
    d.power_sites.append(('GND',xy(78,115),0))
    d.heading(8,20,'')
    d.put('Y501',19,44)
    d.field('Y501',15,37)
    d.put('R502',33,44,270)
    d.put('C513',12,52);d.put('C514',25,52)
    d.bus(['Y501.1','C513.1'],axis='v',level=12,label=True)
    d.wire('Y501.2','R502.2',label=True)
    d.bus(['Y501.2','C514.1'],level=44)
    d.note(8,61,'8 MHz crystal; load capacitors\nremain subject to startup validation.')
    d.put('R504',15,70);d.put('C515',15,82);d.put('SW501',28,77)
    d.bus(['R504.2','C515.1','SW501.1'],level=77,label=True)
    d.put('R503',85,62);d.put('JP501',85,74)
    d.note(93,70,'PB8 is BOOT0. PA15 carries I2C1 SCL.',1.1)
    d.heading(93,78,'Nonvolatile configuration')
    d.put('U503',112,91);d.put('R506',135,80);d.put('R507',148,80)
    d.put('R508',94,98);d.put('C516',145,100)
    d.heading(175,17,'Programming / debug')
    d.put('J501',185,31)
    d.put('R505',175,56);d.put('SW502',185,64)
    d.wire('R505.2',(175,64),'SW502.1',label=True)
    for i,r in enumerate(['TP501','TP502','TP503','TP504','TP505','TP506']):d.put(r,178,83+12*i)
    d.put('#FLG501',154,26)
    d.note(94,114,'VREF+ = 3.0 V; current midpoint = 1.5 V.\nReference supply tracks VDDA during brownout.')
    d.note(10,134,'Injected ADC conversions use TIM1 TRGO. Configure break inputs, deadtime and safe GPIO states before requesting bridge arm.')


def sensors(d):
    for k,(prefix,base) in enumerate([('Hall',0),('Encoder',82)]):
        d.heading(8+base,17,prefix+' interface')
        u='U'+str(601+k);first=601+4*k
        d.put(u,base+37,30)
        d.put('R'+str(first),base+16,37);d.put('R'+str(first+1),base+17,24)
        d.put('R'+str(first+2),base+61,28)
        d.decap('C'+str(601+2*k),base+9,28);d.decap('C'+str(602+2*k),base+69,28)
        d.put('J'+str(601+k),base+16,60)
        buf='U'+str(603+k)
        for j,unit in enumerate([1,3,2]):
            y=55+17*j;n=620+12*k+3*j
            d.put(buf,base+56,y,unit=unit)
            d.put('R'+str(n),base+41,y,90)
            d.put('R'+str(n+1),base+24,y-7)
            d.put('C'+str(610+3*k+j),base+47,y+6)
            d.put('D'+str(610+3*k+j),base+29,y+7,90)
            inp=str([1,3,6][j]);r='R'+str(n);pull='R'+str(n+1);cap='C'+str(610+3*k+j);esd='D'+str(610+3*k+j)
            d.wire(r+'.2',buf+'.'+inp,label=True)
            d.bus([r+'.2',cap+'.1'],level=y)
            d.bus([r+'.1',pull+'.2',esd+'.1'],level=y,label=True)
        d.put(buf,base+50,39,unit=4);d.decap('C'+str(605+k),base+76,40)
        d.note(base+8,109,'5 V supply: current limited, latch-off on fault.\nInputs: 3.3/5 V single-ended, not 24 V.',1.1)
    d.note(8,117,'Connector labels define the controller pinout only. Verify the OEM motor Hall supply, ground and signal wires before connection.')


def communications(d):
    d.heading(8,18,'CAN FD')
    d.put('U709',45,40);d.put('C704',24,25)
    d.decap('C706',38,25)
    d.put('R717',15,40);d.put('R718',15,53)
    d.put('D703',89,54);d.put('J701',132,36)
    d.field('D703',89,48)
    d.label('J701.1','l',length=8)
    d.put('R719',109,46);d.put('JP701',120,58)
    d.wire('R719.2',(109,58),'JP701.1',label=True)
    d.wire('U709.7',(126,38.5),(126,36),'J701.2',label=True)
    d.wire('U709.6',(53,39.5),(53,42.5),(123,42.5),(123,37),'J701.3',label=True)
    d.wire('D703.1',(81,53.5),(81,38.5),(109,38.5),'R719.1')
    d.wire('D703.2',(78,54.5),(78,42.5),(115,42.5),(115,59),'JP701.2')
    p=d.point('U709.8');q=d.point('R717.2')
    d.wire('R717.2',(28,q[1]/G),(28,p[1]/G),'U709.8',label=True)
    p=d.point('U709.1');q=d.point('R718.2')
    d.wire('R718.2',(32,q[1]/G),(32,p[1]/G),'U709.1',label=True)
    d.note(8,76,'JP701 fitted = 120 ohm termination. Fit termination only at the two ends of the CAN bus.')
    d.heading(8,88,'UART / 3.3 V logic')
    d.put('J702',33,102)
    d.label('J702.1','l',length=8)
    d.label('J702.4','l',length=11)
    d.note(63,102,'Short local 3.3 V wiring only; TX/RX are controller-side names.\nNot an RS-232 or 5 V port. Supply pin is an output, not a power input.')


def voltage_sensing(d):
    for i,label in enumerate(['Bus voltage','Phase A voltage','Phase B voltage','Phase C voltage']):
        x=12 if i%2==0 else 88;y=28+43*(i//2);n=801+10*i
        d.heading(x,y-10,label)
        d.put('R'+str(n),x+3,y,90);d.put('R'+str(n+1),x+17,y,90)
        d.wire('R'+str(n)+'.2','R'+str(n+1)+'.1',label=True)
        d.put('R'+str(n+2),x+27,y+7);d.put('C'+str(n),x+37,y+7)
        d.put('D'+str(n),x+16,y+14,90);d.field('D'+str(n),x+9,y+16)
        unit=i+1;pos,neg,out=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)][i]
        d.put('U801',x+46,y+1,unit=unit)
        d.bus(['R'+str(n+1)+'.2','R'+str(n+2)+'.1','C'+str(n)+'.1','U801.'+str(pos)],level=y)
        d.labels.append((d.net('U801.'+str(pos)),xy(x+38,y),'right'))
        d.wire('D'+str(n)+'.3',(x+22,y+14),(x+22,y),'R'+str(n+2)+'.1')
        d.put('R'+str(n+3),x+57,y+1,90);d.put('C'+str(n+1),x+68,y+8)
        d.wire('U801.'+str(out),'R'+str(n+3)+'.1')
        d.labels.append((d.net('U801.'+str(out)),xy(x+54,y+1),'right'))
        d.wire('U801.'+str(neg),(x+41,y+2),(x+41,y+9),(x+51,y+9),(x+51,y+1),'U801.'+str(out))
        d.wire('R'+str(n+3)+'.2',(x+68,y+1),'C'+str(n+1)+'.1',label=True)
    d.put('U801',32,103,unit=5);d.decap('C840',45,103)
    d.note(65,99,'21:1 dividers; 3.0 V ADC full scale = 63 V at the input.\nBuffers isolate the dividers from ADC sampling transients.\nNormal operation remains limited to a 12-30 V bus.')


def current_protection(d):
    d.heading(8,17,'Bipolar phase-current window')
    defs=[('U101',1,2,5,4),('U101',2,1,7,6),('U101',4,14,9,8),('U101',3,13,11,10),
          ('U102',1,2,5,4),('U102',2,1,7,6)]
    for i,(ref,unit,out,pos,neg) in enumerate(defs):
        x=29+48*(i//2);y=31+13*(i%2)
        d.put(ref,x,y,unit=unit)
        d.note(x-13,y-10,['Phase A','Phase B','Phase C'][i//2] + (' / upper' if i%2==0 else ' / lower'),1.2)
    d.bus(['U101.2','U101.1','U101.14','U101.13','U102.2','U102.1'],level=52,label=True)
    d.put('R116',145,47)
    d.bus(['U101.2','R116.2'],level=52)
    d.heading(8,60,'Current thresholds / about +/-50 A')
    d.divider('R110','R111','C110',18,67)
    d.divider('R112','R113','C111',43,67)
    d.put('U101',30,91,unit=5);d.decap('C113',43,91)
    d.put('U102',68,91,unit=5);d.decap('C114',81,91)
    d.note(91,91,'Board protection only.\nUse lower motor limits.\nOEM motor: 0.75 A.',1.1)
    d.heading(74,60,'Bus window / about 10.5-33 V')
    d.put('U102',82,69,unit=4);d.put('U102',108,69,unit=3)
    d.put('R117',126,66)
    d.bus(['U102.14','U102.13','R117.2'],level=80,label=True)
    d.divider('R114','R115','C112',142,68)
    d.field('C112',146,82)


def analog_inputs(d):
    d.heading(8,17,'Analog controls / 0-5 V input')
    for i in range(2):
        x=10+110*i;n=850+5*i;j='J'+str(801+i)
        d.put(j,x+5,30);d.put('R'+str(n),x+27,33,90)
        d.put('R'+str(n+1),x+42,40);d.put('C'+str(n),x+55,40);d.put('D'+str(n),x+30,48,90)
        plus,minus,out=[(3,2,1),(5,6,7)][i]
        d.put('U803',x+69,34,unit=i+1)
        d.bus(['R'+str(n)+'.2','R'+str(n+1)+'.1','C'+str(n)+'.1','U803.'+str(plus)],level=33)
        d.labels.append((d.net('U803.'+str(plus)),xy(x+58,33),'right'))
        d.wire('D'+str(n)+'.3',(x+37,48),(x+37,33),'R'+str(n+1)+'.1')
        d.wire('U803.'+str(minus),(x+64,35),(x+64,42),(x+75,42),(x+75,34),'U803.'+str(out))
        d.labels.append((d.net('U803.'+str(out)),xy(x+73,42),'right'))
        r='R'+str(n+2);cap='C'+str(n+2);di='D'+str(n+2)
        d.put(r,x+80,34,90);d.put(cap,x+88,40);d.put(di,x+17,42,90)
        d.wire('U803.'+str(out),r+'.1')
        d.bus([r+'.2',cap+'.1'],level=34,label=True)
        d.bus([di+'.1','R'+str(n)+'.1'],level=33)
        d.labels.append((d.net(di+'.1'),xy(x+17,33),'right'))
    d.put('U803',53,58,unit=3);d.decap('C847',65,58)
    d.heading(8,63,'Digital controls / 3.3 or 5 V logic')
    d.put('J803',14,78);d.put('J804',14,99)
    for i,unit in enumerate([1,3,2]):
        x=42+50*i;y=84;n=865+3*i
        d.put('U802',x+18,y,unit=unit)
        d.put('R'+str(n),x,y,90);d.put('R'+str(n+1),x-10,y-9)
        d.put('C'+str(n),x+7,y+7);d.put('D'+str(n),x-11,y+8,90)
        d.wire('R'+str(n)+'.2','U802.'+str([1,3,6][i]),label=True)
        d.bus(['R'+str(n)+'.2','C'+str(n)+'.1'],level=y)
        d.bus(['R'+str(n)+'.1','R'+str(n+1)+'.2','D'+str(n)+'.1'],level=y,label=True)
    d.put('U802',179,84,unit=4);d.decap('C845',194,84)


def thermal(d):
    d.heading(8,113,'Temperature feedback')
    for i in range(4):
        x=[16,60,104,194][i];n=880+3*i
        d.put('R'+str(n),x,124);d.put('C'+str(n),x+13,137)
        if i<2:
            th='TH'+str(801+i);d.put(th,x,138)
            d.bus(['R'+str(n)+'.2','C'+str(n)+'.1',th+'.1'],level=131,label=True)
        else:
            j='J'+str(803+i);r='R'+str(n+1);di='D'+str(n)
            d.put(j,x+3,150);d.put(r,x-10,135,90);d.put(di,x+25,145,90)
            plus,minus,out=[(3,2,1),(5,6,7)][i-2]
            d.put('U804',x+30,132,unit=i-1)
            d.bus([r+'.2','R'+str(n)+'.2','C'+str(n)+'.1','U804.'+str(plus)],level=131)
            d.labels.append((d.net('U804.'+str(plus)),xy(x+21,131),'right'))
            d.wire(di+'.3',(x+22,145),(x+22,131),(x+13,131),'C'+str(n)+'.1')
            d.wire('U804.'+str(minus),(x+26,133),(x+26,139),(x+35,139),(x+35,132),'U804.'+str(out))
            d.labels.append((d.net('U804.'+str(out)),xy(x+34,139),'right'))
            rf='R'+str(n+2);cf='C'+str(n+2);df='D'+str(n+2)
            d.put(rf,x+40,132,90);d.put(cf,x+48,138);d.put(df,x-19,144,90)
            d.wire('U804.'+str(out),rf+'.1')
            d.bus([rf+'.2',cf+'.1'],level=132,label=True)
            d.bus([r+'.1',df+'.1'],level=135)
            d.labels.append((d.net(r+'.1'),xy(x-18,135),'right'))
    d.put('U804',280,137,unit=3);d.decap('C848',293,137)
    d.divider('R898','R899','C899',320,124)
    d.note(8,159,'TH801/TH802: 10k, B25/50=3380 K. External NTC conversion must subtract the 1k series resistor.\nExternal channels are buffered; configure their actual R/T curves before thermal-limit testing.')


def regen(d):
    d.heading(8,17,'Independent bus clamp / nominal 31.3 V on, 30.6 V off')
    d.put('U301',43,37)
    d.put('R301',13,25);d.put('R302',13,35);d.put('R303',13,46);d.put('C301',25,46)
    d.wire('R301.2','R302.1',label=True)
    d.bus(['R302.2','R303.1','C301.1','U301.4'],level=41,label=True)
    d.put('R304',54,51,90);d.put('R305',67,58,90);d.put('R306',62,27)
    d.put('C303',54,62);d.decap('C302',30,23)
    d.put('U308',26,62);d.decap('C313',13,65);d.put('C314',38,74)
    d.field('U308',32,54)
    d.wire('U308.5',(38,62),'C314.1',label=True)
    d.wire('U308.1',(42,63),(42,55),(54,55),'C303.1',label=True)
    d.put('Q302',70,70);d.put('R319',58,74)
    d.wire('R319.1',(58,70),'Q302.1',label=True)
    d.put('U302',93,35)
    d.field('U302',98,24)
    d.put('R307',105,34,90);d.put('R308',105,36,90)
    d.field('R307',101,29);d.field('R308',101,40)
    d.put('Q301',120,35);d.put('R309',114,44);d.put('R310',121,62)
    d.wire('U302.2','R307.1',label=True);d.wire('U302.3','R308.1',label=True)
    d.bus(['R307.2','R308.2','Q301.4','R309.1'],axis='v',level=112,label=True)
    d.wire('Q301.1','R310.1',label=True)
    d.bus(['R309.2','U302.4','Q301.1'],level=51,label=True)
    d.put('C304',83,47);d.put('C305',95,47)
    d.bus(['C304.2','C305.2','U302.4'],level=51)
    d.put('J301',150,25);d.put('D301',137,37,90)
    d.field('D301',140,30)
    d.bus(['Q301.5','D301.2','J301.2'],level=28,label=True)
    d.put('#FLG301',106,54)
    d.put('U303',151,63);d.decap('C306',136,65);d.put('TP301',166,63)
    d.wire('U303.1','TP301.1',label=True)
    d.note(8,80,'External dump resistor: 2-25 ohm; pulse/thermal rating required.\nChopper trip: about 20.8 A, power-cycle reset. Reference U308 stays bus-powered.')
    d.note(8,86,'U302 return is Kelvin-connected to the top of R310.\nDo not force a bench supply to sink regenerative current.')


def regen_safety(d):
    d.divider('R315','R316',None,192,29);d.divider('R317','R318',None,212,29)
    d.note(177,59,'5 V-to-3.3 V monitor dividers')
    d.put('R320',192,72,90);d.put('R321',201,80);d.put('C312',212,80)
    d.bus(['R320.2','R321.1','C312.1'],level=72,label=True)
    d.note(177,91,'Dump current: 36 mV/A to PA6 ADC2_IN3.\nUse a long regular ADC acquisition time.',1.1)
    d.heading(8,91,'Chopper overcurrent trip and power-cycle latch')
    d.put('U305',27,108);d.put('C308',13,120);d.decap('C309',13,99)
    d.put('R312',43,97)
    d.put('U304',67,108);d.decap('C307',62,92)
    d.put('D302',91,105,90);d.put('D303',102,105,90);d.put('R311',95,94)
    d.bus(['R311.2','D302.2','D303.2'],level=100,label=True)
    d.put('R313',52,122,90);d.put('C310',66,130)
    d.put('U306',87,122);d.put('U307',105,122)
    d.bus(['R313.2','C310.1','U306.2'],level=122,label=True)
    d.wire('U306.4','U307.1',label=True)
    d.put('R314',118,133);d.decap('C311',118,110)
    d.bus(['U307.5','R314.1'],axis='v',level=118,label=True)


def supervisor(d):
    d.heading(8,17,'Power-on reset and watchdog')
    d.put('U701',30,32);d.put('C702',16,43);d.decap('C701',13,26);d.put('R701',48,23)
    d.put('U702',83,32);d.put('R702',63,26);d.put('R703',101,24);d.put('R704',65,46);d.decap('C703',99,43)
    d.note(8,55,'Open-drain reset outputs share NRST through zero-ohm links.\nR504 on the MCU sheet provides the pull-up.',1.1)
    d.heading(148,17,'Service and hardware enable')
    d.put('JP704',161,31);d.put('R722',178,26)
    d.put('J703',160,53);d.put('R720',151,43);d.put('R721',170,56,90);d.put('C705',185,64)
    d.put('D704',157,66,90)
    d.bus(['D704.1','R721.1'],level=56,label=True)
    d.put('U710',201,56)
    d.bus(['R721.2','C705.1','U710.2'],level=56)
    d.labels.append((d.net('U710.2'),xy(180,56),'left'))
    d.note(148,77,'RUN 1-2 / SERVICE 2-3.\nSERVICE or a chopper fault forces\nboth driver-enable and bridge-arm paths off.')
    d.decap('C717',208,68);d.decap('C718',181,33)


def safety(d):
    d.heading(8,66,'Arm interlock / fault removal does not re-arm the bridge')
    d.put('U703',27,84);d.put('U711',60,84);d.put('U704',94,84);d.put('U705',131,83)
    d.wire('U703.4','U711.1',label=True)
    d.wire('U711.4',(78,84),'U704.1',label=True)
    d.wire('U704.4',(110,84),'U705.6',label=True)
    d.put('R705',112,73);d.put('R706',153,73)
    d.put('U706',183,102)
    for i in range(6):
        r='R'+str(710+i);x=195+5*i
        d.put(r,x,123)
        out=str([18,16,14,12,9,7][i]);pos=d.point('U706.'+out)
        d.wire('U706.'+out,(x,pos[1]/G),r+'.1',label=True)
    d.heading(8,106,'Driver wake / independent chopper request')
    d.put('U707',29,125);d.put('U712',63,125);d.put('U708',117,125)
    d.wire('U707.4','U712.1',label=True)
    d.put('R716',12,140)
    for ref,x,y in [('C711',42,72),('C712',78,72),('C713',135,71),('C714',207,90),
                    ('C715',44,114),('C716',108,114),
                    ('C719',66,72),('C720',76,114)]:d.decap(ref,x,y)
    d.heading(145,139,'MCU monitoring / series isolation')
    for i,ref in enumerate(['R707','R708','R709','R723','R724','R725']):
        d.put(ref,159+38*(i%2),150+12*(i//2),90)
    d.note(145,182,'Hardware fault and enable nodes are isolated from MCU GPIO drive.\nDisable UCPD dead-battery control before reading PB4.',1.1)


def prepare(c):
    for name in ['10_voltage_sensing','11_current_protection','12_gate_driver','13_usb_status','14_temperature','15_regen_safety','16_supervisor']:
        if name not in c.SHEETS:c.SHEETS.append(name)
    voltage={'U801','C840'}
    for n in [801,811,821,831]:
        voltage.update('R'+str(v) for v in range(n,n+4))
        voltage.update(['C'+str(n),'C'+str(n+1),'D'+str(n)])
    protection={'U101','U102',*['R'+str(n) for n in range(110,118)],*['C'+str(n) for n in range(110,115)]}
    driver={'U201','#FLG201',*['R'+str(n) for n in range(201,206)],*['C'+str(n) for n in range(201,208)]}
    usb={'J401','F401','U404','C413',*['R'+str(n) for n in range(411,417)],*['R'+str(n) for n in range(511,514)],*['D'+str(n) for n in range(511,514)],*['TP'+str(n) for n in range(401,405)],*['#FLG'+str(n) for n in range(401,404)]}
    temperatures={'TH801','TH802','J805','J806','U804','C848',*['R'+str(n) for n in range(880,900)],*['C'+str(n) for n in range(880,900)],*['D'+str(n) for n in range(880,900)]}
    regen_trip={*['U'+str(n) for n in range(304,308)],*['R'+str(n) for n in range(311,319)],
                *['C'+str(n) for n in range(307,313)],'R320','R321','D302','D303'}
    supervision={'U701','U702','U710','J703','JP704','D701','D702','D704','C705','C717','C718',
                 *['R'+str(n) for n in range(701,705)],*['R'+str(n) for n in range(720,723)],
                 *['C'+str(n) for n in range(701,704)]}
    for p in c.parts:
        if p['ref'] in voltage:p['sheet']='10_voltage_sensing'
        if p['ref'] in protection:p['sheet']='11_current_protection'
        if p['ref'] in driver:p['sheet']='12_gate_driver'
        if p['ref'] in usb:p['sheet']='13_usb_status'
        if p['ref'] in temperatures:p['sheet']='14_temperature'
        if p['ref'] in regen_trip:p['sheet']='15_regen_safety'
        if p['ref'] in supervision:p['sheet']='16_supervisor'


def render(c):
    prepare(c)
    replace_units(c)
    c.drawing_metrics={}
    output={}
    for name,title,paper,fn in PAGES:
        d=Drawing(c,name,title,paper);fn(d);output[name]=d.finish()
    return output


PAGES=[('01_dc_link','DC input and motor connections','A3',dc_link),
       ('02_bridge','Three-phase bridge and current sensing','A2',bridge),
       ('04_power_usb','Power supplies','A2',power_usb),
       ('05_mcu','MCU, reference and debug','A2',mcu),
       ('06_sensors','Hall and encoder interfaces','A2',sensors),
       ('07_io_can','CAN FD and UART','A3',communications),
       ('03_regen','Regenerative brake chopper','A2',regen),
       ('08_analog_inputs','Analog and digital controls','A2',analog_inputs),
       ('09_safety','Hardware bridge interlock','A2',safety),
       ('10_voltage_sensing','Bus and phase voltage sensing','A3',voltage_sensing),
       ('11_current_protection','Current and bus protection','A3',current_protection)]
PAGES.extend([('12_gate_driver','Gate driver and charge pump','A4',gate_driver),
              ('13_usb_status','USB and status indicators','A4',usb_status),
              ('14_temperature','Temperature and logic-rail feedback','A3',thermal),
              ('15_regen_safety','Brake protection and telemetry','A3',regen_safety),
              ('16_supervisor','Reset, watchdog and hardware enable','A3',supervisor)])
