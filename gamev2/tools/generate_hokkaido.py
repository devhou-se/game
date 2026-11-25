#!/usr/bin/env python3
"""generate_hokkaido.py — draw the Hokkaido sprites (issue #43).

No asset pack has Sapporo or Asahikawa art, so the landmarks are drawn here,
as shaded pixel art in the GuttyKreum palette and at its scale: everything is
drawn at half size (one drawn pixel = one pixel of a 32px RPG Maker tile) and
pixel-doubled, exactly like the 2x building crops. They are NOT white line-art
placeholders like Tokyo Tower / Tsutenkaku.

  sapporo-clock-tower_0_0   5x8   the Sapporo Clock Tower (Tokeidai): white
                                   clapboard hall, red roofs, the clock tower
                                   rising out of the front, snow on the roofs
  sapporo-tv-tower_0_0      6x13  the Sapporo TV Tower: red lattice (see-through
                                   between the members), green observation deck,
                                   the big digital clock, low base building
  asahikawa-bridge_0_0      2x5   a timber deck with green steel rails — the
                                   bridge over Asahikawa's frozen river (flat:
                                   Non-Collidables + depthBias, you walk ON it)
  ramen-banner_0_0          1x2   a red nobori reading ラーメン (hand-set pixel
                                   glyphs — no font needed)
  road-plain_0_0            1x1   bare asphalt for street crossings, derived from
                                   road-div-horizontal by removing the lane line
  dirt-snow-autotile_*      1x1   the dirt-outside path family with its green grass
                                   fringe recoloured to snow, for paths trodden
                                   through a snowed-in town (9 autotile roles)

(The LimeZu Modern_Exteriors clock tower in Tileset_53_MV was considered for
the Clock Tower and rejected: it is 16px art, so at this game's cell size its
pixels are twice the size of the GuttyKreum buildings beside it, it is more
saturated, and it is a red-brick European tower — nothing like the Tokeidai.)

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_sapporo.py / generate_asahikawa.py:
    python3 tools/generate_hokkaido.py [--preview out.png]
"""
import json
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

C = 32                                   # one cell, in drawn (half-size) pixels
CLEAR = (0, 0, 0, 0)


def rgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# the GuttyKreum palette (sampled from the house / torii / high-rise sprites)
INK = rgb('0a1627')
NAVY = rgb('172459')
RED, RED_HI, RED_LO, RED_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31'), rgb('904a37')
CREAM, CREAM_LO, CREAM_DK = rgb('e4cecc'), rgb('be9e8c'), rgb('8e7366')
WHITE, SNOW, SNOW_LO = rgb('ffffff'), rgb('f2f5fb'), rgb('c9d6ea')
GLASS, GLASS_HI, GLASS_DK = rgb('4b6396'), rgb('7db9fa'), rgb('2c2d51')
WOOD, WOOD_LO, WOOD_DK = rgb('bb8971'), rgb('86624f'), rgb('594b45')
STONE, STONE_LO, STONE_DK = rgb('bcc7cc'), rgb('848295'), rgb('47485d')
GREEN, GREEN_LO, GREEN_HI = rgb('506b6b'), rgb('395050'), rgb('89af78')
GOLD = rgb('c6a663')
AMBER = rgb('f9c22e')


def canvas(cw, ch):
    im = Image.new('RGBA', (cw * C, ch * C), CLEAR)
    return im, ImageDraw.Draw(im)


def outline(im, ink=INK):
    """Ink a 1px outline round everything drawn so far (4-neighbour), the way
    every GuttyKreum object is edged."""
    a = im.getchannel('A').point(lambda v: 255 if v else 0)
    grown = a.filter(ImageFilter.MaxFilter(3))
    cross = Image.new('L', a.size, 0)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cross = ImageChops.lighter(cross, ImageChops.offset(a, dx, dy))
    edge = ImageChops.subtract(ImageChops.multiply(cross, grown), a)
    im.paste(ink, (0, 0), edge)


def snow_cap(d, x0, x1, y, depth=3, seed=0):
    """A lumpy strip of lying snow with its lower edge in shadow."""
    for x in range(x0, x1 + 1):
        h = depth + ((x * 7 + seed * 13) % 5 in (0, 1)) - ((x * 3 + seed) % 7 == 0)
        d.line([(x, y), (x, y + h - 1)], fill=SNOW)
        d.point((x, y + h), fill=SNOW_LO)


