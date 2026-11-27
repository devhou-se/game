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
same interiors. check_store() holds every built room to the rules a plan must
obey: all of the floor reachable from the door, a free cell under every
fixture that sells, a free side on everything else you can bump.

The art is the konbini-* kit (tools/generate_konbini_art.py) and the drinks
cooler office-fridge_0_0 (tools/generate_cooler_art.py). The legacy hand-made
'Konbini' room, if one is still in the config, is dropped.

Run from gamev2/:  python3 tools/generate_konbini_art.py            (needs Pillow; only when the kit changes)
                   python3 tools/generate_konbinis.py [Host ...]    (--help: this text, nothing run)
Then:              python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
"""
import hashlib
import random
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
    seed = int(hashlib.md5(f"{store['host']}:{store['door']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    layout = rng.choice(LAYOUT_NAMES)
    mirror = rng.random() < 0.5
    stock = GONDOLAS[:]
    rng.shuffle(stock)
    return layout, mirror, stock


def build_interior(store):
    """(room, arrival cell) for one store."""
    layout, mirror, stock = plan_of(store)
    fw, walls, items = parse(layout, mirror)
    fx = (ROOM_W - fw) // 2
    b = rg.Builder(ROOM_W, ROOM_H)
    b.fill('office-void-autotile')

    def put(layer, x, y, key):
        assert key in cfg['spriteMetadata'], f'{key} is not registered: run tools/generate_konbini_art.py'
        b.put(layer, x, y, key)

    def solid(key, x, y, w=1, h=1):
        put('Collidables', x, y, key)
        for dx in range(w):
            for dy in range(h):
                b.solid(x + dx, y + dy)

    # the floor, a chequer of two near tones, and the mat: the two middle columns, one row below it
    mx, my = fx + fw // 2 - 1, FY + FH
    for c in range(fw):
        for r in range(FH):
            put('Floor', fx + c, FY + r, f"konbini-floor-{'ab'[(c + r) % 2]}_0_0")
    for i, x in enumerate((mx, mx + 1)):
        put('Floor', x, my, f"konbini-floor-{'ab'[(x - fx + FH + 1) % 2]}_0_0")
    put('Over Floor', mx, my, 'konbini-mat_0_0')

    # the tops of the walls you look over, on the void around the floor: the sides, the glazed
    # shopfront either side of the doors, the corners where they meet
    for y in range(FY - 2, my):
        put('Over Floor', fx - 1, y, 'konbini-side-w_0_0')
        put('Over Floor', fx + fw, y, 'konbini-side-e_0_0')
    for x in range(fx, fx + fw):
        if x not in (mx, mx + 1):
            put('Over Floor', x, my, 'konbini-front_0_0')
    put('Over Floor', fx - 1, my, 'konbini-front-w_0_0')
    put('Over Floor', fx + fw, my, 'konbini-front-e_0_0')

    # the back wall, two rows of it, and what stands against it and on the floor
    for ch, c, w in walls:
        solid(WALLS[ch][0], fx + c, FY - 2, w, 2)
    chillers = gondolas = 0
    for ch, c, r, w, h in items:
        if ch in AT_WALL:
            key = AT_WALL[ch]
            if ch == 'O':                                   # the chiller's two halves, turn about
                key, chillers = f"{key}-{'ab'[chillers % 2]}_0_0", chillers + 1
            put('Collidables', fx + c, FY - 1, key)
            b.solid(fx + c, FY)
        else:
            key = FURNITURE[ch][0]
            if ch == 'C':                                   # the nook is in the corner the counter stands in
                key = f"{key}-{'e' if mirror else 'w'}_0_0"
            elif ch == 'G':
                key, gondolas = f'{key}-{stock[gondolas % len(stock)]}_0_0', gondolas + 1
            solid(key, fx + c, FY + r, w, h)

    front = store['front']
    room = b.room(store['name'], transporters=[
        rg.transporter(mx, my, store['host'], front[0], front[1], hidden=True),
        rg.transporter(mx + 1, my, store['host'], front[0], front[1], hidden=True),
    ])
    # movement is confined to the lit floor and the mat: the void and the wall tops need no colliders.
    # The outline also takes in the back wall (solid, so nobody walks it): a phone's camera holds a
    # room no taller than its view to its outline (GameScene.applyRoomBounds), which would leave the
    # wall, and the top half of everything standing against it, off the top of the screen
    x1, y0, y1 = fx + fw, FY - 2, FY + FH
    room['boundary'] = [[fx, y0], [x1, y0], [x1, y1], [mx + 2, y1], [mx + 2, y1 + 1], [mx, y1 + 1], [mx, y1], [fx, y1]]
    room['interior'] = True          # day/night grading never applies inside
    arrive = (mx, my - 1)            # just inside the doors; the mat is the cell below
    check_store(store['key'], room, arrive, (fx, fw))
    return room, arrive


def check_store(name, room, arrive, floor):
    """The rules every plan obeys: all of the free floor can be walked to from
    the way in; every cooler, chiller, machine and shelf block, and the clock,
    has a free cell under each of its columns; the till and everything that
    only says a line has a free cell on some side."""
    fx, fw = floor
    solid = {tuple(map(int, c.split(','))) for c in room['layers'][-1]['tiles']}
    mat = {(t['gridX'], t['gridY']) for t in room['transporters']}
    free = ({(fx + c, FY + r) for c in range(fw) for r in range(FH)} | mat) - solid
    assert arrive in free and len(mat) == 2 and mat <= free, f'{name}: the way in is blocked'
    seen, todo = {arrive}, [arrive]
    while todo:
        x, y = todo.pop()
        for cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if cell in free and cell not in seen:
                seen.add(cell)
                todo.append(cell)
    assert seen == free, f'{name}: floor nobody can reach: {sorted(free - seen)}'
    sizes = {WALLS[ch][0]: (WALLS[ch][1], 2) for ch in WALLS}
    for xy, idx in room['layers'][4]['tiles'].items():
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
