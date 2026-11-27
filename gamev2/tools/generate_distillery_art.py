#!/usr/bin/env python3
"""generate_distillery_art.py — everything inside the tasting bar of the Nikka
distillery in Sendai (issue #217).

In the manner of tools/generate_pub_art.py, whose frame (the side walls, the
front wall, the doorway, the light through it), drawing helpers and register()
it imports: shaded pixel art with a 1px ink outline, drawn at half size (32px a
cell) and pixel-doubled. Nothing is random between runs and the only text (the
sign over the shelf) is set in the game's own font, so a re-run is
byte-identical on the same machine.

The room is the inside of the red brick kiln (`sendai-kiln`): brick, oak,
copper and stone flags. All sprites are `distillery-in-<piece>`:
  floor-a / floor-b       stone flags
  side-w / side-e         the side walls seen along their length
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-brick              1x3 a bay of the back wall: brick under a beam
  wall-window             2x3 the kiln's two arched windows, from inside
  wall-casks              4x3 casks racked three high, end on (bump them)
  wall-shelf              5x3 the bottles behind the counter, under the sign
  still                   3x4 the one copper pot still: the pot on its brick hearth, the swan
                          neck with its rope, the lyne arm down to the condenser (bump it)
  counter                 5x2 the tasting counter: the staff's aisle behind, glasses poured
                          on it (bump it: the shop list)
  stool                   an oak stool
  cask                    a cask stood on end (bump it)
  lamp-hang               1x2 a copper lamp hung from the beams (Tops)
                          (the lamps and the windows glow at night: src/utils/Glows.js)

Run from gamev2/:  python3 tools/generate_distillery_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import random
import sys

from generate_pub_art import (C, INK, WHITE, CREAM, CREAM_SH, GLOW, GLOW_HI, BRASS, BRASS_HI, BRASS_DK,
                              STEEL, STEEL_HI, STEEL_DK, BLACK, new, box, text, mix, bar, post, shadow, bottle, latin,
                              wall_side, wall_front, threshold, doorlight, register)

BRICK, BRICK_ALT, BRICK_HI, BRICK_DK = (181, 90, 64), (170, 77, 49), (208, 122, 92), (138, 64, 48)   # the kiln's own
MORTAR = (124, 58, 44)
TIMBER, TIMBER_HI, TIMBER_DK = (89, 75, 69), (134, 98, 79), (58, 48, 54)                              # the beams
OAK, OAK_HI, OAK_DK = (176, 124, 76), (214, 166, 104), (122, 80, 58)
STONE, STONE_ALT, STONE_HI, STONE_DK = (136, 132, 140), (146, 142, 146), (170, 166, 166), (100, 98, 116)
COPPER, COPPER_HI, COPPER_DK, COPPER_SHINE = (204, 118, 72), (240, 164, 104), (146, 76, 58), (255, 214, 164)
WHISKY, WHISKY_DK = (222, 150, 54), (176, 104, 44)
GLASS, GLASS_HI, SKY = (150, 190, 214), (214, 232, 240), (190, 214, 226)
HOOP, HOOP_HI = (84, 88, 108), (132, 136, 156)

# the frame, in brick: tools/generate_pub_art.py draws it
KILN = {'head': MORTAR, 'head_hi': BRICK_DK, 'head_dk': (96, 46, 44), 'face': BRICK, 'face_hi': BRICK_HI, 'face_dk': BRICK_DK,
        'trim': (190, 158, 140), 'post': TIMBER, 'post_hi': TIMBER_HI, 'post_dk': TIMBER_DK, 'sill': (188, 199, 204)}


# ---- the floor ----------------------------------------------------------------------------

def flags(shift):
    """Stone flags, two courses a cell, the joints staggered."""
    def draw():
        im, d = new(C, C)
        rnd = random.Random(2170 + shift)
        d.rectangle([0, 0, 31, 31], fill=STONE)
        for i in range(2):
            a = i * 16
            joint = (shift + i * 16) % 32
            if (i + shift) % 2:
                d.rectangle([0, a, 31, a + 15], fill=STONE_ALT)
            d.line([0, a, 31, a], fill=STONE_DK)
            d.line([0, a + 1, 31, a + 1], fill=STONE_HI)
            d.line([joint, a, joint, a + 15], fill=STONE_DK)
            d.line([(joint + 1) % 32, a + 1, (joint + 1) % 32, a + 15], fill=STONE_HI)
            for _ in range(5):                                      # the stone's grain
                x, y = rnd.randrange(32), a + 4 + rnd.randrange(10)
                d.point((x, y), fill=STONE_DK if rnd.random() < 0.6 else STONE_HI)
        return im
    return draw


# ---- the back wall ------------------------------------------------------------------------

def _bricks(d, x0, y0, x1, y1):
    """Brick in courses 4px tall, a brick 8px long, every other course shifted
    half a brick. The shades repeat every cell, so pieces of any width join."""
    d.rectangle([x0, y0, x1, y1], fill=BRICK)
    for row, y in enumerate(range(y0, y1 + 1, 4)):
        off = 4 if row % 2 else 0
        for x in range(x0 - 8 + off, x1 + 1, 8):
            n = ((x // 8) % 4 * 7 + row * 13) % 11
            col = (BRICK, BRICK, BRICK_ALT, BRICK, BRICK_DK, BRICK, BRICK_ALT, BRICK_HI, BRICK, BRICK, BRICK_ALT)[n]
            a, b = max(x, x0), min(x + 6, x1)
            if a <= b and col != BRICK:
                d.rectangle([a, y, b, min(y + 2, y1)], fill=col)
            if x0 <= x + 7 <= x1:
                d.line([x + 7, y, x + 7, min(y + 2, y1)], fill=MORTAR)
        if y + 3 <= y1:
            d.line([x0, y + 3, x1, y + 3], fill=MORTAR)


def _wall(d, w):
    """Every back-wall piece: a beam along the head, brick, a stone footing."""
    _bricks(d, 0, 8, w - 1, 87)
    bar(d, -1, 0, w, 8, TIMBER, TIMBER_HI, TIMBER_DK)               # the beam
    d.line([0, 9, w - 1, 9], fill=BRICK_DK)
    d.rectangle([0, 88, w - 1, 95], fill=STONE_DK)                  # the footing
    d.line([0, 88, w - 1, 88], fill=INK)
    d.line([0, 89, w - 1, 89], fill=STONE)
    d.line([0, 95, w - 1, 95], fill=INK)


def wall_brick():
    im, d = new(C, 3 * C)
    _wall(d, C)
    return im


def wall_window():
    """The two arched windows either side of the kiln's door, seen from
    inside: white frames, the day through them, a stone sill."""
    W = 2 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    for x0 in (6, 37):
        x1 = x0 + 20
        d.pieslice([x0 - 3, 13, x1 + 3, 39], 180, 360, fill=BRICK_DK, outline=INK)    # the arch's soldier course
        d.pieslice([x0, 16, x1, 36], 180, 360, fill=WHITE, outline=INK)               # the frame
        d.rectangle([x0, 26, x1, 66], fill=WHITE, outline=INK)
        d.line([x0 + 1, 26, x1 - 1, 26], fill=WHITE)
        d.pieslice([x0 + 2, 18, x1 - 2, 34], 180, 360, fill=SKY)                      # the glass
        d.rectangle([x0 + 2, 26, x1 - 2, 64], fill=SKY)
        for y in range(27, 64):
            d.line([x0 + 2, y, x1 - 2, y], fill=mix(SKY, GLASS, (y - 27) / 37))
        d.line([x0 + 10, 18, x0 + 10, 64], fill=WHITE)                               # the glazing bars
        for y in (30, 42, 54):
            d.line([x0 + 2, y, x1 - 2, y], fill=WHITE)
        d.line([x0 + 4, 44, x0 + 8, 34], fill=GLASS_HI)                              # a glint
        d.line([x0 + 13, 62, x0 + 17, 52], fill=GLASS_HI)
        box(d, x0 - 3, 66, x1 + 3, 70, (188, 199, 204))                              # the sill
        d.line([x0 - 2, 67, x1 + 2, 67], fill=WHITE)
    return im


def _cask_end(d, cx, cy, r, chalk=None):
    """A cask seen end on: the head's boards inside the chime, a hoop round it, the bung."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=OAK_DK, outline=INK)
    d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], outline=HOOP)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=OAK, outline=OAK_DK)
    for y in range(cy - r + 6, cy + r - 4, 4):                      # the head's boards
        half = int(((r - 4) ** 2 - (y - cy) ** 2) ** 0.5)
        d.line([cx - half, y, cx + half, y], fill=OAK_DK)
    d.arc([cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4], 190, 280, fill=OAK_HI)
    d.arc([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], 200, 260, fill=HOOP_HI)
    d.rectangle([cx - 1, cy + 3, cx, cy + 4], fill=TIMBER_DK)       # the bung
    if chalk:                                                       # what is chalked on it
        for x, y, w in chalk:
            d.line([cx + x, cy + y, cx + x + w, cy + y], fill=CREAM)


