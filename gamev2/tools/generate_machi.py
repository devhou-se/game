#!/usr/bin/env python3
"""generate_machi.py — generate the "Machi" room (a quaint Japanese town) and
the "Konbini" shop interior behind its 7-Eleven door.

Objects come from the Tiled-authored prefab library (tiled/prefabs/*.tmj —
edit them in the Tiled app; see tools/make_prefabs.py for the initial seed).
Each prefab carries its sprites, its collision (the visible collider-marker
tile) and `door` points; stamping a prefab with seal_doors=False leaves the
doorway open so a hidden transporter can be wired to it — that's how the
7-Eleven's door leads into the Konbini room.

Deterministic and idempotent: rebuilds rooms.Machi and rooms.Konbini from
scratch on every run, leaves all other rooms alone, and (once) adds the Tokyo
road transporters.

Run from gamev2/:  python3 tools/generate_machi.py
Then:              python3 tools/qa_port.py --room Machi   (and --room Konbini)
                   python3 tools/config_to_tiled.py Machi  (and Konbini, Tokyo)
"""
import json, random, os
import prefab as _prefab

cfg = json.load(open('config.json'))
pal = cfg['tilePalette']
IDX = {k: i for i, k in enumerate(pal)}
def pidx(k):
    if k not in IDX:
        pal.append(k); IDX[k] = len(pal) - 1
    return IDX[k]

LAYER_NAMES = ['Floor', 'Over Floor', 'Water', 'Non-Collidables', 'Collidables', 'Other', 'Tops', 'Colliders']
_PF = {}

class Builder:
    def __init__(self, w, h):
        self.W, self.H = w, h
        self.L = {n: {} for n in LAYER_NAMES}

    def put(self, layer, x, y, key):
        assert 0 <= x < self.W and 0 <= y < self.H, (layer, x, y, key)
        self.L[layer][f'{x},{y}'] = pidx(key)

    def solid(self, x, y): self.put('Colliders', x, y, 'gk_blank')

    def stamp(self, name, x, y, seal=True):
        if name not in _PF: _PF[name] = _prefab.load_prefab(name)
        return _prefab.stamp(_PF[name], x, y, self.put, self.solid, seal_doors=seal)

    def autotile(self, fam, cells, roles=None):
        roles = roles or {'center','edge-n','edge-e','edge-s','edge-w','corner-nw','corner-ne','corner-sw','corner-se'}
        cells = set(cells)
        for (x, y) in cells:
            n, e, s, w = (x, y-1) in cells, (x+1, y) in cells, (x, y+1) in cells, (x-1, y) in cells
            role = 'center'
            if not n and not w and e and s: role = 'corner-nw'
            elif not n and not e and w and s: role = 'corner-ne'
            elif not s and not w and e and n: role = 'corner-sw'
            elif not s and not e and w and n: role = 'corner-se'
            elif not n and e and w and s: role = 'edge-n'
            elif not s and e and w and n: role = 'edge-s'
            elif not w and n and s and e: role = 'edge-w'
            elif not e and n and s and w: role = 'edge-e'
            if role not in roles: role = 'center'
            self.put('Floor', x, y, f'{fam}_{role}')

    def plants(self, x, y, v=0):
        self.put('Over Floor', x, y, f'ground-plants-1_{["0_0","0_1","1_0","1_1"][v % 4]}')

    def paver(self, x, y, v=0):
        self.put('Over Floor', x, y, ['pavers_1_0','pavers_2_0','pavers_1_2','pavers_2_1','pavers_0_2','pavers_2_2'][v % 6])

    def fence(self, x, y, v=0):
        self.put('Collidables', x, y, ['fence-barriers_2_0','fence-barriers_0_2','fence-barriers_1_2','fence-barriers_0_3'][v % 4])
        self.solid(x, y)

    def room(self, name, npcs, transporters):
        return {'name': name, 'worldWidth': self.W * 64, 'worldHeight': self.H * 64,
                'boundary': [[0, 0], [self.W, 0], [self.W, self.H], [0, self.H]],
                'layers': [
                    {'name': 'Floor', 'z': 0, 'collision': False, 'tiles': self.L['Floor']},
                    {'name': 'Over Floor', 'z': 1, 'collision': False, 'tiles': self.L['Over Floor']},
                    {'name': 'Water', 'z': 1, 'collision': False, 'tiles': self.L['Water']},
                    {'name': 'Non-Collidables', 'z': 4, 'collision': False, 'tiles': self.L['Non-Collidables']},
                    {'name': 'Collidables', 'z': 5, 'collision': False, 'tiles': self.L['Collidables']},
                    {'name': 'Other', 'z': 6, 'collision': False, 'tiles': self.L['Other']},
                    {'name': 'Tops', 'z': 7, 'collision': False, 'tiles': self.L['Tops']},
                    {'name': 'Colliders', 'z': 5, 'collision': True, 'tiles': self.L['Colliders']},
                ],
                'npcs': npcs, 'objects': [], 'transporters': transporters}

