import re, json, os
from PIL import Image
import os as _os
ROOT=_os.environ.get('GAME_ROOT', _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
GV2=_os.environ.get('GV2_DIR', _os.path.join(ROOT, 'gamev2'))
SPRD=GV2+'/assets/sprites'

def parse_tileset(p):
    txt=open(p).read(); ext={}
    for m in re.finditer(r'\[ext_resource path="res://([^"]+)" type="Texture" id=(\d+)\]', txt):
        ext[int(m.group(2))]=ROOT+'/'+m.group(1)
    T={}
    for m in re.finditer(r'(\d+)/texture = ExtResource\( (\d+) \)', txt): T.setdefault(int(m.group(1)),{})['tex']=ext.get(int(m.group(2)))
    for m in re.finditer(r'(\d+)/region = Rect2\( ([\d.\-]+), ([\d.\-]+), ([\d.\-]+), ([\d.\-]+) \)', txt): T.setdefault(int(m.group(1)),{})['region']=tuple(float(x) for x in m.groups()[1:])
    for m in re.finditer(r'(\d+)/tile_mode = (\d+)', txt): T.setdefault(int(m.group(1)),{})['mode']=int(m.group(2))
    for m in re.finditer(r'(\d+)/autotile/tile_size = Vector2\( ([\d.]+), ([\d.]+) \)', txt):
        T.setdefault(int(m.group(1)),{})['ts']=(float(m.group(2)),float(m.group(3)))
    for m in re.finditer(r'(\d+)/name = "([^"]+)"', txt):
        T.setdefault(int(m.group(1)),{})['name']=m.group(2)
    return T

def decode(blob):
    ints=[int(x) for x in blob.replace('\n','').split(',') if x.strip()!='']
    out=[]
    for i in range(0,len(ints),3):
        p=ints[i]&0xFFFFFFFF; v=ints[i+1]&0xFFFFFFFF; a=ints[i+2]&0xFFFFFFFF
        x=p&0xFFFF; y=(p>>16)&0xFFFF
        if x>=0x8000:x-=0x10000
        if y>=0x8000:y-=0x10000
        out.append((x,y,v&0x1FFFFFFF,bool(v&0x20000000),bool(v&0x40000000),a&0xFFFF,(a>>16)&0xFFFF))
    return out

def parse_scene(p):
    txt=open(p).read(); tsmap={}
    for m in re.finditer(r'\[ext_resource path="res://([^"]+)" type="TileSet" id=(\d+)\]', txt): tsmap[int(m.group(2))]=ROOT+'/'+m.group(1)
    layers=[]
    for b in re.split(r'\n\[node ', txt):
        if 'type="TileMap"' not in b: continue
        name=re.search(r'name="([^"]+)"',b).group(1)
        tsid=re.search(r'tile_set = ExtResource\( (\d+) \)', b)
        td=re.search(r'tile_data = PoolIntArray\( ([^)]*) \)', b)
        if not td: continue
        layers.append((name,int(tsid.group(1)) if tsid else 1, decode(td.group(1))))
    return tsmap,layers

texcache={}
def gettex(p):
    if p not in texcache: texcache[p]=Image.open(p).convert('RGBA')
    return texcache[p]

def subtile(ts,tid,cx,cy,fh,fv):
    t=ts.get(tid)
    if not t or 'region' not in t or not t.get('tex'): return None
    rx,ry,rw,rh=t['region']; mode=t.get('mode',0)
    if mode in (1,2):
        tsz=t.get('ts',(32,32)); sw,sh=int(tsz[0]),int(tsz[1]); sx=int(rx+cx*sw); sy=int(ry+cy*sh)
    else: sx,sy,sw,sh=int(rx),int(ry),int(rw),int(rh)
    try: im=gettex(t['tex']).crop((sx,sy,sx+sw,sy+sh))
    except Exception: return None
    if fh: im=im.transpose(Image.FLIP_LEFT_RIGHT)
    if fv: im=im.transpose(Image.FLIP_TOP_BOTTOM)
    return im

# Rect + target room are parametrised via env vars so the SAME pipeline ports any
# district. Defaults = the garden (room "Tokyo", the start room).
ROOM=os.environ.get('PORT_ROOM','Tokyo')
ISSTART=os.environ.get('PORT_START','1')=='1'
_rect=os.environ.get('PORT_RECT')
if _rect: RX0,RX1,RY0,RY1=[int(v) for v in _rect.split(',')]
else: RX0,RX1,RY0,RY1=-60,-2,-62,-17
W=RX1-RX0+1; H=RY1-RY0+1
print(f'porting room={ROOM} start={ISSTART} rect X[{RX0}..{RX1}] Y[{RY0}..{RY1}] ({W}x{H})')
GMAP=[('floor','Floor',0,False),('overfloor','Over Floor',1,False),
      ('overworld-noncollidables','Non-Collidables',4,False),('julia-tmp','Julia',4,False),
      ('overworld-collidables','Collidables',5,True),('other-tmp','Other',6,False)]

tsmap,layers=parse_scene(ROOT+'/Scenes/tokyo/tokyo_outside.tscn')
tilesets={i:parse_tileset(p) for i,p in tsmap.items()}
byl={n:(t,c) for n,t,c in layers}

regtiles={}  # key -> (PIL, anchorX, anchorY)
KEYNAMES={}     # key -> human tile name (filled by regkey, consumed by the tileNames union)
_NAME_OWNER={}  # slug -> first (tsid,tid) that claimed it
import autotile as _at
_BM={}      # tsid -> {tid: {(cx,cy): mask}} from the tileset's autotile bitmasks
_ROLES={}   # (tsid,tid) -> {(cx,cy): role}
def _subrole(tsid,tid,cx,cy):
    if tsid not in _BM:
        p=tsmap.get(tsid)
        _BM[tsid]=_at.parse_bitmasks(p) if p else {}
    flags=_BM[tsid].get(tid)
    if not flags or (cx,cy) not in flags: return None
    if (tsid,tid) not in _ROLES: _ROLES[(tsid,tid)]=_at.subtile_roles(flags)
    return _ROLES[(tsid,tid)].get((cx,cy))
def regkey(tsid,tid,cx,cy,fh,fv):
    # Semantic sprite keys, so the PNG filename says what the tile IS:
    #   fixed tiles:      <godot-tile-name-slug>_<cx>_<cy>   (sakura-large-top_1_0)
    #   autotile pieces:  <slug>_<role>                       (gravel-autotile_edge-n)
    # where role comes from the Godot autotile bitmask (center / edge-* /
    # corner-* / inner-* ...). Unnamed tiles fall back to the old gk scheme; a
    # name reused by a different tile id gets a deterministic -<tsid>-<tid>
    # suffix. config_to_tiled.py inverts the role names into Tiled wang sets.
    nm=(tilesets.get(tsid,{}).get(tid,{}).get('name') or '').strip()
    base=re.sub(r'[^a-z0-9]+','-',nm.lower()).strip('-') if nm else f"gk{tsid}_{tid}"
    if nm:
        owner=_NAME_OWNER.setdefault(base,(tsid,tid))
        if owner!=(tsid,tid): base=f"{base}-{tsid}-{tid}"
    suffix=_subrole(tsid,tid,cx,cy) or f"{cx}_{cy}"
    key=f"{base}_{suffix}{'_h' if fh else ''}{'_v' if fv else ''}"
    if nm: KEYNAMES[key]=nm
    return key

GVDEF={'Floor':(0,False),'Over Floor':(1,False),'Water':(1,True),'Non-Collidables':(4,False),'Julia':(4,False),'Collidables':(5,True),'Other':(6,False),'Tops':(7,False)}

# --- De-overlap dense trees (broad, map-wide) -----------------------------
# The source crams trees into tight clusters so canopies pile up. Drop any
# tree whose canopy CENTER lands under an already-kept canopy (front trees
# kept), and drop that tree's trunk too. Spaced trees are untouched.
CANOPY_TIDS={33,31,86,87,88,91}   # sakura/tree tops + whole small sakura
TRUNK_TIDS={32,30,83,84,85}       # sakura/tree bases & base-shadows
# canopy tid -> its trunk tid, per what the SOURCE places directly below each
# canopy (91 = whole tree, no separate trunk). tree-3-top(86)->tree-3-base(85)
# and tree-1-top(88)->tree-1-base(83): these were previously swapped, which glued
# the foliage-heavy tree-1 base (83) under the tree-3 canopy and made it look like
# two stacked trees.
CANOPY_TRUNK={33:32, 31:30, 86:85, 87:84, 88:83}
def _dims(tid):
    r=tilesets.get(1,{}).get(tid,{}).get('region',(0,0,32,32)); return int(r[2])//32, int(r[3])//32
_canopies=[]
for _g,(_t,_cells) in byl.items():
    for (x,y,tid,*_r) in _cells:
        if tid in CANOPY_TIDS and RX0<=x<=RX1 and RY0<=y<=RY1:
            fw,fh=_dims(tid)
            foot=[(x+a,y+b) for a in range(fw) for b in range(fh)]
            _canopies.append((x,y,tid,fw,fh,foot,(x+fw//2,y+fh//2),y+fh))
_canopies.sort(key=lambda c:-c[7])  # front (largest feet) first
# Keep canopies whose centre isn't already under a kept canopy; drop the rest.
# Discard ALL source trunks and regenerate exactly one per kept canopy at the
# canopy's own base position, so every tree is a clean canopy+trunk (no orphan
# trunks, no floating canopies).
covered=set(); kept_canopies={}; gen_trunks=[]
for x,y,tid,fw,fh,foot,center,feet in _canopies:
    # Drop any canopy that overlaps an already-kept canopy at all (front trees,
    # i.e. larger feet, are kept first). Footprint-based, not just centre, so two
    # trees can never share a cell -> no same-depth z-fight where one tree's
    # trunk-half draws over another tree's canopy. Also reserve the trunk cell
    # below so a neighbour's canopy can't land on this tree's trunk.
    if any(c in covered for c in foot): continue
    tw,th=_dims(CANOPY_TRUNK[tid]) if tid in CANOPY_TRUNK else (1,1)
    trunkfoot=[(x+(fw-tw)//2+a, y+fh+b) for a in range(tw) for b in range(th)]
    if any(c in covered for c in trunkfoot): continue
    covered.update(foot); covered.update(trunkfoot); kept_canopies[(x,y)]=tid
    if tid in CANOPY_TRUNK:
        ttid=CANOPY_TRUNK[tid]; tw,th=_dims(ttid)
        gen_trunks.append((ttid, x+(fw-tw)//2, y+fh))
print('trees: kept', len(kept_canopies), 'canopies, regen', len(gen_trunks), 'trunks')

# Pagoda TOWER vs open pavilion: a 'pagoda-floor' sitting under 'red-pagoda-spacing'
# (the tower body) is the solid base of a CLOSED tower, not a walk-in pavilion floor.
red_spacing_cells=set()
for _g,(_t,_cells) in byl.items():
    for (x,y,tid,*_r) in _cells:
        if RX0<=x<=RX1 and RY0<=y<=RY1 and 'red-pagoda-spacing' in (tilesets.get(_t,{}).get(tid,{}).get('name') or '').lower():
            fw0,fh0=_dims(tid)
            for a in range(fw0):
                for b in range(fh0):
                    red_spacing_cells.add((x-RX0+a, y-RY0+b))

# A 'pagoda-floor' sitting directly under a 'pagoda-roof' is the porch/base of a
# CLOSED temple building (the temple-hallway complex over the pond), not a
# walk-through garden gazebo -> make both the roof body and the floor base solid.
pagoda_roof_cells=set()
for _g,(_t,_cells) in byl.items():
    for (x,y,tid,*_r) in _cells:
        if RX0<=x<=RX1 and RY0<=y<=RY1 and (tilesets.get(_t,{}).get(tid,{}).get('name') or '')=='pagoda-roof':
            fw0,fh0=_dims(tid)
            for a in range(fw0):
                for b in range(fh0):
                    pagoda_roof_cells.add((x-RX0+a, y-RY0+b))

# Hall-roof corners: in the SOURCE a transparent eave-curl (overworld-collidables)
# overlays a SOLID roof tile (overworld-noncollidables) in the same cell. gamev2
# has one tile per cell+layer, so the curl was overwriting the solid underlay,
# leaving the corner floating over the bare wall. Keep the SOLID underlay at these
# cells (the curl is decorative; solid matches the roof edge below it).
roofs_nc_cells=set()
for _g,(_t,_cells) in byl.items():
    if _g!='overworld-noncollidables': continue
    for (x,y,tid,*_r) in _cells:
        if RX0<=x<=RX1 and RY0<=y<=RY1 and (tilesets.get(_t,{}).get(tid,{}).get('name') or '')=='red-pagoda-roofs':
            roofs_nc_cells.add((x-RX0, y-RY0))

# Walkway cells = the brown-brick path floor. A big hall roof sitting OVER the
# walkway is a covered bridge -> walk UNDER it (no collision); over grey-brick
# hall body it's solid.
walkway_cells=set()
_ft,_fc=byl.get('floor',(1,[]))
for (x,y,tid,*_r) in _fc:
    if RX0<=x<=RX1 and RY0<=y<=RY1 and 'brown-brick' in (tilesets.get(_ft,{}).get(tid,{}).get('name') or '').lower():
        walkway_cells.add((x-RX0, y-RY0))

gv={}  # gamev2 layer name -> {"rx,ry": key}
collidable_cells=set()
floor_cells=set()
for gname,lname,z,coll in GMAP:
    if gname not in byl: continue
    tsid,cells=byl[gname]; ts=tilesets.get(tsid,{})
    for (x,y,tid,fh,fv,cx,cy) in cells:
        if not(RX0<=x<=RX1 and RY0<=y<=RY1): continue
        if tid in TRUNK_TIDS: continue                                   # source trunks dropped; regenerated below
        if tid in CANOPY_TIDS and kept_canopies.get((x,y)) != tid: continue  # overlapping/duplicate canopy dropped
        if (ts.get(tid,{}).get('name') or '') in ('block','block2','block3'): continue  # Godot editor zone/dimension markers (magenta placeholder squares from the 'other-tmp' layer) — never real game art
        im=subtile(ts,tid,cx,cy,fh,fv)
        if im is None: continue
        key=regkey(tsid,tid,cx,cy,fh,fv)
        if key not in regtiles:
            sw,sh=im.size
            regtiles[key]=(im.resize((sw*2,sh*2),Image.NEAREST),round(16.0/sw,4),round(16.0/sh,4))
        rx=x-RX0; ry=y-RY0
        nm=(ts.get(tid,{}).get('name') or '').lower()
        # Target gamev2 layer + collision, with per-object overrides.
        # --- Per-object collision + render-layer classification -------------
        # gamev2 ties render depth to the layer, so "walk-behind" upper parts
        # (canopies/heads/roofs/tips) go on a high Tops layer with no collision,
        # while the solid footprint of each object is authored explicitly.
        im2=regtiles[key][0]; fw=max(1,im2.size[0]//64); fh=max(1,im2.size[1]//64)
        # Skip a placeholder BUILDING that bleeds in from the neighbouring district:
        # its anchor (= visual top, since tiles extend DOWN) sits at this room's
        # bottom edge with more than half its body hanging below the rect. Its real
        # home is the adjacent room where the whole thing is visible (the Park
        # tokyo-tower poked up into the Palace plaza as a cut-off stub). Scoped to
        # 'placeholder' so the intentional south-edge fence-barriers border is kept.
        if 'placeholder' in nm and ry+fh//2>=H:
            continue
        full=[(rx+ax,ry+ay) for ax in range(fw) for ay in range(fh)]
        base1=[(rx+fw//2, ry+fh-1)]                       # single ground-contact cell
        botrow=[(rx+ax, ry+fh-1) for ax in range(fw)]     # whole bottom row
        posts=[(rx,ry+fh-1),(rx+fw-1,ry+fh-1)]            # left+right (walk-through gates)
        TOP = (('top' in nm and 'vending' not in nm and 'road' not in nm) or ('roof' in nm and 'wall' not in nm))  # 'road-edge-top' is ground; '*-wall-*-roof' is a solid wall, not an overhang
        tlayer='Collidables' if coll else lname
        collcells=[]
        toprow=[(rx+ax, ry) for ax in range(fw)]          # whole top row
        if 'vending' in nm:
            tlayer='Other'                                         # vending machine on its OWN layer (z6, above ground clutter) so a lantern/torii-post sharing the cell can't overwrite it and it draws OVER those posts (which sit on Collidables); Y-sorted so the player still stands in front
            if 'top' in nm: collcells=base1                        # machine body solid at its ground cell; base/front stays walkable so you stand flush in front
        elif 'lantern' in nm:
            if cy==1: tlayer='Collidables'; collcells=base1        # lantern POST/base subtiles (cy==1; blue+red, both _3_1 and _4_1): solid
            else: tlayer='Tops'                                    # lantern lamp head: walk-behind, no collision
        elif 'sign' in nm:
            tlayer='Tops'                                          # signage (konbini etc.): walk completely behind, no collision
        elif 'placeholder' in nm:
            tlayer='Collidables'; collcells=full                   # placeholder building: fully solid
        elif nm=='red-pagoda-roof':
            tlayer='Tops'                                          # pagoda tower roof: ALL solid except the spire (top-centre), which stays walk-behind
            collcells=[(rx+ax,ry+ay) for ax in range(fw) for ay in range(1,fh)]  # solid body; the whole TOP row (spire + eave tips) stays walk-behind
        elif nm in ('red-pagoda-roofs','red-small-pagoda-top'):
            if coll and (rx,ry) in roofs_nc_cells:
                continue                                           # corner cell: keep the SOLID noncollidables underlay already placed here; drop the floating eave-curl overlay (collision already authored by the underlay)
            tlayer='Tops'                                          # big central HALL roof: solid building...
            collcells=[] if (rx,ry) in walkway_cells else full     # ...but walk UNDER where it bridges the walkway (brown-brick path)
        elif 'red-pagoda-small' in nm:
            tlayer='Tops' if 'top' in nm else 'Collidables'        # small pagoda tower (base + top): fully solid
            collcells=full
        elif 'red-pagoda-spacing' in nm:
            collcells=full                                         # pagoda tower body: solid (renders on its own low layer)
        elif nm=='pagoda-roof':
            tlayer='Tops'                                          # temple pagoda-roof: walk-behind overhead...
            collcells=[(rx+ax,ry+ay) for ax in range(fw) for ay in range(1,fh)]  # ...but the building BODY below the spire is solid (a closed temple tower, not a walk-through gazebo)
        elif 'pagoda-floor' in nm:
            roof_above=any((rx+ax, ry-1) in pagoda_roof_cells for ax in range(fw))
            if any(c in red_spacing_cells for c in full):
                tlayer='Collidables'; collcells=full               # base of a CLOSED pagoda tower (Market): solid
            elif roof_above:
                tlayer='Over Floor'; collcells=full                # porch/base under a temple pagoda-roof (Tokyo): a closed building base — solid, but rendered low (it's a floor texture)
            else:
                tlayer='Over Floor'                                # open pavilion floor (garden): walkable
        elif 'building-roof' in nm:
            tlayer='Tops'                                          # building roof: solid except its top row (walk behind the peak)
            collcells=[(rx+ax,ry+ay) for ax in range(fw) for ay in range(1,fh)]
        elif any(w in nm for w in ('building-tier','building-rafter','building-entrance')):
            tlayer='Collidables'; collcells=full                   # building body: fully solid
        elif coll and 'temple-hallway' in nm:
            tlayer='Tops'; collcells=full                          # temple building (roof+walls+doors): walk-behind roof; FULL footprint solid so you can't walk onto/around-into it
        elif 'wall' in nm and 'roof' in nm:
            tlayer='Collidables'; collcells=full                   # side-wall segment: solid barrier ('roof' in the name is the wall cap, NOT a walk-under overhang)
        elif coll and 'wall-gate' in nm:
            tlayer='Tops'                                          # blue-wall-gate is a walk-UNDER gateway ARCH: its blue span is a roof that must draw OVER the central path + the player (not flat under it); opening stays walkable (no collision)
        elif coll and ('moat' in nm or 'pond' in nm):
            tlayer='Water'; collcells=full                         # water: render low (overhangs draw over it), solid
        elif TOP:
            tlayer='Tops'                                          # canopy/head/roof/tip: walk-behind, no collision
        elif coll and 'kirin-statue' in nm:
            tlayer='Tops'; collcells=botrow                        # big kirin pedestal: base row solid, walk behind the body
        elif coll and 'fox-statue' in nm:
            tlayer='Collidables'; collcells=toprow                 # fox: the figure (upper) blocks; lower is walkable so you stand IN FRONT of it
        elif coll and 'sakura-small' in nm and 'base' not in nm:
            tlayer='Tops'; collcells=base1                         # whole small cherry tree (one tile): walk-behind, single trunk base
        elif coll and any(w in nm for w in ('tree-1-base','tree-2-base','tree-3-base')):
            tlayer='Collidables'; collcells=base1                  # tree trunk/shadow: render BELOW the canopy (Tops), single base cell
        elif coll and 'shrine-building' in nm:
            tlayer='Collidables'                                   # feet depth so the player on the steps draws in front, not under the staircase
            _cx=rx+fw//2                                           # central doorway column
            collcells=[(rx+ax, ry+ay) for ax in range(fw) for ay in range(fh-1)
                       if not (rx+ax==_cx and ay>=fh-3)]           # body solid EXCEPT the central door+stairs (centre col, bottom 2 body rows) -> a walkable passage up to the door (used as a hidden portal)
        elif coll and 'shrine-walls' in nm:
            tlayer='Collidables'
            collcells=[] if (cx==2 and cy==2) else base1           # the _2_2 subtile is the DOOR opening -> walkable (hidden portal); other segments are solid wall
        elif coll and 'torii' in nm and 'feet' in nm:
            tlayer='Collidables'; collcells=posts                  # torii FEET are ground-level posts: Y-sort (Collidables) so props/player standing in FRONT draw over them, instead of the posts always-on-top hiding e.g. the vending machines parked at their base. (The torii-*top* beam stays a walk-under overhead on Tops.) Walk through; only the posts are solid
        elif coll and 'bell-closed' in nm:
            tlayer='Collidables'; collcells=full                   # "closed bell" is actually a solid 2x2 hut/building -> fully solid
        elif coll and 'bell-blue-baseless' in nm:
            tlayer='Collidables'                                   # bell: solid body, collision shifted up 1 (walk in front, not behind)
            collcells=[(rx+ax, ry+ay-1) for ax in range(fw) for ay in range(fh)]
        elif coll and any(w in nm for w in ('shrub','platform')):
            tlayer='Collidables'; collcells=full                   # squat solid masses (bushes, platforms): no walk-behind
        elif coll:
            tlayer='Collidables'; collcells=base1                  # walls/fences/lamps/corners: solid at base cell (keeps gates/gaps open)
        gv.setdefault(tlayer,{})[f"{rx},{ry}"]=key
        if gname=='floor': floor_cells.add((rx,ry))
        for (cx,cy) in collcells:
            if 0<=cx<W and 0<=cy<H: collidable_cells.add((cx,cy))

# Regenerate one trunk per kept canopy, exactly at the canopy's base position.
ts1=tilesets.get(1,{})
for ttid,tx,ty in gen_trunks:
    if not(RX0<=tx<=RX1 and RY0<=ty<=RY1): continue
    im=subtile(ts1,ttid,0,0,False,False)
    if im is None: continue
    key=regkey(1,ttid,0,0,False,False)
    if key not in regtiles:
        sw,sh=im.size; regtiles[key]=(im.resize((sw*2,sh*2),Image.NEAREST),round(16.0/sw,4),round(16.0/sh,4))
    rx,ry=tx-RX0, ty-RY0
    gv.setdefault('Collidables',{})[f"{rx},{ry}"]=key
    im2=regtiles[key][0]; fw2=max(1,im2.size[0]//64); fh2=max(1,im2.size[1]//64)
    # Solidify the WHOLE trunk footprint. A single bottom-centre cell (rx+fw//2,
    # ry+fh-1) lands off-centre + on the lowest row for multi-cell trunks (e.g.
    # the 2x2 tree-1/2/3 bases), which can fall on the moat edge and leave the
    # visible trunk walkable. Trees are de-overlapped/spaced, so a full base
    # block won't seal paths.
    for ax in range(fw2):
        for ay in range(fh2):
            if 0<=rx+ax<W and 0<=ry+ay<H: collidable_cells.add((rx+ax, ry+ay))

# Fill floor holes so there are no black gaps at the rect edges: propagate the
# nearest floor tile into any empty cell (a few passes covers the thin border).
floorL=gv.setdefault('Floor',{})
for _ in range(8):
    changed=False
    for y in range(H):
        for x in range(W):
            k=f'{x},{y}'
            if k in floorL: continue
            for nx,ny in ((x,y+1),(x,y-1),(x+1,y),(x-1,y)):
                nk=f'{nx},{ny}'
                if nk in floorL:
                    floorL[k]=floorL[nk]; changed=True; break
    if not changed: break
holes=[1 for y in range(H) for x in range(W) if f'{x},{y}' not in floorL]
print('floor holes remaining:', len(holes))

# Assemble visible layers in z order. Render and collision are fully
# decoupled: every visible layer is collision=false, and a single Colliders
# layer holds exactly the authored solid cells (so collision == collcells).
out_layers=[]
for lname in ['Floor','Over Floor','Water','Non-Collidables','Julia','Collidables','Other','Tops']:
    if gv.get(lname):
        z,_=GVDEF[lname]
        out_layers.append({'name':lname,'z':z,'collision':False,'tiles':gv[lname]})

blank={f"{cx},{cy}":'gk_blank' for (cx,cy) in collidable_cells}
if blank:
    out_layers.append({'name':'Colliders','z':5,'collision':True,'tiles':blank})
print('collider cells:',len(blank))

# save PNGs
os.makedirs(SPRD,exist_ok=True)
for key,(im,ax,ay) in regtiles.items():
    im.save(f"{SPRD}/{key}.png")
print('unique tiles/PNGs:',len(regtiles))
print('layers:',[(l['name'],len(l['tiles'])) for l in out_layers])

# player start: walkable floor cell near bottom-center entrance
startx,starty=None,None
cx0=W//2
for ry in range(H-1,-1,-1):
    for dx in range(0,8):
        for sx in (cx0+dx,cx0-dx):
            if (sx,ry) in floor_cells and (sx,ry) not in collidable_cells:
                # also ensure a couple cells above are walkable (room to move)
                if (sx,ry-1) in floor_cells and (sx,ry-1) not in collidable_cells:
                    startx,starty=sx,ry; break
        if startx is not None: break
    if startx is not None: break
print('player start (rect):',startx,starty)

# build config from existing — MERGE this room in, keep the others intact.
cfg=json.load(open(GV2+'/config.json'))
# sprite metadata: keep everything already there (other rooms' tiles, character
# sprites) and ADD this room's sliced tiles (shared keys just overwrite with same).
newmeta={k:v for k,v in cfg.get('spriteMetadata',{}).items() if not re.match(r'^tile_',k) and k not in ('tile_dirt','tile_pavement')}
for key,(im,ax,ay) in regtiles.items():
    newmeta[key]={'frameCount':1,'anchorX':ax,'anchorY':ay}
newmeta['gk_blank']={'frameCount':1}                         # transparent collider (was a post-port patch)
cfg['spriteMetadata']=newmeta
# Human-readable source name per sliced tile, for the debug inspector (union).
tileNames=dict(cfg.get('tileNames',{}))
for key in regtiles:
    nm=KEYNAMES.get(key)
    if nm: tileNames[key]=nm
cfg['tileNames']=tileNames
# Tall buildings: lower render depth ~1 row so the player stays visible climbing
# the steps/stairs and only disappears IN the doorway (shrine = a walk-in gateway).
for key,nm in tileNames.items():
    if nm=='shrine-building' and key in newmeta:
        newmeta[key]['depthBias']=-10
cfg['game']['title']='game.devhou.se'
# Per-room size + explicit full-rect boundary (so each room sizes its own camera
# + movement bounds; rooms can differ in size).
room_obj={'name':ROOM,'worldWidth':W*64,'worldHeight':H*64,
          'boundary':[[0,0],[W,0],[W,H],[0,H]],
          'npcs':[],'objects':[],'transporters':[],'layers':out_layers}
# preserve any hand-added transporters/npcs/objects already on this room
prev=cfg.get('rooms',{}).get(ROOM,{})
for k in ('transporters','npcs','objects'):
    if prev.get(k): room_obj[k]=prev[k]
cfg.setdefault('rooms',{})[ROOM]=room_obj
if ISSTART:
    cfg['game']['worldWidth']=W*64; cfg['game']['worldHeight']=H*64
    # Preserve a hand-tuned spawn for this start room across re-ports; only
    # auto-place (bottom-centre walkable cell) when the room wasn't already the
    # start room with a spawn set. (Read the prior startRoom BEFORE overwriting.)
    p=cfg.setdefault('player',{})
    keep_spawn=(p.get('startRoom')==ROOM and p.get('startX') is not None)
    p['startRoom']=ROOM
    if not keep_spawn:
        p['startX']=startx; p['startY']=starty
# ---- Encode config to v2: tile palette + deterministic output --------------
# Decode any rooms already stored in v2 back to tile-key strings so the whole
# config is uniform, then re-encode every room against an APPEND-ONLY palette
# (existing indices never move => a re-port with no change is a byte-identical
# file, and a real change diffs only the affected cells).
prior_palette=list(cfg.get('tilePalette',[]))
if prior_palette:
    for r in cfg.get('rooms',{}).values():
        for L in r.get('layers',[]):
            t=L.get('tiles',{})
            if t and isinstance(next(iter(t.values())),int):
                L['tiles']={xy:prior_palette[i] for xy,i in t.items()}
used=set()
for r in cfg.get('rooms',{}).values():
    for L in r.get('layers',[]):
        used.update(L.get('tiles',{}).values())
palette=prior_palette+sorted(used-set(prior_palette))         # append-only -> stable indices
pidx={k:i for i,k in enumerate(palette)}
for r in cfg.get('rooms',{}).values():
    for L in r.get('layers',[]):
        L['tiles']={xy:pidx[k] for xy,k in L.get('tiles',{}).items()}
cfg['version']=2
cfg['tilePalette']=palette
json.dump(cfg,open(GV2+'/config.json','w'),sort_keys=True,indent=2,ensure_ascii=False)
print(f'room {ROOM}: {W}x{H} cells -> {W*64}x{H*64}px; rooms now: {list(cfg["rooms"].keys())}; palette={len(palette)}')
print('config written')
