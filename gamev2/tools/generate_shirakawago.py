#!/usr/bin/env python3
"""generate_shirakawago.py — "Shirakawa-go", the mountain village between
Kanazawa and Toyama (issue #68, stage 3).

devhouse 2's Damian and Julia were here on 4-5 November 2025. It is a small
district of the stitched `HokurikuCity` (tools/hokuriku.py has the layout) with
NO station: you walk in along the road from Kanazawa (west edge, rows 10-12)
or down the mountain path from Toyama (north edge, columns 24-25).

  west    the road in from Kanazawa ends at a bus bay on the west bank, in
          autumn woods, under a bear warning (posts 631, 635: the bus, the bears)
  river   the Sho river, bank to bank down the whole map (and on through Toyama
          to the sea), crossed only by the SUSPENSION FOOTBRIDGE - "the scary
          bridge" of post 610, the "long wobbly bridge" of post 631. It is a
          flat deck you walk ON (the asahikawa-bridge recipe)
  east    the village: an earth lane from the bridge, GASSHO-ZUKURI farmhouses
          either side of it, harvested paddies with sheaves drying on racks,
          a path south between the fields
  NE      the VIEWPOINT: a gravel terrace up a flight of steps, a rail to look
          over the roofs from (post 631)
  north   the peaks, snow on top and autumn colour below ("a rainbow of green,
          brown and yellow ... some of the mountains have snow on them"), with
          the path to Toyama through the pass between them

Nobody gets lost behind a farmhouse: each is solid over its whole footprint,
thatch included, and the woods and the peaks are solid throughout.

Art is drawn by tools/generate_hokuriku_art.py. Deterministic and idempotent:
rebuilds rooms.Shirakawago from scratch each run, keeping any NPCs the blog
pipeline has placed there. The build order for the whole region is in
tools/generate_kanazawa.py.

Run from gamev2/:  python3 tools/generate_shirakawago.py
"""
import random
import roomgen as rg
from roomgen import rect
import hokuriku as hk

cfg = rg.load_config()

W, H = hk.SIZE['Shirakawago']
b = rg.Builder(W, H)
k = hk.Kit(b)
rng = random.Random(6810)

ROAD = hk.S_ROAD[0]               # the road from Kanazawa: rows 10-12
DECK = ROAD + 1                   # the bridge deck's row, and the lane's upper row
R0, R1 = hk.S_RIVER               # the river, bank to bank (columns 10-15)
P0, P1 = hk.S_PATH                # the path north to Toyama (columns 24-25)
AUTUMN = ['sendai-maple', 'hokuriku-ginkgo', 'sendai-cedar', 'sendai-maple', 'sendai-pine']

b.fill('grass-autotile')

# ---- the west bank: the road in, a bus bay, the bridgehead --------------------------
k.road_h(0, 6, ROAD, cap_e=True)
b.autotile('light-concrete-autotile', rect(7, ROAD, R0 - 1, ROAD + 2))
b.stamp('bus-stop', 7, ROAD - 1); b.solid(7, ROAD - 1)
BEAR = (5, ROAD - 2)
b.stamp('shirakawa-bear-sign', *BEAR)                 # feet on the verge, beside the road
k.woods(0, 0, R0 - 1, ROAD - 1, AUTUMN, rng)
k.woods(0, ROAD + 3, R0 - 1, H - 1, AUTUMN, rng)

# ---- the Sho river ------------------------------------------------------------------
for y in range(H):
    for x in range(R0, R1 + 1):
        role = 'edge-w' if x == R0 else 'edge-e' if x == R1 else 'center'
        b.put('Water', x, y, f'pond-autotile_{role}')
        if y != DECK:
            b.solid(x, y)                             # the deck row is the only way over
BRIDGE = (R0 - 1, DECK - 1)                           # 8x2: its towers stand on the banks
b.stamp('shirakawa-bridge', *BRIDGE)

# ---- the village, on the east bank -----------------------------------------------------
LANE_END = 33
b.autotile('dirt-outside-autotile',
           rect(R1 + 1, DECK, LANE_END, DECK + 1)                 # the lane from the bridge
           + rect(P0, 0, P1, DECK - 1)                            # the path north to Toyama
           + rect(22, DECK + 2, 23, 22) + rect(22, 21, 34, 22))   # the path south, and east between the paddies

