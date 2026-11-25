#!/usr/bin/env python3
"""render_room.py — render a room's Tiled map to a PNG with Pillow.

A dependency-light stand-in for Tiled's `tmxrasterizer` (which needs the Tiled
app installed): reads `tiled/<room>.tmj` with the same conventions as
src/systems/TiledAdapter.js and draws it the way the game does — ground layers
(z < 2) flat in layer order, everything standing Y-sorted by its feet row with
the Tops bias and per-sprite depthBias (RoomManager.loadLayer). Collision
layers and the Meta layer are not drawn unless --colliders is passed (then
solid cells get a translucent red wash, handy when checking a new room).

Used by tools/make_worldmap.py when tmxrasterizer is missing, and as the
"look at the render" step of the generate-room loop. Needs Pillow.

Run from gamev2/:
    python3 tools/render_room.py Osaka /tmp/osaka.png [--scale 0.5] [--colliders]
"""
import json, os, sys
from PIL import Image

GS = 64
_tex = {}


def _sprite(key):
    if key not in _tex:
        _tex[key] = Image.open(f'assets/sprites/{key}.png').convert('RGBA')
    return _tex[key]


def _prop(o, name, default=None):
    return next((p['value'] for p in o.get('properties', []) if p['name'] == name), default)


def load_tmj(path):
    """-> (width, height, [(name, z, collision, [(x, y, key)])]) in file order,
    a tile layer and its '·obj' companion kept as separate entries."""
    tmj = json.load(open(path))
    ts = tmj['tilesets'][0]
    id2key = {t['id']: os.path.basename(t['image'])[:-4] for t in ts['tiles']}
    keyof = lambda gid: id2key[(gid & 0x1FFFFFFF) - ts['firstgid']]
    W = tmj['width']
    layers = []
    for L in tmj['layers']:
        if L['type'] == 'objectgroup' and _prop(L, 'gv2meta', False):
            continue
        name, z, coll = _prop(L, 'gv2layer', L['name']), _prop(L, 'z', 0), _prop(L, 'collision', False)
        if L['type'] == 'tilelayer':
            cells = [(i % W, i // W, keyof(g)) for i, g in enumerate(L['data']) if g]
        elif L['type'] == 'objectgroup':
            cells = [(round(o['x'] / GS), round(o['y'] / GS), keyof(o['gid']))
                     for o in L['objects'] if o.get('gid')]
        else:
            continue
        layers.append((name, z, coll, cells))
    return W, tmj['height'], layers


def render_tmj(path, colliders=False, sprite_meta=None):
    """Draw one room map at full resolution (64px cells) -> RGBA image."""
    sprite_meta = sprite_meta or {}
    W, H, layers = load_tmj(path)
    canvas = Image.new('RGBA', (W * GS, H * GS), (0, 0, 0, 255))
    standing, solid = [], []
    for order, (name, z, coll, cells) in enumerate(layers):
        if coll:
            solid += [(x, y) for (x, y, _k) in cells]
            continue
        for (x, y, key) in cells:
            im = _sprite(key)
            if z < 2:
                _paste(canvas, im, x, y)
            else:
                feet = y + max(1, round(im.height / GS))
                depth = feet * 10 + (11 if z >= 7 else 0) + sprite_meta.get(key, {}).get('depthBias', 0)
                standing.append((depth, order, y, x, key))
    for (_d, _o, y, x, key) in sorted(standing):
        _paste(canvas, _sprite(key), x, y)
    if colliders:
        wash = Image.new('RGBA', (GS, GS), (255, 0, 0, 90))
        for (x, y) in solid:
            if 0 <= x < W and 0 <= y < H:
                canvas.alpha_composite(wash, (x * GS, y * GS))
    return canvas


def _paste(canvas, im, x, y):
    """alpha_composite that tolerates sprites hanging over the map edge."""
    px, py = x * GS, y * GS
    box = (max(0, -px), max(0, -py), min(im.width, canvas.width - px), min(im.height, canvas.height - py))
    if box[2] <= box[0] or box[3] <= box[1]:
        return
    canvas.alpha_composite(im.crop(box), (px + box[0], py + box[1]))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit(__doc__)
    scale = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 1.0
    if '--scale' in sys.argv:
        args = [a for a in args if a != sys.argv[sys.argv.index('--scale') + 1]]
    room, out = args[0], args[1]
    meta = json.load(open('config.json')).get('spriteMetadata', {})
    im = render_tmj(f'tiled/{room.lower()}.tmj', colliders='--colliders' in sys.argv, sprite_meta=meta)
    if scale != 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.convert('RGB').save(out)
    print(f'{room}: {im.width}x{im.height}px -> {out}')
