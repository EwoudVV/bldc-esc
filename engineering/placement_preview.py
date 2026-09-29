import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon

from placement_geometry import ROOT,read_board,rotate

plan=json.loads((ROOT/'engineering/placement.json').read_text())
_,parts=read_board(ROOT/'bldc-esc.kicad_pcb')
fig,ax=plt.subplots(figsize=(14,13),dpi=180)
x0,y0,x1,y1=plan['outline'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc='#172b26',ec='#101c17',lw=2))
for ref,p in plan['components'].items():
    f=parts[ref];x,y,a=p['x'],p['y'],p['angle']
    b=f['courtyard'];poly=[rotate(xx,yy,a) for xx,yy in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]]
    ax.add_patch(Polygon([(x+px,y+py) for px,py in poly],fc='none',ec='#627268',lw=.35))
    for pad in f['pads']:
        if not pad['number'] or not any(layer.endswith('.Cu') for layer in pad['layers']):continue
        px,py=rotate(pad['x'],pad['y'],a);pa=a+pad['angle']
        points=[rotate(xx,yy,pa) for xx,yy in [(-pad['w']/2,-pad['h']/2),(pad['w']/2,-pad['h']/2),(pad['w']/2,pad['h']/2),(-pad['w']/2,pad['h']/2)]]
        net=pad['net'].split('/')[-1]
        color='#ccaa60' if net=='GND' else '#ed6b55' if net=='VBUS' else '#78bbdc' if net.startswith('PHASE_') else '#c6cabf'
        ax.add_patch(Polygon([(x+px+vx,y+py+vy) for vx,vy in points],fc=color,ec='#0e1915',lw=.2))
    ax.text(x,y,ref,ha='center',va='center',fontsize=3.5,color='white',weight='bold')
ax.set_xlim(x0-4,x1+4);ax.set_ylim(y1+4,y0-4);ax.set_aspect('equal')
ax.set_xlabel('mm');ax.set_ylabel('mm');ax.grid(alpha=.12)
ax.set_title('Placement candidate - unrouted',fontsize=12)
fig.tight_layout()
fig.savefig(ROOT/'work/placement-20260928/placement-preview.png')
