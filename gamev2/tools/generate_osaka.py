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
          the Dotonbori entrance ARCH over the street (walk under it); to the
          west an office block, a townhouse and the DISCOUNT STORE (the "Don
          Quijote", issue #18 - its door leads into DonTakoteOsaka, issue #91);
          the oval FERRIS WHEEL to the east
  middle  the Dotonbori CANAL (issue #61): three rows of water from one edge
          of the map to the other, under the street's bridge. It is declared
          as the room's one `waterways` entry, which is what gives it ambient
          boats (src/AmbientBoats.js): they sail in from off the map, pass
          UNDER the bridge deck (the `under` columns) and out the other side.
          The deck has a stone parapet each side and throws a shadow on the
          water (issue #180).
          South of it, CANAL-SIDE AVENUE runs east-west across the whole town.

The ROADS (issues #106, #151): the main street is four cells of roadway
(columns 23-26) between brick pavements - a kerb, two lanes with the centre
line on the boundary between them (tools/make_road_tiles.py), a kerb. It ends
square just below the station forecourt, runs under the arch, over a signalled
zebra crossing and the bridge, and meets the avenue at a T-junction in front
of the tower's garden. The avenue is the standard three-cell road (kerb, centre
line, kerb) and leaves town through the hedge at both ends. Roads are ordinary
walkable floor - there is no traffic.

  south   Shinsekai: TSUTENKAKU TOWER on the street's axis, standing on its
          own plaza, townhouses, an apartment block and a glass tower either
          side. A garden thicket fills the ground
          behind the tower, so the street forks round it (nobody walks hidden
          behind a 13-cell sprite). The city buildings follow the same rule
          through their prefabs: solid from the ground up, only the top two
          rows (the roof line) are walk-behind

The three landmarks are prefabs (tools/make_prefabs.py) whose art comes from
tools/extract_dotonbori.py (real GuttyKreum Dotonbori art) and
tools/generate_tsutenkaku.py (line-art placeholder). Deterministic and
idempotent: rebuilds rooms.Osaka from scratch each run, keeping any NPCs the
blog pipeline has placed there.

Run from gamev2/:
    python3 tools/extract_dotonbori.py
    python3 tools/extract_city.py                 # high-rises + discount store
    python3 tools/generate_tsutenkaku.py
    python3 tools/extract_street.py               # traffic light, crossing, kerb props
    python3 tools/make_road_tiles.py              # lane + corner road pieces (Pillow)
    python3 tools/make_bridge_tiles.py            # the bridge's parapet + shadow (Pillow)
    python3 tools/generate_discount_art.py        # the discount store's interior signage
    python3 tools/make_prefabs.py
    python3 tools/generate_osaka.py
    python3 tools/generate_discount_stores.py Osaka   # DonTakoteOsaka (the door is wired here)
    python3 tools/generate_stations.py            # builds OsakaStation + registry
    python3 tools/config_to_tiled.py Osaka OsakaStation DonTakoteOsaka
    node tools/play.js lint Osaka OsakaStation DonTakoteOsaka
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect
import generate_discount_stores as don

cfg = rg.load_config()

W, H = 50, 46
# Rows, north to south: rail 3-5, station 6-8, the north bank's paving 9-18,
# grass bank 19, CANAL 20-22, grass bank 23, the AVENUE (pavement 24, road 25-27,
# pavement 28), Shinsekai from 29. S is how far Shinsekai sits below where it was
# drawn before the avenue went in (issue #151): its rows below are written as
# their old numbers + S.
CANAL_Y0, CANAL_Y1 = 20, 22
AVENUE_Y = 25                    # top kerb row of the three-cell avenue
S = 6
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
b.autotile('brown-brick-autotile', rect(2, 23 + S, 47, 37 + S))
# the street's pavement is one cell either side of the road; on the bridge
# (rows 19-23, bank to bank) it is two, so there is a way round the signal posts
# that stand on the kerb at the bridgehead without stepping into the road (issue
# #139). The avenue's pavements are one cell too, and run out to the map's edge
# with it. One region, so the paving has no seam where the streets meet.
DECK_X0, DECK_X1 = 21, 28
b.autotile('flat-grey-brick-autotile',
           rect(22, 10, 27, AVENUE_Y - 1) + rect(DECK_X0, 19, DECK_X1, AVENUE_Y - 1)
           + rect(0, AVENUE_Y - 1, W - 1, AVENUE_Y + 3))
b.autotile('light-concrete-autotile', rect(18, 32 + S, 31, 37 + S))  # the tower's plaza

# ---- the roads (issues #106, #151). The main street's middle four columns are
#      asphalt, the dark brick either side is its pavement. It ends square a row
#      below the station door (you step out onto paving, not into the road) and
#      runs south to the avenue. Four wide, not the usual three (edge / centre
#      line / edge): the arch's opening is four cells and the arch is the
#      landmark, so the road keeps its axis and gets its centre line from the
#      two lane tiles, which carry half the line each on their shared edge.
ROAD_X0, ROAD_X1 = 23, 26
ROAD_Y0 = 11
b.put('Floor', ROAD_X0, ROAD_Y0, 'road-corner-nw_0_0')
for x in range(ROAD_X0 + 1, ROAD_X1):
    b.put('Floor', x, ROAD_Y0, 'road-edge-top_0_0')
b.put('Floor', ROAD_X1, ROAD_Y0, 'road-corner-ne_0_0')
for y in range(ROAD_Y0 + 1, AVENUE_Y):
    b.put('Floor', ROAD_X0, y, 'road-edge-left_0_0')
    b.put('Floor', ROAD_X0 + 1, y, 'road-lane-left_0_0')
    b.put('Floor', ROAD_X1 - 1, y, 'road-lane-right_0_0')
    b.put('Floor', ROAD_X1, y, 'road-edge-right_0_0')
# Canal-side Avenue: the standard three-cell road from one edge of the map to
# the other, with the street's mouth a plain junction box (as in Sapporo)
for x in range(W):
    junction = ROAD_X0 <= x <= ROAD_X1
    b.put('Floor', x, AVENUE_Y, 'road-plain_0_0' if junction else 'road-edge-top_0_0')
    b.put('Floor', x, AVENUE_Y + 1, 'road-plain_0_0' if junction else 'road-div-horizontal_0_0')
    b.put('Floor', x, AVENUE_Y + 2, 'road-edge-bottom_0_0')

# the zebra crossing, between the arch and the bridge, on the row the canal-bank
# lamps stand on: it joins the west bank's shops to the ferris wheel. The
# crossing-v prefab is three cells (one per cell of a standard road); this road
# has one more lane, so the same three tiles are laid here with the middle one
# repeated. Both signals stand on the pavement just south of it, at the
# bridgehead: north of it their heads would be lost in the arch's side boards.
CROSSING_Y = 18
b.put('Over Floor', ROAD_X0, CROSSING_Y, 'crossing-v-left_0_0')
for x in range(ROAD_X0 + 1, ROAD_X1):
    b.put('Floor', x, CROSSING_Y, 'road-plain_0_0')       # the centre line stops for the stripes
    b.put('Over Floor', x, CROSSING_Y, 'crossing-v-mid_0_0')
b.put('Over Floor', ROAD_X1, CROSSING_Y, 'crossing-v-right_0_0')
b.stamp('traffic-light', ROAD_X0 - 1, CROSSING_Y - 1)     # 1x3: base on row 19
b.stamp('traffic-light', ROAD_X1 + 1, CROSSING_Y - 1)

# ---- Dotonbori: the entrance arch astride the main street ---------------------
ARCH = (21, 12)
b.stamp('dotonbori-arch', *ARCH)
b.stamp('lantern-red', 20, 10); b.stamp('lantern-red', 29, 10)

# ---- west of the street: an office block, a townhouse and the discount store
#      (ドン・タコーテ — Dotonbori's Don Quijote, by the arch and across from its
#      ferris wheel). City buildings come from tools/extract_city.py; all feet
#      on row 16-17 so the row reads as one street front. Doors sealed — no
#      interiors — except the discount store's, which opens into DonTakoteOsaka
#      (tools/generate_discount_stores.py builds the shop floor; issue #91). -----
b.stamp('highrise-blue', 3, 7); b.stamp('house-black', 9, 11)
store_door = b.stamp('discount-store', 13, 9, seal=False)[0]
b.stamp('lantern-red', 8, 16); b.stamp('lantern-red', 12, 16)
b.stamp('vending-white', 18, 13); b.stamp('vending-red', 19, 13)
for x in (11, 16):                                # (none at 6: the office block's feet are on
    b.stamp('lamp-blue', x, 18)                   #  row 17, a lamp there stood beside its door)

# ---- east of the street: the oval ferris wheel on the canal bank --------------
WHEEL = (33, 7)
b.stamp('dotonbori-wheel', *WHEEL)
b.stamp('lamp-blue', 31, 18); b.stamp('lamp-blue', 46, 18)
b.stamp('shrub-small', 46, 10); b.stamp('shrub-small', 46, 13)
b.stamp('sakura-small', 30, 13); b.stamp('sakura-small', 2, 16)

# ---- the Dotonbori canal (issue #61): open water three rows wide, from one
#      edge of the map to the other - rock rim along both banks, no end caps -
#      interrupted only by the bridge deck (eight cells: the road and two cells
#      of pavement each side, #139). The water tiles stop at the deck's edge;
#      the `waterways` entry at the bottom of this file tells AmbientBoats the
#      channel carries on under it.
for x in [x for x in range(W) if not DECK_X0 <= x <= DECK_X1]:
    for y in range(CANAL_Y0, CANAL_Y1 + 1):
        role = 'edge-n' if y == CANAL_Y0 else 'edge-s' if y == CANAL_Y1 else 'center'
        b.put('Water', x, y, f'pond-autotile_{role}'); b.solid(x, y)
# the deck reads as a bridge (issue #180; tools/make_bridge_tiles.py): a stone
# parapet down each side of it over the water - a strip on the outer edge of
# the pavement cell, not solid, so the two-cell pavement (#139) keeps its width -
# and the deck's shadow on the water against it. A boat sails into the shadow
# before it goes under.
for y in range(CANAL_Y0, CANAL_Y1 + 1):
    b.put('Non-Collidables', DECK_X0, y, 'bridge-parapet-w_0_0')
    b.put('Non-Collidables', DECK_X1, y, 'bridge-parapet-e_0_0')
    b.put('Non-Collidables', DECK_X0 - 1, y, 'bridge-shade-w_0_0')
    b.put('Non-Collidables', DECK_X1 + 1, y, 'bridge-shade-e_0_0')
# south bridgehead: the lanterns stand on the bank, their heads against the water
b.stamp('lantern-red', DECK_X0 - 1, CANAL_Y1); b.stamp('lantern-red', DECK_X1 + 1, CANAL_Y1)

# ---- Shinsekai: Tsutenkaku on the axis of the street, on its plaza ------------
TOWER = (21, 23 + S)
b.stamp('tsutenkaku', *TOWER)
# The tower garden: the tower is 13 cells tall and stands on the street's axis,
# so without this the main street would run BEHIND it and hide the player for
# ten cells. A thicket fills the ground behind the shaft and deck; the street
# forks at the avenue and passes either side of it down to the plaza.
for gy in range(24 + S, 32 + S, 2):
    for gx in range(22, 28, 2):
        for cx, cy in rect(gx, gy, gx + 1, gy + 1):
            b.put('Floor', cx, cy, 'grass-autotile_center')
        b.stamp('shrub-large', gx, gy)
b.stamp('lantern-red', 19, 35 + S); b.stamp('lantern-red', 30, 35 + S)
for i, (px, py) in enumerate([(19, 33), (30, 33), (22, 37), (27, 37), (20, 37), (29, 37)]):
    b.paver(px, py + S, i)
b.stamp('highrise-apartment', 3, 24 + S); b.stamp('house-black', 10, 26 + S)       # feet on row 31 + S
# (the glass tower stands a row lower than its neighbours: its two walk-behind
#  roof rows would otherwise lie on the avenue's pavement)
b.stamp('house-blue', 37, 26 + S); b.stamp('highrise-glass', 42, 23 + S)
b.stamp('vending-red', 14, 29 + S); b.stamp('vending-white', 35, 29 + S)
b.stamp('lantern-red', 9, 31 + S); b.stamp('lantern-red', 41, 31 + S)
b.stamp('sakura-large', 16, 26 + S); b.stamp('sakura-large', 31, 26 + S)   # flanking the tower
b.stamp('sakura-large', 3, 33 + S); b.stamp('sakura-large', 44, 33 + S)
b.stamp('sakura-small', 15, 34 + S); b.stamp('sakura-small', 34, 34 + S)
b.stamp('shrub-small', 17, 30 + S); b.stamp('shrub-small', 32, 30 + S)
b.stamp('shrub-small', 46, 25 + S)
for x in (8, 13, 36, 41):
    b.stamp('lamp-blue', x, 36 + S)

# ---- street accessories (issue #19; tools/extract_street.py): bikes and a
#      scooter outside the discount store (clear of its door at column 15), the
#      bus stop on the kerb where the road begins (#106), a utility pole on the
#      north bank, a scooter by the flats. The zebra crossing and its signals
#      are with the road, above. -----------------------------------------------
b.stamp('bicycle-blue', 13, 17); b.stamp('bicycle-orange', 14, 17); b.stamp('scooter-grey', 18, 17)
b.stamp('bus-stop', 21, 11); b.stamp('utility-pole', 19, 16); b.stamp('scooter-red', 8, 32 + S)

# ---- borders: hedges west / east, a fence along the south ---------------------
#      (continuous — a gap would let the player slip round behind the fences)
#      The hedge is two cells deep and solid on every row except the canal's
#      (water, solid anyway) and the avenue's five (pavement, road, pavement),
#      where the street leaves town: you can walk it to the edge of the map.
for y in list(range(8, CANAL_Y0, 2)) + list(range(AVENUE_Y + 5, H - 2, 2)):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', W - 2, y)
for y in (CANAL_Y1 + 1, AVENUE_Y + 4):                # the bank row, and the odd row below the avenue
    for x in (0, 1, W - 2, W - 1):
        b.stamp('shrub-small', x, y)
b.stamp('shrub-small', 0, H - 2); b.stamp('shrub-small', W - 1, H - 2)
for y in (6, 7):
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, H - 2, i)

# ---- greenery on the canal banks ----------------------------------------------
for i in range(60):
    sx, sy = rng.randrange(2, W - 2), rng.choice((CANAL_Y0 - 1, CANAL_Y1 + 1))
    if all(f'{sx},{sy}' not in b.L[n] for n in
           ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water', 'Tops')) \
       and rg._pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      platform, so a platform-edge fence closes the gravel row behind it -------
for x in range(10, 27):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into OsakaStation (the
# discount store's door leads to its own interior and back).
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) — keep them.
prev = cfg['rooms'].get('Osaka', {})
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
cfg['rooms']['Osaka'] = b.room('Osaka', npcs=prev.get('npcs', []), transporters=[
    rg.transporter(station_door[0], station_door[1], 'OsakaStation', 11, 11, hidden=True),
    don.door_transporter('Osaka', store_door),
])
# the canal is navigable (src/AmbientBoats.js): cells, inclusive. `under` is the
# bridge deck - a boat is not drawn there, so it passes beneath the street.
cfg['rooms']['Osaka']['waterways'] = [
    {'axis': 'h', 'row': CANAL_Y0, 'rows': CANAL_Y1 - CANAL_Y0 + 1, 'from': 0, 'to': W - 1,
     'under': [[DECK_X0, DECK_X1]]},
]

rg.save_config(cfg)
print(f'Osaka {W}x{H}; station house door at {station_door} -> OsakaStation; '
      f'arch at {ARCH}, ferris wheel at {WHEEL}, Tsutenkaku at {TOWER}')
