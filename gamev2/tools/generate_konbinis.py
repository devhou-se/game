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
    'office-clock_0_0', 'office-fridge_0_0', 'office-bin_0_0', 'office-counter_0_0',
    'office-register_0_0', 'office-poster-chart_0_0', 'office-poster-menu_0_0',
    'office-poster-photo_0_0', 'office-plant-a_0_0', 'office-plant-b_0_0',
    'office-boxes-large_0_0', 'office-boxes-small_0_0', 'office-wall-white_0_0',
    'office-floor-autotile_center', 'office-warm-autotile_center',
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
        # only the hand-made 'Konbini' room counts as pre-wired; doors wired to
        # generated rooms are rebuilt, so re-running regenerates cleanly
        wired = {(t['gridX'], t['gridY']) for t in room.get('transporters', [])
                 if t.get('targetRoom') == 'Konbini'}
        for n, (y, x) in enumerate(sorted(cells), start=1):
            door = (x + DOOR_DX, y + DOOR_DY)
            stores.append({
                'host': host, 'ordinal': n, 'door': door,
                'front': (door[0], door[1] + 1),
                'key': f'Konbini{host}{n}',
                'wired': door in wired,
            })
    return stores


def furnish(b, rng, W, H):
    """Seeded store furniture. Rows: 0-1 wall band, 2(-3) coolers, aisles on
    alternating rows, counter + clutter near the front. Every corridor row
    between furniture rows stays fully walkable."""
    def put_solid(key, x, y):
        w, h = png_size(key)
        b.put('Collidables', x, y, key)
        for dx in range(max(1, round(w / 64))):
            for dy in range(max(1, round(h / 64))):
                b.solid(x + dx, y + dy)

    # wall dressing (drawn over the wall band, no collision of its own)
    for x in rng.sample(range(3, W - 3), k=rng.randint(2, 4)):
        b.put('Other', x, 1, rng.choice(POSTERS))
    b.put('Other', rng.choice([2, W - 3]), 1, 'office-clock_0_0')

    # coolers against the back wall (fridges are 2 tall: rows 2-3); x >= 5
    # keeps the corners free for the stockroom boxes
    n_coolers = rng.randint(1, 3)
    slots = rng.sample(range(5, W - 4, 3), k=min(n_coolers, len(range(5, W - 4, 3))))
    for sx in slots:
        kind = rng.choice(COOLERS)
        for dx in range(rng.randint(2, 3)):
            put_solid(kind, sx + dx, 2)

    # aisles: shelf runs with a guaranteed walkway ring (issue asks 2-5)
    n_aisles = rng.randint(2, min(5, (H - 10) // 2 + 2))
    aisle_rows = [5 + 2 * i for i in range(n_aisles) if 5 + 2 * i <= H - 5]
    for y in aisle_rows:
        x0 = rng.randint(2, 4)
        x1 = rng.randint(W - 6, W - 3)
        theme = rng.choice(SHELVES)
        for x in range(x0, x1 + 1):
            # mostly one theme per aisle, with the odd interloper
            put_solid(theme if rng.random() > 0.25 else rng.choice(SHELVES), x, y)

    # exactly one counter (3 wide) near the front, register on top
    side = rng.choice(['left', 'right'])
    cy = H - 4
    cx = 2 if side == 'left' else W - 6
    put_solid('office-counter_0_0', cx, cy)
    b.put('Tops', cx + 1, cy, 'office-register_0_0')

    # 0-3 rubbish bins
    bin_spots = [(cx + 3, cy) if side == 'left' else (cx - 1, cy),
                 (1, H - 3), (W - 2, H - 3)]
    for x, y in rng.sample(bin_spots, k=rng.randint(0, 3)):
        put_solid('office-bin_0_0', x, y)

    # stockroom boxes in a back corner (cooler row corners are kept free)
    if rng.random() < 0.7:
        boxes = rng.choice(['office-boxes-large_0_0', 'office-boxes-small_0_0'])
        bx = 1 if side == 'right' else W - 1 - round(png_size(boxes)[0] / 64)
        put_solid(boxes, bx, 2)

    # a plant or two, and maybe a water cooler by the counter
    for x, y in rng.sample([(1, H - 5), (W - 2, H - 5)], k=rng.randint(1, 2)):
        put_solid(rng.choice(PLANTS), x, y)
    if rng.random() < 0.5:
        put_solid('office-watercooler_0_0', cx + 4 if side == 'left' else cx - 2, cy)


def build_interior(store):
    seed = int(hashlib.md5(f"{store['host']}:{store['door']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    W = rng.choice([20, 22, 24])
    H = rng.choice([15, 16])
    b = rg.Builder(W, H)

    b.fill(rng.choice(['office-floor-autotile', 'office-floor-autotile', 'office-warm-autotile']))

    # walls: 2-row band on top, sides, bottom row with a 2-cell door gap;
    # the row below the bottom wall is the threshold (exit transporters)
    midx = W // 2
    gap = {(midx - 1, H - 2), (midx, H - 2)}
    for x in range(W):
        for y in (0, 1):
            b.put('Collidables', x, y, 'office-wall-white_0_0'); b.solid(x, y)
    for y in range(2, H - 2):
        for x in (0, W - 1):
            b.put('Collidables', x, y, 'office-wall-white_0_0'); b.solid(x, y)
    for x in range(W):
        if (x, H - 2) in gap:
            continue
        b.put('Collidables', x, H - 2, 'office-wall-white_0_0'); b.solid(x, H - 2)

    furnish(b, rng, W, H)

    # door mat on the threshold row, under the gap
    b.paver(midx - 1, H - 1, 0)
    b.paver(midx, H - 1, 1)

    fx, fy = store['front']
    room = b.room(store['key'], transporters=[
        rg.transporter(midx - 1, H - 1, store['host'], fx, fy, hidden=True),
        rg.transporter(midx, H - 1, store['host'], fx, fy, hidden=True),
    ])
    room['interior'] = True          # day/night grading never applies inside
    return room, (midx - 1, H - 2)   # arrival: standing in the door gap


register_metadata()
stores = find_stores()
new_rooms = []
for store in stores:
    if store['wired']:
        print(f"skip   {store['host']} #{store['ordinal']} at {store['door']} (already wired)")
        continue
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
