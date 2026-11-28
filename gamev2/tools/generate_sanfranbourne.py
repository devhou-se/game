#!/usr/bin/env python3
"""generate_sanfranbourne.py — the home city (issue #218).

devhouse people come from Melbourne or from San Francisco, so home is both at
once: one city, not two halves. A generated room (roomgen, the
generate_fukuoka.py recipe). Reachable ONLY by air: the terminal's doors in the
north-west lead into its airport (tools/generate_airports.py); no train line
comes here and it is on no departures board. North to south:

  north   the AIRPORT TERMINAL and its control tower (west); the SPORTS GROUND
          (east): an oval with four posts at each end and light towers, and
          the fog that rolls in over it every afternoon
  street  the tram street: a CABLE CAR and a GREEN-AND-YELLOW TRAM share one
          pair of rails, the cable car west of the avenue and the tram east of
          it; the avenue crosses on a signalled zebra crossing. Neither is a
          tile: each runs its rails and can be ridden (the room's `tramways`,
          src/AmbientTrams.js, issue #245)
  hill    PAINTED LADIES in a row, each a step higher than the last, on a
          bluestone wall covered in STREET ART with COFFEE WINDOWS let into it;
          the laneway runs along its foot (milk crates for seats)
  city    the POINTY PYRAMID beside the ARTS-CENTRE SPIRE, a glass tower, the
          7-Eleven and vending machines, on a paved plaza; and here and there
          on the pavements somebody standing folded double at the waist
  river   the brown river, rowers on it, and the RED SUSPENSION BRIDGE that
          carries the avenue over: you walk between the legs of its towers
  south   the yellow STATION WITH THE CLOCKS over its door (nobody catches a
          train there: you meet under the clocks; its two doors open into
          a room built by tools/generate_flinders.py, which owns them),
          a palm garden, townhouses
  bay     the boardwalk, the PIER, the raft of SEA LIONS beside it, and the
          island with the lighthouse out in the fog

The avenue (columns 28-31) is the spine: crossing -> past the lane and the
plaza -> the bridge -> past the station -> the pier.

The display name is NAME below and nowhere else: it is written to
rooms.SanFranbourne.name, and the Map label, the flights board and the footer
all read it from there (config `places` / `airports` carry no copy).

Houses stay sealed (tools/generate_houses.py is not run for this town here);
its glass tower's lobby comes from `generate_houses.py --lobbies SanFranbourne`,
which opens the tower's pair of doors, kept through a rebuild of the town.
Nobody is placed here by a trip, and `blog: false` keeps the blog pipeline out
(tools/blog_to_npc.py overworld_rooms). Deterministic and idempotent; keeps any
NPCs and the konbini door generate_konbinis.py wired (sealed until that runs).

Run from gamev2/:
    python3 tools/generate_sanfranbourne_art.py       # sprites (needs Pillow)
    python3 tools/generate_airports.py
    python3 tools/generate_sanfranbourne.py
    python3 tools/generate_konbinis.py SanFranbourne  # KonbiniSanFranbourne1 + its door
    python3 tools/config_to_tiled.py SanFranbourne SanFranbourneAirport KonbiniSanFranbourne1
    node tools/play.js lint SanFranbourne
"""
import roomgen as rg
from roomgen import rect

NAME = 'San Franbourne'         # the one place the city's display name is written
KEY = 'SanFranbourne'
AIRPORT = 'SanFranbourneAirport'

cfg = rg.load_config()

W, H = 60, 60
b = rg.Builder(W, H)

AVE_X0, AVE_X1 = 28, 31                  # the avenue, the bridge deck and the pier
STREET_Y = 15                            # top row of the tram street (three rows)
LADIES_Y, WALL_Y, LANE_Y = 19, 24, 26    # the terrace, the wall under it, the laneway (two rows)
RIVER_Y0, RIVER_Y1 = 33, 37
BOARDWALK_Y0, BOARDWALK_Y1 = 46, 48
SHORE_Y = 49                             # the waterline; the bay is everything below


def place(layer, x, y, sprite, solid=()):
    b.place(layer, x, y, f'{sprite}_0_0', solid)


b.fill('grass-autotile')

