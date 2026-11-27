#!/usr/bin/env python3
"""generate_osaka_art.py — draw Osaka's own buildings and street pieces (issue #219).

Osaka had three sprites of its own (the Dotonbori arch and wheel, and a
line-art Tsutenkaku) and filled the rest with the shared high-rises and
townhouses, the same kit on two greys either side of the canal. These are the
pieces its three areas are rebuilt from, drawn the way generate_sapporo_art.py
draws Sapporo's: shaded pixel art in the GuttyKreum palette, at half size (one
drawn pixel = one pixel of a 32px tile) and pixel-doubled, lit from the left,
with a 1px ink outline. Osaka is loud, warm and edible, and it is mid November:
no snow. Every name and mascot on a sign is invented; there is no real brand
artwork (no running man, no crab logo, no drummer doll, no lucky imp, no
scowling chef).

Station front (a threshold)
  osaka-station-front_0_0      10x6  Osaka Station as its roof: one sloping
                                     plane of glass wider than the building,
                                     on steel trees; the deck, a gold clock, a
                                     train; four shop bays and the doors
  osaka-wheel-mall_0_0          5x7  a red-tiled mall, a red wheel in its roof
Dotonbori (the canal)
  osaka-crab-restaurant_0_0     4x5  a seafood restaurant under a giant
                                     mechanical crab (riveted, steel joints)
  osaka-takoyaki-stand_0_0      4x4  a takoyaki stand under a giant octopus in
                                     a headband; a steaming griddle, a queue rope
  osaka-gyoza-izakaya_0_0       4x5  an izakaya, a giant plate of gyoza on its roof
  osaka-sprinter-billboard_0_0  6x6  the great neon board on a gantry over a
                                     diner: an invented hurdler, DASH!
  osaka-dragon-ramen_0_0        4x5  a ramen shop; a blue dragon has come
                                     through the sign, tail out of the roof
  osaka-okonomiyaki-front_0_0   3x4  charred boards and copper under a giant
                                     pancake on an iron plate and two turners
  osaka-sign-tower-a_0_0        3x7  a tenant building: a lit floor per bar,
  osaka-sign-tower-b_0_0        4x6  blade signs down both edges, a roof sign
  osaka-boat-pier_0_0           3x3  the river cruise's booth and gangway gate
  osaka-boat-landing_0_0        3x2  (ground) the gangway and a floating stage
  osaka-river-boat_0_0          4x2  the sightseeing boat, moored
  osaka-neon-lanterns_0_0       1x3  a pole of small neon signs; the key holds
                                     `-lanterns`, so DayNight gives it a halo
  osaka-canal-rail_0_0          1x1  the canal's low railing, a span, and
  osaka-canal-rail-post_0_0     1x1  its lamp post; a string of bulbs on both
  osaka-quay-wall_0_0           1x1  (ground) the stone embankment for the
  osaka-quay-wall-drain_0_0     1x1  first water row; one with an outfall
  osaka-queue-rope_0_0          1x1  brass posts and a red rope, tiling
  osaka-menu-board_0_0          1x1  an A-frame menu board
  osaka-boardwalk-autotile_*         the canal promenade: dark ironwood planks
                                     running east-west, a steel edge with studs
Shinsekai
  osaka-tsutenkaku_0_0         8x13  Tsutenkaku in shaded steel, open lattice
                                     you see through, on the placeholder's
                                     exact silhouette and cells
  osaka-oni-kushikatsu_0_0      4x5  a kushikatsu shop under a huge scowling
                                     oni: tiger skin, iron club, one skewer
  osaka-retro-arcade_0_0        4x5  a retro game arcade: GAME in bulbs, lit
                                     cabinets, a giant joystick on the roof
  osaka-shooting-gallery_0_0    3x4  a cork-gun gallery: a giant target and rifle
  osaka-shogi-parlour_0_0       3x4  a shogi parlour under a giant shogi piece
  osaka-tachinomi_0_0           3x4  a standing bar in tin and timber
  osaka-shinsekai-arch_0_0      5x4  the street's arch: SHINSEKAI letter by
                                     letter in discs, lanterns; walk through
  osaka-lucky-idol_0_0          2x3  an invented lucky idol: a round gold owl
                                     painted like a daruma, on a plinth
  osaka-fugu-lantern_0_0        2x3  a giant paper pufferfish hung from a post
  osaka-fugu-sign_0_0           2x2  the same fish on a wall bracket
  osaka-gacha-row_0_0           2x2  eight capsule machines, two high
  osaka-gacha-single_0_0        1x2  two capsule machines, one on the other
  osaka-shinsekai-lanterns_0_0  1x2  a post of white paper lanterns (halo)
  osaka-beer-crates_0_0         1x1  stacked bottle crates
  osaka-retro-paving-autotile_*      retro tiled paving: cream and rose
                                     checker, teal insets, a dark red border

This tool writes the PNGs into assets/sprites/ and NOTHING else: no
config.json, no prefabs. tsutenkaku_0_0 (the placeholder) is not touched.

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs a python3 with Pillow (plain python3 on this machine has none; use
/Library/Developer/CommandLineTools/usr/bin/python3) and its three sibling
tools, which it imports: generate_hokkaido, generate_sapporo_art,
generate_kanazawa_art. Drawing the sprites needs nothing else; --sheet and
--scenes also READ existing sprites from assets/sprites/ (ground tiles, water,
the player, a few buildings), so they only work inside the repo. Run from gamev2/:
    python3 tools/generate_osaka_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
"""
import json
import math
import os
import sys
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import (rgb, canvas, outline, CLEAR, INK, NAVY,                     # noqa: E402
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK,
                               WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               GOLD, AMBER)
from generate_sapporo_art import glyphs, glass_door, lantern, star                         # noqa: E402
from generate_kanazawa_art import FONT as _FONT, KANA as _KANA, h3, shade, night           # noqa: E402

SPR = 'assets/sprites'
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')

# ---- Osaka's colours --------------------------------------------------------------
WARM, LIT = rgb('f6dc8c'), rgb('f2c66a')
VERM, VERM_HI, VERM_LO, VERM_DK = rgb('d8452f'), rgb('f27a55'), rgb('a83224'), rgb('75241f')
YEL, YEL_HI, YEL_LO, YEL_DK = rgb('f6c636'), rgb('ffe680'), rgb('d39a26'), rgb('9c6a1e')
TEAL, TEAL_HI, TEAL_LO, TEAL_DK = rgb('2fa39a'), rgb('6fd6c4'), rgb('1f7773'), rgb('16504f')
PINK, PINK_HI, PINK_LO, PINK_DK = rgb('ee5d93'), rgb('fba5c4'), rgb('c13b74'), rgb('8a2957')
CYAN = rgb('66dcea')
LIME = rgb('8fe08a')
VIOLET, VIOLET_LO, VIOLET_DK = rgb('5b3f8f'), rgb('40296b'), rgb('2a1c4a')
NIGHT = rgb('1b2040')
DARK = rgb('2a2330')
TILE, TILE_HI, TILE_LO, TILE_DK = rgb('efe7d8'), rgb('fffaf0'), rgb('cfc3ad'), rgb('a2947f')     # white facade tile
TAN, TAN_HI, TAN_LO, TAN_DK = rgb('cfa57a'), rgb('e6c39c'), rgb('a97f58'), rgb('7a5a40')          # the station's stone
TERRA, TERRA_HI, TERRA_LO, TERRA_DK = rgb('b9684a'), rgb('d58866'), rgb('93503a'), rgb('6b3a2c')  # terracotta
STEEL, STEEL_HI, STEEL_LO, STEEL_DK = rgb('a9b4c2'), rgb('dfe7ee'), rgb('7a8598'), rgb('4d566b')
TIMBER, TIMBER_HI, TIMBER_LO, TIMBER_DK = rgb('6b4a3a'), rgb('8d6650'), rgb('4b342c'), rgb('2f2224')
KAWARA, KAWARA_HI, KAWARA_LO = rgb('4a4f63'), rgb('6f7690'), rgb('2f3346')
PAPER, PAPER_LO = rgb('f6efdc'), rgb('d6cbb0')
SKIN, SKIN_LO = rgb('f3cfa8'), rgb('cf9f78')
DOUGH, DOUGH_HI, DOUGH_LO, DOUGH_DK = rgb('f2e2bd'), rgb('fff6dc'), rgb('d6bb8a'), rgb('b0834a')
FRY, FRY_HI, FRY_LO = rgb('d9952f'), rgb('f3c45c'), rgb('a3641f')                                  # golden crumb
INDIGO, INDIGO_HI, INDIGO_LO = rgb('2f3f7a'), rgb('4d63ad'), rgb('1e2850')
DRAG, DRAG_HI, DRAG_LO, DRAG_DK = rgb('3b7fd0'), rgb('7fc0f5'), rgb('285a9e'), rgb('1b3a70')     # the dragon's blue

P_RED = (VERM_HI, VERM, VERM_LO, VERM_DK)
P_PINK = (PINK_HI, PINK, PINK_LO, PINK_DK)
P_GOLD = (YEL_HI, YEL, YEL_LO, YEL_DK)
P_DOUGH = (DOUGH_HI, DOUGH, DOUGH_LO, DOUGH_DK)
P_STEEL = (STEEL_HI, STEEL, STEEL_LO, STEEL_DK)
P_DRAG = (DRAG_HI, DRAG, DRAG_LO, DRAG_DK)
P_WHITE = (WHITE, rgb('f1eee6'), rgb('cfc9c0'), rgb('a39c98'))
P_SKIN = (rgb('ffe6c8'), SKIN, SKIN_LO, rgb('a87858'))
P_FRY = (FRY_HI, FRY, FRY_LO, rgb('7a4a1c'))

# ---- lettering: the house 5x7 capitals, completed, and a few more kana ------------
FONT = dict(_FONT)
FONT.update({
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
    'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    '!': ['..#..', '..#..', '..#..', '..#..', '..#..', '.....', '..#..'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '-': ['.....', '.....', '.....', '.###.', '.....', '.....', '.....'],
})
KANA = dict(_KANA)
KANA.update({
    'shi': ['.#....#', '..#...#', '#.....#', '.#...#.', '.....#.', '....#..', '.###...'],
    'tsu': ['#.#...#', '#.#...#', '.#.#..#', '.....#.', '.....#.', '....#..', '.###...'],
    'fu':  ['#######', '......#', '......#', '.....#.', '.....#.', '....#..', '.###...'],
    'ne':  ['...#...', '#######', '.....#.', '....#..', '..###.#', '.#.#..#', '...#...'],
    'so':  ['#....#.', '#....#.', '.#...#.', '.....#.', '....#..', '...#...', '.##....'],
    'vbar': ['...#...'] * 7,
    # hand-set characters
    'kushi': ['...#...', '.#####.', '.#.#.#.', '.#####.', '#######', '#..#..#', '#######', '...#...'],   # 串 skewer
    'king':  ['#######', '...#...', '...#...', '.#####.', '...#...', '...#...', '#######'],              # 王
    'big':   ['...#...', '...#...', '#######', '...#...', '..#.#..', '.#...#.', '#.....#'],              # 大
    'sake':  ['#.#####', '.#.#.#.', '#.#####', '..#.#.#', '#.##.##', '#.#...#', '#.#####'],              # 酒, near enough
})


def text(d, s, x, y, fill, scale=1, vertical=False):
    glyphs(d, [FONT[c] for c in s], x, y, fill, scale, 1, vertical)


def kana(d, names, x, y, fill, scale=1, vertical=False):
    glyphs(d, [KANA['vbar' if (vertical and n == 'bar') else n] for n in names], x, y, fill, scale, 1, vertical)


def text_w(s, scale=1):
    return (len(s) * 6 - 1) * scale


def kana_w(n, scale=1):
    return (n * 8 - 1) * scale


def ctext(d, s, cx, y, fill, scale=1, shadow=None):
    x = cx - text_w(s, scale) // 2
    if shadow:
        text(d, s, x + scale, y + scale, shadow, scale)
    text(d, s, x, y, fill, scale)


def ckana(d, names, cx, y, fill, scale=1, shadow=None):
    x = cx - kana_w(len(names), scale) // 2
    if shadow:
        kana(d, names, x + scale, y + scale, shadow, scale)
    kana(d, names, x, y, fill, scale)


# ---- helpers ------------------------------------------------------------------------
def bar(d, x0, y0, x1, y1, base, hi=None, lo=None):
    """A lit block: a highlight down its west edge, shade down its east."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    if hi:
        d.line([(x0, y0), (x0, y1)], fill=hi)
    if lo:
        d.line([(x1, y0), (x1, y1)], fill=lo)


def ball(im, cx, cy, rx, ry, pal, a0=-999, a1=999):
    """A shaded ellipsoid, lit from the upper left: pal = (highlight, base,
    shade, deep shade). Only rows a0..a1 (relative to cy) are drawn."""
    px = im.load()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        if not (0 <= y < im.height) or not (a0 <= y - cy <= a1):
            continue
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not 0 <= x < im.width:
                continue
            nx, ny = (x - cx) / rx, (y - cy) / ry
            r2 = nx * nx + ny * ny
            if r2 > 1:
                continue
            t = nx * 0.55 + ny * 0.7
            if t > 0.66:
                c = pal[3]
            elif t > 0.28:
                c = pal[2]
            elif t < -0.42 and r2 < 0.78:
                c = pal[0]
            else:
                c = pal[1]
            px[x, y] = c


def tube(d, pts, w0, w1, pal):
    """A shaded limb along a polyline, tapering from width w0 to w1."""
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1
    samples, run = [], 0
    for i, L in enumerate(seg):
        n = max(1, int(L * 2))
        for k in range(n + (i == len(seg) - 1)):
            t = k / n
            samples.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                            pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t, (run + L * t) / total))
        run += L
    for off, shrink, c in ((0, 0, pal[2]), (-0.6, 1.2, pal[1]), (-1.2, 3.2, pal[0])):
        for x, y, t in samples:
            r = (w0 + (w1 - w0) * t) / 2 - shrink / 2
            if r < 0.45:
                continue
            d.ellipse([x + off - r, y + off - r, x + off + r, y + off + r], fill=c)


def bulbs(d, x0, y0, x1, y1, step=4, on=WARM, off=AMBER):
    """A rim of bulbs round a board."""
    k = 0
    for x in range(x0, x1 + 1, step):
        d.point((x, y0), fill=on if k % 2 == 0 else off); d.point((x, y1), fill=off if k % 2 == 0 else on); k += 1
    for y in range(y0 + step, y1, step):
        d.point((x0, y), fill=on if k % 2 == 0 else off); d.point((x1, y), fill=off if k % 2 == 0 else on); k += 1


def board(d, x0, y0, x1, y1, bg, rim=INK, lamp=True, hi=None):
    d.rectangle([x0, y0, x1, y1], fill=rim)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=bg)
    if hi:
        d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=hi)
    if lamp:
        bulbs(d, x0, y0, x1, y1)


def stripes(d, x0, y0, x1, y1, a, b, w=4, lo=None):
    """A striped awning, its lower edge scalloped."""
    for x in range(x0, x1 + 1):
        c = a if ((x - x0) // w) % 2 == 0 else b
        d.line([(x, y0), (x, y1 - (1 if (x - x0) % w in (0, w - 1) else 0))], fill=c)
    d.line([(x0, y0), (x1, y0)], fill=WHITE)
    if lo:
        d.line([(x0, y1 + 1), (x1, y1 + 1)], fill=lo)


def lit_window(d, x0, y0, x1, y1, frame=TIMBER_DK, goods=None, bars=0):
    """A lit shop window; `goods` = rows of coloured stock on shelves."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=WARM)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=WHITE)
    d.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=LIT)
    if goods:
        for j, sy in enumerate(range(y0 + 5, y1 - 1, 6)):
            d.line([(x0 + 1, sy), (x1 - 1, sy)], fill=CREAM_DK)
            for i, sx in enumerate(range(x0 + 2, x1 - 2, 3)):
                c = goods[(i + j * 2 + (x0 % 3)) % len(goods)]
                d.rectangle([sx, sy - 3, sx + 1, sy - 1], fill=c)
    if bars:
        for x in range(x0 + bars, x1, bars):
            d.line([(x, y0 + 1), (x, y1 - 1)], fill=frame)


