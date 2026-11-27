#!/usr/bin/env python3
"""generate_tower_deck.py — the observation deck up Fukuoka Tower (issue #242).

Fukuoka Tower is one sprite on the map (`fukuoka-tower`, 4x12), sealed until
now. The two leaves of the door in its foot open into this room, 123 m up, and
each cell of the lift's sill inside puts you back on the cell in front of the
leaf above it. The ride between the two is not this tool's: a door into a room
that carries the `deck` marker is a lift (RoomManager.liftFor), and the game
plays the way up and the way down (src/ViewRide.js).

As tools/generate_mall.py does for Canal City, the tower is found by its sprite
(roomgen.DECK_DOORS), wherever the town's generator stands it: the collider on
each door cell is removed and a hidden transporter is wired onto it (replaced
in place, so a re-run leaves config.json byte-identical).
tools/generate_fukuoka.py is not edited and knows nothing about the doors:
roomgen.OWNED_DOORS keeps them through a rebuild of the town for as long as
the tower stands where it stood. If the town's rebuild moves it, the town
generator leaves it sealed and this tool must be run again (then
config_to_tiled): it finds the tower and wires the doors anew.
rooms.DeckFukuoka1 is rebuilt from scratch (any NPCs it holds are kept).

Inside (20x15; art: tools/generate_tower_deck_art.py) is one long room:
  * the back wall, five rows tall, is glass from the floor up: six panes of
    one view north over Hakata Bay, the view the lift came up through (bump a
    pane for a line about it). It is inside the room's boundary (view=True),
    so a phone's camera shows all of it;
  * three coin-operated binoculars and the lovers' fence of padlocks along
    the glass, a brass map of the bay on a plinth, the sign by the lift (bump
    any of them), and two benches;
  * pendant lamps over the middle of the floor;
  * the lift in the front wall: its sill is the doorway, two cells wide.
The room is `interior` (never offered to the blog pipeline) and `daylight`:
its light is the sky's, so it is graded by the hour as the street is and its
lamps and the lights of the town below come on at night (DayNight.gradeFor).

Run from gamev2/:  python3 tools/generate_tower_deck.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py DeckFukuoka1 Fukuoka
       node tools/play.js lint DeckFukuoka1 Fukuoka
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Fukuoka'
KEY = f'{rg.DECK_PREFIX}{HOST}1'
NAME = 'Tower Deck'       # under 12 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 18, 6            # the floor, in cells
OX, OY = 1, 6             # room cell of floor cell (0, 0): a 5-row back wall under one row of dark
WALL = 5                  # the back wall's rows: glass, floor to ceiling
PANES = 6                 # of the back wall, each three cells wide
DOOR_X = 8                # the lift: floor columns 8 and 9
BINOCULARS = (2, 6, 11)   # each viewer's column, against the glass
LOCKS = 15                # the padlock fence's west column; two cells wide, against the glass
COMPASS = (1, 3)          # the brass map's plinth; two cells wide
BENCHES = ((5, 3), (11, 3))                                        # two cells wide each, facing the glass
SIGN = DOOR_X + 2         # the sign's column, beside the lift
LAMPS = ((3, 3), (7, 3), (10, 3), (14, 3))                         # the cell under each pendant lamp


def build(doors):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'deck-in-{piece}_0_0'

    # ---- the floor and the side walls ---------------------------------------------------
    it.floor(lambda fx, fy: s('floor-a' if (fx + fy) % 2 == 0 else 'floor-b'))
    it.side_walls(s('side-w'), s('side-e'), WALL)

    # ---- the front wall and the lift in it ------------------------------------------------
    it.front_wall(s('wall-front'), (DOOR_X, DOOR_X + 1), (s('lift-w'), s('lift-e')))
    it.put('Non-Collidables', DOOR_X, FH - 3, s('doorlight'))
    it.stand(s('lift-sign'), SIGN, FH - 1)

    # ---- the back wall: six panes of one view, inside the boundary so a phone shows all of it ----
    it.back_wall([(n * 3, s(f'window-{n + 1}'), 3) for n in range(PANES)], WALL, view=True)

    # ---- along the glass: the viewers and the padlocks; on the floor: the map, the benches ------
    for fx in BINOCULARS:
        it.stand(s('binoculars'), fx, 0)
    it.stand(s('locks'), LOCKS, 0, w=2)
    it.prop(s('compass'), *COMPASS, 2, 1)
    for fx, fy in BENCHES:
        it.prop(s('bench'), fx, fy, 2, 1)
    for fx, fy in LAMPS:
        it.put('Tops', fx, fy - 2, s('downlight'))

    # ---- the lift: each cell of its sill leads down to the cell in front of the leaf above it ----
    assert len(doors) == 2 and doors[1][0][0] == doors[0][0][0] + 1, doors
    inside = it.doorway(DOOR_X, HOST, [front for _, front in doors])
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose room this is: the marker roomgen.owned_door reads, as a house's `house` is - and
        # what makes the door into it a lift (RoomManager.liftFor)
        deck={'host': HOST, 'doors': [list(door) for door, _ in doors]},
        # its light is the sky's: graded by the hour as the street is (DayNight.gradeFor).
        # Nothing is sold here: what stands on the floor is flavour (Interactions)
        daylight=True, shopEnabled=False)
    return room, inside


doors = rg.sprite_doors(cfg, HOST, rg.DECK_DOORS)
assert len(doors) == 2, f'{HOST}: expected exactly one Fukuoka Tower with two door leaves ({list(rg.DECK_DOORS)}), found {len(doors)} doors'
room, arrive = build(doors)
cfg['rooms'][KEY] = room
for (door, front), cell in zip(doors, arrive):
    rg.open_door(cfg['rooms'][HOST], door, KEY, cell)       # unsealed, wired in place: a re-run changes nothing
    print(f'door   {HOST} {door} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
