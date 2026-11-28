#!/usr/bin/env python3
"""generate_devhouse_art.py — the two Devhouses and what stands in them (issue #69).

The trips' own houses: a slim six-storey block in Minato (Tokyo) and a narrow
four-storey townhouse on Dotonbori (Osaka). tools/generate_devhouses.py builds
a room per floor from the real floor plans, out of the home kit
(tools/generate_house_art.py) and this one: what a home had not needed so far.

Drawn the way the home kit is - shaded pixel art in the GuttyKreum palette, at
half size (32px a cell) and pixel-doubled, a 1px ink outline on everything that
stands - but with rectangles, points and whole-number arithmetic only (no
Pillow ellipse, polygon or slanted line: those move by a pixel from one Pillow
to the next, and tools/check_generators.py compares bytes).

The two buildings seen from the street are in the house look (#319): GuttyKreum
sheet colours only (the S_* block), a navy outline, the pack's dark glass with
its slanted glare in place of lit windows, ragged foliage and the pack's roof
tile (from generate_sendai_art.py). The rest is still in the older look (#325).

  outside (one sprite each; prefabs in tools/make_prefabs.py)
    devhouse-tokyo_0_0    5x8   a flat roof seen from above (tank, condenser, aerial,
                                the lift's motor room), six window rows, the stair
                                tower up its east side, the entrance under its name
                                at column 3
    devhouse-osaka_0_0    3x7   the roof garden seen from above inside a tiled eave,
                                dark timber and plaster, a noren over the door at
                                column 1 under a tiled pent roof
  floors (1x1, Floor layer)
    devhouse-stairs-up_0_0 / -down_0_0    the step you take to the next floor
    devhouse-tile_0_0             the wet rooms
    devhouse-gravel_0_0           raked gravel (the roof garden)
    devhouse-stepping-stone_0_0   a flat stone in it
  walls
    devhouse-wall-h_0_0   1x1   a partition seen from the front
    devhouse-wall-v_0_0   1x1   one seen from above, running north-south
    devhouse-wall-v-end_0_0     ...and where it stops, its end face
    devhouse-stairwell_0_0  1x1 a flight seen from above (solid: you take the step at its end)
    devhouse-door_0_0     1x2   back-wall piece: a locked door (not ours)
    devhouse-fence_0_0    1x2   back-wall piece: a bamboo fence
  furniture
    devhouse-table-wide_0_0 4x1, -table-tall_0_0 1x3, -table-small_0_0 1x2
    devhouse-chair-n / -s / -e / -w_0_0   named for the side of the table it sits on
    devhouse-stool_0_0, -counter_0_0 2x1, -sofa_0_0 1x3, -armchair_0_0, -side-table_0_0
    devhouse-bunk_0_0 1x2, -basin_0_0, -toilet_0_0, -shower_0_0, -bath_0_0 1x2,
    devhouse-washer_0_0, -clothes-rack_0_0 1x2
  the roof garden
    devhouse-rock_0_0, -shrub_0_0, -lantern_0_0 (lit at night: src/utils/Glows.js),
    devhouse-garden-seat_0_0, -water-bowl_0_0 (goldfish in it)

What a bump on each says is in src/utils/Interactions.js. No rubbish bin in it.

Deterministic and idempotent (no source image, no font): rewrites the PNGs in
assets/sprites/ and registers them in config.json spriteMetadata + tileNames.
Needs Pillow. Run from gamev2/ BEFORE make_prefabs.py and generate_devhouses.py:
    python3 tools/generate_devhouse_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image, ImageDraw, ImageOps

from generate_hokkaido import (rgb, canvas, outline, INK, NAVY, RED, RED_HI, RED_LO, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO,
                               STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_house_art import (WOOD_HI, BEAM, BEAM_HI, BEAM_LO, PAPER, PAPER_LO, PAPER_DK, PLASTER, INDIGO,
                                INDIGO_HI, INDIGO_LO, ROSE, ROSE_HI, ROSE_LO, SKY, SKY_HI, SKY_LO, STEEL,
                                STEEL_HI, STEEL_LO, IRON, IRON_HI, LIT, LIT_HI, ORANGE, box, speckle,
                                wall_frame, plaster)
from generate_sendai_art import pane as glass, foliage, roof_tile, speck, LEAF

GRAIN = rgb('c99a80')
TILE, TILE_HI, TILE_LO = rgb('dfe9ee'), rgb('f1f7f9'), rgb('b7c8d2')
GRAVEL, GRAVEL_HI, GRAVEL_LO, GRAVEL_DK = rgb('d9d5c7'), rgb('e9e6da'), rgb('c4bfb0'), rgb('a9a495')
BAMBOO, BAMBOO_HI, BAMBOO_LO, BAMBOO_DK = rgb('c2b872'), rgb('ddd596'), rgb('969050'), rgb('6d6a3c')
MOSS = rgb('6f8f5a')
WATER, WATER_HI, WATER_LO = rgb('5c80b4'), rgb('8fb4dc'), rgb('3f5f92')
CONCRETE, CONCRETE_HI, CONCRETE_LO = rgb('d9d6cf'), rgb('efede8'), rgb('b3afa8')
CHAR, CHAR_HI, CHAR_LO = rgb('3a3940'), rgb('56555f'), rgb('26252b')


# ---- drawing in whole numbers --------------------------------------------------------
def R(d, x0, y0, x1, y1, fill):
    d.rectangle([x0, y0, x1, y1], fill=fill)


def H(d, x0, x1, y, fill):
    d.rectangle([x0, y, x1, y], fill=fill)


def V(d, x, y0, y1, fill):
    d.rectangle([x, y0, x, y1], fill=fill)


def P(d, fill, *points):
    for x, y in points:
        d.rectangle([x, y, x, y], fill=fill)


def oval(d, x0, y0, x1, y1, fill):
    """A filled ellipse inside the box, a pixel at a time and in integers."""
    a2, b2 = (x1 - x0 + 1) ** 2, (y1 - y0 + 1) ** 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (2 * x - x0 - x1) ** 2 * b2 + (2 * y - y0 - y1) ** 2 * a2 <= a2 * b2:
                d.rectangle([x, y, x, y], fill=fill)


def soft(d, x0, y0, x1, y1, fill, r=1):
    """A rectangle with its corners taken off by `r` pixels."""
    for i in range(r):
        H(d, x0 + r - i, x1 - r + i, y0 + i, fill)
        H(d, x0 + r - i, x1 - r + i, y1 - i, fill)
    R(d, x0, y0 + r, x1, y1 - r, fill)


def slant(d, x0, y0, x1, y1, fill):
    """A one-pixel line between two points (Bresenham)."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        d.rectangle([x0, y0, x0, y0], fill=fill)
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


GLYPHS = {'D': ('110', '101', '101', '101', '110'), 'E': ('111', '100', '110', '100', '111'),
          'V': ('101', '101', '101', '101', '010'), 'H': ('101', '101', '111', '101', '101'),
          'O': ('111', '101', '101', '101', '111'), 'U': ('101', '101', '101', '101', '111'),
          'S': ('111', '100', '111', '001', '111')}


def letters(d, x, y, word, fill):
    """`word` in a 3x5 face, a pixel between letters: the name over each door."""
    for ch in word:
        for dy, row in enumerate(GLYPHS[ch]):
            for dx, on in enumerate(row):
                if on == '1':
                    P(d, fill, (x + dx, y + dy))
        x += 4


# ---- floors ----------------------------------------------------------------------------
def wet_tile():
    im, d = canvas(1, 1)
    R(d, 0, 0, 31, 31, TILE)
    for k in range(0, 32, 8):
        H(d, 0, 31, k, TILE_HI); V(d, k, 0, 31, TILE_HI)
    for k in range(7, 32, 8):
        H(d, 0, 31, k, TILE_LO); V(d, k, 0, 31, TILE_LO)
    return im


def rake(d):
    """Raked gravel over the whole cell: the furrows run east-west and join cell to cell."""
    R(d, 0, 0, 31, 31, GRAVEL)
    for y in range(0, 32, 4):
        H(d, 0, 31, y, GRAVEL_HI)
        H(d, 0, 31, y + 2, GRAVEL_LO)
    speckle(d, 0, 0, 31, 31, GRAVEL_DK, 2, every=5)
    speckle(d, 0, 0, 31, 31, WHITE, 9, every=11)


