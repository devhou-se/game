#!/usr/bin/env python3
"""generate_pagoda_art.py — everything inside a pagoda (issue #214; the rooms
are built by tools/generate_pagodas.py). The GuttyKreum pagodas are exteriors
only, so the inside is drawn here, in the manner of the other interior art
tools: shaded pixel art with a 1px ink outline, drawn at half size (32px a
cell) and pixel-doubled. Nothing is line art, nothing is random between runs
(every scatter is seeded) and there is no lettering, so a re-run draws the
same pixels on any machine; a PNG whose pixels have not changed is left as it
is on disk (zlib differs between machines, pixels do not).

A pagoda's room is a cutaway of the whole tower: every storey one above the
other, the roofs outside them, the dark all round. Old timber, vermilion posts
and beams, white plaster, old gold; the roofs are the terracotta of the towers
outside. All sprites are `pagoda-in-<piece>`:
  board-a / board-b       a storey's floor: wide old boards
  hatch                   the floor cell a stair comes up through
  wall-head (-w / -e)     the back wall's upper row: the beam, bracket blocks, plaster
  wall (-w / -e)          its lower row: plaster over a boarded dado (-w / -e: the corner posts)
  side-w / side-e         the side walls, seen from above along their length
  edge (-w / -e)          a storey's cut floor: boards, the vermilion beam, the joists under it
  base (-w / -e)          the ground floor's: boards on the stone podium
  threshold               the doorway in the podium, the day outside it
  doorlight               1x2 daylight through the door (lies flat)
  eave-w / eave-e         3x1 the roof skirt that hangs outside a storey's floor, a wind bell at its tip
  roof                    9x6 the top roof, seen from the front, and the spire on it: the rings and the flame
  stair                   1x3 a steep stair up the back wall and through the floor above
  pillar                  1x3 the heart pillar: it stands in a gap in the floor; only its foot is solid
  shumidan                3x3 the ground floor's dais round the pillar: four small Buddhas (three seen)
  saisen                  the offering box (bump it)
  shokudai                1x2 a candle on a tall stand;  toro-hang: 1x2 a hung lantern (Tops)
  kyozo                   2x2 shelves of sutra chests (on the back wall)
  senbutsu                2x2 a wall of tiny gilt Buddhas (on the back wall)
  window                  3x2 a slatted window: roofs outside (on the back wall)

Run from gamev2/:  python3 tools/generate_pagoda_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames,
and the roof in game.lookUp.sprites.
"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageOps

C = 32      # canvas px per cell (doubled on save)

INK = (30, 26, 44)
VOID = (12, 12, 17)                                                            # office-void: the dark round the tower
WHITE, PAPER_SH = (250, 246, 232), (190, 180, 168)
GLOW, GLOW_HI = (255, 206, 120), (255, 240, 196)
FLAME, FLAME_HI = (255, 170, 60), (255, 244, 190)
LQ, LQ_HI, LQ_DK = (40, 32, 46), (86, 70, 90), (24, 18, 30)                    # black lacquer, deep shadow
VERM, VERM_HI, VERM_DK = (186, 58, 48), (228, 104, 72), (128, 36, 46)          # vermilion posts and beams
GOLD, GOLD_HI, GOLD_DK = (214, 164, 70), (250, 220, 130), (150, 104, 52)       # gilt
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = (116, 80, 58), (108, 74, 56), (148, 106, 72), (76, 50, 46)
WOOD, WOOD_HI, WOOD_DK = (96, 62, 50), (140, 96, 68), (62, 40, 42)             # dark timber
CYP, CYP_HI, CYP_DK = (168, 124, 84), (206, 164, 112), (116, 80, 62)           # the pillar's bare cypress
PLASTER, PLASTER_HI, PLASTER_SH = (204, 190, 160), (226, 214, 184), (166, 150, 134)
STONE, STONE_HI, STONE_DK = (104, 100, 112), (138, 134, 144), (70, 66, 82)
TILE, TILE_HI, TILE_DK = (188, 96, 78), (228, 138, 102), (126, 58, 62)         # roof tiles
BRASS, BRASS_HI, BRASS_DK = (190, 150, 74), (240, 210, 130), (126, 92, 52)
IRON, IRON_HI = (58, 56, 70), (104, 102, 118)
SLAT, SLAT_HI = (70, 112, 84), (112, 156, 108)                                 # a window's green slats
SKY, SKY_LO = (176, 208, 228), (214, 226, 226)
PURPLE, PURPLE_DK = (98, 58, 120), (62, 36, 84)
PINK, PINK_HI = (214, 120, 140), (244, 176, 184)


def new(w, h, fill=(0, 0, 0, 0)):
    im = Image.new('RGBA', (w, h), fill)
    return im, ImageDraw.Draw(im)


def box(d, x0, y0, x1, y1, fill, outline=INK):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bar(d, x0, y0, x1, y1, base, hi, dk):
    """A horizontal timber: lit along the top, shaded along the bottom."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0, y0 + 1, x1, y0 + 1], fill=hi)
    d.line([x0, y1 - 1, x1, y1 - 1], fill=dk)
    d.line([x0, y0, x1, y0], fill=INK)
    d.line([x0, y1, x1, y1], fill=INK)


