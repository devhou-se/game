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
A hall that is no longer on the host's map loses its room, the room's
tiled/*.tmj and its old door on the next run (roomgen.drop_stale, issue #243;
halls are numbered per town, so it is the highest number that goes).

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
check_generators.py runs), and visits a town whose rooms say it had a hall and
that has no door into one left; name a host to give its halls an interior for
the first time. Then:  python3 tools/config_to_tiled.py <each new room + hosts>
                   node tools/play.js lint <each new room + hosts>
(.agent-queue/items/shrines_apply.sh does all of it, and the gates.)
"""
import sys

import interiors
import roomgen as rg
from interiors import Interior

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
    """Hosts that already have a door into a shrine interior, then the hosts a
    worship hall's `shrine` marker names that have none: a town that lost its
    only hall, whose room is still to be dropped."""
    hosts = [k for k, r in cfg['rooms'].items()
             if any(t['targetRoom'].startswith(PREFIX) for t in r.get('transporters', []))]
    for r in cfg['rooms'].values():
        host = (r.get('shrine') or {}).get('host')
        if host and host not in hosts:
            hosts.append(host)
    return hosts


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
        found = rg.find_sprites(room, HALLS)
        for n, (x, y, key) in enumerate(found, start=1):
            (dx, dy), look = HALLS[key]
            look = look or ROOFS.get(tops.get(f'{x - 1},{y - 2}'))
            assert look, f'{host}: the hall at {x},{y} has no shrine roof over it'
            halls.append({
                'host': host, 'key': f'{PREFIX}{host}{n}', 'look': look,
                'size': 'large' if (host, key) in LARGE else 'standard',
                'name': NAMES.get((host, key), interiors.named(cfg, 'Shrine', host, n if len(found) > 1 else None)),
                'door': (x + dx, y + dy), 'front': (x + dx, y + dy + 1),
            })
    return halls


def build_interior(hall):
    look, large = hall['look'], hall['size'] == 'large'
    fw, fh = (24, 12) if large else (18, 10)      # the floor, in cells
    cx = fw // 2                                  # the hall's axis is the seam left of this column
    it = Interior(fw, fh)                         # a wall each side, a 2-row back wall under one row of dark
    k = lambda piece: f'shrine-in-{piece}-{look}_0_0'       # a piece in this hall's look
    s = lambda piece: f'shrine-in-{piece}_0_0'              # a shared piece

    def side(west, off, w=1):
        """Column of a piece `w` wide standing `off` cells in from a side wall."""
        return off if west else fw - off - w

    # ---- floor, walls --------------------------------------------------------------
    it.floor(lambda fx, fy: k('floor-a' if (fx + fy // 2) % 2 == 0 else 'floor-b'))
    it.side_walls(k('side-w'), k('side-e'), 2)
    it.front_wall(k('wall-front'), (cx - 1, cx), (k('threshold-w'), k('threshold-e')))
    it.put('Non-Collidables', cx - 1, fh - 3, s('doorlight'))

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
    it.back_wall([(fx, k(wall_piece(fx)), 1) for fx in list(range(cx - 3)) + list(range(cx + 3, fw))], 2)

    # ---- the inner sanctuary, its railing and rope -------------------------------------
    it.prop(k('honden'), cx - 3, -2, 6, 3)
    for fx in (cx - 4, cx + 3):                    # evergreen offerings either side of it
        it.stand(s('sakaki'), fx, 0)
    for fx in range(cx - 4, cx + 4):               # the railing: feet on row 1, seen through
        it.stand(k('lattice'), fx, 1)
    for fx in (cx - 5, cx + 4):                    # a standing lamp at each end of it
        it.stand(s('lanterns-floor'), fx, 1)
    it.put('Tops', cx - 3, -2, s('shimenawa'))

    # ---- the offering box, the bell over it ------------------------------------------------
    box_y = 4 if not large else 5
    it.prop(s('saisen'), cx - 1, box_y - 1, 2, 2)
    it.put('Tops', cx - 1, box_y - 2, s('bell'))
    for fy in range(box_y + 1, fh):                # the runner from the door to the box
        it.put('Over Floor', cx - 1, fy, k('runner-l'))
        it.put('Over Floor', cx, fy, k('runner-r'))

    # ---- pillars: only the foot is solid, the shaft is walked behind ---------------------------
    feet = [fh - 2]                                # the front pair, by the door
    if look == 'red' or large:
        feet.append(box_y)                         # a pair level with the offering box
    if large:
        feet.append(fh - 5)                        # a third pair between them, two cells further out:
    for foot in feet:                              # in the nave's own columns its head would stand on
        out = 2 if large and foot == fh - 5 else 0     # the foot of the pair by the box
        for fx in (cx - 4 - out, cx + 3 + out):
            it.stand(k('pillar'), fx, foot, h=3)
    # a garland of rope and paper between the front pair's heads
    for fx in (cx - 3, cx):
        it.put('Tops', fx, fh - 4, s('rope'))

    # ---- the two wings -------------------------------------------------------------------------
    def tatami(fx0, fx1, rows):
        for fy in range(rows):
            for fx in range(fx0, fx1 + 1):
                it.put('Floor', fx, fy, s('tatami-l' if (fx - fx0 + fy) % 2 == 0 else 'tatami-r'))

    mats = wing - 1 - (wing - 1) % 2               # an even number of half-mats, from the side wall
    low = fh - 4                                   # top row of the two-row pieces by the door
    for west in (True, False):
        x0 = side(west, 0, mats)
        if west == counter_west:
            # the miko's counter, on a strip of tatami, facing the hall
            tatami(x0, x0 + mats - 1, 3)
            it.prop(s('counter'), side(west, 1, 3), 1, 3, 2)
            # by the door on this side: the fortune stand and its rail of tied fortunes
            it.prop(s('omikuji'), side(west, 2, 2), low, 2, 2)
            it.stand(s('omikuji-rail'), side(west, 0, 2), low + 1, w=2)
        else:
            # the tatami room: a drum in the corner, cushions set out in two rows
            tatami(x0, x0 + mats - 1, 4)
            it.prop(s('drum'), side(west, 0, 2), 0, 2, 2)
            for off in range(mats):
                it.put('Over Floor', side(west, off), 2 + off % 2, s('zabuton'))
            # by the door on this side: the rack of wishing plaques
            it.stand(s('ema'), side(west, 1, 3), low + 1, w=3)
        if large:                                  # a big hall has plaques on both sides, further in
            if west == counter_west:
                it.stand(s('ema'), side(west, 4, 3), low + 1, w=3)
            else:
                it.stand(s('omikuji-rail'), side(west, 4, 3), low + 1, w=2)
    if look == 'blue':                             # standing lamps either side of the offering box
        for fx in (cx - 3, cx + 2):
            it.stand(s('lanterns-floor'), fx, box_y)

    # ---- lanterns --------------------------------------------------------------------------------
    hang = [(cx - 3, fh - 3), (cx + 2, fh - 3), (0, box_y), (fw - 1, box_y)]
    if large:
        hang += [(cx - 6, 2), (cx + 5, 2), (3, fh - 6), (fw - 4, fh - 6)]
    for fx, fy in hang:
        it.put('Tops', fx, fy, k('lanterns'))

    # ---- the door: a threshold either side of the axis, both leading out in front of the hall ----------
    inside = it.doorway(cx - 1, hall['host'], hall['front'])
    room = it.room(
        hall['name'], npcs=cfg['rooms'].get(hall['key'], {}).get('npcs', []),
        # whose hall this is: the marker roomgen.owned_door reads, as a house's `house` is
        shrine={'host': hall['host'], 'door': list(hall['door']), 'look': look, 'size': hall['size']},
        lanternLight=True,           # at night it dims and its lanterns glow (DayNight)
        shopEnabled=False)           # not a konbini
    return room, inside[0]                         # arrive just inside the door


halls = find_halls()
built = []
for hall in halls:
    room, arrive = build_interior(hall)
    cfg['rooms'][hall['key']] = room
    rg.open_door(cfg['rooms'][hall['host']], hall['door'], hall['key'], arrive)     # unsealed, wired in place
    built.append(hall['key'])
    print(f"built  {hall['key']} ({hall['look']}, {hall['size']}) - {hall['name']}: "
          f"{hall['host']} door {hall['door']}, front {hall['front']}, "
          f"{room['worldWidth'] // 64}x{room['worldHeight'] // 64}")

# what an earlier run left for a hall that is gone: its old door (shut), and the host's rooms that
# no hall claims any more (deleted; rg.save_config deletes their maps)
for host in HOSTS:
    stale = [k for k, r in cfg['rooms'].items() if (r.get('shrine') or {}).get('host') == host and k not in built]
    for line in rg.drop_stale(cfg, host, PREFIX, [h['door'] for h in halls if h['host'] == host], stale):
        print(line)

rg.save_config(cfg)
print(f"\n{len(built)} shrine interiors written. Now run config_to_tiled, then play.js lint, for:")
print('  ' + ' '.join(built + HOSTS))