def gravel():
    im, d = canvas(1, 1)
    rake(d)
    return im


def stepping_stone():
    im, d = canvas(1, 1)
    rake(d)
    oval(d, 4, 8, 27, 26, GRAVEL_DK)                       # the hollow it sits in
    oval(d, 5, 7, 26, 23, STONE_LO)
    oval(d, 5, 6, 26, 21, STONE)
    oval(d, 8, 8, 19, 13, rgb('cdd6da'))
    P(d, STONE_LO, (21, 12), (12, 17), (17, 18), (9, 14))
    P(d, MOSS, (6, 15), (7, 16), (24, 17))
    return im


def stairs(up):
    def draw():
        im, d = canvas(1, 1)
        tread, lip, riser = (WOOD_HI, rgb('e6bfa3'), WOOD_LO) if up else (WOOD, GRAIN, WOOD_DK)
        for y in range(0, 32, 8):                          # four treads
            R(d, 0, y, 31, y + 5, tread)
            H(d, 0, 31, y, lip)
            R(d, 0, y + 6, 31, y + 7, riser)
        for x in (0, 29):                                  # the strings either side
            R(d, x, 0, x + 2, 31, BEAM)
        V(d, 2, 0, 31, BEAM_LO); V(d, 29, 0, 31, BEAM_LO)
        V(d, 0, 0, 31, BEAM_HI)
        for i in range(6):                                 # which way it goes, painted on the treads
            y = 11 + i if up else 20 - i
            for x in (15 - i, 16 + i):
                R(d, x, y, x, y + 2, PAPER if up else LIT_HI)
                P(d, BEAM_LO, (x, y + 3 if up else y - 1))
        return im
    return draw


def stairwell():
    im, d = canvas(1, 1)
    for y in range(0, 32, 8):
        R(d, 0, y, 31, y + 5, GRAIN)
        H(d, 0, 31, y, WOOD_HI)
        R(d, 0, y + 6, 31, y + 7, WOOD_DK)
    for x in (0, 28):                                      # a handrail each side
        R(d, x, 0, x + 3, 31, BEAM)
        V(d, x, 0, 31, BEAM_HI); V(d, x + 3, 0, 31, BEAM_LO)
    return im


# ---- walls -----------------------------------------------------------------------------
def wall_h():
    im, d = canvas(1, 1)
    base, mid, lo = PLASTER['sand']
    R(d, 0, 0, 31, 8, BEAM)                                # its top, seen from above
    H(d, 0, 31, 0, BEAM_LO); H(d, 0, 31, 1, BEAM_HI); H(d, 0, 31, 8, BEAM_LO)
    R(d, 0, 9, 31, 27, base)
    speckle(d, 0, 10, 31, 27, mid, 1, every=5)
    H(d, 0, 31, 9, lo)
    R(d, 0, 28, 31, 31, BEAM)                              # the skirting board
    H(d, 0, 31, 28, BEAM_HI); H(d, 0, 31, 31, BEAM_LO)
    return im


def wall_v(end):
    def draw():
        im, d = canvas(1, 1)
        base, mid, lo = PLASTER['sand']
        y1 = 12 if end else 31
        R(d, 10, 0, 21, y1, BEAM)
        V(d, 10, 0, y1, BEAM_HI); V(d, 21, 0, y1, BEAM_LO)
        H(d, 10, 21, 0, BEAM_LO)                           # a joint a cell: it is built of panels
        if end:
            H(d, 10, 21, 12, BEAM_LO)
            R(d, 10, 13, 21, 26, base)
            speckle(d, 10, 14, 21, 26, mid, 1, every=5)
            H(d, 10, 21, 13, lo)
            R(d, 10, 27, 21, 30, BEAM)
            H(d, 10, 21, 27, BEAM_HI); H(d, 10, 21, 30, BEAM_LO)
        outline(im)
        return im
    return draw


def locked_door():
    im = plaster('sand')()
    d = ImageDraw.Draw(im)
    R(d, 5, 19, 26, 57, BEAM_LO)                           # the frame
    R(d, 7, 21, 24, 57, STEEL)
    V(d, 7, 21, 57, STEEL_HI); H(d, 7, 24, 21, STEEL_HI)
    V(d, 24, 22, 57, STEEL_LO)
    for y0 in (33, 45):                                    # two pressed panels
        R(d, 10, y0, 21, y0 + 9, rgb('aab6c2'))
        H(d, 10, 21, y0, STEEL_LO); V(d, 10, y0, y0 + 9, STEEL_LO)
        H(d, 10, 21, y0 + 9, STEEL_HI)
    R(d, 10, 24, 21, 29, WHITE)                            # the notice: no way through
    H(d, 12, 19, 26, RED); H(d, 12, 17, 28, STEEL_LO)
    R(d, 20, 38, 22, 43, IRON)                             # the lock and its lever
    P(d, RED, (21, 39))
    H(d, 17, 21, 42, IRON_HI)
    H(d, 7, 24, 57, STEEL_LO)
    return im


def fence():
    im, d = canvas(1, 2)
    R(d, 0, 0, 31, 63, BAMBOO)
    for x in range(0, 32, 4):                              # canes, four pixels each
        V(d, x, 0, 63, BAMBOO_HI)
        V(d, x + 2, 0, 63, BAMBOO_LO)
        V(d, x + 3, 0, 63, BAMBOO_DK)
        for y in range(9 + (x * 5) % 13, 60, 17):          # their joints
            H(d, x, x + 2, y, BAMBOO_LO)
    for y in (12, 34, 52):                                 # split canes tied across them
        R(d, 0, y, 31, y + 2, BAMBOO_HI)
        H(d, 0, 31, y + 2, BAMBOO_LO); H(d, 0, 31, y + 3, BAMBOO_DK)
        for x in range(5, 32, 12):                         # the black cord
            R(d, x, y - 1, x + 1, y + 3, CHAR_LO)
    R(d, 0, 0, 31, 3, BEAM)                                # the capping pole
    H(d, 0, 31, 0, BEAM_HI); H(d, 0, 31, 3, BEAM_LO)
    R(d, 0, 59, 31, 63, STONE_LO)                          # and the kerb it stands on
    H(d, 0, 31, 59, STONE); H(d, 0, 31, 63, STONE_DK)
    return im


# ---- tables and what sits round them -----------------------------------------------------
def laptop(d, x, y, turned=False):
    """A laptop left open, 8x6: it is that kind of house."""
    if turned:                                             # its back to you
        R(d, x, y, x + 7, y + 4, IRON); H(d, x, x + 7, y, IRON_HI)
        P(d, WHITE, (x + 3, y + 2), (x + 4, y + 2))
        H(d, x, x + 7, y + 5, STEEL_LO)
    else:
        R(d, x, y, x + 7, y + 3, IRON)
        R(d, x + 1, y + 1, x + 6, y + 3, SKY_HI)
        H(d, x + 2, x + 4, y + 2, WHITE)
        R(d, x, y + 4, x + 7, y + 5, STEEL); H(d, x + 1, x + 6, y + 4, STEEL_LO)


def mug(d, x, y, drink=rgb('7a9a55')):
    R(d, x, y, x + 3, y + 3, PAPER); H(d, x + 1, x + 2, y, drink); P(d, PAPER_DK, (x + 4, y + 1), (x + 4, y + 2))
    H(d, x, x + 3, y + 3, PAPER_DK)


def table(cw, ch, things):
    def draw():
        im, d = canvas(cw, ch)
        x1, y1 = cw * 32 - 3, ch * 32 - 3
        soft(d, 2, 2, x1, y1 - 3, WOOD_HI, 2)              # the top
        H(d, 4, x1 - 2, 2, rgb('e6bfa3'))
        R(d, 2, y1 - 8, x1, y1 - 4, WOOD)                  # its near edge
        H(d, 2, x1, y1 - 8, WOOD_LO); H(d, 3, x1 - 1, y1 - 4, WOOD_LO)
        for x in (4, x1 - 5):                              # the legs
            R(d, x, y1 - 3, x + 2, y1, WOOD_DK)
        if cw > ch:                                        # the grain runs the long way
            for x in range(18, x1 - 8, 22):
                H(d, x, x + 9, 6 + (x * 7) % 9, GRAIN)
        else:
            for y in range(10, y1 - 16, 14):
                V(d, 8 + (y * 5) % 15, y, y + 7, GRAIN)
        things(d)
        outline(im)
        return im
    return draw


