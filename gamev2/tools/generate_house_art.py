#!/usr/bin/env python3
"""generate_house_art.py — draw the furniture of a Japanese home (issue #208)
and of a tower's lobby (issue #216, the `lobby-*` sprites at the end).

None of the GuttyKreum packs has a home interior (they are all
exteriors plus a train car; there is no Modern_Interiors), so everything the
house interiors of tools/generate_houses.py stand on, apart from the two
sprites tools/extract_house_interior.py does find, is drawn here the way
tools/generate_hokkaido.py draws Hokkaido: shaded pixel art in the GuttyKreum
palette, at half size and pixel-doubled, with a 1px ink outline on everything
that stands. Nothing here is a white line-art placeholder.

  floors (1x1, Floor layer)
    home-tatami-green_w / _e    the two halves of a tatami mat, fresh rush
    home-tatami-gold_w / _e     the same mat, sun-aged
    home-genkan_0_0             the entry's lowered stone floor
    home-agari_0_0              the board you step up onto from the genkan
  walls (1x2, the back wall; solid)
    home-wall-sand_0_0 / home-wall-moss_0_0    plaster under a beam (two colours)
    home-wall-shoji_0_0         a shoji screen
    home-wall-fusuma_0_0        a painted sliding door (the closet)
    home-wall-window-sand_0_0 / -moss_0_0      a frosted window in that plaster
    home-tokonoma_0_0     2x2   the alcove: hanging scroll, a vase with a branch
  against the wall (1x2: the top half stands over the wall's lower half)
    home-tansu_0_0, home-bookshelf_0_0, home-tv_0_0, home-fridge_0_0
    home-kitchen_0_0      2x2   sink, hob and kettle under wall cupboards
  on the floor
    home-kotatsu-red_0_0 / -indigo_0_0   2x2   heated table under its quilt
    home-table_0_0        2x1   a low table (chabudai) with the tea things
    home-irori_0_0        2x2   the sunken hearth, an iron kettle on its hook
    home-futon-blue_0_0 / -rose_0_0      1x2   a futon laid out
    home-bed_0_0          1x2   a western bed
    home-stove_0_0        1x1   a paraffin stove with a kettle on it
    home-andon_0_0        1x1   a paper floor lamp
    home-getabako_0_0     1x1   the shoe cupboard by the door
    home-zabuton-red / -indigo / -green_0_0    1x1, flat: floor cushions
    home-shoes-a_0_0 / -b_0_0   1x1, flat: shoes left in the genkan
    home-doormat_0_0      1x1, flat: the mat you leave by

  a tower's lobby (issue #216)
    lobby-floor_a / _b          1x1  polished stone, laid as a chequer
    lobby-mat_0_0               1x1, flat: the entrance mat you leave by
    lobby-wall_0_0              1x2  panelled stone under a cornice (solid)
    lobby-lift_0_0              2x2  a lift: steel doors, the floor indicator, the call button
    lobby-directory_0_0         1x2  the building directory on the wall
    lobby-desk_0_0              3x1  the reception desk: a bell, a screen, the visitors' book
    lobby-sofa_0_0 / lobby-sofa-back_0_0   2x1  a sofa from the front, and from behind
    lobby-table_0_0             2x1  a glass coffee table with magazines
    lobby-plant_0_0             1x1  a potted palm

Deterministic and idempotent (no source image, no font): rewrites the PNGs in
assets/sprites/ and registers them in config.json spriteMetadata + tileNames.
Needs Pillow. Run from gamev2/ BEFORE generate_houses.py:
    python3 tools/generate_house_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (C, rgb, canvas, outline, INK, RED, RED_HI, RED_LO, CREAM, CREAM_LO,
                               CREAM_DK, WHITE, GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)

WOOD_HI = rgb('d7a98c')
BEAM, BEAM_HI, BEAM_LO = rgb('5e4a42'), rgb('7c6455'), rgb('3d302e')
PAPER, PAPER_LO, PAPER_DK = rgb('f7f1e3'), rgb('e6dcc6'), rgb('cbbfa6')
RUSH = {'green': (rgb('c3c98c'), rgb('b2ba7d'), rgb('98a26b')),
        'gold': (rgb('dccb8e'), rgb('cdb97c'), rgb('b39d66'))}
HERI, HERI_HI = rgb('2f4a44'), rgb('46695c')
RUSH_END = rgb('6f7a52')
PLASTER = {'sand': (rgb('e7d8b9'), rgb('d6c4a0'), rgb('bfab86')),
           'moss': (rgb('c3cbab'), rgb('aeb894'), rgb('95a07c'))}
INDIGO, INDIGO_HI, INDIGO_LO = rgb('3c4f86'), rgb('6480bd'), rgb('26335c')
ROSE, ROSE_HI, ROSE_LO = rgb('d98f96'), rgb('efb9b7'), rgb('b4686f')
SKY, SKY_HI, SKY_LO = rgb('7fa6d6'), rgb('a9c8ec'), rgb('5c80b4')
STEEL, STEEL_HI, STEEL_LO = rgb('b9c4cf'), rgb('e2e9ef'), rgb('7f8ea0')
IRON, IRON_HI = rgb('2c2d3a'), rgb('4b4f63')
ASH, ASH_LO = rgb('a9a59c'), rgb('8a857d')
LIT, LIT_HI, EMBER = rgb('f2c66a'), rgb('fbe6a4'), rgb('e8623a')
ORANGE = rgb('f0943a')


def box(d, x0, y0, x1, y1, top, face, lo, th):
    """A piece of furniture seen from above and in front: `th` rows of top
    face, the front face under it, a lit top edge and a shaded foot."""
    d.rectangle([x0, y0, x1, y0 + th - 1], fill=top)
    d.rectangle([x0, y0 + th, x1, y1], fill=face)
    d.line([(x0, y0 + th), (x1, y0 + th)], fill=lo)
    d.line([(x0, y1), (x1, y1)], fill=lo)


def speckle(d, x0, y0, x1, y1, colour, seed, every=11):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x * 7 + y * 13 + seed * 5) % every == 0 and (x + y * 3 + seed) % 3 == 0:
                d.point((x, y), fill=colour)


# ---- floors --------------------------------------------------------------------
def tatami(colour, half):
    def draw():
        im, d = canvas(1, 1)
        base, mid, lo = RUSH[colour]
        d.rectangle([0, 0, 31, 31], fill=base)
        for y in range(0, 32, 2):                          # the rush, woven across the mat
            d.line([(0, y), (31, y)], fill=mid)
        speckle(d, 0, 3, 31, 28, lo, 3 if half == 'w' else 8, every=7)
        d.line([(0, 0), (31, 0)], fill=HERI)               # the cloth border (heri), both long sides
        d.line([(0, 31), (31, 31)], fill=HERI)
        d.line([(0, 1), (31, 1)], fill=lo); d.line([(0, 30), (31, 30)], fill=lo)
        for x in range(1, 32, 4):
            d.point((x, 0), fill=HERI_HI); d.point((x + 2, 31), fill=HERI_HI)
        x = 0 if half == 'w' else 31                       # where this mat ends and the next begins
        d.line([(x, 1), (x, 30)], fill=RUSH_END)
        d.line([(1 if half == 'w' else 30, 2), (1 if half == 'w' else 30, 29)], fill=lo)
        return im
    return draw


def genkan():
    im, d = canvas(1, 1)
    d.rectangle([0, 0, 31, 31], fill=STONE_LO)
    for y in range(0, 32, 16):
        for x in range(0, 32, 16):
            d.rectangle([x + 1, y + 1, x + 14, y + 14], fill=STONE if (x + y) % 32 == 0 else rgb('a9b2bb'))
            d.line([(x + 1, y + 14), (x + 14, y + 14)], fill=rgb('9099a6'))
    d.rectangle([0, 0, 31, 2], fill=STONE_DK)              # in the shadow of the step above it
    return im


def agari():
    im, d = canvas(1, 1)
    d.rectangle([0, 0, 31, 31], fill=WOOD)
    for y in (0, 13):
        d.line([(0, y), (31, y)], fill=WOOD_LO)
    for x, y in ((5, 5), (19, 8), (11, 19), (25, 21)):      # the grain of two long boards
        d.line([(x, y), (x + 5, y)], fill=rgb('c99a80'))
    d.line([(0, 26), (31, 26)], fill=WOOD_HI)              # the worn front edge of the step...
    d.rectangle([0, 27, 31, 30], fill=WOOD_LO)             # ...and its riser, down to the genkan
    d.line([(0, 31), (31, 31)], fill=WOOD_DK)
    return im


# ---- the back wall, 1x2 ----------------------------------------------------------
def wall_frame(d, w=32):
    """What every wall piece shares, so they join side by side: the ceiling
    beam, the picture rail (nageshi) and the skirting board."""
    d.rectangle([0, 0, w - 1, 5], fill=BEAM)
    d.line([(0, 0), (w - 1, 0)], fill=BEAM_LO)
    d.line([(0, 5), (w - 1, 5)], fill=BEAM_LO)
    d.line([(0, 1), (w - 1, 1)], fill=BEAM_HI)
    d.rectangle([0, 16, w - 1, 18], fill=BEAM)
    d.line([(0, 16), (w - 1, 16)], fill=BEAM_HI)
    d.rectangle([0, 58, w - 1, 63], fill=BEAM)
    d.line([(0, 58), (w - 1, 58)], fill=BEAM_HI)
    d.line([(0, 63), (w - 1, 63)], fill=BEAM_LO)


def plaster(colour):
    def draw():
        im, d = canvas(1, 2)
        base, mid, lo = PLASTER[colour]
        d.rectangle([0, 0, 31, 63], fill=base)
        speckle(d, 0, 6, 31, 57, mid, 1, every=5)
        d.line([(0, 6), (31, 6)], fill=lo); d.line([(0, 19), (31, 19)], fill=lo)
        wall_frame(d)
        return im
    return draw


def shoji():
    im, d = canvas(1, 2)
    d.rectangle([0, 0, 31, 63], fill=BEAM)                  # the screen's own frame: no plaster shows
    for x0 in (1, 17):                                      # two sliding leaves
        d.rectangle([x0, 20, x0 + 13, 56], fill=PAPER)
        for y in range(20, 57):                             # daylight through the paper
            if y > 46:
                d.line([(x0, y), (x0 + 13, y)], fill=PAPER_LO)
        for x in (x0 + 4, x0 + 9):
            d.line([(x, 20), (x, 56)], fill=WOOD_LO)
        for y in (26, 32, 38, 44, 50):
            d.line([(x0, y), (x0 + 13, y)], fill=WOOD_LO)
    d.rectangle([0, 7, 31, 15], fill=PAPER_LO)              # the transom (ranma) above the rail
    for x in range(3, 32, 4):
        d.line([(x, 7), (x, 15)], fill=WOOD_LO)
    wall_frame(d)
    return im


def fusuma():
    im, d = canvas(1, 2)
    d.rectangle([0, 0, 31, 63], fill=IRON)                  # black lacquer frame: no plaster shows
    for i, x0 in enumerate((1, 17)):
        d.rectangle([x0, 20, x0 + 13, 56], fill=PAPER)
        d.rectangle([x0, 44, x0 + 13, 56], fill=PAPER_LO)   # a band of mist low on the leaf
        for k, (px, py) in enumerate(((3, 40), (6, 36), (9, 39), (11, 34), (5, 31))):   # a pine bough in ink and green
            d.line([(x0 + px - 2, py + i), (x0 + px + 2, py + i)], fill=GREEN if k % 2 else GREEN_LO)
        d.line([(x0 + 2, 43), (x0 + 11, 33 + i)], fill=BEAM_HI)
        d.rectangle([x0 + (10 if i == 0 else 2), 38, x0 + (11 if i == 0 else 3), 40], fill=IRON)   # the pulls meet in the middle
        d.point((x0 + (10 if i == 0 else 2), 38), fill=GOLD)
    d.rectangle([0, 7, 31, 15], fill=PAPER_LO)              # a plain paper transom
    d.line([(15, 7), (15, 15)], fill=IRON); d.line([(16, 7), (16, 15)], fill=IRON)
    wall_frame(d)
    return im


def wall_window(colour):
    def draw():
        im, d = canvas(1, 2)
        base, mid, lo = PLASTER[colour]
        d.rectangle([0, 0, 31, 63], fill=base)
        speckle(d, 0, 6, 31, 57, mid, 4, every=5)
        wall_frame(d)
        d.rectangle([3, 22, 28, 48], fill=BEAM)
        d.rectangle([5, 24, 26, 46], fill=SKY_HI)
        for y in range(24, 47):                                 # frosted glass, brighter at the top
            if y > 36:
                d.line([(5, y), (26, y)], fill=SKY)
        d.line([(6, 25), (12, 25)], fill=WHITE); d.line([(6, 26), (8, 26)], fill=WHITE)
        d.line([(15, 24), (15, 46)], fill=BEAM); d.line([(16, 24), (16, 46)], fill=BEAM_HI)
        d.line([(5, 35), (26, 35)], fill=BEAM)
        d.rectangle([2, 49, 29, 50], fill=WOOD); d.line([(2, 51), (29, 51)], fill=lo)   # the sill
        return im
    return draw


def tokonoma():
    im, d = canvas(2, 2)
    d.rectangle([0, 0, 63, 63], fill=WOOD_LO)               # framed in timber: no plaster shows
    d.rectangle([2, 7, 57, 57], fill=rgb('a89674'))         # the recess, in its own shade
    d.rectangle([2, 7, 57, 12], fill=rgb('7f6f58'))         # and darker under the lintel
    d.rectangle([2, 7, 4, 57], fill=rgb('8f7f64'))
    speckle(d, 5, 13, 57, 50, rgb('9c8a6a'), 6, every=5)
    # the hanging scroll: brocade, paper, an ink mountain, a red seal
    d.rectangle([17, 10, 34, 47], fill=INDIGO_LO)
    d.rectangle([18, 14, 33, 43], fill=PAPER)
    d.line([(16, 10), (35, 10)], fill=BEAM_LO); d.rectangle([15, 47, 36, 48], fill=BEAM_LO)
    d.line([(25, 7), (25, 9)], fill=BEAM_LO)
    for x, top in zip(range(20, 32), (36, 33, 30, 27, 25, 27, 29, 26, 24, 28, 32, 35)):
        d.line([(x, top), (x, 38)], fill=rgb('7c8088') if x % 3 else rgb('5a5e68'))
    d.line([(19, 39), (32, 39)], fill=PAPER_DK)
    d.ellipse([27, 17, 31, 21], fill=RED)                   # the sun
    d.rectangle([20, 40, 21, 41], fill=RED_LO)              # the seal
    # the raised floor board of the alcove, and a vase with a flowering branch
    d.rectangle([2, 51, 57, 57], fill=WOOD); d.line([(2, 51), (57, 51)], fill=WOOD_HI)
    d.line([(2, 57), (57, 57)], fill=WOOD_DK)
    d.rectangle([44, 42, 50, 50], fill=SKY_LO); d.rectangle([45, 40, 49, 42], fill=SKY)
    d.line([(44, 44), (44, 49)], fill=SKY_HI); d.line([(43, 51), (51, 51)], fill=WOOD_DK)
    for (x0, y0), (x1, y1) in (((47, 40), (46, 30)), ((46, 30), (50, 22)), ((46, 32), (41, 26)), ((48, 27), (53, 25))):
        d.line([(x0, y0), (x1, y1)], fill=BEAM_LO)
    for x, y in ((50, 22), (41, 26), (53, 25), (44, 29), (49, 25), (52, 21), (40, 24)):
        d.rectangle([x - 1, y - 1, x, y], fill=ROSE_HI); d.point((x, y), fill=ROSE)
    # the alcove post (tokobashira), a natural trunk, down its right side
    d.rectangle([58, 6, 62, 57], fill=WOOD_LO); d.line([(59, 6), (59, 57)], fill=WOOD)
    d.line([(62, 6), (62, 57)], fill=WOOD_DK)
    for y in (18, 33, 46):
        d.point((60, y), fill=WOOD_DK)
    wall_frame(d, 64)
    d.rectangle([2, 16, 57, 18], fill=rgb('a89674'))        # the rail stops at the alcove...
    d.rectangle([2, 16, 4, 18], fill=rgb('8f7f64'))
    d.rectangle([17, 16, 34, 18], fill=INDIGO_LO)           # ...and the scroll hangs across where it was
    d.line([(0, 6), (0, 57)], fill=WOOD); d.line([(1, 6), (1, 57)], fill=WOOD_DK)
    d.line([(63, 6), (63, 57)], fill=WOOD_DK)
    return im


# ---- against the wall, 1x2 (the top half stands over the wall) --------------------
def tansu():
    im, d = canvas(1, 2)
    box(d, 2, 20, 29, 61, WOOD_HI, WOOD, WOOD_LO, 5)
    for y0, y1, split in ((26, 33, True), (35, 42, False), (44, 51, False), (53, 60, False)):
        d.rectangle([4, y0, 27, y1], fill=rgb('a87861'))
        d.line([(4, y0), (27, y0)], fill=WOOD_HI); d.line([(4, y1), (27, y1)], fill=WOOD_DK)
        if split:
            d.line([(15, y0), (15, y1)], fill=WOOD_DK); d.line([(16, y0), (16, y1)], fill=WOOD_HI)
        for hx in ((9, 22) if split else (15,)):            # iron pulls and corner plates
            d.rectangle([hx - 2, y0 + 3, hx + 2, y0 + 4], fill=IRON); d.point((hx, y0 + 5), fill=IRON)
        for cx in (4, 27):
            d.point((cx, y0), fill=IRON); d.point((cx, y1), fill=IRON)
    d.rectangle([9, 14, 15, 20], fill=RED); d.rectangle([10, 12, 14, 14], fill=RED_HI)   # a daruma on top
    d.rectangle([11, 15, 13, 17], fill=CREAM); d.point((11, 16), fill=INK); d.point((13, 16), fill=INK)
    d.rectangle([19, 16, 25, 20], fill=PAPER); d.line([(19, 20), (25, 20)], fill=PAPER_DK)   # a folded cloth
    outline(im)
    return im


def bookshelf():
    im, d = canvas(1, 2)
    box(d, 2, 10, 29, 61, WOOD_HI, WOOD_LO, WOOD_DK, 4)
    spines = (RED, INDIGO, GREEN_HI, GOLD, CREAM, SKY, ROSE, GREEN, INDIGO_HI, RED_LO, AMBER, STONE)
    for row, y0 in enumerate((16, 28, 40, 52)):
        d.rectangle([4, y0, 27, y0 + 9], fill=rgb('3d302e'))
        x, k = 5, row * 5
        while x < 26:
            w = 2 + (k * 7 + row) % 2
            h = 7 + (k * 3) % 3
            if (k + row) % 7 == 6:                          # a gap, or a book lying flat
                d.rectangle([x, y0 + 7, min(26, x + 5), y0 + 9], fill=spines[k % len(spines)])
                x += 7
            else:
                d.rectangle([x, y0 + 10 - h, min(26, x + w - 1), y0 + 9], fill=spines[k % len(spines)])
                d.point((x, y0 + 11 - h), fill=WHITE if k % 3 == 0 else spines[(k + 1) % len(spines)])
                x += w + (1 if k % 4 == 0 else 0)
            k += 1
        d.line([(3, y0 + 10), (28, y0 + 10)], fill=WOOD)
    outline(im)
    return im


def tv():
    im, d = canvas(1, 2)
    box(d, 1, 40, 30, 61, WOOD_HI, WOOD, WOOD_LO, 5)        # the low stand
    d.rectangle([3, 47, 14, 59], fill=WOOD_LO); d.rectangle([17, 47, 28, 59], fill=GLASS_DK)
    d.line([(18, 53), (27, 53)], fill=IRON_HI); d.point((26, 50), fill=AMBER)   # a recorder behind glass
    d.point((12, 53), fill=WOOD_DK)
    d.rectangle([13, 37, 18, 40], fill=IRON); d.rectangle([9, 40, 22, 41], fill=IRON_HI)   # the foot
    d.rectangle([2, 14, 29, 37], fill=IRON)                 # the set
    d.rectangle([4, 16, 27, 35], fill=GLASS_DK)
    d.rectangle([4, 16, 27, 22], fill=SKY_LO); d.rectangle([4, 23, 27, 27], fill=SKY)   # the evening news: a weather map
    d.rectangle([4, 28, 27, 35], fill=INDIGO)
    for x, y in ((8, 20), (15, 18), (21, 21)):
        d.rectangle([x, y, x + 3, y + 1], fill=WHITE)
    d.rectangle([6, 30, 16, 31], fill=WHITE); d.rectangle([6, 33, 12, 33], fill=SKY_HI)
    d.rectangle([20, 29, 25, 34], fill=AMBER); d.point((22, 31), fill=RED)
    d.point((28, 36), fill=RED)
    outline(im)
    return im


def fridge():
    im, d = canvas(1, 2)
    box(d, 3, 8, 28, 61, WHITE, rgb('e4ebf2'), STEEL, 5)
    d.line([(3, 31), (28, 31)], fill=STEEL_LO); d.line([(3, 32), (28, 32)], fill=WHITE)
    d.rectangle([24, 18, 25, 28], fill=STEEL_LO); d.rectangle([24, 35, 25, 47], fill=STEEL_LO)
    d.line([(27, 13), (27, 60)], fill=STEEL)
    d.rectangle([7, 17, 12, 23], fill=PAPER); d.line([(8, 19), (11, 19)], fill=STEEL_LO)   # a note, a magnet, a photo
    d.line([(8, 21), (10, 21)], fill=STEEL_LO); d.point((9, 17), fill=RED)
    d.rectangle([15, 20, 19, 25], fill=SKY); d.rectangle([15, 23, 19, 25], fill=GREEN_HI)
    d.rectangle([8, 37, 10, 39], fill=ORANGE); d.rectangle([13, 39, 15, 41], fill=INDIGO_HI)
    outline(im)
    return im


def kitchen():
    im, d = canvas(2, 2)
    # wall cupboards and the extractor hood, over a tiled splashback
    box(d, 1, 2, 38, 19, WOOD_HI, WOOD, WOOD_LO, 3)
    for x0 in (3, 15, 27):
        d.rectangle([x0, 7, x0 + 9, 17], fill=rgb('c99a80')); d.line([(x0, 17), (x0 + 9, 17)], fill=WOOD_LO)
        d.point((x0 + 8, 12), fill=IRON)
    d.polygon([(42, 2), (61, 2), (63, 14), (40, 14)], fill=STEEL)
    d.line([(42, 2), (61, 2)], fill=STEEL_HI); d.rectangle([40, 14, 63, 17], fill=STEEL_LO)
    d.line([(44, 16), (59, 16)], fill=IRON_HI)
    d.rectangle([1, 20, 62, 33], fill=WHITE)
    for x in range(1, 63, 6):
        d.line([(x, 20), (x, 33)], fill=STEEL_HI)
    d.line([(1, 26), (62, 26)], fill=STEEL_HI)
    for i, x in enumerate((6, 10, 14)):                     # ladle, turner, whisk on a rail
        d.line([(x, 22), (x, 29)], fill=IRON_HI); d.rectangle([x - 1, 29, x + 1, 31], fill=(STEEL_LO, IRON, STEEL)[i])
    d.line([(4, 22), (17, 22)], fill=STEEL_LO)
    # the worktop: sink and tap on the left, a two-ring hob with the kettle on the right
    box(d, 1, 34, 62, 61, STEEL_HI, WOOD, WOOD_LO, 12)
    d.rectangle([1, 34, 62, 45], fill=rgb('d9dfe5')); d.line([(1, 45), (62, 45)], fill=STEEL_LO)
    d.rectangle([5, 36, 24, 43], fill=STEEL_LO); d.rectangle([6, 37, 23, 42], fill=STEEL)
    d.line([(6, 37), (23, 37)], fill=IRON_HI); d.point((14, 40), fill=IRON)
    d.rectangle([14, 31, 15, 36], fill=STEEL_LO); d.line([(14, 31), (18, 31)], fill=STEEL_LO); d.point((18, 32), fill=STEEL_LO)
    d.rectangle([27, 37, 33, 42], fill=PAPER); d.rectangle([28, 36, 32, 36], fill=PAPER_LO)   # the rice cooker
    d.rectangle([29, 39, 31, 40], fill=AMBER); d.line([(27, 42), (33, 42)], fill=PAPER_DK)
    d.rectangle([38, 35, 61, 44], fill=IRON)
    for cx in (44, 55):
        d.ellipse([cx - 4, 36, cx + 4, 43], outline=IRON_HI)
    d.ellipse([40, 33, 48, 41], fill=SKY_LO); d.ellipse([41, 33, 47, 38], fill=SKY)   # the kettle, on the boil
    d.line([(42, 34), (45, 34)], fill=SKY_HI); d.line([(48, 36), (50, 34)], fill=SKY_LO)
    d.rectangle([43, 31, 45, 32], fill=IRON)
    d.point((51, 31), fill=WHITE); d.point((52, 29), fill=WHITE); d.point((51, 27), fill=STEEL_HI)
    for x0 in (3, 18, 33, 48):                              # the doors under the worktop
        d.rectangle([x0, 48, x0 + 12, 59], fill=rgb('c99a80')); d.line([(x0, 59), (x0 + 12, 59)], fill=WOOD_DK)
        d.line([(x0, 48), (x0 + 12, 48)], fill=WOOD_HI); d.point((x0 + 10, 53), fill=IRON)
    outline(im)
    return im


# ---- on the floor ------------------------------------------------------------------
def kotatsu(base, hi, lo):
    def draw():
        im, d = canvas(2, 2)
        d.rounded_rectangle([2, 8, 61, 61], radius=7, fill=base)          # the quilt, spread on the tatami
        for y in range(8, 62):                                            # a woven check
            for x in range(2, 62):
                if im.getpixel((x, y))[3] and ((x // 5 + y // 5) % 2 == 0):
                    d.point((x, y), fill=hi)
        for y in range(52, 62):                                           # the near edge falls in shadow
            for x in range(2, 62):
                if im.getpixel((x, y))[3] and (x + y) % 2:
                    d.point((x, y), fill=lo)
        d.rounded_rectangle([2, 8, 61, 61], radius=7, outline=lo)
        for (x0, y0), (x1, y1) in (((12, 20), (4, 12)), ((51, 20), (59, 12)), ((12, 46), (5, 58)), ((51, 46), (58, 58))):
            d.line([(x0, y0), (x1, y1)], fill=lo)                         # the folds at its corners
        box(d, 12, 14, 51, 47, WOOD_HI, WOOD, WOOD_LO, 28)                # the table top over it
        d.rectangle([12, 14, 51, 15], fill=rgb('e6bfa3')); d.line([(12, 41), (51, 41)], fill=WOOD)
        for x in (22, 32, 42):
            d.line([(x, 16), (x, 40)], fill=rgb('c99a80'))
        d.ellipse([17, 20, 30, 30], fill=BEAM); d.ellipse([18, 20, 29, 28], fill=BEAM_HI)   # a bowl of mikan
        for x, y in ((20, 22), (24, 20), (26, 24), (22, 25)):
            d.ellipse([x, y, x + 3, y + 3], fill=ORANGE); d.point((x + 1, y), fill=AMBER)
        d.point((25, 20), fill=GREEN_HI)
        d.rectangle([38, 27, 42, 32], fill=SKY_LO); d.rectangle([39, 27, 41, 28], fill=rgb('7a9a55'))   # a cup of tea
        d.rectangle([37, 19, 46, 24], fill=PAPER); d.line([(38, 21), (44, 21)], fill=STONE_LO)   # the paper, half read
        d.line([(38, 23), (42, 23)], fill=STONE_LO)
        outline(im)
        return im
    return draw


def low_table():
    im, d = canvas(2, 1)
    d.rounded_rectangle([4, 5, 59, 24], radius=6, fill=WOOD_HI)
    d.rounded_rectangle([4, 20, 59, 26], radius=3, fill=WOOD_LO)
    d.rounded_rectangle([4, 5, 59, 22], radius=6, fill=WOOD_HI)
    d.line([(8, 22), (55, 22)], fill=WOOD)
    for x in (20, 33, 46):
        d.line([(x, 7), (x, 21)], fill=rgb('c99a80'))
    for x in (9, 51):                                       # the stub legs
        d.rectangle([x, 26, x + 3, 29], fill=WOOD_DK)
    d.ellipse([24, 8, 33, 17], fill=IRON); d.ellipse([25, 8, 32, 14], fill=IRON_HI)   # an iron teapot
    d.line([(33, 12), (36, 10)], fill=IRON); d.arc([25, 4, 32, 12], 180, 360, fill=IRON)
    for x in (14, 41):
        d.rectangle([x, 12, x + 4, 16], fill=PAPER); d.rectangle([x + 1, 12, x + 3, 13], fill=rgb('7a9a55'))
    d.rectangle([46, 10, 53, 15], fill=RED_LO); d.rectangle([47, 10, 52, 13], fill=ROSE_HI)   # a plate of sweets
    outline(im)
    return im


def irori():
    im, d = canvas(2, 2)
    d.rectangle([3, 12, 60, 60], fill=WOOD); d.rectangle([3, 12, 60, 14], fill=WOOD_HI)     # the frame, flush with the boards
    d.rectangle([3, 56, 60, 60], fill=WOOD_LO)
    d.rectangle([10, 19, 53, 52], fill=ASH); d.rectangle([10, 19, 53, 22], fill=ASH_LO)     # the ash bed
    d.rectangle([10, 19, 12, 52], fill=ASH_LO)
    speckle(d, 13, 23, 52, 51, ASH_LO, 5, every=5)
    for x, y in ((17, 27), (45, 30), (20, 47), (42, 46), (48, 39)):
        d.point((x, y), fill=WHITE)
    for (x0, y0, x1, y1) in ((24, 36, 33, 39), (30, 33, 40, 36), (27, 40, 38, 43)):          # charcoal, glowing
        d.rectangle([x0, y0, x1, y1], fill=IRON)
        d.rectangle([x0 + 1, y0 + 1, x1 - 2, y1 - 1], fill=EMBER); d.point((x0 + 3, y0 + 1), fill=LIT)
    d.line([(31, 0), (31, 22)], fill=BEAM_LO); d.line([(32, 0), (32, 22)], fill=BEAM)        # the hook from the rafters
    d.rectangle([28, 10, 35, 12], fill=WOOD_LO)                                             # its wooden fish
    d.ellipse([24, 21, 39, 34], fill=IRON); d.ellipse([25, 21, 38, 29], fill=IRON_HI)        # the iron kettle
    d.arc([25, 15, 38, 29], 180, 360, fill=IRON); d.line([(39, 26), (43, 23)], fill=IRON)
    d.rectangle([30, 20, 33, 21], fill=IRON)
    for x, y in ((44, 20), (45, 17), (44, 14)):
        d.point((x, y), fill=WHITE)
    for x in (16, 46):                                                                      # tongs stuck in the ash
        d.line([(x, 44), (x + 1, 50)], fill=IRON_HI)
    outline(im)
    return im


def futon(base, hi, lo):
    def draw():
        im, d = canvas(1, 2)
        d.rounded_rectangle([3, 4, 28, 60], radius=3, fill=PAPER)            # the mattress
        d.line([(4, 60), (27, 60)], fill=PAPER_DK)
        d.rounded_rectangle([7, 7, 24, 16], radius=3, fill=WHITE)             # the pillow
        d.line([(9, 15), (22, 15)], fill=PAPER_LO)
        d.rounded_rectangle([2, 21, 29, 61], radius=4, fill=base)             # the quilt
        d.rectangle([2, 21, 29, 25], fill=PAPER_LO); d.line([(2, 26), (29, 26)], fill=lo)   # turned back at the top
        for y in range(30, 60, 8):
            for x in range(6, 28, 8):
                ox = x + (4 if (y // 8) % 2 else 0)
                if ox < 27:
                    d.rectangle([ox, y, ox + 1, y + 1], fill=hi); d.point((ox + 2, y + 1), fill=hi); d.point((ox - 1, y + 1), fill=hi)
        d.line([(3, 60), (28, 60)], fill=lo); d.line([(28, 28), (28, 59)], fill=lo)
        outline(im)
        return im
    return draw


def bed():
    im, d = canvas(1, 2)
    box(d, 2, 2, 29, 12, WOOD_HI, WOOD, WOOD_LO, 3)                          # the headboard
    d.rectangle([3, 13, 28, 55], fill=WHITE)
    d.rounded_rectangle([6, 14, 25, 22], radius=3, fill=PAPER); d.line([(8, 21), (23, 21)], fill=PAPER_DK)
    d.rectangle([3, 26, 28, 55], fill=GREEN); d.rectangle([3, 26, 28, 29], fill=PAPER_LO)
    d.line([(3, 30), (28, 30)], fill=GREEN_LO)
    for y in range(34, 55, 6):
        d.line([(3, y), (28, y)], fill=GREEN_HI)
    d.line([(27, 31), (27, 55)], fill=GREEN_LO)
    box(d, 2, 55, 29, 61, WOOD_HI, WOOD, WOOD_LO, 2)                         # the foot board
    outline(im)
    return im


def stove():
    im, d = canvas(1, 1)
    box(d, 7, 12, 24, 29, STONE, CREAM, CREAM_DK, 3)
    d.rectangle([10, 17, 21, 24], fill=IRON); d.rectangle([11, 18, 20, 23], fill=EMBER)   # the glowing mantle
    for x in (12, 15, 18):
        d.line([(x, 18), (x, 23)], fill=LIT)
    d.line([(11, 18), (20, 18)], fill=ORANGE)
    d.rectangle([9, 26, 12, 27], fill=IRON); d.point((21, 27), fill=RED)
    d.ellipse([10, 3, 21, 13], fill=GOLD); d.ellipse([11, 3, 20, 9], fill=rgb('e2c98a'))   # a brass kettle on top
    d.arc([11, 0, 20, 9], 180, 360, fill=IRON); d.line([(21, 8), (24, 6)], fill=GOLD)
    d.point((25, 4), fill=WHITE); d.point((26, 2), fill=WHITE)
    outline(im)
    return im


def andon():
    im, d = canvas(1, 1)
    d.rectangle([9, 5, 22, 25], fill=LIT_HI)
    d.rectangle([9, 15, 22, 25], fill=LIT)
    for x in (9, 15, 16, 22):
        d.line([(x, 5), (x, 25)], fill=BEAM)
    for y in (5, 12, 19, 25):
        d.line([(9, y), (22, y)], fill=BEAM)
    d.rectangle([8, 3, 23, 4], fill=BEAM_LO); d.rectangle([8, 26, 23, 27], fill=BEAM_LO)
    d.rectangle([9, 28, 10, 30], fill=BEAM_LO); d.rectangle([21, 28, 22, 30], fill=BEAM_LO)
    outline(im)
    return im


def getabako():
    im, d = canvas(1, 1)
    box(d, 2, 8, 29, 29, WOOD_HI, WOOD, WOOD_LO, 5)
    for x0 in (4, 17):
        d.rectangle([x0, 15, x0 + 10, 27], fill=rgb('a87861'))
        for y in range(17, 27, 3):
            d.line([(x0 + 1, y), (x0 + 9, y)], fill=WOOD_DK)
    d.rectangle([6, 4, 11, 8], fill=SKY_LO); d.line([(8, 1), (8, 4)], fill=GREEN_LO)     # a bud vase, and the keys
    d.rectangle([7, 0, 9, 1], fill=ROSE_HI)
    d.rectangle([19, 7, 24, 9], fill=PAPER_DK); d.point((21, 8), fill=GOLD); d.point((22, 8), fill=STEEL_LO)
    outline(im)
    return im


def zabuton(base, hi, lo):
    def draw():
        im, d = canvas(1, 1)
        d.rounded_rectangle([5, 7, 26, 26], radius=3, fill=base)
        d.rounded_rectangle([5, 7, 26, 23], radius=3, fill=base)
        d.line([(7, 8), (24, 8)], fill=hi); d.line([(6, 10), (6, 22)], fill=hi)
        d.rectangle([6, 24, 25, 26], fill=lo)
        d.rectangle([15, 15, 16, 16], fill=lo)                               # the tuft in the middle
        for x, y in ((5, 7), (26, 7), (5, 26), (26, 26)):                    # and one at each corner
            d.point((x, y), fill=GOLD)
        for x, y in ((11, 12), (20, 12), (11, 20), (20, 20)):
            d.point((x, y), fill=hi)
        outline(im)
        return im
    return draw


def shoes(pairs):
    def draw():
        im, d = canvas(1, 1)
        for x, y, upper, sole, geta in pairs:
            for dx in (0, 6):
                if geta:                                                     # wooden sandals, toes to the door
                    d.rectangle([x + dx, y, x + dx + 4, y + 9], fill=WOOD_HI)
                    d.line([(x + dx, y + 9), (x + dx + 4, y + 9)], fill=WOOD_LO)
                    d.line([(x + dx + 2, y + 5), (x + dx, y + 2)], fill=upper)
                    d.line([(x + dx + 2, y + 5), (x + dx + 4, y + 2)], fill=upper)
                else:
                    d.rounded_rectangle([x + dx, y, x + dx + 4, y + 9], radius=2, fill=sole)
                    d.rectangle([x + dx + 1, y + 3, x + dx + 3, y + 8], fill=upper)
                    d.point((x + dx + 2, y + 4), fill=WHITE)
        outline(im)
        return im
    return draw


def doormat():
    im, d = canvas(1, 1)
    d.rectangle([4, 8, 27, 25], fill=GREEN)
    for y in range(9, 25, 2):
        d.line([(5, y), (26, y)], fill=GREEN_HI)
    d.rectangle([4, 8, 27, 25], outline=GREEN_LO)
    d.rectangle([9, 13, 22, 20], outline=CREAM)
    return im


# ---- a tower's lobby (issue #216) ---------------------------------------------------
MARBLE = {'a': (rgb('e6e3dc'), rgb('d5d1c8'), rgb('f4f2ee')), 'b': (rgb('c9c6c1'), rgb('b8b4ae'), rgb('dad7d2'))}
PANEL, PANEL_LO, PANEL_HI = rgb('d9d4c7'), rgb('bdb6a6'), rgb('ece8de')
SLATE, SLATE_HI, SLATE_LO = rgb('3f4658'), rgb('5c6680'), rgb('2a2f3e')


def lobby_floor(tone):
    def draw():
        im, d = canvas(1, 1)
        base, vein, hi = MARBLE[tone]
        d.rectangle([0, 0, 31, 31], fill=base)
        speckle(d, 1, 1, 30, 30, vein, 2 if tone == 'a' else 6, every=6)
        for x, y, n in ((4, 9, 6), (17, 21, 8), (22, 5, 4)) if tone == 'a' else ((6, 23, 7), (15, 7, 9)):
            d.line([(x, y), (x + n, y + n // 2)], fill=vein)                # a vein across the slab
        d.line([(1, 1), (30, 1)], fill=hi); d.line([(1, 1), (1, 30)], fill=hi)   # the polish, and the joint
        d.line([(0, 31), (31, 31)], fill=vein); d.line([(31, 0), (31, 31)], fill=vein)
        return im
    return draw


def lobby_mat():
    im, d = canvas(1, 1)
    d.rectangle([2, 7, 29, 26], fill=SLATE)
    for y in range(9, 26, 2):
        d.line([(4, y), (27, y)], fill=SLATE_HI)
    d.rectangle([2, 7, 29, 26], outline=SLATE_LO)
    d.rectangle([5, 10, 26, 23], outline=RED)
    return im


def lobby_wall_frame(d, w=32):
    """What every lobby wall piece shares, so they join side by side: the
    cornice, the stone panelling and the dark skirting."""
    d.rectangle([0, 0, w - 1, 63], fill=PANEL)
    d.rectangle([0, 0, w - 1, 4], fill=SLATE); d.line([(0, 4), (w - 1, 4)], fill=SLATE_LO)
    d.line([(0, 1), (w - 1, 1)], fill=SLATE_HI)
    d.line([(0, 5), (w - 1, 5)], fill=PANEL_HI); d.line([(0, 6), (w - 1, 6)], fill=PANEL_LO)
    d.rectangle([0, 58, w - 1, 63], fill=SLATE); d.line([(0, 58), (w - 1, 58)], fill=SLATE_HI)
    d.line([(0, 63), (w - 1, 63)], fill=SLATE_LO)


def lobby_wall():
    im, d = canvas(1, 2)
    lobby_wall_frame(d)
    for x in (0, 16):                                                       # two stone panels to a cell
        d.rectangle([x + 2, 10, x + 13, 54], outline=PANEL_LO)
        d.line([(x + 3, 11), (x + 12, 11)], fill=PANEL_HI); d.line([(x + 3, 11), (x + 3, 53)], fill=PANEL_HI)
    speckle(d, 4, 13, 28, 52, PANEL_LO, 4, every=9)
    return im


def lobby_lift():
    im, d = canvas(2, 2)
    lobby_wall_frame(d, 64)
    d.rectangle([7, 16, 50, 57], fill=SLATE_LO)                             # the frame
    d.rectangle([9, 18, 48, 57], fill=STEEL)                                # two brushed-steel doors
    for x0 in (9, 29):
        d.rectangle([x0, 18, x0 + 19, 57], fill=STEEL)
        d.line([(x0 + 1, 19), (x0 + 1, 56)], fill=STEEL_HI); d.line([(x0 + 18, 19), (x0 + 18, 56)], fill=STEEL_LO)
        for y in range(22, 56, 6):
            d.line([(x0 + 4, y), (x0 + 15, y)], fill=rgb('aab6c2'))
    d.line([(28, 18), (28, 57)], fill=SLATE_LO); d.line([(29, 18), (29, 57)], fill=SLATE_LO)
    d.rectangle([20, 8, 37, 14], fill=IRON)                                 # the indicator: it is on the 7th floor
    for x, y in ((24, 10), (25, 10), (26, 10), (26, 11), (25, 12), (25, 13)):
        d.point((x, y), fill=AMBER)
    d.polygon([(31, 12), (33, 9), (35, 12)], fill=AMBER)
    d.rectangle([54, 30, 59, 41], fill=STEEL_LO); d.rectangle([55, 31, 58, 40], fill=STEEL_HI)   # the call button
    d.rectangle([56, 33, 57, 34], fill=AMBER); d.rectangle([56, 37, 57, 38], fill=IRON_HI)
    return im


def lobby_directory():
    im, d = canvas(1, 2)
    lobby_wall_frame(d)
    d.rectangle([3, 11, 28, 50], fill=IRON); d.rectangle([4, 12, 27, 49], fill=SLATE_LO)
    d.rectangle([6, 14, 25, 17], fill=GOLD)                                 # the building's name plate
    for i, y in enumerate(range(21, 48, 3)):                                # a floor number and a tenant to a row
        d.rectangle([6, y, 7, y + 1], fill=AMBER)
        d.line([(10, y), (10 + (9, 13, 7, 12, 14, 8, 11, 13, 6)[i], y)], fill=WHITE)
        if i % 3 == 1:
            d.line([(10, y + 1), (16, y + 1)], fill=STEEL_LO)
    d.line([(3, 51), (28, 51)], fill=PANEL_LO)
    return im


def lobby_desk():
    im, d = canvas(3, 1)
    box(d, 2, 6, 93, 29, rgb('eeeae2'), WOOD, WOOD_LO, 7)                    # a stone top on a timber front
    d.line([(2, 6), (93, 6)], fill=WHITE)
    for x in range(10, 90, 10):
        d.line([(x, 14), (x, 28)], fill=WOOD_LO); d.line([(x + 1, 14), (x + 1, 28)], fill=WOOD_HI)
    d.rectangle([38, 17, 57, 25], fill=SLATE); d.rectangle([40, 19, 55, 20], fill=GOLD)   # the plate: RECEPTION
    d.rectangle([42, 22, 53, 22], fill=PANEL_HI)
    d.rectangle([62, 1, 79, 10], fill=IRON); d.rectangle([63, 2, 78, 8], fill=SKY)       # a screen
    d.rectangle([65, 4, 72, 4], fill=WHITE); d.rectangle([65, 6, 69, 6], fill=SKY_HI)
    d.rectangle([69, 10, 72, 11], fill=IRON_HI)
    d.ellipse([14, 5, 21, 10], fill=GOLD); d.rectangle([17, 3, 18, 5], fill=GOLD)       # the bell
    d.line([(13, 11), (22, 11)], fill=WOOD_DK)
    d.rectangle([27, 7, 35, 11], fill=PAPER); d.line([(31, 7), (31, 11)], fill=PAPER_DK)  # the visitors' book
    d.line([(36, 6), (33, 10)], fill=INDIGO)
    outline(im)
    return im


def lobby_sofa(back):
    def draw():
        im, d = canvas(2, 1)
        d.rounded_rectangle([3, 4, 60, 28], radius=4, fill=INDIGO_LO)
        if back:                                                            # seen from behind: the tall back, a seam
            d.rounded_rectangle([3, 4, 60, 26], radius=4, fill=INDIGO)
            d.line([(6, 6), (57, 6)], fill=INDIGO_HI); d.line([(31, 8), (31, 25)], fill=INDIGO_LO)
            d.line([(32, 8), (32, 25)], fill=INDIGO_HI)
        else:
            d.rounded_rectangle([3, 4, 60, 15], radius=4, fill=INDIGO)      # the back, then two seat cushions
            d.line([(6, 5), (57, 5)], fill=INDIGO_HI)
            for x0 in (9, 33):
                d.rounded_rectangle([x0, 14, x0 + 21, 25], radius=2, fill=INDIGO_HI)
                d.line([(x0 + 1, 24), (x0 + 20, 24)], fill=INDIGO)
            for x0 in (3, 55):                                              # the arms
                d.rounded_rectangle([x0, 11, x0 + 5, 27], radius=2, fill=INDIGO)
                d.line([(x0 + 1, 12), (x0 + 4, 12)], fill=INDIGO_HI)
        for x in (6, 54):
            d.rectangle([x, 28, x + 3, 30], fill=WOOD_DK)
        outline(im)
        return im
    return draw


def lobby_table():
    im, d = canvas(2, 1)
    d.rounded_rectangle([6, 7, 57, 23], radius=3, fill=STEEL)
    d.rounded_rectangle([8, 8, 55, 20], radius=2, fill=rgb('cfe2ee'))        # the glass top
    d.line([(11, 10), (22, 10)], fill=WHITE); d.line([(40, 18), (51, 18)], fill=STEEL_HI)
    d.line([(8, 22), (55, 22)], fill=STEEL_LO)
    for x in (9, 51):
        d.rectangle([x, 24, x + 2, 28], fill=IRON)
    d.rectangle([16, 12, 26, 18], fill=RED); d.rectangle([17, 13, 25, 14], fill=WHITE)   # magazines
    d.rectangle([29, 11, 38, 17], fill=GREEN_HI); d.rectangle([30, 12, 34, 13], fill=CREAM)
    outline(im)
    return im


def lobby_plant():
    im, d = canvas(1, 1)
    d.polygon([(10, 20), (21, 20), (19, 30), (12, 30)], fill=CREAM)          # a glazed pot
    d.line([(10, 20), (21, 20)], fill=WHITE); d.line([(12, 30), (19, 30)], fill=CREAM_DK)
    d.line([(19, 22), (18, 29)], fill=CREAM_LO)
    d.line([(15, 20), (15, 9)], fill=WOOD_LO); d.line([(16, 20), (16, 9)], fill=WOOD_DK)
    for (x0, y0), (x1, y1) in (((15, 10), (4, 6)), ((15, 10), (27, 6)), ((15, 12), (3, 14)), ((16, 12), (28, 14)),
                               ((15, 9), (10, 1)), ((16, 9), (21, 1)), ((15, 8), (15, 0))):
        d.line([(x0, y0), (x1, y1)], fill=GREEN, width=2)                   # the fronds
        d.line([(x0, y0 - 1), (x1, y1 - 1)], fill=GREEN_HI)
    for x, y in ((4, 6), (27, 6), (3, 14), (28, 14)):
        d.line([(x, y), (x, y + 3)], fill=GREEN_LO)
    outline(im)
    return im


SPRITES = {      # key: (builder, tileNames label)
    'home-tatami-green_w': (tatami('green', 'w'), 'home-tatami'),
    'home-tatami-green_e': (tatami('green', 'e'), 'home-tatami'),
    'home-tatami-gold_w': (tatami('gold', 'w'), 'home-tatami'),
    'home-tatami-gold_e': (tatami('gold', 'e'), 'home-tatami'),
    'home-genkan_0_0': (genkan, 'home-genkan'),
    'home-agari_0_0': (agari, 'home-agari'),
    'home-wall-sand_0_0': (plaster('sand'), 'home-wall'),
    'home-wall-moss_0_0': (plaster('moss'), 'home-wall'),
    'home-wall-shoji_0_0': (shoji, 'home-wall-shoji'),
    'home-wall-fusuma_0_0': (fusuma, 'home-wall-fusuma'),
    'home-wall-window-sand_0_0': (wall_window('sand'), 'home-wall-window'),
    'home-wall-window-moss_0_0': (wall_window('moss'), 'home-wall-window'),
    'home-tokonoma_0_0': (tokonoma, 'home-tokonoma'),
    'home-tansu_0_0': (tansu, 'home-tansu'),
    'home-bookshelf_0_0': (bookshelf, 'home-bookshelf'),
    'home-tv_0_0': (tv, 'home-tv'),
    'home-fridge_0_0': (fridge, 'home-fridge'),
    'home-kitchen_0_0': (kitchen, 'home-kitchen'),
    'home-kotatsu-red_0_0': (kotatsu(RED, RED_HI, RED_LO), 'home-kotatsu'),
    'home-kotatsu-indigo_0_0': (kotatsu(INDIGO, INDIGO_HI, INDIGO_LO), 'home-kotatsu'),
    'home-table_0_0': (low_table, 'home-table'),
    'home-irori_0_0': (irori, 'home-irori'),
    'home-futon-blue_0_0': (futon(SKY, SKY_HI, SKY_LO), 'home-futon'),
    'home-futon-rose_0_0': (futon(ROSE, ROSE_HI, ROSE_LO), 'home-futon'),
    'home-bed_0_0': (bed, 'home-bed'),
    'home-stove_0_0': (stove, 'home-stove'),
    'home-andon_0_0': (andon, 'home-andon'),
    'home-getabako_0_0': (getabako, 'home-getabako'),
    'home-zabuton-red_0_0': (zabuton(RED, RED_HI, RED_LO), 'home-zabuton'),
    'home-zabuton-indigo_0_0': (zabuton(INDIGO, INDIGO_HI, INDIGO_LO), 'home-zabuton'),
    'home-zabuton-green_0_0': (zabuton(GREEN, GREEN_HI, GREEN_LO), 'home-zabuton'),
    'home-shoes-a_0_0': (shoes([(4, 5, INDIGO, WHITE, False), (18, 16, RED, WOOD, True)]), 'home-shoes'),
    'home-shoes-b_0_0': (shoes([(17, 4, RED_LO, STONE_DK, False), (3, 17, GREEN, WHITE, False)]), 'home-shoes'),
    'home-doormat_0_0': (doormat, 'home-doormat'),
    'lobby-floor_a': (lobby_floor('a'), 'lobby-floor'),
    'lobby-floor_b': (lobby_floor('b'), 'lobby-floor'),
    'lobby-mat_0_0': (lobby_mat, 'lobby-mat'),
    'lobby-wall_0_0': (lobby_wall, 'lobby-wall'),
    'lobby-lift_0_0': (lobby_lift, 'lobby-lift'),
    'lobby-directory_0_0': (lobby_directory, 'lobby-directory'),
    'lobby-desk_0_0': (lobby_desk, 'lobby-desk'),
    'lobby-sofa_0_0': (lobby_sofa(False), 'lobby-sofa'),
    'lobby-sofa-back_0_0': (lobby_sofa(True), 'lobby-sofa'),
    'lobby-table_0_0': (lobby_table, 'lobby-table'),
    'lobby-plant_0_0': (lobby_plant, 'lobby-plant'),
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
    print(f'{len(built)} home and lobby sprites written')

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        ims = list(built.items())
        sheet = Image.new('RGBA', (1400, 600), rgb('c3c98c'))
        x = y = 12
        row_h = 0
        for key, im in ims:
            if x + im.width + 12 > sheet.width:
                x, y, row_h = 12, y + row_h + 12, 0
            sheet.alpha_composite(im, (x, y)); x += im.width + 12
            row_h = max(row_h, im.height)
        sheet.crop((0, 0, sheet.width, y + row_h + 12)).save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
