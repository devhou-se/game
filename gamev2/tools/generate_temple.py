#!/usr/bin/env python3
"""generate_temple.py — the main hall inside Senso-ji (issue #213).

What "the temple" is on the map: at the head of the stall street in the Tokyo
district `Market` (display name "Asakusa") stands one great red-roofed hall,
laid from `shrine-walls` and `red-shrine-top-parts` tiles - twelve cells wide,
its double door (two `shrine-walls_2_2` leaves, Market 27,15 and 28,15) at the
top of four `castle-stairs`. It is the hall the `Senso-ji temple` landmark
hangs on. It is NOT the district's shrine: that is the smaller `shrine-red`
prefab to its east (Market 43,11), which already opens into its own worship
hall ("Shrine · Asakusa", tools/generate_shrines.py) and is left alone. The
temple hall was sealed; its two door leaves are now its door, into ONE
interior, a Buddhist main hall (hondo).

The district is a ported map with no generator, so its map is the source of
truth and this tool changes exactly two things in it, the way
generate_palace.py does: the collider on each door leaf is removed and a
hidden transporter is wired onto it (replaced in place, so a re-run leaves
config.json byte-identical). rooms.TempleMarket1 is rebuilt from scratch (any
NPCs it holds are kept). Zuihoden in Sendai and any other temple wait for
their own city's rebuild: only this hall is opened here.

Inside (26x22; art: tools/generate_temple_art.py), dim, old gold and dark red
lacquer on a stone floor:
  * the back wall under the edge of a coffered, painted ceiling and a frieze
    (over the sanctum, two dragons and a pearl): the charm counter at the
    head of the west aisle, the hundred-drawer fortune cabinet at the head of
    the east one (shake the cylinder: src/TempleVisit.js), and between them,
    behind the sanctum, old gold panels either side of the cabinet where the
    Kannon sits under her golden canopy, the brocade curtains drawn across;
  * the inner sanctum (naijin), sixteen cells behind a gilt lattice you see
    through - altar, banked candles, gilt lotus, the monk's seat - the
    lattice open in the middle over a low rail;
  * in front of the opening the offering box, then the great bronze incense
    burner with its smoke (waft it over yourself), then, inside the doors,
    the great red paper lantern hanging over your head;
  * dark red columns you walk behind, a great drum and a bowl bell before the
    lattice, a rack of votive candles on the west wall, the rail of
    tied-up bad fortunes on the east, hung gilt lanterns, haze in the air.
The room is `interior` (never offered to the blog pipeline) and `lanternLight`:
at night it dims and its candles and lanterns glow (DayNight; their spots are
rows of src/utils/Glows.js).

Run from gamev2/:  python3 tools/generate_temple.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py TempleMarket1 Market
       node tools/play.js lint TempleMarket1 Market
(.agent-queue/items/temple_apply.sh does all of it, and the gates.)
"""
import sys

import roomgen as rg

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Market'
KEY = f'{rg.TEMPLE_PREFIX}{HOST}1'
NAME = 'Senso-ji'         # 8 characters: a phone's one-row HUD bar fits the countdown beside it
FW, FH = 24, 15           # the floor, in cells
OX, OY = 1, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
W, H = FW + 2, FH + 7
SANCTUM = (4, 16, 4)      # the naijin: its first floor column, its width, its depth in rows
DOOR_X = 11               # the doorway: floor columns 11 and 12, under the outside's two leaves


def leaves():
    """The hall's door, west leaf first: (door cell, the cell in front of it).

    The two `shrine-walls_2_2` tiles that stand side by side with a step
    (`castle-stairs`) below each: the gate and the side halls of the district
    are laid from the same family but have no such pair."""
    host = cfg['rooms'][HOST]
    cells = {name: set() for name in ('door', 'step')}
    for layer in host['layers']:
        for xy, idx in layer['tiles'].items():
            key = rg._pal[idx]
            x, y = map(int, xy.split(','))
            if layer['name'] in rg.DOOR_LAYERS and key in rg.TEMPLE_DOORS:
                cells['door'].add((x, y))
            elif key.startswith('castle-stairs'):
                cells['step'].add((x, y))
    found = sorted(c for c in cells['door'] if (c[0], c[1] + 1) in cells['step']
                   and ((c[0] - 1, c[1]) in cells['door'] or (c[0] + 1, c[1]) in cells['door']))
    assert len(found) == 2 and found[1] == (found[0][0] + 1, found[0][1]), \
        f'{HOST}: expected the two leaves of the temple door at the top of its steps, found {found}'
    return [((x, y), (x, y + 1)) for x, y in found]