def wide_things(d):
    laptop(d, 12, 6); laptop(d, 84, 5); laptop(d, 50, 13, turned=True)
    mug(d, 26, 10); mug(d, 70, 6, rgb('6a4a3a')); mug(d, 104, 12)
    R(d, 36, 5, 44, 10, PAPER); H(d, 37, 42, 7, STEEL_LO); H(d, 37, 40, 9, STEEL_LO)       # notes
    oval(d, 110, 4, 119, 10, RED_LO); oval(d, 111, 4, 118, 8, ORANGE)                      # a bowl of mikan
    P(d, AMBER, (113, 5), (116, 6))


def tall_things(d):
    laptop(d, 5, 10); laptop(d, 18, 34, turned=True); laptop(d, 6, 58)
    mug(d, 20, 14); mug(d, 8, 40, rgb('6a4a3a')); mug(d, 19, 66)
    oval(d, 12, 24, 21, 30, RED_LO); oval(d, 13, 24, 20, 28, ORANGE)
    P(d, AMBER, (15, 25), (18, 26))
    R(d, 14, 74, 22, 79, PAPER); H(d, 15, 20, 76, STEEL_LO)


def small_things(d):
    laptop(d, 5, 8); mug(d, 20, 12)
    R(d, 15, 28, 23, 33, PAPER); H(d, 16, 21, 30, STEEL_LO)
    mug(d, 7, 38, rgb('6a4a3a'))


def chair(side):
    """A dining chair that faces the table: `side` is the side of the table it sits on."""
    def draw():
        im, d = canvas(1, 1)
        if side == 'n':                                    # facing you: the back behind the seat
            R(d, 8, 3, 23, 14, WOOD)
            H(d, 8, 23, 3, WOOD_HI)
            for x in (11, 15, 16, 20):
                V(d, x, 6, 13, WOOD_DK)
            R(d, 7, 15, 24, 23, INDIGO); H(d, 8, 23, 15, INDIGO_HI)
            R(d, 7, 24, 24, 25, WOOD_LO)
            for x in (8, 22):
                R(d, x, 26, x + 1, 29, WOOD_DK)
        elif side == 's':                                  # its back to you
            R(d, 7, 6, 24, 11, INDIGO); H(d, 8, 23, 6, INDIGO_HI)
            R(d, 8, 10, 23, 24, WOOD)
            H(d, 8, 23, 10, WOOD_HI)
            for x in (11, 15, 16, 20):
                V(d, x, 13, 22, WOOD_LO)
            H(d, 8, 23, 24, WOOD_LO)
            for x in (8, 22):
                R(d, x, 25, x + 1, 29, WOOD_DK)
        else:                                              # west of the table, facing east (-e is mirrored)
            R(d, 6, 3, 9, 24, WOOD)
            V(d, 6, 3, 24, WOOD_HI); V(d, 9, 4, 24, WOOD_LO)
            R(d, 10, 13, 25, 21, INDIGO); H(d, 10, 25, 13, INDIGO_HI)
            V(d, 25, 14, 21, INDIGO_LO)
            R(d, 10, 22, 25, 23, WOOD_LO)
            for x in (6, 23):
                R(d, x, 24, x + 1, 29, WOOD_DK)
        outline(im)
        return ImageOps.mirror(im) if side == 'e' else im
    return draw


def stool():
    im, d = canvas(1, 1)
    for x in (9, 21):                                      # legs and a rung
        R(d, x, 17, x + 1, 28, WOOD_DK)
    H(d, 10, 21, 24, WOOD_LO)
    oval(d, 6, 7, 25, 20, WOOD_LO)
    oval(d, 6, 6, 25, 17, RED)
    oval(d, 9, 7, 20, 12, RED_HI)
    outline(im)
    return im


def counter():
    im, d = canvas(2, 1)
    box(d, 1, 4, 62, 29, STEEL_HI, WOOD, WOOD_LO, 11)
    R(d, 1, 4, 62, 14, rgb('d9dfe5')); H(d, 1, 62, 4, WHITE); H(d, 1, 62, 14, STEEL_LO)
    for x0 in (3, 18, 33, 48):                             # the doors under the worktop
        R(d, x0, 17, x0 + 12, 27, GRAIN); H(d, x0, x0 + 12, 27, WOOD_DK)
        H(d, x0, x0 + 12, 17, WOOD_HI); P(d, IRON, (x0 + 10, 22))
    R(d, 6, 6, 15, 11, WOOD_HI); H(d, 6, 15, 11, WOOD_LO)                                   # a chopping board
    P(d, GREEN_HI, (8, 8), (9, 8), (11, 9)); P(d, RED, (13, 7))
    mug(d, 24, 7)
    R(d, 40, 3, 47, 12, IRON); R(d, 41, 4, 46, 7, IRON_HI); R(d, 42, 9, 45, 11, STEEL)      # the coffee machine
    P(d, RED, (46, 9))
    R(d, 52, 6, 58, 12, PAPER); H(d, 53, 57, 5, PAPER_LO); R(d, 54, 8, 56, 9, AMBER)        # the rice cooker
    outline(im)
    return im


def sofa():
    im, d = canvas(1, 3)
    soft(d, 3, 4, 28, 91, INDIGO, 2)                       # seen from above, its back to the west wall
    R(d, 3, 6, 10, 89, INDIGO_LO)                          # the back
    V(d, 4, 7, 88, INDIGO); V(d, 10, 6, 89, INDIGO_LO)
    for y0 in (5, 80):                                     # the arms
        R(d, 5, y0, 27, y0 + 9, INDIGO)
        H(d, 6, 26, y0 + 1, INDIGO_HI); H(d, 5, 27, y0 + 9, INDIGO_LO)
    for y0 in (15, 37, 59):                                # three seats
        R(d, 11, y0, 27, y0 + 20, INDIGO_HI)
        R(d, 12, y0 + 1, 26, y0 + 19, rgb('5670ab'))
        H(d, 12, 26, y0 + 19, INDIGO); V(d, 27, y0, y0 + 20, INDIGO)
    R(d, 14, 19, 21, 26, ROSE); H(d, 14, 21, 19, ROSE_HI); H(d, 14, 21, 26, ROSE_LO)        # a cushion
    R(d, 3, 90, 28, 93, INDIGO_LO)                         # its foot, in shadow
    outline(im)
    return im


def armchair():
    im, d = canvas(1, 1)
    soft(d, 5, 3, 26, 16, RED, 2)                          # the back
    H(d, 8, 23, 4, RED_HI)
    R(d, 9, 14, 22, 23, RED_HI)                            # the seat
    H(d, 9, 22, 23, RED)
    R(d, 9, 24, 22, 27, RED_LO)
    for x0 in (3, 23):                                     # the arms
        soft(d, x0, 11, x0 + 5, 27, RED, 1)
        H(d, x0 + 1, x0 + 4, 12, RED_HI)
        H(d, x0 + 1, x0 + 4, 27, RED_LO)
    for x in (5, 25):
        R(d, x, 28, x + 1, 29, WOOD_DK)
    outline(im)
    return im


def side_table():
    im, d = canvas(1, 1)
    R(d, 14, 19, 17, 27, WOOD_DK)                          # one leg, a round foot
    H(d, 10, 21, 28, WOOD_DK)
    oval(d, 5, 9, 26, 22, WOOD_LO)
    oval(d, 5, 8, 26, 19, WOOD_HI)
    H(d, 10, 21, 9, rgb('e6bfa3'))
    mug(d, 9, 12)
    R(d, 17, 11, 23, 15, INDIGO); H(d, 17, 23, 11, INDIGO_HI); V(d, 17, 11, 15, PAPER)      # a paperback
    outline(im)
    return im


