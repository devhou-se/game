#!/usr/bin/env python3
"""generate_chikagai_art.py — the art of an underground arcade (a chikagai) and
of its entrance on the street.

Drawn in the house look, the manner of the GuttyKreum packs the rest of the
world is cut from: every colour is one the pack's own sheets use
(art-source/GuttyKreum), the outline is the pack's navy, glass is the pack's
dark window with a slanted glare, and nothing is lit (an exit sign, a step's
nosing or a lamp is the pack's dim gold). Light falls from the upper left;
whatever stands proud of a wall casts a pixel of shade below and to its right.
Drawn at half size (32px a cell) and pixel-doubled, with rectangles and points
only (no Pillow ellipse, polygon, arc or slanted line, which move by a pixel
between Pillow versions); the text is set in the game's own fonts, so a re-run
is byte-identical on any machine.

This tool owns its palette. From tools/generate_station_art.py it takes only
the canvas and the text helpers, and from tools/generate_sendai_art.py the
pack's window (pane), its leafy clumps (foliage) and its scatter (speck). The
arcade also uses the station's bench, planters, pillar, lockers and tactile
paving as they are.

  chika-floor-a / -b            the floor: cool white tile, and the stone apron in front of the shops
  chika-wall, -wall-poster-a/-b the back wall, 1x2 (a teal band), plain or with a framed advert
  chika-side-w / -e, -front, -front-w / -e
                                the tops of the walls you look over: beside the floor, in
                                front of it, and where a stem leaves the hall
  chika-shop-<kind>             a 3x2 shopfront in the back wall: bakery, kissa (coffee) and
                                bar sell over the counter, books, flowers and shutter say a
                                line (src/utils/Interactions.js)
  chika-exit-<slug>             4x2, the stairs up to the street in the back wall under a
                                gold exit sign, one per exit of every town in tools/chikagai.py
  chika-sign-<slug>             4x1, the same sign hung from the ceiling (Tops), for an
                                exit in a south wall
  chika-exit-south-w / -e       the foot of the stairs in a south wall, in two cells
  chika-gacha                   2x2 capsule-toy machines
  chika-map                     1x2 floor map on a stand
  chikagai-entrance-snow        2x3, the entrance on the street: a glass roof seen from
                                above under the snow, the blue sign, the steps going down

Run from gamev2/:  python3 tools/generate_chikagai_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import random
import sys

from PIL import Image

import chikagai
from generate_station_art import C, new, text, text_size, kana, latin
from generate_sendai_art import pane, foliage, speck


def rgb(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---- the palette: every colour is one the GuttyKreum sheets use ----------------------

INK, EDGE = rgb('080d16'), rgb('172459')                    # the void; the outline
W0, W1, W2, W3, W4, W5 = (rgb(c) for c in ('fafcfd', 'dae2e4', 'bcc7cc', 'a4b0b5', '848295', '646e86'))
ST0, ST1, ST2, ST3 = (rgb(c) for c in ('e4cecc', 'd7b6ab', 'be9e8c', '8e7366'))     # stone
SL0, SL1, SL2 = rgb('78768a'), rgb('5f6177'), rgb('47485d')                          # slate
STEEL_HI, STEEL, STEEL_LO = rgb('d1e2eb'), rgb('94a2a8'), rgb('575c6d')
TEAL0, TEAL1, TEAL2, TEAL3, TEAL4 = (rgb(c) for c in ('93c297', '508582', '4a6262', '395050', '2e4040'))
GOLD_HI, GOLD, GOLD_LO, GOLD_DK = rgb('f3d890'), rgb('c6a663'), rgb('a7843b'), rgb('86624f')
RED_HI, RED, RED_LO = rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')
ORANGE_HI, ORANGE, ORANGE_DK = rgb('f6a583'), rgb('ce6a42'), rgb('904a37')
BLUE_HI, BLUE, BLUE_LO, BLUE_DK = rgb('7db9fa'), rgb('588cc6'), rgb('425faa'), rgb('314b8e')
WOOD_HI, WOOD, WOOD_LO, WOOD_DK, WOOD_DEEP = ST2, rgb('a68777'), rgb('7c5d56'), rgb('594b45'), rgb('5a3827')
KISSA = rgb('7f513b')
BREAD_HI, BREAD, BREAD_LO = rgb('e3c587'), rgb('bb8971'), GOLD_DK
NIGHT_HI, NIGHT = rgb('3c3a4c'), rgb('1b1e2a')
PINK_HI, PINK, PINK_LO = rgb('d78bc1'), rgb('bb6479'), rgb('83374f')
PURPLE_HI, PURPLE, PURPLE_LO = rgb('bfabd7'), rgb('8f72b6'), rgb('444679')
SAGE_HI, SAGE, SAGE_LO = TEAL0, rgb('6c8e7f'), rgb('506b6b')
GREEN = rgb('83af6f')
GLASS, GLASS_LO, GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')
SNOW_HI, SNOW, SNOW_LO = W0, rgb('ecfaff'), rgb('b7c3e3')
LEAF = [rgb(c) for c in ('b1dfdc', '93c297', '83af6f', '508582', '425faa', '3c396d')]
SHADE = rgb('2a3151', 90)                                   # on the floor, under what stands on it

# the next colour down each ramp: what a thing standing proud of it casts on it
DOWN = {}
for ramp in ((W0, W1, W2, W3, W4, W5), (ST0, ST1, ST2, ST3), (TEAL0, TEAL1, TEAL2, TEAL3, TEAL4),
             (GOLD_HI, GOLD, GOLD_LO, GOLD_DK), (SL0, SL1, SL2), (STEEL_HI, STEEL, STEEL_LO)):
    for a, b in zip(ramp, ramp[1:]):
        DOWN.setdefault(a, b)


# ---- helpers (half-size pixels, inclusive coordinates) ---------------------------------

def R(d, x0, y0, x1, y1, fill):
    if x1 >= x0 and y1 >= y0:
        d.rectangle([x0, y0, x1, y1], fill=fill)


def box(d, x0, y0, x1, y1, base, hi, lo, edge=EDGE):
    """An outlined block, lit along its top and left, shaded along its bottom and right."""
    R(d, x0, y0, x1, y1, edge)
    R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, base)
    R(d, x0 + 1, y0 + 1, x1 - 1, y0 + 1, hi)
    R(d, x0 + 1, y0 + 1, x0 + 1, y1 - 1, hi)
    R(d, x0 + 1, y1 - 1, x1 - 1, y1 - 1, lo)
    R(d, x1 - 1, y0 + 1, x1 - 1, y1 - 1, lo)


def cast(im, x0, y0, x1, y1):
    """The shade of something standing proud: each pixel one down its ramp. Call
    before drawing the thing that casts it."""
    px = im.load()
    for y in range(max(0, y0), min(im.height - 1, y1) + 1):
        for x in range(max(0, x0), min(im.width - 1, x1) + 1):
            c = px[x, y]
            if c[3] == 0:
                px[x, y] = SHADE
            elif c in DOWN:
                px[x, y] = DOWN[c]


def label(d, x, y, s, f, fill, shadow=None):
    if shadow:
        text(d, x + 1, y + 1, s, f, shadow)
    text(d, x, y, s, f, fill)


def centred(d, cx, y, s, f, fill, shadow=None):
    label(d, cx - text_size(d, s, f)[0] // 2, y, s, f, fill, shadow)


def ring(im):
    """Close the shape: every clear pixel beside an opaque one becomes outline."""
    px = im.load()
    hits = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3] == 0 and any(
        0 <= x + dx < im.width and 0 <= y + dy < im.height and px[x + dx, y + dy][3] == 255
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in hits:
        px[p] = EDGE


def spans(d, rows, fill):
    """A shape a row at a time: rows is [(y, x0, x1), ...]."""
    for y, x0, x1 in rows:
        R(d, x0, y, x1, y, fill)


# ---- floor and walls -------------------------------------------------------------

def floor(base, hi, joint, seed):
    def draw():
        im, d = new(C, C)
        R(d, 0, 0, 31, 31, base)
        for y in range(32):
            for x in range(32):
                if x % 16 == 15 or y % 16 == 15:
                    d.point((x, y), fill=joint)
                elif y % 16 == 0:
                    d.point((x, y), fill=hi)
        rnd, n = random.Random(seed), 0
        while n < 7:
            x, y = rnd.randint(0, 31), rnd.randint(0, 31)
            if x % 16 != 15 and y % 16 not in (0, 15):
                d.point((x, y), fill=joint)
                n += 1
        return im
    return draw


def paint_wall(d, x0, x1):
    """The back wall's face over columns x0..x1 of a 64px-tall canvas."""
    for y, c in enumerate((EDGE, SL0, SL1, SL2)):           # the ceiling's edge
        R(d, x0, y, x1, y, c)
    R(d, x0, 4, x1, 39, W0)                                 # white tile
    R(d, x0, 4, x1, 5, W2)
    R(d, x0, 6, x1, 6, W1)
    for y in (16, 28):
        R(d, x0, y, x1, y, W1)
    for x in range(x0, x1 + 1):
        if x % 16 == 15:
            R(d, x, 7, x, 15, W1)
            R(d, x, 29, x, 39, W1)
        if x % 16 == 7:
            R(d, x, 17, x, 27, W1)
    for y, c in zip(range(40, 46), (EDGE, TEAL0, TEAL1, TEAL1, TEAL2, EDGE)):   # the band
        R(d, x0, y, x1, y, c)
    R(d, x0, 46, x1, 57, ST0)                               # the dado
    R(d, x0, 46, x1, 46, ST2)
    R(d, x0, 57, x1, 57, ST1)
    for x in range(x0, x1 + 1):
        if x % 8 == 7:
            R(d, x, 47, x, 56, ST1)
    for y, c in zip(range(58, 64), (EDGE, SL0, SL1, SL1, SL2, EDGE)):          # the skirting
        R(d, x0, y, x1, y, c)


