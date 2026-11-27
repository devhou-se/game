#!/usr/bin/env python3
"""generate_chikagai_art.py — the art of an underground arcade (a chikagai) and
of its entrance on the street.

Shaded pixel art with a 1px ink outline, drawn at half size (32px a cell) and
pixel-doubled, in the station interior's palette and with its helpers
(tools/generate_station_art.py); the text is set in the game's own fonts, so a
re-run is byte-identical on any machine. The arcade also uses the station's
bench, planters, pillar, lockers and tactile paving as they are.

  chika-floor-a / -b            the floor: cream tile, and the tan apron in front of the shops
  chika-wall, -wall-poster-a/-b the back wall, 1x2 (a teal band), plain or with a framed advert
  chika-side-w / -e, -front, -front-w / -e
                                the tops of the walls you look over: beside the floor, in
                                front of it, and where a stem leaves the hall
  chika-shop-<kind>             a 3x2 shopfront in the back wall: bakery, kissa (coffee) and
                                bar sell over the counter, books, flowers and shutter say a
                                line (src/utils/Interactions.js)
  chika-exit-<slug>             4x2, the stairs up to the street in the back wall under a
                                yellow exit sign, one per exit of every town in tools/chikagai.py
  chika-sign-<slug>             4x1, the same sign hung from the ceiling (Tops), for an
                                exit in a south wall
  chika-exit-south-w / -e       the foot of the stairs in a south wall, in two cells
  chika-gacha                   2x2 capsule-toy machines
  chika-map                     1x2 floor map on a stand
  chikagai-entrance-snow        2x3, the entrance on the street: a glass canopy under snow,
                                the blue sign, the steps going down

Run from gamev2/:  python3 tools/generate_chikagai_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import random
import sys

from PIL import Image

import chikagai
from generate_station_art import (C, INK, STEEL_LIGHT, STEEL, STEEL_DARK, WHITE, OFFWHITE, VOID, SLATE,
                                  RED, RED_DARK, YELLOW, YELLOW_DARK, BLUE, BLUE_DARK, CYAN, GREEN, GREEN_DARK,
                                  ORANGE, ORANGE_DARK, CREAM, new, box, text, text_size, centred, kana, latin)

TEAL, TEAL_DARK = (64, 160, 160), (44, 118, 126)
TILE, TILE_JOINT, TILE_LIGHT = (228, 222, 206), (204, 196, 178), (240, 236, 224)
TAN, TAN_JOINT = (208, 190, 158), (184, 164, 132)
WOOD, WOOD_DARK, WOOD_LIGHT = (176, 120, 72), (124, 82, 56), (212, 160, 104)
BROWN, BROWN_DARK = (104, 68, 50), (72, 46, 40)
WARM, WARM_DARK = (244, 224, 180), (214, 184, 132)
BREAD, BREAD_DARK = (214, 150, 78), (160, 100, 52)
PINK, PURPLE, LEAF = (236, 130, 160), (150, 110, 190), (70, 130, 76)
SNOW, SNOW_SHADE = (248, 250, 255), (206, 220, 238)
GLASS, GLASS_DARK = (156, 204, 226), (104, 150, 186)
DARK = (30, 34, 52)


# ---- floor and walls -------------------------------------------------------------

def floor(fill, joint, light):
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=fill)
        d.line([0, 0, 31, 0], fill=light)
        d.line([0, 0, 0, 31], fill=light)
        d.line([0, 31, 31, 31], fill=joint)
        d.line([31, 0, 31, 31], fill=joint)
        return im
    return draw


def paint_wall(d, x0, x1):
    """The back wall's face over columns x0..x1 of a 64px-tall canvas."""
    d.rectangle([x0, 0, x1, 3], fill=STEEL_DARK)
    d.line([x0, 0, x1, 0], fill=INK)
    d.rectangle([x0, 4, x1, 39], fill=OFFWHITE)
    d.line([x0, 4, x1, 4], fill=WHITE)
    for y in (15, 27):
        d.line([x0, y, x1, y], fill=STEEL_LIGHT)
    for x in range(x0, x1 + 1):
        if x % 16 == 15:
            d.line([x, 5, x, 39], fill=STEEL_LIGHT)
    d.rectangle([x0, 40, x1, 45], fill=TEAL)
    d.line([x0, 40, x1, 40], fill=INK)
    d.line([x0, 45, x1, 45], fill=INK)
    d.line([x0, 44, x1, 44], fill=TEAL_DARK)
    d.rectangle([x0, 46, x1, 57], fill=TILE)
    for x in range(x0, x1 + 1):
        if x % 8 == 7:
            d.line([x, 46, x, 57], fill=TILE_JOINT)
    d.rectangle([x0, 58, x1, 63], fill=STEEL_DARK)
    d.line([x0, 58, x1, 58], fill=INK)
    d.line([x0, 63, x1, 63], fill=INK)


