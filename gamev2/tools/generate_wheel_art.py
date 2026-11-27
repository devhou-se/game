#!/usr/bin/env python3
"""generate_wheel_art.py — a ride on the Dotonbori ferris wheel: the gondola
you board at its foot, and the view from inside one on the way round (issue #242).

In the manner of tools/generate_tower_deck_art.py, whose view helpers (sky,
cloud, water, block, tree, lamp, person, picture, register_pictures, the
preview's night / framed / sheet) it imports: shaded pixel art drawn at half
size and pixel-doubled, every scatter seeded, nothing lettered, so a re-run is
identical on any machine.

The sprite:
  wheel-boarding          2x2 a gondola down at the ground with its door open,
                          on a boarding step: the fourth of the three that hang
                          down the wheel's west side (bump it: one turn of the
                          wheel, src/ViewRide.js). It is one of the wheel's own
                          gondolas, cut from assets/sprites/dotonbori-wheel_0_0.png
                          (4 px to the pixel, as that sheet is drawn), so it is the
                          wheel's red and the wheel's glass whatever they become.

Pictures for the ride (whole images, centred, no tile name; saved pixel-doubled):
  view-gondola            640x640 the inside of a gondola: the red shell, a wide
                          window with a grab rail across it, the two seats (the
                          window is a hole: ViewRide.RIDES.wheel.window)
  view-dotonbori-near     looking south over the canal: at the bottom the bank
                          you left, the canal with its two bridges and a
                          sightseeing boat, the river walk and the fronts across
                          it with their boards; then the roofs behind, street
                          after street, with Tsutenkaku standing over the last
                          of them (here and not in `far`, so that it is lit at
                          night). Transparent above its skyline.
  view-dotonbori-far      the plain out to the hills, and the day sky. Opaque.
  view-dotonbori-lights   the lit pixels of `near` and nothing else: the boards,
                          windows, lamps, the boat, what the boards throw on the water
The ride pans `near` and `far` behind the window as the gondola rises and
comes down again (ViewRide.height), and slides them sideways as the wheel
carries it across (ViewRide.drift): the three layers are 64 px wider than the
window, 32 px to spare either side.

Run from gamev2/:  python3 tools/generate_wheel_art.py [--preview out.png]
Needs Pillow. Registers the sprite in config.json spriteMetadata + tileNames,
the pictures in spriteMetadata alone.
"""
import math
import random
import sys

from PIL import Image, ImageDraw

from generate_pub_art import INK, WHITE, BRASS, BRASS_HI, BRASS_DK, STEEL, STEEL_HI, STEEL_DK, GLOW, GLOW_HI, new, box, mix, bar, register
from generate_tower_deck_art import (
    HAZE, SEA, SEA_DEEP, GRASS, GRASS_HI, GRASS_DK, PAVE, PAVE_HI, PAVE_DK, ROAD, ROAD_DK, LINE, GLASS, GLASS_HI, GLASS_DK,
    WALLS, RED, RED_HI, LIT, LIT_HI, LIT_COOL, LIT_RED,
    sky, cloud, water, block, tree, lamp, person, picture, register_pictures, night, framed, sheet,
)

# ---- the boarding gondola ---------------------------------------------------------------------
WHEEL = 'assets/sprites/dotonbori-wheel_0_0.png'
POD = (0, 512, 128, 640)        # the lowest gondola of the wheel's west side, in the wheel's own px
PX = 4                          # the wheel's sheet is drawn 4 px to the pixel
# the wheel's own colours (the sheet's), for what is added to the gondola
W_INK, W_RED, W_RED_HI, W_PALE, W_DARK, W_WOOD, W_WOOD_DK = (8, 13, 22), (209, 107, 86), (246, 165, 131), (255, 226, 224), (42, 38, 54), (133, 85, 62), (113, 65, 42)
W_GLASS, W_GLASS_HI, W_GLASS_DK = (90, 134, 222), (125, 185, 250), (66, 95, 170)


