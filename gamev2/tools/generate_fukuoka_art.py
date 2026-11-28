#!/usr/bin/env python3
"""generate_fukuoka_art.py — draw the Fukuoka sprites (issue #67).

No asset pack has Fukuoka art, so the town's landmarks are drawn here the way
tools/generate_hokkaido.py draws Sapporo's: shaded pixel art in the GuttyKreum
palette, at half size (one drawn pixel = one pixel of a 32px tile) and
pixel-doubled, with a 1px ink outline. Not line-art placeholders.

  fukuoka-tower_0_0      4x12  Fukuoka Tower: the mirrored triangular prism at
                               Momochi, its mast, the low base building
  yatai-ramen_0_0        3x3   a Nakasu food stall: striped canvas roof, a noren
  yatai-yakitori_0_0     3x3   (ラーメン on the ramen one), the lit counter with
  yatai-oden_0_0         3x3   bowls, stools in front, a paper lantern
  yatai-lanterns_0_0     1x2   a post strung with red paper lanterns - the key
                               holds `-lanterns`, so src/DayNight.js lights it
                               at night like every other lantern
  hakata-yamakasa_0_0    2x4   a decorated Hakata Gion Yamakasa float, the kind
                               that stands at Kushida shrine all year
  canal-city_0_0         8x6   Canal City Hakata: the curved terracotta mall
  canal-fountain_0_0     2x2   its dancing fountain
  dazaifu-hall_0_0       6x5   Dazaifu Tenmangu as the group saw it in 2025:
                               the temporary hall whose roof carries a grove
  dazaifu-bridge_0_0     2x4   the arched vermilion taiko bridge over the
                               shrine pond (flat: Non-Collidables + depthBias,
                               you walk ON it - the asahikawa-bridge recipe)
  plum-tree_0_0          2x3   an ume in blossom (Dazaifu's tobiume)
  beach-shore-{e,n,ne}   1x1   the sea meeting Momochi beach: water, foam, wet
                               sand (land to the east / north / both)
  sand-autotile_*        1x1   the dirt-outside family recoloured to sand (9
                               autotile roles; the grass fringe is kept)

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json (spriteMetadata, tileNames, and the tower in
game.lookUp.sprites so the camera looks up at it). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_fukuoka.py:
    python3 tools/generate_fukuoka_art.py [--preview out.png]
"""
import json
import math
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (rgb, canvas, outline, tiles, window, GLYPHS, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK, WHITE,
                               GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)

WOOD_HI = rgb('d2a58c')
VERMILION, VERMILION_HI, VERMILION_DK = rgb('d9553b'), rgb('ee8468'), rgb('a13a2a')
PINK, PINK_HI, PINK_DK = rgb('f0b4c6'), rgb('fbe3ea'), rgb('c9728c')
PURPLE = rgb('6b4a8c')
DARK = rgb('2a2330')                       # a lit stall's back wall, the hall's interior
SEA, SHALLOW, WET, SAND = rgb('425faa'), rgb('8ec2fa'), rgb('bca67c'), rgb('e2cea0')
LEAF, LEAF_HI, LEAF_LO = rgb('678e57'), rgb('89af78'), rgb('395050')

# Brought into line with the GuttyKreum pack: blossom and leaves in ragged
# clumps shaded the way the pack's trees are (generate_sendai_art.foliage),
# and every colour the pack does not have swapped for its nearest one that it
# does - a lit bulb or lantern is the pack's dim gold, not a bright yellow.
from generate_sendai_art import foliage, repaint, limb, LEAF as PACK_LEAF, NEEDLE, P_INK    # noqa: E402

BLOSSOM = [rgb(c) for c in ('fafcfd', 'ffe2e0', 'ffe2e0', 'd78bc1', 'bb6479', '83374f')]
PACK_SWAP = {rgb(a): rgb(b) for a, b in (
    ('f9c22e', 'c6a663'), ('d2a58c', 'be9e8c'), ('5a3b34', '5a3827'), ('2a2330', '1b1e2a'), ('40303a', '3c3a4c'),
    ('34343f', '3c3a4c'), ('2f3f7a', '314b8e'), ('6b4a8c', '585575'), ('d9553b', 'd16b56'), ('ee8468', 'e78d7b'),
    ('a13a2a', 'aa4d31'), ('6583bd', '588cc6'), ('a9d3fb', '8ec2fa'), ('5d7fc0', '588cc6'), ('89af78', '83af6f'))}
KEEP = ('beach-shore',)                    # the sand is the sand set's own colour


