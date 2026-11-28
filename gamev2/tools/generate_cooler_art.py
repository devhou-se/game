#!/usr/bin/env python3
"""generate_cooler_art.py — the konbini drinks cooler (issue #140).

  office-fridge_0_0   1x2  upright glass-door drinks cooler: steel cabinet,
                           a blue name plate, four shelves of bottles and cans
                           behind the dark glass door, vent grille at the foot

It replaces the old art under the same key (a slim grey locker that filled
a third of its two solid cells), at the same 64x128 size and anchor, so no
map or config.json changes: tools/generate_konbinis.py still stands it
against a store's back wall (COOLERS) and Interactions.js still sells the
drinks from it.

The look is the house look of the GuttyKreum pack (the approved Sendai /
Kanazawa / Fukuoka art): every colour is one the pack's own sheets use
(art-source/GuttyKreum), the outline is the pack's navy, not black, the
cabinet is the pack's steel lit from the upper left, and the door is the
pack's dark window with a slanted glare (generate_sendai_art.pane), the
drinks showing through it, each a lit side and a shaded side. Drawn at
half size and pixel-doubled, with rectangles and points only. The art is
fully procedural - no source image, no font - so a re-run draws the same
pixels. Needs Pillow.

Run from anywhere (paths are resolved from this file):
  python3 tools/generate_cooler_art.py [--preview out.png]
"""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_sendai_art import pane  # noqa: E402

SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
OUT = os.path.join(SPRITES, 'office-fridge_0_0.png')
W, H = 32, 64                           # half size; doubled to 64x128 (1x2 cells)


def rgb(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


INK, EDGE = rgb('0a1627'), rgb('172459')
WHITE, WHITE_LO = rgb('fafcfd'), rgb('dae2e4')
STEEL_HI, STEEL_MID, STEEL, STEEL_LO = rgb('d1e2eb'), rgb('a4b0b5'), rgb('94a2a8'), rgb('575c6d')
SLATE, SLATE_LO = rgb('5b6c79'), rgb('444f5e')
GOLD_HI, GOLD, GOLD_LO = rgb('e3c587'), rgb('c6a663'), rgb('a7843b')
RED_LIT, RED_HI, RED, RED_LO = rgb('e78d7b'), rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')
SKY, BLUE_HI, BLUE, BLUE_LO = rgb('7db9fa'), rgb('588cc6'), rgb('425faa'), rgb('314b8e')
GREEN, GREEN_LO, TEAL, TEAL_LO = rgb('83af6f'), rgb('678e57'), rgb('508582'), rgb('4a6262')
SHELF = rgb('8689a6')                   # a shelf board, seen through the glass

# the drinks: (lit side, shaded side), and a label the same way
TEA, WATER, MILK = (GREEN, GREEN_LO), (TEAL, TEAL_LO), (WHITE, WHITE_LO)
COLA, LEMON, SODA = (RED, RED_LO), (GOLD_HI, GOLD), (BLUE_HI, BLUE)
JUICE, SPORTS, CHERRY = (RED_LIT, RED_HI), (SKY, BLUE_HI), (RED_HI, RED)
COFFEE = (STEEL, STEEL_LO)
L_WHITE, L_GOLD, L_RED = (WHITE, WHITE_LO), (GOLD, GOLD_LO), (RED, RED_LO)
L_GREEN, L_BLUE = (GREEN, GREEN_LO), (BLUE, BLUE_LO)

# Each shelf: (height of its products, [(body, cap-or-None, label-or-None), ...]).
# A product is 2px wide with a 1px gap; a cap makes it a bottle, none a can.
SHELVES = [
    (7, [(TEA, WHITE, L_WHITE)] * 3 + [(WATER, WHITE, L_WHITE)] * 2 + [(MILK, TEAL, L_GREEN)] * 3),
    (5, [(COLA, None, L_WHITE)] * 3 + [(LEMON, None, L_RED)] * 2 + [(SODA, None, L_WHITE)] * 3),
    (7, [(JUICE, WHITE, L_WHITE)] * 2 + [(SPORTS, WHITE, L_BLUE)] * 3 + [(CHERRY, WHITE, L_WHITE)] * 3),
    (5, [(COFFEE, None, L_GOLD)] * 2 + [(TEA, None, L_WHITE)] * 3 + [(JUICE, None, L_WHITE)] * 3),
]


def cooler():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = lambda x0, y0, x1, y1, c: d.rectangle([x0, y0, x1, y1], fill=c)

    # cabinet: navy outline and the shadow line under it, then the steel lid (rows 1-6)
    box(0, 0, W - 1, H - 2, EDGE)
    box(0, H - 1, W - 1, H - 1, INK)
    box(1, 1, W - 2, 6, STEEL)
    box(1, 1, W - 2, 1, STEEL_HI)
    box(1, 1, 1, 6, STEEL_HI)
    box(2, 6, W - 2, 6, STEEL_LO)
    box(W - 2, 2, W - 2, 6, STEEL_LO)

    # header: a blue name plate with a white wordmark of dashes
    box(1, 8, W - 2, 12, STEEL_LO)
    box(3, 9, W - 4, 11, BLUE)
    box(3, 9, W - 4, 9, BLUE_HI)
    box(3, 11, W - 4, 11, BLUE_LO)
    for x in (6, 7, 9, 10, 11, 13, 14, 16, 17, 18, 20, 22, 23, 24):
        d.point((x, 10), WHITE)

    # door: steel frame around the glass, handle down the left stile
    top, bottom = 14, 56
    box(1, top, W - 2, bottom, STEEL_MID)
    box(1, top, 1, bottom, STEEL_HI)
    box(W - 3, top, W - 3, bottom, STEEL)
    box(W - 2, top, W - 2, bottom, STEEL_LO)
    box(2, bottom, W - 2, bottom, STEEL_LO)
    gx0, gx1, gy0, gy1 = 5, W - 4, top + 1, bottom - 1    # the glass
    box(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, EDGE)
    pane(d, gx0, gy0, gx1, gy1, 11)
    glass = im.copy()                                     # what shows past a bottle's neck
    box(2, 30, 2, 41, INK)                                # handle
    box(3, 30, 3, 41, STEEL_HI)

    # four shelves of drinks, bottoms 10 rows apart
    for i, (tall, row) in enumerate(SHELVES):
        base = gy0 + 10 + i * 10                          # the shelf board's row
        box(gx0, base, gx1, base, SHELF)
        for n, ((lit, shade), cap, label) in enumerate(row):
            x = gx0 + 1 + n * 3
            box(x, base - tall, x, base - 1, lit)
            box(x + 1, base - tall, x + 1, base - 1, shade)
            if cap:                                       # bottle: a cap, the glass beside its neck
                d.point((x, base - tall), cap)
                for y in (base - tall, base - tall + 1):
                    d.point((x + 1, y), glass.getpixel((x + 1, y)))
            if label:
                d.point((x, base - 3), label[0])
                d.point((x, base - 2), label[0])
                d.point((x + 1, base - 3), label[1])
                d.point((x + 1, base - 2), label[1])

    # foot: kick plate with a vent grille
    box(1, bottom + 2, W - 2, H - 3, SLATE)
    box(1, bottom + 2, W - 2, bottom + 2, STEEL)
    for x in range(4, W - 4, 2):
        box(x, bottom + 3, x, H - 4, SLATE_LO)
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
