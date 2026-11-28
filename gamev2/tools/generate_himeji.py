#!/usr/bin/env python3
"""generate_himeji.py — "Himeji", the castle town west of Osaka (issue #255; #68, run 2).

devhouse 2's Damian was here on 13 November 2025 (post 754: the castle, then
Koko-en beside it). It is a small district of the stitched `KansaiCity`
(tools/kansai.py has the layout) with NO station: you walk in from Osaka along
Canal-side Avenue (east edge, rows 18-22). Its west edge is closed until
Okayama is built (`ks.is_open('Himeji', 'w')`).

  north   HIMEJI CASTLE on its hill: the white keep on the district's top row,
          a corner turret, a gravel terrace with pines and stone lanterns. Two
          wall tiers hold the hill up - the castle's white plaster wall over a
          stone base - and the only way up is the GATEHOUSE: over the bridge,
          through the gateway, up the steps
  moat    Osaka's canal runs on west as the castle moat (rows 14-16) and ends
          at a bank; a timber bridge crosses it to the gate. It is declared in
          `waterways`, so the canal's boats sail it
  avenue  Canal-side Avenue carries on from Osaka and ends at the woods; a
          fingerpost stands by the seam
  south   KOKO-EN: the walled strolling garden, through its roofed gate - a
          gravel loop round a pond with a bridge, lanterns, pines and maples

Nobody gets lost behind anything: the keep and the turret are solid over their
whole footprint, and the woods round the district are solid throughout. There
is no building with a door here: the keep is looked at, not entered.

Art is drawn by tools/generate_kansai_art.py. Deterministic and idempotent:
rebuilds rooms.Himeji from scratch each run, keeping any NPCs the blog pipeline
has placed there. The build order for the whole region is in
docs/landmarks-and-towns.md ("Kansai").

Run from gamev2/:  python3 tools/generate_himeji.py
"""
import random
import roomgen as rg
from roomgen import rect
import kansai as ks

cfg = rg.load_config()

W, H = ks.SIZE['Himeji']
b = rg.Builder(W, H)
k = ks.Kit(b)
rng = random.Random(2551)

AVE0, AVE1 = ks.H_AVENUE[0], ks.H_AVENUE[-1]      # Canal-side Avenue: rows 18-22
MOAT0, MOAT1 = ks.H_MOAT                          # the moat: rows 14-16
BRIDGE = (32, MOAT0)                              # 2x4: the deck's columns 32-33, landing on row 17
GATE = (30, 10)                                   # 6x4: the gateway is columns 32-33
KEEP = (8, 0)                                     # 10x8, on the district's top row
TURRET = (38, 3)                                  # 3x4
KOKOEN_GATE = (20, 23)                            # 4x3: the gateway is columns 21-22
POND = (13, 31, 33)                               # Koko-en's pond: x0, its first row, x1
POND_BRIDGE = (22, 30)                            # 2x4, north to south over the pond
AUTUMN = ['sendai-maple', 'sendai-pine', 'sendai-cedar', 'sendai-maple', 'sendai-pine']
GARDEN = ['sendai-maple', 'sendai-pine', 'sendai-maple']

b.fill('grass-autotile')

# ---- Canal-side Avenue, in from Osaka ------------------------------------------------
b.autotile('flat-grey-brick-autotile', rect(5, AVE0, W - 1, AVE1))
b.put('Floor', W - 1, AVE0, 'flat-grey-brick-autotile_edge-n')    # the pavement runs on into Osaka:
b.put('Floor', W - 1, AVE1, 'flat-grey-brick-autotile_edge-s')    # no rounded corner at the seam
k.road_h(6, W - 1, AVE0 + 1, cap_w=True)

# ---- the ground of the castle hill and of the garden ---------------------------------
# Laid before the walls and the paving, so that what shows under and between the
# two wall tiers is the terrace's gravel and nothing green.
b.autotile('gravel-autotile',
           rect(6, 8, 41, 13) + rect(18, 2, 41, 7)                # the terrace: in front of the keep, and east of it
           + rect(BRIDGE[0], MOAT0, BRIDGE[0] + 1, MOAT1 + 1))    # under the bridge, to its landing on row 17
b.autotile('gravel-autotile',
           rect(21, 24, 22, 26)                                   # in through Koko-en's gate
           + rect(8, 27, 38, 28) + rect(8, 27, 9, 35) + rect(8, 34, 38, 35) + rect(37, 27, 38, 35)   # the loop
           + rect(POND_BRIDGE[0], 29, POND_BRIDGE[0] + 1, 33))    # and across the pond by its bridge

# ---- the moat: Osaka's canal, ending at a bank ----------------------------------------
for x in range(6, W):
    for y, role in zip(range(MOAT0, MOAT1 + 1), (('corner-nw', 'edge-w', 'corner-sw') if x == 6 else
                                                 ('edge-n', 'center', 'edge-s'))):
        b.put('Water', x, y, f'pond-autotile_{role}')
        if x not in (BRIDGE[0], BRIDGE[0] + 1):
            b.solid(x, y)                                         # the bridge is the only way over
b.stamp('himeji-bridge', *BRIDGE)

