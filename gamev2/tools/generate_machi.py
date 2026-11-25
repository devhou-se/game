#!/usr/bin/env python3
"""generate_machi.py — generate the "Machi" room (a quaint Japanese town).

Composition-only: all machinery lives in tools/roomgen.py, and every object
comes from the Tiled-authored prefab library (tiled/prefabs/*.tmj — edit them
in the Tiled app). Deterministic and idempotent: rebuilds rooms.Machi from
scratch each run, leaves other rooms alone, and (once) adds the Tokyo road
transporters.

What the generator does not own it keeps from the room as it stands: the NPCs
(the blog pipeline's dated states live on them), the ad `signage` spots (issue
#26) and the 7-Eleven door into KonbiniMachi1 (wired by generate_konbinis.py).
So a re-run on an unchanged world leaves config.json byte-identical —
tools/check_generators.py fails if that stops being true (issue #107). A
change made to Machi by hand must be mirrored here, or that check fails.

Run from gamev2/:  python3 tools/generate_machi.py
Then:              python3 tools/generate_konbinis.py Machi   (only if the 7-Eleven moved)
                   python3 tools/config_to_tiled.py Machi Tokyo  (and Machi's konbini rooms)
                   node tools/play.js lint Machi
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()
prev = cfg['rooms'].get('Machi', {})

# =============================== MACHI =======================================
b = rg.Builder(48, 34)
rng = random.Random(7)

b.fill('grass-autotile')

plaza_shrine = rect(20, 2, 29, 8)
approach = rect(22, 9, 25, 14)
street = rect(3, 15, 45, 16)
plaza_south = rect(19, 18, 30, 24)
lane = rect(23, 17, 24, 17)
road_east = rect(31, 20, 47, 21)
path_garden = rect(4, 22, 18, 23)

b.autotile('flat-grey-brick-autotile', plaza_shrine + approach + lane)
b.autotile('grey-brick-autotile', street)
b.autotile('light-concrete-autotile', plaza_south)
b.autotile('gravel-autotile', road_east + path_garden)

for (fx, fy) in [(14, 6), (43, 8), (5, 26), (15, 26), (34, 25)]:
    b.flowers(fx, fy)

b.pond(5, 7, 10)
b.pond(36, 6, 41)

# borders
for x in (2, 7, 12, 33, 38, 43): b.stamp('sakura-large', x, 0)
for x in (3, 8, 13, 18, 23, 28, 33, 38, 43): b.stamp('sakura-large', x, 30)
for y in range(2, 29, 3): b.stamp('shrub-large', 0, y)
for y in range(2, 29, 3):
    if not (18 <= y <= 21): b.stamp('shrub-large', 46, y)
b.stamp('shrub-small', 46, 19); b.stamp('shrub-small', 46, 22)

# shrine precinct
b.stamp('shrine', 22, 0)   # 5x8 with its roof: hall at (23,2), steps on row 7
b.stamp('fox-statue', 21, 4); b.stamp('fox-statue', 27, 4)
b.stamp('bell-blue', 29, 1)
b.stamp('lantern-red', 20, 6); b.stamp('lantern-red', 28, 6)
b.stamp('lantern-red', 21, 10); b.stamp('lantern-red', 26, 10)
b.stairs(23, 9); b.stairs(24, 9)
b.stamp('torii-red', 21, 11)
b.plants(19, 8, 1); b.plants(30, 8, 2)

# sakura park (top-left)
b.stamp('sakura-large', 4, 2); b.stamp('sakura-large', 9, 3); b.stamp('sakura-large', 13, 2)
b.stamp('sakura-small', 3, 6); b.stamp('sakura-small', 15, 4)
b.stamp('shrub-small', 12, 8); b.plants(4, 6, 0); b.plants(11, 5, 3); b.plants(13, 9, 2)

# east garden (top-right)
b.stamp('tree-green', 34, 2); b.stamp('tree-green', 41, 2); b.stamp('tree-green', 37, 9)
b.stamp('sakura-small', 44, 4); b.stamp('shrub-small', 35, 8); b.plants(42, 9, 1); b.plants(33, 5, 0)

# street lamps (kept clear of the shop fronts and house footprints)
for x in (6, 34): b.stamp('lamp-blue', x, 14)
for x in (27, 37, 43): b.stamp('lamp-blue', x, 17)      # (9 and 15 made way for the machiya lane)

# shop row: the 7-Eleven's door keeps the transporter generate_konbinis.py wired
# onto it (into KonbiniMachi1); with none to keep it is sealed until that runs
konbini_door = b.stamp('seven-eleven', 7, 11, seal=False)[0]
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.stamp('sign-7-11', 10, 12)
b.stamp('vending-white', 12, 13); b.stamp('vending-red', 14, 13); b.stamp('vending-white', 16, 13)
b.stamp('sakura-small', 18, 12)
# street accessories (issue #19): utility poles above the lane, parked bikes, a scooter by the konbini
b.stamp('utility-pole', 4, 12); b.stamp('utility-pole', 36, 12)
b.stamp('bicycle-blue', 3, 21); b.stamp('bicycle-orange', 37, 14); b.stamp('scooter-red', 10, 14)

# houses (doors sealed — no interiors for these yet). Stamped a row higher than
# the door row now that the prefab carries a wall tier above the entrance.
b.stamp('house-blue', 28, 9)
b.stamp('house-black', 33, 8)
b.stamp('house-red', 38, 9)
b.stamp('house-blue', 43, 9)

# south plaza (pagoda anchored so its feet stay on row 22 now that the fixed
# prefab is 6 tall — the paver ring frames it and fronts the door)
b.stamp('pagoda-small', 24, 17)
for i, (px, py) in enumerate([(21, 19), (28, 19), (21, 23), (28, 23),
                              (22, 21), (27, 21), (23, 24), (26, 24)]):
    b.paver(px, py, i)
b.stamp('vending-red', 30, 18); b.stamp('vending-white', 19, 18)
b.stamp('lantern-red', 20, 16); b.stamp('lantern-red', 29, 16)
b.stamp('lantern-red', 20, 24); b.stamp('lantern-red', 29, 24)
b.plants(22, 18, 0); b.plants(27, 18, 3); b.plants(20, 21, 2); b.plants(29, 22, 1)

# old-town lane (south-west, issue #18): three narrow machiya townhouses
# (tools/extract_city.py) shoulder to shoulder along the north side of the dirt
# lane, feet on row 21, the blossom row facing them across it. Live in the map
# via tools/stamp_prefab.py — this generator is not re-run (tiled/README.md).
for i, colour in enumerate(('black', 'red', 'blue')):
    b.stamp(f'machiya-{colour}', 4 + 5 * i, 17)
for ox in (5, 8, 11, 14):
    b.stamp('sakura-small', ox, 24)
b.plants(6, 22, 0); b.plants(9, 23, 1); b.plants(12, 22, 2); b.plants(15, 23, 3); b.plants(7, 26, 1)

# east road lanterns + greenery south of the houses
b.stamp('lantern-red', 44, 18); b.stamp('lantern-red', 44, 22)
b.stamp('sakura-small', 34, 17); b.stamp('sakura-small', 40, 17)
b.stamp('shrub-small', 37, 18); b.stamp('shrub-small', 42, 18); b.plants(35, 18, 1); b.plants(38, 17, 2)

# south fence line
for i, x in enumerate(range(3, 45)):
    if x in (23, 24): continue
    b.fence(x, 28, i)

# the east gate (the road to Tokyo, rows 20-21): the grass cell either side of
# it is solid - a shrub on the north one - so the stitched city (issue #41),
# which has no seam teleport there, cannot be walked round the gate
b.put('Collidables', 47, 19, 'shrub-small-circle_0_0'); b.solid(47, 19)
b.solid(47, 22)
# two cells boxed in north of the gate that no walk reaches are solid (issue #196)
b.solid(46, 13); b.solid(47, 13)
# the path runs out through the gate instead of ending in a rounded cap (issue #147)
b.put('Floor', 47, 20, 'gravel-autotile_edge-n', replace=True)
b.put('Floor', 47, 21, 'gravel-autotile_edge-s', replace=True)

# scattered plants
for i in range(14):
    sx, sy = rng.randrange(3, 45), rng.randrange(17, 27)
    if (4 <= sx <= 18 and 17 <= sy <= 21):       # under the machiya lane: would never be seen
        continue
    if all(f'{sx},{sy}' not in b.L[n] for n in ('Collidables', 'Colliders', 'Over Floor', 'Other')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

dylan = rg.make_npc('Dylan', 'dylan', 27, 22, [
    "Hello! I'm Dylan.",
    "A whole town, generated by one script.",
    "...I still bet it would've been better in Godot."
])
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
# NPCs: Dylan lives here, and the blog pipeline (tools/blog_to_npc.py) adds
# dated states and other members to the room - keep whatever is there.
cfg['rooms']['Machi'] = b.room('Machi', npcs=prev.get('npcs') or [dylan], transporters=[
    rg.transporter(47, 20, 'Tokyo', 3, 41, hidden=True),
    rg.transporter(47, 21, 'Tokyo', 3, 42, hidden=True),
] + ([konbini_entry] if konbini_entry else []))
if 'signage' in prev:
    cfg['rooms']['Machi']['signage'] = prev['signage']    # ad spots on the house walls (issue #26)

# =============================== WIRING ======================================
tok = cfg['rooms']['Tokyo']['transporters']
if not any(t.get('targetRoom') == 'Machi' for t in tok):
    tok.append(rg.transporter(0, 41, 'Machi', 45, 20, hidden=True))
    tok.append(rg.transporter(0, 42, 'Machi', 45, 21, hidden=True))

rg.save_config(cfg)
print(f"Machi {b.W}x{b.H}; 7-Eleven door at {konbini_door} -> "
      + (konbini_entry['targetRoom'] if konbini_entry else 'sealed: run generate_konbinis.py Machi'))