def wall(poster=None):
    def draw():
        im, d = new(C, 2 * C)
        paint_wall(d, 0, 31)
        if poster == 'a':                                   # ski season: a white peak on a blue sky
            box(d, 5, 8, 26, 36, (120, 176, 226))
            d.polygon([(8, 34), (16, 16), (24, 34)], fill=WHITE)
            d.polygon([(13, 34), (20, 24), (25, 34)], fill=SNOW_SHADE)
            d.rectangle([6, 30, 25, 35], fill=RED)
            d.line([8, 32, 23, 32], fill=WHITE)
            d.rectangle([20, 10, 23, 13], fill=YELLOW)
        elif poster == 'b':                                 # a sale: a red sun on yellow
            box(d, 5, 8, 26, 36, YELLOW)
            d.ellipse([9, 12, 22, 25], fill=RED, outline=RED_DARK)
            d.rectangle([8, 28, 23, 30], fill=INK)
            d.rectangle([8, 32, 18, 33], fill=RED_DARK)
        return im
    return draw


def edge(top=False, left=False, right=False):
    """The top of a wall seen from above: a strip along the named sides of a dark cell."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        if top:
            d.rectangle([0, 0, 31, 5], fill=STEEL_LIGHT)
            d.line([0, 5, 31, 5], fill=INK)
            d.line([0, 0, 31, 0], fill=STEEL)
        if left:
            d.rectangle([0, 0, 5, 31], fill=STEEL_LIGHT)
            d.line([5, 6 if top else 0, 5, 31], fill=INK)
            d.line([0, 0, 0, 31], fill=STEEL)
        if right:
            d.rectangle([26, 0, 31, 31], fill=STEEL_LIGHT)
            d.line([26, 6 if top else 0, 26, 31], fill=INK)
            d.line([31, 0, 31, 31], fill=STEEL)
        return im
    return draw


# ---- shopfronts --------------------------------------------------------------------

def shop_frame(fascia, label, ink=WHITE, back=WARM):
    """A 3x2 shopfront: ceiling, the fascia with its name, the opening and a counter."""
    im, d = new(3 * C, 2 * C)
    d.rectangle([0, 0, 95, 3], fill=STEEL_DARK)
    d.line([0, 0, 95, 0], fill=INK)
    box(d, 0, 4, 95, 21, fascia)
    ja, en = label
    w = (text_size(d, ja, kana())[0] if ja else 0) + (text_size(d, en, latin())[0] if en else 0) + (6 if ja and en else 0)
    x = 48 - w // 2
    if ja:
        text(d, x, 7, ja, kana(), ink)
        x += text_size(d, ja, kana())[0] + 6
    if en:
        text(d, x, 9, en, latin(), ink)
    d.rectangle([0, 22, 95, 63], fill=back)
    for x0 in (0, 92):                                      # the pilasters either side
        box(d, x0, 21, x0 + 3, 63, OFFWHITE)
    d.line([0, 63, 95, 63], fill=INK)
    return im, d


def counter(d, y, fill, dark, light):
    d.rectangle([4, y, 91, 62], fill=fill)
    d.line([4, y, 91, y], fill=INK)
    d.line([4, y + 1, 91, y + 1], fill=light)
    d.rectangle([4, 59, 91, 62], fill=dark)


def shop_bakery():
    im, d = shop_frame(ORANGE, ('ベーカリー', ''))
    for i, x in enumerate(range(4, 92, 8)):                 # the awning's stripes
        d.rectangle([x, 22, x + 7, 27], fill=ORANGE if i % 2 == 0 else WHITE)
    d.line([4, 28, 91, 28], fill=INK)
    for y in (36, 44):                                      # two shelves of loaves
        d.line([6, y, 89, y], fill=WOOD_DARK)
        for i, x in enumerate(range(8, 86, 10)):
            if (i + y) % 3:
                d.ellipse([x, y - 6, x + 7, y - 1], fill=BREAD, outline=BREAD_DARK)
            else:
                d.rectangle([x, y - 5, x + 7, y - 1], fill=BREAD, outline=BREAD_DARK)
            d.point([(x + 2, y - 4), (x + 4, y - 4)], fill=WARM)
    counter(d, 46, WOOD, WOOD_DARK, WOOD_LIGHT)
    box(d, 8, 48, 60, 58, GLASS)                            # the glass case
    for x in range(11, 56, 9):
        d.ellipse([x, 51, x + 6, 56], fill=BREAD, outline=BREAD_DARK)
    d.line([9, 49, 59, 49], fill=WHITE)
    box(d, 68, 49, 84, 57, STEEL_LIGHT)                     # the till
    d.rectangle([70, 51, 78, 53], fill=DARK)
    return im


def shop_kissa():
    im, d = shop_frame(BROWN, ('喫茶', 'COFFEE'), ink=YELLOW, back=(132, 90, 62))
    d.rectangle([4, 22, 91, 24], fill=BROWN_DARK)
    for x in (24, 48, 72):                                  # hanging lamps
        d.line([x, 22, x, 27], fill=INK)
        d.polygon([(x - 4, 31), (x, 27), (x + 4, 31)], fill=YELLOW, outline=INK)
        d.rectangle([x - 2, 32, x + 2, 33], fill=(255, 236, 170))
    d.line([6, 43, 89, 43], fill=BROWN_DARK)                # the back shelf: cups, a row of jars
    for x in range(8, 40, 6):
        d.rectangle([x, 39, x + 3, 42], fill=WHITE, outline=INK)
    for i, x in enumerate(range(54, 88, 7)):
        d.rectangle([x, 36, x + 4, 42], fill=(BREAD_DARK, BROWN_DARK, WOOD)[i % 3], outline=INK)
        d.line([x + 1, 37, x + 3, 37], fill=WARM)
    counter(d, 46, BROWN, BROWN_DARK, WOOD)
    d.rectangle([14, 38, 17, 45], fill=STEEL_LIGHT, outline=INK)     # the siphon
    d.ellipse([12, 33, 19, 39], fill=GLASS, outline=INK)
    for x in (30, 40):
        d.rectangle([x, 42, x + 4, 45], fill=WHITE, outline=INK)     # two cups set out
        d.point((x + 6, 43), fill=INK)
    box(d, 58, 49, 86, 57, (38, 60, 44))                    # the chalk board
    for y in (51, 53, 55):
        d.line([61, y, 61 + (y * 7) % 19 + 4, y], fill=OFFWHITE)
    return im


def shop_bar():
    im, d = shop_frame(INK, ('立呑み', ''), ink=WHITE, back=(226, 170, 96))
    for x in (6, 84):                                       # a red lantern at each end of the name
        d.ellipse([x, 6, x + 6, 18], fill=RED, outline=RED_DARK)
        d.line([x + 1, 9, x + 5, 9], fill=RED_DARK)
        d.line([x + 1, 14, x + 5, 14], fill=RED_DARK)
    d.line([6, 40, 89, 40], fill=WOOD_DARK)                 # the bottles behind
    rnd = random.Random(7)
    for x in range(8, 88, 5):
        colour = rnd.choice([(70, 120, 80), (120, 72, 44), (214, 220, 226), (190, 150, 60)])
        d.rectangle([x, 33, x + 2, 39], fill=colour, outline=INK)
        d.point((x + 1, 31), fill=INK)
        d.point((x + 1, 32), fill=colour)
    for i, x in enumerate(range(4, 92, 18)):                # the short curtain, in five panels
        d.rectangle([x, 22, min(x + 16, 91), 30], fill=RED)
        d.line([x, 30, min(x + 16, 91), 30], fill=RED_DARK)
        d.line([x, 22, x, 30], fill=RED_DARK)
        d.ellipse([x + 6, 24, x + 10, 28], outline=WHITE)
    d.line([4, 22, 91, 22], fill=INK)
    counter(d, 46, WOOD_LIGHT, WOOD_DARK, WARM)
    for x in (16, 44, 70):                                  # glasses on the counter
        d.rectangle([x, 41, x + 4, 45], fill=(244, 200, 90), outline=INK)
        d.line([x + 1, 41, x + 3, 41], fill=WHITE)
    d.rectangle([28, 43, 34, 45], fill=GREEN, outline=INK)  # a dish of edamame
    return im


def shop_books():
    im, d = shop_frame(BLUE, ('本', 'BOOKS'), back=(98, 84, 76))
    rnd = random.Random(3)
    spines = [RED, YELLOW, GREEN, CYAN, OFFWHITE, ORANGE, PURPLE, TEAL, WOOD_LIGHT, PINK]
    for y0 in (24, 35):                                     # two shelves of spines
        x = 6
        while x < 88:
            w = rnd.choice([2, 2, 3])
            d.rectangle([x, y0 + rnd.choice([0, 0, 1, 2]), x + w - 1, y0 + 8], fill=rnd.choice(spines))
            x += w + (1 if rnd.random() < 0.2 else 0)
        d.line([4, y0 + 9, 91, y0 + 9], fill=INK)
    counter(d, 46, WOOD, WOOD_DARK, WOOD_LIGHT)
    for i, x in enumerate(range(8, 86, 12)):                # magazines laid out face up
        cover = spines[(i * 3) % len(spines)]
        d.rectangle([x, 49, x + 8, 58], fill=cover, outline=INK)
        d.rectangle([x + 2, 51, x + 6, 53], fill=WHITE)
    return im


def shop_flowers():
    im, d = shop_frame(GREEN_DARK, ('花', 'FLOWERS'), back=(222, 232, 216))
    rnd = random.Random(11)
    blooms = [RED, PINK, YELLOW, WHITE, PURPLE, ORANGE]
    d.rectangle([4, 22, 91, 24], fill=GREEN)
    for row, (y, xs) in enumerate(((40, range(8, 86, 13)), (54, range(6, 88, 12)))):   # buckets on two steps
        for i, x in enumerate(xs):
            colour = blooms[(i + row * 2) % len(blooms)]
            d.ellipse([x - 1, y - 12, x + 9, y - 3], fill=LEAF)
            for _ in range(7):
                px, py = x + rnd.randint(0, 8), y - rnd.randint(4, 12)
                d.rectangle([px, py, px + 1, py + 1], fill=colour)
            d.polygon([(x, y - 3), (x + 8, y - 3), (x + 7, y + 5), (x + 1, y + 5)], fill=STEEL_LIGHT, outline=INK)
        d.line([4, y + 6, 91, y + 6], fill=INK)
        d.rectangle([4, y + 7, 91, y + 8], fill=WOOD)
    return im


def shop_shutter():
    im, d = shop_frame(STEEL, ('', ''), back=STEEL_LIGHT)
    for y in range(24, 62, 3):                              # the roller shutter's slats
        d.line([4, y, 91, y], fill=STEEL)
    d.line([4, 22, 91, 22], fill=INK)
    d.rectangle([4, 59, 91, 62], fill=STEEL_DARK)
    d.rectangle([44, 58, 51, 60], fill=INK)                 # its handle
    box(d, 21, 32, 74, 47, WHITE)                           # the notice: tenant wanted
    centred(d, 48, 34, 'テナント', kana(), BLUE_DARK)
    return im


SHOPS = {'bakery': shop_bakery, 'kissa': shop_kissa, 'bar': shop_bar, 'books': shop_books,
         'flowers': shop_flowers, 'shutter': shop_shutter}


# ---- exits ---------------------------------------------------------------------------

def paint_sign(d, x0, y0, ja, en):
    """The yellow exit sign, 112x26 from (x0, y0): 出口, the place's name, and its name in English."""
    box(d, x0, y0, x0 + 111, y0 + 25, YELLOW)
    d.line([x0 + 1, y0 + 24, x0 + 110, y0 + 24], fill=YELLOW_DARK)
    wj = text_size(d, ja, kana())[0]
    x = x0 + 56 - (28 + 4 + wj) // 2
    d.rectangle([x, y0 + 2, x + 27, y0 + 14], fill=INK)
    text(d, x + 2, y0 + 3, '出口', kana(), YELLOW)
    text(d, x + 32, y0 + 3, ja, kana(), INK)
    centred(d, x0 + 56, y0 + 16, en, latin(), INK)


