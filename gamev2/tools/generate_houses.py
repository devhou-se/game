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

A SECOND KIND OF BUILDING, THE TOWER (issue #216, `--lobbies`): every
high-rise, office tower and block of flats (roomgen.TOWER_DOORS: the
highrise-yellow / -blue / -glass / -apartment and midrise-apartment sprites)
gets a door into a `Lobby<Town><n>` room, found, numbered, skipped, sealed
and re-run by the same code as a house (KINDS). A tower with a pair of doors
(the glass tower) opens each door that passes the rules, and is skipped only
when none does. Landmark towers (Tokyo Tower, the TV tower, Fukuoka Tower,
castles) are not towers here and stay sealed, and neither is a block whose
ground floor is a store (STOREFRONTS: Sendai's flats, with the town's
7-Eleven standing across their door) - it is in use, entered through the
store. THE LOBBY is one design,
identical everywhere for now (LOBBY): a stone-panelled back wall with two
lifts and the building directory, eleven by six cells of polished floor, the
reception desk, a sofa either side of a glass table, a palm in each corner,
and the entrance mat below the middle of the floor. A bump on the directory
or on a lift says one line. Nobody works there yet.

A THIRD KIND, THE SHOP (issue #219, `--shops`): a shopfront in
roomgen.SHOP_DOORS (Tanukikoji's souvenir shop, crab shop and drugstore) gets a
door into a `Shop<Town><n>` room, by the same rules. THE SHOP FLOOR is one
layout (SHOP): a white back wall with posters, shelves against it, seven by
five cells of floor, a counter with a till, a plant in each front corner and
the mat below the middle. It reuses the konbini's furniture. The room is named
by what the front sells (SHOP_TYPES: 'Souvenirs · Sapporo'), its shelves are
that type's, and a bump on the counter opens the shop list of that type
(`shopMenu`, a row of Shop.VENUES: two or three things from the existing
catalogue). It is not a store: `shopEnabled: false`, so no stamp, and the
shelves are only to look at.

Art: tools/extract_house_interior.py (floorboards, a house plant) and
tools/generate_house_art.py (everything else, the lobby's too). Run both first.

Run from gamev2/:
    python3 tools/generate_houses.py Asahikawa [<Town> ...]   # build / rebuild those towns' houses
    python3 tools/generate_houses.py --lobbies Osaka [...]    # build / rebuild those towns' tower lobbies
    python3 tools/generate_houses.py --shops Sapporo [...]    # build / rebuild those towns' shop floors
    python3 tools/generate_houses.py                          # rebuild every town's houses, lobbies and shops that has them
    python3 tools/generate_houses.py --dry-run [--lobbies | --shops] <Town> ...   # say what would be built; write nothing
    python3 tools/generate_houses.py --variants               # every house layout as JSON, nothing written
    python3 tools/generate_houses.py --help                   # this text; nothing is run (an unknown option is an error)
Then:   python3 tools/config_to_tiled.py <each House / Lobby room + the towns>
        node tools/play.js lint <each House / Lobby room + the towns>
(.agent-queue/items/houses_apply.sh <Town> ... and lobbies_apply.sh <Town> ... do all of it.)
"""
import json
import sys

import interiors
import roomgen as rg
from interiors import Interior

SHOP_SIGNS = ('ramen-banner_0_0',)      # a house with one of these at its front is a shop
STOREFRONTS = ('seven-eleven_0_0',)     # a tower with one of these standing across its door is that store's block
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

# The lobby of a tower (issue #216): one design. Read like a house layout, on
# a floor LW x LH cells:
#   wall:  p panelling   Ll a lift (2 wide)   D the directory board
#   floor: . free   P a palm   Rrr the reception desk (3x1)   Ss a sofa   Bb a sofa seen from
#          behind   Tt the glass table between them (2x1 each)
LW, LH = 11, 6
LX, LY = (ROOM_W - LW) // 2, 4
LOBBY = dict(wall='pLlpLlppDpp',
             floor=['P.........P',
                    '...........',
                    '.Rrr...Ss..',
                    '.......Tt..',
                    '.......Bb..',
                    'P.........P'],
             door=5)
LOBBY_WALL = {'p': ('lobby-wall_0_0', 1), 'L': ('lobby-lift_0_0', 2), 'D': ('lobby-directory_0_0', 1)}
LOBBY_FURNITURE = {'P': ('lobby-plant_0_0', 1), 'R': ('lobby-desk_0_0', 3), 'S': ('lobby-sofa_0_0', 2),
                   'B': ('lobby-sofa-back_0_0', 2), 'T': ('lobby-table_0_0', 2)}
LOBBY_FLAVOUR = ('lobby-directory', 'lobby-lift')

# The shop floor behind a shopfront (issue #219): one layout, on a floor SW x SH cells:
#   wall:  w white wall   p a poster on it
#   floor: . free   S a shelf (the type's own, against the wall)   Cc the counter (2x1, the till on its
#          right half)   P a plant
SW, SH = 7, 5
SX, SY = (ROOM_W - SW) // 2, 5
SHOP = dict(wall='wpwwwpw',
            floor=['SS...SS',
                   '.......',
                   '.Cc....',
                   '.......',
                   'P.....P'],
            door=3)
# what a shopfront sells: the sprite family -> (room label, Shop.VENUES id, its shelves)
SHOP_TYPES = {
    'tanukikoji-shop-souvenir': ('Souvenirs', 'souvenirs', 'office-shelf-snacks_0_0'),
    'tanukikoji-shop-crab': ('Crab shop', 'crab', 'office-freezer_0_0'),
    'tanukikoji-shop-drug': ('Drugstore', 'drugstore', 'office-shelf-glass_0_0'),
}
SHOP_FLAVOUR = ('office-counter2',)

# The kinds of building this generator opens: the room-key prefix, the key
# on the interior that marks it (and holds its host and door), the sprites that
# carry its doors -> the door cells relative to the sprite, and its name.
KINDS = {
    'house': dict(prefix=rg.HOUSE_PREFIX, marker='house', label='House', what='house',
                  doors={k: [v] for k, v in rg.HOUSE_DOORS.items()}),
    'lobby': dict(prefix=rg.LOBBY_PREFIX, marker='lobby', label='Lobby', what='tower', doors=rg.TOWER_DOORS),
    # a shop is named by its type (`labels`), numbered only among its own type
    'shop': dict(prefix=rg.SHOP_PREFIX, marker='shop', label='Shop', what='shop', doors=rg.SHOP_DOORS,
                 labels={family: t[0] for family, t in SHOP_TYPES.items()}),
}


def seed_of(host, door):
    return interiors.seed_of(f'{host}:{door[0]},{door[1]}')


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
    it = Interior(FW, FH, ox=FX, oy=FY, w=ROOM_W, h=ROOM_H)

    # the floor: tatami laid as two-cell mats, each row half a mat along from the last; boards
    # where the layout says; the step you come up over, above the genkan
    it.floor(lambda c, r: 'home-wood-floor_0_0' if (c, r) in boards else f"{tatami}_{'w' if (c + r) % 2 == 0 else 'e'}")
    for c in (g - 1, g, g + 1):
        it.put('Floor', c, FH - 1, 'home-agari_0_0')

    # the back wall, two rows of it, and what stands against it (over the wall's lower half)
    it.back_wall([(c, 'home-tokonoma_0_0' if ch == 'A' else f'home-wall-window-{plaster}_0_0' if ch == 'n'
                   else WALLS.get(ch, f'home-wall-{plaster}_0_0'), w) for ch, c, w in walls], 2)
    for ch, c, r, w, h in items:
        if ch in AT_WALL:
            it.stand(AT_WALL[ch][0], c, 0, w)
        else:
            key = FURNITURE[ch][0]
            it.prop(cloth.get(key, key), c, r, w, h)
    for i, (c, r) in enumerate(cushions):
        it.put('Over Floor', c, r, cloth['cushions'][0 if i % 3 else 1 + (i // 3) % 2])

    # the genkan: three cells of stone a step down from the floor - shoes left on one side,
    # the shoe cupboard on the other, the way in between them - and the mat you leave by
    for c in (g - 1, g, g + 1):
        it.put('Floor', c, FH, 'home-genkan_0_0')
        it.walk.add(it.cell(c, FH))
    side = -1 if mirror else 1
    it.prop(f"home-shoes-{'ab'[shoes]}_0_0", g - side, FH)
    it.prop('home-getabako_0_0', g + side, FH)
    # you arrive in the genkan, among the shoes; the mat is the cell below
    (arrive,) = it.doorway(g, host, front, n=1, fy=FH + 1, mat='home-genkan_0_0')
    it.put('Over Floor', g, FH + 1, 'home-doormat_0_0')

    # movement is confined to the lit floor, the genkan and the mat: the void needs no colliders
    room = it.room(name, shopEnabled=False)          # a home: nothing in it sells
    check_interior(name, it)
    return room, arrive


def build_lobby(name, host, front):
    """(room, arrival cell) for a tower's lobby: the one design, LOBBY."""
    it = Interior(LW, LH, ox=LX, oy=LY, w=ROOM_W, h=ROOM_H)
    it.floor(lambda c, r: f"lobby-floor_{'ab'[(c + r) % 2]}")
    assert len(LOBBY['wall']) == LW and len(LOBBY['floor']) == LH, 'the lobby does not fit its floor'
    # the back wall, two rows of it
    it.back_wall([(c, *LOBBY_WALL[ch]) for c, ch in enumerate(LOBBY['wall']) if ch in LOBBY_WALL], 2)
    for r, row in enumerate(LOBBY['floor']):
        assert len(row) == LW, row
        for c, ch in enumerate(row):
            if ch in LOBBY_FURNITURE:
                key, w = LOBBY_FURNITURE[ch]
                it.prop(key, c, r, w)

    # the entrance: one cell below the floor, the mat on it; you arrive just inside the doors
    (arrive,) = it.doorway(LOBBY['door'], host, front, n=1, mat='lobby-floor_a')
    it.put('Over Floor', LOBBY['door'], LH, 'lobby-mat_0_0')
    room = it.room(name, shopEnabled=False)          # nothing in it sells
    check_interior(name, it, flavour=LOBBY_FLAVOUR, wide=('lobby-lift',))
    return room, arrive


def build_shop(name, host, front, family):
    """(room, arrival cell) for the shop floor behind a shopfront of `family`: the one layout, SHOP."""
    _, menu, shelf = SHOP_TYPES[family]
    it = Interior(SW, SH, ox=SX, oy=SY, w=ROOM_W, h=ROOM_H)
    it.floor(lambda c, r: 'office-warm-autotile_center')
    assert len(SHOP['wall']) == SW and len(SHOP['floor']) == SH, 'the shop does not fit its floor'
    posters = ['office-poster-menu_0_0', 'office-poster-photo_0_0']
    it.back_wall([(c, 'office-wall-white_0_0', 1) for c in range(SW)], 1)      # one row of it, as a konbini's
    for c, ch in enumerate(SHOP['wall']):
        if ch == 'p':
            it.put('Other', c, -1, posters.pop(0))
    for r, row in enumerate(SHOP['floor']):
        assert len(row) == SW, row
        for c, ch in enumerate(row):
            if ch == 'S':
                it.prop(shelf, c, r)
            elif ch == 'P':
                it.prop('office-plant-a_0_0', c, r)
            elif ch == 'C':
                it.prop('office-counter2_0_0', c, r, 2)
                it.put('Tops', c + 1, r, 'office-register_0_0')

    # the way out: one cell below the floor, the mat on it
    (arrive,) = it.doorway(SHOP['door'], host, front, n=1, mat='office-warm-autotile_center')
    it.put('Over Floor', SHOP['door'], SH, 'lobby-mat_0_0')
    room = it.room(name,
                   shopEnabled=False,                # not a store: no stamp, and the shelves are only to look at...
                   shopMenu=menu)                    # ...but the counter sells this type's short list (Shop.VENUES)
    check_interior(name, it, flavour=SHOP_FLAVOUR, wide=())
    return room, arrive


def check_interior(name, it, flavour=FLAVOUR, wide=('home-kotatsu', 'home-irori')):
    """Every flavour object of a finished home (lobby, shop) can be bumped from the
    cell in front of it. (That every free cell can be walked to from the way in is
    Interior.room's own check; `it.reached` is what it found.)"""
    bumps = 0
    for xy, idx in it.b.L['Collidables'].items():
        key = rg._pal[idx]
        if key.startswith(flavour):
            x, y = map(int, xy.split(','))
            w, h = (2, 2) if key.startswith(wide) else (1, 2) if y < it.oy else (1, 1)
            assert all((x + dx, y + h) in it.reached for dx in range(w)), f'{name}: {key} at {xy} has no cell in front'
            bumps += 1
    assert bumps, f'{name}: nothing to bump'


# ---- finding the houses ---------------------------------------------------------
def find_houses(cfg, host, kind='house'):
    """Every house front in `host` (or, for kind 'lobby', every tower), in
    (y, x) order of its door, as dicts: key / name / door / doors / front /
    family / origin, plus `excluded` (not one: 'in use', 'shop') or `skipped`
    (one that must stay sealed, and why). `doors` are the door cells to open -
    one for a house; for a tower with a pair of doors, each that passes the
    rules - and `door` / `front` the first of them and the cell outside it.
    `kind` is a name in KINDS, or another generator's own row of the same
    shape (generate_pagodas.py finds its pagodas by these rules)."""
    import blog_to_npc as bn
    K = KINDS[kind] if isinstance(kind, str) else kind
    room = cfg['rooms'][host]
    found = []
    signs, stores = set(), set()
    for layer in room['layers']:
        for xy, idx in layer['tiles'].items():
            key = rg._pal[idx]
            x, y = map(int, xy.split(','))
            if kind == 'house' and key in SHOP_SIGNS:
                signs.add((x, y))
            elif kind == 'lobby' and key in STOREFRONTS:
                stores.add((x, y))
            elif layer['name'] == 'Collidables' and key in K['doors']:
                cells = [(x + dx, y + dy) for dx, dy in K['doors'][key]]
                dx, dy = K['doors'][key][0]
                found.append(dict(family=key.rsplit('_', 2)[0], origin=(x, y), door=cells[0], all_doors=cells,
                                  front=(cells[0][0], cells[0][1] + 1), span=(x - 1, x + 2 * dx + 1)))
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

    def sealed_because(door):
        """Why the door at `door` must stay sealed, or None."""
        front = (door[0], door[1] + 1)
        fkey = f'{front[0]},{front[1]}'
        if not (0 <= front[0] < width and 0 <= front[1] < height and fkey in floored and fkey not in blocked):
            return f'the cell in front of its door {front} cannot be stood on'
        if front in doors:
            return f'the cell in front of its door {front} is itself a door'
        if reach is not None and front not in reach:
            return f'the cell in front of its door {front} cannot be walked to'
        why = None
        for cell, what in ((door, 'on its door'), (front, 'in front of its door')):
            if cell in people:
                why = f'{people[cell]} stands {what} {cell}'
            elif cell in spots:
                why = f'the blog spot "{spots[cell]}" is {what} {cell}'
        return why

    houses, n = [], 0
    for h in found:
        door = h['door']
        target = next((doors[d] for d in h['all_doors'] if d in doors and not doors[d].startswith(K['prefix'])), None)
        if target:
            h['excluded'] = f'in use: its door leads to {target}'
        elif any(h['span'][0] <= x <= h['span'][1] and abs(y - door[1]) <= 1 for x, y in signs):
            h['excluded'] = 'a shop: it has a shop sign at its front'
        elif any(y == door[1] + 1 and h['span'][0] < x < h['span'][1] for x, y in stores):
            h['excluded'] = 'in use: the 7-Eleven standing across its door is its ground floor'
        else:
            n += 1
            h['key'] = f"{K['prefix']}{host}{n}"
            why = {d: sealed_because(d) for d in h['all_doors']}
            h['doors'] = [d for d in h['all_doors'] if not why[d]]
            if h['doors']:
                h['door'] = h['doors'][0]
                h['front'] = (h['door'][0], h['door'][1] + 1)
            else:
                h['skipped'] = why[door]
        houses.append(h)
    labels, ordinal = K.get('labels'), {}
    for h in houses:
        if 'key' not in h:
            continue
        if labels:                  # named by its type, numbered only where the town has several of that type
            label = labels[h['family']]
            ordinal[label] = ordinal.get(label, 0) + 1
            several = sum(1 for o in houses if 'key' in o and labels[o['family']] == label) > 1
            h['name'] = interiors.named(cfg, label, host, ordinal[label] if several else None)
        else:                       # by its kind, with the number in its key where the town has several
            h['name'] = interiors.named(cfg, K['label'], host, h['key'][len(K['prefix'] + host):] if n > 1 else None)
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


def apply(cfg, host, kind='house'):
    """(Re)build `host`'s houses (or, for kind 'lobby', its towers' lobbies) in
    cfg. Returns (built keys, report lines)."""
    K = KINDS[kind]
    marker, prefix, what = K['marker'], K['prefix'], K['what']
    room = cfg['rooms'][host]
    candidates = find_houses(cfg, host, kind)
    houses = [h for h in candidates if 'key' in h]
    if kind == 'house':
        pick_layouts(host, houses)
    built, lines = [], []
    for h in candidates:
        if 'excluded' in h:
            lines.append(f"not a {what}  {host} {h['family']} at {h['origin']} - {h['excluded']}")
    # rooms of this town from an earlier run that no house claims any more
    for key in [k for k, r in cfg['rooms'].items() if (r.get(marker) or {}).get('host') == host]:
        if key not in {h['key'] for h in houses if 'skipped' not in h}:
            was = cfg['rooms'][key][marker]
            for cell in was.get('doors') or [was['door']]:
                rg.shut_door(room, cell, prefix)
            del cfg['rooms'][key]
    for h in houses:
        if 'skipped' in h:
            for cell in h['all_doors']:
                rg.shut_door(room, cell, prefix)
            lines.append(f"skipped  {h['key']} ({h['family']}, door {h['door']}) - {h['skipped']}")
            continue
        if kind == 'house':
            interior, arrive = build_interior(h['name'], host, h['front'], h['layout'], seed_of(host, h['door']))
            interior[marker] = {'host': host, 'door': list(h['door']), 'layout': h['layout']}
            said = f"the {h['layout']} room"
        elif kind == 'shop':
            interior, arrive = build_shop(h['name'], host, h['front'], h['family'])
            interior[marker] = {'host': host, 'door': list(h['door']), 'type': SHOP_TYPES[h['family']][1]}
            said = f"the {SHOP_TYPES[h['family']][1]} shop floor"
        else:
            interior, arrive = build_lobby(h['name'], host, h['front'])
            interior[marker] = {'host': host, 'door': list(h['door']), 'doors': [list(d) for d in h['doors']]}
            said = 'the lobby' + (f", {len(h['doors'])} doors" if len(h['doors']) > 1 else '')
        cfg['rooms'][h['key']] = interior
        for cell in h['all_doors']:                          # a door of a pair that may not open stays shut
            if cell not in h['doors']:
                rg.shut_door(room, cell, prefix)
        for cell in h['doors']:
            # unseal the doorway and wire it in, replacing the door's transporter where it already sits
            # (append only a new one): a re-run on an unchanged world leaves config.json byte-identical
            rg.open_door(room, cell, h['key'], arrive)
        built.append(h['key'])
        lines.append(f"built    {h['key']} \"{h['name']}\" - {h['family']}, door {h['door']}, {said}")
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
    named = rg.cli(__doc__, argv, ('--variants', '--dry-run', '--lobbies', '--shops'))   # --help: usage, nothing run
    cfg = rg.load_config()
    if '--variants' in argv:
        print(json.dumps({'tilePalette': cfg['tilePalette'], 'variants': variants()}))
        return 0
    dry, lobbies = '--dry-run' in argv, '--lobbies' in argv
    only = 'lobby' if lobbies else 'shop' if '--shops' in argv else None
    have = {kind: sorted({r[K['marker']]['host'] for r in cfg['rooms'].values() if r.get(K['marker'])})
            for kind, K in KINDS.items()}
    # named towns: their houses, or with --lobbies their towers, or with --shops their shops;
    # no town: everything there is, of every kind
    jobs = [(only or 'house', t) for t in named] if named else \
        [(kind, t) for kind in ([only] if only else KINDS) for t in have[kind]]
    unknown = [t for t in named if t not in cfg['rooms'] or cfg['rooms'][t].get('interior')
               or t in cfg.get('stations', {})]
    if unknown:
        print(f'not a town: {unknown}')
        return 2
    if not jobs:
        print('no town has houses yet: name the towns to build, e.g. generate_houses.py Asahikawa')
        return 0
    built = []
    for kind, host in jobs:
        keys, lines = apply(cfg, host, kind)
        built += keys
        print('\n'.join(lines) if lines else f"{host}: no {KINDS[kind]['what']}s")
    towns = sorted({host for _, host in jobs})
    if dry:
        print(f"\ndry run: {len(built)} interior(s) would be written, nothing was.")
        return 0
    rg.save_config(cfg)
    print(f"\n{len(built)} {only or 'house'} interior(s) written. Now run config_to_tiled, then play.js lint, for:")
    print('  ' + ' '.join(built + towns))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
