#!/usr/bin/env python3
"""generate_seven_eleven_art.py — the 7-Eleven on the street (issue #89).

  seven-eleven_0_0   3x4  a one-storey store in the manner of the GuttyKreum
                          city pack: the flat roof seen from above, panelled
                          inside its steel coping with two condensers on it,
                          the white fascia with the orange / green / red
                          stripes and the 7 on its plate, and a dark glass
                          shopfront with the shelves showing through, either
                          side of the sliding doors

A placeholder until the store is drawn by hand (the issue stays open for
that art; when it lands, this tool and its line in check_generators.ART_TOOLS
go). Same 192x256 size and anchor as the picture it replaces, so no map,
prefab or config.json changes. The doors are the middle cell of the bottom
row, the cell the `seven-eleven` prefab (tools/make_prefabs.py) leaves open
and tools/generate_konbinis.py wires to the store's interior.

Every colour is one the pack's own sheets use (art-source/GuttyKreum), the
outline is the pack's blue, not black, and the glass is the pack's dark
window with a slanted glare. Drawn at half size (32px a cell) and
pixel-doubled, with rectangles and points only (no Pillow ellipse, polygon or
slanted line, which move by a pixel between Pillow versions), so a re-run
draws the same pixels on any Pillow. Needs Pillow.

Run from anywhere (paths are resolved from this file):
  python3 tools/generate_seven_eleven_art.py [--preview out.png]
"""
import os
import sys

from PIL import Image, ImageDraw

SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
OUT = os.path.join(SPRITES, 'seven-eleven_0_0.png')
C = 32
W, H = 3 * C, 4 * C                     # half size; doubled to 192x256 (3x4 cells)