def exit_north(ja, en):
    def draw():
        im, d = new(4 * C, 2 * C)
        paint_wall(d, 0, 127)
        box(d, 30, 29, 97, 63, DARK)                        # the stairwell's opening
        steps = [(244, 247, 252), (226, 231, 240), STEEL_LIGHT, (176, 182, 198), STEEL, (128, 136, 158)]
        d.rectangle([34, 30, 93, 32], fill=WHITE)           # daylight at the top
        for i, colour in enumerate(steps):                  # six steps up to it
            y = 33 + i * 5
            d.rectangle([34, y, 93, y + 4], fill=colour)
            d.line([34, y + 4, 93, y + 4], fill=STEEL_DARK)
            d.line([34, y, 93, y], fill=YELLOW)
        for x in (31, 94):                                  # the side walls of the well
            d.rectangle([x, 30, x + 2, 62], fill=OFFWHITE)
        d.rectangle([63, 33, 64, 62], fill=STEEL_DARK)      # the handrail down the middle
        d.line([62, 33, 62, 62], fill=INK)
        d.line([65, 33, 65, 62], fill=INK)
        paint_sign(d, 8, 2, ja, en)
        return im
    return draw


def exit_sign(ja, en):
    def draw():
        im, d = new(4 * C, C)
        for x in (22, 104):
            d.rectangle([x, 0, x + 1, 5], fill=STEEL_DARK)
        paint_sign(d, 8, 5, ja, en)
        return im
    return draw