# ---- paving ---------------------------------------------------------------------
b.autotile('light-concrete-autotile', rect(2, 13, 57, 14) + rect(2, 18, 57, 18))          # the street's pavements
b.autotile('grey-brick-autotile', rect(4, LANE_Y, 27, LANE_Y + 1))                        # the laneway (bluestone)
b.autotile('brown-brick-autotile', rect(2, 19, 4, LANE_Y - 1))                            # the steps down to it
b.autotile('grey-brick-autotile', rect(33, 19, 57, 31))                                   # the city plaza
b.autotile('light-concrete-autotile', rect(2, 30, 27, 31))                                # the north bank
b.autotile('light-concrete-autotile', rect(2, 39, 27, 40) + rect(32, 39, 57, 40))         # the south bank
b.autotile('grey-brick-autotile', rect(12, 46, 25, 47))                                   # under the clocks
b.autotile('brown-brick-autotile', rect(2, BOARDWALK_Y0, 57, BOARDWALK_Y1))               # the boardwalk
b.autotile('flat-grey-brick-autotile', rect(AVE_X0, 18, AVE_X1, BOARDWALK_Y1))            # the avenue

# ---- the bay along the south: the waterline, then open water ---------------------
for x in range(W):
    if not AVE_X0 <= x <= AVE_X1:
        b.put('Water', x, SHORE_Y, 'beach-shore-n_0_0'); b.solid(x, SHORE_Y)
    for y in range(SHORE_Y + 1, H):
        b.put('Water', x, y, 'pond-autotile_center')
        b.solid(x, y)
for x in range(AVE_X0, AVE_X1 + 1):
    b.put('Water', x, SHORE_Y, 'pond-autotile_center')
PIER = (AVE_X0, BOARDWALK_Y1 + 1)        # 4x9: rows 49-57
place('Non-Collidables', *PIER, 'sfb-pier')
for cx, cy in rect(PIER[0], SHORE_Y + 1, PIER[0] + 3, PIER[1] + 7):   # the deck is walked on (its last row is the edge)
    del b.L['Colliders'][f'{cx},{cy}']
SEA_LIONS = (AVE_X0 - 3, 52)             # beside the pier: bump them from it
place('Collidables', *SEA_LIONS, 'sfb-sea-lions')
ROCK = (44, 54)
place('Collidables', *ROCK, 'sfb-rock')
b.put('Tops', 36, 56, 'sfb-fog-b_0_0'); b.put('Tops', 6, 55, 'sfb-fog-a_0_0'); b.put('Tops', 50, 51, 'sfb-fog-a_0_0')

# ---- the airport terminal, north-west: doors -> the airport hall ------------------
TERMINAL = (5, 8)
place('Collidables', *TERMINAL, 'sfb-terminal', rg.block(9, 5, 2))
airport_doors = [(TERMINAL[0] + 4, TERMINAL[1] + 4), (TERMINAL[0] + 5, TERMINAL[1] + 4)]
for cell in airport_doors:
    del b.L['Colliders'][f'{cell[0]},{cell[1]}']
place('Collidables', 2, 9, 'sfb-palm', [(1, 3)]); place('Collidables', 15, 9, 'sfb-palm', [(1, 3)])
b.stamp('lamp-blue', 4, 13); b.stamp('lamp-blue', 15, 13)
for x in (19, 22, 25):
    b.stamp('tree-green', x, 9)

# ---- the sports ground, north-east: the oval (flat), posts, lights, fog -----------
OVAL = (36, 4)
place('Non-Collidables', *OVAL, 'sfb-oval')
place('Collidables', OVAL[0], OVAL[1] + 2, 'sfb-goalposts', [(0, 2), (1, 2)])
place('Collidables', OVAL[0] + 10, OVAL[1] + 2, 'sfb-goalposts', [(0, 2), (1, 2)])
for x, y in ((34, 0), (49, 0), (34, 8), (49, 8)):
    place('Collidables', x, y, 'sfb-oval-lamp-post', [(0, 4)])
for (x, y), kind in (((37, 3), 'a'), ((43, 5), 'b'), ((39, 8), 'b'), ((51, 3), 'a'), ((30, 5), 'b')):
    b.put('Tops', x, y, f'sfb-fog-{kind}_0_0')
b.stamp('tree-green', 52, 9); b.stamp('tree-green', 55, 6)

# ---- the tram street: the standard three-cell road, closed at both ends, the
#      rails down its middle; the avenue crosses on a signalled zebra crossing ------
ROAD_X0, ROAD_X1 = 3, 56
for (x, top, mid, bot) in ((ROAD_X0, 'corner-nw', 'edge-left', 'corner-sw'), (ROAD_X1, 'corner-ne', 'edge-right', 'corner-se')):
    b.put('Floor', x, STREET_Y, f'road-{top}_0_0')
    b.put('Floor', x, STREET_Y + 1, f'road-{mid}_0_0')
    b.put('Floor', x, STREET_Y + 2, f'road-{bot}_0_0')
