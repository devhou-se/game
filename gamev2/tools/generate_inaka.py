#!/usr/bin/env python3
"""generate_inaka.py — "Inaka", a quiet countryside train stop.

NOT contiguous with the rest of the overworld: you get here by boarding the
train on the platform west of Tokyo Station (Palace room) — visible station
transporters both ways. A rail line crosses the north, a small platform with
lamps and a station house sits beside it, and the rest is farmland: dirt
paths, tilled plots, an orchard, a pond, farmhouses.

Deterministic and idempotent: rebuilds rooms.Inaka from scratch each run
while preserving Inaka's dated blog NPC history. The red farmhouse beside the
pond is a sealed house: the Izakaya it used to open into moved to Tokyo
(issue #68, tools/generate_izakaya.py).

Run from gamev2/:  python3 tools/generate_inaka.py
Then:              python3 tools/config_to_tiled.py Inaka     (fences and tracks are done here: b.finish())
                   node tools/play.js lint Inaka
                   node tools/play.js check
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
b.stamp('house-red', 12, 11)                 # the lakeside farmhouse: a sealed house (#68)
b.stamp('house-blue', 25, 16)

# orchard (east) + loose trees
for (ox, oy) in [(33, 10), (36, 12), (33, 15), (36, 17)]:
    b.stamp('sakura-small', ox, oy)
b.stamp('tree-green', 4, 13); b.stamp('tree-green', 34, 20)
b.stamp('shrub-small', 16, 12); b.stamp('shrub-small', 23, 15)
b.flowers(8, 14); b.flowers(22, 11); b.flowers(33, 22)

# ---- borders ------------------------------------------------------------------
for y in range(9, 24, 2):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', 38, y)
for y in (6, 7, 8, 25):
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', 39, y)
for x in (2, 7, 13, 18, 23, 28, 33):
    b.stamp('sakura-large', x, 23)       # south sakura line (trunks on row 25)

# scattered plants
for i in range(12):
    sx, sy = rng.randrange(2, 38), rng.randrange(9, 22)
    if all(f'{sx},{sy}' not in b.L[n] for n in ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

for x in range(12, 32):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# ---- wiring: the station house ------------------------------------------------
# (the actual train ride happens inside the station — see generate_stations.py)
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
cfg['rooms']['Inaka'] = b.room('Inaka', npcs=inaka_npcs, transporters=[
    {'gridX': station_door[0], 'gridY': station_door[1],
     'targetRoom': 'InakaStation', 'targetX': 11, 'targetY': 11, 'hidden': True},
])

rg.save_config(cfg)
print(f'Inaka {W}x{H}; station door {station_door} -> InakaStation')