def exit_south():
    im, d = new(2 * C, C)
    d.rectangle([0, 0, 63, 31], fill=VOID)
    steps = [STEEL, (176, 182, 198), STEEL_LIGHT, (214, 220, 232)]
    for i, colour in enumerate(steps):                      # four steps, lighter towards the street
        y = i * 8
        d.rectangle([3, y, 60, y + 7], fill=colour)
        d.line([3, y, 60, y], fill=YELLOW)
        d.line([3, y + 7, 60, y + 7], fill=STEEL_DARK)
    for x in (0, 61):
        d.rectangle([x, 0, x + 2, 31], fill=STEEL_LIGHT)
        d.line([2 if x == 0 else 61, 0, 2 if x == 0 else 61, 31], fill=INK)
    d.rectangle([31, 0, 32, 31], fill=STEEL_DARK)
    return im


def half(draw, i):
    return lambda: draw().crop((i * C, 0, (i + 1) * C, C))


# ---- things standing in the arcade ----------------------------------------------------

def gacha():
    im, d = new(2 * C, 2 * C)
    rnd = random.Random(5)
    fronts = [RED, BLUE, YELLOW, GREEN, ORANGE, PURPLE, TEAL, PINK]
    for row in range(2):
        for col in range(4):
            x, y = 1 + col * 16, 3 + row * 30
            colour = fronts[(row * 4 + col) % len(fronts)]
            box(d, x, y, x + 13, y + 28, WHITE)
            box(d, x + 2, y + 2, x + 11, y + 13, GLASS)     # the globe of capsules
            for _ in range(9):
                px, py = x + rnd.randint(3, 9), y + rnd.randint(6, 11)
                d.rectangle([px, py, px + 1, py + 1], fill=rnd.choice(fronts))
            d.rectangle([x + 1, y + 15, x + 12, y + 27], fill=colour)
            d.ellipse([x + 4, y + 17, x + 9, y + 22], fill=STEEL_LIGHT, outline=INK)    # the crank
            d.rectangle([x + 4, y + 24, x + 9, y + 26], fill=DARK)
    d.line([1, 62, 62, 62], fill=INK)
    return im


