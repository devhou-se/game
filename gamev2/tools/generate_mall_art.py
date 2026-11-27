#!/usr/bin/env python3
"""generate_mall_art.py — everything inside Canal City's atrium in Fukuoka
(issue #217).

In the manner of tools/generate_pub_art.py, whose frame (the side walls, the
front wall, the doorway, the light through it), drawing helpers and register()
it imports: shaded pixel art with a 1px ink outline, drawn at half size (32px a
cell) and pixel-doubled. Nothing is random between runs and the only text (the
shops' signs) is set in the game's own font, so a re-run is byte-identical on
the same machine.

The room is the inside of `canal-city`: cream stone and terracotta, the canal
through the middle of the floor, the galleries stacked over the shops. The
canal is the one tools/generate_fukuoka_town_art.py draws for the street
outside (`fukuoka-canal*`): the same teal water, cream coping with its
terracotta band, terracotta brick quay. All sprites are `mall-in-<piece>`:
  floor-a / floor-b       pale stone paving (a: a terracotta diamond set in it)
  side-w / side-e         the side walls seen along their length: the galleries' ends
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-pier               1x5 a pier of the back wall, banded where the galleries meet it
  front-fashion / -toys / -okonomiyaki / -cafe / -ramen
                          4x5 a shopfront under two gallery levels: curved terracotta
                          balconies, glass rails, small lit fronts behind (bump the shop)
  canal-n-a / -n-b        the north quay: coping, the brick wall under it, water
  canal-a / -b            water
  canal-s-a / -s-b        water, the south quay's coping
  bridge                  2x3 a timber deck between terracotta rails, lying flat over the
                          canal (walked on: depthBias -200, as dazaifu-bridge)
  fountain                4x3 the canal with the fountain's basin in it, the jets at rest
                          (bump it)
  palm                    1x2 a palm in a terracotta tub

Run from gamev2/:  python3 tools/generate_mall_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames,
and the back wall's pieces in game.lookUp.sprites (issue #258).
"""
import json
import random
import sys

from generate_pub_art import (C, INK, WHITE, CREAM, CREAM_SH, GLOW, GLOW_HI, BRASS, BRASS_HI, BRASS_DK,
                              STEEL, STEEL_HI, STEEL_DK, BLACK, new, box, text, mix, bar, post, shadow, latin,
                              wall_side, wall_front, threshold, doorlight, register)

# the canal's colours are tools/generate_fukuoka_town_art.py's, so the water inside is the water outside
TEAL, TEAL_HI, TEAL_LO = (63, 159, 176), (143, 219, 224), (47, 127, 150)
TERRA, TERRA_HI, TERRA_LO = (200, 103, 74), (224, 138, 102), (156, 74, 58)
COPING, COPING_HI, COPING_SH = (241, 226, 196), (255, 246, 224), (205, 184, 147)
QUAY_LINE, WATER_SHADE = (122, 58, 48), (37, 106, 128)
PAVE, PAVE_ALT, PAVE_HI, PAVE_DK = (234, 226, 210), (226, 217, 200), (246, 241, 230), (204, 193, 174)
DECK, DECK_HI, DECK_DK = (214, 166, 104), (238, 198, 134), (164, 116, 76)
LEAF, LEAF_HI, LEAF_DK = (64, 150, 84), (120, 196, 104), (38, 104, 78)
TRUNK, TRUNK_DK = (150, 110, 78), (104, 74, 62)
PANE, PANE_HI = (176, 214, 226), (224, 240, 244)                  # the galleries' glass rails

# the frame, in cream stone and terracotta: tools/generate_pub_art.py draws it
ATRIUM = {'head': COPING, 'head_hi': COPING_HI, 'head_dk': COPING_SH, 'face': TERRA, 'face_hi': TERRA_HI, 'face_dk': TERRA_LO,
          'trim': COPING_HI, 'post': COPING, 'post_hi': COPING_HI, 'post_dk': COPING_SH, 'sill': COPING_SH}


# ---- the floor ----------------------------------------------------------------------------

def paving(inlay):
    """Pale stone, four slabs a cell; `inlay` sets a terracotta diamond where they meet."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=PAVE)
        d.rectangle([0, 0, 15, 15], fill=PAVE_ALT)
        d.rectangle([16, 16, 31, 31], fill=PAVE_ALT)
        for v in (0, 16):
            d.line([v, 0, v, 31], fill=PAVE_DK)
            d.line([0, v, 31, v], fill=PAVE_DK)
        for v in (1, 17):
            d.line([v, v, v + 13, v], fill=PAVE_HI)
            d.line([v, v, v, v + 13], fill=PAVE_HI)
            d.line([v + 15 if v == 1 else 1, v, (v + 28) if v == 1 else 14, v], fill=PAVE_HI)
        if inlay:
            d.polygon([(16, 11), (21, 16), (16, 21), (11, 16)], fill=TERRA, outline=TERRA_LO)
            d.line([14, 15, 16, 13], fill=TERRA_HI)
        return im
    return draw


# ---- the canal ----------------------------------------------------------------------------
#
# Three rows of cells: the north quay (its coping, then the brick wall you look
# down on, then water), a row of water, and the south quay (water, then the
# coping: its wall faces away). Drawn into any image at any x, so the fountain,
# which stands in the canal, carries the same quays and water behind it.

def _coping(d, x0, x1, y):
    """A quay's coping, 10px deep from `y`: cream stone, the terracotta band through it."""
    d.rectangle([x0, y, x1, y + 9], fill=COPING)
    d.line([x0, y, x1, y], fill=COPING_HI)
    d.rectangle([x0, y + 3, x1, y + 5], fill=TERRA)
    d.line([x0, y + 3, x1, y + 3], fill=TERRA_HI)
    d.line([x0, y + 8, x1, y + 8], fill=COPING_SH)
    d.line([x0, y + 9, x1, y + 9], fill=COPING_SH)
    for x in range(x0, x1 + 1):
        if x % 16 == 0:                                             # a joint every half cell
            d.line([x, y, x, y + 2], fill=COPING_SH)
            d.line([x, y + 6, x, y + 9], fill=COPING_SH)


