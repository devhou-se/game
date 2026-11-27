#!/usr/bin/env python3
"""generate_shrines.py — the worship hall inside every shrine (issue #212).

A shrine hall in a town is the `shrine` / `shrine-red` prefab (or Dazaifu's own
hall): until this ran it was sealed. This builds one interior room per hall
and opens the hall's door onto it, the way generate_konbinis.py does for a
7-Eleven:
  * rooms.Shrine<Host><n> is rebuilt from scratch (any NPCs it holds are kept);
  * the host's door cell is unsealed and a hidden transporter wired onto it,
    replaced in place so a re-run leaves config.json byte-identical;
  * the room's exit mats lead back to the cell in front of the door.
Nothing else in the host is touched. A town generator that rebuilds the host
seals the hall again and knows nothing of this door: roomgen.save_config puts it
back (OWNED_DOORS / keep_house_doors, the mechanism that keeps a house's door).

What is inside (art: tools/generate_shrine_art.py, the garland rope from
tools/extract_shrine.py): the inner sanctuary on a raised floor at the back,
its doors open on the mirror, behind a railing you see through and under the
thick straw rope; the offering box with the bell and its rope over it; pillars
you walk behind, a garland strung between the front pair; hanging and standing
paper lanterns (they glow at night: the room is `lanternLight`, DayNight); a
tatami room with a drum and cushions; the miko's counter; a rack of wishing
plaques; the fortune stand and its rail of tied fortunes; daylight through the
door. The offering box and the fortune stand do something when bumped
(src/ShrineVisit.js, two rules in src/utils/Interactions.js).

Three variants:
  look  'blue' under a blue roof (shrine-top): bare cypress, white plaster and
        indigo, the counter on the west side;
        'red' under a red roof (red-shrine-top): vermilion and gilt, the
        counter on the east side, a second pair of pillars by the sanctuary.
  size  'large' for the halls named in LARGE (Kushida, Dazaifu Tenmangu): a
        wider, deeper hall with a third pair of pillars (outside the nave's
        two), a rack of plaques on both sides and more lanterns.

Run from gamev2/:  python3 tools/generate_shrines.py [Host ...]     (--help: this text, nothing run)
With no host it rebuilds the shrines that are already wired (what
check_generators.py runs); name a host to give its halls an interior for the
first time. Then:  python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
(.agent-queue/items/shrines_apply.sh does all of it, and the gates.)
"""
import sys

import roomgen as rg

ARGS = rg.cli(__doc__, sys.argv[1:])   # --help: usage, nothing run
cfg = rg.load_config()

# hall tile -> (door cell relative to the tile, look; None = by the roof over it).
# The door cells are roomgen.SHRINE_DOORS: what save_config keeps through a town rebuild.
LOOKS = {'shrine-building_0_0': None, 'dazaifu-hall_0_0': 'red'}
HALLS = {key: (cells[0], LOOKS[key]) for key, cells in rg.SHRINE_DOORS.items()}
ROOFS = {'shrine-top_0_0': 'blue', 'red-shrine-top_0_0': 'red'}
# (host, hall tile) -> the hall's own name; any other is "Shrine · <town>"
NAMES = {
    ('Fukuoka', 'shrine-building_0_0'): 'Kushida Shrine',
    ('Fukuoka', 'dazaifu-hall_0_0'): 'Dazaifu Tenmangu',
    # the hall inside the moat: "Shrine · Imperial Palace" is too long for a phone's one-row HUD bar
    # ("Imperial Palace shrine | Feb 10 | ¥5,000" is 2 characters over at 667x375, issue #219)
    ('Tokyo', 'shrine-building_0_0'): 'Palace Shrine',
}
LARGE = {('Fukuoka', 'shrine-building_0_0'), ('Fukuoka', 'dazaifu-hall_0_0')}
PREFIX = rg.SHRINE_PREFIX   # room keys; roomgen.OWNED_DOORS keeps these doors through a town rebuild


def wired_hosts():
    """Hosts that already have a door into a shrine interior."""
    return [k for k, r in cfg['rooms'].items()
            if any(t['targetRoom'].startswith(PREFIX) for t in r.get('transporters', []))]


HOSTS = ARGS or wired_hosts()
unknown = [h for h in HOSTS if h not in cfg['rooms']]
assert not unknown, f'no such room: {unknown}'


def find_halls():
    """Every shrine hall of the hosts, in stable (host, y, x) order."""
    halls = []
    for host in HOSTS:
        room = cfg['rooms'][host]
        tops = {xy: rg._pal[i] for layer in room['layers'] if layer['name'] == 'Tops'
                for xy, i in layer['tiles'].items()}
        found = []
        for layer in room['layers']:
            for xy, idx in layer['tiles'].items():
                key = rg._pal[idx]
                if key in HALLS:
                    x, y = map(int, xy.split(','))
                    found.append((y, x, key))
        for n, (y, x, key) in enumerate(sorted(found), start=1):
            (dx, dy), look = HALLS[key]
            look = look or ROOFS.get(tops.get(f'{x - 1},{y - 2}'))
            assert look, f'{host}: the hall at {x},{y} has no shrine roof over it'
            where = room.get('name', host)
            halls.append({
                'host': host, 'key': f'{PREFIX}{host}{n}', 'look': look,
                'size': 'large' if (host, key) in LARGE else 'standard',
                'name': NAMES.get((host, key), f'Shrine · {where}' + (f' {n}' if len(found) > 1 else '')),
                'door': (x + dx, y + dy), 'front': (x + dx, y + dy + 1),
            })
    return halls


