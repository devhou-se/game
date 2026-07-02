#!/usr/bin/env python3
"""generate_machi.py — generate the "Machi" room (a quaint Japanese town)
entirely from the existing gamev2 tile vocabulary.

Deterministic and idempotent: rebuilds rooms.Machi from scratch on every run,
leaves all other rooms alone, and (once) adds the Tokyo road transporters.
Layer/collider conventions are copied from how each prefab is used in the
ported rooms (canopy on Tops + solid trunk, lantern head on Tops + solid post,
torii top overhead + post-only feet, water = Water layer + gk_blank colliders,
buildings = walk-behind roof + solid body, vending top solid / bottom open).

Run from gamev2/:  python3 tools/generate_machi.py
Then:              python3 tools/qa_port.py --room Machi
                   python3 tools/config_to_tiled.py Machi
"""
import json, random, sys, os

W, H = 48, 34
ROOM = 'Machi'
rng = random.Random(7)

cfg = json.load(open('config.json'))
pal = cfg['tilePalette']
IDX = {k: i for i, k in enumerate(pal)}
def pidx(k):
    if k not in IDX:
        pal.append(k); IDX[k] = len(pal) - 1
    return IDX[k]

L = {name: {} for name in
     ['Floor', 'Over Floor', 'Water', 'Non-Collidables', 'Collidables', 'Other', 'Tops', 'Colliders']}

def put(layer, x, y, key):
    assert 0 <= x < W and 0 <= y < H, (layer, x, y, key)
    L[layer][f'{x},{y}'] = pidx(key)

def solid(x, y): put('Colliders', x, y, 'gk_blank')

# ---------------- floors (autotiled terrains over a full grass base) --------
def autotile(fam, cells, roles_available):
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
        if role not in roles_available: role = 'center'
        put('Floor', x, y, f'{fam}_{role}')

FULL9 = {'center','edge-n','edge-e','edge-s','edge-w','corner-nw','corner-ne','corner-sw','corner-se'}
def rect(x0, y0, x1, y1): return [(x, y) for x in range(x0, x1+1) for y in range(y0, y1+1)]

# base grass everywhere
for x in range(W):
    for y in range(H):
        put('Floor', x, y, 'grass-autotile_center')

# shrine plaza (top centre) + approach path down to the street
plaza_shrine = rect(20, 2, 29, 8)
approach = rect(22, 9, 25, 14)
# main street east-west
street = rect(3, 15, 45, 16)
# market lane continues south from approach into the south plaza
plaza_south = rect(19, 18, 30, 24)
lane = rect(23, 17, 24, 17)
# east road out to Tokyo (rows 20-21) + west garden path into the plaza
road_east = rect(31, 20, 47, 21)
path_garden = rect(4, 22, 18, 23)

autotile('flat-grey-brick-autotile', plaza_shrine + approach + lane, FULL9)
autotile('grey-brick-autotile', street, FULL9)
autotile('light-concrete-autotile', plaza_south, FULL9)
autotile('gravel-autotile', road_east + path_garden, FULL9)

# flower patches (only the 4 corner pieces exist -> 2x2 patches)
for (fx, fy) in [(14, 6), (43, 8), (5, 26), (15, 26), (34, 25)]:
    put('Floor', fx, fy, 'flowering-grass-autotile_corner-nw')
    put('Floor', fx+1, fy, 'flowering-grass-autotile_corner-ne')
    put('Floor', fx, fy+1, 'flowering-grass-autotile_corner-sw')
    put('Floor', fx+1, fy+1, 'flowering-grass-autotile_corner-se')

# ---------------- water ------------------------------------------------------
def pond(x0, y0, x1):  # two rows tall (the pond set has no edge-w piece)
    top = [('corner-nw', x0)] + [('edge-n', x) for x in range(x0+1, x1)] + [('corner-ne', x1)]
    bot = [('corner-sw', x0)] + [('edge-s', x) for x in range(x0+1, x1)] + [('corner-se', x1)]
    for role, x in top: put('Water', x, y0, f'pond-autotile_{role}'); solid(x, y0)
    for role, x in bot: put('Water', x, y0+1, f'pond-autotile_{role}'); solid(x, y0+1)

pond(5, 7, 10)     # sakura park pond
pond(36, 6, 41)    # east garden pond

# ---------------- prefabs ----------------------------------------------------
def sakura_large(x, y):           # canopy 3x2 on Tops, 1x1 trunk below centre
    put('Tops', x, y, 'sakura-large-top_0_0')
    put('Collidables', x+1, y+2, 'sakura-large-base_0_0'); solid(x+1, y+2)

def sakura_small(x, y):           # whole 1x2 tree, bottom cell solid
    put('Tops', x, y, 'sakura-small_0_0'); solid(x, y+1)

def tree3(x, y):                  # 2x2 canopy + 2x1 trunk
    put('Tops', x, y, 'tree-3-top_0_0')
    put('Collidables', x, y+2, 'tree-3-base-shadow_0_0'); solid(x, y+2); solid(x+1, y+2)

