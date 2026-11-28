#!/usr/bin/env python3
"""generate_shinjuku.py — "Shinjuku", the street of high-rises west of
Marunouchi (issue #94).

Market and Palace are ported maps with no free street frontage, so the towers
issue #18 asked for stand here instead: a fifth district of the stitched
`TokyoCity` (config `cities`, src/systems/CityStitcher.js), in what was the
wood west of the Palace/Park west road. Nothing of Tokyo, Market, Palace or
Park is moved or removed.

  east    the district's last column is the WEST KERB of the west road (the
          city's backdrop drew it there until now). On rows 14-16 it is open
          road: the road between Palace and Park (Palace rows 18-20, Park rows
          0-2) carries on west through its junction as Shinjuku's avenue, and
          the junction is a crossroads
  north   five towers standing on row 11, one of each kind, vending machines
          between two of them, wood behind and between
  middle  the avenue, a pavement either side, a zebra crossing under two
          signals. It ends in the west at a turning box with a bus bay beside
          it: a road that leaves a junction leads somewhere
  south   the south block: four towers standing on row 29, trees round them,
          opening onto a promenade that joins the avenue's pavements at both
          ends of the block

Every tower opens into a lobby (LobbyShinjuku1-9): tools/generate_houses.py
--lobbies Shinjuku finds them and wires their doors, and roomgen.save_config
keeps those doors when this generator rebuilds the room.

There is no new art: the towers are the prefabs of tools/make_prefabs.py, the
road, the pavement and the wood are what the rest of the city is made of.
Deterministic and idempotent: rebuilds rooms.Shinjuku from scratch each run,
keeping any NPCs the blog pipeline has placed there. It also pins Palace's
side of the seam (three hidden transporters, for `?stitch=0`) and adds the
district to cities.TokyoCity.rooms when it is not there; where it sits is
../devhouse.world's to say (tools/sync_cities.py).

Run from gamev2/:  python3 tools/generate_shinjuku.py
Build order for a first build, or after moving a tower:
    python3 tools/generate_shinjuku.py
    python3 tools/generate_houses.py --lobbies Shinjuku
    python3 tools/sync_cities.py
    python3 tools/districts.py
    python3 tools/config_to_tiled.py Shinjuku Palace LobbyShinjuku1 ... LobbyShinjuku9
    python3 tools/make_worldmap.py                  (needs Pillow)
"""
import random
import roomgen as rg
from roomgen import rect
import hokuriku as hk

cfg = rg.load_config()

W, H = 34, 36
AT = (24, 51)                     # in TokyoCity's cells; devhouse.world is the truth (sync_cities.py)
KERB = W - 1                      # the west road's west kerb (the city's column 57)
AVE = 14                          # the avenue: rows 14-16 (the city's 65-67, the Palace/Park road carried on west)
FRONT_N, FRONT_S = 11, 29         # the rows the two rows of towers stand on
NORTH = [('highrise-apartment', 4, 5, 8), ('highrise-glass', 10, 4, 10), ('highrise-blue', 15, 5, 11),
         ('highrise-yellow', 21, 4, 8), ('midrise-apartment', 26, 5, 6)]          # prefab, x, w, h
SOUTH = [('highrise-blue', 5, 5, 11), ('highrise-glass', 12, 4, 10), ('highrise-apartment', 18, 5, 8),
         ('highrise-yellow', 25, 4, 8)]
CROSSING = (22, 23)               # the zebra crossing's columns
ROAD_ROW = 18                     # Palace: the first row of the road the avenue carries on (rows 18-20, at x = 0)
IN = 3                            # a seam transporter lands this many cells inside the neighbour

b = rg.Builder(W, H)
k = hk.Kit(b)
rng = random.Random(94)

b.fill('grass-autotile')

# ---- the pavements: one each side of the avenue, the promenade, the two walks that join them ----
b.autotile('flat-grey-brick-autotile',
           sorted(set(rect(2, AVE - 2, KERB - 1, AVE - 1) + rect(2, AVE + 3, KERB - 1, AVE + 4)
                      + rect(2, AVE, 3, AVE + 2)                                  # round the avenue's west end
                      + rect(2, AVE + 5, 3, FRONT_S + 3) + rect(KERB - 2, AVE + 5, KERB - 1, FRONT_S + 3)
                      + rect(2, FRONT_S + 1, KERB - 1, FRONT_S + 3))))

# ---- the avenue, and the west road's kerb it leaves through ---------------------------------------
k.road_h(4, KERB - 1, AVE, cap_w=True)
for y in range(H):
    b.put('Floor', KERB, y, 'road-plain_0_0' if AVE <= y <= AVE + 2 else 'road-edge-left_0_0')
for x in (5, 6) + CROSSING:       # the turning box at the west end, and no centre line under the zebra
    b.put('Floor', x, AVE + 1, 'road-plain_0_0')
for x in CROSSING:
    b.stamp('crossing-h', x, AVE)
b.stamp('traffic-light', CROSSING[0] - 1, AVE - 3)        # feet on the north pavement
b.stamp('traffic-light', CROSSING[1] + 1, AVE + 1)        # feet on the south pavement

# ---- the towers -------------------------------------------------------------------------------------
for name, x, w, h in NORTH:
    k.building(name, x, FRONT_N - h + 1, w)
for name, x, w, h in SOUTH:
    k.building(name, x, FRONT_S - h + 1, w)
b.stamp('vending-white', 9, FRONT_N - 1); b.stamp('vending-red', 14, FRONT_N - 1)
b.stamp('utility-pole', 20, FRONT_N - 2)
BUS = (4, AVE + 3)
b.stamp('bus-stop', *BUS); b.solid(*BUS)                  # the bus bay the avenue ends at

# ---- wood: behind and between the towers, round the south block, along the edges ---------------------
k.woods(0, 0, KERB - 1, FRONT_N, ['tree-green'], rng)
k.woods(0, FRONT_N + 1, 1, H - 1, ['tree-green'], rng)
k.woods(4, AVE + 5, KERB - 3, FRONT_S, ['tree-green'], rng)
k.woods(2, FRONT_S + 4, KERB - 1, H - 1, ['tree-green'], rng)

# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Shinjuku', {})
seams = [rg.transporter(KERB, AVE + i, 'Palace', IN, ROAD_ROW + i, hidden=True) for i in range(3)]
k.dress()         # no invisible walls: a bare collider beside open ground becomes a shrub
b.finish()
cfg['rooms']['Shinjuku'] = b.room('Shinjuku', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, seams))
for i in range(3):                # Palace is a ported map: its side of the seam is pinned, nothing else touched
    rg.pin(cfg['rooms']['Palace']['transporters'],
           rg.transporter(0, ROAD_ROW + i, 'Shinjuku', KERB - IN, AVE + i, hidden=True))
if not any(m['room'] == 'Shinjuku' for m in cfg['cities']['TokyoCity']['rooms']):
    cfg['cities']['TokyoCity']['rooms'].append({'room': 'Shinjuku', 'x': AT[0], 'y': AT[1]})
rg.save_config(cfg)
print(f'Shinjuku {W}x{H}; the avenue on rows {AVE}-{AVE + 2}, {len(NORTH)} towers standing on row {FRONT_N} '
      f'and {len(SOUTH)} on row {FRONT_S}, the crossing on columns {CROSSING}, the bus bay at {BUS}')
