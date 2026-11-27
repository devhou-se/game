#!/usr/bin/env python3
"""generate_sanfranbourne_art.py — draw the San Franbourne, airport and plane sprites (issue #218).

San Franbourne is the home city: Melbourne and San Francisco at once. No asset
pack has either, so everything is drawn here the way tools/generate_hokkaido.py
and tools/generate_fukuoka_art.py draw theirs: shaded pixel art in the
GuttyKreum palette, at half size (one drawn pixel = one pixel of a 32px tile)
and pixel-doubled, with a 1px ink outline. No brand marks.

The city (tools/generate_sanfranbourne.py places them):
  sfb-clocks-station_0_0   12x7  the yellow station with the copper dome and the
                                 row of clocks over its door ("under the clocks")
  sfb-bridge-tower_0_0     6x7   a tower of the red suspension bridge: you walk
                                 between its legs, under the portal beams
  sfb-bridge-cable-{w,e}   1x1   the deck's red rail and suspender cables
  sfb-river_{center,edge-n,edge-s}  the pond water recoloured brown (the river
                                 that flows upside down)
  sfb-rowers_0_0           4x1   a rowing four on the river
  sfb-lady-{a,b,c,d}_0_0   3x5   painted-lady terraces, each a step higher up
                                 the hill than the last
  sfb-mural-{a,b,c}_0_0    3x2   the laneway wall under them: street art
  sfb-coffee_0_0           3x2   ...and a hole-in-the-wall coffee window
  sfb-crates_0_0           1x1   milk-crate seats and a tiny table
  sfb-pyramid_0_0          4x12  the pointy pyramid tower
  sfb-spire_0_0            4x11  the arts-centre spire (see-through lattice)
  sfb-cable-car_0_0        3x2   a cable car
  sfb-tram_0_0             4x2   a green-and-yellow tram
  sfb-rail-h_0_0           1x1   the rails and cable slot they share (Over Floor)
  sfb-oval_0_0             12x7  the sports ground (flat: you walk on it)
  sfb-goalposts_0_0        2x3   four posts
  sfb-oval-lamp-post_0_0   1x5   a light tower (`lamp-post`: DayNight lights it)
  sfb-fog-{a,b}_0_0        5x2   the fog that rolls over the ground (Tops)
  sfb-terminal_0_0         9x5   the airport terminal and its control tower
  sfb-pier_0_0             4x9   the timber pier (flat: you walk on it)
  sfb-sea-lions_0_0        3x2   a raft of sea lions
  sfb-palm_0_0             3x4   a palm
  sfb-rock_0_0             5x3   the island in the bay, with its lighthouse
  sfb-lean-{a,b,c,d}_0_0   1x1   four people standing folded double at the waist
                                 (hoodie, beanie, backpack, cap and a cup)

The airports (tools/generate_airports.py, one template for both):
  airport-wall_0_0 1x2, airport-window_0_0 2x2, airport-gate_0_0 2x2 (the jet
  bridge door), airport-board_0_0 2x2 (the departures board), airport-seats_0_0
  3x1, airport-security_0_0 1x2 (the scanner arch you walk through),
  airport-xray_0_0 3x2, airport-checkin_0_0 3x2, airport-bar_0_0 5x3 (the pub:
  back shelf, counter with taps, stools), airport-trolley_0_0 1x1,
  airport-carpet_0_0 1x1 (floor)

The flight (src/AirTravel.js): plane-interior (the cabin, windows cut through)
and plane-sky (what slides past them: day, cloud, sea, sunset, dusk). Like the
train interiors they are whole pictures, not tiles: spriteMetadata only.

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and registers
them in config.json (spriteMetadata, tileNames, the two towers in
game.lookUp.sprites). Text is set in the game's own PressStart2P, so no system
font is needed. Needs Pillow.

Run from gamev2/ BEFORE generate_airports.py / generate_sanfranbourne.py:
    python3 tools/generate_sanfranbourne_art.py [--preview out.png]
"""
import json
import math
import sys
from PIL import Image, ImageDraw, ImageFont

from generate_hokkaido import (rgb, canvas, outline, window, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK, WHITE,
                               GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)

C = 32
ORANGE, ORANGE_HI, ORANGE_LO = rgb('c8452c'), rgb('e8674a'), rgb('8e2d20')      # the bridge
MUSTARD, MUSTARD_HI, MUSTARD_LO = rgb('e0b040'), rgb('f2d070'), rgb('b07c2c')   # the station
MAROON = rgb('8a3a34')
COPPER, COPPER_HI, COPPER_LO = rgb('5fa58a'), rgb('8fd0b0'), rgb('3c7462')
LEAF, LEAF_HI, LEAF_LO = rgb('678e57'), rgb('89af78'), rgb('395050')
TURF, TURF_HI = rgb('6f9a55'), rgb('82ad63')
TRAM, TRAM_LO = rgb('3f7a4c'), rgb('2a5637')
BLUESTONE, BLUESTONE_LO, BLUESTONE_HI = rgb('5c6272'), rgb('444959'), rgb('777e8e')
BROWN, BROWN_HI, BROWN_LO = rgb('8a6a48'), rgb('a88560'), rgb('64492f')
SEAL, SEAL_HI, SEAL_LO = rgb('7a5a44'), rgb('9c7a5c'), rgb('4e382c')
SKIN = rgb('e8b898')
PINK, MINT, SKYBLUE, LEMON = rgb('e8a0b0'), rgb('9cd0b4'), rgb('8cb8e0'), rgb('f0d888')
CARPET, CARPET_LO = rgb('46587e'), rgb('3c4c70')
LED = rgb('ffaa28')

_font = None


def font():
    global _font
    if _font is None:
        _font = ImageFont.truetype('fonts/PressStart2P-Regular.ttf', 8)
    return _font


