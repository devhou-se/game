#!/usr/bin/env python3
"""generate_cooler_art.py — the konbini drinks cooler (issue #140).

  office-fridge_0_0   1x2  upright glass-door drinks cooler: steel cabinet,
                           lit header, four lit shelves of bottles and cans
                           behind the door, vent grille at the foot

It replaces the old art under the same key (a slim grey locker that filled
a third of its two solid cells), at the same 64x128 size and anchor, so no
map or config.json changes: tools/generate_konbinis.py still stands it
against a store's back wall (COOLERS) and Interactions.js still sells the
drinks from it.

The cabinet uses the colours of the furniture it stands beside
(office-shelf-*, office-freezer: the same steel greys, outline and glass
blues) with the same lid band on top, and like them it is drawn at half
size and pixel-doubled. The art is fully procedural - no source image, no
font - so a re-run writes a byte-identical PNG. Needs Pillow.

Run from anywhere (paths are resolved from this file):
  python3 tools/generate_cooler_art.py [--preview out.png]
"""
import os
import sys
from PIL import Image, ImageDraw

SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
OUT = os.path.join(SPRITES, 'office-fridge_0_0.png')
W, H = 32, 64                           # half size; doubled to 64x128 (1x2 cells)

# the konbini furniture's own palette (office-shelf-drinks / office-freezer)
INK, STEEL_D, STEEL, STEEL_L, STEEL_HI = '#263238', '#37474f', '#546e7a', '#90a4ae', '#b0bec5'
BLUE_D, BLUE, BLUE_L = '#0277bd', '#039be5', '#81d4fa'
# the lit interior, and what is on the shelves
GLOW, GLOW_HI, WHITE = '#b3e5fc', '#e1f5fe', '#ffffff'
GREEN, GREEN_D, RED, RED_D = '#2baf2b', '#1b7a1b', '#d01716', '#9a1010'
YELLOW, ORANGE, TEAL, CREAM = '#fbc02d', '#ef6c00', '#00838f', '#fff59d'

# Each shelf: (height of its products, [(body, cap-or-None, label-or-None), ...]).
# A product is 2px wide with a 1px gap; a cap makes it a bottle, none a can.
SHELVES = [
    (7, [(GREEN, WHITE, CREAM), (GREEN, WHITE, CREAM), (GREEN, WHITE, CREAM), (TEAL, WHITE, WHITE),
         (TEAL, WHITE, WHITE), (CREAM, GREEN_D, GREEN), (CREAM, GREEN_D, GREEN), (CREAM, GREEN_D, GREEN)]),
    (5, [(RED, None, WHITE), (RED, None, WHITE), (RED, None, WHITE), (YELLOW, None, RED_D),
         (YELLOW, None, RED_D), (BLUE, None, WHITE), (BLUE, None, WHITE), (BLUE, None, WHITE)]),
    (7, [(ORANGE, WHITE, CREAM), (ORANGE, WHITE, CREAM), (BLUE_D, WHITE, BLUE_L), (BLUE_D, WHITE, BLUE_L),
         (BLUE_D, WHITE, BLUE_L), (RED_D, WHITE, WHITE), (RED_D, WHITE, WHITE), (RED_D, WHITE, WHITE)]),
    (5, [(STEEL_D, None, YELLOW), (STEEL_D, None, YELLOW), (GREEN_D, None, CREAM), (GREEN_D, None, CREAM),
         (GREEN_D, None, CREAM), (ORANGE, None, WHITE), (ORANGE, None, WHITE), (ORANGE, None, WHITE)]),
]


def cooler():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = lambda x0, y0, x1, y1, c: d.rectangle([x0, y0, x1, y1], fill=c)

    # cabinet: outline, then the lid band every shelf unit has (rows 1-6)
    box(0, 0, W - 1, H - 2, INK)
    box(1, 1, W - 2, 6, STEEL_L)
    box(1, 5, W - 2, 5, STEEL_HI)

    # lit header: a blue light box with a white wordmark of dashes
    box(1, 8, W - 2, 12, STEEL)
    box(3, 9, W - 4, 11, BLUE)
    box(3, 9, W - 4, 9, BLUE_L)
    for x in (6, 7, 9, 10, 11, 13, 14, 16, 17, 18, 20, 22, 23, 24):
        d.point((x, 10), WHITE)

    # door: steel frame around the glass, handle down the left stile
    top, bottom = 14, 56
    box(1, top, W - 2, bottom, STEEL_L)
    box(1, top, 1, bottom, STEEL)
    box(W - 2, top, W - 2, bottom, STEEL)
    gx0, gx1, gy0, gy1 = 5, W - 4, top + 1, bottom - 1    # the glass
    box(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, INK)
    box(gx0, gy0, gx1, gy1, GLOW)
    box(gx0, gy0, gx1, gy0, WHITE)                        # the strip light
    box(gx0, gy0 + 1, gx1, gy0 + 1, GLOW_HI)
    box(2, 30, 2, 41, INK)                                # handle
    box(3, 30, 3, 41, STEEL_HI)

    # four shelves of drinks, bottoms 10 rows apart
    for i, (tall, row) in enumerate(SHELVES):
        base = gy0 + 10 + i * 10                          # the shelf board's row
        box(gx0, base, gx1, base, STEEL_L)
        if i < len(SHELVES) - 1:
            box(gx0, base + 1, gx1, base + 1, BLUE_L)     # its shadow on the stock below
        for n, (body, cap, label) in enumerate(row):
            x = gx0 + 1 + n * 3
            box(x, base - tall, x + 1, base - 1, body)
            if cap:                                       # bottle: narrow neck + cap
                box(x, base - tall, x + 1, base - tall + 1, GLOW)
                d.point((x, base - tall + 1), body)
                d.point((x, base - tall), cap)
            if label:
                box(x, base - 3, x + 1, base - 2, label)
    # glass glare: two short diagonals, top right (as on office-shelf-glass)
    for k in range(5):
        d.point((gx1 - 1 - k, gy0 + 3 + k), WHITE)
        d.point((gx1 - 4 - k, gy0 + 3 + k), GLOW_HI)

    # foot: kick plate with a vent grille, and the shadow line under it
    box(1, bottom + 2, W - 2, H - 3, STEEL)
    for x in range(4, W - 4, 2):
        box(x, bottom + 3, x, H - 4, STEEL_D)
    box(0, H - 1, W - 1, H - 1, STEEL_D)
    return im.resize((W * 2, H * 2), Image.NEAREST)


def main():
    im = cooler()
    im.save(OUT)
    print('wrote', os.path.relpath(OUT), im.size)
    if '--preview' in sys.argv:
        # beside the furniture it shares a store with, on a floor-ish grey, 3x
        keys = ['office-shelf-drinks_0_0', None, None, 'office-freezer_0_0', 'office-shelf-snacks_0_0']
        sheet = Image.new('RGBA', (64 * len(keys), 128), '#cfd8dc')
        for n, key in enumerate(keys):
            piece = im if key is None else Image.open(os.path.join(SPRITES, f'{key}.png')).convert('RGBA')
            sheet.alpha_composite(piece, (64 * n, 128 - piece.height))
        path = sys.argv[sys.argv.index('--preview') + 1]
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
        print('wrote', path)


if __name__ == '__main__':
    main()
