#!/usr/bin/env python3
"""generate_kansai_art.py — draw the Kansai sprites (issues #255, #267): Himeji,
Okayama, and the fingerposts where the districts meet.

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
Okayama
  okayama-keep_0_0         8x7   the "crow castle": black weatherboards under a
                                 band of white plaster at each storey, darker
                                 tiles, gold shachi on the ridge, a low stone
                                 base. Broader and lower than Himeji's, and
                                 exactly its footprint
  okayama-bridge_0_0       2x4   the Tsukimi bridge: a grey steel footbridge
                                 walked north-south (flat, as himeji-bridge)
  okayama-bank-rock_0_0    2x2   a heap of the pond rim's white stones, centred
                                 where its four cells meet (flat): the rim has
                                 no inner-corner piece, and this covers the
                                 notch at each corner of Korakuen's island
  okayama-crane_0_0        1x2   a red-crowned crane
  okayama-momotaro_0_0     2x3   the bronze Momotaro on a stone plinth, the
                                 pheasant on his hand, the dog and the monkey
                                 at his feet
  okayama-bizen-stall_0_0  3x3   an open stall of Bizen ware: an awning, a
                                 counter, rows of brown unglazed pots
Kansai
  kansai-fingerpost_0_0    1x2   a wooden fingerpost, one arm west, one east
  okayama-fingerpost_0_0   1x2   the same post, where Himeji and Okayama meet
                                 (its own key: a bump's line goes by the key)

Deterministic and idempotent: rewrites the PNGs in assets/sprites/, registers
them in config.json spriteMetadata + tileNames, and asks the camera to look up
at the two keeps (game.lookUp.sprites). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py and the generators:
    python3 tools/generate_kansai_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from generate_hokkaido import (CLEAR, rgb, canvas, outline, INK, CREAM, CREAM_LO, WHITE, SNOW_LO, WOOD, WOOD_LO,
                               WOOD_DK, STONE, STONE_LO, STONE_DK, GOLD)
from generate_sendai_art import (roof_rows, coping, plaster, footing, LACQUER_LO, GOLD_HI, GOLD_LO,
                                 SLATE_LO)
from generate_hokuriku_art import (masonry, PLASTER, PLASTER_LO, BOARD, BOARD_LO, SOOT, SOOT_HI, SOOT_LO,
                                   INDIGO, INDIGO_HI)

# Himeji's roofs: grey tiles with every joint sealed in white plaster, which is
# why the whole castle reads white
ROOF, ROOF_HI, ROOF_LO, ROOF_DK = rgb('8794a6'), rgb('d5dce4'), rgb('66748a'), rgb('4a566c')
TILES = (ROOF, ROOF_HI, ROOF_LO, ROOF_DK)
# Okayama's: plain grey tiles, darker, over black boards - the "crow castle"
KAWARA = (rgb('5f6b80'), rgb('8d99ab'), rgb('465166'), rgb('2f384a'))
WHITE_FACE = (PLASTER, PLASTER_LO, SLATE_LO, PLASTER)             # a gable's face, its shade, its window, the bar
CROW_FACE = (SOOT, SOOT_LO, PLASTER, SOOT_LO)
PLANK, PLANK_HI = rgb('a97c62'), rgb('d8ae94')
BRONZE, BRONZE_HI = rgb('6f7f6a'), rgb('a3b596')
STEEL, STEEL_HI, STEEL_LO, STEEL_DK = rgb('9aa6b4'), rgb('cfd8e0'), rgb('6f7b8c'), rgb('4b566a')
STATUE, STATUE_HI, STATUE_LO = rgb('4f6359'), rgb('7d9584'), rgb('2f3d3a')     # weathered bronze (Sendai's Masamune)
BIZEN, BIZEN_HI, BIZEN_LO, BIZEN_DK = rgb('99593f'), rgb('c28563'), rgb('6e3d30'), rgb('44302c')
PEBBLE = (rgb('ffffff'), rgb('e3e3e3'), rgb('bdbdbd'), rgb('919191'), rgb('737373'), rgb('585575'))   # the pond rim's stones
CROWN = rgb('d8442f')


def castle_roof(d, rows, tiles=TILES):
    """A fall of castle tiles over (y, x0, x1) scanlines: ribs down the slope
    (Himeji's are white plaster), a darker line under each course, lit on the
    left and shaded on the right. `tiles` is (tile, light, shade, dark)."""
    ROOF, ROOF_HI, ROOF_LO, _ = tiles
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=ROOF_LO if y % 5 == 4 else ROOF_HI if x % 4 == 0 else ROOF)
        d.point((x0, y), fill=ROOF_HI); d.point((x0 + 1, y), fill=ROOF_HI)
        d.point((x1, y), fill=ROOF_LO); d.point((x1 - 1, y), fill=ROOF_LO)


def eave(d, x0, x1, y, lift=4, tiles=TILES):
    """The eave under a roof, two pixels deep from y: the round tile ends, and
    the corners turned up."""
    ROOF, ROOF_HI, ROOF_LO, ROOF_DK = tiles
    d.rectangle([x0, y, x1, y + 1], fill=ROOF_LO)
    for x in range(x0 + 2, x1, 4):
        d.point((x, y + 1), fill=ROOF_HI)
    d.line([(x0, y + 2), (x1, y + 2)], fill=ROOF_DK)
    if lift:
        for sx, x in ((1, x0), (-1, x1)):
            d.polygon([(x, y + 1), (x + sx * (lift + 3), y + 1), (x, y - lift)], fill=ROOF)
            d.line([(x, y - lift), (x, y + 1)], fill=ROOF_HI if sx > 0 else ROOF_LO)


def ridge(d, x0, x1, y, tiles=TILES, fish=None):
    """A ridge five pixels deep from y, a shachi (the roof's fish) on each end:
    tile, or `fish` (the fish's colour, its light, its shade)."""
    ROOF, ROOF_HI, ROOF_LO, ROOF_DK = tiles
    body, lit, dark = fish or (ROOF, ROOF_HI, ROOF_DK)
    d.rectangle([x0, y, x1, y + 4], fill=ROOF_LO); d.line([(x0, y), (x1, y)], fill=ROOF_HI)
    for x in range(x0 + 3, x1, 5):
        d.point((x, y + 2), fill=ROOF_HI)
    for sx, x in ((1, x0), (-1, x1)):
        d.polygon([(x - sx * 2, y + 4), (x + sx * 4, y + 4), (x + sx * 4, y - 1), (x + sx, y - 5), (x - sx * 2, y - 1)],
                  fill=body)
        d.point((x, y - 2), fill=lit); d.point((x + sx * 2, y), fill=dark)


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


def chidori(d, cx, apex, base, half, tiles=TILES, face=WHITE_FACE):
    """A triangular dormer gable (chidori-hafu): tiled slopes round a face
    (white at Himeji, black boards at Okayama)."""
    ROOF, ROOF_HI, ROOF_LO, ROOF_DK = tiles
    PLASTER, PLASTER_LO, SLATE_LO, bar = face
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
        d.line([(cx, base - 7), (cx, base - 3)], fill=bar)
    d.point((cx, apex), fill=ROOF_HI); d.point((cx, apex + 1), fill=GOLD)


def karahafu(d, cx, y, half, depth, tiles=TILES, face=WHITE_FACE):
    """A cusped gable (kara-hafu): the eave swells up over a panel."""
    ROOF, ROOF_HI, ROOF_LO, ROOF_DK = tiles
    PLASTER = face[0]
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


def white_storey(d, x0, y0, x1, y1, n):
    """A storey of Himeji's: white plaster and `n` lattice windows."""
    white_wall(d, x0, y0, x1, y1)
    if n:
        lattice_windows(d, spread(x0 + 3, x1 - 4, n), y0 + 5, min(y1 - 3, y0 + 13))


def crow_storey(d, x0, y0, x1, y1, n):
    """A storey of Okayama's: black weatherboards, lapped, under a band of white
    plaster that holds the `n` windows."""
    band = y0 + 10                                                # the eave above hides its first three rows
    d.rectangle([x0, y0, x1, band], fill=PLASTER)
    d.rectangle([x0, y0, x1, y0 + 4], fill=PLASTER_LO)
    d.rectangle([x1 - 3, y0, x1, band], fill=PLASTER_LO)
    for x in (spread(x0 + 3, x1 - 4, n) if n else ()):
        d.rectangle([x, y0 + 6, x + 5, band], fill=SOOT_LO)
        d.line([(x + 2, y0 + 6), (x + 2, band)], fill=SOOT_HI); d.line([(x + 4, y0 + 6), (x + 4, band)], fill=SOOT_HI)
    d.rectangle([x0, band + 1, x1, y1], fill=SOOT)
    for i, y in enumerate(range(band + 1, y1 + 1, 4)):            # each board laps the one under it
        d.line([(x0, y), (x1, y)], fill=SOOT_LO)
        if y + 1 <= y1:
            for x in range(x0 + 2 + (i * 5) % 9, x1 - 3, 9):
                d.line([(x, y + 1), (x + 3, y + 1)], fill=SOOT_HI)
    d.line([(x0, band + 1), (x0, y1)], fill=SOOT_HI)
    d.rectangle([x1 - 3, band + 1, x1, y1], fill=SOOT_LO)


def storeys(im, d, cx, tiers, base, wall=white_storey, tiles=TILES):
    """A keep or a turret: `tiers` from the top, each (roof y0, roof y1, the
    roof's top half-width, its eave half-width, the wall's bottom y, the wall's
    half-width, windows), on a stone `base` (y0, y1, half-width at the foot, lean, seed).
    `wall` draws one storey (white_storey, crow_storey) and `tiles` roofs it."""
    for y0, y1, top, out, wy, half, n in tiers:
        wall(d, cx - half, y1 + 1, cx + half - 1, wy, n)
    by0, by1, foot, lean, seed = base
    stone_base(im, cx - foot, by0, cx + foot - 1, by1, lean, seed)
    d = ImageDraw.Draw(im)
    for y0, y1, top, out, wy, half, n in tiers:
        castle_roof(d, roof_rows(y0, y1, (cx - top, cx + top - 1), (cx - out, cx + out - 1)), tiles)
        d.line([(cx - top, y0), (cx + top - 1, y0)], fill=tiles[2])
        eave(d, cx - out, cx + out - 1, y1 + 1, tiles=tiles)
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


# ---------------------------------------------------------------- Okayama
GOLD_FISH = (GOLD, GOLD_HI, GOLD_LO)


def crow_keep():
    im, d = canvas(8, 7)                 # 256 x 224: the art fills its footprint, nothing above it
    cx = 128
    d = storeys(im, d, cx, [(13, 30, 22, 46, 54, 34, 3),
                            (55, 74, 38, 68, 100, 56, 5),
                            (101, 122, 60, 92, 150, 80, 7),
                            (151, 172, 84, 118, 196, 104, 9)],
                (197, 222, 114, 5, 3), wall=crow_storey, tiles=KAWARA)
    ridge(d, cx - 22, cx + 21, 8, KAWARA, GOLD_FISH)
    chidori(d, cx, 48, 75, 28, KAWARA, CROW_FACE)                 # the great gable over the second roof
    for sx in (-1, 1):                                            # a dormer either side on the third
        chidori(d, cx + sx * 44, 104, 123, 16, KAWARA, CROW_FACE)
    karahafu(d, cx, 173, 18, 10, KAWARA, CROW_FACE)               # and the cusped one over the way in
    d.rectangle([cx - 6, 180, cx + 5, 196], fill=SOOT_LO)         # the door under it: iron-bound, shut
    d.line([(cx - 1, 180), (cx - 1, 196)], fill=SOOT_HI)
    for y in (184, 190):
        d.line([(cx - 6, y), (cx + 5, y)], fill=GOLD_LO)
    # gold on every gable's point and on the tile ends of the corners: the castle was "the golden crow"
    for x, y in ((cx, 49), (cx - 44, 105), (cx + 44, 105), (cx, 164)):
        d.rectangle([x - 1, y, x, y + 1], fill=GOLD); d.point((x - 1, y), fill=GOLD_HI)
    for y1, out in ((30, 46), (74, 68), (122, 92), (172, 118)):
        for sx, x in ((1, cx - out), (-1, cx + out - 1)):
            d.rectangle([min(x, x + sx), y1 - 3, max(x, x + sx), y1 - 2], fill=GOLD)
            d.point((x, y1 - 3), fill=GOLD_HI)
    outline(im)
    return im


def tsukimi_bridge():
    im, d = canvas(2, 4)                 # 64 x 128, walked north-south: a steel footbridge
    d.rectangle([5, 2, 58, 125], fill=STEEL)
    for i, y in enumerate(range(2, 126, 16)):                     # the deck's plates, a joint between each
        d.line([(5, y), (58, y)], fill=STEEL_LO)
        d.line([(5, y + 1), (58, y + 1)], fill=STEEL_HI)
        for x in range(12, 54, 6):                                # the tread: rows of raised studs
            for dy in (5, 9, 13):
                if y + dy < 125:
                    d.point((x + (dy // 4) % 2 * 3, y + dy), fill=STEEL_LO)
    d.line([(31, 3), (31, 124)], fill=STEEL_LO); d.line([(32, 3), (32, 124)], fill=STEEL_HI)   # the deck's spine
    for x0 in (2, 56):                                            # the rails: a girder, riveted, a post every cell
        d.rectangle([x0, 1, x0 + 5, 126], fill=STEEL_DK)
        d.line([(x0, 1), (x0, 126)], fill=STEEL_LO); d.line([(x0 + 1, 1), (x0 + 1, 126)], fill=STEEL_HI)
        for y in range(6, 126, 8):
            d.point((x0 + 3, y), fill=STEEL_HI)
        for y in range(4, 126, 30):
            d.rectangle([x0 - 1, y, x0 + 6, y + 5], fill=STEEL_LO)
            d.line([(x0 - 1, y), (x0 + 6, y)], fill=STEEL_HI)
            d.rectangle([x0 + 1, y + 2, x0 + 4, y + 3], fill=STEEL_DK)
    outline(im)
    return im


def pebble(im, pts, tone=0):
    """One of the pond rim's stones, a polygon: white on top, grey down its near
    side and to the east, inked all round."""
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    less = lambda dx, dy: ImageChops.subtract(mask, ImageChops.offset(mask, dx, dy))    # the band `mask` has on that side
    im.paste(PEBBLE[1 + tone], (0, 0), mask)
    im.paste(PEBBLE[0], (0, 0), less(0, 2 - tone))
    im.paste(PEBBLE[2 + tone], (0, 0), less(-2, 0))
    im.paste(PEBBLE[3 + tone], (0, 0), less(0, -3))
    im.paste(PEBBLE[5], (0, 0), less(0, -1))
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3)))
    im.paste(INK, (0, 0), edge)


def bank_rock():
    im, d = canvas(2, 2)                 # 64 x 64; the heap is centred on (32, 32), where the four cells meet
    for pts, tone in (([(19, 22), (25, 18), (31, 20), (32, 27), (25, 30), (19, 28)], 1),
                      ([(31, 19), (39, 17), (45, 21), (45, 28), (37, 30), (32, 27)], 0),
                      ([(17, 29), (23, 28), (27, 34), (25, 41), (18, 39)], 0),
                      ([(38, 29), (45, 28), (48, 34), (45, 41), (39, 39)], 1),
                      ([(20, 41), (26, 37), (32, 40), (32, 46), (24, 47)], 1),
                      ([(32, 40), (39, 38), (45, 41), (43, 47), (34, 47)], 0),
                      ([(25, 27), (33, 23), (40, 27), (41, 35), (34, 41), (27, 39), (23, 33)], 0)):
        pebble(im, pts, tone)
    return im


def crane():
    im, d = canvas(1, 2)                 # 32 x 64: a red-crowned crane, facing east
    d.ellipse([7, 58, 25, 62], fill=rgb('3a5f66', 150))           # ground shadow
    for x, bend in ((13, 1), (17, -1)):                           # the legs: long, grey, a knee each
        d.line([(x, 40), (x + bend, 50), (x, 60)], fill=STONE_DK)
        d.line([(x, 60), (x + 3, 60)], fill=STONE_DK)
    d.ellipse([5, 28, 23, 41], fill=WHITE)                        # the body
    d.chord([5, 28, 23, 41], 20, 160, fill=SNOW_LO)
    d.polygon([(3, 33), (10, 30), (12, 40), (6, 45), (2, 43)], fill=SOOT)        # the black bustle of the wings
    d.line([(4, 35), (9, 32)], fill=SOOT_HI); d.line([(3, 43), (6, 44)], fill=SOOT_LO)
    d.line([(20, 31), (22, 22), (20, 14)], fill=SOOT, width=3)    # the neck: black, white behind
    d.line([(19, 31), (21, 22), (19, 15)], fill=WHITE)
    d.ellipse([17, 8, 24, 15], fill=WHITE)                        # the head
    d.rectangle([19, 7, 22, 9], fill=CROWN)                       # the red crown
    d.rectangle([20, 13, 23, 15], fill=SOOT)                      # the black throat
    d.polygon([(24, 10), (30, 12), (24, 13)], fill=GOLD_LO)       # the bill
    d.point((22, 11), fill=INK)                                   # the eye
    outline(im)
    return im


def momotaro():
    im, d = canvas(2, 3)                 # 64 x 96
    # ---- the plinth: dressed stone with a cap, a bronze plate
    for y in range(62, 94):
        w = 20 + (y - 62) * 3 // 32
        d.line([(32 - w, y), (31 + w, y)], fill=STONE)
        d.point((32 - w, y), fill=WHITE); d.point((33 - w, y), fill=WHITE)
        d.line([(31 + w - 4, y), (31 + w, y)], fill=STONE_LO)
    for y in (72, 83):
        d.line([(12, y), (51, y)], fill=STONE_LO)
    for x, y0 in ((22, 62), (42, 62), (16, 73), (32, 73), (47, 73), (24, 84), (40, 84)):
        d.line([(x, y0 + 1), (x, y0 + 9)], fill=STONE_LO)
    d.rectangle([9, 57, 54, 62], fill=STONE); d.line([(9, 57), (54, 57)], fill=WHITE)
    d.line([(9, 62), (54, 62)], fill=STONE_DK)
    d.rectangle([7, 92, 56, 95], fill=STONE_LO); d.line([(7, 92), (56, 92)], fill=STONE)
    d.rectangle([22, 75, 41, 82], fill=STATUE_LO); d.rectangle([23, 76, 40, 81], fill=STATUE)
    for y in (77, 79):
        d.line([(25, y), (38, y)], fill=STATUE_HI)
    d.rectangle([12, 54, 51, 57], fill=STATUE_LO); d.line([(12, 54), (51, 54)], fill=STATUE)     # the bronze base
    # ---- Momotaro: legs apart, a sword at his hip, a hand to his brow, looking out for the ogres' island
    for x0, x1 in ((28, 25), (35, 38)):                           # the legs, in leggings
        d.line([(x0, 38), (x1, 53)], fill=STATUE, width=4)
        d.line([(x0 + 2, 39), (x1 + 2, 53)], fill=STATUE_LO)
        d.rectangle([x1 - 2, 52, x1 + 3, 54], fill=STATUE_LO)
    d.polygon([(25, 22), (38, 22), (42, 41), (21, 41)], fill=STATUE)              # the jinbaori, flared
    d.line([(25, 22), (21, 41)], fill=STATUE_HI); d.line([(38, 23), (42, 41)], fill=STATUE_LO)
    d.line([(31, 23), (31, 40)], fill=STATUE_LO)
    d.rectangle([24, 32, 39, 34], fill=STATUE_LO)                 # his sash
    d.ellipse([33, 25, 37, 29], fill=STATUE_HI); d.point((35, 24), fill=STATUE_HI)                 # the peach crest
    d.line([(22, 35), (13, 31)], fill=STATUE_LO, width=2)         # the sword at his hip
    d.line([(38, 24), (45, 19), (38, 14)], fill=STATUE, width=3)  # an arm up, the hand at his brow
    d.line([(44, 20), (39, 16)], fill=STATUE_HI)
    d.line([(25, 24), (19, 30), (24, 34)], fill=STATUE, width=3)  # the other on his hip
    d.ellipse([26, 10, 37, 21], fill=STATUE)                      # the head
    d.rectangle([29, 15, 35, 19], fill=STATUE_HI)                 # his face in the light
    d.point((30, 16), fill=STATUE_LO); d.point((34, 16), fill=STATUE_LO)
    d.rectangle([26, 12, 37, 13], fill=STATUE_LO)                 # the headband, its knot behind
    d.line([(25, 13), (23, 16)], fill=STATUE_LO)
    d.rectangle([31, 6, 32, 10], fill=STATUE_LO); d.rectangle([30, 4, 33, 6], fill=STATUE)         # the topknot
    # ---- the pheasant on his shoulder: a long tail down behind
    d.ellipse([16, 16, 23, 21], fill=STATUE); d.line([(18, 17), (21, 17)], fill=STATUE_HI)
    d.rectangle([21, 12, 24, 16], fill=STATUE); d.point((25, 14), fill=STATUE_HI); d.point((23, 13), fill=STATUE_LO)
    d.line([(17, 20), (11, 25), (8, 31)], fill=STATUE_HI)
    # ---- the dog, sitting at his right foot, and the monkey, crouched at his left
    d.polygon([(12, 53), (12, 45), (15, 42), (19, 45), (21, 53)], fill=STATUE)    # the dog's back and haunch
    d.line([(12, 46), (12, 53)], fill=STATUE_HI); d.line([(20, 50), (23, 46)], fill=STATUE_LO)   # ...and tail
    d.rectangle([11, 37, 18, 43], fill=STATUE); d.rectangle([8, 40, 11, 43], fill=STATUE)        # head, muzzle
    d.polygon([(11, 37), (12, 34), (14, 37)], fill=STATUE); d.polygon([(15, 37), (17, 34), (18, 37)], fill=STATUE)
    d.point((8, 40), fill=STATUE_LO); d.point((12, 39), fill=STATUE_LO); d.line([(11, 37), (13, 37)], fill=STATUE_HI)
    d.ellipse([42, 44, 52, 53], fill=STATUE); d.chord([42, 44, 52, 53], 20, 160, fill=STATUE_LO)   # the monkey
    d.ellipse([43, 37, 51, 45], fill=STATUE); d.ellipse([45, 39, 50, 44], fill=STATUE_HI)
    d.point((46, 41), fill=STATUE_LO); d.point((49, 41), fill=STATUE_LO)
    d.point((42, 40), fill=STATUE); d.point((52, 40), fill=STATUE)                # its ears
    d.line([(52, 51), (55, 47), (54, 43)], fill=STATUE_LO)                        # its tail
    outline(im)
    return im


def pot(d, x, y, kind, seed=0):
    """A piece of Bizen ware standing on (x, y), its foot's left end: unglazed
    brown, a scorch down one side, pale ash on the shoulder. kind: a jar, a
    flask (tokkuri), a bowl, a cup."""
    if kind == 'jar':
        d.ellipse([x, y - 11, x + 9, y], fill=BIZEN); d.rectangle([x + 3, y - 13, x + 6, y - 10], fill=BIZEN_LO)
        d.chord([x, y - 11, x + 9, y], -60, 80, fill=BIZEN_LO); d.line([(x + 2, y - 8), (x + 3, y - 9)], fill=BIZEN_HI)
        d.point((x + 5 + seed % 2, y - 5), fill=BIZEN_DK)
    elif kind == 'flask':
        d.ellipse([x, y - 8, x + 6, y], fill=BIZEN); d.rectangle([x + 2, y - 12, x + 4, y - 7], fill=BIZEN)
        d.line([(x + 1, y - 12), (x + 5, y - 12)], fill=BIZEN_LO); d.line([(x + 5, y - 6), (x + 5, y - 1)], fill=BIZEN_LO)
        d.point((x + 2, y - 5), fill=BIZEN_HI)
    elif kind == 'bowl':
        d.chord([x, y - 9, x + 9, y], 0, 180, fill=BIZEN); d.line([(x, y - 5), (x + 9, y - 5)], fill=BIZEN_HI)
        d.line([(x + 6, y - 3), (x + 8, y - 4)], fill=BIZEN_LO); d.line([(x + 3, y), (x + 6, y)], fill=BIZEN_LO)
    else:
        d.rectangle([x, y - 5, x + 4, y], fill=BIZEN); d.line([(x, y - 5), (x + 4, y - 5)], fill=BIZEN_HI)
        d.line([(x + 4, y - 4), (x + 4, y)], fill=BIZEN_LO)


def bizen_stall():
    im, d = canvas(3, 3)                 # 96 x 96: open to the south, the potter's wares on two shelves and the counter
    d.ellipse([4, 88, 91, 95], fill=rgb('3a5f66', 150))           # ground shadow
    for x0 in (5, 86):                                            # the posts
        d.rectangle([x0, 30, x0 + 4, 93], fill=WOOD); d.line([(x0, 30), (x0, 93)], fill=PLANK_HI)
        d.line([(x0 + 4, 30), (x0 + 4, 93)], fill=WOOD_LO)
    d.rectangle([10, 34, 85, 62], fill=BOARD_LO)                  # the back of the stall, in shade
    for x in range(16, 85, 9):
        d.line([(x, 34), (x, 62)], fill=WOOD_DK)
    for y in (46, 60):                                            # two shelves
        d.rectangle([10, y, 85, y + 2], fill=WOOD); d.line([(10, y + 2), (85, y + 2)], fill=WOOD_LO)
    for i, (x, kind) in enumerate(((13, 'jar'), (25, 'flask'), (33, 'flask'), (42, 'jar'), (54, 'cup'), (61, 'cup'),
                                   (68, 'jar'), (79, 'flask'))):
        pot(d, x, 45, kind, i)
    for i, (x, kind) in enumerate(((12, 'bowl'), (24, 'cup'), (31, 'jar'), (43, 'bowl'), (55, 'flask'), (63, 'jar'),
                                   (75, 'bowl'))):
        pot(d, x, 59, kind, i + 1)
    d.rectangle([3, 63, 92, 68], fill=WOOD); d.line([(3, 63), (92, 63)], fill=PLANK_HI)          # the counter
    d.line([(3, 68), (92, 68)], fill=WOOD_LO)
    d.rectangle([5, 69, 90, 93], fill=BOARD); d.rectangle([5, 69, 90, 71], fill=BOARD_LO)
    for x in range(14, 90, 10):
        d.line([(x, 72), (x, 93)], fill=BOARD_LO)
    d.rectangle([5, 91, 90, 93], fill=BOARD_LO)
    for i, (x, kind) in enumerate(((8, 'flask'), (17, 'bowl'), (30, 'jar'), (42, 'cup'), (49, 'cup'), (57, 'bowl'),
                                   (70, 'jar'), (82, 'flask'))):
        pot(d, x, 64, kind, i + 2)
    d.rectangle([34, 75, 61, 87], fill=CREAM); d.rectangle([34, 75, 61, 87], outline=WOOD_LO)    # the price board
    for y in (78, 81, 84):
        d.line([(37, y), (58 - (y % 2) * 6, y)], fill=WOOD_DK)
    # the awning: indigo cloth, a pale stripe, sagging between the posts
    for y in range(6, 31):
        w = 40 + (y - 6) * 7 // 24
        for x in range(48 - w, 48 + w):
            stripe = (x - 48) % 16 in (0, 1, 2, 3)
            d.point((x, y), fill=(CREAM if y < 26 else CREAM_LO) if stripe else (INDIGO_HI if y < 26 else INDIGO))
        d.point((48 - w, y), fill=INDIGO_HI); d.point((47 + w, y), fill=INDIGO)
    d.line([(8, 6), (87, 6)], fill=WOOD); d.line([(8, 7), (87, 7)], fill=WOOD_LO)                # its pole
    for x in range(1, 95, 8):                                     # the scalloped hem
        d.polygon([(x, 31), (x + 7, 31), (x + 3, 35)], fill=INDIGO)
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
    'okayama-keep_0_0': (crow_keep, 2, 'okayama-keep'),
    'okayama-bridge_0_0': (tsukimi_bridge, 2, 'okayama-bridge'),
    'okayama-bank-rock_0_0': (bank_rock, 2, 'okayama-bank-rock'),
    'okayama-crane_0_0': (crane, 2, 'okayama-crane'),
    'okayama-momotaro_0_0': (momotaro, 2, 'okayama-momotaro'),
    'okayama-bizen-stall_0_0': (bizen_stall, 2, 'okayama-bizen-stall'),
    'okayama-fingerpost_0_0': (fingerpost, 2, 'okayama-fingerpost'),
}

# Flat decks you walk ON: Non-Collidables with a depth nudge that puts them over
# the Water layer and under everyone standing on them (the asahikawa-bridge
# recipe, see generate_hokkaido.FLAT).
FLAT = {'himeji-bridge_0_0': -200, 'okayama-bridge_0_0': -200, 'okayama-bank-rock_0_0': -200}
# Worth looking up at (config game.lookUp.sprites: family -> 0 for a one-sprite landmark)
LOOK_UP = {'himeji-keep': 0, 'okayama-keep': 0}


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
