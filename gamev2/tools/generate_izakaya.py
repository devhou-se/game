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

Run from gamev2/:  python3 tools/generate_izakaya.py
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
# The registered interior pack has no true wood floor, chairs, drinkware or
# izakaya furniture yet. Warm floor tiles, office counters and cabinets are
# deliberate placeholders; drink/glass shelves make the bar read clearly.
it = Interior(16, 10, ox=2, oy=3, w=20, h=15)     # the floor is room cells (2..17, 3..12)
it.floor(lambda fx, fy: 'office-warm-autotile_center')
ib = it.b                           # the furniture is laid in room coordinates

# Back wall, menu and clock.
it.back_wall([(fx, 'office-wall-white_0_0', 1) for fx in range(it.fw)], 1)
ib.put('Other', 5, 2, 'office-poster-menu_0_0')
ib.put('Other', 9, 2, 'office-clock_0_0')

# Bar: bottle/glass shelves behind a six-cell counter, with a register.
for x, key in zip(range(11, 17), [
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0']):
    ib.prop(key, x, 3, layer='Other')
for x in (11, 13, 15):
    ib.prop('office-counter2_0_0', x, 5, 2)
ib.put('Tops', 15, 5, 'office-register_0_0')
for x in (11, 13, 15):
    ib.prop('izakaya-stool_0_0', x, 6)               # bar stools (tools/extract_street.py)

# Red lanterns frame the dining room.
ib.stamp('lantern-red', 2, 3)
ib.stamp('lantern-red', 17, 3)
ib.prop('office-plant-a_0_0', 2, 12)
ib.prop('office-plant-b_0_0', 17, 12)

# Communal tables. The sprite canvas is three cells wide but its visible table
# and usable footprint are two, so only those two cells are solid/interactive.
# Stools (never bins - issue #19) are placed diagonally to leave a direct
# approach on both long sides instead of turning the dining area into a maze.
TABLES = [(4, 7), (4, 11), (12, 10)]
for tx, ty in TABLES:
    ib.prop('office-counter_0_0', tx, ty, 2)
    for sx, sy in ((tx, ty - 1), (tx, ty + 1)):
        ib.prop('izakaya-stool_0_0', sx, sy)

damian = rg.make_npc('Damian', 'damian', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
bailey = rg.make_npc('Bailey', 'bailey', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
for opponent in (damian, bailey):
    opponent['drinkingGameOpponent'] = True
    opponent['stationary'] = True

# Clear doorway mats at the bottom (room cells 9,13 and 10,13). Arrival is one row
# inside, never on an exit transporter, so entering cannot bounce the player straight back out.
outside = (DOOR[0], DOOR[1] + 1)   # the pavement cell in front of the street door
ARRIVE = it.doorway(7, HOST, outside, mat='office-warm-autotile_center')[0]
cfg['rooms']['Izakaya'] = it.room(
    'Izakaya', npcs=cfg['rooms'].get('Izakaya', {}).get('npcs') or [damian, bailey],
    pockets=[(15, 0)],             # the corner behind the east lantern, shut in by the bar's shelves
    shopEnabled=False,             # not a konbini: its shelves and tables stay furniture...
    shopMenu='izakaya',            # ...but the bar (office-counter2) sells the izakaya menu
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