def shrub_large(x, y):
    put('Collidables', x, y, 'shrub-large-circle_0_0')
    for dx in (0, 1):
        for dy in (0, 1): solid(x+dx, y+dy)

def shrub_small(x, y):
    put('Collidables', x, y, 'shrub-small-circle_0_0'); solid(x, y)

def lantern(x, y):                # head on Tops, solid post below
    put('Tops', x, y, 'red-lanterns_6_3')
    put('Collidables', x, y+1, 'red-lanterns_4_1'); solid(x, y+1)

def lamp(x, y):
    put('Collidables', x, y, 'blue-lamp-post_0_0'); solid(x, y)

def fox(x, y):                    # 1x2 statue, feet solid
    put('Collidables', x, y, 'fox-statue-base-1_0_0'); solid(x, y+1)

def vending(x, y, colour='white'):
    put('Other', x, y, f'{colour}-vending-machine-top_0_0')
    put('Other', x, y+1, f'{colour}-vending-machine-bottom_0_0')
    solid(x, y)

def bell(x, y):                   # blue bell: overhead tip + solid base row
    put('Tops', x, y-2, 'blue-bell-top_0_0')
    put('Collidables', x, y, 'bell-blue-baseless_0_0'); solid(x, y); solid(x+1, y)

def torii(x, y):                  # 6x3 top overhead; 4x2 feet, posts solid
    put('Tops', x, y, 'torii-red-top_0_0')
    put('Collidables', x+1, y+3, 'torii-red-feet_0_0')
    for dy in (3, 4): solid(x+1, y+dy); solid(x+4, y+dy)

def shrine(x, y):                 # 3x6 building, solid except the bottom step row
    put('Collidables', x, y, 'shrine-building_0_0')
    for dx in range(3):
        for dy in range(5): solid(x+dx, y+dy)

def house(x, y, colour, entrance):  # 3x3 roof overhead + 3x1 facade, body solid
    put('Tops', x, y, f'building-roof-{colour}_0_0')
    put('Collidables', x, y+3, f'building-entrance-{entrance}_0_0')
    for dx in range(3):
        for dy in (1, 2, 3): solid(x+dx, y+dy)

def seven_eleven(x, y):           # 3x4 store, fully solid, sign to the right
    put('Collidables', x, y, 'seven-eleven_0_0')
    for dx in range(3):
        for dy in range(4): solid(x+dx, y+dy)
    put('Tops', x+3, y+1, '7-11-sign-left_0_0'); solid(x+3, y+2)

def stairs(x, y):
    put('Over Floor', x, y, 'castle-stairs_0_0')

def plants(x, y, v=0):
    put('Over Floor', x, y, f'ground-plants-1_{["0_0","0_1","1_0","1_1"][v % 4]}')

def paver(x, y, v=0):
    put('Over Floor', x, y, ['pavers_1_0','pavers_2_0','pavers_1_2','pavers_2_1','pavers_0_2','pavers_2_2'][v % 6])

def fence(x, y, v=0):
    put('Collidables', x, y, ['fence-barriers_2_0','fence-barriers_0_2','fence-barriers_1_2','fence-barriers_0_3'][v % 4])
    solid(x, y)

# ---------------- composition ------------------------------------------------
# north border: sakura line left+right of the shrine
for x in (2, 7, 12): sakura_large(x, 0)
for x in (33, 38, 43): sakura_large(x, 0)
# south border: sakura canopies with trunks on row 32
for x in (3, 8, 13, 18, 23, 28, 33, 38, 43): sakura_large(x, 30)
# west border shrubs; east border shrubs except the road gap (rows 20-21)
for y in range(2, 29, 3):
    shrub_large(0, y)
for y in range(2, 29, 3):
    if not (18 <= y <= 21): shrub_large(46, y)
shrub_small(46, 19); shrub_small(46, 22)

# shrine precinct
shrine(23, 1)
fox(21, 4); fox(27, 4)
bell(29, 3)
lantern(20, 6); lantern(28, 6)
lantern(21, 10); lantern(26, 10)
stairs(23, 9); stairs(24, 9)
torii(21, 11)
plants(19, 8, 1); plants(30, 8, 2)

# sakura park (top-left)
sakura_large(4, 2); sakura_large(9, 3); sakura_large(13, 2)
sakura_small(3, 6); sakura_small(15, 4)
shrub_small(12, 8); plants(4, 6, 0); plants(11, 5, 3); plants(13, 9, 2)

# east garden (top-right)
tree3(34, 2); tree3(41, 2); tree3(37, 9)
sakura_small(44, 4); shrub_small(35, 8); plants(42, 9, 1); plants(33, 5, 0)

# main street lamps (kept clear of the shop fronts and house footprints)
for x in (6, 34): lamp(x, 14)
for x in (9, 15, 27, 37, 43): lamp(x, 17)

# shop row north of the street (west side)
seven_eleven(7, 11)
vending(12, 13, 'white'); vending(14, 13, 'red'); vending(16, 13, 'white')
sakura_small(18, 12)

