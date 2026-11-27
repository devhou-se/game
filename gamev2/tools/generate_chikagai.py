#!/usr/bin/env python3
"""generate_chikagai.py — the underground arcade (chikagai) under a town.

Japanese cities run a shopping arcade under their main streets, reached by
stairs from the pavement. A town in tools/chikagai.py gets one: its own
generator stamps the street entrances (the `chikagai-entrance-snow` prefab,
sealed) where that table says, and this builds the arcade and opens them:
  * rooms.Chikagai<Host> is rebuilt from scratch (any NPCs it holds are kept);
  * each entrance's two door cells are unsealed and a hidden transporter wired
    onto each, replaced in place so a re-run leaves config.json byte-identical;
  * each exit of the arcade leads back to the cell in front of its entrance.
A town generator that rebuilds the host seals the entrances again and knows
nothing of these doors: roomgen.save_config puts them back (OWNED_DOORS).

The arcade is a cross of corridors (the table gives the hall and its two
stems): shopfronts set into the hall's north wall behind a tan apron, the
stairs up under yellow exit signs, tactile paving from every exit to the line
down the hall, pillars, benches and planters along it, coin lockers and a
floor map at the foot of the north stairs, capsule-toy machines at the hall's
west end. The bakery, the coffee counter and the standing bar sell
(Shop.VENUES); the other fronts, the machines and the map say a line when
bumped (src/utils/Interactions.js). Art: tools/generate_chikagai_art.py and the
station interior's.

Run from gamev2/:  python3 tools/generate_chikagai.py [Host ...]     (--help: this text, nothing run)
With no host it rebuilds every town in the table. Then:
    python3 tools/config_to_tiled.py Chikagai<Host> <Host>
    node tools/play.js lint Chikagai<Host> <Host>
"""
import sys

import chikagai
import interiors
import roomgen as rg
from interiors import Interior

ARGS = rg.cli(__doc__, sys.argv[1:])   # --help: usage, nothing run
cfg = rg.load_config()

PREFIX = rg.CHIKAGAI_PREFIX
HOSTS = ARGS or list(chikagai.TOWNS)
unknown = [h for h in HOSTS if h not in chikagai.TOWNS or h not in cfg['rooms']]
assert not unknown, f'no arcade is planned under: {unknown}'


