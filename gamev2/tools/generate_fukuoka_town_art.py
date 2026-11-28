#!/usr/bin/env python3
"""generate_fukuoka_town_art.py — Fukuoka's own town pieces, drawn ahead of its rebuild (issue #219).

tools/generate_fukuoka_art.py gave Fukuoka its landmarks (the tower, the yatai,
the Yamakasa float, Canal City and its fountain, Dazaifu's hall, bridge and
plum). Everything between them is shared kit: the station is a townhouse,
there are three stock high-rises, a generic east block, the machiya row and a
small pagoda. These are the pieces the rebuild replaces that kit with, in the
style of generate_sapporo_art.py: shaded pixel art in the GuttyKreum palette,
drawn at 32px per cell and pixel-doubled, lit from the west, a 1px ink outline.
Mid November: mild, NO snow, the Christmas illuminations going up.

Hakata Station
  fukuoka-hakata-station_0_0      9x6  the wide charcoal-tile station front: the
                                       big clock, a roof garden, a glass canopy
  fukuoka-xmas-hut-wine_0_0       3x3  the forecourt's Christmas market: timber
  fukuoka-xmas-hut-wurst_0_0      3x3  huts under fir garlands and string lights
  fukuoka-xmas-hut-gifts_0_0      3x3  (mulled wine, sausages, ornaments)
  fukuoka-xmas-tree_0_0           3x5  the market's tall lit tree
  fukuoka-illumination-arch_0_0   3x3  a fir-garland arch of lights, walked under
  fukuoka-ramen-shop_0_0          3x4  a tonkotsu ramen shop: a red noren, a
                                       stock-pot flue with a pork-bone steam plume
  fukuoka-mentaiko-shop_0_0       3x3  a mentaiko (spiced cod roe) shop
Nakasu
  fukuoka-neon-bar_0_0            4x6  a bar building of stacked signs, to face the river
  fukuoka-pub_0_0                 4x4  the mock-Tudor pub
  fukuoka-river-rail_0_0          1x1  the riverside railing, and the same with a
  fukuoka-river-rail-lanterns_0_0 1x2  lantern post (it gets the lantern halo)
  fukuoka-nakasu-gate_0_0         4x4  the district's neon gate sign, walked under
Canal City (canal-city_0_0 is already its own and has its arch: not redrawn)
  fukuoka-canal_0_0 / -jets       1x2  a strip of the mall's canal between red and
  fukuoka-canal-end-e/-w_0_0      1x2  cream quays; with fountain jets; its ends
  fukuoka-canal-bridge_0_0        1x2  a footbridge over it (flat, walked on)
Old Hakata
  fukuoka-tochoji-hall_0_0        5x4  Tochoji's low wooden hall, the great-buddha plaque
  fukuoka-hakata-ori-shop_0_0     4x4  a Hakata-ori textile merchant's front
  fukuoka-senbei-shop_0_0         3x4  a rice-cracker shop, its griddle on the street
  fukuoka-hakata-bei*_0_0              the Hakata-bei wall, stones and broken roof
                                       tiles set in clay: straight (1x2);
                                       -corner-e, -corner-w, -v, -end (1x3)
Momochi
  fukuoka-beach-house_0_0         4x3  a seaside cafe
  fukuoka-beach-umbrella-a/-b_0_0 2x2  a parasol with a lounger / with a towel
  fukuoka-lifeguard-chair_0_0     2x3  the lifeguard's high chair
  fukuoka-wet-sand-e/-n/-s_0_0    1x1  the beach's wet edge and the foam line
  fukuoka-shallows-e/-n/-s_0_0    1x1  ankle-deep water over sand (walkable)
Dazaifu
  fukuoka-umegae-stall_0_0        3x3  an umegae-mochi stall with its griddle
  fukuoka-lattice-cafe_0_0        4x4  an invented cafe behind a woven timber lattice
  fukuoka-stone-lantern_0_0       1x2  the approach's stone lantern
  fukuoka-ox-statue_0_0           2x2  the shrine's bronze ox
  fukuoka-hedge*_0_0              1x1  a clipped sasanqua hedge: straight, -v, four
                                       corners, four ends
Ground (9 autotile roles each, opaque)
  fukuoka-station-plaza-autotile_*     the forecourt: pale granite, charcoal insets
  fukuoka-riverwalk-autotile_*         Nakasu's promenade: mauve herringbone brick
  fukuoka-canal-paving-autotile_*      Canal City: warm fan-laid setts
  fukuoka-beach-autotile_*             Momochi: rippled sand

This tool writes the PNGs into assets/sprites/ and NOTHING else: no config.json,
no prefabs. generate_fukuoka_art.py and its sprites are untouched.

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs Pillow. Run from gamev2/:
    python3 tools/generate_fukuoka_town_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import (rgb, canvas, outline, CLEAR, INK, NAVY, CREAM_DK,          # noqa: E402
                               WHITE, GLASS, GLASS_HI, WOOD_DK, STONE, STONE_LO, STONE_DK, GOLD, AMBER)
from generate_sendai_art import blob, BRONZE, BRONZE_HI, BRONZE_LO                          # noqa: E402
from generate_sapporo_art import glyphs, glazing, glass_door, lantern, star                 # noqa: E402
from generate_kanazawa_art import FONT as _FONT, KANA as _KANA, h3, curve_rows, night, roof, shade   # noqa: E402
from generate_sendai_town_art import bar, glyph, puff, grounded, family                     # noqa: E402
from generate_sendai_art import foliage                                                     # noqa: E402
from house_look import tone                                                                 # noqa: E402

SPR = 'assets/sprites'
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')

# ---- Fukuoka's colours ------------------------------------------------------------
CH, CH_HI, CH_LO, CH_DK = rgb('5a5662'), rgb('7c7886'), rgb('423f4a'), rgb('2b2932')         # the station's charcoal tile
BRZ, BRZ_HI, BRZ_LO = rgb('b08a52'), rgb('dcb878'), rgb('7a5a32')                             # its bronze trim
WARM, LIT = rgb('f6dc8c'), rgb('f2c66a')
PAPER, PAPER_LO = rgb('f1e9d6'), rgb('cfc4aa')
SOOT, SOOT_LO = rgb('2b2a30'), rgb('1a191e')
FIR, FIR_HI, FIR_LO, FIR_DK = rgb('3f7350'), rgb('5f9a62'), rgb('2d5744'), rgb('1f3f38')     # fir garland, the tree
HONEY, HONEY_HI, HONEY_LO, HONEY_DK = rgb('c99560'), rgb('e6ba84'), rgb('9c6c42'), rgb('6c4830')   # the huts' timber
XRED, XRED_HI, XRED_LO = rgb('c2403a'), rgb('e46a58'), rgb('8c2a30')                          # Christmas red
VERM, VERM_HI, VERM_LO = rgb('d4503a'), rgb('ee7a5c'), rgb('9c3628')
ROE, ROE_HI, ROE_LO = rgb('ee7f76'), rgb('fbb3a6'), rgb('c4524e')                             # mentaiko pink
IBUSHI_P = (rgb('7d838c'), rgb('5c606b'), rgb('abb1ba'), rgb('41444f'))       # Hakata's silver-grey smoked tile
TOCHO_P = (rgb('756c6a'), rgb('554d4f'), rgb('a1968f'), rgb('3a3438'))        # the temple's older brown-grey tile
CEDAR, CEDAR_HI, CEDAR_LO, CEDAR_DK = rgb('c69a66'), rgb('e3bf8c'), rgb('9a7148'), rgb('6a4a32')   # unpainted cedar
DWOOD, DWOOD_HI, DWOOD_LO, DWOOD_DK = rgb('6f5144'), rgb('8f6c58'), rgb('4f3832'), rgb('342526')   # old dark timber
PLASTER, PLASTER_LO, PLASTER_SH = rgb('f4f1ea'), rgb('d3cdc2'), rgb('b4aea6')
CLAY, CLAY_HI, CLAY_LO, CLAY_DK = rgb('c8ab82'), rgb('dcc39c'), rgb('a98b64'), rgb('86694c')       # the wall's clay
INDIGO, INDIGO_HI, INDIGO_LO = rgb('2c3d6a'), rgb('4b6396'), rgb('1e2a4c')
NEON_PK, NEON_CY, NEON_YL, NEON_GR, NEON_VI = rgb('ff5fa8'), rgb('5fe6f0'), rgb('ffd84a'), rgb('7cf08a'), rgb('b98cff')
PLUM, PLUM_HI, PLUM_LO, PLUM_DK = rgb('3a2f44'), rgb('554866'), rgb('2a2233'), rgb('1c1724')       # the bar's dark tile
PUBG, PUBG_HI, PUBG_LO = rgb('2f5a48'), rgb('4a7c62'), rgb('1f3f36')                               # the pub's green
SAND, SAND_HI, SAND_LO, SAND_WET = rgb('ead7a8'), rgb('f6e8c2'), rgb('d6c08e'), rgb('c2a67a')
SEA, SEA_SH, SEA_HI = rgb('425faa'), rgb('5f97c8'), rgb('8ec2fa')             # pond-autotile's own blue, the shallows
TEAL, TEAL_HI, TEAL_LO = rgb('3f9fb0'), rgb('8fdbe0'), rgb('2f7f96')          # the canal's water, the cafe's trim
TERRA, TERRA_HI, TERRA_LO = rgb('c8674a'), rgb('e08a66'), rgb('9c4a3a')       # Canal City's red
GRAN, GRAN_HI, GRAN_LO, GRAN_DK = rgb('a9aeb2'), rgb('d2d7da'), rgb('7c8089'), rgb('545866')
SKIN = rgb('e8b99a')
HEDGE, HEDGE_HI, HEDGE_LO, HEDGE_DK = rgb('3f6f4c'), rgb('5f9458'), rgb('2f5644'), rgb('213f38')

FONT = dict(_FONT)
FONT.update({
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
})
KANA = dict(_KANA)
KANA.update({      # ナ ハ ツ セ ベ モ, for ナカス, ハカタオリ, トンコツ, センベイ, ウメモチ
    'na': ['...#...', '...#...', '#######', '...#...', '...#...', '..#....', '.#.....'],
    'ha': ['.......', '..#.#..', '..#.#..', '.#...#.', '.#...#.', '#.....#', '#.....#'],
    'tsu': ['.......', '#.#...#', '#.#...#', '.....#.', '....#..', '...#...', '.##....'],
    'se': ['..#....', '..#....', '#######', '..#...#', '..#..#.', '..#....', '...####'],
    'be': ['....#.#', '.....#.', '..#....', '.#.#...', '#...#..', '.....#.', '......#'],
    'mo': ['.#####.', '..#....', '..#....', '#######', '..#....', '..#....', '...####'],
})
DAI = ['...#...', '...#...', '#######', '...#...', '..#.#..', '.#...#.', '#.....#']       # 大, hand-set
BUTSU = ['..#..#.', '.#...#.', '##..#..', '.#..#..', '.#.#..#', '.#.####', '.#....#']     # 仏, hand-set


def text(d, s, x, y, fill, scale=1, vertical=False):
    glyphs(d, [FONT[c] for c in s], x, y, fill, scale, 1, vertical)


def kana(d, names, x, y, fill, scale=1, vertical=False):
    glyphs(d, [KANA['vbar' if (vertical and n == 'bar') else n] for n in names], x, y, fill, scale, 1, vertical)


def text_w(s, scale=1):
    return (len(s) * 6 - 1) * scale


def kana_w(n, scale=1):
    return (n * 8 - 1) * scale


def ctext(d, s, cx, y, fill, scale=1):
    text(d, s, cx - text_w(s, scale) // 2, y, fill, scale)


def ckana(d, names, cx, y, fill, scale=1):
    kana(d, names, cx - kana_w(len(names), scale) // 2, y, fill, scale)


# ---- helpers ----------------------------------------------------------------------
def px_rect(d, x0, y0, x1, y1, fn):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=fn(x, y))


def planks(d, x0, y0, x1, y1, pal, w=6, seed=0, horizontal=False):
    """Boards: a lit arris, a dark joint, the odd knot."""
    base, hi, lo, dk = pal
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = ((y - y0) if horizontal else (x - x0)) % w
            v = (x if horizontal else y)
            b = ((y - y0) if horizontal else (x - x0)) // w
            if u == w - 1:
                c = dk
            elif u == 0:
                c = hi
            elif h3(b, v // 3, 9 + seed) < 14:
                c = lo
            else:
                c = base if (b + seed) % 3 else (lo if u > w // 2 else base)
            d.point((x, y), fill=c)


def bulbs(d, pts, cols, step=1):
    """A string of fairy lights along a list of points."""
    for i, (x, y) in enumerate(pts):
        if i % step == 0:
            d.point((x, y), fill=cols[(i // step) % len(cols)])


XMAS_BULBS = (rgb('fff2b0'), rgb('ff6a5a'), rgb('fff2b0'), rgb('6fe08a'), rgb('fff2b0'), rgb('6fb4ff'))
GOLD_BULBS = (rgb('fff2b0'), rgb('ffd24a'))


def garland(d, x0, x1, y, depth=4, seed=0, lights=True):
    """A swag of fir along an eave, with lights in it."""
    for x in range(x0, x1 + 1):
        t = (x - x0) % 16
        sag = round(depth * math.sin(math.pi * t / 16))
        for k in range(3):
            c = FIR_HI if k == 0 and h3(x, k, seed) < 120 else (FIR_LO if k == 2 else FIR)
            d.point((x, y + sag + k), fill=c)
        if h3(x, 3, seed) < 40:
            d.point((x, y + sag + 3), fill=FIR_DK)
        if lights and (x - x0) % 4 == 1:
            d.point((x, y + sag + 1), fill=XMAS_BULBS[((x - x0) // 4) % 6])
        if t == 0:
            d.rectangle([x - 1, y, x + 1, y + 2], fill=XRED)      # a red bow where it is tied
            d.point((x, y), fill=XRED_HI)


def person(d, x, y, coat, hat=None, hat_trim=None):
    """A shopkeeper behind a counter: head and shoulders, 9px wide, at (x, y)."""
    d.rectangle([x + 1, y + 9, x + 9, y + 18], fill=coat)
    d.rectangle([x + 2, y + 2, x + 8, y + 9], fill=SKIN)
    d.rectangle([x + 2, y, x + 8, y + 2], fill=hat or rgb('3a2c2a'))
    if hat_trim:
        d.line([(x + 1, y + 3), (x + 9, y + 3)], fill=hat_trim)
    d.point((x + 4, y + 6), fill=INK); d.point((x + 7, y + 6), fill=INK)


def lit_window(d, x0, y0, x1, y1, frame, bars=(1, 1), glow=None):
    """A lamplit window: a frame, warm glass, glazing bars."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=glow or WARM)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=WHITE)
    nx, ny = bars
    for k in range(1, nx + 1):
        x = x0 + round((x1 - x0) * k / (nx + 1))
        d.line([(x, y0 + 1), (x, y1 - 1)], fill=frame)
    for k in range(1, ny + 1):
        y = y0 + round((y1 - y0) * k / (ny + 1))
        d.line([(x0 + 1, y), (x1 - 1, y)], fill=frame)


def noren(d, x0, y0, x1, y1, body, hi, lo, slits=3):
    """A shop curtain on its pole: panels, the hem lifting between them."""
    d.line([(x0 - 1, y0 - 1), (x1 + 1, y0 - 1)], fill=WOOD_DK)
    d.rectangle([x0, y0, x1, y1], fill=body)
    d.line([(x0, y0), (x1, y0)], fill=hi)
    w = (x1 - x0 + 1) / slits
    for k in range(slits):
        a = round(x0 + k * w)
        d.line([(a, y0 + 1), (a, y1)], fill=hi)
        if k:
            d.line([(a - 1, y0 + 3), (a - 1, y1)], fill=lo)
            d.point((a - 1, y1), fill=SOOT_LO); d.point((a, y1), fill=SOOT_LO)
    d.line([(x1, y0 + 1), (x1, y1)], fill=lo)


def footing(d, x0, x1, y, h=4, c=GRAN_LO, hi=GRAN_HI):
    d.rectangle([x0, y, x1, y + h - 1], fill=c)
    d.line([(x0, y), (x1, y)], fill=hi)


# ==============================================================================
# Hakata Station
# ==============================================================================
def tile_wall(d, x0, y0, x1, y1):
    """The station's skin: charcoal ceramic panels, 8 x 6, a lit upper arris."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u, v = (x - x0) % 8, (y - y0) % 6
            if v == 5 or u == 7:
                c = CH_LO
            elif v == 0:
                c = CH_HI if h3(x // 8, y // 6, 4) < 150 else CH
            else:
                c = CH if h3(x // 8, y // 6, 1) > 40 else rgb('64606e')
            d.point((x, y), fill=c)


def clock(d, cx, cy, r):
    d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=BRZ_LO)
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=BRZ)
    d.arc([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], 150, 280, fill=BRZ_HI)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb('fbf6e6'))
    d.chord([cx - r, cy - r, cx + r, cy + r], 10, 120, fill=rgb('e9dfc6'))
    for k in range(12):
        a = math.radians(k * 30)
        x, y = cx + (r - 3) * math.sin(a), cy - (r - 3) * math.cos(a)
        if k % 3 == 0:
            d.rectangle([round(x) - 1, round(y) - 1, round(x), round(y)], fill=CH_DK)
        else:
            d.point((round(x), round(y)), fill=CH)
    d.line([(cx, cy), (cx - round(r * 0.45), cy - round(r * 0.3))], fill=CH_DK, width=2)       # ten past ten
    d.line([(cx, cy), (cx + round(r * 0.55), cy - round(r * 0.55))], fill=CH_DK, width=1)
    d.line([(cx, cy), (cx + 1, cy + round(r * 0.6))], fill=XRED)
    d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=BRZ_LO)


def roof_garden(d, x0, x1, y, seed=0, torii=None):
    """A roof garden seen over a parapet: clipped trees, some turned for
    November, a rail; with `torii`, the little rooftop shrine's gate."""
    cols = ((rgb('4f8250'), rgb('6fa262'), rgb('35603f')), (rgb('5a8c58'), rgb('82b472'), rgb('3c6846')),
            (rgb('c98a3a'), rgb('eeb054'), rgb('9a5c2a')), (rgb('4f8250'), rgb('6fa262'), rgb('35603f')),
            (rgb('b8503c'), rgb('e07a54'), rgb('8a342e')))
    x = x0 + 5
    i = seed
    while x < x1 - 4:
        rx = 5 + (i * 3 + seed) % 3
        ry = 5 + (i * 5 + seed) % 3
        if torii and abs(x - torii) < 12:
            x += 9; i += 1
            continue
        base, hi, lo = cols[(i * 2 + seed) % 5]
        d.rectangle([x - 1, y - 3, x, y], fill=rgb('6a4a3a'))
        blob(d, x, y - 3 - ry, rx, ry, base, hi, lo, seed=i)
        x += rx * 2 + 1 + (i % 2) * 3
        i += 1
    if torii:
        tx = torii
        d.rectangle([tx - 6, y - 12, tx + 6, y - 11], fill=VERM); d.line([(tx - 7, y - 13), (tx + 7, y - 13)], fill=SOOT)
        d.line([(tx - 5, y - 8), (tx + 5, y - 8)], fill=VERM)
        d.rectangle([tx - 5, y - 11, tx - 4, y], fill=VERM); d.rectangle([tx + 4, y - 11, tx + 5, y], fill=VERM_LO)
        d.point((tx - 5, y - 12), fill=VERM_HI)
    for xx in range(x0, x1 + 1, 4):                               # the rail
        d.point((xx, y - 1), fill=STONE_LO); d.point((xx, y - 2), fill=STONE_LO)
    d.line([(x0, y - 3), (x1, y - 3)], fill=STONE)


def shop_goods(d, x0, y0, x1, y1, seed=0):
    """A lit show window: shelves of goods."""
    d.rectangle([x0, y0, x1, y1], fill=WARM)
    d.line([(x0, y0), (x1, y0)], fill=WHITE)
    cols = (rgb('e0503c'), rgb('3f8fd0'), rgb('5fb86a'), rgb('f08a3c'), rgb('c05a9a'), rgb('f9c22e'))
    for j, y in enumerate(range(y0 + 6, y1 - 2, 9)):
        d.line([(x0, y + 6), (x1, y + 6)], fill=LIT)
        for i, x in enumerate(range(x0 + 2, x1 - 3, 5)):
            hgt = 3 + h3(i, j, seed) % 3
            d.rectangle([x, y + 6 - hgt, x + 2, y + 5], fill=cols[(i * 3 + j * 2 + seed) % 6])


def louvre_skin(d, x0, y0, x1, y1):
    """Hakata Station's skin: a continuous screen of dark vertical fins over
    the glass, banded at each floor, lamplight showing between the fins in
    places. No windows as such."""
    for y in range(y0, y1 + 1):
        v = (y - y0) % 18
        for x in range(x0, x1 + 1):
            u = (x - x0) % 4
            bay, flo = (x - x0) // 24, (y - y0) // 18
            if v == 17:
                c = CH_DK                                         # the floor band's shadow
            elif v == 0:
                c = BRZ_LO if (x - x0) % 24 < 23 else CH_DK       # a bronze string at each floor
            elif u == 0:
                c = CH_HI if v < 9 else rgb('6c6876')             # a fin's lit arris
            elif u == 1:
                c = CH
            else:                                                 # the gap between two fins
                lit = h3(bay, flo, 21) < 50
                c = (rgb('a8843c') if u == 2 else rgb('5e4c34')) if lit and 2 < v < 16 else CH_DK
            d.point((x, y), fill=c)


def garden_tree(d, x, y, r, k, seed=0):
    cols = ((rgb('4f8250'), rgb('6fa262'), rgb('35603f')), (rgb('5a8c58'), rgb('82b472'), rgb('3c6846')),
            (rgb('c98a3a'), rgb('eeb054'), rgb('9a5c2a')), (rgb('456f4c'), rgb('629658'), rgb('2f5440')),
            (rgb('b8503c'), rgb('e07a54'), rgb('8a342e')))
    base, hi, lo = cols[k % 5]
    d.rectangle([x - 1, y - 4, x, y], fill=rgb('6a4a3a'))
    blob(d, x, y - 3 - r, r, r, base, hi, lo, seed=seed)


