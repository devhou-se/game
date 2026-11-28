#!/usr/bin/env python3
"""generate_izakaya_art.py — the inside of the Izakaya in Tokyo (issue #286):
the izakaya-in-* kit tools/generate_izakaya.py furnishes the room with.

Drawn in the house look (docs/generators-and-checks.md, "House look:
GuttyKreum"; the helpers are tools/house_look.py): every colour one of the
GuttyKreum sheets', light from the upper left, the standing pieces closed with
the pack's ink, drawn at half size (32px a cell) and doubled. Rectangles,
single pixels and the game's 1-bit PixelMplus12 only, and fixed seeds, so a
re-run paints the same pixels on any Pillow. The lanterns are drawn unlit: at
night the room is lantern-lit and the glow is the engine's (GLOW).

  izakaya-in-floor-a / -b         the floor: four timber boards a cell, laid as a chequer
  izakaya-in-side-w / -e          the tops of the side walls (on the void)
  izakaya-in-wall-front           the top of the front wall
  izakaya-in-threshold-w / -e     the doorway: the sill, the pavement beyond, a door post
  izakaya-in-wall                 the back wall, 1x2: a timber beam, plaster, a rail, boards
  izakaya-in-wall-menu            2x2, the same with three paper menu strips
  izakaya-in-wall-clock           1x2, the same with a pendulum clock: the time-travel clock
  izakaya-in-backbar              6x2, shelves of bottles and flasks over a cupboard
  izakaya-in-bar                  6x1, the counter: beer, edamame, karaage and sake on its top
  izakaya-in-table                2x1, a low table laid for two
  izakaya-in-chochin              1x2, a red paper lantern hung on its cord
  izakaya-in-casks                1x2, two straw-wrapped sake casks, stacked

What a bump on each opens is in src/utils/Interactions.js. No rubbish bin in it.
The bar stools are izakaya-stool_0_0 (tools/extract_street.py).

Run from gamev2/:  python3 tools/generate_izakaya_art.py [--sheet out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames;
generate_izakaya.py appends their palette keys when it places them.
"""
import random
import sys

from PIL import Image

import art_register
import house_look as hl

# all timber, dark to light: GuttyKreum sheet colours (tools/tests/izakaya.test.js holds it)
W = [hl.rgb(t) for t in '3f210f 5a3827 71412a 7f513b aa775f bb8971'.split()]
P = hl.RAMPS['cream']               # plaster, paper, china, the head on a beer
RED, GOLD, GREEN, BLUE, STEEL, NIGHT = (hl.RAMPS[r] for r in ('red', 'gold', 'green', 'blue', 'steel', 'night'))
INK, INK_DEEP = hl.INK, hl.INK_DEEP
fill = hl.fill


def dot(im, x, y, c):
    im.putpixel((x, y), c)


def rows(im, cx2, y, widths, c):
    """One row a width from y down, each centred on cx2 / 2: a round shape a row at a time."""
    for i, w in enumerate(widths):
        x0 = (cx2 - w + 1) // 2
        fill(im, (x0, y + i, x0 + w - 1, y + i), c)


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


# ---- the frame and the ground (not outlined) -----------------------------------------
def boards(seed, shift):
    def draw():
        rnd = random.Random(seed)
        im = hl.canvas(32, 32)
        fill(im, (0, 0, 31, 31), W[2])
        for i in range(4):
            a = 8 * i
            fill(im, (0, a, 31, a), W[3])
            fill(im, (0, a + 7, 31, a + 7), W[1])
            for _ in range(3):
                x, y = rnd.randrange(32), a + rnd.randrange(2, 6)
                n = rnd.randrange(3, 7) + 1
                fill(im, (x, y, min(x + n - 1, 31), y), rnd.choice((W[1], W[3])))
            if i % 2 == shift:                      # a butt joint
                j = (10, 4, 22, 26)[i]
                fill(im, (j, a, j, a + 6), W[1])
                fill(im, (j + 1, a + 1, j + 1, a + 6), W[3])
        return im
    return draw


