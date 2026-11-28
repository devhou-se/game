#!/usr/bin/env python3
"""generate_sanfranbourne_art.py — draw the San Franbourne, airport and plane sprites (issue #218).

San Franbourne is the home city: Melbourne and San Francisco at once. No asset
pack has either, so everything is drawn here the way tools/generate_hokkaido.py
and tools/generate_fukuoka_art.py draw theirs: shaded pixel art in the
GuttyKreum palette, at half size (one drawn pixel = one pixel of a 32px tile)
and pixel-doubled, with a 1px ink outline. No brand marks.

The bridge, the station, the painted ladies, the lane and the two towers (#322)
are in the house look: only colours the GuttyKreum sheets use (the T_ palette),
roofs seen from above, the pack's dark glass with a slanted glare
(generate_sendai_art.pane), gold only as the pack's unlit c6a663, and integer
drawing only, so they come out the same on any Pillow.

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

from generate_hokkaido import (rgb, canvas, outline, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK, WHITE,
                               GLASS, GLASS_HI, GLASS_DK, WOOD, WOOD_LO, WOOD_DK,
                               STONE, STONE_LO, STONE_DK, GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_sendai_art import foliage, pane, speck, ground_shade, P_SHADE, LEAF as P_LEAF

C = 32
MUSTARD = rgb('e0b040')
MAROON = rgb('8a3a34')
LEAF, LEAF_HI, LEAF_LO = rgb('678e57'), rgb('89af78'), rgb('395050')
TURF, TURF_HI = rgb('6f9a55'), rgb('82ad63')
COPPER, COPPER_HI, COPPER_LO = rgb('5fa58a'), rgb('8fd0b0'), rgb('3c7462')
TRAM, TRAM_LO = rgb('3f7a4c'), rgb('2a5637')
BROWN, BROWN_HI, BROWN_LO = rgb('8a6a48'), rgb('a88560'), rgb('64492f')
SKIN = rgb('e8b898')
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


# ------------------------------------------------------------------------------ the city
# The bridge, the station, the painted ladies, the lane and the two towers (#322), in the house look:
# only colours the GuttyKreum sheets use, an ink silhouette, light from the upper left, roofs seen
# from above, the pack's dark glass (generate_sendai_art.pane) and its gold only unlit. Integer
# drawing only (rectangles and points), so the output is the same on any Pillow.
T_STEEL = [rgb(c) for c in ('fafcfd', 'dae2e4', 'a4b0b5', '848295', '575f79', '47485d', '2a2636')]
T_MUSTARD = [rgb(c) for c in ('f3d890', 'e3c587', 'c6a663', 'a7843b', '86624f')]
T_MAROON = [rgb(c) for c in ('aa4d31', '904a37', '5b283b')]
T_COPPER = [rgb(c) for c in ('b1dfdc', '93c297', '508582', '4a6262', '395050')]
T_SLATE = [rgb(c) for c in ('698592', '5b6c79', '444f5e')]
T_STONE = [rgb(c) for c in ('78768a', '5f6177', '47485d')]
T_ORANGE = [rgb(c) for c in ('db785c', 'c66347', 'aa4d31', '8a3a22')]
T_WOOD = [rgb(c) for c in ('be9e8c', 'bb8971', '86624f', '7f513b', '594b45')]
T_CREAM = [rgb(c) for c in ('e4cecc', 'be9e8c', '8e7366')]
T_GLASS, T_GLASS_LO, T_GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
T_BLUE = [rgb(c) for c in ('bbe9ff', '8ec2fa', '7db9fa', '588cc6', '425faa', '314b8e')]
T_PINK = [rgb(c) for c in ('ffe2e0', 'ff9b92', 'e78d7b', 'bb6479')]
T_SKIN, T_SKIN_LO = rgb('ffe2e0'), rgb('d7b6ab')
T_RED = [rgb(c) for c in ('e78d7b', 'd16b56', 'aa4d31')]
T_PURPLE = [rgb(c) for c in ('8f72b6', '3c396d')]
T_TEAL = [rgb(c) for c in ('508582', '3f827f', '395050')]
T_SAGE = [rgb(c) for c in ('6c8e7f', '506b6b')]
T_SHADE = rgb('2a3151', 90)


def R(d, x0, y0, x1, y1, c):
    if x0 <= x1 and y0 <= y1:            # an empty span draws nothing
        d.rectangle([x0, y0, x1, y1], fill=c)


def seg(d, x0, y0, x1, y1, c, w=1):
    """A slanted line a point at a time, w px wide along x."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = x0 + ((x1 - x0) * i * 2 + n) // (2 * n) if x1 >= x0 else x0 - ((x0 - x1) * i * 2 + n) // (2 * n)
        y = y0 + ((y1 - y0) * i * 2 + n) // (2 * n) if y1 >= y0 else y0 - ((y0 - y1) * i * 2 + n) // (2 * n)
        d.rectangle([x, y, x + w - 1, y], fill=c)


def arc_w(rx, ry, t):
    """The half-width of an ellipse t rows from its centre line."""
    t = min(abs(t), ry)
    return math.isqrt(rx * rx * (ry * ry - t * t)) // ry


def orb(d, cx, cy, r, c):
    """A disc, row by row."""
    for t in range(-r, r + 1):
        w = min(r, math.isqrt(r * r - t * t + r))
        R(d, cx - w, cy + t, cx + w, cy + t, c)


def cast(im, boxes):
    """The ground shade, on the pixels of each box still clear (after the outline)."""
    px = im.load()
    for x0, y0, x1, y1 in boxes:
        for y in range(max(0, y0), min(im.height - 1, y1) + 1):
            for x in range(max(0, x0), min(im.width - 1, x1) + 1):
                if px[x, y][3] == 0:
                    px[x, y] = T_SHADE


def pixmap(d, x0, y0, rows, colours):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colours:
                d.point((x0 + i, y0 + j), fill=colours[ch])