# ---- beds and the wet rooms ----------------------------------------------------------------
def bunk():
    im, d = canvas(1, 2)
    R(d, 2, 2, 29, 61, WOOD)                               # the frame
    R(d, 2, 2, 29, 4, WOOD_HI)
    R(d, 4, 6, 27, 40, WHITE)                              # the top bunk
    soft(d, 7, 8, 24, 15, PAPER, 1); H(d, 9, 22, 15, PAPER_DK)
    R(d, 4, 19, 27, 40, INDIGO); R(d, 4, 19, 27, 21, PAPER_LO); H(d, 4, 27, 22, INDIGO_LO)
    for y in range(26, 40, 5):
        H(d, 4, 27, y, INDIGO_HI)
    R(d, 2, 41, 29, 43, WOOD_HI); H(d, 2, 29, 43, WOOD_LO)   # its rail
    R(d, 4, 44, 27, 57, BEAM_LO)                           # the one underneath, in its shadow
    R(d, 4, 50, 27, 57, ROSE_LO); H(d, 4, 27, 50, ROSE)
    R(d, 4, 47, 12, 49, PAPER_DK)
    R(d, 2, 58, 29, 61, WOOD_LO); H(d, 2, 29, 58, WOOD)
    for x in (2, 28):                                      # the posts
        R(d, x, 2, x + 1, 61, WOOD_LO)
    for x in (19, 24):                                     # the ladder
        V(d, x, 41, 61, WOOD_HI)
    for y in (46, 51, 56):
        H(d, 19, 24, y, WOOD_HI)
    outline(im)
    return im


def basin():
    im, d = canvas(1, 1)
    box(d, 3, 5, 28, 29, WHITE, rgb('e4ebf2'), STEEL, 13)
    oval(d, 7, 8, 24, 16, STEEL)                           # the bowl
    oval(d, 8, 9, 23, 16, WHITE)
    oval(d, 10, 11, 21, 15, SKY_HI)
    P(d, IRON, (15, 13))
    R(d, 15, 3, 16, 9, STEEL_LO); H(d, 14, 17, 3, STEEL_LO)        # the tap
    P(d, STEEL_HI, (15, 4))
    V(d, 15, 19, 28, STEEL); V(d, 16, 19, 28, WHITE)       # the cupboard under it
    P(d, IRON, (13, 23), (18, 23))
    R(d, 22, 6, 25, 8, ROSE)                               # the soap
    outline(im)
    return im


def toilet():
    im, d = canvas(1, 1)
    box(d, 8, 2, 23, 11, WHITE, rgb('e4ebf2'), STEEL, 3)   # the cistern
    R(d, 14, 3, 17, 3, STEEL_LO)
    oval(d, 7, 9, 24, 28, STEEL)                           # the bowl, its lid down
    oval(d, 7, 8, 24, 26, WHITE)
    oval(d, 10, 11, 21, 23, rgb('e4ebf2'))
    H(d, 12, 19, 12, WHITE)
    R(d, 13, 27, 18, 29, STEEL)
    P(d, SKY, (25, 14)); P(d, STEEL_LO, (26, 14), (26, 15))        # the washlet's panel
    outline(im)
    return im


def shower():
    im, d = canvas(1, 1)
    R(d, 2, 6, 29, 29, STEEL)                              # the tray
    R(d, 3, 7, 28, 27, TILE_HI)
    for k in range(9, 28, 6):
        H(d, 3, 28, k, TILE); V(d, k - 2, 7, 27, TILE)
    R(d, 14, 17, 17, 19, STEEL_LO); P(d, IRON, (15, 18), (16, 18))  # the drain
    R(d, 2, 28, 29, 29, STEEL_LO)
    V(d, 22, 1, 12, STEEL_LO); V(d, 23, 1, 12, STEEL_HI)   # the riser, the head, the mixer
    R(d, 15, 1, 23, 2, STEEL_LO); R(d, 13, 3, 18, 4, STEEL_LO); H(d, 13, 18, 3, STEEL_HI)
    R(d, 21, 11, 24, 13, IRON_HI); P(d, RED, (21, 12)); P(d, SKY, (24, 12))
    P(d, SKY, (14, 7), (17, 8), (15, 11), (13, 13), (18, 14), (16, 22), (12, 24))
    P(d, SKY_HI, (16, 6), (13, 9), (17, 12))
    outline(im)
    return im


def bath():
    im, d = canvas(1, 2)
    soft(d, 2, 3, 29, 60, WHITE, 3)                        # a deep tub, seen from above
    soft(d, 2, 52, 29, 60, STEEL, 3); R(d, 2, 52, 29, 54, rgb('e4ebf2'))
    soft(d, 5, 8, 26, 50, STEEL_LO, 3)
    soft(d, 6, 9, 25, 49, SKY_HI, 3)
    for x, y, w in ((9, 15, 6), (15, 24, 7), (8, 33, 5), (16, 41, 6), (10, 45, 4)):         # the water moves
        H(d, x, x + w, y, WHITE)
    for x, y in ((11, 20), (19, 31), (12, 38)):
        H(d, x, x + 3, y, SKY)
    R(d, 14, 3, 17, 9, STEEL_LO); H(d, 13, 18, 4, STEEL_LO); P(d, STEEL_HI, (15, 5))        # the tap
    P(d, RED, (12, 5)); P(d, SKY, (19, 5))
    P(d, WHITE, (22, 6), (24, 3), (9, 5), (7, 2))          # steam
    R(d, 21, 44, 24, 47, AMBER); P(d, ORANGE, (22, 44)); P(d, INK, (23, 46))                # a rubber duck
    outline(im)
    return im


def washer():
    im, d = canvas(1, 1)
    box(d, 4, 3, 27, 29, WHITE, rgb('e4ebf2'), STEEL, 5)
    R(d, 6, 9, 25, 12, STEEL); P(d, AMBER, (8, 10)); P(d, SKY, (10, 10)); R(d, 19, 10, 23, 11, IRON)
    P(d, GREEN_HI, (20, 10))
    oval(d, 8, 13, 23, 27, STEEL_LO)                       # the door, and a wash going round
    oval(d, 10, 15, 21, 25, GLASS_DK)
    oval(d, 11, 18, 20, 25, SKY_LO)
    P(d, WHITE, (12, 17), (13, 16)); P(d, ROSE, (14, 21), (15, 22), (17, 20)); P(d, WHITE, (13, 23), (18, 23))
    outline(im)
    return im


def clothes_rack():
    im, d = canvas(1, 2)
    for x in (4, 26):                                      # the stand: two posts on feet
        R(d, x, 5, x + 1, 59, STEEL_LO); V(d, x, 5, 59, STEEL_HI)
        R(d, x - 2, 59, x + 3, 60, STEEL_LO)
    R(d, 3, 5, 28, 6, STEEL_LO); H(d, 3, 28, 5, STEEL_HI)  # the top rail, and the washing on it
    R(d, 4, 34, 27, 35, STEEL_LO)                          # the low one
    R(d, 7, 7, 15, 22, WHITE); R(d, 5, 8, 6, 13, WHITE); R(d, 16, 8, 17, 13, WHITE)          # a shirt
    V(d, 11, 9, 21, STEEL_HI); H(d, 7, 15, 22, STEEL)
    R(d, 19, 7, 25, 28, INDIGO); V(d, 22, 12, 28, INDIGO_LO); H(d, 19, 25, 7, INDIGO_HI)     # jeans
    R(d, 6, 36, 13, 50, ROSE); H(d, 6, 13, 36, ROSE_HI); H(d, 6, 13, 44, ROSE_LO)            # a towel
    for x, c in ((16, RED), (19, GREEN_HI), (22, AMBER)):                                    # socks
        R(d, x, 36, x + 1, 42, c); P(d, c, (x + 2, 42))
    outline(im)
    return im


# ---- the roof garden ---------------------------------------------------------------------------
def rock():
    im, d = canvas(1, 1)
    oval(d, 3, 11, 28, 29, STONE_DK)
    oval(d, 3, 9, 28, 27, STONE_LO)
    oval(d, 5, 6, 23, 23, STONE)
    oval(d, 8, 7, 17, 13, rgb('d6dee2'))
    slant(d, 19, 9, 22, 20, STONE_LO); slant(d, 12, 16, 9, 24, STONE_LO)
    for x, y in ((6, 13), (7, 12), (8, 11), (6, 15), (9, 10), (24, 22), (25, 21), (23, 24)):
        P(d, MOSS, (x, y))
    P(d, GREEN_HI, (7, 13), (24, 23))
    outline(im)
    return im