def floor_map():
    im, d = new(C, 2 * C)
    for x in (7, 23):
        d.rectangle([x, 40, x + 1, 61], fill=STEEL_DARK)
        d.rectangle([x - 2, 61, x + 3, 62], fill=INK)
    box(d, 2, 10, 29, 44, STEEL_LIGHT)
    d.rectangle([4, 12, 27, 17], fill=TEAL)
    d.rectangle([6, 14, 16, 15], fill=WHITE)
    d.rectangle([4, 19, 27, 42], fill=CREAM)
    d.rectangle([6, 29, 25, 32], fill=TEAL)                 # the arcade, as the map shows it
    d.rectangle([8, 21, 10, 29], fill=TEAL)
    d.rectangle([18, 32, 20, 39], fill=TEAL)
    for x, y in ((8, 21), (14, 27), (24, 27), (18, 39)):
        d.rectangle([x, y, x + 2, y + 1], fill=YELLOW)
    d.rectangle([9, 24, 10, 25], fill=RED)                  # you are here
    return im


# ---- the entrance on the street --------------------------------------------------------

def entrance_snow():
    im, d = new(2 * C, 3 * C)
    # the mouth: dark beyond the first steps
    d.rectangle([8, 44, 55, 66], fill=DARK)
    steps = [(70, 78, 104), (92, 102, 128), (116, 126, 150), STEEL, (176, 182, 198), STEEL_LIGHT]
    for i, colour in enumerate(steps):                      # six steps going down, away from you
        y = 60 + i * 6
        d.rectangle([12, y, 51, y + 5], fill=colour)
        d.line([12, y + 5, 51, y + 5], fill=YELLOW_DARK if i >= 3 else INK)
    d.rectangle([31, 50, 32, 95], fill=STEEL_DARK)          # the handrail
    d.line([30, 50, 30, 95], fill=INK)
    d.line([33, 50, 33, 95], fill=INK)
    for x0 in (2, 52):                                      # the parapets either side, snow along their tops
        box(d, x0, 58, x0 + 9, 95, OFFWHITE)
        d.line([x0 + 1, 76, x0 + 8, 76], fill=STEEL_LIGHT)
        d.line([x0 + 5, 60, x0 + 5, 94], fill=STEEL_LIGHT)
        d.rectangle([x0 + 1, 59, x0 + 8, 62], fill=TEAL)
        d.rectangle([x0 - 1, 54, x0 + 10, 58], fill=SNOW, outline=None)
        d.line([x0, 58, x0 + 9, 58], fill=SNOW_SHADE)
    for x0 in (4, 56):                                      # the canopy's posts
        d.rectangle([x0, 42, x0 + 3, 57], fill=STEEL_DARK, outline=INK)
    # the glass canopy
    d.rounded_rectangle([1, 12, 62, 31], radius=6, fill=GLASS, outline=INK)
    for x in range(11, 60, 10):
        d.line([x, 13, x, 30], fill=STEEL)
    d.line([3, 22, 60, 22], fill=GLASS_DARK)
    d.line([4, 15, 20, 15], fill=WHITE)
    # the snow lying on it
    d.rounded_rectangle([0, 5, 63, 16], radius=5, fill=SNOW)
    d.line([4, 5, 59, 5], fill=SNOW_SHADE)
    d.arc([0, 5, 10, 16], 90, 270, fill=SNOW_SHADE)
    d.arc([53, 5, 63, 16], 270, 90, fill=SNOW_SHADE)
    for x, w in ((6, 9), (24, 12), (46, 8)):                # where it sags over the edge
        d.rectangle([x, 16, x + w, 17], fill=SNOW)
        d.line([x, 18, x + w, 18], fill=SNOW_SHADE)
    # the sign
    box(d, 3, 30, 60, 44, BLUE)
    d.line([4, 43, 59, 43], fill=BLUE_DARK)
    centred(d, 32, 32, '地下街', kana(), WHITE)
    return im


