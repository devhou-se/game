#!/usr/bin/env python3
"""generate_temple_art.py — everything inside a temple's main hall (issue #213;
the first one is Senso-ji's, tools/generate_temple.py). The GuttyKreum temple
packs are exteriors only, so the interior is drawn here, in the manner of
tools/generate_shrine_art.py and generate_palace_art.py: shaded pixel art with
a 1px outline in the pack's temple navy, drawn at half size (32px a cell) and
pixel-doubled. Every colour is one the GuttyKreum sheets use (PACK; settle()
moves anything else, a ramp or a blended edge, to the nearest one), and a lamp
or flame is the pack's dim gold with a small pale core, never lit yellow: the
glow at night is src/utils/Glows.js's (#326). Nothing
is line art, nothing is random between runs (every scatter is seeded), and the
only text is set in the game's own font, so a re-run is byte-identical on any
machine. All lettering is invented or generic (no sponsor's name is on the
great lantern).

The hall is a Buddhist hondo, not a shrine's worship hall and not the palace:
dim, dark red lacquer and old gold, bronze, stone underfoot, incense in the air.
All sprites are `temple-in-<piece>`:
  slab-a / slab-b         the outer hall's worn stone floor
  side-w / side-e         the side walls seen along their length: slatted windows
  sun-w / sun-e           2x1 thin daylight through those slats (lies flat)
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-charms             4x3 back wall, west aisle: the charm counter (omamori) under its shelves
  wall-tennin-l / -r      5x3 back wall behind the sanctum: old gold panels, a heavenly
                          maiden on each, brocade banners, hung lanterns
  kuden                   6x3 the sanctum's shrine cabinet: the golden canopy (tengai), the
                          seated Kannon half-hidden behind brocade curtains
  omikuji                 4x3 back wall, east aisle: the hundred-drawer fortune cabinet and
                          its shaker cylinder (bump it: src/TempleVisit.js)
                          (every back-wall piece carries the edge of the coffered, painted
                          ceiling and a frieze; over the sanctum the frieze is two dragons)
  naijin                  16x4 the inner sanctum behind its gilt lattice: altar, banked
                          candles, lotus stands, the monk's seat; the lattice is open in
                          the middle over a low rail
  pillar                  1x3 dark red lacquer column: only its foot is solid
  saisen                  4x2 the offering box (bump it)
  jokoro                  4x3 the great bronze incense burner and its smoke (bump it)
  chochin                 4x3 the great red paper lantern hung inside the doors (Tops)
  toro-hang               1x2 hung gilt lantern (Tops);  shokudai: 1x2 candle on a tall stand
  candles                 2x2 a rack of votive candles
  drum                    2x2 the great drum on its stand;  keisu: 2x2 the bowl bell on its cushion
  musubi                  2x2 the rail the unlucky fortunes are tied to
  bench                   2x1 a visitors' bench;  renge: 1x2 a bronze vase of gilt lotus
  haze                    3x2 incense haze hanging in the air (Tops)

Run from gamev2/:  python3 tools/generate_temple_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFont

C = 32      # canvas px per cell (doubled on save)

def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; temple.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy
VOID = rgb('080d16')
SHADE = rgb('080d16')                    # shadows and the lattice veil, with alpha
DAY = rgb('e4cecc')                      # daylight: slats' sun, the doorway, with alpha
WHITE, PAPER, PAPER_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('be9e8c')
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')   # a pane; its core
FLAME, FLAME_HI = rgb('c6a663'), rgb('f3d890')
LQ, LQ_HI, LQ_DK = rgb('2a2636'), rgb('524b59'), rgb('171831')                    # black lacquer
RED, RED_HI, RED_DK = rgb('8a3a22'), rgb('aa4d31'), rgb('5b283b')                 # old dark red lacquer
VERM, VERM_HI, VERM_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31')              # the lantern's paper
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')              # gilt
LEAF_A, LEAF_B, LEAF_C = rgb('a7843b'), rgb('b2a168'), rgb('a7843b')              # old gold leaf, in shadow
STONE, STONE_ALT, STONE_HI, STONE_DK = rgb('443d4a'), rgb('4c4754'), rgb('655d6d'), rgb('322b38')
STONE_GLINT = rgb('826f60')
WOOD, WOOD_HI, WOOD_DK = rgb('6d483b'), rgb('85553e'), rgb('4d3326')
BRONZE, BRONZE_HI, BRONZE_DK = rgb('506b6b'), rgb('6c8e7f'), rgb('2e4040')        # patinated
BRASS, BRASS_HI, BRASS_DK = rgb('c6aa71'), rgb('e3c587'), rgb('86624c')
PURPLE, PURPLE_HI, PURPLE_DK = rgb('5c527d'), rgb('8f72b6'), rgb('3f3651')
TATAMI, TATAMI_HI, TATAMI_DK = rgb('716555'), rgb('928372'), rgb('584a43')
SKIN, SKIN_SH = rgb('ebbca2'), rgb('c69f96')
TEAL, TEAL_HI = rgb('3f827f'), rgb('6c8e7f')
PINK, PINK_HI = rgb('bb6479'), rgb('d78bc1')
LOTUS_G, LOTUS_G_HI = rgb('506d33'), rgb('83af6f')
SMOKE = rgb('d0ccdc')
# the rest of what settle() may leave in a sprite: frieze grounds, steel, ash, fruit, the bowl bell, charms
PACK_MORE = [rgb(h) for h in (
    '514542 232446 2d4051 35444a c66347 d7d0ba 20212a 413130 6b5241 3a5252 b0c276 e77f6a db785c 6b7d9a '
    '949494 949bb2 6d574e 433830 1b1e2a aaaaaa adb2c2 4a6262 dedede 7f513b 3a5792 dfdfdf f27e66 95402c '
    'e6d6cd d7af9e efefef 3a3b54 726f86 dae2e4 747e93 e75d42 8fb2b0 9599bb ebebe9 201c2d 76cae3').split()]
# the closed list settle() moves every pixel onto: the constants above, in order, then PACK_MORE
PACK = list(dict.fromkeys([
    INK, VOID, SHADE, DAY, WHITE, PAPER, PAPER_SH, LAMP, LAMP_SH, LAMP_HI, FLAME, FLAME_HI,
    LQ, LQ_HI, LQ_DK, RED, RED_HI, RED_DK, VERM, VERM_HI, VERM_DK, GOLD, GOLD_HI, GOLD_DK,
    LEAF_A, LEAF_B, LEAF_C, STONE, STONE_ALT, STONE_HI, STONE_DK, STONE_GLINT, WOOD, WOOD_HI, WOOD_DK,
    BRONZE, BRONZE_HI, BRONZE_DK, BRASS, BRASS_HI, BRASS_DK, PURPLE, PURPLE_HI, PURPLE_DK,
    TATAMI, TATAMI_HI, TATAMI_DK, SKIN, SKIN_SH, TEAL, TEAL_HI, PINK, PINK_HI, LOTUS_G, LOTUS_G_HI, SMOKE,
] + PACK_MORE))
PACK_SET = set(PACK)

_FONTS = {}


def kana(size=12):
    if size not in _FONTS:
        _FONTS[size] = ImageFont.truetype('fonts/PixelMplus12-Grid.ttf', size)
    return _FONTS[size]


def new(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'        # no anti-aliasing: pixel fonts stay pixels
    return im, d


def box(d, x0, y0, x1, y1, fill, outline=INK):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)


def text(d, x, y, s, f, fill):
    """Text with its top-left ink pixel at (x, y), whatever the font's bearings."""
    l, t, _, _ = d.textbbox((0, 0), s, font=f)
    d.text((x - l, y - t), s, font=f, fill=fill)


def text_w(d, s, f):
    l, _, r, _ = d.textbbox((0, 0), s, font=f)
    return r - l


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bar(d, x0, y0, x1, y1, base, hi, dk, outline=True):
    """A horizontal timber: lit along the top, shaded along the bottom."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0, y0 + (1 if outline else 0), x1, y0 + (1 if outline else 0)], fill=hi)
    d.line([x0, y1 - (1 if outline else 0), x1, y1 - (1 if outline else 0)], fill=dk)
    if outline:
        d.rectangle([x0, y0, x1, y1], outline=INK)


def post(d, x0, y0, x1, y1, base, hi, dk, outline=True):
    """An upright timber: lit down its left side, shaded down its right."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0 + (1 if outline else 0), y0, x0 + (1 if outline else 0), y1], fill=hi)
    d.line([x1 - (1 if outline else 0), y0, x1 - (1 if outline else 0), y1], fill=dk)
    if outline:
        d.rectangle([x0, y0, x1, y1], outline=INK)


def shadow(d, x0, y0, x1, y1, a=90):
    d.ellipse([x0, y0, x1, y1], fill=SHADE + (a,))


def stud(d, x, y):
    """A gilt nail cover, 3x3."""
    d.rectangle([x, y, x + 2, y + 2], fill=GOLD)
    d.point((x, y), fill=GOLD_HI)
    d.point((x + 2, y + 2), fill=GOLD_DK)


def flame(d, x, y):
    """A candle flame, its base at (x, y): 3 wide, 5 tall."""
    d.line([x, y - 4, x, y], fill=FLAME)
    d.line([x - 1, y - 2, x - 1, y], fill=FLAME)
    d.line([x + 1, y - 2, x + 1, y], fill=FLAME)
    d.line([x, y - 2, x, y], fill=FLAME_HI)


def candle(d, x, y, h=6):
    """A candle standing on (x, y) with its flame: 2 wide."""
    d.rectangle([x, y - h, x + 1, y], fill=WHITE)
    d.line([x + 1, y - h, x + 1, y], fill=PAPER_SH)
    flame(d, x, y - h - 1)


