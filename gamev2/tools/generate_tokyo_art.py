#!/usr/bin/env python3
"""generate_tokyo_art.py — paint Tokyo Tower and Tokyo Station (issues #70, #271).

The two Tokyo landmarks came over from the Godot game as the team's white line
drawings, which clashed with the GuttyKreum buildings round them. They are
those drawings still, with colour laid on: the line art is kept as source in
../art-source/line-art/ and painted by rule (tools/line_art.py: its docstring
has the rules), at half size (one pixel = one pixel of a 32px tile) and
pixel-doubled, lit from the top left, in the house palette. Nothing is redrawn:
this tool only says which part of a drawing is which material. THESE ARE
PLACEHOLDERS STILL (#70 waits on the team's art): a PNG of the same size
dropped over one of them needs no code or map change (and this tool then stops
being run for it).

  tokyo-tower_0_0     8x15  Tokyo Tower: the drawing's lattice in the real
                            tower's bands of vermilion and white, brighter on
                            the drawing's centre panel (the face turned to us)
                            and in shade to its right; the mast and the decks
                            white, their grid cells glass; concrete footings
                            under the legs
  tokyo-tower-feet    8x3   the bottom three rows of that picture, cut from it
                            here: Park's copy of the feet (the stitched city
                            drops it, `?stitch=0` shows it)
  tokyo-station_0_0   41x8  Tokyo Station's Marunouchi front: red brick banded
                            in stone under slate roofs, copper on the caps, the
                            dormers, the crest and the porch, granite at the
                            foot; every pane of the drawing is glass, about one
                            window in ten lamplit

The one hard rule: a sprite's alpha is its drawing's, pixel for pixel
(line_art.paint asserts it, tools/tests/landmark-placeholders.test.js checks
the saved files). So the sizes, the outlines and what the map relies on are the
drawings' own, as they were before #70: the cells you walk through between the
tower's feet, the station's clear forecourt cells and its door cell, the rows
the passing train shows on behind the station's roof. The towers are solid
again (the drawing fills its lattice), and to change an outline is to change
the drawing in ../art-source/line-art/, which then has to fit the map.

Deterministic and idempotent: rewrites the three PNGs in assets/sprites/ and
nothing else (the keys are registered already: no config.json write). Needs
Pillow and its sibling tools, which it imports: line_art, generate_hokkaido,
generate_sapporo_art. Run from gamev2/:
    python3 tools/generate_tokyo_art.py [--sheet sheet.png]
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import rgb, WHITE, SNOW, SNOW_LO, STONE_LO, STONE_DK, GLASS_DK    # noqa: E402
from generate_sapporo_art import BRICK, BRICK_HI, BRICK_DK, SLATE, SNOW_SH, DARK         # noqa: E402
from line_art import (template, paint, Plan,                                             # noqa: E402
                      BRICKWORK, BRICK_SHADE, STONEWORK, STONE_SHADE, SLATES, SLATE_SHADE,
                      WHITE_STEEL, WHITE_SHADE, COPPER, COPPER_SHADE, CONCRETE, SHADOW, GLAZED, LAMPLIT)

SPR = 'assets/sprites'
C = 32                                   # one cell, in drawn (half-size) pixels


# ==============================================================================
# Tokyo Tower
# ==============================================================================
# the tower's paint: the palette's red a step towards orange, to stand off the station's brick
VERM, VERM_HI, VERM_LO, VERM_DK = rgb('e06a45'), rgb('f59470'), rgb('b84d2e'), rgb('8f3a26')
VERMILION = (VERM, VERM_HI, VERM_LO, VERM_DK)
VERM_LIT = (VERM_HI, rgb('ffb597'), VERM, VERM_DK)           # the face turned to us
VERM_SHADE = (VERM_LO, VERM, VERM_DK, rgb('5e2a22'))
PAINT_LIT = (WHITE, WHITE, SNOW, STONE_LO)                   # the white bands (WHITE_STEEL) on that face
DECK = (SNOW, WHITE, SNOW_LO, STONE_DK)                      # the mast and the decks: white too, but another
DECK_SHADE = (SNOW_LO, SNOW, SNOW_SH, STONE_DK)              # material, so only their grid cells are panes
RED_BANDS = ((126, 156), (190, 237), (268, 312), (346, 378), (414, 469))   # rows; edges on the drawing's members
FOOTING = 470                            # the legs' last rows: what they stand on
PANEL = 114                              # where the drawing's red panel starts: left of it is lit, right in shade


def tower_zone(x, y, accent):
    """The material of a fill pixel of the tower; `accent` is the drawing's red panel."""
    lattice = 97 <= x <= 165 and y <= 237                        # the shaft, standing on the main deck's roof
    if y < 126 or 205 <= y <= 267 and not lattice:
        if 113 <= x <= 143 and 100 <= y <= 118:
            return GLAZED                                        # the top deck's windows
        return DECK_SHADE if x > 140 else DECK
    if y >= FOOTING:
        return CONCRETE
    red = any(a <= y <= b for a, b in RED_BANDS)
    if accent:
        return VERM_LIT if red else PAINT_LIT
    if x < PANEL:
        return VERMILION if red else WHITE_STEEL
    return VERM_SHADE if red else WHITE_SHADE


