#!/usr/bin/env python3
"""generate_devhouses.py — the two Devhouses, a room per floor (issue #69).

The houses the trips stayed in, built from their real floor plans:

  Tokyo   six floors, in Minato: the `devhouse-tokyo` block on the paved square
          under Tokyo Tower's feet (the district `Park`, a ported map: the
          building was stamped there once, tools/stamp_prefab.py). The ground
          floor and the one above are not ours - a locked door and the stairs,
          on the same cells as the stair hall of the floors over them - then
          3F the kitchen and the long table, 4F and 6F beds, 5F the tatami
          room and the bath.
  Osaka   four floors on Dotonbori: the `devhouse-osaka` townhouse beside Don
          Takote (tools/generate_osaka.py stamps it, sealed). 1F the kitchen
          and the tall table, 2F and 3F bedrooms, and on top a tatami room
          that opens onto a zen garden on the roof.

Each floor is one interior on tools/interiors.py: rooms.Devhouse<City><n>F,
named "Devhouse <n>F · <City>" (a phone's HUD bar shows the part before the
dot: which floor you are on). The floors are data, FLOORS below: a grid of
characters per floor, a string for its back wall and one for the row below it.

Stairs are hidden exits laid with a stair tile, the way a door mat is: `u`
leads to the floor above, `d` to the one below. Every stair cell has exactly
one free cell directly north or south of it, its ARRIVAL cell. Taking `u` on
floor N puts you on the arrival cell of `d` on floor N+1, and taking that `d`
puts you on the arrival cell of `u` on floor N. An arrival cell is never an
exit itself.

THE HELD-KEY RULE. A room change does not let go of a held key: after the
fade the same step is taken again from the cell you arrived on. So the two
ends of a flight are entered in opposite directions, and for every stair and
street door, and every direction it can be entered from, that step repeated
from the arrival cell at the other end must not land on another exit. (With
`u` and `d` side by side on the same row, holding DOWN on the ground floor's
stair took you up and straight back down, for ever.) Move a stair only with
tools/tests/devhouse.test.js open: it checks the rule from config.json.

Only the street door is a kept door (roomgen.OWNED_DOORS): the ground floor's
marker carries `door`, the other floors' markers must not.

Art: the home kit (tools/generate_house_art.py) and tools/generate_devhouse_art.py.
The roof garden is `lanternLight`: at night it dims and its stone lantern
glows (src/utils/Glows.js); the other floors are lit rooms.

Run from gamev2/:  python3 tools/generate_devhouses.py     (--help: this text, nothing run)
Then:  python3 tools/config_to_tiled.py Park Osaka <the ten rooms it lists>
       node tools/play.js lint Park Osaka <the same>
A re-run leaves config.json byte-identical.
"""
import sys

import roomgen as rg
from interiors import Interior

rg.cli(__doc__, sys.argv[1:])           # --help: usage, nothing run
cfg = rg.load_config()

# city: (host room, the building's sprite, its floors' letter in FLOORS, how many floors)
CITIES = {'Tokyo': ('Park', 'devhouse-tokyo_0_0', 'T', 6),
          'Osaka': ('Osaka', 'devhouse-osaka_0_0', 'O', 4)}


def shell(city, n):
    """The Interior of floor `n`: (fw, fh, ox, oy, room height). Tokyo's two stair
    floors are the stair hall of the floors above, on the same room cells."""
    if city == 'Osaka':
        return 9, 10, 5, 4, 17
    return (14, 8, 3, 4, 15) if n >= 3 else (2, 4, 15, 8, 15)


# ---- the legend ---------------------------------------------------------------------------
# 1x1, solid:
ONE = {'-': 'devhouse-wall-h_0_0', '#': 'devhouse-stairwell_0_0',
       'n': 'devhouse-chair-n_0_0', 's': 'devhouse-chair-s_0_0', 'w': 'devhouse-chair-w_0_0',
       'e': 'devhouse-chair-e_0_0', 'o': 'devhouse-stool_0_0', 't': 'devhouse-side-table_0_0',
       'c': 'devhouse-armchair_0_0', 'p': 'home-plant_0_0', 'l': 'home-andon_0_0', 'g': 'home-getabako_0_0',
       'b': 'devhouse-basin_0_0', 'x': 'devhouse-toilet_0_0', 'h': 'devhouse-shower_0_0',
       'm': 'devhouse-washer_0_0', 'r': 'devhouse-rock_0_0', 'y': 'devhouse-shrub_0_0',
       'i': 'devhouse-lantern_0_0', 'q': 'devhouse-garden-seat_0_0', 'k': 'devhouse-water-bowl_0_0'}
