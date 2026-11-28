#!/usr/bin/env python3
"""generate_karuizawa_art.py — draw Karuizawa's sprites (issues #68, #256).

Karuizawa is the fifth district of the stitched `TokyoCity`, out of Tokyo's
west gate (tools/generate_karuizawa.py). No asset pack has its art, so it is
drawn here the way tools/generate_hokuriku_art.py draws Hokuriku: shaded pixel
art in the GuttyKreum palette, at half size and pixel-doubled, with a 1px ink
outline.

  karuizawa-fingerpost_0_0     1x2  the fingerpost inside the gate: a wooden
                                    post on a stone foot, one cream arm pointing
                                    east (Tokyo), one west (up the road)
  karuizawa-larch_0_0          2x3  a larch in November: a narrow cone of
                                    drooping gold boughs on a straight bare
                                    trunk, needles on the ground
  karuizawa-larch_0_1          2x4  the same tree a row taller
  karuizawa-falls_0_0          8x3  Shiraito Falls: a low, wide, mossy rock wall
                                    curved round its pool, hundreds of white
                                    threads coming out of a seam in the face (not
                                    over the top), foam at the foot. The end cells
                                    of its bottom row are rock arms on the bank;
                                    between them the last rows are clear, and the
                                    pool (pond-autotile, on the Water layer) shows
  karuizawa-corn-stall_0_0     3x2  the roadside corn stand by the bus stop: an
                                    indigo striped awning on two posts, cobs on a
                                    charcoal grill, a basket of corn in the husk,
                                    the counter to the south

Kyu-Karuizawa Ginza's three shopfronts (issue #261, part 2 of #256), each 3x4
with its door in the middle cell of its bottom row (roomgen.SHOP_DOORS) and
its lit window and door in GLOW, the night glow spots written to its
spriteMetadata (src/utils/Glows.js). Autumn, no snow; the lettering is too
small to read:

  karuizawa-shop-bakery_0_0    3x4  the tiny boulangerie: cream plaster and
                                    dark half-timbering under a steep red-brown
                                    gable, a lit window of loaves and an apple
                                    pie, a board with a loaf on it
  karuizawa-shop-jam_0_0       3x4  the jam and souvenir shop: white clapboard
                                    under a green roof with a dormer, two lit
                                    windows of red, purple and orange jars, a
                                    board with a jar on it
  karuizawa-shop-lounge_0_0    3x4  the cocktail lounge: dark timber over a
                                    stone dado under a low slate gable, a small
                                    amber window with bottles, a brass lantern
                                    by the door, a board with a cocktail glass

And, at the head of the road (issue #262, part 3): the larches (a 2x3 and a 2x4),
Shiraito Falls (8x3) and the corn stall (3x2). Nothing here is lettered but the
shopfronts' boards: the falls and the stall need no font.

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE generate_karuizawa.py:
    python3 tools/generate_karuizawa_art.py [--preview out.png]
"""
import json
import math
import random
import sys
from PIL import Image

from generate_hokkaido import (C, rgb, canvas, outline, tiles, INK, AMBER, GREEN_HI, SNOW_LO,
                               CREAM, CREAM_LO, CREAM_DK, WHITE, WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               RED, RED_HI, RED_LO, RED_DK, GLASS_DK, NAVY, GOLD)
from generate_sendai_art import blob, BARK, BARK_LO
# the Ginza's own colours, beside the GuttyKreum palette
LIT, LIT_HI, LIT_LO = rgb('f6dc8c'), rgb('fff4d6'), rgb('d9a650')            # a lamplit window
PLASTER, PLASTER_LO = rgb('f1e3cb'), rgb('d3bfa3')
TIMBER, TIMBER_HI, TIMBER_LO = rgb('6b4a3c'), rgb('8a6350'), rgb('4b342c')   # half-timbering, the lounge's boards
BRICK, BRICK_LO = rgb('b8614a'), rgb('8f4636')
CRUST, CRUST_HI, CRUST_LO = rgb('c98a4b'), rgb('f0c98a'), rgb('a3683a')      # bread
MOSS, MOSS_HI, MOSS_LO = rgb('4f7a5c'), rgb('76a07a'), rgb('38584a')         # the jam shop's roof and paint
BOARD, BOARD_LO = rgb('f6f3ee'), rgb('cfc9c4')                               # white clapboard
JAMS = (rgb('c5423c'), rgb('7d4a94'), rgb('e58f35'))                         # strawberry, blueberry, apricot
DUSK, DUSK_LO, DUSK_HI = rgb('54392f'), rgb('3d2a25'), rgb('6c4b3d')         # the lounge's dark boards
OXBLOOD, OXBLOOD_LO, OXBLOOD_HI = rgb('7d362c'), rgb('5e261f'), rgb('9a4a3c')
AMBERS = (rgb('f0a843'), rgb('ffd27a'), rgb('c47e2c'))                       # the lounge's window: lit, bright, dim
SLATE, SLATE_HI, SLATE_LO = rgb('56576e'), STONE_LO, GLASS_DK
LEAVES = (rgb('d9772f'), rgb('b8452f'), rgb('e0b04a'))                       # fallen maple and larch
# the falls' and the larches' own colours
LARCH, LARCH_HI, LARCH_LO, LARCH_DK = rgb('d9a441'), rgb('f2cf6b'), rgb('a8742f'), rgb('7d5327')   # November gold
WATER_HI = rgb('8ec2fa')                # pond-autotile's own highlight
RMOSS, RMOSS_HI, RMOSS_LO, RMOSS_DK = rgb('4f8250'), rgb('6a9c59'), rgb('447549'), rgb('35603f')
ROCK, ROCK_HI, ROCK_LO, ROCK_DK, ROCK_WET = rgb('848295'), rgb('a9aeb2'), rgb('5f6078'), rgb('47485d'), rgb('30324a')
INDIGO, INDIGO_LO = rgb('3a4f86'), rgb('2c3d6a')
SHADOW = rgb('3a5f66', 150)             # the ground shadow every tree here stands in


