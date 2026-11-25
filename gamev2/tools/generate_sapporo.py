#!/usr/bin/env python3
"""generate_sapporo.py — "Sapporo", Hokkaido's city, in winter (issue #43).

A generated room (roomgen + prefabs, the generate_osaka.py recipe). Reachable
ONLY by train: the station house door on the north side leads into the
SapporoStation interior (built by generate_stations.py). Unlike the other
towns it is laid out on a street GRID, the way Sapporo is:

  north   the rail line, the platform and the station house; the station
          plaza; west of the avenue a row of high-rises and the discount store,
          east of it the SAPPORO CLOCK TOWER on its own paving and the konbini
  middle  Kita-Odori street, then ODORI PARK - a boulevard strip of snow trees
          and lanterns with a path down the middle, cut by the three
          north-south streets - and the SAPPORO TV TOWER at its east end
  south   Minami-Odori street, then houses, and a frozen-pond park corner in
          the south-west

Streets: two east-west (rows 20-22 and 31-33) and three north-south (columns
14-16, 30-32 the station avenue, and 44-46), plain asphalt where they cross.
You can walk on them - there is no traffic.

Nobody gets lost behind a building: the high-rises stand shoulder to shoulder
and a hedge closes the ground behind them; the Clock Tower and the TV Tower
collide along their silhouettes (tools/make_prefabs.py), so only a roof tip
or the TV Tower's thin mast is ever between the player and the camera.

Landmark art is drawn by tools/generate_hokkaido.py. Deterministic and
idempotent: rebuilds rooms.Sapporo from scratch each run, keeping any NPCs the
blog pipeline has placed there. The konbini door is wired by
generate_konbinis.py, which must therefore run after this.

Run from gamev2/:
    python3 tools/generate_hokkaido.py            # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_sapporo.py
    python3 tools/generate_konbinis.py Sapporo    # KonbiniSapporo1 + its door
    python3 tools/generate_discount_stores.py Sapporo   # DonTakoteSapporo (door wired here)
    python3 tools/generate_stations.py            # builds SapporoStation + registry
    python3 tools/fix_fences.py Sapporo           # MANDATORY (b.fence)
    python3 tools/seal_tracks.py Sapporo          # MANDATORY (rail line)
    node tools/play.js lint Sapporo            (and SapporoStation, KonbiniSapporo1)
    python3 tools/config_to_tiled.py Sapporo SapporoStation KonbiniSapporo1 DonTakoteSapporo
"""
import roomgen as rg
from roomgen import rect
import generate_discount_stores as don

cfg = rg.load_config()

W, H = 56, 43
b = rg.Builder(W, H)

b.fill('snow-autotile')


# ---- streets ---------------------------------------------------------------------
def hroad(y, x0, x1):
    for x in range(x0, x1 + 1):
        b.put('Floor', x, y, 'road-edge-top_0_0')
        b.put('Floor', x, y + 1, 'road-div-horizontal_0_0')
        b.put('Floor', x, y + 2, 'road-edge-bottom_0_0')


def vroad(x, y0, y1):
    for y in range(y0, y1 + 1):
        b.put('Floor', x, y, 'road-edge-left_0_0')
        b.put('Floor', x + 1, y, 'road-div-vertical_0_0')
        b.put('Floor', x + 2, y, 'road-edge-right_0_0')


def crossing(x, y):
    for cx, cy in rect(x, y, x + 2, y + 2):
        b.put('Floor', cx, cy, 'road-plain_0_0')


