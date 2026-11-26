#!/usr/bin/env python3
"""generate_toyama.py — "Toyama", the small coastal district of the Hokuriku
region (issue #68, stage 3).

devhouse 2's Damian and Julia were here on 2-3 November 2025, in the rain. It
is a district of the stitched `HokurikuCity` (tools/hokuriku.py has the layout)
with NO station: you walk in up the mountain path from Shirakawa-go (south
edge, columns 18-19).

  north   the SEA, the whole top of the map (`pond-autotile`, so you can fish it
          from the quay; its `waterways` entry gives it ambient boats), and the
          quay along it
  NE      the PORT OBSERVATION TOWER on the quay (post 587; post 611's "mountains
          on one side, ocean on the other")
  N       Iwase's old street: machiya shoulder to shoulder, and at its east end
          the BLACK-RAMEN SHOP - seven stools at a counter (posts 587, 611)
  middle  the tram street: rails down the middle, a tram at the TRAM STOP
          (post 583: "the Glass Art Museum by tram"), and on its north side the
          GLASS ART MUSEUM (posts 576, 583)
  west    the Sho river, coming down from Shirakawa-go to the sea
  south   cedar woods, an old house in them (the Airbnb), and the path in from
          the mountains

Nobody gets lost behind a building: every building is solid over its roof rows,
and the woods are solid throughout.

Art is drawn by tools/generate_hokuriku_art.py. Deterministic and idempotent:
rebuilds rooms.Toyama from scratch each run, keeping any NPCs the blog pipeline
has placed there. The build order for the whole region is in
tools/generate_kanazawa.py.

Run from gamev2/:  python3 tools/generate_toyama.py
"""
import random
import roomgen as rg
from roomgen import rect
import hokuriku as hk

cfg = rg.load_config()

W, H = hk.SIZE['Toyama']
b = rg.Builder(W, H)
k = hk.Kit(b)
rng = random.Random(6811)

SEA = 6                           # the sea's last row (0-6); the quay is rows 7-9
QUAY0, QUAY1 = 7, 9
R0, R1 = hk.T_RIVER               # the Sho river (columns 4-9)
P0, P1 = hk.T_PATH                # the path south to Shirakawa-go (columns 18-19)
LANE = 15                         # Iwase's old street (rows 15-16)
TRAM = 20                         # the tram street's top kerb row (20-22)
EAST = 41                         # the last column of town; a hedge closes 42-43
WOODS = ['sendai-cedar', 'sendai-cedar', 'sendai-pine', 'sendai-maple']

b.fill('grass-autotile')

# ---- the sea and the river --------------------------------------------------------------
for y in range(SEA + 1):                              # the coast runs up the map's west side from the river's bank
    for x in range(R0, W):
        mouth = R0 < x < R1
        role = 'edge-w' if x == R0 else 'center' if mouth or y < SEA else 'edge-s'
        b.put('Water', x, y, f'pond-autotile_{role}')
        b.solid(x, y)
for y in range(SEA + 1, H):
    for x in range(R0, R1 + 1):
        role = 'edge-w' if x == R0 else 'edge-e' if x == R1 else 'center'
        b.put('Water', x, y, f'pond-autotile_{role}')
        b.solid(x, y)
k.woods(0, 0, R0 - 1, H - 1, WOODS, rng)              # the far bank

# ---- the quay, and the port observation tower on it ----------------------------------------
b.autotile('light-concrete-autotile',
           rect(R1 + 1, QUAY0, EAST, QUAY1)
           + rect(R1 + 1, QUAY1 + 1, R1 + 2, TRAM - 1)            # the riverside walk
           + rect(32, QUAY1 + 1, 33, TRAM - 1)                    # the street down past the ramen shop
           + rect(R1 + 1, TRAM - 1, EAST, TRAM - 1) + rect(R1 + 1, TRAM + 3, EAST, TRAM + 3))
TOWER = (36, 2)                                       # its podium stands on quay rows 7-8
b.stamp('toyama-port-tower', *TOWER)
for x in (13, 21, 29):
    b.stamp('lamp-blue', x, QUAY0)
for i, (px, py) in enumerate([(12, 8), (17, 9), (24, 8), (30, 9), (35, 9), (40, 8)]):
    b.paver(px, py, i)

