#!/usr/bin/env python3
"""generate_tokyo_art.py — draw Tokyo Tower and Tokyo Station (issue #70).

The two Tokyo landmarks came over from the Godot game as white line art, with
no tool behind them, and clashed with the GuttyKreum buildings round them.
Until the team's own pixel art arrives they are drawn here the way
generate_hokkaido.py / generate_sapporo_art.py draw theirs: shaded pixel art in
the GuttyKreum palette, at half size (one drawn pixel = one pixel of a 32px
tile) and pixel-doubled, lit from the left, with a 1px ink outline. THESE ARE
PLACEHOLDERS STILL: a PNG of the same size dropped over one of them needs no
code or map change (and this tool then stops being run for it).

  tokyo-tower_0_0     8x15  Tokyo Tower: open lattice in bands of vermilion and
                            white (see-through between the members), the white
                            two-storey main observatory, the small top deck, a
                            banded antenna with a red lamp, Foot Town under the
                            arch, the two front legs carrying on to their
                            concrete footings
  tokyo-tower-feet    8x3   the bottom three rows of that picture, cut from it
                            here: Park's copy of the feet (the stitched city
                            drops it, `?stitch=0` shows it)
  tokyo-station_0_0   41x8  Tokyo Station's Marunouchi front: three storeys of
                            red brick banded in stone under a slate roof, a
                            slate dome on an octagonal drum over each end
                            pavilion, a brick gable with one big lit window
                            over the centre block, the stone porch and the door

The map, the prefabs and config.json are not touched, so the pictures have to
fit what is already there. Hard rules (tools/tests/landmark-placeholders.test.js):

  tower    - 512x960; the feet file is its bottom 192 rows, pixel for pixel
           - the cells you walk through between the feet (row 13 columns 2..5,
             row 14 columns 1..6: no collider in Palace) are more than half
             transparent. What stands on the ground is over the solid cells:
             row 12 columns 1..6, row 13 columns 0..1 and 6..7, row 14 columns
             0 and 7
  station  - 2624x512
           - rows 0 and 1 are transparent outside columns 0, 4..6, 18..22,
             34..36 and 40 (the turrets, the domes, the centre gable): Palace's
             passing train runs on the row behind the roof and has to show
           - the forecourt is clear: cells (16..18, 7) and (22..24, 7) are
             fully transparent, and beside the porch nothing comes below the
             ground line (GROUND) in row 6 either. Palace's shrub gardens, lamp
             posts and a vending machine stand there, inside the footprint
           - cell (20, 7), the one door cell, is drawn

Deterministic and idempotent: rewrites the three PNGs in assets/sprites/ and
nothing else (the keys are registered already: no config.json write). Needs
Pillow and its two sibling tools, which it imports: generate_hokkaido,
generate_sapporo_art. Run from gamev2/:
    python3 tools/generate_tokyo_art.py [--sheet sheet.png]
"""
import math
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import (rgb, canvas, outline, tiles, CLEAR, INK, NAVY,              # noqa: E402
                               RED, CREAM, CREAM_LO, CREAM_DK,
                               WHITE, GLASS, GLASS_HI, GLASS_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, GOLD)
from generate_sapporo_art import (brick, glazing, glass_door, text, text_w,                # noqa: E402
                                  BRICK, BRICK_HI, BRICK_DK, SLATE, SLATE_LO, WARM, DARK)

SPR = 'assets/sprites'
C = 32                                   # one cell, in drawn (half-size) pixels
SLATE_HI = STONE_LO                      # slate where the light falls on it


def layer(im, draw):
    """Draw one mass on a sheet of its own, ink its outline and lay it over
    `im`: what stands in front is edged against what it stands in front of."""
    lay = Image.new('RGBA', im.size, CLEAR)
    draw(lay, ImageDraw.Draw(lay))
    outline(lay)
    im.alpha_composite(lay)


# ==============================================================================
# Tokyo Tower
# ==============================================================================
# the tower's paint: the palette's red a step towards orange, to stand off the station's brick
VERM, VERM_HI, VERM_LO, VERM_DK = rgb('e06a45'), rgb('f59470'), rgb('b84d2e'), rgb('8f3a26')
AXIS = 127.5                             # the tower's axis lies between x 127 and 128
SHAFT = (32, 54, 76, 98, 120, 142, 166, 190, 216)                # tiers of the upper shaft, top to bottom
LEGS = (264, 286, 308, 330, 352, 374, 396, 418, 440, 464)        # tiers below the main observatory
ARCH = 330                               # the crown of the arch between the legs
FOOT = 464                               # where the front legs meet their footings


