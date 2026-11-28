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

    # ---- the roof, seen from above as the pack's are: a hipped roof whose ridge
    # sits a third of the way down, the back slope above it, the front slope
    # below, a lit hip to the west and a shaded one to the east ----------------
    px = im.load()
    ridge, top, eave, rx0, rx1 = 26, 4, 80, 62, 161
    for y in range(top, eave + 1):
        if y >= ridge:
            xl, xr = rx0 - (y - ridge) * 60 // (eave - ridge), rx1 + (y - ridge) * 60 // (eave - ridge)
        else:
            xl, xr = rx0 - (ridge - y) * 60 // (ridge - top), rx1 + (ridge - y) * 60 // (ridge - top)
        for x in range(2, 222):
            if xl <= x <= xr:
                px[x, y] = roof_tile(x, y, ROOF_TILE if y >= ridge else ROOF_SHADE)
            else:
                px[x, y] = roof_tile(y, x, ROOF_LIT if x < cx else ROOF_SHADE)
            if abs(x - xl) <= 1 or abs(x - xr) <= 1:              # the hip ridges
                px[x, y] = ROOF_TILE[2] if abs(x - xl) == 0 or abs(x - xr) == 0 else ROOF_TILE[0]
    d.rectangle([2, top, 221, top], fill=P_INK)
    d.rectangle([0, 80, 223, 83], fill=SLATE_LO)                  # eaves
    d.line([(0, 83), (223, 83)], fill=RED_LO)                     # the red rafter ends
    for x in range(3, 222, 5):
        d.point((x, 83), fill=GOLD)
    for x in (0, 221):                                            # gold tips on the front corners
        d.rectangle([x, 76, x + 2, 80], fill=GOLD)
    d.rectangle([rx0 - 4, ridge - 4, rx1 + 4, ridge + 2], fill=SLATE_LO)      # the ridge
    d.rectangle([rx0 - 4, ridge - 4, rx1 + 4, ridge - 4], fill=SLATE_HI)
    for x in range(rx0 + 2, rx1 - 2, 12):
        d.rectangle([x, ridge - 2, x + 3, ridge], fill=GOLD)
    for x0 in (rx0 - 12, rx1 + 2):                                # gold ridge-end ornaments
        d.rectangle([x0, ridge - 10, x0 + 10, ridge + 2], fill=GOLD)
        d.rectangle([x0 + 2, ridge - 14, x0 + 7, ridge - 10], fill=GOLD)
        d.rectangle([x0 + 1, ridge - 10, x0 + 1, ridge + 1], fill=GOLD_HI)
        d.rectangle([x0 + 9, ridge - 10, x0 + 9, ridge + 1], fill=GOLD_LO)
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
    repaint(im, {LACQUER: rgb('1b1e2a'), LACQUER_LO: rgb('080d16'), LACQUER_HI: rgb('413f53'), SLATE_HI: rgb('53596d'),
                 SLATE_LO: rgb('191c2a'), SLATE: rgb('293038'),
                 GOLD_LO: rgb('a7843b'), GOLD_HI: rgb('f3d890'), rgb('ffffff'): P_WHITE, rgb('89af78'): rgb('83af6f')})
    outline(im, P_INK)
    return im


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
# The trees and the pub are drawn in the manner of the GuttyKreum pack: its own
# colours (art-source/GuttyKreum), foliage that runs from a pale green through
# teal and blue to a purple shade the way the pack's trees do, dark glass with
# a slanted glare, and the pack's near-black navy for the outline. Rectangles
# and points only, so any Pillow draws the same pixels.
P_INK, P_EDGE = rgb('080d16'), rgb('172459')
LEAF = [rgb(c) for c in ('b1dfdc', '93c297', '83af6f', '508582', '425faa', '3c396d')]
NEEDLE = [rgb(c) for c in ('93c297', '83af6f', '508582', '4a6262', '3c396d', '2a3151')]
AUTUMN = [rgb(c) for c in ('e4cecc', 'e78d7b', 'd16b56', 'aa4d31', '83374f', '5b283b')]
P_BARK, P_BARK_HI, P_BARK_LO = rgb('7f513b'), rgb('a68777'), rgb('594b45')
P_SHADE = rgb('2a3151', 90)
P_ROOF, P_ROOF_HI, P_ROOF_RIB, P_ROOF_LO = rgb('5b6c79'), rgb('698592'), rgb('4a6262'), rgb('2b373c')
P_STEEL, P_STEEL_HI = rgb('94a2a8'), rgb('d1e2eb')
P_SIDING, P_SIDING_HI, P_SIDING_LO, P_SIDING_DK = rgb('a68777'), rgb('be9e8c'), rgb('8e7366'), rgb('7c5d56')
P_PLASTER, P_WHITE, P_GREY = rgb('e4cecc'), rgb('fafcfd'), rgb('a4b0b5')
P_GLASS, P_GLASS_LO, P_GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
P_RED, P_RED_HI, P_RED_LO = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
P_JOIN, P_JOIN_HI, P_JOIN_LO = rgb('4a6262'), rgb('508582'), rgb('2b373c')
P_WOOD, P_WOOD_LO = rgb('7f513b'), rgb('594b45')
P_LAMP, P_LAMP_HI = rgb('c6a663'), rgb('f3d890')


