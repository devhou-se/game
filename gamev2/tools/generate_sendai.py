#!/usr/bin/env python3
"""generate_sendai.py — "Sendai", the samurai town (issue #66).

devhouse 2's first base (26-30 October 2025), built from what the twelve
Sendai posts say happened. A generated room (roomgen + prefabs, the
generate_osaka.py / generate_sapporo.py recipe), reachable ONLY by train: the
station house door on the north side leads into the SendaiStation interior
(built by generate_stations.py).

  north   the rail line, the platform and the station house, with the station
          forecourt below it
  NW      the AOBA CASTLE RUINS: a gravel terrace on a two-tier stone wall, up
          a flight of steps from the street. DATE MASAMUNE rides his bronze
          horse on a plinth at the top, the foundations of the great hall are
          laid out in paving beside him (post 505 walked them "like a
          warlord"), and the terrace's south edge looks out over the town
  N       downtown: an office tower, the British-style PUB the baseball finals
          were watched in, vending machines; across the main street a 7-Eleven
          (its door leads into KonbiniSendai1) under an apartment block
  NE      ZUIHODEN, Masamune's mausoleum: a black-and-gold hall at the top of
          six stone steps ("so many stairs", post 491), in a cedar grove
          behind an earthen wall
  middle  Aoba-dori, the east-west street, and the main street down from the
          station crossing it
  SW      the NIKKA DISTILLERY at the west edge of town: the red-brick kiln
          house with its pagoda roof, casks, and maples in autumn colour
          (Sakunami, 29 October). Yamadera is not built - one landmark stands
          for that day trip
  S       the samurai quarter: an earth lane between earthen walls and gates,
          machiya on its north side, a walled residence with a garden pond
          east of the main street (a gate at each end, so it is a way
          through), a courtyard house behind a gate on the south side, pines
          over every wall
  east    MATSUSHIMA BAY, the town's whole east edge: a promenade, the timber
          pier with the two-deck sightseeing boat moored at it, pine islets -
          one of them "a rock with a ball on top" (post 487). The channel
          beyond the islets is the room's `waterways` entry, so ambient boats
          sail it (src/AmbientBoats.js), in from the south edge of the map.
          The water is `pond-autotile`, so you can fish it from the promenade
          or the pier

Nobody gets lost behind a building: every building is solid over its whole
footprint here, roof rows included, and the cedar groves are solid throughout.

Landmark art is drawn by tools/generate_sendai_art.py. Deterministic and
idempotent: rebuilds rooms.Sendai from scratch each run, keeping any NPCs the
blog pipeline has placed there and the konbini door generate_konbinis.py wired
(on a first build there is none to keep: the door is sealed until that runs).
Fences and tracks are finished here (b.finish()), so a re-run on an unchanged
world changes nothing - tools/check_generators.py (issue #107).

Run from gamev2/:
    python3 tools/generate_sendai_art.py          # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_sendai.py
    python3 tools/generate_konbinis.py Sendai     # KonbiniSendai1 + its door (first build, or the store moved)
    python3 tools/generate_stations.py            # builds SendaiStation + registry
    python3 tools/config_to_tiled.py Sendai SendaiStation KonbiniSendai1
    node tools/play.js lint Sendai SendaiStation KonbiniSendai1
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 70, 48
b = rg.Builder(W, H)
rng = random.Random(66)

# Columns: the town is 2-55, the bay promenade 56-58, the shore 59, water 60-69.
# Rows: rail 3-5, station 6-11, the north blocks 12-20, AOBA-DORI (pavement 21,
# road 22-24, pavement 25), the verge and the old town below it, the LANE 34-35.
MAIN = 34                         # the main street's left kerb column (34-36)
AOBA = 22                         # Aoba-dori's top kerb row (22-24)
LANE0, LANE1 = 34, 35             # the samurai quarter's lane
PROM0, PROM1 = 56, 58             # the bay promenade
SHORE = 59                        # the bay's west bank
SOUTH = H - 1                     # the south fence row

b.fill('grass-autotile')


def solid_rect(x0, y0, x1, y1):
    b.solid(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def building(name, x, y, w, roof=2):
    """A street building, solid over its roof rows too: nobody walks in behind it."""
    doors = b.stamp(name, x, y)
    solid_rect(x, y, x + w - 1, y + roof - 1)
    return doors


def house(colour, x, y):
    """A townhouse (3x6: three roof rows on Tops), solid over the roof."""
    b.stamp(f'house-{colour}', x, y)
    solid_rect(x, y, x + 2, y + 2)


def trees(name, tall, cells):
    """Stamp `name` (2 wide, `tall` cells high) with its trunk on each (x, y)."""
    for x, y in cells:
        b.stamp(name, x, y - tall + 1)


def wall(x0, x1, y):
    """An earthen wall along rows y..y+1."""
    for x in range(x0, x1 + 1):
        b.stamp('sendai-earthen-wall', x, y)


def paved(cells, fam='flat-grey-brick-autotile'):
    for x, y in cells:
        b.put('Floor', x, y, f'{fam}_center')


# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-autotile', rect(0, 3, W - 1, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 24)) + list(range(37, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):                                   # caps at the corridor ends
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
trees('sendai-pine', 3, [(x, 2) for x in range(4, W - 3, 7)])   # pines beyond the tracks

# ---- station platform, station house, forecourt --------------------------------
b.autotile('light-concrete-autotile', rect(24, 6, 33, 8))
b.stamp('lamp-blue', 25, 7); b.stamp('lamp-blue', 32, 7)
b.stamp('vending-white', 27, 6); b.stamp('vending-red', 29, 6)
for i, px in enumerate((26, 28, 31)):
    b.paver(px, 8, i)
station_door = b.stamp('house-black', 34, 4, seal=False)[0]   # door -> SendaiStation
b.autotile('light-concrete-autotile', rect(22, 9, 37, 11))
b.stamp('sendai-stone-lantern', 33, 8); b.stamp('sendai-stone-lantern', 37, 8)     # either side of the door
trees('sendai-maple', 3, [(23, 10), (29, 10)])
for i, (px, py) in enumerate([(26, 9), (27, 11), (31, 10), (32, 9), (36, 11), (25, 11)]):
    b.paver(px, py, i)
b.stamp('shrub-large', 22, 7)                         # the platform's west end
for x in (37, 39, 41):                                # ...and the strip east of the station house
    b.stamp('shrub-large', x, 7)

# ---- streets ---------------------------------------------------------------------
# pavements first (one region each, so the paving has no seam where they meet)
b.autotile('light-concrete-autotile', rect(2, AOBA - 1, PROM1, AOBA - 1))
b.autotile('light-concrete-autotile', rect(2, AOBA + 3, PROM1, AOBA + 3))
b.autotile('light-concrete-autotile', rect(PROM0, 8, PROM1, SOUTH - 1))
paved(rect(MAIN - 1, 12, MAIN - 1, AOBA - 2) + rect(MAIN + 3, 12, MAIN + 3, AOBA - 2), 'light-concrete-autotile')
paved(rect(MAIN - 1, AOBA + 4, MAIN - 1, LANE0 - 1) + rect(MAIN + 3, AOBA + 4, MAIN + 3, LANE0 - 1),
      'light-concrete-autotile')
# Aoba-dori: the standard three-cell road, ending square at the hedge and the promenade
for x in range(2, PROM0):
    b.put('Floor', x, AOBA, 'road-edge-top_0_0')
    b.put('Floor', x, AOBA + 1, 'road-div-horizontal_0_0')
    b.put('Floor', x, AOBA + 2, 'road-edge-bottom_0_0')
for x, (top, mid, bottom) in ((2, ('road-corner-nw', 'road-edge-left', 'road-corner-sw')),
                              (PROM0 - 1, ('road-corner-ne', 'road-edge-right', 'road-corner-se'))):
    b.put('Floor', x, AOBA, f'{top}_0_0')
    b.put('Floor', x, AOBA + 1, f'{mid}_0_0')
    b.put('Floor', x, AOBA + 2, f'{bottom}_0_0')
# the main street: from the forecourt down to Aoba-dori, and on to the lane
for y in list(range(12, AOBA)) + list(range(AOBA + 3, LANE0 - 1)):
    b.put('Floor', MAIN, y, 'road-edge-left_0_0')
    b.put('Floor', MAIN + 1, y, 'road-div-vertical_0_0')
    b.put('Floor', MAIN + 2, y, 'road-edge-right_0_0')
for y, (left, mid, right) in ((12, ('road-corner-nw', 'road-edge-top', 'road-corner-ne')),
                              (LANE0 - 2, ('road-corner-sw', 'road-edge-bottom', 'road-corner-se'))):
    b.put('Floor', MAIN, y, f'{left}_0_0')
    b.put('Floor', MAIN + 1, y, f'{mid}_0_0')
    b.put('Floor', MAIN + 2, y, f'{right}_0_0')
for cx, cy in rect(MAIN, AOBA, MAIN + 2, AOBA + 2):   # the junction box
    b.put('Floor', cx, cy, 'road-plain_0_0')
# zebra crossings on three arms of the junction (the centre line stops for the stripes)
for cx, cy in rect(MAIN, AOBA - 2, MAIN + 2, AOBA - 2) + rect(MAIN - 3, AOBA, MAIN - 3, AOBA + 2) \
        + rect(MAIN + 5, AOBA, MAIN + 5, AOBA + 2):
    b.put('Floor', cx, cy, 'road-plain_0_0')
b.stamp('crossing-v', MAIN, AOBA - 2)
b.stamp('crossing-h', MAIN - 3, AOBA); b.stamp('crossing-h', MAIN + 5, AOBA)

# ---- the Aoba Castle ruins (north-west) -----------------------------------------
# cedars close the back of the terrace and its east side
trees('sendai-cedar', 4, [(x, 7) for x in range(2, 22, 2)])
trees('sendai-cedar', 4, [(20, y) for y in (10, 12, 14, 16, 18, 20)])
solid_rect(20, 7, 21, 20)
b.autotile('gravel-autotile', rect(2, 8, 19, 13))
# the stone wall the terrace stands on: two tiers of castle masonry, and the
# flight of steps up through it from the street
STAIR0, STAIR1 = 10, 11
for x in range(2, 20):
    if not STAIR0 <= x <= STAIR1:
        b.wall_stone(x, 14); b.wall_stone(x, 16)
paved(rect(STAIR0, 14, STAIR1, 20))
for x, y in rect(STAIR0, 14, STAIR1, 20):
    b.stairs(x, y)
MASAMUNE = (9, 7)                                     # on the axis of the steps
b.stamp('sendai-masamune', *MASAMUNE)                 # plinth on rows 9-10
b.stamp('sendai-stone-lantern', 7, 9); b.stamp('sendai-stone-lantern', 13, 9)
trees('sendai-pine', 3, [(3, 9)])                     # the overlook corner, west of the statue
for i, (px, py) in enumerate([(5, 12), (7, 13), (3, 13), (6, 10)]):
    b.paver(px, py, i)
# the great hall's foundations, laid out in paving with its pillar bases
b.autotile('flat-grey-brick-autotile', rect(14, 10, 19, 13))
for i, (px, py) in enumerate([(14, 10), (16, 10), (19, 10), (14, 13), (17, 13), (19, 13), (16, 12), (18, 11)]):
    b.paver(px, py, i)
b.stamp('sendai-stone-lantern', 9, 12); b.stamp('sendai-stone-lantern', 12, 12)   # the head of the steps
# the slope below the wall: pines either side of the steps
trees('sendai-pine', 3, [(3, 19), (7, 20), (14, 20), (17, 19)])
b.stamp('sendai-stone-lantern', 9, 19); b.stamp('sendai-stone-lantern', 12, 19)

# ---- downtown, west of the main street ------------------------------------------
building('highrise-yellow', 22, 13, 4)
PUB = (26, 16)
building('sendai-pub', *PUB, 5)
b.stamp('vending-white', 31, 17); b.stamp('vending-red', 32, 17)
b.autotile('grey-brick-autotile', rect(26, 12, 32, 15))            # the square behind the pub
b.stamp('tree-green', 27, 11); b.stamp('tree-green', 30, 12)
b.stamp('lantern-red', 26, 14)
b.stamp('bus-stop', 33, 13)

# ---- downtown, east of the main street: the 7-Eleven under an apartment block ----
building('highrise-apartment', 38, 9, 5)
KONBINI = (38, 17)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('sign-7-11', 41, 19); b.solid(41, 19)
b.stamp('vending-white', 42, 19); b.stamp('vending-red', 43, 19)
for x, y in ((41, 17), (42, 17), (41, 18), (42, 18)):
    b.stamp('shrub-small', x, y)

# ---- Zuihoden (north-east): the hall at the top of the steps, in the cedars ------
ZUIHODEN = (47, 8)
b.stamp('sendai-zuihoden', *ZUIHODEN)                 # rows 8-12
solid_rect(47, 8, 53, 8)
paved(rect(47, 13, 53, 14) + rect(49, 15, 51, 20))             # the landing, two rows deep
for x, y in rect(49, 15, 51, 20):
    b.stairs(x, y)
b.stamp('sendai-stone-lantern', 47, 13); b.stamp('sendai-stone-lantern', 53, 13)   # on the landing's corners
trees('sendai-cedar', 4, [(x, 7) for x in range(43, 55, 2)])       # behind the hall
trees('sendai-cedar', 4, [(x, y) for y in (10, 12) for x in (43, 45)] + [(54, 10), (54, 12)])
trees('sendai-cedar', 4, [(x, y) for y in (14, 16, 18) for x in (43, 45, 54)] + [(52, 16), (52, 18)])
trees('sendai-cedar', 4, [(47, 17)])
for x0, y0, x1, y1 in ((43, 7, 55, 7), (43, 8, 46, 12), (54, 8, 55, 12), (43, 13, 46, 14), (54, 13, 55, 14),
                       (43, 15, 48, 18), (52, 15, 55, 18)):
    solid_rect(x0, y0, x1, y1)
wall(44, 48, 19); wall(52, 55, 19)

# ---- the Nikka distillery, at the west edge ---------------------------------------
KILN = (3, 28)
building('sendai-kiln', *KILN, 5, roof=3)             # feet on row 33, on the lane
b.stamp('sendai-barrels', 8, 32)
b.stamp('sendai-barrels', 10, 32)
b.stamp('shrub-small', 2, 33); b.stamp('shrub-small', 2, 32)
trees('sendai-maple', 3, [(9, 30), (12, 28), (2, 27), (12, 32)])
b.flowers(6, 26); b.flowers(10, 26)

# ---- the samurai quarter -------------------------------------------------------------
b.autotile('dirt-outside-autotile', rect(2, LANE0, PROM0 - 1, LANE1))
# north side, west of the main street: machiya shoulder to shoulder, then a
# walled plot on the corner
for i, colour in enumerate(('black', 'red', 'blue')):
    building(f'machiya-{colour}', 15 + 5 * i, 29, 5)              # feet on row 33
wall(30, 32, 32)
trees('sendai-pine', 3, [(30, 31)])
b.solid(32, 31)
trees('sendai-pine', 3, [(17, 27), (24, 28)])                      # on the verge behind them
# north side, east of the main street: a residence and its garden, a gate on the
# lane and open to Aoba-dori's pavement - a way through, not a dead end
wall(38, 43, 32); wall(48, 55, 32)
GATE_N = (44, 31)
b.stamp('sendai-gate', *GATE_N)
b.autotile('gravel-autotile', rect(45, 26, 46, 33))
house('black', 39, 26)                                             # feet on row 31
b.solid(38, 31); b.solid(42, 31); b.solid(43, 31)
b.pond(49, 28, 53)
trees('sendai-pine', 3, [(48, 31), (53, 31)])
b.stamp('sendai-stone-lantern', 47, 28); b.stamp('sendai-stone-lantern', 54, 26)
b.stamp('sendai-stone-lantern', 44, 28)
trees('sendai-maple', 3, [(42, 29)])
solid_rect(50, 31, 52, 31); solid_rect(55, 30, 55, 31)
for i, (px, py) in enumerate([(50, 31), (51, 31), (52, 31), (55, 30), (55, 31)]):
    b.put('Collidables', px, py, 'shrub-small-circle_0_0')
# south side: one long earthen wall a row back from the lane (so the gate's roof
# is over the verge, not over the lane), with a gate into a courtyard house
GATE_S = (20, 36)
wall(2, 19, 37); wall(24, PROM0 - 1, 37)
b.stamp('sendai-gate', *GATE_S)
b.autotile('gravel-autotile', rect(19, 39, 28, 45))
paved(rect(21, 37, 22, 38), 'gravel-autotile')
house('black', 25, 39)                                             # feet on row 44
trees('sendai-pine', 3, [(19, 42)])
b.stamp('sendai-stone-lantern', 23, 39)
b.pond(19, 44, 22)
for y in range(39, SOUTH):                                         # the courtyard's side hedges
    b.stamp('shrub-small', 18, y); b.stamp('shrub-small', 29, y)
# the compounds behind the wall, seen over it: roofs and pines
for colour, x in (('blue', 4), ('black', 10), ('red', 33), ('black', 40), ('blue', 47)):
    house(colour, x, 40)                                           # feet on row 45
trees('sendai-pine', 3, [(2, 42), (8, 41), (14, 42), (16, 45), (31, 42), (37, 41), (44, 42), (51, 41), (54, 44),
                          (54, 40)])
b.stamp('shrub-small', 55, 39); b.stamp('shrub-small', 55, 45)
trees('sendai-maple', 3, [(13, 46), (36, 45), (52, 46)])
for x0, x1 in ((2, 17), (30, PROM0 - 1)):                          # ...and nobody walks there
    solid_rect(x0, 39, x1, SOUTH - 1)

# ---- Matsushima bay: the east edge -----------------------------------------------------
BAY_Y = 7
for x in range(SHORE, W):
    for y in range(BAY_Y, H):
        role = 'edge-w' if x == SHORE else 'edge-n' if y == BAY_Y else 'center'
        b.put('Water', x, y, f'pond-autotile_{role}')
PIER = (SHORE, 30)                                    # five cells out from the bank
pier_cells = {(PIER[0] + i, PIER[1]) for i in range(5)}
for x in range(SHORE, W):
    for y in range(BAY_Y, H):
        if (x, y) not in pier_cells:
            b.solid(x, y)
b.stamp('matsushima-pier', *PIER)
FERRY = (60, 28)
b.stamp('matsushima-ferry', *FERRY)                   # moored along the pier's north side
b.stamp('matsushima-islet', 61, 11); b.stamp('matsushima-islet', 61, 37)
b.stamp('matsushima-ball-rock', 62, 18)               # "a rock with a ball on top" (post 487)
b.stamp('matsushima-islet-small', 60, 23); b.stamp('matsushima-islet-small', 63, 43)
b.stamp('matsushima-islet-small', 63, 14); b.stamp('matsushima-islet-small', 60, 33)
b.stamp('matsushima-islet', 60, 45)
CHANNEL_X0, CHANNEL_X1 = 66, 68                       # clear water: the boats' lane
for x in (PROM0, PROM0 + 1, PROM1):
    b.stamp('shrub-small', x, 7)
for y in (12, 20, 36, 44):
    b.stamp('lamp-blue', PROM1, y)
trees('sendai-pine', 3, [(PROM0, 16), (PROM0, 40)])   # the pines Matsushima is named for
for i, (px, py) in enumerate([(57, 27), (57, 31), (58, 33), (57, 10), (58, 23), (57, 42)]):
    b.paver(px, py, i)

# ---- lamps, borders, greenery --------------------------------------------------------
for x in (5, 15, 24, 31, 44, 54):                     # clear of the doors, the steps and the crossings
    b.stamp('lamp-blue', x, AOBA - 1)
for x in (8, 19, 28, 41, 49):
    b.stamp('lamp-blue', x, AOBA + 3)
# west hedge (continuous - a gap would let the player slip round behind the fences)
for y in range(7, SOUTH, 2):
    b.stamp('shrub-large', 0, y)
b.stamp('shrub-small', 0, 6); b.stamp('shrub-small', 0, SOUTH)
for i, x in enumerate(range(1, SHORE)):
    b.fence(x, SOUTH, i)
# plants on the open grass
for i in range(160):
    sx, sy = rng.randrange(2, PROM0), rng.randrange(18, 37)
    if all(f'{sx},{sy}' not in b.L[n] for n in
           ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water', 'Tops')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      platform, so a platform-edge fence closes the gravel row behind it -------
for x in range(24, 37):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into SendaiStation (the
# konbini leads to its own interior and back).
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Sendai', {})
# the konbini door keeps the transporter generate_konbinis.py wired onto it;
# with none to keep (a first build) it is sealed until that runs
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
cfg['rooms']['Sendai'] = b.room('Sendai', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    # into the station at its entry cell (generate_stations.py: a large station's is not 11,11)
    rg.transporter(station_door[0], station_door[1], 'SendaiStation',
                   *cfg.get('stations', {}).get('SendaiStation', {}).get('entry', [11, 11]), hidden=True),
] + ([konbini_entry] if konbini_entry else [])))
# the bay is navigable (src/AmbientBoats.js): cells, inclusive. The channel runs
# off the south edge of the map, so boats sail in and out there.
cfg['rooms']['Sendai']['waterways'] = [
    {'axis': 'v', 'col': CHANNEL_X0, 'cols': CHANNEL_X1 - CHANNEL_X0 + 1, 'from': BAY_Y + 1, 'to': H - 1},
]

rg.save_config(cfg)
print(f'Sendai {W}x{H}; station house door at {station_door} -> SendaiStation; '
      f'Masamune at {MASAMUNE}, Zuihoden at {ZUIHODEN}, pub at {PUB}, konbini at {KONBINI}, '
      f'kiln at {KILN}, ferry at {FERRY}')
