#!/usr/bin/env python3
"""generate_sendai_art.py — draw the Sendai sprites (issue #66).

No asset pack has Sendai, Matsushima or the Nikka distillery, so they are
drawn here the way tools/generate_hokkaido.py draws Hokkaido: shaded pixel art
in the GuttyKreum palette, at half size and pixel-doubled, with a 1px ink
outline. Nothing here is a white line-art placeholder.

  sendai-masamune_0_0        3x4   Date Masamune on horseback, in bronze, on a
                                    tall stone plinth (the Aoba Castle statue)
  sendai-zuihoden_0_0        7x5   Zuihoden, his mausoleum: black lacquer walls,
                                    gold fittings, a band of painted brackets
                                    under a heavy tiled roof, on a stone base
  sendai-gate_0_0            4x3   a samurai gate: two posts under a tiled gable
                                    roof, two cells of open gateway between them
  sendai-earthen-wall_0_0    1x2   an earthen wall under a tiled coping; tiles
                                    side by side into a run of any length
  sendai-pine_0_0            2x3   a Japanese black pine (cloud-pruned pads)
  sendai-cedar_0_0           2x4   a tall cedar, for Zuihoden's hillside
  sendai-maple_0_0           2x3   a maple in autumn colour (Sakunami, late October)
  sendai-stone-lantern_0_0   1x2   an ishidoro stone lantern
  sendai-pub_0_0             5x5   the British-style pub the baseball was watched
                                    in: red fascia, dark wood front, lit windows
  sendai-kiln_0_0            5x6   the distillery's red-brick kiln house with its
                                    pagoda-roofed kiln tower (Nikka Miyagikyo)
  sendai-barrels_0_0         2x2   three whisky casks, stacked
  matsushima-islet_0_0       3x2   a pale rock islet, undercut at the waterline,
                                    with pines on top
  matsushima-islet-small_0_0 2x2   a small one with a single pine
  matsushima-ball-rock_0_0   2x2   "a rock with a ball on top" (post 487)
  matsushima-ferry_0_0       5x2   the two-deck sightseeing boat, moored
  matsushima-pier_0_0        5x1   the timber pier it is moored at (flat:
                                    Non-Collidables + depthBias, you walk ON it)
  pond-autotile_edge-w       1x1   the pond set's missing west bank (edge-e
                                    mirrored), so water can have a shore down
                                    its west side - the bay's

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_sendai.py:
    python3 tools/generate_sendai_art.py [--preview out.png]
"""
import json
import math
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (C, CLEAR, rgb, canvas, outline, tiles, window,
                               INK, RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)

LACQUER, LACQUER_HI, LACQUER_LO = rgb('23232e'), rgb('3b3d52'), rgb('15151c')
GOLD_HI, GOLD_LO = rgb('f0d98c'), rgb('8f7440')
SLATE, SLATE_HI, SLATE_LO = rgb('3f4c60'), rgb('62748c'), rgb('2a3344')
EARTH, EARTH_HI, EARTH_LO, EARTH_DK = rgb('d6b88e'), rgb('e8d2ae'), rgb('b8946a'), rgb('8a6c50')
BRONZE, BRONZE_HI, BRONZE_LO = rgb('4f6359'), rgb('7d9584'), rgb('2f3d3a')
PINE, PINE_HI, PINE_LO, PINE_DK = rgb('3a6b55'), rgb('6aa56a'), rgb('2a4f47'), rgb('1c3636')
BARK, BARK_LO = rgb('7a5645'), rgb('513a33')
CEDAR, CEDAR_HI, CEDAR_LO = rgb('2f5a4c'), rgb('4f8468'), rgb('1f3f3c')
MAPLE, MAPLE_HI, MAPLE_LO, MAPLE_OR = rgb('cf5a45'), rgb('ee8a58'), rgb('9a3b33'), rgb('f0a84a')
ROCK, ROCK_HI, ROCK_LO, ROCK_DK = rgb('d9cfba'), rgb('f0e9d8'), rgb('b3a48c'), rgb('85776a')
BRICK, BRICK_HI, BRICK_LO = rgb('b55a40'), rgb('d07a5c'), rgb('8a4030')
HULL, HULL_LO = rgb('f4f6fa'), rgb('c4d0e2')
BLUE, BLUE_DK = rgb('4b6396'), rgb('2c3d6a')
PUB_GREEN, PUB_GREEN_HI, PUB_GREEN_LO = rgb('2f4a44'), rgb('46695c'), rgb('1e302f')
LIT, LIT_HI = rgb('f2c66a'), rgb('fbe6a4')

FONT = {     # 5x7 capitals, hand-set (no font file needed)
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
}


def text(d, s, x, y, fill, gap=1):
    for ch in s:
        for gy, row in enumerate(FONT[ch]):
            for gx, c in enumerate(row):
                if c == '#':
                    d.point((x + gx, y + gy), fill=fill)
        x += 5 + gap
    return x


def text_width(s, gap=1):
    return len(s) * (5 + gap) - gap


def roof_rows(y0, y1, top, bottom):
    """Scanlines of a roof that widens from `top` (x0, x1) at y0 to `bottom` at y1."""
    out = []
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        out.append((y, round(top[0] + (bottom[0] - top[0]) * t), round(top[1] + (bottom[1] - top[1]) * t)))
    return out


def tiled_roof(d, rows, light=SLATE, dark=SLATE_LO, hi=SLATE_HI):
    tiles(d, rows, light, dark)
    for y, x0, x1 in rows:
        d.point((x0, y), fill=hi); d.point((x0 + 1, y), fill=hi)
        d.point((x1, y), fill=dark); d.point((x1 - 1, y), fill=dark)


