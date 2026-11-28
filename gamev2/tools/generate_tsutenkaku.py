#!/usr/bin/env python3
"""generate_tsutenkaku.py — paint the Tsutenkaku Tower landmark sprite.

There is no Tsutenkaku art anywhere in the asset packs. The landmark is a line
drawing that was first drawn here; the drawing is now kept as source in
../art-source/line-art/tsutenkaku_0_0.png and this tool paints it by rule
(tools/line_art.py, issue #271): grey steel lattice, in shade on its right
half, copper roofs, two glazed decks with every fourth bay lit, and the
drawing's red panel as the neon sign. Only colour is laid on: the sprite has
the drawing's outline, lines and cells pixel for pixel, so nothing moves: the
same 8x13 cells (256x416 at half size, pixel-doubled to 512x832), the same legs
and the same open archway between them, and the mast still ends below the
avenue's kerb (issue #181). The picture is a placeholder still, until the
team's own art arrives (issue #70); a PNG of the same size dropped over it
needs no code or map change.

Deterministic and idempotent: rewrites assets/sprites/tsutenkaku_0_0.png and
registers it in config.json spriteMetadata + tileNames (the game only loads a
tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_osaka.py:
    python3 tools/generate_tsutenkaku.py
"""
import json
from PIL import Image

from line_art import template, paint, GREY_STEEL, GREY_SHADE, COPPER, NEON, GLAZED, LAMPLIT

KEY = 'tsutenkaku_0_0'
ROOFS = ((44, 55), (240, 247))        # rows of the drawing, at half size
DECKS = ((56, 96, 10), (248, 270, 11))    # the glazed storeys under them, and the height of a row of cells
CORBELS = ((97, 111), (271, 282))     # and what carries each deck
BAY = 8                               # a deck's cells are 8 wide, the first starting at x = 85


def zone(x, y, accent):
    """The material of a fill pixel of the drawing."""
    if accent:
        return NEON                   # the sign down the tower's face
    for top, bottom, row in DECKS:
        if top <= y <= bottom:        # every fourth bay is lit, a row of cells two bays on from the one above
            return LAMPLIT if ((x - 85) // BAY + 2 * ((y - top - 1) // row)) % 4 == 1 else GLAZED
    if any(a <= y <= b for a, b in ROOFS):
        return COPPER
    return GREY_SHADE if x >= 128 or any(a <= y <= b for a, b in CORBELS) else GREY_STEEL


im = paint(template(KEY), zone)       # half size; doubled to 512x832 = 8x13 cells
big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
big.save(f'assets/sprites/{KEY}.png')

# register so the game loads it: multi-cell sprites anchor on the centre of
# their top-left cell (same rule as the Godot port / the train sprites)
cfg = json.load(open('config.json'))
cfg['spriteMetadata'][KEY] = {'frameCount': 1,
                              'anchorX': round(32 / big.width, 4),
                              'anchorY': round(32 / big.height, 4)}
cfg.setdefault('tileNames', {})[KEY] = 'placeholder-tsutenkaku'
json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

print(f'{KEY}: {big.width}x{big.height}px ({big.width // 64}x{big.height // 64} cells)')