def build(doors):
    b = rg.Builder(W, H)
    s = lambda piece: f'temple-in-{piece}_0_0'

    def put(layer, fx, fy, piece):
        b.put(layer, OX + fx, OY + fy, s(piece))

    def solid(fx, fy, w=1, h=1):
        for dx in range(w):
            for dy in range(h):
                b.solid(OX + fx + dx, OY + fy + dy)

    def stand(fx, foot, piece, w=1, h=2, layer='Collidables'):
        """A piece `h` rows tall whose bottom row (`foot`) is solid: the rest is walked behind."""
        put(layer, fx, foot - h + 1, piece)
        solid(fx, foot, w)

    # ---- the floor and the side walls ---------------------------------------------------
    b.fill('office-void-autotile')
    for fx in range(FW):
        for fy in range(FH):
            put('Floor', fx, fy, 'slab-a' if (fx * 3 + fy * 5 + fx // 3) % 4 else 'slab-b')
    for fy in range(-3, FH):
        b.put('Floor', 0, OY + fy, s('side-w'))
        b.put('Floor', W - 1, OY + fy, s('side-e'))
    for fy in (5, 9, 13):                                           # a little day through the slats
        put('Over Floor', 0, fy, 'sun-w')
        put('Over Floor', FW - 2, fy, 'sun-e')

    # ---- the front wall and the doorway ---------------------------------------------------
    for fx in range(FW):
        if fx not in (DOOR_X, DOOR_X + 1):
            put('Floor', fx, FH, 'wall-front')
    put('Floor', DOOR_X, FH, 'threshold-w')
    put('Floor', DOOR_X + 1, FH, 'threshold-e')
    put('Non-Collidables', DOOR_X, FH - 3, 'doorlight')

    # ---- the back wall: charms, the sanctum's wall and cabinet, the fortune drawers ----------
    for fx, piece, w in ((0, 'wall-charms', 4), (4, 'wall-tennin-l', 5), (9, 'kuden', 6),
                         (15, 'wall-tennin-r', 5), (20, 'omikuji', 4)):
        put('Collidables', fx, -3, piece)
        solid(fx, -3, w, 3)

    # ---- the inner sanctum behind its lattice ---------------------------------------------------
    sx, sw, sd = SANCTUM
    put('Collidables', sx, 0, 'naijin')
    solid(sx, 0, sw, sd)

    # ---- down the middle: the offering box, the incense burner, the great lantern -----------------
    put('Collidables', DOOR_X - 1, 4, 'saisen')
    solid(DOOR_X - 1, 4, 4, 2)
    stand(DOOR_X - 1, 9, 'jokoro', w=4, h=3)
    solid(DOOR_X, 8, 2)                                             # the bowl is two rows deep in the middle
    put('Tops', DOOR_X - 1, 11, 'chochin')

    # ---- columns: two rows of four, only their feet solid -------------------------------------------
    for fx in (3, 7, 16, 20):
        for foot in (7, 12):
            stand(fx, foot, 'pillar', h=3)

    # ---- before the lattice: candles by the box, the drum to the west, the bowl bell to the east ------
    stand(DOOR_X - 2, 5, 'shokudai')
    stand(DOOR_X + 3, 5, 'shokudai')
    stand(5, 5, 'drum', w=2)
    stand(17, 5, 'keisu', w=2)

    # ---- the aisles ---------------------------------------------------------------------------------
    stand(0, 9, 'candles', w=2)                                     # votive candles on the west wall
    stand(FW - 2, 9, 'musubi', w=2)                                 # the tied fortunes on the east
    stand(1, 14, 'shokudai')
    stand(FW - 2, 14, 'shokudai')
    stand(DOOR_X - 2, 14, 'renge')                                  # gilt lotus either side of the doors
    stand(DOOR_X + 3, 14, 'renge')
    for fx in (4, FW - 6):                                          # a bench each side, for the footsore
        put('Collidables', fx, 14, 'bench')
        solid(fx, 14, 2)

    # ---- overhead: hung lanterns, and the haze ----------------------------------------------------------
    for fx, fy in ((1, 1), (FW - 2, 1), (5, 8), (FW - 6, 8), (9, 12), (FW - 10, 12), (1, 11), (FW - 2, 11)):
        put('Tops', fx, fy, 'toro-hang')
    for fx, fy in ((8, 6), (13, 9), (3, 10), (17, 12)):
        put('Tops', fx, fy, 'haze')

    # ---- the door ---------------------------------------------------------------------------------------
    exits = [rg.transporter(OX + DOOR_X + i, OY + FH, HOST, front[0], front[1], hidden=True)
             for i, (_, front) in enumerate(doors)]
    room = b.room(NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []), transporters=exits)
    # the floor plus the two doorway cells; the walls round it need no colliders
    room['boundary'] = [
        [OX, OY], [OX + FW, OY], [OX + FW, OY + FH], [OX + DOOR_X + 2, OY + FH], [OX + DOOR_X + 2, OY + FH + 1],
        [OX + DOOR_X, OY + FH + 1], [OX + DOOR_X, OY + FH], [OX, OY + FH],
    ]
    # whose hall this is: the marker roomgen.owned_door reads, as a house's `house` is
    room['temple'] = {'host': HOST, 'doors': [list(door) for door, _ in doors]}
    room['interior'] = True          # never offered to the blog pipeline; no day/night grade...
    room['lanternLight'] = True      # ...but at night it dims and its lights glow (DayNight, Glows)
    room['shopEnabled'] = False      # not a konbini
    # arrive just inside the leaf you came through
    return room, [(OX + DOOR_X + i, OY + FH - 1) for i in range(2)]


doors = leaves()
room, arrive = build(doors)
cfg['rooms'][KEY] = room
host = cfg['rooms'][HOST]
ts = host.setdefault('transporters', [])
for ((dx, dy), front), cell in zip(doors, arrive):
    for layer in host['layers']:
        if layer['name'] == 'Colliders':
            layer['tiles'].pop(f'{dx},{dy}', None)          # unseal the doorway
    door = rg.transporter(dx, dy, KEY, *cell, hidden=True)
    at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == (dx, dy)]
    if at:                                                  # in place: a re-run changes nothing
        ts[at[0]] = door
        for i in reversed(at[1:]):
            del ts[i]
    else:
        ts.append(door)
    print(f'door   {HOST} {(dx, dy)} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
