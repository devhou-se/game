#!/usr/bin/env python3
"""make_bridge_tiles.py — a parapet and a shadow for a bridge deck over water (issue #180).

A bridge in a generated room is plain paving laid across a gap in the water
(Osaka's street over the Dotonbori canal): nothing says "bridge" but the
boats being cut off at its edge. These four one-cell pieces dress the two
sides of a deck that runs north-south:

  bridge-parapet-w_0_0   a stone coping down the WEST edge of a deck cell, with
  bridge-parapet-e_0_0   a pier at the cell's top and bottom (stacked cells
                         join them into one pier per boundary) and a thin
                         shadow on the paving beside it. It takes the outer
                         14px of the cell, so it needs no collider: a walker
                         in that cell stands clear of it, and the deck keeps
                         its full width (#139).
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

SRC = 'assets/sprites'
A = 32                              # art pixels per cell; the sheet's 2x upscale makes it 64

# the ported stonework's own palette (castle-wall-siding)
INK, DARK = (8, 13, 22, 255), (71, 72, 93, 255)
MID, LIGHT, SHINE = (164, 176, 181, 255), (188, 199, 204, 255), (225, 233, 236, 255)
CAST = (8, 13, 22, 70)              # the coping's shadow on the paving
SHADE = [(8, 13, 40, 35), (8, 13, 40, 70)] + [(8, 13, 40, 105)] * 4               # on the water, deck side last

COPING = [INK, SHINE, LIGHT, LIGHT, MID, DARK, CAST]      # west parapet, outside edge first
PIER = 3                            # rows of pier at the cell's top and at its bottom
FLAT_BIAS = -200                    # see generate_hokkaido.py FLAT


def parapet():
    """The west one; the east one is its mirror."""
    im = Image.new('RGBA', (A, A), (0, 0, 0, 0))
    px = im.load()
    for y in range(A):
        for x, colour in enumerate(COPING):
            px[x, y] = colour
        if y == A // 2:                                 # a joint in the coping stones
            for x in range(1, 5):
                px[x, y] = MID
    for y in list(range(PIER)) + list(range(A - PIER, A)):
        inner = y == PIER - 1 or y == A - PIER          # the pier's edge facing the next stone
        for x in range(8):
            px[x, y] = INK if (x in (0, 7) or inner) else SHINE if x < 4 else LIGHT
        px[8, y] = CAST
    return im


def shade():
    """For the water cell WEST of the deck: the band is on its east edge."""
    im = Image.new('RGBA', (A, A), (0, 0, 0, 0))
    px = im.load()
    for y in range(A):
        for i, colour in enumerate(SHADE):
            px[A - len(SHADE) + i, y] = colour
    return im


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


TILES = {
    'bridge-parapet-w': parapet,
    'bridge-parapet-e': lambda: mirror(parapet()),
    'bridge-shade-w': shade,
    'bridge-shade-e': lambda: mirror(shade()),
}


def main():
    cfg = json.load(open('config.json'))
    for name, draw in TILES.items():
        key = f'{name}_0_0'
        draw().resize((A * 2, A * 2), Image.NEAREST).save(f'{SRC}/{key}.png')
        cfg['spriteMetadata'][key] = {'anchorX': 0.5, 'anchorY': 0.5, 'depthBias': FLAT_BIAS, 'frameCount': 1}
        cfg.setdefault('tileNames', {})[key] = name
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'wrote {len(TILES)} bridge tiles: ' + ' '.join(TILES))


if __name__ == '__main__':
    main()
