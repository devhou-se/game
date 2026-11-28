#!/usr/bin/env python3
"""generate_izakaya.py — the Izakaya (bar, communal tables, the drinking-game
table) and its street door in Tokyo.

The Izakaya is in Market, the temple-town district of the stitched Tokyo
(issue #68: it used to be behind the farmhouse of Inaka, a made-up town that
is deleted). It is the red townhouse in the south-west corner of the
temple precinct, west of the big torii: the house front at Market (6..8, 37),
door on (7,37), reached from the paving in front of it (7,38). A red lantern
(akachochin) stands either side of the house so the door can be found, and
the two ad boards on its upper wall are its own sign: they always show the
all-you-can-drink board and the red sake tag from the ad pool (SIGNS), where
every other board in the street draws a random ad.

Like generate_konbinis.py, this owns the interior AND the door it opens in a
host room that has no generator of its own (Market is a ported district):
  * rooms.Izakaya is rebuilt from scratch (its NPCs are kept as they stand);
  * the host's door cell is unsealed and a hidden transporter wired onto it,
    replaced in place so a re-run leaves config.json byte-identical;
  * the two lanterns are (re)placed beside the house front;
  * the house's two signage spots are pinned to their ads (`ad`).
Nothing else in the host is touched. To move the Izakaya again: seal the old
door by hand (collider back, transporter and lanterns out), change HOST / DOOR
/ LANTERNS here and re-run.

The room is drawn with its own kit, izakaya-in-* (issue #286), which
tools/generate_izakaya_art.py draws in the house look and registers: run that
first. The only other sprites in it are the bar stools (izakaya-stool, from
tools/extract_street.py) and the void every interior is filled with.

Run from gamev2/:  python3 tools/generate_izakaya_art.py
                   python3 tools/generate_izakaya.py
Then:              python3 tools/config_to_tiled.py Izakaya Market
                   node tools/play.js lint Izakaya Market TokyoCity
                   node tools/play.js check
"""
import roomgen as rg
from interiors import Interior

HOST = 'Market'
DOOR = (7, 37)                      # the red townhouse's door (building-entrance-3 at 6,37)
LANTERNS = [(5, 36), (9, 36)]       # lantern-red prefab origins (head; the solid foot is one row down)

# the house's ad boards, pinned: (cell, shape, key in assets/ads/manifest.json)
SIGNS = [((6, 36), 'wide', 'ad-wide-03'),      # 飲み放題 90分 ¥980 (all you can drink), a mug
         ((8, 36), 'square', 'ad-square-01')]  # 酒 (sake) on red, a lantern

cfg = rg.load_config()

# ---- the interior --------------------------------------------------------------
# Drawn with the room's own kit, izakaya-in-* (tools/generate_izakaya_art.py, in the
# house look): timber boards underfoot, a two-row plaster and timber back wall with the
# menu strips and the clock, a back bar of bottles behind a six-cell bar, low tables,
# paper lanterns hung overhead, sake casks in the corners. The stools are izakaya-stool.
LAMPS = (3, 7, 10)                       # room columns of the lanterns hung along the back wall
CASKS = ((2, 12), (17, 12), (17, 5))     # the feet of the cask stacks
s = lambda piece: f'izakaya-in-{piece}_0_0'

it = Interior(16, 10, ox=2, oy=3, w=20, h=15)     # the floor is room cells (2..17, 3..12)
it.floor(lambda fx, fy: s('floor-a' if (fx + fy) % 2 == 0 else 'floor-b'))
it.side_walls(s('side-w'), s('side-e'), 2)
it.front_wall(s('wall-front'), (7, 8), (s('threshold-w'), s('threshold-e')))

# The back wall, two rows (room rows 1-2) inside the boundary, so a phone's camera keeps it on screen.
WALL = {2: ('wall-menu', 2), 7: ('wall-clock', 1)}     # floor columns: the menu on room x 4-5, the clock on 9
pieces, fx = [], 0
while fx < it.fw:
    piece, w = WALL.get(fx, ('wall', 1))
    pieces.append((fx, s(piece), w))
    fx += w
it.back_wall(pieces, 2, view=True)

ib = it.b                           # the furniture is laid in room coordinates

# The bar: the back bar of bottles against the wall, the counter that sells, its stools.
ib.stand(s('backbar'), 11, 3, 6)                       # head over wall row 2, solid on (11..16, 3)
ib.prop(s('bar'), 11, 5, 6)                            # (11..16, 5): the counter's cells
for x in (11, 13, 15):
    ib.prop('izakaya-stool_0_0', x, 6)               # bar stools (tools/extract_street.py)

# Communal tables, each two cells, with a stool north and south (never bins - issue #19),
# which leaves a direct approach on both long sides; a lantern hangs over each.
TABLES = [(4, 7), (4, 11), (12, 10)]
for tx, ty in TABLES:
    ib.prop(s('table'), tx, ty, 2)
    for sx, sy in ((tx, ty - 1), (tx, ty + 1)):
        ib.prop('izakaya-stool_0_0', sx, sy)
    ib.put('Tops', tx + 1, ty - 2, s('chochin'))       # (5,5), (5,9), (13,8): over each table
for x in LAMPS:
    ib.put('Tops', x, 2, s('chochin'))                 # cord down the wall, paper over floor row 3
for x, y in CASKS:
    ib.stand(s('casks'), x, y)

damian = rg.make_npc('Damian', 'damian', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
bailey = rg.make_npc('Bailey', 'bailey', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
for opponent in (damian, bailey):
    opponent['drinkingGameOpponent'] = True
    opponent['stationary'] = True

# The way out at the bottom (room cells 9,13 and 10,13), drawn by the thresholds. Arrival is one row
# inside, never on an exit transporter, so entering cannot bounce the player straight back out.
outside = (DOOR[0], DOOR[1] + 1)   # the pavement cell in front of the street door
ARRIVE = it.doorway(7, HOST, outside)[0]
cfg['rooms']['Izakaya'] = it.room(
    'Izakaya', npcs=cfg['rooms'].get('Izakaya', {}).get('npcs') or [damian, bailey],
    lanternLight=True,             # at night the room dims and the hung lanterns glow, as the pub's lamps do
    shopEnabled=False,             # not a konbini: its shelves and tables stay furniture...
    shopMenu='izakaya',            # ...but the bar (izakaya-in-bar) sells the izakaya menu
    drinkingGame={
        'triggerCells': [[4, 7], [5, 7]],
        'durationMs': 15_000,
    })


# ---- the street door, in the host district ----------------------------------------
host = cfg['rooms'][HOST]
rg.open_door(host, DOOR, 'Izakaya', ARRIVE)                     # unsealed, wired in place
layers = {layer['name']: layer['tiles'] for layer in host['layers']}
for lx, ly in LANTERNS:             # the lantern-red prefab, written straight into the host's layers
    layers['Tops'][f'{lx},{ly}'] = rg.pidx('red-lanterns_6_3')
    layers['Collidables'][f'{lx},{ly + 1}'] = rg.pidx('red-lanterns_4_1')
    layers['Colliders'][f'{lx},{ly + 1}'] = rg.pidx('gk_blank')

for (sx, sy), shape, ad in SIGNS:   # the house's own sign: pin the ad on its board, in place
    rg.pin(host.setdefault('signage', []), {'gridX': sx, 'gridY': sy, 'shape': shape, 'ad': ad})

rg.save_config(cfg)
print(f'Izakaya 20x15; street door {HOST} {DOOR} -> Izakaya {ARRIVE}; '
      f'exit lands on {HOST} {outside}; lanterns (feet) {[(x, y + 1) for x, y in LANTERNS]}')