def courses(d, x0, y0, x1, y1, base, joint, hi=None, ch=6, cw=12):
    """Coursed brick or stone: a joint row at the foot of each full course, perpends every cw,
    shifted half a block on odd courses; with `hi`, a lit point right of each perpend on top."""
    R(d, x0, y0, x1, y1, base)
    for k, top in enumerate(range(y0, y1 + 1, ch)):
        foot = top + ch - 1
        if foot <= y1:
            R(d, x0, foot, x1, foot, joint)
        for x in range(x0 + cw - 1 - (cw // 2 if k % 2 else 0), x1 + 1, cw):
            R(d, x, top, x, min(foot - 1, y1), joint)
            if hi and x + 1 <= x1:
                d.point((x + 1, top), fill=hi)


def arch_pane(d, x0, y0, x1, y1, surround, step=7):
    """The pack's window with a round head."""
    pane(d, x0, y0, x1, y1, step)
    for k, n in enumerate((3, 2, 1)):
        R(d, x0, y0 + k, x0 + n - 1, y0 + k, surround)
        R(d, x1 - n + 1, y0 + k, x1, y0 + k, surround)


def band(d, x0, x1, y, shade):
    """A maroon string course and the row of shadow it casts."""
    for k, c in enumerate((T_MAROON[0], T_MAROON[1], T_MAROON[1], T_MAROON[2], shade)):
        R(d, x0, y + k, x1, y + k, c)


def clocks_station():
    im, d = canvas(12, 7)                # 384 x 224
    S, M, MA, CO, SL = T_STEEL, T_MUSTARD, T_MAROON, T_COPPER, T_SLATE
    # ---- the wings: a slate roof seen from above, hipped at the ends, ribbed, a steel ridge cap
    for y in range(80, 101):
        inset = max(0, (91 - y) * 10 // 12)
        R(d, 4 + inset, y, 379 - inset, y, SL[1])
        if y >= 84:
            for x in range(8 + inset - inset % 6, 376 - inset, 6):
                if 4 + inset < x < 379 - inset:
                    d.point((x, y), fill=CO[3])
                    if y < 100:
                        d.point((x + 1, y), fill=SL[0])
    R(d, 14, 80, 369, 80, S[2]); R(d, 14, 81, 369, 82, S[3])
    R(d, 4, 101, 379, 103, CO[3])
    # the wall: coursed brick, banded in maroon, the eave's shadow along its top
    courses(d, 4, 104, 379, 213, M[1], M[2])
    R(d, 4, 104, 379, 105, M[3])
    R(d, 4, 106, 5, 213, M[0]); R(d, 377, 106, 379, 213, M[3])
    for y in (126, 168, 206):
        band(d, 4, 379, y, M[3])
    for x in (14, 36, 58, 80, 102, 124, 256, 278, 300):
        for y0 in (134, 176):
            R(d, x - 1, y0 - 1, x + 12, y0 + 26, S[0])
            for k, n in enumerate((3, 2, 1)):          # the frame's round head
                R(d, x - 1, y0 - 1 + k, x - 2 + n, y0 - 1 + k, M[1])
                R(d, x + 13 - n, y0 - 1 + k, x + 12, y0 - 1 + k, M[1])
            arch_pane(d, x, y0, x + 11, y0 + 26, S[0])
            R(d, x + 5, y0 + 2, x + 6, y0 + 26, S[1])
            R(d, x + 12, y0 + 2, x + 12, y0 + 26, S[1])
            R(d, x - 2, y0 + 27, x + 13, y0 + 27, S[0]); R(d, x - 2, y0 + 28, x + 13, y0 + 28, S[1])
            R(d, x - 2, y0 + 29, x + 13, y0 + 29, M[3])
    R(d, 4, 214, 379, 221, S[3]); R(d, 4, 214, 379, 214, S[2]); R(d, 4, 220, 379, 221, S[4])
    # ---- the corner pavilion: a flat roof seen from above, a white cornice, piers, the great arch
    R(d, 144, 53, 239, 61, SL[1]); R(d, 144, 53, 239, 53, SL[0]); R(d, 144, 60, 239, 61, CO[3])
    R(d, 140, 62, 243, 65, S[0]); R(d, 140, 65, 243, 65, S[1])
    courses(d, 142, 66, 241, 213, M[1], M[2])
    R(d, 142, 66, 241, 67, M[3])
    for y in (84, 126, 206):
        band(d, 142, 241, y, M[3])
    for x0 in (142, 232):
        R(d, x0, 66, x0 + 9, 213, M[0])
        for y in range(73, 206, 8):
            R(d, x0, y, x0 + 8, y, M[2])
        R(d, x0 + 9, 66, x0 + 9, 213, M[3])
    R(d, 242, 80, 244, 103, CO[3]); R(d, 242, 104, 244, 213, M[3])     # its shade on the east wing
    for y in range(97, 214):             # the archivolt and its jambs
        w = arc_w(34, 47, 143 - y) if y < 143 else 34
        if w == 0:
            continue
        R(d, 192 - w, y, 191 + w, y, MA[1])
        d.point((192 - w, y), fill=MA[0]); d.point((191 + w, y), fill=MA[2])
        if y == 97 or (y < 143 and arc_w(34, 47, 144 - y) < w - 1):
            R(d, 192 - w, y, 191, y, MA[0])
    glass = set()
    for y in range(103, 144):            # the fanlight
        w = arc_w(29, 41, 143 - y)
        if w == 0:
            continue
        for x in range(192 - w, 192 + w):
            c = T_GLARE if (x + y) % 9 == 0 else T_GLASS
            if (x, y - 1) not in glass:
                c = T_GLASS_LO
            d.point((x, y), fill=c); glass.add((x, y))
    for dx, dy in ((-26, -10), (-21, -25), (-11, -35), (0, -40), (11, -35), (21, -25), (26, -10)):
        x0 = 191 if dx <= 0 else 192
        seg(d, x0, 143, x0 + dx, 143 + dy, M[2])
    seg(d, 192, 143, 192, 103, M[2])
    for t in range(0, 7):                # the hub
        w = math.isqrt(49 - t * t)
        R(d, 192 - w, 143 - t, 191 + w, 143 - t, M[2])
    R(d, 163, 144, 220, 146, M[1]); R(d, 163, 146, 220, 146, M[2])
    R(d, 163, 147, 220, 213, MA[2])
    # THE CLOCKS: a board of nine dials over the doors
    R(d, 160, 148, 223, 166, CO[4])
    R(d, 160, 148, 223, 148, CO[2]); R(d, 160, 148, 160, 166, CO[2])
    R(d, 160, 166, 223, 166, INK); R(d, 223, 148, 223, 166, INK)
    for i in range(9):
        cx = 165 + i * 6 + (i // 3) * 2
        orb(d, cx, 156, 2, S[0])
        d.point((cx, 156), fill=INK)
        d.point(((cx + 1, 156), (cx, 155), (cx - 1, 156))[i % 3], fill=INK)
        R(d, cx - 1, 162, cx + 1, 162, M[2])
    for x in (166, 184, 202):            # three doors
        R(d, x, 170, x + 14, 213, T_WOOD[4])
        R(d, x + 1, 171, x + 13, 213, T_WOOD[3])
        pane(d, x + 1, 172, x + 13, 190, 7)
        R(d, x + 7, 170, x + 7, 213, T_WOOD[4])
        for px0 in (x + 2, x + 9):
            R(d, px0, 194, px0 + 3, 210, T_WOOD[4]); R(d, px0 + 1, 195, px0 + 3, 210, T_WOOD[3])
        d.point((x + 6, 200), fill=M[2]); d.point((x + 8, 200), fill=M[2])
    R(d, 154, 214, 229, 217, S[2]); R(d, 154, 214, 229, 214, S[1]); R(d, 154, 217, 229, 217, S[3])
    R(d, 150, 218, 233, 221, S[2]); R(d, 150, 218, 233, 218, S[1]); R(d, 150, 221, 233, 221, S[3])
    # ---- the dome: a white drum with dark windows, eight copper gores lit from the west
    R(d, 160, 48, 223, 58, S[0]); R(d, 160, 58, 223, 58, S[1]); R(d, 222, 48, 223, 58, S[1])
    for x in range(164, 222, 8):
        R(d, x, 50, x + 3, 56, T_GLASS); R(d, x, 50, x + 3, 50, T_GLASS_LO); d.point((x, 53), fill=T_GLARE)
    R(d, 157, 45, 226, 47, S[2]); R(d, 157, 45, 226, 45, S[1]); R(d, 157, 47, 226, 47, S[3])
    for y in range(11, 45):
        w = arc_w(34, 34, 44 - y)
        for x in range(192 - w, 192 + w):
            r = (2 * x - 383) * 50 // w
            c = CO[2] if r < -90 else CO[1] if r < -34 else CO[2] if r < 34 else CO[3] if r < 90 else CO[4]
            d.point((x, y), fill=c)
        for f in (-90, -67, -34, 0, 34, 67, 90):
            d.point((191 + (f > 0) + (w * abs(f) // 100) * (1 if f > 0 else -1), y), fill=CO[4])
    R(d, 187, 3, 196, 11, CO[2]); R(d, 187, 3, 196, 3, CO[1]); R(d, 187, 3, 187, 11, CO[1])
    R(d, 195, 3, 196, 11, CO[4]); R(d, 190, 5, 193, 9, T_GLASS); R(d, 190, 5, 193, 5, T_GLASS_LO)
    R(d, 191, 0, 192, 2, M[2]); d.point((191, 0), fill=M[0])
    # ---- the clock tower at the east end
    courses(d, 330, 44, 368, 213, M[1], M[2])
    R(d, 330, 44, 331, 213, M[0]); R(d, 366, 44, 368, 213, M[3])
    for y in (84, 126, 168, 206):
        band(d, 330, 368, y, M[3])
    R(d, 369, 80, 371, 103, CO[3]); R(d, 369, 104, 371, 213, M[3])
    orb(d, 349, 63, 13, M[3]); orb(d, 349, 63, 12, INK); orb(d, 349, 63, 11, S[0])
    for t in range(-11, 12):
        for s in range(-11, 12):
            if s + t > 9 and s * s + t * t <= 121 + 11:
                d.point((349 + s, 63 + t), fill=S[1])
    for dx, dy in ((0, -9), (4, -8), (8, -4), (9, 0), (8, 4), (4, 8), (0, 9), (-4, 8), (-8, 4), (-9, 0),
                   (-8, -4), (-4, -8)):
        d.point((349 + dx, 63 + dy), fill=INK)
    seg(d, 349, 63, 349, 55, INK); seg(d, 349, 63, 355, 66, INK)
    for y in range(16, 42):
        w = (y - 16) * 23 // 25
        dark = (y - 16) % 4 == 3
        R(d, 349 - w, y, 349, y, CO[2] if dark else CO[1])
        R(d, 350, y, 350 + w, y, CO[3] if dark else CO[2])
    R(d, 325, 42, 374, 43, CO[2]); R(d, 325, 43, 374, 43, CO[4])
    R(d, 349, 6, 350, 15, M[2]); R(d, 348, 9, 351, 11, M[2]); d.point((348, 9), fill=M[0])
    for y0 in (96, 138, 178):
        R(d, 342, y0, 356, y0 + 20, MA[1])
        pane(d, 343, y0 + 1, 355, y0 + 19, 7)
        R(d, 349, y0 + 1, 349, y0 + 19, MA[1]); R(d, 343, y0 + 10, 355, y0 + 10, MA[1])
    outline(im)
    cast(im, [(3, 223, 380, 223)])
    return im


def bridge_tower():
    im, d = canvas(6, 7)                 # 192 x 224: legs in the outer cells, the deck between
    O, S = T_ORANGE, T_STEEL
    tiers = ((6, 6), (30, 4), (84, 2), (150, 0))

    def inset_at(y):
        return [i for y0, i in tiers if y0 <= y][-1]

    for x0 in (5, 167):
        # a leg, stepping in as it rises (art deco), lit from the west
        for y0, inset in tiers:
            a, b = x0 + inset, x0 + 19 - inset
            R(d, a, y0, b, 213, O[1])
            R(d, a, y0, a, 213, O[0]); R(d, a, y0, b, y0, O[0])
            R(d, b - 2, y0 + 1, b, 213, O[2])
        R(d, x0 + 8, 34, x0 + 11, 209, O[2]); R(d, x0 + 8, 34, x0 + 8, 209, O[3])
        for y in range(40, 210, 12):
            d.point((x0 + 10, y), fill=O[0])
            j = y + 6
            if j >= 84 and j <= 209:
                i = inset_at(j)
                R(d, x0 + i + 1, j, x0 + 7, j, O[2]); R(d, x0 + 12, j, x0 + 16 - i, j, O[3])
        R(d, x0 + 6, 3, x0 + 13, 5, O[1]); R(d, x0 + 6, 3, x0 + 13, 3, O[0])
        R(d, x0 - 3, 214, x0 + 22, 221, S[2]); R(d, x0 - 3, 214, x0 + 22, 214, S[1])
        R(d, x0 - 3, 220, x0 + 22, 221, S[3])
    # the portal beams: three, the lowest well clear of a walker's head
    for y0, h in ((14, 12), (56, 10), (98, 12)):
        R(d, 17, y0, 174, y0 + h, O[1]); R(d, 17, y0, 174, y0, O[0])
        R(d, 17, y0 + h - 1, 174, y0 + h, O[2])
        for x in range(26, 160, 16):
            R(d, x, y0 + 2, x + 11, y0 + h - 3, O[2])
            R(d, x, y0 + 2, x + 11, y0 + 2, O[3]); R(d, x, y0 + 2, x, y0 + h - 3, O[3])
            R(d, x + 2, y0 + 4, x + 10, y0 + h - 4, O[1]); R(d, x + 2, y0 + h - 4, x + 10, y0 + h - 4, O[0])
        for x0 in (5, 167):
            i = inset_at(y0 + h + 1)
            R(d, x0 + i, y0 + h + 1, x0 + 19 - i, y0 + h + 1, O[3])
    # the main cables, sweeping down and away from the tower tops
    for x0, dx in ((10, -1), (181, 1)):
        for i in range(2):
            pts = [(x0 + dx * t, 6 + i * 3 + t * t * 26 // 81) for t in range(11)]
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                seg(d, xa, ya, xb, yb, O[1] if i == 0 else O[2])
                seg(d, xa, ya + 1, xb, yb + 1, O[2] if i == 0 else O[3])
    outline(im)
    cast(im, [(2, 223, 27, 223), (164, 223, 189, 223)])
    return im


def bridge_cable(side):
    """One cell of the deck's edge: a red rail on the outer side, with the
    suspender cables rising from it. Flat by function: it tiles down the deck."""
    im, d = canvas(1, 1)
    O, S = T_ORANGE, T_STEEL
    x = 2 if side == 'w' else 27
    R(d, x - 1, 0, x - 1, 31, INK); R(d, x + 3, 0, x + 3, 31, INK)
    R(d, x, 0, x, 31, O[0]); R(d, x + 1, 0, x + 1, 31, O[1]); R(d, x + 2, 0, x + 2, 31, O[2])
    for y in (4, 20):
        R(d, x - 1, y - 1, x + 3, y - 1, INK); R(d, x - 1, y + 4, x + 3, y + 4, INK)
        R(d, x - 1, y, x + 3, y + 3, O[1]); R(d, x - 1, y, x + 3, y, O[0]); R(d, x - 1, y + 3, x + 3, y + 3, O[3])
        d.point((x, y + 1), fill=S[1]); d.point((x + 2, y + 2), fill=S[1])
    for k in range(4):                   # the rail's shadow on the deck, east of it
        for y in range(32):
            if x + 4 + k <= 31 and (k < 3 or y % 2 == 0):
                d.point((x + 4 + k, y), fill=T_SHADE)
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
    S = T_STEEL
    for y, (x0, x1) in zip(range(14, 21), ((18, 110), (12, 116), (8, 120), (6, 123), (8, 120), (12, 116), (18, 110))):
        R(d, x0, y, x1, y, S[0] if y < 16 else S[1] if y < 19 else S[2])
    R(d, 20, 16, 108, 16, S[3]); R(d, 20, 17, 108, 17, S[4])
    for i, x in enumerate((30, 50, 70, 90)):
        up = i % 2
        ey = 2 if up else 28
        seg(d, x + 3, 13, x - 8, ey, T_WOOD[1]); seg(d, x + 4, 13, x - 7, ey, T_WOOD[4])
        by = 0 if up else 27
        R(d, x - 12, by, x - 8, by + 2, T_RED[1]); R(d, x - 12, by, x - 8, by, T_RED[0])
        R(d, x - 12, by + 2, x - 8, by + 2, T_RED[2])
        hi, base, lo = (T_MUSTARD[0], T_MUSTARD[2], T_MUSTARD[3]) if i % 2 == 0 else (T_BLUE[4], T_BLUE[5], NAVY)
        R(d, x, 9, x + 5, 15, base); R(d, x, 9, x, 15, hi); R(d, x, 9, x + 5, 9, hi); R(d, x + 5, 10, x + 5, 15, lo)
        R(d, x + 1, 5, x + 4, 8, T_SKIN); R(d, x + 4, 5, x + 4, 8, T_SKIN_LO); R(d, x + 1, 5, x + 4, 5, T_WOOD[4])
    d.point((1, 17), fill=S[0]); d.point((3, 16), fill=S[1])
    outline(im)
    return im


LADIES = {      # body hi, body, board line, deep shade, trim, trim lit, door, door shade
    'a': ('bbe9ff', '8ec2fa', '588cc6', '425faa', '172459', '314b8e', 'aa4d31', '8a3a22'),
    'b': ('fafcfd', 'f3d890', 'e3c587', 'c6a663', '904a37', 'aa4d31', '508582', '395050'),
    'c': ('ffe2e0', 'ff9b92', 'e78d7b', 'bb6479', '3c396d', '8f72b6', '172459', '0a1627'),
    'd': ('b1dfdc', '93c297', '6c8e7f', '508582', '395050', '506b6b', '904a37', '5b283b'),
}


def lady(kind, step):
    """A painted lady. `step` px of brick footing lift it: the row climbs the hill."""
    hi, body, board, deep, trim, trim_hi, door, door_lo = (rgb(c) for c in LADIES[kind])
    S, SL, MA = T_STEEL, T_SLATE, T_MAROON
    im, d = canvas(3, 5)                 # 96 x 160
    base = 157 - step
    courses(d, 4, base, 91, 157, MA[1], MA[2], None, 4, 8)
    if step:
        R(d, 4, base, 91, base, MA[0])
    # the wall: weatherboards, lit on the west, the eave's shadow under the cornice
    R(d, 6, 62, 89, base - 1, body)
    for y in range(72, base, 5):
        R(d, 6, y, 89, y, board)
    R(d, 6, 67, 89, 68, deep)
    R(d, 6, 69, 7, base - 1, hi); R(d, 87, 69, 89, base - 1, board); R(d, 89, 69, 89, base - 1, deep)
    # the roof seen from above: two shingled planes behind a gable
    for x in range(2, 94):
        west = x <= 47
        dx = 47 - x if west else x - 48
        yg = 20 + dx
        lit, dark = (SL[0], SL[1]) if west else (SL[1], SL[2])
        for y in range(yg - 12, yg):
            k = y - (yg - 12)
            joint = k % 4 == 3 or (x + (0 if (k // 4) % 2 else 2)) % 4 == 0
            d.point((x, y), fill=dark if joint else lit)
        d.point((x, yg - 12), fill=S[2] if west else SL[1])
        for y in range(yg, 62):
            k = y - 22
            o = 2 if (k // 4) % 2 else 0
            scale = (k % 4 == 3 and (x + o) % 4 != 1) or (k % 4 == 2 and (x + o) % 4 == 1)
            d.point((x, y), fill=board if scale else body)
        for k, c in enumerate((S[0], S[0], S[0], trim, deep)):
            if yg + k < 62:
                d.point((x, yg + k), fill=c)
    R(d, 47, 8, 47, 22, S[0]); R(d, 48, 8, 48, 22, S[2])
    R(d, 47, 3, 48, 7, T_MUSTARD[2]); d.point((47, 3), fill=T_MUSTARD[0])
    courses(d, 66, 22, 73, 37, MA[1], MA[2], None, 4, 4)            # the stack
    R(d, 66, 22, 66, 37, MA[0]); R(d, 73, 22, 73, 37, MA[2])
    R(d, 65, 20, 74, 20, S[1]); R(d, 65, 21, 74, 21, S[2]); R(d, 65, 22, 74, 22, S[3])
    # the sunburst in the gable
    for y in range(51, 61):
        w = arc_w(11, 10, 60 - y)
        R(d, 48 - w, y, 47 + w, y, S[0])
    for ox, dx, dy in ((47, -9, -2), (47, -7, -6), (47, -3, -8), (48, 3, -8), (48, 7, -6), (48, 9, -2)):
        seg(d, ox, 60, ox + dx, 60 + dy, trim_hi)
    R(d, 46, 58, 49, 60, trim)
    # the cornice
    R(d, 2, 61, 93, 62, S[0]); R(d, 2, 63, 93, 63, S[1]); R(d, 2, 64, 93, 66, trim)
    R(d, 2, 64, 93, 64, trim_hi)
    for x in range(4, 92, 6):
        R(d, x, 65, x + 1, 66, S[0])
    # the bay window, two storeys of it, under a slate cap
    R(d, 10, 72, 46, base - 6, S[0]); R(d, 45, 72, 46, base - 6, S[1])
    R(d, 9, 69, 47, 72, SL[1]); R(d, 9, 69, 47, 69, SL[0]); R(d, 9, 72, 47, 72, SL[2])
    for y0 in (76, 110):
        if y0 + 22 > base - 8:
            continue
        for x in (13, 24, 35):
            pane(d, x, y0, x + 8, y0 + 22, 7)
            R(d, x, y0 + 11, x + 8, y0 + 11, S[0])
        R(d, 10, y0 + 24, 46, min(y0 + 27, base - 6), trim); R(d, 10, y0 + 24, 46, y0 + 24, trim_hi)
    for y in range(141, base - 5, 3):
        R(d, 10, y, 46, y, S[1])
    # the window over the door
    R(d, 61, 73, 79, 93, S[0]); R(d, 79, 73, 79, 93, S[1])
    pane(d, 63, 75, 77, 91, 7)
    R(d, 70, 75, 70, 91, S[0]); R(d, 63, 83, 77, 83, S[0])
    R(d, 60, 94, 80, 94, S[1])
    # the porch: a roof seen from above on two posts, the door up its own flight of steps
    R(d, 55, 97, 85, 102, SL[1]); R(d, 55, 97, 85, 97, SL[0]); R(d, 55, 101, 85, 102, S[0])
    R(d, 55, 103, 85, 103, trim)
    for x in (57, 82):
        R(d, x, 104, x + 1, base - 10, S[0]); R(d, x + 1, 104, x + 1, base - 10, S[1])
    R(d, 62, 106, 78, base - 10, door); R(d, 77, 106, 78, base - 10, door_lo)
    pane(d, 64, 108, 75, 120, 7)
    R(d, 65, 125, 75, base - 14, door_lo); R(d, 66, 126, 74, base - 15, door)
    d.point((76, 123), fill=T_MUSTARD[2])
    for i in range(3):
        y0 = base - 9 + i * 3
        R(d, 56 - i * 2, y0, 84 + i * 2, y0 + 2, S[2]); R(d, 56 - i * 2, y0, 84 + i * 2, y0, S[1])
        R(d, 56 - i * 2, y0 + 2, 84 + i * 2, y0 + 2, S[3])
    outline(im)
    return im


def lane_wall(d, w=96):
    """Bluestone, 3x2: coursed blocks under a coping seen from above. A wall face, so flat."""
    ST, S = T_STONE, T_STEEL
    R(d, 0, 0, w - 1, 63, ST[1])
    for k, top in enumerate(range(5, 61, 8)):
        R(d, 0, top + 7, w - 1, top + 7, ST[2])
        off = 7 if k % 2 else 0
        for x in range(off - 14, w, 14):
            if x >= 0:
                R(d, x, top, x, top + 6, ST[2])
            R(d, max(x + 1, 0), top, min(x + 13, w - 1), top, ST[0])
            if x + 4 >= 0 and speck(x, top, 3) < 30:
                R(d, max(x + 4, 0), top + 3, min(x + 6, w - 1), top + 3, ST[2])
    R(d, 0, 0, w - 1, 3, S[3]); R(d, 0, 0, w - 1, 0, S[2])
    for x in range(23, w, 24):
        R(d, x, 0, x, 3, S[4])
    R(d, 0, 4, w - 1, 4, S[6])
    R(d, 0, 61, w - 1, 63, ST[2])


def inked(d, x0, y0, x1, y1, fill):
    """A piece painted or set into the wall, boxed in ink by hand (the wall fills its canvas)."""
    R(d, x0, y0, x1, y1, INK); R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)


BIRD = (
    '..........WWW.....................', '.........WWWWW....................',
    '........WWWWWWW...................', '........WWWWWWWW..................',
    '.........WWWWWWWW.................', '..........WWWWWWWW......WWWW......',
    '...........WWWWWWWW...WWWWWWW.....', 'W...........WWWWWWWWWWWWWWKWWW....',
    'WWW..........WWWWWWWWWWWWWWWWWGG..', '.WWWW......WWWWWWWWWWWWWWWWWWW....',
    '..WWWWWWWWWWWWWWWWWWWWWWWWWW......', '...WWWWWWWWWWWWWWWWWWWWWWW........',
    '....WWWWWWWWSSSSSSSWWWWW..........', '..WWWWWW......SSSSSSSSW...........',
    '.WWW............SSSSSSSS..........', 'W.................SSSSSSS.........',
    '....................SSSSS.........', '......................SSS.........',
)


def mural(kind):
    im, d = canvas(3, 2)
    lane_wall(d)
    S, P = T_STEEL, T_PINK
    if kind == 'a':                      # a face in profile, pink on teal, and a tag
        inked(d, 6, 10, 52, 56, T_TEAL[1])
        for y in range(12, 56, 8):
            R(d, 7, y, 51, y, T_TEAL[2])
        R(d, 7, 11, 51, 11, T_TEAL[0])
        for y in range(14, 51):
            w = arc_w(15, 18, y - 32)
            for x in range(30 - w, 30 + w):
                s = (x - 29) * 30 + (y - 32) * 45
                d.point((x, y), fill=P[0] if s < -560 else P[1] if s < 420 else P[2])
        for (y0, y1, x1) in ((28, 29, 45), (30, 31, 47), (32, 33, 50), (34, 35, 48), (36, 37, 45)):
            R(d, 42, y0, x1, y1, P[1])
            R(d, x1, y0, x1, y1, P[2])
        R(d, 42, 37, 45, 37, P[2])
        R(d, 34, 24, 38, 24, INK)                                   # brow, eye, mouth
        R(d, 35, 26, 37, 27, S[0]); d.point((37, 27), fill=INK)
        R(d, 37, 42, 41, 42, T_RED[2]); d.point((41, 41), fill=T_RED[2])
        for y in range(12, 22):                                     # a navy cap over the crown
            w = arc_w(15, 18, y - 32) + 1 if y >= 14 else 8 + (y - 12) * 3
            R(d, 30 - w, y, 29 + w, y, NAVY)
            R(d, 30 - w, y, 30 - w + 3, y, T_BLUE[5])
        R(d, 14, 21, 47, 22, NAVY); R(d, 14, 21, 47, 21, T_BLUE[5])
        for y, (c, lo) in zip((20, 29, 38), ((T_MUSTARD[0], T_MUSTARD[2]), (P[2], T_RED[2]), (S[0], S[1]))):
            pts = ((58, y), (66, y - 6), (72, y + 4), (80, y - 8), (88, y + 2))
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                seg(d, xa, ya + 1, xb, yb + 1, lo, 2); seg(d, xa, ya, xb, yb, c, 2)
    elif kind == 'b':                    # bubble letters and drips
        tones = ((T_MUSTARD[0], T_MUSTARD[2], T_MUSTARD[3]), (T_BLUE[2], T_BLUE[3], T_BLUE[4]),
                 (P[1], P[2], P[3]), (T_COPPER[1], T_COPPER[2], T_COPPER[4]))
        ins = (4, 2, 1, 1)
        for i, (c, lo, dk) in enumerate(tones):
            x = 6 + i * 22
            dx = x + 6 + i
            R(d, dx - 1, 46, dx + 1, 51 + i * 2, INK); R(d, dx, 46, dx, 50 + i * 2, lo)
            for y in range(13, 48):
                k = min(y - 13, 47 - y)
                n = ins[k] if k < 4 else 0
                R(d, x - 1 + n, y, x + 19 - n, y, INK)
            for y in range(14, 47):
                k = min(y - 14, 46 - y)
                n = ins[k] if k < 4 else 0
                for xx in range(x + n, x + 19 - n):
                    col = c if y < 38 else lo if y > 38 else (c if xx % 2 else lo)
                    if xx >= x + 16:
                        col = dk
                    d.point((xx, y), fill=col)
            R(d, x + 6, 22, x + 12, 34, INK); R(d, x + 7, 23, x + 11, 33, T_STONE[1])
            R(d, x + 7, 23, x + 11, 23, T_STONE[2])
            R(d, x + 4, 16, x + 9, 16, S[0]); d.point((x + 3, 18), fill=S[0])
        for x in (10, 40, 70, 84):
            d.point((x, 9), fill=S[1])
    else:                                # a stencilled bird, a paste-up, a rainbow stripe
        bands = (T_RED[1], T_MUSTARD[0], T_COPPER[1], T_BLUE[2], T_PURPLE[0])
        for x in range(96):
            y0 = 45 - x * 14 // 95
            for i, c in enumerate(bands):
                R(d, x, y0 + i * 3, x, y0 + i * 3 + 2, c)
            d.point((x, y0 + 15), fill=T_STONE[2])
        pixmap(d, 14, 14, BIRD, {'W': S[0], 'S': S[1], 'K': INK, 'G': T_MUSTARD[2]})
        inked(d, 68, 12, 88, 38, T_CREAM[0])
        R(d, 87, 13, 87, 37, T_CREAM[1]); R(d, 69, 37, 87, 37, T_CREAM[1])
        R(d, 70, 14, 86, 26, NAVY); R(d, 70, 14, 86, 14, T_BLUE[5])
        R(d, 74, 18, 80, 24, T_BLUE[4]); R(d, 74, 18, 80, 18, T_BLUE[3]); d.point((82, 17), fill=T_MUSTARD[0])
        for y, w in ((29, 14), (32, 11), (35, 13)):
            R(d, 70, y, 70 + w, y, T_CREAM[2])
        for k in range(4):               # the corner peeling off
            R(d, 88 - 3 + k, 12 + k, 88, 12 + k, T_STONE[1])
            d.point((88 - 4 + k, 12 + k), fill=INK)
        R(d, 85, 13, 86, 14, T_CREAM[1])
    outline(im)
    return im


def coffee():
    im, d = canvas(3, 2)
    lane_wall(d)
    S, W = T_STEEL, T_WOOD
    # the hatch: dark inside, not lit; a machine and cups on the counter, a shelf to lean on
    inked(d, 30, 16, 66, 44, S[6])
    R(d, 31, 34, 65, 43, S[5]); R(d, 31, 34, 65, 34, S[4])
    R(d, 34, 24, 48, 40, S[2]); R(d, 34, 24, 48, 24, S[1]); R(d, 34, 24, 34, 40, S[1])
    R(d, 48, 25, 48, 40, S[3]); R(d, 34, 40, 48, 40, S[3])
    R(d, 36, 27, 46, 29, T_GLASS); d.point((38, 32), fill=T_MAROON[0]); d.point((44, 32), fill=T_MUSTARD[2])
    R(d, 40, 33, 42, 36, S[4])
    for x in (52, 57, 62):
        R(d, x, 30, x + 2, 33, S[0]); R(d, x + 2, 30, x + 2, 33, S[1])
    R(d, 26, 44, 70, 47, W[1]); R(d, 26, 44, 70, 44, W[0]); R(d, 26, 46, 70, 46, W[2])
    R(d, 26, 47, 70, 47, W[3])
    # the awning, seen from above: striped canvas with a scalloped edge
    R(d, 22, 4, 74, 4, INK)
    for x in range(23, 74):
        dark = ((x - 23) // 6) % 2 == 0
        R(d, x, 5, x, 9, T_COPPER[2] if dark else S[0])
        R(d, x, 10, x, 13, T_COPPER[4] if dark else S[1])
        if (x - 23) % 3 != 2:
            d.point((x, 14), fill=T_COPPER[4] if dark else S[1]); d.point((x, 15), fill=INK)
        else:
            d.point((x, 14), fill=INK)
    R(d, 22, 5, 22, 14, INK); R(d, 74, 5, 74, 14, INK)
    # the chalk board and a hanging cup sign
    R(d, 5, 17, 25, 51, INK)
    R(d, 6, 18, 24, 50, W[3]); R(d, 6, 18, 24, 18, W[0]); R(d, 6, 18, 6, 50, W[0])
    R(d, 8, 20, 22, 48, T_COPPER[4])
    for i, wdt in enumerate((12, 9, 12, 8, 11)):
        R(d, 9, 23 + i * 5, min(9 + wdt, 21), 23 + i * 5, T_MUSTARD[0] if i == 0 else S[1])
    R(d, 83, 10, 83, 14, INK)
    orb(d, 83, 23, 8, INK); orb(d, 83, 23, 7, T_CREAM[0])
    for t in range(-7, 8):
        for s in range(-7, 8):
            if s + t > 3 and s * s + t * t <= 49 + 7:
                d.point((83 + s, 23 + t), fill=T_CREAM[1])
    R(d, 79, 20, 85, 27, W[2]); R(d, 79, 20, 85, 20, W[1]); R(d, 86, 22, 87, 22, W[2])
    R(d, 87, 22, 87, 25, W[2]); R(d, 86, 25, 87, 25, W[2])
    # two milk crates stacked by the hatch, in the bridge's orange
    R(d, 74, 38, 92, 57, INK)
    for y0 in (39, 48):
        R(d, 75, y0, 91, y0 + 7, T_ORANGE[1]); R(d, 75, y0, 91, y0, T_ORANGE[0])
        R(d, 75, y0 + 3, 91, y0 + 3, T_ORANGE[2]); R(d, 75, y0 + 7, 91, y0 + 7, T_ORANGE[3])
        R(d, 81, y0 + 5, 85, y0 + 5, INK); R(d, 89, y0 + 1, 91, y0 + 6, T_ORANGE[2])
    outline(im)
    return im


def crates():
    im, d = canvas(1, 1)
    for x, (hi, c, lo, dk) in ((1, T_ORANGE), (21, (T_BLUE[2], T_BLUE[4], T_BLUE[5], NAVY))):
        R(d, x, 15, x + 9, 18, dk); R(d, x, 15, x + 9, 15, hi); R(d, x, 15, x, 18, hi)
        R(d, x + 9, 15, x + 9, 18, c)
        R(d, x, 19, x + 9, 28, c); R(d, x, 19, x, 28, hi); R(d, x + 8, 19, x + 9, 28, lo)
        R(d, x, 28, x + 9, 28, lo)
        R(d, x + 2, 22, x + 3, 22, dk); R(d, x + 6, 22, x + 7, 22, dk)
        R(d, x + 1, 25, x + 7, 25, lo)
    W = T_WOOD
    R(d, 15, 12, 16, 27, W[4]); R(d, 13, 27, 18, 28, W[4])
    R(d, 12, 7, 20, 7, W[1]); R(d, 10, 8, 22, 10, W[1]); R(d, 12, 11, 20, 11, W[2])
    R(d, 12, 7, 16, 7, W[0]); R(d, 10, 8, 11, 9, W[0]); R(d, 21, 9, 22, 10, W[2])
    for cx, cy in ((12, 8), (18, 8)):
        R(d, cx, cy - 2, cx + 2, cy, T_STEEL[0]); R(d, cx + 2, cy - 2, cx + 2, cy, T_STEEL[1])
    outline(im)
    cast(im, [(0, 30, 31, 31)])
    return im


def pyramid():
    im, d = canvas(4, 12)                # 128 x 384
    S = T_STEEL
    cx = 64
    px = im.load()

    def half(y):
        return 1 + (y - 40) * 43 // 280

    R(d, cx, 4, cx, 40, S[1]); R(d, cx - 1, 22, cx - 1, 40, S[0])     # the spire
    d.point((cx, 3), fill=T_RED[1])
    for y in range(40, 322):
        w = half(y)
        floor = (y - 40) % 6
        for x in range(cx - w, cx + w + 1):
            lit = x < cx
            win = floor in (2, 3) and (x - cx) % 5 != 0 and y > 70
            if win:
                c = T_GLASS_LO if floor == 2 else T_GLARE if lit and (x + y // 6 * 2) % 11 == 0 else T_GLASS
            elif lit:
                c = S[1] if floor == 4 else S[0]
            else:
                c = S[3] if floor == 4 else S[2]
            px[x, y] = c
        px[cx - w, y] = S[0]
        px[cx + w, y] = S[4]
        px[cx, y] = S[3]
    # the two wings high on the tower (the lift shaft and the stair)
    for y in range(118, 250):
        w = half(y)
        joint = y >= 120 and (y - 120) % 12 == 11
        cap = y < 120
        for i in range(1, 6):
            west = (S[2], S[1], S[1], S[1], S[0])[i - 1]
            east = (S[2], S[3], S[3], S[3], S[4])[i - 1]
            if cap:
                west = east = S[0] if y == 118 else S[1]
            elif joint:
                west, east = S[2], S[4]
            px[cx - w - i, y] = west
            px[cx + w + i, y] = east
    # the base: leaning columns, dark glass behind, a canopy and doors
    pane(d, 14, 325, 113, 379, 13)
    for y in range(325, 380):
        o = (379 - y) * 8 // 55
        for x in range(14, 110, 16):
            R(d, x + o, y, x + o + 3, y, S[0])
            R(d, x + 13 - o, y, min(x + 15 - o, 113), y, S[2])
    R(d, 12, 318, 115, 324, S[0]); R(d, 12, 323, 115, 323, S[1]); R(d, 12, 324, 115, 324, S[2])
    R(d, 48, 350, 79, 379, S[4])
    pane(d, 50, 352, 63, 379, 7); pane(d, 65, 352, 77, 379, 7)
    d.point((62, 366), fill=T_MUSTARD[2]); d.point((66, 366), fill=T_MUSTARD[2])
    R(d, 12, 380, 115, 380, S[3]); R(d, 12, 381, 115, 381, S[4])
    outline(im)
    cast(im, [(10, 383, 117, 383)])
    return im


def spire():
    im, d = canvas(4, 11)                # 128 x 352
    S, SL, ST, M = T_STEEL, T_SLATE, T_STONE, T_MUSTARD
    cx = 64
    # the hall it stands on: a flat roof seen from above over coursed bluestone and dark glass
    R(d, 6, 268, 121, 287, SL[1]); R(d, 6, 268, 121, 268, SL[0])
    for x in range(17, 121, 12):
        R(d, x, 269, x, 285, SL[2]); R(d, x + 1, 269, x + 1, 285, SL[0])
    R(d, 6, 286, 121, 287, SL[2])
    courses(d, 10, 288, 117, 347, ST[1], ST[2], ST[0], 8, 14)
    R(d, 10, 288, 117, 289, ST[2])
    R(d, 10, 290, 10, 340, ST[0]); R(d, 115, 290, 117, 347, ST[2]); R(d, 10, 341, 117, 347, ST[2])
    for x in range(16, 101, 12):
        if 50 <= x <= 68:
            continue
        R(d, x - 1, 295, x + 8, 331, S[2]); R(d, x - 1, 295, x + 8, 295, S[1])
        pane(d, x, 296, x + 7, 330, 7)
    R(d, 49, 304, 78, 347, S[4])
    pane(d, 51, 306, 63, 347, 7); pane(d, 65, 306, 76, 347, 7)
    d.point((62, 326), fill=M[2]); d.point((66, 326), fill=M[2])
    R(d, 45, 299, 82, 303, M[2]); R(d, 45, 299, 82, 299, M[0]); R(d, 45, 303, 82, 303, M[3])
    # the mast and the lattice skirt: open work, so the sky shows through
    R(d, cx, 4, cx, 150, S[0]); R(d, cx + 1, 60, cx + 1, 150, S[2])
    d.point((cx, 3), fill=T_RED[1])

    def half(y):                         # thin, then flaring out to the roof
        u = y - 90
        return 2 + 50 * u * u * math.isqrt(u * 190) // (190 * 190 * 190)

    hoops = range(110, 281, 14)

    def hoop(y, near):
        w = half(y)
        for x in range(-w, w + 2):
            sag = 3 * math.isqrt(max(0, w * w - x * x)) // w
            if near:
                c = M[0] if x < -w // 3 else M[2] if x < w // 2 else M[3]
                d.point((cx + x, y + sag), fill=c)
            else:
                d.point((cx + x, y - sag), fill=S[3])

    for y in hoops:
        hoop(y, False)
    for y in range(90, 281):
        h = half(y)
        for i in range(-6, 7):
            x = cx + (h * abs(i) // 6) * (1 if i > 0 else -1) + (1 if i > 0 else 0)
            d.point((x, y), fill=S[0] if i <= 0 else S[1] if i < 4 else S[2])
    for y in hoops:
        hoop(y, True)
    outline(im)
    cast(im, [(9, 349, 118, 350)])
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
