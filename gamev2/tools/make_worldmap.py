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

The image is rasterized by Tiled's `tmxrasterizer` when the Tiled app is
installed, and otherwise (or with --pil) room by room with
`node tools/play.js render`, which draws them in the game's own order — so the
tool runs on a machine without Tiled. Needs Pillow either way.

RE-RUN whenever exterior rooms change (unless custom). Run from gamev2/.
"""
import json, os, subprocess, sys, tempfile

RAST = '/Applications/Tiled.app/Contents/MacOS/tmxrasterizer'
WORLD = '../devhouse.world'
OUT_DIR = 'assets/map'
META = f'{OUT_DIR}/world-map.json'
TARGET_W = 1400

# the game stitches the districts in config `cities` together using cell
# offsets copied from the world file — refuse to go on if they disagree.
# Checked FIRST, before the hand-made-map exit below: with custom art the
# game cannot re-check the offsets against world-map.json at boot, so this
# (and `sync_cities.py --check`) is the only guard left.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync_cities
sync_cities.check()

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

size = TARGET_W if world_w >= world_h else int(TARGET_W * world_h / world_w)
from PIL import Image
if os.path.exists(RAST) and '--pil' not in sys.argv:
    tmp = tempfile.mktemp(suffix='.png')
    # hide the collision markers — they'd wash the minimap red
    subprocess.run([RAST, '--size', str(size), '--hide-layer', 'Colliders',
                    os.path.abspath(WORLD), tmp], check=True)
    im = Image.open(tmp).convert('RGB')
    os.unlink(tmp)
else:
    # No Tiled on this machine (or --pil): each room is drawn by the game's
    # own draw order (`node tools/play.js render`, colliders and Meta pins
    # left out) and pasted at its world position.
    k = size / max(world_w, world_h)
    im = Image.new('RGB', (round(world_w * k), round(world_h * k)), (0, 0, 0))
    here = os.path.dirname(os.path.abspath(__file__))
    for m in world['maps']:
        tmp = tempfile.mktemp(suffix='.png')
        subprocess.run(['node', os.path.join(here, 'play.js'), 'render',
                        os.path.basename(m['fileName'])[:-4], tmp], check=True, stdout=subprocess.DEVNULL)
        room_im = Image.open(tmp).convert('RGB')
        os.unlink(tmp)
        # size from the far edge, not the width, so neighbours meet without a seam
        x0, y0 = round((m['x'] - minx) * k), round((m['y'] - miny) * k)
        x1, y1 = round((m['x'] + m['width'] - minx) * k), round((m['y'] + m['height'] - miny) * k)
        im.paste(room_im.resize((x1 - x0, y1 - y0), Image.NEAREST), (x0, y0))
    print('tmxrasterizer not used — rooms rendered by tools/play.js')
os.makedirs(OUT_DIR, exist_ok=True)
im.save(f'{OUT_DIR}/world-map.png', optimize=True)
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
