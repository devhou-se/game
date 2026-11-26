#!/usr/bin/env python3
"""generate_sapporo_art.py — draw Sapporo's own buildings and street pieces (issue #219).

Sapporo had two sprites of its own (the Clock Tower and the TV Tower, from
tools/generate_hokkaido.py) and borrowed Osaka's high-rises and the generic
townhouses for everything else. These are the pieces its five districts are
rebuilt from, drawn the way generate_hokkaido.py / generate_fukuoka_art.py draw
theirs: shaded pixel art in the GuttyKreum palette, at half size (one drawn
pixel = one pixel of a 32px tile) and pixel-doubled, lit from the left, with a
1px ink outline, and all of it under snow. Not line-art placeholders. Every
name on a sign is a look-alike; there is no real brand artwork.

Station front
  sapporo-station-front_0_0   10x7  Sapporo Station: a four-storey glazed hall
                                    with the star clock, stone wings, a long
                                    canopy with snow on it, a stub of the
                                    station tower behind the east wing
  sapporo-akarenga_0_0         7x6  the Former Hokkaido Government Office: red
                                    brick, slate roof, green copper dome, the
                                    red pioneer star in its gable
  sapporo-office-brick_0_0     4x7  filler: a red-brick office block
  sapporo-office-glass_0_0     5x6  filler: a brick-framed glass block with a
                                    rooftop board (KITA, the red star)
  sapporo-konbini_0_0          4x3  a konbini front in this style (the town's
                                    7-Eleven tile is bare line art)
Tanukikoji (the covered arcade)
  tanukikoji-gate_0_0          4x4  the arcade's arch: a tanuki medallion over
                                    a red board, bulbs under the arch; you walk
                                    through the two middle cells
  tanukikoji-rib_0_0           4x3  a rib of the roof: the arch without the
                                    board, glass between its chords, banners
  tanukikoji-shop-souvenir_0_0 3x4  three north-row shopfront modules under one
  tanukikoji-shop-crab_0_0     3x4  length of the arcade's glass roof each;
  tanukikoji-shop-drug_0_0     3x4  they tile side by side
  tanukikoji-south-row-a/-b    3x3  the south row seen from behind under the
                                    same roof; its top row overhangs the street
  tanukikoji-end-sign_0_0      1x4  the roof's east / west end: a post and the
                                    upright タヌキ sign
Susukino
  susukino-neon-corner_0_0     5x7  the crossing's neon building: an invented
                                    mascot board (a winking fox with a mug of
                                    beer, on rays) over stacked sign boards
  susukino-ramen-gate_0_0      3x3  the ramen alley's gate: a yellow board, a
                                    row of red paper lanterns; walk through
  susukino-karaoke_0_0         4x5  a karaoke / bar front with lit rooms
  susukino-neon-lanterns_0_0   1x2  a pole of small neon signs, and
  ramen-alley-lanterns_0_0     1x2  a post of paper lanterns. Their keys hold
                                    `-lanterns`, so src/DayNight.js gives each
                                    a halo at night like every other lantern
                                    (the game has no lit-window layer: a halo on
                                    a lamp/lantern cell is the only emissive)
Odori Park
  snow-sculpture-castle_0_0    5x4  the big one: a castle keep carved in snow
  snow-sculpture-tanuki_0_0    2x3  a snow tanuki in a straw hat
  snow-sculpture-bear_0_0      3x2  a snow bear, side on, a salmon in its jaws
  snowfest-stall-corn_0_0      3x3  festival tents: grilled corn, hot drinks
  snowfest-stall-drinks_0_0    3x3
  odori-fountain_0_0           3x3  the fountain frozen over, lights in the ice
  odori-lamp-post_0_0          1x2  the park's lamp: a white globe on a green
                                    iron post (`lamp-post`: a halo at night)
  odori-bench_0_0              2x1  a dark green park bench under snow
Streetcar
  tram-rail-h / -v / -cross    1x1  track: an opaque ground tile in place of the
                                    road tile - setts, grey rails, dark grooves
  tram-pole_0_0                2x3  an overhead-wire pole with its bracket arm
  sapporo-streetcar_0_0        5x3  a green and cream streetcar, side on, its
                                    feet on the bottom edge like train-green
Kerbs
  snowbank-h / -v / -pile      1x1  what the plough leaves along a kerb
Ground
  arcade-brick-autotile_*      1x1  basket-weave red brick with a stone kerb (9
                                    autotile roles) - the arcade's floor
  snow-path-autotile_*         1x1  a path trodden through the snow (9 roles):
                                    the snow tile a shade lower, boot prints

This tool writes the PNGs into assets/sprites/ and registers every one in
config.json (spriteMetadata, tileNames), as generate_fukuoka_art.py does; the
palette grows when a generator first places a sprite (roomgen.pidx). The
prefabs of the pieces that are placed are in tools/make_prefabs.py, the two
office blocks' doors in roomgen.TOWER_DOORS, and the town itself is built by
tools/generate_sapporo.py - stage by stage, so most of this is not placed yet.

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs Pillow. Run from gamev2/:
    python3 tools/generate_sapporo_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (rgb, canvas, outline, snow_cap, tiles, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, SNOW, SNOW_LO, GLASS, GLASS_HI, GLASS_DK,
                               WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)

SPR = 'assets/sprites'

WOOD_HI = rgb('d2a58c')
BRICK, BRICK_HI, BRICK_LO, BRICK_DK = rgb('b8614a'), rgb('cf7c63'), rgb('9a4c39'), rgb('74382e')
SNOW_SH, SNOW_DK = rgb('a9bbd6'), rgb('8497b8')        # snow in shade / in deep shade
DARK = rgb('2a2330')
NIGHT = rgb('1b2040')
PURPLE, PURPLE_LO, PURPLE_HI = rgb('6b4a8c'), rgb('4a3266'), rgb('8d6bb0')
PINK, PINK_HI = rgb('f0669e'), rgb('fbb4d0')
CYAN, CYAN_LO = rgb('66dcea'), rgb('2f93b0')
LIME = rgb('8fe08a')
FOX, FOX_LO = rgb('e8873a'), rgb('b85e24')
TRAM, TRAM_HI, TRAM_LO = rgb('3d6a52'), rgb('5d8f70'), rgb('294a3b')
WARM = rgb('f6dc8c')                                    # lamplight behind glass

# ---- lettering ----------------------------------------------------------------
FONT = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'J': ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#.#.#', '#..##', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    ' ': ['.....'] * 7,
}
KANA = {       # 7x7 katakana, hand-set
    'ka': ['..#....', '#######', '..#...#', '..#...#', '.#....#', '.#....#', '#...##.'],
    'ni': ['.......', '.#####.', '.......', '.......', '.......', '#######', '.......'],
    'ta': ['..#....', '..#####', '.#....#', '#.##.#.', '....#..', '...#...', '.##....'],
    'nu': ['#######', '......#', '.#...#.', '..#.#..', '...#...', '..#.#..', '##...#.'],
    'ki': ['...#...', '.######', '...#...', '#######', '....#..', '....#..', '....#..'],
    'su': ['#######', '......#', '.....#.', '....#..', '...#.#.', '..#...#', '##....#'],
    'no': ['......#', '......#', '.....#.', '....#..', '...#...', '..#....', '##.....'],
    'ra': ['.#####.', '.......', '#######', '......#', '.....#.', '....#..', '.###...'],
    'o':  ['....#..', '#######', '....#..', '...##..', '..#.#..', '.#..#..', '#..##..'],
    'ke': ['.#.....', '.#.....', '.######', '#...#..', '....#..', '...#...', '.##....'],
    'ku': ['..#....', '..#####', '.#....#', '#....#.', '....#..', '...#...', '.##....'],
    'ri': ['#....#.', '#....#.', '#....#.', '#....#.', '.....#.', '....#..', '..##...'],
    'me': ['.....#.', '.#...#.', '..##.#.', '....#..', '...#.#.', '..#...#', '##.....'],
    'n':  ['#......', '.#....#', '......#', '.....#.', '....#..', '..##...', '##.....'],
    'bi': ['#...#.#', '#....#.', '#..##..', '###....', '#......', '#......', '.#####.'],
    'ko': ['#######', '......#', '......#', '......#', '......#', '......#', '#######'],
    'bar': ['.......', '.......', '.......', '#######', '.......', '.......', '.......'],
    'vbar': ['...#...'] * 7,                      # the long-vowel bar in vertical text
}


def glyphs(d, rows_list, x, y, fill, scale=1, gap=1, vertical=False):
    for rows in rows_list:
        for gy, row in enumerate(rows):
            for gx, ch in enumerate(row):
                if ch == '#':
                    d.rectangle([x + gx * scale, y + gy * scale,
                                 x + gx * scale + scale - 1, y + gy * scale + scale - 1], fill=fill)
        if vertical:
            y += (len(rows) + gap) * scale
        else:
            x += (len(rows[0]) + gap) * scale


def text(d, s, x, y, fill, scale=1, vertical=False):
    glyphs(d, [FONT[c] for c in s], x, y, fill, scale, 1, vertical)


def kana(d, names, x, y, fill, scale=1, vertical=False):
    glyphs(d, [KANA['vbar' if (vertical and n == 'bar') else n] for n in names], x, y, fill, scale, 1, vertical)


def text_w(s, scale=1):
    return (len(s) * 6 - 1) * scale


def kana_w(n, scale=1):
    return (n * 8 - 1) * scale


# ---- surfaces -------------------------------------------------------------------
def brick(d, x0, y0, x1, y1, shade=False):
    """Running-bond brickwork: 3px courses, a dark bed joint, staggered perpends,
    the odd brick a tone lighter or darker."""
    base, lo = (BRICK_LO, BRICK_DK) if shade else (BRICK, BRICK_LO)
    for y in range(y0, y1 + 1):
        course = (y - y0) // 3
        for x in range(x0, x1 + 1):
            if (y - y0) % 3 == 2:
                c = lo
            elif (x + course * 4) % 8 == 0:
                c = lo
            else:
                k = ((x + course * 4) // 8 * 7 + course * 13) % 11
                c = BRICK_HI if (k == 0 and not shade) else (lo if k == 5 else base)
            d.point((x, y), fill=c)


def glazing(d, x0, y0, x1, y1, cw=6, ch=7, lit=(), frame=GLASS_DK):
    """A curtain wall: panes on a grid, the sky sliding across them, a few
    panes with the lights on."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    for j, py in enumerate(range(y0 + 1, y1, ch)):
        for i, px in enumerate(range(x0 + 1, x1, cw)):
            ex, ey = min(px + cw - 2, x1 - 1), min(py + ch - 2, y1 - 1)
            if ex < px or ey < py:
                continue
            if (i, j) in lit:
                d.rectangle([px, py, ex, ey], fill=WARM)
                d.line([(px, ey), (ex, ey)], fill=AMBER)
                continue
            streak = ((px - x0) + (py - y0)) // 14 % 3 == 0
            d.rectangle([px, py, ex, ey], fill=rgb('6583bd') if streak else GLASS)
            d.line([(px, py), (ex, py)], fill=GLASS_HI)
            if streak:
                d.point((px, py + 1), fill=GLASS_HI)


