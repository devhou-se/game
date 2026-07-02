import re, sys
from PIL import Image
import os as _os
ROOT=_os.environ.get('GAME_ROOT', _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))

def parse_tileset(tres_path):
    txt=open(tres_path).read()
    # ext resources: id -> texture path
    ext={}
    for m in re.finditer(r'\[ext_resource path="res://([^"]+)" type="Texture" id=(\d+)\]', txt):
        ext[int(m.group(2))]=ROOT+'/'+m.group(1)
    tiles={}
    # find all N/region lines etc. Collect by tile index
    for m in re.finditer(r'(\d+)/texture = ExtResource\( (\d+) \)', txt):
        tiles.setdefault(int(m.group(1)),{})['tex']=ext.get(int(m.group(2)))
    for m in re.finditer(r'(\d+)/region = Rect2\( ([\d.\-]+), ([\d.\-]+), ([\d.\-]+), ([\d.\-]+) \)', txt):
        i=int(m.group(1)); tiles.setdefault(i,{})['region']=tuple(float(x) for x in m.groups()[1:])
    for m in re.finditer(r'(\d+)/tile_mode = (\d+)', txt):
        tiles.setdefault(int(m.group(1)),{})['mode']=int(m.group(2))
    for m in re.finditer(r'(\d+)/autotile/tile_size = Vector2\( ([\d.]+), ([\d.]+) \)', txt):
        i=int(m.group(1)); tiles.setdefault(i,{})['ts']=(float(m.group(2)),float(m.group(3)))
    for m in re.finditer(r'(\d+)/tex_offset = Vector2\( ([\d.\-]+), ([\d.\-]+) \)', txt):
        i=int(m.group(1)); tiles.setdefault(i,{})['off']=(float(m.group(2)),float(m.group(3)))
    return tiles

def decode_cells(blob):
    ints=[int(x) for x in blob.replace('\n','').split(',') if x.strip()!='']
    cells=[]
    for i in range(0,len(ints),3):
        p=ints[i]&0xFFFFFFFF; v=ints[i+1]&0xFFFFFFFF; a=ints[i+2]&0xFFFFFFFF
        x=p&0xFFFF; y=(p>>16)&0xFFFF
        if x>=0x8000: x-=0x10000
        if y>=0x8000: y-=0x10000
        tid=v&0x1FFFFFFF
        fh=bool(v&0x20000000); fv=bool(v&0x40000000); tr=bool(v&0x80000000)
        cx=a&0xFFFF; cy=(a>>16)&0xFFFF
        cells.append((x,y,tid,fh,fv,tr,cx,cy))
    return cells

def parse_scene(tscn_path):
    txt=open(tscn_path).read()
    # ext id -> tileset path
    tsmap={}
    for m in re.finditer(r'\[ext_resource path="res://([^"]+)" type="TileSet" id=(\d+)\]', txt):
        tsmap[int(m.group(2))]=ROOT+'/'+m.group(1)
    layers=[]
    # split into node blocks
    blocks=re.split(r'\n\[node ', txt)
    for b in blocks:
        if 'type="TileMap"' not in b: continue
        name=re.search(r'name="([^"]+)"', b).group(1)
        tsid=re.search(r'tile_set = ExtResource\( (\d+) \)', b)
        td=re.search(r'tile_data = PoolIntArray\( ([^)]*) \)', b)
        if not td: continue
        layers.append((name, int(tsid.group(1)) if tsid else None, decode_cells(td.group(1))))
    return tsmap, layers

texcache={}
def gettex(p):
    if p not in texcache: texcache[p]=Image.open(p).convert('RGBA')
    return texcache[p]

