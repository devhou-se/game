#!/usr/bin/env python3
"""square_junctions.py — road junctions in the ported districts are plain boxes (issues #147, #179, #240, #247).

The Godot port drew a three-cell road (kerb / centre line / kerb) straight
through every junction, so wherever a road joined another its mouth was closed
by the other road's kerb and its centre line ran on into the junction.

A junction is the 3x3 box where the roads meet. This lays each one the way
#147 laid the west gate by hand:

  - `road-plain` on every cell, so each joining road opens into the box and
    every centre line stops at its edge;
  - the kerb (`road-edge-*`) along a CLOSED side of the box - the side no road
    leaves by (the far side of a T-junction, the outside of a bend);
  - a mitred `road-corner-*` (tools/make_road_tiles.py) where two closed sides
    meet, the outer corner of a bend.

JUNCTIONS lists the boxes per district, in the district's own cells: the
box's top-left cell and its closed sides. A box may hang over the map edge
(the Tokyo/Market road is half in each map; Park's west road is half in the
woods): cells outside the room are skipped, and the neighbour's entry lays
them. Sides are as the district reads ON ITS OWN (`?stitch=0`); where the
stitched city opens a side that the lone map closes (Park's top row, which
Palace's roads run into), config `cities.TokyoCity.patch` opens it.

ARMS lists stretches of an east-west road that the port paved over (issue
#194: two cells of brick across the avenue on either side of the Tokyo/Market
crossroads, which no other arm of any junction has). Each is laid as the road
it interrupts: kerb / centre line / kerb, up to the box.

A road that leaves a junction must lead somewhere. The port ran every
east-west road of Market, Palace and Park on across the pavement beyond the
east road and off the edge of the city, two cells on, so the east road read as
four crossroads on the edge of the map (issue #240). Those boxes are closed on
the east (the kerb runs straight down the east road; the avenue at the top and
the south road at the bottom end in a bend), and PAVEMENT lays the two-cell
stubs as the pavement they cut through. The same junction is in Palace's own
map (its rows 18..20 are Park's top three, and Park owns them in the stitched
city), so Palace has that one box and stub too. It has Park's top-left box as
well (issue #247), open on every side: in Palace's map the west road runs into
it from the north and on out of the bottom of the map.

Idempotent. Edits config.json only: follow with
    python3 tools/config_to_tiled.py Tokyo Market Palace Park
    /Library/Developer/CommandLineTools/usr/bin/python3 tools/make_worldmap.py

Run from gamev2/:  python3 tools/square_junctions.py [--dry-run]
"""
import json, sys

# district -> [(x, y, closed sides)]: the box is cells x..x+2, y..y+2
JUNCTIONS = {
    'Tokyo': [
        (2, 2, 'NW'),       # north-west bend: the avenue turns south
        (57, 2, 'N'),       # the Tokyo/Market road leaves the avenue (half the box; Market has the rest)
        (2, 41, 'WS'),      # the west gate bend (#147)
        (57, 41, ''),       # crossroads on the Tokyo/Market road
    ],
    'Market': [
        (-1, 3, 'N'),       # the other half of the two above
        (-1, 42, ''),
        (54, 3, 'NE'),      # north-east bend: the avenue turns south into the east road (#240)
        (54, 42, 'E'),      # the east road; the road from the Tokyo/Market crossroads ends on it (#240)
    ],
    'Palace': [
        (-1, 18, ''),       # Park's top-left box, in Palace's own map (#247), where the west road runs on through it
        (54, 18, 'E'),      # Park's top-right box, in Palace's own map (#240); the stitched city draws Park's
    ],
    'Park': [
        (-1, 0, 'N'),       # top-left: the west road leaves the Palace/Park road
        (54, 0, 'NE'),      # top-right: the Palace/Park road ends on the east road (#240)
        (-1, 39, 'S'),      # bottom-left bend (its west kerb is in the woods: cities.backdrop.edges)
        (54, 39, 'SE'),     # bottom-right bend: the east road turns west into the south road (#240)
    ],
}