def half_width(y):
    """Half the tower's width at height y: a slim shaft, then the Eiffel flare
    of the legs, out to the front footings."""
    if y <= 264:
        return 8 + (min(y, 216) - 32) * 24 / 184
    return 32 + 86 * ((y - 264) / (FOOT - 264)) ** 1.6


def opening(y):
    """Half the width of the arch between the legs at height y (0 above its
    crown): a round head, then the legs' inner edges, each leg narrowing from
    30px to 14px at its foot."""
    if y < ARCH:
        return 0
    inner = lambda v: half_width(v) - (14 + 16 * (FOOT - v) / (FOOT - ARCH))      # noqa: E731
    spring = ARCH + 45
    if y >= spring:
        return inner(y)
    return inner(spring) * math.sqrt(1 - ((spring - y) / 45) ** 2)


def tower_steel(size):
    """The steelwork as two masks: the near face of the lattice, and the far
    face seen through it (thinner, half a bay out of step)."""
    lat, far = Image.new('L', size, 0), Image.new('L', size, 0)
    ld, fd = ImageDraw.Draw(lat), ImageDraw.Draw(far)

    def chord(fn, y0, y1, s, width):
        pts = [(AXIS + s * fn(y), y) for y in range(y0, y1 + 1, 2)]
        ld.line(pts, fill=255, width=width)

    def braces(a0, a1, b0, b1, y0, y1, bays):
        """A girder a0..a1 at y0 and crossed braces down to b0..b1 at y1."""
        ld.line([(a0, y0), (a1, y0)], fill=255, width=2)
        ym = (y0 + y1) // 2
        fd.line([((a0 + b0) / 2, ym), ((a1 + b1) / 2, ym)], fill=255)
        for b in range(bays):
            p0, p1 = a0 + (a1 - a0) * b / bays, a0 + (a1 - a0) * (b + 1) / bays
            q0, q1 = b0 + (b1 - b0) * b / bays, b0 + (b1 - b0) * (b + 1) / bays
            ld.line([(p0, y0), (q1, y1)], fill=255, width=2)
            ld.line([(p1, y0), (q0, y1)], fill=255, width=2)
            fd.line([((p0 + p1) / 2, y0), ((q0 + q1) / 2, y1)], fill=255)

    for y0, y1 in zip(SHAFT, SHAFT[1:]):
        w0, w1 = half_width(y0), half_width(y1)
        braces(AXIS - w0, AXIS + w0, AXIS - w1, AXIS + w1, y0, y1, 1 if w1 < 21 else 2)
        for s in (-1, 1):
            chord(half_width, y0, y1, s, 3)
    for y0, y1 in zip(LEGS, LEGS[1:]):
        w0, w1 = half_width(y0), half_width(y1)
        if y1 <= ARCH:                                           # above the arch: one face, side to side
            braces(AXIS - w0, AXIS + w0, AXIS - w1, AXIS + w1, y0, y1, 2)
        else:                                                    # the two legs, the arch between them
            for s in (-1, 1):
                a, b = sorted((AXIS + s * w0, AXIS + s * opening(y0)))
                c, e = sorted((AXIS + s * w1, AXIS + s * opening(y1)))
                braces(a, b, c, e, y0, y1, 1)
                chord(opening, y0, y1, s, 3)
        for s in (-1, 1):
            chord(half_width, y0, y1, s, 4)
    return lat, far


