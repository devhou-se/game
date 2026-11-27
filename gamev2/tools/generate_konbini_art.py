#!/usr/bin/env python3
"""generate_konbini_art.py — the inside of a 7-Eleven (issue #221): the kit
tools/generate_konbinis.py furnishes every konbini interior with.

Shaded pixel art with a 1px ink outline, drawn at half size (32px a cell) and
pixel-doubled, in the station interior's palette and with its helpers
(tools/generate_station_art.py); the only lettering (ATM) is set in the game's
own font, and the stock on the shelves is dealt from seeded shuffles, so a
re-run is byte-identical on the same machine. The drinks coolers are not here:
they are office-fridge_0_0 (tools/generate_cooler_art.py), as before.

  konbini-floor-a / -b          the floor: pale vinyl tile, two tones laid as a chequer
  konbini-side-w / -e, -front, -front-w / -e
                                the tops of the walls you look over (Over Floor, on the
                                void): beside the floor, the glazed shopfront in front of
                                it, and the two front corners
  konbini-mat                   2x1, the door mat between the parted sliding doors
  konbini-wall, -wall-clock     the back wall, 1x2: white, the orange / green / red stripe
                                along its top; the clock is the time-travel clock
  konbini-wall-tobacco          2x2, the same with the numbered cigarette rack and the 7
  konbini-counter-w / -e        2x3, the till: an L counter closing a corner nook, the
                                clerk in the nook, a hot-snack case, the till and a bun
                                steamer on the counter (-e is -w mirrored)
  konbini-chiller-a / -b        1x2 open chiller: onigiri and sandwiches / bento and noodles
  konbini-coffee, -water        1x2: the coffee machine; the hot-water pot and water tap
  konbini-atm, -copier          1x2 cash machine and multifunction copier
  konbini-gondola-<stock>       2x2 shelf block: snacks, noodles, bread, daily (umbrellas,
                                socks, chargers)
  konbini-freezer, -magazines   2x1 ice-cream chest and low magazine rack
  konbini-baskets               a stack of shopping baskets

What a bump on each opens is in src/utils/Interactions.js. No rubbish bin in it.

Run from gamev2/:  python3 tools/generate_konbini_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import random
import sys

from PIL import Image, ImageOps

from generate_station_art import (C, INK, STEEL_LIGHT, STEEL, STEEL_DARK, WHITE, OFFWHITE, SLATE, SLATE_DARK,
                                  RED, RED_DARK, YELLOW, YELLOW_DARK, BLUE, BLUE_DARK, CYAN, GREEN, GREEN_DARK,
                                  ORANGE, ORANGE_DARK, CREAM, CREAM_SHADE, LED_GREEN, new, box, text, latin)

VINYL_A, VINYL_B, VINYL_JOINT, VINYL_LIGHT = (232, 232, 224), (222, 224, 218), (202, 206, 204), (242, 242, 236)
GLASS, GLASS_DARK = (156, 204, 226), (104, 150, 186)
DARK, SHADOW = (30, 34, 52), (58, 66, 96)
LIT, WARM, WARM_DARK = (236, 246, 250), (255, 232, 170), (232, 186, 110)
BREAD, BREAD_DARK, BREAD_LIGHT = (214, 150, 78), (160, 100, 52), (240, 196, 130)
BROWN, BROWN_DARK = (104, 68, 50), (72, 46, 40)
PINK, PURPLE, TEAL = (236, 130, 160), (150, 110, 190), (64, 160, 160)
SKIN, HAIR, MOUTH = (246, 195, 154), (60, 46, 32), (229, 59, 68)
BLACK = (0, 0, 0)
STOCK = [RED, YELLOW, CYAN, GREEN, ORANGE, BLUE, PINK, PURPLE, TEAL, WHITE]


# ---- floor, mat and the walls you look over ----------------------------------------

def floor(fill):
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=fill)
        d.line([0, 0, 31, 0], fill=VINYL_LIGHT)
        d.line([0, 0, 0, 31], fill=VINYL_LIGHT)
        d.line([0, 31, 31, 31], fill=VINYL_JOINT)
        d.line([31, 0, 31, 31], fill=VINYL_JOINT)
        return im
    return draw


def edge(top=False, left=False, right=False, corner=None):
    """The top of a wall seen from above, on a cell of the void: a strip along
    the named sides (the front one is the glazed shopfront), or just the corner
    block where a side wall meets the front."""
    def draw():
        im, d = new(C, C)
        if top:
            d.rectangle([0, 0, 31, 5], fill=GLASS)
            d.line([0, 0, 31, 0], fill=STEEL_LIGHT)
            d.line([0, 1, 31, 1], fill=WHITE)
            d.line([0, 4, 31, 4], fill=GLASS_DARK)
            d.line([0, 5, 31, 5], fill=INK)
            for x in (0, 16):                                    # the mullions
                d.rectangle([x, 0, x + 1, 4], fill=STEEL_LIGHT)
                d.line([x + 2, 1, x + 2, 4], fill=STEEL_DARK)
        for x0, on in ((0, left or corner == 'e'), (26, right or corner == 'w')):
            if not on:
                continue
            y1 = 5 if corner else 31
            d.rectangle([x0, 0, x0 + 5, y1], fill=STEEL_LIGHT)
            d.line([x0 + 5 if x0 == 0 else x0, 0, x0 + 5 if x0 == 0 else x0, y1], fill=INK)
            d.line([x0 if x0 == 0 else x0 + 5, 0, x0 if x0 == 0 else x0 + 5, y1], fill=STEEL)
            if corner:
                d.line([x0, 5, x0 + 5, 5], fill=INK)
        return im
    return draw


def mat():
    """The door: the floor carries on to the threshold, the two glass leaves
    stand parted at its ends, and the mat lies between them."""
    im, d = new(2 * C, C)
    for x0 in (0, 52):                                           # the leaves, seen from above
        d.rectangle([x0, 0, x0 + 11, 5], fill=GLASS)
        d.line([x0, 1, x0 + 11, 1], fill=WHITE)
        d.line([x0, 4, x0 + 11, 4], fill=GLASS_DARK)
        d.rectangle([x0, 0, x0 + 11, 5], outline=INK)
    d.line([12, 5, 51, 5], fill=STEEL)                           # the track they slide on
    d.line([12, 4, 51, 4], fill=STEEL_LIGHT)
    box(d, 9, 9, 54, 27, GREEN_DARK)
    d.rectangle([11, 11, 52, 25], outline=GREEN)
    for y in range(13, 25, 2):                                   # its ribs
        d.line([13, y, 50, y], fill=(64, 94, 58))
    return im


def paint_wall(d, x0, x1):
    """The back wall's face over columns x0..x1 of a 64px-tall canvas: the
    ceiling's edge, the fascia with the three stripes, a lit strip, the panels."""
    d.rectangle([x0, 0, x1, 3], fill=STEEL_DARK)
    d.line([x0, 0, x1, 0], fill=INK)
    d.rectangle([x0, 4, x1, 24], fill=WHITE)
    d.rectangle([x0, 7, x1, 10], fill=ORANGE)
    d.rectangle([x0, 12, x1, 16], fill=GREEN)
    d.rectangle([x0, 18, x1, 21], fill=RED)
    d.line([x0, 10, x1, 10], fill=ORANGE_DARK)
    d.line([x0, 16, x1, 16], fill=GREEN_DARK)
    d.line([x0, 21, x1, 21], fill=RED_DARK)
    d.line([x0, 25, x1, 25], fill=STEEL)
    d.line([x0, 26, x1, 26], fill=WARM)
    d.rectangle([x0, 27, x1, 55], fill=OFFWHITE)
    d.line([x0, 27, x1, 27], fill=WHITE)
    for x in range(x0, x1 + 1):
        if x % 16 == 15:
            d.line([x, 28, x, 55], fill=STEEL_LIGHT)
    d.rectangle([x0, 56, x1, 63], fill=STEEL_DARK)
    d.line([x0, 56, x1, 56], fill=INK)
    d.line([x0, 57, x1, 57], fill=STEEL)
    d.line([x0, 63, x1, 63], fill=INK)


