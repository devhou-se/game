#!/usr/bin/env python3
"""generate_nara.py — "Nara", the Great Buddha Hall, the deer and Kasuga Taisha, east of Osaka (issue #268; #68, run 5).

devhouse 2's Damian was here on 14 November 2025 (post 764: the day trip to
Nara, the Great Buddha, the deer). It is the eastern district of the stitched
`KansaiCity` (tools/kansai.py has the layout) with NO station: you walk in from
Osaka along the avenue (west edge, rows 18-22). Its north edge opens with Lake
Biwa (`ks.is_open('Nara', 'n')`); until then it is woods. Its east and south
edges are closed: nothing is planned beyond them.

Todaiji is laid out on one north-south axis (columns 36-37): the hall, its
gravel court, the gate, the plaza.

  north   TODAIJI: the GREAT BUDDHA HALL over its gravel court, behind an
          earthen wall crossed only through the NANDAIMON gate on the axis.
          Rows 0-1 behind the hall are wood
  west    Osaka's canal runs on as a RIVER (rows 14-16) that bends north up
          columns 20-22, with a gravel TOWPATH beside it (23-24) up to where
          Lake Biwa will join. It is declared in `waterways` as far as the
          bend, so the canal's boats sail it
  avenue  the avenue in from Osaka ends in a paved PLAZA below the gate: a
          stall of deer crackers, deer bowing for them. A fingerpost stands by
          the seam
  south   NARA PARK's lawn, maples and pines, deer resting on the grass; and
          KASUGA TAISHA: through a vermilion torii, up an approach lined with
          stone lanterns round a cedar wood, to the shrine (`shrine-red`, whose
          door tools/generate_shrines.py wires to its worship hall)

The river is `pond-autotile`, solid throughout. The set has no inner-corner
piece, so a heap of the rim's stones (`okayama-bank-rock`) lies over the inside
of the bend; while the north is closed the river ends in a round east corner
with another heap over its west one (not `corner-nw`, which the blog pipeline
would read as a pond of its own).

Nobody gets lost behind anything: the hall is solid over its whole footprint,
roof rows and all, the woods round the district are solid throughout, and a
lantern closes the one cell behind the shrine's roof. There is no building
with a door here but the shrine: the hall and the gate are looked at.

Art is drawn by tools/generate_kansai_art.py (the two resting deer are cut from
the UrbanAccessoriesv2 sheet by tools/extract_street.py). Deterministic and
idempotent: rebuilds rooms.Nara from scratch each run, keeping any NPCs the
blog pipeline has placed there and the shrine's door. The build order for the
whole region is in docs/landmarks-and-towns.md ("Kansai").

Run from gamev2/:  python3 tools/generate_nara.py
"""
import random
import roomgen as rg
from roomgen import rect
import kansai as ks

cfg = rg.load_config()

W, H = ks.SIZE['Nara']
b = rg.Builder(W, H)
k = ks.Kit(b)
rng = random.Random(268)

AVE0, AVE1 = ks.N_AVENUE[0], ks.N_AVENUE[-1]      # the avenue in from Osaka: rows 18-22
RIV0, RIV1 = ks.N_RIVER                           # the river in from Osaka: rows 14-16
BX0, BX1 = ks.N_BEND                              # the columns it turns north up: 20-22
TX0, TX1 = ks.N_TOWPATH                           # the towpath beside it: 23-24
NORTH = ks.is_open('Nara', 'n')                   # the towpath runs on to Lake Biwa
TOP = 0 if NORTH else 2                           # the river's and the towpath's first row
HALL = (31, 2)                                    # 12x8: rows 0-1 behind it are wood
GATE = (34, 12)                                   # 6x4: the gateway is columns 36-37
TORII = (31, 24)                                  # 4x4: walked through on columns 32-33
SHRINE = (42, 24)                                 # shrine-red: the door (44, 30), its front (44, 31)
AUTUMN = ['sendai-maple', 'sendai-pine', 'sendai-cedar', 'sendai-maple', 'sendai-pine']
CEDARS = ['sendai-cedar', 'sendai-cedar', 'sendai-pine']

b.fill('grass-autotile')

# ---- the avenue, in from Osaka, and the plaza it ends in ---------------------------------
b.autotile('flat-grey-brick-autotile', rect(0, AVE0, 42, AVE1) + rect(31, 16, 42, 23))
b.put('Floor', 0, AVE0, 'flat-grey-brick-autotile_edge-n')        # the pavement runs on into Osaka:
b.put('Floor', 0, AVE1, 'flat-grey-brick-autotile_edge-s')        # no rounded corner at the seam
k.road_h(0, 29, AVE0 + 1, cap_e=True)


# ---- the river, in from Osaka's canal and bending north --------------------------------
def bank(x, y):
    """The pond piece of a cell of the river: rimmed on the side its bank is."""
    if y >= RIV0:
        if (x, y) == (BX1, RIV1):
            return 'corner-se'
        if x == BX1:
            return 'edge-e'
        if y == RIV1:
            return 'edge-s'
        return 'edge-n' if y == RIV0 and x < BX0 else 'center'
    if y == TOP and not NORTH:                                    # the closed head, until Lake Biwa
        return 'corner-ne' if x == BX1 else 'edge-n'
    return {BX0: 'edge-w', BX1: 'edge-e'}.get(x, 'center')


for x, y in rect(0, RIV0, BX1, RIV1) + rect(BX0, TOP, BX1, RIV0 - 1):
    b.put('Water', x, y, f'pond-autotile_{bank(x, y)}')
    b.solid(x, y)
