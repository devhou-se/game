#!/usr/bin/env python3
"""
Port QA / pre-flight verification for the gamev2 Phaser world.

Reads gamev2/config.json (+ the sprite PNG sizes) and reconstructs the engine's
depth + collision rules, then flags the bug-classes we kept hitting by hand:

  ERROR  floor-hole               cell with no Floor tile  -> black gap
  ERROR  missing-collision        solid object (Collidables) with NO collider in its footprint
  ERROR  canopy-overlap           2+ tree canopies share a cell -> z-fight
  ERROR  trunk-over-canopy        a trunk draws over a canopy it overlaps
  ERROR  oob-collider             collider cell outside the world
  WARN   stray-collision          collider cell under no visible object (often a misplaced box)
  WARN   under-overhead           tall object on the overhead (Tops) layer whose base row is
                                  walkable -> player draws UNDER it (the "under the staircase" bug)
  WARN   ground-on-tops           big contiguous run of one tile on Tops -> probably flat ground
                                  misclassified as an overhang (the road-edge-top bug)
  WARN   floating-canopy          tree canopy with no trunk directly below it

Usage:  python3 qa_port.py [path/to/config.json] [--room Tokyo]
Exit code is non-zero if any ERROR is found, so it can gate a port.
"""
import json, sys, os
from collections import defaultdict, deque
from PIL import Image

