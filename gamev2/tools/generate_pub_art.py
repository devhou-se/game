#!/usr/bin/env python3
"""generate_pub_art.py — everything inside the pub in Sendai (issue #217), and
the frame the two other interiors of that issue are built in.

In the manner of tools/generate_palace_art.py: shaded pixel art with a 1px ink
outline, drawn at half size (32px a cell) and pixel-doubled, in the house look
(issue #334): every colour is one the GuttyKreum sheets use, the outline is the
pack's navy, and nothing is lit (a lamp is the pack's dim gold, c6a663). Nothing is random
between runs (every scatter is seeded) and the only text (the score on the
television) is set in the game's own font, so a re-run is byte-identical on
the same machine.

The room is a British pub as Japan builds them: mahogany, dark green paper,
brass and red leather. All sprites are `pub-in-<piece>`:
  floor-a / floor-b       dark boards
  side-w / side-e         the side walls seen along their length
  wall-front              the front wall's head from inside
  threshold-w / -e        the doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-panel, wall-print  1x3 bays of the back wall: paper over a wainscot; a framed print
  wall-backbar            7x3 the back bar: dark glass, two shelves of bottles, optics
  wall-tv                 4x3 the big screen: the baseball (bump it)
  wall-darts              2x3 the dartboard in its cabinet, chalk scores (bump it)
  bar                     7x2 the bar: the staff's aisle behind, the counter with three
                          sets of taps and the till in front (bump it: the shop list)
  stool                   a bar stool
  table                   2x1 a table with two pints on it;  chair-w / chair-e: its chairs
  booth                   2x3 a high-backed bench either side of a table
  chalkboard              1x2 the specials, on an easel (bump it)
  lamp-hang               1x2 a green glass lamp hung from the ceiling (Tops)
                          (the lamps, the back bar and the screen glow at night: src/utils/Glows.js)

The frame (wall_side, wall_front, threshold, doorlight), the drawing helpers,
the colours and register() are imported by tools/generate_distillery_art.py,
generate_mall_art.py, generate_tower_deck_art.py, generate_wheel_art.py and
generate_flinders_art.py: rerun them after changing a value here. Nothing is
drawn or written on import.

Run from gamev2/:  python3 tools/generate_pub_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import random
import sys

from PIL import Image, ImageDraw, ImageFont

C = 32      # canvas px per cell (doubled on save)


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; pub.test.js holds the pub to it).

INK = rgb('172459')                      # the pack's navy: every outline
VOID = rgb('080d16')
SHADE = rgb('2a3151')                    # what a thing throws on the floor, with alpha
WHITE, CREAM, CREAM_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('d7b6ab')
DAY = (WHITE, rgb('ffe2e0'), CREAM)      # daylight at a door, palest first
GLOW, GLOW_HI = rgb('c6a663'), rgb('f3d890')                          # a lamp: the pack's dim gold, its core
WOOD, WOOD_HI, WOOD_DK = rgb('71412a'), rgb('85553e'), rgb('4d3326')  # mahogany
TOP, TOP_HI, TOP_DK = rgb('85553e'), rgb('b07c63'), rgb('68422d')     # a polished counter top
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = rgb('4d3326'), rgb('5a3827'), rgb('68422d'), rgb('2a2636')
GREEN, GREEN_HI, GREEN_DK = rgb('395050'), rgb('4a6262'), rgb('2e4040')   # the wallpaper
GREEN_GLINT = rgb('6c8e7f')
BRASS, BRASS_HI, BRASS_DK = rgb('c6a663'), rgb('f3d890'), rgb('a7843b')
LEATHER, LEATHER_HI, LEATHER_DK = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
STEEL, STEEL_HI, STEEL_DK = rgb('a4b0b5'), rgb('d1e2eb'), rgb('656e92')
MIRROR, MIRROR_HI = rgb('2c2d51'), rgb('4b6396')    # the back bar's glass: dark, a slanted glare
BEER, BEER_DK, FOAM = rgb('c6a663'), rgb('a7843b'), rgb('fafcfd')
SLATE, SLATE_HI = rgb('2e4040'), rgb('4a6262')
BLACK, BLACK_HI = rgb('1b1e2a'), rgb('47485d')
GRASS, GRASS_HI, DIRT, DIRT_DK = rgb('678e57'), rgb('83af6f'), rgb('b07c63'), rgb('86624f')
RED, LEAF, BLUE, BLUE_DK, ORANGE, PINK = rgb('d16b56'), rgb('508582'), rgb('4b6396'), rgb('314b8e'), rgb('ce6a42'), rgb('bb6479')
MAT, MAT_HI, ICE, SKY, SKIN = rgb('2a2636'), rgb('47485d'), rgb('d1e2eb'), rgb('bbe9ff'), rgb('f6a583')
# a bottle: its glass, the light down its side, its label
BOTTLES = [(LEAF, rgb('93c297'), CREAM), (GLOW, GLOW_HI, WHITE), (rgb('904a37'), RED, CREAM), (BLUE, rgb('588cc6'), CREAM),
           (CREAM, WHITE, CREAM_SH), (rgb('7f513b'), rgb('aa775f'), CREAM), (PINK, rgb('d78bc1'), CREAM)]

_FONTS = {}


def latin(size=8):
    """The game's own display face: the only lettering any of this art carries."""
    if size not in _FONTS:
        _FONTS[size] = ImageFont.truetype('fonts/PressStart2P-Regular.ttf', size)
    return _FONTS[size]