# houses north of the street (east side)
house(28, 11, 'blue', 1)
house(33, 10, 'black', 2)
house(38, 11, 'red', 3)
house(43, 11, 'blue', 3)
for hx in (29, 34, 39, 44):
    put('Over Floor', hx, 15, 'tile-brick-path_2_1')

# south plaza: mini pagoda centrepiece, paver walk, lantern corners, vending
put('Tops', 24, 20, 'red-pagoda-small-top_0_0')
put('Collidables', 24, 19, 'red-pagoda-small-base_0_0')
for dy in range(19, 23): solid(24, dy); solid(25, dy)
for i, (px, py) in enumerate([(21, 19), (28, 19), (21, 23), (28, 23),
                              (22, 21), (27, 21), (23, 24), (26, 24)]):
    paver(px, py, i)
vending(30, 18, 'red'); vending(19, 18, 'white')
lantern(20, 16); lantern(29, 16)
lantern(20, 24); lantern(29, 24)
plants(22, 18, 0); plants(27, 18, 3); plants(20, 21, 2); plants(29, 22, 1)

# orchard + garden (south-west)
for ox in (5, 8, 11, 14):
    for oy in (20, 24):
        sakura_small(ox, oy)
plants(6, 22, 0); plants(9, 23, 1); plants(12, 22, 2); plants(15, 23, 3); plants(7, 26, 1)

# east road lanterns + a little green south of the houses
lantern(44, 18); lantern(44, 22)
sakura_small(34, 17); sakura_small(40, 17)
shrub_small(37, 18); shrub_small(42, 18); plants(35, 18, 1); plants(38, 17, 2)

# south fence line
for i, x in enumerate(range(3, 45)):
    if x in (23, 24): continue
    fence(x, 28, i)

# scattered plants for texture
for i in range(14):
    sx, sy = rng.randrange(3, 45), rng.randrange(17, 27)
    if f'{sx},{sy}' not in L['Collidables'] and f'{sx},{sy}' not in L['Colliders'] \
       and f'{sx},{sy}' not in L['Over Floor'] and f'{sx},{sy}' not in L['Other'] \
       and pal[L['Floor'][f'{sx},{sy}']].startswith('grass'):
        plants(sx, sy, i)

# ---------------- room + wiring ---------------------------------------------
room = {
    'name': ROOM,
    'worldWidth': W * 64, 'worldHeight': H * 64,
    'boundary': [[0, 0], [W, 0], [W, H], [0, H]],
    'layers': [
        {'name': 'Floor', 'z': 0, 'collision': False, 'tiles': L['Floor']},
        {'name': 'Over Floor', 'z': 1, 'collision': False, 'tiles': L['Over Floor']},
        {'name': 'Water', 'z': 1, 'collision': False, 'tiles': L['Water']},
        {'name': 'Non-Collidables', 'z': 4, 'collision': False, 'tiles': L['Non-Collidables']},
        {'name': 'Collidables', 'z': 5, 'collision': False, 'tiles': L['Collidables']},
        {'name': 'Other', 'z': 6, 'collision': False, 'tiles': L['Other']},
        {'name': 'Tops', 'z': 7, 'collision': False, 'tiles': L['Tops']},
        {'name': 'Colliders', 'z': 5, 'collision': True, 'tiles': L['Colliders']},
    ],
    'npcs': [{
        'name': 'Dylan', 'sprite': 'dylan_front',
        'gridX': 27, 'gridY': 22, 'gridOffsetX': 0, 'gridOffsetY': 0,
        'dialogue': [
            "Hello! I'm Dylan.",
            "A whole town, generated by one script.",
            "...I still bet it would've been better in Godot."
        ],
        'directionalSprites': {'up': 'dylan_back', 'down': 'dylan_front', 'left': '', 'right': 'dylan_side'},
        'autoFlip': {'horizontal': True, 'vertical': False},
    }],
    'objects': [],
    'transporters': [
        {'gridX': 47, 'gridY': 20, 'targetRoom': 'Tokyo', 'targetX': 3, 'targetY': 41, 'hidden': False},
        {'gridX': 47, 'gridY': 21, 'targetRoom': 'Tokyo', 'targetX': 3, 'targetY': 42, 'hidden': False},
    ],
}
cfg['rooms'][ROOM] = room

# Tokyo -> Machi (west road edge), added once
tok = cfg['rooms']['Tokyo']['transporters']
if not any(t.get('targetRoom') == ROOM for t in tok):
    tok.append({'gridX': 1, 'gridY': 41, 'targetRoom': ROOM, 'targetX': 45, 'targetY': 20, 'hidden': False})
    tok.append({'gridX': 1, 'gridY': 42, 'targetRoom': ROOM, 'targetX': 45, 'targetY': 21, 'hidden': False})

# sanity: every referenced sprite exists on disk
missing = [pal[i] for lay in L.values() for i in lay.values()
           if not os.path.exists(f'assets/sprites/{pal[i]}.png')]
assert not missing, f'missing sprites: {sorted(set(missing))[:8]}'

open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
print(f'{ROOM}: {W}x{H} cells; tiles per layer:',
      {k: len(v) for k, v in L.items() if v})