def blob(d, cx, cy, rx, ry, base, hi, lo, seed=0):
    """A foliage pad: an ellipse lit from the upper left, with a dappled edge."""
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=base)
    d.ellipse([cx - rx + 1, cy - ry, cx + rx - 3, cy + ry - 3], fill=hi)
    d.ellipse([cx - rx + 3, cy - ry + 2, cx + rx - 1, cy + ry], fill=base)
    d.chord([cx - rx, cy - ry, cx + rx, cy + ry], 20, 160, fill=lo)
    for i in range(rx):
        px = cx - rx + 2 + (i * 5 + seed * 3) % max(1, 2 * rx - 3)
        py = cy - ry + 1 + (i * 7 + seed) % max(1, 2 * ry - 2)
        inside = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 < 0.8
        if inside:
            d.point((px, py), fill=hi if (i + seed) % 3 else lo)


# ------------------------------------------------------------------------------
def masamune():
    im, d = canvas(3, 4)                 # 96 x 128
    # ---- the plinth: dressed stone, battered, with a cap -----------------------
    for y in range(66, 126):
        w = 26 + (y - 66) * 6 // 60
        d.line([(48 - w, y), (47 + w, y)], fill=STONE)
        d.point((48 - w, y), fill=WHITE); d.point((48 - w + 1, y), fill=WHITE)
        d.line([(47 + w - 5, y), (47 + w, y)], fill=STONE_LO)
    for y in range(74, 126, 10):                                  # courses
        d.line([(20, y), (76, y)], fill=STONE_LO)
    for i, y in enumerate(range(66, 126, 10)):                    # joints, running bond
        for x in range(26 + (i % 2) * 7, 74, 14):
            if 48 - 26 < x < 47 + 26:
                d.line([(x, y + 1), (x, y + 9)], fill=STONE_LO)
    d.rectangle([17, 60, 78, 66], fill=STONE); d.line([(17, 60), (78, 60)], fill=WHITE)
    d.line([(17, 66), (78, 66)], fill=STONE_DK)
    d.rectangle([14, 124, 81, 127], fill=STONE_LO); d.line([(14, 124), (81, 124)], fill=STONE)
    d.rectangle([36, 88, 59, 102], fill=BRONZE_LO)                # the bronze plaque
    d.rectangle([37, 89, 58, 101], fill=BRONZE)
    for y in (92, 95, 98):
        d.line([(40, y), (55, y)], fill=BRONZE_HI)

    # ---- the horse, facing right ----------------------------------------------
    d.rectangle([24, 57, 72, 60], fill=BRONZE_LO)                 # the bronze base
    d.line([(24, 57), (72, 57)], fill=BRONZE)
    d.ellipse([27, 30, 66, 47], fill=BRONZE)                      # barrel
    d.ellipse([27, 30, 44, 46], fill=BRONZE)                      # haunch
    d.chord([27, 30, 66, 47], 10, 170, fill=BRONZE_LO)            # belly in shade
    d.polygon([(58, 34), (66, 20), (72, 16), (75, 22), (68, 38)], fill=BRONZE)   # neck
    d.polygon([(70, 14), (80, 18), (84, 25), (80, 27), (72, 23)], fill=BRONZE)   # head
    d.point((78, 20), fill=BRONZE_LO); d.line([(70, 13), (71, 10)], fill=BRONZE)  # eye, ear
    d.line([(64, 20), (70, 14)], fill=BRONZE_LO, width=2)         # mane
    for x0, x1, lift in ((31, 30, 0), (38, 39, 0), (58, 60, 0), (64, 70, 6)):    # legs
        d.line([(x0, 44), (x1, 56 - lift)], fill=BRONZE, width=3)
        d.line([(x0 + 2, 45), (x1 + 2, 56 - lift)], fill=BRONZE_LO)
        d.rectangle([x1 - 1, 55 - lift, x1 + 3, 57 - lift], fill=BRONZE_LO)      # hoof
    d.line([(28, 34), (22, 40), (21, 50)], fill=BRONZE, width=3)   # tail
    d.line([(23, 42), (22, 50)], fill=BRONZE_LO)
    d.line([(30, 31), (62, 31)], fill=BRONZE_HI); d.line([(66, 20), (71, 16)], fill=BRONZE_HI)

    # ---- the rider: armour, a sword at his side, the crescent-moon helmet ------
    d.polygon([(42, 32), (40, 44), (46, 48), (50, 42), (52, 32)], fill=BRONZE_LO)   # leg + saddle skirt
    d.rectangle([40, 16, 53, 33], fill=BRONZE)                    # cuirass
    d.line([(40, 16), (40, 33)], fill=BRONZE_HI); d.line([(53, 17), (53, 33)], fill=BRONZE_LO)
    for y in (21, 25, 29):
        d.line([(41, y), (52, y)], fill=BRONZE_LO)                # the lames of the armour
    d.line([(52, 20), (60, 28), (64, 26)], fill=BRONZE, width=2)  # arm to the reins
    d.line([(64, 26), (70, 20)], fill=BRONZE_LO)                  # reins
    d.line([(40, 28), (30, 36)], fill=BRONZE_LO, width=2)         # the scabbard
    d.rectangle([42, 8, 51, 16], fill=BRONZE)                     # head
    d.rectangle([40, 6, 53, 10], fill=BRONZE_LO)                  # helmet bowl
    d.line([(38, 11), (55, 11)], fill=BRONZE_LO)                  # its brim
    d.rectangle([44, 12, 50, 14], fill=BRONZE_HI)                 # the face in the light
    d.arc([36, -8, 58, 8], 15, 165, fill=GOLD, width=2)           # the crescent crest
    d.point((37, 2), fill=GOLD_HI); d.point((57, 2), fill=GOLD_HI)
    outline(im)
    return im