def post(d, x0, y0, x1, y1, base, hi, dk):
    """An upright timber: lit down its left side, shaded down its right."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0 + 1, y0, x0 + 1, y1], fill=hi)
    d.line([x1 - 1, y0, x1 - 1, y1], fill=dk)
    d.line([x0, y0, x0, y1], fill=INK)
    d.line([x1, y0, x1, y1], fill=INK)


def shadow(d, x0, y0, x1, y1, a=90):
    d.ellipse([x0, y0, x1, y1], fill=(0, 0, 0, a))


def stud(d, x, y):
    """A gilt nail cover, 3x3."""
    d.rectangle([x, y, x + 2, y + 2], fill=GOLD)
    d.point((x, y), fill=GOLD_HI)
    d.point((x + 2, y + 2), fill=GOLD_DK)


def mirrored(fn):
    return lambda: ImageOps.mirror(fn())


# ---- the floor --------------------------------------------------------------------

def _boards(d, x0, y0, x1, y1, seed):
    """Wide boards laid across the room, their butt joints staggered."""
    rnd = random.Random(seed)
    d.rectangle([x0, y0, x1, y1], fill=BOARD)
    for i, y in enumerate(range(y0, y1 + 1, 8)):
        if (i + seed) % 3 == 0:
            d.rectangle([x0, y, x1, min(y + 7, y1)], fill=BOARD_ALT)
        d.line([x0, y, x1, y], fill=BOARD_DK)
        if y + 1 <= y1:
            a = x0 + rnd.randrange(2, 12)
            d.line([a, y + 1, a + rnd.randrange(6, 16), y + 1], fill=BOARD_HI)              # worn smooth
        j = x0 + (7 if (i + seed) % 2 else 22)
        if j <= x1:
            d.line([j, y, j, min(y + 7, y1)], fill=BOARD_DK)
        for _ in range(2):
            gx, gy = x0 + rnd.randrange(x1 - x0 + 1), y + 3 + rnd.randrange(4)
            if gy <= y1:
                d.line([gx, gy, min(gx + 3, x1), gy], fill=mix(BOARD, BOARD_DK, 0.5))       # grain


def board(seed):
    def draw():
        im, d = new(C, C)
        _boards(d, 0, 0, 31, 31, seed)
        return im
    return draw


def _treads(d, y0, y1):
    """A steep stair seen from its foot: two stringers, the treads between them."""
    d.rectangle([3, y0, 28, y1], fill=LQ_DK)
    for x in (3, 25):
        post(d, x, y0, x + 3, y1, WOOD, WOOD_HI, WOOD_DK)
    for y in range(y0 + 2, y1 - 2, 6):
        d.rectangle([7, y, 24, y + 2], fill=BOARD)
        d.line([7, y, 24, y], fill=BOARD_HI)
        d.line([7, y + 2, 24, y + 2], fill=BOARD_DK)
        d.line([7, y + 3, 24, y + 3], fill=INK)


def hatch():
    """The floor cell a stair comes up through: the opening, its trimmers, the top treads."""
    im, d = new(C, C)
    _boards(d, 0, 0, 31, 31, 2)
    _treads(d, 9, 31)
    bar(d, 2, 6, 29, 10, WOOD, WOOD_HI, WOOD_DK)                 # the trimmer across its head
    for x in (2, 27):                                            # a newel each side
        box(d, x, 2, x + 2, 9, WOOD)
        d.point((x + 1, 3), fill=WOOD_HI)
        d.point((x + 1, 1), fill=GOLD)
    return im


# ---- the walls --------------------------------------------------------------------

def _wall_head(d, x0, x1):
    """The back wall's upper row over x0..x1: the dark under the floor above, the
    vermilion beam with its gilt nails, plaster between posts a cell apart."""
    d.rectangle([x0, 0, x1, 3], fill=LQ_DK)
    d.line([x0, 3, x1, 3], fill=INK)
    d.rectangle([x0, 10, x1, 31], fill=PLASTER)
    d.line([x0, 10, x1, 10], fill=PLASTER_SH)
    d.line([x0, 11, x1, 11], fill=PLASTER_SH)
    bar(d, x0, 4, x1, 9, VERM, VERM_HI, VERM_DK)


def _wall(d, x0, x1):
    """Its lower row: plaster, a rail, the boarded dado."""
    d.rectangle([x0, 0, x1, 15], fill=PLASTER)
    bar(d, x0, 15, x1, 19, VERM, VERM_HI, VERM_DK)
    d.rectangle([x0, 20, x1, 29], fill=WOOD)
    d.line([x0, 20, x1, 20], fill=WOOD_HI)
    d.rectangle([x0, 30, x1, 31], fill=LQ_DK)


def _posts(d, y0, y1, dado=False):
    """Half a post at each side of a wall cell: whole posts where cells meet."""
    for x0, x1, col in ((0, 1, VERM), (30, 31, VERM_DK)):
        d.rectangle([x0, y0, x1, y1], fill=col)
    d.line([1, y0, 1, y1], fill=INK)
    d.line([30, y0, 30, y1], fill=INK)
    d.line([0, y0, 0, y1], fill=VERM_DK)
    d.line([31, y0, 31, y1], fill=VERM_HI)
    if dado:
        for x in (8, 16, 24):
            d.line([x, 21, x, 29], fill=WOOD_DK)


def wall_head():
    im, d = new(C, C)
    _wall_head(d, 0, 31)
    _posts(d, 10, 31)
    for x in (0, 28):                                            # bracket blocks under the beam
        d.rectangle([x, 10, x + 3, 13], fill=WOOD)
        d.line([x, 13, x + 3, 13], fill=INK)
    stud(d, 15, 5)
    d.point((9, 20), fill=PLASTER_HI)
    d.line([19, 16, 22, 16], fill=PLASTER_HI)
    return im


def wall():
    im, d = new(C, C)
    _wall(d, 0, 31)
    _posts(d, 0, 29, dado=True)
    d.line([6, 6, 9, 6], fill=PLASTER_HI)
    d.point((22, 10), fill=PLASTER_SH)
    return im


def _corner(d, y0=0, y1=31):
    """The west corner post in a wall cell, and the dark outside it."""
    d.rectangle([0, 0, 19, 31], fill=VOID)
    d.rectangle([20, y0, 31, y1], fill=VERM)
    d.rectangle([22, y0, 23, y1], fill=VERM_HI)
    d.rectangle([28, y0, 30, y1], fill=VERM_DK)
    d.line([20, y0, 20, y1], fill=INK)
    d.line([31, y0, 31, y1], fill=INK)


def wall_head_w():
    im, d = new(C, C)
    _wall_head(d, 20, 31)
    _corner(d, 10, 31)
    d.rectangle([20, 0, 31, 3], fill=LQ_DK)
    bar(d, 20, 4, 31, 9, VERM, VERM_HI, VERM_DK)
    d.line([20, 0, 20, 9], fill=INK)
    stud(d, 24, 5)
    return im


def wall_w():
    im, d = new(C, C)
    _corner(d)
    box(d, 20, 24, 31, 31, STONE_DK)                             # the stone its foot stands on
    d.line([21, 25, 30, 25], fill=STONE)
    for y in (6, 16):
        d.rectangle([21, y, 30, y + 1], fill=GOLD_DK)
        d.line([22, y, 25, y], fill=GOLD)
    return im


def side_w():
    """The west wall from above: its top, and a sliver of its inner face."""
    im, d = new(C, C, VOID)
    d.rectangle([20, 0, 31, 31], fill=WOOD)
    d.rectangle([22, 0, 23, 31], fill=WOOD_HI)
    d.rectangle([28, 0, 31, 31], fill=VERM_DK)
    d.line([20, 0, 20, 31], fill=INK)
    d.line([27, 0, 27, 31], fill=INK)
    for y in (0, 16):
        d.line([21, y, 26, y], fill=WOOD_DK)
    return im


def _edge(d, x0, x1, seed=0):
    """A storey's floor cut through: the boards' ends, the vermilion beam the
    floor sits on, rafter ends, and the dark of the storey below."""
    d.rectangle([x0, 0, x1, 2], fill=BOARD_HI)
    d.line([x0, 2, x1, 2], fill=BOARD)
    bar(d, x0, 3, x1, 12, VERM, VERM_HI, VERM_DK)
    for y in range(13, 32):
        d.line([x0, y, x1, y], fill=mix(WOOD_DK, LQ_DK, min(1, (y - 13) / 12)))
    d.line([x0, 13, x1, 13], fill=INK)
    for x in range(x0 + 2 - (x0 % 8), x1, 8):                    # rafter ends, painted white
        if x >= x0 and x + 3 <= x1:
            d.rectangle([x, 15, x + 3, 19], fill=PAPER_SH)
            d.rectangle([x, 15, x + 2, 18], fill=WHITE)
            d.rectangle([x, 20, x + 3, 27], fill=WOOD_DK)


def edge():
    im, d = new(C, C)
    _edge(d, 0, 31)
    stud(d, 15, 6)
    return im


def edge_w():
    im, d = new(C, C, VOID)
    _edge(d, 20, 31)
    d.line([20, 0, 20, 31], fill=INK)
    return im


def _base(d, x0, x1):
    """The ground floor's: boards on a podium of dressed stone."""
    d.rectangle([x0, 0, x1, 2], fill=BOARD_HI)
    d.line([x0, 2, x1, 2], fill=BOARD)
    d.line([x0, 3, x1, 3], fill=INK)
    d.rectangle([x0, 4, x1, 31], fill=STONE)
    d.line([x0, 4, x1, 4], fill=STONE_HI)
    d.line([x0, 5, x1, 5], fill=STONE_HI)
    for y in (13, 22):
        d.line([x0, y, x1, y], fill=STONE_DK)
    for y, off in ((6, 9), (14, 25), (23, 15)):
        for x in range(x0 - (x0 % 32) + off, x1, 32):
            if x >= x0:
                d.line([x, y, x, y + 7], fill=STONE_DK)
    d.rectangle([x0, 29, x1, 31], fill=STONE_DK)
    d.line([x0, 31, x1, 31], fill=INK)


