#!/usr/bin/env python3
"""generate_asahikawa_art.py — draw Asahikawa's own buildings and street pieces (issue #219).

Asahikawa had one sprite of its own (the timber bridge) and a banner; its
station was a cottage and its ramen shops were the machiya every town has.
These are the pieces its four areas are rebuilt from, drawn the way
generate_sapporo_art.py draws Sapporo's: shaded pixel art in the GuttyKreum
palette at half size (one drawn pixel = one pixel of a 32px tile) and
pixel-doubled, lit from the left, a 1px ink outline, all of it in deep snow.
It is a small cold river city, not a small Sapporo: timber and glass, not
brick; steep coloured metal roofs; a green steel bridge; penguins.
Every name on a sign is a look-alike or a generic word; no brand artwork.

Station front and Heiwa-dori (the pedestrian shopping street)
  asahikawa-station-front_0_0  10x5  a wide glass hall with the warm timber
                                     lining showing through the glazing, tree
                                     columns, two pairs of sliding glass doors,
                                     the train hall as a second tier behind
  heiwa-shop-sake_0_0           3x4  a white-walled sake shop: cedar ball,
                                     noren, straw-wrapped casks, namako wall
  heiwa-shop-woodcraft_0_0      4x3  a low timber-clad furniture workshop,
                                     chairs in a lit window
  heiwa-shop-bakery_0_0         3x4  a green false-front bakery / coffee shop
  heiwa-shop-books_0_0          3x3  a slate-tiled second-hand bookshop
  ice-sculpture-crane_0_0       2x2  clear ice (not packed snow, as Sapporo's
  ice-sculpture-owl_0_0         1x2  are): a calling crane, an owl
  heiwa-bench_0_0               2x1  a slatted bench with snow on it
  heiwa-lamp-post_0_0           1x2  a timber post with a lantern box; glows
  heiwa-paving-autotile_*       1x1  granite setts in running bond, a faded
                                     rose one here and there; the snow creeps
                                     over its edges (9 autotile roles)
Ramen alley
  ramen-shoyu-front_0_0         4x4  a shoyu-ramen counter: red board, red
                                     nobori, a lit counter window, steam
  ramen-narrow-front_0_0        2x4  a narrow two-storey ramen shop, upright
                                     yellow sign, stovepipe up the wall
  ramen-miso-front_0_0          3x4  a gabled miso-ramen shop, indigo board
  asahikawa-ramen-gate_0_0      3x3  two posts and a beam hung with four
                                     round paper lanterns; walk through
  asahikawa-ramen-lanterns_0_0  1x2  a post of three round lanterns; glows
  ramen-crates_0_0              1x2  stacked beer crates under snow
  ramen-stockpot_0_0            1x2  a stock pot steaming on a gas ring
  ramen-alley-autotile_*        1x1  wet asphalt and slush (9 autotile roles)
Asahibashi and the riverbank
  asahibashi-deck_0_0           2x5  the deck: a plain grey road, flat, walked
                                     ON; three rows of river under it
  asahibashi-arch-w / -e_0_0    1x5  the green riveted arch ribs (a deep
                                     latticed truss), one each side of the
                                     deck, leaning away from it as seen from
                                     above; never over the deck
  asahibashi-brace_0_0          4x1  one overhead brace between the crowns
                                     (above the player: you walk under it)
  hokkaido-house-red_0_0        3x4  Hokkaido houses: steep coloured metal
  hokkaido-house-blue_0_0       3x4  roofs, snow sliding off, a glazed porch,
                                     a heating-oil tank, chimney smoke
  snow-fence-h_0_0              1x2  a steel louvred snow fence, tiles east-west
  ice-crack-a / -b_0_0          1x1  overlays for the frozen river
  ice-fishing-hole_0_0          1x1  a hole cut in the ice, a stool, a rod
  ice-fishing-tent_0_0          2x2  an orange dome tent on the ice, a sled
Asahiyama Zoo gate
  zoo-gate_0_0                  5x4  timber pylons, a bear and penguins on
                                     them, a blue ASAHI ZOO board, bunting
  zoo-fence-h / -end_0_0        1x2  the zoo's mesh fence, and its end post
  zoo-ticket-booth_0_0          2x3  a kiosk under a green hipped roof
  penguin-walk-a / -b_0_0       2x1  king penguins in a line, mid-waddle
  zoo-seal-statue_0_0           2x2  a spotted seal rearing on a boulder

Writes the PNGs into assets/sprites/ and registers every one in config.json
(spriteMetadata, tileNames, the night glow of the lit pieces, the deck's
depthBias) through tools/art_register.py; tools/generate_asahikawa.py places them.

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs Pillow. Run from gamev2/:
    python3 tools/generate_asahikawa_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageOps

import art_register

from generate_hokkaido import (rgb, canvas, outline, snow_cap, tiles, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, SNOW, SNOW_LO, GLASS, GLASS_HI, GLASS_DK,
                               WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_sapporo_art import (FONT, KANA, glyphs, kana_w, drift, lantern, rows, ROLES,
                                  Scene, spr, _wob, SNOW_SH, SNOW_DK, DARK, WARM, WOOD_HI)

SPR = 'assets/sprites'

TIMBER, TIMBER_HI, TIMBER_LO, TIMBER_DK = rgb('d9a066'), rgb('efc793'), rgb('b47c48'), rgb('7d5233')
CHAR, CHAR_LO, CHAR_HI = rgb('4a3e3c'), rgb('332a2b'), rgb('6a5a55')          # charred cladding
PLASTER, PLASTER_LO, PLASTER_DK = rgb('f1ece4'), rgb('d2c9be'), rgb('a39a92')
BG, BG_HI, BG_LO, BG_DK = rgb('6fa888'), rgb('a6d6b8'), rgb('4a7d64'), rgb('2f5646')   # Asahibashi's green
ICE, ICE_HI, ICE_LO, ICE_DK = rgb('bfe3f6'), rgb('ecf9ff'), rgb('8fc3e6'), rgb('5f9fd0')
ROOF_R, ROOF_R_HI, ROOF_R_LO = rgb('b8463c'), rgb('d4685a'), rgb('8c322d')
ROOF_B, ROOF_B_HI, ROOF_B_LO = rgb('3f6fb0'), rgb('6a97d2'), rgb('2c4f85')
ROOF_G, ROOF_G_HI, ROOF_G_LO = rgb('4f8f6c'), rgb('78b592'), rgb('356650')
KAWARA, KAWARA_LO, KAWARA_HI = rgb('4a5568'), rgb('2f3848'), rgb('6b7890')
ORANGE = rgb('f08a3c')
PEN, PEN_HI = rgb('1f2633'), rgb('3b4a60')

FONT = dict(FONT)
FONT.update({
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
})
KANA = dict(KANA)
KANA.update({
    'pa': ['.....##', '.....##', '..#.#..', '..#.#..', '.#...#.', '.#...#.', '#.....#'],
    'sa': ['..#..#.', '#######', '..#..#.', '..#..#.', '.....#.', '....#..', '..##...'],
    'mi': ['.###...', '....##.', '.###...', '....##.', '.......', '.####..', '.....##'],
    'so': ['#.....#', '#.....#', '.#....#', '.....#.', '....#..', '...#...', '.##....'],
})
KANJI = {
    'asahi': ['..#...#####', '..#...#...#', '#####.#...#', '..#.#.#####', '..#.#.#...#', '..#.#.#...#',
              '.#..#.#####', '.#..#......', '#...#.....#', '#...#.....#', '....#######'],
    'kawa': ['#...#...#', '#...#...#', '#...#...#', '#...#...#', '#...#...#', '#...#...#',
             '#...#...#', '#...#...#', '#...#...#', '#.......#', '#.......#'],
    'sake': ['#..#######', '.#...#.#..', '...#######', '#..#.#.#.#', '.#.#.#.#.#', '...##...##',
             '..##.....#', '.#.#######', '#..#.....#', '#..#######'],
}


def text(d, s, x, y, fill, scale=1, vertical=False):
    glyphs(d, [FONT[c] for c in s], x, y, fill, scale, 1, vertical)


def kana(d, names, x, y, fill, scale=1, vertical=False):
    glyphs(d, [KANA['vbar' if (vertical and n == 'bar') else n] for n in names], x, y, fill, scale, 1, vertical)


def text_w(s, scale=1):
    return (len(s) * 6 - 1) * scale


def kanji(d, names, x, y, fill, scale=1, gap=2):
    glyphs(d, [KANJI[n] for n in names], x, y, fill, scale, gap)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


# ---- surfaces -------------------------------------------------------------------
def boards_v(d, x0, y0, x1, y1, base, lo, hi=None, step=4):
    """Vertical cladding: a board every `step` px, a dark joint, a lit edge."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    for x in range(x0, x1 + 1):
        k = (x - x0) % step
        if k == step - 1:
            d.line([(x, y0), (x, y1)], fill=lo)
        elif k == 0 and hi:
            d.line([(x, y0), (x, y1)], fill=hi)


def boards_h(d, x0, y0, x1, y1, base, lo, hi=None, step=4):
    d.rectangle([x0, y0, x1, y1], fill=base)
    for y in range(y0, y1 + 1):
        k = (y - y0) % step
        if k == step - 1:
            d.line([(x0, y), (x1, y)], fill=lo)
        elif k == 0 and hi:
            d.line([(x0, y), (x1, y)], fill=hi)


def seam_roof(d, scan, base, hi, lo, step=6):
    """A standing-seam metal roof over (y, x0, x1) scanlines: a seam every
    `step` px with a lit flank, the lowest rows in the eave's shade."""
    ys = [y for y, _, _ in scan]
    for y, x0, x1 in scan:
        for x in range(x0, x1 + 1):
            k = x % step
            c = lo if k == 0 else (hi if k == 1 else base)
            if y >= max(ys) - 1:
                c = lo
            d.point((x, y), fill=c)


def snow_slab(d, x0, x1, y0, y1, seed=0, shade_from=None):
    """Deep snow lying on a roof: a slab from y0 down to a lumpy lower edge
    about y1, white on its crest, blue under its lip and at its right end."""
    for x in range(x0, x1 + 1):
        e = min(x - x0, x1 - x)                                       # rounded shoulders
        sh = (3, 2, 1, 1)[e] if e < 4 and y1 - y0 > 5 else (1 if e == 0 else 0)
        top = y0 - ((x * 5 + seed) % 7 in (0, 1)) + sh
        bot = y1 + ((x * 7 + seed * 5) % 9 in (0, 1, 2)) + ((x * 3 + seed) % 11 == 0) - (e == 0)
        d.line([(x, top), (x, bot)], fill=SNOW)
        d.point((x, top), fill=WHITE); d.point((x, top + 1), fill=WHITE)
        d.point((x, bot), fill=SNOW_SH); d.point((x, bot - 1), fill=SNOW_LO)
        if x > (shade_from if shade_from is not None else x1 - 5):
            d.line([(x, top + 2), (x, bot - 1)], fill=SNOW_LO)


def icicles(d, x0, x1, y, seed=0):
    for x in range(x0, x1 + 1, 3):
        n = (x * 7 + seed * 3) % 5
        if n == 4:
            continue
        d.line([(x, y), (x, y + n)], fill=ICE_HI)
        if n > 1:
            d.point((x, y + n), fill=ICE_LO)