def wall_casks():
    """Casks racked three high on timber rails, end on, a chalk mark on each."""
    W = 4 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    d.rectangle([0, 10, W - 1, 87], fill=mix(BRICK_DK, BLACK, 0.55))    # the rack stands in the wall's shade
    marks = ([(-5, -3, 4), (1, -3, 3)], [(-4, -2, 7)], [(-5, -3, 2), (-1, -3, 5)], [(-3, -2, 5)], None)
    for row in range(3):
        cy = 23 + row * 25
        for col in range(5):
            _cask_end(d, 14 + col * 25, cy, 11, marks[(row * 2 + col) % 5])
        bar(d, -1, cy + 11, W, cy + 14, TIMBER, TIMBER_HI, TIMBER_DK)       # the rail they lie on
        for col in range(6):                                                # the chocks
            x = 1 + col * 25
            d.polygon([(x - 2, cy + 11), (x + 2, cy + 11), (x, cy + 7)], fill=TIMBER_HI, outline=INK)
    for x in (0, W - 4):                                            # the rack's uprights
        post(d, x, 9, x + 3, 87, TIMBER, TIMBER_HI, TIMBER_DK)
    return im


def wall_shelf():
    """Behind the counter: the sign, and three oak shelves of bottles, the
    old ones in the middle under a lamp of their own."""
    W = 5 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    rnd = random.Random(217)
    box(d, 3, 10, W - 4, 87, OAK_DK)                                # the cabinet
    box(d, 40, 12, 119, 25, BLACK)                                  # the sign, as over the door outside
    d.rectangle([41, 13, 118, 24], outline=BRASS_DK)
    text(d, 56, 15, 'WHISKY', latin(8), BRASS_HI)
    for x in (10, 22, 130, 142):                                    # glasses hung by their feet either side of it
        d.line([x, 13, x + 6, 13], fill=STEEL_HI)
        d.line([x + 3, 14, x + 3, 17], fill=STEEL_HI)
        d.polygon([(x, 18), (x + 6, 18), (x + 5, 23), (x + 1, 23)], outline=STEEL_HI)
    for shelf in (46, 66, 86):
        d.rectangle([5, shelf - 18, W - 6, shelf - 1], fill=mix(OAK_DK, BLACK, 0.45))
        if shelf == 46:                                             # lit from above
            for x in range(8, W - 8):
                d.line([x, shelf - 18, x, shelf - 16], fill=mix(OAK_DK, GLOW, 0.35))
        x = 8
        while x + 4 < W - 7:
            col = rnd.choice((WHISKY, WHISKY, WHISKY_DK, (236, 190, 90), (150, 86, 50), (200, 128, 60)))
            if not any(up - 5 < x < up + 4 for up in (53, 104)):    # none behind an upright
                bottle(d, x, shelf - 1, rnd.choice((13, 14, 15, 16)), col)
            x += rnd.choice((6, 7, 7, 8, 12))
        d.line([4, shelf, W - 5, shelf], fill=OAK_HI)
        d.line([4, shelf + 1, W - 5, shelf + 1], fill=OAK)
    for x in (3, 53, 104, W - 6):                                   # its uprights
        post(d, x, 27, x + 2, 87, OAK, OAK_HI, OAK_DK, outline=False)
    d.rectangle([3, 10, W - 4, 87], outline=INK)
    return im