def rgb(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


INK, EDGE = rgb('0a1627'), rgb('172459')
ROOF, ROOF_LIGHT, ROOF_JOINT, ROOF_DARK = rgb('5b6c79'), rgb('698592'), rgb('444f5e'), rgb('2e4040')
STEEL, STEEL_LIGHT, STEEL_DARK = rgb('94a2a8'), rgb('d1e2eb'), rgb('575c6d')
PLASTER, WHITE, WHITE_SHADE, GREY = rgb('e4cecc'), rgb('fafcfd'), rgb('dae2e4'), rgb('a4b0b5')
GLASS, GLASS_DARK, GLARE, GLASS_LIGHT = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396'), rgb('8689a6')
ORANGE, ORANGE_DARK, RED, RED_DARK = rgb('e78d7b'), rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')
GREEN, GREEN_DARK = rgb('508582'), rgb('4a6262')
BLUE, BLUE_DARK, BLUE_LIGHT = rgb('588cc6'), rgb('425faa'), rgb('7db9fa')

EAVE = 44                               # rows 0..EAVE-1: the roof, seen from above
FASCIA = EAVE + 4                       # rows FASCIA..FASCIA+19: the sign band
SHOP = FASCIA + 24                      # the shopfront's first row
FOOT = H - 6                            # the step's first row
DOOR = (C + 2, 2 * C - 3)               # the sliding doors' columns, inside the middle cell
WINDOWS = ((5, DOOR[0] - 6), (DOOR[1] + 6, W - 6))
GOODS = (ORANGE, BLUE, WHITE, GREEN, RED, BLUE_LIGHT, ORANGE_DARK, GLASS_LIGHT)


def roof(d):
    d.rectangle([0, 0, W - 1, EAVE - 1], fill=EDGE)
    d.rectangle([1, 1, W - 2, EAVE - 2], fill=STEEL)                 # the coping
    d.rectangle([1, 1, W - 2, 1], fill=STEEL_LIGHT)
    d.rectangle([1, 1, 1, EAVE - 2], fill=STEEL_LIGHT)
    d.rectangle([4, 4, W - 5, EAVE - 5], fill=EDGE)
    x0, y0, x1, y1 = 5, 5, W - 6, EAVE - 6
    d.rectangle([x0, y0, x1, y1], fill=ROOF)
    for n, x in enumerate(range(x0, x1, 9)):                         # panels, their joints staggered
        d.rectangle([x, y0, x, y1], fill=ROOF_JOINT)
        d.rectangle([x + 1, y0, min(x + 8, x1), y0], fill=ROOF_LIGHT)
        for y in range(y0 + 4 + n % 3 * 9, y1, 17):
            d.rectangle([x + 1, y, min(x + 8, x1), y], fill=ROOF_JOINT)
    d.rectangle([x0, y1 - 1, x1, y1], fill=ROOF_DARK)
    d.rectangle([x1 - 2, y0, x1, y1], fill=ROOF_DARK)
    for x in (15, 60):                                               # the condensers and their shade
        d.rectangle([x, 10, x + 19, 25], fill=INK)
        d.rectangle([x + 1, 11, x + 18, 24], fill=STEEL)
        d.rectangle([x + 1, 11, x + 18, 11], fill=STEEL_LIGHT)
        d.rectangle([x + 3, 14, x + 12, 22], fill=STEEL_DARK)
        d.rectangle([x + 5, 16, x + 10, 20], fill=ROOF_DARK)
        d.rectangle([x + 14, 14, x + 16, 15], fill=GLASS)
        d.rectangle([x + 14, 18, x + 16, 19], fill=GLASS)
        d.rectangle([x + 2, 26, x + 19, 27], fill=ROOF_DARK)


def fascia(d):
    d.rectangle([0, EAVE, W - 1, EAVE], fill=STEEL_LIGHT)
    d.rectangle([0, EAVE + 1, W - 1, EAVE + 2], fill=GREY)
    d.rectangle([0, EAVE + 3, W - 1, EAVE + 3], fill=EDGE)
    y = FASCIA
    d.rectangle([0, y, W - 1, y + 19], fill=WHITE)
    d.rectangle([0, y + 16, W - 1, y + 19], fill=WHITE_SHADE)
    for row, (colour, shade) in zip((4, 8, 12), ((ORANGE, ORANGE_DARK), (GREEN, GREEN_DARK), (RED, RED_DARK))):
        d.rectangle([1, y + row, W - 2, y + row + 2], fill=colour)
        d.rectangle([1, y + row + 2, W - 2, y + row + 2], fill=shade)
    d.rectangle([0, y, 0, y + 19], fill=EDGE)
    d.rectangle([W - 1, y, W - 1, y + 19], fill=EDGE)
    d.rectangle([0, y + 20, W - 1, y + 22], fill=GLASS_DARK)         # the fascia's shade on the glass
    d.rectangle([0, y + 23, W - 1, y + 23], fill=EDGE)
    x0, x1 = W // 2 - 11, W // 2 + 10                               # the plate, and the 7 on it
    d.rectangle([x0, y - 2, x1, y + 21], fill=EDGE)
    d.rectangle([x0 + 1, y - 1, x1 - 1, y + 20], fill=WHITE)
    d.rectangle([x0 + 1, y + 18, x1 - 1, y + 20], fill=WHITE_SHADE)
    d.rectangle([x0 + 4, y + 2, x1 - 4, y + 5], fill=ORANGE)
    d.rectangle([x0 + 4, y + 5, x1 - 4, y + 5], fill=ORANGE_DARK)
    d.rectangle([x0 + 4, y + 6, x0 + 6, y + 8], fill=ORANGE)
    for n in range(11):
        x = x1 - 5 - n // 2
        d.rectangle([x - 2, y + 6 + n, x, y + 6 + n], fill=RED)
    d.rectangle([x0 + 5, y + 10, x1 - 3, y + 11], fill=GREEN)


def glare(d, x0, y0, x1, y1, step, colour, shade):
    """Slanted streaks across a pane, a point at a time."""
    for k in range(-40, 40, step):
        for t in range(y1 - y0 + 1):
            x, y = x0 + k + t, y1 - t
            if x0 <= x <= x1:
                d.point((x, y), colour)
                if x + 1 <= x1:
                    d.point((x + 1, y), shade)


def shopfront(d):
    d.rectangle([0, SHOP, W - 1, FOOT - 1], fill=PLASTER)
    for x0, x1 in WINDOWS:
        d.rectangle([x0 - 1, SHOP + 1, x1 + 1, SHOP + 36], fill=EDGE)
        d.rectangle([x0, SHOP + 2, x1, SHOP + 35], fill=GLASS)
        glare(d, x0, SHOP + 2, x1, SHOP + 35, 11, GLARE, GLASS_DARK)
        d.rectangle([x0, SHOP + 2, x1, SHOP + 3], fill=GLASS_DARK)
        for row, y in enumerate((SHOP + 12, SHOP + 20, SHOP + 28)):  # the shelves through the glass
            d.rectangle([x0 + 1, y + 5, x1 - 1, y + 5], fill=GLASS_LIGHT)
            for n, x in enumerate(range(x0 + 2, x1 - 1, 3)):
                d.rectangle([x, y + 1, x + 1, y + 4], fill=GOODS[(n + row * 3) % len(GOODS)])
        d.rectangle([x0 - 1, SHOP + 37, x1 + 1, FOOT - 1], fill=GREY)  # the stall riser
        d.rectangle([x0 - 1, SHOP + 37, x1 + 1, SHOP + 37], fill=STEEL_LIGHT)
        d.rectangle([x0 - 1, FOOT - 2, x1 + 1, FOOT - 1], fill=STEEL_DARK)
    for x in (0, WINDOWS[0][1] + 2, WINDOWS[1][0] - 5, W - 4):       # the piers
        d.rectangle([x, SHOP, x + 3, FOOT - 1], fill=WHITE)
        d.rectangle([x + 3, SHOP, x + 3, FOOT - 1], fill=WHITE_SHADE)
    d.rectangle([0, SHOP, 0, FOOT - 1], fill=EDGE)
    d.rectangle([W - 1, SHOP, W - 1, FOOT - 1], fill=EDGE)

    x0, x1 = DOOR                                                    # the doors: a transom and two leaves
    d.rectangle([x0 - 1, SHOP, x1 + 1, FOOT - 1], fill=EDGE)
    d.rectangle([x0, SHOP + 1, x1, SHOP + 5], fill=GREEN_DARK)
    d.rectangle([x0 + 3, SHOP + 2, x1 - 3, SHOP + 4], fill=GREEN)
    mid = (x0 + x1) // 2
    for lx0, lx1 in ((x0, mid - 1), (mid + 2, x1)):
        d.rectangle([lx0, SHOP + 6, lx1, FOOT - 1], fill=STEEL)
        d.rectangle([lx0 + 1, SHOP + 7, lx1 - 1, FOOT - 4], fill=BLUE_DARK)
        d.rectangle([lx0 + 1, SHOP + 7, lx1 - 1, SHOP + 8], fill=GLASS)
        for t in range(30):
            x, y = lx0 + 2 + t // 3, FOOT - 6 - t
            if x <= lx1 - 2:
                d.point((x, y), BLUE)
                d.point((x + 1, y), BLUE_LIGHT)
        d.rectangle([lx0 + 1, FOOT - 3, lx1 - 1, FOOT - 1], fill=STEEL_DARK)
    d.rectangle([mid, SHOP + 6, mid + 1, FOOT - 1], fill=INK)
    d.rectangle([mid - 2, SHOP + 22, mid - 1, SHOP + 27], fill=STEEL_LIGHT)   # the pulls
    d.rectangle([mid + 2, SHOP + 22, mid + 3, SHOP + 27], fill=STEEL_LIGHT)


def step(d):
    d.rectangle([0, FOOT, W - 1, FOOT + 1], fill=GREY)
    d.rectangle([0, FOOT, W - 1, FOOT], fill=STEEL_LIGHT)
    d.rectangle([0, FOOT + 2, W - 1, FOOT + 4], fill=ROOF_LIGHT)
    d.rectangle([0, FOOT + 4, W - 1, FOOT + 4], fill=ROOF_JOINT)
    d.rectangle([0, FOOT + 5, W - 1, FOOT + 5], fill=INK)
    d.rectangle([0, FOOT, 0, FOOT + 5], fill=EDGE)
    d.rectangle([W - 1, FOOT, W - 1, FOOT + 5], fill=EDGE)


def store():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    roof(d)
    shopfront(d)
    fascia(d)
    step(d)
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
