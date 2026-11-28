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
  chaya-front-a / -b / -c_0_0   3x4  two-storey teahouse fronts in bengara under
                                     the pack's kawara, lattice over dark glass;
                                     they tile along a street
  chaya-gold-leaf-shop_0_0      4x4  the gold-leaf shop: a gilded upper wall, a
                                     gold-leaf soft-serve sign
  chaya-phono-museum_0_0        3x4  the phonograph museum: a flat roof seen from
                                     above, a stone front under a horn-gramophone
                                     roundel
  chaya-stone-autotile_*        1x1  the stone-flagged lane: big low-contrast
                                     flags (9 autotile roles)
  teramachi-stair_0_0           2x3  the temple hill's stone stair (flat, walked
                                     ON; tiles north-south)
  teramachi-gate_0_0            3x3  a small mossy-shingled temple gate; walk through
  teramachi-hall_0_0            5x4  a temple hall: smoked-tile hip roof, a
                                     gabled porch, shoji bays, steps
Katamachi
  katamachi-whisky-bar_0_0      3x5  a narrow dark-brick whisky bar, its roof
                                     seen from above
  katamachi-izakaya_0_0         4x4  an all-you-can-drink izakaya
  katamachi-kissaten_0_0        3x4  a Showa coffee shop: brown tile, striped awning
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
Needs Pillow, and five sibling tools on the import path, so run it from where
it lives (it cannot be copied out alone): it imports the palette and helpers
of tools/generate_hokkaido.py, generate_sendai_art.py,
generate_sapporo_art.py, generate_hokuriku_art.py and house_look.py
(importing them draws nothing). The ten building fronts of Higashi Chaya,
Katamachi and Nagamachi are drawn in the house look (#290; see "the house
look" below), and so are Kenrokuen's garden pieces (#386). Plain python3 here has no Pillow;
/Library/Developer/CommandLineTools/usr/bin/python3 does. Run from gamev2/:
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
from generate_sendai_art import (roof_tile, pane, speck, foliage, SLATE, SLATE_HI, SLATE_LO, NEEDLE, P_SHADE,
                                 P_BARK, P_BARK_HI, P_BARK_LO, MAPLE, MAPLE_OR, LACQUER, LACQUER_HI, LACQUER_LO)
from generate_sapporo_art import FONT as _FONT, KANA as _KANA, glyphs
from generate_hokuriku_art import kawara, bars
import house_look as hl

SPR = 'assets/sprites'
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')

# ---- Kanazawa's colours ---------------------------------------------------------
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


# ---- the castle's colours: every one a GuttyKreum sheet colour ---------------------------
# lead tiles in roof_tile's order: course line, joint, lit lip, shade, base
C_LEAD = [rgb(c) for c in ('575f79', '848295', 'd1e2eb', '949bb2', 'a4b0b5')]
C_LEAD_LIT = [rgb(c) for c in ('646e86', '949bb2', 'fafcfd', 'a4b0b5', 'bcc7cc')]      # a fall facing west
C_LEAD_SH = [rgb(c) for c in ('47485d', '575f79', '949bb2', '646e86', '848295')]       # a fall facing east
C_RIDGE, C_RIDGE_HI, C_EAVE, C_EAVE_DK = rgb('a4b0b5'), rgb('dae2e4'), rgb('646e86'), rgb('47485d')
LEAD_PAL = (C_LEAD, C_LEAD_LIT, C_LEAD_SH, C_RIDGE, C_RIDGE_HI, C_EAVE, C_EAVE_DK)
C_PL, C_PL_LO, C_PL_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('be9e8c')    # white plaster, its shade, an eave's shadow on it
C_NK, C_NK_LO = rgb('47485d'), rgb('2a2636')                            # namako slate
C_DARK, C_DARK_LO = rgb('2c2d51'), rgb('2a3151')                        # an opening: never lit
C_ST = [rgb(c) for c in ('bcc7cc', 'a4b0b5', 'd1e2eb', 'bcc7cc', 'e4cecc', 'a4b0b5', '949bb2')]   # Tomuro stone, the odd red and blue block
C_ST_HI, C_ST_LO, C_ST_JOINT, C_ST_DK = rgb('fafcfd'), rgb('949bb2'), rgb('848295'), rgb('646e86')
C_TB, C_TB_HI, C_TB_LO, C_TB_DK = rgb('71412a'), rgb('aa775f'), rgb('5a3827'), rgb('3f210f')
C_IRON, C_IRON_HI, C_SOFFIT = rgb('2a2636'), rgb('848295'), rgb('191c2a')
C_GILT, C_GILT_HI = rgb('c6a663'), rgb('f3d890')


def rect(im, x0, y0, x1, y1, c):
    hl.fill(im, (x0, y0, x1, y1), c)


def lead_band(im, x0, y0, x1, y1, ridge=3):
    """A straight band of lead tiles: a ridge course of `ridge` rows, the tiles, a dark eave of two."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = roof_tile(x, y - y0 - ridge, C_LEAD)
    rect(im, x0, y0, x1, y0 + ridge - 1, C_RIDGE)
    rect(im, x0, y0, x1, y0, C_RIDGE_HI)
    rect(im, x0, y0 + ridge - 1, x1, y0 + ridge - 1, C_EAVE)
    rect(im, x0, y1 - 1, x1, y1 - 1, C_EAVE)
    rect(im, x0, y1, x1, y1, C_EAVE_DK)


def lead_hip(im, x0, x1, top, eave, run, side_rows, caps=True, pal=None):
    """A hipped lead roof seen from above. The ridge bar is the 4 rows above `top`,
    `run` in from either end; the front slope falls from `top` to `eave` between two
    hips that reach the eave's corners; outside them the hip ends (the west lit, the
    east in shade, their tiles running down them) widen to the full width in
    `side_rows` rows; an eave lip of 3 rows lies under `eave`. `pal` is another
    roof's tones in LEAD_PAL's order (Kenrokuen's tea house is shingled, #386)."""
    C_LEAD, C_LEAD_LIT, C_LEAD_SH, C_RIDGE, C_RIDGE_HI, C_EAVE, C_EAVE_DK = pal or LEAD_PAL
    px = im.load()
    n = eave - top
    for y in range(top, eave + 1):
        hip = (y - top) * run // n
        side = min(run, (y - top) * run // side_rows)
        hw, he, ow, oe = x0 + run - hip, x1 - run + hip, x0 + run - side, x1 - run + side
        for x in range(ow, oe + 1):
            if x < hw - 1:
                c = roof_tile(y - top, x - ow, C_LEAD_LIT)
            elif x > he + 1:
                c = roof_tile(y - top, oe - x, C_LEAD_SH)
            elif x <= hw + 1:
                c = C_LEAD_LIT[2] if x <= hw else C_LEAD[0]            # the west hip's cap, lit
            elif x >= he - 1:
                c = C_LEAD[2] if x == he - 1 else (C_LEAD_SH[0] if x == he + 1 else C_LEAD_SH[1])
            else:
                c = roof_tile(x, y - top, C_LEAD)
                if x > he - 9 and c == C_LEAD[4]:
                    c = C_LEAD[3]                                      # the slope's east end turns from the light
            px[x, y] = c
    rect(im, x0, eave + 1, x1, eave + 1, C_LEAD[2])
    rect(im, x0, eave + 2, x1, eave + 2, C_EAVE)
    rect(im, x0, eave + 3, x1, eave + 3, C_EAVE_DK)
    a, b = x0 + run - 2, x1 - run + 2
    rect(im, a, top - 4, b, top - 1, C_RIDGE)
    rect(im, a, top - 4, b, top - 4, C_RIDGE_HI)
    rect(im, a, top - 1, b, top - 1, C_LEAD[0])
    for x in range(a + 3, b - 1, 6):
        rect(im, x, top - 3, x, top - 2, C_LEAD[1])
    if caps:                                                           # an end tile either end of the ridge
        for cx in (a - 4, b - 1):
            rect(im, cx, top - 6, cx + 5, top, C_LEAD[4])
            rect(im, cx, top - 6, cx, top, C_LEAD_LIT[2])
            rect(im, cx + 1, top - 6, cx + 5, top - 6, C_LEAD_LIT[2])
            rect(im, cx + 5, top - 5, cx + 5, top, C_EAVE)


def plaster(im, x0, y0, x1, y1, east=6):
    """White plaster: the eave's shadow along its top (one row, a lighter row, a dithered
    row), its `east` end columns turned from the light."""
    rect(im, x0, y0, x1, y1, C_PL)
    rect(im, x1 - east + 1, y0, x1, y1, C_PL_LO)
    rect(im, x0, y0, x1, y0, C_PL_SH)
    rect(im, x0, y0 + 1, x1, y0 + 1, C_PL_LO)
    px = im.load()
    for x in range(x0, x1 - east + 1):
        if (x + y0) % 2:
            px[x, y0 + 2] = C_PL_LO


def musha(im, x0, y0, x1, y1):
    """A musha-mado: a dark opening behind stout plaster bars. No glass, so no glare, and never lit."""
    rect(im, x0 - 1, y0 - 1, x1 + 1, y1 + 1, C_PL_SH)
    rect(im, x0, y0, x1, y1, C_DARK)
    rect(im, x0, y0, x1, y0, C_DARK_LO)
    for x in range(x0 + 2, x1, 4):
        rect(im, x, y0, x, y1, C_PL)
        rect(im, x, y0, x, y0, C_PL_LO)
    rect(im, x0 - 1, y1 + 1, x1 + 1, y1 + 1, C_PL)                     # the sill, lit


def namako(im, x0, y0, x1, y1, shade_from=None):
    """Namako-kabe: slate tiles set on the diagonal, their joints raised in white
    plaster (period 8 in x), each joint's shadow on the tile below and east of it."""
    px = im.load()
    for y in range(y0, y1 + 1):
        v = y - y0
        for x in range(x0, x1 + 1):
            a, b = (x + v) % 8, (x - v) % 8
            if v == 0 or y == y1 or a == 0 or b == 0:
                c = C_PL_LO if y == y1 or (shade_from is not None and x >= shade_from) else C_PL
            else:
                c = C_NK_LO if a == 7 or b == 1 else C_NK
            px[x, y] = c


def stonework(im, x0, y0, x1, y1, seed=0, ch=8):
    """Kanazawa Castle's fitted Tomuro stone in courses of `ch`: pale grey with the odd
    red and blue block, each block lit along its top, its joints below and to the east.
    Period 32 in x, so runs of wall tile."""
    px = im.load()
    for y in range(y0, y1 + 1):
        j, yy = (y - y0) // ch, (y - y0) % ch
        off = (j * 13 + seed * 7) % 32
        for x in range(x0, x1 + 1):
            u = (x - off) % 32
            seg = 2 if u >= 21 else (1 if u >= 11 else 0)
            if u in (0, 11, 21) or yy == ch - 1:
                c = C_ST_JOINT
            elif yy == 0:
                c = C_ST_HI
            elif u in (10, 20, 31):
                c = C_ST_LO
            else:
                c = C_ST[(seg * 3 + j * 5 + ((x - off) // 32) * 2 + seed) % 7]
            px[x, y] = c


def sill_beam(im, x0, y0, x1, y1):
    rect(im, x0, y0, x1, y1, C_TB_LO)
    rect(im, x0, y0, x1, y0, C_TB_HI)
    rect(im, x0, y1, x1, y1, C_TB_DK)


def iron_post(im, x0, y0, x1, y1, bands):
    rect(im, x0, y0, x1, y1, C_TB)
    rect(im, x0, y0, x0, y1, C_TB_HI)
    rect(im, x1 - 1, y0, x1, y1, C_TB_LO)
    for y in bands:
        rect(im, x0, y, x1, y + 2, C_IRON)
        rect(im, x0 + 2, y + 1, x0 + 2, y + 1, C_IRON_HI)
        rect(im, x1 - 2, y + 1, x1 - 2, y + 1, C_IRON_HI)


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


def barred(d, x0, y0, x1, y1, frame=PLASTER_LO):
    """A musha-mado: a dark opening behind stout white bars."""
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=frame)
    d.rectangle([x0, y0, x1, y1], fill=SOOT)
    for x in range(x0 + 2, x1, 4):
        d.line([(x, y0), (x, y1)], fill=PLASTER)
    d.line([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], fill=PLASTER_SH)


def paper_lantern(d, x, y, w=7, h=12, mark=RED):
    """A white paper lantern with a mark, on its hook."""
    d.rectangle([x + 2, y, x + w - 3, y + 1], fill=SOOT)
    d.rectangle([x, y + 2, x + w - 1, y + h - 3], fill=PAPER)
    d.line([(x, y + 2), (x, y + h - 3)], fill=WHITE)
    d.line([(x + w - 1, y + 2), (x + w - 1, y + h - 3)], fill=PAPER_LO)
    d.rectangle([x + 2, y + 4, x + w - 3, y + h - 5], fill=mark)
    d.rectangle([x + 1, y + h - 2, x + w - 2, y + h - 1], fill=SOOT)


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


# ---- the Tsuzumi-mon's timber: sheet colours ----------------------------------------------
TS, TS_HI, TS_LO, TS_DK = rgb('ab7656'), rgb('c18e75'), rgb('904a37'), rgb('5a3827')
TS_COFFER, TS_COFFER_DK = rgb('4d3326'), rgb('312522')


def drum_pillar(im, cx, y0, y1):
    """One drum of the Tsuzumi-mon: two families of leaning timbers that cross,
    narrow at the waist, as the cords of a hand drum do."""
    px = im.load()
    mid, half = (y0 + y1) / 2, (y1 - y0) / 2

    def hw(y):
        return 6.5 + 9.5 * ((y - mid) / half) ** 2

    for y in range(y0, y1 + 1):
        w = round(hw(y))
        rect(im, cx - w, y, cx + w, y, TS_DK)
        rect(im, cx - w, y, cx - w, y, TS_HI)
        rect(im, cx + w, y, cx + w, y, TS_COFFER)
    for dirn in (1, -1):
        for k in range(9):
            th0 = 2 * math.pi * k / 9 + (0.2 if dirn < 0 else 0)
            for y in range(y0, y1 + 1):
                th = th0 + dirn * (y - y0) / (y1 - y0) * math.pi * 0.95
                if math.cos(th) <= 0.08:
                    continue                                       # round the back
                s = math.sin(th)
                x = round(cx + (hw(y) - 0.5) * s)
                px[x, y] = TS_HI if s < -0.35 else (TS if s < 0.45 else TS_LO)
                if abs(s) < 0.8:
                    px[x + dirn, y] = TS_LO if s > 0.2 else TS
    rect(im, cx - 17, y0 - 4, cx + 17, y0 - 1, TS_LO)              # the collar under the roof
    rect(im, cx - 17, y0 - 4, cx + 17, y0 - 4, TS_DK)
    rect(im, cx - 17, y0 - 3, cx + 10, y0 - 3, TS)
    rect(im, cx - 18, y1 + 1, cx + 18, y1 + 5, C_ST[1])            # the stone plinth
    rect(im, cx - 18, y1 + 1, cx + 18, y1 + 1, C_ST_HI)
    rect(im, cx - 18, y1 + 2, cx - 18, y1 + 5, C_ST[2])
    rect(im, cx - 18, y1 + 4, cx + 18, y1 + 5, C_ST_JOINT)
    rect(im, cx + 13, y1 + 2, cx + 18, y1 + 5, C_ST_JOINT)


def tsuzumi_gate():
    im, d = canvas(6, 5)                 # 192 x 160; pillars stand in columns 1 and 4
    px = im.load()
    # ---- the roof, seen from above: one flat slab of crossed timbers over dark coffers, 8px a bay
    x0, x1, y0, y1 = 3, 188, 4, 47
    rect(im, x0, y0, x1, y1, TS)
    for y in range(y0 + 2, y1 - 1):
        for x in range(x0 + 2, x1 - 1):
            u, v = (x - x0 - 2) % 8, (y - y0 - 2) % 8
            if u < 6 and v < 6:                                    # a coffer: the beams' shadow on its top row and west column
                c = TS_COFFER_DK if u == 0 or v == 0 else TS_COFFER
            elif (u == 6 and v < 6) or (v == 6 and u < 6):
                c = TS_HI                                          # a beam's lit edge
            elif (u == 7 and v < 6) or (v == 7 and u < 6):
                c = TS_LO                                          # and its far one
            else:
                c = TS
            px[x, y] = c
    rect(im, x0, y0, x1, y0, TS_HI); rect(im, x0, y0, x0, y1, TS_HI)
    rect(im, x1 - 1, y0 + 1, x1, y1, TS_LO)
    # ---- its front edge: the fascia, a beam end at every bay; the underside in shade
    rect(im, x0, 48, x1, 56, TS)
    rect(im, x0, 48, x1, 48, TS_DK); rect(im, x0, 49, x1, 49, TS_HI)
    rect(im, x0, 55, x1, 56, TS_LO)
    rect(im, 184, 49, 188, 56, TS_LO)
    for x in range(x0 + 8, x1 - 4, 8):
        rect(im, x, 51, x + 1, 54, TS_LO)
        rect(im, x, 51, x + 1, 51, TS_DK)
    rect(im, 8, 57, 183, 58, TS_DK)
    drum_pillar(im, 48, 63, 150)
    drum_pillar(im, 144, 63, 150)
    hl.outline(im)
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
    # ---- the stone piers, flush to the canvas so the wall joins them
    stonework(im, 0, 78, 33, 127, 1)
    stonework(im, 94, 78, 127, 127, 4)
    rect(im, 29, 78, 33, 127, C_ST_JOINT); rect(im, 29, 78, 29, 127, C_ST_LO)      # the west pier's reveal, in shade
    rect(im, 94, 78, 95, 127, C_ST_HI)                                             # the east pier's, lit
    rect(im, 0, 78, 33, 78, C_ST_DK); rect(im, 94, 78, 127, 78, C_ST_DK)           # the gatehouse's shadow
    # ---- the gatehouse: white plaster, barred openings, a namako dado, the sill beam on the stone
    plaster(im, 3, 44, 124, 62, east=8)
    musha(im, 12, 50, 31, 58); musha(im, 46, 50, 81, 58); musha(im, 96, 50, 115, 58)
    namako(im, 3, 63, 124, 73, shade_from=117)
    sill_beam(im, 2, 74, 125, 77)
    lead_hip(im, 1, 126, 12, 39, 24, 9)
    # ---- the gateway: a lintel with the plum crest, iron-bound posts, the leaves folded back
    rect(im, 34, 78, 93, 87, C_TB)
    rect(im, 34, 78, 93, 78, C_TB_DK); rect(im, 34, 79, 93, 79, C_TB_HI); rect(im, 34, 86, 93, 87, C_TB_LO)
    for x in range(40, 90, 8):
        if x != 64:
            rect(im, x, 82, x + 1, 84, C_IRON); rect(im, x, 82, x, 82, C_IRON_HI)
    for x, y in ((64, 80), (62, 82), (66, 82), (63, 84), (65, 84)):
        rect(im, x, y, x, y, C_GILT)
    rect(im, 64, 82, 64, 82, C_GILT_HI)
    iron_post(im, 34, 88, 41, 127, (94, 108, 121))
    iron_post(im, 86, 88, 93, 127, (94, 108, 121))
    for x0 in (42, 80):
        rect(im, x0, 88, x0 + 5, 126, C_TB_DK)
        rect(im, x0 + 2, 90, x0 + 2, 125, C_TB_LO)
        for y in range(92, 124, 6):
            rect(im, x0 + 4, y, x0 + 4, y, C_IRON_HI)
    rect(im, 48, 88, 79, 92, C_SOFFIT)                                             # the passage's ceiling: opaque
    rect(im, 48, 88, 79, 88, C_IRON)
    hl.outline(im)
    return im


def castle_turret():
    im, d = canvas(4, 5)                 # 128 x 160
    px = im.load()
    # ---- the battered stone base
    stonework(im, 2, 118, 125, 157, 2)
    for y in range(118, 158):
        inset = 9 * (157 - y) // 39
        for x in list(range(2, 2 + inset)) + list(range(126 - inset, 126)):
            px[x, y] = CLEAR
        px[2 + inset, y] = C_ST_HI
        for x in range(119 - inset, 126 - inset):                                  # the east arris, turned from the light
            if px[x, y] != C_ST_JOINT:
                px[x, y] = C_ST[1] if px[x, y] == C_ST_HI else C_ST_LO
    rect(im, 2, 158, 125, 159, C_ST_JOINT)
    rect(im, 11, 118, 116, 118, C_ST_DK)
    # ---- the first storey, its bay window
    plaster(im, 13, 79, 114, 101, east=8)
    musha(im, 20, 88, 39, 96); musha(im, 88, 88, 107, 96)
    namako(im, 13, 102, 114, 112, shade_from=107)
    sill_beam(im, 12, 113, 115, 117)
    rect(im, 46, 89, 81, 112, C_PL); rect(im, 79, 89, 81, 112, C_PL_LO)
    rect(im, 46, 89, 81, 89, C_PL_SH); rect(im, 46, 90, 81, 90, C_PL_LO)
    musha(im, 51, 94, 76, 104)
    rect(im, 46, 109, 81, 112, C_PL_LO); rect(im, 46, 112, 81, 112, C_PL_SH)
    rect(im, 82, 90, 83, 112, C_PL_SH)                                             # the bay's shadow on the wall
    # ---- the lower roof, a skirt round the second storey; the bay's bowed hood breaks through its eave
    lead_hip(im, 2, 125, 66, 74, 18, 4, caps=False)
    for i, (xa, xb) in enumerate(((57, 70), (51, 76), (47, 80), (44, 83)) + ((43, 84),) * 6):
        for x in range(xa, xb + 1):
            lit = i == 0 or (i < 4 and x <= xa + 1)
            px[x, 79 + i] = C_LEAD_LIT[2] if lit else (
                C_LEAD[1] if (x - 43) % 6 == 3 else (C_LEAD[3] if x > 76 else C_LEAD[4]))
    rect(im, 43, 87, 84, 87, C_EAVE); rect(im, 43, 88, 84, 88, C_EAVE_DK)
    # ---- the second storey
    plaster(im, 27, 42, 100, 65, east=7)
    musha(im, 35, 49, 50, 57); musha(im, 56, 49, 71, 57); musha(im, 77, 49, 92, 57)
    rect(im, 27, 62, 93, 65, C_PL_LO); rect(im, 94, 62, 100, 65, C_PL_SH)
    # ---- the top roof, a plastered gable in its front slope: stepped rows
    lead_hip(im, 11, 116, 13, 37, 30, 9)
    for i in range(15):
        y, w = 22 + i, i + 2
        rect(im, 64 - w, y, 63 + w, y, C_LEAD[0] if i < 2 else C_PL)
        rect(im, 64 - w, y, 65 - w, y, C_LEAD_LIT[2])
        rect(im, 62 + w, y, 63 + w, y, C_LEAD_SH[0])
        if i >= 2:
            rect(im, 66 - w, y, 66 - w, y, C_PL_SH)
    rect(im, 47, 37, 80, 37, C_LEAD[0])
    rect(im, 62, 30, 65, 35, C_DARK); rect(im, 62, 30, 65, 30, C_DARK_LO)
    hl.outline(im)
    return im


def castle_storehouse():
    im, d = canvas(6, 3)                 # 192 x 96; the door is column 2 (x 64-95)
    stonework(im, 2, 78, 189, 95, 5)
    rect(im, 182, 78, 189, 95, C_ST_LO)
    rect(im, 182, 86, 189, 86, C_ST_JOINT)
    rect(im, 2, 78, 189, 78, C_ST_DK)
    plaster(im, 4, 36, 187, 59, east=8)
    for x0 in (12, 38, 106, 132, 158):
        musha(im, x0, 46, x0 + 19, 54)
    namako(im, 4, 60, 187, 70, shade_from=180)
    rect(im, 4, 71, 187, 73, C_PL_LO)
    sill_beam(im, 3, 74, 188, 77)
    # ---- the door: iron-bound leaves under a little lead hood
    rect(im, 65, 52, 94, 95, C_TB_DK)
    rect(im, 67, 55, 92, 95, C_TB)
    rect(im, 67, 55, 67, 95, C_TB_HI); rect(im, 79, 55, 79, 95, C_TB_DK); rect(im, 80, 55, 80, 95, C_TB_HI)
    rect(im, 91, 55, 92, 95, C_TB_LO)
    for y in (61, 75, 88):
        rect(im, 67, y, 92, y + 2, C_IRON)
        for x in (70, 76, 83, 89):
            rect(im, x, y + 1, x, y + 1, C_IRON_HI)
    lead_band(im, 61, 44, 98, 51, ridge=2)
    rect(im, 62, 52, 97, 52, C_PL_SH)
    lead_hip(im, 1, 190, 9, 31, 18, 8)
    hl.outline(im)
    return im


# ---- walls: the castle's white one and Nagamachi's ochre one, as one family each ----
def _lead_fall(im, x0, x1, y0, y1, tones, lit, clip=None):
    """One fall of a north-south coping: lead tiles whose courses run down the map."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if clip is None or clip(x):
                px[x, y] = roof_tile(y, (x1 - x) if lit else (x - x0), tones)


def _lead_v_coping(im, y0, y1):
    _lead_fall(im, 3, 14, y0, y1, C_LEAD_LIT, True)
    _lead_fall(im, 17, 28, y0, y1, C_LEAD_SH, False)
    rect(im, 2, y0, 2, y1, C_LEAD_LIT[2])
    rect(im, 29, y0, 29, y1, C_EAVE_DK)
    rect(im, 15, y0, 15, y1, C_LEAD_LIT[2])
    rect(im, 16, y0, 16, y1, C_EAVE)


def castle_wall(kind):
    """One piece of the castle's wall, 1x2 cells: wall()'s kinds h, v, end, corner-e
    and corner-w, on its rows, in lead, white plaster, namako and Tomuro stone."""
    im, d = canvas(1, 2)
    px = im.load()

    def coping(x0, x1):
        lead_band(im, x0, 12, x1, 24)
        rect(im, x0, 25, x1, 25, C_PL_SH)

    def face(x0, x1):
        rect(im, x0, 26, x1, 35, C_PL)
        rect(im, x0, 26, x1, 26, C_PL_LO)
        namako(im, x0, 36, x1, 47)
        rect(im, x0, 48, x1, 48, C_ST_DK)
        stonework(im, x0, 49, x1, 63)

    def end_face():
        rect(im, 5, 32, 26, 39, C_PL)
        rect(im, 24, 32, 26, 39, C_PL_LO)
        rect(im, 5, 32, 26, 32, C_PL_SH); rect(im, 5, 33, 26, 33, C_PL_LO)
        namako(im, 5, 40, 26, 49, shade_from=24)
        rect(im, 5, 50, 26, 50, C_ST_DK)
        stonework(im, 5, 51, 26, 63, 3)
        rect(im, 5, 51, 5, 63, C_ST_HI); rect(im, 26, 51, 26, 63, C_ST_JOINT)

    if kind == 'h':
        coping(0, 31); face(0, 31)
    elif kind in ('v', 'end'):
        _lead_v_coping(im, 0, 31)
        if kind == 'end':                                          # the coping's hipped south end
            for y in range(18, 30):
                t = y - 18
                for x in range(max(3, 15 - t), min(28, 16 + t) + 1):
                    px[x, y] = roof_tile(x, t, C_LEAD)
                if 15 - t >= 3:
                    px[15 - t, y] = C_LEAD_LIT[2]; px[16 + t, y] = C_EAVE
            rect(im, 2, 30, 29, 30, C_EAVE); rect(im, 2, 31, 29, 31, C_EAVE_DK)
        end_face()
    else:
        east = kind == 'corner-e'
        fx0, fx1 = (0, 27) if east else (4, 31)
        coping(0 if east else 2, 29 if east else 31)
        face(fx0, fx1)
        _lead_v_coping(im, 0, 11)
        rect(im, 15, 12, 15, 14, C_LEAD_LIT[2]); rect(im, 16, 12, 16, 14, C_EAVE)
        for y in range(12, 26):                                    # the hip between the two roofs
            reach = y - 12
            if east:
                _lead_fall(im, 17, 28, y, y, C_LEAD_SH, False, clip=lambda x, r=reach: x > 16 + r)
                px[29, y] = C_EAVE_DK
                if reach:
                    px[16 + reach, y] = C_LEAD_LIT[2]
            else:
                _lead_fall(im, 3, 14, y, y, C_LEAD_LIT, True, clip=lambda x, r=reach: x < 15 - r)
                px[2, y] = C_LEAD_LIT[2]
                if reach:
                    px[15 - reach, y] = C_EAVE
        for i, y in enumerate(range(26, 62, 6)):                   # the corner's long-and-short stones
            w = 7 if i % 2 else 4
            xa, xb = (fx1 - w, fx1) if east else (fx0, fx0 + w)
            rect(im, xa, y, xb, y + 5, C_ST[(i * 2 + (0 if east else 3)) % 7])
            rect(im, xa, y, xb, y, C_ST_HI)
            rect(im, xa, y + 5, xb, y + 5, C_ST_JOINT)
            if east:
                rect(im, xb - 1, y + 1, xb, y + 5, C_ST_JOINT)
                rect(im, xa, y + 1, xa, y + 4, C_ST_LO)
            else:
                rect(im, xa, y, xa, y + 5, C_ST_HI)
                rect(im, xb, y + 1, xb, y + 4, C_ST_LO)
        rect(im, fx1 - 6 if east else fx0, 62, fx1 if east else fx0 + 6, 63, C_ST_JOINT)
    hl.outline(im)
    return im


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
    wall's south end (earth between posts on river stones). Stacked down the map each piece's coping covers the end of
    the one north of it, so a run is one roof with a wall face and foot under
    its last piece. `end` is the same with the coping hipped, to finish a run.
    `corner-e` / `corner-w` are the ends of an east-west run where the wall
    turns north: the face stops at corner stones (a post), the coping turns up
    the map over a hip, and `v` goes in the cells above. Each corner is drawn
    for its own side: light comes from the west."""
    coping = _naga_coping
    pal = SHINGLE_P
    light, dark, hi, deep = pal
    top = 15

    def face(d, x0, x1):
        _naga_face(d, x0, x1, komo=(style == 'komo'))

    def end_face(d):                                             # the south end of a north-south wall
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
        if east:                                                 # a corner post, in shade
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
# ---- the garden's colours: every one a GuttyKreum sheet colour -------------------------------
G_ST_HI, G_ST_LT, G_ST, G_ST_MD = rgb('fafcfd'), rgb('dae2e4'), rgb('bcc7cc'), rgb('a4b0b5')   # granite
G_ST_LO, G_ST_DK, G_ST_DEEP = rgb('848295'), rgb('646e86'), rgb('47485d')
G_LICHEN, G_LICHEN_LO, G_LICHEN_DK = rgb('83af6f'), rgb('678e57'), rgb('506b6b')
G_ROPE, G_ROPE_HI, G_ROPE_LO, G_ROPE_DK = rgb('c6a663'), rgb('f3d890'), rgb('a7843b'), rgb('86624f')
G_RING = rgb('8ec2fa')                                           # pond-autotile's own highlight
# cedar-bark shingles in roof_tile's order (course line, joint, lit lip, shade, base), then a
# fall facing west and one facing east; ridge, its lit row, the eave and its dark row
G_SHINGLE = ([rgb(c) for c in ('594b45', '7c5d56', 'be9e8c', '8e7366', 'a68777')],
             [rgb(c) for c in ('6d574e', '8e7366', 'e4cecc', 'a68777', 'be9e8c')],
             [rgb(c) for c in ('3c3029', '594b45', '8e7366', '6d574e', '7c5d56')],
             rgb('8e7366'), rgb('be9e8c'), rgb('594b45'), rgb('3c3029'))
G_PAPER, G_PAPER_HI, G_PAPER_LO = rgb('e4cecc'), rgb('fafcfd'), rgb('be9e8c')
G_MOSS = [rgb(c) for c in ('357570', '488582', '6c8e7f', '2e4040')]     # floor, cushion, lit rim, shade
G_GRAVEL, G_GRAVEL_HI, G_GRAVEL_LO, G_GRAVEL_SH = rgb('d7d0ba'), rgb('eae9e8'), rgb('cdc8c5'), rgb('b3aaa0')


def spans(im, y0, rows, tones):
    """A stepped shape: one (x0, x1) a row from y0 down, each row `tones` =
    (lit left edge, base, shaded right edge) with the edge 1px and the shade 2."""
    lit, base, lo = tones
    for n, (x0, x1) in enumerate(rows):
        rect(im, x0, y0 + n, x1, y0 + n, base)
        rect(im, x0, y0 + n, x0, y0 + n, lit)
        rect(im, max(x0 + 1, x1 - 1), y0 + n, x1, y0 + n, lo)


def lerp_rows(knots):
    """(y, x) for every row of a stepped line through (x, y) knots, whole numbers only."""
    out = []
    for (xa, ya), (xb, yb) in zip(knots, knots[1:]):
        for y in range(ya, yb + (1 if (xb, yb) == knots[-1] else 0)):
            out.append((y, xa + (xb - xa) * (y - ya) // (yb - ya)))
    return out


def cast(im, y0, rows):
    """The shadow on the ground or the water: P_SHADE on the pixels still clear
    (so it goes on after the outline, and is not inked)."""
    px = im.load()
    for n, (x0, x1) in enumerate(rows):
        for x in range(max(0, x0), min(im.width - 1, x1) + 1):
            if px[x, y0 + n][3] == 0:
                px[x, y0 + n] = P_SHADE


def dots(im, pts, c):
    px = im.load()
    for x, y in pts:
        px[x, y] = c


KOTOJI_ROOF = ((30, 34), (28, 36), (26, 38), (24, 40), (22, 42), (20, 44), (18, 46), (16, 48),      # y 10 on
               (14, 50), (13, 51), (12, 52), (9, 55), (9, 55), (9, 55))
KOTOJI_JEWEL = ((32, 32), (30, 34), (29, 35), (28, 36), (28, 36), (28, 36), (29, 35), (30, 34))     # y 1 on
STEP_STONE = ((8, 21), (5, 24), (4, 25), (3, 26), (3, 26), (3, 26), (4, 25), (5, 24), (8, 21))      # y 84 on
RING = ((9, 19), (5, 23), (3, 25), (2, 26), (2, 26), (2, 26), (2, 26), (2, 26), (3, 25), (5, 23), (9, 19))   # y 84 on


def kotoji(water=False):
    im, d = canvas(2, 3)                 # 64 x 96
    px = im.load()
    # ---- the rock on the bank the short leg stands on: three facets, moss up its foot
    left = dict(lerp_rows([(47, 66), (41, 70), (36, 80), (34, 94)]))
    right = dict(lerp_rows([(54, 66), (60, 74), (63, 84), (63, 94)]))
    for y in range(66, 94):
        l, r = left[y], right[y]
        for x in range(l, r + 1):
            t = (x - l) * 100 // (r - l + 1) + (y - 66)
            c = G_ST_LT if t < 30 else (G_ST_MD if t < 64 else G_ST_LO)
            top = 91 - speck(x // 2, 0, 2) % 4                    # moss up its foot, its upper edge ragged
            if y >= top:
                c = G_LICHEN if y == top else (G_LICHEN_DK if x > r - 6 or speck(x, y, 5) < 12 else G_LICHEN_LO)
            px[x, y] = c
        px[l, y] = G_ST_HI if y < 80 else px[l, y]
    for y, x in lerp_rows([(45, 76), (49, 85), (47, 93)]):        # a crack down it
        px[x, y] = G_ST_DK
    dots(im, ((42, 72), (45, 69), (50, 68), (38, 81), (58, 76)), G_LICHEN)
    dots(im, ((43, 72), (46, 69), (51, 68), (39, 81), (59, 76)), G_LICHEN_LO)
    # ---- what the long leg stands on: a low stone in the shallows (dry) or the pond itself
    if not water:
        spans(im, 84, STEP_STONE, (G_ST_LT, G_ST, G_ST_LO))
        rect(im, 8, 84, 21, 84, G_ST_HI)
        for n, (x0, x1) in enumerate(STEP_STONE[5:]):             # its side, in shade
            rect(im, x0, 89 + n, x1, 89 + n, G_ST_LO)
            rect(im, x0, 89 + n, x0 + 1, 89 + n, G_ST_MD)
        rect(im, 8, 92, 21, 92, G_ST_DK)
        spans(im, 88, ((25, 37), (23, 39), (22, 40), (22, 40), (23, 39), (26, 36)), (G_ST, G_ST_MD, G_ST_LO))
        rect(im, 23, 92, 39, 92, G_ST_LO); rect(im, 26, 93, 36, 93, G_ST_DK)
    # ---- the two legs, bowed: the long one to the stone, the short one to the rock
    for knots in ([(25, 46), (22, 58), (18, 71), (14, 89 if water else 87)], [(39, 46), (43, 54), (47, 61), (50, 68)]):
        for y, x in lerp_rows(knots):
            rect(im, x - 3, y, x + 2, y, G_ST)
            rect(im, x - 3, y, x - 3, y, G_ST_HI); rect(im, x - 2, y, x - 2, y, G_ST_LT)
            rect(im, x + 1, y, x + 2, y, G_ST_LO)
    if not water:
        rect(im, 9, 84, 19, 87, G_ST); rect(im, 9, 84, 19, 84, G_ST_HI); rect(im, 18, 85, 19, 87, G_ST_LO)   # its foot
    # ---- the platform, the light box (a window in dim gold: never lit), the roof, the jewel
    rect(im, 21, 38, 43, 40, G_ST_LO); rect(im, 21, 38, 43, 38, G_ST_MD); rect(im, 40, 38, 43, 40, G_ST_DK)
    rect(im, 18, 41, 46, 46, G_ST)
    rect(im, 18, 41, 46, 41, G_ST_HI); rect(im, 18, 42, 18, 46, G_ST_LT)
    rect(im, 42, 42, 46, 46, G_ST_MD); rect(im, 18, 45, 46, 46, G_ST_LO); rect(im, 42, 45, 46, 46, G_ST_DK)
    rect(im, 24, 27, 40, 37, G_ST)
    rect(im, 24, 27, 24, 37, G_ST_LT); rect(im, 37, 27, 40, 37, G_ST_MD); rect(im, 24, 27, 40, 27, G_ST_LO)
    rect(im, 27, 29, 35, 36, G_ST_DK)
    rect(im, 28, 30, 34, 35, G_ROPE); rect(im, 28, 30, 29, 31, G_ROPE_HI)
    rect(im, 31, 30, 31, 35, G_ST_DK); rect(im, 28, 33, 34, 33, G_ST_DK)
    for n, (x0, x1) in enumerate(KOTOJI_ROOF):                    # six-sided: a lit fall, the front, a shaded fall
        y = 10 + n
        a, b = 32 - n * 2 // 3 - 1, 32 + n * 2 // 3 + 1
        rect(im, x0, y, x1, y, G_ST)
        rect(im, x0, y, a, y, G_ST_LT); rect(im, b, y, x1, y, G_ST_MD)
        rect(im, a, y, a, y, G_ST_HI); rect(im, b, y, b, y, G_ST_LO)
        rect(im, x0, y, x0, y, G_ST_HI); rect(im, x1 - 1, y, x1, y, G_ST_LO)
    rect(im, 9, 24, 55, 24, G_ST_LO); rect(im, 9, 24, 22, 24, G_ST_MD)          # the eave's face
    rect(im, 11, 25, 53, 26, G_ST_DK); rect(im, 14, 26, 50, 26, G_ST_DEEP)      # under it
    dots(im, ((9, 20), (10, 20), (9, 19), (54, 20), (55, 20), (55, 19)), G_ST_MD)    # the corners turn up
    dots(im, ((9, 19), (9, 20)), G_ST_HI)
    dots(im, ((18, 20), (26, 16), (38, 17), (46, 21), (30, 13)), G_LICHEN)      # lichen on the roof
    dots(im, ((19, 21), (27, 17), (39, 18), (47, 22), (31, 14)), G_LICHEN_LO)
    spans(im, 1, KOTOJI_JEWEL, (G_ST_LT, G_ST, G_ST_LO))
    rect(im, 30, 9, 34, 9, G_ST_DK)
    dots(im, ((30, 3), (31, 3), (30, 4)), G_ST_HI)
    rect(im, 30, 7, 34, 8, G_ST_MD); rect(im, 33, 7, 34, 8, G_ST_LO)
    hl.outline(im)
    if water:                            # the leg goes down into the pond: cut at the waterline, its shadow, a ring
        for y in range(89, 96):
            for x in range(0, 30):
                px[x, y] = CLEAR
        rect(im, 10, 89, 17, 89, G_RING)                              # the water against the leg
        cast(im, 84, RING)
        for n, (x0, x1) in enumerate(RING):
            y = 84 + n
            ring = range(x0, x1 + 1) if n in (0, len(RING) - 1) else (
                [x for x in range(x0, x1 + 1) if x < RING[n - 1][0] or x > RING[n - 1][1]
                 or x < RING[n + 1][0] or x > RING[n + 1][1]])
            for x in ring:
                if px[x, y][3] != 255:
                    px[x, y] = G_RING
    else:
        cast(im, 93, ((6, 23), (9, 24)))
    return im


def g_rope(im, x0, y0, x1, y1, c, glint=None):
    """A rope from the pole's top to the rim, a pixel a step; `glint` lights two points on it."""
    px = im.load()
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for n in range(steps + 1):
        x, y = x0 + (x1 - x0) * n // steps, y0 + (y1 - y0) * n // steps
        px[x, y] = glint if glint and n in (steps // 6, steps // 3) else c


def yukitsuri(cw, ch, pads, n):
    def build():
        im, d = canvas(cw, ch)
        px = im.load()
        W, H = cw * 32, ch * 32
        cx = W // 2
        rim_y, rx, ry = H - 20, W // 2 - 3, 7 + cw
        ends = []                                                 # n rope ends round the rim: (x, y, in front)
        for k in range(n // 2):
            dx = -rx + (2 * k + 1) * rx * 2 // n
            dy = math.isqrt(ry * ry * (rx * rx - dx * dx)) // rx
            ends += [(cx + dx, rim_y - dy, False), (cx + dx, rim_y + dy, True)]
        for x, y, front in ends:                                  # the ropes round the back
            if not front:
                g_rope(im, cx, 5, x, y, G_ROPE_LO)
        # the trunk, leaning, and two boughs
        for knots, w in (([(cx - 3, H - 6), (cx - 5, H - 30), (cx + 2, H // 2), (cx + 5, min(p[1] for p in pads))], 5),):
            for y, x in lerp_rows(knots[::-1]):
                rect(im, x - 2, y, x + w - 3, y, P_BARK)
                rect(im, x - 2, y, x - 2, y, P_BARK_HI); rect(im, x + w - 4, y, x + w - 3, y, P_BARK_LO)
        for x0, y0, x1, y1 in ((cx - 5, H - 30, cx - rx + 12, H - 40), (cx, H - 34, cx + rx - 12, H - 44)):
            steps = abs(x1 - x0)
            for s in range(steps + 1):
                x, y = x0 + (x1 - x0) * s // steps, y0 + (y1 - y0) * s // steps
                rect(im, x, y, x, y + 1, P_BARK); rect(im, x, y + 2, x, y + 2, P_BARK_LO)
        rect(im, cx - 7, H - 8, cx + 1, H - 5, P_BARK_LO); rect(im, cx - 7, H - 8, cx - 4, H - 7, P_BARK)   # the root
        # the bamboo pole the ropes hang from
        rect(im, cx + 1, 6, cx + 2, H - 6, G_ROPE); rect(im, cx + 2, 6, cx + 2, H - 6, G_ROPE_LO)
        for y in range(18, H - 10, 14):
            rect(im, cx + 1, y, cx + 2, y, G_ROPE_DK)
        foliage(im, [(cx + ox, y, prx, pry) for ox, y, prx, pry in pads], NEEDLE, cw)   # the pads, back to front
        for x, y, front in ends:                                  # the ropes in front, a knot where each is pegged
            if front:
                g_rope(im, cx, 5, x, y, G_ROPE, G_ROPE_HI if abs(x - cx) * 4 < rx * 3 else None)
                px[x, y] = G_ROPE_DK
                px[x, y + 1] = G_ROPE_DK
        rect(im, cx - 2, 1, cx + 3, 7, G_ROPE)                    # the straw knot at the top
        rect(im, cx - 2, 1, cx - 2, 7, G_ROPE_HI); rect(im, cx + 3, 2, cx + 3, 7, G_ROPE_LO)
        rect(im, cx - 2, 5, cx + 3, 5, G_ROPE_DK)
        rect(im, cx, 0, cx + 1, 0, G_ROPE)
        hl.outline(im)
        cast(im, H - 13, [(cx - rx + 6 + i, cx + rx - 6 - i) for i in (6, 3, 1, 0, 0, 0, 0, 0, 1, 3, 6)])
        return im
    return build


def teahouse():
    im, d = canvas(4, 3)                 # 128 x 96; it stands on posts in the bottom row
    px = im.load()
    # ---- the posts in the water, each on a stone
    for x in (14, 46, 79, 111):
        rect(im, x, 76, x + 3, 90, C_TB)
        rect(im, x, 76, x, 90, C_TB_HI); rect(im, x + 3, 76, x + 3, 90, C_TB_DK)
        rect(im, x - 2, 89, x + 5, 93, G_ST_MD); rect(im, x - 2, 89, x + 5, 89, G_ST_LT)
        rect(im, x - 2, 93, x + 5, 93, G_ST_DK); rect(im, x + 4, 90, x + 5, 92, G_ST_LO)
    rect(im, 18, 79, 110, 80, C_TB_DK)                            # the tie under the floor
    for x in (14, 46, 79, 111):
        rect(im, x, 79, x, 80, C_TB_LO)
    # ---- the veranda: its boards from above, its edge, the shade under it
    rect(im, 6, 69, 121, 75, C_TB)
    rect(im, 6, 69, 121, 70, C_TB_HI); rect(im, 6, 69, 121, 69, G_PAPER_LO)
    rect(im, 6, 74, 121, 75, C_TB_DK); rect(im, 6, 73, 121, 73, C_TB_LO)
    for x in range(11, 120, 8):
        rect(im, x, 70, x, 72, C_TB_LO)
    # ---- the room: paper screens either side, the middle slid open on a dark room
    rect(im, 12, 37, 115, 68, C_TB)
    rect(im, 12, 37, 115, 39, C_TB_DK)                            # the eave's shadow
    rect(im, 12, 40, 115, 44, C_TB); rect(im, 12, 40, 115, 40, C_TB_LO); rect(im, 12, 44, 115, 44, C_TB_LO)
    for x0, x1 in ((15, 43), (84, 112)):
        rect(im, x0, 46, x1, 67, G_PAPER)
        for y in range(48, 68):                                   # the light falls across it on a slant
            rect(im, x0, y, x0 + 11 - (y - 48) // 2, y, G_PAPER_HI)
            rect(im, x1 - 3 - (y - 48) // 3, y, x1, y, G_PAPER_LO)
        rect(im, x0, 46, x1, 47, G_PAPER_LO)                      # the lintel's shade
        for x in range(x0 + 7, x1, 7):
            rect(im, x, 46, x, 67, C_TB_HI)
        for y in (54, 61):
            rect(im, x0, y, x1, y, C_TB_HI)
    rect(im, 47, 46, 80, 67, C_DARK)
    rect(im, 47, 46, 80, 48, C_DARK_LO)
    rect(im, 47, 60, 80, 67, G_PAPER_LO)                          # tatami
    rect(im, 47, 60, 80, 60, G_PAPER); rect(im, 63, 61, 63, 67, H_EARTH); rect(im, 47, 66, 80, 67, H_EARTH)
    rect(im, 68, 48, 76, 58, G_PAPER); rect(im, 70, 50, 74, 56, G_PAPER_LO)      # a hanging scroll
    rect(im, 72, 51, 72, 55, C_TB_DK)
    rect(im, 52, 55, 60, 59, C_TB_LO); rect(im, 52, 55, 60, 55, C_TB_HI)         # a low table, a tea bowl
    rect(im, 55, 52, 57, 54, G_LICHEN_DK); rect(im, 55, 52, 57, 52, G_LICHEN_LO)
    for x in (12, 45, 81, 114):                                   # the posts of the frame
        rect(im, x, 40, x + 1, 68, C_TB_LO)
    rect(im, 12, 40, 12, 68, C_TB_HI)
    rect(im, 8, 62, 119, 62, C_TB_LO)                             # the rail
    for x in (8, 26, 44, 83, 101, 119):
        rect(im, x, 62, x, 68, C_TB_LO)
    # ---- the shingled roof, hipped, seen from above; moss in its courses
    lead_hip(im, 1, 126, 11, 32, 22, 9, pal=G_SHINGLE)
    for x, y in ((20, 29), (40, 21), (58, 27), (86, 17), (97, 30), (70, 31), (47, 15)):
        dots(im, ((x, y), (x + 1, y)), G_LICHEN_LO)
        dots(im, ((x, y + 1),), G_LICHEN_DK)
    hl.outline(im)
    cast(im, 77, [(8, 119)] * 9 + [(9, 118)])                     # the floor's shadow on the water
    for x0, x1, y in ((22, 34, 91), (56, 70, 93), (90, 100, 91), (36, 42, 94)):
        for x in range(x0, x1 + 1):
            if px[x, y][3] == 0:
                px[x, y] = G_RING                                 # ripples
    return im


BRIDGE_DECK = (G_ST_MD, G_ST, G_ST_LT, G_ST_LT, G_ST, G_ST_MD)    # a slab each: the crown of the arch catches the light


def stone_bridge():
    """The garden's arched stone bridge from straight above, as
    kanazawa-canal-bridge is drawn: kerbs along its two sides, the slabs of the
    deck between, lighter over the crown of the arch and darker where it comes
    down to the banks. Inked along the two sides over the water, open at the
    two ends that meet the path."""
    im, d = canvas(3, 1)                 # 96 x 32, flat: walked ON, east-west
    px = im.load()
    for y in range(6, 26):
        for x in range(96):
            base = BRIDGE_DECK[x // 16]
            lit = G_ST_HI if base == G_ST_LT else (G_ST_LT if base == G_ST else G_ST)
            lo = G_ST_LO if base == G_ST_MD else G_ST_MD
            c = base
            if x % 16 == 15:
                c = G_ST_LO if base != G_ST_MD else G_ST_DK       # the joint between two slabs
            elif x % 16 == 0 or y == 7:
                c = lit                                           # a slab's lit edges
            elif y == 25 or x % 16 == 14:
                c = lo
            elif y == 16 and x // 16 % 2 == 0:
                c = lo                                            # a slab cut in two
            elif speck(x, y, 5) < 3:
                c = lo
            if y == 6:
                c = G_ST_LO if x % 16 != 15 else G_ST_DK          # the north kerb's shadow on the deck
            px[x, y] = c
    for y0 in (1, 26):                                            # the kerbs: a lit top, joints, a dark foot
        rect(im, 0, y0, 95, y0 + 4, G_ST)
        rect(im, 0, y0, 95, y0, G_ST_HI); rect(im, 0, y0 + 1, 95, y0 + 1, G_ST_LT)
        rect(im, 0, y0 + 4, 95, y0 + 4, G_ST_DK)
        for x in range(11 if y0 == 1 else 5, 96, 12):
            rect(im, x, y0 + 1, x, y0 + 3, G_ST_LO)
    for x0 in (0, 90):                                            # a post at each corner
        for y0 in (1, 25):
            rect(im, x0, y0, x0 + 5, y0 + 5, G_ST_MD)
            rect(im, x0, y0, x0 + 5, y0, G_ST_HI); rect(im, x0, y0, x0, y0 + 5, G_ST_HI)
            rect(im, x0 + 1, y0 + 1, x0 + 4, y0 + 1, G_ST_LT)
            rect(im, x0 + 5, y0 + 1, x0 + 5, y0 + 5, G_ST_DK); rect(im, x0, y0 + 5, x0 + 5, y0 + 5, G_ST_DK)
    rect(im, 0, 0, 95, 0, hl.INK); rect(im, 0, 31, 95, 31, hl.INK)
    return im


MOUNDS = ((6, 5, 5, 3), (20, 3, 6, 3), (13, 12, 6, 4), (28, 14, 5, 3),          # cx, cy, rx, ry
          (4, 20, 5, 3), (21, 22, 7, 4), (11, 28, 5, 3), (30, 28, 4, 3))


def moss_px(x, y):
    """Kenrokuen's moss at drawn pixel (x, y) of a 32px tile: a deep floor
    heaped into ragged cushions, each with a lit rim to the upper left and a
    dark one under its lower right edge. Periodic at 32 both ways; whole
    numbers only."""
    floor, cushion, lit, lo = G_MOSS
    x, y = x % 32, y % 32
    for n, (cx, cy, rx, ry) in enumerate(MOUNDS):
        dx = (x - cx + 16) % 32 - 16
        dy = (y - cy + 16) % 32 - 16
        q = (dx * dx * ry * ry + dy * dy * rx * rx) * 100 // (rx * rx * ry * ry)
        if q <= 80 + speck(x // 2, y, n) // 5:
            s = (dx * ry + dy * rx) * 100 // (rx * ry)
            return lo if s > 72 else (lit if s < -50 and q > 30 else cushion)
    return floor


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


PATH_JOINTS = (4, 10, 15, 21, 26, 31)                             # where one edging stone ends, along a side


def _path_part(role, x, y):
    """0 moss, 1 an edging stone, 2 gravel. Good past the tile's edge too: the next tile's part."""
    dist = _edge_dist(role, x, y)
    return 0 if dist < 3.2 else (1 if dist < 6.2 else 2)


def garden_path(role):
    """Kenrokuen's paths: pale raked gravel between lines of edging stones,
    moss beyond them. The stones are lit on their north and west sides and
    throw a shade south and east, whichever side of the path they edge."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    tail = '' if role == 'center' else role.split('-')[-1]
    for y in range(32):
        for x in range(32):
            part = _path_part(role, x, y)
            above, left = _path_part(role, x, y - 1), _path_part(role, x - 1, y)
            if part == 0:
                c = moss_px(x, y)
                if 1 in (above, left):
                    c = G_MOSS[3]                                 # the stone's shade on the moss
            elif part == 1:
                a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
                b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
                if (x if a <= b else y) in PATH_JOINTS:
                    c = G_ST_LO
                elif above != 1 or left != 1:
                    c = G_ST_HI if (above != 1 and left != 1) else G_ST_LT
                elif _path_part(role, x, y + 1) != 1 or _path_part(role, x + 1, y) != 1:
                    c = G_ST_MD
                else:
                    c = G_ST
            else:
                k = speck(x, y, 7)
                c = G_GRAVEL_HI if k < 5 else (G_GRAVEL_LO if k < 12 else (G_GRAVEL_SH if k < 14 else G_GRAVEL))
                if y % 6 == 2 and (x + y // 6 * 3) % 5 < 3 and _edge_dist(role, x, y) > 8:
                    c = G_GRAVEL_LO                               # the rake's lines
                if 1 in (above, left):
                    c = G_GRAVEL_SH                               # the stone's shade on the gravel
            px[x, y] = c
    return im


# ==============================================================================
# Higashi Chaya
# ==============================================================================
# ---- the house look (#290) ------------------------------------------------------
# The ten building fronts below (chaya-front-a/-b/-c, the gold-leaf shop, the
# phonograph museum, Katamachi's four and the samurai house) are drawn in the
# GuttyKreum house look (docs/generators-and-checks.md), as the done
# kanazawa-chaya-a/-b of generate_hokuriku_art.py are: only the sheets'
# colours, the machiya under the pack's kawara in straight courses, the
# flat-roofed shops with their roof seen from above, dark glass with a slanted
# glare in every window, lamps in the pack's dim gold, an ink silhouette.
# Rectangles, points and pixel access only. tools/tests/kanazawa-art.test.js
# holds them to it.
H_INK, H_EDGE, H_EAVE = rgb('0a1627'), rgb('172459'), rgb('191c2a')
H_WALL, H_WALL_HI, H_WALL_LO, H_WALL_DK = rgb('71412a'), rgb('aa775f'), rgb('5a3827'), rgb('3f210f')
H_GLASS, H_GLASS_LO, H_GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
H_REED, H_EARTH = rgb('be9e8c'), rgb('8e7366')
H_PAPER, H_PAPER_HI = rgb('e4cecc'), rgb('fafcfd')
H_RED, H_RED_HI, H_RED_LO = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
H_STONE, H_STONE_LO, H_STONE_HI, H_STONE_LT, H_STEEL = (rgb('848295'), rgb('53596d'), rgb('a4b0b5'),
                                                        rgb('dae2e4'), rgb('575f79'))
H_LACQUER = rgb('2a2636')
H_SLATE, H_SLATE_HI, H_SLATE_JOINT, H_SLATE_LO = rgb('5b6c79'), rgb('698592'), rgb('444f5e'), rgb('2e4040')
H_COPING, H_COPING_HI = rgb('94a2a8'), rgb('d1e2eb')
H_LAMP, H_LAMP_HI = rgb('c6a663'), rgb('f3d890')
H_GOLD_DK, H_GOLD_LO = rgb('86624f'), rgb('a7843b')
H_INDIGO = rgb('314b8e')
H_GREEN, H_GREEN_HI, H_GREEN_LO = rgb('506b6b'), rgb('6c8e7f'), rgb('395050')
H_KAKI, H_KAKI_HI = rgb('ce6a42'), rgb('f6a583')


def roof_plan(im, x0, y0, x1, y1):
    """A flat roof seen from above: slate panels inside a steel coping (the
    pattern of generate_fukuoka_art.flat_roof, with a sheet colour for its dark)."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                c = H_EDGE
            elif x in (x0 + 1, x0 + 2, x1 - 1, x1 - 2) or y in (y0 + 1, y0 + 2, y1 - 1):
                c = H_COPING_HI if (x == x0 + 1 or y == y0 + 1) else H_COPING
            elif (x - x0) % 9 == 3 or (y - y0 + (x - x0) // 9 * 5) % 14 == 6:
                c = H_SLATE_JOINT
            elif x >= x1 - 5 or y >= y1 - 3:
                c = H_SLATE_LO
            else:
                c = H_SLATE_HI if y == y0 + 3 else H_SLATE
            px[x, y] = c


def disc(d, cx, cy, r, fill):
    """A round thing as stepped rows of rectangles, centred on (cx, cy)."""
    for dy in range(-r, r + 1):
        w = math.isqrt(r * r - dy * dy)
        d.rectangle([cx - w, cy + dy, cx + w, cy + dy], fill=fill)


def lantern_h(d, x, y, w, h, paper, hi, lo, mark=None):
    """A paper lantern on its hook: rounded by one step top and bottom, lit on
    the left, its bands in the pack's dim gold, a mark on it."""
    cx = x + w // 2
    d.rectangle([cx - 1, y, cx + 1, y], fill=H_EAVE)
    d.rectangle([x + 1, y + 1, x + w - 2, y + 1], fill=H_LAMP)
    d.rectangle([x + 1, y + 2, x + w - 2, y + h - 3], fill=paper)
    d.rectangle([x, y + 3, x + w - 1, y + h - 4], fill=paper)
    d.rectangle([x, y + 3, x, y + h - 4], fill=hi); d.rectangle([x + 1, y + 2, x + 1, y + h - 3], fill=hi)
    d.rectangle([x + w - 1, y + 3, x + w - 1, y + h - 4], fill=lo)
    d.rectangle([x + 1, y + h - 2, x + w - 2, y + h - 2], fill=H_LAMP)
    d.rectangle([cx, y + h - 1, cx, y + h - 1], fill=H_EAVE)
    if mark:
        d.rectangle([cx - 1, y + 4, cx + 1, y + h - 5], fill=mark)


def noren_h(d, x0, y0, x1, y1, cloth, hi, line, slits=2, pole=H_WALL_DK):
    """A noren on its pole: the lit top row, the slits and the hem in the cloth's dark."""
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y0 - 1], fill=pole)
    d.rectangle([x0, y0, x1, y1], fill=cloth)
    d.rectangle([x0, y0, x1, y0], fill=hi)
    d.rectangle([x0, y1, x1, y1], fill=line)
    w = (x1 - x0 + 1) / (slits + 1)
    for k in range(1, slits + 1):
        x = round(x0 + k * w)
        d.rectangle([x, y0 + 3, x, y1], fill=line)


def lattice_doors(d, x0, y0, x1, y1, frame, bar):
    """A pair of koshi-do: dark glass behind a fine lattice, a kick board, the
    leaves' lit left stiles."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    m = (x0 + x1) // 2
    for a, b in ((x0 + 1, m - 1), (m + 1, x1 - 1)):
        bars(d, a, y0 + 1, b, y1 - 5, bar, H_GLASS)
        d.rectangle([a, y0 + 1, b, y0 + 1], fill=H_GLASS_LO)
        d.rectangle([a, y1 - 4, b, y1], fill=frame)
        d.rectangle([a, y1 - 4, b, y1 - 4], fill=bar)


def stone_foot(d, x0, x1, y0=124, y1=127, joint=12):
    """The stone kerb a front stands on: lit top row, jointed."""
    d.rectangle([x0, y0, x1, y1], fill=H_STONE_LO)
    d.rectangle([x0, y0, x1, y0], fill=H_STONE)
    for x in range(x0 + 7, x1, joint):
        d.rectangle([x, y0 + 1, x, y1], fill=H_SLATE_LO)


def bricks(px, x0, y0, x1, y1, base, hi, lo, joint):
    """Brick in courses of 3 rows, stretchers 8 long, lit here and there."""
    for y in range(y0, y1 + 1):
        course = (y - y0) // 3
        for x in range(x0, x1 + 1):
            if (y - y0) % 3 == 2 or (x + course * 4) % 8 == 0:
                c = joint
            elif (y - y0) % 3 == 0 and ((x + course * 4) // 8 + course) % 3 == 0:
                c = hi
            elif x >= x1 - 6:
                c = lo
            else:
                c = base
            px[x, y] = c


def chaya(v):
    def build():
        im, d = canvas(3, 4)             # 96 x 128; the door is column 1 (x 32-63)
        ry = {'a': 9, 'b': 13, 'c': 7}[v]                         # each house's ridge at its own height
        wall, hi, lo, dk = {
            'a': (H_WALL, H_WALL_HI, H_WALL_LO, H_WALL_DK),
            'b': (H_WALL_LO, H_WALL, rgb('4d3326'), rgb('312522')),
            'c': (H_RED_LO, H_RED, rgb('71391f'), H_WALL_DK)}[v]
        kawara(im, d, 0, ry, 95, 34)                              # the main roof, eave to eave with its neighbours
        # ---- the upper floor: the tea rooms
        d.rectangle([2, 35, 93, 68], fill=wall)
        d.rectangle([2, 35, 93, 36], fill=dk)                     # the eave's shade
        d.rectangle([2, 37, 2, 68], fill=hi); d.rectangle([91, 37, 93, 68], fill=lo)
        if v == 'a':                                              # one long screen of lattice, two reed blinds
            d.rectangle([5, 39, 90, 63], fill=H_INK)
            bars(d, 6, 40, 89, 62, lo, H_GLASS)
            for x in (27, 47, 67):
                d.rectangle([x, 40, x + 1, 62], fill=wall)
            for x0, x1 in ((6, 26), (69, 89)):
                d.rectangle([x0, 40, x1, 50], fill=H_REED)
                for y in range(42, 51, 2):
                    d.rectangle([x0, y, x1, y], fill=H_WALL_HI)
                d.rectangle([x0, 51, x1, 51], fill=H_GLASS_LO)
        elif v == 'b':                                            # three lattice windows, a blind in one
            for x0 in (7, 36, 65):
                d.rectangle([x0 - 1, 39, x0 + 24, 63], fill=H_INK)
                bars(d, x0, 40, x0 + 23, 62, H_WALL, H_GLASS)
            d.rectangle([65, 40, 88, 47], fill=H_REED)
            for y in range(41, 48, 2):
                d.rectangle([65, y, 88, y], fill=H_WALL_HI)
            d.rectangle([65, 48, 88, 48], fill=H_GLASS_LO)
        else:                                                     # two wide windows between shutter boxes
            for x0, x1 in ((13, 43), (52, 82)):
                d.rectangle([x0 - 1, 40, x1 + 1, 62], fill=dk)
                pane(d, x0, 41, x1, 61)
                d.rectangle([(x0 + x1) // 2, 41, (x0 + x1) // 2, 61], fill=dk)
                d.rectangle([x0, 50, x1, 50], fill=dk)
            for x0 in (5, 85):
                d.rectangle([x0, 39, x0 + 5, 63], fill=lo if x0 == 5 else dk)
                d.rectangle([x0, 39, x0 + 5, 39], fill=hi)
                d.rectangle([x0 + 2, 40, x0 + 2, 62], fill=dk if x0 == 5 else lo)
        d.rectangle([4, 64, 91, 65], fill=lo); d.rectangle([4, 64, 91, 64], fill=hi)   # the balcony rail
        d.rectangle([4, 66, 91, 68], fill=dk)
        for x in range(6, 91, 4):
            d.rectangle([x, 66, x, 67], fill=lo)
        kawara(im, d, 0, 69, 95, 78)                              # the pent roof over the street
        # ---- the ground floor
        d.rectangle([2, 79, 93, 123], fill=lo)
        d.rectangle([2, 79, 93, 80], fill=dk)
        d.rectangle([2, 81, 2, 123], fill=wall); d.rectangle([91, 81, 93, 123], fill=dk)
        for x0, x1 in ((5, 28), (67, 89)):                        # the lattice bays
            if v == 'c' and x0 == 67:
                continue
            d.rectangle([x0 - 1, 83, x1 + 1, 114], fill=dk)
            bars(d, x0, 84, x1, 113, wall, dk, 2)
            d.rectangle([x0 - 1, 115, x1 + 1, 116], fill=wall); d.rectangle([x0 - 1, 115, x1 + 1, 115], fill=hi)
            d.rectangle([x0, 117, x1, 123], fill=dk)
            for x in range(x0 + 1, x1, 3):
                d.rectangle([x, 118, x, 123], fill=lo)
        d.rectangle([32, 81, 63, 123], fill=H_INK)                # the entrance
        d.rectangle([33, 82, 62, 123], fill=H_GLASS)
        if v == 'a':
            lattice_doors(d, 34, 97, 61, 123, dk, lo)
            noren_h(d, 34, 83, 61, 98, H_INDIGO, H_GLARE, H_EDGE)
            d.rectangle([46, 87, 49, 92], fill=H_PAPER); d.rectangle([45, 88, 50, 91], fill=H_PAPER)
            lantern_h(d, 64, 89, 7, 14, H_PAPER, H_PAPER_HI, H_REED, H_RED)
        elif v == 'b':
            lattice_doors(d, 34, 97, 61, 120, dk, wall)
            noren_h(d, 34, 83, 61, 97, H_GREEN, H_GREEN_HI, H_GREEN_LO, pole=dk)
            d.rectangle([46, 87, 49, 91], fill=H_PAPER); d.rectangle([45, 88, 50, 90], fill=H_PAPER)
            d.rectangle([31, 121, 64, 123], fill=H_STONE)          # a stone step up to the door
            d.rectangle([31, 121, 64, 121], fill=H_STONE_HI)
            d.rectangle([20, 83, 28, 84], fill=dk)                # a round red lantern on a bracket
            d.rectangle([24, 85, 24, 85], fill=dk)
            lantern_h(d, 20, 86, 9, 14, H_RED, H_RED_HI, H_RED_LO)
            d.rectangle([66, 89, 71, 108], fill=H_REED)           # the house's name board
            d.rectangle([66, 89, 66, 108], fill=H_PAPER); d.rectangle([71, 89, 71, 108], fill=H_WALL_HI)
            for y in (92, 97, 102):
                d.rectangle([68, y, 69, y + 2], fill=dk)
        else:
            lattice_doors(d, 34, 102, 61, 123, dk, lo)
            noren_h(d, 34, 83, 61, 104, H_KAKI, H_KAKI_HI, H_RED, slits=3)
            for x in range(68, 92, 4):                            # a boarded bay: a small window,
                d.rectangle([x, 81, x, 123], fill=dk)             # a bench under a red cloth for tea outside
            d.rectangle([70, 86, 86, 100], fill=dk)
            pane(d, 71, 87, 85, 99)
            d.rectangle([78, 87, 78, 99], fill=dk)
            d.rectangle([66, 109, 91, 112], fill=H_RED); d.rectangle([66, 109, 91, 109], fill=H_RED_HI)
            d.rectangle([66, 113, 91, 114], fill=dk)
            for x in (68, 88):
                d.rectangle([x, 115, x + 1, 123], fill=dk)
            d.rectangle([75, 106, 78, 108], fill=H_PAPER); d.rectangle([75, 106, 78, 106], fill=H_PAPER_HI)
            d.rectangle([82, 107, 86, 108], fill=H_GREEN)
        stone_foot(d, 0, 95)
        hl.outline(im)
        return im
    return build


def gold_shop():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1 (x 32-63)
    px = im.load()
    kawara(im, d, 0, 11, 127, 34)
    # ---- the upper wall: a storehouse front laid with squares of gold leaf, the far side in shade
    for y in range(35, 69):
        for x in range(2, 126):
            gx, gy = (x - 2) % 8, (y - 37) % 8
            far = x >= 102
            if y <= 36 or y >= 67:
                c = H_GOLD_DK
            elif gx == 7 or gy == 7:
                c = H_GOLD_DK if far else H_GOLD_LO
            elif gx == 0 and gy == 0 and (((x - 2) // 8) * 5 + ((y - 37) // 8) * 3) % 4 == 0 and not far:
                c = H_LAMP_HI
            else:
                c = H_GOLD_LO if far else H_LAMP
            px[x, y] = c
    d.rectangle([2, 37, 2, 66], fill=H_LAMP_HI)
    d.rectangle([41, 40, 86, 62], fill=H_GOLD_DK)                 # the shop's board: HAKU, leaf
    d.rectangle([42, 41, 85, 61], fill=H_EAVE)
    d.rectangle([42, 41, 85, 41], fill=H_LACQUER)
    text(d, 'HAKU', 64 - text_w('HAKU') // 2 + 1, 48, H_INK)
    text(d, 'HAKU', 64 - text_w('HAKU') // 2, 47, H_LAMP)
    d.rectangle([47, 50, 47, 50], fill=H_GOLD_LO); d.rectangle([80, 50, 80, 50], fill=H_GOLD_LO)
    kawara(im, d, 0, 69, 127, 78)                                 # the pent roof
    # ---- the ground floor: black lacquer, gold trim
    d.rectangle([2, 79, 125, 123], fill=H_LACQUER)
    d.rectangle([2, 79, 125, 80], fill=H_EAVE)
    d.rectangle([2, 81, 125, 81], fill=H_GOLD_LO)
    d.rectangle([2, 82, 2, 123], fill=H_GLASS); d.rectangle([121, 82, 125, 123], fill=H_EAVE)
    for x in range(8, 121, 6):
        d.rectangle([x, 119, x, 123], fill=H_EAVE)
    # the left window: a gilded screen behind the glass, a pine branch on it
    d.rectangle([6, 86, 29, 118], fill=H_GOLD_DK)
    pane(d, 7, 87, 28, 117)
    d.rectangle([9, 95, 26, 115], fill=H_GOLD_LO)
    d.rectangle([9, 95, 26, 95], fill=H_LAMP)
    for x in (15, 21):
        d.rectangle([x, 96, x, 115], fill=H_GOLD_DK)
    for x, y in ((11, 107), (12, 106), (13, 105), (14, 104), (16, 104), (17, 103), (18, 102), (19, 101),
                 (22, 100), (23, 101)):
        d.rectangle([x, y, x, y], fill=H_GOLD_DK)
    for x, y in ((13, 102), (19, 99), (23, 99)):
        d.rectangle([x - 1, y - 1, x + 1, y], fill=H_GREEN)
    # the door under a cream noren with one square of leaf
    d.rectangle([32, 83, 63, 123], fill=H_INK)
    d.rectangle([33, 84, 62, 123], fill=H_GLASS)
    lattice_doors(d, 34, 100, 61, 123, H_EAVE, H_LACQUER)
    noren_h(d, 34, 85, 61, 101, H_PAPER, H_PAPER_HI, H_REED, pole=H_GOLD_DK)
    d.rectangle([45, 89, 51, 95], fill=H_LAMP); d.rectangle([45, 89, 51, 89], fill=H_LAMP_HI)
    d.rectangle([45, 95, 51, 95], fill=H_GOLD_LO); d.rectangle([51, 90, 51, 95], fill=H_GOLD_LO)
    # the right window: gilded boxes and bowls on two shelves
    d.rectangle([66, 86, 101, 118], fill=H_GOLD_DK)
    pane(d, 67, 87, 100, 117)
    for y in (102, 116):
        d.rectangle([67, y, 100, y + 1], fill=H_GOLD_DK)
    for i, x in enumerate((70, 78, 86, 93)):
        d.rectangle([x, 96 + i % 2, x + 4, 101], fill=(H_LAMP, H_RED, H_LAMP, H_EAVE)[i])
        d.rectangle([x, 96 + i % 2, x + 4, 96 + i % 2], fill=(H_LAMP_HI, H_RED_HI, H_LAMP_HI, H_LACQUER)[i])
        d.rectangle([x - 1, 112, x + 5, 115], fill=(H_EAVE, H_LAMP, H_RED, H_LAMP)[i])
        d.rectangle([x, 111, x + 4, 111], fill=(H_LACQUER, H_LAMP_HI, H_RED_HI, H_LAMP_HI)[i])
        d.rectangle([x + 1, 115, x + 3, 115], fill=H_GOLD_DK)
    d.rectangle([83, 87, 83, 117], fill=H_GOLD_DK)
    # the sign: a soft-serve cone wrapped in gold leaf
    d.rectangle([104, 85, 123, 117], fill=H_GOLD_LO)
    d.rectangle([105, 86, 122, 116], fill=H_EAVE)
    d.rectangle([105, 86, 122, 86], fill=H_LACQUER)
    for i, (w, y) in enumerate(((1, 89), (2, 91), (3, 93), (4, 95), (5, 97), (5, 99), (4, 101))):
        d.rectangle([113 - w, y, 114 + w, y + 1], fill=H_LAMP)
        d.rectangle([113 - w, y, 113 - w, y + 1], fill=H_LAMP_HI)
        d.rectangle([114 + w, y, 114 + w, y + 1], fill=H_GOLD_LO)
    d.rectangle([113, 88, 113, 88], fill=H_LAMP_HI)
    for k in range(9):                                            # the wafer
        w = 4 - k // 2
        d.rectangle([113 - w, 103 + k, 114 + w, 103 + k], fill=H_GOLD_DK if k % 3 else H_GOLD_LO)
    d.rectangle([112, 118, 115, 123], fill=H_EAVE)
    stone_foot(d, 0, 127)
    hl.outline(im)
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


GRAMOPHONE = ('........dlll.',
              '.......dgghhl',
              '......dggghhl',
              '.....dgggggl.',
              '....dggggll..',
              '...dgggl.....',
              '...dgl.......',
              '...dl........',
              '.kkkkkkk.....',
              '.ddddddddd...',
              '.dglllllld...',
              '.dllllllld...',
              '.ddddddddd...')


def gramophone(im, x, y):
    """A horn gramophone in the gold ramp: the horn, the disc, the box."""
    hl.stamp(im, hl.pixmap(GRAMOPHONE, dict(d=H_GOLD_DK, l=H_GOLD_LO, g=H_LAMP, h=H_LAMP_HI, k=H_EAVE)), x, y)


def phono_museum():
    """The phonograph museum by the teahouse quarter: a flat roof with a
    skylight, a plain stone front under a horn gramophone in a roundel."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is column 1 (x 32-63)
    roof_plan(im, 1, 2, 94, 34)
    d.rectangle([60, 9, 83, 26], fill=H_EDGE)                     # the skylight in its steel frame
    d.rectangle([61, 10, 82, 25], fill=H_COPING)
    d.rectangle([61, 10, 82, 10], fill=H_COPING_HI); d.rectangle([61, 10, 61, 25], fill=H_COPING_HI)
    pane(d, 63, 12, 80, 23, step=7)
    d.rectangle([71, 12, 72, 23], fill=H_COPING)
    d.rectangle([62, 27, 84, 27], fill=H_SLATE_LO); d.rectangle([84, 10, 84, 27], fill=H_SLATE_LO)
    # ---- the stone front, in courses under a cornice lip and its shadow
    d.rectangle([2, 35, 93, 37], fill=H_STONE_HI); d.rectangle([2, 35, 93, 35], fill=H_COPING_HI)
    d.rectangle([3, 38, 92, 123], fill=H_STONE)
    for y in range(38, 80):
        if (y - 38) % 7 == 6:
            d.rectangle([4, y, 91, y], fill=H_STEEL)
        elif (y - 38) % 7 == 0:
            d.rectangle([4, y, 91, y], fill=H_STONE_HI)
    for y in range(38, 80, 7):
        for x in range(8 + (y // 7) % 2 * 9, 90, 18):
            d.rectangle([x, y + 1, x, y + 5], fill=H_STEEL)
    d.rectangle([3, 38, 92, 38], fill=H_STEEL)
    d.rectangle([3, 39, 3, 123], fill=H_STONE_HI); d.rectangle([88, 39, 92, 123], fill=H_STEEL)
    # ---- the roundel: a green disc in a gold ring, the gramophone on it
    disc(d, 47, 52, 13, H_GOLD_LO)
    disc(d, 47, 52, 11, H_GREEN_LO)
    for dy in range(-11, 0):                                      # lit on its upper left
        w = math.isqrt(121 - dy * dy)
        d.rectangle([47 - w, 52 + dy, 47 - w + 1, 52 + dy], fill=H_SLATE_HI)
    disc(d, 47, 52, 0, H_GREEN_LO)
    gramophone(im, 41, 45)
    for x, y in ((38, 46), (55, 57)):                              # notes in the air
        d.rectangle([x, y, x, y + 4], fill=H_LAMP_HI); d.rectangle([x - 2, y + 4, x, y + 5], fill=H_LAMP_HI)
    for x0 in (8, 76):                                            # a slit window either side
        d.rectangle([x0, 41, x0 + 11, 71], fill=H_STEEL)
        pane(d, x0 + 1, 42, x0 + 10, 70, step=7)
        d.rectangle([x0 + 1, 56, x0 + 10, 56], fill=H_STEEL)
        d.rectangle([x0 - 1, 72, x0 + 12, 72], fill=H_STONE_HI)
    d.rectangle([20, 67, 75, 77], fill=H_GOLD_LO)                 # its name
    d.rectangle([21, 68, 74, 76], fill=H_EAVE)
    text(d, 'PHONO', 48 - text_w('PHONO') // 2, 69, H_LAMP)
    # ---- a flat canopy, the ground floor
    d.rectangle([1, 79, 94, 82], fill=H_COPING); d.rectangle([1, 79, 94, 79], fill=H_COPING_HI)
    d.rectangle([1, 82, 94, 82], fill=H_STEEL)
    d.rectangle([3, 83, 92, 84], fill=H_STEEL)                     # its shadow
    d.rectangle([7, 88, 29, 118], fill=H_STEEL)                   # a window: a gramophone and records
    pane(d, 8, 89, 28, 117)
    gramophone(im, 9, 101)
    for y in (96, 109):
        disc(d, 25, y, 3, H_EAVE); d.rectangle([25, y, 25, y], fill=H_LAMP)
    d.rectangle([8, 114, 28, 115], fill=H_STEEL)
    d.rectangle([33, 86, 62, 123], fill=H_STEEL)                  # glass doors
    for x0, x1 in ((35, 47), (48, 60)):
        d.rectangle([x0, 88, x1, 123], fill=H_STONE_LO)
        pane(d, x0 + 1, 89, x1 - 1, 121, step=8)
    d.rectangle([45, 104, 45, 109], fill=H_COPING_HI); d.rectangle([50, 104, 50, 109], fill=H_COPING_HI)
    d.rectangle([66, 89, 88, 118], fill=H_PAPER)                  # the poster: a record, a title
    d.rectangle([66, 89, 88, 89], fill=H_COPING_HI); d.rectangle([87, 90, 88, 118], fill=H_STONE_HI)
    disc(d, 76, 101, 7, H_EAVE)
    disc(d, 76, 101, 5, H_GLASS)
    disc(d, 76, 101, 2, H_LAMP)
    d.rectangle([76, 101, 76, 101], fill=H_PAPER)
    d.rectangle([71, 96, 72, 97], fill=H_GLARE)
    for y, x1 in ((112, 84), (115, 80)):
        d.rectangle([69, y, x1, y], fill=H_EAVE)
    stone_foot(d, 1, 94)
    hl.outline(im)
    return im


# ==============================================================================
# Katamachi
# ==============================================================================
def bottles(d, x0, x1, y, seed=0):
    """A shelf of bottles standing dark against the glass, their shoulders caught by the light."""
    tones = (H_EAVE, H_GREEN_LO, H_GOLD_LO, H_WALL_DK)
    for i, x in enumerate(range(x0, x1 - 1, 4)):
        h = (7, 9, 6, 8, 9, 7)[(i + seed) % 6]
        c = tones[(i + seed) % 4]
        d.rectangle([x + 1, y - h, x + 1, y - h + 2], fill=c)
        d.rectangle([x, y - h + 3, x + 2, y], fill=c)
        d.rectangle([x, y - h + 3, x, y - h + 3], fill=H_GLARE)
    d.rectangle([x0 - 1, y + 1, x1, y + 1], fill=H_WALL_DK)


def whisky_bar():
    im, d = canvas(3, 5)                 # 96 x 160; the door is column 1 (x 32-63)
    px = im.load()
    # ---- the roof from above: a water tank and a flue standing on it, each with its shadow
    roof_plan(im, 1, 2, 94, 44)
    for dy in range(-9, 10):                                      # the tank's shadow, to the lower right
        w = math.isqrt(81 - dy * dy)
        d.rectangle([26 - w + 3, 22 + dy + 3, 26 + w + 3, 22 + dy + 3], fill=H_SLATE_LO)
    disc(d, 26, 22, 9, H_STONE)
    for dy in range(-9, 10):
        w = math.isqrt(81 - dy * dy)
        d.rectangle([26 - w, 22 + dy, 26 - w + 1, 22 + dy], fill=H_STONE_HI)
        d.rectangle([26 + w - 1, 22 + dy, 26 + w, 22 + dy], fill=H_SLATE_JOINT)
    disc(d, 26, 22, 3, H_SLATE_JOINT)
    disc(d, 25, 21, 2, H_STONE_HI)
    d.rectangle([62, 16, 71, 25], fill=H_SLATE_LO)                # the flue, a square stack
    d.rectangle([60, 14, 68, 22], fill=H_SLATE_JOINT)
    d.rectangle([60, 14, 68, 14], fill=H_STONE_HI); d.rectangle([60, 14, 60, 22], fill=H_STONE_HI)
    d.rectangle([62, 16, 66, 20], fill=H_EAVE)
    # ---- the front: dark brick
    bricks(px, 3, 45, 92, 156, H_WALL_LO, H_WALL, H_WALL_DK, H_WALL_DK)
    d.rectangle([3, 45, 92, 46], fill=H_WALL_DK)                  # the coping's shadow
    # the painted board: a glass of whisky, MALT BAR
    d.rectangle([17, 49, 78, 67], fill=H_GOLD_LO)
    d.rectangle([18, 50, 77, 66], fill=H_EAVE)
    d.rectangle([18, 50, 77, 50], fill=H_GLASS)
    d.rectangle([22, 53, 34, 64], fill=H_GLARE)                   # the tumbler, amber over ice
    d.rectangle([23, 53, 33, 63], fill=H_GLASS)
    d.rectangle([23, 57, 33, 63], fill=H_LAMP); d.rectangle([23, 61, 33, 63], fill=H_GOLD_LO)
    d.rectangle([25, 56, 28, 59], fill=H_PAPER); d.rectangle([25, 56, 25, 56], fill=H_LAMP_HI)
    d.rectangle([29, 59, 31, 61], fill=H_PAPER)
    d.rectangle([22, 64, 34, 64], fill=H_PAPER)
    text(d, 'MALT', 43, 52, H_LAMP)
    text(d, 'BAR', 47, 60, H_PAPER)
    # ---- the first floor: two windows with stepped arched heads, bottles on a shelf
    for x in (10, 62):
        d.rectangle([x - 1, 74, x + 21, 100], fill=H_WALL_DK)
        for k, inset in enumerate((7, 4, 2, 1)):
            d.rectangle([x - 1 + inset, 70 + k, x + 21 - inset, 70 + k], fill=H_WALL_DK)
        pane(d, x + 1, 75, x + 19, 98, step=8)
        for k, inset in enumerate((7, 4, 2, 1)):
            d.rectangle([x + 1 + inset - 1, 71 + k, x + 19 - inset + 1, 71 + k], fill=H_GLASS_LO)
        d.rectangle([x + 10, 71, x + 10, 98], fill=H_WALL_DK)
        bottles(d, x + 2, x + 19, 87, x)
        d.rectangle([x - 2, 101, x + 22, 102], fill=H_STONE)
        d.rectangle([x - 2, 101, x + 22, 101], fill=H_STONE_HI)
    # the lamp on an iron bracket between them, the pack's dim gold
    d.rectangle([43, 72, 51, 72], fill=H_EAVE); d.rectangle([47, 72, 47, 76], fill=H_EAVE)
    d.rectangle([44, 77, 50, 77], fill=H_EAVE)
    d.rectangle([44, 78, 50, 91], fill=H_LAMP); d.rectangle([43, 80, 51, 89], fill=H_LAMP)
    d.rectangle([44, 80, 44, 89], fill=H_LAMP_HI); d.rectangle([50, 80, 51, 89], fill=H_GOLD_LO)
    d.rectangle([46, 83, 47, 85], fill=H_LAMP_HI)
    d.rectangle([45, 92, 49, 93], fill=H_EAVE)
    # ---- a green canopy over the pavement, its shadow on the brick
    d.rectangle([1, 106, 94, 115], fill=H_GREEN)
    for y in range(107, 115, 2):
        d.rectangle([1, y, 94, y], fill=H_GREEN_LO)
    d.rectangle([1, 115, 94, 115], fill=H_SLATE_LO)
    d.rectangle([3, 116, 92, 117], fill=H_WALL_DK)
    # ---- the ground floor: the bottle window, the timber door, a chalk board and a cask
    d.rectangle([7, 121, 30, 148], fill=H_WALL_DK)
    pane(d, 8, 122, 29, 147)
    bottles(d, 9, 29, 133, 1)
    bottles(d, 9, 29, 145, 3)
    d.rectangle([34, 119, 61, 156], fill=H_WALL_DK)               # the door
    d.rectangle([36, 121, 59, 156], fill=H_WALL)
    d.rectangle([36, 121, 36, 156], fill=H_WALL_HI); d.rectangle([57, 122, 59, 156], fill=H_WALL_LO)
    d.rectangle([40, 125, 55, 138], fill=H_WALL_DK)
    pane(d, 41, 126, 54, 137, step=7)
    bottles(d, 42, 54, 136, 2)
    d.rectangle([41, 142, 54, 152], fill=H_WALL_LO); d.rectangle([41, 142, 54, 142], fill=H_WALL_HI)
    d.rectangle([53, 139, 54, 140], fill=H_LAMP)
    d.rectangle([66, 122, 87, 134], fill=H_WALL_DK)               # the chalk board
    d.rectangle([67, 123, 86, 133], fill=H_SLATE_LO)
    d.rectangle([67, 123, 86, 123], fill=H_GREEN_LO)
    for y, x1 in ((125, 82), (128, 79), (131, 83)):
        d.rectangle([69, y, x1, y], fill=H_PAPER)
    for k, inset in enumerate((2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)):   # a cask on end
        y = 139 + k
        d.rectangle([68 + inset, y, 85 - inset, y], fill=H_WALL)
        d.rectangle([68 + inset, y, 69 + inset, y], fill=H_WALL_HI)
        d.rectangle([83 - inset, y, 85 - inset, y], fill=H_WALL_LO)
    d.rectangle([70, 139, 83, 139], fill=H_WALL_HI)
    for y in (143, 151):
        d.rectangle([68, y, 85, y], fill=H_EAVE)
    for x in (73, 78):
        d.rectangle([x, 140, x, 156], fill=H_WALL_LO)
    d.rectangle([2, 157, 93, 159], fill=H_SLATE_JOINT); d.rectangle([2, 157, 93, 157], fill=H_STONE)
    hl.outline(im)
    return im


def mug(d, x, y):
    """A mug of beer with its head on, painted on the board."""
    d.rectangle([x - 1, y, x + 8, y + 2], fill=H_PAPER_HI)
    d.rectangle([x, y + 3, x + 7, y + 11], fill=H_GOLD_LO)
    d.rectangle([x + 1, y + 3, x + 2, y + 11], fill=H_LAMP_HI)
    d.rectangle([x + 8, y + 4, x + 10, y + 9], fill=H_WALL_DK); d.rectangle([x + 8, y + 6, x + 9, y + 7], fill=H_LAMP)
    d.rectangle([x, y + 12, x + 7, y + 12], fill=H_WALL_DK)


def izakaya():
    im, d = canvas(4, 4)                 # 128 x 128; the door is column 1 (x 32-63)
    kawara(im, d, 0, 8, 127, 30)
    # ---- the upper floor: boards, the big painted board, small windows under it
    d.rectangle([2, 31, 125, 66], fill=H_WALL_LO)
    for x in range(8, 124, 6):
        d.rectangle([x, 33, x, 66], fill=H_WALL_DK)
    d.rectangle([2, 31, 125, 32], fill=H_WALL_DK)
    d.rectangle([2, 33, 2, 66], fill=H_WALL); d.rectangle([121, 33, 125, 66], fill=H_WALL_DK)
    d.rectangle([5, 34, 122, 55], fill=H_RED_LO)                  # the board, unlit: dim gold in scanlines
    hl.scanlines(im, (7, 36, 120, 53), H_LAMP, H_GOLD_LO)
    d.rectangle([7, 36, 120, 36], fill=H_LAMP_HI)
    kana(d, ['no', 'mi', 'ho', 'u', 'da', 'i'], 11, 41, H_WALL_DK)
    mug(d, 62, 39)
    d.rectangle([77, 38, 117, 51], fill=H_RED_LO)                 # the red SAKE tab
    d.rectangle([78, 39, 116, 50], fill=H_RED)
    d.rectangle([78, 39, 116, 39], fill=H_RED_HI)
    text(d, 'SAKE', 97 - text_w('SAKE') // 2 + 1, 42, H_RED_LO)
    text(d, 'SAKE', 97 - text_w('SAKE') // 2, 41, H_PAPER_HI)
    for x in (10, 30, 86, 106):                                   # small windows under the board
        d.rectangle([x, 57, x + 12, 65], fill=H_WALL_DK)
        pane(d, x + 1, 58, x + 11, 64, step=6)
        d.rectangle([x + 6, 58, x + 6, 64], fill=H_WALL_DK)
    kawara(im, d, 0, 67, 127, 77)                                 # the pent roof
    # ---- the ground floor
    d.rectangle([2, 78, 125, 123], fill=H_WALL_LO)
    d.rectangle([2, 78, 125, 79], fill=H_WALL_DK)
    d.rectangle([2, 80, 2, 123], fill=H_WALL); d.rectangle([121, 80, 125, 123], fill=H_WALL_DK)
    for x in range(8, 121, 6):
        d.rectangle([x, 119, x, 123], fill=H_WALL_DK)
    # the left window: the menu on paper strips
    d.rectangle([6, 96, 29, 118], fill=H_WALL_DK)
    pane(d, 7, 97, 28, 117)
    for i, x in enumerate(range(9, 27, 4)):
        d.rectangle([x, 99, x + 2, 112 - i % 2 * 3], fill=H_PAPER)
        d.rectangle([x, 99, x + 2, 99], fill=H_PAPER_HI)
        for y in range(101, 110 - i % 2 * 3, 3):
            d.rectangle([x + 1, y, x + 1, y], fill=H_RED_LO if (i + y) % 2 else H_WALL_DK)
    # the door under its red noren
    d.rectangle([32, 94, 63, 123], fill=H_INK)
    d.rectangle([33, 95, 62, 123], fill=H_GLASS)
    lattice_doors(d, 34, 106, 61, 123, H_WALL_DK, H_WALL_LO)
    noren_h(d, 34, 96, 61, 112, H_RED, H_RED_HI, H_RED_LO, slits=3)
    for x in (37, 44, 51, 58):
        d.rectangle([x - 1, 100, x, 108], fill=H_PAPER)
        d.rectangle([x - 2, 102, x + 1, 102], fill=H_PAPER)
    # the right window: the counter, heads against the dark glass
    d.rectangle([66, 96, 103, 118], fill=H_WALL_DK)
    pane(d, 67, 97, 102, 117)
    for x in (71, 81, 92):
        d.rectangle([x + 1, 104, x + 4, 109], fill=H_GLASS_LO); d.rectangle([x, 105, x + 5, 108], fill=H_GLASS_LO)
        d.rectangle([x - 2, 110, x + 7, 115], fill=H_GLASS_LO)
    d.rectangle([67, 115, 102, 117], fill=H_WALL)
    d.rectangle([67, 115, 102, 115], fill=H_WALL_HI)
    d.rectangle([84, 97, 84, 114], fill=H_WALL_DK)
    # crates of empties
    for j, y in enumerate((114, 105)):
        body, top, low = ((H_RED, H_RED_HI, H_RED_LO), (H_STONE, H_PAPER, H_STONE_LO))[j]
        d.rectangle([106, y, 117, y + 8], fill=body)
        d.rectangle([106, y, 117, y], fill=top)
        d.rectangle([108, y + 3, 110, y + 5], fill=H_EAVE); d.rectangle([113, y + 3, 115, y + 5], fill=H_EAVE)
        d.rectangle([106, y + 8, 117, y + 8], fill=low)
    # the row of lanterns under the eave, red and cream in turn
    d.rectangle([4, 81, 123, 81], fill=H_WALL_DK)
    for i, x in enumerate(range(6, 120, 13)):
        if i % 2 == 0:
            lantern_h(d, x, 82, 9, 12, H_RED, H_RED_HI, H_RED_LO)
        else:
            lantern_h(d, x, 82, 9, 12, H_PAPER, H_PAPER_HI, H_WALL_HI, H_RED)
    stone_foot(d, 0, 127)
    hl.outline(im)
    return im


def kissaten():
    """A kissaten, the old kind of coffee house: a flat roof, cream stucco with
    a COFFEE board and three windows with coloured top lights, a scalloped
    awning, brown tile below, siphons in the window and a case of wax samples
    (a cream soda, a pudding) by the door."""
    im, d = canvas(3, 4)                 # 96 x 128; the door is column 1 (x 32-63)
    px = im.load()
    roof_plan(im, 1, 2, 94, 34)
    d.rectangle([69, 11, 78, 20], fill=H_SLATE_LO)                # the flue from above, its shadow
    d.rectangle([67, 9, 75, 17], fill=H_SLATE_JOINT)
    d.rectangle([67, 9, 75, 9], fill=H_STONE); d.rectangle([67, 9, 67, 17], fill=H_STONE)
    d.rectangle([69, 11, 73, 15], fill=H_INK)
    # ---- the stucco front
    d.rectangle([3, 35, 92, 66], fill=H_PAPER)
    d.rectangle([3, 35, 92, 36], fill=H_REED)                     # the coping's shadow
    d.rectangle([3, 37, 3, 66], fill=H_PAPER_HI); d.rectangle([86, 37, 92, 66], fill=H_REED)
    d.rectangle([14, 38, 81, 48], fill=H_WALL_DK)                 # the board: a cup and the word
    d.rectangle([15, 39, 80, 47], fill=H_WALL_LO)
    d.rectangle([15, 39, 80, 39], fill=H_WALL)
    text(d, 'COFFEE', 37, 41, H_WALL_DK)
    text(d, 'COFFEE', 36, 40, H_PAPER)
    d.rectangle([20, 42, 26, 46], fill=H_PAPER); d.rectangle([27, 43, 28, 44], fill=H_PAPER)
    d.rectangle([21, 42, 25, 42], fill=H_WALL_DK)
    d.rectangle([19, 46, 28, 46], fill=H_PAPER_HI)
    tops = (H_RED, H_GREEN, H_INDIGO)
    for i, x0 in enumerate((9, 37, 65)):                          # three windows, coloured top lights
        d.rectangle([x0 - 1, 50, x0 + 20, 64], fill=H_WALL_DK)
        pane(d, x0, 54, x0 + 19, 63, step=7)
        for k in range(4):
            d.rectangle([x0 + k * 5, 51, x0 + k * 5 + 3, 52], fill=tops[(i + k) % 3])
        d.rectangle([x0, 53, x0 + 19, 53], fill=H_WALL_DK)
        d.rectangle([x0 + 9, 54, x0 + 10, 63], fill=H_WALL_DK)
        d.rectangle([x0 - 2, 65, x0 + 21, 65], fill=H_REED)
    # ---- the awning, green and cream, scalloped, its shadow on the tile
    for x in range(1, 95):
        s = (x - 1) % 8
        green = ((x - 1) // 8) % 2 == 0
        hem = 78 + (1 if 1 <= s <= 6 else 0) + (1 if 2 <= s <= 5 else 0)
        d.rectangle([x, 67, x, hem], fill=H_GREEN if green else H_PAPER)
        d.rectangle([x, 67, x, 67], fill=H_GREEN_HI if green else H_PAPER_HI)
        d.rectangle([x, 74, x, 74], fill=H_GREEN_LO if green else H_REED)
        d.rectangle([x, hem, x, hem], fill=H_GREEN_LO if green else H_REED)
    # ---- the ground floor in brown tile courses
    for y in range(81, 124):
        for x in range(3, 93):
            if (y - 81) % 5 == 4 or (x + ((y - 81) // 5) % 2 * 5) % 10 == 0:
                c = H_WALL_DK
            elif x >= 86:
                c = H_WALL_LO
            else:
                c = H_WALL_HI if (y - 81) % 5 == 0 else H_WALL
            px[x, y] = c
    d.rectangle([3, 81, 92, 82], fill=H_WALL_DK)                  # the awning's shadow
    d.rectangle([6, 88, 29, 116], fill=H_WALL_DK)                 # the window: two siphons, a lace half-curtain
    pane(d, 7, 89, 28, 115)
    for x in (10, 20):
        d.rectangle([x + 2, 92, x + 2, 104], fill=H_STONE)
        d.rectangle([x + 1, 92, x + 4, 96], fill=H_STONE); d.rectangle([x + 1, 92, x + 1, 92], fill=H_PAPER_HI)
        d.rectangle([x + 1, 99, x + 4, 104], fill=H_WALL); d.rectangle([x, 100, x + 5, 103], fill=H_WALL)
        d.rectangle([x + 1, 100, x + 1, 101], fill=H_WALL_HI)
        d.rectangle([x - 1, 105, x + 6, 105], fill=H_WALL_DK)
    d.rectangle([7, 106, 28, 115], fill=H_PAPER)
    for x in range(7, 29):
        if x % 4 == 1:
            d.rectangle([x, 106, x, 106], fill=H_GLASS)
        if (x + 2) % 4 == 0:
            d.rectangle([x, 109, x, 109], fill=H_REED); d.rectangle([x + 1, 112, x + 1, 112], fill=H_REED)
    d.rectangle([17, 89, 17, 105], fill=H_WALL_DK)
    d.rectangle([34, 86, 61, 123], fill=H_WALL_DK)                # the door: timber, a pane with clipped corners
    d.rectangle([36, 88, 59, 123], fill=H_WALL)
    d.rectangle([36, 88, 36, 123], fill=H_WALL_HI); d.rectangle([57, 89, 59, 123], fill=H_WALL_LO)
    d.rectangle([41, 92, 54, 110], fill=H_WALL_DK)
    pane(d, 42, 93, 53, 109, step=7)
    for x, y in ((42, 93), (53, 93), (42, 109), (53, 109)):
        d.rectangle([x, y, x, y], fill=H_WALL_DK)
    d.rectangle([41, 113, 54, 120], fill=H_WALL_LO); d.rectangle([41, 113, 54, 113], fill=H_WALL_HI)
    d.rectangle([55, 106, 56, 108], fill=H_STONE)
    d.rectangle([65, 89, 90, 115], fill=H_WALL_DK)                # the sample case
    pane(d, 66, 90, 89, 114)
    d.rectangle([66, 102, 89, 103], fill=H_PAPER)
    d.rectangle([68, 95, 71, 101], fill=H_GREEN); d.rectangle([68, 93, 71, 94], fill=H_PAPER_HI)   # a cream soda
    d.rectangle([69, 92, 69, 92], fill=H_RED)
    d.rectangle([75, 98, 80, 101], fill=H_WALL_HI); d.rectangle([75, 97, 80, 97], fill=H_WALL_LO)   # a pudding
    d.rectangle([84, 96, 87, 101], fill=H_PAPER); d.rectangle([84, 96, 87, 97], fill=H_WALL_LO)    # a coffee
    d.rectangle([68, 108, 75, 111], fill=H_PAPER); d.rectangle([67, 109, 76, 110], fill=H_PAPER)   # napolitan
    d.rectangle([69, 108, 73, 109], fill=H_RED)
    d.rectangle([80, 108, 87, 111], fill=H_PAPER); d.rectangle([79, 109, 88, 110], fill=H_PAPER)   # toast
    d.rectangle([81, 108, 85, 109], fill=H_WALL_HI)
    d.rectangle([65, 116, 90, 123], fill=H_WALL_LO)
    d.rectangle([65, 116, 90, 116], fill=H_WALL)
    d.rectangle([2, 124, 93, 127], fill=H_SLATE_JOINT); d.rectangle([2, 124, 93, 124], fill=H_STONE)
    hl.outline(im)
    return im


def yakitori():
    """A yakitori counter: one low storey under black tiles, a great red
    lantern with its name, a short noren, skewers over the coals in the open
    window, a steel flue."""
    im, d = canvas(3, 3)                 # 96 x 96; the door is column 1 (x 32-63)
    d.rectangle([74, 4, 83, 22], fill=H_STONE)                    # the flue
    d.rectangle([74, 4, 75, 22], fill=H_STONE_HI); d.rectangle([81, 5, 83, 22], fill=H_STEEL)
    d.rectangle([72, 1, 85, 3], fill=H_STEEL); d.rectangle([72, 1, 85, 1], fill=H_STONE_HI)
    kawara(im, d, 0, 16, 95, 30)
    d.rectangle([2, 31, 93, 91], fill=H_WALL_LO)
    for x in range(8, 88, 6):
        d.rectangle([x, 33, x, 91], fill=H_WALL_DK)
    d.rectangle([2, 31, 93, 32], fill=H_WALL_DK)
    d.rectangle([2, 33, 2, 91], fill=H_WALL); d.rectangle([88, 33, 93, 91], fill=H_WALL_DK)
    # ---- the great red lantern
    d.rectangle([12, 35, 19, 36], fill=H_EAVE)
    d.rectangle([10, 37, 21, 38], fill=H_LAMP)
    for y in range(39, 84):
        w = math.isqrt(max(0, 100 * 22 * 22 - 100 * (y - 61) ** 2)) // 22
        c = H_RED_LO if (y - 39) % 5 == 4 else H_RED
        d.rectangle([15 - w, y, 16 + w, y], fill=c)
        d.rectangle([15 - w, y, 16 - w, y], fill=H_RED_HI)
        d.rectangle([16 + w, y, 16 + w, y], fill=H_RED_LO)
    d.rectangle([10, 84, 21, 85], fill=H_LAMP)
    d.rectangle([12, 86, 19, 87], fill=H_EAVE)
    d.rectangle([11, 44, 20, 78], fill=H_RED)
    kana(d, ['ya', 'ki', 'to', 'ri'], 13, 46, H_RED_LO, vertical=True)
    kana(d, ['ya', 'ki', 'to', 'ri'], 12, 45, H_PAPER, vertical=True)
    # ---- the door under a short noren
    d.rectangle([32, 38, 63, 91], fill=H_INK)
    d.rectangle([33, 39, 62, 91], fill=H_GLASS)
    lattice_doors(d, 34, 56, 61, 91, H_WALL_DK, H_WALL_LO)
    noren_h(d, 34, 41, 61, 58, H_INDIGO, H_GLARE, H_EDGE, slits=3)
    for x in (37, 44, 51, 58):                                    # a skewer on each panel
        d.rectangle([x, 45, x, 55], fill=H_PAPER)
        d.rectangle([x - 1, 46, x + 1, 47], fill=H_KAKI); d.rectangle([x - 1, 49, x + 1, 50], fill=H_PAPER)
        d.rectangle([x - 1, 52, x + 1, 53], fill=H_KAKI)
    # ---- the open window: the cook, skewers over the coals
    d.rectangle([65, 42, 90, 74], fill=H_WALL_DK)
    d.rectangle([66, 43, 89, 62], fill=H_GLASS)
    d.rectangle([66, 43, 89, 44], fill=H_GLASS_LO)
    d.rectangle([75, 47, 79, 52], fill=H_GLASS_LO); d.rectangle([74, 48, 80, 51], fill=H_GLASS_LO)   # the cook
    d.rectangle([71, 54, 83, 62], fill=H_GLASS_LO); d.rectangle([73, 53, 81, 53], fill=H_GLASS_LO)
    d.rectangle([74, 48, 80, 48], fill=H_PAPER)
    d.rectangle([66, 63, 89, 65], fill=H_EAVE)
    for x in range(68, 89, 4):
        d.rectangle([x, 57, x, 65], fill=H_PAPER)
        d.rectangle([x, 59, x, 59], fill=H_WALL_HI); d.rectangle([x, 61, x, 61], fill=H_WALL)
        d.rectangle([x, 63, x, 63], fill=H_WALL_HI)
    d.rectangle([66, 66, 89, 69], fill=H_EAVE)                    # the coals
    for x, y, c in ((68, 67, H_KAKI), (73, 68, H_RED), (77, 66, H_KAKI), (82, 67, H_RED), (86, 68, H_KAKI)):
        d.rectangle([x, y, x, y], fill=c)
    d.rectangle([66, 70, 89, 73], fill=H_WALL_DK)
    d.rectangle([64, 75, 91, 78], fill=H_WALL); d.rectangle([64, 75, 91, 75], fill=H_WALL_HI)
    d.rectangle([64, 78, 91, 78], fill=H_WALL_DK)
    d.rectangle([68, 81, 80, 90], fill=H_INDIGO); d.rectangle([68, 81, 80, 81], fill=H_GLARE)    # a crate
    d.rectangle([70, 84, 72, 86], fill=H_EAVE); d.rectangle([76, 84, 78, 86], fill=H_EAVE)
    d.rectangle([68, 90, 80, 90], fill=H_EDGE)
    stone_foot(d, 0, 95, 92, 95)
    hl.outline(im)
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
    """A samurai house of the Nagamachi court: a deep roof of black tiles over
    a low plastered storey squared off by dark posts and a tie, a pent roof,
    earthen walls over boards on river stones, paper screens, a barred window,
    the entrance."""
    im, d = canvas(5, 4)                 # 160 x 128; the door is column 2 (x 64-95)
    px = im.load()
    kawara(im, d, 0, 6, 159, 40)                                  # the main roof
    # ---- the plastered storey under it, posts and a tie
    d.rectangle([4, 41, 155, 58], fill=H_PAPER)
    d.rectangle([4, 41, 155, 42], fill=H_WALL_DK)                 # the eave's shade
    d.rectangle([4, 43, 155, 43], fill=H_PAPER_HI)
    d.rectangle([4, 55, 155, 58], fill=H_REED)
    d.rectangle([140, 44, 155, 54], fill=H_REED)                  # the far end in shade
    for x in range(4, 156, 16):
        d.rectangle([x, 43, x + 1, 58], fill=H_WALL_LO); d.rectangle([x + 1, 43, x + 1, 58], fill=H_WALL_DK)
    d.rectangle([154, 43, 155, 58], fill=H_WALL_DK)
    d.rectangle([4, 49, 155, 49], fill=H_WALL_LO); d.rectangle([4, 50, 155, 50], fill=H_WALL_DK)
    d.rectangle([76, 44, 83, 48], fill=H_WALL_DK)                 # a vent in the middle bay
    for x in (78, 81):
        d.rectangle([x, 44, x, 48], fill=H_PAPER)
    kawara(im, d, 0, 59, 159, 68)                                 # the pent roof
    # ---- the ground floor: earth over boards
    for y in range(69, 100):
        for x in range(4, 156):
            k = h3(x % 32, y, 3)
            far = x >= 146
            if y <= 70:
                c = H_WALL_LO
            elif k < 20:
                c = H_EARTH if far else H_PAPER
            elif k < 60 or far:
                c = H_EARTH
            else:
                c = H_REED
            px[x, y] = c
    d.rectangle([4, 100, 155, 119], fill=H_WALL_LO)
    for x in range(4, 156):
        if (x - 4) % 6 == 0:
            d.rectangle([x, 101, x, 119], fill=H_WALL_DK)
        elif (x - 4) % 6 == 1:
            d.rectangle([x, 101, x, 119], fill=H_WALL)
    d.rectangle([4, 100, 155, 100], fill=H_WALL_HI)
    for y0, off in ((120, 0), (124, 5)):                          # river stones
        for x0 in range(4 - off, 156, 10):
            a, b = max(4, x0), min(155, x0 + 8)
            if b < a:
                continue
            d.rectangle([a, y0, b, y0 + 3], fill=H_STONE)
            d.rectangle([a, y0, b, y0], fill=H_STONE_HI); d.rectangle([a, y0, a, y0 + 3], fill=H_STONE_HI)
            d.rectangle([a, y0 + 3, b, y0 + 3], fill=H_STONE_LO)
            if b < 155:
                d.rectangle([b + 1, y0, b + 1, y0 + 3], fill=H_STONE_LO)
    d.rectangle([9, 76, 57, 112], fill=H_WALL_LO)                 # paper screens on the veranda, unlit
    for i in range(4):
        x0 = 11 + i * 11
        d.rectangle([x0, 78, x0 + 9, 104], fill=H_PAPER)
        d.rectangle([x0, 78, x0 + 9, 78], fill=H_PAPER_HI)
        d.rectangle([x0 + 9, 79, x0 + 9, 104], fill=H_REED)
        d.rectangle([x0 + 5, 78, x0 + 5, 104], fill=H_WALL_LO)
        for y in (85, 91, 97):
            d.rectangle([x0, y, x0 + 9, y], fill=H_WALL_LO)
        d.rectangle([x0, 105, x0 + 9, 110], fill=H_WALL_DK)
    d.rectangle([7, 113, 59, 116], fill=H_WALL); d.rectangle([7, 113, 59, 113], fill=H_WALL_HI)
    d.rectangle([7, 117, 59, 118], fill=H_WALL_DK)
    d.rectangle([109, 79, 147, 93], fill=H_WALL_LO)               # the barred window, dark behind
    d.rectangle([110, 80, 146, 92], fill=H_GLASS)
    d.rectangle([110, 80, 146, 80], fill=H_GLASS_LO)
    for x in range(112, 146, 4):
        d.rectangle([x, 80, x + 1, 92], fill=H_PAPER); d.rectangle([x + 1, 80, x + 1, 92], fill=H_REED)
    d.rectangle([108, 94, 148, 94], fill=H_EARTH)
    # ---- the entrance
    d.rectangle([62, 72, 97, 78], fill=H_WALL_LO)
    d.rectangle([62, 72, 97, 72], fill=H_WALL_HI); d.rectangle([62, 78, 97, 78], fill=H_WALL_DK)
    d.rectangle([65, 79, 94, 121], fill=H_INK)
    lattice_doors(d, 66, 80, 93, 119, H_WALL_DK, H_WALL_LO)
    d.rectangle([66, 120, 93, 121], fill=H_GLASS)
    for x0 in (62, 95):
        d.rectangle([x0, 79, x0 + 2, 121], fill=H_WALL_LO)
        d.rectangle([x0, 79, x0, 121], fill=H_WALL_HI); d.rectangle([x0 + 2, 79, x0 + 2, 121], fill=H_WALL_DK)
    d.rectangle([60, 120, 99, 123], fill=H_STONE_HI)              # the stone step
    d.rectangle([60, 120, 99, 120], fill=H_STONE_LT); d.rectangle([60, 123, 99, 123], fill=H_STONE)
    d.rectangle([101, 82, 106, 98], fill=H_PAPER)                 # the family's name
    d.rectangle([101, 82, 101, 98], fill=H_PAPER_HI); d.rectangle([106, 82, 106, 98], fill=H_EARTH)
    for y in (85, 89, 93):
        d.rectangle([103, y, 104, y + 2], fill=H_WALL_DK)
    for x in (4, 154):                                            # corner posts
        d.rectangle([x, 69, x + 1, 119], fill=H_WALL_LO); d.rectangle([x, 69, x, 119], fill=H_WALL_HI)
    hl.outline(im)
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
     'and blue block, a white-plaster storey with barred windows and a namako dado, a hipped lead-tile roof seen from above; '
     'iron-bound posts, the leaves folded back, a plum crest on the lintel. Walk through the middle two '
     'cells. The castle wall joins it flush on either side.'),
    ('kanazawa-castle-turret_0_0', castle_turret, (4, 5), 'Kanazawa Castle', dict(
        solid=rows(4, 3, 4)),
     'A yagura: battered stone base, a white first storey with a namako dado and a bay window under a bowed '
     'lead hood, a lead pent roof seen from above, a smaller white second storey, a hipped lead roof seen from '
     'above with a plastered gable. No door.'),
    ('kanazawa-castle-storehouse_0_0', castle_storehouse, (6, 3), 'Kanazawa Castle', dict(
        door=[[2, 2]], solid=rows(6, 1, 2)),
     'A nagaya for the castle terrace, so it is not an empty lawn: one long low storey on a stone foot, '
     'white plaster with barred windows and a namako band, a long hipped lead roof seen from above, iron-bound doors under a small '
     'lead hood (column 2; leave it sealed or open it).'),
    ('kanazawa-castle-wall_0_0', lambda: castle_wall('h'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     "The long white wall running east-west, to replace sendai-earthen-wall: lead coping, white plaster, a "
     'band of namako (a white diagonal lattice on slate), a fitted stone base. Tiles left-right; the bottom '
     'cell is solid.'),
    ('kanazawa-castle-wall-corner-e_0_0', lambda: castle_wall('corner-e'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The east end of an east-west run where the wall turns north: the face stops at long-and-short corner '
     'stones (in shade) and the lead coping turns up the map over a hip. Put kanazawa-castle-wall-v in the '
     'cells above it (north).'),
    ('kanazawa-castle-wall-corner-w_0_0', lambda: castle_wall('corner-w'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The west end where the wall turns north, drawn for its own side (lit corner stones, the lit fall of '
     'the coping), not a mirror of -corner-e.'),
    ('kanazawa-castle-wall-v_0_0', lambda: castle_wall('v'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     'The wall running north-south. Top cell: its lead coping seen from above (the lit west fall, the '
     'ridge, the east fall in shade, 28px wide). Bottom cell: the wall\'s south end (plaster, namako band, '
     'stone foot). Stacked down the map, each piece\'s coping covers the end of the piece north of it, so a '
     'run is one roof with a wall face and foot under its last piece. It joins the coping of a corner piece '
     'south of it; running south from an east-west wall it comes forward over that wall\'s face.'),
    ('kanazawa-castle-wall-end_0_0', lambda: castle_wall('end'), (1, 2), 'Kanazawa Castle', dict(
        solid=[[0, 1]]),
     "The same as -v with the coping hipped at its south end: the last piece of a north-south run."),
    ('kenrokuen-kotoji_0_0', kotoji, (2, 3), 'Kenrokuen', dict(
        solid=rows(2, 2, 2), lit=[[1.0, 1.0, WARM_HEX]]),
     'The Kotoji lantern, the garden\'s emblem, at twice the old sprite\'s height: a granite lantern on two '
     'bowed legs, the long one on a stone in the shallows and the short one on a rock on the bank, lichen on '
     'its roof, its light box unlit, dim gold. Stand it on the pond\'s edge with its left column over the water\'s rim.'),
    ('kenrokuen-kotoji-water_0_0', lambda: kotoji(True), (2, 3), 'Kenrokuen', dict(
        solid=rows(2, 2, 2), lit=[[1.0, 1.0, WARM_HEX]]),
     'The same lantern with its long leg going down into the pond (a ring on the water round it, no stepping '
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
     'The tea house on the pond (Uchihashi-tei): a hipped cedar-shingle roof seen from above, moss in its '
     'courses, paper screens either side of an open '
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
     'Teahouse front, 3 cells, in the house look: the pack\'s kawara in straight courses, an upper floor '
     'screened in lattice over dark glass with two reed blinds, a balcony rail, a kawara pent roof, lattice '
     'bays, an indigo noren with a cream mark over dark lattice doors, a white paper lantern banded in dim '
     'gold. The three fronts tile side by side, each with its ridge at its own height and in its own '
     'bengara.'),
    ('chaya-front-b_0_0', chaya('b'), (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3), lit=[[1.5, 1.6, WARM_HEX], [1.5, 3.4, WARM_HEX]]),
     'Teahouse front a tone darker: three lattice windows over dark glass, one with a reed blind, a short '
     'green noren over dark lattice doors up a stone step, a red lantern on a bracket, the house\'s name '
     'board.'),
    ('chaya-front-c_0_0', chaya('c'), (3, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(3, 2, 3), lit=[[0.9, 1.6, WARM_HEX], [2.1, 1.6, WARM_HEX], [1.5, 3.5, WARM_HEX]]),
     'Teahouse front in the red bengara: two wide windows of dark glass upstairs between shutter boxes, a '
     'long persimmon noren, and instead of a second lattice bay a boarded wall with a small window and a '
     'bench under a red cloth for tea outside.'),
    ('chaya-gold-leaf-shop_0_0', gold_shop, (4, 4), 'Higashi Chaya', dict(
        door=[[1, 3]], solid=rows(4, 2, 3), lit=[[2.6, 3.2, WARM_HEX], [1.5, 3.4, WARM_HEX]]),
     'The gold-leaf shop: kawara roofs, a storehouse upper wall laid with squares of gold leaf (the far side '
     'in shade), a black HAKU (leaf) board, black lacquer below with a gilded screen behind the glass of one '
     'window and gilded bowls and boxes in the other, a cream noren with one gold square, and a sign of a '
     'soft-serve cone wrapped in gold leaf.'),
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
     'The phonograph museum the posts name: a flat roof seen from above with a skylight, a plain stone front '
     'in courses under a cornice, a roundel with a brass horn gramophone and notes, a PHONO board, slit '
     'windows, and on the ground floor a window with a gramophone and records, glass doors and a record '
     'poster.'),
    ('katamachi-whisky-bar_0_0', whisky_bar, (3, 5), 'Katamachi', dict(
        door=[[1, 4]], solid=rows(3, 3, 4),
        lit=[[0.65, 2.6, AMBER_HEX], [2.3, 2.6, AMBER_HEX], [0.6, 4.2, AMBER_HEX], [1.5, 2.7, AMBER_HEX]]),
     'The whisky bar: a flat roof seen from above with a water tank and a flue on it, dark brick, a painted '
     'board of a glass of whisky on ice (MALT BAR), two windows with stepped arched heads and bottles dark '
     'against the glass, a dim gold lamp on an iron bracket between them, a green canopy, a timber door, a '
     'bottle window, a cask on end and a chalk board. No upright sign.'),
    ('katamachi-izakaya_0_0', izakaya, (4, 4), 'Katamachi', dict(
        door=[[1, 3]], solid=rows(4, 2, 3),
        lit=[[0.6, 3.3, WARM_HEX], [2.6, 3.3, WARM_HEX], [1.5, 3.5, WARM_HEX], [2.0, 2.8, RED_HEX]]),
     'The all-you-can-drink izakaya: kawara roofs, a big unlit board in dim gold reading nomihodai in kana '
     'with a mug of beer and a red SAKE tab, a row of red and cream paper lanterns under the eave, a red '
     'noren over dark lattice doors, the menu on paper strips in one window and heads at the counter in the '
     'other, crates of empties.'),
    ('katamachi-kissaten_0_0', kissaten, (3, 4), 'Katamachi', dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[[0.55, 3.2, WARM_HEX], [1.5, 3.2, WARM_HEX], [2.4, 3.2, WARM_HEX], [1.5, 1.75, WARM_HEX]]),
     'A kissaten, the old kind of coffee house: a flat roof seen from above with its flue, cream stucco with '
     'a COFFEE board and three windows with coloured top lights, a green and cream scalloped awning, brown '
     'tile below, siphons and a lace half-curtain in the window, a timber door with a clipped-corner pane, a '
     'case of wax samples.'),
    ('katamachi-yakitori_0_0', yakitori, (3, 3), 'Katamachi', dict(
        door=[[1, 2]], solid=rows(3, 1, 2),
        lit=[[0.5, 1.9, RED_HEX], [2.4, 2.05, COAL_HEX], [1.5, 2.4, WARM_HEX]]),
     'A yakitori counter, one low storey: kawara and a steel flue, a great red lantern banded in dim gold '
     'reading yakitori in kana, a short indigo noren with skewers on it over dark lattice doors, an open '
     'window with the cook dark against it, skewers and a few coals, a beer crate.'),
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
     'The samurai house for the court behind the gate: a deep kawara roof over a low plastered storey '
     'squared off by dark posts and a tie, a kawara pent roof, earthen walls over boards on river stones, '
     'unlit paper screens on a veranda, a barred dark window, dark lattice doors up a stone step. The door '
     'is the middle cell.'),
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


def save_png(im, path):
    """Write im unless the file already holds these pixels, so a rerun leaves the
    committed PNGs byte for byte as they are whatever Pillow's encoder does."""
    if os.path.exists(path):
        with Image.open(path) as old:
            if old.size == im.size and old.convert('RGBA').tobytes() == im.convert('RGBA').tobytes():
                return False
    im.save(path)
    return True


def main():
    built = build()
    for key, im in built.items():
        save_png(im, f'{SPR}/{key}.png')
        if 'autotile' not in key:
            print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    print(', '.join(f[0] for f in FAMILIES) + f': {len(ROLES)} roles each')
    for flag, fn in (('--sheet', sheet), ('--scenes', scenes), ('--manifest', manifest)):
        if flag in sys.argv:
            fn(built, sys.argv[sys.argv.index(flag) + 1])


if __name__ == '__main__':
    main()
