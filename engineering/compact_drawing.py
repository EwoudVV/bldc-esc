import math

from kicad_sexpr import Atom as A, child, pins, tag


GRID = 1.27


def visible(node):
    return not any(isinstance(v, list) and v and v[0] == 'hide' and v[1] == 'yes'
                   for v in [*node, *(child(node, 'effects', [])[1:])])


def text_size(node):
    effects=child(node,'effects',[])
    font=child(effects,'font',[])
    size=child(font,'size',[None,1.15,1.15])
    value=node[2] if node[0]=='property' else node[1]
    rows=str(value).splitlines() or ['']
    return max(len(row) for row in rows)*float(size[1])*0.62+1.27, len(rows)*float(size[2])*1.5


def axis_map(intervals, gap, margin):
    ranges=[]
    for a,b in sorted((math.floor(a/GRID)*GRID,math.ceil(b/GRID)*GRID) for a,b in intervals):
        if ranges and a<=ranges[-1][1]:ranges[-1]=(ranges[-1][0],max(b,ranges[-1][1]))
        else:ranges.append((a,b))
    removed=[]
    for (_,a),(b,_) in zip(ranges,ranges[1:]):
        if b-a>gap:removed.append((a,b,b-a-gap))
    offset=margin-ranges[0][0]
    def translate(v):
        reduction=0
        for a,b,amount in removed:
            if v>=b:reduction+=amount
            elif v>a:reduction+=amount*(v-a)/(b-a)
        return round(round((v+offset-reduction)/GRID)*GRID,4)
    return translate, sum(x[2] for x in removed)


def compact(tree):
    library={n[1]:n for n in child(tree,'lib_symbols')[1:]}
    intervals=[[],[]]
    extents=[]
    def protect(x0,y0,x1,y1,pad=1.27):
        intervals[0].append((x0-pad,x1+pad));intervals[1].append((y0-pad,y1+pad))
        extents.append((x0,y0,x1,y1))
    for item in tree:
        if not isinstance(item,list) or not item:continue
        kind=item[0]
        if kind=='symbol':
            at=child(item,'at');x,y,a=map(float,at[1:]);rad=math.radians(a)
            lib=library[child(item,'lib_id')[1]];unit=int(child(item,'unit')[1])
            points=[(x-1.27,y-1.27),(x+1.27,y+1.27)]
            for p in pins(lib,unit):
                p_at=child(p,'at');px,py=map(float,p_at[1:3])
                points.append((x+px*math.cos(rad)-py*math.sin(rad),y-px*math.sin(rad)-py*math.cos(rad)))
            protect(min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points))
            for prop in item:
                if not isinstance(prop,list) or not prop or prop[0]!='property' or not visible(prop):continue
                px,py=map(float,child(prop,'at')[1:3]);w,h=text_size(prop)
                justify=child(child(prop,'effects',[]),'justify',[])
                left=px if 'left' in justify else px-w if 'right' in justify else px-w/2
                protect(left,py-h/2,left+w,py+h/2,pad=0.635)
        elif kind in ('label','global_label'):
            x,y=map(float,child(item,'at')[1:3]);w,h=text_size(item)
            justify=child(child(item,'effects',[]),'justify',[])
            left=x-w if 'right' in justify else x
            protect(left,y-h,left+w,y+0.635,pad=0.635)
        elif kind=='text':
            x,y=map(float,child(item,'at')[1:3]);w,h=text_size(item)
            # Notes reserve vertical space without forcing distant columns apart.
            intervals[1].append((y-h/2-1.27,y+h/2+1.27))
            extents.append((x,y-h/2,x+w,y+h/2))
        elif kind=='wire':
            a,b=[tuple(map(float,p[1:])) for p in child(item,'pts')[1:]]
            if a[0]==b[0]:intervals[0].append((a[0]-0.635,a[0]+0.635))
            if a[1]==b[1]:intervals[1].append((a[1]-0.635,a[1]+0.635))
    fx,dx=axis_map(intervals[0],2.54,12.7)
    fy,dy=axis_map(intervals[1],3.81,12.7)
    for item in tree:
        if not isinstance(item,list) or not item:continue
        if item[0] in ('symbol','label','global_label','junction','no_connect','text'):
            at=child(item,'at');at[1],at[2]=fx(float(at[1])),fy(float(at[2]))
            if item[0]=='text':at[1]=max(12.7,at[1]);at[2]=max(12.7,at[2])
            if item[0]=='symbol':
                for p in item:
                    if isinstance(p,list) and p and p[0]=='property':
                        at=child(p,'at');at[1],at[2]=fx(float(at[1])),fy(float(at[2]))
        elif item[0]=='wire':
            for point in child(item,'pts')[1:]:point[1],point[2]=fx(float(point[1])),fy(float(point[2]))
    # Choose a standard page from actual post-compaction objects and visible text.
    max_x=max(fx(e[2]) for e in extents);max_y=max(fy(e[3]) for e in extents)
    for item in tree:
        if isinstance(item,list) and item and item[0]=='text':
            x,y=map(float,child(item,'at')[1:3]);w,h=text_size(item)
            max_x=max(max_x,x+w);max_y=max(max_y,y+h/2)
    old_paper=child(tree,'paper')[1]
    paper='A2'
    for name,w,h in [('A4',297,210),('A3',420,297),('A2',594,420)]:
        if max_x<=w-12.7 and max_y<=h-25.4:
            paper=name;break
    child(tree,'paper')[1:]=[paper]
    return {'paper_before':old_paper,'paper_after':paper,'removed_x_mm':round(dx,2),
            'removed_y_mm':round(dy,2),'content_width_mm':round(max_x,2),'content_height_mm':round(max_y,2)}