for x in range(ROAD_X0 + 1, ROAD_X1):
    crossing = AVE_X0 <= x <= AVE_X1
    b.put('Floor', x, STREET_Y, 'road-edge-top_0_0')
    b.put('Floor', x, STREET_Y + 1, 'road-plain_0_0')
    b.put('Floor', x, STREET_Y + 2, 'road-edge-bottom_0_0')
    if not crossing:
        b.put('Over Floor', x, STREET_Y + 1, 'sfb-rail-h_0_0')
for x in range(AVE_X0, AVE_X1 + 1):
    b.stamp('crossing-h', x, STREET_Y)
b.stamp('traffic-light', AVE_X0 - 1, STREET_Y - 3)
b.stamp('traffic-light', AVE_X1 + 1, STREET_Y + 1)
for x in (7, 18, 24, 36, 44, 54):
    b.stamp('lamp-blue', x, STREET_Y + 3)
BUS_STOP = (20, STREET_Y - 1)
b.stamp('bus-stop', *BUS_STOP)
# the cable car and the tram (src/AmbientTrams.js, shuttles: one car each, always in the
# street, solid while it stands and ridden by bumping it), one on each side of the avenue.
# The cable car stops where it used to stand and at the bus stop; the tram, whose art
# heads west, where it used to stand, and it turns back clear of the traffic light drawn
# over the first rail east of the crossing.
TRAMWAYS = [
    {'row': STREET_Y + 1, 'from': ROAD_X0 + 1, 'to': AVE_X0 - 1, 'sprite': 'sfb-cable-car_0_0', 'shuttle': True,
     'name': 'cable car', 'stops': [11, BUS_STOP[0]], 'speed': 192, 'dwell': 5, 'headway': 8},
    {'row': STREET_Y + 1, 'from': AVE_X1 + 2, 'to': ROAD_X1 - 1, 'sprite': 'sfb-tram_0_0', 'shuttle': True,
     'name': 'tram', 'faces': 'west', 'stops': [48], 'speed': 256, 'dwell': 6, 'headway': 8},
]

# ---- the hill: painted ladies on the wall of street art, the laneway below -------
LADIES = [(6 + i * 3, 'abcdab'[i]) for i in range(6)]
for x, kind in LADIES:
    place('Collidables', x, LADIES_Y, f'sfb-lady-{kind}', rg.block(3, 5, 2))
WALL = ['mural-a', 'coffee', 'mural-b', 'mural-c', 'coffee', 'mural-a']
for i, piece in enumerate(WALL):
    place('Collidables', 6 + i * 3, WALL_Y, f'sfb-{piece}', rg.block(3, 2))
COFFEE = [(6 + i * 3, WALL_Y) for i, piece in enumerate(WALL) if piece == 'coffee']
for x in (13, 22):
    place('Collidables', x, LANE_Y, 'sfb-crates', rg.block(1, 1))
for x in range(4, 28):                                    # the hedge that closes the lane's south side
    b.stamp('shrub-small', x, LANE_Y + 2)
for y in range(LADIES_Y, WALL_Y + 2):                     # ...and the terrace's east end
    b.stamp('shrub-small', 24, y)
b.stamp('lamp-blue', 5, LANE_Y - 1)
b.stamp('lamp-blue', 26, LANE_Y - 1)

# ---- the city: pyramid, spire, a glass tower, the konbini, on the plaza -----------
PYRAMID = (35, 16)                                        # feet on rows 25-27
place('Collidables', *PYRAMID, 'sfb-pyramid', rg.block(4, 12, 9))
SPIRE = (41, 17)
place('Collidables', *SPIRE, 'sfb-spire', rg.block(4, 11, 9))
b.stamp('highrise-glass', 46, 18)
KONBINI = (52, 24)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('sign-7-11', 55, 26)
b.stamp('vending-white', 33, 26); b.stamp('vending-red', 34, 26)
for x in (39, 45, 51, 56):
    b.stamp('lamp-blue', x, 29)
for i, (px, py) in enumerate([(37, 29), (43, 30), (48, 29), (54, 30), (34, 22)]):
    b.paver(px, py, i)
b.stamp('bicycle-blue', 50, 28); b.stamp('scooter-red', 56, 28)

# ---- the leaners: four people standing folded double at the waist, as still as
#      the lamp posts. Street props, not NPCs: one solid cell each, walked round,
#      and a bump says a line (src/utils/Interactions.js). Each stands off the
#      avenue and off every door and the cell in front of it, with open ground
#      beside it: by the tram stop, on the pavement between the two towers, in the
#      laneway under the wall, and beside the 7-Eleven. ----------------------------
LEANERS = [('a', 40, STREET_Y + 3), ('b', 16, LANE_Y), ('c', 45, STREET_Y - 1), ('d', KONBINI[0] - 1, KONBINI[1] + 3)]
for kind, x, y in LEANERS:
    place('Collidables', x, y, f'sfb-lean-{kind}', rg.block(1, 1))

