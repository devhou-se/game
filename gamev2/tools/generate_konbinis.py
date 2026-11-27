#!/usr/bin/env python3
"""generate_konbinis.py — the inside of every 7-Eleven (issues #23, #221).

Every 7-Eleven building in the world gets its own interior, wired to its door
both ways. A store is laid out like a Pokémon Mart and dressed like a real
7-Eleven: the clerk in a counter nook in one back corner under the tobacco
rack, a back wall of drink coolers, an open chiller, the coffee machine, the
water and the cash machine, shelf blocks you walk around, magazines and
baskets by the door, the mat at the bottom centre.

The floor plans are the text grids in LAYOUTS; a store's plan, whether it is
mirrored, and what its shelf blocks stock are dealt from its identity (host
room + door cell), so regenerating without moving buildings reproduces the
same interiors. The room is an Interior (tools/interiors.py: the shell, the
door, and its check that all of the floor is reached from the door);
check_store() holds it to the rules that are a store's own: a free cell under
every fixture that sells, a free side on everything else you can bump.

The art is the konbini-* kit (tools/generate_konbini_art.py) and the drinks
cooler office-fridge_0_0 (tools/generate_cooler_art.py). The legacy hand-made
'Konbini' room, if one is still in the config, is dropped. A store that is no
longer on its host's map loses its room (Konbini<Host><n>: stores are numbered
per host, so it is the highest number that goes), the room's tiled/*.tmj and
its old door on the next run (roomgen.drop_stale, issue #243).

Run from gamev2/:  python3 tools/generate_konbini_art.py            (needs Pillow; only when the kit changes)
                   python3 tools/generate_konbinis.py [Host ...]    (--help: this text, nothing run)
Then:              python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
"""
import random
import re
import sys

import interiors
import roomgen as rg
from interiors import Interior

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


def find_stores():
    """All 7-Eleven doors, per host, in stable (y, x) order. A store whose door
    already has a transporter is 'wired'."""
    stores = []
    for host in HOSTS:
        found = rg.find_sprites(cfg['rooms'][host], SEVEN)
        for n, (x, y, _) in enumerate(found, start=1):
            door = (x + DOOR_DX, y + DOOR_DY)
            stores.append({
                'host': host, 'ordinal': n, 'door': door,
                'front': (door[0], door[1] + 1),
                'key': f'Konbini{host}{n}',
                # the HUD shows this, never the room key; numbered only where a host has several stores
                'name': interiors.named(cfg, '7-Eleven', host, n if len(found) > 1 else None),
            })
    return stores


ROOM_W, ROOM_H = 20, 15   # engine/camera minimum; the store floats inside
FH, FY = 6, 4             # the floor is FH rows from row FY; the wall is the two rows above it

# One character per cell, the counter in the west corner (a store is mirrored or not by its seed).
# `wall` is the back wall by column, `floor` is FH rows:
#   wall   w plain, k with the clock, Tt the tobacco rack (behind the till)
#   row 0  against the wall: D drinks cooler, O open chiller, K coffee, W water, X copier, A cash machine
#   floor  Cc the counter and its nook (2x3), Gg a shelf block (2x2), Ff ice-cream chest (2x1),
#          Mm magazine rack (2x1), B baskets, . free
# A lower-case letter is the rest of the piece that starts at its capital.
LAYOUTS = {
    'aisles': dict(wall='Ttkwwwwwwwww',
                   floor=['Cc.DDDDOOOWA',
                          'cc..........',
                          'cc.Gg.Gg.Gg.',
                          '...gg.gg.gg.',
                          '............',
                          'B.........Mm']),
    'freezer': dict(wall='Ttkwwwwwwwww',
                    floor=['Cc.DDDOOKWXA',
                           'cc..........',
                           'cc.Gg.Gg.Ff.',
                           '...gg.gg....',
                           '............',
                           'B.........Mm']),
    'small': dict(wall='Ttkwwwwwww',
                  floor=['Cc.DDDOOWA',
                         'cc........',
                         'cc.Gg.Gg..',
                         '...gg.gg..',
                         '..........',
                         'B.......Mm']),
}
LAYOUT_NAMES = list(LAYOUTS)

