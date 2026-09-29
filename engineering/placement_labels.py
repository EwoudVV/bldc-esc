import json
import math
from pathlib import Path

from capture import patch
from placement_geometry import ROOT,read_board,rotate

plan=json.loads((ROOT/'engineering/placement.json').read_text())
_,parts=read_board(ROOT/'bldc-esc.kicad_pcb')
out=plan['outline'];boxes={};through=[]
def intersects(a,b,margin=0):
    return a[0]<b[2]+margin and a[2]>b[0]-margin and a[1]<b[3]+margin and a[3]>b[1]-margin
for ref,p in plan['components'].items():
    b=parts[ref]['courtyard'];v=[rotate(x,y,p['angle']) for x in (b[0],b[2]) for y in (b[1],b[3])]
    boxes[ref]=(p['x']+min(x for x,y in v),p['y']+min(y for x,y in v),p['x']+max(x for x,y in v),p['y']+max(y for x,y in v))
    for pad in parts[ref]['pads']:
        if pad['type'] not in ('thru_hole','np_thru_hole'):continue
        x,y=rotate(pad['x'],pad['y'],p['angle']);x+=p['x'];y+=p['y']
        angle=p['angle']+pad['angle'];a=math.radians(angle)
        w=abs(math.cos(a))*pad['w']+abs(math.sin(a))*pad['h'];h=abs(math.sin(a))*pad['w']+abs(math.cos(a))*pad['h']
        through.append((x-w/2,y-h/2,x+w/2,y+h/2))
reserved_front=[(out[0],out[3]-2.1,out[2],out[3]),(out[2]-1.1,out[1]+58,out[2],out[1]+104)]
front=[];back=[];fallback=[]
order=sorted(plan['components'],key=lambda r:(0 if r.startswith(('J','U','Q','L','Y','SW','F')) else 1 if r in ['R214','R234','R254','R310'] else 2,r))
for ref in order:
    p=plan['components'][ref];b=boxes[ref];width=max(2,len(ref)*.8*.76+.2);height=1.10
    candidates=[]
    for angle in [0,90]:
        w,h=(width,height) if angle==0 else (height,width)
        for gap in [.75,1.25,1.75,2.25,3.0]:
            for x,y in [((b[0]+b[2])/2,b[1]-gap),((b[0]+b[2])/2,b[3]+gap),(b[0]-gap,(b[1]+b[3])/2),(b[2]+gap,(b[1]+b[3])/2)]:
                bb=(x-w/2,y-h/2,x+w/2,y+h/2)
                if bb[0]<out[0]+.5 or bb[1]<out[1]+.5 or bb[2]>out[2]-.5 or bb[3]>out[3]-.5:continue
                if any(intersects(bb,q,.12) for q in [*boxes.values(),*front,*reserved_front]):continue
                candidates.append((math.hypot(x-p['x'],y-p['y'])+.3*(angle!=0),x,y,angle,bb))
    if candidates:
        _,x,y,angle,bb=min(candidates);layer='F.SilkS';front.append(bb)
    else:
        # Back-side references retain identification when a printable front label will not fit.
        candidates=[]
        for angle in [p['angle']%180,(p['angle']+90)%180]:
            w,h=(width,height) if angle==0 else (height,width)
            for dx in [0,-1,1,-2,2,-3,3]:
                for dy in [0,-1,1,-2,2,-3,3]:
                    x,y=p['x']+dx,p['y']+dy;bb=(x-w/2,y-h/2,x+w/2,y+h/2)
                    if bb[0]<out[0]+.5 or bb[1]<out[1]+.5 or bb[2]>out[2]-.5 or bb[3]>out[3]-.5:continue
                    if any(intersects(bb,q,.35) for q in [*through,*back]):continue
                    candidates.append((abs(dx)+abs(dy)+.1*(angle!=p['angle']%180),x,y,angle,bb))
        if candidates:
            _,x,y,angle,bb=min(candidates);layer='B.SilkS';back.append(bb)
        else:
            x,y=p['x'],p['y'];angle=0;layer='F.Fab';fallback.append(ref)
    p.update(ref_x=round(x,4),ref_y=round(y,4),ref_angle=angle,ref_layer=layer)
plan['reference_fields']={'front_silk':len(front),'back_silk':len(back),'fab_only':fallback}
plan['legends']=[]
for ref,name in [('J702','UART'),('J601','HALL'),('J602','ENC'),('J803','RC'),('J801','THR'),('J802','AUX')]:
    p=plan['components'][ref]
    plan['legends'].append({'text':name,'x':p['x'],'y':out[3]-1,'angle':0,'size':.8})
for ref,name in [('J805','TEMP M'),('J806','TEMP R'),('J701','CAN'),('J804','BRK DIR')]:
    p=plan['components'][ref]
    plan['legends'].append({'text':name,'x':out[2]-.55,'y':p['y'],'angle':90,'size':.8})
plan['legends'].append({'text':'BLDC-ESC v1','x':out[0]+27,'y':out[1]+3.5,'angle':0,'size':1.2})
plan['legends'].append({'text':'12-30 V','x':out[0]+27,'y':out[1]+6.0,'angle':0,'size':.8})
print('*** Begin Patch\n'+patch('engineering/placement.json',json.dumps(plan,indent=2)+'\n')+'*** End Patch')