# =============================== MACHI =======================================
W, H = 48, 34
b = Builder(W, H)
rng = random.Random(7)
rect = lambda x0, y0, x1, y1: [(x, y) for x in range(x0, x1+1) for y in range(y0, y1+1)]

for x in range(W):
    for y in range(H):
        b.put('Floor', x, y, 'grass-autotile_center')

plaza_shrine = rect(20, 2, 29, 8)
approach = rect(22, 9, 25, 14)
street = rect(3, 15, 45, 16)
plaza_south = rect(19, 18, 30, 24)
lane = rect(23, 17, 24, 17)
road_east = rect(31, 20, 47, 21)
path_garden = rect(4, 22, 18, 23)

b.autotile('flat-grey-brick-autotile', plaza_shrine + approach + lane)
b.autotile('grey-brick-autotile', street)
b.autotile('light-concrete-autotile', plaza_south)
b.autotile('gravel-autotile', road_east + path_garden)

for (fx, fy) in [(14, 6), (43, 8), (5, 26), (15, 26), (34, 25)]:
    b.put('Floor', fx, fy, 'flowering-grass-autotile_corner-nw')
    b.put('Floor', fx+1, fy, 'flowering-grass-autotile_corner-ne')
    b.put('Floor', fx, fy+1, 'flowering-grass-autotile_corner-sw')
    b.put('Floor', fx+1, fy+1, 'flowering-grass-autotile_corner-se')

def pond(x0, y0, x1):  # two rows tall (the pond set has no edge-w piece)
    top = [('corner-nw', x0)] + [('edge-n', x) for x in range(x0+1, x1)] + [('corner-ne', x1)]
    bot = [('corner-sw', x0)] + [('edge-s', x) for x in range(x0+1, x1)] + [('corner-se', x1)]
    for role, x in top: b.put('Water', x, y0, f'pond-autotile_{role}'); b.solid(x, y0)
    for role, x in bot: b.put('Water', x, y0+1, f'pond-autotile_{role}'); b.solid(x, y0+1)

pond(5, 7, 10)
pond(36, 6, 41)

# borders
for x in (2, 7, 12, 33, 38, 43): b.stamp('sakura-large', x, 0)
for x in (3, 8, 13, 18, 23, 28, 33, 38, 43): b.stamp('sakura-large', x, 30)
for y in range(2, 29, 3): b.stamp('shrub-large', 0, y)
for y in range(2, 29, 3):
    if not (18 <= y <= 21): b.stamp('shrub-large', 46, y)
b.stamp('shrub-small', 46, 19); b.stamp('shrub-small', 46, 22)

# shrine precinct
b.stamp('shrine', 23, 1)
b.stamp('fox-statue', 21, 4); b.stamp('fox-statue', 27, 4)
b.stamp('bell-blue', 29, 1)
b.stamp('lantern-red', 20, 6); b.stamp('lantern-red', 28, 6)
b.stamp('lantern-red', 21, 10); b.stamp('lantern-red', 26, 10)
b.put('Over Floor', 23, 9, 'castle-stairs_0_0'); b.put('Over Floor', 24, 9, 'castle-stairs_0_0')
b.stamp('torii-red', 21, 11)
b.plants(19, 8, 1); b.plants(30, 8, 2)

