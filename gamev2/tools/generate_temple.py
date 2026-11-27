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
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Market'
KEY = f'{rg.TEMPLE_PREFIX}{HOST}1'
NAME = 'Senso-ji'         # 8 characters: a phone's one-row HUD bar fits the countdown beside it
FW, FH = 24, 15           # the floor, in cells
OX, OY = 1, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
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
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'temple-in-{piece}_0_0'

    # ---- the floor and the side walls ---------------------------------------------------
    it.floor(lambda fx, fy: s('slab-a' if (fx * 3 + fy * 5 + fx // 3) % 4 else 'slab-b'))
    it.side_walls(s('side-w'), s('side-e'), 3)
    for fy in (5, 9, 13):                                           # a little day through the slats
        it.put('Over Floor', 0, fy, s('sun-w'))
        it.put('Over Floor', FW - 2, fy, s('sun-e'))

    # ---- the front wall and the doorway ---------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('threshold-w'), s('threshold-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))

    # ---- the back wall: charms, the sanctum's wall and cabinet, the fortune drawers ----------
    it.back_wall([(fx, s(piece), w) for fx, piece, w in (
        (0, 'wall-charms', 4), (4, 'wall-tennin-l', 5), (9, 'kuden', 6), (15, 'wall-tennin-r', 5), (20, 'omikuji', 4))], 3)

    # ---- the inner sanctum behind its lattice ---------------------------------------------------
    sx, sw, sd = SANCTUM
    it.prop(s('naijin'), sx, 0, sw, sd)

    # ---- down the middle: the offering box, the incense burner, the great lantern -----------------
    it.prop(s('saisen'), DOOR_X - 1, 4, 4, 2)
    it.stand(s('jokoro'), DOOR_X - 1, 9, w=4, h=3)
    it.solid(DOOR_X, 8, 2)                                          # the bowl is two rows deep in the middle
    it.put('Tops', DOOR_X - 1, 11, s('chochin'))

    # ---- columns: two rows of four, only their feet solid -------------------------------------------
    for fx in (3, 7, 16, 20):
        for foot in (7, 12):
            it.stand(s('pillar'), fx, foot, h=3)

    # ---- before the lattice: candles by the box, the drum to the west, the bowl bell to the east ------
    it.stand(s('shokudai'), DOOR_X - 2, 5)
    it.stand(s('shokudai'), DOOR_X + 3, 5)
    it.stand(s('drum'), 5, 5, w=2)
    it.stand(s('keisu'), 17, 5, w=2)

    # ---- the aisles ---------------------------------------------------------------------------------
    it.stand(s('candles'), 0, 9, w=2)                               # votive candles on the west wall
    it.stand(s('musubi'), FW - 2, 9, w=2)                           # the tied fortunes on the east
    it.stand(s('shokudai'), 1, 14)
    it.stand(s('shokudai'), FW - 2, 14)
    it.stand(s('renge'), DOOR_X - 2, 14)                            # gilt lotus either side of the doors
    it.stand(s('renge'), DOOR_X + 3, 14)
    for fx in (4, FW - 6):                                          # a bench each side, for the footsore
        it.prop(s('bench'), fx, 14, 2)

    # ---- overhead: hung lanterns, and the haze ----------------------------------------------------------
    for fx, fy in ((1, 1), (FW - 2, 1), (5, 8), (FW - 6, 8), (9, 12), (FW - 10, 12), (1, 11), (FW - 2, 11)):
        it.put('Tops', fx, fy, s('toro-hang'))
    for fx, fy in ((8, 6), (13, 9), (3, 10), (17, 12)):
        it.put('Tops', fx, fy, s('haze'))

    # ---- the door: a threshold under each leaf, and you arrive just inside the one you came through ------
    inside = it.doorway(DOOR_X, HOST, [front for _, front in doors])
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose hall this is: the marker roomgen.owned_door reads, as a house's `house` is
        temple={'host': HOST, 'doors': [list(door) for door, _ in doors]},
        lanternLight=True,           # at night it dims and its lights glow (DayNight, Glows)
        shopEnabled=False)           # not a konbini
    return room, inside


doors = leaves()
room, arrive = build(doors)
cfg['rooms'][KEY] = room
for (door, front), cell in zip(doors, arrive):
    rg.open_door(cfg['rooms'][HOST], door, KEY, cell)       # unsealed, wired in place: a re-run changes nothing
    print(f'door   {HOST} {door} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