def block_for(sheet,x,y,ref=''):
    x/=2.54;y/=2.54
    if sheet=='01_dc_link':return 'input' if y<61 else 'chassis' if x<78 else 'motor'
    if sheet=='02_bridge':return 'phase_a' if x<123 else 'phase_b' if x<165 else 'phase_c'
    if sheet=='12_gate_driver':return 'driver'
    if sheet=='13_usb_status':return 'usb' if x<96 else 'leds'
    if sheet=='03_regen':
        if y>=88:return 'trip'
        return 'control' if x<77 else 'power' if x<176 else 'monitors'
    if sheet=='04_power_usb':return 'buck' if x<96 else 'mux'
    if sheet=='05_mcu':return 'core' if x<88 else 'debug' if x>=171 else 'reference' if y<75 else 'eeprom'
    if sheet=='06_sensors':return 'hall' if x<82 else 'encoder'
    if sheet=='07_io_can':return 'can' if y<86 else 'uart'
    if sheet=='08_analog_inputs':
        if y<60:return 'throttle' if x<85 else 'aux'
        if y<110:
            return 'ports' if x<27 else 'rc' if x<76 else 'brake' if x<126 else 'direction' if x<172 else 'buffer_power'
        return 'bridge_ntc' if x<41 else 'pcb_ntc' if x<86 else 'motor_ntc' if x<133 else 'dump_ntc' if x<190 else 'rail_adc'
    if sheet=='09_safety':
        if ref=='R706':return 'arm'
        if y>=144:return 'bypass'
        if x>=160 and y>=80:return 'buffer'
        if x>=146 and y<80:return 'service'
        if y<60:return 'reset'
        if y<103:return 'arm'
        return 'wake'
    if sheet=='10_voltage_sensing':return 'power' if y>=94 else ('bus' if x<83 else 'phase_a') if y<60 else ('phase_b' if x<83 else 'phase_c')
    if sheet=='11_current_protection':return 'current' if y<56 else 'power' if y>=85 else 'thresholds' if x<70 else 'bus'
    raise ValueError(sheet)


PACKING={
    '01_dc_link':['col','input',['row','chassis','motor']],
    '02_bridge':['row','phase_a','phase_b','phase_c'],
    '12_gate_driver':'driver',
    '13_usb_status':['row','usb','leds'],
    '03_regen':['row',['col','control','monitors'],['col','power','trip']],
    '04_power_usb':['row','buck','mux'],
    '05_mcu':['row','core',['col','reference','eeprom'],'debug'],
    '06_sensors':['row','hall','encoder'],
    '07_io_can':['col','can','uart'],
    '08_analog_inputs':['col',['row','throttle','aux'],['row','ports','rc','brake','direction','buffer_power'],['row','bridge_ntc','pcb_ntc','motor_ntc','dump_ntc','rail_adc']],
    '09_safety':['row',['col','reset','arm','wake'],['col','service','buffer']],
    '10_voltage_sensing':['col',['row','bus','phase_a'],['row','phase_b','phase_c'],'power'],
    '11_current_protection':['col','current',['row','thresholds','bus'],'power'],
}


