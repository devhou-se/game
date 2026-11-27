#!/usr/bin/env python3
"""generate_konbinis.py — procedurally generated konbini interiors (issue #23).

Every 7-Eleven building in the world gets its own interior: a seeded-unique
store room (aisle count, coolers, corner fillers, floor style, counter side all
derive from the store's identity), wired to its door both ways. Store ids are
deterministic — seeded by host room + building position — so regenerating
without moving buildings reproduces the exact same interiors.

Interiors are furnished with the office/interior pack sliced into
assets/sprites/office-*.png. The legacy hand-made 'Konbini' room, if one is
still in the config, is dropped.

Run from gamev2/:  python3 tools/generate_konbinis.py [Host ...]    (--help: this text, nothing run)
Then:              python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
"""
import hashlib
import random
import struct
import sys

import roomgen as rg

ARGS = rg.cli(__doc__, sys.argv[1:])   # --help: usage, nothing run
cfg = rg.load_config()

# Rooms whose 7-Elevens get an interior. Name hosts on the command line to
# (re)build only theirs - e.g. `generate_konbinis.py Sapporo` after regenerating
# Sapporo - and leave every other store's room exactly as it is.
ALL_HOSTS = ['Market', 'Park', 'Sapporo', 'Sendai']
ALL_HOSTS += ['Fukuoka']
ALL_HOSTS += ['Kanazawa']         # issue #68
ALL_HOSTS += ['SanFranbourne']     # the home city (issue #218)
HOSTS = ARGS or ALL_HOSTS
assert all(h in ALL_HOSTS for h in HOSTS), f'unknown host; expected some of {ALL_HOSTS}'
SEVEN = 'seven-eleven_0_0'
DOOR_DX, DOOR_DY = 1, 3      # door cell relative to the building's top-left

OFFICE_KEYS = [
    'office-shelf-snacks_0_0', 'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
    'office-freezer_0_0', 'office-cabinet_0_0', 'office-watercooler_0_0',
    'office-clock_0_0', 'office-fridge_0_0', 'office-counter2_0_0',
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


def store_name(host, ordinal, count):
    """The room's display name (the HUD shows it, never the room key):
    '7-Eleven · Sapporo', numbered only where a host has several stores."""
    where = cfg['rooms'][host].get('name', host)
    return f'7-Eleven · {where}' + (f' {ordinal}' if count > 1 else '')


def find_stores():
    """All 7-Eleven doors, per host, in stable (y, x) order. A store whose door
    already has a transporter is 'wired'."""
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
                'name': store_name(host, n, len(cells)),
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

    # one cooler run against the back wall (office-fridge, the glass-door drinks
    # cooler drawn by tools/generate_cooler_art.py, is 2 tall)
    run = rng.randint(2, 3)
    cx0 = rng.randint(left + 1, right - run)
    kind = rng.choice(COOLERS)
    # THE FRONT-CELL RULE (issue #152): a cooler or shelf is used by bumping it from
    # the cell below it, so the row under every fixture stays a walkway -
    #   coolers | walkway | aisle | walkway | (aisle | walkway) | counter row.
    # A two-cell cooler therefore pushes the aisles down a row, and the last aisle
    # stops two rows short of the counter row: one on the row above it had the
    # counter and the corner plant under its ends, which closed the ring and
    # left the back of the store sealed off from the door. The smallest store
    # (five floor rows) has no room for a two-cell cooler AND an aisle, so it
    # gets the one-cell freezer. `play.js lint` enforces it (shop-no-front).
    if png_size(kind)[1] > 64 and bottom - top < 5:
        kind = 'office-freezer_0_0'
    deep = max(1, round(png_size(kind)[1] / 64))
    for dx in range(run):
        put_solid(kind, cx0 + dx, top)

    # 1-2 short aisles, side columns always left as the walkway ring
    aisle_rows = [y for y in (top + deep + 1, top + deep + 3) if y <= bottom - 2]
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

    # 0-2 corner fillers (a water dispenser, then a plant), a plant opposite the
    # counter. NO rubbish bins - issue #19; `play.js lint` fails a room that has one.
    # The back one stands in the back corner, against the wall (issue #182): a row
    # lower it left the corner cell above it a one-cell dead end beside the
    # cooler run. Where the corner would leave a single cell between it and the
    # coolers, the run grows one unit to meet it - a one-cell nook is a dead
    # end whichever side of the dispenser it falls on. The coolers still keep
    # off the side columns and are used from the row below, so no fixture's
    # front cell is taken.
    if side == 'left':
        back, gap = right, (right - 1 if right - (cx0 + run) == 1 else None)
    else:
        back, gap = left, (left + 1 if cx0 - 1 - left == 1 else None)
    spots = [(back, top),
             (cx + 2, cy) if side == 'left' else (cx - 1, cy)]
    picked = sorted(rng.sample(spots, k=rng.randint(0, 2)))
    for (x, y), key in zip(picked, ('office-watercooler_0_0', 'office-plant-b_0_0')):
        put_solid(key, x, y)
    if gap is not None and (back, top) in picked:
        put_solid(kind, gap, top)
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
    room = b.room(store['name'], transporters=[
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
# the original hand-made interior is long gone; drop it from an old config
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
    # replace the door's transporter where it already sits (append only a new
    # one): a re-run on an unchanged world must leave config.json byte-identical
    door = rg.transporter(dx, dy, store['key'], *arrive, hidden=True)
    ts = host.setdefault('transporters', [])
    at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == (dx, dy)]
    if at:
        ts[at[0]] = door
        for i in reversed(at[1:]):
            del ts[i]
    else:
        ts.append(door)
    new_rooms.append(store['key'])
    print(f"built  {store['key']} — door {store['door']}, "
          f"{cfg['rooms'][store['key']]['worldWidth'] // 64}x"
          f"{cfg['rooms'][store['key']]['worldHeight'] // 64}")

rg.save_config(cfg)
print(f"\n{len(new_rooms)} interiors written. Now run config_to_tiled, then play.js lint, for:")
print('  ' + ' '.join(new_rooms + HOSTS))
