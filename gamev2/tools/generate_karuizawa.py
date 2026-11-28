#!/usr/bin/env python3
"""generate_karuizawa.py — "Karuizawa", the mountain resort out of Tokyo's west
gate (issues #68, #256; this is #260, part 1: the room and the gate).

devhouse 2's Damian and Julia were here on 1-2 November 2025. It is the fifth
district of the stitched `TokyoCity`, west of the `Tokyo` room at world cell
(-48, 8), with NO station and no `train-track*` tile: you walk in through
Tokyo's west gate, along the old road out of Edo.

  gate    the east edge, rows 34-35: the same brick as Tokyo's apron, turning
          to a packed-dirt road. It is Tokyo's west gate (Tokyo x=0, rows
          41-42), which e3cb4d0d fenced when Machi was deleted
  post    the fingerpost on the verge just inside the gate: Tokyo one way, the
          road the other (src/utils/Interactions.js has its line)
  road    packed dirt, two cells wide: west from the gate to column 14, then
          north up columns 14-15 to row 10 (parts 2 and 3 line it with the
          shopfronts of Kyu-Karuizawa Ginza)
  head    an open clearing, (10..21, 5..11), where the falls will stand
  woods   everywhere else, solid throughout. They are `tree-green`, Tokyo's
          own tree, until part 2 draws `karuizawa-larch`

Every seam cell carries a hidden transporter to the cell three in from the
neighbour's edge, which is what `?stitch=0` (and `play.js --stitch=0`) plays;
stitched, the transporters are dropped and you just walk.

It also owns one edit to the ported Tokyo map, as generate_palace.py owns its
doors there: the two gate cells go back to plain brick (the fence and its
collider come off) and get their two seam transporters. Those are put among
Tokyo's other seams, after the last one that leads into a district of the
city, not at the end of the list: generate_palace.py re-appends its doors when
it rebuilds from a sealed palace, and the list must come out the same.

Art is drawn by tools/generate_karuizawa_art.py. Deterministic and idempotent:
rebuilds rooms.Karuizawa from scratch each run, keeping any NPCs the blog
pipeline has placed there, and re-makes the same edit to Tokyo.

Run from gamev2/:  python3 tools/generate_karuizawa.py

Build order:
    python3 tools/generate_karuizawa_art.py
    python3 tools/generate_karuizawa.py
    python3 tools/districts.py
    python3 tools/config_to_tiled.py Karuizawa Tokyo
    python3 tools/sync_cities.py           # config `cities` from ../devhouse.world
    python3 tools/make_worldmap.py
"""
import random
import roomgen as rg
from roomgen import rect
from hokuriku import Kit

CITY, HOST = 'TokyoCity', 'Tokyo'
W, H = 48, 40
GATE = (34, 35)                   # Karuizawa: the rows of the gate, at x = 47
HOST_GATE = (41, 42)              # Tokyo: the same rows, at x = 0
IN = 3                            # a seam transporter lands this many cells inside the neighbour
BRICK = 'flat-grey-brick-autotile_center'
POST = (44, 33)                   # the fingerpost's foot, on the verge north of the road
LARCH = ['tree-green']            # part 2: karuizawa-larch
RX0, RX1 = 14, 15                 # the columns of the road north

cfg = rg.load_config()
host = cfg['rooms'][HOST]

b = rg.Builder(W, H)
k = Kit(b)
rng = random.Random(260)

b.fill('grass-autotile')

# ---- the road: in from the gate, west, then north to the clearing ---------------------
b.autotile('dirt-outside-autotile', rect(RX0, GATE[0], W - 2, GATE[1]) + rect(RX0, 10, RX1, GATE[0] - 1))
b.put('Floor', W - 2, GATE[0], 'dirt-outside-autotile_edge-n')    # open to the brick, not a closed end
b.put('Floor', W - 2, GATE[1], 'dirt-outside-autotile_edge-s')
for y in GATE:
    b.put('Floor', W - 1, y, BRICK)                               # the same brick as Tokyo's apron
b.stand('karuizawa-fingerpost_0_0', *POST)

# ---- the woods: solid, everywhere but the road, its verges and the clearing ------------
k.woods(0, 0, W - 1, 4, LARCH, rng)                               # north
k.woods(0, 5, 9, H - 1, LARCH, rng)                               # west
k.woods(22, 5, W - 1, GATE[0] - 2, LARCH, rng)                    # east, north of the road in
k.woods(10, 12, RX0 - 2, H - 1, LARCH, rng)                       # west of the road north
k.woods(RX1 + 2, 12, 21, GATE[0] - 2, LARCH, rng)                 # east of it, under the clearing
k.woods(RX0 - 1, GATE[1] + 2, W - 1, H - 1, LARCH, rng)           # south
k.solid_rect(W - 1, GATE[0] - 1, W - 1, GATE[0] - 1)              # the verge cells on the edge: only the gate is open
k.solid_rect(W - 1, GATE[1] + 1, W - 1, GATE[1] + 1)
k.plants(rng, 40, 10, 5, 21, 11)                                  # the clearing
k.plants(rng, 30, RX0 - 1, GATE[0] - 1, W - 2, GATE[1] + 1)       # the verges

# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Karuizawa', {})
k.dress()         # no invisible walls: a bare collider beside open ground becomes a shrub
b.finish()
seams = [rg.transporter(W - 1, y, HOST, IN, hy, hidden=True) for y, hy in zip(GATE, HOST_GATE)]
cfg['rooms']['Karuizawa'] = b.room('Karuizawa', npcs=prev.get('npcs', []),
                                   transporters=rg.kept_order(prev, seams))

# ---- Tokyo's west gate, reopened (the reverse of e3cb4d0d) ------------------------------
DISTRICTS = [m['room'] for m in cfg['cities'][CITY]['rooms']]


def seam(items, t):
    """Put seam transporter `t` into Tokyo's list: in place if its cell has one,
    else after the last transporter that leads into a district of the city."""
    if any((i['gridX'], i['gridY']) == (t['gridX'], t['gridY']) for i in items):
        return rg.pin(items, t)
    at = max((n for n, i in enumerate(items) if i['targetRoom'] in DISTRICTS), default=-1) + 1
    items.insert(at, t)
    return t


layers = {l['name']: l['tiles'] for l in host['layers']}
for y, hy in zip(GATE, HOST_GATE):
    layers['Floor'][f'0,{hy}'] = rg.pidx(BRICK)
    layers['Collidables'].pop(f'0,{hy}', None)                    # fence-barriers_0_2
    layers['Colliders'].pop(f'0,{hy}', None)
    seam(host['transporters'], rg.transporter(0, hy, 'Karuizawa', W - 1 - IN, y, hidden=True))

rg.save_config(cfg)
print(f'Karuizawa {W}x{H}; gate on rows {GATE} of its east edge (Tokyo x=0, rows {HOST_GATE}), '
      f'fingerpost at {POST}, road north on columns {(RX0, RX1)}')