def logo(d, x, y):
    """The 7 on its plate, 21x22 from (x, y): orange bar, red stem, the green band across it."""
    box(d, x, y, x + 20, y + 21, WHITE)
    d.rectangle([x + 3, y + 3, x + 17, y + 6], fill=ORANGE)
    d.polygon([(x + 13, y + 7), (x + 17, y + 7), (x + 11, y + 19), (x + 7, y + 19)], fill=RED)
    d.rectangle([x + 2, y + 9, x + 18, y + 13], fill=WHITE)
    d.rectangle([x + 2, y + 10, x + 18, y + 12], fill=GREEN)


def wall(clock=False):
    def draw():
        im, d = new(C, 2 * C)
        paint_wall(d, 0, 31)
        if clock:
            d.ellipse([6, 31, 25, 50], fill=STEEL_DARK, outline=INK)
            d.ellipse([8, 33, 23, 48], fill=WHITE, outline=STEEL)
            for x, y in ((15, 35), (16, 35), (15, 46), (16, 46), (10, 40), (10, 41), (21, 40), (21, 41)):
                d.point((x, y), fill=STEEL_DARK)
            d.line([16, 41, 16, 36], fill=INK)                   # ten past twelve, as ever
            d.line([16, 41, 19, 39], fill=INK)
            d.point((16, 41), fill=RED)
        return im
    return draw


def wall_tobacco():
    im, d = new(2 * C, 2 * C)
    paint_wall(d, 0, 63)
    logo(d, 22, 3)
    box(d, 3, 29, 60, 57, DARK)                                  # the rack behind the till
    rnd = random.Random(221)
    packs = [WHITE, RED, BLUE, GREEN, YELLOW, CYAN, ORANGE, OFFWHITE, PURPLE, (196, 160, 96)]
    for row in range(3):
        y = 31 + row * 9
        for x in range(5, 58, 5):
            colour = rnd.choice(packs)
            d.rectangle([x, y, x + 3, y + 4], fill=colour)
            d.line([x, y, x + 3, y], fill=WHITE if colour != WHITE else STEEL_LIGHT)
            d.point((x + 1, y + 2), fill=INK if rnd.random() < 0.5 else colour)
        d.rectangle([4, y + 5, 59, y + 6], fill=WHITE)           # the number under every pack
        for x in range(5, 58, 5):
            d.line([x + 1, y + 6, x + 2, y + 6], fill=INK)
        d.line([4, y + 7, 59, y + 7], fill=INK)
    return im


