#!/usr/bin/env python3
"""generate_inaka.py — "Inaka", a quiet countryside train stop, plus the
Izakaya inside the red farmhouse beside the pond.

NOT contiguous with the rest of the overworld: you get here by boarding the
train on the platform west of Tokyo Station (Palace room) — visible station
transporters both ways. A rail line crosses the north, a small platform with
lamps and a station house sits beside it, and the rest is farmland: dirt
paths, tilled plots, an orchard, a pond, farmhouses.

Deterministic and idempotent: rebuilds rooms.Inaka and rooms.Izakaya from
scratch each run while preserving Inaka's dated blog NPC history.

Run from gamev2/:  python3 tools/generate_inaka.py
Then:              python3 tools/fix_fences.py Inaka
                   python3 tools/seal_tracks.py
                   python3 tools/qa_port.py --room Inaka
                   python3 tools/qa_port.py --room Izakaya
                   python3 tools/config_to_tiled.py Inaka
                   python3 tools/config_to_tiled.py Izakaya
                   python3 tools/make_worldmap.py          (after editing devhouse.world)
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()
# Blog ingestion adds dated NPC records after this room is generated. Keep
# those records when rebuilding the scenery so a layout edit never erases the
# time-travel history.
inaka_npcs = cfg.get('rooms', {}).get('Inaka', {}).get('npcs', [])

W, H = 40, 26
b = rg.Builder(W, H)
rng = random.Random(11)

b.fill('grass-autotile')

# ---- the rail corridor across the north --------------------------------------
b.autotile('gravel-autotile', rect(0, 3, 39, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, 39):
    b.fence(x, 2, x)                     # north fence line
for x in list(range(1, 12)) + list(range(32, 39)):
    b.fence(x, 6, x)                     # south fence line, gap at the platform
for y in (3, 4, 5):                      # cap the corridor ends
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', 39, y)

# ---- station platform ---------------------------------------------------------
b.autotile('light-concrete-autotile', rect(12, 6, 27, 8))
b.stamp('lamp-blue', 13, 7); b.stamp('lamp-blue', 26, 7)
b.stamp('vending-white', 20, 6); b.stamp('vending-red', 22, 6)
station_door = b.stamp('house-black', 28, 4, seal=False)[0]   # the station house — door leads inside
for i, px in enumerate((14, 18, 24)):
    b.paver(px, 8, i)

# ---- countryside --------------------------------------------------------------
b.autotile('gravel-autotile', rect(19, 9, 20, 21))          # lane south
b.autotile('dirt-outside-autotile', rect(26, 12, 32, 14))   # tilled plots
b.autotile('dirt-outside-autotile', rect(5, 17, 11, 19))
for x in range(27, 32):
    b.plants(x, 13, x)                                       # crop rows
for x in range(6, 11):
    b.plants(x, 18, x)

b.pond(5, 10, 10)
izakaya_door = b.stamp('house-red', 12, 11, seal=False)[0]
b.stamp('house-blue', 25, 16)

# orchard (east) + loose trees
for (ox, oy) in [(33, 10), (36, 12), (33, 15), (36, 17)]:
    b.stamp('sakura-small', ox, oy)
b.stamp('tree-green', 4, 13); b.stamp('tree-green', 34, 20)
b.stamp('shrub-small', 16, 12); b.stamp('shrub-small', 23, 15)
b.flowers(8, 14); b.flowers(22, 11); b.flowers(33, 22)

# ---- borders ------------------------------------------------------------------
for y in range(9, 24, 3):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', 38, y)
for x in (2, 7, 13, 18, 23, 28, 33):
    b.stamp('sakura-large', x, 23)       # south sakura line (trunks on row 25)

# scattered plants
for i in range(12):
    sx, sy = rng.randrange(2, 38), rng.randrange(9, 22)
    if all(f'{sx},{sy}' not in b.L[n] for n in ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

# ---- wiring: station house + lakeside farmhouse interiors ---------------------
# (the actual train ride happens inside the station — see generate_stations.py)
cfg['rooms']['Inaka'] = b.room('Inaka', npcs=inaka_npcs, transporters=[
    {'gridX': station_door[0], 'gridY': station_door[1],
     'targetRoom': 'InakaStation', 'targetX': 11, 'targetY': 11, 'hidden': True},
    rg.transporter(izakaya_door[0], izakaya_door[1], 'Izakaya', 9, 12, hidden=True),
])

# ---- IZAKAYA ------------------------------------------------------------------
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
ib.put('Other', 5, 3, 'office-poster-menu_0_0')
ib.put('Other', 9, 3, 'office-clock_0_0')

# Bar: bottle/glass shelves behind a six-cell counter, with a register.
for x, key in zip(range(11, 17), [
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0',
        'office-shelf-drinks_0_0', 'office-shelf-glass_0_0']):
    ib.put('Other', x, 3, key)
for x in (11, 13, 15):
    solid_furniture(ib, 'office-counter2_0_0', x, 5, 2)
ib.put('Tops', 15, 5, 'office-register_0_0')
for x in (11, 13, 15):
    solid_furniture(ib, 'office-bin_0_0', x, 6)   # compact bar-stool placeholders

# Red lanterns frame the dining room.
ib.stamp('lantern-red', 2, 3)
ib.stamp('lantern-red', 17, 3)
solid_furniture(ib, 'office-plant-a_0_0', 2, 11)
solid_furniture(ib, 'office-plant-b_0_0', 17, 11)

# Communal tables. The counters are convincing table placeholders; the small
# brown cabinets are temporary stools. Keep the centre seat lanes open so each
# table remains reachable from above and below.
TABLES = [(4, 7), (4, 10), (11, 9)]
for tx, ty in TABLES:
    solid_furniture(ib, 'office-counter_0_0', tx, ty, 3)
    for sx, sy in ((tx, ty - 1), (tx + 2, ty - 1),
                   (tx, ty + 1), (tx + 2, ty + 1)):
        solid_furniture(ib, 'office-cabinet_0_0', sx, sy)

# Clear doorway mats at the bottom. Arrival is one row inside, never on an
# exit transporter, so entering cannot bounce the player straight back out.
for x in (9, 10):
    ib.put('Floor', x, 13, 'office-warm-autotile_center')

damian = rg.make_npc('Damian', 'damian', 7, 7, [
    'Bump the table when you are ready. Sixty seconds. No excuses.',
])
bailey = rg.make_npc('Bailey', 'bailey', 7, 7, [
    'Want a drinking game? I only need a ten-point head start.',
])
for opponent in (damian, bailey):
    opponent['drinkingGameOpponent'] = True
    opponent['stationary'] = True

outside = (izakaya_door[0], izakaya_door[1] + 1)
izakaya = ib.room('Izakaya', npcs=[damian, bailey], transporters=[
    rg.transporter(9, 13, 'Inaka', outside[0], outside[1], hidden=True),
    rg.transporter(10, 13, 'Inaka', outside[0], outside[1], hidden=True),
])
izakaya['boundary'] = [
    [2, 3], [18, 3], [18, 13], [11, 13],
    [11, 14], [9, 14], [9, 13], [2, 13],
]
izakaya['interior'] = True
izakaya['shopEnabled'] = False
izakaya['drinkingGame'] = {
    'triggerCells': [[4, 7], [5, 7], [6, 7]],
    'durationMs': 60_000,
}
cfg['rooms']['Izakaya'] = izakaya

rg.save_config(cfg)
print(f'Inaka {W}x{H}; station door {station_door} -> InakaStation; '
      f'farmhouse door {izakaya_door} -> Izakaya')