WALLS = {'w': ('konbini-wall_0_0', 1), 'k': ('konbini-wall-clock_0_0', 1), 'T': ('konbini-wall-tobacco_0_0', 2)}
# 1x2 sprites standing over the wall's lower row, solid on floor row 0
AT_WALL = {'D': 'office-fridge_0_0', 'O': 'konbini-chiller', 'K': 'konbini-coffee_0_0',
           'W': 'konbini-water_0_0', 'X': 'konbini-copier_0_0', 'A': 'konbini-atm_0_0'}
FURNITURE = {'C': ('konbini-counter', 2, 3), 'G': ('konbini-gondola', 2, 2), 'F': ('konbini-freezer_0_0', 2, 1),
             'M': ('konbini-magazines_0_0', 2, 1), 'B': ('konbini-baskets_0_0', 1, 1)}
GONDOLAS = ['snacks', 'noodles', 'bread', 'daily']     # what a shelf block may stock
# what check_store() asks of each piece: a free cell under every column (it sells, or is the
# clock: play.js lint shop-no-front), or a free cell on any side (the till, and what says a line)
FRONT = ('office-fridge', 'konbini-chiller', 'konbini-coffee', 'konbini-water', 'konbini-gondola', 'konbini-wall-clock')
ANY_SIDE = ('konbini-counter', 'konbini-atm', 'konbini-copier', 'konbini-freezer', 'konbini-magazines')


def parse(layout, mirror):
    """A layout's pieces in floor coordinates: its width, the walls
    [(char, col, w)] and the furniture [(char, col, row, w, h)] in reading
    order - flipped left to right when `mirror` (a piece keeps its own left
    and right; only where it stands changes)."""
    spec = LAYOUTS[layout]
    fw = len(spec['wall'])
    assert len(spec['floor']) == FH and all(len(row) == fw for row in spec['floor']), f'{layout} does not fit its floor'
    flip = (lambda c, w=1: fw - c - w) if mirror else (lambda c, w=1: c)
    walls, c = [], 0
    while c < fw:
        ch = spec['wall'][c]
        w = WALLS[ch][1]
        walls.append((ch, flip(c, w), w))
        c += w
    items = []
    for r, row in enumerate(spec['floor']):
        for c, ch in enumerate(row):
            if ch in AT_WALL:
                assert r == 0, f'{layout}: {ch} must stand against the wall'
                items.append((ch, flip(c), r, 1, 1))
            elif ch in FURNITURE:
                _, w, h = FURNITURE[ch]
                items.append((ch, flip(c, w), r, w, h))
    return fw, walls, items


def plan_of(store):
    """(layout, mirrored, the shelf blocks' stock in reading order) for a store,
    from its identity (Asakusa's six stores come out on all three layouts;
    konbini.test.js holds a town with several to more than one plan)."""
    rng = random.Random(interiors.seed_of(f"{store['host']}:{store['door']}"))
    layout = rng.choice(LAYOUT_NAMES)
    mirror = rng.random() < 0.5
    stock = GONDOLAS[:]
    rng.shuffle(stock)
    return layout, mirror, stock


