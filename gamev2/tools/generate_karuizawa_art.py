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

That is all of it for now. The falls, the larches and the corn stall are added
to SPRITES by the tickets that build them.

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE generate_karuizawa.py:
    python3 tools/generate_karuizawa_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image

from generate_hokkaido import (rgb, canvas, outline, tiles,
                               CREAM, CREAM_LO, CREAM_DK, WHITE, WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               RED, RED_HI, RED_LO, RED_DK, GLASS_DK, NAVY, GOLD)

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
WARM, AMBER = 0xf6dc8c, 0xffb366
GLOW = {
    'karuizawa-shop-bakery_0_0': [{'x': 0.75, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},        # the bread window
                                  {'x': 1.85, 'y': 2.8, 'r': 1.0, 'ry': 0.8, 'color': WARM, 'a': 0.5}],   # the door glass, the east window
    'karuizawa-shop-jam_0_0': [{'x': 0.67, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},           # the west window of jars
                               {'x': 2.3, 'y': 2.9, 'r': 0.9, 'color': WARM, 'a': 0.5},            # the east one
                               {'x': 1.5, 'y': 2.85, 'r': 0.6, 'color': WARM, 'a': 0.4}],          # the door glass
    'karuizawa-shop-lounge_0_0': [{'x': 0.66, 'y': 2.5, 'r': 0.9, 'color': AMBER, 'a': 0.55},      # the window of bottles
                                  {'x': 2.0, 'y': 2.5, 'r': 0.6, 'color': AMBER, 'a': 0.6}],       # the lantern by the door
}

SPRITES = {      # key: (builder, scale, tileNames label)
    'karuizawa-fingerpost_0_0': (fingerpost, 2, 'karuizawa-fingerpost'),
    'karuizawa-shop-bakery_0_0': (shop_bakery, 2, 'karuizawa-shop-bakery'),
    'karuizawa-shop-jam_0_0': (shop_jam, 2, 'karuizawa-shop-jam'),
    'karuizawa-shop-lounge_0_0': (shop_lounge, 2, 'karuizawa-shop-lounge'),
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