def base():
    im, d = new(C, C)
    _base(d, 0, 31)
    return im


def base_w():
    im, d = new(C, C, VOID)
    _base(d, 16, 31)
    d.line([16, 3, 16, 31], fill=INK)
    d.rectangle([16, 0, 19, 2], fill=VOID)
    d.line([20, 0, 20, 3], fill=INK)
    return im


def threshold():
    """The doorway through the podium: both leaves open, the day outside."""
    im, d = new(C, C)
    _base(d, 0, 31)
    for y in range(0, 32):
        d.line([4, y, 27, y], fill=mix((236, 214, 170), (255, 248, 226), y / 31))
    for y in (10, 21):                                           # the steps down
        d.line([4, y, 27, y], fill=(214, 190, 150))
    for x in (1, 28):                                            # the door posts, the leaves folded back
        post(d, x, 0, x + 2, 31, VERM, VERM_HI, VERM_DK)
    for x in (4, 25):
        d.rectangle([x, 0, x + 2, 26], fill=WOOD)
        d.line([x, 0, x, 26], fill=WOOD_HI)
        d.point((x + 1, 14), fill=GOLD)
    return im


def doorlight():
    """Daylight through the door, lying on the boards (flat, half-clear)."""
    im, d = new(C, 2 * C)
    for y in range(8, 64):
        t = (y - 8) / 55
        half = round(6 + 8 * t)
        d.line([16 - half, y, 15 + half, y], fill=(255, 228, 170, round(12 + 44 * t)))
    return im


