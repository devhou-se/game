#!/usr/bin/env python3
"""generate_konbinis.py — procedurally generated konbini interiors (issue #23).

Every 7-Eleven building in the world gets its own interior: a seeded-unique
store room (aisle count, coolers, bins, boxes, floor style, counter side all
derive from the store's identity), wired to its door both ways. Store ids are
deterministic — seeded by host room + building position — so regenerating
without moving buildings reproduces the exact same interiors.

Interiors are furnished with the office/interior pack sliced into
assets/sprites/office-*.png. The Machi 7-Eleven that already leads to the
hand-made 'Konbini' room is left untouched.

Run from gamev2/:  python3 tools/generate_konbinis.py
Then:              python3 tools/qa_port.py --room <each new room + hosts>
                   python3 tools/config_to_tiled.py <each new room + hosts>
"""
import hashlib
import random
import struct

import roomgen as rg

cfg = rg.load_config()

HOSTS = ['Machi', 'Market', 'Park']
SEVEN = 'seven-eleven_0_0'
DOOR_DX, DOOR_DY = 1, 3      # door cell relative to the building's top-left

OFFICE_KEYS = [
    'office-shelf-snacks_0_0', 'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
    'office-freezer_0_0', 'office-cabinet_0_0', 'office-watercooler_0_0',
    'office-clock_0_0', 'office-fridge_0_0', 'office-bin_0_0', 'office-counter2_0_0',
    'office-register_0_0', 'office-poster-chart_0_0', 'office-poster-menu_0_0',
    'office-poster-photo_0_0', 'office-plant-a_0_0', 'office-plant-b_0_0',
    'office-boxes-large_0_0', 'office-boxes-small_0_0', 'office-wall-white_0_0',
    'office-floor-autotile_center', 'office-warm-autotile_center',
    'office-void-autotile_center',
]

SHELVES = ['office-shelf-snacks_0_0', 'office-shelf-drinks_0_0', 'office-shelf-glass_0_0']
COOLERS = ['office-fridge_0_0', 'office-freezer_0_0', 'office-cabinet_0_0']
POSTERS = ['office-poster-chart_0_0', 'office-poster-menu_0_0', 'office-poster-photo_0_0']
PLANTS = ['office-plant-a_0_0', 'office-plant-b_0_0']


def png_size(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16)
        return struct.unpack('>II', f.read(8))


def register_metadata():
    """Every tile key needs a spriteMetadata entry or its texture never loads.
    Anchor = half a cell over the sprite's own size (top-left-cell alignment)."""
    sm = cfg['spriteMetadata']
    for k in OFFICE_KEYS:
        if k in sm:
            continue
        w, h = png_size(k)
        sm[k] = {'anchorX': round(32 / w, 4), 'anchorY': round(32 / h, 4), 'frameCount': 1}


def find_stores():
    """All 7-Eleven doors, per host, in stable (y, x) order. A store whose door
    already has a transporter (the original Machi Konbini) is 'wired'."""
    stores = []
    for host in HOSTS:
        room = cfg['rooms'][host]
        cells = []
        for layer in room['layers']:
            for xy, idx in layer.get('tiles', {}).items():
                if rg._pal[idx] == SEVEN:
                    x, y = map(int, xy.split(','))
                    cells.append((y, x))
        for n, (y, x) in enumerate(sorted(cells), start=1):
            door = (x + DOOR_DX, y + DOOR_DY)
            stores.append({
                'host': host, 'ordinal': n, 'door': door,
                'front': (door[0], door[1] + 1),
                'key': f'Konbini{host}{n}',
            })
    return stores


ROOM_W, ROOM_H = 20, 15   # engine/camera minimum; the store box floats inside


def furnish(b, rng, x0, y0, bw, bh):
    """Seeded store furniture inside the box at (x0, y0), size (bw, bh).
    Box rows: y0..y0+1 wall band, walkable y0+2 .. y0+bh-3, bottom wall
    y0+bh-2, threshold y0+bh-1. Konbini-sized: everything within a couple
    of steps of the door."""
    def put_solid(key, x, y):
        w, h = png_size(key)
        b.put('Collidables', x, y, key)
        for dx in range(max(1, round(w / 64))):
            for dy in range(max(1, round(h / 64))):
                b.solid(x + dx, y + dy)

    left, right = x0 + 1, x0 + bw - 2       # walkable column range
    top, bottom = y0 + 2, y0 + bh - 3       # walkable row range

    # wall dressing on the band
    for x in rng.sample(range(left + 1, right), k=rng.randint(1, 3)):
        b.put('Other', x, y0 + 1, rng.choice(POSTERS))
    b.put('Other', rng.choice([left, right]), y0 + 1, 'office-clock_0_0')

    # one cooler run against the back wall (fridges are 2 tall)
    run = rng.randint(2, 3)
    cx0 = rng.randint(left + 1, right - run)
    kind = rng.choice(COOLERS)
    for dx in range(run):
        put_solid(kind, cx0 + dx, top)

    # 1-2 short aisles, side columns always left as the walkway ring
    aisle_rows = [top + 2 + 2 * i for i in range(2) if top + 2 + 2 * i <= bottom - 1]
    for y in aisle_rows[:rng.randint(1, 2)]:
        theme = rng.choice(SHELVES)
        for x in range(left + 1, right):
            put_solid(theme if rng.random() > 0.25 else rng.choice(SHELVES), x, y)

    # exactly one counter (2 wide, fills its tiles exactly) on the front row,
    # register on the inner tile
    side = rng.choice(['left', 'right'])
    cy = bottom
    cx = left if side == 'left' else right - 1
    put_solid('office-counter2_0_0', cx, cy)
    b.put('Tops', cx + 1 if side == 'left' else cx, cy, 'office-register_0_0')

    # 0-2 bins in the free corners, a plant opposite the counter
    spots = [(right, top + 1) if side == 'left' else (left, top + 1),
             (cx + 2, cy) if side == 'left' else (cx - 1, cy)]
    for x, y in rng.sample(spots, k=rng.randint(0, 2)):
        put_solid('office-bin_0_0', x, y)
    put_solid(rng.choice(PLANTS), right if side == 'left' else left, cy)