# district -> [(x, y, cells)]: an east-west road, rows y..y+2, columns x..x+cells-1
ARMS = {
    'Tokyo': [(55, 41, 2)],     # west of the Tokyo/Market crossroads
    'Market': [(2, 42, 2)],     # east of it
}
ARM = ['road-edge-top_0_0', 'road-div-horizontal_0_0', 'road-edge-bottom_0_0']

# district -> [(x, y, rows)]: pavement from cell (x, y) down, one string per row, one brick piece per cell.
# The pavement east of the east road is two cells wide: `edge-w` along the kerb, `edge-e` along the edge
# of the map. Each entry runs from the pavement above a closed stub to the pavement below it, so the
# corner pieces that turned into the stub become the straight run; round a bend the outer corner is a
# `corner-*` and the inner one `center`, as at Tokyo's two western bends.
BRICK = 'flat-grey-brick-autotile_'
RUN = 'edge-w edge-e'
PAVEMENT = {
    'Market': [
        (57, 1, ['edge-n corner-ne', 'center edge-e'] + [RUN] * 5),         # round the north-east bend
        (57, 40, [RUN] * 7),                                                # past the east crossroads' stub
    ],
    'Palace': [(57, 16, [RUN] * 6)],                                        # to the bottom of the map
    'Park': [
        (57, 0, [RUN] * 5),                                                 # from the top of the map
        (57, 37, [RUN] * 5 + ['center edge-e', 'edge-s corner-se']),        # round the south-east bend
    ],
}

PLAIN = 'road-plain_0_0'
EDGE = {'N': 'road-edge-top_0_0', 'S': 'road-edge-bottom_0_0', 'W': 'road-edge-left_0_0', 'E': 'road-edge-right_0_0'}
CORNER = {'NW': 'road-corner-nw_0_0', 'NE': 'road-corner-ne_0_0', 'SW': 'road-corner-sw_0_0', 'SE': 'road-corner-se_0_0'}


def box_tile(dx, dy, closed):
    """The tile for cell (dx, dy) of a 3x3 box (0..2 each) whose `closed` sides carry a kerb."""
    ns = 'N' if dy == 0 and 'N' in closed else 'S' if dy == 2 and 'S' in closed else ''
    we = 'W' if dx == 0 and 'W' in closed else 'E' if dx == 2 and 'E' in closed else ''
    if ns and we:
        return CORNER[ns + we]
    return EDGE[ns or we] if (ns or we) else PLAIN


def main():
    dry = '--dry-run' in sys.argv
    cfg = json.load(open('config.json'))
    pal = cfg['tilePalette']

    def pidx(key):
        if key not in pal:
            pal.append(key)         # positional: append only
        return pal.index(key)

    total = 0
    for name, boxes in JUNCTIONS.items():
        room = cfg['rooms'][name]
        w, h = room['worldWidth'] // 64, room['worldHeight'] // 64
        floor = next(L for L in room['layers'] if L['name'] == 'Floor')['tiles']
        changed = []
        for (x0, y0, cells) in ARMS.get(name, []):
            for dy in range(3):
                for x in range(x0, x0 + cells):
                    want = pidx(ARM[dy])
                    if floor.get(f'{x},{y0 + dy}') != want:
                        floor[f'{x},{y0 + dy}'] = want
                        changed.append(f'{x},{y0 + dy}')
        for (x0, y0, closed) in boxes:
            for dy in range(3):
                for dx in range(3):
                    x, y = x0 + dx, y0 + dy
                    if not (0 <= x < w and 0 <= y < h):
                        continue
                    want = pidx(box_tile(dx, dy, closed))
                    if floor.get(f'{x},{y}') != want:
                        floor[f'{x},{y}'] = want
                        changed.append(f'{x},{y}')
        for (x0, y0, rows) in PAVEMENT.get(name, []):
            for dy, row in enumerate(rows):
                for dx, piece in enumerate(row.split()):
                    want = pidx(BRICK + piece)
                    if floor.get(f'{x0 + dx},{y0 + dy}') != want:
                        floor[f'{x0 + dx},{y0 + dy}'] = want
                        changed.append(f'{x0 + dx},{y0 + dy}')
        total += len(changed)
        if changed:
            print(f'{name}: {len(changed)} cell(s): {" ".join(changed)}')
    if not total:
        print('junctions are already square')
    elif dry:
        print('(dry run: nothing written)')
    else:
        open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
