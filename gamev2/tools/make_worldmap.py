#!/usr/bin/env python3
"""make_worldmap.py — build the in-game Map screen's assets.

The map shows the OVERWORLD ONLY (../devhouse.world — every exterior room in
its true position, one single view). Interiors never appear on the map; they
are seen by entering them, and the map marks the player at their entrance.

Writes assets/map/world-map.png + world-map.json. The JSON is a CONTRACT the
game reads — the image is replaceable art:

  { "custom": false,
    "image": "assets/map/world-map.png", "width": W, "height": H,
    "rooms": { "Tokyo": {"x":..,"y":..,"w":..,"h":..,"cells":[59,46]}, ... } }

Rects are in IMAGE pixels; "cells" is the room's grid size. The game maps a
grid cell to the image through the room's own rect, so replacement art does
NOT need to be to scale — draw any graphic (hand-drawn, parchment, whatever),
describe where each room sits on it, set "custom": true, and this tool will
refuse to overwrite your work (--force overrides).

RE-RUN whenever exterior rooms change (unless custom). Run from gamev2/.
"""
import json, os, subprocess, sys, tempfile

RAST = '/Applications/Tiled.app/Contents/MacOS/tmxrasterizer'
WORLD = '../devhouse.world'
OUT_DIR = 'assets/map'
META = f'{OUT_DIR}/world-map.json'
TARGET_W = 1400

if os.path.exists(META) and '--force' not in sys.argv:
    if json.load(open(META)).get('custom'):
        sys.exit('world-map.json is marked "custom": true (hand-made art) — not overwriting. Use --force.')

world = json.load(open(WORLD))
cfg = json.load(open('config.json'))
room_keys = {k.lower(): k for k in cfg['rooms']}

minx = min(m['x'] for m in world['maps'])
miny = min(m['y'] for m in world['maps'])
world_w = max(m['x'] + m['width'] for m in world['maps']) - minx
world_h = max(m['y'] + m['height'] for m in world['maps']) - miny

tmp = tempfile.mktemp(suffix='.png')
size = TARGET_W if world_w >= world_h else int(TARGET_W * world_h / world_w)
# hide the collision markers — they'd wash the minimap red
subprocess.run([RAST, '--size', str(size), '--hide-layer', 'Colliders',
                os.path.abspath(WORLD), tmp], check=True)

from PIL import Image
im = Image.open(tmp)
os.makedirs(OUT_DIR, exist_ok=True)
im.convert('RGB').save(f'{OUT_DIR}/world-map.png', optimize=True)
os.unlink(tmp)
scale = im.width / world_w

rooms = {}
for m in world['maps']:
    room = room_keys.get(os.path.basename(m['fileName'])[:-4])
    if not room:
        print(f"warn: no room for {m['fileName']}", file=sys.stderr); continue
    r = cfg['rooms'][room]
    rooms[room] = {'x': round((m['x'] - minx) * scale, 1),
                   'y': round((m['y'] - miny) * scale, 1),
                   'w': round(m['width'] * scale, 1),
                   'h': round(m['height'] * scale, 1),
                   'cells': [r['worldWidth'] // 64, r['worldHeight'] // 64]}

meta = {'custom': False, 'image': f'{OUT_DIR}/world-map.png',
        'width': im.width, 'height': im.height, 'rooms': rooms}
json.dump(meta, open(META, 'w'), indent=1, sort_keys=True)
print(f"world-map.png {im.width}x{im.height} "
      f"({os.path.getsize(f'{OUT_DIR}/world-map.png') // 1024}KB), rooms: {sorted(rooms)}")
