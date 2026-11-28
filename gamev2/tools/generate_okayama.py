#!/usr/bin/env python3
"""generate_okayama.py — "Okayama", the black castle and Korakuen, west of Himeji (issue #267; #68, run 4).

devhouse 2's Damian was here on 12 November 2025 (post 745: Hakata to Okayama,
Korakuen, the castle, Bizen ware). It is the westernmost district of the
stitched `KansaiCity` (tools/kansai.py has the layout) with NO station: you
walk in from Himeji along the avenue (east edge, rows 18-22). Its own west edge
is closed: nothing is planned beyond it.

The district is laid out on one north-south axis (columns 21-22): the keep, the
steps down the stone wall, across the avenue, the Tsukimi bridge, the island.

  north   OKAYAMA CASTLE, the black "crow castle", on a gravel terrace above a
          stone wall, with pines and stone lanterns. The only way up is the
          steps on the axis
  avenue  the avenue in from Himeji ends in a paved PLAZA: the bronze MOMOTARO
          with his dog, monkey and pheasant, and a stall of BIZEN WARE beside
          the pavement. A fingerpost stands by the seam
  south   KORAKUEN on its island in the river, over the TSUKIMI BRIDGE: a
          gravel loop round the lawns, a pond, pines and maples, lanterns, two
          red-crowned cranes

The river is a ring of `pond-autotile` round the island, solid but for the
bridge's two columns. The set has no inner-corner piece, so a heap of the rim's
own stones (`okayama-bank-rock`) lies over each corner of the island. No arm of
the ring leads anywhere, so it is not a `waterways` run: no boat sails it.

Nobody gets lost behind anything: the keep is solid over its whole footprint,
roof rows and all, and the woods round the district are solid throughout. There
is no building with a door here: the keep is looked at, not entered, and the
stall is an open counter.

Art is drawn by tools/generate_kansai_art.py. Deterministic and idempotent:
rebuilds rooms.Okayama from scratch each run, keeping any NPCs the blog
pipeline has placed there. The build order for the whole region is in
docs/landmarks-and-towns.md ("Kansai").

Run from gamev2/:  python3 tools/generate_okayama.py
"""
import random
import roomgen as rg
from roomgen import rect
import kansai as ks

cfg = rg.load_config()

W, H = ks.SIZE['Okayama']
b = rg.Builder(W, H)
k = ks.Kit(b)
rng = random.Random(267)

AVE0, AVE1 = ks.OK_AVENUE[0], ks.OK_AVENUE[-1]    # the avenue in from Himeji: rows 18-22
AXIS = (21, 22)                                   # the columns everything lines up on
PLAZA = (6, 15, 12, 23)                           # where the avenue ends
KEEP = (18, 2)                                    # 8x7: rows 0-1 behind it are wood
WALL = 13                                         # the terrace's stone wall: rows 13-14
RIVER = (5, 24, 40, 37)                           # the ring of water, and
ISLAND = (7, 27, 38, 35)                          # Korakuen inside it
BRIDGE = (AXIS[0], RIVER[1])                      # 2x4: the Tsukimi bridge, landing on row 27
POND = (14, 31, 19)                               # the garden's pond: x0, its first row, x1
AUTUMN = ['sendai-maple', 'sendai-pine', 'sendai-cedar', 'sendai-maple', 'sendai-pine']

b.fill('grass-autotile')

# ---- the avenue, in from Himeji, and the plaza it ends in -----------------------------
b.autotile('flat-grey-brick-autotile', rect(6, AVE0, W - 1, AVE1) + rect(*PLAZA))
b.put('Floor', W - 1, AVE0, 'flat-grey-brick-autotile_edge-n')    # the pavement runs on into Himeji:
b.put('Floor', W - 1, AVE1, 'flat-grey-brick-autotile_edge-s')    # no rounded corner at the seam
k.road_h(PLAZA[2] + 1, W - 1, AVE0 + 1, cap_w=True)
k.paved(rect(AXIS[0], 15, AXIS[1], AVE0 - 1) + rect(AXIS[0], AVE1 + 1, AXIS[1], AVE1 + 1))   # the axis crosses it

# ---- the castle terrace -----------------------------------------------------------------
# The gravel is laid before the keep and the wall, and runs in under the wall's top
# row, so nothing green shows between them.
b.autotile('gravel-autotile', rect(13, 3, 40, WALL))
for x in range(13, 41):
    if x not in AXIS:
        b.wall_stone(x, WALL)                                     # rows 13-14
k.paved(rect(AXIS[0], WALL, AXIS[1], WALL + 1))                   # the steps: the only way up
for x, y in rect(AXIS[0], WALL, AXIS[1], WALL + 1):
    b.stairs(x, y)