# ---- the still ------------------------------------------------------------------------------

def still():
    """The one copper pot still, 3x4: the pot on a brick hearth, the swan neck
    with the rope Nikka ties round it, the lyne arm falling to the condenser.
    Its two lower rows are solid; the neck and the arm are walked behind."""
    W, H = 3 * C, 4 * C
    im, d = new(W, H)
    shadow(d, 2, 112, 93, 127, 80)
    # the condenser: a tall copper drum on the right, the arm runs into its head
    box(d, 74, 44, 91, 120, COPPER)
    d.rectangle([75, 45, 78, 119], fill=COPPER_HI)
    d.line([76, 47, 76, 117], fill=COPPER_SHINE)
    d.rectangle([86, 45, 90, 119], fill=COPPER_DK)
    for y in (52, 76, 100, 116):                                    # its bands, riveted
        d.line([75, y, 90, y], fill=COPPER_DK)
        for x in range(77, 90, 4):
            d.point((x, y + 1), fill=COPPER_SHINE)
    d.ellipse([74, 40, 91, 48], fill=COPPER_HI, outline=INK)
    d.rectangle([79, 121, 86, 124], fill=BRASS, outline=INK)        # the spirit runs off here
    d.rectangle([81, 125, 84, 126], fill=WHISKY)
    # the hearth: brick, an iron fire door with the fire behind it
    _bricks(d, 4, 104, 68, 123)
    d.rectangle([4, 104, 68, 123], outline=INK)
    d.line([5, 105, 67, 105], fill=BRICK_HI)
    box(d, 28, 109, 44, 123, BLACK)
    d.pieslice([28, 104, 44, 114], 180, 360, fill=BLACK, outline=INK)
    d.rectangle([31, 113, 41, 120], fill=(236, 120, 50))
    d.rectangle([33, 115, 39, 120], fill=GLOW)
    for x in (32, 35, 38, 41):
        d.line([x, 112, x, 121], fill=BLACK)
    # the pot: an onion of copper
    d.ellipse([2, 56, 70, 110], fill=COPPER, outline=INK)
    d.chord([3, 57, 69, 109], 20, 150, fill=COPPER_DK)
    d.chord([8, 58, 64, 104], 30, 150, fill=COPPER)
    d.arc([6, 60, 66, 106], 185, 265, fill=COPPER_HI, width=3)
    d.arc([9, 63, 40, 96], 190, 250, fill=COPPER_SHINE, width=2)
    d.arc([3, 57, 69, 109], 0, 360, fill=INK)
    for y, half in ((74, 31), (92, 31)):                            # the seams where its plates meet
        d.arc([36 - half, y - 8, 36 + half, y + 8], 10, 170, fill=COPPER_DK)
    for x in range(10, 64, 6):
        d.point((x, 82 + abs(x - 36) // 9 * -1), fill=COPPER_SHINE)
    d.ellipse([28, 74, 44, 90], fill=BRASS, outline=INK)            # the man door
    d.ellipse([31, 77, 41, 87], fill=GLASS, outline=BRASS_DK)
    d.line([33, 82, 36, 79], fill=GLASS_HI)
    for x, y in ((29, 82), (43, 82), (36, 75), (36, 89)):
        d.point((x, y), fill=BRASS_HI)
    # the neck: it narrows as it climbs, then turns over
    d.polygon([(26, 60), (46, 60), (41, 20), (31, 20)], fill=COPPER, outline=INK)
    d.polygon([(28, 59), (31, 59), (33, 21), (32, 21)], fill=COPPER_HI)
    d.polygon([(42, 59), (45, 59), (40, 21), (39, 21)], fill=COPPER_DK)
    d.line([30, 58, 33, 22], fill=COPPER_SHINE)
    d.rectangle([24, 58, 48, 62], fill=COPPER_DK, outline=INK)      # the collar where it meets the pot
    d.line([25, 59, 47, 59], fill=COPPER_HI)
    d.pieslice([30, 8, 50, 30], 180, 360, fill=COPPER, outline=INK)     # the swan's head
    d.arc([32, 10, 46, 26], 190, 260, fill=COPPER_SHINE)
    d.polygon([(40, 9), (78, 36), (78, 44), (40, 19)], fill=COPPER, outline=INK)   # the lyne arm, falling to the condenser
    d.line([42, 11, 77, 37], fill=COPPER_HI)
    d.line([42, 18, 77, 42], fill=COPPER_DK)
    d.rectangle([76, 35, 82, 45], fill=COPPER_DK, outline=INK)      # its flange
    d.line([77, 36, 77, 44], fill=COPPER_HI)
    # the rope round the neck, its paper streamers: every Nikka still wears one
    d.line([29, 40, 43, 40], fill=CREAM, width=3)
    d.line([29, 42, 43, 42], fill=CREAM_SH)
    for x in range(30, 43, 3):
        d.point((x, 40), fill=CREAM_SH)
    for x in (31, 36, 41):
        d.polygon([(x - 1, 43), (x + 1, 43), (x + 2, 46), (x, 46), (x + 1, 49), (x - 1, 49), (x - 2, 46), (x, 46)], fill=WHITE)
        d.line([x - 1, 43, x - 2, 46], fill=CREAM_SH)
    d.line([28, 39, 44, 39], fill=INK)
    d.line([28, 43, 30, 43], fill=INK)
    d.line([42, 43, 44, 43], fill=INK)
    # a gauge on the pot's shoulder, a brass plate on the hearth
    d.line([58, 66, 62, 58], fill=BRASS_DK)
    d.ellipse([59, 52, 67, 60], fill=WHITE, outline=INK)
    d.line([63, 56, 65, 54], fill=(200, 58, 48))
    d.rectangle([8, 110, 22, 117], fill=BRASS, outline=INK)
    d.line([10, 112, 20, 112], fill=BRASS_DK)
    d.line([10, 115, 17, 115], fill=BRASS_DK)
    return im


# ---- the counter and what stands on the floor ---------------------------------------------------

def dram(d, x, y):
    """A tasting glass, 5x7, a finger of whisky in it."""
    d.line([x + 1, y, x + 3, y], fill=GLASS_HI)
    d.rectangle([x, y + 1, x + 4, y + 4], fill=GLASS_HI, outline=STEEL_DK)
    d.rectangle([x + 1, y + 3, x + 3, y + 4], fill=WHISKY)
    d.point((x + 2, y + 5), fill=STEEL_DK)
    d.line([x + 1, y + 6, x + 3, y + 6], fill=STEEL_DK)


def counter():
    """The tasting counter, 5x2, flush to the east wall: the staff's aisle
    behind it, the oak top turning back to the wall at its west end, three
    flights of drams poured on it, the bottles they came from, water."""
    W = 5 * C
    im, d = new(W, 2 * C)
    d.rectangle([0, 0, W - 1, 23], fill=(64, 60, 70))               # the aisle: duckboards
    for x in range(24, W, 6):
        d.line([x, 1, x, 22], fill=(84, 78, 84))
    box(d, 96, 2, 150, 13, STEEL)                                   # the sink, glasses draining by it
    d.rectangle([99, 4, 122, 11], fill=STEEL_DK)
    d.line([110, 2, 110, 6], fill=STEEL_HI)
    for x in range(127, 148, 6):
        d.ellipse([x, 5, x + 4, 9], fill=GLASS_HI, outline=STEEL)
    d.rectangle([0, 19, W - 1, 37], fill=OAK)                       # the top
    d.rectangle([0, 0, 21, 37], fill=OAK)                           # ...and its return to the wall
    d.line([22, 20, W - 1, 20], fill=OAK_HI)
    d.line([20, 1, 20, 20], fill=OAK_HI)
    for x in range(8, W - 20, 31):                                  # the grain
        d.line([x, 26, x + 14, 26], fill=OAK_HI)
        d.line([x + 9, 31, x + 19, 31], fill=OAK_DK)
    d.line([22, 19, W - 1, 19], fill=INK)
    d.line([21, 0, 21, 19], fill=INK)
    d.line([2, 8, 19, 8], fill=OAK_DK)                              # the flap in it
    d.line([2, 9, 19, 9], fill=OAK_HI)
    d.rectangle([0, 38, W - 1, 40], fill=OAK_DK)                    # the lip
    d.line([0, 37, W - 1, 37], fill=INK)
    d.rectangle([0, 41, W - 1, 60], fill=TIMBER)                    # the front: cask staves, hooped
    for x in range(0, W, 8):
        d.line([x, 42, x, 59], fill=TIMBER_DK)
        d.line([x + 1, 42, x + 1, 59], fill=TIMBER_HI)
    for y in (45, 55):
        d.rectangle([0, y, W - 1, y + 1], fill=HOOP)
        d.line([0, y, W - 1, y], fill=HOOP_HI)
    d.rectangle([0, 60, W - 1, 62], fill=TIMBER_DK)
    d.line([0, 63, W - 1, 63], fill=INK)
    d.line([0, 41, W - 1, 41], fill=INK)
    d.line([0, 0, 0, 63], fill=INK)
    for n, x in enumerate((30, 76, 122)):                           # three flights: a board, three drams, a card
        box(d, x, 27, x + 24, 34, TIMBER)
        d.line([x + 1, 28, x + 23, 28], fill=TIMBER_HI)
        for k in range(3):
            dram(d, x + 2 + k * 8, 22)
        d.rectangle([x + 27, 26, x + 33, 33], fill=CREAM, outline=CREAM_SH)
        d.line([x + 29, 28, x + 31, 28], fill=TIMBER)
        d.line([x + 29, 30, x + 31, 30], fill=CREAM_SH)
    for x, col in ((64, WHISKY), (69, WHISKY_DK), (112, (236, 190, 90))):     # the bottles they came from
        bottle(d, x, 27, 15, col)
    box(d, 146, 14, 153, 28, GLASS_HI)                              # a jug of water
    d.rectangle([147, 19, 152, 27], fill=GLASS)
    d.line([154, 17, 156, 19], fill=INK)
    d.line([156, 19, 154, 24], fill=INK)
    d.line([148, 16, 148, 26], fill=WHITE)
    d.rectangle([6, 23, 16, 34], fill=BLACK, outline=INK)           # the till: a tablet on a stand
    d.rectangle([7, 24, 15, 31], fill=(120, 200, 150))
    d.line([9, 27, 13, 27], fill=BLACK)
    return im


def stool():
    """An oak stool, a round seat on three legs."""
    im, d = new(C, C)
    shadow(d, 7, 23, 24, 30, 70)
    for x in (10, 20):
        d.line([x, 13, x - (1 if x == 10 else -1), 27], fill=OAK_DK, width=2)
    d.line([15, 13, 15, 26], fill=OAK_DK, width=2)
    d.line([9, 21, 22, 21], fill=TIMBER)
    d.ellipse([7, 4, 24, 14], fill=OAK, outline=INK)
    d.arc([9, 5, 22, 12], 180, 300, fill=OAK_HI)
    d.arc([8, 6, 23, 13], 20, 140, fill=OAK_DK)
    d.ellipse([12, 7, 19, 11], outline=OAK_DK)
    return im


def cask():
    """A cask stood on end: its head, the staves bellying under it, four hoops."""
    im, d = new(C, C)
    shadow(d, 2, 22, 29, 31, 80)
    d.rounded_rectangle([4, 8, 27, 28], radius=4, fill=OAK, outline=INK)    # the staves
    d.rectangle([3, 13, 28, 23], fill=OAK, outline=None)
    d.line([3, 13, 3, 23], fill=INK)
    d.line([28, 13, 28, 23], fill=INK)
    for x in range(7, 27, 4):
        d.line([x, 10, x, 27], fill=OAK_DK)
    d.line([5, 11, 5, 26], fill=OAK_HI)
    d.rectangle([24, 10, 27, 26], fill=OAK_DK)
    d.line([27, 10, 27, 26], fill=INK)
    d.line([28, 13, 28, 23], fill=INK)
    for y in (11, 15, 21, 25):                                      # the hoops
        x0, x1 = (4, 27) if y in (11, 25) else (3, 28)
        d.line([x0, y, x1, y], fill=HOOP)
        d.line([x0 + 1, y, x0 + 5, y], fill=HOOP_HI)
    d.ellipse([4, 2, 27, 12], fill=OAK_HI, outline=INK)             # the head
    d.ellipse([6, 3, 25, 11], fill=OAK, outline=OAK_DK)
    for y in (5, 7, 9):
        d.line([8 if y != 7 else 6, y, 23 if y != 7 else 25, y], fill=OAK_DK)
    d.line([10, 6, 13, 6], fill=CREAM)                              # chalk: not before...
    d.line([15, 6, 20, 6], fill=CREAM)
    d.line([12, 8, 18, 8], fill=CREAM)
    d.rectangle([15, 17, 16, 18], fill=TIMBER_DK)                   # the bung
    return im


def lamp_hang():
    """A copper lamp on a black flex, hung from the beams, over your head."""
    im, d = new(C, 2 * C)
    d.line([15, 0, 15, 31], fill=BLACK)
    d.line([16, 0, 16, 31], fill=TIMBER_DK)
    d.rectangle([13, 30, 18, 34], fill=BRASS, outline=INK)
    d.pieslice([4, 33, 27, 59], 180, 360, fill=COPPER, outline=INK)     # the shade: a copper dome
    d.arc([6, 35, 25, 57], 190, 250, fill=COPPER_SHINE)
    d.arc([6, 35, 25, 57], 250, 290, fill=COPPER_HI)
    d.arc([5, 34, 26, 58], 300, 355, fill=COPPER_DK)
    d.rectangle([4, 46, 27, 47], fill=COPPER_DK, outline=INK)
    d.ellipse([10, 46, 21, 52], fill=GLOW_HI, outline=GLOW)         # the light under it
    return im


def sprites():
    p = 'distillery-in-'
    return {
        p + 'floor-a': flags(0), p + 'floor-b': flags(11),
        p + 'side-w': wall_side(KILN, 'w'), p + 'side-e': wall_side(KILN, 'e'),
        p + 'wall-front': wall_front(KILN),
        p + 'threshold-w': threshold(KILN, 'w'), p + 'threshold-e': threshold(KILN, 'e'),
        p + 'doorlight': doorlight,
        p + 'wall-brick': wall_brick, p + 'wall-window': wall_window,
        p + 'wall-casks': wall_casks, p + 'wall-shelf': wall_shelf,
        p + 'still': still, p + 'counter': counter,
        p + 'stool': stool, p + 'cask': cask,
        p + 'lamp-hang': lamp_hang,
    }


# As the pub's: the hanging lamps are lifted in front of whatever taller thing
# stands behind them; the light through the door lies on the floor.
DEPTH_BIAS = {'distillery-in-lamp-hang': 10, 'distillery-in-doorlight': -40}


if __name__ == '__main__':
    register(sprites(), DEPTH_BIAS, sys.argv)