# ---- the roofs outside -----------------------------------------------------------

def _tiles(im, mask, seed):
    """Fill `mask` with courses of roof tile: ribs down the slope, a lit lip to each."""
    rnd = random.Random(seed)
    tex, d = new(*im.size)
    d.rectangle([0, 0, im.width, im.height], fill=TILE)
    for x in range(0, im.width, 6):
        d.line([x, 0, x, im.height], fill=TILE_DK)
        d.line([x + 1, 0, x + 1, im.height], fill=TILE_HI)
    for y in range(3, im.height, 7):
        for x in range(0, im.width, 6):
            d.line([x + 2, y, x + 5, y], fill=TILE_DK)
            if rnd.random() < 0.5:
                d.point((x + 3, y + 1), fill=TILE_HI)
    im.paste(tex, (0, 0), mask)


def eave_w():
    """The roof skirt outside a storey's floor: it hangs from the wall (which
    stands in the last 12px) out to an upturned tip, a wind bell under it."""
    w = 3 * C
    im, d = new(w, C)
    top = [(84, 1), (60, 7), (36, 14), (16, 19), (6, 19), (1, 13)]
    under = [(3, 20), (12, 26), (36, 22), (60, 17), (84, 13)]
    mask = Image.new('L', (w, C), 0)
    ImageDraw.Draw(mask).polygon(top + under, fill=255)
    _tiles(im, mask, 3)
    d.line(top, fill=INK)
    d.line(under + [(84, 1)], fill=INK)
    d.line([(4, 19), (13, 24), (36, 20), (60, 15), (83, 11)], fill=TILE_DK)
    d.polygon([(14, 27), (36, 23), (60, 18), (84, 14), (84, 19), (60, 23), (36, 27), (18, 30)], fill=WOOD_DK, outline=INK)
    for x, y in ((24, 26), (34, 25), (44, 23), (54, 21), (64, 19), (74, 17)):                # rafter ends
        d.rectangle([x, y, x + 2, y + 2], fill=WHITE)
        d.point((x + 2, y + 2), fill=PAPER_SH)
    d.line([1, 13, 1, 10], fill=GOLD)                                                          # the tip's gilt cap
    d.point((2, 12), fill=GOLD_HI)
    d.line([6, 22, 6, 25], fill=BRASS_DK)                                                      # the wind bell
    d.polygon([(4, 26), (8, 26), (9, 30), (3, 30)], fill=BRASS, outline=INK)
    d.point((5, 28), fill=BRASS_HI)
    d.point((6, 31), fill=GOLD_HI)
    return im


def _roof():
    """The top roof from the front: tiled slopes swept up at the corners, the
    rafters under its eaves."""
    w, h = 9 * C, 3 * C
    im, d = new(w, h)
    cx = w // 2
    left = [(cx - 14, 8), (cx - 40, 34), (cx - 78, 56), (cx - 112, 70), (cx - 132, 72), (cx - 142, 62)]
    low = [(cx - 138, 74), (cx - 120, 82), (cx, 82)]
    pts = left + low
    pts = pts + [(w - 1 - x, y) for x, y in reversed(pts)]
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    _tiles(im, mask, 5)
    for x, y in ((cx - 30, 26), (cx - 62, 48), (cx - 100, 66)):   # the hips catch the light
        d.line([x, y, x + 3, y - 3], fill=TILE_HI)
        d.line([w - 1 - x, y, w - 4 - x, y - 3], fill=TILE_DK)
    d.line(pts + [pts[0]], fill=INK)
    d.line([(cx - 137, 73), (cx - 120, 80), (cx + 120, 80), (cx + 137, 73)], fill=TILE_DK)
    d.polygon([(cx - 118, 83), (cx + 118, 83), (cx + 108, 95), (cx - 108, 95)], fill=WOOD_DK, outline=INK)
    bar(d, cx - 112, 84, cx + 112, 88, VERM, VERM_HI, VERM_DK)
    for x in range(cx - 104, cx + 104, 8):                        # rafter ends
        d.rectangle([x, 90, x + 3, 93], fill=WHITE)
        d.line([x + 3, 90, x + 3, 93], fill=PAPER_SH)
    for sx in (cx - 142, cx + 141):                               # gilt caps, a wind bell at each corner
        d.line([sx, 62, sx, 58], fill=GOLD)
    for bx in (cx - 134, cx + 133):
        d.line([bx, 75, bx, 79], fill=BRASS_DK)
        d.polygon([(bx - 2, 80), (bx + 2, 80), (bx + 3, 85), (bx - 3, 85)], fill=BRASS, outline=INK)
        d.point((bx, 86), fill=GOLD_HI)
    box(d, cx - 15, 2, cx + 14, 9, GOLD_DK)                       # the dew basin the spire stands in
    d.line([cx - 14, 3, cx + 13, 3], fill=GOLD_HI)
    return im


