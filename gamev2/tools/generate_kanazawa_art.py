#!/usr/bin/env python3
"""generate_kanazawa_art.py — draw Kanazawa's own buildings and street pieces (issue #219).

The audit of #210 found Kanazawa shares 0.63 of its sprites with Sendai: it
stands on Sendai's earthen wall, Sendai's gate, Sendai's trees and the generic
machiya and townhouses. These are the pieces its six districts are rebuilt
from, drawn the way generate_sapporo_art.py draws Sapporo's: shaded pixel art
in the GuttyKreum palette, at half size (one drawn pixel = one pixel of a 32px
tile) and pixel-doubled, lit from the left, with a 1px ink outline. Not
line-art placeholders. The town is seasoned for early November as the rest of
the region is (ginkgo gold, maples, no lying snow), so nothing here carries
snow; winter shows in the yukitsuri ropes and the komo straw mats, which go
up on 1 November. Every name on a sign is a generic word or a look-alike.

Station front
  kanazawa-station-dome_0_0     8x4  the Motenashi dome: a low, wide glass shell
                                     in an aluminium rim over a plain glazed
                                     concourse; an entrance two cells wide
  kanazawa-tsuzumi-gate_0_0     6x5  the Tsuzumi-mon drum gate: two drum pillars
                                     of twisted timber under one deep, flat,
                                     coffered lattice roof; you walk under it.
                                     Its feet go five rows south of the dome's
  kanazawa-bus-stop_0_0         2x2  the stop for the Shirakawa-go bus
Kanazawa Castle
  kanazawa-castle-gate_0_0      4x4  the Ishikawa gate as a gatehouse: white
                                     plaster and namako tile over stone piers,
                                     a lead roof; walk through the middle two
  kanazawa-castle-turret_0_0    4x5  a two-storey yagura on a battered stone base
  kanazawa-castle-storehouse_0_0 6x3 a long plastered storehouse for the terrace
  kanazawa-castle-wall_0_0      1x2  the long white wall, east-west (white
                                     lattice on dark for its namako band)
  kanazawa-castle-wall-corner-e / -corner-w   1x2  its ends where it turns
                                     north, each drawn for its own side
  kanazawa-castle-wall-v_0_0    1x2  the wall running north-south: coping from
                                     above on the top cell, the wall's face and
                                     stone foot on the bottom one
  kanazawa-castle-wall-end_0_0  1x2  the hipped south end of a north-south run
Kenrokuen
  kenrokuen-kotoji_0_0          2x3  the Kotoji lantern, two-legged, the hero piece
  kenrokuen-kotoji-water_0_0    2x3  the same with its long leg standing in water
                                     (bottom-left cell on pond, bottom-right on bank)
  kenrokuen-yukitsuri_0_0       3x4  a great pine under its cone of ropes
  kenrokuen-yukitsuri-small_0_0 2x3  a smaller one
  kenrokuen-teahouse_0_0        4x3  the tea house standing in the pond on posts
  kenrokuen-bridge_0_0          3x1  a stone slab bridge seen from above (flat,
                                     walked ON, like kanazawa-canal-bridge)
  garden-moss_0_0               1x1  moss in low cushions, blue-green (a ground tile)
  garden-path-autotile_*        1x1  a pale gravel path edged with stones, moss
                                     outside it (9 autotile roles)
Higashi Chaya
  chaya-front-a / -b / -c_0_0   3x4  two-storey teahouse fronts in dark bengara
                                     with kimusuko lattice; they tile along a street
  chaya-gold-leaf-shop_0_0      4x4  the gold-leaf shop: a gilded upper wall, a
                                     gold-leaf soft-serve sign
  chaya-phono-museum_0_0        3x4  the phonograph museum: a grey clapboard
                                     front under a horn-gramophone roundel
  chaya-stone-autotile_*        1x1  the stone-flagged lane: big low-contrast
                                     flags (9 autotile roles)
  teramachi-stair_0_0           2x3  the temple hill's stone stair (flat, walked
                                     ON; tiles north-south)
  teramachi-gate_0_0            3x3  a small mossy-shingled temple gate; walk through
  teramachi-hall_0_0            5x4  a temple hall: smoked-tile hip roof, a
                                     gabled porch, shoji bays, steps
Katamachi
  katamachi-whisky-bar_0_0      3x5  a narrow dark-brick whisky bar
  katamachi-izakaya_0_0         4x4  an all-you-can-drink izakaya
  katamachi-kissaten_0_0        3x4  a Showa coffee shop: pink tile, striped awning
  katamachi-yakitori_0_0        3x3  a yakitori counter: a big red lantern, a grill
  katamachi-andon-lanterns_0_0  1x2  a tall paper andon post, the quarter's name
                                     down it. Its key holds `-lanterns`, so
                                     src/DayNight.js gives it a halo at night
                                     like every other lantern
Nagamachi
  nagamachi-wall_0_0            1x2  the ochre earthen wall under its winter komo
                                     (straw mats bound with ropes, a fringe), on
                                     river stones, a shingle cap
  nagamachi-wall-bare_0_0       1x2  the same without mats
  nagamachi-wall-corner-e / -corner-w, -v, -end   as the castle wall's
  nagamachi-wall-gate_0_0       1x2  a roofed wicket in the wall; walk through
  nagamachi-samurai-gate_0_0    5x3  a samurai house's nagaya-mon gatehouse
  nagamachi-samurai-house_0_0   5x4  the house in the court behind it
  nagamachi-canal-n / -s_0_0    1x1  the canal's stone banks (ground tiles): the
                                     north bank's wall over the water, the south
                                     bank's coping

This tool only writes the PNGs into assets/sprites/. It registers nothing:
config.json, the palette, prefabs, generators and check_generators.py are for
the map change that places these. tools/generate_hokuriku_art.py keeps the
region's older sprites (kanazawa-ishikawa-gate, -kotoji, -chaya-a/-b, ...);
none of its keys is written here.

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs Pillow, and three sibling tools on the import path, so run it from where
it lives (it cannot be copied out alone): it imports the palette and helpers
of tools/generate_hokkaido.py, generate_sendai_art.py and
generate_sapporo_art.py (importing them draws nothing). Plain python3 here has
no Pillow; /Library/Developer/CommandLineTools/usr/bin/python3 does. Run from gamev2/:
    python3 tools/generate_kanazawa_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
--scenes also writes each scene as <name>_night.png: the night grade and the
manifest's glow spots as DayNight / Glows would draw them (a Pillow preview).
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

from generate_hokkaido import (rgb, canvas, outline, tiles, CLEAR, INK, NAVY,
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK,
                               WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_sendai_art import (blob, SLATE, SLATE_HI, SLATE_LO, PINE, PINE_HI, PINE_LO, PINE_DK,
                                 BARK, BARK_LO, MAPLE, MAPLE_OR, LACQUER, LACQUER_HI, LACQUER_LO)
from generate_sapporo_art import FONT as _FONT, KANA as _KANA, glyphs, lantern, glass_door

SPR = 'assets/sprites'
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')

# ---- Kanazawa's colours ---------------------------------------------------------
LEAD_P = (rgb('b9c3ca'), rgb('8c97a3'), rgb('e3e9ed'), rgb('687382'))       # lead tiles: light, joint, lit, deep
KAWARA_P = (rgb('3b3f4e'), rgb('282b38'), rgb('666c80'), rgb('1a1c26'))     # Hokuriku's black glazed tiles
SHINGLE_P = (rgb('7f6a5b'), rgb('5e4d46'), rgb('a38b76'), rgb('403634'))    # cedar-bark shingles
PLASTER, PLASTER_LO, PLASTER_SH = rgb('f4f1ea'), rgb('d3cdc2'), rgb('b4aea6')
KIM, KIM_HI, KIM_LO, KIM_DK = rgb('7c3d31'), rgb('9c5341'), rgb('5c2c28'), rgb('3c2022')   # bengara, aged
OCHRE, OCHRE_HI, OCHRE_LO, OCHRE_DK = rgb('c99f5a'), rgb('dfbb7a'), rgb('a67e44'), rgb('7b5c38')
STRAW, STRAW_HI, STRAW_LO, ROPE = rgb('cdb67c'), rgb('e6d6a2'), rgb('a8925c'), rgb('7d6038')
MOSS, MOSS_HI, MOSS_LO, MOSS_DK = rgb('4f8250'), rgb('6a9c59'), rgb('447549'), rgb('35603f')
LEAF, LEAF_HI, LEAF_LO, LEAF_DK = rgb('f0cc50'), rgb('fff2a8'), rgb('c8982c'), rgb('93701f')   # gold leaf
TIMBER, TIMBER_HI, TIMBER_LO, TIMBER_DK = rgb('b06a42'), rgb('d48e5e'), rgb('854a30'), rgb('532c22')
ALU, ALU_LO, ALU_DK = rgb('dfe6ec'), rgb('a9b6c4'), rgb('76849a')
GRAN, GRAN_HI, GRAN_LO, GRAN_DK = rgb('a9aeb2'), rgb('d2d7da'), rgb('7c8089'), rgb('545866')   # weathered granite
DBRICK, DBRICK_HI, DBRICK_LO = rgb('5c3b37'), rgb('77514a'), rgb('432a2b')
WATER, WATER_DK, WATER_HI = rgb('425faa'), rgb('36508f'), rgb('8ec2fa')     # pond-autotile's own blue
WARM, LIT = rgb('f6dc8c'), rgb('f2c66a')
SOOT, SOOT_LO = rgb('2b2a30'), rgb('1a191e')
INDIGO, INDIGO_HI = rgb('2c3d6a'), rgb('4b6396')
KAKI = rgb('d9773a')                                                         # persimmon
PAPER, PAPER_LO = rgb('f1e9d6'), rgb('cfc4aa')
GINKGO = rgb('e8b93a')

FONT = dict(_FONT)
FONT.update({
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
})
KANA = dict(_KANA)
KANA.update({      # ミ ホ ウ ダ イ, for ノミホウダイ (all you can drink); マ チ for カタマチ; ヤ ト for ヤキトリ
    'ma': ['#######', '......#', '.....#.', '..#.#..', '...#...', '....#..', '.......'],
    'chi': ['....##.', '.###...', '...#...', '#######', '...#...', '..#....', '.#.....'],
    'ya': ['..#....', '..#.###', '####..#', '..#..#.', '..#....', '...#...', '...#...'],
    'to': ['..#....', '..#....', '..##...', '..#.##.', '..#....', '..#....', '..#....'],
    'mi': ['.####..', '.....#.', '.###...', '....##.', '.......', '####...', '....###'],
    'ho': ['...#...', '#######', '...#...', '.#.#.#.', '.#.#.#.', '#..#..#', '..##...'],
    'u':  ['...#...', '#######', '#.....#', '#.....#', '.....#.', '....#..', '..##...'],
    'da': ['..#.#.#', '..####.', '.#...#.', '#.##.#.', '....#..', '...#...', '.##....'],
    'i':  ['.....#.', '....#..', '...#...', '.###...', '#..#...', '...#...', '...#...'],
})


def text(d, s, x, y, fill, scale=1, vertical=False):
    glyphs(d, [FONT[c] for c in s], x, y, fill, scale, 1, vertical)


def kana(d, names, x, y, fill, scale=1, vertical=False):
    glyphs(d, [KANA[n] for n in names], x, y, fill, scale, 1, vertical)


def text_w(s):
    return len(s) * 6 - 1


def h3(x, y, s=0):
    """A small deterministic hash, for speckle."""
    return (x * 73 + y * 151 + (x * y) * 31 + s * 97 + (x ^ (y * 5)) * 13) % 251


def shade(im, box, col):
    """Lay a translucent rectangle over what is drawn (ImageDraw would replace it)."""
    ov = Image.new('RGBA', im.size, CLEAR)
    ImageDraw.Draw(ov).rectangle(box, fill=col)
    im.alpha_composite(ov)


# ---- surfaces -------------------------------------------------------------------
def curve_rows(y0, y1, top, bottom, p=1.5):
    """Scanlines of a roof slope that flares toward the eave."""
    out = []
    for y in range(y0, y1 + 1):
        t = ((y - y0) / max(1, y1 - y0)) ** p
        out.append((y, round(top[0] + (bottom[0] - top[0]) * t), round(top[1] + (bottom[1] - top[1]) * t)))
    return out


def roof(d, y0, y1, top, bottom, pal=KAWARA_P, ridge=True, p=1.5, step=4, caps=True):
    """A tiled slope from `top` (x0, x1) at y0 to `bottom` at y1: the lit west
    hip, the shaded east one, an eave of round tile ends (3px below y1) and,
    with `ridge`, the ridge bar (5px above y0) and its end tiles."""
    light, dark, hi, deep = pal
    rows = curve_rows(y0, y1, top, bottom, p)
    tiles(d, rows, light, dark, step)
    for y, x0, x1 in rows:
        d.point((x0, y), fill=hi); d.point((x0 + 1, y), fill=hi)
        d.point((x1, y), fill=deep); d.point((x1 - 1, y), fill=dark)
        if (y - y0) % step == 0:                                  # each course's lit lip, to the west
            for x in range(x0 + 2, x0 + (x1 - x0) // 3, 6):
                d.point((x + (y // step) % 2 * 3, y), fill=hi)
    bx0, bx1 = bottom
    d.rectangle([bx0, y1 + 1, bx1, y1 + 2], fill=dark)
    d.line([(bx0, y1 + 3), (bx1, y1 + 3)], fill=deep)
    for x in range(bx0 + 1, bx1, 4):
        d.point((x, y1 + 2), fill=hi)
    if ridge:
        tx0, tx1 = top
        d.rectangle([tx0 - 3, y0 - 5, tx1 + 3, y0 - 1], fill=dark)
        d.line([(tx0 - 3, y0 - 5), (tx1 + 3, y0 - 5)], fill=hi)
        d.line([(tx0 - 3, y0 - 1), (tx1 + 3, y0 - 1)], fill=deep)
        for x in range(tx0, tx1, 5):
            d.point((x, y0 - 3), fill=light)
        if caps:
            for x0 in (tx0 - 7, tx1 + 2):
                d.rectangle([x0, y0 - 8, x0 + 5, y0], fill=light)
                d.line([(x0, y0 - 8), (x0, y0)], fill=hi)
                d.line([(x0 + 5, y0 - 7), (x0 + 5, y0)], fill=dark)


STONES = (STONE, rgb('cdd3d7'), rgb('c5bbba'), rgb('b0b9c5'), STONE, rgb('d8dcdf'), rgb('b5b2b9'))


def stonework(d, x0, y0, x1, y1, seed=0, ch=8):
    """Kanazawa Castle's fitted Tomuro stone: grey with the odd red and blue
    block. Periodic in x at 32, so a run of wall tiles joins."""
    cuts = (0, 11, 21)
    for y in range(y0, y1 + 1):
        j = (y - y0) // ch
        yy = (y - y0) % ch
        off = (j * 13 + seed * 7) % 32
        for x in range(x0, x1 + 1):
            u = (x - off) % 32
            seg = 2 if u >= 21 else (1 if u >= 11 else 0)
            first = u in cuts
            tone = STONES[(seg * 3 + j * 5 + ((x - off) // 32) * 2 + seed) % 7]
            if first or yy == ch - 1:
                c = STONE_LO
            elif yy == 0:
                c = WHITE if tone != STONES[2] else rgb('e6d6d3')
            elif u in (10, 20, 31) and yy > 1:
                c = rgb('9da3ad')
            else:
                c = tone
            d.point((x, y), fill=c)


COBBLES = (rgb('b3a48c'), rgb('9c9486'), rgb('c4baa6'), rgb('8f8a86'), rgb('a89c90'))


def cobbles(d, x0, y0, x1, y1, seed=0):
    """Round river stones laid dry: the foot of a Nagamachi wall. Period 32."""
    for y in range(y0, y1 + 1):
        j = (y - y0) // 6
        yy = (y - y0) % 6
        off = (j * 4 + seed * 3) % 8
        for x in range(x0, x1 + 1):
            u = (x - off) % 8
            k = ((x - off) // 8) % 4
            tone = COBBLES[(k * 2 + j * 3 + seed) % 5]
            corner = (u in (0, 7) and yy in (0, 5))
            if corner or u == 7 and yy == 5:
                c = rgb('5f5850')
            elif yy == 5 or u == 7:
                c = rgb('776e64')
            elif yy == 0 and 1 <= u <= 4:
                c = rgb('ddd5c4')
            else:
                c = tone
            d.point((x, y), fill=c)


def namako(d, x0, y0, x1, y1):
    """Namako-kabe: square slate tiles set on the diagonal, their joints raised
    in white plaster, so the band is a white lattice on dark (period 8 in x:
    a run of wall tiles joins)."""
    for y in range(y0, y1 + 1):
        v = y - y0
        for x in range(x0, x1 + 1):
            lattice = v == 0 or y == y1 or (x + v) % 8 == 0 or (x - v) % 8 == 0
            d.point((x, y), fill=PLASTER if lattice else SLATE)
    d.line([(x0, y1 + 1), (x1, y1 + 1)], fill=PLASTER_SH)


def kimusuko(d, x0, y0, x1, y1, lit=False, bar=KIM, gap=KIM_DK):
    """Kimusuko: a screen of fine vertical slats, one drawn pixel each, tied by
    a rail; lamplight shows between the slats when the room is lit."""
    d.rectangle([x0, y0, x1, y1], fill=LIT if lit else gap)
    for x in range(x0, x1 + 1, 2):
        d.line([(x, y0), (x, y1)], fill=bar)
    if lit:
        d.line([(x0, y0), (x1, y0)], fill=WARM)
    m = (y0 + y1) // 2
    d.line([(x0, m), (x1, m)], fill=bar)
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y0 - 1], fill=KIM_DK)
    d.rectangle([x0 - 1, y1 + 1, x1 + 1, y1 + 1], fill=KIM_DK)


def sudare(d, x0, y0, x1, y1):
    """A bamboo blind rolled part way down."""
    d.rectangle([x0, y0, x1, y1], fill=STRAW)
    for y in range(y0 + 1, y1 + 1, 2):
        d.line([(x0, y), (x1, y)], fill=STRAW_LO)
    d.line([(x0, y0), (x1, y0)], fill=STRAW_HI)
    d.rectangle([x0, y1, x1, y1 + 1], fill=ROPE)
    for x in (x0 + 3, x1 - 3):
        d.line([(x, y0), (x, y1)], fill=ROPE)


def barred(d, x0, y0, x1, y1, frame=PLASTER_LO):
    """A musha-mado: a dark opening behind stout white bars."""
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=frame)
    d.rectangle([x0, y0, x1, y1], fill=SOOT)
    for x in range(x0 + 2, x1, 4):
        d.line([(x, y0), (x, y1)], fill=PLASTER)
    d.line([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], fill=PLASTER_SH)


def noren(d, x0, y0, x1, y1, body, hi, mark, slits=2):
    d.rectangle([x0, y0, x1, y1], fill=body)
    d.line([(x0, y0), (x1, y0)], fill=hi)
    d.line([(x0, y0 - 1), (x1, y0 - 1)], fill=WOOD_DK)             # the pole
    w = (x1 - x0 + 1) / (slits + 1)
    for k in range(1, slits + 1):
        x = round(x0 + k * w)
        d.line([(x, y0 + 3), (x, y1)], fill=SOOT_LO)
    for k in range(slits + 1):                                    # the hem lifts between the panels
        xa = round(x0 + k * w) + 1
        d.point((xa, y1), fill=SOOT_LO)
    if mark:
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=mark)
        d.point((cx, cy), fill=body)


def sliding_doors(d, x0, y0, x1, y1, lit=True, frame=KIM_DK):
    """A pair of koshi-do: paper behind a wooden grid, lamplight inside."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    m = (x0 + x1) // 2
    for a, b in ((x0 + 1, m - 1), (m + 1, x1 - 1)):
        d.rectangle([a, y0 + 1, b, y1 - 8], fill=LIT if lit else PAPER)
        d.line([(a, y0 + 1), (b, y0 + 1)], fill=WARM if lit else WHITE)
        for x in range(a + 2, b, 3):
            d.line([(x, y0 + 1), (x, y1 - 8)], fill=frame)
        for y in range(y0 + 6, y1 - 8, 6):
            d.line([(a, y), (b, y)], fill=frame)
        d.rectangle([a, y1 - 7, b, y1], fill=KIM_LO)
        d.line([(a, y1 - 7), (b, y1 - 7)], fill=KIM)


def paper_lantern(d, x, y, w=7, h=12, mark=RED):
    """A white paper lantern with a mark, on its hook."""
    d.rectangle([x + 2, y, x + w - 3, y + 1], fill=SOOT)
    d.rectangle([x, y + 2, x + w - 1, y + h - 3], fill=PAPER)
    d.line([(x, y + 2), (x, y + h - 3)], fill=WHITE)
    d.line([(x + w - 1, y + 2), (x + w - 1, y + h - 3)], fill=PAPER_LO)
    d.rectangle([x + 2, y + 4, x + w - 3, y + h - 5], fill=mark)
    d.rectangle([x + 1, y + h - 2, x + w - 2, y + h - 1], fill=SOOT)


