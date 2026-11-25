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
  middle  the Dotonbori canal, crossed by the street (the bridge)

The main street is Osaka's one asphalt ROAD (issue #106): four cells of roadway
(columns 23-26) between brick pavements, from below the station forecourt,
under the arch and over the bridge to the tower's garden, with a signalled
zebra crossing between the arch and the bridge. Roads are ordinary walkable
floor - there is no traffic.

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
    python3 tools/generate_discount_art.py        # the discount store's interior signage
    python3 tools/make_prefabs.py
    python3 tools/generate_osaka.py
    python3 tools/generate_discount_stores.py Osaka   # DonTakoteOsaka (the door is wired here)
    python3 tools/generate_stations.py            # builds OsakaStation + registry
    python3 tools/fix_fences.py Osaka             # MANDATORY (b.fence)
    python3 tools/seal_tracks.py Osaka            # MANDATORY (rail line)
    python3 tools/config_to_tiled.py Osaka OsakaStation DonTakoteOsaka
    node tools/play.js lint Osaka OsakaStation DonTakoteOsaka
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect
import generate_discount_stores as don

cfg = rg.load_config()

W, H = 50, 40
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
b.autotile('brown-brick-autotile', rect(2, 23, 47, 37))
b.autotile('flat-grey-brick-autotile', rect(22, 10, 27, 22))
b.autotile('light-concrete-autotile', rect(18, 32, 31, 37))  # the tower's plaza

# ---- the road (issue #106): the main street's middle four columns are asphalt,
#      the dark brick either side is its pavement. It starts a row below the
#      station door (you step out onto paving, not into the road) and ends at the
#      tower's garden, where the street forks. Four wide, not the usual three
#      (edge / centre line / edge): the arch's opening and the tower's archway
#      are both an even number of cells, so only an even road sits on their axis.
ROAD_X0, ROAD_X1 = 23, 26
ROAD_Y0, ROAD_Y1 = 11, 22
for y in range(ROAD_Y0, ROAD_Y1 + 1):
    b.put('Floor', ROAD_X0, y, 'road-edge-left_0_0')
    for x in range(ROAD_X0 + 1, ROAD_X1):
        b.put('Floor', x, y, 'road-plain_0_0')
    b.put('Floor', ROAD_X1, y, 'road-edge-right_0_0')

# the zebra crossing, between the arch and the bridge, on the row the canal-bank
# lamps stand on: it joins the west bank's shops to the ferris wheel. The
# crossing-v prefab is three cells (one per cell of a standard road); this road
# has one more lane, so the same three tiles are laid here with the middle one
# repeated. Both signals stand on the pavement just south of it, at the
# bridgehead: north of it their heads would be lost in the arch's side boards.
CROSSING_Y = 18
b.put('Over Floor', ROAD_X0, CROSSING_Y, 'crossing-v-left_0_0')
for x in range(ROAD_X0 + 1, ROAD_X1):
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

# ---- the Dotonbori canal, bridged by the main street --------------------------
b.pond(2, 20, 21)
b.pond(28, 20, 47)
b.stamp('lantern-red', 20, 22); b.stamp('lantern-red', 29, 22)   # south bridgehead (clear of
                                                                 # the tower's own top-left cell)

# ---- Shinsekai: Tsutenkaku on the axis of the street, on its plaza ------------
TOWER = (21, 23)
b.stamp('tsutenkaku', *TOWER)
# The tower garden: the tower is 13 cells tall and stands on the street's axis,
# so without this the main street would run BEHIND it and hide the player for
# ten cells. A thicket fills the ground behind the shaft and deck; the street
# forks at the bridgehead and passes either side of it down to the plaza.
for gy in range(24, 32, 2):
    for gx in range(22, 28, 2):
        for cx, cy in rect(gx, gy, gx + 1, gy + 1):
            b.put('Floor', cx, cy, 'grass-autotile_center')
        b.stamp('shrub-large', gx, gy)
b.stamp('lantern-red', 19, 35); b.stamp('lantern-red', 30, 35)
for i, (px, py) in enumerate([(19, 33), (30, 33), (22, 37), (27, 37), (20, 37), (29, 37)]):
    b.paver(px, py, i)
b.stamp('highrise-apartment', 3, 24); b.stamp('house-black', 10, 26)       # feet on row 31
b.stamp('house-blue', 37, 26); b.stamp('highrise-glass', 42, 22)
b.stamp('vending-red', 14, 29); b.stamp('vending-white', 35, 29)
b.stamp('lantern-red', 9, 31); b.stamp('lantern-red', 41, 31)
b.stamp('sakura-large', 16, 26); b.stamp('sakura-large', 31, 26)   # flanking the tower
b.stamp('sakura-large', 3, 33); b.stamp('sakura-large', 44, 33)
b.stamp('sakura-small', 15, 34); b.stamp('sakura-small', 34, 34)
b.stamp('shrub-small', 17, 30); b.stamp('shrub-small', 32, 30)
b.stamp('shrub-small', 46, 25)
for x in (8, 13, 36, 41):
    b.stamp('lamp-blue', x, 36)

# ---- street accessories (issue #19; tools/extract_street.py): bikes and a
#      scooter outside the discount store (clear of its door at column 15), the
#      bus stop on the kerb where the road begins (#106), a utility pole on the
#      north bank, a scooter by the flats. The zebra crossing and its signals
#      are with the road, above. -----------------------------------------------
b.stamp('bicycle-blue', 13, 17); b.stamp('bicycle-orange', 14, 17); b.stamp('scooter-grey', 18, 17)
b.stamp('bus-stop', 21, 11); b.stamp('utility-pole', 19, 16); b.stamp('scooter-red', 8, 32)

# ---- borders: hedges west / east, a fence along the south ---------------------
#      (continuous — a gap would let the player slip round behind the fences)
for y in range(8, 38, 2):
    b.stamp('shrub-large', 0, y); b.stamp('shrub-large', W - 2, y)
b.stamp('shrub-small', 0, 38); b.stamp('shrub-small', W - 1, 38)
for y in (6, 7):
    b.stamp('shrub-small', 0, y); b.stamp('shrub-small', W - 1, y)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, 38, i)

# ---- greenery on the canal banks ----------------------------------------------
for i in range(60):
    sx, sy = rng.randrange(2, W - 2), rng.choice((19, 22))
    if 42 <= sx <= 45 and sy == 22:               # under the glass tower's roof line
        continue
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
cfg['rooms']['Osaka'] = b.room('Osaka', npcs=prev.get('npcs', []), transporters=[
    rg.transporter(station_door[0], station_door[1], 'OsakaStation', 11, 11, hidden=True),
    don.door_transporter('Osaka', store_door),
])

rg.save_config(cfg)
print(f'Osaka {W}x{H}; station house door at {station_door} -> OsakaStation; '
      f'arch at {ARCH}, ferris wheel at {WHEEL}, Tsutenkaku at {TOWER}')