def lit_window(d, x0, y0, x1, y1, frame=WHITE, lit=True, bars=True, curtain=None):
    """A double-glazed house window: a fat frame, a lit or dark pane."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=WARM if lit else GLASS)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=WHITE if lit else GLASS_HI)
    if curtain:
        d.rectangle([x0 + 1, y0 + 2, x0 + 3, y1 - 1], fill=curtain)
        d.rectangle([x1 - 3, y0 + 2, x1 - 1, y1 - 1], fill=curtain)
    if not lit:
        d.line([(x0 + 3, y0 + 3), (x0 + 3, y1 - 3)], fill=GLASS_HI)
    if bars:
        m = (x0 + x1) // 2
        d.line([(m, y0 + 1), (m, y1 - 1)], fill=frame)
    d.line([(x0 - 1, y1 + 1), (x1 + 1, y1 + 1)], fill=frame)          # the sill
    d.line([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], fill=STONE_LO)
    d.line([(x0, y0 - 1), (x1, y0 - 1)], fill=SNOW)                   # snow on its head


def puffs(im, x, y, n=7, seed=0, lean=1, colour=(255, 255, 255), a0=235, grow=3):
    """Steam / smoke, drawn after the outline: soft unoutlined puffs that
    rise from (x, y), drift with the wind and thin out."""
    lay = Image.new('RGBA', im.size, CLEAR)
    ld = ImageDraw.Draw(lay)
    for i in range(n):
        cx = x + int(round(2.2 * math.sin(i * 1.1 + seed))) + (lean * i) // 2
        cy = y - i * 4
        r = 1 + min(grow, (i + 1) // 2)
        a = max(60, a0 - i * 26)
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (a,))
        ld.point((cx - r + 1, cy - r + 1), fill=(255, 255, 255, min(255, a + 20)))
    im.alpha_composite(lay)


def under(im, shapes):
    """Soft blue shadows on the snow, put UNDER the inked sprite."""
    base = Image.new('RGBA', im.size, CLEAR)
    bd = ImageDraw.Draw(base)
    for box in shapes:
        bd.ellipse(box, fill=SNOW_SH[:3] + (150,))
    base.alpha_composite(im)
    return base


def bowl(d, x, y, fill=WHITE, band=RED):
    """A ramen bowl 11px wide with two wisps of steam, its rim on y."""
    d.pieslice([x, y - 6, x + 10, y + 6], 0, 180, fill=fill)
    d.line([(x, y), (x + 10, y)], fill=fill)
    d.line([(x + 1, y + 2), (x + 9, y + 2)], fill=band)
    d.line([(x + 3, y - 2), (x + 3, y - 4)], fill=fill); d.line([(x + 7, y - 2), (x + 7, y - 5)], fill=fill)


# ==============================================================================
# Station front and Heiwa-dori
# ==============================================================================
def wood_glass(d, x0, y0, x1, y1, bay=16, transoms=(), lamps=True, phase=0):
    """A glass wall with the station's timber lining showing through it: a
    slatted ceiling, a boarded wall, pendant lamps, a dim floor; then the sky
    sliding across the panes and the mullions in front."""
    h = y1 - y0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            ry = y - y0
            if ry < h * 0.13:                                         # the slatted ceiling
                c = TIMBER_DK if (x + ry) % 3 == 0 else TIMBER_LO
            elif ry > h * 0.80:                                       # the concourse floor, dim
                c = mix(TIMBER_DK, DARK, 0.35 if (x // 2 + ry) % 5 else 0.15)
            else:
                k = x % 4
                c = TIMBER_LO if k == 3 else (TIMBER_HI if k == 0 else TIMBER)
                if ry > h * 0.62:
                    c = mix(c, TIMBER_DK, 0.35)
            s = (x - x0 + (y - y0) + phase) % 52                      # the sky on the glass
            if s < 9:
                c = mix(c, GLASS_HI, 0.55)
            elif s < 13 or 24 <= s < 28:
                c = mix(c, WHITE, 0.28)
            else:
                c = mix(c, GLASS, 0.20)
            d.point((x, y), fill=c)
    if lamps:
        ly = y0 + int(h * 0.13) + 3
        for x in range(x0 + bay // 2, x1 - 2, bay):
            d.line([(x, y0 + 1), (x, ly - 1)], fill=TIMBER_DK)
            d.rectangle([x - 1, ly, x + 1, ly + 2], fill=WARM)
            d.point((x, ly + 1), fill=WHITE)
            d.point((x - 2, ly + 1), fill=TIMBER_HI); d.point((x + 2, ly + 1), fill=TIMBER_HI)
            d.point((x, ly + 3), fill=TIMBER_HI)
    for x in range(x0, x1 + 1, bay):
        d.line([(x, y0), (x, y1)], fill=STONE_DK)
        if x + 1 <= x1:
            d.line([(x + 1, y0), (x + 1, y1)], fill=mix(STONE, GLASS_HI, 0.4))
    for ty in transoms:
        d.line([(x0, ty), (x1, ty)], fill=STONE_DK)
    d.rectangle([x0, y0, x1, y1], outline=STONE_DK)


def tree_column(d, x, y_top, y_fork, y_foot, spread=15):
    """One of the station's branching columns: a trunk that forks into four
    struts under the roof."""
    for dx in (-spread, -int(spread * 0.4), int(spread * 0.4), spread):
        d.line([(x + 1, y_fork), (x + dx + 1, y_top)], fill=TIMBER_DK, width=2)
        d.line([(x, y_fork), (x + dx, y_top)], fill=PLASTER, width=2)
    d.rectangle([x - 2, y_fork - 1, x + 2, y_foot], fill=PLASTER)
    d.line([(x - 2, y_fork - 1), (x - 2, y_foot)], fill=WHITE)
    d.rectangle([x + 2, y_fork, x + 3, y_foot], fill=PLASTER_DK)
    d.rectangle([x - 3, y_foot - 2, x + 4, y_foot], fill=STONE_LO)


def sliding_doors(d, x0, y0, x1, y1):
    """A pair of automatic sliding glass doors: an operator housing with a
    sensor light, two aluminium-framed leaves of tinted glass (the lit
    concourse beyond, the sky streaking across), a dark split between them
    with a pull on each leaf, kick plates, a dark threshold."""
    m = (x0 + x1 + 1) // 2
    ym = (y0 + y1) // 2
    d.rectangle([x0, y0, x1, y1], fill=STONE_DK)
    d.rectangle([x0, y0, x1, y0 + 4], fill=CHAR)
    d.line([(x0, y0), (x1, y0)], fill=CHAR_HI)
    d.rectangle([m - 2, y0 + 2, m + 1, y0 + 3], fill=rgb('7fd08a'))
    for a, b in ((x0 + 1, m - 2), (m + 1, x1 - 1)):
        for y in range(y0 + 6, y1 - 1):
            for x in range(a, b + 1):
                t = (y - y0) / (y1 - y0)
                c = mix(mix(WARM, TIMBER, 0.1 + 0.5 * t), GLASS, 0.28)
                s = (x - x0 + y) % 30
                if s < 4:
                    c = mix(c, WHITE, 0.65)
                elif s < 6 or 12 <= s < 14:
                    c = mix(c, WHITE, 0.3)
                d.point((x, y), fill=c)
        d.rectangle([a, y0 + 6, b, y1 - 2], outline=STONE)
        d.line([(a, y0 + 6), (a, y1 - 2)], fill=WHITE)
        d.rectangle([a, y1 - 9, b, y1 - 2], fill=STONE)
        d.line([(a, y1 - 9), (b, y1 - 9)], fill=WHITE); d.line([(a, y1 - 2), (b, y1 - 2)], fill=STONE_LO)
        for x in range(a + 3, b - 1, 3):                              # the safety strip across the glass
            d.point((x, ym + 8), fill=WHITE)
    d.rectangle([m - 1, y0 + 5, m, y1], fill=INK)                     # where the leaves meet
    d.rectangle([m - 4, ym - 6, m - 3, ym + 4], fill=WHITE); d.rectangle([m + 2, ym - 6, m + 3, ym + 4], fill=WHITE)
    d.point((m - 3, ym + 4), fill=STONE_LO); d.point((m + 3, ym + 4), fill=STONE_LO)
    d.rectangle([x0, y1 - 1, x1, y1], fill=INK)                       # the threshold


def station_front():
    im, d = canvas(10, 5)                # 320 x 160
    # the train hall behind, set back: a second tier of the same glass under its own roof
    d.rectangle([44, 12, 275, 40], fill=STONE)
    wood_glass(d, 47, 14, 272, 39, bay=12, lamps=False, phase=20)
    d.line([(47, 27), (272, 27)], fill=STONE_DK)
    d.rectangle([40, 8, 279, 12], fill=WHITE)
    d.line([(40, 12), (279, 12)], fill=STONE_LO); d.rectangle([272, 9, 279, 12], fill=STONE)
    snow_slab(d, 40, 279, 4, 7, seed=4)
    # the roof slab: thin, wide, a timber soffit under its overhang
    d.rectangle([0, 44, 319, 49], fill=WHITE)
    d.rectangle([0, 48, 319, 49], fill=STONE)
    d.rectangle([312, 45, 319, 49], fill=STONE)
    for x in range(2, 318):
        d.line([(x, 50), (x, 54)], fill=TIMBER_DK if x % 4 == 3 else (TIMBER if x % 4 == 0 else TIMBER_LO))
    d.line([(2, 54), (317, 54)], fill=TIMBER_DK)
    snow_slab(d, 0, 319, 39, 43, seed=7)
    # timber end walls
    for x0 in (5, 302):
        boards_v(d, x0, 55, x0 + 12, 153, TIMBER, TIMBER_LO, TIMBER_HI, step=4)
        d.line([(x0 + 12, 55), (x0 + 12, 153)], fill=TIMBER_DK)
    d.rectangle([308, 55, 314, 153], fill=TIMBER_LO)
    # the glass wall, the timber lining behind it
    wood_glass(d, 18, 55, 301, 153, bay=16, transoms=(88, 121))
    for x in (50, 98, 221, 269):
        tree_column(d, x, 56, 100, 153, spread=19)
    # the name board over the doors
    d.rectangle([110, 59, 209, 76], fill=DARK)
    d.line([(110, 59), (209, 59)], fill=CHAR_HI); d.line([(110, 76), (209, 76)], fill=INK)
    kanji(d, ('asahi', 'kawa'), 116, 62, WHITE)
    text(d, 'ASAHIKAWA', 146, 64, WARM)
    d.line([(146, 73), (198, 73)], fill=TIMBER)
    # the entrance (cells 4,4 and 5,4): a canopy, two pairs of sliding glass doors, a mat
    d.rectangle([120, 92, 199, 153], fill=STONE_DK)
    d.rectangle([116, 88, 203, 92], fill=WHITE)
    d.line([(116, 92), (203, 92)], fill=STONE_LO); d.rectangle([198, 89, 203, 92], fill=STONE)
    snow_cap(d, 116, 203, 85, 3, seed=2)
    sliding_doors(d, 123, 95, 158, 153)
    sliding_doors(d, 161, 95, 196, 153)
    # a stone plinth, the door mat, a timber bench either side of the doors
    d.rectangle([3, 154, 316, 157], fill=STONE_LO)
    d.line([(3, 154), (316, 154)], fill=STONE)
    d.rectangle([122, 154, 197, 157], fill=CHAR)
    for x in range(124, 197, 3):
        d.line([(x, 155), (x, 156)], fill=CHAR_HI)
    for x in (66, 234):
        d.rectangle([x, 145, x + 19, 147], fill=TIMBER); d.line([(x, 145), (x + 19, 145)], fill=SNOW)
        d.line([(x, 144), (x + 19, 144)], fill=WHITE)
        d.rectangle([x + 1, 148, x + 2, 153], fill=TIMBER_DK); d.rectangle([x + 17, 148, x + 18, 153], fill=TIMBER_DK)
    drift(d, 2, 40, 159, 6, seed=1); drift(d, 280, 317, 159, 6, seed=4)
    drift(d, 74, 118, 159, 3, seed=6); drift(d, 202, 246, 159, 3, seed=8)
    outline(im)
    return im


def komodaru(d, cx, cy, r=8, mark=RED):
    """A straw-wrapped sake cask lying on its side, its round end to you: a
    rope hoop, a white paper face with the brewer's mark, rope ties."""
    straw, straw_lo, straw_hi, rope = rgb('dcc48c'), rgb('a98f5c'), rgb('f1e2b4'), rgb('7a6540')
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=straw)
    d.chord([cx - r, cy - r, cx + r, cy + r], 320, 110, fill=straw_lo)
    d.arc([cx - r, cy - r, cx + r, cy + r], 170, 290, fill=straw_hi)
    d.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2], outline=rope)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=WHITE)
    d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=mark)
    d.point((cx, cy), fill=WHITE)
    for dx, dy in ((-r + 1, -r + 1), (r - 1, -r + 1), (-r + 1, r - 1), (r - 1, r - 1)):   # the rope's knots
        d.point((cx + dx * 7 // 10, cy + dy * 7 // 10), fill=rope)


def shop_sake():
    im, d = canvas(3, 4)                 # 96 x 128
    # the main roof, eaves to the street, dark tile under deep snow
    scan = [(y, 6 - (y - 26) // 4, 89 + (y - 26) // 4) for y in range(26, 50)]
    tiles(d, scan, KAWARA, KAWARA_LO, step=4)
    for y, x0, x1 in scan:
        d.point((x0, y), fill=KAWARA_HI); d.point((x1, y), fill=KAWARA_LO)
    d.rectangle([1, 50, 94, 51], fill=KAWARA_LO)
    snow_slab(d, 6, 89, 22, 29, seed=3, shade_from=80)
    d.rectangle([12, 21, 83, 23], fill=KAWARA_LO)                       # the ridge shows through
    snow_slab(d, 14, 81, 18, 20, seed=5, shade_from=74)
    for x in range(10, 88, 9):                                          # snow caught on the tiles lower down
        d.line([(x, 36 + (x % 4)), (x + 3 + x % 3, 36 + (x % 4))], fill=SNOW)
    icicles(d, 3, 92, 52, seed=2)
    # the upper wall: white plaster, a name board
    d.rectangle([8, 52, 87, 72], fill=PLASTER)
    d.rectangle([8, 52, 87, 54], fill=PLASTER_DK)
    d.rectangle([82, 55, 87, 72], fill=PLASTER_LO)
    d.rectangle([13, 57, 82, 70], fill=TIMBER_HI)
    d.rectangle([13, 57, 82, 70], outline=WOOD_LO)
    d.line([(14, 58), (81, 58)], fill=WHITE)
    kanji(d, ('sake',), 17, 59, INK)
    text(d, 'SAKAGURA', 31, 60, DARK)
    # the pent roof over the shop front
    scan = [(y, 3 - (y - 73) // 2, 92 + (y - 73) // 2) for y in range(73, 80)]
    tiles(d, scan, KAWARA, KAWARA_LO, step=3)
    d.line([(0, 80), (95, 80)], fill=KAWARA_LO)
    snow_slab(d, 2, 93, 70, 73, seed=8, shade_from=82)
    # the ground floor: plaster over a namako (tile and white lattice) dado
    d.rectangle([6, 81, 89, 123], fill=PLASTER)
    d.rectangle([6, 81, 89, 83], fill=PLASTER_DK)
    d.rectangle([84, 84, 89, 123], fill=PLASTER_LO)
    for y in range(105, 124):
        for x in range(6, 90):
            on = (x + y) % 8 == 0 or (x - y) % 8 == 0
            d.point((x, y), fill=PLASTER if on else (KAWARA_LO if x > 83 else KAWARA))
    d.line([(6, 104), (89, 104)], fill=PLASTER_DK)
    # a slatted window, lamplit
    d.rectangle([10, 87, 33, 102], fill=WOOD_DK)
    d.rectangle([11, 88, 32, 101], fill=WARM)
    for x in range(12, 33, 3):
        d.line([(x, 88), (x, 101)], fill=WOOD_LO)
    d.line([(11, 94), (32, 94)], fill=WOOD_LO)
    # the doorway (cell 1,3): a navy noren, a lit sliding door
    d.rectangle([37, 84, 58, 123], fill=WOOD_DK)
    d.rectangle([39, 86, 56, 123], fill=mix(WARM, WOOD, 0.3))
    for x in range(41, 56, 4):
        d.line([(x, 100), (x, 123)], fill=WOOD_LO)
    d.line([(39, 110), (56, 110)], fill=WOOD_LO)
    d.rectangle([47, 86, 48, 123], fill=WOOD_DK)
    for i, x in enumerate(range(39, 57, 6)):
        d.rectangle([x, 86, x + 4, 99], fill=NAVY)
        d.line([(x, 86), (x, 99)], fill=rgb('2c3d80'))
        d.rectangle([x + 1, 91, x + 3, 93], fill=WHITE); d.point((x + 2, 92), fill=NAVY)
    # the cedar ball under the eave
    d.line([(48, 76), (48, 79)], fill=INK)
    d.rectangle([44, 73, 52, 75], fill=WOOD_DK); d.line([(43, 72), (53, 72)], fill=SNOW)
    d.ellipse([41, 77, 55, 91], fill=rgb('6c7a44'))
    d.chord([41, 77, 55, 91], 300, 110, fill=rgb('4c5830'))
    d.arc([42, 78, 54, 90], 180, 290, fill=rgb('93a35c'))
    for k in range(9):
        px_, py_ = 43 + (k * 5) % 11, 79 + (k * 7) % 11
        if (px_ - 48) ** 2 + (py_ - 84) ** 2 < 36:
            d.point((px_, py_), fill=rgb('93a35c') if k % 2 else rgb('3d4728'))
    # casks stacked by the door, snow on the top one
    komodaru(d, 69, 114); komodaru(d, 85, 114, mark=NAVY)
    komodaru(d, 77, 100)
    d.chord([70, 89, 84, 97], 180, 360, fill=SNOW); d.line([(73, 90), (81, 90)], fill=WHITE)
    drift(d, 2, 36, 127, 5, seed=3); drift(d, 58, 94, 127, 3, seed=5)
    outline(im)
    return im


def chair(d, x, y, c=TIMBER, lo=TIMBER_DK):
    """A spindle-back chair, side on, its feet on y (11 wide, 19 tall)."""
    d.line([(x + 1, y - 18), (x + 1, y)], fill=lo, width=2)
    for k in range(3):
        d.line([(x + 2, y - 16 + k * 3), (x + 4, y - 16 + k * 3)], fill=c)
    d.rectangle([x + 1, y - 9, x + 10, y - 8], fill=c)
    d.line([(x + 9, y - 7), (x + 10, y)], fill=lo)
    d.line([(x + 3, y - 4), (x + 9, y - 4)], fill=lo)


def shop_woodcraft():
    im, d = canvas(4, 3)                 # 128 x 96
    # a flat roof: a dark metal parapet, snow lying on it
    d.rectangle([3, 12, 124, 18], fill=CHAR)
    d.line([(3, 12), (124, 12)], fill=CHAR_HI); d.rectangle([3, 17, 124, 18], fill=CHAR_LO)
    snow_slab(d, 3, 124, 7, 11, seed=6)
    # the upper band: horizontal timber cladding and a carved board
    boards_h(d, 5, 19, 122, 42, TIMBER, TIMBER_LO, TIMBER_HI, step=4)
    d.rectangle([117, 19, 122, 42], fill=TIMBER_LO)
    d.rectangle([18, 22, 109, 39], fill=CHAR)
    d.rectangle([18, 22, 109, 23], fill=CHAR_HI); d.line([(18, 39), (109, 39)], fill=CHAR_LO)
    chair(d, 23, 37, TIMBER_HI, TIMBER)
    text(d, 'KAGU', 40, 27, TIMBER_HI)
    d.rectangle([66, 30, 68, 31], fill=TIMBER)
    text(d, 'CRAFT', 73, 27, WHITE)
    # the ground floor: charred posts, one long lit window, a door (cell 3,2)
    d.rectangle([5, 43, 122, 91], fill=CHAR)
    d.rectangle([5, 43, 122, 45], fill=CHAR_LO)
    d.rectangle([9, 48, 89, 86], fill=WOOD_DK)
    d.rectangle([10, 49, 88, 85], fill=WARM)
    d.rectangle([10, 49, 88, 50], fill=WHITE)
    d.rectangle([10, 78, 88, 85], fill=TIMBER_HI)                   # the showroom floor
    d.line([(10, 78), (88, 78)], fill=TIMBER)
    # in the window: a chair, a table with a lamp, a tall shelf, a stool
    chair(d, 15, 80)
    d.rectangle([32, 66, 54, 67], fill=TIMBER_LO); d.line([(32, 66), (54, 66)], fill=TIMBER)
    d.line([(34, 68), (33, 80)], fill=TIMBER_DK); d.line([(52, 68), (53, 80)], fill=TIMBER_DK)
    d.rectangle([41, 60, 44, 65], fill=RED); d.line([(42, 56), (42, 59)], fill=GREEN); d.point((44, 57), fill=GREEN)
    d.rectangle([62, 54, 76, 80], fill=TIMBER_LO)
    for sy in (54, 62, 70, 80):
        d.line([(62, sy), (76, sy)], fill=TIMBER_DK)
    d.line([(62, 54), (62, 80)], fill=TIMBER_DK); d.line([(76, 54), (76, 80)], fill=TIMBER_DK)
    for k, (bx, by) in enumerate(((64, 61), (68, 61), (72, 61), (65, 69), (71, 69), (66, 79), (70, 79))):
        d.rectangle([bx, by - 4, bx + 2, by], fill=(RED, GREEN_HI, WHITE, NAVY, GOLD)[k % 5])
    d.rectangle([80, 72, 86, 73], fill=TIMBER_LO); d.line([(81, 74), (80, 80)], fill=TIMBER_DK)
    d.line([(85, 74), (86, 80)], fill=TIMBER_DK)
    for x in (47,):                                                   # a pendant lamp
        d.line([(x, 51), (x, 54)], fill=WOOD_DK); d.polygon([(x - 3, 58), (x, 54), (x + 3, 58)], fill=CHAR)
        d.line([(x - 2, 59), (x + 2, 59)], fill=WHITE)
    for x in (36, 62):                                                # the window's posts
        d.rectangle([x, 49, x + 1, 85], fill=WOOD_DK)
    d.rectangle([98, 50, 117, 91], fill=WOOD_DK)                      # the door
    d.rectangle([100, 52, 115, 91], fill=TIMBER)
    d.line([(100, 52), (100, 91)], fill=TIMBER_HI)
    d.rectangle([103, 56, 112, 74], fill=WARM); d.line([(103, 56), (112, 56)], fill=WHITE)
    d.rectangle([113, 72, 114, 78], fill=CHAR_LO)
    d.rectangle([94, 46, 121, 49], fill=CHAR_HI); snow_cap(d, 94, 121, 43, 3, seed=9)
    d.rectangle([3, 92, 124, 94], fill=STONE_LO); d.line([(3, 92), (124, 92)], fill=STONE)
    # sawn planks leaning by the window, snow on their ends
    for k in range(4):
        x = 91 + k * 2
        d.line([(x, 60 + k * 2), (x, 91)], fill=(TIMBER_HI, TIMBER, TIMBER_LO, TIMBER)[k])
    d.line([(90, 59), (93, 60)], fill=SNOW)
    drift(d, 2, 40, 95, 5, seed=2); drift(d, 60, 97, 95, 3, seed=7); drift(d, 118, 126, 95, 3, seed=1)
    outline(im)
    return im


MINT, MINT_LO, MINT_HI, MINT_DK = rgb('8fbfae'), rgb('6d9c8c'), rgb('b3d9cb'), rgb('4f7669')


def shop_bakery():
    im, d = canvas(3, 4)                 # 96 x 128
    # a painted false front: a stepped parapet hiding a shed roof
    d.rectangle([6, 30, 89, 123], fill=MINT)
    d.rectangle([20, 20, 75, 30], fill=MINT)
    d.rectangle([34, 12, 61, 20], fill=MINT)
    for y in range(14, 124, 4):
        x0, x1 = (34, 61) if y < 20 else ((20, 75) if y < 30 else (6, 89))
        d.line([(x0, y), (x1, y)], fill=MINT_LO)
    for x0, y0, x1 in ((6, 30, 19), (20, 20, 33), (34, 12, 61), (62, 20, 75), (76, 30, 89)):
        d.rectangle([x0 - 1, y0 - 2, x1 + 1, y0], fill=WHITE)
        d.line([(x0 - 1, y0), (x1 + 1, y0)], fill=MINT_DK)
        snow_cap(d, x0 - 1, x1 + 1, y0 - 5, 3, seed=x0)
    d.rectangle([84, 31, 89, 123], fill=MINT_LO)
    d.line([(6, 31), (6, 123)], fill=MINT_HI)
    # a brick chimney behind the parapet
    d.rectangle([70, 4, 79, 17], fill=rgb('b8614a'))
    for y in range(6, 18, 3):
        d.line([(70, y), (79, y)], fill=rgb('8f4636'))
    d.rectangle([77, 5, 79, 17], fill=rgb('8f4636'))
    d.rectangle([68, 2, 81, 4], fill=STONE_LO); d.line([(68, 1), (81, 1)], fill=SNOW)
    # the oval board: PAN (bread) in kana, a loaf
    d.ellipse([16, 33, 79, 56], fill=CREAM)
    d.ellipse([16, 33, 79, 56], outline=WOOD_LO)
    d.ellipse([18, 35, 77, 54], outline=GOLD)
    kana(d, ('pa', 'n'), 27, 41, WOOD_DK)
    d.ellipse([49, 41, 69, 50], fill=rgb('c98a4b'))
    d.chord([49, 41, 69, 50], 20, 160, fill=rgb('a3683a'))
    for x in (54, 59, 64):
        d.line([(x, 42), (x - 2, 46)], fill=rgb('f0c98a'))
    # a striped awning
    for x in range(4, 92):
        c = rgb('8a4b3a') if (x // 6) % 2 == 0 else CREAM
        lo = rgb('6a3729') if (x // 6) % 2 == 0 else CREAM_LO
        d.line([(x, 62), (x, 71)], fill=c)
        d.line([(x, 72), (x, 73 + ((x % 6) in (2, 3)))], fill=lo)
    d.line([(4, 61), (91, 61)], fill=WOOD_DK)
    snow_cap(d, 4, 91, 58, 3, seed=5)
    # the window: loaves and rolls on two shelves, lamplit
    d.rectangle([9, 78, 44, 110], fill=WHITE)
    d.rectangle([11, 80, 42, 108], fill=WARM)
    d.line([(11, 80), (42, 80)], fill=WHITE)
    for sy in (93, 107):
        d.line([(11, sy), (42, sy)], fill=WOOD_LO)
    for k, (bx, by, bw) in enumerate(((13, 92, 8), (23, 92, 6), (31, 92, 9), (13, 106, 6), (21, 106, 9), (32, 106, 7))):
        d.ellipse([bx, by - 6, bx + bw, by], fill=(rgb('c98a4b'), rgb('dba862'), rgb('b3733f'))[k % 3])
        d.line([(bx + 2, by - 5), (bx + bw - 2, by - 5)], fill=rgb('f0c98a'))
    d.line([(26, 80), (26, 108)], fill=WHITE)
    d.rectangle([9, 111, 44, 123], fill=MINT_DK)
    for x in range(13, 44, 8):
        d.rectangle([x, 114, x + 4, 120], fill=MINT_LO)
    # the door (cell 1,3), a glazed half
    d.rectangle([50, 78, 69, 123], fill=WHITE)
    d.rectangle([52, 80, 67, 123], fill=rgb('8a4b3a'))
    d.line([(52, 80), (52, 123)], fill=rgb('b06a52'))
    d.rectangle([54, 83, 65, 102], fill=WARM); d.line([(54, 83), (65, 83)], fill=WHITE)
    d.line([(54, 92), (65, 92)], fill=rgb('8a4b3a')); d.line([(59, 83), (59, 102)], fill=rgb('8a4b3a'))
    d.rectangle([64, 104, 65, 108], fill=GOLD)
    d.rectangle([49, 123, 70, 125], fill=STONE_LO)
    # a hanging cup sign, and the chalkboard on the step
    d.line([(74, 80), (86, 80)], fill=INK); d.line([(84, 80), (84, 83)], fill=INK)
    d.ellipse([77, 83, 90, 96], fill=CREAM); d.ellipse([77, 83, 90, 96], outline=WOOD_LO)
    d.rectangle([80, 88, 86, 92], fill=rgb('8a4b3a')); d.arc([85, 88, 89, 92], 270, 90, fill=rgb('8a4b3a'))
    d.line([(82, 86), (82, 85)], fill=WOOD_LO); d.line([(85, 86), (85, 84)], fill=WOOD_LO)
    d.polygon([(74, 123), (77, 104), (88, 104), (91, 123)], fill=WOOD_LO)
    d.rectangle([78, 106, 87, 119], fill=rgb('2f3b36'))
    for k, y in enumerate((108, 111, 114, 117)):
        d.line([(80, y), (85 - (k % 2) * 2, y)], fill=WHITE if k == 0 else rgb('c9d6c8'))
    d.line([(77, 104), (88, 104)], fill=SNOW)
    drift(d, 2, 48, 127, 4, seed=4); drift(d, 70, 94, 127, 3, seed=2)
    outline(im)
    puffs(im, 75, -1 + 2, n=1, seed=1, colour=(214, 222, 236), a0=200)
    return im


def ice_block(d, x0, y0, x1, y1):
    """A plinth of clear ice: a lit top face, facets, a blue right end."""
    d.rectangle([x0, y0, x1, y1], fill=ICE)
    d.rectangle([x0, y0, x1, y0 + 2], fill=ICE_HI)
    d.rectangle([x1 - 3, y0 + 3, x1, y1], fill=ICE_LO)
    d.line([(x0, y1), (x1, y1)], fill=ICE_LO)
    for x in range(x0 + 5, x1 - 4, 7):
        d.line([(x, y0 + 4), (x - 1, y1 - 1)], fill=ICE_LO if (x // 7) % 2 else ICE_HI)
    d.line([(x0 + 1, y0 + 3), (x0 + 1, y1 - 1)], fill=ICE_HI)


def sparkle(d, x, y):
    d.point((x, y), fill=WHITE)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.point((x + dx, y + dy), fill=ICE_HI)


def ice_crane():
    """A red-crowned crane cut from clear ice, calling: a long thin S of a
    neck, the bill up, both wings raised and swept back, long legs."""
    im, d = canvas(2, 2)                 # 64 x 64
    ice_block(d, 13, 52, 52, 60)
    d.polygon([(38, 28), (45, 13), (54, 2), (58, 3), (57, 13), (50, 28)], fill=ICE_LO)   # the far wing
    for k in range(4):
        d.line([(43 + k * 3, 26), (49 + k * 3, 7 + k * 2)], fill=ICE_DK)
    d.polygon([(29, 28), (30, 14), (35, 2), (39, 2), (43, 13), (42, 28)], fill=ICE)      # the near wing
    d.line([(29, 28), (30, 14)], fill=ICE_HI); d.line([(30, 14), (35, 2)], fill=ICE_HI)
    for k in range(4):
        d.line([(32 + k * 3, 27), (34 + k * 2, 6 + k)], fill=ICE_LO)
    d.line([(39, 2), (43, 13)], fill=ICE_LO)
    d.ellipse([24, 24, 45, 36], fill=ICE)                                # the body
    d.chord([24, 24, 45, 36], 20, 160, fill=ICE_LO)
    d.arc([25, 25, 44, 35], 190, 300, fill=ICE_HI)
    d.polygon([(42, 28), (51, 31), (52, 39), (46, 36)], fill=ICE_LO)     # the drooping bustle
    d.line([(46, 32), (51, 38)], fill=ICE_DK)
    neck = [(27, 28), (22, 25), (18, 20), (17, 14), (20, 9), (20, 5)]    # the neck, an S
    for (xa, ya), (xb, yb) in zip(neck, neck[1:]):
        d.line([(xa, ya), (xb, yb)], fill=ICE, width=3)
    for (xa, ya), (xb, yb) in zip(neck[1:], neck[2:]):
        d.line([(xa - 1, ya), (xb - 1, yb)], fill=ICE_HI)
    d.line([(20, 21), (19, 15)], fill=ICE_LO)
    d.ellipse([17, 1, 24, 7], fill=ICE)                                  # the head, the long bill
    d.polygon([(18, 3), (6, 1), (18, 5)], fill=ICE_LO); d.line([(18, 3), (7, 1)], fill=ICE_HI)
    d.point((21, 4), fill=ICE_DK)
    d.rectangle([19, 1, 22, 1], fill=rgb('e58b93'))                      # a blush of red on its crown
    for x in (31, 38):                                                   # the legs: a third of its height
        d.rectangle([x, 36, x + 1, 51], fill=ICE_LO); d.line([(x, 36), (x, 51)], fill=ICE)
        d.point((x - 1, 43), fill=ICE); d.line([(x - 2, 51), (x + 3, 51)], fill=ICE)
    for sx, sy in ((37, 9), (34, 30), (48, 56), (17, 56)):
        sparkle(d, sx, sy)
    drift(d, 9, 56, 63, 3, seed=3)
    outline(im, ICE_DK)
    return im


def ice_owl():
    """A fish owl cut from clear ice, facing you, on its block."""
    im, d = canvas(1, 2)                 # 32 x 64
    ice_block(d, 3, 48, 28, 60)
    d.ellipse([5, 20, 26, 50], fill=ICE)                                 # the body
    d.chord([5, 20, 26, 50], 300, 80, fill=ICE_LO)
    d.ellipse([5, 9, 26, 30], fill=ICE)                                  # the head
    d.polygon([(6, 15), (7, 4), (13, 10)], fill=ICE); d.polygon([(25, 15), (24, 4), (18, 10)], fill=ICE_LO)
    d.line([(6, 15), (7, 4)], fill=ICE_HI)
    d.arc([5, 9, 26, 30], 180, 280, fill=ICE_HI)
    for x0 in (7, 16):                                                   # the face discs, the eyes
        d.ellipse([x0, 13, x0 + 8, 21], fill=ICE_HI)
        d.ellipse([x0, 13, x0 + 8, 21], outline=ICE_LO)
        d.rectangle([x0 + 3, 16, x0 + 5, 18], fill=ICE_DK); d.point((x0 + 3, 16), fill=WHITE)
    d.polygon([(15, 20), (16, 20), (16, 25), (15, 25)], fill=ICE_DK)
    for j, y in enumerate((30, 35, 40)):                                 # breast feathers
        for x in range(10 + (j % 2) * 2, 22, 4):
            d.line([(x, y), (x + 1, y + 2)], fill=ICE_LO); d.line([(x + 2, y + 2), (x + 3, y)], fill=ICE_LO)
    d.arc([3, 22, 13, 48], 90, 250, fill=ICE_HI)                         # the folded wings
    d.arc([19, 22, 29, 48], 290, 90, fill=ICE_DK)
    d.line([(8, 30), (8, 44)], fill=ICE_LO); d.line([(23, 30), (23, 44)], fill=ICE_DK)
    for x in (10, 18):                                                   # the feet
        d.rectangle([x, 46, x + 3, 48], fill=ICE_LO)
    sparkle(d, 9, 26); sparkle(d, 24, 53)
    drift(d, 1, 30, 63, 3, seed=5)
    outline(im, ICE_DK)
    return im


def bench():
    im, d = canvas(2, 1)                 # 64 x 32
    for x in (8, 53):                                                    # cast-iron ends
        d.rectangle([x, 7, x + 2, 29], fill=CHAR_LO)
        d.line([(x, 7), (x, 29)], fill=CHAR_HI)
        d.rectangle([x - 2, 28, x + 4, 29], fill=CHAR_LO)
        d.rectangle([x - 3, 15, x + 5, 16], fill=CHAR)                   # the arm
    for y in (8, 12):                                                    # the back's slats
        d.rectangle([6, y, 57, y + 2], fill=TIMBER)
        d.line([(6, y), (57, y)], fill=TIMBER_HI); d.line([(6, y + 2), (57, y + 2)], fill=TIMBER_LO)
    d.rectangle([5, 19, 58, 22], fill=TIMBER)                            # the seat's front edge
    d.line([(5, 22), (58, 22)], fill=TIMBER_DK); d.line([(5, 19), (58, 19)], fill=TIMBER_LO)
    for x in range(11, 58, 9):
        d.line([(x, 20), (x, 21)], fill=TIMBER_LO)
    snow_slab(d, 5, 58, 5, 6, seed=2, shade_from=52)                     # snow along the back
    for x in range(6, 58):                                               # and heaped on the seat
        top = 16 - int(round(1.6 * math.sin((x - 6) / 51 * math.pi))) - ((x * 5) % 7 == 0)
        d.line([(x, top), (x, 18)], fill=SNOW)
        d.point((x, top), fill=WHITE); d.point((x, 18), fill=SNOW_LO)
        if x > 50:
            d.line([(x, top + 1), (x, 18)], fill=SNOW_LO)
    for x0, x1 in ((22, 31),):                                           # where somebody sat
        d.rectangle([x0, 17, x1, 18], fill=TIMBER); d.line([(x0, 16), (x1, 16)], fill=SNOW_LO)
    outline(im)
    return under(im, [(3, 26, 60, 31)])


PAVE = (rgb('c5bbb0'), rgb('b8ada3'), rgb('cdc4ba'), rgb('aea39b'), rgb('bfb3a8'))
PAVE_ROSE, PAVE_ROSE_LO, PAVE_JOINT, PAVE_HI = rgb('c4aca2'), rgb('b39c93'), rgb('a69d96'), rgb('dcd5cc')


def paving_px(x, y):
    """Heiwa-dori's paving at drawn scale: granite setts laid in running bond,
    in five quiet greys with one in eight a faded rose (scattered, never on a
    diagonal), soft joints, a lit top-left arris, grit, snow in a few joints."""
    by, iy = (y // 8) % 4, y % 8
    xo = x + (4 if by % 2 else 0)
    bx, ix = (xo // 8) % 4, xo % 8
    if ix == 7 or iy == 7:
        return SNOW_LO if (bx * 5 + by * 3 + ix + iy) % 13 == 0 else PAVE_JOINT
    rose = (bx, by) in ((1, 0), (2, 3))
    c = PAVE_ROSE if rose else PAVE[(bx * 3 + by * 7 + bx * by) % 5]
    if ix == 0 or iy == 0:
        return mix(c, WHITE, 0.18)
    if (x * 7 + y * 13) % 29 == 0:
        return PAVE_ROSE_LO if rose else PAVE[3]
    return c


ASPH, ASPH_HI, ASPH_DK, ASPH_WET = rgb('5d6274'), rgb('6c7286'), rgb('4c5062'), rgb('3f4354')
SLUSH, SLUSH_HI = rgb('a4adbf'), rgb('d5dce8')


def alley_px(x, y):
    """The ramen alley's floor at drawn scale: dark wet asphalt, trodden
    slush lying in soft patches, meltwater pooling by the stoves. Periodic
    over one tile."""
    a, b = 2 * math.pi * (x % 32) / 32, 2 * math.pi * (y % 32) / 32
    v = (math.sin(a + 1.3) + math.sin(2 * b + 0.4) + math.sin(a + b + 2.0) + 0.6 * math.sin(3 * a - 2 * b))
    h = ((x % 32) * 7 + (y % 32) * 13 + ((x % 32) * (y % 32)) % 5) % 17
    if v > 2.3:
        return SLUSH_HI
    if v > 1.7 or (v > 1.3 and h % 3 == 0):
        return SLUSH if h % 5 else SLUSH_HI
    if v < -2.0:
        return ASPH_WET if h % 4 else rgb('6f7f9c')
    if h == 0:
        return ASPH_HI
    if h in (5, 11):
        return ASPH_DK
    return ASPH


def ground(role, px_fn):
    """A ground tile of a family. Opaque; on an edge the snow field lies over
    it with a wavy lip (the snow tile's own texture outside), shadowed where
    the bank faces away from the light."""
    im = Image.new('RGBA', (64, 64), CLEAR)
    px = im.load()
    for y in range(64):
        for x in range(64):
            px[x, y] = px_fn(x // 2, y // 2)
    if role == 'center':
        return im
    snow = Image.open(f'{SPR}/snow-autotile_center.png').convert('RGBA').load()
    tail = role.split('-')[-1]
    for y in range(64):
        for x in range(64):
            dn = y - (10 + _wob(x, 64)) if 'n' in tail else 99
            ds = (53 - _wob(x + 20, 64)) - y if 's' in tail else 99
            dw = x - (10 + _wob(y + 40, 64)) if 'w' in tail else 99
            de = (53 - _wob(y + 9, 64)) - x if 'e' in tail else 99
            a, b = min(dn, ds), min(dw, de)
            dist = 12 - math.hypot(12 - a, 12 - b) if (a < 12 and b < 12) else min(a, b)
            if dist < 0:
                px[x, y] = snow[x, y]
                if dist >= -2 and (min(ds, de) < 0):                  # the lit lip of a south / east bank
                    px[x, y] = (250, 252, 255, 255)
            elif dist < 4 and min(dn, dw) < 4:                        # the bank's shadow on the ground
                r, g, bl, _ = px[x, y]
                k = 0.72 if dist < 2 else 0.86
                px[x, y] = (int(r * k), int(g * k), int(bl * (k + 0.08)), 255)
            elif dist < 2:
                px[x, y] = (236, 242, 250, 255)                         # snow scuffed onto it
    return im


def heiwa_paving(role):
    """The pedestrian street's floor."""
    return ground(role, paving_px)


def alley_ground(role):
    """The ramen alley's floor."""
    return ground(role, alley_px)


def heiwa_lamp():
    """Heiwa-dori's street lamp (`lamp-post`: it glows at night): a timber
    post on a stone foot carrying a woodcraft lantern box, snow on its cap.
    The lantern is in the top cell, which is the cell the tile is placed on."""
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([14, 23, 17, 58], fill=TIMBER)
    d.line([(14, 23), (14, 58)], fill=TIMBER_HI); d.line([(17, 23), (17, 58)], fill=TIMBER_DK)
    for y in (31, 51):
        d.line([(14, y), (17, y)], fill=CHAR_LO)
    d.rectangle([12, 57, 19, 61], fill=STONE_DK); d.line([(12, 57), (19, 57)], fill=STONE_LO)
    d.rectangle([9, 9, 22, 22], fill=TIMBER_DK)                          # the lantern box
    d.rectangle([11, 11, 20, 20], fill=WARM)
    d.rectangle([13, 13, 18, 18], fill=mix(WARM, WHITE, 0.6)); d.rectangle([15, 14, 16, 17], fill=WHITE)
    for y in (13, 18):
        d.line([(11, y), (20, y)], fill=TIMBER_LO)
    d.line([(9, 9), (9, 22)], fill=TIMBER_LO)
    d.rectangle([12, 22, 19, 24], fill=CHAR); d.line([(12, 22), (19, 22)], fill=CHAR_HI)
    d.polygon([(6, 9), (14, 4), (17, 4), (25, 9)], fill=CHAR)             # its cap, under snow
    d.line([(6, 9), (25, 9)], fill=CHAR_LO)
    d.polygon([(7, 7), (14, 2), (17, 2), (24, 7), (22, 8), (9, 8)], fill=SNOW)
    d.line([(8, 6), (14, 2)], fill=WHITE); d.line([(14, 2), (17, 2)], fill=WHITE)
    d.line([(18, 3), (23, 7)], fill=SNOW_LO)
    drift(d, 7, 24, 62, 2, seed=3)
    outline(im)
    return im


def shop_books():
    """A second-hand bookshop: a low front in slate-blue tile, a cream BOOKS
    board, a green awning, a lit window of spines, a sale cart in the snow."""
    im, d = canvas(3, 3)                 # 96 x 96
    tile, tile_lo, tile_hi = rgb('7d8fa6'), rgb('5f7088'), rgb('9db0c6')
    d.rectangle([3, 12, 92, 17], fill=tile_lo)
    d.line([(3, 12), (92, 12)], fill=tile_hi); d.line([(3, 17), (92, 17)], fill=rgb('46546a'))
    snow_slab(d, 3, 92, 7, 11, seed=3)
    for y in range(18, 92):
        for x in range(5, 91):
            joint = (y % 5 == 4) or ((x + (y // 5 % 2) * 3) % 6 == 5)
            c = tile_lo if joint else (tile_hi if (x * 3 + (y // 5) * 7) % 11 == 0 else tile)
            d.point((x, y), fill=mix(c, tile_lo, 0.5) if x > 85 else c)
    d.rectangle([10, 21, 85, 36], fill=CREAM)                            # the board
    d.rectangle([10, 21, 85, 36], outline=NAVY)
    d.line([(11, 22), (84, 22)], fill=WHITE)
    for k, c in enumerate((RED, ROOF_G, AMBER)):                         # three books on end
        d.rectangle([15 + k * 4, 25 + (k == 1), 17 + k * 4, 33], fill=c)
        d.line([(15 + k * 4, 27 + (k == 1)), (17 + k * 4, 27 + (k == 1))], fill=WHITE)
    text(d, 'BOOKS', 34, 25, NAVY)
    d.rectangle([68, 28, 80, 29], fill=NAVY); d.rectangle([68, 31, 76, 32], fill=RED_DK)
    for x in range(4, 92):                                               # a green awning, scalloped
        d.line([(x, 40), (x, 46)], fill=ROOF_G if (x // 8) % 2 else ROOF_G_HI)
        d.line([(x, 47), (x, 47 + ((x % 8) in (2, 3, 4, 5)))], fill=ROOF_G_LO)
    d.line([(4, 39), (91, 39)], fill=WOOD_DK)
    snow_cap(d, 4, 91, 36, 3, seed=7)
    d.rectangle([8, 51, 58, 85], fill=WHITE)                             # the window: three shelves of spines
    d.rectangle([10, 53, 56, 83], fill=WARM)
    d.line([(10, 53), (56, 53)], fill=WHITE)
    cols = (RED, NAVY, ROOF_G, AMBER, rgb('8a4b3a'), CREAM, ROOF_B, rgb('7a5aa0'))
    for j, sy in enumerate((63, 73, 83)):
        d.line([(10, sy), (56, sy)], fill=WOOD_LO)
        x = 11
        while x < 55:
            k = (x * 5 + j * 3) % 8
            w, h = 2 + (k % 2), 6 + (k % 3)
            if k != 5:
                d.rectangle([x, sy - h, min(55, x + w - 1), sy - 1], fill=cols[k])
            x += w + 1
    d.line([(33, 53), (33, 83)], fill=WHITE)
    d.rectangle([66, 51, 87, 91], fill=WHITE)                            # the door (cell 2,2), glazed
    d.rectangle([68, 53, 85, 91], fill=rgb('46546a'))
    d.rectangle([70, 56, 83, 78], fill=WARM); d.line([(70, 56), (83, 56)], fill=WHITE)
    d.line([(72, 59), (72, 74)], fill=WHITE)
    d.rectangle([73, 64, 80, 68], fill=CREAM); d.line([(74, 66), (79, 66)], fill=RED_DK)   # OPEN card
    d.rectangle([82, 79, 83, 84], fill=GOLD)
    d.rectangle([3, 92, 92, 94], fill=STONE_LO); d.line([(3, 92), (92, 92)], fill=STONE)
    d.rectangle([12, 80, 38, 90], fill=TIMBER)                           # the sale cart
    d.line([(12, 80), (38, 80)], fill=TIMBER_HI); d.rectangle([12, 89, 38, 90], fill=TIMBER_DK)
    d.rectangle([34, 81, 38, 90], fill=TIMBER_LO)
    for k, x in enumerate(range(14, 36, 3)):
        d.rectangle([x, 75 + (k % 3 == 1), x + 1, 79], fill=cols[(k * 3) % 8])
    d.line([(13, 74), (37, 74)], fill=SNOW); d.line([(15, 73), (34, 73)], fill=WHITE)
    for x in (14, 34):
        d.ellipse([x, 89, x + 4, 93], fill=CHAR_LO); d.point((x + 2, 91), fill=STONE)
    drift(d, 40, 66, 95, 3, seed=2); drift(d, 86, 95, 95, 3, seed=5); drift(d, 0, 11, 95, 4, seed=1)
    outline(im)
    return im


# ==============================================================================
# Ramen alley
# ==============================================================================
def nobori(d, x, y0, y1, names=('ra', 'bar', 'me', 'n'), body=RED, ink=WHITE):
    """A banner on a pole: 13px of cloth from y0 to y1, kana down it."""
    d.rectangle([x, y0 - 3, x + 1, y1 + 12], fill=WOOD_LO)
    d.rectangle([x, y0 - 2, x + 14, y0 - 1], fill=WOOD_LO)
    d.rectangle([x + 2, y0, x + 14, y1], fill=body)
    d.line([(x + 2, y0), (x + 2, y1)], fill=RED_HI if body == RED else WHITE)
    d.line([(x + 14, y0), (x + 14, y1)], fill=RED_DK if body == RED else CREAM_LO)
    d.line([(x + 2, y1), (x + 14, y1)], fill=RED_DK if body == RED else CREAM_LO)
    kana(d, names, x + 5, y0 + 3, ink, vertical=True)
    for y in range(y0 + 4, y1, 9):
        d.point((x + 2, y), fill=WOOD_DK)


def ramen_shoyu():
    im, d = canvas(4, 4)                 # 128 x 128
    # a low tin roof, deep in snow, a stovepipe through it
    scan = [(y, 6 - (y - 14) // 3, 121 + (y - 14) // 3) for y in range(14, 30)]
    seam_roof(d, scan, rgb('7a4a3a'), rgb('9a6450'), rgb('573428'), step=7)
    d.rectangle([97, 2, 103, 20], fill=STONE)
    d.line([(97, 2), (97, 20)], fill=WHITE); d.rectangle([102, 2, 103, 20], fill=STONE_LO)
    d.rectangle([94, 0, 106, 2], fill=STONE_LO); d.line([(94, 0), (106, 0)], fill=STONE)
    snow_slab(d, 5, 92, 9, 16, seed=4)
    snow_slab(d, 108, 122, 10, 16, seed=9)
    for x in range(8, 120, 11):                                          # snow sliding down the seams
        d.line([(x, 20), (x, 22 + x % 3)], fill=SNOW)
    d.rectangle([0, 30, 127, 31], fill=CHAR_LO)
    icicles(d, 2, 125, 32, seed=5)
    # the board: red, a white rule, ramen in kana between a bowl and the town's mark
    d.rectangle([5, 32, 122, 55], fill=RED)
    d.rectangle([5, 32, 122, 33], fill=RED_HI); d.rectangle([5, 54, 122, 55], fill=RED_DK)
    d.rectangle([118, 34, 122, 55], fill=RED_DK)
    d.rectangle([8, 35, 119, 52], outline=WHITE)
    kana(d, ('ra', 'bar', 'me', 'n'), 64 - kana_w(4, 2) // 2, 37, WHITE, scale=2)
    bowl(d, 14, 45)
    d.ellipse([101, 36, 116, 51], fill=WHITE)
    kanji(d, ('asahi',), 103, 38, RED_DK)
    # the front: charred boards, posts, a beam hung with small lanterns
    boards_v(d, 5, 56, 122, 123, CHAR, CHAR_LO, None, step=5)
    d.rectangle([5, 56, 122, 58], fill=INK)
    for x in (5, 119):
        d.rectangle([x, 56, x + 3, 123], fill=WOOD_LO); d.line([(x, 56), (x, 123)], fill=WOOD)
    # the counter window: lamplight, the cook, pots steaming, bowls, menu slips
    d.rectangle([22, 60, 82, 101], fill=WOOD_DK)
    d.rectangle([24, 62, 80, 99], fill=WARM)
    d.rectangle([24, 86, 80, 99], fill=rgb('e2b45c'))
    d.rectangle([24, 62, 80, 76], fill=mix(WARM, WHITE, 0.4))
    d.ellipse([46, 76, 54, 85], fill=rgb('e9b796'))                    # the cook, a towel round his head
    d.rectangle([46, 76, 54, 78], fill=WHITE); d.point((55, 78), fill=WHITE)
    d.rectangle([43, 85, 57, 99], fill=WHITE); d.line([(50, 85), (50, 99)], fill=CREAM_LO)
    d.point((48, 81), fill=INK); d.point((52, 81), fill=INK)
    d.rectangle([28, 86, 39, 98], fill=STONE); d.rectangle([28, 86, 39, 87], fill=WHITE)   # a stock pot
    d.rectangle([37, 88, 39, 98], fill=STONE_LO)
    for x in (62, 69, 76):                                               # bowls stacked on the counter
        for k in range(2 + (x % 2)):
            d.rectangle([x - 3, 95 - k * 3, x + 3, 96 - k * 3], fill=WHITE)
            d.line([(x - 3, 97 - k * 3), (x + 3, 97 - k * 3)], fill=RED)
    for i, x in enumerate(range(27, 80, 7)):                             # menu slips along the lintel
        d.rectangle([x, 63, x + 4, 73], fill=WHITE)
        d.line([(x + 2, 65), (x + 2, 71)], fill=RED_DK if i % 3 else INK)
    d.rectangle([20, 100, 84, 103], fill=WOOD)                           # the counter
    d.line([(20, 100), (84, 100)], fill=WOOD_HI); d.line([(20, 103), (84, 103)], fill=WOOD_DK)
    for i, x in enumerate(range(24, 81, 12)):                            # a short red noren over it
        d.rectangle([x, 60, x + 10, 68], fill=RED)
        d.line([(x, 60), (x, 68)], fill=RED_HI); d.line([(x, 68), (x + 10, 68)], fill=RED_DK)
        d.ellipse([x + 3, 62, x + 7, 66], fill=WHITE)
    for x in (30, 44, 58, 72):                                           # stools tucked under
        d.rectangle([x, 108, x + 7, 109], fill=RED); d.line([(x, 108), (x + 7, 108)], fill=RED_HI)
        d.line([(x + 1, 110), (x, 122)], fill=INK); d.line([(x + 6, 110), (x + 7, 122)], fill=INK)
    # the door (cell 3,3): a lamplit lattice, a red noren
    d.rectangle([97, 62, 116, 123], fill=WOOD_DK)
    d.rectangle([99, 64, 114, 123], fill=mix(WARM, WOOD_HI, 0.35))
    for x in range(101, 114, 3):
        d.line([(x, 78), (x, 123)], fill=WOOD_LO)
    for y in (92, 108):
        d.line([(99, y), (114, y)], fill=WOOD_LO)
    d.rectangle([106, 64, 107, 123], fill=WOOD_DK)
    for x in (99, 107):
        d.rectangle([x, 64, x + 7, 78], fill=RED)
        d.line([(x, 64), (x, 78)], fill=RED_HI); d.line([(x, 78), (x + 7, 78)], fill=RED_DK)
        d.rectangle([x + 2, 68, x + 5, 73], fill=WHITE)
    # two red nobori, a paper lantern by the door
    nobori(d, 6, 62, 101)
    nobori(d, 82, 62, 101)
    lantern(d, 118, 66, 8, 13)
    d.rectangle([121, 70, 122, 74], fill=WHITE)
    d.rectangle([3, 123, 124, 125], fill=STONE_LO); d.line([(3, 123), (124, 123)], fill=STONE)
    drift(d, 0, 24, 127, 5, seed=2); drift(d, 84, 98, 127, 3, seed=6); drift(d, 114, 127, 127, 4, seed=3)
    outline(im)
    puffs(im, 100, -2 + 2, n=1, seed=0)
    puffs(im, 34, 84, n=6, seed=2, lean=1, a0=190, grow=2)
    return im


def ramen_narrow():
    im, d = canvas(2, 4)                 # 64 x 128
    # a shed roof in blue tin under snow, the wall rendered mustard
    scan = [(y, 3, 60) for y in range(16, 24)]
    seam_roof(d, scan, ROOF_B, ROOF_B_HI, ROOF_B_LO, step=6)
    snow_slab(d, 3, 60, 10, 17, seed=6)
    d.rectangle([2, 24, 61, 25], fill=ROOF_B_LO)
    icicles(d, 4, 60, 26, seed=1)
    wall, wall_lo, wall_hi = rgb('d8b66a'), rgb('b3924e'), rgb('ecd292')
    d.rectangle([5, 26, 58, 123], fill=wall)
    d.rectangle([5, 26, 58, 28], fill=wall_lo)
    d.rectangle([54, 29, 58, 123], fill=wall_lo)
    d.line([(5, 29), (5, 123)], fill=wall_hi)
    for k in range(14):                                                  # patched render
        d.point((9 + (k * 17) % 44, 32 + (k * 29) % 40), fill=wall_lo)
    # upstairs: a lit window, a unit on brackets
    lit_window(d, 28, 36, 47, 52, frame=WHITE, lit=True, curtain=rgb('c9d6ea'))
    d.rectangle([30, 58, 44, 67], fill=STONE); d.rectangle([30, 58, 44, 59], fill=WHITE)
    d.ellipse([32, 60, 38, 66], fill=STONE_LO); d.point((35, 63), fill=STONE_DK)
    d.line([(40, 61), (43, 61)], fill=STONE_LO); d.line([(40, 63), (43, 63)], fill=STONE_LO)
    d.line([(30, 56), (44, 56)], fill=SNOW); d.line([(30, 57), (44, 57)], fill=SNOW_LO)
    # the upright sign: yellow, ramen in red, hung off the wall
    d.rectangle([8, 32, 22, 73], fill=AMBER)
    d.line([(8, 32), (8, 73)], fill=rgb('fde38a')); d.rectangle([20, 33, 22, 73], fill=rgb('d49a1c'))
    d.rectangle([8, 32, 22, 73], outline=RED_DK)
    kana(d, ('ra', 'bar', 'me', 'n'), 11, 36, RED_DK, vertical=True)
    d.line([(8, 30), (22, 30)], fill=SNOW); d.line([(9, 31), (22, 31)], fill=SNOW_LO)
    # the pent roof over the shop front
    scan = [(y, 3 - (y - 76) // 2, 60 + (y - 76) // 2) for y in range(76, 82)]
    seam_roof(d, scan, ROOF_B, ROOF_B_HI, ROOF_B_LO, step=6)
    snow_slab(d, 2, 61, 73, 76, seed=3, shade_from=54)
    # the shop front: a lit window with a bowl in it, a white noren on the door (cell 1,3)
    d.rectangle([5, 83, 58, 85], fill=wall_lo)
    d.rectangle([8, 88, 27, 104], fill=WOOD_DK)
    d.rectangle([9, 89, 26, 103], fill=WARM); d.line([(9, 89), (26, 89)], fill=WHITE)
    bowl(d, 12, 98, fill=WHITE, band=NAVY)
    d.rectangle([9, 101, 26, 103], fill=WOOD_LO)
    boards_v(d, 8, 106, 27, 123, WOOD_LO, WOOD_DK, None, step=4)
    d.rectangle([33, 86, 54, 123], fill=WOOD_DK)
    d.rectangle([35, 88, 52, 123], fill=mix(WARM, WOOD_HI, 0.35))
    for x in range(37, 52, 3):
        d.line([(x, 102), (x, 123)], fill=WOOD_LO)
    d.line([(35, 112), (52, 112)], fill=WOOD_LO)
    d.rectangle([43, 88, 44, 123], fill=WOOD_DK)
    for x in (35, 41, 47):
        d.rectangle([x, 88, x + 4, 100], fill=WHITE)
        d.line([(x + 4, 88), (x + 4, 100)], fill=CREAM_LO); d.line([(x, 100), (x + 4, 100)], fill=CREAM_LO)
        d.rectangle([x + 1, 92, x + 3, 95], fill=RED)
    lantern(d, 27, 86, 6, 11)
    # the stovepipe: out of the wall, up past the roof
    d.rectangle([55, 94, 62, 97], fill=STONE); d.line([(55, 94), (62, 94)], fill=WHITE)
    d.rectangle([59, 6, 62, 97], fill=STONE)
    d.line([(59, 6), (59, 93)], fill=WHITE); d.line([(62, 6), (62, 97)], fill=STONE_LO)
    for y in (30, 60, 88):
        d.line([(59, y), (62, y)], fill=STONE_DK)
    d.rectangle([57, 3, 63, 5], fill=STONE_LO); d.line([(57, 3), (63, 3)], fill=STONE)
    d.rectangle([3, 123, 60, 125], fill=STONE_LO); d.line([(3, 123), (60, 123)], fill=STONE)
    drift(d, 0, 34, 127, 5, seed=4); drift(d, 52, 63, 127, 4, seed=7)
    outline(im)
    puffs(im, 59, 0 + 2, n=1, seed=3)
    return im


def round_lantern(d, cx, cy, r, name):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.chord([cx - r, cy - r, cx + r, cy + r], 320, 100, fill=CREAM)
    d.arc([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], 180, 290, fill=WHITE)
    for dy in (-r + 3, r - 3):
        d.line([(cx - r + 3, cy + dy), (cx + r - 3, cy + dy)], fill=CREAM_LO)
    d.rectangle([cx - 2, cy - r - 2, cx + 2, cy - r], fill=INK)
    d.rectangle([cx - 2, cy + r, cx + 2, cy + r + 1], fill=INK)
    d.line([(cx, cy + r + 2), (cx, cy + r + 4)], fill=RED)
    glyphs(d, [KANA[name]], cx - 3, cy - 3, RED_DK)       # the gate's row reads across: its long mark lies flat


def ramen_gate():
    """Two timber posts, a beam with a shingled cap, a plank that says YOKOCHO
    and four round paper lanterns spelling ramen. You walk through the middle."""
    im, d = canvas(3, 3)                 # 96 x 96
    for x in (6, 84):
        d.rectangle([x, 22, x + 5, 91], fill=WOOD_LO)
        d.line([(x, 22), (x, 91)], fill=WOOD); d.rectangle([x + 4, 22, x + 5, 91], fill=WOOD_DK)
        d.rectangle([x - 2, 88, x + 7, 93], fill=STONE_DK); d.line([(x - 2, 88), (x + 7, 88)], fill=STONE_LO)
        d.line([(x + 6 if x < 40 else x - 1, 34), (x + 14 if x < 40 else x - 9, 27)], fill=WOOD_DK, width=2)   # a knee brace
    scan = [(y, 3 - (y - 8), 92 + (y - 8)) for y in range(8, 13)]
    tiles(d, scan, rgb('6b4a3a'), rgb('4a3228'), step=3)
    d.rectangle([0, 13, 95, 14], fill=INK)
    d.rectangle([2, 15, 93, 21], fill=WOOD_LO)
    d.line([(2, 15), (93, 15)], fill=WOOD); d.line([(2, 21), (93, 21)], fill=WOOD_DK)
    snow_slab(d, 2, 93, 3, 8, seed=5, shade_from=84)
    d.rectangle([24, 14, 71, 26], fill=TIMBER)                           # the plank
    d.line([(24, 14), (71, 14)], fill=TIMBER_HI); d.rectangle([24, 25, 71, 26], fill=TIMBER_DK)
    d.line([(71, 14), (71, 26)], fill=TIMBER_DK)
    text(d, 'YOKOCHO', 48 - text_w('YOKOCHO') // 2, 17, INK)
    d.line([(12, 30), (83, 30)], fill=INK)                               # the lantern wire
    for cx, name in zip((21, 39, 57, 75), ('ra', 'bar', 'me', 'n')):
        d.line([(cx, 30), (cx, 32)], fill=INK)
        round_lantern(d, cx, 42, 7, name)
    drift(d, 0, 18, 95, 4, seed=2); drift(d, 77, 95, 95, 4, seed=9)
    outline(im)
    return im


def ramen_lanterns():
    """The alley's own light (`-lanterns`: it glows at night): a timber post
    with a bracket arm and three round white paper lanterns hung down it,
    ra-me-n in red, the same lanterns as the gate's. The arm and the top
    lantern are in the top cell, which is the cell the tile is placed on."""
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([4, 4, 6, 60], fill=WOOD_LO)
    d.line([(4, 4), (4, 60)], fill=WOOD); d.line([(6, 4), (6, 60)], fill=WOOD_DK)
    d.rectangle([2, 58, 8, 61], fill=STONE_DK); d.line([(2, 58), (8, 58)], fill=STONE_LO)
    d.rectangle([4, 6, 27, 7], fill=WOOD_LO); d.line([(4, 6), (27, 6)], fill=WOOD)
    d.line([(7, 15), (14, 8)], fill=WOOD_DK)
    d.line([(20, 8), (20, 50)], fill=INK)
    for cy, name in zip((16, 31, 46), ('ra', 'me', 'n')):
        round_lantern(d, 20, cy, 6, name)
    snow_cap(d, 3, 27, 3, 2, seed=6)
    drift(d, 0, 14, 62, 2, seed=5)
    outline(im)
    return im


def ramen_miso():
    """A miso-ramen shop, gable to the street: a brown tin roof thick with
    snow, a plastered gable with a round lit window, an indigo board (miso
    ramen in kana), an indigo noren, a yellow nobori, a red lantern."""
    im, d = canvas(3, 4)                 # 96 x 128
    ax, ay, ey = 47, 14, 52
    tin, tin_hi, tin_lo = rgb('7a4a3a'), rgb('9a6450'), rgb('573428')
    d.rectangle([72, 14, 76, 40], fill=STONE)                            # a stovepipe through the roof
    d.line([(72, 14), (72, 40)], fill=WHITE); d.line([(76, 14), (76, 40)], fill=STONE_LO)
    d.rectangle([70, 11, 78, 13], fill=STONE_LO); d.line([(70, 11), (78, 11)], fill=STONE)
    for y in range(ay + 6, ey):                                          # the gable wall
        half = int((y - ay - 5) * 40 / (ey - ay - 5))
        for x in range(ax - half, ax + half + 1):
            d.point((x, y), fill=PLASTER_LO if x > ax + half - 5 else PLASTER)
    d.rectangle([ax - 1, ay + 8, ax + 1, ey - 1], fill=WOOD_LO)          # its timbers
    d.rectangle([ax - 26, ey - 10, ax + 26, ey - 9], fill=WOOD_LO)
    for sx in (-14, 14):
        d.rectangle([ax + sx - 1, ey - 22, ax + sx, ey - 1], fill=WOOD_LO)
    d.ellipse([ax - 7, 27, ax + 7, 41], fill=WOOD_DK)                    # the round window
    d.ellipse([ax - 5, 29, ax + 5, 39], fill=WARM)
    d.line([(ax, 29), (ax, 39)], fill=WOOD_DK); d.line([(ax - 5, 34), (ax + 5, 34)], fill=WOOD_DK)
    d.arc([ax - 5, 29, ax + 5, 39], 180, 280, fill=WHITE)
    for i in range(0, 46):                                               # the roof's two slopes, snow on both
        t = i / 45
        y = ay + t * (ey - ay)
        for side in (-1, 1):
            xi, yi = int(round(ax + side * (1 + t * 44))), int(round(y))
            d.rectangle([xi - 1, yi + 3, xi + 1, yi + 7], fill=tin if side < 0 else tin_lo)
            d.point((xi - side, yi + 7), fill=tin_lo)
            if side < 0:
                d.point((xi - 1, yi + 3), fill=tin_hi)
            depth = 5 - int(2 * t) + ((i * 5) % 7 == 0)
            d.rectangle([xi - 1, yi + 3 - depth, xi + 1, yi + 2], fill=SNOW if side < 0 else SNOW_LO)
            d.rectangle([xi - 1, yi + 3 - depth, xi + 1, yi + 4 - depth], fill=WHITE if side < 0 else SNOW)
    d.ellipse([ax - 5, ay - 5, ax + 5, ay + 4], fill=SNOW)
    d.arc([ax - 5, ay - 5, ax + 5, ay + 4], 180, 300, fill=WHITE)
    # the board: indigo, cream kana
    d.rectangle([6, 55, 89, 72], fill=NAVY)
    d.line([(6, 55), (89, 55)], fill=rgb('4a5fa8')); d.rectangle([6, 71, 89, 72], fill=INK)
    d.rectangle([85, 56, 89, 72], fill=rgb('1c2850'))
    d.rectangle([8, 57, 86, 69], outline=CREAM_LO)
    bowl(d, 12, 65, fill=CREAM, band=RED)
    kana(d, ('mi', 'so'), 27, 60, AMBER)
    kana(d, ('ra', 'bar', 'me', 'n'), 48, 60, CREAM)
    icicles(d, 6, 89, 73, seed=7)
    # the front: plaster between timber posts over a boarded dado
    d.rectangle([6, 73, 89, 123], fill=PLASTER)
    d.rectangle([6, 73, 89, 75], fill=PLASTER_DK)
    d.rectangle([84, 76, 89, 123], fill=PLASTER_LO)
    boards_v(d, 6, 106, 89, 123, WOOD_LO, WOOD_DK, None, step=4)
    d.line([(6, 105), (89, 105)], fill=WOOD)
    for x in (6, 87):
        d.rectangle([x, 73, x + 2, 123], fill=WOOD_LO); d.line([(x, 73), (x, 123)], fill=WOOD)
    d.rectangle([11, 79, 31, 101], fill=WOOD_DK)                         # a latticed window, lamplit
    d.rectangle([12, 80, 30, 100], fill=WARM)
    for x in range(15, 30, 3):
        d.line([(x, 80), (x, 100)], fill=WOOD_LO)
    d.line([(12, 90), (30, 90)], fill=WOOD_LO)
    d.rectangle([36, 76, 59, 123], fill=WOOD_DK)                         # the door (cell 1,3)
    d.rectangle([38, 78, 57, 123], fill=mix(WARM, WOOD_HI, 0.35))
    for x in range(40, 57, 3):
        d.line([(x, 96), (x, 123)], fill=WOOD_LO)
    d.line([(38, 110), (57, 110)], fill=WOOD_LO)
    d.rectangle([47, 78, 48, 123], fill=WOOD_DK)
    for x in (38, 45, 52):                                               # an indigo noren
        d.rectangle([x, 78, x + 5, 94], fill=NAVY)
        d.line([(x, 78), (x, 94)], fill=rgb('4a5fa8')); d.line([(x, 94), (x + 5, 94)], fill=INK)
        d.ellipse([x + 1, 83, x + 4, 86], fill=CREAM)
    lantern(d, 62, 77, 9, 14)
    d.rectangle([65, 82, 66, 86], fill=WHITE)
    nobori(d, 72, 80, 108, names=('mi', 'so'), body=AMBER, ink=RED_DK)
    d.rectangle([3, 123, 92, 125], fill=STONE_LO); d.line([(3, 123), (92, 123)], fill=STONE)
    drift(d, 0, 36, 127, 5, seed=5); drift(d, 60, 95, 127, 4, seed=1)
    outline(im)
    puffs(im, 74, 7, n=2, seed=2, lean=1, a0=220)
    return im


def crate(d, x, y, body, lo, hi):
    """A plastic bottle crate 14 wide and 9 tall with its foot on y."""
    d.rectangle([x, y - 8, x + 13, y], fill=body)
    d.line([(x, y - 8), (x + 13, y - 8)], fill=hi); d.line([(x, y - 8), (x, y)], fill=hi)
    d.line([(x + 13, y - 7), (x + 13, y)], fill=lo); d.line([(x, y), (x + 13, y)], fill=lo)
    d.rectangle([x + 4, y - 6, x + 9, y - 5], fill=lo)                   # the hand hole
    d.line([(x + 2, y - 2), (x + 11, y - 2)], fill=WHITE)


def ramen_crates():
    im, d = canvas(1, 2)                 # 32 x 64
    yl, yl_lo, yl_hi = AMBER, rgb('c8941c'), rgb('fde38a')
    rd = (RED, RED_DK, RED_HI)
    bl = (rgb('3a5fb0'), NAVY, rgb('6a8fd8'))
    crate(d, 2, 61, yl, yl_lo, yl_hi); crate(d, 16, 61, *rd)
    crate(d, 2, 52, *rd); crate(d, 16, 52, yl, yl_lo, yl_hi)
    crate(d, 2, 43, *bl); crate(d, 16, 43, *rd)
    crate(d, 9, 34, yl, yl_lo, yl_hi)
    for x in range(11, 22, 3):                                           # empties in the top one
        d.rectangle([x, 20, x + 1, 25], fill=rgb('5b3a22')); d.point((x, 19), fill=GOLD)
        d.point((x, 21), fill=rgb('8a5a34'))
    for x in (3, 26):
        d.rectangle([x, 31, x + 2, 34], fill=SNOW); d.point((x + 1, 30), fill=WHITE)
    d.line([(2, 34), (8, 34)], fill=SNOW); d.line([(23, 34), (29, 34)], fill=SNOW)
    d.line([(9, 25), (22, 25)], fill=SNOW); d.line([(9, 24), (10, 24)], fill=WHITE); d.line([(21, 24), (22, 24)], fill=WHITE)
    drift(d, 0, 31, 63, 2, seed=8)
    outline(im)
    return im


def ramen_stockpot():
    im, d = canvas(1, 2)                 # 32 x 64
    al, al_hi, al_lo, al_dk = rgb('c9d0d8'), rgb('f4f7fa'), rgb('9099a6'), rgb('646c7a')
    # the burner: an iron ring on three legs, a blue flame
    for x in (6, 14, 22):
        d.rectangle([x, 50, x + 1, 60], fill=CHAR_LO)
    d.rectangle([4, 48, 25, 50], fill=CHAR); d.line([(4, 48), (25, 48)], fill=CHAR_HI)
    for x in range(8, 22, 3):
        d.point((x, 47), fill=rgb('6fb6ff')); d.point((x + 1, 46), fill=rgb('bfe3ff'))
    # the pot
    d.rectangle([4, 26, 25, 45], fill=al)
    d.rectangle([4, 26, 7, 45], fill=al_hi); d.rectangle([20, 26, 25, 45], fill=al_lo)
    d.line([(4, 45), (25, 45)], fill=al_dk); d.line([(4, 30), (25, 30)], fill=al_lo)
    d.ellipse([3, 22, 26, 29], fill=al_hi)
    d.ellipse([5, 23, 24, 28], fill=rgb('c58b4a'))                       # the broth
    d.ellipse([8, 24, 14, 26], fill=rgb('e3b66c')); d.point((19, 26), fill=rgb('e3b66c'))
    for x in (1, 26):                                                    # the handles
        d.rectangle([x, 32, x + 2, 35], fill=al_dk)
    d.line([(17, 25), (27, 12)], fill=al_dk, width=2)                    # a ladle left in it
    d.line([(17, 24), (26, 12)], fill=al_hi)
    # a gas bottle beside it
    d.rectangle([26, 49, 31, 60], fill=rgb('8a93a0')); d.line([(26, 49), (26, 60)], fill=al)
    d.rectangle([28, 46, 29, 48], fill=al_dk); d.line([(27, 53), (30, 53)], fill=RED)
    d.line([(25, 49), (27, 47)], fill=INK)
    drift(d, 0, 31, 63, 2, seed=1)
    outline(im)
    puffs(im, 13, 20, n=6, seed=1, lean=1, a0=225, grow=4)
    return im


# ==============================================================================
# Asahibashi and the riverbank
# ==============================================================================
def green_rail(d, x0, y0, y1, posts):
    """A riveted green parapet 6px wide, snow on its posts."""
    d.rectangle([x0, y0, x0 + 5, y1], fill=BG)
    d.line([(x0, y0), (x0, y1)], fill=BG_HI); d.line([(x0 + 1, y0), (x0 + 1, y1)], fill=BG_HI)
    d.rectangle([x0 + 4, y0, x0 + 5, y1], fill=BG_LO)
    for y in range(y0 + 2, y1, 4):
        d.point((x0 + 3, y), fill=BG_DK)
    for y in posts:
        d.rectangle([x0 - 1, y, x0 + 6, y + 6], fill=BG_LO)
        d.rectangle([x0 - 1, y, x0 + 6, y + 3], fill=SNOW)
        d.line([(x0 - 1, y), (x0 + 6, y)], fill=WHITE); d.line([(x0 - 1, y + 4), (x0 + 6, y + 4)], fill=SNOW_LO)


DECK, DECK_LO, DECK_HI = rgb('878d9d'), rgb('787e90'), rgb('969cab')
BRIDGE_ROWS = 5                          # the deck's length in cells: one on each bank, the rest over the river
PIER_LAMP_Y = (2, (BRIDGE_ROWS * 32 - 17) * 2)   # the two pier lamps of a rib, in file pixels from its top


def asahibashi_deck(n=BRIDGE_ROWS):
    """The deck, seen from above: a plain grey road between green riveted
    parapets, a pale kerb line each side with the snow blown up against the
    parapet behind it, a worn centre line, stone thresholds at the banks.
    Flat and walked ON; 2 cells wide, `n` long (the two end cells on the banks)."""
    im, d = canvas(2, n)
    L = n * 32
    px = im.load()
    for y in range(3, L - 3):
        for x in range(8, 56):
            h = (x * 7 + y * 13 + (x * y) % 7) % 19
            px[x, y] = DECK_HI if h == 0 else (DECK_LO if h in (4, 11) else DECK)
    for y in range(8, L - 8):                                            # a worn centre line; packed snow in the wheel ruts
        if (y // 8) % 2 == 0:
            px[31, y] = px[32, y] = rgb('bcc1cc') if (y * 5) % 7 else DECK_HI
        for x in (21, 42):
            if (y * 3 + x) % 11 < 4:
                px[x, y] = rgb('a9afbd')
    for kx, sx in ((12, 14), (50, 49)):                                  # the kerbs
        d.rectangle([kx, 3, kx + 1, L - 4], fill=STONE)
        d.line([(kx, 3), (kx, L - 4)], fill=WHITE)
        d.line([(sx, 3), (sx, L - 4)], fill=rgb('666c7e'))
        for y in range(10, L - 4, 12):
            d.line([(kx, y), (kx + 1, y)], fill=STONE_LO)
    for y in range(3, L - 3):                                            # snow blown against the parapets
        wl = 3 + ((y * 5) % 7 in (0, 1, 2))
        wr = 3 + ((y * 7) % 9 in (0, 1))
        for x in range(8, 8 + wl):
            px[x, y] = SNOW if x < 8 + wl - 1 else SNOW_LO
        for x in range(56 - wr, 56):
            px[x, y] = SNOW_LO if x == 56 - wr else SNOW
    posts = list(range(8, L - 10, 24))
    green_rail(d, 2, 5, L - 6, posts)
    green_rail(d, 56, 5, L - 6, posts)
    for y0 in (0, L - 7):                                                # stone thresholds
        d.rectangle([0, y0, 63, y0 + 6], fill=STONE)
        d.line([(0, y0), (63, y0)], fill=WHITE); d.line([(0, y0 + 6), (63, y0 + 6)], fill=STONE_LO)
        for x in range(7, 64, 14):
            d.line([(x, y0 + 1), (x, y0 + 5)], fill=STONE_LO)
    outline(im)
    return im


def _arch_pts(side, L, H, inset, n=120):
    """One chord of a rib as (x, y) points in the piece's own pixels. The
    deck's edge is the piece's inner edge; height leans the rib away from the
    deck and a little up the screen, as a tall thing does when you look down
    on it. `inset` draws the same curve that much inside the outer chord."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = H * math.sin(math.pi * t) ** 0.8
        v = (L - 12.0 - inset) - t * (L - 24.0 - 2 * inset) - 0.32 * u
        pts.append((int(round(31 - u if side == 'w' else u)), int(round(v))))
    return pts


def asahibashi_arch(side, n=BRIDGE_ROWS, H=26.0, depth=7.0):
    """One rib of the arch: a deep riveted green truss (two chords, a lattice
    web between them) springing from a stone pier on each bank, a few thin
    hangers down to the deck's edge. 'w' stands west of the deck, 'e' east;
    neither covers a deck cell. Lit from the west: each rib's west chord is
    the bright one, so the east rib is drawn, not mirrored."""
    im, d = canvas(1, n)
    L = n * 32
    outer, inner = _arch_pts(side, L, H, 0), _arch_pts(side, L, H - depth, depth)
    N = len(outer) - 1
    d.polygon(outer + inner[::-1], fill=BG_DK)                           # the web's shade
    k = 6
    for i in range(0, N, k):                                             # the lattice
        m = min(N, i + k // 2)
        d.line([outer[i], inner[m]], fill=BG); d.line([inner[m], outer[min(N, i + k)]], fill=BG)
    lit, shade = (outer, inner) if side == 'w' else (inner, outer)
    d.line(shade, fill=BG_LO, width=2)
    d.line(lit, fill=BG, width=2)
    for i, (x, y) in enumerate(lit):
        d.point((x - 1, y), fill=BG_HI)
        if i % 5 == 2:
            d.point((x, y), fill=BG_DK)                                  # rivets
    for i, (x, y) in enumerate(shade):
        if i % 5 == 0:
            d.point((x, y), fill=BG_DK)
    sgn = -1 if side == 'w' else 1
    for i, (x, y) in enumerate(outer):                                   # snow lying on the rib's back
        if N * 0.2 < i < N * 0.8 and (i * 7) % 11 < 7:
            d.point((x + sgn, y - 1), fill=SNOW); d.point((x + sgn, y - 2), fill=WHITE)
    x0 = 19 if side == 'w' else 1
    for y0 in (2, L - 16):                                               # the stone piers, a lamp on each
        d.rectangle([x0, y0 + 4, x0 + 11, y0 + 13], fill=STONE)
        d.line([(x0, y0 + 4), (x0, y0 + 13)], fill=WHITE)
        d.rectangle([x0 + 9, y0 + 5, x0 + 11, y0 + 13], fill=STONE_LO)
        d.line([(x0, y0 + 9), (x0 + 11, y0 + 9)], fill=STONE_LO)
        d.rectangle([x0 - 1, y0 + 2, x0 + 12, y0 + 4], fill=SNOW)
        d.line([(x0 - 1, y0 + 2), (x0 + 12, y0 + 2)], fill=WHITE); d.line([(x0 - 1, y0 + 4), (x0 + 12, y0 + 4)], fill=SNOW_LO)
        d.rectangle([x0 + 5, y0 - 1, x0 + 6, y0 + 1], fill=BG_DK)
        d.rectangle([x0 + 4, y0 - 2, x0 + 7, y0 - 1], fill=WARM)
    outline(im)
    hd = ImageDraw.Draw(im)                                              # hangers: thin, uninked, a few
    edge = 31 if side == 'w' else 0
    nh = n
    for j in range(1, nh + 1):
        t = j / (nh + 1)
        x, y = inner[int(round(t * N))]
        gy = int(round((L - 12.0) - t * (L - 24.0)))
        if abs(x - edge) > 2:
            hd.line([(x - sgn, y), (edge, gy)], fill=BG_LO)
            hd.point((edge, gy), fill=BG_DK)
    return im


def asahibashi_brace():
    """The overhead brace between the two crowns: a lattice beam that joins the
    ribs over the deck. Stands in the row of the crown, on a layer above the
    player, starting in the west rib's column."""
    im, d = canvas(4, 1)                 # 128 x 32
    xa, xb = 6, 121
    d.line([(xa, 4), (xb, 4)], fill=BG, width=2)
    d.line([(xa, 3), (xb, 3)], fill=BG_HI)
    d.line([(xa, 11), (xb, 11)], fill=BG_LO, width=2)
    for i, x in enumerate(range(xa, xb - 5, 8)):
        d.line([(x, 5), (x + 4, 10)], fill=BG_LO); d.line([(x + 4, 10), (x + 8, 5)], fill=BG_LO)
        d.point((x + 4, 4), fill=BG_DK)
    for x in (xa - 2, xb - 2):                                           # gussets on the ribs
        d.rectangle([x, 2, x + 5, 13], fill=BG)
        d.line([(x, 2), (x, 13)], fill=BG_HI); d.line([(x + 5, 2), (x + 5, 13)], fill=BG_LO)
        for y in (4, 8, 12):
            d.point((x + 2, y), fill=BG_DK)
    for x in range(14, 114):
        if (x * 7) % 13 < 7:
            d.point((x, 2), fill=SNOW)
            if (x * 3) % 5 == 0:
                d.point((x, 1), fill=WHITE)
    outline(im)
    return im


def oil_tank(d, x, y):
    """The heating-oil tank every Hokkaido house has: 20 wide, feet on y."""
    d.rectangle([x + 2, y - 4, x + 3, y], fill=STONE_DK); d.rectangle([x + 16, y - 4, x + 17, y], fill=STONE_DK)
    d.rectangle([x, y - 17, x + 19, y - 4], fill=rgb('dfe4e8'))
    d.line([(x, y - 17), (x + 19, y - 17)], fill=WHITE); d.line([(x, y - 17), (x, y - 4)], fill=WHITE)
    d.rectangle([x + 16, y - 16, x + 19, y - 4], fill=rgb('b5bec8'))
    d.line([(x, y - 4), (x + 19, y - 4)], fill=STONE_LO)
    d.rectangle([x + 4, y - 13, x + 8, y - 8], fill=WHITE); d.line([(x + 5, y - 10), (x + 7, y - 10)], fill=RED)
    d.rectangle([x + 11, y - 20, x + 13, y - 18], fill=RED)
    d.rectangle([x, y - 20, x + 9, y - 18], fill=SNOW); d.line([(x + 1, y - 21), (x + 8, y - 21)], fill=WHITE)
    d.line([(x + 14, y - 19), (x + 19, y - 19)], fill=SNOW)


def house_red():
    """A Hokkaido house, eaves to the street: a steep red standing-seam roof
    with the snow half slid off it, a dormer, a block chimney, a glazed
    porch against the wind, the oil tank by the wall."""
    im, d = canvas(3, 4)                 # 96 x 128
    siding, siding_lo, siding_hi = rgb('ead9b4'), rgb('c9b588'), rgb('f7ecd2')
    d.rectangle([72, 6, 81, 30], fill=STONE)                             # the chimney
    d.line([(72, 6), (72, 30)], fill=WHITE); d.rectangle([79, 6, 81, 30], fill=STONE_LO)
    for y in range(11, 30, 5):
        d.line([(72, y), (81, y)], fill=STONE_LO)
    d.rectangle([70, 3, 83, 6], fill=STONE_DK); d.line([(70, 2), (83, 2)], fill=SNOW)
    scan = [(y, 12 - (y - 14) * 10 // 48, 83 + (y - 14) * 10 // 48) for y in range(14, 63)]
    seam_roof(d, scan, ROOF_R, ROOF_R_HI, ROOF_R_LO, step=6)
    for y, x0, x1 in scan:
        d.point((x0, y), fill=ROOF_R_HI); d.point((x1, y), fill=ROOF_R_LO)
    # snow: the ridge and upper slope still deep, the lower slope has slid
    for x in range(11, 85):
        top = 10 - ((x * 5) % 7 in (0, 1)) + (x in (11, 84))
        bot = 33 + int(round(5 * math.sin(x / 7.0) + 3 * math.sin(x / 2.9 + 1))) + (4 if 50 < x < 70 else 0)
        d.line([(x, top), (x, bot)], fill=SNOW)
        d.point((x, top), fill=WHITE); d.point((x, top + 1), fill=WHITE)
        d.point((x, bot), fill=SNOW_SH); d.point((x, bot - 1), fill=SNOW_LO)
        if x > 76:
            d.line([(x, top + 2), (x, bot - 1)], fill=SNOW_LO)
    d.rectangle([72, 6, 81, 14], fill=STONE); d.line([(72, 6), (72, 14)], fill=WHITE)   # chimney over the snow
    d.rectangle([79, 6, 81, 14], fill=STONE_LO)
    d.line([(4, 54), (91, 54)], fill=ROOF_R_LO)                          # the snow guard
    for x in range(6, 90, 9):
        d.rectangle([x, 51, x + 4, 53], fill=SNOW); d.point((x + 1, 50), fill=WHITE)
    # the dormer
    d.polygon([(34, 44), (46, 30), (58, 44)], fill=ROOF_R_LO)
    d.polygon([(32, 44), (46, 27), (60, 44), (57, 44), (46, 31), (35, 44)], fill=SNOW)
    d.line([(46, 27), (60, 44)], fill=SNOW_LO); d.line([(32, 44), (46, 27)], fill=WHITE)
    d.rectangle([37, 44, 55, 56], fill=siding)
    lit_window(d, 40, 45, 52, 54, frame=WHITE, lit=True)
    d.rectangle([0, 62, 95, 64], fill=ROOF_R_LO)                         # the eave
    d.line([(0, 62), (95, 62)], fill=ROOF_R)
    icicles(d, 2, 93, 65, seed=4)
    # the wall
    boards_h(d, 6, 65, 89, 121, siding, siding_lo, None, step=4)
    d.rectangle([6, 65, 89, 67], fill=siding_lo)
    d.line([(6, 68), (6, 121)], fill=siding_hi); d.rectangle([85, 68, 89, 121], fill=siding_lo)
    lit_window(d, 10, 76, 28, 94, frame=WHITE, lit=True, curtain=rgb('d98a7a'))
    lit_window(d, 68, 76, 86, 94, frame=WHITE, lit=False)
    # the glazed porch (cell 1,3) with its own bit of roof
    d.rectangle([34, 80, 61, 121], fill=STONE)
    d.rectangle([36, 82, 59, 121], fill=GLASS)
    d.rectangle([40, 86, 55, 121], fill=mix(WARM, WOOD, 0.4))            # the inner door, lit
    d.rectangle([43, 90, 52, 102], fill=WARM)
    d.rectangle([53, 104, 54, 108], fill=GOLD)
    for x in (36, 47, 59):
        d.line([(x, 82), (x, 121)], fill=STONE)
    d.line([(36, 100), (59, 100)], fill=STONE)
    d.line([(38, 84), (38, 98)], fill=GLASS_HI); d.line([(49, 84), (49, 92)], fill=GLASS_HI)
    scan = [(y, 32 - (y - 74), 63 + (y - 74)) for y in range(74, 80)]
    seam_roof(d, scan, ROOF_R, ROOF_R_HI, ROOF_R_LO, step=6)
    snow_slab(d, 31, 64, 70, 74, seed=2, shade_from=58)
    d.rectangle([4, 121, 91, 124], fill=STONE_LO); d.line([(4, 121), (91, 121)], fill=STONE)
    oil_tank(d, 67, 121)
    # a shovel in the heap that came off the roof
    for x in range(4, 33):
        t = (x - 4) / 28
        top = 125 - int(round(15 * math.sin(math.pi * t) ** 0.7)) + (x % 5 == 0)
        d.line([(x, top), (x, 126)], fill=SNOW)
        d.point((x, top), fill=WHITE)
        if x > 24:
            d.line([(x, top + 1), (x, 126)], fill=SNOW_LO)
    d.line([(4, 126), (32, 126)], fill=SNOW_SH)
    d.line([(22, 96), (17, 114)], fill=WOOD_LO, width=2)
    d.rectangle([20, 93, 25, 96], fill=WOOD_DK)
    d.polygon([(13, 112), (20, 114), (18, 121), (11, 119)], fill=RED)
    drift(d, 60, 94, 127, 3, seed=6)
    outline(im)
    puffs(im, 77, -2 + 2, n=1, seed=2, colour=(206, 214, 228), a0=215)
    return im


def house_blue():
    """The other Hokkaido house: a 'triangle roof' - a steep blue gable to the
    street, the gable boarded dark, a stainless stovepipe up the wall, the
    winter's firewood stacked under the window."""
    im, d = canvas(3, 4)                 # 96 x 128
    wall, wall_lo, wall_hi = rgb('dfe6e2'), rgb('b9c5c2'), rgb('f3f7f5')
    gab, gab_lo, gab_hi = rgb('56677f'), rgb('3f4d63'), rgb('7386a0')
    ax, ay, ey = 46, 12, 62                                              # apex, eave height
    # the gable wall
    for y in range(ay + 6, ey):
        half = int((y - ay - 5) * 38 / (ey - ay - 5))
        for x in range(ax - half, ax + half + 1):
            k = x % 4
            d.point((x, y), fill=gab_lo if k == 3 else (gab_hi if k == 0 and x < ax else gab))
    # the roof's two slopes: blue metal seen edge on, snow lying thick on both
    for i in range(0, 46):
        t = i / 45
        y = ay + t * (ey - ay)
        for side in (-1, 1):
            x = ax + side * (1 + t * 43)
            xi, yi = int(round(x)), int(round(y))
            d.rectangle([xi - 1, yi + 3, xi + 1, yi + 7], fill=ROOF_B if side < 0 else ROOF_B_LO)
            d.point((xi - side, yi + 7), fill=ROOF_B_LO)
            if side < 0:
                d.point((xi - 1, yi + 3), fill=ROOF_B_HI)
            depth = 6 - int(3 * t) + ((i * 5) % 7 == 0)
            d.rectangle([xi - 1, yi + 3 - depth, xi + 1, yi + 2], fill=SNOW if side < 0 else SNOW_LO)
            d.rectangle([xi - 1, yi + 3 - depth, xi + 1, yi + 4 - depth], fill=WHITE if side < 0 else SNOW)
    d.ellipse([ax - 6, ay - 6, ax + 6, ay + 5], fill=SNOW)               # the heap on the ridge
    d.arc([ax - 6, ay - 6, ax + 6, ay + 5], 180, 300, fill=WHITE)
    for sx in (2, 86):                                                   # the eave ends, a lump on each
        d.rectangle([sx, ey + 2, sx + 6, ey + 6], fill=ROOF_B_LO if sx > 40 else ROOF_B)
        d.ellipse([sx - 1, ey - 5, sx + 8, ey + 3], fill=SNOW if sx < 40 else SNOW_LO)
    lit_window(d, 39, 36, 53, 50, frame=WHITE, lit=True)                 # the attic window
    # the wall below
    d.rectangle([8, ey, 84, ey + 2], fill=WHITE); d.line([(8, ey + 2), (84, ey + 2)], fill=wall_lo)
    boards_h(d, 8, ey + 3, 84, 121, wall, wall_lo, None, step=4)
    d.line([(8, ey + 3), (8, 121)], fill=wall_hi); d.rectangle([80, ey + 3, 84, 121], fill=wall_lo)
    lit_window(d, 11, 76, 29, 92, frame=WHITE, lit=False)
    lit_window(d, 63, 76, 79, 92, frame=WHITE, lit=True, curtain=rgb('8fb0d8'))
    # the front door (cell 1,3) under a little flat canopy, a porch light
    d.rectangle([36, 82, 57, 121], fill=WHITE)
    d.rectangle([38, 84, 55, 121], fill=ROOF_B)
    d.line([(38, 84), (38, 121)], fill=ROOF_B_HI); d.rectangle([53, 84, 55, 121], fill=ROOF_B_LO)
    d.rectangle([41, 87, 46, 100], fill=WARM); d.line([(41, 87), (46, 87)], fill=WHITE)
    d.rectangle([51, 102, 52, 106], fill=GOLD)
    d.rectangle([33, 77, 60, 80], fill=STONE); d.line([(33, 80), (60, 80)], fill=STONE_LO)
    snow_slab(d, 33, 60, 73, 76, seed=5, shade_from=54)
    d.rectangle([59, 84, 61, 87], fill=WARM); d.point((60, 83), fill=CHAR_LO)
    d.rectangle([34, 121, 59, 124], fill=STONE); d.line([(34, 124), (59, 124)], fill=STONE_LO)
    d.rectangle([6, 121, 86, 123], fill=STONE_LO)
    d.rectangle([34, 121, 59, 124], fill=STONE); d.line([(34, 121), (59, 121)], fill=WHITE)
    # firewood under the window
    for j in range(4):
        for i in range(5):
            cx, cy = 12 + i * 5 + (j % 2) * 2, 118 - j * 5
            d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=rgb('b98a5c'))
            d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], outline=rgb('6f4a30'))
            d.point((cx, cy), fill=rgb('e3bb8a'))
    d.rectangle([9, 97, 36, 99], fill=SNOW); d.line([(10, 96), (35, 96)], fill=WHITE)
    d.line([(9, 100), (36, 100)], fill=SNOW_LO)
    # the stovepipe
    d.rectangle([81, 100, 91, 103], fill=STONE); d.line([(81, 100), (91, 100)], fill=WHITE)
    d.rectangle([88, 44, 91, 103], fill=STONE)
    d.line([(88, 44), (88, 99)], fill=WHITE); d.line([(91, 44), (91, 103)], fill=STONE_LO)
    for y in (58, 78, 96):
        d.line([(88, y), (91, y)], fill=STONE_DK)
    d.rectangle([86, 41, 93, 43], fill=STONE_LO); d.line([(86, 41), (93, 41)], fill=STONE)
    drift(d, 0, 34, 127, 3, seed=1); drift(d, 60, 95, 127, 5, seed=7)
    outline(im)
    puffs(im, 89, 37, n=7, seed=5, lean=1, colour=(206, 214, 228), a0=215)
    return im


def snow_fence():
    """A highway snow fence, one cell of it, two cells tall: galvanised steel
    posts carrying five angled louvre slats, a gap under them, and the drift
    it drops on its lee side. Tiles east-west (drawn three cells long and the
    middle cut out, so the slats join)."""
    big = Image.new('RGBA', (96, 64), CLEAR)
    d = ImageDraw.Draw(big)
    st, st_hi, st_lo, st_dk = rgb('aab2bf'), rgb('e3e8ee'), rgb('7d8696'), rgb('4b5565')
    for c in range(3):                                                   # the back stays, behind the slats
        x = c * 32 + 16
        d.line([(x + 2, 40), (x + 9, 58)], fill=st_dk, width=2)
    for j in range(5):                                                   # louvres: lit on top, a dark slot under each
        y = 9 + j * 7
        d.rectangle([0, y, 95, y + 4], fill=st)
        d.rectangle([0, y, 95, y + 1], fill=st_hi)
        d.line([(0, y + 4), (95, y + 4)], fill=st_lo)
        if j < 4:
            d.rectangle([0, y + 5, 95, y + 6], fill=st_dk)
        for x in range(6 + j * 5, 96, 16):
            d.point((x, y + 2), fill=st_lo)
    for x in range(96):                                                  # snow lying along the top slat
        d.point((x, 8), fill=SNOW)
        d.point((x, 7), fill=WHITE if (x * 5) % 9 < 6 else SNOW)
        if (x * 3) % 7 == 0:
            d.point((x, 6), fill=WHITE)
    for c in range(3):                                                   # the posts, in front
        x = c * 32 + 14
        d.rectangle([x, 4, x + 3, 60], fill=st_lo)
        d.line([(x, 4), (x, 60)], fill=st_hi); d.line([(x + 3, 4), (x + 3, 60)], fill=st_dk)
        for y in (11, 25, 39):
            d.point((x + 1, y), fill=st_dk)
        d.rectangle([x - 1, 2, x + 4, 4], fill=SNOW); d.line([(x, 1), (x + 3, 1)], fill=WHITE)
    for x in range(96):                                                  # the drift on its lee side
        u = (x % 32) / 32 * 2 * math.pi
        top = 52 - int(round(3.0 * math.sin(u + 0.6) + 1.4 * math.sin(2 * u + 1)))
        d.line([(x, top), (x, 62)], fill=SNOW)
        d.point((x, top), fill=WHITE); d.point((x, top + 1), fill=WHITE)
        d.point((x, 62), fill=SNOW_SH); d.point((x, 61), fill=SNOW_LO)
        if math.cos(u + 0.6) < -0.2 and top + 3 < 61:                    # the lee slope of each hump, in shade
            d.line([(x, top + 2), (x, top + 4)], fill=SNOW_LO)
    outline(big)
    return big.crop((32, 0, 64, 64))


def zoo_fence(kind='h'):
    """The zoo's boundary, two cells tall: timber posts, a green rail top and
    bottom, green wire mesh you can see the snow through. 'h' is one cell of
    it with its post at the west end (tiles east-west); 'end' is the lone
    post that closes a run at its east end."""
    big = Image.new('RGBA', (96, 64), CLEAR)
    d = ImageDraw.Draw(big)
    x0, x1 = (0, 95) if kind == 'h' else (32, 36)
    if kind == 'h':
        for y in range(19, 56):
            for x in range(96):
                on = (x + y) % 6 == 0 or (x - y) % 6 == 0
                d.point((x, y), fill=ROOF_G if on else (47, 86, 70, 70))
        for y, c, hi in ((17, ROOF_G, ROOF_G_HI), (55, ROOF_G_LO, ROOF_G)):
            d.rectangle([0, y, 95, y + 2], fill=c); d.line([(0, y), (95, y)], fill=hi)
        for x in range(96):
            if (x * 5) % 13 < 9:
                d.point((x, 16), fill=SNOW)
                if (x * 3) % 5 == 0:
                    d.point((x, 15), fill=WHITE)
    for c in range(3):
        x = c * 32
        if not (x0 <= x <= x1):
            continue
        d.rectangle([x, 12, x + 4, 60], fill=TIMBER)
        d.line([(x, 12), (x, 60)], fill=TIMBER_HI); d.rectangle([x + 3, 12, x + 4, 60], fill=TIMBER_LO)
        d.line([(x + 4, 12), (x + 4, 60)], fill=TIMBER_DK)
        d.rectangle([x - 1, 9, x + 5, 11], fill=SNOW); d.line([(x, 8), (x + 4, 8)], fill=WHITE)
        d.line([(x - 1, 11), (x + 5, 11)], fill=SNOW_LO)
    for x in range(x0 if kind == 'h' else 30, (x1 if kind == 'h' else 39) + 1):   # snow against its foot
        top = 59 - ((x * 5) % 7 in (0, 1)) - (x % 32 < 7)
        d.line([(x, top), (x, 62)], fill=SNOW)
        d.point((x, top), fill=WHITE); d.point((x, 62), fill=SNOW_LO)
    outline(big)
    return big.crop((32, 0, 64, 64))


def fishing_tent():
    """An ice-fishing tent on the frozen river: an orange dome with a dark
    door, snow on its crown, a red sled and a bucket beside it."""
    im, d = canvas(2, 2)                 # 64 x 64
    o, o_hi, o_lo, o_dk = ORANGE, rgb('f8b070'), rgb('c8642a'), rgb('8f431c')
    d.pieslice([6, 20, 50, 94], 180, 360, fill=o)
    d.rectangle([6, 57, 50, 60], fill=o)
    d.pieslice([24, 20, 50, 94], 270, 360, fill=o_lo)
    d.rectangle([37, 57, 50, 60], fill=o_lo)
    d.arc([8, 22, 48, 92], 195, 255, fill=o_hi)
    d.arc([17, 20, 39, 94], 180, 360, fill=o_dk)                         # the pole sleeves
    d.line([(6, 60), (50, 60)], fill=o_dk)
    d.polygon([(21, 60), (28, 36), (35, 60)], fill=rgb('3a2a2a'))        # the door, a lamp inside
    d.polygon([(25, 60), (28, 48), (31, 60)], fill=rgb('5a3c2c'))
    d.rectangle([27, 52, 29, 55], fill=WARM)
    d.polygon([(35, 60), (28, 36), (31, 36), (40, 52)], fill=o_hi)       # the flap tied back
    d.line([(35, 60), (40, 52)], fill=o_dk)
    d.chord([15, 18, 41, 30], 180, 360, fill=SNOW)                       # snow on its crown
    d.arc([15, 18, 41, 30], 190, 300, fill=WHITE)
    d.line([(16, 24), (40, 24)], fill=SNOW_LO)
    d.polygon([(49, 55), (62, 55), (60, 60), (51, 60)], fill=RED)        # a sled
    d.line([(49, 55), (62, 55)], fill=RED_HI); d.line([(51, 60), (60, 60)], fill=RED_DK)
    d.rectangle([53, 48, 58, 54], fill=STONE); d.line([(53, 48), (58, 48)], fill=WHITE)
    d.rectangle([57, 49, 58, 54], fill=STONE_LO)
    drift(d, 2, 22, 62, 2, seed=4); drift(d, 34, 52, 62, 2, seed=6)
    outline(im)
    return under(im, [(2, 56, 62, 63)])


CRACK_HI, CRACK_LO = (244, 251, 255, 255), (150, 186, 212, 255)


def ice_crack(variant):
    """Cracks in the river ice: a transparent overlay for an ice cell. A white
    fracture with a blue shadow one pixel under it, a patch of wind-scoured
    snow."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    d = ImageDraw.Draw(im)
    if variant == 'a':
        runs = ([(3, 9), (9, 12), (14, 11), (20, 16), (28, 18)], [(14, 11), (16, 5), (21, 3)],
                [(20, 16), (18, 23), (22, 28)], [(9, 12), (6, 18)])
        snow = (22, 22, 29, 25)
    else:
        runs = ([(29, 6), (22, 9), (19, 15), (11, 17), (4, 24)], [(19, 15), (24, 21), (23, 27)],
                [(11, 17), (9, 10)], [(22, 9), (20, 4)])
        snow = (4, 6, 12, 9)
    for run in runs:
        d.line([(x, y + 1) for x, y in run], fill=CRACK_LO)
    for run in runs:
        d.line(run, fill=CRACK_HI)
    d.ellipse(snow, fill=(240, 246, 252, 255))
    d.line([(snow[0] + 1, snow[3]), (snow[2] - 1, snow[3])], fill=(203, 222, 236, 255))
    return im


def ice_fishing_hole():
    """A hole cut for smelt fishing: dark water in a ring of chipped ice, a
    folding stool, a short rod on a rest, a bucket."""
    im, d = canvas(1, 1)                 # 32 x 32
    d.ellipse([7, 17, 17, 24], fill=rgb('2c5280'))                       # the hole
    d.arc([7, 17, 17, 24], 180, 360, fill=rgb('17304f'))
    d.arc([6, 16, 18, 25], 0, 180, fill=WHITE)                           # its lit lower lip
    d.line([(10, 22), (13, 22)], fill=rgb('5f8fc0'))
    for x, y, w in ((1, 20, 4), (2, 23, 5), (4, 26, 3), (0, 17, 2)):     # the ice chipped out of it, heaped
        d.rectangle([x, y, x + w, y + 2], fill=WHITE); d.line([(x, y + 2), (x + w, y + 2)], fill=(203, 222, 236, 255))
    d.line([(12, 15), (22, 9)], fill=WOOD_DK)                            # the rod, its line into the hole
    d.line([(12, 15), (12, 20)], fill=WHITE)
    d.rectangle([20, 9, 23, 10], fill=RED)
    d.rectangle([21, 12, 30, 13], fill=ROOF_B); d.line([(21, 12), (30, 12)], fill=ROOF_B_HI)   # the stool
    d.line([(22, 14), (29, 21)], fill=CHAR_LO); d.line([(29, 14), (22, 21)], fill=CHAR_LO)
    d.rectangle([24, 22, 29, 28], fill=STONE); d.line([(24, 22), (29, 22)], fill=WHITE)     # the bucket
    d.rectangle([28, 23, 29, 28], fill=STONE_LO); d.arc([23, 18, 30, 26], 180, 360, fill=CHAR_LO)
    im2 = Image.new('RGBA', im.size, CLEAR)
    im2.alpha_composite(im)
    hole = im.crop((0, 11, 21, 30))                                      # ink the gear, not the hole
    gear = im.copy()
    ImageDraw.Draw(gear).rectangle([0, 11, 20, 31], fill=CLEAR)
    outline(gear)
    out = Image.new('RGBA', im.size, CLEAR)
    out.alpha_composite(hole, (0, 11))
    out.alpha_composite(gear)
    return out


# ==============================================================================
# Asahiyama Zoo gate
# ==============================================================================
def penguin(d, x, y, step=0, chick=False):
    """A king penguin walking left, its feet on y: 11 wide, 18 tall. `step`
    0 / 1 puts the other foot forward and swings the flipper."""
    if chick:
        fur, fur_hi, fur_lo = rgb('8b6b54'), rgb('ab8a70'), rgb('654a3a')
        d.ellipse([x + 1, y - 11, x + 9, y - 1], fill=fur)
        d.ellipse([x + 2, y - 15, x + 8, y - 9], fill=fur)
        d.arc([x + 1, y - 11, x + 9, y - 1], 150, 260, fill=fur_hi)
        d.chord([x + 1, y - 11, x + 9, y - 1], 320, 80, fill=fur_lo)
        d.line([(x, y - 12), (x + 2, y - 12)], fill=INK)
        d.point((x + 4, y - 13), fill=INK)
        d.rectangle([x + 2 + step, y - 1, x + 4 + step, y], fill=rgb('3a3a44'))
        d.rectangle([x + 6 - step, y - 1, x + 8 - step, y], fill=rgb('3a3a44'))
        return
    d.ellipse([x + 1, y - 13, x + 10, y - 1], fill=PEN)                  # the back
    d.ellipse([x + 1, y - 12, x + 7, y - 1], fill=WHITE)                 # the belly, to the front
    d.chord([x + 1, y - 12, x + 7, y - 1], 30, 150, fill=SNOW_LO)
    d.ellipse([x + 2, y - 18, x + 9, y - 11], fill=PEN)                  # the head
    d.line([(x - 1, y - 16 + step), (x + 2, y - 15)], fill=PEN)          # the bill, a streak of orange
    d.point((x + 1, y - 15 + step), fill=ORANGE)
    d.rectangle([x + 6, y - 15, x + 7, y - 13], fill=ORANGE)             # the ear patch
    d.point((x + 6, y - 12), fill=AMBER)
    d.line([(x + 2, y - 11), (x + 4, y - 11)], fill=AMBER)               # the gold bib
    d.point((x + 2, y - 10), fill=rgb('fde38a')); d.point((x + 3, y - 10), fill=rgb('fde38a'))
    d.point((x + 4, y - 16), fill=PEN_HI)
    fx = x + 8 + (2 if step else 0)                                      # the flipper swings
    d.line([(x + 7, y - 10), (fx, y - 4)], fill=PEN_HI, width=2)
    if step:
        d.rectangle([x + 1, y - 1, x + 4, y], fill=ORANGE); d.rectangle([x + 6, y - 2, x + 8, y - 1], fill=rgb('c0682a'))
    else:
        d.rectangle([x + 2, y - 2, x + 4, y - 1], fill=rgb('c0682a')); d.rectangle([x + 5, y - 1, x + 8, y], fill=ORANGE)


def penguin_walk(variant):
    im, d = canvas(2, 1)                 # 64 x 32
    if variant == 'a':
        spots = ((3, 28, 0, False), (18, 27, 1, False), (33, 28, 0, False), (49, 27, 1, False))
    else:
        spots = ((4, 27, 1, False), (20, 28, 0, True), (34, 28, 1, True), (49, 27, 0, False))
    for x, y, step, chick in spots:
        penguin(d, x, y, step, chick)
    outline(im)
    return under(im, [(x - 1, y - 1, x + 11, y + 3) for x, y, _s, _c in spots])


def bunting(d, x0, x1, y, sag=5):
    cols = (RED, AMBER, ROOF_G, rgb('3a8fd8'), WHITE, ORANGE)
    n = (x1 - x0) // 8
    for i in range(n + 1):
        t = i / max(1, n)
        yy = y + int(round(sag * math.sin(math.pi * t)))
        x = x0 + i * 8
        if i < n:
            t2 = (i + 1) / n
            d.line([(x, yy), (x + 8, y + int(round(sag * math.sin(math.pi * t2))))], fill=INK)
            c = cols[i % len(cols)]
            d.polygon([(x + 1, yy + 1), (x + 7, yy + 1), (x + 4, yy + 7)], fill=c)


def small_bear(d, x, y, body=WHITE, lo=SNOW_LO):
    """A polar bear on all fours facing left, 24 wide, its paws on y."""
    d.ellipse([x + 6, y - 14, x + 23, y - 4], fill=body)
    d.ellipse([x + 4, y - 16, x + 15, y - 5], fill=body)
    d.ellipse([x, y - 14, x + 9, y - 6], fill=body)
    d.polygon([(x - 2, y - 10), (x + 2, y - 12), (x + 3, y - 7), (x - 1, y - 7)], fill=body)
    d.chord([x + 6, y - 14, x + 23, y - 4], 10, 170, fill=lo)
    for lx in (x + 6, x + 18):
        d.rectangle([lx, y - 6, lx + 3, y], fill=body); d.line([(lx + 3, y - 5), (lx + 3, y)], fill=lo)
    for lx in (x + 10, x + 14):
        d.rectangle([lx, y - 5, lx + 2, y], fill=lo)
    d.point((x - 2, y - 10), fill=INK); d.point((x + 3, y - 11), fill=INK)
    d.ellipse([x + 5, y - 17, x + 8, y - 14], fill=body)
    d.point((x + 6, y - 16), fill=lo)
    d.line([(x + 9, y - 6), (x + 9, y - 10)], fill=lo)                   # the shoulder


def zoo_gate():
    """The zoo's gate: two timber pylons on stone feet carrying a sky-blue
    board (ASAHI ZOO, a look-alike name) with a penguin badge; a polar bear
    and two penguins stand in the snow on top of it; bunting underneath. You
    walk through the three middle cells."""
    im, d = canvas(5, 4)                 # 160 x 128
    for x0 in (3, 131):                                                  # the pylons
        boards_v(d, x0, 50, x0 + 25, 118, TIMBER, TIMBER_LO, TIMBER_HI, step=5)
        d.rectangle([x0 + 21, 50, x0 + 25, 118], fill=TIMBER_LO)
        d.rectangle([x0, 50, x0 + 25, 53], fill=TIMBER_DK)               # the board's shadow
        d.rectangle([x0 - 2, 114, x0 + 27, 124], fill=STONE)
        d.line([(x0 - 2, 114), (x0 + 27, 114)], fill=WHITE); d.rectangle([x0 + 23, 115, x0 + 27, 124], fill=STONE_LO)
        d.line([(x0 - 2, 119), (x0 + 27, 119)], fill=STONE_LO)
        d.rectangle([x0 + 4, 68, x0 + 20, 98], fill=WHITE)               # a poster panel on each
    d.rectangle([9, 70, 21, 96], fill=rgb('3a8fd8'))                     # a seal, nose up
    d.ellipse([11, 80, 20, 93], fill=STONE_LO); d.ellipse([11, 74, 17, 83], fill=STONE_LO)
    d.point((12, 77), fill=INK); d.ellipse([12, 71, 15, 74], fill=AMBER)
    d.rectangle([137, 70, 149, 96], fill=ROOF_G)                         # a red-crowned crane
    d.ellipse([139, 82, 148, 90], fill=WHITE); d.line([(141, 82), (140, 74)], fill=WHITE, width=2)
    d.point((140, 73), fill=RED); d.line([(137, 75), (139, 75)], fill=INK)
    d.line([(143, 90), (143, 95)], fill=INK); d.line([(146, 90), (146, 95)], fill=INK)
    d.rectangle([146, 84, 148, 88], fill=INK)
    # the board across the top of both
    blue, blue_hi, blue_lo = rgb('3a8fd8'), rgb('7dbdf2'), rgb('2565a8')
    d.rectangle([1, 23, 158, 49], fill=blue)
    d.rectangle([1, 23, 158, 24], fill=blue_hi); d.rectangle([1, 48, 158, 49], fill=blue_lo)
    d.rectangle([153, 25, 158, 49], fill=blue_lo)
    d.rectangle([4, 26, 155, 46], outline=WHITE)
    text(d, 'ASAHI', 14, 29, WHITE, scale=2)
    text(d, 'ZOO', 110, 29, AMBER, scale=2)
    d.ellipse([82, 26, 100, 46], fill=WHITE)                             # the penguin badge
    d.ellipse([86, 28, 96, 45], fill=PEN); d.ellipse([88, 33, 94, 45], fill=WHITE)
    d.rectangle([89, 31, 90, 32], fill=WHITE); d.rectangle([93, 31, 94, 32], fill=WHITE)
    d.polygon([(90, 34), (93, 34), (91, 37)], fill=ORANGE)
    snow_slab(d, 0, 159, 19, 22, seed=6, shade_from=150)
    # the figures standing in the snow on top of it
    small_bear(d, 14, 20, body=rgb('f4ead0'), lo=rgb('cdbf9c'))
    penguin(d, 122, 20, 0); penguin(d, 136, 20, 1)
    for x0, x1 in ((12, 40), (120, 149)):                                # their feet sunk in it
        d.line([(x0, 20), (x1, 20)], fill=SNOW); d.line([(x0, 19), (x1, 19)], fill=WHITE)
    d.line([(13, 18), (39, 18)], fill=SNOW_SH)                           # the bear's shadow on the snow
    bunting(d, 29, 131, 52, sag=7)
    drift(d, 0, 34, 127, 5, seed=3); drift(d, 126, 159, 127, 5, seed=8)
    outline(im)
    return im


def ticket_booth():
    im, d = canvas(2, 3)                 # 64 x 96
    # a green hipped roof under snow
    scan = [(y, 8 - (y - 14) * 7 // 14, 55 + (y - 14) * 7 // 14) for y in range(14, 29)]
    seam_roof(d, scan, ROOF_G, ROOF_G_HI, ROOF_G_LO, step=6)
    snow_slab(d, 8, 55, 7, 18, seed=7, shade_from=46)
    d.rectangle([0, 29, 63, 30], fill=ROOF_G_LO)
    icicles(d, 2, 61, 31, seed=3)
    # the hut: cream boards, timber corners
    boards_v(d, 5, 31, 58, 90, CREAM, CREAM_LO, None, step=5)
    d.rectangle([5, 31, 58, 33], fill=CREAM_DK)
    for x in (5, 55):
        d.rectangle([x, 31, x + 3, 90], fill=TIMBER_LO); d.line([(x, 31), (x, 90)], fill=TIMBER)
    d.rectangle([10, 35, 53, 45], fill=AMBER)                            # the board
    d.line([(10, 35), (53, 35)], fill=rgb('fde38a')); d.line([(10, 45), (53, 45)], fill=rgb('c8941c'))
    text(d, 'TICKET', 32 - text_w('TICKET') // 2, 37, DARK)
    for x in range(8, 56):                                               # a red and white awning
        c = RED if (x // 5) % 2 == 0 else WHITE
        d.line([(x, 48), (x, 53)], fill=c)
        d.point((x, 54 + ((x % 5) in (1, 2, 3))), fill=RED_DK if c == RED else CREAM_LO)
    d.line([(8, 47), (55, 47)], fill=SNOW)
    # the window: the clerk, a slot, the counter
    d.rectangle([12, 56, 51, 76], fill=WOOD_DK)
    d.rectangle([13, 57, 50, 75], fill=WARM); d.line([(13, 57), (50, 57)], fill=WHITE)
    d.ellipse([27, 60, 35, 69], fill=rgb('e9b796')); d.rectangle([26, 59, 36, 62], fill=ROOF_G)
    d.rectangle([24, 69, 38, 75], fill=ROOF_G); d.point((29, 65), fill=INK); d.point((33, 65), fill=INK)
    d.line([(31, 57), (31, 59)], fill=WOOD_DK)
    d.rectangle([40, 60, 48, 70], fill=WHITE); d.line([(42, 63), (46, 63)], fill=RED); d.line([(42, 66), (46, 66)], fill=INK)
    d.rectangle([10, 76, 53, 79], fill=TIMBER); d.line([(10, 76), (53, 76)], fill=TIMBER_HI)
    d.line([(10, 79), (53, 79)], fill=TIMBER_DK)
    d.rectangle([24, 82, 39, 88], fill=rgb('3a8fd8'))                    # a poster under the counter
    d.ellipse([28, 83, 34, 88], fill=WHITE); d.point((30, 85), fill=INK)
    d.rectangle([3, 90, 60, 92], fill=STONE_LO); d.line([(3, 90), (60, 90)], fill=STONE)
    drift(d, 0, 22, 95, 5, seed=5); drift(d, 42, 63, 95, 4, seed=2)
    outline(im)
    return im


def seal_statue():
    """A spotted seal rearing on a boulder: grey stone, pale belly, dark
    spots, whiskers, snow along its back, a plaque."""
    im, d = canvas(2, 2)                 # 64 x 64
    s, s_hi, s_lo, s_dk = rgb('8e99a8'), rgb('c3ccd6'), rgb('6a7586'), rgb('4b5565')
    d.polygon([(5, 60), (8, 47), (20, 42), (46, 42), (57, 48), (60, 60)], fill=STONE_LO)   # the boulder
    d.polygon([(8, 47), (20, 42), (46, 42), (50, 45), (22, 46), (11, 50)], fill=STONE)
    d.line([(24, 52), (30, 59)], fill=STONE_DK); d.line([(44, 49), (41, 58)], fill=STONE_DK)
    d.polygon([(46, 44), (57, 48), (60, 60), (50, 60)], fill=STONE_DK)
    d.rectangle([14, 52, 23, 57], fill=GOLD); d.line([(16, 54), (21, 54)], fill=WOOD_DK)
    d.line([(14, 52), (23, 52)], fill=rgb('e6cf94'))
    d.ellipse([22, 27, 58, 45], fill=s)                                  # the hind body
    d.chord([22, 27, 58, 45], 10, 170, fill=s_lo)
    d.polygon([(54, 33), (63, 24), (62, 33), (63, 40), (55, 40)], fill=s_lo)             # the tail flippers
    d.line([(56, 34), (62, 27)], fill=s)
    d.polygon([(14, 44), (12, 24), (20, 12), (30, 14), (36, 30), (34, 44)], fill=s)     # the chest, reared
    d.polygon([(14, 44), (12, 26), (17, 16), (21, 22), (22, 44)], fill=s_hi)            # the pale belly
    d.ellipse([10, 4, 30, 21], fill=s)                                   # the head, nose up and left
    d.ellipse([5, 6, 18, 16], fill=s_hi)
    d.arc([10, 4, 30, 21], 200, 320, fill=s_hi)
    d.rectangle([5, 8, 7, 10], fill=INK)                                 # the nose
    d.rectangle([17, 9, 19, 11], fill=INK); d.point((17, 9), fill=WHITE)   # the eye
    for dy in (-1, 1, 3):
        d.line([(8, 12 + dy // 2), (1, 12 + dy)], fill=s_dk)
    d.polygon([(22, 36), (10, 45), (24, 45), (28, 39)], fill=s_lo)       # the fore flipper
    d.line([(22, 36), (11, 45)], fill=s)
    for k, (x, y) in enumerate(((30, 20), (27, 28), (33, 34), (40, 31), (47, 34), (44, 38), (52, 31), (25, 10), (37, 38))):
        d.rectangle([x, y, x + 1 + k % 2, y + 1], fill=s_dk)
    for x in range(34, 56):                                              # snow along its back
        if (x * 3) % 7 != 0:
            d.point((x, 27 + (x - 45) ** 2 // 60), fill=SNOW)
    d.line([(13, 4), (24, 3)], fill=SNOW); d.line([(15, 3), (22, 2)], fill=WHITE)
    d.line([(20, 42), (45, 42)], fill=SNOW); d.line([(8, 47), (19, 42)], fill=SNOW)
    drift(d, 1, 63, 63, 3, seed=4)
    outline(im)
    return im


# ==============================================================================
# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH or ON
#   glow: lit parts, as (cell, [x, y] in file pixels from the sprite's top-left, colour, what)
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'flat' = on the
#          ground under the player (Non-Collidables + depthBias, as asahikawa-bridge),
#          'overlay' = flat over a floor tile (Over Floor), 'above' = over the player
PIECES = [
    ('asahikawa-station-front_0_0', station_front, (10, 5), 'Station front and Heiwa-dori', dict(
        door=[[4, 4], [5, 4]], solid=rows(10, 2, 4),
        glow=[([4, 4], [282, 250], '#f6dc8c', 'the west pair of sliding doors'),
              ([5, 4], [358, 250], '#f6dc8c', 'the east pair of sliding doors'),
              ([1, 2], [120, 150], '#efc793', 'pendant lamps on the timber lining, west half'),
              ([8, 2], [520, 150], '#efc793', 'pendant lamps on the timber lining, east half')]),
     'Asahikawa Station, the biggest building in town (10x5): a wide glass hall under a thin white roof slab deep '
     'in snow, with the station\'s warm timber lining (slatted ceiling, boarded wall, pendant lamps) showing '
     'through the glazing, four white branching tree columns, timber end walls and soffit, a dark name board '
     '(the kanji for Asahikawa and ASAHIKAWA), a canopy over two pairs of automatic sliding glass doors (tinted '
     'glass with the sky streaking across, a dark split and a pull on each leaf, kick plates, a threshold and a '
     'door mat), and the train hall as a second glazed tier set back behind.'),
    ('heiwa-shop-sake_0_0', shop_sake, (3, 4), 'Station front and Heiwa-dori', dict(
        door=[[1, 3]], solid=rows(3, 1, 3),
        glow=[([1, 3], [96, 210], '#f6dc8c', 'the lit sliding door'), ([0, 2], [44, 190], '#f6dc8c', 'the slatted window')]),
     'A sake brewery shop in kura style: white plaster over a namako (tile and white lattice) dado, dark tiled '
     'roof and pent roof under deep snow, a timber board with the kanji for sake and SAKAGURA (a generic '
     'word: sake cellar), a green cedar ball under the eave, a navy noren, three straw-wrapped casks on their sides (round ends, '
     'rope hoops) by the door.'),
    ('heiwa-shop-woodcraft_0_0', shop_woodcraft, (4, 3), 'Station front and Heiwa-dori', dict(
        door=[[3, 2]], solid=rows(4, 1, 2),
        glow=[([1, 2], [98, 134], '#f6dc8c', 'the showroom window'), ([3, 2], [216, 130], '#f6dc8c', 'the door light')]),
     'A furniture and woodcraft workshop (Asahikawa is a furniture town): low and flat-roofed, honey timber '
     'cladding over a charred-board ground floor, a KAGU CRAFT board with a chair on it, one long lit showroom '
     'window with a spindle-back chair, a table, a shelf and a stool, planks leaning by the door.'),
    ('heiwa-shop-bakery_0_0', shop_bakery, (3, 4), 'Station front and Heiwa-dori', dict(
        door=[[1, 3]], solid=rows(3, 1, 3),
        glow=[([0, 2], [52, 186], '#f6dc8c', 'the bread window'), ([1, 3], [118, 184], '#f6dc8c', 'the door glass')]),
     'A bakery and coffee shop behind a mint-green stepped false front (the pioneer-town shopfront), an oval '
     'board reading pan (bread) in kana with a loaf, a brown and cream striped awning, loaves in a lit window, '
     'a half-glazed door, a hanging coffee-cup sign, a chalkboard, a brick chimney.'),
    ('heiwa-shop-books_0_0', shop_books, (3, 3), 'Station front and Heiwa-dori', dict(
        door=[[2, 2]], solid=rows(3, 1, 2),
        glow=[([0, 2], [66, 136], '#f6dc8c', 'the window of spines'), ([2, 2], [152, 134], '#f6dc8c', 'the door glass')]),
     'A second-hand bookshop: a low flat-roofed front in slate-blue tile, a cream BOOKS board with three books '
     'on it, a green scalloped awning under snow, a lit window with three shelves of coloured spines, a glazed '
     'door with a card in it, a timber sale cart of books out in the snow.'),
    ('ice-sculpture-crane_0_0', ice_crane, (2, 2), 'Station front and Heiwa-dori', dict(
        solid=rows(2, 1, 1)),
     'An ice sculpture in clear blue ice, not packed snow: a red-crowned crane calling, a long thin S of a neck '
     'with the bill up, both wings raised and swept back, long legs, on an ice block. For the middle of the '
     'pedestrian street.'),
    ('ice-sculpture-owl_0_0', ice_owl, (1, 2), 'Station front and Heiwa-dori', dict(
        solid=[[0, 1]]),
     'A smaller ice sculpture: a fish owl facing you on an ice block.'),
    ('heiwa-bench_0_0', bench, (2, 1), 'Station front and Heiwa-dori', dict(
        solid=rows(2, 0, 0)),
     'A slatted timber bench on cast-iron ends, snow along its back and heaped on the seat, one place brushed '
     'clear where somebody sat.'),
    ('heiwa-lamp-post_0_0', heiwa_lamp, (1, 2), 'Station front and Heiwa-dori', dict(
        solid=[[0, 1]], glow=[([0, 0], [31, 30], '#f6dc8c', 'the lantern box (DayNight halo: the key has lamp-post)')]),
     'Heiwa-dori\'s own street lamp: a timber post on a stone foot carrying a woodcraft lantern box with a '
     'warm pane and a dark cap under snow. Its key matches DayNight\'s /lamp-post/ rule, so it gets a halo '
     'at night on the cell it is placed on (the lantern\'s cell); the post stands in the cell below.'),
    ('ramen-shoyu-front_0_0', ramen_shoyu, (4, 4), 'Ramen alley', dict(
        door=[[3, 3]], solid=rows(4, 1, 3),
        glow=[([1, 2], [104, 160], '#f6dc8c', 'the counter window'), ([3, 3], [214, 190], '#f6dc8c', 'the door'),
              ([3, 2], [244, 146], '#d16b56', 'the red paper lantern')]),
     'The shoyu-ramen counter: a low tin roof deep in snow with a steaming stovepipe, a long red board (ramen '
     'in kana, a bowl, the kanji asahi in a white roundel), charred boards, a wide lamplit counter window '
     '(the cook, a stock pot, stacked bowls, menu slips, a short red noren, four red stools), a lattice door '
     'under a red noren, two red ramen nobori, a red paper lantern, steam off the pot and the pipe only.'),
    ('ramen-narrow-front_0_0', ramen_narrow, (2, 4), 'Ramen alley', dict(
        door=[[1, 3]], solid=rows(2, 1, 3),
        glow=[([1, 3], [88, 200], '#f6dc8c', 'the door'), ([0, 3], [36, 192], '#f6dc8c', 'the shop window'),
              ([1, 1], [76, 88], '#f6dc8c', 'the upstairs window'), ([0, 2], [60, 182], '#d16b56', 'the red lantern')]),
     'A narrow two-storey ramen shop: mustard render, a blue tin shed roof and pent roof under snow, an '
     'upright yellow sign with ramen in red kana, a lit upstairs window and a heating unit, a bowl in the '
     'shop window, a white noren with red marks, a stovepipe out of the wall and up past the roof.'),
    ('ramen-miso-front_0_0', ramen_miso, (3, 4), 'Ramen alley', dict(
        door=[[1, 3]], solid=rows(3, 1, 3),
        glow=[([1, 3], [94, 190], '#f6dc8c', 'the door'), ([0, 2], [42, 180], '#f6dc8c', 'the latticed window'),
              ([1, 1], [94, 68], '#f6dc8c', 'the round gable window'), ([1, 2], [132, 168], '#d16b56', 'the red lantern')]),
     'A third ramen shop, a miso one, gable to the street so its roofline differs from the other two: a brown '
     'tin roof thick with snow, a plastered half-timbered gable with a round lit window, a stovepipe with '
     'steam, an indigo board (a bowl, miso ramen in kana, miso in yellow), a latticed window, an indigo noren, '
     'a red paper lantern, a yellow miso nobori.'),
    ('asahikawa-ramen-lanterns_0_0', ramen_lanterns, (1, 2), 'Ramen alley', dict(
        solid=[[0, 1]], glow=[([0, 0], [40, 32], '#fff4d6', 'top paper lantern (DayNight halo: the key has -lanterns)'),
                              ([0, 0], [40, 62], '#fff4d6', 'middle paper lantern'),
                              ([0, 1], [40, 92], '#fff4d6', 'bottom paper lantern')]),
     'The alley\'s own light: a timber post with a bracket arm and three round white paper lanterns hung down '
     'it reading ra-me-n in red, the same lanterns as the gate\'s (Sapporo\'s are red and white boxes). Its '
     'key matches DayNight\'s /-lanterns/ rule, so it gets a halo at night on the cell it is placed on.'),
    ('asahikawa-ramen-gate_0_0', ramen_gate, (3, 3), 'Ramen alley', dict(
        solid=[[0, 2], [2, 2]], walk=[[1, 2]],
        glow=[([0, 1], [42, 84], '#fff4d6', 'paper lantern'), ([1, 1], [78, 84], '#fff4d6', 'paper lantern'),
              ([1, 1], [114, 84], '#fff4d6', 'paper lantern'), ([2, 1], [150, 84], '#fff4d6', 'paper lantern')]),
     'The alley gate: two timber posts with knee braces, a beam with a shingled cap under snow, a plank '
     'reading YOKOCHO (alley), and four round white paper lanterns on a wire spelling ramen in red kana. '
     'Walk through the middle cell. Unlike Sapporo\'s red-posted, yellow-boarded ramen gate.'),
    ('ramen-crates_0_0', ramen_crates, (1, 2), 'Ramen alley', dict(
        solid=[[0, 1]]),
     'Seven beer crates stacked against a wall (yellow, red, blue), empties in the top one, snow on them.'),
    ('ramen-stockpot_0_0', ramen_stockpot, (1, 2), 'Ramen alley', dict(
        solid=[[0, 1]], glow=[([0, 1], [26, 94], '#6fb6ff', 'the gas flame (small)')]),
     'A big aluminium stock pot of broth on an iron gas ring outside a shop, a ladle left in it, a gas bottle '
     'beside it, a tall plume of steam.'),
    ('asahibashi-deck_0_0', asahibashi_deck, (2, BRIDGE_ROWS), 'Asahibashi and the riverbank', dict(
        walk=rows(2, 0, BRIDGE_ROWS - 1), layer='flat'),
     'Asahibashi\'s deck seen from above: a plain grey road (its own surface, not Heiwa-dori\'s setts) between '
     'green riveted parapets with snow-capped posts, a pale kerb line each side with snow blown up behind it, a '
     'worn centre line, a stone threshold at each bank. 2x5, flat, walked ON (Non-Collidables + depthBias '
     '-200, the asahikawa-bridge_0_0 recipe): rows 1-3 lie over the three river rows, rows 0 and 4 on the '
     'banks. All ten cells are walkable. For another river width change BRIDGE_ROWS in the tool and re-run; '
     'the kit redraws to any length.'),
    ('asahibashi-arch-w_0_0', lambda: asahibashi_arch('w'), (1, BRIDGE_ROWS), 'Asahibashi and the riverbank', dict(
        solid=rows(1, 0, BRIDGE_ROWS - 1),
        glow=[([0, 0], [50, PIER_LAMP_Y[0]], '#f6dc8c', 'pier lamp'),
              ([0, BRIDGE_ROWS - 1], [50, PIER_LAMP_Y[1]], '#f6dc8c', 'pier lamp')]),
     'The west rib of the green steel arch: a deep riveted truss (two chords with a zigzag lattice web between '
     'them, readable at 1x) springing from a stone pier with a lamp on each bank, thin hangers down to '
     'the deck\'s edge, snow on its back. Stands in the column WEST of the deck, rows as the deck, so the arch '
     'spans the river. Drawn leaning away from the deck, as a tall thing looks from above, so it '
     'never covers a deck cell. Its cells are solid (three are river ice anyway).'),
    ('asahibashi-arch-e_0_0', lambda: asahibashi_arch('e'), (1, BRIDGE_ROWS), 'Asahibashi and the riverbank', dict(
        solid=rows(1, 0, BRIDGE_ROWS - 1),
        glow=[([0, 0], [14, PIER_LAMP_Y[0]], '#f6dc8c', 'pier lamp'),
              ([0, BRIDGE_ROWS - 1], [14, PIER_LAMP_Y[1]], '#f6dc8c', 'pier lamp')]),
     'The east rib, for the column EAST of the deck: the same truss drawn for its own side and lit from the '
     'west like everything else (its bright chord is the one facing the deck), not a mirror of the west rib.'),
    ('asahibashi-brace_0_0', asahibashi_brace, (4, 1), 'Asahibashi and the riverbank', dict(
        walk=[[1, 0], [2, 0]], layer='above'),
     'Optional: the overhead lattice brace that joins the two crowns over the deck. One row, four cells, '
     'starting in the west rib\'s column, in the bridge\'s MIDDLE row (deck row 2); it must draw above the '
     'player (a Tops-type layer), who walks under it. Leave it out and the bridge still reads.'),
    ('hokkaido-house-red_0_0', house_red, (3, 4), 'Asahibashi and the riverbank', dict(
        door=[[1, 3]], solid=rows(3, 1, 3),
        glow=[([0, 2], [38, 170], '#f6dc8c', 'the lit window'), ([1, 3], [94, 190], '#f6dc8c', 'the porch'),
              ([1, 1], [92, 100], '#f6dc8c', 'the dormer')]),
     'A Hokkaido house, eaves to the street: a steep red standing-seam roof with the snow slid off its lower '
     'half onto a heap below (a shovel in it), a snow guard, a lit dormer, a block chimney with smoke, cream '
     'siding, a glazed wind porch with its own bit of roof, the heating-oil tank by the wall, icicles.'),
    ('hokkaido-house-blue_0_0', house_blue, (3, 4), 'Asahibashi and the riverbank', dict(
        door=[[1, 3]], solid=rows(3, 1, 3),
        glow=[([2, 2], [142, 168], '#f6dc8c', 'the lit window'), ([1, 1], [92, 86], '#f6dc8c', 'the attic window'),
              ([1, 2], [120, 170], '#f6dc8c', 'the porch light')]),
     'The other Hokkaido house, a "triangle roof": a steep blue gable to the street with thick snow on both '
     'slopes, the gable boarded dark with a lit attic window, pale siding, a blue door under a small canopy '
     'with a porch light, firewood stacked under the window, a stainless stovepipe up the wall, smoke.'),
    ('snow-fence-h_0_0', snow_fence, (1, 2), 'Asahibashi and the riverbank', dict(
        solid=[[0, 1]]),
     'A highway snow fence, one cell wide and two tall (taller than the player): galvanised steel posts '
     'carrying five angled louvre slats, a back stay, a gap under the slats and the drift it drops on its lee '
     'side. Tiles east-west with itself (slats and drift join). For the riverbank road and the town edge.'),
    ('ice-crack-a_0_0', lambda: ice_crack('a'), (1, 1), 'Asahibashi and the riverbank', dict(layer='overlay'),
     'Frozen-river detail: a transparent overlay for an ice cell (ice-pond-autotile_center): a branching '
     'white fracture with a blue shadow, a patch of wind-scoured snow. Not solid by itself.'),
    ('ice-crack-b_0_0', lambda: ice_crack('b'), (1, 1), 'Asahibashi and the riverbank', dict(layer='overlay'),
     'A second crack, running the other way.'),
    ('ice-fishing-hole_0_0', ice_fishing_hole, (1, 1), 'Asahibashi and the riverbank', dict(layer='overlay'),
     'Frozen-river detail: a smelt-fishing hole cut in the ice (dark water, a chipped white rim), a short '
     'rod on a rest, a folding stool, a bucket. Transparent overlay for an ice cell.'),
    ('ice-fishing-tent_0_0', fishing_tent, (2, 2), 'Asahibashi and the riverbank', dict(
        solid=rows(2, 1, 1), glow=[([0, 1], [56, 106], '#f6dc8c', 'the lamp inside the door (small)')]),
     'An ice-fishing tent standing on the frozen river: an orange dome with a dark door and a lamp inside, '
     'its flap tied back, snow on its crown, a red sled and a bucket beside it. Reads at 1x where the hole '
     'alone does not; stand the hole beside it.'),
    ('zoo-gate_0_0', zoo_gate, (5, 4), 'Asahiyama Zoo gate', dict(
        solid=[[0, 3], [4, 3]], walk=[[1, 3], [2, 3], [3, 3]]),
     'The zoo gate: two timber pylons on stone feet with animal posters (a seal, a crane), a cream polar bear on '
     'one and two king penguins on the other, a sky-blue board reading ASAHI ZOO (a look-alike name, not the '
     'zoo\'s own) with a penguin badge, snow on top, bunting under it. Walk through the three middle cells.'),
    ('zoo-fence-h_0_0', lambda: zoo_fence('h'), (1, 2), 'Asahiyama Zoo gate', dict(
        solid=[[0, 1]]),
     'The zoo\'s boundary, one cell wide and two tall: a timber post at its west end, green rails top and '
     'bottom, green wire mesh you see the snow through (part-transparent), snow on '
     'the rail and against its foot. Tiles east-west; run it out from both gate pylons.'),
    ('zoo-fence-end_0_0', lambda: zoo_fence('end'), (1, 2), 'Asahiyama Zoo gate', dict(
        solid=[[0, 1]]),
     'The lone timber post that closes a run of zoo-fence-h at its EAST end (each fence cell carries only '
     'its west post). Put it in the cell after the last fence cell, or let a pylon or building end the run.'),
    ('zoo-ticket-booth_0_0', ticket_booth, (2, 3), 'Asahiyama Zoo gate', dict(
        solid=rows(2, 1, 2), glow=[([0, 2], [62, 130], '#f6dc8c', 'the ticket window')]),
     'A ticket kiosk: a green hipped tin roof under snow, cream boards, a yellow TICKET board, a red and '
     'white awning, a lit window with the clerk and a price card, a timber counter. No door: bump it from '
     'the south.'),
    ('penguin-walk-a_0_0', lambda: penguin_walk('a'), (2, 1), 'Asahiyama Zoo gate', dict(
        solid=rows(2, 0, 0)),
     'The penguin walk: four king penguins in a line walking west, alternate feet forward, flippers '
     'swinging, blue shadows on the snow. Tiles with -b for a longer line.'),
    ('penguin-walk-b_0_0', lambda: penguin_walk('b'), (2, 1), 'Asahiyama Zoo gate', dict(
        solid=rows(2, 0, 0)),
     'The rest of the line: two adults with two brown downy chicks between them.'),
    ('zoo-seal-statue_0_0', seal_statue, (2, 2), 'Asahiyama Zoo gate', dict(
        solid=rows(2, 1, 1)),
     'A statue of a spotted seal rearing nose-up on a boulder, pale belly, dark spots, whiskers, snow along '
     'its back, a brass plaque. (A seal, not a bear: Sapporo already has a snow bear.)'),
]
FAMILIES = [
    ('heiwa-paving-autotile', heiwa_paving, False, 'Station front and Heiwa-dori',
     "Heiwa-dori's pedestrian paving: warm grey granite setts in running bond, five quiet greys with one in "
     'eight a faded rose (scattered, no diagonal), soft joints, snow in a few of them. Opaque ground tile; on '
     "an edge or corner role the snow field lies over it with a wavy lip (the snow tile's own texture outside "
     'the edge), so it sits straight on snow-autotile.'),
    ('ramen-alley-autotile', alley_ground, False, 'Ramen alley',
     "The ramen alley's floor, in place of the brown dirt path every town has: dark wet asphalt with trodden "
     'slush lying in soft patches and meltwater pooling. Opaque ground tile with the same snow-lipped edge '
     'and corner roles as the paving; sits straight on snow-autotile.'),
]
SPRITES = {key: (fn, True) for key, fn, *_ in PIECES}      # key: (builder, pixel-double?)
for _fam, _fn, _double, *_ in FAMILIES:
    for _r in ROLES:
        SPRITES[f'{_fam}_{_r}'] = ((lambda r=_r, fn=_fn: fn(r)), _double)

DISTRICTS = ('station', 'ramen', 'bridge', 'zoo')
FLAT = {key for key, _fn, _size, _district, m, _desc in PIECES if m.get('layer') == 'flat'}   # walked ON


def glow_spots():
    """{key: [{x, y, r, color, a}]} in cells from the sprite's top-left, from each
    piece's `glow` (which is in file pixels and has no size): a window or a door
    is a soft warm spot, a lantern or a flame a smaller one. art_register drops
    the two keys DayNight lights itself (heiwa-lamp-post, asahikawa-ramen-lanterns)."""
    out = {}
    for key, _fn, _size, _district, m, _desc in PIECES:
        spots = [{'x': px / 64, 'y': py / 64, 'color': colour, 'a': 0.5,
                  'r': 0.6 if ('lantern' in what or 'small' in what or 'lamp' in what) else 0.9}
                 for _cell, (px, py), colour, what in m.get('glow', [])]
        if spots:
            out[key] = spots
    return out


def build():
    built = {}
    for key, (fn, double) in SPRITES.items():
        im = fn()
        if double:
            im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        built[key] = im
    return built


def manifest(built, out):
    """What the rebuild needs to place these, as JSON."""
    sprites = []
    for key, _fn, (w, h), district, m, desc in PIECES:
        im = built[key]
        assert im.size == (w * 64, h * 64), key
        doors = m.get('door') or []
        solid = m.get('solid', [])
        assert all(dc in solid for dc in doors), key
        for _cell, (gx, gy), _c, _what in m.get('glow', []):
            assert 0 <= gx < im.width and 0 <= gy < im.height, (key, gx, gy)
        sprites.append({
            'key': key, 'file': f'gamev2/{SPR}/{key}.png', 'size': [w, h], 'px': list(im.size),
            'anchor': [round(32 / im.width, 6), round(32 / im.height, 6)],
            'door': doors[0] if doors else None, 'doors': doors,
            'solid': solid, 'walk_through': m.get('walk', []),
            'night_glow': [{'cell': [gx // 64, gy // 64], 'px': [gx, gy], 'colour': colour, 'what': what}
                           for _cell, (gx, gy), colour, what in m.get('glow', [])],
            'layer': m.get('layer', 'standing'),
            'district': district, 'description': desc,
        })
    doc = {
        'tool': 'gamev2/tools/generate_asahikawa_art.py',
        'run': 'cd gamev2 && python3 tools/generate_asahikawa_art.py [--sheet out.png] [--scenes dir] [--manifest out.json]'
               '   (any python3 that has Pillow)',
        'notes': [
            "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per "
            "cell and pixel-doubled, as generate_hokkaido.py / generate_sapporo_art.py do); 'size' is in cells.",
            'main() registers every sprite in config.json (tools/art_register.py): spriteMetadata '
            '{frameCount:1, anchorX: 32/widthPx, anchorY: 32/heightPx} '
            "(centre of the top-left cell; that is 'anchor'), 1x1 tiles 0.5/0.5, the glow list of a lit piece.",
            "'door' / 'doors', 'solid' and 'walk_through' are [col,row] from the sprite's top-left cell. 'solid' is "
            'the suggested footprint (rows above it are roof, snow or steam the player walks behind). A gate lists '
            "the cells you walk through under it in 'walk_through'; the deck lists the cells you walk ON.",
            "layer: 'standing' = Y-sorted on a Collidables-type layer; 'flat' = under the player (asahibashi-deck: "
            "Non-Collidables + depthBias -200, exactly the asahikawa-bridge_0_0 recipe in generate_hokkaido.FLAT and "
            "make_prefabs); 'overlay' = flat over a floor tile; 'above' = over the player (asahibashi-brace).",
            'The bridge is 5 cells long over the three rows of river (rows 17-19; the deck is at (20,16)-(21,20), '
            'where asahikawa-bridge_0_0 was). asahibashi-deck_0_0 (2x5) has its end rows on the banks; '
            'asahibashi-arch-w_0_0 goes in the '
            'column west of the deck and -arch-e east, same five rows. The ribs lean away from the deck, so no '
            'deck cell is covered and the player is never behind them; their cells are solid. '
            'asahibashi-brace_0_0 is optional (deck row 2). For another river width change BRIDGE_ROWS in the '
            'tool and re-run.',
            "night_glow lists each sprite's lit parts: the cell, the pixel in the file (from the sprite's top-left) "
            'and a colour. The game has no lit-window layer today: DayNight.buildGlows only puts a halo on cells '
            'whose tile key matches /lamp-post|-lanterns/, at the tile\'s own cell. Two keys here match and so '
            'glow: heiwa-lamp-post_0_0 (Heiwa-dori) and asahikawa-ramen-lanterns_0_0 (the alley); stand them by '
            'the fronts and the gate. The other spots are for a glow list if one is added.',
            'snow-fence-h, zoo-fence-h, zoo-fence-end, heiwa-lamp-post, asahikawa-ramen-lanterns are 1x2: the '
            'tile cell is the top one, the solid cell the one below (as lantern-post / ramen-alley-lanterns).',
            'Names are look-alikes or generic words: ASAHIKAWA and its kanji (the town), SAKAGURA (sake cellar), '
            'KAGU CRAFT (furniture), BOOKS, pan in kana (bread), ramen and miso in kana, YOKOCHO (alley), TICKET, ASAHI ZOO (not '
            "the zoo's own name or mark). No real brand artwork.",
            'Steam and smoke are soft, unoutlined, part-transparent puffs inside the sprite (stovepipes, the stock '
            'pot, the counter window, chimneys); they do not animate.',
        ],
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, _fn, _double, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/asahikawa_art_sheet.png',
            'scenes': [f'.agent-queue/shots/asahikawa_art_{n}.png' for n in DISTRICTS],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


# ---- previews (not part of the game) --------------------------------------------
GRID = ('corner-nw', 'edge-n', 'corner-ne', 'edge-w', 'center', 'edge-e', 'corner-sw', 'edge-s', 'corner-se')
SMALL = ('ice-crack-a_0_0', 'ice-crack-b_0_0', 'ice-fishing-hole_0_0', 'asahibashi-brace_0_0',
         'asahibashi-arch-w_0_0', 'asahibashi-arch-e_0_0', 'asahibashi-deck_0_0',
         'snow-fence-h_0_0', 'zoo-fence-h_0_0', 'zoo-fence-end_0_0')


def bridge_patch(built, w=8):
    """The bridge put together over its rows of river ice, with the ice details."""
    n = BRIDGE_ROWS
    snow, ice = spr('snow-autotile_center'), spr('ice-pond-autotile_center')
    im = Image.new('RGBA', (w * 64, n * 64), CLEAR)
    for y in range(n):
        for x in range(w):
            im.alpha_composite(snow, (x * 64, y * 64))
            if 1 <= y <= n - 2:
                im.alpha_composite(ice, (x * 64, y * 64))
                edge = {1: 'ice-pond-autotile_edge-n', n - 2: 'ice-pond-autotile_edge-s'}.get(y)
                if edge:
                    im.alpha_composite(spr(edge), (x * 64, y * 64))
    for name, x, y in (('ice-crack-a_0_0', 0, 2), ('ice-fishing-hole_0_0', 1, n - 2), ('ice-crack-b_0_0', 6, 2),
                       ('ice-crack-a_0_0', 7, n - 2), ('ice-crack-b_0_0', 1, 1), ('ice-crack-a_0_0', 6, 1)):
        im.alpha_composite(built[name], (x * 64, y * 64))
    im.alpha_composite(built['ice-fishing-tent_0_0'], (0, 64))
    im.alpha_composite(built['asahibashi-deck_0_0'], (3 * 64, 0))
    im.alpha_composite(built['asahibashi-arch-w_0_0'], (2 * 64, 0))
    im.alpha_composite(built['asahibashi-arch-e_0_0'], (5 * 64, 0))
    im.alpha_composite(spr('james_front_frame_0'), (3 * 64, (n - 1) * 64))
    im.alpha_composite(built['asahibashi-brace_0_0'], (2 * 64, (n // 2) * 64))
    return im


def sheet(built, out):
    """Everything on one snow-coloured sheet, at 4x the drawn size (2x the file)."""
    keys = [k for k, *_ in PIECES if k not in SMALL]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1500 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + BRIDGE_ROWS * 64 + 60
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
    im.alpha_composite(bridge_patch(built), (x, y))
    x += 8 * 64 + 24
    for k in ('asahibashi-arch-w_0_0', 'asahibashi-deck_0_0', 'asahibashi-arch-e_0_0'):   # the pieces apart
        im.alpha_composite(built[k], (x, y)); x += built[k].width + 12
    im.alpha_composite(built['asahibashi-brace_0_0'], (x, y))
    snow = spr('snow-autotile_center')
    for j, fam in enumerate(f[0] for f in FAMILIES):              # each ground family as a 3x3 patch
        for i, r in enumerate(GRID):
            im.alpha_composite(built[f'{fam}_{r}'], (x + (i % 3) * 64, y + 56 + j * 200 + (i // 3) * 64))
    x += 3 * 64 + 24
    ice = spr('ice-pond-autotile_center')
    for i, k in enumerate(('ice-crack-a_0_0', 'ice-crack-b_0_0', 'ice-fishing-hole_0_0')):
        im.alpha_composite(ice, (x, y + 56 + i * 64)); im.alpha_composite(built[k], (x, y + 56 + i * 64))
    me = spr('james_front_frame_0')
    for j, run in enumerate((['snow-fence-h_0_0'] * 3, ['zoo-fence-h_0_0'] * 3 + ['zoo-fence-end_0_0'])):
        for i, k in enumerate(run):                               # the fences in a run, on snow, the player for height
            for dy in (0, 64):
                im.alpha_composite(snow, (x + 88 + i * 64, y + 56 + j * 160 + dy))
        im.alpha_composite(snow, (x + 88 + len(run) * 64, y + 56 + j * 160 + 64))
        for i, k in enumerate(run):
            im.alpha_composite(built[k], (x + 88 + i * 64, y + 56 + j * 160))
        im.alpha_composite(me, (x + 88 + len(run) * 64, y + 56 + j * 160 + 64))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


class Town(Scene):
    def flat(self, name, x, y):
        """A flat sprite straight onto the ground (under everything standing)."""
        self.im.alpha_composite(self.get(name), (x * 64, y * 64))

    def river(self, y, x0, x1, n=BRIDGE_ROWS - 2):
        for x in range(x0, x1 + 1):
            for j in range(n):
                self.tile('ice-pond-autotile_center', x, y + j)
                edge = 'edge-n' if j == 0 else ('edge-s' if j == n - 1 else None)
                if edge:
                    self.tile(f'ice-pond-autotile_{edge}', x, y + j)

    def tree(self, x, base):
        self.put('tree-3-top-snow_0_0', x, base - 1)
        self.things.append((base, x, 'tree-3-base-shadow-snow_0_0'))


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    # Station front and Heiwa-dori: the station, the forecourt, the shops down the pedestrian street
    s = Town(built, 26, 15)
    s.floor('heiwa-paving-autotile', (1, 7, 24, 8), (11, 9, 15, 14))
    s.put('asahikawa-station-front_0_0', 1, 6)
    s.put('heiwa-shop-sake_0_0', 12, 6); s.put('heiwa-shop-bakery_0_0', 15, 6); s.put('heiwa-shop-woodcraft_0_0', 19, 6)
    s.put('heiwa-shop-books_0_0', 7, 13); s.put('heiwa-shop-woodcraft_0_0', 17, 13)
    s.put('ice-sculpture-crane_0_0', 12, 11); s.put('ice-sculpture-owl_0_0', 14, 13)
    s.put('heiwa-bench_0_0', 12, 13); s.put('heiwa-bench_0_0', 22, 7)
    for x, y in ((11, 10), (15, 10), (11, 14), (15, 14), (23, 7)):
        s.put('heiwa-lamp-post_0_0', x, y)
    s.tree(1, 11); s.tree(24, 11); s.tree(4, 12)
    s.put(me, 5, 7); s.put(me, 6, 7); s.put(me, 13, 8); s.put(me, 14, 11); s.put(me, 16, 7); s.put(me, 20, 8); s.put(me, 13, 14)
    s.put(me, 9, 14)
    s.save(f'{outdir}/asahikawa_art_station.png')
    # Ramen alley: three different fronts, the gate over a side lane, lanterns, crates and a stock pot
    s = Town(built, 18, 11)
    s.floor('ramen-alley-autotile', (0, 6, 17, 7), (10, 2, 10, 5))
    s.put('ramen-shoyu-front_0_0', 1, 5); s.put('ramen-crates_0_0', 5, 5); s.put('ramen-narrow-front_0_0', 6, 5)
    s.put('ramen-stockpot_0_0', 8, 5)
    s.put('asahikawa-ramen-gate_0_0', 9, 5); s.put('asahikawa-ramen-lanterns_0_0', 12, 5)
    s.put('ramen-miso-front_0_0', 13, 5); s.put('ramen-crates_0_0', 16, 5); s.put('asahikawa-ramen-lanterns_0_0', 17, 5)
    s.put('asahikawa-ramen-lanterns_0_0', 0, 5)
    s.put('ramen-narrow-front_0_0', 2, 10); s.put('ramen-stockpot_0_0', 4, 10); s.put('ramen-crates_0_0', 9, 10)
    s.put('ramen-banner_0_0', 5, 10); s.put('ramen-miso-front_0_0', 12, 10); s.put('asahikawa-ramen-lanterns_0_0', 15, 10)
    s.put(me, 3, 6); s.put(me, 7, 6); s.put(me, 10, 5); s.put(me, 10, 7); s.put(me, 14, 6); s.put(me, 11, 9)
    s.save(f'{outdir}/asahikawa_art_ramen.png')
    # Asahibashi and the riverbank: the bridge over five river rows, houses and the snow fence on the banks
    s = Town(built, 20, 16)
    s.river(6, 0, 19)
    s.floor('snow-path-autotile', (9, 0, 10, 4), (9, 12, 10, 15))
    for name, x, y in (('ice-crack-a_0_0', 2, 7), ('ice-fishing-hole_0_0', 5, 9), ('ice-crack-b_0_0', 6, 6),
                       ('ice-crack-b_0_0', 14, 7), ('ice-crack-a_0_0', 17, 9), ('ice-crack-a_0_0', 13, 9),
                       ('ice-crack-b_0_0', 1, 10), ('ice-fishing-hole_0_0', 16, 8)):
        s.tile(name, x, y)
    s.flat('asahibashi-deck_0_0', 9, 5)
    s.put('asahibashi-arch-w_0_0', 8, 11); s.put('asahibashi-arch-e_0_0', 11, 11)
    s.put('ice-fishing-tent_0_0', 3, 9); s.put('ice-fishing-tent_0_0', 14, 8)
    s.put('hokkaido-house-red_0_0', 1, 4); s.put('hokkaido-house-blue_0_0', 5, 4)
    s.put('hokkaido-house-blue_0_0', 13, 4); s.put('hokkaido-house-red_0_0', 16, 4)
    s.put('hokkaido-house-red_0_0', 3, 15); s.put('hokkaido-house-blue_0_0', 15, 15)
    for x in list(range(0, 7)) + list(range(13, 20)):
        s.put('snow-fence-h_0_0', x, 12)
    s.tree(12, 3); s.tree(7, 15)
    s.put('shrub-small-circle-snow_0_0', 12, 5); s.put('shrub-small-circle-snow_0_0', 4, 5)
    s.put(me, 9, 8); s.put(me, 10, 4); s.put(me, 10, 13); s.put(me, 2, 5); s.put(me, 17, 5); s.put(me, 13, 13)
    s.put(me, 5, 12)
    s.save(f'{outdir}/asahikawa_art_bridge.png', top=[('asahibashi-brace_0_0', 8, 8)])
    # Asahiyama Zoo gate: the gate in its fence, the booth, the penguin walk, the seal
    s = Town(built, 16, 10)
    s.floor('snow-path-autotile', (6, 2, 8, 9), (0, 7, 15, 8))
    s.put('zoo-gate_0_0', 5, 5); s.put('zoo-ticket-booth_0_0', 2, 6); s.put('zoo-seal-statue_0_0', 11, 6)
    s.put('penguin-walk-a_0_0', 9, 7); s.put('penguin-walk-b_0_0', 11, 7); s.put('penguin-walk-a_0_0', 13, 7)
    for x in (0, 1, 2, 3, 4, 10, 11, 12, 13, 14):
        s.put('zoo-fence-h_0_0', x, 5)
    s.put('zoo-fence-end_0_0', 15, 5)
    s.tree(0, 3); s.tree(13, 3); s.tree(3, 3)
    s.put(me, 7, 5); s.put(me, 4, 7); s.put(me, 8, 8); s.put(me, 13, 6); s.put(me, 5, 8); s.put(me, 1, 6)
    s.save(f'{outdir}/asahikawa_art_zoo.png')


def _save(self, out, top=()):
    for base, x, name in sorted(self.things):
        im = self.get(name)
        self.im.alpha_composite(im, (x * 64, (base + 1) * 64 - im.height))
    for name, x, y in top:
        self.im.alpha_composite(self.get(name), (x * 64, y * 64))
    self.im.save(out)
    print('scene ->', out, self.im.size)


Town.save = _save


def main():
    built = build()
    for key, im in built.items():
        im.save(f'{SPR}/{key}.png')
        if 'autotile' not in key:
            print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    print(', '.join(f[0] for f in FAMILIES) + f': {len(ROLES)} roles each')
    art_register.register(built, glow_spots(), FLAT)
    for flag, fn in (('--sheet', sheet), ('--scenes', scenes), ('--manifest', manifest)):
        if flag in sys.argv:
            fn(built, sys.argv[sys.argv.index(flag) + 1])


if __name__ == '__main__':
    main()