def _spire(d, x, yb):
    """The spire, from the dew basin up: the inverted bowl, nine rings, the
    water-flame and the jewel. `x` is its cell's left edge, `yb` its foot."""
    f = yb - 69                                                                                # the flame's tip
    d.rectangle([x + 15, f, x + 16, yb], fill=GOLD_DK)                                         # the mast
    d.polygon([(x + 9, yb), (x + 22, yb), (x + 19, yb - 8), (x + 12, yb - 8)], fill=GOLD, outline=INK)   # the inverted bowl
    d.line([x + 13, yb - 6, x + 18, yb - 6], fill=GOLD_HI)
    for i in range(9):                                                                         # nine rings, wider towards the foot
        y, half = yb - 45 + 4 * i, 5 + i // 2
        d.rectangle([x + 15 - half, y, x + 16 + half, y + 2], fill=GOLD, outline=INK)
        d.line([x + 16 - half, y + 1, x + 15, y + 1], fill=GOLD_HI)
    d.polygon([(x + 15, f), (x + 9, f + 9), (x + 11, f + 18), (x + 15, f + 22), (x + 16, f + 22), (x + 20, f + 18), (x + 22, f + 9),
               (x + 16, f)], fill=GOLD, outline=INK)
    for px, py in ((13, 9), (18, 9), (15, 13), (13, 17), (18, 17)):                            # the water-flame's openwork
        d.point((x + px, f + py), fill=INK)
    d.line([x + 12, f + 7, x + 14, f + 3], fill=GOLD_HI)
    d.ellipse([x + 12, f - 8, x + 19, f - 1], fill=GOLD, outline=INK)                          # the jewel
    d.point((x + 14, f - 6), fill=GOLD_HI)
    d.rectangle([x + 15, f - 10, x + 16, f - 9], fill=GOLD)


def roof():
    """The top roof with its spire, one sprite: the camera looks up at it from
    the top storey (LOOK_UP), and one sprite as wide as the roof holds the
    view still as you cross that floor."""
    im, d = new(9 * C, 6 * C)
    im.alpha_composite(_roof(), (0, 3 * C))
    _spire(d, 4 * C, 3 * C + 6)                                   # its foot in the dew basin; clear of the HUD bar at the room's top
    return im


# ---- the stair ----------------------------------------------------------------

def stair():
    """A steep stair against the back wall: it climbs both wall rows and goes
    through the floor above (the top cell is that storey's cut floor)."""
    im, d = new(C, 3 * C)
    im.alpha_composite(edge(), (0, 0))
    im.alpha_composite(wall_head(), (0, C))
    im.alpha_composite(wall(), (0, 2 * C))
    _treads(d, 0, 95)
    d.rectangle([7, 0, 24, 5], fill=LQ_DK)                       # the dark of the opening
    for x in (2, 29):                                            # a handrail each side, pegged to the wall
        d.line([x, 36, x, 92], fill=WOOD_DK)
    return im


# ---- what stands on the floors ----------------------------------------------------

def _grain(d, x0, y0, x1, y1, seed):
    rnd = random.Random(seed)
    for _ in range((y1 - y0) // 5):
        x, y = rnd.randrange(x0 + 2, x1 - 3), rnd.randrange(y0, y1 - 8)
        d.line([x, y, x, y + rnd.randrange(4, 9)], fill=mix(CYP, CYP_DK, 0.45))


def _shaft(im, x0, y0, x1, y1, seed):
    """The heart pillar's shaft: bare cypress, round, darker up in the gloom."""
    d = ImageDraw.Draw(im)
    d.rectangle([x0, y0, x1, y1], fill=CYP)
    d.rectangle([x0 + 1, y0, x0 + 3, y1], fill=CYP_HI)
    d.rectangle([x0 + 4, y0, x0 + 4, y1], fill=mix(CYP, CYP_HI, 0.5))
    d.rectangle([x1 - 4, y0, x1 - 1, y1], fill=CYP_DK)
    _grain(d, x0 + 4, y0, x1 - 4, y1, seed)
    for y in range(y0, min(y1, y0 + 10)):                        # it goes on up, into the dark
        t = 1 - (y - y0) / 10
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=mix(im.getpixel((x, y))[:3], LQ_DK, 0.7 * t))
    d.line([x0, y0, x0, y1], fill=INK)
    d.line([x1, y0, x1, y1], fill=INK)


def pillar():
    """The heart pillar where it passes a floor: it touches nothing, so there
    is a gap in the boards all round it. An iron band, a gilt one."""
    im, d = new(C, 3 * C)
    d.ellipse([2, 80, 29, 95], fill=VOID, outline=INK)           # the gap in the floor
    d.arc([3, 81, 28, 94], 200, 340, fill=BOARD_DK)
    _shaft(im, 8, 0, 23, 89, 1)
    d.rectangle([8, 54, 23, 58], fill=IRON)
    d.line([9, 55, 14, 55], fill=IRON_HI)
    d.rectangle([8, 54, 23, 58], outline=INK)
    box(d, 8, 30, 23, 33, GOLD_DK)
    d.line([9, 31, 14, 31], fill=GOLD_HI)
    d.rectangle([8, 86, 23, 89], fill=mix(CYP_DK, LQ_DK, 0.6))   # its foot goes down into the dark
    d.line([8, 86, 8, 89], fill=INK)
    d.line([23, 86, 23, 89], fill=INK)
    return im


