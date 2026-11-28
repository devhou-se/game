#!/usr/bin/env python3
"""generate_asahikawa.py — "Asahikawa", a day trip up the line from Sapporo (issue #43),
rebuilt from its own art (issue #219, stage B).

A small generated town (the roomgen recipe), reachable ONLY by train through
the AsahikawaStation interior (built by generate_stations.py). Snowier and
quieter than Sapporo: a small cold river city of timber and glass, a ramen
town, with a zoo.

  north   the rail line; under it ASAHIKAWA STATION's glass hall (its two door
          cells lead into the station) and HEIWA-DORI, the pedestrian shopping
          street on its own granite setts: a 7-Eleven, a bookshop, a sake shop,
          a bakery and a woodcraft shop in one row with the station, ice
          sculptures, benches and the street's own lamps
  west    RAMEN ALLEY on wet asphalt, through its lantern gate off Heiwa-dori
          (or round its open east end): a shoyu counter, a narrow shop and a
          miso shop, feet on row 13, a closed yard of snow trees behind them
  middle  the frozen river, bank to bank, and ASAHIBASHI, the green steel
          arch that is the only way over: a flat deck you walk on, a rib each
          side, a brace overhead; a fishing tent and holes cut in the ice
  south   three Hokkaido houses behind a snow fence, and the ASAHIYAMA ZOO
          GATE with its ticket booth, fence, penguins and seal; the wood
          behind the gate is closed (the gate's porch is one cell deep)

The river is laid by hand (ice edge-n / center / edge-s rows) because
Builder.pond is two rows tall and rock-rimmed at both ends; the deck is a
flat sprite over the ice whose cells are left open (see 'asahibashi-deck' in
tools/make_prefabs.py). The art is generate_asahikawa_art.py's.
Doors: the houses, the shops (sake, bakery, woodcraft, the shoyu counter) and
the 7-Eleven are opened by generate_houses.py and generate_konbinis.py, which
run after this; the bookshop and the other two ramen shops stay sealed.
Deterministic and idempotent: rebuilds rooms.Asahikawa from scratch each run,
keeping any NPCs the blog pipeline has placed there.

Run from gamev2/:
    python3 tools/generate_asahikawa_art.py       # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_asahikawa.py
    python3 tools/generate_houses.py Asahikawa; python3 tools/generate_houses.py --shops Asahikawa
    python3 tools/generate_konbinis.py Asahikawa
    python3 tools/generate_stations.py            # builds AsahikawaStation + registry
    node tools/play.js lint Asahikawa          (and AsahikawaStation)
    python3 tools/config_to_tiled.py Asahikawa AsahikawaStation
"""
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 42, 32
b = rg.Builder(W, H)

b.fill('snow-autotile')

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-snow-autotile', rect(0, 3, W - 1, 5))   # gravel with a snow bank, not a grass fringe
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
# the south fence runs wherever no building's top row stands on row 6 (the
# 7-Eleven, the sake shop, the bakery and the station all start on row 5 or 6)
for x in list(range(1, 12)) + list(range(15, 18)) + list(range(24, 28)) + list(range(38, W - 1)):
    b.fence(x, 6, x)
for y in (3, 4, 5):                                   # snowy caps at the corridor ends
    b.stamp('shrub-small-snow', 0, y); b.stamp('shrub-small-snow', W - 1, y)

# ---- the ground of the streets: Heiwa-dori's setts from the alley gate to the
#      station's far end with a leg down to the bridgehead, and the ramen
#      alley's wet asphalt. The two meet as one street: an edge is laid only
#      where the snow is, never between them ---------------------------------------
BRIDGE = (20, 16)
PAVING = set(rect(11, 10, 38, 12)) | set(rect(19, 13, 22, 15))
ALLEY = set(rect(2, 14, 18, 15)) | {(12, 13)}          # (12,13): the cell under the gate
STREET = PAVING | ALLEY


def street(fam, cells):
    """rg.Builder.autotile for a part of STREET: its edges and corners face the snow only."""
    for x, y in cells:
        n, e, s, w = (x, y - 1) in STREET, (x + 1, y) in STREET, (x, y + 1) in STREET, (x - 1, y) in STREET
        role = {(False, True, True, False): 'corner-nw', (False, False, True, True): 'corner-ne',
                (True, True, False, False): 'corner-sw', (True, False, False, True): 'corner-se',
                (False, True, True, True): 'edge-n', (True, True, False, True): 'edge-s',
                (True, True, True, False): 'edge-w', (True, False, True, True): 'edge-e'}.get((n, e, s, w), 'center')
        b.put('Floor', x, y, f'{fam}_{role}')


