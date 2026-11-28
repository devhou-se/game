#!/usr/bin/env python3
"""make_bridge_tiles.py — a parapet and a shadow for a bridge deck over water (issue #180).

A bridge in a generated room is plain paving laid across a gap in the water
(Osaka's street over the Dotonbori canal): nothing says "bridge" but the
boats being cut off at its edge. These four one-cell pieces dress the two
sides of a deck that runs north-south:

  bridge-parapet-w_0_0   a stone coping down the WEST edge of a deck cell, with
  bridge-parapet-e_0_0   a pier at the cell's top and bottom (stacked cells
                         join them into one pier per boundary) / the EAST
                         edge. It takes the outer 14px of the cell, so it needs
                         no collider: a walker in that cell stands clear of it,
                         and the deck keeps its full width (#139). Drawn in the
                         house look (#359): the pack's steel ramp edged in its
                         navy ink, lit from the upper left, so the west coping
                         casts a thin shadow on the paving beside it and the
                         east one, lit on the deck side, casts none there.
  bridge-shade-w_0_0     the deck's shadow on the WATER cell west of it (a dark
  bridge-shade-e_0_0     band against the deck's edge) / east of it.

They lie flat but must cover the Water layer, so they go on Non-Collidables
with a negative `depthBias` (the asahikawa-bridge recipe): above the water and
a boat passing under the deck, below everyone standing. The shade is
translucent, so AmbientBoats does not count it as scenery hiding the canal.

Deterministic and idempotent: rewrites the four PNGs and registers each key in
config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE generate_osaka.py:
    /Library/Developer/CommandLineTools/usr/bin/python3 tools/make_bridge_tiles.py
"""
import json
from PIL import Image

import house_look as hl

SRC = 'assets/sprites'
A = 32                              # art pixels per cell; the sheet's 2x upscale makes it 64

# the house look (issue #359): the stone in the pack's steel ramp, edged in its navy ink,
# lit from the upper left (tools/house_look.py, docs/generators-and-checks.md)
INK = hl.INK
LO, BASE, HI = hl.tone('steel', 3), hl.tone('steel', 4), hl.tone('steel', 5)
JOINT = hl.tone('steel', 1)         # the line between two coping stones
CAST = INK[:3] + (70,)              # the coping's shadow on the paving
SHADE = [INK[:3] + (35,), INK[:3] + (70,)] + [INK[:3] + (105,)] * 4      # on the water, deck side last

COPING = [INK, HI, BASE, BASE, LO, INK]                  # west to east, lit on its west side
PIER = 3                            # rows of pier at the cell's top and at its bottom
PIER_W = 8
FLAT_BIAS = -200                    # see generate_hokkaido.py FLAT


def pier_row(kind):
    """One row of a pier, west to east: its edge rows ink, its top row lit and its
    bottom row in shadow, its west column lit and its east one in shadow."""
    if kind == 'ink':
        return [INK] * PIER_W
    face = {'hi': HI, 'base': BASE, 'lo': LO}[kind]
    return [INK, LO if kind == 'lo' else HI] + [face] * (PIER_W - 4) + [LO, INK]


# a pier's rows from the top: the bottom of one cell, then the top of the next, so that
# stacked cells join them into one pier per boundary
PIER_TOP = ['base', 'lo', 'ink']                         # rows 0 .. PIER-1
PIER_BOTTOM = ['ink', 'hi', 'base']                      # rows A-PIER .. A-1


def parapet(side):
    """A coping down the deck's `side` edge. Both are lit on their west side, so the
    east one is not the west one's mirror: only the west one casts its shadow
    on the paving (the east one's falls beyond the deck)."""
    im = hl.canvas(A, A)
    px = im.load()
    x0 = 0 if side == 'w' else A - len(COPING)
    for y in range(A):
        for i, colour in enumerate(COPING):
            px[x0 + i, y] = colour
        if side == 'w':
            px[len(COPING), y] = CAST
        if y == A // 2:                                 # a joint in the coping stones
            for i in range(1, len(COPING) - 1):
                px[x0 + i, y] = JOINT
    x0 = 0 if side == 'w' else A - PIER_W
    for y, kind in list(enumerate(PIER_TOP)) + [(A - PIER + i, k) for i, k in enumerate(PIER_BOTTOM)]:
        for i, colour in enumerate(pier_row(kind)):
            px[x0 + i, y] = colour
        if side == 'w':
            px[PIER_W, y] = CAST
    return im


def shade():
    """For the water cell WEST of the deck: the band is on its east edge."""
    im = hl.canvas(A, A)
    px = im.load()
    for y in range(A):
        for i, colour in enumerate(SHADE):
            px[A - len(SHADE) + i, y] = colour
    return im


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


TILES = {
    'bridge-parapet-w': lambda: parapet('w'),
    'bridge-parapet-e': lambda: parapet('e'),
    'bridge-shade-w': shade,
    'bridge-shade-e': lambda: mirror(shade()),
}


def main():
    cfg = json.load(open('config.json'))
    for name, draw in TILES.items():
        key = f'{name}_0_0'
        hl.double(draw()).save(f'{SRC}/{key}.png')
        cfg['spriteMetadata'][key] = {'anchorX': 0.5, 'anchorY': 0.5, 'depthBias': FLAT_BIAS, 'frameCount': 1}
        cfg.setdefault('tileNames', {})[key] = name
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'wrote {len(TILES)} bridge tiles: ' + ' '.join(TILES))


if __name__ == '__main__':
    main()