def _buddha(d, cx, y, small=False):
    """A small seated gilt Buddha, its lotus on (cx, y): halo, head, robes."""
    d.ellipse([cx - 6, y - 21, cx + 6, y - 8], fill=GOLD_DK, outline=INK)                    # the halo
    d.ellipse([cx - 4, y - 19, cx + 4, y - 10], outline=GOLD)
    d.polygon([(cx - 6, y - 3), (cx - 3, y - 11), (cx + 3, y - 11), (cx + 6, y - 3)], fill=GOLD, outline=INK)
    d.line([cx - 2, y - 9, cx - 3, y - 4], fill=GOLD_HI)
    d.line([cx - 3, y - 5, cx + 3, y - 5], fill=GOLD_DK)                                     # the hands in the lap
    d.rectangle([cx - 2, y - 16, cx + 2, y - 11], fill=GOLD, outline=INK)                    # the head
    d.point((cx - 1, y - 14), fill=GOLD_HI)
    d.line([cx - 1, y - 17, cx + 1, y - 17], fill=LQ)
    d.polygon([(cx - 8, y - 3), (cx + 8, y - 3), (cx + 5, y + 1), (cx - 5, y + 1)], fill=PINK, outline=INK)   # the lotus
    for x in (cx - 4, cx, cx + 4):
        d.point((x, y - 2), fill=PINK_HI)