def shrub():
    im, d = canvas(1, 1)
    oval(d, 2, 6, 29, 29, GREEN_LO)                        # clipped round, the way a garden's are
    oval(d, 2, 4, 29, 26, GREEN)
    oval(d, 6, 5, 22, 16, rgb('5f8062'))
    for x, y in ((9, 8), (14, 6), (19, 9), (7, 13), (13, 12), (22, 14), (17, 16), (10, 18), (25, 19), (5, 20)):
        P(d, GREEN_HI, (x, y), (x + 1, y), (x, y + 1))
    for x, y in ((12, 9), (21, 12), (8, 16), (16, 20), (24, 22), (11, 23)):                  # azalea, in flower
        P(d, ROSE_HI, (x, y), (x + 1, y)); P(d, ROSE, (x, y + 1))
    outline(im)
    return im


def lantern():
    im, d = canvas(1, 1)
    R(d, 15, 0, 16, 2, STONE_LO)                           # the jewel on top
    R(d, 12, 3, 19, 4, STONE)                              # the roof, spreading
    R(d, 9, 5, 22, 6, STONE); R(d, 6, 7, 25, 9, STONE_LO)
    H(d, 12, 19, 3, rgb('d6dee2')); H(d, 6, 25, 9, STONE_DK)
    P(d, MOSS, (10, 5), (11, 5), (8, 7), (21, 6))
    R(d, 10, 10, 21, 18, STONE)                            # the fire box, its window lit
    R(d, 13, 12, 18, 17, LIT); R(d, 14, 13, 17, 15, LIT_HI)
    V(d, 21, 10, 18, STONE_LO)
    R(d, 8, 19, 23, 20, STONE_LO); H(d, 8, 23, 19, STONE)  # the shelf it sits on
    R(d, 13, 21, 18, 26, STONE); V(d, 18, 21, 26, STONE_LO)  # the post
    R(d, 9, 27, 22, 29, STONE_LO); H(d, 9, 22, 27, STONE)  # the foot
    P(d, MOSS, (9, 28), (10, 28), (21, 29))
    outline(im)
    return im


def garden_seat():
    im, d = canvas(1, 1)
    for x in (6, 23):                                      # a bench of weathered boards
        R(d, x, 20, x + 2, 28, WOOD_DK)
    H(d, 9, 22, 25, WOOD_DK)
    R(d, 4, 9, 27, 18, WOOD_HI)
    for y in (12, 15):
        H(d, 4, 27, y, WOOD)
    H(d, 5, 26, 9, rgb('e6bfa3'))
    R(d, 4, 19, 27, 21, WOOD_LO)
    outline(im)
    return im


def water_bowl():
    im, d = canvas(1, 1)
    oval(d, 3, 9, 28, 29, STONE_DK)                        # a stone basin, hollowed by hand
    oval(d, 3, 7, 28, 26, STONE_LO)
    oval(d, 4, 6, 27, 23, STONE)
    oval(d, 7, 8, 24, 20, WATER_LO)
    oval(d, 8, 9, 23, 20, WATER)
    H(d, 11, 15, 11, WATER_HI); H(d, 17, 20, 17, WATER_HI)
    for x, y, c in ((11, 14, ORANGE), (18, 13, RED)):      # two goldfish
        R(d, x, y, x + 3, y + 1, c); P(d, c, (x + 4, y - 1), (x + 4, y + 2)); P(d, INK, (x, y))
        P(d, WHITE if c == RED else AMBER, (x + 2, y))
    R(d, 19, 17, 21, 18, GREEN_HI); P(d, GREEN, (20, 17))  # a lily pad
    P(d, MOSS, (5, 16), (6, 18), (25, 19), (5, 13))
    outline(im)
    return im


# ---- the two houses, from the street ---------------------------------------------------------
# the pack's colours, for the two houses seen from the street
S_WALL, S_WALL_HI, S_WALL_LO, S_WALL_DK = rgb('dae2e4'), rgb('fafcfd'), rgb('bcc7cc'), rgb('a4b0b5')
S_TOWER, S_TOWER_HI, S_TOWER_LO, S_TOWER_DK = rgb('a4b0b5'), rgb('bcc7cc'), rgb('919ea4'), rgb('848295')
S_FRAME, S_FRAME_HI, S_FRAME_LO = rgb('47485d'), rgb('5f6177'), rgb('2a2636')
S_METAL, S_METAL_HI, S_METAL_LO = rgb('94a2a8'), rgb('d1e2eb'), rgb('646e86')
S_SLATE, S_SLATE_HI, S_SLATE_JOINT, S_SLATE_LO = rgb('5b6c79'), rgb('698592'), rgb('444f5e'), rgb('293038')
S_DARK, S_GLARE = rgb('2c2d51'), rgb('4b6396')
S_SHOJI, S_SHOJI_HI, S_SHOJI_LO = rgb('e4cecc'), rgb('fafcfd'), rgb('d2bab0')
S_TIMBER, S_TIMBER_HI, S_TIMBER_LO, S_TIMBER_DK = rgb('aa775f'), rgb('c18e75'), rgb('7f513b'), rgb('5a3827')
S_TIMBER_INK = rgb('3f210f')
S_POT, S_POT_HI, S_POT_LO = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
S_PINK, S_PINK_HI, S_PINK_LO = rgb('bb6479'), rgb('d78bc1'), rgb('83374f')
S_CLOTH, S_CLOTH_HI, S_CLOTH_LO = rgb('314b8e'), rgb('4b6396'), rgb('232449')
S_SIGN, S_BOARD_HI = rgb('f3d890'), rgb('ebbca2')
S_WASH, S_WASH_LO = rgb('588cc6'), rgb('425faa')
S_SOOT, S_SOOT_HI, S_SOOT_LO = rgb('3c3a4c'), rgb('47485d'), rgb('2a2636')
S_BAMBOO, S_BAMBOO_HI, S_BAMBOO_LO, S_BAMBOO_DK = rgb('c6aa71'), rgb('e3c587'), rgb('a7843b'), rgb('86624f')
S_REED, S_REED_LO = rgb('be9e8c'), rgb('aa775f')
S_ROCK, S_ROCK_HI, S_ROCK_LO = rgb('848295'), rgb('bcc7cc'), rgb('53596d')
S_RIDGE, S_RIDGE_HI, S_EAVE = rgb('434857'), rgb('53596d'), rgb('191c2a')


def window(d, x0, y0, x1, y1, frame=S_FRAME, step=9):
    """The pack's dark glass with its slanted glare, in a frame."""
    R(d, x0, y0, x1, y1, frame)
    glass(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, step)


def flat_roof(d, x0, y0, x1, y1):
    """A flat roof seen from above: a steel coping lit on its top and left, slate panels inside it."""
    R(d, x0, y0, x1, y1, S_METAL)
    H(d, x0, x1, y0, S_METAL_HI); V(d, x0, y0, y1, S_METAL_HI)
    H(d, x0, x1, y1, S_METAL_LO); V(d, x1, y0 + 1, y1, S_METAL_LO)
    R(d, x0 + 3, y0 + 3, x1 - 3, y1 - 3, NAVY)
    x0, y0, x1, y1 = x0 + 4, y0 + 4, x1 - 4, y1 - 4
    R(d, x0, y0, x1, y1, S_SLATE)
    for n, x in enumerate(range(x0, x1, 9)):               # panels, their joints staggered
        V(d, x, y0, y1, S_SLATE_JOINT)
        H(d, x + 1, min(x + 8, x1), y0, S_SLATE_HI)
        for y in range(y0 + 4 + n % 3 * 5, y1, 13):
            H(d, x + 1, min(x + 8, x1), y, S_SLATE_JOINT)
            if y + 1 < y1:
                H(d, x + 1, min(x + 8, x1), y + 1, S_SLATE_HI)
    R(d, x0, y1 - 1, x1, y1, S_SLATE_LO); R(d, x1 - 1, y0, x1, y1, S_SLATE_LO)