def speck(x, y, seed=0):
    """0..99, the same for the same cell on any machine."""
    n = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
    return (n ^ (n >> 13)) * 1274126177 % 100 if n >= 0 else (-n ^ (-n >> 13)) * 1274126177 % 100


ROOF_TILE = [rgb(c) for c in ('0a1627', '172459', '434857', '2e4040', '395050')]


ROOF_LIT = [rgb(c) for c in ('0a1627', '172459', '53596d', '395050', '434857')]
ROOF_SHADE = [rgb(c) for c in ('080d16', '0a1627', '2e4040', '21272d', '293038')]


def roof_tile(x, y, tones=None):
    """The pack's kawara: small tiles in courses, a blue joint down each, every other course shifted."""
    if tones:
        return tones[ROOF_TILE.index(roof_tile(x, y))]
    row = y % 5
    col = (x + (2 if y // 5 % 2 else 0)) % 4
    if row == 4:
        return ROOF_TILE[0]
    if col == 3:
        return ROOF_TILE[1]
    if row == 0:
        return ROOF_TILE[2]
    return ROOF_TILE[3] if col == 2 or row == 3 else ROOF_TILE[4]


def repaint(im, swap, roof=()):
    """Every pixel of a colour in `swap` becomes its pack colour; one in `roof` becomes roof tile."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c in roof:
                px[x, y] = roof_tile(x, y)
            elif c in swap:
                px[x, y] = swap[c]


def foliage(im, clumps, ramp, seed=0):
    """Leafy clumps (cx, cy, rx, ry), each lit from the upper left and dark
    underneath, a later one over an earlier one, their edges ragged."""
    px = im.load()
    for n, (cx, cy, rx, ry) in enumerate(clumps):
        for y in range(cy - ry - 1, cy + ry + 2):
            for x in range(cx - rx - 1, cx + rx + 2):
                if not (0 <= x < im.width and 0 <= y < im.height):
                    continue
                dx, dy = (x - cx) * 1000 // rx, (y - cy) * 1000 // ry
                rag = speck(x // 2, y // 2, seed + n)
                if dx * dx + dy * dy > 1000 * (820 + rag * 3):
                    continue
                t = 500 + dy * 55 // 100 + dx * 30 // 100 + (speck(x, y // 2, seed + n + 7) - 50) * 3
                px[x, y] = ramp[max(0, min(len(ramp) - 1, t * len(ramp) // 1000))]


def ground_shade(d, cx, y, w):
    for row, inset in enumerate((4, 1, 0, 0, 1, 4)):
        d.rectangle([cx - w + inset, y + row, cx + w - inset, y + row], fill=P_SHADE)


def trunk(d, pts, w=4):
    d.line(pts, fill=BARK, width=w)
    d.line([(x + w // 2, y) for x, y in pts], fill=BARK_LO)


def stem(d, x, y0, y1, w=4):
    """An upright trunk: bark, a lit left edge, a dark right one."""
    d.rectangle([x, y0, x + w - 1, y1], fill=P_BARK)
    d.rectangle([x, y0, x, y1], fill=P_BARK_HI)
    d.rectangle([x + w - 1, y0, x + w - 1, y1], fill=P_BARK_LO)


def limb(d, x0, y0, x1, y1, w=3):
    """A slanted bough, a point at a time."""
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for n in range(steps + 1):
        x, y = x0 + (x1 - x0) * n // steps, y0 + (y1 - y0) * n // steps
        d.rectangle([x, y, x + w - 1, y], fill=P_BARK)
        d.point((x + w - 1, y), fill=P_BARK_LO)


def pine():
    im, d = canvas(2, 3)                 # 64 x 96
    ground_shade(d, 34, 88, 17)
    limb(d, 31, 91, 29, 74, 5); limb(d, 29, 74, 35, 58, 5); limb(d, 35, 58, 30, 44, 4); limb(d, 30, 44, 33, 28, 4)
    limb(d, 35, 60, 47, 53); limb(d, 30, 46, 17, 43)
    foliage(im, [(16, 40, 14, 7), (48, 50, 13, 7), (34, 28, 17, 8), (22, 21, 12, 7), (45, 16, 12, 7), (32, 9, 11, 6)],
            NEEDLE, 3)
    outline(im, P_INK)
    return im


def cedar():
    im, d = canvas(2, 4)                 # 64 x 128
    ground_shade(d, 33, 120, 17)
    stem(d, 29, 96, 124, 6)
    tiers = [(32, 102 - n * 7, 22 - n * 19 // 13, 7) for n in range(14)]
    foliage(im, tiers + [(32, 6, 2, 5)], NEEDLE, 5)
    outline(im, P_INK)
    return im


def maple():
    im, d = canvas(2, 3)                 # 64 x 96
    ground_shade(d, 34, 88, 17)
    stem(d, 30, 60, 92, 5)
    limb(d, 31, 68, 21, 52); limb(d, 33, 66, 44, 50)
    foliage(im, [(20, 45, 15, 12), (45, 43, 15, 12), (32, 34, 14, 10), (19, 22, 12, 10), (44, 19, 13, 10),
                 (32, 15, 13, 11)], AUTUMN, 9)
    outline(im, P_INK)
    return im


def stone_lantern():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([8, 58, 23, 62], fill=STONE_LO); d.line([(8, 58), (23, 58)], fill=STONE)      # base
    d.rectangle([13, 38, 18, 58], fill=STONE); d.line([(18, 38), (18, 58)], fill=STONE_LO)    # shaft
    d.line([(13, 38), (13, 58)], fill=P_WHITE)
    d.rectangle([9, 34, 22, 38], fill=STONE); d.line([(9, 38), (22, 38)], fill=STONE_DK)      # platform
    d.rectangle([10, 22, 21, 34], fill=STONE_LO)                                              # the light box
    d.rectangle([12, 24, 19, 32], fill=P_LAMP); d.rectangle([13, 25, 16, 28], fill=P_LAMP_HI)
    d.line([(15, 24), (15, 32)], fill=STONE_DK); d.line([(16, 24), (16, 32)], fill=STONE_DK)
    d.polygon([(4, 22), (27, 22), (20, 13), (11, 13)], fill=STONE)                            # the roof
    d.line([(11, 13), (4, 22)], fill=P_WHITE); d.line([(20, 13), (27, 22)], fill=STONE_LO)
    d.line([(4, 22), (27, 22)], fill=STONE_DK)
    d.rectangle([14, 8, 17, 13], fill=STONE); d.rectangle([15, 5, 16, 8], fill=STONE_LO)      # the jewel
    outline(im, P_INK)
    return im


# ------------------------------------------------------------------------------
def lit_window(d, x0, y0, x1, y1, frame):
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=LIT)
    d.rectangle([x0 + 2, y0 + 2, (x0 + x1) // 2 - 1, (y0 + y1) // 2 - 1], fill=LIT_HI)
    d.line([((x0 + x1) // 2, y0 + 1), ((x0 + x1) // 2, y1 - 1)], fill=frame)
    d.line([(x0 + 1, (y0 + y1) // 2), (x1 - 1, (y0 + y1) // 2)], fill=frame)


def pane(d, x0, y0, x1, y1, step=9):
    """The pack's window: dark glass, a slanted glare, a shaded head."""
    d.rectangle([x0, y0, x1, y1], fill=P_GLASS)
    for k in range(-(y1 - y0), x1 - x0, step):
        for t in range(y1 - y0 + 1):
            x, y = x0 + k + t, y1 - t
            if x0 <= x <= x1:
                d.point((x, y), fill=P_GLARE)
    d.rectangle([x0, y0, x1, y0 + 1], fill=P_GLASS_LO)


def pub():
    im, d = canvas(5, 5)                 # 160 x 160
    # ---- the roof, seen from above: ribbed sheet, a ridge cap, a brick stack ---
    d.rectangle([0, 2, 159, 54], fill=P_EDGE)
    d.rectangle([1, 3, 158, 53], fill=P_ROOF)
    for x in range(1, 159, 6):
        d.rectangle([x, 6, x, 53], fill=P_ROOF_RIB)
        d.rectangle([x + 1, 6, x + 1, 49], fill=P_ROOF_HI)
    d.rectangle([1, 3, 158, 5], fill=P_STEEL); d.rectangle([1, 3, 158, 3], fill=P_STEEL_HI)
    d.rectangle([1, 50, 158, 53], fill=P_ROOF_LO)
    d.rectangle([22, 10, 39, 30], fill=P_EDGE)                    # the stack
    d.rectangle([23, 11, 38, 29], fill=P_RED)
    for y in range(15, 30, 4):
        d.rectangle([23, y, 38, y], fill=P_RED_LO)
    d.rectangle([35, 11, 38, 29], fill=P_RED_LO)
    d.rectangle([21, 9, 40, 12], fill=P_EDGE); d.rectangle([22, 10, 39, 11], fill=P_STEEL)
    d.rectangle([24, 31, 41, 33], fill=P_ROOF_LO)
    # ---- the upper storey: weatherboard, four sash windows, the hanging sign ---
    d.rectangle([0, 55, 159, 97], fill=P_SIDING)
    for y in range(61, 97, 6):
        d.rectangle([1, y, 158, y], fill=P_SIDING_LO)
    d.rectangle([1, 55, 158, 58], fill=P_SIDING_DK)               # the eave's shade
    d.rectangle([1, 59, 2, 97], fill=P_SIDING_HI); d.rectangle([155, 59, 158, 97], fill=P_SIDING_LO)
    d.rectangle([0, 55, 0, 97], fill=P_EDGE); d.rectangle([159, 55, 159, 97], fill=P_EDGE)
    for x in (14, 44, 100, 130):
        d.rectangle([x - 2, 63, x + 17, 89], fill=P_EDGE)
        d.rectangle([x - 1, 64, x + 16, 88], fill=P_PLASTER)
        pane(d, x + 1, 66, x + 14, 86)
        d.rectangle([x + 7, 66, x + 8, 86], fill=P_PLASTER); d.rectangle([x + 1, 75, x + 14, 76], fill=P_PLASTER)
        d.rectangle([x - 3, 89, x + 18, 94], fill=P_EDGE)         # a window box of flowers
        d.rectangle([x - 2, 90, x + 17, 93], fill=P_JOIN)
        for n in range(x - 1, x + 17, 3):
            d.point((n, 90), fill=(P_RED_HI, P_PLASTER, P_WHITE)[(n // 3) % 3]); d.point((n + 1, 91), fill=P_JOIN_HI)
    d.rectangle([72, 59, 87, 59], fill=P_INK); d.rectangle([79, 59, 80, 63], fill=P_INK)
    d.rectangle([69, 63, 90, 90], fill=P_EDGE); d.rectangle([70, 64, 89, 89], fill=P_RED)
    d.rectangle([70, 87, 89, 89], fill=P_RED_LO)
    d.rectangle([75, 70, 83, 82], fill=P_PLASTER); d.rectangle([75, 70, 83, 72], fill=P_WHITE)   # a pint, on the board
    d.rectangle([84, 73, 86, 79], fill=P_PLASTER); d.rectangle([84, 75, 84, 77], fill=P_RED)
    d.rectangle([82, 73, 83, 82], fill=P_SIDING_HI)
    # ---- the fascia: red, lined, white capitals --------------------------------
    d.rectangle([0, 98, 159, 117], fill=P_EDGE)
    d.rectangle([1, 99, 158, 116], fill=P_RED)
    d.rectangle([1, 99, 158, 100], fill=P_RED_HI); d.rectangle([1, 114, 158, 116], fill=P_RED_LO)
    d.rectangle([4, 102, 155, 102], fill=P_SIDING_HI); d.rectangle([4, 112, 155, 112], fill=P_SIDING_HI)
    label = 'PUB'
    text(d, label, 80 - (text_width(label, 3)) // 2, 104, P_WHITE, gap=3)
    for sx in (42, 116):                                          # a star either side
        d.rectangle([sx - 3, 106, sx + 3, 107], fill=P_PLASTER); d.rectangle([sx - 1, 104, sx, 109], fill=P_PLASTER)
        d.point((sx - 2, 109), fill=P_PLASTER); d.point((sx + 2, 109), fill=P_PLASTER)
    # ---- the ground floor: dark green joinery, two bays, the door --------------
    d.rectangle([0, 118, 159, 156], fill=P_EDGE)
    d.rectangle([1, 118, 158, 156], fill=P_JOIN)
    d.rectangle([1, 118, 158, 120], fill=P_JOIN_LO)
    d.rectangle([1, 148, 158, 156], fill=P_JOIN_LO); d.rectangle([1, 148, 158, 148], fill=P_JOIN_HI)
    for x in (1, 60, 96, 155):                                    # pilasters
        d.rectangle([x, 121, x + 3, 156], fill=P_JOIN_HI); d.rectangle([x + 3, 121, x + 3, 156], fill=P_JOIN_LO)
        d.rectangle([x, 123, x + 3, 124], fill=P_SIDING_HI)
    for x0 in (9, 103):
        d.rectangle([x0, 123, x0 + 47, 146], fill=P_EDGE)
        pane(d, x0 + 1, 124, x0 + 46, 145, 13)
        d.rectangle([x0 + 1, 141, x0 + 46, 145], fill=P_WOOD_LO)  # the bar, through the glass
        d.rectangle([x0 + 1, 141, x0 + 46, 141], fill=P_WOOD)
        for x in (x0 + 16, x0 + 31):
            d.rectangle([x, 124, x, 145], fill=P_JOIN_LO)
    d.rectangle([65, 121, 94, 156], fill=P_EDGE)                  # the door
    d.rectangle([66, 122, 93, 156], fill=P_WOOD_LO)
    for x0 in (68, 81):
        d.rectangle([x0, 124, x0 + 10, 156], fill=P_WOOD)
        d.rectangle([x0, 124, x0, 156], fill=P_SIDING)
        pane(d, x0 + 2, 127, x0 + 8, 142, 7)
        d.rectangle([x0 + 2, 146, x0 + 8, 153], fill=P_WOOD_LO)
    d.point((78, 144), fill=P_PLASTER); d.point((81, 144), fill=P_PLASTER)
    for x in (62, 97):                                            # carriage lamps by the door
        d.rectangle([x - 2, 124, x + 1, 131], fill=P_INK); d.rectangle([x - 1, 125, x, 130], fill=P_PLASTER)
    d.rectangle([0, 157, 159, 157], fill=P_GREY); d.rectangle([0, 158, 159, 158], fill=P_ROOF_HI)
    d.rectangle([0, 159, 159, 159], fill=P_INK)
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
