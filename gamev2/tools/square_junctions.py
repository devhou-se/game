#!/usr/bin/env python3
"""square_junctions.py — road junctions in the ported districts are plain boxes (issues #147, #179).

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

Idempotent. Edits config.json only: follow with
    python3 tools/config_to_tiled.py Tokyo Market Park
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
        (54, 3, 'N'),       # north-east: the east road leaves the avenue
        (54, 42, ''),       # east crossroads
    ],
    'Park': [
        (-1, 0, 'N'),       # top-left: the west road leaves the Palace/Park road
        (54, 0, 'N'),       # top-right
        (-1, 39, 'S'),      # bottom-left bend (its west kerb is in the woods: cities.backdrop.edges)
        (54, 39, 'S'),      # bottom-right: the east road ends on the south road
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
