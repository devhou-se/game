#!/usr/bin/env python3
"""generate_pagodas.py — the inside of every pagoda (issue #214).

A pagoda in a town is `pagoda-floor` (the five-storey one's foot) or
`red-pagoda-small-base` (a small red one's) on the Collidables layer: until
this ran it was sealed. This builds one interior room per pagoda and opens the
pagoda's door onto it, the way generate_shrines.py does for a shrine's hall:
  * rooms.Pagoda<Host><n> is rebuilt from scratch (any NPCs it holds are kept);
    n counts the town's pagodas in (y, x) order of their doors, sealed ones too;
  * the host's door cells are unsealed and a hidden transporter wired onto each,
    replaced in place so a re-run leaves config.json byte-identical;
  * the room's mat leads back to the cell in front of the (first) door.
A pagoda whose door cannot be walked up to stays sealed (generate_houses.py's
rules: find_houses), and so does one whose door already leads somewhere - the
palace's end towers are `pagoda-floor` too, laid flat on Over Floor, and are
the palace hall's. Nothing else in the host is touched. A town generator that
rebuilds the host seals the pagoda again and knows nothing of this door:
roomgen.save_config puts it back (OWNED_DOORS / keep_house_doors).

What is inside (art: tools/generate_pagoda_art.py): the whole tower cut open,
in one room. Every storey is a floor of its own, one above the other and
narrower as they go up, with the roofs' skirts outside them, the top roof and
the spire over the last, and the dark all round. On each storey: the back wall
(two rows), five rows of boards, and the floor's cut edge. The heart pillar
stands in the middle of every floor (you walk behind it; only its foot is
solid); on the ground floor it rises out of a dais with four small Buddhas
round it, an offering box before them and a candle either side. A steep stair
climbs each back wall, on alternate sides, through the floor above and out of
a hatch in its boards; you walk up and down it, there is no door between
storeys. The middle storeys keep sutra chests or a wall of tiny gilt Buddhas,
the top one has a slatted window; a lantern hangs on every storey (the room is
`lanternLight`: it dims at night and its lights glow). The offering box and
the fittings answer a bump (rules in src/utils/Interactions.js).

The walls, the edges, the eaves, the roof and the stair are flat (Floor / Over
Floor) and have no colliders: the room's boundary is the outline of the
floors, the stairs and the mat, so nothing drawn round them can be walked on
and nothing hides you on a stair. The room is built on the shared shell
(tools/interiors.py): the shell's floor is the ground floor's boards, and the
storeys over it and the stairs between them are added to its walk.

Run from gamev2/:  python3 tools/generate_pagodas.py [Host ...] [--dry-run]     (--help: this text, nothing run)
With no host it rebuilds the pagodas of the towns that already have one open
(what check_generators.py runs); name a host to open its pagodas for the first
time; --dry-run lists what would be built and writes nothing. Then:
                   python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
"""
import sys

import generate_houses as gh
import interiors
import roomgen as rg
from interiors import Interior

ARGS = rg.cli(__doc__, sys.argv[1:], flags=('--dry-run',))   # --help: usage, nothing run
DRY = '--dry-run' in sys.argv[1:]
cfg = rg.load_config()

PREFIX, MARKER = rg.PAGODA_PREFIX, 'pagoda'
# what generate_houses.find_houses looks for: a row shaped like one of its KINDS
KIND = dict(prefix=PREFIX, marker=MARKER, label='Pagoda', what='pagoda', doors=rg.PAGODA_DOORS)

W, CX = 21, 10                                   # the room's width; the column of the heart pillar
# storeys -> the width of each floor, from the ground up
FLOORS = {5: (9, 9, 7, 7, 5), 3: (9, 7, 5)}
STOREYS = {'pagoda-floor': 5, 'red-pagoda-small-base': 3}
# (host, the pagoda's first door cell) -> storeys, where its tower outdoors is taller than its foot's kind
TALLER = {('Park', (34, 17)): 5}
FITTINGS = ('kyozo', 'senbutsu')                 # a middle storey's back wall: sutra chests, the thousand Buddhas


def wired_hosts():
    """Hosts that already have a pagoda open."""
    return sorted({r[MARKER]['host'] for r in cfg['rooms'].values() if r.get(MARKER)})


HOSTS = ARGS or wired_hosts()
unknown = [h for h in HOSTS if h not in cfg['rooms']]
assert not unknown, f'no such room: {unknown}'