def fingerpost():
    im, d = canvas(1, 2)                 # 32 x 64; it stands on the lower cell
    d.rectangle([14, 6, 17, 60], fill=WOOD); d.line([(17, 6), (17, 60)], fill=WOOD_LO)
    d.rectangle([13, 4, 18, 6], fill=WOOD_LO); d.line([(13, 4), (18, 4)], fill=WOOD)     # the cap
    d.rectangle([11, 59, 20, 62], fill=STONE_LO); d.line([(11, 59), (20, 59)], fill=STONE)
    # the arms: a board with a pointed end, a line of lettering, its lower edge in shadow
    for y, tip, back in ((10, 29, 9), (21, 2, 22)):         # east (Tokyo) above, west (the road) below
        x0, x1 = sorted((back, tip + (-4 if tip > back else 4)))
        d.rectangle([x0, y, x1, y + 7], fill=CREAM)
        d.polygon([(tip, y + 3), (tip, y + 4), (x1 if tip > back else x0, y + 7),
                   (x1 if tip > back else x0, y)], fill=CREAM)
        d.line([(x0, y), (x1, y)], fill=WHITE)
        d.line([(x0, y + 7), (x1, y + 7)], fill=CREAM_LO)
        for x in range(x0 + 2, x1 - 1, 2):                  # the name, too small to read
            d.point((x, y + 3), fill=WOOD_DK); d.point((x, y + 4), fill=CREAM_DK)
        d.point((15, y + 2), fill=WOOD_DK); d.point((16, y + 5), fill=WOOD_DK)           # the nails
    outline(im)
    return im


def larch(rows):
    """A larch in November, `rows` cells tall: tiers of drooping boughs, narrow
    at the leader and widest low down, on a straight trunk that is bare in the
    bottom cell. Lit from the upper left."""
    def build():
        im, d = canvas(2, rows)
        h = rows * C
        d.ellipse([17, h - 11, 47, h - 3], fill=SHADOW)
        d.rectangle([30, 12, 33, h - 6], fill=BARK)
        d.line([(33, 12), (33, h - 6)], fill=BARK_LO)
        d.line([(28, h - 6), (35, h - 6)], fill=BARK_LO)                 # the root flare
        tiers = 3 * rows - 2                                              # 7 or 10
        step = (h - 44) / (tiers - 1)
        for i in reversed(range(tiers)):                                  # the lowest first: each tier hangs over the one below
            y0 = 8 + round(i * step)
            w = 6 + round(i * (18 if rows == 3 else 20) / (tiers - 1)) + (i * 5 % 3 - 1)   # how far the bough reaches
            for dx in range(w + 1):
                t = dx / w
                top = y0 + round(5 * t ** 1.5) - (dx == w)                # it droops, and lifts again at the very tip
                thick = max(2, round(8 - 5 * t)) + ((dx * 3 + i) % 4 == 0)   # a fringe of needles
                for side in (-1, 1):
                    x = 32 + side * dx - (side < 0)
                    for n in range(thick):
                        if side < 0:
                            c = LARCH_HI if n < 2 else LARCH if n < thick - 1 else LARCH_LO
                        elif dx < w // 3:                                      # the light comes a little way round the trunk
                            c = LARCH_HI if n < 1 else LARCH if n < thick - 2 else LARCH_LO
                        else:
                            c = LARCH if n < 2 else LARCH_LO if n < thick - 1 else LARCH_DK
                        if (dx * 5 + n * 3 + i) % 9 == 0 and 0 < n < thick - 1:
                            c = LARCH_LO if side < 0 else LARCH                # the needles are not one flat colour
                        d.point((x, top + n), fill=c)
            if i < tiers - 1:
                for x in range(32 - w + 3, 32 + w - 3):                   # the shade it throws on the tier below
                    d.point((x, y0 + 8 + round(3 * (abs(x - 31.5) / w) ** 1.5)), fill=LARCH_DK)
        d.rectangle([31, 1, 32, 9], fill=LARCH_HI)                        # the leader
        d.line([(32, 3), (32, 9)], fill=LARCH)
        for x, y in ((12, h - 5), (20, h - 2), (26, h - 8), (40, h - 3), (45, h - 7), (52, h - 4), (37, h - 9)):
            d.point((x, y), fill=LARCH if x % 3 else LARCH_HI)            # fallen needles
        outline(im)
        return im
    return build