def devhouse_tokyo():
    """160x256: a flat roof seen from above, five storeys of 35 rows and a ground floor of 37."""
    im, d = canvas(5, 8)
    flat_roof(d, 1, 4, 158, 43)
    # on the roof: the water tank, a condenser, an aerial, the lift's motor room over the stair tower
    R(d, 19, 32, 44, 35, S_SLATE_LO)
    R(d, 14, 14, 40, 33, NAVY); R(d, 15, 15, 39, 32, S_METAL)
    R(d, 15, 15, 18, 32, S_METAL_HI); R(d, 34, 15, 39, 32, S_METAL_LO)
    for y in (22, 27):
        H(d, 15, 39, y, S_METAL_LO)
    oval(d, 14, 7, 40, 20, NAVY); oval(d, 15, 8, 39, 19, S_WALL_LO)
    oval(d, 17, 9, 33, 15, S_METAL_HI); R(d, 25, 12, 30, 15, S_METAL); H(d, 25, 30, 12, S_WALL_HI)
    R(d, 52, 34, 71, 35, S_SLATE_LO)
    R(d, 50, 20, 69, 33, NAVY); R(d, 51, 21, 68, 32, S_METAL); H(d, 51, 68, 21, S_METAL_HI)
    R(d, 53, 24, 62, 31, S_METAL_LO); R(d, 55, 26, 60, 29, S_FRAME); P(d, S_METAL_HI, (57, 27))
    R(d, 64, 24, 66, 25, S_DARK); R(d, 64, 28, 66, 29, S_DARK)
    R(d, 82, 25, 90, 26, S_SLATE_LO)
    R(d, 79, 22, 87, 25, S_FRAME); H(d, 79, 87, 22, S_FRAME_HI)
    V(d, 83, 1, 21, S_FRAME); H(d, 79, 87, 3, S_FRAME); H(d, 80, 86, 6, S_FRAME); H(d, 81, 85, 9, S_FRAME)
    R(d, 106, 36, 154, 38, S_SLATE_LO); R(d, 152, 10, 154, 36, S_SLATE_LO)
    R(d, 103, 1, 151, 35, NAVY)
    R(d, 104, 2, 150, 20, S_METAL); H(d, 104, 150, 2, S_METAL_HI); V(d, 104, 2, 20, S_METAL_HI)
    H(d, 104, 150, 20, S_METAL_LO); V(d, 150, 3, 20, S_METAL_LO)
    R(d, 107, 5, 147, 17, NAVY); R(d, 108, 6, 146, 16, S_SLATE_HI)
    for x in range(108, 146, 9):
        V(d, x, 6, 16, S_SLATE)
    R(d, 108, 15, 146, 16, S_SLATE); R(d, 145, 6, 146, 16, S_SLATE)
    R(d, 104, 21, 150, 34, S_TOWER); H(d, 104, 150, 21, S_TOWER_DK); H(d, 104, 150, 22, S_TOWER_LO)
    for y in (27, 33):
        H(d, 104, 150, y, S_TOWER_LO)
    V(d, 104, 23, 34, S_TOWER_HI); V(d, 150, 21, 34, S_TOWER_DK)
    R(d, 110, 24, 125, 31, S_FRAME)
    for y in range(25, 31, 2):
        H(d, 111, 124, y, S_METAL); H(d, 111, 124, y + 1, S_METAL_LO)
    R(d, 132, 23, 143, 34, S_FRAME); R(d, 133, 24, 142, 34, S_METAL); V(d, 133, 24, 34, S_METAL_HI)
    V(d, 142, 24, 34, S_METAL_LO); P(d, S_FRAME, (140, 29), (140, 30))
    # the body: pale tile, and the stair tower in grey tile up the east side
    R(d, 1, 44, 158, 255, S_WALL); R(d, 96, 44, 158, 255, S_TOWER)
    for y in range(49, 256, 6):                            # the courses of tile
        H(d, 2, 95, y, S_WALL_LO); H(d, 98, 157, y, S_TOWER_LO)
    R(d, 1, 44, 95, 45, S_WALL_DK); R(d, 96, 44, 158, 45, S_TOWER_DK)                # the coping's shade
    V(d, 1, 46, 255, S_WALL_HI); V(d, 158, 46, 255, S_TOWER_DK)
    V(d, 96, 46, 255, S_TOWER_DK); V(d, 97, 46, 255, S_TOWER_HI)
    for n in range(6, 0, -1):                              # the top floor first
        y = 44 + (6 - n) * 35
        if n < 6:                                          # the slab between floors
            R(d, 1, y, 95, y + 1, S_WALL_DK); H(d, 1, 95, y, S_WALL_HI)
            R(d, 96, y, 158, y + 1, S_TOWER_DK); H(d, 97, 158, y, S_TOWER_HI)
        if n == 1:
            break
        # the stair tower: one tall landing window a floor, and a small one beside it
        window(d, 132, y + 5, 151, y + 30, step=7)
        V(d, 141, y + 6, y + 29, S_FRAME); V(d, 142, y + 6, y + 29, S_FRAME_HI)
        for gy in (y + 13, y + 22):
            H(d, 133, 150, gy, S_FRAME)
        H(d, 131, 152, y + 31, S_TOWER_HI); H(d, 131, 152, y + 32, S_TOWER_DK)
        window(d, 104, y + 11, 120, y + 21, step=7)
        V(d, 112, y + 12, y + 20, S_FRAME)
        H(d, 103, 121, y + 22, S_TOWER_HI); H(d, 103, 121, y + 23, S_TOWER_DK)
        # the rooms: three windows over a balcony
        for i, x0 in enumerate((6, 35, 64)):
            x1, y0, y1 = x0 + 25, y + 5, y + 20
            R(d, x0, y0, x1, y1, S_FRAME)
            if n == 2:                                     # the floor that is not ours: blinds down
                R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, S_WALL_LO)
                for by in range(y0 + 3, y1, 3):
                    H(d, x0 + 1, x1 - 1, by, S_METAL)
                H(d, x0 + 1, x1 - 1, y0 + 1, S_WALL_DK)
            elif n == 5:                                   # the tatami room: paper screens, one slid open
                R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, S_SHOJI)
                for bx in range(x0 + 5, x1, 5):
                    V(d, bx, y0 + 1, y1 - 1, S_TIMBER)
                H(d, x0 + 1, x1 - 1, y0 + 8, S_TIMBER)
                H(d, x0 + 1, x1 - 1, y0 + 1, S_SHOJI_LO)
                if i == 1:
                    glass(d, x0 + 16, y0 + 1, x1 - 1, y1 - 1, 7)
                    V(d, x0 + 15, y0 + 1, y1 - 1, S_TIMBER_LO)
            else:
                glass(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1)
                V(d, x0 + 12, y0 + 1, y1 - 1, S_FRAME); V(d, x0 + 13, y0 + 1, y1 - 1, S_FRAME_HI)
                if n == 4 and i != 1:                      # curtains half drawn
                    R(d, x0 + 1, y0 + 1, x0 + 5, y1 - 1, S_PINK); V(d, x0 + 3, y0 + 1, y1 - 1, S_PINK_LO)
                    V(d, x0 + 1, y0 + 1, y1 - 1, S_PINK_HI)
                if (n, i) in ((3, 0), (3, 1), (6, 2)):     # a roller blind part down
                    R(d, x0 + 1, y0 + 1, x1 - 1, y0 + 7, S_SHOJI); H(d, x0 + 1, x1 - 1, y0 + 8, S_SHOJI_LO)
                    V(d, x0 + 12, y0 + 1, y0 + 8, S_FRAME); V(d, x0 + 13, y0 + 1, y0 + 8, S_FRAME_HI)
            H(d, x0, x1, y0, S_FRAME_LO)
            if n == 2:
                H(d, x0 - 1, x1 + 1, y1 + 1, S_WALL_HI); H(d, x0 - 1, x1 + 1, y1 + 2, S_WALL_DK)
        if n > 2:                                          # the balcony: a rail of bars, something on it
            R(d, 4, y + 22, 92, y + 23, S_FRAME); H(d, 4, 92, y + 22, S_FRAME_HI)
            for bx in range(5, 92, 4):
                V(d, bx, y + 24, y + 30, S_FRAME)
            R(d, 4, y + 31, 92, y + 32, S_WALL_DK); H(d, 4, 92, y + 31, S_WALL_HI)
            H(d, 5, 93, y + 33, S_WALL_LO)
        if n == 6:                                         # a plant in the sun
            R(d, 11, y + 25, 17, y + 30, S_POT); H(d, 11, 17, y + 25, S_POT_HI); R(d, 16, y + 26, 17, y + 30, S_POT_LO)
            foliage(im, [(14, y + 19, 7, 6), (10, y + 21, 4, 4), (18, y + 22, 4, 3)], LEAF, 3)
        if n == 4:                                         # the washing
            H(d, 40, 68, y + 23, S_METAL_HI)
            R(d, 44, y + 24, 49, y + 30, S_WALL_HI); H(d, 44, 49, y + 30, S_WALL_LO)
            R(d, 52, y + 24, 56, y + 29, S_WASH); H(d, 52, 56, y + 29, S_WASH_LO)
            R(d, 59, y + 24, 63, y + 30, S_POT_HI); H(d, 59, 63, y + 30, S_POT)
        if n == 3:                                         # the air conditioner's box
            R(d, 69, y + 23, 85, y + 31, S_FRAME); R(d, 70, y + 24, 84, y + 30, S_METAL_HI)
            oval(d, 72, y + 25, 78, y + 30, S_METAL_LO); P(d, S_FRAME, (75, y + 27), (75, y + 28))
            H(d, 70, 84, y + 30, S_METAL); R(d, 80, y + 26, 83, y + 27, S_METAL)
    # the ground floor: a shutter that is never up, and the way in under the name
    y = 219
    R(d, 5, y + 3, 69, 253, S_FRAME); H(d, 5, 69, y + 3, S_FRAME_HI)
    R(d, 7, y + 7, 67, 252, S_METAL)
    for sy in range(y + 8, 252, 3):
        H(d, 7, 67, sy, S_METAL_LO); H(d, 7, 67, sy + 1, S_METAL_HI)
    V(d, 67, y + 7, 252, S_METAL_LO)
    R(d, 74, y + 11, 88, y + 25, S_FRAME); R(d, 75, y + 12, 87, y + 24, S_METAL_LO)               # the post boxes
    for py in range(y + 15, y + 24, 3):
        H(d, 75, 87, py, S_FRAME_LO); H(d, 75, 87, py + 1, S_ROCK)
    V(d, 81, y + 12, y + 24, S_FRAME_LO)
    R(d, 96, y + 2, 131, y + 10, S_FRAME_LO); H(d, 96, 131, y + 2, S_FRAME); H(d, 96, 131, y + 10, INK)   # the name board
    letters(d, 98, y + 4, 'DEVHOUSE', S_SIGN)
    R(d, 99, y + 11, 128, 255, S_FRAME)                      # the door: two leaves of dark glass
    glass(d, 101, y + 13, 113, 251, 7); glass(d, 115, y + 13, 126, 251, 7)
    R(d, 101, 247, 113, 251, S_FRAME_HI); R(d, 115, 247, 126, 251, S_FRAME_HI)
    R(d, 111, y + 20, 112, y + 27, S_METAL_HI); R(d, 116, y + 20, 117, y + 27, S_METAL_HI)
    R(d, 132, y + 9, 139, y + 21, S_FRAME); R(d, 133, y + 10, 138, y + 13, S_DARK)                # the intercom
    P(d, S_GLARE, (133, y + 13), (134, y + 12), (135, y + 11), (136, y + 10))
    for py in (y + 15, y + 17, y + 19):
        P(d, S_METAL_HI, (134, py), (136, py), (138, py))
    P(d, S_POT_HI, (138, y + 10))
    R(d, 1, 252, 158, 253, S_ROCK); R(d, 1, 254, 158, 255, S_ROCK_LO)                            # the kerb
    H(d, 1, 158, 252, S_WALL_DK)
    R(d, 99, 252, 128, 255, S_WALL_DK); H(d, 99, 128, 252, S_WALL_LO)
    R(d, 144, 242, 153, 251, S_POT); H(d, 144, 153, 242, S_POT_HI); R(d, 151, 243, 153, 251, S_POT_LO)   # a pot by the door
    foliage(im, [(150, 234, 7, 8), (146, 238, 4, 4), (154, 239, 4, 5), (150, 228, 5, 4)], LEAF, 5)
    outline(im, NAVY)
    return im


