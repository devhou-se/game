#!/usr/bin/env python3
"""generate_lakebiwa.py — "Lake Biwa", the lake north of Nara (issue #380; #269, part 1 of 3).

devhouse's Dylan was in Shiga (posts 568, 590, 615, 636 and 681: the cycle round
the lake, Hikone Castle, a hill over the paddies, the tunnel and its monkeys at
Takashima). It is the north-east district of the stitched `KansaiCity`
(tools/kansai.py has the layout) with NO station: you walk in from Nara up the
towpath (south edge, columns 9-10). Its west, north and east edges are closed:
nothing is planned beyond them.

  south   the river from Nara (columns 6-8) widens into the LAKE; the towpath
          beside it reaches the OTSU quay, a paved lakefront with the blue sign
          of the Biwaichi, the cycle path round the lake, and a lawn of pines.
          A fingerpost stands by the seam
  east    the BIWAICHI, a gravel path up the east shore (columns 27-28), with
          two spurs inland:
            HIKONE CASTLE, the white keep on a wooded knoll, reached up one
            flight of stone steps through the pines to a small stone apron
            under it. No wall, no terrace, no moat: the lake is its water
            the HILL VIEWPOINT, a grass hilltop with a picket rail on its brow,
            steps up its west flank, and walkable paddies of harvested stubble
            below it, parted by grass levees into four plots
  north   TAKASHIMA: the path runs west along the shore (rows 4-5) and into a
          TUNNEL mouth; monkeys on the verge, the station's nameboard, and
          Shirahige's TORII standing in the water off the shore

The lake is `pond-autotile`, solid throughout, so the fishing rule answers a
bump into it. Its north-west corner is `edge-n` under a heap of the rim's stones
(`okayama-bank-rock`), as Nara's river does it: `corner-nw` is what the blog
pipeline reads as a pond of its own. Heaps lie over the two inside corners too.

Nobody gets lost behind anything: the keep is solid over all 36 cells, the
woods round the district and the slope under the hill's rail are solid
throughout, and the tunnel is twelve solid cells. There is no building here and
no train track; the bins rule holds.

Art is drawn by tools/generate_lakebiwa_art.py. Deterministic and idempotent:
rebuilds rooms.LakeBiwa from scratch each run, keeping any NPCs the blog
pipeline has placed there. The build order for the whole region is in
docs/landmarks-and-towns.md ("Kansai").

Run from gamev2/:  python3 tools/generate_lakebiwa.py
"""
import random
import roomgen as rg
from roomgen import rect
import kansai as ks

cfg = rg.load_config()

W, H = ks.SIZE['LakeBiwa']
b = rg.Builder(W, H)
k = ks.Kit(b)
rng = random.Random(380)

RX0, RX1 = ks.L_RIVER                             # the river in from Nara: columns 6-8
TX0, TX1 = ks.L_TOWPATH                           # the towpath beside it: 9-10
LAKE, BASIN = (RX0, 7, 24, 22), (RX0, 23, 13, 29)  # the open lake, and the basin by the quay
BX0, BX1 = 27, 28                                 # the Biwaichi up the east shore
KEEP, TUNNEL = (33, 6), (26, 0)                   # 6x6 and 4x3
AX0, AX1 = 35, 36                                 # the castle's steps
HX0, HX1, BROW = 31, 32, 25                       # the hill's steps; the row of its rail
PINES = ['sendai-pine', 'sendai-pine', 'sendai-cedar']
MIXED = ['sendai-pine', 'sendai-cedar', 'sendai-maple', 'sendai-pine']

assert not any(ks.is_open('LakeBiwa', side) for side in 'wne'), \
    'a new join on the west, north or east needs this room rebuilt: its edges there are woods'

b.fill('grass-autotile')

# ---- the lake: the river from Nara widening into it --------------------------------------
water = set(rect(*LAKE) + rect(*BASIN) + rect(RX0, 30, RX1, H - 1))


def bank(x, y):
    """The pond piece of a water cell, from its four neighbours (below the room is the river)."""
    wet = lambda cx, cy: (cx, cy) in water or cy >= H
    n, e, s, w = wet(x, y - 1), wet(x + 1, y), wet(x, y + 1), wet(x - 1, y)
    if not n and not w:
        return 'edge-n'                               # never corner-nw: a heap lies over it
    for role, dry in (('corner-ne', not n and not e), ('corner-se', not s and not e),
                      ('corner-sw', not s and not w), ('edge-n', not n), ('edge-s', not s),
                      ('edge-w', not w), ('edge-e', not e)):
        if dry:
            return role
    return 'center'


for x, y in sorted(water):
    b.put('Water', x, y, f'pond-autotile_{bank(x, y)}')
    b.solid(x, y)
for at in ((5, 6), (13, 22), (8, 29)):
    b.stamp('okayama-bank-rock', *at)                 # the NW corner, the two inside corners