def wall(poster=None):
    def draw():
        im, d = new(C, 2 * C)
        paint_wall(d, 0, 31)
        if poster:
            cast(im, 6, 9, 27, 37)
            box(d, 5, 8, 26, 36, STEEL, STEEL_HI, STEEL_LO)
            R(d, 7, 10, 24, 34, EDGE)
        if poster == 'a':                                   # ski season: a white peak on a blue sky
            R(d, 8, 11, 23, 33, BLUE)
            R(d, 8, 11, 23, 15, BLUE_HI)
            R(d, 19, 12, 21, 14, GOLD)
            d.point((19, 12), fill=GOLD_HI)
            for y in range(14, 28):
                hw = (y - 14) * 7 // 13
                R(d, max(8, 15 - hw), y, min(23, 15 + hw), y, SNOW)
                R(d, 16, y, min(23, 15 + hw), y, SNOW_LO)
            R(d, 15, 14, 15, 14, SNOW_HI)
            R(d, 8, 28, 23, 33, RED)
            R(d, 8, 28, 23, 28, RED_HI)
            R(d, 9, 30, 22, 30, W0)
            R(d, 8, 33, 23, 33, RED_LO)
        elif poster == 'b':                                 # a sale: a red sun on gold
            R(d, 8, 11, 23, 33, GOLD)
            R(d, 8, 11, 23, 11, GOLD_HI)
            for i, hw in enumerate((3, 5, 6, 6, 7, 7, 7, 7, 6, 6, 5, 3)):
                y = 13 + i
                R(d, 16 - hw, y, 15 + hw, y, RED)
                if i >= 6:
                    d.point((15 + hw, y), fill=RED_LO)
            R(d, 13, 24, 18, 24, RED_LO)
            R(d, 12, 15, 13, 16, RED_HI)
            d.point((14, 14), fill=RED_HI)
            R(d, 9, 27, 22, 28, EDGE)
            R(d, 9, 30, 18, 31, GOLD_DK)
        return im
    return draw