def kawara(im, d, x0, y0, x1, y1):
    """A band of the pack's roof tile: a ridge course, the tiles, a dark eave."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = roof_tile(x, y - y0)
    R(d, x0, y0, x1, y0 + 2, S_RIDGE); H(d, x0, x1, y0, S_RIDGE_HI)
    R(d, x0, y1 - 1, x1, y1, S_EAVE)
    V(d, x0, y0, y1, NAVY); V(d, x1, y0, y1, NAVY)


def lattice(d, x0, y0, x1, y1, bar=S_TIMBER_LO):
    """A window behind wooden bars (koshi): the dark of the room between them."""
    R(d, x0, y0, x1, y1, S_DARK)
    for x in range(x0, x1 + 1, 3):
        V(d, x, y0, y1, bar)
    H(d, x0, x1, y0, S_TIMBER_DK); H(d, x0, x1, y1, S_TIMBER_DK)


def devhouse_osaka():
    """96x224: the roof garden seen from above inside a tiled eave, three storeys of 42 rows, the shop front."""
    im, d = canvas(3, 7)
    # the roof garden, seen from above: raked gravel inside a bamboo fence
    R(d, 1, 9, 94, 41, S_WALL)
    for y in range(20, 42):
        for x in range(3, 93):
            s = speck(x, y, 11)
            if y % 3 == 0:
                P(d, S_WALL_LO if s > 12 else S_WALL_DK, (x, y))
            elif s < 7:
                P(d, S_WALL_HI, (x, y))
            elif s > 95:
                P(d, S_WALL_DK, (x, y))
    R(d, 1, 9, 94, 18, S_BAMBOO)                             # the fence along the back
    for x in range(1, 95, 4):
        V(d, x, 11, 18, S_BAMBOO_HI); V(d, x + 3, 11, 18, S_BAMBOO_LO)
    H(d, 1, 94, 13, S_BAMBOO_DK); H(d, 1, 94, 14, S_BAMBOO_HI)
    R(d, 1, 9, 94, 10, S_TIMBER_LO); H(d, 1, 94, 9, S_TIMBER)
    H(d, 1, 94, 19, S_WALL_DK)
    for x in (1, 93):                                      # and down each side
        R(d, x, 19, x + 1, 41, S_BAMBOO_LO)
        for y in range(20, 41, 3):
            P(d, S_BAMBOO_HI, (x, y)); P(d, S_BAMBOO_DK, (x + 1, y + 1))
    for x0, y0 in ((45, 35), (40, 29), (47, 23)):          # stepping stones to the back
        soft(d, x0, y0, x0 + 7, y0 + 4, S_ROCK); H(d, x0 + 1, x0 + 6, y0, S_ROCK_HI)
        H(d, x0 + 1, x0 + 6, y0 + 4, S_ROCK_LO)
    oval(d, 62, 26, 76, 37, NAVY); oval(d, 63, 27, 75, 36, S_ROCK); oval(d, 64, 27, 72, 32, S_ROCK_HI)   # a rock
    oval(d, 66, 29, 75, 36, S_ROCK); R(d, 66, 35, 73, 36, S_ROCK_LO)
    foliage(im, [(17, 11, 14, 10), (36, 8, 9, 7), (78, 11, 13, 9), (88, 16, 5, 6)], LEAF, 21)
    foliage(im, [(13, 31, 8, 6), (22, 35, 5, 4), (84, 32, 6, 6)], LEAF, 31)
    for x, y in ((9, 29), (16, 32), (12, 34), (82, 30), (86, 34), (24, 34)):                 # azalea
        P(d, S_PINK_HI, (x, y), (x + 1, y)); P(d, S_PINK, (x, y + 1))
    kawara(im, d, 0, 42, 95, 53)                           # the eave round it
    # the body: charred boards round plaster
    R(d, 1, 54, 94, 223, S_SOOT)
    R(d, 1, 54, 94, 55, S_SOOT_LO)
    V(d, 1, 56, 223, S_SOOT_HI); V(d, 94, 54, 223, S_SOOT_LO)
    for n in (4, 3, 2):
        y = 54 + (4 - n) * 42
        R(d, 5, y + 2, 90, y + 33, S_SHOJI)                  # plaster between the posts
        R(d, 5, y + 2, 90, y + 3, S_SHOJI_LO)
        for x in range(5, 91):
            if (x + y) % 2:
                P(d, S_SHOJI_LO, (x, y + 4))
        for x in (5, 31, 64, 90):                          # the posts
            V(d, x, y + 2, y + 33, S_SOOT); V(d, x + (1 if x < 90 else -1), y + 4, y + 33, S_SHOJI_LO)
        y0, y1 = y + 7, y + 28
        if n == 4:                                         # the tatami room: paper screens, one slid open
            for x0 in (9, 35, 68):
                R(d, x0, y0, x0 + 18, y1, S_SHOJI_HI)
                for bx in range(x0 + 6, x0 + 18, 6):
                    V(d, bx, y0, y1, S_TIMBER)
                for by in range(y0 + 5, y1, 6):
                    H(d, x0, x0 + 18, by, S_TIMBER)
                H(d, x0, x0 + 18, y0 + 1, S_SHOJI_LO)
                if x0 == 35:
                    glass(d, x0, y0 + 1, x0 + 8, y1 - 1, 7); V(d, x0 + 9, y0, y1, S_TIMBER_LO)
                H(d, x0 - 1, x0 + 19, y0, S_TIMBER_DK); H(d, x0 - 1, x0 + 19, y1, S_TIMBER_DK)
                V(d, x0 - 1, y0, y1, S_TIMBER_DK); V(d, x0 + 19, y0, y1, S_TIMBER_DK)
        elif n == 3:                                       # bars, and a reed blind let down
            lattice(d, 9, y0, 27, y1); lattice(d, 35, y0, 60, y1); lattice(d, 68, y0, 86, y1)
            R(d, 68, y0, 86, y0 + 15, S_REED)
            for by in range(y0 + 1, y0 + 15, 2):
                H(d, 68, 86, by, S_REED_LO)
            H(d, 68, 86, y0 + 15, S_TIMBER_LO)
        else:                                              # glass in wooden frames
            for x0 in (9, 35, 68):
                w = 25 if x0 == 35 else 18
                window(d, x0, y0, x0 + w, y1, S_TIMBER_DK)
                V(d, x0 + w // 2, y0 + 1, y1 - 1, S_TIMBER_DK)
                H(d, x0 + 1, x0 + w - 1, y0 + 11, S_TIMBER_DK)
        R(d, 3, y + 30, 92, y + 31, S_TIMBER_DK); H(d, 3, 92, y + 30, S_TIMBER_LO)    # a rail of bars under the windows
        for bx in range(4, 92, 3):
            V(d, bx, y + 32, y + 37, S_TIMBER_DK)
        R(d, 1, y + 38, 94, y + 41, S_SOOT_LO); H(d, 1, 94, y + 38, S_SOOT_HI)       # the floor's beam
    # the ground floor: a pent roof of tiles, the name, a noren over the door, bars either side
    y = 180
    kawara(im, d, 0, y, 95, y + 11)
    R(d, 2, y + 12, 93, 223, S_TIMBER_DK); R(d, 2, y + 12, 93, y + 13, S_TIMBER_INK)
    lattice(d, 5, y + 16, 27, 216, S_TIMBER); lattice(d, 68, y + 16, 90, 216, S_TIMBER)
    R(d, 3, 217, 29, 222, S_ROCK); R(d, 66, 217, 92, 222, S_ROCK)
    H(d, 3, 29, 217, S_ROCK_HI); H(d, 66, 92, 217, S_ROCK_HI); H(d, 3, 29, 222, S_ROCK_LO); H(d, 66, 92, 222, S_ROCK_LO)
    R(d, 32, y + 12, 63, y + 20, S_TIMBER_HI); H(d, 32, 63, y + 12, S_BOARD_HI)              # the name board
    H(d, 32, 63, y + 20, S_TIMBER_LO)
    letters(d, 33, y + 14, 'DEVHOUSE', S_SOOT_LO)
    R(d, 33, y + 21, 62, 223, S_DARK)                        # the doorway: the dark of the hall
    R(d, 33, y + 21, 62, y + 22, S_TIMBER_LO)
    R(d, 33, 218, 62, 223, S_SOOT); H(d, 33, 62, 218, S_SOOT_HI)
    V(d, 47, y + 35, 217, S_TIMBER_LO); V(d, 48, y + 35, 217, S_TIMBER_DK)
    for x0 in (34, 44, 54):                                # the noren, three widths of indigo
        R(d, x0, y + 23, x0 + 8, y + 34, S_CLOTH)
        V(d, x0, y + 23, y + 34, S_CLOTH_HI); H(d, x0, x0 + 8, y + 34, S_CLOTH_LO)
        R(d, x0 + 3, y + 27, x0 + 5, y + 29, S_SHOJI); P(d, S_CLOTH, (x0 + 4, y + 28))
    outline(im, NAVY)
    return im


SPRITES = {      # key: (builder, tileNames label)
    'devhouse-tokyo_0_0': (devhouse_tokyo, 'devhouse-tokyo'),
    'devhouse-osaka_0_0': (devhouse_osaka, 'devhouse-osaka'),
    'devhouse-stairs-up_0_0': (stairs(True), 'devhouse-stairs'),
    'devhouse-stairs-down_0_0': (stairs(False), 'devhouse-stairs'),
    'devhouse-tile_0_0': (wet_tile, 'devhouse-tile'),
    'devhouse-gravel_0_0': (gravel, 'devhouse-gravel'),
    'devhouse-stepping-stone_0_0': (stepping_stone, 'devhouse-stepping-stone'),
    'devhouse-wall-h_0_0': (wall_h, 'devhouse-wall'),
    'devhouse-wall-v_0_0': (wall_v(False), 'devhouse-wall'),
    'devhouse-wall-v-end_0_0': (wall_v(True), 'devhouse-wall'),
    'devhouse-stairwell_0_0': (stairwell, 'devhouse-stairwell'),
    'devhouse-door_0_0': (locked_door, 'devhouse-door'),
    'devhouse-fence_0_0': (fence, 'devhouse-fence'),
    'devhouse-table-wide_0_0': (table(4, 1, wide_things), 'devhouse-table'),
    'devhouse-table-tall_0_0': (table(1, 3, tall_things), 'devhouse-table'),
    'devhouse-table-small_0_0': (table(1, 2, small_things), 'devhouse-table'),
    'devhouse-chair-n_0_0': (chair('n'), 'devhouse-chair'),
    'devhouse-chair-s_0_0': (chair('s'), 'devhouse-chair'),
    'devhouse-chair-e_0_0': (chair('e'), 'devhouse-chair'),
    'devhouse-chair-w_0_0': (chair('w'), 'devhouse-chair'),
    'devhouse-stool_0_0': (stool, 'devhouse-stool'),
    'devhouse-counter_0_0': (counter, 'devhouse-counter'),
    'devhouse-sofa_0_0': (sofa, 'devhouse-sofa'),
    'devhouse-armchair_0_0': (armchair, 'devhouse-armchair'),
    'devhouse-side-table_0_0': (side_table, 'devhouse-side-table'),
    'devhouse-bunk_0_0': (bunk, 'devhouse-bunk'),
    'devhouse-basin_0_0': (basin, 'devhouse-basin'),
    'devhouse-toilet_0_0': (toilet, 'devhouse-toilet'),
    'devhouse-shower_0_0': (shower, 'devhouse-shower'),
    'devhouse-bath_0_0': (bath, 'devhouse-bath'),
    'devhouse-washer_0_0': (washer, 'devhouse-washer'),
    'devhouse-clothes-rack_0_0': (clothes_rack, 'devhouse-clothes-rack'),
    'devhouse-rock_0_0': (rock, 'devhouse-rock'),
    'devhouse-shrub_0_0': (shrub, 'devhouse-shrub'),
    'devhouse-lantern_0_0': (lantern, 'devhouse-lantern'),
    'devhouse-garden-seat_0_0': (garden_seat, 'devhouse-garden-seat'),
    'devhouse-water-bowl_0_0': (water_bowl, 'devhouse-water-bowl'),
}


def main():
    built = {}
    for key, (fn, _) in SPRITES.items():
        im = fn()
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im

    # register so the game loads them: every sprite anchors on the centre of
    # its top-left cell (unrounded - a rounded anchor drifts off the grid)
    cfg = json.load(open('config.json'))
    for key, (_, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = label
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
    print(f'{len(built)} devhouse sprites written')

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (1500, 1400), rgb('bb8971'))
        x = y = 12
        row_h = 0
        for key, im in built.items():
            if x + im.width + 12 > sheet.width:
                x, y, row_h = 12, y + row_h + 12, 0
            sheet.alpha_composite(im, (x, y)); x += im.width + 12
            row_h = max(row_h, im.height)
        sheet.crop((0, 0, sheet.width, y + row_h + 12)).save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
