#!/usr/bin/env python3
"""generate_houses.py — a generic interior for every house in a town (issue #208).

The konbini recipe (tools/generate_konbinis.py), for homes: it finds a town's
HOUSES in the town's map data, builds one small interior room per house from a
layout rule, opens the house's front door (collider off, a hidden transporter
on the door cell, replaced in place) and wires the way back out to the
pavement cell in front of it. A re-run on an unchanged world is a no-op.

WHAT COUNTS AS A HOUSE (roomgen.HOUSE_DOORS):
  * the three townhouse prefabs house-blue / house-red / house-black, found by
    their ground floor (`building-entrance-1/2/3`), door in the middle;
  * the machiya (machiya-black / -red / -blue), door in the middle of its front.
and of those, NOT:
  * a house whose door already leads somewhere else - the station houses, the
    Izakaya in Market ("in use");
  * a house with a shop sign at its front (SHOP_SIGNS: the ramen nobori of
    Asahikawa's ramen alley) - that is a shop, and wants its own interior.
Never a house: 7-Elevens, the discount store, high-rises and apartment
blocks, shrine halls, pagodas, temple halls, landmark buildings, stations.

A house is SKIPPED, and stays sealed, rather than anything else being moved:
  * when the cell in front of its door cannot be stood on or walked to;
  * when an NPC's base or dated position (any content date) is on the door
    or on the cell in front of it;
  * when a blog landmark's stand cell (blog_to_npc.find_spots) is.
The run prints every house it skipped and why.

THE INTERIOR is one lit room floating in the void, like a konbini's: a
two-row back wall (plaster, shoji, fusuma, a window, the tokonoma alcove with
its scroll), six rows of floor, and a genkan sticking out below it - shoes,
the shoe cupboard, and the mat you leave by. Four layouts (LAYOUTS): the
kotatsu room, the quiet futon room, the farmhouse with its sunken hearth, and
the one-room flat with a bed. Each is mirrored or not and takes one of two
tatami, two plasters and two sets of cloth, all from the house's own position
(md5 of town + door), so a re-run rebuilds the same home; the layout is the
one its nearest neighbours do not have (pick_layouts). Nobody lives in them
and nothing is sold: `interior` (so the blog pipeline never offers them),
`shopEnabled: false`, and one flavour line when you bump the kotatsu, the
hearth, the stove, the television or the bookshelf (src/utils/Interactions.js).

Art: tools/extract_house_interior.py (floorboards, a house plant) and
tools/generate_house_art.py (everything else). Run both first.

Run from gamev2/:
    python3 tools/generate_houses.py Asahikawa [<Town> ...]   # build / rebuild those towns' houses
    python3 tools/generate_houses.py                          # rebuild every town that has houses
    python3 tools/generate_houses.py --variants               # every layout as JSON, nothing written
Then:   python3 tools/config_to_tiled.py <each House room + the towns>
        node tools/play.js lint <each House room + the towns>
(.agent-queue/items/houses_apply.sh <Town> ... does all of it.)
"""
import hashlib
import json
import sys

import roomgen as rg

SHOP_SIGNS = ('ramen-banner_0_0',)      # a house with one of these at its front is a shop
ROOM_W, ROOM_H = 20, 15                 # engine / camera minimum; the home floats inside
FW, FH = 9, 6                           # the floor, in cells
FX, FY = (ROOM_W - FW) // 2, 4          # its top-left cell; the wall is the two rows above

