#!/usr/bin/env python3
"""generate_izakaya.py — the Izakaya (bar, communal tables, the drinking-game
table) and its street door in Tokyo.

The Izakaya is in Market, the temple-town district of the stitched Tokyo
(issue #68: it used to be behind Inaka's farmhouse, and Inaka is a made-up
town that will go). It is the red townhouse in the south-west corner of the
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

HOST = 'Market'
DOOR = (7, 37)                      # the red townhouse's door (building-entrance-3 at 6,37)
ARRIVE = (9, 12)                    # inside, one row above the exit mats
LANTERNS = [(5, 36), (9, 36)]       # lantern-red prefab origins (head; the solid foot is one row down)

# the house's ad boards, pinned: (cell, shape, key in assets/ads/manifest.json)
SIGNS = [((6, 36), 'wide', 'ad-wide-03'),      # のみほうだい 90分 ¥980 (all you can drink), a mug
         ((8, 36), 'square', 'ad-square-01')]  # 酒 (sake) on red, a lantern

cfg = rg.load_config()

# ---- the interior --------------------------------------------------------------
# The registered interior pack has no true wood floor, chairs, drinkware or
# izakaya furniture yet. Warm floor tiles, office counters and cabinets are
# deliberate placeholders; drink/glass shelves make the bar read clearly.
ib = rg.Builder(20, 15)
ib.fill('office-void-autotile')
for x in range(2, 18):
    for y in range(3, 13):
        ib.put('Floor', x, y, 'office-warm-autotile_center')


def solid_furniture(builder, key, x, y, w=1, h=1):
    """Place a registered multi-cell furniture sprite and seal its footprint."""
    builder.put('Collidables', x, y, key)
    for dx in range(w):
        for dy in range(h):
            builder.solid(x + dx, y + dy)


# Back wall, menu and clock.
for x in range(2, 18):
    solid_furniture(ib, 'office-wall-white_0_0', x, 2)
ib.put('Other', 5, 2, 'office-poster-menu_0_0')
ib.put('Other', 9, 2, 'office-clock_0_0')

# Bar: bottle/glass shelves behind a six-cell counter, with a register.
for x, key in zip(range(11, 17), [
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0']):
    ib.put('Other', x, 3, key)
    ib.solid(x, 3)
for x in (11, 13, 15):
    solid_furniture(ib, 'office-counter2_0_0', x, 5, 2)
ib.put('Tops', 15, 5, 'office-register_0_0')
for x in (11, 13, 15):
    solid_furniture(ib, 'izakaya-stool_0_0', x, 6)   # bar stools (tools/extract_street.py)

# Red lanterns frame the dining room.
ib.stamp('lantern-red', 2, 3)
ib.stamp('lantern-red', 17, 3)
solid_furniture(ib, 'office-plant-a_0_0', 2, 12)
solid_furniture(ib, 'office-plant-b_0_0', 17, 12)

# Communal tables. The sprite canvas is three cells wide but its visible table
# and usable footprint are two, so only those two cells are solid/interactive.
# Stools (never bins - issue #19) are placed diagonally to leave a direct
# approach on both long sides instead of turning the dining area into a maze.
TABLES = [(4, 7), (4, 11), (12, 10)]
for tx, ty in TABLES:
    solid_furniture(ib, 'office-counter_0_0', tx, ty, 2)
    for sx, sy in ((tx, ty - 1), (tx, ty + 1)):
        solid_furniture(ib, 'izakaya-stool_0_0', sx, sy)

# Clear doorway mats at the bottom. Arrival is one row inside, never on an
# exit transporter, so entering cannot bounce the player straight back out.
for x in (9, 10):
    ib.put('Floor', x, 13, 'office-warm-autotile_center')

damian = rg.make_npc('Damian', 'damian', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
bailey = rg.make_npc('Bailey', 'bailey', 6, 7, [
    'Bump the table when you are ready. Fifteen seconds. No excuses.',
])
for opponent in (damian, bailey):
    opponent['drinkingGameOpponent'] = True
    opponent['stationary'] = True

outside = (DOOR[0], DOOR[1] + 1)   # the pavement cell in front of the street door
izakaya = ib.room('Izakaya', npcs=cfg['rooms'].get('Izakaya', {}).get('npcs') or [damian, bailey], transporters=[
    rg.transporter(9, 13, HOST, outside[0], outside[1], hidden=True),
    rg.transporter(10, 13, HOST, outside[0], outside[1], hidden=True),
])
izakaya['boundary'] = [
    [2, 3], [18, 3], [18, 13], [11, 13],
    [11, 14], [9, 14], [9, 13], [2, 13],
]
izakaya['interior'] = True
izakaya['shopEnabled'] = False   # not a konbini: its shelves and tables stay furniture...
izakaya['shopMenu'] = 'izakaya'    # ...but the bar (office-counter2) sells the izakaya menu
izakaya['drinkingGame'] = {
    'triggerCells': [[4, 7], [5, 7]],
    'durationMs': 15_000,
}
cfg['rooms']['Izakaya'] = izakaya


# ---- the street door, in the host district ----------------------------------------
host = cfg['rooms'][HOST]
layers = {layer['name']: layer['tiles'] for layer in host['layers']}
layers['Colliders'].pop(f'{DOOR[0]},{DOOR[1]}', None)          # unseal the doorway
door = rg.transporter(DOOR[0], DOOR[1], 'Izakaya', ARRIVE[0], ARRIVE[1], hidden=True)
ts = host.setdefault('transporters', [])
at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == DOOR]
if at:
    ts[at[0]] = door
    for i in reversed(at[1:]):
        del ts[i]
else:
    ts.append(door)
for lx, ly in LANTERNS:             # the lantern-red prefab, written straight into the host's layers
    layers['Tops'][f'{lx},{ly}'] = rg.pidx('red-lanterns_6_3')
    layers['Collidables'][f'{lx},{ly + 1}'] = rg.pidx('red-lanterns_4_1')
    layers['Colliders'][f'{lx},{ly + 1}'] = rg.pidx('gk_blank')

signage = host.setdefault('signage', [])
for (sx, sy), shape, ad in SIGNS:   # the house's own sign: pin the ad on its board, in place
    spot = {'gridX': sx, 'gridY': sy, 'shape': shape, 'ad': ad}
    at = [i for i, s in enumerate(signage) if (s['gridX'], s['gridY']) == (sx, sy)]
    if at:
        signage[at[0]] = spot
        for i in reversed(at[1:]):
            del signage[i]
    else:
        signage.append(spot)

rg.save_config(cfg)
print(f'Izakaya 20x15; street door {HOST} {DOOR} -> Izakaya {ARRIVE}; '
      f'exit lands on {HOST} {outside}; lanterns (feet) {[(x, y + 1) for x, y in LANTERNS]}')
