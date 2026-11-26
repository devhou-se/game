#!/usr/bin/env python3
"""generate_hokuriku_art.py — draw the Hokuriku sprites (issue #68, stage 3):
Kanazawa, Shirakawa-go and Toyama.

No asset pack has them, so they are drawn here the way
tools/generate_sendai_art.py draws Sendai (it imports that file's palette and
helpers): shaded pixel art in the GuttyKreum palette, at half size and
pixel-doubled, with a 1px ink outline. Nothing here is a white line-art
placeholder.

Kanazawa
  kanazawa-ishikawa-gate_0_0   8x4  Kanazawa Castle's Ishikawa gate: a two-storey
                                    turret, white plaster over a stone base, lead
                                    tiles, and a roofed gateway two cells wide
  kanazawa-kotoji_0_0          2x2  Kenrokuen's two-legged Kotoji stone lantern
  kanazawa-chaya-a/-b_0_0      4x4  Higashi Chaya teahouses: bengara lattice,
                                    bamboo blinds, a noren and a paper lantern
  kanazawa-whisky-bar_0_0      4x4  the whisky bar: a dark front, amber windows
  kanazawa-canal-bridge_0_0    2x4  a stone slab bridge over the Nagamachi canal
                                    (flat: Non-Collidables + depthBias, walked ON)
  hokuriku-ginkgo_0_0          2x3  a ginkgo in November gold
Shirakawa-go
  shirakawa-gassho_0_0         5x5  a gassho-zukuri farmhouse, gable on: the steep
                                    thatch, three tiers of paper windows
  shirakawa-gassho-small_0_0   4x4  a smaller one
  shirakawa-paddy_0_0          1x1  a harvested rice paddy (a Floor tile)
  shirakawa-hasa_0_0           3x2  sheaves drying on a rack
  shirakawa-bridge_0_0         8x2  the suspension footbridge over the Sho river:
                                    the deck row is walked ON (flat), the row above
                                    is its far cable and hangers
  shirakawa-lookout_0_0        4x1  the viewpoint's rail and its signboard
  shirakawa-peak_0_0           6x4  a mountain: snow on the peak, autumn below
  shirakawa-bear-sign_0_0      1x2  the bear warning
Toyama
  toyama-glass-museum_0_0      6x6  the Glass Art Museum: a facade of glass, stone
                                    and aluminium strips round a cedar atrium
  toyama-tram_0_0              5x2  a low-floor tram at its stop
  toyama-tram-rail_0_0         1x1  tram rails set in the asphalt (a Floor tile)
  toyama-tram-stop_0_0         3x2  the stop's shelter
  toyama-ramen_0_0             4x4  the black-ramen shop: seven stools at a counter
  toyama-port-tower_0_0        3x7  the port observation tower, built like a
                                    harbour lantern

Deterministic and idempotent: rewrites the PNGs in assets/sprites/, registers
them in config.json spriteMetadata + tileNames, and asks the camera to look up
at the port tower (game.lookUp.sprites). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py and the three generators:
    python3 tools/generate_hokuriku_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image

from generate_hokkaido import (rgb, canvas, outline, tiles, GLYPHS,
                               INK, RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_sendai_art import (roof_rows, tiled_roof, blob, trunk, lit_window,
                                 LACQUER, LACQUER_HI, LACQUER_LO, GOLD_HI, GOLD_LO,
                                 SLATE, SLATE_HI, SLATE_LO, PINE, PINE_HI, PINE_LO,
                                 MAPLE, MAPLE_HI, MAPLE_OR, BARK, BARK_LO, LIT, LIT_HI, FONT as _FONT)

LEAD, LEAD_HI, LEAD_LO = rgb('b9c3ca'), rgb('e3e9ed'), rgb('8c97a3')            # Kanazawa's lead roof tiles
PLASTER, PLASTER_LO = rgb('f4f1ea'), rgb('d3cdc2')
BENGARA, BENGARA_HI, BENGARA_LO, BENGARA_DK = rgb('8f4a3a'), rgb('ad6049'), rgb('6e3830'), rgb('4c2a28')
BLIND, BLIND_LO = rgb('d9c58a'), rgb('b39c62')
INDIGO, INDIGO_HI = rgb('2c3d6a'), rgb('4b6396')
THATCH, THATCH_HI, THATCH_LO, THATCH_DK = rgb('8a7256'), rgb('ab9272'), rgb('6b5744'), rgb('4b3d33')
BOARD, BOARD_LO = rgb('6e5444'), rgb('4f3c33')
GINKGO, GINKGO_HI, GINKGO_LO = rgb('e8b93a'), rgb('f6dc74'), rgb('b98a2a')
ROCKY, ROCKY_HI, ROCKY_LO = rgb('7c8ba0'), rgb('a3b0c2'), rgb('596a82')
SNOW, SNOW_LO = rgb('f2f5fb'), rgb('c9d6ea')
SOOT, SOOT_HI, SOOT_LO = rgb('2b2a30'), rgb('45444d'), rgb('1a191e')
TEAL, TEAL_HI, TEAL_LO = rgb('3f9a8f'), rgb('6cc4b4'), rgb('2a6e6a')
ALU, ALU_LO = rgb('dfe6ec'), rgb('a9b6c4')

FONT = dict(_FONT)
FONT.update({
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'G': ['.####', '#....', '#....', '#.###', '#...#', '#...#', '.###.'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
})


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


def lead_roof(d, rows):
    tiled_roof(d, rows, LEAD, LEAD_LO, LEAD_HI)


def masonry(d, x0, y0, x1, y1, seed=0):
    """A castle's stone base: fitted stones in uneven courses, lit from above."""
    d.rectangle([x0, y0, x1, y1], fill=STONE)
    d.line([(x0, y0), (x1, y0)], fill=WHITE)
    for i, y in enumerate(range(y0 + 8, y1 + 1, 9)):
        d.line([(x0, y), (x1, y)], fill=STONE_LO)
        step = 11 + (i * 3 + seed) % 5
        for x in range(x0 + (i * 7 + seed * 3) % step, x1, step):
            d.line([(x, y - 8), (x, y - 1)], fill=STONE_LO)
            d.point((x + 2, y - 6), fill=WHITE)
    d.rectangle([x0, y1 - 2, x1, y1], fill=STONE_LO)


def namako(d, x0, y0, x1, y1):
    """Namako-kabe: dark flat tiles in a grid of raised white joints."""
    d.rectangle([x0, y0, x1, y1], fill=SLATE)
    for x in range(x0, x1 + 1, 7):
        d.line([(x, y0), (x, y1)], fill=PLASTER)
    for y in range(y0, y1 + 1, 7):
        d.line([(x0, y), (x1, y)], fill=PLASTER)