def shumidan():
    """The ground floor: the heart pillar stands on its foundation stone in a
    lacquered dais, a small gilt Buddha at its foot on each side (the fourth is
    behind it)."""
    w = 3 * C
    im, d = new(w, 3 * C)
    shadow(d, 4, 80, w - 5, 95, 100)
    _shaft(im, 39, 0, 56, 60, 2)
    box(d, 39, 26, 56, 29, GOLD_DK)
    d.line([40, 27, 46, 27], fill=GOLD_HI)
    d.polygon([(14, 62), (w - 15, 62), (w - 7, 70), (w - 7, 88), (6, 88), (6, 70)], fill=LQ, outline=INK)    # the dais
    d.polygon([(16, 60), (w - 17, 60), (w - 9, 68), (8, 68)], fill=VERM_DK, outline=INK)                      # its top
    d.line([18, 61, w - 19, 61], fill=VERM)
    bar(d, 6, 68, w - 7, 72, GOLD_DK, GOLD, mix(GOLD_DK, INK, 0.4))
    for x in range(12, w - 14, 12):                                                                           # panels
        d.rectangle([x, 75, x + 8, 84], fill=LQ_DK, outline=LQ_HI)
        d.point((x + 4, 79), fill=GOLD)
    bar(d, 4, 86, w - 5, 91, LQ, LQ_HI, LQ_DK)
    d.ellipse([34, 52, 61, 64], fill=STONE_DK, outline=INK)                                                   # the foundation stone
    d.ellipse([36, 52, 59, 59], fill=STONE)
    d.rectangle([40, 50, 55, 58], fill=CYP)
    d.rectangle([40, 50, 42, 58], fill=CYP_HI)
    d.rectangle([52, 50, 55, 58], fill=CYP_DK)
    _buddha(d, 20, 62)
    _buddha(d, w - 21, 62)
    _buddha(d, w // 2, 68)
    for x in (30, w - 34):                                                                                    # offerings set out
        d.rectangle([x, 62, x + 3, 65], fill=BRASS, outline=INK)
        d.point((x + 1, 60), fill=PINK_HI)
        d.point((x + 2, 61), fill=SLAT_HI)
    return im


def saisen():
    """The offering box: a small slatted chest."""
    im, d = new(C, C)
    shadow(d, 2, 22, 29, 31, 100)
    d.polygon([(5, 14), (26, 14), (28, 28), (3, 28)], fill=WOOD, outline=INK)                # the front
    for y in (19, 24):
        d.line([5, y, 26, y], fill=WOOD_DK)
        d.line([5, y + 1, 26, y + 1], fill=WOOD_HI)
    for x in (6, 23):                                                                          # iron straps, gilt nails
        d.rectangle([x, 15, x + 2, 27], fill=LQ)
        d.point((x + 1, 17), fill=GOLD)
        d.point((x + 1, 25), fill=GOLD)
    d.rectangle([13, 17, 18, 24], fill=LQ, outline=GOLD_DK)                                    # the crest
    d.point((15, 20), fill=GOLD_HI)
    d.point((16, 21), fill=GOLD)
    d.polygon([(3, 14), (28, 14), (25, 5), (6, 5)], fill=WOOD_DK, outline=INK)                # the top: slats over the dark
    for x in range(8, 25, 4):
        t = (x - 15.5) / 12
        d.line([x, 6, round(x + t * 3), 13], fill=WOOD_HI)
    bar(d, 2, 12, 29, 15, WOOD, WOOD_HI, WOOD_DK)
    d.point((9, 30), fill=GOLD_HI)                                                             # a coin that missed
    return im


def shokudai():
    """A tall iron candle stand: one fat candle, wax down its side."""
    im, d = new(C, 2 * C)
    shadow(d, 7, 55, 24, 63, 90)
    for x0, x1 in ((9, 13), (18, 22)):                                                         # three feet
        d.line([x0, 61, x1 - (x0 - 9) // 2, 55], fill=IRON)
    d.line([15, 61, 16, 55], fill=IRON)
    d.rectangle([14, 30, 17, 56], fill=IRON)
    d.line([14, 30, 14, 56], fill=IRON_HI)
    d.rectangle([14, 30, 17, 56], outline=INK)
    for y in (38, 48):
        d.rectangle([12, y, 19, y + 2], fill=BRASS, outline=BRASS_DK)
    d.polygon([(8, 27), (23, 27), (20, 31), (11, 31)], fill=BRASS, outline=INK)               # the pan
    d.line([10, 28, 21, 28], fill=BRASS_HI)
    d.rectangle([12, 14, 19, 27], fill=WHITE, outline=PAPER_SH)                                # the candle
    d.line([18, 15, 18, 26], fill=PAPER_SH)
    d.point((12, 20), fill=WHITE)
    d.line([15, 11, 15, 13], fill=INK)
    d.polygon([(15, 3), (18, 9), (16, 12), (14, 12), (12, 9)], fill=FLAME)
    d.polygon([(15, 6), (17, 10), (15, 12), (14, 10)], fill=FLAME_HI)
    return im


def toro_hang():
    """An iron lantern hung on a chain from the floor above (Tops)."""
    im, d = new(C, 2 * C)
    for y in range(0, 16, 3):
        d.rectangle([15, y, 16, y + 1], fill=IRON_HI)
    d.polygon([(15, 14), (16, 14), (26, 23), (5, 23)], fill=IRON, outline=INK)                # its roof
    d.line([15, 16, 9, 22], fill=IRON_HI)
    d.rectangle([14, 12, 17, 14], fill=BRASS, outline=INK)
    box(d, 9, 24, 22, 40, GLOW_HI)
    for y in range(25, 40):
        d.line([10, y, 21, y], fill=mix(GLOW_HI, GLOW, min(1, abs(y - 32) / 8)))
    for x in (13, 18):                                                                         # the cage's bars
        d.line([x, 25, x, 39], fill=IRON)
    d.line([10, 32, 21, 32], fill=IRON)
    d.rectangle([9, 24, 22, 40], outline=INK)
    box(d, 7, 40, 24, 43, IRON)
    d.line([8, 41, 23, 41], fill=IRON_HI)
    d.polygon([(12, 44), (19, 44), (16, 48), (15, 48)], fill=IRON, outline=INK)
    d.line([15, 49, 15, 55], fill=VERM)                                                        # the tassel
    d.line([16, 49, 16, 55], fill=VERM_DK)
    d.point((15, 56), fill=GOLD)
    return im


# ---- on the back wall ---------------------------------------------------------------

def kyozo():
    """Shelves of sutra chests: tied with cord, a paper label on each."""
    rnd = random.Random(7)
    w = 2 * C
    im, d = new(w, 2 * C)
    box(d, 2, 8, w - 3, 61, LQ_DK)
    bar(d, 0, 5, w - 1, 9, WOOD, WOOD_HI, WOOD_DK)                                            # the cornice
    for y in (26, 43, 60):                                                                     # the shelves
        bar(d, 2, y, w - 3, y + 3, WOOD, WOOD_HI, WOOD_DK)
    post(d, 2, 9, 4, 61, WOOD, WOOD_HI, WOOD_DK)
    post(d, w - 5, 9, w - 3, 61, WOOD, WOOD_HI, WOOD_DK)
    for y in (26, 43, 60):
        x = 6
        while x < w - 14:
            cw, ch = rnd.choice((9, 10, 12)), rnd.choice((9, 11, 13))
            if x + cw > w - 6:
                break
            col = rnd.choice(((132, 92, 62), (112, 76, 58), (150, 108, 70)))
            box(d, x, y - ch, x + cw, y - 1, col)
            d.line([x + 1, y - ch + 1, x + cw - 1, y - ch + 1], fill=mix(col, WHITE, 0.25))
            d.line([x + cw // 2, y - ch, x + cw // 2, y - 1], fill=VERM)                      # the cord
            d.line([x + 1, y - ch // 2 - 1, x + cw - 1, y - ch // 2 - 1], fill=VERM_DK)
            d.rectangle([x + 2, y - ch + 3, x + 4, y - 3], fill=WHITE)                        # the label
            d.point((x + 3, y - ch + 4), fill=INK)
            d.point((x + 3, y - ch + 6), fill=INK)
            x += cw + 2
        if x < w - 9:                                                                          # scrolls laid on their side
            for i in range(3):
                d.rectangle([x, y - 4 - i * 3, w - 7, y - 2 - i * 3], fill=PLASTER_HI, outline=INK)
                d.point((x + 1, y - 3 - i * 3), fill=PURPLE)
    return im


def senbutsu():
    """A wall of tiny gilt Buddhas, row on row, behind a gilt frame."""
    rnd = random.Random(11)
    w = 2 * C
    im, d = new(w, 2 * C)
    box(d, 2, 5, w - 3, 59, VERM_DK)
    d.rectangle([4, 7, w - 5, 57], fill=(70, 24, 36))
    for row, y in enumerate(range(9, 54, 7)):
        for x in range(6 + (3 if row % 2 else 0), w - 9, 6):
            col = rnd.choice((GOLD, GOLD, GOLD_HI, GOLD_DK))
            d.point((x + 1, y), fill=col)                                                      # head
            d.rectangle([x, y + 1, x + 2, y + 3], fill=col)                                    # robes
            d.point((x + 1, y + 2), fill=mix(col, INK, 0.45))
            d.line([x - 1, y + 4, x + 3, y + 4], fill=GOLD_DK)                                 # its shelf
    d.rectangle([2, 5, w - 3, 59], outline=INK)
    d.rectangle([3, 6, w - 4, 58], outline=GOLD_DK)
    for x, y in ((3, 6), (w - 6, 6), (3, 56), (w - 6, 56)):
        stud(d, x, y)
    bar(d, 0, 58, w - 1, 62, WOOD, WOOD_HI, WOOD_DK)                                           # the ledge under it
    for x in (14, w - 17):                                                                     # a candle each end of it
        d.rectangle([x, 52, x + 1, 57], fill=WHITE)
        d.point((x, 50), fill=FLAME)
        d.point((x, 51), fill=FLAME_HI)
    return im


def window():
    """A slatted window on the top storey: green slats, tiled roofs far below."""
    w = 3 * C
    im, d = new(w, 2 * C)
    x0, y0, x1, y1 = 10, 12, w - 11, 46
    for y in range(y0, y1 + 1):
        d.line([x0, y, x1, y], fill=mix(SKY, SKY_LO, (y - y0) / (y1 - y0)))
    d.polygon([(x0, 40), (26, 34), (40, 39), (52, 33), (66, 38), (x1, 35), (x1, y1), (x0, y1)], fill=(118, 132, 150))   # roofs
    d.line([(x0, 40), (26, 34), (40, 39), (52, 33), (66, 38), (x1, 35)], fill=(90, 102, 124))
    d.polygon([(x0, y1), (x0, 44), (34, 41), (60, 44), (x1, 42), (x1, y1)], fill=(150, 104, 96))
    d.ellipse([58, 16, 70, 21], fill=WHITE)                                                    # a cloud
    d.ellipse([20, 20, 36, 24], fill=WHITE)
    for x in range(x0 + 2, x1 - 1, 5):                                                         # the slats
        d.rectangle([x, y0, x + 2, y1], fill=SLAT)
        d.line([x, y0, x, y1], fill=SLAT_HI)
    box(d, x0 - 4, y0 - 4, x1 + 4, y0 - 1, VERM)                                               # the frame
    d.line([x0 - 3, y0 - 3, x1 + 3, y0 - 3], fill=VERM_HI)
    box(d, x0 - 4, y1 + 1, x1 + 4, y1 + 5, VERM)
    d.line([x0 - 3, y1 + 2, x1 + 3, y1 + 2], fill=VERM_HI)
    post(d, x0 - 4, y0 - 4, x0 - 1, y1 + 5, VERM, VERM_HI, VERM_DK)
    post(d, x1 + 1, y0 - 4, x1 + 4, y1 + 5, VERM, VERM_HI, VERM_DK)
    for x in (x0 - 3, x1 + 1):
        stud(d, x, y0 - 4)
        stud(d, x, y1 + 2)
    bar(d, x0 - 7, y1 + 6, x1 + 7, y1 + 10, WOOD, WOOD_HI, WOOD_DK)                            # the sill
    return im


def sprites():
    return {
        'pagoda-in-board-a': board(0), 'pagoda-in-board-b': board(1),
        'pagoda-in-hatch': hatch,
        'pagoda-in-wall-head': wall_head, 'pagoda-in-wall-head-w': wall_head_w, 'pagoda-in-wall-head-e': mirrored(wall_head_w),
        'pagoda-in-wall': wall, 'pagoda-in-wall-w': wall_w, 'pagoda-in-wall-e': mirrored(wall_w),
        'pagoda-in-side-w': side_w, 'pagoda-in-side-e': mirrored(side_w),
        'pagoda-in-edge': edge, 'pagoda-in-edge-w': edge_w, 'pagoda-in-edge-e': mirrored(edge_w),
        'pagoda-in-base': base, 'pagoda-in-base-w': base_w, 'pagoda-in-base-e': mirrored(base_w),
        'pagoda-in-threshold': threshold,
        'pagoda-in-doorlight': doorlight,
        'pagoda-in-eave-w': eave_w, 'pagoda-in-eave-e': mirrored(eave_w),
        'pagoda-in-roof': roof,
        'pagoda-in-stair': stair,
        'pagoda-in-pillar': pillar,
        'pagoda-in-shumidan': shumidan,
        'pagoda-in-saisen': saisen,
        'pagoda-in-shokudai': shokudai, 'pagoda-in-toro-hang': toro_hang,
        'pagoda-in-kyozo': kyozo, 'pagoda-in-senbutsu': senbutsu,
        'pagoda-in-window': window,
    }


# The hung lantern is a Tops piece under four rows tall: lifted in front of
# whatever taller thing stands behind it. The light through the door lies on
# the floor.
DEPTH_BIAS = {'pagoda-in-toro-hang': 10, 'pagoda-in-doorlight': -40}

# Worth looking up at from the top storey: sprite family -> rows of building
# below the sprite (config game.lookUp.sprites, see "Looking up at landmarks"
# in hud-input-touch.md). The two rows are the top storey's back wall, so the
# reach starts on that storey's floor and has faded out by the storey below.
LOOK_UP = {'pagoda-in-roof': 2}


def main():
    built = {}
    for name, fn in sprites().items():
        im = fn()
        built[name] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        path = f'assets/sprites/{key}.png'
        if not (os.path.exists(path) and Image.open(path).convert('RGBA').tobytes() == im.tobytes()):
            im.save(path)
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if name in DEPTH_BIAS:
            cfg['spriteMetadata'][key]['depthBias'] = DEPTH_BIAS[name]
        cfg.setdefault('tileNames', {})[key] = name
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
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