def edge(top=False, left=False, right=False):
    """The top of a wall seen from above: a strip along the named sides of a dark cell."""
    def draw():
        im, d = new(C, C)
        R(d, 0, 0, 31, 31, INK)
        if top:
            for y, c in enumerate((W1, W2, W2, W2, W4, EDGE)):
                R(d, 0, y, 31, y, c)
        y0 = 5 if top else 0
        if left:
            for x, c in enumerate((W1, W2, W2, W2, W4, EDGE)):
                R(d, x, y0, x, 31, c)
        if right:
            for x, c in zip(range(26, 32), (EDGE, W1, W2, W2, W2, W4)):
                R(d, x, y0, x, 31, c)
        return im
    return draw


# ---- shopfronts --------------------------------------------------------------------

def shop_frame(fascia, name, ink=W0, shadow=None, back=W1, back_lo=W2):
    """A 3x2 shopfront: ceiling, the fascia with its name, the opening and a counter."""
    im, d = new(3 * C, 2 * C)
    for y, c in enumerate((EDGE, SL0, SL1, SL2)):
        R(d, 0, y, 95, y, c)
    base, hi, lo = fascia
    box(d, 0, 4, 95, 21, base, hi, lo)
    R(d, 1, 19, 94, 20, lo)
    ja, en = name
    w = (text_size(d, ja, kana())[0] if ja else 0) + (text_size(d, en, latin())[0] if en else 0) + (6 if ja and en else 0)
    x = 48 - w // 2
    if ja:
        label(d, x, 7, ja, kana(), ink, shadow)
        x += text_size(d, ja, kana())[0] + 6
    if en:
        label(d, x, 9, en, latin(), ink, shadow)
    R(d, 0, 22, 95, 63, back)
    R(d, 4, 22, 91, 24, back_lo)                            # the fascia's shade
    for x0 in (0, 92):                                      # the pilasters either side
        R(d, x0, 21, x0 + 3, 63, EDGE)
        R(d, x0 + 1, 22, x0 + 1, 62, W0)
        R(d, x0 + 2, 22, x0 + 2, 62, W2)
    R(d, 0, 63, 95, 63, EDGE)
    return im, d


def counter(d, y, base, hi, lo):
    R(d, 4, y, 91, 62, base)
    R(d, 4, y, 91, y, EDGE)
    R(d, 4, y + 1, 91, y + 1, hi)
    R(d, 4, y + 2, 91, y + 2, lo)
    for x in range(15, 91, 12):
        R(d, x, y + 3, x, 58, lo)
    R(d, 4, 59, 91, 62, lo)