def tower():
    tpl = template('tokyo-tower_0_0')    # 256 x 480
    # by the pixel: the bands cut across the lattice's triangles. The decks' cells are 8 to 12 pixels
    return paint(tpl, tower_zone, by_region=False, pane=12, walls=(DECK, DECK_SHADE),
                 lit=lambda x, y: (x // 3 + y // 14 * 5) % 7 == 0)


# ==============================================================================
# Tokyo Station
# ==============================================================================
SW = 41 * C                              # 1312: the drawing is mirrored about x 655 / 656
BRICK_LIT = (BRICK_HI, BRICK_HI, BRICK, BRICK_DK)            # a face turned to the light
SLATE_LIT = (STONE_LO, STONE_LO, SLATE, GLASS_DK)
CLOCK = (WHITE, WHITE, SNOW_LO, DARK)                        # a clock's face; its hands are the lines on it
FACES = {                                # a material as it faces us, the light (<) and away from it (>)
    'brick': (BRICK_LIT, BRICKWORK, BRICK_SHADE),
    'stone': (STONEWORK, STONEWORK, STONE_SHADE),
    'slate': (SLATE_LIT, SLATES, SLATE_SHADE),
    'copper': (COPPER, COPPER, COPPER_SHADE),
    'granite': (CONCRETE, CONCRETE, CONCRETE),
    'dark': (SHADOW, SHADOW, SHADOW),
    'glass': (GLAZED, GLAZED, GLAZED),
    'lit': (LAMPLIT, LAMPLIT, LAMPLIT),
    'clock': (CLOCK, CLOCK, CLOCK),
}


def station_plan():
    """The west half of the station, by material."""
    p = Plan((SW // 2, 256), 'brick')
    # ---- the wings, by height ---------------------------------------------------
    p.box('slate', 0, 0, 655, 125)
    p.box('slate<', 0, 69, 655, 76)                              # the top slope, to the sky
    p.poly('slate<', (30, 70), (76, 70), (76, 78), (36, 114), (30, 114))    # the hip at the west end
    p.box('stone', 0, 127, 655, 136)
    p.box('brick', 0, 139, 655, 178)
    p.box('stone', 0, 181, 655, 185)
    p.box('brick', 0, 186, 655, 207)
    p.box('stone', 0, 191, 655, 193)
    p.box('stone', 0, 201, 655, 202)
    p.box('granite', 0, 208, 655, 255)
    for x in (283, 361, 453, 531):                               # the tall dormers: a copper hood, a window
        p.box('copper', x, 95, x + 7, 104)
        p.box('stone', x - 2, 106, x + 9, 112)
        p.box('glass', x + 2, 107, x + 5, 110)
    for x in (60, 309, 334, 479, 504):                           # and the low ones
        p.box('copper', x + 1, 104, x + 6, 106)
        p.box('glass', x, 108, x + 7, 112)
    # ---- the end turret: two lanterns, one behind the other ---------------------
    p.box('brick', 0, 60, 31, 126)
    p.box('brick<', 0, 80, 16, 112)
    for y in (44, 100):
        p.box('slate<', 0, y, 15, y + 22)
        p.box('slate>', 17, y, 31, y + 22)
        p.box('copper', 9, y - 4, 23, y + 6)                     # the cap
        p.box('copper', 13, y + 7, 19, y + 22)                   # and its drop
    p.box('stone', 0, 122, 31, 146)
    p.box('brick', 0, 147, 31, 186)
    p.box('stone', 0, 187, 31, 194)
    p.box('brick', 0, 195, 31, 209)
    p.box('granite', 0, 210, 31, 230)
    # ---- the small towers: the one in the wing, the one by the centre block ------
    for x in (384, 554):
        w = 425 - 384 if x == 384 else 585 - 554
        p.box('slate', x, 90, x + w, 125)
        p.box('slate<', x, 90, x + 11, 123)
        p.box('slate>', x + w - 10, 90, x + w, 123)
        p.box('copper', x + w // 2 - 6, 90, x + w // 2 + 6, 107)
        p.box('stone', x, 124, x + w, 146)
        p.box('brick', x, 147, x + w, 190)
        p.box('granite', x, 215, x + w, 230)
    # ---- the domed pavilion --------------------------------------------------------
    p.box('brick', 96, 126, 260, 255)
    p.box('slate<', 96, 28, 176, 150)
    p.box('slate>', 177, 28, 260, 150)
    p.poly('slate', (167, 30), (185, 30), (199, 78), (153, 78))  # the dome's face to us
    p.box('copper', 168, 18, 184, 31)                            # its cap
    p.box('glass', 145, 54, 153, 64); p.box('lit', 171, 57, 181, 68); p.box('glass', 199, 54, 207, 64)
    p.box('brick<', 139, 66, 151, 98)                            # the drum
    p.box('brick', 152, 76, 199, 97)
    p.box('brick>', 200, 66, 213, 98)
    p.box('stone', 152, 75, 199, 78)
    p.box('stone<', 131, 64, 138, 92); p.box('stone>', 214, 64, 221, 92)     # the piers at its corners
    p.poly('stone<', (131, 86), (138, 86), (158, 100), (158, 107), (150, 107))
    p.poly('stone>', (221, 86), (214, 86), (194, 100), (194, 107), (202, 107))
    p.box('stone', 152, 97, 200, 106)                            # the balustrade
    p.poly('slate', (150, 148), (150, 125), (160, 110), (176, 105), (192, 110), (202, 125), (202, 148),
           (196, 148), (196, 128), (176, 116), (156, 128), (156, 148))      # the round gable's roof
    p.poly('brick', (153, 150), (153, 132), (164, 120), (188, 120), (199, 132), (199, 150))
    p.box('brick', 130, 150, 222, 158)
    p.box('stone', 160, 131, 192, 139)                           # the hood over the clock
    p.box('stone', 160, 138, 192, 163)                           # the clock's surround
    p.box('clock', 170, 142, 182, 156)
    p.box('stone', 112, 113, 132, 127); p.box('stone>', 220, 113, 240, 127)  # the corner blocks
    p.box('slate<', 96, 119, 112, 127); p.box('slate>', 241, 119, 258, 127)
    p.box('brick<', 96, 128, 129, 240)                           # the faces turned to the west
    p.box('brick>', 223, 128, 260, 240)                          # and to the east
    p.box('stone<', 96, 127, 129, 136); p.box('stone>', 223, 127, 260, 136)
    p.box('stone', 124, 146, 130, 204); p.box('stone>', 221, 146, 227, 204)  # the columns
    p.box('stone', 130, 158, 222, 163)
    p.box('stone', 160, 179, 192, 190)                           # the balcony
    p.box('granite', 130, 239, 222, 255)
    # ---- the centre block ------------------------------------------------------------
    p.box('slate', 600, 30, 655, 128)
    p.poly('slate<', (576, 66), (640, 33), (606, 128), (600, 128), (608, 78))
    p.box('copper', 638, 0, 655, 31)                             # the crest
    p.box('stone', 586, 128, 608, 137)
    p.box('brick', 609, 128, 623, 190)                           # the pier
    p.box('stone', 613, 130, 619, 161)
    p.poly('stone', (624, 135), (624, 120), (640, 106), (655, 103), (655, 124), (640, 128), (630, 140))  # the great arch
    p.box('copper', 650, 116, 655, 123)
    p.box('brick', 630, 142, 655, 182)
    p.box('copper', 626, 184, 655, 199)                          # the porch
    p.box('stone', 638, 196, 655, 211)
    p.box('stone', 624, 188, 640, 250)                           # the round pier beside it
    p.box('stone', 641, 212, 655, 246)
    p.box('dark', 646, 223, 655, 239)
    return p


def station():
    tpl = template('tokyo-station_0_0')  # 1312 x 256
    plan = station_plan()

    def name_at(x, y):
        return plan(SW - 1 - x if x >= SW // 2 else x, y)

    def zone(x, y, accent):
        name = name_at(x, y)
        turn = {'<': 0, '>': 2}.get(name[-1], 1)
        return FACES[name.rstrip('<>')][2 - turn if x >= SW // 2 else turn]

    def lit(x, y):
        """About one window in ten, and none on a face that is turned away: its panes are slivers."""
        return name_at(x, y)[-1] not in '<>' and (x * 7 + y * 13) % 10 == 0

    walls = {m for name in ('brick', 'stone') for m in FACES[name]}
    return paint(tpl, zone, pane=6, walls=walls, bar=2, lit=lit)


# ------------------------------------------------------------------------------
def build():
    """{key: the doubled picture}. The feet are cut from the tower."""
    double = lambda im: im.resize((im.width * 2, im.height * 2), Image.NEAREST)   # noqa: E731
    big = double(tower())
    return {'tokyo-tower_0_0': big,
            'tokyo-tower-feet': big.crop((0, big.height - 6 * C, big.width, big.height)),
            'tokyo-station_0_0': double(station())}


def sheet(built, out):
    """The pictures on one paving-coloured sheet (a preview, not part of the game)."""
    keys = ('tokyo-station_0_0', 'tokyo-tower_0_0', 'tokyo-tower-feet')
    im = Image.new('RGBA', (built[keys[0]].width + 48, sum(built[k].height for k in keys) + 24 * 4), rgb('9aa6b4'))
    y = 24
    for k in keys:
        im.alpha_composite(built[k], (24, y)); y += built[k].height + 24
    im.save(out)
    print('sheet ->', out)


def main():
    built = build()
    for key, im in built.items():
        im.save(f'{SPR}/{key}.png')
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    if '--sheet' in sys.argv:
        sheet(built, sys.argv[sys.argv.index('--sheet') + 1])


if __name__ == '__main__':
    main()