def falls():
    """Shiraito Falls, 8x3: the wall is drawn as a shallow horseshoe (its middle
    further off, so higher up the picture, its two ends coming forward as rock
    arms). The water comes out of a seam part-way down the face, not over the
    top. Under the six middle cells the picture stops short of its bottom edge:
    the pool lies there, on the Water layer."""
    im, d = canvas(8, 3)
    W = 8 * C
    rnd = random.Random(262)
    bow = lambda x: ((x - (W - 1) / 2) / ((W - 1) / 2)) ** 2             # 0 in the middle, 1 at either end
    top = lambda x: 9 + round(8 * bow(x))                                # the wall's top edge
    foot = lambda x: 74 + round(6 * bow(x))                              # the foot of the face, behind the foam
    seam = lambda x: top(x) + 19 + round(1.5 * math.sin(x / 9)) + (x % 23 == 0)
    A, B = C + 3, W - C - 4                                              # the curtain: x = A..B

    # ---- the face: banded rock, darker and wet below the seam -----------------------
    for x in range(2, W - 2):
        for y in range(top(x), foot(x) + 1):
            band = (y - top(x) + round(2 * math.sin(x / 17))) // 5
            c = (ROCK, ROCK_LO)[band % 2]
            if (x * 7 + y * 13) % 11 == 0:
                c = ROCK_LO if c == ROCK else ROCK_DK
            if A - 2 <= x <= B + 2 and y >= seam(x):
                c = ROCK_WET if (x + y // 3) % 5 else ROCK_DK
            d.point((x, y), fill=c)
        if A - 2 <= x <= B + 2:
            d.point((x, seam(x) - 2), fill=ROCK_HI)                       # the lip the water comes out under
            d.point((x, seam(x) - 1), fill=ROCK_DK)
    # ---- the arms: boulders either side, down to the bank ------------------------------
    for side in (0, 1):
        m = (lambda x: W - 1 - x) if side else (lambda x: x)
        for x0, y0, x1, y1 in ((1, 40, 30, 82), (4, 62, 37, 94), (0, 70, 20, 93)):
            l, r = sorted((m(x0), m(x1)))
            d.ellipse([l, y0, r, y1], fill=ROCK_LO)
            d.ellipse([l + 1, y0, r - 4, y1 - 6], fill=ROCK)              # lit from the upper left, both sides
            d.chord([l, y0, r, y1], 25, 155, fill=ROCK_DK)
            d.line([(l + 5, y0 + 5), (l + 12, y0 + 3)], fill=ROCK_HI)
        d.line([(m(22), 66), (m(30), 70)], fill=ROCK_DK)                  # a crack between the boulders
        blob(d, m(15), 46, 11, 5, RMOSS, RMOSS_HI, RMOSS_LO, 3 + side)       # moss on its shoulder
    # ---- moss and ferns along the top, hanging a little way down the face --------------
    for x in range(2, W - 2):
        hang = 6 + (x * 5 % 7) // 2 + (3 if x % 13 < 3 else 0)
        up = 2 + (x * 3 % 5 > 2) + (2 if x % 9 == 4 else 0)               # tufts above the edge
        for y in range(top(x) - up, top(x) + hang):
            n = y - top(x)
            c = RMOSS_HI if n < -1 else RMOSS if n < 3 else RMOSS_LO if n < hang - 1 else RMOSS_DK
            if (x * 11 + y * 5) % 13 == 0:
                c = RMOSS_HI if n < 2 else RMOSS_DK
            d.point((x, y), fill=c)
    for x in (20, 58, 97, 141, 176, 215, 238):                            # larch needles blown onto it
        d.point((x, top(x) + 1), fill=LARCH); d.point((x + 3, top(x) - 1), fill=LARCH_HI)
    outline(im)
    # ---- the threads: drawn after the outline, so no ink runs along the foam -----------
    run = 0
    for x in range(A, B + 1):
        r = rnd.random()
        end = foot(x) + rnd.randint(0, 2)
        if r < 0.66 and run < 2 and x % 31 > 2:                           # thin: never three abreast, and a few bare ribs of rock
            run += 1
            y0 = seam(x) + rnd.choice((0, 0, 0, 1, 2, 6, 11))            # most from the seam, some from lower cracks
            c = WHITE if r < 0.36 else SNOW_LO if r < 0.54 else WATER_HI
            d.line([(x, y0), (x, end)], fill=c)
            if r < 0.1:                                                   # a thread broken on a ledge
                d.line([(x, y0 + 14), (x, y0 + 16)], fill=ROCK_WET)
        else:
            run = 0
            for y in range(foot(x) - 14, end + 1):                        # spray between the threads, thicker lower down
                if rnd.random() < (y - foot(x) + 15) / 22:
                    d.point((x, y), fill=SNOW_LO if (x + y) % 3 else WATER_HI)
    for x in range(A - 2, B + 3):                                         # foam where they land, and the mist over it
        t = min(x - (A - 2), B + 2 - x)
        y0 = foot(x) - (2 if t > 2 else 0) - rnd.randint(0, 2)
        y1 = foot(x) + 5 + rnd.randint(0, 2) - (2 if t < 2 else 0)
        for y in range(y0, y1 + 1):
            c = WHITE if y < y1 - 1 else SNOW_LO if y < y1 else WATER_HI
            if (x + y * 3) % 7 == 0 and y > y0:
                c = SNOW_LO
            d.point((x, y), fill=c)
        if rnd.random() < 0.3:
            d.point((x, y0 - 2 - rnd.randint(0, 5)), fill=WHITE)
        if rnd.random() < 0.25:                                           # a ripple going out over the pool
            d.point((x, y1 + 2 + rnd.randint(0, 2)), fill=WATER_HI)
    return im


def corn_stall():
    """The roadside stand, 3x2: its counter is the lower cell, bumped from the south."""
    im, d = canvas(3, 2)                 # 96 x 64
    # ---- inside: the back cloth in shadow --------------------------------------------
    d.rectangle([7, 18, 88, 40], fill=rgb('3b2f33'))
    d.rectangle([7, 18, 88, 22], fill=rgb('2b2228'))
    # ---- the awning: a lean-to of striped canvas, a scalloped valance -----------------
    for y in range(2, 17):
        x0, x1 = 6 - (y - 2) // 4, 89 + (y - 2) // 4
        for x in range(x0, x1 + 1):
            band = ((x - 3) // 6) % 2
            c = (CREAM, INDIGO)[band]
            if y < 4:
                c = (WHITE, rgb('4b6396'))[band]                          # the ridge pole catches the light
            if y > 13:
                c = (CREAM_LO, INDIGO_LO)[band]
            d.point((x, y), fill=c)
    for x in range(2, 94):
        band = ((x - 3) // 6) % 2
        d.line([(x, 17), (x, 20 + ((x - 3) % 6 in (2, 3)) - ((x - 3) % 6 in (0, 5)))], fill=(CREAM, INDIGO)[band])
    d.line([(2, 17), (93, 17)], fill=INK)                                 # the fold where the valance hangs
    for x in (5, 89):                                                     # the posts
        d.rectangle([x, 21, x + 1, 60], fill=WOOD)
        d.line([(x + 1, 21), (x + 1, 60)], fill=WOOD_LO)
    # ---- the counter -------------------------------------------------------------------
    d.rectangle([3, 39, 92, 42], fill=WOOD); d.line([(3, 39), (92, 39)], fill=rgb('d7a88c'))
    d.rectangle([4, 43, 91, 60], fill=WOOD_LO); d.line([(4, 43), (91, 43)], fill=WOOD_DK)
    for x in range(4, 92, 11):
        d.line([(x, 44), (x, 60)], fill=WOOD_DK)                          # its boards
    d.line([(4, 60), (91, 60)], fill=WOOD_DK)
    d.rectangle([3, 61, 92, 62], fill=SHADOW)
    d.rectangle([41, 46, 54, 56], fill=CREAM); d.line([(41, 56), (54, 56)], fill=CREAM_LO)      # the price card: a cob, no words
    d.rectangle([44, 50, 50, 52], fill=AMBER); d.line([(44, 50), (50, 50)], fill=rgb('fde38a'))
    d.line([(51, 49), (52, 48)], fill=RMOSS_HI); d.line([(51, 53), (52, 54)], fill=RMOSS_HI)
    d.point((47, 44), fill=WOOD_DK)                                       # its pin
    # ---- the charcoal grill, cobs turning on it ------------------------------------------
    d.rectangle([13, 31, 52, 38], fill=STONE_DK); d.line([(13, 31), (52, 31)], fill=STONE_LO)
    d.rectangle([12, 30, 53, 30], fill=STONE)
    for x in range(15, 52, 2):
        d.point((x, 37), fill=rgb('e78d7b') if (x // 2) % 3 else AMBER)   # the coals, through the vents
    for k, x in enumerate(range(16, 46, 12)):
        y = 26 + (k == 1)
        d.rectangle([x + 1, y, x + 8, y + 3], fill=AMBER)                 # a cob: rounded ends, rows of kernels
        d.line([(x, y + 1), (x, y + 2)], fill=AMBER); d.line([(x + 9, y + 1), (x + 9, y + 2)], fill=rgb('c98f1c'))
        d.line([(x + 1, y), (x + 8, y)], fill=rgb('fde38a'))
        d.line([(x + 1, y + 3), (x + 8, y + 3)], fill=rgb('c98f1c'))
        for kx in range(x + 2, x + 9, 2):
            d.point((kx, y + 1), fill=rgb('fde38a')); d.point((kx - 1, y + 2), fill=rgb('e0a526'))
        d.point((x + 3 + k, y + 2), fill=rgb('8a5a1e')); d.point((x + 6, y + 1), fill=rgb('8a5a1e'))   # where the soy has caught
        d.line([(x - 3, y + 2), (x - 1, y + 2)], fill=CREAM)              # the stick
    for sx, sy in ((19, 22), (20, 20), (30, 23), (31, 21), (41, 22), (40, 19)):
        d.point((sx, sy), fill=STONE_LO if sy % 2 else CREAM_DK)          # smoke
    # ---- a basket of corn in the husk, and a brush in its pot of soy ---------------------
    d.rectangle([64, 31, 84, 38], fill=rgb('b98a55'))
    for x in range(64, 85, 3):
        d.line([(x, 31), (x, 38)], fill=rgb('8e6537'))
    d.line([(64, 34), (84, 34)], fill=rgb('8e6537')); d.line([(63, 30), (85, 30)], fill=rgb('d8b07a'))
    for k, x in enumerate((65, 70, 75, 80)):                              # cobs stood in it, husks peeled back off the tip
        y = 22 + (k * 2) % 3
        d.rectangle([x, y + 3, x + 3, 29], fill=GREEN_HI)
        d.line([(x + 3, y + 3), (x + 3, 29)], fill=RMOSS_HI); d.line([(x, y + 4), (x, 29)], fill=rgb('a9cc8e'))
        d.rectangle([x + 1, y, x + 2, y + 3], fill=AMBER); d.point((x + 1, y), fill=rgb('fde38a'))
        d.point((x - 1, y + 2), fill=GREEN_HI); d.point((x + 4, y + 2), fill=RMOSS_HI)                # the husk, opened
    d.rectangle([55, 33, 59, 38], fill=rgb('5a3b34')); d.line([(55, 33), (59, 33)], fill=rgb('2b2228'))
    d.line([(58, 32), (60, 27)], fill=CREAM)
    outline(im)
    return im


def gable(d, apex, eave, half, thick, hi, mid, lo, step=5):
    """The roof of a front gable as it is seen from the street: a band `thick`
    deep down each slope from the apex (y, on the centre line) to the eaves
    (y, `half` columns out), lit along its top and shaded along its foot."""
    for x in range(48 - half, 48 + half):
        out = abs(x - 47.5)
        y = apex + round((eave - apex) * out / half)
        d.line([(x, y), (x, y + thick - 1)], fill=lo if int(out) % step == step - 1 else mid)
        d.point((x, y), fill=hi)
        d.point((x, y + thick - 1), fill=lo)


def lettering(d, x0, x1, y, ink, soft):
    """A line of a name, too small to read."""
    for x in range(x0, x1 + 1):
        if (x - x0) % 4 != 3:
            d.point((x, y + (x * 7) % 2), fill=ink); d.point((x, y + 2), fill=soft if (x * 5) % 3 else ink)


def loaf(d, x0, y0, x1, y1, crust=CRUST):
    d.ellipse([x0, y0, x1, y1], fill=crust)
    d.chord([x0, y0, x1, y1], 20, 160, fill=CRUST_LO)
    for x in range(x0 + 2, x1 - 1, 3):
        d.line([(x + 1, y0 + 1), (x, y0 + 2)], fill=CRUST_HI)


def stone_course(d, x0, y0, x1, y1, rows=7, bond=10):
    """Dressed stone: a lit top edge, courses `rows` deep with staggered joints."""
    d.rectangle([x0, y0, x1, y1], fill=STONE_LO)
    d.line([(x0, y0), (x1, y0)], fill=STONE)
    for n, y in enumerate(range(y0 + rows, y1 + 1, rows)):
        d.line([(x0, y), (x1, y)], fill=STONE_DK)
    for n, y in enumerate(range(y0, y1 + 1, rows)):
        for x in range(x0 + 3 + (n % 2) * (bond // 2), x1, bond):
            d.line([(x, y + 1), (x, min(y1, y + rows - 1))], fill=STONE_DK)
            if x + 1 <= x1:
                d.point((x + 1, y + 1), fill=STONE)


def fallen(d, cells):
    """Autumn: a few fallen leaves, one pixel each."""
    for n, (x, y) in enumerate(cells):
        d.point((x, y), fill=LEAVES[n % 3])


def step(d, x0, x1):
    """The door's stone step, on the sprite's bottom edge."""
    d.rectangle([x0, 124, x1, 126], fill=STONE_LO)
    d.line([(x0, 124), (x1, 124)], fill=STONE)


def shop_bakery():
    """The tiny boulangerie: a half-timbered front gable, steep and red-brown."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is cell (1, 3)
    # the chimney, behind the east slope
    d.rectangle([65, 9, 74, 38], fill=BRICK)
    for y in range(11, 38, 3):
        d.line([(65, y), (74, y)], fill=BRICK_LO)
    d.rectangle([73, 9, 74, 38], fill=BRICK_LO)
    d.rectangle([63, 6, 76, 8], fill=STONE_LO); d.line([(63, 6), (76, 6)], fill=STONE)
    # the wall: plaster up into the gable
    d.polygon([(11, 126), (11, 50), (47, 12), (48, 12), (84, 50), (84, 126)], fill=PLASTER)
    d.rectangle([79, 58, 81, 119], fill=PLASTER_LO)                       # the shaded end
    gable(d, 5, 55, 45, 7, RED_HI, RED_LO, rgb('6f3527'))
    # the timbers of the gable: king post, collar, two struts, the tie beam
    d.rectangle([47, 13, 48, 53], fill=TIMBER)
    d.rectangle([27, 37, 68, 38], fill=TIMBER); d.line([(27, 39), (68, 39)], fill=PLASTER_LO)
    for a, b in (((22, 53), (36, 40)), ((73, 53), (59, 40))):
        d.line([a, b], fill=TIMBER, width=2)
    d.ellipse([44, 22, 51, 29], fill=TIMBER); d.ellipse([45, 23, 50, 28], fill=GLASS_DK)      # the vent in the peak
    d.point((46, 24), fill=STONE_LO)
    # the attic window between the struts
    d.rectangle([40, 41, 55, 53], fill=TIMBER)
    d.rectangle([42, 43, 53, 52], fill=LIT); d.line([(42, 43), (53, 43)], fill=LIT_HI)
    d.line([(47, 43), (47, 52)], fill=TIMBER); d.line([(48, 43), (48, 52)], fill=TIMBER)
    d.rectangle([9, 54, 86, 57], fill=TIMBER); d.line([(9, 54), (86, 54)], fill=TIMBER_HI)
    d.line([(11, 58), (84, 58)], fill=PLASTER_LO)
    # the ground floor's frame: corner posts, the posts of the door, a rail over the heads
    for x in (11, 35, 58, 82):
        d.rectangle([x, 58, x + 2, 123], fill=TIMBER); d.line([(x, 58), (x, 123)], fill=TIMBER_HI)
    d.rectangle([11, 74, 84, 76], fill=TIMBER); d.line([(11, 74), (84, 74)], fill=TIMBER_HI)
    # the board: a loaf, and the name
    d.rectangle([17, 60, 78, 71], fill=WOOD_LO)
    d.rectangle([18, 61, 77, 70], fill=CREAM); d.line([(18, 70), (77, 70)], fill=CREAM_LO)
    loaf(d, 22, 62, 34, 69)
    lettering(d, 40, 72, 64, TIMBER_LO, CREAM_DK)
    # the window: loaves on the upper shelf, an apple pie and a roll below
    d.rectangle([15, 79, 33, 108], fill=TIMBER_LO)
    d.rectangle([17, 81, 31, 106], fill=LIT); d.line([(17, 81), (31, 81)], fill=LIT_HI)
    for y in (93, 105):
        d.line([(17, y), (31, y)], fill=WOOD_LO)
    loaf(d, 18, 86, 24, 92); loaf(d, 25, 87, 30, 92, rgb('dba862'))
    d.ellipse([18, 99, 27, 104], fill=rgb('dba862')); d.arc([18, 99, 27, 104], 0, 180, fill=CRUST_LO)      # the pie
    for x, y in ((20, 101), (22, 100), (24, 101), (22, 102), (25, 100)):
        d.point((x, y), fill=RED_LO)
    d.line([(20, 99), (25, 99)], fill=CRUST_HI)
    d.ellipse([28, 101, 31, 104], fill=CRUST)
    # the flower box under it: autumn chrysanthemums
    d.rectangle([14, 111, 34, 115], fill=WOOD_LO); d.line([(14, 111), (34, 111)], fill=WOOD)
    for n, x in enumerate(range(15, 34, 2)):
        d.point((x, 110 - n % 2), fill=LEAVES[n % 3]); d.point((x + 1, 110), fill=MOSS)
    # the plinth
    d.rectangle([11, 120, 84, 126], fill=STONE_LO); d.line([(11, 120), (84, 120)], fill=STONE)
    for x in range(16, 84, 9):
        d.line([(x, 122), (x, 126)], fill=STONE_DK)
    # the door (cell 1, 3): boards under a glazed half
    d.rectangle([38, 77, 57, 126], fill=TIMBER_LO)
    d.rectangle([40, 79, 55, 126], fill=WOOD); d.line([(40, 79), (40, 126)], fill=rgb('d3a48c'))
    for x in (45, 50):
        d.line([(x, 101), (x, 126)], fill=WOOD_LO)
    d.rectangle([42, 82, 53, 98], fill=TIMBER_LO)
    d.rectangle([43, 83, 52, 97], fill=LIT); d.line([(43, 83), (52, 83)], fill=LIT_HI)
    d.line([(43, 90), (52, 90)], fill=TIMBER_LO); d.line([(47, 83), (47, 97)], fill=TIMBER_LO)
    d.rectangle([53, 103, 54, 107], fill=GOLD)
    step(d, 36, 59)
    # the east bay: a small window, and the chalkboard on the step
    d.rectangle([63, 79, 79, 96], fill=TIMBER_LO)
    d.rectangle([65, 81, 77, 94], fill=LIT); d.line([(65, 81), (77, 81)], fill=LIT_HI)
    d.line([(71, 81), (71, 94)], fill=TIMBER_LO); d.line([(65, 87), (77, 87)], fill=TIMBER_LO)
    d.polygon([(63, 126), (66, 103), (78, 103), (81, 126)], fill=WOOD_LO)
    d.rectangle([67, 105, 77, 120], fill=rgb('2f3b36'))
    loaf(d, 68, 107, 76, 112, rgb('dba862'))
    for n, y in enumerate((115, 118)):
        d.line([(69, y), (75 - n * 2, y)], fill=rgb('c9d6c8'))
    fallen(d, [(20, 43), (9, 51), (70, 33), (88, 52), (30, 28)])
    outline(im)
    return im


def jam_shelves(d, x0, y0, x1, y1, first=0):
    """A lit window of jam: three shelves of jars, a lid on each."""
    d.rectangle([x0, y0, x1, y1], fill=MOSS_LO)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=LIT)
    d.line([(x0 + 2, y0 + 2), (x1 - 2, y0 + 2)], fill=LIT_HI)
    for row, y in enumerate(range(y0 + 10, y1 - 1, 9)):
        d.line([(x0 + 2, y), (x1 - 2, y)], fill=WOOD_LO)
        for n, x in enumerate(range(x0 + 3, x1 - 4, 5)):
            jam = JAMS[(first + row + n) % 3]
            d.rectangle([x, y - 4, x + 2, y - 1], fill=jam)
            d.line([(x, y - 5), (x + 2, y - 5)], fill=WHITE if (row + n) % 2 else GOLD)
            d.point((x, y - 3), fill=LIT_HI)


def shop_jam():
    """The jam and souvenir shop: white clapboard, a wide green roof, a dormer."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is cell (1, 3)
    # the wall
    d.rectangle([7, 52, 88, 126], fill=BOARD)
    for y in range(60, 122, 3):
        d.line([(7, y), (88, y)], fill=BOARD_LO)
    d.rectangle([7, 52, 8, 126], fill=WHITE); d.rectangle([87, 52, 88, 126], fill=BOARD_LO)
    # the roof: hipped, the eaves to the street
    tiles(d, [(y, 2 + (53 - y) * 14 // 31, 93 - (53 - y) * 14 // 31) for y in range(22, 54)], MOSS, MOSS_LO)
    for y in range(22, 54):
        d.point((2 + (53 - y) * 14 // 31, y), fill=MOSS_HI)
    d.line([(16, 22), (79, 22)], fill=MOSS_HI); d.line([(16, 23), (79, 23)], fill=MOSS_HI)
    d.rectangle([1, 54, 94, 56], fill=WHITE); d.line([(1, 56), (94, 56)], fill=BOARD_LO)
    d.line([(7, 57), (88, 57)], fill=CREAM_DK)                            # the eaves' shadow
    # the dormer: a small gable of its own, a lit window in its face
    for y in range(9, 28):
        half = (y - 9) + 1
        d.line([(47 - half, y), (48 + half, y)], fill=MOSS)
        d.point((47 - half, y), fill=MOSS_HI); d.point((48 + half, y), fill=MOSS_LO)
    for y in range(15, 28):
        half = (y - 15)
        d.line([(47 - half, y), (48 + half, y)], fill=BOARD)
    d.rectangle([36, 28, 59, 45], fill=BOARD)
    for y in range(30, 45, 3):
        d.line([(36, y), (59, y)], fill=BOARD_LO)
    d.line([(58, 28), (58, 45)], fill=BOARD_LO); d.line([(59, 28), (59, 45)], fill=BOARD_LO)
    d.rectangle([41, 24, 54, 41], fill=MOSS_LO)
    d.rectangle([43, 26, 52, 39], fill=LIT); d.line([(43, 26), (52, 26)], fill=LIT_HI)
    d.line([(47, 26), (47, 39)], fill=MOSS_LO); d.line([(48, 26), (48, 39)], fill=MOSS_LO)
    d.line([(43, 32), (52, 32)], fill=MOSS_LO)
    d.line([(34, 46), (61, 46)], fill=MOSS_LO)
    # the board: a jar between two words
    d.rectangle([14, 59, 81, 72], fill=MOSS_LO)
    d.rectangle([16, 61, 79, 70], fill=rgb('f3e6c8')); d.line([(16, 70), (79, 70)], fill=CREAM_LO)
    d.rectangle([44, 64, 51, 69], fill=JAMS[0]); d.rectangle([45, 62, 50, 63], fill=GOLD)
    d.rectangle([45, 66, 50, 67], fill=WHITE); d.point((44, 64), fill=RED_HI)
    lettering(d, 20, 39, 64, MOSS_LO, MOSS)
    lettering(d, 56, 75, 64, MOSS_LO, MOSS)
    # two windows of jars
    jam_shelves(d, 9, 77, 34, 108)
    jam_shelves(d, 61, 77, 86, 108, first=1)
    # a bench under the west window, a crate of apples under the east
    d.rectangle([11, 114, 32, 116], fill=WOOD); d.line([(11, 117), (32, 117)], fill=WOOD_LO)
    for x in (12, 30):
        d.rectangle([x, 118, x + 1, 126], fill=WOOD_LO)
    d.rectangle([13, 109, 18, 113], fill=JAMS[2]); d.line([(13, 108), (18, 108)], fill=GOLD)      # a big jar on it
    d.rectangle([14, 110, 17, 111], fill=WHITE)
    d.rectangle([64, 114, 84, 126], fill=WOOD)
    for y in (117, 121, 125):
        d.line([(64, y), (84, y)], fill=WOOD_LO)
    d.line([(64, 114), (64, 126)], fill=WOOD_LO); d.line([(84, 114), (84, 126)], fill=WOOD_LO)
    for n, x in enumerate(range(65, 82, 4)):
        d.ellipse([x, 110 + n % 2, x + 3, 113 + n % 2], fill=RED if n % 3 else rgb('c5423c'))
        d.point((x + 1, 111 + n % 2), fill=RED_HI)
    # the door (cell 1, 3): green, glazed above, a panel below
    d.rectangle([37, 76, 58, 126], fill=WHITE); d.line([(58, 76), (58, 126)], fill=BOARD_LO)
    d.rectangle([39, 78, 56, 126], fill=MOSS); d.line([(39, 78), (39, 126)], fill=MOSS_HI)
    d.rectangle([42, 81, 53, 100], fill=MOSS_LO)
    d.rectangle([43, 82, 52, 99], fill=LIT); d.line([(43, 82), (52, 82)], fill=LIT_HI)
    d.line([(47, 82), (47, 99)], fill=MOSS_LO); d.line([(48, 82), (48, 99)], fill=MOSS_LO)
    d.line([(43, 90), (52, 90)], fill=MOSS_LO)
    d.rectangle([42, 105, 53, 120], outline=MOSS_LO)
    d.rectangle([54, 101, 55, 105], fill=GOLD)
    step(d, 35, 60)
    fallen(d, [(24, 30), (70, 36), (12, 47), (83, 49), (60, 25)])
    outline(im)
    return im


def shop_lounge():
    """The cocktail lounge: dark boards over a stone dado, a low slate gable."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is cell (1, 3)
    # the stone chimney, up through the west slope
    stone_course(d, 14, 8, 25, 44, rows=5, bond=6)
    d.rectangle([12, 5, 27, 7], fill=STONE); d.line([(12, 7), (27, 7)], fill=STONE_DK)
    # the wall: upright boards
    d.polygon([(8, 126), (8, 38), (47, 23), (48, 23), (87, 38), (87, 126)], fill=DUSK)
    for x in range(12, 85, 4):
        d.line([(x, 24 + round(abs(x - 47.5) * 15 / 39.5)), (x, 104)], fill=DUSK_LO)
    d.line([(8, 38), (8, 104)], fill=DUSK_HI); d.rectangle([85, 38, 87, 104], fill=DUSK_LO)
    gable(d, 16, 34, 46, 7, SLATE_HI, SLATE, SLATE_LO, step=6)
    # the round window in the peak, the name board under it
    d.ellipse([42, 27, 53, 38], fill=TIMBER_HI); d.ellipse([44, 29, 51, 36], fill=AMBERS[2])
    d.line([(47, 29), (47, 36)], fill=TIMBER_HI); d.line([(48, 29), (48, 36)], fill=TIMBER_HI)
    d.line([(44, 32), (51, 32)], fill=TIMBER_HI); d.point((45, 30), fill=AMBERS[1])
    d.rectangle([22, 44, 73, 55], fill=GOLD)
    d.rectangle([23, 45, 72, 54], fill=rgb('25302c'))
    lettering(d, 28, 67, 48, GOLD, rgb('8a7440'))
    # the stone dado
    stone_course(d, 6, 104, 89, 126)
    # the window: bottles against the light
    d.rectangle([11, 68, 31, 94], fill=TIMBER_HI); d.line([(10, 95), (32, 95)], fill=TIMBER_HI)
    d.line([(10, 96), (32, 96)], fill=DUSK_LO)
    d.rectangle([13, 70, 29, 92], fill=AMBERS[0]); d.line([(13, 70), (29, 70)], fill=AMBERS[1])
    d.rectangle([13, 89, 29, 92], fill=AMBERS[2]); d.line([(13, 88), (29, 88)], fill=TIMBER_LO)
    for n, x in enumerate((14, 19, 24)):
        glass, tall = ((rgb('2f4a3a'), 12), (rgb('5a2f22'), 9), (rgb('1f2a3a'), 11))[n]
        d.rectangle([x, 88 - tall + 4, x + 2, 87], fill=glass)                  # the body
        d.line([(x + 1, 88 - tall), (x + 1, 88 - tall + 3)], fill=glass)        # the neck
        d.line([(x, 84), (x + 2, 84)], fill=CREAM)                              # the label
        d.point((x, 88 - tall + 5), fill=AMBERS[1])
    # the door (cell 1, 3): oxblood, a small lit pane, brass on it
    d.rectangle([37, 66, 58, 126], fill=TIMBER_HI); d.line([(37, 66), (58, 66)], fill=rgb('a67c62'))
    d.rectangle([39, 68, 56, 126], fill=OXBLOOD); d.line([(39, 68), (39, 126)], fill=OXBLOOD_HI)
    d.rectangle([43, 72, 52, 82], fill=OXBLOOD_LO)
    d.rectangle([44, 73, 51, 81], fill=AMBERS[0]); d.line([(44, 73), (51, 73)], fill=AMBERS[1])
    d.line([(47, 73), (47, 81)], fill=OXBLOOD_LO); d.line([(48, 73), (48, 81)], fill=OXBLOOD_LO)
    d.rectangle([42, 87, 53, 103], outline=OXBLOOD_LO); d.rectangle([42, 107, 53, 119], outline=OXBLOOD_LO)
    d.rectangle([40, 122, 55, 123], fill=GOLD)
    d.rectangle([53, 94, 54, 99], fill=GOLD)
    step(d, 35, 60)
    # the brass lantern by the door
    d.line([(60, 72), (64, 72)], fill=GOLD); d.line([(64, 72), (64, 74)], fill=GOLD)
    d.rectangle([62, 75, 66, 76], fill=GOLD)
    d.rectangle([62, 77, 66, 83], fill=AMBERS[1]); d.rectangle([64, 78, 64, 82], fill=LIT_HI)
    d.line([(62, 77), (62, 83)], fill=GOLD); d.line([(66, 77), (66, 83)], fill=GOLD)
    d.rectangle([62, 84, 66, 84], fill=GOLD); d.point((64, 85), fill=GOLD)
    # the hanging board: a cocktail glass
    d.line([(69, 61), (86, 61)], fill=TIMBER_LO)
    for x in (72, 83):
        d.line([(x, 62), (x, 64)], fill=GOLD)
    d.rectangle([69, 65, 86, 86], fill=GOLD)
    d.rectangle([70, 66, 85, 85], fill=NAVY)
    d.polygon([(72, 69), (83, 69), (78, 75), (77, 75)], fill=rgb('c8f2f6'))
    d.line([(72, 69), (83, 69)], fill=WHITE)
    d.line([(77, 76), (77, 81)], fill=WHITE); d.line([(78, 76), (78, 81)], fill=rgb('c8f2f6'))
    d.line([(74, 82), (81, 82)], fill=WHITE)
    d.rectangle([75, 70, 76, 71], fill=RED); d.line([(77, 68), (80, 67)], fill=GOLD)
    # a whisky barrel on the step, firewood stacked against the dado
    d.rectangle([70, 105, 84, 126], fill=WOOD); d.rectangle([69, 109, 85, 122], fill=WOOD)
    for x in range(72, 84, 3):
        d.line([(x, 105), (x, 126)], fill=WOOD_LO)
    for y in (108, 123):
        d.line([(70, y), (84, y)], fill=STONE_DK)
    d.line([(69, 115), (85, 115)], fill=STONE_DK)
    d.ellipse([70, 102, 84, 107], fill=rgb('d3a48c')); d.ellipse([72, 103, 82, 106], fill=WOOD)
    for row, y in enumerate((121, 116, 111)):
        for x in range(11 + row * 2, 31 - row * 2, 5):
            d.ellipse([x, y, x + 4, y + 4], fill=WOOD_LO); d.ellipse([x + 1, y + 1, x + 3, y + 3], fill=rgb('d3a48c'))
            d.point((x + 2, y + 2), fill=WOOD_LO)
    fallen(d, [(30, 24), (66, 27), (80, 33), (20, 30)])
    outline(im)
    return im


# What each front lights at night: glow spots (src/utils/Glows.js), in cells from the
# sprite's top-left, written to its spriteMetadata. The fingerpost has none.
WARM, GLOW_AMBER = 0xf6dc8c, 0xffb366
GLOW = {
    'karuizawa-shop-bakery_0_0': [{'x': 0.75, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},        # the bread window
                                  {'x': 1.85, 'y': 2.8, 'r': 1.0, 'ry': 0.8, 'color': WARM, 'a': 0.5}],   # the door glass, the east window
    'karuizawa-shop-jam_0_0': [{'x': 0.67, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},           # the west window of jars
                               {'x': 2.3, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},            # the east one
                               {'x': 1.5, 'y': 2.85, 'r': 0.6, 'color': WARM, 'a': 0.4}],          # the door glass
    'karuizawa-shop-lounge_0_0': [{'x': 0.66, 'y': 2.5, 'r': 0.9, 'color': GLOW_AMBER, 'a': 0.55},      # the window of bottles
                                  {'x': 2.0, 'y': 2.5, 'r': 0.6, 'color': GLOW_AMBER, 'a': 0.6}],       # the lantern by the door
}

SPRITES = {      # key: (builder, scale, tileNames label)
    'karuizawa-fingerpost_0_0': (fingerpost, 2, 'karuizawa-fingerpost'),
    'karuizawa-shop-bakery_0_0': (shop_bakery, 2, 'karuizawa-shop-bakery'),
    'karuizawa-shop-jam_0_0': (shop_jam, 2, 'karuizawa-shop-jam'),
    'karuizawa-shop-lounge_0_0': (shop_lounge, 2, 'karuizawa-shop-lounge'),
    'karuizawa-larch_0_0': (larch(3), 2, 'karuizawa-larch'),
    'karuizawa-larch_0_1': (larch(4), 2, 'karuizawa-larch'),
    'karuizawa-falls_0_0': (falls, 2, 'karuizawa-falls'),
    'karuizawa-corn-stall_0_0': (corn_stall, 2, 'karuizawa-corn-stall'),
}


def main():
    built = {}
    for key, (fn, scale, _) in SPRITES.items():
        im = fn()
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')

    cfg = json.load(open('config.json'))
    for key, (_, _, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if key in GLOW:
            cfg['spriteMetadata'][key]['glow'] = GLOW[key]
        cfg.setdefault('tileNames', {})[key] = label
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (sum(im.width + 16 for im in built.values()) + 16,
                                   max(im.height for im in built.values()) + 32), rgb('83af6f'))
        x = 16
        for im in built.values():
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
