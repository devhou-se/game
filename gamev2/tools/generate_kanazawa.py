#!/usr/bin/env python3
"""generate_kanazawa.py — "Kanazawa", the full town of the Hokuriku region
(issue #68, stage 3).

devhouse 2 was here on 5-8 November 2025, and the town is built from what its
posts say happened. It is one of the three districts of the stitched
`HokurikuCity` (tools/hokuriku.py has the layout): you arrive by train
(`KanazawaStation`, the Hokuriku line from Tokyo) and WALK on, out of the east
end of the avenue, to Shirakawa-go and Toyama.

  north   the rail line, the platform and the station house, the forecourt
  NW      HIGASHI CHAYA: a paved lane under a row of four teahouses (bengara
          lattice, bamboo blinds, a noren each) and two shops, a cedar hill
          behind them (posts 669, 686, 707: tea and wagashi, gold leaf)
  W       downtown, on the avenue: a machiya, the WHISKY BAR (posts 635, 653,
          677, 686 - "our favourite whiskey bar"), an office tower, a 7-Eleven
          (its door leads into KonbiniKanazawa1; post 686's berry smoothie)
  NE      KANAZAWA CASTLE: the Ishikawa gate, and beyond it the grounds - a
          gravel terrace with the keep's foundations and nothing on them
          ("Kanazawa Castle has no castle", post 652; "under reconstruction",
          post 662, hence the cones)
  E       KENROKUEN, between the gate and the avenue: the pond, the two-legged
          Kotoji lantern on its bank, pines, maples and ginkgo in November colour
  middle  the avenue (rows 30-32), which runs out of the east edge as the road
          to Shirakawa-go; the main street comes down to it from the station
  SW      NAGAMACHI, the samurai quarter: an earth lane between earthen walls
          with pines over them, the canal along its south side, a stone bridge
          to a samurai gate and the house behind it (posts 652, 662, 677)
  SE      Teramachi's wood of shrines: a shrine in a clearing among cedars,
          down a path from the avenue (post 707: "a forest full of shrines")

Nobody gets lost behind a building: every building is solid over its roof rows,
and the woods and the walled compounds are solid throughout.

Art is drawn by tools/generate_hokuriku_art.py (and Sendai's walls, gate, pines
and maples by tools/generate_sendai_art.py). Deterministic and idempotent:
rebuilds rooms.Kanazawa from scratch each run, keeping any NPCs the blog
pipeline has placed there and the konbini door generate_konbinis.py wired (on
a first build the door is sealed until that runs). Fences and tracks are
finished here (b.finish()), so a re-run on an unchanged world changes nothing
(tools/check_generators.py).

Run from gamev2/ (the whole region):
    python3 tools/generate_hokuriku_art.py        # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_kanazawa.py
    python3 tools/generate_shirakawago.py
    python3 tools/generate_toyama.py
    python3 tools/generate_konbinis.py Kanazawa   # KonbiniKanazawa1 + its door
    python3 tools/generate_houses.py Kanazawa     # HouseKanazawa1..4 + their doors (kept through a rebuild by roomgen)
    python3 tools/generate_stations.py            # KanazawaStation + registry
    python3 tools/config_to_tiled.py Kanazawa Shirakawago Toyama KanazawaStation KonbiniKanazawa1 \
        HouseKanazawa1 HouseKanazawa2 HouseKanazawa3 HouseKanazawa4
    python3 tools/sync_cities.py                  # after placing the three maps in ../devhouse.world
    node tools/play.js lint Kanazawa Shirakawago Toyama HokurikuCity
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect
import hokuriku as hk

cfg = rg.load_config()

W, H = hk.SIZE['Kanazawa']
b = rg.Builder(W, H)
k = hk.Kit(b)
rng = random.Random(68)

MAIN = 32                         # the main street's left kerb column (32-34)
AVE = hk.K_ROAD[0]                # the avenue's top kerb row (30-32)
LANE0, LANE1 = 38, 39             # Nagamachi's lane
CANAL = 40                        # the canal's two rows (40-41)
SOUTH = H - 1                     # the south fence row
CHAYA_LANE = 19                   # Higashi Chaya's paved lane (19-20)

b.fill('grass-autotile')

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-autotile', rect(0, 3, W - 1, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 22)) + list(range(35, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):
    b.stamp('shrub-small', 0, y)                      # the corridor's west end (the east runs on into the woods)
k.trees('sendai-pine', [(x, 2) for x in range(4, W - 3, 7)])

# ---- station platform, station house, forecourt --------------------------------
b.autotile('light-concrete-autotile', rect(22, 6, 31, 8))
b.stamp('lamp-blue', 23, 7); b.stamp('lamp-blue', 30, 7)
b.stamp('vending-white', 25, 6); b.stamp('vending-red', 27, 6)
for i, px in enumerate((24, 26, 29)):
    b.paver(px, 8, i)
station_door = b.stamp('house-black', MAIN, 4, seal=False)[0]     # door -> KanazawaStation
b.autotile('light-concrete-autotile', rect(20, 9, 37, 11))
b.stamp('sendai-stone-lantern', 31, 8); b.stamp('sendai-stone-lantern', 35, 8)
k.trees('hokuriku-ginkgo', [(21, 10), (27, 10)])
for i, (px, py) in enumerate([(24, 9), (25, 11), (29, 10), (30, 9), (36, 11), (23, 11)]):
    b.paver(px, py, i)
b.stamp('shrub-large', 20, 7)
b.stamp('shrub-large', 36, 7)

# ---- streets ---------------------------------------------------------------------
b.autotile('light-concrete-autotile', rect(2, AVE - 1, W - 1, AVE - 1))
b.autotile('light-concrete-autotile', rect(2, AVE + 3, W - 1, AVE + 3))
k.paved(rect(MAIN - 1, 12, MAIN - 1, AVE - 2) + rect(MAIN + 3, 12, MAIN + 3, AVE - 2), 'light-concrete-autotile')
k.road_h(2, W - 1, AVE, cap_w=True)                   # the avenue: closed at the west hedge, open to the east
for y in range(12, AVE):                              # the main street, station to avenue
    b.put('Floor', MAIN, y, 'road-edge-left_0_0')
    b.put('Floor', MAIN + 1, y, 'road-div-vertical_0_0')
    b.put('Floor', MAIN + 2, y, 'road-edge-right_0_0')
for x, piece in zip(range(MAIN, MAIN + 3), ('road-corner-nw', 'road-edge-top', 'road-corner-ne')):
    b.put('Floor', x, 12, f'{piece}_0_0')
for cx, cy in rect(MAIN, AVE, MAIN + 2, AVE + 1):     # the T junction: plain, the far kerb unbroken
    b.put('Floor', cx, cy, 'road-plain_0_0')
for cx, cy in rect(MAIN - 4, AVE, MAIN - 4, AVE + 2) + rect(MAIN, AVE - 2, MAIN + 2, AVE - 2):
    b.put('Floor', cx, cy, 'road-plain_0_0')          # under the zebra crossings
b.stamp('crossing-h', MAIN - 4, AVE)
b.stamp('crossing-v', MAIN, AVE - 2)
# the road out of town is the only way across the east edge: the pavements end in a hedge
for y in (AVE - 1, AVE + 3):
    b.stamp('shrub-small', W - 2, y); b.stamp('shrub-small', W - 1, y)
b.stamp('bus-stop', W - 4, AVE - 1)                   # the bus to Shirakawa-go (posts 635, 653)

# ---- Higashi Chaya (north-west): the teahouse row on its paved lane ---------------
b.autotile('flat-grey-brick-autotile', rect(2, CHAYA_LANE, MAIN - 2, CHAYA_LANE + 1))
CHAYA = (4, 15)                                       # the first of the row; feet on row 18
for i in range(4):
    k.building('kanazawa-chaya-' + 'ab'[i % 2], CHAYA[0] + 4 * i, CHAYA[1], 4)
k.building('machiya-red', 21, 14, 5)                  # the gold-leaf shops (post 707)
k.building('machiya-blue', 26, 14, 5)
b.stamp('lantern-red', 20, 17); b.stamp('lantern-red', 3, 17)
for x, y in ((2, 15), (2, 16), (2, 17), (2, 18), (3, 15), (3, 16), (20, 15), (20, 16)):
    b.stamp('shrub-small', x, y)
k.woods(2, 7, 19, 14, ['sendai-cedar', 'sendai-cedar', 'sendai-pine'], rng)       # the hill behind the row
k.woods(20, 12, 30, 13, ['sendai-pine'], rng, over=0)        # a hedge: no canopy over the forecourt
b.solid(20, 14)

# ---- downtown: the avenue's north side ----------------------------------------------
k.wall(2, 13, 21); k.wall(18, MAIN - 2, 21)           # the lane's south side: an earthen wall
k.building('machiya-black', 3, 24, 5)
BAR = (9, 25)
k.building('kanazawa-whisky-bar', *BAR, 4)
k.building('highrise-yellow', 14, 21, 4)
KONBINI = (19, 25)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('sign-7-11', 22, 27); b.solid(22, 27)
b.stamp('vending-white', 23, 27); b.stamp('vending-red', 24, 27)
k.building('midrise-apartment', 26, 23, 5)
for x, y in rect(2, 23, MAIN - 2, 28):                # the gaps between and behind them are hedge
    if not k.taken(x, y) and (x, y) != konbini_door:
        b.stamp('shrub-small', x, y)

# ---- Kanazawa Castle (north-east): the Ishikawa gate and the empty grounds --------
GATE = (40, 14)                                       # gateway on columns 43-44
b.autotile('gravel-autotile', rect(40, 8, 57, 13))
k.paved(rect(43, 14, 44, 17), 'gravel-autotile')
b.stamp('kanazawa-ishikawa-gate', *GATE)
for x in list(range(38, 40)) + list(range(48, 58)):   # the castle wall either side of it
    b.wall_stone(x, 16)
k.solid_rect(38, 14, 39, 15); k.solid_rect(48, 14, 57, 15)
k.trees('sendai-pine', [(38, 15), (50, 15), (55, 15)])
k.trees('sendai-cedar', [(x, 7) for x in range(40, 58, 2)])
k.solid_rect(40, 7, 57, 7)
k.woods(38, 7, 39, 13, ['sendai-cedar'], rng, over=3)
# the keep's foundations, laid out in paving, and nothing on them
b.autotile('flat-grey-brick-autotile', rect(47, 9, 55, 12))
for i, (px, py) in enumerate([(47, 9), (51, 9), (55, 9), (47, 12), (51, 12), (55, 12), (49, 10), (53, 11)]):
    b.paver(px, py, i)
for x, y in ((46, 13), (56, 13), (46, 8), (56, 8)):
    b.stamp('traffic-cone', x, y)                     # "under reconstruction" (post 662)
k.trees('sendai-pine', [(41, 10)])
b.stamp('sendai-stone-lantern', 41, 12); b.stamp('sendai-stone-lantern', 46, 11)
for y in range(12, 28, 2):                            # the hedge between the main street and the park
    b.stamp('shrub-large', 36, y)
for y in range(7, 29, 2):                             # ...and down the east edge
    b.stamp('shrub-large', 58, y)

# ---- Kenrokuen: between the gate and the avenue --------------------------------------
b.autotile('gravel-autotile', rect(43, 18, 44, 28) + rect(45, 20, 56, 22))
POND = (47, 23)
b.pond(POND[0], POND[1], 54)
KOTOJI = (49, 21)
b.stamp('kanazawa-kotoji', *KOTOJI)                   # on the pond's north bank
b.stamp('sendai-stone-lantern', 57, 20)
k.trees('sendai-pine', [(46, 19), (55, 19)])
k.trees('sendai-maple', [(46, 27), (53, 27)])
k.trees('hokuriku-ginkgo', [(49, 27), (56, 26)])
k.woods(38, 18, 42, 27, ['sendai-pine', 'sendai-maple', 'hokuriku-ginkgo'], rng)
for x in list(range(38, 43)) + list(range(45, 58)):   # a clipped hedge along the pavement, the path between
    if not k.taken(x, 28):
        b.stamp('shrub-small', x, 28)

# ---- Nagamachi, the samurai quarter (south-west) ---------------------------------------
b.autotile('dirt-outside-autotile', rect(2, LANE0, 33, LANE1) + rect(16, AVE + 4, 17, LANE0 - 1)
           + rect(32, AVE + 4, 33, LANE0 - 1))
k.wall(2, 15, 36); k.wall(18, 31, 36)                 # the lane's north side, pines over the wall
k.trees('sendai-pine', [(4, 35), (10, 35), (21, 35), (27, 35)])
k.solid_rect(2, 34, 15, 35); k.solid_rect(18, 34, 31, 35)
# the canal along the lane's south side
for x in range(2, 33):
    b.put('Water', x, CANAL, 'pond-autotile_edge-n'); b.put('Water', x, CANAL + 1, 'pond-autotile_edge-s')
b.put('Water', 33, CANAL, 'pond-autotile_corner-ne'); b.put('Water', 33, CANAL + 1, 'pond-autotile_corner-se')
BRIDGE = (20, 39)                                     # a stone slab over it, lane to gate
bridge_cells = set(rect(BRIDGE[0], CANAL, BRIDGE[0] + 1, CANAL + 1))
for x, y in rect(2, CANAL, 33, CANAL + 1):
    if (x, y) not in bridge_cells:
        b.solid(x, y)
b.stamp('kanazawa-canal-bridge', *BRIDGE)
# the far bank: the wall again, a samurai gate at the bridge, a house in its court
k.wall(2, 18, 42); k.wall(23, 33, 42)
SAMURAI_GATE = (19, 41)
b.stamp('sendai-gate', *SAMURAI_GATE)
b.autotile('gravel-autotile', rect(19, 44, 28, 50))
k.paved(rect(20, 42, 21, 43), 'gravel-autotile')
k.house('black', 24, 44)                              # feet on row 49
k.trees('sendai-pine', [(19, 47)])
k.trees('hokuriku-ginkgo', [(27, 50)])
b.stamp('sendai-stone-lantern', 22, 45)
for y in range(44, SOUTH):
    b.stamp('shrub-small', 18, y); b.stamp('shrub-small', 29, y)
# the compounds behind the wall, seen over it: roofs and pines
for colour, x in (('blue', 4), ('black', 10), ('red', 30)):
    k.house(colour, x, 45)                            # feet on row 50
k.trees('sendai-pine', [(2, 47), (8, 46), (14, 48), (16, 50)])
k.trees('sendai-maple', [(14, 45)])
k.solid_rect(2, 44, 17, SOUTH - 1); k.solid_rect(30, 44, 33, SOUTH - 1)
k.woods(34, 34, 35, 50, ['sendai-cedar'], rng)        # between the quarter and the wood of shrines

# ---- Teramachi: a shrine in the wood (south-east) -----------------------------------------
SHRINE = (43, 36)                                     # the hall's steps come down to row 43
b.stamp('shrine', *SHRINE)
b.autotile('dirt-outside-autotile', rect(50, AVE + 4, 51, 43))
b.autotile('gravel-autotile', rect(41, 44, 51, 47))
b.stamp('fox-statue', 43, 43); b.stamp('fox-statue', 47, 43)
b.stamp('sendai-stone-lantern', 41, 44); b.stamp('sendai-stone-lantern', 49, 44)
# the wood stands back from the hall's bottom step (a cedar grew on it, across the door: issue #212)
k.woods(36, 34, 49, 43, ['sendai-cedar', 'sendai-cedar', 'sendai-maple'], rng,
        clear=[(SHRINE[0] + dx, SHRINE[1] + 7) for dx in (1, 2, 3)])
k.woods(52, 34, 57, 50, ['sendai-cedar', 'sendai-cedar', 'sendai-maple'], rng)
k.woods(36, 44, 40, 47, ['sendai-cedar'], rng)
k.woods(36, 48, 51, 50, ['sendai-cedar', 'sendai-maple'], rng)
for y in range(34, SOUTH, 2):
    b.stamp('shrub-large', 58, y)

# ---- lamps, borders, greenery --------------------------------------------------------
for x in (7, 12, 25, 40, 52):                         # clear of the doors and the crossings
    b.stamp('lamp-blue', x, AVE - 1)
for x in (9, 22, 42, 54):
    b.stamp('lamp-blue', x, AVE + 3)
for y in range(7, SOUTH, 2):                          # the west hedge, continuous
    b.stamp('shrub-large', 0, y)
b.stamp('shrub-small', 0, 6); b.stamp('shrub-small', 0, SOUTH)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, SOUTH, i)
b.stamp('shrub-small', W - 1, SOUTH)
k.plants(rng, 140, 2, 12, W - 3, SOUTH - 1)

# ---- keep the player off the ballast: a platform-edge fence ----------------------------
for x in range(22, 35):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Kanazawa', {})
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)                            # sealed until generate_konbinis.py wires it
k.dress()         # no invisible walls: a bare collider beside open ground becomes a shrub
b.finish()
cfg['rooms']['Kanazawa'] = b.room('Kanazawa', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    # into the station at its entry cell (generate_stations.py: a large station's is not 11,11)
    rg.transporter(station_door[0], station_door[1], 'KanazawaStation',
                   *cfg.get('stations', {}).get('KanazawaStation', {}).get('entry', [11, 11]), hidden=True),
] + hk.seams('Kanazawa') + ([konbini_entry] if konbini_entry else [])))

rg.save_config(cfg)
print(f'Kanazawa {W}x{H}; station house door at {station_door} -> KanazawaStation; '
      f'gate at {GATE}, Kotoji at {KOTOJI}, teahouses from {CHAYA}, bar at {BAR}, konbini at {KONBINI}, '
      f'samurai gate at {SAMURAI_GATE}, shrine at {SHRINE}; road east on rows {hk.K_ROAD}')
