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
import random
import sys

import interiors
import roomgen as rg
from interiors import Interior

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


def find_stores(cfg, hosts):
    """Every discount-store door, per host, in stable (y, x) order."""
    stores = []
    for host in hosts:
        room = cfg['rooms'][host]
        found = rg.find_sprites(room, FACADE)
        for n, (x, y, _) in enumerate(found, start=1):
            door = (x + DOOR_DX, y + DOOR_DY)
            stores.append({'host': host, 'door': door, 'front': (door[0], door[1] + 1),
                           'key': room_key(host, n, len(found)),
                           # the HUD shows this, never the room key; numbered only where a host has several
                           'name': interiors.named(cfg, 'Don Takote', host, n if len(found) > 1 else None)})
    return stores


def furnish(b, rng):
    def put_solid(key, x, y):
        b.prop(key, x, y, *rg.sprite_cells(key))

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
    rng = random.Random(interiors.seed_of(f"don:{store['host']}:{store['door']}"))
    # a dark void with the lit shop floor floating in it (as the konbini are)
    it = Interior(RIGHT - LEFT + 1, BOTTOM - TOP + 1, ox=LEFT, oy=TOP, w=ROOM_W, h=ROOM_H)
    floor = rng.choice(['office-warm-autotile', 'office-warm-autotile', 'office-floor-autotile'])
    it.floor(lambda fx, fy: f'{floor}_center')

    # only the back wall is drawn, two panels tall so the sign fits; the sides
    # and front are framed by the void and closed by the room boundary
    for fx in range(it.fw):
        it.prop('don-takote-wall-top_0_0', fx, -2)
        it.prop('don-takote-wall_0_0', fx, -1)

    furnish(it.b, rng)

    # the door mat: one row sticking out below the floor; the exits sit on it
    inside = it.doorway(MAT[0] - LEFT, store['host'], store['front'], n=len(MAT), mat=f'{floor}_center')
    for i, x in enumerate(MAT):
        it.b.paver(x, MAT_Y, i)
    assert inside[1] == ARRIVE, 'the town generators wire their door to ARRIVE'

    # movement is confined to the lit floor plus the mat. `interior` and no shopEnabled: a shop
    # (Interactions.js); the till's list is not titled KONBINI (Shop.titleFor, #136)
    return it.room(store['name'], shopTitle='DON TAKOTE')


def main(argv):
    hosts = rg.cli(__doc__, argv) or ALL_HOSTS   # --help: usage, nothing run
    assert all(h in ALL_HOSTS for h in hosts), f'unknown host; expected some of {ALL_HOSTS}'
    cfg = rg.load_config()
    for k in KEYS:                               # the signage is drawn, not sliced from a pack
        if k not in cfg['spriteMetadata']:
            assert not k.startswith('don-takote'), f'{k}: run tools/generate_discount_art.py first'
    rg.register_metadata(cfg, KEYS)
    built = []
    for store in find_stores(cfg, hosts):
        host = cfg['rooms'][store['host']]
        solid = {xy for L in host['layers'] if L.get('collision') for xy in L['tiles']}
        fx, fy = store['front']
        assert f'{fx},{fy}' not in solid, \
            f"{store['host']}: the cell in front of the door {store['front']} is blocked - shoppers could not leave"
        cfg['rooms'][store['key']] = build_interior(store)

        # open the facade's door and wire it in (a no-op where the town's own
        # generator already did - Osaka, Sapporo), replacing the door's transporter
        # where it already sits: a re-run must leave config.json byte-identical (issue #107)
        rg.open_door(host, store['door'], store['key'], ARRIVE)
        built.append(store['key'])
        print(f"built  {store['key']} ({store['name']}) - door {store['door']} in {store['host']}")
    rg.save_config(cfg)
    print(f'\n{len(built)} interiors written. Now run config_to_tiled, then play.js lint, for:')
    print('  ' + ' '.join(built + hosts))


if __name__ == '__main__':
    main(sys.argv[1:])
