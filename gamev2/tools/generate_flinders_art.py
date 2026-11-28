#!/usr/bin/env python3
"""generate_flinders_art.py — everything inside the station with the clocks in
San Franbourne (issue #246), in the house look (#292, #309).

Drawn the way tools/generate_seven_eleven_art.py and the pub of
tools/generate_sendai_art.py are: every colour is one the GuttyKreum sheets use
(art-source/GuttyKreum), the outline is the pack's navy, not black, the glass
is the pack's dark window with a slanted glare, and nothing is lit: a lamp is
the pack's dim gold. Light comes from the upper left; every piece is lit along
its top and left, shaded along its bottom and right, and casts its shade to
the lower right in the next colour down the ramp of what it falls on. Drawn at
half size (32px a cell) and pixel-doubled, with rectangles and points only (no
Pillow ellipse, polygon, arc or slanted line, which move by a pixel between
Pillow versions). Nothing is random between runs (the terrazzo's chips are
seeded) and the only text (the name board, TICKETS, the buses) is set in the
game's own font, so a re-run draws the same pixels.

The frame (the side walls, the front wall, the doorway, the light through it)
is drawn here, in the same cells and shapes as the pub's; only the plumbing
(the canvas, the font, register()) is tools/generate_pub_art.py's. The room is
the inside of `sfb-clocks-station`: mustard render banded in maroon, bluestone
at the foot, copper green ironwork; Flinders is not Japanese, only the drawing
is the pack's. The gates, the railing, the benches, the planters and the
track are the station kit's (tools/generate_station_art.py); all sprites
drawn here are `flinders-in-<piece>`:
  floor-a / floor-b       cream terrazzo (a: a maroon diamond set in it)
  side-w / side-e         the side walls seen along their length
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-bay                3x3 a bay of the back wall: mustard, maroon bands, a pilaster
  wall-arch               4x3 the back wall with an arched window, dark glass in it
  wall-name               6x3 the back wall with the name board: FLINDERS ST
  clocks                  4x3 the board of nine dials from over the door outside, their
                          hands in the same order, on two iron posts with a rail
                          between their feet (bump it: Time Travel)
  tickets                 3x2 two ticket machines under one sign (bump them)
  board                   3x2 a departures board on a stand: every row is a bus (bump it)

Run from gamev2/:  python3 tools/generate_flinders_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames,
and the back wall's three pieces in game.lookUp.sprites.
"""
import json
import math
import random
import sys

from PIL import Image

from generate_pub_art import C, new, text, latin, register
from generate_sendai_art import pane