def tiles(d, poly_rows, light, dark, step=4):
    """Roof tiling: (y, x0, x1) scanlines, alternating courses with a running
    bond of darker joints."""
    for y, x0, x1 in poly_rows:
        course = (y // step) % 2
        for x in range(x0, x1 + 1):
            joint = (y % step == step - 1) or ((x + course * 3) % 6 == 0)
            d.point((x, y), fill=dark if joint else light)


def window(d, x0, y0, x1, y1, frame=GREEN_LO):
    """A sash window: frame, glass with a highlight, a cross of glazing bars."""
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=GLASS)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=GLASS_HI)
    d.point((x0 + 2, y0 + 2), fill=GLASS_HI)
    d.line([((x0 + x1) // 2, y0 + 1), ((x0 + x1) // 2, y1 - 1)], fill=frame)
    d.line([(x0 + 1, (y0 + y1) // 2), (x1 - 1, (y0 + y1) // 2)], fill=frame)
    d.line([(x0, y1 + 1), (x1, y1 + 1)], fill=CREAM_LO)        # the sill's shadow


def clapboard(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=CREAM)
    for y in range(y0 + 2, y1 + 1, 3):
        d.line([(x0, y), (x1, y)], fill=CREAM_LO)
    d.line([(x0, y0), (x0, y1)], fill=WHITE)                    # lit corner board
    d.line([(x1, y0), (x1, y1)], fill=CREAM_DK)                 # shaded one


# ------------------------------------------------------------------------------
def clock_tower():
    im, d = canvas(5, 8)                 # 160 x 256
    cx = 80

    # ---- the hall: two clapboard storeys on a stone plinth --------------------
    clapboard(d, 6, 152, 153, 247)
    d.rectangle([6, 198, 153, 200], fill=CREAM_DK)              # the storey band
    d.line([(6, 197), (153, 197)], fill=WHITE)
    d.rectangle([4, 246, 155, 253], fill=STONE_LO)
    d.line([(4, 246), (155, 246)], fill=STONE)
    for x in range(10, 154, 12):
        d.line([(x, 248), (x, 253)], fill=STONE_DK)
    for wx in (14, 38, 108, 132):                               # upper + lower windows
        window(d, wx, 162, wx + 13, 186)
        window(d, wx, 208, wx + 13, 234)
    # the porch: double doors under a small red pent roof
    d.rectangle([62, 206, 97, 245], fill=CREAM_LO)
    d.rectangle([66, 214, 93, 245], fill=WOOD_DK)
    d.rectangle([67, 215, 79, 245], fill=WOOD_LO); d.rectangle([81, 215, 92, 245], fill=WOOD_LO)
    d.rectangle([69, 218, 77, 228], fill=GLASS); d.rectangle([83, 218, 90, 228], fill=GLASS)
    d.line([(69, 218), (77, 218)], fill=GLASS_HI); d.line([(83, 218), (90, 218)], fill=GLASS_HI)
    d.point((78, 232), fill=GOLD); d.point((82, 232), fill=GOLD)
    tiles(d, [(y, 58 - (y - 202), 101 + (y - 202)) for y in range(202, 210)], RED, RED_LO)
    snow_cap(d, 58, 101, 201, 2, seed=3)

    # ---- the main roof: a red hip roof, eaves wider than the walls ------------
    rows = []
    for y in range(112, 153):
        t = (y - 112) / 40
        rows.append((y, int(22 - 22 * t), int(137 + 22 * t)))
    tiles(d, rows, RED, RED_LO)
    for y, x0, x1 in rows:                                      # lit left hip, shaded right hip
        d.point((x0, y), fill=RED_HI); d.point((x0 + 1, y), fill=RED_HI)
        d.point((x1, y), fill=RED_DK); d.point((x1 - 1, y), fill=RED_DK)
    d.rectangle([0, 152, 159, 154], fill=RED_DK)                # the eaves' underside
    snow_cap(d, 22, 137, 110, 4, seed=1)                        # snow along the ridge...
    for x0, x1 in ((2, 30), (44, 58), (100, 118), (130, 157)):  # ...and drifts on the eaves
        snow_cap(d, x0, x1, 147, 3, seed=x0)

    # ---- the clock tower, rising out of the front of the roof -----------------
    clapboard(d, 50, 58, 109, 138)
    d.rectangle([50, 104, 109, 106], fill=CREAM_DK)             # belt under the clock
    d.line([(50, 103), (109, 103)], fill=WHITE)
    # the gable at its foot, with the red five-pointed star of the Kaitakushi
    for y in range(126, 153):
        w = (y - 126)
        d.line([(cx - 14 - w, y), (cx + 13 + w, y)], fill=CREAM if (y % 3) else CREAM_LO)
    for y in range(124, 153):                                   # its red bargeboards
        w = (y - 124)
        d.line([(cx - 16 - w, y), (cx - 13 - w, y)], fill=RED_HI if y % 4 else RED_LO)
        d.line([(cx + 12 + w, y), (cx + 15 + w, y)], fill=RED_DK if y % 4 else RED_LO)
    star = [(cx, 132), (cx + 2, 138), (cx + 8, 138), (cx + 3, 142), (cx + 5, 148),
            (cx, 144), (cx - 5, 148), (cx - 3, 142), (cx - 8, 138), (cx - 2, 138)]
    d.polygon(star, fill=RED, outline=RED_DK)
    window(d, 72, 110, 87, 122)                                 # the louvred belfry window
    # the clock: a white dial in a dark ring, twelve ticks, hands at ten past ten
    d.ellipse([cx - 19, 62, cx + 18, 99], fill=INK)
    d.ellipse([cx - 17, 64, cx + 16, 97], fill=WOOD_DK)
    d.ellipse([cx - 15, 66, cx + 14, 95], fill=WHITE)
    d.ellipse([cx - 15, 66, cx + 14, 95], outline=SNOW_LO)
    import math
    for h in range(12):
        a = math.radians(h * 30)
        d.point((round(cx - 0.5 + 12 * math.sin(a)), round(80.5 - 12 * math.cos(a))), fill=INK)
    d.line([(cx, 80), (cx - 7, 75)], fill=INK)                  # hour hand
    d.line([(cx, 80), (cx + 5, 70)], fill=INK)                  # minute hand
    d.point((cx, 80), fill=RED)
    # the tower's pyramid roof and its finial
    rows = []
    for y in range(22, 60):
        t = (y - 22) / 37
        rows.append((y, int(cx - 2 - 38 * t), int(cx + 1 + 38 * t)))
    tiles(d, rows, RED, RED_LO)
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            if x > cx + (y - 22) // 3:                          # the shaded right face
                d.point((x, y), fill=RED_DK if (y % 4 == 3) else RED_LO)
        d.point((x0, y), fill=RED_HI)
    d.rectangle([40, 59, 119, 61], fill=RED_DK)
    snow_cap(d, cx - 12, cx + 4, 24, 5, seed=5)                 # snow on the windward face
    for x0, x1 in ((42, 62), (92, 117)):
        snow_cap(d, x0, x1, 54, 3, seed=x0)
    d.rectangle([cx - 1, 8, cx, 22], fill=STONE_LO)             # finial
    d.rectangle([cx - 3, 12, cx + 2, 14], fill=GOLD)
    d.point((cx - 1, 6), fill=GOLD); d.point((cx, 6), fill=GOLD)

    outline(im)
    return im


# ------------------------------------------------------------------------------
def tv_tower():
    im, d = canvas(6, 13)                # 192 x 416
    cx = 96

    def half_width(y):
        """Half the tower's width at height y: a slim shaft that flares out
        towards the feet, the Eiffel profile of the real tower."""
        if y <= 150:
            return 9 + (y - 60) * 13 / 90
        t = (y - 180) / (372 - 180)
        return 25 + 50 * (t ** 1.7)

    lat = Image.new('L', im.size, 0)     # the steelwork, as a mask
    ld = ImageDraw.Draw(lat)

    def section(y0, y1, bays):
        """One tier of lattice: two legs, a girder at the top, crossed braces."""
        w0, w1 = half_width(y0), half_width(y1)
        ld.line([(cx - w0, y0), (cx - w1, y1)], fill=255, width=4)
        ld.line([(cx + w0, y0), (cx + w1, y1)], fill=255, width=4)
        ld.line([(cx - w0, y0), (cx + w0, y0)], fill=255, width=3)
        for b in range(bays):
            a0 = cx - w0 + 2 * w0 * b / bays; a1 = cx - w0 + 2 * w0 * (b + 1) / bays
            b0 = cx - w1 + 2 * w1 * b / bays; b1 = cx - w1 + 2 * w1 * (b + 1) / bays
            ld.line([(a0, y0), (b1, y1)], fill=255, width=2)
            ld.line([(a1, y0), (b0, y1)], fill=255, width=2)

    for y0, y1 in ((60, 82), (82, 104), (104, 127), (127, 150)):
        section(y0, y1, 1)
    for y0, y1 in ((180, 204), (204, 232), (232, 264), (264, 300), (300, 336), (336, 372)):
        section(y0, y1, 2)
    ld.line([(cx - half_width(372), 372), (cx + half_width(372), 372)], fill=255, width=3)

    # paint the steel: red, lit from the left, with the right-hand side in shade
    steel = Image.new('RGBA', im.size, CLEAR)
    px, mk = steel.load(), lat.load()
    for y in range(im.height):
        for x in range(im.width):
            if not mk[x, y]:
                continue
            lit = x > 0 and not mk[x - 1, y]
            dark = x < im.width - 1 and not mk[x + 1, y]
            px[x, y] = RED_HI if lit else (RED_DK if dark else (RED if x < cx + 4 else RED_LO))
    outline(steel)
    im.alpha_composite(steel)

    # ---- the mast: red and white bands ----------------------------------------
    for y in range(6, 60):
        band = RED if ((y - 6) // 9) % 2 == 0 else WHITE
        d.line([(cx - 2, y), (cx + 1, y)], fill=band)
        d.point((cx + 1, y), fill=RED_DK if band == RED else SNOW_LO)
    d.rectangle([cx - 5, 54, cx + 4, 60], fill=STONE_LO)
    d.line([(cx - 5, 54), (cx + 4, 54)], fill=STONE)

    # ---- the observation deck: a green box with a band of windows -------------
    d.rectangle([cx - 30, 150, cx + 29, 181], fill=GREEN)
    d.rectangle([cx - 30, 150, cx + 29, 153], fill=GREEN_HI)
    d.rectangle([cx - 30, 176, cx + 29, 181], fill=GREEN_LO)
    d.rectangle([cx - 27, 158, cx + 26, 170], fill=GLASS_DK)
    for x in range(cx - 26, cx + 26, 7):
        d.rectangle([x, 159, x + 4, 169], fill=GLASS)
        d.line([(x, 159), (x + 4, 159)], fill=GLASS_HI)
    d.rectangle([cx - 33, 172, cx + 32, 174], fill=STONE)       # the gallery rail
    snow_cap(d, cx - 30, cx + 29, 147, 3, seed=2)

    # ---- the digital clock, hung on the lattice below the deck ----------------
    d.rectangle([cx - 27, 196, cx + 26, 222], fill=INK)
    d.rectangle([cx - 25, 198, cx + 24, 220], fill=rgb('1c1c22'))
    seg = {'1': 'bc', '0': 'abcdef', '5': 'afgcd', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
           '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abfgcd'}

    def digit(ch, x, y, w=8, h=16):
        m = h // 2
        lines = {'a': [(x + 1, y), (x + w - 2, y)], 'g': [(x + 1, y + m), (x + w - 2, y + m)],
                 'd': [(x + 1, y + h), (x + w - 2, y + h)],
                 'f': [(x, y + 1), (x, y + m - 1)], 'e': [(x, y + m + 1), (x, y + h - 1)],
                 'b': [(x + w - 1, y + 1), (x + w - 1, y + m - 1)],
                 'c': [(x + w - 1, y + m + 1), (x + w - 1, y + h - 1)]}
        for s in seg[ch]:
            d.line(lines[s], fill=AMBER, width=2)

    for ch, x in zip('1504', (cx - 22, cx - 11, cx + 3, cx + 14)):
        digit(ch, x, 201)
    d.rectangle([cx - 1, 205, cx, 206], fill=AMBER); d.rectangle([cx - 1, 212, cx, 213], fill=AMBER)

    # ---- the base building the legs stand in ----------------------------------
    d.rectangle([14, 360, 177, 411], fill=STONE)
    d.rectangle([14, 360, 177, 364], fill=WHITE)
    d.rectangle([14, 404, 177, 411], fill=STONE_LO)
    d.line([(177, 360), (177, 411)], fill=STONE_LO)
    for x in range(22, 170, 18):
        if 78 <= x <= 104:
            continue
        d.rectangle([x, 372, x + 11, 388], fill=GLASS_DK)
        d.rectangle([x + 1, 373, x + 10, 387], fill=GLASS)
        d.line([(x + 1, 373), (x + 10, 373)], fill=GLASS_HI)
        d.line([(x + 5, 373), (x + 5, 387)], fill=GLASS_DK)
    d.rectangle([80, 370, 111, 411], fill=STONE_DK)             # the entrance
    d.rectangle([82, 376, 95, 411], fill=GLASS); d.rectangle([97, 376, 109, 411], fill=GLASS)
    d.line([(82, 376), (95, 376)], fill=GLASS_HI); d.line([(97, 376), (109, 376)], fill=GLASS_HI)
    d.rectangle([76, 366, 115, 371], fill=RED)                  # its red canopy
    d.line([(76, 371), (115, 371)], fill=RED_DK)
    snow_cap(d, 14, 177, 357, 4, seed=4)

    outline(im)
    return im


# ------------------------------------------------------------------------------
def bridge():
    im, d = canvas(2, 5)                 # 64 x 160
    d.rectangle([4, 2, 59, 157], fill=WOOD)
    for y in range(2, 158):                                      # boards across the walk
        if y % 6 == 1:
            d.line([(4, y), (59, y)], fill=WOOD_LO)
        elif y % 6 == 2:
            d.line([(4, y), (59, y)], fill=rgb('d2a58c'))
    for y in range(8, 158, 12):                                  # a few nail heads / knots
        d.point((14 + (y * 5) % 9, y), fill=WOOD_DK); d.point((44 + (y * 3) % 7, y + 3), fill=WOOD_DK)
    for x0 in (2, 56):                                           # green steel rails
        d.rectangle([x0, 4, x0 + 5, 155], fill=GREEN)
        d.line([(x0 + 1, 4), (x0 + 1, 155)], fill=GREEN_HI)
        d.line([(x0 + 5, 4), (x0 + 5, 155)], fill=GREEN_LO)
        for y in range(4, 156, 19):                              # posts, capped with snow
            d.rectangle([x0 - 1, y, x0 + 6, y + 5], fill=GREEN_LO)
            d.rectangle([x0 - 1, y, x0 + 6, y + 2], fill=SNOW)
            d.line([(x0 - 1, y + 3), (x0 + 6, y + 3)], fill=SNOW_LO)
    for y0 in (0, 154):                                          # stone abutments at each bank
        d.rectangle([1, y0, 62, y0 + 5], fill=STONE_LO)
        d.line([(1, y0), (62, y0)], fill=STONE)
    outline(im)
    return im


# ------------------------------------------------------------------------------
GLYPHS = {       # ラ ー メ ン, top to bottom (ー stands upright in vertical text)
    'ra': ['.#######.', '.........', '#########', '........#', '........#',
           '.......#.', '......#..', '....##...', '..##.....'],
    'bar': ['....#....'] * 7,
    'me': ['......#..', '......#..', '.#...#...', '..##.#...', '....##...',
           '....#.#..', '...#...#.', '..#......', '.#.......'],
    'n': ['.#.......', '..#.....#', '...#....#', '.......#.', '.......#.',
          '......#..', '.....#...', '...##....', '.##......'],
}


def ramen_banner():
    im, d = canvas(1, 2)                 # 32 x 64
    d.rectangle([5, 2, 6, 61], fill=WOOD_LO)                     # the pole
    d.point((5, 2), fill=WOOD); d.rectangle([3, 60, 8, 62], fill=STONE_DK)
    d.rectangle([5, 4, 22, 5], fill=WOOD_LO)                     # the cross arm
    d.rectangle([9, 6, 23, 52], fill=RED)
    d.line([(9, 6), (9, 52)], fill=RED_HI)
    d.line([(23, 6), (23, 52)], fill=RED_DK)
    d.line([(9, 52), (23, 52)], fill=RED_DK)
    y = 9
    for name in ('ra', 'bar', 'me', 'n'):
        for gy, row in enumerate(GLYPHS[name]):
            for gx, ch in enumerate(row):
                if ch == '#':
                    d.point((12 + gx, y + gy), fill=WHITE)
        y += len(GLYPHS[name]) + 2
    snow_cap(d, 5, 22, 2, 2, seed=6)
    outline(im)
    return im


# ------------------------------------------------------------------------------
def road_plain():
    """road-div-horizontal with its lane line painted out: each pixel of the
    line takes the asphalt pixel the same distance above the line's band."""
    src = Image.open('assets/sprites/road-div-horizontal_0_0.png').convert('RGBA')
    top = Image.open('assets/sprites/road-edge-bottom_0_0.png').convert('RGBA')
    px = src.load()
    lum = lambda p: (p[0] * 3 + p[1] * 6 + p[2]) / 10
    base = sorted(lum(px[x, y]) for x in range(64) for y in range(64))[2048]
    out = src.copy(); op = out.load(); tp = top.load()
    for y in range(64):
        for x in range(64):
            if lum(px[x, y]) > base + 24:                        # the pale lane paint
                op[x, y] = tp[x, (y + 20) % 40]
    return out


SPRITES = {      # key: (builder, pixel-double?, tileNames label)
    'sapporo-clock-tower_0_0': (clock_tower, True, 'sapporo-clock-tower'),
    'sapporo-tv-tower_0_0': (tv_tower, True, 'sapporo-tv-tower'),
    'asahikawa-bridge_0_0': (bridge, True, 'asahikawa-bridge'),
    'ramen-banner_0_0': (ramen_banner, True, 'ramen-banner'),
    'road-plain_0_0': (road_plain, False, 'road-plain'),
}


# Sprites that lie flat on the ground but must cover the Water layer: they go on
# Non-Collidables (Y-sorted) with a depth nudge that drops them under everything
# standing, so the player walks ON them (RoomManager reads depthBias).
FLAT = {'asahikawa-bridge_0_0': -200}


# dirt-outside-autotile's grass fringe -> snow bank (exact palette swaps; the
# dirt, its shadow and the ink line are kept)
SNOW_FRINGE = {(131, 175, 111): (232, 240, 249), (80, 133, 130): (196, 208, 224),
               (66, 95, 170): (160, 176, 200)}
DIRT_ROLES = ('center', 'edge-n', 'edge-s', 'edge-e', 'edge-w',
              'corner-ne', 'corner-nw', 'corner-se', 'corner-sw')


def snow_dirt(cfg):
    for role in DIRT_ROLES:
        src, dst = f'dirt-outside-autotile_{role}', f'dirt-snow-autotile_{role}'
        im = Image.open(f'assets/sprites/{src}.png').convert('RGBA')
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if (r, g, b) in SNOW_FRINGE:
                    px[x, y] = SNOW_FRINGE[(r, g, b)] + (a,)
        im.save(f'assets/sprites/{dst}.png')
        cfg['spriteMetadata'][dst] = dict(cfg['spriteMetadata'][src])
        cfg.setdefault('tileNames', {})[dst] = 'dirt-snow-autotile'
    print(f'dirt-snow-autotile: {len(DIRT_ROLES)} roles')


def main():
    built = {}
    for key, (fn, double, _) in SPRITES.items():
        im = fn()
        if double:
            im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')

    # register so the game loads them: multi-cell sprites anchor on the centre
    # of their top-left cell (unrounded — a rounded anchor drifts off the grid)
    cfg = json.load(open('config.json'))
    for key, (_, _, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if key in FLAT:
            cfg['spriteMetadata'][key]['depthBias'] = FLAT[key]
        cfg.setdefault('tileNames', {})[key] = label
    snow_dirt(cfg)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (sum(i.width + 16 for i in built.values()) + 16,
                                   max(i.height for i in built.values()) + 32), rgb('e9eef6'))
        x = 16
        for im in built.values():
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