def new(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'        # no anti-aliasing: pixel fonts stay pixels
    return im, d


def box(d, x0, y0, x1, y1, fill, outline=INK):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)


def text(d, x, y, s, f, fill):
    """Text with its top-left ink pixel at (x, y), whatever the font's bearings."""
    l, t, _, _ = d.textbbox((0, 0), s, font=f)
    d.text((x - l, y - t), s, font=f, fill=fill)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bar(d, x0, y0, x1, y1, base, hi, dk, outline=True):
    """A horizontal timber: lit along the top, shaded along the bottom."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0, y0 + (1 if outline else 0), x1, y0 + (1 if outline else 0)], fill=hi)
    d.line([x0, y1 - (1 if outline else 0), x1, y1 - (1 if outline else 0)], fill=dk)
    if outline:
        d.rectangle([x0, y0, x1, y1], outline=INK)


def post(d, x0, y0, x1, y1, base, hi, dk, outline=True):
    """An upright timber: lit down its left side, shaded down its right."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.line([x0 + (1 if outline else 0), y0, x0 + (1 if outline else 0), y1], fill=hi)
    d.line([x1 - (1 if outline else 0), y0, x1 - (1 if outline else 0), y1], fill=dk)
    if outline:
        d.rectangle([x0, y0, x1, y1], outline=INK)


def shadow(d, x0, y0, x1, y1, a=90):
    d.ellipse([x0, y0, x1, y1], fill=SHADE + (a,))


def pint(d, x, y):
    """A pint of beer, 6x9, its top-left at (x, y)."""
    d.rectangle([x, y, x + 5, y + 8], fill=BEER, outline=INK)
    d.rectangle([x + 1, y + 1, x + 4, y + 2], fill=FOAM)
    d.line([x + 1, y + 3, x + 1, y + 7], fill=GLOW_HI)
    d.line([x + 4, y + 4, x + 4, y + 7], fill=BEER_DK)


def bottle(d, x, foot, h, col, hi=None, label=None):
    """A bottle 4px wide standing on `foot`, `h` tall, neck and all."""
    hi, label = hi or mix(col, WHITE, 0.45), label or mix(col, CREAM, 0.7)
    d.rectangle([x, foot - h + 5, x + 3, foot], fill=col)
    d.rectangle([x + 1, foot - h + 1, x + 2, foot - h + 4], fill=col)
    d.point((x + 1, foot - h), fill=CREAM)
    d.point((x + 2, foot - h), fill=CREAM)
    d.line([x, foot - h + 6, x, foot - 1], fill=hi)
    d.rectangle([x + 1, foot - 5, x + 3, foot - 3], fill=label)     # the label


# ---- the frame: shared by the three interiors of issue #217 ---------------------------
#
# Each takes a palette: {'head', 'head_hi', 'head_dk'} the timber (or stone) of the
# wall's head, {'face', 'face_hi', 'face_dk'} the wall's face, 'trim' a line of
# colour along it, {'post', 'post_hi', 'post_dk'} the door posts, 'sill' the step.

PUB = {'head': WOOD, 'head_hi': WOOD_HI, 'head_dk': WOOD_DK, 'face': GREEN, 'face_hi': GREEN_HI, 'face_dk': GREEN_DK,
       'trim': BRASS, 'post': WOOD, 'post_hi': WOOD_HI, 'post_dk': WOOD_DK, 'sill': CREAM_SH}