def s(piece):
    return f'pagoda-in-{piece}_0_0'


def build(p):
    """The room for pagoda `p` (a find_houses dict with `name` and `storeys`),
    and the cell you arrive on."""
    S = p['storeys']
    widths = FLOORS[S]
    H = 7 + 8 * S                                 # six rows of roof and spire, eight a storey, one under the mat
    seed = gh.seed_of(p['host'], p['door'])

    def top(k):
        """The first row of storey k (0 is the ground): its back wall's upper row."""
        return 6 + 8 * (S - 1 - k)

    def stair_x(k):
        """The column of the stair from storey k up to k + 1: east, west, east..."""
        return CX + 2 if k % 2 == 0 else CX - 2

    def board(x, y, k):
        return s('board-a' if (x * 3 + y * 5 + x // 3 + k) % 4 else 'board-b')

    # the shell is the ground floor's boards; the storeys over it and the stairs join its walk below
    it = Interior(widths[0], 5, ox=CX - widths[0] // 2, oy=top(0) + 2, w=W, h=H)
    b = it.b                                      # everything past the shell is in room cells
    it.floor(lambda fx, fy: board(*it.cell(fx, fy), 0))
    bumps = []                                    # (piece, the cell it is bumped from)

    def on_wall(x, t, piece, w):
        """A fitting on the back wall, two rows tall: bumped from the floor under it."""
        b.prop(s(piece), x, t, w, 2)
        bumps.extend((piece, (x + dx, t + 2)) for dx in range(w))

    for k, w in enumerate(widths):
        t, x0, x1 = top(k), CX - w // 2, CX + w // 2
        # ---- the back wall, the side walls, the boards -------------------------------------------
        for x in range(x0, x1 + 1):
            b.put('Floor', x, t, s('wall-head'))
            b.put('Floor', x, t + 1, s('wall'))
            for y in range(t + 2, t + 7) if k else ():
                b.put('Floor', x, y, board(x, y, k))
                it.walk.add((x, y))
        for x, side in ((x0 - 1, 'w'), (x1 + 1, 'e')):
            b.put('Floor', x, t, s(f'wall-head-{side}'))
            b.put('Floor', x, t + 1, s(f'wall-{side}'))
            for y in range(t + 2, t + 7):
                b.put('Floor', x, y, s(f'side-{side}'))
        # ---- the floor's cut edge: the stone podium under the ground floor, the roof's skirt
        #      outside every other ------------------------------------------------------------
        under = 'base' if k == 0 else 'edge'
        for x in range(x0, x1 + 1):
            b.put('Floor', x, t + 7, s(under))
        b.put('Floor', x0 - 1, t + 7, s(f'{under}-w'))
        b.put('Floor', x1 + 1, t + 7, s(f'{under}-e'))
        if k:
            b.put('Over Floor', x0 - 3, t + 7, s('eave-w'))       # 3x1: its last 12px lie on the wall
            b.put('Over Floor', x1 + 1, t + 7, s('eave-e'))
        # ---- the heart pillar ----------------------------------------------------------------
        if k == 0:
            b.stand(s('shumidan'), CX - 1, t + 4, w=3, h=3)         # the dais it rises from, four small Buddhas
            bumps.append(('shumidan', (CX - 2, t + 4)))
            b.stand(s('saisen'), CX, t + 5, h=1)                    # the offering box before them
            bumps.append(('saisen', (CX, t + 6)))
            for x in (CX - 3, CX + 3):                              # a candle either side
                b.stand(s('shokudai'), x, t + 4)
            b.put('Non-Collidables', CX, t + 5, s('doorlight'))
        else:
            b.stand(s('pillar'), CX, t + 4, h=3)
            bumps.append(('pillar', (CX - 1, t + 4)))
        # ---- the stair up, and what is on the back wall ----------------------------------------
        if k < S - 1:
            sx = stair_x(k)
            b.put('Over Floor', sx, t - 1, s('stair'))              # 1x3: through the floor above
            it.walk |= {(sx, t + 1), (sx, t), (sx, t - 1)}
            if k:
                # a middle storey: one fitting, on the side away from the stair
                piece = FITTINGS[(seed + k) % len(FITTINGS)]
                on_wall(min(2 * CX - sx, CX + (1 if sx < CX else -1)), t, piece, 2)
                lamp = sx + (1 if sx > CX else -1)                  # the lantern: outside the stair
            else:
                lamp = 2 * CX - sx
        else:
            on_wall(CX - 1, t, 'window', 3)                         # the top storey: a slatted window
            lamp = 2 * CX - stair_x(k - 1)                          # the lantern: across from the hatch
        b.put('Tops', lamp, t + 1, s('toro-hang'))

    for k in range(S - 1):                                          # where each stair comes out, on the storey above
        b.put('Floor', stair_x(k), top(k) - 2, s('hatch'))

    # ---- the top roof and the spire ----------------------------------------------------------------
    b.put('Over Floor', CX - 4, 0, s('roof'))                       # one sprite: the camera looks up at it

    # ---- the way in: the mat under the middle of the ground floor, out to the front of the door ----------
    inside = it.doorway(widths[0] // 2, p['host'], p['front'], n=1, mat=s('threshold'))
    # the floors, the stairs between them and the mat are the room's outline: everything round them is
    # drawn, not walked on. Every board, stair and hatch can be walked to from the mat (Interior.room)...
    room = it.room(
        p['name'], npcs=cfg['rooms'].get(p['key'], {}).get('npcs', []),
        # whose pagoda this is: the marker roomgen.owned_door reads, as a house's `house` is
        **{MARKER: {'host': p['host'], 'door': list(p['door']), 'doors': [list(d) for d in p['doors']], 'storeys': S}},
        lanternLight=True,           # at night it dims and its lights glow (DayNight, Glows)
        shopEnabled=False)           # not a konbini
    # ...and every fitting bumped
    stuck = [(piece, cell) for piece, cell in bumps if cell not in it.reached]
    assert not stuck, f"{p['key']}: nowhere to stand to bump: {stuck}"
    return room, inside[0]


def apply(host):
    """(Re)build `host`'s pagodas in cfg. Returns the keys built."""
    room = cfg['rooms'][host]
    found = gh.find_houses(cfg, host, KIND)
    pagodas = [p for p in found if 'key' in p]
    opened = [p for p in pagodas if 'skipped' not in p]
    built = []
    for p in found:
        if 'excluded' in p:
            print(f"not a pagoda  {host} {p['family']} at {p['origin']} - {p['excluded']}")
    # rooms of this town from an earlier run that no pagoda claims any more
    for key in [k for k, r in cfg['rooms'].items() if (r.get(MARKER) or {}).get('host') == host]:
        if key not in {p['key'] for p in opened}:
            for cell in cfg['rooms'][key][MARKER]['doors']:
                rg.shut_door(room, cell, PREFIX)
            del cfg['rooms'][key]
    for p in pagodas:
        if 'skipped' in p:
            for cell in p['all_doors']:
                rg.shut_door(room, cell, PREFIX)
            print(f"skipped  {p['key']} ({p['family']}, door {p['door']}) - {p['skipped']}")
            continue
        p['host'] = host
        p['storeys'] = TALLER.get((host, p['all_doors'][0]), STOREYS[p['family']])
        # numbered only where the town opens more than one
        p['name'] = interiors.named(cfg, KIND['label'], host, p['key'][len(PREFIX + host):] if len(opened) > 1 else None)
        interior, arrive = build(p)
        cfg['rooms'][p['key']] = interior
        for cell in p['all_doors']:                              # a door of a pair that may not open stays shut
            if cell not in p['doors']:
                rg.shut_door(room, cell, PREFIX)
        for cell in p['doors']:
            rg.open_door(room, cell, p['key'], arrive)           # unsealed, wired in place: a re-run changes nothing
        built.append(p['key'])
        print(f"built    {p['key']} \"{p['name']}\" - {p['family']}, {p['storeys']} storeys, "
              f"doors {p['doors']}, front {p['front']}, {interior['worldWidth'] // 64}x{interior['worldHeight'] // 64}")
    if not pagodas:
        print(f'no pagoda in {host}')
    return built


built = []
for host in HOSTS:
    built += apply(host)
if DRY:
    print(f'\n--dry-run: {len(built)} pagoda interiors would be written, nothing saved')
else:
    rg.save_config(cfg)
    print(f'\n{len(built)} pagoda interiors written. Now run config_to_tiled, then play.js lint, for:')
    print('  ' + ' '.join(built + HOSTS))