def side_w():
    im = hl.canvas(32, 32)
    fill(im, (0, 0, 15, 31), INK_DEEP)
    fill(im, (16, 0, 16, 31), INK)
    fill(im, (17, 0, 28, 31), W[1])
    fill(im, (17, 0, 17, 31), W[3])
    fill(im, (18, 0, 18, 31), W[2])
    fill(im, (28, 0, 28, 31), W[0])
    fill(im, (22, 5, 22, 12), W[0])
    fill(im, (22, 21, 22, 28), W[0])
    fill(im, (29, 0, 29, 31), INK)
    fill(im, (30, 0, 31, 31), W[1])             # the wall's shade on the floor
    return im


def side_e():
    im = mirror(side_w())
    fill(im, (0, 0, 1, 31), W[3])               # that face is lit
    return im


def wall_front():
    im = hl.canvas(32, 32)
    fill(im, (0, 0, 31, 31), INK_DEEP)
    fill(im, (0, 0, 31, 0), INK)
    fill(im, (0, 1, 31, 11), W[1])
    fill(im, (0, 1, 31, 1), W[3])
    fill(im, (0, 2, 31, 2), W[2])
    fill(im, (0, 11, 31, 11), W[0])
    fill(im, (6, 6, 13, 6), W[0])
    fill(im, (22, 6, 29, 6), W[0])
    fill(im, (0, 12, 31, 12), INK)
    return im


def threshold_w():
    im = hl.canvas(32, 32)
    fill(im, (0, 0, 31, 12), W[4])              # the sill
    fill(im, (0, 0, 31, 0), W[5])
    fill(im, (0, 11, 31, 12), W[3])
    fill(im, (0, 13, 31, 13), INK)
    fill(im, (0, 14, 31, 31), STEEL[1])         # the pavement outside
    fill(im, (0, 14, 31, 17), STEEL[2])
    for x in range(0, 32, 2):
        dot(im, x, 18, STEEL[2])
    fill(im, (0, 26, 31, 31), STEEL[0])
    for x in range(1, 32, 2):
        dot(im, x, 25, STEEL[0])
    fill(im, (0, 0, 4, 31), W[1])               # the door post
    fill(im, (0, 0, 0, 31), W[3])
    fill(im, (4, 0, 4, 31), W[0])
    fill(im, (5, 0, 5, 31), INK)
    return im


def threshold_e():
    return mirror(threshold_w())


# ---- the back wall, two cells tall ---------------------------------------------------
BEAM, RAIL, FOOT = 6, 42, 62


def bay(im, x0, w):
    x1 = x0 + w - 1
    fill(im, (x0, 0, x1, 0), INK)
    fill(im, (x0, 1, x1, BEAM), W[1])           # the beam
    fill(im, (x0, 1, x1, 1), W[3])
    fill(im, (x0, BEAM, x1, BEAM), W[0])
    fill(im, (x0, 7, x1, RAIL - 1), P[2])       # plaster, in the beam's shadow at the top
    fill(im, (x0, 7, x1, 8), P[1])
    for x in range(x0, x1 + 1):
        if (x + 9) % 2:
            dot(im, x, 9, P[1])
        if (x + 42) % 2:
            dot(im, x, 40, P[3])
    fill(im, (x0, 41, x1, 41), P[3])
    fill(im, (x0, RAIL, x1, RAIL + 2), W[1])    # the rail
    fill(im, (x0, RAIL, x1, RAIL), W[3])
    fill(im, (x0, RAIL + 2, x1, RAIL + 2), W[0])
    fill(im, (x0, 45, x1, FOOT - 1), W[1])      # the boards under it
    fill(im, (x0, 45, x1, 45), W[0])
    for x in range(x0, x1 + 1, 8):
        fill(im, (x, 46, x, FOOT - 1), W[0])
        fill(im, (x + 1, 46, x + 1, FOOT - 1), W[2])
    fill(im, (x0, FOOT, x1, FOOT), W[0])
    fill(im, (x0, 63, x1, 63), INK)
    fill(im, (x0, 7, x0 + 3, RAIL - 1), W[1])   # a post over the plaster, and its shade
    fill(im, (x0, 7, x0, RAIL - 1), W[3])
    fill(im, (x0 + 3, 7, x0 + 3, RAIL - 1), W[0])
    fill(im, (x0 + 4, 9, x0 + 4, RAIL - 1), P[1])


