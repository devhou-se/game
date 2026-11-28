#!/usr/bin/env python3
"""generate_flinders_art.py — everything inside the station with the clocks in
San Franbourne (issue #246).

In the manner of tools/generate_mall_art.py: the frame (the side walls, the
front wall, the doorway, the light through it), the drawing helpers and
register() are tools/generate_pub_art.py's; shaded pixel art with a 1px ink
outline, drawn at half size (32px a cell) and pixel-doubled. Nothing is random
between runs (the terrazzo's chips are seeded) and the only text (the name
board, TICKETS, the buses) is set in the game's own font, so a re-run is
byte-identical on the same machine.

The room is the inside of `sfb-clocks-station`: its mustard walls banded in
maroon, bluestone at the foot, copper green ironwork. The colours are the
building's (tools/generate_sanfranbourne_art.py), copied here as values. The
gates, the railing, the benches, the planters and the track are the station
kit's (tools/generate_station_art.py); all sprites drawn here are
`flinders-in-<piece>`:
  floor-a / floor-b       cream terrazzo (a: a maroon diamond set in it)
  side-w / side-e         the side walls seen along their length
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-bay                3x3 a bay of the back wall: mustard, maroon bands, a pilaster
  wall-arch               4x3 the back wall with an arched window, daylight in its glass
  wall-name               6x3 the back wall with the name board: FLINDERS ST
  clocks                  4x3 the board of nine dials from over the door outside, their
                          hands in the same order, on two iron posts with a rail
                          between their feet (bump it: Time Travel)
  tickets                 3x2 two ticket machines under one sign (bump them)
  board                   3x2 a departures board on a stand: every row is a bus (bump it)

Run from gamev2/:  python3 tools/generate_flinders_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames,
and the back wall's three pieces in game.lookUp.sprites.
"""
import json
import random
import sys

from generate_pub_art import (C, INK, WHITE, CREAM, CREAM_SH, GLOW, GLOW_HI, STEEL, STEEL_HI, STEEL_DK, BLACK,
                              new, box, text, mix, bar, post, shadow, latin,
                              wall_side, wall_front, threshold, doorlight, register)

# the building's colours, as tools/generate_sanfranbourne_art.py has them: the room is the inside of that sprite
MUSTARD, MUSTARD_HI, MUSTARD_LO = (224, 176, 64), (242, 208, 112), (176, 124, 44)
MAROON, MAROON_HI, MAROON_DK = (138, 58, 52), (176, 84, 70), (96, 40, 44)
COPPER, COPPER_HI, COPPER_LO = (95, 165, 138), (143, 208, 176), (60, 116, 98)
ENAMEL = (44, 58, 48)                                             # the clocks board's ground
STONE, STONE_HI, STONE_DK = (222, 210, 186), (244, 236, 216), (170, 152, 130)
BLUESTONE, BLUESTONE_HI, BLUESTONE_LO = (92, 98, 114), (119, 126, 142), (68, 73, 89)
TERRAZZO, TERRAZZO_HI, TERRAZZO_DK = (236, 226, 204), (248, 242, 228), (206, 192, 166)
DAYLIGHT, DAYLIGHT_HI, DAYLIGHT_SH = (214, 236, 240), (244, 252, 250), (176, 208, 222)
LED, LED_DIM = (255, 170, 40), (150, 96, 40)

# the frame, in stone, mustard and maroon: tools/generate_pub_art.py draws it
CONCOURSE = {'head': STONE, 'head_hi': STONE_HI, 'head_dk': STONE_DK, 'face': MUSTARD, 'face_hi': MUSTARD_HI, 'face_dk': MUSTARD_LO,
             'trim': MAROON, 'post': MAROON, 'post_hi': MAROON_HI, 'post_dk': MAROON_DK, 'sill': STONE_DK}