# ---------------------------------------------------------------- Kanazawa
def ishikawa_gate():
    im, d = canvas(8, 4)                 # 256 x 128; the gateway is columns 3-4 (x 96-159)
    # ---- the long wall either side of the gate: stone base, white plaster, lead coping
    for x0, x1, s in ((84, 95, 1), (160, 255, 2)):
        masonry(d, x0, 96, x1, 127, s)
        d.rectangle([x0, 70, x1, 95], fill=PLASTER)
        namako(d, x0, 84, x1, 95)
        d.line([(x0, 83), (x1, 83)], fill=PLASTER_LO)
        lead_roof(d, [(y, x0, x1) for y in range(58, 70)])
        d.line([(x0, 57), (x1, 57)], fill=LEAD_HI); d.line([(x0, 70), (x1, 70)], fill=LEAD_LO)
    for x in range(176, 250, 22):                                 # loopholes
        d.rectangle([x, 74, x + 3, 79], fill=SLATE_LO)
    # ---- the gate: posts, a lintel, the leaves folded back, a lead-tiled roof
    for x0 in (92, 156):
        d.rectangle([x0, 56, x0 + 7, 127], fill=WOOD_LO)
        d.line([(x0, 56), (x0, 127)], fill=WOOD); d.line([(x0 + 7, 56), (x0 + 7, 127)], fill=WOOD_DK)
        for y in (72, 96, 118):
            d.rectangle([x0, y, x0 + 7, y + 2], fill=LACQUER_LO)   # iron bands
        d.rectangle([x0 - 1, 122, x0 + 8, 127], fill=STONE_LO)
    d.rectangle([88, 54, 167, 64], fill=WOOD_LO); d.line([(88, 54), (167, 54)], fill=WOOD)
    d.line([(88, 64), (167, 64)], fill=WOOD_DK)
    for x in range(94, 166, 9):
        d.rectangle([x, 58, x + 1, 60], fill=LACQUER_LO)          # nail heads
    for x0, x1 in ((100, 105), (150, 155)):
        d.rectangle([x0, 65, x1, 125], fill=WOOD_DK)
        d.line([(x0 + 2, 67), (x0 + 2, 124)], fill=WOOD_LO)
        for y in (76, 100):
            d.point((x0 + 4, y), fill=GOLD)
    rows = roof_rows(34, 52, (96, 159), (80, 175))
    lead_roof(d, rows)
    d.rectangle([80, 52, 175, 54], fill=LEAD_LO)
    for x in range(82, 175, 4):
        d.point((x, 54), fill=LEAD_HI)
    d.rectangle([94, 29, 161, 34], fill=LEAD_LO); d.line([(94, 29), (161, 29)], fill=LEAD_HI)
    for x0 in (90, 160):
        d.rectangle([x0, 26, x0 + 5, 34], fill=LEAD); d.point((x0 + 1, 27), fill=LEAD_HI)
    # ---- the turret on the left: a taller base, two white storeys, a hipped roof
    masonry(d, 4, 84, 83, 127, 3)
    d.rectangle([8, 44, 79, 83], fill=PLASTER)
    d.line([(8, 44), (8, 83)], fill=WHITE); d.rectangle([75, 44, 79, 83], fill=PLASTER_LO)
    namako(d, 8, 70, 79, 83)
    d.line([(8, 69), (79, 69)], fill=PLASTER_LO)
    # the bay window under its curved gable
    d.rectangle([32, 50, 55, 68], fill=PLASTER_LO)
    d.rectangle([34, 54, 53, 67], fill=SLATE_LO)
    for x in range(37, 53, 4):
        d.line([(x, 54), (x, 67)], fill=PLASTER)
    d.pieslice([28, 40, 59, 62], 180, 360, fill=LEAD)
    d.arc([28, 40, 59, 62], 180, 360, fill=LEAD_HI)
    d.line([(28, 51), (59, 51)], fill=LEAD_LO)
    d.ellipse([41, 44, 46, 49], fill=GOLD)
    for x in (14, 64):
        d.rectangle([x, 52, x + 9, 64], fill=SLATE_LO)
        d.line([(x + 3, 52), (x + 3, 64)], fill=PLASTER); d.line([(x + 6, 52), (x + 6, 64)], fill=PLASTER)
    rows = roof_rows(14, 42, (22, 65), (0, 87))
    lead_roof(d, rows)
    d.rectangle([0, 42, 87, 44], fill=LEAD_LO)
    for x in range(2, 87, 4):
        d.point((x, 44), fill=LEAD_HI)
    d.rectangle([20, 8, 67, 14], fill=LEAD_LO); d.line([(20, 8), (67, 8)], fill=LEAD_HI)
    for x0 in (16, 66):                                           # ridge-end ornaments
        d.polygon([(x0, 14), (x0 + 6, 14), (x0 + 6, 4), (x0 + 3, 1), (x0, 6)], fill=LEAD)
        d.point((x0 + 2, 4), fill=LEAD_HI)
    outline(im)
    return im


def kotoji():
    im, d = canvas(2, 2)                 # 64 x 64
    d.ellipse([6, 54, 58, 63], fill=rgb('3a5f66', 150))
    d.polygon([(34, 50), (58, 50), (62, 62), (30, 62)], fill=STONE_LO)        # the rock the short leg stands on
    d.line([(34, 50), (58, 50)], fill=STONE); d.point((40, 55), fill=STONE_DK); d.point((52, 58), fill=STONE_DK)
    d.line([(26, 36), (20, 46), (16, 61)], fill=STONE, width=4)               # the long leg
    d.line([(28, 37), (22, 47), (18, 61)], fill=STONE_LO)
    d.line([(38, 36), (44, 44), (47, 50)], fill=STONE, width=4)               # the short one
    d.line([(40, 36), (46, 44), (49, 50)], fill=STONE_LO)
    d.rectangle([20, 32, 44, 36], fill=STONE); d.line([(20, 36), (44, 36)], fill=STONE_DK)
    d.rectangle([23, 20, 41, 32], fill=STONE_LO)
    d.rectangle([26, 22, 38, 30], fill=LIT); d.rectangle([27, 23, 31, 26], fill=LIT_HI)
    d.line([(32, 22), (32, 30)], fill=STONE_DK)
    d.polygon([(14, 20), (50, 20), (40, 10), (24, 10)], fill=STONE)
    d.line([(24, 10), (14, 20)], fill=WHITE); d.line([(40, 10), (50, 20)], fill=STONE_LO)
    d.line([(14, 20), (50, 20)], fill=STONE_DK)
    d.rectangle([29, 5, 35, 10], fill=STONE); d.rectangle([31, 2, 33, 5], fill=STONE_LO)
    outline(im)
    return im


def lattice(d, x0, y0, x1, y1, a, b, step=3):
    d.rectangle([x0, y0, x1, y1], fill=b)
    for x in range(x0, x1 + 1, step):
        d.line([(x, y0), (x, y1)], fill=a)