# ---- the till -------------------------------------------------------------------------

CLERK = """
.....AAAAAAAAA.....
...AAAGGGGGGGAAA...
...AGGGGGWGGGGGA...
..AAGGGGWWWGGGGAA..
.AOOOOOOOOOOOOOOOA.
.AHHHHHHHHHHHHHHHA.
AAHHSSSSSSSSSSSHHAA
ASSHSSSSSSSSSSSHSSA
ASSSSSASSSSSASSSSSA
.ASASSASSSSSASSASA.
..AASSSSSSSSSSSAA..
...AASSSSMMMSSSAA..
....AASSSSSSSSAA...
..AAAAAAAAAAAAAAA..
.ASSAWRWGWWWGWRASSA
.ASSAWRWGWOWGWRASSA
..AAAWRWGWWWGWRAAA.
...AAWRWGWWWGWRAA..
....AWRWGWWWGWRA...
....AAAAAAAAAAAA...
....ADDDDAADDDDA...
....ADDDDAADDDDA...
"""
CLERK_INK = {'A': BLACK, 'G': GREEN_DARK, 'W': WHITE, 'O': ORANGE, 'H': HAIR, 'S': SKIN, 'M': MOUTH,
             'R': RED, 'D': SLATE_DARK}


def clerk(d, x0, y0):
    """The clerk, in the cast's own proportions and black outline: a green cap
    with the orange peak, the striped tunic, facing you."""
    for y, row in enumerate(CLERK.strip('\n').split('\n')):
        for x, ch in enumerate(row):
            if ch != '.':
                d.point((x0 + x, y0 + y), fill=CLERK_INK[ch])


def counter_w():
    """The L counter in the west corner: the nook (left clear, so the floor
    shows) holds the clerk; one arm runs down the nook's east side, the other
    closes it along the front."""
    im, d = new(2 * C, 3 * C)
    clerk(d, 8, 31)
    # the counter's top, one L: an arm down the east side, an arm along the front
    box(d, 35, 0, 63, 77, CREAM)
    box(d, 0, 54, 63, 77, CREAM)
    d.rectangle([36, 54, 62, 55], fill=CREAM)
    d.rectangle([35, 55, 36, 76], fill=CREAM)
    d.line([36, 1, 36, 54], fill=WHITE)
    d.line([1, 55, 36, 55], fill=WHITE)
    d.line([37, 1, 62, 1], fill=WHITE)
    d.line([1, 76, 62, 76], fill=CREAM_SHADE)
    d.line([62, 2, 62, 76], fill=CREAM_SHADE)
    # its front face, with the stripe
    box(d, 0, 77, 63, 95, OFFWHITE)
    d.line([1, 78, 62, 78], fill=WHITE)
    d.rectangle([1, 80, 62, 81], fill=ORANGE)
    d.rectangle([1, 83, 62, 85], fill=GREEN)
    d.rectangle([1, 87, 62, 88], fill=RED)
    d.rectangle([1, 92, 62, 94], fill=STEEL)
    # the bun steamer at the back of the east arm
    box(d, 42, 1, 58, 20, WHITE)
    d.rectangle([43, 2, 57, 4], fill=ORANGE)
    d.line([43, 5, 57, 5], fill=INK)
    d.rectangle([44, 6, 56, 16], fill=WARM)
    d.line([44, 11, 56, 11], fill=STEEL)
    for y in (7, 13):
        for x in (45, 49, 53):
            d.rectangle([x, y, x + 2, y + 2], fill=WHITE)
            d.line([x, y + 3, x + 2, y + 3], fill=CREAM_SHADE)
    d.rectangle([43, 17, 57, 19], fill=STEEL_LIGHT)
    d.point((55, 18), fill=RED)
    # the till, turned to the customer
    box(d, 41, 29, 59, 41, STEEL_DARK)
    box(d, 43, 23, 57, 31, DARK)
    d.rectangle([45, 25, 55, 29], fill=LED_GREEN)
    d.line([46, 27, 51, 27], fill=GREEN_DARK)
    d.rectangle([43, 33, 57, 39], fill=STEEL_LIGHT)
    for y in (34, 36, 38):
        for x in range(44, 57, 3):
            d.point((x, y), fill=STEEL_DARK)
    d.rectangle([53, 34, 56, 35], fill=RED)
    # the hot-snack case where the two arms meet: fried chicken, croquettes, skewers
    box(d, 30, 45, 61, 72, STEEL_LIGHT)
    d.rectangle([32, 47, 59, 66], fill=WARM)
    d.line([32, 47, 59, 47], fill=WHITE)
    d.line([32, 56, 59, 56], fill=WARM_DARK)
    d.line([32, 66, 59, 66], fill=WARM_DARK)
    for i, x in enumerate((33, 40, 47, 54)):
        d.ellipse([x, 50, x + 5, 55], fill=(BREAD, BREAD_LIGHT)[i % 2], outline=BREAD_DARK)
        d.rectangle([x, 60, x + 4, 65], fill=(BREAD_LIGHT, BREAD)[i % 2], outline=BREAD_DARK)
    d.rectangle([31, 68, 60, 71], fill=STEEL)
    d.rectangle([33, 69, 37, 70], fill=RED)
    d.rectangle([39, 69, 43, 70], fill=YELLOW)
    # in front of the clerk: the coin tray
    box(d, 8, 61, 22, 71, BLUE)
    d.rectangle([10, 63, 20, 69], fill=CYAN)
    d.line([10, 63, 20, 63], fill=BLUE_DARK)
    return im