def tower():
    im, _ = canvas(8, 15)                # 256 x 480

    # ---- Foot Town: the low building under the arch (the body of the solid row) --
    def foot_town(lay, d):
        d.rectangle([56, 368, 199, 415], fill=STONE)
        d.rectangle([56, 368, 199, 370], fill=WHITE)                              # the parapet
        d.line([(56, 371), (199, 371)], fill=STONE_LO)
        glazing(d, 60, 375, 195, 388, cw=8, ch=13)
        d.rectangle([56, 391, 199, 393], fill=VERM); d.line([(56, 393), (199, 393)], fill=VERM_DK)   # a vermilion fascia
        d.line([(56, 391), (199, 391)], fill=VERM_HI)
        glazing(d, 60, 396, 195, 410, cw=12, ch=14, lit=((4, 0), (5, 0), (6, 0)))
        d.rectangle([56, 411, 199, 415], fill=STONE_LO)
        d.line([(56, 411), (199, 411)], fill=STONE)
        d.rectangle([193, 372, 199, 410], fill=STONE_LO)                          # its east end, in shade

    layer(im, foot_town)

    # ---- the steel: bands of vermilion and white, lit from the left --------------
    lat, far = tower_steel(im.size)
    steel = Image.new('RGBA', im.size, CLEAR)
    px, mk, fk = steel.load(), lat.load(), far.load()
    bands = SHAFT[:-1] + LEGS[:-1]                                # each band starts at a tier

    def band(y):
        return sum(1 for b in bands if b <= y) // 2 % 2 == 0     # two tiers to a band; True: vermilion

    for y in range(im.height):
        red = band(y)
        for x in range(im.width):
            if not mk[x, y]:
                if fk[x, y]:
                    px[x, y] = VERM_DK if red else CREAM_DK
                continue
            lit = x > 0 and not mk[x - 1, y]
            dark = x < im.width - 1 and not mk[x + 1, y]
            east = x > AXIS + 4
            if red:
                px[x, y] = VERM_HI if lit else (VERM_DK if dark else (VERM_LO if east else VERM))
            else:
                px[x, y] = WHITE if lit else (CREAM_LO if dark else (CREAM if east else WHITE))
    outline(steel)
    im.alpha_composite(steel)

    def decks(lay, d):
        # ---- the antenna: banded, a red lamp on top -------------------------------
        for y in range(5, 28):
            c = VERM if ((y - 5) // 5) % 2 == 0 else WHITE
            d.point((127, y), fill=c)
            d.point((128, y), fill=VERM_DK if c == VERM else CREAM_LO)
        d.rectangle([126, 2, 129, 4], fill=VERM); d.point((126, 2), fill=VERM_HI)
        d.rectangle([123, 28, 132, 33], fill=STONE); d.rectangle([129, 28, 132, 33], fill=STONE_LO)
        d.line([(123, 28), (132, 28)], fill=WHITE)
        # ---- the top deck: a small white box on the shaft --------------------------
        d.rectangle([106, 110, 149, 127], fill=WHITE)
        d.rectangle([106, 123, 149, 127], fill=STONE); d.rectangle([142, 110, 149, 127], fill=STONE_LO)
        d.rectangle([108, 114, 147, 120], fill=GLASS_DK)
        for x in range(109, 146, 5):
            d.rectangle([x, 115, x + 3, 119], fill=GLASS); d.line([(x, 115), (x + 3, 115)], fill=GLASS_HI)
        d.rectangle([104, 108, 151, 110], fill=STONE); d.line([(104, 108), (151, 108)], fill=WHITE)
        # ---- the main observatory: two glazed storeys, white ------------------------
        d.polygon([(84, 257), (171, 257), (161, 263), (94, 263)], fill=STONE_LO)  # its underside
        d.line([(94, 263), (161, 263)], fill=STONE_DK)
        d.rectangle([84, 216, 171, 257], fill=WHITE)
        d.rectangle([162, 216, 171, 257], fill=STONE)                             # the east end, in shade
        for y0 in (222, 243):                                                     # the two window bands
            d.rectangle([86, y0, 169, y0 + 10], fill=GLASS_DK)
            for i, x in enumerate(range(87, 168, 6)):
                lit = (i + y0) % 5 == 0
                d.rectangle([x, y0 + 1, x + 4, y0 + 9], fill=WARM if lit else GLASS)
                d.line([(x, y0 + 1), (x + 4, y0 + 1)], fill=WHITE if lit else GLASS_HI)
        d.rectangle([82, 236, 173, 239], fill=STONE); d.line([(82, 236), (173, 236)], fill=WHITE)   # the gallery
        d.line([(82, 239), (173, 239)], fill=STONE_LO)
        d.rectangle([82, 214, 173, 217], fill=STONE); d.line([(82, 214), (173, 214)], fill=WHITE)   # the roof slab
        d.rectangle([84, 255, 171, 257], fill=STONE_LO)
        # ---- the front footings: concrete blocks under the two front legs ----------
        for x0 in (5, 226):
            d.rectangle([x0, 462, x0 + 24, 475], fill=STONE)
            d.line([(x0, 462), (x0 + 24, 462)], fill=WHITE)
            d.rectangle([x0, 471, x0 + 24, 475], fill=STONE_LO)
            d.rectangle([x0 + 20, 463, x0 + 24, 475], fill=STONE_LO)
            for x in (x0 + 5, x0 + 15):                                           # the anchor bolts
                d.rectangle([x, 465, x + 1, 467], fill=STONE_DK)

    layer(im, decks)
    return im


# ==============================================================================
# Tokyo Station
# ==============================================================================
SW = 41 * C                              # 1312: the front is mirrored about x 655 / 656
GROUND = 207                             # the foot of the wings' wall: nothing but the
#                                          pavilions and the porch comes below it
RIDGE = 67                               # the wings' roof ridge: rows 0 and 1 stay clear above it


def mirror(x, w=1):
    """Where a piece w wide that starts at x stands in the other half."""
    return SW - x - w


def disc(d, cx, cy, r, fill):
    """A filled circle about a pixel centre or corner (cx, cy may end in .5),
    by scanlines: the same pixels on every Pillow."""
    for y in range(int(math.floor(cy - r)), int(math.ceil(cy + r)) + 1):
        for x in range(int(math.floor(cx - r)), int(math.ceil(cx + r)) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                d.point((x, y), fill=fill)


def round_head(d, x0, x1, y0, y1, fill):
    """A round-headed shape x0..x1 wide: a semicircle from y0, straight to y1."""
    r = (x1 - x0 + 1) / 2
    cx, cy = (x0 + x1) / 2, y0 + r - 0.5
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if y >= cy or (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                d.point((x, y), fill=fill)


def arch(d, x0, x1, y0, y1, lit=False, rail=True, sill=BRICK_DK):
    """A round-headed window x0..x1 in a white stone surround, a mullion down
    its middle and a transom at the springing (generate_sapporo_art.arched,
    for any width)."""
    w = x1 - x0 + 1
    spring = y0 + w // 2
    round_head(d, x0 - 1, x1 + 1, y0 - 1, y1 + 1, CREAM)
    round_head(d, x0, x1, y0, y1, WARM if lit else GLASS)
    d.line([(x0, spring), (x0 + w // 2 - 1, spring)], fill=WHITE if lit else GLASS_HI)
    d.rectangle([x0 + (w - 1) // 2, y0 + 1, x0 + w // 2, y1], fill=CREAM)
    if rail:
        d.line([(x0, spring + 4), (x1, spring + 4)], fill=CREAM)
    d.line([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], fill=sill)


def sash(d, x0, x1, y0, y1, lit=False, sill=BRICK_DK):
    """A square-headed window in the same surround."""
    w = x1 - x0 + 1
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=CREAM)
    d.rectangle([x0, y0, x1, y1], fill=WARM if lit else GLASS)
    d.line([(x0, y0), (x0 + w // 2 - 1, y0)], fill=WHITE if lit else GLASS_HI)
    d.rectangle([x0 + (w - 1) // 2, y0, x0 + w // 2, y1], fill=CREAM)
    d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=CREAM)
    d.line([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], fill=sill)


def band(d, x0, x1, y, h=2):
    """A course of white stone across the brick, its lower edge in shadow."""
    d.rectangle([x0, y, x1, y + h - 1], fill=CREAM)
    d.line([(x0, y), (x1, y)], fill=WHITE)
    d.line([(x0, y + h), (x1, y + h)], fill=BRICK_DK)


def cornice(d, x0, x1, y):
    d.rectangle([x0, y, x1, y + 3], fill=CREAM)
    d.line([(x0, y), (x1, y)], fill=WHITE)
    d.line([(x0, y + 3), (x1, y + 3)], fill=CREAM_DK)


def quoins(d, x, y0, y1, w=3, shade=False):
    """Blocks of white stone up a corner."""
    for y in range(y0, y1 - 1, 6):
        d.rectangle([x, y, x + w - 1, y + 2], fill=CREAM_LO if shade else CREAM)


def plinth(d, x0, x1, y0, y1):
    """The granite the brick stands on."""
    d.rectangle([x0, y0, x1, y1], fill=STONE)
    d.line([(x0, y0), (x1, y0)], fill=WHITE)
    for x in range(x0 + 6, x1, 12):
        d.line([(x, y0 + 1), (x, y1)], fill=STONE_LO)
    d.line([(x0, y1), (x1, y1)], fill=STONE_LO)


def slate(d, rows, light=SLATE, dark=SLATE_LO):
    tiles(d, rows, light, dark, step=4)


def clipped(lay, rows, draw):
    """Draw with `draw(d)` on a sheet of its own and keep only the (y, x0, x1)
    scanlines of `rows`: brickwork cut to a gable."""
    part = Image.new('RGBA', lay.size, CLEAR)
    draw(ImageDraw.Draw(part))
    mask = Image.new('L', lay.size, 0)
    md = ImageDraw.Draw(mask)
    for y, x0, x1 in rows:
        md.line([(x0, y), (x1, y)], fill=255)
    lay.paste(part, (0, 0), mask)


def storeys(d, x, i=0):
    """One bay of the wings: a round-headed window over two square ones, 9 wide."""
    arch(d, x, x + 8, 113, 130, lit=i % 7 == 2)
    sash(d, x, x + 8, 145, 161, lit=i % 9 == 5)
    sash(d, x, x + 8, 176, 193, lit=i % 11 == 3)


def wings(im, d):
    # ---- the slate roof: a shallow top slope, a steep one below it, dormers -------
    slate(d, [(y, 10, SW - 11) for y in range(RIDGE, 78)], SLATE_HI, SLATE)
    slate(d, [(y, 8, SW - 9) for y in range(78, 104)])
    d.line([(10, RIDGE), (SW - 11, RIDGE)], fill=GREEN_HI)                        # the copper ridge
    d.line([(10, RIDGE + 1), (SW - 11, RIDGE + 1)], fill=GREEN_LO)
    d.line([(8, 78), (SW - 9, 78)], fill=SLATE_LO)
    # ---- three storeys of brick, banded in white stone, on granite ----------------
    brick(d, 8, 108, SW - 9, 199)
    cornice(d, 6, SW - 7, 104)
    band(d, 8, SW - 9, 138)
    band(d, 8, SW - 9, 168)
    plinth(d, 8, SW - 9, 200, GROUND)
    # ---- the windows, bay by bay; each stretch of wall is mirrored in the other half
    n = 0
    for x0, bays in ((32, 6), (224, 10), (416, 10)):
        for i in range(bays):
            x = x0 + 16 * i + 4
            for wx in (x, mirror(x, 9)):
                storeys(d, wx, n)
                n += 1
            if i % 2 == 0:                                                        # a dormer over every other bay
                for wx in (x + 8, mirror(x + 8, 9)):
                    d.rectangle([wx - 2, 83, wx + 10, 85], fill=GREEN_LO)
                    d.line([(wx - 2, 83), (wx + 10, 83)], fill=GREEN_HI)
                    sash(d, wx, wx + 8, 87, 97, sill=SLATE_LO)
        for i in range(2, bays, 2 if bays == 6 else 4):                           # stone piers up the wall
            x = x0 + 16 * i - 1
            for px0 in (x, mirror(x, 3)):
                quoins(d, px0, 110, 198)


def bay(lay, d, x0):
    """A gabled bay, a cell wide, breaking the long run of each wing: brick
    standing a little proud, its gable against the roof."""
    cx = x0 + 15.5
    rows = [(y, int(math.ceil(cx - (y - 69) * 0.47 - 1)), int(math.floor(cx + (y - 69) * 0.47 + 1)))
            for y in range(70, 104)]
    clipped(lay, rows, lambda pd: brick(pd, x0, 70, x0 + 31, 103))
    for y, a, b in rows:                                                          # the stone coping
        d.line([(a - 1, y), (a + 1, y)], fill=CREAM); d.point((a - 1, y), fill=WHITE)
        d.line([(b - 1, y), (b + 1, y)], fill=CREAM_LO)
    disc(d, cx, 90, 4.5, CREAM); disc(d, cx, 90, 3, GLASS); d.point((x0 + 14, 88), fill=GLASS_HI)
    brick(d, x0, 108, x0 + 31, 199)
    brick(d, x0 + 27, 108, x0 + 31, 199, shade=True)
    cornice(d, x0 - 1, x0 + 32, 104)
    band(d, x0, x0 + 31, 138); band(d, x0, x0 + 31, 168)
    plinth(d, x0, x0 + 31, 200, GROUND)
    quoins(d, x0, 110, 198); quoins(d, x0 + 29, 110, 198, shade=True)
    arch(d, x0 + 9, x0 + 22, 112, 131, lit=True)
    sash(d, x0 + 6, x0 + 13, 145, 161); sash(d, x0 + 18, x0 + 25, 145, 161)
    arch(d, x0 + 9, x0 + 22, 175, 193, rail=False)


def turret(lay, d, x0):
    """An end turret: an octagonal brick shaft under a pointed slate cap."""
    cx = x0 + 12.5                                                                # 26 wide
    for y in range(36, 76):                                                       # the cap
        hw = 1 + (y - 36) * 14 / 39
        a, b = int(math.ceil(cx - hw)), int(math.floor(cx + hw))
        for x in range(a, b + 1):
            t = (x - a) / max(1, b - a)
            c = SLATE_HI if t < 0.3 else (SLATE if t < 0.65 else SLATE_LO)
            d.point((x, y), fill=SLATE_LO if (y % 4 == 3 and t < 0.65) else c)
    d.rectangle([x0 + 12, 31, x0 + 13, 36], fill=STONE_DK); d.point((x0 + 12, 31), fill=GOLD)
    brick(d, x0, 80, x0 + 25, 203)
    brick(d, x0 + 19, 80, x0 + 25, 203, shade=True)
    d.rectangle([x0, 80, x0 + 5, 203], fill=BRICK_HI)                             # the lit face
    for y in range(82, 203, 3):
        d.line([(x0, y), (x0 + 5, y)], fill=BRICK)
    cornice(d, x0 - 1, x0 + 26, 76)
    band(d, x0, x0 + 25, 104, 3); band(d, x0, x0 + 25, 138); band(d, x0, x0 + 25, 168)
    plinth(d, x0 - 1, x0 + 26, 204, 213)
    arch(d, x0 + 9, x0 + 16, 86, 99, rail=False)
    arch(d, x0 + 9, x0 + 16, 113, 130)
    sash(d, x0 + 9, x0 + 16, 145, 161, lit=True)
    sash(d, x0 + 9, x0 + 16, 176, 193)


def pavilion(lay, d, x0):
    """A domed end pavilion, three cells wide: a brick block standing forward
    of the wings, an octagonal drum, a slate dome with copper ribs."""
    cx = x0 + 47.5
    # ---- the dome -------------------------------------------------------------------
    for y in range(16, 53):
        t = (52 - y) / 37
        hw = 38 * (1 - t ** 2.2) ** 0.62
        a, b = int(math.ceil(cx - hw)), int(math.floor(cx + hw))
        for x in range(a, b + 1):
            rel = (x - cx) / max(1.0, hw)                                         # -1 .. 1 across the dome
            c = SLATE_HI if rel < -0.42 else (SLATE if rel < 0.36 else SLATE_LO)
            if y % 4 == 3:
                c = SLATE if c == SLATE_HI else SLATE_LO
            d.point((x, y), fill=c)
        for rel, c in ((-0.42, GREEN_HI), (0.36, GREEN), (-0.86, GREEN_HI), (0.84, GREEN_LO)):   # the ribs
            d.point((int(round(cx + rel * hw)), y), fill=c)
    disc(d, cx, 38, 5.5, CREAM); disc(d, cx, 38, 4, GLASS)                        # a round window in its face
    d.line([(x0 + 45, 36), (x0 + 47, 36)], fill=GLASS_HI)
    d.rectangle([x0 + 43, 9, x0 + 52, 16], fill=GREEN); d.rectangle([x0 + 49, 9, x0 + 52, 16], fill=GREEN_LO)
    d.line([(x0 + 43, 9), (x0 + 52, 9)], fill=GREEN_HI)                           # the copper lantern
    d.rectangle([x0 + 45, 6, x0 + 50, 8], fill=GREEN_LO)
    d.rectangle([x0 + 47, 1, x0 + 48, 5], fill=STONE_DK); d.point((x0 + 47, 1), fill=GOLD)
    # ---- the drum: three of its eight faces ----------------------------------------
    brick(d, x0 + 10, 56, x0 + 85, 85)
    brick(d, x0 + 68, 56, x0 + 85, 85, shade=True)
    d.rectangle([x0 + 10, 56, x0 + 27, 85], fill=BRICK_HI)
    for y in range(58, 86, 3):
        d.line([(x0 + 10, y), (x0 + 27, y)], fill=BRICK)
    cornice(d, x0 + 8, x0 + 87, 52)
    for wx in (15, 33, 44, 55, 73):
        arch(d, x0 + wx, x0 + wx + 7, 62, 78, lit=wx == 44, rail=False)
    band(d, x0 + 10, x0 + 85, 83, 3)
    # ---- the roof the drum stands on -------------------------------------------------
    slate(d, [(y, x0 + 6 - (y - 86) // 2, x0 + 89 + (y - 86) // 2) for y in range(86, 100)])
    for y in range(86, 100):
        a = x0 + 6 - (y - 86) // 2
        d.line([(a, y), (a + 18, y)], fill=SLATE_HI if y % 4 != 3 else SLATE)
    # ---- the block, standing forward: its foot is lower than the wings' ----------
    for bx, shade in ((x0 - 9, False), (x0 + 96, True)):                          # a buttress at each corner: with
        brick(d, bx, 116, bx + 8, 235, shade=shade)                               # them the block's foot is as wide
        d.rectangle([bx, 112, bx + 8, 115], fill=CREAM_LO if shade else CREAM)    # as the line art's was, on the
        d.line([(bx, 112), (bx + 8, 112)], fill=CREAM if shade else WHITE)        # cells Palace keeps solid (#259)
    brick(d, x0, 108, x0 + 95, 235)
    brick(d, x0 + 88, 108, x0 + 95, 235, shade=True)
    cornice(d, x0 - 2, x0 + 97, 100)
    d.rectangle([x0 - 2, 104, x0 + 97, 107], fill=CREAM_LO); d.line([(x0 - 2, 107), (x0 + 97, 107)], fill=CREAM_DK)
    quoins(d, x0, 110, 234, 4); quoins(d, x0 + 92, 110, 234, 4, shade=True)
    band(d, x0 - 9, x0 + 104, 136); band(d, x0 - 9, x0 + 104, 166, 3); band(d, x0 - 9, x0 + 104, 200, 3)
    plinth(d, x0 - 10, x0 + 105, 236, 247)
    disc(d, cx, 121, 9.5, CREAM_DK); disc(d, cx, 121, 8.5, CREAM); disc(d, cx, 121, 6.5, WHITE)     # the clock
    for h in range(12):
        a = math.radians(h * 30)
        d.point((int(round(cx + 5.5 * math.sin(a))), int(round(121 - 5.5 * math.cos(a)))), fill=CREAM_DK)
    d.line([(x0 + 47, 121), (x0 + 44, 119)], fill=INK); d.line([(x0 + 48, 121), (x0 + 50, 116)], fill=INK)
    for wx in (11, 73):                                                           # the outer bays
        arch(d, x0 + wx, x0 + wx + 11, 112, 130)
        arch(d, x0 + wx, x0 + wx + 11, 142, 160, lit=wx == 73)
        sash(d, x0 + wx, x0 + wx + 11, 174, 193)
        arch(d, x0 + wx, x0 + wx + 11, 208, 228, rail=False)
    for wx in (32, 52):                                                           # the middle bay
        sash(d, x0 + wx, x0 + wx + 11, 143, 160, lit=wx == 32)
        sash(d, x0 + wx, x0 + wx + 11, 174, 193)
    arch(d, x0 + 32, x0 + 63, 206, 230)                                           # the hall's big window
    for x in (x0 + 39, x0 + 55):
        d.line([(x, 212), (x, 230)], fill=CREAM)


def centre(lay, d):
    """The centre block, five cells wide: a slate roof with a copper crest, a
    brick gable with one large lit window, the stone porch and the door."""
    x0, x1, cx = 576, 735, 655.5
    # ---- the roof --------------------------------------------------------------------
    rows = [(y, x0 + 2 + (103 - y) * 30 // 59, x1 - 2 - (103 - y) * 30 // 59) for y in range(44, 104)]
    slate(d, rows)
    for y, a, b in rows:
        d.line([(a, y), (a + 22, y)], fill=SLATE_HI if y % 4 != 3 else SLATE)
        d.point((a, y), fill=GREEN_HI); d.point((b, y), fill=GREEN_LO)
    d.rectangle([608, 41, 703, 43], fill=GREEN); d.line([(608, 41), (703, 41)], fill=GREEN_HI)     # the crest
    for x in range(610, 703, 6):
        d.line([(x, 37), (x, 40)], fill=GREEN_LO)
    d.line([(608, 37), (703, 37)], fill=GREEN)
    for x in (608, 702):
        d.rectangle([x, 30, x + 1, 40], fill=STONE_DK); d.point((x, 30), fill=GOLD)
    # ---- the gable ---------------------------------------------------------------------
    rows = [(y, int(math.ceil(cx - 3 - (y - 10) * 0.56)), int(math.floor(cx + 3 + (y - 10) * 0.56)))
            for y in range(10, 104)]
    clipped(lay, rows, lambda pd: brick(pd, 596, 10, 715, 103))
    for y, a, b in rows:
        d.line([(a - 2, y), (a + 1, y)], fill=CREAM); d.point((a - 2, y), fill=WHITE)             # the coping
        d.line([(b - 1, y), (b + 2, y)], fill=CREAM_LO)
    d.rectangle([652, 6, 659, 10], fill=CREAM); d.line([(652, 6), (659, 6)], fill=WHITE)
    d.rectangle([655, 1, 656, 5], fill=STONE_DK); d.point((655, 1), fill=GOLD)
    disc(d, cx, 30, 6.5, CREAM); disc(d, cx, 30, 5, GOLD); disc(d, cx, 30, 2.5, RED)               # a roundel
    arch(d, 640, 671, 46, 94, lit=True)                                           # the large window
    for x in (647, 664):
        d.line([(x, 52), (x, 94)], fill=CREAM)
    for y in (74, 84):
        d.line([(640, y), (671, y)], fill=CREAM)
    # ---- the wall ----------------------------------------------------------------------
    brick(d, x0, 108, x1, 199)
    brick(d, x1 - 7, 108, x1, 199, shade=True)
    cornice(d, x0 - 2, x1 + 2, 100)
    d.rectangle([x0 - 2, 104, x1 + 2, 107], fill=CREAM_LO); d.line([(x0 - 2, 107), (x1 + 2, 107)], fill=CREAM_DK)
    band(d, x0, x1, 138); band(d, x0, x1, 168)
    plinth(d, x0, x1, 200, GROUND)
    quoins(d, x0, 110, 198, 4); quoins(d, x1 - 3, 110, 198, 4, shade=True)
    quoins(d, 620, 110, 198); quoins(d, 689, 110, 198)
    for i, x in enumerate((586, 603)):
        for wx in (x, mirror(x, 9)):
            storeys(d, wx, i + (4 if wx > cx else 0))
    for x in (631, 651, 671):                                                     # over the porch
        arch(d, x, x + 9, 113, 131, lit=x == 651)
        sash(d, x, x + 9, 145, 161, lit=x != 651)
    # ---- the porch: stone piers, the name over the doorway, the door (cell 20,7) ---
    d.rectangle([624, 176, 687, 255], fill=CREAM)
    d.rectangle([682, 190, 687, 255], fill=CREAM_LO)
    for x in (624, 672):                                                          # the piers' joints
        for y in range(196, 250, 6):
            d.line([(x, y), (x + 15, y)], fill=CREAM_LO)
        d.line([(x, 190), (x, 255)], fill=WHITE)
        d.rectangle([x, 248, x + 15, 255], fill=STONE); d.line([(x, 248), (x + 15, 248)], fill=WHITE)
    d.rectangle([683, 248, 687, 255], fill=STONE_LO)
    d.rectangle([622, 174, 689, 177], fill=CREAM); d.line([(622, 174), (689, 174)], fill=WHITE)
    d.line([(622, 177), (689, 177)], fill=CREAM_LO)
    d.rectangle([636, 180, 675, 189], fill=NAVY)                                  # the name board
    text(d, 'TOKYO', 656 - text_w('TOKYO') // 2 - 1, 181, GOLD)
    d.line([(624, 191), (687, 191)], fill=CREAM_LO)
    round_head(d, 640, 671, 196, 255, DARK)                                       # the doorway
    round_head(d, 642, 669, 198, 221, WARM)                                       # its fanlight
    for x in (648, 655, 656, 663):
        d.line([(x, 199), (x, 221)], fill=DARK)
    d.rectangle([640, 222, 671, 223], fill=DARK)
    glass_door(d, 640, 224, 671, 255)


def station():
    im, d = canvas(41, 8)                # 1312 x 256
    wings(im, d)
    outline(im)
    for x in (384, mirror(384, 32)):
        layer(im, lambda lay, ld, x=x: bay(lay, ld, x))
    for x in (4, mirror(4, 26)):
        layer(im, lambda lay, ld, x=x: turret(lay, ld, x))
    layer(im, centre)
    for x in (128, mirror(128, 96)):
        layer(im, lambda lay, ld, x=x: pavilion(lay, ld, x))
    return im


# ------------------------------------------------------------------------------
def build():
    """{key: the doubled picture}. The feet are cut from the tower."""
    double = lambda im: im.resize((im.width * 2, im.height * 2), Image.NEAREST)   # noqa: E731
    big = double(tower())
    return {'tokyo-tower_0_0': big,
            'tokyo-tower-feet': big.crop((0, big.height - 6 * C, big.width, big.height)),
            'tokyo-station_0_0': double(station())}


def sheet(built, out):
    """The pictures on one paving-coloured sheet (a preview, not part of the game)."""
    keys = ('tokyo-station_0_0', 'tokyo-tower_0_0', 'tokyo-tower-feet')
    im = Image.new('RGBA', (built[keys[0]].width + 48, sum(built[k].height for k in keys) + 24 * 4), rgb('9aa6b4'))
    y = 24
    for k in keys:
        im.alpha_composite(built[k], (24, y)); y += built[k].height + 24
    im.save(out)
    print('sheet ->', out)


def main():
    built = build()
    for key, im in built.items():
        im.save(f'{SPR}/{key}.png')
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    if '--sheet' in sys.argv:
        sheet(built, sys.argv[sys.argv.index('--sheet') + 1])


if __name__ == '__main__':
    main()