# more than a cell: the capital is its top-left cell, `+` the rest of its footprint (w, h)
BIG = {'B': ('home-bed_0_0', 1, 2), 'F': ('futon', 1, 2), 'Y': ('devhouse-bunk_0_0', 1, 2),
       'J': ('devhouse-sofa_0_0', 1, 3), 'Q': ('lobby-sofa_0_0', 2, 1), 'T': ('devhouse-table-wide_0_0', 4, 1),
       'M': ('devhouse-table-tall_0_0', 1, 3), 'H': ('devhouse-table-small_0_0', 1, 2),
       'X': ('devhouse-counter_0_0', 2, 1), 'A': ('devhouse-bath_0_0', 1, 2), 'C': ('devhouse-clothes-rack_0_0', 1, 2)}
# tall pieces walked behind: the foot on their row, drawn from the row above (key, width)
TALL = {'K': ('home-kitchen_0_0', 2), 'R': ('home-fridge_0_0', 1), 'D': ('home-tansu_0_0', 1)}
FUTONS = ['home-futon-blue_0_0', 'home-futon-rose_0_0']
CUSHIONS = ['home-zabuton-indigo_0_0', 'home-zabuton-red_0_0', 'home-zabuton-green_0_0']
FREE = '.z:'                            # what you can stand on: bare floor, a cushion, a stepping stone
WALLS = '|-#'                           # what a partition runs into
# the back wall, a 1x2 piece a column
BACK = {'p': 'home-wall-sand_0_0', 'n': 'home-wall-window-sand_0_0', 'u': 'home-wall-fusuma_0_0',
        's': 'home-wall-shoji_0_0', 'L': 'devhouse-door_0_0', 'f': 'devhouse-fence_0_0'}
STAIR = {'u': 'devhouse-stairs-up_0_0', 'd': 'devhouse-stairs-down_0_0'}

# What the floor is laid with, where it is not boards: (kind, x0, y0, x1, y1), floor cells.
WET = [('tile', 12, 0, 13, 2)]          # Tokyo's wet rooms, at the head of the stair hall
ZONES = {
    'T3F': WET, 'T4F': WET, 'T5F': WET + [('tatami', 0, 0, 6, 7)], 'T6F': WET,
    'O1F': [('tile', 0, 0, 2, 2)],
    'O2F': [('tile', 0, 0, 2, 2), ('tatami', 0, 4, 2, 5), ('tatami', 0, 7, 2, 9)],
    'O3F': [('tile', 0, 0, 2, 2), ('tile', 7, 9, 8, 9), ('tatami', 4, 0, 8, 2), ('tatami', 0, 6, 2, 9)],
    'O4F': [('gravel', 0, 0, 8, 3), ('tatami', 0, 5, 4, 9)],
}

