#!/usr/bin/env python3
"""generate_sapporo.py — "Sapporo", Hokkaido's city, in winter (issue #43).

A generated room (roomgen + prefabs, the generate_osaka.py recipe). Reachable
ONLY by train: the doors under the station's star clock on the north side lead
into the SapporoStation interior (built by generate_stations.py). Unlike the
other towns it is laid out on a street GRID, the way Sapporo is.

It is being rebuilt district by district (issue #219). Stage 1, the north, is
done - two districts with ground and buildings of their own:

  SAPPORO STATION FRONT   red basket-weave brick (arcade-brick-autotile). The
          station front with the star clock stands across the rail line; its
          plaza runs down to Kita-Odori west of the avenue. West of the plaza,
          on the same brick, the red-brick government hall (Akarenga, sealed:
          a landmark) and the glass KITA office block, then the discount store.
  CLOCK TOWER BLOCK       dark setts (flat-grey-brick-autotile), east of the
          avenue: the SAPPORO CLOCK TOWER where it always stood, the konbini,
          and the red-brick office block in the north-east corner.

  The two office blocks open into lobbies (tools/generate_houses.py --lobbies
  Sapporo; their doors are in roomgen.TOWER_DOORS, and roomgen.save_config
  keeps them through a rebuild). No generic townhouse stands in the north.

Still to come (stages 2-4): Odori Park, Tanukikoji, Susukino. Until then:

  middle  Kita-Odori street, then ODORI PARK - a boulevard strip of snow trees
          and lanterns with a path down the middle, cut by the three
          north-south streets - and the SAPPORO TV TOWER at its east end
  south   Minami-Odori street, then houses, and a frozen-pond park corner in
          the south-west

Streets: two east-west (rows 20-22 and 31-33) and three north-south (columns
14-16, 30-32 the station avenue, and 44-46), plain asphalt where they cross.
You can walk on them - there is no traffic.

Nobody gets lost behind a building: the west row is closed by a shrub in each
gap between its buildings and a hedge behind them; the station front, the
government hall and the office blocks collide up to their roof lines and the
Clock Tower and the TV Tower along their silhouettes (tools/make_prefabs.py),
so only a roof tip, a rooftop board or the TV Tower's thin mast is ever
between the player and the camera.

Landmark art is drawn by tools/generate_hokkaido.py (the two towers) and
tools/generate_sapporo_art.py (everything else of Sapporo's own). Deterministic and
idempotent: rebuilds rooms.Sapporo from scratch each run, keeping any NPCs the
blog pipeline has placed there and the konbini door generate_konbinis.py wired
(on a first build there is none to keep: the door is sealed until that runs).
Fences and tracks are finished here (b.finish()), so a re-run on an unchanged
world changes nothing - tools/check_generators.py (issue #107).

Run from gamev2/:
    python3 tools/generate_hokkaido.py            # sprites (needs Pillow)
    python3 tools/generate_sapporo_art.py         # sprites + their spriteMetadata (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_sapporo.py
    python3 tools/generate_konbinis.py Sapporo    # KonbiniSapporo1 + its door (first build, or the store moved)
    python3 tools/generate_discount_stores.py Sapporo   # DonTakoteSapporo (door wired here)
    python3 tools/generate_stations.py            # builds SapporoStation + registry
    python3 tools/generate_houses.py Sapporo            # HouseSapporo<n> (the houses in the south)
    python3 tools/generate_houses.py --lobbies Sapporo  # LobbySapporo<n> (the two office blocks)
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
for x in list(range(1, 24)) + list(range(34, W - 1)):
    b.fence(x, 6, x)                                  # south fence, up to the station's wings
for y in (3, 4, 5):                                   # snowy caps at the corridor ends
    b.stamp('shrub-small-snow', 0, y); b.stamp('shrub-small-snow', W - 1, y)
for x in range(3, W - 3, 6):                          # drifts beyond the tracks
    b.stamp('shrub-large-snow', x, 0)

# ---- the two northern districts' own ground (issue #219, stage 1) ---------------
STATION_BRICK = 'arcade-brick-autotile'       # Sapporo Station front: red basket-weave brick
CLOCK_SETTS = 'flat-grey-brick-autotile'      # Clock Tower block: dark setts
STATION = (24, 4)                             # the station front, 10x7: its feet on row 10
# Station front: the strip the station stands on and the yard east of it, the
# plaza down to Kita-Odori, and the forecourt of the row west of the plaza
b.autotile(STATION_BRICK, set(rect(23, 7, 38, 10)) | set(rect(23, 11, 29, 18)))
b.autotile(STATION_BRICK, rect(2, 17, 15, 18))
# Clock Tower block: one square from the avenue to the east hedge
b.autotile(CLOCK_SETTS, rect(34, 12, 53, 18))

# ---- the station front, across the rail line: the track runs behind it and the
#      doors under the star clock (a pair) open onto the plaza -> SapporoStation --
station_doors = b.stamp('sapporo-station-front', *STATION, seal=False)

# ---- paving: the pavements, Odori's path, the TV Tower's plaza -------------------
b.autotile('light-concrete-autotile', rect(2, 19, 53, 19))       # north pavement of Kita-Odori
b.autotile('light-concrete-autotile', rect(2, 34, 53, 34))       # south pavement of Minami-Odori
b.autotile('light-concrete-autotile', rect(2, 41, 53, 41))       # the lane the houses front on
# Odori Park's own ground (issue #219, stage 2): a path of packed snow down the
# middle of the boulevard, opening into a court, a plaza and four ways in
ODORI_PATH = 'snow-path-autotile'
b.autotile(ODORI_PATH, set(rect(9, 26, 46, 27))                      # the path, block to block
           | set(rect(3, 27, 10, 29)) | set(rect(9, 23, 10, 25)) | set(rect(6, 30, 7, 30))    # west: the sculpture court
           | set(rect(20, 24, 26, 29)) | set(rect(22, 23, 24, 23)) | set(rect(22, 30, 24, 30))   # middle: the fountain's plaza
           | set(rect(35, 23, 36, 25)) | set(rect(38, 28, 39, 30)))                           # east: the lawn's two ways in
b.autotile('grey-brick-autotile', rect(47, 23, 53, 30))          # the TV Tower's plaza

hroad(KITA, 2, 53)
hroad(MINAMI, 2, 53)
vroad(AVENUE, 11, 40)                 # the station avenue runs the whole town
vroad(WEST, KITA, 40)
vroad(EAST, KITA, 40)
for sx in (WEST, AVENUE, EAST):
    crossing(sx, KITA); crossing(sx, MINAMI)

# ---- west of the plaza, still Station front: the red-brick government hall
#      (a landmark: sealed) and the glass KITA office block (its lobby is opened
#      by generate_houses.py --lobbies), feet on row 16 behind a brick forecourt;
#      then the discount store, which opens into DonTakoteSapporo (issue #91;
#      tools/generate_discount_stores.py builds the shop floor). A shrub closes
#      each gap in the row -----------------------------------------------------
AKARENGA = (2, 11)
b.stamp('sapporo-akarenga', *AKARENGA)
b.stamp('shrub-small-snow', 9, 16)
b.stamp('sapporo-office-glass', 10, 11)
b.stamp('shrub-small-snow', 15, 16)
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

# ---- east of the avenue, the Clock Tower block: the Clock Tower, the konbini and
#      the red-brick office block (a lobby, as the glass one) --------------------
CLOCK = (37, 11)
b.stamp('sapporo-clock-tower', *CLOCK)
b.stamp('lantern-red', 36, 17); b.stamp('lantern-red', 42, 17)
b.stamp('shrub-small-snow', 34, 12); b.stamp('shrub-small-snow', 43, 12)
b.stamp('tree-snow', 34, 13)
KONBINI = (44, 15)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('sign-7-11', 47, 17)
b.stamp('sapporo-office-brick', 49, 9)
b.stamp('tree-snow', 45, 9); b.stamp('tree-snow', 40, 7)
b.stamp('shrub-small-snow', 48, 13)

# lamps along the pavements (clear of the konbini door and the crossings)
for x in (3, 8, 15, 22, 28, 34, 42, 52):                # 52: clear of the TV Tower's mast
    b.stamp('lamp-blue', x, 19)
for x in (5, 11, 20, 27, 36, 41, 50):
    b.stamp('lamp-blue', x, 34)

# ---- Odori Park: rows 23-30, cut into three blocks by the north-south streets
#      (issue #219, stage 2). Ploughed snowbanks close its edges - you come in by
#      the path at a block's ends or by a gap in the bank - and no two blocks are
#      alike. Everything a visitor looks at faces south, onto the path ------------
def bank(row=None, col=None, cells=(), heaps=()):
    """Snowbank: `cells` of row `row` (the east-west piece) or of column `col`
    (the north-south piece), and a shovelled heap on each of `heaps`."""
    for c in cells:
        b.stamp('snowbank-h' if col is None else 'snowbank-v', *((c, row) if col is None else (col, c)))
    for x, y in heaps:
        b.stamp('snowbank-pile', x, y)


# west block, the SCULPTURE COURT: the snow castle (the festival's big sculpture)
# with its court in front, the snow tanuki beside the way in from Kita-Odori
CASTLE, TANUKI = (4, 23), (12, 23)
b.stamp('snow-sculpture-castle', *CASTLE)             # feet on row 26, the court on rows 27-29
b.stamp('snow-sculpture-tanuki', *TANUKI)             # feet on row 25, facing the path
b.stamp('tree-snow', 2, 23)                           # trunk on row 25
b.stamp('tree-snow', 11, 28)                          # trunk on row 30
b.stamp('odori-lamp', 2, 26); b.stamp('odori-lamp', 11, 24)     # either side of the castle (feet on rows 27, 25)
b.stamp('odori-lamp', 3, 28); b.stamp('odori-lamp', 10, 28)     # the court's south corners
b.stamp('odori-bench', 4, 29); b.stamp('odori-bench', 8, 29)    # either side of the way in from Minami-Odori
bank(row=30, cells=(3, 4, 5, 8, 9, 10), heaps=[(2, 30), (13, 30)])
bank(col=13, cells=(28, 29))

# middle block, the FOUNTAIN AND THE STALLS: the frozen fountain in the middle of
# a plaza the path runs round, a festival tent either side of it (grilled corn,
# hot drinks), their counters on the path
FOUNTAIN, CORN, DRINKS = (22, 25), (17, 23), (27, 23)
b.stamp('odori-fountain', *FOUNTAIN)                  # basin on rows 26-27
b.stamp('snowfest-stall-corn', *CORN)                 # counters on row 25: you stand on the path
b.stamp('snowfest-stall-drinks', *DRINKS)
b.stamp('odori-bench', 20, 24); b.stamp('odori-bench', 25, 24)   # under the north bank, facing the fountain
b.stamp('odori-lamp', 20, 28); b.stamp('odori-lamp', 26, 28)     # the plaza's south corners
b.stamp('tree-snow', 18, 28); b.stamp('tree-snow', 27, 28)       # trunks on row 30
bank(row=23, cells=(20, 21, 25, 26))
bank(row=30, cells=(20, 21, 25, 26), heaps=[(17, 30), (29, 30)])
bank(col=17, cells=(28, 29)); bank(col=29, cells=(28, 29))

# east block, the TV TOWER LAWN: open snow towards the tower, the snow bear north
# of the path between two lamps, benches on the lawn, children's heaps of snow
BEAR = (38, 24)
b.stamp('snow-sculpture-bear', *BEAR)                 # feet on row 25
b.stamp('tree-snow', 33, 23); b.stamp('tree-snow', 42, 23)       # trunks on row 25
b.stamp('tree-snow', 33, 28)                          # trunk on row 30
b.stamp('odori-lamp', 37, 24); b.stamp('odori-lamp', 41, 24)     # either side of the bear
b.stamp('odori-lamp', 37, 28); b.stamp('odori-lamp', 40, 28)     # either side of the way in from Minami-Odori
b.stamp('odori-bench', 35, 28); b.stamp('odori-bench', 41, 28)
bank(row=23, cells=(37, 38, 39, 40, 41))
bank(row=30, cells=(35, 36, 37, 40, 41, 42), heaps=[(43, 30), (42, 29), (43, 29)])

# ---- the TV Tower, closing the east end of the park. Its upper shaft and mast
#      rise over Kita-Odori: the shaft blocks the roadway there (columns 49-50),
#      and you pass on the north pavement, behind the thin mast -----------------
TOWER = (47, 17)
b.stamp('sapporo-tv-tower', *TOWER)
b.stamp('lamp-blue', 47, 30); b.stamp('lamp-blue', 52, 30)
b.stamp('shrub-small-snow', 53, 24); b.stamp('shrub-small-snow', 53, 27)

# ---- south: houses fronting the lane, and a park corner (stages 3-4) -----------
for x in (18, 22, 26):
    b.stamp(('house-red', 'house-blue', 'house-black')[(x // 4) % 3], x, 35)
b.stamp('house-black', 34, 35); b.stamp('house-red', 38, 35)
b.stamp('vending-white', 42, 38)
b.stamp('house-blue', 48, 35)
b.stamp('tree-snow', 52, 36)
b.stamp('vending-red', 47, 38)

# the park corner in the south-west: snow, trees and a lantern (the frozen pond
# went with stage 2 - Asahikawa keeps the frozen water - and so did the sakura)
b.stamp('tree-snow', 2, 34); b.stamp('tree-snow', 12, 34)
b.stamp('lantern-red', 7, 35)
b.stamp('shrub-small-snow', 3, 39); b.stamp('shrub-small-snow', 12, 39)
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

# isolated: the ONLY way out is the station's doors into SapporoStation (the
# konbini and the discount store lead to their own interiors and back).
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Sapporo', {})
# The devhouse 3 base cast of the park stands at its named spots (issue #219,
# stage 2): Sam beside the corn tent ("the snow festival stalls"), Julia at the
# foot of the snow castle's steps ("the snow castle"). Each is moved only from
# the cell they had before the park was rebuilt, so a later edit stays. Julia's
# line pointed at the Clock Tower she stood by: at the castle it names the castle
# (only that exact line, and only while she stands at the castle).
PARK_CAST = {'Sam': ((21, 27), (CORN[0] + 3, CORN[1] + 3)), 'Julia': ((39, 19), (CASTLE[0] + 2, CASTLE[1] + 4))}
PARK_LINES = {'Julia': ("That's the Sapporo Clock Tower behind me.", "That's the snow castle behind me. Three storeys of it.")}
for npc in prev.get('npcs', []):
    was, now = PARK_CAST.get(npc.get('name'), (None, None))
    if npc.get('trip') != 'devhouse3' or npc.get('stay') != 'Sapporo':
        continue
    if (npc['gridX'], npc['gridY']) == was:
        npc['gridX'], npc['gridY'] = now
    said, says = PARK_LINES.get(npc['name'], (None, None))
    if (npc['gridX'], npc['gridY']) == now and said in npc.get('dialogue', []):
        npc['dialogue'] = [says if line == said else line for line in npc['dialogue']]
# the konbini door keeps the transporter generate_konbinis.py wired onto it;
# with none to keep (a first build) it is sealed until that runs
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
# (listed in the order they already are: generate_konbinis.py appends its door)
cfg['rooms']['Sapporo'] = b.room('Sapporo', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    # into the station at its entry cell (generate_stations.py: a large station's is not 11,11)
    rg.transporter(x, y, 'SapporoStation',
                   *cfg.get('stations', {}).get('SapporoStation', {}).get('entry', [11, 11]), hidden=True)
    for x, y in station_doors
] + ([konbini_entry] if konbini_entry else []) + [
    don.door_transporter('Sapporo', store_door),
]))

rg.save_config(cfg)
print(f'Sapporo {W}x{H}; station doors at {station_doors} -> SapporoStation; '
      f'Clock Tower at {CLOCK}, TV Tower at {TOWER}, konbini at {KONBINI}')
