#!/usr/bin/env python3
"""generate_sendai_town_art.py — Sendai's own town pieces, drawn ahead of its rebuild (issue #219).

tools/generate_sendai_art.py gave Sendai its landmarks (the Masamune statue,
Zuihoden, the kiln, the bay's islets). Everything between them is shared kit:
the station is a townhouse, the centre is the standard road cross, and the
samurai quarter is the machiya, townhouses, earthen wall and gate that other
towns use too. These are the pieces the rebuild replaces that kit with, in the
style of generate_sapporo_art.py / generate_kanazawa_art.py: shaded pixel art
in the GuttyKreum palette, drawn at 32px per cell and pixel-doubled, lit from
the west, a 1px ink outline. Late October: autumn colour, no snow.

Sendai's look is the Date clan's: BLACK LACQUER AND GOLD under verdigris copper
and thatch, on cut grey stone. Nothing here is Kanazawa's white plaster, ochre
earth, straw mats or dark-red lattice.

Station front
  sendai-station-front_0_0     9x5  the long cream station: arched windows, a
                                    stained-glass window over the doors (the
                                    meeting spot), the deck's rail along it
  sendai-deck-span_0_0         3x3  the elevated pedestrian deck, east-west: its
                                    rail at the station's, a pier, shadow under
  sendai-deck-span-v_0_0       1x3  the deck running north-south (a spur)
  sendai-deck-end-e/-w/-s_0_0  1x3  its ends, the rail returned over a pier
  sendai-deck-stair-e/-w_0_0   3x3  the stair down, seen from its side
  sendai-tanabata-a_0_0        1x3  a bamboo pole with one great kusudama and
  sendai-tanabata-b_0_0        3x3  its paper streamers; a pair on a cross pole
Downtown / Jozenji-dori
  sendai-zelkova-a/-b_0_0      3x4  keyaki in autumn gold, the avenue's trees
                                    (a broad one and a narrower, redder one)
  sendai-jozenji-statue_0_0    2x3  a bronze dancer on a block, for the median
  sendai-gyutan_0_0            4x4  a beef-tongue grill: charred timber, coals
                                    in the window, a flue with smoke
  sendai-zunda_0_0             3x3  a zunda sweet shop in sage green
  sendai-izakaya_0_0           3x4  an alley izakaya: lanterns, a long noren
  sendai-midrise_0_0           4x6  a pale-tile store, in place of the shared towers
  sendai-arcade-gate_0_0       4x5  the covered street's mouth: a tall portal
                                    under the gable of a pitched glass roof
  sendai-arcade-roof_0_0       4x4  a length of that roof, its glass see-through
  sendai-kokeshi-shop_0_0      3x3  the arcade's shops: kokeshi dolls, and
  sendai-sasakama-shop_0_0     3x3  bamboo-leaf fish cakes toasting
Samurai quarter
  sendai-samurai-gate_0_0      4x3  a residence gate: black lacquer, gold
                                    fittings, a copper roof, an invented mon
  sendai-board-fence*_0_0           black board-and-batten fence on cut stone:
                                    straight and -wicket (1x2); -corner-e,
                                    -corner-w, -v, -end (1x3: a north-south
                                    run is seen end-on)
  sendai-samurai-house-a_0_0   5x4  a thatched house, an engawa and shoji
  sendai-samurai-house-b_0_0   4x4  a smaller one, a shingle pent roof over
                                    its engawa
  sendai-samurai-store_0_0     3x3  a thatched outbuilding, firewood under its eave
  sendai-well_0_0              1x2  a roofed stone well
  sendai-propped-pine_0_0      3x3  an old pine, its long limb on props
  sendai-kabuto-stand_0_0      2x3  armour on its chest before a gold screen:
                                    the crescent-moon helmet (the hero prop)
  sendai-andon-lamp-post_0_0   1x2  the quarter's lamp (it gets the lamp halo)
  sendai-stepping-stone-a/-b/-c 1x1 stones to lay on the lane's gravel
Distillery yard
  sendai-distillery-warehouse_0_0 6x4  a red-brick still house; a copper pot
                                    still through its arched window, its own door
  sendai-cask-rack_0_0         3x2  five casks end-on, stacked on chocks
  sendai-red-maple_0_0         3x4  a big maple in deep red
  sendai-yamadera_0_0          6x6  the hill behind, a backdrop: a wooded
                                    mountain, two crags, a red hall, a lookout
Matsushima bay (land side)
  sendai-godaido_0_0           4x4  Godaido hall on its rock islet, a stone quay
  sendai-red-bridge_0_0        2x1  its vermilion bridge (flat, walked on)
  sendai-red-bridge-head_0_0   1x1  the bridge's first cell, with newel posts
  sendai-cruise-booth_0_0      3x3  the bay cruise's ticket booth
  sendai-oyster-shack_0_0      4x3  a grilled-oyster shack
  sendai-bay-lamp-post_0_0     1x2  the bay front's lamp (it gets the lamp halo)
Ground (9 autotile roles each, opaque)
  sendai-plaza-autotile_*           the station plaza: slabs in brick bands
  sendai-jozenji-autotile_*         the avenue's median walk: pavers, leaves
  sendai-arcade-floor-autotile_*    the arcade's polished tile
  sendai-samurai-lane-autotile_*    plain raked gravel, a stone kerb
  sendai-brick-yard-autotile_*      the distillery yard's worn brick
  sendai-boardwalk-autotile_*       the bay's timber boardwalk

This tool writes the PNGs into assets/sprites/ and NOTHING else: no config.json,
no prefabs. The pub is not redrawn (sendai-pub_0_0 is already its own).

Deterministic (no randomness, no clock): two runs give byte-identical files.
Needs Pillow. Run from gamev2/:
    python3 tools/generate_sendai_town_art.py [--sheet sheet.png] [--scenes dir] [--manifest out.json]
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import (rgb, canvas, outline, CLEAR, INK, NAVY,                     # noqa: E402
                               RED, RED_HI, RED_LO, RED_DK, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK,
                               WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, GOLD, AMBER)
from generate_sendai_art import (blob, trunk, rock, SLATE, SLATE_HI, SLATE_LO, PINE, PINE_HI, PINE_LO,   # noqa: E402
                                 PINE_DK, BARK, BARK_LO, LACQUER, LACQUER_HI, LACQUER_LO,
                                 GOLD_HI, GOLD_LO, ROCK, ROCK_HI, ROCK_LO, ROCK_DK,
                                 BRONZE, BRONZE_HI, BRONZE_LO)
from generate_sapporo_art import brick, glass_door, lantern, BRICK, BRICK_HI, BRICK_LO, BRICK_DK   # noqa: E402
from generate_kanazawa_art import text, kana, text_w, h3, shade, curve_rows, night, roof               # noqa: E402

SPR = 'assets/sprites'
ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
         'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')

# ---- Sendai's colours -------------------------------------------------------------
LQ, LQ_HI, LQ_LO, LQ_MID = LACQUER, LACQUER_HI, LACQUER_LO, rgb('2e2f3e')
COPPER_P = (rgb('6fa593'), rgb('4d8173'), rgb('a5d1bb'), rgb('335a55'))      # verdigris: light, seam, lit, deep
THATCH, THATCH_HI, THATCH_LO, THATCH_DK = rgb('b3956a'), rgb('d6bd8c'), rgb('8c7350'), rgb('5f4d3b')
SHINGLE, SHINGLE_HI, SHINGLE_LO, SHINGLE_DK = rgb('9a948f'), rgb('c4beb4'), rgb('77716f'), rgb('55505a')
ASH, ASH_HI, ASH_LO, ASH_DK = rgb('9aa0ae'), rgb('c3c8d2'), rgb('747a8c'), rgb('525769')     # cut grey stone
PAPER, PAPER_LO = rgb('f1e9d6'), rgb('cfc4aa')
WARM, LIT = rgb('f6dc8c'), rgb('f2c66a')
KEY, KEY_HI, KEY_LO, KEY_DK = rgb('e0a63a'), rgb('f6d66a'), rgb('b8792c'), rgb('8a5526')     # keyaki in gold
RUS, RUS_HI, RUS_LO = rgb('d0853a'), rgb('eeb054'), rgb('a05c2a')                             # and in russet
MAP, MAP_HI, MAP_LO, MAP_DK = rgb('c23a3c'), rgb('e8684a'), rgb('8e2a36'), rgb('641f2e')     # maple red
ZBARK, ZBARK_HI, ZBARK_LO = rgb('8a8078'), rgb('ada39a'), rgb('5f5753')                       # keyaki's grey bark
STN, STN_HI, STN_LO, STN_DK = rgb('ead9a8'), rgb('f8eecb'), rgb('cdb77f'), rgb('a38c5c')     # the station's tile
UMBER, UMBER_LO = rgb('6e4a3a'), rgb('4c332c')
ZUN, ZUN_HI, ZUN_LO, ZUN_DK = rgb('bcd3ac'), rgb('dde9d0'), rgb('95b189'), rgb('5f8763')     # zunda green
CU, CU_HI, CU_LO, CU_DK = rgb('c9793f'), rgb('f4bd7c'), rgb('96502e'), rgb('63351f')         # polished copper
COAL, EMBER = rgb('f0903a'), rgb('d9482e')
VERM, VERM_HI, VERM_LO = rgb('d4503a'), rgb('ee7a5c'), rgb('9c3628')                          # vermilion
SOOT = rgb('2b2a30')
CHAR, CHAR_HI, CHAR_LO = rgb('3a3336'), rgb('554a4c'), rgb('241f23')                          # charred cedar
SEA_BLUE, SEA_HI, SEA_DK = rgb('3f6aa8'), rgb('79b4ee'), rgb('2b4a80')
WARM_HEX, COAL_HEX, CU_HEX, RED_HEX = '#f6dc8c', '#f0903a', '#f4bd7c', '#d16b56'

GYU = ['.#.#...', '.#####.', '#..#...', '#######', '...#...', '...#...', '...#...']      # 牛, hand-set


# ---- helpers ----------------------------------------------------------------------
def bar(d, x0, y0, x1, y1, base, hi=None, lo=None):
    """A lit block: a highlight down its west edge, shade down its east."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    if hi:
        d.line([(x0, y0), (x0, y1)], fill=hi)
    if lo:
        d.line([(x1, y0), (x1, y1)], fill=lo)


def glyph(d, rows, x, y, fill, scale=1):
    for gy, row in enumerate(rows):
        for gx, ch in enumerate(row):
            if ch == '#':
                d.rectangle([x + gx * scale, y + gy * scale, x + gx * scale + scale - 1, y + gy * scale + scale - 1],
                            fill=fill)


def puff(im, cx, cy, r, col=(236, 236, 240), a=120):
    """A soft puff of smoke or steam, blended over what is drawn."""
    ov = Image.new('RGBA', im.size, CLEAR)
    od = ImageDraw.Draw(ov)
    od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    od.ellipse([cx - r + 1, cy - r, cx + r - 2, cy + r - 2], fill=(255, 255, 255, min(255, a + 40)))
    im.alpha_composite(ov)


def grounded(im, ellipses=(), rects=(), a=90, leaves=None, polys=()):
    """Lay soft ground shadows UNDER a finished (outlined) sprite, so the ink
    outline does not ring them. rects are (x0, y0, x1, y1[, alpha]); polys are
    (points, alpha)."""
    base = Image.new('RGBA', im.size, CLEAR)
    bd = ImageDraw.Draw(base)
    for box in ellipses:
        bd.ellipse(list(box), fill=(30, 50, 70, a))
    for box in rects:
        bd.rectangle(list(box[:4]), fill=(20, 26, 50, box[4] if len(box) > 4 else a))
    for pts, pa in polys:
        bd.polygon(list(pts), fill=(20, 26, 50, pa))
    if leaves:
        x0, x1, y0, y1, cols, n, seed = leaves
        for i in range(n):                                        # leaves lying under a tree
            x = x0 + h3(i, seed, 3) % max(1, x1 - x0)
            y = y0 + h3(seed, i, 8) % max(1, y1 - y0)
            bd.point((x, y), fill=cols[i % len(cols)])
            if i % 3 == 0:
                bd.point((x + 1, y), fill=cols[(i + 1) % len(cols)])
    base.alpha_composite(im)
    return base


def lacquer_boards(d, x0, y0, x1, y1, batten=8, off=3, studs=False):
    """Shitami-ita in black: lapped boards 4px deep, each with a lit upper
    arris and a shadow under its lap, held by thin battens."""
    for y in range(y0, y1 + 1):
        k = (y - y0) % 4
        c = rgb('3d3f54') if k == 0 else (LQ_LO if k == 3 else (LQ_MID if k == 1 else LQ))
        d.line([(x0, y), (x1, y)], fill=c)
    for x in range(x0, x1 + 1):
        if (x - off) % batten == 0:
            d.line([(x, y0), (x, y1)], fill=rgb('474a63'))
            if x + 1 <= x1:
                d.line([(x + 1, y0), (x + 1, y1)], fill=LQ_LO)
            if studs:
                d.point((x, y0 + 2), fill=GOLD_HI); d.point((x, y1 - 2), fill=GOLD)


