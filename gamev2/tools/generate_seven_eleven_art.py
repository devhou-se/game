#!/usr/bin/env python3
"""generate_seven_eleven_art.py — the 7-Eleven on the street (issue #89).

  seven-eleven_0_0   3x4  a two-storey corner store, front on: a flat roof
                          with its parapet and two condensers, an upstairs
                          flat of three sash windows, the white fascia with
                          the orange / green / red stripes and the 7 on its
                          plate, and a lit glass shopfront - magazines in the
                          left window, the copier and posters in the right -
                          either side of the sliding doors

A placeholder until the store is drawn by hand (the issue stays open for
that art; when it lands, this tool and its line in check_generators.ART_TOOLS
go). It replaces the white line drawing that was ported from the Godot game
under the same key, at the same 192x256 size and anchor, so no map, prefab or
config.json changes. The doors are the middle cell of the bottom row, the
cell the `seven-eleven` prefab (tools/make_prefabs.py) leaves open and
tools/generate_konbinis.py wires to the store's interior.

Shaded pixel art with a 1px ink outline, drawn at half size (32px a cell)
and pixel-doubled, in the palette of the store's interior
(tools/generate_konbini_art.py: the same stripes and the same 7). Fully
procedural, and drawn with rectangles and points only (no Pillow ellipse,
polygon or slanted line, which move by a pixel between Pillow versions), so
a re-run draws the same pixels on any Pillow. Needs Pillow.

Run from anywhere (paths are resolved from this file):
  python3 tools/generate_seven_eleven_art.py [--preview out.png]
"""
import os
import sys

from PIL import Image

from generate_station_art import (C, INK, STEEL_LIGHT, STEEL, STEEL_DARK, WHITE, OFFWHITE, SLATE, SLATE_DARK,
                                  RED, RED_DARK, YELLOW, BLUE, BLUE_DARK, CYAN, GREEN, GREEN_DARK,
                                  ORANGE, ORANGE_DARK, CREAM, CREAM_SHADE, new)
from generate_konbini_art import GLASS, GLASS_DARK, SHADOW, LIT, WARM, WARM_DARK, PINK, PURPLE, TEAL

SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
OUT = os.path.join(SPRITES, 'seven-eleven_0_0.png')
W, H = 3 * C, 4 * C                     # half size; doubled to 192x256 (3x4 cells)

ROOF = 9                                # rows 0..ROOF: the roof, seen from a little above
FASCIA = 52                             # rows FASCIA..FASCIA+17: the sign band
SHOP = FASCIA + 18                      # the shopfront's first row
DOOR = (C + 1, 2 * C - 2)               # the sliding doors' columns, inside the middle cell
# the magazine rack in the left window, a row of covers per shelf
COVERS = [
    (RED, YELLOW, CYAN, PINK, WHITE, ORANGE, BLUE, GREEN),
    (PURPLE, WHITE, RED, TEAL, YELLOW, PINK, CYAN, ORANGE),
    (BLUE, ORANGE, GREEN, WHITE, RED, PURPLE, YELLOW, TEAL),
]


def roof(d):
    """The flat roof behind its parapet, and what stands on it."""
    d.rectangle([0, 0, W - 1, ROOF], fill=INK)
    d.rectangle([1, 1, W - 2, 2], fill=STEEL_LIGHT)               # the far coping
    d.rectangle([1, 3, W - 2, ROOF - 3], fill=SLATE)
    d.rectangle([1, 3, W - 2, 3], fill=SLATE_DARK)                # its shadow on the deck
    d.rectangle([1, ROOF - 2, W - 2, ROOF - 1], fill=STEEL_LIGHT)  # the near coping
    d.rectangle([1, ROOF - 2, W - 2, ROOF - 2], fill=WHITE)
    for x in (58, 74):                                            # two condensers
        d.rectangle([x, 1, x + 12, ROOF - 3], fill=INK)
        d.rectangle([x + 1, 2, x + 11, ROOF - 4], fill=STEEL)
        d.rectangle([x + 1, 2, x + 11, 2], fill=STEEL_LIGHT)
        for gx in range(x + 2, x + 11, 2):
            d.rectangle([gx, 4, gx, ROOF - 4], fill=STEEL_DARK)