# sakura park (top-left)
b.stamp('sakura-large', 4, 2); b.stamp('sakura-large', 9, 3); b.stamp('sakura-large', 13, 2)
b.stamp('sakura-small', 3, 6); b.stamp('sakura-small', 15, 4)
b.stamp('shrub-small', 12, 8); b.plants(4, 6, 0); b.plants(11, 5, 3); b.plants(13, 9, 2)

# east garden (top-right)
b.stamp('tree-green', 34, 2); b.stamp('tree-green', 41, 2); b.stamp('tree-green', 37, 9)
b.stamp('sakura-small', 44, 4); b.stamp('shrub-small', 35, 8); b.plants(42, 9, 1); b.plants(33, 5, 0)

# street lamps (kept clear of the shop fronts and house footprints)
for x in (6, 34): b.stamp('lamp-blue', x, 14)
for x in (9, 15, 27, 37, 43): b.stamp('lamp-blue', x, 17)

# shop row: the 7-Eleven's door stays OPEN and leads into the Konbini room
konbini_door = b.stamp('seven-eleven', 7, 11, seal=False)[0]
b.stamp('sign-7-11', 10, 12)
b.stamp('vending-white', 12, 13); b.stamp('vending-red', 14, 13); b.stamp('vending-white', 16, 13)
b.stamp('sakura-small', 18, 12)

# houses (doors sealed — no interiors for these yet)
b.stamp('house-blue', 28, 11)
b.stamp('house-black', 33, 10)
b.stamp('house-red', 38, 11)
b.stamp('house-blue', 43, 11)
for hx in (29, 34, 39, 44):
    b.put('Over Floor', hx, 15, 'tile-brick-path_2_1')

# south plaza
b.stamp('pagoda-small', 24, 19)
for i, (px, py) in enumerate([(21, 19), (28, 19), (21, 23), (28, 23),
                              (22, 21), (27, 21), (23, 24), (26, 24)]):
    b.paver(px, py, i)
b.stamp('vending-red', 30, 18); b.stamp('vending-white', 19, 18)
b.stamp('lantern-red', 20, 16); b.stamp('lantern-red', 29, 16)
b.stamp('lantern-red', 20, 24); b.stamp('lantern-red', 29, 24)
b.plants(22, 18, 0); b.plants(27, 18, 3); b.plants(20, 21, 2); b.plants(29, 22, 1)

# orchard + garden (south-west)
for ox in (5, 8, 11, 14):
    for oy in (20, 24):
        b.stamp('sakura-small', ox, oy)
b.plants(6, 22, 0); b.plants(9, 23, 1); b.plants(12, 22, 2); b.plants(15, 23, 3); b.plants(7, 26, 1)

# east road lanterns + greenery south of the houses
b.stamp('lantern-red', 44, 18); b.stamp('lantern-red', 44, 22)
b.stamp('sakura-small', 34, 17); b.stamp('sakura-small', 40, 17)
b.stamp('shrub-small', 37, 18); b.stamp('shrub-small', 42, 18); b.plants(35, 18, 1); b.plants(38, 17, 2)

# south fence line
for i, x in enumerate(range(3, 45)):
    if x in (23, 24): continue
    b.fence(x, 28, i)

# scattered plants
for i in range(14):
    sx, sy = rng.randrange(3, 45), rng.randrange(17, 27)
    if all(f'{sx},{sy}' not in b.L[n] for n in ('Collidables', 'Colliders', 'Over Floor', 'Other')) \
       and pal[b.L['Floor'][f'{sx},{sy}']].startswith('grass'):
        b.plants(sx, sy, i)