def rgb(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# the GuttyKreum colours the room is drawn in, light to dark along each ramp
INK, EDGE = rgb('080d16'), rgb('172459')                                     # the void, the outline
MUSTARD_HI, MUSTARD, MUSTARD_LO, MUSTARD_DK = rgb('e3c587'), rgb('c6a663'), rgb('a7843b'), rgb('86624f')
MAROON_HI, MAROON, MAROON_DK = rgb('aa4d31'), rgb('904a37'), rgb('5b283b')
COPPER_HI, COPPER, COPPER_LO = rgb('93c297'), rgb('508582'), rgb('4a6262')
ENAMEL, ENAMEL_DK = rgb('395050'), rgb('2e4040')
STONE_HI, STONE, STONE_LO, STONE_DK = rgb('fafcfd'), rgb('e4cecc'), rgb('d7b6ab'), rgb('be9e8c')
BLUE_HI, BLUESTONE, BLUE_LO = rgb('78768a'), rgb('5f6177'), rgb('47485d')
TERRAZZO = rgb('d7d0ba')
CHIPS = (STONE_DK, STONE_DK, STONE_HI, STONE_HI, rgb('c69f96'), MUSTARD_HI, rgb('a4b0b5'))
STEEL_HI, STEEL, STEEL_LO = rgb('d1e2eb'), rgb('94a2a8'), rgb('575c6d')
GLASS, GLASS_LO, GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
TITLE, PANEL = rgb('588cc6'), rgb('1b1e2a')                                  # a screen's title bar; the board's panel
LAMP, LAMP_HI, LAMP_LO, LAMP_GREEN = MUSTARD, rgb('f3d890'), MUSTARD_LO, rgb('83af6f')   # unlit
DAY, DAY_MID, DAY_LO = STONE_HI, rgb('ffe2e0'), STONE                        # the day outside the door
SHADE = rgb('2a3151', 90)                                                    # shade on the floor

# what a shade turns each colour into: the next one down its ramp
DOWN = {}
for ramp in ((MUSTARD_HI, MUSTARD, MUSTARD_LO, MUSTARD_DK), (MAROON_HI, MAROON, MAROON_DK),
             (COPPER_HI, COPPER, COPPER_LO, ENAMEL, ENAMEL_DK), (STONE_HI, STONE, STONE_LO, STONE_DK),
             (BLUE_HI, BLUESTONE, BLUE_LO), (STEEL_HI, STEEL, STEEL_LO), (TERRAZZO, STONE_DK)):
    for a, b in zip(ramp, ramp[1:]):
        DOWN.setdefault(a, b)


def R(d, x0, y0, x1, y1, fill):
    if x0 <= x1 and y0 <= y1:
        d.rectangle([x0, y0, x1, y1], fill=fill)


def box(d, x0, y0, x1, y1, base, hi, lo, edge=EDGE):
    """A block: outlined, lit along its top and left, shaded along its bottom and right."""
    R(d, x0, y0, x1, y1, edge)
    R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, base)
    R(d, x0 + 1, y0 + 1, x1 - 1, y0 + 1, hi)
    R(d, x0 + 1, y0 + 1, x0 + 1, y1 - 1, hi)
    R(d, x0 + 1, y1 - 1, x1 - 1, y1 - 1, lo)
    R(d, x1 - 1, y0 + 2, x1 - 1, y1 - 1, lo)


def cast(im, x0, y0, x1, y1):
    """A shade over what is already drawn: each pixel the next colour down its ramp, the floor `SHADE`."""
    px = im.load()
    for y in range(max(0, y0), min(im.height - 1, y1) + 1):
        for x in range(max(0, x0), min(im.width - 1, x1) + 1):
            p = px[x, y]
            if p[3] == 0:
                px[x, y] = SHADE
            elif p in DOWN:
                px[x, y] = DOWN[p]


def ground_shade(d, x0, y0, x1, y1):
    """A shade on the floor: whole rows, its corners stepped in."""
    for y in range(y0, y1 + 1):
        step = 2 if y in (y0, y1) else 1 if y in (y0 + 1, y1 - 1) else 0
        R(d, x0 + step, y, x1 - step, y, SHADE)


def span(r, dy):
    """Half the width of a disc of radius r, dy rows from its middle."""
    return math.isqrt(r * r + r - dy * dy)


def disc(d, cx, cy, r, fill):
    for dy in range(-r, r + 1):
        w = span(r, dy)
        R(d, cx - w, cy + dy, cx + w, cy + dy, fill)