def loaf(d, x, y, tin):
    """An 8x5 loaf from (x, y): crust, a lit top, a dark foot and right side."""
    R(d, x, y, x + 7, y + 4, BREAD)
    R(d, x, y, x + 7, y, BREAD_HI)
    R(d, x + 7, y, x + 7, y + 4, BREAD_LO)
    R(d, x, y + 4, x + 7, y + 4, BREAD_LO)
    if not tin:                                             # a cob: its top corners rounded off
        d.point((x, y), fill=ST1)
        d.point((x + 7, y), fill=ST1)
        d.point((x + 1, y), fill=BREAD_HI)


def shop_bakery():
    im, d = shop_frame((ORANGE, ORANGE_HI, RED), ('ベーカリー', ''), shadow=ORANGE_DK, back=ST1, back_lo=ST2)
    for i, x in enumerate(range(4, 92, 8)):                 # the awning: stripes, a scalloped foot
        c, lo = (ORANGE, RED) if i % 2 == 0 else (W0, W2)
        R(d, x, 22, x + 7, 26, c)
        R(d, x, 22, x + 7, 22, ORANGE_HI if i % 2 == 0 else W0)
        R(d, x, 27, x + 7, 27, lo)
        R(d, x + 1, 28, x + 6, 28, lo)
        d.point((x, 28), fill=EDGE)
        d.point((x + 7, 28), fill=EDGE)
        R(d, x + 2, 29, x + 5, 29, EDGE)
    for y in (37, 45):                                      # two shelves of loaves
        R(d, 6, y, 89, y, WOOD_LO)
        for i, x in enumerate(range(8, 86, 10)):
            loaf(d, x, y - 5, (i + y) % 3 == 0)
    counter(d, 46, WOOD, WOOD_HI, WOOD_LO)
    R(d, 8, 48, 60, 58, EDGE)                               # the glass case
    pane(d, 9, 49, 59, 57, 11)
    for x in range(12, 57, 10):                             # buns, seen through it
        R(d, x, 53, x + 6, 56, BREAD)
        R(d, x + 1, 53, x + 5, 53, BREAD_HI)
        R(d, x, 53, x, 53, GLASS)
        R(d, x + 6, 53, x + 6, 53, GLASS)
        R(d, x + 1, 56, x + 6, 56, BREAD_LO)
    R(d, 10, 59, 58, 59, STEEL)
    box(d, 68, 49, 84, 57, STEEL, STEEL_HI, STEEL_LO)       # the till
    R(d, 70, 51, 78, 53, GLASS)
    d.point((71, 51), fill=GLARE)
    R(d, 80, 53, 81, 54, GOLD)
    return im


def shop_kissa():
    im, d = shop_frame((KISSA, WOOD, WOOD_DK), ('喫茶', 'COFFEE'), ink=GOLD, shadow=WOOD_DEEP,
                       back=WOOD_LO, back_lo=WOOD_DK)
    for x in range(15, 91, 16):                             # the panelled back wall
        R(d, x, 25, x, 45, WOOD_DK)
    for x in (24, 48, 72):                                  # hanging lamps, not lit
        R(d, x, 22, x, 26, EDGE)
        for i in range(4):
            y, hw = 27 + i, i + 1
            R(d, x - hw, y, x + hw, y, GOLD_DK if i == 3 else GOLD)
            if i < 3:
                d.point((x - hw, y), fill=GOLD_HI)
                d.point((x + hw, y), fill=GOLD_LO)
        R(d, x - 1, 31, x + 1, 32, GOLD_HI)
    R(d, 6, 43, 89, 43, WOOD_DK)                            # the back shelf: cups, a row of jars
    for x in range(8, 40, 6):
        R(d, x, 39, x + 3, 42, EDGE)
        R(d, x + 1, 40, x + 2, 41, W0)
        d.point((x + 2, 41), fill=W2)
    for i, x in enumerate(range(54, 88, 7)):
        R(d, x, 36, x + 4, 42, EDGE)
        R(d, x + 1, 37, x + 3, 41, (BREAD, GOLD_LO, WOOD)[i % 3])
        R(d, x + 1, 37, x + 3, 37, BREAD_HI)
        R(d, x + 3, 38, x + 3, 41, (BREAD_LO, GOLD_DK, WOOD_LO)[i % 3])
    counter(d, 46, KISSA, WOOD, WOOD_DK)
    R(d, 14, 39, 17, 45, EDGE)                              # the siphon: its stand
    R(d, 15, 40, 16, 44, STEEL)
    d.point((15, 40), fill=STEEL_HI)
    spans(d, [(32, 14, 17), (33, 13, 18), (34, 12, 19), (35, 12, 19), (36, 12, 19), (37, 13, 18), (38, 14, 17)], EDGE)
    spans(d, [(33, 14, 17), (34, 13, 18), (35, 13, 18), (36, 13, 18), (37, 14, 17)], GLASS)
    spans(d, [(36, 13, 18), (37, 14, 17)], WOOD_DEEP)
    d.point((14, 34), fill=GLARE)
    d.point((15, 33), fill=GLARE)
    for x in (30, 40):                                      # two cups set out
        R(d, x, 42, x + 4, 45, EDGE)
        R(d, x + 1, 43, x + 3, 44, W0)
        R(d, x + 3, 43, x + 3, 44, W2)
        d.point((x + 5, 43), fill=EDGE)
    R(d, 58, 49, 86, 57, EDGE)                              # the chalk board
    R(d, 59, 50, 85, 56, TEAL4)
    for y in (51, 53, 55):
        R(d, 61, y, 61 + (y * 7) % 19 + 4, y, W3)
    return im