def wall_side(pal, side):
    """A side wall seen along its length from above: the wall's dark head, then
    a sliver of its face."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        d.rectangle([12, 0, 21, 31], fill=pal['head'])              # the head
        d.line([13, 0, 13, 31], fill=pal['head_hi'])
        d.line([21, 0, 21, 31], fill=pal['head_dk'])
        d.rectangle([22, 0, 29, 31], fill=pal['face'])              # the face, foreshortened
        d.line([22, 0, 22, 31], fill=INK)
        d.line([24, 0, 24, 31], fill=pal['face_hi'])
        d.line([27, 0, 27, 31], fill=pal['face_dk'])
        d.rectangle([30, 0, 31, 31], fill=pal['head_dk'])           # the skirting
        d.line([30, 0, 30, 31], fill=INK)
        d.rectangle([22, 15, 31, 17], fill=pal['head_dk'])          # a joint along it
        d.line([22, 15, 31, 15], fill=pal['trim'])
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def wall_front(pal):
    """The front wall from inside: all you see is its head; below it is dark."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        bar(d, -1, 0, 32, 9, pal['head'], pal['head_hi'], pal['head_dk'])
        d.rectangle([0, 10, 31, 16], fill=pal['head_dk'])
        d.line([0, 16, 31, 16], fill=INK)
        d.line([0, 5, 31, 5], fill=pal['trim'])
        return im
    return draw


def threshold(pal, side):
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=DAY[0])                    # the day outside, in flat steps
        d.rectangle([0, 0, 31, 3], fill=DAY[2])
        d.rectangle([0, 4, 31, 9], fill=DAY[1])
        d.line([0, 10, 31, 10], fill=pal['sill'])                   # the step
        d.line([0, 22, 31, 22], fill=pal['sill'])
        x0 = 0 if side == 'w' else 26                               # the door post
        post(d, x0, -1, x0 + 5, 32, pal['post'], pal['post_hi'], pal['post_dk'])
        d.rectangle([x0, 0, x0 + 5, 6], fill=pal['head_dk'])
        d.line([x0, 7, x0 + 5, 7], fill=pal['trim'])
        d.line([x0, 0, x0, 31], fill=INK)
        d.line([x0 + 5, 0, x0 + 5, 31], fill=INK)
        return im
    return draw


def doorlight():
    """Daylight falling in through a door: 2x3, on the floor, strongest at the sill."""
    im, d = new(2 * C, 3 * C)
    for y0, y1, inset, a in ((28, 47, 9, 28), (48, 67, 6, 56), (68, 83, 3, 84), (84, 95, 0, 112)):
        d.rectangle([inset, y0, 63 - inset, y1], fill=CREAM + (a,))
    return im


def register(sprites, bias=None, argv=()):
    """Draw `sprites` ({name: function -> image at 32px a cell}), save each
    pixel-doubled as assets/sprites/<name>_0_0.png and register it in
    config.json (spriteMetadata, tileNames; `bias`: {name: depthBias}).
    `--preview out.png` in argv also writes a contact sheet."""
    built = {}
    for name, fn in sprites.items():
        im = fn()
        built[name] = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if name in (bias or {}):
            cfg['spriteMetadata'][key]['depthBias'] = bias[name]
        cfg.setdefault('tileNames', {})[key] = name
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in argv:
        out = argv[argv.index('--preview') + 1]
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


# ---- the pub: floor ---------------------------------------------------------------------