# ---- the brown river, edge to edge, and the red bridge over it --------------------
for x in [x for x in range(W) if not AVE_X0 <= x <= AVE_X1]:
    for y in range(RIVER_Y0, RIVER_Y1 + 1):
        role = 'edge-n' if y == RIVER_Y0 else 'edge-s' if y == RIVER_Y1 else 'center'
        b.put('Water', x, y, f'sfb-river_{role}'); b.solid(x, y)
for y in range(RIVER_Y0, RIVER_Y1 + 1):
    b.put('Non-Collidables', AVE_X0, y, 'sfb-bridge-cable-w_0_0')
    b.put('Non-Collidables', AVE_X1, y, 'sfb-bridge-cable-e_0_0')
    b.put('Non-Collidables', AVE_X0 - 1, y, 'bridge-shade-w_0_0')
    b.put('Non-Collidables', AVE_X1 + 1, y, 'bridge-shade-e_0_0')
TOWERS = [(AVE_X0 - 1, RIVER_Y0 - 7), (AVE_X0 - 1, RIVER_Y1 - 5)]     # feet on each bank: rows 32 and 38
for x, y in TOWERS:
    place('Collidables', x, y, 'sfb-bridge-tower', [(0, 6), (5, 6)])
ROWERS = [(9, 35), (41, 34), (50, 36)]
for x, y in ROWERS:
    place('Collidables', x, y, 'sfb-rowers')
for x in (6, 14, 22, 36, 44, 52):
    b.stamp('lamp-blue', x, RIVER_Y0 - 2)
for x in (4, 12, 20, 38, 46, 54):
    b.stamp('lamp-blue', x, RIVER_Y1 + 2)

# ---- the south bank: the station with the clocks, townhouses, the palm garden ----
STATION = (13, 39)
place('Collidables', *STATION, 'sfb-clocks-station', rg.block(12, 7, 2))
b.stamp('house-red', 3, 40); b.stamp('house-black', 7, 40)
for x, y in ((34, 41), (41, 40), (48, 41), (54, 40)):
    place('Collidables', x, y, 'sfb-palm', [(1, 3)])
b.stamp('tree-green', 38, 42); b.stamp('tree-green', 45, 42); b.stamp('tree-green', 51, 42)
b.flowers(36, 42); b.flowers(43, 44); b.flowers(52, 44)
for x in (3, 11, 26, 33, 40, 47, 55):
    b.stamp('lamp-blue', x, BOARDWALK_Y0)
b.stamp('vending-white', 9, 46); b.stamp('vending-red', 10, 46)
b.stamp('bicycle-orange', 24, 47); b.stamp('scooter-grey', 37, 47)

# ---- borders: hedges along the north, west and east, open where the river runs ---
for x in list(range(0, 34, 2)) + list(range(50, W, 2)):
    b.stamp('shrub-large', x, 0)
for y in list(range(2, RIVER_Y0 - 1, 2)) + list(range(RIVER_Y1 + 1, SHORE_Y - 1, 2)):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', W - 2, y)

prev = cfg['rooms'].get(KEY, {})
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.finish()
entry = cfg.get('airports', {}).get(AIRPORT, {}).get('entry', [17, 18])
cfg['rooms'][KEY] = b.room(NAME, npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    rg.transporter(x, y, AIRPORT, entry[0], entry[1], hidden=True) for (x, y) in airport_doors
] + ([konbini_entry] if konbini_entry else [])))
cfg['rooms'][KEY]['blog'] = False        # the blog pipeline never offers this room (it is not on a trip)
# not in Japan: a plane out in the sea south-east of Honshu, on a dashed course off the Map's
# bottom-right corner (src/utils/Places.js `overseas`). `geo` is where that marker goes on the picture,
# not a real longitude / latitude: the one stretch of sea where its long label clears every other
# label in every view (tools/tests/japan-map.test.js). No label: the room's name.
cfg.setdefault('places', {})[KEY] = {'geo': [141.5, 32.7], 'overseas': True}
cfg['rooms'][KEY]['tramways'] = TRAMWAYS

rg.save_config(cfg)
print(f'{NAME} {W}x{H}; airport doors at {airport_doors} -> {AIRPORT}; clocks station at {STATION}, '
      f'bridge towers at {TOWERS}, pyramid at {PYRAMID}, spire at {SPIRE}, konbini at {KONBINI}, pier at {PIER}, '
      f'leaners at {[(x, y) for _, x, y in LEANERS]}')