import os as _os
GV2 = _os.environ.get('GV2_DIR', _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
GS = 64

def load(cfg_path):
    cfg = json.load(open(cfg_path))
    # v2: expand tile-palette indices back to tile-key strings
    pal = cfg.get('tilePalette')
    if cfg.get('version', 1) >= 2 and pal:
        for r in cfg.get('rooms', {}).values():
            for L in r.get('layers', []):
                L['tiles'] = {xy: pal[i] for xy, i in L.get('tiles', {}).items()}
    return cfg

_dimcache = {}
def dims(key):
    """sprite size in CELLS (w,h)."""
    if key in _dimcache: return _dimcache[key]
    p = os.path.join(GV2, 'assets', 'sprites', key + '.png')
    try:
        with Image.open(p) as im: w, h = im.size
        d = (max(1, round(w/GS)), max(1, round(h/GS)))
    except Exception:
        d = (1, 1)
    _dimcache[key] = d
    return d

def foot(x, y, key):
    w, h = dims(key)
    return [(x+a, y+b) for a in range(w) for b in range(h)], w, h

def depth_of(z, y, h):
    if z < 2: return -1000  # ground layers: fixed low
    feet = y + h
    return feet*10 + (11 if z >= 7 else 0)

def is_canopy(nm):
    return (nm.endswith('-top') and ('sakura' in nm or nm.startswith('tree-'))) or nm == 'sakura-small'
def is_trunk(nm):
    return ('base' in nm) and ('sakura' in nm or nm.startswith('tree-'))

def main():
    args = sys.argv[1:]
    room = 'Tokyo'
    if '--room' in args:
        i = args.index('--room'); room = args[i+1]; del args[i:i+2]
    cfg_path = next((a for a in args if not a.startswith('--')), GV2+'/config.json')
    cfg = load(cfg_path)
    tn = cfg.get('tileNames', {})
    nm = lambda k: tn.get(k, k)
    layers = cfg['rooms'][room]['layers']

    # index layers
    floor_cells = set()
    over_floor_cells = set()     # deliberate walkable interior floors (pavilions, paths-on-collidables)
    collider_cells = []          # list of (x,y)
    objects = []                 # visible standing objects: (layer_name, z, x, y, key, footprint, w, h)
    W = H = 0
    for L in layers:
        z = L.get('z', 0); coll = L.get('collision', False); lname = L['name']
        for pos, key in L.get('tiles', {}).items():
            x, y = map(int, pos.split(','))
            W = max(W, x+1); H = max(H, y+1)
            if lname == 'Floor': floor_cells.add((x, y))
            if lname == 'Over Floor':
                fpof, _, _ = foot(x, y, key); over_floor_cells.update(fpof)
            if coll:
                collider_cells.append((x, y)); continue
            if z >= 1 and lname != 'Floor':   # Water(1)+Over Floor(1)+Collidables(5)+Tops(7) = potential objects
                fp, w, h = foot(x, y, key)
                objects.append((lname, z, x, y, key, fp, w, h))
    collider_set = set(collider_cells)
    # cells with a transporter (intentionally walkable doors/portals) — never "missing collision"
    transporter_cells = {(t.get('gridX'), t.get('gridY')) for t in cfg['rooms'][room].get('transporters', [])}

    # reachable set: flood-fill from the player spawn over walkable, floored, in-boundary cells
    boundary = cfg['rooms'][room].get('boundary') or []
    def in_bounds_poly(x, y):
        if len(boundary) < 3: return True
        px, py = x+0.5, y+0.5; inside = False; n = len(boundary)
        for i in range(n):
            x1, y1 = boundary[i]; x2, y2 = boundary[(i+1) % n]
            if (y1 > py) != (y2 > py) and px < (x2-x1)*(py-y1)/(y2-y1)+x1: inside = not inside
        return inside
    pl = cfg.get('player', {})
    reachable = set()
    walkable = lambda nb: (0 <= nb[0] < W and 0 <= nb[1] < H and nb in floor_cells
                           and nb not in collider_set and in_bounds_poly(*nb))
    # Seed the flood at the room's spawn if valid for THIS room, else the first
    # walkable floor cell (non-start rooms are entered via a transporter).
    sx, sy = pl.get('startX', 0), pl.get('startY', 0)
    if not walkable((sx, sy)):
        sx, sy = next((c for c in sorted(floor_cells) if walkable(c)), (sx, sy))
    if walkable((sx, sy)):
        dq = deque([(sx, sy)]); reachable.add((sx, sy))
        while dq:
            cx, cy = dq.popleft()
            for nb in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                if nb not in reachable and walkable(nb):
                    reachable.add(nb); dq.append(nb)

    errors = defaultdict(list); warns = defaultdict(list)

    # 1. floor holes
    for y in range(H):
        for x in range(W):
            if (x, y) not in floor_cells: errors['floor-hole'].append((x, y))

    # 2. oob colliders
    for (x, y) in collider_set:
        if not (0 <= x < W and 0 <= y < H): errors['oob-collider'].append((x, y))

    # union of all object footprints (for stray-collision)
    covered = set()
    for (_l, _z, _x, _y, _k, fp, _w, _h) in objects: covered.update(fp)
    # bell shifts collision up 1 row -> allow one-row-up neighbours of any footprint
    covered_loose = set(covered) | {(cx, cy-1) for (cx, cy) in covered}

    # 3. stray collisions
    for (x, y) in sorted(collider_set):
        if (x, y) not in covered_loose: warns['stray-collision'].append((x, y))

    # 4. missing collision: a Collidables object with NO collider anywhere in its footprint
    for (lname, z, x, y, key, fp, w, h) in objects:
        if lname != 'Collidables': continue
        if any(c in transporter_cells for c in fp): continue   # door/portal tile: intentionally walkable
        if not any(c in collider_set for c in fp):
            warns['missing-collision'].append(f"{nm(key)}@{x},{y}") if False else errors['missing-collision'].append(f"{nm(key)} @{x},{y}")

    # 5. under-overhead: tall (h>=4) Tops object whose bottom row is REACHABLE + walkable.
    #    Suppress walk-in structures (an Over-Floor interior beneath = pavilion) and
    #    unreachable overheads (you can't actually stand under them).
    for (lname, z, x, y, key, fp, w, h) in objects:
        if z < 7 or h < 4: continue
        # pavilion: a deliberate walk-in floor under or just below the overhead -> not a bug
        if any(c in over_floor_cells for c in fp) or any((x+a, y+h) in over_floor_cells for a in range(w)): continue
        botrow = [(x+a, y+h-1) for a in range(w)]
        if any((c not in collider_set and c in reachable) for c in botrow):
            warns['under-overhead'].append(f"{nm(key)} @{x},{y} ({w}x{h})")

    # 6. ground-on-tops: large contiguous run of one key on Tops
    tops_cells = defaultdict(set)   # key -> set of anchor cells
    for (lname, z, x, y, key, fp, w, h) in objects:
        if z >= 7: tops_cells[key].add((x, y))
    for key, cells in tops_cells.items():
        seen = set()
        for c in cells:
            if c in seen: continue
            comp = []; dq = deque([c]); seen.add(c)
            while dq:
                cx, cy = dq.popleft(); comp.append((cx, cy))
                for nb in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                    if nb in cells and nb not in seen: seen.add(nb); dq.append(nb)
            if len(comp) > 15:
                warns['ground-on-tops'].append(f"{nm(key)} x{len(comp)} contiguous (e.g. @{comp[0][0]},{comp[0][1]})")

    # 7. tree checks
    canopies = [(x, y, key, fp, w, h) for (lname, z, x, y, key, fp, w, h) in objects if z >= 7 and is_canopy(nm(key))]
    trunks  = [(x, y, key, fp, w, h) for (lname, z, x, y, key, fp, w, h) in objects if lname == 'Collidables' and is_trunk(nm(key))]
    # canopy overlap
    cov = defaultdict(list)
    for (x, y, key, fp, w, h) in canopies:
        for c in fp: cov[c].append(f"{nm(key)}@{x},{y}")
    for c, lst in cov.items():
        if len(lst) > 1: errors['canopy-overlap'].append(f"{c[0]},{c[1]}: {' + '.join(sorted(set(lst)))}")
    # trunk over canopy
    for (tx, ty, tk, tfp, tw, th) in trunks:
        td = depth_of(5, ty, th)
        for (cx, cy, ck, cfp, cw, ch) in canopies:
            if set(tfp) & set(cfp):
                cd = depth_of(7, cy, ch)
                if td > cd:
                    errors['trunk-over-canopy'].append(f"{nm(tk)}@{tx},{ty}(d{td}) over {nm(ck)}@{cx},{cy}(d{cd})")
    # floating canopy (skip whole-tree sakura-small)
    trunk_anchor = {(x, y) for (x, y, key, fp, w, h) in trunks}
    trunk_cells = set()
    for (x, y, key, fp, w, h) in trunks: trunk_cells.update(fp)
    for (x, y, key, fp, w, h) in canopies:
        if nm(key) == 'sakura-small': continue   # fused trunk
        below = [(x+a, y+h) for a in range(w)]
        if not any(b in trunk_cells for b in below):
            warns['floating-canopy'].append(f"{nm(key)} @{x},{y}")

    # ---- report ----
    def show(d, tag):
        if not d: return 0
        n = 0
        for k, v in sorted(d.items()):
            n += len(v)
            print(f"  [{tag}] {k}: {len(v)}")
            for item in v[:8]:
                print(f"        {item}")
            if len(v) > 8: print(f"        ... +{len(v)-8} more")
        return n
    print(f"== Port QA: {cfg_path} room={room}  world {W}x{H} ==")
    print(f"   objects={len(objects)} colliders={len(collider_set)} floor={len(floor_cells)}")
    ne = show(errors, 'ERR')
    nw = show(warns, 'WARN')
    print(f"-- {ne} errors, {nw} warnings --")
    sys.exit(1 if ne else 0)

if __name__ == '__main__':
    main()