b.stamp('okayama-keep', *KEEP)
k.solid_rect(KEEP[0], KEEP[1], KEEP[0] + 7, KEEP[1] + 6)          # its roof rows too: nobody walks in behind it
# None of these on (18..25, 9..10): whoever the blog pipeline stands in front of the
# keep is there, and so is whoever walks up to talk to them.
k.trees('sendai-pine', [(14, 6), (29, 5), (36, 7), (38, 11)])
for x, y in ((16, 10), (27, 10)):                                 # feet
    b.stamp('sendai-stone-lantern', x, y - 1)

# ---- the plaza: Momotaro, and the Bizen-ware stall beside the pavement -------------------
b.stamp('okayama-momotaro', 8, 17)                                # feet on (8..9, 19)
b.stamp('okayama-bizen-stall', 15, 15)                            # bumped from the pavement, row 18

# ---- the river round Korakuen ------------------------------------------------------------
rx0, ry0, rx1, ry1 = RIVER
ix0, iy0, ix1, iy1 = ISLAND


def bank(x, y):
    """The pond piece of a cell of the ring: rimmed on the side its bank is."""
    if (x, y) in ((rx0, ry0), (rx1, ry0), (rx0, ry1), (rx1, ry1)):
        return 'corner-' + ('n' if y == ry0 else 's') + ('w' if x == rx0 else 'e')
    if y == ry0 or (y == iy1 + 1 and ix0 <= x <= ix1):
        return 'edge-n'
    if y == ry1 or (y == iy0 - 1 and ix0 <= x <= ix1):
        return 'edge-s'
    if x == rx0 or (x == ix1 + 1 and iy0 <= y <= iy1):
        return 'edge-w'
    if x == rx1 or (x == ix0 - 1 and iy0 <= y <= iy1):
        return 'edge-e'
    return 'center'


for x, y in rect(*RIVER):
    if ix0 <= x <= ix1 and iy0 <= y <= iy1:
        continue
    b.put('Water', x, y, f'pond-autotile_{bank(x, y)}')
    if x not in AXIS or y >= iy0:
        b.solid(x, y)                                             # the bridge is the only way over
for x, y in ((ix0 - 1, iy0 - 1), (ix1, iy0 - 1), (ix0 - 1, iy1), (ix1, iy1)):
    b.stamp('okayama-bank-rock', x, y)                            # 2x2, over each corner of the island

# ---- Korakuen ------------------------------------------------------------------------------
b.autotile('gravel-autotile',
           rect(BRIDGE[0], BRIDGE[1], BRIDGE[0] + 1, 29)          # under the bridge, and in from its landing
           + rect(9, 28, 36, 29) + rect(9, 28, 10, 34) + rect(9, 33, 36, 34) + rect(35, 28, 36, 34))   # the loop
b.stamp('okayama-bridge', *BRIDGE)
b.pond(*POND)
k.trees('sendai-maple', [(12, 31), (31, 31), (25, 32)])
k.trees('sendai-pine', [(7, 28), (37, 28), (22, 32), (7, 35), (37, 35)])
for x, y in ((28, 31), (30, 32)):                                 # feet: the cranes on the lawn
    b.stamp('okayama-crane', x, y - 1)
for x, y in ((20, 27), (23, 27), (33, 31)):                       # feet: two of them flank the bridge's landing
    b.stamp('sendai-stone-lantern', x, y - 1)

# ---- the fingerpost by the seam ------------------------------------------------------------
b.stamp('okayama-fingerpost', 39, AVE1)                           # feet on (39, 23), beside the pavement

# ---- closed all round, but for the avenue into Himeji ----------------------------------------
for x in (W - 2, W - 1):
    b.stamp('shrub-small', x, AVE1 + 1)                           # the verge south of the avenue, at the seam
k.woods(0, 0, W - 1, 1, AUTUMN, rng)                              # behind the keep
k.woods(0, 2, 12, 14, AUTUMN, rng)                                # west of the terrace
k.woods(0, 15, 4, H - 1, AUTUMN, rng)                             # the west edge: nothing is planned beyond it
k.woods(W - 3, 2, W - 1, AVE0 - 1, AUTUMN, rng)                   # east of the terrace
k.woods(W - 3, 24, W - 1, H - 1, AUTUMN, rng)                     # east of the river
k.woods(5, 38, 40, H - 1, AUTUMN, rng)                            # south of it
k.plants(rng, 18, 11, 30, 34, 32)                                 # the garden's lawn
k.plants(rng, 6, 13, 15, 40, 17); k.plants(rng, 5, 13, 23, 40, 23)    # the verges

# ---- write ----------------------------------------------------------------------------------
prev = cfg['rooms'].get('Okayama', {})
k.dress()
b.finish()
cfg['rooms']['Okayama'] = b.room('Okayama', npcs=prev.get('npcs', []),
                                 transporters=rg.kept_order(prev, ks.seams('Okayama')))
rg.save_config(cfg)
print(f'Okayama: {W}x{H}, {len(cfg["rooms"]["Okayama"]["npcs"])} NPCs kept; the keep at {KEEP}, the bridge at {BRIDGE}')