dylan = {
    'name': 'Dylan', 'sprite': 'dylan_front',
    'gridX': 27, 'gridY': 22, 'gridOffsetX': 0, 'gridOffsetY': 0,
    'dialogue': [
        "Hello! I'm Dylan.",
        "A whole town, generated by one script.",
        "...I still bet it would've been better in Godot."
    ],
    'directionalSprites': {'up': 'dylan_back', 'down': 'dylan_front', 'left': '', 'right': 'dylan_side'},
    'autoFlip': {'horizontal': True, 'vertical': False},
}
machi_transporters = [
    {'gridX': 47, 'gridY': 20, 'targetRoom': 'Tokyo', 'targetX': 3, 'targetY': 41, 'hidden': False},
    {'gridX': 47, 'gridY': 21, 'targetRoom': 'Tokyo', 'targetX': 3, 'targetY': 42, 'hidden': False},
    # the 7-Eleven doorway (prefab door point, left open by seal=False)
    {'gridX': konbini_door[0], 'gridY': konbini_door[1],
     'targetRoom': 'Konbini', 'targetX': 9, 'targetY': 13, 'hidden': True},
]
cfg['rooms']['Machi'] = b.room('Machi', [dylan], machi_transporters)

# =============================== KONBINI =====================================
kb = Builder(20, 15)
kb.autotile('light-concrete-autotile', rect(0, 0, 19, 14))
# warm brick runner from the door up to the counter
for rx in (9, 10):
    for ry in range(7, 14):
        kb.put('Over Floor', rx, ry, 'tile-brick-path_2_1')

# walls: stone across the top and bottom (door gap), panelled sides
for x in range(20):
    kb.put('Collidables', x, 0, 'castle-wall-siding_0_0'); kb.solid(x, 0); kb.solid(x, 1)
for y in (2, 4, 6, 8, 10, 12):
    for x in (0, 19):
        kb.put('Collidables', x, y, 'blue-wall-short_0_0'); kb.solid(x, y); kb.solid(x, y + 1)
for x in range(1, 19):
    if x in (9, 10): continue
    kb.put('Collidables', x, 13, 'castle-wall-siding_0_0'); kb.solid(x, 13); kb.solid(x, 14)

# aisles: vending "coolers" against the back wall, a stone counter, lanterns
for x in (3, 4, 5): kb.stamp('vending-white', x, 2)
for x in (14, 15, 16): kb.stamp('vending-red', x, 2)
kb.put('Collidables', 9, 5, 'blue-shrine-platform-base_0_0')
for dx in (0, 1):
    for dy in (0, 1): kb.solid(9 + dx, 5 + dy)
kb.stamp('lantern-red', 1, 11); kb.stamp('lantern-red', 18, 11)
kb.paver(9, 14, 0); kb.paver(10, 14, 1)   # door mat

outside = (konbini_door[0], konbini_door[1] + 1)   # cell in front of the 7-Eleven door
konbini_transporters = [
    {'gridX': 9, 'gridY': 14, 'targetRoom': 'Machi', 'targetX': outside[0], 'targetY': outside[1], 'hidden': True},
    {'gridX': 10, 'gridY': 14, 'targetRoom': 'Machi', 'targetX': outside[0], 'targetY': outside[1], 'hidden': True},
]
cfg['rooms']['Konbini'] = kb.room('Konbini', [], konbini_transporters)

# =============================== WIRING ======================================
tok = cfg['rooms']['Tokyo']['transporters']
if not any(t.get('targetRoom') == 'Machi' for t in tok):
    tok.append({'gridX': 1, 'gridY': 41, 'targetRoom': 'Machi', 'targetX': 45, 'targetY': 20, 'hidden': False})
    tok.append({'gridX': 1, 'gridY': 42, 'targetRoom': 'Machi', 'targetX': 45, 'targetY': 21, 'hidden': False})

missing = [pal[i] for bb in (b, kb) for lay in bb.L.values() for i in lay.values()
           if not os.path.exists(f'assets/sprites/{pal[i]}.png')]
assert not missing, f'missing sprites: {sorted(set(missing))[:8]}'

open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
print(f"Machi {b.W}x{b.H} + Konbini {kb.W}x{kb.H}; 7-Eleven door at {konbini_door} -> Konbini")