def counter_e():
    return ImageOps.mirror(counter_w())


# ---- against the back wall --------------------------------------------------------------

def onigiri(d, x, y, i):
    d.polygon([(x, y + 7), (x + 3, y + 1), (x + 4, y + 1), (x + 7, y + 7)], fill=WHITE, outline=STEEL)
    d.rectangle([x + 2, y + 5, x + 5, y + 7], fill=DARK)
    d.point((x + 3, y + 3), fill=(RED, GREEN, ORANGE)[i % 3])
    d.point((x + 4, y + 3), fill=(RED, GREEN, ORANGE)[i % 3])


def sandwich(d, x, y, i):
    d.polygon([(x, y + 7), (x, y + 1), (x + 7, y + 7)], fill=WHITE, outline=STEEL)
    d.line([x + 1, y + 3, x + 5, y + 7], fill=(GREEN, YELLOW, PINK)[i % 3])
    d.line([x + 1, y + 4, x + 4, y + 7], fill=(RED, WHITE, GREEN)[i % 3])


def bento(d, x, y, i):
    d.rectangle([x, y + 2, x + 11, y + 7], fill=DARK)
    d.rectangle([x + 1, y + 3, x + 5, y + 6], fill=WHITE)
    d.point((x + 3, y + 4), fill=RED)
    d.rectangle([x + 7, y + 3, x + 10, y + 4], fill=(BREAD, ORANGE, BREAD_DARK)[i % 3])
    d.rectangle([x + 7, y + 5, x + 10, y + 6], fill=(GREEN, YELLOW, GREEN)[i % 3])
    d.line([x, y + 2, x + 11, y + 2], fill=STEEL_LIGHT)


def bowl(d, x, y, i):
    d.polygon([(x, y + 3), (x + 9, y + 3), (x + 7, y + 7), (x + 2, y + 7)], fill=(DARK, RED_DARK, DARK)[i % 3])
    d.rectangle([x + 1, y + 2, x + 8, y + 3], fill=(CREAM, YELLOW, BREAD_LIGHT)[i % 3])
    d.point((x + 3, y + 2), fill=GREEN)
    d.point((x + 6, y + 3), fill=(PINK, GREEN, RED)[i % 3])
    d.line([x, y + 1, x + 9, y + 1], fill=WHITE)


def chiller(rows):
    """An open, lit chiller: four shelves, each a row of one thing."""
    def draw():
        im, d = new(C, 2 * C)
        box(d, 0, 0, 31, 63, WHITE)
        d.rectangle([1, 1, 30, 7], fill=OFFWHITE)                # the canopy and its light
        d.line([1, 1, 30, 1], fill=WHITE)
        d.rectangle([1, 3, 30, 4], fill=GREEN)
        d.line([1, 8, 30, 8], fill=INK)
        d.rectangle([3, 9, 28, 55], fill=LIT)
        d.line([3, 9, 28, 9], fill=WARM)
        d.line([2, 9, 2, 55], fill=STEEL_LIGHT)
        d.line([29, 9, 29, 55], fill=STEEL_LIGHT)
        for row, item in enumerate(rows):
            y = 11 + row * 11
            if item in (onigiri, sandwich):
                for i, x in enumerate((4, 12, 20)):
                    item(d, x, y, i + row)
            else:
                for i, x in enumerate((4, 17) if item is bento else (5, 17)):
                    item(d, x, y, i + row)
            d.rectangle([3, y + 8, 28, y + 9], fill=WHITE)       # the shelf's edge, a price on it
            d.line([3, y + 10, 28, y + 10], fill=STEEL)
            for x in (6, 14, 22):
                d.line([x, y + 9, x + 3, y + 9], fill=YELLOW)
        d.line([1, 55, 30, 55], fill=INK)                        # the kick plate and its vents
        for y in (58, 60):
            d.line([5, y, 26, y], fill=STEEL_LIGHT)
        d.rectangle([1, 62, 30, 62], fill=STEEL)
        return im
    return draw