def boards(shift):
    """Dark boards running east-west, four a cell."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=BOARD)
        for i in range(4):
            a = i * 8
            joint = (shift + (10 if i % 2 == 0 else 26) + i * 3) % 32
            streak = (joint + 9 + i * 5) % 32
            if i % 2:
                d.rectangle([0, a, 31, a + 7], fill=BOARD_ALT)
            d.line([0, a, 31, a], fill=BOARD_DK)
            d.line([joint, a + 1, joint, a + 7], fill=BOARD_DK)
            for k in range(6):
                d.point(((streak + k) % 32, a + 3), fill=BOARD_HI)
            d.point(((streak + 13) % 32, a + 5), fill=BOARD_HI)
        return im
    return draw


# ---- the pub: the back wall --------------------------------------------------------------

def _wall(d, w):
    """Every back-wall piece: the cornice, dark green paper with a small figure,
    a dado rail, a mahogany wainscot and the skirting."""
    d.rectangle([0, 0, w - 1, 95], fill=GREEN)
    for y in range(12, 58, 8):                                  # the paper's figure
        for x in range(4 if (y // 8) % 2 else 0, w, 8):
            d.point((x, y), fill=GREEN_HI)
            d.point((x, y + 1), fill=GREEN_DK)
    bar(d, -1, 0, w, 7, WOOD_DK, WOOD, BLACK)                   # the cornice
    d.line([0, 8, w - 1, 8], fill=GREEN_DK)
    bar(d, -1, 59, w, 63, WOOD, WOOD_HI, WOOD_DK)               # the dado rail
    d.rectangle([0, 64, w - 1, 87], fill=WOOD)                  # the wainscot, a panel every half cell
    for x in range(0, w, 16):
        d.rectangle([x + 2, 67, x + 13, 84], outline=WOOD_DK)
        d.line([x + 3, 68, x + 12, 68], fill=WOOD_HI)
        d.line([x + 3, 68, x + 3, 83], fill=WOOD_HI)
    d.rectangle([0, 88, w - 1, 95], fill=WOOD_DK)               # the skirting
    d.line([0, 88, w - 1, 88], fill=INK)
    d.line([0, 89, w - 1, 89], fill=WOOD)
    d.line([0, 95, w - 1, 95], fill=INK)


def wall_panel():
    im, d = new(C, 3 * C)
    _wall(d, C)
    return im


def wall_print():
    """A bay with a framed print: a hill, a tree, a pale sky."""
    im, d = new(C, 3 * C)
    _wall(d, C)
    d.line([15, 9, 15, 20], fill=BRASS_DK)                      # its wire
    box(d, 5, 20, 26, 46, WOOD_DK)
    d.rectangle([6, 21, 25, 45], outline=BRASS)
    d.rectangle([8, 23, 23, 43], fill=CREAM)
    d.rectangle([9, 24, 22, 34], fill=SKY)
    d.rectangle([9, 35, 22, 42], fill=GRASS_HI)
    d.polygon([(9, 35), (14, 30), (19, 33), (22, 31), (22, 35)], fill=GREEN_GLINT)
    d.line([18, 28, 18, 35], fill=WOOD_DK)
    d.rectangle([16, 26, 20, 30], fill=LEAF)
    return im


def wall_backbar():
    """The back bar: a mahogany cabinet of three glass-backed bays, two shelves of
    bottles in each, a row of optics across the middle one, cupboards below."""
    W = 7 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    rnd = random.Random(2170)
    box(d, 3, 9, W - 4, 87, WOOD_DK)
    bar(d, 3, 9, W - 4, 15, WOOD, WOOD_HI, WOOD_DK)             # its head
    d.line([5, 12, W - 6, 12], fill=BRASS)
    bays = [(6, 74), (77, 146), (149, 217)]
    for n, (x0, x1) in enumerate(bays):
        d.rectangle([x0, 17, x1, 61], fill=MIRROR)              # the mirror, glints across it
        for k in range(3):
            gx = x0 + 8 + k * 22
            d.line([gx, 60, gx + 14, 18], fill=MIRROR_HI)
            d.line([gx + 3, 60, gx + 17, 18], fill=MIRROR_HI)
        d.rectangle([x0, 17, x1, 61], outline=INK)
        for shelf in (38, 60):                                  # two shelves of bottles
            d.line([x0 + 1, shelf, x1 - 1, shelf], fill=WOOD_HI)
            d.line([x0 + 1, shelf + 1, x1 - 1, shelf + 1], fill=WOOD_DK)
            if n == 1 and shelf == 38:
                continue                                        # the optics hang there instead
            x = x0 + 3
            while x + 4 < x1 - 1:
                bottle(d, x, shelf - 1, rnd.choice((13, 15, 16, 17)), *rnd.choice(BOTTLES))
                x += rnd.choice((5, 6, 6, 7))
    x0, x1 = bays[1]
    d.line([x0 + 3, 20, x1 - 3, 20], fill=BRASS)                # the optics: bottles hung upside down
    d.line([x0 + 3, 21, x1 - 3, 21], fill=BRASS_DK)
    for i in range(6):
        x = x0 + 7 + i * 10
        col, hi, label = BOTTLES[(i * 3 + 1) % len(BOTTLES)]
        d.rectangle([x, 22, x + 4, 32], fill=col)
        d.line([x, 22, x, 32], fill=hi)
        d.rectangle([x + 1, 26, x + 4, 29], fill=label)
        d.rectangle([x + 1, 33, x + 3, 35], fill=STEEL)
        d.point((x + 2, 36), fill=STEEL_DK)
    for x0, x1 in bays:                                         # cupboards under the shelves
        box(d, x0, 63, x1, 85, WOOD)
        mid = (x0 + x1) // 2
        for a, b in ((x0 + 2, mid - 1), (mid + 1, x1 - 2)):
            d.rectangle([a, 65, b, 83], outline=WOOD_DK)
            d.line([a + 1, 66, b - 1, 66], fill=WOOD_HI)
        d.point((mid - 3, 74), fill=BRASS_HI)
        d.point((mid + 3, 74), fill=BRASS_HI)
    for x in (3, 75, 147, W - 6):                               # the posts between the bays
        post(d, x, 15, x + 2, 87, WOOD, WOOD_HI, WOOD_DK, outline=False)
    return im


def wall_tv():
    """The big screen: a ball game from high behind home plate - the diamond,
    the fielders, a runner on first, the score in the corner."""
    W = 4 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    box(d, 6, 11, W - 7, 57, BLACK)                             # the set
    d.line([7, 12, W - 8, 12], fill=BLACK_HI)
    d.rectangle([9, 14, W - 10, 54], fill=GRASS)                # the picture
    for y in range(14, 55, 6):                                  # mown stripes
        d.rectangle([9, y, W - 10, min(y + 2, 54)], fill=GRASS_HI)
    d.rectangle([9, 14, W - 10, 19], fill=BLUE_DK)        # the outfield wall, the crowd over it
    rnd = random.Random(505)
    for x in range(10, W - 10, 2):
        d.point((x, 15 + rnd.randrange(2)), fill=rnd.choice((RED, CREAM, GLOW, rgb('588cc6'))))
    d.line([9, 19, W - 10, 19], fill=GLOW)
    home, first, second, third = (64, 50), (88, 38), (64, 27), (40, 38)
    d.polygon([home, first, second, third], fill=DIRT)          # the infield
    d.polygon([(64, 44), (78, 38), (64, 32), (50, 38)], fill=GRASS_HI)
    d.ellipse([60, 35, 68, 40], fill=DIRT)                      # the mound
    d.ellipse([58, 46, 70, 54], fill=DIRT)                      # round the plate
    d.line([home, (100, 32)], fill=WHITE)                       # the foul lines
    d.line([home, (28, 32)], fill=WHITE)
    for x, y in (first, second, third):
        d.rectangle([x - 1, y - 1, x + 1, y], fill=WHITE)
    d.polygon([(63, 50), (65, 50), (65, 51), (64, 52), (63, 51)], fill=WHITE)

    def man(x, y, shirt, cap):
        d.rectangle([x, y, x + 2, y + 3], fill=shirt)
        d.point((x + 1, y - 1), fill=SKIN)
        d.line([x, y - 2, x + 2, y - 2], fill=cap)
    for x, y in ((62, 33), (84, 33), (70, 26), (54, 27), (42, 33), (30, 23), (63, 21), (96, 23)):
        man(x, y, WHITE, LEATHER_DK)                         # the Eagles in the field
    man(60, 45, BLUE, BLUE_DK)                   # the batter, and his bat
    d.line([63, 43, 66, 41], fill=BRASS_HI)
    man(63, 51, BLACK, BLACK)                                   # the catcher
    man(89, 34, BLUE, BLUE_DK)                   # a runner on first
    box(d, 11, 43, 43, 53, BLACK, outline=BLACK_HI)         # the score
    d.rectangle([13, 45, 15, 51], fill=LEATHER_DK)
    text(d, 18, 45, '3-2', latin(8), WHITE)
    d.rectangle([9, 14, W - 10, 54], outline=INK)
    d.line([10, 15, W - 11, 15], fill=rgb('93c297'))   # the glass
    d.point((W - 12, 56), fill=rgb('93c297'))                  # it is on
    d.rectangle([58, 58, 69, 59], fill=BLACK)                   # its bracket
    return im


def wall_darts():
    """The dartboard in its cabinet, the doors folded back with the chalk
    scores on them - and three darts in the wall under it."""
    W = 2 * C
    im, d = new(W, 3 * C)
    _wall(d, W)
    box(d, 12, 11, 51, 51, WOOD_DK)                             # the cabinet
    d.rectangle([13, 12, 50, 50], outline=WOOD)
    for x0 in (3, 52):                                          # its doors: slates
        box(d, x0, 12, x0 + 8, 50, SLATE)
        d.rectangle([x0, 12, x0 + 8, 50], outline=WOOD_DK)
        for y in range(16, 46, 4):
            d.line([x0 + 2, y, x0 + 2 + (y * 7 + x0) % 5, y], fill=CREAM)
    cx, cy, r = 32, 31, 17
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK, outline=INK)
    for i in range(20):                                         # the wedges
        d.pieslice([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], i * 18 - 9, i * 18 + 9,
                   fill=CREAM if i % 2 else BLACK)
    for rr, wdt in ((14, 1), (8, 1)):                           # the double and the treble
        for i in range(20):
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], i * 18 - 9, i * 18 + 9,
                  fill=RED if i % 2 else GRASS, width=wdt + 1)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=GRASS, outline=INK)
    d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=RED)
    for x, y, col in ((8, 55, RED), (27, 54, BRASS), (47, 56, BLUE)):   # three darts in the paper
        d.line([x, y, x + 5, y - 3], fill=STEEL_HI)
        d.point((x, y), fill=INK)
        d.rectangle([x + 5, y - 5, x + 7, y - 3], fill=col)
    return im


# ---- the pub: the bar and what stands on the floor -------------------------------------------

def the_bar():
    """The bar, 7x2, flush to the west wall: the staff's aisle behind it, the
    counter in front, turning back to the wall at its east end. Three sets of
    taps, the till, glasses, a towel."""
    W = 7 * C
    im, d = new(W, 2 * C)
    d.rectangle([0, 0, W - 1, 23], fill=MAT)           # the aisle: a rubber mat
    for y in range(3, 22, 4):
        for x in range(2 + (y // 4 % 2) * 2, W - 22, 4):
            d.point((x, y), fill=MAT_HI)
    d.rectangle([4, 2, 40, 12], fill=STEEL_DK, outline=INK)     # the glass washer's rack
    for x in range(7, 39, 6):
        d.ellipse([x, 4, x + 4, 8], fill=STEEL_HI, outline=STEEL)
    box(d, 150, 3, 190, 13, STEEL)                              # the ice well
    d.rectangle([152, 5, 188, 11], fill=ICE)
    for x in range(154, 187, 5):
        d.point((x, 7 + x % 3), fill=WHITE)
    d.polygon([(0, 19), (W - 1, 19), (W - 1, 37), (0, 37)], fill=TOP)   # the counter top
    d.rectangle([W - 22, 0, W - 1, 37], fill=TOP)               # ...and its return to the wall
    d.line([0, 20, W - 23, 20], fill=TOP_HI)
    d.line([W - 21, 1, W - 21, 20], fill=TOP_HI)
    for x in range(10, W - 30, 37):                             # the polish
        d.line([x, 27, x + 12, 27], fill=TOP_HI)
        d.line([x + 20, 31, x + 26, 31], fill=TOP_HI)
    d.line([0, 19, W - 23, 19], fill=INK)
    d.line([W - 22, 0, W - 22, 19], fill=INK)
    d.line([W - 20, 8, W - 2, 8], fill=TOP_DK)                  # the flap in it
    d.line([W - 20, 9, W - 2, 9], fill=TOP_HI)
    d.rectangle([0, 38, W - 1, 40], fill=TOP_DK)                # the lip
    d.line([0, 37, W - 1, 37], fill=INK)
    d.rectangle([0, 41, W - 1, 60], fill=WOOD)                  # the front: panels, a brass rail at the foot
    for x in range(2, W - 4, 28):
        d.rectangle([x, 43, x + 24, 53], outline=WOOD_DK)
        d.line([x + 1, 44, x + 23, 44], fill=WOOD_HI)
        d.line([x + 1, 44, x + 1, 52], fill=WOOD_HI)
    d.line([0, 56, W - 1, 56], fill=BRASS)
    d.line([0, 57, W - 1, 57], fill=BRASS_DK)
    for x in range(14, W, 44):
        d.line([x, 54, x, 59], fill=BRASS_DK)
    d.rectangle([0, 60, W - 1, 62], fill=WOOD_DK)
    d.line([0, 63, W - 1, 63], fill=INK)
    d.line([0, 41, W - 1, 41], fill=INK)
    d.line([W - 1, 0, W - 1, 63], fill=INK)
    for n, cx in enumerate((48, 112, 176)):                     # the taps: a brass T, three handles, a drip tray
        box(d, cx - 12, 29, cx + 12, 34, STEEL)
        d.line([cx - 10, 31, cx + 10, 31], fill=STEEL_DK)
        d.line([cx - 10, 32, cx + 10, 32], fill=STEEL_HI)
        post(d, cx - 2, 12, cx + 2, 30, BRASS, BRASS_HI, BRASS_DK)
        bar(d, cx - 11, 12, cx + 11, 16, BRASS, BRASS_HI, BRASS_DK)
        for k, col in enumerate((RED, CREAM, GRASS)):
            hx = cx - 9 + k * 8
            col = (col, ORANGE, BLUE_DK)[(k + n) % 3] if n else col
            d.rectangle([hx, 3, hx + 2, 11], fill=col, outline=INK)
            d.point((hx + 1, 5), fill=WHITE)
            d.line([hx + 1, 17, hx + 1, 20], fill=BRASS_DK)     # the spout
    box(d, 70, 13, 91, 33, BLACK)                               # the till
    d.rectangle([72, 15, 89, 20], fill=rgb('93c297'))
    d.line([74, 17, 80, 17], fill=BLACK)
    for y in (23, 26, 29):
        for x in range(73, 89, 4):
            d.rectangle([x, y, x + 1, y + 1], fill=BRASS)
    d.rectangle([68, 33, 93, 35], fill=WOOD_DK, outline=INK)    # its drawer
    pint(d, 24, 22)
    pint(d, 134, 23)
    pint(d, 143, 25)
    d.ellipse([10, 26, 20, 32], fill=CREAM, outline=INK)        # a bowl of nuts
    d.rectangle([12, 27, 18, 29], fill=DIRT)
    d.rectangle([196, 24, 208, 33], fill=RED, outline=INK)    # a bar towel
    d.line([198, 27, 206, 27], fill=CREAM)
    d.line([198, 30, 206, 30], fill=CREAM)
    for x in (30, 96, 160):                                     # beer mats
        d.rectangle([x + 4, 33, x + 8, 35], fill=CREAM)
    return im


def stool():
    im, d = new(C, C)
    shadow(d, 7, 23, 24, 30)
    for x in (10, 20):                                          # its legs, a ring to rest your feet on
        d.line([x, 13, x - (1 if x == 10 else -1), 27], fill=WOOD_DK, width=2)
    d.line([15, 13, 15, 26], fill=WOOD_DK, width=2)
    d.line([9, 21, 22, 21], fill=BRASS)
    d.ellipse([7, 4, 24, 14], fill=LEATHER, outline=INK)        # the seat
    d.arc([9, 5, 22, 12], 180, 300, fill=LEATHER_HI)
    d.arc([8, 6, 23, 13], 20, 140, fill=LEATHER_DK)
    d.point((15, 9), fill=BRASS_HI)
    return im


def table():
    """A pub table with two pints on it."""
    im, d = new(2 * C, C)
    shadow(d, 5, 22, 58, 31)
    for x in (10, 51):
        d.rectangle([x, 20, x + 2, 28], fill=WOOD_DK)
        d.line([x, 20, x, 28], fill=WOOD)
    d.line([12, 25, 51, 25], fill=WOOD_DK)
    d.rounded_rectangle([3, 6, 60, 19], radius=3, fill=TOP, outline=INK)
    d.line([6, 7, 57, 7], fill=TOP_HI)
    d.line([10, 12, 22, 12], fill=TOP_HI)
    d.line([38, 15, 46, 15], fill=TOP_HI)
    d.rectangle([4, 19, 59, 21], fill=TOP_DK)
    d.line([4, 22, 59, 22], fill=INK)
    pint(d, 16, 3)
    pint(d, 41, 6)
    d.rectangle([27, 12, 31, 15], fill=CREAM, outline=CREAM_SH)     # a beer mat, a packet of crisps
    d.rectangle([33, 8, 38, 13], fill=BLUE, outline=INK)
    d.point((35, 10), fill=BRASS_HI)
    return im


def chair(side):
    """A chair drawn up to a table: `w` stands on its west side, `e` on its east."""
    def draw():
        im, d = new(C, C)
        shadow(d, 8, 23, 27, 30)
        post(d, 9, 3, 12, 27, WOOD, WOOD_HI, WOOD_DK)              # the back
        d.rectangle([9, 3, 12, 5], fill=WOOD_HI)
        d.point((9, 3), fill=INK)
        d.rectangle([22, 17, 24, 28], fill=WOOD_DK, outline=INK)   # the front leg
        d.line([12, 23, 22, 23], fill=WOOD_DK)
        d.rectangle([9, 14, 25, 18], fill=LEATHER, outline=INK)    # the seat
        d.line([11, 15, 23, 15], fill=LEATHER_HI)
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def booth():
    """A booth against the wall, 2x3: a high-backed bench facing you, the
    table, and the back of the bench that faces it."""
    W = 2 * C
    im, d = new(W, 3 * C)
    box(d, 1, 0, W - 2, 22, WOOD)                               # the far bench: its back...
    d.line([2, 1, W - 3, 1], fill=WOOD_HI)
    d.rectangle([4, 4, W - 5, 20], fill=LEATHER, outline=INK)
    d.line([5, 5, W - 6, 5], fill=LEATHER_HI)
    for x in range(10, W - 6, 11):                              # buttoned
        for y in (9, 15):
            d.point((x + (3 if y == 15 else 0), y), fill=LEATHER_DK)
    box(d, 1, 22, W - 2, 31, LEATHER)                           # ...and its seat
    d.line([2, 23, W - 3, 23], fill=LEATHER_HI)
    d.line([2, 30, W - 3, 30], fill=LEATHER_DK)
    d.rectangle([6, 32, W - 7, 38], fill=SHADE + (90,))         # the table between them
    d.rounded_rectangle([5, 34, W - 6, 56], radius=3, fill=TOP, outline=INK)
    d.line([8, 35, W - 9, 35], fill=TOP_HI)
    d.line([12, 44, 26, 44], fill=TOP_HI)
    d.line([36, 50, 46, 50], fill=TOP_HI)
    d.rectangle([6, 56, W - 7, 58], fill=TOP_DK)
    d.line([6, 59, W - 7, 59], fill=INK)
    pint(d, 14, 38)
    pint(d, 42, 44)
    d.ellipse([27, 40, 37, 47], fill=CREAM, outline=INK)        # a plate of chips
    for x, y in ((29, 42), (32, 43), (34, 42), (31, 44)):
        d.line([x, y, x + 2, y], fill=BEER)
    box(d, 1, 60, W - 2, 68, LEATHER)                           # the near bench: its seat...
    d.line([2, 61, W - 3, 61], fill=LEATHER_HI)
    box(d, 1, 66, W - 2, 95, WOOD)                              # ...and the back of its back
    d.line([2, 67, W - 3, 67], fill=WOOD_HI)
    for x in (4, 33):
        d.rectangle([x, 71, x + 26, 91], outline=WOOD_DK)
        d.line([x + 1, 72, x + 25, 72], fill=WOOD_HI)
        d.line([x + 1, 72, x + 1, 90], fill=WOOD_HI)
    d.line([1, 94, W - 2, 94], fill=WOOD_DK)
    return im


def chalkboard():
    """The specials, chalked on a board on an easel."""
    im, d = new(C, 2 * C)
    shadow(d, 3, 54, 28, 62)
    d.line([7, 8, 4, 60], fill=WOOD_DK, width=2)                # the easel
    d.line([24, 8, 27, 60], fill=WOOD_DK, width=2)
    d.line([15, 30, 15, 56], fill=WOOD_DK)
    box(d, 4, 9, 27, 46, WOOD)
    d.line([5, 10, 26, 10], fill=WOOD_HI)
    d.rectangle([6, 12, 25, 43], fill=SLATE, outline=INK)
    d.line([7, 13, 24, 13], fill=SLATE_HI)
    d.line([9, 16, 22, 16], fill=CREAM)                         # a heading, underlined twice
    d.line([9, 18, 22, 18], fill=BRASS_HI)
    d.ellipse([9, 22, 18, 27], outline=CREAM)                   # a fish, and its chips
    d.polygon([(18, 24), (21, 22), (21, 27)], outline=CREAM)
    d.point((11, 24), fill=CREAM)
    for x, y in ((9, 31), (13, 32), (17, 31)):
        d.line([x, y, x + 2, y], fill=BEER)
    for y, w in ((35, 12), (38, 8), (41, 10)):                  # the rest, in a smaller hand
        d.line([9, y, 9 + w, y], fill=CREAM_SH)
    d.line([20, 38, 22, 38], fill=rgb('ff9b92'))              # a price, in pink chalk
    return im


def lamp_hang():
    """A green glass lamp on a brass chain: hung from the ceiling, over your head."""
    im, d = new(C, 2 * C)
    for y in range(0, 31, 3):
        d.point((15, y), fill=BRASS_DK)
        d.point((16, y + 1), fill=BRASS)
    d.rectangle([13, 30, 18, 33], fill=BRASS, outline=INK)
    d.polygon([(11, 34), (20, 34), (27, 46), (4, 46)], fill=GREEN_HI, outline=INK)   # the shade
    d.line([12, 36, 8, 44], fill=GREEN_GLINT)
    d.line([20, 36, 24, 44], fill=GREEN_DK)
    d.rectangle([4, 46, 27, 47], fill=BRASS, outline=INK)
    d.ellipse([10, 46, 21, 52], fill=GLOW, outline=BRASS_DK)    # the bulb under it: unlit, the pack's dim gold
    d.rectangle([13, 48, 16, 49], fill=GLOW_HI)
    return im


def sprites():
    return {
        'pub-in-floor-a': boards(0), 'pub-in-floor-b': boards(15),
        'pub-in-side-w': wall_side(PUB, 'w'), 'pub-in-side-e': wall_side(PUB, 'e'),
        'pub-in-wall-front': wall_front(PUB),
        'pub-in-threshold-w': threshold(PUB, 'w'), 'pub-in-threshold-e': threshold(PUB, 'e'),
        'pub-in-doorlight': doorlight,
        'pub-in-wall-panel': wall_panel, 'pub-in-wall-print': wall_print,
        'pub-in-wall-backbar': wall_backbar, 'pub-in-wall-tv': wall_tv, 'pub-in-wall-darts': wall_darts,
        'pub-in-bar': the_bar,
        'pub-in-stool': stool, 'pub-in-table': table,
        'pub-in-chair-w': chair('w'), 'pub-in-chair-e': chair('e'),
        'pub-in-booth': booth, 'pub-in-chalkboard': chalkboard,
        'pub-in-lamp-hang': lamp_hang,
    }


# The hanging lamps are Tops under four rows tall: lifted in front of whatever
# taller thing stands behind them. The light through the door lies on the floor.
DEPTH_BIAS = {'pub-in-lamp-hang': 10, 'pub-in-doorlight': -40}


if __name__ == '__main__':
    register(sprites(), DEPTH_BIAS, sys.argv)
