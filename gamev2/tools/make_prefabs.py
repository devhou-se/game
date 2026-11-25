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

def building(w, h, door, roof=2, door_w=1):
    """A single-sprite street building, w x h cells. Everything collides except
    the top `roof` rows, which are walk-behind (the house-roof convention): a
    tower whose whole upper half was open hid the player in a pocket up to
    5x6 cells deep. The door cell(s) sit in the bottom row from column `door`."""
    return dict(w=w, h=h, sprites=None,
                colliders=[(x, y) for x in range(w) for y in range(roof, h)],
                doors=[(door + i, h - 1) for i in range(door_w)])


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
    # snow-dusted variants (recoloured by tools/make_snow_tiles.py) for Yukimura
    'tree-snow':    dict(w=2, h=3, sprites=[('Tops', 0, 0, 'tree-3-top-snow_0_0'), ('Collidables', 0, 2, 'tree-3-base-shadow-snow_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'shrub-large-snow': dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'shrub-large-circle-snow_0_0')],
                             colliders=[(0, 0), (0, 1), (1, 0), (1, 1)], doors=[]),
    'shrub-small-snow': dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'shrub-small-circle-snow_0_0')], colliders=[(0, 0)], doors=[]),
    'torii-red':    dict(w=6, h=5, sprites=[('Tops', 0, 0, 'torii-red-top_0_0'), ('Collidables', 1, 3, 'torii-red-feet_0_0')],
                         colliders=[(1, 3), (4, 3), (1, 4), (4, 4)], doors=[]),
    # The blue shrine hall, 5x8: the whole roof (re-sectioned by tools/extract_shrine.py
    # so its eaves are not cut off) overhangs the 3-wide hall by a cell each side
    # and two rows above it. Never place shrine-building without a roof on top —
    # its own roof rows are a 3-cell slice that the Tops sprite is there to cover.
    'shrine':       dict(w=5, h=8, sprites=[('Tops', 0, 0, 'shrine-top_0_0'), ('Collidables', 1, 2, 'shrine-building_0_0')],
                         # solid: the hall, plus every cell the roof would hide a walker in (the row
                         # behind the hall and the eave columns) — nobody vanishes under the roof
                         colliders=[(x, y) for x in (1, 2, 3) for y in range(2, 7) if (x, y) != (2, 6)]
                                   + [(x, 1) for x in range(5)] + [(x, y) for x in (0, 4) for y in (2, 3, 4)], doors=[(2, 6)]),
    # A GuttyKreum townhouse, top to bottom (matching the pack's promo):
    #   roof (3, with the eaves) + rafter (the window wall) + tier (the tiled
    #   awning band) + entrance (the ground-floor door). 6 cells tall.
    'house-blue':   dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-blue_0_0'), ('Collidables', 0, 3, 'building-rafter-blue_0_0'), ('Collidables', 0, 4, 'building-tier-blue_0_0'), ('Collidables', 0, 5, 'building-entrance-1_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'house-red':    dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-red_0_0'), ('Collidables', 0, 3, 'building-rafter-red_0_0'), ('Collidables', 0, 4, 'building-tier-red_0_0'), ('Collidables', 0, 5, 'building-entrance-3_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'house-black':  dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-black_0_0'), ('Collidables', 0, 3, 'building-rafter-black_0_0'), ('Collidables', 0, 4, 'building-tier-black_0_0'), ('Collidables', 0, 5, 'building-entrance-2_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
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
    # The GuttyKreum small pagoda, two 2x3 pieces stacked flush: spire + hip
    # roof + balcony on top, pent roof + walls + door below. 6 cells tall,
    # house convention: overhead art on Tops, only the wall storey collides.
    # (Born inverted and overlapping — the spire rendered mid-structure.)
    'pagoda-small': dict(w=2, h=6, sprites=[('Tops', 0, 0, 'red-pagoda-small-top_0_0'), ('Collidables', 0, 3, 'red-pagoda-small-base_0_0')],
                         colliders=[(x, y) for x in (0, 1) for y in (3, 4, 5)], doors=[]),
    # ---- Osaka landmarks (one big sprite each; art from tools/extract_dotonbori.py
    #      and tools/generate_tsutenkaku.py). All sit on Collidables so they Y-sort
    #      by their feet: solid at the base, walk-behind above it. -----------------
    # Dotonbori entrance arch: only the two posts collide (columns 0 and 7), so
    # the street runs straight under the sign through columns 1-6.
    'dotonbori-arch':  dict(w=8, h=6, sprites=[('Collidables', 0, 0, 'dotonbori-arch_0_0')],
                            colliders=[(x, y) for x in (0, 7) for y in (4, 5)], doors=[]),
    # The oval ferris wheel: the two truss legs (columns 2-3 and 8-9) and the
    # boarding gate between them collide; the rest of the ring is overhead.
    'dotonbori-wheel': dict(w=12, h=12, sprites=[('Collidables', 0, 0, 'dotonbori-wheel_0_0')],
                            colliders=[(x, y) for x in (2, 3, 8, 9) for y in (9, 10, 11)] + [(4, 10), (5, 10)], doors=[]),
    # Tsutenkaku Tower: the legs and the body over the archway collide; the two
    # cells in the archway mouth stay open so you can step in under the tower.
    # The colliders follow the splay of the legs (row 9 = where they leave the
    # deck, cols 2-5; rows 10-11 cols 1-6; the feet span all 8) so there is no
    # invisible wall on the empty plaza beside them.
    'tsutenkaku':      dict(w=8, h=13, sprites=[('Collidables', 0, 0, 'tsutenkaku_0_0')],
                            colliders=[(x, 9) for x in range(2, 6)]
                                      + [(x, y) for x in range(1, 7) for y in (10, 11)]
                                      + [(x, 12) for x in range(8) if x not in (3, 4)], doors=[]),
    # ---- generic city buildings (issue #18; art assembled by tools/extract_city.py
    #      at the 2x scale of the houses). One sprite each on Collidables, so it
    #      Y-sorts by its feet: solid from the ground up, only the top two rows
    #      (the roof line) are walk-behind. Doors are listed so a generator can
    #      wire an interior later; stamped sealed, the whole footprint is solid. --
    'highrise-yellow':    building(4, 8, door=1),
    'highrise-blue':      building(5, 11, door=2),
    'highrise-glass':     building(4, 10, door=1, door_w=2),
    'highrise-apartment': building(5, 8, door=2),
    'midrise-apartment':  building(5, 6, door=2),
    # the discount store ("Don Quijote"): generated parody sign over the facade
    'discount-store':     building(5, 8, door=2),
    # Kyoto-style two-storey townhouses: the main roof (rows 0-1) is overhead,
    # the upper wall, pent roof and shopfront (rows 2-4) are solid.
    'machiya-black':      building(5, 5, door=2),
    'machiya-red':        building(5, 5, door=2),
    'machiya-blue':       building(5, 5, door=2),
}
for _name, _spec in PREFABS.items():
    if _spec['sprites'] is None:                 # building(): one sprite named after the prefab
        _spec['sprites'] = [('Collidables', 0, 0, f'{_name}_0_0')]


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