def cabinet(d):
    """A waist-high cabinet filling the floor cell, its top from the wall's
    foot down to y 43: what the coffee machine and the water stand on. Above
    it the wall shows."""
    box(d, 0, 32, 31, 63, OFFWHITE)
    d.rectangle([1, 33, 30, 43], fill=CREAM)
    d.line([1, 33, 30, 33], fill=WHITE)
    d.line([1, 43, 30, 43], fill=CREAM_SHADE)
    d.line([0, 44, 31, 44], fill=INK)
    d.line([15, 45, 15, 59], fill=STEEL)
    d.line([16, 45, 16, 59], fill=WHITE)
    for x in (11, 19):
        d.rectangle([x, 50, x + 1, 53], fill=STEEL_DARK)
    d.rectangle([1, 60, 30, 62], fill=STEEL)


def coffee():
    im, d = new(C, 2 * C)
    cabinet(d)
    box(d, 3, 13, 21, 40, DARK)                                  # the machine
    box(d, 6, 6, 18, 13, GLASS)                                  # its hopper of beans
    d.rectangle([7, 9, 17, 12], fill=BROWN)
    d.point([(9, 10), (13, 11), (15, 9)], fill=BROWN_DARK)
    d.line([7, 7, 12, 7], fill=WHITE)
    d.rectangle([6, 16, 18, 20], fill=WHITE)                     # the panel: hot / iced, R / L
    d.rectangle([7, 17, 9, 19], fill=RED)
    d.rectangle([11, 17, 13, 19], fill=BLUE)
    d.rectangle([15, 17, 17, 19], fill=BROWN)
    d.line([4, 23, 20, 23], fill=SHADOW)
    d.rectangle([6, 25, 18, 36], fill=(16, 18, 30))              # the bay, a cup under the spout
    d.rectangle([11, 25, 13, 27], fill=STEEL_LIGHT)
    d.polygon([(9, 30), (15, 30), (14, 36), (10, 36)], fill=WHITE)
    d.line([10, 30, 14, 30], fill=BROWN)
    d.line([10, 33, 14, 33], fill=(RED))
    d.rectangle([5, 37, 19, 38], fill=STEEL)
    for x in (24, 28):                                           # stacks of cups, and lids
        d.rectangle([x - 1, 26 + (x - 24), x + 2, 37], fill=WHITE, outline=STEEL)
        for y in range(28 + (x - 24), 37, 2):
            d.line([x - 1, y, x + 2, y], fill=STEEL_LIGHT)
    d.rectangle([23, 38, 30, 40], fill=BROWN, outline=INK)
    return im


def water():
    im, d = new(C, 2 * C)
    box(d, 8, 2, 23, 12, BLUE)                                   # the sign on the wall: a drop
    d.polygon([(15, 3), (16, 3), (19, 8), (18, 10), (13, 10), (12, 8)], fill=WHITE)
    d.point((14, 8), fill=CYAN)
    cabinet(d)
    box(d, 2, 21, 13, 40, WHITE)                                 # the hot-water pot
    box(d, 2, 17, 13, 22, DARK)
    d.rectangle([5, 15, 10, 17], fill=DARK, outline=INK)
    d.rectangle([0, 23, 2, 25], fill=DARK)                       # its spout
    d.rectangle([5, 25, 6, 34], fill=STEEL_LIGHT)                # how full it is
    d.rectangle([5, 29, 6, 34], fill=CYAN)
    d.rectangle([9, 25, 11, 27], fill=RED)
    d.line([3, 38, 12, 38], fill=STEEL_LIGHT)
    box(d, 16, 16, 29, 40, STEEL_LIGHT)                          # the water tap
    d.rectangle([18, 18, 27, 23], fill=CYAN)
    d.line([18, 18, 27, 18], fill=WHITE)
    d.rectangle([20, 20, 21, 21], fill=WHITE)
    d.rectangle([18, 26, 27, 36], fill=(16, 18, 30))
    d.rectangle([22, 26, 23, 28], fill=STEEL)
    d.polygon([(20, 31), (25, 31), (24, 36), (21, 36)], fill=WHITE)
    d.line([21, 32, 24, 32], fill=CYAN)
    d.rectangle([17, 37, 28, 38], fill=STEEL)
    return im


def atm():
    im, d = new(C, 2 * C)
    box(d, 2, 3, 29, 63, OFFWHITE)
    box(d, 2, 3, 29, 14, WHITE)                                  # its name
    text(d, 4, 5, 'ATM', latin(), GREEN_DARK)
    d.line([3, 15, 28, 15], fill=ORANGE)
    d.line([3, 16, 28, 16], fill=GREEN)
    d.line([3, 17, 28, 17], fill=RED)
    box(d, 5, 20, 26, 35, DARK)                                  # the screen
    d.rectangle([7, 22, 24, 33], fill=CYAN)
    d.rectangle([9, 24, 22, 25], fill=WHITE)
    for y in (28, 31):
        for x in (9, 17):
            d.rectangle([x, y, x + 5, y + 1], fill=BLUE)
    box(d, 4, 37, 27, 47, STEEL_LIGHT)                           # the shelf: keys, the card slot
    for y in (39, 41, 43, 45):
        for x in (7, 9, 11):
            d.point((x, y), fill=STEEL_DARK)
    d.rectangle([16, 40, 24, 41], fill=DARK)
    d.point((25, 40), fill=LED_GREEN)
    d.rectangle([16, 44, 24, 45], fill=DARK)
    d.line([18, 45, 22, 45], fill=WHITE)
    box(d, 6, 50, 25, 54, DARK)                                  # where the notes come out
    d.line([8, 52, 23, 52], fill=STEEL)
    d.line([3, 57, 28, 57], fill=STEEL_LIGHT)
    d.rectangle([3, 60, 28, 62], fill=STEEL)
    return im