# ------------------------------------------------------------------------------
def zuihoden():
    im, d = canvas(7, 5)                 # 224 x 160
    cx = 112
    # ---- the stone base and the steps -----------------------------------------
    d.rectangle([10, 144, 213, 157], fill=STONE)
    d.line([(10, 144), (213, 144)], fill=WHITE)
    d.rectangle([10, 153, 213, 157], fill=STONE_LO)
    for x in range(22, 212, 16):
        d.line([(x, 146), (x, 152)], fill=STONE_LO)
    d.rectangle([92, 142, 131, 157], fill=STONE)
    for y in (145, 149, 153):
        d.line([(92, y), (131, y)], fill=STONE_LO)
    d.line([(92, 142), (131, 142)], fill=WHITE)

    # ---- the hall: black lacquer between gold-capped pillars -------------------
    d.rectangle([22, 96, 201, 143], fill=LACQUER)
    d.rectangle([22, 96, 201, 98], fill=LACQUER_HI)
    d.rectangle([22, 138, 201, 143], fill=LACQUER_LO)
    for x in (22, 52, 82, 136, 166, 196):                         # pillars
        d.rectangle([x, 96, x + 5, 143], fill=LACQUER_HI)
        d.line([(x + 5, 96), (x + 5, 143)], fill=LACQUER_LO)
        d.rectangle([x - 1, 96, x + 6, 99], fill=GOLD); d.line([(x - 1, 96), (x + 6, 96)], fill=GOLD_HI)
        d.rectangle([x - 1, 139, x + 6, 142], fill=GOLD); d.line([(x - 1, 142), (x + 6, 142)], fill=GOLD_LO)
    for x0 in (30, 60, 144, 174):                                 # panelled bays: gold-framed lattice
        d.rectangle([x0, 104, x0 + 19, 134], fill=GOLD_LO)
        d.rectangle([x0 + 1, 105, x0 + 18, 133], fill=LACQUER_LO)
        for x in range(x0 + 3, x0 + 18, 3):
            d.line([(x, 106), (x, 132)], fill=GOLD_LO)
        d.line([(x0 + 1, 119), (x0 + 18, 119)], fill=GOLD)
        d.point((x0 + 9, 119), fill=GOLD_HI); d.point((x0 + 10, 119), fill=GOLD_HI)
    # the doors: red lacquer frame, black leaves, a gold crest on each
    d.rectangle([90, 100, 133, 143], fill=RED_LO)
    d.rectangle([92, 102, 131, 143], fill=LACQUER_LO)
    d.rectangle([93, 103, 110, 143], fill=LACQUER); d.rectangle([113, 103, 130, 143], fill=LACQUER)
    for mx in (101, 121):
        d.ellipse([mx - 5, 112, mx + 5, 122], fill=GOLD)
        d.ellipse([mx - 3, 114, mx + 3, 120], fill=LACQUER)
        d.point((mx, 117), fill=GOLD_HI)
        d.rectangle([mx - 6, 130, mx + 6, 131], fill=GOLD_LO)
    d.rectangle([111, 103, 112, 143], fill=GOLD_LO)
    d.point((109, 126), fill=GOLD_HI); d.point((114, 126), fill=GOLD_HI)

    # ---- the painted bracket band under the eaves ------------------------------
    d.rectangle([16, 84, 207, 95], fill=LACQUER_LO)
    paint = (RED, GOLD, GREEN_HI, GLASS_HI, GOLD, RED)
    for i, x in enumerate(range(18, 206, 6)):
        col = paint[i % len(paint)]
        d.rectangle([x, 86, x + 3, 89], fill=col)
        d.rectangle([x + 1, 90, x + 4, 93], fill=paint[(i + 2) % len(paint)])
        d.point((x, 86), fill=WHITE)
    d.line([(16, 84), (207, 84)], fill=GOLD); d.line([(16, 95), (207, 95)], fill=GOLD_LO)

    # ---- the roof: a heavy hipped roof, eaves turned up at the corners ---------
    rows = roof_rows(26, 80, (54, 169), (2, 221))
    tiled_roof(d, rows)
    for y, x0, x1 in rows:                                        # the ribs of the tiling
        for x in range(x0 + 4, x1 - 2, 9):
            if (y // 4) % 2 == 0:
                d.point((x, y), fill=SLATE_HI)
    d.rectangle([0, 80, 223, 83], fill=SLATE_LO)                  # eaves
    d.line([(0, 83), (223, 83)], fill=RED_LO)                     # the red rafter ends
    for x in range(3, 222, 5):
        d.point((x, 83), fill=GOLD)
    for sx, x in ((1, 0), (-1, 223)):                             # upturned corners with gold tips
        d.polygon([(x, 80), (x + sx * 8, 80), (x, 72)], fill=SLATE)
        d.rectangle([x if sx > 0 else x - 2, 71, x + 2 if sx > 0 else x, 74], fill=GOLD)
    d.rectangle([52, 20, 171, 26], fill=SLATE_LO)                 # the ridge
    d.line([(52, 20), (171, 20)], fill=SLATE_HI)
    for x in range(58, 168, 12):
        d.rectangle([x, 22, x + 3, 24], fill=GOLD)
    for x0 in (46, 166):                                          # gold ridge-end ornaments
        d.polygon([(x0, 26), (x0 + 11, 26), (x0 + 11, 12), (x0 + 6, 8), (x0 + 3, 14)], fill=GOLD)
        d.line([(x0 + 4, 14), (x0 + 4, 25)], fill=GOLD_HI)
        d.line([(x0 + 10, 12), (x0 + 10, 25)], fill=GOLD_LO)
    # the front gable over the doors, with the crest of the Date
    for y in range(44, 81):
        w = (y - 44) * 34 // 36
        d.line([(cx - 2 - w, y), (cx + 1 + w, y)], fill=LACQUER if y > 50 else SLATE_LO)
    for y in range(42, 81):                                       # its gold-edged bargeboards
        w = (y - 42) * 36 // 38
        d.line([(cx - 5 - w, y), (cx - 2 - w, y)], fill=SLATE_HI)
        d.line([(cx + 1 + w, y), (cx + 4 + w, y)], fill=SLATE_LO)
        d.point((cx - 2 - w, y), fill=GOLD); d.point((cx + 1 + w, y), fill=GOLD_LO)
    d.ellipse([cx - 9, 58, cx + 8, 75], fill=GOLD)
    d.ellipse([cx - 6, 61, cx + 5, 72], fill=LACQUER)
    d.ellipse([cx - 3, 64, cx + 2, 69], fill=GOLD_HI)
    d.rectangle([cx - 2, 36, cx + 1, 44], fill=GOLD)              # finial
    outline(im)
    return im


# ------------------------------------------------------------------------------
def coping(d, x0, x1, y):
    """A wall's tiled coping, 14px deep from y: ridge, a fall of tiles, the eave."""
    d.rectangle([x0, y, x1, y + 2], fill=SLATE_LO)
    d.line([(x0, y), (x1, y)], fill=SLATE_HI)
    tiles(d, [(yy, x0, x1) for yy in range(y + 3, y + 12)], SLATE, SLATE_LO, step=4)
    d.rectangle([x0, y + 11, x1, y + 12], fill=SLATE_LO)
    for x in range(x0 + 1, x1, 4):
        d.point((x, y + 12), fill=SLATE_HI)                       # the round tile ends
    d.line([(x0, y + 13), (x1, y + 13)], fill=EARTH_DK)           # its shadow on the wall


def plaster(d, x0, x1, y0, y1):
    d.rectangle([x0, y0, x1, y1], fill=EARTH)
    d.line([(x0, y0), (x1, y0)], fill=EARTH_LO)
    for i, y in enumerate(range(y0 + 7, y1 - 6, 9)):              # the courses of rammed earth
        d.line([(x0, y), (x1, y)], fill=EARTH_LO)
        for x in range(x0 + (3 if i % 2 else 9), x1, 13):
            d.point((x, y - 3), fill=EARTH_HI); d.point((x + 5, y + 3), fill=EARTH_LO)


def footing(d, x0, x1, y0, y1):
    d.rectangle([x0, y0, x1, y1], fill=STONE_LO)
    d.line([(x0, y0), (x1, y0)], fill=STONE)
    for x in range(x0 + 5, x1, 11):
        d.line([(x, y0 + 1), (x, y1)], fill=STONE_DK)


def earthen_wall():
    im, d = canvas(1, 2)                 # 32 x 64: the wall fills the lower cell and a half
    coping(d, 0, 31, 12)
    plaster(d, 0, 31, 26, 55)
    footing(d, 0, 31, 56, 63)
    outline(im)
    return im


def gate():
    im, d = canvas(4, 3)                 # 128 x 96
    # wing walls joining the earthen wall either side
    for x0, x1 in ((0, 21), (106, 127)):
        coping(d, x0, x1, 44)
        plaster(d, x0, x1, 58, 87)
        footing(d, x0, x1, 88, 95)
    # the posts and the lintel
    for x0 in (22, 96):
        d.rectangle([x0, 40, x0 + 9, 95], fill=WOOD_LO)
        d.line([(x0, 40), (x0, 95)], fill=WOOD); d.line([(x0 + 1, 40), (x0 + 1, 95)], fill=WOOD)
        d.line([(x0 + 9, 40), (x0 + 9, 95)], fill=WOOD_DK)
        d.rectangle([x0 - 1, 90, x0 + 10, 95], fill=STONE_LO); d.line([(x0 - 1, 90), (x0 + 10, 90)], fill=STONE)
        d.rectangle([x0, 60, x0 + 9, 62], fill=LACQUER_LO)        # iron bands
        d.rectangle([x0, 78, x0 + 9, 80], fill=LACQUER_LO)
    d.rectangle([18, 38, 109, 47], fill=WOOD_LO)
    d.line([(18, 38), (109, 38)], fill=WOOD); d.line([(18, 47), (109, 47)], fill=WOOD_DK)
    for x in range(26, 108, 12):
        d.rectangle([x, 41, x + 1, 44], fill=LACQUER_LO)          # nail heads
    # the open leaves, folded back against the posts
    for x0, x1 in ((32, 37), (90, 95)):
        d.rectangle([x0, 48, x1, 93], fill=WOOD_DK)
        d.line([(x0 + 2, 50), (x0 + 2, 92)], fill=WOOD_LO)
        d.point((x0 + 3, 70), fill=GOLD)
    # the roof: a tiled gable, ridge on top, wide eaves
    rows = roof_rows(10, 36, (20, 107), (4, 123))
    tiled_roof(d, rows)
    d.rectangle([4, 36, 123, 38], fill=SLATE_LO)
    for x in range(6, 122, 4):
        d.point((x, 38), fill=SLATE_HI)
    d.rectangle([18, 5, 109, 10], fill=SLATE_LO); d.line([(18, 5), (109, 5)], fill=SLATE_HI)
    for x0 in (14, 108):
        d.rectangle([x0, 2, x0 + 5, 10], fill=SLATE); d.point((x0 + 1, 3), fill=SLATE_HI)
    d.ellipse([60, 14, 67, 21], fill=GOLD); d.ellipse([62, 16, 65, 19], fill=SLATE_LO)   # the crest
    outline(im)
    return im


# ------------------------------------------------------------------------------
def trunk(d, pts, w=4):
    d.line(pts, fill=BARK, width=w)
    d.line([(x + w // 2, y) for x, y in pts], fill=BARK_LO)


def pine():
    im, d = canvas(2, 3)                 # 64 x 96
    d.ellipse([18, 86, 50, 94], fill=rgb('3a5f66', 150))         # ground shadow
    trunk(d, [(32, 92), (30, 74), (36, 58), (30, 44), (33, 30)], 5)
    trunk(d, [(34, 60), (46, 52)], 3)
    trunk(d, [(31, 46), (18, 42)], 3)
    for cx, cy, rx, ry, s in ((16, 40, 14, 7, 1), (48, 50, 13, 6, 2), (34, 28, 17, 8, 3),
                              (22, 22, 12, 6, 4), (44, 16, 12, 6, 5), (32, 10, 11, 6, 6)):
        blob(d, cx, cy, rx, ry, PINE, PINE_HI, PINE_LO, s)
        d.line([(cx - rx + 3, cy + ry - 1), (cx + rx - 3, cy + ry - 1)], fill=PINE_DK)
    outline(im)
    return im


def cedar():
    im, d = canvas(2, 4)                 # 64 x 128
    d.ellipse([16, 118, 48, 126], fill=rgb('3a5f66', 150))
    d.rectangle([29, 96, 35, 124], fill=BARK); d.line([(35, 96), (35, 124)], fill=BARK_LO)
    d.line([(29, 96), (29, 124)], fill=rgb('9a7460'))
    for i, y in enumerate(range(8, 104, 8)):                      # drooping tiers, widening downwards
        w = 6 + i * 2 if i < 9 else 24 - (i - 9) * 3
        d.polygon([(32, y - 6), (32 - w, y + 10), (32 + w, y + 10)], fill=CEDAR)
        d.polygon([(32, y - 6), (32 - w, y + 10), (32 - w // 3, y + 10)], fill=CEDAR_HI)
        d.polygon([(32 + w // 2, y + 4), (32 + w, y + 10), (32 + w // 3, y + 10)], fill=CEDAR_LO)
        for x in range(32 - w + 2, 32 + w - 1, 4):
            d.point((x, y + 10), fill=CEDAR_LO); d.point((x + 1, y + 11), fill=CEDAR)
    d.polygon([(32, 0), (28, 8), (36, 8)], fill=CEDAR_HI)
    outline(im)
    return im


def maple():
    im, d = canvas(2, 3)                 # 64 x 96
    d.ellipse([16, 86, 50, 94], fill=rgb('3a5f66', 150))
    trunk(d, [(32, 92), (32, 62)], 5)
    trunk(d, [(32, 68), (22, 54)], 3); trunk(d, [(33, 66), (44, 52)], 3)
    for cx, cy, rx, ry, s, (a, b, c) in (
            (20, 46, 15, 12, 1, (MAPLE, MAPLE_HI, MAPLE_LO)), (45, 44, 15, 12, 2, (MAPLE_HI, MAPLE_OR, MAPLE)),
            (32, 28, 19, 14, 3, (MAPLE, MAPLE_OR, MAPLE_LO)), (20, 20, 11, 9, 4, (MAPLE_HI, MAPLE_OR, MAPLE)),
            (44, 18, 12, 9, 5, (MAPLE, MAPLE_HI, MAPLE_LO))):
        blob(d, cx, cy, rx, ry, a, b, c, s)
    for i in range(26):                                           # loose leaves of the other colours
        x, y = 8 + (i * 13) % 48, 10 + (i * 29) % 46
        if im.getpixel((x, y))[3]:
            d.point((x, y), fill=(MAPLE_OR, MAPLE_LO, AMBER)[i % 3])
    outline(im)
    return im


def stone_lantern():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([8, 58, 23, 62], fill=STONE_LO); d.line([(8, 58), (23, 58)], fill=STONE)      # base
    d.rectangle([13, 38, 18, 58], fill=STONE); d.line([(18, 38), (18, 58)], fill=STONE_LO)    # shaft
    d.line([(13, 38), (13, 58)], fill=WHITE)
    d.rectangle([9, 34, 22, 38], fill=STONE); d.line([(9, 38), (22, 38)], fill=STONE_DK)      # platform
    d.rectangle([10, 22, 21, 34], fill=STONE_LO)                                              # the light box
    d.rectangle([12, 24, 19, 32], fill=LIT); d.rectangle([13, 25, 16, 28], fill=LIT_HI)
    d.line([(15, 24), (15, 32)], fill=STONE_DK); d.line([(16, 24), (16, 32)], fill=STONE_DK)
    d.polygon([(4, 22), (27, 22), (20, 13), (11, 13)], fill=STONE)                            # the roof
    d.line([(11, 13), (4, 22)], fill=WHITE); d.line([(20, 13), (27, 22)], fill=STONE_LO)
    d.line([(4, 22), (27, 22)], fill=STONE_DK)
    d.rectangle([14, 8, 17, 13], fill=STONE); d.rectangle([15, 5, 16, 8], fill=STONE_LO)      # the jewel
    outline(im)
    return im


# ------------------------------------------------------------------------------
def lit_window(d, x0, y0, x1, y1, frame):
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=LIT)
    d.rectangle([x0 + 2, y0 + 2, (x0 + x1) // 2 - 1, (y0 + y1) // 2 - 1], fill=LIT_HI)
    d.line([((x0 + x1) // 2, y0 + 1), ((x0 + x1) // 2, y1 - 1)], fill=frame)
    d.line([(x0 + 1, (y0 + y1) // 2), (x1 - 1, (y0 + y1) // 2)], fill=frame)


def pub():
    im, d = canvas(5, 5)                 # 160 x 160
    # ---- the upper storey: cream render, sash windows, a parapet ---------------
    d.rectangle([4, 20, 155, 84], fill=CREAM)
    for y in range(26, 84, 6):
        d.line([(4, y), (155, y)], fill=CREAM_LO)
    d.line([(4, 20), (4, 84)], fill=WHITE); d.rectangle([150, 20, 155, 84], fill=CREAM_LO)
    d.rectangle([2, 12, 157, 20], fill=CREAM_DK); d.line([(2, 12), (157, 12)], fill=CREAM)
    d.rectangle([2, 18, 157, 20], fill=WOOD_DK)
    for x in (16, 46, 98, 128):
        window(d, x, 34, x + 15, 62, frame=PUB_GREEN_LO)
        d.rectangle([x - 1, 64, x + 16, 71], fill=PUB_GREEN)      # a window box of flowers
        for i in range(x, x + 16, 3):
            d.point((i, 64), fill=(RED_HI, AMBER, WHITE)[(i // 3) % 3]); d.point((i + 1, 65), fill=GREEN_HI)
    # the hanging sign on its bracket
    d.line([(72, 30), (87, 30)], fill=LACQUER_LO); d.line([(79, 30), (79, 36)], fill=LACQUER_LO)
    d.rectangle([70, 36, 89, 60], fill=RED_DK); d.rectangle([71, 37, 88, 59], fill=RED)
    d.ellipse([75, 42, 84, 51], fill=GOLD); d.rectangle([78, 51, 81, 55], fill=GOLD)
    d.rectangle([75, 55, 84, 56], fill=GOLD_HI)                   # a pint, on the board
    # ---- the fascia: red, gold-lined, white capitals ---------------------------
    d.rectangle([0, 84, 159, 104], fill=RED)
    d.rectangle([0, 84, 159, 86], fill=RED_HI); d.rectangle([0, 102, 159, 104], fill=RED_DK)
    d.line([(3, 88), (156, 88)], fill=GOLD); d.line([(3, 100), (156, 100)], fill=GOLD)
    label = 'PUB'
    x = text(d, label, 80 - (text_width(label, 3)) // 2, 91, WHITE, gap=3)
    for sx in (40, 114):                                          # a gold star either side
        d.polygon([(sx, 90), (sx + 2, 93), (sx + 5, 94), (sx + 2, 96), (sx + 3, 99),
                   (sx, 97), (sx - 3, 99), (sx - 2, 96), (sx - 5, 94), (sx - 2, 93)], fill=GOLD_HI)
    # ---- the ground floor: dark green joinery, lit windows, the door -----------
    d.rectangle([2, 105, 157, 157], fill=PUB_GREEN)
    d.rectangle([2, 105, 157, 107], fill=PUB_GREEN_LO)
    d.rectangle([2, 146, 157, 157], fill=PUB_GREEN_LO)
    d.line([(2, 146), (157, 146)], fill=PUB_GREEN_HI)
    for x in (2, 60, 96, 154):                                    # pilasters
        d.rectangle([x, 105, x + 3, 157], fill=PUB_GREEN_HI); d.line([(x + 3, 105), (x + 3, 157)], fill=PUB_GREEN_LO)
        d.rectangle([x, 108, x + 3, 110], fill=GOLD)
    for x0 in (10, 102):
        lit_window(d, x0, 112, x0 + 45, 142, PUB_GREEN_LO)
        d.line([(x0 + 15, 113), (x0 + 15, 141)], fill=PUB_GREEN_LO)
        d.line([(x0 + 30, 113), (x0 + 30, 141)], fill=PUB_GREEN_LO)
    d.rectangle([28, 118, 39, 126], fill=GREEN_HI)                # the baseball, on the TV inside
    d.rectangle([28, 118, 39, 119], fill=LACQUER_LO); d.point((34, 122), fill=WHITE)
    d.rectangle([66, 110, 93, 157], fill=WOOD_DK)                 # the door
    d.rectangle([68, 112, 79, 157], fill=WOOD_LO); d.rectangle([81, 112, 91, 157], fill=WOOD_LO)
    d.rectangle([70, 115, 77, 132], fill=LIT); d.rectangle([83, 115, 89, 132], fill=LIT)
    d.point((78, 138), fill=GOLD_HI); d.point((82, 138), fill=GOLD_HI)
    for x in (62, 97):                                            # carriage lamps by the door
        d.rectangle([x - 2, 114, x + 1, 121], fill=LACQUER_LO); d.rectangle([x - 1, 115, x, 120], fill=LIT_HI)
    d.rectangle([0, 157, 159, 159], fill=STONE_LO)
    outline(im)
    return im


# ------------------------------------------------------------------------------
def bricks(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=BRICK)
    for i, y in enumerate(range(y0, y1 + 1, 4)):
        d.line([(x0, y + 3), (x1, y + 3)], fill=BRICK_LO)
        for x in range(x0 + (0 if i % 2 else 4), x1, 8):
            d.line([(x, y), (x, min(y1, y + 2))], fill=BRICK_LO)
        for x in range(x0 + 2 + (i * 5) % 8, x1, 16):
            d.point((x, y + 1), fill=BRICK_HI)
    d.line([(x0, y0), (x0, y1)], fill=BRICK_HI)
    d.rectangle([x1 - 3, y0, x1, y1], fill=BRICK_LO)


def kiln():
    im, d = canvas(5, 6)                 # 160 x 192
    cx = 80
    # ---- the long malt house: red brick, a slate roof ---------------------------
    bricks(d, 6, 128, 153, 185)
    d.rectangle([4, 184, 155, 189], fill=STONE_LO); d.line([(4, 184), (155, 184)], fill=STONE)
    rows = roof_rows(100, 128, (20, 139), (0, 159))
    tiled_roof(d, rows, RED_LO, RED_DK, RED)
    d.rectangle([0, 128, 159, 130], fill=RED_DK)
    for x in (14, 36, 110, 132):                                  # white-framed arched windows
        d.rectangle([x, 142, x + 13, 168], fill=WHITE)
        d.pieslice([x, 136, x + 13, 150], 180, 360, fill=WHITE)
        d.rectangle([x + 2, 144, x + 11, 166], fill=GLASS_DK)
        d.pieslice([x + 2, 138, x + 11, 150], 180, 360, fill=GLASS)
        d.line([(x + 6, 140), (x + 6, 166)], fill=WHITE); d.line([(x + 2, 154), (x + 11, 154)], fill=WHITE)
    d.rectangle([62, 146, 97, 185], fill=WHITE)                   # the doorway
    d.rectangle([65, 149, 94, 185], fill=WOOD_DK)
    d.rectangle([66, 150, 79, 185], fill=WOOD_LO); d.rectangle([81, 150, 93, 185], fill=WOOD_LO)
    d.point((78, 168), fill=GOLD); d.point((82, 168), fill=GOLD)
    d.rectangle([58, 134, 101, 145], fill=WHITE)                  # the name board
    d.rectangle([59, 135, 100, 144], fill=LACQUER)
    text(d, 'WHISKY', 80 - text_width('WHISKY') // 2, 136, GOLD_HI)
    # ---- the kiln tower rising out of the roof ---------------------------------
    bricks(d, 48, 62, 111, 128)
    d.rectangle([46, 60, 113, 63], fill=WHITE)                    # a white band course
    for x in (58, 88):
        d.rectangle([x, 76, x + 13, 100], fill=WHITE)
        d.rectangle([x + 2, 78, x + 11, 98], fill=GLASS_DK)
        for y in range(80, 98, 4):
            d.line([(x + 2, y), (x + 11, y)], fill=STONE_LO)      # louvres
    # the pagoda roof: a steep pyramid, a louvred lantern, a little cap on top
    rows = roof_rows(34, 60, (cx - 12, cx + 11), (38, 121))
    tiled_roof(d, rows, RED_LO, RED_DK, RED)
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            if x > cx + (y - 34) // 2:
                d.point((x, y), fill=RED_DK if (y % 4 == 3) else rgb('7c3a2c'))
    d.rectangle([36, 59, 123, 61], fill=RED_DK)
    d.rectangle([cx - 10, 22, cx + 9, 34], fill=CREAM_LO)
    for y in range(24, 34, 3):
        d.line([(cx - 9, y), (cx + 8, y)], fill=CREAM_DK)
    rows = roof_rows(10, 22, (cx - 3, cx + 2), (cx - 16, cx + 15))
    tiled_roof(d, rows, RED_LO, RED_DK, RED)
    d.rectangle([cx - 17, 21, cx + 16, 22], fill=RED_DK)
    d.rectangle([cx - 1, 2, cx, 10], fill=STONE_LO); d.rectangle([cx - 2, 4, cx + 1, 5], fill=GOLD)
    outline(im)
    return im


def barrels():
    im, d = canvas(2, 2)                 # 64 x 64

    def cask(cx, cy):
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=WOOD_LO)
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=WOOD)
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], outline=LACQUER_LO)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=WOOD_LO)
        for dx in (-5, 0, 5):
            d.line([(cx + dx, cy - 9), (cx + dx, cy + 9)], fill=WOOD_LO)
        d.point((cx, cy), fill=LACQUER_LO); d.point((cx - 5, cy - 6), fill=rgb('d8ae94'))

    d.ellipse([3, 54, 60, 63], fill=rgb('3a5f66', 150))
    cask(17, 46); cask(46, 46); cask(32, 22)
    d.rectangle([4, 58, 60, 61], fill=WOOD_DK)                    # the rack
    outline(im)
    return im


# ------------------------------------------------------------------------------
def rock(d, x0, x1, y0, y1, seed=0):
    """A Matsushima islet's rock: a pale tuff crag, uneven along the top, wider
    at the foot, banded, with the notch the sea has cut along its waterline."""
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, x1 - x0)
        edge = min(t, 1 - t)                                      # 0 at the ends
        top = y0 + (6 if edge < 0.06 else 3 if edge < 0.14 else 0) \
            + (1 if (x * 7 + seed * 5) % 11 < 3 else 0) - (1 if (x * 5 + seed) % 13 == 0 else 0)
        d.line([(x, top), (x, y1)], fill=ROCK)
        d.point((x, top), fill=ROCK_HI); d.point((x, top + 1), fill=ROCK_HI)
        if t > 0.72:
            d.line([(x, top + 2), (x, y1)], fill=ROCK_LO)         # the east face, in shade
        if t < 0.08:
            d.line([(x, top), (x, y1)], fill=ROCK_HI)
    for i, y in enumerate(range(y0 + 7, y1 - 5, 5)):              # the strata, broken
        for x in range(x0 + 3, x1 - 2):
            if (x + i * 5 + seed) % 9 != 0:
                d.point((x, y + ((x + seed) // 14) % 2), fill=ROCK_LO if x < x0 + (x1 - x0) * 0.72 else ROCK_DK)
    d.rectangle([x0 + 1, y1 - 3, x1 - 1, y1 - 1], fill=ROCK_DK)   # the waterline notch
    for x in range(x0 + 2, x1 - 1, 7):
        d.rectangle([x, y1 - 4, x + 2, y1 - 3], fill=ROCK_LO)
    d.line([(x0 - 1, y1), (x1 + 1, y1)], fill=WHITE)              # surf at the foot
    for x in range(x0 - 3, x1 + 4, 5):
        d.point((x, y1 + 1), fill=WHITE)


def small_pine(d, x, y, s=0):
    """A wind-bent pine standing at (x, y)."""
    d.line([(x, y), (x + 1, y - 9), (x - 1, y - 16)], fill=BARK, width=2)
    blob(d, x - 4, y - 16, 8, 4, PINE, PINE_HI, PINE_LO, s)
    blob(d, x + 4, y - 22, 7, 4, PINE, PINE_HI, PINE_LO, s + 1)
    blob(d, x - 1, y - 27, 5, 3, PINE_HI, PINE_HI, PINE, s + 2)


def islet():
    im, d = canvas(3, 2)                 # 96 x 64
    rock(d, 12, 82, 30, 58, 1)
    d.rectangle([14, 28, 80, 31], fill=PINE_LO)                   # scrub along the top
    for x in range(15, 80, 3):
        d.point((x, 27 + x % 2), fill=PINE)
    d.rectangle([40, 48, 47, 57], fill=ROCK_DK); d.rectangle([41, 46, 46, 48], fill=ROCK_DK)   # a sea cave
    small_pine(d, 26, 30, 1); small_pine(d, 50, 29, 3); small_pine(d, 70, 30, 5)
    outline(im)
    return im


def islet_small():
    im, d = canvas(2, 2)                 # 64 x 64
    rock(d, 16, 48, 32, 58, 2)
    d.rectangle([18, 30, 46, 33], fill=PINE_LO)
    small_pine(d, 32, 32, 2)
    outline(im)
    return im


def ball_rock():
    im, d = canvas(2, 2)                 # 64 x 64
    rock(d, 12, 52, 40, 58, 3)
    d.ellipse([22, 20, 43, 41], fill=ROCK)                        # the ball
    d.ellipse([22, 20, 39, 37], fill=ROCK_HI)
    d.ellipse([25, 23, 43, 41], fill=ROCK)
    d.chord([22, 20, 43, 41], 10, 150, fill=ROCK_LO)
    d.line([(27, 30), (39, 30)], fill=ROCK_LO)
    d.rectangle([14, 38, 20, 40], fill=PINE_LO); d.rectangle([45, 38, 50, 40], fill=PINE_LO)
    outline(im)
    return im


def ferry():
    im, d = canvas(5, 2)                 # 160 x 64, bow to the right
    # the hull
    d.polygon([(6, 40), (150, 40), (158, 36), (146, 56), (12, 56)], fill=HULL)
    d.polygon([(10, 50), (148, 50), (146, 56), (12, 56)], fill=BLUE)
    d.line([(8, 46), (152, 46)], fill=RED)                        # the boot stripe
    d.line([(6, 40), (156, 37)], fill=WHITE)
    d.line([(12, 56), (146, 56)], fill=BLUE_DK)
    # the main deck saloon: a band of windows
    d.rectangle([14, 26, 128, 40], fill=HULL)
    d.rectangle([14, 36, 128, 40], fill=HULL_LO)
    for x in range(18, 124, 9):
        d.rectangle([x, 29, x + 5, 34], fill=GLASS); d.line([(x, 29), (x + 5, 29)], fill=GLASS_HI)
    # the open upper deck: a rail, a canopy on stanchions, the wheelhouse forward
    d.rectangle([20, 24, 104, 26], fill=HULL_LO)
    for x in range(22, 104, 8):
        d.line([(x, 14), (x, 24)], fill=STONE_LO)
    d.line([(20, 20), (104, 20)], fill=STONE_LO)
    d.rectangle([18, 11, 106, 14], fill=BLUE); d.line([(18, 11), (106, 11)], fill=GLASS_HI)
    d.rectangle([106, 12, 126, 26], fill=HULL); d.rectangle([109, 15, 123, 21], fill=GLASS)
    d.line([(109, 15), (123, 15)], fill=GLASS_HI); d.rectangle([104, 10, 128, 12], fill=BLUE_DK)
    d.rectangle([60, 2, 67, 11], fill=RED); d.rectangle([60, 2, 67, 4], fill=WHITE)      # funnel
    d.line([(134, 26), (134, 8)], fill=STONE_LO); d.polygon([(135, 8), (144, 11), (135, 14)], fill=RED)  # jack staff + flag
    d.ellipse([30, 42, 37, 49], fill=RED_HI); d.ellipse([32, 44, 35, 47], fill=HULL)     # lifebuoys
    d.ellipse([92, 42, 99, 49], fill=RED_HI); d.ellipse([94, 44, 97, 47], fill=HULL)
    outline(im)
    for x in range(8, 150, 6):                                    # its wake line on the water (after the ink)
        d.point((x, 58), fill=WHITE); d.point((x + 2, 59), fill=rgb('ffffff', 150))
    return im


def pier():
    im, d = canvas(5, 1)                 # 160 x 32
    d.rectangle([0, 4, 157, 27], fill=WOOD)
    for x in range(0, 158, 8):                                    # planks across the walk
        d.line([(x, 4), (x, 27)], fill=WOOD_LO)
        d.point((x + 3, 7 + (x // 8) % 3 * 6), fill=WOOD_DK)
    d.line([(0, 4), (157, 4)], fill=rgb('d8ae94')); d.rectangle([0, 26, 157, 28], fill=WOOD_DK)
    for x in range(6, 158, 30):                                   # mooring posts along both edges
        for y in (1, 24):
            d.rectangle([x, y, x + 4, y + 6], fill=WOOD_LO); d.rectangle([x, y, x + 4, y + 1], fill=WHITE)
    outline(im)
    return im


def shore_west():
    """pond-autotile_edge-e mirrored: the rocks on the west, the water to the east."""
    return Image.open('assets/sprites/pond-autotile_edge-e.png').convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT)


SPRITES = {      # key: (builder, pixel-double?, tileNames label)
    'sendai-masamune_0_0': (masamune, True, 'sendai-masamune'),
    'sendai-zuihoden_0_0': (zuihoden, True, 'sendai-zuihoden'),
    'sendai-gate_0_0': (gate, True, 'sendai-gate'),
    'sendai-earthen-wall_0_0': (earthen_wall, True, 'sendai-earthen-wall'),
    'sendai-pine_0_0': (pine, True, 'sendai-pine'),
    'sendai-cedar_0_0': (cedar, True, 'sendai-cedar'),
    'sendai-maple_0_0': (maple, True, 'sendai-maple'),
    'sendai-stone-lantern_0_0': (stone_lantern, True, 'sendai-stone-lantern'),
    'sendai-pub_0_0': (pub, True, 'sendai-pub'),
    'sendai-kiln_0_0': (kiln, True, 'sendai-kiln'),
    'sendai-barrels_0_0': (barrels, True, 'sendai-barrels'),
    'matsushima-islet_0_0': (islet, True, 'matsushima-islet'),
    'matsushima-islet-small_0_0': (islet_small, True, 'matsushima-islet-small'),
    'matsushima-ball-rock_0_0': (ball_rock, True, 'matsushima-ball-rock'),
    'matsushima-ferry_0_0': (ferry, True, 'matsushima-ferry'),
    'matsushima-pier_0_0': (pier, True, 'matsushima-pier'),
    'pond-autotile_edge-w': (shore_west, False, 'pond-autotile'),
}

# The pier lies flat on the water: Non-Collidables with a depth nudge that puts
# it over the Water layer and under everyone standing on it (the
# asahikawa-bridge recipe, see generate_hokkaido.FLAT).
FLAT = {'matsushima-pier_0_0': -200}


def main():
    built = {}
    for key, (fn, double, _) in SPRITES.items():
        im = fn()
        if double:
            im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')

    cfg = json.load(open('config.json'))
    for key, (_, _, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if key in FLAT:
            cfg['spriteMetadata'][key]['depthBias'] = FLAT[key]
        cfg.setdefault('tileNames', {})[key] = label
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        ims = list(built.values())
        sheet = Image.new('RGBA', (sum(i.width + 16 for i in ims) + 16, max(i.height for i in ims) + 32),
                          rgb('83af6f'))
        x = 16
        for im in ims:
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