for x, y in ((6, 6), (14, 23), (9, 30)):
    b.solid(x, y)                                     # the land cell under each heap

# ---- the towpath, the Otsu quay and the Biwaichi ---------------------------------------
b.autotile('gravel-autotile', rect(TX0, 32, TX1, H - 1))
b.put('Floor', TX0, H - 1, 'gravel-autotile_edge-w')  # it runs on into Nara:
b.put('Floor', TX1, H - 1, 'gravel-autotile_edge-e')  # no rounded end at the seam
b.autotile('flat-grey-brick-autotile', rect(TX0, 30, 17, 31) + rect(14, 23, 17, 29))
b.stamp('biwa-cycle-sign', 18, 26)
b.stamp('biwa-fingerpost', 11, 31)                    # feet on (11, 32), beside the towpath
b.autotile('gravel-autotile', rect(18, 24, BX1, 25) + rect(BX0, 3, BX1, 29) + rect(6, 4, BX1, 5)
           + rect(29, 18, AX1, 19) + rect(29, 28, HX1, 29))

# ---- Takashima: the tunnel, the station sign, the monkeys, the torii in the water -------
b.stamp('biwa-tunnel', *TUNNEL)
b.stamp('biwa-station-sign', 21, 2)
for at in ((24, 3), (19, 6), (26, 7)):
    b.stamp('biwa-monkey', *at)
b.stamp('biwa-torii', 9, 8)

# ---- Hikone Castle: the keep on its knoll, the apron, one flight of steps ----------------
b.stamp('biwa-hikone-keep', *KEEP)
k.solid_rect(33, 6, 38, 11)                           # its roof rows too: nobody walks in behind it
k.paved(rect(34, 12, 37, 12) + rect(AX0, 13, AX1, 17))
for x, y in rect(AX0, 13, AX1, 17):
    b.stairs(x, y)

# ---- the hill viewpoint: steps up its flank, the rail on its brow, the paddies below -------
k.paved(rect(HX0, BROW, HX1, BROW + 2))
for x, y in rect(HX0, BROW, HX1, BROW + 2):
    b.stairs(x, y)
for i, x in enumerate(range(33, 42)):
    b.fence(x, BROW, i)
k.solid_rect(33, BROW + 1, 41, BROW + 2)              # the slope under the rail
for x, y in rect(30, 28, 43, 33):                     # walkable stubble in four plots, parted by
    if not (x <= HX1 and y <= 29) and x != 37 and y != 31:   # grass levees on column 37 and row 31
        b.put('Floor', x, y, 'biwa-paddy_0_0')
k.trees('sendai-pine', [(39, 22)])

# ---- the lawn by the quay ------------------------------------------------------------------
k.trees('sendai-pine', [(20, 29), (24, 32), (14, 33)])
k.trees('sendai-maple', [(22, 27)])

# ---- closed all round, but for the towpath into Nara ----------------------------------------
k.woods(0, 0, 5, H - 1, MIXED, rng); k.woods(6, 0, 25, 1, MIXED, rng)      # the west shore, the north edge
k.woods(30, 0, W - 1, 5, MIXED, rng); k.woods(29, 3, 29, 5, MIXED, rng)    # behind the castle
k.woods(29, 6, 32, 11, PINES, rng); k.woods(39, 6, W - 1, 11, PINES, rng)  # either side of the keep
k.woods(29, 12, 34, 17, PINES, rng, clear=[(34, 12)])                      # ...of the apron and the flight
k.woods(37, 12, W - 1, 17, PINES, rng, clear=[(37, 12)])
k.woods(37, 18, W - 1, 19, PINES, rng)                                     # east of the castle's spur
k.woods(29, 20, 41, 21, PINES, rng); k.woods(29, 22, 30, 27, PINES, rng)   # the hilltop's back, its west flank
k.woods(42, 20, W - 1, 27, MIXED, rng); k.woods(44, 28, W - 1, H - 1, MIXED, rng)   # its east end, the east edge
k.woods(11, 34, W - 1, H - 1, MIXED, rng)                                  # the south edge
k.plants(rng, 14, 18, 26, 26, 33); k.plants(rng, 8, 6, 2, 20, 3); k.plants(rng, 5, 33, 22, 41, 24)

# ---- write ----------------------------------------------------------------------------------
prev = cfg['rooms'].get('LakeBiwa', {})
k.dress()
b.finish()
cfg['rooms']['LakeBiwa'] = b.room('Lake Biwa', npcs=prev.get('npcs', []),
                                  transporters=rg.kept_order(prev, ks.seams('LakeBiwa')))
cfg['rooms']['LakeBiwa']['sentenceName'] = 'Shiga, by Lake Biwa'
rg.save_config(cfg)
print(f'LakeBiwa: {W}x{H}, {len(cfg["rooms"]["LakeBiwa"]["npcs"])} NPCs kept; the keep at {KEEP}, '
      f'the tunnel at {TUNNEL}')