# Each layout: the back wall (one character per column), the floor (FH rows of
# FW), the columns of bare boards, and the genkan's middle column.
#   wall:  p plaster   s shoji   u fusuma   n window   Aa the tokonoma (2 wide)
#   against the wall, on the first floor row (they stand over the wall's lower half):
#          D tansu   S bookshelf   V television   R fridge   Cc the kitchen (2 wide)
#   floor: . free   z a cushion (flat, walked over)   Kk kotatsu (2x2)   Ii the hearth (2x2)
#          Tt low table (2x1)   Ff futon (1x2)   Bb bed (1x2)   H stove   L lamp   P plant
LAYOUTS = {
    'kotatsu': dict(                    # the winter living room: everyone under one quilt, facing the television
        wall='Aasspnppp',
        floor=['....VHCcR',
               'L.zz.....',
               '.zKkz....',
               '.zkkz.FF.',
               '..zz..ff.',
               '........P'],
        boards=[(6, 0, 8, 1)], genkan=4),
    'futon': dict(                      # the quiet room: beds laid out by the closet, tea at the low table
        wall='uusAapppp',
        floor=['.....SCcR',
               'FF.......',
               'ff.zTtz..',
               '....zz..L',
               'H.......P',
               '.........'],
        boards=[(6, 0, 8, 1)], genkan=5),
    'flat': dict(                       # the one-room flat: a bed on the boards, a tatami corner to sit in
        wall='pppnpsAap',
        floor=['CcR.V...S',
               '.........',
               'B..zTtz..',
               'b...zz..L',
               'P........',
               '.........'],
        boards=[(0, 0, 2, 5), (3, 0, 8, 0)], genkan=5),
    'hearth': dict(                     # the farmhouse: boards round the sunken hearth, a tatami room beside it
        wall='ppnppAass',
        floor=['Cc.SD...L',
               '..z.....F',
               'zIiz....f',
               '.iiz..z..',
               '.z......P',
               '.........'],
        boards=[(0, 0, 4, 5)], genkan=4),
}
LAYOUT_NAMES = list(LAYOUTS)

# character -> (sprite key or a name looked up in the house's cloth, w, h)
FURNITURE = {'K': ('kotatsu', 2, 2), 'I': ('home-irori_0_0', 2, 2), 'T': ('home-table_0_0', 2, 1),
             'F': ('futon', 1, 2), 'B': ('home-bed_0_0', 1, 2), 'H': ('home-stove_0_0', 1, 1),
             'L': ('home-andon_0_0', 1, 1), 'P': ('home-plant_0_0', 1, 1)}
AT_WALL = {'D': ('home-tansu_0_0', 1), 'S': ('home-bookshelf_0_0', 1), 'V': ('home-tv_0_0', 1),
           'R': ('home-fridge_0_0', 1), 'C': ('home-kitchen_0_0', 2)}
WALLS = {'s': 'home-wall-shoji_0_0', 'u': 'home-wall-fusuma_0_0'}
CLOTH = [dict(kotatsu='home-kotatsu-red_0_0', futon='home-futon-blue_0_0',
              cushions=['home-zabuton-indigo_0_0', 'home-zabuton-red_0_0', 'home-zabuton-green_0_0']),
         dict(kotatsu='home-kotatsu-indigo_0_0', futon='home-futon-rose_0_0',
              cushions=['home-zabuton-red_0_0', 'home-zabuton-green_0_0', 'home-zabuton-indigo_0_0'])]
TATAMI = ['home-tatami-green', 'home-tatami-gold']
PLASTER = ['sand', 'moss']
# what a bump says something about (Interactions' flavour rules): each layout has at least one
FLAVOUR = ('home-kotatsu', 'home-irori', 'home-stove', 'home-tv', 'home-bookshelf')


def seed_of(host, door):
    return int(hashlib.md5(f'{host}:{door[0]},{door[1]}'.encode()).hexdigest()[:8], 16)