def chaya(noren, blinds):
    def build():
        im, d = canvas(4, 4)             # 128 x 128; the door is column 1 (x 32-63)
        # the main roof
        rows = roof_rows(10, 34, (10, 117), (0, 127))
        tiled_roof(d, rows)
        d.rectangle([8, 5, 119, 10], fill=SLATE_LO); d.line([(8, 5), (119, 5)], fill=SLATE_HI)
        d.rectangle([0, 34, 127, 36], fill=SLATE_LO)
        for x in range(2, 127, 4):
            d.point((x, 36), fill=SLATE_HI)
        # the upper floor: bengara lattice, bamboo blinds rolled half down
        d.rectangle([3, 37, 124, 70], fill=BENGARA)
        d.line([(3, 37), (3, 70)], fill=BENGARA_HI); d.rectangle([121, 37, 124, 70], fill=BENGARA_LO)
        d.line([(3, 37), (124, 37)], fill=BENGARA_DK)
        for i, x0 in enumerate((9, 39, 69, 99)):
            lattice(d, x0, 42, x0 + 21, 66, BENGARA_DK, LIT if i in blinds else BENGARA_LO)
            if i in blinds:
                d.rectangle([x0, 42, x0 + 21, 54], fill=BLIND)
                for y in range(44, 55, 2):
                    d.line([(x0, y), (x0 + 21, y)], fill=BLIND_LO)
            d.rectangle([x0 - 1, 67, x0 + 22, 68], fill=BENGARA_DK)
        # the pent roof over the ground floor
        rows = roof_rows(71, 83, (4, 123), (0, 127))
        tiled_roof(d, rows)
        d.rectangle([0, 83, 127, 85], fill=SLATE_LO)
        # the ground floor: fine kimusuko lattice, the doorway under its noren
        d.rectangle([3, 86, 124, 123], fill=BENGARA_LO)
        lattice(d, 6, 90, 29, 118, BENGARA, BENGARA_DK, 2)
        lattice(d, 68, 90, 121, 118, BENGARA, BENGARA_DK, 2)
        d.rectangle([4, 119, 123, 123], fill=BENGARA_DK)
        d.rectangle([34, 88, 61, 123], fill=SOOT_LO)
        d.rectangle([36, 104, 47, 123], fill=BOARD_LO); d.rectangle([49, 104, 59, 123], fill=BOARD_LO)
        d.rectangle([34, 88, 61, 103], fill=noren[0])
        d.line([(34, 88), (61, 88)], fill=noren[1])
        for x in (43, 52):
            d.line([(x, 92), (x, 103)], fill=SOOT_LO)
        d.ellipse([45, 92, 50, 97], fill=noren[2])
        # a paper lantern by the door
        d.rectangle([64, 92, 66, 94], fill=SOOT_LO)
        d.rectangle([62, 95, 68, 108], fill=CREAM); d.line([(62, 95), (62, 108)], fill=WHITE)
        d.rectangle([62, 95, 68, 96], fill=SOOT); d.rectangle([62, 107, 68, 108], fill=SOOT)
        d.rectangle([64, 99, 66, 104], fill=RED)
        d.rectangle([0, 124, 127, 127], fill=STONE_LO); d.line([(0, 124), (127, 124)], fill=STONE)
        outline(im)
        return im
    return build


