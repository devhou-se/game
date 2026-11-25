#!/usr/bin/env python3
"""generate_osaka.py — "Osaka", the second city: Dotonbori and Shinsekai.

A generated room (roomgen + prefabs, the generate_yukimura.py recipe), NOT a
port: the legacy Godot scene Scenes/osaka/osaka_outside.tscn turned out to be
an older copy of the Tokyo overworld (same garden / market / park, even the
Tokyo Station placeholder) with no Osaka content, so there was nothing to port.

Reachable ONLY by train, like Yukimura: the station house door on the north
side leads into the OsakaStation interior (built by generate_stations.py).
From the station you walk south down the main street:

  north   the rail line, the platform and the station house
          the Dotonbori entrance ARCH over the street (walk under it), a row
          of townhouses to the west, the oval FERRIS WHEEL to the east
  middle  the Dotonbori canal, crossed by the street (the bridge)
  south   Shinsekai: TSUTENKAKU TOWER on the street's axis, standing on its
          own plaza, townhouses either side. A garden thicket fills the ground
          behind the tower, so the street forks round it (nobody walks hidden
          behind a 13-cell sprite)

The three landmarks are prefabs (tools/make_prefabs.py) whose art comes from
tools/extract_dotonbori.py (real GuttyKreum Dotonbori art) and
tools/generate_tsutenkaku.py (line-art placeholder). Deterministic and
idempotent: rebuilds rooms.Osaka from scratch each run, keeping any NPCs the
blog pipeline has placed there.

Run from gamev2/:
    python3 tools/extract_dotonbori.py
    python3 tools/generate_tsutenkaku.py
    python3 tools/make_prefabs.py
    python3 tools/generate_osaka.py
    python3 tools/generate_stations.py            # builds OsakaStation + registry
    python3 tools/fix_fences.py Osaka             # MANDATORY (b.fence)
    python3 tools/seal_tracks.py Osaka            # MANDATORY (rail line)
    python3 tools/qa_port.py --room Osaka          (and --room OsakaStation)
    python3 tools/config_to_tiled.py Osaka         (and OsakaStation)
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 50, 40
b = rg.Builder(W, H)
rng = random.Random(17)
FLAT = {'center'}

b.fill('grass-autotile')

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-autotile', rect(0, 3, W - 1, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 10)) + list(range(27, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):                                   # caps at the corridor ends
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
for x in range(4, W - 3, 6):                          # blossom beyond the tracks
    b.stamp('sakura-small', x, 0)

# ---- station platform + station house -----------------------------------------
b.autotile('light-concrete-autotile', rect(10, 6, 22, 8))
b.stamp('lamp-blue', 11, 7); b.stamp('lamp-blue', 21, 7)
b.stamp('vending-white', 15, 6); b.stamp('vending-red', 17, 6)
for i, px in enumerate((12, 16, 19)):
    b.paver(px, 8, i)
station_door = b.stamp('house-blue', 23, 4, seal=False)[0]   # door -> OsakaStation

# ---- ground: light paving on the north bank, warm brick in Shinsekai, and the
#      darker main street running station -> arch -> bridge -> tower ------------
b.autotile('grey-brick-autotile', rect(2, 9, 47, 18))
b.autotile('brown-brick-autotile', rect(2, 23, 47, 37))
b.autotile('flat-grey-brick-autotile', rect(22, 10, 27, 22))
b.autotile('light-concrete-autotile', rect(18, 32, 31, 37))  # the tower's plaza

# ---- Dotonbori: the entrance arch astride the main street ---------------------
ARCH = (21, 12)
b.stamp('dotonbori-arch', *ARCH)
b.stamp('lantern-red', 20, 10); b.stamp('lantern-red', 29, 10)

# ---- west of the street: a row of townhouses (doors sealed — no interiors) ----
b.stamp('house-red', 4, 10); b.stamp('house-black', 9, 10); b.stamp('house-blue', 14, 10)
b.stamp('lantern-red', 8, 15); b.stamp('lantern-red', 13, 15)
b.stamp('vending-white', 18, 13); b.stamp('vending-red', 19, 13)
for x in (6, 11, 16):
    b.stamp('lamp-blue', x, 18)

# ---- east of the street: the oval ferris wheel on the canal bank --------------
WHEEL = (33, 7)
b.stamp('dotonbori-wheel', *WHEEL)
b.stamp('lamp-blue', 31, 18); b.stamp('lamp-blue', 46, 18)
b.stamp('shrub-small', 46, 10); b.stamp('shrub-small', 46, 13)
b.stamp('sakura-small', 30, 13); b.stamp('sakura-small', 2, 16)

# ---- the Dotonbori canal, bridged by the main street --------------------------
b.pond(2, 20, 21)
b.pond(28, 20, 47)
b.stamp('lantern-red', 20, 22); b.stamp('lantern-red', 29, 22)   # south bridgehead (clear of
                                                                 # the tower's own top-left cell)

# ---- Shinsekai: Tsutenkaku on the axis of the street, on its plaza ------------
TOWER = (21, 23)
b.stamp('tsutenkaku', *TOWER)
# The tower garden: the tower is 13 cells tall and stands on the street's axis,
# so without this the main street would run BEHIND it and hide the player for
# ten cells. A thicket fills the ground behind the shaft and deck; the street
# forks at the bridgehead and passes either side of it down to the plaza.
for gy in range(24, 32, 2):
    for gx in range(22, 28, 2):
        for cx, cy in rect(gx, gy, gx + 1, gy + 1):
            b.put('Floor', cx, cy, 'grass-autotile_center')
        b.stamp('shrub-large', gx, gy)
b.stamp('lantern-red', 19, 35); b.stamp('lantern-red', 30, 35)
for i, (px, py) in enumerate([(19, 33), (30, 33), (22, 37), (27, 37), (20, 37), (29, 37)]):
    b.paver(px, py, i)
b.stamp('house-red', 5, 26); b.stamp('house-black', 10, 26)
b.stamp('house-blue', 37, 26); b.stamp('house-red', 42, 26)
b.stamp('vending-red', 14, 29); b.stamp('vending-white', 35, 29)
b.stamp('lantern-red', 9, 31); b.stamp('lantern-red', 41, 31)
b.stamp('sakura-large', 16, 26); b.stamp('sakura-large', 31, 26)   # flanking the tower
b.stamp('sakura-large', 3, 33); b.stamp('sakura-large', 44, 33)
b.stamp('sakura-small', 15, 34); b.stamp('sakura-small', 34, 34)
b.stamp('shrub-small', 17, 30); b.stamp('shrub-small', 32, 30)
b.stamp('shrub-small', 3, 25); b.stamp('shrub-small', 46, 25)
for x in (8, 13, 36, 41):
    b.stamp('lamp-blue', x, 36)

# ---- borders: hedges west / east, a fence along the south ---------------------
#      (continuous — a gap would let the player slip round behind the fences)
for y in range(8, 38, 2):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', W - 2, y)
b.stamp('shrub-small', 0, 38); b.stamp('shrub-small', W - 1, 38)
for y in (6, 7):
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, 38, i)

# ---- greenery on the canal banks ----------------------------------------------
for i in range(60):
    sx, sy = rng.randrange(2, W - 2), rng.choice((19, 22))
    if all(f'{sx},{sy}' not in b.L[n] for n in
           ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water', 'Tops')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      platform, so a platform-edge fence closes the gravel row behind it -------
for x in range(10, 27):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into OsakaStation.
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) — keep them.
prev = cfg['rooms'].get('Osaka', {})
cfg['rooms']['Osaka'] = b.room('Osaka', npcs=prev.get('npcs', []), transporters=[
    rg.transporter(station_door[0], station_door[1], 'OsakaStation', 11, 11, hidden=True),
])

rg.save_config(cfg)
print(f'Osaka {W}x{H}; station house door at {station_door} -> OsakaStation; '
      f'arch at {ARCH}, ferris wheel at {WHEEL}, Tsutenkaku at {TOWER}')