def copier():
    im, d = new(C, 2 * C)
    box(d, 2, 24, 29, 62, OFFWHITE)                              # the body and its paper drawers
    box(d, 1, 17, 30, 25, STEEL_LIGHT)                           # the lid
    d.line([2, 18, 29, 18], fill=WHITE)
    box(d, 3, 11, 21, 17, WHITE)                                 # the feeder, a sheet in it
    d.rectangle([6, 9, 17, 11], fill=WHITE, outline=STEEL)
    d.line([5, 14, 19, 14], fill=STEEL)
    box(d, 21, 6, 30, 15, DARK)                                  # the touch panel
    d.rectangle([23, 8, 28, 12], fill=CYAN)
    d.line([23, 8, 28, 8], fill=WHITE)
    d.point((24, 14), fill=LED_GREEN)
    d.point((27, 14), fill=RED)
    d.rectangle([4, 28, 27, 34], fill=DARK)                      # the tray the copies land in
    d.rectangle([7, 31, 24, 32], fill=WHITE)
    d.line([6, 33, 25, 33], fill=STEEL_LIGHT)
    for y in (37, 45, 53):
        d.line([3, y, 28, y], fill=INK)
        d.line([3, y + 1, 28, y + 1], fill=WHITE)
        d.rectangle([12, y + 3, 19, y + 4], fill=STEEL_DARK)
    d.rectangle([24, 39, 27, 43], fill=YELLOW, outline=INK)      # the coin box
    d.rectangle([3, 60, 28, 61], fill=STEEL)
    return im


# ---- standing on the floor ------------------------------------------------------------

def bag(d, x, y, colour, rnd):
    d.rectangle([x, y + 1, x + 5, y + 8], fill=colour)
    d.line([x, y, x + 5, y], fill=WHITE if colour != WHITE else STEEL_LIGHT)
    d.rectangle([x + 1, y + 3, x + 4, y + 5], fill=YELLOW if colour not in (YELLOW, WHITE) else RED)
    return 7


def snack_box(d, x, y, colour, rnd):
    d.rectangle([x, y + 4, x + 6, y + 8], fill=colour)
    d.line([x, y + 4, x + 6, y + 4], fill=WHITE if colour != WHITE else STEEL_LIGHT)
    d.line([x + 1, y + 6, x + 4, y + 6], fill=BROWN if colour != BLUE else WHITE)
    return 8


def cup(d, x, y, colour, rnd):
    d.polygon([(x, y + 2), (x + 5, y + 2), (x + 4, y + 8), (x + 1, y + 8)], fill=WHITE)
    d.rectangle([x, y + 4, x + 5, y + 5], fill=colour if colour != WHITE else RED)
    d.line([x, y + 1, x + 5, y + 1], fill=colour if colour != WHITE else RED)
    return 7


def pot_noodle(d, x, y, colour, rnd):
    d.polygon([(x, y + 4), (x + 8, y + 4), (x + 7, y + 8), (x + 1, y + 8)], fill=colour)
    d.line([x, y + 3, x + 8, y + 3], fill=WHITE if colour != WHITE else STEEL_LIGHT)
    d.line([x + 2, y + 6, x + 6, y + 6], fill=WHITE if colour != WHITE else RED)
    return 10


def bun(d, x, y, colour, rnd):
    d.ellipse([x, y + 3, x + 7, y + 8], fill=rnd.choice([BREAD, BREAD_LIGHT, BREAD]), outline=BREAD_DARK)
    d.line([x + 2, y + 4, x + 4, y + 4], fill=BREAD_LIGHT)
    d.point((x + 6, y + 8), fill=colour)
    return 9


def loaf(d, x, y, colour, rnd):
    d.rectangle([x, y + 2, x + 6, y + 8], fill=WHITE, outline=STEEL_LIGHT)
    d.rectangle([x + 1, y + 3, x + 5, y + 6], fill=BREAD_LIGHT)
    d.line([x + 1, y + 3, x + 5, y + 3], fill=BREAD_DARK)
    d.rectangle([x + 1, y + 7, x + 5, y + 7], fill=colour)
    return 8


def umbrella(d, x, y, colour, rnd):
    d.line([x + 1, y, x + 1, y + 1], fill=INK)
    d.rectangle([x, y + 2, x + 2, y + 8], fill=colour if colour != WHITE else LIT)
    d.line([x, y + 2, x, y + 8], fill=WHITE)
    return 4