def sprites():
    out = {
        'chika-floor-a': floor(TILE, TILE_JOINT, TILE_LIGHT),
        'chika-floor-b': floor(TAN, TAN_JOINT, TILE),
        'chika-wall': wall(),
        'chika-wall-poster-a': wall('a'),
        'chika-wall-poster-b': wall('b'),
        'chika-side-w': edge(right=True),
        'chika-side-e': edge(left=True),
        'chika-front': edge(top=True),
        'chika-front-w': edge(top=True, right=True),
        'chika-front-e': edge(top=True, left=True),
        'chika-exit-south-w': half(exit_south, 0),
        'chika-exit-south-e': half(exit_south, 1),
        'chika-gacha': gacha,
        'chika-map': floor_map,
        'chikagai-entrance-snow': entrance_snow,
    }
    for kind, fn in SHOPS.items():
        out[f'chika-shop-{kind}'] = fn
    for town in chikagai.TOWNS.values():
        for slug, e in town['exits'].items():
            out[f'chika-exit-{slug}' if e['at'][0] != 'south' else f'chika-sign-{slug}'] = \
                (exit_north if e['at'][0] != 'south' else exit_sign)(e['ja'], e['en'])
    return out


def main():
    built = {}
    for name, fn in sprites().items():
        im = fn()
        built[name] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = name
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
