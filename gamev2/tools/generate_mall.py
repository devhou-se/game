#!/usr/bin/env python3
"""generate_mall.py — the atrium inside Canal City in Fukuoka (issue #217).

Canal City is one sprite on the map (`canal-city`, 8x6), sealed until now. The
two leaves of the door under its arch open into this room, and each mat inside
puts you back on the cell in front of the leaf above it.

As tools/generate_pub.py does for the pub, the building is found by its sprite
(roomgen.MALL_DOORS), wherever the town's generator stands it: the collider on
each door cell is removed and a hidden transporter is wired onto it (replaced
in place, so a re-run leaves config.json byte-identical).
tools/generate_fukuoka.py is not edited and knows nothing about the doors:
roomgen.OWNED_DOORS keeps them through a rebuild of the town for as long as
the mall stands where it stood. If the town's rebuild moves it, the town
generator leaves it sealed and this tool must be run again (then
config_to_tiled): it finds the building and wires the doors anew.
rooms.MallFukuoka1 is rebuilt from scratch (any NPCs it holds are kept).

Inside (28x23; art: tools/generate_mall_art.py) is a bright atrium, not a mall
to shop in:
  * the back wall, five rows tall: five shopfronts between piers (bump one
    for a line about it), and over them two gallery levels of curved
    terracotta balconies and small lit fronts. The camera looks up at it from
    the north bank (game.lookUp.sprites, written by the art tool: issue #258);
  * the canal through the middle of the floor, three rows of it, the same
    water and quays as the canal outside. It is drawn, not `pond-autotile`:
    nobody fishes indoors. Solid, except under the two bridges;
  * the two footbridges, lying flat (Non-Collidables, depthBias -200): the
    only ways across;
  * the fountain, standing in the canal between them (bump it);
  * benches on both banks facing the water, palms in tubs, planters at the
    ends of the south row and either side of the door: the station's benches
    and planters, each 2x2 with its lower row in the way.
The room is `interior` (never offered to the blog pipeline) and, unlike the
pub and the distillery, not `lanternLight`: an atrium is as bright at night.

Run from gamev2/:  python3 tools/generate_mall.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py MallFukuoka1 Fukuoka
       node tools/play.js lint MallFukuoka1 Fukuoka
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Fukuoka'
KEY = f'{rg.MALL_PREFIX}{HOST}1'
NAME = 'Canal City'       # under 12 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 26, 14           # the floor, in cells
OX, OY = 1, 6             # room cell of floor cell (0, 0): a 5-row back wall under one row of dark
WALL = 5                  # the back wall's rows: two gallery levels over the ground floor
DOOR_X = 12               # the doorway: floor columns 12 and 13
FRONTS = ('fashion', 'toys', 'okonomiyaki', 'cafe', 'ramen')       # west to east, a pier between each
CANAL = 5                 # the canal's north row; three rows of it
BRIDGES = (4, 20)         # each bridge's west column; two cells wide
FOUNTAIN = 11             # the fountain's west column; four cells wide
PALMS = ((2, 3), (23, 3), (8, 9), (17, 9))                         # each palm's foot
NORTH_BENCHES = (7, 17)                                            # foot row 3, facing the water
SOUTH_ROW = ((0, 'station-planter-a'), (2, 'station-bench-back'), (6, 'station-bench-back'), (9, 'station-bench-back'),
             (15, 'station-bench-back'), (18, 'station-bench-back'), (22, 'station-bench-back'), (24, 'station-planter-b'))
BANK = 9                  # the south row's foot row


def build(doors):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'mall-in-{piece}_0_0'
    station = lambda piece: f'{piece}_0_0'                          # the station's 2x2 benches and planters: the foot row in the way

    # ---- the floor and the side walls ---------------------------------------------------
    it.floor(lambda fx, fy: s('floor-a' if (fx + fy) % 2 == 0 else 'floor-b'))
    it.side_walls(s('side-w'), s('side-e'), WALL)

    # ---- the front wall and the doorway ---------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('threshold-w'), s('threshold-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))

    # ---- the back wall: a pier, a shopfront, a pier ... under the galleries -------------------
    it.back_wall([(n * 5, s('wall-pier'), 1) for n in range(len(FRONTS) + 1)] +
                 [(n * 5 + 1, s(f'front-{name}'), 4) for n, name in enumerate(FRONTS)], WALL)

    # ---- the canal: on the Water layer, as a pond is; in the way except under the bridges -------
    under = {x for west in BRIDGES for x in (west, west + 1)}
    for fx in range(FW):
        if FOUNTAIN <= fx < FOUNTAIN + 4:
            continue
        for dy, row in enumerate(('canal-n', 'canal', 'canal-s')):
            it.put('Water', fx, CANAL + dy, s(f"{row}-{'ab'[fx % 2]}"))
            if fx not in under:
                it.solid(fx, CANAL + dy)
    for west in BRIDGES:
        it.put('Non-Collidables', west, CANAL, s('bridge'))
    it.prop(s('fountain'), FOUNTAIN, CANAL, 4, 3)

    # ---- the banks: benches facing the water, palms, planters ---------------------------------
    for fx in NORTH_BENCHES:
        it.stand(station('station-bench'), fx, 3, w=2)
    for fx, piece in SOUTH_ROW:
        it.stand(station(piece), fx, BANK, w=2)
    it.stand(station('station-planter-a'), DOOR_X - 2, FH - 1, w=2)   # either side of the door
    it.stand(station('station-planter-b'), DOOR_X + 2, FH - 1, w=2)
    for fx, foot in PALMS:
        it.stand(s('palm'), fx, foot)

    # ---- the doors: each mat leads out to the cell in front of the leaf above it ---------------
    assert len(doors) == 2 and doors[1][0][0] == doors[0][0][0] + 1, doors
    inside = it.doorway(DOOR_X, HOST, [front for _, front in doors])
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose room this is: the marker roomgen.owned_door reads, as a house's `house` is
        mall={'host': HOST, 'doors': [list(door) for door, _ in doors]},
        # no lanternLight: an atrium is lit. Nothing is sold here: the shopfronts are flavour (Interactions)
        shopEnabled=False)
    # room() has held every open floor cell to be reachable from the doors; the bridges are how: both stay open
    for west in BRIDGES:
        assert all(it.cell(west + dx, CANAL + dy) in it.reached for dx in range(2) for dy in range(3)), f'{KEY}: bridge at {west} blocked'
    return room, inside


doors = rg.sprite_doors(cfg, HOST, rg.MALL_DOORS)
assert len(doors) == 2, f'{HOST}: expected exactly one Canal City with two door leaves ({list(rg.MALL_DOORS)}), found {len(doors)} doors'
room, arrive = build(doors)
cfg['rooms'][KEY] = room
for (door, front), cell in zip(doors, arrive):
    rg.open_door(cfg['rooms'][HOST], door, KEY, cell)       # unsealed, wired in place: a re-run changes nothing
    print(f'door   {HOST} {door} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