def shop_bar():
    im, d = shop_frame((NIGHT, NIGHT_HI, INK), ('立呑み', ''), back=BREAD, back_lo=BREAD_LO)
    for x in (6, 84):                                       # a red lantern at each end of the name
        R(d, x + 1, 6, x + 5, 6, WOOD_DK)
        R(d, x + 1, 18, x + 5, 18, WOOD_DK)
        R(d, x + 1, 7, x + 5, 17, RED)
        R(d, x, 8, x + 6, 16, RED)
        R(d, x, 8, x, 16, RED_HI)
        R(d, x + 1, 7, x + 1, 7, RED_HI)
        R(d, x + 6, 8, x + 6, 16, RED_LO)
        R(d, x + 5, 17, x + 5, 17, RED_LO)
        for y in (10, 14):
            R(d, x + 1, y, x + 5, y, RED_LO)
    R(d, 6, 40, 89, 40, WOOD_DK)                            # the bottles behind
    rnd = random.Random(7)
    for x in range(8, 88, 5):
        colour = rnd.choice([SAGE_LO, KISSA, W1, GOLD_LO])
        R(d, x, 33, x + 2, 39, EDGE)
        R(d, x + 1, 34, x + 1, 38, colour)
        d.point((x + 1, 31), fill=EDGE)
        d.point((x + 1, 32), fill=colour)
    R(d, 4, 22, 91, 22, EDGE)                               # the short curtain, in five panels
    for x in range(4, 92, 18):
        x1 = min(x + 16, 91)
        R(d, x, 23, x1, 30, RED)
        R(d, x, 23, x1, 23, RED_HI)
        R(d, x, 30, x1, 30, RED_LO)
        R(d, x1, 23, x1, 30, RED_LO)
        R(d, x + 7, 25, x + 9, 25, W0)
        R(d, x + 7, 29, x + 9, 29, W0)
        R(d, x + 6, 26, x + 6, 28, W0)
        R(d, x + 10, 26, x + 10, 28, W0)
    counter(d, 46, ST2, ST0, ST3)
    for x in (16, 44, 70):                                  # glasses of beer on the counter
        R(d, x, 41, x + 4, 45, EDGE)
        R(d, x + 1, 42, x + 3, 44, GOLD)
        R(d, x + 1, 42, x + 3, 42, W0)
        R(d, x + 3, 43, x + 3, 44, GOLD_LO)
    R(d, 28, 43, 34, 45, EDGE)                              # a dish of edamame
    R(d, 29, 44, 33, 44, GREEN)
    d.point((30, 44), fill=TEAL0)
    return im


SPINES = [(RED, RED_LO), (GOLD, GOLD_LO), (TEAL1, TEAL2), (BLUE, BLUE_LO), (ST0, ST1), (ORANGE, RED),
          (PURPLE, PURPLE_LO), (TEAL0, SAGE), (WOOD, WOOD_LO), (PINK_HI, PINK)]


def shop_books():
    im, d = shop_frame((BLUE_LO, BLUE, BLUE_DK), ('本', 'BOOKS'), shadow=EDGE, back=WOOD_DK, back_lo=WOOD_DEEP)
    rnd = random.Random(3)
    for y0 in (24, 35):                                     # two shelves of spines
        x = 6
        while x < 88:
            w = rnd.choice([2, 2, 3])
            base, lo = rnd.choice(SPINES)
            top = y0 + rnd.choice([0, 0, 1, 2])
            R(d, x, top, x + w - 1, y0 + 8, base)
            R(d, x + w - 1, top, x + w - 1, y0 + 8, lo)
            R(d, x, y0 + 5, x + w - 1, y0 + 5, lo)
            x += w + (1 if rnd.random() < 0.2 else 0)
        R(d, 4, y0 + 9, 91, y0 + 9, WOOD)
        R(d, 4, y0 + 10, 91, y0 + 10, WOOD_DEEP)
    counter(d, 46, WOOD, WOOD_HI, WOOD_LO)
    for i, x in enumerate(range(8, 86, 12)):                # magazines laid out face up
        base, lo = SPINES[(i * 3) % len(SPINES)]
        R(d, x, 49, x + 8, 58, EDGE)
        R(d, x + 1, 50, x + 7, 57, base)
        R(d, x + 2, 51, x + 6, 53, W0)
        R(d, x + 2, 55, x + 6, 55, lo)
        R(d, x + 7, 50, x + 7, 57, lo)
    return im


