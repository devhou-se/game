#!/usr/bin/env python3
"""generate_pub.py — the inside of the pub in Sendai (issue #217).

The pub is the building the trip watched the baseball in: one sprite on the
map (`sendai-pub`, 5x5), sealed until now. Its door, in the middle of its
front, opens into this room, and the mat inside puts you back on the cell in
front of the door.

The building is found by its sprite (roomgen.PUB_DOORS), wherever the town's
generator stands it: the collider on the door cell is removed and a hidden
transporter is wired onto it (roomgen.open_door: replaced in place, so a
re-run leaves config.json byte-identical). tools/generate_sendai.py is not edited and knows
nothing about the door: roomgen.OWNED_DOORS keeps it through a rebuild of the
town for as long as the building stands where it stood. If the town's rebuild
moves the pub, the town generator leaves it sealed and this tool must be run
again (then config_to_tiled): it finds the building and wires the door anew.
rooms.PubSendai1 is rebuilt from scratch on the shared shell, tools/interiors.py
(any NPCs it holds are kept).

Inside (20x17; art: tools/generate_pub_art.py) is a proper pub:
  * the back wall: the back bar (mirrors, bottles, optics), the big screen
    with the baseball on, the dartboard, framed prints between them;
  * the bar, flush to the west wall under the back bar: the staff's aisle
    behind it, three sets of taps and the till on it, stools in front. Bump
    it to order (Shop.VENUES.taproom: the izakaya's list, no stamp);
  * tables with chairs, two booths back to back on the east wall, the
    specials on a chalkboard, green glass lamps hung over the bar and tables.
The room is `interior` (never offered to the blog pipeline) and `lanternLight`:
at night it dims and its lamps, the back bar and the screen glow (DayNight;
their spots are rows of src/utils/Glows.js).

Run from gamev2/:  python3 tools/generate_pub.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py PubSendai1 Sendai
       node tools/play.js lint PubSendai1 Sendai
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Sendai'
KEY = f'{rg.PUB_PREFIX}{HOST}1'
NAME = 'The Pub'          # under 12 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 18, 10           # the floor, in cells
OX, OY = 1, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
DOOR_X = 8                # the doorway: floor columns 8 and 9
BAR = 7                   # the bar's length, from the west wall
TABLES = ((3, 5), (3, 8), (12, 4), (11, 7))     # the west cell of each table


def build(door, front):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'pub-in-{piece}_0_0'

    # ---- the floor and the side walls ---------------------------------------------------
    it.floor(lambda fx, fy: s('floor-a' if (fx + fy // 2) % 2 == 0 else 'floor-b'))
    it.side_walls(s('side-w'), s('side-e'), 3)

    # ---- the front wall and the doorway ---------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('threshold-w'), s('threshold-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))

    # ---- the back wall: the back bar, prints, the screen, the dartboard -----------------------
    it.back_wall([(fx, s(piece), w) for fx, piece, w in (
        (0, 'wall-backbar', BAR), (7, 'wall-panel', 1), (8, 'wall-print', 1), (9, 'wall-panel', 1),
        (10, 'wall-tv', 4), (14, 'wall-print', 1), (15, 'wall-darts', 2), (17, 'wall-print', 1))], 3)

    # ---- the bar: flush to the west wall, so nobody stands on the staff's side ------------------
    it.prop(s('bar'), 0, 0, BAR, 2)
    for fx in (1, 3, 5):                                            # stools; 0, 2, 4, 6 are left to reach the bar
        it.prop(s('stool'), fx, 2)

    # ---- tables, a chair each side ----------------------------------------------------------------
    for fx, fy in TABLES:
        it.prop(s('table'), fx, fy, 2)
        it.prop(s('chair-w'), fx - 1, fy)
        it.prop(s('chair-e'), fx + 2, fy)

    # ---- the booths on the east wall, back to back, solid throughout ---------------------------------
    for fy in (3, 6):
        it.prop(s('booth'), FW - 2, fy, 2, 3)

    # ---- the specials: its head is walked behind --------------------------------------------------------
    it.stand(s('chalkboard'), 0, 8)

    # ---- overhead: lamps over the bar (between the taps) and over each table ----------------------------
    for fx in (0, 2, 4, 6):
        it.put('Tops', fx, -2, s('lamp-hang'))
    for fx, fy in TABLES:
        it.put('Tops', fx, fy - 2, s('lamp-hang'))

    # ---- the door: a mat two cells wide, both back out to the cell in front of the door -------------------
    inside = it.doorway(DOOR_X, HOST, front)
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose room this is: the marker roomgen.owned_door reads, as a house's `house` is
        pub={'host': HOST, 'doors': [list(door)]},
        lanternLight=True,           # at night it dims and its lights glow (DayNight, Glows)
        shopEnabled=False)           # not a konbini: the bar is its own rule (Interactions, Shop.VENUES.taproom)
    return room, inside[0]


doors = rg.sprite_doors(cfg, HOST, rg.PUB_DOORS)
assert len(doors) == 1, f'{HOST}: expected exactly one pub ({list(rg.PUB_DOORS)}), found {len(doors)}'
(door, front), = doors
room, arrive = build(door, front)
cfg['rooms'][KEY] = room
rg.open_door(cfg['rooms'][HOST], door, KEY, arrive)         # unsealed, wired in place: a re-run changes nothing
print(f'door   {HOST} {door} -> {KEY} {arrive}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
