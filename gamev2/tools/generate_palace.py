#!/usr/bin/env python3
"""generate_palace.py — the audience hall inside the palace (issue #215).

What "the palace" is on the map: inside the moat of the Tokyo district `Tokyo`
(display name "Imperial Palace") stands one long blue-roofed building - a
central hall, a `temple-hallway` wing either side of it and a three-storey
tower (`pagoda-roof` over `pagoda-floor`) at each end. The central hall is the
`shrine` prefab and already opens into its worship hall ("Palace Shrine",
tools/generate_shrines.py); the wings and towers were sealed. Each tower has a
door at its foot, and those two doors are the palace's: both lead into ONE
interior, the hall the wings are the outside of. You come in at the foot of a
side corridor and leave by the door you choose - the west door puts you back
in front of the west tower, the east door in front of the east one.

The district is a ported map with no generator, so its map is the source of
truth and this tool changes exactly two things in it, the way
generate_shrines.py does for a ported host: the collider on each door cell is
removed and a hidden transporter is wired onto it (replaced in place, so a
re-run leaves config.json byte-identical). rooms.PalaceHallTokyo1 is rebuilt
from scratch (any NPCs it holds are kept).

Inside (26x22; art: tools/generate_palace_art.py) is an Edo audience hall:
  * the back wall under the edge of a coffered ceiling: gold-leaf screens
    painted as one picture, an old pine and cranes, with staggered shelves to
    the left of them and tasselled lacquer doors to the right;
  * the jodan, a matted floor one step up, with the lord's empty seat (bump
    it to ask for an audience: src/PalaceVisit.js), a suit of armour on one
    side of it and a rack of swords on the other;
  * a tatami hall with the retainers' cushions set out in rows, vermilion and
    black lacquer pillars you walk behind, gilt lamps hung over it;
  * a side corridor (engawa) of polished boards down each side, daylight
    coming through its paper screens;
  * a long corridor across the front, between the two doors, walled off from
    the hall by painted screens you also walk behind - a tiger in bamboo to
    the west, waves and plovers to the east - with the way into the hall
    between them;
  * in that corridor: by the west door the visitors' book (sign it, once a
    game day) and the guard's rack of polearms; at the east end a waiting
    room behind a folding screen, tea set out on a low table.
The room is `interior` (never offered to the blog pipeline) and `lanternLight`:
at night it dims and its lamps glow (DayNight; their spots are rows of
src/utils/Glows.js).

Run from gamev2/:  python3 tools/generate_palace.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py PalaceHallTokyo1 Tokyo
       node tools/play.js lint PalaceHallTokyo1 Tokyo
(.agent-queue/items/palace_apply.sh does all of it, and the gates.)
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

HOST = 'Tokyo'
KEY = f'{rg.PALACE_PREFIX}{HOST}1'
NAME = 'Palace Hall'      # 11 characters: a phone's one-row HUD bar still fits the countdown beside it
FW, FH = 24, 15           # the floor, in cells
OX, OY = 1, 4             # room cell of floor cell (0, 0): a 3-row back wall under one row of dark
HALL = 10                 # rows of the hall (fy 0..9); the screens stand on fy 10..11, the corridor is fy 12..14
GAP = (10, 13)            # the way through the screens, in floor columns


def towers():
    """The palace's two end towers, west first: (door cell, the cell in front of it)."""
    found = [((x + dx, y + dy), (x + dx, y + dy + 1))
             for x, y, key in rg.find_sprites(cfg['rooms'][HOST], rg.PALACE_DOORS)
             for dx, dy in rg.PALACE_DOORS[key]]
    assert len(found) == 2, f'{HOST}: expected the two towers of the palace, found {len(found)}'
    return sorted(found)