BLOOMS = [(RED_HI, RED), (PINK_HI, PINK), (GOLD_HI, GOLD), (W0, W1), (PURPLE_HI, PURPLE), (ORANGE_HI, ORANGE)]


def shop_flowers():
    im, d = shop_frame((TEAL1, TEAL0, TEAL3), ('花', 'FLOWERS'), shadow=TEAL4, back=W1, back_lo=W3)
    rnd = random.Random(11)
    R(d, 4, 22, 91, 24, SAGE)                               # the pelmet
    R(d, 4, 22, 91, 22, SAGE_HI)
    R(d, 4, 24, 91, 24, SAGE_LO)
    n = 0
    for row, (y, xs) in enumerate(((40, range(8, 86, 13)), (54, range(6, 88, 12)))):   # buckets on two steps
        for i, x in enumerate(xs):
            hi, base = BLOOMS[(i + row * 2) % len(BLOOMS)]
            foliage(im, [(x + 4, y - 8, 6, 5)], LEAF, seed=n)
            n += 1
            for _ in range(6):
                px, py = x + rnd.randint(0, 7), y - rnd.randint(5, 12)
                R(d, px, py, px + 1, py + 1, base)
                d.point((px, py), fill=hi)
            R(d, x, y - 3, x + 8, y + 1, EDGE)              # the bucket, galvanised
            R(d, x + 1, y + 2, x + 7, y + 5, EDGE)
            R(d, x + 1, y - 2, x + 7, y + 1, W3)
            R(d, x + 2, y + 2, x + 6, y + 4, W3)
            R(d, x + 1, y - 2, x + 7, y - 2, W1)
            R(d, x + 1, y - 1, x + 1, y + 1, W1)
            R(d, x + 2, y + 2, x + 2, y + 4, W1)
            R(d, x + 7, y - 1, x + 7, y + 1, W4)
            R(d, x + 6, y + 2, x + 6, y + 4, W4)
        R(d, 4, y + 6, 91, y + 6, EDGE)
        R(d, 4, y + 7, 91, y + 8, WOOD)
        R(d, 4, y + 8, 91, y + 8, WOOD_LO)
    return im


def shop_shutter():
    im, d = shop_frame((STEEL, STEEL_HI, STEEL_LO), ('', ''))
    R(d, 4, 22, 91, 22, EDGE)
    for y in range(23, 59):                                 # the roller shutter's slats
        R(d, 4, y, 91, y, (W1, W2, W4)[(y - 23) % 3])
    cast(im, 4, 23, 91, 25)                                 # in the fascia's shade
    R(d, 4, 59, 91, 62, W5)                                 # its bottom bar and handle
    R(d, 44, 58, 51, 60, EDGE)
    R(d, 45, 59, 50, 59, STEEL)
    cast(im, 22, 33, 75, 48)                                # the notice: tenant wanted
    R(d, 21, 32, 74, 47, EDGE)
    R(d, 22, 33, 73, 46, W0)
    centred(d, 48, 34, 'テナント', kana(), BLUE_DK)
    return im


SHOPS = {'bakery': shop_bakery, 'kissa': shop_kissa, 'bar': shop_bar, 'books': shop_books,
         'flowers': shop_flowers, 'shutter': shop_shutter}


# ---- exits ---------------------------------------------------------------------------

def paint_sign(im, d, x0, y0, ja, en, on_wall=True):
    """The gold exit sign, 112x26 from (x0, y0): 出口, the place's name, and its name in English."""
    if on_wall:
        cast(im, x0 + 1, y0 + 1, x0 + 112, y0 + 26)
    box(d, x0, y0, x0 + 111, y0 + 25, GOLD, GOLD_HI, GOLD_LO)
    wj = text_size(d, ja, kana())[0]
    x = x0 + 56 - (28 + 4 + wj) // 2
    R(d, x, y0 + 2, x + 27, y0 + 14, EDGE)
    text(d, x + 2, y0 + 3, '出口', kana(), GOLD_HI)
    text(d, x + 32, y0 + 3, ja, kana(), EDGE)
    centred(d, x0 + 56, y0 + 16, en, latin(), EDGE)