FLOORS = {
 'T1F': dict(wall='Lp', rows=['.p', '..', '..', '..'], front='=u'),
 'T2F': dict(wall='Lp', rows=['..', '#.', 'd.', '..'], front=' u'),
 'T3F': dict(wall='ppnppppppnpppp', front='             u', rows=[
    '....K+RK+..|bx',
    'J.............',
    '+..nnnn....|..',
    '+..T+++....|--',
    '...ssss.......',
    '...........|#.',
    'p..oooo....|d.',
    '...X+X+....|..']),
 'T4F': dict(wall='ppnpppnppppppp', front='             u', rows=[
    'D.Y..Q+....|bx',
    '..+...........',
    '...........|..',
    '...........|--',
    '..............',
    '...........|#.',
    '.B..B..B...|d.',
    '.+..+..+..p|..']),
 'T5F': dict(wall='uuuupppppLpppp', front='             u', rows=[   # L: "Staff Only"
    'D......|...|bA',
    '.......|.....+',
    '.F.F.F.|...|.x',
    '.+.+.+.....|--',
    '.......|......',
    '..z.z..|...|#.',
    '.......|...|d.',
    'l.....p|..p|..']),
 'T6F': dict(wall='ppnppppnpppppp', front='              ', rows=[   # two single beds end to end
    'B..|.......|bm',
    '+.............',
    'B..|...wHe.|..',
    '+..|...w+e.|--',
    '..............',
    '...........|#.',
    '...........|d.',
    'X+X+X+...p.|..']),
 'O1F': dict(wall='pnppppppp', front='     =   ', rows=[
    'hb.|K+R..',
    '...|.....',
    'x.......g',
    '----...|#',
    '...n...|#',
    'D.wMe..|#',
    '..w+e..|#',
    '..w+e..|u',
    'p..s.....',
    'p........']),
 'O2F': dict(wall='pnppnpppp', front='         ', rows=[
    'hb.|....p',
    '...|.....',
    'x......|d',
    '----...|#',
    'B.l|..c|#',
    '+.....t|#',
    '----..c|#',
    'B..|...|u',
    '+........',
    '..l|.....']),
 'O3F': dict(wall='pnppnpppp', front='         ', rows=[
    'hb.|.B..t',
    '...|.+...',
    'x..|....l',
    '--.|-.---',
    'm........',
    '----..|du',
    't..|..|##',
    'B.....|##',
    '+..|..|--',
    '..l|....x']),
 'O4F': dict(wall='fffffffff', front='         ', rows=[
    'yyr....:y',
    '.:..k..:y',
    '.:.....:.',
    'i::::qtq.',
    '-.-------',
    '.ztz.|bC#',
    'B.B.B|.+#',
    '+.+.+|..#',
    '........d',
    'l...p|...']),
}


def room_key(city, n):
    return f'{rg.DEVHOUSE_PREFIX}{city}{n}F'


def site(city):
    """(door cell, the cell in front of it) of a city's Devhouse, in its host room."""
    host, sprite = CITIES[city][:2]
    found = rg.find_sprites(cfg['rooms'][host], [sprite], rg.DOOR_LAYERS)
    assert len(found) == 1, f'{host}: expected one {sprite}, found {[(x, y) for x, y, _ in found]}'
    x, y, _ = found[0]
    dx, dy = rg.DEVHOUSE_DOORS[sprite][0]
    return (x + dx, y + dy), (x + dx, y + dy + 1)


def exits(city, n):
    """Pass 1. The exits of a floor: {'u' / 'd' / '=': (fx, fy, the ROOM cell you arrive on beside it)}."""
    code = f'{CITIES[city][2]}{n}F'
    spec = FLOORS[code]
    fw, fh, ox, oy, _ = shell(city, n)
    rows = spec['rows'] + [spec['front']]
    assert len(spec['rows']) == fh and len(spec['wall']) == fw and all(len(r) == fw for r in rows), f'{code}: not {fw}x{fh}'
    at = lambda fx, fy: rows[fy][fx] if 0 <= fy < fh and 0 <= fx < fw else ' '
    found = {}
    for fy, row in enumerate(rows):
        for fx, ch in enumerate(row):
            if ch in 'ud=':
                beside = [(fx, y) for y in (fy - 1, fy + 1) if at(fx, y) in FREE]
                assert ch not in found and len(beside) == 1, f'{code}: {ch} at {fx},{fy} needs one free cell north or south: {beside}'
                found[ch] = (fx, fy, (ox + beside[0][0], oy + beside[0][1]))
            else:
                assert fy < fh or ch == ' ', f'{code}: {ch!r} on the row below the floor'
    return found