def build(doors):
    it = Interior(FW, FH, OX, OY)
    s = lambda piece: f'palace-in-{piece}_0_0'

    # ---- floors -------------------------------------------------------------------
    engawa = (0, 1, FW - 2, FW - 1)

    def boards(fx, fy):
        ab = 'a' if (fx + fy // 2) % 2 == 0 else 'b'
        if fx in engawa and fy < HALL + 2:
            return s(f'board-{ab}')                                 # the side corridors run north
        if fy >= HALL:
            return s(f'board-h-{ab}')                               # the long corridor runs across
        return s('tatami-l' if (fx + fy) % 2 == 0 else 'tatami-r')

    it.floor(boards)
    it.side_walls(s('side-w'), s('side-e'), 3)                      # the side walls: paper screens
    for fy in range(1, HALL + 2, 2):                                # daylight through them
        it.put('Over Floor', 0, fy, s('sun-w'))
        it.put('Over Floor', FW - 2, fy, s('sun-e'))

    # ---- the front wall and its two doors --------------------------------------------
    door_x = (0, FW - 2)                                            # west door, east door
    it.front_wall(s('wall-front'), [x + dx for x in door_x for dx in (0, 1)], [s('threshold-w'), s('threshold-e')] * 2)
    for x in door_x:
        it.put('Non-Collidables', x, FH - 3, s('doorlight'))

    # ---- the back wall -----------------------------------------------------------------
    back = [(0, 'wall-shoji', 1), (1, 'wall-shoji', 1), (2, 'wall-plain', 1), (3, 'alcove-shelves', 3),
            (6, 'mural', 12), (18, 'alcove-doors', 3), (21, 'wall-plain', 1), (22, 'wall-shoji', 1), (23, 'wall-shoji', 1)]
    it.back_wall([(fx, s(piece), w) for fx, piece, w in back], 3)

    # ---- the dais, and what stands either side of it --------------------------------------
    it.prop(s('dais'), 6, 0, 12, 3)
    it.stand(s('armour'), 3, 2, w=2, h=3)
    it.stand(s('andon'), 5, 2)
    it.stand(s('andon'), 18, 2)
    it.stand(s('swords'), 19, 2, w=2)

    # ---- pillars: between the hall and each side corridor, and at the ends of the screens ----
    for fx in (2, FW - 3):
        for foot in (2, 6):
            it.stand(s('pillar'), fx, foot, h=3)
    for fx in (2, GAP[0] - 1, GAP[1] + 1, FW - 3):
        it.stand(s('pillar'), fx, HALL + 1, h=3)

    # ---- the painted screens between the hall and the corridor ------------------------------
    it.stand(s('fusuma-tiger'), 3, HALL + 1, w=6)
    it.stand(s('fusuma-waves'), GAP[1] + 2, HALL + 1, w=6)

    # ---- the hall: cushions in rows, lamps hung over it ---------------------------------------
    for fy in (5, 7):
        for fx in (5, 7, 9, 14, 16, 18):
            it.put('Over Floor', fx, fy, s('zabuton'))
    for fx, fy in ((3, 3), (FW - 4, 3), (3, 7), (FW - 4, 7), (GAP[0], HALL - 2), (GAP[1], HALL - 2)):
        it.put('Tops', fx, fy, s('lamp-hang'))

    # ---- the corridor: the book and the guard by the west door, the waiting room by the east ----
    low = FH - 1
    it.stand(s('guestbook'), 2, low)
    it.stand(s('guardpost'), 4, low, w=3)
    it.stand(s('andon'), 8, low - 1)
    it.stand(s('andon'), 15, low - 1)
    it.stand(s('byobu'), 15, low, w=3)
    it.prop(s('table'), 19, low - 1, 2)
    for fx in (19, 20):
        it.put('Over Floor', fx, low - 2, s('zabuton'))
        it.put('Over Floor', fx, low, s('zabuton'))
    it.stand(s('andon'), 21, low)

    # ---- the doors: both cells of each lead out in front of its tower -----------------------------
    west, east = (it.doorway(x, HOST, front) for x, (_, front) in zip(door_x, doors))
    room = it.room(
        NAME, npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
        # whose hall this is: the marker roomgen.owned_door reads, as a house's `house` is
        palace={'host': HOST, 'doors': [list(door) for door, _ in doors]},
        lanternLight=True,           # at night it dims and its lamps glow (DayNight, Glows)
        shopEnabled=False)           # not a konbini
    # arrive just inside each door: the inner cell of the pair
    return room, [west[1], east[0]]


doors = towers()
room, arrive = build(doors)
cfg['rooms'][KEY] = room
for (door, front), cell in zip(doors, arrive):
    rg.open_door(cfg['rooms'][HOST], door, KEY, cell)       # unsealed, wired in place: a re-run changes nothing
    print(f'door   {HOST} {door} -> {KEY} {cell}, back out on {front}')

rg.save_config(cfg)
print(f"built  {KEY} - {NAME}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}. Now run config_to_tiled, then play.js lint, for:")
print(f'  {KEY} {HOST}')
