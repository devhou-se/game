#!/usr/bin/env python3
"""generate_himeji.py — "Himeji", the castle town west of Osaka (issue #255; #68, run 2).

devhouse 2's Damian was here on 13 November 2025 (post 754: the castle, then
Koko-en beside it). It is a small district of the stitched `KansaiCity`
(tools/kansai.py has the layout) with NO station: you walk in from Osaka along
Canal-side Avenue (east edge, rows 18-22), and on out of its west edge along
the same avenue to Okayama (issue #267; `ks.is_open('Himeji', 'w')`, and the
edge is woods wherever that is False).

  north   HIMEJI CASTLE on its hill, climbed as a hairpin through three
          sand courts (the Kansai plan, #275). Over the bridge and through the
          GATEHOUSE in the white wall (over its stone base) into SANNOMARU, the
          lower court; east to the steps in the inner stone wall (rows 4-5,
          columns 38-39); back west along the UPPER WALK under the woods; down
          the lane on the keep's east flank into HONMARU, the court in front of
          the keep. The corner turret stands against the inner wall and closes
          Honmaru from Sannomaru, so the keep is reached only the long way round
  moat    Osaka's canal runs on west as the castle moat (rows 14-16) and ends
          at a bank; a timber bridge crosses it to the gate. It is declared in
          `waterways`, so the canal's boats sail it
  avenue  Canal-side Avenue carries on from Osaka and out west to Okayama; a
          fingerpost stands by each seam
  south   KOKO-EN: the walled garden, entered through its roofed gate at the
          Okayama end. Three rooms in a row, parted by north-south earthen
          walls whose openings are staggered: pines and lanterns, then the koi
          pond under a timber bridge, then maples. Its paths are stepping stones

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
WEST = ks.is_open('Himeji', 'w')                  # the avenue runs on to Okayama
MOAT0, MOAT1 = ks.H_MOAT                          # the moat: rows 14-16
BRIDGE = (32, MOAT0)                              # 2x4: the deck's columns 32-33, landing on row 17
GATE = (30, 10)                                   # 6x4: the gateway is columns 32-33
KEEP = (8, 0)                                     # 10x8, on the district's top row
TURRET = (20, 6)                                  # 3x4, against the inner wall: closes Honmaru from Sannomaru
INNER = 4                                         # the inner stone wall: rows 4-5
STEPS = (38, 39)                                  # its steps, the only way up to the upper walk
KOKOEN_GATE = (8, 23)                             # 4x3: the gateway is columns 9-10
GARDEN0, GARDEN1 = 26, 37                         # Koko-en's rows, inside the row-24 wall
GARDEN_WALLS = {5: (), 18: (28, 29), 31: (34, 35), 41: ()}    # its north-south walls: column -> the opening's rows
POND = (21, 30, 28, 32)                           # Koko-en's koi pond: x0, y0, x1, y1
POND_BRIDGE = (24, 30)                            # 2x4, north to south over the pond
PINES = ['sendai-pine', 'sendai-cedar', 'sendai-pine']

b.fill('grass-autotile')

# ---- Canal-side Avenue, in from Osaka ------------------------------------------------
b.autotile('flat-grey-brick-autotile', rect(0 if WEST else 5, AVE0, W - 1, AVE1))
for x in (W - 1,) + ((0,) if WEST else ()):
    b.put('Floor', x, AVE0, 'flat-grey-brick-autotile_edge-n')    # the pavement runs on into Osaka (and
    b.put('Floor', x, AVE1, 'flat-grey-brick-autotile_edge-s')    # Okayama): no rounded corner at a seam
k.road_h(0 if WEST else 6, W - 1, AVE0 + 1, cap_w=not WEST)

# ---- the ground of the castle hill -----------------------------------------------------
# Laid before the walls and the paving, so that what shows under and between the
# wall tiers is the courts' sand and nothing green.
b.autotile('sand-autotile',
           rect(6, 8, 41, 13) + rect(18, 2, 41, 7)                # Honmaru and Sannomaru, the upper walk, the lane
           + rect(BRIDGE[0], MOAT0, BRIDGE[0] + 1, MOAT1 + 1))    # under the bridge, to its landing on row 17

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
for x in range(TURRET[0], 42):                                    # the inner wall: Sannomaru below it, the
    if x not in STEPS:                                            # upper walk above
        b.wall_stone(x, INNER)
k.paved(rect(STEPS[0], INNER, STEPS[1], INNER + 1))
for x, y in rect(STEPS[0], INNER, STEPS[1], INNER + 1):
    b.stairs(x, y)

# ---- the courts: the keep, the turret, pines and lanterns -------------------------------
b.stamp('himeji-keep', *KEEP)
k.solid_rect(KEEP[0], KEEP[1], KEEP[0] + 9, KEEP[1] + 7)          # its roof rows too: nobody walks in behind it
b.stamp('himeji-turret', *TURRET)
k.solid_rect(TURRET[0], TURRET[1], TURRET[0] + 2, TURRET[1] + 3)  # rows 6-9: from the inner wall to the white wall
# None of these on (9..16, 8..9): whoever the blog pipeline stands in front of the
# keep is there, and so is whoever walks up to talk to them.
k.trees('sendai-pine', [(24, 7), (27, 9), (40, 3)])
for x, y in ((36, 7), (41, 7), (6, 9), (18, 9)):                  # feet
    b.stamp('sendai-stone-lantern', x, y - 1)

# ---- Koko-en, south of the avenue --------------------------------------------------------
k.wall(5, KOKOEN_GATE[0] - 1, 24); k.wall(KOKOEN_GATE[0] + 4, 41, 24)
b.stamp('himeji-kokoen-gate', *KOKOEN_GATE)
k.paved(rect(KOKOEN_GATE[0] + 1, 24, KOKOEN_GATE[0] + 2, 25))     # the gateway
for x, gap in GARDEN_WALLS.items():                               # the north-south walls, in runs either side of
    rows = [y for y in range(GARDEN0, GARDEN1 + 1) if y not in gap]   # their opening
    runs = [[rows[0]]]
    for y in rows[1:]:
        if y == runs[-1][-1] + 1:
            runs[-1].append(y)
        else:
            runs.append([y])
    for run in runs:
        y0, y1 = run[0], run[-1]
        for y in range(y0, y1 - 1):
            b.prop('himeji-kokoen-wall-v-top_0_0' if y == y0 and y0 > GARDEN0 else 'himeji-kokoen-wall-v_0_0', x, y)
        b.prop('himeji-kokoen-wall-v-end_0_0', x, y1 - 1, 1, 2)   # its south end, where its end face shows
for i, (x, y) in enumerate([(10, y) for y in range(26, 34)] + [(x, 28) for x in range(11, 25)] + [(24, 29)]
                           + [(x, 33) for x in range(11, 15)] + [(25, 34)] + [(x, 34) for x in range(26, 37)]
                           + [(36, y) for y in range(29, 34)]):
    b.paver(x, y, i)                                              # the stepping stones, room to room
px0, py0, px1, py1 = POND                                         # three rows: b.pond makes two
for x, y in rect(px0, py0, px1, py1):
    ns = 'n' if y == py0 else 's' if y == py1 else ''
    we = 'w' if x == px0 else 'e' if x == px1 else ''
    role = f'corner-{ns}{we}' if ns and we else f'edge-{ns or we}' if ns or we else 'center'
    b.put('Water', x, y, f'pond-autotile_{role}')
    if x not in (POND_BRIDGE[0], POND_BRIDGE[0] + 1):
        b.solid(x, y)                                             # the bridge's deck is walked on
b.stamp('himeji-bridge', *POND_BRIDGE)
k.trees('sendai-pine', [(7, 31), (14, 31), (12, 36), (15, 27), (20, 36), (28, 28)])   # rooms A and B
k.trees('sendai-maple', [(33, 29), (38, 31), (33, 37), (38, 36), (38, 27)])           # room C
for x, y in ((8, 27), (12, 29), (15, 33), (22, 29), (29, 33), (35, 28)):              # feet
    b.stamp('sendai-stone-lantern', x, y - 1)

# ---- the fingerpost by the seam ----------------------------------------------------------
b.stamp('kansai-fingerpost', 39, AVE1)                            # feet on (39, 23), beside the pavement

# ---- closed all round, but for the avenue into Osaka and on to Okayama ---------------------
k.woods(0, 0, 7, 7, PINES, rng)                                   # behind and beside the keep
k.woods(0, 8, 5, AVE0 - 1, PINES, rng)                            # the hill's west flank, the moat's bank
if WEST:
    b.stamp('okayama-fingerpost', 4, AVE1)                        # feet on (4, 23): the one for the west seam
    for x in (0, 1):
        b.stamp('shrub-small', x, AVE1 + 1)                       # the verge south of the avenue, at the seam
    k.woods(0, AVE1 + 2, 4, H - 1, PINES, rng)                    # west of the garden
else:
    k.woods(0, AVE0, 4, H - 1, PINES, rng)                        # the end of the avenue, west of the garden
k.woods(18, 0, W - 1, 1, PINES, rng)                              # behind the upper walk
k.woods(W - 2, 2, W - 1, 13, PINES, rng)                          # east of the courts
for y in (MOAT1 + 1, AVE1 + 1):                                   # the verges either side of the avenue
    for x in (W - 2, W - 1):
        b.stamp('shrub-small', x, y)
k.woods(W - 2, 24, W - 1, H - 1, PINES, rng)                      # east of the garden's wall
k.woods(5, GARDEN1 + 1, 41, H - 1, PINES, rng)                    # south of it
k.plants(rng, 16, 6, GARDEN0, 40, GARDEN1)                        # the garden's lawn
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
