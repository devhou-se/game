#!/usr/bin/env python3
"""generate_distillery.py — the tasting bar inside the Nikka distillery in Sendai (issue #217).

The distillery is the red brick kiln the trip went out to on the Sakunami day:
one sprite on the map (`sendai-kiln`, 5x6), sealed until now. Its door, in the
middle of its front under the WHISKY sign, opens into this room, and the mat
inside puts you back on the cell in front of the door.

As tools/generate_pub.py does for the pub, the building is found by its sprite
(roomgen.DISTILLERY_DOORS), wherever the town's generator stands it: the
collider on the door cell is removed and a hidden transporter is wired onto it
(replaced in place, so a re-run leaves config.json byte-identical).
tools/generate_sendai.py is not edited and knows nothing about the door:
roomgen.OWNED_DOORS keeps it through a rebuild of the town for as long as the
kiln stands where it stood. If the town's rebuild moves the kiln, the town
generator leaves it sealed and this tool must be run again (then
config_to_tiled): it finds the building and wires the door anew.
rooms.DistillerySendai1 is rebuilt from scratch (any NPCs it holds are kept).

Inside (20x15; art: tools/generate_distillery_art.py) is a small tasting bar:
  * the back wall: casks racked three high, the kiln's two arched windows,
    the bottles behind the counter under the sign;
  * the one copper pot still, on its brick hearth: its two lower rows are
    solid, the swan neck and the lyne arm are walked behind. Bump it;
  * the tasting counter, flush to the east wall under the bottles: the
    staff's aisle behind it, three flights poured on it, stools in front.
    Bump it to order (Shop.VENUES.tasting: a Highball, no stamp);
  * casks stood on end by the side walls (bump them), copper lamps hung over
    the counter and either side of the still.
The room is `interior` (never offered to the blog pipeline) and `lanternLight`:
at night it dims and its lamps and windows glow (DayNight; their spots are
rows of src/utils/Glows.js).

Run from gamev2/:  python3 tools/generate_distillery.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py DistillerySendai1 Sendai
       node tools/play.js lint DistillerySendai1 Sendai
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Sendai'
KEY = f'{rg.DISTILLERY_PREFIX}{HOST}1'
NAME = 'Distillery'       # under 12 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 18, 8            # the floor, in cells
OX, OY = 1, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
DOOR_X = 8                # the doorway: floor columns 8 and 9
STILL = 4                 # the still's west column: three cells wide, four rows tall
COUNTER = 5               # the counter's length, to the east wall
CASKS = ((0, 4), (1, 4), (0, 6), (16, 5), (17, 5), (17, 7))


def build(door, front):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'distillery-in-{piece}_0_0'

    # ---- the floor and the side walls ---------------------------------------------------
    it.floor(lambda fx, fy: s('floor-a' if (fx + fy) % 2 == 0 else 'floor-b'))
    it.side_walls(s('side-w'), s('side-e'), 3)

    # ---- the front wall and the doorway ---------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('threshold-w'), s('threshold-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))

    # ---- the back wall: racked casks, brick, the windows, the bottles behind the counter ------
    it.back_wall([(fx, s(piece), w) for fx, piece, w in (
        (0, 'wall-casks', 4), (4, 'wall-brick', 1), (5, 'wall-brick', 1), (6, 'wall-brick', 1),
        (7, 'wall-window', 2), (9, 'wall-brick', 1), (10, 'wall-brick', 1), (11, 'wall-brick', 1),
        (12, 'wall-brick', 1), (FW - COUNTER, 'wall-shelf', COUNTER))], 3)

    # ---- the still: the pot and the condenser are in the way, the neck is walked behind -------
    it.place('Collidables', STILL, 0, s('still'), rg.block(3, 4, 2))

    # ---- the counter: flush to the east wall, so nobody stands on the staff's side ------------
    it.prop(s('counter'), FW - COUNTER, 0, COUNTER, 2)
    for fx in (FW - 4, FW - 2):                                     # stools; the cells between are left to reach the counter
        it.prop(s('stool'), fx, 2)

    # ---- casks stood on end -------------------------------------------------------------------
    for fx, fy in CASKS:
        it.prop(s('cask'), fx, fy)

    # ---- overhead: lamps over the counter, either side of the still, and in the middle ---------
    for fx, fy in ((FW - 4, -1), (FW - 2, -1), (STILL - 1, -1), (STILL + 3, -1), (10, 3)):
        it.put('Tops', fx, fy, s('lamp-hang'))

    # ---- the door: a mat two cells wide, both back out to the cell in front of the door ---------
    inside = it.doorway(DOOR_X, HOST, front)
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose room this is: the marker roomgen.owned_door reads, as a house's `house` is
        distillery={'host': HOST, 'doors': [list(door)]},
        lanternLight=True,           # at night it dims and its lights glow (DayNight, Glows)
        shopEnabled=False)           # not a konbini: the counter is its own rule (Interactions, Shop.VENUES.tasting)
    return room, inside[0]


doors = rg.sprite_doors(cfg, HOST, rg.DISTILLERY_DOORS)
assert len(doors) == 1, f'{HOST}: expected exactly one kiln ({list(rg.DISTILLERY_DOORS)}), found {len(doors)}'
(door, front), = doors
room, arrive = build(door, front)
cfg['rooms'][KEY] = room
rg.open_door(cfg['rooms'][HOST], door, KEY, arrive)         # unsealed, wired in place: a re-run changes nothing
print(f'door   {HOST} {door} -> {KEY} {arrive}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
