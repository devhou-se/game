#!/usr/bin/env python3
"""generate_fukuoka.py — "Fukuoka", the last city of devhouse 2 (issue #67):
Hakata, Nakasu, Momochi, and Dazaifu on its southern edge.

A generated room (roomgen + prefabs, the generate_osaka.py / generate_sapporo.py
recipe). Reachable ONLY by train: the station house door on the north side
leads into the FukuokaStation interior ("Hakata", built by generate_stations.py).
The town is what the group's posts describe (8-12 Nov 2025), north to south:

  north   the rail line, the platform and the station house (Hakata Station).
          West of it a row of high-rises and, on Momochi's shore, FUKUOKA
          TOWER; east of it the station plaza and the 7-Eleven.
          The west edge of the whole map is the sea, with a strip of beach.
  street  the downtown street (asphalt, a signalled zebra crossing where the
          avenue crosses it); it leaves town through the hedge at the east end
  middle  CANAL CITY and its fountain (west); KUSHIDA SHRINE under the red
          roof with a Yamakasa float beside it, the old Hakata townhouses and
          Tochoji's pagoda (east)
  river   THE RAMEN RIVER STREET: a row of yatai food stalls - noren, stools,
          strings of paper lanterns between them - backs onto a hedge and
          faces the promenade along the Naka river. The river (three rows of
          water, from the sea to the east edge of the map) is the room's one
          `waterways` entry, which gives it ambient boats (src/AmbientBoats.js):
          they pass UNDER the avenue's bridge deck (the `under` columns).
  south   over the bridge: Ohori Park's pond (west) and DAZAIFU TENMANGU
          (east) - approached from the south as a shrine is: the lane, the
          torii, the arched bridge over the pond between the plum trees, and
          the hall with the grove on its roof.

The avenue (a paved pedestrian street, columns 29-32) is the spine: station
door -> crossing -> between Canal City and Kushida -> the yatai -> the bridge
-> the south lane. Nobody gets lost behind a building: the high-rises stand
shoulder to shoulder with a hedge behind them, the stalls back onto a hedge,
and the landmarks collide along their silhouettes (tools/make_prefabs.py).

Landmark art is drawn by tools/generate_fukuoka_art.py. Deterministic and
idempotent: rebuilds rooms.Fukuoka from scratch each run, keeping any NPCs the
blog pipeline has placed there and the konbini door generate_konbinis.py wired
(on a first build there is none to keep: the door is sealed until that runs).
Fences and tracks are finished here (b.finish()), so a re-run on an unchanged
world changes nothing - tools/check_generators.py (issue #107).

Run from gamev2/:
    python3 tools/generate_fukuoka_art.py         # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_fukuoka.py
    python3 tools/generate_konbinis.py Fukuoka    # KonbiniFukuoka1 + its door
    python3 tools/generate_stations.py            # builds FukuokaStation + registry
    python3 tools/config_to_tiled.py Fukuoka FukuokaStation KonbiniFukuoka1
    node tools/play.js lint Fukuoka FukuokaStation KonbiniFukuoka1
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 62, 62
b = rg.Builder(W, H)
rng = random.Random(67)

SEA_X1, SHORE_X, BEACH_X1 = 4, 5, 8      # sea columns 0-4, the waterline, sand 6-8
TOWN_X0 = BEACH_X1 + 1                   # first column of the town proper
AVE_X0, AVE_X1 = 29, 32                  # the avenue (and the bridge deck)
STREET_Y = 20                            # top kerb row of the downtown street
LANE_Y = 32                              # the lane in front of Kushida and the townhouses
YATAI_Y = 34                             # the stalls' roof row (cart 35, stools 36)
PROM_Y0, PROM_Y1 = 37, 38                # the riverside promenade
RIVER_Y0, RIVER_Y1 = 40, 42
SOUTH_LANE_Y = 57                        # the lane along the south (rows 57-58)

b.fill('grass-autotile')

# ---- Momochi beach and the sea down the west edge. The sand is laid first as
#      one region (so it has no fringe against the water), then the sea goes on
#      top: open water, and the waterline tiles on the sand's side of it --------
b.autotile('sand-autotile', rect(0, 6, BEACH_X1, H - 1))
for x in range(SEA_X1 + 1):
    b.put('Water', x, 7, 'beach-shore-n_0_0'); b.solid(x, 7)
b.put('Water', SHORE_X, 7, 'beach-shore-ne_0_0'); b.solid(SHORE_X, 7)
for y in range(8, H):
    for x in range(SEA_X1 + 1):
        b.put('Water', x, y, 'pond-autotile_center'); b.solid(x, y)
    if RIVER_Y0 <= y <= RIVER_Y1:                     # the river mouth: open water
        b.put('Water', SHORE_X, y, 'pond-autotile_center')
    else:
        b.put('Water', SHORE_X, y, 'beach-shore-e_0_0')
    b.solid(SHORE_X, y)

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-autotile', rect(0, 3, W - 1, 5))
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 29)) + list(range(44, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the station
for y in (3, 4, 5):                                   # caps at the corridor ends
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
for x in range(3, W - 3, 6):                          # greenery beyond the tracks
    b.stamp('shrub-large', x, 0)

# ---- Hakata Station: the station house on the avenue's axis, the platform
#      east of it, the forecourt below both ---------------------------------------
station_door = b.stamp('house-blue', 29, 4, seal=False)[0]   # door -> FukuokaStation
b.autotile('light-concrete-autotile', rect(32, 6, 43, 8) + rect(28, 9, 44, 10))
b.stamp('lamp-blue', 33, 7); b.stamp('lamp-blue', 42, 7)
b.stamp('vending-white', 36, 6); b.stamp('vending-red', 38, 6)
for i, px in enumerate((34, 37, 40)):
    b.paver(px, 8, i)

# ---- paving ---------------------------------------------------------------------
b.autotile('grey-brick-autotile', rect(33, 11, 59, 18))                  # the station plaza
# the street's pavements run out to the east edge with it; at the west end they
# open into the plaza at the foot of the tower
b.autotile('light-concrete-autotile',
           rect(TOWN_X0, STREET_Y - 1, W - 1, STREET_Y - 1) + rect(TOWN_X0, STREET_Y + 3, W - 1, STREET_Y + 3)
           + rect(TOWN_X0, 17, 15, STREET_Y + 3))
b.autotile('brown-brick-autotile', rect(TOWN_X0, 24, 28, LANE_Y))        # Canal City's plaza
b.autotile('gravel-autotile', rect(34, 26, 45, LANE_Y - 1))              # Kushida's court
b.autotile('brown-brick-autotile', rect(33, LANE_Y, 59, LANE_Y))         # the lane past the townhouses
b.autotile('grey-brick-autotile', rect(TOWN_X0, YATAI_Y, 59, PROM_Y1))   # under the stalls + the promenade
b.autotile('gravel-autotile', rect(38, 49, 55, 56))                      # Dazaifu's court
b.autotile('dirt-outside-autotile', rect(10, 52, 28, 53))                # the path round Ohori's pond
# the avenue: one region from the forecourt to the south lane, bridge deck included
b.autotile('flat-grey-brick-autotile',
           rect(AVE_X0, 11, AVE_X1, SOUTH_LANE_Y + 1) + rect(TOWN_X0, SOUTH_LANE_Y, 59, SOUTH_LANE_Y + 1))

# ---- the downtown street: the standard three-cell road. It ends square at the
#      tower's plaza and leaves town at the east edge; the avenue crosses it on
#      a signalled zebra crossing (TrafficLights.js runs the lamps) --------------
ROAD_X0 = 16
b.put('Floor', ROAD_X0, STREET_Y, 'road-corner-nw_0_0')
b.put('Floor', ROAD_X0, STREET_Y + 1, 'road-edge-left_0_0')
b.put('Floor', ROAD_X0, STREET_Y + 2, 'road-corner-sw_0_0')
for x in range(ROAD_X0 + 1, W):
    crossing = AVE_X0 <= x <= AVE_X1
    b.put('Floor', x, STREET_Y, 'road-edge-top_0_0')
    b.put('Floor', x, STREET_Y + 1, 'road-plain_0_0' if crossing else 'road-div-horizontal_0_0')
    b.put('Floor', x, STREET_Y + 2, 'road-edge-bottom_0_0')
for x in range(AVE_X0, AVE_X1 + 1):
    b.stamp('crossing-h', x, STREET_Y)
b.stamp('traffic-light', AVE_X0 - 1, STREET_Y - 3)        # 1x3: base on the north pavement
b.stamp('traffic-light', AVE_X1 + 1, STREET_Y + 1)        # base on the south pavement

# ---- Momochi: Fukuoka Tower at the head of its plaza, by the beach --------------
TOWER = (10, 7)
b.stamp('fukuoka-tower', *TOWER)
for y in range(7, 17, 2):                                 # a hedge between the tower's lawn and the towers
    b.stamp('shrub-large', 14, y)
b.stamp('lamp-blue', 9, 18); b.stamp('lamp-blue', 15, 18)
for i, (px, py) in enumerate([(9, 21), (12, 22), (14, 20), (11, 20)]):
    b.paver(px, py, i)

# ---- the business district, shoulder to shoulder, feet on row 18. Doors
#      sealed - no interiors. The ground behind them is planted, not walked ------
b.stamp('highrise-glass', 16, 9)
b.stamp('highrise-blue', 20, 8)
b.stamp('highrise-yellow', 25, 11)
for x in range(16, 29):
    b.stamp('shrub-small', x, 7)
for x in list(range(16, 20)) + list(range(25, 29)):
    b.stamp('shrub-small', x, 8)
b.stamp('shrub-large', 25, 9); b.stamp('shrub-large', 27, 9)

# ---- the station plaza, east of the avenue: flats, a townhouse, the konbini ----
b.stamp('midrise-apartment', 36, 13)
b.stamp('house-black', 43, 13)
KONBINI = (49, 15)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('sign-7-11', 52, 17)
b.stamp('house-red', 55, 13)
b.stamp('vending-white', 34, 17); b.stamp('vending-red', 35, 17)
b.stamp('tree-green', 46, 10); b.stamp('tree-green', 52, 11)
b.stamp('tree-green', 49, 7); b.stamp('tree-green', 56, 8)
b.stamp('shrub-small', 58, 12); b.stamp('shrub-small', 41, 16)
b.stamp('bicycle-blue', 47, 18); b.stamp('scooter-grey', 53, 18)
for x in (18, 23, 38, 42, 47, 54, 58):                    # lamps along the pavements
    b.stamp('lamp-blue', x, STREET_Y - 1)
for x in (18, 24, 38, 44, 50, 56):
    b.stamp('lamp-blue', x, STREET_Y + 3)
b.stamp('bus-stop', 27, STREET_Y - 1)

# ---- Canal City: the mall on its brick plaza, the fountain east of it ----------
CANAL_CITY = (12, 24)
b.stamp('canal-city', *CANAL_CITY)
FOUNTAIN = (23, 27)
b.stamp('canal-fountain', *FOUNTAIN)
b.stamp('tree-green', 9, 25); b.stamp('tree-green', 26, 24)
for x in (11, 20, 27):
    b.stamp('lamp-blue', x, 30)
b.stamp('bicycle-orange', 11, 29); b.stamp('scooter-red', 10, 31)
for i, (px, py) in enumerate([(22, 30), (25, 30), (21, 26), (26, 28), (13, 31), (18, 31)]):
    b.paver(px, py, i)

# ---- Kushida shrine: the hall under the red roof on a gravel court, the
#      Yamakasa float standing beside it, lanterns at the steps -------------------
KUSHIDA = (36, 24)
b.stamp('shrine-red', *KUSHIDA)
YAMAKASA = (42, 27)
b.stamp('hakata-yamakasa', *YAMAKASA)
b.stamp('lantern-red', 35, 30); b.stamp('lantern-red', 41, 30)
b.stamp('tree-green', 33, 24); b.stamp('tree-green', 43, 23)
b.stamp('shrub-small', 45, 27)

# ---- old Hakata: the townhouses (the Machiya Folk Museum) and Tochoji's
#      pagoda, on the lane; a hedge closes the ground behind them ----------------
b.stamp('machiya-black', 46, 27); b.stamp('machiya-red', 51, 27)
b.stamp('pagoda-small', 57, 26)
for x in range(46, 60, 2):
    b.stamp('shrub-large', x, 24)
b.stamp('shrub-small', 56, 26); b.stamp('shrub-small', 59, 26)
b.stamp('lantern-red', 56, 30)

# ---- THE RAMEN RIVER STREET: yatai along the promenade, facing the river. A
#      hedge runs behind the row; between the stalls stand posts strung with
#      paper lanterns (they glow at night - DayNight lights every `-lanterns`
#      tile) ----------------------------------------------------------------------
STALLS = [10, 14, 18, 22, 26, 34, 38, 42, 46, 50]
KINDS = ('ramen', 'yakitori', 'oden')
for i, x in enumerate(STALLS):
    b.stamp(f'yatai-{KINDS[i % 3]}', x, YATAI_Y)
POSTS = [13, 17, 21, 25, 37, 41, 45, 49, 53]
for x in POSTS:
    b.stamp('yatai-lanterns', x, YATAI_Y + 1)
stall_cols = {x + dx for x in STALLS for dx in range(3)}
for x in list(range(TOWN_X0, AVE_X0)) + list(range(AVE_X1 + 1, 60)):
    b.stamp('shrub-small', x, YATAI_Y - 1)                # the hedge behind the row
    if x not in stall_cols:
        b.stamp('shrub-small', x, YATAI_Y)                # ...and behind the gaps in it
b.stamp('vending-white', 55, YATAI_Y + 1); b.stamp('vending-red', 56, YATAI_Y + 1)
b.stamp('tree-green', 58, YATAI_Y)
# the bank: lamps and reeds between the promenade and the water
for x in (11, 17, 23, 36, 42, 48, 54):
    b.stamp('lamp-blue', x, RIVER_Y0 - 1)

# ---- the Naka river: three rows of open water from the beach to the east edge
#      of the map, rock rim along both banks, interrupted only by the bridge
#      deck. The `waterways` entry at the bottom tells AmbientBoats the channel
#      carries on under it. ------------------------------------------------------
RIVER_X0 = SHORE_X + 1
for x in [x for x in range(RIVER_X0, W) if not AVE_X0 <= x <= AVE_X1]:
    for y in range(RIVER_Y0, RIVER_Y1 + 1):
        role = 'edge-n' if y == RIVER_Y0 else 'edge-s' if y == RIVER_Y1 else 'center'
        b.put('Water', x, y, f'pond-autotile_{role}'); b.solid(x, y)
# the deck reads as a bridge (tools/make_bridge_tiles.py, Osaka's recipe): a
# stone parapet on the outer edge of its outer cells - not solid - and the
# deck's shadow on the water beside it
for y in range(RIVER_Y0, RIVER_Y1 + 1):
    b.put('Non-Collidables', AVE_X0, y, 'bridge-parapet-w_0_0')
    b.put('Non-Collidables', AVE_X1, y, 'bridge-parapet-e_0_0')
    b.put('Non-Collidables', AVE_X0 - 1, y, 'bridge-shade-w_0_0')
    b.put('Non-Collidables', AVE_X1 + 1, y, 'bridge-shade-e_0_0')
b.stamp('lantern-red', AVE_X0 - 1, RIVER_Y1); b.stamp('lantern-red', AVE_X1 + 1, RIVER_Y1)

# ---- Ohori Park, south-west: the pond, trees round it, a path along its shore --
b.pond(12, 49, 24)
for x, y in ((10, 44), (15, 45), (20, 44), (25, 45)):
    b.stamp('tree-green', x, y)
b.stamp('lantern-red', 11, 50); b.stamp('lantern-red', 25, 50)
b.stamp('sakura-large', 13, 54); b.stamp('sakura-large', 21, 54)
b.stamp('shrub-small', 18, 55); b.stamp('shrub-small', 27, 55); b.stamp('shrub-small', 10, 55)

# ---- Dazaifu Tenmangu, south-east. A shrine is walked up to from the south:
#      the lane, the torii, the arched bridge over the pond, the hall. Plum
#      trees either side - the shrine's tree - and lanterns at the hall. The
#      hall is the temporary one the group saw, a grove growing on its roof. ----
HALL = (44, 44)
b.stamp('dazaifu-hall', *HALL)
b.pond(39, 50, 54)
BRIDGE = (46, 49)
b.stamp('dazaifu-bridge', *BRIDGE)
for cx, cy in rect(BRIDGE[0], 50, BRIDGE[0] + 1, 51):     # the deck is walked on: no water collider under it
    del b.L['Colliders'][f'{cx},{cy}']
TORII = (44, 52)
b.stamp('torii-red', *TORII)
for x, y in ((40, 46), (52, 46), (41, 53), (51, 53), (36, 47), (56, 47)):
    b.stamp('plum-tree', x, y)
b.stamp('lantern-red', 43, 47); b.stamp('lantern-red', 50, 47)
b.stamp('tree-green', 35, 44); b.stamp('tree-green', 57, 43)
b.stamp('shrub-small', 38, 44); b.stamp('shrub-small', 54, 44)
for x in (12, 22, 36, 42, 52, 58):                        # lamps along the south lane
    b.stamp('lamp-blue', x, SOUTH_LANE_Y + 2)

# ---- borders: the sea on the west; a hedge down the east side, two cells deep,
#      open only where the street leaves town (the river is water to the edge);
#      a fence along the south --------------------------------------------------
for y in list(range(7, STREET_Y - 1, 2)) + list(range(STREET_Y + 4, RIVER_Y0, 2)) \
        + list(range(RIVER_Y1 + 1, H - 3, 2)):
    b.stamp('shrub-large', W - 2, y)
for x in (W - 2, W - 1):
    b.stamp('shrub-small', x, H - 3)
b.stamp('shrub-small', W - 1, 6); b.stamp('shrub-small', W - 1, H - 2)
for i, x in enumerate(range(BEACH_X1 - 2, W - 1)):
    b.fence(x, H - 2, i)

# ---- reeds and flowers on the river banks and the lawns -------------------------
for i in range(90):
    sx, sy = rng.randrange(TOWN_X0, W - 2), rng.choice((RIVER_Y0 - 1, RIVER_Y1 + 1, 44, 48, 55))
    if all(f'{sx},{sy}' not in b.L[n] for n in
           ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water', 'Tops', 'Non-Collidables')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      station, so a platform-edge fence closes the gravel row behind it ---------
for x in range(29, 44):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into FukuokaStation (the
# konbini leads to its own interior and back).
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Fukuoka', {})
# the konbini door keeps the transporter generate_konbinis.py wired onto it;
# with none to keep (a first build) it is sealed until that runs
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
cfg['rooms']['Fukuoka'] = b.room('Fukuoka', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    # into the station at its entry cell (generate_stations.py: a large station's is not 11,11)
    rg.transporter(station_door[0], station_door[1], 'FukuokaStation',
                   *cfg.get('stations', {}).get('FukuokaStation', {}).get('entry', [11, 11]), hidden=True),
] + ([konbini_entry] if konbini_entry else [])))
# the river is navigable (src/AmbientBoats.js): cells, inclusive. It is measured
# from its first rimmed column, so its west end - the river mouth - is a closed
# end (a boat fades in there) and its east end, on the map's edge, an open one.
# `under` is the bridge deck: a boat is not drawn there, so it passes beneath.
cfg['rooms']['Fukuoka']['waterways'] = [
    {'axis': 'h', 'row': RIVER_Y0, 'rows': RIVER_Y1 - RIVER_Y0 + 1, 'from': RIVER_X0, 'to': W - 1,
     'under': [[AVE_X0, AVE_X1]]},
]

rg.save_config(cfg)
print(f'Fukuoka {W}x{H}; station house door at {station_door} -> FukuokaStation; '
      f'Fukuoka Tower at {TOWER}, Canal City at {CANAL_CITY}, Kushida at {KUSHIDA}, '
      f'{len(STALLS)} yatai on row {YATAI_Y}, Dazaifu hall at {HALL}, konbini at {KONBINI}')