def exit_north(ja, en):
    def draw():
        im, d = new(4 * C, 2 * C)
        paint_wall(d, 0, 127)
        R(d, 30, 29, 97, 63, EDGE)                          # the stairwell's opening
        R(d, 31, 30, 96, 62, INK)
        R(d, 34, 30, 93, 32, W0)                            # daylight at the top
        steps = [SNOW, W1, W2, W3, W4, W5]
        for i, c in enumerate(steps):                       # six steps up to it
            y = 33 + i * 5
            R(d, 34, y, 93, y, GOLD_HI if i == 0 else GOLD)
            R(d, 34, y + 1, 93, y + 2, c)
            R(d, 34, y + 3, 93, y + 4, DOWN.get(c, W1) if c != W5 else SL1)
        for x, out in ((31, 31), (94, 96)):                 # the side walls of the well
            R(d, x, 30, x + 2, 62, W2)
            R(d, out, 30, out, 62, W1)
        R(d, 62, 33, 65, 62, EDGE)                          # the handrail down the middle
        R(d, 63, 33, 63, 62, STEEL_HI)
        R(d, 64, 33, 64, 62, STEEL)
        paint_sign(im, d, 8, 2, ja, en)
        return im
    return draw


def exit_sign(ja, en):
    def draw():
        im, d = new(4 * C, C)
        for x in (22, 104):
            R(d, x, 0, x + 1, 5, STEEL_LO)
        paint_sign(im, d, 8, 5, ja, en, on_wall=False)
        return im
    return draw


def exit_south():
    im, d = new(2 * C, C)
    R(d, 0, 0, 63, 31, INK)
    for i, c in enumerate((W4, W3, W2, W1)):                # four steps, lighter towards the street
        y = i * 8
        R(d, 3, y, 60, y + 7, c)
        R(d, 3, y, 60, y, GOLD)
        R(d, 3, y + 6, 60, y + 7, DOWN[c])
    for x, inner in ((0, 2), (61, 61)):
        R(d, x, 0, x + 2, 31, W2)
        R(d, inner, 0, inner, 31, EDGE)
    R(d, 30, 0, 33, 31, EDGE)                               # the handrail
    R(d, 31, 0, 31, 31, STEEL_HI)
    R(d, 32, 0, 32, 31, STEEL)
    return im


def half(draw, i):
    return lambda: draw().crop((i * C, 0, (i + 1) * C, C))


# ---- things standing in the arcade ----------------------------------------------------

FRONTS = [(RED_HI, RED, RED_LO), (BLUE_HI, BLUE, BLUE_LO), (GOLD_HI, GOLD, GOLD_LO), (TEAL0, TEAL1, TEAL2),
          (ORANGE_HI, ORANGE, RED), (PURPLE_HI, PURPLE, PURPLE_LO), (SAGE_HI, SAGE, SAGE_LO), (PINK_HI, PINK, PINK_LO)]


def gacha():
    im, d = new(2 * C, 2 * C)
    rnd = random.Random(5)
    for row in range(2):
        for col in range(4):
            x, y = 1 + col * 16, 3 + row * 30
            hi, base, lo = FRONTS[row * 4 + col]
            R(d, x, y, x + 13, y + 28, EDGE)                # the cabinet
            R(d, x + 1, y + 1, x + 12, y + 27, W0)
            R(d, x + 12, y + 1, x + 12, y + 27, W2)
            R(d, x + 2, y + 2, x + 11, y + 13, EDGE)        # the globe of capsules
            pane(d, x + 3, y + 3, x + 10, y + 12, 7)
            for _ in range(7):
                px, py = x + rnd.randint(3, 9), y + rnd.randint(8, 11)
                R(d, px, py, px + 1, py + 1, FRONTS[rnd.randrange(len(FRONTS))][1])
                d.point((px, py), fill=FRONTS[rnd.randrange(len(FRONTS))][0])
            R(d, x + 1, y + 15, x + 12, y + 27, base)       # the front, in the machine's colour
            R(d, x + 1, y + 15, x + 12, y + 15, hi)
            R(d, x + 12, y + 15, x + 12, y + 27, lo)
            R(d, x + 1, y + 27, x + 12, y + 27, lo)
            spans(d, [(y + 17, x + 5, x + 8), (y + 18, x + 4, x + 9), (y + 19, x + 4, x + 9),
                      (y + 20, x + 4, x + 9), (y + 21, x + 4, x + 9), (y + 22, x + 5, x + 8)], STEEL)   # the crank
            spans(d, [(y + 17, x + 5, x + 7), (y + 18, x + 4, x + 4), (y + 19, x + 4, x + 4)], STEEL_HI)
            spans(d, [(y + 22, x + 6, x + 8), (y + 21, x + 9, x + 9), (y + 20, x + 9, x + 9)], STEEL_LO)
            R(d, x + 6, y + 19, x + 7, y + 20, EDGE)
            R(d, x + 4, y + 24, x + 9, y + 26, NIGHT)       # the chute
    R(d, 1, 62, 62, 62, EDGE)
    R(d, 1, 63, 62, 63, SHADE)
    return im