def build_interior(store):
    seed = int(hashlib.md5(f"{store['host']}:{store['door']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    bw = rng.randint(10, 13)   # box incl. side walls  -> 8-11 cells walkable
    bh = rng.randint(9, 11)    # box incl. band + wall + threshold -> 5-7 walkable
    x0 = (ROOM_W - bw) // 2
    y0 = (ROOM_H - bh) // 2
    b = rg.Builder(ROOM_W, ROOM_H)

    # the room is a dark void with one small lit store floating in it
    b.fill('office-void-autotile')
    floor = rng.choice(['office-floor-autotile', 'office-floor-autotile', 'office-warm-autotile'])
    for x in range(x0 + 1, x0 + bw - 1):
        for y in range(y0 + 2, y0 + bh - 2):
            b.put('Floor', x, y, f'{floor}_center')

    # walls: only the back wall is drawn — a single 1-tile-tall row directly
    # above the floor, aligned to the floor width. The sides and front have no
    # wall at all; the lit floor is framed by the surrounding void, and the room
    # boundary (set below) keeps the player on the floor, so no invisible
    # side/front colliders are needed. Door is a 2-cell gap in the front.
    midx = x0 + bw // 2
    gapx = (midx - 1, midx)
    for x in range(x0 + 1, x0 + bw - 1):
        b.put('Collidables', x, y0 + 1, 'office-wall-white_0_0'); b.solid(x, y0 + 1)

    furnish(b, rng, x0, y0, bw, bh)

    # lit doorway: a single mat row (1 deep) sticking out below the floor; the
    # exit transporters sit on the mat, the player arrives one cell inside it.
    for i, x in enumerate(gapx):
        b.put('Floor', x, y0 + bh - 2, f'{floor}_center')
        b.paver(x, y0 + bh - 2, i)

    fx, fy = store['front']
    room = b.room(store['key'], transporters=[
        rg.transporter(gapx[0], y0 + bh - 2, store['host'], fx, fy, hidden=True),
        rg.transporter(gapx[1], y0 + bh - 2, store['host'], fx, fy, hidden=True),
    ])
    # confine movement to the lit floor plus the 1-deep door mat — the
    # surrounding void isn't walkable, so the missing side/front walls need no
    # colliders.
    room['boundary'] = [
        [x0 + 1, y0 + 2], [x0 + bw - 1, y0 + 2],
        [x0 + bw - 1, y0 + bh - 2],
        [gapx[1] + 1, y0 + bh - 2], [gapx[1] + 1, y0 + bh - 1],
        [gapx[0], y0 + bh - 1], [gapx[0], y0 + bh - 2],
        [x0 + 1, y0 + bh - 2],
    ]
    room['interior'] = True          # day/night grading never applies inside
    return room, (gapx[0], y0 + bh - 3)   # arrival: just inside the door mat


register_metadata()
stores = find_stores()
# the original hand-made Machi interior is replaced by a generated one
cfg['rooms'].pop('Konbini', None)
new_rooms = []
for store in stores:
    room, arrive = build_interior(store)
    cfg['rooms'][store['key']] = room

    host = cfg['rooms'][store['host']]
    dx, dy = store['door']
    # unseal the door and wire it in
    for layer in host['layers']:
        if layer['name'] == 'Colliders':
            layer['tiles'].pop(f'{dx},{dy}', None)
    host['transporters'] = [t for t in host.get('transporters', [])
                            if (t['gridX'], t['gridY']) != (dx, dy)]
    host['transporters'].append(rg.transporter(dx, dy, store['key'], *arrive, hidden=True))
    new_rooms.append(store['key'])
    print(f"built  {store['key']} — door {store['door']}, "
          f"{cfg['rooms'][store['key']]['worldWidth'] // 64}x"
          f"{cfg['rooms'][store['key']]['worldHeight'] // 64}")

rg.save_config(cfg)
print(f"\n{len(new_rooms)} interiors written. Now run qa_port + config_to_tiled for:")
print('  ' + ' '.join(new_rooms + HOSTS))