b.put('Floor', P0, 0, 'dirt-outside-autotile_edge-w')         # the path runs on into Toyama: no rounded end
b.put('Floor', P1, 0, 'dirt-outside-autotile_edge-e')


def farmhouse(name, x, y, w, h):
    """A gassho farmhouse, solid over the whole of its thatch."""
    b.stamp(name, x, y)
    k.solid_rect(x, y, x + w - 1, y + h - 1)


GASSHO = (17, 6)                                      # the big house by the bridge: feet on row 10
farmhouse('shirakawa-gassho', *GASSHO, 5, 5)
farmhouse('shirakawa-gassho-small', 26, 7, 4, 4)      # under the viewpoint
farmhouse('shirakawa-gassho-small', 17, 15, 4, 4)     # south of the lane, feet on row 18
farmhouse('shirakawa-gassho', 18, 23, 5, 5)           # feet on row 27
farmhouse('shirakawa-gassho-small', 28, 14, 4, 4)     # among the fields, feet on row 17
k.trees('sendai-maple', [(22, 10), (30, 10)])
k.trees('hokuriku-ginkgo', [(16, 22), (34, 13)])
# the paddies, harvested, sheaves drying on the racks
for x, y in rect(24, 14, 27, 20) + rect(32, 15, 34, 20) + rect(28, 18, 31, 20) + rect(24, 23, 34, 27):
    b.put('Floor', x, y, 'shirakawa-paddy_0_0')
b.stamp('shirakawa-hasa', 24, 15); b.stamp('shirakawa-hasa', 30, 24); b.stamp('shirakawa-hasa', 25, 25)

# ---- the viewpoint (north-east): up the steps from the lane's east end ---------------------
STAIR0, STAIR1 = 32, 33
b.autotile('gravel-autotile', rect(28, 4, 34, 5))
k.paved(rect(STAIR0, 6, STAIR1, DECK - 1))
for x, y in rect(STAIR0, 6, STAIR1, DECK - 1):
    b.stairs(x, y)
LOOKOUT = (28, 6)                                     # the rail, along the terrace's south edge
b.stamp('shirakawa-lookout', *LOOKOUT)
k.solid_rect(30, 7, 31, 10)                           # the bank between the house and the steps
k.solid_rect(34, 6, 35, 10)

# ---- the peaks along the north, the pass between them ----------------------------------------
for x in (R1 + 1, R1 + 3, 26, 28, 30):                # a range: each peak overlaps the next
    b.stamp('shirakawa-peak', x, 0)
k.solid_rect(R1 + 1, 0, P0 - 1, 3); k.solid_rect(P1 + 1, 0, W - 1, 3)
k.trees('sendai-cedar', [(22, 5)])
k.solid_rect(R1 + 1, 4, P0 - 1, 5)
k.solid_rect(P1 + 1, 4, 27, 6)

# ---- the edges: woods east and south, a fence along the bottom ---------------------------------
for y in range(4, H - 1):
    if not k.taken(W - 1, y):
        b.stamp('shrub-small', W - 1, y)
k.solid_rect(W - 1, 4, W - 1, H - 1)
k.woods(R1 + 1, 28, W - 2, H - 2, AUTUMN, rng)
for i, x in enumerate(range(R1 + 1, W)):
    b.fence(x, H - 1, i)
k.plants(rng, 70, R1 + 1, 4, W - 2, 27)

# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Shirakawago', {})
k.dress()         # no invisible walls: a bare collider beside open ground becomes a shrub
b.finish()
cfg['rooms']['Shirakawago'] = b.room('Shirakawa-go', npcs=prev.get('npcs', []),
                                     transporters=rg.kept_order(prev, hk.seams('Shirakawago')))
rg.save_config(cfg)
print(f'Shirakawa-go {W}x{H}; bridge at {BRIDGE} (deck row {DECK}), farmhouse at {GASSHO}, '
      f'viewpoint rail at {LOOKOUT}; road west on rows {hk.S_ROAD}, path north on columns {hk.S_PATH}')