def build_interior(store):
    """(room, arrival cell) for one store."""
    layout, mirror, stock = plan_of(store)
    fw, walls, items = parse(layout, mirror)
    it = Interior(fw, FH, ox=(ROOM_W - fw) // 2, oy=FY, w=ROOM_W, h=ROOM_H)

    # the floor, a chequer of two near tones
    tone = lambda c, r: f"konbini-floor-{'ab'[(c + r) % 2]}_0_0"
    it.floor(tone)
    # the tops of the walls you look over, on the void around the floor: the sides, the glazed
    # shopfront either side of the doors (the mat lies across the two middle columns), the
    # corners where they meet
    m = fw // 2 - 1
    it.side_walls('konbini-side-w_0_0', 'konbini-side-e_0_0', 2, layer='Over Floor')
    it.front_wall('konbini-front_0_0', (m, m + 1), ('konbini-mat_0_0',), layer='Over Floor')
    it.put('Over Floor', -1, FH, 'konbini-front-w_0_0')
    it.put('Over Floor', fw, FH, 'konbini-front-e_0_0')

    # the back wall, two rows of it, and what stands against it and on the floor. The wall is
    # inside the room's outline (solid, so nobody walks it): a phone's camera holds a room no
    # taller than its view to its outline, which would leave the wall, and the top half of
    # everything standing against it, off the top of the screen
    it.back_wall([(c, WALLS[ch][0], w) for ch, c, w in walls], 2, view=True)
    chillers = gondolas = 0
    for ch, c, r, w, h in items:
        if ch in AT_WALL:
            key = AT_WALL[ch]
            if ch == 'O':                                   # the chiller's two halves, turn about
                key, chillers = f"{key}-{'ab'[chillers % 2]}_0_0", chillers + 1
            it.stand(key, c, 0)                             # over the wall's lower row, solid on floor row 0
        else:
            key = FURNITURE[ch][0]
            if ch == 'C':                                   # the nook is in the corner the counter stands in
                key = f"{key}-{'e' if mirror else 'w'}_0_0"
            elif ch == 'G':
                key, gondolas = f'{key}-{stock[gondolas % len(stock)]}_0_0', gondolas + 1
            it.prop(key, c, r, w, h)

    # the way out: the mat's two cells, one row below the floor (their floor is a tone out of
    # step with the chequer); you arrive just inside the doors, the mat the cell below
    inside = it.doorway(m, store['host'], store['front'], mat=lambda c, r: tone(c, r + 1))
    for key in sorted({rg._pal[i] for tiles in it.b.L.values() for i in tiles.values()}):
        assert key in cfg['spriteMetadata'], f'{key} is not registered: run tools/generate_konbini_art.py'
    # `interior` and nothing else: a store, whose counter and shelves sell (Interactions.js)
    room = it.room(store['name'])
    check_store(store['key'], it, inside[0])
    return room, inside[0]


def check_store(name, it, arrive):
    """The rules every plan obeys, on a finished store: the way in is free; every
    cooler, chiller, machine and shelf block, and the clock, has a free cell
    under each of its columns; the till and everything that only says a line
    has a free cell on some side. (That all of the free floor can be walked to
    from the mat is Interior.room's own check; `it.reached` is what it found.)"""
    seen = it.reached
    assert arrive in seen and all((t['gridX'], t['gridY']) in seen for t in it.exits), f'{name}: the way in is blocked'
    sizes = {WALLS[ch][0]: (WALLS[ch][1], 2) for ch in WALLS}
    for xy, idx in it.b.L['Collidables'].items():
        key = rg._pal[idx]
        x, y = map(int, xy.split(','))
        w, h = sizes.get(key) or next(((w, h) for k, w, h in FURNITURE.values() if key.startswith(k)), (1, 2))
        if key.startswith(FRONT):
            assert all((x + dx, y + h) in seen for dx in range(w)), f'{name}: {key} at {xy} has no cell in front'
        elif key.startswith(ANY_SIDE):
            around = ([(x + dx, y - 1) for dx in range(w)] + [(x + dx, y + h) for dx in range(w)]
                      + [(x - 1, y + dy) for dy in range(h)] + [(x + w, y + dy) for dy in range(h)])
            assert any(cell in seen for cell in around), f'{name}: {key} at {xy} cannot be reached'


stores = find_stores()
# the original hand-made interior is long gone; drop it from an old config
cfg['rooms'].pop('Konbini', None)
new_rooms = []
for store in stores:
    room, arrive = build_interior(store)
    cfg['rooms'][store['key']] = room

    # unseal the door and wire it in, where its transporter already sits (append only a new
    # one): a re-run on an unchanged world must leave config.json byte-identical
    rg.open_door(cfg['rooms'][store['host']], store['door'], store['key'], arrive)
    new_rooms.append(store['key'])
    print(f"built  {store['key']} — door {store['door']}, "
          f"{cfg['rooms'][store['key']]['worldWidth'] // 64}x"
          f"{cfg['rooms'][store['key']]['worldHeight'] // 64}")

# what an earlier run left for a store that is gone: its old door (its transporter dropped), and
# the host's rooms that no store claims any more (deleted; rg.save_config deletes their maps)
for host in HOSTS:
    stale = [k for k in cfg['rooms'] if re.fullmatch(f'Konbini{re.escape(host)}\\d+', k) and k not in new_rooms]
    for line in rg.drop_stale(cfg, host, 'Konbini', [s['door'] for s in stores if s['host'] == host], stale):
        print(line)

rg.save_config(cfg)
print(f"\n{len(new_rooms)} interiors written. Now run config_to_tiled, then play.js lint, for:")
print('  ' + ' '.join(new_rooms + HOSTS))
