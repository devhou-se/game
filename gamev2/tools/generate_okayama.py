#!/usr/bin/env python3
"""generate_okayama.py — "Okayama", the black castle and Korakuen, west of Himeji (issue #267; #68, run 4).

devhouse 2's Damian was here on 12 November 2025 (post 745: Hakata to Okayama,
Korakuen, the castle, Bizen ware). It is the westernmost district of the
stitched `KansaiCity` (tools/kansai.py has the layout) with NO station: you
walk in from Himeji along the avenue (east edge, rows 18-22). Its own west edge
is closed: nothing is planned beyond it.

It is a stroll (issue #276; the plan is "Kansai: one plan for Osaka, Himeji
and Okayama" in docs/landmarks-and-towns.md): the road runs ten cells in from
Himeji and stops at a plaza on a river that bends through the room.

  east    the avenue in from Himeji ends in a paved PLAZA on the river's east
          bank: the bronze MOMOTARO with his dog, monkey and pheasant, and a
          stall of BIZEN WARE. A fingerpost stands by the seam
  north   OKAYAMA CASTLE, the black "crow castle", stands low at the water on
          the north bank, beside a small gravel court that opens onto the plaza
  south   KORAKUEN is the inside of the bend, reached only over the TSUKIMI
          BRIDGE beside the keep: open lawn, one cranked gravel path, the hill
          Yuishinzan, a pond, two red-crowned cranes, and the castle across the
          water

The river is one bend of `pond-autotile`: in at the west edge on rows 19-21,
east to columns 29-32, then south out of the bottom edge. It is solid but for
the bridge's two columns. The set has no inner-corner piece, so a heap of the
rim's own stones (`okayama-bank-rock`) lies over the bend's one inner corner, at
the garden's tip. The river has no `corner-nw`: the garden pond's is the room's
only one. Nothing sails it, so it is not a `waterways` run.

Nobody gets lost behind anything: the keep and the hill are solid over their
whole footprints, roof rows and all, and the woods round the district are solid
throughout. There is no building with a door here: the keep is looked at, from
the garden's bank across the river, not entered, and the stall is an open
counter.

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
PLAZA = (34, 14, 40, AVE1)                        # where the avenue ends, on the east bank
REACH = (0, 19, 32, 21)                           # the river: in at the west edge, east to the bend...
BEND = (29, 22, 32, H - 1)                        # ...and south out of the bottom edge
KEEP = (14, 12)                                   # 8x7: its stone base stands on the north bank, row 18
COURT = (22, 14, 33, 18)                          # the gravel court beside it
BRIDGE = (22, REACH[1])                           # 2x4: the Tsukimi bridge, beside the keep, landing on row 22
GARDEN = (3, 22, 28, 37)                          # Korakuen: the inside of the bend
MOUND = (4, 25)                                   # 5x4: Yuishinzan
POND = (6, 32, 13, 35)                            # the garden's pond
PATH = rect(22, 22, 23, 25) + rect(10, 24, 23, 25) + rect(10, 24, 11, 31)    # from the landing: south, west, south to the pond
AUTUMN = ['sendai-maple', 'sendai-cedar', 'sendai-maple']

b.fill('grass-autotile')

# ---- the avenue, in from Himeji, and the plaza it ends in -----------------------------
b.autotile('flat-grey-brick-autotile', rect(PLAZA[0], AVE0, W - 1, AVE1) + rect(*PLAZA))
b.put('Floor', W - 1, AVE0, 'flat-grey-brick-autotile_edge-n')    # the pavement runs on into Himeji:
b.put('Floor', W - 1, AVE1, 'flat-grey-brick-autotile_edge-s')    # no rounded corner at the seam
k.road_h(38, W - 1, AVE0 + 1, cap_w=True)                         # six cells of it, and the road stops
b.stamp('okayama-momotaro', 35, 16)                               # feet on (35..36, 18)
b.stamp('okayama-bizen-stall', 37, 14)                            # bumped from the plaza, row 17
k.solid_rect(37, 14, 39, 14)                                      # its awning's row: nobody walks in behind it

# ---- the river: one bend of water, solid but for the bridge's two columns ---------------
rx0, ry0, rx1, ry1 = REACH
bx0, by0, bx1, by1 = BEND


def bank(x, y):
    """The pond piece of a cell of the river: rimmed on the side its bank is."""
    if (x, y) == (rx1, ry0):
        return 'corner-ne'
    if y == ry0:
        return 'edge-n'
    if x == rx1:
        return 'edge-e'
    if y == ry1 and x < bx0:
        return 'edge-s'
    if x == bx0 and y >= by0:
        return 'edge-w'
    return 'center'


for x, y in rect(*REACH) + rect(*BEND):
    b.put('Water', x, y, f'pond-autotile_{bank(x, y)}')
    if x not in (BRIDGE[0], BRIDGE[0] + 1) or y > ry1:
        b.solid(x, y)                                             # the bridge is the only way over
b.stamp('okayama-bank-rock', bx0 - 1, ry1)                        # 2x2, over the inner corner at the garden's tip

# ---- the north bank: the keep at the water, the court beside it ---------------------------
# One gravel region: the court, under the bridge, and the garden's path from its landing.
b.autotile('gravel-autotile', rect(*COURT) + rect(BRIDGE[0], ry0, BRIDGE[0] + 1, ry1) + PATH)
b.stamp('okayama-keep', *KEEP)
k.solid_rect(KEEP[0], KEEP[1], KEEP[0] + 7, KEEP[1] + 6)          # its roof rows too: nobody walks in behind it
b.stamp('okayama-bridge', *BRIDGE)
k.trees('sendai-pine', [(31, 15)])                                # the court's one pine

# ---- Korakuen: lawn, the path, the mound, the pond, the cranes ----------------------------
b.stamp('okayama-mound', *MOUND)
px0, py0, px1, py1 = POND
for x, y in rect(*POND):
    ns = 'n' if y == py0 else 's' if y == py1 else ''
    we = 'w' if x == px0 else 'e' if x == px1 else ''
    b.put('Water', x, y, 'pond-autotile_' + ('corner-' + ns + we if ns and we else 'edge-' + (ns or we) if ns or we else 'center'))
    b.solid(x, y)
for x, y in ((14, 27), (16, 28)):                                 # feet: the cranes on the lawn
    b.stamp('okayama-crane', x, y - 1)
# None of these on rows 22-23 west of the bridge: that bank is where the keep is looked at from.
k.trees('sendai-maple', [(26, 29), (19, 33), (5, 31)])
k.trees('sendai-cedar', [(26, 36), (23, 36)])
k.trees('sendai-pine', [(15, 35)])                                # the pond's pine
b.stamp('sendai-stone-lantern', 12, 30)                           # feet on (12, 31): where the path meets the pond

# ---- the fingerpost by the seam ------------------------------------------------------------
b.stamp('okayama-fingerpost', 39, AVE1)                           # feet on (39, 23), on the verge

# ---- closed all round, but for the avenue into Himeji ----------------------------------------
for x in (W - 2, W - 1):
    b.stamp('shrub-small', x, AVE1 + 1)                           # the verge south of the avenue, at the seam
k.woods(0, 0, W - 1, KEEP[1] - 1, AUTUMN, rng)                    # the north, behind the keep
k.woods(0, KEEP[1], KEEP[0] - 1, ry0 - 1, AUTUMN, rng)            # west of the keep, down to the river
k.woods(COURT[0], KEEP[1], W - 1, COURT[1] - 1, AUTUMN, rng)      # north of the court and the plaza
k.woods(PLAZA[2] + 1, PLAZA[1], W - 1, AVE0 - 1, AUTUMN, rng)     # east of the plaza, north of the avenue
k.woods(bx1 + 1, AVE1 + 2, W - 1, H - 1, AUTUMN, rng)             # the east bank, south of the avenue
k.woods(0, ry1 + 1, GARDEN[0] - 1, H - 1, AUTUMN, rng)            # the west edge: nothing is planned beyond it
k.woods(GARDEN[0], GARDEN[3] + 1, GARDEN[2], H - 1, AUTUMN, rng)  # south of the garden
k.plants(rng, 22, 12, 26, 28, 37)                                 # the garden's lawn
k.plants(rng, 5, bx1 + 1, AVE1 + 1, 41, AVE1 + 1)                 # the verge

# ---- write ----------------------------------------------------------------------------------
prev = cfg['rooms'].get('Okayama', {})
k.dress()
b.finish()
cfg['rooms']['Okayama'] = b.room('Okayama', npcs=prev.get('npcs', []),
                                 transporters=rg.kept_order(prev, ks.seams('Okayama')))
rg.save_config(cfg)
print(f'Okayama: {W}x{H}, {len(cfg["rooms"]["Okayama"]["npcs"])} NPCs kept; the keep at {KEEP} on the north bank, the Tsukimi bridge at {BRIDGE}')