def centred(d, cx, y, s, fill):
    """`s` in the game's face, its ink centred on cx, its top ink row at y."""
    l, _, r, _ = d.textbbox((0, 0), s, font=latin(8))
    text(d, cx - (r - l) // 2, y, s, latin(8), fill)


# ---- the floor ----------------------------------------------------------------------------

def terrazzo(inlay, seed):
    """Cream terrazzo, a slab a cell, brass between the slabs; `inlay` sets a maroon diamond in it."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=TERRAZZO)
        rnd = random.Random(seed)
        for _ in range(46):                                         # the chips in it
            x, y = rnd.randrange(1, 32), rnd.randrange(1, 32)
            d.point((x, y), fill=rnd.choice((TERRAZZO_DK, TERRAZZO_DK, TERRAZZO_HI, TERRAZZO_HI, mix(TERRAZZO, MAROON, 0.4),
                                             mix(TERRAZZO, MUSTARD, 0.6), mix(TERRAZZO, BLUESTONE, 0.4))))
        d.line([0, 0, 31, 0], fill=TERRAZZO_DK)                     # the joints
        d.line([0, 0, 0, 31], fill=TERRAZZO_DK)
        d.line([1, 1, 30, 1], fill=TERRAZZO_HI)
        d.line([1, 1, 1, 30], fill=TERRAZZO_HI)
        if inlay:
            d.polygon([(16, 8), (24, 16), (16, 24), (8, 16)], fill=MAROON, outline=MAROON_DK)
            d.line([11, 15, 16, 10], fill=MAROON_HI)
            d.polygon([(16, 13), (19, 16), (16, 19), (13, 16)], fill=MUSTARD, outline=MUSTARD_LO)
        return im
    return draw


# ---- the back wall --------------------------------------------------------------------------
#
# Every piece is three cells tall and they join end to end: a stone cornice, the
# mustard face with a maroon band under the cornice and another at the dado, a
# panelled dado, bluestone at the foot.

BAND, DADO, FOOT = 14, 62, 86     # the upper band, the dado's band, the bluestone


def _wall(d, w):
    d.rectangle([0, 0, w - 1, 95], fill=MUSTARD)
    d.rectangle([0, 9, w - 1, 11], fill=MUSTARD_LO)                 # the shade under the cornice
    bar(d, -1, 0, w, 8, STONE, STONE_HI, STONE_DK)                  # the cornice
    d.line([0, 5, w - 1, 5], fill=STONE_DK)
    for y in (BAND, DADO):                                          # the bands, as on the street front
        d.rectangle([0, y, w - 1, y + 3], fill=MAROON)
        d.line([0, y, w - 1, y], fill=MAROON_HI)
        d.line([0, y + 3, w - 1, y + 3], fill=MAROON_DK)
    d.line([0, BAND + 4, w - 1, BAND + 4], fill=MUSTARD_HI)
    d.rectangle([0, DADO + 4, w - 1, FOOT - 1], fill=mix(MUSTARD, MUSTARD_LO, 0.35))   # the dado: a panel a cell
    for x in range(0, w, 32):
        d.rectangle([x + 3, DADO + 7, x + 28, FOOT - 4], outline=MUSTARD_LO)
        d.line([x + 4, DADO + 8, x + 27, DADO + 8], fill=MUSTARD)
        d.line([x + 4, DADO + 8, x + 4, FOOT - 5], fill=MUSTARD)
    d.rectangle([0, FOOT, w - 1, 95], fill=BLUESTONE)               # bluestone at the foot
    d.line([0, FOOT, w - 1, FOOT], fill=INK)
    d.line([0, FOOT + 1, w - 1, FOOT + 1], fill=BLUESTONE_HI)
    for x in range(0, w, 16):
        d.line([x + 7, FOOT + 2, x + 7, 94], fill=BLUESTONE_LO)
    d.line([0, 95, w - 1, 95], fill=INK)


def _lamp(d, x, y):
    """A wall lamp: an iron bracket, a glass globe under it; (x, y) is the bracket's top-left."""
    d.rectangle([x, y, x + 7, y + 2], fill=COPPER_LO, outline=INK)
    d.ellipse([x - 1, y + 2, x + 8, y + 12], fill=GLOW_HI, outline=INK)
    d.arc([x + 1, y + 4, x + 6, y + 10], 180, 280, fill=WHITE)
    d.line([x + 2, y + 13, x + 5, y + 13], fill=COPPER_LO)


def wall_bay():
    """A bay of the wall, 3x3: a pilaster up its middle, a lamp on it."""
    W = 3 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    post(d, 38, 8, 57, FOOT, MUSTARD_HI, WHITE, MUSTARD_LO)         # the pilaster, as the pavilion's corner piers
    d.rectangle([41, 9, 43, FOOT - 1], fill=mix(MUSTARD_HI, WHITE, 0.5))
    for y in (BAND, DADO):                                          # the bands run round it
        d.rectangle([38, y, 57, y + 3], fill=MAROON, outline=INK)
        d.line([39, y + 1, 56, y + 1], fill=MAROON_HI)
    d.rectangle([35, 8, 60, 12], fill=STONE, outline=INK)           # its capital
    d.line([36, 9, 59, 9], fill=STONE_HI)
    d.rectangle([35, FOOT - 5, 60, FOOT], fill=STONE, outline=INK)  # its foot
    d.line([36, FOOT - 4, 59, FOOT - 4], fill=STONE_HI)
    _lamp(d, 44, 28)
    return im


def wall_arch():
    """The wall with an arched window, 4x3: maroon frame, a fan in its head,
    pale daylight in the glass, a stone sill."""
    W = 4 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    d.pieslice([29, 11, 98, 80], 180, 360, fill=MAROON, outline=INK)        # the frame
    d.rectangle([29, 45, 98, 57], fill=MAROON)
    d.line([29, 45, 29, 57], fill=INK)
    d.line([98, 45, 98, 57], fill=INK)
    d.arc([31, 13, 96, 78], 185, 300, fill=MAROON_HI)
    d.pieslice([34, 16, 93, 75], 180, 360, fill=DAYLIGHT)                   # the glass
    d.rectangle([34, 45, 93, 56], fill=DAYLIGHT)
    d.pieslice([38, 20, 76, 66], 180, 262, fill=DAYLIGHT_HI)                # the day in it
    d.polygon([(70, 56), (82, 56), (92, 40), (92, 28)], fill=DAYLIGHT_SH)
    for a, b in (((63, 45), (38, 34)), ((63, 45), (48, 21)), ((64, 45), (79, 21)), ((64, 45), (89, 34))):
        d.line([a, b], fill=MAROON)                                         # the fan of the arch
    d.rectangle([63, 16, 64, 56], fill=MAROON)
    d.rectangle([34, 44, 93, 46], fill=MAROON)                              # the transom
    d.line([34, 44, 93, 44], fill=MAROON_HI)
    for x in (48, 79):
        d.line([x, 47, x, 56], fill=MAROON)
    d.pieslice([59, 40, 68, 49], 180, 360, fill=MAROON, outline=MAROON_DK)  # the fan's boss
    d.arc([34, 16, 93, 75], 180, 360, fill=MAROON_DK)
    d.rectangle([26, 57, 101, 61], fill=STONE, outline=INK)                 # the sill
    d.line([27, 58, 100, 58], fill=STONE_HI)
    return im


def wall_name():
    """The wall with the name board, 6x3: enamel in a copper frame, hung by two
    rods from the cornice, a lamp either side."""
    W = 6 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    for x in (62, 128):                                             # the rods it hangs by
        d.rectangle([x, 9, x + 1, 26], fill=COPPER_LO)
    box(d, 40, 26, 151, 50, COPPER)                                 # the frame
    d.line([41, 27, 150, 27], fill=COPPER_HI)
    d.line([41, 49, 150, 49], fill=COPPER_LO)
    box(d, 43, 29, 148, 47, ENAMEL)
    d.line([44, 30, 147, 30], fill=mix(ENAMEL, WHITE, 0.2))
    centred(d, 96, 35, 'FLINDERS ST', CREAM)
    for x in (41, 149):                                             # its rivets
        for y in (28, 48):
            d.point((x, y), fill=COPPER_HI)
    _lamp(d, 16, 28)
    _lamp(d, 168, 28)
    return im


# ---- what stands on the floor ---------------------------------------------------------------

def clocks():
    """The clocks, 4x3: the board of nine dials from over the doors outside
    (tools/generate_sanfranbourne_art.py: the same order of hands, a lamp under
    each), a line's plate under every dial, on two iron posts. The bottom cell
    is the posts' feet and the rail between them: that row is in the way, the
    board is over your head."""
    W = 4 * C
    im, d = new(W, 3 * C)
    shadow(d, 4, 86, 123, 95, 60)
    for x0 in (9, 113):                                             # the posts
        post(d, x0, 40, x0 + 5, 90, COPPER_LO, COPPER, ENAMEL)
        d.rectangle([x0 - 1, 56, x0 + 6, 58], fill=COPPER, outline=INK)     # a collar
        d.rectangle([x0 - 2, 88, x0 + 7, 92], fill=BLUESTONE, outline=INK)  # the foot
        d.line([x0 - 1, 89, x0 + 6, 89], fill=BLUESTONE_HI)
    bar(d, 15, 68, 112, 71, COPPER_LO, COPPER, ENAMEL)              # the rail between their feet
    d.rectangle([15, 84, 112, 85], fill=COPPER_LO)
    d.line([15, 86, 112, 86], fill=INK)
    for x in range(20, 110, 6):                                     # its balusters
        d.line([x, 72, x, 84], fill=COPPER_LO)
        d.point((x, 78), fill=COPPER)
    d.polygon([(50, 8), (64, 1), (77, 8)], fill=COPPER, outline=INK)        # the board's cresting
    d.line([53, 7, 64, 2], fill=COPPER_HI)
    box(d, 3, 8, 124, 42, COPPER)                                   # the board: a copper frame...
    d.line([4, 9, 123, 9], fill=COPPER_HI)
    d.line([4, 41, 123, 41], fill=COPPER_LO)
    box(d, 5, 11, 122, 39, ENAMEL)                                  # ...round dark enamel
    d.line([6, 12, 121, 12], fill=mix(ENAMEL, WHITE, 0.2))
    for i in range(9):                                              # the nine dials, in threes
        cx, cy = 14 + i * 12 + (i // 3) * 2, 20
        hx, hy = ((1, 0), (0, 1), (-1, 0))[i % 3]
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=WHITE, outline=INK)
        d.arc([cx - 4, cy - 4, cx + 4, cy + 4], 20, 150, fill=CREAM_SH)
        d.line([cx, cy, cx, cy - 3], fill=INK)                      # the minute hand, straight up
        d.line([cx, cy, cx + 3 * hx, cy + 3 * hy], fill=MAROON)     # the hour hand
        d.point((cx, cy), fill=INK)
        d.rectangle([cx - 4, 28, cx + 4, 32], fill=CREAM, outline=INK)      # the line's plate
        d.line([cx - 2, 30, cx + 1 + i % 2, 30], fill=ENAMEL)
        d.rectangle([cx - 1, 35, cx, 36], fill=LED)                 # its lamp
    return im


def _machine(d, x0, shift):
    """One ticket machine, 42px wide from x0: a screen, a slot for the fare card, a tray."""
    box(d, x0, 14, x0 + 41, 59, COPPER)
    d.line([x0 + 1, 15, x0 + 40, 15], fill=COPPER_HI)
    d.line([x0 + 1, 15, x0 + 1, 58], fill=COPPER_HI)
    d.line([x0 + 40, 16, x0 + 40, 58], fill=COPPER_LO)
    box(d, x0 + 4, 18, x0 + 37, 36, (40, 52, 84))                   # the screen
    d.rectangle([x0 + 6, 20, x0 + 35, 22], fill=(120, 170, 210))
    for n, y in enumerate((25, 28, 31)):                            # the fares on it
        d.line([x0 + 7, y, x0 + 16 + (n + shift) % 3 * 3, y], fill=(200, 220, 236))
        d.rectangle([x0 + 29, y - 1, x0 + 33, y], fill=LED)
    d.line([x0 + 6, 34, x0 + 12, 20], fill=(86, 104, 140))          # the glass
    box(d, x0 + 4, 39, x0 + 23, 46, STEEL)                          # where the card goes
    d.rectangle([x0 + 7, 42, x0 + 20, 43], fill=BLACK)
    d.rectangle([x0 + 10, 40, x0 + 17, 42], fill=WHITE, outline=INK)        # a card, left in it
    d.line([x0 + 12, 41, x0 + 15, 41], fill=MAROON)
    for row in range(2):                                            # the keys
        for col in range(3):
            d.rectangle([x0 + 27 + col * 4, 40 + row * 4, x0 + 28 + col * 4, 41 + row * 4], fill=CREAM)
    box(d, x0 + 4, 49, x0 + 37, 56, STEEL_DK)                       # the tray
    d.rectangle([x0 + 6, 51, x0 + 35, 55], fill=BLACK)
    d.line([x0 + 5, 50, x0 + 36, 50], fill=STEEL_HI)


def tickets():
    """Two ticket machines side by side, 3x2, under one sign."""
    W = 3 * C
    im, d = new(W, 2 * C)
    shadow(d, 2, 56, 93, 63, 60)
    _machine(d, 4, 0)
    _machine(d, 50, 1)
    d.rectangle([3, 59, 92, 62], fill=BLUESTONE, outline=INK)       # the plinth they stand on
    d.line([4, 60, 91, 60], fill=BLUESTONE_HI)
    box(d, 8, 1, 87, 14, MAROON)                                    # the sign over them
    d.line([9, 2, 86, 2], fill=MAROON_HI)
    d.line([9, 13, 86, 13], fill=MAROON_DK)
    centred(d, 48, 4, 'TICKETS', CREAM)
    return im


def board():
    """A departures board on a stand, 3x2: a platform's lamp, where to, and how
    you are going - every row is a bus."""
    W = 3 * C
    im, d = new(W, 2 * C)
    shadow(d, 8, 55, 87, 63, 60)
    for x0 in (20, 71):                                             # the stand
        post(d, x0, 44, x0 + 4, 58, STEEL_DK, STEEL, BLACK)
        d.rectangle([x0 - 6, 57, x0 + 10, 60], fill=STEEL_DK, outline=INK)
        d.line([x0 - 5, 58, x0 + 9, 58], fill=STEEL)
    box(d, 4, 1, 91, 46, STEEL_DK)                                  # the case
    d.line([5, 2, 90, 2], fill=STEEL_HI)
    d.line([5, 45, 90, 45], fill=BLACK)
    box(d, 7, 4, 88, 43, BLACK)
    for n, y in enumerate((7, 16, 25, 34)):                         # the rows
        d.rectangle([10, y + 1, 14, y + 5], fill=(90, 200, 120) if n == 0 else LED_DIM)
        for k in range(3 + (n * 2) % 3):                            # where to: too small to read
            d.rectangle([19 + k * 6, y + 2, 22 + k * 6, y + 4], fill=LED_DIM)
        text(d, 62, y, 'BUS', latin(8), LED)
        if n:
            d.line([8, y - 2, 87, y - 2], fill=(44, 46, 60))
    d.line([8, 5, 87, 5], fill=(60, 64, 84))                        # the glass
    return im


def sprites():
    p = 'flinders-in-'
    return {
        p + 'floor-a': terrazzo(True, 246), p + 'floor-b': terrazzo(False, 247),
        p + 'side-w': wall_side(CONCOURSE, 'w'), p + 'side-e': wall_side(CONCOURSE, 'e'),
        p + 'wall-front': wall_front(CONCOURSE),
        p + 'threshold-w': threshold(CONCOURSE, 'w'), p + 'threshold-e': threshold(CONCOURSE, 'e'),
        p + 'doorlight': doorlight,
        p + 'wall-bay': wall_bay, p + 'wall-arch': wall_arch, p + 'wall-name': wall_name,
        p + 'clocks': clocks, p + 'tickets': tickets, p + 'board': board,
    }


# The light through the door lies on the floor, as the pub's and the mall's.
DEPTH_BIAS = {'flinders-in-doorlight': -40}


# Worth looking up at from the platform: sprite family -> rows of building
# below the sprite (config game.lookUp.sprites, see "Looking up at landmarks"
# in hud-input-touch.md). The two rows are the track: nobody stands nearer the
# wall than the platform's edge, five rows under its top, and from there the
# ordinary camera of a landscape phone shows none of it. The whole wall is
# marked, so the view is the same from one end of the platform to the other;
# the reach has faded out a few rows into the concourse.
LOOK_UP = {'flinders-in-wall-bay': 2, 'flinders-in-wall-arch': 2, 'flinders-in-wall-name': 2}


if __name__ == '__main__':
    register(sprites(), DEPTH_BIAS, sys.argv)
    cfg = json.load(open('config.json'))
    cfg['game']['lookUp']['sprites'].update(LOOK_UP)
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