# ------------------------------------------------------------------------------
def tower():
    im, d = canvas(4, 12)                # 128 x 384
    cx = 64

    def half(y):
        """Half the prism's width: it widens a little towards the ground."""
        return 13 + (y - 62) * 9 / 268

    # ---- the mast: red and white bands, a small yard ---------------------------
    for y in range(6, 50):
        band = RED if ((y - 6) // 8) % 2 == 0 else WHITE
        d.line([(cx - 1, y), (cx, y)], fill=band)
    d.rectangle([cx - 3, 34, cx + 2, 35], fill=STONE_LO)
    # ---- the pointed cap of the prism ------------------------------------------
    for y in range(50, 62):
        w = int(1 + (half(62) - 1) * (y - 50) / 12)
        d.line([(cx - w, y), (cx - 3, y)], fill=GLASS_HI)
        d.line([(cx - 2, y), (cx + w, y)], fill=GLASS)
    # ---- the mirrored shaft: a lit face and a shaded one meeting on an edge
    #      left of centre, glazing bars, and the sky sliding across the glass ----
    px = im.load()
    for y in range(62, 332):
        w = int(half(y))
        edge = cx - w // 3
        for x in range(cx - w, cx + w + 1):
            lit = x < edge
            bar = (y % 7 == 0) or ((x - edge) % 6 == 0)
            streak = ((x * 2 + y) // 18) % 4 == 0
            if x == edge or x == edge - 1:
                c = WHITE if x == edge - 1 else GLASS_DK
            elif bar:
                c = GLASS if lit else GLASS_DK
            elif lit:
                c = WHITE if streak and (x + y) % 3 == 0 else (rgb('a9d3fb') if streak else GLASS_HI)
            else:
                c = rgb('6583bd') if streak else GLASS
            px[x, y] = c
        px[cx - w, y] = rgb('a9d3fb'); px[cx + w, y] = GLASS_DK
    # ---- the observation floors: a dark band of windows near the top ----------
    for y0 in (84, 100):
        w = int(half(y0)) + 2
        d.rectangle([cx - w, y0, cx + w, y0 + 9], fill=GLASS_DK)
        d.line([(cx - w, y0), (cx + w, y0)], fill=WHITE)
        d.line([(cx - w, y0 + 9), (cx + w, y0 + 9)], fill=STONE_LO)
        for x in range(cx - w + 2, cx + w - 1, 4):
            d.rectangle([x, y0 + 3, x + 1, y0 + 6], fill=AMBER if (x // 4) % 3 else GLASS_HI)
    # ---- the base building: stone, a glazed hall, the entrance under a canopy --
    d.rectangle([8, 330, 119, 379], fill=STONE)
    d.rectangle([8, 330, 119, 334], fill=WHITE)
    d.rectangle([8, 372, 119, 379], fill=STONE_LO)
    d.line([(119, 330), (119, 379)], fill=STONE_LO)
    for x in range(14, 112, 14):
        if 48 <= x <= 70:
            continue
        d.rectangle([x, 340, x + 9, 362], fill=GLASS_DK)
        d.rectangle([x + 1, 341, x + 8, 361], fill=GLASS)
        d.line([(x + 1, 341), (x + 8, 341)], fill=GLASS_HI)
        d.line([(x + 1, 351), (x + 8, 351)], fill=GLASS_DK)
    d.rectangle([48, 338, 79, 379], fill=STONE_DK)
    d.rectangle([50, 346, 63, 379], fill=GLASS); d.rectangle([65, 346, 77, 379], fill=GLASS)
    d.line([(50, 346), (63, 346)], fill=GLASS_HI); d.line([(65, 346), (77, 346)], fill=GLASS_HI)
    d.rectangle([44, 336, 83, 341], fill=GLASS_HI)                # the glass canopy
    d.line([(44, 341), (83, 341)], fill=GLASS)
    for x in (22, 36, 92, 106):                                   # planters by the wall
        d.rectangle([x - 3, 366, x + 3, 371], fill=LEAF); d.point((x - 1, 366), fill=LEAF_HI)

    outline(im)
    return im


# ------------------------------------------------------------------------------
def glyph_row(d, names, x, y, fill):
    """Hand-set kana (generate_hokkaido.GLYPHS), left to right. A long-vowel
    bar lies flat in horizontal text."""
    for name in names:
        if name == 'bar':
            d.line([(x + 1, y + 4), (x + 7, y + 4)], fill=fill)
        else:
            for gy, row in enumerate(GLYPHS[name]):
                for gx, ch in enumerate(row):
                    if ch == '#':
                        d.point((x + gx, y + gy), fill=fill)
        x += 11


def paper_lantern(d, x, y, w=8, h=11, body=RED, hi=RED_HI, lo=RED_DK):
    """A chochin: a ribbed paper drum between two dark caps."""
    d.rectangle([x + 1, y, x + w - 2, y + 1], fill=INK)
    d.rectangle([x, y + 2, x + w - 1, y + h - 3], fill=body)
    d.line([(x, y + 2), (x, y + h - 3)], fill=hi)
    d.line([(x + w - 1, y + 2), (x + w - 1, y + h - 3)], fill=lo)
    for ry in range(y + 4, y + h - 3, 2):
        d.line([(x + 1, ry), (x + w - 2, ry)], fill=lo)
    d.rectangle([x + 2, y + 3, x + 3, y + h - 5], fill=hi)
    d.rectangle([x + 1, y + h - 2, x + w - 2, y + h - 1], fill=INK)


YATAI = {      # kind: (roof stripe, noren cloth, noren shade, noren mark)
    'ramen':    (RED, RED, RED_DK, WHITE),
    'yakitori': (NAVY, rgb('2f3f7a'), NAVY, WHITE),
    'oden':     (GREEN, CREAM, CREAM_LO, RED),
}


def yatai(kind):
    stripe, cloth, cloth_lo, mark = YATAI[kind]
    im, d = canvas(3, 3)                 # 96 x 96

    # ---- the lit inside of the stall, behind everything -------------------------
    d.rectangle([9, 26, 86, 62], fill=DARK)
    d.rectangle([9, 44, 86, 62], fill=rgb('5a3b34'))              # lamplight on the back boards
    for x in range(14, 84, 10):
        d.line([(x, 44), (x, 62)], fill=DARK)
    d.rectangle([14, 48, 80, 49], fill=WOOD_LO)                   # a shelf of bottles
    for i, x in enumerate(range(17, 78, 6)):
        c = (GREEN_HI, AMBER, WHITE, RED_HI)[i % 4]
        d.rectangle([x, 44, x + 1, 47], fill=c)
    d.rectangle([60, 52, 72, 60], fill=STONE_DK)                  # the stock pot, steaming
    d.line([(60, 52), (72, 52)], fill=STONE)
    for sx, sy in ((63, 49), (66, 47), (69, 49), (65, 45)):
        d.point((sx, sy), fill=WHITE)
    d.rectangle([46, 40, 49, 43], fill=AMBER); d.point((47, 41), fill=WHITE)    # the bare bulb
    # ---- corner poles ------------------------------------------------------------
    for x in (7, 87):
        d.rectangle([x, 22, x + 1, 70], fill=WOOD_LO)
        d.line([(x, 22), (x, 70)], fill=WOOD)
    # ---- the canvas roof: striped, wider at the eaves, a scalloped valance ------
    for y in range(5, 23):
        t = (y - 5) / 17
        x0, x1 = int(15 - 12 * t), int(80 + 12 * t)
        for x in range(x0, x1 + 1):
            band = int((x - 47.5) / (4 + 3 * t) + 40) % 2
            c = stripe if band else CREAM
            if y >= 21:
                c = RED_DK if band and stripe == RED else (INK if band else CREAM_LO)
            d.point((x, y), fill=c)
        d.point((x0, y), fill=WHITE)
    for x in range(3, 93):
        if (x // 5) % 2 == 0:
            d.line([(x, 23), (x, 24)], fill=CREAM if (x // 5) % 4 == 0 else stripe)
    # ---- the noren: split cloth across the front --------------------------------
    for i, x0 in enumerate(range(12, 84, 12)):
        d.rectangle([x0, 26, x0 + 10, 41], fill=cloth)
        d.line([(x0, 26), (x0, 41)], fill=cloth_lo)
        d.line([(x0, 41), (x0 + 10, 41)], fill=cloth_lo)
    d.line([(10, 25), (86, 25)], fill=WOOD_DK)                    # the rod it hangs on
    if kind == 'ramen':
        glyph_row(d, ('ra', 'bar', 'me', 'n'), 27, 29, mark)
    elif kind == 'yakitori':
        for x0 in range(12, 84, 12):                              # a white roundel on every strip
            d.ellipse([x0 + 2, 30, x0 + 8, 36], outline=mark)
            d.line([(x0 + 4, 33), (x0 + 6, 33)], fill=mark)
    else:
        for x0 in range(12, 84, 24):                              # red discs on cream
            d.ellipse([x0 + 8, 29, x0 + 15, 36], fill=mark)
    # ---- the counter, with bowls on it, and the cart's boarded front ------------
    d.rectangle([5, 60, 90, 64], fill=WOOD_HI)
    d.line([(5, 64), (90, 64)], fill=WOOD_LO)
    for bx in (18, 40, 72):
        d.rectangle([bx, 57, bx + 7, 59], fill=WHITE)
        d.line([(bx, 57), (bx + 7, 57)], fill=RED)
        d.line([(bx + 1, 60), (bx + 6, 60)], fill=CREAM_LO)
    d.rectangle([7, 65, 88, 84], fill=WOOD)
    for x in range(7, 89, 9):
        d.line([(x, 65), (x, 84)], fill=WOOD_LO)
    d.line([(7, 65), (88, 65)], fill=WOOD_DK)
    d.rectangle([7, 83, 88, 84], fill=WOOD_DK)
    for wx in (14, 81):                                           # cart wheels
        d.ellipse([wx - 6, 78, wx + 6, 90], fill=WOOD_DK)
        d.ellipse([wx - 3, 81, wx + 3, 87], fill=STONE_LO)
        d.point((wx, 84), fill=INK)
    # ---- three stools on the pavement in front -----------------------------------
    for sx in (27, 44, 61):
        d.rectangle([sx + 1, 84, sx + 2, 92], fill=STONE_DK); d.rectangle([sx + 7, 84, sx + 8, 92], fill=STONE_DK)
        d.rectangle([sx, 80, sx + 9, 83], fill=RED if kind != 'ramen' else rgb('2f3f7a'))
        d.line([(sx, 80), (sx + 9, 80)], fill=RED_HI if kind != 'ramen' else GLASS)
    # ---- the paper lantern on the corner pole ------------------------------------
    paper_lantern(d, 84, 27, 9, 14)
    outline(im)
    return im


def lantern_post():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([15, 4, 16, 60], fill=WOOD_LO)
    d.line([(15, 4), (15, 60)], fill=WOOD)
    d.rectangle([12, 59, 19, 61], fill=STONE_DK)
    d.rectangle([3, 5, 28, 6], fill=WOOD_LO)                      # the cross arm
    for lx in (4, 20):                                            # two strings of two
        d.line([(lx + 3, 7), (lx + 3, 8)], fill=INK)
        paper_lantern(d, lx, 9, 8, 11)
        paper_lantern(d, lx, 21, 8, 11, body=WHITE, hi=WHITE, lo=CREAM_LO)
        d.rectangle([lx + 3, 25, lx + 4, 27], fill=RED)           # the stall's mark on the white one
    outline(im)
    return im


# ------------------------------------------------------------------------------
def yamakasa():
    im, d = canvas(2, 4)                 # 64 x 128
    cx = 32
    # ---- the carrying frame: six long poles on a trestle, a striped skirt ------
    d.rectangle([10, 96, 53, 106], fill=WHITE)
    for x in range(10, 54, 6):
        d.rectangle([x, 96, x + 2, 106], fill=RED)
    d.line([(10, 96), (53, 96)], fill=GOLD)
    for y in (108, 114):
        d.rectangle([1, y, 62, y + 2], fill=WOOD_HI)
        d.line([(1, y + 2), (62, y + 2)], fill=WOOD_LO)
    for x in (12, 30, 48):
        d.rectangle([x, 106, x + 3, 123], fill=WOOD)
        d.line([(x + 3, 106), (x + 3, 123)], fill=WOOD_LO)
    d.rectangle([8, 120, 55, 123], fill=WOOD_LO)
    # ---- the tableau: four tiers of castle roofs, waves, rocks and figures -----
    tiers = [(74, 96, 22), (52, 74, 18), (32, 52, 14), (16, 32, 9)]
    for i, (y0, y1, w) in enumerate(tiers):
        d.rectangle([cx - w, y0 + 6, cx + w - 1, y1], fill=(NAVY, rgb('2f3f7a'))[i % 2])
        for k in range(3):                                        # breaking waves
            wx = cx - w + 2 + ((k * 11 + i * 5) % max(1, 2 * w - 8))
            wy = y1 - 3 - (k * 4 + i) % 8
            d.arc([wx, wy, wx + 7, wy + 6], 180, 360, fill=GLASS_HI)
            d.point((wx, wy + 2), fill=WHITE); d.point((wx + 7, wy + 2), fill=WHITE)
        d.rectangle([cx - w + 1, y1 - 4, cx - w + 6, y1], fill=GREEN)            # rocks and pines
        d.rectangle([cx + w - 7, y1 - 6, cx + w - 2, y1], fill=GREEN_LO)
        d.point((cx - w + 2, y1 - 4), fill=GREEN_HI)
        for k, fx in enumerate((cx - w // 2 - 1, cx + w // 2 - 3)):             # warrior dolls
            robe = (RED, PURPLE, GOLD, VERMILION)[(i + k) % 4]
            d.rectangle([fx, y0 + 9, fx + 3, y0 + 11], fill=CREAM)
            d.line([(fx, y0 + 8), (fx + 3, y0 + 8)], fill=INK)
            d.rectangle([fx - 1, y0 + 12, fx + 4, max(y0 + 13, y1 - 5)], fill=robe)
            d.line([(fx + 5, y0 + 9), (fx + 5, max(y0 + 12, y1 - 6))], fill=GOLD)             # a spear / banner pole
        # the tier's roof: a red hip roof with upturned gold eaves
        for y in range(y0, y0 + 6):
            ww = w - 3 + (y - y0)
            d.line([(cx - ww, y), (cx + ww - 1, y)], fill=RED if (y - y0) % 2 else RED_LO)
        d.line([(cx - w - 2, y0 + 6), (cx + w + 1, y0 + 6)], fill=GOLD)
        d.point((cx - w - 3, y0 + 5), fill=GOLD); d.point((cx + w + 2, y0 + 5), fill=GOLD)
    # ---- the crown: a pine sprig and a gold finial ------------------------------
    d.rectangle([cx - 1, 6, cx, 16], fill=WOOD_LO)
    d.ellipse([cx - 6, 7, cx + 5, 14], fill=GREEN)
    d.ellipse([cx - 4, 8, cx + 1, 11], fill=GREEN_HI)
    d.rectangle([cx - 1, 3, cx, 6], fill=GOLD)
    outline(im)
    return im


# ------------------------------------------------------------------------------
FONT = {       # 5x7 capitals for the mall's sign
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#.#.#', '#..##', '#...#', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'I': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '#####'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    ' ': ['.....'] * 7,
}


def canal_city():
    im, d = canvas(8, 6)                 # 256 x 192
    px = im.load()

    def sag(x):
        """The front is a concave curve: its floor lines dip in the middle."""
        return int(round(7 * (1 - ((x - 128) / 122) ** 2)))

    # ---- the curved terracotta front: four floors of ribbon windows -------------
    for x in range(40, 216):
        s = sag(x)
        shade = abs(x - 128) / 90                                 # the hollow of the curve is in shadow
        for y in range(34 + s, 150):
            v = y - s - 34
            if v < 4:
                c = CREAM if v < 3 else CREAM_LO                  # the parapet
            else:
                band = (v - 4) % 26
                if band < 9:
                    c = RED if shade > 0.75 else (RED_LO if shade > 0.3 else RED_DK)
                    if band == 0:
                        c = RED_HI if shade > 0.3 else RED
                elif band < 22:
                    c = CREAM_DK if x % 8 == 0 else (GLASS_HI if band == 9 else GLASS)
                    if (x // 8 + (v // 26)) % 5 == 0 and band > 12:
                        c = GLASS_DK if x % 8 else CREAM_DK       # a few rooms with the blinds down
                else:
                    c = CREAM if band < 25 else CREAM_LO
            px[x, y] = c
    # ---- the hotel block on the left, cream with a grid of windows --------------
    d.rectangle([4, 12, 43, 186], fill=CREAM)
    d.line([(4, 12), (4, 186)], fill=WHITE); d.rectangle([40, 12, 43, 186], fill=CREAM_LO)
    d.rectangle([2, 8, 45, 12], fill=CREAM_DK); d.line([(2, 8), (45, 8)], fill=CREAM)
    for wy in range(18, 146, 13):
        for wx in (9, 19, 29):
            d.rectangle([wx, wy, wx + 6, wy + 8], fill=GLASS)
            d.line([(wx, wy), (wx + 6, wy)], fill=GLASS_HI)
            d.line([(wx, wy + 9), (wx + 6, wy + 9)], fill=CREAM_LO)
    # ---- the drum on the right: blue, ribbed, a ring of glass under its cap -----
    for x in range(212, 252):
        t = (x - 212) / 39
        base = rgb('5d7fc0') if t < 0.25 else (GLASS if t < 0.7 else NAVY)
        for y in range(22, 187):
            c = base
            if (x - 212) % 5 == 0:
                c = GLASS_DK if t >= 0.25 else GLASS
            if 30 <= y <= 38:
                c = GLASS_HI if (x - 212) % 5 else GLASS_DK
            px[x, y] = c
    d.rectangle([210, 18, 253, 22], fill=STONE); d.line([(210, 18), (253, 18)], fill=WHITE)
    # ---- the sign, across the top of the curve ----------------------------------
    text = 'CANAL CITY'
    tx = 128 - (len(text) * 6 - 1) // 2
    d.rectangle([tx - 5, 50, tx + len(text) * 6 + 3, 62], fill=CREAM)
    d.rectangle([tx - 5, 50, tx + len(text) * 6 + 3, 50], fill=WHITE)
    d.rectangle([tx - 5, 62, tx + len(text) * 6 + 3, 62], fill=CREAM_DK)
    for i, ch in enumerate(text):
        for gy, row in enumerate(FONT[ch]):
            for gx, bit in enumerate(row):
                if bit == '#':
                    d.point((tx + i * 6 + gx, 53 + gy), fill=RED_DK)
    # ---- the ground floor: an arcade of shop windows under striped awnings ------
    d.rectangle([4, 150, 251, 186], fill=CREAM_LO)
    d.line([(4, 150), (251, 150)], fill=CREAM)
    for x0 in range(10, 244, 26):
        if 100 <= x0 <= 140:
            continue
        d.rectangle([x0, 160, x0 + 19, 186], fill=GLASS_DK)
        d.rectangle([x0 + 1, 161, x0 + 18, 185], fill=GLASS)
        d.line([(x0 + 1, 161), (x0 + 18, 161)], fill=GLASS_HI)
        d.line([(x0 + 9, 161), (x0 + 9, 185)], fill=GLASS_DK)
        for ax in range(x0 - 2, x0 + 22):                         # the awning
            d.line([(ax, 154), (ax, 159)], fill=(GREEN if (ax // 3) % 2 else CREAM))
        d.line([(x0 - 2, 160), (x0 + 21, 160)], fill=GREEN_LO)
    # the entrance: a tall arch, double glass doors, steps
    d.rectangle([98, 146, 157, 186], fill=CREAM)
    d.pieslice([102, 148, 153, 200], 180, 360, fill=GLASS_DK)
    d.rectangle([102, 174, 153, 186], fill=GLASS_DK)
    d.rectangle([106, 166, 126, 186], fill=GLASS); d.rectangle([129, 166, 149, 186], fill=GLASS)
    d.line([(106, 166), (126, 166)], fill=GLASS_HI); d.line([(129, 166), (149, 166)], fill=GLASS_HI)
    d.point((125, 177), fill=GOLD); d.point((130, 177), fill=GOLD)
    d.arc([102, 148, 153, 200], 180, 360, fill=RED_LO)
    d.rectangle([4, 186, 251, 189], fill=STONE_LO); d.line([(4, 186), (251, 186)], fill=STONE)
    # ---- roof gardens along the parapet ------------------------------------------
    for x in range(52, 206, 9):
        y = 31 + sag(x)
        d.ellipse([x, y - 3, x + 6, y + 3], fill=LEAF if (x // 9) % 2 else LEAF_LO)
        d.point((x + 2, y - 2), fill=LEAF_HI)
    outline(im)
    return im


def fountain():
    im, d = canvas(2, 2)                 # 64 x 64
    # the basin: a stone ring, water inside
    d.ellipse([3, 36, 60, 61], fill=STONE_LO)
    d.ellipse([3, 34, 60, 58], fill=STONE)
    d.ellipse([7, 37, 56, 55], fill=SEA)
    d.arc([7, 37, 56, 55], 200, 340, fill=SHALLOW)
    # the jets: a tall one in the middle, shorter ones dancing either side
    for jx, top in ((31, 6), (21, 18), (41, 18), (13, 30), (49, 30)):
        d.rectangle([jx, top + 3, jx + 1, 46], fill=SHALLOW)
        d.line([(jx, top + 3), (jx, 46)], fill=WHITE)
        for k, (ox, oy) in enumerate(((-2, 3), (3, 2), (-3, 7), (4, 6), (-1, 0), (2, -1))):
            d.point((jx + ox, top + oy), fill=WHITE if k % 2 else SHALLOW)
        d.ellipse([jx - 3, 44, jx + 4, 48], outline=WHITE)        # where it lands
    outline(im)
    return im


# ------------------------------------------------------------------------------
def blob(d, x, y, r, base, hi, lo):
    d.ellipse([x - r, y - r, x + r, y + r], fill=base)
    d.ellipse([x - r + 1, y - r + 1, x + 1, y], fill=hi)
    d.arc([x - r, y - r, x + r, y + r], 20, 150, fill=lo)


def dazaifu_hall():
    im, d = canvas(6, 5)                 # 192 x 160
    # ---- the grove on the roof: two rows of crowns, a few in blossom -----------
    foliage(im, [(x, 22 + (i * 5) % 6, 10 + i % 3, 9 + i % 3) for i, x in enumerate(range(18, 180, 13))], NEEDLE, 11)
    for i, x in enumerate(range(12, 186, 12)):
        r = 8 + (i * 7) % 4
        foliage(im, [(x, 36 + (i * 3) % 5, r + 1, r)], BLOSSOM if i % 5 == 2 else PACK_LEAF, 20 + i)
    # ---- the roof itself: a dark shallow bowl floating over the hall -----------
    for y in range(44, 66):
        t = (y - 44) / 21
        inset = int(2 + 14 * t * t)
        c = rgb('34343f') if y < 48 else (DARK if y < 60 else INK)
        d.line([(inset, y), (191 - inset, y)], fill=c)
    d.line([(2, 44), (189, 44)], fill=STONE_LO)
    d.line([(4, 48), (187, 48)], fill=STONE_DK)
    # ---- the hall under it: timber posts, white curtains with the plum crest ---
    d.rectangle([20, 66, 171, 136], fill=DARK)
    d.rectangle([20, 66, 171, 88], fill=WHITE)
    d.rectangle([20, 72, 171, 76], fill=PURPLE)
    d.line([(20, 88), (171, 88)], fill=CREAM_LO)
    for x in range(34, 164, 22):                                  # the ume crest: five petals
        for ox, oy in ((0, -2), (-2, 0), (2, 0), (-1, 2), (1, 2)):
            d.point((x + ox, 82 + oy), fill=PURPLE)
        d.point((x, 82), fill=GOLD)
    for x in (20, 62, 126, 168):                                  # posts
        d.rectangle([x, 66, x + 4, 136], fill=WOOD)
        d.line([(x, 66), (x, 136)], fill=WOOD_HI)
        d.line([(x + 4, 66), (x + 4, 136)], fill=WOOD_LO)
    for x0, x1 in ((25, 61), (131, 167)):                         # side bays: paper lattice
        d.rectangle([x0, 90, x1, 128], fill=CREAM)
        for x in range(x0, x1 + 1, 6):
            d.line([(x, 90), (x, 128)], fill=WOOD_LO)
        for y in range(90, 129, 8):
            d.line([(x0, y), (x1, y)], fill=WOOD_LO)
    # the sanctuary: a gold mirror on a red-draped altar, shimenawa above
    d.rectangle([67, 90, 125, 128], fill=rgb('40303a'))
    d.rectangle([80, 112, 112, 128], fill=VERMILION); d.line([(80, 112), (112, 112)], fill=VERMILION_HI)
    d.ellipse([89, 96, 103, 110], fill=GOLD); d.ellipse([92, 99, 100, 107], fill=WHITE)
    d.point((94, 101), fill=GOLD)
    d.line([(67, 91), (125, 91)], fill=CREAM); d.line([(67, 92), (125, 92)], fill=CREAM_LO)
    for x in (76, 88, 104, 116):
        d.rectangle([x, 93, x + 2, 97], fill=WHITE)               # paper streamers
    # ---- the timber deck, the offering box, stone steps -------------------------
    d.rectangle([16, 128, 175, 138], fill=WOOD_HI)
    d.line([(16, 128), (175, 128)], fill=WHITE)
    d.rectangle([16, 136, 175, 138], fill=WOOD_LO)
    d.rectangle([84, 118, 107, 132], fill=WOOD_DK)
    for x in range(86, 106, 3):
        d.line([(x, 119), (x, 124)], fill=WOOD)
    d.line([(84, 125), (107, 125)], fill=WOOD_LO)
    d.rectangle([12, 138, 179, 146], fill=STONE_LO)
    d.line([(12, 138), (179, 138)], fill=STONE)
    for y in range(138, 157, 6):
        d.rectangle([66, y, 125, y + 5], fill=STONE)
        d.line([(66, y + 5), (125, y + 5)], fill=STONE_DK)
        d.line([(66, y), (125, y)], fill=WHITE)
    for x in (54, 132):                                           # stone lanterns by the steps
        d.rectangle([x, 140, x + 5, 155], fill=STONE_LO)
        d.rectangle([x - 2, 132, x + 7, 140], fill=STONE)
        d.rectangle([x, 134, x + 5, 138], fill=AMBER)
        d.rectangle([x - 3, 129, x + 8, 131], fill=STONE_DK)
    outline(im)
    return im


def taiko_bridge():
    im, d = canvas(2, 4)                 # 64 x 128
    for y in range(4, 124):
        t = abs(y - 63.5) / 60                                    # 0 on the crown, 1 at the banks
        c = WOOD_HI if t < 0.3 else (WOOD if t < 0.72 else WOOD_LO)
        step = 6 if t < 0.3 else (4 if t < 0.72 else 3)           # the treads close up as it steepens
        d.line([(10, y), (53, y)], fill=WOOD_DK if y % step == 0 else c)
    for x0 in (4, 54):                                            # vermilion rails
        d.rectangle([x0, 3, x0 + 5, 124], fill=VERMILION)
        d.line([(x0 + 1, 3), (x0 + 1, 124)], fill=VERMILION_HI)
        d.line([(x0 + 5, 3), (x0 + 5, 124)], fill=VERMILION_DK)
        for y in range(4, 124, 20):                               # posts with bronze caps
            d.rectangle([x0 - 1, y, x0 + 6, y + 5], fill=VERMILION_DK)
            d.rectangle([x0 + 1, y + 1, x0 + 4, y + 3], fill=GOLD)
    for y0 in (0, 123):                                           # stone abutments
        d.rectangle([2, y0, 61, y0 + 4], fill=STONE_LO)
        d.line([(2, y0), (61, y0)], fill=STONE)
    outline(im)
    return im


def plum_tree():
    im, d = canvas(2, 3)                 # 64 x 96
    # the trunk: dark, bent, forking low the way an old ume does
    limb(d, 30, 92, 28, 70, 5); limb(d, 28, 70, 33, 54, 4); limb(d, 32, 62, 19, 44); limb(d, 33, 56, 45, 40)
    limb(d, 29, 66, 13, 58, 2)
    d.rectangle([26, 90, 37, 92], fill=WOOD_DK)
    # the crown: clouds of pale blossom, deeper pink in the shade
    foliage(im, [(12, 54, 7, 6), (52, 48, 8, 7), (16, 40, 11, 10), (46, 36, 12, 11), (31, 42, 10, 9),
                 (22, 22, 9, 8), (42, 20, 9, 8), (31, 26, 13, 12)], BLOSSOM, 4)
    outline(im, P_INK)
    return im


# ------------------------------------------------------------------------------
def shore(kind):
    """The sea against the beach, one tile: 'e' has the land on its east side,
    'n' on its north, 'ne' on both (water only in the south-west). The
    waterline wobbles with a period of half a tile, so the tiles join."""
    im = Image.new('RGBA', (32, 32), SAND)
    px = im.load()
    wob = lambda v: round(1.6 * math.sin(v * math.pi / 8))
    for y in range(32):
        for x in range(32):
            east, north = x - (15 + wob(y)), (16 - wob(x)) - y
            dist = east if kind == 'e' else north if kind == 'n' else max(east, north)
            px[x, y] = SEA if dist < -4 else SHALLOW if dist < -2 else WHITE if dist < 0 \
                else WET if dist < 3 else SAND
    return im


def sand_family(cfg):
    """dirt-outside-autotile with the dirt recoloured to sand; the grass fringe,
    its shadow and the ink line are kept."""
    swap = {(198, 159, 150): SAND[:3], (130, 111, 96): WET[:3], (77, 51, 38): (150, 128, 96)}
    for role in ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
                 'corner-ne', 'corner-nw', 'corner-se', 'corner-sw'):
        src, dst = f'dirt-outside-autotile_{role}', f'sand-autotile_{role}'
        im = Image.open(f'assets/sprites/{src}.png').convert('RGBA')
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if (r, g, b) in swap:
                    px[x, y] = swap[(r, g, b)] + (a,)
        im.save(f'assets/sprites/{dst}.png')
        cfg['spriteMetadata'][dst] = dict(cfg['spriteMetadata'][src])
        cfg.setdefault('tileNames', {})[dst] = 'sand-autotile'
    print('sand-autotile: 9 roles')


SPRITES = {      # key: (builder, tileNames label)
    'fukuoka-tower_0_0': (tower, 'fukuoka-tower'),
    'yatai-ramen_0_0': (lambda: yatai('ramen'), 'yatai-ramen'),
    'yatai-yakitori_0_0': (lambda: yatai('yakitori'), 'yatai-yakitori'),
    'yatai-oden_0_0': (lambda: yatai('oden'), 'yatai-oden'),
    'yatai-lanterns_0_0': (lantern_post, 'yatai-lanterns'),
    'hakata-yamakasa_0_0': (yamakasa, 'hakata-yamakasa'),
    'canal-city_0_0': (canal_city, 'canal-city'),
    'canal-fountain_0_0': (fountain, 'canal-fountain'),
    'dazaifu-hall_0_0': (dazaifu_hall, 'dazaifu-hall'),
    'dazaifu-bridge_0_0': (taiko_bridge, 'dazaifu-bridge'),
    'plum-tree_0_0': (plum_tree, 'plum-tree'),
    'beach-shore-e_0_0': (lambda: shore('e'), 'beach-shore'),
    'beach-shore-n_0_0': (lambda: shore('n'), 'beach-shore'),
    'beach-shore-ne_0_0': (lambda: shore('ne'), 'beach-shore'),
}

# Flat on the ground but over the Water layer: Non-Collidables with a depth
# nudge under everything standing (see generate_hokkaido.FLAT).
FLAT = {'dazaifu-bridge_0_0': -200}

# Tall enough to look up at: sprite family -> rows of building below the sprite
# (config game.lookUp.sprites, see "Looking up at landmarks" in hud-input-touch.md)
LOOK_UP = {'fukuoka-tower': 0}


def main():
    built = {}
    for key, (fn, _) in SPRITES.items():
        im = fn()
        if not key.startswith(KEEP):
            repaint(im, PACK_SWAP)
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')

    cfg = json.load(open('config.json'))
    for key, (_, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if key in FLAT:
            cfg['spriteMetadata'][key]['depthBias'] = FLAT[key]
        cfg.setdefault('tileNames', {})[key] = label
    sand_family(cfg)
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (sum(i.width + 16 for i in built.values()) + 16,
                                   max(i.height for i in built.values()) + 32), rgb('8fb07a'))
        x = 16
        for im in built.values():
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
