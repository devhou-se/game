#!/usr/bin/env python3
"""generate_yukimura.py — "Yukimura" (雪村), a quiet snowy village.

Another world: a small village in a snowed-in forest clearing, reachable ONLY
by train — there are no road/edge transporters to anywhere. A rail line and a
fenced platform run along the north; the station house door leads into the
YukimuraStation interior (built by generate_stations.py), where you board the
branch-line train. Everything else is winter: a snow field underfoot, a frozen
pond, a little red shrine gate glowing against the white, snow-dusted
evergreens ringing the clearing, warm lanterns, a couple of cottages.

Snow art is recoloured from the existing pack by tools/make_snow_tiles.py, and
the snow trees/shrubs are prefabs added by tools/make_prefabs.py — so run BOTH
of those first. Deterministic and idempotent: rebuilds rooms.Yukimura from
scratch each run.

Run from gamev2/:
    python3 tools/make_snow_tiles.py
    python3 tools/make_prefabs.py
    python3 tools/generate_yukimura.py
    python3 tools/generate_stations.py            # builds YukimuraStation + registry
    python3 tools/qa_port.py --room Yukimura       (and --room YukimuraStation)
    python3 tools/config_to_tiled.py Yukimura      (and YukimuraStation)
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 42, 28
b = rg.Builder(W, H)
rng = random.Random(23)

b.fill('snow-autotile')

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-autotile', rect(0, 3, W - 1, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 12)) + list(range(32, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):                                   # snowy caps at the corridor ends
    b.stamp('shrub-small-snow', 0, y); b.stamp('shrub-small-snow', W - 1, y)

# ---- station platform + station house -----------------------------------------
b.autotile('light-concrete-autotile', rect(12, 6, 27, 8))
b.stamp('lamp-blue', 13, 7); b.stamp('lamp-blue', 26, 7)
b.stamp('vending-white', 20, 6); b.stamp('vending-red', 22, 6)
station_door = b.stamp('house-blue', 28, 4, seal=False)[0]   # door -> YukimuraStation
for i, px in enumerate((14, 18, 24)):
    b.paver(px, 8, i)
# a shovelled forecourt joining the platform down to the arrival cell (29,10)
b.autotile('light-concrete-autotile', rect(12, 9, 30, 10))

# ---- the shrine approach (sando): a path trodden down to dirt through the
#      snow, straight from the platform, through the torii, into the square -----
b.autotile('dirt-outside-autotile', rect(23, 11, 24, 24))
b.stamp('lantern-red', 22, 13); b.stamp('lantern-red', 25, 13)

# ---- frozen pond (west) -------------------------------------------------------
b.pond(4, 13, 10, fam='ice-pond-autotile')
b.stamp('lantern-red', 11, 12)
b.stamp('shrub-small-snow', 3, 12); b.stamp('shrub-small-snow', 11, 15)

# ---- cottages (colour is welcome against all the white) -----------------------
b.stamp('house-red', 5, 18)
b.stamp('house-blue', 32, 12)
b.stamp('house-black', 32, 19)

# ---- the little shrine gate: a red torii glowing in the snow, opening astride
#      the approach so you walk through it into the square ----------------------
b.stamp('torii-red', 21, 17)
b.stamp('fox-statue', 20, 19); b.stamp('fox-statue', 27, 19)
b.stamp('lantern-red', 20, 22); b.stamp('lantern-red', 27, 22)
for i, (px, py) in enumerate([(21, 23), (26, 23), (21, 25), (26, 25), (22, 25), (25, 25)]):
    b.paver(px, py, i)

# ---- a small snowy grove softening the open west side ------------------------
b.stamp('tree-snow', 9, 15); b.stamp('tree-snow', 13, 19)
b.stamp('shrub-small-snow', 12, 16); b.stamp('shrub-small-snow', 8, 21); b.stamp('shrub-small-snow', 15, 18)
b.stamp('tree-snow', 29, 15); b.stamp('shrub-small-snow', 30, 21)

# ---- pretty pink accents: a couple of bare sakura standing in the snow --------
b.stamp('sakura-small', 11, 22); b.stamp('sakura-small', 30, 24)

# ---- snowy evergreen treeline ringing the clearing (west / east / south) ------
for y in (8, 12, 16, 20):
    b.stamp('tree-snow', 0, y); b.stamp('tree-snow', W - 2, y)
for y in range(9, 25, 4):
    b.stamp('shrub-small-snow', 2, y)
    b.stamp('shrub-small-snow', W - 3, y)
# south treeline + fence, with a gap where the approach fades into the forest
for x in range(3, W - 3, 4):
    if 21 <= x <= 26:
        continue
    b.stamp('tree-snow', x, 24)
for i, x in enumerate(range(3, W - 3)):
    if 22 <= x <= 25:            # the approach peters out into the trees here
        continue
    b.fence(x, 26, i)

# ---- scattered snow shrubs / plants for texture on the open field -------------
for i in range(10):
    sx, sy = rng.randrange(3, W - 3), rng.randrange(11, 24)
    if all(f'{sx},{sy}' not in b.L[n] for n in
           ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('snow'):
        b.stamp('shrub-small-snow', sx, sy)

# ---- a lone villager ----------------------------------------------------------
james = rg.make_npc('James', 'james', 14, 15, [
    "Oh — a visitor. We don't get many, all the way out here.",
    "No road reaches Yukimura. Only the train, once the snow sets in.",
    "Quiet, isn't it? I wouldn't trade it for the city."
])

# isolated: the ONLY way out is the station house door into YukimuraStation.
cfg['rooms']['Yukimura'] = b.room('Yukimura', npcs=[james], transporters=[
    rg.transporter(station_door[0], station_door[1], 'YukimuraStation', 11, 11, hidden=True),
])

rg.save_config(cfg)
print(f'Yukimura {W}x{H}; station house door at {station_door} -> YukimuraStation')