def facade_tile(d, x0, y0, x1, y1, pal=(TILE, TILE_HI, TILE_LO, TILE_DK), tw=8, th=4):
    """A tiled front: faint joints, the east strip in shade."""
    base, hi, lo, dk = pal
    d.rectangle([x0, y0, x1, y1], fill=base)
    for y in range(y0 + th - 1, y1, th):
        d.line([(x0, y), (x1, y)], fill=lo)
    for j, y in enumerate(range(y0, y1, th)):
        for x in range(x0 + (j % 2) * (tw // 2), x1, tw):
            d.line([(x, y), (x, min(y + th - 2, y1))], fill=lo)
    d.line([(x0, y0), (x0, y1)], fill=hi)
    d.rectangle([x1 - 3, y0, x1, y1], fill=lo)
    d.line([(x1, y0), (x1, y1)], fill=dk)


def pent_roof(d, x0, y0, x1, h=7, pal=(KAWARA, KAWARA_HI, KAWARA_LO)):
    """A tiled pent roof over a shopfront: courses of round tiles, a lit lip."""
    base, hi, lo = pal
    for y in range(h):
        a, b = x0 - y // 2, x1 + y // 2
        d.line([(a, y0 + y), (b, y0 + y)], fill=base)
        for x in range(a + (y % 2) * 2, b, 4):
            d.point((x, y0 + y), fill=lo)
        d.point((a, y0 + y), fill=hi)
    d.line([(x0, y0), (x1, y0)], fill=hi)
    d.line([(x0 - h // 2, y0 + h), (x1 + h // 2, y0 + h)], fill=lo)


def steam(im, x, y, n=3, s=0):
    """Wisps of steam rising from (x, y)."""
    ov = Image.new('RGBA', im.size, CLEAR)
    od = ImageDraw.Draw(ov)
    for k in range(n):
        yy = y - k * 5
        xx = x + (1, -1, 2, -2, 0)[(k + s) % 5]
        r = 2 + (k % 2)
        od.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, 200 - k * 45))
    im.alpha_composite(ov)
    im.putalpha(im.getchannel('A').point(lambda v: 255 if v else 0))     # over open sky it is solid: no soft pixels


def chochin(d, x, y, w=9, h=12, body=VERM, hi=VERM_HI, lo=VERM_DK, mark=None):
    """A paper lantern (round shouldered), its top at (x, y)."""
    d.rectangle([x + 2, y, x + w - 3, y + 1], fill=INK)
    d.rectangle([x + 1, y + 2, x + w - 2, y + h - 3], fill=body)
    d.rectangle([x, y + 3, x + w - 1, y + h - 4], fill=body)
    d.line([(x, y + 3), (x, y + h - 4)], fill=hi)
    d.line([(x + 1, y + 2), (x + 1, y + h - 3)], fill=hi)
    d.line([(x + w - 1, y + 3), (x + w - 1, y + h - 4)], fill=lo)
    for ry in range(y + 4, y + h - 3, 2):
        d.line([(x + 2, ry), (x + w - 2, ry)], fill=lo)
    if mark:
        d.rectangle([x + w // 2 - 1, y + h // 2 - 2, x + w // 2, y + h // 2 + 1], fill=mark)
    d.rectangle([x + 2, y + h - 2, x + w - 3, y + h - 1], fill=INK)


def person(d, x, y, shirt, hair=INK, cap=None):
    """A shopkeeper behind a counter: head and shoulders, feet off-stage. (x, y) = top of the head."""
    d.rectangle([x - 4, y + 8, x + 4, y + 14], fill=shirt)
    d.rectangle([x - 3, y + 1, x + 3, y + 7], fill=SKIN)
    d.line([(x + 3, y + 2), (x + 3, y + 7)], fill=SKIN_LO)
    d.rectangle([x - 3, y, x + 3, y + 2], fill=cap or hair)
    if cap:
        d.line([(x - 3, y + 2), (x + 3, y + 2)], fill=VERM)
    d.point((x - 2, y + 4), fill=INK); d.point((x + 1, y + 4), fill=INK)
    d.line([(x - 1, y + 6), (x, y + 6)], fill=VERM_LO)


P_TEAL = (TEAL_HI, TEAL, TEAL_LO, TEAL_DK)


# ==============================================================================
# Dotonbori
# ==============================================================================
def mech_crab(im, d, cx, cy):
    """The giant crab: a riveted shell, steel discs at every joint."""
    def joint(x, y, r=2):
        d.ellipse([x - r, y - r, x + r, y + r], fill=STEEL_LO)
        d.ellipse([x - r, y - r, x + r - 1, y + r - 1], fill=STEEL)
        d.point((x - 1, y - 1), fill=WHITE)
    for s in (-1, 1):
        for k in range(4):
            hip = (cx + s * (17 + k * 2), cy + 1 + k * 3)
            knee = (cx + s * (33 + k * 4), cy - 9 + k * 6)
            foot = (cx + s * (45 + k * 3), cy + 5 + k * 8)
            tube(d, [hip, knee], 7, 6, P_RED); tube(d, [knee, foot], 6, 2, P_RED)
            joint(*knee)
        sh, el, hand = (cx + s * 19, cy - 7), (cx + s * 37, cy - 19), (cx + s * 31, cy - 31)
        tube(d, [sh, el], 6, 5, P_RED); tube(d, [el, hand], 5, 6, P_RED)
        ball(im, hand[0] - s * 3, hand[1] - 6, 10, 8, P_RED)
        d.polygon([(hand[0] - s * 14, hand[1] - 10), (hand[0] - s * 4, hand[1] - 6),
                   (hand[0] - s * 14, hand[1] - 5)], fill=CLEAR)
        d.line([(hand[0] - s * 13, hand[1] - 11), (hand[0] - s * 5, hand[1] - 7)], fill=VERM_DK)
        d.point((hand[0] - s * 12, hand[1] - 12), fill=WHITE)
        joint(*el, r=3)
    ball(im, cx, cy, 26, 15, P_RED)
    for s in (-1, 1):
        d.line([(cx + s * 7, cy - 12), (cx + s * 9, cy - 19)], fill=VERM_LO, width=2)
        d.ellipse([cx + s * 9 - 4, cy - 25, cx + s * 9 + 3, cy - 18], fill=WHITE)
        d.rectangle([cx + s * 9 - 1 - (s < 0), cy - 22, cx + s * 9 + (s > 0), cy - 20], fill=INK)
    for dx, dy in ((-15, -3), (-8, -9), (0, -11), (8, -9), (15, -3), (-19, 4), (19, 4)):   # rivets
        d.point((cx + dx, cy + dy), fill=YEL_HI); d.point((cx + dx, cy + dy + 1), fill=VERM_DK)
    d.arc([cx - 16, cy - 12, cx + 16, cy + 6], 20, 160, fill=VERM_LO)            # a seam across the shell
    d.line([(cx - 5, cy + 9), (cx + 5, cy + 9)], fill=VERM_DK)
    d.line([(cx - 3, cy + 11), (cx + 3, cy + 11)], fill=VERM_DK)


def crab_restaurant():
    im, d = canvas(4, 5)                 # 128 x 160
    facade_tile(d, 6, 58, 121, 157)
    bar(d, 4, 54, 123, 58, TILE_HI, WHITE, TILE_LO); d.line([(4, 58), (123, 58)], fill=TILE_DK)
    # the wave board the crab sits on
    board(d, 12, 70, 115, 92, INDIGO, rim=INK, hi=INDIGO_HI)
    for x in range(14, 114):
        y = 87 + round(2 * math.sin(x / 4.0))
        d.line([(x, y), (x, 90)], fill=rgb('3f6aa8'))
        d.point((x, y), fill=WHITE if x % 8 < 3 else rgb('79b4ee'))
    ckana(d, ['ka', 'ni'], 40, 73, WHITE, 1); ctext(d, 'SEAFOOD', 82, 74, YEL_HI, 1)
    # first-floor windows with lattice, lanterns between
    for x in (12, 50, 88):
        lit_window(d, x, 98, x + 27, 112, frame=TIMBER_DK, bars=5)
    for x in (41, 79):
        chochin(d, x, 98, 8, 12, WHITE, WHITE, PAPER_LO, mark=VERM)
    # awning, ground floor
    stripes(d, 4, 116, 123, 123, VERM, WHITE, 6, lo=TILE_DK)
    d.rectangle([7, 125, 120, 157], fill=TIMBER)
    doorway(d, 33, 126, 62, 157, INDIGO, INDIGO_LO, mark=WHITE)
    d.rectangle([66, 128, 117, 150], fill=TIMBER_DK)              # the tank in the window
    d.rectangle([67, 129, 116, 149], fill=rgb('3f6aa8'))
    d.line([(67, 129), (116, 129)], fill=rgb('79b4ee')); d.line([(67, 131), (116, 131)], fill=rgb('5b8dc9'))
    for x, y in ((74, 143), (90, 140), (105, 144)):
        d.rectangle([x - 3, y - 1, x + 3, y + 1], fill=VERM); d.point((x - 2, y - 2), fill=VERM_HI)
        d.line([(x - 5, y + 2), (x - 4, y + 2)], fill=VERM); d.line([(x + 4, y + 2), (x + 5, y + 2)], fill=VERM)
        d.point((x - 4, y - 3), fill=VERM); d.point((x + 4, y - 3), fill=VERM)
    for x in (70, 84, 99, 112):
        d.point((x, 136 - x % 3), fill=WHITE)
    d.rectangle([66, 151, 117, 157], fill=TIMBER_LO)
    d.rectangle([10, 130, 29, 152], fill=PAPER); d.rectangle([10, 130, 29, 131], fill=VERM)   # the menu case
    for y in range(135, 150, 4):
        d.line([(13, y), (26, y)], fill=CREAM_DK)
    d.rectangle([12, 134, 16, 138], fill=VERM)
    d.rectangle([4, 158, 123, 159], fill=STONE_LO)
    mech_crab(im, d, 64, 50)
    outline(im)
    return im


def octopus(im, d, cx, cy):
    """The giant octopus in a headband, one arm up with a takoyaki on a pick."""
    arms = ([(cx - 14, cy + 14), (cx - 30, cy + 22), (cx - 40, cy + 32), (cx - 36, cy + 42)],
            [(cx - 8, cy + 18), (cx - 16, cy + 30), (cx - 22, cy + 37), (cx - 18, cy + 43)],
            [(cx + 14, cy + 14), (cx + 30, cy + 22), (cx + 40, cy + 32), (cx + 36, cy + 42)],
            [(cx + 8, cy + 18), (cx + 16, cy + 30), (cx + 22, cy + 37), (cx + 18, cy + 43)],
            [(cx - 18, cy + 6), (cx - 34, cy + 2), (cx - 42, cy - 10), (cx - 37, cy - 18)],
            [(cx + 18, cy + 6), (cx + 34, cy + 0), (cx + 42, cy - 12)])
    for a in arms:
        tube(d, a, 8, 3.5, P_PINK)
        for i in range(1, len(a)):                                # suckers
            mx, my = (a[i - 1][0] + a[i][0]) // 2, (a[i - 1][1] + a[i][1]) // 2
            d.point((mx + 1, my + 2), fill=PINK_HI)
    # the pick and the takoyaki
    hx, hy = cx + 42, cy - 12
    d.line([(hx, hy), (hx + 5, hy - 16)], fill=WOOD_DK)
    ball(im, hx + 6, hy - 19, 6, 6, P_FRY)
    d.line([(hx + 3, hy - 21), (hx + 9, hy - 20)], fill=rgb('5a3420'))           # sauce
    d.point((hx + 5, hy - 23), fill=LIME); d.point((hx + 8, hy - 22), fill=LIME)
    ball(im, cx, cy, 25, 23, P_PINK)
    # hachimaki
    for x in range(cx - 24, cx + 25):
        nx = (x - cx) / 25.0
        yb = cy - 10 - round(3 * (1 - nx * nx))
        if abs(nx) < 0.93:
            d.line([(x, yb), (x, yb + 3)], fill=WHITE if nx < 0.5 else rgb('cfc9c0'))
    d.ellipse([cx - 3, cy - 14, cx + 2, cy - 10], fill=VERM)
    d.polygon([(cx + 22, cy - 11), (cx + 30, cy - 16), (cx + 28, cy - 9)], fill=WHITE)
    d.polygon([(cx + 22, cy - 9), (cx + 31, cy - 6), (cx + 26, cy - 3)], fill=rgb('cfc9c0'))
    for s in (-1, 1):                                             # eyes, brows, cheeks
        d.ellipse([cx + s * 10 - 4, cy - 4, cx + s * 10 + 4, cy + 6], fill=WHITE)
        d.ellipse([cx + s * 10 - 2 + (s > 0) * -1, cy - 1, cx + s * 10 + 1 + (s > 0) * -1, cy + 4], fill=INK)
        d.point((cx + s * 10 - 1, cy), fill=WHITE)
        d.line([(cx + s * 6, cy - 6), (cx + s * 14, cy - 8)], fill=PINK_DK)
        d.rectangle([cx + s * 17 - 2, cy + 7, cx + s * 17 + 1, cy + 8], fill=VERM_HI)
    d.ellipse([cx - 4, cy + 9, cx + 4, cy + 17], fill=PINK_DK)                  # the spout of a mouth
    d.ellipse([cx - 2, cy + 11, cx + 2, cy + 15], fill=rgb('5e1c3c'))
    d.point((cx - 3, cy + 10), fill=PINK_HI)


def takoyaki_stand():
    im, d = canvas(4, 4)                 # 128 x 128
    cx = 52
    # the stall
    d.rectangle([5, 70, 99, 125], fill=TIMBER)
    d.line([(5, 70), (5, 125)], fill=TIMBER_HI); d.rectangle([96, 70, 99, 125], fill=TIMBER_LO)
    board(d, 8, 72, 96, 90, VERM, rim=VERM_DK, hi=VERM_HI)
    ckana(d, ['ta', 'ko', 'ya', 'ki'], cx, 74, WHITE, 2, shadow=VERM_DK)
    d.rectangle([9, 92, 95, 110], fill=rgb('3a2a2c'))                           # the serving window
    d.rectangle([9, 92, 95, 93], fill=TIMBER_DK)
    person(d, 30, 94, WHITE, cap=WHITE)
    for x in (62, 74, 86):                                                      # paper boats on a shelf
        d.rectangle([x - 4, 97, x + 4, 100], fill=PAPER); d.line([(x - 4, 100), (x + 4, 100)], fill=PAPER_LO)
        d.rectangle([x - 3, 95, x - 1, 96], fill=FRY); d.rectangle([x + 1, 95, x + 3, 96], fill=FRY_LO)
    d.rectangle([10, 105, 94, 110], fill=rgb('2b2a30'))                         # the griddle
    d.line([(10, 105), (94, 105)], fill=STEEL_LO)
    for i, x in enumerate(range(13, 93, 5)):
        c = (FRY, FRY_HI, FRY_LO)[i % 3]
        d.rectangle([x, 106, x + 2, 108], fill=c); d.point((x, 106), fill=FRY_HI)
    d.rectangle([5, 111, 99, 113], fill=WOOD); d.line([(5, 111), (99, 111)], fill=rgb('d2a58c'))
    for i, x in enumerate(range(9, 94, 22)):                                    # banners on the counter front
        d.rectangle([x, 115, x + 17, 124], fill=(WHITE, YEL)[i % 2])
        d.rectangle([x + 2, 117, x + 5, 122], fill=VERM)
        d.line([(x + 8, 118), (x + 14, 118)], fill=INK); d.line([(x + 8, 121), (x + 13, 121)], fill=INK)
    stripes(d, 2, 62, 102, 70, YEL, VERM, 5, lo=TIMBER_DK)
    d.rectangle([3, 58, 101, 61], fill=VERM_LO); d.line([(3, 58), (101, 58)], fill=VERM_HI)
    d.rectangle([4, 126, 100, 127], fill=STONE_LO)
    # the queue rope beside it
    for x in (108, 123):
        d.rectangle([x - 1, 104, x, 124], fill=YEL_LO); d.line([(x - 1, 104), (x - 1, 124)], fill=YEL_HI)
        d.ellipse([x - 3, 100, x + 2, 105], fill=YEL); d.point((x - 2, 101), fill=WHITE)
        d.rectangle([x - 4, 124, x + 3, 126], fill=YEL_DK); d.line([(x - 4, 124), (x + 3, 124)], fill=YEL_LO)
    for x in range(108, 123):
        t = (x - 108) / 14.0
        y = 107 + round(5 * math.sin(math.pi * t))
        d.point((x, y), fill=VERM); d.point((x, y + 1), fill=VERM_LO)
    octopus(im, d, cx, 30)
    steam(im, 46, 100, 3); steam(im, 70, 101, 3, 2)
    outline(im)
    return im


def gyoza(im, d, cx, cy, rx=14, ry=9):
    """One pan-fried dumpling: a pleated crescent, its base browned."""
    ball(im, cx, cy, rx, ry, P_DOUGH)
    ball(im, cx, cy, rx, ry, P_FRY, a0=ry * 0.35)
    for k in range(-3, 4):                                        # the pleats along its crest
        x = cx + k * (rx / 4.2)
        y = cy - ry * math.sqrt(max(0, 1 - ((x - cx) / rx) ** 2))
        d.line([(x, y + 1), (x + 1, y + 4)], fill=DOUGH_LO)
        d.point((x - 1, y + 1), fill=WHITE)


def skewer(im, d, a, b, bits):
    """A giant skewer from a to b with fried pieces along it."""
    d.line([a, b], fill=WOOD_LO, width=2); d.line([(a[0] - 1, a[1]), (b[0] - 1, b[1])], fill=rgb('d2a58c'))
    for t, kind in bits:
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if kind == 'green':
            ball(im, x, y, 6, 5, (LIME, rgb('5fae5a'), rgb('3f7f48'), rgb('2a5a38')))
        else:
            ball(im, x, y, 7, 6, P_FRY)
            for k in range(5):
                d.point((round(x) - 3 + (k * 3) % 7, round(y) - 2 + (k * 2) % 5), fill=FRY_HI)
        if kind == 'shrimp':
            d.polygon([(x + 5, y - 4), (x + 11, y - 9), (x + 10, y - 2)], fill=VERM)


def neon_pole():
    im, d = canvas(1, 3)                 # 32 x 96
    d.rectangle([15, 8, 16, 92], fill=STEEL_LO); d.line([(15, 8), (15, 92)], fill=STEEL_HI)
    d.rectangle([12, 92, 19, 95], fill=STEEL_DK); d.line([(12, 92), (19, 92)], fill=STEEL_LO)
    ball(im, 15.5, 6, 4, 4, (WHITE, WARM, LIT, AMBER))
    signs = ((1, 12, PINK, PINK_HI, 'sake'), (18, 26, YEL_LO, YEL_HI, 'big'),
             (1, 42, TEAL_LO, CYAN, 'ta'), (18, 56, rgb('3f7f48'), LIME, 'ko'), (1, 70, VERM_LO, WARM, 'ya'))
    for x, y, rim, fg, g in signs:
        d.rectangle([x, y, x + 12, y + 12], fill=rim)
        d.rectangle([x + 1, y + 1, x + 11, y + 11], fill=rgb('1c1a22'))
        kana(d, [g], x + 3, y + 3, fg, 1)
        d.line([(x + 13, y + 5), (14, y + 5)] if x < 10 else [(17, y + 5), (x - 1, y + 5)], fill=STEEL_DK)
    outline(im)
    return im


def queue_rope():
    im, d = canvas(1, 1)
    for x in (5, 26):
        d.rectangle([x, 12, x + 1, 27], fill=YEL_LO); d.line([(x, 12), (x, 27)], fill=YEL_HI)
        d.ellipse([x - 2, 8, x + 3, 13], fill=YEL); d.point((x - 1, 9), fill=WHITE)
        d.rectangle([x - 3, 27, x + 4, 29], fill=YEL_DK); d.line([(x - 3, 27), (x + 4, 27)], fill=YEL_LO)
    for x in range(0, 32):                                        # the rope: post to post, and on to the next tile's
        if x in (5, 6, 26, 27):
            continue
        if 6 < x < 26:
            y = 14 + round(4 * math.sin(math.pi * (x - 7) / 18.0))
        else:
            y = 14 + round(2 * math.sin(math.pi * (((x + 32) if x < 5 else x) - 27) / 10.0))
        d.point((x, y), fill=VERM); d.point((x, y + 1), fill=VERM_DK)
    outline(im)
    return im


def menu_board():
    im, d = canvas(1, 1)
    d.polygon([(8, 9), (23, 9), (25, 28), (6, 28)], fill=TIMBER)
    d.line([(8, 9), (6, 28)], fill=TIMBER_HI); d.line([(23, 9), (25, 28)], fill=TIMBER_DK)
    d.rectangle([9, 11, 22, 25], fill=rgb('24302c'))
    d.rectangle([10, 12, 21, 13], fill=YEL)
    for y, w in ((16, 9), (19, 7), (22, 10)):
        d.line([(11, y), (10 + w, y)], fill=PAPER)
    d.rectangle([18, 18, 20, 20], fill=VERM)
    d.rectangle([6, 29, 8, 30], fill=TIMBER_DK); d.rectangle([23, 29, 25, 30], fill=TIMBER_DK)
    outline(im)
    return im


# ==============================================================================
# Ground families (opaque, 9 autotile roles)
# ==============================================================================
def _edge(role, x, y):
    tail = '' if role == 'center' else role.split('-')[-1]
    a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
    b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
    return min(a, b), (x if a <= b else y)


def family(role, tex, kerb, kw):
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    for y in range(32):
        for x in range(32):
            m, along = _edge(role, x, y)
            px[x, y] = kerb(m, along) if m < kw else tex(x, y)
    return im


DECKING = (rgb('6e4b3c'), rgb('654436'), rgb('775242'), rgb('6a4839'))


def board_kerb(m, along):
    if m == 1 and along % 8 == 3:
        return rgb('ffe9a8')                                      # footlight studs in the steel edge
    return (STEEL, STEEL_LO, STEEL_DK)[m]


RETRO = (rgb('ead9bd'), rgb('d99a86'), rgb('e3cfae'), rgb('cf8c7a'))


def retro_tex(x, y):
    """Retro tiled paving: an 8px checker of cream and dusty rose, a teal inset
    where four tiles meet, worn here and there."""
    tx, ty = x // 8, y // 8
    if x % 8 == 7 or y % 8 == 7:
        return rgb('b99f86')
    ix, iy = (x + 4) % 16, (y + 4) % 16
    if ix in (2, 3, 4) and iy in (2, 3, 4) and not (ix == 3 and iy == 3):
        return TEAL if (ix + iy) % 2 == 0 else TEAL_LO
    if ix == 3 and iy == 3:
        return TEAL_HI
    c = RETRO[((tx + ty) % 2) + (2 if h3(tx, ty, 5) < 60 else 0)]
    if x % 8 == 0 or y % 8 == 0:
        return rgb('f4e8d2') if (tx + ty) % 2 == 0 else rgb('e2a896')
    return c


def retro_kerb(m, along):
    if m == 0:
        return rgb('9c4a3c') if along % 8 != 7 else rgb('6b3a2c')
    if m == 1:
        return rgb('b9684a') if along % 8 != 7 else rgb('6b3a2c')
    return rgb('6b3a2c')


def ground(fam):
    tex, kerb, kw = {'osaka-boardwalk-autotile': (board_tex, board_kerb, 3),
                     'osaka-retro-paving-autotile': (retro_tex, retro_kerb, 3)}[fam]
    return lambda role: family(role, tex, kerb, kw)


# ==============================================================================
# Shinsekai
# ==============================================================================
BACK = rgb('475069')                     # what shows through a lattice: the far side of it, in shade


def cabinet(d, x, y, screen, body=DARK):
    """An arcade cabinet seen through the window: marquee, lit screen, panel."""
    d.rectangle([x, y, x + 11, y + 30], fill=body)
    d.line([(x, y), (x, y + 30)], fill=rgb('4a4258'))
    d.rectangle([x + 1, y + 1, x + 10, y + 4], fill=screen[1])
    d.rectangle([x + 1, y + 7, x + 10, y + 16], fill=screen[0])
    d.line([(x + 1, y + 7), (x + 10, y + 7)], fill=WHITE)
    d.point((x + 3, y + 11), fill=WHITE); d.point((x + 7, y + 13), fill=screen[1]); d.point((x + 5, y + 10), fill=INK)
    d.rectangle([x, y + 18, x + 11, y + 21], fill=rgb('5a5268'))
    d.point((x + 3, y + 18), fill=VERM); d.point((x + 3, y + 17), fill=VERM)
    d.point((x + 7, y + 19), fill=YEL); d.point((x + 9, y + 19), fill=CYAN)


def _arcade_front():
    im, d = canvas(4, 4)                 # 128 x 128
    d.rectangle([6, 22, 121, 125], fill=VIOLET)
    d.line([(6, 22), (6, 125)], fill=rgb('7a5cb0')); d.rectangle([116, 22, 121, 125], fill=VIOLET_LO)
    bar(d, 4, 18, 123, 22, PINK, PINK_HI, PINK_DK)
    # the marquee
    board(d, 10, 26, 117, 54, NIGHT, rim=INK)
    ctext(d, 'GAME', 64, 30, YEL_HI, 3, shadow=PINK)
    heart = ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...']
    glyphs(d, [heart], 16, 34, PINK, 1); d.point((17, 35), fill=WHITE)
    bot = ['#.....#', '##...##', '#######', '#.###.#', '#######', '.#####.']             # an invented pixel critter
    glyphs(d, [bot], 104, 34, CYAN, 1)
    for y in (57, 60):                                                                # chevron stripes
        for x in range(7, 116, 6):
            d.line([(x, y + 2), (x + 2, y), (x + 4, y + 2)], fill=TEAL_HI if y == 57 else PINK_HI)
    # the front: cabinets behind glass, the door, a crane machine
    d.rectangle([8, 66, 61, 118], fill=INK)
    d.rectangle([9, 67, 60, 117], fill=rgb('2b2444'))
    cabinet(d, 12, 82, (CYAN, PINK)); cabinet(d, 28, 82, (LIME, YEL)); cabinet(d, 44, 82, (PINK_HI, CYAN))
    for x in range(10, 60, 4):                                                        # a string of bulbs in the window
        d.point((x, 70 + (x // 4) % 2), fill=(WARM, PINK_HI, CYAN)[(x // 4) % 3])
    d.rectangle([9, 113, 60, 117], fill=rgb('40365e'))
    for x in range(9, 60, 8):
        d.rectangle([x, 113, x + 3, 117], fill=rgb('5b4f80'))
    d.rectangle([8, 66, 61, 118], outline=PINK)
    glass_door(d, 66, 78, 93, 125, frame=INK)
    board(d, 66, 66, 93, 76, TEAL_DK, rim=INK, lamp=False); ctext(d, 'OPEN', 80, 68, CYAN, 1)
    d.rectangle([98, 66, 119, 118], fill=INK)                                         # the crane machine
    d.rectangle([99, 67, 118, 100], fill=rgb('cfeafc'))
    d.line([(99, 67), (118, 67)], fill=WHITE); d.line([(101, 69), (101, 96)], fill=WHITE)
    d.line([(108, 67), (108, 78)], fill=STEEL_DK); d.line([(105, 79), (111, 79)], fill=STEEL_DK)
    d.line([(105, 79), (105, 82)], fill=STEEL_DK); d.line([(111, 79), (111, 82)], fill=STEEL_DK)
    for i, (x, y) in enumerate(((102, 94), (107, 92), (112, 95), (115, 91), (104, 89), (110, 97))):
        c = (PINK, YEL, TEAL, VERM, LIME, CYAN)[i]
        d.rectangle([x, y, x + 3, y + 3], fill=c); d.point((x, y), fill=WHITE)
    d.rectangle([99, 101, 118, 117], fill=PINK); d.line([(99, 101), (118, 101)], fill=PINK_HI)
    d.rectangle([102, 106, 108, 112], fill=INK); d.ellipse([112, 105, 115, 108], fill=YEL)
    d.rectangle([6, 119, 121, 125], fill=VIOLET_DK)
    d.rectangle([4, 126, 123, 127], fill=STONE_LO)
    return im


TIN, TIN_HI, TIN_LO, TIN_DK = rgb('8fa39c'), rgb('b9cbc2'), rgb('6c807c'), rgb('4e5e5e')
RUST = rgb('a8623c')


def tachinomi():
    im, d = canvas(3, 4)                 # 96 x 128
    # the upper wall: corrugated tin gone to rust at the seams
    for x in range(6, 90):
        c = (TIN_HI, TIN, TIN, TIN_LO)[x % 4]
        d.line([(x, 36), (x, 84)], fill=c)
    for x, y, n in ((8, 70, 12), (40, 78, 6), (84, 44, 10), (60, 38, 4), (20, 38, 5)):
        for k in range(n):
            d.point((x + (k * 5) % 7, y + k), fill=RUST)
    d.rectangle([86, 36, 89, 84], fill=TIN_DK)
    d.rectangle([4, 32, 91, 36], fill=TIN_LO); d.line([(4, 32), (91, 32)], fill=TIN_HI)
    for x in range(6, 90, 4):
        d.point((x, 35), fill=TIN_DK)
    board(d, 12, 42, 72, 56, VERM, rim=VERM_DK, lamp=False, hi=VERM_HI)
    ctext(d, 'TACHINOMI', 42, 46, WHITE, 1)
    d.rectangle([12, 60, 34, 80], fill=YEL_HI); d.rectangle([12, 60, 34, 80], outline=TIMBER_DK)   # a beer poster
    d.rectangle([18, 67, 26, 77], fill=AMBER); d.rectangle([18, 64, 26, 67], fill=WHITE)
    d.rectangle([27, 69, 29, 74], fill=AMBER); d.point((28, 71), fill=YEL_HI)
    d.rectangle([38, 60, 58, 80], fill=TEAL_HI); d.rectangle([38, 60, 58, 80], outline=TIMBER_DK)  # and a faded one
    d.ellipse([43, 64, 53, 74], fill=VERM_HI); d.line([(41, 77), (55, 77)], fill=TEAL_DK)
    chochin(d, 72, 56, 14, 22, VERM, VERM_HI, VERM_DK)
    kana(d, ['sake'], 76, 64, WHITE, 1)
    # the lean-to and the open front
    for y in range(7):
        d.line([(3 - y // 2, 85 + y), (92 + y // 2, 85 + y)], fill=TIN_LO if y in (0, 6) else TIN)
        for x in range(4, 92, 4):
            d.point((x, 85 + y), fill=TIN_DK)
    d.line([(3, 85), (92, 85)], fill=TIN_HI)
    d.rectangle([6, 93, 89, 125], fill=TIMBER); d.rectangle([85, 93, 89, 125], fill=TIMBER_DK)
    d.rectangle([8, 95, 31, 125], fill=TIMBER_DK)                                # the bar, open to the street
    d.rectangle([9, 96, 30, 110], fill=WARM)
    for x in (11, 15, 25):                                                       # bottles on the back shelf
        d.rectangle([x, 99, x + 2, 106], fill=(TEAL_DK, rgb('7a4a1c'), VERM_LO)[x % 3]); d.point((x + 1, 98), fill=WHITE)
    person(d, 20, 97, WHITE, hair=rgb('8a8078'))
    d.rectangle([8, 111, 31, 114], fill=WOOD); d.line([(8, 111), (31, 111)], fill=rgb('d2a58c'))
    d.rectangle([9, 115, 30, 125], fill=TIMBER_LO)
    for x in range(12, 30, 5):
        d.line([(x, 115), (x, 125)], fill=TIMBER_DK)
    for x in (11, 26):                                                           # mugs on the counter
        d.rectangle([x, 107, x + 3, 110], fill=AMBER); d.line([(x, 107), (x + 3, 107)], fill=WHITE)
    doorway(d, 34, 95, 61, 125, rgb('7a4a34'), rgb('553224'), mark=PAPER)
    for y0 in (104, 115):                                                        # crates by the door
        d.rectangle([68, y0, 83, y0 + 10], fill=YEL); d.line([(68, y0), (83, y0)], fill=YEL_HI)
        d.rectangle([70, y0 + 3, 81, y0 + 5], fill=YEL_DK); d.line([(68, y0 + 10), (83, y0 + 10)], fill=YEL_DK)
        d.rectangle([80, y0, 83, y0 + 10], fill=YEL_LO)
    for x in range(70, 82, 4):
        d.rectangle([x, 101, x + 1, 103], fill=rgb('7a4a1c')); d.point((x, 101), fill=YEL_HI)
    d.rectangle([3, 126, 92, 127], fill=STONE_LO)
    outline(im)
    return im


def shinsekai_arch():
    im, d = canvas(5, 4)                 # 160 x 128
    cx = 80

    def top(x):
        return 14 + 22 * ((x - cx) / 76.0) ** 2

    # the posts: teal lattice columns on concrete feet
    for x0 in (5, 133):
        d.rectangle([x0, 34, x0 + 21, 122], fill=TEAL_DK)
        for y in range(38, 120, 14):
            d.line([(x0 + 2, y), (x0 + 19, y + 13)], fill=TEAL_LO); d.line([(x0 + 19, y), (x0 + 2, y + 13)], fill=TEAL)
            d.line([(x0, y), (x0 + 21, y)], fill=TEAL_HI)
        d.rectangle([x0, 34, x0 + 3, 122], fill=TEAL_HI); d.rectangle([x0 + 1, 34, x0 + 3, 122], fill=TEAL)
        d.rectangle([x0 + 18, 34, x0 + 21, 122], fill=TEAL_LO)
        d.rectangle([x0 - 2, 120, x0 + 23, 127], fill=STONE); d.line([(x0 - 2, 120), (x0 + 23, 120)], fill=WHITE)
        d.rectangle([x0 - 2, 125, x0 + 23, 127], fill=STONE_LO)
    # the beam: a yellow bow, red rims, a disc for every letter
    for x in range(3, 157):
        t = int(round(top(x)))
        d.line([(x, t), (x, t + 25)], fill=YEL if x < 110 else YEL_LO)
        d.rectangle([x, t, x, t + 2], fill=VERM); d.point((x, t), fill=VERM_HI)
        d.rectangle([x, t + 23, x, t + 25], fill=VERM_LO)
        if x % 4 == 0:
            d.point((x, t + 1), fill=WARM); d.point((x, t + 24), fill=WARM)
    for i, ch in enumerate('SHINSEKAI'):
        x = round(cx + (i - 4) * 15.5)
        y = int(round(top(x))) + 13
        ball(im, x, y, 7.5, 7.5, (VERM_HI, VERM, VERM, VERM_LO))
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=VERM_DK)
        text(d, ch, x - 2, y - 3, WHITE, 1)
    # the crown: a starburst
    ball(im, cx, 9, 9, 9, P_TEAL)
    star(d, cx, 9, 7, YEL_HI, edge=YEL_LO)
    for a in range(0, 360, 30):
        r0, r1 = 11, 14
        d.line([(cx + r0 * math.cos(math.radians(a)), 9 + r0 * math.sin(math.radians(a)) * 0.8),
                (cx + r1 * math.cos(math.radians(a)), 9 + r1 * math.sin(math.radians(a)) * 0.8)], fill=YEL)
    # lanterns on a wire under the beam
    for i in range(8):
        x = round(34 + i * 13.1)
        y = int(round(top(x))) + 27
        d.line([(x + 4, y - 1), (x + 4, y)], fill=INK)
        chochin(d, x, y, 9, 12, WHITE, WHITE, PAPER_LO, mark=VERM if i % 2 == 0 else TEAL)
    outline(im)
    return im


GACHA = (VERM, YEL, TEAL, PINK, INDIGO_HI, LIME, rgb('f08a3c'), WHITE)


def gacha_machine(d, x, y, w, h, i):
    body = GACHA[i % len(GACHA)]
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=body)
    d.line([(x, y), (x, y + h - 1)], fill=WHITE); d.line([(x + w - 1, y), (x + w - 1, y + h - 1)], fill=STONE_DK)
    d.line([(x, y + h - 1), (x + w - 1, y + h - 1)], fill=STONE_DK)
    wy = y + 2
    d.rectangle([x + 1, wy, x + w - 2, wy + h // 2 - 2], fill=rgb('dff1fb'))    # the capsule window
    d.line([(x + 1, wy), (x + w - 2, wy)], fill=WHITE)
    for k in range((w - 3) // 3):                                               # capsules: a coloured half, a clear half
        for j in range(2):
            cxx, cyy = x + 2 + k * 3 + (j % 2), wy + 2 + j * 4 + (h // 2 - 8) // 2
            d.rectangle([cxx, cyy, cxx + 1, cyy + 1], fill=GACHA[(i * 3 + k + j * 2) % len(GACHA)])
            d.point((cxx, cyy + 2), fill=WHITE)
    ly = wy + h // 2
    d.rectangle([x + 1, ly, x + w // 2 - 1, y + h - 3], fill=WHITE)             # the card
    d.rectangle([x + 2, ly + 1, x + w // 2 - 2, ly + 3], fill=GACHA[(i + 3) % len(GACHA)])
    d.ellipse([x + w // 2 + 1, ly, x + w - 3, ly + w // 2 - 4], fill=STEEL)     # the knob
    d.point((x + w // 2 + 2, ly + 1), fill=WHITE)
    d.rectangle([x + w // 2 + 1, y + h - 4, x + w - 3, y + h - 3], fill=INK)    # the chute


def gacha_row():
    im, d = canvas(2, 2)                 # 64 x 64
    board(d, 8, 2, 55, 13, VERM, rim=VERM_DK, lamp=False, hi=VERM_HI)
    ctext(d, 'GACHA', 32, 4, YEL_HI, 1)
    for r in range(2):
        for i in range(4):
            gacha_machine(d, 2 + i * 15, 14 + r * 23, 15, 23, i + r * 5)
    d.rectangle([1, 60, 62, 63], fill=STONE_DK); d.line([(1, 60), (62, 60)], fill=STONE_LO)
    outline(im)
    return im


def gacha_single():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([9, 10, 22, 13], fill=YEL); d.line([(9, 10), (22, 10)], fill=YEL_HI)
    star(d, 16, 8, 4, VERM)
    gacha_machine(d, 8, 14, 16, 23, 2); gacha_machine(d, 8, 37, 16, 23, 6)
    d.rectangle([7, 60, 24, 63], fill=STONE_DK); d.line([(7, 60), (24, 60)], fill=STONE_LO)
    outline(im)
    return im


def shinsekai_lanterns():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([15, 6, 16, 60], fill=TIMBER); d.line([(15, 6), (15, 60)], fill=TIMBER_HI)
    d.rectangle([12, 60, 19, 63], fill=STONE_LO); d.line([(12, 60), (19, 60)], fill=STONE)
    d.rectangle([2, 8, 29, 9], fill=TIMBER); d.line([(2, 8), (29, 8)], fill=TIMBER_HI)
    d.rectangle([13, 3, 18, 6], fill=KAWARA); d.line([(13, 3), (18, 3)], fill=KAWARA_HI)
    chochin(d, 2, 11, 10, 14, WHITE, WHITE, PAPER_LO, mark=VERM)
    chochin(d, 20, 11, 10, 14, WHITE, WHITE, PAPER_LO, mark=TEAL)
    d.rectangle([6, 30, 25, 31], fill=TIMBER); d.line([(6, 30), (25, 30)], fill=TIMBER_HI)
    chochin(d, 4, 33, 9, 12, VERM, VERM_HI, VERM_DK, mark=WHITE)
    chochin(d, 19, 33, 9, 12, WHITE, WHITE, PAPER_LO, mark=VERM)
    outline(im)
    return im


# ==============================================================================
# Second pass: shared bits
# ==============================================================================
def walker(d, x, y, shirt, legs=INDIGO_LO, hair=INK):
    """A passer-by, whole: head, hair, shirt, two legs. (x, y) = between the feet."""
    d.rectangle([x - 2, y - 4, x - 1, y], fill=legs); d.rectangle([x + 1, y - 4, x + 2, y], fill=legs)
    d.rectangle([x - 3, y - 10, x + 3, y - 5], fill=shirt)
    d.line([(x - 3, y - 10), (x - 3, y - 6)], fill=SKIN); d.line([(x + 3, y - 10), (x + 3, y - 6)], fill=SKIN_LO)
    d.rectangle([x - 2, y - 15, x + 2, y - 11], fill=SKIN)
    d.line([(x + 2, y - 14), (x + 2, y - 11)], fill=SKIN_LO)
    d.rectangle([x - 2, y - 16, x + 2, y - 14], fill=hair); d.point((x - 2, y - 13), fill=hair)


def doorway(d, x0, y0, x1, y1, col, lo, mark=None, frame=TIMBER_DK):
    """An open way in, unmistakably a door: a heavy frame, the lit room behind,
    a stone step, and a noren parted down the middle."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 2, y0 + 1, x1 - 2, y1 - 3], fill=WARM)
    d.rectangle([x0 + 2, y0 + 16, x1 - 2, y1 - 3], fill=LIT)
    d.rectangle([x0 + 2, y1 - 9, x1 - 2, y1 - 3], fill=rgb('d9952f'))
    d.line([(x0 + 2, y1 - 9), (x1 - 2, y1 - 9)], fill=rgb('a3641f'))          # the floor inside
    d.rectangle([x0 - 1, y1 - 2, x1 + 1, y1], fill=STONE)                     # the step
    d.line([(x0 - 1, y1 - 2), (x1 + 1, y1 - 2)], fill=WHITE); d.line([(x0 - 1, y1), (x1 + 1, y1)], fill=STONE_LO)
    m = (x0 + x1) // 2
    d.line([(x0 - 1, y0), (x1 + 1, y0)], fill=WOOD_DK)
    for a, b in ((x0 + 1, m - 3), (m + 3, x1 - 1)):
        d.rectangle([a, y0 + 1, b, y0 + 12], fill=col)
        d.line([(b, y0 + 1), (b, y0 + 12)], fill=lo)
        c = (a + b) // 2
        d.line([(c, y0 + 8), (c, y0 + 12)], fill=lo)
        if mark:
            d.rectangle([c - 2, y0 + 3, c + 1, y0 + 6], fill=mark)


def outline_hull(im, hull):
    """Ink the outer silhouette only. `hull` (an L mask) counts as solid, so the
    gaps of an open lattice inside it are not edged and stay see-through."""
    f = im.copy()
    hole = ImageChops.multiply(hull, f.getchannel('A').point(lambda v: 0 if v else 255))
    f.paste((1, 2, 3, 255), (0, 0), hole)
    before = f.getchannel('A')
    outline(f)
    im.paste(INK, (0, 0), ImageChops.subtract(f.getchannel('A'), before))


def burst(d, cx, cy, r0, r1, n=9, fill=rgb('2a1418'), turn=8):
    """A jagged hole smashed through a board."""
    pts = []
    for k in range(n * 2):
        r = r0 if k % 2 == 0 else r1
        a = math.radians(k * 180.0 / n + turn)
        pts.append((round(cx + r * math.cos(a)), round(cy + r * 0.85 * math.sin(a))))
    d.polygon(pts, fill=fill)


P_IRON = (rgb('7a8598'), rgb('4d566b'), rgb('363c50'), rgb('23283a'))
P_HORN = (WHITE, DOUGH, DOUGH_LO, DOUGH_DK)


# ==============================================================================
# Station front
# ==============================================================================
def station_front():
    """Osaka Station as its roof: one great sloping plane of glass, wider than
    the building and higher than anything beside it, on white steel trees; under
    it the open deck with the gold clock, a train standing at the platform
    behind, and a low stone front of shops with the doors in the middle."""
    im, d = canvas(10, 6)                # 320 x 192
    FAR, FAR_LO, FAR_HI = rgb('3c4c7c'), rgb('2d3a62'), rgb('5269a3')

    def top(x):
        return 3 + int(round(20 * x / 319.0))

    # ---- the far gate building, seen under the roof ------------------------------
    for x in range(12, 308):
        d.line([(x, top(x) + 21), (x, 97)], fill=FAR)
    for j, y in enumerate(range(33, 70, 7)):
        for x in range(14, 306):
            if y > top(x) + 30 and x % 6 != 5:
                lit = h3(x // 6, j, 3) % 9 == 0
                d.point((x, y), fill=WHITE if lit else FAR_HI)
                d.line([(x, y + 1), (x, y + 3)], fill=WARM if lit else FAR_LO)
    # ---- a train standing at the platform ---------------------------------------
    d.rectangle([14, 71, 305, 72], fill=STEEL_LO)
    d.rectangle([14, 73, 305, 88], fill=rgb('ece4d0'))
    d.line([(14, 73), (305, 73)], fill=WHITE)
    d.rectangle([14, 84, 305, 85], fill=rgb('f08a3c'))
    for x in range(18, 300, 9):
        k = ((x - 18) % 72) // 9
        if k == 7:
            d.rectangle([x + 2, 73, x + 4, 88], fill=FAR_LO)                  # between two cars
        elif k in (2, 5):
            d.rectangle([x, 75, x + 6, 88], fill=STEEL)
            d.rectangle([x + 1, 76, x + 2, 82], fill=GLASS); d.rectangle([x + 4, 76, x + 5, 82], fill=GLASS)
        else:
            lit = h3(x, 1, 7) % 4 != 0
            d.rectangle([x, 76, x + 6, 81], fill=WARM if lit else GLASS)
            d.line([(x, 76), (x + 6, 76)], fill=WHITE if lit else GLASS_HI)
    d.rectangle([12, 89, 307, 91], fill=STEEL_DK)
    # ---- the white steel trees that carry the roof -------------------------------
    for x in (52, 124, 196, 268):
        for bx in (x - 22, x, x + 22):
            d.line([(x + 1, 66), (bx + 1, top(bx) + 27)], fill=STEEL_LO)
            d.line([(x, 66), (bx, top(bx) + 27)], fill=WHITE)
        bar(d, x - 1, 64, x + 2, 95, STEEL_HI, WHITE, STEEL_LO)
    # ---- the two stone pylons at its ends ----------------------------------------
    for x0 in (8, 298):
        t = top(x0) + 28
        facade_tile(d, x0, t, x0 + 13, 97, pal=(TAN, TAN_HI, TAN_LO, TAN_DK), tw=6, th=5)
        d.rectangle([x0 + 5, t + 6, x0 + 8, 90], fill=GLASS_DK)
        for y in range(t + 7, 88, 6):
            d.rectangle([x0 + 6, y, x0 + 7, y + 3], fill=WARM if h3(x0, y, 2) % 3 == 0 else GLASS)
    # ---- people on the deck, the clock they meet under ----------------------------
    crowd = ((30, VERM, INDIGO_LO, INK), (40, TILE, TIMBER_DK, TIMBER_LO), (70, TEAL, INDIGO_LO, INK),
             (104, YEL, TIMBER_DK, INK), (112, PINK, INDIGO_LO, TIMBER_LO), (146, INDIGO_HI, DARK, INK),
             (170, TILE, INDIGO_LO, rgb('8a8078')), (216, VERM_LO, DARK, INK), (228, LIME, INDIGO_LO, TIMBER_LO),
             (250, TEAL_DK, TIMBER_DK, INK), (284, YEL_LO, INDIGO_LO, INK))
    for x, sh, lg, hr in crowd:
        walker(d, x, 95, sh, lg, hr)
    cxk, cyk = 88, 53
    bar(d, cxk - 2, 62, cxk + 1, 95, YEL_LO, YEL_HI, YEL_DK)
    d.rectangle([cxk - 5, 92, cxk + 4, 95], fill=YEL_DK); d.line([(cxk - 5, 92), (cxk + 4, 92)], fill=YEL_LO)
    ball(im, cxk, cyk, 14, 14, P_GOLD)
    ball(im, cxk, cyk, 11, 11, (WHITE, WHITE, PAPER, PAPER_LO))
    d.ellipse([cxk - 11, cyk - 11, cxk + 11, cyk + 11], outline=YEL_DK)
    for k in range(12):
        a = math.radians(k * 30)
        d.point((round(cxk + 9 * math.sin(a)), round(cyk - 9 * math.cos(a))), fill=INK if k % 3 == 0 else TERRA_DK)
    d.line([(cxk, cyk), (cxk - 5, cyk - 6)], fill=INK, width=2); d.line([(cxk, cyk), (cxk + 7, cyk + 2)], fill=INK)
    d.point((cxk, cyk), fill=VERM)
    d.line([(8, 91), (311, 91)], fill=WHITE); d.line([(8, 92), (311, 92)], fill=STEEL_LO)      # the deck's rail
    for x in range(8, 312, 12):
        d.line([(x, 92), (x, 96)], fill=STEEL)
    # ---- the roof: glass in a white steel grid, a truss under its lower edge -------
    for x in range(0, 320):
        t = top(x)
        for k in range(21):
            if x % 10 == 0 or k in (7, 14):
                c = WHITE
            elif ((x + k * 2) // 14) % 5 == 0:
                c = rgb('d4eefc')
            else:
                c = (rgb('aad8f5'), rgb('93c8ee'), rgb('7fb6e4'))[k // 7]
            d.point((x, t + k), fill=c)
        d.point((x, t), fill=WHITE); d.point((x, t + 1), fill=WHITE)
        d.point((x, t + 21), fill=STEEL_HI); d.point((x, t + 27), fill=STEEL_LO)
        w = x % 10
        d.point((x, t + 22 + min(4, w if w < 5 else 10 - w)), fill=STEEL)
    d.line([(0, top(0)), (0, top(0) + 27)], fill=STEEL_HI); d.line([(319, top(319)), (319, top(319) + 27)], fill=STEEL_LO)
    # ---- the stone front under the deck --------------------------------------------
    facade_tile(d, 4, 98, 315, 188, pal=(TAN, TAN_HI, TAN_LO, TAN_DK), tw=10, th=5)
    d.rectangle([0, 96, 319, 99], fill=STEEL_HI)
    d.line([(0, 96), (319, 96)], fill=WHITE); d.line([(0, 99), (319, 99)], fill=STEEL_LO)
    d.rectangle([4, 100, 315, 119], fill=CREAM)
    d.line([(4, 100), (315, 100)], fill=WHITE); d.line([(4, 119), (315, 119)], fill=CREAM_LO)
    d.line([(4, 120), (315, 120)], fill=TAN_DK)
    d.rectangle([312, 100, 315, 119], fill=CREAM_LO)
    ctext(d, 'OSAKA', 250, 103, TERRA_DK, 2)                                   # the name, east of the doors
    d.rectangle([22, 102, 114, 117], fill=STEEL_DK)                            # the departures board, west of them
    d.rectangle([23, 103, 113, 116], fill=rgb('141a2a'))
    for j, y in enumerate((105, 108, 111, 114)):
        d.line([(26, y), (36, y)], fill=LIME)
        d.line([(41, y), (41 + 14 + (h3(j, 2, 1) % 4) * 6, y)], fill=AMBER)
        d.line([(88, y), (98, y)], fill=AMBER if j % 2 else VERM_HI)
        d.line([(103, y), (109, y)], fill=CYAN)

    def bay(x0, x1, col, lo, word, fg=WHITE, room=WARM):
        d.rectangle([x0, 123, x1, 133], fill=col)
        d.line([(x0, 133), (x1, 133)], fill=lo)
        ctext(d, word, (x0 + x1 + 1) // 2, 125, fg, 1)
        d.rectangle([x0, 136, x1, 182], fill=STONE_DK)
        d.rectangle([x0 + 1, 137, x1 - 1, 181], fill=room)
        d.line([(x0 + 1, 137), (x1 - 1, 137)], fill=WHITE)
        d.rectangle([x0, 183, x1, 188], fill=TAN_LO); d.line([(x0, 183), (x1, 183)], fill=TAN_DK)

    # a bakery: loaves on three shelves
    bay(9, 57, TERRA, TERRA_DK, 'BAKERY', CREAM)
    for j, sy in enumerate((151, 164, 177)):
        d.line([(10, sy), (56, sy)], fill=WOOD_LO); d.line([(10, sy + 1), (56, sy + 1)], fill=WOOD_DK)
        for i, x in enumerate(range(13 + (j % 2) * 3, 52, 8)):
            c, hi = ((FRY, FRY_HI), (DOUGH_LO, DOUGH_HI), (rgb('b9783a'), FRY))[(i + j) % 3]
            d.rectangle([x, sy - 4, x + 5, sy - 1], fill=c); d.line([(x + 1, sy - 5), (x + 4, sy - 5)], fill=c)
            d.line([(x + 1, sy - 4), (x + 3, sy - 4)], fill=hi)
    # the ticket office: two clerks at a counter
    GREEN, GREEN_LO = rgb('3f8f5a'), rgb('2a6a42')
    bay(65, 117, GREEN, GREEN_LO, 'TICKETS', WHITE, room=rgb('dfe9f2'))
    d.line([(91, 137), (91, 162)], fill=STONE_DK)
    person(d, 78, 146, INDIGO, cap=INDIGO_LO); person(d, 104, 146, INDIGO, cap=INDIGO_LO)
    d.rectangle([66, 161, 116, 164], fill=STEEL_HI); d.line([(66, 164), (116, 164)], fill=STEEL_LO)
    d.rectangle([66, 165, 116, 181], fill=GREEN)
    d.line([(66, 165), (116, 165)], fill=GREEN_LO)
    for x in (74, 100):
        d.rectangle([x, 169, x + 8, 176], fill=WHITE); d.line([(x + 2, 171), (x + 6, 171)], fill=GREEN_LO)
        d.line([(x + 2, 174), (x + 5, 174)], fill=GREEN_LO)
    # a cafe: two people at a table
    bay(203, 251, INDIGO, INDIGO_LO, 'CAFE', WARM)
    person(d, 215, 150, VERM_LO); person(d, 239, 150, TEAL_DK, hair=TIMBER_LO)
    d.rectangle([221, 163, 233, 164], fill=TIMBER); d.line([(227, 165), (227, 170)], fill=TIMBER_DK)
    d.rectangle([222, 160, 224, 162], fill=WHITE); d.rectangle([230, 160, 232, 162], fill=WHITE)
    d.rectangle([204, 168, 250, 181], fill=TIMBER); d.line([(204, 168), (250, 168)], fill=TIMBER_HI)
    for x in range(210, 250, 8):
        d.line([(x, 170), (x, 181)], fill=TIMBER_LO)
    d.rectangle([222, 140, 232, 146], fill=INDIGO_LO)                           # a hanging lamp
    d.line([(227, 137), (227, 140)], fill=INK); d.line([(223, 147), (231, 147)], fill=WHITE)
    # a station-bento counter: lacquer boxes stacked, a clerk
    bay(261, 311, VERM, VERM_DK, 'BENTO', WHITE)
    for j, sy in enumerate((152, 162, 172)):
        d.line([(262, sy), (294, sy)], fill=WOOD_LO)
        for i, x in enumerate(range(264, 290, 9)):
            d.rectangle([x, sy - 5, x + 6, sy - 1], fill=(VERM_LO, INK, rgb('5a3420'))[(i + j) % 3])
            d.rectangle([x + 1, sy - 4, x + 3, sy - 2], fill=WHITE)
            d.point((x + 5, sy - 4), fill=(YEL, LIME, PINK)[(i + j * 2) % 3]); d.point((x + 5, sy - 2), fill=FRY)
    person(d, 302, 152, WHITE, cap=VERM)
    d.rectangle([262, 173, 310, 181], fill=VERM_LO); d.line([(262, 173), (310, 173)], fill=VERM_HI)
    for x in (4, 59, 119, 197, 253, 312):                                       # stone piers
        d.rectangle([x, 122, x + 3, 188], fill=CREAM)
        d.line([(x, 122), (x, 188)], fill=WHITE); d.line([(x + 3, 122), (x + 3, 188)], fill=CREAM_LO)
    # the way in: a glass canopy, two pairs of doors (cells 4 and 5 of row 5)
    d.rectangle([126, 126, 193, 188], fill=STONE_DK)
    glass_door(d, 129, 128, 158, 188); glass_door(d, 161, 128, 190, 188)
    d.rectangle([121, 112, 198, 123], fill=rgb('9fd0f2'))
    for x in range(121, 199, 11):
        d.line([(x, 112), (x, 123)], fill=WHITE)
    d.line([(121, 112), (198, 112)], fill=WHITE); d.line([(121, 113), (198, 113)], fill=WHITE)
    d.rectangle([121, 124, 198, 126], fill=STEEL); d.line([(121, 126), (198, 126)], fill=STEEL_DK)
    for x in range(125, 197, 6):
        d.point((x, 127), fill=WARM)
    d.rectangle([2, 189, 317, 191], fill=STONE_LO); d.line([(2, 189), (317, 189)], fill=STONE)
    outline(im)
    return im


def wheel_mall():
    """The station district's other landmark: a red wheel rising out of the roof
    of a shopping block."""
    W, H = 160, 224
    im, d = canvas(5, 7)
    cx, cy, R = 80, 68, 62
    hull = Image.new('L', (W, H), 0)
    ImageDraw.Draw(hull).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    for k in range(16):                                           # spokes, a far set behind them
        a = math.radians(k * 22.5 + 11.25)
        d.line([(cx, cy), (cx + (R - 3) * math.cos(a), cy + (R - 3) * math.sin(a))], fill=VERM_DK)
    for k in range(16):
        a = math.radians(k * 22.5)
        ex, ey = cx + (R - 2) * math.cos(a), cy + (R - 2) * math.sin(a)
        d.line([(cx + 1, cy), (ex + 1, ey)], fill=VERM_LO)
        d.line([(cx, cy), (ex, ey)], fill=VERM_HI if math.cos(a) < 0 else VERM)
    for r, c in ((R, VERM_LO), (R - 1, VERM), (R - 2, VERM_HI), (R - 3, VERM), (R - 16, VERM_LO), (R - 17, VERM)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c)
    for k in range(48):                                           # bulbs round the rim
        a = math.radians(k * 7.5 + 3.75)
        d.point((round(cx + (R - 1.5) * math.cos(a)), round(cy + (R - 1.5) * math.sin(a))), fill=WARM)
    for k in range(16):                                           # gondolas, hanging level
        a = math.radians(k * 22.5)
        gx, gy = round(cx + R * math.cos(a)), round(cy + R * math.sin(a))
        col, hi, lo = ((TILE, WHITE, TILE_LO), (YEL, YEL_HI, YEL_LO))[k % 2]
        d.rectangle([gx - 4, gy, gx + 4, gy + 8], fill=col)
        d.line([(gx - 4, gy), (gx - 4, gy + 8)], fill=hi); d.line([(gx + 4, gy), (gx + 4, gy + 8)], fill=lo)
        d.rectangle([gx - 3, gy + 2, gx + 3, gy + 4], fill=rgb('9fd0f2')); d.point((gx - 3, gy + 2), fill=WHITE)
        d.rectangle([gx - 4, gy, gx + 4, gy], fill=VERM_LO)
        d.point((gx, gy - 1), fill=STEEL_DK)
    ball(im, cx, cy, 8, 8, P_RED)
    ball(im, cx, cy, 4, 4, P_WHITE)
    # the legs that carry the hub down into the roof
    for s in (-1, 1):
        d.line([(cx, cy), (cx + s * 26, 126)], fill=STEEL_LO, width=3)
        d.line([(cx - 1, cy), (cx + s * 26 - 1, 126)], fill=WHITE)
    ball(im, cx, cy, 5, 5, P_RED)
    # ---- the block ----------------------------------------------------------------
    BR = (rgb('b8483a'), rgb('d06a55'), rgb('94382e'), rgb('6c2a24'))
    facade_tile(d, 6, 118, 153, 221, pal=BR, tw=8, th=4)
    bar(d, 4, 112, 155, 118, TILE, WHITE, TILE_LO); d.line([(4, 118), (155, 118)], fill=TILE_DK)
    d.rectangle([10, 122, 149, 140], fill=TILE); d.line([(10, 122), (149, 122)], fill=WHITE)
    d.line([(10, 140), (149, 140)], fill=TILE_LO)
    ctext(d, 'WHEEL PLAZA', 80, 124, BR[2], 2)
    d.rectangle([58, 144, 101, 186], fill=GLASS_DK)                # the glass atrium: floors, escalators
    d.rectangle([60, 145, 99, 185], fill=rgb('9fd0f2'))
    for y in (158, 172):
        d.line([(60, y), (99, y)], fill=WHITE); d.line([(60, y + 1), (99, y + 1)], fill=rgb('6f9fd6'))
    for (a, b) in (((64, 157), (82, 146)), ((78, 171), (96, 159)), ((64, 184), (82, 173))):
        d.line([a, b], fill=STEEL_DK, width=2); d.line([(a[0], a[1] - 2), (b[0], b[1] - 2)], fill=YEL)
    for x, y, c in ((90, 157, VERM), (70, 171, INDIGO), (92, 185, TEAL_DK), (68, 157, TIMBER)):
        d.rectangle([x - 1, y - 6, x + 1, y - 1], fill=c); d.rectangle([x - 1, y - 9, x + 1, y - 7], fill=SKIN)
    for x in (70, 80, 90):
        d.line([(x, 145), (x, 185)], fill=WHITE)
    posters = (PINK, TEAL, YEL, INDIGO_HI, VERM_HI, LIME)
    for j, y in enumerate((146, 160, 174)):                         # lit display windows either side
        for i, x in enumerate((12, 28, 44, 106, 122, 138)):
            lit = (i + j) % 4 != 3
            d.rectangle([x, y, x + 11, y + 10], fill=BR[3])
            d.rectangle([x + 1, y + 1, x + 10, y + 9], fill=WARM if lit else GLASS)
            d.line([(x + 1, y + 1), (x + 10, y + 1)], fill=WHITE if lit else GLASS_HI)
            if lit:
                d.rectangle([x + 3, y + 3, x + 8, y + 9], fill=posters[(i * 2 + j) % 6])
                d.rectangle([x + 5, y + 4, x + 6, y + 5], fill=SKIN)
    d.rectangle([2, 188, 157, 193], fill=TILE); d.line([(2, 188), (157, 188)], fill=WHITE)
    d.line([(2, 193), (157, 193)], fill=TILE_DK)
    d.rectangle([8, 194, 151, 221], fill=BR[3])
    for x0, x1 in ((10, 60), (100, 149)):                           # shop windows: mannequins
        d.rectangle([x0, 196, x1, 218], fill=WARM); d.line([(x0, 196), (x1, 196)], fill=WHITE)
        for i, x in enumerate(range(x0 + 8, x1 - 4, 11)):
            walker(d, x, 217, (PINK, TEAL, YEL, VERM, INDIGO_HI)[(i + x0) % 5], (DARK, TILE_LO)[i % 2], TIMBER_LO)
        d.rectangle([x0, 219, x1, 221], fill=TILE_LO)
    glass_door(d, 66, 196, 93, 221, frame=BR[3])
    d.rectangle([4, 222, 155, 223], fill=STONE_LO)
    outline_hull(im, hull)
    return im


# ==============================================================================
# Dotonbori, redrawn
# ==============================================================================
def gyoza_izakaya():
    im, d = canvas(4, 5)                 # 128 x 160
    # upper storey: plaster between dark posts, a row of lattice windows, the name
    d.rectangle([8, 54, 119, 110], fill=PAPER)
    d.rectangle([112, 54, 119, 110], fill=PAPER_LO)
    for x in (8, 44, 81, 117):
        d.rectangle([x, 54, x + 2, 110], fill=TIMBER); d.line([(x + 2, 54), (x + 2, 110)], fill=TIMBER_DK)
    d.rectangle([8, 76, 119, 78], fill=TIMBER); d.line([(8, 78), (119, 78)], fill=TIMBER_DK)
    for x in (13, 50, 87):
        lit_window(d, x, 58, x + 27, 73, frame=TIMBER_DK, bars=4)
    pent_roof(d, 8, 44, 119, 9)
    d.rectangle([20, 39, 107, 43], fill=KAWARA_LO); d.line([(20, 39), (107, 39)], fill=KAWARA_HI)
    # the plate on the roof and its three dumplings, a fourth lifted in giant chopsticks
    ball(im, 60, 36, 46, 11, (WHITE, rgb('eef2f8'), rgb('c3cde0'), rgb('8ea0c4')))
    d.arc([18, 27, 102, 45], 0, 360, fill=INDIGO_HI)
    d.arc([26, 30, 94, 43], 200, 340, fill=rgb('c3cde0'))
    gyoza(im, d, 36, 28, 13, 9); gyoza(im, d, 84, 28, 13, 9); gyoza(im, d, 60, 31, 14, 10)
    d.line([(127, 3), (90, 14)], fill=VERM_DK, width=2); d.line([(127, 2), (90, 13)], fill=VERM)
    d.line([(127, 12), (92, 20)], fill=VERM_DK, width=2); d.line([(127, 11), (92, 19)], fill=VERM)
    gyoza(im, d, 88, 14, 11, 8)
    d.line([(98, 10), (88, 13)], fill=VERM); d.line([(100, 17), (90, 19)], fill=VERM)
    steam(im, 40, 14, 3); steam(im, 62, 16, 2, 1)
    # the name board in solid letters, lanterns
    board(d, 28, 82, 99, 104, VERM, rim=VERM_DK, lamp=False, hi=VERM_HI)
    ctext(d, 'GYOZA', 64, 86, WHITE, 2)
    d.line([(31, 102), (96, 102)], fill=YEL)
    chochin(d, 12, 82, 13, 22, WHITE, WHITE, PAPER_LO, mark=VERM)
    chochin(d, 103, 82, 13, 22, WHITE, WHITE, PAPER_LO, mark=VERM)
    # the front: pent roof, lattice, noren over the door
    d.rectangle([8, 118, 119, 157], fill=TIMBER)
    d.rectangle([112, 118, 119, 157], fill=TIMBER_LO)
    pent_roof(d, 6, 110, 121, 8)
    doorway(d, 34, 123, 61, 157, INDIGO, INDIGO_LO, mark=WHITE)
    lit_window(d, 68, 126, 114, 148, frame=TIMBER_DK, bars=4)
    for x in (76, 88, 101):                                                     # bottles on the sill
        d.rectangle([x, 140, x + 2, 147], fill=(TEAL_DK, rgb('7a4a1c'), TEAL_LO)[x % 3])
        d.point((x + 1, 139), fill=WHITE)
    d.rectangle([68, 149, 114, 157], fill=TIMBER_LO)
    d.rectangle([12, 128, 29, 150], fill=rgb('1c1a22'))                          # a chalk menu
    for y in range(132, 148, 4):
        d.line([(15, y), (26 - (y % 3), y)], fill=PAPER)
    d.rectangle([14, 144, 18, 147], fill=VERM)
    d.rectangle([6, 158, 121, 159], fill=STONE_LO)
    outline(im)
    return im


def shoe(d, a, t, side):
    """A spiked running shoe from the ankle a to the toe t; the sole and its
    spikes are on `side` (+1 / -1) of that line."""
    tube(d, [a, t], 6.5, 4.5, (WHITE, YEL_HI, YEL, YEL_LO))
    L_ = math.hypot(t[0] - a[0], t[1] - a[1]) or 1
    nx, ny = -(t[1] - a[1]) / L_ * side, (t[0] - a[0]) / L_ * side
    d.line([(a[0] + nx * 3, a[1] + ny * 3), (t[0] + nx * 2.5, t[1] + ny * 2.5)], fill=WHITE)
    for f in (0.35, 0.65, 0.95):
        x, y = a[0] + (t[0] - a[0]) * f + nx * 5, a[1] + (t[1] - a[1]) * f + ny * 5
        d.point((round(x), round(y)), fill=CYAN)
    d.line([(a[0] + (t[0] - a[0]) * 0.4, a[1] + (t[1] - a[1]) * 0.4),
            (a[0] + (t[0] - a[0]) * 0.7 - nx * 2, a[1] + (t[1] - a[1]) * 0.7 - ny * 2)], fill=VERM)   # a stripe


def hand(im, d, x, y, dx, dy):
    ball(im, x, y, 3.5, 3.5, P_SKIN)
    d.line([(x + dx, y + dy), (x + dx * 3, y + dy * 3)], fill=SKIN)
    d.line([(x + dx - dy, y + dy + dx), (x + dx * 3 - dy, y + dy * 3 + dx)], fill=SKIN_LO)


def hurdler(im, d, ox, oy):
    """The billboard's athlete: an invented hurdler, side on, mid-leap, built of
    jointed limbs (thigh, shin, upper arm, forearm), hands and spiked shoes."""
    P = lambda x, y: (ox + x, oy + y)                                             # noqa: E731
    # the far arm, swung back and bent
    tube(d, [P(20, -23), P(6, -33)], 7, 5.5, P_SKIN); tube(d, [P(6, -33), P(-7, -25)], 5.5, 4, P_SKIN)
    ball(im, ox + 6, oy - 33, 3, 3, (SKIN, SKIN, SKIN_LO, SKIN_LO))
    hand(im, d, ox - 9, oy - 24, -1, 0)
    # the trailing leg: thigh back and down, the shin folded flat behind
    tube(d, [P(0, 0), P(-17, 12)], 11, 8, P_SKIN); tube(d, [P(-17, 12), P(-39, 4)], 8, 5, P_SKIN)
    ball(im, ox - 17, oy + 12, 4.5, 4.5, P_SKIN)
    shoe(d, P(-39, 4), P(-51, -2), -1)
    # the trunk, leaning into the leap
    tube(d, [P(2, -2), P(22, -24)], 16, 14, P_TEAL)
    d.rectangle([ox + 7, oy - 18, ox + 16, oy - 9], fill=WHITE)
    text(d, '1', ox + 9, oy - 17, INK, 1)
    d.line([(ox + 15, oy - 28), (ox + 26, oy - 19)], fill=YEL_HI)                 # the singlet's trim
    # the lead leg, out straight over the bar
    tube(d, [P(2, 0), P(27, -6)], 11, 8, P_SKIN); tube(d, [P(27, -6), P(51, -2)], 8, 5, P_SKIN)
    ball(im, ox + 27, oy - 6, 4.5, 4.5, P_SKIN)
    shoe(d, P(51, -2), P(57, -13), 1)
    ball(im, ox + 2, oy - 1, 11, 8, P_GOLD)                                       # shorts
    d.line([(ox - 6, oy + 4), (ox + 10, oy + 5)], fill=WHITE)
    # the near arm, reaching for the toes
    tube(d, [P(22, -22), P(36, -16)], 7, 5.5, P_SKIN); tube(d, [P(36, -16), P(50, -19)], 5.5, 4, P_SKIN)
    ball(im, ox + 36, oy - 16, 3, 3, P_SKIN)
    hand(im, d, ox + 52, oy - 19, 1, 0)
    # head: hair streaming back, a pink headband
    d.rectangle([ox + 24, oy - 30, ox + 28, oy - 26], fill=SKIN_LO)
    ball(im, ox + 31, oy - 36, 8, 8, P_SKIN)
    d.pieslice([ox + 22, oy - 45, ox + 39, oy - 28], 160, 320, fill=INK)
    d.polygon([(ox + 24, oy - 40), (ox + 14, oy - 42), (ox + 22, oy - 35)], fill=INK)
    d.line([(ox + 23, oy - 37), (ox + 38, oy - 40)], fill=PINK, width=2)
    d.polygon([(ox + 23, oy - 37), (ox + 15, oy - 36), (ox + 17, oy - 32)], fill=PINK)
    d.rectangle([ox + 35, oy - 36, ox + 36, oy - 35], fill=INK)
    d.line([(ox + 35, oy - 31), (ox + 38, oy - 31)], fill=VERM_LO)


def sprinter_billboard():
    """The canal's great neon board, six cells wide, on a steel gantry over a
    low black-tiled diner."""
    im, d = canvas(6, 6)                 # 192 x 192
    # ---- the board ----------------------------------------------------------------
    d.rectangle([6, 3, 185, 123], fill=INK)
    for y in range(6, 121):                                       # dusk: violet up top, hot pink low
        t = (y - 6) / 114.0
        c = VIOLET_DK if t < 0.28 else (VIOLET_LO if t < 0.5 else (VIOLET if t < 0.68 else PINK_DK))
        d.line([(9, y), (182, y)], fill=c)
    for x in range(9, 183):                                       # the town's roofs along the horizon
        hgt = 4 + h3(x // 7, 3, 9) % 11
        d.line([(x, 84 - hgt), (x, 84)], fill=VIOLET_DK)
        if x % 7 in (2, 4) and h3(x, hgt, 1) % 3 == 0 and hgt > 5:
            d.point((x, 84 - hgt + 2 + h3(x, 2, 2) % 3), fill=WARM)
    for k in range(6):                                            # the track's lanes sweeping under
        for x in range(9, 183):
            y = 87 + k * 7 + round(((x - 96) / 88.0) ** 2 * (3 + k * 2))
            if y < 121:
                d.point((x, y), fill=PINK_HI if k % 2 == 0 else PINK)
    for i, (x, y, w) in enumerate(((14, 40, 30), (20, 50, 40), (12, 60, 26), (24, 70, 20), (16, 30, 16), (30, 78, 14))):
        d.line([(x, y), (x + w, y)], fill=CYAN if i % 2 == 0 else TEAL_HI)     # speed lines
        d.line([(x + 4, y + 1), (x + w - 6, y + 1)], fill=TEAL_LO)
    for x, y in ((24, 14), (104, 12), (150, 20), (172, 40), (128, 26), (166, 14), (90, 20)):
        d.point((x, y), fill=WHITE)
    star(d, 160, 26, 6, YEL_HI)
    # the hurdle, under him
    d.rectangle([62, 82, 118, 86], fill=WHITE)
    for x in range(62, 118, 10):
        d.rectangle([x, 82, x + 4, 86], fill=VERM)
    for x in (65, 115):
        d.rectangle([x, 87, x + 1, 108], fill=WHITE); d.line([(x - 5, 108), (x + 6, 108)], fill=WHITE)
        d.line([(x - 5, 109), (x + 6, 109)], fill=PINK_DK)
    hurdler(im, d, 86, 66)
    text(d, 'NANIWA', 16, 11, VIOLET, 2); text(d, 'NANIWA', 15, 10, CYAN, 2)
    x = 139 - text_w('DASH!', 3) // 2
    text(d, 'DASH!', x + 2, 99, VERM_DK, 3); text(d, 'DASH!', x + 1, 98, VERM, 3); text(d, 'DASH!', x, 97, YEL_HI, 3)
    bulbs(d, 6, 3, 185, 123, 4)
    # ---- the gantry it stands on ----------------------------------------------------
    for x0 in (14, 92, 170):
        bar(d, x0, 124, x0 + 7, 141, STEEL, STEEL_HI, STEEL_DK)
    d.rectangle([10, 124, 181, 126], fill=STEEL_LO); d.line([(10, 124), (181, 124)], fill=STEEL_HI)
    d.rectangle([10, 136, 181, 138], fill=STEEL_LO); d.line([(10, 136), (181, 136)], fill=STEEL_HI)
    for x in range(22, 170, 12):
        if not 86 < x < 100:
            d.line([(x, 127), (x + 6, 135)], fill=STEEL); d.line([(x + 6, 135), (x + 12, 127)], fill=STEEL_LO)
    for x in (40, 66, 124, 150):                                  # floodlights thrown up at the board
        d.rectangle([x, 120, x + 5, 123], fill=STEEL_DK); d.line([(x + 1, 119), (x + 4, 119)], fill=WARM)
    # ---- the diner at its foot: black tile, a lit band of windows ------------------
    BLK = (rgb('2f3440'), rgb('4a5062'), rgb('23262f'), rgb('15171d'))
    facade_tile(d, 6, 142, 185, 189, pal=BLK, tw=6, th=4)
    bar(d, 4, 139, 187, 143, TEAL, TEAL_HI, TEAL_DK)
    d.rectangle([10, 146, 181, 156], fill=rgb('15171d'))
    ctext(d, 'NANIWA DINER', 96, 148, WARM, 1)
    star(d, 46, 151, 3, PINK_HI); star(d, 146, 151, 3, PINK_HI)
    for x in range(12, 181, 6):
        if not 52 < x < 140:
            d.point((x, 151), fill=CYAN if (x // 6) % 2 else WARM)
    for x0, x1 in ((10, 60), (100, 181)):
        d.rectangle([x0, 160, x1, 184], fill=TEAL_DK)
        d.rectangle([x0 + 1, 161, x1 - 1, 183], fill=WARM); d.line([(x0 + 1, 161), (x1 - 1, 161)], fill=WHITE)
        for i, x in enumerate(range(x0 + 9, x1 - 6, 16)):          # diners in booths
            person(d, x, 166, (VERM, INDIGO, TEAL_DK, PINK_LO, TIMBER)[(i + x0) % 5],
                   hair=(INK, TIMBER_LO, rgb('8a8078'))[i % 3])
            d.rectangle([x + 5, 177, x + 10, 178], fill=WHITE)
        d.rectangle([x0 + 1, 179, x1 - 1, 183], fill=VERM_LO); d.line([(x0 + 1, 179), (x1 - 1, 179)], fill=VERM_HI)
        for x in range(x0 + 16, x1, 16):
            d.line([(x, 161), (x, 183)], fill=TEAL_DK)
    glass_door(d, 66, 160, 93, 189, frame=TEAL_DK)
    d.rectangle([4, 190, 187, 191], fill=STONE_LO)
    outline(im)
    return im


def scales(d, pts, w0, w1, pal):
    """Rows of scales over a tube drawn along pts."""
    j = 0
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)) or 1
    run = 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L_ = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L_, (x1 - x0) / L_
        for k in range(int(L_ // 4)):
            t = k * 4 / L_
            w = (w0 + (w1 - w0) * (run + L_ * t) / total) / 2 - 2
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for f in ((-0.55, 0.15, 0.8) if j % 2 else (-0.85, -0.2, 0.5)):
                if w < 2.5 and f != 0.15 and f != -0.2:
                    continue
                sx, sy = x + nx * w * f, y + ny * w * f
                d.arc([sx - 2, sy - 2, sx + 2, sy + 2], 10, 170, fill=pal[2])
                d.point((round(sx), round(sy) - 1), fill=pal[0])
            j += 1
        run += L_


def dragon_head(im, d, hx, hy, k=1.2):
    """The dragon's head, three-quarters on: horns, a long snout, jaws wide."""
    S = lambda v: int(round(v * k))                                               # noqa: E731
    for s in (1, 2, 3):                                           # the mane, flaring behind the head
        d.polygon([(hx + S(8 + s * 3), hy - S(10)), (hx + S(16 + s * 6), hy - S(22 - s * 6)),
                   (hx + S(12 + s * 3), hy - S(2 - s * 4))], fill=PINK if s % 2 else PINK_LO)
    for s in (-1, 1):                                             # horns
        tube(d, [(hx + S(s * 7 - 2), hy - S(9)), (hx + S(s * 12 - 2), hy - S(21)), (hx + S(s * 9 - 2), hy - S(28))],
             4 * k, 1.5 * k, P_HORN)
    d.polygon([(hx - S(15), hy - S(2)), (hx - S(24), hy - S(9)), (hx - S(16), hy - S(10))], fill=PINK)      # cheek fins
    d.polygon([(hx + S(13), hy - S(4)), (hx + S(22), hy - S(12)), (hx + S(12), hy - S(10))], fill=PINK_LO)
    ball(im, hx, hy, S(16), S(13), P_DRAG)
    for dx, dy in ((-8, -8), (-2, -10), (4, -9), (-11, -3), (9, -5)):                                        # brow scales
        d.arc([hx + S(dx) - 2, hy + S(dy) - 2, hx + S(dx) + 2, hy + S(dy) + 2], 10, 170, fill=DRAG_LO)
    d.polygon([(hx - S(6), hy + S(8)), (hx + S(20), hy + S(10)), (hx + S(16), hy + S(25)), (hx - S(2), hy + S(20))],
              fill=VERM_DK)                                                                                  # the open mouth
    d.polygon([(hx - S(3), hy + S(10)), (hx + S(17), hy + S(12)), (hx + S(14), hy + S(22)), (hx, hy + S(18))], fill=VERM)
    d.polygon([(hx + S(3), hy + S(15)), (hx + S(12), hy + S(16)), (hx + S(9), hy + S(21))], fill=PINK_HI)   # tongue
    ball(im, hx + S(9), hy + S(23), S(9), S(4), P_DRAG)                                                     # the lower jaw
    ball(im, hx + S(8), hy + S(7), S(14), S(7), P_DRAG)                                                     # the snout
    for x in (0, 6, 12, 17):
        d.polygon([(hx + S(x) - 1, hy + S(13)), (hx + S(x) + 1, hy + S(13)), (hx + S(x), hy + S(17))], fill=WHITE)
    for x in (4, 10, 15):
        d.polygon([(hx + S(x) - 1, hy + S(21)), (hx + S(x) + 1, hy + S(21)), (hx + S(x), hy + S(18))], fill=WHITE)
    d.rectangle([hx + S(15), hy + S(3), hx + S(15) + 1, hy + S(3) + 1], fill=INK)
    d.rectangle([hx + S(9), hy + S(2), hx + S(9) + 1, hy + S(2) + 1], fill=INK)
    for ex, r in ((hx - S(5), S(4)), (hx + S(6), S(3))):                                                     # eyes under a heavy brow
        d.ellipse([ex - r, hy - S(7), ex + r, hy - S(7) + r * 2 - 1], fill=YEL_HI)
        d.line([(ex, hy - S(7) + 1), (ex, hy - S(7) + r * 2 - 2)], fill=INK)
        d.line([(ex - r - 1, hy - S(9)), (ex + r + 1, hy - S(7))], fill=DRAG_DK, width=2)
    d.line([(hx + S(19), hy + S(6)), (hx + S(25), hy + S(1)), (hx + S(27), hy + S(8))], fill=YEL_HI)        # whiskers
    d.line([(hx - S(2), hy + S(9)), (hx - S(10), hy + S(14)), (hx - S(9), hy + S(22))], fill=YEL_HI)
    d.polygon([(hx + S(2), hy + S(26)), (hx + S(8), hy + S(33)), (hx + S(12), hy + S(26))], fill=PINK)      # a beard


def claw(d, a, b):
    """A forearm from a to the paw at b, three talons hooked over what it grips."""
    tube(d, [a, b], 9, 8, P_DRAG)
    for k in (-3, 0, 3):
        d.line([(b[0] + k, b[1] + 2), (b[0] + k, b[1] + 7)], fill=WHITE)
        d.point((b[0] + k + 1, b[1] + 7), fill=PAPER_LO)


def dragon_ramen():
    """A ramen shop whose dragon has come through the sign: the head and both
    claws out of a hole smashed in the board, the tail out through the roof at
    the far end."""
    im, d = canvas(4, 5)                 # 128 x 160
    d.rectangle([6, 46, 121, 157], fill=VERM_LO)                  # red lacquer boards, gold trim
    for y in range(50, 108, 5):
        d.line([(6, y), (121, y)], fill=VERM_DK)
    d.line([(6, 46), (6, 157)], fill=VERM_HI); d.rectangle([116, 46, 121, 157], fill=VERM_DK)
    bar(d, 4, 42, 123, 46, YEL_LO, YEL_HI, YEL_DK)
    board(d, 4, 52, 123, 90, YEL, rim=VERM_DK, hi=YEL_HI)
    kana(d, ['ra', 'bar', 'me', 'n'], 8, 60, VERM, 2)
    ctext(d, 'RAMEN', 38, 79, VERM_DK, 1)
    for i, x in enumerate(range(10, 66, 11)):
        chochin(d, x, 93, 8, 10, VERM, VERM_HI, VERM_DK, mark=YEL_HI if i % 2 else None)
    d.rectangle([4, 105, 123, 110], fill=VERM); d.line([(4, 105), (123, 105)], fill=VERM_HI)
    d.line([(4, 110), (123, 110)], fill=YEL); d.line([(4, 111), (123, 111)], fill=VERM_DK)
    # ---- the ground floor: a ticket machine, the door, the kitchen window -----------
    d.rectangle([8, 112, 119, 157], fill=TIMBER); d.rectangle([114, 112, 119, 157], fill=TIMBER_LO)
    d.rectangle([11, 120, 29, 154], fill=STEEL_LO); d.line([(11, 120), (11, 154)], fill=STEEL_HI)   # meal tickets
    d.rectangle([13, 122, 27, 130], fill=WARM)
    for j, y in enumerate(range(133, 146, 4)):
        for i, x in enumerate(range(13, 27, 4)):
            d.rectangle([x, y, x + 2, y + 2], fill=(VERM, YEL, WHITE, LIME)[(i + j) % 4])
    d.rectangle([14, 148, 26, 151], fill=INK)
    doorway(d, 34, 116, 61, 157, VERM, VERM_DK, mark=YEL_HI)
    d.rectangle([66, 116, 117, 142], fill=TIMBER_DK)
    d.rectangle([67, 117, 116, 141], fill=rgb('3a2a2c'))
    d.rectangle([67, 117, 116, 121], fill=WARM)
    person(d, 80, 121, WHITE, cap=WHITE)
    d.rectangle([94, 124, 110, 135], fill=STEEL_LO); d.line([(94, 124), (110, 124)], fill=STEEL_HI)   # the stock pot
    d.rectangle([96, 122, 108, 123], fill=STEEL)
    d.rectangle([66, 136, 117, 141], fill=WOOD); d.line([(66, 136), (117, 136)], fill=rgb('d2a58c'))
    for x in (74, 88):                                                           # bowls on the pass
        d.rectangle([x - 5, 132, x + 5, 135], fill=WHITE); d.line([(x - 4, 135), (x + 4, 135)], fill=VERM)
        d.line([(x - 4, 131), (x + 4, 131)], fill=rgb('e0b060'))
    d.rectangle([66, 143, 117, 157], fill=TIMBER_LO)
    for x in range(70, 116, 6):
        d.line([(x, 144), (x, 157)], fill=TIMBER_DK)
    d.rectangle([4, 158, 123, 159], fill=STONE_LO)
    # ---- the tail, out through the roof at the west end ------------------------------
    burst(d, 20, 46, 16, 10, 8)
    for sx, sy, tx, ty in ((2, 38, 8, 30), (6, 54, 0, 50), (36, 52, 41, 57)):    # flying splinters
        d.line([(sx, sy), (tx, ty)], fill=VERM_LO, width=2); d.point((tx, ty), fill=YEL)
    tail = [(22, 49), (15, 36), (17, 23), (27, 13), (36, 5)]
    tube(d, [(x + 4, y + 1) for x, y in tail], 15, 3, P_GOLD)                    # the belly
    tube(d, tail, 18, 5, P_DRAG)
    scales(d, tail, 18, 5, P_DRAG)
    for (x, y), (dx, dy) in (((10, 41), (-7, -3)), ((9, 29), (-7, -4)), ((16, 17), (-6, -6))):   # fins down its back
        d.polygon([(x, y - 3), (x + dx, y + dy), (x + 1, y + 3)], fill=PINK); d.point((x + dx + 1, y + dy + 1), fill=PINK_HI)
    d.polygon([(35, 8), (30, 0), (36, 3), (41, 0), (39, 9)], fill=PINK)          # the tuft
    d.line([(35, 7), (32, 2)], fill=PINK_HI)
    # ---- a coil of its body, up through the roof and down again -----------------------
    burst(d, 47, 45, 11, 7, 7); burst(d, 71, 45, 11, 7, 7, turn=20)
    hump = [(47, 48), (48, 33), (59, 24), (70, 33), (71, 48)]
    tube(d, [(x, y + 4) for x, y in hump], 14, 14, P_GOLD)
    tube(d, hump, 17, 17, P_DRAG)
    scales(d, hump, 17, 17, P_DRAG)
    for x, y, dx, dy in ((45, 30, -4, -6), (59, 17, 0, -8), (73, 30, 4, -6)):
        d.polygon([(x - 3, y + 2), (x + dx, y + dy), (x + 3, y + 2)], fill=PINK); d.point((x + dx, y + dy + 2), fill=PINK_HI)
    # ---- the head and claws, out through the board ----------------------------------
    burst(d, 98, 66, 27, 19, 10, turn=3)
    for sx, sy, tx, ty in ((124, 88, 127, 94), (72, 86, 66, 92), (122, 48, 127, 42)):
        d.line([(sx, sy), (tx, ty)], fill=YEL_LO, width=2); d.point((tx, ty), fill=YEL_HI)
    neck = [(114, 50), (106, 56), (98, 60)]
    tube(d, neck, 24, 24, P_DRAG); scales(d, neck, 24, 24, P_DRAG)
    claw(d, (84, 74), (77, 86)); claw(d, (114, 76), (119, 88))
    dragon_head(im, d, 95, 62, 1.2)
    steam(im, 102, 120, 3); steam(im, 76, 128, 2, 1)
    outline(im)
    return im


def okonomiyaki_front():
    """Charred boards and copper: an okonomiyaki house under a giant pancake on
    an iron plate and two steel turners."""
    im, d = canvas(3, 4)                 # 96 x 128
    CHAR, CHAR_HI, CHAR_LO = rgb('3d3539'), rgb('554b50'), rgb('2a2429')
    COP, COP_HI, COP_LO, COP_DK = rgb('c0703c'), rgb('e8a060'), rgb('8f4e2c'), rgb('643624')
    GRN, GRN_LO = rgb('2f7a55'), rgb('1f5a40')
    d.rectangle([5, 44, 90, 125], fill=CHAR)
    for x in range(5, 90, 6):
        d.line([(x, 44), (x, 125)], fill=CHAR_LO); d.line([(x + 1, 44), (x + 1, 125)], fill=CHAR_HI)
    d.rectangle([86, 44, 90, 125], fill=CHAR_LO)
    bar(d, 3, 40, 92, 44, COP, COP_HI, COP_DK); d.line([(3, 40), (92, 40)], fill=COP_HI)
    for x in range(7, 90, 8):
        d.point((x, 42), fill=COP_DK)
    for x in (12, 13, 40, 70, 71, 84):
        d.point((x, 43), fill=TEAL_HI)                                            # verdigris
    # ---- the plate, the pancake, the two turners -----------------------------------
    for s in (0, 1):                                                              # turners, crossed behind the plate
        M = (lambda x: 95 - x) if s else (lambda x: x)                           # noqa: E731
        d.line([(M(9), 3), (M(20), 22)], fill=WOOD_LO, width=4)
        d.line([(M(8), 3), (M(19), 22)], fill=WOOD)
        blade_ = [(M(15), 18), (M(27), 12), (M(40), 30), (M(24), 38)]
        d.polygon(blade_, fill=STEEL)
        d.line([blade_[0], blade_[1]], fill=WHITE); d.line([blade_[2], blade_[3]], fill=STEEL_DK)
        d.line([(M(22), 20), (M(32), 32)], fill=STEEL_HI)
    ball(im, 48, 30, 42, 11, P_IRON)
    d.arc([8, 20, 88, 40], 0, 360, fill=rgb('23283a'))
    PAN = (rgb('f0c070'), rgb('d9973f'), rgb('a86a28'), rgb('7a4a1c'))
    ball(im, 48, 25, 29, 10, PAN)
    ball(im, 48, 23, 23, 7, (rgb('8a4a24'), rgb('6a3418'), rgb('522612'), rgb('40200f')))   # the sauce
    for k in range(-4, 5):                                                        # mayonnaise, in a lattice
        x = 48 + k * 5
        d.line([(x - 4, 28), (x + 4, 18)], fill=PAPER)
    for x, y in ((34, 22), (44, 19), (53, 26), (62, 22), (40, 26), (58, 19), (48, 23)):
        d.point((x, y), fill=LIME); d.point((x + 2, y + 1), fill=rgb('3f7f48'))
    for x, y in ((38, 20), (50, 20), (60, 25), (45, 27)):                         # bonito flakes
        d.line([(x, y), (x + 2, y - 1)], fill=PINK_HI)
    steam(im, 36, 12, 3); steam(im, 56, 10, 3, 2)
    # ---- the name, wooden menu plaques under it -------------------------------------
    d.rectangle([5, 48, 90, 66], fill=COP_DK); d.rectangle([6, 49, 89, 65], fill=GRN_LO)
    d.line([(6, 49), (89, 49)], fill=GRN)
    ctext(d, 'OKONOMI', 48, 51, PAPER, 2)
    for i, x in enumerate(range(9, 84, 11)):
        d.line([(x + 3, 68), (x + 3, 70)], fill=INK)
        d.rectangle([x, 70, x + 7, 84], fill=DOUGH if i != 3 else VERM); d.line([(x, 70), (x, 84)], fill=DOUGH_HI if i != 3 else VERM_HI)
        d.line([(x + 7, 70), (x + 7, 84)], fill=DOUGH_LO if i != 3 else VERM_DK)
        for y in (73, 76, 79):
            d.line([(x + 3, y), (x + 4, y + 1)], fill=INK if i != 3 else WHITE)
        d.point((x + 2, 82), fill=VERM if i != 3 else WHITE)
    for y in range(6):                                                            # a copper hood
        d.line([(3 - y // 2, 87 + y), (92 + y // 2, 87 + y)], fill=COP if y < 4 else COP_LO)
    d.line([(3, 87), (92, 87)], fill=COP_HI); d.line([(1, 93), (94, 93)], fill=COP_DK)
    for x in range(6, 92, 10):
        d.line([(x, 88), (x, 92)], fill=COP_LO)
    # ---- the front -----------------------------------------------------------------
    d.rectangle([8, 97, 30, 117], fill=CHAR_LO)                                   # the griddle window: a cook, two pancakes
    d.rectangle([9, 98, 29, 116], fill=WARM)
    person(d, 19, 99, WHITE, cap=GRN)
    d.rectangle([9, 111, 29, 116], fill=rgb('30323e')); d.line([(9, 111), (29, 111)], fill=STEEL_LO)
    for x in (11, 21):
        d.rectangle([x, 112, x + 6, 114], fill=PAN[1]); d.line([(x + 1, 112), (x + 5, 112)], fill=rgb('6a3418'))
    d.rectangle([8, 118, 30, 125], fill=CHAR_LO)
    doorway(d, 34, 96, 61, 125, GRN, GRN_LO, mark=PAPER, frame=CHAR_LO)
    d.rectangle([65, 97, 87, 117], fill=CHAR_LO)                                  # diners at the iron counter
    d.rectangle([66, 98, 86, 116], fill=WARM)
    person(d, 72, 101, INDIGO); person(d, 81, 102, VERM_LO, hair=TIMBER_LO)
    d.rectangle([66, 113, 86, 116], fill=rgb('30323e'))
    d.rectangle([65, 118, 87, 125], fill=CHAR_LO)
    d.rectangle([3, 126, 92, 127], fill=STONE_LO)
    outline(im)
    return im


def boat_pier():
    """The river cruise's booth on the quay: a wheelhouse of a hut with a yellow
    barrel roof, a porthole and a wave round its skirt, and the gate to the
    gangway under a line of pennants."""
    im, d = canvas(3, 3)                 # 96 x 96
    d.rectangle([5, 40, 61, 93], fill=TILE)
    d.line([(5, 40), (5, 93)], fill=WHITE); d.rectangle([57, 40, 61, 93], fill=TILE_LO)
    d.rectangle([5, 76, 61, 93], fill=INDIGO); d.rectangle([57, 76, 61, 93], fill=INDIGO_LO)
    for x in range(6, 61):
        y = 78 + round(1.6 * math.sin(x / 2.6))
        d.point((x, y), fill=WHITE); d.point((x, y + 6), fill=INDIGO_HI)
    for x in range(1, 66):                                        # the barrel roof
        t = ((x - 33) / 33.0) ** 2
        y0 = 25 + round(12 * t)
        d.line([(x, y0), (x, 38)], fill=YEL_HI if x < 14 else (YEL if x < 46 else YEL_LO))
        if x % 9 == 4:
            d.line([(x, y0 + 1), (x, 38)], fill=YEL_LO if x < 46 else YEL_DK)
        d.point((x, y0), fill=WHITE if x < 46 else YEL_HI)
    d.rectangle([1, 38, 65, 40], fill=INDIGO); d.line([(1, 38), (65, 38)], fill=INDIGO_HI)
    board(d, 9, 3, 59, 22, INDIGO, rim=INK, hi=INDIGO_HI)
    ctext(d, 'BOAT', 34, 6, WHITE, 2)
    d.line([(18, 23), (18, 27)], fill=STEEL_DK); d.line([(50, 23), (50, 27)], fill=STEEL_DK)
    d.rectangle([9, 45, 37, 67], fill=INDIGO_LO)                  # the ticket window
    d.rectangle([10, 46, 36, 66], fill=WARM); d.line([(10, 46), (36, 46)], fill=WHITE)
    person(d, 23, 51, INDIGO, cap=WHITE)
    d.rectangle([8, 68, 38, 70], fill=STEEL_HI); d.line([(8, 70), (38, 70)], fill=STEEL_LO)
    ball(im, 49, 55, 8, 8, (STEEL_HI, YEL, YEL_LO, YEL_DK))       # a brass porthole
    ball(im, 49, 55, 5, 5, (WHITE, rgb('9fd0f2'), rgb('6f9fd6'), rgb('4b6396')))
    d.ellipse([43, 77, 55, 89], fill=VERM); d.ellipse([46, 80, 52, 86], fill=INDIGO)       # a lifebuoy
    d.rectangle([48, 77, 50, 79], fill=WHITE); d.rectangle([48, 87, 50, 89], fill=WHITE)
    d.rectangle([43, 82, 45, 84], fill=WHITE); d.rectangle([53, 82, 55, 84], fill=WHITE)
    d.rectangle([3, 94, 63, 95], fill=STONE_LO)
    # the gate: striped posts, a way-down sign, pennants from the booth
    for x in (69, 92):
        d.rectangle([x - 1, 56, x + 1, 94], fill=YEL)
        for y in range(58, 94, 8):
            d.rectangle([x - 1, y, x + 1, y + 3], fill=INK)
        ball(im, x, 53, 3, 3, (WHITE, WARM, LIT, AMBER))
        d.rectangle([x - 3, 93, x + 3, 95], fill=STONE_DK)
    d.rectangle([73, 60, 88, 72], fill=TEAL_DK); d.rectangle([74, 61, 87, 71], fill=TEAL)
    d.line([(80, 63), (80, 69)], fill=WHITE); d.line([(81, 63), (81, 69)], fill=WHITE)
    d.line([(77, 66), (80, 69)], fill=WHITE); d.line([(84, 66), (81, 69)], fill=WHITE)
    d.line([(69, 60), (73, 62)], fill=STEEL_DK); d.line([(92, 60), (88, 62)], fill=STEEL_DK)
    for i, x in enumerate(range(61, 93, 6)):
        t = (x - 61) / 31.0
        y = round(12 + 38 * t - 8 * math.sin(math.pi * t))
        d.point((x, y), fill=INK); d.point((x + 3, y + 3), fill=INK)
        d.polygon([(x, y + 1), (x + 4, y + 3), (x + 2, y + 8)], fill=(VERM, YEL, TEAL, PINK, WHITE, VERM)[i])
    outline(im)
    return im


DEEP = rgb('2f4585')                     # the canal in shade
RIP = rgb('8fb0ee')                      # a ripple catching the light


def boat_landing():
    """What the pier's gate leads down to, flat on the water: the gangway
    crossing the quay wall and a floating landing stage."""
    im, d = canvas(3, 2)                 # 96 x 64
    # the gangway (column 2): bright at the quay, in the wall's shade lower down
    for y in range(0, 37):
        t = y / 36.0
        x0, x1 = 68 + round(2 * t), 91 - round(2 * t)
        c = (STEEL_HI, STEEL, STEEL_LO)[0 if y < 8 else (1 if y < 22 else 2)]
        d.line([(x0, y), (x1, y)], fill=c)
        if y % 4 == 3:
            d.line([(x0 + 2, y), (x1 - 2, y)], fill=STEEL_DK)      # cleats underfoot
        d.point((x0, y), fill=YEL); d.point((x1, y), fill=YEL_LO)
        d.point((x0 - 1, y), fill=STEEL_DK); d.point((x1 + 1, y), fill=STEEL_DK)
    for y in (2, 13, 24, 34):                                      # the handrail's posts, and its shadow on the water
        d.rectangle([66, y, 67, y + 2], fill=WHITE); d.rectangle([92, y, 93, y + 2], fill=STEEL_HI)
    d.polygon([(93, 20), (95, 22), (95, 36), (93, 36)], fill=DEEP)
    # the landing stage
    d.rectangle([2, 36, 93, 55], fill=rgb('9a8f84'))
    for x in range(2, 94, 7):
        d.line([(x, 37), (x, 55)], fill=rgb('7d7268'))
    d.line([(2, 36), (93, 36)], fill=rgb('c4b9ad'))
    for x in range(2, 94, 8):
        d.rectangle([x, 53, x + 3, 54], fill=YEL); d.rectangle([x + 4, 53, x + 7, 54], fill=INK)
    d.rectangle([2, 56, 93, 59], fill=rgb('4a4440')); d.line([(2, 56), (93, 56)], fill=rgb('6a625c'))
    for x in (12, 38, 64, 86):                                     # tyre fenders
        d.ellipse([x - 4, 54, x + 4, 62], fill=rgb('23262f')); d.ellipse([x - 1, 57, x + 1, 59], fill=rgb('4a4440'))
        d.point((x - 2, 55), fill=STEEL_LO)
    for x in (9, 55):                                              # bollards
        ball(im, x, 42, 4, 3, P_IRON); d.rectangle([x - 2, 43, x + 2, 47], fill=P_IRON[2])
        d.line([(x - 2, 43), (x - 2, 47)], fill=P_IRON[0])
    d.line([(9, 44), (20, 50), (55, 44)], fill=DOUGH_LO)           # a coil of line
    d.line([(0, 61), (95, 61)], fill=DEEP); d.line([(4, 62), (93, 62)], fill=DEEP)
    for x in (6, 24, 46, 72, 90):
        d.line([(x - 3, 63), (x + 3, 63)], fill=RIP)
    outline(im)
    return im


def river_boat():
    """The sightseeing boat, moored: a long low yellow hull, an open deck of
    benches under a flat canopy hung with lanterns, the wheel at the stern."""
    im, d = canvas(4, 2)                 # 128 x 64
    # hull: sheer line rising to the bow (east)
    for x in range(4, 125):
        t = (x - 4) / 120.0
        top = 40 - round(5 * t ** 3) + (2 if x < 8 else 0)
        bot = 56 - (round((x - 112) * 0.55) if x > 112 else 0) - (2 if x < 7 else 0)
        d.line([(x, top), (x, bot)], fill=YEL if x < 96 else YEL_LO)
        d.point((x, top), fill=WHITE); d.point((x, top + 1), fill=YEL_HI)
        d.line([(x, bot - 4), (x, bot)], fill=INDIGO); d.point((x, bot - 5), fill=WHITE)
        d.point((x, bot), fill=INDIGO_LO)
    text(d, 'NANIWA MARU', 26, 43, INDIGO, 1)
    for x in (12, 108):
        d.ellipse([x - 3, 44, x + 3, 50], fill=rgb('23262f')); d.point((x, 47), fill=STEEL_LO)
    # the deck: benches and passengers, the wheelhouse at the stern
    d.rectangle([8, 22, 26, 39], fill=TILE); d.line([(8, 22), (8, 39)], fill=WHITE); d.rectangle([23, 22, 26, 39], fill=TILE_LO)
    d.rectangle([11, 25, 22, 32], fill=rgb('9fd0f2')); d.line([(11, 25), (22, 25)], fill=WHITE)
    d.rectangle([14, 28, 18, 32], fill=INDIGO); d.rectangle([15, 26, 17, 28], fill=SKIN)
    d.rectangle([14, 25, 18, 26], fill=WHITE)
    for i, x in enumerate(range(34, 104, 10)):
        d.rectangle([x, 33, x + 6, 39], fill=VERM); d.line([(x, 33), (x + 6, 33)], fill=VERM_HI)
        if i % 3 != 2:
            c = (INDIGO_HI, TEAL, PINK, TILE, YEL_LO)[i % 5]
            d.rectangle([x + 1, 30, x + 5, 35], fill=c)
            d.rectangle([x + 1, 25, x + 5, 29], fill=SKIN); d.rectangle([x + 1, 24, x + 5, 26], fill=(INK, TIMBER_LO)[i % 2])
    for x in (30, 66, 104):
        d.line([(x, 20), (x, 39)], fill=STEEL); d.line([(x + 1, 20), (x + 1, 39)], fill=STEEL_DK)
    d.rectangle([4, 14, 110, 19], fill=TILE); d.line([(4, 14), (110, 14)], fill=WHITE)
    d.line([(4, 19), (110, 19)], fill=TILE_DK); d.rectangle([4, 17, 110, 18], fill=VERM)
    for i, x in enumerate(range(34, 104, 8)):
        d.rectangle([x, 20, x + 2, 23], fill=(VERM_HI, WARM)[i % 2])
    d.line([(118, 34), (118, 22)], fill=STEEL_DK)                  # a jackstaff and its flag
    d.polygon([(118, 22), (126, 25), (118, 28)], fill=VERM)
    # water: its shadow, ripples at the waterline
    d.line([(6, 57), (122, 57)], fill=DEEP); d.line([(10, 58), (116, 58)], fill=DEEP)
    for x in (10, 30, 52, 76, 98, 118):
        d.line([(x - 4, 59), (x + 2, 59)], fill=RIP)
    outline(im)
    return im


def canal_rail(post=False):
    """The canal's railing, low and open so the water shows: two rails and a
    wire, with (post=True) a lamp standard that the string of bulbs rises to."""
    im, d = canvas(1, 1)
    d.line([(0, 19), (31, 19)], fill=STEEL_HI); d.line([(0, 20), (31, 20)], fill=STEEL_LO)
    d.line([(0, 28), (31, 28)], fill=STEEL); d.line([(0, 29), (31, 29)], fill=STEEL_DK)
    if post:
        bar(d, 14, 9, 17, 29, STEEL, STEEL_HI, STEEL_DK)
        d.rectangle([12, 28, 19, 30], fill=STEEL_LO); d.line([(12, 28), (19, 28)], fill=STEEL_HI)
        ball(im, 15.5, 6, 3.5, 3.5, (WHITE, WARM, LIT, AMBER))
    else:
        d.line([(15, 21), (15, 27)], fill=STEEL_LO)
    outline(im)
    d = ImageDraw.Draw(im)
    d.line([(0, 24), (13 if post else 31, 24)], fill=STEEL_LO)     # the wire: not inked, to stay light
    if post:
        d.line([(18, 24), (31, 24)], fill=STEEL_LO)
    for x in range(32):                                            # the string of bulbs
        if post:
            if 12 <= x <= 19:
                continue
            y = 14 - round(4 * (1 - abs(x - 15.5) / 15.5))
        else:
            y = 14 + round(2 * math.sin(math.pi * x / 31.0))
        d.point((x, y), fill=STEEL_DK)
        if x % 6 == 2:
            c = (WARM, PINK_HI, CYAN, YEL_HI, LIME)[(x // 6 + (2 if post else 0)) % 5]
            d.rectangle([x, y + 1, x + 1, y + 2], fill=c); d.point((x, y + 1), fill=WHITE)
    return im


def quay_wall(drain=False):
    """The canal's embankment, for the water row under a boardwalk's south edge:
    a stone coping, coursed blocks going green toward the waterline, the wall's
    shade and a few ripples on the water (the rest of the cell is clear, so the
    water tile under it shows)."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    d = ImageDraw.Draw(im)
    Q, Q_HI, Q_LO, Q_DK = rgb('9aa0ad'), rgb('c3cad2'), rgb('747a8c'), rgb('545a6e')
    d.rectangle([0, 0, 31, 3], fill=STONE)
    d.line([(0, 0), (31, 0)], fill=WHITE); d.line([(0, 3), (31, 3)], fill=STONE_LO)
    d.line([(0, 4), (31, 4)], fill=Q_DK)
    for x in (15, 31):
        d.line([(x, 1), (x, 3)], fill=STONE_LO)
    for j, y in enumerate(range(5, 23, 6)):
        d.rectangle([0, y, 31, y + 5], fill=(Q, Q, Q_LO)[j])
        d.line([(0, y), (31, y)], fill=(Q_HI, Q_HI, Q)[j]); d.line([(0, y + 5), (31, y + 5)], fill=Q_DK)
        for x in range((j % 2) * 8 + 7, 32, 16):
            d.line([(x, y), (x, y + 5)], fill=Q_DK); d.point((x + 1, y), fill=(Q_HI, Q_HI, Q)[j])
    for x in range(32):                                            # weed and damp above the waterline
        hgt = 1 + (h3(x, 3, 11) % 3)
        d.line([(x, 22 - hgt), (x, 22)], fill=rgb('4f6a5a') if h3(x, 1, 4) % 3 else rgb('3d5248'))
    if drain:
        d.ellipse([11, 8, 20, 17], fill=Q_DK); d.ellipse([12, 9, 19, 16], fill=rgb('1b2040'))
        d.arc([11, 8, 20, 17], 180, 300, fill=Q_HI)
        d.line([(15, 16), (15, 23)], fill=RIP); d.line([(16, 17), (16, 24)], fill=rgb('5f86d6'))
        d.line([(13, 17), (13, 21)], fill=rgb('3d5248')); d.line([(18, 17), (18, 20)], fill=rgb('3d5248'))
        d.rectangle([25, 9, 28, 10], fill=P_IRON[1]); d.arc([24, 10, 29, 16], 0, 180, fill=P_IRON[2])   # a mooring ring
    d.rectangle([0, 23, 31, 26], fill=DEEP)
    for x in range(32):
        if h3(x // 3, 7, 5) % 3 == 0:
            d.point((x, 23), fill=RIP)
        if h3(x // 4, 2, 8) % 4 != 0:
            d.point((x, 27), fill=DEEP)
        if h3(x // 5, 5, 2) % 4 == 0:
            d.point((x, 29), fill=RIP)
    return im


TOWERS = (
    dict(size=(3, 7), fh=23, wall=(rgb('8a7e78'), rgb('a59a92'), rgb('6e645f'), rgb('4f4744')),
         roof=('MINAMI', NIGHT, PINK_HI),
         floors=(('IZAKAYA', VERM, VERM_DK, WHITE, WARM), ('DARTS', DARK, INK, LIME, rgb('c8f0a0')),
                 ('CURRY', YEL, YEL_LO, INK, WARM), ('SAUNA', TEAL_DK, INK, CYAN, rgb('bfeff5')),
                 ('MAHJONG', rgb('2f7a55'), rgb('1f5a40'), WHITE, WARM),
                 ('BILLIARDS', VIOLET, VIOLET_DK, PINK_HI, rgb('fbc5d8')), ('YAKINIKU', VERM_DK, INK, YEL_HI, LIT)),
         left=((['ra', 'bar', 'me', 'n'], VERM_DK, YEL_HI), ('CAFE', NIGHT, CYAN),
               (['ta', 'ko', 'ya', 'ki'], PINK_DK, WHITE), ('GYOZA', DARK, YEL_HI)),
         right=(('SAKE', INDIGO, WARM), (['ka', 'ni'], VERM, WHITE), ('UDON', YEL, INK), ('KUSHI', VERM_DK, WHITE))),
    dict(size=(4, 6), fh=26, wall=(TEAL_DK, TEAL_LO, rgb('123f3f'), rgb('0d2c2e')),
         roof=('NAMBA', VERM, YEL_HI),
         floors=(('MANZAI HALL', VERM, VERM_DK, YEL_HI, WARM), ('JAZZ KISSA', INDIGO, INDIGO_LO, WARM, rgb('ffd9a0')),
                 ('UDON', TILE, TILE_LO, INDIGO, WARM), ('RECORDS', DARK, INK, PINK_HI, rgb('fbc5d8')),
                 ('BAR TAKO', VIOLET, VIOLET_DK, CYAN, rgb('bfeff5'))),
         left=((['ya', 'ki', 'to', 'ri'], VERM_DK, WARM), ('BAR', NIGHT, PINK_HI), (['ra', 'bar', 'me', 'n'], YEL, VERM_DK)),
         right=(('SAKE', DARK, LIME), ('JAZZ', INDIGO_LO, YEL_HI), (['ta', 'ko'], PINK_DK, WHITE))),
)


def blade(d, x, y, word, bg, fg):
    """One projecting vertical sign; returns the y the next one starts at."""
    h = len(word) * 8 + 3
    d.rectangle([x, y, x + 10, y + h], fill=fg)
    d.rectangle([x + 1, y + 1, x + 9, y + h - 1], fill=bg)
    if isinstance(word, str):
        text(d, word, x + 3, y + 3, fg, 1, vertical=True)
    else:
        kana(d, word, x + 2, y + 3, fg, 1, vertical=True)
    return y + h + 4


def sign_tower(v):
    """A narrow tenant building, a different bar or parlour on every floor: a
    lettered fascia and a band of coloured light per storey, blade signs stacked
    down both edges, a bulb sign on the roof. The street's backdrop."""
    T = TOWERS[v]
    cw, ch = T['size']
    W, H = cw * 32, ch * 32
    im, d = canvas(cw, ch)
    x0, x1, fh = 13, W - 14, T['fh']
    wall = T['wall']
    facade_tile(d, x0, 24, x1, H - 3, pal=wall, tw=8, th=4)
    d.rectangle([x0 - 1, 22, x1 + 1, 25], fill=wall[1]); d.line([(x0 - 1, 25), (x1 + 1, 25)], fill=wall[3])
    for i, (word, bg, lo, fg, light) in enumerate(T['floors']):
        y = 27 + i * fh
        d.rectangle([x0 + 2, y, x1 - 2, y + 9], fill=bg)
        d.line([(x0 + 2, y + 9), (x1 - 2, y + 9)], fill=lo)
        ctext(d, word, W // 2, y + 1, fg, 1)
        a, b = y + 11, y + fh - 3
        d.rectangle([x0 + 2, a, x1 - 2, b], fill=wall[3])
        d.rectangle([x0 + 3, a + 1, x1 - 3, b], fill=light)
        d.line([(x0 + 3, a + 1), (x1 - 3, a + 1)], fill=WHITE)
        if i % 3 == 1:                                             # blinds half down
            for yy in range(a + 2, a + 6, 2):
                d.line([(x0 + 3, yy), (x1 - 3, yy)], fill=lo)
        for k, x in enumerate(range(x0 + 6, x1 - 8, 7)):
            if h3(x, i, 5 + v) % 3 == 0:                           # somebody at the window
                d.rectangle([x, b - 4, x + 4, b], fill=(DARK, INDIGO_LO, TIMBER_DK)[k % 3])
                d.rectangle([x + 1, b - 7, x + 3, b - 5], fill=(DARK, INDIGO_LO, TIMBER_DK)[k % 3])
        for x in range(x0 + 14, x1 - 3, 12):
            d.line([(x, a + 1), (x, b)], fill=wall[3])
    # blade signs down both edges
    y = 30
    for word, bg, fg in T['left']:
        d.line([(11, y + 3), (x0, y + 3)], fill=STEEL_DK)
        y = blade(d, 1, y, word, bg, fg)
    y = 34
    for word, bg, fg in T['right']:
        d.line([(x1, y + 3), (W - 12, y + 3)], fill=STEEL_DK)
        y = blade(d, W - 12, y, word, bg, fg)
    # the roof sign on its frame
    word, bg, fg = T['roof']
    tw_ = text_w(word, 2)
    bx0, bx1 = W // 2 - tw_ // 2 - 4, W // 2 + tw_ // 2 + 4
    for x in (bx0 + 6, W // 2, bx1 - 6):
        d.line([(x, 19), (x, 22)], fill=STEEL_DK); d.line([(x - 3, 22), (x + 3, 19)], fill=STEEL_LO)
    board(d, bx0, 1, bx1, 19, bg, rim=INK)
    ctext(d, word, W // 2, 3, fg, 2)
    if v == 1:
        star(d, bx0 - 9, 10, 6, YEL_HI, edge=YEL_LO); star(d, bx1 + 9, 10, 6, YEL_HI, edge=YEL_LO)
    # the ground floor: a tenants' board, the door, a lit shop
    g0 = 27 + len(T['floors']) * fh
    d.rectangle([x0 - 2, g0 - 1, x1 + 2, g0 + 3], fill=STEEL_HI); d.line([(x0 - 2, g0 + 3), (x1 + 2, g0 + 3)], fill=STEEL_DK)
    d.rectangle([x0 + 1, g0 + 4, x1 - 1, H - 3], fill=wall[2])
    d.rectangle([x0 + 3, g0 + 7, 30, H - 8], fill=INK)
    for j, yy in enumerate(range(g0 + 9, H - 10, 3)):
        d.line([(x0 + 5, yy), (28 - (j % 3) * 2, yy)], fill=(WARM, CYAN, PINK_HI, LIME, YEL_HI)[j % 5])
    glass_door(d, 34, g0 + 6, 61, H - 3, frame=wall[3])
    lit_window(d, 66, g0 + 7, x1 - 3, H - 9, frame=wall[3], goods=(VERM, YEL, TEAL, PINK, CREAM_DK))
    d.rectangle([x0 - 2, H - 2, x1 + 2, H - 1], fill=STONE_LO)
    outline(im)
    return im


# ==============================================================================
# Shinsekai, redrawn
# ==============================================================================
def lattice(im, pts, rows, cols, chord=3):
    """An OPEN steel lattice panel, TL TR BR BL. Nothing is drawn behind the
    members: the ground and whatever stands beyond show through. The far face
    is a darker lattice half a bay out of step; every near member has its own
    shaded edge."""
    (x0, y0), (x1, _), (x2, y2), (x3, _) = pts
    lay = Image.new('RGBA', im.size, CLEAR)
    pd = ImageDraw.Draw(lay)
    edge = lambda t: (x0 + (x3 - x0) * t, x1 + (x2 - x1) * t, y0 + (y2 - y0) * t)      # noqa: E731
    for r in range(rows):                                          # the far face
        la, ra, ya = edge(r / rows)
        lb, rb, yb = edge((r + 1) / rows)
        for c in range(cols):
            am = la + (ra - la) * (c + 0.5) / cols
            bm = lb + (rb - lb) * (c + 0.5) / cols
            pd.line([(am, ya), (bm, yb)], fill=BACK)
        pd.line([((la + lb) / 2, (ya + yb) / 2), ((ra + rb) / 2, (ya + yb) / 2)], fill=BACK)
    for r in range(rows):                                          # the near face: crossed braces
        la, ra, ya = edge(r / rows)
        lb, rb, yb = edge((r + 1) / rows)
        for c in range(cols):
            a0, a1 = la + (ra - la) * c / cols, la + (ra - la) * (c + 1) / cols
            b0, b1 = lb + (rb - lb) * c / cols, lb + (rb - lb) * (c + 1) / cols
            east = c >= cols * 0.6
            pd.line([(a0 + 1, ya), (b1 + 1, yb)], fill=STEEL_DK); pd.line([(a0, ya), (b1, yb)], fill=STEEL_LO if east else STEEL)
            pd.line([(a1 + 1, ya), (b0 + 1, yb)], fill=STEEL_DK); pd.line([(a1, ya), (b0, yb)], fill=STEEL if east else STEEL_HI)
    for r in range(rows + 1):
        la, ra, ya = edge(r / rows)
        pd.line([(la, ya), (ra, ya)], fill=STEEL_HI)
        pd.line([(la, ya + 1), (ra, ya + 1)], fill=STEEL_LO)
        pd.line([(la, ya + 2), (ra, ya + 2)], fill=STEEL_DK)
    for c in range(cols + 1):
        t = c / cols
        tp, bt = (x0 + (x1 - x0) * t, y0), (x3 + (x2 - x3) * t, y2)
        col = STEEL_HI if t < 0.3 else (STEEL if t < 0.6 else STEEL_LO)
        w = chord if c in (0, cols) else 2
        pd.line([(tp[0] + 1, tp[1]), (bt[0] + 1, bt[1])], fill=STEEL_DK, width=w)
        pd.line([tp, bt], fill=col, width=w)
        if c == 0:
            pd.line([(tp[0] - 1, tp[1]), (bt[0] - 1, bt[1])], fill=WHITE)
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    keep = ImageChops.multiply(mask, lay.getchannel('A'))
    im.paste(lay, (0, 0), keep)
    return mask


def tsutenkaku():
    """Tsutenkaku on the placeholder's silhouette (generate_tsutenkaku.py): the
    same 8x13 cells, legs, archway, deck, shaft and head at the same pixels.
    The steelwork is open: legs and shaft are see-through lattice."""
    W, H = 256, 416
    im, d = canvas(8, 13)
    CX = W // 2
    LEGS = [(66, 282), (190, 282), (232, 414), (24, 414)]
    SHAFT = [(98, 112), (158, 112), (176, 240), (80, 240)]
    # ---- legs + archway -----------------------------------------------------------
    hull = lattice(im, LEGS, rows=8, cols=6, chord=5)
    arch = Image.new('L', (W, H), 0)
    ad = ImageDraw.Draw(arch)
    ad.ellipse([86, 316, 170, 400], fill=255)
    ad.rectangle([86, 358, 170, H], fill=255)
    im.paste(CLEAR, (0, 0), arch)
    hull = ImageChops.subtract(hull, arch)
    d = ImageDraw.Draw(im)
    for k, c in enumerate((STEEL_DK, STEEL_LO, STEEL, STEEL_HI)):                 # the arch's steel rim
        d.arc([86 - 4 + k, 316 - 4 + k, 170 + 4 - k, 400 + 4 - k], 180, 360, fill=c)
        d.line([(86 - 4 + k, 358), (86 - 4 + k, 404)], fill=c)
        d.line([(170 + 4 - k, 358), (170 + 4 - k, 404)], fill=(STEEL_DK, STEEL_DK, STEEL_LO, STEEL)[k])
    d.arc([86, 316, 170, 400], 180, 360, fill=INK)
    d.line([(86, 358), (86, 404)], fill=INK); d.line([(170, 358), (170, 404)], fill=INK)
    for x in range(92, 166, 6):                                                   # bulbs round the arch
        y = 358 - math.sqrt(max(0, 42 ** 2 - (x - 128) ** 2)) - 2
        d.point((x, round(y)), fill=WARM)
    for x0, x1 in ((22, 84), (172, 234)):                                         # concrete footings
        d.rectangle([x0, 402, x1, 414], fill=STONE)
        d.line([(x0, 402), (x1, 402)], fill=WHITE); d.rectangle([x0, 410, x1, 414], fill=STONE_LO)
        d.rectangle([x1 - 5, 403, x1, 414], fill=STONE_LO)
        for x in range(x0 + 8, x1 - 4, 12):
            d.rectangle([x, 405, x + 1, 407], fill=STONE_DK)
    # ---- lower deck -----------------------------------------------------------------
    d.polygon([(58, 270), (198, 270), (190, 282), (66, 282)], fill=STEEL_DK)      # its underside
    for x in range(64, 196, 8):
        d.line([(x, 271), (x + (2 if x < 128 else -2), 281)], fill=STEEL_LO)
    d.rectangle([52, 248, 204, 270], fill=GLASS_DK)                               # the glazed band
    for i, x in enumerate(range(54, 202, 8)):
        lit = i % 5 in (1, 3)
        d.rectangle([x, 250, x + 5, 262], fill=WARM if lit else GLASS)
        d.line([(x, 250), (x + 5, 250)], fill=WHITE if lit else GLASS_HI)
    d.rectangle([52, 264, 204, 270], fill=VERM)                                   # a red fascia with bulbs
    d.line([(52, 264), (204, 264)], fill=VERM_HI); d.line([(52, 270), (204, 270)], fill=VERM_DK)
    for x in range(56, 202, 6):
        d.point((x, 267), fill=WARM)
    d.rectangle([196, 248, 204, 270], fill=GLASS_DK)
    d.polygon([(60, 240), (196, 240), (204, 248), (52, 248)], fill=TEAL_LO)       # its roof
    d.line([(60, 240), (196, 240)], fill=TEAL_HI)
    d.polygon([(60, 241), (128, 241), (128, 247), (53, 247)], fill=TEAL)
    for x in range(64, 196, 10):
        d.line([(x, 241), (x - (3 if x < 128 else -3), 247)], fill=TEAL_DK)
    # ---- shaft ----------------------------------------------------------------------
    hull = ImageChops.lighter(hull, lattice(im, SHAFT, rows=9, cols=4, chord=4))
    d = ImageDraw.Draw(im)
    # neon tubes down every outer edge: the tower's lit outline
    for (ax, ay), (bx, by), s in ((LEGS[0], LEGS[3], 1), (LEGS[1], LEGS[2], -1), (SHAFT[0], SHAFT[3], 1), (SHAFT[1], SHAFT[2], -1)):
        n = int((by - ay) // 6)
        for k in range(1, n):
            x, y = ax + (bx - ax) * k / n + s * 2, ay + (by - ay) * k / n
            if y < 400:
                d.point((round(x), round(y)), fill=WARM if k % 2 else WHITE)
    d.rectangle([CX - 12, 116, CX + 12, 236], fill=INK)                           # the neon sign band
    d.rectangle([CX - 10, 118, CX + 10, 234], fill=NIGHT)
    d.rectangle([CX - 10, 118, CX + 10, 234], outline=PINK)
    d.rectangle([CX - 8, 120, CX + 8, 232], outline=CYAN)
    star(d, CX, 128, 4, YEL_HI); star(d, CX, 224, 4, YEL_HI)
    text(d, 'OSAKA', CX - 5, 138, WHITE, 2, vertical=True)
    # ---- observation head -------------------------------------------------------------
    d.polygon([(84, 96), (172, 96), (158, 112), (98, 112)], fill=STEEL_DK)        # corbelled underside
    for x in range(90, 170, 8):
        d.line([(x, 97), (x + (4 if x < 128 else -4), 111)], fill=STEEL_LO)
    d.line([(84, 96), (172, 96)], fill=STEEL_LO)
    for (x0, x1, y0, y1) in ((84, 172, 76, 96), (92, 164, 56, 76)):
        d.rectangle([x0, y0, x1, y1], fill=STEEL)
        d.line([(x0, y0), (x1, y0)], fill=WHITE)
        d.rectangle([x0, y1 - 3, x1, y1], fill=STEEL_LO)
        d.rectangle([x1 - 8, y0, x1, y1], fill=STEEL_LO)
        for i, x in enumerate(range(x0 + 3, x1 - 6, 8)):
            lit = (i + y0 // 20) % 3 == 0
            d.rectangle([x, y0 + 4, x + 5, y1 - 6], fill=WARM if lit else GLASS)
            d.line([(x, y0 + 4), (x + 5, y0 + 4)], fill=WHITE if lit else GLASS_HI)
    d.line([(84, 76), (91, 76)], fill=WHITE); d.line([(165, 76), (172, 76)], fill=STEEL_HI)
    d.polygon([(104, 44), (152, 44), (164, 56), (92, 56)], fill=TEAL_LO)          # the roof: copper, a ring of neon
    d.polygon([(104, 45), (128, 45), (128, 55), (94, 55)], fill=TEAL)
    d.line([(104, 44), (152, 44)], fill=TEAL_HI)
    for x in range(98, 162, 8):
        d.line([(x + (3 if x < 128 else -3), 45), (x, 55)], fill=TEAL_DK)
    d.line([(93, 55), (163, 55)], fill=YEL_HI)
    d.rectangle([116, 34, 140, 44], fill=STEEL_DK)                                # the lantern room, lit
    d.rectangle([118, 36, 138, 43], fill=WARM); d.line([(118, 36), (138, 36)], fill=WHITE)
    for x in range(122, 138, 5):
        d.line([(x, 36), (x, 43)], fill=STEEL_DK)
    d.rectangle([114, 32, 142, 34], fill=STEEL); d.line([(114, 32), (142, 32)], fill=STEEL_HI)
    d.rectangle([124, 16, 132, 32], fill=STEEL)                                   # mast base
    d.line([(124, 16), (124, 32)], fill=STEEL_HI); d.rectangle([130, 16, 132, 32], fill=STEEL_LO)
    for y in range(20, 32, 4):
        d.line([(124, y), (132, y)], fill=STEEL_DK)
    d.rectangle([CX - 1, 10, CX, 16], fill=STEEL_LO)                              # the mast, a red lamp on it
    d.rectangle([CX - 2, 8, CX + 1, 10], fill=VERM); d.point((CX - 2, 8), fill=VERM_HI)
    outline_hull(im, hull)
    return im


def oni(im, d, cx, cy):
    """The shop's mascot: a scowling red oni, wild-haired and horned, a tiger
    skin across his chest, an iron club in one fist and one giant skewer in the
    other."""
    TIGER = (YEL_HI, YEL, YEL_LO, YEL_DK)
    ball(im, cx, cy + 32, 32, 16, P_RED)                                          # bare red shoulders
    d.polygon([(cx - 30, cy + 27), (cx - 14, cy + 19), (cx + 28, cy + 31), (cx + 28, cy + 36), (cx - 30, cy + 36)], fill=TIGER[1])
    d.line([(cx - 30, cy + 27), (cx - 14, cy + 19), (cx + 28, cy + 31)], fill=TIGER[0])
    for x in range(cx - 24, cx + 26, 7):                                          # its stripes
        d.line([(x, cy + 24 + (x - cx + 24) // 6), (x - 3, cy + 35)], fill=INK, width=2)
    # the club (west fist) and the skewer (east fist)
    club = [(cx - 40, cy + 30), (cx - 45, cy - 30)]
    tube(d, club, 6, 13, P_IRON)
    for k in range(7):
        t = 0.3 + k * 0.1
        x, y = club[0][0] + (club[1][0] - club[0][0]) * t, club[0][1] + (club[1][1] - club[0][1]) * t
        for s in (-1, 1):
            d.rectangle([round(x) + s * (3 + k // 3) - (s < 0), round(y), round(x) + s * (3 + k // 3) + (s > 0), round(y) + 1],
                        fill=STEEL_HI if s < 0 else STEEL)
    ball(im, cx - 45, cy - 31, 6, 4, P_IRON)
    skewer(im, d, (cx + 40, cy + 30), (cx + 44, cy - 30), ((0.42, 'fry'), (0.6, 'green'), (0.78, 'shrimp'), (0.94, 'fry')))
    for s in (-1, 1):
        tube(d, [(cx + s * 24, cy + 28), (cx + s * 34, cy + 24), (cx + s * 40, cy + 18)], 10, 9, P_RED)
        ball(im, cx + s * 40, cy + 16, 8, 7, P_RED)
        for k in (-3, 0, 3):
            d.line([(cx + s * 40 - 5, cy + 16 + k), (cx + s * 40 + 4, cy + 16 + k)], fill=VERM_LO)
        d.rectangle([cx + s * 34 - 2, cy + 20, cx + s * 34 + 2, cy + 27], fill=YEL)          # a gold wristband
        d.line([(cx + s * 34 - 2, cy + 20), (cx + s * 34 - 2, cy + 27)], fill=YEL_HI)
        tube(d, [(cx + s * 9, cy - 16), (cx + s * 15, cy - 26), (cx + s * 14, cy - 31)], 6, 1.5, P_HORN)   # horns
    HAIR = (rgb('4d566b'), rgb('23283a'), rgb('171b2b'), INK)
    for dx, dy, r in ((-17, -13, 6), (17, -13, 6), (-10, -20, 6), (10, -20, 6), (-3, -23, 7), (4, -24, 6), (-21, -5, 5), (21, -5, 5)):
        ball(im, cx + dx, cy + dy, r, r, HAIR)                                    # a mop of tight black curls
    ball(im, cx, cy, 23, 21, P_RED)
    for dx in (-13, -5, 3, 11):
        ball(im, cx + dx, cy - 17, 5, 4, HAIR)
    for s in (-1, 1):                                                             # the scowl
        d.line([(cx + s * 16, cy - 10), (cx + s * 4, cy - 4)], fill=INK, width=3)
        d.ellipse([cx + s * 9 - 3, cy - 4, cx + s * 9 + 3, cy + 2], fill=YEL_HI)
        d.rectangle([cx + s * 8 - 1, cy - 3, cx + s * 8, cy], fill=INK)
    ball(im, cx, cy + 5, 5, 4, (VERM_HI, VERM_HI, VERM, VERM_LO))                 # nose
    d.arc([cx - 13, cy + 9, cx + 13, cy + 25], 200, 340, fill=INK, width=2)       # a turned-down mouth
    for s in (-1, 1):
        d.polygon([(cx + s * 9 - 2, cy + 14), (cx + s * 9 + 2, cy + 14), (cx + s * 9, cy + 8)], fill=WHITE)


def oni_kushikatsu():
    im, d = canvas(4, 5)                 # 128 x 160
    facade_tile(d, 6, 60, 121, 157, pal=(rgb('f0d27a'), rgb('fbe9a8'), rgb('d3ae56'), rgb('a8843c')))
    bar(d, 4, 56, 123, 60, VERM, VERM_HI, VERM_DK)
    oni(im, d, 64, 34)
    board(d, 10, 68, 117, 88, VERM, rim=VERM_DK, hi=VERM_HI)
    ckana(d, ['kushi', 'ka', 'tsu'], 64, 70, WHITE, 2, shadow=VERM_DK)
    star(d, 24, 78, 5, YEL_HI); star(d, 103, 78, 5, YEL_HI)
    for i, x in enumerate(range(9, 114, 12)):
        chochin(d, x, 92, 9, 11, WHITE, WHITE, PAPER_LO, mark=VERM if i % 2 == 0 else INK)
    stripes(d, 4, 106, 123, 112, YEL, VERM, 5, lo=rgb('a8843c'))
    d.rectangle([8, 114, 119, 157], fill=TIMBER)
    lit_window(d, 10, 118, 58, 142, frame=TIMBER_DK)
    for i, x in enumerate((20, 34, 48)):                                          # customers at the counter
        person(d, x, 126, (INDIGO, TEAL_DK, VERM_LO)[i], hair=(INK, rgb('8a8078'), TIMBER_LO)[i])
    d.rectangle([11, 139, 57, 141], fill=WOOD)
    d.rectangle([10, 143, 58, 157], fill=TIMBER_LO)
    for x in range(14, 58, 6):
        d.line([(x, 144), (x, 157)], fill=TIMBER_DK)
    doorway(d, 66, 119, 93, 157, VERM, VERM_DK, mark=WHITE)
    d.rectangle([99, 116, 116, 152], fill=WHITE); d.rectangle([99, 116, 116, 152], outline=VERM)   # the sauce rule
    kana(d, ['so', 'bar', 'su'], 104, 121, VERM, 1, vertical=True)
    d.line([(102, 147), (113, 147)], fill=INK)
    d.rectangle([6, 158, 121, 159], fill=STONE_LO)
    outline(im)
    return im


def retro_arcade():
    """The arcade with a joystick the size of a car on its roof."""
    im, d = canvas(4, 5)                 # 128 x 160
    im.paste(_arcade_front(), (0, 32))
    d.polygon([(34, 52), (94, 52), (88, 38), (40, 38)], fill=DARK)                # the console it stands in
    d.polygon([(40, 38), (88, 38), (86, 34), (42, 34)], fill=rgb('5a5268'))
    d.line([(42, 34), (86, 34)], fill=rgb('7a7090')); d.line([(34, 52), (40, 38)], fill=rgb('4a4258'))
    d.rectangle([34, 50, 94, 52], fill=INK)
    ball(im, 50, 36, 6, 3, (rgb('7a7090'), rgb('3a3348'), INK, INK))               # the gate
    bar(d, 48, 12, 52, 36, STEEL, WHITE, STEEL_DK)
    ball(im, 50, 11, 11, 11, P_RED)
    ball(im, 70, 37, 6, 4, P_GOLD); ball(im, 82, 39, 6, 4, P_TEAL)                # two fat buttons
    d.line([(64, 41), (76, 41)], fill=YEL_DK); d.line([(76, 43), (88, 43)], fill=TEAL_DK)
    outline(im)
    return im


KOMA, KOMA_HI, KOMA_LO, KOMA_DK = rgb('e2bd7a'), rgb('f6dca0'), rgb('bb9150'), rgb('8a6636')


def shogi_parlour():
    im, d = canvas(3, 4)                 # 96 x 128
    # upper storey: dark boards, a tiled roof
    d.rectangle([6, 44, 89, 84], fill=TIMBER)
    for y in range(48, 84, 5):
        d.line([(6, y), (89, y)], fill=TIMBER_LO)
    d.line([(6, 44), (6, 84)], fill=TIMBER_HI); d.rectangle([85, 44, 89, 84], fill=TIMBER_DK)
    pent_roof(d, 6, 34, 89, 10)
    d.rectangle([14, 29, 81, 33], fill=KAWARA_LO); d.line([(14, 29), (81, 29)], fill=KAWARA_HI)
    for x in (9, 72):
        lit_window(d, x, 54, x + 14, 72, frame=TIMBER_DK, bars=4)
    # the giant piece: the king, one clean character
    pts = [(48, 12), (65, 23), (70, 80), (26, 80), (31, 23)]
    d.polygon(pts, fill=KOMA)
    d.polygon([(48, 12), (65, 23), (70, 80), (63, 80), (59, 25), (48, 17)], fill=KOMA_LO)
    d.line([(48, 12), (31, 23), (26, 80)], fill=KOMA_HI)
    d.line([(26, 80), (70, 80)], fill=KOMA_DK)
    for y in range(28, 78, 9):
        d.line([(32, y), (36, y + 1)], fill=KOMA_LO)                             # the grain
    kana(d, ['king'], 38, 34, INK, 3)
    d.rectangle([44, 62, 51, 69], fill=VERM); d.rectangle([46, 64, 49, 67], fill=KOMA)   # the maker's seal
    # the front
    d.rectangle([6, 94, 89, 125], fill=TIMBER); d.rectangle([85, 94, 89, 125], fill=TIMBER_DK)
    pent_roof(d, 4, 85, 91, 8)
    doorway(d, 34, 97, 61, 125, rgb('7a4a34'), rgb('553224'), mark=PAPER)
    d.rectangle([8, 99, 30, 117], fill=TIMBER_DK)                               # two players at a board
    d.rectangle([9, 100, 29, 116], fill=WARM)
    d.rectangle([11, 104, 15, 109], fill=INK); d.rectangle([10, 110, 16, 116], fill=INDIGO)
    d.rectangle([23, 104, 27, 109], fill=rgb('8a8078')); d.rectangle([22, 110, 28, 116], fill=TEAL_DK)
    d.rectangle([12, 106, 15, 109], fill=SKIN); d.rectangle([23, 106, 26, 109], fill=SKIN)
    d.rectangle([16, 112, 22, 116], fill=KOMA); d.line([(16, 112), (22, 112)], fill=KOMA_HI)
    d.line([(18, 113), (18, 116)], fill=KOMA_DK); d.line([(20, 113), (20, 116)], fill=KOMA_DK)
    d.rectangle([8, 118, 30, 125], fill=TIMBER_LO)
    d.rectangle([69, 82, 81, 124], fill=PAPER); d.rectangle([69, 82, 81, 124], outline=TIMBER_DK)   # the signboard
    text(d, 'SHOGI', 73, 84, INK, 1, vertical=True)
    d.rectangle([3, 126, 92, 127], fill=STONE_LO)
    outline(im)
    return im


def shooting_gallery():
    """A cork-gun shooting gallery in mint boards: a giant target and a giant
    cork rifle on the roof, prizes on stepped shelves, rifles on the counter."""
    im, d = canvas(3, 4)                 # 96 x 128
    MINT, MINT_HI, MINT_LO, MINT_DK = rgb('9fd6c0'), rgb('c8eedd'), rgb('78b39e'), rgb('4f8a78')
    d.rectangle([5, 42, 90, 125], fill=MINT)
    for y in range(46, 125, 5):
        d.line([(5, y), (90, y)], fill=MINT_LO)
    d.line([(5, 42), (5, 125)], fill=MINT_HI); d.rectangle([86, 42, 90, 125], fill=MINT_LO)
    bar(d, 3, 38, 92, 42, VERM, VERM_HI, VERM_DK)
    # the rifle, lying along the roof, and the target
    d.polygon([(40, 30), (58, 24), (62, 30), (52, 37), (42, 37)], fill=WOOD_LO)   # the stock
    d.line([(40, 30), (58, 24)], fill=WOOD); d.polygon([(42, 37), (52, 37), (50, 33)], fill=WOOD_DK)
    tube(d, [(58, 27), (90, 16)], 5, 4, P_IRON)
    d.rectangle([89, 13, 93, 17], fill=DOUGH_LO); d.point((89, 13), fill=DOUGH_HI)   # the cork in its muzzle
    d.line([(62, 31), (66, 36), (70, 31)], fill=P_IRON[1])                        # the trigger guard
    for r, c in ((19, VERM_DK), (18, VERM), (14, WHITE), (10, VERM), (6, WHITE), (3, YEL)):
        d.ellipse([26 - r, 20 - r, 26 + r, 20 + r], fill=c)
    d.arc([8, 2, 44, 38], 150, 270, fill=VERM_HI)
    d.rectangle([29, 13, 33, 17], fill=DOUGH_LO); d.point((29, 13), fill=DOUGH_HI)   # a cork, stuck just off the gold
    # the name, in red on cream
    d.rectangle([5, 46, 90, 64], fill=VERM_DK); d.rectangle([6, 47, 89, 63], fill=PAPER)
    ctext(d, 'SHATEKI', 48, 49, VERM, 2)
    # the open stall
    d.rectangle([8, 68, 87, 108], fill=rgb('3a2a2c'))
    d.rectangle([8, 68, 87, 71], fill=WARM)
    for i, x in enumerate(range(10, 87, 5)):
        d.point((x, 73 + (i % 2)), fill=(WARM, PINK_HI, CYAN)[i % 3])
    prizes = (VERM, YEL, TEAL, PINK, INDIGO_HI, LIME, WHITE)
    for j, sy in enumerate((84, 94, 104)):                                        # prizes on stepped shelves
        d.rectangle([10 + j * 2, sy, 66 - j * 2, sy + 1], fill=WOOD); d.line([(10 + j * 2, sy + 2), (66 - j * 2, sy + 2)], fill=WOOD_DK)
        for i, x in enumerate(range(13 + j * 2, 62 - j * 2, 7)):
            c = prizes[(i * 2 + j * 3) % 7]
            if (i + j) % 3 == 0:
                ball(im, x + 2, sy - 3, 3, 3, (WHITE, c, c, INK))                 # a soft toy
                d.point((x + 1, sy - 4), fill=INK); d.point((x + 3, sy - 4), fill=INK)
            else:
                d.rectangle([x, sy - 6 + (i % 2), x + 4, sy - 1], fill=c); d.line([(x, sy - 6 + (i % 2)), (x + 4, sy - 6 + (i % 2))], fill=WHITE)
    person(d, 77, 84, VERM, cap=WHITE)
    d.rectangle([5, 105, 90, 109], fill=WOOD); d.line([(5, 105), (90, 105)], fill=rgb('d2a58c'))
    d.line([(5, 109), (90, 109)], fill=WOOD_DK)
    for x in (12, 36):                                                            # rifles laid ready, a dish of corks
        d.rectangle([x, 102, x + 6, 104], fill=WOOD_LO); d.line([(x + 6, 102), (x + 20, 102)], fill=P_IRON[1])
        d.line([(x + 6, 103), (x + 18, 103)], fill=P_IRON[2])
    d.rectangle([62, 102, 70, 104], fill=WHITE); d.line([(63, 101), (69, 101)], fill=DOUGH_LO)
    d.rectangle([5, 110, 90, 125], fill=MINT)
    for x in range(5, 90, 6):
        d.line([(x, 111), (x, 125)], fill=MINT_LO)
    d.rectangle([86, 110, 90, 125], fill=MINT_LO)
    for x in (20, 48, 76):
        star(d, x, 118, 5, VERM, edge=VERM_DK)
    d.rectangle([3, 126, 92, 127], fill=STONE_LO)
    outline(im)
    return im


def lucky_idol():
    """Shinsekai's own idol, invented: Fuku-san, a round gold owl painted like a
    daruma, its belly rubbed bright by passers-by."""
    im, d = canvas(2, 3)                 # 64 x 96
    cx = 32
    # the plinth: stone, a red cloth, a plaque
    d.rectangle([9, 68, 54, 93], fill=STONE)
    d.line([(9, 68), (9, 93)], fill=WHITE); d.rectangle([49, 68, 54, 93], fill=STONE_LO)
    d.line([(9, 80), (54, 80)], fill=STONE_LO); d.rectangle([7, 90, 56, 93], fill=STONE_LO)
    d.line([(7, 90), (56, 90)], fill=STONE)
    d.rectangle([7, 64, 56, 69], fill=VERM); d.line([(7, 64), (56, 64)], fill=VERM_HI)
    d.line([(7, 69), (56, 69)], fill=VERM_DK)
    for x in range(9, 56, 4):
        d.point((x, 70), fill=YEL)
    d.rectangle([21, 73, 43, 86], fill=YEL_LO); d.rectangle([22, 74, 42, 85], fill=YEL)
    kana(d, ['fu', 'ku'], 25, 76, VERM_DK, 1)
    # the owl
    BRZ = (YEL_HI, YEL, YEL_LO, YEL_DK)
    for s in (-1, 1):                                                            # ear tufts
        d.polygon([(cx + s * 18, 30), (cx + s * 17, 8), (cx + s * 5, 20)], fill=YEL if s < 0 else YEL_LO)
        d.line([(cx + s * 17, 9), (cx + s * 8, 19)], fill=YEL_HI if s < 0 else YEL)
    ball(im, cx, 42, 23, 24, BRZ)
    for s in (-1, 1):                                                            # folded wings
        ball(im, cx + s * 20, 48, 5, 13, (YEL, YEL_LO, YEL_DK, YEL_DK))
        for y in (42, 48, 54):
            d.arc([cx + s * 20 - 4, y - 3, cx + s * 20 + 4, y + 3], 20, 160, fill=YEL_DK)
    ball(im, cx, 56, 13, 9, (WHITE, YEL_HI, YEL_HI, YEL))                        # the rubbed belly
    for y, n in ((52, 3), (57, 4), (62, 3)):                                     # feathers, in scallops
        for k in range(n):
            x = cx - (n - 1) * 3 + k * 6
            d.arc([x - 3, y - 3, x + 3, y + 3], 20, 160, fill=YEL_LO)
    d.pieslice([cx - 9, 40, cx + 9, 54], 0, 180, fill=VERM)                      # a red bib
    d.line([(cx - 9, 47), (cx + 9, 47)], fill=VERM_HI); d.rectangle([cx - 1, 49, cx, 51], fill=YEL_HI)
    for s in (-1, 1):                                                            # daruma's painted face: great round eyes
        ball(im, cx + s * 9, 33, 9, 9, (WHITE, rgb('fbf1dc'), DOUGH, DOUGH_LO))
        d.ellipse([cx + s * 9 - 9, 24, cx + s * 9 + 9, 42], outline=YEL_DK)
        d.ellipse([cx + s * 8 - 4, 30, cx + s * 8 + 4, 38], fill=INK)
        d.rectangle([cx + s * 8 - 2, 31, cx + s * 8 - 1, 32], fill=WHITE)
        d.line([(cx + s * 2, 26), (cx + s * 16, 20)], fill=INK, width=3)         # sweeping brows
        d.line([(cx + s * 16, 20), (cx + s * 19, 23)], fill=INK, width=2)
    d.polygon([(cx - 4, 39), (cx + 3, 39), (cx, 46), (cx - 1, 46)], fill=rgb('f08a3c'))   # the beak
    d.line([(cx - 4, 39), (cx + 3, 39)], fill=YEL_HI)
    for s in (-1, 1):                                                            # talons on the cloth
        for k in (-3, 0, 3):
            d.rectangle([cx + s * 9 + k - 1, 64, cx + s * 9 + k, 67], fill=rgb('f08a3c'))
        d.line([(cx + s * 9 - 4, 64), (cx + s * 9 + 3, 64)], fill=FRY_HI)
    outline(im)
    return im


def fugu(im, d, cx, cy):
    """The paper pufferfish, lit from inside."""
    for k in range(20):                                                          # spikes all round
        a = math.radians(k * 18 + 9)
        x0, y0 = cx + 21 * math.cos(a), cy + 19 * math.sin(a)
        d.line([(x0, y0), (cx + 25 * math.cos(a), cy + 23 * math.sin(a))], fill=DOUGH if y0 > cy else rgb('b0895e'))
    d.polygon([(cx - 20, cy - 2), (cx - 27, cy - 8), (cx - 26, cy + 5)], fill=rgb('c9a070'))     # fins
    d.polygon([(cx + 20, cy - 2), (cx + 27, cy - 8), (cx + 26, cy + 5)], fill=rgb('8f6a46'))
    ball(im, cx, cy, 22, 20, (WHITE, rgb('fff3cf'), rgb('f0d79c'), rgb('cfa868')))               # the lit belly
    ball(im, cx, cy, 22, 20, (rgb('d9b888'), rgb('b8905e'), rgb('8f6a46'), rgb('6b4c36')), a1=-3)   # the back
    for dx, dy in ((-10, -15), (0, -17), (10, -14), (-5, -10), (6, -9), (-14, -8), (14, -7)):    # spots
        d.rectangle([cx + dx, cy + dy, cx + dx + 1, cy + dy + 1], fill=rgb('5f4434'))
    for y in (cy + 4, cy + 10, cy + 15):                                         # the paper's ribs
        w = 20 * math.sqrt(max(0, 1 - ((y - cy) / 20.0) ** 2))
        d.line([(cx - w + 2, y), (cx + w - 3, y)], fill=rgb('e6c98c'))
    for s in (-1, 1):
        d.ellipse([cx + s * 10 - 4, cy - 6, cx + s * 10 + 4, cy + 2], fill=WHITE)
        d.ellipse([cx + s * 10 - 2, cy - 4, cx + s * 10 + 1, cy], fill=INK)
        d.point((cx + s * 10 - 1, cy - 3), fill=WHITE)
    d.ellipse([cx - 4, cy + 4, cx + 4, cy + 10], fill=VERM)                      # pouting lips
    d.line([(cx - 3, cy + 7), (cx + 3, cy + 7)], fill=VERM_DK)
    d.point((cx - 2, cy + 5), fill=VERM_HI)
    d.line([(cx, cy + 21), (cx, cy + 25)], fill=INK)                             # a tassel
    d.rectangle([cx - 2, cy + 25, cx + 1, cy + 33], fill=VERM); d.line([(cx - 2, cy + 25), (cx - 2, cy + 33)], fill=VERM_HI)


def fugu_lantern():
    im, d = canvas(2, 3)                 # 64 x 96
    d.rectangle([7, 8, 9, 91], fill=TIMBER); d.line([(7, 8), (7, 91)], fill=TIMBER_HI)        # the post and its bracket
    d.rectangle([4, 91, 12, 95], fill=STONE_LO); d.line([(4, 91), (12, 91)], fill=STONE)
    d.rectangle([7, 10, 42, 11], fill=TIMBER); d.line([(7, 10), (42, 10)], fill=TIMBER_HI)
    d.line([(9, 24), (22, 12)], fill=TIMBER_LO)
    d.line([(38, 12), (38, 21)], fill=INK)
    fugu(im, d, 38, 43)
    outline(im)
    return im


def fugu_sign():
    """The same fish for a shopfront: hung from an iron wall bracket, no post."""
    im, d = canvas(2, 2)                 # 64 x 64
    d.rectangle([2, 1, 5, 9], fill=P_IRON[1]); d.line([(2, 1), (2, 9)], fill=P_IRON[0])        # the wall plate
    d.rectangle([5, 3, 40, 4], fill=P_IRON[1]); d.line([(5, 3), (40, 3)], fill=P_IRON[0])
    d.arc([6, 4, 20, 16], 180, 270, fill=P_IRON[2]); d.arc([36, 0, 44, 8], 270, 90, fill=P_IRON[1])
    d.line([(33, 5), (33, 8)], fill=INK)
    fugu(im, d, 33, 29)
    outline(im)
    return im


def beer_crates():
    """Empties out the back of a bar: bottle crates stacked two and one, the
    brown bottles standing in them."""
    im, d = canvas(1, 1)

    def crate(x, y, pal, bottles):
        base, hi, lo, dk = pal
        if bottles:
            for bx in range(x + 2, x + 13, 3):
                d.rectangle([bx, y - 5, bx + 1, y - 1], fill=rgb('7a4a1c')); d.point((bx, y - 5), fill=rgb('b9783a'))
                d.line([(bx, y - 6), (bx + 1, y - 6)], fill=YEL_HI)
        d.rectangle([x, y, x + 14, y + 9], fill=base)
        d.line([(x, y), (x + 14, y)], fill=hi); d.line([(x, y), (x, y + 9)], fill=hi)
        d.line([(x + 14, y + 1), (x + 14, y + 9)], fill=lo); d.line([(x, y + 9), (x + 14, y + 9)], fill=dk)
        d.rectangle([x + 4, y + 2, x + 10, y + 3], fill=INK)                      # the hand hole
        for sx in (x + 2, x + 7, x + 12):
            d.line([(sx, y + 5), (sx, y + 8)], fill=lo)                           # ribs
        d.line([(x + 1, y + 5), (x + 13, y + 5)], fill=lo)

    crate(2, 20, P_GOLD, False)
    crate(3, 10, P_RED, True)
    crate(16, 20, (TEAL_HI, TEAL, TEAL_LO, TEAL_DK), True)
    outline(im)
    return im


def board_tex(x, y):
    """Dark ironwood planks running east-west. One butt joint a row, stepped
    half and quarter a tile from row to row so no two line up into a ladder."""
    row = y // 8
    v = (x + (3, 19, 11, 27)[row]) % 32
    if y % 8 == 7:
        return rgb('3a2822')
    if v == 31:
        return rgb('4a3229')
    if v in (1, 29) and y % 8 == 3:
        return rgb('b3a595')                                      # a screw head either side of the joint
    if y % 8 == 0:
        return rgb('86614f')
    if h3(x // 4, y, 17) < 26:
        return rgb('5e4034')
    return DECKING[row]


# ==============================================================================
def rows(w, r0, r1):
    return [[c, r] for r in range(r0, r1 + 1) for c in range(w)]


def L(x, y, color, r=0.9, a=0.5, **kw):
    """One glow spot, as src/utils/Glows.js reads it (cells from the sprite's
    top-left; `color` a number)."""
    return dict(x=x, y=y, r=r, color=color, a=a, **kw)


def edge_lights(a, b, n, color, r=0.55, alpha=0.4):
    """n glow spots strung from a to b (cells): a lit edge."""
    return [L(round(a[0] + (b[0] - a[0]) * (k + 0.5) / n, 2), round(a[1] + (b[1] - a[1]) * (k + 0.5) / n, 2), color, r, alpha)
            for k in range(n)]


ST, DB, SK = 'Station front', 'Dotonbori', 'Shinsekai'
G_WARM, G_PAPER, G_RED, G_YEL, G_PINK, G_CYAN, G_COOL = 0xffc070, 0xfff0d0, 0xff6050, 0xffd24a, 0xff5fa8, 0x4fe0e8, 0xbfd4ff
G_LIME, G_NEON = 0x9fe88a, 0xffe2a0

# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH under it (gates)
#   lit: its lit parts as glow spots (see L)
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'ground' = flat, under the player
PIECES = [
    ('osaka-station-front_0_0', station_front, (10, 6), ST, dict(
        door=[[4, 5], [5, 5]], solid=rows(10, 3, 5),
        lit=[L(2.75, 1.56, 0xfff0c0, 0.7, 0.7), L(5, 0.75, G_COOL, 3.2, 0.25, ry=0.8),
             L(2.6, 2.45, 0xffe9b0, 2.4, 0.3, ry=0.4), L(7.4, 2.45, 0xffe9b0, 2.4, 0.3, ry=0.4),
             L(2.1, 3.4, 0xffb347, 1.2, 0.45, ry=0.4), L(7.8, 3.4, G_PAPER, 1.2, 0.3, ry=0.4),
             L(5, 4.9, G_COOL, 1.3, 0.6), L(1.05, 4.95, G_WARM, 0.9, 0.55), L(2.85, 4.9, 0xdfe9f2, 0.9, 0.45),
             L(7.1, 4.95, G_WARM, 0.9, 0.55), L(8.95, 4.95, G_WARM, 0.9, 0.55)]),
     'Osaka Station as its roof: one great sloping plane of glass in a white steel grid, wider than the '
     'building and higher than anything beside it, carried on four white steel trees and two slim stone '
     'pylons. Under it the open deck: people along a rail, a gold clock on a post (the meeting spot, west of '
     'centre), a cream and orange train standing at the platform behind, the far building in shade. Below, '
     'a low stone front: a departures board, OSAKA cut in the cream band east of the doors, a glass canopy '
     'over two pairs of glass doors (the two middle cells), and four different bays: a bakery, the ticket '
     'office with two clerks, a cafe with two people at a table, a station-bento counter.'),
    ('osaka-wheel-mall_0_0', wheel_mall, (5, 7), ST, dict(
        door=[[2, 6]], solid=rows(5, 4, 6),
        lit=[L(2.5, 2.1, G_RED, 2.3, 0.35), L(2.5, 2.1, 0xfff0c0, 0.6, 0.6), L(2.5, 4.1, G_PAPER, 2.0, 0.35, ry=0.4),
             L(2.5, 5.15, G_COOL, 0.9, 0.5), L(1.1, 5.1, G_WARM, 1.0, 0.4), L(3.9, 5.1, G_WARM, 1.0, 0.4),
             L(1.1, 6.45, G_WARM, 1.0, 0.6), L(3.9, 6.45, G_WARM, 1.0, 0.6), L(2.5, 6.5, G_COOL, 0.6, 0.4)]),
     'The station district\'s second landmark: a red-tiled shopping block with a red observation wheel '
     'rising out of its roof (see-through between the spokes; sixteen cream and yellow gondolas, bulbs '
     'round the rim). WHEEL PLAZA on a white band, a glass atrium with escalators, lit display windows, '
     'mannequins in the shop windows either side of the glass door. An invented name; round and red, where '
     'the existing dotonbori-wheel is a yellow oval on the discount store.'),
    ('osaka-crab-restaurant_0_0', crab_restaurant, (4, 5), DB, dict(
        door=[[1, 4]], solid=rows(4, 2, 4),
        lit=[L(2, 2.55, 0x8fc4ff, 1.6, 0.5, ry=0.6), L(2, 1.5, G_RED, 1.6, 0.35), L(2, 3.3, G_WARM, 1.7, 0.4, ry=0.5),
             L(2.85, 4.35, 0x6fb4ff, 0.9, 0.6), L(1.5, 4.45, G_WARM, 0.7, 0.6)]),
     'A seafood restaurant in white tile under a giant mechanical crab: a red riveted shell, steel discs at '
     'every joint, both claws up, eyes on stalks; it sits on an indigo wave board (crab in kana, SEAFOOD). '
     'Lattice windows and white lanterns upstairs, a red and white awning, an open doorway with a parted '
     'indigo noren and a stone step, a tank of crabs in the window. An invented crab, not a chain\'s.'),
    ('osaka-takoyaki-stand_0_0', takoyaki_stand, (4, 4), DB, dict(
        solid=rows(3, 2, 3) + [[3, 3]],
        lit=[L(1.6, 2.5, G_RED, 1.5, 0.5, ry=0.5), L(1.6, 3.2, G_WARM, 1.5, 0.65, ry=0.5), L(1.6, 0.95, G_PINK, 1.3, 0.3)]),
     'A takoyaki stand under a giant pink octopus in a headband, one arm up with a takoyaki on a pick, the '
     'others draped over the awning: takoyaki in kana on a red board, a cook at a steaming griddle of '
     'dumplings, paper boats on the shelf, and a queue rope on brass posts in its fourth column. A stall: '
     'no door, you are served at the counter.'),
    ('osaka-gyoza-izakaya_0_0', gyoza_izakaya, (4, 5), DB, dict(
        door=[[1, 4]], solid=rows(4, 2, 4),
        lit=[L(0.58, 2.9, G_PAPER, 0.7, 0.7), L(3.42, 2.9, G_PAPER, 0.7, 0.7), L(2, 2.9, G_RED, 1.2, 0.45, ry=0.5),
             L(2, 2.05, G_WARM, 1.7, 0.35, ry=0.4), L(2.85, 4.3, G_WARM, 0.9, 0.6), L(1.5, 4.4, G_WARM, 0.7, 0.6)]),
     'An izakaya in plaster and dark timber with a giant plate of pan-fried gyoza on its roof, a fourth '
     'dumpling lifted clear in red chopsticks: a row of lit lattice windows upstairs, GYOZA in solid white '
     'letters on a red board between two white lanterns, tiled pent roofs, an open doorway with a parted '
     'indigo noren, bottles in a lattice window, a chalk menu.'),
    ('osaka-sprinter-billboard_0_0', sprinter_billboard, (6, 6), DB, dict(
        door=[[2, 5]], solid=rows(6, 3, 5),
        lit=[L(3, 1.9, G_PINK, 3.0, 0.5, flicker=True), L(3, 0.8, 0x8f6bff, 2.4, 0.35), L(4.35, 3.3, G_YEL, 1.5, 0.55, ry=0.5),
             L(1.2, 0.5, G_CYAN, 1.1, 0.4, ry=0.4), L(3, 4.72, G_WARM, 2.6, 0.4, ry=0.4),
             L(1.1, 5.35, G_WARM, 1.0, 0.6), L(4.4, 5.35, G_WARM, 1.5, 0.6), L(2.5, 5.45, G_COOL, 0.6, 0.4)]),
     'The canal\'s great neon board, six cells wide, on a steel gantry with floodlights over a low '
     'black-tiled diner: an invented hurdler in a teal singlet (number 1) and yellow shorts, side on, '
     'mid-leap over a red and white hurdle, built of jointed limbs with hands and spiked yellow shoes, hair '
     'and a pink headband streaming; the town\'s roofs on the horizon, pink track lanes, speed lines, NANIWA '
     'above and DASH! below, bulbs round the frame. Not the real running man: another event, pose, kit and '
     'sky. Below: NANIWA DINER in lights, diners in booths, a glass door (third cell).'),
    ('osaka-dragon-ramen_0_0', dragon_ramen, (4, 5), DB, dict(
        door=[[1, 4]], solid=rows(4, 2, 4),
        lit=[L(1.25, 2.2, G_YEL, 1.3, 0.55, ry=0.6), L(2.9, 1.9, 0x7fc0f5, 1.0, 0.3), L(1.1, 3.05, G_RED, 1.1, 0.4, ry=0.35),
             L(1.5, 4.3, G_WARM, 0.7, 0.6), L(2.85, 4.0, G_WARM, 0.9, 0.6), L(0.6, 3.95, 0xfff0c0, 0.4, 0.5)]),
     'A ramen shop in red lacquer whose dragon has come through the sign: a thick blue scaled neck, a big '
     'horned head with jaws wide and both claws hooked over the yellow board, out of a jagged hole smashed '
     'in it, splinters flying; the tail, gold-bellied with pink fins, out through the roof at the far end. '
     'Ramen in kana and RAMEN on what is left of the board, red lanterns, a meal-ticket machine, an open '
     'doorway with a parted red noren (second cell), a cook and a stock pot in the kitchen window.'),
    ('osaka-okonomiyaki-front_0_0', okonomiyaki_front, (3, 4), DB, dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[L(1.5, 1.78, 0x9fe0b0, 1.3, 0.45, ry=0.4), L(1.5, 0.8, G_WARM, 1.1, 0.25), L(0.6, 3.35, G_WARM, 0.6, 0.6),
             L(2.4, 3.35, G_WARM, 0.6, 0.6), L(1.5, 3.45, G_WARM, 0.7, 0.6)]),
     'An okonomiyaki house in charred boards and copper (the street\'s one dark front): a giant pancake on '
     'an iron plate on the roof, sauce and a lattice of mayonnaise, two giant steel turners crossed behind '
     'it, steam; OKONOMI in cream on dark green, wooden menu plaques, a copper hood, a cook at the griddle '
     'window, an open doorway with a parted green noren, diners at the iron counter.'),
    ('osaka-sign-tower-a_0_0', lambda: sign_tower(0), (3, 7), DB, dict(
        door=[[1, 6]], solid=rows(3, 4, 6),
        lit=[L(1.5, 0.32, G_PINK, 1.3, 0.6, ry=0.4, flicker=True)]
            + [L(1.5, y, c, 1.1, 0.45, ry=0.35) for y, c in ((1.28, G_WARM), (2.0, G_LIME), (2.72, G_WARM), (3.44, G_CYAN),
                                                              (4.16, G_WARM), (4.87, G_PINK), (5.59, G_WARM))]
            + [L(0.2, y, c, 0.45, 0.5) for y, c in ((1.6, G_YEL), (2.8, G_CYAN), (4.0, G_PINK), (5.2, G_YEL))]
            + [L(2.8, y, c, 0.45, 0.5) for y, c in ((1.7, G_WARM), (2.7, G_RED), (3.6, G_YEL), (4.9, G_RED))]
            + [L(1.5, 6.5, G_COOL, 0.6, 0.4), L(2.35, 6.4, G_WARM, 0.6, 0.6)]),
     'The street\'s backdrop: a narrow seven-storey tenant building, a different bar or parlour on every '
     'floor (IZAKAYA, DARTS, CURRY, SAUNA, MAHJONG, BILLIARDS, YAKINIKU), each a lettered fascia over a band '
     'of its own coloured light with people at the windows; vertical blade signs stacked down both edges '
     '(ramen, CAFE, takoyaki, GYOZA; SAKE, crab, UDON, KUSHI); MINAMI in bulbs on the roof; a tenants\' board, '
     'a glass door (middle cell) and a lit shop at the foot. Stand it between the mascot fronts.'),
    ('osaka-sign-tower-b_0_0', lambda: sign_tower(1), (4, 6), DB, dict(
        door=[[1, 5]], solid=rows(4, 3, 5),
        lit=[L(2, 0.32, G_RED, 1.4, 0.6, ry=0.4, flicker=True)]
            + [L(2, y, c, 1.5, 0.45, ry=0.35) for y, c in ((1.28, G_WARM), (2.09, 0xffd9a0), (2.91, G_WARM), (3.72, G_PINK),
                                                            (4.53, G_CYAN))]
            + [L(0.2, y, c, 0.45, 0.5) for y, c in ((1.55, G_WARM), (2.75, G_PINK), (3.7, G_YEL))]
            + [L(3.8, y, c, 0.45, 0.5) for y, c in ((1.65, G_LIME), (2.8, G_YEL), (3.75, G_PINK))]
            + [L(1.5, 5.5, G_COOL, 0.6, 0.4), L(2.85, 5.4, G_WARM, 0.9, 0.6)]),
     'A second, broader tenant building in dark teal tile, five floors (MANZAI HALL, JAZZ KISSA, UDON, '
     'RECORDS, BAR TAKO), blade signs down both edges (yakitori, BAR, ramen; SAKE, JAZZ, tako), NAMBA '
     'between two stars in bulbs on the roof, a glass door (second cell) and a lit shop at the foot.'),
    ('osaka-boat-pier_0_0', boat_pier, (3, 3), DB, dict(
        solid=[[0, 1], [1, 1], [0, 2], [1, 2]], walk=[[2, 2]],
        lit=[L(1.05, 0.4, 0xdfeaff, 0.9, 0.5, ry=0.4), L(0.72, 1.75, G_WARM, 0.6, 0.6), L(1.53, 1.72, 0xbfe4ff, 0.35, 0.5),
             L(2.15, 1.65, G_WARM, 0.35, 0.7), L(2.87, 1.65, G_WARM, 0.35, 0.7)]),
     'The river cruise\'s booth on the quay: a wheelhouse of a hut with a yellow barrel roof, BOAT in white '
     'on indigo with bulbs, a clerk at the ticket window, a brass porthole, a lifebuoy, a wave painted round '
     'its skirt; beside it (third column) the gate to the gangway: two yellow and black lamp posts, a '
     'way-down sign, a line of pennants from the booth. Stand its bottom row on the boardwalk row that '
     'edges the water, leave a gap in the rail at the gate, and put osaka-boat-landing directly below.'),
    ('osaka-boat-landing_0_0', boat_landing, (3, 2), DB, dict(
        layer='ground', walk=[[2, 0], [0, 1], [1, 1], [2, 1]]),
     'What the pier\'s gate leads down to, drawn flat for a ground-type layer (the player walks ON it, it '
     'does not Y-sort): in its top row, third column, a steel gangway with cleats and handrail posts that '
     'crosses the quay wall, bright at the quay and in shade lower down; in its bottom row a floating '
     'landing stage at water level with a yellow and black edge, tyre fenders, two bollards and a coil of '
     'line, its shadow and ripples on the water. Place it on the two water rows straight below the pier, '
     'column for column; the other two cells of its top row are clear (quay wall and water show). The berth '
     'is the water row below it or the cells west of the stage: moor osaka-river-boat there.'),
    ('osaka-river-boat_0_0', river_boat, (4, 2), DB, dict(
        solid=rows(4, 1, 1), lit=[L(2.1, 0.7, G_WARM, 1.6, 0.45, ry=0.4)]),
     'The sightseeing boat, moored: a long low yellow hull with an indigo waterline and NANIWA MARU on its '
     'side, red benches and passengers on an open deck under a flat white canopy hung with lanterns, the '
     'skipper in a wheelhouse at the stern, a red flag at the bow, its own shadow and ripples. Static '
     'scenery for the berth; the passing boats on the declared waterway are a separate, existing system.'),
    ('osaka-neon-lanterns_0_0', neon_pole, (1, 3), DB, dict(solid=[[0, 2]]),
     'A pole of five small neon signs (single characters in pink, yellow, cyan, green, red) under a lamp. '
     'Its key holds -lanterns, so DayNight gives it a halo with no data. Use sparingly: one or two a street.'),
    ('osaka-canal-rail_0_0', canal_rail, (1, 1), DB, dict(solid=[[0, 0]], lit=[L(0.5, 0.5, 0xffd9a0, 0.5, 0.3)]),
     'The canal\'s railing, span: low and open (two rails and a wire, one slim stanchion) so the water and '
     'anyone behind it show, under a sagging string of coloured bulbs. Tiles east-west with itself and '
     'with the post piece.'),
    ('osaka-canal-rail-post_0_0', lambda: canal_rail(True), (1, 1), DB, dict(
        solid=[[0, 0]], lit=[L(0.5, 0.2, G_WARM, 0.6, 0.7)]),
     'The canal\'s railing, post: the same rails with a steel lamp standard that the string of bulbs rises '
     'to. Every third or fourth cell of a run (post, span, span, post ...), and at each end of a gap.'),
    ('osaka-quay-wall_0_0', quay_wall, (1, 1), DB, dict(layer='ground'),
     'The canal\'s embankment, seen from across the water: a pale stone coping, three courses of stone '
     'blocks going green toward the waterline, then the wall\'s shade and a few ripples; the lowest strip of '
     'the cell is clear so the water tile under it shows. A decoration for the FIRST WATER ROW under a '
     'boardwalk\'s south edge (the north bank). The south bank needs none: there you see only the '
     'boardwalk\'s own steel edge.'),
    ('osaka-quay-wall-drain_0_0', lambda: quay_wall(True), (1, 1), DB, dict(layer='ground'),
     'The same wall with a round outfall trickling into the canal and an iron mooring ring: one in every '
     'six or eight cells.'),
    ('osaka-queue-rope_0_0', queue_rope, (1, 1), DB, dict(solid=[[0, 0]]),
     'Brass posts and a red rope, tiling east-west: the queue outside a ramen or takoyaki front.'),
    ('osaka-menu-board_0_0', menu_board, (1, 1), 'any', dict(solid=[[0, 0]]),
     'An A-frame chalk menu board for the pavement.'),
    ('osaka-tsutenkaku_0_0', tsutenkaku, (8, 13), SK, dict(
        solid=[[x, 9] for x in range(2, 6)] + [[x, y] for y in (10, 11) for x in range(1, 7)]
              + [[x, 12] for x in range(8) if x not in (3, 4)],
        walk=[[3, 12], [4, 12]],
        lit=[L(4, 5.5, G_CYAN, 1.0, 0.6, ry=2.2, flicker=True), L(4, 2.4, 0xffd9a0, 1.7, 0.55, ry=0.8),
             L(4, 1.65, G_YEL, 1.3, 0.5, ry=0.4), L(4, 1.25, 0xfff0c0, 0.7, 0.7),
             L(4, 0.28, 0xff4030, 0.4, 0.9, pulse={'period': 2000, 'depth': 0.7}),
             L(4, 8.05, G_WARM, 2.7, 0.6, ry=0.7), L(4, 10.2, 0xffd9a0, 1.7, 0.35)]
            + edge_lights((2.06, 8.9), (0.8, 12.7), 5, G_NEON) + edge_lights((5.94, 8.9), (7.2, 12.7), 5, G_NEON)
            + edge_lights((3.06, 3.6), (2.5, 7.4), 4, G_NEON) + edge_lights((4.94, 3.6), (5.5, 7.4), 4, G_NEON)),
     'Tsutenkaku in shaded steel, to replace the line-art tsutenkaku_0_0 without moving anything: the same '
     '512x832px, anchor, legs, archway, deck, shaft and head at the same pixels, so the placeholder\'s '
     'prefab colliders (given here as solid) and its open archway cells (walk_through) still fit. The '
     'steelwork is OPEN lattice: the ground and whatever stands behind show between the members of the legs '
     'and the shaft (a darker far face behind the near braces), with a line of bulbs down every outer edge. '
     'A steel-rimmed arch with bulbs on concrete footings, a glazed deck with a red fascia under a copper '
     'roof, a neon band reading OSAKA (not the real tower\'s sponsor), a two-storey observation head, a lit '
     'lantern room and a mast with a red lamp. The glow list strings spots down all four edges, so at '
     'night it is a lit outline, not a dark mass.'),
    ('osaka-oni-kushikatsu_0_0', oni_kushikatsu, (4, 5), SK, dict(
        door=[[2, 4]], solid=rows(4, 2, 4),
        lit=[L(2, 2.45, G_RED, 1.7, 0.6, ry=0.5), L(2, 3.05, G_PAPER, 1.8, 0.4, ry=0.4), L(1.05, 4.05, G_WARM, 0.9, 0.6),
             L(2.5, 4.45, G_WARM, 0.7, 0.6), L(2, 1.0, G_RED, 1.3, 0.3)]),
     'Shinsekai\'s kushikatsu shop, a yellow tiled front under a huge scowling mascot: an invented red oni '
     'with a mop of black curls between his horns, fangs up, a tiger skin across his chest and gold '
     'wristbands, a studded iron club in one fist and one giant skewer in the other. The skewer character '
     'and ka-tsu in white on red, a row of lanterns, three customers at the counter, an open doorway with a '
     'parted red noren (third cell), a sauce notice. A folk demon, not the real chain\'s chef.'),
    ('osaka-retro-arcade_0_0', retro_arcade, (4, 5), SK, dict(
        door=[[2, 4]], solid=rows(4, 3, 4),
        lit=[L(2, 2.25, G_YEL, 1.8, 0.6, ry=0.6, flicker=True), L(1.1, 3.9, G_CYAN, 1.0, 0.6), L(1.1, 4.1, G_PINK, 0.9, 0.3),
             L(3.4, 3.7, 0xdff1fb, 0.7, 0.6), L(2.5, 4.2, G_COOL, 0.7, 0.4), L(1.55, 0.35, G_RED, 0.6, 0.4)]),
     'A retro game arcade in violet and pink with a joystick the size of a car on its roof (a red ball on '
     'a steel stick in a dark console, two fat buttons): GAME in bulbs between a pixel heart and an '
     'invented pixel critter, three lit cabinets behind a pink-framed window, glass doors under OPEN, a '
     'crane machine full of prizes.'),
    ('osaka-shooting-gallery_0_0', shooting_gallery, (3, 4), SK, dict(
        solid=rows(3, 2, 3),
        lit=[L(1.5, 1.72, G_PAPER, 1.3, 0.35, ry=0.4), L(1.5, 2.75, G_WARM, 1.4, 0.6, ry=0.7), L(0.8, 0.62, G_RED, 0.7, 0.3)]),
     'A cork-gun shooting gallery in mint-green boards with red trim: a giant red and white target and a '
     'giant cork rifle on the roof, SHATEKI in red on cream, an open stall with prizes and soft toys on '
     'stepped shelves under a string of bulbs, the keeper, rifles and a dish of corks on the counter, red '
     'stars on the counter front. A stall: no door.'),
    ('osaka-shogi-parlour_0_0', shogi_parlour, (3, 4), SK, dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[L(0.5, 1.95, G_WARM, 0.5, 0.5), L(2.5, 1.95, G_WARM, 0.5, 0.5), L(0.6, 3.4, G_WARM, 0.6, 0.6),
             L(1.5, 3.45, G_WARM, 0.7, 0.6)]),
     'A shogi parlour in dark boards under tiled roofs, a giant wooden shogi piece standing through the '
     'eaves with one clean character on it (the king) over a red seal; two players at a board in the '
     'window, an open doorway with a parted brown noren, SHOGI down a paper sign.'),
    ('osaka-tachinomi_0_0', tachinomi, (3, 4), SK, dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[L(2.45, 2.1, G_RED, 0.7, 0.8), L(0.62, 3.2, G_WARM, 0.7, 0.7), L(1.5, 3.45, G_WARM, 0.7, 0.55)]),
     'A standing bar in rusting corrugated tin: TACHINOMI on a red board, two faded posters, a big red '
     'lantern, a tin lean-to over a bar hatch open to the street (bottles, the keeper, mugs) in the first '
     'cell and an open doorway with a parted brown noren and a step in the second, beer crates beside it.'),
    ('osaka-shinsekai-arch_0_0', shinsekai_arch, (5, 4), SK, dict(
        solid=[[0, 3], [4, 3]], walk=[[1, 3], [2, 3], [3, 3]],
        lit=[L(2.5, 0.9, G_RED, 2.4, 0.5, ry=0.7), L(2.5, 1.55, G_PAPER, 2.2, 0.5, ry=0.5), L(2.5, 0.3, G_YEL, 0.5, 0.7)]),
     'The lantern street\'s arch: teal lattice posts, a yellow bowed beam with bulbs along both rims and '
     'SHINSEKAI letter by letter on nine red discs, a starburst on top, eight paper lanterns on a wire '
     'beneath. Walk through its three middle cells; only the post cells are solid.'),
    ('osaka-lucky-idol_0_0', lucky_idol, (2, 3), SK, dict(
        solid=[[0, 2], [1, 2]], lit=[L(1, 1.3, G_YEL, 0.9, 0.25)]),
     'Shinsekai\'s own lucky idol, invented: Fuku-san, a round gold owl painted like a daruma (great round '
     'eyes under sweeping black brows, ear tufts, an orange beak, a red bib), its feathered belly rubbed '
     'bright, on a stone plinth with a red cloth and a plaque reading fu-ku. Neither a beckoning cat nor '
     'the real seated imp. A thing to bump (rub its belly for luck).'),
    ('osaka-fugu-lantern_0_0', fugu_lantern, (2, 3), SK, dict(
        solid=[[0, 2]], walk=[[1, 2]], lit=[L(1.2, 1.35, 0xffe0a0, 1.1, 0.9)]),
     'A giant paper pufferfish hung from a post\'s bracket: spikes all round, a lit cream belly under a '
     'brown spotted back, big eyes, pouting lips, a red tassel. Only the post\'s cell is solid; you walk '
     'under the fish. For a street corner; over a shopfront use osaka-fugu-sign.'),
    ('osaka-fugu-sign_0_0', fugu_sign, (2, 2), SK, dict(
        walk=[[0, 1], [1, 1]], lit=[L(1.03, 0.9, 0xffe0a0, 1.0, 0.9)]),
     'The same pufferfish for a shopfront: hung from an iron wall bracket, no post, nothing solid. Overlay '
     'it on a front\'s upper rows (it is drawn over the tachinomi in the preview) on a layer above the building.'),
    ('osaka-gacha-row_0_0', gacha_row, (2, 2), SK, dict(
        solid=[[0, 1], [1, 1]], lit=[L(1, 1.1, 0xdff1fb, 1.0, 0.35)]),
     'Eight capsule machines, two high and four across, each its own colour, under a GACHA board.'),
    ('osaka-gacha-single_0_0', gacha_single, (1, 2), SK, dict(solid=[[0, 1]], lit=[L(0.5, 1.1, 0xdff1fb, 0.6, 0.35)]),
     'Two capsule machines, one on the other: ends a row, or stands by a shop door.'),
    ('osaka-shinsekai-lanterns_0_0', shinsekai_lanterns, (1, 2), SK, dict(solid=[[0, 1]]),
     'A timber post of four paper lanterns (three white, one red). Its key holds -lanterns, so DayNight '
     'gives it a halo with no data: the lantern street\'s lamp.'),
    ('osaka-beer-crates_0_0', beer_crates, (1, 1), 'any', dict(solid=[[0, 0]]),
     'Empties out the back of a bar: three bottle crates (yellow, red on top of it, teal beside), hand '
     'holes and ribs, brown bottles with gold caps standing in two of them.'),
]
FAMILIES = [
    ('osaka-boardwalk-autotile', DB,
     "The canal promenade: dark ironwood planks running east-west, one butt joint a row stepped from row "
     "to row so none line up, screw heads, a steel edge with footlight studs. (Sendai's boardwalk is pale "
     "and runs north-south.)"),
    ('osaka-retro-paving-autotile', SK,
     "Shinsekai's retro tiled paving: an 8px checker of cream and dusty rose, a teal inset where four "
     'tiles meet, a dark red tile border. In place of the brown brick there.'),
]
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


SCENES = ('station', 'dotonbori', 'shinsekai')


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
        assert all(isinstance(s['color'], int) and 0 <= s['x'] <= w and 0 <= s['y'] <= h for s in m.get('lit', [])), key
        sprites.append({
            'key': key, 'file': f'gamev2/{SPR}/{key}.png', 'size': [w, h], 'px': list(im.size),
            'anchor': [round(32 / im.width, 6), round(32 / im.height, 6)],
            'door': doors[0] if doors else None, 'doors': doors,
            'solid': solid, 'walk_through': m.get('walk', []),
            'night_halo': halo(key),
            'glow': m.get('lit', []),
            'layer': m.get('layer', 'standing'),
            'district': district, 'description': desc,
        })
    doc = {
        'tool': 'gamev2/tools/generate_osaka_art.py',
        'run': 'cd gamev2 && /Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_osaka_art.py '
               '[--sheet out.png] [--scenes dir] [--manifest out.json]   (any python3 with Pillow; plain python3 here '
               'has none. Imports generate_hokkaido, generate_sapporo_art, generate_kanazawa_art from tools/; '
               '--sheet and --scenes also read existing sprites from assets/sprites/, so run it in the repo)',
        'notes': [
            "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per "
            "cell and pixel-doubled, as generate_sapporo_art.py does); 'size' is in cells.",
            'Nothing is registered: config.json, tilePalette, spriteMetadata, tileNames, prefabs, generators, '
            'check_generators.py and docs are untouched, and the tool does not write config.json. To register a '
            'multi-cell sprite follow generate_sapporo_art.register: spriteMetadata {frameCount:1, anchorX: '
            "32/widthPx, anchorY: 32/heightPx} (centre of the top-left cell; that is 'anchor'); 1x1 tiles use "
            '0.5/0.5. The map change should also add the tool to check_generators.py.',
            "'doors' (every door cell; 'door' is the first), 'solid' and 'walk_through' are [col,row] from the "
            "sprite's top-left cell. 'solid' is the suggested footprint (rows above it are roof, sign or mascot "
            "the player walks behind). 'walk_through' lists cells of the sprite's own rows that stay walkable: "
            "under the arch, in Tsutenkaku's archway mouth, under the hanging pufferfish, the pier's gate, the "
            'landing stage. Every door is drawn as a door: glass leaves, or an open doorway with a parted noren '
            'and a stone step. The takoyaki stand and the shooting gallery are counters with no door.',
            "'layer': 'standing' is Y-sorted art for a Collidables-type layer. 'ground' (osaka-boat-landing, the "
            'two osaka-quay-wall pieces) is flat art for a layer under the player, laid over the water tiles.',
            "Night: 'night_halo' is true for the two keys that match DayNight's /lamp-post|-lanterns/ rule "
            '(osaka-neon-lanterns for Dotonbori, osaka-shinsekai-lanterns for Shinsekai): they get the lamp halo '
            "with no further data. 'glow' is each other sprite's lit parts as glow spots in the shape "
            "src/utils/Glows.js reads ({x, y, r, ry?, color, a, flicker?, pulse?}: centre in cells from the "
            "sprite's top-left, radius in cells; 'color' is a NUMBER, 0xRRGGBB in decimal): copy the list into "
            "the sprite's spriteMetadata `glow` when it is registered. The billboard, the arcade marquee, the two "
            "roof signs and the tower's neon band flicker; the mast lamp pulses. All of it was checked only in the "
            'Pillow night previews (previews.night), which ignore ry / flicker / pulse, NOT in the running game.',
            'Season: mid November (the posts are 13-16 Nov 2025): no snow anywhere.',
            'Every sign word is generic or invented: OSAKA, BAKERY, TICKETS, CAFE, BENTO, WHEEL PLAZA, SEAFOOD, '
            'GYOZA, NANIWA (an old name for the city), DASH!, NANIWA DINER, RAMEN, OKONOMI, BOAT, NANIWA MARU, '
            'MINAMI and NAMBA (districts), the tenants on the two sign towers, GAME, OPEN, SHATEKI, SHOGI, '
            'TACHINOMI, GACHA, SHINSEKAI, and kana for crab, takoyaki, ramen, yakitori, kushi-katsu, sauce, '
            'fu-ku. No real brand artwork: the crab is a riveted machine with steel joints, the athlete is a '
            'hurdler in teal and yellow at dusk (not the running man on his blue track), the kushikatsu mascot '
            'is a red oni with a club and a tiger skin (not the scowling chef), the idol is a gold owl painted '
            'as a daruma (neither the imp nor a beckoning cat), the dragon is blue with a pink mane (not the '
            'gold one), the octopus wears a headband (Don Takote\'s is a small red one on a sign), the wheel is '
            'an invented mall\'s, and the tower\'s band reads OSAKA.',
            'Tsutenkaku: osaka-tsutenkaku_0_0 is drawn over generate_tsutenkaku.py\'s own coordinates (512x832, '
            'anchor 0.0625 / 0.0385). To swap it in, point the tsutenkaku prefab in make_prefabs.py at the new '
            'key (colliders unchanged) and retire the placeholder\'s palette slot as a dead entry. Its lattice '
            'is see-through, so what is behind it (paving, a far shop) is visible between the members.',
            'Dotonbori as drawn in the preview, north to south: the wall of fronts (mascot shops with the two '
            'sign towers and the billboard between them, so the skyline steps up and down), a three-row '
            'boardwalk, the rail on its last row (post, span, span ...; a gap at the pier\'s gate), '
            'osaka-quay-wall on the first water row, water, and the south bank\'s boardwalk. The pier stands on '
            'the boardwalk with its bottom row on the rail\'s row; the landing is on the two water rows below it '
            'and the boat is moored west of the landing stage. The fronts\' top rows (mascots) overhang whatever '
            'is north of them, so keep two free rows behind a front or back it onto another building. The '
            'existing canal bridge and the passing boats of the declared waterway are meant to be kept.',
            'Kept clear of the other kits: Sapporo owns the fox neon corner (a billboard over a grid of small '
            'signs), the ramen gate, the covered arcade, a flat crab on an arcade shop sign and a station that '
            'is a clock over a name on a glass grid; Sendai the glass arcade, tanabata and the pale north-south '
            'boardwalk; Kanazawa the lattice fronts and andon posts. Osaka\'s station is a roof, its neon is '
            'stacked tenant floors and blade signs, its mascots are three-dimensional.',
            'Dropped in the second pass: osaka-kushikatsu-front_0_0 (it repeated Shinsekai\'s shop); its place '
            'in Dotonbori is taken by osaka-okonomiyaki-front_0_0.',
        ],
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/osaka_art_sheet.png',
            'scenes': [f'.agent-queue/shots/osaka_art_{n}.png' for n in SCENES],
            'night': [f'.agent-queue/shots/osaka_art_{n}_night.png' for n in SCENES],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


# ---- previews (not part of the game) --------------------------------------------
# These read sprites that are already in assets/sprites/ (ground tiles, water, the
# player, existing buildings), so --sheet and --scenes only work inside the repo.
GRID = ('corner-nw', 'edge-n', 'corner-ne', 'edge-w', 'center', 'edge-e', 'corner-sw', 'edge-s', 'corner-se')


def spr(name):
    return Image.open(f'{SPR}/{name}.png').convert('RGBA')


def rail_run(xs):
    """The rail pieces for a run of cells: a post at each end and every third cell."""
    xs = list(xs)
    return [(x, 'osaka-canal-rail-post_0_0' if (i % 3 == 0 or i == len(xs) - 1) else 'osaka-canal-rail_0_0')
            for i, x in enumerate(xs)]


class Scene:
    def __init__(self, built, w, h, ground_='grey-brick-autotile_center'):
        self.b, self.w, self.h = built, w, h
        self.im = Image.new('RGBA', (w * 64, h * 64), CLEAR)
        g = self.get(ground_)
        for y in range(h):
            for x in range(w):
                self.im.alpha_composite(g, (x * 64, y * 64))
        self.things = []

    def get(self, name):
        return self.b[name] if name in self.b else spr(name)

    def floor(self, fam, *rects):
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
        """Lay a ground-layer piece with its top-left cell at (x, y)."""
        self.im.alpha_composite(self.get(name), (x * 64, y * 64))

    def road(self, y, x0, x1):
        for x in range(x0, x1 + 1):
            self.fill('road-edge-top_0_0', x, y, x, y)
            self.fill('road-div-horizontal_0_0', x, y + 1, x, y + 1)
            self.fill('road-edge-bottom_0_0', x, y + 2, x, y + 2)

    def put(self, name, x, base, over=0):
        """Stand a sprite with its left edge on cell x and its feet on row `base`
        (`over` > 0 draws it after everything on that row: a wall-hung sign)."""
        self.things.append((base, over, x, name))

    def save(self, out):
        halos = []
        for base, _over, x, name in sorted(self.things):
            im = self.get(name)
            top = (base + 1) * 64 - im.height
            self.im.alpha_composite(im, (x * 64, top))
            for s in META.get(name, {}).get('lit', []):
                halos.append((x * 64 + s['x'] * 64, top + s['y'] * 64, s['r'] * 64, s['color'], s['a']))
            if halo(name):                                        # DayNight's own lamp halo, on the top cell
                halos.append((x * 64 + 32, top + 32 - 64 * 0.15, 64 * 1.6, 0xffb366, 1.0))
        self.im.save(out)
        print('scene ->', out, self.im.size)
        night(self.im, halos).save(out[:-4] + '_night.png')


def sheet(built, out):
    """Everything on one sheet at the file's size, doubled: the pieces in rows,
    each ground family as a 3x3 patch, the rail on the quay over the water, the
    rope in a run."""
    keys = [k for k, *_ in PIECES]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1720 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + 64 * 3 + 60
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
    for fam, *_ in FAMILIES:
        for i, r in enumerate(GRID):
            im.alpha_composite(built[f'{fam}_{r}'], (x + (i % 3) * 64, y + (i // 3) * 64))
        x += 3 * 64 + 24
    water = spr('pond-autotile_center')                           # the quay: boardwalk, rail, wall, water
    for i, (_x, rail) in enumerate(rail_run(range(7))):
        im.alpha_composite(built['osaka-boardwalk-autotile_edge-s'], (x + i * 64, y))
        im.alpha_composite(water, (x + i * 64, y + 64)); im.alpha_composite(water, (x + i * 64, y + 128))
        im.alpha_composite(built['osaka-quay-wall-drain_0_0' if i == 4 else 'osaka-quay-wall_0_0'], (x + i * 64, y + 64))
        im.alpha_composite(built[rail], (x + i * 64, y))
    x += 7 * 64 + 24
    for i in range(3):
        im.alpha_composite(built['osaka-retro-paving-autotile_center'], (x + i * 64, y + 64))
        im.alpha_composite(built['osaka-queue-rope_0_0'], (x + i * 64, y + 64))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    # Station front: the station and the wheel across a concrete plaza, beside a tower the plan keeps, the road
    s = Scene(built, 25, 14, 'light-concrete-autotile_center')
    s.road(11, 0, 24)
    s.put('highrise-yellow_0_0', 0, 8); s.put('osaka-station-front_0_0', 5, 8); s.put('osaka-wheel-mall_0_0', 17, 8)
    s.put('blue-lamp-post_0_0', 4, 10); s.put('blue-lamp-post_0_0', 15, 10)
    s.put('osaka-menu-board_0_0', 13, 9)
    s.put(me, 9, 9); s.put(me, 10, 10); s.put(me, 3, 10); s.put(me, 19, 9); s.put(me, 12, 13); s.put(me, 7, 9)
    s.save(f'{outdir}/osaka_art_station.png')
    # Dotonbori: the wall of fronts on the north bank beside the discount store that is already there, the
    # boardwalk with its rail, the quay wall, the canal, the pier with its landing and the boat, the south bank
    s = Scene(built, 39, 20)
    s.floor('osaka-boardwalk-autotile', (0, 9, 38, 11), (0, 17, 38, 18))
    s.fill('pond-autotile_center', 0, 12, 38, 16)
    for x in range(39):
        s.flat('osaka-quay-wall-drain_0_0' if x % 7 == 3 else 'osaka-quay-wall_0_0', x, 12)
    x = 0
    for name, w in (('osaka-sign-tower-a_0_0', 3), ('osaka-crab-restaurant_0_0', 4), ('osaka-takoyaki-stand_0_0', 4),
                    ('osaka-sprinter-billboard_0_0', 6), ('osaka-dragon-ramen_0_0', 4), ('osaka-sign-tower-b_0_0', 4),
                    ('osaka-gyoza-izakaya_0_0', 4), ('osaka-okonomiyaki-front_0_0', 3), ('osaka-neon-lanterns_0_0', 1),
                    ('discount-store_0_0', 5)):
        s.put(name, x, 8); x += w
    for x, rail in rail_run(range(0, 20)) + rail_run(range(23, 39)):
        s.put(rail, x, 11)
    s.put('osaka-boat-pier_0_0', 20, 11)
    s.flat('osaka-boat-landing_0_0', 20, 12)
    s.put('osaka-river-boat_0_0', 16, 13)
    s.put('osaka-queue-rope_0_0', 11, 9); s.put('osaka-queue-rope_0_0', 12, 9); s.put('osaka-menu-board_0_0', 27, 9)
    s.put('osaka-menu-board_0_0', 4, 9)
    s.put(me, 1, 9); s.put(me, 5, 9); s.put(me, 8, 10); s.put(me, 14, 9); s.put(me, 16, 11); s.put(me, 19, 9)
    s.put(me, 26, 11); s.put(me, 30, 9); s.put(me, 33, 10); s.put(me, 22, 11); s.put(me, 21, 13); s.put(me, 25, 17)
    s.save(f'{outdir}/osaka_art_dotonbori.png')
    # Shinsekai: Tsutenkaku on its paving at the head of the lantern street, the shops either side, the arch
    s = Scene(built, 27, 19)
    s.floor('osaka-retro-paving-autotile', (0, 9, 26, 18))
    s.put('osaka-tsutenkaku_0_0', 8, 13)
    s.put('osaka-oni-kushikatsu_0_0', 0, 12); s.put('osaka-shogi-parlour_0_0', 4, 12)
    s.put('osaka-retro-arcade_0_0', 16, 12); s.put('osaka-shooting-gallery_0_0', 20, 12); s.put('osaka-tachinomi_0_0', 23, 12)
    s.put('osaka-fugu-sign_0_0', 25, 11, over=1)
    s.put('osaka-shinsekai-lanterns_0_0', 7, 13); s.put('osaka-shinsekai-lanterns_0_0', 16, 14)
    s.put('osaka-gacha-row_0_0', 20, 16); s.put('osaka-gacha-single_0_0', 22, 16); s.put('osaka-beer-crates_0_0', 26, 13)
    s.put('osaka-lucky-idol_0_0', 3, 15); s.put('osaka-fugu-lantern_0_0', 16, 17)
    s.put('osaka-shinsekai-arch_0_0', 9, 17)
    s.put('osaka-shinsekai-lanterns_0_0', 7, 17); s.put('osaka-shinsekai-lanterns_0_0', 15, 17)
    s.put('osaka-menu-board_0_0', 1, 13)
    s.put(me, 11, 13); s.put(me, 12, 12); s.put(me, 2, 14); s.put(me, 5, 13); s.put(me, 18, 14); s.put(me, 24, 13)
    s.put(me, 11, 17); s.put(me, 21, 17); s.put(me, 6, 16); s.put(me, 13, 15); s.put(me, 21, 13); s.put(me, 10, 11)
    s.save(f'{outdir}/osaka_art_shinsekai.png')


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