def render(tscn, out, layer_filter=None):
    tsmap, layers=parse_scene(tscn)
    tilesets={tid:parse_tileset(p) for tid,p in tsmap.items()}
    # bounds
    allc=[(x,y) for _,_,cells in layers for (x,y,*_ ) in cells]
    minx=min(c[0] for c in allc); maxx=max(c[0] for c in allc)
    miny=min(c[1] for c in allc); maxy=max(c[1] for c in allc)
    CS=32
    W=(maxx-minx+1)*CS; H=(maxy-miny+1)*CS
    print('layers:',[ (l[0],len(l[2])) for l in layers])
    print('bounds x',minx,maxx,'y',miny,maxy,'-> canvas',W,H)
    canvas=Image.new('RGBA',(W,H),(0,0,0,255))
    for name,tsid,cells in layers:
        if layer_filter and name not in layer_filter: continue
        ts=tilesets.get(tsid,{})
        for (x,y,tid,fh,fv,tr,cx,cy) in cells:
            t=ts.get(tid)
            if not t or 'region' not in t or not t.get('tex'): continue
            rx,ry,rw,rh=t['region']
            mode=t.get('mode',0)
            if mode in (1,2):
                ts_=t.get('ts',(CS,CS))
                sw,sh=int(ts_[0]),int(ts_[1])
                sx=int(rx+cx*sw); sy=int(ry+cy*sh)
            else:
                sx,sy,sw,sh=int(rx),int(ry),int(rw),int(rh)
            try:
                sub=gettex(t['tex']).crop((sx,sy,sx+sw,sy+sh))
            except Exception:
                continue
            if fh: sub=sub.transpose(Image.FLIP_LEFT_RIGHT)
            if fv: sub=sub.transpose(Image.FLIP_TOP_BOTTOM)
            # placement: cell top-left, tiles taller than cell extend upward
            px=(x-minx)*CS; py=(y-miny)*CS - (sh-CS)
            canvas.alpha_composite(sub,(px,py))
    canvas.convert('RGB').save(out)
    print('saved',out, canvas.size)

render(ROOT+'/Scenes/tokyo/tokyo_outside.tscn', '/Users/bailey/projects/game/.playwright-mcp/godot_tokyo.png')

def render_visual(tscn, out, scale=0.5):
    VIS={'floor','overfloor','overworld-collidables','julia-tmp','overworld-noncollidables','other-tmp'}
    tsmap, layers=parse_scene(tscn)
    tilesets={tid:parse_tileset(p) for tid,p in tsmap.items()}
    # bounds from floor only
    fc=[c for n,_,cells in layers if n=='floor' for c in cells]
    minx=min(c[0] for c in fc); maxx=max(c[0] for c in fc)
    miny=min(c[1] for c in fc); maxy=max(c[1] for c in fc)
    CS=32
    W=(maxx-minx+1)*CS; H=(maxy-miny+1)*CS
    print('floor bounds x',minx,maxx,'y',miny,maxy,'cells',(maxx-minx+1),'x',(maxy-miny+1))
    canvas=Image.new('RGBA',(W,H),(20,20,20,255))
    order=['floor','overfloor','overworld-noncollidables','julia-tmp','overworld-collidables','other-tmp']
    bylayer={n:(tsid,cells) for n,tsid,cells in layers}
    for name in order:
        if name not in bylayer: continue
        tsid,cells=bylayer[name]; ts=tilesets.get(tsid,{})
        for (x,y,tid,fh,fv,tr,cx,cy) in cells:
            if not(minx<=x<=maxx and miny<=y<=maxy): continue
            t=ts.get(tid)
            if not t or 'region' not in t or not t.get('tex'): continue
            rx,ry,rw,rh=t['region']; mode=t.get('mode',0)
            if mode in (1,2):
                ts_=t.get('ts',(CS,CS)); sw,sh=int(ts_[0]),int(ts_[1])
                sx=int(rx+cx*sw); sy=int(ry+cy*sh)
            else:
                sx,sy,sw,sh=int(rx),int(ry),int(rw),int(rh)
            try: sub=gettex(t['tex']).crop((sx,sy,sx+sw,sy+sh))
            except Exception: continue
            if fh: sub=sub.transpose(Image.FLIP_LEFT_RIGHT)
            if fv: sub=sub.transpose(Image.FLIP_TOP_BOTTOM)
            px=(x-minx)*CS; py=(y-miny)*CS-(sh-CS)
            canvas.alpha_composite(sub,(px,py))
    out_img=canvas.convert('RGB')
    if scale!=1: out_img=out_img.resize((int(W*scale),int(H*scale)),Image.LANCZOS)
    out_img.save(out); print('saved',out,out_img.size)

render_visual(ROOT+'/Scenes/tokyo/tokyo_outside.tscn','/Users/bailey/projects/game/.playwright-mcp/godot_tokyo_vis.png', scale=0.42)

# Osaka
render_visual(ROOT+'/Scenes/osaka/osaka_outside.tscn','/Users/bailey/projects/game/.playwright-mcp/godot_osaka_vis.png', scale=0.5)
# Full-res Tokyo for cropping zones
render_visual(ROOT+'/Scenes/tokyo/tokyo_outside.tscn','/Users/bailey/projects/game/.playwright-mcp/godot_tokyo_full.png', scale=1.0)
