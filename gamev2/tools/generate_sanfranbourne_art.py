#!/usr/bin/env python3
"""generate_sanfranbourne_art.py — draw the San Franbourne, airport and plane sprites (issue #218).

San Franbourne is the home city: Melbourne and San Francisco at once. No asset
pack has either, so everything is drawn here the way tools/generate_hokkaido.py
and tools/generate_fukuoka_art.py draw theirs: shaded pixel art in the
GuttyKreum palette, at half size (one drawn pixel = one pixel of a 32px tile)
and pixel-doubled, with a 1px ink outline. No brand marks.

The transport, sports, terrain and creature sprites (the cable car to the rock,
and the leaners) are in the house look (docs/generators-and-checks.md, "House
look: GuttyKreum", #328): sheet colours only, roofs seen from above, dark glass
and the palm's fronds by generate_sendai_art's `pane` and `foliage`, lamps unlit
in dim gold. The oval, the pier, the rail and the fog are flat on purpose.

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
from generate_sendai_art import foliage, pane, speck, ground_shade, P_SHADE, LEAF as P_LEAF

C = 32
ORANGE, ORANGE_HI, ORANGE_LO = rgb('c8452c'), rgb('e8674a'), rgb('8e2d20')      # the bridge
MUSTARD, MUSTARD_HI, MUSTARD_LO = rgb('e0b040'), rgb('f2d070'), rgb('b07c2c')   # the station
MAROON = rgb('8a3a34')
COPPER, COPPER_HI, COPPER_LO = rgb('5fa58a'), rgb('8fd0b0'), rgb('3c7462')
TRAM, TRAM_LO = rgb('3f7a4c'), rgb('2a5637')
BLUESTONE, BLUESTONE_LO, BLUESTONE_HI = rgb('5c6272'), rgb('444959'), rgb('777e8e')
BROWN, BROWN_HI, BROWN_LO = rgb('8a6a48'), rgb('a88560'), rgb('64492f')
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


# ---- transport, sports, terrain and creatures: the house look (#328) ----
# Drawn the way tools/generate_sendai_art.py draws its trees and pub: GuttyKreum
# sheet colours only, rectangles, points and integer maths, light from the upper
# left, roofs seen from above, dark glass with a slanted glare (`pane`), lamps
# unlit in the pack's dim gold. The oval, the pier, the rail and the fog are flat
# in function and stay flat in drawing: textured, no outline.
P_NAVY = rgb('172459')
P_W, P_W1, P_S2, P_S3, P_S4, P_S5, P_S6 = (rgb(c) for c in (
    'fafcfd', 'dae2e4', 'a4b0b5', '848295', '575f79', '47485d', '2a2636'))
P_ROCK_TOP, P_COAL = rgb('bcc7cc'), rgb('191c2a')
P_CREAM, P_CREAM_LO, P_CREAM_DK = rgb('e4cecc'), rgb('be9e8c'), rgb('8e7366')
P_RED_HI, P_RED, P_RED_LO, P_RED_DK, P_BLUSH = (rgb(c) for c in ('d16b56', 'aa4d31', '904a37', '8a3a22', 'e78d7b'))
P_GOLD_HI, P_GOLD, P_GOLD_LO, P_GOLD_DK = rgb('f3d890'), rgb('c6a663'), rgb('a7843b'), rgb('86624f')
P_G_HI, P_G1, P_G, P_G_LO, P_G_DK = (rgb(c) for c in ('93c297', '83af6f', '678e57', '508582', '395050'))
P_WOOD_HI, P_WOOD, P_WOOD_LO, P_WOOD_DK, P_WOOD_DKR = (rgb(c) for c in ('be9e8c', 'bb8971', 'a68777', '86624f', '594b45'))
P_FUR_HI, P_FUR, P_FUR_LO = rgb('a68777'), rgb('7f513b'), rgb('594b45')
P_GLASS, P_GLASS_LO, P_GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
P_BLUE_HI, P_BLUE = rgb('425faa'), rgb('314b8e')
P_JOINT = rgb('413f53')                  # a colour of road-plain
P_SKIN, P_SKIN_LO = rgb('ffe2e0'), rgb('d7b6ab')
P_FOG = (rgb('dae2e4', 70), rgb('dae2e4', 110), rgb('fafcfd', 150))


def R(d, x0, y0, x1, y1, c):
    d.rectangle([x0, y0, x1, y1], fill=c)


def disc(d, x, y, n, c):
    """An n x n round, by rows (n is 6 or 8)."""
    for row, inset in enumerate((2, 1, 0, 0, 1, 2) if n == 6 else (2, 1, 0, 0, 0, 0, 1, 2)):
        R(d, x + inset, y + row, x + n - 1 - inset, y + row, c)


def lump(im, cx, cy, rx, ry, base, hi, lo):
    """A smooth body, lit on its upper left, dark underneath."""
    px = im.load()
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < im.width and 0 <= y < im.height):
                continue
            dx, dy = (x - cx) * 1000 // rx, (y - cy) * 1000 // ry
            if dx * dx + dy * dy > 1000000:
                continue
            t = dy * 55 // 100 + dx * 30 // 100
            px[x, y] = hi if t < -330 else lo if t > 300 else base


def cast(im, boxes):
    """The shadow on the ground, only where nothing is drawn (after the outline)."""
    px = im.load()
    for x0, y0, x1, y1 in boxes:
        for y in range(max(0, y0), min(im.height - 1, y1) + 1):
            for x in range(max(0, x0), min(im.width - 1, x1) + 1):
                if px[x, y][3] == 0:
                    px[x, y] = P_SHADE


def edge_cols(im, x, swap):
    """Recolour one column by `swap` (a lit or shaded end)."""
    px = im.load()
    for y in range(im.height):
        if px[x, y] in swap:
            px[x, y] = swap[px[x, y]]


def wheels(d, xs, y):
    for x in xs:
        disc(d, x, y, 8, P_S6)
        R(d, x + 3, y + 3, x + 4, y + 4, P_S3)
        d.point((x + 2, y + 2), fill=P_S4)


def cable_car():
    im, d = canvas(3, 2)                 # 96 x 64
    # the open ends: dark under the roof, a bench, a red dash, three posts
    for x0 in (6, 66):
        R(d, x0, 20, x0 + 23, 45, P_S6)
        R(d, x0, 29, x0 + 23, 35, P_WOOD_DK); R(d, x0, 29, x0 + 23, 29, P_WOOD)
        R(d, x0, 36, x0 + 23, 39, P_WOOD); R(d, x0, 36, x0 + 23, 36, P_WOOD_HI)
        R(d, x0, 40, x0 + 23, 45, P_RED); R(d, x0, 40, x0 + 23, 40, P_RED_HI); R(d, x0, 45, x0 + 23, 45, P_RED_LO)
        for x in (x0, x0 + 11, x0 + 22):
            R(d, x, 20, x, 45, P_CREAM); R(d, x + 1, 20, x + 1, 45, P_CREAM_LO)
        R(d, x0, 20, x0 + 23, 20, INK)
    # the closed middle: red, a cream window frame, three dark panes, a gold band
    R(d, 30, 20, 65, 45, P_RED)
    R(d, 30, 20, 30, 45, P_RED_HI); R(d, 65, 20, 65, 45, P_RED_DK)
    R(d, 33, 23, 62, 37, P_CREAM); R(d, 62, 23, 62, 37, P_CREAM_LO); R(d, 33, 37, 62, 37, P_CREAM_LO)
    for x in (34, 44, 54):
        pane(d, x, 24, x + 7, 36)
    R(d, 31, 40, 64, 43, P_GOLD); R(d, 31, 40, 64, 40, P_GOLD_HI); R(d, 31, 43, 64, 43, P_GOLD_LO)
    for x in range(35, 61, 4):
        R(d, x, 41, x + 1, 42, P_GOLD_DK)
    R(d, 30, 20, 65, 20, P_RED_DK)       # the eave's shadow
    # the roof seen from above: the deck, the clerestory with its vents, the bell
    R(d, 6, 13, 89, 19, P_CREAM); R(d, 6, 13, 89, 13, P_W)
    R(d, 6, 18, 89, 18, P_CREAM_LO); R(d, 6, 19, 89, 19, P_CREAM_DK)
    R(d, 14, 7, 81, 10, P_W); R(d, 14, 11, 81, 12, P_CREAM_LO)
    for x in range(17, 79, 8):
        R(d, x, 11, x + 3, 12, P_CREAM_DK)
    disc(d, 45, 2, 6, P_GOLD)
    R(d, 46, 3, 47, 3, P_GOLD_HI); d.point((46, 4), fill=P_GOLD_HI); R(d, 47, 7, 48, 7, P_GOLD_LO)
    # the running board, the frame, the wheels
    R(d, 4, 46, 91, 51, P_RED_LO); R(d, 4, 46, 91, 46, P_RED); R(d, 4, 51, 91, 51, P_RED_DK)
    R(d, 4, 52, 91, 54, P_WOOD_DKR)
    wheels(d, (16, 70), 54)
    outline(im)
    cast(im, [(6, 61, 89, 63)])
    return im


def tram():
    im, d = canvas(4, 2)                 # 128 x 64, facing west
    # the body: cream over green, a gold band and pinstripe
    R(d, 4, 14, 123, 29, P_CREAM); R(d, 4, 14, 123, 14, P_CREAM_LO); R(d, 4, 29, 123, 29, P_CREAM_LO)
    for x in range(10, 118, 13):
        if 55 <= x <= 68:
            continue
        pane(d, x, 17, x + 9, 27)
    R(d, 4, 30, 123, 33, P_GOLD); R(d, 4, 30, 123, 30, P_GOLD_HI); R(d, 4, 33, 123, 33, P_GOLD_LO)
    R(d, 4, 34, 123, 49, P_G); R(d, 4, 34, 123, 34, P_G1); R(d, 4, 44, 123, 49, P_G_LO)
    for x in range(4, 124, 2):
        d.point((x, 43), fill=P_G_LO)
    R(d, 4, 39, 123, 39, P_GOLD)
    R(d, 4, 50, 123, 50, P_G_LO); R(d, 4, 51, 123, 52, P_G_DK); R(d, 4, 53, 123, 54, P_S6)
    # the centre doors
    R(d, 57, 15, 71, 53, P_G_LO); R(d, 71, 15, 71, 53, P_G_DK)
    pane(d, 59, 18, 63, 49); pane(d, 65, 18, 69, 49)
    # the lamps, unlit (AmbientTrams adds the halos at night)
    R(d, 6, 36, 9, 39, P_GOLD); d.point((6, 36), fill=P_GOLD_HI); d.point((7, 36), fill=P_GOLD_HI)
    R(d, 6, 39, 9, 39, P_GOLD_LO)
    R(d, 118, 36, 121, 39, P_RED); d.point((118, 36), fill=P_RED_HI); R(d, 118, 39, 121, 39, P_RED_DK)
    edge_cols(im, 4, {P_CREAM: P_W, P_CREAM_LO: P_CREAM, P_GOLD: P_GOLD_HI, P_GOLD_LO: P_GOLD,
                      P_G: P_G1, P_G1: P_G_HI, P_G_LO: P_G, P_G_DK: P_G_LO, P_S6: P_S5})
    edge_cols(im, 123, {P_CREAM: P_CREAM_LO, P_GOLD_HI: P_GOLD, P_GOLD: P_GOLD_LO,
                        P_G1: P_G, P_G: P_G_LO, P_G_LO: P_G_DK, P_G_DK: P_S6})
    # the roof seen from above, ribbed, the pole lying along it
    R(d, 8, 5, 119, 13, P_S2); R(d, 8, 5, 119, 5, P_W1)
    for x in range(18, 119, 10):
        R(d, x, 6, x, 11, P_S3)
    R(d, 8, 12, 119, 12, P_S3); R(d, 8, 13, 119, 13, P_S4)
    R(d, 60, 7, 67, 9, P_S4); R(d, 60, 7, 67, 7, P_S3)
    R(d, 68, 8, 104, 8, P_S6); R(d, 103, 7, 105, 9, P_S6)
    px = im.load()
    for x, y in ((8, 5), (119, 5), (4, 14), (123, 14), (4, 54), (123, 54)):
        px[x, y] = CLEAR
    wheels(d, (18, 34, 86, 102), 54)
    outline(im)
    cast(im, [(6, 61, 121, 63)])
    return im


def rail():
    """Two rails and the cable slot between them, across a road tile (flat, no outline)."""
    im, d = canvas(1, 1)
    for y in (5, 23):
        R(d, 0, y, 31, y, P_S2); R(d, 0, y + 1, 31, y + 1, P_S6); R(d, 0, y + 2, 31, y + 2, P_S4)
    R(d, 0, 14, 31, 14, P_S3); R(d, 0, 15, 31, 15, INK); R(d, 0, 16, 31, 16, P_S5)
    for x in (7, 23):
        R(d, x, 8, x, 13, P_JOINT); R(d, x, 17, x, 22, P_JOINT)
    return im


def oval():
    im, d = canvas(12, 7)                # 384 x 224, flat: no outline

    def inside(x, y, a, b, cx2=383):
        return (2 * x - cx2) ** 2 * b * b + (2 * y - 223) ** 2 * a * a <= a * a * b * b

    A, B = 375, 211
    lighter = {P_G1: P_G_HI, P_G: P_G1}
    darker = {P_G1: P_G, P_G: P_G_LO}
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if not inside(x, y, A, B):
                continue
            if not inside(x, y, A - 10, B - 10):
                px[x, y] = P_G                       # meets the grass tile without an edge
                continue
            if not inside(x, y, A - 15, B - 15):
                px[x, y] = P_W                       # the boundary line
                continue
            r2 = (2 * x - 383) ** 2 + (2 * y - 223) ** 2
            if (37 * 37 < r2 <= 41 * 41 or (191 <= x <= 192 and 93 <= y <= 130)
                    or (x in (168, 215) and 88 <= y <= 135) or (y in (88, 135) and 168 <= x <= 215)
                    or any((x in (x0, x1) and 96 <= y <= 127) or (y in (96, 127) and x0 <= x <= x1)
                           for x0, x1 in ((10, 33), (350, 373)))
                    or any(inside(x, y, 220, 179, c) and not inside(x, y, 216, 175, c) for c in (19, 747))):
                px[x, y] = P_W
                continue
            c = P_G1 if (x // 16) % 2 else P_G       # mown stripes, with tufts
            s = speck(x // 2, y, 7)
            px[x, y] = lighter[c] if s < 3 else darker[c] if s > 96 else c
    return im


def goalposts():
    im, d = canvas(2, 3)                 # 64 x 96: two tall posts between two short ones
    for x, top in ((8, 44), (24, 6), (38, 6), (54, 44)):
        R(d, x, top, x + 2, 92, P_W); R(d, x + 2, top, x + 2, 92, P_S2)
        base, hi, lo = (P_RED, P_RED_HI, P_RED_DK) if top < 20 else (P_BLUE, P_BLUE_HI, P_NAVY)
        R(d, x - 1, 74, x + 3, 92, base)
        R(d, x - 1, 74, x + 3, 74, hi); R(d, x - 1, 74, x - 1, 91, hi)
        R(d, x - 1, 92, x + 3, 92, lo); R(d, x + 3, 75, x + 3, 92, lo)
    outline(im)
    cast(im, [(x, 93, x + 8, 95) for x in (8, 24, 38, 54)])
    return im


def light_tower():
    im, d = canvas(1, 5)                 # 32 x 160
    R(d, 14, 30, 17, 156, P_S3); R(d, 14, 30, 14, 156, P_W1); R(d, 17, 30, 17, 156, P_S4)
    for y in range(44, 150, 14):
        R(d, 13, y, 18, y, P_S5)
    R(d, 3, 6, 28, 30, P_S4)
    R(d, 3, 6, 28, 6, P_S2); R(d, 3, 6, 3, 30, P_S2)
    R(d, 4, 30, 28, 30, P_S5); R(d, 28, 7, 28, 30, P_S5)
    for y in (9, 16, 23):                # the lamps, unlit: DayNight lights a lamp-post
        for x in (6, 12, 18, 24):
            R(d, x, y, x + 2, y + 4, P_GOLD); d.point((x, y), fill=P_GOLD_HI); R(d, x, y + 4, x + 2, y + 4, P_GOLD_LO)
    R(d, 10, 152, 21, 157, P_S5); R(d, 10, 152, 21, 152, P_S4)
    outline(im)
    cast(im, [(10, 158, 24, 159)])
    return im


def fog(kind):
    """A bank of fog: ragged lumps, flat underneath, see-through, no outline."""
    im, d = canvas(5, 2)                 # 160 x 64
    lumps = ([(18, 30, 26), (48, 22, 30), (86, 30, 34), (122, 26, 28), (144, 36, 18)] if kind == 'a' else
             [(14, 36, 16), (40, 30, 26), (76, 24, 30), (108, 32, 30), (140, 28, 22)])
    seed = 1 if kind == 'a' else 2
    px = im.load()
    for colour, grow in zip(P_FOG, (6, 0, -8)):     # each layer replaces the one under it
        for n, (cx, cy, r) in enumerate(lumps):
            rx = r + grow
            up, down = rx * 55 // 100, rx * 35 // 100
            if rx <= 2 or down < 1:
                continue
            for y in range(max(0, cy - up - 1), min(im.height, cy + down + 2)):
                for x in range(max(0, cx - rx - 1), min(im.width, cx + rx + 2)):
                    dx, dy = (x - cx) * 1000 // rx, (y - cy) * 1000 // (up if y < cy else down)
                    if dx * dx + dy * dy <= 1000 * (820 + speck(x // 2, y // 2, seed + n) * 3):
                        px[x, y] = colour
    return im


def terminal():
    im, d = canvas(9, 5)                 # 288 x 160
    px = im.load()
    # the hall: one wall of dark glass, its glare running across, mullions and a transom over it
    R(d, 40, 78, 283, 157, P_S5)
    pane(d, 44, 82, 281, 148, 31)
    for x in range(58, 280, 14):
        R(d, x, 82, x + 1, 148, P_S5)
    R(d, 44, 113, 281, 114, P_S5)
    R(d, 40, 150, 283, 157, P_S3); R(d, 40, 150, 283, 150, P_S2)
    # the roof seen from above: a white wave, banded in the light, with standing seams
    darker = {P_W: P_W1, P_W1: P_S2, P_S2: P_S3}
    for x in range(36, 288):
        t = (x - 36) % 100
        h = 24 * t * (50 - t) // 2500 if t < 50 else -(24 * (t - 50) * (100 - t) // 2500)
        c = P_W if t < 25 else P_W1 if t < 50 else P_S2 if t < 75 else P_W1
        if (x - 42) % 14 == 0:
            c = darker[c]
        R(d, x, 58 - h, x, 75, c)
        px[x, 58 - h] = P_W
    R(d, 36, 76, 287, 79, P_S2); R(d, 36, 76, 287, 76, P_W1); R(d, 36, 79, 287, 79, P_S3)
    R(d, 40, 80, 283, 81, P_GLASS_LO)    # the fascia's shadow on the glass
    # the doors, dark, and the sign over them: a plane, wheels down
    R(d, 126, 106, 193, 157, P_S5)
    for x0, x1 in ((130, 143), (145, 158), (161, 174), (176, 189)):
        pane(d, x0, 116, x1, 157)
    R(d, 122, 92, 197, 106, P_NAVY); R(d, 122, 92, 197, 92, P_BLUE); R(d, 122, 92, 122, 106, P_BLUE)
    plane_icon(d, 160, 99, P_W)
    # the control tower, at the west end
    R(d, 12, 44, 30, 157, P_CREAM); R(d, 12, 44, 13, 157, P_W)
    R(d, 27, 44, 29, 157, P_CREAM_LO); R(d, 30, 44, 30, 157, P_CREAM_DK)
    for y in range(54, 150, 16):
        R(d, 18, y, 24, y + 6, P_GLASS); R(d, 18, y, 24, y, P_GLASS_LO)
        d.point((20, y + 4), fill=P_GLARE); d.point((21, y + 3), fill=P_GLARE)
    for y in range(18, 41):              # the cab: dark glass, splaying out to the gallery
        x0, x1 = 8 - (y - 18) * 6 // 22, 34 + (y - 18) * 6 // 22
        for x in range(x0, x1 + 1):
            px[x, y] = P_GLASS_LO if y < 20 else P_GLARE if (x + y) % 13 == 0 else P_GLASS
        for k in (1, 2, 3):
            px[x0 + (x1 - x0) * k // 4, y] = P_NAVY
    R(d, 6, 12, 36, 17, P_W1); R(d, 6, 12, 36, 12, P_W); R(d, 6, 17, 36, 17, P_S2)
    R(d, 2, 40, 40, 43, P_W1); R(d, 2, 40, 40, 40, P_W); R(d, 2, 43, 40, 43, P_S2)
    R(d, 21, 0, 21, 11, P_S4); px[21, 0] = P_RED_HI
    outline(im)
    cast(im, [(12, 158, 285, 159)])
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
    im, d = canvas(4, 9)                 # 128 x 288, flat: no outline
    for x0 in range(2, 126, 10):         # planks laid along the pier, butt joints staggered
        R(d, x0, 0, min(x0 + 9, 125), 283, P_WOOD if (x0 // 10) % 2 == 0 else P_WOOD_LO)
        R(d, x0, 0, x0, 283, P_WOOD_DK)
        for y in range((x0 * 7) % 40, 284, 40):
            R(d, x0, y, min(x0 + 9, 125), y, P_WOOD_DK)
            d.point((x0 + 2, y + 1), fill=P_WOOD_DKR); d.point((x0 + 7, y + 1), fill=P_WOOD_DKR)
    R(d, 2, 0, 5, 283, P_WOOD_DK); R(d, 2, 0, 2, 283, P_WOOD_HI)
    R(d, 122, 0, 125, 283, P_WOOD_DKR); R(d, 2, 280, 125, 283, P_WOOD_DKR)
    for y in range(8, 284, 44):          # bollards and the rope between them
        for x in (1, 120):
            R(d, x, y, x + 6, y + 8, P_WOOD_DKR); R(d, x + 1, y, x + 5, y + 2, P_WOOD_LO)
            R(d, x + 1, y, x + 5, y, P_CREAM); R(d, x + 6, y, x + 6, y + 8, INK)
    for x in (4, 123):
        for y in range(8, 240, 4):
            d.point((x, y + 10), fill=P_CREAM)
    R(d, 2, 284, 125, 287, P_SHADE); R(d, 126, 4, 127, 287, P_SHADE)    # its shadow on the water
    return im


def sea_lions():
    im, d = canvas(3, 2)                 # 96 x 64: a raft low in the water
    for x0 in range(4, 92, 11):
        R(d, x0, 34, min(x0 + 10, 91), 51, P_WOOD if (x0 // 11) % 2 == 0 else P_WOOD_LO)
        R(d, x0, 52, min(x0 + 10, 91), 58, P_WOOD_DKR); R(d, x0, 52, x0, 58, P_S6)
    R(d, 4, 34, 91, 34, P_WOOD_HI)
    for x0, y0, flip in ((8, 30, 1), (36, 34, -1), (60, 28, 1)):         # three lying down
        if flip > 0:
            R(d, x0 - 3, y0 + 9, x0, y0 + 11, P_FUR_LO); R(d, x0 + 16, y0 + 11, x0 + 19, y0 + 12, P_FUR_LO)
        else:
            R(d, x0 + 26, y0 + 9, x0 + 29, y0 + 11, P_FUR_LO); R(d, x0 + 7, y0 + 11, x0 + 10, y0 + 12, P_FUR_LO)
        lump(im, x0 + 13, y0 + 6, 13, 6, P_FUR, P_FUR_HI, P_FUR_LO)
        hx = x0 + (22 if flip > 0 else -2)
        lump(im, hx + 4, y0, 5, 4, P_FUR, P_FUR_HI, P_FUR_LO)
        d.point((hx + (6 if flip > 0 else 2), y0 - 1), fill=INK)
        d.point((hx + (9 if flip > 0 else -1), y0 + 1), fill=INK)
    for y in range(12, 33):              # one sitting up, barking: the neck by rows
        xl = 44 + (32 - y) * 4 // 20
        R(d, xl, y, xl + 9, y, P_FUR); R(d, xl, y, xl + 1, y, P_FUR_HI); d.point((xl + 9, y), fill=P_FUR_LO)
    lump(im, 53, 9, 5, 4, P_FUR, P_FUR_HI, P_FUR_LO)
    R(d, 57, 10, 59, 12, P_FUR_HI); d.point((59, 10), fill=INK); d.point((54, 8), fill=INK)
    for x, y in ((64, 4), (67, 7), (64, 10)):
        R(d, x, y, x + 2, y, P_W)
    outline(im)
    for x in range(2, 94, 5):            # ripples round the raft
        d.point((x, 61), fill=P_W)
    cast(im, [(4, 60, 91, 60), (4, 62, 91, 62)])
    return im


WOOD_HI = rgb('d2a58c')


# ---- the leaners: street colour on the pavements (tools/generate_sanfranbourne.py LEANERS) ----
# Each is a person in the cast's proportions (a big head, a small body, the same
# inked edge) standing folded double at the waist: legs straight, the back a hump
# over the hips, the head hanging at knee height, one arm straight down. Drawn
# facing left; `flip` mirrors. One look per letter, told apart by clothes.
LEAN_LOOKS = {
    #    top (fill, lit, shaded)            legs (near, far)      shoes        hair        extras
    'a': dict(top=(P_RED, P_RED_HI, P_RED_DK), legs=(P_BLUE, P_NAVY), shoes=P_CREAM,
              hair=P_WOOD_DKR, hood=True),                                           # red hoodie, hood up
    'b': dict(top=(P_WOOD_DK, P_WOOD, P_WOOD_DKR), legs=(P_S5, P_S6), shoes=P_S6,
              hair=P_S6, beanie=(P_RED_HI, P_RED), flip=True),                         # brown jacket, red beanie
    'c': dict(top=(P_G, P_G1, P_G_LO), legs=(P_CREAM_DK, P_WOOD_DKR), shoes=P_RED_LO,
              hair=P_GOLD, pack=(P_BLUE, P_BLUE_HI, P_GOLD_HI)),                       # green parka, backpack
    'd': dict(top=(P_S6, P_S5, P_COAL), legs=(P_S3, P_S4), shoes=P_W1,
              hair=P_FUR, cap=(P_GOLD, P_GOLD_LO), cup=True, flip=True),             # black puffer, cap, a cup
}


def leaner(kind):
    look = LEAN_LOOKS[kind]
    im, _ = canvas(1, 1)
    top, top_hi, top_lo = look['top']
    legs, legs_lo = look['legs']

    def part(draw):
        """One inked piece laid over what is there (the cast's bodies are inked piece by piece)."""
        layer, d = canvas(1, 1)
        draw(d)
        outline(layer)
        im.alpha_composite(layer)

    def far_leg(d):
        d.rectangle([22, 12, 24, 26], fill=legs_lo)
        d.rectangle([20, 26, 24, 27], fill=look['shoes'])

    def near_leg(d):
        d.polygon([(19, 10), (25, 10), (25, 13), (22, 15), (22, 26), (19, 26)], fill=legs)   # the seat, the leg
        d.rectangle([22, 15, 22, 25], fill=legs_lo)
        d.rectangle([17, 26, 22, 27], fill=look['shoes'])

    def head(d):
        # a cast-sized head hanging crown-down off the shoulders, the face turned to the knees
        d.rectangle([2, 15, 9, 25], fill=P_SKIN); d.rectangle([1, 16, 10, 24], fill=P_SKIN)
        d.rectangle([5, 20, 9, 20], fill=P_SKIN_LO)
        if look.get('hood'):
            d.rectangle([1, 16, 3, 24], fill=top); d.rectangle([2, 22, 9, 25], fill=top); d.rectangle([2, 15, 4, 15], fill=top)
            d.line([(1, 17), (1, 23)], fill=top_hi); d.line([(4, 16), (4, 21)], fill=top_lo); d.line([(4, 21), (10, 21)], fill=top_lo)
        else:
            d.rectangle([1, 16, 4, 24], fill=look['hair']); d.rectangle([2, 21, 9, 25], fill=look['hair'])
            d.rectangle([2, 15, 4, 15], fill=look['hair']); d.rectangle([5, 20, 6, 20], fill=look['hair'])
        if look.get('beanie'):
            beanie, band = look['beanie']
            d.rectangle([1, 21, 10, 24], fill=beanie); d.rectangle([2, 25, 9, 26], fill=beanie)
            d.line([(1, 21), (10, 21)], fill=band)
        if look.get('cap'):
            cap, cap_lo = look['cap']
            d.rectangle([1, 22, 10, 24], fill=cap); d.rectangle([2, 25, 9, 25], fill=cap)
            d.rectangle([10, 23, 13, 24], fill=cap); d.line([(1, 24), (13, 24)], fill=cap_lo)
        d.line([(7, 19), (8, 19)], fill=INK)                      # an eye, shut
        d.point((9, 17), fill=P_BLUSH)

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
        d.rectangle([11, 24, 13, 26], fill=P_SKIN)
        if look.get('cup'):
            d.rectangle([11, 26, 14, 29], fill=P_W); d.line([(11, 27), (14, 27)], fill=P_RED_HI)

    for draw in (far_leg, near_leg, body) + ((pack,) if look.get('pack') else ()) + (head, near_arm):
        part(draw)
    cast(im, [(14, 29, 27, 30)])
    return im.transpose(Image.FLIP_LEFT_RIGHT) if look.get('flip') else im


def frond(im, x0, y0, side, reach, rise, droop, seed):
    """A palm frond: a rib that rises and droops, leaflets hanging from it, shaded down the ramp."""
    px = im.load()
    for t in range(reach + 1):
        x = x0 + side * t
        y = y0 - rise * t // reach + droop * t * t // (reach * reach)
        if not 0 <= x < im.width:
            continue
        ln = 3 + 28 * t * (reach - t) // (reach * reach) + speck(x, 0, seed) % 3 - (2 if x % 3 == 0 else 0)
        n = max(ln, 1)
        for k in range(n + 1):
            f = k * 100 // n
            c = (P_LEAF[1] if k == 0 else P_LEAF[2] if f < 40 else P_LEAF[3] if f < 70
                 else P_LEAF[4] if f < 95 else P_LEAF[5])
            if 0 <= y + k < im.height:
                px[x, y + k] = c
        if speck(x // 2, 1, seed) < 45 and y >= 1:
            px[x, y - 1] = P_LEAF[0]


def palm():
    im, d = canvas(3, 4)                 # 96 x 128, trunk in the middle cell
    ground_shade(d, 50, 120, 13)
    for y in range(40, 124):             # a leaning, ringed trunk
        t = y - 40
        x = 45 + 12 * t * (83 - t) // (83 * 83)
        R(d, x, y, x + 4, y, P_FUR_LO if t % 6 == 0 else P_FUR)
        if t % 6:
            d.point((x, y), fill=P_FUR_HI); d.point((x + 4, y), fill=P_FUR_LO)
    for side, reach, rise, droop, seed in ((-1, 30, 2, 30, 1), (1, 30, 2, 30, 2), (-1, 40, 10, 30, 3),
                                           (1, 40, 10, 30, 4), (-1, 34, 26, 22, 5), (1, 34, 26, 22, 6),
                                           (-1, 14, 30, 6, 7), (1, 12, 32, 6, 8)):
        frond(im, 47 if side < 0 else 48, 40, side, reach, rise, droop, seed)
    foliage(im, [(48, 39, 6, 4)], P_LEAF, 4)
    R(d, 44, 42, 46, 44, P_FUR_LO); R(d, 49, 42, 51, 44, P_FUR_LO)
    outline(im)
    return im


def rock():
    im, d = canvas(5, 3)                 # 160 x 96
    px = im.load()
    edge = [(6, 88), (14, 60), (40, 48), (70, 52), (104, 44), (136, 56), (154, 88)]
    for (xa, ya), (xb, yb) in zip(edge, edge[1:]):
        for x in range(xa, xb + 1):
            top = ya + (yb - ya) * (x - xa) // (xb - xa)
            for y in range(top, 89):
                depth = y - top + speck(x // 3, y // 2, 5) % 4 + (x - 80) // 30
                px[x, y] = (P_ROCK_TOP if depth < 4 else P_S2 if depth < 11 else P_S3 if depth < 21
                            else P_S4 if depth < 31 else P_S5)
    for x in range(16, 150, 9):          # clefts
        for k in range(6):
            px[x + k // 3, 70 + x % 4 + k] = P_S5
    # the cell block: a flat roof seen from above, a cream wall, dark windows
    R(d, 42, 28, 110, 35, P_S2); R(d, 42, 28, 110, 28, P_W1)
    R(d, 42, 34, 110, 34, P_S3); R(d, 42, 35, 110, 35, P_S4)
    for x in (54, 92):
        R(d, x, 30, x + 5, 32, P_S3); R(d, x, 30, x + 5, 30, P_S4)
    R(d, 44, 36, 108, 52, P_CREAM); R(d, 44, 36, 108, 36, P_CREAM_DK)
    R(d, 44, 37, 44, 52, P_W); R(d, 108, 37, 108, 52, P_CREAM_LO); R(d, 45, 52, 108, 52, P_CREAM_LO)
    for i in range(8):
        x = 49 + i * 7
        R(d, x, 40, x + 3, 47, P_GLASS); R(d, x, 40, x + 3, 40, P_GLASS_LO)
        d.point((x + 1, 45), fill=P_GLARE); d.point((x + 2, 44), fill=P_GLARE)
    foliage(im, [(26, 58, 8, 5), (89, 50, 7, 4), (140, 62, 6, 4)], P_LEAF, 2)
    # the lighthouse
    R(d, 120, 14, 127, 54, P_W); R(d, 125, 14, 126, 54, P_W1); R(d, 127, 14, 127, 54, P_S2)
    R(d, 120, 28, 127, 33, P_RED); R(d, 120, 28, 120, 33, P_RED_HI); R(d, 126, 28, 127, 33, P_RED_DK)
    R(d, 118, 13, 129, 14, P_S4)
    pane(d, 118, 8, 129, 12, 7)
    for i, y in enumerate(range(2, 8)):  # the cap, stepped, lit on its left
        R(d, 123 - i - 1, y, 124 + i + 1, y, P_RED); R(d, 123 - i - 1, y, 123, y, P_RED_HI)
    outline(im)
    for x in range(4, 158, 6):
        d.point((x, 91 + (x % 3)), fill=P_W)
    cast(im, [(6, 89, 154, 90)])
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