def build(host):
    town = chikagai.TOWNS[host]
    hw, hh = town['hall']
    north, south = town.get('north'), town.get('south')
    OX, OY = 1, 3 + (north[2] if north else 0)                 # room cell of the hall's cell (0, 0)
    W, H = hw + 2, OY + hh + (south[2] if south else 0) + 3
    it = Interior(hw, hh, ox=OX, oy=OY, w=W, h=H)             # the hall; the stems join its walk below
    b = it.b                                                   # everything past the shell is in room cells
    s = lambda piece: f'chika-{piece}_0_0'

    # ---- floor: cream tile, a tan apron along the shops ---------------------------------
    it.floor(lambda fx, fy: s('floor-a' if fy else 'floor-b'))
    stems = set()
    if north:
        stems |= {it.cell(north[0] + x, -y - 1) for x in range(north[1]) for y in range(north[2])}
    if south:
        stems |= {it.cell(south[0] + x, hh + y) for x in range(south[1]) for y in range(south[2])}
    for x, y in stems:
        b.put('Floor', x, y, s('floor-a'))
    it.walk |= stems
    floor = set(it.walk)                                       # the cross of corridors, before its exits join it
    top_of = lambda x: min(y for fx, y in floor if fx == x)    # a column's first floor row
    bottom_of = lambda x: max(y for fx, y in floor if fx == x)

    # ---- exits: where each is, its door cells and where you arrive from the street: every
    #      exit leads to the cell in front of its entrance, and both its cells bring you in
    #      on the same one -------------------------------------------------------------------
    exits, doors = {}, set()
    for slug, e in town['exits'].items():
        wall, fx = e['at']
        x, south_wall = OX + fx, wall == 'south'
        y = bottom_of(x) + 1 if south_wall else top_of(x) - 1
        sx, sy = e['street']
        inside = it.doorway(fx, host, (sx, sy + 3), fy=y - OY, inward=-1 if south_wall else 1)
        exits[slug] = {'cells': [(x, y), (x + 1, y)], 'arrive': inside[0], 'south': south_wall}
        doors |= set(exits[slug]['cells'])

    # ---- walls: the face of every north wall, the tops of the others ----------------------
    face = {(x, y - d) for x, y in floor if (x, y - 1) not in floor for d in (1, 2)}
    wide = {x + dx for e in exits.values() if not e['south'] for x, y in e['cells'][:1] for dx in (-1, 0, 1, 2)}
    shops = {OX + fx + dx: kind for fx, kind in town['shops'] for dx in range(3)}
    posters = 0
    for x in sorted({x for x, _ in face}):
        y = top_of(x) - 2
        if x in wide:
            continue                                            # an exit's stairs, laid below
        if x in shops:
            if (x - OX, shops[x]) in town['shops']:
                b.place('Collidables', x, y, s(f'shop-{shops[x]}'), rg.block(3, 2))
            continue
        pier = x - 1 in shops and x + 1 in shops                # a pier between two shopfronts carries an advert
        b.place('Collidables', x, y, s(f"wall-poster-{'ab'[posters % 2]}" if pier else 'wall'), rg.block(1, 2))
        posters += pier
    for slug, e in exits.items():
        (x, y), (x1, _) = e['cells']
        if e['south']:
            b.put('Floor', x, y, s('exit-south-w'))
            b.put('Floor', x1, y, s('exit-south-e'))
            b.put('Tops', x - 1, y - 2, s(f'sign-{slug}'))
        else:
            b.place('Over Floor', x - 1, y - 1, s(f'exit-{slug}'),
                    [(dx, 0) for dx in range(4)] + [(0, 1), (3, 1)])
    for x in range(W):
        for y in range(H):
            if (x, y) in floor or (x, y) in face or (x, y) in doors:
                continue
            top, left, right = (x, y - 1) in floor, (x - 1, y) in floor, (x + 1, y) in floor
            piece = ('front-w' if right else 'front-e' if left else 'front') if top else \
                    'side-w' if right else 'side-e' if left else None
            if piece:
                b.put('Floor', x, y, s(piece))

    # ---- tactile paving: a line down the hall, a spur to every exit ------------------------
    line = OY + 2
    spurs = {e['arrive'][0]: e for e in exits.values()}
    tactile = {}
    for x in range(min(spurs), max(spurs) + 1):
        tactile[x, line] = 'h'
    for x, e in spurs.items():
        y0, y1 = sorted((e['arrive'][1], line))
        for y in range(y0, y1 + 1):
            tactile[x, y] = 'v'
        tactile[x, line] = tactile[e['arrive']] = 'stop'
    for (x, y), kind in tactile.items():
        b.put('Over Floor', x, y, f'station-tactile-{kind}_0_0')

    # ---- along the hall, south of the line: pillars, with a bench or planters between -------
    row = OY + hh - 2                                       # the feet of everything standing here
    mouth = set(range(OX + south[0] - 1, OX + south[0] + south[1] + 1)) if south else set()
    free = lambda x0, w: all(x not in mouth and (x, row) not in tactile and (x, row - 1) not in tactile
                             for x in range(x0 - 1, x0 + w + 1))
    n = 0
    for x in range(OX + 3, OX + hw - 3, 8):
        if free(x, 1):
            b.place('Collidables', x, row - 1, 'station-pillar_0_0', [(0, 1)])
        if free(x + 3, 2):
            key = ('station-bench_0_0', 'station-planter-a_0_0', 'station-bench_0_0', 'station-planter-b_0_0')[n % 4]
            b.place('Collidables', x + 3, row - 1, key, [(0, 1), (1, 1)])
            n += 1

    # ---- at the foot of the north stairs: coin lockers and the floor map; the capsule
    #      machines against the hall's west wall ----------------------------------------------
    if north:
        x0, x1, y = OX + north[0], OX + north[0] + north[1] - 1, OY - north[2]
        b.place('Collidables', x0, y, 'station-lockers_0_0', rg.block(2, 2))
        b.place('Collidables', x1, y, s('map'), [(0, 1)])
    if (OX, OY - 1) in face and OX not in shops and OX + 1 not in shops and not {OX, OX + 1} & wide:
        b.place('Collidables', OX, OY, s('gacha'), rg.block(2, 2))

    # ---- the room: the floor and the stairs are its outline; the walls round it need no colliders
    street = [[sx + dx, sy + dy] for e in town['exits'].values() for sx, sy in [e['street']]
              for dx, dy in chikagai.ENTRANCE_DOORS]
    room = it.room(town['name'], npcs=cfg['rooms'].get(PREFIX + host, {}).get('npcs', []),
                   chikagai={'host': host, 'doors': street},      # the marker roomgen.owned_door reads
                   shopEnabled=False)       # not a store: no stamp; three of its counters sell (Interactions)

    # Interior.room has walked to every free cell from one exit or another; here it is all one arcade
    walk = it.reached
    assert interiors.reachable(walk, [exits[next(iter(exits))]['arrive']]) == walk, f'{host}: an exit is cut off from the others'
    for fx, kind in town['shops']:
        assert all((OX + fx + dx, OY) in walk for dx in range(3)), f'{host}: the {kind} front at {fx} has no cell in front'
    return room, exits


built = []
for host in HOSTS:
    key = PREFIX + host
    room, exits = build(host)
    cfg['rooms'][key] = room
    town_room = cfg['rooms'][host]
    for slug, e in chikagai.TOWNS[host]['exits'].items():
        sx, sy = e['street']
        for dx, dy in chikagai.ENTRANCE_DOORS:
            x, y = sx + dx, sy + dy
            assert rg.house_door_at(town_room, x, y, rg.OWNED_DOORS[PREFIX][1]), \
                f'{host}: no arcade entrance stands at {sx},{sy} (its generator stamps chikagai.TOWNS)'
            rg.open_door(town_room, (x, y), key, exits[slug]['arrive'])     # unsealed, wired in place
    built.append(key)
    print(f"built  {key} - {room['name']}: {room['worldWidth'] // 64}x{room['worldHeight'] // 64}, "
          f"{len(exits)} exits ({', '.join(exits)})")

rg.save_config(cfg)
print('\nNow run config_to_tiled, then play.js lint, for:')
print('  ' + ' '.join(built + HOSTS))
