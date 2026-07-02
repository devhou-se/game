"""prefab.py — load Tiled-authored prefab maps (gamev2/tiled/prefabs/*.tmj)
and stamp them into a room under construction.

A prefab is a small ordinary Tiled map, built by hand in the Tiled app:
  - object layers whose `gv2layer` property names the room layer the pieces
    belong to (Collidables / Tops / Other / Over Floor ...), holding the
    sprites as tile-objects;
  - a `Colliders` tile layer painted with the visible `collider-marker` tile
    (converted to the game's invisible gk_blank colliders on stamp);
  - a `Meta` object layer of point objects: `kind=door` marks a cell that is
    left open in the collision and reported back so the caller can wire a
    transporter to it (a house door, a shop entrance...).

Generators do:   pf = load_prefab('house-blue')
                 doors = stamp(pf, x, y, put, solid)   # callbacks into the
                 # room being built; doors = [(cellx, celly), ...] world cells.
If a door is not wired to a transporter, pass seal_doors=True to keep it solid.
"""
import json, os

PREFAB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiled', 'prefabs')
GS = 64


def load_prefab(name):
    tmj = json.load(open(os.path.join(PREFAB_DIR, name + '.tmj')))
    ts = tmj['tilesets'][0]
    id2key = {t['id']: os.path.basename(t['image'])[:-4] for t in ts['tiles']}
    keyof = lambda gid: id2key[(gid & 0x1FFFFFFF) - ts['firstgid']]
    prop = lambda o, n, d=None: next((p['value'] for p in o.get('properties', []) if p['name'] == n), d)

    sprites, colliders, doors = [], [], []
    for L in tmj['layers']:
        if L['type'] == 'objectgroup' and prop(L, 'gv2meta', False):
            for o in L['objects']:
                if prop(o, 'kind') == 'door':
                    doors.append((int(o['x'] // GS), int(o['y'] // GS)))
        elif L['type'] == 'objectgroup':
            layer = prop(L, 'gv2layer', L['name'].replace(' ·obj', ''))
            for o in L['objects']:
                if o.get('gid'):
                    sprites.append((layer, round(o['x'] / GS), round(o['y'] / GS), keyof(o['gid'])))
        elif L['type'] == 'tilelayer':
            name_ = prop(L, 'gv2layer', L['name'])
            for i, gid in enumerate(L['data']):
                if not gid: continue
                cx, cy = i % L['width'], i // L['width']
                k = keyof(gid)
                if name_ == 'Colliders' or k == 'collider-marker':
                    colliders.append((cx, cy))
                else:
                    sprites.append((name_, cx, cy, k))
    return {'name': name, 'w': tmj['width'], 'h': tmj['height'],
            'sprites': sprites, 'colliders': colliders, 'doors': doors}


def stamp(pf, x, y, put, solid, seal_doors=True):
    """Place prefab pf with its top-left at cell (x, y).
    put(layer, x, y, key) and solid(x, y) are the room builder's callbacks.
    Returns the world cells of the prefab's doors (empty if none)."""
    doors = [(x + dx, y + dy) for (dx, dy) in pf['doors']]
    for layer, dx, dy, key in pf['sprites']:
        put(layer, x + dx, y + dy, key)
    for (dx, dy) in pf['colliders']:
        cell = (x + dx, y + dy)
        if cell in doors and not seal_doors:
            continue
        solid(*cell)
    if seal_doors:
        for c in doors: solid(*c)
    return doors
