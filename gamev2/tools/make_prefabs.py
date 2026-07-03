#!/usr/bin/env python3
"""make_prefabs.py — seed gamev2/tiled/prefabs/*.tmj, the object library.

Each prefab is an ordinary small Tiled map you can open and edit in Tiled:
sprites on object layers (tagged with the room layer they belong to), solid
cells painted with the visible collider-marker tile on a `Colliders` layer,
and doors as `kind=door` points on a `Meta` layer. prefab.py stamps these
into rooms; doors come back as cells the generator can wire transporters to.

Run from gamev2/:  python3 tools/make_prefabs.py
"""
import json, os, struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiled', 'prefabs')
GS = 64

def png_size(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16); return struct.unpack('>II', f.read(8))

def props(d):
    return [{'name': n, 'type': 'bool' if isinstance(v, bool) else 'int' if isinstance(v, int) else 'string', 'value': v}
            for n, v in d.items()]

Z = {'Floor': 0, 'Over Floor': 1, 'Water': 1, 'Non-Collidables': 4, 'Collidables': 5, 'Other': 6, 'Tops': 7}

# name -> dict(w, h, sprites=[(layer, dx, dy, key)], colliders=[(dx,dy)], doors=[(dx,dy)])
PREFABS = {
    'lantern-red':  dict(w=1, h=2, sprites=[('Tops', 0, 0, 'red-lanterns_6_3'), ('Collidables', 0, 1, 'red-lanterns_4_1')],
                         colliders=[(0, 1)], doors=[]),
    'lamp-blue':    dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'blue-lamp-post_0_0')], colliders=[(0, 0)], doors=[]),
    'sakura-large': dict(w=3, h=3, sprites=[('Tops', 0, 0, 'sakura-large-top_0_0'), ('Collidables', 1, 2, 'sakura-large-base_0_0')],
                         colliders=[(1, 2)], doors=[]),
    'sakura-small': dict(w=1, h=2, sprites=[('Tops', 0, 0, 'sakura-small_0_0')], colliders=[(0, 1)], doors=[]),
    'tree-green':   dict(w=2, h=3, sprites=[('Tops', 0, 0, 'tree-3-top_0_0'), ('Collidables', 0, 2, 'tree-3-base-shadow_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'shrub-large':  dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'shrub-large-circle_0_0')],
                         colliders=[(0, 0), (0, 1), (1, 0), (1, 1)], doors=[]),
    'shrub-small':  dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'shrub-small-circle_0_0')], colliders=[(0, 0)], doors=[]),
    'torii-red':    dict(w=6, h=5, sprites=[('Tops', 0, 0, 'torii-red-top_0_0'), ('Collidables', 1, 3, 'torii-red-feet_0_0')],
                         colliders=[(1, 3), (4, 3), (1, 4), (4, 4)], doors=[]),
    'shrine':       dict(w=3, h=6, sprites=[('Collidables', 0, 0, 'shrine-building_0_0')],
                         colliders=[(x, y) for x in range(3) for y in range(5) if (x, y) != (1, 4)], doors=[(1, 4)]),
    # roof(3) + a wall tier + entrance(1): without the tier the gable sits straight
    # on the door and grass shows through the "missing middle" of the facade.
    # house-blue's entrance-1 is a full 2-cell sliding door (192x128), so this
    # house is a row taller than the others and its door sits on the bottom row.
    'house-blue':   dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-blue_0_0'), ('Collidables', 0, 3, 'building-tier-blue_0_0'), ('Collidables', 0, 4, 'building-entrance-1_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'house-red':    dict(w=3, h=5, sprites=[('Tops', 0, 0, 'building-roof-red_0_0'), ('Collidables', 0, 3, 'building-tier-red_0_0'), ('Collidables', 0, 4, 'building-entrance-3_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (2, 3, 4) if (x, y) != (1, 4)], doors=[(1, 4)]),
    'house-black':  dict(w=3, h=5, sprites=[('Tops', 0, 0, 'building-roof-black_0_0'), ('Collidables', 0, 3, 'building-tier-black_0_0'), ('Collidables', 0, 4, 'building-entrance-2_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (2, 3, 4) if (x, y) != (1, 4)], doors=[(1, 4)]),
    'seven-eleven': dict(w=3, h=4, sprites=[('Collidables', 0, 0, 'seven-eleven_0_0')],
                         colliders=[(x, y) for x in range(3) for y in range(4) if (x, y) != (1, 3)], doors=[(1, 3)]),
    'sign-7-11':    dict(w=1, h=2, sprites=[('Tops', 0, 0, '7-11-sign-left_0_0')], colliders=[(0, 1)], doors=[]),
    'vending-white': dict(w=1, h=2, sprites=[('Other', 0, 0, 'white-vending-machine-top_0_0'), ('Other', 0, 1, 'white-vending-machine-bottom_0_0')],
                          colliders=[(0, 0)], doors=[]),
    'vending-red':  dict(w=1, h=2, sprites=[('Other', 0, 0, 'red-vending-machine-top_0_0'), ('Other', 0, 1, 'red-vending-machine-bottom_0_0')],
                         colliders=[(0, 0)], doors=[]),
    'bell-blue':    dict(w=2, h=4, sprites=[('Tops', 0, 0, 'blue-bell-top_0_0'), ('Collidables', 0, 2, 'bell-blue-baseless_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'fox-statue':   dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'fox-statue-base-1_0_0')], colliders=[(0, 1)], doors=[]),
    'pagoda-small': dict(w=2, h=4, sprites=[('Collidables', 0, 0, 'red-pagoda-small-base_0_0'), ('Tops', 0, 1, 'red-pagoda-small-top_0_0')],
                         colliders=[(x, y) for x in (0, 1) for y in range(4)], doors=[]),
}


def write_prefab(name, spec):
    keys = sorted({k for (_, _, _, k) in spec['sprites']}) + ['collider-marker']
    sizes = {k: png_size(k) for k in keys}
    kid = {k: i for i, k in enumerate(keys)}
    tileset = {'firstgid': 1, 'name': 'gamev2', 'tilewidth': GS, 'tileheight': GS,
               'tilecount': len(keys), 'columns': 0, 'objectalignment': 'topleft',
               'grid': {'orientation': 'orthogonal', 'width': GS, 'height': GS},
               'tiles': [{'id': kid[k], 'image': f'../../assets/sprites/{k}.png',
                          'imagewidth': sizes[k][0], 'imageheight': sizes[k][1]} for k in keys]}
    layers, lid, oid = [], 1, 1
    bylayer = {}
    for (layer, dx, dy, k) in spec['sprites']:
        bylayer.setdefault(layer, []).append((dx, dy, k))
    for layer in sorted(bylayer, key=lambda l: Z[l]):
        objs = []
        for (dx, dy, k) in bylayer[layer]:
            objs.append({'id': oid, 'gid': 1 + kid[k], 'name': k, 'x': dx * GS, 'y': dy * GS,
                         'width': sizes[k][0], 'height': sizes[k][1], 'visible': True})
            oid += 1
        layers.append({'type': 'objectgroup', 'id': lid, 'name': layer + ' ·obj', 'x': 0, 'y': 0,
                       'opacity': 1, 'visible': True, 'draworder': 'index', 'objects': objs,
                       'properties': props({'gv2layer': layer, 'z': Z[layer], 'collision': False})})
        lid += 1
    data = [0] * (spec['w'] * spec['h'])
    for (dx, dy) in spec['colliders']:
        data[dy * spec['w'] + dx] = 1 + kid['collider-marker']
    layers.append({'type': 'tilelayer', 'id': lid, 'name': 'Colliders', 'width': spec['w'], 'height': spec['h'],
                   'x': 0, 'y': 0, 'opacity': 0.6, 'visible': True, 'data': data,
                   'properties': props({'gv2layer': 'Colliders', 'z': 5, 'collision': True})})
    lid += 1
    meta = [{'id': oid + i, 'name': 'door', 'point': True, 'x': dx * GS + GS / 2, 'y': dy * GS + GS / 2,
             'width': 0, 'height': 0, 'visible': True, 'properties': props({'kind': 'door'})}
            for i, (dx, dy) in enumerate(spec['doors'])]
    layers.append({'type': 'objectgroup', 'id': lid, 'name': 'Meta', 'x': 0, 'y': 0, 'opacity': 1,
                   'visible': True, 'draworder': 'index', 'objects': meta, 'properties': props({'gv2meta': True})})
    tmj = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal',
           'renderorder': 'right-down', 'width': spec['w'], 'height': spec['h'], 'tilewidth': GS,
           'tileheight': GS, 'infinite': False, 'nextlayerid': lid + 1, 'nextobjectid': oid + len(meta) + 1,
           'properties': props({'gv2prefab': name}), 'tilesets': [tileset], 'layers': layers}
    json.dump(tmj, open(os.path.join(OUT, name + '.tmj'), 'w'), indent=1)


os.makedirs(OUT, exist_ok=True)
for name, spec in PREFABS.items():
    write_prefab(name, spec)
print(f'wrote {len(PREFABS)} prefabs to tiled/prefabs/')
