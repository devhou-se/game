#!/usr/bin/env python3
"""generate_discount_stores.py — the Don Takote interiors (issue #91).

Every `discount-store` facade in a host town gets its own shop floor, wired to
its door both ways, on the generate_konbinis.py pattern - only bigger and
louder, the way the real thing is: the facade's sign across a yellow back wall,
a run of drink coolers, three ranks of shelves packed either side of a centre
aisle, stock piled in cartons, POP cards, one till by the door.

It is a shop through the existing rules, with no code of its own: the room is
`interior: true`, so src/utils/Interactions.js treats it as a konbini - the
counter sells everything, drink shelves and coolers the drinks, snack
shelves the food. No rubbish bins (issue #19; `play.js lint` would fail).

The floor plan is FIXED (so the town generators can wire their door without
running this first); what is seeded per store - by host room and door cell, so
a rebuild reproduces it - is the stock: which wing the coolers are on, what
each shelf rank carries, which side the till is, the floor.

Hosts and their generators:
  Osaka, Sapporo   generator-owned. generate_osaka.py / generate_sapporo.py
                   stamp the facade with its door open and add the transporter
                   themselves (door_transporter() below), so a regeneration
                   keeps the shop open. Run this after them for the interior.
  Market           a ported room with no generator: this script opens the door
                   surgically (lifts the one collider, adds the transporter)
                   and touches nothing else. It does the same, idempotently,
                   for the generated hosts.

Run from gamev2/:  python3 tools/generate_discount_art.py     # once: signage (Pillow)
                   python3 tools/generate_discount_stores.py [Host ...]
Then:              python3 tools/config_to_tiled.py <each store room + its host>
                   node tools/play.js lint <each store room + its host>
"""
import hashlib
import random
import struct
import sys

import roomgen as rg

ALL_HOSTS = ['Market', 'Osaka', 'Sapporo']
FACADE = 'discount-store_0_0'
DOOR_DX, DOOR_DY = 2, 7          # door cell relative to the facade's top-left

# ---- the fixed floor plan ---------------------------------------------------------
ROOM_W, ROOM_H = 27, 19
BW, BH = 21, 14                  # the store box: side margins, 2 wall rows, 10 floor rows, the mat
X0, Y0 = (ROOM_W - BW) // 2, (ROOM_H - BH) // 2
LEFT, RIGHT = X0 + 1, X0 + BW - 2            # floor columns (19 of them)
TOP, BOTTOM = Y0 + 2, Y0 + BH - 3            # floor rows (10 of them)
MID = (LEFT + RIGHT) // 2                    # the centre aisle, in line with the door
MAT_Y = Y0 + BH - 2
MAT = (MID - 1, MID, MID + 1)                # the door mat: three cells wide
ARRIVE = (MID, BOTTOM)                       # where you come in: just inside the mat

SHELVES = ['office-shelf-snacks_0_0', 'office-shelf-drinks_0_0', 'office-shelf-glass_0_0']
PLANTS = ['office-plant-a_0_0', 'office-plant-b_0_0']
POPS = ['don-takote-pop-yen_0_0', 'don-takote-pop-sale_0_0']
KEYS = SHELVES + PLANTS + POPS + [
    'don-takote-sign_0_0', 'don-takote-wall_0_0', 'don-takote-wall-top_0_0', 'office-freezer_0_0',
    'office-cabinet_0_0', 'office-counter2_0_0', 'office-register_0_0', 'office-boxes-large_0_0',
    'office-boxes-small_0_0', 'office-floor-autotile_center', 'office-warm-autotile_center',
    'office-void-autotile_center',
]


def room_key(host, ordinal=1, count=1):
    return f'DonTakote{host}' + (str(ordinal) if count > 1 else '')


def door_transporter(host, door, ordinal=1, count=1):
    """The hidden transporter a town generator puts on its facade's open door."""
    return rg.transporter(door[0], door[1], room_key(host, ordinal, count), *ARRIVE, hidden=True)


def png_size(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16)
        return struct.unpack('>II', f.read(8))