def slant(d, x0, y0, x1, y1, fill, inside=None):
    """A straight line a point at a time; `inside(x, y)` clips it."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = x0 + (2 * (x1 - x0) * i + n) // (2 * n)
        y = y0 + (2 * (y1 - y0) * i + n) // (2 * n)
        if inside is None or inside(x, y):
            d.point((x, y), fill=fill)


def centred(d, cx, y, s, fill):
    """`s` in the game's face, its ink centred on cx, its top ink row at y."""
    l, _, r, _ = d.textbbox((0, 0), s, font=latin(8))
    text(d, cx - (r - l) // 2, y, s, latin(8), fill)


# ---- the frame ------------------------------------------------------------------------------

def wall_side(side):
    """A side wall seen along its length from above: the void, its stone pier, a
    sliver of its mustard face, bluestone at the floor."""
    def draw():
        im, d = new(C, C)
        R(d, 0, 0, 11, 31, INK)
        R(d, 12, 0, 21, 31, STONE)                                  # the pier
        R(d, 12, 0, 12, 31, EDGE)
        R(d, 13, 0, 13, 31, STONE_HI)
        R(d, 20, 0, 20, 31, STONE_LO)
        R(d, 21, 0, 21, 31, STONE_DK)
        R(d, 22, 0, 29, 31, MUSTARD)                                # the face, foreshortened
        R(d, 22, 0, 22, 31, EDGE)
        R(d, 23, 0, 23, 31, MUSTARD_HI)
        R(d, 27, 0, 28, 31, MUSTARD_LO)
        R(d, 29, 0, 29, 31, MUSTARD_DK)
        R(d, 23, 15, 29, 17, MAROON)                                # its band
        R(d, 23, 15, 29, 15, MAROON_HI)
        R(d, 23, 17, 29, 17, MAROON_DK)
        R(d, 30, 0, 30, 31, EDGE)                                   # the bluestone at its foot
        R(d, 31, 0, 31, 31, BLUESTONE)
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def wall_front():
    """The front wall from inside: all you see is its stone coping; below it is dark."""
    im, d = new(C, C)
    R(d, 0, 0, 31, 31, INK)
    R(d, 0, 0, 31, 9, STONE)
    R(d, 0, 0, 31, 0, EDGE)
    R(d, 0, 1, 31, 1, STONE_HI)
    R(d, 0, 5, 31, 5, MAROON)
    R(d, 0, 8, 31, 8, STONE_LO)
    R(d, 0, 9, 31, 9, EDGE)
    R(d, 0, 10, 31, 15, STONE_DK)                                   # its face, in shade
    R(d, 0, 16, 31, 16, EDGE)
    return im


def threshold(side):
    """A doorway cell: the day outside in flat bands, the step, a maroon door post."""
    def draw():
        im, d = new(C, C)
        R(d, 0, 0, 31, 3, DAY_LO)
        R(d, 0, 4, 31, 9, DAY_MID)
        R(d, 0, 10, 31, 31, DAY)
        R(d, 0, 10, 31, 10, STONE_LO)                               # the step
        R(d, 0, 22, 31, 22, STONE_LO)
        x0 = 0 if side == 'w' else 26                               # the door post
        R(d, x0, 0, x0 + 5, 31, MAROON)
        R(d, x0, 0, x0, 31, EDGE)
        R(d, x0 + 5, 0, x0 + 5, 31, EDGE)
        R(d, x0 + 1, 8, x0 + 1, 31, MAROON_HI)
        R(d, x0 + 4, 8, x0 + 4, 31, MAROON_DK)
        R(d, x0 + 1, 0, x0 + 4, 6, MAROON_DK)                       # its head, in the wall's shade
        R(d, x0 + 1, 7, x0 + 4, 7, STONE)
        return im
    return draw


def doorlight():
    """Daylight falling in through the door: 2x3, on the floor, four flat steps widening to the sill."""
    im, d = new(2 * C, 3 * C)
    for y0, y1, inset, a in ((28, 47, 9, 28), (48, 67, 6, 56), (68, 83, 3, 84), (84, 95, 0, 112)):
        R(d, inset, y0, 63 - inset, y1, rgb('fafcfd', a))
    return im


# ---- the floor ----------------------------------------------------------------------------

def terrazzo(inlay, seed):
    """Cream terrazzo, a slab a cell; `inlay` sets a maroon diamond in it."""
    def draw():
        im, d = new(C, C)
        R(d, 0, 0, 31, 31, TERRAZZO)
        rnd = random.Random(seed)
        for _ in range(46):                                         # the chips in it
            x, y = rnd.randrange(1, 32), rnd.randrange(1, 32)
            d.point((x, y), fill=rnd.choice(CHIPS))
        R(d, 0, 0, 31, 0, STONE_DK)                                 # the joints
        R(d, 0, 0, 0, 31, STONE_DK)
        R(d, 1, 1, 31, 1, STONE_HI)
        R(d, 1, 1, 1, 31, STONE_HI)
        if inlay:
            for y in range(8, 25):
                for x in range(8, 25):
                    r = abs(x - 16) + abs(y - 16)
                    upper_left = x <= 16 and y <= 16
                    if r == 8:
                        d.point((x, y), fill=MAROON_HI if upper_left else MAROON_DK)
                    elif r < 8 and r > 3:
                        d.point((x, y), fill=MAROON)
                    elif r == 3:
                        d.point((x, y), fill=MUSTARD_HI if upper_left else MUSTARD_LO)
                    elif r < 3:
                        d.point((x, y), fill=MUSTARD)
        return im
    return draw


# ---- the back wall --------------------------------------------------------------------------
#
# Every piece is three cells tall and they join end to end: a stone cornice, the
# mustard render lined out in courses, a maroon band under the cornice and
# another at the dado, a panelled dado, bluestone at the foot.

BAND, DADO, FOOT = 14, 62, 86     # the upper band, the dado's band, the bluestone


def _wall(d, w):
    R(d, 0, 0, w - 1, 95, MUSTARD)
    joints = list(range(22, DADO - 1, 10))
    tops = [BAND + 4] + [j + 1 for j in joints]
    for k, (top, bottom) in enumerate(zip(tops, joints + [DADO])):  # the render, lined out as courses
        for x in range(16 * (k % 2), w, 32):
            R(d, x, top, x, bottom - 1, MUSTARD_LO)
            if x + 1 < w:
                R(d, x + 1, top + 1, x + 1, bottom - 1, MUSTARD_HI)
    for j in joints:
        R(d, 0, j, w - 1, j, MUSTARD_LO)
        R(d, 0, j + 1, w - 1, j + 1, MUSTARD_HI)
    R(d, 0, 0, w - 1, 8, STONE)                                     # the cornice
    R(d, 0, 0, w - 1, 0, EDGE)
    R(d, 0, 1, w - 1, 1, STONE_HI)
    R(d, 0, 5, w - 1, 5, STONE_DK)
    R(d, 0, 7, w - 1, 7, STONE_LO)
    R(d, 0, 8, w - 1, 8, EDGE)
    R(d, 0, 9, w - 1, 9, MUSTARD_DK)                                # its shade on the render
    R(d, 0, 10, w - 1, 11, MUSTARD_LO)
    for y in (BAND, DADO):                                          # the bands, as on the street front
        R(d, 0, y, w - 1, y + 3, MAROON)
        R(d, 0, y, w - 1, y, MAROON_HI)
        R(d, 0, y + 3, w - 1, y + 3, MAROON_DK)
    R(d, 0, BAND + 4, w - 1, BAND + 4, MUSTARD_LO)
    R(d, 0, DADO + 4, w - 1, FOOT - 1, MUSTARD_LO)                  # the dado: a panel a cell, set in
    R(d, 0, DADO + 4, w - 1, DADO + 4, MUSTARD_DK)
    for x in range(0, w, 32):
        R(d, x + 3, DADO + 7, x + 28, FOOT - 4, MUSTARD_HI)
        R(d, x + 3, DADO + 7, x + 27, FOOT - 5, MUSTARD_DK)
        R(d, x + 4, DADO + 8, x + 27, FOOT - 5, MUSTARD)
    R(d, 0, FOOT, w - 1, 95, BLUESTONE)                             # bluestone at the foot
    R(d, 0, FOOT, w - 1, FOOT, EDGE)
    R(d, 0, FOOT + 1, w - 1, FOOT + 1, BLUE_HI)
    for x in range(0, w, 16):
        R(d, x + 7, FOOT + 2, x + 7, 94, BLUE_LO)
    R(d, 0, 95, w - 1, 95, INK)


GLOBE = (2, 4, 5, 5, 5, 5, 5, 5, 4, 2)    # half-widths of the lamp's globe, row by row (10 across)


def _lamp(im, d, x, y):
    """A wall lamp, unlit: a copper bracket, an opal globe under it; (x, y) is the bracket's top-left."""
    cx = x + 4                                                      # the globe spans cx - 5 .. cx + 4
    cast(im, cx + 5, y + 3, cx + 6, y + 13)                         # its shade, to the lower right
    cast(im, cx - 3, y + 13, cx + 6, y + 14)
    box(d, x, y, x + 7, y + 2, COPPER, COPPER_HI, COPPER_LO)
    for k, h in enumerate(GLOBE):
        R(d, cx - h, y + 3 + k, cx + h - 1, y + 3 + k, EDGE)
        if 0 < k < len(GLOBE) - 1:
            R(d, cx - h + 1, y + 3 + k, cx + h - 2, y + 3 + k, STONE if k < 5 else LAMP)
    d.point((cx - 3, y + 5), fill=STONE_HI)                         # the glint
    d.point((cx - 2, y + 5), fill=STONE_HI)
    d.point((cx - 3, y + 6), fill=STONE_HI)
    d.point((cx - 2, y + 8), fill=LAMP_HI)
    d.point((cx + 2, y + 10), fill=LAMP_LO)
    d.point((cx + 1, y + 11), fill=LAMP_LO)
    d.point((cx + 3, y + 9), fill=LAMP_LO)


def wall_bay():
    """A bay of the wall, 3x3: a stone pilaster up its middle, a lamp on it."""
    W = 3 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    cast(im, 61, 13, 63, FOOT - 6)                                  # its shade down the wall
    R(d, 38, 9, 57, FOOT, EDGE)                                     # the pilaster
    R(d, 39, 9, 56, FOOT, STONE)
    R(d, 39, 9, 39, FOOT, STONE_HI)
    R(d, 55, 9, 55, FOOT, STONE_LO)
    R(d, 56, 9, 56, FOOT, STONE_DK)
    for x in (43, 47, 51):                                          # its flutes
        R(d, x, 13, x, FOOT - 6, STONE_LO)
        R(d, x + 1, 13, x + 1, FOOT - 6, STONE_HI)
    for y in (BAND, DADO):                                          # the bands run round it
        R(d, 38, y, 57, y + 3, EDGE)
        R(d, 39, y + 1, 56, y + 2, MAROON)
        R(d, 39, y + 1, 56, y + 1, MAROON_HI)
        R(d, 56, y + 1, 56, y + 2, MAROON_DK)
    box(d, 35, 8, 60, 12, STONE, STONE_HI, STONE_DK)                # its capital
    box(d, 35, FOOT - 5, 60, FOOT, STONE, STONE_HI, STONE_DK)       # its foot
    _lamp(im, d, 44, 28)
    return im


def wall_arch():
    """The wall with an arched window, 4x3: a maroon frame, a fan in its head,
    dark glass with the glare across it, a stone sill."""
    W = 4 * C
    im, d = new(W, 3 * C)
    _wall(d, W)

    def r2(x, y):
        return (2 * x - 127) ** 2 + ((2 * (y - 45) - 1) ** 2 if y <= 45 else 0)

    def glass(x, y):
        return y <= 56 and r2(x, y) <= 59 ** 2

    cast(im, 99, 47, 100, 56)                                       # its shade on the wall
    for y in range(8, 57):
        for x in range(W):
            q = r2(x, y)
            if q > 70 ** 2:
                continue
            if q > 67 ** 2:
                c = EDGE
            elif q > 59 ** 2:                                       # the frame: lit on its upper left, dark on its right
                lit = -(2 * x - 127) - (2 * (y - 45) - 1 if y <= 45 else 0)
                c = MAROON_HI if lit > 40 else MAROON_DK if 2 * x - 127 > 30 and q > 63 ** 2 else MAROON
            elif not glass(x, y - 1) or not glass(x, y - 2):
                c = GLASS_LO
            else:
                c = GLARE if (x + y) % 13 == 0 else GLASS
            d.point((x, y), fill=c)
    for a, b in (((63, 45), (38, 34)), ((63, 45), (48, 21)), ((64, 45), (79, 21)), ((64, 45), (89, 34))):
        slant(d, *a, *b, MAROON, glass)                             # the fan of the arch
    R(d, 63, 16, 64, 56, MAROON)                                    # the mullion
    R(d, 64, 16, 64, 43, MAROON_DK)
    R(d, 34, 44, 93, 46, MAROON)                                    # the transom
    R(d, 34, 44, 93, 44, MAROON_HI)
    R(d, 34, 46, 93, 46, MAROON_DK)
    for x0, x1 in ((34, 47), (49, 62), (65, 78), (80, 93)):
        R(d, x0, 47, x1, 47, GLASS_LO)
    for x in (48, 79):
        R(d, x, 47, x, 56, MAROON)
    for dy in range(-3, 1):                                         # the fan's boss
        w = span(3, dy)
        R(d, 64 - w, 45 + dy, 63 + w, 45 + dy, MAROON_DK if dy == -3 else MAROON)
    d.point((62, 43), fill=MAROON_HI)
    box(d, 26, 57, 101, 61, STONE, STONE_HI, STONE_DK)              # the sill
    cast(im, 28, 62, 103, 62)
    return im


def wall_name():
    """The wall with the name board, 6x3: enamel in a copper frame, hung by two
    rods from the cornice, a lamp either side."""
    W = 6 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    for x in (62, 128):                                             # the rods it hangs by
        R(d, x, 9, x, 25, COPPER)
        R(d, x + 1, 9, x + 1, 25, COPPER_LO)
        cast(im, x + 2, 11, x + 2, 25)
    cast(im, 152, 29, 154, 53)                                      # the board's shade on the wall
    cast(im, 43, 51, 151, 53)
    box(d, 40, 26, 151, 50, COPPER, COPPER_HI, COPPER_LO)           # the frame
    R(d, 43, 29, 148, 47, EDGE)                                     # ...round dark enamel
    R(d, 44, 30, 147, 46, ENAMEL)
    R(d, 44, 30, 147, 30, COPPER_LO)
    R(d, 44, 46, 147, 46, ENAMEL_DK)
    centred(d, 96, 35, 'FLINDERS ST', STONE)
    for x in (41, 149):                                             # its rivets
        for y in (28, 48):
            d.point((x, y), fill=STONE_HI)
    _lamp(im, d, 16, 28)
    _lamp(im, d, 168, 28)
    return im


# ---- what stands on the floor ---------------------------------------------------------------

def clocks():
    """The clocks, 4x3: the board of nine dials from over the doors outside
    (tools/generate_sanfranbourne_art.py: the same order of hands, a lamp under
    each), a line's plate under every dial, on two iron posts. The bottom cell
    is the posts' feet and the rail between them: that row is in the way, the
    board is over your head."""
    W = 4 * C
    im, d = new(W, 3 * C)
    ground_shade(d, 6, 87, 125, 95)
    R(d, 6, 43, 125, 43, SHADE)                                     # the board's shade
    for x0 in (9, 113):                                             # the posts
        box(d, x0, 40, x0 + 5, 90, COPPER, COPPER_HI, COPPER_LO)
        box(d, x0 - 1, 56, x0 + 6, 59, COPPER, COPPER_HI, COPPER_LO)        # a collar
        box(d, x0 - 2, 88, x0 + 7, 93, BLUESTONE, BLUE_HI, BLUE_LO)         # the foot
    box(d, 15, 68, 112, 71, COPPER, COPPER_HI, COPPER_LO)           # the rail between their feet
    R(d, 15, 84, 112, 85, COPPER_LO)
    R(d, 15, 84, 112, 84, COPPER)
    R(d, 15, 86, 112, 86, EDGE)
    for x in range(20, 110, 6):                                     # its balusters
        R(d, x, 72, x, 83, COPPER_LO)
        d.point((x, 78), fill=COPPER_HI)
        d.point((x + 1, 73), fill=SHADE)
    for y in range(1, 8):                                           # the board's cresting, stepped
        h = 2 * (y - 1) + 1
        R(d, 64 - h, y, 63 + h, y, EDGE)
        if y > 1:
            R(d, 65 - h, y, 62 + h, y, COPPER)
            R(d, 65 - h, y, 66 - h, y, COPPER_HI)
            R(d, 61 + h, y, 62 + h, y, COPPER_LO)
    box(d, 3, 8, 124, 42, COPPER, COPPER_HI, COPPER_LO)             # the board: a copper frame...
    R(d, 5, 11, 122, 39, EDGE)                                      # ...round dark enamel
    R(d, 6, 12, 121, 38, ENAMEL)
    R(d, 6, 12, 121, 12, COPPER_LO)
    R(d, 6, 38, 121, 38, ENAMEL_DK)
    for i in range(9):                                              # the nine dials, in threes
        cx, cy = 14 + i * 12 + (i // 3) * 2, 20
        hx, hy = ((1, 0), (0, 1), (-1, 0))[i % 3]
        disc(d, cx, cy, 5, EDGE)
        disc(d, cx, cy, 4, STONE_HI)
        for dy in range(-4, 5):                                     # its rim, shaded lower right
            for dx in range(-4, 5):
                if abs(dx) <= span(4, dy) and (abs(dx) > span(3, dy) if abs(dy) <= 3 else True) and dx + dy > 0:
                    d.point((cx + dx, cy + dy), fill=STONE_LO)
        R(d, cx, cy - 3, cx, cy, INK)                               # the minute hand, straight up
        R(d, min(cx, cx + 3 * hx), min(cy, cy + 3 * hy), max(cx, cx + 3 * hx), max(cy, cy + 3 * hy), MAROON)   # the hour hand
        d.point((cx, cy), fill=INK)
        box(d, cx - 4, 28, cx + 4, 32, STONE, STONE_HI, STONE_LO)  # the line's plate
        R(d, cx - 2, 30, cx + 1 + i % 2, 30, ENAMEL)
        R(d, cx - 1, 35, cx, 36, LAMP)                              # its lamp, unlit
        d.point((cx - 1, 35), fill=LAMP_HI)
    return im


def _machine(d, x0, shift):
    """One ticket machine, 42px wide from x0: a screen, a slot for the fare card, a tray."""
    box(d, x0, 14, x0 + 41, 59, COPPER, COPPER_HI, COPPER_LO)
    R(d, x0 + 4, 18, x0 + 37, 36, EDGE)                             # the screen
    pane(d, x0 + 5, 19, x0 + 36, 35, 17)
    R(d, x0 + 6, 21, x0 + 35, 22, TITLE)
    for n, y in enumerate((25, 28, 31)):                            # the fares on it
        R(d, x0 + 7, y, x0 + 16 + (n + shift) % 3 * 3, y, STEEL_HI)
        R(d, x0 + 29, y - 1, x0 + 33, y, LAMP)
    box(d, x0 + 4, 39, x0 + 23, 46, STEEL, STEEL_HI, STEEL_LO)      # where the card goes
    R(d, x0 + 7, 42, x0 + 20, 43, INK)
    box(d, x0 + 10, 39, x0 + 17, 42, STONE_HI, STONE_HI, STONE_LO)  # a card, left in it
    R(d, x0 + 12, 40, x0 + 15, 40, MAROON)
    for row in range(2):                                            # the keys
        for col in range(3):
            kx, ky = x0 + 27 + col * 4, 40 + row * 4
            R(d, kx, ky, kx + 1, ky + 1, STONE)
            d.point((kx, ky), fill=STONE_HI)
            d.point((kx + 1, ky + 1), fill=STONE_DK)
            d.point((kx + 2, ky + 1), fill=COPPER_LO)
    box(d, x0 + 4, 49, x0 + 37, 56, STEEL_LO, STEEL, STEEL_LO)      # the tray
    R(d, x0 + 6, 51, x0 + 35, 54, INK)


def tickets():
    """Two ticket machines side by side, 3x2, under one sign."""
    W = 3 * C
    im, d = new(W, 2 * C)
    ground_shade(d, 6, 58, 95, 63)
    R(d, 46, 16, 49, 58, SHADE)                                     # the first machine's shade on the gap
    _machine(d, 4, 0)
    _machine(d, 50, 1)
    box(d, 3, 59, 92, 62, BLUESTONE, BLUE_HI, BLUE_LO)              # the plinth they stand on
    box(d, 8, 1, 87, 14, MAROON, MAROON_HI, MAROON_DK)              # the sign over them
    centred(d, 48, 4, 'TICKETS', STONE)
    return im


def board():
    """A departures board on a stand, 3x2: a platform's lamp, where to, and how
    you are going - every row is a bus."""
    W = 3 * C
    im, d = new(W, 2 * C)
    ground_shade(d, 10, 56, 94, 63)
    for x0 in (20, 71):                                             # the stand
        box(d, x0, 44, x0 + 4, 58, STEEL, STEEL_HI, STEEL_LO)
        box(d, x0 - 6, 57, x0 + 10, 61, STEEL_LO, STEEL, STEEL_LO)
    box(d, 4, 1, 91, 46, STEEL, STEEL_HI, STEEL_LO)                 # the case
    R(d, 7, 4, 88, 43, EDGE)
    R(d, 8, 5, 87, 42, PANEL)

    def inside(x, y):
        return 8 <= x <= 87 and 5 <= y <= 42

    for x in (18, 44, 70):                                          # the glass over it: the glare
        slant(d, x, 42, x + 19, 5, GLASS, inside)
        slant(d, x + 1, 42, x + 20, 5, GLASS, inside)
    for n, y in enumerate((7, 16, 25, 34)):                         # the rows, unlit
        R(d, 10, y + 1, 14, y + 5, LAMP_GREEN if n == 0 else LAMP_LO)
        for k in range(3 + (n * 2) % 3):                            # where to: too small to read
            R(d, 19 + k * 6, y + 2, 22 + k * 6, y + 4, LAMP_LO)
        text(d, 62, y, 'BUS', latin(8), LAMP)
        if n:
            R(d, 8, y - 2, 87, y - 2, GLASS_LO)
    return im


def sprites():
    p = 'flinders-in-'
    return {
        p + 'floor-a': terrazzo(True, 246), p + 'floor-b': terrazzo(False, 247),
        p + 'side-w': wall_side('w'), p + 'side-e': wall_side('e'),
        p + 'wall-front': wall_front,
        p + 'threshold-w': threshold('w'), p + 'threshold-e': threshold('e'),
        p + 'doorlight': doorlight,
        p + 'wall-bay': wall_bay, p + 'wall-arch': wall_arch, p + 'wall-name': wall_name,
        p + 'clocks': clocks, p + 'tickets': tickets, p + 'board': board,
    }


# The light through the door lies on the floor, as the pub's and the mall's.
DEPTH_BIAS = {'flinders-in-doorlight': -40}


# Worth looking up at from the platform: sprite family -> rows of building
# below the sprite (config game.lookUp.sprites, see "Looking up at landmarks"
# in hud-input-touch.md). The two rows are the track: nobody stands nearer the
# wall than the platform's edge, five rows under its top, and from there the
# ordinary camera of a landscape phone shows none of it. The whole wall is
# marked, so the view is the same from one end of the platform to the other;
# the reach has faded out a few rows into the concourse.
LOOK_UP = {'flinders-in-wall-bay': 2, 'flinders-in-wall-arch': 2, 'flinders-in-wall-name': 2}


if __name__ == '__main__':
    register(sprites(), DEPTH_BIAS, sys.argv)
    cfg = json.load(open('config.json'))
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