def ashlar(d, x0, y0, x1, y1, ch=6, bw=16, seed=0):
    """Cut grey stone in courses (period 32 in x, so a run joins)."""
    tones = (ASH, rgb('a6acb9'), rgb('8f95a5'), ASH, rgb('a0a3b4'))
    for y in range(y0, y1 + 1):
        j = (y - y0) // ch
        yy = (y - y0) % ch
        for x in range(x0, x1 + 1):
            u = (x + j * (bw // 2) + seed * 5) % 32
            b = u // bw
            if yy == ch - 1 or u % bw == bw - 1:
                c = ASH_DK
            elif yy == 0:
                c = ASH_HI
            elif u % bw == 0:
                c = ASH_HI
            else:
                c = tones[(b + j * 2 + seed) % 5]
                if h3(x % 32, y, 7 + seed) < 10:
                    c = ASH_LO
            d.point((x, y), fill=c)


def copper_roof(d, y0, y1, top, bottom, ridge=True, p=1.3, gold=True):
    """A verdigris copper slope with standing seams, flaring to the eave; with
    `ridge`, a ridge bar (5px above y0) with gilded ends."""
    light, dark, hi, deep = COPPER_P
    rows = curve_rows(y0, y1, top, bottom, p)
    n = max(1, y1 - y0)
    for y, x0, x1 in rows:
        t = (y - y0) / n
        mid = (top[0] + top[1]) / 2 + ((bottom[0] + bottom[1]) / 2 - (top[0] + top[1]) / 2) * t
        half = max(1.0, (x1 - x0) / 2)
        for x in range(x0, x1 + 1):
            u = (x - mid) / half                                  # -1..1 across the slope
            s = round(u * 11)                                     # the seams fan with the flare
            s2 = round(((x + 1) - mid) / half * 11)
            if s != s2:
                c = dark
            elif (y - y0) % 9 == 8:
                c = dark
            elif h3(x, y, 2) < 9:
                c = hi if u < 0 else dark                         # the patina is patchy
            else:
                c = light if u < 0.45 else dark
            d.point((x, y), fill=c)
        d.point((x0, y), fill=hi); d.point((x0 + 1, y), fill=hi)
        d.point((x1, y), fill=deep); d.point((x1 - 1, y), fill=deep)
    bx0, bx1 = bottom
    d.rectangle([bx0, y1 + 1, bx1, y1 + 2], fill=dark)
    d.line([(bx0, y1 + 3), (bx1, y1 + 3)], fill=deep)
    for x in range(bx0 + 2, bx1 - 1, 5):
        d.point((x, y1 + 2), fill=GOLD_HI if gold else hi)
    if ridge:
        tx0, tx1 = top
        d.rectangle([tx0 - 2, y0 - 5, tx1 + 2, y0 - 1], fill=dark)
        d.line([(tx0 - 2, y0 - 5), (tx1 + 2, y0 - 5)], fill=hi)
        d.line([(tx0 - 2, y0 - 1), (tx1 + 2, y0 - 1)], fill=deep)
        if gold:
            for x0 in (tx0 - 5, tx1 + 2):
                d.rectangle([x0, y0 - 7, x0 + 3, y0], fill=GOLD)
                d.line([(x0, y0 - 7), (x0, y0)], fill=GOLD_HI)
                d.line([(x0 + 3, y0 - 6), (x0 + 3, y0)], fill=GOLD_LO)


def thatch_roof(d, y0, y1, top, bottom, p=1.15, ridge=True):
    """A thatched hip roof: combed reed in layers, a thick trimmed eave, a
    bark-covered ridge held down by straddling poles."""
    rows = curve_rows(y0, y1, top, bottom, p)
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            k = h3(x, y // 2, 5)
            if (y - y0) % 11 == 10:
                c = THATCH_LO                                     # where one layer laps the next
            elif (x * 7 + (x // 3) * 5) % 11 == 0:
                c = THATCH_LO
            elif k < 34:
                c = THATCH_HI
            elif k > 228:
                c = THATCH_LO
            else:
                c = THATCH
            d.point((x, y), fill=c)
        w = x1 - x0
        for i in range(3):
            d.point((x0 + i, y), fill=THATCH_HI)
        for i in range(max(3, w // 9)):
            d.point((x1 - i, y), fill=THATCH_LO if i > 1 else THATCH_DK)
    bx0, bx1 = bottom
    d.rectangle([bx0, y1 + 1, bx1, y1 + 5], fill=THATCH_DK)       # the eave's cut edge, in its own shadow
    d.line([(bx0, y1 + 1), (bx1, y1 + 1)], fill=THATCH_LO)
    for x in range(bx0, bx1 + 1):
        if x % 2 == 0:
            d.line([(x, y1 + 2), (x, y1 + 4)], fill=THATCH_LO if x % 6 else THATCH)
    d.line([(bx0, y1 + 5), (bx1, y1 + 5)], fill=rgb('43372f'))
    if ridge:
        tx0, tx1 = top
        d.rectangle([tx0 - 3, y0 - 6, tx1 + 3, y0], fill=UMBER)
        d.line([(tx0 - 3, y0 - 6), (tx1 + 3, y0 - 6)], fill=rgb('93705a'))
        d.line([(tx0 - 3, y0), (tx1 + 3, y0)], fill=UMBER_LO)
        n = max(3, (tx1 - tx0) // 16)
        for i in range(n + 1):                                    # the straddling poles
            x = tx0 + round(i * (tx1 - tx0) / n)
            d.rectangle([x - 1, y0 - 9, x + 1, y0 + 3], fill=THATCH_HI)
            d.line([(x + 1, y0 - 9), (x + 1, y0 + 3)], fill=THATCH_LO)
            d.point((x, y0 - 10), fill=THATCH_LO)


def shingle_pent(d, y0, y1, x0, x1):
    """A pent roof of weathered board shingles over a veranda."""
    for y in range(y0, y1 + 1):
        for x in range(x0 - (y - y0) // 3, x1 + (y - y0) // 3 + 1):
            k = (y - y0) % 4
            if k == 3:
                c = SHINGLE_DK
            elif (x + ((y - y0) // 4) * 3) % 6 == 0:
                c = SHINGLE_LO
            elif k == 0:
                c = SHINGLE_HI
            else:
                c = SHINGLE if h3(x, y, 9) > 30 else SHINGLE_LO
            d.point((x, y), fill=c)
    e = (y1 - y0) // 3
    d.rectangle([x0 - e, y1 + 1, x1 + e, y1 + 2], fill=SHINGLE_DK)
    d.line([(x0 - e, y1 + 1), (x1 + e, y1 + 1)], fill=SHINGLE_LO)


def shoji(d, x0, y0, x1, y1, lit=False, cw=5, chh=6):
    """A paper screen: a dark frame, a lattice, paper that glows if lit."""
    d.rectangle([x0, y0, x1, y1], fill=LQ)
    paper = WARM if lit else PAPER
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=paper)
    for x in range(x0 + 1 + cw, x1, cw + 1):
        d.line([(x, y0 + 1), (x, y1 - 1)], fill=rgb('8a7a66') if not lit else rgb('c79a4a'))
    for y in range(y0 + 1 + chh, y1, chh + 1):
        d.line([(x0 + 1, y), (x1 - 1, y)], fill=rgb('8a7a66') if not lit else rgb('c79a4a'))
    d.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=PAPER_LO if not lit else LIT)


def mon(d, cx, cy, r=5):
    """The quarter's invented crest: a crescent in a gold ring. Not a real mon."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], fill=LQ_LO)
    d.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2], fill=GOLD_HI)
    d.ellipse([cx - r + 2, cy - r + 1, cx + r - 3, cy + r - 4], fill=LQ_LO)
    d.point((cx - r + 1, cy - r + 1), fill=GOLD_HI)


def arch_window(d, x, y0, y1, w, glass=GLASS, hi=GLASS_HI, frame=UMBER, bars=True):
    """A tall round-headed window."""
    r = w // 2
    d.rectangle([x, y0 + r, x + w, y1], fill=frame)
    d.pieslice([x, y0, x + w, y0 + w], 180, 360, fill=frame)
    d.rectangle([x + 1, y0 + r, x + w - 1, y1 - 1], fill=glass)
    d.pieslice([x + 1, y0 + 1, x + w - 1, y0 + w - 1], 180, 360, fill=glass)
    d.line([(x + 2, y0 + r - 1), (x + 2, y1 - 3)], fill=hi)
    if bars:
        d.line([(x + r, y0 + 1), (x + r, y1 - 1)], fill=frame)
        for y in range(y0 + r + 1, y1 - 2, 9):
            d.line([(x + 1, y), (x + w - 1, y)], fill=frame)


def kusudama(d, cx, y, cols, r=7, length=44, n=7):
    """A tanabata decoration: a paper flower ball and its fall of streamers
    (cols: ball, ball lit, ball shade, then the streamer colours)."""
    ball, hi, lo = cols[0], cols[1], cols[2]
    strips = cols[3:]
    top = y + 2 * r - 1
    w = 2
    x0 = cx - (n * (w + 1) - 1) // 2
    for i in range(n):                                            # the streamers: long paper strips
        x = x0 + i * (w + 1)
        ln = length - ((i * 5 + 2) % 7) - abs(i - n // 2)
        c = strips[i % len(strips)]
        for yy in range(top, top + ln):
            d.line([(x, yy), (x + w, yy)], fill=c)                # a strip and its neighbour's edge: no gaps
            if (yy - top) % 7 == 3 + i % 3:                       # the printed pattern on the paper
                d.point((x + (yy // 7) % 2, yy), fill=WHITE)
        d.point((x, top + ln), fill=c)
    d.rectangle([cx - r + 2, top - 1, cx + r - 2, top + 1], fill=lo)          # the hoop the strips hang from
    d.ellipse([cx - r, y, cx + r, y + 2 * r], fill=ball)
    d.chord([cx - r, y, cx + r, y + 2 * r], 20, 160, fill=lo)
    for k in range(8):                                            # folded paper flowers
        a = math.radians(k * 45 + 20)
        px, py = cx + round((r - 3) * math.cos(a)), y + r + round((r - 3) * math.sin(a))
        d.point((px, py), fill=hi); d.point((px + 1, py), fill=WHITE if k % 2 else hi)
    d.rectangle([cx - 1, y + r - 1, cx + 1, y + r + 1], fill=hi)
    d.point((cx - r + 2, y + 2), fill=WHITE)


# ==============================================================================
# Station front
# ==============================================================================
STAINED = (rgb('3f6fd0'), rgb('e0503c'), rgb('f2c12e'), rgb('3fa46a'), rgb('8a4fc0'), rgb('f08a3c'),
           rgb('63c5e8'), rgb('f4f1e4'))


def stained_glass(d, x0, y0, x1, y1):
    """The meeting spot: a wide leaded window in a few big fields of strong
    colour - a sun in its ring over a blue sky, green hills, a river at the
    foot - with heavy leading between the fields and three stout mullions."""
    d.rectangle([x0, y0, x1, y1], fill=SOOT)
    cx, cy = (x0 + x1) // 2, y1 - 22

    def field(x, y):
        if y > y1 - 9 + round(2 * math.sin((x - x0) / 9.0)):
            return 4                                              # the river
        if y > y1 - 19 - round(6 * math.sin((x - x0) / 13.0 + 0.6)):
            return 3                                              # green hills
        r = math.hypot(x - cx, (y - cy) * 1.1)
        return 2 if r < 15 else (1 if r < 22 else 0)              # the sun, its ring, the sky

    cols = ((rgb('3f6fd0'), rgb('5584e2')), (rgb('f08a3c'), rgb('f39a4c')), (rgb('f9cf3e'), rgb('fbdc62')),
            (rgb('3fa46a'), rgb('2f8f5a')), (rgb('63c5e8'), rgb('7fd4f0')))
    w = x1 - x0
    bars = [x0 + round(w * k / 4) for k in (1, 2, 3)]
    for y in range(y0 + 2, y1 - 1):
        for x in range(x0 + 2, x1 - 1):
            f = field(x, y)
            lead = any(abs(x - b) < 1.5 for b in bars) or any(
                field(x + dx, y + dy) != f for dx, dy in ((1, 0), (0, 1), (2, 0), (0, 2)))
            pane = sum(x > b for b in bars)
            d.point((x, y), fill=SOOT if lead else cols[f][pane % 2])
    for x, y in ((x0 + 6, y0 + 5), (x0 + 7, y0 + 6), (bars[1] + 5, y0 + 5), (bars[2] + 6, y0 + 7)):
        d.point((x, y), fill=WHITE)                               # the daylight coming through


# ---- the pedestrian deck: one rail, slab and paving for the station and every piece ----
DECK_GLASS, DECK_GLASS_HI, SOFFIT = rgb('9cc4ea'), rgb('e6f0fa'), rgb('3a3c52')
DPAVE, DPAVE_J, DPAVE_HI = rgb('cfc6b8'), rgb('b3a999'), rgb('ddd6ca')
TREAD = rgb('d6d9de')


def deck_px(x, y):
    """The deck's paving seen from above (period 8 both ways, so pieces join)."""
    if y % 8 == 0 or (x + (y // 8) * 4) % 8 == 0:
        return DPAVE_J
    return DPAVE_HI if h3(x % 32, y % 32, 4) < 8 else DPAVE


def deck_paving(d, x0, y0, x1, y1, strip=None):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=deck_px(x, y))
    if strip is not None:                                         # the tactile strip along it
        for x in range(x0, x1 + 1):
            if x % 16 < 10:
                d.line([(x, strip), (x, strip + 2)], fill=AMBER)
                d.point((x, strip + 3), fill=rgb('c8982c'))


def deck_rail(d, x0, x1, y):
    """The deck's glass rail seen from the south: 6px, its top at y, posts
    every 8px. It stands on the slab at y + 6."""
    d.rectangle([x0, y + 1, x1, y + 5], fill=DECK_GLASS)
    d.line([(x0, y), (x1, y)], fill=STONE_DK)
    for x in range(x0, x1 + 1):
        if x % 8 == 0:
            d.line([(x, y), (x, y + 5)], fill=STONE_DK)
        elif x % 8 == 3:
            d.point((x, y + 2), fill=WHITE)


def deck_back_rail(d, x0, x1, y):
    """The far rail, over the paving's north edge: 4px."""
    d.rectangle([x0, y + 1, x1, y + 3], fill=DECK_GLASS)
    d.line([(x0, y), (x1, y)], fill=STONE_DK)
    for x in range(x0, x1 + 1):
        if x % 8 == 0:
            d.line([(x, y), (x, y + 3)], fill=STONE_DK)


def deck_slab(d, x0, x1, y):
    """The slab's south edge (7px) and the soffit under it (4px)."""
    d.rectangle([x0, y, x1, y + 4], fill=STONE)
    d.line([(x0, y), (x1, y)], fill=WHITE)
    d.rectangle([x0, y + 5, x1, y + 6], fill=STONE_LO)
    d.rectangle([x0, y + 7, x1, y + 10], fill=SOFFIT)


def deck_pier(d, cx, y0, y1):
    """A pair of round concrete columns under a cross head."""
    d.rectangle([cx - 14, y0, cx + 13, y0 + 5], fill=STONE_LO)
    d.line([(cx - 14, y0), (cx + 13, y0)], fill=STONE); d.line([(cx - 14, y0 + 5), (cx + 13, y0 + 5)], fill=STONE_DK)
    for x in (cx - 11, cx + 4):
        bar(d, x, y0 + 6, x + 6, y1 - 3, STONE, WHITE, STONE_LO)
        d.line([(x + 5, y0 + 6), (x + 5, y1 - 3)], fill=STONE_LO)
        d.line([(x + 1, y0 + 6), (x + 1, y0 + 8)], fill=STONE_LO)                # the head's shadow on it
        d.rectangle([x - 2, y1 - 3, x + 8, y1], fill=STONE_LO)
        d.line([(x - 2, y1 - 3), (x + 8, y1 - 3)], fill=STONE)


def deck_shade(x0, x1):
    """The dark under a length of deck: deepest up under the slab, then the
    deck's own shadow lying on the ground as far as its south edge."""
    return [(x0, 51, x1, 58, 150), (x0, 59, x1, 93, 100), (x0, 94, x1, 95, 45)]


def station_front():
    im, d = canvas(9, 5)                 # 288 x 160
    # ---- the long body: cream tile over a recessed ground floor ----------------
    bar(d, 4, 34, 283, 152, STN)
    d.rectangle([270, 34, 283, 152], fill=STN_LO)                 # the east return, in shade
    for y in range(40, 104, 8):                                   # the tile courses
        d.line([(4, y), (283, y)], fill=STN_LO if y % 16 else STN_DK)
    for x in range(4, 284, 16):
        for y in range(34, 104):
            if (y // 8) % 2 == (x // 16) % 2 and y % 8:
                d.point((x, y), fill=STN_LO)
    d.line([(4, 34), (4, 152)], fill=STN_HI); d.line([(5, 34), (5, 152)], fill=STN_HI)
    # ---- the parapet and the raised centre with the name ------------------------
    d.rectangle([2, 28, 285, 34], fill=UMBER)
    d.line([(2, 28), (285, 28)], fill=rgb('93705a')); d.line([(2, 34), (285, 34)], fill=UMBER_LO)
    bar(d, 92, 8, 195, 30, STN, STN_HI, STN_LO)
    d.rectangle([90, 4, 197, 9], fill=UMBER); d.line([(90, 4), (197, 4)], fill=rgb('93705a'))
    d.line([(90, 9), (197, 9)], fill=UMBER_LO)
    d.rectangle([104, 12, 183, 28], fill=NAVY); d.rectangle([105, 13, 182, 27], fill=rgb('24377a'))
    d.line([(105, 13), (182, 13)], fill=rgb('3a5fb0'))
    text(d, 'SENDAI', 144 - (text_w('SENDAI') * 2) // 2, 14, WHITE, scale=2)
    for x in (20, 60, 228, 262):                                  # roof plant on the wings
        bar(d, x, 20, x + 14, 27, STONE_LO, STONE, STONE_DK)
        d.line([(x + 2, 23), (x + 12, 23)], fill=STONE_DK)
    d.rectangle([44, 14, 45, 27], fill=STONE_DK); d.line([(41, 17), (48, 17)], fill=STONE_DK)
    # ---- the wings' tall arched windows ------------------------------------------
    for i, x in enumerate(list(range(12, 92, 16)) + list(range(200, 268, 16))):
        lit = i in (1, 6)
        arch_window(d, x, 44, 96, 11, glass=WARM if lit else GLASS, hi=WHITE if lit else GLASS_HI)
        d.line([(x - 1, 97), (x + 12, 97)], fill=STN_HI)          # the sill
        d.line([(x - 1, 98), (x + 12, 98)], fill=STN_DK)
    # ---- the centre: the stained glass in a stone frame ---------------------------
    bar(d, 98, 36, 189, 102, CREAM, WHITE, CREAM_LO)
    stained_glass(d, 103, 40, 184, 97)
    d.line([(98, 102), (189, 102)], fill=CREAM_DK)
    # ---- the pedestrian deck where it meets the station: a rail, a slab -----------
    deck_slab(d, 0, 287, 104)                                     # the same rail and slab the deck pieces carry
    deck_rail(d, 0, 287, 98)
    # ---- the ground floor under the deck: columns, lit shops, the doors -----------
    d.rectangle([4, 115, 283, 152], fill=GLASS_DK)
    for i, x0 in enumerate((10, 40, 70, 196, 226, 256)):          # shop windows
        d.rectangle([x0, 120, x0 + 24, 150], fill=WARM)
        d.line([(x0, 120), (x0 + 24, 120)], fill=WHITE)
        d.rectangle([x0, 120, x0 + 24, 125], fill=(RED, GREEN, NAVY, rgb('f08a3c'), GREEN, RED)[i])   # fascia
        for k in range(4):                                        # goods on shelves
            d.rectangle([x0 + 2 + k * 6, 134, x0 + 5 + k * 6, 139],
                        fill=(RED_HI, AMBER, GLASS_HI, GREEN_HI)[(k + i) % 4])
            d.rectangle([x0 + 2 + k * 6, 143, x0 + 5 + k * 6, 148],
                        fill=(CREAM, RED, AMBER, CREAM_LO)[(k + i) % 4])
        d.line([(x0, 141), (x0 + 24, 141)], fill=CREAM_DK)
        d.line([(x0 + 12, 126), (x0 + 12, 150)], fill=CREAM_DK)
    for k in range(3):                                            # three pairs of doors (cells 3-5, row 4)
        glass_door(d, 99 + k * 31, 120, 99 + k * 31 + 27, 152)
    d.rectangle([97, 115, 190, 119], fill=AMBER)                  # the lit sign band over the doors
    d.line([(97, 115), (190, 115)], fill=WHITE)
    for x in range(102, 188, 10):
        d.rectangle([x, 117, x + 5, 117], fill=UMBER)
    for x in (4, 34, 64, 93, 189, 220, 250, 278):                 # the deck's columns
        bar(d, x, 111, x + 5, 152, STONE, WHITE, STONE_LO)
    d.rectangle([2, 152, 285, 157], fill=STONE_LO); d.line([(2, 152), (285, 152)], fill=STONE)
    outline(im)
    return im


def deck_span():
    """A length of the deck running east-west, 3x3. From the top: the far
    rail, the paving seen from above, the near rail and the slab (at the
    height of the station front's own, so a run joins it), then the dark
    under it: a pier of two columns in the middle cell, shadow on the ground."""
    im, d = canvas(3, 3)                 # 96 x 96
    deck_back_rail(d, 0, 95, 4)
    deck_paving(d, 0, 8, 95, 33, strip=19)
    deck_rail(d, 0, 95, 34); deck_slab(d, 0, 95, 40)
    for x in (10, 78):                                            # lights under the deck
        d.rectangle([x, 49, x + 7, 50], fill=WARM)
    deck_pier(d, 48, 51, 93)
    outline(im)
    return grounded(im, rects=deck_shade(0, 95))


def deck_end(east):
    """The deck's end, 1x3: the rail returns across it over a last pier."""
    im, d = canvas(1, 3)                 # 32 x 96
    a, b = (0, 22) if east else (9, 31)
    deck_back_rail(d, a, b, 4)
    deck_paving(d, a, 8, b, 33, strip=19)
    deck_rail(d, a, b, 34); deck_slab(d, a, b, 40)
    edge, step = (b, -1) if east else (a, 1)                      # the end rail, seen from above
    d.line([(edge, 4), (edge, 39)], fill=STONE_DK)
    d.line([(edge + step, 5), (edge + step, 39)], fill=DECK_GLASS)
    d.line([(edge + 2 * step, 8), (edge + 2 * step, 33)], fill=DECK_GLASS_HI)
    for y in range(8, 40, 8):
        d.line([(edge, y), (edge + 2 * step, y)], fill=STONE_DK)
    deck_pier(d, 11 if east else 20, 51, 93)
    outline(im)
    return grounded(im, rects=deck_shade(0, 25) if east else deck_shade(6, 31))


def deck_span_v():
    """A length of the deck running north-south, 1x3 and stacked down the map:
    the paving between its two rails seen from above; under its south end the
    slab's edge and its shadow. Each piece's paving covers the end of the one
    north of it, so only the last shows an end."""
    im, d = canvas(1, 3)                 # 32 x 96
    deck_paving(d, 3, 0, 28, 39)
    for y in range(0, 40):
        if y % 16 < 10:
            d.line([(14, y), (16, y)], fill=AMBER); d.point((17, y), fill=rgb('c8982c'))
    for x0, cols in ((0, (STONE_DK, DECK_GLASS, DECK_GLASS_HI)), (29, (DECK_GLASS_HI, DECK_GLASS, STONE_DK))):
        for k, c in enumerate(cols):
            d.line([(x0 + k, 0), (x0 + k, 39)], fill=c)
        for y in range(0, 40, 8):
            d.line([(x0, y), (x0 + 2, y)], fill=STONE_DK)
    deck_slab(d, 0, 31, 40)
    outline(im)
    return grounded(im, rects=deck_shade(0, 31))


def deck_end_s():
    """The south end of a north-south run, 1x3: the rail across it, a pier."""
    im, d = canvas(1, 3)                 # 32 x 96
    deck_paving(d, 3, 0, 28, 33)
    for y in range(0, 26):
        if y % 16 < 10:
            d.line([(14, y), (16, y)], fill=AMBER); d.point((17, y), fill=rgb('c8982c'))
    for x0, cols in ((0, (STONE_DK, DECK_GLASS, DECK_GLASS_HI)), (29, (DECK_GLASS_HI, DECK_GLASS, STONE_DK))):
        for k, c in enumerate(cols):
            d.line([(x0 + k, 0), (x0 + k, 33)], fill=c)
        for y in range(0, 34, 8):
            d.line([(x0, y), (x0 + 2, y)], fill=STONE_DK)
    deck_rail(d, 0, 31, 34); deck_slab(d, 0, 31, 40)
    deck_pier(d, 16, 51, 93)
    outline(im)
    return grounded(im, rects=deck_shade(0, 31))


def deck_stair(east):
    """The stair from the deck down to the street, 3x3, seen from its side:
    a landing level with the deck (a pier under it), then thirteen treads
    falling away east (or west) between two glass balustrades on sloping
    stringers, a prop under the flight, a tactile mat at its foot."""
    im, d = canvas(3, 3)                 # 96 x 96
    fx = (lambda x: x) if east else (lambda x: 95 - x)
    la, lb = (0, 19) if east else (76, 95)
    deck_back_rail(d, la, lb, 4)
    deck_paving(d, la, 8, lb, 33)
    deck_rail(d, la, lb, 34); deck_slab(d, la, lb, 40)
    for x in (16, 18):                                            # the warning strip at the stair's head
        for y in range(9, 33, 2):
            d.point((fx(x), y), fill=AMBER)
    deck_pier(d, 10 if east else 85, 51, 93)
    prop = fx(54)
    bar(d, prop - 3, 80, prop + 3, 90, STONE, WHITE, STONE_LO)    # the prop under the flight
    d.rectangle([prop - 5, 90, prop + 5, 93], fill=STONE_LO); d.line([(prop - 5, 90), (prop + 5, 90)], fill=STONE)

    def col(x, y0, y1, c):
        if y0 <= 93:
            d.line([(x, y0), (x, min(93, y1))], fill=c)

    for i in range(13):
        drop = 4 * (i + 1) + (1 if i == 12 else 0)
        for k in range(5):
            x = fx(20 + 5 * i + k)
            post = (i % 3 == 0 and k == 0)
            col(x, 4 + drop, 4 + drop, STONE_DK)                  # the far balustrade
            col(x, 5 + drop, 7 + drop, STONE_DK if post else DECK_GLASS)
            col(x, 8 + drop, 33 + drop, WHITE if k == 0 else (STONE_LO if k == 4 else TREAD))   # the tread
            if k == 0:
                col(x, 8 + drop, 10 + drop, AMBER); col(x, 31 + drop, 33 + drop, AMBER)
            col(x, 34 + drop, 34 + drop, STONE_DK)                # the near balustrade
            col(x, 35 + drop, 39 + drop, STONE_DK if post else DECK_GLASS)
            if k == 2 and not post:
                col(x, 36 + drop, 36 + drop, WHITE)
            col(x, 40 + drop, 40 + drop, WHITE)                   # the stringer
            col(x, 41 + drop, 44 + drop, STONE)
            col(x, 45 + drop, 46 + drop, STONE_LO)
            col(x, 47 + drop, 48 + drop, SOFFIT)
    for x in (85, 86):                                            # newel posts at the foot
        col(fx(x), 55, 60, STONE_DK); col(fx(x), 85, 93, STONE_DK)
    for x in range(88, 94):                                       # the tactile mat on the ground
        for y in range(63, 91):
            if (x + y) % 2 == 0:
                d.point((fx(x), y), fill=AMBER)
            else:
                d.point((fx(x), y), fill=rgb('c8982c'))
    outline(im)
    under = [([(fx(20), 51), (fx(20), 93), (fx(84), 93), (fx(84), 92)], 100)]
    return grounded(im, rects=deck_shade(la, lb + 1) if east else deck_shade(la - 1, lb), polys=under)


BAMBOO, BAMBOO_HI, BAMBOO_LO = rgb('8fa85a'), rgb('c0d27e'), rgb('5f7a44')
KUSU_A = (rgb('f0669e'), rgb('fbb4d0'), rgb('c0447a'), rgb('f0669e'), rgb('f9c22e'), WHITE, rgb('e0503c'),
          rgb('fbb4d0'), rgb('f08a3c'))
KUSU_B = (rgb('4b8fe0'), rgb('a8d4fa'), rgb('2f5fae'), rgb('4b8fe0'), WHITE, rgb('63c5e8'), rgb('8a4fc0'),
          rgb('a8d4fa'))
KUSU_C = (rgb('5fb86a'), rgb('b6e6a0'), rgb('3a8450'), rgb('5fb86a'), rgb('f9c22e'), WHITE, rgb('f08a3c'),
          rgb('b6e6a0'))


def bamboo(d, pts, w=3):
    d.line(pts, fill=BAMBOO, width=w)
    d.line([(x - 1, y) for x, y in pts], fill=BAMBOO_HI)
    d.line([(x + 1, y) for x, y in pts], fill=BAMBOO_LO)


def tanabata(variant):
    if variant == 'a':
        im, d = canvas(1, 3)             # 32 x 96
        sh = (2, 88, 22, 94)
        bamboo(d, [(6, 92), (6, 10)])
        for y in range(18, 92, 13):
            d.line([(5, y), (7, y)], fill=BAMBOO_LO)              # nodes
        d.line([(6, 10), (10, 5), (18, 4)], fill=BAMBOO, width=2)             # the tip, bent by the weight
        for x, y in ((9, 3), (12, 1), (3, 8), (2, 14)):           # leaves
            d.line([(x, y), (x + 3, y + 1)], fill=BAMBOO_LO)
        d.line([(18, 4), (18, 8)], fill=CREAM_DK)                 # the string
        kusudama(d, 18, 8, KUSU_A, r=7, length=58, n=7)
        d.rectangle([2, 90, 10, 93], fill=STONE_LO); d.line([(2, 90), (10, 90)], fill=STONE)
    else:
        im, d = canvas(3, 3)             # 96 x 96: a pair on a cross pole; the pole stands in the middle cell
        sh = (36, 88, 60, 94)
        bamboo(d, [(48, 92), (48, 6)])
        for y in range(16, 92, 13):
            d.line([(47, y), (49, y)], fill=BAMBOO_LO)
        d.line([(12, 10), (84, 7)], fill=BAMBOO, width=2)         # the cross pole
        d.line([(12, 9), (84, 6)], fill=BAMBOO_HI)
        for x, y in ((51, 2), (43, 3), (9, 7), (84, 4)):
            d.line([(x, y), (x + 3, y + 1)], fill=BAMBOO_LO)
        d.line([(22, 10), (22, 13)], fill=CREAM_DK); d.line([(74, 8), (74, 14)], fill=CREAM_DK)
        kusudama(d, 22, 13, KUSU_B, r=7, length=52, n=7)
        kusudama(d, 74, 14, KUSU_C, r=7, length=46, n=7)
        for i, x in enumerate(range(36, 62, 4)):                  # paper strips of wishes on the pole
            if x != 48:
                d.rectangle([x, 12 + i % 2 * 3, x + 1, 22 + i % 3 * 3], fill=(WHITE, AMBER, RED_HI, WHITE)[i % 4])
        d.rectangle([43, 90, 53, 93], fill=STONE_LO); d.line([(43, 90), (53, 90)], fill=STONE)
    outline(im)
    return grounded(im, [sh])


# ==============================================================================
# Downtown / Jozenji-dori
# ==============================================================================
def limb(d, pts, w, base=ZBARK, hi=ZBARK_HI, lo=ZBARK_LO):
    d.line(pts, fill=base, width=w)
    d.line([(x - max(1, w // 2), y) for x, y in pts], fill=hi)
    d.line([(x + max(1, w // 2), y) for x, y in pts], fill=lo)


def zelkova(variant):
    """A keyaki: a smooth grey trunk that forks low into a vase of rising
    limbs, a broad dome of small leaves gone gold."""
    if variant == 'a':
        im, d = canvas(3, 4)             # 96 x 128
        cx, base = 48, 122
        sh, lv = (18, 112, 80, 126), (14, 82, 114, 126, (KEY, KEY_HI, KEY_LO, RUS), 34, 1)
        limb(d, [(cx, base), (cx, 86)], 9)
        d.polygon([(cx - 8, base), (cx - 4, base - 8), (cx + 4, base - 8), (cx + 8, base)], fill=ZBARK)   # root flare
        d.line([(cx - 8, base), (cx - 4, base - 8)], fill=ZBARK_HI)
        d.line([(cx + 8, base), (cx + 4, base - 8)], fill=ZBARK_LO)
        for pts, w in (([(cx - 2, 90), (30, 62), (18, 44)], 5), ([(cx - 1, 88), (40, 56), (36, 30)], 5),
                       ([(cx + 1, 88), (56, 56), (60, 28)], 5), ([(cx + 2, 90), (66, 64), (80, 46)], 5),
                       ([(cx, 86), (48, 50), (48, 22)], 4)):
            limb(d, pts, w)
        for y in range(90, 120, 7):                               # the bark's flaking plates
            d.point((cx - 1, y), fill=ZBARK_LO); d.point((cx + 2, y + 3), fill=ZBARK_HI)
        pads = ((14, 52, 13, 11, 1, 0), (82, 54, 13, 11, 2, 2), (26, 36, 16, 13, 3, 0), (70, 36, 16, 13, 4, 1),
                (48, 24, 20, 14, 5, 0), (34, 16, 14, 10, 6, 1), (62, 15, 14, 10, 7, 0), (48, 9, 12, 8, 8, 0),
                (20, 62, 10, 8, 9, 2), (76, 64, 10, 8, 10, 1), (48, 46, 15, 11, 11, 0), (32, 56, 11, 8, 12, 1),
                (64, 57, 11, 8, 13, 2))
    else:
        im, d = canvas(2, 4)             # 64 x 128
        cx, base = 32, 122
        sh, lv = (10, 112, 56, 126), (8, 58, 114, 126, (RUS, KEY, RUS_LO, KEY_HI), 22, 4)
        limb(d, [(cx, base), (cx, 80)], 7)
        d.polygon([(cx - 6, base), (cx - 3, base - 7), (cx + 3, base - 7), (cx + 6, base)], fill=ZBARK)
        d.line([(cx - 6, base), (cx - 3, base - 7)], fill=ZBARK_HI)
        for pts, w in (([(cx - 1, 84), (22, 58), (16, 40)], 4), ([(cx, 82), (30, 50), (28, 24)], 4),
                       ([(cx + 1, 84), (42, 56), (48, 36)], 4)):
            limb(d, pts, w)
        pads = ((14, 46, 11, 10, 1, 1), (50, 44, 11, 10, 2, 2), (24, 30, 13, 11, 3, 1), (42, 28, 13, 11, 4, 0),
                (32, 16, 14, 11, 5, 1), (32, 8, 10, 7, 6, 0), (32, 44, 11, 9, 7, 2), (18, 58, 8, 6, 8, 1),
                (46, 58, 8, 6, 9, 2))
    pal = ((KEY, KEY_HI, KEY_LO), (RUS, RUS_HI, RUS_LO), (KEY_LO, KEY, KEY_DK))
    if variant == 'b':
        pal = ((RUS, RUS_HI, RUS_LO), (KEY, KEY_HI, KEY_LO), (RUS_LO, RUS, KEY_DK))
    for px, py, rx, ry, s, tone in sorted(pads, key=lambda p: -p[1]):         # lower pads first, the crown over them
        a, b, c = pal[tone]
        blob(d, px, py, rx, ry, a, b, c, s)
    w, h = im.size
    for i in range(110 if variant == 'a' else 60):                # single leaves catching the light, and gaps
        x, y = 4 + (i * 29) % (w - 8), 4 + (i * 17) % 66
        if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] not in (ZBARK[:3], ZBARK_HI[:3], ZBARK_LO[:3]):
            d.point((x, y), fill=(KEY_HI, KEY_DK, RUS_HI, rgb('fff0a8'))[i % 4])
    if variant == 'b':                                            # three cells wide, the trunk in the middle one
        wide, d = canvas(3, 4)
        wide.alpha_composite(im, (16, 0))
        im = wide
        sh = (sh[0] + 16, sh[1], sh[2] + 16, sh[3])
        lv = (lv[0] + 16, lv[1] + 16) + lv[2:]
    outline(im)
    return grounded(im, [sh], leaves=lv)


DBRONZE, DBRONZE_HI, DBRONZE_LO = rgb('6b4f3a'), rgb('a98458'), rgb('43302a')


def jozenji_statue():
    """A bronze for the avenue's median, 2x3: a dancer on a granite block, the
    left arm flung up, the right held out with a bird on the hand, striding."""
    im, d = canvas(2, 3)                 # 64 x 96
    ashlar(d, 13, 68, 50, 89, ch=11, bw=19, seed=3)               # the granite block
    d.line([(13, 68), (13, 89)], fill=ASH_HI); d.rectangle([47, 68, 50, 89], fill=ASH_LO)
    d.rectangle([11, 64, 52, 67], fill=ASH_HI); d.line([(11, 67), (52, 67)], fill=ASH_DK)
    d.rectangle([10, 90, 53, 92], fill=ASH_LO); d.line([(10, 90), (53, 90)], fill=ASH)
    d.rectangle([24, 75, 39, 82], fill=DBRONZE_LO); d.line([(26, 77), (37, 77)], fill=GOLD)   # the plate
    d.line([(26, 80), (34, 80)], fill=GOLD_LO)
    B, H, L = DBRONZE, DBRONZE_HI, DBRONZE_LO

    def limb_(pts, w=3):
        d.line(pts, fill=B, width=w)
        d.line([(x - 1, y) for x, y in pts], fill=H)
        d.line([(x + w // 2, y) for x, y in pts], fill=L)

    d.rectangle([24, 61, 40, 63], fill=L); d.line([(24, 61), (40, 61)], fill=B)              # the base plate
    limb_([(27, 61), (29, 52), (31, 44)], 4)                      # the standing leg
    limb_([(39, 60), (37, 52), (34, 44)], 4)                      # the trailing leg, on its toe
    d.polygon([(26, 46), (39, 46), (37, 35), (29, 35)], fill=B)   # the hips, a short skirt swung out
    d.line([(26, 46), (29, 35)], fill=H); d.line([(39, 46), (37, 36)], fill=L)
    d.line([(27, 47), (40, 47)], fill=L)
    d.rectangle([29, 24, 36, 36], fill=B)                         # the torso
    d.line([(29, 24), (29, 35)], fill=H); d.line([(36, 25), (36, 36)], fill=L)
    d.line([(30, 30), (35, 30)], fill=L)
    limb_([(30, 26), (24, 19), (21, 8)], 3)                       # the left arm, flung up
    d.rectangle([20, 5, 22, 8], fill=H)
    limb_([(36, 26), (43, 24), (49, 19)], 3)                      # the right arm, held out
    d.polygon([(48, 17), (52, 14), (56, 15), (53, 17), (55, 19), (50, 19)], fill=B)          # the bird on her hand
    d.point((52, 15), fill=H); d.point((56, 15), fill=GOLD)
    d.rectangle([31, 21, 34, 24], fill=L)                         # the neck
    d.ellipse([29, 13, 36, 21], fill=B)                           # the head, turned up to the bird
    d.arc([29, 13, 36, 21], 150, 280, fill=H)
    d.rectangle([28, 13, 31, 17], fill=L); d.ellipse([26, 14, 30, 18], fill=L)               # hair in a knot
    for x, y in ((31, 40), (33, 43), (30, 28), (28, 55), (38, 56)):                          # verdigris in the folds
        d.point((x, y), fill=BRONZE_HI)
    outline(im)
    return grounded(im, [(6, 86, 58, 95)])


def coals(d, x0, y0, x1, y1):
    """A charcoal bed under a mesh: black with pieces glowing."""
    d.rectangle([x0, y0, x1, y1], fill=SOOT)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            k = h3(x, y, 8)
            if k < 70:
                d.point((x, y), fill=COAL if k < 30 else EMBER)
            elif k < 82:
                d.point((x, y), fill=AMBER)


def gyutan():
    im, d = canvas(4, 4)                 # 128 x 128
    # ---- the upper wall: charred cedar boards, a plaster band, the board ---------
    for x in range(6, 122):
        for y in range(26, 72):
            k = (x - 6) % 6
            c = CHAR_LO if k == 5 else (CHAR_HI if k == 0 else CHAR)
            if h3(x // 6, y, 6) < 22 and k not in (0, 5):
                c = CHAR_LO                                       # the alligator skin of the burn
            d.point((x, y), fill=c)
    d.rectangle([114, 26, 121, 72], fill=CHAR_LO)
    d.rectangle([4, 20, 123, 26], fill=SOOT); d.line([(4, 20), (123, 20)], fill=rgb('55525c'))   # the parapet
    d.line([(4, 26), (123, 26)], fill=INK)
    bar(d, 20, 32, 83, 62, rgb('1c1a1f'), None, None)             # the name board: gold on black
    d.rectangle([20, 32, 83, 62], outline=GOLD)
    d.rectangle([22, 34, 81, 60], outline=GOLD_LO)
    glyph(d, GYU, 27, 40, GOLD_HI, 2)
    kana(d, ['ta'], 46, 40, GOLD_HI, 2); kana(d, ['n'], 63, 40, GOLD_HI, 2)
    d.rectangle([90, 34, 99, 60], fill=VERM)                      # an upright tab: charcoal-grilled
    d.line([(90, 34), (90, 60)], fill=VERM_HI); d.line([(99, 34), (99, 60)], fill=VERM_LO)
    for y in (38, 45, 52):
        d.rectangle([93, y, 96, y + 3], fill=WHITE)
    # ---- the flue up the east side, and its smoke ---------------------------------
    bar(d, 104, 12, 111, 76, STONE, WHITE, STONE_DK)
    d.rectangle([109, 12, 111, 76], fill=STONE_LO)
    for y in (22, 40, 58):
        d.line([(104, y), (111, y)], fill=STONE_DK)
    d.rectangle([102, 10, 113, 13], fill=STONE_LO); d.line([(102, 10), (113, 10)], fill=STONE)
    # ---- the pent roof over the front: black tile, a gold-capped eave --------------
    for y in range(72, 82):
        e = (y - 72)
        for x in range(4 - e // 3, 124 + e // 3):
            c = rgb('1f2029') if (y - 72) % 4 == 3 or (x + ((y - 72) // 4) * 3) % 6 == 0 else rgb('34364a')
            d.point((x, y), fill=c)
    d.rectangle([1, 82, 126, 83], fill=rgb('1f2029'))
    for x in range(3, 126, 5):
        d.point((x, 83), fill=GOLD)
    # ---- the ground floor ------------------------------------------------------------
    d.rectangle([6, 84, 121, 122], fill=CHAR_LO)
    for x in (6, 62, 92, 118):                                    # posts
        bar(d, x, 84, x + 3, 122, CHAR, CHAR_HI, INK)
    # the grill window (cells 0-1): the cook, the mesh, slices of tongue, the coals
    d.rectangle([10, 88, 61, 116], fill=rgb('40282a'))
    d.rectangle([10, 88, 61, 90], fill=WARM)                      # the hood's light
    d.rectangle([28, 91, 38, 104], fill=WHITE); d.rectangle([29, 86, 37, 91], fill=WHITE)    # the cook, in whites
    d.rectangle([30, 92, 36, 97], fill=rgb('e8b99a')); d.point((31, 94), fill=INK); d.point((35, 94), fill=INK)
    d.rectangle([24, 100, 42, 106], fill=WHITE); d.line([(24, 106), (42, 106)], fill=CREAM_LO)
    d.line([(42, 102), (48, 105)], fill=rgb('e8b99a'), width=2)   # an arm, turning a slice
    coals(d, 12, 110, 59, 115)
    d.line([(12, 108), (59, 108)], fill=STONE_DK)                 # the mesh
    for x in range(12, 60, 3):
        d.point((x, 109), fill=STONE_DK)
    for x in (16, 24, 32, 45, 53):                                # slices of tongue on it
        d.rectangle([x, 106, x + 4, 107], fill=rgb('c98a78')); d.point((x + 1, 106), fill=rgb('e7b3a2'))
    d.rectangle([10, 116, 61, 122], fill=CHAR); d.line([(10, 116), (61, 116)], fill=CHAR_HI)
    puff(im, 20, 100, 3, a=70); puff(im, 50, 97, 4, a=70)
    d = ImageDraw.Draw(im)
    # the door (cell 2): lamplit lattice behind a short noren
    d.rectangle([66, 88, 91, 122], fill=LQ)
    shoji(d, 67, 96, 78, 121, lit=True, cw=3, chh=5); shoji(d, 79, 96, 90, 121, lit=True, cw=3, chh=5)
    d.rectangle([65, 86, 92, 97], fill=UMBER)
    for k in range(3):
        x0 = 65 + k * 9 + (1 if k else 0)
        d.rectangle([x0, 87, x0 + 8, 99 + (k % 2)], fill=rgb('7a2f2c'))
        d.line([(x0, 87), (x0, 99)], fill=rgb('a04a3e'))
    glyph(d, GYU, 75, 89, CREAM, 1)
    d.line([(64, 86), (93, 86)], fill=GOLD_LO)
    # the east bay (cell 3): a lantern, the menu, a stack of charcoal sacks
    lantern(d, 98, 88, 9, 15)
    bar(d, 110, 92, 117, 108, PAPER, WHITE, PAPER_LO)
    for y in (95, 98, 101, 104):
        d.line([(112, y), (115, y)], fill=CREAM_DK)
    d.rectangle([96, 110, 112, 121], fill=rgb('8a6a4c')); d.line([(96, 110), (112, 110)], fill=rgb('b08a64'))
    d.line([(96, 115), (112, 115)], fill=rgb('5f4a3a')); d.line([(104, 110), (104, 121)], fill=rgb('5f4a3a'))
    d.rectangle([4, 122, 123, 126], fill=ASH_LO); d.line([(4, 122), (123, 122)], fill=ASH_HI)
    outline(im)
    puff(im, 109, 6, 3, a=170); puff(im, 114, 3, 4, a=130); puff(im, 120, 5, 3, a=90)      # charcoal smoke
    puff(im, 104, 3, 2, a=110)
    return im


def edamame(d, x, y, c=ZUN_DK, hi=ZUN_HI):
    """A pod: three beans in a row."""
    d.rectangle([x, y + 1, x + 9, y + 3], fill=c)
    for k in range(3):
        d.rectangle([x + k * 3 + 1, y, x + k * 3 + 2, y + 4], fill=c)
        d.point((x + k * 3 + 1, y + 1), fill=hi)
    d.point((x + 10, y + 2), fill=c)


def zunda():
    im, d = canvas(3, 3)                 # 96 x 96
    bar(d, 5, 14, 90, 90, ZUN, ZUN_HI, ZUN_LO)                    # pale green render
    d.rectangle([84, 14, 90, 90], fill=ZUN_LO)
    for y in range(22, 46, 8):
        d.line([(5, y), (90, y)], fill=ZUN_LO)
    d.rectangle([3, 9, 92, 14], fill=WHITE); d.line([(3, 14), (92, 14)], fill=ZUN_DK)       # the cornice
    d.line([(3, 9), (92, 9)], fill=ZUN_HI)
    bar(d, 62, 2, 76, 9, ZUN_LO, ZUN, ZUN_DK)                     # a roof vent
    # the board: ZUNDA and a pod on cream
    bar(d, 8, 18, 87, 35, PAPER, WHITE, PAPER_LO)
    d.rectangle([8, 18, 87, 35], outline=ZUN_DK)
    text(d, 'ZUNDA', 26, 20, rgb('35603f'), scale=2)
    edamame(d, 11, 21); edamame(d, 13, 28, rgb('3f7a4a'))
    # the awning: green and white scallops
    for x in range(3, 93):
        stripe = ((x - 3) // 6) % 2
        for y in range(38, 46):
            d.point((x, y), fill=(ZUN_DK if y > 43 else rgb('6fae6a')) if stripe else (PAPER_LO if y > 43 else WHITE))
        if (x - 3) % 6 in (1, 2, 3, 4):
            d.point((x, 46), fill=rgb('6fae6a') if stripe else WHITE)
    d.line([(3, 38), (92, 38)], fill=ZUN_HI)
    # the window (cells 0-1): plates of zunda mochi, a shake, a clerk
    d.rectangle([9, 50, 55, 84], fill=WHITE)
    d.rectangle([10, 51, 54, 83], fill=WARM)
    d.line([(10, 51), (54, 51)], fill=WHITE)
    d.rectangle([34, 54, 44, 68], fill=rgb('e8b99a'))             # the clerk: a green cap and apron
    d.rectangle([33, 52, 45, 56], fill=ZUN_DK); d.point((36, 60), fill=INK); d.point((41, 60), fill=INK)
    d.rectangle([31, 66, 47, 74], fill=rgb('6fae6a')); d.line([(31, 66), (47, 66)], fill=ZUN_HI)
    d.rectangle([10, 74, 54, 83], fill=PAPER); d.line([(10, 74), (54, 74)], fill=PAPER_LO)  # the counter
    for x in (13, 24, 45):                                        # mochi under green paste, on plates
        d.rectangle([x - 1, 80, x + 8, 81], fill=WHITE); d.line([(x - 1, 82), (x + 8, 82)], fill=PAPER_LO)
        for k in range(3):
            d.rectangle([x + k * 3, 77, x + k * 3 + 1, 79], fill=rgb('7fc06a'))
            d.point((x + k * 3, 77), fill=ZUN_HI)
    d.rectangle([14, 56, 20, 68], fill=WHITE); d.rectangle([14, 56, 20, 60], fill=rgb('8fd07a'))    # a zunda shake
    d.rectangle([15, 61, 19, 67], fill=rgb('cfeebb')); d.line([(18, 50), (17, 56)], fill=RED)
    d.rectangle([22, 60, 27, 68], fill=WHITE); d.rectangle([22, 60, 27, 63], fill=rgb('8fd07a'))
    d.line([(32, 51), (32, 73)], fill=WHITE)
    # the door (cell 2): glass, a short green noren with a pod on it
    d.rectangle([62, 50, 85, 90], fill=WHITE)
    d.rectangle([63, 51, 84, 90], fill=GLASS)
    d.rectangle([63, 51, 84, 60], fill=rgb('4f8250'))
    d.line([(63, 51), (84, 51)], fill=rgb('6a9c59'))
    d.line([(70, 51), (70, 61)], fill=rgb('35603f')); d.line([(77, 51), (77, 61)], fill=rgb('35603f'))
    edamame(d, 68, 54, ZUN_HI, WHITE)
    d.line([(73, 61), (73, 90)], fill=WHITE); d.line([(64, 62), (72, 62)], fill=GLASS_HI)
    d.line([(74, 62), (83, 62)], fill=GLASS_HI)
    d.point((71, 76), fill=WHITE); d.point((75, 76), fill=WHITE)
    d.rectangle([5, 84, 61, 90], fill=WHITE); d.line([(5, 84), (61, 84)], fill=ZUN_LO)       # the stall riser
    for x in range(8, 60, 6):
        d.rectangle([x, 86, x + 3, 88], fill=ZUN)
    d.rectangle([3, 90, 92, 94], fill=ASH_LO); d.line([(3, 90), (92, 90)], fill=ASH_HI)
    outline(im)
    return im


PANES = (rgb('a9d4f6'), rgb('7fb2e6'), rgb('8fc0ee'), rgb('6a9cd6'))          # lit pair, shaded pair
RAFTER = rgb('f4f8fc')


def arcade_gate():
    """The mouth of the covered street: two tall clad pylons carrying the
    gable end of a pitched glass roof, the name board right across between
    them, banners and a kusudama hung in the head of the opening. A tall
    rectangular portal, not an arch."""
    im, d = canvas(4, 5)                 # 128 x 160
    cx = 64
    # ---- the glazed gable ------------------------------------------------------------
    for y in range(6, 41):
        half = round((y - 5) * 62 / 35)
        for x in range(cx - half, cx + half):
            u = x - cx
            west = u < 0
            if half - abs(u + 0.5) < 3.5:
                c = WHITE if west else STONE                      # the rake
            elif (u % 14) in (0, 13) or (40 - y) % 12 == 0:
                c = WHITE if west else STONE                      # mullions and transoms
            else:
                k = (u // 14 + (40 - y) // 12) % 2
                c = PANES[k] if west else PANES[2 + k]
            d.point((x, y), fill=c)
    d.rectangle([61, 2, 66, 7], fill=WHITE); d.rectangle([64, 2, 66, 7], fill=STONE)
    d.rectangle([62, 0, 65, 1], fill=KEY); d.point((62, 0), fill=KEY_HI)
    d.rectangle([0, 40, 127, 45], fill=WHITE)                     # the tie beam the roof springs from
    d.line([(0, 44), (127, 44)], fill=STONE); d.line([(0, 45), (127, 45)], fill=STONE_LO)
    for x in range(6, 124, 10):
        d.point((x, 42), fill=STONE_LO)
    # ---- the pylons -------------------------------------------------------------------
    for x0 in (3, 110):
        bar(d, x0, 46, x0 + 14, 152, rgb('eef1f5'), WHITE, STONE)
        d.rectangle([x0 + 11, 46, x0 + 14, 152], fill=STONE)
        for y in range(64, 150, 22):
            d.line([(x0 + 1, y), (x0 + 14, y)], fill=STONE_LO)
        for y in (50, 144):
            d.rectangle([x0, y, x0 + 14, y + 2], fill=KEY); d.line([(x0, y), (x0 + 14, y)], fill=KEY_HI)
        d.rectangle([x0 + 3, 98, x0 + 10, 126], fill=NAVY)        # a poster case
        d.rectangle([x0 + 4, 99, x0 + 9, 110], fill=KEY_HI); d.rectangle([x0 + 4, 113, x0 + 9, 125], fill=RED_HI)
        d.line([(x0 + 5, 103), (x0 + 8, 103)], fill=RUS); d.line([(x0 + 5, 118), (x0 + 8, 118)], fill=WHITE)
        d.rectangle([x0 - 2, 150, x0 + 16, 155], fill=STONE_LO); d.line([(x0 - 2, 150), (x0 + 16, 150)], fill=STONE)
    # ---- the name board right across, gold on indigo ------------------------------------
    d.rectangle([18, 46, 109, 71], fill=rgb('24305e'))
    d.rectangle([18, 46, 109, 71], outline=KEY)
    d.line([(19, 47), (108, 47)], fill=rgb('3a4c8e'))
    text(d, 'KEYAKI', cx - 35, 52, KEY_HI, scale=2)
    for x in (24, 103):                                           # a keyaki leaf roundel each side
        d.ellipse([x - 4, 54, x + 4, 62], fill=KEY)
        d.ellipse([x - 2, 56, x + 2, 60], fill=rgb('24305e'))
        d.point((x, 58), fill=KEY_HI)
    d.rectangle([18, 72, 109, 74], fill=STONE_LO); d.line([(18, 72), (109, 72)], fill=WHITE)
    for x in range(21, 108, 6):                                   # bulbs along the board's foot
        d.point((x, 73), fill=WARM)
    # ---- what hangs in the head of the opening -------------------------------------------
    for i, x in enumerate((22, 36, 84, 98)):
        c, hi = ((RUS, RUS_HI), (MAP, MAP_HI), (rgb('3f7a4a'), GREEN_HI), (KEY, KEY_HI))[i]
        d.rectangle([x, 75, x + 7, 99], fill=c)
        d.line([(x, 75), (x, 99)], fill=hi)
        for y in (79, 85, 91):
            d.rectangle([x + 2, y, x + 5, y + 3], fill=WHITE)
        d.polygon([(x, 100), (x + 7, 100), (x + 3, 103)], fill=c)
    kusudama(d, cx, 75, KUSU_A, r=7, length=36, n=9)
    outline(im)
    return im


def arcade_roof():
    """A length of the arcade's pitched glass roof, 4x4, on a short white
    post each side: the two falls seen from above and the south (the west one
    lit), a ridge and rafters in white steel, like a station canopy. Its
    glass is nearly clear, so the floor and whoever walks on it show. It is drawn two cells above the ground
    (the height of the deck), over its own row and the row south of it, so
    pieces stand every second row behind the gate and make one roof."""
    im, d = canvas(4, 4)                 # 128 x 128
    for x0 in (2, 120):                                           # the posts
        bar(d, x0, 91, x0 + 5, 120, rgb('eef1f5'), WHITE, STONE)
        d.rectangle([x0 + 4, 91, x0 + 5, 120], fill=STONE)
        d.rectangle([x0 - 1, 119, x0 + 6, 123], fill=STONE_LO); d.line([(x0 - 1, 119), (x0 + 6, 119)], fill=STONE)
        d.rectangle([x0, 100, x0 + 5, 101], fill=KEY)
    edge = {}
    for x in range(2, 126):
        u = abs(x - 63.5)
        ys = 91 - round(14 * (1 - u / 61.5))                      # the roof's south edge at this x: a low pitch
        edge[x] = ys
        west = x < 64
        frame, shade_ = (WHITE, STONE) if west else (STONE, STONE_LO)
        for y in range(ys - 64, ys):
            v = y - (ys - 64)
            if x < 6 or x > 121:
                c = frame if (x not in (5, 122)) else shade_      # the eave beam the posts carry
            elif 61 <= x <= 66:
                c = WHITE if x < 63 else (STONE if x < 65 else STONE_LO)      # the ridge
            elif v % 16 == 0 or x in (33, 94):
                c = RAFTER                                        # rafters across each fall, one purlin
            else:
                k = (v // 16) % 2
                c = PANES[k] if west else PANES[2 + k]
            d.point((x, y), fill=c)
    for x in (20, 46, 80, 106):                                   # lamps hung under the rafters
        d.rectangle([x, edge[x] - 2, x + 3, edge[x] - 1], fill=WARM)
    outline(im)
    px = im.load()
    for x in range(1, 127):                                       # no ink where the next piece north joins
        ys = edge.get(x, edge.get(x + 1, edge.get(x - 1)))
        for y in (ys - 65, ys - 66):
            if 0 <= y and px[x, y] == INK and 6 <= x <= 121:
                px[x, y] = CLEAR
    for y in range(im.height):                                    # the glass is see-through
        for x in range(im.width):
            if px[x, y] in PANES:
                px[x, y] = px[x, y][:3] + (70 if px[x, y] in PANES[:2] else 95,)
            elif px[x, y] == RAFTER:
                px[x, y] = RAFTER[:3] + (200,)
    return im


# ==============================================================================
# Samurai quarter: black lacquer and gold
# ==============================================================================
def gold_band(d, x0, y, x1, h=2):
    d.rectangle([x0, y, x1, y + h - 1], fill=GOLD)
    d.line([(x0, y), (x1, y)], fill=GOLD_HI)
    d.point((x1, y + h - 1), fill=GOLD_LO)


def lq_post(d, x0, y0, x1, y1, bands=True):
    bar(d, x0, y0, x1, y1, LQ, LQ_HI, LQ_LO)
    if x1 - x0 >= 4:
        d.line([(x0 + 1, y0), (x0 + 1, y1)], fill=LQ_MID)
    if bands:
        gold_band(d, x0, y0 + 2, x1, 2)
        gold_band(d, x0, y1 - 5, x1, 3)


def samurai_gate():
    im, d = canvas(4, 3)                 # 128 x 96
    copper_roof(d, 12, 33, (14, 113), (1, 126))
    # the lintel: lacquer, gilded ends, the mon
    bar(d, 8, 38, 119, 49, LQ, LQ_HI, LQ_LO)
    d.line([(8, 38), (119, 38)], fill=LQ_HI); d.line([(8, 49), (119, 49)], fill=LQ_LO)
    for x0 in (8, 114):
        d.rectangle([x0, 38, x0 + 5, 49], fill=GOLD); d.line([(x0, 38), (x0, 49)], fill=GOLD_HI)
        d.line([(x0 + 5, 39), (x0 + 5, 49)], fill=GOLD_LO)
    for x in range(22, 108, 8):                                   # gilt nail covers
        if abs(x - 62) > 10:
            d.rectangle([x, 42, x + 1, 44], fill=GOLD_HI); d.point((x + 1, 45), fill=GOLD_LO)
    mon(d, 64, 43, 6)
    # the wing walls: a little copper cap, black boards, cut stone
    for x0, x1 in ((2, 13), (114, 125)):
        d.rectangle([x0, 51, x1, 53], fill=COPPER_P[0]); d.line([(x0, 51), (x1, 51)], fill=COPPER_P[2])
        d.line([(x0, 54), (x1, 54)], fill=COPPER_P[3])
        lacquer_boards(d, x0, 55, x1, 83, batten=6, off=x0 + 2)
        ashlar(d, x0, 84, x1, 91, ch=4, bw=8)
    # the posts and the leaves folded back
    for x0 in (14, 104):
        lq_post(d, x0, 50, x0 + 9, 88)
        d.rectangle([x0 - 1, 88, x0 + 10, 92], fill=ASH); d.line([(x0 - 1, 88), (x0 + 10, 88)], fill=ASH_HI)
        d.line([(x0 - 1, 92), (x0 + 10, 92)], fill=ASH_DK)
    for x0 in (24, 97):
        bar(d, x0, 51, x0 + 6, 89, LQ_MID, LQ_HI if x0 == 24 else LQ, LQ_LO)
        for y in range(56, 88, 8):
            d.point((x0 + 2, y), fill=GOLD_HI); d.point((x0 + 4, y), fill=GOLD)
        gold_band(d, x0, 68, x0 + 6, 2)
    d.rectangle([31, 50, 96, 52], fill=LQ_LO)                     # the shadow under the lintel
    outline(im)
    return im


def fence(kind):
    """One piece of the black board fence. `h` (1x2) runs east-west: a copper
    ridge on a board cap, lapped black boards with battens and gilt nails, on
    two courses of cut stone; `wicket` (1x2) is a roofed side gate, walked
    through. The rest are 1x3, because a fence running NORTH-SOUTH is seen
    end-on: all that shows of it is its cap from above, a narrow copper strip
    between two board edges, a cell and a half up the map from where it
    stands (the fence is as tall as the east-west run). `v` is a length of
    that strip; `end` is the same with the fence's south end under it - the
    copper cap, the board cap, a gilt-banded post, the stone footing, drawn to
    the east-west run's own heights; `corner-e` / `corner-w` end an east-west
    run where the fence turns north: the face stops at a corner post and the
    cap turns up the map over a mitre (`v` goes in the cells above)."""
    light, dark, hi, deep = COPPER_P
    tall = kind in ('v', 'end', 'corner-e', 'corner-w')
    im, d = canvas(1, 3 if tall else 2)  # 32 x 96 or 32 x 64
    oy = 32 if tall else 0

    def cap_h(x0, x1):
        d.rectangle([x0, oy + 16, x1, oy + 17], fill=light); d.line([(x0, oy + 16), (x1, oy + 16)], fill=hi)
        for x in range(x0, x1 + 1, 8):
            d.point((x, oy + 17), fill=deep)
        d.rectangle([x0, oy + 18, x1, oy + 22], fill=LQ_MID)
        d.line([(x0, oy + 18), (x1, oy + 18)], fill=rgb('474a63'))
        d.line([(x0, oy + 22), (x1, oy + 22)], fill=LQ_LO); d.line([(x0, oy + 23), (x1, oy + 23)], fill=INK)

    def face(x0, x1):
        lacquer_boards(d, x0, oy + 24, x1, oy + 51, studs=True)
        ashlar(d, x0, oy + 52, x1, oy + 63)

    # a north-south run from the south and a little west: the stone foot, the boards' lit laps, the copper cap
    STRIP = ((6, ASH_HI), (7, ASH), (8, rgb('3d3f54')), (9, LQ), (10, LQ_LO), (11, rgb('3d3f54')), (12, LQ),
             (13, LQ_LO), (14, hi), (15, light), (16, light), (17, dark), (18, deep), (19, LQ_LO))

    def cap_v(y0, y1):
        for y in range(y0, y1 + 1):
            for x, c in STRIP:
                d.point((x, y), fill=c)
            if y % 8 == 3:                                        # a batten, a gilt nail at each lap
                for x in range(8, 14):
                    d.point((x, y), fill=rgb('474a63'))
                d.point((9, y), fill=GOLD_HI); d.point((12, y), fill=GOLD)
            elif y % 8 == 4:
                for x in range(8, 14):
                    d.point((x, y), fill=LQ_LO)
            if y % 8 == 7:                                        # a seam in the copper
                for x in range(14, 19):
                    d.point((x, y), fill=dark)
            if y % 16 == 15:                                      # a joint in the stone
                d.point((6, y), fill=ASH_DK); d.point((7, y), fill=ASH_DK)

    if kind == 'h':
        cap_h(0, 31); face(0, 31)
    elif kind == 'v':
        cap_v(17, 48)
    elif kind == 'end':
        cap_v(17, 47)
        d.rectangle([6, 48, 20, 49], fill=light); d.line([(6, 48), (20, 48)], fill=hi)       # the copper cap's end
        d.point((20, 49), fill=deep)
        d.rectangle([6, 50, 20, 54], fill=LQ_MID); d.line([(6, 50), (20, 50)], fill=rgb('474a63'))
        d.line([(6, 54), (20, 54)], fill=LQ_LO); d.line([(8, 55), (18, 55)], fill=INK)
        lq_post(d, 8, 56, 18, 83)
        ashlar(d, 6, 84, 20, 95, bw=8, seed=2)
        d.line([(6, 84), (6, 95)], fill=ASH_HI); d.line([(20, 84), (20, 95)], fill=ASH_DK)
    elif kind in ('corner-e', 'corner-w'):
        east = kind == 'corner-e'
        fx0, fx1 = (0, 19) if east else (6, 31)
        cap_v(17, 47)                                             # the run going north
        cap_h(0 if east else 5, 20 if east else 31)               # its copper turns along the east-west cap
        face(fx0, fx1)
        px = fx1 - 5 if east else fx0
        lq_post(d, px, oy + 24, px + 5, oy + 51)                  # the corner post
        d.point((14, 47), fill=deep); d.point((15, 48), fill=deep)               # the mitre in the copper
    elif kind == 'wicket':
        copper_roof(d, 8, 14, (3, 28), (0, 31), ridge=False)
        d.rectangle([2, 5, 29, 7], fill=dark); d.line([(2, 5), (29, 5)], fill=hi)
        bar(d, 0, 19, 31, 24, LQ, LQ_HI, LQ_LO)
        d.line([(0, 19), (31, 19)], fill=LQ_HI)
        mon(d, 15, 21, 3)
        for x0 in (0, 27):
            lq_post(d, x0, 25, x0 + 4, 60)
            d.rectangle([x0, 60, x0 + 4, 63], fill=ASH); d.line([(x0, 60), (x0 + 4, 60)], fill=ASH_HI)
        bar(d, 5, 25, 8, 61, LQ_MID, LQ_HI, LQ_LO)                # the leaf, folded back
        d.point((6, 34), fill=GOLD_HI); d.point((6, 44), fill=GOLD_HI); d.point((6, 54), fill=GOLD)
    outline(im)
    return im


def engawa(d, x0, x1, y0, y1, open_at=None, lit=()):
    """A veranda: paper screens behind a timber deck on short posts and stones.
    y0 is the screens' head, y1 the ground."""
    deck = y1 - 12
    n = max(1, (x1 - x0 + 1) // 13)
    w = (x1 - x0 + 1) / n
    for i in range(n):
        a, b = round(x0 + i * w), round(x0 + (i + 1) * w) - 1
        if i == open_at:                                          # one screen slid back: the room, an alcove
            d.rectangle([a, y0, b, deck - 1], fill=rgb('3a2c2c'))
            d.rectangle([a + 3, y0 + 4, b - 3, deck - 6], fill=PAPER_LO)        # a hanging scroll
            d.line([(a + 5, y0 + 8), (b - 5, y0 + 14)], fill=INK)
            d.line([(a + 5, y0 + 16), (b - 6, y0 + 16)], fill=CREAM_DK)
            d.rectangle([a + 2, deck - 5, b - 2, deck - 3], fill=rgb('7a9a5a'))  # tatami
        else:
            shoji(d, a, y0, b, deck - 1, lit=i in lit)
    d.rectangle([x0, y0 - 3, x1, y0 - 1], fill=LQ); d.line([(x0, y0 - 3), (x1, y0 - 3)], fill=LQ_HI)
    d.rectangle([x0 - 1, deck, x1 + 1, deck + 3], fill=WOOD)      # the deck, its boards end-on
    d.line([(x0 - 1, deck), (x1 + 1, deck)], fill=rgb('d2a58c'))
    for x in range(x0, x1 + 1, 4):
        d.point((x, deck + 2), fill=WOOD_LO)
    d.line([(x0 - 1, deck + 4), (x1 + 1, deck + 4)], fill=WOOD_DK)
    d.rectangle([x0, deck + 5, x1, y1], fill=rgb('2a2228'))       # under the floor
    for x in range(x0 + 3, x1 - 2, 14):
        d.rectangle([x, deck + 5, x + 2, y1 - 3], fill=WOOD_LO)
        d.rectangle([x - 1, y1 - 2, x + 3, y1], fill=ASH); d.line([(x - 1, y1 - 2), (x + 3, y1 - 2)], fill=ASH_HI)


def lit_door(d, x0, y0, x1, y1):
    """The way in: one lattice leaf slid back on the dark of the entry (a lamp
    burning inside), the other closed, under a gilt-nailed head. Dark, so it
    cannot be taken for one of the lit paper windows."""
    d.rectangle([x0, y0, x1, y1], fill=LQ)
    m = (x0 + x1) // 2
    d.rectangle([x0 + 1, y0 + 7, m, y1], fill=rgb('1d1418'))      # the open half
    d.rectangle([x0 + 3, y1 - 12, m - 2, y1 - 6], fill=rgb('5a3a2a'))        # a step up into the house
    d.line([(x0 + 3, y1 - 12), (m - 2, y1 - 12)], fill=rgb('8a6248'))
    d.rectangle([x0 + 4, y0 + 13, x0 + 6, y0 + 17], fill=WARM); d.point((x0 + 5, y0 + 12), fill=LIT)   # the lamp
    d.rectangle([m + 1, y0 + 7, x1 - 1, y1], fill=WOOD_LO)        # the closed leaf: a timber lattice
    for x in range(m + 2, x1 - 1, 2):
        d.line([(x, y0 + 8), (x, y1 - 1)], fill=WOOD)
    for y in (y0 + 16, y0 + 28):
        d.line([(m + 1, y), (x1 - 1, y)], fill=WOOD_DK)
    d.line([(m + 1, y0 + 7), (m + 1, y1)], fill=WOOD_DK)
    d.rectangle([x0, y0, x1, y0 + 6], fill=LQ_MID); d.line([(x0, y0), (x1, y0)], fill=LQ_HI)
    for x in range(x0 + 3, x1 - 1, 5):
        d.point((x, y0 + 3), fill=GOLD_HI)
    d.line([(x0, y0 + 6), (x1, y0 + 6)], fill=GOLD_LO)


def step_stone(d, x0, x1, y):
    """The shoe stone before a door: one long pale slab, standing proud."""
    d.rectangle([x0, y, x1, y + 4], fill=rgb('c9ccd4'))
    d.line([(x0, y), (x1, y)], fill=WHITE); d.line([(x0, y + 4), (x1, y + 4)], fill=ASH_DK)
    d.line([(x0, y), (x0, y + 3)], fill=WHITE); d.line([(x1, y + 1), (x1, y + 4)], fill=ASH_LO)


def samurai_house(variant):
    if variant == 'a':
        im, d = canvas(5, 4)             # 160 x 128: thatch over an engawa, the door, a boarded bay
        thatch_roof(d, 16, 62, (46, 113), (3, 156))
        d.rectangle([8, 68, 151, 120], fill=LQ_LO)
        engawa(d, 12, 61, 74, 120, open_at=2, lit=(0,))
        lit_door(d, 66, 72, 93, 116)
        mon(d, 79, 75, 3)
        lacquer_boards(d, 99, 69, 148, 113, studs=True)
        d.rectangle([108, 78, 139, 97], fill=LQ_LO)               # a barred window, gilt-framed
        d.rectangle([109, 79, 138, 96], fill=rgb('3a2c2c'))
        for x in range(111, 138, 4):
            d.rectangle([x, 79, x + 1, 96], fill=WOOD_LO); d.line([(x, 79), (x, 96)], fill=WOOD)
        d.rectangle([107, 77, 140, 77], fill=GOLD); d.rectangle([107, 98, 140, 98], fill=GOLD_LO)
        ashlar(d, 98, 114, 149, 120, ch=7, bw=16)
        bar(d, 138, 104, 147, 119, WOOD, rgb('d2a58c'), WOOD_LO)  # a rain tub, a dipper on it
        d.line([(138, 108), (147, 108)], fill=WOOD_DK); d.line([(138, 115), (147, 115)], fill=WOOD_DK)
        d.rectangle([139, 103, 146, 104], fill=SEA_HI)
        for x in (8, 62, 95, 149):
            lq_post(d, x, 68, x + 2, 120, bands=False)
        d.rectangle([6, 121, 153, 123], fill=ASH_LO); d.line([(6, 121), (153, 121)], fill=ASH)
        step_stone(d, 66, 93, 118)
    else:
        im, d = canvas(4, 4)             # 128 x 128: thatch above, a shingle pent over door and engawa
        thatch_roof(d, 16, 50, (36, 91), (5, 122))
        d.rectangle([8, 56, 119, 62], fill=LQ)                    # the wall between the two roofs
        for x in range(12, 118, 10):
            d.rectangle([x, 57, x + 5, 60], fill=PAPER); d.line([(x, 61), (x + 5, 61)], fill=PAPER_LO)
        shingle_pent(d, 62, 73, 6, 121)
        d.rectangle([8, 76, 119, 120], fill=LQ_LO)
        lacquer_boards(d, 9, 77, 35, 113, studs=True)
        d.ellipse([14, 84, 30, 100], fill=GOLD)                   # a round window in a gilt rim
        d.ellipse([15, 85, 29, 99], fill=PAPER)
        d.line([(22, 85), (22, 99)], fill=rgb('8a7a66')); d.line([(15, 92), (29, 92)], fill=rgb('8a7a66'))
        d.line([(18, 86), (18, 98)], fill=rgb('b0a28a')); d.line([(26, 86), (26, 98)], fill=rgb('b0a28a'))
        ashlar(d, 9, 114, 36, 120, ch=7, bw=16)
        lit_door(d, 39, 78, 60, 116)
        engawa(d, 65, 118, 81, 120, lit=(1,))
        for x in (6, 36, 61, 119):
            lq_post(d, x, 76, x + 2, 120, bands=False)
        d.rectangle([4, 121, 123, 123], fill=ASH_LO); d.line([(4, 121), (123, 121)], fill=ASH)
        step_stone(d, 39, 60, 118)
    outline(im)
    return im


def well():
    im, d = canvas(1, 2)                 # 32 x 64
    copper_roof(d, 6, 12, (6, 25), (2, 29), ridge=False, gold=False)
    d.rectangle([5, 3, 26, 5], fill=COPPER_P[1]); d.line([(5, 3), (26, 3)], fill=COPPER_P[2])
    for x0 in (5, 24):                                            # the posts
        bar(d, x0, 17, x0 + 2, 47, LQ, LQ_HI, LQ_LO)
    bar(d, 4, 17, 27, 19, LQ, LQ_HI, LQ_LO)                       # the beam the pulley hangs from
    d.ellipse([13, 20, 18, 25], fill=WOOD_LO); d.point((15, 22), fill=WOOD_DK)             # the pulley
    d.line([(13, 23), (13, 44)], fill=CREAM_LO); d.line([(18, 23), (18, 33)], fill=CREAM_LO)   # the rope
    bar(d, 16, 33, 21, 39, WOOD, rgb('d2a58c'), WOOD_LO)          # the bucket
    d.line([(16, 36), (21, 36)], fill=WOOD_DK)
    # the stone curb: a square of cut blocks, the dark of the shaft
    d.rectangle([3, 42, 28, 47], fill=ASH_HI)
    d.rectangle([7, 43, 24, 46], fill=rgb('1b2040'))
    d.line([(8, 45), (14, 45)], fill=SEA_DK)
    d.line([(3, 47), (28, 47)], fill=ASH_LO)
    ashlar(d, 3, 48, 28, 59, ch=6, bw=13, seed=1)
    d.line([(3, 48), (3, 59)], fill=ASH_HI); d.line([(28, 48), (28, 59)], fill=ASH_DK)
    d.rectangle([2, 60, 29, 61], fill=ASH_LO)
    for x, y in ((5, 58), (9, 59), (25, 57)):                     # moss at its foot
        d.point((x, y), fill=GREEN_HI)
    outline(im)
    return im


def propped_pine():
    im, d = canvas(3, 3)                 # 96 x 96
    # the trunk leans east; one long limb runs out level and is carried on props
    trunk(d, [(20, 92), (22, 76), (30, 62), (30, 48), (24, 36)], 7)
    trunk(d, [(30, 62), (46, 58), (66, 60), (88, 56)], 5)
    trunk(d, [(30, 50), (40, 40), (52, 36)], 4)
    trunk(d, [(26, 40), (14, 34)], 3)
    for x, top in ((68, 61), (84, 59)):                           # the props: a post and a padded crutch
        bar(d, x, top, x + 2, 92, WOOD, rgb('d2a58c'), WOOD_LO)
        d.rectangle([x - 3, top - 1, x + 5, top + 1], fill=WOOD_LO); d.line([(x - 3, top - 1), (x + 5, top - 1)], fill=WOOD)
        d.rectangle([x - 1, top - 3, x + 3, top - 2], fill=rgb('cdb67c'))      # straw rope padding
        d.line([(x - 4, 92), (x + 6, 92)], fill=ASH_LO)
    d.rectangle([18, 90, 24, 93], fill=BARK_LO)
    for cx, cy, rx, ry, s in ((12, 32, 12, 6, 1), (24, 24, 15, 8, 2), (44, 18, 14, 7, 3), (56, 30, 12, 6, 4),
                              (30, 12, 11, 6, 5), (48, 50, 12, 6, 6), (66, 51, 11, 5, 7), (86, 48, 9, 5, 8),
                              (66, 42, 10, 5, 9)):
        blob(d, cx, cy, rx, ry, PINE, PINE_HI, PINE_LO, s)
        d.line([(cx - rx + 3, cy + ry - 1), (cx + rx - 3, cy + ry - 1)], fill=PINE_DK)
    outline(im)
    return grounded(im, [(8, 86, 90, 95)])


def kabuto_stand():
    im, d = canvas(2, 3)                 # 64 x 96
    # ---- a low dais and a folding screen in gold leaf behind ---------------------
    d.rectangle([4, 84, 59, 90], fill=LQ); d.line([(4, 84), (59, 84)], fill=LQ_HI)
    d.line([(4, 90), (59, 90)], fill=LQ_LO)
    gold_band(d, 4, 86, 59, 2)
    d.rectangle([2, 91, 61, 93], fill=ASH_LO); d.line([(2, 91), (61, 91)], fill=ASH)
    for i in range(4):                                            # four leaves of the screen, zig-zag
        x0 = 6 + i * 13
        top = 30 + (2 if i % 2 else 0)
        d.rectangle([x0, top, x0 + 12, 83], fill=rgb('e3bf5c') if i % 2 == 0 else rgb('c9a244'))
        d.line([(x0, top), (x0 + 12, top)], fill=rgb('fff0a8'))
        d.rectangle([x0, top, x0 + 12, 83], outline=LQ)
        for k in range(5):
            xx, yy = x0 + 2 + (k * 5 + i * 3) % 9, top + 5 + (k * 11 + i * 7) % 40
            d.point((xx, yy), fill=rgb('fff0a8'))
    d.line([(10, 62), (18, 52), (24, 58)], fill=PINE_LO)          # a painted pine bough on the leaf
    d.line([(44, 66), (52, 56)], fill=PINE_LO)
    # ---- the armour chest ------------------------------------------------------------
    bar(d, 19, 68, 44, 83, LQ, LQ_HI, LQ_LO)
    d.rectangle([19, 68, 44, 69], fill=LQ_HI)
    gold_band(d, 19, 71, 44, 1); gold_band(d, 19, 80, 44, 1)
    mon(d, 32, 76, 3)
    # ---- the cuirass: black plates laced in gold, shoulder guards, a skirt -------
    d.polygon([(24, 46), (39, 46), (41, 62), (22, 62)], fill=LQ_MID)
    d.line([(24, 46), (22, 62)], fill=LQ_HI)
    for y in range(48, 62, 3):
        d.line([(24, y), (39, y)], fill=GOLD if y % 2 else GOLD_LO)
    d.line([(31, 46), (31, 62)], fill=LQ_LO); d.line([(32, 46), (32, 62)], fill=LQ_LO)
    for x0 in (16, 41):                                           # sode
        d.rectangle([x0, 45, x0 + 6, 58], fill=LQ)
        for y in range(47, 58, 3):
            d.line([(x0, y), (x0 + 6, y)], fill=GOLD)
        d.line([(x0, 45), (x0, 58)], fill=LQ_HI)
    for i, x0 in enumerate((22, 27, 32, 37)):                     # kusazuri tassets
        d.rectangle([x0, 62, x0 + 3, 67], fill=LQ)
        d.line([(x0, 64), (x0 + 3, 64)], fill=GOLD); d.line([(x0, 66), (x0 + 3, 66)], fill=VERM)
    # ---- the helmet: a black bowl, a flared neck guard, the mask, the crescent ----
    d.polygon([(21, 44), (42, 44), (39, 38), (24, 38)], fill=LQ)  # the shikoro
    d.line([(22, 42), (41, 42)], fill=GOLD); d.line([(23, 40), (40, 40)], fill=GOLD_LO)
    d.rectangle([27, 38, 36, 45], fill=rgb('2a2630'))             # the menpo: a dark iron half-mask
    d.line([(27, 38), (27, 45)], fill=LQ_HI)
    d.rectangle([28, 40, 30, 40], fill=INK); d.rectangle([33, 40, 35, 40], fill=INK)
    d.line([(31, 41), (32, 43)], fill=LQ_HI)                      # its nose
    d.line([(28, 45), (35, 45)], fill=VERM_LO)                    # the cord under the chin
    d.pieslice([24, 26, 39, 44], 180, 360, fill=LQ)               # the bowl
    d.arc([24, 26, 39, 44], 180, 260, fill=LQ_HI)
    d.rectangle([24, 35, 39, 37], fill=LQ_MID); d.line([(24, 35), (39, 35)], fill=GOLD)     # the peak
    for x in range(26, 39, 3):
        d.line([(x, 28 + abs(x - 31) // 3), (x, 34)], fill=LQ_HI if x < 31 else LQ_LO)
    # the crescent: one great thin moon of gold, its horns up, the east one longer
    for y in range(4, 36):
        for x in range(8, 58):
            outer = ((x - 33) / 23.0) ** 2 + ((y - 14) / 19.0) ** 2 <= 1
            inner = ((x - 34.5) / 22.0) ** 2 + ((y - 9.5) / 19.5) ** 2 <= 1
            if outer and not inner and not (x < 14 and y < 14):
                d.point((x, y), fill=GOLD_HI if x < 30 else (GOLD if x < 46 else GOLD_LO))
    d.rectangle([30, 31, 34, 34], fill=GOLD); d.point((30, 31), fill=GOLD_HI)             # its socket on the peak
    outline(im)
    return grounded(im, [(2, 88, 62, 95)])


# ==============================================================================
# The distillery yard, and Yamadera on the hill behind
# ==============================================================================
SLATE_P = (SLATE, SLATE_LO, SLATE_HI, rgb('1e2636'))


def brick_px(x, y, shade_=False):
    """One pixel of running-bond brickwork (generate_sapporo_art.brick's bond)."""
    base, lo = (BRICK_LO, BRICK_DK) if shade_ else (BRICK, BRICK_LO)
    course = y // 3
    if y % 3 == 2 or (x + course * 4) % 8 == 0:
        return lo
    k = ((x + course * 4) // 8 * 7 + course * 13) % 11
    return BRICK_HI if (k == 0 and not shade_) else (lo if k == 5 else base)


def pot_still(d, cx, base):
    """A copper pot still: a round pot, a tall tapering neck, the lyne arm
    bending away at the top."""
    d.line([(cx, base - 54), (cx + 10, base - 57), (cx + 19, base - 52)], fill=CU_LO, width=3)    # the lyne arm
    d.line([(cx, base - 55), (cx + 10, base - 58), (cx + 19, base - 53)], fill=CU)
    for y in range(base - 54, base - 30):                         # the neck
        t = (y - (base - 54)) / 24.0
        w = 2 + round(5 * t * t + 1.5 * t)
        d.line([(cx - w, y), (cx + w, y)], fill=CU)
        d.point((cx - w, y), fill=CU_HI); d.point((cx - w + 1, y), fill=CU_HI)
        d.point((cx + w, y), fill=CU_DK); d.point((cx + w - 1, y), fill=CU_LO)
    d.ellipse([cx - 14, base - 34, cx + 14, base - 4], fill=CU)   # the pot
    d.chord([cx - 14, base - 34, cx + 14, base - 4], -40, 80, fill=CU_LO)
    d.chord([cx - 14, base - 34, cx + 14, base - 4], 30, 150, fill=CU_LO)
    d.arc([cx - 14, base - 34, cx + 14, base - 4], 150, 250, fill=CU_HI)
    d.ellipse([cx - 10, base - 30, cx - 5, base - 22], fill=CU_HI)
    d.point((cx - 9, base - 29), fill=WHITE); d.point((cx - 8, base - 28), fill=WHITE)
    d.line([(cx - 13, base - 18), (cx + 13, base - 18)], fill=CU_DK)          # a riveted seam
    for x in range(cx - 12, cx + 13, 3):
        d.point((x, base - 19), fill=CU_HI)
    d.ellipse([cx + 1, base - 16, cx + 8, base - 9], fill=CU_DK)  # the manhole
    d.ellipse([cx + 2, base - 15, cx + 7, base - 10], fill=CU_LO); d.point((cx + 3, base - 14), fill=CU_HI)
    d.line([(cx - 7, base - 31), (cx + 7, base - 31)], fill=CU_DK)            # the collar
    d.rectangle([cx - 15, base - 5, cx + 15, base], fill=rgb('5c3b37'))        # its brick hearth
    d.line([(cx - 15, base - 5), (cx + 15, base - 5)], fill=rgb('77514a'))
    d.rectangle([cx - 5, base - 3, cx + 5, base - 1], fill=COAL); d.point((cx, base - 2), fill=AMBER)


def cask_end(d, cx, cy, r, mark=0):
    """A cask seen end on: the head's boards, the chime hoop, a stencil."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=STONE_DK)
    d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], fill=WOOD_LO)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=WOOD)
    d.chord([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], 10, 150, fill=rgb('a87862'))
    for x in range(cx - r + 5, cx + r - 3, 4):
        h = int(math.sqrt(max(0, (r - 3) ** 2 - (x - cx) ** 2)))
        d.line([(x, cy - h + 1), (x, cy + h - 1)], fill=WOOD_LO)
    d.arc([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], 170, 280, fill=rgb('d2a58c'))
    d.arc([cx - r, cy - r, cx + r, cy + r], 180, 270, fill=STONE_LO)
    d.rectangle([cx - 4, cy - 3, cx + 3, cy + 1], fill=PAPER if mark % 2 == 0 else rgb('3a3336'))   # the stencil
    d.line([(cx - 3, cy - 1), (cx + 2, cy - 1)], fill=INK if mark % 2 == 0 else PAPER)
    d.point((cx + (2 if mark % 2 else -2), cy + 5), fill=WOOD_DK)                 # the bung


def distillery_warehouse():
    im, d = canvas(6, 4)                 # 192 x 128
    roof(d, 12, 40, (16, 175), (2, 189), SLATE_P, ridge=True, caps=False, p=1.2)
    for x in (40, 148):                                           # roof vents
        bar(d, x, 2, x + 9, 9, rgb('5c3b37'), rgb('77514a'), rgb('432a2b'))
        d.rectangle([x - 1, 0, x + 10, 2], fill=SLATE_LO)
    # ---- the brick body ------------------------------------------------------------
    for y in range(45, 116):
        for x in range(6, 186):
            d.point((x, y), fill=brick_px(x, y, x > 176))
    d.rectangle([4, 43, 187, 46], fill=CREAM); d.line([(4, 43), (187, 43)], fill=WHITE)   # a stone cornice
    d.line([(4, 46), (187, 46)], fill=CREAM_DK)
    for x in range(8, 186, 6):                                    # dentils of brick under it
        d.rectangle([x, 47, x + 2, 48], fill=BRICK_DK)
    # ---- the centre gable, a cask in its roundel -------------------------------------
    for y in range(8, 45):
        half = round((y - 6) * 36 / 38)
        for x in range(96 - half, 96 + half):
            d.point((x, y), fill=brick_px(x, y))
        d.point((96 - half - 1, y), fill=CREAM); d.point((96 - half, y), fill=WHITE)
        d.point((96 + half, y), fill=CREAM_LO); d.point((96 + half - 1, y), fill=CREAM)
    d.rectangle([92, 4, 99, 8], fill=CREAM); d.line([(92, 4), (99, 4)], fill=WHITE)
    d.ellipse([85, 18, 106, 39], fill=CREAM)
    cask_end(d, 96, 29, 8, 1)
    # ---- arched windows with iron shutters (cells 0, 1 and 5) --------------------------
    for i, x in enumerate((16, 42, 164)):
        d.rectangle([x - 2, 66, x + 13, 97], fill=CREAM)
        d.pieslice([x - 2, 58, x + 13, 74], 180, 360, fill=CREAM)
        arch_window(d, x, 60, 96, 11, glass=WARM if i == 1 else GLASS_DK, hi=WHITE if i == 1 else GLASS,
                    frame=rgb('2f4a44'))
        d.rectangle([x - 2, 97, x + 13, 98], fill=WHITE); d.line([(x - 2, 99), (x + 13, 99)], fill=BRICK_DK)
        for sx in (x - 8, x + 14):                                # the shutters, folded back
            d.rectangle([sx, 66, sx + 5, 96], fill=rgb('2f4a44'))
            d.line([(sx, 66), (sx, 96)], fill=rgb('46695c'))
            for y in (72, 82, 92):
                d.line([(sx, y), (sx + 5, y)], fill=rgb('1e302f'))
    # ---- the still room's great arched WINDOW (cells 2-3): the pot still behind a rail --
    d.rectangle([70, 76, 121, 115], fill=CREAM)
    d.pieslice([70, 50, 121, 102], 180, 360, fill=CREAM)
    for k in range(13):                                           # the joints of the arch stones
        a = math.radians(180 + k * 15)
        d.line([(96 + 22 * math.cos(a), 76 + 22 * math.sin(a)), (96 + 26 * math.cos(a), 76 + 26 * math.sin(a))],
               fill=CREAM_DK)
    d.rectangle([74, 76, 117, 112], fill=rgb('2c1e20'))
    d.pieslice([74, 54, 117, 98], 180, 360, fill=rgb('2c1e20'))
    d.pieslice([78, 58, 113, 94], 180, 360, fill=rgb('4a2f28'))   # the lamplit back wall
    d.rectangle([78, 76, 113, 110], fill=rgb('4a2f28'))
    for y in range(64, 110, 6):
        d.line([(80, y), (111, y)], fill=rgb('3a2422'))
    pot_still(d, 93, 112)
    d.rectangle([109, 68, 112, 110], fill=CU_LO); d.line([(109, 68), (109, 110)], fill=CU)      # the condenser pipe
    d.line([(74, 100), (117, 100)], fill=SOOT)                    # an iron rail across the opening
    for x in range(75, 118, 4):
        d.line([(x, 100), (x, 110)], fill=SOOT)
    d.rectangle([70, 110, 121, 112], fill=WHITE); d.line([(70, 112), (121, 112)], fill=CREAM_DK)  # its stone sill
    for y in range(113, 116):
        for x in range(70, 122):
            d.point((x, y), fill=brick_px(x, y))
    d.rectangle([65, 49, 126, 59], fill=SOOT)                     # the board
    d.rectangle([65, 49, 126, 59], outline=GOLD_LO)
    text(d, 'DISTILLERY', 96 - text_w('DISTILLERY') // 2, 51, PAPER)
    # ---- the door (cell 4): green double doors in a stone surround, a fanlight, a lamp --
    d.rectangle([131, 76, 156, 115], fill=CREAM)
    d.pieslice([131, 63, 156, 89], 180, 360, fill=CREAM)
    d.line([(131, 76), (131, 115)], fill=WHITE); d.line([(156, 76), (156, 115)], fill=CREAM_DK)
    d.pieslice([134, 66, 153, 86], 180, 360, fill=WARM)           # the fanlight
    for a in (210, 240, 270, 300, 330):
        r = math.radians(a)
        d.line([(143.5, 76), (143.5 + 10 * math.cos(r), 76 + 10 * math.sin(r))], fill=rgb('2f4a44'))
    d.rectangle([134, 77, 153, 115], fill=rgb('1e302f'))
    for x0 in (135, 144):                                         # two panelled leaves
        d.rectangle([x0, 78, x0 + 8, 115], fill=rgb('2f4a44'))
        d.line([(x0, 78), (x0, 115)], fill=rgb('46695c'))
        d.rectangle([x0 + 2, 81, x0 + 6, 93], fill=rgb('24403a')); d.rectangle([x0 + 2, 97, x0 + 6, 112], fill=rgb('24403a'))
        d.line([(x0 + 2, 81), (x0 + 6, 81)], fill=rgb('1e302f')); d.line([(x0 + 2, 97), (x0 + 6, 97)], fill=rgb('1e302f'))
    d.point((142, 96), fill=GOLD_HI); d.point((145, 96), fill=GOLD_HI)
    d.rectangle([141, 58, 146, 63], fill=SOOT); d.rectangle([142, 59, 145, 62], fill=WARM)       # the lamp over it
    d.line([(143, 55), (143, 57)], fill=SOOT)
    # ---- ivy gone red up the east corner, casks by the west window -----------------
    for y in range(47, 116):
        for x in range(158, 186):
            reach = (x - 150) / 36.0 + (116 - y) / 200.0
            if 154 <= x <= 180 and 56 <= y <= 100:
                continue                                          # it is kept cut back round the window
            if h3(x, y, 13) < 255 * max(0.0, reach - 0.3) * 1.3:
                d.point((x, y), fill=(MAP, MAP_HI, MAP_LO, RUS, MAP)[h3(x, y, 3) % 5])
    cask_end(d, 16, 108, 8, 0); cask_end(d, 34, 108, 8, 1)
    d.rectangle([4, 116, 187, 121], fill=ASH); d.line([(4, 116), (187, 116)], fill=ASH_HI)
    d.line([(4, 121), (187, 121)], fill=ASH_DK)
    d.rectangle([180, 116, 187, 121], fill=ASH_LO)
    step_stone(d, 130, 157, 117)                                  # the door's step
    outline(im)
    return im


def cask_rack():
    im, d = canvas(3, 2)                 # 96 x 64: five casks end-on, on chocks
    d.rectangle([3, 57, 92, 60], fill=WOOD_LO); d.line([(3, 57), (92, 57)], fill=WOOD)
    d.line([(3, 60), (92, 60)], fill=WOOD_DK)
    for i, cx in enumerate((18, 48, 78)):
        cask_end(d, cx, 44, 13, i)
    for i, cx in enumerate((33, 63)):
        cask_end(d, cx, 21, 13, i + 1)
    for x in (4, 32, 62, 90):                                     # the chocks
        d.polygon([(x - 3, 57), (x + 3, 57), (x, 51)], fill=WOOD_LO)
    outline(im)
    return grounded(im, [(2, 54, 94, 63)])


def red_maple():
    im, d = canvas(3, 4)                 # 96 x 128
    trunk(d, [(48, 122), (46, 100), (48, 84)], 7)
    trunk(d, [(47, 96), (30, 76), (20, 60)], 4); trunk(d, [(48, 90), (62, 72), (76, 58)], 4)
    trunk(d, [(48, 86), (46, 60), (48, 40)], 4)
    d.polygon([(41, 122), (44, 114), (52, 114), (56, 122)], fill=BARK)
    d.line([(52, 114), (56, 122)], fill=BARK_LO)
    pads = ((48, 22, 24, 13, 1, 0), (22, 36, 19, 11, 2, 1), (74, 36, 19, 11, 3, 0), (48, 46, 26, 12, 4, 0),
            (13, 54, 11, 8, 5, 2), (83, 54, 11, 8, 6, 1), (32, 62, 15, 9, 7, 0), (64, 62, 15, 9, 8, 2),
            (36, 14, 13, 8, 9, 1), (62, 13, 13, 8, 10, 0), (48, 72, 10, 6, 11, 1))
    pal = ((MAP, MAP_HI, MAP_LO), (MAP_HI, COAL, MAP), (MAP_LO, MAP, MAP_DK))
    for px, py, rx, ry, s, tone in sorted(pads, key=lambda p_: -p_[1]):
        a, b, c = pal[tone]
        blob(d, px, py, rx, ry, a, b, c, s)
    for i in range(120):
        x, y = 4 + (i * 31) % 88, 4 + (i * 19) % 74
        if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] not in (BARK[:3], BARK_LO[:3]):
            d.point((x, y), fill=(COAL, MAP_DK, rgb('f6b05a'), MAP_HI)[i % 4])
    outline(im)
    return grounded(im, [(16, 112, 82, 126)], leaves=(12, 86, 113, 126, (MAP, MAP_HI, MAP_LO, COAL), 40, 2))


def yamadera():
    """The hill behind the distillery, a backdrop for the room's north edge:
    a wooded mountain in autumn colour, two pale crags above the trees, the
    red hall on the higher one and the lookout stage on stilts on the other,
    the stone stair climbing through the wood from a gate at the foot. The
    trees are a canopy of small pads - far smaller than the halls."""
    im, d = canvas(6, 6)                 # 192 x 192

    def top(x):
        return (104 - 30 * math.exp(-((x - 56) / 19.0) ** 2) - 40 * math.exp(-((x - 128) / 22.0) ** 2)
                - 12 * math.exp(-((x - 96) / 60.0) ** 2) + 2.0 * math.sin(x / 3.3) + 1.5 * math.sin(x / 1.7)
                + max(0, 34 - x) * 2.3 + max(0, x - 158) * 2.3)

    def tree_line(x):
        return 112 + 9 * math.sin(x / 17.0) + 5 * math.sin(x / 6.0 + 1) - 16 * math.exp(-((x - 92) / 9.0) ** 2)

    # ---- the rock: pale tuff in strata and ledges, lit from the west ------------------
    for x in range(4, 188):
        t = int(top(x))
        slope = top(x + 2) - top(x - 2)
        for y in range(max(2, t), 186):
            depth = y - t
            strata = (x + int(5 * math.sin(y / 11.0)) + (y // 23) * 3) % 9
            ledge = (y + int(4 * math.sin(x / 7.0))) % 17
            if strata == 0 or ledge == 0:
                c = ROCK_DK
            elif ledge == 1:
                c = ROCK_HI
            elif slope < -1.2 or strata in (1, 2):
                c = ROCK_HI if depth < 30 and strata == 1 else ROCK
            elif slope > 1.2 or strata in (7, 8):
                c = ROCK_LO
            else:
                c = ROCK if h3(x, y, 5) > 26 else ROCK_LO
            if depth < 2:
                c = ROCK_HI
            d.point((x, y), fill=c)
    # ---- the lookout stage on the west crag: a timber hall on a stage on tall stilts ----
    lx, ly = 56, int(top(56)) + 2
    for x in (lx - 14, lx - 5, lx + 4, lx + 13):
        bar(d, x, ly - 12, x + 1, ly + 8 + abs(x - lx) // 4, WOOD_LO, WOOD, WOOD_DK)
    d.line([(lx - 14, ly - 4), (lx + 14, ly + 2)], fill=WOOD_DK); d.line([(lx - 14, ly + 2), (lx + 14, ly - 4)], fill=WOOD_DK)
    d.rectangle([lx - 18, ly - 16, lx + 18, ly - 12], fill=WOOD); d.line([(lx - 18, ly - 16), (lx + 18, ly - 16)], fill=rgb('d2a58c'))
    d.line([(lx - 18, ly - 12), (lx + 18, ly - 12)], fill=WOOD_DK)
    d.rectangle([lx - 15, ly - 31, lx + 15, ly - 17], fill=rgb('3a2c2c'))     # the open hall: posts, a rail
    for x in range(lx - 15, lx + 16, 6):
        d.line([(x, ly - 31), (x, ly - 17)], fill=WOOD)
    d.line([(lx - 17, ly - 22), (lx + 17, ly - 22)], fill=WOOD); d.line([(lx - 17, ly - 20), (lx + 17, ly - 20)], fill=WOOD_LO)
    roof(d, ly - 42, ly - 33, (lx - 11, lx + 11), (lx - 21, lx + 21),
         (rgb('6e5a50'), rgb('4c3d39'), rgb('93786a'), rgb('33292a')), ridge=False, step=3)
    d.rectangle([lx - 12, ly - 46, lx + 12, ly - 43], fill=rgb('4c3d39'))
    d.line([(lx - 12, ly - 46), (lx + 12, ly - 46)], fill=rgb('93786a'))
    # ---- the red hall on the east pinnacle ----------------------------------------------
    hx, hy = 128, int(top(128)) + 3
    d.rectangle([hx - 19, hy - 4, hx + 19, hy], fill=ASH); d.line([(hx - 19, hy - 4), (hx + 19, hy - 4)], fill=ASH_HI)
    d.line([(hx - 19, hy), (hx + 19, hy)], fill=ASH_DK)
    bar(d, hx - 16, hy - 24, hx + 16, hy - 5, VERM, VERM_HI, VERM_LO)
    d.rectangle([hx + 10, hy - 24, hx + 16, hy - 5], fill=VERM_LO)
    d.rectangle([hx - 6, hy - 19, hx + 5, hy - 5], fill=rgb('3a2c2c'))        # the doors
    d.line([(hx, hy - 19), (hx, hy - 5)], fill=GOLD_LO); d.point((hx - 2, hy - 12), fill=GOLD_HI); d.point((hx + 2, hy - 12), fill=GOLD_HI)
    for x0 in (hx - 14, hx + 8):
        d.rectangle([x0, hy - 19, x0 + 5, hy - 10], fill=PAPER if x0 < hx else PAPER_LO)
        d.line([(x0 + 3, hy - 19), (x0 + 3, hy - 10)], fill=VERM_LO); d.line([(x0, hy - 15), (x0 + 5, hy - 15)], fill=VERM_LO)
    d.line([(hx - 16, hy - 22), (hx + 16, hy - 22)], fill=WHITE)
    roof(d, hy - 40, hy - 26, (hx - 12, hx + 12), (hx - 24, hx + 24), SLATE_P, ridge=False, step=3, p=1.6)
    d.rectangle([hx - 13, hy - 45, hx + 13, hy - 41], fill=SLATE_LO); d.line([(hx - 13, hy - 45), (hx + 13, hy - 45)], fill=SLATE_HI)
    d.rectangle([hx - 1, hy - 51, hx + 1, hy - 45], fill=GOLD); d.point((hx, hy - 52), fill=GOLD_HI)
    # ---- the wood: a canopy of small pads, upper rows first -----------------------------
    pal = ((MAP, MAP_HI, MAP_LO), (KEY, KEY_HI, KEY_LO), (RUS, RUS_HI, RUS_LO), (MAP_LO, MAP, MAP_DK),
           (PINE, PINE_HI, PINE_LO), (KEY_LO, KEY, KEY_DK), (PINE_LO, PINE, PINE_DK))
    pads = []
    for j in range(13):
        y = 106 + j * 6
        for i in range(-1, 24):
            x = 4 + i * 8 + (j % 2) * 4 + h3(i, j, 3) % 3 - 1
            yy = y + h3(j, i, 5) % 3
            if not 8 <= x <= 184 or yy < tree_line(x) or yy < top(x) + 6:
                continue
            tone = h3((i + j % 2) // 2, j // 2, 11) % 7 if h3(i, j, 29) > 60 else h3(i * 3, j * 7, 11) % 7
            pads.append((yy, x, tone, i * 13 + j))                    # colour comes in drifts
    for x, y in ((40, 92), (72, 96), (150, 84), (104, 84), (168, 104), (24, 110), (112, 96), (84, 106)):   # trees in the clefts
        pads.append((y, x, (x + y) % 7, x))
    for yy, x, tone, s in sorted(pads):
        a, b, c = pal[tone]
        blob(d, x, yy, 6, 5, a, b, c, s)
    for i, (x, y) in enumerate(((16, 150), (34, 128), (50, 144), (74, 124), (118, 122), (142, 136), (160, 120),
                                (176, 150), (130, 160), (62, 166), (22, 172), (154, 172))):                # cedars standing through it
        for k in range(15):
            w = 1 + k // 3
            d.line([(x - w, y - 15 + k), (x + w, y - 15 + k)], fill=PINE_LO if k % 4 == 3 else PINE)
            d.point((x - w, y - 15 + k), fill=PINE_HI)
            d.point((x + w, y - 15 + k), fill=PINE_DK)
    # ---- the stair: stone treads zig-zagging up from the gate ----------------------------
    path = [(96, 180), (96, 164), (74, 150), (108, 136), (86, 122), (104, 108), (92, 97), (112, 82), (118, 66)]
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x = round(xa + (xb - xa) * i / n); y = round(ya + (yb - ya) * i / n)
            d.rectangle([x - 2, y, x + 2, y], fill=ASH_HI if y % 2 == 0 else ASH_LO)
            d.point((x - 3, y), fill=ASH_DK); d.point((x + 3, y), fill=ASH_DK)
    for i, (x, y) in enumerate(((82, 160), (96, 146), (100, 128), (92, 115), (110, 142), (80, 136))):     # boughs over it
        a, b, c = pal[(i * 2) % 7]
        blob(d, x, y, 5, 4, a, b, c, i + 50)
    # ---- the gate at the foot: red posts under a little roof ------------------------------
    for x0 in (86, 103):
        bar(d, x0, 166, x0 + 3, 184, VERM, VERM_HI, VERM_LO)
    d.rectangle([84, 162, 108, 165], fill=VERM_LO); d.line([(84, 162), (108, 162)], fill=VERM)
    roof(d, 153, 159, (88, 104), (80, 112), SLATE_P, ridge=False, step=3)
    d.rectangle([91, 180, 101, 186], fill=ASH); d.line([(91, 180), (101, 180)], fill=ASH_HI)
    d.line([(91, 183), (101, 183)], fill=ASH_LO)
    # ---- its foot breaks into the ground: bushes and boulders, no straight edge -----------
    for i, x in enumerate(range(6, 190, 9)):
        if 82 < x < 110:
            continue
        a, b, c = pal[(i * 3 + 1) % 7]
        blob(d, x, 182 + (i * 5) % 4, 6 + i % 2, 4, a, b, c, i + 70)
    for x, w in ((30, 9), (66, 7), (120, 8), (164, 10)):
        d.ellipse([x, 181, x + w, 188], fill=ROCK); d.arc([x, 181, x + w, 188], 180, 300, fill=ROCK_HI)
        d.chord([x, 181, x + w, 188], 10, 150, fill=ROCK_LO)
    outline(im)
    return grounded(im, [(0, 178, 191, 191)], a=70)


# ==============================================================================
# Matsushima bay, the land side
# ==============================================================================
HALL, HALL_HI, HALL_LO, HALL_DK = rgb('a08874'), rgb('c4ab92'), rgb('7c6858'), rgb('54463f')
TILE_P = (rgb('8a8684'), rgb('686466'), rgb('b6b0a8'), rgb('474650'))


def small_pine(d, x, y, s=0, lean=1):
    trunk(d, [(x, y), (x + lean * 2, y - 12), (x - lean * 2, y - 22)], 3)
    for cx, cy, rx, ry, k in ((x - lean * 6, y - 16, 8, 4, 1), (x + lean * 5, y - 22, 9, 5, 2), (x - lean * 2, y - 29, 8, 4, 3)):
        blob(d, cx, cy, rx, ry, PINE, PINE_HI, PINE_LO, k + s)
        d.line([(cx - rx + 2, cy + ry - 1), (cx + rx - 2, cy + ry - 1)], fill=PINE_DK)


def godaido():
    im, d = canvas(4, 4)                 # 128 x 128
    # ---- the islet: the bay's own pale banded tuff (generate_sendai_art.rock) ---------
    rock(d, 16, 120, 84, 122, 4)
    d.rectangle([18, 82, 116, 85], fill=PINE_LO)                  # scrub along the top
    for x in range(19, 116, 3):
        d.point((x, 81 + x % 2), fill=PINE)
    d.rectangle([64, 108, 72, 119], fill=ROCK_DK); d.rectangle([65, 105, 71, 108], fill=ROCK_DK)   # a sea cave
    small_pine(d, 26, 84, 1, -1); small_pine(d, 110, 86, 4, 1); small_pine(d, 100, 80, 7, -1)
    # ---- the landing (row 3, west): a cut-stone quay level with the bridge deck, two
    #      tall vermilion newels, steps up the rock to the terrace --------------------------
    ashlar(d, 0, 104, 19, 124, ch=7, bw=10, seed=1)
    d.rectangle([0, 103, 19, 121], fill=ASH_HI)                   # its top, walked on
    for x in range(0, 20, 5):
        d.line([(x, 104), (x, 120)], fill=ASH)
    d.line([(0, 112), (19, 112)], fill=ASH)
    d.rectangle([0, 122, 19, 124], fill=ASH_DK); d.line([(0, 125), (20, 125)], fill=WHITE)
    for y0 in (90, 112):                                          # the newel posts, black caps, a gilt jewel
        bar(d, 1, y0, 4, y0 + 12, VERM, VERM_HI, VERM_LO)
        d.rectangle([0, y0 - 2, 5, y0], fill=LQ); d.point((2, y0 - 3), fill=GOLD_HI); d.point((3, y0 - 3), fill=GOLD)
    d.line([(5, 99), (16, 99)], fill=VERM); d.line([(5, 100), (16, 100)], fill=VERM_LO)       # a rail to the steps
    d.line([(16, 96), (16, 102)], fill=VERM)
    for i in range(7):                                            # the steps up to the terrace
        x0, y0 = 19 + i * 3, 101 - i * 3
        d.rectangle([x0, y0, x0 + 3, y0 + 9], fill=ASH_HI)
        d.line([(x0 + 3, y0), (x0 + 3, y0 + 9)], fill=ASH_LO)
        d.line([(x0, y0 + 10), (x0 + 3, y0 + 10)], fill=ASH_DK)
    # ---- the terrace: a low wall of cut stone under the hall -----------------------------
    ashlar(d, 32, 72, 95, 83, ch=6, bw=12, seed=2)
    d.line([(32, 72), (32, 83)], fill=ASH_HI); d.rectangle([92, 72, 95, 83], fill=ASH_LO)
    # ---- the hall: weathered timber, a railed veranda, a pyramid roof and its jewel -
    d.rectangle([34, 68, 93, 72], fill=ASH); d.line([(34, 68), (93, 68)], fill=ASH_HI)
    d.line([(34, 72), (93, 72)], fill=ASH_DK)
    bar(d, 40, 44, 87, 66, HALL, HALL_HI, HALL_LO)
    d.rectangle([80, 44, 87, 66], fill=HALL_LO)
    for x in (40, 52, 75, 87):
        d.line([(x, 44), (x, 66)], fill=HALL_DK)
    d.rectangle([54, 48, 73, 66], fill=HALL_DK)                   # the lattice doors
    for x in range(56, 73, 3):
        d.line([(x, 49), (x, 65)], fill=HALL_LO)
    for y in range(51, 65, 4):
        d.line([(55, y), (72, y)], fill=HALL_LO)
    d.line([(63, 48), (63, 66)], fill=INK); d.point((62, 58), fill=GOLD); d.point((64, 58), fill=GOLD)
    for x0 in (43, 77):                                           # barred windows
        d.rectangle([x0, 50, x0 + 7, 60], fill=HALL_DK)
        for x in range(x0 + 1, x0 + 7, 2):
            d.line([(x, 51), (x, 59)], fill=HALL_HI)
    d.rectangle([36, 62, 91, 63], fill=HALL_HI); d.rectangle([36, 66, 91, 67], fill=HALL_LO)      # the veranda rail
    for x in range(36, 92, 5):
        d.line([(x, 60), (x, 67)], fill=HALL_DK)
    d.rectangle([40, 41, 87, 43], fill=HALL_DK)                   # brackets under the eave
    for x in range(42, 87, 4):
        d.point((x, 42), fill=PAPER)
    roof(d, 14, 36, (61, 66), (28, 99), TILE_P, ridge=False, p=1.7, step=4)
    for y in range(14, 37):                                       # the hips of the pyramid
        t = ((y - 14) / 22.0) ** 1.7
        for sx, c in ((-1, TILE_P[2]), (1, TILE_P[3])):
            x = 63.5 + sx * (2.5 + t * 16)
            d.point((round(x), y), fill=c)
    d.rectangle([60, 9, 67, 13], fill=BRONZE); d.line([(60, 9), (67, 9)], fill=BRONZE_HI)         # the dew basin
    d.ellipse([61, 2, 66, 9], fill=GOLD); d.point((62, 4), fill=GOLD_HI); d.point((63, 1), fill=GOLD)
    outline(im)
    return im


def red_bridge():
    """The bridge to Godaido, flat and walked on, tiling east-west: vermilion
    rails with black-capped posts, and planks laid with gaps the sea shows
    through."""
    im, d = canvas(2, 1)                 # 64 x 32
    d.rectangle([0, 7, 63, 25], fill=SEA_DK)
    for x in range(0, 64, 8):                                     # the planks, a gap between each pair
        d.rectangle([x, 7, x + 6, 25], fill=PLANK[(x // 8) % 4])
        d.line([(x, 7), (x, 25)], fill=rgb('d2b08c')); d.line([(x + 6, 7), (x + 6, 25)], fill=rgb('8a6850'))
        d.point((x + 3, 9), fill=WOOD_DK); d.point((x + 3, 23), fill=WOOD_DK)
        d.point((x + 7, 12 + x % 5), fill=SEA_HI)
    for y0 in (2, 24):
        d.rectangle([0, y0, 63, y0 + 3], fill=VERM)
        d.line([(0, y0), (63, y0)], fill=VERM_HI); d.line([(0, y0 + 3), (63, y0 + 3)], fill=VERM_LO)
        for x in (6, 22, 38, 54):
            d.rectangle([x, y0 - 2, x + 3, y0 + 5], fill=VERM)
            d.line([(x, y0 - 2), (x, y0 + 5)], fill=VERM_HI); d.line([(x + 3, y0 - 1), (x + 3, y0 + 5)], fill=VERM_LO)
            d.rectangle([x, y0 - 2, x + 3, y0 - 2], fill=LQ)
            d.point((x + 1, y0 - 2), fill=GOLD)
    d.line([(0, 6), (63, 6)], fill=INK); d.line([(0, 30), (63, 30)], fill=INK)
    d.line([(0, 0), (63, 0)], fill=CLEAR)
    return im


def red_bridge_head():
    """The bridge's first cell at the boardwalk: the same planks and rails
    between two stout newel posts (black caps, gilt jewels) on a stone sill."""
    im, d = canvas(1, 1)                 # 32 x 32
    d.rectangle([0, 7, 31, 25], fill=SEA_DK)
    for x in range(0, 32, 8):
        d.rectangle([x, 7, x + 6, 25], fill=PLANK[(x // 8) % 4])
        d.line([(x, 7), (x, 25)], fill=rgb('d2b08c')); d.line([(x + 6, 7), (x + 6, 25)], fill=rgb('8a6850'))
        d.point((x + 3, 9), fill=WOOD_DK); d.point((x + 3, 23), fill=WOOD_DK)
        d.point((x + 7, 12 + x % 5), fill=SEA_HI)
    d.rectangle([0, 6, 3, 26], fill=ASH); d.line([(0, 6), (0, 26)], fill=ASH_HI); d.line([(3, 7), (3, 25)], fill=ASH_DK)
    for y0 in (2, 24):
        d.rectangle([0, y0, 31, y0 + 3], fill=VERM)
        d.line([(0, y0), (31, y0)], fill=VERM_HI); d.line([(0, y0 + 3), (31, y0 + 3)], fill=VERM_LO)
        d.rectangle([22, y0 - 2, 25, y0 + 5], fill=VERM)
        d.line([(22, y0 - 2), (22, y0 + 5)], fill=VERM_HI); d.line([(25, y0 - 1), (25, y0 + 5)], fill=VERM_LO)
        d.rectangle([22, y0 - 2, 25, y0 - 2], fill=LQ); d.point((23, y0 - 2), fill=GOLD)
        d.rectangle([1, y0 - 2, 7, y0 + 6], fill=VERM)            # the newel
        d.line([(1, y0 - 2), (1, y0 + 6)], fill=VERM_HI); d.rectangle([6, y0 - 1, 7, y0 + 6], fill=VERM_LO)
        d.rectangle([0, y0 - 2, 8, y0 - 1], fill=LQ)
        d.rectangle([3, y0, 5, y0 + 2], fill=GOLD); d.point((3, y0), fill=GOLD_HI)
    d.line([(0, 30), (31, 30)], fill=INK)
    d.line([(8, 6), (31, 6)], fill=INK)
    return im


def boat_icon(d, x, y, c=SEA_BLUE):
    d.polygon([(x, y + 5), (x + 15, y + 5), (x + 12, y + 8), (x + 2, y + 8)], fill=c)
    d.rectangle([x + 3, y + 2, x + 10, y + 4], fill=c)
    d.rectangle([x + 5, y, x + 7, y + 1], fill=RED)
    for k in range(3):
        d.point((x + 4 + k * 2, y + 3), fill=WHITE)
    for k in range(0, 16, 4):
        d.line([(x + k, y + 10), (x + k + 1, y + 10)], fill=SEA_HI)


def cruise_booth():
    im, d = canvas(3, 3)                 # 96 x 96
    # the board on the roof
    for x in (22, 70):
        d.rectangle([x, 16, x + 1, 24], fill=STONE_DK)
    bar(d, 8, 2, 87, 18, WHITE, WHITE, STONE)
    d.rectangle([8, 2, 87, 18], outline=SEA_DK)
    text(d, 'CRUISE', 48 - text_w('CRUISE'), 4, SEA_DK, scale=2)
    # a blue hipped roof
    roof(d, 24, 36, (14, 81), (3, 92), (SEA_BLUE, SEA_DK, SEA_HI, rgb('1e3560')), ridge=False, p=1.3, step=4)
    # the kiosk: white boards, a blue wave band, the window, the timetable
    bar(d, 7, 41, 88, 90, rgb('f4f6fa'), WHITE, rgb('c4d0e2'))
    d.rectangle([82, 41, 88, 90], fill=rgb('c4d0e2'))
    for y in range(47, 78, 6):
        d.line([(8, y), (87, y)], fill=rgb('d7dfec'))
    d.rectangle([7, 78, 88, 85], fill=SEA_BLUE)
    for x in range(7, 88):
        yy = 79 + round(1.5 * math.sin(x / 2.6))
        d.point((x, yy), fill=WHITE); d.point((x, yy + 3), fill=SEA_HI)
    d.rectangle([11, 45, 50, 70], fill=SEA_DK)                    # the ticket window (cells 0-1)
    d.rectangle([12, 46, 49, 69], fill=WARM)
    d.line([(12, 46), (49, 46)], fill=WHITE)
    d.rectangle([26, 52, 35, 62], fill=rgb('e8b99a'))             # the clerk in a cap
    d.rectangle([25, 49, 36, 53], fill=SEA_DK); d.rectangle([29, 50, 32, 51], fill=GOLD)
    d.point((28, 57), fill=INK); d.point((33, 57), fill=INK)
    d.rectangle([22, 62, 39, 69], fill=WHITE); d.line([(30, 62), (30, 69)], fill=SEA_BLUE)
    d.rectangle([40, 48, 47, 58], fill=WHITE); d.line([(41, 51), (46, 51)], fill=RED)       # a price card
    d.line([(41, 54), (46, 54)], fill=CREAM_DK)
    d.rectangle([9, 70, 52, 73], fill=WOOD); d.line([(9, 70), (52, 70)], fill=rgb('d2a58c'))   # the sill
    d.line([(9, 73), (52, 73)], fill=WOOD_DK)
    bar(d, 58, 45, 84, 72, PAPER, WHITE, PAPER_LO)                # the timetable, a boat on it
    d.rectangle([58, 45, 84, 72], outline=SEA_DK)
    boat_icon(d, 63, 48)
    for y in (62, 65, 68):
        d.line([(61, y), (70, y)], fill=CREAM_DK); d.line([(74, y), (81, y)], fill=SEA_BLUE)
    d.ellipse([10, 75, 21, 86], fill=RED); d.ellipse([13, 78, 18, 83], fill=rgb('f4f6fa'))    # a life ring
    d.rectangle([15, 75, 16, 77], fill=WHITE); d.rectangle([15, 84, 16, 86], fill=WHITE)
    d.rectangle([10, 80, 12, 81], fill=WHITE); d.rectangle([19, 80, 21, 81], fill=WHITE)
    d.rectangle([5, 90, 90, 93], fill=ASH_LO); d.line([(5, 90), (90, 90)], fill=ASH_HI)
    outline(im)
    return im


SHACK, SHACK_HI, SHACK_LO, SHACK_DK = rgb('8f8378'), rgb('b0a498'), rgb('6c625c'), rgb('4a4442')
TIN, TIN_HI, TIN_LO, RUST = rgb('5f8f8c'), rgb('8ab8b0'), rgb('426a6a'), rgb('a8643c')


def oyster(d, x, y):
    d.rectangle([x, y + 1, x + 5, y + 2], fill=rgb('7c8088')); d.point((x + 1, y), fill=rgb('a9aeb2'))
    d.rectangle([x + 1, y, x + 4, y], fill=rgb('a9aeb2'))
    d.rectangle([x + 2, y + 1, x + 3, y + 1], fill=PAPER)


def oyster_shack():
    im, d = canvas(4, 3)                 # 128 x 96
    # ---- a corrugated tin roof, patched and rusting -----------------------------------
    for y in range(8, 28):
        e = (y - 8) // 3
        for x in range(8 - e, 120 + e):
            k = x % 4
            c = TIN_HI if k == 0 else (TIN_LO if k == 3 else TIN)
            if h3(x // 4, y // 3, 4) < 26:
                c = RUST if k != 3 else rgb('7c4a30')
            if 60 <= x < 84 and y < 18:
                c = rgb('7fa0b4') if k != 3 else rgb('5c7c90')    # a newer sheet
            d.point((x, y), fill=c)
    d.rectangle([1, 28, 126, 29], fill=TIN_LO); d.line([(1, 30), (126, 30)], fill=SHACK_DK)
    bar(d, 96, 0, 103, 10, STONE_LO, STONE, STONE_DK)             # a stovepipe
    d.rectangle([94, 0, 105, 1], fill=STONE_DK)
    # ---- the fascia: the oyster board, a sushi tab, glass floats -----------------------
    d.rectangle([6, 31, 121, 46], fill=SHACK_LO)
    bar(d, 10, 31, 50, 46, PAPER, WHITE, PAPER_LO)
    d.rectangle([10, 31, 50, 46], outline=SHACK_DK)
    kana(d, ['ka', 'ki'], 15, 32, VERM, 2)
    d.rectangle([56, 34, 90, 44], fill=NAVY); d.line([(56, 34), (90, 34)], fill=rgb('3a5fb0'))
    kana(d, ['ya', 'ki'], 66, 36, WHITE)                          # yaki: grilled
    for i, x in enumerate((97, 106, 115)):                        # floats in nets
        d.line([(x + 2, 31), (x + 2, 35)], fill=CREAM_DK)
        c = (rgb('5fb8a8'), COAL, rgb('5fb8a8'))[i]
        d.ellipse([x - 1, 35, x + 5, 41], fill=c); d.point((x, 36), fill=WHITE)
        d.line([(x - 1, 38), (x + 5, 38)], fill=SHACK_DK)
    # ---- the body: grey weathered boards ------------------------------------------------
    for x in range(6, 122):
        for y in range(47, 90):
            k = (x - 6) % 7
            c = SHACK_HI if k == 0 else (SHACK_DK if k == 6 else (SHACK if h3(x // 7, y, 2) > 30 else SHACK_LO))
            d.point((x, y), fill=c)
    d.rectangle([114, 47, 121, 90], fill=SHACK_LO)
    # the open counter (cells 0-2): the cook, the grill, oysters on the coals
    d.rectangle([9, 49, 86, 74], fill=rgb('3a2c2c'))
    d.rectangle([9, 49, 86, 51], fill=WARM)
    for x in (22, 46, 70):                                        # bare bulbs
        d.line([(x, 49), (x, 53)], fill=INK); d.rectangle([x - 1, 54, x + 1, 56], fill=WARM)
    d.rectangle([52, 56, 62, 68], fill=rgb('e8b99a'))             # the cook: a headband, an apron
    d.rectangle([52, 54, 62, 56], fill=WHITE); d.point((55, 61), fill=INK); d.point((59, 61), fill=INK)
    d.rectangle([49, 66, 65, 72], fill=NAVY)
    d.line([(65, 67), (72, 70)], fill=rgb('e8b99a'), width=2)
    coals(d, 12, 70, 44, 73)
    d.line([(12, 69), (44, 69)], fill=STONE_DK)
    for x in (14, 22, 30, 38):
        oyster(d, x, 66)
    for x in (70, 78):                                            # plates of them, opened, at the east end
        d.rectangle([x - 1, 72, x + 6, 72], fill=WHITE)
        oyster(d, x, 69)
    d.rectangle([7, 74, 88, 77], fill=WOOD); d.line([(7, 74), (88, 74)], fill=rgb('d2a58c'))   # the counter
    d.line([(7, 77), (88, 77)], fill=WOOD_DK)
    d.rectangle([12, 79, 40, 89], fill=NAVY)                      # a banner on its front: a white fish
    d.polygon([(18, 84), (24, 81), (32, 84), (24, 87)], fill=WHITE)
    d.polygon([(32, 84), (36, 81), (36, 87)], fill=WHITE); d.point((21, 83), fill=NAVY)
    for x0 in (46, 60, 74):                                       # crates of shells
        bar(d, x0, 81, x0 + 11, 89, rgb('4f8ab8'), rgb('7fb2e6'), rgb('35608a'))
        d.line([(x0, 85), (x0 + 11, 85)], fill=rgb('35608a'))
        for x in range(x0 + 1, x0 + 10, 3):
            d.point((x, 80), fill=rgb('a9aeb2')); d.point((x + 1, 79 + x % 2), fill=PAPER)
    # the door (cell 3): timber, a short blue noren with a wave
    d.rectangle([94, 50, 117, 90], fill=SHACK_DK)
    bar(d, 95, 51, 105, 90, WOOD_LO, WOOD, WOOD_DK); bar(d, 106, 51, 116, 90, WOOD_LO, WOOD, WOOD_DK)
    d.rectangle([97, 60, 103, 72], fill=WARM); d.rectangle([108, 60, 114, 72], fill=WARM)
    d.rectangle([93, 49, 118, 58], fill=SEA_BLUE); d.line([(93, 49), (118, 49)], fill=SEA_HI)
    for x in (101, 110):
        d.line([(x, 49), (x, 59)], fill=SEA_DK)
    for x in range(94, 118):
        d.point((x, 54 + round(1.2 * math.sin(x / 2.0))), fill=WHITE)
    d.rectangle([4, 90, 123, 93], fill=ASH_LO); d.line([(4, 90), (123, 90)], fill=ASH_HI)
    outline(im)
    puff(im, 18, 60, 3, a=90); puff(im, 34, 58, 4, a=80); puff(im, 99, -1, 3, a=120)
    return im


# ==============================================================================
# Sendai's own street lamps (their keys hold `lamp-post`, so DayNight gives them a halo)
# ==============================================================================
def andon_lamp():
    """The samurai quarter's lamp: a slim black-lacquer post with gilt bands
    carrying a square paper lantern under a little copper cap."""
    im, d = canvas(1, 2)                 # 32 x 64
    light, dark, hi, deep = COPPER_P
    d.rectangle([10, 58, 21, 61], fill=ASH); d.line([(10, 58), (21, 58)], fill=ASH_HI)
    d.line([(10, 61), (21, 61)], fill=ASH_DK)
    lq_post(d, 14, 27, 17, 58, bands=False)
    gold_band(d, 14, 30, 17, 2); gold_band(d, 14, 52, 17, 2)
    d.rectangle([8, 25, 23, 26], fill=LQ); d.line([(8, 25), (23, 25)], fill=GOLD)         # the lantern's shelf
    d.rectangle([9, 10, 22, 24], fill=LQ)                         # its frame
    d.rectangle([10, 11, 21, 23], fill=rgb('f8ecc4'))             # lit paper
    d.line([(10, 11), (10, 23)], fill=WHITE); d.line([(21, 11), (21, 23)], fill=rgb('e6cf94'))
    d.rectangle([10, 20, 21, 23], fill=LIT)
    d.line([(15, 11), (15, 23)], fill=LQ); d.line([(16, 11), (16, 23)], fill=LQ_MID)
    d.line([(10, 17), (21, 17)], fill=LQ_MID)
    for y in range(4, 10):                                        # the copper cap
        w = 3 + (y - 4) * 2 - (y - 4) // 3
        d.line([(15 - w, y), (16 + w, y)], fill=dark if y == 9 else light)
        d.point((15 - w, y), fill=hi); d.point((16 + w, y), fill=deep)
    d.rectangle([15, 1, 16, 3], fill=GOLD); d.point((15, 1), fill=GOLD_HI)
    outline(im)
    return grounded(im, [(6, 57, 26, 63)])


def bay_lamp():
    """The bay front's lamp: a tarred timber pile, rope-bound, a ship's copper
    lantern hung from an iron bracket, a glass float at its foot."""
    im, d = canvas(1, 2)                 # 32 x 64
    bar(d, 12, 12, 17, 60, WOOD_LO, WOOD, WOOD_DK)
    d.line([(13, 12), (13, 60)], fill=rgb('75564a'))
    d.rectangle([11, 10, 18, 12], fill=WOOD_DK); d.line([(11, 10), (18, 10)], fill=WOOD_LO)
    for y in (40, 42, 44):                                        # a rope whipping
        d.line([(11, y), (18, y)], fill=PAPER_LO); d.point((11, y), fill=PAPER)
    d.line([(11, 41), (18, 41)], fill=rgb('8a7a66')); d.line([(11, 43), (18, 43)], fill=rgb('8a7a66'))
    d.line([(18, 15), (28, 15)], fill=SOOT); d.line([(18, 16), (28, 16)], fill=SOOT)       # the bracket
    d.line([(18, 23), (24, 17)], fill=SOOT)
    d.line([(26, 17), (26, 19)], fill=SOOT)
    d.rectangle([22, 20, 30, 21], fill=CU_LO); d.line([(22, 20), (30, 20)], fill=CU)       # the lantern
    d.rectangle([23, 22, 29, 31], fill=WARM)
    d.line([(23, 22), (23, 31)], fill=WHITE); d.line([(29, 22), (29, 31)], fill=LIT)
    d.line([(26, 22), (26, 31)], fill=CU_DK); d.line([(23, 26), (29, 26)], fill=CU_DK)
    d.rectangle([22, 32, 30, 33], fill=CU_LO); d.point((26, 34), fill=CU_DK)
    d.ellipse([19, 53, 27, 61], fill=rgb('5fb8a8')); d.arc([19, 53, 27, 61], 160, 290, fill=WHITE)   # a glass float
    d.line([(19, 57), (27, 57)], fill=SHACK_DK); d.line([(23, 53), (23, 61)], fill=SHACK_DK)
    d.rectangle([9, 60, 20, 61], fill=ASH_LO)
    outline(im)
    return grounded(im, [(6, 57, 30, 63)])


# ==============================================================================
# More of Sendai's own fronts: the arcade's shops, an izakaya, a mid-rise
# ==============================================================================
KANA_SA = ['.#...#.', '#######', '.#...#.', '.#...#.', '.....#.', '....#..', '..##...']      # サ, hand-set
SKIN = rgb('f3dcc0')


def kokeshi(d, x, y, body=VERM, s=1):
    """A kokeshi doll: a round head with a black fringe on a plain turned
    body, banded in colour. 6 x 13 at s=1 (x, y its top-left)."""
    w = 6 * s
    d.rectangle([x, y + s, x + w - 1, y + 5 * s - 1], fill=SKIN)
    d.rectangle([x + s, y, x + w - 1 - s, y + s - 1], fill=INK)   # hair
    d.line([(x, y + s), (x + w - 1, y + s)], fill=INK)
    d.rectangle([x + s, y + 3 * s, x + 2 * s - 1, y + 3 * s + s - 1], fill=INK)             # eyes
    d.rectangle([x + w - 2 * s, y + 3 * s, x + w - s - 1, y + 3 * s + s - 1], fill=INK)
    d.rectangle([x + s, y + 5 * s, x + w - 1 - s, y + 13 * s - 1], fill=rgb('f1e0b8'))      # the body
    d.line([(x + w - 1 - s, y + 5 * s), (x + w - 1 - s, y + 13 * s - 1)], fill=rgb('cfb98a'))
    for yy in (6, 11):
        d.rectangle([x + s, y + yy * s, x + w - 1 - s, y + yy * s + s - 1], fill=body)
    d.rectangle([x + 2 * s, y + 8 * s, x + 3 * s - 1, y + 9 * s - 1], fill=body)            # a painted flower
    d.rectangle([x + 3 * s, y + 9 * s, x + 4 * s - 1, y + 10 * s - 1], fill=rgb('3f7a4a'))


def kokeshi_shop():
    im, d = canvas(3, 3)                 # 96 x 96
    bar(d, 5, 12, 90, 90, PAPER, WHITE, PAPER_LO)                 # plaster
    d.rectangle([84, 12, 90, 90], fill=PAPER_LO)
    d.rectangle([3, 7, 92, 12], fill=UMBER); d.line([(3, 7), (92, 7)], fill=rgb('93705a'))
    d.line([(3, 12), (92, 12)], fill=UMBER_LO)
    bar(d, 6, 15, 89, 34, VERM, VERM_HI, VERM_LO)                 # the board
    d.rectangle([6, 15, 89, 34], outline=rgb('7a2a20'))
    text(d, 'KOKESHI', 7, 18, WHITE, scale=2)
    d.rectangle([3, 37, 92, 41], fill=UMBER); d.line([(3, 37), (92, 37)], fill=rgb('93705a'))
    d.line([(3, 41), (92, 41)], fill=UMBER_LO)
    # the window (cells 0-1): two shelves of dolls
    d.rectangle([9, 44, 43, 85], fill=UMBER_LO)
    d.rectangle([10, 45, 42, 84], fill=WARM); d.line([(10, 45), (42, 45)], fill=WHITE)
    for row, y in enumerate((49, 69)):
        d.rectangle([10, y + 13, 42, y + 14], fill=WOOD); d.line([(10, y + 15), (42, y + 15)], fill=WOOD_DK)
        for i in range(4):
            kokeshi(d, 12 + i * 8, y, (VERM, rgb('3f7a4a'), NAVY, rgb('8a4fc0'), VERM)[(i + row * 2) % 5])
    # the shop's great doll standing out front, between window and door
    kokeshi(d, 46, 51, VERM, 2)
    d.rectangle([45, 77, 58, 89], fill=rgb('f1e0b8')); d.line([(57, 77), (57, 89)], fill=rgb('cfb98a'))
    d.rectangle([47, 80, 56, 81], fill=VERM); d.rectangle([47, 85, 56, 86], fill=rgb('3f7a4a'))
    # the door (cell 2): glass under a vermilion noren with a white ring
    d.rectangle([62, 44, 86, 90], fill=UMBER_LO)
    glass_door(d, 63, 54, 85, 90, frame=UMBER_LO)
    d.rectangle([62, 44, 86, 56], fill=VERM); d.line([(62, 44), (86, 44)], fill=VERM_HI)
    for x in (70, 78):
        d.line([(x, 44), (x, 57)], fill=VERM_LO)
    d.ellipse([71, 46, 77, 52], outline=WHITE)
    for x in (5, 59, 87):                                         # timber posts
        bar(d, x, 42, x + 2, 90, UMBER, rgb('93705a'), UMBER_LO)
    d.rectangle([9, 86, 43, 90], fill=PAPER); d.line([(9, 86), (43, 86)], fill=PAPER_LO)
    for x in range(12, 42, 5):
        d.point((x, 88), fill=VERM)
    d.rectangle([3, 90, 92, 94], fill=ASH_LO); d.line([(3, 90), (92, 90)], fill=ASH_HI)
    outline(im)
    return im


INDIGO_S, INDIGO_S_HI, INDIGO_S_LO = rgb('2c3d6a'), rgb('4b6396'), rgb('1e2a4c')
CAKE, CAKE_LO, TOAST = rgb('f3e6c4'), rgb('d9c69a'), rgb('b8792c')


def sasa_cake(d, x, y):
    """A sasa-kamaboko: a bamboo-leaf-shaped fish cake, toasted, on a skewer."""
    d.polygon([(x, y + 2), (x + 3, y), (x + 9, y + 2), (x + 3, y + 4)], fill=CAKE)
    d.line([(x + 2, y + 4), (x + 8, y + 3)], fill=CAKE_LO)
    d.point((x + 3, y + 2), fill=TOAST); d.point((x + 5, y + 1), fill=TOAST); d.point((x + 6, y + 3), fill=TOAST)
    d.line([(x + 9, y + 2), (x + 12, y + 2)], fill=WOOD_LO)


def sasakama_shop():
    im, d = canvas(3, 3)                 # 96 x 96
    for x in range(5, 91):                                        # the upper wall: indigo-stained boards
        for y in range(12, 38):
            k = (x - 5) % 6
            d.point((x, y), fill=INDIGO_S_LO if k == 5 else (INDIGO_S_HI if k == 0 else INDIGO_S))
    d.rectangle([84, 12, 90, 38], fill=INDIGO_S_LO)
    d.rectangle([3, 7, 92, 12], fill=SOOT); d.line([(3, 7), (92, 7)], fill=rgb('55525c'))
    bar(d, 12, 15, 83, 34, PAPER, WHITE, PAPER_LO)                # the board: sa-sa-ka-ma in kana
    d.rectangle([12, 15, 83, 34], outline=INDIGO_S_LO)
    glyph(d, KANA_SA, 17, 18, INDIGO_S, 2); glyph(d, KANA_SA, 33, 18, INDIGO_S, 2)
    kana(d, ['ka'], 49, 18, INDIGO_S, 2); kana(d, ['ma'], 65, 18, INDIGO_S, 2)
    roof(d, 38, 44, (5, 90), (2, 93), TILE_P, ridge=False, step=3, p=1.0)     # a tiled pent over the front
    d.rectangle([5, 48, 90, 90], fill=WOOD_LO)
    # the grill window (cells 0-1): cakes toasting on skewers over charcoal, a cook
    d.rectangle([9, 50, 57, 80], fill=rgb('40282a'))
    d.rectangle([9, 50, 57, 52], fill=WARM)
    d.rectangle([36, 55, 45, 66], fill=rgb('e8b99a'))             # the cook: a white kerchief, an indigo apron
    d.rectangle([35, 53, 46, 56], fill=WHITE); d.point((38, 60), fill=INK); d.point((43, 60), fill=INK)
    d.rectangle([33, 65, 48, 73], fill=INDIGO_S); d.line([(33, 65), (48, 65)], fill=INDIGO_S_HI)
    d.line([(33, 68), (27, 71)], fill=rgb('e8b99a'), width=2)
    coals(d, 11, 75, 55, 79)
    d.line([(11, 74), (55, 74)], fill=STONE_DK)
    for i, x in enumerate((11, 24, 37)):
        sasa_cake(d, x, 68 + i % 2)
    for x in (13, 22):                                            # a stack ready on a tray
        sasa_cake(d, x, 58); sasa_cake(d, x + 1, 61)
    d.rectangle([11, 64, 30, 65], fill=WOOD)
    d.rectangle([7, 80, 59, 83], fill=WOOD); d.line([(7, 80), (59, 80)], fill=rgb('d2a58c'))
    d.line([(7, 83), (59, 83)], fill=WOOD_DK)
    for x in range(8, 58):                                        # a bamboo-leaf frieze under the counter
        d.point((x, 86 + (x // 3) % 2), fill=rgb('3f7a4a') if x % 6 < 4 else rgb('6fae6a'))
    # the door (cell 2): a timber lattice under an indigo noren with a bamboo leaf
    d.rectangle([63, 50, 86, 90], fill=WOOD_DK)
    shoji(d, 64, 60, 74, 89, lit=True, cw=3, chh=6); shoji(d, 75, 60, 85, 89, lit=True, cw=3, chh=6)
    d.rectangle([62, 49, 87, 61], fill=INDIGO_S); d.line([(62, 49), (87, 49)], fill=INDIGO_S_HI)
    for x in (70, 79):
        d.line([(x, 49), (x, 62)], fill=INDIGO_S_LO)
    d.polygon([(71, 55), (74, 52), (78, 55), (74, 58)], fill=rgb('8fd07a'))
    d.line([(72, 55), (77, 55)], fill=rgb('3f7a4a'))
    for x in (5, 60, 88):
        bar(d, x, 48, x + 2, 90, WOOD, rgb('d2a58c'), WOOD_DK)
    d.rectangle([3, 90, 92, 94], fill=ASH_LO); d.line([(3, 90), (92, 90)], fill=ASH_HI)
    outline(im)
    puff(im, 18, 62, 3, a=70); puff(im, 44, 49, 3, a=60)
    return im


def chochin(d, x, y, mark=VERM):
    """A white paper lantern, a red mark on it."""
    d.rectangle([x + 1, y, x + 5, y], fill=INK)
    d.rectangle([x, y + 1, x + 6, y + 9], fill=PAPER)
    d.line([(x, y + 1), (x, y + 9)], fill=WHITE); d.line([(x + 6, y + 1), (x + 6, y + 9)], fill=PAPER_LO)
    for yy in (y + 3, y + 7):
        d.line([(x + 1, yy), (x + 5, yy)], fill=PAPER_LO)
    d.rectangle([x + 2, y + 4, x + 4, y + 6], fill=mark)
    d.rectangle([x + 1, y + 10, x + 5, y + 10], fill=INK)


def izakaya():
    """An alley izakaya, 3x4: weathered boards and lit paper windows upstairs,
    a row of white lanterns under the eave, a long indigo noren, crates."""
    im, d = canvas(3, 4)                 # 96 x 128
    roof(d, 10, 22, (10, 85), (2, 93), TILE_P, ridge=True, caps=False, step=3, p=1.2)
    for x in range(6, 90):                                        # upstairs: grey weathered boards
        for y in range(27, 66):
            k = (x - 6) % 7
            c = SHACK_HI if k == 0 else (SHACK_DK if k == 6 else (SHACK if h3(x // 7, y, 2) > 30 else SHACK_LO))
            d.point((x, y), fill=c)
    d.rectangle([83, 27, 89, 66], fill=SHACK_LO)
    for x0 in (12, 54):                                           # two lit paper windows, a rail before them
        shoji(d, x0, 33, x0 + 28, 54, lit=True, cw=6, chh=6)
        d.rectangle([x0 - 2, 55, x0 + 30, 56], fill=WOOD_LO); d.line([(x0 - 2, 55), (x0 + 30, 55)], fill=WOOD)
        for x in range(x0 - 1, x0 + 30, 4):
            d.line([(x, 57), (x, 61)], fill=WOOD_LO)
        d.line([(x0 - 2, 62), (x0 + 30, 62)], fill=WOOD_DK)
    bar(d, 44, 31, 51, 58, PAPER, WHITE, PAPER_LO)                # an upright board: sa-ke
    d.rectangle([44, 31, 51, 58], outline=SHACK_DK)
    glyph(d, KANA_SA, 45, 34, VERM, 1); kana(d, ['ke'], 45, 46, VERM, 1)
    for y in range(66, 74):                                       # the pent roof over the door
        e = (y - 66) // 2
        for x in range(4 - e, 92 + e):
            d.point((x, y), fill=TILE_P[1] if (y - 66) % 3 == 2 or (x + ((y - 66) // 3) * 3) % 6 == 0 else TILE_P[0])
    d.rectangle([0, 74, 95, 75], fill=TILE_P[3])
    d.rectangle([6, 76, 89, 122], fill=rgb('3a2c2c'))             # the ground floor, open to the street
    for i, x in enumerate(range(8, 86, 10)):                      # the lanterns
        chochin(d, x, 77, VERM if i % 2 == 0 else INDIGO_S)
    d.rectangle([8, 90, 35, 118], fill=WARM)                      # the counter window (cell 0): bottles, a cook
    d.line([(8, 90), (35, 90)], fill=WHITE)
    for i, x in enumerate((10, 15, 20)):
        d.rectangle([x, 96, x + 2, 104], fill=(rgb('3f7a4a'), rgb('7a4a2a'), rgb('2c3d6a'))[i]); d.point((x + 1, 94), fill=WHITE)
        d.rectangle([x + 1, 94, x + 1, 95], fill=PAPER)
    d.rectangle([25, 96, 32, 104], fill=rgb('e8b99a')); d.rectangle([24, 94, 33, 96], fill=INDIGO_S)
    d.point((27, 100), fill=INK); d.point((30, 100), fill=INK)
    d.rectangle([8, 105, 35, 107], fill=WOOD); d.line([(8, 105), (35, 105)], fill=rgb('d2a58c'))
    d.rectangle([8, 108, 35, 118], fill=WOOD_LO)
    for x in range(10, 35, 5):
        d.line([(x, 108), (x, 118)], fill=WOOD_DK)
    d.rectangle([38, 90, 61, 122], fill=WOOD_DK)                  # the door (cell 1): lit lattice, a long noren
    shoji(d, 39, 98, 49, 121, lit=True, cw=3, chh=5); shoji(d, 50, 98, 60, 121, lit=True, cw=3, chh=5)
    d.rectangle([37, 89, 62, 104], fill=INDIGO_S); d.line([(37, 89), (62, 89)], fill=INDIGO_S_HI)
    for x in (45, 54):
        d.line([(x, 89), (x, 105)], fill=INDIGO_S_LO)
    for x in range(38, 62):
        d.point((x, 97 + round(1.5 * math.sin(x / 2.2))), fill=WHITE)
    lantern(d, 65, 90, 10, 17)                                    # the red lantern by the door (cell 2)
    d.rectangle([68, 95, 70, 101], fill=PAPER)
    for i, y in enumerate((106, 114)):                            # beer crates, stacked
        bar(d, 66, y, 85, y + 7, AMBER if i else rgb('d9a82a'), rgb('fde08a'), rgb('b8862a'))
        d.line([(66, y + 4), (85, y + 4)], fill=rgb('b8862a'))
        for x in range(69, 85, 5):
            d.rectangle([x, y + 1, x + 1, y + 2], fill=rgb('7a4a2a'))
    for x in (6, 35, 62, 87):
        bar(d, x, 76, x + 2, 122, SHACK_LO, SHACK, SHACK_DK)
    d.rectangle([4, 122, 91, 126], fill=ASH_LO); d.line([(4, 122), (91, 122)], fill=ASH_HI)
    outline(im)
    return im


MID, MID_HI, MID_LO, MID_DK = rgb('e6e0d2'), rgb('f7f3ea'), rgb('c4bca8'), rgb('9c937e')


def midrise():
    """Sendai's mid-rise: a six-storey store in pale tile, ribbon windows in
    green glass, a rooftop board, a red upright banner down its east pier,
    a zelkova-leaf roundel, a deep green canopy over lit windows and doors."""
    im, d = canvas(4, 6)                 # 128 x 192
    for x0 in (36, 88):                                           # the board on the roof, on its frame
        d.rectangle([x0, 14, x0 + 1, 22], fill=STONE_DK)
    bar(d, 24, 1, 103, 17, rgb('2f5a44'), rgb('4a7a5c'), rgb('1e3f30'))
    d.rectangle([24, 1, 103, 17], outline=rgb('1e3f30'))
    text(d, 'AOBA', 64 - 23, 3, KEY_HI, scale=2)
    for x in (30, 97):
        d.ellipse([x - 3, 6, x + 3, 12], fill=KEY); d.line([(x, 7), (x, 11)], fill=rgb('2f5a44'))
    bar(d, 6, 22, 121, 186, MID, MID_HI, MID_LO)                  # the body
    d.rectangle([114, 22, 121, 186], fill=MID_LO)
    d.rectangle([4, 19, 123, 23], fill=MID_DK); d.line([(4, 19), (123, 19)], fill=MID_LO)
    for x in range(6, 114, 12):                                   # the tile joints
        d.line([(x, 24), (x, 150)], fill=MID_LO)
    for f in range(5):                                            # five floors of ribbon window (cells 0-2)
        y = 28 + f * 24
        d.rectangle([10, y, 91, y + 14], fill=rgb('2a4a44'))
        for i, x in enumerate(range(11, 90, 10)):
            lit = (i * 3 + f * 5) % 7 == 0
            d.rectangle([x, y + 1, x + 8, y + 13], fill=WARM if lit else rgb('4f8a7a'))
            d.line([(x, y + 1), (x + 8, y + 1)], fill=WHITE if lit else rgb('8fc4b0'))
            d.line([(x + 1, y + 3), (x + 1, y + 10)], fill=WHITE if lit else rgb('8fc4b0'))
            if not lit and (i + f) % 3 == 0:
                d.rectangle([x, y + 8, x + 8, y + 13], fill=rgb('e9e4d6'))   # a blind half down
        d.line([(10, y + 15), (91, y + 15)], fill=MID_HI); d.line([(10, y + 16), (91, y + 16)], fill=MID_DK)
    d.rectangle([97, 28, 110, 132], fill=MAP)                     # the upright banner down the east pier
    d.line([(97, 28), (97, 132)], fill=MAP_HI); d.line([(110, 28), (110, 132)], fill=MAP_LO)
    text(d, 'AOBA', 99, 36, WHITE, scale=2, vertical=True)
    d.ellipse([98, 108, 109, 119], fill=KEY); d.ellipse([100, 110, 107, 117], fill=MAP)
    d.line([(103, 110), (103, 117)], fill=KEY_HI); d.line([(101, 113), (106, 113)], fill=KEY_HI)
    d.rectangle([98, 136, 109, 146], fill=rgb('4f8a7a')); d.line([(98, 136), (109, 136)], fill=rgb('8fc4b0'))
    # the canopy and the ground floor
    d.rectangle([2, 150, 125, 157], fill=rgb('2f5a44')); d.line([(2, 150), (125, 150)], fill=rgb('4a7a5c'))
    d.rectangle([2, 156, 125, 157], fill=rgb('1e3f30'))
    for x in range(5, 124, 6):
        d.point((x, 157), fill=KEY_HI)
    d.rectangle([6, 158, 121, 186], fill=GLASS_DK)
    for i, x0 in enumerate((9, 98)):                              # show windows (cells 0 and 3)
        d.rectangle([x0, 161, x0 + 21, 184], fill=WARM); d.line([(x0, 161), (x0 + 21, 161)], fill=WHITE)
        for k, x in enumerate((x0 + 3, x0 + 13)):                 # dressed figures
            c = (MAP, KEY, rgb('3f7a4a'), INDIGO_S)[(k + i * 2) % 4]
            d.rectangle([x + 1, 165, x + 3, 168], fill=rgb('e8b99a'))
            d.rectangle([x, 169, x + 4, 178], fill=c); d.rectangle([x + 1, 179, x + 3, 183], fill=SOOT)
    for x0, c in ((33, RUS), (88, MAP)):                          # autumn sale banners
        d.rectangle([x0, 160, x0 + 6, 182], fill=c); d.line([(x0, 160), (x0, 182)], fill=WHITE)
        for y in (164, 170, 176):
            d.rectangle([x0 + 2, y, x0 + 4, y + 2], fill=WHITE)
    glass_door(d, 42, 162, 62, 186); glass_door(d, 65, 162, 85, 186)          # the doors (cells 1-2)
    d.rectangle([42, 158, 85, 161], fill=AMBER); d.line([(42, 158), (85, 158)], fill=WHITE)
    for x in (6, 30, 40, 86, 96, 119):
        bar(d, x, 158, x + 2, 186, MID, MID_HI, MID_LO)
    d.rectangle([4, 186, 123, 189], fill=STONE_LO); d.line([(4, 186), (123, 186)], fill=STONE)
    outline(im)
    return im


def samurai_store():
    """A thatched outbuilding for a house court, 3x3: black boards, wide plank
    doors with iron straps, firewood stacked under the eave, a straw raincoat."""
    im, d = canvas(3, 3)                 # 96 x 96
    thatch_roof(d, 14, 40, (28, 67), (3, 92))
    d.rectangle([7, 46, 88, 88], fill=LQ_LO)
    lacquer_boards(d, 8, 47, 87, 83, studs=True)
    ashlar(d, 7, 84, 88, 89, ch=6, bw=16)
    d.rectangle([33, 50, 62, 88], fill=LQ)                        # the doors (cell 1)
    for x0 in (34, 48):
        bar(d, x0, 52, x0 + 13, 88, rgb('6b4a3a'), rgb('8a6248'), rgb('4a3229'))
        for x in range(x0 + 3, x0 + 13, 4):
            d.line([(x, 52), (x, 88)], fill=rgb('4a3229'))
        for y in (58, 80):
            d.rectangle([x0, y, x0 + 13, y + 1], fill=SOOT); d.point((x0 + 2, y), fill=GOLD_HI); d.point((x0 + 11, y), fill=GOLD_HI)
    d.rectangle([46, 68, 49, 72], fill=GOLD); d.point((46, 68), fill=GOLD_HI)               # the lock
    d.rectangle([33, 50, 62, 51], fill=LQ_MID); d.line([(33, 50), (62, 50)], fill=GOLD_LO)
    for row in range(3):                                          # firewood, stacked end-on (cell 0)
        for i in range(5 - row % 2):
            cx, cy = 11 + i * 5 + (row % 2) * 2, 85 - row * 5
            d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=WOOD); d.point((cx, cy), fill=WOOD_DK)
            d.arc([cx - 2, cy - 2, cx + 2, cy + 2], 150, 300, fill=rgb('d2a58c'))
    d.line([(8, 88), (32, 88)], fill=WOOD_DK)
    d.polygon([(70, 56), (80, 56), (84, 76), (66, 76)], fill=THATCH)          # a straw raincoat on a peg (cell 2)
    for x in range(67, 84, 2):
        d.line([(x, 62 + (x % 4)), (x, 76 + x % 3)], fill=THATCH_LO)
    d.line([(70, 56), (66, 76)], fill=THATCH_HI); d.rectangle([73, 53, 77, 56], fill=THATCH_LO)
    d.ellipse([68, 49, 82, 54], fill=THATCH_HI); d.line([(68, 52), (82, 52)], fill=THATCH_LO)   # and its hat
    for x in (7, 31, 62, 86):
        lq_post(d, x, 46, x + 2, 88, bands=False)
    step_stone(d, 36, 59, 88)
    d.rectangle([5, 90, 90, 92], fill=ASH_LO); d.line([(5, 90), (90, 90)], fill=ASH)
    outline(im)
    return im


# ==============================================================================
# Ground families (opaque, 9 autotile roles)
# ==============================================================================
def _edge(role, x, y):
    """Distance in from the sides the role names, and the coordinate along the
    nearer one."""
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


PAVERS = (rgb('c9b59b'), rgb('bfa98d'), rgb('d1bfa4'), rgb('c4af94'))


def jozenji_tex(x, y):
    j = y // 4
    u = x + (j % 2) * 4
    if y % 4 == 3 or u % 8 == 7:
        return rgb('a8937a')
    if h3(x, y, 31) < 5 or h3(x - 1, y, 31) < 5:
        return KEY if h3(x, y, 2) % 3 else KEY_HI                 # keyaki leaves, fallen
    if h3(x, y, 47) < 4:
        return RUS
    if h3(x, y, 53) < 2:
        return KEY_LO
    return PAVERS[(u // 8 * 3 + j * 5) % 4]


def jozenji_kerb(m, along):
    if m == 3:
        return rgb('8f8676')
    if along % 16 == 15:
        return rgb('8a8e98')
    return rgb('dde0e5') if m == 0 else rgb('b9bdc4')


def lane_tex(x, y):
    """Plain raked gravel: fine cool-grey grit, the rake's lines running with
    the lane in a slow wave (period 32, so cells join)."""
    k = h3(x, y, 17)
    rake = (y + round(1.5 * math.sin(x * math.pi / 16))) % 4
    if rake == 0:
        return rgb('9499a8') if k > 70 else rgb('a5a9b5')
    if rake == 1:
        return rgb('bfc3cd') if k > 80 else rgb('b0b4bf')
    return rgb('c4c8d1') if k < 26 else (rgb('979baa') if k > 232 else rgb('a9adb9'))


STEPPING = {'a': [[(6, 10), (13, 5), (23, 7), (27, 14), (24, 23), (14, 26), (7, 21)]],
            'b': [[(3, 7), (11, 4), (16, 9), (14, 15), (6, 15)], [(16, 18), (24, 16), (29, 21), (25, 28), (17, 27)]],
            'c': [[(4, 9), (27, 7), (28, 21), (5, 23)]]}


def stepping_stone(variant):
    """Stepping stones to lay ON the gravel (flat, see-through round them):
    -a one broad stone, -b two smaller ones, -c a cut slab."""
    im, d = canvas(1, 1)                 # 32 x 32
    for pts in STEPPING[variant]:
        d.polygon([(x + 1, y + 2) for x, y in pts], fill=rgb('7d8192'))       # its shadow on the gravel
    for pts in STEPPING[variant]:
        d.polygon(pts, fill=rgb('c6c8d0'), outline=rgb('9a9dab'))
    px = im.load()
    for y in range(32):
        for x in range(32):
            if px[x, y] == rgb('c6c8d0'):
                up = px[x, y - 1] if y else CLEAR
                left = px[x - 1, y] if x else CLEAR
                if up == rgb('9a9dab') or left == rgb('9a9dab'):
                    px[x, y] = rgb('e4e6eb')                      # the lit arris
                elif h3(x, y, 6) < 24:
                    px[x, y] = rgb('b6b8c2')
                elif h3(x, y, 9) < 6:
                    px[x, y] = rgb('8fa07c')                      # lichen
    return im


def lane_kerb(m, along):
    if along % 11 == 10:
        return rgb('3f4254')
    return (rgb('8a8ea2'), rgb('63667a'), rgb('4c4f62'))[m]


YARD = (rgb('a8604a'), rgb('98523f'), rgb('b56e55'), rgb('8f4c3c'))


def yard_tex(x, y):
    col = x // 4
    v = y + (col % 2) * 4
    if x % 4 == 3 or v % 8 == 7:
        return rgb('6a7a4a') if h3(x, y, 9) < 16 else rgb('6f4034')          # moss in the joints
    if h3(col * 7 + 3, (v // 8) * 5 + col * 3, 12) < 7:
        return rgb('6f4a44')                                      # a brick blackened by soot
    c = YARD[(col * 3 + (v // 8) * 5) % 4]
    return rgb('c08268') if (x % 4 == 0 and v % 8 == 0) else c


def yard_kerb(m, along):
    if m == 3:
        return ASH_DK
    if along % 16 == 15:
        return ASH_LO
    return ASH_HI if m == 0 else ASH


PLANK = (rgb('b08a68'), rgb('a57f5f'), rgb('ba9572'), rgb('ad8766'))


def board_tex(x, y):
    col = x // 8
    v = y + col * 13
    if x % 8 == 7:
        return rgb('6f5240')
    if v % 32 == 31:
        return rgb('7a5a45')
    if v % 32 in (2, 28) and x % 8 in (1, 5):
        return rgb('5a4636')                                      # nail heads
    if x % 8 == 0:
        return rgb('c6a27e')
    if h3(x, y // 3, 21) < 20:
        return rgb('9c7858')                                      # the grain
    return PLANK[(col * 3 + v // 32) % 4]


def board_kerb(m, along):
    if m == 1 and along % 8 == 4:
        return rgb('3f3230')
    return (rgb('b08c68'), rgb('8a6850'), rgb('5f4636'))[m]


PLAZA = (rgb('ddd2c0'), rgb('d3c7b3'))


def plaza_tex(x, y):
    """The station plaza: big pale stone slabs set in a grid of terracotta
    brick bands (a band down the west and along the north of every cell)."""
    bx, by = x % 32 < 4, y % 32 < 4
    if bx or by:
        if bx and by:
            return rgb('bf9a84')
        along, across = (y, x % 32) if bx else (x, y % 32)
        if across in (0, 3) or along % 8 == 7:
            return rgb('b8ab95') if across in (0, 3) else rgb('b48e78')
        return rgb('cfab95') if (along // 8) % 2 else rgb('c6a18b')
    sx, sy = (x % 32 - 4) % 14, (y % 32 - 4) % 14
    if sx == 13 or sy == 13:
        return rgb('b8ab95')
    if sx == 0 or sy == 0:
        return rgb('ebe2d2')
    return PLAZA[((x % 32 - 4) // 14 + (y % 32 - 4) // 14) % 2] if h3(x, y, 23) > 9 else rgb('c9bca6')


def plaza_kerb(m, along):
    if along % 16 == 15:
        return rgb('8a8e98')
    return (rgb('eef0f3'), rgb('c9ccd3'), rgb('a2a6b0'))[m]


def arcade_tex(x, y):
    """The arcade's floor: polished cream tiles with a russet diamond at every
    second crossing and a long reflection of the roof's light."""
    tx, ty = x % 8, y % 8
    dx, dy = min(x % 16, 16 - x % 16), min(y % 16, 16 - y % 16)
    if dx + dy <= 2:
        return rgb('b9714e') if dx + dy < 2 else rgb('d39a74')
    if tx == 0 or ty == 0:
        return rgb('cfc4b0')
    if tx == 1 and ty > 1:
        return rgb('fbf7ec')
    if (x % 32) in (12, 13) and h3(x, y, 3) > 40:
        return rgb('fbf7ec')                                      # the skylight, mirrored in the polish
    return rgb('efe7d6') if (x // 8 + y // 8) % 2 else rgb('e6dcc8')


def arcade_kerb(m, along):
    if along % 8 == 7:
        return rgb('6f4034')
    return (rgb('b9714e'), rgb('a05c40'), rgb('834a36'))[m]


def ground(fam):
    tex, kerb, kw = {'sendai-jozenji-autotile': (jozenji_tex, jozenji_kerb, 4),
                     'sendai-samurai-lane-autotile': (lane_tex, lane_kerb, 3),
                     'sendai-brick-yard-autotile': (yard_tex, yard_kerb, 4),
                     'sendai-boardwalk-autotile': (board_tex, board_kerb, 3),
                     'sendai-plaza-autotile': (plaza_tex, plaza_kerb, 3),
                     'sendai-arcade-floor-autotile': (arcade_tex, arcade_kerb, 3)}[fam]
    return lambda role: family(role, tex, kerb, kw)


# ==============================================================================
def rows(w, r0, r1):
    return [[c, r] for r in range(r0, r1 + 1) for c in range(w)]


FENCE = 'sendai-board-fence'
DECK = 'sendai-deck'
ST, DT, SQ, NK, MB = 'Station front', 'Downtown / Jozenji-dori', 'Samurai quarter', 'Distillery yard', 'Matsushima bay'
AR = 'Downtown (the arcade)'
PINK_HEX, BLUE_HEX, LEAF_HEX, GILT_HEX, COOL_HEX = '#ff8fc0', '#8fc4ff', '#9fe6a0', '#f0d98c', '#bfd4ff'

# key, builder, size in cells, district, what the map needs to know, description
#   door: the cell(s) an interior can open ([col,row] from the top-left cell)
#   solid: the cells it stands on; walk: cells you walk THROUGH or UNDER (gates, the deck)
#   lit: its lit parts, [col, row, colour(, radius in cells(, strength))] from the
#        top-left (fractions allowed): the glow spots src/utils/Glows.js would draw at night
#   layer: 'standing' = Y-sorted art on a Collidables-type layer, 'ground' = a floor
#          tile, 'flat' = lies on the ground and is walked ON (Non-Collidables +
#          a negative depthBias, as matsushima-pier is)
PIECES = [
    ('sendai-station-front_0_0', station_front, (9, 5), ST, dict(
        door=[[3, 4], [4, 4], [5, 4]], solid=rows(9, 2, 4),
        lit=[[0.7, 4.2, WARM_HEX, 0.8], [1.65, 4.2, WARM_HEX, 0.8], [2.6, 4.2, WARM_HEX, 0.8], [6.5, 4.2, WARM_HEX, 0.8],
             [7.45, 4.2, WARM_HEX, 0.8], [8.4, 4.2, WARM_HEX, 0.8], [4.5, 3.7, '#f9c22e', 1.3, 0.6],
             [4.5, 2.15, '#fff0c0', 2.0, 0.9], [3.6, 2.2, '#7fa6ff', 1.0, 0.5], [5.4, 2.2, '#ffb040', 1.0, 0.5]]),
     "Sendai Station's long front: three storeys of cream tile under a brown parapet, tall arched windows "
     'down both wings, a raised centre with SENDAI on a navy board, and under it the stained-glass window '
     '(the meeting spot): a sun in its ring over blue sky, green hills and a river, in a few big fields of '
     'colour with heavy leading; at night it is the brightest thing on the building. The pedestrian deck '
     "meets it at first-floor height (the deck pieces' own glass rail and slab right across), with lit shops "
     'and three pairs of glass doors between the deck columns below. Doors are the three middle cells.'),
    (f'{DECK}-span_0_0', deck_span, (3, 3), ST, dict(
        solid=[[1, 2]], walk=[[0, 2], [2, 2]], lit=[[0.45, 1.6, WARM_HEX, 0.7], [2.55, 1.6, WARM_HEX, 0.7]]),
     'A length of the elevated pedestrian deck, running east-west: the far rail, paving with a tactile '
     'strip seen from above, the near glass rail and the slab edge - drawn at the height of the station '
     "front's own rail and slab, so a run stood on the station's base row joins the building - and under "
     'it the dark: a soffit with lights, a pier of two concrete columns in the middle cell, the deck\'s '
     'shadow on the ground. Tiles left-right; you walk UNDER it in the two outer cells of its bottom row '
     '(the middle one is the pier). The deck itself is scenery: nothing in the game climbs it.'),
    (f'{DECK}-span-v_0_0', deck_span_v, (1, 3), ST, dict(walk=[[0, 2]]),
     'The deck running north-south (a spur from the east-west run, or a footbridge over the road): paving '
     'between its two rails seen from above, the slab edge and shadow under its south end. Stack it down '
     'the map from the row below an east-west span; each piece covers the end of the one north of it. No '
     'columns: you (and the traffic) pass under it. Finish the run with sendai-deck-end-s.'),
    (f'{DECK}-end-e_0_0', lambda: deck_end(True), (1, 3), ST, dict(solid=[[0, 2]]),
     'The east end of an east-west deck run: the rail returns across the end over a last pier.'),
    (f'{DECK}-end-w_0_0', lambda: deck_end(False), (1, 3), ST, dict(solid=[[0, 2]]),
     'The west end of an east-west deck run.'),
    (f'{DECK}-end-s_0_0', deck_end_s, (1, 3), ST, dict(solid=[[0, 2]]),
     'The south end of a north-south deck run: the rail across it, a pier under it.'),
    (f'{DECK}-stair-e_0_0', lambda: deck_stair(True), (3, 3), ST, dict(solid=rows(3, 2, 2)),
     'The stair from the deck down to the street, seen from its side and falling away EAST: a landing '
     'level with the deck over a pier (west cell, joins a span to its west), thirteen treads with yellow '
     'nosings between two glass balustrades on sloping stringers, a prop under the flight, newel posts '
     'and a tactile mat at the foot. Stands on the same base row as the spans. Scenery: solid, not climbed.'),
    (f'{DECK}-stair-w_0_0', lambda: deck_stair(False), (3, 3), ST, dict(solid=rows(3, 2, 2)),
     'The same stair falling away WEST (its landing is the east cell, joining a span to its east).'),
    ('sendai-tanabata-a_0_0', lambda: tanabata('a'), (1, 3), 'any (Station front, the arcade)', dict(
        solid=[[0, 2]], lit=[[0.56, 0.5, PINK_HEX, 0.7, 0.4]]),
     "The city's signature street prop: a bamboo pole bent over by one great tanabata kusudama (a pink paper "
     'flower ball) and its long fall of pink, gold, white and red paper streamers. The festival is in '
     'August: in late October keep these to the station and the arcade, where they hang all year.'),
    ('sendai-tanabata-b_0_0', lambda: tanabata('b'), (3, 3), 'any (Station front, the arcade)', dict(
        solid=[[1, 2]], lit=[[0.69, 0.62, BLUE_HEX, 0.7, 0.4], [2.31, 0.66, LEAF_HEX, 0.7, 0.4]]),
     'A pair of kusudama (blue and green) on a bamboo cross pole, paper wish strips tied to it. Three cells '
     'wide; the pole stands in the middle one and the streamers hang over the cells either side.'),
    ('sendai-zelkova-a_0_0', lambda: zelkova('a'), (3, 4), DT, dict(
        solid=[[1, 3]]),
     "Jozenji-dori's keyaki (zelkova) in autumn gold: a smooth grey trunk forking low into a vase of rising "
     'limbs, a broad dome of gold and russet, fallen leaves in its shadow. The avenue tree: plant in rows '
     'on the median walk.'),
    ('sendai-zelkova-b_0_0', lambda: zelkova('b'), (3, 4), DT, dict(
        solid=[[1, 3]]),
     'A narrower keyaki turned russet, to alternate with -a. Also three cells wide, the trunk in the middle one.'),
    ('sendai-jozenji-statue_0_0', jozenji_statue, (2, 3), DT, dict(
        solid=rows(2, 2, 2)),
     "A bronze for the avenue's median (the street is lined with them): a dancer in dark bronze on a granite "
     'block, striding, the left arm flung up and a bird on the outstretched right hand. Invented, not a '
     'copy of a real work.'),
    ('sendai-gyutan_0_0', gyutan, (4, 4), DT, dict(
        door=[[2, 3]], solid=rows(4, 2, 3),
        lit=[[1.1, 3.45, COAL_HEX, 1.0, 0.6], [2.45, 3.3, WARM_HEX, 0.7], [3.2, 2.95, RED_HEX, 0.6, 0.6],
             [1.6, 1.45, GILT_HEX, 1.0, 0.3]]),
     'A gyutan (charcoal-grilled beef tongue) restaurant: charred-cedar boards, a black board lettered in '
     'gold with the character for beef and "tan" in kana, a vermilion tab, a black-tiled pent roof with '
     'gilt eave tiles, a steel flue with smoke; below, the grill window (a cook in whites, slices on the '
     'mesh, glowing charcoal), lamplit lattice doors under a dark red noren, a red lantern, the menu.'),
    ('sendai-zunda_0_0', zunda, (3, 3), DT, dict(
        door=[[2, 2]], solid=rows(3, 1, 2), lit=[[1.0, 2.1, WARM_HEX, 1.0]]),
     'A zunda (sweet edamame paste) shop in soft sage green: a ZUNDA board with pods, a green and white '
     'scalloped awning, a lit window with a clerk, zunda shakes and plates of zunda mochi, a glass door '
     'under a short green noren.'),
    ('sendai-izakaya_0_0', izakaya, (3, 4), DT, dict(
        door=[[1, 3]], solid=rows(3, 2, 3),
        lit=[[0.8, 1.35, WARM_HEX, 0.9], [2.1, 1.35, WARM_HEX, 0.9], [1.5, 2.6, '#ffd9a0', 1.5, 0.45],
             [0.7, 3.2, WARM_HEX, 0.8], [2.2, 3.05, RED_HEX, 0.6, 0.6]]),
     'An alley izakaya: grey weathered boards and two lit paper windows upstairs behind a rail, an upright '
     'board reading sa-ke in kana, a tiled pent, a row of white paper lanterns with red and indigo marks, '
     'a counter window with bottles and a cook, lamplit lattice doors under a long indigo noren with a '
     'white wave (middle cell), a red lantern and yellow beer crates.'),
    ('sendai-midrise_0_0', midrise, (4, 6), DT, dict(
        door=[[1, 5], [2, 5]], solid=rows(4, 4, 5),
        lit=[[2.0, 0.3, '#ffd24a', 1.4, 0.5], [0.6, 5.4, WARM_HEX, 0.9], [3.4, 5.4, WARM_HEX, 0.9],
             [2.0, 5.0, '#f9c22e', 1.2, 0.5], [3.25, 2.5, '#ff6a5a', 1.0, 0.3]]),
     "Sendai's mid-rise, to stand where the shared high-rises do: a six-storey store in pale tile, five "
     'floors of green-glass ribbon window (some lit, some with blinds), a green rooftop board lettered '
     'AOBA in gold (the ward\'s name, not a brand), a red upright AOBA banner with a keyaki-leaf roundel '
     'down the east pier, a deep green canopy, lit show windows with dressed figures, autumn banners and '
     'two pairs of glass doors (the two middle cells).'),
    ('sendai-arcade-gate_0_0', arcade_gate, (4, 5), AR, dict(
        solid=[[0, 4], [3, 4]], walk=[[1, 4], [2, 4]],
        lit=[[2.0, 1.85, '#ffd24a', 1.6, 0.7], [2.0, 2.75, PINK_HEX, 0.7, 0.4], [2.0, 0.8, COOL_HEX, 1.4, 0.35]]),
     "The mouth of the covered shopping street: a tall RECTANGULAR portal - two clad pylons with gold "
     'bands and poster cases carrying the glazed gable end of a pitched glass roof - with an indigo board '
     "lettered KEYAKI in gold (an invented name) right across, autumn banners and one kusudama in the head "
     "of the opening. Not Sapporo's arch. Walk through the two middle cells."),
    ('sendai-arcade-roof_0_0', arcade_roof, (4, 4), AR, dict(
        solid=[[0, 3], [3, 3]], walk=[[1, 3], [2, 3]],
        lit=[[1.0, 2.5, WARM_HEX, 1.0, 0.35], [3.0, 2.5, WARM_HEX, 1.0, 0.35]]),
     "A length of the arcade's pitched glass roof on a short white post each side: the two falls seen "
     'from above (the west one lit), a ridge and rafters in white steel, lamps under it. The panes are '
     'nearly CLEAR (alpha 70 west, 95 east), so the floor and the player show under them. It is drawn two '
     "cells above the ground (the deck's height; lower than the gate, whose portal you see it through) "
     'and roofs its own row and the row south of it: stand one on the row behind the gate and then on '
     'every second row north, and they make one continuous roof up the map.'),
    ('sendai-kokeshi-shop_0_0', kokeshi_shop, (3, 3), AR, dict(
        door=[[2, 2]], solid=rows(3, 1, 2), lit=[[0.8, 2.0, WARM_HEX, 1.0], [1.5, 0.75, '#ff8a6a', 1.2, 0.3]]),
     'A kokeshi doll shop for the arcade: white plaster and dark timber, a vermilion board lettered '
     'KOKESHI, a lit window with two shelves of dolls, a doll as tall as the door standing out front, and '
     'a glass door under a vermilion noren with a white ring.'),
    ('sendai-sasakama-shop_0_0', sasakama_shop, (3, 3), AR, dict(
        door=[[2, 2]], solid=rows(3, 1, 2), lit=[[1.0, 2.4, COAL_HEX, 0.9, 0.55], [2.35, 2.3, WARM_HEX, 0.7]]),
     'A sasa-kamaboko (bamboo-leaf fish cake) shop for the arcade: indigo-stained boards, a cream board '
     'reading sa-sa-ka-ma in kana, a tiled pent, a grill window where a cook toasts the leaf-shaped cakes '
     'on skewers over charcoal, a bamboo-leaf frieze, lit lattice doors under an indigo noren with a leaf.'),
    ('sendai-samurai-gate_0_0', samurai_gate, (4, 3), SQ, dict(
        solid=[[0, 2], [3, 2]], walk=[[1, 2], [2, 2]]),
     "A samurai residence's gate in the Date colours: a verdigris copper roof with gilt ridge ends, a "
     'black-lacquer lintel with gilt nail covers, gilt-banded lacquer posts, studded leaves folded back, '
     'short boarded wing walls on cut stone. On the lintel the quarter\'s INVENTED mon: a crescent in a '
     'gold ring (not a real crest). Walk through the two middle cells; the board fence joins either end.'),
    (f'{FENCE}_0_0', lambda: fence('h'), (1, 2), SQ, dict(solid=[[0, 1]]),
     "The quarter's fence, east-west: black shitami-ita (lapped boards under thin battens, gilt nails), a "
     'board cap with a copper ridge, on two courses of cut grey stone. Tiles left-right. To replace '
     'sendai-earthen-wall in the samurai quarter.'),
    (f'{FENCE}-corner-e_0_0', lambda: fence('corner-e'), (1, 3), SQ, dict(solid=[[0, 2]]),
     'The east end of an east-west run where the fence turns north (1x3): the face stops at a gilt-banded '
     f'corner post and the copper cap turns up the map over a mitre. {FENCE}-v goes in the cells above it.'),
    (f'{FENCE}-corner-w_0_0', lambda: fence('corner-w'), (1, 3), SQ, dict(solid=[[0, 2]]),
     'The west end where the fence turns north (1x3).'),
    (f'{FENCE}-v_0_0', lambda: fence('v'), (1, 3), SQ, dict(solid=[[0, 2]]),
     'The fence running north-south, seen end-on (1x3): all that shows is its cap from above - a narrow '
     'copper strip between two board edges with a seam every 8px - a cell and a half up the map from the '
     'cell it stands on, because the fence is as tall as the east-west run. Its bottom cell is the solid '
     'one. Stack down the map; finish with -end.'),
    (f'{FENCE}-end_0_0', lambda: fence('end'), (1, 3), SQ, dict(solid=[[0, 2]]),
     'The south end of a north-south run (1x3): the cap strip, then the fence end-on at the east-west '
     "run's own heights - copper cap, board cap, a gilt-banded lacquer post, the cut-stone footing."),
    (f'{FENCE}-wicket_0_0', lambda: fence('wicket'), (1, 2), SQ, dict(walk=[[0, 1]]),
     'A side gate in the fence: lacquer posts, a little copper roof, the mon on its lintel, the leaf '
     'folded back. One cell, walked through.'),
    ('sendai-samurai-house-a_0_0', lambda: samurai_house('a'), (5, 4), SQ, dict(
        door=[[2, 3]], solid=rows(5, 2, 3), lit=[[0.6, 2.9, WARM_HEX, 0.9], [2.25, 2.75, WARM_HEX, 0.5]]),
     'A samurai house under a great thatched hip roof (bark ridge, straddling poles, a thick trimmed '
     'eave): an engawa with paper screens, one lit and one slid back on an alcove with a scroll; the way '
     'in under the mon - one lattice leaf slid back on the dark entry, a lamp inside, a pale shoe stone '
     'before it; a black-boarded bay with a gilt-framed barred window and a rain tub. Door is the middle cell.'),
    ('sendai-samurai-house-b_0_0', lambda: samurai_house('b'), (4, 4), SQ, dict(
        door=[[1, 3]], solid=rows(4, 2, 3), lit=[[1.35, 2.85, WARM_HEX, 0.5], [2.75, 3.0, WARM_HEX, 0.9]]),
     'A smaller thatched house with a weathered shingle pent roof over its front: a black-boarded bay '
     'with a round paper window in a gilt rim, the dark half-open door on its shoe stone (second cell), '
     'an engawa of paper screens.'),
    ('sendai-samurai-store_0_0', samurai_store, (3, 3), SQ, dict(
        door=[[1, 2]], solid=rows(3, 1, 2)),
     "A thatched outbuilding for a house court (the quarter's third building): black boards on cut stone, "
     'wide plank doors with iron straps and a gilt lock (middle cell), firewood stacked end-on under the '
     'eave, a straw raincoat and hat on a peg.'),
    ('sendai-well_0_0', well, (1, 2), SQ, dict(solid=[[0, 1]]),
     'A well for a house court: a square curb of cut stone, lacquer posts, a little copper roof, a pulley, '
     'rope and bucket.'),
    ('sendai-propped-pine_0_0', propped_pine, (3, 3), SQ, dict(solid=[[0, 2], [2, 2]], walk=[[1, 2]]),
     'An old garden pine leaning east, one long limb run out level and carried on two timber props with '
     'straw padding (not yukitsuri ropes: that is Kanazawa). The trunk stands in the west cell and both '
     'props in the east one; you walk under the limb in the middle.'),
    ('sendai-kabuto-stand_0_0', kabuto_stand, (2, 3), SQ, dict(
        solid=rows(2, 2, 2), lit=[[1.0, 1.6, GILT_HEX, 1.1, 0.4]]),
     "The quarter's hero prop: a suit of black armour laced in gold on its chest, on a lacquer dais before "
     'a gold-leaf folding screen - a dark iron half-mask under the helmet and over it the great thin gold '
     'crescent moon. An invented display; the crescent is the silhouette, no crest is copied.'),
    ('sendai-andon-lamp-post_0_0', andon_lamp, (1, 2), SQ, dict(solid=[[0, 1]]),
     "The samurai quarter's street lamp: a slim black-lacquer post with gilt bands carrying a square lit "
     'paper lantern under a little copper cap. Its key holds `lamp-post`, so DayNight gives it the lamp halo.'),
    ('sendai-stepping-stone-a_0_0', lambda: stepping_stone('a'), (1, 1), SQ, dict(layer='flat', walk=[[0, 0]]),
     'A stepping stone to lay ON the raked gravel of the lane or a court (flat, see-through round it): one '
     'broad irregular stone. Lay a few along a path; leave most of the gravel bare.'),
    ('sendai-stepping-stone-b_0_0', lambda: stepping_stone('b'), (1, 1), SQ, dict(layer='flat', walk=[[0, 0]]),
     'Two smaller stepping stones, set askew.'),
    ('sendai-stepping-stone-c_0_0', lambda: stepping_stone('c'), (1, 1), SQ, dict(layer='flat', walk=[[0, 0]]),
     'A long cut slab, for a threshold or a gate.'),
    ('sendai-distillery-warehouse_0_0', distillery_warehouse, (6, 4), NK, dict(
        door=[[4, 3]], solid=rows(6, 2, 3),
        lit=[[3.0, 2.9, CU_HEX, 1.1, 0.55], [1.5, 2.45, WARM_HEX, 0.7], [4.5, 2.3, WARM_HEX, 0.6, 0.6]]),
     'The distillery\'s still house: red brick under slate, a centre gable with a cask roundel, arched '
     'windows with green iron shutters, a DISTILLERY board over a great stone-arched WINDOW (an iron rail '
     'and a stone sill across it) through which the copper pot still shows - pot, tall neck, lyne arm, a '
     'fire under it. The DOOR is its own: green panelled double doors under a lit fanlight and a lamp, on '
     'a pale step, in the fifth cell. Ivy gone red up the east corner, two casks by the west window. No '
     'brand name or mark.'),
    ('sendai-cask-rack_0_0', cask_rack, (3, 2), NK, dict(solid=rows(3, 1, 1)),
     'Five whisky casks stacked end-on (three and two) on a timber rail with chocks, stencilled heads. '
     'Bigger than sendai-barrels; for the yard.'),
    ('sendai-red-maple_0_0', red_maple, (3, 4), NK, dict(solid=[[1, 3]]),
     'A big spreading maple in deep red with orange lights, red leaves fallen under it. (sendai-maple is '
     'the small 2x3 orange one.)'),
    ('sendai-yamadera_0_0', yamadera, (6, 6), NK + ' (the hill behind: a backdrop for the north edge)', dict(
        solid=rows(6, 1, 5)),
     'Yamadera as a sealed landmark and BACKDROP: a wooded mountain in autumn colour (a canopy of small '
     'maple, keyaki and russet pads with cedars standing through it), two pale crags above the trees, the '
     'red hall on the higher one and the timber lookout stage on stilts on the other, the stone stair '
     'zig-zagging up through the wood from a red gate at the foot. Its foot is bushes and boulders, not a '
     'straight edge. Stand it on the north edge of the room: every row but the top is solid.'),
    ('sendai-godaido_0_0', godaido, (4, 4), MB, dict(solid=rows(4, 2, 3)),
     "Godaido hall on its islet: the bay's own pale banded tuff (as matsushima-islet), scrub, pines and a "
     'sea cave; a weathered timber hall with a railed veranda under a grey pyramid roof and a gilt jewel, '
     'on a low cut-stone terrace. Stands in the WATER. At the west edge of its bottom row a cut-stone quay '
     'level with the bridge deck, two tall vermilion newel posts with black caps, and stone steps up the '
     'rock to the terrace: sendai-red-bridge arrives there. Scenery: the islet is solid.'),
    ('sendai-red-bridge_0_0', red_bridge, (2, 1), MB, dict(layer='flat', walk=[[0, 0], [1, 0]]),
     "Godaido's vermilion bridge, flat and walked on, tiling east-west over water: black-capped posts, "
     'planks with gaps the sea shows through.'),
    ('sendai-red-bridge-head_0_0', red_bridge_head, (1, 1), MB, dict(layer='flat', walk=[[0, 0]]),
     "The bridge's first cell, at the boardwalk (its west end): the same planks and rails between two "
     'stout newel posts with black caps and gilt jewels, on a stone sill.'),
    ('sendai-cruise-booth_0_0', cruise_booth, (3, 3), MB, dict(
        solid=rows(3, 1, 2), lit=[[1.0, 1.8, WARM_HEX, 1.0], [1.5, 0.3, COOL_HEX, 1.2, 0.3]]),
     'The bay cruise ticket booth: white boards with a blue wave band, a blue hipped roof and a CRUISE '
     'board, a lit window with a clerk in a cap, a timetable with a boat on it, a life ring. A booth: '
     'talk at the window from the south, no door.'),
    ('sendai-oyster-shack_0_0', oyster_shack, (4, 3), MB, dict(
        door=[[3, 2]], solid=rows(4, 1, 2),
        lit=[[1.5, 1.9, WARM_HEX, 1.2], [0.9, 2.25, COAL_HEX, 0.8, 0.6], [3.3, 2.0, WARM_HEX, 0.5]]),
     'A grilled-oyster shack: grey weathered boards under a patched tin roof, a board reading kaki '
     '(oyster) in kana and a tab reading yaki (grilled), glass floats; an open counter with bare bulbs, a '
     'cook, oysters steaming over charcoal and plates of opened ones; crates of shells; a door under a '
     'blue noren (east cell).'),
    ('sendai-bay-lamp-post_0_0', bay_lamp, (1, 2), MB, dict(solid=[[0, 1]]),
     "The bay front's lamp: a tarred timber pile with a rope whipping, a ship's copper lantern hung from "
     'an iron bracket, a glass float at its foot. Its key holds `lamp-post`, so DayNight gives it the lamp halo.'),
]
FAMILIES = [
    ('sendai-plaza-autotile', ST,
     "The station plaza's paving, so the station front is not the downtown's grey pavement: big pale "
     'stone slabs set in a grid of terracotta brick bands, a pale granite kerb.'),
    ('sendai-jozenji-autotile', DT,
     "Jozenji-dori's median walk: warm stone pavers in running bond scattered with fallen keyaki leaves, "
     'a pale granite kerb. Lay it two or three cells wide down the middle of the avenue.'),
    ('sendai-arcade-floor-autotile', AR,
     "The covered street's floor: polished cream tiles with a russet diamond at every second crossing and "
     'the skylight mirrored down the middle of each cell, a russet border. Lay it under the arcade roof.'),
    ('sendai-samurai-lane-autotile', SQ,
     'The samurai quarter\'s lane: plain cool blue-grey gravel, raked in slow waves, with dark kerb stones '
     'along the edges; no stones in it (lay sendai-stepping-stone-a/-b/-c on it where a path wants them). '
     'In place of dirt-outside-autotile there.'),
    ('sendai-brick-yard-autotile', NK,
     "The distillery yard: worn dark-red brick laid lengthwise north-south (not Sapporo's basket weave), "
     'a few sooty bricks, moss in the joints, a solid kerb of grey stone.'),
    ('sendai-boardwalk-autotile', MB,
     "The bay front's timber boardwalk: long planks running north-south with staggered butt joints and "
     'nail heads, a bolted edge beam. In place of the concrete promenade.'),
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


def glow_spots(m):
    """A piece's lit parts as the spots src/utils/Glows.js reads; `color` is a
    number, as it is in config.json (0xRRGGBB written in decimal)."""
    out = []
    for x, y, c, *rest in m.get('lit', []):
        out.append({'x': x, 'y': y, 'r': rest[0] if rest else 0.9, 'color': int(c[1:], 16),
                    'a': rest[1] if len(rest) > 1 else 0.5})
    return out


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
        'tool': 'gamev2/tools/generate_sendai_town_art.py',
        'run': 'cd gamev2 && python3 tools/generate_sendai_town_art.py [--sheet out.png] [--scenes dir] [--manifest out.json]'
               '   (a python3 with Pillow; imports generate_hokkaido, generate_sendai_art, generate_sapporo_art, '
               'generate_kanazawa_art from tools/)',
        'notes': [
            "Files are in gamev2/assets/sprites/<key>.png. A cell is 64x64px in the file (art is drawn at 32px per "
            "cell and pixel-doubled, as generate_sapporo_art.py does); 'size' is in cells.",
            'Nothing is registered: config.json, tilePalette, spriteMetadata, tileNames, prefabs, generators, '
            'check_generators.py and docs are untouched, and the tool does not write config.json. To register a '
            'multi-cell sprite follow generate_sapporo_art.register: spriteMetadata {frameCount:1, anchorX: '
            "32/widthPx, anchorY: 32/heightPx} (centre of the top-left cell; that is 'anchor'); 1x1 tiles use "
            '0.5/0.5. The map change should also add the tool to check_generators.py.',
            "'doors' (every door cell; 'door' is the first), 'solid' and 'walk_through' are [col,row] from the "
            "sprite's top-left cell. 'solid' is the suggested footprint (rows above it are roof or sky the player "
            "walks behind). 'walk_through' lists cells of the sprite's own rows that stay walkable: the cells you "
            'walk through under a gate, UNDER the deck (beside its pier) or under the propped pine\'s limb, and '
            "the cells of a 'flat' piece. layer 'flat' (the bridge pieces, the stepping stones) lies on the ground "
            'and is walked ON, as matsushima-pier_0_0 is (Non-Collidables with a negative depthBias).',
            "Night: 'night_halo' is true for the two keys that match DayNight's /lamp-post|-lanterns/ rule "
            '(sendai-andon-lamp-post for the samurai quarter, sendai-bay-lamp-post for the bay front): they get '
            "the lamp halo with no further data. 'glow' is each other sprite's lit parts as glow spots in the "
            "shape src/utils/Glows.js reads ({x, y, r, color, a}: centre in cells from the sprite's top-left, "
            "radius in cells; 'color' is a NUMBER, 0xRRGGBB in decimal): copy the list into the sprite's "
            'spriteMetadata `glow` when it is registered. Radii and strengths differ by what is lit: the station\'s '
            'stained glass is the strongest (r 2.0, a 0.9), then the arcade board, shop windows, coals, lanterns, '
            'and faint colour on the kusudama and the gold screen. All of it was checked only in the Pillow night '
            'previews (previews.night), NOT in the running game.',
            'Season: late October (the posts are 27-30 Oct 2025): keyaki in gold, maples in red, no snow anywhere. '
            'Tanabata is an August festival: the kusudama are for the station and the arcade, where decorations '
            'hang all year, not for the avenue.',
            "Sendai's look is the Date clan's black lacquer and gold: black boards, gilt fittings, verdigris "
            "copper roofs, thatch, cut grey stone. Kept clear of Kanazawa's kit (white plaster and lead tiles, "
            'ochre earthen walls with straw mats, dark-red lattice fronts, black glazed tiles on houses).',
            'All sign words are generic or invented: SENDAI (the station), KEYAKI (an invented arcade name), AOBA '
            "(the ward's name, on the mid-rise), ZUNDA, KOKESHI, DISTILLERY, CRUISE, the character for beef + "
            '"tan" in kana, sa-sa-ka-ma, sa-ke, ka-ki and ya-ki in kana. No real brand artwork; no key, sign or '
            'district name carries a brand (the still house is sendai-distillery-warehouse). The mon (a crescent '
            'in a gold ring) is invented and is not the Date crest; the bronze is not a copy of a real statue.',
            'New keys only, all prefixed sendai-; generate_sendai_art.py and its sprites are untouched. NOT '
            'redrawn: the pub (sendai-pub_0_0 is already its own red-fascia pub front), the pine islets, ferry '
            'and pier. Superseded for the samurai quarter: sendai-gate (use sendai-samurai-gate), '
            'sendai-earthen-wall (use the sendai-board-fence family); sendai-maple stays as the small maple; '
            'sendai-stone-lantern stays (the new lamp posts are the ones that light a street).',
            'Fence: an east-west run is sendai-board-fence tiles (1x2, foot cell solid; -wicket is walked '
            'through). The pieces of a north-south run are 1x3 with the BOTTOM cell solid, because a fence seen '
            'end-on shows only its cap, drawn a cell and a half up the map from where it stands: where an '
            'east-west run turns north use -corner-e / -corner-w on the run\'s own row and stack -v in the rows '
            'above; a run going south from an east-west fence is -v from the next row down, ended with -end.',
            'Pedestrian deck: every deck piece is 3 cells tall and stands on ONE base row; the deck surface is '
            "drawn in its top two rows, at the height of the station front's own rail and slab. Put "
            "sendai-deck-span on the station's base row beside the station and the rails line up. A run is "
            'spans, ended by -end-e / -end-w or by -stair-e / -stair-w (the stair\'s landing cell joins the '
            'span). A north-south spur is -span-v stacked from the row BELOW a span, ended by -end-s. You walk '
            'under a span beside its pier and under -span-v; nothing climbs the deck (the game has one level).',
            'Arcade: sendai-arcade-gate at the mouth, sendai-arcade-roof on the row behind it and then every '
            'second row north (see its description), sendai-arcade-floor-autotile under them, and the kokeshi '
            'and sasakama shops (or any front) along it. Keep the floor under the whole roof: the glass is '
            'nearly clear, and it is the floor showing through that makes it read as a roof.',
            'Godaido: sendai-godaido stands in water; from the boardwalk run sendai-red-bridge-head, then '
            'sendai-red-bridge, east to the west edge of its BOTTOM row (the stone quay with two red newels).',
            'Yamadera is a side elevation by nature (a mountain): use it only as a backdrop on the north edge '
            'of the room, with nothing walkable north of its second row.',
        ],
        'sprites': sprites,
        'tile_families': [
            {'family': fam, 'roles': list(ROLES), 'files': f'gamev2/{SPR}/{fam}_<role>.png', 'size': [1, 1],
             'px': [64, 64], 'layer': 'ground', 'district': district, 'description': desc}
            for fam, district, desc in FAMILIES],
        'previews': {
            'sheet': '.agent-queue/shots/sendai_art_sheet.png',
            'scenes': [f'.agent-queue/shots/sendai_art_{n}.png' for n in SCENES],
            'night': [f'.agent-queue/shots/sendai_art_{n}_night.png' for n in SCENES],
        },
    }
    with open(out, 'w') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('manifest ->', out, f'({len(sprites)} sprites, {len(FAMILIES)} families)')


# ---- previews (not part of the game) --------------------------------------------
SCENES = ('station', 'downtown', 'samurai', 'distillery', 'bay')
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
    only make sense assembled - the fence, the deck, the bridge, the stones."""
    F, D = FENCE, DECK
    keys = [k for k, *_ in PIECES if F not in k and D not in k and 'bridge' not in k and 'stepping' not in k]
    lines, line, w = [], [], 0
    for k in keys:
        if w + built[k].width + 24 > 1720 and line:
            lines.append(line); line, w = [], 0
        line.append(k); w += built[k].width + 24
    lines.append(line)
    H = sum(max(built[k].height for k in r) + 40 for r in lines) + 64 * 4 + 64 * 8 + 80
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
    # the fence: a court's south side with both corners, a wicket, runs going north; a free run and its end
    s = Scene(built, 9, 7, None)
    s.put(f'{F}-corner-w_0_0', 0, 6); s.put(f'{F}-corner-e_0_0', 6, 6)
    for x_, n in ((1, ''), (2, ''), (3, '-wicket'), (4, ''), (5, '')):
        s.put(f'{F}{n}_0_0', x_, 6)
    for b in (5, 4, 3):
        s.put(f'{F}-v_0_0', 0, b); s.put(f'{F}-v_0_0', 6, b)
    s.put(f'{F}-v_0_0', 8, 4); s.put(f'{F}-v_0_0', 8, 5); s.put(f'{F}-end_0_0', 8, 6)
    s.render()
    im.alpha_composite(s.im, (20, y))
    # the deck: a stair, two spans, an end; a spur south from the second span and its end
    s = Scene(built, 11, 7, None)
    s.put(f'{D}-stair-w_0_0', 0, 3); s.put(f'{D}-span_0_0', 3, 3); s.put(f'{D}-span_0_0', 6, 3)
    s.put(f'{D}-end-e_0_0', 9, 3)
    s.put(f'{D}-span-v_0_0', 8, 4); s.put(f'{D}-span-v_0_0', 8, 5); s.put(f'{D}-end-s_0_0', 8, 6)
    s.put(f'{D}-stair-e_0_0', 0, 6); s.put(f'{D}-end-w_0_0', 5, 6)
    s.render()
    im.alpha_composite(s.im, (20 + 9 * 64 + 40, y))
    # the bridge over water, the stones on the lane's gravel
    x = 20 + 20 * 64 + 100
    water = spr('pond-autotile_center')
    for i in range(5):
        im.alpha_composite(water, (x + i * 64, y + 64))
    im.alpha_composite(built['sendai-red-bridge-head_0_0'], (x, y + 64))
    im.alpha_composite(built['sendai-red-bridge_0_0'], (x + 64, y + 64))
    im.alpha_composite(built['sendai-red-bridge_0_0'], (x + 192, y + 64))
    for i, v in enumerate('abc'):
        im.alpha_composite(built['sendai-samurai-lane-autotile_center'], (x + i * 64, y + 192))
        im.alpha_composite(built[f'sendai-stepping-stone-{v}_0_0'], (x + i * 64, y + 192))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(out)
    print('sheet ->', out, im.size)


def scenes(built, outdir):
    os.makedirs(outdir, exist_ok=True)
    me = 'james_front_frame_0'
    F, D = FENCE, DECK
    # Station front: the station on its plaza paving, the deck running off both ways at the height of
    # the station's own rail (a stair down at the west end, an end cap and a spur south at the east),
    # tanabata poles by the doors, the road
    s = Scene(built, 25, 14)
    s.floor('sendai-plaza-autotile', (0, 3, 24, 10))
    s.road(11, 0, 24)
    s.put('sendai-station-front_0_0', 8, 5)
    s.put(f'{D}-stair-w_0_0', 2, 5); s.put(f'{D}-span_0_0', 5, 5)
    s.put(f'{D}-span_0_0', 17, 5); s.put(f'{D}-span_0_0', 20, 5); s.put(f'{D}-end-e_0_0', 23, 5)
    for b in (6, 7, 8):
        s.put(f'{D}-span-v_0_0', 21, b)
    s.put(f'{D}-end-s_0_0', 21, 9)
    s.put('sendai-tanabata-a_0_0', 10, 7); s.put('sendai-tanabata-b_0_0', 13, 7)
    s.put('blue-lamp-post_0_0', 9, 10); s.put('blue-lamp-post_0_0', 16, 10)
    s.put('sendai-zelkova-b_0_0', 0, 10)
    s.put(me, 12, 6); s.put(me, 11, 8); s.put(me, 5, 5); s.put(me, 7, 7); s.put(me, 17, 5); s.put(me, 19, 8)
    s.put(me, 22, 8); s.put(me, 3, 8); s.put(me, 12, 13)
    s.save(f'{outdir}/sendai_art_station.png')
    # Downtown: the avenue with its median walk under keyaki and the bronze; on the north pavement the
    # mid-rise, the gyutan grill, the arcade's mouth, the zunda shop, the izakaya and the pub that is
    # already there; behind the gate the arcade's floor under three lengths of glass roof, its two shops
    s = Scene(built, 26, 20)
    s.floor('light-concrete-autotile', (0, 10, 25, 11))
    s.floor('light-concrete-autotile', (4, 2, 15, 3))               # the street at the arcade's far end
    s.floor('sendai-arcade-floor-autotile', (8, 4, 11, 9), (5, 7, 7, 7), (12, 7, 14, 7))
    s.road(12, 0, 25)
    s.floor('sendai-jozenji-autotile', (0, 15, 25, 16))
    s.road(17, 0, 25)
    s.put('sendai-sasakama-shop_0_0', 5, 6); s.put('sendai-kokeshi-shop_0_0', 12, 6)
    for b in (8, 6, 4):
        s.put('sendai-arcade-roof_0_0', 8, b)
    s.put('sendai-midrise_0_0', 0, 9)
    s.put('sendai-gyutan_0_0', 4, 9)
    s.put('sendai-arcade-gate_0_0', 8, 9)
    s.put('sendai-zunda_0_0', 12, 9)
    s.put('sendai-izakaya_0_0', 16, 9)
    s.put('sendai-pub_0_0', 20, 9)
    s.put('sendai-tanabata-a_0_0', 7, 10)
    for i, x in enumerate((0, 5, 10, 16, 21)):
        s.put('sendai-zelkova-a_0_0' if i % 2 == 0 else 'sendai-zelkova-b_0_0', x, 15)
    s.put('sendai-jozenji-statue_0_0', 13, 16); s.put('sendai-jozenji-statue_0_0', 3, 16)
    s.put(me, 5, 10); s.put(me, 9, 9); s.put(me, 10, 7); s.put(me, 9, 5); s.put(me, 13, 10); s.put(me, 17, 10)
    s.put(me, 22, 10); s.put(me, 8, 16); s.put(me, 15, 15); s.put(me, 19, 16); s.put(me, 2, 10); s.put(me, 13, 7)
    s.put(me, 6, 7); s.put(me, 10, 3)
    s.save(f'{outdir}/sendai_art_downtown.png')
    # Samurai quarter: the raked gravel lane between black fences (stepping stones laid on it), the
    # gate into a court with the thatched house, the storehouse, the armour stand, a well and the
    # propped pine; a second house to the east; the quarter's own lamps
    s = Scene(built, 24, 17)
    s.floor('sendai-samurai-lane-autotile', (0, 8, 23, 9), (5, 4, 6, 7), (17, 10, 18, 16))
    s.floor('gravel-autotile', (1, 4, 4, 6), (7, 4, 12, 6))
    for x, y, v in ((5, 7, 'c'), (5, 6, 'a'), (6, 5, 'b'), (5, 4, 'a'), (2, 8, 'a'), (3, 8, 'b'), (9, 9, 'a'),
                    (10, 8, 'b'), (17, 10, 'a'), (18, 11, 'b'), (17, 13, 'a'), (17, 9, 'c'), (20, 8, 'a')):
        s.flat(f'sendai-stepping-stone-{v}_0_0', x, y)
    s.put('sendai-samurai-house-a_0_0', 4, 3); s.put('sendai-samurai-store_0_0', 10, 3)
    s.put('sendai-kabuto-stand_0_0', 1, 5); s.put('sendai-well_0_0', 12, 5)
    s.put('sendai-propped-pine_0_0', 8, 6)
    s.put(f'{F}-corner-w_0_0', 0, 7)
    for x in range(1, 4):
        s.put(f'{F}_0_0', x, 7)
    s.put('sendai-samurai-gate_0_0', 4, 7)
    for x in range(8, 13):
        s.put(f'{F}-wicket_0_0' if x == 10 else f'{F}_0_0', x, 7)
    s.put(f'{F}-corner-e_0_0', 13, 7)
    for y in range(2, 7):
        s.put(f'{F}-v_0_0', 0, y); s.put(f'{F}-v_0_0', 13, y)
    s.put('sendai-samurai-house-b_0_0', 16, 6)
    s.put('sendai-red-maple_0_0', 20, 6); s.put('sendai-andon-lamp-post_0_0', 15, 7)
    s.put('sendai-andon-lamp-post_0_0', 3, 10); s.put('sendai-andon-lamp-post_0_0', 19, 12)
    for x in list(range(0, 17)) + list(range(19, 24)):
        s.put(f'{F}_0_0', x, 11)
    for y in (12, 13, 14):
        s.put(f'{F}-v_0_0', 8, y)
    s.put(f'{F}-end_0_0', 8, 15)
    s.put('sendai-pine_0_0', 3, 15); s.put('sendai-zelkova-b_0_0', 11, 15); s.put('sendai-well_0_0', 21, 14)
    s.put(me, 5, 8); s.put(me, 6, 6); s.put(me, 3, 5); s.put(me, 10, 8); s.put(me, 14, 9); s.put(me, 17, 12)
    s.put(me, 17, 7); s.put(me, 21, 9); s.put(me, 3, 6); s.put(me, 9, 6); s.put(me, 9, 13); s.put(me, 6, 13)
    s.save(f'{outdir}/sendai_art_samurai.png')
    # The distillery: the brick yard, the still house beside the kiln that is already there, casks,
    # red maples, and Yamadera as the backdrop on the north edge
    s = Scene(built, 24, 15)
    s.floor('sendai-brick-yard-autotile', (6, 9, 21, 12), (11, 13, 12, 14))
    s.put('sendai-yamadera_0_0', 0, 6)
    s.put('sendai-kiln_0_0', 7, 8); s.put('sendai-distillery-warehouse_0_0', 13, 8)
    s.put('sendai-cask-rack_0_0', 7, 11); s.put('sendai-cask-rack_0_0', 18, 11); s.put('sendai-barrels_0_0', 10, 11)
    s.put('sendai-red-maple_0_0', 20, 8); s.put('sendai-red-maple_0_0', 21, 14); s.put('sendai-maple_0_0', 3, 12)
    s.put('sendai-cedar_0_0', 22, 5); s.put('sendai-zelkova-b_0_0', 0, 13); s.put('sendai-cedar_0_0', 6, 4)
    s.put('blue-lamp-post_0_0', 12, 9)
    s.put(me, 17, 9); s.put(me, 15, 9); s.put(me, 11, 10); s.put(me, 11, 13); s.put(me, 20, 10); s.put(me, 3, 7)
    s.put(me, 1, 9)
    s.save(f'{outdir}/sendai_art_distillery.png')
    # Matsushima bay: the boardwalk along the shore with its lamps, the cruise booth and the oyster
    # shack, the pier and ferry that are already there, Godaido on its islet at the end of the red
    # bridge (its head at the boardwalk), the islets
    s = Scene(built, 24, 14)
    s.fill('pond-autotile_center', 11, 0, 23, 13)
    s.fill('pond-autotile_edge-w', 11, 0, 11, 13)
    s.floor('sendai-boardwalk-autotile', (7, 0, 10, 13))
    s.floor('light-concrete-autotile', (0, 5, 6, 6))
    s.flat('sendai-red-bridge-head_0_0', 11, 4); s.flat('sendai-red-bridge_0_0', 12, 4)
    s.flat('matsushima-pier_0_0', 11, 10)
    s.put('sendai-godaido_0_0', 14, 4)
    s.put('matsushima-ferry_0_0', 16, 10)
    s.put('matsushima-islet_0_0', 20, 2); s.put('matsushima-islet-small_0_0', 21, 7); s.put('matsushima-islet_0_0', 14, 13)
    s.put('matsushima-ball-rock_0_0', 20, 12)
    s.put('sendai-oyster-shack_0_0', 2, 4); s.put('sendai-cruise-booth_0_0', 3, 10)
    s.put('sendai-pine_0_0', 0, 3); s.put('sendai-pine_0_0', 0, 12)
    s.put('sendai-bay-lamp-post_0_0', 10, 2); s.put('sendai-bay-lamp-post_0_0', 10, 8); s.put('sendai-bay-lamp-post_0_0', 7, 13)
    s.put(me, 8, 4); s.put(me, 12, 4); s.put(me, 5, 5); s.put(me, 9, 8); s.put(me, 4, 11); s.put(me, 12, 10)
    s.put(me, 8, 12)
    s.save(f'{outdir}/sendai_art_bay.png')


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