def sash(d, x, y, drawn):
    """An upstairs window, 22x21 from (x, y): two sliding panes over a sill,
    a curtain drawn across `drawn` of them (0, 1 or 2)."""
    d.rectangle([x, y, x + 21, y + 18], fill=INK)
    d.rectangle([x + 1, y + 1, x + 20, y + 17], fill=STEEL_DARK)
    for n, px in enumerate((x + 2, x + 11)):                      # the panes, 9 wide
        d.rectangle([px, y + 2, px + 8, y + 16], fill=BLUE)
        d.rectangle([px, y + 2, px + 8, y + 6], fill=GLASS)
        d.rectangle([px, y + 7, px + 8, y + 8], fill=GLASS_DARK)
        d.rectangle([px, y + 15, px + 8, y + 16], fill=BLUE_DARK)
        if n < drawn:
            d.rectangle([px, y + 2, px + 8, y + 16], fill=CREAM)
            for fx in (px + 2, px + 5, px + 8):                   # its folds
                d.rectangle([fx, y + 2, fx, y + 16], fill=CREAM_SHADE)
        else:
            for k in range(3):                                    # glare
                d.point((px + 6 - k, y + 3 + k), fill=WHITE)
    d.rectangle([x - 1, y + 19, x + 22, y + 20], fill=INK)        # the sill
    d.rectangle([x, y + 19, x + 21, y + 19], fill=STEEL_LIGHT)


def upstairs(d):
    """The flat over the store: a panelled white wall and three windows."""
    top, bottom = ROOF + 1, FASCIA - 1
    d.rectangle([0, top, W - 1, bottom], fill=INK)
    d.rectangle([1, top, W - 2, bottom], fill=OFFWHITE)
    d.rectangle([1, top, W - 2, top + 1], fill=STEEL)             # the parapet's shadow
    d.rectangle([1, top + 2, W - 2, top + 2], fill=STEEL_LIGHT)
    for y in (top + 3, top + 31):                                 # panel joints, above and below the windows
        d.rectangle([1, y, W - 2, y], fill=WHITE)
    d.rectangle([1, top + 30, W - 2, top + 30], fill=STEEL_LIGHT)
    for x in (32, 63):                                            # ... and between them
        d.rectangle([x, top + 3, x, bottom], fill=STEEL_LIGHT)
    for x, drawn in ((5, 1), (37, 0), (69, 2)):
        sash(d, x, top + 7, drawn)
    d.rectangle([1, bottom - 2, W - 2, bottom], fill=STEEL_LIGHT)  # the wall darkens onto the fascia
    d.rectangle([1, bottom, W - 2, bottom], fill=STEEL)


def logo(d, x, y):
    """The 7 on its plate, 21x22 from (x, y), as on the wall inside
    (generate_konbini_art.logo): orange bar, red stem, the green band across it."""
    d.rectangle([x, y, x + 20, y + 21], fill=INK)
    d.rectangle([x + 1, y + 1, x + 19, y + 20], fill=WHITE)
    d.rectangle([x + 3, y + 3, x + 17, y + 6], fill=ORANGE)
    for row in range(7, 20):                                      # the stem, stepping left as it falls
        sx = x + 13 - (row - 7) // 2
        d.rectangle([sx, y + row, sx + 4, y + row], fill=RED)
        d.point((sx + 4, y + row), fill=RED_DARK)
    d.rectangle([x + 2, y + 9, x + 18, y + 13], fill=WHITE)
    d.rectangle([x + 2, y + 10, x + 18, y + 12], fill=GREEN)
    d.rectangle([x + 2, y + 12, x + 18, y + 12], fill=GREEN_DARK)