# ---- the walls of the hill and the gatehouse -------------------------------------------
for x in range(6, 42):
    if not GATE[0] <= x < GATE[0] + 6:
        b.stamp('himeji-wall', x, 10)                             # the white wall, rows 10-11
        b.wall_stone(x, 12)                                       # on its stone base, rows 12-13
b.stamp('himeji-gate', *GATE)
k.paved(rect(BRIDGE[0], 10, BRIDGE[0] + 1, 13))                   # the gateway: the only way up
for x, y in rect(BRIDGE[0], 10, BRIDGE[0] + 1, 12):
    b.stairs(x, y)

# ---- the terrace: the keep, the turret, pines and lanterns -----------------------------
b.stamp('himeji-keep', *KEEP)
k.solid_rect(KEEP[0], KEEP[1], KEEP[0] + 9, KEEP[1] + 7)          # its roof rows too: nobody walks in behind it
b.stamp('himeji-turret', *TURRET)
k.solid_rect(TURRET[0], TURRET[1], TURRET[0] + 2, TURRET[1] + 3)
# None of these on (9..16, 8..9): whoever the blog pipeline stands in front of the
# keep is there, and so is whoever walks up to talk to them.
k.trees('sendai-pine', [(20, 4), (26, 3), (34, 4), (40, 9)])
for x, y in ((23, 7), (29, 7), (36, 7)):                          # top cells: their feet are on row 8
    b.stamp('sendai-stone-lantern', x, y)

# ---- Koko-en, south of the avenue --------------------------------------------------------
k.wall(5, KOKOEN_GATE[0] - 1, 24); k.wall(KOKOEN_GATE[0] + 4, 41, 24)
b.stamp('himeji-kokoen-gate', *KOKOEN_GATE)
b.pond(*POND)
b.stamp('himeji-bridge', *POND_BRIDGE)
for x, y in rect(POND_BRIDGE[0], POND[1], POND_BRIDGE[0] + 1, POND[1] + 1):
    del b.L['Colliders'][f'{x},{y}']                              # the deck is walked on
k.trees('sendai-maple', [(16, 30), (34, 30), (27, 33)])
k.trees('sendai-pine', [(11, 32), (30, 30), (18, 33)])
for x, y in ((12, 29), (34, 32), (19, 26), (24, 26)):             # feet: two of them flank the gate, inside
    b.stamp('sendai-stone-lantern', x, y - 1)

# ---- the fingerpost by the seam ----------------------------------------------------------
b.stamp('kansai-fingerpost', 39, AVE1)                            # feet on (39, 23), beside the pavement

# ---- closed all round, but for the avenue into Osaka ---------------------------------------
if not ks.is_open('Himeji', 'w'):                                 # until Okayama is built
    k.woods(0, 0, 7, 7, AUTUMN, rng)                              # behind and beside the keep
    k.woods(0, 8, 5, AVE0 - 1, AUTUMN, rng)                       # the hill's west flank, the moat's bank
    k.woods(0, AVE0, 4, H - 1, AUTUMN, rng)                       # the end of the avenue, west of the garden
k.woods(18, 0, W - 1, 1, AUTUMN, rng)                             # behind the terrace
k.woods(W - 2, 2, W - 1, 13, AUTUMN, rng)                         # east of it
for y in (MOAT1 + 1, AVE1 + 1):                                   # the verges either side of the avenue
    for x in (W - 2, W - 1):
        b.stamp('shrub-small', x, y)
k.woods(W - 2, 24, W - 1, H - 1, AUTUMN, rng)                     # east of the garden's wall
k.woods(5, 26, 6, 35, GARDEN, rng)                                # round the garden, inside the wall
k.woods(40, 26, 41, 35, GARDEN, rng)
k.woods(5, 36, 41, H - 1, AUTUMN, rng)
k.plants(rng, 16, 10, 29, 36, 33)                                 # the garden's lawn
k.plants(rng, 8, 6, 17, 41, 17); k.plants(rng, 8, 5, 23, 41, 23)  # the verges

# ---- write ----------------------------------------------------------------------------------
prev = cfg['rooms'].get('Himeji', {})
k.dress()
b.finish()
cfg['rooms']['Himeji'] = b.room('Himeji', npcs=prev.get('npcs', []),
                                transporters=rg.kept_order(prev, ks.seams('Himeji')))
# The moat is the west end of Osaka's canal (docs/ambient-traffic.md): the same
# three rows, declared from the first cell with open water either side of the
# hull (x = 7: the bank column gives no band, and a run with none is dropped),
# so that in the stitched city the two runs meet and sail as one.
cfg['rooms']['Himeji']['waterways'] = [
    {'axis': 'h', 'row': MOAT0, 'rows': MOAT1 - MOAT0 + 1, 'from': 7, 'to': W - 1,
     'under': [[BRIDGE[0], BRIDGE[0] + 1]]},
]
rg.save_config(cfg)
print(f'Himeji: {W}x{H}, {len(cfg["rooms"]["Himeji"]["npcs"])} NPCs kept; the keep at {KEEP}, the gate at {GATE}')