def _ripples(d, x0, x1, y0, y1, seed):
    """Short lighter and darker dashes on the water; the same for the same seed."""
    rnd = random.Random(seed)
    for _ in range(max(2, (x1 - x0 + 1) * (y1 - y0 + 1) // 110)):
        x, y, n = rnd.randrange(x0, x1 - 5), rnd.randrange(y0, y1 + 1), rnd.choice((3, 4, 5))
        d.line([x, y, x + n, y], fill=TEAL_HI if rnd.random() < 0.6 else TEAL_LO)


def _canal(d, x0, w, row, seed):
    """One row of the canal, `w` px wide from `x0`: 'n', 'mid' or 's'."""
    x1, y = x0 + w - 1, {'n': 0, 'mid': C, 's': 2 * C}[row] if w > C else 0
    if row == 'n':
        _coping(d, x0, x1, y)
        d.line([x0, y + 10, x1, y + 10], fill=QUAY_LINE)
        d.rectangle([x0, y + 11, x1, y + 22], fill=TERRA)           # the quay wall: brick, three courses
        for n, cy in enumerate(range(y + 11, y + 23, 4)):
            d.line([x0, cy + 3, x1, cy + 3], fill=TERRA_LO)
            for x in range(x0, x1 + 1):
                if (x + (4 if n % 2 else 0)) % 8 == 0:
                    d.line([x, cy, x, cy + 2], fill=TERRA_LO)
            d.line([x0, cy, x1, cy], fill=TERRA_HI if n == 0 else TERRA)
        d.line([x0, y + 23, x1, y + 23], fill=TEAL_LO)              # the waterline
        d.rectangle([x0, y + 24, x1, y + 27], fill=mix(TEAL, TERRA_LO, 0.28))   # the wall, in the water
        d.rectangle([x0, y + 28, x1, y + 31], fill=TEAL)
        for x in range(x0, x1 + 1, 2):
            d.point((x + (y + x // 2) % 2, y + 28), fill=mix(TEAL, TERRA_LO, 0.28))
        _ripples(d, x0, x1, y + 29, y + 31, seed)
    elif row == 'mid':
        d.rectangle([x0, y, x1, y + 31], fill=TEAL)
        _ripples(d, x0, x1, y + 1, y + 30, seed + 1)
    else:
        d.rectangle([x0, y, x1, y + 20], fill=TEAL)
        _ripples(d, x0, x1, y + 1, y + 17, seed + 2)
        d.line([x0, y + 20, x1, y + 20], fill=TEAL_LO)
        d.line([x0, y + 21, x1, y + 21], fill=QUAY_LINE)            # the coping's lip, over the water
        _coping(d, x0, x1, y + 22)


def canal(row, seed):
    def draw():
        im, d = new(C, C)
        _canal(d, 0, C, row, seed)
        return im
    return draw


def bridge():
    """A footbridge over the canal, 2x3, lying flat: honey boards laid across
    between terracotta rails with cream caps, a stone step at each bank."""
    W, H = 2 * C, 3 * C
    im, d = new(W, H)
    d.rectangle([62, 12, 63, 84], fill=WATER_SHADE)                 # its shadow on the water, to the east
    d.rectangle([4, 0, 59, H - 1], fill=DECK)
    for n, y in enumerate(range(4, H - 4, 4)):                      # the boards; the crown of the deck catches the light
        t = 1 - abs(y - 46) / 46
        d.rectangle([8, y, 55, y + 3], fill=mix(DECK, DECK_HI, 0.55 * t) if n % 2 else mix(DECK_DK, DECK, 0.5 + 0.5 * t))
        d.line([8, y + 3, 55, y + 3], fill=DECK_DK)
        for x in (12 + (n % 3) * 9, 44 - (n % 2) * 11):             # nail heads
            d.point((x, y + 1), fill=DECK_DK)
    for y0 in (0, H - 4):                                           # the steps onto it
        d.rectangle([4, y0, 59, y0 + 3], fill=COPING)
        d.line([4, y0, 59, y0], fill=COPING_HI)
        d.line([4, y0 + 3, 59, y0 + 3], fill=COPING_SH)
    for x0 in (2, 56):                                              # the rails
        d.rectangle([x0, 0, x0 + 5, H - 1], fill=TERRA, outline=INK)
        d.line([x0 + 1, 1, x0 + 1, H - 2], fill=TERRA_HI)
        d.line([x0 + 4, 1, x0 + 4, H - 2], fill=TERRA_LO)
        for y in (0, 30, 62, H - 6):                                # their posts' caps
            d.rectangle([x0 - 1, y, x0 + 6, y + 5], fill=COPING, outline=INK)
            d.line([x0, y + 1, x0 + 5, y + 1], fill=COPING_HI)
            d.line([x0, y + 4, x0 + 5, y + 4], fill=COPING_SH)
    return im


def _jet(d, x, foot, h):
    """A jet at rest: a short white column, its head falling back, a ring round its foot."""
    d.ellipse([x - 5, foot - 2, x + 6, foot + 2], outline=TEAL_HI)
    d.rectangle([x, foot - h, x + 1, foot], fill=WHITE)
    d.line([x - 1, foot - h + 2, x - 1, foot - h + 4], fill=PANE_HI)
    d.line([x + 2, foot - h + 2, x + 2, foot - h + 4], fill=PANE_HI)
    d.point((x - 2, foot - h + 5), fill=WHITE)
    d.point((x + 3, foot - h + 5), fill=WHITE)
    d.line([x - 2, foot, x + 3, foot], fill=WHITE)


def fountain():
    """The fountain, 4x3, standing in the canal: the quays and the water run
    on behind it; a round stone basin, a raised bowl in its middle, the jets
    resting between shows."""
    W, H = 4 * C, 3 * C
    im, d = new(W, H)
    for row in ('n', 'mid', 's'):
        _canal(d, 0, W, row, 2177)
    d.ellipse([14, 30, 113, 80], fill=WATER_SHADE)                  # the basin's shadow on the canal
    d.ellipse([12, 26, 115, 76], fill=COPING, outline=INK)          # the basin: a stone ring
    d.arc([14, 28, 113, 74], 180, 330, fill=COPING_HI)
    d.arc([13, 27, 114, 75], 20, 160, fill=COPING_SH, width=2)
    d.ellipse([19, 31, 108, 69], fill=TERRA, outline=INK)           # its band
    d.ellipse([22, 33, 105, 67], fill=mix(TEAL, TEAL_HI, 0.45), outline=TEAL_LO)    # the pool, shallow and bright
    d.arc([26, 36, 101, 65], 200, 320, fill=TEAL_HI)
    _ripples(d, 34, 94, 40, 62, 2178)
    d.ellipse([47, 42, 80, 60], fill=COPING, outline=INK)           # the bowl in the middle
    d.arc([49, 43, 78, 58], 180, 320, fill=COPING_HI)
    d.ellipse([52, 45, 75, 56], fill=TEAL_HI, outline=COPING_SH)
    _jet(d, 63, 50, 18)
    for x, foot, h in ((33, 50, 8), (94, 50, 8), (45, 62, 7), (82, 62, 7), (40, 40, 6), (87, 40, 6)):
        _jet(d, x, foot, h)
    return im


def palm():
    """A palm in a terracotta tub, 1x2: the tub is in the way, the fronds are walked behind."""
    im, d = new(C, 2 * C)
    shadow(d, 3, 54, 28, 63, 70)
    for n, y in enumerate(range(22, 48, 4)):                        # the trunk, ringed
        d.rectangle([14, y, 17, y + 3], fill=TRUNK if n % 2 else mix(TRUNK, TRUNK_DK, 0.4))
        d.point((14, y), fill=TRUNK_DK)
        d.point((17, y + 3), fill=TRUNK_DK)
    d.line([13, 22, 13, 47], fill=INK)
    d.line([18, 22, 18, 47], fill=INK)
    for pts, col in (                                               # the fronds, the far ones first
        ([(16, 20), (4, 8), (0, 12), (2, 18), (8, 16)], LEAF_DK),
        ([(16, 20), (27, 8), (31, 12), (29, 18), (23, 16)], LEAF_DK),
        ([(16, 20), (9, 3), (14, 2), (17, 8)], LEAF),
        ([(16, 20), (22, 3), (18, 2), (15, 8)], LEAF),
        ([(16, 21), (2, 22), (0, 28), (5, 30), (10, 25)], LEAF),
        ([(16, 21), (29, 22), (31, 28), (26, 30), (21, 25)], LEAF),
        ([(16, 21), (9, 26), (8, 34), (12, 33), (15, 26)], LEAF_HI),
        ([(16, 21), (22, 26), (23, 34), (19, 33), (16, 26)], LEAF_HI),
    ):
        d.polygon(pts, fill=col, outline=INK)
    for a, b in (((16, 20), (5, 11)), ((16, 20), (26, 11)), ((16, 21), (4, 26)), ((16, 21), (27, 26)), ((16, 19), (12, 5)), ((16, 19), (20, 5))):
        d.line([a, b], fill=LEAF_DK)                                # their ribs
    d.ellipse([13, 17, 18, 22], fill=TRUNK_DK, outline=INK)         # the crown
    d.polygon([(6, 46), (25, 46), (23, 61), (8, 61)], fill=TERRA, outline=INK)   # the tub
    d.line([8, 49, 9, 60], fill=TERRA_HI)
    d.line([22, 49, 21, 60], fill=TERRA_LO)
    d.rectangle([5, 44, 26, 47], fill=COPING, outline=INK)          # its rim
    d.line([6, 45, 25, 45], fill=COPING_HI)
    d.line([10, 54, 21, 54], fill=TERRA_LO)
    return im


# ---- the back wall: shops under two gallery levels ------------------------------------------
#
# Every piece is five cells tall. The top two are the galleries, one above the
# other, each a cell tall: small lit fronts in the back of it, a glass rail, the
# terracotta balcony with its cream stripe. In a shopfront's bay the balcony
# bows out towards you (down the screen); at a pier it is flat, so they join.
# The bottom three are the ground floor.

GALLERY = (1, 33)                 # where each gallery level starts, from the piece's top
SOFFIT, PLINTH = 64, 150          # the ground floor: from under the lower balcony to the paving
BACK, BACK_SH = (214, 190, 166), (170, 140, 128)                  # the back of a gallery, and the shade under its ceiling
UNITS = ((GLOW, (70, 110, 170)), (GLOW_HI, (200, 70, 80)), ((255, 232, 170), (62, 130, 96)), (GLOW, (226, 150, 60)))


def _level(d, w, y0, bow, shift=0):
    """One gallery level `w` px wide from y0; bow(x): how far the balcony bows out at column x."""
    d.rectangle([0, y0, w - 1, y0 + 31], fill=BACK)
    d.rectangle([0, y0, w - 1, y0 + 2], fill=BACK_SH)               # under the ceiling
    for n, x in enumerate(range(3, w - 12, 16)):                    # the little shops up there, lit
        light, sign = UNITS[(n + shift) % len(UNITS)]
        d.rectangle([x, y0 + 4, x + 11, y0 + 6], fill=sign)
        d.rectangle([x, y0 + 7, x + 11, y0 + 16], fill=light)
        d.rectangle([x, y0 + 4, x + 11, y0 + 16], outline=TERRA_LO)
        d.line([x + 6, y0 + 7, x + 6, y0 + 16], fill=TERRA_LO)
        d.line([x + 1, y0 + 14, x + 5, y0 + 14], fill=mix(light, TERRA, 0.4))     # something in the window
        d.line([x + 8, y0 + 12, x + 9, y0 + 12], fill=mix(light, sign, 0.6))
    for x in range(w):
        b = bow(x)
        d.line([x, y0 + 12 + b, x, y0 + 19 + b], fill=PANE if (x // 2 + b) % 5 else PANE_HI)   # the glass rail
        d.point((x, y0 + 11 + b), fill=STEEL_HI)                    # its handrail
        d.point((x, y0 + 12 + b), fill=STEEL_DK)
        if x % 16 == 0:
            d.line([x, y0 + 12 + b, x, y0 + 19 + b], fill=STEEL_DK)
        d.line([x, y0 + 20 + b, x, y0 + 27 + b], fill=TERRA)        # the balcony
        d.point((x, y0 + 20 + b), fill=INK)
        d.point((x, y0 + 21 + b), fill=TERRA_HI)
        d.line([x, y0 + 23 + b, x, y0 + 24 + b], fill=COPING)       # its stripe
        d.point((x, y0 + 27 + b), fill=TERRA_LO)
        d.point((x, y0 + 28 + b), fill=INK)
        if y0 + 29 + b <= y0 + 31:
            d.line([x, y0 + 29 + b, x, y0 + 31], fill=BACK_SH)      # the shade under it


def _cornice(d, w):
    d.rectangle([0, 0, w - 1, 3], fill=COPING)
    d.line([0, 0, w - 1, 0], fill=INK)
    d.line([0, 1, w - 1, 1], fill=COPING_HI)
    d.line([0, 3, w - 1, 3], fill=TERRA)
    d.line([0, 4, w - 1, 4], fill=INK)


def _plinth(d, w):
    d.rectangle([0, PLINTH, w - 1, 159], fill=COPING_SH)
    d.line([0, PLINTH, w - 1, PLINTH], fill=INK)
    d.line([0, PLINTH + 1, w - 1, PLINTH + 1], fill=COPING)
    d.line([0, 159, w - 1, 159], fill=INK)


def wall_pier():
    """A pier between two shops, the full height of the wall: cream stone,
    banded in terracotta where each balcony meets it, a lamp at head height."""
    im, d = new(C, 5 * C)
    flat = lambda x: 0
    for n, y0 in enumerate(GALLERY):
        _level(d, C, y0, flat, n)
    d.rectangle([0, SOFFIT, C - 1, PLINTH], fill=BACK_SH)           # the shops' flanks, in its shade
    d.line([0, SOFFIT, C - 1, SOFFIT], fill=INK)
    post(d, 5, 5, 26, PLINTH, COPING, COPING_HI, COPING_SH)         # the pier itself, in front of the galleries
    d.rectangle([8, 6, 10, PLINTH - 1], fill=mix(COPING, COPING_HI, 0.6))
    for y0 in GALLERY:                                              # the balconies' bands run round it
        d.rectangle([5, y0 + 20, 26, y0 + 28], fill=TERRA, outline=INK)
        d.line([6, y0 + 21, 25, y0 + 21], fill=TERRA_HI)
        d.rectangle([6, y0 + 23, 25, y0 + 24], fill=COPING)
        d.line([6, y0 + 27, 25, y0 + 27], fill=TERRA_LO)
    d.rectangle([3, SOFFIT, 28, SOFFIT + 5], fill=COPING, outline=INK)     # its capital
    d.line([4, SOFFIT + 1, 27, SOFFIT + 1], fill=COPING_HI)
    d.rectangle([12, 92, 19, 95], fill=BRASS_DK, outline=INK)       # the lamp: a bracket, a glass globe
    d.ellipse([10, 94, 21, 107], fill=GLOW_HI, outline=INK)
    d.arc([12, 96, 19, 105], 180, 280, fill=WHITE)
    d.line([13, 108, 18, 108], fill=BRASS)
    for y in range(116, PLINTH - 4, 12):                            # the stone's joints
        d.line([6, y, 25, y], fill=COPING_SH)
    _cornice(d, C)
    _plinth(d, C)
    d.rectangle([3, PLINTH - 4, 28, PLINTH], fill=COPING, outline=INK)     # its foot
    d.line([4, PLINTH - 3, 27, PLINTH - 3], fill=COPING_HI)
    return im


# ---- what is in each shop's windows: (d, x0, y0, x1, y1) is the glass ------------------------

def _mannequin(d, cx, foot, coat, hat=None):
    dk, hi = mix(coat, BLACK, 0.35), mix(coat, WHITE, 0.3)
    d.line([cx, foot - 8, cx, foot - 1], fill=STEEL_DK)             # the stand
    d.line([cx - 4, foot, cx + 4, foot], fill=STEEL_DK)
    d.polygon([(cx - 6, foot - 34), (cx + 6, foot - 34), (cx + 9, foot - 9), (cx - 9, foot - 9)], fill=coat, outline=INK)
    d.line([cx - 5, foot - 32, cx - 7, foot - 11], fill=hi)
    d.line([cx, foot - 31, cx, foot - 10], fill=dk)                 # where it buttons
    for y in (foot - 27, foot - 21, foot - 15):
        d.point((cx + 2, y), fill=BRASS_HI)
    d.polygon([(cx - 5, foot - 34), (cx, foot - 28), (cx + 5, foot - 34)], fill=dk)   # the collar
    d.line([cx - 9, foot - 30, cx - 11, foot - 14], fill=coat, width=3)               # the sleeves
    d.line([cx + 9, foot - 30, cx + 11, foot - 14], fill=dk, width=3)
    d.ellipse([cx - 3, foot - 42, cx + 3, foot - 35], fill=CREAM, outline=INK)        # a head with no face
    if hat:
        d.rectangle([cx - 4, foot - 44, cx + 4, foot - 41], fill=hat, outline=INK)


def _coats(d, x0, y0, x1, y1, side):
    foot = y1 - 3
    d.rectangle([x0, y1 - 2, x1, y1], fill=(196, 168, 150))         # the window's floor
    if side == 'w':
        _mannequin(d, x0 + 11, foot, (198, 148, 92))
        _mannequin(d, x0 + 31, foot, (186, 58, 62), hat=(60, 60, 84))
    else:
        _mannequin(d, x0 + 13, foot, (62, 78, 128), hat=(186, 58, 62))
        for n, col in enumerate(((226, 150, 60), (62, 130, 96), (186, 58, 62), (240, 230, 206))):   # scarves, folded
            d.rectangle([x0 + 27, foot - 8 - n * 6, x0 + 40, foot - 3 - n * 6], fill=col, outline=INK)
        d.rectangle([x0 + 26, y0 + 4, x0 + 41, y0 + 12], fill=(214, 64, 72), outline=INK)          # a card: so much off
        d.line([x0 + 29, y0 + 7, x0 + 38, y0 + 7], fill=WHITE)
        d.line([x0 + 29, y0 + 9, x0 + 35, y0 + 9], fill=WHITE)


def _toys(d, x0, y0, x1, y1, side):
    foot = y1 - 1
    if side == 'w':                                                 # capsule machines, two high
        for row in range(2):
            for n in range(4):
                x, y = x0 + 2 + n * 10, foot - 22 - row * 24
                col = ((226, 70, 80), (70, 130, 200), (240, 190, 60), (90, 170, 110))[(n + row) % 4]
                d.rectangle([x, y, x + 8, y + 22], fill=WHITE, outline=INK)
                d.rectangle([x + 1, y + 1, x + 7, y + 10], fill=PANE_HI)
                for k, (cx, cy) in enumerate(((2, 4), (5, 3), (3, 7), (6, 8))):      # the capsules
                    d.rectangle([x + cx, y + cy, x + cx + 1, y + cy + 1], fill=((226, 70, 80), (240, 190, 60), (70, 130, 200), (90, 170, 110))[(k + n) % 4])
                d.rectangle([x + 1, y + 12, x + 7, y + 20], fill=col)
                d.rectangle([x + 3, y + 14, x + 5, y + 16], fill=STEEL_HI, outline=STEEL_DK)   # the crank
                d.line([x + 2, y + 19, x + 6, y + 19], fill=BLACK)
    else:                                                           # the big one, and the ones that are for sale
        d.rectangle([x0, y1 - 2, x1, y1], fill=(196, 168, 150))
        bear, bear_dk = (176, 124, 84), (128, 86, 66)
        cx = x0 + 15
        d.ellipse([cx - 13, foot - 26, cx + 13, foot - 1], fill=bear, outline=INK)           # its body
        d.ellipse([cx - 7, foot - 18, cx + 7, foot - 4], fill=(226, 196, 150))
        for ex in (cx - 12, cx + 6):                                                         # ears, then the head
            d.ellipse([ex, foot - 46, ex + 6, foot - 40], fill=bear, outline=INK)
        d.ellipse([cx - 11, foot - 43, cx + 11, foot - 23], fill=bear, outline=INK)
        d.ellipse([cx - 4, foot - 33, cx + 4, foot - 26], fill=(226, 196, 150))
        d.point((cx - 4, foot - 35), fill=INK)
        d.point((cx + 4, foot - 35), fill=INK)
        d.line([cx - 1, foot - 31, cx + 1, foot - 31], fill=INK)
        d.arc([cx - 12, foot - 42, cx + 2, foot - 26], 180, 260, fill=mix(bear, WHITE, 0.3))
        for fx in (cx - 15, cx + 8):                                                         # its feet
            d.ellipse([fx, foot - 8, fx + 7, foot], fill=bear_dk, outline=INK)
        d.rectangle([cx - 5, foot - 23, cx + 5, foot - 21], fill=(214, 64, 72))              # a ribbon
        for n, col in enumerate(((244, 160, 180), (250, 214, 90), (150, 200, 230))):         # small ones on a shelf
            x, y = x0 + 31, foot - 12 - n * 15
            d.line([x - 1, y + 11, x1 - 1, y + 11], fill=TERRA_LO)
            d.ellipse([x + 1, y + 2, x + 9, y + 10], fill=col, outline=INK)
            d.rectangle([x + 2, y - 1, x + 3, y + 2], fill=col, outline=INK)
            d.rectangle([x + 7, y - 1, x + 8, y + 2], fill=col, outline=INK)
            d.point((x + 4, y + 5), fill=INK)
            d.point((x + 7, y + 5), fill=INK)


def _disc(d, x, y):
    """An okonomiyaki on the plate: sauce, a lattice of mayonnaise, green laver."""
    d.ellipse([x, y, x + 13, y + 7], fill=(150, 86, 50), outline=INK)
    d.ellipse([x + 2, y + 1, x + 11, y + 5], fill=(110, 58, 44))
    for k in range(3):
        d.line([x + 3 + k * 3, y + 2, x + 5 + k * 3, y + 5], fill=CREAM)
    d.point((x + 4, y + 4), fill=LEAF_HI)
    d.point((x + 9, y + 2), fill=LEAF_HI)


def _steam(d, x, y):
    for k in range(3):
        d.point((x + (k % 2), y - k * 2), fill=WHITE)
        d.point((x + 1 - (k % 2), y - k * 2 - 1), fill=PANE_HI)


def _griddle(d, x0, y0, x1, y1, side):
    d.rectangle([x0, y1 - 20, x1, y1], fill=(96, 60, 48))           # the counter's front
    for x in range(x0 + 3, x1, 6):
        d.line([x, y1 - 12, x, y1 - 1], fill=(64, 42, 44))
    if side == 'w':                                                 # the plate, and what is on it
        d.rectangle([x0 + 1, y1 - 24, x1 - 1, y1 - 12], fill=STEEL_DK, outline=INK)
        d.line([x0 + 2, y1 - 23, x1 - 2, y1 - 23], fill=STEEL_HI)
        d.rectangle([x0 + 3, y1 - 21, x1 - 3, y1 - 14], fill=(66, 68, 84))
        for x in (x0 + 4, x0 + 23):
            _disc(d, x, y1 - 22)
            _steam(d, x + 6, y1 - 26)
        d.polygon([(x0 + 18, y1 - 32), (x0 + 22, y1 - 32), (x0 + 21, y1 - 22), (x0 + 19, y1 - 22)], fill=STEEL_HI, outline=INK)   # a spatula
        d.rectangle([x0 + 19, y1 - 40, x0 + 21, y1 - 32], fill=(96, 60, 48))
        d.ellipse([x0 + 12, y0 + 12, x0 + 22, y0 + 22], fill=CREAM, outline=INK)     # whoever is cooking: a head, a cap, an apron
        d.rectangle([x0 + 11, y0 + 8, x0 + 23, y0 + 13], fill=WHITE, outline=INK)
        d.rectangle([x0 + 9, y0 + 22, x0 + 25, y1 - 25], fill=WHITE, outline=INK)
        d.line([x0 + 14, y0 + 17, x0 + 15, y0 + 17], fill=INK)
        d.line([x0 + 19, y0 + 17, x0 + 20, y0 + 17], fill=INK)
    else:                                                           # the queue's stools, the list on the wall
        d.rectangle([x0, y1 - 24, x1, y1 - 21], fill=(150, 92, 62), outline=INK)
        for x in (x0 + 5, x0 + 19, x0 + 33):
            d.ellipse([x, y1 - 14, x + 9, y1 - 9], fill=(186, 58, 62), outline=INK)
            d.line([x + 4, y1 - 8, x + 4, y1 - 1], fill=STEEL_DK)
        for n, x in enumerate(range(x0 + 3, x1 - 6, 8)):
            d.rectangle([x, y0 + 5, x + 5, y0 + 24], fill=CREAM, outline=TERRA_LO)
            for y in range(y0 + 8, y0 + 22, 3 + n % 2):
                d.line([x + 2, y, x + 3, y], fill=INK)


def _pastries(d, x0, y0, x1, y1, side):
    if side == 'w':                                                 # the case, and the machine behind it
        d.rectangle([x0, y1 - 26, x1, y1], fill=PANE_HI, outline=INK)
        for n, y in enumerate((y1 - 14, y1 - 2)):
            d.line([x0 + 1, y, x1 - 1, y], fill=STEEL)
            for k, x in enumerate(range(x0 + 3, x1 - 7, 8)):
                if (k + n) % 2:                                     # a slice of cake
                    d.polygon([(x, y - 1), (x + 6, y - 1), (x + 6, y - 6)], fill=(250, 232, 190), outline=TERRA_LO)
                    d.point((x + 5, y - 7), fill=(214, 64, 72))
                else:                                               # a croissant
                    d.ellipse([x, y - 6, x + 7, y - 1], fill=(226, 160, 80), outline=TERRA_LO)
                    d.line([x + 2, y - 4, x + 5, y - 4], fill=(250, 214, 140))
        d.rectangle([x0 + 4, y0 + 8, x0 + 22, y1 - 27], fill=STEEL, outline=INK)     # the espresso machine
        d.rectangle([x0 + 6, y0 + 10, x0 + 20, y0 + 14], fill=STEEL_HI)
        for x in (x0 + 8, x0 + 16):
            d.line([x, y0 + 16, x, y0 + 20], fill=BLACK)
        d.rectangle([x0 + 28, y1 - 34, x0 + 36, y1 - 27], fill=WHITE, outline=INK)   # cups, stacked
        d.rectangle([x0 + 29, y1 - 40, x0 + 35, y1 - 35], fill=WHITE, outline=INK)
    else:                                                           # a table for two; nobody has got to it yet
        d.rectangle([x0, y1 - 2, x1, y1], fill=(196, 168, 150))
        d.line([x0 + 21, y0 + 1, x0 + 21, y0 + 8], fill=BLACK)
        d.pieslice([x0 + 14, y0 + 6, x0 + 28, y0 + 20], 180, 360, fill=(62, 110, 90), outline=INK)
        d.rectangle([x0 + 18, y0 + 13, x0 + 24, y0 + 15], fill=GLOW_HI)
        d.ellipse([x0 + 9, y1 - 22, x0 + 33, y1 - 15], fill=(240, 230, 206), outline=INK)
        d.line([x0 + 21, y1 - 14, x0 + 21, y1 - 3], fill=STEEL_DK, width=2)
        d.line([x0 + 15, y1 - 2, x0 + 27, y1 - 2], fill=STEEL_DK)
        for x in (x0 + 13, x0 + 25):
            d.rectangle([x, y1 - 24, x + 4, y1 - 20], fill=WHITE, outline=INK)
            _steam(d, x + 2, y1 - 27)
        for x, flip in ((x0 + 1, 1), (x1 - 8, -1)):                 # the chairs
            d.rectangle([x, y1 - 14, x + 7, y1 - 11], fill=(150, 92, 62), outline=INK)
            bx = x if flip == 1 else x + 6
            d.rectangle([bx, y1 - 28, bx + 1, y1 - 11], fill=(150, 92, 62), outline=INK)
            d.line([x + 1, y1 - 10, x + 1, y1 - 3], fill=INK)
            d.line([x + 6, y1 - 10, x + 6, y1 - 3], fill=INK)


def _bowls(d, x0, y0, x1, y1, side):
    if side == 'w':                                                 # the counter: bowls, steam, a lantern
        d.rectangle([x0, y1 - 18, x1, y1], fill=(96, 60, 48))
        d.rectangle([x0, y1 - 20, x1, y1 - 17], fill=(150, 92, 62), outline=INK)
        for x in (x0 + 3, x0 + 17, x0 + 31):
            d.chord([x, y1 - 32, x + 11, y1 - 16], 0, 180, fill=(40, 44, 70), outline=INK)
            d.line([x, y1 - 24, x + 11, y1 - 24], fill=INK)
            d.line([x + 1, y1 - 25, x + 10, y1 - 25], fill=(240, 214, 150))
            d.point((x + 3, y1 - 26), fill=LEAF_HI)
            d.point((x + 7, y1 - 26), fill=(244, 160, 180))
            _steam(d, x + 5, y1 - 29)
        d.line([x0 + 8, y0 + 1, x0 + 8, y0 + 4], fill=BLACK)
        d.rounded_rectangle([x0 + 3, y0 + 4, x0 + 13, y0 + 20], radius=3, fill=(214, 64, 72), outline=INK)
        for y in range(y0 + 7, y0 + 19, 3):
            d.line([x0 + 4, y, x0 + 12, y], fill=(170, 40, 44))
        d.line([x0 + 8, y0 + 8, x0 + 8, y0 + 16], fill=WHITE)
        d.line([x0 + 6, y0 + 11, x0 + 10, y0 + 11], fill=WHITE)
    else:                                                           # the escalator up to the stadium: part of the wall
        d.rectangle([x0, y0, x1, y1], fill=(210, 204, 198))
        d.polygon([(x0 + 2, y1), (x0 + 16, y1), (x1, y0 + 12), (x1, y0 + 1), (x1 - 8, y0 + 1)], fill=STEEL, outline=INK)
        d.polygon([(x0 + 7, y1 - 1), (x0 + 13, y1 - 1), (x1 - 1, y0 + 10), (x1 - 1, y0 + 4)], fill=(66, 68, 84))
        n = 9
        for k in range(n):                                          # its steps
            t = k / (n - 1)
            x, y = x0 + 10 + (x1 - x0 - 12) * t, y1 - 3 - (y1 - y0 - 10) * t
            d.line([x - 2, y, x + 2, y], fill=STEEL_HI)
        d.line([x0 + 2, y1 - 1, x1 - 8, y0 + 2], fill=BLACK, width=2)     # the handrail
        d.rectangle([x0 + 2, y0 + 3, x0 + 19, y0 + 13], fill=(170, 40, 44), outline=INK)    # which way, how far
        text(d, x0 + 4, y0 + 5, '5F', latin(8), CREAM)


# name -> (the sign, its ground and letters, the two awning colours (None: a noren in the sign's colour), the windows)
FRONTS = {
    'fashion':     ('MODE',    (52, 64, 110),  CREAM,       ((52, 64, 110), WHITE),         _coats),
    'toys':        ('TOYS',    (214, 64, 72),  WHITE,       ((250, 204, 70), WHITE),        _toys),
    'okonomiyaki': ('OKONOMI', (96, 60, 48),   CREAM,       None,                           _griddle),
    'cafe':        ('CAFE',    (62, 110, 90),  CREAM,       ((62, 110, 90), (240, 230, 206)), _pastries),
    'ramen':       ('RAMEN',   (170, 40, 44),  (250, 224, 134), None,                       _bowls),
}


def front(name):
    """A shopfront, 4x5: two gallery levels, their balconies bowing out over
    it; under them the sign, an awning or a noren, a window either side of an
    open doorway, the plinth."""
    sign, ground, letters, awning, window = FRONTS[name]

    def draw():
        W = 4 * C
        im, d = new(W, 5 * C)
        bow = lambda x: round(3 * (1 - ((x - 63.5) / 64) ** 2))
        for n, y0 in enumerate(GALLERY):
            _level(d, W, y0, bow, n + len(name))
        _cornice(d, W)
        d.rectangle([0, SOFFIT, W - 1, PLINTH], fill=COPING)        # the shop's face
        d.rectangle([0, SOFFIT, W - 1, SOFFIT + 2], fill=BACK_SH)   # the shade under the balcony
        box(d, 2, SOFFIT + 3, W - 3, SOFFIT + 19, ground)           # the sign
        d.line([3, SOFFIT + 4, W - 4, SOFFIT + 4], fill=mix(ground, WHITE, 0.3))
        d.line([3, SOFFIT + 18, W - 4, SOFFIT + 18], fill=mix(ground, BLACK, 0.3))
        text(d, (W - len(sign) * 8) // 2, SOFFIT + 8, sign, latin(8), letters)
        top = SOFFIT + 20
        for x0, x1, side in ((5, 49, 'w'), (78, 122, 'e')):         # the windows, lit from inside
            d.rectangle([x0, top + 9, x1, PLINTH - 1], fill=(250, 238, 206))
            d.rectangle([x0, top + 9, x1, top + 11], fill=(226, 208, 176))
            window(d, x0 + 1, top + 10, x1 - 1, PLINTH - 2, side)
            d.rectangle([x0, top + 9, x1, PLINTH - 1], outline=INK)
            d.line([x0 + 3, top + 24, x0 + 9, top + 13], fill=WHITE)                # a glint on the glass
        d.rectangle([54, top + 9, 73, PLINTH - 1], fill=(110, 84, 84), outline=INK)   # the doorway, open: the shop beyond
        d.rectangle([56, top + 11, 71, top + 22], fill=(250, 238, 206))
        d.rectangle([55, PLINTH - 12, 72, PLINTH - 1], fill=(150, 118, 108))
        d.line([55, PLINTH - 12, 72, PLINTH - 12], fill=(84, 62, 70))
        if awning:                                                  # an awning, striped, scalloped
            a, b = awning
            for x in range(2, W - 2):
                col = a if (x // 8) % 2 == 0 else b
                d.line([x, top, x, top + 6 + (1 if x % 8 in (2, 3, 4, 5) else 0)], fill=col)
                d.point((x, top + 7 + (1 if x % 8 in (2, 3, 4, 5) else 0)), fill=INK)
            d.line([2, top, W - 3, top], fill=INK)
            d.line([2, top, 2, top + 7], fill=INK)
            d.line([W - 3, top, W - 3, top + 7], fill=INK)
        else:                                                       # a noren over the door, a lantern either side
            d.line([50, top + 8, 77, top + 8], fill=INK)
            for n, x in enumerate(range(52, 76, 8)):
                d.rectangle([x, top + 9, x + 6, top + 22], fill=ground, outline=INK)
                d.ellipse([x + 2, top + 13, x + 4, top + 15], fill=letters)
            for x in (40, 80):
                d.rounded_rectangle([x, top - 1, x + 7, top + 9], radius=2, fill=(214, 64, 72) if name == 'ramen' else CREAM, outline=INK)
                d.line([x + 1, top + 3, x + 6, top + 3], fill=(170, 40, 44) if name == 'ramen' else CREAM_SH)
                d.line([x + 1, top + 6, x + 6, top + 6], fill=(170, 40, 44) if name == 'ramen' else CREAM_SH)
        if name == 'cafe':                                          # the queue for the queue: rope between brass posts
            for x in (52, 75):
                d.rectangle([x, PLINTH - 12, x + 1, PLINTH - 1], fill=BRASS, outline=None)
                d.rectangle([x - 1, PLINTH - 14, x + 2, PLINTH - 12], fill=BRASS_HI, outline=INK)
            d.arc([53, PLINTH - 18, 75, PLINTH - 6], 20, 160, fill=(170, 40, 44))
        _plinth(d, W)
        d.rectangle([54, PLINTH, 73, 159], fill=(150, 118, 108), outline=INK)   # the doorway comes down to the paving
        d.line([55, PLINTH, 72, PLINTH], fill=(150, 118, 108))
        d.line([55, 158, 72, 158], fill=COPING_SH)
        d.line([0, SOFFIT, W - 1, SOFFIT], fill=INK)
        return im
    return draw


def sprites():
    p = 'mall-in-'
    return {
        p + 'floor-a': paving(True), p + 'floor-b': paving(False),
        p + 'side-w': wall_side(ATRIUM, 'w'), p + 'side-e': wall_side(ATRIUM, 'e'),
        p + 'wall-front': wall_front(ATRIUM),
        p + 'threshold-w': threshold(ATRIUM, 'w'), p + 'threshold-e': threshold(ATRIUM, 'e'),
        p + 'doorlight': doorlight,
        p + 'wall-pier': wall_pier,
        **{p + f'front-{name}': front(name) for name in FRONTS},
        p + 'canal-n-a': canal('n', 21), p + 'canal-n-b': canal('n', 34),
        p + 'canal-a': canal('mid', 47), p + 'canal-b': canal('mid', 60),
        p + 'canal-s-a': canal('s', 73), p + 'canal-s-b': canal('s', 86),
        p + 'bridge': bridge, p + 'fountain': fountain,
        p + 'palm': palm,
    }


# The bridge lies flat under whoever crosses it, as tools/generate_fukuoka_art.py's
# taiko bridge does (FLAT); the light through the door lies on the floor, as the pub's.
DEPTH_BIAS = {'mall-in-bridge': -200, 'mall-in-doorlight': -40}

# Worth looking up at from the north bank (issue #258): sprite family -> rows of
# building below the sprite (config game.lookUp.sprites, see "Looking up at
# landmarks" in hud-input-touch.md). The back wall is five rows tall and stands
# on the floor (0), and a landscape phone shows seven and a half rows: its
# ordinary camera showed a row and a half of the wall to somebody standing
# against it, and neither gallery. The whole wall is marked, piers and
# shopfronts, so the view is the same from one end of it to the other; the
# reach has faded out by the canal.
LOOK_UP = {'mall-in-wall-pier': 0, **{f'mall-in-front-{name}': 0 for name in FRONTS}}


if __name__ == '__main__':
    register(sprites(), DEPTH_BIAS, sys.argv)
    cfg = json.load(open('config.json'))
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