street('heiwa-paving-autotile', PAVING)
street('ramen-alley-autotile', ALLEY)
# the trodden path south of the river (dirt-snow: the dirt path with a snow bank)
b.autotile('dirt-snow-autotile', rect(4, 28, 37, 29) + rect(20, 21, 21, 27))

# ---- Asahikawa Station: its glass hall on the old station house's door cell,
#      so the way in and out of AsahikawaStation has not moved --------------------
STATION = (28, 5)
station_doors = b.stamp('asahikawa-station-front', *STATION, seal=False)   # (32,9), (33,9)
b.stamp('tree-snow', 38, 6)                           # closes the corner behind the hall's east end

# ---- Heiwa-dori: one row of shopfronts west of the station, feet on row 9 ------
KONBINI = (12, 6)
konbini_door = b.stamp('seven-eleven', *KONBINI, seal=False)[0]   # wired by generate_konbinis.py; kept below
b.stamp('heiwa-shop-books', 15, 7)                    # sealed: nothing in the catalogue is a book
b.stamp('heiwa-shop-sake', 18, 6)
b.stamp('heiwa-shop-bakery', 21, 6)
b.stamp('heiwa-shop-woodcraft', 24, 7)
# on the setts: the ice sculptures and benches down the middle, the street's own
# lamps along its south side. Door fronts (row 10) and the stand cells stay clear.
b.stamp('ice-sculpture-crane', 15, 10)
b.stamp('ice-sculpture-owl', 25, 10)
b.stamp('heiwa-bench', 20, 11); b.stamp('heiwa-bench', 35, 11)
for x in (23, 30, 37):                                # (31,12) is where a stay that starts here stands
    b.stamp('heiwa-lamp', x, 11)
b.stamp('vending-red', 18, 12)

# ---- ramen alley: three fronts in a row, feet on row 13, facing the asphalt ----
b.stamp('ramen-shoyu-front', 2, 10)
b.stamp('ramen-narrow-front', 6, 10)                  # sealed: one ramen shop is opened, the shoyu counter
b.stamp('ramen-miso-front', 8, 10)                    # sealed
RAMEN_GATE = (11, 11)
b.stamp('asahikawa-ramen-gate', *RAMEN_GATE)          # through its middle cell, (12,13), off Heiwa-dori
# against the fronts, feet on row 14. Somebody stood on row 15 is walked round
# along row 14 or along the bank, row 16: so no foot within two columns of a bank
# shrub (13, 16), and no single free cell between two feet
b.stamp('ramen-crates', 2, 13)
b.stamp('ramen-stockpot', 3, 13)
b.stamp('asahikawa-ramen-lanterns', 6, 13); b.stamp('asahikawa-ramen-lanterns', 10, 13)
b.stamp('asahikawa-ramen-lanterns', 14, 12)           # east of the gate, foot on the snow of row 13
# the yard behind the alley: snow trees, and a hedge on column 11 so nobody
# wanders in behind the shops from Heiwa-dori
for x in (3, 8):
    b.stamp('tree-snow', x, 6)
for y in (7, 8, 9):
    b.stamp('shrub-small-snow', 11, y)

# ---- the frozen river, bank to bank, and Asahibashi ------------------------------
for x in range(W):
    for y, role in ((17, 'edge-n'), (18, 'center'), (19, 'edge-s')):
        b.put('Water', x, y, f'ice-pond-autotile_{role}')
        if x not in (BRIDGE[0], BRIDGE[0] + 1):
            b.solid(x, y)
b.stamp('asahibashi-deck', *BRIDGE)                   # rows 16-20, walked on
b.stamp('asahibashi-arch-w', BRIDGE[0] - 1, BRIDGE[1])
b.stamp('asahibashi-arch-e', BRIDGE[0] + 2, BRIDGE[1])
b.stamp('asahibashi-brace', BRIDGE[0] - 1, BRIDGE[1] + 2)   # over the deck's middle row, above the player
for x in (13, 16, 27, 33, 38):                                # bare shrubs on the banks
    b.stamp('shrub-small-snow', x, 16)