def boarding():
    """The gondola at the ground, 64x64: the wheel's own pod, its glass swung open to the
    west, the seat inside, a step under the door."""
    sheet_ = Image.open(WHEEL).convert('RGBA')
    pod = sheet_.crop(POD).resize((32, 32), Image.NEAREST)
    assert pod.resize((128, 128), Image.NEAREST).tobytes() == sheet_.crop(POD).tobytes(), 'the wheel is no longer drawn 4 px to the pixel'
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # its shade on the paving, and the step you board from
    d.ellipse([8, 24, 30, 30], fill=(0, 0, 0, 70))
    d.rectangle([12, 26, 27, 29], fill=W_WOOD, outline=W_INK)
    d.line([13, 27, 26, 27], fill=(228, 206, 204))
    for x in (15, 19, 23):
        d.point((x, 28), fill=W_WOOD_DK)
    im.alpha_composite(pod)
    # the doorway: where the glass was, the dark inside and the seat across it
    glass = [(x, y) for y in range(32) for x in range(32) if pod.getpixel((x, y))[:3] in (W_GLASS, W_GLASS_HI, W_GLASS_DK, (187, 233, 255))]
    for x, y in glass:
        im.putpixel((x, y), W_DARK + (255,))
    top, bottom = min(y for _, y in glass), max(y for _, y in glass)
    left, right = min(x for x, y in glass if y == bottom - 2), max(x for x, y in glass if y == bottom - 2)
    d.line([left + 1, bottom - 3, right - 1, bottom - 3], fill=W_WOOD)                # the seat's back
    d.line([left + 1, bottom - 2, right - 1, bottom - 2], fill=W_RED_HI)              # its cushion
    d.line([left + 1, bottom - 1, right - 1, bottom - 1], fill=W_RED)
    d.point(((left + right) // 2, top + 1), fill=(255, 222, 150))                     # the lamp inside
    d.point(((left + right) // 2 + 1, top + 1), fill=(255, 222, 150))
    # the glass, swung out on its hinge
    d.rectangle([2, top - 1, 6, bottom], fill=W_GLASS, outline=W_INK)
    d.line([3, top, 3, bottom - 1], fill=W_GLASS_HI)
    d.line([5, top + 2, 5, bottom - 1], fill=W_GLASS_DK)
    d.point((4, top + 1), fill=(187, 233, 255))
    d.line([6, top + 2, 7, top + 2], fill=W_INK)
    d.line([6, bottom - 2, 7, bottom - 2], fill=W_INK)
    return im.resize((64, 64), Image.NEAREST)


# ---- the view south from the wheel ---------------------------------------------------------------
VW = 288                    # the three layers as drawn: the window, and 16 px of drift either side
NEAR_H, FAR_H = 400, 240    # the taller one moves further (ViewRide.pan)
WIN = (32, 112, 256, 160)   # the hole in view-gondola: x, y, w, h as drawn (doubled: ViewRide.RIDES.wheel.window)
HORIZON = 92                # far's row where the plain meets the hills
SKYLINE = 119               # near's first row of ground: above it only roofs, and the tower
FRONT = 318                 # the feet of the fronts along the canal
CANAL = (332, 371)          # the water's rows
BANK = 386                  # the paving of the bank you left starts here
STREET = 86                 # the middle column of the street that runs south from the first bridge
BRIDGES = ((74, 98, (206, 206, 216), (146, 150, 190)), (238, 260, (196, 206, 200), (70, 120, 110)))    # x0, x1, deck, parapet
TOWER = (196, 122)          # Tsutenkaku: its middle column, the row its feet are on

BOARDS = [(250, 200, 70), (244, 96, 84), (90, 150, 230), (96, 190, 150), (246, 240, 226), (236, 130, 180)]


def far_layer():
    rnd = random.Random(24202)
    im, d = new(VW, FAR_H)
    sky(d, VW, 0, HORIZON)
    for x, y, w in ((14, 34, 40), (92, 20, 52), (170, 50, 30), (226, 30, 44), (60, 62, 22), (254, 66, 20), (140, 70, 16)):
        cloud(d, x, y, w)
    # the hills the plain ends at, palest of all
    hill = mix((126, 156, 178), HAZE, 0.55)
    for x in range(VW):
        top = HORIZON - 5 - round(5 * math.sin(x / 37) + 3 * math.sin(x / 11 + 2) + 2 * math.sin(x / 5))
        d.line([x, max(top, HORIZON - 14), x, HORIZON], fill=hill)
    # the plain: streets, paler the further off
    for y in range(HORIZON + 1, FAR_H):
        t = (y - HORIZON) / (FAR_H - HORIZON)
        d.line([0, y, VW - 1, y], fill=mix(mix(PAVE_DK, HAZE, 0.78), mix(ROAD, HAZE, 0.4), t))
    # the one tall slab on the far side of town, over everything
    d.rectangle([232, HORIZON - 24, 241, HORIZON + 8], fill=mix(GLASS_HI, HAZE, 0.62))
    d.line([232, HORIZON - 24, 232, HORIZON + 8], fill=mix(WHITE, HAZE, 0.5))
    d.line([241, HORIZON - 24, 241, HORIZON + 8], fill=mix(GLASS, HAZE, 0.6))
    for y in range(HORIZON - 21, HORIZON + 6, 3):
        d.line([234, y, 239, y], fill=mix(GLASS, HAZE, 0.7))
    # block after block, out to the hills: each row's feet lower, its blocks bigger and clearer
    foot = HORIZON + 4
    while foot < FAR_H + 24:
        t = min(1.0, (foot - HORIZON) / (FAR_H - HORIZON))
        x = -rnd.randrange(0, 6)
        while x < VW:
            w = rnd.randrange(4 + round(t * 7), 8 + round(t * 12))
            block(d, None, rnd, x, foot + rnd.randrange(0, 3), w, rnd.randrange(3 + round(t * 10), 7 + round(t * 20)), rnd.choice(WALLS),
                  roof=rnd.choice((1, 2, 2)), pitch=(3, 3), pane=(1, 1), haze=0.82 - 0.4 * t, ink=False)
            x += w + rnd.randrange(0, 3)
        foot += 5 + round(t * 12)
    return im


def tsutenkaku(d, dl, x, foot):
    """Tsutenkaku, small and a long way off: splayed legs, the shaft with its sign down it, the
    two-tier head, the mast. Lit at night: the sign, the head, the light on the mast."""
    steel, dk, hi = mix((204, 208, 220), HAZE, 0.3), mix((120, 126, 150), HAZE, 0.3), mix(WHITE, HAZE, 0.15)
    edge = mix(INK, HAZE, 0.35)
    d.polygon([(x - 8, foot), (x - 3, foot - 17), (x + 3, foot - 17), (x + 8, foot)], fill=steel, outline=edge)
    d.polygon([(x - 4, foot), (x - 1, foot - 11), (x + 1, foot - 11), (x + 4, foot)], fill=(0, 0, 0, 0))     # between the legs
    d.line([x - 4, foot, x - 1, foot - 11], fill=edge)
    d.line([x + 4, foot, x + 1, foot - 11], fill=edge)
    for y, w in ((foot - 5, 6), (foot - 11, 4)):
        d.line([x - w, y, x + w, y], fill=dk)
    d.rectangle([x - 3, foot - 31, x + 3, foot - 17], fill=steel, outline=edge)
    d.line([x - 2, foot - 30, x - 2, foot - 18], fill=hi)
    d.rectangle([x - 1, foot - 29, x + 1, foot - 19], fill=mix(RED, HAZE, 0.2))
    d.rectangle([x - 7, foot - 36, x + 7, foot - 31], fill=steel, outline=edge)
    d.line([x - 6, foot - 34, x + 6, foot - 34], fill=mix(GLASS, HAZE, 0.2))
    d.rectangle([x - 5, foot - 41, x + 5, foot - 36], fill=hi, outline=edge)
    d.line([x - 4, foot - 39, x + 4, foot - 39], fill=mix(GLASS, HAZE, 0.2))
    d.rectangle([x - 2, foot - 44, x + 2, foot - 41], fill=steel, outline=edge)
    d.line([x, foot - 52, x, foot - 44], fill=edge)
    for y in range(foot - 29, foot - 18, 2):
        dl.line([x - 1, y, x + 1, y], fill=LIT_RED if (y // 2) % 2 else LIT_HI)
    dl.line([x - 6, foot - 34, x + 6, foot - 34], fill=LIT_HI)
    dl.line([x - 4, foot - 39, x + 4, foot - 39], fill=LIT_COOL)
    dl.point((x, foot - 52), fill=LIT_RED)
    for dx in (-7, 7):
        dl.point((x + dx, foot - 1), fill=LIT)


def motif(t, kind, x, y, w, h, ink):
    """What a board shows, drawn on `t` (the picture, then its lights): nothing is lettered."""
    cx, cy = x + w // 2, y + h // 2
    if kind == 'sun':
        for a in range(0, 360, 30):
            t.line([cx, cy, cx + round((h // 2 - 1) * 1.5 * math.cos(math.radians(a))), cy + round((h // 2 - 1) * math.sin(math.radians(a)))], fill=ink)
        t.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(250, 250, 246))
    elif kind == 'fish':
        t.ellipse([cx - 6, cy - 3, cx + 4, cy + 3], fill=ink)
        t.polygon([(cx + 3, cy), (cx + 8, cy - 3), (cx + 8, cy + 3)], fill=ink)
        t.point((cx - 4, cy - 1), fill=(250, 250, 246))
    elif kind == 'octopus':
        t.ellipse([cx - 5, cy - 5, cx + 5, cy + 2], fill=ink)
        for dx in (-5, -2, 1, 4):
            t.line([cx + dx, cy + 2, cx + dx + (1 if dx > 0 else -1), cy + 5], fill=ink)
        t.point((cx - 2, cy - 2), fill=(250, 250, 246))
        t.point((cx + 2, cy - 2), fill=(250, 250, 246))
    elif kind == 'stripes':
        for i, sx in enumerate(range(x + 2, x + w - 2, 3)):
            t.rectangle([sx, y + 2, sx + 1, y + h - 3], fill=BOARDS[i % len(BOARDS)])
    elif kind == 'star':
        t.polygon([(cx, cy - 5), (cx + 2, cy - 1), (cx + 6, cy - 1), (cx + 3, cy + 1), (cx + 4, cy + 5), (cx, cy + 3), (cx - 4, cy + 5),
                   (cx - 3, cy + 1), (cx - 6, cy - 1), (cx - 2, cy - 1)], fill=ink)
    elif kind == 'rings':
        for r in (5, 3, 1):
            t.ellipse([cx - r * 1.4, cy - r, cx + r * 1.4, cy + r], outline=ink)
    elif kind == 'bars':
        for sy in range(y + 2, y + h - 2, 3):
            t.line([x + 2, sy, x + w - 3, sy], fill=ink)


def board(d, dl, x, y, w, h, ground, kind, ink):
    """A signboard on a front: its ground and what is on it, the same on the lights picture."""
    for t in (d, dl):
        t.rectangle([x, y, x + w - 1, y + h - 1], fill=ground)
        motif(t, kind, x, y, w, h, ink)
    d.rectangle([x - 1, y - 1, x + w, y + h], outline=INK)


def near_layers():
    """The near layer and its lights: (near, lights)."""
    rnd = random.Random(2422)
    im, d = new(VW, NEAR_H)
    li, dl = new(VW, NEAR_H)

    def street_half(y):
        """Half the width of the street south from the bridge at row y: it narrows as it goes."""
        return 3 + round(9 * (y - SKYLINE) / (FRONT - SKYLINE))

    # ---- Tsutenkaku, behind the last roofs ---------------------------------------------------
    tsutenkaku(d, dl, *TOWER)

    # ---- the ground under the town: streets, paler the further off ---------------------------
    for y in range(SKYLINE, FRONT + 1):
        t = (y - SKYLINE) / (FRONT - SKYLINE)
        d.line([0, y, VW - 1, y], fill=mix(mix(ROAD, HAZE, 0.5), ROAD, t))
    for y in range(SKYLINE, FRONT + 1):                              # the street from the bridge
        hw, t = street_half(y), (y - SKYLINE) / (FRONT - SKYLINE)
        d.line([STREET - hw, y, STREET + hw, y], fill=mix(mix(PAVE, HAZE, 0.5), PAVE, t))
        if y % 9 < 5:
            d.point((STREET, y), fill=mix(mix(LINE, HAZE, 0.5), LINE, t))
    for y in range(SKYLINE + 14, FRONT - 6, 11):                     # its lamps, either side
        hw = street_half(y)
        for x in (STREET - hw + 1, STREET + hw - 1):
            dl.point((x, y), fill=LIT_HI)
            dl.point((x, y + 1), fill=LIT + (130,))

    # ---- the roofs: back rows first, each row's feet lower, its blocks bigger and clearer ----
    rows = [(125, (7, 13), (6, 10), 0.52), (137, (8, 15), (7, 11), 0.44), (151, (10, 18), (8, 13), 0.36), (167, (12, 21), (9, 15), 0.28),
            (186, (14, 25), (10, 17), 0.2), (208, (17, 30), (12, 20), 0.13), (234, (20, 36), (14, 23), 0.07), (264, (24, 40), (16, 26), 0.03)]
    for n, (foot, hs, ws, haze) in enumerate(rows):
        hw = street_half(foot) + 1
        x = -rnd.randrange(0, 8)
        while x < VW:
            w = rnd.randrange(*ws)
            if x < STREET + hw and x + w > STREET - hw:              # the street is left clear
                if STREET - hw - x >= ws[0]:
                    w = STREET - hw - x
                else:
                    x = STREET + hw
                    continue
            big = n >= 4
            block(d, dl, rnd, x, foot + rnd.randrange(0, 3), w, rnd.randrange(*hs), rnd.choice(WALLS), roof=rnd.choice((2, 3, 3, 4)) + (2 if big else 0),
                  pitch=(4, 4) if big else (3, 3), pane=(2, 2) if big else (1, 1), lit=0.42, haze=haze, ink=n >= 2)
            if big and rnd.random() < 0.3:                           # a sign down the side of one
                col = rnd.choice(BOARDS)
                sx, sy = x + w - 3, foot - rnd.randrange(12, 18)
                for t in (d, dl):
                    t.rectangle([sx, sy, sx + 1, sy + 8], fill=col)
            x += w + rnd.randrange(0, 3)
    for x, y, r in ((30, 196, 4), (140, 214, 5), (232, 190, 4), (272, 240, 5), (116, 246, 5), (182, 172, 3), (52, 160, 3)):
        tree(d, x, y, r, ink=False)

    # ---- the fronts along the canal, and their boards ----------------------------------------
    fronts = [(0, 30, 52, WALLS[2], 'stripes'), (32, 40, 62, WALLS[1], 'octopus'), (101, 37, 58, WALLS[4], 'sun'), (140, 32, 48, WALLS[0], 'fish'),
              (174, 30, 64, WALLS[3], 'star'), (206, 30, 54, WALLS[6], 'rings'), (263, 25, 60, WALLS[5], 'bars')]
    grounds = [(246, 240, 226), (246, 240, 226), (244, 96, 84), (90, 150, 230), (60, 62, 90), (250, 200, 70), (96, 190, 150)]
    inks = [INK, (244, 96, 84), (250, 200, 70), (250, 250, 246), (250, 200, 70), (244, 96, 84), (250, 250, 246)]
    for i, (x, w, h, wall, kind) in enumerate(fronts):
        top = block(d, dl, rnd, x, FRONT, w, h, wall, roof=7, pitch=(6, 7), pane=(4, 4), lit=0.55)
        bw, bh = min(w - 6, 26), 15
        bx, by = x + (w - bw) // 2, FRONT - h + 5
        board(d, dl, bx, by, bw, bh, grounds[i], kind, inks[i])
        d.rectangle([x + 2, top + 2, x + 2 + w // 4, top + 4], fill=mix(wall, INK, 0.3))                # plant on its roof
        # the shop at its foot: an awning, the lit window under it
        awn = BOARDS[(i * 2 + 1) % len(BOARDS)]
        d.rectangle([x + 2, FRONT - 9, x + w - 3, FRONT - 1], fill=GLASS_DK)
        dl.rectangle([x + 3, FRONT - 6, x + w - 4, FRONT - 2], fill=LIT)
        d.rectangle([x + 1, FRONT - 12, x + w - 2, FRONT - 9], fill=awn, outline=INK)
        for sx in range(x + 3, x + w - 3, 4):
            d.line([sx, FRONT - 11, sx, FRONT - 10], fill=WHITE)
        if i % 2 == 0:                                               # and a sign down its corner
            col = BOARDS[(i + 2) % len(BOARDS)]
            for t in (d, dl):
                t.rectangle([x + w - 5, by + bh + 4, x + w - 3, FRONT - 16], fill=col)
            d.rectangle([x + w - 6, by + bh + 3, x + w - 2, FRONT - 15], outline=INK)

    # ---- the river walk under them -----------------------------------------------------------
    d.rectangle([0, FRONT + 1, VW - 1, CANAL[0] - 1], fill=(214, 196, 160))
    d.line([0, FRONT + 1, VW - 1, FRONT + 1], fill=(238, 224, 192))
    for x in range(0, VW, 6):
        d.line([x, FRONT + 2, x, CANAL[0] - 3], fill=(196, 176, 140))
    d.line([0, CANAL[0] - 3, VW - 1, CANAL[0] - 3], fill=STEEL_DK)                                       # its rail
    for x in range(3, VW, 8):
        d.line([x, CANAL[0] - 4, x, CANAL[0] - 2], fill=STEEL_DK)
    d.line([0, CANAL[0] - 1, VW - 1, CANAL[0] - 1], fill=INK)
    for x in range(14, VW, 30):
        if not any(x0 - 4 < x < x1 + 4 for x0, x1, _, _ in BRIDGES):
            lamp(d, dl, x, CANAL[0] - 4, 8)
    for i, x in enumerate((8, 22, 46, 58, 110, 126, 150, 168, 186, 214, 226, 268, 280)):
        person(d, x, FRONT + 8 + (i % 3), ((236, 96, 96), WHITE, (90, 150, 230), (250, 200, 70))[i % 4])

    # ---- the canal ---------------------------------------------------------------------------
    water(d, rnd, VW, CANAL[0], CANAL[1], far=mix(SEA, GLASS_DK, 0.25), near=SEA_DEEP, glints=0.02)
    d.line([0, CANAL[0], VW - 1, CANAL[0]], fill=mix(SEA_DEEP, INK, 0.5))                                # the wall's shade
    for i, (x, w, h, wall, kind) in enumerate(fronts):                                                 # what the boards throw on it
        col = grounds[i] if grounds[i] != (60, 62, 90) else inks[i]
        for y in range(CANAL[0] + 3, CANAL[0] + 20, 2):
            a = 150 - (y - CANAL[0]) * 6
            sx = x + 5 + rnd.randrange(0, 4)
            dl.line([sx, y, sx + w - 12 - rnd.randrange(0, 5), y], fill=col + (a,))
    # the sightseeing boat, and a smaller one going the other way
    bx, by = 138, 348
    d.polygon([(bx, by + 3), (bx + 4, by + 9), (bx + 46, by + 9), (bx + 52, by + 3)], fill=(250, 200, 70), outline=INK)
    d.rectangle([bx + 6, by - 2, bx + 44, by + 3], fill=WHITE, outline=INK)
    d.line([bx + 7, by - 1, bx + 43, by - 1], fill=(244, 96, 84))
    for x in range(bx + 9, bx + 43, 5):
        d.rectangle([x, by + 1, x + 2, by + 2], fill=GLASS_DK)
        dl.rectangle([x, by + 1, x + 2, by + 2], fill=LIT_HI)
    for i in range(8):
        d.line([bx + 54 + i * 5, by + 9 + i // 3, bx + 57 + i * 5, by + 9 + i // 3], fill=(214, 236, 255))
    dl.point((bx - 1, by + 5), fill=LIT_HI)
    sx, sy = 34, 360
    d.polygon([(sx, sy), (sx + 3, sy + 5), (sx + 18, sy + 5), (sx + 20, sy)], fill=WHITE, outline=INK)
    d.rectangle([sx + 8, sy - 3, sx + 14, sy], fill=(90, 150, 230), outline=INK)
    for i in range(5):
        d.line([sx - 4 - i * 5, sy + 5 + i // 2, sx - 1 - i * 5, sy + 5 + i // 2], fill=(214, 236, 255))
    dl.point((sx + 21, sy + 2), fill=LIT_HI)

    # ---- the bank you left: the rocks, the grass, the paving ----------------------------------
    d.rectangle([0, CANAL[1] + 1, VW - 1, NEAR_H - 1], fill=GRASS)
    for x in range(-2, VW, 7):                                       # the rock rim
        d.ellipse([x, CANAL[1] - 1, x + 7, CANAL[1] + 5], fill=(244, 244, 248) if (x // 7) % 2 else (214, 218, 232), outline=INK)
        d.line([x + 2, CANAL[1] + 1, x + 4, CANAL[1] + 1], fill=WHITE)
    for _ in range(90):
        x, y = rnd.randrange(VW), rnd.randrange(CANAL[1] + 7, BANK - 1)
        d.line([x, y, x + rnd.randrange(1, 4), y], fill=rnd.choice((GRASS_HI, GRASS_HI, GRASS_DK)))
    d.rectangle([0, BANK, VW - 1, NEAR_H - 1], fill=PAVE)
    d.line([0, BANK, VW - 1, BANK], fill=PAVE_HI)
    for y in range(BANK + 4, NEAR_H, 5):                             # grey brick
        d.line([0, y, VW - 1, y], fill=PAVE_DK)
        for x in range((y // 5 % 2) * 5, VW, 10):
            d.line([x, y - 4, x, y - 1], fill=PAVE_DK)

    # ---- the bridges: over the walk's edge, the water and the rocks, and on down the bank -----
    for x0, x1, deck, rail in BRIDGES:
        d.rectangle([x0 + 3, CANAL[0] + 1, x1 + 5, CANAL[1]], fill=mix(SEA_DEEP, INK, 0.35))            # its shade on the water
        d.rectangle([x0, CANAL[0] - 6, x1, NEAR_H - 1], fill=deck)
        d.rectangle([x0 + 4, CANAL[1] + 6, x1 - 4, NEAR_H - 1], fill=ROAD)
        for y in range(CANAL[1] + 9, NEAR_H, 8):
            d.line([(x0 + x1) // 2, y, (x0 + x1) // 2, y + 3], fill=LINE)
        for x in (x0, x1 - 2):
            d.rectangle([x, CANAL[0] - 6, x + 2, CANAL[1] + 5], fill=rail, outline=INK)
            for y in range(CANAL[0] - 2, CANAL[1] + 3, 6):
                d.point((x + 1, y), fill=mix(rail, WHITE, 0.5))
        d.line([x0 + 3, CANAL[0] - 6, x1 - 3, CANAL[0] - 6], fill=mix(deck, INK, 0.25))
        for y in range(CANAL[0], CANAL[1], 7):
            d.line([x0 + 4, y, x1 - 4, y], fill=mix(deck, INK, 0.12))
        for x in (x0 - 1, x1 + 1):
            for foot in (CANAL[0] - 2, CANAL[1] + 8):
                lamp(d, dl, x, foot, 7)
    for i, (x, y) in enumerate(((80, 344), (90, 356), (84, 366), (244, 350), (252, 340), (248, 364))):
        person(d, x, y, ((236, 96, 96), WHITE, (90, 150, 230))[i % 3])

    # ---- on the bank: lamps, a tree or two, who is waiting for the wheel -----------------------
    for x, y, r in ((18, 384, 6), (214, 383, 6), (282, 384, 5)):
        tree(d, x, y, r)
    for x in (48, 128, 190, 228):
        lamp(d, dl, x, NEAR_H - 6, 16)
    for i, (x, y) in enumerate(((30, 396), (62, 398), (118, 396), (142, 398), (168, 397), (206, 396), (270, 398))):
        person(d, x, y, ((236, 96, 96), WHITE, (90, 150, 230), (250, 200, 70))[i % 4], s=2)
    return im, li


# ---- the gondola from inside ---------------------------------------------------------------------
SHELL, SHELL_HI, SHELL_DK, SHELL_PALE, SHELL_PALE_DK = RED, RED_HI, (160, 78, 66), (255, 226, 224), (228, 206, 204)
SEAT, SEAT_HI, SEAT_DK = (133, 85, 62), (176, 122, 88), (113, 65, 42)


def gondola_frame():
    """The gondola from inside, 320x320: you stand facing its window, the wheel's arm overhead."""
    body, d = new(320, 320)
    wx, wy, ww, wh = WIN
    # the shell: the ceiling and its lamp, the head of the wall, the wall round the window
    d.rectangle([0, 0, 319, 319], fill=SHELL)
    d.rectangle([0, 28, 319, 50], fill=SHELL_DK)
    d.line([0, 51, 319, 51], fill=INK)
    d.rectangle([0, 52, 319, 56], fill=SHELL_PALE)
    d.line([0, 57, 319, 57], fill=SHELL_PALE_DK)
    d.line([0, 58, 319, 58], fill=INK)
    d.rectangle([136, 35, 183, 45], fill=GLOW_HI, outline=INK)
    d.line([139, 46, 180, 46], fill=GLOW)
    for x in range(20, 300, 12):                                     # the shell's ribs
        if not 128 < x < 190:
            d.line([x, 31, x, 48], fill=mix(SHELL_DK, INK, 0.25))
    for x in (wx - 20, wx + ww + 19):                                # rivets down the wall either side
        for y in range(70, 292, 12):
            d.point((x, y), fill=SHELL_HI)
            d.point((x, y + 1), fill=SHELL_DK)
    for y in (64, 100):                                              # ...and across its head
        for x in range(wx - 8, wx + ww + 9, 12):
            d.point((x, y), fill=SHELL_HI)
            d.point((x, y + 1), fill=SHELL_DK)
    # on the head of the wall: a notice (the wheel, and which way it turns), a grille
    box(d, 62, 70, 96, 96, (246, 240, 226))
    d.ellipse([70, 73, 88, 91], outline=RED)
    for a in range(0, 360, 45):
        d.point((79 + round(9 * math.cos(math.radians(a))), 82 + round(9 * math.sin(math.radians(a)))), fill=GLASS)
    d.line([79, 82, 79, 93], fill=INK)
    box(d, 226, 72, 258, 94, SHELL_DK)
    for y in range(76, 92, 4):
        d.line([229, y, 255, y], fill=INK)
        d.line([229, y + 1, 255, y + 1], fill=SHELL)
    # under the window: the sill's wall, the two seats, the floor
    d.rectangle([0, wy + wh + 8, 319, 297], fill=SHELL_DK)
    d.rectangle([0, 286, 319, 290], fill=SHELL_PALE)
    d.line([0, 291, 319, 291], fill=SHELL_PALE_DK)
    for x0, x1 in ((6, 78), (241, 313)):
        d.rectangle([x0, 268, x1, 297], fill=SEAT, outline=INK)
        d.rectangle([x0 + 1, 269, x1 - 1, 276], fill=SEAT_HI)
        d.line([x0 + 1, 277, x1 - 1, 277], fill=SEAT_DK)
        for x in range(x0 + 12, x1 - 6, 14):
            d.line([x, 279, x, 295], fill=SEAT_DK)
    d.rectangle([0, 298, 319, 319], fill=(52, 54, 74))
    d.line([0, 298, 319, 298], fill=INK)
    for y in range(303, 318, 5):
        for x in range(10 + (y % 2) * 3, 312, 7):
            d.point((x, y), fill=(84, 88, 112))
    # the window's frame, and the glass: a hole
    bar(d, wx - 8, wy - 8, wx + ww + 7, wy + wh + 7, SHELL_PALE, WHITE, SHELL_PALE_DK)
    d.rectangle([wx - 2, wy - 2, wx + ww + 1, wy + wh + 1], fill=SHELL_DK, outline=INK)
    body.paste((0, 0, 0, 0), (wx, wy, wx + ww, wy + wh))
    for x in (wx + ww // 3, wx + 2 * ww // 3):                       # two glazing bars
        d.rectangle([x - 1, wy, x + 1, wy + wh - 1], fill=SHELL_DK)
        d.line([x - 1, wy, x - 1, wy + wh - 1], fill=SHELL)
    for x0, y0, n in ((wx + 16, wy + 6, 30), (wx + 24, wy + 6, 18), (wx + 196, wy + 30, 26)):          # light on the glass
        for i in range(n):
            d.point((x0 + i // 2, y0 + i), fill=(255, 255, 255, 46))
    # the grab rail across it
    for x in (wx + 12, wx + ww - 16):
        box(d, x, wy + wh - 30, x + 3, wy + wh - 1, STEEL_DK)
    bar(d, wx - 2, wy + wh - 36, wx + ww + 1, wy + wh - 30, BRASS, BRASS_HI, BRASS_DK)

    # cut to the pod's round shell, and hung from the wheel's arm
    im, d = new(320, 320)
    mask = Image.new('L', (320, 320), 0)
    ImageDraw.Draw(mask).rounded_rectangle([2, 28, 317, 319], radius=44, fill=255)
    bar(d, 108, 16, 211, 27, STEEL, STEEL_HI, STEEL_DK)
    d.rectangle([150, 0, 169, 20], fill=STEEL, outline=INK)
    d.line([152, 1, 152, 19], fill=STEEL_HI)
    d.line([167, 1, 167, 19], fill=STEEL_DK)
    for x in (116, 203):
        d.ellipse([x - 3, 19, x + 3, 25], fill=STEEL_DK, outline=INK)
    im.paste(body, (0, 0), mask)
    d.rounded_rectangle([2, 28, 317, 319], radius=44, outline=INK)
    d.arc([4, 30, 92, 118], 180, 270, fill=SHELL_HI)                 # light along the shell's shoulders
    d.arc([227, 30, 315, 118], 270, 360, fill=mix(SHELL_DK, INK, 0.3))
    return im


def sprites():
    return {'wheel-boarding': boarding}


def main(argv):
    register(sprites())
    near, lights = near_layers()
    frame = gondola_frame()
    pictures = {'view-gondola': frame, 'view-dotonbori-near': near, 'view-dotonbori-far': far_layer(), 'view-dotonbori-lights': lights}
    for key, im in pictures.items():
        picture(key, im)
    register_pictures(pictures)

    if '--preview' in argv:
        # the ride as ViewRide draws it, at the foot, half way up and the top, by day and by night;
        # then the layers, and the gondola beside the one it is cut from
        day = [pictures['view-dotonbori-far'], near]
        dark = [night(pictures['view-dotonbori-far']), night(near), lights]
        ims = [framed(frame, WIN, layers, h) for layers in (day, dark) for h in (0, 0.5, 1)]
        glow = night(near)
        glow.alpha_composite(lights)
        ims += [near, glow, pictures['view-dotonbori-far'], lights]
        pod = boarding()
        ims += [im.resize((im.width * 4, im.height * 4), Image.NEAREST) for im in (pod.resize((128, 128), Image.NEAREST), Image.open(WHEEL).convert('RGBA').crop(POD))]
        sheet(ims, argv[argv.index('--preview') + 1], width=2000)


if __name__ == '__main__':
    main(sys.argv)