def pane(d, x0, y0, x1, y1, frame=WHITE, lit=False):
    """A plain framed window."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=WARM if lit else GLASS)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=WHITE if lit else GLASS_HI)
    d.line([((x0 + x1) // 2, y0 + 1), ((x0 + x1) // 2, y1 - 1)], fill=frame)


def drift(d, x0, x1, y, h=4, seed=0):
    """Snow shovelled against the foot of a wall: a low mound standing on y."""
    n = x1 - x0
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, n)
        top = y - int(round(h * math.sin(math.pi * t) + ((x * 5 + seed) % 4 == 0)))
        d.line([(x, top), (x, y)], fill=SNOW)
        d.point((x, y), fill=SNOW_LO)
        if x > x0 + n * 0.7:
            d.line([(x, min(top + 1, y)), (x, y)], fill=SNOW_LO)


def lantern(d, x, y, w=8, h=11, body=RED, hi=RED_HI, lo=RED_DK):
    d.rectangle([x + 1, y, x + w - 2, y + 1], fill=INK)
    d.rectangle([x, y + 2, x + w - 1, y + h - 3], fill=body)
    d.line([(x, y + 2), (x, y + h - 3)], fill=hi)
    d.line([(x + w - 1, y + 2), (x + w - 1, y + h - 3)], fill=lo)
    for ry in range(y + 4, y + h - 3, 2):
        d.line([(x + 1, ry), (x + w - 2, ry)], fill=lo)
    d.rectangle([x + 2, y + 3, x + 3, y + h - 5], fill=hi)
    d.rectangle([x + 1, y + h - 2, x + w - 2, y + h - 1], fill=INK)


def star(d, cx, cy, r, fill, edge=None):
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((round(cx + rr * math.cos(a)), round(cy + rr * math.sin(a))))
    d.polygon(pts, fill=fill, outline=edge or fill)


def glass_door(d, x0, y0, x1, y1, frame=STONE_DK):
    """A pair of sliding glass doors."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    m = (x0 + x1) // 2
    d.rectangle([x0 + 1, y0 + 1, m - 1, y1], fill=GLASS)
    d.rectangle([m + 1, y0 + 1, x1 - 1, y1], fill=GLASS)
    d.line([(x0 + 1, y0 + 1), (m - 1, y0 + 1)], fill=GLASS_HI)
    d.line([(m + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=GLASS_HI)
    d.line([(x0 + 2, y0 + 3), (x0 + 2, y1 - 3)], fill=GLASS_HI)
    d.point((m - 2, (y0 + y1) // 2), fill=WHITE); d.point((m + 2, (y0 + y1) // 2), fill=WHITE)


# ==============================================================================
# Station front: the two office blocks (the station itself is further down)
# ==============================================================================
def office_brick():
    im, d = canvas(4, 7)                 # 128 x 224
    # ---- the brick body, a shaded east edge --------------------------------------
    brick(d, 6, 34, 121, 180)
    brick(d, 114, 34, 121, 180, shade=True)
    for y in range(56, 180, 22):                                  # stone string courses
        d.rectangle([6, y, 121, y + 1], fill=CREAM)
        d.line([(6, y + 2), (121, y + 2)], fill=BRICK_DK)
    for k in range(6):                                            # six floors of sash windows
        y = 39 + k * 22
        for i, x in enumerate((13, 30, 47, 98)):
            pane(d, x, y, x + 11, y + 13, lit=(k * 3 + i * 5) % 7 == 0)
            d.line([(x - 1, y + 14), (x + 12, y + 14)], fill=CREAM)          # the sill
            d.line([(x, y - 1), (x + 11, y - 1)], fill=BRICK_DK)             # the lintel's shadow
    # ---- the glazed stair tower up the front -------------------------------------
    d.rectangle([64, 30, 93, 180], fill=STONE)
    d.line([(64, 30), (64, 180)], fill=WHITE); d.line([(93, 30), (93, 180)], fill=STONE_LO)
    glazing(d, 67, 34, 90, 178, cw=8, ch=11, lit={(1, 3), (0, 8), (2, 10)})
    # ---- the copper cornice and what stands on the roof --------------------------
    d.rectangle([3, 28, 124, 34], fill=GREEN)
    d.line([(3, 28), (124, 28)], fill=GREEN_HI)
    d.rectangle([3, 33, 124, 34], fill=GREEN_LO)
    for x in range(8, 122, 6):
        d.point((x, 31), fill=GREEN_LO)
    d.rectangle([16, 12, 46, 27], fill=STONE_LO)                  # the lift house
    d.line([(16, 12), (16, 27)], fill=STONE); d.rectangle([40, 13, 46, 27], fill=STONE_DK)
    d.rectangle([22, 18, 27, 23], fill=GLASS_DK)
    d.rectangle([100, 6, 101, 27], fill=STONE_DK)                 # an aerial
    d.line([(96, 10), (105, 10)], fill=STONE_DK); d.line([(98, 14), (103, 14)], fill=STONE_DK)
    snow_cap(d, 16, 46, 9, 3, seed=2)
    snow_cap(d, 3, 124, 24, 4, seed=5)
    # ---- the ground floor: stone, arched windows, the door under a red awning ---
    d.rectangle([6, 181, 121, 214], fill=CREAM)
    d.line([(6, 181), (121, 181)], fill=WHITE)
    d.rectangle([114, 182, 121, 214], fill=CREAM_LO)
    for y in (192, 203):
        d.line([(6, y), (121, y)], fill=CREAM_LO)
    for x in (13, 36, 100):
        d.rectangle([x, 190, x + 13, 212], fill=CREAM_DK)
        d.pieslice([x, 184, x + 13, 197], 180, 360, fill=CREAM_DK)
        d.rectangle([x + 1, 191, x + 12, 211], fill=WARM if x == 36 else GLASS)
        d.pieslice([x + 1, 185, x + 12, 197], 180, 360, fill=WARM if x == 36 else GLASS)
        d.line([(x + 6, 186), (x + 6, 211)], fill=CREAM_DK)
        d.line([(x + 1, 199), (x + 12, 199)], fill=CREAM_DK)
    d.rectangle([66, 190, 91, 214], fill=WOOD_DK)                 # double doors (cell 2,6)
    d.rectangle([67, 191, 78, 214], fill=WOOD_LO); d.rectangle([80, 191, 90, 214], fill=WOOD_LO)
    d.rectangle([69, 194, 76, 205], fill=GLASS); d.rectangle([82, 194, 88, 205], fill=GLASS)
    d.line([(69, 194), (76, 194)], fill=GLASS_HI); d.line([(82, 194), (88, 194)], fill=GLASS_HI)
    d.point((77, 208), fill=GOLD); d.point((81, 208), fill=GOLD)
    for y in range(183, 190):                                     # the awning
        w = y - 183
        d.line([(64 - w, y), (93 + w, y)], fill=RED if y % 2 else RED_LO)
    d.line([(57, 190), (100, 190)], fill=RED_DK)
    snow_cap(d, 63, 94, 181, 2, seed=9)
    d.rectangle([4, 214, 123, 219], fill=STONE_LO)
    d.line([(4, 214), (123, 214)], fill=STONE)
    drift(d, 3, 24, 219, 5, seed=2); drift(d, 104, 124, 219, 4, seed=6)
    outline(im)
    return im


def office_glass():
    im, d = canvas(5, 6)                 # 160 x 192
    # ---- brick piers at each end, brick spandrels between the floors ------------
    brick(d, 6, 46, 153, 154)
    brick(d, 140, 46, 153, 154, shade=True)
    for k in range(5):
        y = 52 + k * 21
        glazing(d, 22, y, 137, y + 12, cw=10, ch=12,
                lit={((k * 5 + 3) % 11, 0), ((k * 3 + 7) % 11, 0)} if k % 2 else {((k * 7 + 1) % 11, 0)})
        d.line([(22, y + 13), (137, y + 13)], fill=CREAM)         # a stone sill under each band
    for x in (10, 144):                                           # slit windows in the piers
        for k in range(5):
            d.rectangle([x, 54 + k * 21, x + 5, 62 + k * 21], fill=GLASS_DK)
            d.line([(x + 1, 55 + k * 21), (x + 4, 55 + k * 21)], fill=GLASS)
    # ---- the stone parapet, stepped up in the middle, and the rooftop board -----
    d.rectangle([4, 40, 155, 46], fill=CREAM)
    d.line([(4, 40), (155, 40)], fill=WHITE); d.line([(4, 46), (155, 46)], fill=CREAM_DK)
    d.rectangle([148, 41, 155, 46], fill=CREAM_LO)
    for x in (48, 78, 110):                                       # the board's steel legs
        d.rectangle([x, 30, x + 1, 39], fill=STONE_DK)
        d.line([(x - 4, 39), (x + 5, 31)], fill=STONE_DK)
    d.rectangle([36, 8, 123, 31], fill=NAVY)
    d.rectangle([38, 10, 121, 29], fill=rgb('24377a'))
    d.line([(38, 10), (121, 10)], fill=rgb('3a5fb0'))
    text(d, 'KITA', 80 - text_w('KITA', 2) // 2 - 9, 13, WHITE, scale=2)
    d.ellipse([100, 11, 118, 29], fill=WHITE)                     # the pioneers' red star
    star(d, 109, 20, 7, RED, RED_LO)
    snow_cap(d, 36, 123, 5, 3, seed=4)
    snow_cap(d, 4, 35, 36, 4, seed=1); snow_cap(d, 124, 155, 36, 4, seed=8)
    # ---- the lobby floor: glass between brick piers, a steel canopy -------------
    d.rectangle([6, 155, 153, 186], fill=GLASS_DK)
    brick(d, 6, 158, 21, 186); brick(d, 138, 158, 153, 186, shade=True)
    d.rectangle([24, 162, 61, 186], fill=WARM); d.line([(24, 162), (61, 162)], fill=WHITE)
    d.rectangle([98, 162, 135, 186], fill=GLASS); d.line([(98, 162), (135, 162)], fill=GLASS_HI)
    for x in (36, 49, 110, 123):
        d.line([(x, 162), (x, 186)], fill=GLASS_DK)
    d.rectangle([28, 174, 34, 186], fill=GREEN); d.point((30, 173), fill=GREEN_HI)       # a lobby palm
    d.rectangle([42, 178, 58, 186], fill=CREAM_LO)                # the reception desk
    glass_door(d, 66, 160, 79, 186); glass_door(d, 80, 160, 93, 186)        # the doors (cell 2,5)
    d.rectangle([58, 153, 101, 157], fill=STONE)                  # the canopy
    d.line([(58, 157), (101, 157)], fill=STONE_DK)
    snow_cap(d, 58, 101, 150, 3, seed=3)
    d.rectangle([4, 186, 155, 191], fill=STONE_LO)
    d.line([(4, 186), (155, 186)], fill=STONE)
    drift(d, 3, 22, 191, 4, seed=3); drift(d, 132, 156, 191, 5, seed=5)
    outline(im)
    return im


# ==============================================================================
# Tanukikoji
# ==============================================================================
def tanuki_face(d, cx, cy, r=13, snow=False):
    """A tanuki's face: brown, dark eye patches, a cream muzzle, round ears."""
    c, lo, dk = (SNOW, SNOW_LO, SNOW_DK) if snow else (WOOD, WOOD_LO, WOOD_DK)
    muzzle = WHITE if snow else CREAM
    for ex in (cx - r + 2, cx + r - 6):                           # ears
        d.ellipse([ex - 1, cy - r - 3, ex + 6, cy - r + 5], fill=lo)
        d.ellipse([ex + 1, cy - r - 1, ex + 4, cy - r + 3], fill=dk if not snow else SNOW_SH)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], -70, 70, fill=lo)             # the shaded cheek
    d.ellipse([cx - r + 2, cy - 5, cx - 1, cy + 4], fill=dk)                    # eye patches
    d.ellipse([cx + 1, cy - 5, cx + r - 2, cy + 4], fill=dk)
    d.ellipse([cx - 6, cy + 1, cx + 6, cy + r - 2], fill=muzzle)
    d.rectangle([cx - 6, cy - 3, cx - 4, cy - 1], fill=WHITE)                   # eyes
    d.rectangle([cx + 4, cy - 3, cx + 6, cy - 1], fill=WHITE)
    d.point((cx - 5, cy - 2), fill=INK); d.point((cx + 5, cy - 2), fill=INK)
    d.rectangle([cx - 1, cy + 2, cx + 1, cy + 3], fill=INK if not snow else SNOW_DK)   # nose
    d.line([(cx - 3, cy + 7), (cx, cy + 5)], fill=dk); d.line([(cx, cy + 5), (cx + 3, cy + 7)], fill=dk)


def tanuki_gate():
    im, d = canvas(4, 4)                 # 128 x 128
    cx = 64
    # ---- the two steel posts, banded red -----------------------------------------
    for x in (5, 113):
        d.rectangle([x, 50, x + 9, 122], fill=STONE)
        d.line([(x, 44), (x, 122)], fill=WHITE)
        d.rectangle([x + 7, 44, x + 9, 122], fill=STONE_LO)
        for y in (58, 62, 100):
            d.rectangle([x, y, x + 9, y + 1], fill=RED)
        d.rectangle([x - 2, 118, x + 11, 125], fill=STONE_DK)
        d.line([(x - 2, 118), (x + 11, 118)], fill=STONE_LO)
    # ---- the arch: a red board that follows the curve, cream edged ---------------
    for x in range(3, 125):
        t = (x - 63.5) / 61
        top = int(round(24 + 22 * t * t))
        d.line([(x, top), (x, top + 23)], fill=RED)
        d.line([(x, top), (x, top + 1)], fill=CREAM)
        d.line([(x, top + 22), (x, top + 23)], fill=CREAM)
        d.point((x, top + 2), fill=RED_HI)
        d.point((x, top + 21), fill=RED_DK)
        if x % 7 == 3:                                            # bulbs under the arch
            d.rectangle([x, top + 25, x + 1, top + 26], fill=AMBER)
            d.point((x, top + 25), fill=WHITE)
    for word, x0 in (('TANUKI', 9), ('KOJI', 87)):                # lettering along the curve,
        for i, ch in enumerate(word):                             # either side of the medallion
            gx = x0 + i * 6
            t = (gx + 2 - 63.5) / 61
            text(d, ch, gx, int(round(24 + 22 * t * t)) + 8, WHITE)
    # ---- the tanuki medallion on the crown, snow on it and along the arch --------
    d.ellipse([cx - 19, 2, cx + 18, 39], fill=CREAM)
    d.ellipse([cx - 19, 2, cx + 18, 39], outline=GOLD)
    d.ellipse([cx - 17, 4, cx + 16, 37], outline=RED)
    tanuki_face(d, cx, 22, 12)
    for x in range(3, 125):
        if abs(x - 63.5) < 20:
            continue
        t = (x - 63.5) / 61
        top = int(round(24 + 22 * t * t))
        h = 2 + ((x * 7) % 5 in (0, 1))
        d.line([(x, top - h), (x, top - 1)], fill=SNOW)
        d.point((x, top), fill=SNOW_LO)
    for x in range(cx - 13, cx + 13):
        tt = (x - cx) / 19
        top = int(round(20.5 - 18.5 * math.sqrt(max(0, 1 - tt * tt)))) - 1
        d.line([(x, top), (x, top + 2 + (x % 4 == 0))], fill=SNOW)
    outline(im)
    return im


def arcade_roof(d, posts=True, w=96):
    """One module's length of the arcade: the glass vault seen from the street
    side, white steel ribs, snow lying on the crown, the eaves beam, a post at
    each end (so neighbours meet post to post)."""
    for y in range(6, 34):
        t = (y - 6) / 27
        for x in range(0, w):
            c = GLASS_HI if t < 0.3 else (rgb('6f9fe0') if t < 0.6 else GLASS)
            if ((x + y) // 9) % 5 == 0 and t > 0.25:
                c = rgb('a9d3fb') if t < 0.6 else rgb('6583bd')
            d.point((x, y), fill=c)
    for x in list(range(0, w, 12)) + [w - 1]:                     # ribs
        d.line([(x, 6), (x, 33)], fill=WHITE)
        if x < w - 1:
            d.line([(x + 1, 8), (x + 1, 33)], fill=STONE_LO)
    d.line([(0, 20), (w - 1, 20)], fill=STONE)                    # a purlin
    for x in range(0, w):                                         # snow on the crown, sliding off in places
        h = 5 + ((x * 5) % 7 in (0, 3)) + (4 if (x // 12) % 3 == 1 and x % 12 not in (0, 11) else 0)
        d.line([(x, 3), (x, 3 + h)], fill=SNOW)
        d.point((x, 4 + h), fill=SNOW_LO)
    d.rectangle([0, 34, w - 1, 39], fill=STONE)                   # the eaves beam, a red stripe
    d.line([(0, 34), (w - 1, 34)], fill=WHITE)
    d.rectangle([0, 37, w - 1, 38], fill=RED)
    d.line([(0, 39), (w - 1, 39)], fill=STONE_DK)
    d.rectangle([0, 40, w - 1, 43], fill=DARK)                    # the shadow under the roof
    if not posts:
        return
    for x in (0, 92):                                             # the posts
        d.rectangle([x, 40, x + 3, 123], fill=STONE)
        d.line([(x + 3, 40), (x + 3, 123)], fill=STONE_LO)
    d.rectangle([0, 124, 95, 127], fill=STONE_LO)                 # the shop's step
    d.line([(0, 124), (95, 124)], fill=STONE)


def shop_souvenir():
    im, d = canvas(3, 4)                 # 96 x 128
    arcade_roof(d)
    d.rectangle([4, 44, 91, 60], fill=WOOD)                       # a timber sign board
    d.line([(4, 44), (91, 44)], fill=WOOD_HI); d.rectangle([4, 59, 91, 60], fill=WOOD_DK)
    for x in range(10, 90, 14):
        d.line([(x, 46), (x, 58)], fill=WOOD_LO)
    d.rectangle([22, 47, 73, 57], fill=CREAM); d.rectangle([22, 47, 73, 57], outline=WOOD_DK)
    text(d, 'OMIYAGE', 48 - text_w('OMIYAGE') // 2, 49, RED_DK)
    for x in (10, 80):                                            # a carved bear either side
        d.ellipse([x - 4, 49, x + 5, 56], fill=WOOD_DK); d.rectangle([x - 6, 50, x - 3, 53], fill=WOOD_DK)
    d.rectangle([4, 61, 91, 123], fill=CREAM)                     # the plastered front
    d.rectangle([4, 61, 91, 63], fill=CREAM_DK)
    for x0, x1 in ((7, 34), (61, 88)):                            # two lit windows of gift boxes
        d.rectangle([x0, 68, x1, 108], fill=WOOD_DK)
        d.rectangle([x0 + 1, 69, x1 - 1, 107], fill=WARM)
        d.line([(x0 + 1, 69), (x1 - 1, 69)], fill=WHITE)
        for sy in (81, 94, 107):
            d.line([(x0 + 1, sy), (x1 - 1, sy)], fill=WOOD_LO)
            for k, bx in enumerate(range(x0 + 3, x1 - 5, 6)):
                c = (WHITE, rgb('3a5fb0'), RED, GREEN_HI, PINK_HI)[(k + sy) % 5]
                d.rectangle([bx, sy - 6, bx + 3, sy - 1], fill=c)
                d.line([(bx, sy - 4), (bx + 3, sy - 4)], fill=GOLD)
        d.rectangle([x0, 109, x1, 123], fill=WOOD)
        for x in range(x0, x1, 5):
            d.line([(x, 109), (x, 123)], fill=WOOD_LO)
    d.rectangle([38, 66, 57, 123], fill=DARK)                     # the open doorway (cell 1,3)
    d.rectangle([40, 84, 55, 123], fill=rgb('5a3b34'))
    d.rectangle([41, 100, 54, 110], fill=WOOD_LO)                 # a counter inside
    for i, x in enumerate(range(38, 58, 5)):                      # a navy noren
        d.rectangle([x, 66, x + 3, 80], fill=NAVY)
        d.point((x + 1, 73), fill=WHITE); d.point((x + 2, 73), fill=WHITE)
    d.line([(37, 65), (58, 65)], fill=WOOD_DK)
    d.rectangle([10, 112, 22, 123], fill=WHITE)                   # boxes stacked on the step
    d.rectangle([10, 112, 22, 114], fill=rgb('3a5fb0')); d.rectangle([14, 105, 24, 111], fill=PINK_HI)
    d.line([(14, 108), (24, 108)], fill=RED)
    d.rectangle([70, 108, 82, 123], fill=WOOD_DK)                 # the wooden bear by the door
    d.ellipse([66, 96, 84, 110], fill=WOOD_LO); d.ellipse([64, 99, 72, 106], fill=WOOD_LO)
    d.point((66, 101), fill=INK); d.line([(68, 96), (70, 96)], fill=WOOD)
    d.rectangle([60, 102, 66, 104], fill=STONE)                   # its salmon
    outline(im)
    return im


def crab(d, cx, cy, s=1.0, body=RED, lo=RED_DK, hi=RED_HI):
    w, h = int(13 * s), int(8 * s)
    for k in range(4):                                            # legs
        dy = int((k - 1.5) * 3 * s)
        d.line([(cx - w + 2, cy + dy), (cx - w - int(8 * s), cy + dy + int(4 * s) + k)], fill=lo, width=max(1, int(s)))
        d.line([(cx + w - 2, cy + dy), (cx + w + int(8 * s), cy + dy + int(4 * s) + k)], fill=lo, width=max(1, int(s)))
    for sx in (-1, 1):                                            # claws, raised
        d.line([(cx + sx * (w - 3), cy - h + 2), (cx + sx * (w + int(5 * s)), cy - h - int(5 * s))], fill=body, width=max(2, int(2 * s)))
        ex, ey = cx + sx * (w + int(5 * s)), cy - h - int(6 * s)
        d.ellipse([ex - int(4 * s), ey - int(4 * s), ex + int(4 * s), ey + int(3 * s)], fill=body)
        d.line([(ex, ey - int(2 * s)), (ex + sx * int(3 * s), ey - int(4 * s))], fill=lo)
    d.ellipse([cx - w, cy - h, cx + w, cy + h], fill=body)
    d.arc([cx - w + 2, cy - h + 1, cx + w - 2, cy + h - 3], 190, 350, fill=hi)
    d.arc([cx - w, cy - h, cx + w, cy + h], 10, 170, fill=lo)
    for sx in (-3, 3):
        d.line([(cx + sx, cy - h), (cx + sx, cy - h - 2)], fill=lo)
        d.point((cx + sx, cy - h - 3), fill=INK)


def shop_crab():
    im, d = canvas(3, 4)
    arcade_roof(d)
    d.rectangle([4, 44, 91, 60], fill=WHITE)                      # white board, red kana
    d.rectangle([4, 44, 91, 45], fill=RED); d.rectangle([4, 59, 91, 60], fill=RED)
    kana(d, ('ka', 'ni'), 9, 48, RED_DK)
    kana(d, ('ka', 'ni'), 72, 48, RED_DK)
    d.rectangle([4, 61, 91, 123], fill=rgb('2f3f7a'))             # a blue tiled front
    for y in range(64, 124, 6):
        d.line([(4, y), (91, y)], fill=NAVY)
    for x in range(8, 92, 8):
        d.line([(x, 61), (x, 123)], fill=NAVY)
    d.rectangle([36, 64, 59, 123], fill=WOOD_DK)                  # the entrance (cell 1,3): a pair of
    for x0 in (38, 49):                                           # timber sliding doors, lamplit paper
        d.rectangle([x0, 66, x0 + 9, 123], fill=WOOD)             # panes, under a short noren
        d.line([(x0, 66), (x0, 123)], fill=WOOD_HI)
        d.rectangle([x0 + 2, 82, x0 + 7, 108], fill=WARM)
        d.line([(x0 + 2, 82), (x0 + 7, 82)], fill=WHITE)
        for y in (90, 99):
            d.line([(x0 + 2, y), (x0 + 7, y)], fill=WOOD_LO)
        d.line([(x0 + 4, 82), (x0 + 4, 108)], fill=WOOD_LO)
        d.rectangle([x0 + 1, 112, x0 + 8, 121], fill=WOOD_LO)
    d.line([(48, 66), (48, 123)], fill=WOOD_DK)
    d.point((46, 104), fill=INK); d.point((50, 104), fill=INK)    # the finger pulls
    for i, x in enumerate(range(37, 59, 6)):                      # the noren: white, a red crab mark
        d.rectangle([x, 66, x + 4, 79], fill=WHITE)
        d.line([(x + 4, 66), (x + 4, 79)], fill=SNOW_LO)
        d.rectangle([x + 1, 71, x + 3, 73], fill=RED); d.point((x + 1, 70), fill=RED); d.point((x + 3, 70), fill=RED)
    d.rectangle([36, 64, 59, 65], fill=WOOD_DK)
    for x0, x1 in ((6, 35), (60, 89)):                            # sloping trays of ice
        d.rectangle([x0, 70, x1, 92], fill=DARK)                  # the open window over them
        d.rectangle([x0 + 1, 71, x1 - 1, 91], fill=rgb('5a3b34'))
        d.rectangle([x0 + 3, 73, x1 - 3, 75], fill=AMBER)         # a strip light
        for k, px in enumerate(range(x0 + 3, x1 - 6, 9)):         # price cards hung on a line
            d.rectangle([px, 79, px + 5, 85], fill=AMBER if k % 2 else WHITE)
            d.line([(px + 1, 82), (px + 4, 82)], fill=RED)
        for y in range(93, 113):
            d.line([(x0 - (y - 93) // 7, y), (x1 + (y - 93) // 7, y)], fill=SNOW if (y % 3) else WHITE)
        d.line([(x0 - 2, 112), (x1 + 2, 112)], fill=SNOW_LO)
        d.rectangle([x0 - 2, 113, x1 + 2, 123], fill=STONE_LO)
        d.line([(x0 - 2, 113), (x1 + 2, 113)], fill=STONE)
        crab(d, x0 + 9, 100, 0.45); crab(d, x0 + 22, 105, 0.45, body=rgb('e0764a'), lo=RED_DK)
        d.ellipse([x0 + 16, 95, x0 + 25, 98], fill=rgb('8fa3c0'))  # a fish
        d.point((x0 + 17, 96), fill=INK)
    crab(d, 48, 44, 1.25)                                         # the big crab over the door
    outline(im)
    return im


def shop_drug():
    im, d = canvas(3, 4)
    arcade_roof(d)
    d.rectangle([4, 44, 91, 60], fill=AMBER)                      # a loud yellow board
    d.rectangle([4, 57, 91, 60], fill=RED)
    d.line([(4, 44), (91, 44)], fill=rgb('fde38a'))
    kana(d, ('ku', 'su', 'ri'), 48 - kana_w(3) // 2, 47, RED_DK)
    for x in (12, 78):                                            # a green cross each side
        d.rectangle([x, 49, x + 6, 51], fill=GREEN); d.rectangle([x + 2, 47, x + 4, 53], fill=GREEN)
    d.rectangle([4, 61, 91, 123], fill=WHITE)                     # a bright, glazed front
    d.rectangle([4, 61, 91, 64], fill=RED)
    for x0, x1 in ((7, 35), (60, 88)):
        d.rectangle([x0, 67, x1, 110], fill=STONE_LO)
        d.rectangle([x0 + 1, 68, x1 - 1, 109], fill=rgb('f4f7ff'))
        for sy in (80, 91, 102):                                  # shelves of bottles and boxes
            d.line([(x0 + 1, sy), (x1 - 1, sy)], fill=STONE)
            for k, bx in enumerate(range(x0 + 2, x1 - 2, 4)):
                c = (PINK, CYAN, AMBER, LIME, rgb('3a5fb0'), RED)[(k * 5 + sy) % 6]
                d.rectangle([bx, sy - 5 + (k % 2), bx + 2, sy - 1], fill=c)
        d.rectangle([x0 + 2, 69, x0 + 13, 76], fill=PINK)         # sale posters on the glass
        d.line([(x0 + 4, 72), (x0 + 11, 72)], fill=WHITE)
        d.rectangle([x1 - 12, 100, x1 - 2, 108], fill=AMBER)
        d.line([(x1 - 10, 103), (x1 - 4, 103)], fill=RED); d.line([(x1 - 10, 105), (x1 - 6, 105)], fill=RED)
    glass_door(d, 38, 68, 57, 123, frame=STONE_LO)               # automatic doors (cell 1,3)
    d.rectangle([38, 68, 57, 71], fill=RED)
    for x0 in (8, 66):                                            # wire bins of tissue boxes outside
        d.rectangle([x0, 112, x0 + 20, 123], fill=STONE)
        for x in range(x0, x0 + 21, 4):
            d.line([(x, 112), (x, 123)], fill=STONE_DK)
        d.line([(x0, 117), (x0 + 20, 117)], fill=STONE_DK)
        for k in range(4):
            d.rectangle([x0 + 1 + k * 5, 107, x0 + 4 + k * 5, 111], fill=(CYAN, PINK_HI, LIME, AMBER)[k])
    outline(im)
    return im


# ==============================================================================
# Susukino
# ==============================================================================
def fox_board(d, x0, y0, x1, y1):
    """The crossing's big board: an invented mascot - a winking Hokkaido fox
    raising a mug of beer - on neon rays, in a frame of bulbs."""
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=NIGHT)
    cx, cy = (x0 + x1) // 2 - 12, (y0 + y1) // 2 + 2
    for k in range(16):                                           # rays, pink and gold by turns
        a = math.radians(k * 22.5 + 6)
        for r in range(26, 120):
            px, py = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
            if x0 + 3 <= px <= x1 - 3 and y0 + 3 <= py <= y1 - 3:
                d.point((px, py), fill=PINK if k % 2 else AMBER)
                if r % 3 == 0:
                    d.point((px, py + 1), fill=rgb('7a2f6a') if k % 2 else rgb('8a6a20'))
    d.ellipse([cx - 27, cy - 27, cx + 27, cy + 27], fill=rgb('24377a'))
    d.ellipse([cx - 27, cy - 27, cx + 27, cy + 27], outline=CYAN)
    # the fox: ears, a wedge of a head, white cheeks, one eye shut
    for sx in (-1, 1):
        d.polygon([(cx + sx * 20, cy - 6), (cx + sx * 15, cy - 25), (cx + sx * 4, cy - 13)], fill=FOX)
        d.polygon([(cx + sx * 16, cy - 12), (cx + sx * 15, cy - 25), (cx + sx * 11, cy - 17)], fill=DARK)
    d.polygon([(cx - 22, cy - 5), (cx - 11, cy - 15), (cx + 11, cy - 15), (cx + 22, cy - 5),
               (cx + 10, cy + 12), (cx, cy + 21), (cx - 10, cy + 12)], fill=FOX)
    d.polygon([(cx + 4, cy - 15), (cx + 11, cy - 15), (cx + 22, cy - 5), (cx + 10, cy + 12), (cx + 6, cy + 4)], fill=FOX_LO)
    d.polygon([(cx - 22, cy - 5), (cx - 6, cy + 3), (cx, cy + 21), (cx - 10, cy + 12)], fill=WHITE)
    d.polygon([(cx + 22, cy - 5), (cx + 6, cy + 3), (cx, cy + 21), (cx + 10, cy + 12)], fill=SNOW_LO)
    d.rectangle([cx - 2, cy + 16, cx + 2, cy + 19], fill=INK)                   # nose
    d.line([(cx - 12, cy - 4), (cx - 7, cy - 2)], fill=INK, width=2)            # the wink
    d.line([(cx - 7, cy - 2), (cx - 5, cy - 5)], fill=INK)
    d.rectangle([cx + 6, cy - 6, cx + 10, cy - 2], fill=INK)                    # the open eye
    d.point((cx + 7, cy - 5), fill=WHITE)
    d.line([(cx - 4, cy + 11), (cx, cy + 13)], fill=FOX_LO); d.line([(cx, cy + 13), (cx + 4, cy + 11)], fill=FOX_LO)
    # the mug, held up beside it
    mx, my = cx + 40, cy - 8
    d.rectangle([mx, my, mx + 17, my + 24], fill=AMBER)
    d.rectangle([mx, my, mx + 4, my + 24], fill=rgb('fde38a'))
    d.rectangle([mx + 14, my, mx + 17, my + 24], fill=rgb('c98f1c'))
    for y in range(my + 5, my + 24, 5):
        d.line([(mx + 6, y), (mx + 12, y)], fill=rgb('fde38a'))
    d.ellipse([mx - 3, my - 8, mx + 20, my + 4], fill=WHITE)                    # the head on it
    d.ellipse([mx + 2, my - 11, mx + 12, my - 2], fill=WHITE)
    d.arc([mx + 12, my + 4, mx + 25, my + 20], -90, 90, fill=AMBER, width=3)    # the handle
    d.rectangle([mx - 1, my + 24, mx + 18, my + 26], fill=rgb('c98f1c'))
    d.polygon([(cx + 17, cy + 22), (cx + 22, cy + 13), (cx + 37, cy + 3), (cx + 40, cy + 9),   # the arm
               (cx + 27, cy + 21), (cx + 21, cy + 27)], fill=FOX)
    d.line([(cx + 21, cy + 27), (cx + 27, cy + 21)], fill=FOX_LO); d.line([(cx + 27, cy + 21), (cx + 40, cy + 9)], fill=FOX_LO)
    d.rectangle([cx + 36, cy, cx + 44, cy + 11], fill=DARK)                     # a black-socked paw
    d.rectangle([cx + 37, cy + 1, cx + 43, cy + 10], fill=rgb('4a3a44'))        # gripping the mug
    for y in (cy + 3, cy + 6, cy + 9):
        d.line([(cx + 39, y), (cx + 44, y)], fill=DARK)
    for x in range(x0 + 4, x1 - 2, 6):                                          # the frame of bulbs
        d.point((x, y0 + 1), fill=WARM); d.point((x, y1 - 1), fill=WARM)
    for y in range(y0 + 4, y1 - 2, 6):
        d.point((x0 + 1, y), fill=WARM); d.point((x1 - 1, y), fill=WARM)


def neon_corner():
    im, d = canvas(5, 7)                 # 160 x 224
    # ---- the block: a dark front, a narrower shaded side wall on the right -------
    d.rectangle([12, 22, 151, 219], fill=rgb('3a3550'))
    d.rectangle([126, 22, 151, 219], fill=DARK)
    d.line([(12, 22), (12, 219)], fill=rgb('5a5478'))
    d.rectangle([10, 18, 153, 23], fill=STONE_LO)
    d.line([(10, 18), (153, 18)], fill=STONE)
    d.rectangle([20, 8, 44, 17], fill=STONE_DK); d.rectangle([98, 10, 116, 17], fill=STONE_DK)   # roof plant
    snow_cap(d, 20, 44, 5, 3, seed=1); snow_cap(d, 98, 116, 7, 3, seed=2)
    snow_cap(d, 10, 153, 14, 4, seed=6)
    # ---- the mascot board, three floors tall -------------------------------------
    fox_board(d, 15, 27, 123, 103)
    # ---- the boards stacked below it ----------------------------------------------
    d.rectangle([15, 106, 123, 124], fill=INK)                    # ススキノ, pink on night blue
    d.rectangle([16, 107, 122, 123], fill=NIGHT)
    kana(d, ('su', 'su', 'ki', 'no'), 69 - kana_w(4, 2) // 2, 108, PINK, scale=2)
    d.rectangle([15, 127, 66, 141], fill=AMBER)                   # yellow, red letters
    d.rectangle([15, 127, 66, 128], fill=rgb('fde38a')); d.rectangle([15, 140, 66, 141], fill=rgb('c98f1c'))
    kana(d, ('ra', 'bar', 'me', 'n'), 41 - kana_w(4) // 2, 131, RED_DK)
    d.rectangle([69, 127, 123, 141], fill=rgb('1f6f80'))          # cyan
    d.rectangle([69, 127, 123, 128], fill=CYAN)
    text(d, 'BAR', 74, 131, CYAN); star(d, 110, 134, 5, WHITE)
    d.rectangle([15, 144, 123, 146], fill=STONE_DK)
    # ---- two floors of lit windows, the side wall's upright signs ----------------
    for k, y in enumerate((148, 160)):
        for i, x in enumerate(range(18, 118, 15)):
            c = (WARM, PINK_HI, WARM, CYAN, WARM, rgb('c9b4f0'), WARM)[(i + k * 3) % 7]
            d.rectangle([x, y, x + 11, y + 9], fill=INK)
            d.rectangle([x + 1, y + 1, x + 10, y + 8], fill=c)
            d.line([(x + 5, y + 1), (x + 5, y + 8)], fill=INK)
            d.line([(x + 1, y + 1), (x + 10, y + 1)], fill=WHITE)
    for j, (c, lo) in enumerate(((PINK, rgb('7a2f6a')), (LIME, rgb('2f6a3a')), (CYAN, rgb('1f6f80')))):
        y = 30 + j * 50
        d.rectangle([130, y, 147, y + 44], fill=INK)
        d.rectangle([131, y + 1, 146, y + 43], fill=lo)
        d.rectangle([131, y + 1, 132, y + 43], fill=c)
        if j == 0:
            kana(d, ('ka', 'ra', 'o', 'ke'), 136, y + 6, WHITE, vertical=True)
        elif j == 1:
            text(d, 'SNACK', 137, y + 3, WHITE, vertical=True)
        else:
            text(d, 'SUSHI', 137, y + 3, WHITE, vertical=True)
    # ---- the street floor: a lit glass corner shop, the door in the middle -------
    d.rectangle([12, 176, 151, 180], fill=RED)                    # a red fascia right round
    d.line([(12, 176), (151, 176)], fill=RED_HI); d.rectangle([126, 177, 151, 180], fill=RED_DK)
    snow_cap(d, 12, 151, 173, 2, seed=11)
    d.rectangle([12, 181, 151, 214], fill=DARK)
    for x0, x1 in ((16, 60), (100, 123)):
        d.rectangle([x0, 184, x1, 212], fill=WARM)
        d.line([(x0, 184), (x1, 184)], fill=WHITE)
        for x in range(x0 + 11, x1, 11):
            d.line([(x, 184), (x, 212)], fill=DARK)
        d.rectangle([x0, 204, x1, 212], fill=CREAM_LO)
        for k, x in enumerate(range(x0 + 2, x1 - 3, 5)):
            d.rectangle([x, 198, x + 2, 203], fill=(RED, GREEN_HI, PINK, CYAN_LO)[k % 4])
    d.rectangle([129, 184, 148, 212], fill=rgb('8a7a4e'))         # the side window, in shade
    d.line([(138, 184), (138, 212)], fill=DARK)
    glass_door(d, 66, 184, 79, 214, frame=INK); glass_door(d, 80, 184, 93, 214, frame=INK)   # door (cell 2,6)
    d.rectangle([10, 214, 153, 219], fill=STONE_LO)
    d.line([(10, 214), (153, 214)], fill=STONE)
    drift(d, 8, 26, 219, 4, seed=3); drift(d, 134, 155, 219, 5, seed=8)
    outline(im)
    return im


def ramen_gate():
    im, d = canvas(3, 3)                 # 96 x 96
    for x in (7, 81):                                             # red posts on stone feet
        d.rectangle([x, 30, x + 7, 90], fill=RED)
        d.line([(x, 30), (x, 90)], fill=RED_HI)
        d.rectangle([x + 5, 30, x + 7, 90], fill=RED_DK)
        d.rectangle([x - 2, 87, x + 9, 93], fill=STONE_DK)
        d.line([(x - 2, 87), (x + 9, 87)], fill=STONE_LO)
    # the little tiled roof over the board
    rows = [(y, 4 - (y - 6), 91 + (y - 6)) for y in range(6, 13)]
    tiles(d, rows, rgb('3b4a66'), NAVY, step=3)
    d.line([(0, 13), (95, 13)], fill=INK)
    snow_cap(d, 4, 91, 3, 3, seed=5)
    snow_cap(d, 0, 12, 9, 2, seed=1); snow_cap(d, 84, 95, 9, 2, seed=3)
    # the board: yellow, a red frame, ラーメン and a bowl each side
    d.rectangle([3, 14, 92, 33], fill=RED)
    d.rectangle([5, 16, 90, 31], fill=AMBER)
    d.line([(5, 16), (90, 16)], fill=rgb('fde38a'))
    kana(d, ('ra', 'bar', 'me', 'n'), 48 - kana_w(4) // 2, 20, RED_DK)
    for x in (10, 76):
        d.pieslice([x, 16, x + 10, 30], 0, 180, fill=WHITE)
        d.line([(x, 23), (x + 10, 23)], fill=RED)
        d.line([(x + 3, 20), (x + 3, 18)], fill=WHITE); d.line([(x + 7, 20), (x + 7, 18)], fill=WHITE)
    d.rectangle([3, 34, 92, 35], fill=WOOD_DK)                    # the rail the lanterns hang from
    for i, x in enumerate(range(16, 76, 13)):
        d.line([(x + 4, 36), (x + 4, 37)], fill=INK)
        if i % 2:
            lantern(d, x, 38, 9, 13, body=WHITE, hi=WHITE, lo=CREAM_LO)
            d.rectangle([x + 3, 43, x + 5, 46], fill=RED)
        else:
            lantern(d, x, 38, 9, 13)
    drift(d, 0, 18, 95, 4, seed=2); drift(d, 77, 95, 95, 4, seed=9)
    outline(im)
    return im


def neon_lanterns():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([15, 6, 16, 60], fill=STONE_LO)
    d.line([(15, 6), (15, 60)], fill=STONE)
    d.rectangle([12, 59, 19, 61], fill=STONE_DK)
    boards = ((4, 8, PINK, rgb('7a2f6a')), (16, 21, CYAN, rgb('1f6f80')), (4, 34, AMBER, rgb('8a6a20')))
    for x, y, c, lo in boards:
        d.rectangle([x, y, x + 11, y + 11], fill=INK)
        d.rectangle([x + 1, y + 1, x + 10, y + 10], fill=lo)
        d.rectangle([x + 1, y + 1, x + 10, y + 10], outline=c)
        d.rectangle([x + 4, y + 3, x + 7, y + 8], fill=c)
        d.point((x + 5, y + 4), fill=WHITE)
    snow_cap(d, 4, 15, 5, 2, seed=1)
    snow_cap(d, 13, 18, 3, 2, seed=3)
    drift(d, 8, 23, 62, 2, seed=1)
    outline(im)
    return im


def karaoke():
    im, d = canvas(4, 5)                 # 128 x 160
    d.rectangle([6, 24, 121, 155], fill=PURPLE)
    d.line([(6, 24), (6, 155)], fill=PURPLE_HI)
    d.rectangle([112, 24, 121, 155], fill=PURPLE_LO)
    for y in range(30, 110, 6):                                   # the cladding's ribs
        d.line([(7, y), (111, y)], fill=PURPLE_LO)
    d.rectangle([4, 20, 123, 25], fill=STONE_LO); d.line([(4, 20), (123, 20)], fill=STONE)
    snow_cap(d, 4, 123, 16, 4, seed=4)
    # ---- the sign: カラオケ in pink, a microphone, notes ---------------------------
    d.rectangle([10, 29, 105, 51], fill=INK)
    d.rectangle([11, 30, 104, 50], fill=NIGHT)
    d.rectangle([11, 30, 104, 50], outline=PINK)
    kana(d, ('ka', 'ra', 'o', 'ke'), 16, 33, PINK_HI, scale=2)
    d.ellipse([84, 32, 93, 41], fill=STONE); d.point((86, 34), fill=WHITE)      # the microphone
    d.line([(84, 36), (93, 36)], fill=STONE_DK); d.line([(88, 32), (88, 41)], fill=STONE_DK)
    d.line([(88, 41), (92, 48)], fill=CYAN, width=2)
    for nx, ny in ((97, 34), (99, 43)):                                           # notes
        d.rectangle([nx, ny + 4, nx + 2, ny + 5], fill=AMBER); d.line([(nx + 2, ny), (nx + 2, ny + 4)], fill=AMBER)
        d.point((nx + 3, ny + 1), fill=AMBER)
    # ---- two floors of karaoke rooms, each lit its own colour --------------------
    cols = (PINK_HI, CYAN, WARM, LIME, rgb('c9b4f0'), WARM, PINK_HI, CYAN)
    for k, y in enumerate((57, 81)):
        for i, x in enumerate(range(11, 100, 24)):
            c = cols[(i + k * 5) % 8]
            d.rectangle([x, y, x + 19, y + 17], fill=INK)
            d.rectangle([x + 1, y + 1, x + 18, y + 16], fill=c)
            d.line([(x + 1, y + 1), (x + 18, y + 1)], fill=WHITE)
            d.line([(x + 10, y + 1), (x + 10, y + 16)], fill=INK)
            hx = x + 3 + (i * 5 + k * 3) % 5                                     # someone singing
            d.rectangle([hx, y + 9, hx + 3, y + 16], fill=PURPLE_LO)
            d.rectangle([hx, y + 6, hx + 3, y + 9], fill=DARK)
            d.line([(hx + 4, y + 10), (hx + 6, y + 8)], fill=DARK)
            d.rectangle([x, y + 18, x + 19, y + 19], fill=PURPLE_LO)
    d.rectangle([108, 54, 120, 104], fill=INK)                    # the upright sign on the corner
    d.rectangle([109, 55, 119, 103], fill=AMBER)
    d.line([(109, 55), (109, 103)], fill=rgb('fde38a'))
    text(d, 'BAR', 112, 60, RED_DK, vertical=True)
    star(d, 114, 93, 5, RED_DK)
    # ---- the street floor: a striped awning, the bar's door, a menu window -------
    for y in range(106, 115):
        w = y - 106
        for x in range(6 - w // 2, 122 + w // 2):
            d.point((x, y), fill=PINK if (x // 6) % 2 else WHITE)
    d.line([(2, 115), (125, 115)], fill=PURPLE_LO)
    for x in range(2, 126):
        if (x // 3) % 2 == 0:
            d.point((x, 116), fill=PINK if (x // 6) % 2 else WHITE)
    snow_cap(d, 6, 121, 103, 3, seed=7)
    d.rectangle([6, 117, 121, 155], fill=DARK)
    d.rectangle([38, 122, 57, 155], fill=WOOD_DK)                 # the bar's door (cell 1,4)
    d.rectangle([40, 124, 55, 155], fill=WOOD_LO)
    d.line([(40, 124), (40, 155)], fill=WOOD)
    d.ellipse([44, 128, 51, 135], fill=WARM); d.ellipse([44, 128, 51, 135], outline=WOOD_DK)
    d.rectangle([52, 140, 53, 142], fill=GOLD)
    d.rectangle([10, 122, 32, 150], fill=WARM)                    # a window of bottles
    d.line([(10, 122), (32, 122)], fill=WHITE)
    for sy in (133, 144):
        d.line([(10, sy), (32, sy)], fill=WOOD_LO)
        for k, bx in enumerate(range(12, 31, 4)):
            d.rectangle([bx, sy - 6, bx + 1, sy - 1], fill=(GREEN, RED, rgb('8a6a20'), CYAN_LO, PURPLE)[(k + sy) % 5])
    d.rectangle([64, 122, 116, 150], fill=rgb('5a3b34'))          # the menu boards
    for k, x in enumerate(range(67, 112, 17)):
        d.rectangle([x, 125, x + 13, 147], fill=WHITE if k != 1 else AMBER)
        for y in range(129, 146, 4):
            d.line([(x + 2, y), (x + 10 - (y % 3), y)], fill=RED_DK if y == 129 else STONE_LO)
    lantern(d, 59, 120, 7, 10)
    d.rectangle([4, 151, 123, 155], fill=STONE_LO); d.line([(4, 151), (123, 151)], fill=STONE)
    d.rectangle([38, 151, 57, 155], fill=WOOD_DK)
    drift(d, 3, 20, 159, 5, seed=4); drift(d, 100, 124, 159, 5, seed=1)
    outline(im)
    return im


# ==============================================================================
# Odori Park
# ==============================================================================
def snow_block(d, x0, y0, x1, y1, joints=True):
    """A block of packed snow: lit top edge, a shaded right end, saw marks."""
    d.rectangle([x0, y0, x1, y1], fill=SNOW)
    d.line([(x0, y0), (x1, y0)], fill=WHITE)
    w = max(2, (x1 - x0) // 9)
    d.rectangle([x1 - w, y0 + 1, x1, y1], fill=SNOW_SH)
    d.line([(x0, y1), (x1, y1)], fill=SNOW_SH)
    if joints:
        for y in range(y0 + 7, y1, 8):
            d.line([(x0 + 1, y), (x1 - 1, y)], fill=SNOW_LO)
            for x in range(x0 + 6 + (y // 8 % 2) * 8, x1 - 2, 16):
                d.line([(x, y - 7), (x, y)], fill=SNOW_LO)


def snow_roof(d, cx, y, half, h, flare=6):
    """A carved castle roof: a hipped slab whose eaves flare out, dark under."""
    for i in range(h):
        t = i / max(1, h - 1)
        w = int(half - flare + flare * t * t + (half - flare) * 0.0)
        ww = int((half - flare) * (0.55 + 0.45 * t)) + int(flare * t * t)
        d.line([(cx - ww, y + i), (cx + ww, y + i)], fill=WHITE if i < 2 else SNOW)
        d.line([(cx + ww // 2, y + i), (cx + ww, y + i)], fill=SNOW_LO)
        if i % 3 == 2:
            d.line([(cx - ww + 1, y + i), (cx + ww // 2 - 1, y + i)], fill=SNOW_LO)
    d.line([(cx - half, y + h), (cx + half, y + h)], fill=SNOW_DK)
    d.line([(cx - half + 3, y + h + 1), (cx + half - 3, y + h + 1)], fill=SNOW_SH)
    d.point((cx - half, y + h - 1), fill=WHITE); d.point((cx - half - 1, y + h - 2), fill=WHITE)   # upturned tips
    d.point((cx + half, y + h - 1), fill=SNOW_LO); d.point((cx + half + 1, y + h - 2), fill=SNOW_LO)


def snow_castle():
    im, d = canvas(5, 4)                 # 160 x 128
    cx = 80
    # ---- the plinth: a stepped block of packed snow, carved as a stone base -----
    snow_block(d, 4, 100, 155, 123)
    snow_block(d, 16, 88, 143, 100)
    # ---- the keep: three storeys, each under its own roof ------------------------
    tiers = ((48, 68, 88), (36, 48, 64), (24, 30, 44))            # (half width, wall top, wall bottom)
    for half, top, bot in tiers:
        d.rectangle([cx - half, top, cx + half, bot], fill=SNOW)
        d.rectangle([cx + half * 2 // 3, top, cx + half, bot], fill=SNOW_SH)
        d.line([(cx - half, top), (cx - half, bot)], fill=WHITE)
        for x in range(cx - half + 6, cx + half - 6, 12):         # carved windows
            d.rectangle([x, top + 5, x + 4, min(bot - 3, top + 12)], fill=SNOW_DK)
            d.line([(x, top + 5), (x + 4, top + 5)], fill=SNOW_DK)
    snow_roof(d, cx, 58, 58, 9, 8)
    snow_roof(d, cx, 39, 45, 8, 7)
    # the top gable, with its two shachi
    for y in range(8, 30):
        w = int((y - 8) * 34 / 21)
        d.line([(cx - w, y), (cx + w, y)], fill=SNOW)
        d.line([(cx + w // 3, y), (cx + w, y)], fill=SNOW_LO)
        d.point((cx - w, y), fill=WHITE)
        if y % 4 == 3 and w > 4:
            d.line([(cx - w + 2, y), (cx + w // 3 - 1, y)], fill=SNOW_LO)
    d.line([(cx - 36, 30), (cx + 36, 30)], fill=SNOW_DK)
    d.polygon([(cx - 4, 22), (cx, 14), (cx + 4, 22)], fill=SNOW_SH)             # the gable's vent
    for sx in (-1, 1):
        d.rectangle([cx + sx * 3 - 1, 3, cx + sx * 3 + 1, 8], fill=WHITE if sx < 0 else SNOW_LO)
        d.point((cx + sx * 5, 3), fill=WHITE if sx < 0 else SNOW_LO)
    # ---- a turret at each end of the base -----------------------------------------
    for tx in (22, 138):
        d.rectangle([tx - 10, 74, tx + 10, 88], fill=SNOW)
        d.rectangle([tx + 4, 74, tx + 10, 88], fill=SNOW_SH)
        d.rectangle([tx - 3, 78, tx, 84], fill=SNOW_SH)
        snow_roof(d, tx, 64, 14, 8, 4)
    # the gate in the base, and steps cut up to it
    d.rectangle([cx - 9, 74, cx + 9, 88], fill=SNOW_SH)
    d.pieslice([cx - 9, 66, cx + 9, 82], 180, 360, fill=SNOW_SH)
    d.rectangle([cx - 6, 77, cx + 6, 88], fill=SNOW_DK)
    d.pieslice([cx - 6, 70, cx + 6, 84], 180, 360, fill=SNOW_DK)
    for i, y in enumerate(range(89, 123, 5)):
        d.rectangle([cx - 10 - i, y, cx + 10 + i, y + 4], fill=WHITE if i % 2 == 0 else SNOW)
        d.line([(cx - 10 - i, y + 4), (cx + 10 + i, y + 4)], fill=SNOW_SH)
    # ---- the festival's board, and rope posts in front ----------------------------
    d.rectangle([118, 104, 146, 119], fill=WOOD)
    d.rectangle([119, 105, 145, 118], fill=CREAM)
    d.line([(122, 108), (142, 108)], fill=RED); d.line([(122, 112), (140, 112)], fill=WOOD_DK)
    d.line([(122, 115), (136, 115)], fill=WOOD_DK)
    d.rectangle([131, 119, 132, 125], fill=WOOD_LO)
    for x in (8, 34, 60):
        d.rectangle([x, 114, x + 1, 125], fill=RED)
        d.point((x, 113), fill=WHITE); d.point((x + 1, 113), fill=WHITE)
    for a, b in ((9, 34), (35, 60)):
        for x in range(a, b):
            d.point((x, 117 + int(2 * math.sin(math.pi * (x - a) / (b - a)))), fill=AMBER)
    outline(im)
    return im


def snow_tanuki():
    im, d = canvas(2, 3)                 # 64 x 96
    cx = 32
    snow_block(d, 6, 78, 57, 92, joints=False)
    d.line([(8, 85), (50, 85)], fill=SNOW_LO)
    # the tail, behind
    d.ellipse([44, 56, 60, 78], fill=SNOW_LO); d.ellipse([46, 58, 56, 70], fill=SNOW_SH)
    # the body: a big round belly
    d.ellipse([cx - 20, 40, cx + 20, 80], fill=SNOW)
    d.pieslice([cx - 20, 40, cx + 20, 80], -75, 75, fill=SNOW_LO)
    d.ellipse([cx - 12, 48, cx + 10, 74], fill=WHITE)
    d.arc([cx - 12, 48, cx + 10, 74], 20, 160, fill=SNOW_LO)
    d.point((cx - 1, 62), fill=SNOW_DK); d.point((cx, 62), fill=SNOW_DK)        # the navel
    for sx in (-1, 1):                                                           # feet
        d.ellipse([cx + sx * 12 - 6, 73, cx + sx * 12 + 6, 81], fill=SNOW if sx < 0 else SNOW_LO)
        d.line([(cx + sx * 12 - 5, 81), (cx + sx * 12 + 5, 81)], fill=SNOW_SH)
    d.ellipse([cx - 25, 50, cx - 15, 66], fill=SNOW)                             # an arm with a flask
    d.rectangle([cx - 27, 60, cx - 20, 72], fill=WHITE); d.rectangle([cx - 25, 56, cx - 22, 60], fill=WHITE)
    d.line([(cx - 20, 61), (cx - 20, 72)], fill=SNOW_LO); d.line([(cx - 27, 72), (cx - 20, 72)], fill=SNOW_SH)
    d.ellipse([cx + 15, 50, cx + 25, 66], fill=SNOW_LO)
    # the head and the straw hat pushed back on it
    tanuki_face(d, cx, 32, 13, snow=True)
    for y in range(6, 20):
        w = int(3 + (y - 6) * 24 / 13)
        d.line([(cx - w, y), (cx + w, y)], fill=WHITE if y < 9 else SNOW)
        d.line([(cx + w // 3, y), (cx + w, y)], fill=SNOW_LO)
        if y % 3 == 0:
            d.line([(cx - w + 1, y), (cx + w // 3, y)], fill=SNOW_LO)
    d.line([(cx - 27, 20), (cx + 27, 20)], fill=SNOW_DK)
    d.line([(cx - 22, 21), (cx + 22, 21)], fill=SNOW_SH)
    outline(im)
    return im


STALLS = {     # kind: (stripe, stripe shade, cloth)
    'corn': (AMBER, rgb('c98f1c'), RED),
    'drinks': (rgb('3a5fb0'), NAVY, rgb('3a5fb0')),
}


def stall(kind):
    stripe, stripe_lo, cloth = STALLS[kind]
    im, d = canvas(3, 3)                 # 96 x 96
    # ---- the lit inside -----------------------------------------------------------
    d.rectangle([10, 34, 85, 66], fill=DARK)
    d.rectangle([10, 46, 85, 66], fill=rgb('5a3b34'))
    d.rectangle([46, 36, 49, 39], fill=WARM)                      # the bulb
    # ---- a peaked tent: striped canvas, snow on the ridge ------------------------
    for y in range(8, 30):
        t = (y - 8) / 21
        x0, x1 = int(40 - 36 * t), int(55 + 36 * t)
        for x in range(x0, x1 + 1):
            band = int((x - 47.5) / (3 + 5 * t) + 40) % 2
            c = stripe if band else WHITE
            if x > 48 + 20 * t:
                c = stripe_lo if band else SNOW_LO
            d.point((x, y), fill=c)
    d.rectangle([3, 30, 92, 34], fill=WHITE)                      # the valance
    for x in range(3, 93):
        if (x // 6) % 2:
            d.line([(x, 30), (x, 34)], fill=stripe)
        if (x // 3) % 2 == 0:
            d.point((x, 35), fill=stripe if (x // 6) % 2 else WHITE)
    for x in range(32, 64):                                       # snow lying on the peak
        t = abs(x - 47.5) / 16
        d.line([(x, 5 + int(5 * t)), (x, 9 + int(8 * t) + (x % 5 == 0))], fill=SNOW)
    for x0, x1 in ((6, 22), (74, 90)):
        snow_cap(d, x0, x1, 26, 2, seed=x0)
    for x in (8, 86):                                             # poles
        d.rectangle([x, 35, x + 1, 90], fill=STONE)
        d.line([(x + 1, 35), (x + 1, 90)], fill=STONE_LO)
    # ---- the hanging board ---------------------------------------------------------
    d.rectangle([28, 37, 67, 49], fill=WHITE if kind == 'corn' else AMBER)
    d.rectangle([28, 37, 67, 49], outline=cloth if kind == 'corn' else NAVY)
    if kind == 'corn':
        kana(d, ('ko', 'bar', 'n'), 48 - kana_w(3) // 2, 40, RED_DK)
    else:
        text(d, 'HOT', 34, 40, NAVY)
        d.rectangle([54, 42, 60, 47], fill=WHITE); d.rectangle([54, 42, 60, 47], outline=NAVY)   # a cup
        d.point((62, 44), fill=NAVY); d.point((56, 39), fill=NAVY); d.point((58, 40), fill=NAVY)
    # ---- the counter and what is on it ---------------------------------------------
    d.rectangle([6, 62, 89, 66], fill=WOOD_HI)
    d.line([(6, 66), (89, 66)], fill=WOOD_LO)
    if kind == 'corn':
        d.rectangle([16, 54, 58, 61], fill=STONE_DK)              # the charcoal grill
        d.line([(16, 54), (58, 54)], fill=STONE_LO)
        for x in range(18, 57, 3):
            d.point((x, 60), fill=RED_HI if (x // 3) % 2 else AMBER)
        for x in range(19, 55, 9):                                # cobs, turning
            d.rectangle([x, 51, x + 6, 54], fill=AMBER)
            d.line([(x, 51), (x + 6, 51)], fill=rgb('fde38a'))
            d.point((x + 2, 53), fill=rgb('c98f1c')); d.point((x + 5, 52), fill=rgb('c98f1c'))
            d.line([(x + 7, 52), (x + 8, 52)], fill=GREEN_HI)
        for sx, sy in ((24, 47), (33, 45), (42, 48), (50, 46)):   # smoke
            d.point((sx, sy), fill=WHITE); d.point((sx + 1, sy - 2), fill=SNOW_LO)
        d.rectangle([66, 52, 80, 61], fill=CREAM)                 # a tub of butter
        d.rectangle([66, 52, 80, 54], fill=AMBER)
    else:
        d.rectangle([14, 44, 34, 61], fill=STONE)                 # the urn
        d.rectangle([14, 44, 18, 61], fill=WHITE); d.rectangle([29, 45, 34, 61], fill=STONE_LO)
        d.rectangle([12, 42, 36, 45], fill=STONE_DK)
        d.rectangle([22, 54, 26, 57], fill=RED)
        for sx, sy in ((19, 39), (24, 37), (29, 40), (25, 34)):   # steam
            d.point((sx, sy), fill=WHITE)
        for k, x in enumerate(range(42, 82, 8)):                  # paper cups in a row
            d.rectangle([x, 55, x + 4, 61], fill=WHITE)
            d.line([(x, 57), (x + 4, 57)], fill=(RED, rgb('3a5fb0'))[k % 2])
            d.point((x + 2, 52), fill=WHITE)
    # ---- the counter's cloth, striped, to the ground -------------------------------
    d.rectangle([8, 67, 87, 90], fill=WHITE)
    for x in range(8, 88):
        if (x // 5) % 2:
            d.line([(x, 67), (x, 90)], fill=cloth)
    d.line([(8, 67), (87, 67)], fill=WOOD_DK)
    d.rectangle([8, 88, 87, 90], fill=STONE_LO)
    d.rectangle([70, 67, 87, 90], fill=CREAM_DK if kind == 'corn' else NAVY)   # the shaded end
    for x in range(70, 88):
        if (x // 5) % 2 == 0:
            d.line([(x, 68), (x, 87)], fill=SNOW_LO)
    drift(d, 2, 22, 93, 5, seed=3 if kind == 'corn' else 6); drift(d, 72, 94, 93, 4, seed=5)
    outline(im)
    return im


# ==============================================================================
# Streetcar
# ==============================================================================
def streetcar():
    im, d = canvas(5, 3)                 # 160 x 96
    # ---- the pantograph ------------------------------------------------------------
    d.line([(66, 12), (94, 12)], fill=STONE_DK, width=2)
    d.line([(70, 13), (88, 34)], fill=STONE_DK); d.line([(90, 13), (72, 34)], fill=STONE_DK)
    d.rectangle([68, 33, 92, 35], fill=STONE_LO)
    # ---- the body: cream over green, rounded ends ----------------------------------
    d.rounded_rectangle([3, 36, 156, 86], radius=7, fill=CREAM)
    d.rectangle([3, 64, 156, 86], fill=TRAM)
    d.rounded_rectangle([3, 70, 156, 86], radius=5, fill=TRAM)
    d.line([(4, 64), (155, 64)], fill=TRAM_HI)
    d.rectangle([3, 66, 156, 67], fill=WHITE)                     # the waist stripe
    d.rectangle([4, 80, 155, 86], fill=TRAM_LO)
    d.rounded_rectangle([5, 34, 154, 42], radius=4, fill=STONE)   # the roof
    d.line([(8, 34), (151, 34)], fill=WHITE)
    d.rectangle([30, 30, 60, 34], fill=STONE_LO); d.rectangle([100, 30, 130, 34], fill=STONE_LO)   # roof boxes
    snow_cap(d, 30, 60, 27, 3, seed=1); snow_cap(d, 100, 130, 27, 3, seed=5)
    snow_cap(d, 8, 28, 31, 3, seed=2); snow_cap(d, 132, 151, 31, 3, seed=6)
    # ---- windows and the two folding doors ------------------------------------------
    for x in (30, 48, 66, 84, 102, 120):
        d.rectangle([x, 46, x + 14, 61], fill=GLASS_DK)
        d.rectangle([x + 1, 47, x + 13, 60], fill=GLASS)
        d.line([(x + 1, 47), (x + 13, 47)], fill=GLASS_HI)
        d.line([(x + 2, 49), (x + 5, 49)], fill=GLASS_HI)
        d.line([(x + 1, 52), (x + 13, 52)], fill=GLASS_DK)
    for x in (14, 138):
        d.rectangle([x, 45, x + 11, 82], fill=TRAM_LO)
        d.rectangle([x + 1, 47, x + 5, 66], fill=GLASS); d.rectangle([x + 7, 47, x + 10, 66], fill=GLASS)
        d.line([(x + 1, 47), (x + 5, 47)], fill=GLASS_HI); d.line([(x + 7, 47), (x + 10, 47)], fill=GLASS_HI)
        d.rectangle([x + 1, 69, x + 10, 81], fill=TRAM)
    d.rectangle([5, 47, 10, 61], fill=GLASS); d.line([(5, 47), (10, 47)], fill=GLASS_HI)      # the cab windows
    d.rectangle([150, 47, 154, 61], fill=GLASS_DK)
    d.rectangle([58, 43, 101, 45], fill=INK)                      # the destination blind
    d.rectangle([4, 72, 6, 75], fill=WARM); d.rectangle([154, 72, 155, 75], fill=RED)        # lamps
    d.ellipse([73, 69, 86, 82], fill=WHITE)                       # the pioneers' red star on the side
    star(d, 79.5, 75.5, 5, RED, RED_LO)
    # ---- skirts, bogies, the fender -------------------------------------------------
    d.rectangle([10, 86, 149, 89], fill=DARK)
    for x in (22, 40, 112, 130):
        d.ellipse([x, 84, x + 9, 93], fill=STONE_DK)
        d.ellipse([x + 3, 87, x + 6, 90], fill=STONE_LO)
    d.rectangle([20, 88, 52, 89], fill=STONE_DK); d.rectangle([110, 88, 142, 89], fill=STONE_DK)
    d.rectangle([1, 84, 8, 86], fill=STONE_LO); d.rectangle([151, 84, 158, 86], fill=STONE_DK)
    outline(im)
    return im


# ==============================================================================
# Ground
# ==============================================================================
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')


def arcade_brick(role):
    """Basket-weave brick paving; a stone kerb on the sides the role names."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    tones = (BRICK, BRICK, rgb('c56e55'), BRICK_LO, rgb('ad5843'))
    for y in range(32):
        for x in range(32):
            bx, by = x // 8, y // 8
            horiz = (bx + by) % 2 == 0
            if horiz:
                half = (y % 8) // 4
                joint = (y % 4 == 3) or (x % 8 == 7)
            else:
                half = (x % 8) // 4
                joint = (x % 4 == 3) or (y % 8 == 7)
            if joint:
                c = BRICK_DK
            else:
                c = tones[(bx * 3 + by * 5 + half * 2) % 5]
                lead = (y % 4 == 0) if horiz else (x % 4 == 0)
                if lead and (bx + by * 2 + half) % 3 == 0:
                    c = BRICK_HI
            px[x, y] = c
    d = ImageDraw.Draw(im)
    side = {'n': 'n' in role.split('-')[-1] and role != 'center', 's': False, 'e': False, 'w': False}
    tail = role.split('-')[-1] if role != 'center' else ''
    for s in 'nsew':
        side[s] = s in tail
    kerb = {'n': [0, 0, 31, 2], 's': [0, 29, 31, 31], 'w': [0, 0, 2, 31], 'e': [29, 0, 31, 31]}
    for s in 'nsew':
        if not side[s]:
            continue
        x0, y0, x1, y1 = kerb[s]
        d.rectangle([x0, y0, x1, y1], fill=STONE)
        if s in 'ns':
            for x in range(0, 32, 8):
                d.line([(x + (4 if s == 's' else 0), y0), (x + (4 if s == 's' else 0), y1)], fill=STONE_LO)
            d.line([(0, y0 if s == 'n' else y1), (31, y0 if s == 'n' else y1)], fill=STONE_DK)
            d.line([(0, y1 if s == 'n' else y0), (31, y1 if s == 'n' else y0)], fill=WHITE if s == 'n' else STONE_LO)
        else:
            for y in range(0, 32, 8):
                d.line([(x0, y + (4 if s == 'e' else 0)), (x1, y + (4 if s == 'e' else 0))], fill=STONE_LO)
            d.line([(x0 if s == 'w' else x1, 0), (x0 if s == 'w' else x1, 31)], fill=STONE_DK)
            d.line([(x1 if s == 'w' else x0, 0), (x1 if s == 'w' else x0, 31)], fill=WHITE if s == 'w' else STONE_LO)
    return im


# ==============================================================================
# Station front (second pass): the station itself, the red-brick Akarenga, a konbini
# ==============================================================================
def station_front():
    im, d = canvas(10, 7)                # 320 x 224
    cx = 160
    # ---- the tower behind the east wing (a stub of it: the rest is off the top) --
    d.rectangle([222, 16, 291, 110], fill=STONE)
    d.line([(222, 16), (222, 110)], fill=WHITE)
    d.rectangle([284, 17, 291, 110], fill=STONE_LO)
    glazing(d, 227, 22, 281, 108, cw=6, ch=10, lit={(2, 3), (6, 5), (4, 1), (1, 6), (7, 2)})
    for x in (238, 250, 262, 274):                                # stone fins up the glass
        d.line([(x, 22), (x, 108)], fill=STONE)
    d.rectangle([220, 12, 293, 17], fill=WHITE)                   # its crown
    d.line([(220, 17), (293, 17)], fill=STONE_LO)
    d.rectangle([286, 13, 293, 17], fill=STONE)
    d.rectangle([256, 2, 257, 11], fill=STONE_DK)                 # a mast
    d.point((256, 1), fill=RED); d.point((257, 1), fill=RED)
    snow_cap(d, 220, 293, 8, 4, seed=5)
    # ---- the two stone wings ------------------------------------------------------
    d.rectangle([6, 100, 313, 218], fill=STONE)
    for y in range(104, 170, 11):                                 # the cladding's courses
        d.line([(6, y), (313, y)], fill=rgb('a9b4bb'))
    for x in range(6, 314, 20):
        d.line([(x, 100), (x, 170)], fill=rgb('a9b4bb'))
    d.rectangle([4, 96, 315, 100], fill=WHITE)                    # the parapet
    d.line([(4, 100), (315, 100)], fill=STONE_LO)
    d.rectangle([306, 101, 313, 218], fill=STONE_LO)              # the shaded east end
    for x0, x1 in ((14, 103), (216, 301)):                        # three ribbons of windows a side
        for k, y0 in enumerate((106, 128, 150)):
            glazing(d, x0, y0, x1, y0 + 13, cw=8, ch=13,
                    lit=({(2, 0), (7, 0)}, {(4, 0)}, {(1, 0), (5, 0), (9, 0)})[k])
            d.line([(x0, y0 + 14), (x1, y0 + 14)], fill=STONE_LO)
    # ---- the glazed hall, four storeys of glass, with the star clock --------------
    d.rectangle([110, 44, 209, 218], fill=STONE)
    d.rectangle([110, 44, 209, 48], fill=WHITE)
    d.rectangle([110, 44, 114, 218], fill=WHITE)                  # lit pier
    d.rectangle([205, 49, 209, 218], fill=STONE_LO)               # shaded pier
    glazing(d, 115, 49, 204, 170, cw=9, ch=10, frame=GLASS_DK)
    d.ellipse([cx - 28, 53, cx + 27, 108], fill=INK)              # the clock: navy ring,
    d.ellipse([cx - 26, 55, cx + 25, 106], fill=NAVY)             # white dial, the blue
    d.ellipse([cx - 22, 59, cx + 21, 102], fill=WHITE)            # star at its centre
    d.ellipse([cx - 22, 59, cx + 21, 102], outline=SNOW_LO)
    star(d, cx - 0.5, 80.5, 15, rgb('3a5fb0'), NAVY)
    for h in range(12):
        a = math.radians(h * 30)
        hx, hy = round(cx - 0.5 + 19 * math.sin(a)), round(80.5 - 19 * math.cos(a))
        d.rectangle([hx, hy, hx + (h % 3 == 0), hy + (h % 3 == 0)], fill=INK)
    d.line([(cx, 80), (cx - 9, 73)], fill=INK, width=2)           # ten past ten
    d.line([(cx, 80), (cx + 6, 64)], fill=INK)
    d.rectangle([cx - 1, 79, cx, 80], fill=AMBER)
    d.rectangle([116, 116, 203, 137], fill=NAVY)                  # the name board
    d.rectangle([116, 116, 203, 117], fill=rgb('3a5fb0'))
    text(d, 'SAPPORO', cx - text_w('SAPPORO', 2) // 2, 120, WHITE, scale=2)
    # ---- the long canopy, snow lying on it ----------------------------------------
    d.rectangle([0, 172, 319, 178], fill=STONE_LO)
    d.line([(0, 172), (319, 172)], fill=WHITE)
    d.rectangle([0, 177, 319, 178], fill=STONE_DK)
    snow_cap(d, 0, 319, 168, 4, seed=7)
    # ---- the ground floor behind it: lit shop windows, four doors in the middle --
    d.rectangle([6, 179, 313, 218], fill=GLASS_DK)
    d.rectangle([6, 179, 313, 182], fill=DARK)                    # the canopy's shadow
    for i, x in enumerate(range(16, 296, 22)):
        if 120 <= x + 9 <= 200:
            continue
        on = i % 3 != 1
        d.rectangle([x, 186, x + 17, 213], fill=WARM if on else GLASS)
        d.line([(x, 186), (x + 17, 186)], fill=WHITE if on else GLASS_HI)
        d.line([(x + 8, 186), (x + 8, 213)], fill=GLASS_DK)
        d.rectangle([x, 206, x + 17, 213], fill=CREAM_LO if on else GLASS_DK)
        if on:                                                    # goods in the window
            for k in range(3):
                d.rectangle([x + 2 + k * 5, 200, x + 4 + k * 5, 205], fill=(RED, GREEN_HI, rgb('3a5fb0'))[(i + k) % 3])
    for x in (131, 146, 161, 176):                                # the doors (cells 4,6 and 5,6)
        glass_door(d, x, 184, x + 13, 218)
    for x in (10, 54, 98, 124, 193, 219, 263, 307):               # the canopy's columns
        d.rectangle([x, 179, x + 2, 218], fill=STONE)
        d.line([(x + 2, 179), (x + 2, 218)], fill=STONE_DK)
    d.rectangle([4, 218, 315, 222], fill=STONE_LO)
    d.line([(4, 218), (315, 218)], fill=STONE)
    # ---- snow on the roofs ----------------------------------------------------------
    snow_cap(d, 4, 109, 92, 4, seed=1); snow_cap(d, 210, 315, 92, 4, seed=2)
    snow_cap(d, 110, 209, 40, 4, seed=3)
    drift(d, 3, 30, 222, 5, seed=1); drift(d, 288, 317, 222, 5, seed=4)
    outline(im)
    return im


SLATE, SLATE_LO = rgb('5f6a80'), rgb('434b60')


def arched(d, x, y0, y1, w=9, lit=False):
    """A tall round-headed window in a white stone surround."""
    d.rectangle([x - 1, y0 + w // 2, x + w, y1 + 1], fill=CREAM)
    d.pieslice([x - 1, y0 - 1, x + w, y0 + w], 180, 360, fill=CREAM)
    g = WARM if lit else GLASS
    d.rectangle([x, y0 + w // 2, x + w - 1, y1], fill=g)
    d.pieslice([x, y0, x + w - 1, y0 + w - 1], 180, 360, fill=g)
    d.line([(x + w // 2, y0 + 1), (x + w // 2, y1)], fill=CREAM)
    d.line([(x, y0 + w // 2 + 4), (x + w - 1, y0 + w // 2 + 4)], fill=CREAM)
    d.line([(x, y0 + w // 2), (x + w // 2 - 1, y0 + w // 2)], fill=WHITE if lit else GLASS_HI)
    d.line([(x - 1, y1 + 2), (x + w, y1 + 2)], fill=BRICK_DK)


def pioneer_star(d, cx, cy, r=5):
    """The red five-pointed star of the Hokkaido pioneers, on a white roundel
    (as on the Clock Tower's gable)."""
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=WHITE)
    star(d, cx, cy, r, RED, RED_LO)


def akarenga():
    """The Former Hokkaido Government Office: red brick, a slate roof, the
    green copper dome on its octagonal drum, red stars."""
    im, d = canvas(7, 6)                 # 224 x 192
    cx = 112
    # ---- the dome on its drum, behind the centre gable ---------------------------
    d.rectangle([96, 46, 127, 74], fill=BRICK)
    d.rectangle([118, 46, 127, 74], fill=BRICK_LO)
    d.line([(96, 46), (96, 74)], fill=BRICK_HI)
    for x in (100, 108, 116):
        d.rectangle([x, 54, x + 4, 66], fill=CREAM); d.rectangle([x + 1, 55, x + 3, 65], fill=GLASS)
        d.point((x + 1, 55), fill=GLASS_HI)
    d.rectangle([93, 43, 130, 46], fill=CREAM); d.line([(93, 43), (130, 43)], fill=WHITE)
    d.line([(93, 46), (130, 46)], fill=CREAM_DK)
    d.pieslice([94, 13, 129, 73], 180, 360, fill=GREEN)
    d.pieslice([94, 13, 129, 73], 305, 360, fill=GREEN_LO)
    for x, c in ((100, GREEN_HI), (106, GREEN_LO), (117, INK), (123, INK)):     # the dome's ribs
        t = (x - 111.5) / 17.5
        d.line([(x, int(43 - 30 * math.sqrt(1 - t * t)) + 1), (x, 42)], fill=c if c != INK else rgb('2c3f40'))
    d.rectangle([107, 8, 116, 15], fill=CREAM); d.rectangle([113, 8, 116, 15], fill=CREAM_LO)   # the lantern
    d.rectangle([109, 10, 110, 14], fill=GLASS); d.rectangle([105, 6, 118, 8], fill=GREEN)
    d.rectangle([111, 0, 112, 5], fill=STONE_DK)
    for x in range(99, 125):                                      # snow lying on the dome's crown
        t = (x - 111.5) / 17.5
        top = int(43 - 30 * math.sqrt(1 - t * t))
        if x not in range(105, 119):
            d.line([(x, top), (x, top + 2 + (x % 3 == 0))], fill=SNOW)
    snow_cap(d, 105, 118, 4, 2, seed=2)
    # ---- the slate roof, two ventilator turrets, snow ------------------------------
    rows = [(y, 8 + (97 - y) // 2, 215 - (97 - y) // 2) for y in range(78, 98)]
    tiles(d, rows, SLATE, SLATE_LO, step=3)
    snow_cap(d, 42, 82, 93, 2, seed=6); snow_cap(d, 142, 182, 93, 2, seed=8)    # snow caught at the eaves
    for x in (52, 160):
        d.rectangle([x, 64, x + 11, 80], fill=BRICK); d.rectangle([x + 8, 64, x + 11, 80], fill=BRICK_LO)
        d.rectangle([x + 3, 68, x + 6, 76], fill=GLASS_DK)
        d.rectangle([x - 2, 61, x + 13, 64], fill=GREEN); d.line([(x - 2, 61), (x + 13, 61)], fill=GREEN_HI)
        snow_cap(d, x - 2, x + 13, 58, 2, seed=x)
    snow_cap(d, 18, 205, 74, 4, seed=3)
    # ---- the brick front: two storeys of arched windows over a stone basement -----
    brick(d, 8, 98, 215, 183)
    brick(d, 208, 98, 215, 183, shade=True)
    d.rectangle([6, 96, 217, 99], fill=CREAM)
    d.line([(6, 96), (217, 96)], fill=WHITE); d.line([(6, 99), (217, 99)], fill=CREAM_DK)
    d.rectangle([8, 137, 215, 138], fill=CREAM); d.line([(8, 139), (215, 139)], fill=BRICK_DK)
    d.rectangle([8, 172, 215, 183], fill=STONE)
    d.line([(8, 172), (215, 172)], fill=WHITE)
    for x in range(14, 214, 12):
        d.line([(x, 173), (x, 183)], fill=STONE_LO)
    d.rectangle([208, 173, 215, 183], fill=STONE_LO)
    for i, x in enumerate((13, 27, 46, 60, 74, 141, 155, 169, 188, 202)):
        arched(d, x, 106, 128, lit=i in (3, 8))
        arched(d, x, 145, 166, lit=i in (1, 5))
    for x0, x1 in ((8, 40), (183, 215), (86, 137)):               # stone quoins: end pavilions, centre bay
        for y in range(101, 172, 6):
            d.rectangle([x0, y, x0 + 2, y + 2], fill=CREAM)
            d.rectangle([x1 - 2, y, x1, y + 2], fill=CREAM if x1 != 215 else CREAM_LO)
    # ---- end pavilions under their own steep roofs ----------------------------------
    for px0 in (8, 183):
        pc = px0 + 16
        rows = [(y, pc - (y - 60) * 18 // 37, pc + (y - 60) * 18 // 37) for y in range(60, 98)]
        tiles(d, rows, SLATE, SLATE_LO, step=3)
        for y, a, b in rows:
            d.point((a, y), fill=SNOW); d.point((a + 1, y), fill=SNOW)          # snow on the lit slope
            if y < 72:
                d.line([(a, y), (pc, y)], fill=SNOW)
            d.line([(pc + (b - pc) // 2, y), (b, y)], fill=SLATE_LO)
        d.rectangle([pc, 52, pc + 1, 60], fill=STONE_DK)
        d.rectangle([px0 - 2, 96, px0 + 34, 99], fill=CREAM); d.line([(px0 - 2, 96), (px0 + 34, 96)], fill=WHITE)
    # ---- the centre bay: a brick gable with the star, the porch and its steps -----
    for y in range(64, 97):
        w = (y - 64) * 27 // 32
        d.line([(cx - w, y), (cx + w - 1, y)], fill=BRICK)
        d.line([(cx + w // 2, y), (cx + w - 1, y)], fill=BRICK_LO)
        d.rectangle([cx - w - 2, y, cx - w, y], fill=CREAM)
        d.rectangle([cx + w - 1, y, cx + w + 1, y], fill=CREAM_LO)
    for x in range(cx - 27, cx + 28):                             # snow on the gable's rakes
        y = 64 + abs(x - cx) * 32 // 27
        if abs(x - cx) > 2:
            d.line([(x, y - 3), (x, y - 1)], fill=SNOW)
    d.rectangle([cx - 3, 58, cx + 2, 66], fill=CREAM); snow_cap(d, cx - 3, cx + 2, 55, 2, seed=1)
    pioneer_star(d, cx, 83, 6)
    d.rectangle([86, 96, 137, 99], fill=CREAM); d.line([(86, 96), (137, 96)], fill=WHITE)
    arched(d, 92, 106, 128); arched(d, 123, 106, 128)
    arched(d, 107, 104, 128, w=11, lit=True)
    d.rectangle([94, 142, 129, 183], fill=CREAM)                  # the stone porch
    d.rectangle([124, 143, 129, 183], fill=CREAM_LO)
    d.line([(94, 142), (129, 142)], fill=WHITE)
    d.rectangle([91, 139, 132, 142], fill=CREAM); d.line([(91, 139), (132, 139)], fill=WHITE)
    snow_cap(d, 91, 132, 136, 2, seed=4)
    d.rectangle([100, 156, 123, 183], fill=WOOD_DK)               # the doors (cell 3,5)
    d.pieslice([100, 145, 123, 168], 180, 360, fill=WOOD_DK)
    d.pieslice([102, 147, 121, 166], 180, 360, fill=WARM)
    d.line([(111, 147), (111, 156)], fill=WOOD_DK)
    d.rectangle([102, 158, 110, 183], fill=WOOD_LO); d.rectangle([113, 158, 121, 183], fill=WOOD_LO)
    d.line([(102, 158), (110, 158)], fill=WOOD); d.line([(113, 158), (121, 158)], fill=WOOD)
    d.rectangle([104, 161, 108, 170], fill=GLASS); d.rectangle([115, 161, 119, 170], fill=GLASS)
    d.point((110, 172), fill=GOLD); d.point((113, 172), fill=GOLD)
    for i, y in enumerate((184, 186, 188)):                       # steps
        d.rectangle([92 - i * 2, y, 131 + i * 2, y + 1], fill=WHITE if i == 0 else STONE)
        d.line([(92 - i * 2, y + 1), (131 + i * 2, y + 1)], fill=STONE_LO)
    d.rectangle([6, 184, 87, 189], fill=STONE_LO); d.rectangle([136, 184, 217, 189], fill=STONE_LO)
    d.line([(6, 184), (87, 184)], fill=STONE); d.line([(136, 184), (217, 184)], fill=STONE)
    drift(d, 4, 30, 190, 5, seed=2); drift(d, 60, 84, 190, 3, seed=5)
    drift(d, 140, 166, 190, 3, seed=7); drift(d, 192, 219, 190, 5, seed=3)
    outline(im)
    return im


ORANGE = rgb('f08a3c')


def konbini():
    """A corner-shop front in the house style (the town's 7-Eleven tile is bare
    line art): a white fascia with an orange and a teal stripe, a lit glass
    front, automatic doors."""
    im, d = canvas(4, 3)                 # 128 x 96
    d.rectangle([4, 24, 123, 91], fill=WHITE)
    d.rectangle([2, 20, 125, 24], fill=STONE_LO); d.line([(2, 20), (125, 20)], fill=STONE)
    d.rectangle([86, 9, 108, 19], fill=STONE_DK); d.rectangle([86, 9, 90, 19], fill=STONE_LO)   # roof plant
    for x in range(93, 107, 3):
        d.line([(x, 11), (x, 17)], fill=INK)
    snow_cap(d, 86, 108, 6, 3, seed=2)
    snow_cap(d, 2, 125, 16, 4, seed=9)
    # ---- the fascia ------------------------------------------------------------------
    d.rectangle([4, 25, 123, 44], fill=WHITE)
    d.rectangle([4, 26, 123, 28], fill=ORANGE)
    d.rectangle([4, 40, 123, 42], fill=CYAN_LO)
    d.line([(4, 44), (123, 44)], fill=STONE_LO)
    d.rectangle([116, 25, 123, 44], fill=SNOW_LO)
    d.rectangle([116, 26, 123, 28], fill=rgb('c96f2c')); d.rectangle([116, 40, 123, 42], fill=rgb('1f6f80'))
    kana(d, ('ko', 'n', 'bi', 'ni'), 64 - kana_w(4) // 2, 31, NAVY)
    d.rectangle([12, 30, 21, 38], fill=ORANGE)                    # an invented mark: a snow crystal
    d.line([(16, 31), (16, 37)], fill=WHITE); d.line([(13, 34), (20, 34)], fill=WHITE)
    d.point((14, 32), fill=WHITE); d.point((19, 32), fill=WHITE); d.point((14, 36), fill=WHITE); d.point((19, 36), fill=WHITE)
    # ---- the glass front ---------------------------------------------------------------
    d.rectangle([4, 45, 123, 90], fill=GLASS_DK)
    for x0, x1 in ((7, 30), (65, 120)):
        d.rectangle([x0, 48, x1, 84], fill=WARM)
        d.line([(x0, 48), (x1, 48)], fill=WHITE)
        for sy in (60, 71, 82):                                   # shelves
            d.line([(x0, sy), (x1, sy)], fill=CREAM_LO)
            for k, bx in enumerate(range(x0 + 2, x1 - 2, 4)):
                c = (RED, CYAN_LO, WHITE, GREEN_HI, ORANGE, rgb('3a5fb0'), PINK)[(k * 3 + sy) % 7]
                d.rectangle([bx, sy - 5 + (k + sy) % 2, bx + 2, sy - 1], fill=c)
        for x in range(x0 + 18, x1, 19):
            d.line([(x, 48), (x, 84)], fill=GLASS_DK)
        d.rectangle([x0, 85, x1, 90], fill=STONE)
    d.rectangle([68, 50, 80, 60], fill=WHITE); d.rectangle([68, 50, 80, 52], fill=RED)        # posters on the glass
    d.line([(70, 55), (78, 55)], fill=STONE_LO); d.line([(70, 57), (76, 57)], fill=STONE_LO)
    d.rectangle([104, 50, 117, 62], fill=CYAN_LO); d.rectangle([107, 53, 114, 59], fill=WHITE)
    glass_door(d, 34, 48, 47, 90, frame=STONE_LO); glass_door(d, 48, 48, 61, 90, frame=STONE_LO)   # doors (cell 1,2)
    d.rectangle([34, 46, 61, 48], fill=ORANGE)
    d.rectangle([2, 91, 125, 94], fill=STONE_LO); d.line([(2, 91), (125, 91)], fill=STONE)
    d.rectangle([34, 91, 61, 94], fill=STONE_DK)                  # the door mat
    # a nobori by the door and the ash-grey newspaper rack
    d.rectangle([24, 52, 25, 92], fill=STONE_LO)
    d.rectangle([13, 54, 23, 78], fill=RED); d.line([(13, 54), (13, 78)], fill=RED_HI)
    for y in (59, 65, 71):
        d.rectangle([16, y, 20, y + 3], fill=WHITE)
    drift(d, 2, 22, 95, 4, seed=3); drift(d, 100, 126, 95, 5, seed=6)
    outline(im)
    return im


# ==============================================================================
# Tanukikoji (second pass): what makes the street a covered arcade
# ==============================================================================
def tanuki_rib():
    """One rib of the arcade's roof: the gate's arch without its board - white
    steel, glass between the chords, bulbs, three hanging banners. Under the
    roof, so no snow. Walk through the two middle cells."""
    im, d = canvas(4, 3)                 # 128 x 96
    for x in (5, 113):
        d.rectangle([x, 34, x + 9, 90], fill=STONE)
        d.line([(x, 34), (x, 90)], fill=WHITE)
        d.rectangle([x + 7, 34, x + 9, 90], fill=STONE_LO)
        for y in (48, 52):
            d.rectangle([x, y, x + 9, y + 1], fill=RED)
        d.rectangle([x - 2, 86, x + 11, 93], fill=STONE_DK)
        d.line([(x - 2, 86), (x + 11, 86)], fill=STONE_LO)
    def top(x):
        t = (x - 63.5) / 59
        return int(round(6 + 28 * t * t))
    for x in range(5, 123):
        y = top(x)
        d.line([(x, y + 3), (x, y + 10)], fill=rgb('a9d3fb') if (x // 8) % 2 else GLASS_HI)   # glass
        d.line([(x, y), (x, y + 2)], fill=WHITE)                  # upper chord
        d.point((x, y + 2), fill=STONE)
        d.line([(x, y + 11), (x, y + 13)], fill=STONE)            # lower chord, in shade
        d.point((x, y + 11), fill=WHITE); d.point((x, y + 13), fill=STONE_LO)
        if x % 8 == 0:
            d.line([(x, y + 3), (x, y + 10)], fill=WHITE)         # struts
        if x % 7 == 3:                                            # bulbs under the arch
            d.rectangle([x, y + 15, x + 1, y + 16], fill=AMBER)
            d.point((x, y + 15), fill=WHITE)
    for bx, c, lo in ((30, RED, RED_DK), (58, NAVY, INK), (86, RED, RED_DK)):   # banners
        y = top(bx + 5) + 14
        d.line([(bx + 5, y), (bx + 5, y + 3)], fill=STONE_DK)
        d.rectangle([bx, y + 4, bx + 10, y + 26], fill=c)
        d.line([(bx, y + 4), (bx, y + 26)], fill=RED_HI if c == RED else rgb('3a5fb0'))
        d.rectangle([bx + 8, y + 4, bx + 10, y + 26], fill=lo)
        d.rectangle([bx, y + 4, bx + 10, y + 5], fill=WOOD_DK)
        d.ellipse([bx + 3, y + 10, bx + 7, y + 14], fill=WHITE)   # a paw print
        for px_, py_ in ((2, 8), (5, 7), (8, 8)):
            d.point((bx + px_, y + py_), fill=WHITE)
        d.line([(bx + 3, y + 19), (bx + 7, y + 19)], fill=WHITE); d.line([(bx + 3, y + 22), (bx + 7, y + 22)], fill=WHITE)
    outline(im)
    return im


def arcade_south(variant='a'):
    """The arcade's other side: the south row of shops seen from behind - the
    same glass roof over them (it tiles with itself and overhangs the street
    row north of it), then their back wall in three bays: a service door and
    beer crates, a lit kitchen window over two AC units, a roller shutter by
    a steaming vent. Variant b has the bays in another order on grey render."""
    im, d = canvas(3, 3)                 # 96 x 96
    arcade_roof(d, posts=False)
    wall, seam, top = (CREAM_LO, rgb('ab8c7c'), CREAM_DK) if variant == 'a' else (STONE, rgb('a9b4bb'), STONE_LO)
    d.rectangle([0, 44, 95, 91], fill=wall)
    for y in range(49, 91, 5):
        d.line([(0, y), (95, y)], fill=seam)
    d.rectangle([0, 44, 95, 46], fill=top)
    for x in (31, 63):                                            # downpipes between the three backs
        d.rectangle([x, 44, x + 1, 91], fill=STONE_DK)
        d.point((x, 60), fill=STONE_LO); d.point((x, 78), fill=STONE_LO)

    def door(o):
        d.rectangle([o + 6, 56, o + 20, 91], fill=STONE_DK)
        d.rectangle([o + 7, 57, o + 19, 91], fill=STONE_LO); d.line([(o + 7, 57), (o + 7, 91)], fill=WHITE)
        d.rectangle([o + 10, 61, o + 16, 68], fill=WARM); d.point((o + 17, 76), fill=INK)
        d.rectangle([o + 4, 53, o + 22, 55], fill=RED); snow_cap(d, o + 4, o + 22, 51, 2, seed=1)
        for i, cy_ in enumerate((82, 73, 64)):
            c = (AMBER, RED, AMBER)[i]
            d.rectangle([o + 23, cy_, o + 29, cy_ + 8], fill=c)
            d.line([(o + 23, cy_ + 3), (o + 29, cy_ + 3)], fill=rgb('c98f1c') if c == AMBER else RED_DK)
            d.line([(o + 23, cy_ + 8), (o + 29, cy_ + 8)], fill=INK)

    def window(o):
        d.rectangle([o + 5, 52, o + 26, 66], fill=WOOD_DK)
        d.rectangle([o + 6, 53, o + 25, 65], fill=WARM)
        for x in range(o + 9, o + 25, 4):
            d.line([(x, 53), (x, 65)], fill=WOOD_DK)
        d.line([(o + 4, 67), (o + 27, 67)], fill=SNOW); d.line([(o + 5, 68), (o + 26, 68)], fill=SNOW_LO)
        for x in (o + 4, o + 17):
            d.rectangle([x, 76, x + 10, 86], fill=STONE if variant == 'a' else WHITE)
            d.rectangle([x, 76, x + 10, 77], fill=WHITE)
            d.rectangle([x, 76, x + 10, 86], outline=STONE_LO)
            d.ellipse([x + 2, 78, x + 8, 84], fill=STONE_DK); d.point((x + 5, 81), fill=STONE)
            d.line([(x, 87), (x + 10, 87)], fill=STONE_DK)
            d.line([(x, 75), (x + 10, 75)], fill=SNOW)

    def shutter(o):
        d.rectangle([o + 4, 58, o + 22, 91], fill=STONE_LO)
        for y in range(60, 91, 3):
            d.line([(o + 5, y), (o + 21, y)], fill=rgb('a2a3b3'))
        d.rectangle([o + 3, 55, o + 23, 57], fill=STONE_DK); snow_cap(d, o + 3, o + 23, 53, 2, seed=5)
        d.rectangle([o + 25, 48, o + 27, 62], fill=STONE_LO); d.rectangle([o + 22, 47, o + 27, 49], fill=STONE_LO)
        for sx, sy in ((20, 44), (18, 41), (21, 38), (17, 36)):   # the vent's steam
            d.rectangle([o + sx, sy, o + sx + 1, sy + 1], fill=WHITE)
        for x in (o + 25, o + 28):                                # gas bottles
            d.rectangle([x, 78, x + 2, 91], fill=STONE_LO); d.point((x + 1, 77), fill=RED)
            d.line([(x, 78), (x, 91)], fill=WHITE)

    bays = (door, window, shutter) if variant == 'a' else (shutter, door, window)
    for i, bay in enumerate(bays):
        bay(i * 32 + (1 if i else 0))
    d.rectangle([0, 92, 95, 95], fill=STONE_LO); d.line([(0, 92), (95, 92)], fill=STONE)
    for x in range(0, 96):                                        # snow blown against the wall
        h = 2 + ((x * 5) % 7 in (0, 2, 3)) + (2 if 26 < (x + (0 if variant == 'a' else 30)) % 48 < 40 else 0)
        d.line([(x, 92 - h), (x, 92)], fill=SNOW)
        d.point((x, 93), fill=SNOW_LO)
    outline(im)
    return im


def arcade_end():
    """Where the arcade's roof stops at an east or west end: one more bay of
    the glass, a post, and the upright sign (タヌキ) the E-W entrances carry."""
    im, d = canvas(1, 4)                 # 32 x 128
    arcade_roof(d, posts=False, w=32)
    d.rectangle([13, 40, 18, 123], fill=STONE)
    d.line([(13, 40), (13, 123)], fill=WHITE); d.rectangle([17, 40, 18, 123], fill=STONE_LO)
    d.rectangle([10, 118, 21, 125], fill=STONE_DK); d.line([(10, 118), (21, 118)], fill=STONE_LO)
    d.rectangle([5, 46, 26, 104], fill=CREAM)
    d.rectangle([7, 48, 24, 102], fill=RED)
    d.line([(7, 48), (7, 102)], fill=RED_HI); d.rectangle([22, 48, 24, 102], fill=RED_DK)
    kana(d, ('ta', 'nu', 'ki'), 9, 51, WHITE, scale=2, vertical=True)
    for y in (45, 105):                                           # bulbs top and bottom
        for x in (8, 15, 22):
            d.rectangle([x, y, x + 1, y + 1], fill=AMBER)
    outline(im)
    return im


# ==============================================================================
# Odori Park (second pass)
# ==============================================================================
def snow_bear():
    """A brown bear carved in snow, side on, head low, a salmon hanging from
    its jaws, on a block. Legs stand apart so the gaps cut its outline."""
    im, d = canvas(3, 2)                 # 96 x 64
    snow_block(d, 6, 51, 91, 61, joints=False)
    d.line([(8, 56), (82, 56)], fill=SNOW_LO)
    for x in (44, 76):                                            # the far legs, in shade
        d.rectangle([x, 34, x + 8, 50], fill=SNOW_SH)
        d.line([(x + 6, 34), (x + 6, 50)], fill=SNOW_DK)
    d.ellipse([30, 15, 90, 44], fill=SNOW)                        # barrel and rump
    d.ellipse([30, 7, 60, 38], fill=SNOW)                         # the shoulder hump
    d.chord([30, 15, 90, 44], 15, 165, fill=SNOW_SH)              # the belly, in shade
    d.arc([32, 8, 58, 36], 190, 330, fill=WHITE)
    d.arc([52, 16, 88, 42], 220, 330, fill=WHITE)
    d.ellipse([85, 22, 92, 30], fill=SNOW_LO)                     # the stub of a tail
    for x in (33, 65):                                            # the near legs
        d.rectangle([x, 32, x + 10, 50], fill=SNOW)
        d.rectangle([x + 8, 34, x + 10, 50], fill=SNOW_LO)
        d.rectangle([x - 3, 46, x + 10, 50], fill=SNOW)
        d.line([(x - 3, 50), (x + 10, 50)], fill=SNOW_SH)
        for cxp in (x - 2, x + 1, x + 4):
            d.point((cxp, 49), fill=SNOW_DK)
    d.ellipse([12, 12, 40, 38], fill=SNOW)                        # the head, low, facing left
    d.polygon([(3, 24), (14, 19), (18, 34), (5, 33)], fill=SNOW)  # the muzzle
    d.line([(3, 24), (14, 19)], fill=WHITE)
    d.chord([12, 12, 40, 38], 30, 150, fill=SNOW_LO)
    d.rectangle([3, 24, 5, 26], fill=SNOW_DK)                     # nose
    d.rectangle([17, 21, 18, 22], fill=SNOW_DK)                   # eye
    d.line([(15, 19), (20, 18)], fill=SNOW_SH)                    # brow
    d.ellipse([27, 6, 36, 15], fill=SNOW); d.ellipse([30, 9, 33, 13], fill=SNOW_SH)   # ears
    d.ellipse([17, 7, 24, 14], fill=SNOW_LO)
    # the salmon, crosswise in its jaws: its head past the nose, its tail under the neck
    d.polygon([(1, 33), (4, 30), (17, 30), (23, 33), (17, 37), (4, 37)], fill=SNOW_SH)
    d.polygon([(22, 33), (28, 28), (26, 33), (28, 39)], fill=SNOW_SH)
    d.line([(4, 30), (16, 30)], fill=SNOW_LO)
    d.line([(4, 37), (17, 37)], fill=SNOW_DK)
    d.line([(8, 31), (8, 36)], fill=SNOW_DK)                      # the gill
    d.point((4, 32), fill=SNOW_DK)
    for x in (12, 15, 18):
        d.point((x, 33), fill=SNOW_DK); d.point((x + 1, 35), fill=SNOW_DK)
    for k in range(6):                                            # fur, cut with a few strokes
        d.line([(42 + k * 7, 20 + (k % 2) * 4), (44 + k * 7, 25 + (k % 2) * 4)], fill=SNOW_LO)
    for k in range(3):
        d.line([(34 + k * 6, 14 + k), (36 + k * 6, 18 + k)], fill=SNOW_LO)
    outline(im)
    return im


ICE, ICE_HI, ICE_LO = rgb('bfe3f6'), rgb('e6f6fd'), rgb('8fc3e6')


def odori_fountain():
    """Odori's fountain shut down for the winter: the round basin frozen over,
    snow on its rim and bowls, icicles, festival lights set in the ice."""
    im, d = canvas(3, 3)                 # 96 x 96
    cx = 48
    d.ellipse([3, 62, 92, 93], fill=STONE_LO)                     # the basin's wall
    d.rectangle([3, 70, 92, 78], fill=STONE_LO)
    for x in range(9, 90, 10):
        d.line([(x, 80), (x, 91)], fill=STONE_DK)
    d.chord([3, 62, 92, 93], 330, 60, fill=STONE_DK)
    d.ellipse([3, 54, 92, 85], fill=SNOW)                         # snow on its rim
    d.arc([3, 54, 92, 85], 20, 160, fill=SNOW_LO)
    d.ellipse([10, 58, 85, 81], fill=ICE)                         # the ice
    d.arc([10, 58, 85, 81], 180, 360, fill=ICE_LO)
    d.chord([10, 58, 85, 81], 200, 340, fill=ICE_LO)
    d.ellipse([12, 61, 83, 81], fill=ICE)
    for x0, y0, x1 in ((18, 72, 30), (56, 76, 72), (24, 77, 34), (62, 68, 70)):   # light on it
        d.line([(x0, y0), (x1, y0 - 2)], fill=ICE_HI)
    for i, (lx, ly) in enumerate(((17, 69), (27, 76), (40, 79), (56, 79), (69, 76), (79, 69))):   # lights
        c, glow = ((PINK, rgb('f3cfe6')), (CYAN, rgb('c8f2f6')), (WARM, rgb('f8efcf')))[i % 3]
        d.ellipse([lx - 3, ly - 2, lx + 3, ly + 2], fill=glow)
        d.rectangle([lx - 1, ly - 1, lx, ly], fill=c)
    # the stem and its two bowls
    d.rectangle([44, 24, 51, 72], fill=STONE)
    d.line([(44, 24), (44, 72)], fill=WHITE); d.rectangle([50, 24, 51, 72], fill=STONE_LO)
    d.ellipse([40, 68, 55, 76], fill=SNOW); d.arc([40, 68, 55, 76], 20, 160, fill=SNOW_LO)
    for (x0, x1, y, seed) in ((24, 71, 44, 1), (35, 60, 26, 2)):
        d.chord([x0, y - 8, x1, y + 8], 0, 180, fill=STONE)       # the bowl's underside
        d.chord([x0 + (x1 - x0) // 2, y - 8, x1, y + 8], 0, 90, fill=STONE_LO)
        d.ellipse([x0, y - 5, x1, y + 3], fill=SNOW)              # snow heaped in it
        d.ellipse([x0 + 6, y - 9, x1 - 6, y], fill=SNOW)
        d.arc([x0 + 6, y - 9, x1 - 6, y], 190, 300, fill=WHITE)
        d.line([(x0 + 2, y + 1), (x1 - 2, y + 1)], fill=SNOW_LO)
        for x in range(x0 + 2, x1 - 1, 3):                        # icicles off its lip
            n = 3 + (x * 7 + seed * 3) % 6
            d.line([(x, y + 2), (x, y + 2 + n)], fill=ICE_HI)
            d.line([(x + 1, y + 2), (x + 1, y + n)], fill=ICE_LO)
    d.ellipse([44, 8, 51, 15], fill=STONE); d.point((46, 10), fill=WHITE)       # the finial
    d.rectangle([46, 15, 49, 18], fill=STONE_LO)
    snow_cap(d, 44, 51, 6, 2, seed=3)
    outline(im)
    return im


def odori_lamp():
    """Odori Park's lamp: a white globe on a dark green iron post (`lamp-post`:
    DayNight gives its head a halo at night)."""
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([15, 22, 16, 59], fill=TRAM_LO); d.line([(15, 22), (15, 59)], fill=TRAM)      # the post
    for y in (30, 44):                                                                       # its two collars
        d.rectangle([14, y, 17, y + 1], fill=TRAM); d.line([(14, y + 1), (17, y + 1)], fill=TRAM_LO)
    d.rectangle([13, 56, 18, 58], fill=TRAM_LO); d.rectangle([11, 59, 20, 61], fill=TRAM_LO)  # the foot
    d.line([(11, 59), (20, 59)], fill=TRAM)
    d.rectangle([12, 20, 19, 22], fill=TRAM_LO); d.line([(12, 20), (19, 20)], fill=TRAM_HI)   # the cup under the globe
    d.ellipse([8, 5, 23, 20], fill=WHITE)                                                    # the globe
    d.ellipse([10, 8, 21, 19], fill=rgb('fbf3d2'))
    d.ellipse([12, 11, 19, 18], fill=WARM)
    d.arc([8, 5, 23, 20], 20, 150, fill=CREAM_LO)
    d.point((12, 9), fill=WHITE); d.point((13, 8), fill=WHITE)
    d.rectangle([14, 2, 17, 4], fill=TRAM_LO)                                                # the cap
    snow_cap(d, 10, 21, 3, 2, seed=5)
    drift(d, 8, 23, 62, 2, seed=3)
    outline(im)
    return im


def odori_bench():
    """A park bench in Odori's dark green, snow lying on its seat and back."""
    im, d = canvas(2, 1)                 # 64 x 32
    for x in (8, 53):                                             # iron end frames
        d.rectangle([x, 9, x + 2, 28], fill=DARK)
        d.rectangle([x - 2, 27, x + 4, 29], fill=DARK)
        d.line([(x, 9), (x, 26)], fill=STONE_DK)
    for y in (9, 13):                                             # the back's two slats
        d.rectangle([6, y, 57, y + 2], fill=TRAM); d.line([(6, y), (57, y)], fill=TRAM_HI)
        d.line([(6, y + 2), (57, y + 2)], fill=TRAM_LO)
    d.rectangle([5, 19, 58, 22], fill=TRAM); d.line([(5, 22), (58, 22)], fill=TRAM_LO)       # the seat
    d.rectangle([5, 23, 58, 23], fill=DARK)
    snow_cap(d, 6, 57, 6, 2, seed=2)                              # snow along the top of the back
    snow_cap(d, 5, 58, 16, 3, seed=6)                             # and lying on the seat
    drift(d, 3, 14, 30, 2, seed=1); drift(d, 48, 61, 30, 2, seed=4)
    outline(im)
    return im


def lantern_post():
    """A post of paper lanterns for the ramen alley (`-lanterns`: it glows)."""
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([15, 6, 16, 60], fill=WOOD_LO); d.line([(15, 6), (15, 60)], fill=WOOD)
    d.rectangle([12, 59, 19, 61], fill=STONE_DK)
    for y in (9, 31):
        d.rectangle([3, y, 28, y + 1], fill=WOOD_DK)
    lantern(d, 3, 12, 9, 14); lantern(d, 20, 12, 9, 14, body=WHITE, hi=WHITE, lo=CREAM_LO)
    lantern(d, 3, 34, 9, 14, body=WHITE, hi=WHITE, lo=CREAM_LO); lantern(d, 20, 34, 9, 14)
    for x, y in ((23, 18), (6, 40)):
        d.rectangle([x, y, x + 2, y + 3], fill=RED)
    snow_cap(d, 3, 28, 6, 2, seed=4)
    drift(d, 8, 23, 62, 2, seed=2)
    outline(im)
    return im


# ==============================================================================
# Streetcar track, snowbanks
# ==============================================================================
ASPHALT, ASPHALT_DK = (83, 89, 109, 255), (65, 63, 83, 255)      # road-plain's two tones
SETT, SETT_HI, SETT_J = rgb('71768c'), rgb('7f859b'), rgb('5a5f76')
RAIL_HI, RAIL, RAIL_GROOVE = rgb('aab2bf'), rgb('868c9f'), rgb('2c2d44')


def tram_rail(kind):
    """Streetcar track: a full ground tile that stands in for the road tile -
    a bed of setts across the carriageway, two grey steel rails with a dark
    flange groove each, a strip of asphalt either side. h runs east-west, v
    north-south, cross is where two lines (or a line and a side street) meet."""
    im = Image.new('RGBA', (32, 32), ASPHALT)
    px = im.load()
    h, v = kind in ('h', 'cross'), kind in ('v', 'cross')
    for y in range(32):
        for x in range(32):
            if not ((h and 3 <= y <= 28) or (v and 3 <= x <= 28)):
                continue
            course = y // 4
            if y % 4 == 3 or (x + (course % 2) * 2) % 4 == 3:
                px[x, y] = SETT_J
            else:
                px[x, y] = SETT_HI if ((x // 4) * 5 + course * 3) % 7 == 0 else SETT
    for a in range(32):                                           # the bed's kerb line against the asphalt
        if h and not (v and 3 <= a <= 28):
            px[a, 2] = ASPHALT_DK; px[a, 29] = ASPHALT_DK
        if v and not (h and 3 <= a <= 28):
            px[2, a] = ASPHALT_DK; px[29, a] = ASPHALT_DK
    for r in (9, 20):                                             # rail heads
        for a in range(32):
            if h:
                px[a, r] = RAIL_HI; px[a, r + 1] = RAIL
            if v:
                px[r, a] = RAIL_HI; px[r + 1, a] = RAIL
    for r in (9, 20):                                             # the grooves, cut through at a crossing
        for a in range(32):
            if h:
                px[a, r + 2] = RAIL_GROOVE
            if v:
                px[r + 2, a] = RAIL_GROOVE
    return im


def tram_pole():
    """An overhead-wire pole: a green steel mast, a tubular bracket arm on a
    tie rod, the contact wire hung from two insulators. No snow lies on it."""
    im, d = canvas(2, 3)                 # 64 x 96
    d.rectangle([7, 6, 11, 90], fill=TRAM)
    d.line([(7, 6), (7, 90)], fill=TRAM_HI); d.rectangle([10, 6, 11, 90], fill=TRAM_LO)
    d.rectangle([6, 3, 12, 6], fill=TRAM_LO); d.rectangle([8, 1, 10, 3], fill=TRAM_HI)       # the cap
    d.rectangle([4, 86, 14, 93], fill=STONE_DK); d.line([(4, 86), (14, 86)], fill=STONE_LO)
    for y in (40, 44):                                            # a band and a number plate
        d.line([(7, y), (11, y)], fill=TRAM_LO)
    d.rectangle([6, 54, 12, 60], fill=CREAM); d.line([(8, 56), (10, 56)], fill=INK); d.line([(8, 58), (10, 58)], fill=INK)
    d.rectangle([12, 22, 58, 24], fill=TRAM)                      # the bracket arm
    d.line([(12, 22), (58, 22)], fill=TRAM_HI); d.line([(12, 24), (58, 24)], fill=TRAM_LO)
    d.rectangle([58, 21, 60, 25], fill=TRAM_LO)
    d.line([(11, 8), (56, 21)], fill=STONE_DK)                    # the tie rod
    d.line([(12, 34), (26, 25)], fill=TRAM_LO); d.line([(12, 35), (27, 25)], fill=TRAM_LO)    # the strut
    for x in (34, 52):                                            # insulators and droppers
        d.rectangle([x, 25, x + 2, 28], fill=CREAM); d.line([(x, 27), (x + 2, 27)], fill=CREAM_LO)
        d.line([(x + 1, 29), (x + 1, 32)], fill=INK)
    d.line([(24, 33), (63, 33)], fill=INK)                        # the contact wire
    d.line([(24, 34), (63, 34)], fill=STONE_DK)
    drift(d, 0, 19, 95, 3, seed=7)
    outline(im)
    return im


def _wob(t, period=32):
    return int(round(1.5 * math.sin(2 * math.pi * t / period) + math.sin(2 * math.pi * 3 * t / period + 1)))


def _bank_colour(depth, total, x, y):
    """A ploughed bank: bright on its crest, blue in its foot, road grit in it."""
    if depth < 2:
        return WHITE
    if depth >= total - 3:
        return SNOW_SH
    if depth >= total * 0.55:
        return rgb('9aa3b8') if (x * 7 + y * 11) % 17 == 0 else SNOW_LO
    return SNOW_LO if (x * 5 + y * 3) % 19 == 0 else SNOW


def snowbank(kind):
    """What the plough leaves along a kerb. h tiles east-west, v north-south
    (drawn three tiles long and the middle cut out, so the ends join); pile is
    one heap on its own. Transparent: they stand on the pavement cell."""
    if kind == 'h':
        big = Image.new('RGBA', (96, 32), CLEAR); px = big.load()
        for x in range(96):
            top = 11 + _wob(x % 32) + (2 if (x % 32) in range(18, 26) else 0)
            for y in range(top, 30):
                px[x, y] = _bank_colour(y - top, 30 - top, x % 32, y)
        outline(big)
        return big.crop((32, 0, 64, 32))
    if kind == 'v':
        big = Image.new('RGBA', (32, 96), CLEAR); px = big.load()
        for y in range(96):
            x0, x1 = 7 + _wob(y % 32), 24 - _wob((y + 11) % 32)
            for x in range(x0, x1 + 1):
                t = x - x0
                c = WHITE if t < 3 else (SNOW_SH if x1 - x < 3 else
                                         (SNOW_LO if x1 - x < 7 or (x * 5 + (y % 32) * 3) % 19 == 0 else SNOW))
                if x1 - x in (4, 5) and (x * 7 + (y % 32) * 11) % 17 == 0:
                    c = rgb('9aa3b8')
                px[x, y] = c
        outline(big)
        return big.crop((0, 32, 32, 64))
    im = Image.new('RGBA', (32, 32), CLEAR); px = im.load()
    for x in range(3, 29):
        t = (x - 3) / 25
        top = 29 - int(round(17 * math.sin(math.pi * t) ** 0.6)) + (x % 5 == 0)
        for y in range(top, 30):
            px[x, y] = _bank_colour(y - top, 30 - top, x, y)
            if x > 20 and px[x, y] == SNOW:
                px[x, y] = SNOW_LO
    outline(im)
    return im


PRINTS = ((12, 18, 0), (22, 26, 0), (34, 16, 0), (44, 25, 0),     # boot prints (x, y, heading): two walkers
          (50, 40, 1), (40, 46, 1), (28, 40, 1), (18, 47, 1))


def snow_path(role):
    """A path trodden through the snow: the snow field's own texture a shade
    lower (so it is still snow, not ice), a soft shadow under its north and
    west banks, a lit lip on the south and east ones, boot prints. Opaque,
    drawn at the snow tile's own resolution; the wavy edge has the tile's
    period, so neighbours join."""
    im = Image.open(f'{SPR}/snow-autotile_center.png').convert('RGBA')
    px = im.load()
    tail = '' if role == 'center' else role.split('-')[-1]

    def inside(x, y):
        dn = y - (9 + _wob(x, 64)) if 'n' in tail else 99
        ds = (54 - _wob(x + 20, 64)) - y if 's' in tail else 99
        dw = x - (9 + _wob(y + 40, 64)) if 'w' in tail else 99
        de = (54 - _wob(y + 9, 64)) - x if 'e' in tail else 99
        a, b = min(dn, ds), min(dw, de)
        if a < 12 and b < 12:                                     # a rounded corner
            dist = 12 - math.hypot(12 - a, 12 - b)
        else:
            dist = min(a, b)
        shade = (dn if dn < ds else 99, dw if dw < de else 99)    # distance from a shadowing bank
        return dist, min(shade), (ds if ds <= dn else 99, de if de <= dw else 99)

    for y in range(64):
        for x in range(64):
            dist, shade, lit = inside(x, y)
            r, g, b, _ = px[x, y]
            if dist < -2:
                continue
            if dist < 0:                                          # the lip of the bank
                if min(lit) < 0 and min(lit) >= -2:
                    px[x, y] = (247, 250, 255, 255)
                continue
            drop = (15, 13, 8)
            if shade < 3 and dist < 3:                            # the bank's shadow on the path
                drop = (27, 24, 15) if (dist < 2 or (x + y) % 2) else (19, 17, 11)
            elif dist < 2:
                drop = (8, 7, 4)
            px[x, y] = (r - drop[0], g - drop[1], b - drop[2], 255)
    for fx, fy, heading in PRINTS:
        w, h = (5, 3) if heading == 0 else (3, 5)
        if inside(fx, fy)[0] < 5 or inside(fx + w, fy + h)[0] < 5:
            continue
        for yy in range(h):
            for xx in range(w):
                if (xx in (0, w - 1)) and (yy in (0, h - 1)):
                    continue
                px[fx + xx, fy + yy] = (201, 212, 232, 255)
        for xx in range(1, w - 1):                                # its lit lower lip
            px[fx + xx, fy + h] = (236, 243, 251, 255)
    return im


# ==============================================================================
def rows(w, r0, r1):
    return [[c, r] for r in range(r0, r1 + 1) for c in range(w)]


# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH under it (gates)
#   glow: DayNight gives the key a night halo (it matches /lamp-post|-lanterns/)
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'ground' = a floor
#          tile, 'overlay' = flat on the ground over the floor (e.g. Over Floor)
PIECES = [
    ('sapporo-station-front_0_0', station_front, (10, 7), 'Station front', dict(
        door=[[4, 6], [5, 6]], solid=rows(10, 4, 6)),
     'Sapporo Station: a four-storey glazed hall with the big star clock and a SAPPORO board, three-storey '
     'stone wings, a long snow-covered canopy over lit shop windows, a stub of the station tower behind the '
     'east wing. Four doors under the clock (two cells).'),
    ('sapporo-akarenga_0_0', akarenga, (7, 6), 'Station front', dict(
        door=[[3, 5]], solid=rows(7, 3, 5)),
     'The Former Hokkaido Government Office (Akarenga): red brick, arched windows in white stone, slate roof '
     'under snow, end pavilions, a centre gable with the red pioneer star, the green copper dome on its drum. '
     'The anchor that tells Station front from the Clock Tower block.'),
    ('sapporo-office-brick_0_0', office_brick, (4, 7), 'Station front / Clock Tower block (filler)', dict(
        door=[[2, 6]], solid=rows(4, 4, 6)),
     'Filler, not an identity piece: red-brick office block with stone string courses, sash windows, a glazed '
     'stair tower, copper cornice, arched stone ground floor, door under a red awning. Keep it away from the '
     'station (it is as tall).'),
    ('sapporo-office-glass_0_0', office_glass, (5, 6), 'Station front / Clock Tower block (filler)', dict(
        door=[[2, 5]], solid=rows(5, 3, 5)),
     'Filler: brick-framed glass block, five ribbon-window floors, rooftop KITA board with the red pioneer '
     'star on a white roundel, glass lobby with sliding doors.'),
    ('sapporo-konbini_0_0', konbini, (4, 3), 'any (drawn for the Clock Tower block)', dict(
        door=[[1, 2]], solid=rows(4, 1, 2)),
     'A konbini front in the house style, to stand where the line-art seven-eleven_0_0 tile cannot: white '
     'fascia with an orange and a teal stripe and konbini in kana (an invented mark, no brand), lit glass '
     'front with shelves, automatic doors, a nobori. Note it is 4x3; seven-eleven_0_0 is 3x4.'),
    ('tanukikoji-gate_0_0', tanuki_gate, (4, 4), 'Tanukikoji', dict(
        solid=[[0, 3], [3, 3]], walk=[[1, 3], [2, 3]]),
     "The arcade's main arch, facing south: tanuki medallion on a red curved board reading TANUKI KOJI, "
     'bulbs under the arch, snow on top (none at its feet: it stands on the brick). Set it in the south row.'),
    ('tanukikoji-rib_0_0', tanuki_rib, (4, 3), 'Tanukikoji', dict(
        solid=[[0, 2], [3, 2]], walk=[[1, 2], [2, 2]]),
     "A rib of the arcade roof: the gate's arch without the board - white steel, glass between the chords, "
     'bulbs, three hanging banners; no snow (it is under the roof). Repeatable: across a side entrance in '
     'either row, or one after another along a north-south stretch.'),
    ('tanukikoji-shop-souvenir_0_0', shop_souvenir, (3, 4), 'Tanukikoji', dict(
        door=[[1, 3]], solid=rows(3, 1, 3)),
     'North-row shop module: OMIYAGE timber board, lit windows of gift boxes, navy noren, carved bear by the '
     'door. The three modules tile left-right under one continuous glass arcade roof (posts meet at the seams).'),
    ('tanukikoji-shop-crab_0_0', shop_crab, (3, 4), 'Tanukikoji', dict(
        door=[[1, 3]], solid=rows(3, 1, 3)),
     'North-row shop module: seafood shop, big red crab over the door, kani kana board, blue tiled front, '
     'trays of ice; the entrance is a pair of lamplit timber sliding doors under a white noren.'),
    ('tanukikoji-shop-drug_0_0', shop_drug, (3, 4), 'Tanukikoji', dict(
        door=[[1, 3]], solid=rows(3, 1, 3)),
     'North-row shop module: drugstore-style front, yellow kusuri board with green crosses, bright glazed '
     'shelves, sale posters, wire bins of tissue boxes.'),
    ('tanukikoji-south-row-a_0_0', arcade_south, (3, 3), 'Tanukikoji', dict(
        solid=rows(3, 1, 2)),
     "The arcade's facing side: the south row of shops seen from behind (service door, crates, kitchen "
     'window, AC units, shutter, steaming vent) under the same glass roof. Tiles left-right with itself and '
     "with -b; its top row is roof only and is meant to overhang the street's southern row (you walk behind "
     'it and Occlusion fades it), so the street is roofed from both sides. No door.'),
    ('tanukikoji-south-row-b_0_0', lambda: arcade_south('b'), (3, 3), 'Tanukikoji', dict(
        solid=rows(3, 1, 2)),
     'The same, bays in another order on grey render, so a run of the south row does not repeat.'),
    ('tanukikoji-end-sign_0_0', arcade_end, (1, 4), 'Tanukikoji', dict(
        solid=[[0, 3]]),
     'The east / west end of the north row: one more bay of the roof, a post and the upright red sign '
     '(tanuki in kana) that marks an east-west entrance. Tiles against a shop module on either side.'),
    ('susukino-neon-corner_0_0', neon_corner, (5, 7), 'Susukino', dict(
        door=[[2, 6]], solid=rows(5, 4, 6)),
     "The crossing's neon building: an INVENTED mascot board (a winking Hokkaido fox, a black-socked paw "
     'round a mug of beer, on pink/gold rays; not the Nikka king), Susukino kana board, ramen / BAR boards, '
     'upright karaoke / SNACK / SUSHI signs on the side wall, two rows of lit windows, glass corner shop.'),
    ('susukino-ramen-gate_0_0', ramen_gate, (3, 3), 'Susukino', dict(
        solid=[[0, 2], [2, 2]], walk=[[1, 2]]),
     'Ramen alley gate: red posts, small tiled roof with snow, yellow ramen kana board with bowls, a row of '
     'red and white paper lanterns. The alley is one cell wide. It does not glow by itself: stand a '
     'ramen-alley-lanterns post beside it.'),
    ('susukino-karaoke_0_0', karaoke, (4, 5), 'Susukino', dict(
        door=[[1, 4]], solid=rows(4, 2, 4)),
     'Karaoke / bar front: purple cladding, pink neon karaoke kana sign with microphone, two floors of rooms '
     'each lit its own colour with singers, upright BAR sign, pink striped awning, wooden bar door.'),
    ('susukino-neon-lanterns_0_0', neon_lanterns, (1, 2), 'Susukino', dict(
        solid=[[0, 1]], glow=True),
     'A pole of three small neon signs (pink, cyan, amber). Stand these in front of the neon corner and the '
     'karaoke front: they are what lights the district at night.'),
    ('ramen-alley-lanterns_0_0', lantern_post, (1, 2), 'Susukino', dict(
        solid=[[0, 1]], glow=True),
     'A timber post hung with four red and white paper lanterns, for the ramen alley and its gate.'),
    ('snow-sculpture-castle_0_0', snow_castle, (5, 4), 'Odori Park', dict(
        solid=rows(5, 2, 3)),
     'The big snow sculpture: a three-storey castle keep with turrets carved in snow on a stepped block, '
     'steps to a gate, festival board, rope posts.'),
    ('snow-sculpture-tanuki_0_0', snow_tanuki, (2, 3), 'Odori Park', dict(
        solid=rows(2, 2, 2)),
     'Small snow sculpture: a tanuki in a straw hat with a sake flask, on a block.'),
    ('snow-sculpture-bear_0_0', snow_bear, (3, 2), 'Odori Park', dict(
        solid=rows(3, 1, 1)),
     'Small snow sculpture (now 3x2): a brown bear side on, head low, legs apart, a salmon hanging from its '
     'jaws, on a block.'),
    ('snowfest-stall-corn_0_0', lambda: stall('corn'), (3, 3), 'Odori Park', dict(
        solid=rows(3, 1, 2)),
     'Snow-festival tent stall: yellow striped peaked canvas with snow, corn kana board, charcoal grill of '
     'cobs, red striped counter cloth. Counter faces south (bump from the row below, as a yatai).'),
    ('snowfest-stall-drinks_0_0', lambda: stall('drinks'), (3, 3), 'Odori Park', dict(
        solid=rows(3, 1, 2)),
     'Snow-festival tent stall: blue striped tent, HOT board with a cup, steaming urn and paper cups.'),
    ('odori-fountain_0_0', odori_fountain, (3, 3), 'Odori Park', dict(
        solid=rows(3, 1, 2)),
     "Odori's fountain in winter (replaces odori-arch): the round basin frozen over, snow on the rim and on "
     'its two bowls, icicles, pink / cyan / warm festival lights set in the ice.'),
    ('odori-lamp-post_0_0', odori_lamp, (1, 2), 'Odori Park', dict(
        solid=[[0, 1]], glow=True),
     "Odori Park's lamp: a white globe on a dark green iron post, snow on its cap. Its key holds `lamp-post`, "
     'so its head has a halo at night. Only the foot collides.'),
    ('odori-bench_0_0', odori_bench, (2, 1), 'Odori Park', dict(
        solid=rows(2, 0, 0)),
     "A park bench in Odori's dark green, snow lying on the seat and along the back. Faces south."),
    ('tram-rail-h_0_0', lambda: tram_rail('h'), (1, 1), 'Susukino', dict(layer='ground'),
     'Streetcar track running east-west: an OPAQUE ground tile that replaces the road tile (not an overlay '
     'any more) - sett bed, two grey steel rails each with a dark groove, asphalt strip top and bottom. Not '
     'named train-track*, so AmbientTrains ignores it.'),
    ('tram-rail-v_0_0', lambda: tram_rail('v'), (1, 1), 'Susukino', dict(layer='ground'),
     'Streetcar track running north-south (opaque ground tile).'),
    ('tram-rail-cross_0_0', lambda: tram_rail('cross'), (1, 1), 'Susukino', dict(layer='ground'),
     'Streetcar track crossing (opaque ground tile): both pairs of rails, grooves cut through.'),
    ('tram-pole_0_0', tram_pole, (2, 3), 'Susukino', dict(
        solid=[[0, 2]]),
     'Overhead-wire pole: green steel mast in the left column, tubular bracket arm on a tie rod, two '
     'insulators and a length of contact wire over the right column. No snow on the arm.'),
    ('sapporo-streetcar_0_0', streetcar, (5, 3), 'Susukino', dict(
        solid=rows(5, 1, 2)),
     'A green and cream Sapporo streetcar, side on, pantograph up, snow on the roof, the red pioneer star on '
     "a white roundel; the top row is only the pantograph. Feet on the bottom edge like train-green.png, so "
     "AmbientTrains' placement maths fits it, BUT no existing mover will pick it (trains come from station "
     'liveries and only run on train-track* rows): park it at a stop (solid), or it needs a small mover change.'),
    ('snowbank-h_0_0', lambda: snowbank('h'), (1, 1), 'any (kerbs)', dict(solid=[[0, 0]], layer='overlay'),
     'A ploughed snowbank along a kerb, tiling east-west (transparent; stands on the pavement cell beside '
     'the road). Leave gaps at crossings and doors.'),
    ('snowbank-v_0_0', lambda: snowbank('v'), (1, 1), 'any (kerbs)', dict(solid=[[0, 0]], layer='overlay'),
     'The same bank tiling north-south.'),
    ('snowbank-pile_0_0', lambda: snowbank('pile'), (1, 1), 'any (kerbs)', dict(solid=[[0, 0]], layer='overlay'),
     'One shovelled heap on its own: ends a run of bank, or sits at a corner.'),
]
FAMILIES = [
    ('arcade-brick-autotile', arcade_brick, True, 'Tanukikoji',
     "Basket-weave red brick with a stone kerb: the arcade's floor. Keep it to Tanukikoji."),
    ('snow-path-autotile', snow_path, False, 'Odori Park',
     "A path trodden through the snow: the snow tile's own texture a shade lower, a soft shadow under the "
     'north and west banks, a lit lip on the south and east ones, boot prints. Opaque (snow outside the edge).'),
]
SPRITES = {key: (fn, True) for key, fn, *_ in PIECES}      # key: (builder, pixel-double?)
for _fam, _fn, _double, *_ in FAMILIES:
    for _r in ROLES:
        SPRITES[f'{_fam}_{_r}'] = ((lambda r=_r, fn=_fn: fn(r)), _double)


def build():
    built = {}
    for key, (fn, double) in SPRITES.items():
        im = fn()
        if double:
            im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        built[key] = im
    return built


def manifest(built, out):
    """What the rebuild needs to place these, as JSON (nothing here is registered
    in config.json)."""
    sprites = []
    for key, _fn, (w, h), district, m, desc in PIECES:
        im = built[key]
        assert im.size == (w * 64, h * 64), key
        doors = m.get('door') or []
        solid = m.get('solid', [])
        assert all(dc in solid for dc in doors), key
        sprites.append({
            'key': key, 'file': f'gamev2/{SPR}/{key}.png', 'size': [w, h], 'px': list(im.size),
            'anchor': [round(32 / im.width, 6), round(32 / im.height, 6)],
            'door': doors[0] if doors else None, 'doors': doors,
            'solid': solid, 'walk_through': m.get('walk', []),
            'night_halo': bool(m.get('glow')), 'layer': m.get('layer', 'standing'),
            'district': district, 'description': desc,
        })
    doc = {
        'tool': 'gamev2/tools/generate_sapporo_art.py',
        'run': 'cd gamev2 && python3 tools/generate_sapporo_art.py [--sheet out.png] [--scenes dir] [--manifest out.json]'
               '   (any python3 that has Pillow)',
        'notes': [
            "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per "
            "cell and pixel-doubled, as generate_hokkaido.py / generate_fukuoka_art.py do); 'size' is in cells.",
            'Nothing is registered: config.json, tilePalette, spriteMetadata, prefabs, generators, '
            'check_generators.py and docs are untouched. To register a multi-cell sprite follow '
            'generate_hokkaido.py: spriteMetadata {frameCount:1, anchorX: 32/widthPx, anchorY: 32/heightPx} '
            "(centre of the top-left cell; that is 'anchor'); 1x1 tiles use 0.5/0.5.",
            "'door' / 'doors', 'solid' and 'walk_through' are [col,row] from the sprite's top-left cell. 'solid' is "
            'the suggested footprint (rows above it are roof or sky the player walks behind). A gate lists the '
            "cells you walk through under it in 'walk_through'; only its post cells are solid.",
            "Night: the game has no lit-window or emissive layer. DayNight.buildGlows puts one additive halo on "
            "each CELL whose tile key matches /lamp-post|-lanterns/ (how Fukuoka's yatai-lanterns glow), at the "
            "tile's own cell, so renaming a 5x7 building would light only its top-left corner. 'night_halo': true "
            'marks the keys that match: susukino-neon-lanterns_0_0 and ramen-alley-lanterns_0_0 (both 1x2 posts). '
            'Plan one in front of the neon corner, the karaoke front and the ramen gate; nothing else here glows.',
            'All shop / sign names are look-alikes or generic words (OMIYAGE, KITA, BAR, SNACK, SUSHI, kana for '
            'crab / medicine / ramen / karaoke / Susukino / corn / konbini / tanuki); no real brand artwork. The '
            "star on the station clock is a plain blue five-pointed star (the station's star clock); the KITA "
            "board, the streetcar and the Akarenga carry the red pioneer star, as the Clock Tower's gable does.",
            'A covered Tanukikoji: north row = tanukikoji-shop-* (+ end-sign at the ends), three rows of '
            'arcade-brick street, south row = tanukikoji-south-row-a / -b with its top row over the southern street '
            'row, tanukikoji-gate set in the south row (from Susukino), tanukikoji-rib across a side entrance.',
            'Removed since the first pass: odori-arch_0_0 (replaced by odori-fountain_0_0). tram-rail-* changed '
            'from transparent overlays to opaque ground tiles. snow-sculpture-bear_0_0 changed from 2x2 to 3x2. '
            'sapporo-station-front_0_0 changed from 7x5 to 10x7.',
        ],
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, _fn, _double, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/sapporo_art_sheet.png',
            'scenes': [f'.agent-queue/shots/sapporo_art_{n}.png'
                       for n in ('station', 'clocktower', 'odori', 'tanukikoji', 'susukino')],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


# ---- previews (not part of the game) --------------------------------------------
def spr(name):
    return Image.open(f'{SPR}/{name}.png').convert('RGBA')


GRID = ('corner-nw', 'edge-n', 'corner-ne', 'edge-w', 'center', 'edge-e', 'corner-sw', 'edge-s', 'corner-se')


def sheet(built, out):
    """Everything on one snow-coloured sheet, at 4x the drawn size (2x the file)."""
    keys = [k for k, _fn, size, *_ in PIECES if size != (1, 1)]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1500 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + 64 * 3 + 60
    im = Image.new('RGBA', (1540, H), rgb('e9eef6'))
    y = 20
    for r in lines:
        h = max(built[k].height for k in r)
        x = 20
        for k in r:
            im.alpha_composite(built[k], (x, y + h - built[k].height))
            x += built[k].width + 24
        y += h + 40
    x = 20
    for fam, *_ in FAMILIES:                                      # each family as a 3x3 patch, on snow
        for i, r in enumerate(GRID):
            im.alpha_composite(built[f'{fam}_{r}'], (x + (i % 3) * 64, y + (i // 3) * 64))
        x += 3 * 64 + 24
    road = spr('road-plain_0_0')                                  # the track where two lines cross, in a road
    plan = ('.v.', 'hch', '.v.')
    for j, row in enumerate(plan):
        for i, ch in enumerate(row):
            name = {'h': 'tram-rail-h_0_0', 'v': 'tram-rail-v_0_0', 'c': 'tram-rail-cross_0_0'}.get(ch)
            im.alpha_composite(built[name] if name else road, (x + i * 64, y + j * 64))
    x += 3 * 64 + 24
    snow = spr('snow-autotile_center')                            # the snowbanks, on snow by a road
    for j in range(3):
        for i in range(4):
            im.alpha_composite(road if (i == 3 or j == 2) else snow, (x + i * 64, y + j * 64))
    for i in range(2):
        im.alpha_composite(built['snowbank-h_0_0'], (x + i * 64, y + 64))
    im.alpha_composite(built['snowbank-pile_0_0'], (x + 2 * 64, y + 64))
    for j in range(1):
        im.alpha_composite(built['snowbank-v_0_0'], (x + 2 * 64, y + j * 64))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


class Scene:
    def __init__(self, built, w, h):
        self.b, self.w, self.h = built, w, h
        self.im = Image.new('RGBA', (w * 64, h * 64), CLEAR)
        snow = spr('snow-autotile_center')
        for y in range(h):
            for x in range(w):
                self.im.alpha_composite(snow, (x * 64, y * 64))
        self.things = []

    def get(self, name):
        return self.b[name] if name in self.b else spr(name)

    def floor(self, fam, *rects):
        """An autotile family over the union of (x0, y0, x1, y1) rectangles; a
        cell's role comes from which neighbours are missing."""
        cells = {(x, y) for x0, y0, x1, y1 in rects for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}
        for x, y in sorted(cells):
            ns = 'n' if (x, y - 1) not in cells else ('s' if (x, y + 1) not in cells else '')
            ew = 'w' if (x - 1, y) not in cells else ('e' if (x + 1, y) not in cells else '')
            role = 'center' if not (ns or ew) else (f'corner-{ns}{ew}' if ns and ew else f'edge-{ns or ew}')
            self.im.alpha_composite(self.get(f'{fam}_{role}'), (x * 64, y * 64))

    def tile(self, name, x, y):
        self.im.alpha_composite(self.get(name), (x * 64, y * 64))

    def road(self, y, x0, x1, tram=False):
        for x in range(x0, x1 + 1):
            self.tile('road-edge-top_0_0', x, y)
            self.tile('tram-rail-h_0_0' if tram else 'road-div-horizontal_0_0', x, y + 1)
            self.tile('road-edge-bottom_0_0', x, y + 2)

    def put(self, name, x, base):
        """Stand a sprite with its left edge on cell x and its feet on row `base`."""
        self.things.append((base, x, name))

    def save(self, out):
        for base, x, name in sorted(self.things):
            im = self.get(name)
            self.im.alpha_composite(im, (x * 64, (base + 1) * 64 - im.height))
        self.im.save(out)
        print('scene ->', out, self.im.size)


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    # Station front: the station across the plaza, the Akarenga to one side, a filler block to the other
    s = Scene(built, 27, 13)
    s.floor('grey-brick-autotile', (5, 8, 18, 9))
    s.road(10, 0, 26)
    s.put('sapporo-office-glass_0_0', 0, 8); s.put('sapporo-station-front_0_0', 6, 7)
    s.put('sapporo-akarenga_0_0', 19, 8)
    for x in (0, 1, 2, 3, 6, 7, 8, 9, 14, 15, 16, 17, 20, 21, 25, 26):
        s.put('snowbank-h_0_0', x, 9)
    s.put('snowbank-pile_0_0', 4, 9); s.put('snowbank-pile_0_0', 22, 9)
    s.put('blue-lamp-post_0_0', 5, 9); s.put('blue-lamp-post_0_0', 18, 9)
    s.put(me, 10, 8); s.put(me, 12, 9); s.put(me, 5, 9); s.put(me, 23, 9); s.put(me, 17, 12)
    s.save(f'{outdir}/sapporo_art_station.png')
    # Clock Tower block: the Clock Tower between a filler block and the konbini, banks along the kerb
    s = Scene(built, 22, 12)
    s.floor('grey-brick-autotile', (0, 8, 21, 8))
    s.road(9, 0, 21)
    s.put('sapporo-office-brick_0_0', 1, 7); s.put('sapporo-clock-tower_0_0', 7, 7)
    s.put('sapporo-konbini_0_0', 15, 7)
    for x in (0, 1, 2, 5, 6, 7, 12, 13, 14, 19, 20, 21):
        s.put('snowbank-h_0_0', x, 8)
    s.put('snowbank-pile_0_0', 3, 8); s.put('snowbank-pile_0_0', 18, 8)
    s.put('blue-lamp-post_0_0', 6, 7); s.put('blue-lamp-post_0_0', 13, 7)
    s.put(me, 9, 8); s.put(me, 4, 8); s.put(me, 16, 8); s.put(me, 11, 11)
    s.save(f'{outdir}/sapporo_art_clocktower.png')
    # Odori Park: sculptures, stalls and the frozen fountain on a trodden path, the TV Tower at the east end
    s = Scene(built, 24, 14)
    s.floor('snow-path-autotile', (0, 10, 18, 11), (9, 5, 10, 9))
    s.floor('grey-brick-autotile', (18, 9, 23, 13))
    s.put('sapporo-tv-tower_0_0', 18, 12)
    s.put('snow-sculpture-castle_0_0', 2, 8); s.put('snow-sculpture-tanuki_0_0', 12, 8)
    s.put('snow-sculpture-bear_0_0', 14, 9)
    s.put('odori-fountain_0_0', 6, 9)
    s.put('snowfest-stall-corn_0_0', 1, 13); s.put('snowfest-stall-drinks_0_0', 5, 13)
    s.put(me, 9, 7); s.put(me, 4, 10); s.put(me, 13, 10); s.put(me, 16, 10); s.put(me, 3, 13)
    s.save(f'{outdir}/sapporo_art_odori.png')
    # Tanukikoji: shops along the north side, the south row's roof over the street, the gate and a rib
    s = Scene(built, 20, 11)
    s.floor('arcade-brick-autotile', (0, 5, 19, 7), (7, 8, 8, 9), (11, 2, 12, 4))
    s.put('tanukikoji-end-sign_0_0', 0, 4)
    for i, shop in enumerate(('souvenir', 'crab', 'drug')):
        s.put(f'tanukikoji-shop-{shop}_0_0', 1 + i * 3, 4)
    s.put('tanukikoji-rib_0_0', 10, 4)
    s.put('tanukikoji-shop-crab_0_0', 14, 4); s.put('tanukikoji-shop-souvenir_0_0', 17, 4)
    for i, x in enumerate((0, 3, 10, 13, 16)):
        s.put(f'tanukikoji-south-row-{"ab"[i % 2]}_0_0', x, 9)
    s.put('tanukikoji-gate_0_0', 6, 9)
    s.put(me, 5, 5); s.put(me, 8, 6); s.put(me, 15, 6); s.put(me, 12, 4); s.put(me, 8, 10)
    s.save(f'{outdir}/sapporo_art_tanukikoji.png')
    # Susukino: the neon corner on the crossing, the streetcar on its track, ramen alley and karaoke
    s = Scene(built, 22, 13)
    s.road(9, 0, 21, tram=True)
    s.put('susukino-karaoke_0_0', 0, 8); s.put('susukino-ramen-gate_0_0', 4, 8)
    s.put('ramen-alley-lanterns_0_0', 7, 8)
    s.put('susukino-neon-corner_0_0', 8, 8); s.put('susukino-neon-lanterns_0_0', 13, 8)
    s.put('sapporo-konbini_0_0', 14, 8)
    s.put('tram-pole_0_0', 19, 8); s.put('tram-pole_0_0', 1, 12)
    s.put('sapporo-streetcar_0_0', 9, 10)
    for x in (4, 5, 6, 7, 12, 13, 14, 15):
        s.put('snowbank-h_0_0', x, 12)
    s.put('snowbank-pile_0_0', 8, 12); s.put('snowbank-pile_0_0', 11, 12)
    s.put(me, 5, 8); s.put(me, 10, 8); s.put(me, 9, 12); s.put(me, 18, 12)
    s.save(f'{outdir}/sapporo_art_susukino.png')


def register(built, path='config.json'):
    """spriteMetadata and tileNames for every sprite (the anchor is the centre of
    the top-left cell; a ground tile's is its own centre). Rewrites config.json
    only if something changed, so a re-run is a no-op."""
    cfg = json.load(open(path))
    before = json.dumps(cfg, sort_keys=True)
    for key, im in built.items():
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = key.rsplit('_', 1)[0] if 'autotile' in key else key[:-len('_0_0')]
    if json.dumps(cfg, sort_keys=True) != before:
        json.dump(cfg, open(path, 'w'), indent=2, sort_keys=True)


def main():
    built = build()
    for key, im in built.items():
        im.save(f'{SPR}/{key}.png')
        if 'autotile' not in key:
            print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    print(', '.join(f[0] for f in FAMILIES) + f': {len(ROLES)} roles each')
    register(built)
    for flag, fn in (('--sheet', sheet), ('--scenes', scenes), ('--manifest', manifest)):
        if flag in sys.argv:
            fn(built, sys.argv[sys.argv.index(flag) + 1])


if __name__ == '__main__':
    main()