def floor_map():
    im, d = new(C, 2 * C)
    for x in (7, 23):
        R(d, x, 44, x + 1, 60, STEEL_LO)
        R(d, x - 2, 61, x + 3, 61, EDGE)
        R(d, x - 2, 62, x + 4, 63, SHADE)
    box(d, 2, 10, 29, 44, STEEL, STEEL_HI, STEEL_LO)
    R(d, 4, 12, 27, 17, TEAL1)
    R(d, 4, 12, 27, 12, TEAL0)
    R(d, 6, 14, 16, 15, W0)
    R(d, 4, 19, 27, 42, ST0)
    R(d, 6, 29, 25, 32, TEAL1)                              # the arcade, as the map shows it
    R(d, 8, 21, 10, 29, TEAL1)
    R(d, 18, 32, 20, 39, TEAL1)
    for x, y in ((8, 21), (14, 27), (24, 27), (18, 39)):
        R(d, x, y, x + 2, y + 1, GOLD)
    R(d, 9, 24, 10, 25, RED)                                # you are here
    return im


# ---- the entrance on the street --------------------------------------------------------

def entrance_snow():
    im, d = new(2 * C, 3 * C)
    px = im.load()
    R(d, 8, 44, 55, 66, INK)                                # the mouth: dark beyond the first steps
    steps = [SL2, SL1, SL0, W4, W3, W2]
    lower = [NIGHT_HI, SL2, SL1, W5, W4, W3]
    for i, c in enumerate(steps):                           # six steps going down, away from you
        y = 60 + i * 6
        R(d, 12, y, 51, y + 5, c)
        R(d, 12, y, 51, y, steps[i + 1] if i < 3 else GOLD)
        R(d, 12, y + 5, 51, y + 5, lower[i])
    R(d, 30, 50, 33, 95, EDGE)                              # the handrail
    R(d, 31, 50, 31, 95, STEEL_HI)
    R(d, 32, 50, 32, 95, STEEL)
    for x0 in (2, 52):                                      # the parapets either side, snow along their tops
        box(d, x0, 58, x0 + 9, 95, W1, W0, W2)
        R(d, x0 + 1, 59, x0 + 8, 62, TEAL1)
        R(d, x0 + 1, 59, x0 + 8, 59, TEAL0)
        R(d, x0 + 1, 62, x0 + 8, 62, TEAL2)
        R(d, x0 + 2, 76, x0 + 7, 76, W2)
        R(d, x0, 53, x0 + 9, 58, SNOW)
        R(d, x0 + 1, 53, x0 + 8, 53, SNOW_HI)
        R(d, x0, 54, x0 + 9, 54, SNOW_HI)
        R(d, x0, 58, x0 + 9, 58, SNOW_LO)
        R(d, x0 + 9, 54, x0 + 9, 58, SNOW_LO)
        d.point((x0, 53), fill=(0, 0, 0, 0))
    for x0 in (4, 56):                                      # the canopy's posts
        R(d, x0, 42, x0 + 3, 57, EDGE)
        R(d, x0 + 1, 42, x0 + 1, 57, STEEL)
        R(d, x0 + 2, 42, x0 + 2, 57, STEEL_LO)
    # the canopy, seen from above: a steel frame round a glass roof
    R(d, 1, 6, 62, 29, EDGE)
    R(d, 2, 7, 61, 28, STEEL)
    R(d, 2, 7, 61, 7, STEEL_HI)
    R(d, 2, 7, 2, 28, STEEL_HI)
    R(d, 2, 27, 61, 28, STEEL_LO)
    pane(d, 4, 9, 59, 25, 13)
    for x in range(13, 59, 10):
        R(d, x, 9, x, 25, STEEL)
        R(d, x + 1, 9, x + 1, 25, GLASS_LO)
    # the snow lying on it, but for its front edge
    glass = (GLASS, GLASS_LO, GLARE)
    for x in range(1, 63):
        top, foot = (5 if x in (1, 62) else 4), 19 + speck(x // 3, 1, 316) % 4
        R(d, x, top, x, foot, SNOW)
        R(d, x, top, x, top + 1, SNOW_HI)
        R(d, x, foot - 1, x, foot, SNOW_LO)
        if x >= 56:
            R(d, x, top + 2, x, foot, SNOW_LO)
        under = px[x, foot + 1]
        d.point((x, foot + 1), fill=GLASS_LO if under in glass else STEEL_LO)
        for y in range(top + 2, foot - 1):
            if speck(x, y, 317) < 3:
                d.point((x, y), fill=SNOW_LO)
    # the sign
    box(d, 3, 30, 60, 44, BLUE_LO, BLUE, BLUE_DK)
    centred(d, 32, 32, '地下街', kana(), W0, EDGE)
    ring(im)
    return im


def sprites():
    out = {
        'chika-floor-a': floor(W1, W0, W2, 316),
        'chika-floor-b': floor(ST0, W0, ST1, 317),
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
        sheet = Image.new('RGBA', (width, y + rowh + 16), rgb('5f6177'))
        for im, x, y in rows:
            sheet.alpha_composite(im, (x, y))
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