def fascia(d):
    """The sign band: white, the three stripes, the 7 in the middle."""
    y = FASCIA
    d.rectangle([0, y, W - 1, y + 17], fill=INK)
    d.rectangle([1, y + 1, W - 2, y + 16], fill=WHITE)
    for top, tall, colour, dark in ((3, 3, ORANGE, ORANGE_DARK), (7, 4, GREEN, GREEN_DARK), (12, 3, RED, RED_DARK)):
        d.rectangle([1, y + top, W - 2, y + top + tall - 1], fill=colour)
        d.rectangle([1, y + top + tall - 1, W - 2, y + top + tall - 1], fill=dark)
    d.rectangle([1, y + 16, W - 2, y + 16], fill=STEEL_LIGHT)
    logo(d, W // 2 - 11, y - 2)


def glazing(d, x0, x1, y0, y1):
    """A shop window over columns x0..x1: its frame and the lit store behind it."""
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=WARM)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 2], fill=LIT)       # the ceiling lights
    d.rectangle([x0 + 1, y0 + 3, x1 - 1, y0 + 3], fill=WHITE)


def glare(d, x, y, n):
    for k in range(n):
        d.point((x - k, y + k), fill=WHITE)
        d.point((x - 3 - k, y + k), fill=LIT)


def shopfront(d):
    """The ground floor: two lit windows, the sliding doors between them."""
    top, sill, foot = SHOP, H - 15, H - 1
    d.rectangle([0, top, W - 1, foot], fill=INK)
    d.rectangle([1, top, W - 2, top + 3], fill=SHADOW)            # the soffit under the fascia
    d.rectangle([1, top + 3, W - 2, top + 3], fill=STEEL_DARK)
    for x0, x1 in ((1, 2), (W - 3, W - 2)):                       # the corner posts
        d.rectangle([x0, top + 4, x1, foot - 1], fill=STEEL_LIGHT)
        d.rectangle([x1 if x0 == 1 else x0, top + 4, x1 if x0 == 1 else x0, foot - 1], fill=STEEL)

    # the left window: a magazine rack faces the street
    x0, x1 = 3, DOOR[0] - 2
    glazing(d, x0, x1, top + 4, sill)
    for row, covers in enumerate(COVERS):
        y = top + 12 + row * 9
        for n, colour in enumerate(covers):
            cx = x0 + 2 + n * 3
            d.rectangle([cx, y, cx + 1, y + 5], fill=colour)
            d.rectangle([cx, y, cx + 1, y], fill=WHITE)           # the masthead
        d.rectangle([x0 + 1, y + 6, x1 - 1, y + 6], fill=WARM_DARK)
        d.rectangle([x0 + 1, y + 7, x1 - 1, y + 7], fill=STEEL)   # the shelf's lip
    glare(d, x1 - 3, top + 6, 6)

    # the right window: two posters on the glass, the copier and a shelf end behind it
    x0, x1 = DOOR[1] + 2, W - 4
    glazing(d, x0, x1, top + 4, sill)
    d.rectangle([x0 + 2, top + 8, x0 + 10, top + 19], fill=RED_DARK)      # a poster: this week's offer
    d.rectangle([x0 + 3, top + 9, x0 + 9, top + 18], fill=RED)
    d.rectangle([x0 + 4, top + 10, x0 + 8, top + 12], fill=YELLOW)
    for y in (top + 14, top + 16):
        d.rectangle([x0 + 4, y, x0 + 8, y], fill=WHITE)
    d.rectangle([x0 + 13, top + 8, x0 + 22, top + 15], fill=BLUE_DARK)    # a sign: the cash machine inside
    d.rectangle([x0 + 14, top + 9, x0 + 21, top + 14], fill=BLUE)
    for x in (x0 + 15, x0 + 17, x0 + 19):
        d.rectangle([x, top + 11, x + 1, top + 12], fill=WHITE)
    d.rectangle([x0 + 2, top + 23, x0 + 12, sill - 1], fill=STEEL_DARK)   # the copier
    d.rectangle([x0 + 3, top + 24, x0 + 11, top + 27], fill=STEEL_LIGHT)
    d.rectangle([x0 + 3, top + 28, x0 + 11, sill - 1], fill=OFFWHITE)
    d.rectangle([x0 + 4, top + 30, x0 + 10, top + 30], fill=STEEL)
    d.rectangle([x0 + 9, top + 25, x0 + 10, top + 26], fill=CYAN)
    for row, stock in enumerate(((GREEN, YELLOW, RED, WHITE), (ORANGE, TEAL, PINK, YELLOW), (CYAN, RED, GREEN, PURPLE))):
        y = top + 20 + row * 7                                            # the end of a shelf block
        for n, colour in enumerate(stock):
            sx = x0 + 15 + n * 3
            d.rectangle([sx, y, sx + 1, y + 3], fill=colour)
        d.rectangle([x0 + 14, y + 4, x1 - 1, y + 4], fill=WARM_DARK)
    glare(d, x1 - 3, top + 6, 6)

    # under the windows: a white stall riser, and the plinth along the pavement
    for x0, x1 in ((3, DOOR[0] - 2), (DOOR[1] + 2, W - 4)):
        d.rectangle([x0, sill + 1, x1, foot - 3], fill=OFFWHITE)
        d.rectangle([x0, sill + 1, x1, sill + 1], fill=WHITE)
        d.rectangle([x0, foot - 4, x1, foot - 3], fill=STEEL_LIGHT)
        d.rectangle([x0, foot - 2, x1, foot - 1], fill=STEEL_DARK)
        d.rectangle([x0, foot - 2, x1, foot - 2], fill=STEEL)

    # the doors: a steel frame, a lit transom, two glass leaves that meet in the middle
    x0, x1 = DOOR
    d.rectangle([x0 - 1, top + 4, x1 + 1, foot - 1], fill=INK)
    d.rectangle([x0, top + 4, x1, foot - 1], fill=STEEL_DARK)
    d.rectangle([x0 + 1, top + 5, x1 - 1, top + 9], fill=GREEN_DARK)      # transom: the green "open" strip
    d.rectangle([x0 + 2, top + 6, x1 - 2, top + 8], fill=GREEN)
    for x in range(x0 + 6, x1 - 5, 4):
        d.rectangle([x, top + 7, x + 1, top + 7], fill=WHITE)
    mid = (x0 + x1) // 2
    for lx0, lx1 in ((x0 + 1, mid - 1), (mid + 2, x1 - 1)):
        d.rectangle([lx0, top + 11, lx1, foot - 3], fill=INK)
        d.rectangle([lx0 + 1, top + 12, lx1 - 1, foot - 4], fill=GLASS)
        d.rectangle([lx0 + 1, top + 12, lx1 - 1, top + 14], fill=LIT)     # the store's lights through the glass
        d.rectangle([lx0 + 1, top + 30, lx1 - 1, foot - 4], fill=GLASS_DARK)
        d.rectangle([lx0 + 1, foot - 8, lx1 - 1, foot - 4], fill=BLUE)    # the kick plate's shade
        d.rectangle([lx0 + 1, top + 24, lx1 - 1, top + 25], fill=WHITE)   # the safety band across each leaf
        glare(d, lx1 - 2, top + 16, 5)
    d.rectangle([mid - 2, top + 20, mid - 2, top + 30], fill=STEEL_LIGHT)  # the pulls
    d.rectangle([mid + 3, top + 20, mid + 3, top + 30], fill=STEEL_LIGHT)
    d.rectangle([x0, foot - 2, x1, foot - 1], fill=STEEL)                 # the threshold
    d.rectangle([x0, foot - 2, x1, foot - 2], fill=STEEL_LIGHT)


def store():
    im, d = new(W, H)
    upstairs(d)
    roof(d)
    shopfront(d)
    fascia(d)
    return im.resize((W * 2, H * 2), Image.NEAREST)


def main():
    im = store()
    im.save(OUT)
    print('wrote', os.path.relpath(OUT), im.size)
    if '--preview' in sys.argv:
        # on paving grey between the two signs that stand beside it in the towns, 3x
        keys = ['7-11-sign-left_0_0', None, '7-11-sign-right_0_0']
        pieces = [im if key is None else Image.open(os.path.join(SPRITES, f'{key}.png')).convert('RGBA') for key in keys]
        sheet = Image.new('RGBA', (sum(p.width for p in pieces) + 16 * (len(pieces) + 1), im.height + 32), '#a9b4bb')
        x = 16
        for piece in pieces:
            sheet.alpha_composite(piece, (x, sheet.height - 16 - piece.height))
            x += piece.width + 16
        path = sys.argv[sys.argv.index('--preview') + 1]
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
        print('wrote', path)


if __name__ == '__main__':
    main()