def socks(d, x, y, colour, rnd):
    d.rectangle([x, y + 1, x + 5, y + 8], fill=WHITE)
    d.rectangle([x + 1, y + 2, x + 2, y + 6], fill=colour if colour != WHITE else DARK)
    d.rectangle([x + 1, y + 6, x + 4, y + 7], fill=colour if colour != WHITE else DARK)
    d.point((x + 3, y), fill=INK)
    return 7


def charger(d, x, y, colour, rnd):
    d.rectangle([x, y + 2, x + 5, y + 8], fill=WHITE if colour != WHITE else CYAN)
    d.rectangle([x + 1, y + 4, x + 3, y + 6], fill=DARK)
    d.line([x + 4, y + 5, x + 4, y + 7], fill=colour if colour != WHITE else BLUE)
    d.point((x + 2, y + 1), fill=INK)
    return 7


# what stands on each of a gondola's three shelves, and how its top looks from above
GOODS = {
    'snacks': ((bag, bag, snack_box), 'rect'),
    'noodles': ((cup, pot_noodle, cup), 'round'),
    'bread': ((bun, loaf, bun), 'oval'),
    'daily': ((umbrella, socks, charger), 'long'),
}


def gondola(stock):
    """A shelf block, 2x2: its top with the goods seen from above, and its
    front in three shelves, a price rail under each."""
    shelves, tops = GOODS[stock]

    def draw():
        im, d = new(2 * C, 2 * C)
        rnd = random.Random(f'gondola-{stock}')
        box(d, 0, 0, 63, 22, STEEL_LIGHT)                        # the top
        d.rectangle([2, 2, 61, 20], fill=OFFWHITE)
        d.line([1, 1, 62, 1], fill=WHITE)
        for row, y in enumerate((3, 12)):
            x = 3
            while x < 56:
                colour = rnd.choice(STOCK)
                if tops == 'rect':
                    d.rectangle([x, y, x + 5, y + 6], fill=colour)
                    d.rectangle([x + 1, y + 2, x + 4, y + 4], fill=YELLOW if colour not in (YELLOW, WHITE) else RED)
                    d.line([x, y + 7, x + 5, y + 7], fill=STEEL)
                    x += 7
                elif tops == 'round':
                    d.ellipse([x, y, x + 6, y + 6], fill=WHITE, outline=STEEL)
                    d.ellipse([x + 2, y + 2, x + 4, y + 4], fill=colour if colour != WHITE else RED)
                    x += 8
                elif tops == 'oval':
                    d.ellipse([x, y + 1, x + 7, y + 6], fill=rnd.choice([BREAD, BREAD_LIGHT]), outline=BREAD_DARK)
                    d.line([x + 2, y + 2, x + 4, y + 2], fill=BREAD_LIGHT)
                    x += 9
                else:
                    d.rectangle([x, y + 1, x + 9, y + 3], fill=colour if colour != WHITE else LIT)
                    d.line([x, y + 1, x + 9, y + 1], fill=WHITE)
                    d.rectangle([x + 10, y + 1, x + 11, y + 2], fill=INK)
                    d.rectangle([x, y + 5, x + 9, y + 6], fill=rnd.choice(STOCK[:6]))
                    x += 14
        box(d, 0, 22, 63, 63, WHITE)                             # the front
        for row, item in enumerate(shelves):
            y = 24 + row * 12
            d.rectangle([2, y, 61, y + 8], fill=SHADOW)
            d.line([2, y, 61, y], fill=DARK)
            x = 3
            while x < 55:
                x += item(d, x, y, rnd.choice(STOCK), rnd)
            d.rectangle([2, y + 9, 61, y + 10], fill=WHITE)      # the price rail
            d.line([2, y + 11, 61, y + 11], fill=INK)
            for x in range(4, 58, 8):
                d.line([x, y + 10, x + 3, y + 10], fill=YELLOW if (x + row) % 3 else RED)
        d.rectangle([1, 60, 62, 62], fill=STEEL)
        for x in (0, 62):                                        # the uprights at its ends
            d.rectangle([x, 22, x + 1, 63], fill=STEEL_DARK)
        d.line([0, 22, 63, 22], fill=INK)
        return im
    return draw


def freezer():
    im, d = new(2 * C, C)
    box(d, 0, 0, 63, 19, WHITE)                                  # the chest's top and its two lids
    d.rectangle([3, 3, 60, 16], fill=GLASS)
    rnd = random.Random(31)
    tubs = [PINK, WHITE, YELLOW, BROWN, CYAN, GREEN, ORANGE, PURPLE]
    for y in (4, 10):
        for x in range(5, 57, 7):
            colour = rnd.choice(tubs)
            d.rectangle([x, y, x + 4, y + 4], fill=colour)
            d.line([x, y, x + 4, y], fill=WHITE if colour != WHITE else STEEL_LIGHT)
    d.rectangle([3, 3, 60, 16], outline=INK)
    d.rectangle([30, 3, 33, 16], fill=STEEL_LIGHT, outline=INK)
    for x in (10, 40):                                           # the light on the glass
        d.line([x, 15, x + 10, 5], fill=WHITE)
        d.line([x + 4, 15, x + 12, 7], fill=LIT)
    for x in (26, 36):
        d.rectangle([x, 8, x + 1, 11], fill=STEEL_DARK)
    box(d, 0, 19, 63, 31, WHITE)                                 # its front
    d.rectangle([1, 22, 62, 24], fill=BLUE)
    d.line([1, 24, 62, 24], fill=BLUE_DARK)
    for x in range(48, 60, 2):
        d.line([x, 27, x, 29], fill=STEEL)
    d.rectangle([1, 30, 62, 30], fill=STEEL)
    return im