def wall():
    im = hl.canvas(32, 64)
    bay(im, 0, 32)
    return im


def strip(im, x, y, s, paper):
    """A paper menu strip pinned to the wall, its words set downwards."""
    w, h = hl.text_size(s, vertical=True, pitch=11)
    y1 = y + h + 4
    fill(im, (x + 1, y + 1, x + 14, y1 + 1), P[0])
    fill(im, (x, y, x + 13, y1), W[0])
    fill(im, (x + 1, y + 1, x + 12, y1 - 1), paper)
    fill(im, (x + 1, y1 - 1, x + 12, y1 - 1), P[1] if paper == P[3] else GOLD[2])
    fill(im, (x + 6, y + 1, x + 7, y + 1), RED[1])
    hl.text(im, x + 1 + (12 - w) // 2, y + 3, s, INK, vertical=True, pitch=11)


def wall_menu():
    im = hl.canvas(64, 64)
    bay(im, 0, 64)
    for x, s, paper in ((8, 'ビール', P[3]), (26, '枝豆', GOLD[3]), (44, '唐揚げ', P[3])):
        strip(im, x, 9, s, paper)
    return im


def wall_clock():
    im = hl.canvas(32, 64)
    bay(im, 0, 32)
    fill(im, (11, 10, 26, 40), P[1])            # its shade on the plaster
    fill(im, (9, 8, 24, 38), W[0])              # the case
    fill(im, (10, 9, 23, 37), W[2])
    fill(im, (10, 9, 23, 9), W[4])
    fill(im, (10, 9, 10, 37), W[3])
    fill(im, (23, 10, 23, 37), W[1])
    rows(im, 33, 11, (6, 8, 10, 10, 10, 10, 10, 10, 8, 6), W[0])     # the dial
    rows(im, 33, 12, (4, 8, 8, 8, 8, 8, 8, 4), P[3])
    fill(im, (18, 14, 19, 15), P[2])
    fill(im, (19, 17, 20, 18), P[2])
    fill(im, (16, 13, 16, 16), INK)             # the minute hand
    fill(im, (16, 16, 19, 16), RED[0])          # the hour hand
    fill(im, (12, 23, 21, 35), W[0])            # the pendulum's window
    fill(im, (13, 24, 20, 34), NIGHT[3])
    for i in range(5):
        dot(im, 14 + i, 30 - i, NIGHT[4])
    fill(im, (16, 24, 16, 29), GOLD[1])         # the rod and the bob
    fill(im, (15, 30, 17, 32), GOLD[2])
    dot(im, 15, 30, GOLD[3])
    return im


# ---- small pictures: what stands on the bar, the shelves and the tables ---------------
GLASS = {'green': (GREEN[2], GREEN[3], GREEN[1]), 'brown': (W[2], W[4], W[1]),
         'blue': (BLUE[1], BLUE[3], BLUE[0]), 'gold': (GOLD[2], GOLD[3], GOLD[1])}


def bottle(im, x, base, kind, cap, h=16):
    body, hi, lo = GLASS[kind]
    top = base - h + 1
    fill(im, (x + 1, top, x + 3, top + 1), cap)
    fill(im, (x + 1, top + 2, x + 3, top + 4), body)
    dot(im, x + 1, top + 2, hi)
    fill(im, (x, top + 5, x + 4, base), body)
    fill(im, (x, top + 6, x, base), hi)
    fill(im, (x + 4, top + 5, x + 4, base), lo)
    fill(im, (x, base - 6, x + 4, base - 2), P[3])      # the label
    fill(im, (x + 4, base - 6, x + 4, base - 2), P[2])
    fill(im, (x + 1, base - 5, x + 2, base - 3), INK if kind == 'gold' else RED[1])


def flask(im, x, base):
    """A tokkuri of sake and its cup."""
    rows(im, 2 * x + 3, base - 6, (2, 2, 4, 4, 4, 4, 4), P[2])
    fill(im, (x, base - 4, x, base), P[3])
    fill(im, (x + 3, base - 4, x + 3, base), P[1])
    fill(im, (x, base - 2, x + 3, base - 2), BLUE[2])
    fill(im, (x + 6, base - 1, x + 8, base), P[3])
    dot(im, x + 8, base, P[1])


def mug(im, x, base):
    fill(im, (x, base - 6, x + 3, base), GOLD[2])
    fill(im, (x, base - 6, x, base), GOLD[3])
    fill(im, (x + 3, base - 5, x + 3, base), GOLD[1])
    fill(im, (x, base - 7, x + 3, base - 6), P[3])
    dot(im, x + 3, base - 6, P[1])
    fill(im, (x + 4, base - 4, x + 5, base - 4), STEEL[4])
    fill(im, (x + 4, base - 1, x + 5, base - 1), STEEL[4])
    fill(im, (x + 5, base - 3, x + 5, base - 2), STEEL[4])


FOOD = {'edamame': (GREEN[4], GREEN[3], GREEN[2]), 'karaage': (GOLD[2], GOLD[1], W[3])}


def plate(im, x, base, food):
    rows(im, 2 * x + 8, base - 3, (7, 9, 9, 7), P[3])
    fill(im, (x + 1, base, x + 7, base), P[1])
    for i, (dx, dy) in enumerate(((2, -3), (4, -3), (6, -3), (3, -2), (5, -2), (1, -2), (7, -2), (4, -4))):
        dot(im, x + dx, base + dy, FOOD[food][i % 3])


# ---- the furniture --------------------------------------------------------------------
def backbar():
    rnd = random.Random(286)
    im = hl.canvas(192, 64)
    fill(im, (0, 0, 191, 63), INK)
    fill(im, (1, 1, 190, 3), W[2])              # the top
    fill(im, (1, 1, 190, 1), W[4])
    fill(im, (1, 3, 190, 3), W[0])
    fill(im, (1, 4, 190, 49), W[0])             # the back of the shelves
    for y in (23, 46):
        fill(im, (1, y, 190, y + 2), W[3])
        fill(im, (1, y, 190, y), W[5])
        fill(im, (1, y + 2, 190, y + 2), W[1])
    for y in (4, 26):                           # in the shadow of the board above
        fill(im, (1, y, 190, y), INK_DEEP)
    fill(im, (1, 49, 190, 62), W[2])            # the cupboard
    fill(im, (1, 49, 190, 49), W[0])
    fill(im, (1, 62, 190, 62), W[0])
    for b in range(6):
        x0 = 32 * b
        if b:
            fill(im, (x0 - 1, 4, x0, 62), W[1])
            fill(im, (x0 - 1, 4, x0 - 1, 62), W[3])
        fill(im, (x0 + 3, 51, x0 + 28, 60), W[3])   # a sliding door and its pull
        fill(im, (x0 + 3, 51, x0 + 28, 51), W[4])
        fill(im, (x0 + 3, 60, x0 + 28, 60), W[1])
        fill(im, (x0 + 28, 51, x0 + 28, 60), W[1])
        fill(im, (x0 + 14, 55, x0 + 17, 56), W[0])
        x = x0 + 3
        for _ in range(4):
            kind = rnd.choice(('green', 'brown', 'green', 'blue', 'brown'))
            cap = rnd.choice((GOLD[2], RED[1], P[3]))
            bottle(im, x, 22, kind, cap)
            x += 6 + rnd.randrange(2)
        if b % 2 == 0:
            for i in range(3):
                bottle(im, x0 + 3 + 7 * i, 45, rnd.choice(('gold', 'brown', 'gold')), RED[1], h=13)
            if b != 4:
                flask(im, x0 + 23, 45)
        else:
            flask(im, x0 + 3, 45)
            flask(im, x0 + 13, 45)
            for i in range(2):
                fill(im, (x0 + 24, 43 - 4 * i, x0 + 27, 45 - 4 * i), P[3])
                fill(im, (x0 + 27, 43 - 4 * i, x0 + 27, 45 - 4 * i), P[1])
                fill(im, (x0 + 24, 44 - 4 * i, x0 + 26, 44 - 4 * i), BLUE[3])
    return im


def bar():
    rnd = random.Random(2860)
    im = hl.canvas(192, 32)
    fill(im, (0, 0, 191, 30), INK)
    fill(im, (1, 1, 190, 12), W[4])             # the top, and its grain
    fill(im, (1, 1, 190, 1), W[5])
    for _ in range(26):
        x, y = rnd.randrange(2, 182), rnd.randrange(3, 10)
        n = rnd.randrange(4, 9) + 1
        fill(im, (x, y, x + n - 1, y), rnd.choice((W[5], W[3])))
    fill(im, (1, 11, 190, 11), W[3])
    fill(im, (1, 12, 190, 12), W[2])
    fill(im, (1, 13, 190, 13), W[0])
    fill(im, (1, 14, 190, 28), W[1])            # the front, in boards
    for x in range(1, 191, 16):
        fill(im, (x, 14, x, 28), W[0])
        fill(im, (x + 1, 14, x + 1, 28), W[2])
    fill(im, (1, 22, 190, 22), W[0])            # the foot rail
    fill(im, (1, 23, 190, 23), W[2])
    fill(im, (1, 29, 190, 29), W[0])
    fill(im, (190, 14, 190, 29), W[0])
    mug(im, 14, 9)
    plate(im, 38, 9, 'edamame')
    flask(im, 68, 9)
    mug(im, 98, 9)
    plate(im, 120, 9, 'karaage')
    flask(im, 150, 9)
    bottle(im, 176, 10, 'green', GOLD[2], h=10)
    bottle(im, 182, 10, 'brown', RED[1], h=10)
    return im


def table():
    rnd = random.Random(28600)
    im = hl.canvas(64, 32)
    fill(im, (2, 4, 61, 17), W[4])
    fill(im, (2, 4, 61, 4), W[5])
    fill(im, (2, 4, 2, 17), W[5])
    for _ in range(9):
        x, y = rnd.randrange(4, 50), rnd.randrange(6, 16)
        n = rnd.randrange(4, 9) + 1
        fill(im, (x, y, x + n - 1, y), rnd.choice((W[5], W[3])))
    fill(im, (2, 18, 61, 18), W[3])             # the apron
    fill(im, (2, 19, 61, 19), W[2])
    fill(im, (2, 20, 61, 20), W[1])
    for x in (4, 56):                           # the legs
        fill(im, (x, 21, x + 3, 28), W[1])
        fill(im, (x, 21, x, 28), W[2])
        fill(im, (x + 3, 21, x + 3, 28), W[0])
    fill(im, (8, 21, 55, 21), W[0])
    mug(im, 12, 13)
    mug(im, 44, 12)
    plate(im, 26, 14, 'edamame')
    hl.outline(im)
    return im


def chochin():
    im = hl.canvas(32, 64)
    WD = (12, 16, 18, 20, 20, 20, 20, 20, 20, 20, 20, 20, 18, 16, 12)
    rows(im, 33, 37, WD, RED[1])
    for i, wd in enumerate(WD):
        y, x0 = 37 + i, (34 - wd) // 2
        fill(im, (x0, y, x0 + wd // 4, y), RED[2])
        fill(im, (x0 + wd - (wd // 5 + 1), y, x0 + wd - 1, y), RED[0])
        if i % 3 == 2:                          # a rib
            fill(im, (x0 + 1, y, x0 + wd - 2, y), RED[0])
            fill(im, (x0 + 1, y, x0 + wd // 4, y), RED[1])
    for x, y in ((9, 40), (9, 41), (10, 39)):
        dot(im, x, y, RED[3])
    for y in (34, 52):                          # the rings top and bottom
        fill(im, (11, y, 21, y + 2), NIGHT[2])
        fill(im, (11, y, 21, y), NIGHT[4])
        fill(im, (20, y, 21, y + 2), NIGHT[1])
    fill(im, (15, 55, 17, 57), GOLD[1])         # the tassel's knob
    dot(im, 15, 55, GOLD[2])
    hl.outline(im)
    fill(im, (16, 0, 16, 33), INK)              # the cord: one pixel, not an outlined bar
    fill(im, (15, 0, 15, 32), hl.CLEAR)
    fill(im, (17, 0, 17, 32), hl.CLEAR)
    return im


def cask(im, y):
    rows(im, 31, y, (22, 24) + (26,) * 23 + (24, 22), GOLD[2])
    for i, w in enumerate((22, 24) + (26,) * 23 + (24, 22)):
        x0 = (31 - w + 1) // 2
        fill(im, (x0, y + i, x0 + 1, y + i), GOLD[3])
        fill(im, (x0 + w - 3, y + i, x0 + w - 1, y + i), GOLD[1])
    fill(im, (4, y, 27, y), GOLD[3])
    for ry in (y + 4, y + 22):                  # the ropes
        fill(im, (3, ry, 28, ry + 1), W[2])
        fill(im, (3, ry, 28, ry), W[4])
        for x in range(4, 29, 3):
            dot(im, x, ry + 1, W[0])
    fill(im, (8, y + 7, 23, y + 20), P[3])      # the brand
    fill(im, (8, y + 20, 23, y + 20), P[1])
    fill(im, (23, y + 7, 23, y + 20), P[2])
    hl.text(im, 10, y + 8, '酒', RED[1])
    fill(im, (3, y + 25, 28, y + 26), GOLD[0])


def casks():
    im = hl.canvas(32, 64)
    cask(im, 34)
    cask(im, 6)
    hl.outline(im)
    return im


SPRITES = {
    'floor-a': boards(286, 0), 'floor-b': boards(287, 1),
    'side-w': side_w, 'side-e': side_e, 'wall-front': wall_front,
    'threshold-w': threshold_w, 'threshold-e': threshold_e,
    'wall': wall, 'wall-menu': wall_menu, 'wall-clock': wall_clock,
    'backbar': backbar, 'bar': bar, 'table': table, 'chochin': chochin, 'casks': casks,
}

# the lantern's night glow, in cells from its top-left (Glows.js); a key with -lanterns or lamp-post would get none
GLOW = {'izakaya-in-chochin_0_0': [{'x': 0.5, 'y': 1.4, 'r': 1.3, 'color': 0xff8a5a, 'a': 0.5}]}


def main(argv):
    built = {}
    for name, draw in SPRITES.items():
        key = f'izakaya-in-{name}_0_0'
        im = hl.double(draw())
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width // 64}x{im.height // 64} cells')
    art_register.register(built, GLOW)
    if '--sheet' in argv:
        out = argv[argv.index('--sheet') + 1]
        hl.sheet(list(built.values()), out)
        print(f'contact sheet -> {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