def label(d, cx, y, s, fill):
    """Pixel text centred on cx with its top ink row at y."""
    d.fontmode = '1'
    l, t, r, _ = d.textbbox((0, 0), s, font=font())
    d.text((cx - (r - l) // 2 - l, y - t), s, font=font(), fill=fill)


def box(d, x0, y0, x1, y1, fill, hi=None, lo=None):
    """A filled block with a lit top/left edge and a shaded bottom/right one."""
    d.rectangle([x0, y0, x1, y1], fill=fill)
    if hi:
        d.line([(x0, y0), (x1, y0)], fill=hi); d.line([(x0, y0), (x0, y1)], fill=hi)
    if lo:
        d.line([(x0, y1), (x1, y1)], fill=lo); d.line([(x1, y0), (x1, y1)], fill=lo)


def clock(d, cx, cy, r, hands=(2, -3)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK)
    d.line([(cx, cy), (cx, cy - r + 2)], fill=INK)
    d.line([(cx, cy), (cx + hands[0], cy + hands[1])], fill=INK)


# ------------------------------------------------------------------------------ the city
def clocks_station():
    im, d = canvas(12, 7)                # 384 x 224
    # the wings: mustard walls banded in maroon, a row of arched windows, a slate roof
    box(d, 4, 104, 379, 221, MUSTARD, MUSTARD_HI, MUSTARD_LO)
    d.polygon([(4, 104), (14, 88), (369, 88), (379, 104)], fill=STONE_DK)
    for x in range(8, 376, 6):
        d.line([(x, 90), (x - 3, 103)], fill=STONE_LO)
    d.line([(14, 88), (369, 88)], fill=STONE)
    for y in (126, 168, 206):
        d.rectangle([5, y, 378, y + 3], fill=MAROON)
        d.line([(5, y), (378, y)], fill=RED_HI)
    for x in range(14, 372, 22):
        if 138 <= x <= 232:
            continue
        for y0 in (134, 176):
            d.rectangle([x, y0 + 5, x + 11, y0 + 26], fill=GLASS_DK)
            d.pieslice([x, y0, x + 11, y0 + 11], 180, 360, fill=GLASS_DK)
            d.rectangle([x + 1, y0 + 6, x + 10, y0 + 25], fill=GLASS)
            d.line([(x + 1, y0 + 6), (x + 10, y0 + 6)], fill=GLASS_HI)
            d.line([(x + 6, y0 + 2), (x + 6, y0 + 25)], fill=GLASS_DK)
            d.rectangle([x - 1, y0 + 27, x + 12, y0 + 28], fill=CREAM)
    d.rectangle([4, 214, 379, 221], fill=STONE_LO)
    # the corner pavilion: taller, the great arch, the clocks over the door
    box(d, 142, 62, 241, 221, MUSTARD, MUSTARD_HI, MUSTARD_LO)
    for y in (84, 126, 206):
        d.rectangle([143, y, 240, y + 3], fill=MAROON); d.line([(143, y), (240, y)], fill=RED_HI)
    for x in (146, 232):                 # corner piers
        box(d, x - 4, 62, x + 4, 221, MUSTARD_HI, WHITE, MUSTARD_LO)
    d.pieslice([158, 96, 225, 190], 180, 360, fill=MAROON)
    d.rectangle([158, 143, 225, 213], fill=MAROON)
    d.pieslice([163, 102, 220, 184], 180, 360, fill=rgb('3a2c34'))
    d.rectangle([163, 143, 220, 213], fill=rgb('3a2c34'))
    for i in range(7):                   # the fan of the arch window
        a = math.radians(180 + 15 + i * 25)
        d.line([(191, 143), (191 + int(27 * math.cos(a)), 143 + int(39 * math.sin(a)))], fill=MUSTARD_LO)
    d.rectangle([163, 143, 220, 146], fill=MUSTARD)
    # THE CLOCKS: a board of nine little dials above the doors
    box(d, 160, 148, 223, 166, rgb('2c3a30'), COPPER, INK)
    for i in range(9):
        clock(d, 165 + i * 6 + (i // 3), 157, 2, hands=((1, 0), (0, 1), (-1, 0))[i % 3])
    for i in range(9):
        d.point((165 + i * 6 + (i // 3), 163), fill=LED)
    # the doors and the steps
    for x in (166, 184, 202):
        d.rectangle([x, 172, x + 14, 213], fill=WOOD_DK)
        d.rectangle([x + 1, 173, x + 13, 190], fill=GLASS); d.line([(x + 1, 173), (x + 13, 173)], fill=GLASS_HI)
        d.line([(x + 7, 173), (x + 7, 213)], fill=INK)
    d.rectangle([154, 214, 229, 217], fill=STONE); d.rectangle([150, 218, 233, 221], fill=STONE_LO)
    # the copper dome on its drum
    box(d, 160, 50, 223, 62, CREAM, WHITE, CREAM_DK)
    for x in range(164, 222, 8):
        d.rectangle([x, 53, x + 3, 60], fill=GLASS_DK)
    d.pieslice([158, 12, 225, 90], 180, 360, fill=COPPER)
    for i in range(-3, 4):               # the ribs of the dome
        pts = [(191 + int(i * 11 * math.sin(math.acos(max(-1.0, min(1.0, (50 - y) / 38.0 - 0.0))))), y) for y in range(13, 50, 3)]
        d.line(pts, fill=COPPER_LO)
    d.pieslice([164, 16, 200, 70], 180, 270, fill=COPPER_HI)
    d.rectangle([158, 49, 225, 51], fill=COPPER_LO)
    box(d, 187, 4, 196, 13, COPPER, COPPER_HI, COPPER_LO)
    d.line([(191, 0), (191, 4)], fill=GOLD)
    # the clock tower at the east end
    box(d, 330, 40, 368, 221, MUSTARD, MUSTARD_HI, MUSTARD_LO)
    for y in (84, 126, 168, 206):
        d.rectangle([331, y, 367, y + 3], fill=MAROON)
    clock(d, 349, 62, 12, hands=(6, 3))
    for a in range(0, 360, 30):
        d.point((349 + int(10 * math.cos(math.radians(a))), 62 + int(10 * math.sin(math.radians(a)))), fill=INK)
    d.polygon([(326, 40), (349, 14), (372, 40)], fill=COPPER)
    d.polygon([(326, 40), (349, 14), (349, 40)], fill=COPPER_HI)
    d.line([(349, 6), (349, 14)], fill=GOLD)
    for y0 in (96, 138, 178):
        window(d, 342, y0, 356, y0 + 20, frame=MAROON)
    outline(im)
    return im


def bridge_tower():
    im, d = canvas(6, 7)                 # 192 x 224: legs in the outer cells, the deck between
    for x0 in (5, 167):
        # a leg, stepping in as it rises (art deco)
        for y0, inset in ((150, 0), (84, 2), (30, 4), (6, 6)):
            d.rectangle([x0 + inset, y0, x0 + 19 - inset, 221], fill=ORANGE)
            d.line([(x0 + inset, y0), (x0 + inset, 221)], fill=ORANGE_HI)
            d.line([(x0 + 19 - inset, y0), (x0 + 19 - inset, 221)], fill=ORANGE_LO)
            d.line([(x0 + inset, y0), (x0 + 19 - inset, y0)], fill=ORANGE_HI)
        for y in range(40, 216, 12):     # rivet courses
            d.line([(x0 + 7, y), (x0 + 12, y)], fill=ORANGE_LO)
        d.rectangle([x0 - 2, 214, x0 + 21, 221], fill=STONE_LO)
        d.line([(x0 - 2, 214), (x0 + 21, 214)], fill=STONE)
    # the portal beams: three, the lowest well clear of a walker's head
    for y0, h in ((14, 12), (56, 10), (98, 12)):
        d.rectangle([17, y0, 174, y0 + h], fill=ORANGE)
        d.line([(17, y0), (174, y0)], fill=ORANGE_HI)
        d.line([(17, y0 + h), (174, y0 + h)], fill=ORANGE_LO)
        for x in range(30, 170, 16):     # the chevrons pressed into each beam
            d.line([(x, y0 + h - 3), (x + 4, y0 + 3)], fill=ORANGE_LO)
            d.line([(x + 4, y0 + 3), (x + 8, y0 + h - 3)], fill=ORANGE_LO)
    # the main cables, sweeping down and away from the tower tops
    for x0, dx in ((8, -1), (183, 1)):
        for i in range(2):
            pts = [(x0 + dx * t, 8 + i * 3 + int((t / 8.0) ** 2 * 26)) for t in range(0, 9)]
            d.line(pts, fill=ORANGE_LO if i else ORANGE)
    outline(im)
    return im


def bridge_cable(side):
    """One cell of the deck's edge: a red rail on the outer side, with the
    suspender cables rising from it."""
    im, d = canvas(1, 1)
    x = 2 if side == 'w' else 27
    d.rectangle([x, 0, x + 2, 31], fill=ORANGE)
    d.line([(x, 0), (x, 31)], fill=ORANGE_HI)
    d.line([(x + 2, 0), (x + 2, 31)], fill=ORANGE_LO)
    for y in (4, 20):
        d.rectangle([x - 1, y, x + 3, y + 3], fill=ORANGE_LO)
        d.point((x + 1, y + 1), fill=ORANGE_HI)
    shade = (10, 22, 39, 70)
    for i in range(1, 6):                # the rail's shadow on the deck
        d.line([(x + (3 + i if side == 'w' else -i), 0), (x + (3 + i if side == 'w' else -i), 31)],
               fill=shade if i < 4 else (10, 22, 39, 35))
    return im


def river_tiles():
    """pond-autotile_{center,edge-n,edge-s} with the water turned brown."""
    out = {}
    for role in ('center', 'edge-n', 'edge-s'):
        im = Image.open(f'assets/sprites/pond-autotile_{role}.png').convert('RGBA')
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a and b > r + 24 and b > g:          # water, not the rock rim
                    lum = (r * 3 + g * 6 + b) / 10 / 255.0
                    px[x, y] = (int(70 + 150 * lum), int(52 + 112 * lum), int(34 + 70 * lum), a)
        out[f'sfb-river_{role}'] = im
    return out


def rowers():
    im, d = canvas(4, 1)                 # 128 x 32
    d.polygon([(6, 17), (16, 14), (112, 14), (124, 17), (112, 20), (16, 20)], fill=WHITE)
    d.line([(16, 20), (112, 20)], fill=STONE)
    d.line([(18, 17), (110, 17)], fill=rgb('2c6a8c'))
    for i, x in enumerate(range(30, 106, 20)):
        d.rectangle([x, 9, x + 5, 15], fill=(MUSTARD, NAVY)[i % 2])       # a rowing singlet
        d.rectangle([x + 1, 5, x + 4, 9], fill=SKIN)
        d.line([(x + 1, 5), (x + 4, 5)], fill=WOOD_DK)
        d.line([(x + 3, 13), (x - 8, 2 if i % 2 else 28)], fill=WOOD)     # the oar
        d.rectangle([x - 10, (1 if i % 2 else 27), x - 7, (3 if i % 2 else 29)], fill=RED)
    for x in range(0, 8, 3):             # the wake
        d.point((x, 17), fill=WHITE)
    outline(im)
    return im


LADIES = {      # body, shade, trim accent, door
    'a': (SKYBLUE, rgb('6a94bc'), NAVY, RED),
    'b': (LEMON, rgb('c8ac5c'), MAROON, TRAM),
    'c': (PINK, rgb('c07888'), rgb('6b4a8c'), NAVY),
    'd': (MINT, rgb('74a88c'), TRAM_LO, MAROON),
}


def lady(kind, step):
    """A painted lady. `step` px of brick footing lift it: the row climbs the hill."""
    body, shade, accent, door = LADIES[kind]
    im, d = canvas(3, 5)                 # 96 x 160
    base = 157 - step
    d.rectangle([4, base, 91, 157], fill=BROWN_LO)                       # the footing
    for y in range(base + 2, 157, 4):
        d.line([(4, y), (91, y)], fill=BROWN)
    box(d, 6, 62, 89, base, body, WHITE, shade)
    for y in range(68, base, 5):         # weatherboards
        d.line([(7, y), (88, y)], fill=shade)
    # the gable: steep, with fish-scale shingles and a sunburst
    d.polygon([(2, 64), (48, 12 - 0), (93, 64)], fill=accent)
    d.polygon([(8, 62), (48, 20), (87, 62)], fill=body)
    for y in range(28, 62, 5):
        half = int((y - 20) * 40 / 42)
        for x in range(48 - half + 2, 48 + half - 1, 6):
            d.arc([x, y, x + 5, y + 5], 0, 180, fill=shade)
    d.pieslice([38, 44, 58, 64], 180, 360, fill=WHITE)
    for a in range(200, 350, 25):
        d.line([(48, 54), (48 + int(9 * math.cos(math.radians(a))), 54 + int(9 * math.sin(math.radians(a))))], fill=accent)
    d.line([(2, 64), (48, 12)], fill=WHITE); d.line([(48, 12), (93, 64)], fill=WHITE)
    d.line([(48, 4), (48, 12)], fill=GOLD)
    d.rectangle([4, 62, 91, 65], fill=WHITE); d.line([(4, 66), (91, 66)], fill=accent)
    # the bay window, two storeys of it
    box(d, 10, 72, 46, base - 6, WHITE, WHITE, CREAM_LO)
    for y0 in (76, 110):
        if y0 + 22 > base - 8:
            continue
        for x in (13, 24, 35):
            d.rectangle([x, y0, x + 8, y0 + 22], fill=GLASS_DK)
            d.rectangle([x + 1, y0 + 1, x + 7, y0 + 21], fill=GLASS)
            d.line([(x + 1, y0 + 1), (x + 7, y0 + 1)], fill=GLASS_HI)
            d.line([(x + 1, y0 + 11), (x + 7, y0 + 11)], fill=GLASS_DK)
        d.rectangle([10, y0 + 24, 46, y0 + 26], fill=accent)
    # the door up its own flight of steps, under a little porch
    d.rectangle([56, 96, 84, 100], fill=WHITE); d.line([(56, 101), (84, 101)], fill=accent)
    for x in (57, 82):
        d.rectangle([x, 100, x + 1, base - 10], fill=WHITE)
    d.rectangle([62, 104, 78, base - 10], fill=door)
    d.rectangle([64, 106, 76, 118], fill=GLASS); d.line([(64, 106), (76, 106)], fill=GLASS_HI)
    d.point((76, 126), fill=GOLD)
    for i in range(3):
        d.rectangle([56 - i * 2, base - 9 + i * 3, 84 + i * 2, base - 7 + i * 3], fill=STONE if i % 2 == 0 else STONE_LO)
    window(d, 62, 72, 78, 92, frame=WHITE)
    outline(im)
    return im


def lane_wall(d, w=96):
    """Bluestone, 3x2: coursed blocks under a coping."""
    d.rectangle([0, 0, w - 1, 63], fill=BLUESTONE)
    for y in range(6, 64, 8):
        d.line([(0, y), (w - 1, y)], fill=BLUESTONE_LO)
        for x in range((y // 8 % 2) * 7, w, 14):
            d.line([(x, y - 7), (x, y)], fill=BLUESTONE_LO)
    d.rectangle([0, 0, w - 1, 3], fill=BLUESTONE_HI)
    d.line([(0, 4), (w - 1, 4)], fill=BLUESTONE_LO)
    d.rectangle([0, 60, w - 1, 63], fill=BLUESTONE_LO)


def mural(kind):
    im, d = canvas(3, 2)
    lane_wall(d)
    if kind == 'a':                      # a face in profile, pink on teal, and a tag
        d.rectangle([6, 10, 52, 56], fill=rgb('2f8c8c'))
        d.ellipse([14, 14, 44, 50], fill=PINK)
        d.polygon([(40, 28), (50, 34), (40, 38)], fill=PINK)
        d.ellipse([30, 26, 36, 31], fill=WHITE); d.point((34, 28), fill=INK)
        d.arc([28, 36, 42, 46], 20, 120, fill=RED)
        d.polygon([(14, 30), (20, 12), (40, 12), (30, 20)], fill=NAVY)
        for i, c in enumerate((AMBER, RED_HI, WHITE)):
            d.line([(58, 20 + i * 9), (66, 14 + i * 9), (72, 24 + i * 9), (80, 12 + i * 9), (88, 22 + i * 9)], fill=c, width=2)
    elif kind == 'b':                    # bubble letters and drips
        for i, (c, lo) in enumerate(((AMBER, ORANGE), (rgb('58c0e0'), GLASS), (PINK, MAROON), (rgb('9ad06a'), TRAM))):
            x = 6 + i * 22
            d.rounded_rectangle([x, 14, x + 18, 46], 6, fill=c, outline=INK)
            d.rounded_rectangle([x + 5, 22, x + 12, 36], 2, fill=lo)
            d.line([(x + 3, 17), (x + 9, 17)], fill=WHITE)
            d.line([(x + 6 + i, 46), (x + 6 + i, 52 + i * 2)], fill=c)
        for x in (10, 40, 70, 84):
            d.point((x, 10), fill=WHITE); d.point((x + 3, 54), fill=AMBER)
    else:                                # a stencilled bird, a paste-up, a rainbow stripe
        for i, c in enumerate((RED, AMBER, rgb('9ad06a'), rgb('58c0e0'), rgb('8a6ac8'))):
            d.line([(0, 44 + i * 2), (95, 30 + i * 2)], fill=c, width=2)
        d.polygon([(18, 28), (30, 14), (44, 18), (58, 10), (50, 24), (62, 30), (44, 32), (36, 42), (32, 30)], fill=WHITE)
        d.point((34, 20), fill=INK)
        d.rectangle([68, 12, 88, 38], fill=CREAM); d.rectangle([70, 14, 86, 26], fill=NAVY)
        for y in (29, 32, 35):
            d.line([(70, y), (84, y)], fill=CREAM_DK)
    outline(im)
    return im


def coffee():
    im, d = canvas(3, 2)
    lane_wall(d)
    # the hatch: lit, a machine and cups inside, a shelf to lean on
    d.rectangle([30, 14, 66, 44], fill=rgb('3a2c34'))
    d.rectangle([31, 26, 65, 43], fill=rgb('6a4a3a'))
    box(d, 34, 28, 48, 42, STONE, WHITE, STONE_LO)                       # the espresso machine
    d.rectangle([36, 31, 46, 33], fill=INK); d.point((38, 36), fill=RED); d.point((44, 36), fill=AMBER)
    for x in (52, 57, 62):
        d.rectangle([x, 36, x + 3, 42], fill=WHITE); d.line([(x, 38), (x + 3, 38)], fill=BROWN)
    d.rectangle([26, 44, 70, 47], fill=WOOD); d.line([(26, 44), (70, 44)], fill=WOOD_LO)
    # the awning: striped canvas
    for x in range(24, 73):
        c = TRAM if ((x - 24) // 6) % 2 == 0 else CREAM
        d.line([(x, 6), (x, 13)], fill=c)
        d.point((x, 14), fill=c if (x // 3) % 2 else CLEAR)
    d.line([(24, 6), (72, 6)], fill=WHITE)
    # the chalk board and a hanging cup sign
    box(d, 6, 16, 24, 50, rgb('2c3a30'), WOOD, WOOD_LO)
    for i, wdt in enumerate((12, 9, 13, 8, 11)):
        d.line([(9, 22 + i * 5), (9 + wdt, 22 + i * 5)], fill=WHITE if i else AMBER)
    d.ellipse([76, 16, 90, 30], fill=CREAM, outline=INK)
    d.rectangle([80, 21, 85, 26], fill=BROWN); d.arc([84, 21, 89, 26], 270, 90, fill=BROWN)
    d.line([(83, 10), (83, 16)], fill=INK)
    d.rectangle([74, 40, 92, 56], fill=rgb('c06a3a'))                    # a stack of milk crates
    for y in (44, 48, 52):
        d.line([(75, y), (91, y)], fill=ORANGE_LO)
    outline(im)
    return im


def crates():
    im, d = canvas(1, 1)
    for x, c, lo in ((2, rgb('c06a3a'), ORANGE_LO), (22, rgb('4a78b8'), GLASS)):
        d.rectangle([x, 16, x + 8, 28], fill=c)
        for y in (19, 23):
            d.line([(x + 1, y), (x + 7, y)], fill=lo)
    d.rectangle([11, 10, 21, 13], fill=WOOD); d.rectangle([15, 13, 17, 28], fill=WOOD_DK)
    d.rectangle([13, 6, 15, 9], fill=WHITE); d.rectangle([18, 6, 20, 9], fill=WHITE)
    outline(im)
    return im


def pyramid():
    im, d = canvas(4, 12)                # 128 x 384
    cx = 64
    px = im.load()

    def half(y):
        return 1 + (y - 40) * 43 / 280.0

    d.line([(cx, 4), (cx, 40)], fill=STONE)                             # the spire
    d.line([(cx - 1, 22), (cx - 1, 40)], fill=WHITE)
    for y in range(40, 322):
        w = int(half(y))
        for x in range(cx - w, cx + w + 1):
            lit = x < cx
            win = (y % 6 in (2, 3)) and ((x - cx) % 5 != 0) and y > 70
            c = (GLASS if lit else GLASS_DK) if win else (WHITE if lit else CREAM)
            px[x, y] = c
        px[cx + w, y] = CREAM_DK
        px[cx, y] = CREAM_LO
    # the two wings high on the tower (the lift shaft and the stair)
    for side in (-1, 1):
        for y in range(120, 250):
            w = int(half(y))
            for i in range(1, 6):
                px[cx + side * (w + i), y] = CREAM_LO if side > 0 else CREAM
        d.line([(cx + side * (int(half(120)) + 1), 119), (cx + side * (int(half(120)) + 5), 119)], fill=WHITE)
    # the base: the lattice of leaning columns, glass behind, a canopy and doors
    d.rectangle([14, 322, 113, 379], fill=GLASS_DK)
    for x in range(14, 110, 16):
        d.polygon([(x, 379), (x + 3, 379), (x + 11, 322), (x + 8, 322)], fill=WHITE)
        d.polygon([(x + 16, 379), (x + 13, 379), (x + 5, 322), (x + 8, 322)], fill=CREAM)
    d.rectangle([12, 318, 115, 323], fill=WHITE); d.line([(12, 324), (115, 324)], fill=CREAM_DK)
    d.rectangle([50, 352, 77, 379], fill=STONE_DK)
    d.rectangle([52, 356, 63, 379], fill=GLASS); d.rectangle([65, 356, 75, 379], fill=GLASS)
    d.line([(52, 356), (75, 356)], fill=GLASS_HI)
    outline(im)
    return im


def spire():
    im, d = canvas(4, 11)                # 128 x 352
    cx = 64
    # the mast and the lattice skirt: open work, so the sky shows through
    d.line([(cx, 4), (cx, 150)], fill=WHITE)
    d.line([(cx + 1, 60), (cx + 1, 150)], fill=STONE)
    d.point((cx, 2), fill=RED)

    def half(y):                         # a tutu: thin, then flaring out to the roof
        t = (y - 90) / 190.0
        return 2 + 50 * t ** 2.4

    for i in range(-6, 7):               # the ribs
        pts = [(cx + int(half(y) * i / 6.0), y) for y in range(90, 281, 6)]
        d.line(pts, fill=WHITE if i <= 0 else CREAM)
    for y in range(110, 281, 14):        # the hoops
        w = int(half(y))
        d.arc([cx - w, y - 3, cx + w, y + 3], 0, 180, fill=GOLD)
        d.arc([cx - w, y - 3, cx + w, y + 3], 180, 360, fill=CREAM_DK)
    for y in range(150, 280, 20):        # lights along the ribs
        for i in (-4, -1, 2, 5):
            d.point((cx + int(half(y) * i / 6.0), y), fill=AMBER)
    # the hall it stands on: a low drum of bluestone and glass
    box(d, 10, 284, 117, 347, BLUESTONE, BLUESTONE_HI, BLUESTONE_LO)
    d.rectangle([6, 280, 121, 286], fill=STONE); d.line([(6, 287), (121, 287)], fill=STONE_DK)
    for x in range(16, 112, 12):
        if 50 <= x <= 68:
            continue
        d.rectangle([x, 296, x + 7, 330], fill=GLASS_DK)
        d.rectangle([x + 1, 297, x + 6, 329], fill=GLASS); d.line([(x + 1, 297), (x + 6, 297)], fill=GLASS_HI)
    d.rectangle([50, 304, 77, 347], fill=STONE_DK)
    d.rectangle([52, 308, 63, 347], fill=AMBER); d.rectangle([65, 308, 75, 347], fill=AMBER)
    d.line([(52, 308), (75, 308)], fill=WHITE)
    d.rectangle([46, 300, 81, 304], fill=GOLD)
    d.rectangle([10, 340, 117, 347], fill=BLUESTONE_LO)
    outline(im)
    return im


def wheels(d, xs, y):
    for x in xs:
        d.ellipse([x, y, x + 7, y + 7], fill=INK); d.point((x + 3, y + 3), fill=STONE)


def cable_car():
    im, d = canvas(3, 2)                 # 96 x 64
    d.rectangle([6, 14, 89, 20], fill=CREAM); d.line([(6, 14), (89, 14)], fill=WHITE)      # the roof
    d.rectangle([14, 9, 81, 14], fill=CREAM_LO)
    box(d, 30, 20, 65, 52, MAROON, RED_HI, RED_DK)                                         # the closed middle
    for x in (34, 45, 56):
        d.rectangle([x, 24, x + 6, 36], fill=GLASS); d.line([(x, 24), (x + 6, 24)], fill=GLASS_HI)
    d.rectangle([31, 40, 64, 43], fill=GOLD)
    for x0 in (8, 66):                   # the open ends: posts, a bench, a running board
        for x in (x0, x0 + 10, x0 + 20):
            d.rectangle([x, 20, x + 1, 46], fill=WOOD_DK)
        d.rectangle([x0, 36, x0 + 21, 40], fill=WOOD); d.rectangle([x0, 40, x0 + 21, 46], fill=MAROON)
    d.rectangle([4, 46, 91, 51], fill=MAROON); d.line([(4, 46), (91, 46)], fill=RED_HI)
    d.rectangle([4, 52, 91, 54], fill=WOOD_LO)
    d.ellipse([44, 3, 51, 9], fill=GOLD)                                                   # the bell
    wheels(d, (16, 70), 54)
    outline(im)
    return im


def tram():
    im, d = canvas(4, 2)                 # 128 x 64
    d.rounded_rectangle([4, 12, 123, 54], 5, fill=TRAM)
    d.rectangle([5, 14, 122, 30], fill=CREAM)                                              # the cream top half
    d.rectangle([5, 30, 122, 33], fill=MUSTARD)
    d.line([(5, 14), (122, 14)], fill=WHITE)
    for x in range(10, 118, 13):
        if 55 <= x <= 68:
            continue
        d.rectangle([x, 17, x + 9, 28], fill=GLASS); d.line([(x, 17), (x + 9, 17)], fill=GLASS_HI)
    d.rectangle([58, 16, 70, 52], fill=TRAM_LO)                                            # the centre doors
    d.rectangle([60, 18, 63, 50], fill=GLASS_DK); d.rectangle([65, 18, 68, 50], fill=GLASS_DK)
    d.rectangle([5, 44, 122, 46], fill=MUSTARD)
    d.rectangle([5, 50, 122, 54], fill=TRAM_LO)
    d.rectangle([8, 8, 119, 12], fill=STONE_LO); d.line([(8, 8), (119, 8)], fill=STONE)    # the roof
    d.line([(64, 8), (52, 2)], fill=INK); d.line([(52, 2), (76, 2)], fill=INK)             # the pole
    d.rectangle([6, 36, 10, 40], fill=AMBER); d.rectangle([117, 36, 121, 40], fill=RED)
    wheels(d, (18, 34, 86, 102), 54)
    outline(im)
    return im


def rail():
    """Two rails and the cable slot between them, across a road tile."""
    im, d = canvas(1, 1)
    for y in (6, 24):
        d.line([(0, y), (31, y)], fill=STONE); d.line([(0, y + 1), (31, y + 1)], fill=STONE_DK)
    d.line([(0, 15), (31, 15)], fill=INK)
    return im


def oval():
    im, d = canvas(12, 7)                # 384 x 224, flat
    d.ellipse([4, 6, 379, 217], fill=TURF)
    px = im.load()
    for y in range(6, 218):              # mown stripes
        for x in range(4, 380):
            if px[x, y][3] and (x // 16) % 2:
                px[x, y] = TURF_HI
    d.ellipse([4, 6, 379, 217], outline=WHITE)
    d.ellipse([5, 7, 378, 216], outline=WHITE)
    d.ellipse([172, 92, 211, 131], outline=WHITE)                     # the centre circle and square
    d.rectangle([168, 88, 215, 135], outline=WHITE)
    d.line([(192, 92), (192, 131)], fill=WHITE)
    for x0, a0, a1 in ((4, 300, 60), (379, 120, 240)):                # the fifty-metre arcs
        d.arc([x0 - 110, 22, x0 + 110, 201], a0, a1, fill=WHITE)
    d.rectangle([4 + 3, 96, 30, 127], outline=WHITE)                  # the goal squares
    d.rectangle([353, 96, 379 - 3, 127], outline=WHITE)
    return im


def goalposts():
    im, d = canvas(2, 3)                 # 64 x 96: two tall posts between two short ones
    for x, top in ((8, 44), (24, 6), (38, 6), (54, 44)):
        d.rectangle([x, top, x + 2, 92], fill=WHITE)
        d.line([(x + 2, top), (x + 2, 92)], fill=STONE)
        d.rectangle([x - 1, 74, x + 3, 92], fill=(RED if top < 20 else NAVY))      # the padding
    outline(im)
    return im


def light_tower():
    im, d = canvas(1, 5)                 # 32 x 160
    d.rectangle([14, 30, 17, 156], fill=STONE_LO); d.line([(14, 30), (14, 156)], fill=STONE)
    for y in range(44, 150, 14):
        d.line([(12, y), (19, y)], fill=STONE_DK)
    box(d, 3, 6, 28, 30, STONE_DK, STONE, INK)
    for y in (9, 16, 23):
        for x in (6, 12, 18, 24):
            d.rectangle([x, y, x + 2, y + 4], fill=rgb('fff4c8'))
    d.rectangle([10, 152, 21, 157], fill=STONE_DK)
    outline(im)
    return im


def fog(kind):
    """A bank of fog: soft lumps, see-through, no outline."""
    im, d = canvas(5, 2)                 # 160 x 64
    lumps = ([(18, 30, 26), (48, 22, 30), (86, 30, 34), (122, 26, 28), (144, 36, 18)] if kind == 'a' else
             [(14, 36, 16), (40, 30, 26), (76, 24, 30), (108, 32, 30), (140, 28, 22)])
    for alpha, grow in ((70, 6), (110, 0), (150, -8)):
        layer = Image.new('RGBA', im.size, CLEAR)
        ld = ImageDraw.Draw(layer)
        for cx, cy, r in lumps:
            r2 = r + grow
            if r2 > 2:
                ld.ellipse([cx - r2, cy - r2 * 0.55, cx + r2, cy + r2 * 0.55], fill=(236, 240, 246, alpha))
        im.alpha_composite(layer)
    return im


def terminal():
    im, d = canvas(9, 5)                 # 288 x 160
    # the hall: a wave of white roof over a wall of glass
    d.rectangle([40, 74, 283, 157], fill=GLASS_DK)
    for x in range(44, 282, 14):
        d.rectangle([x, 78, x + 11, 150], fill=GLASS)
        d.line([(x, 78), (x + 11, 78)], fill=GLASS_HI)
        d.line([(x + 2, 84), (x + 6, 100)], fill=GLASS_HI)
        d.line([(x, 114), (x + 11, 114)], fill=GLASS_DK)
    pts = [(36, 78)] + [(x, 62 - int(10 * math.sin((x - 36) / 247.0 * math.pi * 2.5))) for x in range(36, 288, 4)] + [(287, 78)]
    d.polygon(pts, fill=WHITE)
    d.line(pts[1:-1], fill=STONE)
    d.rectangle([36, 76, 287, 80], fill=STONE); d.line([(36, 81), (287, 81)], fill=STONE_DK)
    d.rectangle([40, 150, 283, 157], fill=STONE_LO)
    # the doors and the sign over them: a plane, wheels down
    d.rectangle([126, 106, 193, 157], fill=STONE_DK)
    d.rectangle([130, 116, 158, 157], fill=GLASS_HI); d.rectangle([161, 116, 189, 157], fill=GLASS_HI)
    d.line([(144, 116), (144, 157)], fill=GLASS); d.line([(175, 116), (175, 157)], fill=GLASS)
    box(d, 122, 92, 197, 106, NAVY, GLASS, INK)
    plane_icon(d, 160, 99, WHITE)
    # the control tower, at the west end
    box(d, 12, 40, 30, 157, CREAM, WHITE, CREAM_DK)
    for y in range(52, 150, 16):
        d.rectangle([18, y, 24, y + 6], fill=GLASS_DK)
    d.polygon([(2, 40), (8, 18), (34, 18), (40, 40)], fill=GLASS)
    d.polygon([(2, 40), (8, 18), (20, 18), (16, 40)], fill=GLASS_HI)
    for x in (14, 24, 32):
        d.line([(x, 18), (x + (x - 21) // 4, 40)], fill=GLASS_DK)
    d.rectangle([6, 12, 36, 18], fill=WHITE); d.rectangle([2, 40, 40, 44], fill=WHITE)
    d.line([(21, 0), (21, 12)], fill=STONE_DK); d.point((21, 0), fill=RED)
    outline(im)
    return im


def plane_icon(d, cx, cy, fill):
    """A little airliner seen from above, nose to the right."""
    d.rectangle([cx - 9, cy - 1, cx + 8, cy + 1], fill=fill)
    d.point((cx + 9, cy), fill=fill)
    d.polygon([(cx - 2, cy - 1), (cx - 6, cy - 6), (cx - 3, cy - 6), (cx + 3, cy - 1)], fill=fill)
    d.polygon([(cx - 2, cy + 1), (cx - 6, cy + 6), (cx - 3, cy + 6), (cx + 3, cy + 1)], fill=fill)
    d.polygon([(cx - 9, cy - 1), (cx - 11, cy - 4), (cx - 9, cy - 4), (cx - 6, cy - 1)], fill=fill)
    d.polygon([(cx - 9, cy + 1), (cx - 11, cy + 4), (cx - 9, cy + 4), (cx - 6, cy + 1)], fill=fill)


def pier():
    im, d = canvas(4, 9)                 # 128 x 288, flat
    d.rectangle([2, 0, 125, 283], fill=WOOD)
    for x in range(2, 126, 10):          # planks, laid along the pier
        d.line([(x, 0), (x, 283)], fill=WOOD_LO)
        for y in range((x * 7) % 40, 284, 40):
            d.line([(x, y), (x + 9, y)], fill=WOOD_LO)
    d.rectangle([2, 0, 5, 283], fill=WOOD_DK); d.rectangle([122, 0, 125, 283], fill=WOOD_DK)
    d.rectangle([2, 280, 125, 283], fill=WOOD_DK)
    for y in range(8, 284, 44):          # bollards and the rope between them
        for x in (1, 120):
            d.rectangle([x, y, x + 6, y + 8], fill=WOOD_DK); d.rectangle([x + 1, y, x + 5, y + 2], fill=WOOD)
    for x in (4, 123):
        for y in range(8, 240, 4):
            d.point((x, y + 10), fill=CREAM)
    d.rectangle([2, 284, 125, 287], fill=(10, 22, 39, 90))               # its shadow on the water
    return im


def sea_lions():
    im, d = canvas(3, 2)                 # 96 x 64: a raft low in the water
    d.rectangle([4, 34, 91, 56], fill=WOOD); d.rectangle([4, 52, 91, 58], fill=WOOD_DK)
    for x in range(4, 92, 11):
        d.line([(x, 34), (x, 52)], fill=WOOD_LO)
    d.line([(4, 34), (91, 34)], fill=WOOD_HI)
    for x0, y0, flip in ((8, 30, 1), (36, 34, -1), (60, 28, 1)):         # three lying down
        d.ellipse([x0, y0, x0 + 26, y0 + 13], fill=SEAL)
        hx = x0 + (22 if flip > 0 else -2)
        d.ellipse([hx, y0 - 4, hx + 8, y0 + 5], fill=SEAL)
        d.point((hx + (6 if flip > 0 else 2), y0 - 1), fill=INK)
        d.arc([x0 + 2, y0 + 1, x0 + 24, y0 + 9], 190, 340, fill=SEAL_HI)
        d.polygon([(x0 + (0 if flip > 0 else 26), y0 + 8), (x0 + (-4 if flip > 0 else 30), y0 + 13),
                   (x0 + (2 if flip > 0 else 24), y0 + 12)], fill=SEAL_LO)
    d.polygon([(44, 30), (48, 8), (56, 6), (58, 14), (54, 30)], fill=SEAL)   # one sitting up, barking
    d.line([(49, 12), (51, 26)], fill=SEAL_HI)
    d.point((55, 9), fill=INK); d.line([(58, 11), (61, 9)], fill=SEAL_LO)
    for x, y in ((64, 4), (67, 7), (64, 10)):
        d.line([(x, y), (x + 2, y)], fill=WHITE)
    outline(im)
    for x in range(2, 94, 5):            # ripples round the raft
        d.point((x, 61), fill=WHITE)
    return im


WOOD_HI = rgb('d2a58c')
BLACK = rgb('000000')                    # the cast's ink (props are inked in INK)


# ---- the leaners: street colour on the pavements (tools/generate_sanfranbourne.py LEANERS) ----
# Each is a person in the cast's proportions (a big head, a small body, the same
# inked edge) standing folded double at the waist: legs straight, the back a hump
# over the hips, the head hanging at knee height, one arm straight down. Drawn
# facing left; `flip` mirrors. One look per letter, told apart by clothes.
LEAN_LOOKS = {
    #    top (fill, lit, shaded)                          trousers        shoes           hair            extras
    'a': dict(top=(rgb('a8424c'), rgb('c8626a'), rgb('7c2c38')), legs=rgb('2e3a5c'), shoes=rgb('e4cecc'),
              hair=rgb('3a2a20'), hood=True),                                        # red hoodie, hood up
    'b': dict(top=(rgb('7a5a3c'), rgb('9c7a58'), rgb('563c28')), legs=rgb('3c4046'), shoes=rgb('2a2a30'),
              hair=rgb('1c1612'), beanie=rgb('c8452c'), flip=True),                  # brown jacket, red beanie
    'c': dict(top=(rgb('4f7a5c'), rgb('6f9a7c'), rgb('34563e')), legs=rgb('6a5a48'), shoes=rgb('8a3a34'),
              hair=rgb('c8a050'), pack=(rgb('3c4c70'), rgb('5c6c94'), rgb('f0d888'))),   # green parka, backpack
    'd': dict(top=(rgb('24242c'), rgb('44444e'), rgb('14141a')), legs=rgb('8e939e'), shoes=rgb('e8e8ee'),
              hair=rgb('6a4a30'), cap=rgb('e0b040'), cup=True, flip=True),           # black puffer, cap, a cup
}


def leaner(kind):
    look = LEAN_LOOKS[kind]
    im, _ = canvas(1, 1)
    top, top_hi, top_lo = look['top']

    def part(draw):
        """One inked piece laid over what is there (the cast's bodies are inked piece by piece)."""
        layer, d = canvas(1, 1)
        draw(d)
        outline(layer, ink=BLACK)
        im.alpha_composite(layer)

    def far_leg(d):
        d.rectangle([22, 12, 24, 26], fill=tuple(int(c * 0.75) for c in look['legs'][:3]) + (255,))
        d.rectangle([20, 26, 24, 27], fill=look['shoes'])

    def near_leg(d):
        d.polygon([(19, 10), (25, 10), (25, 13), (22, 15), (22, 26), (19, 26)], fill=look['legs'])   # the seat, the leg
        d.rectangle([17, 26, 22, 27], fill=look['shoes'])

    def head(d):
        # a cast-sized head hanging crown-down off the shoulders, the face turned to the knees
        d.rectangle([2, 15, 9, 25], fill=SKIN); d.rectangle([1, 16, 10, 24], fill=SKIN)
        if look.get('hood'):
            d.rectangle([1, 16, 3, 24], fill=top); d.rectangle([2, 22, 9, 25], fill=top); d.rectangle([2, 15, 4, 15], fill=top)
            d.line([(1, 17), (1, 23)], fill=top_hi); d.line([(4, 16), (4, 21)], fill=top_lo); d.line([(4, 21), (10, 21)], fill=top_lo)
        else:
            d.rectangle([1, 16, 4, 24], fill=look['hair']); d.rectangle([2, 21, 9, 25], fill=look['hair'])
            d.rectangle([2, 15, 4, 15], fill=look['hair']); d.rectangle([5, 20, 6, 20], fill=look['hair'])
        if look.get('beanie'):
            d.rectangle([1, 21, 10, 24], fill=look['beanie']); d.rectangle([2, 25, 9, 26], fill=look['beanie'])
            d.line([(1, 21), (10, 21)], fill=RED_LO)
        if look.get('cap'):
            d.rectangle([1, 22, 10, 24], fill=look['cap']); d.rectangle([2, 25, 9, 25], fill=look['cap'])
            d.rectangle([10, 23, 13, 24], fill=look['cap'])
        d.line([(7, 19), (8, 19)], fill=BLACK)                    # an eye, shut
        d.point((9, 17), fill=rgb('e8848a'))

    def body(d):
        # the back: from the hips, the highest point, straight down the slope to the shoulders
        d.polygon([(24, 6), (20, 6), (7, 13), (6, 17), (11, 18), (21, 12), (25, 11), (25, 8)], fill=top)
        d.line([(20, 6), (24, 6)], fill=top_hi); d.line([(19, 7), (8, 13)], fill=top_hi)
        d.line([(12, 17), (21, 12)], fill=top_lo); d.line([(21, 12), (25, 11)], fill=top_lo)
        if look.get('hood'):
            d.rectangle([6, 13, 8, 16], fill=top_lo)              # the hood's collar, bunched at the neck

    def pack(d):
        fill, hi, tag = look['pack']
        d.polygon([(21, 1), (17, 1), (9, 6), (9, 10), (12, 10), (22, 5), (23, 3)], fill=fill)
        d.line([(17, 1), (21, 1)], fill=hi); d.line([(16, 2), (10, 6)], fill=hi)
        d.rectangle([14, 5, 16, 6], fill=tag)

    def near_arm(d):
        d.rectangle([11, 15, 13, 23], fill=top)
        d.line([(11, 16), (11, 23)], fill=top_hi)
        d.rectangle([11, 24, 13, 26], fill=SKIN)
        if look.get('cup'):
            d.rectangle([11, 26, 14, 29], fill=WHITE); d.line([(11, 27), (14, 27)], fill=RED)

    for draw in (far_leg, near_leg, body) + ((pack,) if look.get('pack') else ()) + (head, near_arm):
        part(draw)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if look.get('flip') else im


def palm():
    im, d = canvas(3, 4)                 # 96 x 128, trunk in the middle cell
    for y in range(40, 124):             # a leaning, ringed trunk
        x = 46 + int(3 * math.sin((y - 40) / 84.0 * math.pi))
        d.line([(x, y), (x + 4, y)], fill=BROWN if y % 6 else BROWN_LO)
        d.point((x, y), fill=BROWN_HI)
    for a, ln in ((200, 40), (235, 44), (270, 40), (305, 44), (340, 40), (170, 34), (10, 34)):
        for t in range(ln):              # a frond: an arc that droops, leaflets off it
            fx = 48 + math.cos(math.radians(a)) * t
            fy = 40 + math.sin(math.radians(a)) * t * 0.8 + (t / 9.0) ** 2
            d.point((fx, fy), fill=LEAF_LO)
            if t % 3 == 0 and t > 4:
                d.line([(fx, fy), (fx - 2, fy + 5)], fill=LEAF)
                d.line([(fx, fy), (fx + 2, fy + 5)], fill=LEAF_HI)
    d.ellipse([43, 36, 53, 44], fill=BROWN_LO)
    outline(im)
    return im


def rock():
    im, d = canvas(5, 3)                 # 160 x 96
    d.polygon([(6, 88), (14, 60), (40, 48), (70, 52), (104, 44), (136, 56), (154, 88)], fill=STONE_LO)
    d.polygon([(14, 60), (40, 48), (70, 52), (104, 44), (136, 56), (120, 62), (60, 62), (24, 66)], fill=STONE)
    for x in range(16, 150, 9):
        d.line([(x, 70 + (x % 4)), (x + 4, 78 + (x % 3))], fill=STONE_DK)
    box(d, 44, 34, 108, 52, CREAM, WHITE, CREAM_DK)                      # the cell block
    for x in range(48, 106, 7):
        d.rectangle([x, 39, x + 3, 46], fill=GLASS_DK)
    d.rectangle([42, 32, 110, 35], fill=CREAM_DK)
    d.rectangle([120, 14, 127, 54], fill=WHITE); d.line([(127, 14), (127, 54)], fill=STONE)   # the lighthouse
    d.rectangle([120, 28, 127, 33], fill=RED)
    d.rectangle([118, 8, 129, 14], fill=GLASS_HI); d.polygon([(117, 8), (123, 2), (130, 8)], fill=RED_DK)
    d.rectangle([20, 58, 32, 64], fill=LEAF); d.rectangle([84, 54, 94, 58], fill=LEAF_LO)
    outline(im)
    for x in range(4, 158, 6):
        d.point((x, 91 + (x % 3)), fill=WHITE)
    return im


# ------------------------------------------------------------------------------ the airports
def airport_wall():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([0, 0, 31, 63], fill=CREAM)
    d.rectangle([0, 0, 31, 5], fill=STONE); d.line([(0, 6), (31, 6)], fill=STONE_LO)
    d.line([(0, 0), (0, 63)], fill=WHITE); d.line([(31, 7), (31, 55)], fill=CREAM_LO)
    d.rectangle([0, 56, 31, 63], fill=STONE_LO); d.line([(0, 56), (31, 56)], fill=STONE_DK)
    return im


def airport_window():
    im, d = canvas(2, 2)                 # 64 x 64: the apron through the glass
    d.rectangle([0, 0, 63, 63], fill=CREAM)
    d.rectangle([0, 0, 63, 5], fill=STONE); d.line([(0, 6), (63, 6)], fill=STONE_LO)
    d.rectangle([0, 56, 63, 63], fill=STONE_LO); d.line([(0, 56), (63, 56)], fill=STONE_DK)
    d.rectangle([3, 10, 60, 52], fill=STONE_DK)
    for y in range(11, 52):
        t = (y - 11) / 40.0
        d.line([(4, y), (59, y)], fill=(int(120 + 70 * t), int(180 + 40 * t), 250))
    d.rectangle([4, 44, 59, 51], fill=STONE_LO)                          # the tarmac
    d.line([(4, 47), (59, 47)], fill=AMBER)
    # a parked airliner's tail and rear fuselage
    d.polygon([(4, 36), (40, 32), (56, 36), (40, 41), (4, 41)], fill=WHITE)
    d.polygon([(8, 34), (4, 16), (14, 16), (24, 33)], fill=RED)
    d.line([(4, 41), (40, 41)], fill=STONE)
    for x in range(22, 50, 5):
        d.point((x, 36), fill=GLASS_DK)
    d.line([(31, 10), (31, 52)], fill=STONE_DK)
    d.line([(4, 11), (59, 11)], fill=WHITE)
    return im


def airport_gate():
    im, d = canvas(2, 2)                 # 64 x 64: the jet bridge door
    d.rectangle([0, 0, 63, 63], fill=CREAM)
    d.rectangle([0, 0, 63, 5], fill=STONE); d.line([(0, 6), (63, 6)], fill=STONE_LO)
    d.rectangle([0, 56, 63, 63], fill=STONE_LO)
    box(d, 6, 8, 57, 21, NAVY, GLASS, INK)
    plane_icon(d, 20, 14, WHITE)
    label(d, 42, 11, 'GATE', AMBER)
    d.rectangle([8, 23, 55, 63], fill=STONE_DK)
    for i in range(10):                  # the bridge, narrowing away to the aircraft door
        c = (40 + i * 9, 46 + i * 9, 66 + i * 9)
        d.rectangle([10 + i * 2, 25 + i, 53 - i * 2, 63], fill=c)
    d.rectangle([28, 36, 35, 63], fill=rgb('fff4c8'))
    d.line([(10, 62), (28, 50)], fill=AMBER); d.line([(53, 62), (35, 50)], fill=AMBER)
    return im


def airport_board():
    im, d = canvas(2, 2)                 # 64 x 64: the departures board, on the wall
    d.rectangle([0, 0, 63, 63], fill=CREAM)
    d.rectangle([0, 0, 63, 5], fill=STONE); d.line([(0, 6), (63, 6)], fill=STONE_LO)
    d.rectangle([0, 56, 63, 63], fill=STONE_LO)
    box(d, 3, 9, 60, 52, INK, STONE_LO, INK)
    d.rectangle([5, 11, 58, 18], fill=NAVY)
    plane_icon(d, 14, 14, AMBER)
    for x in range(26, 56, 4):
        d.line([(x, 14), (x + 2, 14)], fill=WHITE)
    for i in range(5):
        y = 23 + i * 6
        d.line([(6, y), (11, y)], fill=LED)                              # the time
        d.line([(15, y), (15 + (22, 16, 26, 14, 20)[i], y)], fill=LED)   # where to
        d.line([(47, y), (56, y)], fill=rgb('78e66e') if i != 2 else RED_HI)   # on time / delayed
    d.line([(31, 53), (31, 55)], fill=STONE_DK)
    return im


def airport_seats():
    im, d = canvas(3, 1)                 # 96 x 32: a bank of lounge seats, facing you
    d.rectangle([2, 26, 93, 28], fill=STONE_DK)
    for x in range(4, 92, 15):
        box(d, x, 4, x + 12, 18, CARPET, rgb('6a80b0'), CARPET_LO)
        box(d, x, 18, x + 12, 25, rgb('5a70a0'), rgb('7a90c0'), CARPET_LO)
        d.rectangle([x - 1, 16, x, 24], fill=STONE); d.rectangle([x + 12, 16, x + 13, 24], fill=STONE)
    for x in (6, 88):
        d.line([(x, 28), (x, 30)], fill=STONE_DK)
    outline(im)
    return im


def airport_security():
    im, d = canvas(1, 2)                 # 32 x 64: the arch you walk through
    d.rectangle([2, 8, 6, 62], fill=STONE); d.rectangle([25, 8, 29, 62], fill=STONE_LO)
    d.line([(2, 8), (2, 62)], fill=WHITE)
    d.rectangle([2, 4, 29, 10], fill=STONE); d.line([(2, 4), (29, 4)], fill=WHITE)
    d.rectangle([12, 6, 14, 8], fill=rgb('78e66e')); d.rectangle([17, 6, 19, 8], fill=STONE_DK)
    for y in range(16, 60, 8):
        d.point((4, y), fill=GLASS_HI); d.point((27, y), fill=GLASS_HI)
    d.rectangle([0, 60, 8, 63], fill=STONE_DK); d.rectangle([23, 60, 31, 63], fill=STONE_DK)
    outline(im)
    return im


def airport_xray():
    im, d = canvas(3, 2)                 # 96 x 64: the belt, the scanner, a tray going in
    box(d, 2, 34, 93, 60, STONE_LO, STONE, STONE_DK)
    d.rectangle([4, 30, 91, 36], fill=INK)
    for x in range(6, 90, 6):
        d.line([(x, 31), (x, 35)], fill=STONE_DK)
    box(d, 30, 8, 66, 40, STONE, WHITE, STONE_LO)                        # the tunnel
    d.rectangle([34, 22, 62, 36], fill=INK)
    for x in range(35, 62, 3):
        d.line([(x, 22), (x, 30)], fill=STONE_DK)                        # the lead curtain
    d.rectangle([38, 12, 58, 18], fill=GLASS_DK); d.rectangle([40, 13, 48, 17], fill=rgb('78e66e'))
    box(d, 8, 24, 24, 32, rgb('8a8a94'), WHITE, STONE_DK)                # a tray: a bag in it
    d.rectangle([11, 20, 21, 28], fill=RED); d.line([(14, 18), (18, 18)], fill=RED_DK)
    box(d, 72, 24, 88, 32, rgb('8a8a94'), WHITE, STONE_DK)
    d.rectangle([76, 22, 84, 27], fill=NAVY)
    outline(im)
    return im


def airport_checkin():
    im, d = canvas(3, 2)                 # 96 x 64: two desks, the belt between them
    for x0 in (2, 60):
        box(d, x0, 26, x0 + 33, 60, WHITE, WHITE, STONE)
        d.rectangle([x0 + 1, 36, x0 + 32, 40], fill=NAVY)
        plane_icon(d, x0 + 17, 49, STONE_LO)
        d.rectangle([x0, 22, x0 + 33, 27], fill=STONE); d.line([(x0, 22), (x0 + 33, 22)], fill=WHITE)
        box(d, x0 + 9, 6, x0 + 24, 19, INK, STONE_LO, INK)               # the screen
        d.rectangle([x0 + 11, 8, x0 + 22, 11], fill=GLASS_HI)
        d.line([(x0 + 11, 14), (x0 + 20, 14)], fill=LED); d.line([(x0 + 11, 16), (x0 + 17, 16)], fill=LED)
        d.line([(x0 + 16, 19), (x0 + 16, 22)], fill=STONE_DK)
    d.rectangle([36, 38, 59, 60], fill=STONE_DK)                         # the baggage belt
    for y in range(40, 60, 4):
        d.line([(37, y), (58, y)], fill=INK)
    box(d, 40, 30, 55, 44, rgb('3f7a4c'), GREEN_HI, GREEN_LO)            # a suitcase on it
    d.rectangle([45, 27, 50, 30], fill=INK)
    outline(im)
    return im


def airport_bar():
    im, d = canvas(5, 3)                 # 160 x 96: back shelf, the counter and its taps, stools
    # the back bar: dark timber, a mirror, bottles, the sign
    box(d, 2, 2, 157, 44, WOOD_DK, WOOD_LO, INK)
    box(d, 50, 4, 109, 15, rgb('2c3a30'), GOLD, INK)
    label(d, 80, 6, 'PUB', AMBER)
    d.rectangle([6, 18, 153, 30], fill=rgb('3a2c34'))
    d.rectangle([8, 19, 151, 22], fill=GLASS_DK)
    for i, x in enumerate(range(9, 150, 6)):
        c = (GREEN_HI, AMBER, WHITE, RED_HI, rgb('8a5630'), GLASS_HI)[i % 6]
        h = (9, 7, 10, 8)[i % 4]
        d.rectangle([x, 30 - h, x + 2, 29], fill=c); d.point((x + 1, 30 - h - 1), fill=c)
    d.rectangle([6, 30, 153, 32], fill=WOOD); d.line([(6, 33), (153, 33)], fill=INK)
    for i, x in enumerate(range(10, 150, 9)):                            # glasses on the lower shelf
        d.rectangle([x, 37, x + 3, 42], fill=GLASS_HI if i % 3 else AMBER)
    # the counter: a polished top, a panelled front, a brass foot rail
    box(d, 0, 44, 159, 54, WOOD, WOOD_HI, WOOD_LO)
    d.line([(4, 47), (60, 47)], fill=WOOD_HI); d.line([(90, 49), (150, 49)], fill=WOOD_HI)
    box(d, 2, 54, 157, 80, WOOD_LO, WOOD, WOOD_DK)
    for x in range(8, 156, 18):
        d.rectangle([x, 58, x + 12, 74], outline=WOOD_DK)
    d.line([(2, 78), (157, 78)], fill=GOLD)
    # the taps: a brass font, three handles
    box(d, 68, 36, 91, 44, GOLD, rgb('f2d070'), rgb('8a6a30'))
    for x, c in ((70, RED), (78, WHITE), (86, GREEN_HI)):
        d.rectangle([x, 26, x + 3, 36], fill=c); d.line([(x + 1, 36), (x + 1, 40)], fill=STONE)
    for x, full in ((24, True), (40, False), (116, True), (132, True)):  # pints waiting on the bar
        d.rectangle([x, 37, x + 5, 46], fill=AMBER if full else GLASS_HI)
        d.rectangle([x, 36, x + 5, 38], fill=WHITE)
        d.arc([x + 4, 39, x + 9, 45], 270, 90, fill=WHITE)
    # the stools, pushed up to the rail
    for x in range(14, 150, 30):
        d.ellipse([x, 76, x + 13, 83], fill=MAROON); d.arc([x, 76, x + 13, 83], 180, 360, fill=RED_HI)
        d.line([(x + 6, 83), (x + 6, 92)], fill=STONE_DK)
        d.line([(x + 2, 92), (x + 11, 92)], fill=STONE_DK)
    outline(im)
    return im


def airport_trolley():
    im, d = canvas(1, 1)
    d.rectangle([4, 22, 27, 24], fill=STONE); d.line([(26, 6), (26, 22)], fill=STONE)
    d.line([(22, 6), (27, 6)], fill=STONE_DK)
    box(d, 5, 10, 20, 21, NAVY, GLASS, INK)                              # a case
    box(d, 8, 3, 18, 9, RED, RED_HI, RED_DK)                             # ...and a bag on it
    d.rectangle([10, 14, 15, 15], fill=GOLD)
    for x in (6, 22):
        d.ellipse([x, 25, x + 4, 29], fill=INK)
    outline(im)
    return im


def airport_carpet():
    im, d = canvas(1, 1)
    d.rectangle([0, 0, 31, 31], fill=CARPET)
    for y in range(0, 32, 8):
        for x in range(0, 32, 8):
            d.point((x + 2 + (y // 8 % 2) * 4, y + 3), fill=rgb('6a80b0'))
            d.point((x + 6 - (y // 8 % 2) * 4, y + 7), fill=CARPET_LO)
    return im


# ------------------------------------------------------------------------------ the flight
CABIN_W, CABIN_H = 364, 120              # the train interiors' size at 1x (drawn 1x, saved 2x)
WINDOW_BAND = (20, 46)                   # rows of the cabin wall the windows are cut through
WINDOW_STEP = 26


def plane_interior():
    """The cabin, seen from the aisle: the overhead bins, the window wall (the
    windows are holes: the sky is drawn behind this picture), a row of window
    seats under them, the aisle carpet, and the headrests of the near row."""
    im = Image.new('RGBA', (CABIN_W, CABIN_H), CLEAR)
    d = ImageDraw.Draw(im)
    wall, wall_lo, wall_hi = rgb('dfe3ea'), rgb('b8bfcc'), rgb('f4f6fa')
    d.rounded_rectangle([0, 0, CABIN_W - 1, CABIN_H - 1], 10, fill=wall)
    # the overhead bins: a run of curved lockers with latches, the light strip under them
    d.rectangle([0, 0, CABIN_W - 1, 15], fill=wall_hi)
    for x in range(4, CABIN_W - 4, 52):
        d.rounded_rectangle([x, 2, x + 48, 13], 3, fill=WHITE, outline=wall_lo)
        d.rectangle([x + 21, 10, x + 27, 11], fill=STONE_LO)
    d.rectangle([0, 15, CABIN_W - 1, 16], fill=rgb('fff4c8'))
    d.line([(0, 17), (CABIN_W - 1, 17)], fill=wall_lo)
    # the wall: windows with their shades, a little way down on some
    y0, y1 = WINDOW_BAND
    px = im.load()
    first = (CABIN_W // 2 - WINDOW_STEP // 2) % WINDOW_STEP
    for i, x in enumerate(range(first, CABIN_W - 14, WINDOW_STEP)):
        cx = x
        d.rounded_rectangle([cx - 8, y0 - 2, cx + 8, y1 + 2], 7, fill=wall_hi, outline=wall_lo)
        # the post down the middle of each window. Pillow before 13 left the one middle column of
        # these two rounded rectangles unfilled, and that is the cabin as committed: the column is
        # drawn here, and kept out of the hole, so the picture is the same on any Pillow (issue #230)
        d.line([(cx, y0 - 1), (cx, y1 + 1)], fill=wall)
        hole = Image.new('L', im.size, 0)
        ImageDraw.Draw(hole).rounded_rectangle([cx - 6, y0, cx + 6, y1], 5, fill=255)
        shade = (0, 5, 0, 0, 9, 0, 0)[i % 7]                              # a pulled-down blind
        for yy in range(y0 + shade, y1 + 1):
            for xx in range(cx - 6, cx + 7):
                if xx != cx and hole.getpixel((xx, yy)):
                    px[xx, yy] = CLEAR
        if shade:
            d.line([(cx - 4, y0 + shade - 1), (cx + 4, y0 + shade - 1)], fill=wall_lo)
    d.line([(0, 52), (CABIN_W - 1, 52)], fill=wall_lo)
    d.rectangle([0, 53, CABIN_W - 1, 58], fill=rgb('c8ced8'))
    # the window seats, side on and facing the nose (right): back, headrest cover, cushion, armrest
    seat, seat_lo, seat_hi = rgb('3f5f9a'), rgb('2c4474'), rgb('5c80c0')
    for x in range(8, CABIN_W - 30, WINDOW_STEP):
        d.rounded_rectangle([x, 44, x + 9, 80], 3, fill=seat, outline=seat_lo)
        d.rectangle([x + 1, 45, x + 8, 51], fill=WHITE)
        d.line([(x + 2, 56), (x + 2, 76)], fill=seat_hi)
        d.rounded_rectangle([x + 4, 72, x + 22, 82], 2, fill=seat, outline=seat_lo)
        d.line([(x + 8, 74), (x + 20, 74)], fill=seat_hi)
        d.rectangle([x + 10, 66, x + 21, 68], fill=STONE_LO)
        d.rectangle([x + 12, 54, x + 20, 60], fill=rgb('c8ced8'))        # the tray of the seat in front
        d.line([(x + 6, 82), (x + 6, 88)], fill=STONE_DK); d.line([(x + 20, 82), (x + 20, 88)], fill=STONE_DK)
    # the aisle: carpet, the floor-path lights
    d.rectangle([0, 88, CABIN_W - 1, CABIN_H - 1], fill=CARPET)
    for x in range(0, CABIN_W, 8):
        d.point((x + 2, 92), fill=rgb('6a80b0')); d.point((x + 6, 99), fill=CARPET_LO)
    for x in range(10, CABIN_W, 20):
        d.rectangle([x, 89, x + 3, 89], fill=AMBER)
    # the near row: only the tops of its seat backs show
    for x in range(-6, CABIN_W, 30):
        d.rounded_rectangle([x, 102, x + 24, 126], 5, fill=seat, outline=seat_lo)
        d.rectangle([x + 3, 103, x + 21, 109], fill=WHITE)
        d.line([(x + 4, 113), (x + 20, 113)], fill=seat_hi)
    # the cabin's own outline, and its end walls
    mask = im.getchannel('A')
    edge = Image.new('RGBA', im.size, CLEAR)
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle([0, 0, CABIN_W - 1, CABIN_H - 1], 10, outline=INK)
    im.alpha_composite(Image.composite(edge, Image.new('RGBA', im.size, CLEAR), mask))
    return im


SKY_W, SKY_H = 640, 44


def plane_sky():
    """What goes past the windows, left to right: a bright day over the sea,
    cloud tops, the sun going down, dusk and the first stars. Opaque."""
    im = Image.new('RGBA', (SKY_W, SKY_H), CLEAR)
    px = im.load()
    stops = [      # (x as a fraction, top colour, horizon colour, sea colour)
        (0.00, (86, 150, 232), (170, 214, 250), (58, 104, 176)),
        (0.45, (92, 150, 226), (190, 220, 246), (60, 100, 168)),
        (0.62, (110, 120, 190), (250, 190, 120), (86, 86, 140)),
        (0.74, (96, 70, 140), (248, 140, 80), (90, 60, 100)),
        (0.88, (40, 36, 90), (150, 80, 110), (40, 36, 80)),
        (1.00, (16, 18, 48), (50, 44, 96), (18, 20, 52)),
    ]

    def mix(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    horizon = 31
    for x in range(SKY_W):
        f = x / (SKY_W - 1.0)
        for (f0, t0, h0, s0), (f1, t1, h1, s1) in zip(stops, stops[1:]):
            if f0 <= f <= f1:
                t = (f - f0) / (f1 - f0)
                top, hor, sea = mix(t0, t1, t), mix(h0, h1, t), mix(s0, s1, t)
                break
        for y in range(SKY_H):
            if y < horizon:
                band = int((y / float(horizon)) * 6) / 6.0           # banded, not smooth: pixel art
                px[x, y] = mix(top, hor, band) + (255,)
            else:
                glint = ((x * 7 + y * 13) % 23 == 0)
                px[x, y] = (mix(sea, hor, 0.5) if glint else sea) + (255,)
    d = ImageDraw.Draw(im)
    # the sun, low over the sea at the sunset stop, and its road on the water
    sx = int(SKY_W * 0.70)
    d.ellipse([sx - 7, horizon - 9, sx + 7, horizon + 5], fill=(255, 226, 150))
    d.ellipse([sx - 5, horizon - 7, sx + 5, horizon + 3], fill=(255, 244, 200))
    for y in range(horizon, SKY_H):
        for x in range(sx - 8 + (y - horizon) // 2, sx + 9 - (y - horizon) // 2, 2 + (y % 2)):
            px[x, y] = (255, 200, 130, 255)
    # clouds: flat-bottomed heaps, white by day, lit pink and gold near the sun
    seed = 218
    for i in range(26):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        cx = seed % SKY_W
        cy = 6 + (seed >> 8) % 20
        f = cx / float(SKY_W)
        if f > 0.9:
            continue
        col = (255, 255, 255) if f < 0.55 else (255, 214, 190) if f < 0.72 else (190, 130, 160)
        lo = (206, 222, 244) if f < 0.55 else (232, 150, 130) if f < 0.72 else (110, 80, 130)
        wdt = 10 + (seed >> 4) % 18
        d.rectangle([cx - wdt, cy, cx + wdt, cy + 3], fill=lo)
        for j in range(-wdt + 3, wdt - 2, 5):
            r = 3 + ((seed >> (j % 9 + 3)) % 3)
            d.ellipse([cx + j - r, cy - r, cx + j + r, cy + 2], fill=col)
        d.line([(cx - wdt, cy + 3), (cx + wdt, cy + 3)], fill=lo)
    for i in range(40):                  # the first stars, out past the dusk
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x = int(SKY_W * 0.86) + seed % int(SKY_W * 0.14)
        y = (seed >> 9) % (horizon - 6)
        px[min(x, SKY_W - 1), y] = (255, 255, 230, 255)
    return im


# ------------------------------------------------------------------------------
SPRITES = {      # key: (builder, tileNames label)
    'sfb-clocks-station_0_0': (clocks_station, 'sfb-clocks-station'),
    'sfb-bridge-tower_0_0': (bridge_tower, 'sfb-bridge-tower'),
    'sfb-bridge-cable-w_0_0': (lambda: bridge_cable('w'), 'sfb-bridge-cable'),
    'sfb-bridge-cable-e_0_0': (lambda: bridge_cable('e'), 'sfb-bridge-cable'),
    'sfb-rowers_0_0': (rowers, 'sfb-rowers'),
    'sfb-lady-a_0_0': (lambda: lady('a', 0), 'sfb-lady'),
    'sfb-lady-b_0_0': (lambda: lady('b', 5), 'sfb-lady'),
    'sfb-lady-c_0_0': (lambda: lady('c', 10), 'sfb-lady'),
    'sfb-lady-d_0_0': (lambda: lady('d', 15), 'sfb-lady'),
    'sfb-mural-a_0_0': (lambda: mural('a'), 'sfb-mural'),
    'sfb-mural-b_0_0': (lambda: mural('b'), 'sfb-mural'),
    'sfb-mural-c_0_0': (lambda: mural('c'), 'sfb-mural'),
    'sfb-coffee_0_0': (coffee, 'sfb-coffee'),
    'sfb-crates_0_0': (crates, 'sfb-crates'),
    'sfb-pyramid_0_0': (pyramid, 'sfb-pyramid'),
    'sfb-spire_0_0': (spire, 'sfb-spire'),
    'sfb-cable-car_0_0': (cable_car, 'sfb-cable-car'),
    'sfb-tram_0_0': (tram, 'sfb-tram'),
    'sfb-rail-h_0_0': (rail, 'sfb-rail'),
    'sfb-oval_0_0': (oval, 'sfb-oval'),
    'sfb-goalposts_0_0': (goalposts, 'sfb-goalposts'),
    'sfb-oval-lamp-post_0_0': (light_tower, 'sfb-oval-lamp-post'),
    'sfb-fog-a_0_0': (lambda: fog('a'), 'sfb-fog'),
    'sfb-fog-b_0_0': (lambda: fog('b'), 'sfb-fog'),
    'sfb-terminal_0_0': (terminal, 'sfb-terminal'),
    'sfb-pier_0_0': (pier, 'sfb-pier'),
    'sfb-sea-lions_0_0': (sea_lions, 'sfb-sea-lions'),
    'sfb-palm_0_0': (palm, 'sfb-palm'),
    'sfb-rock_0_0': (rock, 'sfb-rock'),
    'sfb-lean-a_0_0': (lambda: leaner('a'), 'sfb-lean'),
    'sfb-lean-b_0_0': (lambda: leaner('b'), 'sfb-lean'),
    'sfb-lean-c_0_0': (lambda: leaner('c'), 'sfb-lean'),
    'sfb-lean-d_0_0': (lambda: leaner('d'), 'sfb-lean'),
    'airport-wall_0_0': (airport_wall, 'airport-wall'),
    'airport-window_0_0': (airport_window, 'airport-window'),
    'airport-gate_0_0': (airport_gate, 'airport-gate'),
    'airport-board_0_0': (airport_board, 'airport-board'),
    'airport-seats_0_0': (airport_seats, 'airport-seats'),
    'airport-security_0_0': (airport_security, 'airport-security'),
    'airport-xray_0_0': (airport_xray, 'airport-xray'),
    'airport-checkin_0_0': (airport_checkin, 'airport-checkin'),
    'airport-bar_0_0': (airport_bar, 'airport-bar'),
    'airport-trolley_0_0': (airport_trolley, 'airport-trolley'),
    'airport-carpet_0_0': (airport_carpet, 'airport-carpet'),
}

# Flat on the ground / on the water: Non-Collidables with a depth nudge under
# everything standing (see generate_hokkaido.FLAT). You walk ON these.
FLAT = {'sfb-oval_0_0': -200, 'sfb-pier_0_0': -200}

# Tall enough to look up at: sprite family -> rows of building below the sprite
# (config game.lookUp.sprites, see "Looking up at landmarks" in hud-input-touch.md)
LOOK_UP = {'sfb-pyramid': 0, 'sfb-spire': 0}

# Whole pictures for the flight cutscene (src/AirTravel.js): centred, no tile name.
PICTURES = {'plane-interior': plane_interior, 'plane-sky': plane_sky}


def main():
    built = {}
    for key, (fn, _) in SPRITES.items():
        im = fn()
        built[key] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    for key, im in river_tiles().items():        # recoloured from sprites that are already 2x
        built[key] = im
    for key, im in built.items():
        im.save(f'assets/sprites/{key}.png')
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    pictures = {}
    for key, fn in PICTURES.items():
        im = fn()
        pictures[key] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        pictures[key].save(f'assets/sprites/{key}.png')
        print(f'{key}: {pictures[key].width}x{pictures[key].height}px')

    cfg = json.load(open('config.json'))
    for key, im in built.items():
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if key in FLAT:
            cfg['spriteMetadata'][key]['depthBias'] = FLAT[key]
        cfg.setdefault('tileNames', {})[key] = SPRITES[key][1] if key in SPRITES else 'sfb-river'
    for key in pictures:
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 0.5, 'anchorY': 0.5}
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        ims = list(built.values()) + list(pictures.values())
        rows, x, y, rowh, width = [], 16, 16, 0, 2000
        for im in ims:
            if x + im.width + 16 > width:
                x, y, rowh = 16, y + rowh + 16, 0
            rows.append((im, x, y))
            x += im.width + 16
            rowh = max(rowh, im.height)
        sheet = Image.new('RGBA', (width, y + rowh + 16), rgb('8fb07a'))
        for im, x, y in rows:
            sheet.alpha_composite(im, (x, y))
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