KITA, MINAMI = 20, 31                 # the two east-west streets (top rows)
WEST, AVENUE, EAST = 14, 30, 44       # the three north-south streets (left columns)

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-snow-autotile', rect(0, 3, W - 1, 5))   # gravel with a snow bank, not a grass fringe
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 23)) + list(range(37, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):                                   # snowy caps at the corridor ends
    b.stamp('shrub-small-snow', 0, y); b.stamp('shrub-small-snow', W - 1, y)
for x in range(3, W - 3, 6):                          # drifts beyond the tracks
    b.stamp('shrub-large-snow', x, 0)

# ---- station platform, station house, forecourt --------------------------------
b.autotile('light-concrete-autotile', rect(23, 6, 32, 8))
b.stamp('lamp-blue', 24, 7); b.stamp('lamp-blue', 31, 7)
b.stamp('vending-white', 26, 6); b.stamp('vending-red', 28, 6)
for i, px in enumerate((25, 27, 30)):
    b.paver(px, 8, i)
station_door = b.stamp('house-blue', 33, 4, seal=False)[0]   # door -> SapporoStation
b.autotile('light-concrete-autotile', rect(23, 9, 38, 10))

# ---- paving: the station plaza, the Clock Tower's square, the pavements ----------
b.autotile('grey-brick-autotile', rect(23, 11, 29, 18))
b.autotile('grey-brick-autotile', rect(34, 12, 43, 18))
b.autotile('light-concrete-autotile', rect(2, 19, 53, 19))       # north pavement of Kita-Odori
b.autotile('light-concrete-autotile', rect(2, 34, 53, 34))       # south pavement of Minami-Odori
b.autotile('light-concrete-autotile', rect(2, 41, 53, 41))       # the lane the houses front on
b.autotile('flat-grey-brick-autotile', rect(2, 26, 46, 27))      # Odori Park's central path
b.autotile('grey-brick-autotile', rect(47, 23, 53, 30))          # the TV Tower's plaza

hroad(KITA, 2, 53)
hroad(MINAMI, 2, 53)
vroad(AVENUE, 11, 40)                 # the station avenue runs the whole town
vroad(WEST, KITA, 40)
vroad(EAST, KITA, 40)
for sx in (WEST, AVENUE, EAST):
    crossing(sx, KITA); crossing(sx, MINAMI)

# ---- west of the avenue: the business district, shoulder to shoulder, feet on
#      row 18 so the row reads as one street front. Doors sealed - no interiors -
#      except the discount store's, which opens into DonTakoteSapporo (issue #91;
#      tools/generate_discount_stores.py builds the shop floor) -----------------
b.stamp('highrise-blue', 2, 8)
b.stamp('highrise-glass', 7, 9)
b.stamp('highrise-apartment', 11, 11)
store_door = b.stamp('discount-store', 16, 11, seal=False)[0]
# a hedge from the platform fence down to the store's shoulder: the ground behind
# the towers (and under their roof lines) is not somewhere to wander
for y in (7, 9, 11):
    b.stamp('shrub-large-snow', 21, y)
for x in (4, 9, 13, 17):                              # ...so it is planted instead
    b.stamp('shrub-small-snow', x, 7)

# the station plaza, between the store and the avenue
b.stamp('tree-snow', 21, 14)
b.stamp('tree-snow', 26, 13)
b.stamp('vending-white', 24, 11); b.stamp('vending-red', 25, 11)
b.stamp('lantern-red', 23, 17); b.stamp('lantern-red', 29, 17)

# ---- east of the avenue: the Clock Tower, the konbini, a house -----------------
CLOCK = (37, 11)
b.stamp('sapporo-clock-tower', *CLOCK)
b.stamp('lantern-red', 36, 17); b.stamp('lantern-red', 42, 17)
b.stamp('shrub-small-snow', 34, 12); b.stamp('shrub-small-snow', 43, 12)
b.stamp('tree-snow', 34, 13)
KONBINI = (44, 15)
b.stamp('seven-eleven', *KONBINI)                     # door wired by generate_konbinis.py
b.stamp('sign-7-11', 47, 17)
b.stamp('house-red', 49, 9)
b.stamp('tree-snow', 45, 9); b.stamp('tree-snow', 40, 7)
b.stamp('shrub-small-snow', 52, 16); b.stamp('shrub-small-snow', 48, 13)

# lamps along the pavements (clear of the konbini door and the crossings)
for x in (5, 9, 13, 22, 28, 34, 42, 52):                # 52: clear of the TV Tower's mast
    b.stamp('lamp-blue', x, 19)
for x in (5, 11, 20, 27, 36, 41, 50):
    b.stamp('lamp-blue', x, 34)

# ---- Odori Park: rows 23-30. Snow trees along both edges, lanterns between them,
#      the path down the middle; the three streets cut it into blocks ------------
for x0, x1 in ((2, 13), (17, 29), (33, 43)):
    for i, x in enumerate(range(x0 + 1, x1 - 1, 4)):
        b.stamp('tree-snow', x, 23)                   # trunks on row 25
        b.stamp('tree-snow', x, 28)                   # trunks on row 30
        if x + 3 <= x1:
            b.stamp('lantern-red', x + 2, 24)         # base on row 25
            b.stamp('lantern-red', x + 2, 29)         # base on row 30
for i, px in enumerate((4, 9, 19, 24, 28, 35, 40)):
    b.paver(px, 25 if i % 2 else 28, i)

# ---- the TV Tower, closing the east end of the park. Its upper shaft and mast
#      rise over Kita-Odori: the shaft blocks the roadway there (columns 49-50),
#      and you pass on the north pavement, behind the thin mast -----------------
TOWER = (47, 17)
b.stamp('sapporo-tv-tower', *TOWER)
b.stamp('lamp-blue', 47, 30); b.stamp('lamp-blue', 52, 30)
b.stamp('shrub-small-snow', 53, 24); b.stamp('shrub-small-snow', 53, 27)

# ---- south: houses fronting the lane, and the frozen-pond park corner ---------
for x in (18, 22, 26):
    b.stamp(('house-red', 'house-blue', 'house-black')[(x // 4) % 3], x, 35)
b.stamp('house-black', 34, 35); b.stamp('house-red', 38, 35)
b.stamp('vending-white', 42, 38)
b.stamp('house-blue', 48, 35)
b.stamp('tree-snow', 52, 36)
b.stamp('vending-red', 47, 38)

b.pond(4, 37, 11, fam='ice-pond-autotile')
b.stamp('tree-snow', 2, 34); b.stamp('tree-snow', 12, 34)
b.stamp('lantern-red', 7, 35)
b.stamp('shrub-small-snow', 3, 39); b.stamp('shrub-small-snow', 12, 39)
b.stamp('sakura-small', 8, 39)
b.stamp('shrub-small-snow', 5, 36); b.stamp('shrub-small-snow', 10, 36)

# ---- borders: snowy hedges west / east, a fence along the south (continuous -
#      a gap would let the player slip round behind the fences) -----------------
for y in range(7, 41, 2):
    b.stamp('shrub-large-snow', 0, y); b.stamp('shrub-large-snow', W - 2, y)
for x in (0, 1, W - 2, W - 1):
    b.stamp('shrub-small-snow', x, 41)
for x in (0, W - 1):
    b.stamp('shrub-small-snow', x, 6); b.stamp('shrub-small-snow', x, 42)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, 42, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      platform, so a platform-edge fence closes the gravel row behind it -------
for x in range(23, 37):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into SapporoStation (the
# konbini and the discount store lead to their own interiors and back).
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Sapporo', {})
cfg['rooms']['Sapporo'] = b.room('Sapporo', npcs=prev.get('npcs', []), transporters=[
    rg.transporter(station_door[0], station_door[1], 'SapporoStation', 11, 11, hidden=True),
    don.door_transporter('Sapporo', store_door),
])

rg.save_config(cfg)
print(f'Sapporo {W}x{H}; station house door at {station_door} -> SapporoStation; '
      f'Clock Tower at {CLOCK}, TV Tower at {TOWER}, konbini at {KONBINI}')