def whisky_bar():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1
    # a flat parapet roof, dark render above, timber below
    d.rectangle([2, 14, 125, 22], fill=SOOT_HI); d.line([(2, 14), (125, 14)], fill=STONE_LO)
    d.rectangle([4, 22, 123, 78], fill=SOOT)
    for y in range(28, 78, 7):
        d.line([(4, y), (123, y)], fill=SOOT_LO)
    d.line([(4, 22), (4, 78)], fill=SOOT_HI); d.rectangle([119, 22, 123, 78], fill=SOOT_LO)
    for x0 in (12, 92):                                           # two narrow lit windows upstairs
        lit_window(d, x0, 34, x0 + 22, 62, SOOT_LO)
    # the sign: an amber box, lettered
    d.rectangle([40, 34, 87, 60], fill=GOLD_LO)
    d.rectangle([42, 36, 85, 58], fill=LIT)
    d.rectangle([42, 36, 85, 38], fill=LIT_HI)
    text(d, 'BAR', 64 - text_width('BAR', 4) // 2, 44, SOOT_LO, gap=4)
    d.rectangle([60, 28, 67, 33], fill=SOOT_LO)
    # the awning band
    d.rectangle([0, 78, 127, 86], fill=BENGARA_LO); d.line([(0, 78), (127, 78)], fill=BENGARA)
    d.line([(0, 86), (127, 86)], fill=BENGARA_DK)
    # the ground floor
    d.rectangle([4, 87, 123, 123], fill=BOARD)
    for x in range(8, 123, 6):
        d.line([(x, 87), (x, 123)], fill=BOARD_LO)
    d.rectangle([68, 92, 119, 116], fill=SOOT_LO)                 # the window: bottles against the light
    d.rectangle([70, 94, 117, 114], fill=LIT)
    d.rectangle([70, 94, 117, 96], fill=LIT_HI)
    for i, x in enumerate(range(73, 115, 5)):
        h = (9, 12, 7, 11, 8, 13, 9, 10, 12)[i % 9]
        d.rectangle([x, 114 - h, x + 2, 114], fill=(BENGARA_DK, GREEN_LO, SOOT, GOLD_LO)[i % 4])
        d.point((x + 1, 113 - h), fill=SOOT_LO)
    d.line([(70, 108), (117, 108)], fill=BOARD_LO)
    d.rectangle([34, 88, 61, 123], fill=SOOT_LO)                  # the door
    d.rectangle([36, 90, 59, 123], fill=BENGARA_DK)
    d.rectangle([40, 94, 55, 106], fill=LIT); d.line([(47, 94), (47, 106)], fill=BENGARA_DK)
    d.rectangle([56, 108, 57, 114], fill=GOLD_HI)
    d.rectangle([28, 92, 31, 100], fill=SOOT_LO); d.rectangle([29, 93, 30, 99], fill=LIT_HI)   # a lamp
    # a cask by the door
    d.ellipse([8, 100, 28, 123], fill=WOOD_LO); d.ellipse([10, 102, 26, 121], fill=WOOD)
    d.ellipse([8, 100, 28, 123], outline=SOOT_LO)
    for dx in (14, 18, 22):
        d.line([(dx, 104), (dx, 119)], fill=WOOD_LO)
    d.rectangle([0, 124, 127, 127], fill=STONE_LO); d.line([(0, 124), (127, 124)], fill=STONE)
    outline(im)
    return im


def canal_bridge():
    im, d = canvas(2, 4)                 # 64 x 128, walked north-south
    d.rectangle([4, 2, 59, 125], fill=STONE)
    for i, y in enumerate(range(2, 126, 12)):                     # the slabs
        d.line([(4, y), (59, y)], fill=STONE_LO)
        d.point((14 + (i * 17) % 34, y + 5), fill=WHITE); d.point((40 - (i * 11) % 28, y + 8), fill=STONE_LO)
    for x0 in (2, 56):                                            # low parapets
        d.rectangle([x0, 0, x0 + 5, 127], fill=STONE_LO)
        d.line([(x0, 0), (x0, 127)], fill=STONE)
        for y in range(6, 126, 20):
            d.rectangle([x0 - 1, y, x0 + 6, y + 5], fill=STONE); d.line([(x0 - 1, y), (x0 + 6, y)], fill=WHITE)
    outline(im)
    return im


def ginkgo():
    im, d = canvas(2, 3)                 # 64 x 96
    d.ellipse([16, 86, 50, 94], fill=rgb('3a5f66', 150))
    trunk(d, [(32, 92), (32, 56)], 5)
    trunk(d, [(32, 66), (23, 54)], 3); trunk(d, [(33, 64), (43, 52)], 3)
    for cx, cy, rx, ry, s, (a, b, c) in (
            (21, 50, 13, 12, 1, (GINKGO, GINKGO_HI, GINKGO_LO)), (44, 48, 13, 12, 2, (GINKGO, GINKGO_HI, GINKGO_LO)),
            (32, 32, 17, 16, 3, (GINKGO, GINKGO_HI, GINKGO_LO)), (32, 14, 11, 11, 4, (GINKGO_HI, GINKGO_HI, GINKGO))):
        blob(d, cx, cy, rx, ry, a, b, c, s)
    for i in range(22):
        x, y = 10 + (i * 13) % 44, 8 + (i * 29) % 50
        if im.getpixel((x, y))[3]:
            d.point((x, y), fill=(GINKGO_HI, GINKGO_LO, AMBER)[i % 3])
    for x, y in ((12, 90), (20, 93), (44, 91), (52, 93), (38, 94)):   # fallen leaves
        d.point((x, y), fill=GINKGO)
    outline(im)
    return im


# ---------------------------------------------------------------- Shirakawa-go
def gassho(cw, ch):
    def build():
        im, d = canvas(cw, ch)
        W, H = cw * 32, ch * 32
        cx = W // 2
        eave = H - 44                                             # where the thatch ends
        apex = 8
        half = cx - 3
        # the gable wall inside the thatch: dark boards
        for y in range(apex + 8, eave + 1):
            w = (y - apex) * half // (eave - apex) - 9
            if w > 0:
                d.line([(cx - w, y), (cx + w - 1, y)], fill=BOARD)
        for y in range(apex + 30, eave, 22):                      # the floors inside show as beams
            w = (y - apex) * half // (eave - apex) - 9
            d.line([(cx - w, y), (cx + w - 1, y)], fill=BOARD_LO)
            d.line([(cx - w, y + 1), (cx + w - 1, y + 1)], fill=THATCH_DK)
        # paper windows, tier by tier
        tiers = [(apex + 16, 1), (apex + 36, 2), (apex + 58, 3), (apex + 80, 4)]
        for y, n in tiers:
            if y + 14 > eave - 4:
                continue
            span = n * 13 - 3
            for i in range(n):
                x0 = cx - span // 2 + i * 13
                d.rectangle([x0, y, x0 + 9, y + 13], fill=BOARD_LO)
                d.rectangle([x0 + 1, y + 1, x0 + 8, y + 12], fill=PLASTER)
                d.line([(x0 + 4, y + 1), (x0 + 4, y + 12)], fill=BOARD_LO)
                d.line([(x0 + 5, y + 1), (x0 + 5, y + 12)], fill=PLASTER_LO)
                d.line([(x0 + 1, y + 6), (x0 + 8, y + 6)], fill=BOARD_LO)
        # the thatch: a thick band down each slope, cut ends showing in layers
        for y in range(apex, eave + 9):
            w = (y - apex) * half // (eave - apex)
            for side in (-1, 1):
                x_out = cx + side * (w + 2) - (1 if side > 0 else 0)
                for k in range(11):
                    x = x_out - side * k
                    if side * (x - cx) < 0 and y > apex + 4:
                        continue
                    col = THATCH_HI if (k < 2 and side < 0) else THATCH_LO if (k < 3 and side > 0) else THATCH
                    if (y + k * 2) % 6 == 0 and 2 <= k <= 9:
                        col = THATCH_DK if (y // 6 + k) % 2 else THATCH_LO
                    if 0 <= x < W:
                        d.point((x, y), fill=col)
        d.rectangle([1, eave + 6, 13, eave + 9], fill=THATCH_DK); d.rectangle([W - 14, eave + 6, W - 2, eave + 9], fill=THATCH_DK)
        # the ridge: straw bundles lashed over the top
        d.rectangle([cx - 9, apex - 5, cx + 8, apex + 3], fill=THATCH_HI)
        d.line([(cx - 9, apex + 3), (cx + 8, apex + 3)], fill=THATCH_DK)
        for x in range(cx - 7, cx + 8, 5):
            d.line([(x, apex - 5), (x, apex + 3)], fill=THATCH_LO)
        d.rectangle([cx - 12, apex - 2, cx - 10, apex + 1], fill=BOARD_LO); d.rectangle([cx + 9, apex - 2, cx + 11, apex + 1], fill=BOARD_LO)
        # the ground floor: boards, sliding doors, a paper screen
        y0 = eave + 2
        d.rectangle([14, y0, W - 15, H - 5], fill=BOARD)
        for x in range(16, W - 15, 5):
            d.line([(x, y0), (x, H - 5)], fill=BOARD_LO)
        d.line([(14, y0), (W - 15, y0)], fill=THATCH_DK)
        d.rectangle([cx - 13, y0 + 6, cx + 12, H - 5], fill=SOOT_LO)          # the doorway
        d.rectangle([cx - 11, y0 + 8, cx - 1, H - 5], fill=BOARD_LO); d.rectangle([cx + 1, y0 + 8, cx + 10, H - 5], fill=BOARD_LO)
        d.point((cx - 2, H - 20), fill=GOLD); d.point((cx + 2, H - 20), fill=GOLD)
        for x0 in (20, W - 20 - 22):
            d.rectangle([x0, y0 + 8, x0 + 21, H - 14], fill=BOARD_LO)
            d.rectangle([x0 + 1, y0 + 9, x0 + 20, H - 15], fill=PLASTER)
            for x in range(x0 + 5, x0 + 20, 5):
                d.line([(x, y0 + 9), (x, H - 15)], fill=BOARD_LO)
            d.line([(x0 + 1, y0 + 9 + (H - 24 - y0) // 2), (x0 + 20, y0 + 9 + (H - 24 - y0) // 2)], fill=BOARD_LO)
        d.rectangle([12, H - 5, W - 13, H - 1], fill=STONE_LO); d.line([(12, H - 5), (W - 13, H - 5)], fill=STONE)
        outline(im)
        return im
    return build


def paddy():
    """A harvested paddy: wet earth, rows of cut stubble, the sky in a puddle. Full bleed."""
    im = Image.new('RGBA', (32, 32), rgb('9c8a60'))
    px = im.load()
    for y in range(32):
        for x in range(32):
            if (x * 7 + y * 13) % 17 == 0:
                px[x, y] = rgb('8a7a55')
            if (x * 5 + y * 3) % 29 == 0:
                px[x, y] = rgb('ad9c6e')
    for row, y in enumerate(range(3, 32, 8)):                     # stubble, four rows a cell
        for x in range(2 + (row % 2) * 2, 32, 4):
            px[x, y] = rgb('e0cc86'); px[x, y + 1] = rgb('c2aa62'); px[x, (y + 2) % 32] = rgb('6f6247')
    for x, y, n in ((6, 15, 5), (19, 23, 6), (22, 7, 4)):         # standing water
        for i in range(n):
            px[x + i, y] = rgb('b9c9cf')
        px[x + 1, y] = rgb('e6eef0')
    return im


def hasa():
    im, d = canvas(3, 2)                 # 96 x 64
    d.ellipse([6, 55, 90, 63], fill=rgb('3a5f66', 150))
    for x in (8, 47, 86):                                         # posts, braced
        d.rectangle([x - 1, 8, x + 1, 60], fill=BOARD)
        d.line([(x + 1, 8), (x + 1, 60)], fill=BOARD_LO)
    for y in (14, 36):                                            # two rails of sheaves
        d.rectangle([4, y, 91, y + 1], fill=BOARD_LO)
        for i, x in enumerate(range(6, 88, 6)):
            d.polygon([(x, y + 1), (x + 5, y + 1), (x + 6, y + 18), (x - 1, y + 18)], fill=GINKGO if i % 3 else THATCH_HI)
            d.line([(x, y + 2), (x - 1, y + 18)], fill=GINKGO_HI)
            d.line([(x + 5, y + 2), (x + 6, y + 18)], fill=GINKGO_LO)
            d.line([(x, y + 5), (x + 5, y + 5)], fill=THATCH_LO)
            d.point((x + 2, y + 17), fill=THATCH_LO); d.point((x + 4, y + 16), fill=THATCH_LO)
    outline(im)
    return im


def suspension_bridge():
    im, d = canvas(8, 2)                 # 256 x 64: row 0 the far cable, row 1 the deck you walk on
    sag = lambda x: round(3 * (1 - ((x - 128) / 120) ** 2))       # the deck hangs a little in the middle
    # the deck: planks, with a rope rail along each edge
    for x in range(8, 248):
        y = 36 + sag(x)
        d.line([(x, y), (x, y + 21)], fill=WOOD if x % 6 else WOOD_LO)
        d.point((x, y), fill=rgb('d8ae94')); d.point((x, y + 21), fill=WOOD_DK); d.point((x, y + 22), fill=WOOD_DK)
        if x % 6 == 3:
            d.point((x, y + 5 + (x // 6) % 3 * 5), fill=WOOD_DK)
    for x in range(8, 248):                                       # the rails
        d.point((x, 33 + sag(x)), fill=STONE_DK)
        d.point((x, 60 + sag(x)), fill=SOOT_LO)
    for x in range(14, 246, 12):
        d.line([(x, 33 + sag(x)), (x, 36 + sag(x))], fill=STONE_DK)
        d.line([(x, 58 + sag(x)), (x, 60 + sag(x))], fill=SOOT_LO)
    # the far cable from tower to tower, and its hangers down to the deck
    cable = lambda x: round(6 + 22 * (1 - ((x - 128) / 118) ** 2))
    for x in range(10, 246):
        d.point((x, cable(x)), fill=SOOT_HI); d.point((x, cable(x) + 1), fill=SOOT_LO)
    for x in range(22, 240, 12):
        d.line([(x, cable(x) + 2), (x, 33 + sag(x))], fill=STONE_LO)
    # the towers at each bank
    for x0 in (2, 246):
        d.rectangle([x0, 2, x0 + 7, 61], fill=BENGARA)
        d.line([(x0, 2), (x0, 61)], fill=BENGARA_HI); d.line([(x0 + 7, 2), (x0 + 7, 61)], fill=BENGARA_DK)
        d.rectangle([x0 - 1, 2, x0 + 8, 5], fill=BENGARA_DK)
        d.rectangle([x0 - 1, 30, x0 + 8, 32], fill=BENGARA_DK)
        d.rectangle([x0 - 1, 58, x0 + 8, 62], fill=STONE_LO)
    outline(im)
    return im


def lookout():
    im, d = canvas(4, 1)                 # 128 x 32
    for x in (2, 34, 66, 98, 122):                                # posts
        d.rectangle([x, 8, x + 3, 30], fill=BOARD); d.line([(x + 3, 8), (x + 3, 30)], fill=BOARD_LO)
        d.point((x, 8), fill=WOOD)
    for y in (11, 20):                                            # rails
        d.rectangle([2, y, 125, y + 2], fill=WOOD_LO); d.line([(2, y), (125, y)], fill=WOOD)
    # the signboard: the village and its peaks
    d.rectangle([40, 1, 63, 19], fill=BOARD_LO)
    d.rectangle([41, 2, 62, 18], fill=CREAM)
    d.polygon([(43, 17), (50, 6), (57, 17)], fill=ROCKY); d.polygon([(48, 9), (50, 6), (52, 9)], fill=SNOW)
    d.polygon([(52, 17), (57, 10), (61, 17)], fill=ROCKY_LO)
    d.line([(42, 17), (61, 17)], fill=MAPLE)
    outline(im)
    return im


def peak():
    im, d = canvas(6, 4)                 # 192 x 128
    ridge = [(0, 122), (14, 100), (30, 84), (44, 58), (58, 44), (72, 22), (88, 6), (100, 16),
             (112, 12), (126, 36), (142, 52), (156, 78), (172, 96), (191, 120)]

    def top(x):
        for (x0, y0), (x1, y1) in zip(ridge, ridge[1:]):
            if x0 <= x <= x1:
                return round(y0 + (y1 - y0) * (x - x0) / max(1, x1 - x0))
        return 127

    for x in range(192):
        t = top(x)
        for y in range(t, 128):
            h = y - t
            lit = x < 96 + (y - 6) // 6
            snowline = 30 + ((x * 7) % 11) + (8 if (x // 9) % 2 else 0)
            treeline = 78 + ((x * 5) % 9) - (6 if (x // 13) % 2 else 0)
            if y < snowline and h < 40:
                col = SNOW if lit else SNOW_LO
            elif y < treeline:
                col = ROCKY_HI if (lit and h < 3) else ROCKY if lit else ROCKY_LO
                if (x * 3 + y * 5) % 23 == 0:
                    col = SNOW_LO if y < snowline + 16 else ROCKY_LO
            else:
                bx, by = (x + (y // 3) % 2 * 2) // 4, y // 3          # clumps of foliage, not single pixels
                k = (((bx * 73856093) ^ (by * 19349663)) >> 4) % 16
                col = (PINE_LO, PINE, MAPLE, PINE, MAPLE_OR, PINE_LO, GINKGO_LO, PINE,
                       PINE, PINE_LO, PINE, GINKGO_LO, MAPLE, PINE, PINE_LO, PINE_HI)[k]
                if not lit and col in (MAPLE_OR, GINKGO, MAPLE_HI, PINE_HI):
                    col = PINE_LO
            d.point((x, y), fill=col)
    for x0, y0, x1, y1 in ((88, 6, 76, 44), (112, 12, 122, 50), (58, 44, 50, 74), (142, 52, 150, 80)):   # gullies
        d.line([(x0, y0 + 4), (x1, y1)], fill=ROCKY_LO)
    outline(im)
    return im


def bear_sign():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([14, 30, 17, 61], fill=BOARD); d.line([(17, 30), (17, 61)], fill=BOARD_LO)
    d.rectangle([11, 59, 20, 62], fill=STONE_LO)
    d.rectangle([3, 6, 28, 32], fill=AMBER)
    d.rectangle([3, 6, 28, 8], fill=rgb('fbe07a')); d.rectangle([3, 30, 28, 32], fill=GOLD_LO)
    d.rectangle([3, 6, 28, 11], fill=RED); d.line([(7, 8), (24, 8)], fill=WHITE)
    # the bear: head, ears, a muzzle
    d.ellipse([9, 15, 22, 28], fill=SOOT_LO)
    d.ellipse([8, 13, 12, 17], fill=SOOT_LO); d.ellipse([19, 13, 23, 17], fill=SOOT_LO)
    d.ellipse([13, 21, 18, 26], fill=BOARD); d.point((15, 22), fill=SOOT_LO)
    d.point((12, 19), fill=WHITE); d.point((19, 19), fill=WHITE)
    outline(im)
    return im


# ---------------------------------------------------------------- Toyama
def glass_museum():
    im, d = canvas(6, 6)                 # 192 x 192; the doors are columns 2-3 (x 64-127)
    d.rectangle([6, 12, 185, 187], fill=ALU)
    # the facade: tall strips of glass, granite and aluminium set at different angles
    strip = (GLASS_HI, ALU, WHITE, STONE, GLASS, ALU, rgb('a9c4dc'), WHITE, STONE_LO, GLASS_HI, ALU_LO)
    for i, x in enumerate(range(6, 186, 5)):
        y = 12
        k = i * 7
        while y < 150:
            h = 14 + (k * 5) % 23
            col = strip[k % len(strip)]
            d.rectangle([x, y, x + 4, min(149, y + h)], fill=col)
            d.line([(x, y), (x, min(149, y + h))], fill=WHITE if col in (GLASS_HI, GLASS, ALU) else ALU)
            d.line([(x + 4, y), (x + 4, min(149, y + h))], fill=ALU_LO)
            if col in (GLASS, GLASS_HI) and h > 16:
                d.point((x + 2, y + 3), fill=WHITE); d.point((x + 1, y + 4), fill=WHITE)
            y += h + 1
            k += 3
    # the cedar atrium, seen through a tall slot of clear glass
    d.rectangle([80, 30, 111, 149], fill=GLASS_DK)
    for i, y in enumerate(range(34, 148, 7)):
        x0 = 82 + (i * 5) % 9
        d.line([(x0, y), (x0 + 18, y)], fill=WOOD); d.line([(x0, y + 1), (x0 + 18, y + 1)], fill=WOOD_LO)
        d.point((x0 + 4, y), fill=rgb('e8c9a0'))
    d.line([(80, 30), (80, 149)], fill=GLASS_HI); d.line([(111, 30), (111, 149)], fill=GLASS_DK)
    d.rectangle([4, 8, 187, 12], fill=ALU_LO); d.line([(4, 8), (187, 8)], fill=WHITE)
    d.rectangle([182, 12, 185, 187], fill=ALU_LO)
    # the ground floor: a glass wall under a canopy, the name on the fascia
    d.rectangle([2, 150, 189, 160], fill=STONE_DK); d.line([(2, 150), (189, 150)], fill=STONE_LO)
    text(d, 'GLASS', 96 - text_width('GLASS', 2) // 2, 152, WHITE, gap=2)
    d.rectangle([6, 161, 185, 187], fill=GLASS)
    d.rectangle([6, 161, 185, 163], fill=GLASS_HI)
    for x in range(6, 186, 15):
        d.line([(x, 161), (x, 187)], fill=ALU_LO)
    for x, y in ((14, 170), (44, 176), (148, 168), (170, 178)):   # things that glitter inside
        d.point((x, y), fill=WHITE); d.point((x + 1, y + 1), fill=GLASS_HI)
        d.ellipse([x + 5, y + 2, x + 9, y + 8], fill=(TEAL_HI, AMBER, RED_HI, GLASS_HI)[(x // 7) % 4])
    d.rectangle([66, 162, 125, 187], fill=GLASS_DK)               # the doors
    for x0 in (68, 97):
        d.rectangle([x0, 164, x0 + 27, 187], fill=rgb('6f8fc4'))
        d.line([(x0, 164), (x0 + 27, 164)], fill=GLASS_HI); d.line([(x0 + 13, 165), (x0 + 13, 187)], fill=GLASS_DK)
    d.rectangle([2, 188, 189, 191], fill=STONE_LO); d.line([(2, 188), (189, 188)], fill=STONE)
    outline(im)
    return im


def tram():
    im, d = canvas(5, 2)                 # 160 x 64
    d.ellipse([8, 54, 152, 63], fill=rgb('1f2a3a', 120))
    # the body: two low cars and a short middle section, rounded ends
    d.rounded_rectangle([4, 18, 155, 58], radius=9, fill=WHITE)
    d.rectangle([4, 46, 155, 58], fill=TEAL)
    d.rounded_rectangle([4, 46, 155, 58], radius=6, fill=TEAL)
    d.rectangle([10, 46, 149, 50], fill=TEAL)
    d.line([(8, 46), (151, 46)], fill=TEAL_HI); d.rectangle([10, 55, 149, 58], fill=TEAL_LO)
    d.line([(12, 18), (147, 18)], fill=WHITE); d.rectangle([10, 19, 149, 21], fill=ALU)
    for x0, x1 in ((10, 66), (74, 86), (94, 149)):                # the window band
        d.rectangle([x0, 24, x1, 42], fill=GLASS_DK)
        d.rectangle([x0 + 1, 25, x1 - 1, 41], fill=GLASS)
        d.line([(x0 + 1, 25), (x1 - 1, 25)], fill=GLASS_HI)
    for x in (24, 38, 52, 108, 122, 136):
        d.line([(x, 25), (x, 41)], fill=GLASS_DK)
    for x0 in (28, 112):                                          # doors
        d.rectangle([x0, 24, x0 + 19, 54], fill=ALU_LO)
        d.rectangle([x0 + 1, 26, x0 + 9, 52], fill=GLASS); d.rectangle([x0 + 11, 26, x0 + 18, 52], fill=GLASS)
        d.line([(x0 + 1, 26), (x0 + 9, 26)], fill=GLASS_HI); d.line([(x0 + 11, 26), (x0 + 18, 26)], fill=GLASS_HI)
    for x in (70, 90):
        d.rectangle([x, 20, x + 2, 56], fill=SOOT_HI)             # the joints between the cars
    d.rectangle([6, 34, 8, 40], fill=AMBER); d.rectangle([151, 34, 153, 40], fill=RED)   # head and tail lamps
    for x in (22, 56, 104, 138):                                  # wheels under the skirts
        d.ellipse([x - 4, 55, x + 4, 62], fill=SOOT); d.point((x, 58), fill=STONE_LO)
    # the pantograph
    d.rectangle([70, 14, 92, 17], fill=SOOT_HI)
    d.line([(74, 14), (84, 4), (90, 14)], fill=SOOT_LO)
    d.line([(76, 3), (92, 3)], fill=SOOT_LO, width=2)
    outline(im)
    return im


def tram_rail():
    """road-plain with a pair of rails let into it, running east-west. Full bleed."""
    im = Image.open('assets/sprites/road-plain_0_0.png').convert('RGBA')
    px = im.load()
    for y0 in (18, 44):
        for x in range(64):
            px[x, y0] = rgb('3a3f4a'); px[x, y0 + 1] = rgb('c9d1d6')
            px[x, y0 + 2] = rgb('8c97a3'); px[x, y0 + 3] = rgb('3a3f4a')
    return im


def tram_stop():
    im, d = canvas(3, 2)                 # 96 x 64
    d.rectangle([2, 54, 93, 62], fill=STONE); d.line([(2, 54), (93, 54)], fill=WHITE)   # the platform
    d.rectangle([2, 60, 93, 62], fill=STONE_LO)
    for x in range(4, 93, 6):
        d.point((x, 55), fill=AMBER); d.point((x + 1, 55), fill=AMBER)   # the tactile strip
    for x in (10, 82):                                            # the shelter
        d.rectangle([x, 12, x + 2, 54], fill=ALU_LO); d.line([(x, 12), (x, 54)], fill=WHITE)
    d.rectangle([4, 6, 91, 12], fill=TEAL); d.line([(4, 6), (91, 6)], fill=TEAL_HI)
    d.line([(4, 12), (91, 12)], fill=TEAL_LO)
    d.rectangle([14, 16, 80, 40], fill=rgb('7db9fa', 110))        # the glass back
    d.line([(14, 16), (80, 16)], fill=WHITE); d.line([(47, 16), (47, 40)], fill=ALU_LO)
    d.rectangle([22, 44, 60, 47], fill=WOOD); d.line([(22, 44), (60, 44)], fill=rgb('d8ae94'))   # a bench
    d.rectangle([24, 48, 25, 53], fill=SOOT_HI); d.rectangle([57, 48, 58, 53], fill=SOOT_HI)
    d.rectangle([66, 20, 78, 38], fill=WHITE); d.rectangle([66, 20, 78, 23], fill=TEAL)          # the timetable
    for y in range(26, 37, 3):
        d.line([(68, y), (76, y)], fill=STONE_LO)
    outline(im)
    return im


def ramen_shop():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1
    rows = roof_rows(10, 32, (10, 117), (0, 127))
    tiled_roof(d, rows, SOOT_HI, SOOT_LO, STONE_DK)
    d.rectangle([8, 5, 119, 10], fill=SOOT_LO); d.line([(8, 5), (119, 5)], fill=STONE_DK)
    d.rectangle([0, 32, 127, 34], fill=SOOT_LO)
    # the upper wall: black-stained boards and the shop's board
    d.rectangle([3, 35, 124, 76], fill=SOOT)
    for x in range(6, 124, 6):
        d.line([(x, 35), (x, 76)], fill=SOOT_LO)
    d.line([(3, 35), (3, 76)], fill=SOOT_HI)
    d.rectangle([18, 42, 85, 68], fill=BOARD_LO)
    d.rectangle([20, 44, 83, 66], fill=CREAM)
    # ラ ー メ ン, left to right (the long mark lies flat in horizontal text)
    x = 24
    for name in ('ra', 'bar', 'me', 'n'):
        g = GLYPHS[name]
        if name == 'bar':
            d.line([(x, 54), (x + 8, 54)], fill=SOOT_LO); d.line([(x, 55), (x + 8, 55)], fill=SOOT_LO)
        else:
            for gy, row in enumerate(g):
                for gx, c in enumerate(row):
                    if c == '#':
                        d.point((x + gx, 50 + gy), fill=SOOT_LO)
        x += 15
    d.ellipse([94, 42, 118, 66], fill=SOOT_LO)                    # a black bowl on a red disc
    d.ellipse([96, 44, 116, 64], fill=RED)
    d.pieslice([99, 46, 113, 62], 0, 180, fill=SOOT_LO)
    d.line([(99, 54), (113, 54)], fill=SOOT_HI)
    for sx in (103, 106, 109):
        d.line([(sx, 48), (sx + 1, 52)], fill=WHITE)              # steam
    # the pent roof
    rows = roof_rows(77, 86, (4, 123), (0, 127))
    tiled_roof(d, rows, SOOT_HI, SOOT_LO, STONE_DK)
    d.rectangle([0, 86, 127, 88], fill=SOOT_LO)
    # the ground floor: the lit counter and its seven stools, the door under a black noren
    d.rectangle([3, 89, 124, 123], fill=SOOT)
    for x in range(6, 124, 6):
        d.line([(x, 89), (x, 123)], fill=SOOT_LO)
    d.rectangle([66, 92, 121, 118], fill=SOOT_LO)
    d.rectangle([68, 94, 119, 116], fill=LIT)
    d.rectangle([68, 94, 119, 96], fill=LIT_HI)
    d.rectangle([68, 106, 119, 108], fill=BOARD)
    for x in range(71, 118, 7):
        d.rectangle([x, 109, x + 3, 110], fill=RED_LO); d.line([(x + 1, 111), (x + 1, 116)], fill=SOOT_LO)
        d.ellipse([x, 100, x + 4, 104], fill=SOOT)                # a bowl at each place
    d.rectangle([34, 90, 61, 123], fill=SOOT_LO)
    d.rectangle([36, 104, 59, 123], fill=LIT)
    d.line([(47, 104), (47, 123)], fill=SOOT_LO)
    d.rectangle([34, 90, 61, 104], fill=SOOT_HI)
    for x in (43, 52):
        d.line([(x, 93), (x, 104)], fill=SOOT_LO)
    for x in (38, 47, 56):
        d.ellipse([x - 2, 95, x + 2, 99], outline=WHITE)
    d.rectangle([8, 96, 24, 118], fill=RED)                       # the red lantern
    d.rectangle([8, 96, 24, 98], fill=SOOT_LO); d.rectangle([8, 116, 24, 118], fill=SOOT_LO)
    d.line([(8, 99), (8, 115)], fill=RED_HI); d.rectangle([21, 99, 24, 115], fill=RED_LO)
    for y in range(102, 114, 4):
        d.line([(9, y), (23, y)], fill=RED_LO)
    d.rectangle([15, 92, 17, 95], fill=SOOT_LO)
    d.rectangle([0, 124, 127, 127], fill=STONE_LO); d.line([(0, 124), (127, 124)], fill=STONE)
    outline(im)
    return im


def port_tower():
    im, d = canvas(3, 7)                 # 96 x 224
    cx = 48
    # the stone podium
    for y in range(190, 222):
        w = 30 + (y - 190) * 10 // 32
        d.line([(cx - w, y), (cx + w - 1, y)], fill=STONE)
        d.point((cx - w, y), fill=WHITE); d.line([(cx + w - 6, y), (cx + w - 1, y)], fill=STONE_LO)
    for y in range(198, 222, 8):
        d.line([(cx - 38, y), (cx + 37, y)], fill=STONE_LO)
    d.rectangle([cx - 8, 200, cx + 7, 221], fill=SOOT_LO)          # the entrance
    d.rectangle([cx - 6, 202, cx + 5, 221], fill=GLASS); d.line([(cx - 6, 202), (cx + 5, 202)], fill=GLASS_HI)
    d.line([(cx, 202), (cx, 221)], fill=SOOT_LO)
    d.rectangle([cx - 42, 221, cx + 41, 223], fill=STONE_LO)
    # the shaft: white, tapering, a slit window on each floor
    for y in range(74, 190):
        w = 13 + (y - 74) * 12 // 116
        d.line([(cx - w, y), (cx + w - 1, y)], fill=PLASTER)
        d.line([(cx - w, y), (cx - w + 1, y)], fill=WHITE)
        d.line([(cx + w - 5, y), (cx + w - 1, y)], fill=PLASTER_LO)
    for y in range(92, 186, 24):
        d.rectangle([cx - 2, y, cx + 1, y + 10], fill=GLASS_DK); d.point((cx - 2, y), fill=GLASS_HI)
        w = 13 + (y + 16 - 74) * 12 // 116
        d.line([(cx - w, y + 16), (cx + w - 1, y + 16)], fill=PLASTER_LO)
    # the gallery brackets, the observation room, its balcony
    for i in range(8):
        d.line([(cx - 14 - i * 2, 74 - i), (cx + 13 + i * 2, 74 - i)], fill=PLASTER_LO if i % 2 else PLASTER)
    d.rectangle([cx - 31, 62, cx + 30, 66], fill=STONE_LO); d.line([(cx - 31, 62), (cx + 30, 62)], fill=WHITE)
    for x in range(cx - 30, cx + 30, 4):
        d.line([(x, 54), (x, 62)], fill=STONE_DK)                 # the rail
    d.line([(cx - 31, 54), (cx + 30, 54)], fill=STONE_DK)
    d.rectangle([cx - 24, 34, cx + 23, 61], fill=PLASTER)
    d.rectangle([cx - 22, 38, cx + 21, 56], fill=GLASS_DK)
    d.rectangle([cx - 21, 39, cx + 20, 55], fill=GLASS)
    d.line([(cx - 21, 39), (cx + 20, 39)], fill=GLASS_HI)
    for x in range(cx - 14, cx + 20, 7):
        d.line([(x, 39), (x, 55)], fill=PLASTER)
    d.rectangle([cx + 19, 34, cx + 23, 61], fill=PLASTER_LO)
    # the lantern roof and its finial
    rows = roof_rows(14, 32, (cx - 8, cx + 7), (cx - 34, cx + 33))
    tiled_roof(d, rows)
    d.rectangle([cx - 35, 32, cx + 34, 34], fill=SLATE_LO)
    for sx, x in ((1, cx - 35), (-1, cx + 34)):
        d.polygon([(x, 33), (x + sx * 7, 33), (x, 26)], fill=SLATE)
    d.rectangle([cx - 4, 8, cx + 3, 14], fill=SLATE_LO)
    d.ellipse([cx - 4, 1, cx + 3, 8], fill=GOLD); d.point((cx - 2, 3), fill=GOLD_HI)
    outline(im)
    return im


SPRITES = {      # key: (builder, scale, tileNames label)
    'kanazawa-ishikawa-gate_0_0': (ishikawa_gate, 2, 'kanazawa-ishikawa-gate'),
    'kanazawa-kotoji_0_0': (kotoji, 2, 'kanazawa-kotoji'),
    'kanazawa-chaya-a_0_0': (chaya((INDIGO, INDIGO_HI, WHITE), (0, 2)), 2, 'kanazawa-chaya-a'),
    'kanazawa-chaya-b_0_0': (chaya((CREAM, WHITE, BENGARA), (1, 2, 3)), 2, 'kanazawa-chaya-b'),
    'kanazawa-whisky-bar_0_0': (whisky_bar, 2, 'kanazawa-whisky-bar'),
    'kanazawa-canal-bridge_0_0': (canal_bridge, 2, 'kanazawa-canal-bridge'),
    'hokuriku-ginkgo_0_0': (ginkgo, 2, 'hokuriku-ginkgo'),
    'shirakawa-gassho_0_0': (gassho(5, 5), 2, 'shirakawa-gassho'),
    'shirakawa-gassho-small_0_0': (gassho(4, 4), 2, 'shirakawa-gassho-small'),
    'shirakawa-paddy_0_0': (paddy, 2, 'shirakawa-paddy'),
    'shirakawa-hasa_0_0': (hasa, 2, 'shirakawa-hasa'),
    'shirakawa-bridge_0_0': (suspension_bridge, 2, 'shirakawa-bridge'),
    'shirakawa-lookout_0_0': (lookout, 2, 'shirakawa-lookout'),
    'shirakawa-peak_0_0': (peak, 2, 'shirakawa-peak'),
    'shirakawa-bear-sign_0_0': (bear_sign, 2, 'shirakawa-bear-sign'),
    'toyama-glass-museum_0_0': (glass_museum, 2, 'toyama-glass-museum'),
    'toyama-tram_0_0': (tram, 2, 'toyama-tram'),
    'toyama-tram-rail_0_0': (tram_rail, 1, 'toyama-tram-rail'),
    'toyama-tram-stop_0_0': (tram_stop, 2, 'toyama-tram-stop'),
    'toyama-ramen_0_0': (ramen_shop, 2, 'toyama-ramen'),
    'toyama-port-tower_0_0': (port_tower, 2, 'toyama-port-tower'),
}

# Flat decks you walk ON: Non-Collidables with a depth nudge that puts them over
# the Water layer and under everyone standing on them (the asahikawa-bridge
# recipe, see generate_hokkaido.FLAT).
FLAT = {'kanazawa-canal-bridge_0_0': -200, 'shirakawa-bridge_0_0': -200}
# Worth looking up at (config game.lookUp.sprites: family -> 0 for a one-sprite landmark)
LOOK_UP = {'toyama-port-tower': 0}


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
        if key in FLAT:
            cfg['spriteMetadata'][key]['depthBias'] = FLAT[key]
        cfg.setdefault('tileNames', {})[key] = label
    cfg['game'].setdefault('lookUp', {}).setdefault('sprites', {}).update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        ims = list(built.values())
        rows, row, width = [], [], 0
        for im in ims:                                            # wrap the sheet at ~1500px
            if width + im.width > 1500 and row:
                rows.append(row); row, width = [], 0
            row.append(im); width += im.width + 16
        rows.append(row)
        heights = [max(i.height for i in r) + 16 for r in rows]
        sheet = Image.new('RGBA', (1540, sum(heights) + 16), rgb('83af6f'))
        y = 16
        for r, h in zip(rows, heights):
            x = 16
            for im in r:
                sheet.alpha_composite(im, (x, y + h - 16 - im.height)); x += im.width + 16
            y += h
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