for x in (3, 9, 14, 25, 28, 35):
    b.stamp('shrub-small-snow', x, 20)
# on the ice (overlays go on Non-Collidables, above the Water layer)
b.stamp('ice-fishing-tent', 6, 17)
for key, x in (('ice-fishing-hole', 9), ('ice-crack-a', 13), ('ice-crack-b', 26), ('ice-crack-a', 31),
               ('ice-fishing-hole', 33), ('ice-crack-b', 37)):
    b.put('Non-Collidables', x, 18, f'{key}_0_0')

# ---- south bank, west of the path: three Hokkaido houses behind a snow fence ---
for x, colour in ((4, 'red'), (9, 'blue'), (14, 'red')):
    b.stamp(f'hokkaido-house-{colour}', x, 23)        # doors (5,26), (10,26), (15,26)
b.stamp('vending-white', 7, 25)
for x in list(range(4, 9)) + list(range(10, 14)):
    b.stamp('snow-fence-h', x, 21)
b.stamp('tree-snow', 16, 20)
b.stamp('lantern-red', 18, 26); b.stamp('lantern-red', 23, 26)   # either side of the path

# ---- south bank, east: the Asahiyama Zoo gate. The gate has no back, so the
#      ground behind it is a closed wood: a hedge on column 26, the fence either
#      side of the gate, the ticket booth, and the gate's own porch -----------------
ZOO_GATE = (29, 22)
b.stamp('zoo-gate', *ZOO_GATE)                        # feet on row 25; the porch is (30..32, 25)
for y in (21, 22, 23, 24):
    b.stamp('shrub-small-snow', 26, y)
for x in (27, 28):
    b.stamp('zoo-fence-h', x, 24)
b.stamp('zoo-ticket-booth', 34, 23)
for x in (36, 37, 38):
    b.stamp('zoo-fence-h', x, 24)
b.stamp('zoo-fence-end', 39, 24)
for x in (27, 30, 33, 37):                            # the wood
    b.stamp('tree-snow', x, 20)
b.stamp('zoo-seal-statue', 25, 26)
b.stamp('penguin-walk-a', 35, 26); b.stamp('penguin-walk-b', 37, 26)

# ---- borders: snowy hedges west / east (the river itself closes rows 17-19),
#      a fence along the south --------------------------------------------------
for y in list(range(7, 17, 2)) + list(range(20, 30, 2)):
    b.stamp('shrub-large-snow', 0, y); b.stamp('shrub-large-snow', W - 2, y)
for x in (0, 1, W - 2, W - 1):
    b.stamp('shrub-small-snow', x, 30)
for x in (0, W - 1):
    b.stamp('shrub-small-snow', x, 6); b.stamp('shrub-small-snow', x, 31)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, 31, i)

# isolated: the ONLY way out is the station's doors into AsahikawaStation.
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Asahikawa', {})
# Julia stands on the south bank and used to point at the shrine that stood
# where the zoo gate is: her base line follows the town
SAID = {'Julia': ("There's a shrine on this side of the frozen river.",
                  "The zoo gate is on this side of the frozen river.")}
for npc in prev.get('npcs', []):
    said, says = SAID.get(npc.get('name'), (None, None))
    if said in npc.get('dialogue', []):
        npc['dialogue'] = [says if line == said else line for line in npc['dialogue']]
# the konbini door keeps the transporter generate_konbinis.py wired onto it;
# with none to keep (a first build) it is sealed until that runs
konbini_entry = rg.kept_door(prev, konbini_door, 'Konbini')
if not konbini_entry:
    b.solid(*konbini_door)
b.finish()      # picket fences + solid tracks: the room is complete without a post-pass
cfg['rooms']['Asahikawa'] = b.room('Asahikawa', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, [
    # one hidden transporter per door cell of the station front, into the station's entry
    rg.transporter(x, y, 'AsahikawaStation',
                   *cfg.get('stations', {}).get('AsahikawaStation', {}).get('entry', [11, 11]), hidden=True)
    for x, y in station_doors
] + ([konbini_entry] if konbini_entry else [])))

rg.save_config(cfg)
print(f'Asahikawa {W}x{H}; station doors at {station_doors} -> AsahikawaStation; '
      f'bridge at {BRIDGE}, zoo gate at {ZOO_GATE}')