def register_metadata(cfg):
    """Every tile key needs a spriteMetadata entry or its texture never loads."""
    sm = cfg['spriteMetadata']
    for k in KEYS:
        if k in sm:
            continue
        assert not k.startswith('don-takote'), f'{k}: run tools/generate_discount_art.py first'
        w, h = png_size(k)
        sm[k] = {'anchorX': round(32 / w, 4), 'anchorY': round(32 / h, 4), 'frameCount': 1}


def store_name(cfg, host, ordinal, count):
    """The room's display name (the HUD shows it, never the room key):
    'Don Takote · Osaka', numbered only where a host has several stores."""
    where = cfg['rooms'][host].get('name', host)
    return f'Don Takote · {where}' + (f' {ordinal}' if count > 1 else '')


def find_stores(cfg, hosts):
    """Every discount-store door, per host, in stable (y, x) order."""
    stores = []
    for host in hosts:
        room = cfg['rooms'][host]
        cells = sorted((int(xy.split(',')[1]), int(xy.split(',')[0]))
                       for layer in room['layers'] for xy, idx in layer.get('tiles', {}).items()
                       if rg._pal[idx] == FACADE)
        for n, (y, x) in enumerate(cells, start=1):
            door = (x + DOOR_DX, y + DOOR_DY)
            stores.append({'host': host, 'door': door, 'front': (door[0], door[1] + 1),
                           'key': room_key(host, n, len(cells)),
                           'name': store_name(cfg, host, n, len(cells))})
    return stores


def furnish(b, rng):
    def put_solid(key, x, y):
        w, h = png_size(key)
        b.put('Collidables', x, y, key)
        for dx in range(max(1, round(w / 64))):
            for dy in range(max(1, round(h / 64))):
                b.solid(x + dx, y + dy)

    flip = rng.random() < 0.5                    # mirror the whole shop left-right
    mx = (lambda x, w=1: LEFT + RIGHT - x - (w - 1)) if flip else (lambda x, w=1: x)

    # ---- the back wall: the sign in the middle, POP cards either side ----------
    b.put('Other', MID - 2, Y0, 'don-takote-sign_0_0')
    for i, x in enumerate((LEFT + 1, LEFT + 4, RIGHT - 4, RIGHT - 1)):
        b.put('Other', x, Y0 + 1, POPS[(i + flip) % 2])

    # ---- the back row, wall to wall: one wing is a run of drink coolers, the
    #      other shelving, snacks under the sign, a stock cabinet in each corner.
    #      (office-freezer, one cell; office-fridge is the two-cell upright cooler
    #      from tools/generate_cooler_art.py and is left to the konbinis.)
    for x in range(LEFT + 1, MID - 2):
        put_solid('office-freezer_0_0', mx(x), TOP)
    wing = rng.choice(SHELVES)
    for x in range(MID + 3, RIGHT):
        put_solid(wing if rng.random() > 0.3 else rng.choice(SHELVES), mx(x), TOP)
    for x in range(MID - 2, MID + 3):
        put_solid('office-shelf-snacks_0_0', x, TOP)
    for x in (LEFT, RIGHT):
        put_solid('office-cabinet_0_0', x, TOP)

    # ---- three ranks of shelves, packed solid either side of the centre aisle;
    #      the side columns and the rows between are the only walkways ------------
    for y in (TOP + 2, TOP + 4, TOP + 6):
        for x0, x1 in ((LEFT + 1, MID - 1), (MID + 1, RIGHT - 1)):
            theme = rng.choice(SHELVES)
            for x in range(x0, x1 + 1):
                put_solid(theme if rng.random() > 0.2 else rng.choice(SHELVES), x, y)

    # ---- the front row: the till on one side of the door, cartons of stock
    #      stacked in both front corners (two rows deep - nothing else may close
    #      the last walkway, or it leaves a pocket), a plant either side of the mat
    # (office-counter2, as in the konbini: its art fills its two cells, where the
    #  three-cell office-counter leaves an invisible third)
    put_solid('office-counter2_0_0', mx(MID - 6, 2), BOTTOM)
    b.put('Tops', mx(MID - 5), BOTTOM, 'office-register_0_0')
    put_solid('office-boxes-small_0_0', mx(LEFT, 2), BOTTOM - 1)
    put_solid('office-boxes-large_0_0', mx(RIGHT - 2, 3), BOTTOM - 1)
    for x in (MID - 2, MID + 2):
        put_solid(rng.choice(PLANTS), x, BOTTOM)


