#!/usr/bin/env python3
"""
config_to_tiled.py — generate a Tiled .tmj from ONE gamev2 config.json room.

This is the "seeder": it expresses an existing room as a standard, editable
Tiled map so you can author in Tiled instead of the bespoke config.json.

Modeling (the natural Tiled mapping for gamev2's data):
  - flat 1x1 tiles (floor/path/water/colliders)  -> Tiled TILE layers (paintable)
  - multi-cell sprites (trees/statues/buildings)  -> Tiled OBJECT layers as
    tile-objects (placed by position, sized to the image)
  - transporters + boundary + world size          -> a 'Meta' object layer / map props
Each layer carries its gamev2 z + collision as custom properties, and the
tileset is an image-collection of the sprite PNGs (objectalignment=topleft so a
tile-object's top-left sits on its cell, matching how gamev2 anchors sprites).

TiledAdapter.js reads this back into the exact room shape RoomManager renders,
so the whole existing renderer (feet-based Y-sort included) is reused untouched.

Usage:  python3 tools/config_to_tiled.py [RoomName]   (default: Tokyo)
"""
import json, struct, os, sys, re, hashlib
import autotile

GS = 64

def png_size(path):
    with open(path, 'rb') as f:
        f.read(16)                      # 8 sig + 4 len + 4 'IHDR'
        return struct.unpack('>II', f.read(8))

def props(d):
    out = []
    for n, v in d.items():
        t = 'bool' if isinstance(v, bool) else 'int' if isinstance(v, int) else 'string'
        out.append({'name': n, 'type': t, 'value': v})
    return out

def main():
    room_name = sys.argv[1] if len(sys.argv) > 1 else 'Tokyo'
    cfg = json.load(open('config.json'))
    pal = cfg['tilePalette']
    keyof = lambda idx: pal[idx] if isinstance(idx, int) else idx
    room = cfg['rooms'][room_name]
    W = (room.get('worldWidth') or cfg['game']['worldWidth']) // GS
    H = (room.get('worldHeight') or cfg['game']['worldHeight']) // GS

    keys = sorted({keyof(idx) for L in room['layers'] for idx in L['tiles'].values()})
    sizes = {k: png_size(f'assets/sprites/{k}.png') for k in keys}
    kid = {k: i for i, k in enumerate(keys)}     # tile id within the tileset
    FIRST = 1                                     # firstgid

    tileset = {
        'firstgid': FIRST, 'name': 'gamev2', 'tilewidth': GS, 'tileheight': GS,
        'tilecount': len(keys), 'columns': 0, 'objectalignment': 'topleft',
        'grid': {'orientation': 'orthogonal', 'width': GS, 'height': GS},
        'tiles': [{'id': kid[k], 'image': f'../assets/sprites/{k}.png',
                   'imagewidth': sizes[k][0], 'imageheight': sizes[k][1]} for k in keys],
    }

    # Terrain painting: the autotile pieces carry their role in the key
    # (gravel-autotile_edge-n, ..._center, ..._corner-nw — from the Godot
    # bitmasks via doport). Invert the roles into one Tiled wang set per
    # family so the Terrain Brush places edges/corners automatically.
    ROLE_RE = re.compile(r'^(.+)_((?:center|single|edge|corner|inner|end)(?:-[a-z0-9]+)*)$')
    fams = {}
    for k in keys:
        m = ROLE_RE.match(k)
        wid = m and autotile.role_to_wangid(m.group(2))
        if wid: fams.setdefault(m.group(1), []).append((kid[k], wid))
    if fams:
        tileset['wangsets'] = [{
            'name': fam, 'type': 'mixed', 'tile': -1,
            'colors': [{'name': fam, 'tile': -1, 'probability': 1,
                        'color': '#' + hashlib.md5(fam.encode()).hexdigest()[:6]}],
            'wangtiles': [{'tileid': t, 'wangid': w} for t, w in sorted(tiles)],
        } for fam, tiles in sorted(fams.items())]

    layers = []
    lid = 1
    oid = 1
    for L in room['layers']:
        name, z, coll = L['name'], L['z'], bool(L['collision'])
        ones, multi = {}, []
        for xy, idx in L['tiles'].items():
            x, y = map(int, xy.split(','))
            k = keyof(idx); w, h = sizes[k]
            (ones.__setitem__((x, y), k) if (w <= GS and h <= GS)
             else multi.append((x, y, k, w, h)))
        if ones:
            data = [0] * (W * H)
            for (x, y), k in ones.items():
                if 0 <= x < W and 0 <= y < H:
                    data[y * W + x] = FIRST + kid[k]
            layers.append({'type': 'tilelayer', 'id': lid, 'name': name, 'width': W,
                'height': H, 'x': 0, 'y': 0, 'opacity': 1, 'visible': True, 'data': data,
                'properties': props({'gv2layer': name, 'z': z, 'collision': coll})})
            lid += 1
        if multi:
            objs = []
            for (x, y, k, w, h) in multi:
                objs.append({'id': oid, 'gid': FIRST + kid[k], 'name': k,
                    'x': x * GS, 'y': y * GS, 'width': w, 'height': h, 'visible': True})
                oid += 1
            layers.append({'type': 'objectgroup', 'id': lid, 'name': name + ' ·obj',
                'x': 0, 'y': 0, 'opacity': 1, 'visible': True, 'draworder': 'index',
                'objects': objs,
                'properties': props({'gv2layer': name, 'z': z, 'collision': coll})})
            lid += 1

    # Meta object layer: transporters (points) + boundary (polygon)
    meta = []
    for t in room.get('transporters', []):
        meta.append({'id': oid, 'name': 'transporter', 'point': True,
            'x': t['gridX'] * GS + GS / 2, 'y': t['gridY'] * GS + GS / 2,
            'width': 0, 'height': 0, 'visible': True,
            'properties': props({'kind': 'transporter', 'targetRoom': t.get('targetRoom', ''),
                'targetX': int(t.get('targetX', 0)), 'targetY': int(t.get('targetY', 0)),
                'hidden': bool(t.get('hidden', False))})})
        oid += 1
    bnd = room.get('boundary', [])
    if len(bnd) >= 3:
        ox, oy = bnd[0]
        meta.append({'id': oid, 'name': 'boundary', 'x': ox * GS, 'y': oy * GS,
            'polygon': [{'x': (px - ox) * GS, 'y': (py - oy) * GS} for px, py in bnd],
            'width': 0, 'height': 0, 'visible': True, 'properties': props({'kind': 'boundary'})})
        oid += 1
    layers.append({'type': 'objectgroup', 'id': lid, 'name': 'Meta', 'x': 0, 'y': 0,
        'opacity': 1, 'visible': True, 'draworder': 'index', 'objects': meta,
        'properties': props({'gv2meta': True})})
    lid += 1

    tmj = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0',
        'orientation': 'orthogonal', 'renderorder': 'right-down', 'width': W, 'height': H,
        'tilewidth': GS, 'tileheight': GS, 'infinite': False,
        'nextlayerid': lid, 'nextobjectid': oid,
        'properties': props({'gv2room': room_name,
            'gv2worldWidth': room.get('worldWidth') or W * GS,
            'gv2worldHeight': room.get('worldHeight') or H * GS}),
        'tilesets': [tileset], 'layers': layers}

    os.makedirs('tiled', exist_ok=True)
    out = f'tiled/{room_name.lower()}.tmj'
    json.dump(tmj, open(out, 'w'), indent=1)
    print(f'wrote {out}: {W}x{H} cells, {len(keys)} tiles, {len(layers)} Tiled layers')

if __name__ == '__main__':
    main()