def hakata_station():
    """Hakata Station: ONE long flat front. A dark louvred skin with the big
    clock set straight on it, a plain attic band lettered on the tile, a deep
    glass canopy on columns with the illumination curtain hanging from its
    edge, and the roof garden with its shrine above."""
    im, d = canvas(9, 6)                 # 288 x 192
    # ---- the roof garden: big clipped trees, a pergola, the rooftop shrine and its torii ----
    for i, (x, r, k) in enumerate(((12, 6, 3), (40, 7, 0), (66, 6, 3), (90, 7, 1), (116, 6, 0), (168, 6, 3),
                                   (192, 7, 0), (262, 6, 1), (280, 5, 3))):
        garden_tree(d, x, 27, r, k, i + 20)                       # the back row
    for i, (x, r, k) in enumerate(((25, 9, 0), (54, 8, 2), (79, 9, 1), (104, 8, 4), (180, 9, 1), (204, 8, 2),
                                   (272, 8, 4))):
        garden_tree(d, x, 30, r, k, i)
    for x in (130, 143, 156):                                     # a pergola over the middle, wisteria gone gold
        bar(d, x, 14, x + 1, 30, rgb('f3ead2'), WHITE, STONE_LO)
    d.rectangle([126, 12, 161, 14], fill=rgb('f3ead2')); d.line([(126, 14), (161, 14)], fill=STONE_LO)
    for x in range(127, 161, 2):
        d.point((x, 15 + h3(x, 1, 5) % 3), fill=rgb('d9a83c') if x % 4 else rgb('8fae5a'))
        d.point((x, 11), fill=rgb('8fae5a') if x % 6 else rgb('d9a83c'))
    # the shrine: a small cypress hall with a copper roof, the vermilion torii before it
    d.rectangle([243, 16, 255, 30], fill=CEDAR); d.line([(243, 16), (243, 30)], fill=CEDAR_HI)
    d.rectangle([247, 21, 251, 30], fill=DWOOD_DK)
    d.polygon([(238, 17), (247, 8), (251, 8), (260, 17)], fill=rgb('5f9a8c'))
    d.line([(238, 17), (247, 8)], fill=rgb('9ad0bc')); d.line([(238, 17), (260, 17)], fill=rgb('3a6a62'))
    d.rectangle([246, 6, 252, 8], fill=rgb('3a6a62')); d.point((249, 5), fill=GOLD)
    tx = 226
    d.rectangle([tx - 12, 6, tx + 12, 8], fill=SOOT); d.line([(tx - 12, 6), (tx + 12, 6)], fill=rgb('5a5662'))
    d.rectangle([tx - 11, 9, tx + 11, 11], fill=VERM); d.line([(tx - 11, 9), (tx + 11, 9)], fill=VERM_HI)
    d.rectangle([tx - 9, 16, tx + 9, 17], fill=VERM); d.rectangle([tx - 1, 12, tx + 1, 15], fill=SOOT)
    bar(d, tx - 8, 12, tx - 6, 30, VERM, VERM_HI, VERM_LO); bar(d, tx + 6, 12, tx + 8, 30, VERM, VERM_HI, VERM_LO)
    # the parapet, a low hedge behind its rail
    d.rectangle([4, 26, 283, 28], fill=rgb('456f4c'))
    for x in range(4, 284):
        if h3(x, 2, 7) < 90:
            d.point((x, 26), fill=rgb('6fa262'))
    d.rectangle([2, 29, 285, 35], fill=STONE); d.line([(2, 29), (285, 29)], fill=WHITE)
    d.line([(2, 35), (285, 35)], fill=STONE_LO)
    for x in range(4, 285, 6):
        d.line([(x, 24), (x, 28)], fill=STONE_LO)
    d.line([(4, 24), (283, 24)], fill=STONE)
    # ---- the front: a plain attic band of charcoal tile, the louvred skin under it -------------
    tile_wall(d, 4, 36, 283, 57)
    louvre_skin(d, 4, 58, 283, 113)
    d.line([(4, 36), (4, 113)], fill=CH_HI); d.rectangle([281, 36, 283, 113], fill=CH_LO)
    d.line([(4, 57), (283, 57)], fill=CH_DK)
    # the name, set on the tile itself in bronze letters: roman to the west, kana to the east
    text(d, 'HAKATA', 23, 41, BRZ_LO, 2); text(d, 'HAKATA', 22, 40, rgb('f3e2b4'), 2)
    kana(d, ['ha', 'ka', 'ta'], 207, 41, BRZ_LO, 2); kana(d, ['ha', 'ka', 'ta'], 206, 40, rgb('f3e2b4'), 2)
    # the big clock, straight on the skin
    d.ellipse([118, 43, 172, 97], fill=CH_DK)
    clock(d, 144, 69, 21)
    # ---- the glass canopy: a real roof, a cell deep, seen from above and in front ----------------
    for y in range(114, 141):
        t = (y - 114) / 26
        xa, xb = round(8 - 7 * t), round(279 + 7 * t)
        for x in range(xa, xb + 1):
            if x in (xa, xb):
                c = WHITE
            elif y in (114, 123, 132):
                c = rgb('eef6fb')
            else:
                sheen = (x * 2 + y * 3) % 46 < 9
                c = rgb('cfe8f8') if sheen else (rgb('9cc4e4') if t > 0.55 else rgb('86b0d6'))
                if (x + y) % 2 == 0 and t < 0.3:
                    c = rgb('6f8eb4')                             # the skin's dark showing through at the top
            d.point((x, y), fill=c)
    for i in range(-11, 12):                                      # the glazing bars fan out toward the eave
        d.line([(144 + round(i * 135 / 12), 114), (144 + round(i * 142 / 12), 140)], fill=WHITE)
    d.rectangle([0, 141, 287, 144], fill=WHITE); d.line([(0, 144), (287, 144)], fill=STONE)
    d.line([(0, 145), (287, 145)], fill=STONE_DK)
    # ---- under the canopy, in its shade: shops, three pairs of doors ---------------------------
    d.rectangle([4, 146, 283, 185], fill=CH_DK)
    d.rectangle([4, 146, 283, 149], fill=rgb('1f1d26'))
    for k, (x0, x1) in enumerate(((10, 44), (56, 90), (198, 232), (244, 278))):
        shop_goods(d, x0, 154, x1, 179, seed=k)
        d.rectangle([x0 - 1, 153, x1 + 1, 180], outline=STONE_DK)
        d.rectangle([x0, 180, x1, 185], fill=CH); d.line([(x0, 180), (x1, 180)], fill=CH_HI)
    d.rectangle([100, 150, 187, 156], fill=AMBER); d.line([(100, 150), (187, 150)], fill=WARM)   # the lit door header
    d.line([(100, 156), (187, 156)], fill=BRZ_LO)
    for k in range(7):                                            # a departures strip
        d.rectangle([108 + k * 11, 152, 113 + k * 11, 153], fill=NAVY)
    for x0 in (101, 130, 159):
        glass_door(d, x0, 158, x0 + 27, 185, frame=STONE_DK)
        d.rectangle([x0 + 1, 159, x0 + 26, 161], fill=rgb('6583bd'))
    # the columns at the canopy's edge, each with a little splayed head
    for x in (2, 48, 94, 190, 236, 282):
        bar(d, x, 146, x + 3, 185, WHITE, None, STONE)
        d.line([(x - 2, 146), (x + 5, 146)], fill=WHITE); d.line([(x - 1, 147), (x + 4, 147)], fill=STONE)
    # the illumination curtain: strings of lights hanging from the canopy's edge, in swags
    for x in range(8, 282, 2):
        if any(abs(x - c - 1) < 4 for c in (2, 48, 94, 190, 236, 282)):
            continue
        ln = 5 + round(4 * (1 + math.cos((x - 25) * math.pi / 23)))
        if 98 < x < 190:
            ln = 4 + (x // 2) % 2                                 # kept short over the doors
        for k in range(ln):
            c = (rgb('fffbe6'), rgb('ffd24a'), rgb('fff2b0'))[(x // 2 + k) % 3]
            if (k + x // 2) % 2 == 0 or k == ln - 1:
                d.point((x, 146 + k), fill=c)
    footing(d, 0, 287, 186, 4, STONE_LO, WHITE)
    for x in range(98, 190, 4):                                   # a tactile strip to the doors
        d.point((x, 188), fill=AMBER)
    outline(im)
    return im


def hut(kind):
    """A Christmas-market hut: a timber cabin, its gable to the street, a fir
    garland with lights under the eaves, a star, a lit counter."""
    im, d = canvas(3, 3)                 # 96 x 96
    roofc, roof_hi, roof_lo = {'wine': (XRED, XRED_HI, XRED_LO), 'wurst': (FIR, FIR_HI, FIR_DK),
                               'gifts': (rgb('3d5a8c'), rgb('5f82b8'), rgb('2a3f66'))}[kind]
    pal = (HONEY, HONEY_HI, HONEY_LO, HONEY_DK)
    # the gable wall and the body
    for y in range(14, 44):
        half = round((y - 10) * 46 / 34)
        for x in range(48 - half, 48 + half + 1):
            u = (x - 2) % 6
            d.point((x, y), fill=HONEY_DK if u == 5 else (HONEY_HI if u == 0 else (HONEY if x < 64 else HONEY_LO)))
    planks(d, 8, 44, 87, 90, pal, 6, seed=1)
    d.rectangle([82, 44, 87, 90], fill=HONEY_LO)
    for x in (8, 84):
        bar(d, x, 44, x + 3, 90, HONEY_LO, HONEY, HONEY_DK)
    # the roof: two thick slopes meeting at the peak, lit on the west one
    for k in range(9):
        d.line([(48, 6 + k), (0, 38 + k)], fill=roof_hi if k < 2 else (roofc if k < 7 else roof_lo))
        d.line([(48, 6 + k), (95, 38 + k)], fill=roofc if k < 2 else roof_lo)
    for t in range(4, 44, 6):                                     # shingle laps
        x = 48 - round(t * 48 / 34)
        d.line([(x, 8 + t), (x - 2, 15 + t)], fill=roof_lo)
        x = 48 + round(t * 47 / 34)
        d.line([(x, 8 + t), (x + 2, 15 + t)], fill=SOOT)
    # fairy lights under both slopes
    pts = [(48 - round(t * 46 / 34), 17 + t) for t in range(2, 32, 3)] + [(48 + round(t * 46 / 34), 17 + t) for t in range(2, 32, 3)]
    bulbs(d, pts, XMAS_BULBS)
    # the gable's board
    label = {'wine': 'WINE', 'wurst': 'WURST', 'gifts': 'XMAS'}[kind]
    w = text_w(label) + 8
    bar(d, 48 - w // 2, 27, 48 + w // 2, 39, rgb('f3ead2'), WHITE, PAPER_LO)
    d.rectangle([48 - w // 2, 27, 48 + w // 2, 39], outline=roof_lo)
    ctext(d, label, 48, 30, roof_lo)
    star(d, 48, 5, 5, rgb('ffd84a'), rgb('c8982c'))
    d.point((48, 5), fill=WHITE)
    # the counter: a lit opening, the keeper, the goods
    d.rectangle([13, 49, 82, 73], fill=rgb('4a2f2a'))
    d.rectangle([14, 50, 81, 72], fill=rgb('5c3a30'))
    d.rectangle([14, 50, 81, 52], fill=WARM)
    if kind == 'wine':
        person(d, 54, 54, XRED, XRED, WHITE)
        d.rectangle([20, 58, 34, 72], fill=rgb('c9793f')); d.rectangle([22, 55, 32, 58], fill=rgb('96502e'))    # the copper urn
        d.line([(20, 58), (20, 72)], fill=rgb('f4bd7c')); d.rectangle([33, 64, 37, 65], fill=rgb('96502e'))
        d.ellipse([24, 61, 30, 67], fill=rgb('f4bd7c'))
        for k, x in enumerate((40, 46, 68, 74)):                  # mugs
            d.rectangle([x, 66, x + 3, 71], fill=XRED if k % 2 == 0 else WHITE)
            d.point((x + 4, 68), fill=XRED if k % 2 == 0 else WHITE)
            d.line([(x, 66), (x + 3, 66)], fill=rgb('6a2030'))
        for x in (16, 78):                                        # bottles on the back shelf
            d.rectangle([x, 56, x + 2, 64], fill=FIR_DK); d.point((x + 1, 55), fill=FIR_DK)
    elif kind == 'wurst':
        person(d, 22, 54, WHITE, WHITE, None)
        d.rectangle([38, 66, 78, 72], fill=SOOT)                  # the grill
        for x in range(39, 78, 2):
            d.point((x, 71), fill=rgb('f0903a') if (x // 2) % 3 else rgb('d9482e'))
        d.line([(38, 66), (78, 66)], fill=STONE_DK)
        for x in (41, 49, 57, 65, 72):                            # sausages on it
            d.rectangle([x, 64, x + 5, 65], fill=rgb('b5583a')); d.point((x + 1, 64), fill=rgb('e08a5a'))
        for x in range(40, 80, 7):                                # strings of them hung above
            d.line([(x, 53), (x, 59)], fill=rgb('a04a34')); d.line([(x + 1, 53), (x + 1, 59)], fill=rgb('c8684a'))
            d.point((x, 60), fill=rgb('8a3a2c'))
    else:
        person(d, 62, 54, FIR, rgb('3d5a8c'), WHITE)
        cols = (XRED, rgb('ffd84a'), rgb('5f9ae0'), WHITE, rgb('6fc07a'), rgb('e07ab0'))
        for i, x in enumerate(range(17, 58, 6)):                  # baubles on strings
            ln = 4 + (i * 3) % 6
            d.line([(x + 1, 53), (x + 1, 53 + ln)], fill=rgb('c9b48a'))
            d.ellipse([x - 1, 53 + ln, x + 3, 57 + ln], fill=cols[i % 6])
            d.point((x, 54 + ln), fill=WHITE)
        for i, x in enumerate((18, 28, 38, 48)):                  # nutcrackers and stars on the counter
            d.rectangle([x, 66, x + 3, 71], fill=cols[(i * 2) % 6]); d.rectangle([x + 1, 63, x + 2, 65], fill=SKIN)
            d.rectangle([x, 62, x + 3, 62], fill=SOOT)
        star(d, 76, 60, 4, rgb('ffd84a')); star(d, 76, 69, 3, WHITE)
    bar(d, 10, 73, 85, 77, HONEY_HI, WHITE, HONEY_LO)              # the counter shelf
    d.line([(10, 78), (85, 78)], fill=HONEY_DK)
    garland(d, 13, 82, 45, 3, seed={'wine': 1, 'wurst': 2, 'gifts': 3}[kind])
    # the apron: a wreath, a price card
    d.ellipse([40, 80, 55, 89], fill=FIR); d.ellipse([44, 83, 51, 86], fill=HONEY)
    d.arc([40, 80, 55, 89], 180, 300, fill=FIR_HI)
    for x, y in ((42, 82), (53, 84), (47, 88)):
        d.point((x, y), fill=XRED_HI)
    d.rectangle([46, 79, 49, 80], fill=XRED)
    bar(d, 16, 81, 30, 88, PAPER, WHITE, PAPER_LO)
    d.line([(18, 83), (27, 83)], fill=CREAM_DK); d.line([(18, 86), (24, 86)], fill=XRED)
    bar(d, 64, 81, 78, 88, PAPER, WHITE, PAPER_LO)
    d.line([(66, 83), (75, 83)], fill=CREAM_DK); d.line([(66, 86), (72, 86)], fill=XRED)
    footing(d, 6, 89, 90, 4, HONEY_DK, HONEY_LO)
    outline(im)
    return im


def xmas_tree():
    im, d = canvas(3, 5)                 # 96 x 160
    # the planter and trunk
    bar(d, 44, 132, 51, 142, rgb('6a4a3a'), rgb('8a6650'), rgb('4a3228'))
    bar(d, 30, 140, 65, 154, XRED, XRED_HI, XRED_LO)
    d.rectangle([30, 140, 65, 142], fill=XRED_HI); d.line([(30, 154), (65, 154)], fill=rgb('6a2030'))
    d.rectangle([46, 140, 49, 154], fill=rgb('ffd84a')); d.line([(30, 147), (65, 147)], fill=rgb('ffd84a'))
    # five tiers of boughs, each a fringed skirt
    tiers = ((14, 44, 6, 20), (34, 68, 10, 28), (56, 92, 14, 35), (78, 116, 18, 41), (100, 138, 22, 46))
    for ti, (y0, y1, w0, w1) in enumerate(tiers):
        for y in range(y0, y1 + 1):
            t = (y - y0) / (y1 - y0)
            half = w0 + (w1 - w0) * t
            for x in range(48 - round(half), 48 + round(half) + 1):
                u = (x - 48) / max(1.0, half)
                fringe = y1 - y < 4 and (x + ti * 3) % 5 in (0, 1) and y1 - y < 2 + (x % 3)
                if fringe:
                    continue
                k = h3(x, y, 5 + ti)
                if u < -0.35:
                    c = FIR_HI if k < 150 else FIR
                elif u > 0.45:
                    c = FIR_DK if k < 110 else FIR_LO
                else:
                    c = FIR if k > 60 else (FIR_HI if u < 0 else FIR_LO)
                if y - y0 < 3 and ti:
                    c = FIR_DK                                    # the shadow under the tier above
                d.point((x, y), fill=c)
    # garlands of gold beads, baubles, lights
    for gi, (ya, yb, half) in enumerate(((36, 42, 16), (60, 68, 26), (84, 92, 33), (108, 116, 40), (126, 134, 44))):
        for x in range(48 - half, 48 + half + 1, 2):
            t = (x - (48 - half)) / (2 * half)
            y = round(ya + (yb - ya) * t + 3 * math.sin(math.pi * t))
            d.point((x, y), fill=rgb('ffe27a') if (x // 2) % 2 else rgb('fff6c8'))
    cols = (XRED_HI, rgb('5f9ae0'), rgb('ffd84a'), WHITE, rgb('e07ab0'))
    for i, (x, y) in enumerate(((44, 28), (55, 40), (38, 52), (60, 58), (48, 72), (30, 80), (66, 82), (40, 98),
                                (58, 102), (24, 106), (74, 110), (34, 122), (52, 126), (68, 128), (16, 130), (80, 132))):
        c = cols[i % 5]
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
        d.point((x - 1, y - 1), fill=WHITE)
        d.point((x + 1, y + 2), fill=rgb('5a3a4a'))
    for i in range(46):                                           # white fairy lights all through
        x = 14 + h3(i, 3, 21) % 68
        y = 22 + h3(i, 9, 22) % 112
        half = 6 + (y - 14) * 40 / 124
        if abs(x - 48) < half - 2:
            d.point((x, y), fill=rgb('fffbe0'))
    # gifts round the planter
    for x, y, w, h, c, rib in ((16, 146, 12, 9, rgb('5f9ae0'), WHITE), (68, 144, 13, 11, rgb('6fc07a'), XRED),
                               (8, 150, 8, 5, rgb('ffd84a'), XRED), (80, 150, 9, 5, rgb('e07ab0'), WHITE)):
        d.rectangle([x, y, x + w, y + h], fill=c)
        d.line([(x + w // 2, y), (x + w // 2, y + h)], fill=rib); d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=rib)
        d.line([(x + w, y), (x + w, y + h)], fill=rgb('4a4a6a'))
    outline(im)
    # the star, after the outline so its rays stay fine
    d = ImageDraw.Draw(im)
    star(d, 48, 9, 8, rgb('ffd84a'), rgb('c8982c'))
    star(d, 48, 9, 4, rgb('fff6c8'))
    for dx, dy in ((0, -9), (-10, 0), (10, 0)):
        d.point((48 + dx, 9 + dy), fill=rgb('fff6c8'))
    return grounded(im, ellipses=[(6, 148, 90, 159)], a=70)


def illumination_arch():
    im, d = canvas(3, 3)                 # 96 x 96
    cx, cy, ro, ri = 48, 50, 43, 34
    for y in range(4, 92):
        for x in range(2, 94):
            if y <= cy:
                q = math.hypot(x - cx, y - cy)
                inside = ri <= q <= ro
                u = (q - ri) / (ro - ri)
            else:
                inside = (cx - ro <= x <= cx - ri) or (cx + ri <= x <= cx + ro)
                u = (abs(x - cx) - ri) / (ro - ri)
            if not inside:
                continue
            k = h3(x, y, 13)
            west = x < cx
            if u > 0.75:
                c = FIR_HI if (west or y < 20) and k < 170 else FIR
            elif u < 0.2:
                c = FIR_DK
            else:
                c = FIR if k > 70 else (FIR_HI if west else FIR_LO)
            if not west and u > 0.5 and y > 30:
                c = FIR_LO if k > 60 else FIR_DK
            d.point((x, y), fill=c)
    # a gold ribbon wound round it, lights, red bows
    for i in range(0, 200):
        a = math.pi * i / 199
        for rr, c in ((ri + 2 + (i % 12) * 0.6, rgb('ffe27a')),):
            x, y = cx - rr * math.cos(a), cy - rr * math.sin(a)
            if i % 12 < 11:
                d.point((round(x), round(y)), fill=c)
    for y in range(52, 90):
        k = (y - 52) % 10
        for x0 in (cx - ro, cx + ri):
            d.point((x0 + 1 + round(k * 0.7), y), fill=rgb('ffe27a'))
    for i in range(70):
        a = math.pi * (i + 0.5) / 70
        rr = ri + 1 + h3(i, 1, 4) % (ro - ri - 1)
        x, y = round(cx - rr * math.cos(a)), round(cy - rr * math.sin(a))
        d.point((x, y), fill=XMAS_BULBS[i % 6])
    for i in range(24):
        y = 54 + (i // 2) * 3
        x = (cx - ro if i % 2 == 0 else cx + ri) + 1 + h3(i, 5, 6) % 7
        d.point((x, y), fill=XMAS_BULBS[(i * 5) % 6])
    for a_deg in (38, 90, 142):                                   # bows
        a = math.radians(a_deg)
        x, y = round(cx - (ri + 4) * math.cos(a)), round(cy - (ri + 4) * math.sin(a))
        d.polygon([(x - 5, y - 3), (x, y), (x - 5, y + 3)], fill=XRED)
        d.polygon([(x + 5, y - 3), (x, y), (x + 5, y + 3)], fill=XRED_LO)
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=XRED_HI)
    # hanging stars inside the arch
    for x, ln, r in ((30, 10, 3), (48, 16, 5), (66, 10, 3)):
        top = cy - round(math.sqrt(max(0, ri * ri - (x - cx) ** 2)))
        d.line([(x, top), (x, top + ln)], fill=rgb('e6d6a2'))
        star(d, x, top + ln + r, r, rgb('ffd84a'), rgb('c8982c'))
        d.point((x, top + ln + r), fill=WHITE)
    # tubs at the feet
    for x0 in (3, 80):
        bar(d, x0, 86, x0 + 12, 93, XRED, XRED_HI, XRED_LO)
        d.line([(x0, 89), (x0 + 12, 89)], fill=rgb('ffd84a'))
    outline(im)
    d = ImageDraw.Draw(im)
    star(d, 48, 7, 7, rgb('ffd84a'), rgb('c8982c')); star(d, 48, 7, 3, rgb('fff6c8'))
    return im


def bowl(d, x, y, c=WHITE, soup=rgb('f3e3c0')):
    d.rectangle([x, y, x + 8, y + 1], fill=soup)
    d.rectangle([x, y + 2, x + 8, y + 3], fill=c); d.rectangle([x + 1, y + 4, x + 7, y + 4], fill=c)
    d.rectangle([x + 3, y + 5, x + 5, y + 5], fill=rgb('c9c2b4'))
    d.point((x + 2, y), fill=rgb('7fc06a')); d.point((x + 5, y), fill=rgb('d98a7a')); d.point((x + 6, y), fill=rgb('d98a7a'))
    d.line([(x, y + 2), (x + 8, y + 2)], fill=XRED)


def ramen_shop():
    im, d = canvas(3, 4)                 # 96 x 128
    # ---- upstairs: cream tile, the red board ------------------------------------------
    for y in range(40, 78):
        for x in range(5, 91):
            v, u = (y - 40) % 5, (x + ((y - 40) // 5) * 4) % 8
            d.point((x, y), fill=rgb('cdbfa6') if v == 4 or u == 7 else (rgb('f6efdc') if x < 60 else rgb('eadfc6')))
    d.rectangle([85, 40, 90, 78], fill=rgb('cdbfa6'))
    d.rectangle([3, 34, 92, 40], fill=SOOT); d.line([(3, 34), (92, 34)], fill=rgb('5a5662'))
    d.line([(3, 40), (92, 40)], fill=INK)
    bar(d, 9, 44, 80, 66, XRED, XRED_HI, XRED_LO)
    d.rectangle([9, 44, 80, 66], outline=rgb('6a2030'))
    d.rectangle([11, 46, 78, 64], outline=rgb('ffd84a'))
    ckana(d, ['ra', 'bar', 'me', 'n'], 45, 49, WHITE, 2)
    d.rectangle([9, 68, 80, 76], fill=SOOT)
    kana(d, ['to', 'n', 'ko', 'tsu'], 12, 69, rgb('ffd84a'))
    for k in range(3):                                            # three bowls: the grades of richness
        d.ellipse([52 + k * 9, 70, 58 + k * 9, 75], fill=(rgb('f3e3c0'), rgb('e6cf9c'), rgb('d6b87c'))[k])
        d.arc([52 + k * 9, 70, 58 + k * 9, 75], 0, 360, fill=XRED)
    # ---- the stock pot's flue, up the east side ------------------------------------------
    bar(d, 82, 18, 89, 78, STONE, WHITE, STONE_DK)
    d.rectangle([87, 18, 89, 78], fill=STONE_LO)
    for y in (30, 48, 66):
        d.line([(82, y), (89, y)], fill=STONE_DK)
    d.rectangle([80, 15, 91, 19], fill=STONE_LO); d.line([(80, 15), (91, 15)], fill=STONE)
    # ---- the pent roof ----------------------------------------------------------------------
    for y in range(78, 87):
        e = y - 78
        for x in range(3 - e // 3, 93 + e // 3):
            c = rgb('2a2b36') if e % 4 == 3 or (x + (e // 4) * 3) % 6 == 0 else rgb('454759')
            d.point((x, y), fill=c)
    d.rectangle([0, 87, 95, 88], fill=rgb('2a2b36'))
    for x in range(2, 95, 5):
        d.point((x, 88), fill=rgb('8a8ea0'))
    # ---- downstairs: the counter window, the door under its red noren -------------------------
    d.rectangle([5, 89, 90, 122], fill=DWOOD_LO)
    for x in (5, 47, 87):
        bar(d, x, 89, x + 3, 122, DWOOD, DWOOD_HI, DWOOD_DK)
    d.rectangle([9, 92, 46, 114], fill=rgb('40282a'))
    d.rectangle([9, 92, 46, 94], fill=WARM)
    person(d, 12, 94, WHITE, WHITE, None)
    d.rectangle([27, 97, 41, 108], fill=STONE_LO)                 # the stock pot, boiling
    d.line([(27, 97), (27, 108)], fill=WHITE); d.rectangle([26, 96, 42, 97], fill=STONE)
    d.rectangle([28, 95, 40, 95], fill=rgb('f3e3c0'))
    d.rectangle([9, 109, 46, 114], fill=CEDAR); d.line([(9, 109), (46, 109)], fill=CEDAR_HI)
    bowl(d, 12, 104); bowl(d, 30, 110, WHITE)
    d.rectangle([9, 115, 46, 122], fill=DWOOD); d.line([(9, 115), (46, 115)], fill=DWOOD_HI)
    for x in range(11, 46, 4):
        d.line([(x, 117), (x, 121)], fill=DWOOD_LO)
    # the door: lamplit lattice, the long red noren
    d.rectangle([51, 91, 86, 122], fill=DWOOD_DK)
    # the west leaf, slid shut: cedar boards, a paper pane, a pull
    planks(d, 52, 100, 67, 121, (CEDAR, CEDAR_HI, CEDAR_LO, CEDAR_DK), w=4, seed=2)
    d.rectangle([54, 103, 65, 112], fill=CEDAR_DK); d.rectangle([55, 104, 64, 111], fill=LIT)
    d.line([(60, 104), (60, 111)], fill=CEDAR_LO); d.rectangle([65, 113, 66, 117], fill=SOOT)
    # the east leaf stands open: the way in, the lit shop beyond, a stool at the counter
    d.rectangle([69, 100, 85, 121], fill=rgb('3a2224'))
    for y in range(100, 122):
        for x in range(70, 85):
            q = math.hypot((x - 77) / 9, (y - 104) / 16)
            if q < 1:
                d.point((x, y), fill=(WARM, LIT, rgb('c98a4c'), rgb('7a4a34'))[min(3, int(q * 4))])
    d.rectangle([73, 113, 78, 114], fill=XRED); d.line([(75, 115), (75, 120)], fill=SOOT); d.line([(76, 115), (76, 120)], fill=SOOT)
    d.line([(69, 121), (85, 121)], fill=STONE_LO)
    noren(d, 51, 91, 86, 105, XRED, XRED_HI, XRED_LO, 4)
    kana(d, ['ra', 'bar', 'me', 'n'], 53, 95, WHITE)
    lantern(d, 39, 90, 8, 13, rgb('ffd84a'), rgb('fff2b0'), rgb('c8982c'))
    d.rectangle([41, 94, 44, 99], fill=XRED)
    footing(d, 3, 92, 122, 4)
    outline(im)
    puff(im, 86, 10, 5, col=(246, 240, 228), a=200); puff(im, 80, 4, 5, col=(246, 240, 228), a=160)
    puff(im, 90, 3, 4, col=(246, 240, 228), a=120); puff(im, 73, 9, 3, col=(246, 240, 228), a=110)
    puff(im, 70, 2, 4, col=(246, 240, 228), a=80); puff(im, 62, 5, 3, col=(246, 240, 228), a=50)
    puff(im, 34, 91, 3, col=(246, 240, 228), a=90)
    return im


def roe(d, x, y, flip=False):
    """A sac of mentaiko: a plump pink tongue."""
    pts = [(x, y + 1), (x + 3, y), (x + 9, y), (x + 11, y + 1), (x + 9, y + 3), (x + 3, y + 3)]
    if flip:
        pts = [(2 * x + 11 - px, py) for px, py in pts]
    d.polygon(pts, fill=ROE, outline=ROE_LO)
    d.line([(x + 3, y + 1), (x + 8, y + 1)], fill=ROE_HI)


def mentaiko_shop():
    im, d = canvas(3, 3)                 # 96 x 96
    bar(d, 5, 12, 90, 90, PLASTER, WHITE, PLASTER_LO)
    d.rectangle([85, 12, 90, 90], fill=PLASTER_LO)
    for y in range(2, 12):                                        # a low roof of dark red tile
        e = y - 2
        for x in range(8 - e // 2, 88 + e // 2):
            c = rgb('5a2a30') if (e % 4 == 3 or (x + (e // 4) * 3) % 6 == 0) else (rgb('8c4648') if x < 56 else rgb('7a3a3c'))
            d.point((x, y), fill=rgb('b06a66') if e == 0 else c)
    d.rectangle([2, 12, 93, 13], fill=rgb('5a2a30'))
    for x in range(4, 93, 5):
        d.point((x, 13), fill=rgb('b06a66'))
    # the board: white, red kana, a pair of sacs
    bar(d, 8, 15, 87, 34, rgb('fff8ee'), WHITE, PAPER_LO)
    d.rectangle([8, 15, 87, 34], outline=ROE_LO)
    kana(d, ['me', 'n', 'ta', 'i', 'ko'], 11, 18, XRED, 2)
    d.line([(11, 33), (84, 33)], fill=ROE)
    # the awning: coral and white
    for x in range(3, 93):
        s = ((x - 3) // 7) % 2
        for y in range(37, 46):
            d.point((x, y), fill=(ROE_LO if y > 43 else ROE) if s else (PAPER_LO if y > 43 else WHITE))
        if (x - 3) % 7 in (1, 2, 3, 4, 5):
            d.point((x, 46), fill=ROE if s else WHITE)
    d.line([(3, 37), (92, 37)], fill=ROE_HI)
    # the window: boxes of roe on a cedar counter, a clerk
    d.rectangle([8, 50, 57, 84], fill=rgb('7a3a3c'))
    d.rectangle([9, 51, 56, 83], fill=WARM); d.line([(9, 51), (56, 51)], fill=WHITE)
    person(d, 40, 53, rgb('fff8ee'), ROE_LO, WHITE)
    for j, y in enumerate((57, 65)):
        for i, x in enumerate((11, 25)):
            d.rectangle([x, y, x + 12, y + 6], fill=CEDAR_HI); d.rectangle([x, y, x + 12, y + 6], outline=CEDAR_LO)
            roe(d, x + 1, y + 1, flip=(i + j) % 2 == 1)
    d.rectangle([9, 73, 56, 83], fill=CEDAR); d.line([(9, 73), (56, 73)], fill=CEDAR_HI)
    for x in (12, 27, 42):
        d.rectangle([x, 76, x + 11, 81], fill=XRED); d.rectangle([x + 4, 76, x + 6, 81], fill=rgb('ffd84a'))
        d.line([(x, 76), (x + 11, 76)], fill=XRED_HI)
    # the door: glass under a short coral noren with a sac on it
    d.rectangle([62, 50, 85, 90], fill=rgb('7a3a3c'))
    d.rectangle([63, 51, 84, 90], fill=GLASS)
    d.line([(73, 62), (73, 90)], fill=rgb('7a3a3c')); d.line([(64, 63), (72, 63)], fill=GLASS_HI)
    d.line([(74, 63), (83, 63)], fill=GLASS_HI); d.point((71, 77), fill=WHITE); d.point((75, 77), fill=WHITE)
    noren(d, 63, 51, 84, 61, ROE, ROE_HI, ROE_LO, 3)
    roe(d, 68, 54)
    d.rectangle([5, 84, 61, 90], fill=PLASTER_LO); d.line([(5, 84), (61, 84)], fill=WHITE)
    footing(d, 3, 92, 90, 4)
    outline(im)
    return im


# ==============================================================================
# Nakasu
# ==============================================================================
def neon(d, fn, col, dark):
    """Draw a neon tube twice: its dim halo a pixel out, then the lit tube."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        fn(dx, dy, dark)
    fn(0, 0, col)


def dim(c, f=0.45):
    return (round(c[0] * f), round(c[1] * f), round(c[2] * f), 255)


def cocktail(d, x, y, col, dark):
    """A neon cocktail glass, 13 x 16."""
    def draw(dx, dy, c):
        d.line([(x + dx, y + dy), (x + 12 + dx, y + dy)], fill=c)
        d.line([(x + dx, y + dy), (x + 6 + dx, y + 7 + dy)], fill=c)
        d.line([(x + 12 + dx, y + dy), (x + 6 + dx, y + 7 + dy)], fill=c)
        d.line([(x + 6 + dx, y + 7 + dy), (x + 6 + dx, y + 14 + dy)], fill=c)
        d.line([(x + 2 + dx, y + 15 + dy), (x + 10 + dx, y + 15 + dy)], fill=c)
    neon(d, draw, col, dark)
    d.ellipse([x + 8, y - 4, x + 12, y], outline=NEON_GR)        # the olive
    d.line([(x + 4, y + 3), (x + 8, y + 3)], fill=NEON_YL)


def sign_box(d, x0, y0, x1, y1, body, label, fg=WHITE, vertical=True):
    """A lit sign box on a bracket."""
    d.rectangle([x0, y0, x1, y1], fill=body)
    d.line([(x0, y0), (x0, y1)], fill=tuple(min(255, v + 50) for v in body[:3]) + (255,))
    d.line([(x1, y0), (x1, y1)], fill=dim(body, 0.65))
    d.line([(x0, y0), (x1, y0)], fill=tuple(min(255, v + 50) for v in body[:3]) + (255,))
    if vertical:
        text(d, label, (x0 + x1) // 2 - 2, y0 + 3, fg, 1, True)
    else:
        ctext(d, label, (x0 + x1 + 1) // 2, y0 + 2, fg)


def billboard(d, x0, y0, x1, y1, rim, legs=True):
    """A rooftop billboard on its steel frame: a dark face in a lit rim, a
    floodlight arm over it, legs down to the roof."""
    if legs:
        for x in (x0 + 3, x1 - 4):
            d.rectangle([x, y1, x + 1, 69], fill=STONE_DK)
        d.line([(x0 + 4, 69), (x1 - 4, y1 + 1)], fill=rgb('3a3848'))      # a brace
    d.rectangle([x0, y0, x1, y1], fill=rgb('15122a'))
    d.rectangle([x0, y0, x1, y1], outline=rim)
    d.line([(x0, y0), (x1, y0)], fill=tuple(min(255, v + 60) for v in rim[:3]) + (255,))
    for x in range(x0 + 6, x1 - 3, 12):                           # floodlights on arms
        d.line([(x, y0 - 3), (x, y0 - 1)], fill=STONE_DK); d.rectangle([x - 1, y0 - 4, x + 1, y0 - 3], fill=rgb('fff2b0'))


def neon_bar():
    """Nakasu's riverside block: wider than tall, a low dark row of bars
    under a wall of rooftop billboards that faces the water."""
    im, d = canvas(6, 4)                 # 192 x 128
    # ---- the billboards, each its own size and colour -----------------------------------
    # BAR: a big cocktail glass in pink tube
    billboard(d, 5, 18, 38, 63, NEON_PK)
    def glass(dx, dy, c):
        d.line([(11 + dx, 23 + dy), (32 + dx, 23 + dy)], fill=c)
        d.line([(11 + dx, 23 + dy), (21 + dx, 35 + dy)], fill=c); d.line([(32 + dx, 23 + dy), (22 + dx, 35 + dy)], fill=c)
        d.line([(21 + dx, 35 + dy), (21 + dx, 45 + dy)], fill=c); d.line([(22 + dx, 35 + dy), (22 + dx, 45 + dy)], fill=c)
        d.line([(15 + dx, 46 + dy), (28 + dx, 46 + dy)], fill=c)
    neon(d, glass, NEON_PK, dim(NEON_PK))
    d.line([(15, 27), (28, 27)], fill=NEON_CY); d.line([(17, 29), (26, 29)], fill=dim(NEON_CY, 0.7))
    d.ellipse([26, 19, 31, 24], outline=NEON_GR); d.line([(24, 30), (29, 21)], fill=NEON_YL)
    neon(d, lambda dx, dy, c: text(d, 'BAR', 13 + dx, 52 + dy, c), NEON_CY, dim(NEON_CY))
    # SAKE: the widest board, yellow tube on indigo, a flask and cups, chaser bulbs
    billboard(d, 42, 7, 99, 43, NEON_YL)
    neon(d, lambda dx, dy, c: text(d, 'SAKE', 47 + dx, 13 + dy, c, 2), NEON_YL, dim(NEON_YL))
    neon(d, lambda dx, dy, c: d.line([(47 + dx, 31 + dy), (78 + dx, 31 + dy)], fill=c), NEON_PK, dim(NEON_PK))
    def flask(dx, dy, c):
        d.line([(86 + dx, 28 + dy), (86 + dx, 31 + dy)], fill=c); d.line([(90 + dx, 28 + dy), (90 + dx, 31 + dy)], fill=c)
        d.line([(86 + dx, 31 + dy), (83 + dx, 35 + dy)], fill=c); d.line([(90 + dx, 31 + dy), (93 + dx, 35 + dy)], fill=c)
        d.line([(83 + dx, 35 + dy), (83 + dx, 39 + dy)], fill=c); d.line([(93 + dx, 35 + dy), (93 + dx, 39 + dy)], fill=c)
        d.line([(83 + dx, 39 + dy), (93 + dx, 39 + dy)], fill=c); d.line([(86 + dx, 28 + dy), (90 + dx, 28 + dy)], fill=c)
    neon(d, flask, WHITE, dim(NEON_CY))
    for x in range(45, 98, 4):
        d.point((x, 9), fill=rgb('fff2b0') if (x // 4) % 2 else NEON_YL)
        d.point((x, 41), fill=NEON_YL if (x // 4) % 2 else rgb('fff2b0'))
    # under it, a painted board: ya-ki-to-ri and skewers
    d.rectangle([42, 46, 99, 63], fill=rgb('e8702c')); d.rectangle([42, 46, 99, 63], outline=rgb('8c3a1c'))
    d.line([(43, 47), (98, 47)], fill=rgb('ffa860'))
    kana(d, ['ya', 'ki', 'to', 'ri'], 55, 51, WHITE)
    for x0 in (45, 90):
        d.line([(x0, 59), (x0 + 6, 49)], fill=rgb('f3ead2'))
        for k in range(3):
            d.rectangle([x0 + 1 + k * 2, 55 - k * 3, x0 + 3 + k * 2, 57 - k * 3], fill=rgb('7a3a20') if k != 1 else rgb('9ac05a'))
    for x in (46, 94):
        d.rectangle([x, 63, x + 1, 69], fill=STONE_DK)
    # DARTS: a board in green tube
    billboard(d, 103, 21, 134, 63, NEON_GR)
    d.ellipse([108, 25, 130, 47], fill=rgb('f3ead2'))
    for k in range(8):
        d.pieslice([108, 25, 130, 47], k * 45, k * 45 + 22, fill=rgb('2a2a34'))
    d.ellipse([112, 29, 126, 43], outline=XRED); d.ellipse([116, 33, 122, 39], fill=NEON_GR)
    d.ellipse([118, 35, 120, 37], fill=XRED)
    d.line([(121, 34), (129, 26)], fill=NEON_YL); d.line([(128, 25), (130, 27)], fill=WHITE)
    neon(d, lambda dx, dy, c: text(d, 'DARTS', 105 + dx, 52 + dy, c), NEON_GR, dim(NEON_GR))
    # BEER: a foaming mug in yellow tube on deep blue, the tallest board
    billboard(d, 138, 5, 187, 63, NEON_CY)
    def mug(dx, dy, c):
        d.rectangle([152 + dx, 16 + dy, 168 + dx, 38 + dy], outline=c)
        d.arc([165 + dx, 20 + dy, 176 + dx, 34 + dy], 270, 90, fill=c)
        for x in (157, 163):
            d.line([(x + dx, 21 + dy), (x + dx, 35 + dy)], fill=c)
    neon(d, mug, NEON_YL, dim(NEON_YL))
    d.rectangle([153, 17, 167, 19], fill=rgb('8a6a1c'))
    for cx, cy, r in ((154, 13, 3), (160, 11, 4), (166, 13, 3)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.rectangle([152, 13, 168, 16], fill=WHITE); d.point((169, 18), fill=WHITE); d.point((169, 20), fill=WHITE)
    star(d, 145, 14, 3, NEON_PK); star(d, 181, 30, 3, NEON_PK); d.point((178, 12), fill=WHITE); d.point((143, 32), fill=WHITE)
    neon(d, lambda dx, dy, c: text(d, 'BEER', 140 + dx, 44 + dy, c, 2), NEON_CY, dim(NEON_CY))
    # ---- the block under them: two low storeys of dark plum tile ----------------------------
    for y in range(70, 123):
        for x in range(4, 188):
            v, u = (y - 70) % 4, (x + ((y - 70) // 4) * 3) % 6
            c = PLUM_LO if v == 3 or u == 5 else (PLUM_HI if v == 0 and x < 50 else PLUM)
            d.point((x, y), fill=c)
    d.rectangle([182, 70, 187, 122], fill=PLUM_LO); d.line([(4, 70), (4, 122)], fill=PLUM_HI)
    d.rectangle([2, 66, 189, 70], fill=PLUM_DK); d.line([(2, 66), (189, 66)], fill=PLUM_HI)
    # upstairs: no windows to speak of - each bar's own lit sign box, pipes, a cooler
    boxes = ((8, 26, rgb('d8347c'), 'ko'), (30, 50, rgb('f0b62e'), 'ma'), (58, 72, rgb('1f8fa8'), 'no'),
             (76, 98, rgb('7a48c8'), 'mi'), (104, 120, rgb('e8702c'), 'ri'), (124, 146, rgb('2f9a5a'), 'ku'),
             (152, 166, rgb('d8347c'), 'ta'), (170, 184, rgb('f3ead2'), 'o'))
    for x0, x1, body, k in boxes:
        d.rectangle([x0, 74, x1, 86], fill=body)
        d.line([(x0, 74), (x1, 74)], fill=tuple(min(255, v + 50) for v in body[:3]) + (255,))
        d.line([(x1, 74), (x1, 86)], fill=dim(body, 0.65)); d.line([(x0, 86), (x1, 86)], fill=dim(body, 0.65))
        glyph(d, KANA[k], (x0 + x1) // 2 - 3, 77, rgb('3a2030') if body in (rgb('f0b62e'), rgb('f3ead2')) else WHITE)
    for x in (54, 100, 149):
        d.line([(x, 71), (x, 88)], fill=PLUM_DK); d.line([(x + 1, 71), (x + 1, 88)], fill=PLUM_HI)
    d.rectangle([4, 88, 187, 90], fill=PLUM_DK); d.line([(4, 88), (187, 88)], fill=PLUM_HI)
    # ---- street level: six bars, one to a cell ------------------------------------------------
    d.rectangle([4, 91, 187, 122], fill=PLUM_DK)
    # cell 0: a lamplit lattice window, a red lantern
    d.rectangle([8, 96, 28, 116], fill=DWOOD_DK); d.rectangle([9, 97, 27, 115], fill=LIT)
    for x in range(11, 27, 3):
        d.line([(x, 97), (x, 115)], fill=DWOOD_DK)
    d.line([(9, 106), (27, 106)], fill=DWOOD_DK)
    # cell 1: THE door - a padded door inside a pink neon frame
    d.rectangle([36, 92, 60, 122], fill=rgb('15122a'))
    neon(d, lambda dx, dy, c: d.rectangle([37 + dx, 93 + dy, 59 + dx, 121 + dy], outline=c), NEON_PK, dim(NEON_PK))
    bar(d, 40, 97, 56, 122, rgb('6a2438'), rgb('8c3a4c'), rgb('4a1828'))
    for yy in (104, 111, 118):
        for xx in (44, 52):
            d.point((xx, yy), fill=GOLD)
    d.rectangle([54, 109, 55, 113], fill=GOLD)
    d.ellipse([44, 99, 52, 105], fill=rgb('2a1a3a')); d.ellipse([45, 100, 51, 104], fill=WARM)
    # cell 2: an izakaya's sliding door under an indigo noren, lit
    d.rectangle([68, 94, 92, 122], fill=DWOOD_DK); d.rectangle([69, 104, 91, 121], fill=LIT)
    d.line([(80, 104), (80, 121)], fill=DWOOD_DK)
    for x in range(71, 91, 3):
        d.line([(x, 112), (x, 121)], fill=CEDAR_LO)
    noren(d, 68, 95, 92, 105, INDIGO, INDIGO_HI, INDIGO_LO, 3)
    for x in (72, 80, 88):
        d.ellipse([x - 1, 98, x + 1, 100], outline=WHITE)
    # cell 3: a back-lit bottle window
    d.rectangle([100, 95, 124, 117], fill=rgb('2a1a3a')); d.rectangle([101, 96, 123, 99], fill=NEON_VI)
    for i, x in enumerate(range(102, 123, 3)):
        c = (rgb('7fd0a0'), rgb('f0c060'), rgb('e07a7a'), rgb('8fb8f0'))[i % 4]
        d.rectangle([x, 104 + (i % 2), x + 1, 110], fill=c); d.point((x, 103 + (i % 2)), fill=c)
        d.rectangle([x, 113, x + 1, 116], fill=dim(c, 0.7))
    d.line([(101, 111), (123, 111)], fill=PLUM_HI)
    # cell 4: the stair up to the bars above, under a cyan arrow
    d.rectangle([132, 92, 152, 122], fill=rgb('0f0d1a'))
    for k in range(5):
        d.line([(133, 120 - k * 5), (151 - k * 2, 120 - k * 5)], fill=PLUM_HI)
        d.rectangle([133, 121 - k * 5, 151 - k * 2, 122 - k * 5], fill=PLUM)
    neon(d, lambda dx, dy, c: (d.line([(136 + dx, 97 + dy), (147 + dx, 97 + dy)], fill=c),
                               d.line([(144 + dx, 94 + dy), (147 + dx, 97 + dy)], fill=c),
                               d.line([(144 + dx, 100 + dy), (147 + dx, 97 + dy)], fill=c)), NEON_CY, dim(NEON_CY))
    # cell 5: a snack bar's round window and a standing menu
    d.rectangle([160, 94, 184, 122], fill=rgb('2a1a3a'))
    d.ellipse([163, 97, 181, 115], fill=PLUM_DK); d.ellipse([165, 99, 179, 113], fill=rgb('ff9a4a'))
    d.rectangle([166, 107, 170, 113], fill=PLUM_DK); d.rectangle([167, 104, 169, 107], fill=PLUM_DK)      # a head inside
    d.line([(172, 99), (172, 113)], fill=PLUM_DK)
    for x, c in ((30, XRED), (94, rgb('ffd84a')), (126, XRED)):                 # paper lanterns between the doors
        lantern(d, x, 96, 6, 12, c, tuple(min(255, v + 40) for v in c[:3]) + (255,), dim(c, 0.7))
    bar(d, 154, 108, 159, 122, rgb('f3ead2'), WHITE, PAPER_LO)    # an A-board
    d.line([(155, 111), (158, 111)], fill=XRED); d.line([(155, 114), (158, 114)], fill=CREAM_DK)
    d.line([(155, 117), (158, 117)], fill=CREAM_DK)
    footing(d, 2, 189, 122, 4, rgb('4a4658'), rgb('7c7886'))
    d.rectangle([38, 123, 58, 125], fill=XRED)
    outline(im)
    return im


def motsunabe_shop():
    """A motsunabe (offal hot-pot) house, Nakasu's other front: dark boards
    under a low tin roof, a huge red paper lantern, the pot on its board."""
    im, d = canvas(4, 4)                 # 128 x 128
    # a low-pitched tin roof, rust red
    for y in range(18, 34):
        e = y - 18
        for x in range(8 - e // 3, 120 + e // 3):
            c = rgb('6a2f2c') if x % 6 == 5 else (rgb('b0584a') if x % 6 == 0 else rgb('94443c'))
            if e == 0:
                c = rgb('c87a66')
            d.point((x, y), fill=c)
    d.rectangle([2, 34, 125, 36], fill=rgb('5a2826')); d.line([(2, 34), (125, 34)], fill=rgb('c87a66'))
    # upstairs: black boards, the long white board with mo-tsu-na-be, the pot
    planks(d, 6, 37, 121, 76, (rgb('3d3338'), rgb('554a50'), rgb('30282d'), rgb('221c21')), w=7, seed=3)
    bar(d, 12, 42, 86, 62, rgb('fbf6ea'), WHITE, PAPER_LO)
    d.rectangle([12, 42, 86, 62], outline=rgb('3a2c2a'))
    kana(d, ['mo', 'tsu', 'na', 'be'], 19, 45, rgb('1c1a1f'), 2)
    # the pot: an iron nabe heaped with cabbage and chives, chillies, steam
    d.ellipse([92, 50, 118, 62], fill=SOOT); d.rectangle([92, 52, 118, 56], fill=SOOT)
    d.rectangle([89, 52, 91, 54], fill=SOOT); d.rectangle([119, 52, 121, 54], fill=SOOT)
    d.ellipse([94, 44, 116, 56], fill=rgb('dfe8b4')); d.ellipse([94, 44, 108, 52], fill=rgb('f1f4d4'))
    d.rectangle([98, 46, 112, 47], fill=rgb('5f9a52')); d.rectangle([100, 49, 114, 49], fill=rgb('4a8244'))
    for x in (99, 105, 111):
        d.point((x, 51), fill=XRED); d.point((x + 1, 52), fill=XRED)
    d.line([(96, 60), (114, 60)], fill=rgb('5a5662'))
    d.rectangle([12, 66, 86, 73], fill=XRED); d.line([(12, 66), (86, 66)], fill=XRED_HI)
    for k in range(6):                                            # a row of small paper lanterns on the red rail
        x = 16 + k * 12
        d.rectangle([x, 67, x + 6, 72], fill=WHITE if k % 2 else rgb('ffd84a')); d.point((x + 3, 69), fill=XRED)
    # the pent
    for y in range(77, 85):
        e = y - 77
        for x in range(4 - e // 3, 124 + e // 3):
            d.point((x, y), fill=rgb('6a2f2c') if x % 6 == 5 else (rgb('b0584a') if x % 6 == 0 else rgb('94443c')))
    d.rectangle([1, 85, 126, 86], fill=rgb('5a2826'))
    # downstairs: a lit window of tables, the door under a white noren, the great lantern
    d.rectangle([6, 87, 121, 122], fill=rgb('30282d'))
    timber_posts(d, (6, 58, 118), 87, 122, (rgb('3d3338'), rgb('554a50'), rgb('30282d'), rgb('221c21')))
    d.rectangle([12, 92, 54, 114], fill=rgb('221c21')); d.rectangle([13, 93, 53, 113], fill=WARM)
    d.line([(13, 93), (53, 93)], fill=WHITE)
    for x in (18, 34):                                            # diners at a pot
        d.rectangle([x, 101, x + 6, 113], fill=rgb('5a3a44') if x == 18 else rgb('3f5a6a'))
        d.rectangle([x + 1, 96, x + 5, 101], fill=SKIN); d.rectangle([x + 1, 95, x + 5, 96], fill=rgb('3a2c2a'))
    d.rectangle([24, 106, 46, 113], fill=CEDAR_LO); d.rectangle([27, 103, 32, 106], fill=SOOT)
    for x in (26, 40):
        d.line([(x, 93), (x, 113)], fill=rgb('221c21'))
    d.rectangle([12, 115, 54, 122], fill=rgb('3d3338'))
    for x in range(14, 54, 4):
        d.line([(x, 116), (x, 121)], fill=rgb('30282d'))
    # the door (cell 2): sliding lattice doors standing open on a lit hall
    d.rectangle([64, 90, 94, 122], fill=rgb('221c21'))
    d.rectangle([66, 100, 92, 122], fill=LIT)
    d.rectangle([72, 100, 86, 122], fill=rgb('6a4030')); d.rectangle([74, 102, 84, 122], fill=rgb('40282a'))    # the open way in
    d.line([(66, 111), (71, 111)], fill=CEDAR_LO); d.line([(87, 111), (92, 111)], fill=CEDAR_LO)
    for x in (68, 70, 88, 90):
        d.line([(x, 100), (x, 121)], fill=CEDAR_LO)
    noren(d, 64, 91, 94, 101, rgb('fbf6ea'), WHITE, PAPER_LO, 4)
    kana(d, ['mo', 'tsu'], 72, 93, XRED)
    # the great red lantern by the door
    d.line([(107, 87), (107, 90)], fill=SOOT)
    d.rectangle([102, 90, 112, 92], fill=SOOT)
    d.ellipse([98, 91, 116, 117], fill=XRED); d.ellipse([99, 92, 108, 110], fill=XRED_HI)
    d.ellipse([101, 94, 115, 116], fill=XRED)
    for y in range(96, 114, 3):
        d.line([(99, y), (115, y)], fill=XRED_LO)
    d.arc([98, 91, 116, 117], 300, 90, fill=XRED_LO)
    glyph(d, KANA['na'], 104, 97, WHITE); glyph(d, KANA['be'], 104, 106, WHITE)
    d.rectangle([102, 116, 112, 118], fill=SOOT)
    footing(d, 3, 124, 122, 4)
    outline(im)
    puff(im, 100, 40, 4, a=120); puff(im, 108, 35, 4, a=90); puff(im, 104, 29, 3, a=60)
    return im


def leaded(d, x0, y0, x1, y1, frame):
    """A pub window: small leaded panes, lamplight, bottle-glass roundels."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=LIT)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 3], fill=WARM)
    for x in range(x0 + 1, x1):
        for y in range(y0 + 1, y1):
            if (x - x0) % 5 == 0 or (y - y0) % 5 == 0:
                d.point((x, y), fill=rgb('8a6a34'))
    for x in range(x0 + 3, x1 - 1, 10):
        d.point((x, y0 + 8), fill=rgb('7fb8a0')); d.point((x + 5, y0 + 13), fill=rgb('e08a5a'))


def pub():
    """The fake British pub: black-and-white half-timber over a bottle-green
    front in gold letters. Not Sendai's red-fascia pub."""
    im, d = canvas(4, 4)                 # 128 x 128
    # ---- the roof: slate, a centre gable, a chimney ------------------------------------
    slate = (rgb('5c6272'), rgb('434858'), rgb('868c9c'), rgb('2f3340'))
    bar(d, 100, 2, 111, 22, rgb('8a4a3c'), rgb('aa6650'), rgb('643428'))
    d.rectangle([98, 0, 113, 3], fill=rgb('643428')); d.line([(98, 0), (113, 0)], fill=rgb('aa6650'))
    for (y, x0, x1) in curve_rows(12, 36, (14, 113), (2, 125), 1.0):
        for x in range(x0, x1 + 1):
            c = slate[1] if (y - 12) % 4 == 3 or (x + ((y - 12) // 4) * 3) % 6 == 0 else (slate[0] if x < 84 else slate[1])
            d.point((x, y), fill=c)
        d.point((x0, y), fill=slate[2]); d.point((x1, y), fill=slate[3])
    d.rectangle([12, 9, 115, 12], fill=slate[1]); d.line([(12, 9), (115, 9)], fill=slate[2])
    d.rectangle([2, 37, 125, 38], fill=slate[3])
    # the gable: plaster, black timbers, a little window
    for y in range(6, 40):
        half = round((y - 4) * 26 / 36)
        d.line([(64 - half, y), (64 + half, y)], fill=PLASTER if y > 8 else SOOT)
    for k in range(4):
        d.line([(64, 3 + k), (36, 39 + k)], fill=SOOT if k else rgb('55525c'))
        d.line([(64, 3 + k), (92, 39 + k)], fill=SOOT)
    d.line([(64, 8), (64, 39)], fill=SOOT); d.line([(50, 28), (78, 28)], fill=SOOT)
    d.line([(52, 39), (64, 28)], fill=SOOT); d.line([(76, 39), (64, 28)], fill=SOOT)
    lit_window(d, 59, 14, 69, 25, SOOT, (1, 1))
    # ---- the upper storey: half-timber ----------------------------------------------------
    d.rectangle([6, 40, 121, 72], fill=PLASTER)
    d.rectangle([110, 40, 121, 72], fill=PLASTER_LO)
    for x in (6, 30, 54, 73, 97, 119):
        d.rectangle([x, 40, x + 2, 72], fill=SOOT)
    d.rectangle([6, 40, 121, 42], fill=SOOT); d.rectangle([6, 70, 121, 73], fill=SOOT)
    d.line([(6, 40), (121, 40)], fill=rgb('55525c'))
    for x0 in (9, 100):                                           # braces
        d.line([(x0, 69), (x0 + 19, 43)], fill=SOOT, width=2)
    for x0 in (33, 76):
        d.line([(x0, 43), (x0 + 19, 69)], fill=SOOT, width=2)
    for x0 in (12, 79):                                           # windows with flower boxes
        leaded(d, x0 + 22 if x0 == 12 else x0, 46, (x0 + 22 if x0 == 12 else x0) + 15, 62, SOOT)
    for x0 in (34, 79):
        d.rectangle([x0 - 1, 63, x0 + 17, 66], fill=PUBG_LO)
        for x in range(x0, x0 + 17, 3):
            d.point((x, 62), fill=(XRED_HI, rgb('ffd84a'), rgb('e07ab0'))[x % 3]); d.point((x + 1, 63), fill=FIR_HI)
    # the hanging sign on its bracket: an oak
    d.line([(58, 46), (70, 46)], fill=SOOT); d.line([(64, 46), (64, 49)], fill=SOOT)
    bar(d, 57, 49, 71, 67, rgb('1f3f36'), PUBG_HI, PUBG_LO)
    d.rectangle([57, 49, 71, 67], outline=GOLD)
    d.ellipse([60, 52, 68, 60], fill=rgb('6fa262')); d.ellipse([60, 52, 65, 57], fill=rgb('9cc87a'))
    d.rectangle([63, 59, 64, 64], fill=rgb('8a6650'))
    # ---- the front: bottle green, gold letters -----------------------------------------------
    bar(d, 4, 74, 123, 88, PUBG, PUBG_HI, PUBG_LO)
    d.rectangle([4, 74, 123, 75], fill=PUBG_HI); d.line([(4, 88), (123, 88)], fill=INK)
    d.rectangle([8, 77, 119, 86], outline=GOLD)
    ctext(d, 'THE OLD OAK', 64, 78, rgb('f0d98c'))
    d.rectangle([6, 89, 121, 122], fill=PUBG_LO)
    for x in (6, 60, 92, 118):                                    # pilasters
        bar(d, x, 89, x + 3, 122, PUBG, PUBG_HI, rgb('16302a'))
        d.rectangle([x, 89, x + 3, 91], fill=GOLD)
    leaded(d, 11, 93, 58, 111, rgb('16302a'))
    d.line([(34, 93), (34, 111)], fill=rgb('16302a')); d.line([(35, 93), (35, 111)], fill=rgb('16302a'))
    d.rectangle([10, 112, 59, 122], fill=PUBG); d.rectangle([13, 114, 33, 120], outline=PUBG_HI)
    d.rectangle([37, 114, 56, 120], outline=PUBG_HI)
    # the door (cell 2): oxblood, brass, a fanlight
    d.rectangle([65, 91, 90, 122], fill=rgb('16302a'))
    bar(d, 67, 99, 88, 122, rgb('7a2a30'), rgb('9c4448'), rgb('561c24'))
    d.rectangle([70, 102, 76, 110], outline=rgb('561c24')); d.rectangle([79, 102, 85, 110], outline=rgb('561c24'))
    d.rectangle([70, 113, 76, 119], outline=rgb('561c24')); d.rectangle([79, 113, 85, 119], outline=rgb('561c24'))
    d.rectangle([85, 111, 86, 112], fill=rgb('f0d98c')); d.rectangle([75, 120, 80, 121], fill=rgb('c6a663'))
    d.rectangle([67, 92, 88, 97], fill=LIT); d.line([(67, 92), (88, 92)], fill=WARM)
    for x in (72, 77, 83):
        d.line([(x, 92), (x, 97)], fill=rgb('16302a'))
    leaded(d, 97, 93, 116, 111, rgb('16302a'))
    d.rectangle([96, 112, 117, 122], fill=PUBG); d.rectangle([99, 114, 114, 120], outline=PUBG_HI)
    # brass lamps, a chalk board
    for x in (62, 93):
        d.rectangle([x - 1, 92, x + 1, 97], fill=rgb('fff2b0')); d.rectangle([x - 2, 91, x + 2, 91], fill=GOLD)
        d.point((x, 98), fill=GOLD)
    bar(d, 44, 108, 56, 123, rgb('2b2a30'), None, None); d.rectangle([44, 108, 56, 123], outline=rgb('8a6650'))
    text(d, 'ALE', 46, 110, rgb('f3ead2'))
    d.line([(46, 119), (54, 119)], fill=rgb('ffd84a'))
    footing(d, 4, 123, 122, 4)
    outline(im)
    return im


def rail_run(d, y, x0=0, x1=31):
    """The riverside railing standing on y+19: a round top rail, pickets, a
    stone kerb. Its west post is at x0 (a run's posts fall on cell edges)."""
    iron, iron_hi, iron_lo = rgb('3d4656'), rgb('6a768c'), rgb('262c3a')
    d.rectangle([x0, y + 15, x1, y + 19], fill=GRAN); d.line([(x0, y + 15), (x1, y + 15)], fill=GRAN_HI)
    d.line([(x0, y + 19), (x1, y + 19)], fill=GRAN_DK)
    for x in range(x0, x1 + 1):
        if (x - x0) % 16 == 15:
            d.point((x, y + 17), fill=GRAN_LO); d.point((x, y + 16), fill=GRAN_LO)
    for x in range(x0 + 4, x1, 4):
        d.line([(x, y + 3), (x, y + 14)], fill=iron if (x // 4) % 2 else iron_lo)
    d.rectangle([x0, y + 1, x1, y + 2], fill=iron); d.line([(x0, y), (x1, y)], fill=iron_hi)
    d.line([(x0, y + 11), (x1, y + 11)], fill=iron_lo)
    d.rectangle([x0, y - 1, x0 + 1, y + 14], fill=iron); d.line([(x0, y - 1), (x0, y + 14)], fill=iron_hi)
    d.rectangle([x0 - 0, y - 2, x0 + 1, y - 2], fill=iron_hi)


def river_rail(lanterns=False):
    im, d = canvas(1, 2 if lanterns else 1)
    oy = 32 if lanterns else 0
    rail_run(d, oy + 11)
    if lanterns:
        iron, iron_hi = rgb('3d4656'), rgb('6a768c')
        d.rectangle([15, 10, 17, oy + 25], fill=iron); d.line([(15, 10), (15, oy + 25)], fill=iron_hi)
        d.rectangle([14, oy + 22, 18, oy + 26], fill=iron)
        d.rectangle([3, 12, 29, 13], fill=iron); d.line([(3, 12), (29, 12)], fill=iron_hi)
        d.rectangle([14, 7, 18, 9], fill=iron); d.point((16, 6), fill=GOLD)
        d.line([(8, 14), (15, 20)], fill=iron); d.line([(24, 14), (17, 20)], fill=iron)
        # two paper lanterns: red with a white band, white with a red mark
        for x, body, hi, lo, mark in ((3, XRED, XRED_HI, XRED_LO, WHITE), (20, PAPER, WHITE, PAPER_LO, XRED)):
            d.line([(x + 4, 14), (x + 4, 15)], fill=SOOT)
            d.rectangle([x + 2, 16, x + 6, 17], fill=SOOT)
            d.rectangle([x, 18, x + 8, 31], fill=body)
            d.line([(x, 18), (x, 31)], fill=hi); d.line([(x + 8, 18), (x + 8, 31)], fill=lo)
            d.point((x, 18), fill=CLEAR); d.point((x + 8, 18), fill=CLEAR); d.point((x, 31), fill=CLEAR); d.point((x + 8, 31), fill=CLEAR)
            for yy in range(20, 31, 2):
                d.line([(x + 1, yy), (x + 7, yy)], fill=lo)
            d.rectangle([x + 3, 21, x + 5, 28], fill=mark)
            d.rectangle([x + 2, 32, x + 6, 33], fill=SOOT)
            d.line([(x + 4, 34), (x + 4, 36)], fill=GOLD)
    outline(im)
    return im


def nakasu_gate():
    """The district's gate sign: steel posts wound with lights, a marquee arc
    of bulbs, NAKASU in kana as pink tube. Not Sapporo's red ramen gate."""
    im, d = canvas(4, 4)                 # 128 x 128
    steel, steel_hi, steel_lo = rgb('4a5266'), rgb('8a94aa'), rgb('2e3444')
    for x0 in (7, 113):
        bar(d, x0, 30, x0 + 7, 122, steel, steel_hi, steel_lo)
        d.rectangle([x0 + 5, 30, x0 + 7, 122], fill=steel_lo)
        d.rectangle([x0 - 3, 118, x0 + 10, 125], fill=steel_lo); d.line([(x0 - 3, 118), (x0 + 10, 118)], fill=steel_hi)
        for y in range(62, 118):                                  # a spiral of lights
            k = (y - 62) % 8
            d.point((x0 + k, y), fill=(NEON_PK, NEON_CY)[((y - 62) // 8) % 2] if k < 8 else steel)
    # the marquee arc
    for a in range(0, 181, 1):
        r = math.radians(a)
        for rr in range(54, 61):
            x, y = 64 - rr * math.cos(r), 62 - rr * 0.92 * math.sin(r)
            d.point((round(x), round(y)), fill=steel_hi if rr == 60 else (steel_lo if rr == 54 else steel))
    for a in range(4, 180, 7):
        r = math.radians(a)
        x, y = 64 - 57 * math.cos(r), 62 - 57 * 0.92 * math.sin(r)
        d.rectangle([round(x), round(y), round(x) + 1, round(y) + 1], fill=NEON_YL if (a // 7) % 2 else rgb('fff8d8'))
    # the board
    d.rectangle([10, 30, 117, 62], fill=rgb('15122a'))
    d.rectangle([10, 30, 117, 62], outline=steel_hi)
    d.rectangle([12, 32, 115, 60], outline=dim(NEON_CY))
    d.rectangle([12, 32, 115, 32], fill=NEON_CY); d.rectangle([12, 60, 115, 60], fill=NEON_CY)
    neon(d, lambda dx, dy, c: kana(d, ['na', 'ka', 'su'], 30 + dx, 36 + dy, c, 3), NEON_PK, dim(NEON_PK))
    # a crescent moon and stars in the head of the arc
    d.ellipse([56, 10, 72, 26], fill=NEON_YL); d.ellipse([61, 8, 77, 24], fill=CLEAR)
    star(d, 78, 16, 3, NEON_CY); star(d, 46, 20, 2, NEON_PK); star(d, 88, 24, 2, NEON_YL)
    # the under-board: NAKASU in cyan, hanging on chains
    d.line([(34, 63), (34, 66)], fill=steel_lo); d.line([(93, 63), (93, 66)], fill=steel_lo)
    d.rectangle([30, 67, 97, 78], fill=rgb('15122a')); d.rectangle([30, 67, 97, 78], outline=steel)
    neon(d, lambda dx, dy, c: ctext(d, 'NAKASU', 64 + dx, 69 + dy, c), NEON_CY, dim(NEON_CY))
    outline(im)
    return grounded(im, rects=[(4, 124, 18, 127, 70), (110, 124, 124, 127, 70)])


# ==============================================================================
# Canal City
# ==============================================================================
def water_px(x, y):
    k = (x + round(2.5 * math.sin(y * math.pi / 8))) % 16
    if y % 8 == 3 and k < 6:
        return TEAL_HI
    if y % 8 == 7 and 8 <= k < 12:
        return TEAL_LO
    return TEAL


def quay_cap(d, x0, y0, x1, y1):
    """A cream coping with a terracotta band: the mall's own colours."""
    d.rectangle([x0, y0, x1, y1], fill=rgb('f1e2c4'))
    d.line([(x0, y0), (x1, y0)], fill=rgb('fff6e0')); d.line([(x0, y1), (x1, y1)], fill=rgb('cdb893'))
    m = (y0 + y1) // 2
    d.rectangle([x0, m, x1, m + 1], fill=TERRA); d.line([(x0, m), (x1, m)], fill=TERRA_HI)
    for x in range(x0, x1 + 1):
        if x % 16 == 15:
            d.line([(x, y0), (x, y1)], fill=rgb('cdb893'))


def canal(kind='run'):
    """A strip of Canal City's canal, 1x2, tiling east-west: the far quay (its
    coping and its terracotta wall down to the water), teal water, the near
    quay's coping. `jets` adds fountain jets; `end-e` / `end-w` close the basin;
    `bridge` is a footbridge across it (flat: walked on)."""
    im, d = canvas(1, 2)
    px_rect(d, 0, 0, 31, 63, lambda x, y: water_px(x, y))
    quay_cap(d, 0, 0, 31, 6)
    for y in range(7, 17):                                        # the far wall
        for x in range(32):
            v, u = (y - 7) % 4, (x + ((y - 7) // 4) * 4) % 8
            d.point((x, y), fill=TERRA_LO if v == 3 or u == 7 else TERRA)
    d.line([(0, 7), (31, 7)], fill=rgb('7a3a30'))
    d.line([(0, 17), (31, 17)], fill=TEAL_LO); d.line([(0, 18), (31, 18)], fill=TEAL_LO)
    for x in range(0, 32, 2):                                     # the wall's reflection
        d.point((x + (1 if x % 4 else 0), 20), fill=rgb('7a8f96')); d.point((x, 22), fill=rgb('5a97a6'))
    quay_cap(d, 0, 54, 31, 63)
    d.line([(0, 53), (31, 53)], fill=TEAL_LO)
    if kind == 'jets':
        for cx, h in ((6, 20), (16, 30), (26, 20)):
            top = 47 - h
            for k in range(h):
                y = 47 - k
                d.point((cx, y), fill=WHITE); d.point((cx + 1, y), fill=rgb('cfeef4') if k % 3 else WHITE)
            for k in range(1, 7):                                 # the head of the jet falling back
                dy = (k * k) // 4
                d.point((cx - k, top + dy), fill=WHITE); d.point((cx + 1 + k, top + dy), fill=rgb('e4f6f8'))
                if k % 2:
                    d.point((cx - k, top + dy + 2), fill=rgb('cfeef4')); d.point((cx + 1 + k, top + dy + 3), fill=WHITE)
            d.rectangle([cx - 1, top - 1, cx + 2, top], fill=WHITE)
            d.ellipse([cx - 4, 45, cx + 5, 49], outline=TEAL_HI)
            d.point((cx - 5, 44), fill=WHITE); d.point((cx + 6, 43), fill=WHITE)
    if kind in ('end-e', 'end-w'):
        east = kind == 'end-e'
        for y in range(7, 54):                                    # the basin's rounded end
            t = (y - 30) / 24
            inset = round(10 * (1 - math.sqrt(max(0.0, 1 - t * t)))) + 9
            for k in range(inset):
                x = 31 - k if east else k
                c = rgb('f1e2c4')
                if k == inset - 1:
                    c = rgb('7a3a30')
                elif k >= inset - 4:
                    c = TERRA if k > inset - 4 else TERRA_HI
                elif k == inset - 5:
                    c = rgb('cdb893')
                d.point((x, y), fill=c)
        quay_cap(d, 0, 0, 31, 6); quay_cap(d, 0, 54, 31, 63)
    if kind == 'bridge':
        # a timber footbridge sitting ON the two quays: the copings run on unbroken either side of it,
        # water shows past both rails and its shadow lies on the water to the east
        for y in range(19, 54):
            for x in range(27, 32):
                d.point((x, y), fill=rgb('256a80') if (x + y) % 2 or x < 30 else TEAL_LO)
        for y in range(3, 61):                                    # the deck: boards laid across the way you walk
            for x in range(6, 26):
                v = (y - 3) % 5
                c = HONEY_DK if v == 4 else (HONEY_HI if v == 0 else (HONEY_LO if h3(x // 5, y // 5, 3) < 60 else HONEY))
                if x in (6, 25):
                    c = HONEY_DK
                d.point((x, y), fill=c)
        d.line([(6, 3), (25, 3)], fill=HONEY_HI); d.line([(6, 60), (25, 60)], fill=HONEY_DK)
        for x0 in (3, 26):                                        # the rails: terracotta steel, posts, a lit top
            d.rectangle([x0, 4, x0 + 2, 59], fill=TERRA_LO); d.line([(x0, 4), (x0, 59)], fill=TERRA_HI)
            d.line([(x0 + 1, 4), (x0 + 1, 59)], fill=TERRA)
            for y in range(4, 60, 11):
                d.rectangle([x0 - 1, y, x0 + 3, y + 2], fill=rgb('f1e2c4')); d.line([(x0 - 1, y), (x0 + 3, y)], fill=WHITE)
                d.line([(x0 - 1, y + 2), (x0 + 3, y + 2)], fill=rgb('cdb893'))
            d.line([(x0 + 3, 8), (x0 + 3, 58)], fill=rgb('5a3a2a') if x0 == 3 else rgb('256a80'))    # the rail's own shadow
    return im


def fan_tex(x, y):
    """Warm setts laid in fans (period 16 x 8): arcs of ochre, cream joints."""
    row = y // 8
    cx = (x + (8 if row % 2 else 0)) % 16 - 8
    cy = y % 8
    r = math.hypot(cx, cy + 1.0)
    band = int(r / 2.3)
    if abs(r - band * 2.3) < 0.55 or (cy == 0 and abs(cx) >= 7):
        return rgb('b08c68')
    k = h3(x // 2, y // 2, 4)
    tones = (rgb('dcb486'), rgb('d2a878'), rgb('e2c092'), rgb('cc9e74'))
    c = tones[(band + row) % 4]
    return rgb('c0946e') if k < 16 else c


def fan_kerb(m, along):
    if m == 3:
        return rgb('a8744e')
    if m == 0:
        return rgb('fff6e0') if along % 16 != 15 else rgb('d8c49c')
    return (TERRA if m == 1 else rgb('f1e2c4')) if along % 16 != 15 else rgb('d8c49c')


def herring_tex(x, y):
    """Mauve brick in herringbone (period 16): bricks 8 x 4 and 4 x 8."""
    u, v = x % 16, y % 16
    # the classic 2:1 herringbone on a 4px module
    a, b = u // 4, v // 4
    horiz = (a + b) % 4 in (0, 1)
    if horiz:
        start = (a + b) % 4 == 0
        edge = (v % 4 == 3) or (start and u % 4 == 0) or ((not start) and u % 4 == 3)
        idx = (a - (0 if start else 1) + b * 3) % 5
    else:
        start = (a + b) % 4 == 2
        edge = (u % 4 == 3) or (start and v % 4 == 0) or ((not start) and v % 4 == 3)
        idx = (a * 3 + b - (0 if start else 1) + 2) % 5
    if edge:
        return rgb('6f5e72')
    tones = (rgb('a48a9a'), rgb('97808f'), rgb('ad94a2'), rgb('9c8494'), rgb('8f788a'))
    c = tones[idx]
    return rgb('b7a0ac') if h3(x, y, 8) < 6 else c


def herring_kerb(m, along):
    if m == 3:
        return rgb('6f5e72')
    if along % 16 == 15:
        return rgb('8a8e98')
    return rgb('dde0e5') if m == 0 else rgb('b9bdc4')


# ==============================================================================
# Old Hakata
# ==============================================================================
def timber_posts(d, xs, y0, y1, pal=None, w=3):
    base, hi, lo, dk = pal or (DWOOD, DWOOD_HI, DWOOD_LO, DWOOD_DK)
    for x in xs:
        bar(d, x, y0, x + w, y1, base, hi, dk)


def kato_mado(d, cx, y0, y1, w=13, lit=False):
    """A bell-shaped temple window in a vermilion rim, a lattice behind."""
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        half = round(w / 2 * (0.25 + 0.75 * min(1.0, t * 2.2) ** 0.6)) if t < 0.5 else round(w / 2)
        for x in range(cx - half, cx + half + 1):
            edge = x in (cx - half, cx + half) or y in (y0, y1)
            c = VERM_LO if edge else ((LIT if lit else rgb('3a3040')) if (x - cx) % 3 else DWOOD_DK)
            d.point((x, y), fill=c)
    d.point((cx, y0 - 1), fill=VERM_LO)


def tochoji_hall():
    """Tochoji's low wooden hall: a broad hip-and-gable roof of old tile over
    dark timber and white plaster, the great-buddha plaque over open doors."""
    im, d = canvas(5, 4)                 # 160 x 128
    # ---- the roof --------------------------------------------------------------------
    roof(d, 14, 52, (44, 115), (2, 157), pal=TOCHO_P, p=1.35)
    light, dark, hi, deep = TOCHO_P
    # the gable in the roof's face: a plaster triangle with a hanging fish board
    for y in range(20, 40):
        half = round((y - 18) * 22 / 22)
        d.line([(80 - half, y), (80 + half, y)], fill=PLASTER if y > 22 else dark)
        d.point((80 - half, y), fill=dark); d.point((80 + half, y), fill=deep)
        d.point((80 - half - 1, y), fill=hi)
    d.line([(58, 40), (102, 40)], fill=deep); d.line([(58, 41), (102, 41)], fill=dark)
    for x in (70, 80, 90):                                        # the gable's struts and tie beam
        d.line([(x, 24 + abs(80 - x)), (x, 39)], fill=DWOOD)
    d.line([(66, 33), (94, 33)], fill=DWOOD); d.line([(66, 34), (94, 34)], fill=DWOOD_LO)
    d.ellipse([77, 25, 83, 31], fill=rgb('e8b84a')); d.point((79, 27), fill=rgb('fff0a8'))   # a gilt boss
    # ---- the eave's shadow, the bracket band ---------------------------------------------
    d.rectangle([8, 56, 151, 60], fill=DWOOD_DK)
    for x in range(10, 151, 6):
        d.rectangle([x, 57, x + 2, 59], fill=PLASTER_LO); d.point((x, 57), fill=WHITE)
    d.rectangle([8, 61, 151, 63], fill=DWOOD); d.line([(8, 61), (151, 61)], fill=DWOOD_HI)
    # ---- the wall: bays of plaster between dark posts ---------------------------------------
    d.rectangle([10, 64, 149, 108], fill=PLASTER)
    d.rectangle([126, 64, 149, 108], fill=PLASTER_LO)
    d.rectangle([10, 64, 149, 66], fill=PLASTER_SH)
    d.rectangle([10, 98, 149, 108], fill=DWOOD)                   # a boarded dado
    for x in range(10, 150, 4):
        d.line([(x, 99), (x, 108)], fill=DWOOD_LO)
    d.line([(10, 98), (149, 98)], fill=DWOOD_HI)
    timber_posts(d, (8, 30, 54, 102, 126, 148), 64, 110)
    kato_mado(d, 20, 72, 92); kato_mado(d, 42, 72, 92, lit=True)
    kato_mado(d, 116, 72, 92, lit=True); kato_mado(d, 138, 72, 92)
    # ---- the open centre bay: the gilded buddha in lamplight ------------------------------
    d.rectangle([58, 64, 101, 110], fill=rgb('2a1c1e'))
    for y in range(66, 110):                                      # the lamplight falls off to the sides
        for x in range(60, 100):
            q = math.hypot((x - 80) / 20, (y - 86) / 26)
            if q < 1:
                d.point((x, y), fill=(rgb('f6dc8c'), rgb('e0b45c'), rgb('a8743c'), rgb('5e3a2a'))[min(3, int(q * 4))])
    gold, gold_hi, gold_lo = rgb('e8b84a'), rgb('fff0a8'), rgb('a8762c')
    d.ellipse([70, 70, 90, 90], outline=gold_lo)                  # the halo, clear of the plaque
    d.ellipse([75, 74, 85, 84], fill=gold); d.ellipse([75, 74, 81, 80], fill=gold_hi)          # the head
    d.rectangle([78, 71, 82, 74], fill=gold_lo)                   # the topknot
    d.point((78, 79), fill=gold_lo); d.point((82, 79), fill=gold_lo); d.line([(79, 82), (81, 82)], fill=gold_lo)
    d.polygon([(68, 97), (72, 85), (88, 85), (92, 97)], fill=gold)                # shoulders
    d.polygon([(68, 97), (72, 85), (76, 85), (74, 97)], fill=gold_hi)
    d.ellipse([64, 92, 96, 104], fill=gold); d.arc([64, 92, 96, 104], 180, 300, fill=gold_hi)   # the folded knees
    d.arc([64, 92, 96, 104], 0, 140, fill=gold_lo)
    d.rectangle([76, 92, 84, 95], fill=gold_hi)                   # hands in the lap
    d.rectangle([62, 104, 98, 108], fill=rgb('8a3a34')); d.line([(62, 104), (98, 104)], fill=VERM_HI)   # the lotus dais
    for x in range(64, 98, 5):
        d.point((x, 106), fill=gold)
    # the doors folded back, a rope and its bell
    for x0 in (58, 97):
        bar(d, x0, 66, x0 + 4, 110, DWOOD, DWOOD_HI, DWOOD_DK)
        for y in range(70, 108, 8):
            d.point((x0 + 2, y), fill=gold)
    # ---- the plaque: gold on black, DAI-BUTSU ------------------------------------------------
    bar(d, 62, 44, 97, 62, rgb('1c1a1f'), None, None)
    d.rectangle([62, 44, 97, 62], outline=gold); d.rectangle([64, 46, 95, 60], outline=gold_lo)
    glyph(d, DAI, 66, 47, gold_hi, 2); glyph(d, BUTSU, 81, 47, gold_hi, 2)
    d.rectangle([62, 61, 97, 62], fill=gold_lo)
    # bronze lanterns under the eave
    for x in (36, 120):
        d.line([(x + 2, 60), (x + 2, 64)], fill=SOOT)
        d.rectangle([x, 65, x + 4, 72], fill=BRONZE); d.line([(x, 65), (x, 72)], fill=BRONZE_HI)
        d.rectangle([x + 1, 67, x + 3, 70], fill=WARM); d.rectangle([x - 1, 64, x + 5, 64], fill=BRONZE_LO)
        d.point((x + 2, 73), fill=BRONZE_LO)
    # ---- the stone base and the steps, an incense urn ----------------------------------------
    d.rectangle([4, 110, 155, 122], fill=GRAN); d.line([(4, 110), (155, 110)], fill=GRAN_HI)
    d.rectangle([4, 119, 155, 122], fill=GRAN_LO)
    for x in range(4, 156, 19):
        d.line([(x, 111), (x, 118)], fill=GRAN_LO)
    for k in range(4):
        y = 110 + k * 4
        d.rectangle([56 - k * 2, y, 103 + k * 2, y + 3], fill=GRAN_HI if k % 2 == 0 else GRAN)
        d.line([(56 - k * 2, y + 3), (103 + k * 2, y + 3)], fill=GRAN_LO)
    d.rectangle([20, 104, 32, 108], fill=BRONZE_LO); d.rectangle([18, 100, 34, 104], fill=BRONZE)
    d.line([(18, 100), (34, 100)], fill=BRONZE_HI); d.rectangle([22, 108, 23, 112], fill=BRONZE_LO)
    d.rectangle([29, 108, 30, 112], fill=BRONZE_LO); d.rectangle([20, 99, 32, 99], fill=rgb('d8d2c8'))
    outline(im)
    puff(im, 26, 94, 3, a=120); puff(im, 29, 88, 3, a=80); puff(im, 25, 82, 2, a=50)
    return im


def mushiko(d, x0, y0, x1, y1):
    """A mushiko-mado: slits cut in an upstairs plaster wall."""
    d.rectangle([x0, y0, x1, y1], fill=PLASTER_LO)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=PLASTER)
    for x in range(x0 + 3, x1 - 1, 4):
        d.rectangle([x, y0 + 2, x + 1, y1 - 2], fill=rgb('4a4450'))
        d.point((x, y0 + 2), fill=rgb('2a2630'))


def kenjo(d, x0, y0, x1, y1, ground, mark, fine):
    """Hakata-ori's kenjo pattern: bands of small motifs between stripes."""
    d.rectangle([x0, y0, x1, y1], fill=ground)
    for x in range(x0, x1 + 1):
        u = (x - x0) % 8
        if u in (0, 7):
            d.line([(x, y0), (x, y1)], fill=fine)
        elif u == 3 or u == 4:
            for y in range(y0, y1 + 1):
                if (y - y0) % 4 in ((0, 1) if u == 3 else (2, 3)):
                    d.point((x, y), fill=mark)


def cedar_lattice(d, x0, y0, x1, y1, lit=False):
    back = LIT if lit else rgb('4a3a34')
    d.rectangle([x0, y0, x1, y1], fill=back)
    for x in range(x0, x1 + 1, 2):
        d.line([(x, y0), (x, y1)], fill=CEDAR if (x // 2) % 4 else CEDAR_HI)
    d.line([(x0, y0), (x1, y0)], fill=CEDAR_LO); d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=CEDAR_LO)
    d.line([(x0, y1), (x1, y1)], fill=CEDAR_DK)


def ori_shop():
    """A Hakata-ori merchant's front: silver-grey tile, white plaster with
    mushiko slits upstairs, unpainted cedar lattice below, bolts of obi cloth."""
    im, d = canvas(4, 4)                 # 128 x 128
    roof(d, 12, 34, (10, 117), (2, 125), pal=IBUSHI_P, p=1.0)
    d.rectangle([6, 38, 121, 62], fill=PLASTER); d.rectangle([104, 38, 121, 62], fill=PLASTER_LO)
    d.rectangle([6, 38, 121, 40], fill=PLASTER_SH)
    mushiko(d, 12, 44, 44, 58); mushiko(d, 84, 44, 116, 58)
    # the shop board: cedar, the name in indigo kana
    bar(d, 48, 42, 80, 60, CEDAR_HI, WHITE, CEDAR_LO)
    d.rectangle([48, 42, 80, 60], outline=CEDAR_DK)
    kana(d, ['ha', 'ka', 'ta'], 53, 44, INDIGO); kana(d, ['o', 'ri'], 57, 52, XRED_LO)
    # the pent roof
    light, dark, hi, deep = IBUSHI_P
    for y in range(62, 74):
        e = y - 62
        for x in range(4 - e // 2, 124 + e // 2):
            c = dark if e % 4 == 3 or (x + (e // 4) * 3) % 6 == 0 else (light if x < 86 else dark)
            d.point((x, y), fill=c)
        d.point((4 - e // 2, y), fill=hi)
    d.rectangle([0, 74, 127, 75], fill=dark); d.line([(0, 76), (127, 76)], fill=deep)
    for x in range(2, 127, 4):
        d.point((x, 75), fill=hi)
    # ---- the ground floor ------------------------------------------------------------------
    d.rectangle([6, 77, 121, 122], fill=CEDAR_DK)
    timber_posts(d, (6, 60, 92, 118), 77, 122, (CEDAR, CEDAR_HI, CEDAR_LO, CEDAR_DK))
    # the show window (cells 0-1): bolts of obi in kenjo stripes, one unrolled
    d.rectangle([11, 80, 58, 112], fill=rgb('4a3a34'))
    d.rectangle([12, 81, 57, 111], fill=WARM); d.line([(12, 81), (57, 81)], fill=WHITE)
    obis = ((INDIGO, WHITE, INDIGO_HI), (rgb('8a2a3a'), rgb('f0d98c'), rgb('b04a54')), (rgb('f3ead2'), rgb('8a2a3a'), rgb('cdbfa6')),
            (rgb('3f7350'), rgb('f3ead2'), rgb('5f9a62')), (rgb('d9a23a'), rgb('5a3a2a'), rgb('f0c860')), (rgb('5a3a6a'), rgb('f0d98c'), rgb('7c5a8c')))
    for i, (g, m, f) in enumerate(obis):
        x = 14 + i * 7
        kenjo(d, x, 84 + (i % 2) * 2, x + 5, 106, g, m, f)
        d.rectangle([x, 106, x + 5, 108], fill=CEDAR_LO)
    kenjo(d, 12, 104, 57, 110, rgb('f3ead2'), INDIGO, rgb('8a2a3a'))
    d.rectangle([10, 113, 59, 122], fill=CEDAR); d.line([(10, 113), (59, 113)], fill=CEDAR_HI)
    for x in range(12, 59, 3):
        d.line([(x, 115), (x, 121)], fill=CEDAR_LO)
    # the door (cell 2): a long indigo noren with the kenjo band
    d.rectangle([64, 79, 91, 122], fill=rgb('3a2c2a'))
    cedar_lattice(d, 65, 98, 77, 121, True); cedar_lattice(d, 79, 98, 90, 121, True)
    noren(d, 64, 80, 91, 100, INDIGO, INDIGO_HI, INDIGO_LO, 4)
    for x in range(65, 91, 2):
        d.point((x, 95), fill=WHITE); d.point((x + 1, 97), fill=rgb('a8b8d8'))
    d.line([(65, 93), (90, 93)], fill=rgb('a8b8d8'))
    d.ellipse([74, 83, 81, 90], outline=WHITE); d.line([(76, 86), (79, 86)], fill=WHITE); d.line([(77, 85), (77, 88)], fill=WHITE)
    # cell 3: cedar lattice, a tub of thread spools, an upright board
    cedar_lattice(d, 97, 80, 116, 108)
    d.rectangle([96, 109, 117, 122], fill=CEDAR); d.line([(96, 109), (117, 109)], fill=CEDAR_HI)
    for i, x in enumerate((98, 104, 110)):
        d.rectangle([x, 112, x + 4, 119], fill=(XRED, INDIGO_HI, rgb('d9a23a'))[i])
        d.line([(x, 112), (x + 4, 112)], fill=WHITE); d.line([(x, 119), (x + 4, 119)], fill=CEDAR_DK)
    footing(d, 4, 123, 122, 4)
    outline(im)
    return im


def cracker(d, x, y, r=3, nori=True):
    d.ellipse([x - r, y - r, x + r, y + r], fill=rgb('d9a868'))
    d.arc([x - r, y - r, x + r, y + r], 150, 300, fill=rgb('f0cc94'))
    d.arc([x - r, y - r, x + r, y + r], 330, 120, fill=rgb('a8743c'))
    d.point((x - 1, y - 1), fill=rgb('8a5a2c')); d.point((x + 1, y + 1), fill=rgb('8a5a2c'))
    if nori:
        d.line([(x - r + 1, y), (x + r - 1, y)], fill=rgb('2a3a30'))


def senbei_shop():
    """A rice-cracker shop: dark slatted timber upstairs with a great cracker
    for a sign, the toasting griddle open to the street."""
    im, d = canvas(3, 4)                 # 96 x 128
    roof(d, 12, 32, (10, 85), (2, 93), pal=IBUSHI_P, p=1.0, caps=False)
    d.rectangle([5, 36, 90, 64], fill=DWOOD_LO)
    for x in range(5, 91):
        k = (x - 5) % 3
        d.line([(x, 38), (x, 63)], fill=DWOOD_HI if k == 0 else (DWOOD if k == 1 else DWOOD_DK))
    d.rectangle([5, 36, 90, 38], fill=DWOOD_DK)
    d.rectangle([84, 38, 90, 64], fill=DWOOD_DK)
    # the sign: a cracker a yard across, glazed, with its strip of nori
    d.ellipse([33, 37, 61, 65], fill=rgb('d9a868'))
    d.ellipse([33, 37, 58, 62], fill=rgb('e8bd80')); d.ellipse([37, 41, 61, 65], fill=rgb('d9a868'))
    d.arc([33, 37, 61, 65], 320, 130, fill=rgb('a8743c'), width=2)
    for i in range(16):
        x, y = 38 + h3(i, 2, 5) % 19, 42 + h3(i, 7, 6) % 19
        d.point((x, y), fill=rgb('a8743c') if i % 2 else rgb('f6dca8'))
    d.rectangle([33, 47, 61, 55], fill=rgb('2a3a30')); d.line([(33, 47), (61, 47)], fill=rgb('4a5e4c'))
    kana(d, ['se', 'n'], 37, 48, WHITE); d.point((52, 51), fill=rgb('2a3a30'))
    # upright boards either side: se-n / be-i
    for x0, names in ((11, ['se', 'n']), (70, ['be', 'i'])):
        bar(d, x0, 40, x0 + 12, 62, PAPER, WHITE, PAPER_LO)
        d.rectangle([x0, 40, x0 + 12, 62], outline=DWOOD_DK)
        kana(d, names, x0 + 3, 43, rgb('8a3a2c'), 1, True)
    light, dark, hi, deep = IBUSHI_P
    for y in range(64, 75):
        e = y - 64
        for x in range(3 - e // 2, 93 + e // 2):
            c = dark if e % 4 == 3 or (x + (e // 4) * 3) % 6 == 0 else (light if x < 64 else dark)
            d.point((x, y), fill=c)
    d.rectangle([0, 75, 95, 76], fill=dark); d.line([(0, 77), (95, 77)], fill=deep)
    for x in range(2, 95, 4):
        d.point((x, 76), fill=hi)
    # ---- the open front (cells 0-1): the griddle, jars, the keeper ---------------------------
    d.rectangle([5, 78, 90, 122], fill=DWOOD_DK)
    timber_posts(d, (5, 58, 87), 78, 122)
    d.rectangle([9, 80, 57, 104], fill=rgb('40282a')); d.rectangle([9, 80, 57, 82], fill=WARM)
    person(d, 12, 84, rgb('3a4a6a'), WHITE, None)
    for i, x in enumerate((28, 38, 48)):                          # glass jars of crackers on the back shelf
        d.rectangle([x, 85, x + 7, 96], fill=rgb('cfe4ee')); d.rectangle([x, 85, x + 7, 96], outline=rgb('8fa8b8'))
        d.rectangle([x + 1, 84, x + 6, 85], fill=(XRED, rgb('3f7350'), rgb('d9a23a'))[i])
        cracker(d, x + 3, 90, 2, False); cracker(d, x + 4, 94, 2, i % 2 == 0)
    d.line([(26, 97), (57, 97)], fill=CEDAR_LO)
    # the charcoal griddle on the counter
    d.rectangle([9, 104, 57, 108], fill=CEDAR); d.line([(9, 104), (57, 104)], fill=CEDAR_HI)
    d.rectangle([22, 99, 54, 104], fill=SOOT); d.line([(22, 99), (54, 99)], fill=STONE_DK)
    for x in range(23, 54, 2):
        d.point((x, 103), fill=rgb('f0903a') if (x // 2) % 3 else rgb('d9482e'))
    for x in (26, 34, 42, 50):
        cracker(d, x, 99, 3)
    d.rectangle([9, 109, 57, 122], fill=DWOOD)
    for x in range(11, 57, 4):
        d.line([(x, 110), (x, 121)], fill=DWOOD_LO)
    bar(d, 14, 111, 34, 120, PAPER, WHITE, PAPER_LO)              # a paper price list
    for y in (113, 116, 118):
        d.line([(16, y), (31, y)], fill=CREAM_DK)
    # the door (cell 2): a persimmon noren over cedar doors
    d.rectangle([63, 80, 86, 122], fill=rgb('3a2c2a'))
    cedar_lattice(d, 64, 96, 74, 121, True); cedar_lattice(d, 76, 96, 85, 121, True)
    noren(d, 63, 81, 86, 97, rgb('c9703a'), rgb('e89458'), rgb('964a28'), 3)
    cracker(d, 74, 89, 4)
    footing(d, 3, 92, 122, 4)
    outline(im)
    puff(im, 30, 94, 2, a=80); puff(im, 44, 93, 3, a=70)
    return im


# ---- the Hakata-bei wall ---------------------------------------------------------------
BEI_TILE, BEI_TILE_HI, BEI_TILE_LO = rgb('59606e'), rgb('868e9c'), rgb('383d4a')
BEI_STONES = (rgb('9aa0a8'), rgb('b8b2a4'), rgb('8a8e98'), rgb('a89a8c'), rgb('7c8490'))
# one 32px period of the wall's courses: (kind, [(x, length), ...]); tiles are 2px slivers, stones 4px lumps
BEI_COURSES = (
    ('tile', ((0, 9), (11, 7), (20, 10))),
    ('stone', ((1, 5), (8, 6), (16, 4), (22, 7))),
    ('tile', ((3, 8), (13, 9), (24, 7))),
    ('tile', ((0, 6), (8, 10), (20, 5), (27, 4))),
    ('stone', ((0, 4), (6, 7), (15, 5), (22, 4), (28, 3))),
    ('tile', ((2, 10), (14, 7), (23, 8))),
)


def bei_face(d, x0, x1, y0, y1, seed=0):
    """Hakata-bei: fire-salvaged stones and broken roof tiles set in courses
    in ochre clay (period 32 in x, so a run joins)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = h3(x % 32, y, 12 + seed)
            d.point((x, y), fill=CLAY_HI if k < 16 else (CLAY_LO if k > 226 else CLAY))
    y = y0 + 1
    i = seed
    while y < y1 - 1:
        kind, segs = BEI_COURSES[i % len(BEI_COURSES)]
        h = 2 if kind == 'tile' else 4
        if y + h > y1:
            break
        for sx, ln in segs:
            for x in range(x0, x1 + 1):
                u = (x - sx - i * 5) % 32
                if u < ln:
                    if kind == 'tile':
                        d.point((x, y), fill=BEI_TILE_HI if u < ln - 1 else BEI_TILE)
                        d.point((x, y + 1), fill=BEI_TILE if u else BEI_TILE_LO)
                        if u == ln - 1:
                            d.point((x, y + 1), fill=BEI_TILE_LO)
                    else:
                        c = BEI_STONES[(sx + i) % 5]
                        for yy in range(h):
                            if (u in (0, ln - 1)) and yy in (0, h - 1):
                                continue                          # rounded corners
                            cc = c
                            if yy == 0:
                                cc = tuple(min(255, v + 26) for v in c[:3]) + (255,)
                            elif yy == h - 1 or u == ln - 1:
                                cc = tuple(max(0, v - 34) for v in c[:3]) + (255,)
                            d.point((x, y + yy), fill=cc)
        d.line([(x0, y + h), (x1, y + h)], fill=CLAY_LO) if kind == 'tile' else None
        y += h + (2 if kind == 'tile' else 2)
        i += 1


def bei_cap_h(d, x0, x1, y):
    """The wall's little tiled roof, seen from the front: 8px deep from y."""
    light, dark, hi, deep = IBUSHI_P
    d.rectangle([x0, y, x1, y + 1], fill=dark); d.line([(x0, y), (x1, y)], fill=hi)          # the ridge
    for yy in range(y + 2, y + 6):
        for x in range(x0, x1 + 1):
            d.point((x, yy), fill=dark if (x % 4 == 3) else (light if yy < y + 4 else rgb('6c717b')))
    for x in range(x0, x1 + 1):                                   # round eave-tile ends
        d.point((x, y + 6), fill=hi if x % 4 == 1 else (dark if x % 4 == 3 else light))
    d.line([(x0, y + 7), (x1, y + 7)], fill=deep)


def hakata_bei(kind):
    """One piece of the Hakata-bei wall. `h` (1x2) runs east-west. The rest
    are 1x3 as Sendai's fence pieces are, because a wall running north-south
    is seen end-on: `v` is a length of its tiled cap from above, `end` the same
    with the wall's south end under it, `corner-e` / `corner-w` end an
    east-west run where the wall turns north."""
    light, dark, hi, deep = IBUSHI_P
    tall = kind in ('v', 'top', 'end', 'corner-e', 'corner-w')
    im, d = canvas(1, 3 if tall else 2)
    oy = 32 if tall else 0

    def face(x0, x1, seed=0):
        bei_face(d, x0, x1, oy + 24, oy + 55, seed)
        d.line([(x0, oy + 24), (x1, oy + 24)], fill=CLAY_DK)      # the cap's shadow
        d.line([(x0, oy + 25), (x1, oy + 25)], fill=CLAY_LO)
        d.rectangle([x0, oy + 56, x1, oy + 63], fill=GRAN)         # a footing of field stones
        for x in range(x0, x1 + 1):
            u = (x + 3) % 11
            d.point((x, oy + 56), fill=GRAN_HI)
            if u == 0:
                d.line([(x, oy + 57), (x, oy + 63)], fill=GRAN_DK)
            d.point((x, oy + 63), fill=GRAN_DK)
            if h3(x % 32, 3, 9) < 60:
                d.point((x, oy + 59 + x % 3), fill=GRAN_LO)

    # a north-south run seen from the south and a little west: a sliver of its west face (clay,
    # tile slivers, stones), then the cap from above - its west slope, the ridge, its east slope
    STRIP = ((9, hi), (10, light), (11, light), (12, light), (13, hi), (14, dark), (15, dark), (16, light),
             (17, rgb('6c717b')), (18, rgb('6c717b')), (19, dark), (20, deep), (21, deep))

    def cap_v(y0, y1, face_to=None):
        for y in range(y0, y1 + 1):
            for x, c in STRIP:
                d.point((x, y), fill=c)
            if y % 4 == 3:                                        # the tile laps
                for x in (10, 11, 12, 16, 17, 18):
                    d.point((x, y), fill=dark)
            if y % 4 == 0:
                d.point((9, y), fill=WHITE); d.point((19, y), fill=light)
        for y in range(y0 + 2, (face_to or y1) + 1):              # the west face, foreshortened to 3px
            v = y % 12
            for x in (6, 7, 8):
                c = CLAY_HI if x == 6 else CLAY
                if v in (1, 2, 7, 8) and (x + y // 6) % 4 != 3:
                    c = BEI_TILE_HI if v in (1, 7) else BEI_TILE      # a course of tile slivers
                elif v in (4, 5) and x != 6:
                    c = BEI_STONES[(y // 12 + x) % 5]             # a course of stones
                elif v == 10:
                    c = CLAY_LO
                d.point((x, y), fill=c)

    def end_tile(y):
        """The ridge's end tile where a run stops: a round boss."""
        d.rectangle([12, y, 16, y + 2], fill=dark); d.line([(12, y), (16, y)], fill=hi)
        d.point((14, y + 1), fill=WHITE)

    if kind == 'h':
        bei_cap_h(d, 0, 31, oy + 16); face(0, 31)
    elif kind in ('stop-e', 'stop-w'):                            # an east-west run's free end (a gateway)
        east = kind == 'stop-e'
        bei_cap_h(d, 0 if east else 5, 26 if east else 31, oy + 16)
        fx0, fx1 = (0, 23) if east else (8, 31)
        face(fx0, fx1, 1)
        for x, c in ((fx1 if east else fx0, CLAY_DK if east else CLAY_HI),):
            d.line([(x, oy + 26), (x, oy + 55)], fill=c)
        if east:
            d.line([(fx1 - 1, oy + 26), (fx1 - 1, oy + 55)], fill=CLAY_LO)
    elif kind == 'v':
        cap_v(17, 48)
    elif kind == 'top':                                           # the north end of a run: closed, an end tile
        cap_v(19, 48)
        d.rectangle([9, 19, 21, 20], fill=dark); d.line([(9, 19), (21, 19)], fill=hi)
        end_tile(19)
    elif kind == 'end':
        cap_v(17, 47, face_to=47)
        bei_cap_h(d, 6, 21, 48)
        bei_face(d, 9, 19, 56, 87, 2)
        for y in range(56, 88):                                   # the west face comes down beside the end
            for x in (6, 7, 8):
                d.point((x, y), fill=im.getpixel((x, 20 + (y - 56) % 24)))
        d.line([(6, 56), (19, 56)], fill=CLAY_DK)
        d.line([(9, 57), (9, 87)], fill=CLAY_HI); d.line([(19, 56), (19, 87)], fill=CLAY_DK)
        d.rectangle([5, 88, 20, 95], fill=GRAN); d.line([(5, 88), (20, 88)], fill=GRAN_HI)
        d.line([(5, 95), (20, 95)], fill=GRAN_DK); d.line([(14, 89), (14, 94)], fill=GRAN_DK)
        d.line([(9, 89), (9, 94)], fill=GRAN_LO)
    else:
        # a corner: the east-west run's cap and the north-south run's cap are ONE roof, the same
        # 13px wide and flush at the outside edge, mitred where they meet
        east = kind == 'corner-e'
        cap_v(17, 47)
        fx0, fx1 = (0, 19) if east else (9, 31)
        face(fx0, fx1, 1)
        bei_cap_h(d, 0 if east else 9, 21 if east else 31, oy + 16)
        if not east:                                              # the west face turns the corner: its sliver runs down
            for y in range(oy + 16, oy + 56):
                for x in (6, 7, 8):
                    d.point((x, y), fill=im.getpixel((x, 20 + (y - 48) % 24)))
            d.rectangle([5, oy + 56, 8, oy + 63], fill=GRAN); d.point((5, oy + 56), fill=GRAN_HI)
            d.line([(5, oy + 63), (8, oy + 63)], fill=GRAN_DK)
        edge = fx1 if east else fx0                               # the wall's corner: a clay arris
        d.line([(edge, oy + 24), (edge, oy + 55)], fill=CLAY_DK if east else CLAY_HI)
        for k in range(8):                                        # the mitre across the roof
            x = (21 - 13 + k * 13 // 8 + 1) if east else (21 - k * 13 // 8)
            d.point((x, oy + 16 + k), fill=deep)
            d.point((x + (1 if east else -1), oy + 16 + k), fill=hi)
    outline(im)
    if tall:                                                      # no ink across a run: pieces stack seamlessly
        px = im.load()
        for x in range(32):
            if kind != 'top':
                px[x, 16] = CLEAR
            if kind in ('v', 'top'):
                px[x, 49] = CLEAR
    return im

# ==============================================================================
# Momochi
# ==============================================================================
def surfboard(d, x, y0, y1, c, hi, stripe):
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        half = round(3.4 * math.sin(math.pi * min(1.0, 0.12 + t * 0.88) ** 0.7)) if t < 0.9 else 2
        d.line([(x - half, y), (x + half, y)], fill=c)
        d.point((x - half, y), fill=hi)
    d.line([(x, y0 + 3), (x, y1 - 2)], fill=stripe)


def beach_house():
    """A seaside cafe: white boards and teal trim, a striped awning over a deck."""
    im, d = canvas(4, 3)                 # 128 x 96
    # the roof: faded teal corrugated sheet, a board on it
    for y in range(12, 28):
        e = y - 12
        for x in range(8 - e // 2, 120 + e // 2):
            c = TEAL_LO if x % 4 == 3 else (TEAL_HI if x % 4 == 0 and x < 70 else TEAL)
            if h3(x // 4, y // 3, 3) < 22:
                c = rgb('b8704a')                                 # rust
            d.point((x, y), fill=c)
    d.rectangle([0, 28, 127, 29], fill=TEAL_LO); d.line([(0, 30), (127, 30)], fill=rgb('1f5a6c'))
    d.rectangle([6, 9, 121, 12], fill=TEAL_LO); d.line([(6, 9), (121, 9)], fill=TEAL_HI)
    for x in (30, 96):
        d.line([(x, 6), (x, 12)], fill=WOOD_DK)
    bar(d, 24, 0, 103, 11, rgb('fff8ee'), WHITE, PAPER_LO)
    d.rectangle([24, 0, 103, 11], outline=TEAL_LO)
    text(d, 'BEACH', 29, 2, TEAL_LO); text(d, 'CAFE', 66, 2, rgb('e0603c'))
    d.ellipse([92, 2, 99, 9], fill=rgb('ffd84a')); d.point((94, 4), fill=WHITE)             # a sun
    # the wall: white weatherboard
    for y in range(31, 86):
        for x in range(6, 122):
            d.point((x, y), fill=rgb('d9dde2') if (y - 31) % 5 == 4 else (WHITE if x < 90 else rgb('eef1f4')))
    d.rectangle([116, 31, 121, 86], fill=rgb('d9dde2'))
    timber_posts(d, (6, 62, 92, 118), 31, 86, (TEAL, TEAL_HI, TEAL_LO, TEAL_LO))
    # the awning over the hatch: yellow and white
    for x in range(4, 62):
        s = ((x - 4) // 6) % 2
        for y in range(34, 46):
            d.point((x, y), fill=(rgb('e0a82c') if y > 43 else rgb('ffd24a')) if s else (PAPER_LO if y > 43 else WHITE))
        if (x - 4) % 6 in (1, 2, 3, 4):
            d.point((x, 46), fill=rgb('ffd24a') if s else WHITE)
    # the serving hatch (cells 0-1): shaved ice, bottles, the keeper
    d.rectangle([10, 48, 58, 70], fill=TEAL_LO)
    d.rectangle([11, 49, 57, 69], fill=rgb('c8ecf0')); d.rectangle([11, 49, 57, 51], fill=WHITE)
    person(d, 16, 51, rgb('ffd24a'), rgb('e0603c'), None)
    for i, x in enumerate((32, 40, 48)):                          # cups of shaved ice in three syrups
        d.polygon([(x, 62), (x + 6, 62), (x + 5, 68), (x + 1, 68)], fill=WHITE)
        d.ellipse([x - 1, 56, x + 7, 63], fill=(rgb('f07a8a'), rgb('7fd08a'), rgb('6fb4f0'))[i])
        d.ellipse([x, 56, x + 4, 59], fill=WHITE)
    d.rectangle([8, 70, 60, 73], fill=CEDAR_HI); d.line([(8, 73), (60, 73)], fill=CEDAR_LO)
    bar(d, 14, 76, 34, 84, rgb('2b2a30'), None, None); d.rectangle([14, 76, 34, 84], outline=CEDAR)   # a chalk menu
    d.line([(16, 78), (30, 78)], fill=rgb('f3ead2')); d.line([(16, 81), (26, 81)], fill=rgb('ffd84a'))
    d.ellipse([42, 75, 52, 85], fill=XRED); d.ellipse([45, 78, 49, 82], fill=WHITE)         # a life ring
    for a in range(4):
        d.point((47 + (-4, 0, 4, 0)[a], 80 + (0, -4, 0, 4)[a]), fill=WHITE)
    # the door (cell 2): a glass door, a string of bulbs over it
    d.rectangle([67, 40, 90, 86], fill=TEAL_LO)
    d.rectangle([68, 41, 89, 86], fill=GLASS); d.line([(68, 42), (89, 42)], fill=GLASS_HI)
    d.line([(79, 41), (79, 86)], fill=TEAL_LO); d.line([(70, 46), (70, 80)], fill=GLASS_HI)
    d.point((77, 64), fill=WHITE); d.point((81, 64), fill=WHITE)
    bulbs(d, [(x, 36 + round(2 * math.sin((x - 64) * math.pi / 14))) for x in range(64, 94, 3)], GOLD_BULBS)
    # cell 3: a window with shutters, surfboards leaning
    d.rectangle([97, 42, 114, 58], fill=TEAL_LO); d.rectangle([98, 43, 113, 57], fill=GLASS)
    d.line([(98, 43), (113, 43)], fill=GLASS_HI); d.line([(105, 43), (105, 57)], fill=TEAL_LO)
    surfboard(d, 100, 52, 86, rgb('f08a3c'), rgb('ffb870'), WHITE)
    surfboard(d, 109, 48, 86, rgb('f3ead2'), WHITE, TEAL)
    # the deck
    d.rectangle([2, 86, 125, 92], fill=CEDAR)
    for x in range(2, 126):
        if x % 8 == 7:
            d.line([(x, 87), (x, 91)], fill=CEDAR_LO)
    d.line([(2, 86), (125, 86)], fill=CEDAR_HI); d.line([(2, 92), (125, 92)], fill=CEDAR_DK)
    outline(im)
    return im


def umbrella(variant):
    """A beach parasol: `a` red and white over a lounger, `b` blue and yellow
    over a towel and a ball."""
    im, d = canvas(2, 2)                 # 64 x 64
    c1, c1_hi, c1_lo, c2, c2_lo = ((XRED, XRED_HI, XRED_LO, WHITE, rgb('d9dde2')) if variant == 'a' else
                                   (rgb('3f7fd0'), rgb('6fa8f0'), rgb('2a5a9c'), rgb('ffd84a'), rgb('d9a82c')))
    # what lies under it
    if variant == 'a':
        d.polygon([(22, 50), (58, 44), (60, 48), (24, 55)], fill=WHITE)            # the lounger
        d.polygon([(22, 50), (34, 48), (36, 52), (24, 55)], fill=rgb('6fd0d8'))
        d.line([(22, 50), (58, 44)], fill=WHITE); d.line([(24, 55), (60, 48)], fill=rgb('aab4c0'))
        d.polygon([(50, 45), (58, 44), (62, 36), (55, 38)], fill=rgb('eef1f4'))
        for x in range(36, 56, 5):
            d.line([(x, 48), (x + 1, 52)], fill=rgb('6fd0d8'))
        d.line([(26, 55), (26, 59)], fill=rgb('8a94a0')); d.line([(56, 49), (56, 54)], fill=rgb('8a94a0'))
    else:
        d.polygon([(26, 50), (56, 46), (60, 54), (30, 59)], fill=rgb('f08a3c'))    # a towel
        for k in range(4):
            d.line([(30 + k * 7, 50 - k), (34 + k * 7, 58 - k)], fill=WHITE)
        d.ellipse([44, 40, 55, 51], fill=WHITE); d.pieslice([44, 40, 55, 51], 200, 320, fill=XRED)   # a beach ball
        d.pieslice([44, 40, 55, 51], 20, 120, fill=rgb('3f7fd0')); d.point((47, 43), fill=WHITE)
    # the pole, leaning a little
    d.line([(26, 14), (22, 58)], fill=rgb('f3ead2'), width=2); d.line([(27, 14), (23, 58)], fill=rgb('b4aea6'))
    # the canopy: eight gores, a scalloped edge
    cx, cy, rx, ry = 27, 20, 25, 15
    for y in range(cy - ry, cy + 6):
        for x in range(cx - rx, cx + rx + 1):
            ny = (y - cy) / ry
            if ny > 0.38:
                continue
            lim = math.sqrt(max(0.0, 1 - min(1.0, ny * ny if ny < 0 else 0))) * rx
            if ny >= 0:
                lim = rx
            if abs(x - cx) > lim:
                continue
            u = (x - cx) / max(1.0, lim)
            g = int((math.asin(max(-1, min(1, u))) / math.pi + 0.5) * 7.999)
            scallop = ny > 0.2 and ((x - cx + rx) % 7 in (0, 6)) and ny > 0.28
            if scallop:
                continue
            if g % 2 == 0:
                c = c1_hi if u < -0.5 and ny < -0.3 else (c1_lo if u > 0.45 or ny > 0.15 else c1)
            else:
                c = c2_lo if u > 0.45 or ny > 0.15 else c2
            d.point((x, y), fill=c)
    for x in range(cx - rx, cx + rx + 1):                         # a scalloped valance along the lower edge
        k = (x - cx + rx) % 7
        top = im.getpixel((x, cy + 5))
        if top[3] and k in (1, 2, 3, 4, 5):
            d.point((x, cy + 6), fill=top)
            if k in (2, 3, 4):
                d.point((x, cy + 7), fill=c1_lo if top[:3] in (c1[:3], c1_lo[:3], c1_hi[:3]) else c2_lo)
    d.rectangle([cx - 1, cy - ry - 3, cx, cy - ry], fill=rgb('f3ead2'))
    outline(im)
    return grounded(im, ellipses=[(4, 50, 60, 63)], a=60)


def lifeguard_chair():
    im, d = canvas(2, 3)                 # 64 x 96
    wh, wh_lo, wh_dk = rgb('f6f6f2'), rgb('c8ccd0'), rgb('8f97a3')
    # the legs: a splayed frame, cross braces, a ladder up the west side
    for (xa, ya, xb, yb) in ((22, 44, 12, 92), (42, 44, 52, 92)):
        d.line([(xa, ya), (xb, yb)], fill=wh, width=3); d.line([(xa + 2, ya), (xb + 2, yb)], fill=wh_lo)
    d.line([(26, 44), (22, 92)], fill=wh_lo, width=2); d.line([(38, 44), (44, 92)], fill=wh_dk, width=2)
    d.line([(17, 68), (48, 68)], fill=wh, width=2); d.line([(14, 84), (51, 84)], fill=wh, width=2)
    d.line([(18, 68), (49, 84)], fill=wh_lo); d.line([(47, 68), (16, 84)], fill=wh_lo)
    for y in range(50, 92, 7):
        t = (y - 44) / 48
        d.line([(round(22 - 10 * t), y), (round(26 - 4 * t), y)], fill=wh_dk)
    # the seat and its back, a red rail
    d.rectangle([18, 40, 46, 44], fill=wh); d.line([(18, 40), (46, 40)], fill=WHITE); d.line([(18, 44), (46, 44)], fill=wh_dk)
    d.rectangle([20, 24, 44, 40], fill=wh_lo)
    for x in range(20, 45, 5):
        d.rectangle([x, 24, x + 3, 40], fill=wh); d.line([(x + 3, 24), (x + 3, 40)], fill=wh_dk)
    d.rectangle([18, 30, 20, 44], fill=XRED); d.rectangle([44, 30, 46, 44], fill=XRED_LO)
    d.line([(18, 30), (26, 34)], fill=XRED)
    # the little roof: red and yellow
    for y in range(8, 20):
        e = y - 8
        for x in range(18 - e, 46 + e + 1):
            s = ((x + 40) // 7) % 2
            d.point((x, y), fill=(XRED if y < 17 else XRED_LO) if s else (rgb('ffd84a') if y < 17 else rgb('d9a82c')))
    d.line([(12, 20), (52, 20)], fill=wh_dk)
    d.line([(22, 20), (22, 24)], fill=wh_dk); d.line([(42, 20), (42, 24)], fill=wh_dk)
    # a flag, a rescue float
    d.line([(46, 0), (46, 9)], fill=wh_dk)
    d.polygon([(47, 0), (58, 0), (58, 6), (47, 6)], fill=XRED); d.polygon([(47, 3), (58, 3), (58, 6), (47, 6)], fill=rgb('ffd84a'))
    d.rectangle([48, 46, 53, 62], fill=rgb('f0603c')); d.line([(48, 46), (48, 62)], fill=rgb('ff8a64'))
    d.rectangle([49, 44, 52, 45], fill=rgb('f0603c')); d.rectangle([49, 63, 52, 64], fill=rgb('f0603c'))
    d.line([(50, 50), (50, 58)], fill=WHITE)
    outline(im)
    return grounded(im, ellipses=[(6, 86, 58, 95)], a=60)


def sand_tex(x, y):
    """Dry sand: wind ripples, a few shells and pebbles (period 32)."""
    r = (y + round(2.2 * math.sin(x * math.pi / 16) + 1.2 * math.sin(x * math.pi / 8 + 1))) % 8
    k = h3(x, y, 23)
    if (x, y) in ((7, 5), (8, 5), (22, 19), (23, 19), (23, 20)):
        return rgb('fbf4e4')                                      # shells
    if (x, y) in ((8, 6), (24, 20), (15, 27)):
        return rgb('c9a888')
    if r == 0:
        return SAND_HI if k > 40 else SAND
    if r == 1:
        return SAND_LO if k > 90 else SAND
    return rgb('e4cf9e') if k < 14 else (SAND_HI if k > 244 else SAND)


def sand_kerb(m, along):
    """A low promenade lip of pale concrete, sand blown over it."""
    if m == 0:
        return rgb('d9d4c8') if along % 16 != 15 else rgb('b4aea0')
    if m == 1:
        return rgb('bdb6a6') if h3(along, 1, 5) > 60 else SAND
    return SAND_LO if h3(along, 2, 6) > 120 else SAND


def _wave(t, amp=2.2):
    """The waterline's wobble along the shore: period 32 and zero at a cell's
    edges and its middle, so every piece meets every other."""
    return amp * math.sin(t * math.pi / 16) + amp * 0.45 * math.sin(t * math.pi / 8)


SHORE_SHAPES = ('e', 'w', 'n', 's', 'outer-ne', 'outer-nw', 'outer-se', 'outer-sw',
                'inner-ne', 'inner-nw', 'inner-se', 'inner-sw')
DEEPS = (SEA, rgb('4a6fb6'), rgb('5584c2'), SEA_SH, rgb('74aed6'), rgb('8cc4e0'), rgb('a8d4e6'))


def surf(kind, shape):
    """The beach meeting the sea, one cell. Every pixel is coloured by its
    distance d from the waterline (d > 0 up the beach, d < 0 out to sea), so
    nothing is rotated and the sand's grain and the light stay the same in
    every piece: `wet` holds d 0..32 (the swash, the foam line, a narrow band
    of wet sand, dry sand), `shallows` d -32..0 (ankle-deep water deepening to
    the sea's own blue).
    shape: e / w / n / s is the side the LAND is on; outer-XX is a point of
    land toward XX (sea on the two opposite sides); inner-XX is a cove's
    corner, land on all sides but the diagonal opposite XX."""
    tail = shape.split('-')[-1]
    off = 32 if kind == 'shallows' else 0
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    for y in range(32):
        for x in range(32):
            d1 = d2 = None
            if 'e' in tail or 'w' in tail:
                d1 = (x if 'e' in tail else 31 - x) - off - _wave(y)
            if 'n' in tail or 's' in tail:
                d2 = (y if 's' in tail else 31 - y) - off - _wave(x)
            if d2 is None:
                dist = d1
            elif d1 is None:
                dist = d2
            elif shape.startswith('outer'):                       # land is where BOTH are positive
                dist = min(d1, d2) if (d1 >= 0 or d2 >= 0) else -math.hypot(d1, d2)
                if 0 <= d1 < 9 and 0 <= d2 < 9:
                    dist = 9 - math.hypot(9 - d1, 9 - d2)         # the point of the beach, rounded off
            else:                                                 # a cove: sea is where BOTH are negative
                dist = max(d1, d2) if (d1 < 0 or d2 < 0) else math.hypot(d1, d2)
            k = h3(x, y, 31)
            if dist >= 0:
                if dist < 3.0:
                    c = rgb('a8d4e6') if (x + y) % 5 else rgb('c6e6f0')        # the swash, glassy over sand
                elif dist < 5.2:
                    c = WHITE if k > 50 else rgb('e4f2f6')        # the foam line
                elif dist < 6.2:
                    c = rgb('bcae94')                             # its wet shadow
                elif dist < 12.5:
                    c = rgb('d3c5a4') if k > 34 else rgb('c8b996')            # wet sand: darker and cooler
                    if k > 236:
                        c = rgb('e6dcc2')                         # a sheen
                elif dist < 14.5:
                    c = rgb('d3c5a4') if (x + y) % 2 else sand_tex(x, y)
                else:
                    c = sand_tex(x, y)
            else:
                t = max(0.0, 1 + dist / 32)                       # 0 deep .. 1 by the foam
                i = min(6, int(t * 7))
                c = DEEPS[i]
                if i < 6 and (x + y) % 2 and k < 40 + 60 * (t * 7 - i):
                    c = DEEPS[i + 1]
                w = int(-dist + 0.5) % 8
                if w == 0 and (x + y * 3) % 11 < 6 and t > 0.25:
                    c = rgb('e4f2f6') if t > 0.6 else SEA_HI      # the lines of small waves, along the shore
                elif t > 0.55 and w == 4 and (x * 3 + y) % 13 < 4:
                    c = rgb('c9b48a')                             # sand showing through
            px[x, y] = c
    return im


# ==============================================================================
# Dazaifu
# ==============================================================================
def plum_crest(d, cx, cy, c, r=2):
    """Five round petals: the shrine's plum."""
    for k in range(5):
        a = math.radians(-90 + k * 72)
        x, y = round(cx + (r + 1) * math.cos(a)), round(cy + (r + 1) * math.sin(a))
        d.ellipse([x - r + 1, y - r + 1, x + r - 1, y + r - 1], fill=c)
    d.point((cx, cy), fill=rgb('ffd84a'))


def umegae_stall():
    """An umegae-mochi stall on the approach: the iron griddle on the street."""
    im, d = canvas(3, 3)                 # 96 x 96
    roof(d, 10, 26, (10, 85), (1, 94), pal=DZ_P, p=1.0, caps=False)
    d.rectangle([5, 30, 90, 90], fill=DWOOD_LO)
    # the fascia: a cedar board, u-me mo-chi, two crests
    bar(d, 7, 31, 88, 44, CEDAR_HI, WHITE, CEDAR_LO)
    d.rectangle([7, 31, 88, 44], outline=CEDAR_DK)
    kana(d, ['u', 'me'], 22, 34, rgb('a8323c')); kana(d, ['mo', 'chi'], 46, 34, rgb('3a2c2a'))
    plum_crest(d, 14, 37, rgb('d8475a')); plum_crest(d, 80, 37, rgb('d8475a'))
    timber_posts(d, (5, 87), 45, 90)
    # the open front: a white noren with red crests, the keeper, stacked steam trays
    d.rectangle([9, 45, 86, 72], fill=rgb('40282a'))
    d.rectangle([9, 45, 86, 47], fill=WARM)
    noren(d, 9, 46, 86, 54, rgb('fbf6ea'), WHITE, PAPER_LO, 6)
    for x in (15, 28, 41, 54, 67, 80):
        plum_crest(d, x, 50, rgb('d8475a'), 1)
    person(d, 14, 55, rgb('fbf6ea'), rgb('fbf6ea'), rgb('d8475a'))
    for k in range(3):                                            # bamboo steamers
        d.rectangle([66, 57 + k * 5, 82, 61 + k * 5], fill=CEDAR); d.line([(66, 57 + k * 5), (82, 57 + k * 5)], fill=CEDAR_HI)
        d.line([(66, 61 + k * 5), (82, 61 + k * 5)], fill=CEDAR_DK)
    # the griddle: an iron plate of round cakes, each stamped with the plum
    d.rectangle([7, 72, 88, 76], fill=CEDAR); d.line([(7, 72), (88, 72)], fill=CEDAR_HI)
    d.rectangle([28, 64, 62, 72], fill=SOOT); d.line([(28, 64), (62, 64)], fill=STONE_DK)
    d.rectangle([26, 66, 27, 68], fill=STONE_DK); d.rectangle([63, 66, 64, 68], fill=STONE_DK)
    for i, x in enumerate((32, 40, 48, 56)):
        d.ellipse([x - 3, 62, x + 3, 67], fill=rgb('fbf6ea') if i != 2 else rgb('e8c890'))
        d.arc([x - 3, 62, x + 3, 67], 0, 150, fill=rgb('c9b48a'))
        d.point((x, 64), fill=rgb('c98a5a')); d.point((x - 1, 65), fill=rgb('c98a5a')); d.point((x + 1, 65), fill=rgb('c98a5a'))
    for x in range(30, 61, 3):
        d.point((x, 71), fill=rgb('f0903a') if (x // 3) % 2 else rgb('d9482e'))
    # the counter front: boards, a red banner, a tray of cakes for sale
    d.rectangle([7, 77, 88, 90], fill=DWOOD)
    for x in range(9, 88, 4):
        d.line([(x, 78), (x, 89)], fill=DWOOD_LO)
    d.line([(7, 77), (88, 77)], fill=DWOOD_HI)
    bar(d, 12, 78, 24, 89, rgb('c2403a'), XRED_HI, XRED_LO)
    plum_crest(d, 18, 83, WHITE, 2)
    bar(d, 34, 79, 60, 87, PAPER, WHITE, PAPER_LO)
    for y in (81, 84):
        d.line([(36, y), (56, y)], fill=CREAM_DK)
    d.rectangle([68, 79, 84, 86], fill=CEDAR_HI); d.rectangle([68, 79, 84, 86], outline=CEDAR_LO)
    for x in (71, 76, 81):
        d.ellipse([x - 2, 80, x + 2, 84], fill=rgb('fbf6ea')); d.point((x, 82), fill=rgb('c98a5a'))
    footing(d, 3, 92, 90, 4)
    outline(im)
    puff(im, 38, 58, 3, a=110); puff(im, 50, 55, 4, a=90); puff(im, 44, 50, 3, a=60); puff(im, 74, 53, 3, a=80)
    return im


DZ_P = (rgb('8a6258'), rgb('684640'), rgb('b48a7a'), rgb('452c2c'))            # Dazaifu's lane: red-brown tile


def lattice_cafe():
    """An invented cafe on the approach: three layers of woven cedar sticks
    stepping in like a tunnel to glass doors. Its own roof (standing-seam
    bronze, not kawara); its only sign a plain hanging board."""
    im, d = canvas(4, 4)                 # 128 x 128
    # ---- a shallow standing-seam roof, weathered bronze ----------------------------------
    for y in range(16, 37):
        t = (y - 16) / 20
        xa, xb = round(14 - 12 * t), round(113 + 12 * t)
        for x in range(xa, xb + 1):
            k = (round(64 + (x - 64) / (1 + 0.105 * t)) - 1) % 7   # seams that splay a little toward the eave
            east = x > 64 + (xb - 64) * 0.62
            if k == 0:
                c = rgb('3d302c') if east else rgb('4a3a34')
            elif k == 1 and not east:
                c = rgb('8f7660')
            else:
                c = rgb('5c4a40') if east else rgb('6f5a4a')
            if y == 16:
                c = rgb('a88c70')
            d.point((x, y), fill=c)
    d.rectangle([1, 37, 126, 39], fill=rgb('3d302c')); d.line([(1, 37), (126, 37)], fill=rgb('a88c70'))
    d.rectangle([6, 40, 121, 122], fill=rgb('2a1f1e'))

    # ---- the lattice: three layers, each an opening smaller than the last -------------------
    def layer(box, hole, pal, period, w, phase=0):
        """Diagonal sticks `w` px stout both ways over `box`, left open over `hole`."""
        hi, mid, lo, sh = pal
        x0, y0, x1, y1 = box
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if hole[0] <= x <= hole[2] and y >= hole[1]:
                    continue
                a, b = (x + y + phase) % period, (x - y + phase) % period
                over = ((x + y + phase) // period + (x - y + phase) // period) % 2
                if a < w and not (b < w and over):
                    c = hi if a == 0 else mid                     # these rise to the east and catch the light
                elif b < w:
                    c = mid if b == 0 else lo
                elif a == w or b == w:
                    c = sh                                        # each stick's shadow on what is behind
                else:
                    continue                                      # a gap: the layer behind shows
                d.point((x, y), fill=c)

    def step(hole, pal):
        """An opening's rim: the cut stick ends, lit to the west and above;
        and the shadow the layer casts on the one behind."""
        hi, mid, lo, sh = pal
        x0, y0, x1, _ = hole
        shade(im, (x0, y0, x1, y0 + 3), (12, 8, 10, 120)); shade(im, (x0, y0 + 4, x0 + 3, 121), (12, 8, 10, 120))
        for y in range(y0 - 1, 122):
            d.point((x0 - 1, y), fill=hi if y % 3 else mid); d.point((x1 + 1, y), fill=lo if y % 3 else sh)
        for x in range(x0 - 1, x1 + 2):
            d.point((x, y0 - 1), fill=hi if x % 3 else mid)

    back = (rgb('8a6444'), rgb('6c4c34'), rgb('543a2a'), rgb('2a1f1e'))
    mid_ = (rgb('be9464'), rgb('9c7850'), rgb('785a3c'), rgb('30231f'))
    front = (rgb('f0cf9c'), CEDAR, CEDAR_LO, rgb('3a2a24'))
    doors, h2, h1 = (50, 72, 77, 122), (38, 60, 89, 122), (24, 48, 103, 122)
    layer(h2, doors, back, 5, 1, 2)                               # the innermost, round the doors
    step(h2, mid_)
    layer(h1, h2, mid_, 8, 2, 3)
    step(h1, front)
    layer((8, 41, 119, 122), h1, front, 12, 3)                    # the street face, the stoutest sticks
    # ---- the glass doors at the end of the tunnel, the lamplit room behind ----------------------
    d.rectangle([50, 72, 77, 122], fill=rgb('4a342a'))
    for y in range(74, 122):
        for x in range(52, 76):
            q = math.hypot((x - 64) / 14, (y - 96) / 30)
            d.point((x, y), fill=(WARM, LIT, rgb('d9a054'), rgb('a8703c'))[min(3, int(q * 3.4))])
    d.line([(52, 74), (75, 74)], fill=WHITE)
    for x in (57, 70):                                            # pendant lamps
        d.line([(x, 74), (x, 79)], fill=rgb('5a3a2a')); d.rectangle([x - 1, 80, x + 1, 82], fill=WHITE)
    d.rectangle([54, 102, 60, 108], fill=rgb('8a6a4a')); d.rectangle([67, 104, 74, 108], fill=rgb('8a6a4a'))   # tables
    d.rectangle([63, 72, 64, 122], fill=rgb('4a342a'))            # the two leaves meet
    d.line([(52, 98), (75, 98)], fill=rgb('6a4a34'))
    d.rectangle([61, 94, 62, 100], fill=CEDAR_HI); d.rectangle([65, 94, 66, 100], fill=CEDAR_HI)
    # ---- the only sign: a plain cedar board hung from the eave ------------------------------------
    d.line([(14, 40), (14, 43)], fill=SOOT); d.line([(42, 40), (42, 43)], fill=SOOT)
    bar(d, 11, 43, 45, 55, CEDAR_HI, WHITE, CEDAR_LO)
    d.rectangle([11, 43, 45, 55], outline=CEDAR_DK)
    for x in range(13, 44, 5):
        d.point((x, 45 + x % 3), fill=CEDAR)
    text(d, 'CAFE', 17, 46, rgb('4a2e22'))
    footing(d, 4, 123, 122, 4)
    outline(im)
    return im


def stone_lantern():
    """A tall kasuga lantern for the approach: mossed granite, a lit fire box."""
    im, d = canvas(1, 2)                 # 32 x 64
    g, hi, lo, dk = GRAN, GRAN_HI, GRAN_LO, GRAN_DK
    d.polygon([(16, 3), (13, 8), (19, 8)], fill=g); d.point((15, 5), fill=hi)             # the jewel
    d.rectangle([14, 8, 18, 10], fill=lo)
    for y in range(11, 19):                                       # the hexagonal roof, its upturned corners
        half = 3 + (y - 11) * 9 // 7
        d.line([(16 - half, y), (16 + half, y)], fill=g if y < 17 else lo)
        d.point((16 - half, y), fill=hi)
        d.point((16 + half, y), fill=dk)
    d.point((4, 17), fill=hi); d.point((3, 16), fill=hi); d.point((28, 17), fill=dk); d.point((29, 16), fill=lo)
    for x in range(8, 25, 4):
        d.line([(x, 13 + abs(16 - x) // 3), (x - (1 if x < 16 else -1), 18)], fill=lo)
    bar(d, 10, 19, 22, 30, g, hi, dk)                             # the fire box
    d.rectangle([13, 21, 19, 28], fill=WARM); d.rectangle([13, 21, 19, 22], fill=WHITE)
    d.line([(16, 21), (16, 28)], fill=lo); d.line([(13, 25), (19, 25)], fill=lo)
    d.rectangle([8, 31, 24, 33], fill=g); d.line([(8, 31), (24, 31)], fill=hi); d.line([(8, 33), (24, 33)], fill=dk)
    d.rectangle([11, 34, 21, 36], fill=lo)
    bar(d, 13, 37, 19, 52, g, hi, dk)                             # the shaft, a band
    d.rectangle([12, 43, 20, 45], fill=lo); d.line([(12, 43), (20, 43)], fill=hi)
    d.rectangle([9, 53, 23, 56], fill=g); d.line([(9, 53), (23, 53)], fill=hi)
    d.rectangle([6, 57, 26, 61], fill=lo); d.line([(6, 57), (26, 57)], fill=g); d.line([(6, 61), (26, 61)], fill=dk)
    for x, y in ((7, 16), (9, 15), (11, 14), (21, 32), (22, 31), (8, 58), (10, 57), (12, 58), (20, 54), (14, 48), (13, 50), (5, 17)):
        d.point((x, y), fill=rgb('6a9c59'))                       # moss
    for x, y in ((10, 16), (9, 57), (13, 49)):
        d.point((x, y), fill=rgb('4f8250'))
    outline(im)
    return grounded(im, ellipses=[(3, 57, 29, 63)], a=60)


def ox_statue():
    """The shrine's bronze ox, lying on a granite block, its head rubbed bright."""
    im, d = canvas(2, 2)                 # 64 x 64
    b, hi, lo = BRONZE, BRONZE_HI, BRONZE_LO
    dk = rgb('3a2c22')
    shine, glint = rgb('b98a50'), rgb('e8c080')
    # the plinth
    bar(d, 4, 44, 59, 60, GRAN, GRAN_HI, GRAN_DK)
    d.rectangle([2, 42, 61, 45], fill=GRAN_HI); d.line([(2, 45), (61, 45)], fill=GRAN_LO)
    d.rectangle([50, 46, 59, 60], fill=GRAN_LO)
    d.rectangle([22, 49, 42, 56], fill=rgb('3a3a44')); d.rectangle([22, 49, 42, 56], outline=GRAN_DK)
    plum_crest(d, 32, 52, rgb('f0d98c'), 1)
    # the body: a long mound, the rump to the east
    d.ellipse([16, 20, 60, 44], fill=b)
    d.ellipse([18, 20, 54, 36], fill=hi); d.ellipse([20, 23, 60, 44], fill=b)
    d.chord([16, 20, 60, 44], 10, 150, fill=lo)
    d.ellipse([42, 22, 60, 42], fill=b); d.chord([42, 22, 60, 42], 330, 120, fill=lo)       # the haunch
    d.arc([42, 22, 60, 42], 180, 290, fill=hi)
    d.line([(58, 30), (61, 38)], fill=lo, width=2); d.rectangle([60, 38, 62, 41], fill=dk)   # the tail
    # folded legs
    d.rectangle([20, 38, 34, 43], fill=lo); d.rectangle([18, 40, 24, 43], fill=dk)
    d.rectangle([44, 39, 56, 43], fill=lo); d.rectangle([42, 41, 47, 43], fill=dk)
    d.line([(20, 38), (34, 38)], fill=b)
    # the head, turned to the west: brow, muzzle, horns, an ear - polished by hands
    d.ellipse([4, 14, 24, 34], fill=shine)
    d.ellipse([4, 14, 16, 25], fill=glint); d.ellipse([7, 17, 24, 34], fill=shine)
    d.chord([4, 14, 24, 34], 20, 130, fill=b)
    d.ellipse([2, 26, 14, 36], fill=shine); d.chord([2, 26, 14, 36], 20, 160, fill=b)        # the muzzle
    d.point((4, 31), fill=dk); d.point((8, 32), fill=dk); d.line([(4, 34), (10, 35)], fill=dk)
    d.rectangle([11, 22, 13, 24], fill=dk); d.point((11, 22), fill=WHITE)                    # the eye
    d.polygon([(10, 15), (5, 8), (8, 7), (14, 14)], fill=shine); d.line([(5, 8), (10, 15)], fill=glint)   # horns
    d.polygon([(19, 14), (25, 7), (27, 9), (22, 17)], fill=b); d.line([(25, 7), (19, 14)], fill=hi)
    d.polygon([(21, 18), (29, 16), (27, 22)], fill=b); d.line([(21, 18), (29, 16)], fill=hi)  # the ear
    d.arc([14, 20, 30, 40], 250, 330, fill=lo)                    # the neck's fold
    # a red-and-white bib rope round the neck
    for k in range(7):
        x, y = 20 + k, 30 + round(k * 1.3)
        d.point((x, y), fill=XRED if k % 2 else WHITE); d.point((x, y + 1), fill=XRED_LO if k % 2 else PAPER_LO)
    outline(im)
    return grounded(im, ellipses=[(2, 54, 62, 63)], a=60)


def hedge(conn):
    """A clipped sasanqua hedge, one cell, joining to the sides named in
    `conn` (letters of n, e, s, w): its top from above, its south face below."""
    im, d = canvas(1, 1)
    top = set()
    T0, T1 = 5, 21                       # the top's rows where it runs east-west
    L, R = 8, 23                         # its columns where it runs north-south
    core = [(x, y) for x in range(L, R + 1) for y in range(T0, T1 + 1)]
    top.update(core)
    if 'w' in conn:
        top.update((x, y) for x in range(0, L) for y in range(T0, T1 + 1))
    if 'e' in conn:
        top.update((x, y) for x in range(R + 1, 32) for y in range(T0, T1 + 1))
    if 'n' in conn:
        top.update((x, y) for x in range(L, R + 1) for y in range(0, T0))
    if 's' in conn:
        top.update((x, y) for x in range(L, R + 1) for y in range(T1 + 1, 32))
    # round the free corners of the top
    for (x, y) in list(top):
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            if (x + dx, y) not in top and (x, y + dy) not in top and 0 <= x + dx < 32 and 0 <= y + dy < 32:
                top.discard((x, y))
    face = {(x, y + k) for (x, y) in top for k in range(1, 9) if y + k < 32} - top
    for (x, y) in face:
        k = h3(x, y, 41)
        d.point((x, y), fill=HEDGE_DK if k < 90 else HEDGE_LO)
        if (x, y - 1) in top:
            d.point((x, y), fill=HEDGE_DK)
    for (x, y) in top:
        k = h3(x, y, 37)
        lit = (x - 1, y) not in top or (x, y - 1) not in top
        c = HEDGE_HI if (lit and k < 200) or k < 34 else (HEDGE_LO if k > 214 else HEDGE)
        if (x + 1, y) not in top and x < 31:
            c = HEDGE_LO
        d.point((x, y), fill=c)
    blooms = [(x, y) for (x, y) in sorted(top) if h3(x // 3, y // 3, 5) < 16 and x % 3 == 1 and y % 3 == 1]
    for i, (x, y) in enumerate(blooms):                           # sasanqua, in flower in November
        c = rgb('f08aa8') if i % 3 else rgb('fbe3ea')
        d.point((x, y), fill=c); d.point((x + 1, y), fill=c) if (x + 1, y) in top else None
        d.point((x, y + 1), fill=rgb('c9587c')) if (x, y + 1) in top else None
    outline(im)
    return im


# ==============================================================================
# The second pass: what the kit still lacked
# ==============================================================================
# Kushida's hall and the autumn plum are in the house look (#350): every colour a tone of
# house_look.RAMPS or of the pack's trees, a navy outline, light from the upper left.
COPPER = [tone('green', i) for i in range(5)]          # verdigris copper, 2e4040 .. 93c297
HINOKI, HINOKI_HI, HINOKI_LO, HINOKI_DK = tone('cream', 1), tone('cream', 2), tone('cream', 0), rgb('7c5d56')   # bare cypress
STRAW, STRAW_HI, STRAW_LO = tone('gold', 2), tone('gold', 3), tone('gold', 1)
H_LAMP, H_LAMP_HI, H_LAMP_LO, H_LAMP_DK = tone('gold', 2), tone('gold', 3), tone('gold', 1), tone('gold', 0)
H_PANE, H_PANE_LO, H_GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')         # the pack's dark glass
H_RED, H_RED_HI, H_RED_LO = tone('red', 1), tone('red', 2), tone('red', 0)
H_STONE, H_STONE_HI, H_STONE_LO, H_STONE_DK = tone('steel', 4), tone('steel', 5), tone('steel', 3), tone('steel', 2)
H_WHITE, H_PAPER, H_DARK = tone('cream', 3), tone('cream', 2), tone('night', 3)
H_SHADE = rgb('2a3151', 90)
KANA['shi'] = ['.......', '#......', '.#....#', '#....#.', '.#..#..', '...#...', '.##....']


def kushida_hall():
    """Kushida shrine's own hall: bare cypress under a verdigris copper hip roof
    seen from above, tiled in courses, a cusped gable (karahafu) over the steps,
    the great straw rope, two big paper lanterns lit dim gold, latticed windows
    of dark glass. Not the stock vermilion shrine, not Tochoji's tile."""
    im, d = canvas(5, 4)                 # 160 x 128
    px = im.load()
    # ---- the roof from above: a ridge at the back, the front slope between two
    # hips, the hip ends either side (the west one lit, the east in shade) ------
    top, eave = 6, 49
    for y in range(top, eave + 1):
        hip = (y - top) * 37 / (eave - top)                       # the hips run out to the eave's corners
        side = min(37, (y - top) * 37 / 14)                       # the hip ends' outer edges, steeper
        hl, hr, ol, orr = round(41 - hip), round(118 + hip), round(41 - side), round(118 + side)
        course = (y - top) % 4
        for x in range(ol, orr + 1):
            if x < hl - 1 or x > hr + 1:                          # a hip end: tiles running down it
                west = x < hl
                c = (COPPER[4] if course == 1 else COPPER[3]) if west else (COPPER[2] if course == 1 else COPPER[1])
                if course == 0:
                    c = COPPER[2] if west else COPPER[0]
            elif x in (hl - 1, hl, hl + 1, hr - 1, hr, hr + 1):  # the hip ridges, capped
                c = COPPER[4] if x <= hl else (COPPER[0] if x == hr + 1 else COPPER[2])
            else:                                                 # the front slope: courses, staggered seams
                c = COPPER[3] if course in (1, 2) else COPPER[2]
                if course == 0:
                    c = COPPER[1] if (x + (y - top) // 4 * 3) % 6 else COPPER[0]
                elif course == 1 and x < hl + 10:
                    c = COPPER[4]                                 # the west of each course catches the light
                elif x > hr - 8 and course != 1:
                    c = COPPER[1]                                 # the east end turns away
            px[x, y] = c
    for y in (eave + 1, eave + 2):                                # the eave's lip, lit along its top
        d.line([(4, y), (155, y)], fill=COPPER[4] if y == eave + 1 else COPPER[1])
    d.line([(4, eave + 3), (155, eave + 3)], fill=COPPER[0])
    d.rectangle([40, top - 3, 119, top], fill=COPPER[1])          # the ridge, its top lit
    d.line([(40, top - 3), (119, top - 3)], fill=COPPER[4]); d.line([(40, top - 2), (119, top - 2)], fill=COPPER[3])
    for x0 in (34, 120):                                          # gilt ridge ends in place of the tile caps
        d.rectangle([x0, top - 5, x0 + 5, top + 1], fill=H_LAMP)
        d.line([(x0, top - 5), (x0, top + 1)], fill=H_LAMP_HI); d.line([(x0 + 5, top - 4), (x0 + 5, top + 1)], fill=H_LAMP_DK)
    # the eave's shadow on the rafter ends
    d.rectangle([8, 53, 151, 58], fill=HINOKI_DK)
    for x in range(10, 151, 5):
        d.rectangle([x, 55, x + 2, 57], fill=HINOKI); d.point((x, 55), fill=HINOKI_HI); d.point((x + 2, 57), fill=HINOKI_LO)
    d.rectangle([8, 59, 151, 61], fill=HINOKI); d.line([(8, 59), (151, 59)], fill=HINOKI_HI)
    # ---- the wall: cypress boards, latticed windows of dark glass, vermilion only on the rail ----
    for y in range(62, 109):
        for x in range(10, 150):
            k = (x - 10) % 7
            c = HINOKI_HI if k == 0 else (HINOKI_LO if k == 6 else HINOKI)
            if x >= 124:
                c = HINOKI_LO if k else HINOKI_DK                 # the east bay in the roof's shade
            px[x, y] = c
    for y in range(62, 65):                                       # the eave's shadow along the top of the wall
        for x in range(10, 150):
            if y < 64 or (x + y) % 2:
                px[x, y] = HINOKI_DK
    for x0, x1 in ((14, 46), (112, 144)):
        d.rectangle([x0, 66, x1, 94], fill=HINOKI_DK)
        for y in range(67, 94):
            for x in range(x0 + 1, x1):
                u = (x - x0) + (y - 66)                           # the glare slants up to the right
                c = H_PANE_LO if y < 69 else H_PANE
                if u % 24 in (9, 10, 11) or u % 24 == 14:
                    c = H_GLARE
                px[x, y] = c
        for x in range(x0 + 8, x1, 8):                            # the lattice: mullions and a transom
            d.line([(x, 67), (x, 93)], fill=HINOKI_LO)
        d.line([(x0 + 1, 80), (x1 - 1, 80)], fill=HINOKI_LO); d.line([(x0 + 1, 81), (x1 - 1, 81)], fill=HINOKI_DK)
        d.line([(x0, 95), (x1, 95)], fill=HINOKI_HI)              # the sill, lit
    timber_posts(d, (8, 48, 108, 148), 62, 110, (HINOKI, HINOKI_HI, HINOKI_LO, HINOKI_DK))
    d.rectangle([10, 98, 149, 100], fill=H_RED); d.line([(10, 98), (149, 98)], fill=H_RED_HI)    # the veranda rail
    d.line([(10, 101), (149, 101)], fill=H_RED_LO)
    for x in range(12, 149, 6):
        d.line([(x, 102), (x, 108)], fill=H_RED_LO)
    # the open centre: the dark hall, a mirror on its stand in lamplight, the bell rope, the offering box
    d.rectangle([52, 62, 107, 110], fill=H_DARK)
    for y in range(64, 110):
        for x in range(54, 106):
            q = math.hypot((x - 80) / 26, (y - 84) / 28)
            if q < 1:
                px[x, y] = (H_LAMP_HI, H_LAMP, H_LAMP_LO, H_LAMP_DK)[min(3, int(q * 4))]
    d.ellipse([74, 74, 86, 86], fill=H_WHITE); d.ellipse([74, 74, 86, 86], outline=H_LAMP_DK)
    d.arc([76, 76, 84, 84], 180, 300, fill=H_STONE_HI); d.rectangle([77, 87, 83, 90], fill=H_LAMP_DK)
    d.rectangle([70, 91, 90, 93], fill=H_RED_LO)
    for y in range(64, 96):                                       # the bell rope: red and white twist
        d.point((66, y), fill=H_RED if (y // 2) % 2 else H_WHITE); d.point((67, y), fill=H_WHITE if (y // 2) % 2 else H_RED)
    d.ellipse([63, 60, 70, 66], fill=H_LAMP); d.point((65, 62), fill=H_LAMP_HI)
    bar(d, 66, 99, 94, 109, HINOKI_LO, HINOKI, HINOKI_DK)         # the offering box, slatted
    for x in range(69, 93, 4):
        d.line([(x, 99), (x, 102)], fill=H_DARK)
    d.line([(66, 103), (94, 103)], fill=HINOKI_HI)
    # ---- the cusped gable over the steps: a copper bow with upturned ends, tiled ---------------
    def bow(x):
        t = (x - 80) / 34
        return 44 - 14 * math.cos(t * math.pi / 2) ** 0.8 + 5 * max(0.0, abs(t) - 0.6) ** 1.0 * -2.0
    for x in range(46, 115):
        y = round(bow(x))
        for k in range(6):
            c = COPPER[4] if k == 0 else (COPPER[3] if k < 3 else (COPPER[2] if k < 5 else COPPER[0]))
            if x > 96 and 0 < k < 3:
                c = COPPER[2]
            if (x - 46) % 4 == 0 and 0 < k < 5:
                c = COPPER[1]                                     # the joints of its tiles
            px[x, y + k] = c
        for yy in range(y + 6, 58):                               # the gable's face: white plaster, its foot shaded
            px[x, yy] = (H_WHITE if x < 96 else H_PAPER) if yy < 55 else H_PAPER
    for x in (46, 114):
        d.rectangle([x - 1, round(bow(x)) - 2, x + 1, round(bow(x)) + 1], fill=H_LAMP)
        d.point((x - 1, round(bow(x)) - 2), fill=H_LAMP_HI)
    # in the gable: a dark plaque, ku-shi-da in gold, a gilt boss over it
    d.rectangle([65, 40, 95, 52], fill=H_DARK); d.rectangle([65, 40, 95, 52], outline=H_LAMP)
    d.line([(66, 51), (94, 51)], fill=H_PANE_LO)
    kana(d, ['ku', 'shi', 'da'], 69, 43, H_LAMP_HI)
    d.ellipse([77, 33, 83, 38], fill=H_LAMP); d.point((79, 34), fill=H_LAMP_HI)
    d.rectangle([48, 56, 111, 58], fill=HINOKI_DK); d.line([(48, 56), (111, 56)], fill=HINOKI_HI)
    timber_posts(d, (50, 106), 58, 110, (HINOKI, HINOKI_HI, HINOKI_LO, HINOKI_DK))
    # the great straw rope between the porch posts, its paper streamers and tassels
    for x in range(53, 107):
        t = (x - 53) / 53
        y = 61 + round(5 * math.sin(t * math.pi))
        th = 2 + round(1.6 * math.sin(t * math.pi))
        for k in range(th + 1):
            px[x, y + k] = STRAW_HI if k == 0 else (STRAW_LO if k == th or (x + k) % 4 == 0 else STRAW)
    for x in (64, 80, 96):
        y = 61 + round(5 * math.sin((x - 53) / 53 * math.pi)) + 4
        d.line([(x - 4, y), (x - 4, y + 5)], fill=STRAW_LO); d.line([(x - 3, y), (x - 3, y + 4)], fill=STRAW)
        for k in range(4):                                        # a shide: a zigzag of white paper
            d.rectangle([x + (k % 2) * 2, y + k * 2, x + 2 + (k % 2) * 2, y + k * 2 + 1], fill=H_WHITE)
    # two big paper lanterns on the porch posts, lit: dim gold paper, the glow at their hearts
    for x in (39, 111):
        d.line([(x + 5, 60), (x + 5, 64)], fill=H_DARK)
        d.rectangle([x + 2, 64, x + 8, 65], fill=H_DARK)
        d.ellipse([x, 65, x + 10, 85], fill=H_LAMP)
        d.ellipse([x + 1, 67, x + 7, 83], fill=H_LAMP_HI)
        d.ellipse([x + 7, 68, x + 10, 82], fill=H_LAMP_LO)
        for y in range(69, 84, 3):
            d.line([(x + 1, y), (x + 9, y)], fill=H_LAMP_LO)
        plum_crest(d, x + 5, 75, H_RED, 2)
        d.rectangle([x + 2, 85, x + 8, 86], fill=H_DARK)
    # ---- the stone base and steps -----------------------------------------------------------
    d.rectangle([4, 110, 155, 122], fill=H_STONE); d.line([(4, 110), (155, 110)], fill=H_STONE_HI)
    d.rectangle([4, 119, 155, 122], fill=H_STONE_LO); d.line([(4, 122), (155, 122)], fill=H_STONE_DK)
    for x in range(4, 156, 19):
        d.line([(x, 111), (x, 118)], fill=H_STONE_LO)
    for k in range(4):
        y = 110 + k * 4
        d.rectangle([54 - k * 2, y, 105 + k * 2, y + 3], fill=H_STONE_HI if k % 2 == 0 else H_STONE)
        d.line([(54 - k * 2, y + 3), (105 + k * 2, y + 3)], fill=H_STONE_LO)
    outline(im, NAVY)
    for y, inset in zip(range(124, 128), (0, 1, 3, 6)):           # its shadow on the ground
        for x in range(3 + inset, 157 - inset):
            if px[x, y][3] == 0:
                px[x, y] = H_SHADE
    return im


# the autumn plum's leaves, shaded the way the pack's trees are: lit in autumn colours,
# turning through pale green and teal to blue and purple in the shade
PLUM_GOLD = [rgb(c) for c in ('f3d890', 'f3d890', 'c6a663', 'c6a663', 'a7843b', '93c297', '508582', '425faa', '3c396d')]
PLUM_RUSSET = [rgb(c) for c in ('f6a583', 'ce6a42', 'ce6a42', 'aa4d31', 'aa4d31', '6c8e7f', '508582', '314b8e', '3c396d')]


def plum_autumn():
    """The flying plum in mid November: a gnarled trunk, bare twigs and the
    last yellow and russet leaves in ragged clumps, inside its low shrine fence
    with a name board."""
    im, d = canvas(3, 3)                 # 96 x 96
    bark, bark_hi, bark_lo = rgb('7f513b'), rgb('a68777'), rgb('594b45')   # the pack's bark

    def limb(pts, w):
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            steps = max(abs(xb - xa), abs(yb - ya))
            for n in range(steps + 1):
                x, y = xa + (xb - xa) * n // steps, ya + (yb - ya) * n // steps
                d.rectangle([x - w // 2, y, x - w // 2 + w - 1, y], fill=bark)
                d.point((x - w // 2, y), fill=bark_hi)
                if w > 2:
                    d.point((x - w // 2 + w - 1, y), fill=bark_lo)

    # the fence's back rail first, so the trunk stands inside it
    d.line([(16, 70), (80, 70)], fill=H_RED_LO)
    for x in (16, 32, 48, 64, 80):
        d.rectangle([x - 1, 64, x, 72], fill=H_RED_LO)
    # the trunk: thick, leaning west, forking low; lit on the west, dark on the east
    for y in range(50, 87):
        t = (y - 50) / 36
        x0, x1 = round(47 - 7 * math.sin(t * math.pi * 0.8)), round(53 + 4 * t * t)
        for x in range(x0, x1 + 1):
            px_c = bark_hi if x < x0 + 2 else (bark_lo if x > x1 - 3 else bark)
            d.point((x, y), fill=px_c)
    for x, y in ((47, 62), (50, 74), (45, 80), (51, 56)):
        d.point((x, y), fill=bark_lo); d.point((x + 1, y + 1), fill=bark_lo)
    d.rectangle([47, 66, 50, 69], fill=bark_lo); d.point((48, 67), fill=H_DARK)      # a knot hole
    limbs = (
        ([(45, 54), (36, 44), (24, 38), (12, 36)], 4), ([(36, 44), (30, 30), (22, 20)], 3),
        ([(48, 52), (46, 36), (40, 22), (42, 10)], 4), ([(46, 36), (54, 24), (56, 12)], 3),
        ([(52, 52), (62, 42), (74, 36), (86, 36)], 4), ([(62, 42), (68, 28), (78, 18)], 3),
        ([(24, 38), (14, 28)], 2), ([(30, 30), (36, 18)], 2), ([(22, 20), (12, 16)], 2), ([(22, 20), (24, 9)], 2),
        ([(40, 22), (32, 10)], 2), ([(54, 24), (64, 14)], 2), ([(56, 12), (52, 4)], 2), ([(42, 10), (46, 3)], 2),
        ([(74, 36), (82, 26)], 2), ([(68, 28), (62, 18)], 2), ([(78, 18), (88, 14)], 2), ([(78, 18), (76, 8)], 2),
        ([(12, 36), (6, 42)], 2), ([(86, 36), (91, 44)], 2), ([(12, 36), (5, 30)], 2), ([(86, 36), (92, 30)], 2),
    )
    for pts, w in limbs:
        limb(pts, w)
    # the last leaves: ragged clumps along the outer twigs, yellow and russet by turns, with
    # gaps between them where the bare twigs show
    foliage(im, [(13, 32, 8, 6), (37, 19, 7, 6), (62, 16, 8, 6), (86, 33, 7, 6), (71, 26, 6, 5)], PLUM_RUSSET, 11)
    foliage(im, [(22, 19, 9, 7), (48, 8, 9, 6), (80, 15, 9, 7), (8, 40, 5, 4), (91, 41, 5, 4)], PLUM_GOLD, 3)
    # a straw rope with paper streamers round the trunk
    d.rectangle([40, 60, 54, 62], fill=STRAW); d.line([(40, 60), (54, 60)], fill=STRAW_HI); d.line([(40, 62), (54, 62)], fill=STRAW_LO)
    for x in (43, 48, 52):
        d.rectangle([x, 63, x + 1, 66], fill=H_WHITE)
    # the fence's front and sides: low vermilion posts and two rails, on a stone kerb
    d.rectangle([10, 86, 86, 90], fill=H_STONE); d.line([(10, 86), (86, 86)], fill=H_STONE_HI)
    d.line([(10, 90), (86, 90)], fill=H_STONE_DK)
    for x in range(10, 87, 13):
        d.line([(x, 87), (x, 89)], fill=H_STONE_LO)
    for y in (76, 81):
        d.rectangle([12, y, 84, y + 1], fill=H_RED); d.line([(12, y), (84, y)], fill=H_RED_HI)
    for x in (12, 26, 40, 56, 70, 83):
        bar(d, x, 72, x + 2, 86, H_RED, H_RED_HI, H_RED_LO); d.rectangle([x - 1, 70, x + 3, 71], fill=H_DARK)
    d.line([(13, 73), (16, 70)], fill=H_RED_LO); d.line([(84, 73), (80, 70)], fill=H_RED_LO)
    # the name board
    bar(d, 62, 73, 80, 84, H_PAPER, H_WHITE, tone('cream', 1)); d.rectangle([62, 73, 80, 84], outline=bark_lo)
    kana(d, ['u', 'me'], 64, 75, H_DARK)
    outline(im, NAVY)
    return grounded(im, ellipses=[(8, 84, 88, 95)], a=50,
                    leaves=(6, 90, 88, 95, (PLUM_GOLD[1][:3], PLUM_RUSSET[1][:3], PLUM_RUSSET[2][:3]), 22, 5))


def mannequin(d, x, y, coat, hi):
    d.rectangle([x + 2, y, x + 4, y + 2], fill=rgb('e9dccb'))
    d.polygon([(x, y + 4), (x + 6, y + 4), (x + 7, y + 17), (x - 1, y + 17)], fill=coat)
    d.line([(x, y + 4), (x - 1, y + 17)], fill=hi)
    d.rectangle([x + 1, y + 18, x + 2, y + 23], fill=rgb('3a3440')); d.rectangle([x + 4, y + 18, x + 5, y + 23], fill=rgb('3a3440'))


def dept_store():
    """A Tenjin department store for the downtown blocks: a windowless mass of
    the station's charcoal tile, a lit atrium slot up its middle, two long
    Christmas banners, a bulb-edged marquee over show windows."""
    im, d = canvas(5, 6)                 # 160 x 192
    tile_wall(d, 6, 16, 153, 124)
    d.line([(6, 16), (6, 124)], fill=CH_HI); d.rectangle([150, 16, 153, 124], fill=CH_LO)
    d.rectangle([4, 10, 155, 16], fill=STONE); d.line([(4, 10), (155, 10)], fill=WHITE); d.line([(4, 16), (155, 16)], fill=STONE_LO)
    for x, c in ((30, XRED), (80, WHITE), (130, rgb('2f6f4c'))):   # three flags on the roof
        d.line([(x, 1), (x, 10)], fill=STONE_DK); d.rectangle([x + 1, 1, x + 8, 5], fill=c)
        d.line([(x + 1, 5), (x + 8, 5)], fill=dim(c, 0.75))
    for y in (42, 70, 98):                                        # a bronze string at each floor
        d.line([(6, y), (153, y)], fill=BRZ_LO); d.line([(6, y + 1), (149, y + 1)], fill=CH_DK)
    # the atrium slot: glass the whole height, the escalators' lights inside
    d.rectangle([62, 20, 97, 124], fill=BRZ_LO)
    glazing(d, 64, 22, 95, 124, cw=8, ch=9, lit=((0, 1), (1, 1), (2, 3), (3, 3), (1, 5), (2, 5), (0, 7), (3, 8), (1, 9), (2, 10)))
    for k in range(4):                                            # the escalators' diagonals behind the glass
        d.line([(66, 44 + k * 22), (93, 30 + k * 22)], fill=rgb('fff2b0'))
    d.line([(62, 20), (62, 124)], fill=BRZ_HI)
    # two long banners: red with a star and SALE, green with a tree and XMAS
    for x0, body, hi_, lo_, word in ((18, XRED, XRED_HI, XRED_LO, 'SALE'), (116, rgb('2f6f4c'), rgb('4f9468'), rgb('1f4f38'), 'XMAS')):
        d.rectangle([x0 - 1, 22, x0 + 26, 24], fill=BRZ_LO)
        bar(d, x0, 24, x0 + 25, 112, body, hi_, lo_)
        for x in range(x0 + 2, x0 + 25, 3):
            d.point((x, 111), fill=GOLD); d.point((x, 25), fill=GOLD)
        text(d, word, x0 + 8, 62, WHITE, 1, True)
        if word == 'SALE':
            star(d, x0 + 13, 42, 8, rgb('ffd84a')); star(d, x0 + 13, 42, 3, WHITE)
            star(d, x0 + 13, 102, 4, rgb('ffd84a'))
        else:
            for k in range(3):
                d.polygon([(x0 + 13, 31 + k * 6), (x0 + 6 - k, 41 + k * 6), (x0 + 20 + k, 41 + k * 6)], fill=rgb('8fd08a'))
            d.rectangle([x0 + 12, 54, x0 + 14, 57], fill=HONEY_LO); star(d, x0 + 13, 30, 3, rgb('ffd84a'))
            star(d, x0 + 13, 102, 4, WHITE)
    # ---- the marquee: a white canopy edged with bulbs, TENJIN on it -----------------------------
    d.rectangle([2, 125, 157, 137], fill=rgb('f3ead2')); d.line([(2, 125), (157, 125)], fill=WHITE)
    d.rectangle([2, 136, 157, 138], fill=BRZ); d.line([(2, 138), (157, 138)], fill=BRZ_LO)
    ctext(d, 'TENJIN', 80, 128, CH_DK)
    star(d, 50, 131, 3, XRED); star(d, 110, 131, 3, XRED)
    bulbs(d, [(x, 139) for x in range(4, 157, 3)], GOLD_BULBS)
    # ---- the ground floor: show windows of mannequins, the doors ---------------------------------
    d.rectangle([6, 140, 153, 186], fill=CH_DK)
    for k, (x0, x1) in enumerate(((10, 54), (106, 150))):
        d.rectangle([x0, 144, x1, 180], fill=BRZ_LO)
        d.rectangle([x0 + 1, 145, x1 - 1, 179], fill=WARM); d.line([(x0 + 1, 145), (x1 - 1, 145)], fill=WHITE)
        d.rectangle([x0 + 1, 174, x1 - 1, 179], fill=LIT)
        for i, (cc, hh) in enumerate(((XRED, XRED_HI), (INDIGO, INDIGO_HI), (rgb('2f6f4c'), rgb('4f9468')))):
            mannequin(d, x0 + 6 + i * 13, 151, cc if (i + k) % 2 == 0 else (rgb('c9a04a') if i == 1 else cc), hh)
        d.line([((x0 + x1) // 2 + 1, 145), ((x0 + x1) // 2 + 1, 179)], fill=BRZ_LO)
        d.rectangle([x0, 181, x1, 185], fill=CH); d.line([(x0, 181), (x1, 181)], fill=CH_HI)
    d.rectangle([60, 142, 99, 186], fill=BRZ_LO); d.line([(60, 142), (60, 186)], fill=BRZ_HI)
    d.rectangle([62, 144, 97, 150], fill=AMBER); d.line([(62, 144), (97, 144)], fill=WARM)
    glass_door(d, 62, 152, 79, 185, frame=BRZ_LO); glass_door(d, 80, 152, 97, 185, frame=BRZ_LO)
    for x in (58, 100):                                           # a small fir in a tub either side of the doors
        d.polygon([(x, 164), (x - 4, 180), (x + 4, 180)], fill=FIR); d.line([(x, 164), (x - 4, 180)], fill=FIR_HI)
        d.point((x - 1, 172), fill=rgb('ffd24a')); d.point((x + 1, 176), fill=XRED); d.point((x, 168), fill=WHITE)
        d.rectangle([x - 3, 181, x + 3, 185], fill=XRED_LO)
    footing(d, 4, 155, 186, 4, STONE_LO, WHITE)
    outline(im)
    return im


def office_block():
    """A slim downtown office in the same charcoal tile: tall window slots
    between piers, bronze spandrels, a bank on the ground floor."""
    im, d = canvas(3, 6)                 # 96 x 192
    tile_wall(d, 6, 22, 89, 140)
    d.line([(6, 22), (6, 140)], fill=CH_HI); d.rectangle([86, 22, 89, 140], fill=CH_LO)
    d.rectangle([4, 16, 91, 22], fill=STONE); d.line([(4, 16), (91, 16)], fill=WHITE); d.line([(4, 22), (91, 22)], fill=STONE_LO)
    bar(d, 58, 6, 78, 16, STONE_LO, STONE, STONE_DK)              # a tank and an aerial on the roof
    d.line([(58, 6), (78, 6)], fill=WHITE); d.line([(22, 2), (22, 16)], fill=STONE_DK); d.line([(19, 5), (25, 5)], fill=STONE_DK)
    d.point((22, 1), fill=XRED)
    # three window slots the whole height: glass between bronze spandrels
    for i, x0 in enumerate((12, 38, 64)):
        d.rectangle([x0, 28, x0 + 19, 134], fill=CH_DK)
        for j, y in enumerate(range(30, 130, 21)):
            for k in (0, 1):
                on = h3(i * 2 + k, j, 17) < 80
                xa = x0 + 1 + k * 9
                d.rectangle([xa, y, xa + 8, y + 13], fill=WARM if on else GLASS)
                d.line([(xa, y), (xa + 8, y)], fill=WHITE if on else GLASS_HI)
                if not on:
                    d.line([(xa + 1, y + 3), (xa + 1, y + 10)], fill=GLASS_HI)
                else:
                    d.line([(xa, y + 13), (xa + 8, y + 13)], fill=AMBER)
            d.rectangle([x0 + 1, y + 15, x0 + 18, y + 19], fill=BRZ); d.line([(x0 + 1, y + 15), (x0 + 18, y + 15)], fill=BRZ_HI)
            d.line([(x0 + 1, y + 19), (x0 + 18, y + 19)], fill=BRZ_LO)
    # ---- the ground floor: a bank behind a cream stone surround ---------------------------------
    d.rectangle([4, 140, 91, 146], fill=rgb('f3ead2')); d.line([(4, 140), (91, 140)], fill=WHITE)
    d.line([(4, 146), (91, 146)], fill=PAPER_LO)
    d.rectangle([6, 147, 89, 186], fill=rgb('e9dccb')); d.rectangle([80, 147, 89, 186], fill=PAPER_LO)
    bar(d, 10, 150, 50, 160, NAVY, None, None); d.rectangle([10, 150, 50, 160], outline=BRZ)
    text(d, 'BANK', 19, 152, rgb('f3e2b4'))
    d.rectangle([10, 164, 50, 180], fill=BRZ_LO); d.rectangle([11, 165, 49, 179], fill=GLASS)
    d.line([(11, 165), (49, 165)], fill=GLASS_HI); d.line([(30, 165), (30, 179)], fill=BRZ_LO)
    d.rectangle([13, 172, 27, 179], fill=rgb('6583bd')); d.rectangle([34, 170, 46, 179], fill=WARM)   # a counter, a lit desk
    d.rectangle([56, 150, 84, 186], fill=BRZ_LO); d.line([(56, 150), (56, 186)], fill=BRZ_HI)
    d.rectangle([58, 152, 82, 157], fill=AMBER); d.line([(58, 152), (82, 152)], fill=WARM)
    glass_door(d, 58, 159, 82, 185, frame=BRZ_LO)
    for x in (12, 44):                                            # clipped box in stone tubs
        blob(d, x + 3, 181, 4, 3, rgb('4f8250'), rgb('6fa262'), rgb('35603f'), seed=x)
    d.rectangle([10, 183, 50, 186], fill=STONE); d.line([(10, 183), (50, 183)], fill=WHITE)
    footing(d, 4, 91, 186, 4, STONE_LO, WHITE)
    outline(im)
    return im


# ==============================================================================
# Ground families (opaque, 9 autotile roles)
# ==============================================================================
def plaza_tex(x, y):
    """Pale granite squares turned round small charcoal insets (a pinwheel, period 16)."""
    u, v = x % 16, y % 16
    if (u < 4 and v < 4):
        return rgb('8d8f98') if (u in (0, 3) or v in (0, 3)) else rgb('a3a5ad')
    if u == 4 and v < 12 or v == 4 and u >= 4 or u == 15 and v >= 4 or v == 15 and u < 12 or (u == 11 and v >= 12) or (v == 11 and u < 4):
        return rgb('aeb0b6')
    k = h3(x, y, 3)
    return rgb('d6d7da') if k < 18 else (rgb('c3c5ca') if k > 236 else rgb('cdcfd3'))


def plaza_kerb(m, along):
    if m == 2:
        return rgb('8f9199')
    if along % 16 == 15:
        return rgb('9a9ca4')
    return rgb('eceef0') if m == 0 else rgb('c9cbd0')


def ground(fam):
    tex, kerb, kw = GROUNDS[fam]
    return lambda role: family(role, tex, kerb, kw)


GROUNDS = {'fukuoka-station-plaza-autotile': (plaza_tex, plaza_kerb, 3),
           'fukuoka-riverwalk-autotile': (herring_tex, herring_kerb, 4),
           'fukuoka-canal-paving-autotile': (fan_tex, fan_kerb, 4),
           'fukuoka-beach-autotile': (sand_tex, sand_kerb, 3)}


# ==============================================================================
def rows(w, r0, r1):
    return [[c, r] for r in range(r0, r1 + 1) for c in range(w)]


HS, NK, CC, OH, MO, DZ = 'Hakata Station', 'Nakasu', 'Canal City', 'Old Hakata', 'Momochi', 'Dazaifu'
WARM_C, GOLD_C, STAR_C, RED_C, PINK_C, CYAN_C, COAL_C = 0xf6dc8c, 0xffd24a, 0xfff0c0, 0xd16b56, 0xff5fa8, 0x5fe6f0, 0xf0903a

# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH or UNDER (gates, the arch)
#   lit: its lit parts, [col, row, colour (a number, 0xRRGGBB)(, radius in cells(, strength))]
#        from the top-left (fractions allowed): the glow spots src/utils/Glows.js would draw at night
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'ground' = a floor or water
#          tile, 'flat' = lies on the ground and is walked ON (Non-Collidables + a negative depthBias)
PIECES = [
    ('fukuoka-hakata-station_0_0', hakata_station, (9, 6), HS, dict(
        door=[[3, 5], [4, 5], [5, 5]], solid=rows(9, 3, 5),
        lit=[[4.5, 2.15, STAR_C, 1.3, 0.8], [1.7, 1.5, 0xffe8b0, 1.2, 0.45], [7.3, 1.5, 0xffe8b0, 1.0, 0.45],
             [4.5, 5.2, GOLD_C, 1.7, 0.6], [0.85, 5.2, WARM_C, 1.0, 0.75], [2.3, 5.2, WARM_C, 1.0, 0.75],
             [6.7, 5.2, WARM_C, 1.0, 0.75], [8.15, 5.2, WARM_C, 1.0, 0.75],
             [0.8, 4.7, GOLD_C, 0.8, 0.5], [2.2, 4.7, GOLD_C, 0.8, 0.5], [3.6, 4.7, GOLD_C, 0.8, 0.5],
             [5.4, 4.7, GOLD_C, 0.8, 0.5], [6.8, 4.7, GOLD_C, 0.8, 0.5], [8.2, 4.7, GOLD_C, 0.8, 0.5],
             [0.6, 2.2, WARM_C, 0.7, 0.4], [2.4, 2.2, WARM_C, 0.7, 0.4], [6.7, 2.5, WARM_C, 0.8, 0.4],
             [3.4, 3.2, WARM_C, 0.7, 0.4], [5.3, 3.2, WARM_C, 0.7, 0.4], [7.1, 0.5, 0xd4503a, 0.7, 0.3]]),
     "Hakata Station's front: ONE long flat front of charcoal, no tower and no office windows. A plain attic "
     'band of charcoal ceramic tile carries the name in bronze letters set on the tile itself (HAKATA to the '
     'west, ha-ka-ta in kana to the east); below it the skin is a continuous screen of dark vertical fins '
     'banded in bronze at each floor, lamplight showing between the fins here and there, and the big '
     'bronze-ringed clock is set straight onto it. Above the parapet the roof garden: big clipped trees, '
     'some turned for November, a white pergola, and the rooftop shrine - a copper-roofed cypress hall behind '
     'a vermilion torii on the east side. Below, a deep glass canopy on white columns projects about a cell, '
     'seen from above and in front, with the illumination curtain (swags of hanging lights) along its edge; '
     'in its shade, lit shops and three pairs of glass doors under an amber header - the three middle cells.'),
    ('fukuoka-dept-store_0_0', dept_store, (5, 6), HS, dict(
        door=[[2, 5]], solid=rows(5, 3, 5),
        lit=[[2.5, 2.2, WARM_C, 1.4, 0.5], [2.5, 4.1, GOLD_C, 2.2, 0.4], [1.0, 5.1, WARM_C, 1.1, 0.8],
             [4.0, 5.1, WARM_C, 1.1, 0.8], [2.5, 4.75, GOLD_C, 0.8, 0.7], [1.0, 1.3, 0xffd84a, 0.6, 0.5]]),
     "A department store for the station and downtown blocks (in place of a stock high-rise): a windowless "
     "mass of the station's charcoal tile with bronze strings, a glazed atrium slot up its middle with the "
     'escalators\' lights inside, two long Christmas banners (red: a gold star and SALE; green: a tree and '
     'XMAS), three flags on the roof, a white marquee edged with bulbs lettered TENJIN (the downtown\'s name), '
     'and show windows of mannequins either side of bronze-framed glass doors (middle cell) with a small fir '
     'in a tub each side.'),
    ('fukuoka-office_0_0', office_block, (3, 6), HS, dict(
        door=[[2, 5]], solid=rows(3, 3, 5),
        lit=[[0.9, 5.3, WARM_C, 0.9, 0.6], [2.2, 4.85, GOLD_C, 0.6, 0.6], [0.7, 1.4, WARM_C, 0.6, 0.4],
             [1.5, 2.7, WARM_C, 0.6, 0.4], [2.3, 3.4, WARM_C, 0.6, 0.4], [1.5, 0.05, 0xd16b56, 0.3, 0.5]]),
     'A slim downtown office in the same charcoal tile (a second filler front): three window slots the '
     'whole height, glass between bronze spandrels, a few floors lit, a tank and an aerial on the roof, and '
     'a bank on the ground floor behind cream stone - a BANK plate, a window, glass doors under an amber '
     'header (east cell), clipped box in stone tubs.'),
    ('fukuoka-xmas-hut-wine_0_0', lambda: hut('wine'), (3, 3), HS, dict(
        solid=rows(3, 1, 2), lit=[[1.5, 1.95, WARM_C, 1.2, 0.6], [1.5, 0.6, 0xff6a5a, 0.9, 0.25]]),
     'A Christmas-market hut selling mulled wine: a honey-timber cabin with its gable to the street under a '
     'red roof, fairy lights under the slopes, a gold star, a WINE board, a fir garland with red bows over '
     'the lit counter (a keeper in a red hat, a copper urn, red and white mugs), a wreath on the apron. '
     'A stall: you buy at the counter, there is no door.'),
    ('fukuoka-xmas-hut-wurst_0_0', lambda: hut('wurst'), (3, 3), HS, dict(
        solid=rows(3, 1, 2), lit=[[1.5, 1.95, WARM_C, 1.2, 0.6], [1.85, 2.2, COAL_C, 0.7, 0.5]]),
     'The sausage hut: the same cabin under a fir-green roof, WURST on its board, a cook in whites, a '
     'charcoal grill of sausages and strings of them hung above.'),
    ('fukuoka-xmas-hut-gifts_0_0', lambda: hut('gifts'), (3, 3), HS, dict(
        solid=rows(3, 1, 2), lit=[[1.5, 1.95, WARM_C, 1.2, 0.6], [1.5, 0.6, 0x6fb4ff, 0.9, 0.25]]),
     'The ornament hut: a blue roof, XMAS on its board, glass baubles on strings, nutcrackers and stars on '
     'the counter.'),
    ('fukuoka-xmas-tree_0_0', xmas_tree, (3, 5), HS, dict(
        solid=rows(3, 4, 4),
        lit=[[1.5, 0.3, STAR_C, 1.1, 0.9], [1.5, 1.6, GOLD_C, 1.2, 0.7], [1.5, 2.7, GOLD_C, 1.5, 0.7],
             [1.5, 3.7, GOLD_C, 1.7, 0.7]]),
     "The market's tall Christmas tree, the forecourt's centrepiece: five tiers of fir with gold bead "
     'garlands, coloured baubles and white fairy lights, a big gold star, a red planter and parcels at its '
     'foot. Three cells wide; its bottom row (the planter and the parcels either side) is solid, so you walk '
     'behind its boughs.'),
    ('fukuoka-illumination-arch_0_0', illumination_arch, (3, 3), HS, dict(
        solid=[[0, 2], [2, 2]], walk=[[1, 2]],
        lit=[[1.5, 0.25, STAR_C, 0.9, 0.8], [0.45, 1.3, GOLD_C, 0.9, 0.4], [2.55, 1.3, GOLD_C, 0.9, 0.4],
             [1.5, 0.75, GOLD_C, 1.2, 0.4], [0.3, 2.3, GOLD_C, 0.7, 0.4], [2.7, 2.3, GOLD_C, 0.7, 0.4]]),
     'An illumination arch: a round arch of fir garland wound with a gold ribbon and coloured lights, red '
     'bows, gold stars hanging inside it and one on top, red tubs at its feet. Walk under it through the '
     'middle cell; stand two or three in a row as the way into the market.'),
    ('fukuoka-ramen-shop_0_0', ramen_shop, (3, 4), HS, dict(
        door=[[2, 3]], solid=rows(3, 2, 3),
        lit=[[0.85, 3.2, WARM_C, 0.9], [2.15, 3.4, WARM_C, 0.8], [1.35, 3.0, GOLD_C, 0.6, 0.6],
             [1.4, 1.7, RED_C, 1.2, 0.3]]),
     'A tonkotsu ramen shop: cream tile upstairs with a big red board lettered ra-a-me-n in white kana over '
     'to-n-ko-tsu in gold, a steel flue up the east side with a thick plume of pork-bone steam, a dark '
     'tiled pent; below, the counter window (a cook in whites, the boiling stock pot, bowls) and the door '
     'under a long red noren (east cell): one cedar leaf slid shut, the other standing open on the lit shop, '
     'a yellow lantern.'),
    ('fukuoka-mentaiko-shop_0_0', mentaiko_shop, (3, 3), HS, dict(
        door=[[2, 2]], solid=rows(3, 1, 2),
        lit=[[1.0, 2.1, WARM_C, 1.1, 0.8], [2.3, 2.3, 0xd8f4ff, 0.6, 0.4], [1.5, 0.75, 0xffe8e0, 1.1, 0.3]]),
     'A mentaiko (spiced cod roe) shop: white plaster under a low roof of dark red tile, a white board lettered me-n-ta-i-ko in red kana, a '
     'coral and white awning, a lit window of cedar boxes of pink roe and red gift boxes with a clerk, a '
     'glass door under a short coral noren (east cell).'),
    ('fukuoka-neon-bar_0_0', neon_bar, (6, 4), NK, dict(
        door=[[1, 3]], solid=rows(6, 2, 3),
        lit=[[0.7, 1.1, PINK_C, 1.0, 0.7], [2.2, 0.75, GOLD_C, 1.4, 0.7], [2.2, 1.7, COAL_C, 0.9, 0.5],
             [3.7, 1.25, 0x7cf08a, 0.9, 0.7], [5.1, 0.8, GOLD_C, 1.0, 0.6], [5.1, 1.55, CYAN_C, 1.1, 0.7],
             [1.5, 3.35, PINK_C, 0.8, 0.7], [0.55, 3.3, WARM_C, 0.6, 0.6], [2.5, 3.5, WARM_C, 0.6, 0.6],
             [3.5, 3.2, 0xb98cff, 0.6, 0.6], [4.4, 3.0, CYAN_C, 0.5, 0.6], [5.35, 3.3, 0xff9a4a, 0.6, 0.6],
             [1.3, 2.5, GOLD_C, 0.9, 0.3], [3.4, 2.5, 0xb98cff, 0.9, 0.3], [5.0, 2.5, PINK_C, 0.9, 0.3]]),
     "Nakasu's riverside block, to face the water: wider than tall. A low two-storey row of dark plum tile "
     'carries a wall of rooftop billboards on steel frames, each its own size and colour under floodlight '
     'arms - a pink-tube cocktail glass over BAR, the wide SAKE board in yellow tube with a flask and '
     'chaser bulbs over a painted ya-ki-to-ri board with skewers, a dartboard over DARTS in green, and the '
     'tallest, a foaming mug over BEER. Upstairs has no windows, only each bar\'s small lit sign box; at '
     'street level six bars, one to a cell: a lattice window, a padded door in a pink neon frame (THE door, '
     'second cell), an izakaya\'s noren, a back-lit bottle window, the stair up under a cyan arrow, a '
     'snack bar\'s round window; paper lanterns between.'),
    ('fukuoka-motsunabe-shop_0_0', motsunabe_shop, (4, 4), NK, dict(
        door=[[2, 3]], solid=rows(4, 2, 3),
        lit=[[1.05, 3.2, WARM_C, 1.1, 0.75], [2.5, 3.45, WARM_C, 0.7, 0.75], [3.35, 3.25, RED_C, 0.8, 0.8],
             [1.5, 2.15, GOLD_C, 1.2, 0.3]]),
     "A motsunabe (offal hot-pot) house, Nakasu's second front: black boards under a low rust-red tin "
     'roof, a long white board lettered mo-tsu-na-be beside an iron pot heaped with cabbage and chives '
     'under steam, a red rail of small lanterns, and below a lit window of diners at a pot, lattice doors '
     'standing open under a white noren lettered mo-tsu (third cell) and a great red paper lantern '
     'lettered na-be.'),
    ('fukuoka-pub_0_0', pub, (4, 4), NK, dict(
        door=[[2, 3]], solid=rows(4, 2, 3),
        lit=[[1.05, 3.2, WARM_C, 1.1, 0.8], [3.3, 3.2, WARM_C, 0.8, 0.8], [2.4, 2.95, WARM_C, 0.6, 0.75],
             [1.3, 1.7, WARM_C, 0.7, 0.65], [2.7, 1.7, WARM_C, 0.7, 0.65], [2.0, 0.6, WARM_C, 0.5, 0.6]]),
     'The fake British pub from the posts: black-and-white half-timber over a bottle-green front, THE OLD '
     'OAK in gold on the fascia (an invented name), a slate roof with a timbered gable and a brick chimney, '
     'leaded windows lit amber with flower boxes, a hanging sign with an oak, an oxblood door with brass '
     "and a fanlight (third cell), brass lamps and an ALE chalk board. Not Sendai's red-fascia pub."),
    ('fukuoka-river-rail_0_0', river_rail, (1, 1), NK, dict(solid=[[0, 0]]),
     'The riverside railing: dark iron pickets under a round top rail on a granite kerb, a post at each '
     "cell's west edge. Tiles east-west along the bank; solid."),
    ('fukuoka-river-rail-lanterns_0_0', lambda: river_rail(True), (1, 2), NK, dict(solid=[[0, 1]]),
     'The same railing with a lantern post: an iron standard with a cross arm and two paper lanterns (red '
     'with a white band, white with a red mark). Its key holds `-lanterns`, so DayNight gives it the lamp '
     'halo. Every third or fourth cell of a run.'),
    ('fukuoka-nakasu-gate_0_0', nakasu_gate, (4, 4), NK, dict(
        solid=[[0, 3], [3, 3]], walk=[[1, 3], [2, 3]],
        lit=[[2.0, 1.45, PINK_C, 1.7, 0.8], [2.0, 2.3, CYAN_C, 1.0, 0.5], [2.0, 0.55, GOLD_C, 0.8, 0.6],
             [0.35, 2.8, PINK_C, 0.6, 0.4], [3.65, 2.8, CYAN_C, 0.6, 0.4]]),
     "Nakasu's gate sign: two steel posts wound with pink and cyan lights carrying a marquee arc of bulbs "
     'with a neon crescent moon and stars in its head, a dark board lettered na-ka-su in big pink tube kana '
     'between cyan lines, and NAKASU in cyan on a hanging under-board. Walk through the two middle cells.'),
    ('fukuoka-canal_0_0', canal, (1, 2), CC, dict(solid=rows(1, 0, 1), layer='ground'),
     "A strip of Canal City's canal, tiling east-west: the far quay's cream coping with a terracotta band, "
     'its terracotta wall down to the water, teal water (not the river\'s blue), the near coping. Opaque; '
     'both cells are water (solid). Lay it across the plaza in front of the mall.'),
    ('fukuoka-canal-jets_0_0', lambda: canal('jets'), (1, 2), CC, dict(solid=rows(1, 0, 1), layer='ground'),
     'The same strip with three fountain jets standing in the water: the fountain show. A few in a row.'),
    ('fukuoka-canal-end-e_0_0', lambda: canal('end-e'), (1, 2), CC, dict(solid=rows(1, 0, 1), layer='ground'),
     "The canal's east end: the quay turns round the basin in a curve."),
    ('fukuoka-canal-end-w_0_0', lambda: canal('end-w'), (1, 2), CC, dict(solid=rows(1, 0, 1), layer='ground'),
     "The canal's west end."),
    ('fukuoka-canal-bridge_0_0', lambda: canal('bridge'), (1, 2), CC, dict(walk=rows(1, 0, 1), layer='flat'),
     'A footbridge across the canal, in place of one canal cell: a honey timber deck sitting on the two '
     'quays between terracotta rails with cream posts; the copings run on unbroken either side, water shows '
     'past both rails and its shadow lies on the water to the east. Flat: walked ON, north-south (both '
     'cells walkable).'),
    ('fukuoka-tochoji-hall_0_0', tochoji_hall, (5, 4), OH, dict(
        door=[[2, 3]], solid=rows(5, 2, 3),
        lit=[[2.5, 2.7, GOLD_C, 1.5, 0.8], [1.3, 2.55, WARM_C, 0.6, 0.4], [3.65, 2.55, WARM_C, 0.6, 0.4],
             [1.2, 2.15, WARM_C, 0.4, 0.5], [3.8, 2.15, WARM_C, 0.4, 0.5], [2.5, 1.65, GOLD_C, 0.8, 0.3]]),
     "Tochoji's own hall, in place of the small pagoda: a low wooden hall under a broad hip-and-gable roof "
     'of old brown-grey tile, dark unpainted timber and white plaster with bell-shaped windows in vermilion '
     'rims, bronze lanterns under the eave, and over the open centre bay a black plaque lettered dai-butsu '
     '(great buddha) in gold; through the doors the gilded seated buddha in lamplight on a lotus dais. Stone '
     'steps, an incense urn with smoke. The door is the middle cell.'),
    ('fukuoka-kushida-hall_0_0', kushida_hall, (5, 4), OH, dict(
        door=[[2, 3]], solid=rows(5, 2, 3),
        lit=[[2.5, 2.65, GOLD_C, 1.4, 0.7], [1.4, 2.35, 0xfff0d8, 0.7, 0.7], [3.6, 2.35, 0xfff0d8, 0.7, 0.7],
             [2.5, 1.45, GOLD_C, 0.7, 0.4]]),
     "Kushida shrine's own hall, in place of the stock vermilion shrine: bare cypress boards and latticed "
     'windows of dark glass with a slanted glare under a verdigris copper hip roof seen from above, tiled '
     'in courses, with gilt ridge ends; a cusped copper gable (karahafu) over the steps with a dark plaque '
     'lettered ku-shi-da in gold, the great straw rope with paper streamers between the porch posts, two '
     'big paper lanterns lit dim gold with red plum crests, and in the open centre a mirror on its stand '
     'in lamplight, a red-and-white bell rope and the slatted offering box. Vermilion only on the veranda '
     'rail. Stone base and steps; the door is the middle cell.'),
    ('fukuoka-hakata-ori-shop_0_0', ori_shop, (4, 4), OH, dict(
        door=[[2, 3]], solid=rows(4, 2, 3),
        lit=[[1.05, 3.0, WARM_C, 1.1, 0.8], [2.4, 3.4, WARM_C, 0.7, 0.75], [3.4, 3.2, WARM_C, 0.6, 0.5]]),
     'A Hakata-ori (silk textile) merchant\'s front, in place of the machiya: silver-grey smoked tile, white '
     'plaster upstairs with slit windows and a cedar board lettered ha-ka-ta o-ri, a tiled pent, and below '
     'unpainted honey cedar - a lit show window of obi bolts in the striped kenjo pattern, lamplit lattice '
     'doors under a long indigo noren with the kenjo band (third cell), a lattice bay with spools of thread.'),
    ('fukuoka-senbei-shop_0_0', senbei_shop, (3, 4), OH, dict(
        door=[[2, 3]], solid=rows(3, 2, 3),
        lit=[[1.0, 2.9, WARM_C, 1.0], [1.2, 3.2, COAL_C, 0.7, 0.5], [2.35, 3.35, WARM_C, 0.6]]),
     'A rice-cracker shop: dark slatted timber upstairs carrying a great glazed cracker with a nori strip '
     'lettered se-n and paper boards reading se-n / be-i, a tiled pent, and an open front where the keeper '
     'toasts crackers on a charcoal griddle before jars of them; cedar doors under a persimmon noren (east cell).'),
    ('fukuoka-hakata-bei_0_0', lambda: hakata_bei('h'), (1, 2), OH, dict(solid=[[0, 1]]),
     'The Hakata-bei wall, straight (runs east-west): fire-salvaged stones and broken roof tiles set in '
     'courses in ochre clay - dark tile slivers and pale lumps in stripes - under a little roof of grey tile, '
     "on a footing of field stones. Tiles left-right. Unlike Kanazawa's plaster and straw-mat walls and "
     "Sendai's black board fence."),
    ('fukuoka-hakata-bei-stop-e_0_0', lambda: hakata_bei('stop-e'), (1, 2), OH, dict(solid=[[0, 1]]),
     'The free east end of an east-west run (one side of a gateway): the wall stops at a clay arris.'),
    ('fukuoka-hakata-bei-stop-w_0_0', lambda: hakata_bei('stop-w'), (1, 2), OH, dict(solid=[[0, 1]]),
     'The free west end of an east-west run (the other side of a gateway).'),
    ('fukuoka-hakata-bei-corner-e_0_0', lambda: hakata_bei('corner-e'), (1, 3), OH, dict(solid=[[0, 2]]),
     'The east end of an east-west run where the wall turns north: the face stops at a corner and the tiled '
     'cap turns up the map (stack fukuoka-hakata-bei-v in the cells above).'),
    ('fukuoka-hakata-bei-corner-w_0_0', lambda: hakata_bei('corner-w'), (1, 3), OH, dict(solid=[[0, 2]]),
     'The west end of an east-west run where the wall turns north.'),
    ('fukuoka-hakata-bei-v_0_0', lambda: hakata_bei('v'), (1, 3), OH, dict(solid=[[0, 2]]),
     'A length of wall running north-south, seen from the south and a little west: its tiled cap from above '
     'and, down its west side, a 3px sliver of the clay face with its courses of tile and stone; drawn a cell '
     'and a half up the map from the cell it stands on (the bottom one).'),
    ('fukuoka-hakata-bei-top_0_0', lambda: hakata_bei('top'), (1, 3), OH, dict(solid=[[0, 2]]),
     'The NORTH end of a north-south run (the topmost piece, in place of the last -v): the cap closed '
     'across with an ink line and a round end tile.'),
    ('fukuoka-hakata-bei-end_0_0', lambda: hakata_bei('end'), (1, 3), OH, dict(solid=[[0, 2]]),
     'The south end of a north-south run: the cap, and under it the wall\'s end face on its footing.'),
    ('fukuoka-beach-house_0_0', beach_house, (4, 3), MO, dict(
        door=[[2, 2]], solid=rows(4, 1, 2),
        lit=[[1.05, 1.85, WARM_C, 1.1, 0.7], [2.45, 1.2, GOLD_C, 0.8, 0.7], [2.45, 2.0, WARM_C, 0.7, 0.5],
             [3.3, 2.0, WARM_C, 0.6, 0.6]]),
     'A seaside cafe for Momochi beach: white weatherboard with teal posts under a faded, rusting teal tin '
     'roof and a BEACH CAFE board with a sun, a yellow and white awning over a serving hatch (cups of '
     'shaved ice in three syrups, a keeper), a chalk menu and a life ring, a glass door under a string of '
     'bulbs (third cell), surfboards leaning by a window, a timber deck.'),
    ('fukuoka-beach-umbrella-a_0_0', lambda: umbrella('a'), (2, 2), MO, dict(solid=rows(2, 1, 1)),
     'A red and white beach parasol over a white lounger with a turquoise towel. Stands on sand.'),
    ('fukuoka-beach-umbrella-b_0_0', lambda: umbrella('b'), (2, 2), MO, dict(solid=rows(2, 1, 1)),
     'A blue and yellow parasol over an orange towel and a beach ball.'),
    ('fukuoka-lifeguard-chair_0_0', lifeguard_chair, (2, 3), MO, dict(solid=rows(2, 2, 2)),
     "The lifeguard's high chair: a white splayed timber frame with a ladder, a slatted seat with red arms "
     'under a small red and yellow roof, a red-and-yellow flag, an orange rescue float.'),
    # (the 24 shore pieces are appended below, from SHORE_SHAPES)
    ('fukuoka-umegae-stall_0_0', umegae_stall, (3, 3), DZ, dict(
        solid=rows(3, 1, 2), lit=[[1.5, 1.9, WARM_C, 1.2, 0.6], [1.4, 2.2, COAL_C, 0.6, 0.5]]),
     "An umegae-mochi stall for Dazaifu's approach lane: a tiled pent over a cedar board lettered u-me "
     'mo-chi between plum crests, a white noren of red crests, the keeper in a white kerchief, bamboo '
     'steamers, and on the counter the iron griddle of round rice cakes stamped with the plum, steam '
     'rising. A stall: no door.'),
    ('fukuoka-plum-autumn_0_0', plum_autumn, (3, 3), DZ, dict(solid=rows(3, 2, 2)),
     "Dazaifu's plum as it is in mid November (in place of plum-tree_0_0, which is in blossom): a gnarled "
     'trunk leaning west with a straw rope and paper streamers round it, bare spreading twigs carrying the '
     'last yellow and russet leaves, fallen leaves under it, inside a low vermilion shrine fence on a stone '
     'kerb with a white name board lettered u-me. The fence row is solid; you walk behind the crown.'),
    ('fukuoka-lattice-cafe_0_0', lattice_cafe, (4, 4), DZ, dict(
        door=[[1, 3], [2, 3]], solid=rows(4, 2, 3),
        lit=[[2.0, 3.0, WARM_C, 1.4, 0.8], [2.0, 2.2, WARM_C, 1.6, 0.25]]),
     'An invented cafe on the approach behind the famous woven facade: under a shallow standing-seam roof '
     'of weathered bronze (not the lane\'s tile) its whole face is three layers of diagonal cedar sticks, '
     'each layer finer, darker and set further back than the last, stepping in like a tunnel to a pair of '
     'glass doors with the lamplit room behind. Its only sign is a plain cedar board hung from the eave, '
     'lettered CAFE: no roundel, no cup, no brand mark. The glass doors span the two middle cells.'),
    ('fukuoka-stone-lantern_0_0', stone_lantern, (1, 2), DZ, dict(
        solid=[[0, 1]], lit=[[0.5, 0.78, WARM_C, 0.7, 0.6]]),
     'A tall kasuga-style stone lantern for the approach: mossed granite, a jewel, a six-sided roof with '
     'upturned corners, a lit fire box, a banded shaft. In pairs down the lane.'),
    ('fukuoka-ox-statue_0_0', ox_statue, (2, 2), DZ, dict(solid=rows(2, 1, 1)),
     "The shrine's bronze ox (goshingyu) lying on a granite block with a plum crest: dark bronze, its head, "
     'muzzle and horn rubbed bright by visitors, a red and white rope at its neck. Faces west.'),
    ('fukuoka-hedge_0_0', lambda: hedge('ew'), (1, 1), DZ, dict(solid=[[0, 0]]),
     'A clipped sasanqua hedge, running east-west: dark green, a few pink and white flowers (it blooms in '
     'November), its lit top from above and its shaded south face. One cell; tiles left-right. Hedge '
     "Dazaifu's court with it so the way in is through the torii."),
    ('fukuoka-hedge-v_0_0', lambda: hedge('ns'), (1, 1), DZ, dict(solid=[[0, 0]]), 'The hedge running north-south.'),
    ('fukuoka-hedge-corner-nw_0_0', lambda: hedge('es'), (1, 1), DZ, dict(solid=[[0, 0]]),
     "The hedge's north-west corner (it joins east and south)."),
    ('fukuoka-hedge-corner-ne_0_0', lambda: hedge('ws'), (1, 1), DZ, dict(solid=[[0, 0]]),
     "Its north-east corner (joins west and south)."),
    ('fukuoka-hedge-corner-sw_0_0', lambda: hedge('en'), (1, 1), DZ, dict(solid=[[0, 0]]),
     "Its south-west corner (joins east and north)."),
    ('fukuoka-hedge-corner-se_0_0', lambda: hedge('wn'), (1, 1), DZ, dict(solid=[[0, 0]]),
     "Its south-east corner (joins west and north)."),
    ('fukuoka-hedge-end-e_0_0', lambda: hedge('w'), (1, 1), DZ, dict(solid=[[0, 0]]),
     'The east end of an east-west hedge (a gap for a gate).'),
    ('fukuoka-hedge-end-w_0_0', lambda: hedge('e'), (1, 1), DZ, dict(solid=[[0, 0]]), 'The west end of an east-west hedge.'),
    ('fukuoka-hedge-end-n_0_0', lambda: hedge('s'), (1, 1), DZ, dict(solid=[[0, 0]]), 'The north end of a north-south hedge.'),
    ('fukuoka-hedge-end-s_0_0', lambda: hedge('n'), (1, 1), DZ, dict(solid=[[0, 0]]), 'The south end of a north-south hedge.'),
]
FAMILIES = [
    ('fukuoka-station-plaza-autotile', HS,
     "The station forecourt's paving: pale granite squares laid as a pinwheel round small charcoal insets "
     "(the station's own tile), a pale kerb."),
    ('fukuoka-riverwalk-autotile', NK,
     "Nakasu's river promenade, in place of the grey brick: dusky mauve brick laid in herringbone, a pale "
     'granite kerb. Under the yatai and along the bank.'),
    ('fukuoka-canal-paving-autotile', CC,
     "Canal City's plaza: warm ochre setts laid in fans, a cream and terracotta border (the mall's own "
     'colours). In place of the brown brick that renders grey.'),
    ('fukuoka-beach-autotile', MO,
     "Momochi's beach: pale sand in wind ripples with the odd shell, a low concrete promenade lip with "
     'sand blown over it where the beach ends (so include the wet-sand cells in the region you autotile, '
     'then lay the wet-sand tiles over them). In place of sand-autotile, which is dirt recoloured with a '
     'grass fringe.'),
]
def _shore_desc(kind, shape):
    side = {'e': 'east', 'w': 'west', 'n': 'north', 's': 'south'}
    diag = {'ne': 'north-east', 'nw': 'north-west', 'se': 'south-east', 'sw': 'south-west'}
    opp = {'ne': 'sw', 'nw': 'se', 'se': 'nw', 'sw': 'ne'}
    what = ('The wet edge of the beach: the glassy swash, the foam line, a narrow band of darker, cooler wet '
            'sand, then dry sand. Opaque, walkable.' if kind == 'wet' else
            "Ankle-deep water over sand: pale by the foam, deepening to pond-autotile's own blue, lines of "
            'small waves along the shore. Opaque, WALKABLE (you can paddle); its seaward side meets '
            'pond-autotile_center.')
    tail = shape.split('-')[-1]
    if shape in side:
        where = f'LAND TO THE {side[shape].upper()} (a straight waterline).'
    elif shape.startswith('outer'):
        where = (f'A point of the beach: land only toward the {diag[tail]}, sea on the two opposite sides'
                 + (' (the wet band turns the corner).' if kind == 'wet' else
                    ' (this is the diagonal cell off the point: the waves bend round it).'))
    else:
        where = (f"A cove's corner: land on every side but the {diag[opp[tail]]}"
                 + (' (the diagonal cell, sea only at its corner).' if kind == 'wet' else
                    ' (the water runs into the corner of the beach).'))
    return f'{where} {what}'


for _kind, _name in (('wet', 'fukuoka-wet-sand'), ('shallows', 'fukuoka-shallows')):
    for _shape in SHORE_SHAPES:
        PIECES.append((f'{_name}-{_shape}_0_0', (lambda k=_kind, sh=_shape: surf(k, sh)), (1, 1), MO,
                       dict(walk=[[0, 0]], layer='ground'), _shore_desc(_kind, _shape)))
SPRITES = {key: fn for key, fn, *_ in PIECES}
META = {key: m for key, _fn, _size, _district, m, _desc in PIECES}
for _fam, *_ in FAMILIES:
    for _r in ROLES:
        SPRITES[f'{_fam}_{_r}'] = (lambda r=_r, fam=_fam: ground(fam)(r))


def build():
    built = {}
    for key, fn in SPRITES.items():
        im = fn()
        built[key] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    return built


def halo(key):
    """DayNight's own rule for a lamp halo."""
    return 'lamp-post' in key or '-lanterns' in key


def glow_spots(m):
    """A piece's lit parts as the spots src/utils/Glows.js reads; `color` is a
    number, as it is in config.json (0xRRGGBB)."""
    out = []
    for x, y, c, *rest in m.get('lit', []):
        out.append({'x': x, 'y': y, 'r': rest[0] if rest else 0.9, 'color': int(c),
                    'a': rest[1] if len(rest) > 1 else 0.5})
    return out


NOTES = [
    "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per cell "
    "and pixel-doubled, as generate_sapporo_art.py does); 'size' is in cells.",
    'Nothing is registered: config.json, tilePalette, spriteMetadata, tileNames, prefabs, generators, '
    'check_generators.py and docs are untouched, and the tool does not write config.json. To register a '
    'multi-cell sprite follow generate_sapporo_art.register: spriteMetadata {frameCount:1, anchorX: 32/widthPx, '
    "anchorY: 32/heightPx} (centre of the top-left cell; that is 'anchor'); 1x1 tiles use 0.5/0.5. The map "
    'change should also add the tool to check_generators.py.',
    "'doors' (every door cell; 'door' is the first), 'solid' and 'walk_through' are [col,row] from the sprite's "
    "top-left cell. 'solid' is the suggested footprint (rows above it are roof or sky the player walks behind). "
    "'walk_through' lists cells of the sprite's own rows that stay walkable: under the Nakasu gate and the "
    "illumination arch, and the cells of a 'flat' or walkable 'ground' piece (the canal bridge, wet sand, shallows).",
    "Night: 'night_halo' is true for the one key that matches DayNight's /lamp-post|-lanterns/ rule "
    "(fukuoka-river-rail-lanterns). 'glow' is each other sprite's lit parts as glow spots in the shape "
    "src/utils/Glows.js reads ({x, y, r, color, a}: centre in cells from the sprite's top-left, radius in cells; "
    "'color' is a NUMBER, 0xRRGGBB): copy the list into the sprite's spriteMetadata `glow` when it is registered. "
    'All of it was checked only in the Pillow night previews (previews.night), NOT in the running game; the '
    'shop-window spots came out faint there and may want a higher `a`.',
    'Season: mid November (the posts are 8-12 Nov 2025): no snow anywhere; the Christmas market and '
    'illuminations are going up at the station; the roof garden has a few turned trees; the hedge is sasanqua, '
    'which flowers in November. plum-tree_0_0 (in blossom) and the sakura are wrong for the month and are NOT '
    'redrawn here: a bare or autumn plum is still wanted.',
    'All sign words are generic or invented: HAKATA, NAKASU / na-ka-su (place names), ra-a-me-n, to-n-ko-tsu, '
    'me-n-ta-i-ko, ha-ka-ta o-ri, se-n-be-i, u-me mo-chi in kana, dai-butsu (great buddha) in two hand-set kanji, '
    'WINE, WURST, XMAS, BAR, CLUB, PUB, DARTS, SAKE, ALE, CAFE, BEACH CAFE, and THE OLD OAK (an invented pub '
    'name). No real brand artwork and no brand in any key: the lattice cafe carries only a cup.',
    'New keys only, all prefixed fukuoka-; generate_fukuoka_art.py and its sprites are untouched. NOT redrawn '
    'because they are already their own: the tower, the three yatai and yatai-lanterns, the Yamakasa float, the '
    'fountain, the Dazaifu hall and bridge, and canal-city_0_0 - it is a curved terracotta mall with a wide '
    'arched entrance already; for the atrium interior its door cells are [3,5] and [4,5] (the arch, read off '
    "the 8x6 sprite in a preview, not measured to the pixel). Kushida's hall is still the stock shrine-red: "
    'not in this brief, still wanted.',
    'Replaces: the townhouse station (fukuoka-hakata-station), the machiya (the ori and senbei fronts), the '
    'small pagoda (fukuoka-tochoji-hall), grey brick under the yatai (fukuoka-riverwalk-autotile), brown brick '
    'at Canal City (fukuoka-canal-paving-autotile), light concrete at the station (fukuoka-station-plaza-'
    'autotile), sand-autotile and the three beach-shore tiles (fukuoka-beach-autotile + wet-sand + shallows).',
    'Hakata-bei wall: an east-west run is fukuoka-hakata-bei tiles (1x2, foot cell solid), ended at a gateway '
    'by -stop-e / -stop-w. The pieces of a north-south run are 1x3 with the BOTTOM cell solid, because a wall '
    'seen end-on shows only its tiled cap, drawn a cell and a half up the map from where it stands: where an '
    "east-west run turns north use -corner-e / -corner-w on the run's own row and stack -v in the rows above; "
    'a run going south from an east-west wall is -v from the next row down, ended with -end. The topmost -v of '
    'a run has no ink line across its top (the pieces are cut to stack without a seam).',
    'Beach: there are shore pieces for land to the east, north and south only, and NO corner pieces: keep the '
    "waterline straight (the town's coast runs north-south) or end it against something. Seaward order is "
    'fukuoka-beach-autotile, fukuoka-wet-sand-*, fukuoka-shallows-*, then pond-autotile_center. Autotile the '
    'beach over the wet-sand cells too, then overwrite them, or the beach draws its promenade lip at the waterline.',
    'Canal: every canal piece is 1x2 and opaque, laid in one east-west row: -end-w, runs of fukuoka-canal and '
    '-jets, -end-e; fukuoka-canal-bridge replaces one canal cell and is walked north-south. The water is teal '
    'on purpose and does not join pond-autotile.',
    'Hedge: ten 1x1 pieces that join on cell edges (straight, -v, four corners named for the corner of the '
    'enclosure they make, four ends). A gap in a run is -end-e ... -end-w.',
    'Stalls (the three market huts, the umegae-mochi stall) have no door cell: they are counters.',
]


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
        assert all(0 <= c < w and 0 <= r < h for c, r in solid + m.get('walk', [])), key
        sprites.append({
            'key': key, 'file': f'gamev2/{SPR}/{key}.png', 'size': [w, h], 'px': list(im.size),
            'anchor': [round(32 / im.width, 6), round(32 / im.height, 6)],
            'door': doors[0] if doors else None, 'doors': doors,
            'solid': solid, 'walk_through': m.get('walk', []),
            'night_halo': halo(key),
            'glow': glow_spots(m),
            'layer': m.get('layer', 'standing'),
            'district': district, 'description': desc,
        })
    doc = {
        'tool': 'gamev2/tools/generate_fukuoka_town_art.py',
        'run': 'cd gamev2 && python3 tools/generate_fukuoka_town_art.py [--sheet out.png] [--scenes dir] [--manifest out.json]'
               '   (a python3 with Pillow; imports generate_hokkaido, generate_sendai_art, generate_sapporo_art, '
               'generate_kanazawa_art, generate_sendai_town_art from tools/)',
        'notes': NOTES,
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/fukuoka_art_sheet.png',
            'scenes': [f'.agent-queue/shots/fukuoka_art_{n}.png' for n in SCENES],
            'night': [f'.agent-queue/shots/fukuoka_art_{n}_night.png' for n in SCENES],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


def shore_pieces(land, sea):
    """Which shore piece goes on which cell: {(x, y): key}. `land` is the set
    of beach cells, `sea` the set of water cells. A beach cell that touches
    water (by a side or a corner) becomes wet sand; a water cell that touches
    wet sand becomes shallows. One sea side -> the edge named for the side the
    land is on; two -> outer-XX; only a corner -> inner-XX (and the reverse
    for the water cells)."""
    out = {}
    wet = {c for c in land if any((c[0] + dx, c[1] + dy) in sea for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
    for (x, y) in wet:
        ew = ('e' if (x - 1, y) in sea else '') or ('w' if (x + 1, y) in sea else '')
        ns = ('s' if (x, y - 1) in sea else '') or ('n' if (x, y + 1) in sea else '')
        if ew and ns:
            shape = f'outer-{ns}{ew}'
        elif ew or ns:
            shape = ew or ns
        else:
            shape = 'inner-' + next(n for n, (dx, dy) in (('ne', (-1, 1)), ('nw', (1, 1)), ('se', (-1, -1)), ('sw', (1, -1)))
                                    if (x + dx, y + dy) in sea)
        out[(x, y)] = f'fukuoka-wet-sand-{shape}_0_0'
    for (x, y) in sea:
        if not any((x + dx, y + dy) in wet for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        ew = ('e' if (x + 1, y) in wet else '') or ('w' if (x - 1, y) in wet else '')
        ns = ('s' if (x, y + 1) in wet else '') or ('n' if (x, y - 1) in wet else '')
        if ew and ns:
            shape = f'inner-{ns}{ew}'
        elif ew or ns:
            shape = ew or ns
        else:
            shape = 'outer-' + next(n for n, (dx, dy) in (('ne', (1, -1)), ('nw', (-1, -1)), ('se', (1, 1)), ('sw', (-1, 1)))
                                    if (x + dx, y + dy) in wet)
        out[(x, y)] = f'fukuoka-shallows-{shape}_0_0'
    return out


# ---- previews (not part of the game) --------------------------------------------
SCENES = ('station', 'nakasu', 'canalcity', 'oldhakata', 'momochi', 'dazaifu')
GRID = ('corner-nw', 'edge-n', 'corner-ne', 'edge-w', 'center', 'edge-e', 'corner-sw', 'edge-s', 'corner-se')


def spr(name):
    return Image.open(f'{SPR}/{name}.png').convert('RGBA')


class Scene:
    def __init__(self, built, w, h, ground_='grass-autotile_center'):
        self.b, self.w, self.h = built, w, h
        self.im = Image.new('RGBA', (w * 64, h * 64), CLEAR)
        if ground_:
            g = self.get(ground_)
            for y in range(h):
                for x in range(w):
                    self.im.alpha_composite(g, (x * 64, y * 64))
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

    def fill(self, name, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.im.alpha_composite(self.get(name), (x * 64, y * 64))

    def flat(self, name, x, y):
        """A flat piece with its top-left cell at (x, y), under everything standing."""
        self.im.alpha_composite(self.get(name), (x * 64, y * 64))

    def shore(self, land, sea):
        """Lay the shore between `land` (beach cells) and `sea` (water cells):
        shore_pieces() is the rule a map generator would use."""
        for (x, y), name in sorted(shore_pieces(land, sea).items()):
            self.flat(name, x, y)

    def road(self, y, x0, x1):
        for x in range(x0, x1 + 1):
            self.flat('road-edge-top_0_0', x, y)
            self.flat('road-div-horizontal_0_0', x, y + 1)
            self.flat('road-edge-bottom_0_0', x, y + 2)

    def put(self, name, x, base):
        """Stand a sprite with its left edge on cell x and its feet on row `base`."""
        self.things.append((base, x, name))

    def render(self):
        halos = []
        for base, x, name in sorted(self.things):
            im = self.get(name)
            top = (base + 1) * 64 - im.height
            self.im.alpha_composite(im, (x * 64, top))
            for spot in glow_spots(META.get(name, {})):
                halos.append((x * 64 + spot['x'] * 64, top + spot['y'] * 64, spot['r'] * 64, spot['color'], spot['a']))
            if halo(name):                                        # DayNight's own lamp halo, on the top cell
                halos.append((x * 64 + 32, top + 32 - 64 * 0.15, 64 * 1.6, 0xffb366, 1.0))
        self.things = []
        return halos

    def save(self, out):
        halos = self.render()
        self.im.save(out)
        print('scene ->', out, self.im.size)
        night(self.im, halos).save(out[:-4] + '_night.png')


def sheet(built, out):
    """Everything on one sheet at the file's size, doubled: the single pieces
    in rows, then each ground family as a 3x3 patch, then the families that
    only make sense assembled."""
    skip = ('hakata-bei', 'hedge', 'canal', 'wet-sand', 'shallows', 'river-rail')
    keys = [k for k, *_ in PIECES if not any(s in k for s in skip)]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1720 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + 64 * 4 + 64 * 10 + 80
    im = Image.new('RGBA', (1760, H), rgb('e9eef6'))
    y = 20
    for r in lines:
        h = max(built[k].height for k in r)
        x = 20
        for k in r:
            im.alpha_composite(built[k], (x, y + h - built[k].height))
            x += built[k].width + 24
        y += h + 40
    x = 20
    for fam, *_ in FAMILIES:                                      # each family as a 3x3 patch
        for i, r in enumerate(GRID):
            im.alpha_composite(built[f'{fam}_{r}'], (x + (i % 3) * 64, y + (i // 3) * 64))
        x += 3 * 64 + 24
    y += 64 * 4
    assembled(built, im, y)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


def assembled(built, im, y):
    B, H = 'fukuoka-hakata-bei', 'fukuoka-hedge'
    # the wall: a court's south side with both corners and a gateway, runs going north; a free run and its end
    s = Scene(built, 9, 7, None)
    s.put(f'{B}-corner-w_0_0', 0, 6); s.put(f'{B}-corner-e_0_0', 6, 6)
    for x_, n in ((1, ''), (2, '-stop-e'), (4, '-stop-w'), (5, '')):
        s.put(f'{B}{n}_0_0', x_, 6)
    for b in (5, 4, 3):
        n = '-top' if b == 3 else '-v'
        s.put(f'{B}{n}_0_0', 0, b); s.put(f'{B}{n}_0_0', 6, b)
    s.put(f'{B}-top_0_0', 8, 4); s.put(f'{B}-v_0_0', 8, 5); s.put(f'{B}-end_0_0', 8, 6)
    s.render()
    im.alpha_composite(s.im, (20, y))
    # the hedge: a ring with a gap, a free north-south length
    x0 = 20 + 9 * 64 + 40
    s = Scene(built, 8, 5, None)
    s.put(f'{H}-corner-nw_0_0', 0, 0); s.put(f'{H}-corner-ne_0_0', 5, 0)
    s.put(f'{H}-corner-sw_0_0', 0, 3); s.put(f'{H}-corner-se_0_0', 5, 3)
    for x_ in range(1, 5):
        s.put(f'{H}_0_0', x_, 0)
    s.put(f'{H}-end-e_0_0', 1, 3); s.put(f'{H}-end-w_0_0', 4, 3)
    for b in (1, 2):
        s.put(f'{H}-v_0_0', 0, b); s.put(f'{H}-v_0_0', 5, b)
    s.put(f'{H}-end-n_0_0', 7, 0); s.put(f'{H}-v_0_0', 7, 1); s.put(f'{H}-v_0_0', 7, 2); s.put(f'{H}-end-s_0_0', 7, 3)
    s.render()
    im.alpha_composite(s.im, (x0, y))
    # the railing
    for i in range(6):
        k = 'fukuoka-river-rail-lanterns_0_0' if i in (1, 4) else 'fukuoka-river-rail_0_0'
        im.alpha_composite(built[k], (x0 + i * 64, y + 6 * 64 - built[k].height))
    # the canal
    x1 = x0 + 8 * 64 + 40
    for i, k in enumerate(('-end-w', '', '-jets', '-bridge', '-jets', '-end-e')):
        im.alpha_composite(built[f'fukuoka-canal{k}_0_0'], (x1 + i * 64, y))
    # the shore: a coast with a spit of sand and a cove, so every kind of piece shows
    s = Scene(built, 8, 7, 'pond-autotile_center')
    land = ({(x_, y_) for x_ in range(5, 8) for y_ in range(7)} | {(x_, y_) for x_ in (2, 3, 4) for y_ in (0, 1)}
            | {(x_, y_) for x_ in (3, 4) for y_ in (4, 5, 6)})
    sea = {(x_, y_) for x_ in range(8) for y_ in range(7)} - land
    for c in land:
        s.fill('fukuoka-beach-autotile_center', c[0], c[1], c[0], c[1])
    s.shore(land, sea)
    im.alpha_composite(s.im, (x1, y + 3 * 64))


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    # Hakata Station: the station on its forecourt paving, the Christmas market before it - the tree,
    # an arch each side as the way in, three huts - and the ramen and mentaiko shops beside it
    s = Scene(built, 27, 15)
    s.floor('fukuoka-station-plaza-autotile', (0, 6, 26, 11))
    s.road(12, 0, 26)
    s.put('fukuoka-dept-store_0_0', 17, 5); s.put('fukuoka-office_0_0', 23, 5)
    s.put('fukuoka-hakata-station_0_0', 7, 5)
    s.put('fukuoka-ramen-shop_0_0', 0, 5); s.put('fukuoka-mentaiko-shop_0_0', 3, 5)
    s.put('fukuoka-xmas-tree_0_0', 10, 9)
    s.put('fukuoka-illumination-arch_0_0', 6, 9); s.put('fukuoka-illumination-arch_0_0', 14, 9)
    s.put('fukuoka-xmas-hut-wine_0_0', 2, 10); s.put('fukuoka-xmas-hut-wurst_0_0', 17, 9)
    s.put('fukuoka-xmas-hut-gifts_0_0', 21, 11)
    s.put('blue-lamp-post_0_0', 0, 11); s.put('blue-lamp-post_0_0', 26, 8)
    for x, y in ((11, 6), (9, 10), (13, 10), (7, 9), (15, 9), (3, 11), (18, 10), (2, 6), (4, 6), (16, 11), (11, 14), (19, 6), (25, 6), (22, 12)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_station.png')
    # Nakasu: the yatai that are already there on the herringbone promenade, the railing with its
    # lantern posts along the river, the gate sign at the street's mouth, the bar building and the pub
    s = Scene(built, 24, 14)
    s.floor('fukuoka-riverwalk-autotile', (0, 5, 23, 9))
    s.fill('pond-autotile_center', 0, 11, 23, 13)
    s.fill('pond-autotile_edge-n', 0, 11, 23, 11)
    s.put('fukuoka-neon-bar_0_0', 0, 5); s.put('fukuoka-pub_0_0', 6, 5)
    s.put('fukuoka-nakasu-gate_0_0', 10, 6)
    s.put('fukuoka-motsunabe-shop_0_0', 20, 5)
    for i, x in enumerate((1, 5, 14, 18)):
        s.put(('yatai-ramen_0_0', 'yatai-yakitori_0_0', 'yatai-oden_0_0')[i % 3], x, 8)
    s.put('yatai-ramen_0_0', 14, 5); s.put('yatai-oden_0_0', 17, 5)
    for x in range(24):
        s.put('fukuoka-river-rail-lanterns_0_0' if x % 4 == 1 else 'fukuoka-river-rail_0_0', x, 10)
    for x, y in ((10, 7), (11, 9), (3, 9), (7, 9), (16, 9), (20, 9), (5, 6), (22, 6), (13, 6), (9, 9)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_nakasu.png')
    # Canal City: the mall that is already there on the fan paving, a strip of canal with jets and a
    # footbridge across its plaza, the fountain
    s = Scene(built, 20, 13)
    s.floor('fukuoka-canal-paving-autotile', (1, 6, 18, 11))
    s.put('canal-city_0_0', 2, 6)
    s.flat('fukuoka-canal-end-w_0_0', 2, 8)
    for x, k in ((3, ''), (4, '-jets'), (5, '-jets'), (6, '-bridge'), (7, '-jets'), (8, '-jets'), (9, ''), (10, '-bridge'),
                 (11, ''), (12, '-jets'), (13, '')):
        s.flat(f'fukuoka-canal{k}_0_0', x, 8)
    s.flat('fukuoka-canal-end-e_0_0', 14, 8)
    s.put('canal-fountain_0_0', 14, 7)
    s.put('blue-lamp-post_0_0', 1, 11); s.put('blue-lamp-post_0_0', 17, 7)
    for x, y in ((5, 7), (6, 9), (10, 8), (8, 10), (13, 10), (16, 9), (3, 10), (12, 7)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_canalcity.png')
    # Old Hakata: Tochoji's hall in a court walled with Hakata-bei (a gateway in its south side, the
    # wall turning north at both corners), the two merchant fronts and the Yamakasa float on the lane
    B = 'fukuoka-hakata-bei'
    s = Scene(built, 29, 14)
    s.floor('gravel-autotile', (2, 4, 9, 7), (22, 4, 28, 8))
    s.floor('brown-brick-autotile', (0, 9, 28, 10), (5, 8, 6, 8))
    s.put('fukuoka-kushida-hall_0_0', 23, 7)
    s.put('fukuoka-stone-lantern_0_0', 22, 8); s.put('fukuoka-stone-lantern_0_0', 28, 8)
    s.put('fukuoka-tochoji-hall_0_0', 3, 5)
    s.put(f'{B}-corner-w_0_0', 1, 8); s.put(f'{B}-corner-e_0_0', 10, 8)
    for x in (2, 3, 8, 9):
        s.put(f'{B}_0_0', x, 8)
    s.put(f'{B}-stop-e_0_0', 4, 8); s.put(f'{B}-stop-w_0_0', 7, 8)
    for y in range(2, 8):
        n = '-top' if y == 2 else '-v'
        s.put(f'{B}{n}_0_0', 1, y); s.put(f'{B}{n}_0_0', 10, y)
    s.put('fukuoka-stone-lantern_0_0', 2, 7); s.put('fukuoka-stone-lantern_0_0', 9, 7)
    s.put('fukuoka-hakata-ori-shop_0_0', 12, 8); s.put('fukuoka-senbei-shop_0_0', 16, 8)
    s.put('hakata-yamakasa_0_0', 20, 8)
    for x in range(0, 29):
        if x not in (10, 11, 12):
            s.put(f'{B}_0_0', x, 12)
    s.put(f'{B}-stop-e_0_0', 9, 12); s.put(f'{B}-stop-w_0_0', 13, 12)
    for x, y in ((5, 7), (6, 9), (4, 6), (13, 9), (17, 9), (19, 10), (9, 10), (11, 11), (1, 10), (25, 8), (24, 10)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_oldhakata.png')
    # Momochi: the tower that is already there at the head of a real beach - sand, the wet edge, the
    # shallows, the sea - with the cafe, parasols and the lifeguard's chair
    s = Scene(built, 20, 16)
    sea = ({(x, y) for x in range(4) for y in range(16)} | {(x, y) for x in range(4, 13) for y in (6, 7, 8)}
           | {(x, y) for x in (4, 5) for y in (11, 12)})         # the bay, the river's mouth, a cove
    land = {(x, y) for x in range(4, 13) for y in range(14)} - sea
    s.floor('light-concrete-autotile', (13, 0, 19, 15), (4, 14, 12, 15))
    s.floor('fukuoka-beach-autotile', (4, 0, 12, 5))
    s.floor('fukuoka-beach-autotile', (4, 9, 12, 13))
    for x, y in sorted(sea):
        s.fill('pond-autotile_center', x, y, x, y)
    s.shore(land, sea)
    s.put('fukuoka-tower_0_0', 14, 13)
    s.put('fukuoka-beach-house_0_0', 8, 3)
    s.put('fukuoka-lifeguard-chair_0_0', 5, 4)
    s.put('fukuoka-beach-umbrella-a_0_0', 9, 5); s.put('fukuoka-beach-umbrella-b_0_0', 10, 11)
    s.put('fukuoka-beach-umbrella-a_0_0', 7, 12); s.put('fukuoka-beach-umbrella-b_0_0', 8, 10)
    s.put('blue-lamp-post_0_0', 13, 5); s.put('blue-lamp-post_0_0', 13, 12)
    for x, y in ((11, 4), (3, 2), (4, 3), (7, 5), (6, 10), (12, 12), (5, 13), (3, 10), (15, 14), (4, 12), (8, 7)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_momochi.png')
    # Dazaifu: the approach lane between the umegae-mochi stall and the lattice cafe, stone lanterns
    # down it, then the hedge with its one gap at the torii, the ox, and the hall, bridge and plum
    # trees that are already there
    H = 'fukuoka-hedge'
    s = Scene(built, 20, 18)
    s.floor('gravel-autotile', (1, 3, 18, 9))
    s.floor('flat-grey-brick-autotile', (8, 10, 11, 17))
    s.put('dazaifu-hall_0_0', 7, 5)
    s.put('fukuoka-plum-autumn_0_0', 2, 5); s.put('fukuoka-plum-autumn_0_0', 15, 5); s.put('fukuoka-plum-autumn_0_0', 15, 8)
    s.put('fukuoka-ox-statue_0_0', 3, 8)
    s.put('fukuoka-stone-lantern_0_0', 6, 8); s.put('fukuoka-stone-lantern_0_0', 13, 8)
    s.put(f'{H}-corner-nw_0_0', 0, 2); s.put(f'{H}-corner-ne_0_0', 19, 2)
    s.put(f'{H}-corner-sw_0_0', 0, 10); s.put(f'{H}-corner-se_0_0', 19, 10)
    for x in range(1, 19):
        s.put(f'{H}_0_0', x, 2)
        if x < 7 or x > 12:
            s.put(f'{H}_0_0', x, 10)
    s.put(f'{H}-end-e_0_0', 7, 10); s.put(f'{H}-end-w_0_0', 12, 10)
    for y in range(3, 10):
        s.put(f'{H}-v_0_0', 0, y); s.put(f'{H}-v_0_0', 19, y)
    s.put('torii-red-top_0_0', 7, 9); s.put('torii-red-feet_0_0', 8, 11)
    s.put('fukuoka-umegae-stall_0_0', 4, 14); s.put('fukuoka-lattice-cafe_0_0', 13, 15)
    s.put('fukuoka-stone-lantern_0_0', 7, 13); s.put('fukuoka-stone-lantern_0_0', 12, 13)
    s.put('fukuoka-stone-lantern_0_0', 7, 16); s.put('fukuoka-stone-lantern_0_0', 12, 16)
    s.put(f'{H}-end-n_0_0', 2, 14); s.put(f'{H}-v_0_0', 2, 15); s.put(f'{H}-end-s_0_0', 2, 16)
    for x, y in ((9, 12), (10, 15), (5, 15), (15, 16), (9, 7), (5, 8), (11, 9), (14, 9), (9, 17)):
        s.put(me, x, y)
    s.save(f'{outdir}/fukuoka_art_dazaifu.png')


def main():
    built = build()
    for key, im in built.items():
        im.save(f'{SPR}/{key}.png')
        if 'autotile' not in key:
            print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    print(', '.join(f[0] for f in FAMILIES) + f': {len(ROLES)} roles each')
    for flag, fn in (('--sheet', sheet), ('--scenes', scenes), ('--manifest', manifest)):
        if flag in sys.argv:
            fn(built, sys.argv[sys.argv.index(flag) + 1])


if __name__ == '__main__':
    main()