b.stamp('okayama-bank-rock', BX0 - 1, RIV0 - 1)                   # 2x2, over the inside of the bend
if not NORTH:
    b.stamp('okayama-bank-rock', BX0 - 1, TOP - 1)                # ...and over the closed head's west corner

# ---- the towpath, up the river's east bank ----------------------------------------------
b.autotile('gravel-autotile', rect(TX0, TOP, TX1, AVE0 - 1))      # it meets the avenue's pavement at row 18

# ---- Todaiji: the court, the hall, the wall and the Nandaimon ----------------------------
b.autotile('gravel-autotile', rect(28, 10, 45, 13) + rect(36, 13, 37, 15))
b.stamp('nara-daibutsuden', *HALL)
k.solid_rect(HALL[0], HALL[1], HALL[0] + 11, HALL[1] + 7)        # its roof rows too: nobody walks in behind it
k.wall(25, 33, 14)                                                # rows 14-15, either side of the gate
k.wall(40, 46, 14)
b.stamp('nara-nandaimon', *GATE)

# ---- the plaza: the deer cracker stall ------------------------------------------------------
b.stamp('nara-senbei-stall', 41, 16)                              # bumped from row 18 and column 40

# ---- Kasuga Taisha: the torii, the approach round the cedar wood, the shrine --------------
b.autotile('gravel-autotile', rect(32, 24, 33, 36) + rect(32, 35, 45, 36) + rect(44, 31, 45, 36))
b.stamp('nara-kasuga-torii', *TORII)
b.stamp('shrine-red', *SHRINE)
# feet: either side of the approach; the last stands at the plaza's south-east corner
# and closes the one cell behind the shrine's roof (42, 24)
for x, y in ((31, 29), (31, 31), (31, 33), (34, 29), (34, 31), (34, 33), (36, 34), (38, 34), (40, 34),
             (34, 37), (36, 37), (38, 37), (40, 37), (42, 37), (43, 32), (46, 32), (43, 34), (46, 34), (42, 24)):
    b.stamp('nara-stone-lantern', x, y - 1)

# ---- the deer: resting on the lawn and the court, bowing on the plaza and the pavement ------
# (the first stag in "x,y" order, (12, 29), is where blog_to_npc.py's LANDMARKS row anchors)
for x, y in ((8, 26), (17, 30), (25, 27), (30, 12), (26, 17)):
    b.stamp('nara-deer-doe', x, y)
for x, y in ((12, 29), (22, 25), (43, 11), (25, 8)):
    b.stamp('nara-deer-stag', x, y)
for x, y in ((40, 17), (33, 17), (19, 23)):
    b.stamp('nara-deer-bow', x, y)

# ---- Nara Park's lawn ------------------------------------------------------------------------
k.trees('sendai-maple', [(6, 31), (14, 26), (27, 31)])
k.trees('sendai-pine', [(10, 33), (20, 28), (24, 32)])

# ---- the fingerpost by the seam --------------------------------------------------------------
b.stamp('nara-fingerpost', 3, AVE1)                               # feet on (3, 23), beside the pavement

# ---- closed all round, but for the avenue into Osaka (and the towpath, once Lake Biwa is built) --
for x, y in ((0, AVE0 - 1), (1, AVE0 - 1), (0, AVE1 + 1), (1, AVE1 + 1)):
    b.stamp('shrub-small', x, y)                                  # the verges either side of the avenue, at the seam
k.woods(0, 0, BX0 - 1, RIV0 - 1, AUTUMN, rng)                     # west of the river
if not NORTH:
    k.woods(BX0, 0, TX1, TOP - 1, AUTUMN, rng)                    # above the river's head and the towpath's end
k.woods(25, 0, W - 1, 1, AUTUMN, rng)                             # behind the hall
k.woods(25, 2, 30, 9, AUTUMN, rng)                                # west of it
k.woods(25, 10, 27, 13, AUTUMN, rng)                              # ...and of the court
k.woods(43, 2, W - 1, 9, AUTUMN, rng)                             # east of the hall
k.woods(46, 10, W - 1, 13, AUTUMN, rng)                           # ...and of the court
k.woods(47, 14, W - 1, H - 1, CEDARS, rng)                        # the east edge: nothing is planned beyond it
k.woods(43, 21, 46, 25, CEDARS, rng)                              # east of the plaza, round the shrine's roof
k.woods(35, 24, 41, 33, CEDARS, rng)                              # the wood the approach goes round
k.woods(0, 24, 3, H - 1, AUTUMN, rng)                             # the west edge, south of the avenue
k.woods(4, 34, 30, H - 1, AUTUMN, rng)                            # south of the lawn
k.woods(31, 38, 46, H - 1, CEDARS, rng)                           # south of the approach
k.plants(rng, 26, 4, 24, 29, 33)                                  # the lawn
k.plants(rng, 8, 2, 17, 22, 17); k.plants(rng, 6, 25, 16, 30, 17)    # the verges north of the avenue

# ---- write ----------------------------------------------------------------------------------
prev = cfg['rooms'].get('Nara', {})
k.dress()
b.finish()
cfg['rooms']['Nara'] = b.room('Nara', npcs=prev.get('npcs', []),
                              transporters=rg.kept_order(prev, ks.seams('Nara')))
# the river is navigable from Osaka's canal as far as the bend (src/AmbientBoats.js): cells, inclusive
cfg['rooms']['Nara']['waterways'] = [{'axis': 'h', 'row': RIV0, 'rows': RIV1 - RIV0 + 1, 'from': 0, 'to': BX0 - 1}]
rg.save_config(cfg)
print(f'Nara: {W}x{H}, {len(cfg["rooms"]["Nara"]["npcs"])} NPCs kept; the hall at {HALL}, the gate at {GATE}, '
      f'the shrine at {SHRINE}')