def compact_blocks(tree,sheet):
    from collections import Counter,defaultdict
    library={n[1]:n for n in child(tree,'lib_symbols')[1:]}
    objects=[n for n in tree if isinstance(n,list) and n and n[0] in ('symbol','wire','label','global_label','junction','no_connect','text')]
    parent=list(range(len(objects)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):parent[root(b)]=root(a)
    points=defaultdict(list);segments=[];votes={}
    for i,item in enumerate(objects):
        kind=item[0]
        if kind=='symbol':
            at=child(item,'at');x,y,a=map(float,at[1:]);rad=math.radians(a)
            ref=next(v[2] for v in item if isinstance(v,list) and v[0]=='property' and v[1]=='Reference')
            if not ref.startswith('#PWR'):votes[i]=block_for(sheet,x,y,ref)
            for pin in pins(library[child(item,'lib_id')[1]],int(child(item,'unit')[1])):
                p=child(pin,'at');px,py=map(float,p[1:3])
                pos=(round(x+px*math.cos(rad)-py*math.sin(rad),4),round(y-px*math.sin(rad)-py*math.cos(rad),4))
                points[pos].append(i)
        elif kind=='wire':
            pts=[tuple(map(float,n[1:])) for n in child(item,'pts')[1:]]
            segments.append((i,*pts))
            for pt in pts:points[pt].append(i)
        elif kind!='text':
            points[tuple(map(float,child(item,'at')[1:3]))].append(i)
    for ids in points.values():
        for i in ids[1:]:union(ids[0],i)
    for pos,ids in points.items():
        for i,a,b in segments:
            if min(a[0],b[0])<=pos[0]<=max(a[0],b[0]) and min(a[1],b[1])<=pos[1]<=max(a[1],b[1]) and (a[0]==b[0]==pos[0] or a[1]==b[1]==pos[1]):
                for j in ids:union(i,j)
    counts=defaultdict(Counter)
    for i,vote in votes.items():counts[root(i)][vote]+=1
    groups=defaultdict(list)
    title=None
    for i,item in enumerate(objects):
        if item[0]=='text':
            x,y=map(float,child(item,'at')[1:3])
            if y<25.4 and title is None:title=item;continue
            group=block_for(sheet,x,y)
        elif counts[root(i)]:group=counts[root(i)].most_common(1)[0][0]
        else:
            at=child(item,'at')
            if at is None:at=child(item,'pts')[1]
            group=block_for(sheet,float(at[1]),float(at[2]))
        groups[group].append(item)
    metrics={};sizes={}
    for key,items in groups.items():
        partial=tag('kicad_sch',tag('paper',child(tree,'paper')[1]),child(tree,'lib_symbols'),*items)
        metrics[key]=compact(partial)
        sizes[key]=(max(1,metrics[key]['content_width_mm']-12.7),max(1,metrics[key]['content_height_mm']-12.7))
    gap=5.08
    def size(node):
        if isinstance(node,str):return sizes.get(node,(0,0))
        dimensions=[size(v) for v in node[1:] if size(v)!=(0,0)]
        if not dimensions:return 0,0
        if node[0]=='row':return sum(v[0] for v in dimensions)+gap*(len(dimensions)-1),max(v[1] for v in dimensions)
        return max(v[0] for v in dimensions),sum(v[1] for v in dimensions)+gap*(len(dimensions)-1)
    def move_item(item,dx,dy):
        if item[0]=='wire':
            for p in child(item,'pts')[1:]:p[1]=round(p[1]+dx,4);p[2]=round(p[2]+dy,4)
        else:
            a=child(item,'at');a[1]=round(a[1]+dx,4);a[2]=round(a[2]+dy,4)
            if item[0]=='symbol':
                for prop in item:
                    if isinstance(prop,list) and prop and prop[0]=='property':
                        a=child(prop,'at');a[1]=round(a[1]+dx,4);a[2]=round(a[2]+dy,4)
    def arrange(node,x,y):
        if isinstance(node,str):
            dx=round(round((x-12.7)/GRID)*GRID,4);dy=round(round((y-12.7)/GRID)*GRID,4)
            for item in groups.get(node,[]):move_item(item,dx,dy)
            return
        for sub in node[1:]:
            w,h=size(sub)
            if not(w or h):continue
            arrange(sub,x,y)
            if node[0]=='row':x+=math.ceil(w/GRID)*GRID+gap
            else:y+=math.ceil(h/GRID)*GRID+gap
    layout=PACKING[sheet];w,h=size(layout)
    arrange(layout,12.7,27.94)
    if title:child(title,'at')[1:3]=[15.24,17.78]
    paper='A2';portrait=False
    for name,pw,ph,orientation in [('A4',297,210,False),('A4',210,297,True),('A3',420,297,False),('A3',297,420,True),('A2',594,420,False),('A2',420,594,True)]:
        if w+22.86<=pw and h+27.94+12.7<=ph:paper=name;portrait=orientation;break
    old=child(tree,'paper')[1];child(tree,'paper')[1:]=[paper,*([A('portrait')] if portrait else [])]
    return {'paper_before':old,'paper_after':paper+('_portrait' if portrait else ''),'content_width_mm':round(w,2),'content_height_mm':round(h,2),'blocks':metrics}