def parse(layout, mirror):
    """A layout's pieces in floor coordinates: walls [(key or None, col, w)],
    at-wall and floor furniture [(char, col, row, w, h)], cushions, boards,
    the genkan's middle column - flipped left to right when `mirror`."""
    spec = LAYOUTS[layout]
    flip = (lambda c, w=1: FW - c - w) if mirror else (lambda c, w=1: c)
    walls, c = [], 0
    while c < FW:
        ch = spec['wall'][c]
        w = 2 if ch == 'A' else 1
        walls.append((ch, flip(c, w), w))
        c += w
    items, cushions = [], []
    for r, row in enumerate(spec['floor']):
        assert len(row) == FW, (layout, row)
        for c, ch in enumerate(row):
            if ch == 'z':
                cushions.append((flip(c), r))
            elif ch in AT_WALL:
                assert r == 0, f'{layout}: {ch} must stand against the wall'
                items.append((ch, flip(c, AT_WALL[ch][1]), r, AT_WALL[ch][1], 1))
            elif ch in FURNITURE:
                _, w, h = FURNITURE[ch]
                items.append((ch, flip(c, w), r, w, h))
    boards = set()
    for x0, y0, x1, y1 in spec['boards']:
        boards |= {(flip(x), y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    return walls, items, sorted(cushions, key=lambda c: (c[1], c[0])), boards, flip(spec['genkan'])


def build_interior(name, host, front, layout, seed):
    """(room, arrival cell) for one home. `seed` picks the mirror and the swaps."""
    mirror, tatami, plaster = bool(seed & 1), TATAMI[(seed >> 1) & 1], PLASTER[(seed >> 2) & 1]
    cloth, shoes = CLOTH[(seed >> 3) & 1], (seed >> 4) & 1
    walls, items, cushions, boards, g = parse(layout, mirror)
    b = rg.Builder(ROOM_W, ROOM_H)
    b.fill('office-void-autotile')

    def solid(key, x, y, w=1, h=1, layer='Collidables'):
        b.put(layer, x, y, key)
        for dx in range(w):
            for dy in range(h):
                b.solid(x + dx, y + dy)

    # the floor: tatami laid as two-cell mats, each row half a mat along from the last; boards
    # where the layout says; the step you come up over, above the genkan
    for c in range(FW):
        for r in range(FH):
            if (c, r) in boards:
                key = 'home-wood-floor_0_0'
            else:
                key = f"{tatami}_{'w' if (c + r) % 2 == 0 else 'e'}"
            b.put('Floor', FX + c, FY + r, key)
    for c in (g - 1, g, g + 1):
        b.put('Floor', FX + c, FY + FH - 1, 'home-agari_0_0')

    # the back wall, two rows of it, and what stands against it
    for ch, c, w in walls:
        key = ('home-tokonoma_0_0' if ch == 'A' else f'home-wall-window-{plaster}_0_0' if ch == 'n'
               else WALLS.get(ch, f'home-wall-{plaster}_0_0'))
        solid(key, FX + c, FY - 2, w, 2)
    for ch, c, r, w, h in items:
        if ch in AT_WALL:
            b.put('Collidables', FX + c, FY - 1, AT_WALL[ch][0])
            for dx in range(w):
                b.solid(FX + c + dx, FY)
        else:
            key = FURNITURE[ch][0]
            solid(cloth.get(key, key), FX + c, FY + r, w, h)
    for i, (c, r) in enumerate(cushions):
        b.put('Over Floor', FX + c, FY + r, cloth['cushions'][0 if i % 3 else 1 + (i // 3) % 2])

    # the genkan: three cells of stone a step down from the floor - shoes left on one side,
    # the shoe cupboard on the other, the way in between them - and the mat you leave by
    gy, my = FY + FH, FY + FH + 1
    for c in (g - 1, g, g + 1):
        b.put('Floor', FX + c, gy, 'home-genkan_0_0')
    b.put('Floor', FX + g, my, 'home-genkan_0_0')
    b.put('Over Floor', FX + g, my, 'home-doormat_0_0')
    side = -1 if mirror else 1
    solid(f"home-shoes-{'ab'[shoes]}_0_0", FX + g - side, gy)
    solid('home-getabako_0_0', FX + g + side, gy)

    room = b.room(name, transporters=[rg.transporter(FX + g, my, host, front[0], front[1], hidden=True)])
    # movement is confined to the lit floor, the genkan and the mat: the void needs no colliders
    x0, x1, y1 = FX, FX + FW, FY + FH
    room['boundary'] = [[x0, FY], [x1, FY], [x1, y1], [FX + g + 2, y1], [FX + g + 2, gy + 1],
                        [FX + g + 1, gy + 1], [FX + g + 1, my + 1], [FX + g, my + 1], [FX + g, gy + 1],
                        [FX + g - 1, gy + 1], [FX + g - 1, y1], [x0, y1]]
    room['interior'] = True          # never graded by day / night, never offered to the blog pipeline
    room['shopEnabled'] = False      # a home: nothing in it sells
    arrive = (FX + g, gy)            # in the genkan, among the shoes; the mat is the cell below
    check_interior(name, room, arrive)
    return room, arrive


def check_interior(name, room, arrive):
    """Every free cell of the home can be walked to from the genkan, and every
    flavour object can be bumped from the cell in front of it."""
    solid = {tuple(map(int, c.split(','))) for c in room['layers'][-1]['tiles']}
    free = ({(FX + c, FY + r) for c in range(FW) for r in range(FH)} | {arrive, (arrive[0], arrive[1] + 1)}) - solid
    seen, todo = {arrive}, [arrive]
    while todo:
        x, y = todo.pop()
        for cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if cell in free and cell not in seen:
                seen.add(cell)
                todo.append(cell)
    assert seen == free, f'{name}: floor nobody can reach: {sorted(free - seen)}'
    flavour = 0
    for xy, idx in room['layers'][4]['tiles'].items():
        key = rg._pal[idx]
        if key.startswith(FLAVOUR):
            x, y = map(int, xy.split(','))
            w, h = (2, 2) if key.startswith(('home-kotatsu', 'home-irori')) else (1, 2) if y < FY else (1, 1)
            assert all((x + dx, y + h) in seen for dx in range(w)), f'{name}: {key} at {xy} has no cell in front'
            flavour += 1
    assert flavour, f'{name}: nothing to bump'


# ---- finding the houses ---------------------------------------------------------
def find_houses(cfg, host):
    """Every house front in `host`, in (y, x) order of its door, as dicts:
    key / name / door / front / family / origin, plus `excluded` (not a house:
    'in use', 'shop') or `skipped` (a house that must stay sealed, and why)."""
    import blog_to_npc as bn
    room = cfg['rooms'][host]
    found = []
    signs = set()
    for layer in room['layers']:
        for xy, idx in layer['tiles'].items():
            key = rg._pal[idx]
            x, y = map(int, xy.split(','))
            if key in SHOP_SIGNS:
                signs.add((x, y))
            elif layer['name'] == 'Collidables' and key in rg.HOUSE_DOORS:
                dx, dy = rg.HOUSE_DOORS[key]
                found.append(dict(family=key.rsplit('_', 2)[0], origin=(x, y), door=(x + dx, y + dy),
                                  front=(x + dx, y + dy + 1), span=(x - 1, x + 2 * dx + 1)))
    found.sort(key=lambda h: (h['door'][1], h['door'][0]))

    doors = {(t['gridX'], t['gridY']): t['targetRoom'] for t in room.get('transporters', [])}
    width, height, floored, blocked = bn.room_cells(cfg, host)
    reach = bn.reachable_cells(cfg, host)
    people = {}
    for npc in room.get('npcs', []):
        for when, s in [('always', npc)] + sorted((npc.get('states') or {}).items()):
            if s.get('gridX') is not None and s.get('gridY') is not None:
                people.setdefault((s['gridX'], s['gridY']), f"{npc['name']} ({when})")
    spots = {(x, y): label for label, (r, x, y) in bn.find_spots(cfg).items() if r == host}

    houses, n = [], 0
    for h in found:
        door, front = h['door'], h['front']
        target = doors.get(door)
        if target and not target.startswith(rg.HOUSE_PREFIX):
            h['excluded'] = f'in use: its door leads to {target}'
        elif any(h['span'][0] <= x <= h['span'][1] and abs(y - door[1]) <= 1 for x, y in signs):
            h['excluded'] = 'a shop: it has a shop sign at its front'
        else:
            n += 1
            h['key'] = f'{rg.HOUSE_PREFIX}{host}{n}'
            fkey = f'{front[0]},{front[1]}'
            if not (0 <= front[0] < width and 0 <= front[1] < height and fkey in floored and fkey not in blocked):
                h['skipped'] = f'the cell in front of its door {front} cannot be stood on'
            elif front in doors:
                h['skipped'] = f'the cell in front of its door {front} is itself a door'
            elif reach is not None and front not in reach:
                h['skipped'] = f'the cell in front of its door {front} cannot be walked to'
            else:
                for cell, what in ((door, 'on its door'), (front, 'in front of its door')):
                    if cell in people:
                        h['skipped'] = f'{people[cell]} stands {what} {cell}'
                    elif cell in spots:
                        h['skipped'] = f'the blog spot "{spots[cell]}" is {what} {cell}'
        houses.append(h)
    where = room.get('name', host)
    for h in houses:
        if 'key' in h:
            h['name'] = f'House · {where}' + (f" {h['key'][len(rg.HOUSE_PREFIX + host):]}" if n > 1 else '')
    return houses


def pick_layouts(host, houses):
    """A layout for every house: its own favourite (from its position) unless
    a house nearby already has that one - then the next the neighbours do not
    have, and of those the one the town has used least. Two houses side by
    side never match, and a small town shows as many layouts as it has houses."""
    placed, used = [], {name: 0 for name in LAYOUT_NAMES}
    for h in houses:
        fav = seed_of(host, h['door']) >> 8
        order = [LAYOUT_NAMES[(fav + i) % len(LAYOUT_NAMES)] for i in range(len(LAYOUT_NAMES))]
        near = {p['layout'] for p in placed
                if max(abs(p['door'][0] - h['door'][0]), abs(p['door'][1] - h['door'][1])) <= 12}
        choice = min([name for name in order if name not in near] or order, key=lambda name: used[name])
        h['layout'] = choice
        used[choice] += 1
        placed.append(h)


def seal(host, cell):
    for layer in host['layers']:
        if layer['name'] == 'Colliders':
            layer['tiles'][f'{cell[0]},{cell[1]}'] = rg.pidx('gk_blank')
    host['transporters'] = [t for t in host.get('transporters', [])
                            if not ((t['gridX'], t['gridY']) == tuple(cell) and t['targetRoom'].startswith(rg.HOUSE_PREFIX))]


def apply(cfg, host):
    """(Re)build `host`'s houses in cfg. Returns (built keys, report lines)."""
    room = cfg['rooms'][host]
    candidates = find_houses(cfg, host)
    houses = [h for h in candidates if 'key' in h]
    pick_layouts(host, houses)
    built, lines = [], []
    for h in candidates:
        if 'excluded' in h:
            lines.append(f"not a house  {host} {h['family']} at {h['origin']} - {h['excluded']}")
    # rooms of this town from an earlier run that no house claims any more
    for key in [k for k, r in cfg['rooms'].items() if (r.get('house') or {}).get('host') == host]:
        if key not in {h['key'] for h in houses if 'skipped' not in h}:
            seal(room, cfg['rooms'][key]['house']['door'])
            del cfg['rooms'][key]
    for h in houses:
        if 'skipped' in h:
            seal(room, h['door'])
            lines.append(f"skipped  {h['key']} ({h['family']}, door {h['door']}) - {h['skipped']}")
            continue
        interior, arrive = build_interior(h['name'], host, h['front'], h['layout'], seed_of(host, h['door']))
        interior['house'] = {'host': host, 'door': list(h['door']), 'layout': h['layout']}
        cfg['rooms'][h['key']] = interior
        for layer in room['layers']:                         # unseal the doorway...
            if layer['name'] == 'Colliders':
                layer['tiles'].pop(f"{h['door'][0]},{h['door'][1]}", None)
        # ...and wire it in, replacing the door's transporter where it already sits (append
        # only a new one): a re-run on an unchanged world leaves config.json byte-identical
        door = rg.transporter(h['door'][0], h['door'][1], h['key'], arrive[0], arrive[1], hidden=True)
        ts = room.setdefault('transporters', [])
        at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == h['door']]
        if at:
            ts[at[0]] = door
            for i in reversed(at[1:]):
                del ts[i]
        else:
            ts.append(door)
        built.append(h['key'])
        lines.append(f"built    {h['key']} \"{h['name']}\" - {h['family']}, door {h['door']}, the {h['layout']} room")
    return built, lines


def variants():
    """Every layout, plain and mirrored, as rooms - for the tests and for a
    look at them (nothing is written)."""
    out = {}
    for i, layout in enumerate(LAYOUT_NAMES):
        for mirror in (0, 1):
            seed = mirror | (i % 2) << 1 | (i // 2) << 2 | ((i + mirror) % 2) << 3 | mirror << 4
            room, arrive = build_interior(f'House · {layout}', 'Asahikawa', (0, 0), layout, seed)
            room['house'] = {'host': 'Asahikawa', 'door': [0, 0], 'layout': layout}
            out[f"{layout}{'-mirrored' if mirror else ''}"] = {'room': room, 'arrive': list(arrive)}
    return out


def main(argv):
    cfg = rg.load_config()
    if '--variants' in argv:
        print(json.dumps({'tilePalette': cfg['tilePalette'], 'variants': variants()}))
        return 0
    towns = argv or sorted({r['house']['host'] for r in cfg['rooms'].values() if r.get('house')})
    unknown = [t for t in towns if t not in cfg['rooms'] or cfg['rooms'][t].get('interior')
               or t in cfg.get('stations', {})]
    if unknown:
        print(f'not a town: {unknown}')
        return 2
    if not towns:
        print('no town has houses yet: name the towns to build, e.g. generate_houses.py Asahikawa')
        return 0
    built = []
    for host in towns:
        keys, lines = apply(cfg, host)
        built += keys
        print('\n'.join(lines) if lines else f'{host}: no houses')
    rg.save_config(cfg)
    print(f"\n{len(built)} house interior(s) written. Now run config_to_tiled, then play.js lint, for:")
    print('  ' + ' '.join(built + towns))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