def build_interior(store):
    seed = int(hashlib.md5(f"don:{store['host']}:{store['door']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    b = rg.Builder(ROOM_W, ROOM_H)

    # a dark void with the lit shop floor floating in it (as the konbini are)
    b.fill('office-void-autotile')
    floor = rng.choice(['office-warm-autotile', 'office-warm-autotile', 'office-floor-autotile'])
    for x in range(LEFT, RIGHT + 1):
        for y in range(TOP, BOTTOM + 1):
            b.put('Floor', x, y, f'{floor}_center')

    # only the back wall is drawn, two panels tall so the sign fits; the sides
    # and front are framed by the void and closed by the room boundary below
    for x in range(LEFT, RIGHT + 1):
        b.put('Collidables', x, Y0, 'don-takote-wall-top_0_0'); b.solid(x, Y0)
        b.put('Collidables', x, Y0 + 1, 'don-takote-wall_0_0'); b.solid(x, Y0 + 1)

    furnish(b, rng)

    # the door mat: one row sticking out below the floor; the exits sit on it
    for i, x in enumerate(MAT):
        b.put('Floor', x, MAT_Y, f'{floor}_center')
        b.paver(x, MAT_Y, i)

    fx, fy = store['front']
    room = b.room(store['name'], transporters=[
        rg.transporter(x, MAT_Y, store['host'], fx, fy, hidden=True) for x in MAT])
    # movement is confined to the lit floor plus the mat
    room['boundary'] = [
        [LEFT, TOP], [RIGHT + 1, TOP], [RIGHT + 1, BOTTOM + 1],
        [MAT[-1] + 1, BOTTOM + 1], [MAT[-1] + 1, MAT_Y + 1],
        [MAT[0], MAT_Y + 1], [MAT[0], BOTTOM + 1], [LEFT, BOTTOM + 1],
    ]
    room['interior'] = True          # a shop (Interactions.js), and no day/night grade inside
    room['shopTitle'] = 'DON TAKOTE'  # the till's list is not titled KONBINI (Shop.titleFor, #136)
    return room


def main(argv):
    hosts = argv or ALL_HOSTS
    assert all(h in ALL_HOSTS for h in hosts), f'unknown host; expected some of {ALL_HOSTS}'
    cfg = rg.load_config()
    register_metadata(cfg)
    built = []
    for store in find_stores(cfg, hosts):
        host = cfg['rooms'][store['host']]
        solid = {xy for L in host['layers'] if L.get('collision') for xy in L['tiles']}
        fx, fy = store['front']
        assert f'{fx},{fy}' not in solid, \
            f"{store['host']}: the cell in front of the door {store['front']} is blocked - shoppers could not leave"
        cfg['rooms'][store['key']] = build_interior(store)

        # open the facade's door and wire it in (a no-op where the town's own
        # generator already did - Osaka, Sapporo)
        dx, dy = store['door']
        for layer in host['layers']:
            if layer.get('collision'):
                layer['tiles'].pop(f'{dx},{dy}', None)
        # replace the door's transporter where it already sits (append only a
        # new one): a re-run must leave config.json byte-identical (issue #107)
        door = rg.transporter(dx, dy, store['key'], *ARRIVE, hidden=True)
        ts = host.setdefault('transporters', [])
        at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == (dx, dy)]
        if at:
            ts[at[0]] = door
            for i in reversed(at[1:]):
                del ts[i]
        else:
            ts.append(door)
        built.append(store['key'])
        print(f"built  {store['key']} ({store['name']}) - door {store['door']} in {store['host']}")
    rg.save_config(cfg)
    print(f'\n{len(built)} interiors written. Now run config_to_tiled, then play.js lint, for:')
    print('  ' + ' '.join(built + hosts))


if __name__ == '__main__':
    main(sys.argv[1:])
