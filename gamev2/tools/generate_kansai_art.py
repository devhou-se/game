#!/usr/bin/env python3
"""generate_kansai_art.py — draw the Kansai sprites (issue #255): Himeji, and
the fingerpost where Osaka and Himeji meet.

No asset pack has them, so they are drawn here the way
tools/generate_hokuriku_art.py draws Hokuriku (it imports that file's and
Sendai's palette and helpers): shaded pixel art in the GuttyKreum palette, at
half size and pixel-doubled, with a 1px ink outline. Nothing here is a white
line-art placeholder.

Himeji
  himeji-keep_0_0          10x8  the castle: the white main keep, five roofs of
                                 grey tiles pointed with white plaster over a
                                 battered stone base, the west small keep joined
                                 to it by a corridor. Exactly its footprint: it
                                 stands on the district's top row, so nothing
                                 may overhang
  himeji-turret_0_0        3x4   a white corner turret on its stone base
  himeji-gate_0_0          6x4   the gatehouse at the bridgehead: a white storey
                                 on two stone piers; the gateway is columns 2-3
  himeji-bridge_0_0        2x4   a timber bridge with capped posts, walked
                                 north-south (flat: Non-Collidables + depthBias,
                                 walked ON). The moat's, and Koko-en's pond's
  himeji-kokoen-gate_0_0   4x3   Koko-en's roofed gate in the garden's earthen
                                 wall; the gateway is columns 1-2
  himeji-wall_0_0          1x2   one column of the castle's white wall: a tiled
                                 coping, loopholes, a stone footing. Tiles side
                                 by side into a run of any length and fills
                                 both its cells
Kansai
  kansai-fingerpost_0_0    1x2   a wooden fingerpost, one arm west, one east

Deterministic and idempotent: rewrites the PNGs in assets/sprites/, registers
them in config.json spriteMetadata + tileNames, and asks the camera to look up
at the keep (game.lookUp.sprites). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py and the generators:
    python3 tools/generate_kansai_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (CLEAR, rgb, canvas, outline, INK, CREAM, WHITE, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GOLD)
from generate_sendai_art import (roof_rows, coping, plaster, footing, LACQUER_LO, GOLD_HI, GOLD_LO,
                                 SLATE_LO)
from generate_hokuriku_art import masonry, PLASTER, PLASTER_LO, BOARD, BOARD_LO

# Himeji's roofs: grey tiles with every joint sealed in white plaster, which is
# why the whole castle reads white
ROOF, ROOF_HI, ROOF_LO, ROOF_DK = rgb('8794a6'), rgb('d5dce4'), rgb('66748a'), rgb('4a566c')
PLANK, PLANK_HI = rgb('a97c62'), rgb('d8ae94')
BRONZE, BRONZE_HI = rgb('6f7f6a'), rgb('a3b596')


def castle_roof(d, rows):
    """A fall of Himeji's tiles over (y, x0, x1) scanlines: plaster ribs down the
    slope, a darker line under each course, lit on the left and shaded on the right."""
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=ROOF_LO if y % 5 == 4 else ROOF_HI if x % 4 == 0 else ROOF)
        d.point((x0, y), fill=ROOF_HI); d.point((x0 + 1, y), fill=ROOF_HI)
        d.point((x1, y), fill=ROOF_LO); d.point((x1 - 1, y), fill=ROOF_LO)


def eave(d, x0, x1, y, lift=4):
    """The eave under a roof, two pixels deep from y: the round tile ends, and
    the corners turned up."""
    d.rectangle([x0, y, x1, y + 1], fill=ROOF_LO)
    for x in range(x0 + 2, x1, 4):
        d.point((x, y + 1), fill=ROOF_HI)
    d.line([(x0, y + 2), (x1, y + 2)], fill=ROOF_DK)
    if lift:
        for sx, x in ((1, x0), (-1, x1)):
            d.polygon([(x, y + 1), (x + sx * (lift + 3), y + 1), (x, y - lift)], fill=ROOF)
            d.line([(x, y - lift), (x, y + 1)], fill=ROOF_HI if sx > 0 else ROOF_LO)


def ridge(d, x0, x1, y):
    """A ridge five pixels deep from y, a shachi (the roof's fish) on each end."""
    d.rectangle([x0, y, x1, y + 4], fill=ROOF_LO); d.line([(x0, y), (x1, y)], fill=ROOF_HI)
    for x in range(x0 + 3, x1, 5):
        d.point((x, y + 2), fill=ROOF_HI)
    for sx, x in ((1, x0), (-1, x1)):
        d.polygon([(x - sx * 2, y + 4), (x + sx * 4, y + 4), (x + sx * 4, y - 1), (x + sx, y - 5), (x - sx * 2, y - 1)],
                  fill=ROOF)
        d.point((x, y - 2), fill=ROOF_HI); d.point((x + sx * 2, y), fill=ROOF_DK)


def white_wall(d, x0, y0, x1, y1):
    """A storey of white plaster: lit on the left, shaded on the right and under the eave above."""
    d.rectangle([x0, y0, x1, y1], fill=PLASTER)
    d.line([(x0, y0), (x0, y1)], fill=WHITE)
    d.rectangle([x1 - 3, y0, x1, y1], fill=PLASTER_LO)
    d.rectangle([x0, y0, x1, y0 + 1], fill=PLASTER_LO)


def lattice_windows(d, xs, y0, y1, w=6):
    """The keep's windows: dark openings behind white bars."""
    for x in xs:
        d.rectangle([x, y0, x + w - 1, y1], fill=SLATE_LO)
        for bx in range(x + 1, x + w - 1, 2):
            d.line([(bx, y0 + 1), (bx, y1)], fill=PLASTER)
        d.line([(x - 1, y1 + 1), (x + w, y1 + 1)], fill=PLASTER_LO)


def spread(x0, x1, n, w=6):
    """`n` windows of width `w`, evenly spaced between x0 and x1: their left edges."""
    gap = (x1 - x0 + 1 - n * w) / (n + 1)
    return [round(x0 + gap * (i + 1) + w * i) for i in range(n)]


def chidori(d, cx, apex, base, half):
    """A triangular dormer gable (chidori-hafu): tiled slopes round a white face."""
    for y in range(apex, base + 1):
        w = (y - apex) * half // max(1, base - apex)
        d.line([(cx - w, y), (cx + w, y)], fill=ROOF)
        d.point((cx - w, y), fill=ROOF_HI); d.point((cx - w + 1, y), fill=ROOF_HI)
        d.point((cx + w, y), fill=ROOF_DK); d.point((cx + w - 1, y), fill=ROOF_LO)
        inner = w - 5
        if inner > 0 and y < base:
            d.line([(cx - inner, y), (cx + inner, y)], fill=PLASTER)
            d.point((cx + inner, y), fill=PLASTER_LO)
    d.line([(cx - half + 4, base), (cx + half - 4, base)], fill=ROOF_LO)
    if half > 12:
        d.rectangle([cx - 2, base - 8, cx + 1, base - 3], fill=SLATE_LO)
        d.line([(cx, base - 7), (cx, base - 3)], fill=PLASTER)
    d.point((cx, apex), fill=ROOF_HI); d.point((cx, apex + 1), fill=GOLD)


def karahafu(d, cx, y, half, depth):
    """A cusped gable (kara-hafu): the eave swells up over a white panel."""
    d.pieslice([cx - half, y - depth, cx + half, y + depth], 180, 360, fill=ROOF)
    d.pieslice([cx - half + 4, y - depth + 4, cx + half - 4, y + depth - 4], 180, 360, fill=PLASTER)
    d.arc([cx - half, y - depth, cx + half, y + depth], 180, 270, fill=ROOF_HI)
    d.arc([cx - half, y - depth, cx + half, y + depth], 270, 360, fill=ROOF_LO)
    d.line([(cx - half + 3, y), (cx + half - 3, y)], fill=ROOF_LO)
    d.point((cx, y - depth + 2), fill=GOLD)


def stone_base(im, x0, y0, x1, y1, lean, seed=0):
    """A battered stone base laid over what is drawn: `lean` pixels narrower at the top on each side."""
    layer = Image.new('RGBA', im.size, CLEAR)
    d = ImageDraw.Draw(layer)
    masonry(d, x0, y0, x1, y1, seed)
    d.polygon([(x0 - 1, y0 - 1), (x0 + lean, y0 - 1), (x0 - 1, y1 + 1)], fill=CLEAR)
    d.polygon([(x1 + 1, y0 - 1), (x1 - lean, y0 - 1), (x1 + 1, y1 + 1)], fill=CLEAR)
    for y in range(y0, y1 + 1):                                   # its two corners: an ink edge, lit and shaded
        t = (y1 - y) * lean // max(1, y1 - y0)
        d.point((x0 + t, y), fill=INK); d.point((x0 + t + 1, y), fill=WHITE)
        d.point((x1 - t, y), fill=INK); d.point((x1 - t - 1, y), fill=STONE_LO); d.point((x1 - t - 2, y), fill=STONE_LO)
    im.alpha_composite(layer)


def storeys(im, d, cx, tiers, base):
    """A keep or a turret: `tiers` from the top, each (roof y0, roof y1, the
    roof's top half-width, its eave half-width, the wall's bottom y, the wall's
    half-width, windows), on a stone `base` (y0, y1, half-width at the foot, lean, seed)."""
    for y0, y1, top, out, wy, wall, n in tiers:
        white_wall(d, cx - wall, y1 + 1, cx + wall - 1, wy)
        if n:
            lattice_windows(d, spread(cx - wall + 3, cx + wall - 5, n), y1 + 6, min(wy - 3, y1 + 14))
    by0, by1, foot, lean, seed = base
    stone_base(im, cx - foot, by0, cx + foot - 1, by1, lean, seed)
    d = ImageDraw.Draw(im)
    for y0, y1, top, out, wy, wall, n in tiers:
        castle_roof(d, roof_rows(y0, y1, (cx - top, cx + top - 1), (cx - out, cx + out - 1)))
        d.line([(cx - top, y0), (cx + top - 1, y0)], fill=ROOF_LO)
        eave(d, cx - out, cx + out - 1, y1 + 1)
    return d


# ---------------------------------------------------------------- Himeji
def keep():
    im, d = canvas(10, 8)                # 320 x 256: nothing above y 1, the castle fills its footprint
    # ---- the stone terrace everything stands on, and the corridors between the keeps
    masonry(d, 1, 216, 318, 254, 5)
    white_wall(d, 58, 166, 92, 215)                               # the corridor from the small keep
    lattice_windows(d, (66, 78), 176, 184)
    lattice_windows(d, (66, 78), 196, 204)
    castle_roof(d, [(y, 54, 96) for y in range(152, 165)]); eave(d, 54, 96, 165, lift=0)
    white_wall(d, 272, 186, 314, 215)                             # and the one running off east
    lattice_windows(d, (282, 296), 194, 203)
    castle_roof(d, [(y, 268, 318) for y in range(172, 185)]); eave(d, 268, 318, 185, lift=0)
    for x in (286, 302):
        d.point((x, 208), fill=SLATE_LO); d.point((x + 1, 208), fill=SLATE_LO)      # loopholes
    # ---- the west small keep: three storeys on its own tall base
    d = storeys(im, d, 36, [(86, 101, 12, 25, 115, 17, 2),
                            (116, 131, 19, 30, 149, 22, 3),
                            (150, 165, 24, 34, 185, 27, 3)],
                (186, 254, 34, 6, 2))
    ridge(d, 26, 46, 81)
    karahafu(d, 36, 132, 9, 7)
    # ---- the main keep: five roofs, the gables every picture of it has
    cx = 178
    d = storeys(im, d, cx, [(13, 30, 22, 44, 46, 30, 5),
                            (47, 64, 34, 58, 82, 46, 6),
                            (83, 102, 50, 74, 122, 62, 8),
                            (123, 144, 66, 88, 166, 76, 9),
                            (167, 186, 80, 98, 205, 88, 10)],
                (206, 254, 100, 10, 1))
    ridge(d, cx - 22, cx + 21, 8)
    karahafu(d, cx, 65, 15, 11)                                   # the cusped gable under the top storey
    chidori(d, cx - 30, 84, 103, 15); chidori(d, cx + 30, 84, 103, 15)    # the pair of dormers
    chidori(d, cx, 116, 145, 32)                                  # the great gable
    karahafu(d, cx, 187, 17, 10)
    d.rectangle([cx - 5, 190, cx + 4, 199], fill=SLATE_LO)        # the bell-shaped window under it
    for bx in range(cx - 4, cx + 4, 2):
        d.line([(bx, 191), (bx, 199)], fill=PLASTER)
    outline(im)
    return im


def turret():
    im, d = canvas(3, 4)                 # 96 x 128
    d = storeys(im, d, 48, [(16, 35, 16, 40, 49, 27, 3),
                            (50, 63, 30, 44, 93, 35, 4)],
                (94, 126, 43, 6, 4))
    ridge(d, 33, 62, 11)
    chidori(d, 48, 44, 64, 14)
    for x in (22, 46, 70):                                        # loopholes under the windows
        d.rectangle([x, 82, x + 3, 86], fill=SLATE_LO)
    outline(im)
    return im


def gate():
    im, d = canvas(6, 4)                 # 192 x 128; the gateway is columns 2-3 (x 64-127)
    # ---- the stone piers either side
    for x0, x1, s in ((1, 62, 6), (129, 190, 7)):
        masonry(d, x0, 58, x1, 126, s)
    # ---- the gate: posts, the leaves folded back, a lintel studded with iron
    for x0 in (60, 124):
        d.rectangle([x0, 58, x0 + 7, 126], fill=WOOD_LO)
        d.line([(x0, 58), (x0, 126)], fill=WOOD); d.line([(x0 + 7, 58), (x0 + 7, 126)], fill=WOOD_DK)
        for y in (74, 98, 118):
            d.rectangle([x0, y, x0 + 7, y + 2], fill=LACQUER_LO)   # iron bands
        d.rectangle([x0 - 1, 122, x0 + 8, 126], fill=STONE_LO)
    for x0, x1 in ((68, 73), (118, 123)):
        d.rectangle([x0, 64, x1, 124], fill=WOOD_DK)
        d.line([(x0 + 2, 66), (x0 + 2, 123)], fill=WOOD_LO)
        for y in (78, 102):
            d.point((x0 + 4, y), fill=GOLD)
    d.rectangle([56, 52, 135, 63], fill=WOOD_LO); d.line([(56, 52), (135, 52)], fill=WOOD)
    d.line([(56, 63), (135, 63)], fill=WOOD_DK)
    for x in range(62, 134, 9):
        d.rectangle([x, 56, x + 1, 59], fill=LACQUER_LO)          # nail heads
    # ---- the storey over the gateway: white plaster, a row of windows, the castle's tiles
    white_wall(d, 6, 29, 185, 57)
    d.rectangle([56, 50, 135, 57], fill=WOOD_LO); d.line([(56, 50), (135, 50)], fill=WOOD)
    lattice_windows(d, spread(12, 180, 9, 8), 36, 45, 8)
    castle_roof(d, roof_rows(8, 28, (18, 173), (1, 190)))
    d.line([(18, 8), (173, 8)], fill=ROOF_LO)
    eave(d, 1, 190, 29)
    ridge(d, 16, 175, 3)
    outline(im)
    return im


def bridge():
    im, d = canvas(2, 4)                 # 64 x 128, walked north-south
    d.rectangle([5, 2, 58, 125], fill=PLANK)
    for i, y in enumerate(range(2, 126, 5)):                      # the planks
        d.line([(5, y), (58, y)], fill=WOOD_LO)
        d.line([(5, y + 1), (58, y + 1)], fill=PLANK_HI if i % 3 == 0 else PLANK)
        d.point((12 + (i * 19) % 40, y + 3), fill=WOOD_LO)
    for x0 in (2, 56):                                            # the rails, a capped post every cell
        d.rectangle([x0, 1, x0 + 5, 126], fill=WOOD_LO)
        d.line([(x0, 1), (x0, 126)], fill=WOOD); d.line([(x0 + 5, 1), (x0 + 5, 126)], fill=WOOD_DK)
        for y in range(4, 126, 30):
            d.rectangle([x0 - 1, y, x0 + 6, y + 6], fill=BRONZE)
            d.line([(x0 - 1, y), (x0 + 6, y)], fill=BRONZE_HI)
            d.rectangle([x0 + 1, y + 2, x0 + 4, y + 4], fill=GOLD)
            d.point((x0 + 2, y + 2), fill=GOLD_HI)
    outline(im)
    return im


def kokoen_gate():
    im, d = canvas(4, 3)                 # 128 x 96; the gateway is columns 1-2 (x 32-95)
    # wing walls joining the earthen wall either side (sendai-earthen-wall's own courses)
    for x0, x1 in ((0, 27), (100, 127)):
        coping(d, x0, x1, 44)
        plaster(d, x0, x1, 58, 87)
        footing(d, x0, x1, 88, 95)
    # the posts, pale cypress, on stone feet; the lintel and a tie beam under it
    for x0 in (26, 94):
        d.rectangle([x0, 34, x0 + 7, 95], fill=WOOD)
        d.line([(x0, 34), (x0, 95)], fill=PLANK_HI); d.line([(x0 + 7, 34), (x0 + 7, 95)], fill=WOOD_LO)
        d.rectangle([x0 - 1, 90, x0 + 8, 95], fill=STONE_LO); d.line([(x0 - 1, 90), (x0 + 8, 90)], fill=STONE)
    d.rectangle([22, 34, 105, 41], fill=WOOD); d.line([(22, 34), (105, 34)], fill=PLANK_HI)
    d.line([(22, 41), (105, 41)], fill=WOOD_LO)
    d.rectangle([34, 46, 93, 48], fill=WOOD_LO)
    for x in range(40, 92, 8):                                    # the slats between the beams
        d.line([(x, 42), (x, 45)], fill=WOOD_LO)
    # the garden's name on a board over the way in
    d.rectangle([52, 36, 75, 49], fill=BOARD_LO)
    d.rectangle([53, 37, 74, 48], fill=BOARD)
    for x in (57, 63, 69):
        d.rectangle([x, 40, x + 2, 45], fill=GOLD); d.point((x + 1, 42), fill=BOARD)
    # the roof: the castle's tiles, a low gable with wide eaves
    castle_roof(d, roof_rows(12, 31, (18, 109), (3, 124)))
    d.line([(18, 12), (109, 12)], fill=ROOF_LO)
    eave(d, 3, 124, 32, lift=3)
    d.rectangle([16, 7, 111, 11], fill=ROOF_LO); d.line([(16, 7), (111, 7)], fill=ROOF_HI)
    for x0 in (12, 110):
        d.rectangle([x0, 4, x0 + 5, 11], fill=ROOF); d.point((x0 + 1, 5), fill=ROOF_HI)
    outline(im)
    return im


def wall():
    im, d = canvas(1, 2)                 # 32 x 64: full bleed side to side, so a run has no seams
    # the coping
    d.rectangle([0, 1, 31, 3], fill=ROOF_LO); d.line([(0, 1), (31, 1)], fill=ROOF_HI)
    castle_roof(d, [(y, -2, 33) for y in range(4, 13)])
    d.rectangle([0, 13, 31, 14], fill=ROOF_LO)
    for x in range(1, 32, 4):
        d.point((x, 14), fill=ROOF_HI)                            # the round tile ends
    d.line([(0, 15), (31, 15)], fill=ROOF_DK)
    # the plaster, in the coping's shadow at the top
    d.rectangle([0, 16, 31, 52], fill=PLASTER)
    d.rectangle([0, 16, 31, 18], fill=PLASTER_LO)
    d.line([(0, 52), (31, 52)], fill=PLASTER_LO)
    # loopholes, Himeji's mixed shapes: an oblong for an arrow, a triangle for a gun
    d.rectangle([6, 27, 8, 37], fill=SLATE_LO); d.line([(5, 38), (9, 38)], fill=PLASTER_LO)
    d.polygon([(22, 29), (18, 36), (26, 36)], fill=SLATE_LO); d.line([(17, 37), (27, 37)], fill=PLASTER_LO)
    # the stone footing
    d.rectangle([0, 53, 31, 62], fill=STONE)
    d.line([(0, 53), (31, 53)], fill=WHITE); d.rectangle([0, 61, 31, 62], fill=STONE_LO)
    for x, y0, y1 in ((0, 54, 60), (11, 54, 57), (17, 58, 60), (24, 54, 60)):
        d.line([(x, y0), (x, y1)], fill=STONE_LO)
    d.line([(0, 57), (23, 57)], fill=STONE_LO)
    d.point((5, 55), fill=WHITE); d.point((28, 56), fill=WHITE); d.point((20, 59), fill=STONE_DK)
    outline(im)
    return im


def fingerpost():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([14, 8, 17, 60], fill=BOARD); d.line([(14, 8), (14, 60)], fill=WOOD)
    d.line([(17, 8), (17, 60)], fill=BOARD_LO)
    d.rectangle([13, 5, 18, 8], fill=WOOD_LO); d.line([(13, 5), (18, 5)], fill=WOOD)       # the cap
    d.rectangle([11, 58, 20, 62], fill=STONE_LO); d.line([(11, 58), (20, 58)], fill=STONE)
    # the arm west, and under it the arm east: boards cut to a point
    for y, tip, x0, x1 in ((12, 2, 6, 22), (26, 29, 9, 25)):
        d.polygon([(x0, y), (x1, y), (x1, y + 9), (x0, y + 9)] if tip > x1 else
                  [(x0, y), (x1, y), (x1, y + 9), (x0, y + 9)], fill=WOOD)
        side = x0 if tip < x0 else x1
        d.polygon([(side, y), (tip, y + 4), (tip, y + 5), (side, y + 9)], fill=WOOD)
        d.line([(min(x0, tip + 2), y), (max(x1, tip - 2), y)], fill=PLANK_HI)
        d.line([(min(x0, tip + 2), y + 9), (max(x1, tip - 2), y + 9)], fill=WOOD_LO)
        for x in range(x0 + 2, x1 - 1, 3):                        # the place's name, painted on
            d.line([(x, y + 3), (x, y + 6)], fill=CREAM)
        d.point(((x0 + x1) // 2, y + 1), fill=WOOD_DK)            # its nail
    outline(im)
    return im


SPRITES = {      # key: (builder, scale, tileNames label)
    'himeji-keep_0_0': (keep, 2, 'himeji-keep'),
    'himeji-turret_0_0': (turret, 2, 'himeji-turret'),
    'himeji-gate_0_0': (gate, 2, 'himeji-gate'),
    'himeji-bridge_0_0': (bridge, 2, 'himeji-bridge'),
    'himeji-kokoen-gate_0_0': (kokoen_gate, 2, 'himeji-kokoen-gate'),
    'himeji-wall_0_0': (wall, 2, 'himeji-wall'),
    'kansai-fingerpost_0_0': (fingerpost, 2, 'kansai-fingerpost'),
}

# Flat decks you walk ON: Non-Collidables with a depth nudge that puts them over
# the Water layer and under everyone standing on them (the asahikawa-bridge
# recipe, see generate_hokkaido.FLAT).
FLAT = {'himeji-bridge_0_0': -200}
# Worth looking up at (config game.lookUp.sprites: family -> 0 for a one-sprite landmark)
LOOK_UP = {'himeji-keep': 0}


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
        sheet = Image.new('RGBA', (sum(i.width + 16 for i in ims) + 16, max(i.height for i in ims) + 32),
                          rgb('83af6f'))
        x = 16
        for im in ims:
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