def dbrick(d, x0, y0, x1, y1):
    """Dark, smoke-stained brick."""
    for y in range(y0, y1 + 1):
        course = (y - y0) // 3
        for x in range(x0, x1 + 1):
            if (y - y0) % 3 == 2 or (x + course * 4) % 8 == 0:
                c = DBRICK_LO
            else:
                k = ((x + course * 4) // 8 * 7 + course * 13) % 11
                c = DBRICK_HI if k in (0, 6) else DBRICK
            d.point((x, y), fill=c)


def sparkle(d, x, y, c=WHITE):
    d.point((x, y), fill=c)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.point((x + dx, y + dy), fill=LEAF_HI)


# ==============================================================================
# Station front
# ==============================================================================
def station_dome():
    im, d = canvas(8, 4)                 # 256 x 128; the doors are columns 3-4 (x 96-159)
    px = im.load()
    # ---- the shell: a low, wide cap of glass on a diamond grid of aluminium
    # (a shallow segment of a big circle, not a half round), in a heavy rim
    R, cx = 176.0, 127.5
    cy = 4 + R
    for y in range(4, 62):
        for x in range(256):
            r = math.hypot(x - cx, y - cy)
            if r > R:
                continue
            u, v = (x - cx) / 127.5, (y - 60) / 56.0
            if r > R - 6:                                         # the aluminium rim
                c = ALU_DK if r < R - 5 else (ALU_LO if r < R - 3.4 else ALU)
                if r > R - 2 and u < 0.3:
                    c = WHITE
                if x % 16 == 8 and R - 5 <= r <= R - 2:
                    c = ALU_DK                                    # its bolted joints
            elif (x + y) % 14 == 0 or (x - y) % 14 == 0:
                c = ALU if (u + v) < -0.5 else ALU_LO
            else:
                band = (x + 2 * y) // 26 % 4
                if y > 49:
                    c = rgb('34487a') if band else rgb('3d5386')  # the low panes look into the hall
                elif band == 0:
                    c = rgb('86b4e8') if u < 0.1 else rgb('6583bd')
                elif u + v < -0.9:
                    c = rgb('6f93cf')
                else:
                    c = GLASS if u < 0.45 else rgb('40568a')
            px[x, y] = c
    # ---- the ring beam it springs from
    d.rectangle([0, 60, 255, 67], fill=ALU)
    d.line([(0, 60), (255, 60)], fill=WHITE)
    d.rectangle([0, 66, 255, 67], fill=ALU_LO)
    for x in range(6, 252, 12):
        d.point((x, 63), fill=ALU_DK)
    # ---- the concourse front: a louvred band with the name, a thin canopy, plain glass
    d.rectangle([0, 68, 255, 79], fill=rgb('c9d2da'))
    for y in (70, 73, 76, 79):
        d.line([(0, y), (255, y)], fill=ALU_LO)
    d.rectangle([88, 68, 167, 80], fill=SOOT)
    d.rectangle([89, 69, 166, 79], fill=rgb('30343f'))
    text(d, 'KANAZAWA', 128 - text_w('KANAZAWA') // 2, 71, WHITE)
    d.rectangle([0, 81, 255, 84], fill=ALU)
    d.line([(0, 81), (255, 81)], fill=WHITE)
    d.line([(0, 84), (255, 84)], fill=ALU_DK)
    d.rectangle([0, 85, 255, 123], fill=rgb('34487a'))
    d.line([(0, 85), (255, 85)], fill=rgb('1a2140'))
    for k in range(16):
        x0 = k * 16
        d.rectangle([x0 + 2, 86, x0 + 15, 103], fill=GLASS)
        d.line([(x0 + 2, 86), (x0 + 15, 86)], fill=GLASS_HI)
        if k % 3 == 0:
            d.line([(x0 + 12, 88), (x0 + 6, 102)], fill=rgb('6f93cf'))
            d.line([(x0 + 13, 88), (x0 + 7, 102)], fill=rgb('6f93cf'))
        elif k % 3 == 1:
            d.line([(x0 + 9, 88), (x0 + 5, 97)], fill=rgb('6f93cf'))
        d.point((x0 + 8, 108), fill=WARM)                         # the hall's lamps, far inside
        d.line([(x0 + 2, 104), (x0 + 15, 104)], fill=ALU_LO)
        d.line([(x0 + 2, 119), (x0 + 15, 119)], fill=rgb('4b6396'))
        d.rectangle([x0, 85, x0 + 1, 123], fill=ALU)
        d.line([(x0 + 1, 85), (x0 + 1, 123)], fill=ALU_LO)
    for x in (0, 92, 160, 252):                                   # the columns
        d.rectangle([x, 68, x + 3, 123], fill=ALU)
        d.line([(x, 68), (x, 123)], fill=WHITE)
        d.line([(x + 3, 68), (x + 3, 123)], fill=ALU_LO)
    # ---- the way in: open, the lit concourse and its gate line beyond
    d.rectangle([96, 85, 159, 123], fill=rgb('1c2748'))
    d.rectangle([96, 85, 159, 89], fill=SOOT)
    d.rectangle([120, 86, 135, 88], fill=rgb('3f9a6a'))           # the way-out sign
    d.rectangle([125, 87, 130, 87], fill=WHITE)
    for x in range(100, 158, 8):
        d.point((x, 93), fill=WARM); d.point((x + 1, 93), fill=WARM)
    for x in range(101, 154, 11):                                 # ticket gates, lit
        d.rectangle([x, 103, x + 6, 109], fill=LIT)
        d.line([(x, 103), (x + 6, 103)], fill=WARM)
        d.rectangle([x + 2, 105, x + 4, 106], fill=rgb('3f9a6a'))
    d.rectangle([96, 110, 159, 114], fill=rgb('5c5f86'))
    d.rectangle([96, 115, 159, 119], fill=rgb('8087a8'))
    d.rectangle([96, 120, 159, 123], fill=rgb('aab0c8'))
    for x0 in (96, 121, 130, 155):                                # the glass leaves, slid open
        d.rectangle([x0, 90, x0 + 4, 123], fill=GLASS)
        d.line([(x0 + 1, 91), (x0 + 1, 122)], fill=GLASS_HI)
        d.line([(x0 + 4, 90), (x0 + 4, 123)], fill=ALU_DK)
    d.rectangle([126, 85, 129, 123], fill=ALU)
    d.line([(126, 85), (126, 123)], fill=WHITE); d.line([(129, 85), (129, 123)], fill=ALU_LO)
    d.rectangle([0, 124, 255, 127], fill=STONE_LO)
    d.line([(0, 124), (255, 124)], fill=STONE)
    d.rectangle([98, 124, 157, 127], fill=rgb('e8c24a'))          # tactile paving at the doors
    for x in range(99, 157, 3):
        d.point((x, 125), fill=rgb('c79f2e')); d.point((x + 1, 126), fill=rgb('fbe38a'))
    outline(im)
    return im


def drum_pillar(d, cx, y0, y1):
    """One drum of the Tsuzumi-mon: two families of leaning timbers that cross,
    narrow at the waist, as the cords of a hand drum do."""
    mid, half = (y0 + y1) / 2, (y1 - y0) / 2

    def hw(y):
        return 6.5 + 9.5 * ((y - mid) / half) ** 2

    for y in range(y0, y1 + 1):
        w = round(hw(y))
        d.line([(cx - w, y), (cx + w, y)], fill=TIMBER_DK)
    n = 9
    for dirn in (1, -1):
        for k in range(n):
            th0 = 2 * math.pi * k / n + (0.2 if dirn < 0 else 0)
            for y in range(y0, y1 + 1):
                t = (y - y0) / (y1 - y0)
                th = th0 + dirn * t * math.pi * 0.95
                if math.cos(th) <= 0.08:
                    continue                                      # round the back
                s = math.sin(th)
                x = round(cx + (hw(y) - 0.5) * s)
                col = TIMBER_HI if s < -0.35 else (TIMBER if s < 0.45 else TIMBER_LO)
                d.point((x, y), fill=col)
                if abs(s) < 0.8:
                    d.point((x + (1 if dirn > 0 else -1), y), fill=TIMBER_LO if s > 0.2 else TIMBER)
    d.rectangle([cx - 17, y0 - 4, cx + 17, y0 - 1], fill=TIMBER_LO)        # the collar under the roof
    d.line([(cx - 17, y0 - 4), (cx + 17, y0 - 4)], fill=TIMBER_HI)
    d.rectangle([cx - 18, y1 + 1, cx + 18, y1 + 5], fill=STONE)            # the stone plinth
    d.line([(cx - 18, y1 + 1), (cx + 18, y1 + 1)], fill=WHITE)
    d.rectangle([cx - 18, y1 + 4, cx + 18, y1 + 5], fill=STONE_LO)
    d.rectangle([cx + 12, y1 + 1, cx + 18, y1 + 5], fill=STONE_LO)


def tsuzumi_gate():
    im, d = canvas(6, 5)                 # 192 x 160; pillars stand in columns 1 and 4
    # ---- the roof: one deep, flat slab of crossed timbers, seen from in front
    # and a little above, so the coffers show; no upturn, no plaque
    yb, yf, n = 5, 47, 22
    longs = (5, 10, 16, 23, 31, 40)                               # the long beams, wider apart toward the front
    coffer, coffer_dk = rgb('46282a'), rgb('2e1a1f')
    for y in range(yb, yf + 1):
        t = (y - yb) / (yf - yb)
        xa, xb = round(14 - 11 * t), round(177 + 11 * t)
        prev, run = None, 0
        for x in range(xa, xb + 1):
            k = min(n - 1, int((x - xa) * n / (xb - xa + 1)))
            run = 0 if k != prev else run + 1
            prev = k
            if x - xa < 2:
                c = TIMBER_HI
            elif xb - x < 2:
                c = TIMBER_LO
            elif y in longs or y == yf - 1:
                c = TIMBER_HI
            elif y - 1 in longs or y == yf:
                c = TIMBER
            elif run == 0:
                c = TIMBER
            elif run == 1:
                c = TIMBER_LO
            elif y - 2 in longs:
                c = coffer_dk                                     # the beam's shadow in the coffer
            else:
                c = coffer
            d.point((x, y), fill=c)
    # ---- its front edge: the fascia, a beam end at every bay
    d.rectangle([3, 48, 188, 56], fill=TIMBER)
    d.line([(3, 48), (188, 48)], fill=TIMBER_HI)
    d.line([(3, 56), (188, 56)], fill=TIMBER_LO)
    d.rectangle([184, 49, 188, 56], fill=TIMBER_LO)
    for k in range(1, n):
        x = round(3 + k * 185 / n)
        d.rectangle([x - 1, 50, x + 1, 54], fill=TIMBER_LO)
        d.line([(x - 1, 50), (x + 1, 50)], fill=TIMBER_DK)
    d.rectangle([8, 57, 183, 58], fill=TIMBER_DK)                 # the underside, in shade
    drum_pillar(d, 48, 63, 150)
    drum_pillar(d, 144, 63, 150)
    outline(im)
    return im


def bus_stop():
    im, d = canvas(2, 2)                 # 64 x 64
    # the shelter
    d.rectangle([1, 14, 46, 18], fill=ALU)
    d.line([(1, 14), (46, 14)], fill=WHITE); d.line([(1, 18), (46, 18)], fill=ALU_LO)
    d.rectangle([4, 19, 43, 29], fill=NAVY)
    d.rectangle([5, 20, 42, 28], fill=rgb('20317a'))
    text(d, 'BUS', 8, 21, WHITE)
    # the little thatched farmhouse on its board: this is the Shirakawa-go bus
    d.polygon([(34, 21), (29, 27), (39, 27)], fill=rgb('ab9272'))
    d.line([(34, 21), (29, 27)], fill=rgb('d6c19c'))
    d.rectangle([32, 25, 35, 27], fill=PAPER)
    for x in (4, 41):
        d.rectangle([x, 30, x + 2, 60], fill=STONE_DK)
        d.line([(x, 30), (x, 60)], fill=STONE_LO)
    d.rectangle([7, 30, 40, 50], fill=rgb('5a78b4', 200))         # the glass back
    d.line([(7, 30), (40, 30)], fill=GLASS_HI)
    for x in (12, 13, 26):
        d.line([(x, 33), (x - 5 if x > 12 else x, 46)], fill=rgb('9cc4f4', 220))
    d.line([(23, 30), (23, 50)], fill=STONE_DK)
    d.rectangle([9, 47, 38, 50], fill=WOOD)                       # the bench
    d.line([(9, 47), (38, 47)], fill=rgb('d2a58c')); d.line([(9, 50), (38, 50)], fill=WOOD_LO)
    for x in (11, 35):
        d.rectangle([x, 51, x + 1, 60], fill=STONE_DK)
    d.rectangle([1, 61, 46, 62], fill=STONE_LO)
    # the stop's pole: a round sign, the timetable
    d.rectangle([54, 18, 55, 60], fill=STONE_LO); d.line([(54, 18), (54, 60)], fill=STONE)
    d.ellipse([46, 2, 63, 19], fill=WHITE)
    d.ellipse([47, 3, 62, 18], fill=rgb('2f6fb5'))
    d.ellipse([49, 5, 60, 16], fill=WHITE)
    d.rectangle([51, 8, 58, 12], fill=KAKI)                       # a bus
    d.rectangle([52, 9, 53, 10], fill=GLASS); d.rectangle([55, 9, 57, 10], fill=GLASS)
    d.point((52, 13), fill=INK); d.point((57, 13), fill=INK)
    d.rectangle([49, 24, 61, 42], fill=WHITE)
    d.rectangle([49, 24, 61, 27], fill=rgb('2f6fb5'))
    for y in range(30, 41, 3):
        d.line([(51, y), (59, y)], fill=STONE_LO)
    d.rectangle([52, 59, 57, 62], fill=STONE_DK)
    outline(im)
    return im


# ==============================================================================
# Kanazawa Castle
# ==============================================================================
def castle_gate():
    im, d = canvas(4, 4)                 # 128 x 128; the gateway is columns 1-2 (x 32-95)
    # ---- the stone piers
    stonework(d, 0, 78, 33, 127, 1)
    stonework(d, 94, 78, 127, 127, 4)
    d.rectangle([28, 78, 33, 127], fill=STONE_LO)                 # the pier's reveal, in shade
    d.rectangle([94, 78, 96, 127], fill=WHITE)
    # ---- the gatehouse over them: white plaster, barred windows, a namako dado
    d.rectangle([3, 46, 124, 77], fill=PLASTER)
    d.rectangle([117, 46, 124, 77], fill=PLASTER_LO)
    d.line([(3, 46), (124, 46)], fill=PLASTER_SH)
    d.line([(3, 47), (124, 47)], fill=PLASTER_LO)
    barred(d, 12, 51, 31, 59); barred(d, 46, 51, 81, 59); barred(d, 96, 51, 115, 59)
    namako(d, 3, 63, 124, 73)
    d.rectangle([2, 74, 125, 77], fill=WOOD_DK)                   # the sill beam on the stone
    d.line([(2, 74), (125, 74)], fill=WOOD_LO)
    # ---- the lead roof
    roof(d, 15, 40, (24, 103), (0, 127), LEAD_P)
    d.rectangle([4, 44, 123, 45], fill=LEAD_P[3])
    # ---- the gateway: iron-bound posts, a lintel, the leaves folded back
    d.rectangle([34, 78, 93, 87], fill=WOOD_LO)
    d.line([(34, 78), (93, 78)], fill=WOOD); d.line([(34, 87), (93, 87)], fill=WOOD_DK)
    for x in range(40, 90, 8):
        d.rectangle([x, 81, x + 1, 84], fill=LACQUER_LO)
    for x0 in (34, 86):
        d.rectangle([x0, 88, x0 + 7, 127], fill=WOOD_LO)
        d.line([(x0, 88), (x0, 127)], fill=WOOD); d.line([(x0 + 7, 88), (x0 + 7, 127)], fill=WOOD_DK)
        for y in (94, 108, 121):
            d.rectangle([x0, y, x0 + 7, y + 2], fill=LACQUER_LO)
            d.point((x0 + 2, y + 1), fill=STONE); d.point((x0 + 5, y + 1), fill=STONE)
    for x0, x1 in ((42, 47), (80, 85)):
        d.rectangle([x0, 88, x1, 126], fill=WOOD_DK)
        d.line([(x0 + 2, 90), (x0 + 2, 125)], fill=WOOD_LO)
        for y in range(92, 124, 6):
            d.point((x0 + 4, y), fill=STONE_LO)
    for k in range(5):                                            # the plum crest on the lintel
        a = math.radians(-90 + k * 72)
        d.point((round(64 + 2.6 * math.cos(a)), round(83 + 2.6 * math.sin(a))), fill=LEAF)
    d.point((64, 83), fill=LEAF_HI)
    outline(im)
    shade(im, [48, 88, 79, 93], (10, 22, 39, 150))               # the passage's shadow
    shade(im, [48, 94, 79, 98], (10, 22, 39, 70))
    return im


def castle_turret():
    im, d = canvas(4, 5)                 # 128 x 160
    # ---- the battered stone base
    stonework(d, 2, 118, 125, 157, 2)
    px = im.load()
    for y in range(118, 158):
        inset = round(9 * (157 - y) / 39)
        for x in list(range(2, 2 + inset)) + list(range(126 - inset, 126)):
            px[x, y] = CLEAR
        px[2 + inset, y] = WHITE
        for x in range(120 - inset, 126 - inset):
            if px[x, y][3]:
                r, g, b, a = px[x, y]
                px[x, y] = (r - 34, g - 34, b - 28, a)
    d.rectangle([2, 158, 125, 159], fill=STONE_LO)
    # ---- the first storey
    d.rectangle([13, 82, 114, 117], fill=PLASTER)
    d.rectangle([106, 82, 114, 117], fill=PLASTER_LO)
    d.line([(13, 82), (114, 82)], fill=PLASTER_SH); d.line([(13, 83), (114, 83)], fill=PLASTER_LO)
    barred(d, 20, 88, 39, 96); barred(d, 88, 88, 107, 96)
    namako(d, 13, 102, 114, 112)
    d.rectangle([12, 114, 115, 117], fill=WOOD_DK); d.line([(12, 114), (115, 114)], fill=WOOD_LO)
    # the bay window under its bowed lead hood
    d.rectangle([46, 88, 81, 112], fill=PLASTER)
    d.line([(46, 88), (46, 112)], fill=WHITE); d.rectangle([79, 88, 81, 112], fill=PLASTER_LO)
    barred(d, 51, 93, 76, 104)
    d.rectangle([46, 109, 81, 112], fill=PLASTER_SH)
    d.chord([42, 74, 85, 100], 180, 360, fill=LEAD_P[0])
    d.arc([42, 74, 85, 100], 180, 360, fill=LEAD_P[2])
    d.arc([43, 76, 84, 100], 180, 360, fill=LEAD_P[1])
    d.rectangle([42, 86, 85, 88], fill=LEAD_P[1]); d.line([(42, 88), (85, 88)], fill=LEAD_P[3])
    for x in range(48, 82, 6):
        d.line([(x, 80), (x, 85)], fill=LEAD_P[1])
    # ---- the lower roof
    roof(d, 66, 77, (20, 107), (2, 125), LEAD_P, ridge=False)
    d.chord([42, 74, 85, 100], 180, 360, fill=LEAD_P[0])          # the hood breaks through the eave
    d.arc([42, 74, 85, 100], 180, 360, fill=LEAD_P[2])
    d.arc([43, 76, 84, 102], 200, 340, fill=LEAD_P[1])
    for x in range(50, 80, 6):
        d.line([(x, 78), (x, 86)], fill=LEAD_P[1])
    d.rectangle([43, 87, 84, 88], fill=LEAD_P[3])
    # ---- the second storey
    d.rectangle([27, 44, 100, 65], fill=PLASTER)
    d.rectangle([93, 44, 100, 65], fill=PLASTER_LO)
    d.line([(27, 44), (100, 44)], fill=PLASTER_SH); d.line([(27, 45), (100, 45)], fill=PLASTER_LO)
    barred(d, 35, 50, 50, 58); barred(d, 56, 50, 71, 58); barred(d, 77, 50, 92, 58)
    d.rectangle([27, 62, 100, 65], fill=PLASTER_LO)
    # ---- the top roof: lead, a plastered gable in its front slope
    roof(d, 17, 39, (42, 85), (12, 115), LEAD_P)
    d.rectangle([16, 43, 111, 43], fill=LEAD_P[3])
    d.polygon([(64, 20), (48, 38), (80, 38)], fill=LEAD_P[1])
    d.polygon([(64, 24), (53, 38), (75, 38)], fill=PLASTER)
    d.line([(64, 20), (48, 38)], fill=LEAD_P[2]); d.line([(64, 20), (80, 38)], fill=LEAD_P[3])
    d.line([(64, 25), (54, 38)], fill=PLASTER_SH)
    d.rectangle([62, 31, 66, 36], fill=SOOT); d.line([(64, 31), (64, 36)], fill=PLASTER)
    outline(im)
    return im


def castle_storehouse():
    """A nagaya, the long storehouse of the castle terrace (the Gojikken
    Nagaya's kind): one low storey the length of a wall, in the castle's own
    plaster, namako and lead."""
    im, d = canvas(6, 3)                 # 192 x 96; the door is column 2 (x 64-95)
    stonework(d, 2, 78, 189, 95, 5)
    d.rectangle([4, 40, 187, 77], fill=PLASTER)
    d.rectangle([180, 40, 187, 77], fill=PLASTER_LO)
    d.line([(4, 40), (187, 40)], fill=PLASTER_SH); d.line([(4, 41), (187, 41)], fill=PLASTER_LO)
    for x0 in (12, 38, 106, 132, 158):
        barred(d, x0, 46, x0 + 19, 54)
    namako(d, 4, 60, 187, 70)
    d.rectangle([3, 74, 188, 77], fill=WOOD_DK); d.line([(3, 74), (188, 74)], fill=WOOD_LO)
    # ---- the door: iron-bound leaves under a little lead hood
    d.rectangle([65, 52, 94, 95], fill=WOOD_DK)
    d.rectangle([67, 55, 92, 95], fill=WOOD_LO)
    d.line([(67, 55), (67, 95)], fill=WOOD); d.line([(79, 55), (79, 95)], fill=WOOD_DK)
    d.line([(80, 55), (80, 95)], fill=WOOD)
    for y in (61, 75, 88):
        d.rectangle([67, y, 92, y + 2], fill=LACQUER_LO)
        for x in (70, 76, 83, 89):
            d.point((x, y + 1), fill=STONE)
    d.rectangle([61, 45, 98, 51], fill=LEAD_P[0])
    d.line([(61, 45), (98, 45)], fill=LEAD_P[2]); d.rectangle([61, 50, 98, 51], fill=LEAD_P[3])
    for x in range(64, 98, 5):
        d.line([(x, 46), (x, 49)], fill=LEAD_P[1])
    # ---- the long lead roof
    roof(d, 14, 34, (16, 175), (0, 191), LEAD_P)
    d.rectangle([4, 38, 187, 39], fill=LEAD_P[3])
    outline(im)
    shade(im, [182, 78, 189, 95], (10, 22, 39, 60))
    return im


# ---- walls: the castle's white one and Nagamachi's ochre one, as one family each ----
def _castle_coping(d, x0, x1):
    light, dark, hi, deep = LEAD_P
    d.rectangle([x0, 12, x1, 14], fill=dark); d.line([(x0, 12), (x1, 12)], fill=hi)
    tiles(d, [(y, x0, x1) for y in range(15, 23)], light, dark, step=4)
    d.rectangle([x0, 23, x1, 24], fill=dark)
    for x in range(x0 + 1, x1 + 1, 4):
        d.point((x, 24), fill=hi)
    d.line([(x0, 25), (x1, 25)], fill=PLASTER_SH)


def _castle_face(d, x0, x1, seed=0):
    d.rectangle([x0, 26, x1, 35], fill=PLASTER)
    d.line([(x0, 26), (x1, 26)], fill=PLASTER_LO)
    namako(d, x0, 36, x1, 47)
    stonework(d, x0, 49, x1, 63, seed)


def _naga_coping(d, x0, x1):
    light, dark, hi, deep = SHINGLE_P
    d.rectangle([x0, 15, x1, 17], fill=dark); d.line([(x0, 15), (x1, 15)], fill=hi)
    for y in range(18, 24):
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=dark if (x + (y // 3) * 2) % 4 == 0 or y % 3 == 2 else light)
    d.line([(x0, 18), (x1, 18)], fill=hi)
    d.line([(x0, 24), (x1, 24)], fill=deep)
    d.line([(x0, 25), (x1, 25)], fill=OCHRE_DK)


def _naga_face(d, x0, x1, komo=True, seed=0, y0=26):
    d.rectangle([x0, y0, x1, 51], fill=OCHRE)
    d.line([(x0, y0), (x1, y0)], fill=OCHRE_LO)
    for y in range(y0, 52):
        for x in range(x0, x1 + 1):
            k = h3(x % 32, y, 3)
            if k < 14:
                d.point((x, y), fill=OCHRE_HI)                    # chopped straw in the earth
            elif k < 24:
                d.point((x, y), fill=OCHRE_LO)
    for y in (34, 43):
        if y > y0:
            d.line([(x0, y), (x1, y)], fill=OCHRE_LO)             # the lifts it was rammed in
    d.line([(x0, 51), (x1, 51)], fill=OCHRE_DK)
    cobbles(d, x0, 52, x1, 63, seed)
    if komo:
        komo_mats(d, x0, x1)


MAT, MAT_HI, MAT_LO = rgb('d5b56c'), rgb('e3c988'), rgb('b99752')


def komo_mats(d, x0, x1):
    """Komo-gake: straw matting tied over the wall for the winter. It is straw
    on earth, so it is close to the wall's own colour: what shows is the three
    ropes that bind it, the seam between two mats and the ragged fringe at its
    foot, hanging from a pole under the cap."""
    d.line([(x0, 27), (x1, 27)], fill=WOOD_DK)                    # the pole
    for x in range(x0, x1 + 1):
        u = x % 32
        hem = 46 + (u * 5 + u // 3) % 3
        streak = (u * 7 + (u // 2) * 3) % 9
        for y in range(28, hem + 1):
            c = MAT_HI if streak == 0 else (MAT_LO if streak == 4 else MAT)
            if y in (31, 38, 44):
                c = ROPE if (u + y) % 4 else STRAW_LO             # a twisted rope
            elif y in (32, 39, 45):
                c = MAT_LO
            if u == 31:
                c = OCHRE_DK                                      # where two mats meet
            elif u == 0:
                c = MAT_HI
            d.point((x, y), fill=c)
        if u % 2 == 0 and u != 0:                                 # the fringe: loose straw ends
            d.line([(x, hem + 1), (x, hem + 2 + (u % 3 == 0))], fill=MAT)
        else:
            d.point((x, hem + 1), fill=OCHRE_LO)
        if u in (8, 23):                                          # the ties to the pole
            d.line([(x, 27), (x, 30)], fill=ROPE)


def _fall(d, pal, x0, x1, y0, y1, lit, clip=None):
    """One fall of a north-south coping: courses run with the ridge (down the
    map), the tiles' joints across them. Period 8 in y, so pieces stack."""
    light, dark, hi, deep = pal
    a, b = (light, dark) if lit else (dark, deep)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if clip and not clip(x, y):
                continue
            u = x - x0
            joint = u % 4 == 3 or (y + (u // 4) % 2 * 4) % 8 == 0
            d.point((x, y), fill=b if joint else a)


def _v_coping(d, pal, y0, y1):
    """The coping of a wall running north-south, seen from above: the lit west
    fall, the ridge, the east fall in shade (x 2-29)."""
    light, dark, hi, deep = pal
    _fall(d, pal, 3, 14, y0, y1, True)
    _fall(d, pal, 17, 28, y0, y1, False)
    d.line([(2, y0), (2, y1)], fill=hi)
    d.line([(29, y0), (29, y1)], fill=deep)
    d.line([(15, y0), (15, y1)], fill=hi)
    d.line([(16, y0), (16, y1)], fill=dark)


def wall(style, kind):
    """One piece of a wall family, 1x2 cells. `h` runs east-west: coping over
    the face. `v` is the wall running north-south: its top cell is the coping
    seen from above (both falls and the ridge, 28px wide), its bottom cell the
    wall's south end (plaster, namako and stone; or earth between posts on
    river stones). Stacked down the map each piece's coping covers the end of
    the one north of it, so a run is one roof with a wall face and foot under
    its last piece. `end` is the same with the coping hipped, to finish a run.
    `corner-e` / `corner-w` are the ends of an east-west run where the wall
    turns north: the face stops at corner stones (a post), the coping turns up
    the map over a hip, and `v` goes in the cells above. Each corner is drawn
    for its own side: light comes from the west."""
    castle = style == 'castle'
    coping = _castle_coping if castle else _naga_coping
    pal = LEAD_P if castle else SHINGLE_P
    light, dark, hi, deep = pal
    top = 12 if castle else 15

    def face(d, x0, x1):
        if castle:
            _castle_face(d, x0, x1)
        else:
            _naga_face(d, x0, x1, komo=(style == 'komo'))

    def end_face(d):                                             # the south end of a north-south wall
        if castle:
            d.rectangle([5, 32, 26, 39], fill=PLASTER)
            d.rectangle([24, 32, 26, 39], fill=PLASTER_LO)
            d.line([(5, 32), (26, 32)], fill=PLASTER_SH)
            d.line([(5, 33), (26, 33)], fill=PLASTER_LO)
            namako(d, 5, 40, 26, 49)
            stonework(d, 5, 51, 26, 63, 3)
            d.line([(5, 51), (5, 63)], fill=WHITE)
            d.line([(26, 51), (26, 63)], fill=STONE_LO)
        else:
            _naga_face(d, 5, 26, komo=False, y0=32)
            d.line([(5, 32), (26, 32)], fill=OCHRE_DK)
            d.line([(5, 33), (26, 33)], fill=OCHRE_LO)
            d.rectangle([5, 32, 7, 51], fill=WOOD)
            d.line([(5, 32), (5, 51)], fill=rgb('d2a58c')); d.line([(7, 32), (7, 51)], fill=WOOD_LO)
            d.rectangle([24, 32, 26, 51], fill=WOOD_LO)
            d.line([(26, 32), (26, 51)], fill=WOOD_DK)

    im, d = canvas(1, 2)
    if kind == 'h':
        coping(d, 0, 31); face(d, 0, 31)
    elif kind == 'v':
        _v_coping(d, pal, 0, 31)
        end_face(d)
    elif kind == 'end':
        _v_coping(d, pal, 0, 31)
        for y in range(18, 30):                                  # the coping's hipped south end
            t = y - 18
            xa, xb = 15 - t, 16 + t
            for x in range(max(3, xa), min(28, xb) + 1):
                joint = y % 4 == 1 or (x + (y // 4) % 2 * 3) % 6 == 0
                d.point((x, y), fill=dark if joint else light)
            if xa >= 3:
                d.point((xa, y), fill=hi); d.point((xb, y), fill=deep)
        d.rectangle([2, 30, 29, 31], fill=dark)
        for x in range(3, 29, 4):
            d.point((x, 31), fill=hi)
        end_face(d)
    elif kind in ('corner-e', 'corner-w'):
        east = kind == 'corner-e'
        fx0, fx1 = (0, 27) if east else (4, 31)
        coping(d, 0 if east else 2, 29 if east else 31)
        face(d, fx0, fx1)
        _v_coping(d, pal, 0, top - 1)                             # the coping turning north
        d.line([(15, top), (15, top + 2)], fill=hi)
        d.line([(16, top), (16, top + 2)], fill=dark)
        for y in range(top, 26):                                 # the hip between the two roofs
            reach = round((y - top) * 13 / (25 - top))
            if east:
                _fall(d, pal, 17, 28, y, y, False, clip=lambda x, yy, r=reach: x > 16 + r)
                d.point((29, y), fill=deep)
                if reach:
                    d.point((16 + reach, y), fill=hi)
            else:
                _fall(d, pal, 3, 14, y, y, True, clip=lambda x, yy, r=reach: x < 15 - r)
                d.point((2, y), fill=hi)
                if reach:
                    d.point((15 - reach, y), fill=dark)
        if castle:                                               # the corner's long-and-short stones
            for i, y in enumerate(range(26, 62, 6)):
                w = 7 if i % 2 else 4
                xa, xb = (fx1 - w, fx1) if east else (fx0, fx0 + w)
                d.rectangle([xa, y, xb, y + 5], fill=STONES[(i * 2 + (0 if east else 3)) % 7])
                d.line([(xa, y), (xb, y)], fill=WHITE)
                d.line([(xa, y + 5), (xb, y + 5)], fill=STONE_LO)
                if east:
                    d.rectangle([xb - 1, y + 1, xb, y + 5], fill=STONE_LO)      # the corner, turned from the light
                else:
                    d.line([(xa, y), (xa, y + 5)], fill=WHITE)
            d.rectangle([fx0 if not east else fx1 - 6, 62, fx1 if east else fx0 + 6, 63], fill=STONE_LO)
        elif east:                                               # a corner post, in shade
            d.rectangle([fx1 - 3, 26, fx1, 51], fill=WOOD_LO)
            d.line([(fx1 - 3, 26), (fx1 - 3, 51)], fill=WOOD); d.line([(fx1, 26), (fx1, 51)], fill=WOOD_DK)
        else:                                                    # a corner post, lit
            d.rectangle([fx0, 26, fx0 + 3, 51], fill=WOOD)
            d.line([(fx0, 26), (fx0, 51)], fill=rgb('d2a58c')); d.line([(fx0 + 3, 26), (fx0 + 3, 51)], fill=WOOD_LO)
    elif kind == 'gate':
        roof(d, 8, 15, (2, 29), (0, 31), SHINGLE_P, ridge=False, step=3)
        d.rectangle([0, 3, 31, 7], fill=dark); d.line([(0, 3), (31, 3)], fill=hi)
        d.rectangle([0, 19, 31, 23], fill=WOOD_LO)
        d.line([(0, 19), (31, 19)], fill=WOOD); d.line([(0, 23), (31, 23)], fill=WOOD_DK)
        for x0 in (0, 27):
            d.rectangle([x0, 24, x0 + 4, 63], fill=WOOD_LO)
            d.line([(x0, 24), (x0, 63)], fill=WOOD); d.line([(x0 + 4, 24), (x0 + 4, 63)], fill=WOOD_DK)
            d.rectangle([x0, 59, x0 + 4, 63], fill=STONE_LO); d.line([(x0, 59), (x0 + 4, 59)], fill=STONE)
        d.rectangle([5, 24, 8, 62], fill=WOOD_DK)                 # the leaf, folded back
        d.line([(6, 26), (6, 61)], fill=WOOD_LO); d.point((7, 44), fill=GOLD)
    outline(im)
    return im


# ==============================================================================
# Kenrokuen
# ==============================================================================
def kotoji(water=False):
    im, d = canvas(2, 3)                 # 64 x 96
    # ---- what it stands on: a low stone in the shallows (or, `water`, the pond itself), a rock on the bank
    if not water:
        d.ellipse([3, 84, 26, 93], fill=GRAN_LO)
        d.ellipse([4, 84, 24, 90], fill=GRAN)
        d.line([(8, 85), (19, 85)], fill=GRAN_HI)
    rk, rk_hi, rk_lo = rgb('7f8388'), rgb('a4a8aa'), rgb('5a5e68')
    d.polygon([(34, 93), (36, 80), (41, 70), (47, 66), (54, 67), (60, 74), (63, 84), (63, 93)], fill=rk)
    d.polygon([(36, 80), (41, 70), (47, 66), (54, 67), (51, 71), (44, 73), (40, 82)], fill=rk_hi)
    d.polygon([(54, 67), (60, 74), (63, 84), (63, 93), (55, 93), (57, 80), (53, 72)], fill=rk_lo)
    d.line([(44, 78), (48, 86), (46, 92)], fill=rk_lo)
    d.line([(47, 66), (54, 67)], fill=GRAN_HI)
    for x in range(34, 64):                                       # moss up its foot and in its hollows
        for y in range(84, 94):
            if h3(x, y, 2) < 40 + (y - 84) * 16:
                d.point((x, y), fill=MOSS if h3(x, y, 5) < 150 else MOSS_HI)
    for x, y in ((42, 72), (45, 69), (50, 68), (38, 81), (58, 76)):
        d.point((x, y), fill=MOSS_HI); d.point((x + 1, y), fill=MOSS)
    if not water:
        d.ellipse([22, 87, 40, 94], fill=GRAN_LO); d.line([(26, 88), (36, 88)], fill=GRAN)
    # ---- the two legs: the long one in the water, the short one on the rock
    def leg(pts):
        d.line(pts, fill=GRAN, width=6)
        d.line([(x - 3, y) for x, y in pts], fill=GRAN_HI, width=1)
        d.line([(x + 2, y) for x, y in pts], fill=GRAN_LO, width=2)
    leg([(25, 46), (22, 58), (18, 71), (14, 88 if water else 86)])
    leg([(39, 46), (43, 54), (47, 61), (50, 67)])
    if not water:
        d.rectangle([10, 84, 18, 87], fill=GRAN); d.line([(10, 84), (18, 84)], fill=GRAN_HI)
    # ---- the platform, the light box, the roof, the jewel
    d.rectangle([18, 41, 46, 46], fill=GRAN)
    d.line([(18, 41), (46, 41)], fill=GRAN_HI); d.rectangle([18, 45, 46, 46], fill=GRAN_LO)
    d.rectangle([42, 42, 46, 46], fill=GRAN_LO)
    d.rectangle([21, 38, 43, 40], fill=GRAN_LO); d.line([(21, 38), (43, 38)], fill=GRAN)
    d.rectangle([24, 26, 40, 37], fill=GRAN)
    d.line([(24, 26), (24, 37)], fill=GRAN_HI); d.rectangle([37, 26, 40, 37], fill=GRAN_LO)
    d.rectangle([27, 28, 35, 36], fill=GRAN_DK)
    d.rectangle([28, 29, 34, 35], fill=PAPER)
    d.line([(31, 29), (31, 35)], fill=GRAN_DK); d.line([(28, 32), (34, 32)], fill=GRAN_DK)
    d.polygon([(32, 10), (22, 17), (11, 23), (9, 21), (9, 26), (55, 26), (55, 21), (53, 23), (42, 17)], fill=GRAN)
    d.polygon([(32, 10), (22, 17), (11, 23), (9, 21), (9, 24), (24, 21), (31, 14)], fill=GRAN_HI)
    d.polygon([(34, 12), (42, 17), (53, 23), (55, 21), (55, 26), (44, 26)], fill=GRAN_LO)
    d.rectangle([10, 25, 54, 26], fill=GRAN_DK)
    for x, y in ((18, 20), (26, 16), (38, 17), (46, 21), (30, 13)):       # lichen on the roof
        d.point((x, y), fill=MOSS_HI); d.point((x + 1, y + 1), fill=MOSS)
    d.rectangle([30, 7, 34, 10], fill=GRAN_LO)
    d.ellipse([28, 1, 36, 8], fill=GRAN); d.point((30, 3), fill=WHITE); d.point((31, 3), fill=GRAN_HI)
    d.arc([28, 1, 36, 8], -60, 100, fill=GRAN_LO)
    if not water:
        d.point((7, 91), fill=MAPLE); d.point((8, 91), fill=MAPLE_OR)    # a maple leaf on the stone
    outline(im)
    if water:                            # the long leg goes down into the pond: rings round it, its shadow
        ov = Image.new('RGBA', im.size, CLEAR)
        od = ImageDraw.Draw(ov)
        od.ellipse([1, 83, 27, 95], fill=(16, 28, 66, 90))
        od.arc([2, 84, 26, 94], 0, 360, fill=(142, 194, 250, 220))
        od.arc([6, 86, 22, 92], 200, 340, fill=(142, 194, 250, 160))
        od.line([(26, 93), (31, 93)], fill=(142, 194, 250, 200))
        px = im.load()
        for y in range(89, 96):          # the leg is cut at the waterline
            for x in range(0, 30):
                px[x, y] = CLEAR
        under = Image.new('RGBA', im.size, CLEAR)
        under.alpha_composite(ov)
        under.alpha_composite(im)
        return under
    return im


def yukitsuri(cw, ch, pads, n):
    def build():
        im, d = canvas(cw, ch)
        W, H = cw * 32, ch * 32
        cx = W // 2
        rim_y, rx, ry = H - 20, W // 2 - 3, 7 + cw
        apex = (cx, 5)
        ends = []
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            ends.append((a, round(cx + rx * math.cos(a)), round(rim_y + ry * math.sin(a))))
        d.ellipse([cx - rx + 6, H - 13, cx + rx - 6, H - 3], fill=MOSS_DK)          # its shadow on the moss
        for a, x, y in ends:                                      # the ropes round the back
            if math.sin(a) < 0:
                d.line([apex, (x, y)], fill=STRAW_LO)
        # the trunk and its boughs
        d.line([(cx - 3, H - 6), (cx - 5, H - 30), (cx + 2, H * 0.5), (cx + 6, H * 0.38)], fill=BARK, width=4)
        d.line([(cx - 5, H - 8), (cx - 7, H - 30), (cx, H * 0.5)], fill=rgb('9a7460'))
        d.line([(cx - 1, H - 6), (cx - 2, H - 28)], fill=BARK_LO)
        d.line([(cx - 5, H - 30), (cx - rx + 12, H - 40)], fill=BARK_LO, width=2)
        d.line([(cx, H - 34), (cx + rx - 12, H - 44)], fill=BARK_LO, width=2)
        d.rectangle([cx - 6, H - 8, cx + 1, H - 5], fill=BARK_LO)
        # the pole the ropes hang from
        d.line([(cx + 2, H - 6), (cx + 1, 6)], fill=rgb('b9a05e'), width=2)
        d.line([(cx + 3, H - 6), (cx + 2, 8)], fill=rgb('8a7440'))
        for y in range(18, H - 10, 14):
            d.line([(cx + 1, y), (cx + 3, y)], fill=rgb('8a7440'))
        for i, (ox, y, prx, pry) in enumerate(pads):              # the pads of needles, back to front
            blob(d, cx + ox, y, prx, pry, PINE, PINE_HI, PINE_LO, seed=i * 3 + cw)
            d.arc([cx + ox - prx, y - pry, cx + ox + prx, y + pry], 30, 150, fill=PINE_DK)
        for a, x, y in ends:                                      # the ropes in front
            if math.sin(a) >= 0:
                d.line([apex, (x, y)], fill=STRAW)
                d.point((x, y), fill=ROPE); d.point((x, y + 1), fill=ROPE)
        for a, x, y in ends:
            if math.sin(a) >= 0 and abs(math.cos(a)) < 0.75:
                mx, my = (apex[0] + x) // 2, (apex[1] + y) // 2
                d.point((mx, my), fill=STRAW_HI); d.point(((apex[0] * 3 + x) // 4, (apex[1] * 3 + y) // 4), fill=STRAW_HI)
        d.rectangle([cx - 2, 1, cx + 3, 7], fill=STRAW)           # the straw knot at the top
        d.line([(cx - 2, 1), (cx - 2, 7)], fill=STRAW_HI); d.line([(cx + 3, 2), (cx + 3, 7)], fill=STRAW_LO)
        d.line([(cx - 2, 5), (cx + 3, 5)], fill=ROPE)
        d.point((cx, 0), fill=STRAW_HI); d.point((cx + 1, 0), fill=STRAW)
        outline(im)
        return im
    return build


def teahouse():
    im, d = canvas(4, 3)                 # 128 x 96; it stands on posts in the bottom row
    # ---- the posts in the water
    for x in (14, 46, 79, 111):
        d.rectangle([x, 76, x + 3, 90], fill=WOOD_LO)
        d.line([(x, 76), (x, 90)], fill=WOOD); d.line([(x + 3, 76), (x + 3, 90)], fill=WOOD_DK)
        d.rectangle([x - 2, 89, x + 5, 93], fill=GRAN); d.line([(x - 2, 89), (x + 5, 89)], fill=GRAN_HI)
        d.line([(x - 2, 93), (x + 5, 93)], fill=GRAN_DK)
    for x in range(18, 110, 4):                                   # cross ties under the floor
        d.point((x, 79), fill=WOOD_DK)
    d.line([(18, 80), (110, 80)], fill=WOOD_DK)
    # ---- the veranda and its low rail
    d.rectangle([6, 69, 121, 73], fill=WOOD)
    d.line([(6, 69), (121, 69)], fill=rgb('d2a58c')); d.rectangle([6, 73, 121, 75], fill=WOOD_DK)
    for x in range(8, 120, 6):
        d.point((x, 71), fill=WOOD_LO)
    # ---- the room: paper screens either side, the middle slid open
    d.rectangle([12, 40, 115, 68], fill=WOOD_DK)
    d.rectangle([12, 40, 115, 44], fill=WOOD_LO); d.line([(12, 40), (115, 40)], fill=WOOD)
    for x0, x1 in ((15, 43), (84, 112)):
        d.rectangle([x0, 46, x1, 67], fill=PAPER)
        d.line([(x0, 46), (x1, 46)], fill=WHITE)
        d.rectangle([x1 - 5, 47, x1, 67], fill=PAPER_LO)
        for x in range(x0 + 7, x1, 7):
            d.line([(x, 46), (x, 67)], fill=WOOD)
        for y in (53, 60):
            d.line([(x0, y), (x1, y)], fill=WOOD)
    d.rectangle([47, 46, 80, 67], fill=SOOT)
    d.rectangle([47, 60, 80, 67], fill=rgb('b9a878'))             # tatami
    d.line([(47, 60), (80, 60)], fill=rgb('d6c79a')); d.line([(63, 60), (63, 67)], fill=rgb('8f8055'))
    d.rectangle([68, 47, 76, 58], fill=PAPER)                     # a hanging scroll
    d.rectangle([70, 49, 74, 56], fill=PAPER_LO); d.line([(72, 50), (72, 55)], fill=SOOT)
    d.rectangle([52, 55, 60, 59], fill=KIM)                       # a low table, a tea bowl, the kettle
    d.line([(52, 55), (60, 55)], fill=KIM_HI)
    d.rectangle([55, 52, 57, 54], fill=MOSS_HI); d.rectangle([49, 56, 51, 59], fill=SOOT_LO)
    d.rectangle([45, 45, 46, 68], fill=WOOD_LO); d.rectangle([81, 45, 82, 68], fill=WOOD_LO)
    for x in (12, 114):
        d.rectangle([x, 40, x + 1, 68], fill=WOOD_LO)
    d.line([(8, 62), (119, 62)], fill=WOOD_LO)                    # the rail
    for x in (8, 26, 44, 83, 101, 119):
        d.line([(x, 62), (x, 68)], fill=WOOD_LO)
    # ---- the shingled roof, moss in its valleys
    roof(d, 13, 35, (30, 97), (1, 126), SHINGLE_P, step=3)
    for x, y in ((20, 30), (34, 22), (58, 28), (86, 18), (100, 31), (70, 33), (44, 33)):
        d.point((x, y), fill=MOSS_HI); d.point((x + 1, y), fill=MOSS); d.point((x, y + 1), fill=MOSS)
    outline(im)
    ov = Image.new('RGBA', im.size, CLEAR)                        # the floor's shadow on the water, ripples
    od = ImageDraw.Draw(ov)
    for x in range(8, 120):
        if im.getpixel((x, 82))[3] == 0:
            od.line([(x, 77), (x, 85)], fill=(16, 28, 66, 130))
            od.point((x, 86 + (x % 3 == 0)), fill=(16, 28, 66, 70))
    for x0, x1, y in ((22, 34, 91), (56, 70, 93), (90, 100, 91), (36, 42, 94)):
        od.line([(x0, y), (x1, y)], fill=(142, 194, 250, 200))
    under = Image.new('RGBA', im.size, CLEAR)
    under.alpha_composite(ov)
    under.alpha_composite(im)
    return under


def stone_bridge():
    """The garden's arched stone bridge from straight above, as
    kanazawa-canal-bridge is drawn: kerbs along its two sides, the slabs of the
    deck between, lighter over the crown of the arch and darker where it comes
    down to the banks."""
    im, d = canvas(3, 1)                 # 96 x 32, flat: walked ON, east-west
    deck = (rgb('9da2a8'), GRAN, rgb('b9bec2'), rgb('c9cdd0'), rgb('d6dadc'))
    for x in range(96):
        t = math.sin(math.pi * (x + 0.5) / 96)                    # 0 at the banks, 1 at the crown
        lvl = t * 4
        for y in range(32):
            if y <= 4 or y >= 27:                                 # the kerbs
                v = y if y <= 4 else y - 27
                joint = (x + (0 if y <= 4 else 6)) % 12 == 0
                c = (GRAN_DK, WHITE, rgb('c2c6ca'), GRAN, GRAN_DK)[v]
                if joint and v in (1, 2, 3):
                    c = GRAN_LO
            else:
                i = int(lvl)
                if lvl - i > 0.5 and (x + y) % 2 == 0:
                    i += 1                                        # dithered, so the swell is smooth
                c = deck[min(4, i)]
                if x % 16 == 7:
                    c = GRAN_LO                                   # the joints between slabs
                elif x % 16 == 8:
                    c = GRAN_HI
                elif y == 15 and (x // 16) % 2 == 0:
                    c = GRAN_LO
                elif h3(x, y, 5) < 7:
                    c = GRAN_LO
                if y == 5:
                    c = GRAN_LO                                   # the far kerb's shadow on the deck
            d.point((x, y), fill=c)
    for x0 in (0, 91):                                            # a post at each corner
        for y0 in (0, 26):
            d.rectangle([x0, y0, x0 + 4, y0 + 5], fill=GRAN)
            d.rectangle([x0, y0, x0 + 4, y0], fill=WHITE); d.line([(x0, y0), (x0, y0 + 5)], fill=WHITE)
            d.line([(x0 + 4, y0 + 1), (x0 + 4, y0 + 5)], fill=GRAN_DK)
            d.line([(x0, y0 + 5), (x0 + 4, y0 + 5)], fill=GRAN_DK)
    return im


MOSS_B, MOSS_M, MOSS_H, MOSS_S = rgb('3a6c58'), rgb('457b5e'), rgb('5f9668'), rgb('30604f')
MOUNDS = ((6, 5, 5, 3), (20, 3, 6, 3), (13, 12, 6, 4), (28, 14, 5, 3),          # cx, cy, rx, ry
          (4, 20, 5, 3), (21, 22, 7, 4), (11, 28, 5, 3), (30, 28, 4, 3))


def moss_px(x, y):
    """Kenrokuen's moss at drawn pixel (x, y) of a 32px tile: a deep blue-green
    floor heaped into cushions, each lit from the upper left and dark under its
    lower right edge. Periodic at 32 both ways."""
    for cx, cy, rx, ry in MOUNDS:
        dx = (x - cx + 16) % 32 - 16
        dy = (y - cy + 16) % 32 - 16
        q = (dx / rx) ** 2 + (dy / ry) ** 2
        if q <= 1.0:
            s = dx / rx + dy / ry
            if s > 0.75:
                return MOSS_S
            if s < -0.55:
                return MOSS_H
            return MOSS_M
    return MOSS_S if h3(x % 32, y % 32, 2) < 10 else MOSS_B


def garden_moss():
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    for y in range(32):
        for x in range(32):
            px[x, y] = moss_px(x, y)
    return im


def _edge_dist(role, x, y, r=9):
    """How far inside the patch a pixel is, from the sides the role names
    (a rounded corner of radius r where two meet)."""
    tail = '' if role == 'center' else role.split('-')[-1]
    a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
    b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
    if a < r and b < r:
        return r - math.hypot(r - a, r - b)
    return min(a, b)


def garden_path(role):
    """Kenrokuen's paths: pale raked gravel between lines of edging stones,
    moss beyond them."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    grav = (rgb('ddd2ba'), rgb('cdc1a6'), rgb('ece4d0'), rgb('b9ad92'))
    for y in range(32):
        for x in range(32):
            dist = _edge_dist(role, x, y)
            if dist < 3.2:
                c = moss_px(x, y)
            elif dist < 6.2:                                      # an edging stone, low and pale
                c = (GRAN, GRAN_HI, rgb('b9bec2'))[(x // 5 + y // 5 * 3) % 3]
                if x % 5 == 4 and y % 5 == 4:
                    c = GRAN_LO
                elif dist < 3.9:
                    c = GRAN_LO                                   # its foot in the moss
                elif dist > 5.5:
                    c = grav[3]                                   # its shadow on the gravel
            else:
                k = h3(x, y, 7)
                c = grav[2] if k < 20 else (grav[1] if k < 60 else (grav[3] if k < 68 else grav[0]))
                if y % 6 == 2 and (x + y // 6 * 3) % 5 < 3 and dist > 8:
                    c = grav[1]                                   # the rake's lines
            px[x, y] = c
    return im


# ==============================================================================
# Higashi Chaya
# ==============================================================================
def chaya(v):
    def build():
        im, d = canvas(3, 4)             # 96 x 128; the door is column 1 (x 32-63)
        ry = {'a': 9, 'b': 13, 'c': 7}[v]                         # each house's ridge at its own height
        wall, wall_hi, wall_lo, wall_dk = {
            'a': (KIM, KIM_HI, KIM_LO, KIM_DK),
            'b': (rgb('5d3a32'), rgb('7a4f41'), rgb('46292a'), rgb('2f1d22')),
            'c': (rgb('8a4234'), rgb('aa5a44'), rgb('66302a'), rgb('43231f'))}[v]
        # ---- the main roof: black glazed tiles, eave to eave with its neighbours
        roof(d, ry + 5, 34, (2, 93), (0, 95), KAWARA_P, ridge=False, p=1.0)
        d.rectangle([0, ry, 95, ry + 4], fill=KAWARA_P[1])
        d.line([(0, ry), (95, ry)], fill=KAWARA_P[2]); d.line([(0, ry + 4), (95, ry + 4)], fill=KAWARA_P[3])
        for x in range(2, 95, 5):
            d.point((x, ry + 2), fill=KAWARA_P[0])
        for x0 in (0, 91):
            d.rectangle([x0, ry - 3, x0 + 4, ry + 4], fill=KAWARA_P[0])
            d.line([(x0, ry - 3), (x0, ry + 4)], fill=KAWARA_P[2])
        # ---- the upper floor: the tea rooms
        d.rectangle([1, 38, 94, 67], fill=wall)
        d.rectangle([1, 38, 94, 40], fill=wall_dk)
        d.rectangle([1, 38, 3, 67], fill=wall_hi); d.rectangle([92, 38, 94, 67], fill=wall_dk)
        if v == 'a':                                              # one long screen of kimusuko, two blinds
            kimusuko(d, 7, 44, 88, 60, bar=wall, gap=wall_dk)
            sudare(d, 9, 44, 30, 52); sudare(d, 65, 44, 86, 52)
        elif v == 'b':                                            # three lattice windows, the middle one lit
            for i, x0 in enumerate((7, 36, 65)):
                kimusuko(d, x0, 44, x0 + 23, 60, lit=(i == 1), bar=wall, gap=wall_dk)
                d.rectangle([x0 + 24, 43, x0 + 27, 61], fill=wall_lo)
            sudare(d, 65, 44, 88, 50)
        else:                                                     # the room open for the evening: lit paper
            for x0, x1 in ((13, 43), (52, 82)):                   # windows, a guest's shadow, shutter boxes
                d.rectangle([x0 - 1, 43, x1 + 1, 61], fill=wall_dk)
                d.rectangle([x0, 44, x1, 60], fill=LIT)
                d.line([(x0, 44), (x1, 44)], fill=WARM)
            d.ellipse([24, 49, 30, 55], fill=rgb('c99a58')); d.rectangle([22, 55, 32, 60], fill=rgb('c99a58'))
            d.ellipse([64, 50, 69, 55], fill=rgb('c99a58')); d.rectangle([62, 55, 71, 60], fill=rgb('c99a58'))
            for x0, x1 in ((13, 43), (52, 82)):
                for x in range(x0 + 5, x1, 5):
                    d.line([(x, 44), (x, 60)], fill=wall_dk)
                for y in (49, 55):
                    d.line([(x0, y), (x1, y)], fill=wall_dk)
            for x0, c in ((5, wall_lo), (85, wall_dk)):
                d.rectangle([x0, 42, x0 + 5, 62], fill=c)
                d.line([(x0 + 2, 43), (x0 + 2, 61)], fill=wall_dk if x0 == 5 else wall_lo)
        d.rectangle([4, 62, 91, 63], fill=wall_lo)                # the rail of the balcony
        d.rectangle([4, 64, 91, 67], fill=wall_dk)
        for x in range(6, 91, 4):
            d.point((x, 65), fill=wall_lo); d.point((x, 66), fill=wall_lo)
        # ---- the pent roof over the street
        roof(d, 69, 78, (1, 94), (0, 95), KAWARA_P, ridge=False, p=1.0)
        # ---- the ground floor
        d.rectangle([1, 82, 94, 123], fill=wall_lo)
        d.rectangle([1, 82, 94, 84], fill=wall_dk)
        d.rectangle([1, 82, 3, 123], fill=wall); d.rectangle([92, 82, 94, 123], fill=wall_dk)
        for x0, x1 in ((6, 28), (67, 89)):                        # the lattice bays
            if v == 'c' and x0 == 67:
                continue
            kimusuko(d, x0, 89, x1, 113, bar=wall, gap=wall_dk)
            d.rectangle([x0 - 1, 115, x1 + 1, 117], fill=wall)
            d.line([(x0 - 1, 115), (x1 + 1, 115)], fill=wall_hi)
            d.rectangle([x0, 118, x1, 123], fill=wall_dk)
            for x in range(x0 + 1, x1, 3):
                d.line([(x, 119), (x, 123)], fill=wall_lo)
        d.rectangle([33, 86, 62, 123], fill=SOOT_LO)              # the entrance
        d.rectangle([31, 85, 32, 123], fill=wall_dk); d.rectangle([63, 85, 64, 123], fill=wall_dk)
        if v == 'a':
            sliding_doors(d, 34, 100, 61, 123, lit=False, frame=wall_dk)
            noren(d, 34, 88, 61, 102, INDIGO, INDIGO_HI, WHITE)
            paper_lantern(d, 65, 90)
        elif v == 'b':
            sliding_doors(d, 34, 99, 61, 120, lit=True, frame=wall_dk)
            noren(d, 34, 88, 61, 101, rgb('3f5a48'), rgb('5f7d62'), PAPER)
            d.rectangle([32, 121, 63, 123], fill=GRAN)            # a stone step up to the door
            d.line([(32, 121), (63, 121)], fill=WHITE); d.line([(32, 123), (63, 123)], fill=GRAN_LO)
            d.rectangle([22, 86, 29, 87], fill=SOOT)              # a round red lantern on a bracket
            d.ellipse([21, 88, 30, 99], fill=RED); d.ellipse([22, 89, 26, 95], fill=RED_HI)
            d.arc([21, 88, 30, 99], -50, 90, fill=RED_DK)
            d.rectangle([24, 99, 27, 100], fill=SOOT)
            d.rectangle([66, 90, 71, 108], fill=rgb('cfae84'))    # the house's name board
            d.line([(66, 90), (66, 108)], fill=rgb('e8d2ae'))
            for y in (93, 98, 103):
                d.rectangle([68, y, 69, y + 2], fill=SOOT)
        else:
            sliding_doors(d, 34, 104, 61, 123, lit=True, frame=wall_dk)
            noren(d, 34, 88, 61, 108, KAKI, rgb('f0a060'), WHITE, slits=3)
            for x in range(69, 91, 4):                            # a boarded bay: a small lit window,
                d.line([(x, 86), (x, 123)], fill=wall_dk)         # a bench under a red cloth for tea outside
            d.rectangle([70, 89, 86, 101], fill=wall_dk)
            d.rectangle([71, 90, 85, 100], fill=LIT); d.line([(71, 90), (85, 90)], fill=WARM)
            d.line([(78, 90), (78, 100)], fill=wall_dk); d.line([(71, 95), (85, 95)], fill=wall_dk)
            d.rectangle([66, 109, 91, 112], fill=RED); d.line([(66, 109), (91, 109)], fill=RED_HI)
            d.rectangle([66, 113, 91, 115], fill=RED_DK)
            for x in (68, 88):
                d.rectangle([x, 116, x + 1, 123], fill=wall_dk)
            d.rectangle([75, 106, 78, 108], fill=PAPER); d.point((75, 106), fill=WHITE)      # a tea bowl, a plate
            d.rectangle([82, 107, 86, 108], fill=rgb('3f5a48'))
        d.rectangle([0, 124, 95, 127], fill=GRAN_LO)
        d.line([(0, 124), (95, 124)], fill=GRAN)
        for x in range(7, 95, 12):
            d.line([(x, 125), (x, 127)], fill=GRAN_DK)
        outline(im)
        return im
    return build


def gold_cone(d, cx, y):
    """A soft-serve cone wrapped in a sheet of gold leaf."""
    d.polygon([(cx - 4, y + 13), (cx + 4, y + 13), (cx, y + 23)], fill=rgb('c98f52'))
    d.line([(cx - 4, y + 13), (cx, y + 23)], fill=rgb('e6b47a'))
    d.line([(cx - 2, y + 15), (cx + 2, y + 19)], fill=rgb('9a6a3c')); d.line([(cx + 2, y + 15), (cx - 1, y + 19)], fill=rgb('9a6a3c'))
    for i, (w, yy) in enumerate(((5, 10), (4, 7), (3, 4), (2, 1))):
        d.ellipse([cx - w, y + yy, cx + w, y + yy + 4], fill=LEAF)
        d.line([(cx - w + 1, y + yy + 1), (cx - 1, y + yy + 1)], fill=LEAF_HI)
        d.line([(cx, y + yy + 4), (cx + w - 1, y + yy + 3)], fill=LEAF_LO)
    d.point((cx, y), fill=LEAF_HI)
    sparkle(d, cx - 3, y + 3); sparkle(d, cx + 4, y + 9)


def gold_shop():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1 (x 32-63)
    roof(d, 11, 34, (8, 119), (0, 127), KAWARA_P, p=1.2)
    # ---- the upper wall: a storehouse front laid with squares of gold leaf
    d.rectangle([2, 38, 125, 67], fill=LEAF_LO)
    for y in range(40, 66):
        for x in range(4, 124):
            gx, gy = (x - 4) % 8, (y - 40) % 8
            k = (((x - 4) // 8) * 5 + ((y - 40) // 8) * 7) % 6
            if gx == 7 or gy == 7:
                c = LEAF_LO
            elif gx == 0 or gy == 0:
                c = LEAF_HI
            else:
                c = (LEAF, LEAF, rgb('f6da6c'), LEAF, rgb('e2b944'), LEAF)[k]
            d.point((x, y), fill=c)
    d.rectangle([116, 40, 123, 65], fill=LEAF_LO)
    for x in range(116, 124):
        for y in range(40, 66):
            if (x - 4) % 8 == 0 or (y - 40) % 8 == 0:
                d.point((x, y), fill=LEAF)
    d.rectangle([2, 38, 125, 39], fill=LEAF_DK); d.rectangle([2, 66, 125, 67], fill=LEAF_DK)
    for x, y in ((14, 46), (38, 58), (97, 44), (110, 60), (26, 62), (84, 61)):
        sparkle(d, x, y)
    d.rectangle([42, 42, 85, 60], fill=LEAF_DK)                   # the shop's board: HAKU, leaf
    d.rectangle([44, 44, 83, 58], fill=LACQUER)
    d.line([(44, 44), (83, 44)], fill=LACQUER_HI)
    text(d, 'HAKU', 64 - text_w('HAKU') // 2, 48, LEAF)
    d.point((47, 51), fill=LEAF_HI); d.point((80, 51), fill=LEAF_HI)
    # ---- the pent roof
    roof(d, 69, 78, (3, 124), (0, 127), KAWARA_P, ridge=False, p=1.0)
    # ---- the ground floor: black lacquer, gold trim, the goods lit
    d.rectangle([2, 82, 125, 123], fill=LACQUER)
    d.rectangle([2, 82, 4, 123], fill=LACQUER_HI); d.rectangle([120, 82, 125, 123], fill=LACQUER_LO)
    d.line([(2, 84), (125, 84)], fill=LEAF_LO)
    d.rectangle([7, 89, 28, 118], fill=LEAF_DK)                   # a gilded screen in the left window
    d.rectangle([8, 90, 27, 117], fill=LEAF)
    for x in (14, 21):
        d.line([(x, 90), (x, 117)], fill=LEAF_LO)
    d.line([(8, 90), (27, 90)], fill=LEAF_HI)
    d.line([(10, 112), (13, 100), (17, 106), (20, 96), (25, 104)], fill=LEAF_DK)       # a pine branch on it
    for x, y in ((13, 100), (20, 96), (25, 104)):
        d.rectangle([x - 1, y - 2, x + 1, y - 1], fill=PINE)
    sparkle(d, 24, 93)
    sliding_doors(d, 34, 102, 61, 123, lit=True, frame=LACQUER_LO)
    noren(d, 34, 87, 61, 104, PAPER, WHITE, None)
    d.rectangle([45, 92, 51, 98], fill=LEAF); d.line([(45, 92), (51, 92)], fill=LEAF_HI)   # one square of leaf
    d.line([(45, 98), (51, 98)], fill=LEAF_LO)
    d.rectangle([67, 89, 100, 118], fill=LEAF_DK)                 # the lit window: gilded bowls, boxes
    d.rectangle([68, 90, 99, 117], fill=WARM)
    d.line([(68, 90), (99, 90)], fill=WHITE)
    for y in (102, 116):
        d.line([(68, y), (99, y)], fill=rgb('8f7440'))
    for i, x in enumerate((70, 78, 86, 93)):
        d.rectangle([x, 96 + i % 2, x + 4, 101], fill=(LEAF, RED_DK, LEAF, LACQUER)[i])
        d.point((x + 1, 97 + i % 2), fill=LEAF_HI)
        d.ellipse([x - 1, 110, x + 5, 115], fill=(LACQUER, LEAF, RED_DK, LEAF)[i])
        d.line([(x, 111), (x + 3, 111)], fill=LEAF_HI)
    d.line([(83, 90), (83, 117)], fill=LEAF_DK)
    d.rectangle([105, 86, 122, 116], fill=LEAF_DK)                # the sign: gold-leaf soft serve
    d.rectangle([106, 87, 121, 115], fill=rgb('34304a'))
    d.line([(106, 87), (121, 87)], fill=rgb('55506e'))
    gold_cone(d, 113, 89)
    d.rectangle([112, 117, 115, 123], fill=LACQUER_LO)
    d.rectangle([0, 124, 127, 127], fill=GRAN_LO); d.line([(0, 124), (127, 124)], fill=GRAN)
    for x in range(9, 127, 12):
        d.line([(x, 125), (x, 127)], fill=GRAN_DK)
    outline(im)
    return im


SLABS = ((0, 0, 18, 13), (19, 0, 31, 8), (19, 9, 31, 20),        # x0, y0, x1, y1: one cell of flags,
         (0, 14, 9, 31), (10, 14, 18, 20), (10, 21, 31, 31))     # no two alike, no course lines
FLAGS = (rgb('a6a4aa'), rgb('aaa8ad'), rgb('a2a0a7'), rgb('a8a6ab'), rgb('acaaae'), rgb('a4a2a8'))


def chaya_stone(role):
    """The Chaya lane: big grey stone flags of uneven length, fitted close
    (thin joints, almost one colour), a gutter of small setts on the sides the
    role names."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    for i, (x0, y0, x1, y1) in enumerate(SLABS):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if x == x1 or y == y1:
                    c = rgb('908e98')                             # the joint
                elif y == y0 and (x + i) % 9 < 6:
                    c = rgb('b3b1b5')                             # a worn arris
                elif h3(x, y, 11) < 6:
                    c = rgb('9c9aa2')
                elif h3(x, y, 23) < 4:
                    c = rgb('b1afb3')
                else:
                    c = FLAGS[i]
                px[x, y] = c
    tail = '' if role == 'center' else role.split('-')[-1]
    for y in range(32):
        for x in range(32):
            a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
            b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
            m = min(a, b)
            if m > 3:
                continue
            along = x if a <= b else y
            if m == 3:
                c = rgb('7a7886')                                 # the gutter's shadow line
            elif m == 0:
                c = rgb('858290')
            else:
                c = rgb('7f7c8a') if along % 4 == 3 else (rgb('8f8c97') if (along // 4) % 2 else rgb('9a97a0'))
            px[x, y] = c
    return im


def temple_stair():
    im, d = canvas(2, 3)                 # 64 x 96, flat: eight treads; tiles north-south
    for y in range(96):
        t, yy = y // 12, y % 12
        for x in range(64):
            if x < 7 or x > 56:                                   # the cheek walls, mossed
                u = x if x < 7 else x - 57
                c = GRAN_LO if (y + (0 if x < 7 else 5)) % 10 else GRAN_DK
                if u == 0:
                    c = GRAN_DK if x < 7 else GRAN
                if u == 6:
                    c = GRAN if x < 7 else GRAN_DK
                if u in (1, 2, 3) and h3(x, y, 4) < 120:
                    c = MOSS if h3(x, y, 9) < 170 else MOSS_HI
                d.point((x, y), fill=c)
                continue
            joint = (x - 7 + t * 9) % 17 == 0
            if yy == 0:
                c = WHITE
            elif yy <= 6:
                c = GRAN_LO if joint else (GRAN_HI if yy == 1 else rgb('bcc0c4'))
                if h3(x, y, 6) < 10:
                    c = GRAN
            elif yy == 7:
                c = GRAN
            elif yy < 11:
                c = GRAN_DK if joint else GRAN_LO
            else:
                c = GRAN_DK
            if x in (7, 8) and yy in (5, 6, 7) or x in (55, 56) and yy in (6, 7):
                c = MOSS                                          # moss in the corners of the treads
            d.point((x, y), fill=c)
    for x, y, c in ((18, 5, MAPLE), (40, 30, GINKGO), (27, 52, MAPLE_OR), (46, 76, MAPLE), (14, 88, GINKGO)):
        d.rectangle([x, y, x + 1, y], fill=c)
    return im


MOSSY_P = (rgb('727c6c'), rgb('545e54'), rgb('98a488'), rgb('3a423c'))     # old shingles gone grey-green


def temple_gate():
    im, d = canvas(3, 3)                 # 96 x 96; you walk through column 1
    wd, wd_hi, wd_lo, wd_dk = rgb('8b7566'), rgb('ab947f'), rgb('665549'), rgb('43383a')    # weathered cypress
    # ---- the board fences either side
    for x0, x1 in ((0, 20), (75, 95)):
        d.rectangle([x0, 60, x1, 90], fill=wd_lo)
        for x in range(x0, x1 + 1, 4):
            d.line([(x, 60), (x, 90)], fill=wd_dk)
            d.line([(x + 1, 61), (x + 1, 90)], fill=wd)
        d.rectangle([x0, 57, x1, 59], fill=wd_dk); d.line([(x0, 57), (x1, 57)], fill=wd)
        d.line([(x0, 74), (x1, 74)], fill=wd_dk)
        d.rectangle([x0, 91, x1, 95], fill=GRAN_LO); d.line([(x0, 91), (x1, 91)], fill=GRAN)
    # ---- posts, lintel, tie beam, the leaves folded back
    d.rectangle([16, 42, 79, 49], fill=wd)
    d.line([(16, 42), (79, 42)], fill=wd_hi); d.rectangle([16, 48, 79, 49], fill=wd_dk)
    d.rectangle([24, 54, 71, 56], fill=wd_lo)
    for x0 in (21, 68):
        d.rectangle([x0, 44, x0 + 6, 93], fill=wd)
        d.line([(x0, 44), (x0, 93)], fill=wd_hi); d.rectangle([x0 + 5, 44, x0 + 6, 93], fill=wd_lo)
        d.rectangle([x0 - 1, 90, x0 + 7, 95], fill=GRAN); d.line([(x0 - 1, 90), (x0 + 7, 90)], fill=GRAN_HI)
        d.rectangle([x0 - 1, 94, x0 + 7, 95], fill=GRAN_LO)
    for x0 in (28, 63):
        d.rectangle([x0, 57, x0 + 4, 92], fill=wd_dk)
        d.line([(x0 + 2, 59), (x0 + 2, 91)], fill=wd_lo)
        d.point((x0 + 3, 76), fill=GOLD)
    for x in (18, 32, 46, 60, 74):                                # bracket blocks under the eave
        d.rectangle([x, 39, x + 3, 41], fill=wd_lo)
    # ---- the shingled roof, moss where the rain sits
    roof(d, 16, 35, (16, 79), (0, 95), MOSSY_P, step=3)
    for x, y in ((12, 32), (26, 24), (40, 30), (56, 20), (70, 31), (84, 33), (48, 34), (22, 34),
                 (33, 27), (62, 26), (76, 28), (18, 29), (52, 31), (8, 34), (88, 34)):
        d.point((x, y), fill=MOSS_HI); d.point((x + 1, y), fill=MOSS); d.point((x + 1, y + 1), fill=MOSS)
    # ---- the temple's name board, a paper lantern on the post
    d.rectangle([39, 43, 56, 53], fill=wd_dk)
    d.rectangle([40, 44, 55, 52], fill=rgb('2f3d3a'))
    for x in (43, 48, 52):
        d.rectangle([x, 46, x + 1, 50], fill=GOLD)
    paper_lantern(d, 77, 50, mark=SOOT)
    outline(im)
    return im


IBUSHI_P = (rgb('6c7482'), rgb('4e5564'), rgb('98a0ac'), rgb('363b48'))     # smoked silver-grey temple tiles
CYPRESS = (rgb('8b7566'), rgb('ab947f'), rgb('665549'), rgb('43383a'))      # weathered cypress: mid, lit, shade, deep


def temple_hall():
    """A Teramachi temple's main hall: a great hipped roof of smoked tiles with
    a gabled porch over the steps, weathered timber and paper, the doors open on
    the altar's gold, an offertory box at the head of the stone steps."""
    im, d = canvas(5, 4)                 # 160 x 128; the door is column 2 (x 64-95)
    wd, wd_hi, wd_lo, wd_dk = CYPRESS
    # ---- the hall
    d.rectangle([10, 56, 149, 111], fill=wd_lo)
    d.rectangle([10, 56, 149, 63], fill=wd_dk)
    for x in range(14, 148, 8):                                   # bracket blocks under the eave
        d.rectangle([x, 59, x + 3, 62], fill=wd); d.line([(x, 59), (x + 3, 59)], fill=wd_hi)
    d.rectangle([12, 65, 147, 71], fill=PLASTER)
    d.rectangle([140, 65, 147, 71], fill=PLASTER_LO); d.line([(12, 71), (147, 71)], fill=PLASTER_SH)
    for x0, x1 in ((12, 33), (36, 57), (102, 123), (126, 147)):   # paper behind lattice
        d.rectangle([x0 + 1, 75, x1 - 1, 103], fill=PAPER)
        d.line([(x0 + 1, 75), (x1 - 1, 75)], fill=WHITE)
        d.rectangle([x1 - 5, 76, x1 - 1, 103], fill=PAPER_LO)
        for x in range(x0 + 4, x1 - 1, 4):
            d.line([(x, 75), (x, 103)], fill=wd_dk)
        for y in range(80, 103, 5):
            d.line([(x0 + 1, y), (x1 - 1, y)], fill=wd_dk)
        d.rectangle([x0 + 1, 104, x1 - 1, 107], fill=wd_dk)
    d.rectangle([142, 72, 149, 111], fill=wd_dk)
    # ---- the open doors: the dark hall, the five-coloured curtain, the altar
    d.rectangle([60, 72, 99, 111], fill=SOOT_LO)
    d.rectangle([62, 74, 97, 111], fill=rgb('2a2228'))
    d.rectangle([71, 85, 88, 101], fill=LEAF_DK)
    d.rectangle([73, 87, 86, 99], fill=LEAF_LO)
    d.ellipse([76, 88, 83, 96], fill=LEAF); d.point((78, 90), fill=LEAF_HI); d.point((79, 90), fill=LEAF_HI)
    d.rectangle([77, 96, 82, 98], fill=LEAF)
    for x in (67, 92):                                            # a candle either side
        d.line([(x, 95), (x, 101)], fill=PAPER); d.point((x, 93), fill=WARM); d.point((x, 94), fill=AMBER)
    for i, c in enumerate((rgb('6a4a8a'), PAPER, RED, LEAF, rgb('4f8a5a'))):
        d.rectangle([62 + i * 7, 74, 68 + i * 7, 79], fill=c)
    d.rectangle([97, 74, 97, 79], fill=rgb('6a4a8a'))
    d.line([(62, 80), (97, 80)], fill=SOOT_LO)
    for x0 in (62, 93):                                           # the leaves folded back
        d.rectangle([x0, 81, x0 + 4, 111], fill=wd_dk); d.line([(x0 + 2, 83), (x0 + 2, 110)], fill=wd_lo)
    for x in (10, 34, 58, 100, 124, 148):                         # the posts
        d.rectangle([x, 60, x + 1, 111], fill=wd); d.line([(x, 60), (x, 111)], fill=wd_hi)
    # ---- the veranda, its rail, the stone it stands on
    d.line([(4, 99), (58, 99)], fill=wd); d.line([(101, 99), (155, 99)], fill=wd)
    for x in list(range(4, 59, 9)) + list(range(101, 156, 9)):
        d.line([(x, 99), (x, 107)], fill=wd)
    d.rectangle([4, 108, 155, 112], fill=wd); d.line([(4, 108), (155, 108)], fill=wd_hi)
    d.rectangle([4, 113, 155, 115], fill=wd_dk)
    d.rectangle([6, 116, 153, 123], fill=GRAN_LO)
    for x in (8, 32, 56, 98, 122, 146):
        d.rectangle([x, 116, x + 5, 123], fill=GRAN); d.line([(x, 116), (x + 5, 116)], fill=GRAN_HI)
    d.rectangle([4, 124, 155, 127], fill=GRAN); d.line([(4, 124), (155, 124)], fill=GRAN_HI)
    d.line([(4, 127), (155, 127)], fill=GRAN_DK)
    for i, y in enumerate((110, 116, 122)):                       # the steps
        w = 2 * i
        d.rectangle([60 - w, y, 99 + w, y + 5], fill=rgb('c2c6ca'))
        d.line([(60 - w, y), (99 + w, y)], fill=WHITE); d.rectangle([60 - w, y + 4, 99 + w, y + 5], fill=GRAN_LO)
    d.rectangle([69, 101, 90, 110], fill=wd)                      # the offertory box
    d.line([(69, 101), (90, 101)], fill=wd_hi)
    for x in range(71, 90, 3):
        d.line([(x, 102), (x, 105)], fill=SOOT_LO)
    d.rectangle([69, 107, 90, 110], fill=wd_lo)
    # ---- the roof, the porch's gable breaking its eave
    roof(d, 14, 51, (40, 119), (0, 159), IBUSHI_P, p=1.6)
    d.polygon([(79, 36), (80, 36), (108, 56), (51, 56)], fill=IBUSHI_P[1])
    d.line([(79, 36), (51, 56)], fill=IBUSHI_P[2]); d.line([(79, 37), (53, 56)], fill=IBUSHI_P[0])
    d.line([(80, 36), (108, 56)], fill=IBUSHI_P[3])
    d.polygon([(79, 42), (80, 42), (98, 56), (61, 56)], fill=PLASTER)
    d.line([(79, 43), (63, 56)], fill=PLASTER_SH)
    d.line([(79, 44), (79, 56)], fill=wd_lo); d.line([(80, 44), (80, 56)], fill=wd_dk)
    d.line([(68, 51), (91, 51)], fill=wd_lo)
    d.rectangle([49, 57, 110, 59], fill=IBUSHI_P[1]); d.line([(49, 59), (110, 59)], fill=IBUSHI_P[3])
    for x in range(51, 110, 4):
        d.point((x, 58), fill=IBUSHI_P[2])
    for x0 in (55, 102):                                          # the porch's posts
        d.rectangle([x0, 60, x0 + 2, 109], fill=wd)
        d.line([(x0, 60), (x0, 109)], fill=wd_hi); d.line([(x0 + 2, 60), (x0 + 2, 109)], fill=wd_lo)
    for x, y in ((14, 46), (30, 34), (48, 44), (112, 30), (128, 44), (144, 48), (96, 24), (60, 22)):
        d.point((x, y), fill=MOSS_HI); d.point((x + 1, y), fill=MOSS)
    outline(im)
    return im


def gramophone(d, cx, cy):
    """A horn gramophone: brass horn, black disc, wooden box."""
    d.rectangle([cx - 7, cy + 5, cx + 5, cy + 11], fill=WOOD)
    d.line([(cx - 7, cy + 5), (cx + 5, cy + 5)], fill=rgb('d2a58c')); d.rectangle([cx + 3, cy + 6, cx + 5, cy + 11], fill=WOOD_LO)
    d.ellipse([cx - 7, cy + 2, cx + 5, cy + 6], fill=SOOT)
    d.point((cx - 1, cy + 4), fill=RED)
    d.line([(cx + 6, cy + 8), (cx + 8, cy + 8)], fill=LEAF_LO)                  # the crank
    d.polygon([(cx - 2, cy + 3), (cx - 1, cy - 3), (cx + 2, cy - 10), (cx + 11, cy - 7), (cx + 7, cy - 1), (cx + 1, cy + 3)],
              fill=LEAF)
    d.line([(cx - 2, cy + 3), (cx - 1, cy - 3), (cx + 2, cy - 10)], fill=LEAF_HI)
    d.ellipse([cx + 2, cy - 12, cx + 12, cy - 4], fill=LEAF_LO)
    d.ellipse([cx + 4, cy - 10, cx + 10, cy - 6], fill=LEAF_DK)
    d.arc([cx + 2, cy - 12, cx + 12, cy - 4], 150, 300, fill=LEAF_HI)


def phono_museum():
    """The phonograph museum by the teahouse quarter: a plain grey stone front
    under a great horn gramophone in a roundel."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is column 1 (x 32-63)
    st, st_hi, st_lo = rgb('b7bcc0'), rgb('d6dadc'), rgb('8f949c')
    d.rectangle([2, 8, 93, 14], fill=STONE_DK)                    # the cornice
    d.line([(2, 8), (93, 8)], fill=STONE_LO); d.line([(2, 14), (93, 14)], fill=INK)
    d.rectangle([4, 15, 91, 123], fill=st)
    d.rectangle([85, 15, 91, 123], fill=st_lo)
    d.line([(4, 15), (4, 123)], fill=st_hi)
    for y in range(26, 84, 12):                                   # the stone's courses
        d.line([(5, y), (84, y)], fill=st_lo); d.line([(5, y + 1), (84, y + 1)], fill=st_hi)
    # ---- the roundel
    d.ellipse([26, 18, 69, 61], fill=LEAF_DK)
    d.ellipse([28, 20, 67, 59], fill=rgb('20403a'))
    d.arc([28, 20, 67, 59], 130, 250, fill=rgb('3a6a5c'))
    gramophone(d, 45, 42)
    for x, y in ((35, 30), (60, 34)):                             # notes in the air
        d.line([(x, y), (x, y + 5)], fill=LEAF_HI); d.rectangle([x - 2, y + 5, x, y + 6], fill=LEAF_HI)
        d.line([(x, y), (x + 2, y + 1)], fill=LEAF_HI)
    for x0 in (8, 76):                                            # a slit window either side
        d.rectangle([x0, 24, x0 + 11, 56], fill=STONE_DK)
        d.rectangle([x0 + 1, 25, x0 + 10, 55], fill=GLASS)
        d.line([(x0 + 1, 25), (x0 + 10, 25)], fill=GLASS_HI); d.line([(x0 + 3, 28), (x0 + 3, 50)], fill=GLASS_HI)
        d.line([(x0 + 1, 40), (x0 + 10, 40)], fill=STONE_DK)
    d.rectangle([20, 65, 75, 78], fill=LEAF_DK)                   # its name
    d.rectangle([21, 66, 74, 77], fill=LACQUER)
    text(d, 'PHONO', 48 - text_w('PHONO') // 2, 68, LEAF)
    # ---- a flat canopy, the ground floor
    d.rectangle([1, 82, 94, 86], fill=STONE_DK); d.line([(1, 82), (94, 82)], fill=STONE_LO)
    d.line([(1, 87), (94, 87)], fill=INK)
    d.rectangle([4, 88, 91, 123], fill=st_lo)
    d.rectangle([7, 91, 29, 118], fill=STONE_DK)                  # a window: a gramophone and records, lit
    d.rectangle([8, 92, 28, 117], fill=WARM); d.line([(8, 92), (28, 92)], fill=WHITE)
    gramophone(d, 15, 104)
    for x, y in ((24, 97), (24, 110)):
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=SOOT); d.point((x, y), fill=RED)
    d.rectangle([34, 90, 61, 123], fill=STONE_DK)                 # glass doors
    glass_door(d, 35, 91, 60, 123, frame=ALU_DK)
    d.rectangle([66, 91, 88, 118], fill=PAPER)                    # the poster: a record, a title
    d.line([(66, 91), (88, 91)], fill=WHITE); d.rectangle([86, 92, 88, 118], fill=PAPER_LO)
    d.ellipse([70, 95, 84, 109], fill=SOOT); d.ellipse([75, 100, 79, 104], fill=KAKI)
    d.arc([71, 96, 83, 108], 200, 260, fill=STONE_LO)
    for y in (112, 115):
        d.line([(69, y), (85 - (y % 2) * 4, y)], fill=SOOT)
    d.rectangle([2, 124, 93, 127], fill=STONE_LO); d.line([(2, 124), (93, 124)], fill=STONE)
    outline(im)
    return im


# ==============================================================================
# Katamachi
# ==============================================================================
def tumbler(d, x, y, w=15, h=17):
    """A whisky glass: amber over ice."""
    d.rectangle([x, y, x + w, y + h], fill=rgb('2f3a55'))
    d.rectangle([x + 1, y + 7, x + w - 1, y + h - 2], fill=rgb('d98a2b'))
    d.line([(x + 1, y + 7), (x + w - 1, y + 7)], fill=AMBER)
    d.rectangle([x + 1, y + h - 5, x + w - 1, y + h - 2], fill=rgb('a8621f'))
    d.rectangle([x + 3, y + 5, x + 7, y + 10], fill=rgb('f8e6b4')); d.point((x + 4, y + 6), fill=WHITE)
    d.rectangle([x + 8, y + 8, x + 12, y + 12], fill=rgb('f1d190')); d.point((x + 9, y + 9), fill=WHITE)
    d.line([(x, y), (x, y + h)], fill=WHITE); d.line([(x + w, y), (x + w, y + h)], fill=rgb('8fa4c8'))
    d.line([(x, y + h), (x + w, y + h)], fill=WHITE); d.line([(x + 1, y + h - 1), (x + w - 1, y + h - 1)], fill=rgb('8fa4c8'))
    d.line([(x + 2, y + 1), (x + 2, y + 4)], fill=rgb('8fa4c8'))


def bottle(d, x, y, body, h=11):
    d.rectangle([x + 1, y, x + 2, y + 3], fill=body)
    d.point((x + 1, y), fill=LEAF)
    d.rectangle([x, y + 4, x + 3, y + h], fill=body)
    d.line([(x, y + 4), (x, y + h)], fill=WHITE)
    d.rectangle([x + 1, y + 6, x + 3, y + 8], fill=PAPER)


def whisky_bar():
    im, d = canvas(3, 5)                 # 96 x 160; the door is column 1 (x 32-63)
    dbrick(d, 4, 24, 91, 156)
    d.rectangle([84, 24, 91, 156], fill=DBRICK_LO)
    for y in range(26, 156, 3):
        d.point((86 + (y // 3) % 2 * 3, y), fill=rgb('2f1f22'))
    d.line([(4, 24), (4, 156)], fill=DBRICK_HI)
    # ---- the parapet, a water tank and a flue on the roof
    d.rectangle([2, 18, 93, 24], fill=STONE_DK)
    d.line([(2, 18), (93, 18)], fill=STONE_LO); d.line([(2, 24), (93, 24)], fill=INK)
    d.rectangle([12, 4, 34, 17], fill=rgb('7a8494'))
    d.line([(12, 4), (12, 17)], fill=rgb('a4afbd')); d.rectangle([29, 5, 34, 17], fill=rgb('5a6475'))
    d.line([(12, 4), (34, 4)], fill=rgb('a4afbd'))
    for y in (8, 13):
        d.line([(12, y), (34, y)], fill=rgb('5a6475'))
    d.rectangle([62, 8, 67, 17], fill=STONE_DK); d.rectangle([60, 6, 69, 8], fill=STONE_LO)
    # ---- the painted board: a glass of whisky
    d.rectangle([18, 29, 77, 66], fill=LEAF_DK)
    d.rectangle([20, 31, 75, 64], fill=rgb('1d2136'))
    d.line([(20, 31), (75, 31)], fill=rgb('343a5c'))
    tumbler(d, 23, 36, 17, 21)
    text(d, 'MALT', 45, 36, AMBER)
    text(d, 'BAR', 48, 47, PAPER)
    d.line([(45, 57), (71, 57)], fill=LEAF_LO)
    d.point((44, 57), fill=LEAF); d.point((72, 57), fill=LEAF)
    # ---- the first floor: two arched windows, bottles against the light
    for x in (10, 62):
        d.rectangle([x - 1, 78, x + 21, 100], fill=STONE_DK)
        d.pieslice([x - 1, 68, x + 21, 90], 180, 360, fill=STONE_DK)
        d.rectangle([x + 1, 79, x + 19, 98], fill=LIT)
        d.pieslice([x + 1, 70, x + 19, 90], 180, 360, fill=WARM)
        d.line([(x + 10, 71), (x + 10, 98)], fill=STONE_DK)
        d.line([(x + 1, 88), (x + 19, 88)], fill=rgb('8f7440'))
        for i in range(4):
            bottle(d, x + 2 + i * 4 + (1 if i > 1 else 0), 77, (rgb('6a3a1c'), rgb('2f4a44'), rgb('8a5a22'), rgb('3a2a20'))[(i + x) % 4], 10)
        d.rectangle([x - 2, 101, x + 22, 102], fill=STONE_LO)
    d.line([(47, 70), (47, 76)], fill=SOOT_LO); d.line([(43, 70), (51, 70)], fill=SOOT_LO)   # an amber lamp on an iron bracket
    d.rectangle([44, 76, 50, 77], fill=SOOT_LO)
    d.ellipse([41, 78, 53, 93], fill=rgb('e89a2e')); d.ellipse([43, 80, 48, 87], fill=rgb('fde28a'))
    d.arc([41, 78, 53, 93], -60, 90, fill=rgb('b8701f'))
    d.rectangle([45, 94, 49, 95], fill=SOOT_LO)
    # ---- a copper canopy over the pavement
    for y in range(106, 115):
        w = y - 106
        d.line([(3 - min(w, 2), y), (92 + min(w, 2), y)], fill=rgb('2f4a44') if y % 3 else rgb('1e302f'))
    d.line([(3, 106), (92, 106)], fill=rgb('46695c'))
    d.line([(1, 115), (94, 115)], fill=LEAF_LO)
    d.line([(1, 116), (94, 116)], fill=INK)
    # ---- the ground floor
    d.rectangle([4, 117, 91, 156], fill=rgb('3b2a2a'))
    d.rectangle([84, 117, 91, 156], fill=rgb('2c1f22'))
    d.line([(4, 117), (4, 156)], fill=rgb('5a4038'))
    d.rectangle([8, 122, 29, 146], fill=LEAF_DK)                  # the bottle window
    d.rectangle([9, 123, 28, 145], fill=LIT)
    d.line([(9, 123), (28, 123)], fill=WARM)
    d.line([(9, 134), (28, 134)], fill=rgb('8f7440'))
    for i in range(5):
        bottle(d, 10 + i * 4, 123, (rgb('8a5a22'), rgb('6a3a1c'), rgb('2f4a44'), rgb('3a2a20'), rgb('8a5a22'))[i], 10)
        bottle(d, 10 + i * 4, 135, (rgb('2f4a44'), rgb('8a5a22'), rgb('3a2a20'), rgb('6a3a1c'), rgb('2f4a44'))[i], 9)
    d.rectangle([8, 147, 29, 149], fill=rgb('5a4038'))
    d.rectangle([35, 120, 60, 156], fill=rgb('2c1f22'))           # the door
    d.rectangle([37, 122, 58, 156], fill=rgb('6e4630'))
    d.line([(37, 122), (37, 156)], fill=rgb('8f6040')); d.rectangle([56, 123, 58, 156], fill=rgb('553523'))
    d.rectangle([41, 126, 54, 138], fill=LIT); d.line([(41, 126), (54, 126)], fill=WARM)
    d.line([(47, 126), (47, 138)], fill=rgb('553523')); d.line([(41, 132), (54, 132)], fill=rgb('553523'))
    d.rectangle([41, 142, 54, 152], fill=rgb('553523')); d.line([(41, 142), (54, 142)], fill=rgb('8f6040'))
    d.rectangle([53, 139, 54, 141], fill=LEAF)
    d.rectangle([46, 117, 49, 119], fill=WARM)                    # the lamp over it
    # a cask on end by the door, a chalk board on the wall
    d.rectangle([66, 124, 86, 135], fill=rgb('2a3b33'))
    d.rectangle([67, 125, 85, 134], fill=rgb('1f2c28'))
    for y in (127, 130, 132):
        d.line([(69, y), (79 + (y % 4), y)], fill=PAPER_LO)
    d.rectangle([68, 138, 85, 156], fill=WOOD)
    d.ellipse([67, 136, 86, 141], fill=rgb('d2a58c')); d.ellipse([70, 137, 83, 140], fill=WOOD)
    d.line([(68, 139), (68, 156)], fill=rgb('d2a58c')); d.rectangle([82, 140, 85, 156], fill=WOOD_LO)
    for x in (72, 77):
        d.line([(x, 141), (x, 156)], fill=WOOD_LO)
    for y in (143, 151):
        d.rectangle([68, y, 85, y + 1], fill=LACQUER_LO); d.point((69, y), fill=STONE_LO)
    d.rectangle([2, 157, 93, 159], fill=STONE_LO); d.line([(2, 157), (93, 157)], fill=STONE)
    outline(im)
    return im


def mug(d, x, y):
    """A mug of beer with its head on."""
    d.rectangle([x, y + 3, x + 7, y + 12], fill=AMBER)
    d.line([(x, y + 3), (x, y + 12)], fill=rgb('fde28a')); d.line([(x + 7, y + 3), (x + 7, y + 12)], fill=rgb('c98a1e'))
    d.rectangle([x + 3, y + 5, x + 4, y + 11], fill=rgb('fde28a'))
    d.rectangle([x - 1, y, x + 8, y + 3], fill=WHITE); d.point((x - 1, y), fill=AMBER); d.point((x + 8, y), fill=AMBER)
    d.rectangle([x + 8, y + 5, x + 10, y + 10], fill=WHITE); d.rectangle([x + 8, y + 7, x + 9, y + 8], fill=AMBER)
    d.line([(x, y + 13), (x + 7, y + 13)], fill=rgb('c98a1e'))


def izakaya():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1 (x 32-63)
    roof(d, 10, 30, (10, 117), (0, 127), KAWARA_P, p=1.2)
    # ---- the upper floor: the big board, lit rooms either side of nothing at all
    d.rectangle([2, 34, 125, 67], fill=WOOD_LO)
    d.rectangle([2, 34, 4, 67], fill=WOOD); d.rectangle([120, 34, 125, 67], fill=WOOD_DK)
    for x in range(8, 124, 6):
        d.line([(x, 35), (x, 67)], fill=WOOD_DK)
    d.rectangle([6, 37, 121, 57], fill=RED_DK)
    d.rectangle([8, 39, 119, 55], fill=AMBER)
    d.line([(8, 39), (119, 39)], fill=rgb('fde28a')); d.line([(8, 55), (119, 55)], fill=rgb('c98a1e'))
    kana(d, ['no', 'mi', 'ho', 'u', 'da', 'i'], 12, 44, RED_DK)
    mug(d, 63, 41)
    d.rectangle([78, 41, 116, 53], fill=RED)
    d.line([(78, 41), (116, 41)], fill=RED_HI)
    text(d, 'SAKE', 86, 44, WHITE)
    for x in (10, 30, 88, 108):                                   # small lit windows under the board
        d.rectangle([x, 59, x + 12, 66], fill=WOOD_DK)
        d.rectangle([x + 1, 60, x + 11, 65], fill=LIT)
        d.line([(x + 6, 60), (x + 6, 65)], fill=WOOD_DK)
    # ---- the pent roof
    roof(d, 69, 76, (3, 124), (0, 127), KAWARA_P, ridge=False, p=1.0)
    # ---- the ground floor
    d.rectangle([2, 80, 125, 123], fill=WOOD_LO)
    d.rectangle([2, 80, 4, 123], fill=WOOD); d.rectangle([120, 80, 125, 123], fill=WOOD_DK)
    d.rectangle([2, 80, 125, 81], fill=WOOD_DK)
    # the left window: the menu on paper strips
    d.rectangle([6, 96, 29, 118], fill=WOOD_DK)
    d.rectangle([7, 97, 28, 117], fill=LIT); d.line([(7, 97), (28, 97)], fill=WARM)
    for i, x in enumerate(range(9, 27, 4)):
        d.rectangle([x, 99, x + 2, 112 - i % 2 * 3], fill=PAPER)
        for y in range(101, 110 - i % 2 * 3, 3):
            d.point((x + 1, y), fill=RED_DK if (i + y) % 2 else SOOT)
    d.rectangle([6, 119, 29, 123], fill=WOOD_DK)
    # the door under its noren
    d.rectangle([33, 96, 62, 123], fill=SOOT_LO)
    sliding_doors(d, 34, 108, 61, 123, lit=True, frame=WOOD_DK)
    noren(d, 34, 96, 61, 113, RED_DK, RED, None, slits=3)
    for i, x in enumerate((37, 44, 51, 58)):
        d.rectangle([x - 1, 99, x, 108], fill=PAPER)
        d.rectangle([x - 2, 102, x + 1, 102], fill=PAPER)
        d.point((x + (1 if i % 2 else -2), 106), fill=PAPER)
    # the right window: the counter, heads against the light
    d.rectangle([66, 96, 103, 118], fill=WOOD_DK)
    d.rectangle([67, 97, 102, 117], fill=LIT); d.line([(67, 97), (102, 97)], fill=WARM)
    for x in (72, 82, 93):
        d.ellipse([x, 104, x + 5, 109], fill=rgb('5a3a2a'))
        d.rectangle([x - 2, 110, x + 7, 117], fill=rgb('5a3a2a'))
    d.line([(84, 97), (84, 117)], fill=WOOD_DK)
    d.rectangle([66, 119, 103, 123], fill=WOOD_DK)
    # crates of empties, the big red lantern
    for j, y in enumerate((114, 105)):
        d.rectangle([106, y, 117, y + 8], fill=AMBER if j == 0 else rgb('3f7fb5'))
        d.line([(106, y), (117, y)], fill=rgb('fde28a') if j == 0 else rgb('7db9fa'))
        d.rectangle([108, y + 3, 110, y + 5], fill=SOOT); d.rectangle([113, y + 3, 115, y + 5], fill=SOOT)
        d.line([(106, y + 8), (117, y + 8)], fill=rgb('c98a1e') if j == 0 else rgb('2c5a8a'))
    # the row of lanterns under the eave
    d.line([(4, 83), (123, 83)], fill=SOOT)
    for i, x in enumerate(range(6, 120, 13)):
        lantern(d, x, 84, 9, 11) if i % 2 == 0 else lantern(d, x, 84, 9, 11, body=PAPER, hi=WHITE, lo=PAPER_LO)
    d.rectangle([0, 124, 127, 127], fill=STONE_LO); d.line([(0, 124), (127, 124)], fill=STONE)
    outline(im)
    return im


def kissaten():
    """A kissaten, the old kind of coffee house: brown glazed tile under a
    striped awning, coloured glass upstairs, siphons in the window and a case
    of wax samples (a cream soda, a pudding) by the door."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is column 1 (x 32-63)
    tile, tile_hi, tile_lo = rgb('8c5a48'), rgb('a8705a'), rgb('6c4238')
    br, br_dk = rgb('5a3a2a'), rgb('3a2a22')
    d.rectangle([68, 2, 75, 9], fill=STONE_DK); d.rectangle([66, 0, 77, 2], fill=STONE_LO)      # a flue
    d.rectangle([2, 10, 93, 16], fill=CREAM_LO)                   # the parapet
    d.line([(2, 10), (93, 10)], fill=WHITE); d.line([(2, 16), (93, 16)], fill=CREAM_DK)
    d.rectangle([4, 17, 91, 66], fill=CREAM)                      # stucco
    d.rectangle([85, 17, 91, 66], fill=CREAM_LO)
    d.line([(4, 17), (4, 66)], fill=WHITE)
    # ---- the board: a cup and the word
    d.rectangle([12, 20, 75, 35], fill=br)
    d.rectangle([13, 21, 74, 34], fill=PAPER)
    text(d, 'COFFEE', 34, 24, br)
    d.rectangle([18, 26, 25, 31], fill=br); d.rectangle([26, 27, 27, 29], fill=br)
    d.line([(17, 32), (27, 32)], fill=br)
    d.point((20, 24), fill=br); d.point((21, 23), fill=br); d.point((23, 24), fill=br); d.point((24, 23), fill=br)
    # ---- three windows of coloured glass
    panes = (rgb('f2c66a'), rgb('8ab878'), rgb('e58a4a'), WARM, rgb('7aa8c8'), rgb('f2c66a'))
    for i, x0 in enumerate((9, 33, 57)):
        d.rectangle([x0 - 1, 40, x0 + 20, 62], fill=br_dk)
        for r in range(3):
            for c in range(2):
                x, y = x0 + c * 10, 41 + r * 7
                d.rectangle([x, y, x + 9, y + 6], fill=panes[(i * 2 + r * 3 + c) % 6])
                d.line([(x, y), (x + 9, y)], fill=WHITE if (r + c + i) % 3 == 0 else panes[(i * 2 + r * 3 + c) % 6])
                d.line([(x + 9, y), (x + 9, y + 6)], fill=br_dk); d.line([(x, y + 6), (x + 9, y + 6)], fill=br_dk)
        d.rectangle([x0 - 2, 63, x0 + 21, 64], fill=CREAM_DK)
    d.line([(80, 44), (90, 44)], fill=SOOT)                       # a round cup sign on a bracket
    d.ellipse([79, 46, 91, 58], fill=br); d.ellipse([80, 47, 90, 57], fill=PAPER)
    d.rectangle([83, 50, 87, 54], fill=br); d.point((88, 52), fill=br)
    # ---- the awning, scalloped
    green = rgb('3f6a50')
    for x in range(1, 95):
        s = (x - 1) % 8
        c = green if ((x - 1) // 8) % 2 == 0 else PAPER
        hem = 80 + (1 if 1 <= s <= 6 else 0) + (1 if 2 <= s <= 5 else 0)
        d.line([(x, 68), (x, hem)], fill=c)
        d.point((x, 68), fill=rgb('5f8a6a') if c == green else WHITE)
        d.point((x, hem), fill=rgb('2c4a3a') if c == green else PAPER_LO)
    # ---- the ground floor in brown tile
    d.rectangle([4, 83, 91, 123], fill=tile)
    for y in range(83, 124):
        for x in range(4, 92):
            if (y - 83) % 5 == 4 or (x + ((y - 83) // 5) % 2 * 5) % 10 == 0:
                d.point((x, y), fill=tile_lo)
    d.rectangle([86, 83, 91, 123], fill=tile_lo)
    d.line([(4, 83), (4, 123)], fill=tile_hi)
    d.rectangle([4, 83, 91, 84], fill=br_dk)                      # the awning's shadow
    d.rectangle([6, 89, 29, 115], fill=br_dk)                     # the window: two siphons, a lace half-curtain
    d.rectangle([7, 90, 28, 114], fill=LIT); d.line([(7, 90), (28, 90)], fill=WARM)
    for x in (10, 20):
        d.line([(x + 2, 93), (x + 2, 104)], fill=br_dk)
        d.rectangle([x + 1, 93, x + 4, 97], fill=rgb('dfe9f2')); d.point((x + 1, 93), fill=WHITE)
        d.ellipse([x, 99, x + 5, 104], fill=rgb('8a4a22')); d.point((x + 1, 100), fill=rgb('d98a2b'))
        d.line([(x - 1, 105), (x + 6, 105)], fill=br_dk)
    d.rectangle([7, 106, 28, 114], fill=PAPER)
    for x in range(7, 29):
        if x % 4 == 1:
            d.point((x, 106), fill=LIT)
        if (x + 2) % 4 == 0:
            d.point((x, 109), fill=PAPER_LO); d.point((x + 1, 112), fill=PAPER_LO)
    d.line([(17, 90), (17, 105)], fill=br_dk)
    d.rectangle([34, 87, 61, 123], fill=br_dk)                    # the door: timber, an oval of glass
    d.rectangle([36, 89, 59, 123], fill=rgb('7a4a30'))
    d.line([(36, 89), (36, 123)], fill=rgb('a06a44')); d.rectangle([57, 90, 59, 123], fill=rgb('5f3824'))
    d.ellipse([41, 93, 54, 110], fill=br_dk); d.ellipse([42, 94, 53, 109], fill=LIT)
    d.arc([42, 94, 53, 109], 180, 320, fill=WARM)
    d.rectangle([41, 113, 54, 120], fill=rgb('5f3824')); d.line([(41, 113), (54, 113)], fill=rgb('a06a44'))
    d.rectangle([55, 106, 56, 109], fill=LEAF)
    d.rectangle([46, 85, 49, 86], fill=WARM)
    d.rectangle([65, 90, 90, 114], fill=br_dk)                    # the sample case
    d.rectangle([66, 91, 89, 113], fill=WARM); d.line([(66, 91), (89, 91)], fill=WHITE)
    d.line([(66, 102), (89, 102)], fill=rgb('8f7440'))
    d.rectangle([68, 95, 71, 101], fill=rgb('5fb87a')); d.rectangle([68, 93, 71, 95], fill=WHITE)   # a cream soda
    d.point((69, 92), fill=RED)
    d.rectangle([75, 98, 80, 101], fill=rgb('f0cc50')); d.rectangle([75, 97, 80, 97], fill=rgb('8a4a22'))   # a pudding
    d.rectangle([84, 96, 87, 101], fill=PAPER); d.rectangle([84, 96, 87, 97], fill=rgb('8a4a22'))  # coffee
    d.ellipse([67, 106, 76, 111], fill=PAPER); d.rectangle([69, 107, 73, 109], fill=RED)           # napolitan
    d.ellipse([79, 106, 88, 111], fill=PAPER); d.rectangle([81, 107, 85, 109], fill=rgb('c99a58'))  # toast
    d.rectangle([65, 115, 90, 123], fill=br)
    d.line([(65, 115), (90, 115)], fill=rgb('7a5a44'))
    d.rectangle([2, 124, 93, 127], fill=STONE_LO); d.line([(2, 124), (93, 124)], fill=STONE)
    outline(im)
    return im


def yakitori():
    """A yakitori counter: one low storey under black tiles, a great red
    lantern with its name, a short noren, skewers over the coals in the open
    window and the smoke going up the flue."""
    im, d = canvas(3, 3)                 # 96 x 96; the door is column 1 (x 32-63)
    d.rectangle([74, 3, 83, 20], fill=ALU_LO)                     # the flue
    d.line([(74, 3), (74, 20)], fill=ALU); d.rectangle([81, 4, 83, 20], fill=ALU_DK)
    d.rectangle([72, 0, 85, 3], fill=ALU_DK); d.line([(72, 0), (85, 0)], fill=ALU_LO)
    roof(d, 16, 30, (6, 89), (0, 95), KAWARA_P, p=1.2)
    d.rectangle([2, 34, 93, 91], fill=WOOD_LO)
    d.rectangle([2, 34, 4, 91], fill=WOOD); d.rectangle([88, 34, 93, 91], fill=WOOD_DK)
    for x in range(8, 88, 6):
        d.line([(x, 35), (x, 91)], fill=WOOD_DK)
    d.rectangle([2, 34, 93, 35], fill=WOOD_DK)
    # ---- the lantern
    d.rectangle([12, 37, 19, 39], fill=SOOT)
    for y in range(40, 85):
        w = round(9.5 * math.sqrt(max(0.0, 1 - ((y - 62) / 22.5) ** 2)))
        d.line([(15 - w, y), (16 + w, y)], fill=RED_LO if y % 4 == 0 else RED)
        d.point((15 - w, y), fill=RED_HI); d.point((16 + w, y), fill=RED_DK)
        if w > 4:
            d.point((15 - w + 2, y), fill=RED_HI)
    d.rectangle([11, 45, 20, 78], fill=RED)
    kana(d, ['ya', 'ki', 'to', 'ri'], 12, 46, SOOT_LO, vertical=True)
    d.rectangle([12, 85, 19, 87], fill=SOOT)
    # ---- the door under a short noren
    d.rectangle([33, 40, 62, 91], fill=SOOT_LO)
    sliding_doors(d, 34, 56, 61, 91, lit=True, frame=WOOD_DK)
    noren(d, 34, 42, 61, 59, INDIGO, INDIGO_HI, None, slits=3)
    for x in (37, 44, 51, 58):                                    # a skewer on each panel
        d.line([(x, 46), (x, 56)], fill=PAPER)
        d.rectangle([x - 1, 47, x + 1, 48], fill=KAKI); d.rectangle([x - 1, 50, x + 1, 51], fill=PAPER)
        d.rectangle([x - 1, 53, x + 1, 54], fill=KAKI)
    # ---- the open window: skewers over the coals
    d.rectangle([65, 44, 90, 74], fill=WOOD_DK)
    d.rectangle([66, 45, 89, 62], fill=LIT); d.line([(66, 45), (89, 45)], fill=WARM)
    d.ellipse([74, 47, 80, 53], fill=rgb('5a3a2a')); d.rectangle([72, 54, 82, 62], fill=rgb('5a3a2a'))   # the cook
    d.line([(74, 49), (80, 49)], fill=PAPER)
    d.rectangle([66, 63, 89, 65], fill=SOOT)
    for x in range(68, 89, 4):
        d.line([(x, 57), (x, 65)], fill=rgb('e6cf94'))
        d.point((x, 59), fill=rgb('a85a2c')); d.point((x, 61), fill=rgb('7a3c1c')); d.point((x, 63), fill=rgb('a85a2c'))
    d.rectangle([66, 66, 89, 69], fill=rgb('f0903a'))
    for x in range(67, 89, 3):
        d.point((x, 66), fill=AMBER); d.point((x + 1, 68), fill=rgb('c8501e'))
    d.rectangle([66, 70, 89, 73], fill=SOOT_LO)
    d.rectangle([64, 75, 91, 78], fill=WOOD); d.line([(64, 75), (91, 75)], fill=rgb('d2a58c'))
    d.rectangle([68, 81, 80, 90], fill=AMBER); d.line([(68, 81), (80, 81)], fill=rgb('fde28a'))    # a crate
    d.rectangle([70, 84, 72, 86], fill=SOOT); d.rectangle([76, 84, 78, 86], fill=SOOT)
    d.line([(68, 90), (80, 90)], fill=rgb('c98a1e'))
    d.rectangle([0, 92, 95, 95], fill=STONE_LO); d.line([(0, 92), (95, 92)], fill=STONE)
    outline(im)
    for x, y, w in ((77, 40, 3), (79, 37, 2), (78, 33, 3), (80, 29, 2), (79, 24, 2)):       # smoke
        shade(im, [x, y, x + w, y + 1], (233, 238, 246, 120))
    return im


def andon_post():
    """Katamachi's street lamp: a tall paper andon in a wooden frame under a
    little tiled cap, the quarter's name down it in kana. (Its key holds
    `-lanterns`, so DayNight gives it a halo at night.)"""
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([13, 49, 18, 59], fill=WOOD_LO)                   # the post
    d.line([(13, 49), (13, 59)], fill=WOOD); d.line([(18, 49), (18, 59)], fill=WOOD_DK)
    d.rectangle([10, 59, 21, 62], fill=GRAN); d.line([(10, 59), (21, 59)], fill=GRAN_HI)
    d.rectangle([10, 62, 21, 62], fill=GRAN_DK)
    d.rectangle([9, 12, 22, 49], fill=KIM_DK)                     # the frame
    d.rectangle([10, 13, 21, 48], fill=rgb('f8ecc4'))             # lit paper
    d.line([(10, 13), (10, 48)], fill=WHITE)
    d.line([(21, 13), (21, 48)], fill=rgb('e6cf94'))
    d.rectangle([10, 45, 21, 48], fill=rgb('f2c66a'))             # the flame, low in it
    kana(d, ['ka', 'ta', 'ma', 'chi'], 12, 14, KIM, vertical=True)
    for y in (12, 49):
        d.line([(8, y), (23, y)], fill=KIM_LO)
    for y in range(5, 12):                                        # the cap
        w = 4 + (y - 5)
        d.line([(15 - w, y), (16 + w, y)], fill=KAWARA_P[1] if y % 3 == 2 else KAWARA_P[0])
        d.point((15 - w, y), fill=KAWARA_P[2]); d.point((16 + w, y), fill=KAWARA_P[3])
    d.rectangle([14, 2, 17, 4], fill=KAWARA_P[1]); d.point((14, 2), fill=KAWARA_P[2])
    outline(im)
    return im


# ==============================================================================
# Nagamachi
# ==============================================================================
def samurai_gate():
    im, d = canvas(5, 3)                 # 160 x 96; you walk through column 2 (x 64-95)
    roof(d, 13, 34, (12, 147), (0, 159), KAWARA_P, p=1.2)
    for x0, x1, s in ((2, 63, 1), (96, 157, 3)):
        d.rectangle([x0, 38, x1, 56], fill=PLASTER)               # plaster over
        d.line([(x0, 38), (x1, 38)], fill=PLASTER_SH); d.line([(x0, 39), (x1, 39)], fill=PLASTER_LO)
        d.rectangle([x0, 57, x1, 85], fill=rgb('5c4a40'))         # weatherboards under
        for x in range(x0, x1 + 1):
            if (x - x0) % 6 == 0:
                d.line([(x, 58), (x, 85)], fill=rgb('3f3330'))
            elif (x - x0) % 6 == 1:
                d.line([(x, 58), (x, 85)], fill=rgb('77614f'))
        d.rectangle([x0, 56, x1, 58], fill=rgb('3f3330')); d.line([(x0, 56), (x1, 56)], fill=rgb('77614f'))
        d.line([(x0, 72), (x1, 72)], fill=rgb('3f3330'))
        cobbles(d, x0, 86, x1, 95, s)
        for x in (x0, x0 + 30, x1 - 1):                           # the frame's posts
            d.rectangle([x, 38, x + 1, 56], fill=rgb('5c4a40'))
    for x0, x1 in ((10, 26), (38, 54), (104, 120), (132, 148)):
        barred(d, x0, 43, x1, 51, frame=rgb('5c4a40'))
    # ---- the gateway
    d.rectangle([62, 38, 97, 47], fill=rgb('4a3a34'))
    d.line([(62, 38), (97, 38)], fill=rgb('77614f')); d.line([(62, 47), (97, 47)], fill=rgb('2c2224'))
    for x in range(66, 96, 6):
        d.rectangle([x, 41, x + 1, 44], fill=STONE_LO); d.point((x, 41), fill=WHITE)
    for x0 in (62, 92):
        d.rectangle([x0, 48, x0 + 5, 95], fill=rgb('4a3a34'))
        d.line([(x0, 48), (x0, 95)], fill=rgb('77614f')); d.line([(x0 + 5, 48), (x0 + 5, 95)], fill=rgb('2c2224'))
        d.rectangle([x0 - 1, 91, x0 + 6, 95], fill=GRAN); d.line([(x0 - 1, 91), (x0 + 6, 91)], fill=GRAN_HI)
        for y in (56, 70, 84):
            d.rectangle([x0, y, x0 + 5, y + 1], fill=LACQUER_LO)
    for x0 in (68, 87):
        d.rectangle([x0, 48, x0 + 4, 93], fill=rgb('3a2d2b'))
        d.line([(x0 + 1, 50), (x0 + 1, 92)], fill=rgb('5c4a40'))
        for y in range(54, 92, 7):
            d.point((x0 + 3, y), fill=STONE_LO)
    d.rectangle([99, 60, 104, 76], fill=rgb('cfae84'))            # the house's name on the post side
    d.line([(99, 60), (99, 76)], fill=rgb('e8d2ae'))
    for y in (63, 67, 71):
        d.rectangle([101, y, 102, y + 2], fill=SOOT)
    outline(im)
    shade(im, [73, 48, 86, 52], (10, 22, 39, 150))
    shade(im, [73, 53, 86, 56], (10, 22, 39, 70))
    shade(im, [150, 38, 157, 95], (10, 22, 39, 70))               # the east end, turned from the light
    return im


def samurai_house():
    """A samurai house of the Nagamachi court, gable to the front as Kanazawa
    builds them (azuma-dachi): a great white-plastered gable squared off by
    dark posts and ties under black tiles, a pent roof, earthen walls over
    boards on river stones, paper screens, a barred window, the entrance."""
    im, d = canvas(5, 4)                 # 160 x 128; the door is column 2 (x 64-95)
    tb, tb_hi, tb_dk = rgb('4a3a34'), rgb('77614f'), rgb('2c2224')
    # ---- the gable
    d.polygon([(79, 14), (80, 14), (148, 58), (11, 58)], fill=PLASTER)
    d.polygon([(124, 43), (148, 58), (124, 58)], fill=PLASTER_LO)

    def gy(x):
        return 14 + abs(x - 79.5) * 44 / 68

    for x in range(31, 130, 16):                                  # posts
        d.line([(x, round(gy(x))), (x, 58)], fill=tb)
        d.line([(x + 1, round(gy(x + 1))), (x + 1, 58)], fill=tb_dk)
    for y in (29, 39, 49):                                        # ties
        half = (y - 14) * 68 / 44
        d.line([(round(79.5 - half), y), (round(79.5 + half), y)], fill=tb)
        d.line([(round(79.5 - half), y + 1), (round(79.5 + half), y + 1)], fill=tb_dk)
    d.rectangle([76, 19, 83, 25], fill=SOOT)                      # the vent under the ridge
    for x in (78, 81):
        d.line([(x, 19), (x, 25)], fill=PLASTER)
    # ---- the roof's edges: black tiles down each side of the gable
    d.polygon([(79, 5), (80, 5), (80, 13), (4, 62), (4, 55)], fill=KAWARA_P[0])
    d.polygon([(80, 5), (155, 55), (155, 62), (80, 13)], fill=KAWARA_P[1])
    d.line([(79, 5), (4, 55)], fill=KAWARA_P[2])
    d.line([(80, 13), (155, 62)], fill=KAWARA_P[3]); d.line([(79, 13), (4, 62)], fill=KAWARA_P[1])
    for k in range(1, 15):                                        # the tile ends
        xl, xr = 79 - k * 5, 80 + k * 5
        yl = 5 + k * 5 * 50 / 75
        d.line([(xl, round(yl) + 1), (xl, round(yl) + 6)], fill=KAWARA_P[1])
        d.line([(xr, round(yl) + 1), (xr, round(yl) + 6)], fill=KAWARA_P[3])
    d.rectangle([76, 1, 83, 9], fill=KAWARA_P[0])                 # the ridge-end tile
    d.line([(76, 1), (76, 9)], fill=KAWARA_P[2]); d.line([(83, 2), (83, 9)], fill=KAWARA_P[1])
    # ---- the pent roof
    d.rectangle([6, 58, 153, 61], fill=tb_dk)
    roof(d, 61, 68, (4, 155), (0, 159), KAWARA_P, ridge=False, p=1.0)
    # ---- the ground floor: earth over boards
    d.rectangle([4, 72, 155, 99], fill=OCHRE)
    for y in range(72, 100):
        for x in range(4, 156):
            k = h3(x % 32, y, 3)
            if k < 14:
                d.point((x, y), fill=OCHRE_HI)
            elif k < 24:
                d.point((x, y), fill=OCHRE_LO)
    d.rectangle([4, 72, 155, 73], fill=OCHRE_DK)
    d.rectangle([4, 100, 155, 119], fill=rgb('5c4a40'))
    for x in range(4, 156):
        if (x - 4) % 6 == 0:
            d.line([(x, 101), (x, 119)], fill=rgb('3f3330'))
        elif (x - 4) % 6 == 1:
            d.line([(x, 101), (x, 119)], fill=tb_hi)
    d.line([(4, 100), (155, 100)], fill=tb_hi)
    cobbles(d, 4, 120, 155, 127, 2)
    d.rectangle([9, 77, 57, 112], fill=tb)                        # paper screens on the veranda
    for i in range(4):
        x0 = 11 + i * 11
        d.rectangle([x0, 79, x0 + 9, 104], fill=PAPER)
        d.line([(x0, 79), (x0 + 9, 79)], fill=WHITE)
        d.line([(x0 + 5, 79), (x0 + 5, 104)], fill=tb)
        for y in (86, 92, 98):
            d.line([(x0, y), (x0 + 9, y)], fill=tb)
        d.rectangle([x0, 105, x0 + 9, 110], fill=rgb('5c4a40'))
    d.rectangle([7, 113, 59, 116], fill=WOOD); d.line([(7, 113), (59, 113)], fill=rgb('d2a58c'))
    d.rectangle([7, 117, 59, 118], fill=WOOD_DK)
    barred(d, 110, 80, 146, 92, frame=tb)                         # the barred window
    # ---- the entrance
    d.rectangle([62, 72, 97, 78], fill=tb)
    d.line([(62, 72), (97, 72)], fill=tb_hi); d.line([(62, 78), (97, 78)], fill=tb_dk)
    d.rectangle([65, 79, 94, 121], fill=SOOT_LO)
    sliding_doors(d, 66, 81, 93, 119, lit=True, frame=tb_dk)
    for x0 in (62, 95):
        d.rectangle([x0, 79, x0 + 2, 121], fill=tb)
        d.line([(x0, 79), (x0, 121)], fill=tb_hi); d.line([(x0 + 2, 79), (x0 + 2, 121)], fill=tb_dk)
    d.rectangle([60, 120, 99, 123], fill=rgb('c2c6ca'))
    d.line([(60, 120), (99, 120)], fill=WHITE); d.rectangle([60, 123, 99, 123], fill=GRAN_LO)
    d.rectangle([101, 82, 106, 98], fill=rgb('cfae84'))           # the family's name
    d.line([(101, 82), (101, 98)], fill=rgb('e8d2ae'))
    for y in (85, 89, 93):
        d.rectangle([103, y, 104, y + 2], fill=SOOT)
    for x in (4, 154):                                            # corner posts
        d.rectangle([x, 72, x + 1, 119], fill=tb); d.line([(x, 72), (x, 119)], fill=tb_hi)
    outline(im)
    shade(im, [148, 72, 155, 127], (10, 22, 39, 70))
    return im


def canal(side):
    """The Nagamachi canal's banks, as ground tiles over pond-autotile's blue."""
    im = Image.new('RGBA', (32, 32), WATER)
    px = im.load()
    if side == 'n':
        for y in range(32):
            for x in range(32):
                if y < 5:                                         # the coping stones
                    j = (x % 11 == 0)
                    c = GRAN_DK if y == 4 else (GRAN_LO if j else (WHITE if y == 0 else rgb('c2c6ca')))
                elif y < 17:                                      # the wall of fitted stone, green at the foot
                    yy, row = (y - 5) % 6, (y - 5) // 6
                    j = (x + row * 6) % 12 == 0
                    c = GRAN_DK if (yy == 5 or j) else (GRAN if yy == 0 else GRAN_LO)
                    if y > 12 and h3(x, y, 1) < 150:
                        c = MOSS_LO if h3(x, y, 8) < 150 else MOSS
                    elif y > 9 and h3(x, y, 1) < 40:
                        c = MOSS_DK
                elif y == 17:
                    c = rgb('1f2e63')
                elif y < 22:
                    c = WATER_DK if (y < 20 or (x + y) % 2) else WATER
                else:
                    c = WATER
                px[x, y] = c
        for x0, x1, y in ((4, 9, 25), (18, 26, 28), (12, 15, 23)):
            for x in range(x0, x1 + 1):
                px[x, y] = WATER_HI
    else:
        for x0, x1, y in ((6, 14, 4), (20, 27, 10), (2, 6, 14), (15, 19, 17)):
            for x in range(x0, x1 + 1):
                px[x, y] = WATER_HI
        for y in range(20, 32):                                   # the near coping, a broad kerb of long stones
            for x in range(32):
                j = ((x + 5) % 16 == 0)
                if y == 20:
                    c = rgb('1f2e63')
                elif y == 21:
                    c = WHITE
                elif y == 31:
                    c = GRAN_DK
                elif y == 26:
                    c = GRAN_LO                                   # the arris between its top and its face
                else:
                    c = GRAN_LO if j else (rgb('c2c6ca') if y < 26 else GRAN)
                px[x, y] = c
    return im


# ==============================================================================
def rows(w, r0, r1):
    return [[c, r] for r in range(r0, r1 + 1) for c in range(w)]


WARM_HEX, AMBER_HEX, RED_HEX, COAL_HEX = '#f6dc8c', '#f9c22e', '#d16b56', '#f0903a'

# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH under it (gates)
#   glow: DayNight gives the key a night halo (it matches /lamp-post|-lanterns/)
#   lit: where its lit parts are, [col, row, colour] in cells from the top-left
#        (fractions allowed), should the game ever light windows
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'ground' = a floor
#          tile, 'flat' = lies on the ground and is walked ON (Non-Collidables +
#          a negative depthBias, as kanazawa-canal-bridge is)
PIECES = [
    ('kanazawa-station-dome_0_0', station_dome, (8, 4), 'Station front', dict(
        door=[[3, 3], [4, 3]], solid=rows(8, 2, 3),
        lit=[[3.5, 3.3, WARM_HEX], [4.5, 3.3, WARM_HEX]]),
     "Kanazawa Station's east front: the Motenashi dome as a low, wide shell of glass on a diamond grid of "
     'aluminium in a heavy rim, a ring beam, and under it a plain glazed concourse: a louvred band with a '
     'dark KANAZAWA board, a thin canopy, tall panes between slim mullions, and an open entrance two cells '
     'wide (the lit hall and its ticket gates inside, tactile paving at the sill). Rows 0-1 are the shell.'),
    ('kanazawa-tsuzumi-gate_0_0', tsuzumi_gate, (6, 5), 'Station front', dict(
        solid=[[1, 4], [4, 4]], walk=[[0, 4], [2, 4], [3, 4], [5, 4]]),
     'The Tsuzumi-mon drum gate: two drum pillars of crossing red-brown timbers, narrow at the waist, on '
     'stone plinths (columns 1 and 4), carrying one deep, flat, wide roof: a slab of crossed timbers a cell '
     'and a half deep whose coffers show, with a fascia of beam ends. No upturned ends, no plaque. Only the '
     'two pillar cells are solid; you walk under the roof between and beside them. Its feet go FIVE rows '
     "south of the dome's bottom row, so its roof clears the doors and the KANAZAWA board."),
    ('kanazawa-bus-stop_0_0', bus_stop, (2, 2), 'Station front', dict(
        solid=rows(2, 1, 1)),
     'The Shirakawa-go bus stop: a glass shelter with a bench and a blue BUS board carrying a little thatched '
     'farmhouse, and a pole with a round blue bus sign and a timetable. Bump it from the row below.'),
    ('kanazawa-castle-gate_0_0', castle_gate, (4, 4), 'Kanazawa Castle', dict(
        solid=[[0, 3], [3, 3]], walk=[[1, 3], [2, 3]]),
     "The Ishikawa gate as a gatehouse (NOT Sendai's dark gate): fitted grey stone piers with the odd red "
     'and blue block, a white-plaster storey with barred windows and a namako dado, a pale lead-tile roof; '
     'iron-bound posts, the leaves folded back, a plum crest on the lintel. Walk through the middle two '
     'cells. The castle wall joins it flush on either side.'),
    ('kanazawa-castle-turret_0_0', castle_turret, (4, 5), 'Kanazawa Castle', dict(
        solid=rows(4, 3, 4)),
     'A yagura: battered stone base, a white first storey with a namako dado and a bay window under a bowed '
     'lead hood, a lead pent roof, a smaller white second storey, a lead roof with a plastered gable. No door.'),
    ('kanazawa-castle-storehouse_0_0', castle_storehouse, (6, 3), 'Kanazawa Castle', dict(
        door=[[2, 2]], solid=rows(6, 1, 2)),
     'A nagaya for the castle terrace, so it is not an empty lawn: one long low storey on a stone foot, '
     'white plaster with barred windows and a namako band, a long lead roof, iron-bound doors under a small '
     'lead hood (column 2; leave it sealed or open it).'),
    ('kanazawa-castle-wall_0_0', lambda: wall('castle', 'h'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     "The long white wall running east-west, to replace sendai-earthen-wall: lead coping, white plaster, a "
     'band of namako (a white diagonal lattice on slate), a fitted stone base. Tiles left-right; the bottom '
     'cell is solid.'),
    ('kanazawa-castle-wall-corner-e_0_0', lambda: wall('castle', 'corner-e'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The east end of an east-west run where the wall turns north: the face stops at long-and-short corner '
     'stones (in shade) and the lead coping turns up the map over a hip. Put kanazawa-castle-wall-v in the '
     'cells above it (north).'),
    ('kanazawa-castle-wall-corner-w_0_0', lambda: wall('castle', 'corner-w'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The west end where the wall turns north, drawn for its own side (lit corner stones, the lit fall of '
     'the coping), not a mirror of -corner-e.'),
    ('kanazawa-castle-wall-v_0_0', lambda: wall('castle', 'v'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The wall running north-south. Top cell: its lead coping seen from above (the lit west fall, the '
     'ridge, the east fall in shade, 28px wide). Bottom cell: the wall\'s south end (plaster, namako band, '
     'stone foot). Stacked down the map, each piece\'s coping covers the end of the piece north of it, so a '
     'run is one roof with a wall face and foot under its last piece. It joins the coping of a corner piece '
     'south of it; running south from an east-west wall it comes forward over that wall\'s face.'),
    ('kanazawa-castle-wall-end_0_0', lambda: wall('castle', 'end'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     "The same as -v with the coping hipped at its south end: the last piece of a north-south run."),
    ('kenrokuen-kotoji_0_0', kotoji, (2, 3), 'Kenrokuen', dict(
        solid=rows(2, 2, 2), lit=[[1.0, 1.0, WARM_HEX]]),
     'The Kotoji lantern, the garden\'s emblem, at twice the old sprite\'s height: a granite lantern on two '
     'bowed legs, the long one on a stone in the shallows and the short one on a rock on the bank, lichen on '
     'its roof. Stand it on the pond\'s edge with its left column over the water\'s rim.'),
    ('kenrokuen-kotoji-water_0_0', lambda: kotoji(True), (2, 3), 'Kenrokuen', dict(
        solid=rows(2, 2, 2), lit=[[1.0, 1.0, WARM_HEX]]),
     'The same lantern with its long leg going down into the pond (rings on the water round it, no stepping '
     'stone): its bottom-left cell must be a pond cell and its bottom-right cell the bank.'),
    ('kenrokuen-yukitsuri_0_0', yukitsuri(3, 4, ((-25, 88, 18, 9), (25, 84, 18, 9), (-6, 70, 21, 10),
                                               (12, 97, 20, 9), (-15, 101, 16, 7), (3, 54, 15, 8)), 20),
     (3, 4), 'Kenrokuen', dict(solid=[[1, 3]]),
     'Yukitsuri: a great spreading pine under a cone of straw ropes hung from a bamboo pole with a straw '
     'knot at its top, as the garden rigs them from 1 November. Only the trunk cell is solid. Kanazawa\'s own '
     'tree, in place of sendai-pine.'),
    ('kenrokuen-yukitsuri-small_0_0', yukitsuri(2, 3, ((-13, 66, 13, 7), (13, 63, 13, 7), (0, 51, 13, 7),
                                                     (2, 75, 15, 7)), 14),
     (2, 3), 'Kenrokuen', dict(solid=[[0, 2], [1, 2]]),
     'A smaller pine under its ropes; use several along a path.'),
    ('kenrokuen-teahouse_0_0', teahouse, (4, 3), 'Kenrokuen', dict(
        solid=rows(4, 1, 2), lit=[[2.0, 1.7, WARM_HEX]]),
     'The tea house on the pond (Uchihashi-tei): a mossy shingled roof, paper screens either side of an open '
     'room with tatami, a scroll and a low table, a railed veranda, and posts on stones standing in the '
     'water. Its bottom row belongs ON water cells (the posts, a shadow and ripples; transparent between); '
     'row 1 is the room. No door: it is looked at from the bank.'),
    ('kenrokuen-bridge_0_0', stone_bridge, (3, 1), 'Kenrokuen', dict(
        walk=[[0, 0], [1, 0], [2, 0]], layer='flat'),
     'The arched stone bridge, east-west, drawn from straight above as kanazawa-canal-bridge is: a kerb '
     'along each side, the slabs of the deck between (lighter over the crown, darker at the banks), a post '
     'at each corner. Flat: all three cells are walked ON. Lay it across a channel three cells wide.'),
    ('garden-moss_0_0', garden_moss, (1, 1), 'Kenrokuen', dict(layer='ground'),
     "Kenrokuen's ground instead of the shared grass: a deep blue-green moss heaped into cushions, each lit "
     'on one side and dark under the other, so it reads as moss and not lawn. A plain fill tile (no edge '
     'roles: lay it as a rectangle; the path family carries the same moss outside its stones).'),
    ('chaya-front-a_0_0', chaya('a'), (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3)),
     'Teahouse front, 3 cells: black glazed roof, an upper floor screened in fine kimusuko lattice with two '
     'bamboo blinds, a balcony rail, a pent roof, lattice bays, an indigo noren with a white mark over '
     'sliding doors, a white paper lantern. The three fronts tile side by side, each with its ridge at its '
     'own height and in its own tone of bengara.'),
    ('chaya-front-b_0_0', chaya('b'), (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3), lit=[[1.5, 1.6, WARM_HEX], [1.5, 3.4, WARM_HEX]]),
     'Teahouse front in aged brown-black: three lattice windows (the middle one lit), a short green noren '
     'over lamplit paper doors up a stone step, a round red lantern on a bracket, the house\'s name board.'),
    ('chaya-front-c_0_0', chaya('c'), (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3), lit=[[0.9, 1.6, WARM_HEX], [2.1, 1.6, WARM_HEX], [1.5, 3.5, WARM_HEX]]),
     'Teahouse front in the brightest bengara, open for the evening: two wide lit paper windows upstairs '
     'with guests\' shadows on them between shutter boxes, a long persimmon noren, and instead of a second '
     'lattice bay a boarded wall with a small lit window and a bench under a red cloth for tea outside.'),
    ('chaya-gold-leaf-shop_0_0', gold_shop, (4, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(4, 2, 3), lit=[[2.6, 3.2, WARM_HEX], [1.5, 3.4, WARM_HEX]]),
     'The gold-leaf shop: a storehouse upper wall laid with squares of gold leaf, a black HAKU (leaf) board, '
     'black lacquer below with a gilded screen in one window and lit gilded bowls and boxes in the other, a '
     'white noren with one gold square, and a sign of a soft-serve cone wrapped in gold leaf.'),
    ('teramachi-stair_0_0', temple_stair, (2, 3), 'Higashi Chaya (the temple hill behind)', dict(
        walk=rows(2, 0, 2), layer='flat'),
     'The temple hill\'s stone stair, flat and walked ON: eight granite treads between mossed cheek walls, '
     'fallen leaves. Tiles north-south (stack it for a longer climb).'),
    ('teramachi-gate_0_0', temple_gate, (3, 3), 'Higashi Chaya (the temple hill behind)', dict(
        solid=[[0, 2], [2, 2]], walk=[[1, 2]]),
     'A small temple gate in weathered cypress: a mossed grey-green shingle roof, a name board in gold on '
     'green, the leaves folded back, board fences either side, a paper lantern. Walk through the middle cell.'),
    ('teramachi-hall_0_0', temple_hall, (5, 4), 'Higashi Chaya (the temple hill behind)', dict(
        door=[[2, 3]], solid=rows(5, 2, 3), lit=[[2.5, 2.9, WARM_HEX]]),
     "A Teramachi temple's main hall (in place of the generic blue shrine): a great hipped roof of smoked "
     'silver-grey tiles with a plastered porch gable over the steps, weathered timber, paper behind lattice, '
     'the doors open on a dark hall with a five-coloured curtain and the altar\'s gold, a railed veranda, '
     'stone steps with an offertory box at their head. The door is the middle cell.'),
    ('chaya-phono-museum_0_0', phono_museum, (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3), lit=[[0.55, 3.2, WARM_HEX]]),
     'The phonograph museum the posts name: a plain grey stone front, a roundel with a brass horn gramophone '
     'and notes, a PHONO board, slit windows, and on the ground floor a lit window with a gramophone and '
     'records, glass doors and a record poster.'),
    ('katamachi-whisky-bar_0_0', whisky_bar, (3, 5), 'Katamachi', dict(
        door=[[1, 4]], solid=rows(3, 3, 4),
        lit=[[0.65, 2.6, AMBER_HEX], [2.3, 2.6, AMBER_HEX], [0.6, 4.2, AMBER_HEX], [1.5, 2.7, AMBER_HEX]]),
     'The whisky bar: three narrow storeys of dark brick, a painted board of a glass of whisky on ice (MALT '
     'BAR), two arched windows of bottles against the light with an amber lamp on an iron bracket between '
     'them, a copper canopy, a timber door, a bottle window, a cask on end and a chalk board. No upright '
     'sign.'),
    ('katamachi-izakaya_0_0', izakaya, (4, 4), 'Katamachi', dict(
        door=[[1, 3]], solid=rows(4, 2, 3),
        lit=[[0.6, 3.3, WARM_HEX], [2.6, 3.3, WARM_HEX], [1.5, 3.5, WARM_HEX], [2.0, 2.8, RED_HEX]]),
     'The all-you-can-drink izakaya: a big yellow board reading nomihodai in kana with a mug of beer and a '
     'red SAKE tab, a row of red and white paper lanterns under the eave, a red noren over lamplit doors, '
     'the menu on paper strips in one window and heads at the counter in the other, crates of empties.'),
    ('katamachi-kissaten_0_0', kissaten, (3, 4), 'Katamachi', dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[[0.55, 3.2, WARM_HEX], [1.5, 3.2, WARM_HEX], [2.4, 3.2, WARM_HEX], [1.5, 1.6, WARM_HEX]]),
     'A kissaten, the old kind of coffee house: cream stucco with a COFFEE board and three windows of '
     'coloured glass, a green and white scalloped awning, brown glazed tile below, siphons and a lace '
     'half-curtain in the window, a timber door with an oval of glass, a lit case of wax samples.'),
    ('katamachi-yakitori_0_0', yakitori, (3, 3), 'Katamachi', dict(
        door=[[1, 2]], solid=rows(3, 1, 2),
        lit=[[0.5, 1.9, RED_HEX], [2.4, 2.05, COAL_HEX], [1.5, 2.4, WARM_HEX]]),
     'A yakitori counter, one low storey: black tiles and a steel flue with smoke, a great red lantern '
     'reading yakitori in kana, a short indigo noren with skewers on it over lamplit doors, an open window '
     'with the cook, skewers and glowing coals, a beer crate.'),
    ('katamachi-andon-lanterns_0_0', andon_post, (1, 2), 'Katamachi', dict(
        solid=[[0, 1]], glow=True, lit=[[0.5, 0.95, WARM_HEX]]),
     "Katamachi's street lamp (not a neon sign pole): a tall paper andon in a dark wooden frame under a "
     'little tiled cap, on a post and a stone, reading katamachi down it in kana. Its key matches '
     '/-lanterns/, so it gets the night halo: stand one between bar fronts.'),
    ('nagamachi-wall_0_0', lambda: wall('komo', 'h'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     "Nagamachi's earthen wall in winter dress, east-west: a board-shingle cap, ochre rammed earth under "
     'komo straw matting the colour of the wall itself, hung from a pole, bound by three ropes, a seam '
     'between mats and a ragged fringe at its foot, on round river stones. Tiles left-right. To replace '
     'sendai-earthen-wall here.'),
    ('nagamachi-wall-bare_0_0', lambda: wall('bare', 'h'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     'The same wall without mats, to break up a long run (and for any date outside winter).'),
    ('nagamachi-wall-corner-e_0_0', lambda: wall('komo', 'corner-e'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     'The east end where the wall turns north: a corner post in shade, the shingle cap turning up the map '
     'over a hip. nagamachi-wall-v goes in the cells above it.'),
    ('nagamachi-wall-corner-w_0_0', lambda: wall('komo', 'corner-w'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     'The west end where the wall turns north, drawn for its own side (a lit post, the lit fall of the cap).'),
    ('nagamachi-wall-v_0_0', lambda: wall('bare', 'v'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     'The wall running north-south: its shingle cap seen from above in the top cell, its south end (earth '
     'between two posts on river stones) in the bottom cell. Stacks down the map as the castle wall\'s does.'),
    ('nagamachi-wall-end_0_0', lambda: wall('bare', 'end'), (1, 2), 'Nagamachi', dict(
        solid=[[0, 1]]),
     'The same as -v with the cap hipped at its south end: the last piece of a north-south run.'),
    ('nagamachi-wall-gate_0_0', lambda: wall('bare', 'gate'), (1, 2), 'Nagamachi', dict(
        walk=[[0, 1]]),
     'A roofed wicket set in the wall: two posts, a lintel, a small shingle roof a little above the wall\'s '
     'cap, the leaf folded back. One cell, walked through.'),
    ('nagamachi-samurai-gate_0_0', samurai_gate, (5, 3), 'Nagamachi', dict(
        solid=[[0, 2], [1, 2], [3, 2], [4, 2]], walk=[[2, 2]]),
     "A samurai house's nagaya-mon: a long gatehouse under black glazed tiles, white plaster with barred "
     'windows over dark weatherboards on river stones, studded posts and lintel, the leaves folded back, the '
     'house\'s name board. Walk through the middle cell into the court. The Nagamachi wall joins either end.'),
    ('nagamachi-samurai-house_0_0', samurai_house, (5, 4), 'Nagamachi', dict(
        door=[[2, 3]], solid=rows(5, 2, 3), lit=[[2.5, 3.2, WARM_HEX]]),
     'The samurai house for the court behind the gate, gable to the front as Kanazawa builds them: a great '
     'white-plastered gable squared off by dark posts and ties under black tiles, a pent roof, earthen walls '
     'over boards on river stones, paper screens on a veranda, a barred window, lamplit doors up a stone '
     'step. The door is the middle cell.'),
    ('nagamachi-canal-n_0_0', lambda: canal('n'), (1, 1), 'Nagamachi', dict(layer='ground'),
     "The canal's north bank, a ground tile in place of pond-autotile_edge-n: coping stones, a wall of "
     'fitted stone green at the waterline, its shadow on water of pond-autotile\'s own blue. Tiles east-west.'),
    ('nagamachi-canal-s_0_0', lambda: canal('s'), (1, 1), 'Nagamachi', dict(layer='ground'),
     "The canal's south bank (in place of pond-autotile_edge-s): water, then a broad near kerb of long "
     'stones seen from above. With -n over it the canal is two cells wide; put pond-autotile_center between for a wider one.'),
]
FAMILIES = [
    ('garden-path-autotile', garden_path, 'Kenrokuen',
     'A garden path: pale raked gravel between lines of grey edging stones, moss (garden-moss) outside them. '
     'Opaque; lay it on garden-moss.'),
    ('chaya-stone-autotile', chaya_stone, 'Higashi Chaya',
     'The stone-flagged lane: big grey flags of uneven length fitted close (thin joints, nearly one colour, '
     "no courses), a gutter of small setts along the sides the role names. In place of flat-grey-brick."),
]
SPRITES = {key: fn for key, fn, *_ in PIECES}
META = {key: m for key, _fn, _size, _district, m, _desc in PIECES}
for _fam, _fn, *_ in FAMILIES:
    for _r in ROLES:
        SPRITES[f'{_fam}_{_r}'] = (lambda r=_r, fn=_fn: fn(r))


def build():
    built = {}
    for key, fn in SPRITES.items():
        im = fn()
        built[key] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    return built


def glow_spots(m):
    """A piece's lit parts as the spots src/utils/Glows.js reads; `color` is a
    number, as it is in config.json (0xRRGGBB written in decimal)."""
    return [{'x': x, 'y': y, 'r': 0.9, 'color': int(c[1:], 16), 'a': 0.5} for x, y, c in m.get('lit', [])]


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
            'doors': doors,
            'solid': solid, 'walk_through': m.get('walk', []),
            'night_halo': bool(m.get('glow')),
            'glow': glow_spots(m),
            'layer': m.get('layer', 'standing'),
            'district': district, 'description': desc,
        })
    doc = {
        'tool': 'gamev2/tools/generate_kanazawa_art.py',
        'run': 'cd gamev2 && python3 tools/generate_kanazawa_art.py [--sheet out.png] [--scenes dir] [--manifest out.json]'
               '   (a python3 with Pillow; imports generate_hokkaido, generate_sendai_art, generate_sapporo_art from tools/)',
        'notes': [
            "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per "
            "cell and pixel-doubled, as generate_sapporo_art.py does); 'size' is in cells.",
            'Nothing is registered: config.json, tilePalette, spriteMetadata, tileNames, prefabs, generators, '
            'check_generators.py and docs are untouched, and the tool does not write config.json. To register a '
            'multi-cell sprite follow generate_sapporo_art.register: spriteMetadata {frameCount:1, anchorX: '
            "32/widthPx, anchorY: 32/heightPx} (centre of the top-left cell; that is 'anchor'); 1x1 tiles use "
            '0.5/0.5. The map change should also add the tool to check_generators.py.',
            "'doors' (every door cell; the station has two side by side), 'solid' and 'walk_through' are [col,row] from the sprite's top-left cell. 'solid' is "
            'the suggested footprint (rows above it are roof or sky the player walks behind). A gate lists the '
            "cells you walk through under it in 'walk_through'; only its post cells are solid. layer 'flat' "
            'pieces (the stone bridge, the temple stair) lie on the ground and are walked ON, as '
            "kanazawa-canal-bridge_0_0 is (Non-Collidables with a negative depthBias): their 'walk_through' is "
            'the walkable deck.',
            "Night: the game has no lit-window or emissive layer. DayNight.buildGlows puts one additive halo on "
            "each CELL whose tile key matches /lamp-post|-lanterns/, at the tile's own cell. 'night_halo': true "
            'marks the one key here that matches: katamachi-andon-lanterns_0_0 (a 1x2 andon post). Stand one '
            "between Katamachi's fronts. 'glow' is each sprite's lit parts as glow spots in the shape "
            "src/utils/Glows.js reads ({x, y, r, color, a}: centre in cells from the sprite's top-left, radius in "
            "cells; 'color' is a NUMBER, 0xRRGGBB in decimal, as config.json holds it): copy the list as it is "
            "into the sprite's spriteMetadata `glow` when it is registered, or into Glows.SPRITES. The spots "
            'were checked in the night previews (previews.night: the six scenes under the night grade 0x7480c0 '
            "with the halos added as DayNight / Glows draw them, in Pillow), NOT in the running game: nothing "
            'is placed in a map yet, so look at them once with ?tod=night when the map change lands.',
            'Season: early November, as the region is on master (ginkgo, maples, green ground, no snow), so no '
            'piece carries snow. Winter shows as yukitsuri ropes and komo mats, both rigged from 1 November.',
            'All sign words are generic or look-alikes: KANAZAWA (the station), BUS, HAKU (leaf), MALT BAR, SAKE, '
            'COFFEE, PHONO, and nomihodai / yakitori / katamachi in kana; no real brand artwork. The plum crest on the castle gate is five gold dots.',
            'New keys only: nothing written here has a key generate_hokuriku_art.py writes. The older sprites it '
            'draws (kanazawa-ishikawa-gate 8x4, kanazawa-kotoji 2x2, kanazawa-chaya-a/-b 4x4, kanazawa-whisky-bar '
            '4x4, kanazawa-canal-bridge 2x4) are superseded by kanazawa-castle-gate (+ wall + turret), '
            'kenrokuen-kotoji, chaya-front-a/-b/-c and katamachi-whisky-bar; the canal bridge is still good.',
            'Walls: an east-west run is <wall> tiles; where it turns north use <wall>-corner-e / -corner-w and put '
            '<wall>-v in the cells above; a run going south from an east-west wall is <wall>-v from the next row '
            'down, ended with <wall>-end. Every wall piece is 1x2 with its foot (bottom cell) solid.',
            'Station front: kanazawa-station-dome against the rail line; kanazawa-tsuzumi-gate on the forecourt '
            "with its FEET (bottom row) five rows south of the dome's bottom row, centred on the doors (the dome "
            'is 8 wide, the gate 6: offset one cell). Its roof is its top two rows, so any nearer it hides the '
            'doors and the KANAZAWA board. kanazawa-bus-stop to one side.',
        ],
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, _fn, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/kanazawa_art_sheet.png',
            'scenes': [f'.agent-queue/shots/kanazawa_art_{n}.png' for n in SCENES],
            'night': [f'.agent-queue/shots/kanazawa_art_{n}_night.png' for n in SCENES],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


# ---- previews (not part of the game) --------------------------------------------
SCENES = ('station', 'castle', 'kenrokuen', 'chaya', 'katamachi', 'nagamachi')
GRID = ('corner-nw', 'edge-n', 'corner-ne', 'edge-w', 'center', 'edge-e', 'corner-sw', 'edge-s', 'corner-se')


def spr(name):
    return Image.open(f'{SPR}/{name}.png').convert('RGBA')


def sheet(built, out):
    """Everything on one sheet at the file's size, doubled; flat and ground
    pieces last, the wall families assembled."""
    skip = ('-wall', 'canal', 'garden-moss')
    keys = [k for k, _fn, size, *_ in PIECES if not any(s in k for s in skip)]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1500 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + 64 * 8 + 120
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
    for fam, *_ in FAMILIES:                                      # each family as a 3x3 patch
        for i, r in enumerate(GRID):
            im.alpha_composite(built[f'{fam}_{r}'], (x + (i % 3) * 64, y + 64 + (i // 3) * 64))
        x += 3 * 64 + 24
    for i in range(4):                                            # moss
        im.alpha_composite(built['garden-moss_0_0'], (x + (i % 2) * 64, y + 64 + (i // 2) * 64))
    x += 2 * 64 + 24
    for i in range(3):                                            # the canal
        im.alpha_composite(built['nagamachi-canal-n_0_0'], (x + i * 64, y + 64))
        im.alpha_composite(built['nagamachi-canal-s_0_0'], (x + i * 64, y + 128))
    x, y = 20, y + 64 * 4 + 20
    for fam, mid in (('kanazawa-castle-wall', ('', '', '')), ('nagamachi-wall', ('', '-bare', '-gate', ''))):
        names = [f'{fam}-corner-w_0_0'] + [f'{fam}{m}_0_0' for m in mid] + [f'{fam}-corner-e_0_0']
        for j in (2, 1):                                          # a north-south run up from the east corner,
            im.alpha_composite(built[f'{fam}-v_0_0'], (x + (len(names) - 1) * 64, y + 128 - j * 64))
        for i, n in enumerate(names):                             # drawn north to south as the game sorts it
            im.alpha_composite(built[n], (x + i * 64, y + 128))
        x += len(names) * 64 + 16
        im.alpha_composite(built[f'{fam}-v_0_0'], (x, y + 64))
        im.alpha_composite(built[f'{fam}-end_0_0'], (x, y + 128))
        x += 64 + 24
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


class Scene:
    def __init__(self, built, w, h, ground='grass-autotile_center'):
        self.b, self.w, self.h = built, w, h
        self.im = Image.new('RGBA', (w * 64, h * 64), CLEAR)
        g = self.get(ground)
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

    def road(self, y, x0, x1):
        for x in range(x0, x1 + 1):
            self.flat('road-edge-top_0_0', x, y)
            self.flat('road-div-horizontal_0_0', x, y + 1)
            self.flat('road-edge-bottom_0_0', x, y + 2)

    def put(self, name, x, base):
        """Stand a sprite with its left edge on cell x and its feet on row `base`."""
        self.things.append((base, x, name))

    def save(self, out):
        halos = []
        for base, x, name in sorted(self.things):
            im = self.get(name)
            top = (base + 1) * 64 - im.height
            self.im.alpha_composite(im, (x * 64, top))
            m = META.get(name, {})
            for spot in glow_spots(m):
                halos.append((x * 64 + spot['x'] * 64, top + spot['y'] * 64, spot['r'] * 64, spot['color'], spot['a']))
            if m.get('glow') or 'lamp-post' in name:              # DayNight's own lamp halo, on the top cell
                halos.append((x * 64 + 32, top + 32 - 64 * 0.15, 64 * 1.6, 0xffb366, 1.0))
        self.im.save(out)
        print('scene ->', out, self.im.size)
        night(self.im, halos).save(out[:-4] + '_night.png')


def night(im, halos):
    """The scene as the game shows it at night, in Pillow: DayNight's night
    grade (MULTIPLY by 0x7480c0), then each halo added the way Glows.texture
    and DayNight.buildGlows build one (six stepped discs of 0.028 * (7 - i)).
    A preview only: the game is the judge once the sprites are placed."""
    px = im.convert('RGB').load()
    W, H = im.size
    buf = [[px[x, y][0] * 0x74 / 255, px[x, y][1] * 0x80 / 255, px[x, y][2] * 0xc0 / 255]
           for y in range(H) for x in range(W)]
    step = [sum(0.028 * (7 - i) for i in range(k, 7)) for k in range(1, 7)]      # strength inside ring k
    for cx, cy, r, col, a in halos:
        c = ((col >> 16) & 255, (col >> 8) & 255, col & 255)
        for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
            for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
                q = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
                if q < 1:
                    k = step[min(5, int(q * 6))] * a
                    b = buf[y * W + x]
                    b[0] += c[0] * k; b[1] += c[1] * k; b[2] += c[2] * k
    out = Image.new('RGB', (W, H))
    out.putdata([(min(255, round(b[0])), min(255, round(b[1])), min(255, round(b[2]))) for b in buf])
    return out


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    # Station front: the dome on the rail line, the drum gate on the forecourt, the bus stop
    s = Scene(built, 20, 13)
    s.floor('light-concrete-autotile', (1, 6, 18, 12))
    s.put('kanazawa-station-dome_0_0', 6, 6)
    s.put('kanazawa-tsuzumi-gate_0_0', 7, 11)                      # feet five rows south of the dome's
    s.put('kanazawa-bus-stop_0_0', 15, 9); s.put('kanazawa-bus-stop_0_0', 2, 9)
    s.put('hokuriku-ginkgo_0_0', 1, 6); s.put('hokuriku-ginkgo_0_0', 17, 6)
    s.put('blue-lamp-post_0_0', 5, 8); s.put('blue-lamp-post_0_0', 14, 8)
    s.put(me, 9, 7); s.put(me, 10, 11); s.put(me, 6, 11); s.put(me, 16, 10); s.put(me, 13, 12); s.put(me, 9, 9)
    s.save(f'{outdir}/kanazawa_art_station.png')
    # Kanazawa Castle: the gate in the long wall, the turret at its corner, the wall turning north
    s = Scene(built, 22, 12)
    s.floor('gravel-autotile', (9, 7, 10, 11), (0, 10, 21, 11), (9, 4, 10, 6), (9, 3, 16, 4))
    s.put('kanazawa-castle-storehouse_0_0', 13, 2)                # on the terrace inside the wall
    for x in range(1, 8):
        s.put('kanazawa-castle-wall_0_0', x, 7)
    s.put('kanazawa-castle-wall-corner-w_0_0', 0, 7)
    for y in (3, 4, 5, 6):
        s.put('kanazawa-castle-wall-v_0_0', 0, y)
    s.put('kanazawa-castle-gate_0_0', 8, 7)
    for x in range(12, 16):
        s.put('kanazawa-castle-wall_0_0', x, 7)
    s.put('kanazawa-castle-turret_0_0', 16, 7)
    s.put('kanazawa-castle-wall_0_0', 20, 7); s.put('kanazawa-castle-wall-corner-e_0_0', 21, 7)
    for y in (8, 9):
        s.put('kanazawa-castle-wall-v_0_0', 4, y)
    s.put('kanazawa-castle-wall-end_0_0', 4, 10)
    s.put('sendai-maple_0_0', 12, 9); s.put('hokuriku-ginkgo_0_0', 6, 9); s.put('kenrokuen-yukitsuri-small_0_0', 18, 9)
    s.put(me, 9, 8); s.put(me, 10, 7); s.put(me, 14, 10); s.put(me, 2, 10); s.put(me, 5, 9); s.put(me, 15, 3)
    s.save(f'{outdir}/kanazawa_art_castle.png')
    # Kenrokuen: moss, a gravel path, the pond with the Kotoji lantern, the tea house, the bridge, yukitsuri
    s = Scene(built, 22, 14, ground='garden-moss_0_0')
    s.floor('pond-autotile', (8, 3, 19, 6), (12, 7, 14, 9), (8, 7, 10, 9))
    s.floor('garden-path-autotile', (0, 10, 11, 11), (5, 2, 6, 9), (15, 10, 21, 11), (15, 12, 16, 13))
    s.flat('kenrokuen-bridge_0_0', 12, 10)
    s.put('kenrokuen-teahouse_0_0', 14, 4)
    s.put('kenrokuen-kotoji-water_0_0', 9, 8)                     # long leg in the pond, short on the bank
    s.put('kenrokuen-kotoji_0_0', 19, 9)                          # the dry one, on moss
    s.put('kenrokuen-yukitsuri_0_0', 1, 8); s.put('kenrokuen-yukitsuri-small_0_0', 7, 13)
    s.put('kenrokuen-yukitsuri-small_0_0', 16, 9); s.put('kenrokuen-yukitsuri_0_0', 18, 13)
    s.put('sendai-maple_0_0', 2, 13); s.put('hokuriku-ginkgo_0_0', 10, 13); s.put('sendai-maple_0_0', 20, 4)
    s.put('sendai-stone-lantern_0_0', 4, 12)
    s.put(me, 5, 6); s.put(me, 8, 10); s.put(me, 13, 10); s.put(me, 11, 11); s.put(me, 16, 12); s.put(me, 6, 11)
    s.save(f'{outdir}/kanazawa_art_kenrokuen.png')
    # Higashi Chaya: facing rows on the flagged lane, the gold-leaf shop and the phonograph museum, and
    # the temple hill behind: the stair, the gate, the hall
    s = Scene(built, 24, 16)
    s.floor('chaya-stone-autotile', (0, 8, 23, 10), (16, 5, 17, 7))
    s.floor('gravel-autotile', (14, 2, 23, 3))
    s.flat('teramachi-stair_0_0', 16, 4)
    for i, v in enumerate('abcab'):
        s.put(f'chaya-front-{v}_0_0', i * 3, 7)
    s.put('teramachi-gate_0_0', 15, 4)
    s.put('teramachi-hall_0_0', 18, 2)
    s.put('chaya-front-c_0_0', 18, 7); s.put('chaya-front-a_0_0', 21, 7)
    s.put('sendai-cedar_0_0', 14, 3); s.put('sendai-maple_0_0', 22, 5); s.put('sendai-stone-lantern_0_0', 17, 3)
    for i, v in enumerate('cb'):
        s.put(f'chaya-front-{v}_0_0', i * 3, 14)
    s.put('chaya-gold-leaf-shop_0_0', 6, 14)
    s.put('chaya-front-a_0_0', 10, 14); s.put('chaya-phono-museum_0_0', 13, 14)
    for i, v in enumerate('cba'):
        s.put(f'chaya-front-{v}_0_0', 16 + i * 3, 14)
    s.put(me, 4, 8); s.put(me, 7, 9); s.put(me, 12, 10); s.put(me, 16, 8); s.put(me, 17, 6); s.put(me, 14, 15)
    s.put(me, 20, 3)
    s.save(f'{outdir}/kanazawa_art_chaya.png')
    # Katamachi: a night street of small fronts on a paved lane off the road, andon posts between
    s = Scene(built, 20, 11)
    s.floor('light-concrete-autotile', (0, 6, 19, 6))
    s.road(7, 0, 19)
    s.put('katamachi-izakaya_0_0', 0, 5); s.put('katamachi-andon-lanterns_0_0', 4, 6)
    s.put('katamachi-whisky-bar_0_0', 5, 5)
    s.put('katamachi-yakitori_0_0', 8, 5); s.put('katamachi-andon-lanterns_0_0', 11, 6)
    s.put('katamachi-kissaten_0_0', 12, 5)
    s.put('katamachi-izakaya_0_0', 15, 5); s.put('katamachi-andon-lanterns_0_0', 19, 6)
    s.put(me, 1, 6); s.put(me, 6, 6); s.put(me, 9, 6); s.put(me, 13, 6); s.put(me, 15, 10); s.put(me, 3, 10)
    s.save(f'{outdir}/kanazawa_art_katamachi.png')
    # Nagamachi: a dirt lane between komo-hung walls, the canal, the samurai gate into a court and its house
    s = Scene(built, 22, 19)
    s.floor('dirt-outside-autotile', (0, 4, 21, 5), (9, 9, 10, 15), (17, 0, 18, 3), (5, 16, 14, 17))
    s.fill('nagamachi-canal-n_0_0', 0, 6, 21, 6); s.fill('nagamachi-canal-s_0_0', 0, 7, 21, 7)
    s.flat('kanazawa-canal-bridge_0_0', 9, 5)
    for x in range(0, 16):
        s.put('nagamachi-wall-bare_0_0' if x in (3, 11) else 'nagamachi-wall_0_0', x, 3)
    s.put('nagamachi-wall-corner-e_0_0', 16, 3)
    for y in (0, 1, 2):
        s.put('nagamachi-wall-v_0_0', 16, y)
    s.put('nagamachi-wall-corner-w_0_0', 19, 3)
    s.put('nagamachi-wall_0_0', 20, 3); s.put('nagamachi-wall_0_0', 21, 3)
    for y in (0, 1, 2):
        s.put('nagamachi-wall-v_0_0', 19, y)
    for x in range(0, 7):
        s.put('nagamachi-wall-gate_0_0' if x == 3 else 'nagamachi-wall_0_0', x, 11)
    s.put('nagamachi-samurai-gate_0_0', 7, 11)
    for x in range(12, 22):
        s.put('nagamachi-wall_0_0', x, 11)
    for y in (12, 13, 14):
        s.put('nagamachi-wall-v_0_0', 16, y)
    s.put('nagamachi-wall-end_0_0', 16, 15)
    s.put('nagamachi-samurai-house_0_0', 7, 15)                   # the house the gate leads to
    s.put('sendai-pine_0_0', 1, 15); s.put('kenrokuen-yukitsuri-small_0_0', 13, 17)
    s.put('sendai-maple_0_0', 18, 17)
    s.put(me, 4, 4); s.put(me, 9, 5); s.put(me, 13, 5); s.put(me, 9, 12); s.put(me, 17, 2); s.put(me, 3, 12)
    s.put(me, 11, 16)
    s.save(f'{outdir}/kanazawa_art_nagamachi.png')


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