# ---- Iwase's old street: machiya, and the black-ramen shop -----------------------------------
b.autotile('flat-grey-brick-autotile', rect(R1 + 3, LANE, 31, LANE + 1))
for i, colour in enumerate(('black', 'blue', 'red')):
    k.building(f'machiya-{colour}', 12 + 5 * i, 10, 5)            # feet on row 14
RAMEN = (27, 11)
k.building('toyama-ramen', *RAMEN, 4)                             # feet on row 14, door on column 28
k.solid_rect(R1 + 3, QUAY1 + 1, 31, 10)
for x in (R1 + 3,):
    for y in range(11, LANE):
        b.stamp('shrub-small', x, y)
k.solid_rect(31, 11, 31, 12)
b.stamp('shrub-small', 31, 11); b.stamp('shrub-small', 31, 12)
# the verge between the old street and the tram street
k.trees('hokuriku-ginkgo', [(14, 18), (27, 18)])
k.trees('sendai-maple', [(30, 18)])
b.stamp('lantern-red', 12, 17); b.stamp('lantern-red', 26, 17)

# ---- the tram street: the Glass Art Museum, the stop, a tram ----------------------------------
k.road_h(R1 + 1, EAST, TRAM, cap_w=True, cap_e=True)
for x in range(R1 + 2, EAST):
    b.put('Floor', x, TRAM + 1, 'toyama-tram-rail_0_0')
MUSEUM = (35, 13)                                     # feet on row 18, doors on columns 37-38
k.building('toyama-glass-museum', *MUSEUM, 6)
k.solid_rect(34, QUAY1 + 1, EAST, 12)
k.woods(34, QUAY1 + 1, EAST, 12, ['sendai-pine'], rng)
STOP = (20, 17)                                       # the shelter: feet on row 18, at the pavement's back
b.stamp('toyama-tram-stop', *STOP)
TRAMCAR = (19, TRAM)                                  # standing at the stop, on the rails
b.stamp('toyama-tram', *TRAMCAR)
for x in (16, 25, 34, 40):
    b.stamp('lamp-blue', x, TRAM + 3)
b.stamp('bicycle-blue', 34, 18); b.stamp('vending-white', 41, 17)

# ---- the south: woods, the old house, the path in from Shirakawa-go ----------------------------
b.autotile('dirt-outside-autotile', rect(P0, TRAM + 4, P1, H - 1))
b.put('Floor', P0, H - 1, 'dirt-outside-autotile_edge-w')     # the path runs on into Shirakawa-go: no rounded end
b.put('Floor', P1, H - 1, 'dirt-outside-autotile_edge-e')
k.house('blue', 24, 25)                               # the old Japanese house (posts 576, 611); feet on row 30
k.trees('sendai-maple', [(22, 30)])
b.stamp('sendai-stone-lantern', 27, 29)
k.woods(R1 + 1, TRAM + 4, P0 - 1, H - 1, WOODS, rng)
k.woods(P1 + 1, TRAM + 4, W - 1, H - 1, WOODS, rng)
for y in range(QUAY0, TRAM + 4):                      # the east hedge
    for x in (EAST + 1, EAST + 2):
        if not k.taken(x, y):
            b.stamp('shrub-small', x, y)
k.plants(rng, 40, R1 + 1, QUAY1 + 1, EAST, TRAM - 2)

# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Toyama', {})
k.dress()         # no invisible walls: a bare collider beside open ground becomes a shrub
b.finish()
cfg['rooms']['Toyama'] = b.room('Toyama', npcs=prev.get('npcs', []),
                                transporters=rg.kept_order(prev, hk.seams('Toyama')))
# the sea is navigable (src/AmbientBoats.js): cells, inclusive. The lane runs off
# the east edge of the map, so boats sail in and out there.
cfg['rooms']['Toyama']['waterways'] = [
    {'axis': 'h', 'row': 1, 'rows': 3, 'from': R0 + 1, 'to': W - 1},
]
rg.save_config(cfg)
print(f'Toyama {W}x{H}; tower at {TOWER}, museum at {MUSEUM}, tram stop at {STOP}, tram at {TRAMCAR}, '
      f'ramen shop at {RAMEN}; path south on columns {hk.T_PATH}, river on columns {hk.T_RIVER}')