def old_gold(d, x0, y0, x1, y1, seed):
    """A ground of old gold leaf seen in a dim hall: squares of dull gold, as laid."""
    rnd = random.Random(seed)
    d.rectangle([x0, y0, x1, y1], fill=LEAF_A)
    for y in range(y0, y1 + 1, 8):
        for x in range(x0 - (4 if (y // 8) % 2 else 0), x1 + 1, 8):
            col = rnd.choice((LEAF_A, LEAF_A, LEAF_B, LEAF_C))
            d.rectangle([max(x, x0), y, min(x + 7, x1), min(y + 7, y1)], fill=col)
            if rnd.random() < 0.22:
                d.point((min(max(x + rnd.randrange(8), x0), x1), min(y + rnd.randrange(8), y1)), fill=GOLD)


def lotus(d, cx, y, col=PINK, hi=PINK_HI):
    """A lotus flower seen from the side, 9 wide, its base at (cx, y)."""
    d.polygon([(cx - 4, y - 3), (cx - 2, y), (cx + 2, y), (cx + 4, y - 3), (cx + 2, y - 2), (cx, y - 5), (cx - 2, y - 2)],
              fill=col)
    d.line([cx, y - 5, cx, y - 1], fill=hi)
    d.point((cx - 3, y - 2), fill=hi)
    d.point((cx + 3, y - 2), fill=hi)


# ---- floors -----------------------------------------------------------------------

def slab(seed):
    """Worn stone, two slabs a cell each way; the lamps catch in it here and there."""
    def draw():
        rnd = random.Random(seed)
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=STONE)
        for i, (x0, y0) in enumerate(((0, 0), (16, 0), (0, 16), (16, 16))):
            if (i + seed) % 3 == 0:
                d.rectangle([x0, y0, x0 + 15, y0 + 15], fill=STONE_ALT)
            d.line([x0, y0, x0 + 15, y0], fill=STONE_DK)
            d.line([x0, y0, x0, y0 + 15], fill=STONE_DK)
            d.line([x0 + 2, y0 + 1, x0 + 2 + rnd.randrange(4, 10), y0 + 1], fill=STONE_HI)     # a worn edge
            for _ in range(3):
                d.point((x0 + 2 + rnd.randrange(13), y0 + 3 + rnd.randrange(12)), fill=STONE_DK)
            if rnd.random() < 0.6:                                                             # lamplight
                gx, gy = x0 + 4 + rnd.randrange(8), y0 + 5 + rnd.randrange(8)
                d.line([gx, gy, gx + 2, gy], fill=STONE_GLINT)
        return im
    return draw


def wall_side(side):
    """A side wall seen along its length from above: the wall's dark head, then
    a sliver of its slatted window (renji-mado), a little day between the slats."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        d.rectangle([12, 0, 21, 31], fill=LQ)                   # the head rail
        d.line([13, 0, 13, 31], fill=LQ_HI)
        d.rectangle([22, 0, 29, 31], fill=RED_DK)               # the wall below it
        d.line([22, 0, 22, 31], fill=INK)
        for y in range(1, 31, 3):                               # the slats, foreshortened
            d.line([24, y, 28, y], fill=PAPER_SH)
        d.rectangle([30, 0, 31, 31], fill=WOOD_DK)              # the sill
        d.line([30, 0, 30, 31], fill=INK)
        d.rectangle([22, 14, 31, 17], fill=RED)                 # a post
        d.line([22, 14, 31, 14], fill=RED_HI)
        d.line([22, 17, 31, 17], fill=INK)
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def sun(side):
    """Thin daylight through the slats, lying across the stone (2x1): faint
    bars, strongest by the wall. The hall stays dim."""
    def draw():
        im, d = new(2 * C, C)
        for y in range(4, 30):
            if (y - 4) % 6 >= 3:
                continue                                         # the shadow of a slat
            reach = 56 - (y - 4)
            for x in range(0, reach):
                a = round(64 * (1 - x / 60) ** 1.6)
                if a > 3:
                    im.putpixel((x, y), DAY + (a,))
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def wall_front():
    """The front wall from inside: all you see is its head; below it is dark."""
    im, d = new(C, C)
    d.rectangle([0, 0, 31, 31], fill=VOID)
    bar(d, -1, 0, 32, 9, LQ, LQ_HI, LQ_DK)
    d.rectangle([0, 10, 31, 16], fill=RED_DK)
    d.line([0, 16, 31, 16], fill=INK)
    d.line([0, 5, 31, 5], fill=GOLD_DK)
    for x in (7, 23):
        stud(d, x, 3)
    return im


def threshold(side):
    def draw():
        im, d = new(C, C)
        for y in range(0, 32):
            d.line([0, y, 31, y], fill=DAY if y in (0, 1, 2, 3, 5, 8) else WHITE)   # the day outside
        d.line([0, 10, 31, 10], fill=PAPER_SH)                   # the stone steps
        d.line([0, 22, 31, 22], fill=PAPER_SH)
        x0 = 0 if side == 'w' else 26                            # the door post
        post(d, x0, -1, x0 + 5, 32, RED, RED_HI, RED_DK)
        d.rectangle([x0, 0, x0 + 5, 6], fill=LQ)
        d.line([x0, 7, x0 + 5, 7], fill=GOLD)
        d.line([x0, 0, x0, 31], fill=INK)
        d.line([x0 + 5, 0, x0 + 5, 31], fill=INK)
        return im
    return draw


def doorlight():
    """Daylight falling in through the doors: 2x3, on the floor, strongest at the sill."""
    im, d = new(2 * C, 3 * C)
    for y in range(96):
        t = y / 95
        inset = round((1 - t) * 14)
        a = round(110 * t * t)
        if a:
            d.line([inset, y, 63 - inset, y], fill=DAY + (a,))
    return im


# ---- the back wall ------------------------------------------------------------------

BACK_W = 24 * C     # the back wall is one picture 24 cells long; each piece is a cut of it
HEAD = 30           # px of every back-wall piece that is ceiling edge, frieze and beam
_frieze = None


def _dragon(d, x0, x1, y, facing):
    """A dragon along a frieze from its tail at x0 to its head at x1 (`facing`
    1: head to the right). Dull gold-green on the dark ground, a hint, not a poster."""
    body, hi, dk = rgb('6c8e7f'), rgb('b0c276'), rgb('3a5252')
    n = abs(x1 - x0)
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + facing * i
        yy = y + math.sin(t * math.pi * 3.4) * 3.6 * (0.55 + 0.45 * t)
        pts.append((x, yy, 1.0 + 2.2 * math.sin(min(1.0, t * 1.25) * math.pi * 0.62)))
    for x, yy, r in pts:                                        # belly, then back
        d.line([x, round(yy - r), x, round(yy + r)], fill=body)
        d.point((x, round(yy + r)), fill=dk)
        d.point((x, round(yy - r)), fill=hi)
    for i, (x, yy, r) in enumerate(pts):
        if i % 4 == 0 and r > 1.6:                              # scales and the spines of its back
            d.point((x, round(yy)), fill=dk)
        if i % 6 == 3 and r > 1.4:
            d.point((x, round(yy - r) - 1), fill=GOLD)
    for t in (0.32, 0.68):                                      # legs, each ending in a claw
        x, yy, r = pts[round(t * n)]
        d.line([x, round(yy + r), x - facing * 2, round(yy + r) + 3], fill=body)
        d.point((x - facing * 3, round(yy + r) + 3), fill=GOLD_HI)
        d.point((x - facing * 1, round(yy + r) + 4), fill=GOLD_HI)
    hx, hy = x1, round(pts[-1][1])                              # the head: jaw, horn, whisker, eye
    d.rectangle([min(hx, hx + facing * 7), hy - 3, max(hx, hx + facing * 7), hy + 2], fill=body)
    d.line([hx + facing * 2, hy - 3, hx + facing * 7, hy - 3], fill=hi)
    d.line([hx + facing * 4, hy + 1, hx + facing * 9, hy + 1], fill=body)
    d.line([hx + facing * 5, hy + 2, hx + facing * 8, hy + 2], fill=rgb('95402c'))
    d.line([hx + facing * 1, hy - 4, hx - facing * 3, hy - 7], fill=GOLD)
    d.line([hx + facing * 3, hy - 4, hx, hy - 6], fill=GOLD_DK)
    d.point((hx + facing * 5, hy - 2), fill=WHITE)
    d.line([hx + facing * 8, hy - 1, hx + facing * 12, hy - 4], fill=GOLD_HI)
    d.line([hx + facing * 8, hy, hx + facing * 11, hy + 4], fill=GOLD_HI)


def _cloud(d, x, y, w, col, hi):
    """A flat painted cloud: a bar with a curl at one end."""
    d.line([x + 2, y, x + w - 3, y], fill=hi)
    d.line([x, y + 1, x + w - 1, y + 1], fill=col)
    d.line([x + 3, y + 2, x + w - 2, y + 2], fill=col)
    d.point((x + w, y), fill=col)
    d.point((x + w - 1, y - 1), fill=hi)


def frieze():
    """The whole back wall's head, one strip BACK_W x HEAD: the edge of the
    coffered ceiling (each coffer a painted flower), a painted frieze - clouds,
    and over the sanctum two dragons either side of a flaming pearl - then the
    beam the wall hangs from."""
    global _frieze
    if _frieze is not None:
        return _frieze
    im, d = new(BACK_W, HEAD)
    rnd = random.Random(213)
    d.rectangle([0, 0, BACK_W - 1, HEAD - 1], fill=LQ_DK)
    grounds = (rgb('2d4051'), rgb('5b283b'), rgb('35444a'))
    flowers = (PINK, GOLD, rgb('dedede'))
    for i, x in enumerate(range(0, BACK_W, 8)):                 # the coffers: 8px, ribbed in lacquer
        d.rectangle([x + 1, 1, x + 7, 7], fill=grounds[i % 3])
        col = flowers[(i * 2 + 1) % 3]
        d.point((x + 4, 3), fill=col)
        d.point((x + 3, 4), fill=col)
        d.point((x + 5, 4), fill=col)
        d.point((x + 4, 5), fill=col)
        d.point((x + 4, 4), fill=GOLD_HI)
        d.line([x, 0, x, 8], fill=LQ)
        d.point((x, 0), fill=GOLD)
        d.point((x, 8), fill=GOLD)
    d.line([0, 0, BACK_W - 1, 0], fill=LQ)
    d.line([0, 8, BACK_W - 1, 8], fill=LQ_HI)
    d.line([0, 9, BACK_W - 1, 9], fill=INK)
    # the frieze: a night-blue ground
    d.rectangle([0, 10, BACK_W - 1, 23], fill=rgb('232446'))
    for x in range(0, BACK_W):
        if rnd.random() < 0.05:
            d.point((x, 11 + rnd.randrange(12)), fill=rgb('3a3b54'))
    cloud, cloud_hi = rgb('6b7d9a'), rgb('adb2c2')
    for x in range(6, BACK_W - 20, 34):
        _cloud(d, x + rnd.randrange(8), 12 + rnd.randrange(8), 12 + rnd.randrange(8), cloud, cloud_hi)
    mid = BACK_W // 2
    _dragon(d, 4 * C + 14, mid - 26, 16, 1)
    _dragon(d, 20 * C - 14, mid + 26, 16, -1)
    d.ellipse([mid - 4, 13, mid + 3, 20], fill=GOLD, outline=GOLD_DK)       # the pearl, in flame
    d.point((mid - 2, 15), fill=WHITE)
    for dx, dy in ((-6, 14), (5, 13), (-1, 11), (0, 22), (-7, 18), (6, 18)):
        d.point((mid + dx, dy), fill=FLAME)
    for x in range(0, BACK_W, 2 * C):                           # the bay posts cross the frieze
        d.rectangle([x - 1, 10, x + 1, 23], fill=LQ)
        d.point((x, 16), fill=GOLD)
    bar(d, -1, 24, BACK_W, HEAD - 1, LQ, LQ_HI, LQ_DK)          # the beam
    d.line([0, 27, BACK_W - 1, 27], fill=RED)
    for x in range(7, BACK_W, 16):
        stud(d, x, 25)
    _frieze = im
    return im


def _wall(fx, w):
    """A back-wall piece `w` cells wide whose west end is floor column `fx`:
    its cut of the frieze, a dark lacquer wall below, the skirting."""
    im, d = new(w * C, 3 * C)
    d.rectangle([0, HEAD, w * C - 1, 95], fill=RED_DK)
    im.paste(frieze().crop((fx * C, 0, (fx + w) * C, HEAD)), (0, 0))
    d.rectangle([0, 89, w * C - 1, 95], fill=LQ)
    d.line([0, 89, w * C - 1, 89], fill=INK)
    d.line([0, 90, w * C - 1, 90], fill=LQ_HI)
    d.line([0, 95, w * C - 1, 95], fill=INK)
    return im, d


def _toro(d, x, y, lit=True):
    """A small hung lantern, its ring at (x, y): 9 wide, 15 tall."""
    d.line([x, y, x, y + 2], fill=BRASS_DK)
    d.polygon([(x, y + 2), (x + 4, y + 5), (x - 4, y + 5)], fill=LQ)
    d.line([x - 4, y + 5, x + 4, y + 5], fill=BRASS)
    d.rectangle([x - 3, y + 6, x + 3, y + 11], fill=LAMP if lit else BRASS_DK)
    if lit:
        d.rectangle([x - 1, y + 8, x + 1, y + 9], fill=LAMP_HI)
    d.line([x - 3, y + 6, x - 3, y + 11], fill=BRASS_DK)
    d.line([x + 3, y + 6, x + 3, y + 11], fill=BRASS_DK)
    d.line([x, y + 6, x, y + 11], fill=BRASS)
    d.line([x - 3, y + 12, x + 3, y + 12], fill=BRASS)
    d.line([x, y + 13, x, y + 15], fill=VERM)


def _banner(d, x, y0, y1, cols):
    """A hung brocade banner (ban), 7 wide: bands of colour, a gilt head, tails."""
    d.polygon([(x + 3, y0), (x + 7, y0 + 4), (x - 1, y0 + 4)], fill=GOLD, outline=GOLD_DK)
    h = (y1 - y0 - 5) // len(cols)
    for i, col in enumerate(cols):
        d.rectangle([x, y0 + 5 + i * h, x + 6, y0 + 4 + (i + 1) * h], fill=col)
        d.point((x + 3, y0 + 5 + i * h + h // 2), fill=GOLD_HI)
    d.line([x, y0 + 5, x, y0 + 4 + len(cols) * h], fill=GOLD_DK)
    d.line([x + 6, y0 + 5, x + 6, y0 + 4 + len(cols) * h], fill=GOLD_DK)
    for tx in (x, x + 3, x + 6):
        d.line([tx, y0 + 5 + len(cols) * h, tx, y1], fill=cols[tx % len(cols)])
        d.point((tx, y1), fill=GOLD)


def _tennin(d, x, y, flip=False):
    """A heavenly maiden flying, her scarves trailing behind her; (x, y) is her head."""
    s = -1 if flip else 1
    scarf, scarf_hi = rgb('e6d6cd'), rgb('efefef')
    for i in range(30):                                          # the long scarf behind her
        px = x - s * (4 + i)
        py = y + 5 + round(math.sin(i / 4.0) * 3) - i // 6
        d.point((px, py), fill=scarf_hi if i % 5 else scarf)
        d.point((px, py + 1), fill=scarf)
    for i in range(18):                                          # a second, over her shoulder
        px = x - s * (2 + i)
        py = y - 4 - round(math.sin(i / 3.0) * 2) - i // 5
        d.point((px, py), fill=PINK_HI)
    d.polygon([(x - s * 2, y + 3), (x + s * 3, y + 3), (x - s * 14, y + 12), (x - s * 20, y + 9)], fill=TEAL)   # robe
    d.line([x - s * 3, y + 5, x - s * 16, y + 10], fill=TEAL_HI)
    d.polygon([(x - s * 12, y + 10), (x - s * 22, y + 8), (x - s * 24, y + 13), (x - s * 16, y + 13)], fill=VERM_DK)  # skirt
    d.line([x - s * 14, y + 11, x - s * 22, y + 10], fill=VERM)
    d.line([x + s * 2, y + 4, x + s * 8, y + 7], fill=SKIN)                       # an arm, holding a lotus
    lotus(d, x + s * 10, y + 8)
    d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=SKIN)                          # head
    d.point((x + s * 1, y), fill=INK)
    d.rectangle([x - 2, y - 4, x + 2, y - 2], fill=INK)                           # hair, a topknot
    d.rectangle([x - 1, y - 6, x + 1, y - 5], fill=INK)
    d.point((x, y - 4), fill=GOLD_HI)
    d.ellipse([x - 5, y - 8, x + 5, y + 3], outline=GOLD)                         # her halo


def wall_tennin(side):
    """The wall behind the sanctum, one side of the cabinet: old gold panels in
    lacquer frames, a heavenly maiden flying toward the Kannon, banners, lanterns."""
    def draw():
        fx = 4 if side == 'l' else 15
        im, d = _wall(fx, 5)
        w = 5 * C
        old_gold(d, 2, HEAD + 2, w - 3, 86, 31 + fx)
        rnd = random.Random(7 + fx)
        cloud, cloud_hi = rgb('c6a663'), rgb('c6aa71')
        for _ in range(7):                                       # gold cloud bands
            _cloud(d, 6 + rnd.randrange(w - 40), HEAD + 8 + rnd.randrange(46), 16 + rnd.randrange(14), cloud, cloud_hi)
        for x in range(8, w - 8, 9):                             # a lotus pond along the foot
            d.line([x, 86, x + rnd.randrange(-2, 3), 78 + rnd.randrange(4)], fill=LOTUS_G)
            if rnd.random() < 0.5:
                d.ellipse([x - 4, 76 + rnd.randrange(3), x + 4, 80 + rnd.randrange(3)], fill=LOTUS_G, outline=LOTUS_G_HI)
            elif rnd.random() < 0.7:
                lotus(d, x, 78 + rnd.randrange(3))
        hx = 96 if side == 'l' else w - 97
        _tennin(d, hx, HEAD + 26, flip=(side == 'r'))
        for _ in range(9):                                       # petals she lets fall
            px, py = hx - 40 + rnd.randrange(84), HEAD + 44 + rnd.randrange(26)
            d.point((px, py), fill=PINK_HI)
            d.point((px + 1, py + 1), fill=PINK)
        for x in (0, 2 * C, 4 * C, w - 3):                       # the lacquer frames
            post(d, x, HEAD, x + 2, 88, LQ, LQ_HI, LQ_DK, outline=False)
        d.line([0, HEAD + 1, w - 1, HEAD + 1], fill=INK)
        outer = 12 if side == 'l' else w - 19                    # banners at the outer end, a lantern each bay
        _banner(d, outer, HEAD + 2, HEAD + 46, (PURPLE, VERM_DK, TEAL, GOLD_DK))
        _banner(d, outer + (12 if side == 'l' else -12), HEAD + 2, HEAD + 38, (VERM_DK, GOLD_DK, PURPLE))
        for x in (48, 128) if side == 'l' else (w - 49, w - 129):
            _toro(d, x, HEAD + 1)
        return im
    return draw


def kuden():
    """The sanctum's cabinet (kuden) in the middle of the back wall: under a
    golden canopy hung with jewels sits the Kannon, and the brocade curtains are
    drawn most of the way across her: she is not shown."""
    im, d = _wall(9, 6)
    w = 6 * C
    cx = w // 2
    d.rectangle([20, HEAD, w - 21, 88], fill=LQ_DK)                              # the recess
    d.rectangle([20, HEAD, w - 21, 88], outline=INK)
    for y in range(HEAD + 1, 88):                                                # a glow from within
        for x in range(cx - 30, cx + 31):
            t = max(0.0, 1 - math.hypot((x - cx) / 30.0, (y - 62) / 30.0))
            if t > 0.05:
                im.putpixel((x, y), mix(LQ_DK, rgb('85553e'), min(1.0, t * 1.1)) + (255,))
    # the image: a halo, the seated figure, the lotus she sits on
    d.ellipse([cx - 13, 40, cx + 13, 66], fill=GOLD_DK, outline=GOLD)
    d.ellipse([cx - 9, 44, cx + 9, 62], fill=rgb('7f513b'))
    for a in range(0, 360, 30):
        d.point((cx + round(11 * math.cos(math.radians(a))), 53 + round(11 * math.sin(math.radians(a)))), fill=GOLD_HI)
    d.rectangle([cx - 3, 46, cx + 3, 53], fill=GOLD)                             # head
    d.rectangle([cx - 2, 42, cx + 2, 45], fill=GOLD_DK)                          # the crown
    d.point((cx, 42), fill=GOLD_HI)
    d.line([cx - 3, 46, cx - 3, 53], fill=GOLD_HI)
    d.line([cx - 1, 50, cx + 1, 50], fill=GOLD_DK)
    d.polygon([(cx - 4, 54), (cx + 4, 54), (cx + 9, 66), (cx + 12, 72), (cx - 12, 72), (cx - 9, 66)], fill=GOLD)   # robes
    d.line([cx - 4, 55, cx - 9, 66], fill=GOLD_HI)
    d.line([cx + 2, 58, cx + 6, 70], fill=GOLD_DK)
    d.line([cx - 2, 58, cx - 5, 70], fill=GOLD_DK)
    d.ellipse([cx - 3, 62, cx + 3, 66], fill=GOLD_HI)                            # her hands, in her lap
    d.polygon([(cx - 16, 72), (cx + 16, 72), (cx + 12, 78), (cx - 12, 78)], fill=GOLD_DK, outline=INK)   # the lotus seat
    for x in range(cx - 13, cx + 14, 5):
        d.polygon([(x, 72), (x + 4, 72), (x + 2, 76)], fill=GOLD)
    # the tiered stand (shumidan) under her
    for i, (inset, y0) in enumerate(((16, 79), (22, 82), (16, 85))):
        box(d, cx - 38 + inset, y0, cx + 38 - inset, y0 + 3, RED if i != 1 else LQ)
        d.line([cx - 37 + inset, y0 + 1, cx + 37 - inset, y0 + 1], fill=GOLD if i != 1 else LQ_HI)
    # the brocade curtains: drawn from both sides, a hand's width apart
    rnd = random.Random(645)
    for s in (-1, 1):
        inner, outer = cx + s * 5, cx + s * 44
        for y in range(40, 80):
            sag = round(6 * math.sin((y - 40) / 40.0 * math.pi))               # tied back in the middle
            a, b = sorted((inner + s * sag, outer))
            for x in range(a, b + 1):
                fold = (x * 3 + (y // 9)) % 9
                col = PURPLE if fold > 2 else PURPLE_DK
                if fold == 5:
                    col = PURPLE_HI
                im.putpixel((x, y), col + (255,))
            d.point((inner + s * sag, y), fill=GOLD)                           # its gold edge
        for _ in range(26):                                                    # woven roundels
            x, y = cx + s * (12 + rnd.randrange(30)), 43 + rnd.randrange(34)
            d.point((x, y), fill=GOLD)
            d.point((x + 1, y), fill=GOLD_HI)
        d.line([cx + s * 26, 58, cx + s * 44, 58], fill=GOLD)                  # the tie
        d.line([cx + s * 26, 59, cx + s * 44, 59], fill=GOLD_DK)
        d.line([cx + s * 30, 60, cx + s * 30, 67], fill=VERM)
        d.line([cx + s * 31, 60, cx + s * 31, 66], fill=VERM)
    # the canopy (tengai): a gilt hood, a net of jewels hanging from its rim
    d.polygon([(cx - 50, 40), (cx + 50, 40), (cx + 42, HEAD + 1), (cx - 42, HEAD + 1)], fill=GOLD, outline=INK)
    d.line([cx - 41, HEAD + 2, cx + 41, HEAD + 2], fill=GOLD_HI)
    d.line([cx - 48, 38, cx + 48, 38], fill=GOLD_DK)
    for x in range(cx - 44, cx + 45, 8):
        d.line([x, HEAD + 3, x, 37], fill=GOLD_DK)
        d.point((x + 4, 35), fill=VERM)
        d.point((x + 4, 34), fill=GOLD_HI)
    box(d, cx - 52, 40, cx + 52, 43, GOLD)
    d.line([cx - 51, 41, cx + 51, 41], fill=GOLD_HI)
    for i, x in enumerate(range(cx - 50, cx + 51, 5)):                         # the hanging jewels (yoraku)
        edge = abs(x - cx) > 40
        n = 20 if edge else (5 if i % 2 else 3)
        for k in range(n):
            d.point((x, 44 + k), fill=GOLD_HI if k % 3 == 0 else GOLD_DK)
        d.point((x, 44 + n), fill=rgb('76cae3') if i % 3 == 0 else VERM_HI)
    # its gilt posts, and a guardian in a niche either side
    for x in (22, w - 29):
        post(d, x, HEAD, x + 6, 88, GOLD, GOLD_HI, GOLD_DK)
    for x in (9, w - 10):
        d.rectangle([x - 6, HEAD + 14, x + 6, 84], fill=LQ_DK, outline=GOLD_DK)
        d.ellipse([x - 4, HEAD + 18, x + 4, HEAD + 27], outline=GOLD_DK)
        d.rectangle([x - 2, HEAD + 20, x + 2, HEAD + 25], fill=BRASS)          # a small gilt figure
        d.polygon([(x - 3, HEAD + 26), (x + 3, HEAD + 26), (x + 5, 76), (x - 5, 76)], fill=BRASS)
        d.line([x - 3, HEAD + 27, x - 4, 75], fill=BRASS_HI)
        d.line([x + 2, HEAD + 30, x + 3, 75], fill=BRASS_DK)
        d.rectangle([x - 6, 77, x + 6, 80], fill=GOLD_DK)
        _toro(d, x, HEAD)
    return im


def omikuji():
    """The fortune wall: a cabinet of a hundred little drawers, numbered; on its
    counter the six-sided cylinder you shake a numbered stick out of, and the coin box."""
    im, d = _wall(20, 4)
    w = 4 * C
    box(d, 4, HEAD + 1, w - 5, 88, WOOD_DK)
    box(d, 30, HEAD + 3, 97, HEAD + 15, VERM_DK)                               # the sign
    d.rectangle([31, HEAD + 4, 96, HEAD + 14], outline=GOLD_DK)
    label = 'おみくじ'
    text(d, 64 - text_w(d, label, kana()) // 2, HEAD + 4, label, kana(), PAPER)
    for x in (16, 112):                                                        # a lantern either side of it
        _toro(d, x, HEAD + 1)
    rnd = random.Random(100)
    x0, y0 = 10, HEAD + 18                                                     # 12 x 8 drawers, 9 x 4
    for r in range(8):
        for c in range(12):
            x, y = x0 + c * 9, y0 + r * 4
            base = WOOD if (r + c) % 2 else mix(WOOD, WOOD_HI, 0.35)
            if rnd.random() < 0.08:
                base = WOOD_HI                                                 # one worn pale with use
            d.rectangle([x, y, x + 8, y + 3], fill=base)
            d.line([x, y, x + 8, y], fill=WOOD_DK)
            d.line([x, y, x, y + 3], fill=WOOD_DK)
            d.line([x + 2, y + 2, x + 3, y + 2], fill=PAPER)                   # its number slip
            d.point((x + 6, y + 2), fill=BRASS_HI)                             # its pull
    d.rectangle([x0, y0, x0 + 108, y0 + 32], outline=INK)
    one = x0 + 7 * 9, y0 + 5 * 4                                               # one drawer left a little open
    d.rectangle([one[0], one[1] + 1, one[0] + 8, one[1] + 4], fill=WOOD_HI, outline=INK)
    d.line([one[0] + 2, one[1] + 2, one[0] + 6, one[1] + 2], fill=WHITE)
    # the counter
    box(d, 2, 82, w - 3, 88, LQ)
    d.line([3, 83, w - 4, 83], fill=LQ_HI)
    d.line([3, 86, w - 4, 86], fill=GOLD_DK)
    # the cylinder: six-sided, steel, a hole in its end for the stick; one stick is out
    d.polygon([(28, 62), (36, 60), (44, 62), (44, 82), (36, 84), (28, 82)], fill=rgb('949bb2'), outline=INK)
    d.line([30, 63, 30, 81], fill=rgb('dae2e4'))
    d.line([36, 61, 36, 83], fill=rgb('726f86'))
    d.line([40, 63, 40, 81], fill=rgb('747e93'))
    d.ellipse([33, 59, 39, 62], fill=INK)
    d.line([37, 60, 45, 52], fill=PAPER)
    d.line([38, 60, 46, 52], fill=WOOD_HI)
    d.point((45, 52), fill=VERM)
    box(d, 82, 70, 104, 82, WOOD)                                              # the coin box
    d.line([83, 71, 103, 71], fill=WOOD_HI)
    d.line([88, 74, 98, 74], fill=INK)
    text(d, 86, 76, '100', ImageFont.truetype('fonts/PixelOperatorMono.ttf', 8), GOLD_HI)
    for i in range(4):                                                         # slips already read, left on the counter
        d.rectangle([54 + i * 6, 78 - (i % 2), 58 + i * 6, 81], fill=WHITE, outline=PAPER_SH)
    return im


def wall_charms():
    """The charm counter (juyosho) in the west aisle: shelves of brocade
    charms and wooden plaques, a counter with trays of them, nobody behind it."""
    im, d = _wall(0, 4)
    w = 4 * C
    box(d, 4, HEAD + 1, w - 5, 88, WOOD_DK)
    box(d, 40, HEAD + 3, 87, HEAD + 15, LQ)
    d.rectangle([41, HEAD + 4, 86, HEAD + 14], outline=GOLD_DK)
    label = 'お守り'
    text(d, 64 - text_w(d, label, kana()) // 2, HEAD + 4, label, kana(), GOLD_HI)
    for x in (22, 106):
        _toro(d, x, HEAD + 1)
    rnd = random.Random(88)
    cols = (VERM, PURPLE, TEAL, GOLD, rgb('dfdfdf'), PINK, rgb('3a5792'))
    for r, y in enumerate((HEAD + 20, HEAD + 33)):                             # two shelves of charms
        d.rectangle([8, y + 10, w - 9, y + 11], fill=WOOD_HI)
        d.line([8, y + 12, w - 9, y + 12], fill=INK)
        x = 10
        while x < w - 16:
            if r == 1 and 44 < x < 80:                                         # wooden plaques (ema), a string each
                d.polygon([(x, y + 3), (x + 4, y), (x + 8, y + 3), (x + 8, y + 9), (x, y + 9)], fill=WOOD_HI, outline=WOOD_DK)
                d.line([x + 2, y + 5, x + 6, y + 5], fill=VERM_DK)
                d.point((x + 4, y + 7), fill=INK)
                x += 11
                continue
            col = cols[rnd.randrange(len(cols))]
            d.rectangle([x, y + 2, x + 4, y + 9], fill=col)                    # a charm: a brocade pouch
            d.line([x, y + 2, x, y + 9], fill=mix(col, WHITE, 0.4))
            d.line([x + 1, y + 4, x + 3, y + 4], fill=GOLD_HI if col != GOLD else VERM_DK)
            d.point((x + 2, y + 6), fill=GOLD_HI if col != GOLD else VERM_DK)
            d.line([x + 2, y, x + 2, y + 1], fill=WHITE)                       # its cord
            x += 7
    # the counter: a lacquer top, trays of charms on a red cloth, a bell to ring for somebody
    d.rectangle([6, 66, w - 7, 81], fill=VERM_DK)
    d.line([6, 66, w - 7, 66], fill=VERM)
    for x in range(12, w - 30, 22):
        box(d, x, 68, x + 17, 79, WOOD)
        for i in range(3):
            col = cols[(x + i * 3) % len(cols)]
            d.rectangle([x + 2 + i * 5, 70, x + 5 + i * 5, 77], fill=col)
            d.point((x + 3 + i * 5, 72), fill=GOLD_HI)
    d.ellipse([w - 24, 70, w - 14, 78], fill=BRASS, outline=INK)               # the bell
    d.line([w - 22, 72, w - 19, 71], fill=BRASS_HI)
    d.rectangle([w - 20, 67, w - 18, 69], fill=BRASS_DK)
    box(d, 2, 82, w - 3, 88, LQ)
    d.line([3, 83, w - 4, 83], fill=LQ_HI)
    d.line([3, 86, w - 4, 86], fill=GOLD_DK)
    return im


# ---- the sanctum ---------------------------------------------------------------------

def _tatami(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=TATAMI)
    for y in range(y0, y1 + 1, 2):
        d.line([x0, y, x1, y], fill=TATAMI_DK if (y // 2) % 4 == 0 else TATAMI)
    for x in range(x0, x1, 64):                                 # the mats' cloth borders
        d.rectangle([x, y0, x + 2, y1], fill=LQ)
        d.line([x + 1, y0, x + 1, y1], fill=GOLD_DK)
    for y in range(y0 + 31, y1, 32):
        d.line([x0, y, x1, y], fill=LQ)
        d.line([x0, y + 1, x1, y + 1], fill=TATAMI_HI)


def _candle_bank(d, x0, y0, tiers=3, n=9):
    """Banked candles: a stepped stand, a row of lit candles on each step."""
    for t in range(tiers):
        y = y0 + t * 10
        inset = (tiers - 1 - t) * 4
        box(d, x0 + inset, y + 8, x0 + n * 7 + 4 - inset, y + 11, LQ)
        d.line([x0 + inset + 1, y + 9, x0 + n * 7 + 3 - inset, y + 9], fill=GOLD_DK)
        for i in range(n - (tiers - 1 - t)):
            candle(d, x0 + inset + 4 + i * 7, y + 7, 4)
    box(d, x0 + 2, y0 + tiers * 10 + 2, x0 + n * 7 + 2, y0 + tiers * 10 + 6, RED_DK)


def _lotus_stand(d, cx, y):
    """A gilt lotus in a vase on a tall stand (joka), its foot at (cx, y)."""
    d.rectangle([cx - 1, y - 16, cx + 1, y], fill=LQ)
    d.rectangle([cx - 4, y - 1, cx + 4, y + 1], fill=LQ, outline=INK)
    d.polygon([(cx - 4, y - 16), (cx + 4, y - 16), (cx + 3, y - 24), (cx - 3, y - 24)], fill=BRASS, outline=INK)
    d.line([cx - 2, y - 23, cx - 3, y - 17], fill=BRASS_HI)
    for dx, top in ((-7, 40), (0, 46), (7, 38), (-3, 34), (4, 32)):            # stems, leaves and blooms, all gilt
        d.line([cx + dx // 2, y - 24, cx + dx, y - top + 4], fill=GOLD_DK)
        if top in (46, 38):
            lotus(d, cx + dx, y - top + 4, GOLD, GOLD_HI)
        else:
            d.ellipse([cx + dx - 4, y - top + 1, cx + dx + 4, y - top + 6], fill=GOLD_DK, outline=GOLD)


def naijin():
    """The inner sanctum, 16x4, and the gilt lattice across its front. Behind
    the lattice: mats, the altar and its offerings, banked candles, gilt lotus,
    the monk's seat with a sutra desk and a wooden fish. The lattice is a mesh
    you see through; in the middle it is open over a low rail."""
    W, H = 16 * C, 4 * C
    im, d = new(W, H)
    cx = W // 2
    _tatami(d, 0, 0, W - 1, 110)
    for y in range(0, 12):                                      # the cabinet's shadow along the back
        d.line([0, y, W - 1, y], fill=SHADE + (150 - y * 12,))
    # the altar table: black lacquer, a brocade cloth down its front
    shadow(d, cx - 54, 34, cx + 54, 46, 80)
    box(d, cx - 50, 8, cx + 50, 14, LQ)
    d.line([cx - 49, 9, cx + 49, 9], fill=LQ_HI)
    d.rectangle([cx - 46, 15, cx + 46, 38], fill=LQ_DK, outline=INK)
    d.polygon([(cx - 30, 15), (cx + 30, 15), (cx, 36)], fill=PURPLE, outline=GOLD)
    d.polygon([(cx - 18, 15), (cx + 18, 15), (cx, 28)], fill=VERM_DK, outline=GOLD_DK)
    for x in (cx - 40, cx + 38):
        stud(d, x, 20)
        stud(d, x, 30)
    # on it: the censer, a pair of candles, a pair of vases, towers of offerings
    d.ellipse([cx - 6, 1, cx + 6, 9], fill=BRASS, outline=INK)
    d.line([cx - 4, 3, cx, 2], fill=BRASS_HI)
    d.line([cx, 0, cx, 1], fill=SMOKE)
    for s in (-1, 1):
        candle(d, cx + s * 16 - 1, 8, 6)
        d.rectangle([cx + s * 16 - 2, 8, cx + s * 16 + 2, 9], fill=BRASS)
        for i in range(3):                                      # rice cakes, stacked
            d.ellipse([cx + s * 30 - 5 + i, 5 - i * 3 + 1, cx + s * 30 + 5 - i, 9 - i * 3 + 1], fill=WHITE, outline=PAPER_SH)
        d.polygon([(cx + s * 43 - 4, 9), (cx + s * 43 + 4, 9), (cx + s * 43 + 2, 5), (cx + s * 43 - 2, 5)], fill=BRASS)   # fruit on a stand
        for fx_, fy_, col in ((-2, 3, rgb('db785c')), (2, 3, rgb('db785c')), (0, 0, rgb('e75d42'))):
            d.rectangle([cx + s * 43 + fx_ - 1, fy_, cx + s * 43 + fx_ + 1, fy_ + 2], fill=col)
    # gilt lotus either side of the table, banked candles beyond them
    for s in (-1, 1):
        _lotus_stand(d, cx + s * 64, 44)
        _candle_bank(d, cx + s * 114 - 34, 4)
    # the far ends: a standing lantern, offering stands, a row of small gilt figures
    for s in (-1, 1):
        ex = cx + s * 208
        for i in range(5):
            x = ex + (i - 2) * 13
            d.rectangle([x - 4, 22, x + 4, 25], fill=LQ, outline=INK)
            d.polygon([(x - 3, 21), (x + 3, 21), (x + 2, 11), (x - 2, 11)], fill=BRASS)
            d.line([x - 2, 12, x - 3, 20], fill=BRASS_HI)
            d.rectangle([x - 1, 7, x + 1, 10], fill=BRASS)
            d.ellipse([x - 4, 5, x + 4, 14], outline=GOLD_DK)
        lx = cx + s * 160                                        # a gilt standing lantern
        d.rectangle([lx - 1, 28, lx + 1, 50], fill=BRASS_DK)
        d.rectangle([lx - 5, 49, lx + 5, 52], fill=BRASS_DK, outline=INK)
        box(d, lx - 5, 12, lx + 5, 28, LAMP)
        d.rectangle([lx - 2, 17, lx + 2, 23], fill=LAMP_HI)
        d.line([lx, 13, lx, 27], fill=BRASS)
        d.line([lx - 4, 20, lx + 4, 20], fill=BRASS)
        d.polygon([(lx, 5), (lx + 8, 12), (lx - 8, 12)], fill=BRASS, outline=INK)
        for i in range(3):                                       # offering stands in a row on the mats
            x = ex + (i - 1) * 22
            box(d, x - 7, 50, x + 7, 53, WOOD_HI)
            d.rectangle([x - 4, 54, x + 4, 60], fill=WOOD, outline=INK)
            for k in range(3):
                d.ellipse([x - 5 + k, 46 - k * 3, x + 5 - k, 50 - k * 3], fill=rgb('f27e66') if i == 1 else WHITE,
                          outline=rgb('c66347') if i == 1 else PAPER_SH)
    # the monk's seat (raiban): a low square stand and cushion, the sutra desk, the wooden fish, a bowl bell
    shadow(d, cx - 30, 66, cx + 30, 80, 70)
    box(d, cx - 24, 56, cx + 24, 74, LQ)
    d.line([cx - 23, 57, cx + 23, 57], fill=LQ_HI)
    d.line([cx - 23, 71, cx + 23, 71], fill=GOLD_DK)
    d.rounded_rectangle([cx - 15, 53, cx + 15, 67], radius=3, fill=PURPLE, outline=INK)
    d.line([cx - 12, 55, cx + 12, 55], fill=PURPLE_HI)
    d.rectangle([cx - 1, 59, cx + 1, 61], fill=GOLD)
    box(d, cx - 12, 44, cx + 12, 48, VERM_DK)                                  # the desk
    d.line([cx - 11, 45, cx + 11, 45], fill=VERM)
    d.rectangle([cx - 6, 41, cx + 6, 44], fill=PAPER, outline=PAPER_SH)        # the sutra, open
    d.line([cx, 41, cx, 44], fill=PAPER_SH)
    d.rounded_rectangle([cx + 34, 56, cx + 50, 70], radius=5, fill=VERM_DK, outline=INK)   # mokugyo
    d.line([cx + 37, 59, cx + 44, 58], fill=VERM)
    d.line([cx + 38, 65, cx + 47, 65], fill=INK)
    d.rounded_rectangle([cx + 32, 70, cx + 52, 75], radius=2, fill=PURPLE_DK, outline=INK)
    d.ellipse([cx - 50, 58, cx - 34, 70], fill=BRASS_DK, outline=INK)          # a small bowl bell
    d.ellipse([cx - 48, 58, cx - 36, 63], fill=LQ_DK, outline=BRASS_HI)
    d.rounded_rectangle([cx - 52, 69, cx - 32, 75], radius=2, fill=VERM_DK, outline=INK)

    # ---- the lattice: everything below its head rail is seen through it ----
    top, foot = 60, 116
    gap = (cx - 2 * C, cx + 2 * C)                               # open in the middle: four cells
    veil = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.rectangle([0, top, gap[0] - 1, H - 1], fill=SHADE + (96,))
    vd.rectangle([gap[1], top, W - 1, H - 1], fill=SHADE + (96,))
    im.alpha_composite(veil)
    d = ImageDraw.Draw(im)
    for y in range(top + 6, foot):
        for x in list(range(0, gap[0])) + list(range(gap[1], W)):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                im.putpixel((x, y), (GOLD_HI if (x + y) % 6 == 0 and (x - y) % 6 == 0 else GOLD if y < top + 20 else GOLD_DK) + (255,))
    for a, b in ((0, gap[0] - 1), (gap[1], W - 1)):
        bar(d, a, top, b, top + 6, RED, RED_HI, RED_DK)          # the head rail
        for x in range(a + 6, b - 4, 16):
            stud(d, x, top + 2)
        d.rectangle([a, foot, b, H - 1], fill=LQ)                # the foot panel
        d.line([a, foot, b, foot], fill=INK)
        d.line([a, foot + 1, b, foot + 1], fill=LQ_HI)
        d.rectangle([a + 2, foot + 3, b - 2, H - 3], outline=GOLD_DK)
        for x in range(a + 14, b - 8, 32):
            d.ellipse([x - 3, foot + 4, x + 3, H - 4], outline=GOLD)
            d.point((x, foot + 6), fill=GOLD_HI)
    for x in list(range(0, gap[0] + 1, C)) + list(range(gap[1], W + 1, C)):
        x = min(x, W - 4)
        post(d, x - (0 if x == 0 else 2), top - 4, x + 3, H - 1, RED, RED_HI, RED_DK)
        d.rectangle([x - (0 if x == 0 else 2), top - 6, x + 3, top - 3], fill=GOLD, outline=INK)
        d.rectangle([x - (0 if x == 0 else 2), H - 6, x + 3, H - 1], fill=LQ, outline=INK)
    # the opening: the head rail carries on across it, a brocade valance hung from it; below, a low gilt rail
    bar(d, gap[0] + 4, top, gap[1] - 3, top + 6, RED, RED_HI, RED_DK)
    for x in range(gap[0] + 10, gap[1] - 6, 16):
        stud(d, x, top + 2)
    for x in range(gap[0] + 4, gap[1] - 2):
        drop = 5 + round(2.5 * abs(math.sin((x - gap[0]) / 128.0 * math.pi * 4)))
        d.line([x, top + 7, x, top + 6 + drop], fill=PURPLE if (x // 4) % 2 else PURPLE_DK)
        d.point((x, top + 7 + drop), fill=GOLD)
        if x % 8 == 0:
            d.point((x, top + 9), fill=GOLD_HI)
    d.rectangle([gap[0] + 4, 111, gap[1] - 3, H - 1], fill=LQ)
    d.line([gap[0] + 4, 111, gap[1] - 3, 111], fill=GOLD_DK)
    d.line([gap[0] + 4, 112, gap[1] - 3, 112], fill=LQ_HI)
    for x in range(gap[0] + 10, gap[1] - 8, 12):                 # the rail's balusters
        d.rectangle([x, 100, x + 1, 111], fill=VERM_DK)
    bar(d, gap[0] + 4, 97, gap[1] - 3, 100, VERM_DK, VERM, RED_DK)
    for x in (gap[0] + 18, cx - 1, gap[1] - 20):
        d.rectangle([x, 93, x + 3, 97], fill=GOLD, outline=INK)  # gilt finials
        d.point((x + 1, 92), fill=GOLD_HI)
    d.rectangle([gap[0] + 4, H - 3, gap[1] - 3, H - 1], fill=LQ_DK)
    d.line([0, H - 1, W - 1, H - 1], fill=INK)
    return im


# ---- the outer hall -------------------------------------------------------------------

def pillar():
    """A round column in old dark red lacquer: gilt bands, a black foot on a stone."""
    im, d = new(C, 3 * C)
    shadow(d, 4, 86, 28, 95, 100)
    d.rectangle([9, 3, 22, 90], fill=RED)
    d.rectangle([10, 3, 11, 90], fill=RED_HI)
    d.rectangle([12, 3, 12, 90], fill=mix(RED, RED_HI, 0.5))
    d.rectangle([18, 3, 21, 90], fill=RED_DK)
    d.line([9, 3, 9, 90], fill=INK)
    d.line([22, 3, 22, 90], fill=INK)
    for y0 in (62, 20):                                          # gilt bands, a lotus petal worked in each
        d.rectangle([8, y0, 23, y0 + 5], fill=GOLD_DK, outline=INK)
        d.line([9, y0 + 1, 14, y0 + 1], fill=GOLD)
        for x in (11, 15, 19):
            d.point((x, y0 + 3), fill=GOLD_HI)
    d.rectangle([9, 68, 22, 90], fill=LQ)                        # the foot
    d.rectangle([10, 68, 11, 90], fill=LQ_HI)
    d.rectangle([18, 68, 21, 90], fill=LQ_DK)
    d.line([9, 68, 9, 90], fill=INK)
    d.line([22, 68, 22, 90], fill=INK)
    box(d, 5, 0, 26, 4, LQ)                                      # the bracket block at its head
    d.line([6, 1, 25, 1], fill=LQ_HI)
    box(d, 7, 4, 24, 8, GOLD_DK)
    d.line([8, 5, 23, 5], fill=GOLD)
    d.ellipse([5, 85, 26, 94], fill=STONE_DK, outline=INK)       # the stone it stands on
    d.ellipse([7, 85, 24, 90], fill=STONE_HI)
    d.rectangle([9, 83, 22, 88], fill=LQ)
    d.line([9, 83, 9, 88], fill=INK)
    d.line([22, 83, 22, 88], fill=INK)
    d.line([10, 84, 11, 88], fill=LQ_HI)
    return im


def saisen():
    """The offering box: a great slatted chest, a gilt lotus on its front."""
    im, d = new(4 * C, 2 * C)
    w = 4 * C
    shadow(d, 2, 50, w - 3, 63, 100)
    d.polygon([(8, 28), (w - 9, 28), (w - 5, 58), (4, 58)], fill=WOOD, outline=INK)       # the front
    for y in (36, 44, 51):
        d.line([7, y, w - 8, y], fill=WOOD_DK)
        d.line([7, y + 1, w - 8, y + 1], fill=WOOD_HI)
    for x in (8, 30, w - 33, w - 11):                           # iron straps, gilt nails
        d.rectangle([x, 29, x + 2, 57], fill=LQ)
        stud(d, x, 32)
        stud(d, x, 52)
    d.ellipse([w // 2 - 11, 32, w // 2 + 11, 54], fill=LQ, outline=GOLD)                 # the crest: a lotus
    lotus(d, w // 2, 46, GOLD, GOLD_HI)
    lotus(d, w // 2 - 5, 48, GOLD_DK, GOLD)
    lotus(d, w // 2 + 5, 48, GOLD_DK, GOLD)
    d.line([w // 2 - 7, 50, w // 2 + 7, 50], fill=GOLD)
    f = kana()
    for s, x in (('浄', 38), ('財', w - 50)):                   # "pure offering"
        text(d, x, 37, s, f, GOLD_HI)
    d.polygon([(4, 28), (w - 5, 28), (w - 11, 8), (10, 8)], fill=WOOD_DK, outline=INK)   # the top: slats over the dark
    for x in range(14, w - 14, 7):
        t = (x - w / 2) / (w / 2)
        d.line([x, 10, round(x + t * 5), 26], fill=WOOD_HI)
        d.line([x + 1, 10, round(x + 1 + t * 5), 26], fill=WOOD)
    bar(d, 3, 26, w - 4, 30, WOOD, WOOD_HI, WOOD_DK)
    bar(d, 9, 6, w - 10, 9, WOOD, WOOD_HI, WOOD_DK)
    for x in (22, 60, w - 62, w - 24):                           # coins that missed
        d.point((x, 60), fill=GOLD_HI)
    return im


def _wisp(im, x0, y0, y1, phase, amp, a0):
    """A thread of smoke rising from (x0, y0) to y1: it sways, widens and thins."""
    for y in range(y0, y1, -1):
        t = (y0 - y) / max(1, y0 - y1)
        x = x0 + math.sin(phase + t * 5.0) * amp * (0.3 + t)
        wdt = 1 + round(t * 3)
        a = round(a0 * (1 - t) ** 0.8)
        for dx in range(-wdt, wdt + 1):
            px = round(x + dx)
            if 0 <= px < im.width and 0 <= y < im.height and a > 6:
                fall = 1 - abs(dx) / (wdt + 1)
                old = im.getpixel((px, y))
                na = max(old[3], round(a * fall)) if old[3] < 255 else 255
                if old[3] < 255:
                    im.putpixel((px, y), SMOKE + (na,))


def jokoro():
    """The great incense burner: a bronze cauldron on three legs, a bed of ash
    stuck with burning sticks, the smoke going up from it."""
    im, d = new(4 * C, 3 * C)
    w = 4 * C
    cx = w // 2
    shadow(d, 14, 78, w - 15, 95, 110)
    for x, lean in ((cx - 30, -3), (cx + 30, 3), (cx, 0)):       # the legs: lion's feet
        d.polygon([(x - 5, 70), (x + 5, 70), (x + 4 + lean, 88), (x - 4 + lean, 88)], fill=BRONZE_DK, outline=INK)
        d.rectangle([x - 6 + lean, 87, x + 6 + lean, 91], fill=BRONZE, outline=INK)
        d.line([x - 3, 72, x - 3 + lean, 86], fill=BRONZE)
    d.pieslice([cx - 44, 22, cx + 44, 82], 0, 180, fill=BRONZE, outline=INK)   # the bowl
    for y in range(54, 81):
        half = round(44 * math.sqrt(max(0.0, 1 - ((y - 52) / 30.0) ** 2)))
        d.line([cx - half + 1, y, cx - half + 5, y], fill=BRONZE_HI)
        d.line([cx + half - 9, y, cx + half - 1, y], fill=BRONZE_DK)
    for x in range(cx - 34, cx + 35, 8):                         # a band of gilt bosses round it
        t = (x - cx) / 44.0
        y = 60 + round(4 * (1 - t * t))
        d.rectangle([x - 1, y, x + 1, y + 2], fill=BRASS)
        d.point((x - 1, y), fill=BRASS_HI)
    d.ellipse([cx - 9, 62, cx + 9, 76], fill=BRONZE_DK, outline=BRASS_DK)    # a crest on its belly
    lotus(d, cx, 72, BRASS, BRASS_HI)
    for s in (-1, 1):                                            # the handles
        d.arc([cx + s * 40 - 6, 40, cx + s * 40 + 6, 60], 0, 360, fill=INK)
        d.arc([cx + s * 40 - 5, 41, cx + s * 40 + 5, 59], 0, 360, fill=BRONZE_HI)
    d.ellipse([cx - 46, 42, cx + 46, 60], fill=BRONZE, outline=INK)          # the rim
    d.arc([cx - 45, 43, cx + 45, 59], 180, 300, fill=BRONZE_HI)
    d.ellipse([cx - 39, 44, cx + 39, 56], fill=rgb('949494'), outline=BRONZE_DK)   # the ash
    d.ellipse([cx - 30, 45, cx + 24, 52], fill=rgb('aaaaaa'))
    rnd = random.Random(1300)
    tips = []
    for _ in range(26):                                          # the sticks, in bundles, their ends alight
        x = cx - 30 + rnd.randrange(61)
        y = 47 + rnd.randrange(7)
        lean = rnd.randrange(-2, 3)
        d.line([x, y, x + lean, y - 7], fill=rgb('4a6262'))
        d.point((x + lean, y - 8), fill=VERM)
        tips.append((x + lean, y - 9))
    d.ellipse([cx - 6, 46, cx + 6, 53], fill=VERM)     # the embers in the middle
    d.ellipse([cx - 3, 47, cx + 3, 51], fill=GOLD)
    for i, (x, y) in enumerate(tips):
        if i % 2 == 0:
            _wisp(im, x, y, 2 + rnd.randrange(10), rnd.random() * 6, 5 + rnd.randrange(6), 120)
    for i in range(3):
        _wisp(im, cx - 10 + i * 10, 44, 0, i * 2.1, 9, 150)
    return im


def chochin():
    """The great red paper lantern that hangs inside the doors: a lacquer hoop
    top and bottom with gilt fittings, the paper ribbed, the hall's name on it."""
    im, d = new(4 * C, 3 * C)
    w = 4 * C
    cx = w // 2
    for y in range(0, 7, 3):                                     # hung from the beams
        d.rectangle([cx - 1, y, cx, y + 1], fill=BRASS_DK)
    top, bot = 12, 80
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        half = round(30 + 9 * math.sin(t * math.pi))             # a barrel
        for x in range(cx - half, cx + half + 1):
            u = (x - (cx - half)) / (2.0 * half)                 # lit from the west, round
            col = mix(VERM_HI, VERM, min(1, u * 3)) if u < 0.34 else mix(VERM, VERM_DK, min(1, (u - 0.34) * 1.9))
            if (y - top) % 5 == 4:
                col = mix(col, VERM_DK, 0.55)                    # a rib
            im.putpixel((x, y), col + (255,))
        d.point((cx - half - 1, y), fill=INK)
        d.point((cx + half + 1, y), fill=INK)
    f = kana(24)                                                 # 観音: "Kannon"; nobody's name
    for i, s in enumerate('観音'):
        tw = text_w(d, s, f)
        text(d, cx - tw // 2 + 1, 23 + i * 26, s, f, INK)
    for y0, y1 in ((6, 13), (79, 87)):                           # the hoops
        d.rectangle([cx - 31, y0, cx + 31, y1], fill=LQ, outline=INK)
        d.line([cx - 30, y0 + 1, cx + 30, y0 + 1], fill=LQ_HI)
        d.line([cx - 30, y1 - 2, cx + 30, y1 - 2], fill=GOLD_DK)
        for x in range(cx - 26, cx + 27, 13):
            stud(d, x - 1, y0 + 3)
    d.polygon([(cx - 20, 88), (cx + 20, 88), (cx + 12, 93), (cx - 12, 93)], fill=GOLD, outline=INK)    # the gilt boss under it
    d.line([cx - 17, 89, cx + 17, 89], fill=GOLD_HI)
    d.rectangle([cx - 4, 93, cx + 3, 95], fill=GOLD_DK, outline=INK)
    return im


def toro_hang():
    """A gilt bronze lantern hung from the ceiling on a chain (Tops)."""
    im, d = new(C, 2 * C)
    for y in range(0, 14, 3):
        d.rectangle([15, y, 16, y + 1], fill=BRASS_DK)
    d.polygon([(15, 11), (16, 11), (28, 22), (3, 22)], fill=BRONZE_DK, outline=INK)     # six-sided roof, curled eaves
    d.line([15, 13, 7, 21], fill=BRONZE_HI)
    for x in (3, 28):
        d.point((x, 21), fill=BRASS_HI)
        d.point((x, 20), fill=BRASS)
    d.rectangle([14, 9, 17, 11], fill=BRASS, outline=INK)
    box(d, 8, 23, 23, 41, LAMP)
    for y in (24, 25, 26, 38, 39, 40):
        d.line([9, y, 22, y], fill=LAMP_SH)
    d.rectangle([13, 29, 18, 35], fill=LAMP_HI)
    for x in (12, 19):
        d.line([x, 24, x, 40], fill=BRASS_DK)
    for x, y in ((10, 27), (15, 30), (21, 27), (10, 36), (16, 35), (21, 37)):          # pierced work
        d.point((x, y), fill=BRASS_DK)
    d.line([9, 32, 22, 32], fill=BRASS_DK)
    d.rectangle([8, 23, 23, 41], outline=INK)
    box(d, 6, 41, 25, 44, BRASS)
    d.line([7, 42, 24, 42], fill=BRASS_HI)
    d.polygon([(11, 45), (20, 45), (16, 50), (15, 50)], fill=BRASS_DK, outline=INK)
    d.line([15, 51, 15, 57], fill=PURPLE)                         # the tassel
    d.line([16, 51, 16, 57], fill=PURPLE_DK)
    d.point((15, 58), fill=GOLD)
    return im


def shokudai():
    """A tall candle stand: one fat candle, wax down its side."""
    im, d = new(C, 2 * C)
    shadow(d, 7, 55, 24, 63, 90)
    d.polygon([(10, 60), (21, 60), (18, 54), (13, 54)], fill=BRASS_DK, outline=INK)     # the foot
    d.rectangle([14, 30, 17, 54], fill=BRASS)
    d.line([14, 30, 14, 54], fill=BRASS_HI)
    d.line([17, 30, 17, 54], fill=BRASS_DK)
    for y in (36, 46):
        d.rectangle([12, y, 19, y + 2], fill=BRASS, outline=BRASS_DK)
    d.polygon([(8, 27), (23, 27), (20, 31), (11, 31)], fill=BRASS, outline=INK)         # the pan
    d.line([10, 28, 21, 28], fill=BRASS_HI)
    d.rectangle([12, 13, 19, 27], fill=WHITE, outline=PAPER_SH)   # the candle
    d.line([18, 14, 18, 26], fill=PAPER_SH)
    d.line([13, 13, 13, 19], fill=PAPER)
    d.point((12, 20), fill=WHITE)
    d.line([15, 10, 15, 12], fill=INK)
    d.polygon([(15, 2), (18, 8), (16, 11), (14, 11), (12, 8)], fill=FLAME)
    d.polygon([(15, 5), (17, 9), (15, 11), (14, 9)], fill=FLAME_HI)
    return im


def candles():
    """A rack of votive candles: three steps of them under a little roof."""
    im, d = new(2 * C, 2 * C)
    shadow(d, 3, 54, 60, 63, 90)
    for x in (6, 55):
        d.rectangle([x, 14, x + 2, 60], fill=LQ)
        d.line([x, 14, x, 60], fill=LQ_HI)
    d.rectangle([8, 18, 55, 56], fill=rgb('20212a'))               # the dark behind the flames
    d.polygon([(1, 14), (62, 14), (56, 5), (7, 5)], fill=BRONZE_DK, outline=INK)        # the roof
    d.line([8, 6, 55, 6], fill=BRONZE_HI)
    for x in range(10, 56, 6):
        d.line([x, 7, x - 1 if x < 32 else x + 1, 13], fill=BRONZE)
    rnd = random.Random(31)
    for t, y in enumerate((30, 41, 52)):
        box(d, 5, y, 58, y + 3, LQ)
        d.line([6, y + 1, 57, y + 1], fill=GOLD_DK)
        for i in range(8):
            if rnd.random() < 0.82:
                candle(d, 9 + i * 6, y - 1, 3 + rnd.randrange(3))
            else:
                d.rectangle([9 + i * 6, y - 2, 10 + i * 6, y - 1], fill=PAPER_SH)       # burnt down
    d.rectangle([4, 56, 59, 60], fill=LQ, outline=INK)
    return im


def drum():
    """The great drum on its stand, its skin to the hall, a three-comma crest
    painted on it, the sticks in their rest."""
    im, d = new(2 * C, 2 * C)
    shadow(d, 4, 54, 59, 63, 100)
    for x in (10, 50):                                            # the stand
        d.rectangle([x, 34, x + 3, 60], fill=LQ)
        d.line([x, 34, x, 60], fill=LQ_HI)
    box(d, 6, 57, 57, 60, LQ)
    d.line([7, 58, 56, 58], fill=GOLD_DK)
    d.ellipse([8, 2, 55, 49], fill=WOOD_DK, outline=INK)          # the body
    d.ellipse([11, 5, 52, 46], fill=rgb('d7d0ba'), outline=WOOD)   # the skin
    d.arc([12, 6, 51, 45], 150, 280, fill=WHITE)
    for a in range(0, 360, 20):                                   # the tacks round it
        x, y = 31.5 + 22 * math.cos(math.radians(a)), 25.5 + 22 * math.sin(math.radians(a))
        d.point((round(x), round(y)), fill=BRASS_HI)
    for a in (90, 210, 330):                                      # the crest
        x, y = 31.5 + 6 * math.cos(math.radians(a)), 25.5 + 6 * math.sin(math.radians(a))
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=INK)
        tx, ty = 31.5 + 11 * math.cos(math.radians(a + 55)), 25.5 + 11 * math.sin(math.radians(a + 55))
        d.line([x, y, tx, ty], fill=INK, width=2)
    d.line([20, 52, 44, 50], fill=WOOD_HI)                        # the sticks
    d.line([20, 54, 44, 53], fill=WOOD_HI)
    return im


def keisu():
    """The bowl bell: dark bronze on a ring cushion on a lacquer stand, its striker beside it."""
    im, d = new(2 * C, 2 * C)
    shadow(d, 4, 54, 59, 63, 100)
    box(d, 12, 46, 51, 60, LQ)                                    # the stand
    d.line([13, 47, 50, 47], fill=LQ_HI)
    d.line([13, 57, 50, 57], fill=GOLD_DK)
    for x in (14, 47):
        stud(d, x, 51)
    d.ellipse([8, 36, 55, 50], fill=PURPLE, outline=INK)          # the cushion
    d.arc([9, 37, 54, 49], 180, 300, fill=PURPLE_HI)
    for x in range(14, 52, 6):
        d.point((x, 47), fill=GOLD)
    bowl, bowl_hi, bowl_dk = rgb('6b5241'), rgb('b2a168'), rgb('433830')
    d.ellipse([6, 8, 57, 46], fill=bowl, outline=INK)             # the bowl: wide, round-bellied
    for y in range(18, 44):
        half = round(25 * math.sqrt(max(0.0, 1 - ((y - 27) / 19.0) ** 2)))
        d.line([32 - half + 2, y, 32 - half + 5, y], fill=bowl_hi)
        d.line([32 + half - 8, y, 32 + half - 1, y], fill=bowl_dk)
    d.ellipse([8, 8, 55, 24], fill=bowl_hi, outline=INK)          # its mouth
    d.ellipse([12, 10, 51, 22], fill=LQ_DK, outline=bowl_dk)
    d.arc([12, 10, 51, 22], 20, 160, fill=bowl)
    d.line([14, 32, 49, 32], fill=BRASS_HI)                       # an engraved band
    d.line([14, 34, 49, 34], fill=bowl_dk)
    d.line([56, 30, 62, 58], fill=VERM_DK, width=2)               # the striker, leaning
    d.rectangle([54, 24, 59, 32], fill=rgb('d7d0ba'), outline=INK)
    return im


def musubi():
    """The rail the unlucky fortunes are tied to: wires between two posts, white knots all along."""
    im, d = new(2 * C, 2 * C)
    shadow(d, 3, 55, 60, 63, 80)
    for x in (4, 56):
        post(d, x, 8, x + 3, 60, VERM_DK, VERM, RED_DK)
        d.rectangle([x - 1, 5, x + 4, 8], fill=LQ, outline=INK)
    rnd = random.Random(99)
    for y in (16, 26, 36, 46):
        d.line([8, y, 55, y], fill=LQ_HI)
        x = 10
        while x < 53:
            if rnd.random() < 0.85:
                d.rectangle([x, y - 1, x + 2, y + 1], fill=WHITE)             # a knot
                d.line([x + 1, y + 2, x + rnd.randrange(3), y + 5 + rnd.randrange(3)], fill=WHITE)
                d.point((x, y + 2), fill=PAPER_SH)
            x += 4
    box(d, 2, 58, 61, 61, LQ)
    return im


def bench():
    """A plain bench for the old and the footsore, a red cloth over it (2x1)."""
    im, d = new(2 * C, C)
    shadow(d, 3, 22, 60, 31, 80)
    for x in (8, 53):
        d.rectangle([x, 16, x + 2, 28], fill=WOOD_DK)
        d.line([x, 16, x, 28], fill=WOOD)
    d.polygon([(3, 16), (60, 16), (56, 6), (7, 6)], fill=VERM_DK, outline=INK)
    d.line([8, 7, 55, 7], fill=VERM)
    box(d, 3, 16, 60, 20, RED_DK)
    d.line([4, 17, 59, 17], fill=RED)
    for x in range(10, 56, 9):
        d.point((x, 11), fill=GOLD_DK)
    return im


def renge():
    """A tall bronze vase of gilt lotus, as stand either side of a hall's doors (1x2)."""
    im, d = new(C, 2 * C)
    shadow(d, 6, 55, 25, 63, 90)
    d.polygon([(10, 60), (21, 60), (19, 54), (12, 54)], fill=BRONZE_DK, outline=INK)
    d.polygon([(11, 54), (20, 54), (23, 40), (19, 32), (12, 32), (8, 40)], fill=BRONZE, outline=INK)
    d.line([11, 40, 13, 34], fill=BRONZE_HI)
    d.line([20, 42, 19, 52], fill=BRONZE_DK)
    d.line([10, 44, 21, 44], fill=BRASS)
    box(d, 11, 29, 20, 32, BRONZE_DK)
    for dx, top, bloom in ((-8, 6, True), (0, 2, True), (8, 9, True), (-4, 14, False), (5, 17, False), (-10, 18, False)):
        d.line([15 + dx // 3, 29, 15 + dx, top + 4], fill=GOLD_DK)
        if bloom:
            lotus(d, 15 + dx, top + 5, GOLD, GOLD_HI)
        else:
            d.ellipse([15 + dx - 4, top, 15 + dx + 4, top + 5], fill=GOLD_DK, outline=GOLD)
    return im


def haze():
    """Incense haze: a few pale strata hanging in the air, barely there (Tops)."""
    im, d = new(3 * C, 2 * C)
    rnd = random.Random(645)
    for y0, x0, ln, a in ((10, 6, 70, 46), (22, 20, 64, 38), (36, 2, 80, 42), (48, 26, 56, 32)):
        for x in range(x0, x0 + ln):
            t = (x - x0) / ln
            yy = y0 + math.sin(t * 6.0 + y0) * 2.2
            thick = 1 + round(2.2 * math.sin(t * math.pi))
            aa = round(a * math.sin(t * math.pi))
            for k in range(-thick, thick + 1):
                py = round(yy + k)
                if 0 <= py < 2 * C and 0 <= x < 3 * C and aa > 3 and rnd.random() < 0.9:
                    im.putpixel((x, py), SMOKE + (round(aa * (1 - abs(k) / (thick + 1))),))
    return im


def sprites():
    return {
        'temple-in-slab-a': slab(0), 'temple-in-slab-b': slab(1),
        'temple-in-side-w': wall_side('w'), 'temple-in-side-e': wall_side('e'),
        'temple-in-sun-w': sun('w'), 'temple-in-sun-e': sun('e'),
        'temple-in-wall-front': wall_front,
        'temple-in-threshold-w': threshold('w'), 'temple-in-threshold-e': threshold('e'),
        'temple-in-doorlight': doorlight,
        'temple-in-wall-charms': wall_charms,
        'temple-in-wall-tennin-l': wall_tennin('l'), 'temple-in-wall-tennin-r': wall_tennin('r'),
        'temple-in-kuden': kuden,
        'temple-in-omikuji': omikuji,
        'temple-in-naijin': naijin,
        'temple-in-pillar': pillar,
        'temple-in-saisen': saisen,
        'temple-in-jokoro': jokoro,
        'temple-in-chochin': chochin,
        'temple-in-toro-hang': toro_hang, 'temple-in-shokudai': shokudai,
        'temple-in-candles': candles,
        'temple-in-drum': drum, 'temple-in-keisu': keisu,
        'temple-in-musubi': musubi,
        'temple-in-bench': bench, 'temple-in-renge': renge,
        'temple-in-haze': haze,
    }


# The hung pieces are Tops under four rows tall: lifted in front of whatever
# taller thing stands behind them. The light through a door lies on the floor.
DEPTH_BIAS = {'temple-in-toro-hang': 10, 'temple-in-chochin': 10, 'temple-in-haze': 10, 'temple-in-doorlight': -40}


def settle(im):
    """Move every pixel that is not a PACK colour to the nearest one that is; alpha is kept."""
    px, memo = im.load(), {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0 or (r, g, b) in PACK_SET:
                continue
            k = (r, g, b)
            if k not in memo:
                memo[k] = min(PACK, key=lambda c: 2 * (c[0] - r) ** 2 + 4 * (c[1] - g) ** 2 + 3 * (c[2] - b) ** 2)
            px[x, y] = memo[k] + (a,)
    return im


def main():
    built = {}
    for name, fn in sprites().items():
        im = settle(fn())
        built[name] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if name in DEPTH_BIAS:
            cfg['spriteMetadata'][key]['depthBias'] = DEPTH_BIAS[name]
        cfg.setdefault('tileNames', {})[key] = name
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        rows, x, y, rowh, width = [], 16, 16, 0, 1600
        for im in built.values():
            if x + im.width + 16 > width:
                x, y, rowh = 16, y + rowh + 16, 0
            rows.append((im, x, y))
            x += im.width + 16
            rowh = max(rowh, im.height)
        sheet = Image.new('RGBA', (width, y + rowh + 16), (95, 107, 133, 255))
        for im, x, y in rows:
            sheet.alpha_composite(im, (x, y))
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