def build_interior(hall):
    look, large = hall['look'], hall['size'] == 'large'
    fw, fh = (24, 12) if large else (18, 10)      # the floor, in cells
    W, H = fw + 2, fh + 6
    OX, OY = 1, 3                                 # room cell of floor cell (0, 0)
    cx = fw // 2                                  # the hall's axis is the seam left of this column
    b = rg.Builder(W, H)
    k = lambda piece: f'shrine-in-{piece}-{look}_0_0'       # a piece in this hall's look
    s = lambda piece: f'shrine-in-{piece}_0_0'              # a shared piece

    def put(layer, fx, fy, key):
        b.put(layer, OX + fx, OY + fy, key)

    def solid(fx, fy, w=1, h=1):
        for dx in range(w):
            for dy in range(h):
                b.solid(OX + fx + dx, OY + fy + dy)

    def side(west, off, w=1):
        """Column of a piece `w` wide standing `off` cells in from a side wall."""
        return off if west else fw - off - w

    # ---- floor, walls --------------------------------------------------------------
    b.fill('office-void-autotile')
    for fx in range(fw):
        for fy in range(fh):
            put('Floor', fx, fy, k('floor-a' if (fx + fy // 2) % 2 == 0 else 'floor-b'))
    for fy in range(-2, fh):
        b.put('Floor', 0, OY + fy, k('side-w'))
        b.put('Floor', W - 1, OY + fy, k('side-e'))
    for fx in range(fw):
        if fx not in (cx - 1, cx):
            put('Floor', fx, fh, k('wall-front'))
    put('Floor', cx - 1, fh, k('threshold-w'))
    put('Floor', cx, fh, k('threshold-e'))
    put('Non-Collidables', cx - 1, fh - 3, s('doorlight'))

    counter_west = look == 'blue'                 # the two looks are laid out as mirror images
    wing = cx - 4                                 # cells from a side wall to the nave's pillars

    def wall_piece(fx):
        west = fx < cx
        i = fx if west else fw - 1 - fx           # cells in from the side wall
        if i >= wing - 1:
            return 'wall-curtain'                 # the bays beside the sanctuary
        if (west == counter_west) or i == 0:
            return 'wall' if i % 2 == 0 else 'wall-curtain'
        return 'wall-shoji'                       # the tatami room's paper screens
    for fx in list(range(cx - 3)) + list(range(cx + 3, fw)):
        put('Collidables', fx, -2, k(wall_piece(fx)))
        solid(fx, -2, 1, 2)

    # ---- the inner sanctuary, its railing and rope -------------------------------------
    put('Collidables', cx - 3, -2, k('honden'))
    solid(cx - 3, -2, 6, 3)
    for fx in (cx - 4, cx + 3):                    # evergreen offerings either side of it
        put('Collidables', fx, -1, s('sakaki'))
        solid(fx, 0)
    for fx in range(cx - 4, cx + 4):               # the railing: feet on row 1, seen through
        put('Collidables', fx, 0, k('lattice'))
        solid(fx, 1)
    for fx in (cx - 5, cx + 4):                    # a standing lamp at each end of it
        put('Collidables', fx, 0, s('lanterns-floor'))
        solid(fx, 1)
    put('Tops', cx - 3, -2, s('shimenawa'))

    # ---- the offering box, the bell over it ------------------------------------------------
    box_y = 4 if not large else 5
    put('Collidables', cx - 1, box_y - 1, s('saisen'))
    solid(cx - 1, box_y - 1, 2, 2)
    put('Tops', cx - 1, box_y - 2, s('bell'))
    for fy in range(box_y + 1, fh):                # the runner from the door to the box
        put('Over Floor', cx - 1, fy, k('runner-l'))
        put('Over Floor', cx, fy, k('runner-r'))

    # ---- pillars: only the foot is solid, the shaft is walked behind ---------------------------
    feet = [fh - 2]                                # the front pair, by the door
    if look == 'red' or large:
        feet.append(box_y)                         # a pair level with the offering box
    if large:
        feet.append(fh - 5)                        # a third pair between them, two cells further out:
    for foot in feet:                              # in the nave's own columns its head would stand on
        out = 2 if large and foot == fh - 5 else 0     # the foot of the pair by the box
        for fx in (cx - 4 - out, cx + 3 + out):
            put('Collidables', fx, foot - 2, k('pillar'))
            solid(fx, foot)
    # a garland of rope and paper between the front pair's heads
    for fx in (cx - 3, cx):
        put('Tops', fx, fh - 4, s('rope'))

    # ---- the two wings -------------------------------------------------------------------------
    def tatami(fx0, fx1, rows):
        for fy in range(rows):
            for fx in range(fx0, fx1 + 1):
                put('Floor', fx, fy, s('tatami-l' if (fx - fx0 + fy) % 2 == 0 else 'tatami-r'))

    mats = wing - 1 - (wing - 1) % 2               # an even number of half-mats, from the side wall
    low = fh - 4                                   # top row of the two-row pieces by the door
    for west in (True, False):
        x0 = side(west, 0, mats)
        if west == counter_west:
            # the miko's counter, on a strip of tatami, facing the hall
            tatami(x0, x0 + mats - 1, 3)
            put('Collidables', side(west, 1, 3), 1, s('counter'))
            solid(side(west, 1, 3), 1, 3, 2)
            # by the door on this side: the fortune stand and its rail of tied fortunes
            put('Collidables', side(west, 2, 2), low, s('omikuji'))
            solid(side(west, 2, 2), low, 2, 2)
            put('Collidables', side(west, 0, 2), low, s('omikuji-rail'))
            solid(side(west, 0, 2), low + 1, 2, 1)
        else:
            # the tatami room: a drum in the corner, cushions set out in two rows
            tatami(x0, x0 + mats - 1, 4)
            put('Collidables', side(west, 0, 2), 0, s('drum'))
            solid(side(west, 0, 2), 0, 2, 2)
            for off in range(mats):
                put('Over Floor', side(west, off), 2 + off % 2, s('zabuton'))
            # by the door on this side: the rack of wishing plaques
            put('Collidables', side(west, 1, 3), low, s('ema'))
            solid(side(west, 1, 3), low + 1, 3, 1)
        if large:                                  # a big hall has plaques on both sides, further in
            put('Collidables', side(west, 4, 3), low, s('ema' if west == counter_west else 'omikuji-rail'))
            solid(side(west, 4, 3), low + 1, 3 if west == counter_west else 2, 1)
    if look == 'blue':                             # standing lamps either side of the offering box
        for fx in (cx - 3, cx + 2):
            put('Collidables', fx, box_y - 1, s('lanterns-floor'))
            solid(fx, box_y)

    # ---- lanterns --------------------------------------------------------------------------------
    hang = [(cx - 3, fh - 3), (cx + 2, fh - 3), (0, box_y), (fw - 1, box_y)]
    if large:
        hang += [(cx - 6, 2), (cx + 5, 2), (3, fh - 6), (fw - 4, fh - 6)]
    for fx, fy in hang:
        put('Tops', fx, fy, k('lanterns'))

    # ---- the door ------------------------------------------------------------------------------------
    fx, fy = hall['front']
    room = b.room(hall['name'], npcs=cfg['rooms'].get(hall['key'], {}).get('npcs', []), transporters=[
        rg.transporter(OX + cx - 1, OY + fh, hall['host'], fx, fy, hidden=True),
        rg.transporter(OX + cx, OY + fh, hall['host'], fx, fy, hidden=True),
    ])
    # the floor plus the two doorway cells; the walls round it need no colliders
    room['boundary'] = [
        [OX, OY], [OX + fw, OY], [OX + fw, OY + fh],
        [OX + cx + 1, OY + fh], [OX + cx + 1, OY + fh + 1],
        [OX + cx - 1, OY + fh + 1], [OX + cx - 1, OY + fh],
        [OX, OY + fh],
    ]
    # whose hall this is: the marker roomgen.owned_door reads, as a house's `house` is
    room['shrine'] = {'host': hall['host'], 'door': list(hall['door']), 'look': look, 'size': hall['size']}
    room['interior'] = True          # never offered to the blog pipeline; no day/night grade...
    room['lanternLight'] = True      # ...but at night it dims and its lanterns glow (DayNight)
    room['shopEnabled'] = False      # not a konbini
    return room, (OX + cx - 1, OY + fh - 1)        # arrive just inside the door


halls = find_halls()
built = []
for hall in halls:
    room, arrive = build_interior(hall)
    cfg['rooms'][hall['key']] = room
    host = cfg['rooms'][hall['host']]
    dx, dy = hall['door']
    for layer in host['layers']:
        if layer['name'] == 'Colliders':
            layer['tiles'].pop(f'{dx},{dy}', None)          # unseal the doorway
    door = rg.transporter(dx, dy, hall['key'], *arrive, hidden=True)
    ts = host.setdefault('transporters', [])
    at = [i for i, t in enumerate(ts) if (t['gridX'], t['gridY']) == (dx, dy)]
    if at:                                                  # in place: a re-run changes nothing
        ts[at[0]] = door
        for i in reversed(at[1:]):
            del ts[i]
    else:
        ts.append(door)
    built.append(hall['key'])
    print(f"built  {hall['key']} ({hall['look']}, {hall['size']}) - {hall['name']}: "
          f"{hall['host']} door {hall['door']}, front {hall['front']}, "
          f"{room['worldWidth'] // 64}x{room['worldHeight'] // 64}")

rg.save_config(cfg)
print(f"\n{len(built)} shrine interiors written. Now run config_to_tiled, then play.js lint, for:")
print('  ' + ' '.join(built + HOSTS))