def magazines():
    im, d = new(2 * C, C)
    rnd = random.Random(17)
    covers = [RED, YELLOW, CYAN, PINK, ORANGE, BLUE, PURPLE, GREEN, WHITE, TEAL]
    box(d, 0, 0, 63, 14, STEEL_LIGHT)                            # the back tier, tilted to you
    box(d, 0, 14, 63, 28, STEEL)                                 # the front tier
    for y in (1, 16):
        for x in range(2, 60, 9):
            colour = rnd.choice(covers)
            d.rectangle([x, y, x + 7, y + 10], fill=colour, outline=INK)
            d.rectangle([x + 1, y + 1, x + 6, y + 2], fill=WHITE if colour != WHITE else RED)
            d.rectangle([x + 2, y + 4, x + 5, y + 7], fill=rnd.choice([SKIN, DARK, YELLOW, WHITE]))
            d.point((x + 6, y + 9), fill=YELLOW if colour != YELLOW else RED)
    box(d, 0, 28, 63, 31, STEEL_DARK)
    return im


def baskets():
    im, d = new(C, C)
    d.arc([8, 1, 23, 13], 180, 360, fill=INK)                    # the top one's handle, up
    d.arc([8, 2, 23, 14], 180, 360, fill=STEEL_DARK)
    for y in (6, 10, 14):                                        # three more, nested in the one below
        box(d, 4, y, 27, y + 4, ORANGE)
        d.line([5, y + 1, 26, y + 1], fill=(240, 150, 100))
    d.polygon([(4, 18), (27, 18), (25, 29), (6, 29)], fill=ORANGE, outline=INK)
    d.line([5, 19, 26, 19], fill=(240, 150, 100))
    for y in (22, 25):
        for x in range(8, 25, 3):
            d.rectangle([x, y, x + 1, y + 1], fill=ORANGE_DARK)
    d.line([7, 30, 24, 30], fill=INK)
    return im


# key: (how to draw it, its name in the editor)
SPRITES = {
    'konbini-floor-a': (floor(VINYL_A), 'konbini-floor'),
    'konbini-floor-b': (floor(VINYL_B), 'konbini-floor'),
    'konbini-side-w': (edge(right=True), 'konbini-wall-top'),
    'konbini-side-e': (edge(left=True), 'konbini-wall-top'),
    'konbini-front': (edge(top=True), 'konbini-shopfront'),
    'konbini-front-w': (edge(corner='w'), 'konbini-wall-top'),
    'konbini-front-e': (edge(corner='e'), 'konbini-wall-top'),
    'konbini-mat': (mat, 'konbini-mat'),
    'konbini-wall': (wall(), 'konbini-wall'),
    'konbini-wall-clock': (wall(clock=True), 'konbini-wall-clock'),
    'konbini-wall-tobacco': (wall_tobacco, 'konbini-wall-tobacco'),
    'konbini-counter-w': (counter_w, 'konbini-counter'),
    'konbini-counter-e': (counter_e, 'konbini-counter'),
    'konbini-chiller-a': (chiller((onigiri, onigiri, sandwich, sandwich)), 'konbini-chiller'),
    'konbini-chiller-b': (chiller((bento, bento, bowl, bowl)), 'konbini-chiller'),
    'konbini-coffee': (coffee, 'konbini-coffee'),
    'konbini-water': (water, 'konbini-water'),
    'konbini-atm': (atm, 'konbini-atm'),
    'konbini-copier': (copier, 'konbini-copier'),
    'konbini-gondola-snacks': (gondola('snacks'), 'konbini-gondola'),
    'konbini-gondola-noodles': (gondola('noodles'), 'konbini-gondola'),
    'konbini-gondola-bread': (gondola('bread'), 'konbini-gondola'),
    'konbini-gondola-daily': (gondola('daily'), 'konbini-gondola'),
    'konbini-freezer': (freezer, 'konbini-freezer'),
    'konbini-magazines': (magazines, 'konbini-magazines'),
    'konbini-baskets': (baskets, 'konbini-baskets'),
}


def main():
    built = {}
    for name, (fn, _) in SPRITES.items():
        im = fn()
        built[name] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = SPRITES[name][1]
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        rows, x, y, rowh, width = [], 16, 16, 0, 1200
        for im in built.values():
            if x + im.width + 16 > width:
                x, y, rowh = 16, y + rowh + 16, 0
            rows.append((im, x, y))
            x += im.width + 16
            rowh = max(rowh, im.height)
        sheet = Image.new('RGBA', (width, y + rowh + 16), SLATE + (255,))
        for im, x, y in rows:
            sheet.alpha_composite(im, (x, y))
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