def build(city, n, ways, door, front):
    """Pass 2. The room of floor `n`: `ways` is exits() of every floor of the house,
    `door` and `front` its street door and the cell outside it, in the host."""
    host, _, letter, top = CITIES[city]
    code = f'{letter}{n}F'
    spec = FLOORS[code]
    rows = spec['rows']
    fw, fh, ox, oy, height = shell(city, n)
    it = Interior(fw, fh, ox=ox, oy=oy, w=20, h=height)
    at = lambda fx, fy: rows[fy][fx] if 0 <= fy < fh and 0 <= fx < fw else ' '

    # ---- the floor: boards, and what the plan lays elsewhere ---------------------------------
    zone = {cell: kind for kind, x0, y0, x1, y1 in ZONES.get(code, ()) for cell in rg.rect(x0, y0, x1, y1)}

    def laid(fx, fy):
        kind = zone.get((fx, fy))
        if at(fx, fy) == ':':
            return 'devhouse-stepping-stone_0_0'
        if kind == 'tatami':        # two-cell mats, each row half a mat along from the last
            return f"home-tatami-green_{'w' if (fx + fy) % 2 == 0 else 'e'}"
        return f'devhouse-{kind}_0_0' if kind else 'home-wood-floor_0_0'
    it.floor(laid)

    # ---- the back wall, two rows of it ----------------------------------------------------------
    it.back_wall([(fx, BACK[ch], 1) for fx, ch in enumerate(spec['wall'])], 2)

    # ---- what stands on the floor -------------------------------------------------------------------
    covered, futons, cushions = set(), 0, 0
    for fy, row in enumerate(rows):
        for fx, ch in enumerate(row):
            if ch == '|':
                # a partition running north-south: where one running east-west meets it, it is that
                # wall's face; where it stops short of the next wall, its own end face
                if '-' in (at(fx - 1, fy), at(fx + 1, fy)):
                    it.prop(ONE['-'], fx, fy)
                else:
                    it.prop(f"devhouse-wall-v{'' if at(fx, fy + 1) in WALLS else '-end'}_0_0", fx, fy)
            elif ch in ONE:
                it.prop(ONE[ch], fx, fy)
            elif ch in BIG:
                key, w, h = BIG[ch]
                if key == 'futon':
                    key, futons = FUTONS[futons % 2], futons + 1
                it.prop(key, fx, fy, w, h)
                covered |= {(fx + dx, fy + dy) for dx in range(w) for dy in range(h)} - {(fx, fy)}
            elif ch in TALL:
                key, w = TALL[ch]
                it.stand(key, fx, fy, w)
                covered |= {(fx + dx, fy) for dx in range(1, w)}
            elif ch == 'z':
                it.put('Over Floor', fx, fy, CUSHIONS[cushions % 3])
                cushions += 1
            else:
                assert ch in FREE + 'ud+', f'{code}: {ch!r} at {fx},{fy} is not in the legend'
    plus = {(fx, fy) for fy, row in enumerate(rows) for fx, ch in enumerate(row) if ch == '+'}
    assert plus == covered, f'{code}: footprints and their + cells differ: {sorted(plus ^ covered)}'

    # ---- the ways out, last: the stairs, and on the ground floor the street -------------------------
    for ch, (fx, fy, arrive) in ways[n].items():
        if ch == '=':
            it.doorway(fx, host, front, n=1, fy=fy, mat='home-genkan_0_0')
            it.put('Over Floor', fx, fy, 'home-doormat_0_0')
            continue
        other = n + 1 if ch == 'u' else n - 1
        assert 1 <= other <= top, f'{code}: a stair to floor {other}'
        # you step off the far end of the flight: beside the other floor's stair back
        land = ways[other]['d' if ch == 'u' else 'u'][2]
        it.doorway(fx, room_key(city, other), land, n=1, fy=fy, inward=arrive[1] - (oy + fy), mat=STAIR[ch])

    marker = {'host': host, 'floor': n}
    if n == 1:
        marker['door'] = list(door)      # the street door, and only that: the stairs are not kept doors
    flags = {'lanternLight': True} if code == 'O4F' else {}      # the roof garden has a night
    return it.room(f'Devhouse {n}F · {city}', npcs=cfg['rooms'].get(room_key(city, n), {}).get('npcs', []),
                   shopEnabled=False, devhouse=marker, **flags)


built = []
for city, (host, _, _, top) in CITIES.items():
    door, front = site(city)
    ways = {n: exits(city, n) for n in range(1, top + 1)}
    for n in range(1, top + 1):
        assert set(ways[n]) == {'u', 'd', '='} - ({'d'} if n == 1 else {'='}) - ({'u'} if n == top else set()), \
            f'{city} {n}F: its exits are {sorted(ways[n])}'
        cfg['rooms'][room_key(city, n)] = build(city, n, ways, door, front)
        built.append(room_key(city, n))
    arrive = ways[1]['='][2]
    rg.open_door(cfg['rooms'][host], door, room_key(city, 1), arrive)      # wired in place: a re-run changes nothing
    print(f'door   {host} {door} -> {room_key(city, 1)} {arrive}, back out on {front}; {top} floors')

rg.save_config(cfg)
print('built  the Devhouses. Now run config_to_tiled, then play.js lint, for:')
print(f"  {' '.join(sorted({host for host, *_ in CITIES.values()}))} {' '.join(built)}")
