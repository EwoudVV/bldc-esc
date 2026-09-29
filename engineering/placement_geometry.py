import json
import math
from pathlib import Path

from kicad_sexpr import child, parse

ROOT=Path(__file__).resolve().parent.parent

def rotate(x,y,angle):
    a=math.radians(angle)
    return x*math.cos(a)+y*math.sin(a),-x*math.sin(a)+y*math.cos(a)

def ref(fp):
    return next(p[2] for p in fp if isinstance(p,list) and p[:2]==['property','Reference'])

def read_board(path):
    tree=parse(Path(path).read_text())
    output={}
    for fp in tree:
        if not isinstance(fp,list) or not fp or fp[0]!='footprint':continue
        at=child(fp,'at');a=float(at[3]) if len(at)>3 else 0
        pads=[];court=[];fab=[]
        for item in fp:
            if not isinstance(item,list) or not item:continue
            kind=item[0]
            layer=child(item,'layer',[None,''])[1]
            if kind=='pad':
                p=child(item,'at');sz=child(item,'size');net=child(item,'net')
                pads.append({'number':item[1],'type':item[2],'shape':item[3],'x':float(p[1]),'y':float(p[2]),
                    'w':float(sz[1]),'h':float(sz[2]),'angle':(float(p[3]) if len(p)>3 else 0)-a,
                    'net':net[-1] if net else '', 'layers':child(item,'layers')[1:],
                    'drill':child(item,'drill',[None])[1:]})
            elif kind.startswith('fp_') and layer in ('F.CrtYd','B.CrtYd','F.Fab','B.Fab'):
                target=court if layer.endswith('CrtYd') else fab
                if kind in ('fp_line','fp_rect'):
                    for key in ('start','end'):target.append(tuple(map(float,child(item,key)[1:3])))
                elif kind=='fp_circle':
                    cx,cy=map(float,child(item,'center')[1:3]);ex,ey=map(float,child(item,'end')[1:3]);r=math.hypot(ex-cx,ey-cy)
                    target.extend([(cx-r,cy-r),(cx+r,cy+r)])
                elif kind=='fp_arc':
                    for key in ('start','mid','end'):target.append(tuple(map(float,child(item,key)[1:3])))
                elif kind=='fp_poly':
                    target.extend(tuple(map(float,p[1:3])) for p in child(item,'pts')[1:])
        if not court:
            for p in pads:court.extend([(p['x']-p['w']/2-.25,p['y']-p['h']/2-.25),(p['x']+p['w']/2+.25,p['y']+p['h']/2+.25)])
        bbox=lambda pts:[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
        output[ref(fp)]={'footprint':fp[1],'x':float(at[1]),'y':float(at[2]),'angle':a,'pads':pads,
            'courtyard':bbox(court),'body':bbox(fab) if fab else bbox(court),
            'layer':child(fp,'layer')[1], 'uuid':child(fp,'uuid')[1]}
    return tree,output

if __name__=='__main__':
    import sys
    _,parts=read_board(sys.argv[1] if len(sys.argv)>1 else ROOT/'bldc-esc.kicad_pcb')
    selected=sys.argv[2:]
    if selected:print(json.dumps({r:parts[r] for r in selected},indent=2))
    else:
        from collections import Counter
        print(json.dumps({'parts':len(parts),'courtyard_area_mm2':sum((p['courtyard'][2]-p['courtyard'][0])*(p['courtyard'][3]-p['courtyard'][1]) for p in parts.values()),
            'packages':dict(Counter(p['footprint'] for p in parts.values()))},indent=2))
