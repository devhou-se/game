#!/usr/bin/env python3
"""generate_flinders.py — the concourse inside the station with the clocks in
San Franbourne (issue #246).

The station is one sprite on the map (`sfb-clocks-station`, 12x7), sealed
until now. The two door cells under its clocks open into this room, and each
mat inside puts you back on the boardwalk in front of the door above it.

As tools/generate_mall.py does for Canal City, the building is found by its
sprite (roomgen.FLINDERS_DOORS), wherever the town's generator stands it: the
collider on each door cell is removed and a hidden transporter is wired onto
it (replaced in place, so a re-run leaves config.json byte-identical).
tools/generate_sanfranbourne.py is not edited and knows nothing about the
doors: roomgen.OWNED_DOORS keeps them through a rebuild of the town for as
long as the station stands where it stood. If the town's rebuild moves it,
the town generator leaves it sealed and this tool must be run again (then
config_to_tiled): it finds the building and wires the doors anew.
The room is rebuilt from scratch (any NPCs it holds are kept).

Inside (24x18; art: tools/generate_flinders_art.py, and the station kit of
tools/generate_station_art.py for the track, the gates, the railing, the
benches and the planters) is a station nobody catches a train from:
  * the back wall, three rows tall, in the building's mustard and maroon:
    arched windows either side of the name board;
  * the track under it, two rows, solid from end to end and empty: no train
    stops, the room is on no departures board and San Franbourne is still
    reached only by air;
  * the platform, with two benches facing the track;
  * the gate line: two banks of ticket gates, the only ways onto the
    platform, either side of the clocks - the board of nine dials from over
    the door outside, here on two posts (bump it: Time Travel, as every clock);
    the ticket machines against the west wall and the departures board
    against the east one (bump them);
  * the concourse: terrazzo, pillars, benches, planters either side of the
    doorway, the daylight through it.
The room is `interior` (never offered to the blog pipeline) and not
`lanternLight`: a concourse is as bright at night.

Run from gamev2/:  python3 tools/generate_flinders.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py FlindersSanFranbourne1 SanFranbourne
       node tools/play.js lint FlindersSanFranbourne1 SanFranbourne
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'SanFranbourne'
KEY = f'{rg.FLINDERS_PREFIX}{HOST}1'
NAME = 'Flinders St'      # 11 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 20, 11           # the floor, in cells
OX, OY = 2, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
WALL = 3                  # the back wall's rows
TRACK = (0, 1)            # the track's two rows, under the back wall
EDGE = 2                  # the platform's edge; the platform is the two rows below it
GATE_ROW = 5              # the gate line: the last row of the platform's floor
DOOR_X = 9                # the doorway: floor columns 9 and 10
BANKS = (4, 12)           # each bank of gates: its west end's column, two gates, its east end
CLOCKS = 8                # the clocks' west column; four cells wide, between the banks
RAILING = (3, 16)         # the cell of tube railing outside each bank
PLATFORM_BENCHES = (1, 17)                                         # foot row 4, facing the track
PILLARS = (6, 13)                                                  # foot row 8
BENCHES = (3, 15)                                                  # foot row 9
PLANTERS = ((6, 'station-planter-a'), (12, 'station-planter-b'))   # foot row 10, either side of the doorway


def build(doors):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'flinders-in-{piece}_0_0'
    station = lambda piece: f'{piece}_0_0'                          # the station kit (tools/generate_station_art.py)

    # ---- the floor: ballast, the platform's edge, the platform, then the concourse's terrazzo --
    def floor(fx, fy):
        if fy <= TRACK[1]:
            return station('station-ballast')
        if fy == EDGE:
            return station('station-platform-edge')
        if fy <= GATE_ROW:
            return station('station-floor')
        return s('floor-a' if fx % 2 == 0 and fy % 2 == 0 else 'floor-b')
    it.floor(floor)
    it.side_walls(s('side-w'), s('side-e'), WALL)

    # ---- the front wall and the doorway ---------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('threshold-w'), s('threshold-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))

    # ---- the back wall: a bay, a window, the name board, a window, a bay ----------------------
    it.back_wall([(0, s('wall-bay'), 3), (3, s('wall-arch'), 4), (7, s('wall-name'), 6),
                  (13, s('wall-arch'), 4), (17, s('wall-bay'), 3)], WALL)

    # ---- the track: empty, and in the way from end to end (Interior.room seals no track) -------
    for fx in range(FW):
        it.put('Over Floor', fx, TRACK[0], station('station-track-n'))
        it.put('Over Floor', fx, TRACK[1], station('station-track-s'))
    it.solid(0, TRACK[0], FW, 2)

    # ---- the platform: benches facing the track -----------------------------------------------
    for fx in PLATFORM_BENCHES:
        it.stand(station('station-bench-back'), fx, GATE_ROW - 1, w=2)

    # ---- the gate line: machines, railing, gates, the clocks, gates, railing, the board --------
    it.prop(s('tickets'), 0, GATE_ROW, 3, 2)
    it.prop(s('board'), FW - 3, GATE_ROW, 3, 2)
    for west in BANKS:                                              # a gate is 1x2: drawn from the row above
        it.place('Collidables', west, GATE_ROW - 1, station('station-gate-end-w'), [(0, 1)])
        for fx in (west + 1, west + 2):
            it.put('Other', fx, GATE_ROW - 1, station('station-gate'))      # walked through: no collider
        it.place('Collidables', west + 3, GATE_ROW - 1, station('station-gate-end-e'), [(0, 1)])
    it.stand(s('clocks'), CLOCKS, GATE_ROW, w=4, h=3)               # its foot row in the way, its head walked behind
    # railing_row runs the whole width of the room, void and all: everything but the two cells is taken
    it.b.railing_row(it.oy + GATE_ROW, set(range(it.b.W)) - {it.ox + fx for fx in RAILING})

    # ---- the concourse: pillars, benches, planters either side of the doorway ------------------
    for fx in PILLARS:
        it.stand(station('station-pillar'), fx, 8)
    for fx in BENCHES:
        it.stand(station('station-bench'), fx, 9, w=2)
    for fx, piece in PLANTERS:
        it.stand(station(piece), fx, FH - 1, w=2)

    # ---- the doors: each mat leads out to the cell in front of the door above it ---------------
    assert len(doors) == 2 and doors[1][0][0] == doors[0][0][0] + 1, doors
    inside = it.doorway(DOOR_X, HOST, [front for _, front in doors])
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose room this is: the marker roomgen.owned_door reads, as a house's `house` is
        flinders={'host': HOST, 'doors': [list(door) for door, _ in doors]},
        # no lanternLight: a concourse is lit. Nothing is sold here and no train is caught: not a config.stations room
        shopEnabled=False)
    # room() has held every open floor cell to be reachable from the doors; the gates are how you reach the platform
    for west in BANKS:
        assert all(it.cell(fx, GATE_ROW) in it.reached for fx in (west + 1, west + 2)), f'{KEY}: gates at {west} blocked'
    return room, inside


doors = rg.sprite_doors(cfg, HOST, rg.FLINDERS_DOORS)
assert len(doors) == 2, f'{HOST}: expected exactly one station with two door cells ({list(rg.FLINDERS_DOORS)}), found {len(doors)} doors'
room, arrive = build(doors)
cfg['rooms'][KEY] = room
for (door, front), cell in zip(doors, arrive):
    rg.open_door(cfg['rooms'][HOST], door, KEY, cell)       # unsealed, wired in place: a re-run changes nothing
    print(f'door   {HOST} {door} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
