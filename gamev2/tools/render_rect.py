import os
import sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render_godot.py')).read().split("render(ROOT")[0])
RX0,RX1,RY0,RY1=[int(a) for a in sys.argv[1:5]]
out=sys.argv[5]
tscn=ROOT+'/Scenes/tokyo/tokyo_outside.tscn'
tsmap,layers=parse_scene(tscn)
tilesets={tid:parse_tileset(p) for tid,p in tsmap.items()}
CS=32; W=(RX1-RX0+1)*CS; H=(RY1-RY0+1)*CS
canvas=Image.new('RGBA',(W,H),(20,20,20,255))
order=['floor','overfloor','overworld-noncollidables','julia-tmp','overworld-collidables','other-tmp']
bylayer={n:(tsid,cells) for n,tsid,cells in layers}
for name in order:
    if name not in bylayer: continue
    tsid,cells=bylayer[name]; ts=tilesets.get(tsid,{})
    for (x,y,tid,fh,fv,tr,cx,cy) in cells:
        if not(RX0<=x<=RX1 and RY0<=y<=RY1): continue
        t=ts.get(tid)
        if not t or 'region' not in t or not t.get('tex'): continue
        rx,ry,rw,rh=t['region']; mode=t.get('mode',0)
        if mode in (1,2):
            ts_=t.get('ts',(CS,CS)); sw,sh=int(ts_[0]),int(ts_[1]); sx=int(rx+cx*sw); sy=int(ry+cy*sh)
        else: sx,sy,sw,sh=int(rx),int(ry),int(rw),int(rh)
        try: sub=gettex(t['tex']).crop((sx,sy,sx+sw,sy+sh))
        except Exception: continue
        if fh: sub=sub.transpose(Image.FLIP_LEFT_RIGHT)
        if fv: sub=sub.transpose(Image.FLIP_TOP_BOTTOM)
        px=(x-RX0)*CS; py=(y-RY0)*CS-(sh-CS)
        canvas.alpha_composite(sub,(px,py))
canvas.convert('RGB').save(out); print('saved',out,canvas.size,'rect',RX0,RX1,RY0,RY1)
