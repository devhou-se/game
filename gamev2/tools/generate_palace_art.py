#!/usr/bin/env python3
"""generate_palace_art.py — everything inside the palace's audience hall (issue
#215). The GuttyKreum temple packs are exteriors only, so the interior is drawn
here, in the manner of tools/generate_shrine_art.py: shaded pixel art with a
1px ink outline, drawn at half size (32px a cell) and pixel-doubled. Every
colour is one of the GuttyKreum sheets', and the lamps are a dim gold: their
glow at night is src/utils/Glows.js's. Nothing is line art, nothing is random
between runs (every scatter is seeded), and the only text is set in the game's
own font, so a re-run is byte-identical on any machine.

The hall is an Edo ohiroma: gold leaf, black and vermilion lacquer, tatami.
All sprites are `palace-in-<piece>`:
  board-a / board-b       polished boards of the side corridors (engawa), running north
  board-h-a / board-h-b   the same boards running east-west, for the long corridor
  tatami-l / tatami-r     the two halves of a mat with a black-and-gold border
  side-w / side-e         the side walls: shoji seen along their length, lit from outside
  sun-w / sun-e           2x1 daylight thrown across the boards by those shoji (lies flat)
  wall-front              the front wall's head from inside
  threshold-w / -e        a doorway's two cells; doorlight: daylight through it (2x3, flat)
  wall-shoji, wall-plain  1x3 bays of the back wall, under the coffered ceiling's edge
  alcove-shelves          3x3 staggered shelves (chigaidana) left of the dais
  alcove-doors            3x3 tasselled lacquer doors (chodaigamae) right of it
  mural                   12x3 gold-leaf fusuma: an old pine, cranes, gold cloud
  dais                    12x3 the raised jodan: the empty seat, arm rest, sword,
                          candle stands and braziers (bump it: src/PalaceVisit.js)
  pillar                  1x3 vermilion over black lacquer: only its foot is solid
  fusuma-tiger            6x2 the corridor's west screens: a tiger in bamboo
  fusuma-waves            6x2 the corridor's east screens: waves, plovers, a moon
  armour                  2x3 a suit of armour on its chest (bump it)
  swords                  2x2 a rack of three swords
  andon                   1x2 standing paper lamp;  lamp-hang: 1x2 gilt hanging lamp (Tops)
                          (they glow at night: rows of src/utils/Glows.js)
  zabuton                 a retainer's cushion (Over Floor)
  guardpost               3x2 the guard's rack of polearms and his lamp
  guestbook               1x2 the visitors' book on its stand (bump it)
  byobu                   3x2 folding screen: maples over a stream
  table                   2x1 low lacquer table, tea set out

Run from gamev2/:  python3 tools/generate_palace_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFont

C = 32      # canvas px per cell (doubled on save)

def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; palace.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy
VOID = rgb('080d16')
SHADE = rgb('080d16')                    # cast shadows, with alpha
DAY = rgb('e4cecc')                      # daylight lying on the floor, with alpha
WHITE, PAPER, PAPER_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('bcc7cc')
SHOJI, SHOJI_SH = rgb('ffe2e0'), rgb('d7b6ab')                               # paper screens with the day behind them
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')         # a lamp's paper; its small core
LQ, LQ_HI, LQ_DK = rgb('2a2636'), rgb('524b59'), rgb('171831')               # black lacquer
RED, RED_MID, RED_HI, RED_DK = rgb('aa4d31'), rgb('c66347'), rgb('d16b56'), rgb('8a3a22')   # vermilion lacquer
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')         # gilt fittings
LEAF_A, LEAF_B, LEAF_C = rgb('c6aa71'), rgb('c6a663'), rgb('b2a168')         # squares of gold leaf
CLOUD, CLOUD_HI = rgb('e3c587'), rgb('e4cecc')                               # gold mist, lit on top
PINE, PINE_HI, PINE_DK = rgb('506b6b'), rgb('83af6f'), rgb('2e4040')
BARK, BARK_HI, BARK_DK = rgb('7f513b'), rgb('aa775f'), rgb('4d3326')
TATAMI, TATAMI_MID, TATAMI_HI, TATAMI_DK = rgb('b2ad73'), rgb('b2a168'), rgb('b0c276'), rgb('928372')
HERI, HERI_HI = rgb('2e4040'), rgb('506b6b')
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = rgb('7f513b'), rgb('85553e'), rgb('aa775f'), rgb('5a3827')
PLASTER, PLASTER_SH, PLASTER_DK = rgb('e4cecc'), rgb('d7b6ab'), rgb('c69f96')
PURPLE, PURPLE_HI, PURPLE_DK = rgb('5c527d'), rgb('8f72b6'), rgb('3f3651')
INDIGO, INDIGO_HI, INDIGO_DK = rgb('314b8e'), rgb('588cc6'), rgb('172459')
WATER, WATER_HI = rgb('4b6396'), rgb('7db9fa')
STEEL, STEEL_HI, STEEL_DK = rgb('a4b0b5'), rgb('dae2e4'), rgb('575f79')
BAMBOO, BAMBOO_HI, BAMBOO_DK = rgb('678e57'), rgb('83af6f'), rgb('395050')
TIGER, TIGER_HI, TIGER_DK = rgb('ce6a42'), rgb('f6a583'), rgb('904a37')
MAPLE, MAPLE_HI = rgb('d16b56'), rgb('e78d7b')
BRONZE, BRONZE_HI, BRONZE_DK = rgb('826f60'), rgb('a68777'), rgb('594b45')
EARTH, MOSS = rgb('a7843b'), rgb('678e57')
CELADON, CELADON_HI = rgb('a0bbc2'), rgb('dae2e4')
PEONY = rgb('e78d7b')
COFFER_A, COFFER_B = rgb('4b6396'), rgb('83374f')                            # the ceiling's painted panels

_FONTS = {}


def kana(size=12):
    if size not in _FONTS:
        _FONTS[size] = ImageFont.truetype('fonts/PixelMplus12-Grid.ttf', size)
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


def outline_alpha(im, colour=INK):
    """Ink every transparent pixel that touches an opaque one (4-neighbours)."""
    src = im.load()
    w, h = im.size
    edge = []
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] == 255:
                    edge.append((x, y))
                    break
    for x, y in edge:
        src[x, y] = colour + (255,)
    return im


def shadow(d, x0, y0, x1, y1, a=70):
    d.ellipse([x0, y0, x1, y1], fill=SHADE + (a,))


def stud(d, x, y):
    """A gilt nail cover, 3x3."""
    d.rectangle([x, y, x + 2, y + 2], fill=GOLD)
    d.point((x, y), fill=GOLD_HI)
    d.point((x + 2, y + 2), fill=GOLD_DK)


def gold_leaf(d, x0, y0, x1, y1, seed):
    """A ground of gold leaf: squares of slightly different gold, as laid."""
    rnd = random.Random(seed)
    d.rectangle([x0, y0, x1, y1], fill=LEAF_A)
    for y in range(y0, y1 + 1, 8):
        for x in range(x0 - (4 if (y // 8) % 2 else 0), x1 + 1, 8):
            col = rnd.choice((LEAF_A, LEAF_A, LEAF_B, LEAF_C))
            d.rectangle([max(x, x0), y, min(x + 7, x1), min(y + 7, y1)], fill=col)
            if rnd.random() < 0.3:
                d.point((min(max(x + rnd.randrange(8), x0), x1), min(y + rnd.randrange(8), y1)), fill=GOLD_HI)


def gold_cloud(d, x0, y, x1, clip=None):
    """A band of gold mist (suyari-gasumi): a long bar with round ends, lit on top."""
    for i, (dy, inset) in enumerate(((0, 4), (1, 1), (2, 0), (3, 0), (4, 1), (5, 4))):
        a, b = x0 + inset, x1 - inset
        if clip:
            a, b = max(a, clip[0]), min(b, clip[1])
        if a <= b:
            d.line([a, y + dy, b, y + dy], fill=CLOUD_HI if i < 2 else CLOUD)
    a, b = x0 + 4, x1 - 4
    if clip:
        a, b = max(a, clip[0]), min(b, clip[1])
    if a <= b:
        d.line([a, y + 6, b, y + 6], fill=GOLD_DK)


# ---- floors -----------------------------------------------------------------------

def board(shift, across=False):
    """Polished boards, four a cell: running north, or (across) east-west."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=BOARD)
        for i in range(4):
            a = i * 8
            joint = (shift + (10 if i % 2 == 0 else 26) + i * 3) % 32
            streak = (joint + 9 + i * 5) % 32
            if across:
                if i % 2:
                    d.rectangle([0, a, 31, a + 7], fill=BOARD_ALT)
                d.line([0, a, 31, a], fill=BOARD_DK)
                d.line([joint, a + 1, joint, a + 7], fill=BOARD_DK)
                for k in range(7):
                    d.point(((streak + k) % 32, a + 3), fill=BOARD_HI)
                d.point(((streak + 13) % 32, a + 5), fill=BOARD_HI)
                d.point(((streak + 14) % 32, a + 5), fill=BOARD_HI)
            else:
                if i % 2:
                    d.rectangle([a, 0, a + 7, 31], fill=BOARD_ALT)
                d.line([a, 0, a, 31], fill=BOARD_DK)
                d.line([a + 1, joint, a + 7, joint], fill=BOARD_DK)
                for k in range(7):
                    d.point((a + 3, (streak + k) % 32), fill=BOARD_HI)
                d.point((a + 5, (streak + 13) % 32), fill=BOARD_HI)
                d.point((a + 5, (streak + 14) % 32), fill=BOARD_HI)
        return im
    return draw


def tatami(side):
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=TATAMI)
        for y in range(3, 29, 2):               # the weave
            d.line([0, y, 31, y], fill=TATAMI_DK if y % 4 == 1 else TATAMI_HI)
        for x in range(2 if side == 'l' else 6, 32, 8):
            for y in range(4, 28, 4):
                d.point((x, y), fill=TATAMI_DK)
        for y0 in (0, 31):                      # the cloth border: dark silk, a gold figure woven in
            d.line([0, y0, 31, y0], fill=HERI)
        d.line([0, 1, 31, 1], fill=HERI_HI)
        d.line([0, 30, 31, 30], fill=HERI_HI)
        for x in range(1 if side == 'l' else 5, 32, 8):
            d.point((x, 1), fill=GOLD)
            d.point((x + 4, 30), fill=GOLD)
        x = 0 if side == 'l' else 31            # the mat's end
        d.line([x, 3, x, 28], fill=TATAMI_DK)
        return im
    return draw


def zabuton():
    im, d = new(C, C)
    d.rounded_rectangle([5, 9, 26, 25], radius=3, fill=PURPLE, outline=INK)
    d.line([7, 10, 24, 10], fill=PURPLE_HI)
    d.line([6, 12, 6, 22], fill=PURPLE_HI)
    d.line([7, 24, 24, 24], fill=PURPLE_DK)
    d.line([25, 13, 25, 23], fill=PURPLE_DK)
    for x, y in ((11, 14), (20, 14), (11, 20), (20, 20)):     # the tufting
        d.point((x, y), fill=PURPLE_DK)
    d.rectangle([15, 16, 16, 18], fill=GOLD)
    d.point((15, 16), fill=GOLD_HI)
    for x, y in ((5, 9), (26, 9), (5, 25), (26, 25)):         # corner tassels
        d.point((x, y), fill=GOLD)
    return im


def wall_side(side):
    """A side wall seen along its length from above: the wall's dark head, then
    a sliver of its paper screens, lit by the day outside."""
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        d.rectangle([12, 0, 21, 31], fill=LQ)                   # the head rail
        d.line([13, 0, 13, 31], fill=LQ_HI)
        d.rectangle([22, 0, 29, 31], fill=SHOJI)                # paper
        d.line([22, 0, 22, 31], fill=INK)
        for y in (0, 10, 21):                                   # the lattice, foreshortened
            d.line([23, y, 29, y], fill=BOARD)
        d.line([26, 0, 26, 31], fill=SHOJI_SH)
        d.rectangle([30, 0, 31, 31], fill=BOARD_DK)             # the sill the screens run in
        d.line([30, 0, 30, 31], fill=INK)
        d.rectangle([22, 15, 31, 17], fill=RED_DK)              # a post between two screens
        d.line([22, 15, 31, 15], fill=RED)
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def sun(side):
    """Daylight through the screens, lying across the corridor's boards (2x1):
    a pale slant, strongest by the wall, the lattice's shadow in it."""
    def draw():
        im, d = new(2 * C, C)
        for y in range(3, 31):
            reach = 58 - (y - 3)                                 # the far edge slants away from the wall
            for x in range(0, reach):
                if (y - 3) % 9 == 8 or (x + (y - 3) // 2) % 13 == 12:
                    continue                                     # a bar of the lattice
                a = round(96 * (1 - x / 62) ** 1.5)
                if a > 4:
                    im.putpixel((x, y), DAY + (a,))
        return im if side == 'w' else im.transpose(Image.FLIP_LEFT_RIGHT)
    return draw


def wall_front():
    """The front wall from inside: all you see is its head; below it is dark."""
    im, d = new(C, C)
    d.rectangle([0, 0, 31, 31], fill=VOID)
    bar(d, -1, 0, 32, 9, LQ, LQ_HI, LQ_DK)
    d.rectangle([0, 10, 31, 16], fill=BOARD_DK)
    d.line([0, 16, 31, 16], fill=INK)
    d.line([0, 5, 31, 5], fill=RED_DK)
    for x in (7, 23):
        stud(d, x, 3)
    return im


def threshold(side):
    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=WHITE)                  # the day outside
        d.rectangle([0, 0, 31, 2], fill=PAPER)
        for y in (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 18):
            d.line([0, y, 31, y], fill=SHOJI)
        d.line([0, 10, 31, 10], fill=PAPER_SH)                   # the stone step
        d.line([0, 22, 31, 22], fill=PAPER_SH)
        x0 = 0 if side == 'w' else 26                            # the door post
        post(d, x0, -1, x0 + 5, 32, RED, RED_HI, RED_DK)
        d.rectangle([x0, 0, x0 + 5, 6], fill=LQ)
        d.line([x0, 7, x0 + 5, 7], fill=GOLD)
        d.line([x0, 0, x0, 31], fill=INK)
        d.line([x0 + 5, 0, x0 + 5, 31], fill=INK)
        return im
    return draw


def doorlight():
    """Daylight falling in through a door: 2x3, on the floor, strongest at the sill."""
    im, d = new(2 * C, 3 * C)
    for y in range(96):
        t = y / 95
        inset = round((1 - t) * 12)
        a = round(120 * t * t)
        if a:
            d.line([inset, y, 63 - inset, y], fill=DAY + (a,))
    return im


# ---- the back wall ------------------------------------------------------------------

def _wall_head(d, w):
    """The top of every back-wall piece: the coffered ceiling's edge (black
    lacquer ribs, gilt bosses, painted panels between) and the beam under it."""
    d.rectangle([0, 0, w - 1, 13], fill=LQ_DK)
    for x in range(0, w, 8):                                    # the panels, in turn
        d.rectangle([x + 1, 1, x + 6, 5], fill=COFFER_A if (x // 8) % 2 == 0 else COFFER_B)
        d.rectangle([x + 1, 8, x + 6, 12], fill=COFFER_B if (x // 8) % 2 == 0 else COFFER_A)
        d.point((x + 3, 3), fill=GOLD)
        d.point((x + 4, 10), fill=GOLD)
    for x in range(0, w, 8):                                    # ribs and bosses
        d.line([x, 0, x, 13], fill=LQ)
        d.point((x, 6), fill=GOLD_HI)
        d.point((x, 7), fill=GOLD)
        d.point((x, 0), fill=GOLD)
    d.line([0, 6, w - 1, 6], fill=LQ)
    d.line([0, 7, w - 1, 7], fill=LQ)
    for x in range(0, w, 8):
        d.point((x, 6), fill=GOLD_HI)
        d.point((x, 7), fill=GOLD)
    bar(d, -1, 14, w, 21, LQ, LQ_HI, LQ_DK)                     # the beam (nageshi)
    d.line([0, 18, w - 1, 18], fill=RED_DK)
    for x in range(7, w, 16):
        stud(d, x, 16)


def _wall_foot(d, w):
    d.rectangle([0, 88, w - 1, 95], fill=LQ)
    d.line([0, 88, w - 1, 88], fill=INK)
    d.line([0, 89, w - 1, 89], fill=LQ_HI)
    d.line([0, 95, w - 1, 95], fill=INK)


def wall_shoji():
    im, d = new(C, 3 * C)
    d.rectangle([0, 0, 31, 95], fill=PLASTER)
    _wall_head(d, C)
    d.rectangle([1, 23, 30, 87], fill=PAPER)                    # the screen, the day behind it
    d.rectangle([2, 32, 29, 62], fill=SHOJI)
    d.rectangle([2, 40, 29, 54], fill=WHITE)
    for x in (8, 15, 22):                                       # the lattice
        d.line([x, 24, x, 71], fill=BOARD)
    for y in (31, 39, 47, 55, 63, 71):
        d.line([2, y, 29, y], fill=BOARD)
    d.rectangle([2, 72, 29, 86], fill=BOARD)                    # its boarded foot
    d.line([2, 73, 29, 73], fill=BOARD_HI)
    d.line([15, 74, 15, 86], fill=BOARD_DK)
    d.rectangle([1, 23, 30, 87], outline=INK)
    post(d, -1, 22, 1, 88, RED, RED_HI, RED_DK, outline=False)
    post(d, 30, 22, 32, 88, RED, RED_HI, RED_DK, outline=False)
    _wall_foot(d, C)
    return im


def wall_plain():
    """A bay of gold-flecked plaster behind one of the hall's corner posts."""
    im, d = new(C, 3 * C)
    d.rectangle([0, 0, 31, 95], fill=PLASTER)
    rnd = random.Random(215)
    for _ in range(26):
        d.point((rnd.randrange(32), 24 + rnd.randrange(62)), fill=GOLD if rnd.random() < 0.6 else PLASTER_SH)
    for y in (22, 23, 24):
        d.line([0, y, 31, y], fill=PLASTER_SH)
    _wall_head(d, C)
    post(d, 11, 22, 20, 88, RED, RED_HI, RED_DK)
    d.rectangle([11, 66, 20, 88], fill=LQ, outline=INK)         # its lacquered foot
    d.line([12, 67, 12, 87], fill=LQ_HI)
    d.rectangle([11, 63, 20, 66], fill=GOLD, outline=INK)
    d.line([12, 64, 19, 64], fill=GOLD_HI)
    _wall_foot(d, C)
    return im


def alcove_shelves():
    """Chigaidana: the staggered shelves of the alcove left of the dais."""
    W = 3 * C
    im, d = new(W, 3 * C)
    d.rectangle([0, 0, W - 1, 95], fill=PLASTER)
    _wall_head(d, W)
    box(d, 3, 22, W - 4, 87, PLASTER_SH)                        # the recess, in shade
    d.rectangle([4, 23, W - 5, 27], fill=PLASTER_DK)
    # the upper cupboard: four small gold doors
    box(d, 4, 28, W - 5, 42, LQ)
    for i in range(4):
        x0 = 6 + i * 21
        gold_leaf(d, x0, 30, x0 + 19, 40, 300 + i)
        d.rectangle([x0, 30, x0 + 19, 40], outline=LQ_DK)
        d.point((x0 + (17 if i % 2 == 0 else 2), 35), fill=LQ)
    # the two shelves, the little post that joins them
    bar(d, 6, 52, 54, 55, LQ, LQ_HI, LQ_DK)
    bar(d, 44, 64, W - 7, 67, LQ, LQ_HI, LQ_DK)
    post(d, 47, 55, 50, 64, LQ, LQ_HI, LQ_DK)
    d.polygon([(54, 52), (58, 50), (58, 52)], fill=LQ)          # the upturned end of the upper shelf
    # on them: a celadon vase, a lacquer box, an incense burner
    d.ellipse([17, 41, 27, 52], fill=CELADON, outline=INK)
    d.rectangle([20, 38, 24, 42], fill=CELADON, outline=INK)
    d.line([19, 44, 19, 49], fill=CELADON_HI)
    d.line([22, 34, 22, 38], fill=PINE)
    d.point((21, 33), fill=MAPLE)
    d.point((23, 34), fill=MAPLE)
    d.point((22, 32), fill=MAPLE_HI)
    box(d, 60, 58, 72, 64, RED_DK)
    d.line([61, 59, 71, 59], fill=RED_HI)
    d.rectangle([65, 60, 67, 62], fill=GOLD)
    d.ellipse([77, 57, 85, 64], fill=BRONZE, outline=INK)
    d.line([79, 58, 82, 58], fill=BRONZE_HI)
    d.line([81, 52, 81, 56], fill=PAPER_SH)                     # a thread of smoke
    d.point((82, 50), fill=PAPER_SH)
    d.point((81, 48), fill=PAPER_SH)
    # the floor cupboard
    box(d, 4, 74, W - 5, 87, LQ)
    for i in range(4):
        x0 = 6 + i * 21
        gold_leaf(d, x0, 76, x0 + 19, 85, 320 + i)
        d.rectangle([x0, 76, x0 + 19, 85], outline=LQ_DK)
        d.point((x0 + (17 if i % 2 == 0 else 2), 80), fill=LQ)
    for x in (0, W - 4):
        post(d, x, 22, x + 3, 88, RED, RED_HI, RED_DK, outline=False)
    d.line([3, 22, 3, 87], fill=INK)
    d.line([W - 4, 22, W - 4, 87], fill=INK)
    _wall_foot(d, W)
    return im


def alcove_doors():
    """Chodaigamae: the tasselled lacquer doors right of the dais."""
    W = 3 * C
    im, d = new(W, 3 * C)
    d.rectangle([0, 0, W - 1, 95], fill=PLASTER)
    _wall_head(d, W)
    box(d, 3, 22, W - 4, 87, LQ)                                # the heavy black frame
    d.line([4, 23, W - 5, 23], fill=LQ_HI)
    for x in (10, 30, 64, 84):
        stud(d, x, 25)
    for i in range(4):                                          # four gold doors
        x0 = 8 + i * 20
        gold_leaf(d, x0, 31, x0 + 18, 78, 340 + i)
        d.rectangle([x0, 31, x0 + 18, 78], outline=LQ_DK)
        # a spray of peony on each
        rnd = random.Random(350 + i)
        for _ in range(3):
            cx, cy = x0 + 4 + rnd.randrange(11), 42 + rnd.randrange(28)
            d.line([cx, cy, cx - 2, cy + 6], fill=PINE)
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=WHITE if rnd.random() < 0.5 else PEONY)
            d.point((cx, cy), fill=MAPLE)
            d.point((cx + 2, cy + 4), fill=PINE_HI)
    box(d, 4, 79, W - 5, 87, LQ)                                # the raised sill
    d.line([5, 80, W - 6, 80], fill=LQ_HI)
    for x in (16, 47, 78):
        stud(d, x, 82)
    # the tassels on the middle pair: a knot, two cords, two heavy tassels
    for x in (40, 54):
        d.line([x, 34, x, 52], fill=RED)
        d.line([x + 1, 34, x + 1, 52], fill=RED_DK)
        d.ellipse([x - 3, 38, x + 4, 45], outline=RED)
        d.rectangle([x - 1, 52, x + 2, 54], fill=GOLD)
        d.rectangle([x - 2, 55, x + 3, 66], fill=RED, outline=RED_DK)
        d.line([x, 56, x, 65], fill=RED_HI)
    for x in (0, W - 4):
        post(d, x, 22, x + 3, 88, RED, RED_HI, RED_DK, outline=False)
    _wall_foot(d, W)
    return im


def _pine_pad(d, cx, cy, w, h, rnd):
    """One flat-bottomed cloud of pine needles."""
    x0, x1 = cx - w // 2, cx + w // 2
    d.pieslice([x0, cy - h, x1, cy + h], 180, 360, fill=PINE_DK)
    d.pieslice([x0 + 1, cy - h + 1, x1 - 1, cy + h - 3], 180, 360, fill=PINE)
    d.line([x0 + 1, cy, x1 - 1, cy], fill=PINE_DK)
    for x in range(x0 + 2, x1 - 1, 2):                          # needles, fanned along the crown
        u = (x - cx) / (w / 2)
        top = cy - round(h * math.sqrt(max(0, 1 - u * u))) + 1
        if top < cy - 1:
            d.line([x, top, x, top + 1 + rnd.randrange(2)], fill=PINE_HI)
    for _ in range(max(2, w // 6)):
        x = rnd.randrange(x0 + 3, x1 - 2)
        d.point((x, cy - 1 - rnd.randrange(max(1, h // 2))), fill=PINE_DK)


def _limb(d, pts, width):
    for col, w in ((BARK_DK, width + 2), (BARK, width)):
        d.line(pts, fill=col, width=w, joint='curve')
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):                # the lit upper edge, a few knots
        d.line([x0, y0 - width // 2 + 1, x1, y1 - width // 2 + 1], fill=BARK_HI)


def _crane(d, x, y, flip=False, flying=False):
    """A red-crowned crane with its feet at (x, y) (standing) or its body there (flying)."""
    s = -1 if flip else 1
    P = lambda dx, dy: (x + s * dx, y + dy)
    if flying:
        d.polygon([P(-10, 0), P(6, -1), P(8, 2), P(-9, 3)], fill=WHITE, outline=PAPER_SH)       # body
        d.polygon([P(-2, 0), P(-12, -12), P(-5, -10), P(4, -1)], fill=WHITE, outline=PAPER_SH)   # far wing
        d.polygon([P(-1, 2), P(-14, 10), P(-7, 10), P(5, 3)], fill=WHITE, outline=PAPER_SH)      # near wing
        d.line([P(-12, -12), P(-8, -11)], fill=LQ)
        d.line([P(-14, 10), P(-9, 10)], fill=LQ)
        d.line([P(8, 1), P(17, -3)], fill=LQ, width=2)                                         # neck
        d.point(P(18, -4), fill=RED)
        d.line([P(19, -3), P(22, -3)], fill=GOLD_DK)
        d.line([P(-10, 2), P(-18, 4)], fill=LQ)                                                # legs trail
        return
    d.line([P(-1, 0), P(-1, -9)], fill=LQ)                                                     # legs
    d.line([P(3, 0), P(2, -9)], fill=LQ)
    d.line([P(-1, 0), P(1, 0)], fill=LQ)
    d.ellipse([min(P(-7, 0)[0], P(7, 0)[0]), y - 17, max(P(-7, 0)[0], P(7, 0)[0]), y - 8], fill=WHITE, outline=PAPER_SH)
    d.polygon([P(-7, -13), P(-12, -9), P(-6, -9)], fill=LQ)                                    # tail
    d.line([P(-5, -11), P(2, -10)], fill=PAPER_SH)
    d.line([P(6, -14), P(8, -20), P(7, -25)], fill=LQ, width=2)                                # neck
    d.rectangle([min(P(6, 0)[0], P(9, 0)[0]), y - 28, max(P(6, 0)[0], P(9, 0)[0]), y - 26], fill=WHITE)
    d.point(P(8, -29), fill=RED)
    d.point(P(7, -29), fill=RED)
    d.line([P(10, -27), P(13, -26)], fill=GOLD_DK)


def _seams(d, w, y0, y1, step=48):
    """The stiles between sliding screens, and the pulls by each."""
    for x in range(0, w + 1, step):
        d.rectangle([x - 1, y0, x, y1], fill=LQ)
        d.line([x + 1, y0, x + 1, y1], fill=GOLD_DK)
    for x in range(step, w, step * 2):
        for dx in (-5, 4):
            d.rectangle([x + dx, (y0 + y1) // 2 - 2, x + dx + 1, (y0 + y1) // 2 + 2], fill=GOLD_HI, outline=GOLD_DK)


def mural():
    """The back wall of the hall: eight gold-leaf screens painted as one
    picture - an old pine across them all, cranes under it, gold cloud."""
    W = 12 * C
    im, d = new(W, 3 * C)
    rnd = random.Random(2150)
    gold_leaf(d, 0, 22, W - 1, 87, 215)
    _wall_head(d, W)
    # gold cloud drifting across the top and through the picture
    for x0, y, x1 in ((6, 26, 96), (70, 33, 150), (210, 25, 300), (284, 32, 378), (150, 74, 236), (20, 66, 84), (300, 70, 372)):
        gold_cloud(d, x0, y, x1)
    # the ground the pine stands on: a bank of earth and moss at the left
    d.polygon([(0, 87), (0, 76), (30, 72), (70, 75), (112, 82), (130, 87)], fill=EARTH)
    d.polygon([(0, 87), (0, 80), (34, 76), (80, 80), (118, 87)], fill=MOSS)
    for _ in range(26):
        d.point((rnd.randrange(4, 112), 79 + rnd.randrange(8)), fill=PINE)
    # the pine: a heavy trunk leaning in from the left, one bough the length of the wall
    _limb(d, [(34, 87), (40, 70), (52, 56), (70, 47)], 11)
    _limb(d, [(70, 47), (104, 42), (150, 46), (196, 42), (240, 46), (286, 43)], 6)
    _limb(d, [(52, 56), (44, 42), (30, 36)], 5)
    _limb(d, [(150, 46), (170, 56), (196, 60)], 3)
    _limb(d, [(240, 46), (262, 54), (290, 57), (318, 54)], 3)
    _limb(d, [(104, 42), (118, 34), (136, 31)], 3)
    for x, y in ((38, 74), (44, 64), (41, 80), (48, 60), (58, 52), (36, 68)):      # bark
        d.line([x, y, x + 2, y + 3], fill=BARK_DK)
    pads = [(26, 37, 34, 9), (56, 33, 30, 8), (96, 38, 40, 10), (138, 30, 34, 9), (160, 44, 38, 9),
            (204, 39, 44, 10), (198, 60, 30, 7), (252, 43, 40, 9), (296, 40, 36, 9), (322, 54, 32, 7),
            (76, 48, 26, 6), (120, 50, 28, 6)]
    for cx, cy, w, h in pads:
        _pine_pad(d, cx, cy, w, h, rnd)
    # cranes: a pair on the bank, one coming in to land, one by the water at the right
    _crane(d, 92, 86)
    _crane(d, 118, 87, flip=True)
    _crane(d, 250, 70, flying=True, flip=True)
    _crane(d, 342, 86, flip=True)
    # water and reeds at the right
    d.polygon([(250, 87), (270, 80), (384, 78), (384, 87)], fill=WATER)
    for x0, y in ((268, 82), (300, 84), (330, 81), (356, 85), (286, 86)):
        d.line([x0, y, x0 + 9, y], fill=WATER_HI)
    for x in (362, 366, 371, 376):
        d.line([x, 80, x - 1, 66 + (x % 5)], fill=PINE_DK)
        d.point((x - 1, 65 + (x % 5)), fill=BARK_HI)
    _seams(d, W, 22, 87)
    d.line([0, 22, W - 1, 22], fill=INK)
    _wall_foot(d, W)
    return im


# ---- the dais -----------------------------------------------------------------------

def _candle(d, x, y):
    """A tall candle stand with its foot at (x, y)."""
    d.ellipse([x - 5, y - 3, x + 5, y + 1], fill=LQ, outline=INK)
    d.rectangle([x - 1, y - 30, x, y - 3], fill=LQ)
    d.line([x - 1, y - 30, x - 1, y - 3], fill=LQ_HI)
    d.rectangle([x - 2, y - 18, x + 1, y - 16], fill=GOLD)
    d.ellipse([x - 5, y - 33, x + 4, y - 29], fill=GOLD, outline=INK)
    d.rectangle([x - 2, y - 40, x + 1, y - 33], fill=WHITE, outline=PAPER_SH)
    d.rectangle([x - 1, y - 45, x, y - 41], fill=LAMP)
    d.point((x - 1, y - 46), fill=LAMP_SH)
    d.point((x, y - 43), fill=LAMP_HI)


def _brazier(d, x, y):
    """A bronze hibachi with its foot at (x, y)."""
    d.ellipse([x - 9, y - 12, x + 9, y], fill=BRONZE, outline=INK)
    d.ellipse([x - 8, y - 14, x + 8, y - 7], fill=BRONZE_DK, outline=INK)
    d.ellipse([x - 6, y - 13, x + 6, y - 9], fill=PAPER_SH)                       # ash
    for dx in (-3, 0, 3):
        d.point((x + dx, y - 11), fill=RED_HI)
    d.line([x - 7, y - 5, x - 3, y - 2], fill=BRONZE_HI)
    d.line([x + 2, y - 14, x + 2, y - 19], fill=LQ_HI)                              # fire tongs
    d.line([x + 4, y - 14, x + 4, y - 19], fill=LQ_HI)


def dais():
    """The jodan: a floor one step up, matted, where the lord sat. His seat is
    there; he is not."""
    W = 12 * C
    im, d = new(W, 3 * C)
    # the raised floor: mats laid across, a broad figured border round the lot
    d.rectangle([0, 0, W - 1, 81], fill=TATAMI_HI)
    for y in range(1, 81, 2):
        d.line([0, y, W - 1, y], fill=TATAMI if y % 4 == 1 else TATAMI_HI)
    for y in range(0, 6):                                        # shade under the painted wall
        d.line([0, y, W - 1, y], fill=TATAMI_DK if y < 2 else TATAMI_MID if y < 4 else TATAMI)
    for x in range(0, W + 1, 64):                                # the mats' borders (ungen: white, red, indigo)
        d.rectangle([x - 2, 0, x + 1, 81], fill=WHITE)
        for y in range(0, 81, 6):
            d.rectangle([x - 2, y, x + 1, y + 1], fill=RED if (y // 6) % 2 == 0 else INDIGO)
    d.rectangle([0, 40, W - 1, 43], fill=WHITE)
    for x in range(0, W, 6):
        d.rectangle([x, 40, x + 1, 43], fill=RED if (x // 6) % 2 == 0 else INDIGO)
    # the step's face: black lacquer, gilt plates
    d.rectangle([0, 82, W - 1, 93], fill=LQ)
    d.line([0, 82, W - 1, 82], fill=INK)
    d.line([0, 83, W - 1, 83], fill=LQ_HI)
    d.line([0, 93, W - 1, 93], fill=INK)
    for x in range(14, W, 32):
        d.rectangle([x, 85, x + 5, 90], fill=GOLD, outline=GOLD_DK)
        d.point((x + 1, 86), fill=GOLD_HI)
        d.point((x + 3, 88), fill=GOLD_DK)
    for x in range(0, W):                                        # its shadow on the hall floor
        d.point((x, 94), fill=SHADE + (90,))
        d.point((x, 95), fill=SHADE + (40,))
    d.line([0, 0, 0, 93], fill=INK)
    d.line([W - 1, 0, W - 1, 93], fill=INK)
    # the seat: a thick mat of its own, a brocade cushion, the arm rest beside it
    cx = W // 2
    shadow(d, cx - 40, 62, cx + 40, 72, 50)
    box(d, cx - 38, 34, cx + 37, 62, TATAMI_HI)
    for y in range(36, 61, 2):
        d.line([cx - 37, y, cx + 36, y], fill=TATAMI)
    box(d, cx - 38, 62, cx + 37, 67, TATAMI_MID)                  # its thick edge
    for x in range(cx - 38, cx + 38, 6):                         # ungen border all round
        col = RED if ((x - cx) // 6) % 2 == 0 else INDIGO
        d.rectangle([x, 34, min(x + 2, cx + 37), 36], fill=col)
        d.rectangle([x, 60, min(x + 2, cx + 37), 62], fill=col)
    d.rectangle([cx - 38, 34, cx + 37, 67], outline=INK)
    d.rounded_rectangle([cx - 17, 40, cx + 16, 57], radius=4, fill=PURPLE, outline=INK)   # the cushion
    d.line([cx - 14, 41, cx + 13, 41], fill=PURPLE_HI)
    d.line([cx - 14, 56, cx + 13, 56], fill=PURPLE_DK)
    for dx, dy in ((-9, 45), (8, 45), (-9, 52), (8, 52), (0, 48)):
        d.rectangle([cx + dx - 1, dy - 1, cx + dx, dy], fill=GOLD)
    for dx, dy in ((-17, 40), (16, 40), (-17, 57), (16, 57)):
        d.point((cx + dx, dy), fill=GOLD_HI)
    box(d, cx + 22, 44, cx + 33, 48, RED_DK)                     # the arm rest: a padded top on a lacquer stand
    d.line([cx + 23, 45, cx + 32, 45], fill=RED_HI)
    d.rectangle([cx + 24, 49, cx + 25, 55], fill=LQ)
    d.rectangle([cx + 30, 49, cx + 31, 55], fill=LQ)
    d.line([cx + 22, 56, cx + 33, 56], fill=LQ)
    # behind the seat, the sword on its upright stand
    d.rectangle([cx - 31, 26, cx - 24, 32], fill=LQ, outline=INK)
    d.line([cx - 28, 4, cx - 27, 27], fill=LQ, width=3)
    d.line([cx - 29, 6, cx - 29, 26], fill=LQ_HI)
    d.rectangle([cx - 30, 10, cx - 25, 11], fill=GOLD)           # guard
    for y in (5, 7, 9):
        d.point((cx - 28, y), fill=WHITE)                        # the hilt's binding
    d.rectangle([cx - 29, 20, cx - 26, 21], fill=RED)
    # candle stands either side, braziers further out, low tables at the ends
    _candle(d, cx - 62, 58)
    _candle(d, cx + 62, 58)
    _brazier(d, cx - 112, 62)
    _brazier(d, cx + 112, 62)
    for x0 in (22, W - 54):
        shadow(d, x0 - 2, 62, x0 + 34, 69, 50)
        box(d, x0, 48, x0 + 31, 53, RED_DK)
        d.line([x0 + 1, 49, x0 + 30, 49], fill=RED_HI)
        d.rectangle([x0 + 2, 54, x0 + 4, 64], fill=LQ)
        d.rectangle([x0 + 27, 54, x0 + 29, 64], fill=LQ)
        d.line([x0 + 2, 60, x0 + 29, 60], fill=LQ)
        # on it: a scroll box and a writing box
        box(d, x0 + 4, 43, x0 + 14, 47, LQ)
        d.rectangle([x0 + 8, 44, x0 + 10, 46], fill=GOLD)
        d.rectangle([x0 + 18, 44, x0 + 27, 47], fill=WHITE, outline=INK)
        d.line([x0 + 20, 45, x0 + 25, 45], fill=RED)
    return im


def pillar():
    """A round column: vermilion over a black-lacquer foot, gilt at the joins."""
    im, d = new(C, 3 * C)
    shadow(d, 5, 86, 27, 95, 80)
    d.rectangle([10, 3, 21, 90], fill=RED)
    d.rectangle([11, 3, 12, 90], fill=RED_HI)
    d.rectangle([13, 3, 13, 90], fill=RED_MID)
    d.rectangle([18, 3, 20, 90], fill=RED_DK)
    d.rectangle([10, 60, 21, 90], fill=LQ)                       # the lacquered foot
    d.rectangle([11, 60, 12, 90], fill=LQ_HI)
    d.rectangle([18, 60, 20, 90], fill=LQ_DK)
    d.line([10, 3, 10, 90], fill=INK)
    d.line([21, 3, 21, 90], fill=INK)
    for y0 in (56, 22):                                          # gilt bands
        d.rectangle([9, y0, 22, y0 + 4], fill=GOLD, outline=INK)
        d.line([10, y0 + 1, 13, y0 + 1], fill=GOLD_HI)
        d.line([18, y0 + 3, 21, y0 + 3], fill=GOLD_DK)
    box(d, 6, 0, 25, 4, LQ)                                      # the bracket block at its head
    d.line([7, 1, 24, 1], fill=LQ_HI)
    box(d, 8, 4, 23, 8, GOLD)
    d.line([9, 5, 22, 5], fill=GOLD_HI)
    d.ellipse([6, 86, 25, 94], fill=STEEL_DK, outline=INK)       # the stone it stands on
    d.ellipse([8, 86, 23, 91], fill=STEEL)
    d.rectangle([10, 84, 21, 88], fill=LQ)
    d.line([10, 84, 10, 88], fill=INK)
    d.line([21, 84, 21, 88], fill=INK)
    return im


# ---- the corridor's screens ---------------------------------------------------------

def _screen_run(seed):
    """A 6x2 run of sliding screens between two rooms: a lintel, the painted
    leaf, a black foot rail. The caller paints on the leaf (y 9..55)."""
    W = 6 * C
    im, d = new(W, 2 * C)
    gold_leaf(d, 0, 9, W - 1, 56, seed)
    bar(d, -1, 0, W, 8, LQ, LQ_HI, LQ_DK)
    d.line([0, 5, W - 1, 5], fill=RED_DK)
    for x in range(7, W, 16):
        stud(d, x, 3)
    return im, d


def _screen_finish(im, d):
    W = im.width
    _seams(d, W, 9, 56)
    d.rectangle([0, 57, W - 1, 63], fill=LQ)
    d.line([0, 57, W - 1, 57], fill=INK)
    d.line([0, 58, W - 1, 58], fill=LQ_HI)
    d.line([0, 63, W - 1, 63], fill=INK)
    return im


def _bamboo(d, x, y0, y1, lean=0):
    n = max(1, (y1 - y0) // 9)
    for i in range(n):
        ya, yb = y1 - i * 9, max(y0, y1 - (i + 1) * 9 + 1)
        xa = x + round(lean * i / n)
        d.rectangle([xa, yb, xa + 2, ya], fill=BAMBOO)
        d.line([xa, yb, xa, ya], fill=BAMBOO_HI)
        d.line([xa + 2, yb, xa + 2, ya], fill=BAMBOO_DK)
        d.line([xa, ya, xa + 2, ya], fill=BAMBOO_DK)
        if i % 2 == 1 and yb > y0 + 3:                           # a spray of leaves at the joint
            for s in (-1, 1):
                d.line([xa + 1, yb + 1, xa + 1 + s * 6, yb - 2], fill=BAMBOO_DK)
                d.line([xa + 1 + s * 3, yb, xa + 1 + s * 8, yb + 2], fill=BAMBOO)


def fusuma_tiger():
    im, d = _screen_run(2151)
    gold_cloud(d, 4, 12, 70)
    gold_cloud(d, 120, 16, 188)
    for x, lean in ((10, 2), (22, -1), (58, 3), (142, -2), (156, 2), (178, -1), (120, 1)):
        _bamboo(d, x, 10, 56, lean)
    d.polygon([(0, 56), (0, 50), (40, 47), (96, 50), (150, 46), (191, 50), (191, 56)], fill=EARTH)
    # the tiger: crouched, looking back over its shoulder
    x, y = 74, 49
    d.line([x - 22, y - 8, x - 30, y - 14, x - 28, y - 22], fill=TIGER_DK, width=3, joint='curve')   # tail
    d.line([x - 22, y - 9, x - 29, y - 14, x - 28, y - 21], fill=TIGER)
    d.ellipse([x - 24, y - 16, x + 12, y - 2], fill=TIGER, outline=TIGER_DK)                         # body
    d.ellipse([x - 20, y - 8, x + 6, y - 1], fill=PAPER)                                             # belly
    for lx in (-20, -12, 2, 10):                                                                     # legs
        d.rectangle([x + lx, y - 5, x + lx + 4, y + 1], fill=TIGER, outline=TIGER_DK)
        d.line([x + lx + 1, y + 1, x + lx + 3, y + 1], fill=PAPER)
    d.ellipse([x + 6, y - 24, x + 22, y - 9], fill=TIGER, outline=TIGER_DK)                          # head
    d.polygon([(x + 7, y - 21), (x + 8, y - 26), (x + 12, y - 23)], fill=TIGER_DK)
    d.polygon([(x + 17, y - 23), (x + 21, y - 26), (x + 21, y - 20)], fill=TIGER_DK)
    d.ellipse([x + 10, y - 16, x + 19, y - 10], fill=PAPER)                                          # muzzle
    d.point((x + 11, y - 18), fill=LQ)
    d.point((x + 17, y - 18), fill=LQ)
    d.point((x + 11, y - 19), fill=GOLD_HI)
    d.point((x + 17, y - 19), fill=GOLD_HI)
    d.line([x + 13, y - 14, x + 15, y - 14], fill=LQ)
    d.point((x + 14, y - 13), fill=RED_DK)
    for sx in (-18, -13, -8, -3, 2):                                                                 # stripes
        d.line([x + sx, y - 15, x + sx + 2, y - 9], fill=LQ)
    for sx in (9, 13, 17):
        d.line([x + sx, y - 23, x + sx, y - 21], fill=LQ)
    d.line([x - 29, y - 17, x - 27, y - 17], fill=LQ)
    d.line([x - 30, y - 13, x - 28, y - 13], fill=LQ)
    return _screen_finish(im, d)


def fusuma_waves():
    im, d = _screen_run(2152)
    gold_cloud(d, 30, 13, 110)
    d.ellipse([146, 12, 166, 32], fill=PAPER, outline=CLOUD)                # the moon
    gold_cloud(d, 132, 26, 186)
    # the sea: rows of rollers, each crest a white comb
    d.rectangle([0, 36, 191, 56], fill=INDIGO)
    for row, y in enumerate((36, 42, 48, 54)):
        for x in range(-12 + (row % 2) * 9, 200, 18):
            d.pieslice([x, y - 5, x + 18, y + 9], 180, 360, fill=INDIGO if row % 2 else INDIGO_DK)
            d.arc([x, y - 5, x + 18, y + 9], 180, 360, fill=WHITE)
            d.arc([x + 3, y - 2, x + 15, y + 9], 180, 360, fill=INDIGO_HI)
            d.point((x + 9, y - 6), fill=WHITE)
            d.point((x + 12, y - 6), fill=WHITE)
    d.rectangle([0, 55, 191, 56], fill=INDIGO_DK)
    # plovers over the water
    for x, y in ((26, 28), (40, 22), (58, 30), (86, 24), (104, 31), (124, 22)):
        d.polygon([(x - 4, y - 2), (x, y), (x + 4, y - 3), (x + 1, y + 2), (x - 1, y + 2)], fill=WHITE, outline=PAPER_SH)
        d.point((x + 3, y), fill=LQ)
    # a rock the sea breaks on
    d.polygon([(4, 56), (8, 40), (16, 34), (24, 38), (30, 56)], fill=BRONZE, outline=INK)
    d.line([10, 40, 16, 36], fill=BRONZE_HI)
    d.line([18, 42, 22, 52], fill=BRONZE_DK)
    for x, y in ((2, 40), (30, 42), (27, 36), (5, 34), (33, 48)):
        d.point((x, y), fill=WHITE)
    return _screen_finish(im, d)


# ---- furniture ----------------------------------------------------------------------

def armour():
    """A suit of armour set up on its chest: horned helmet, laced cuirass."""
    im, d = new(2 * C, 3 * C)
    shadow(d, 6, 84, 57, 95, 80)
    # the chest
    box(d, 13, 70, 50, 92, LQ)
    d.line([14, 71, 49, 71], fill=LQ_HI)
    d.rectangle([14, 88, 49, 91], fill=LQ_DK)
    d.ellipse([27, 76, 36, 85], fill=GOLD, outline=GOLD_DK)       # the crest on it
    d.ellipse([30, 79, 33, 82], fill=LQ)
    for x in (15, 46):
        d.rectangle([x, 72, x + 2, 76], fill=GOLD)
    # the skirt: four hanging plates, laced in rows
    for i, x0 in enumerate((11, 22, 32, 43)):
        d.polygon([(x0 + 1, 52), (x0 + 9, 52), (x0 + 10, 70), (x0, 70)], fill=LQ, outline=INK)
        for y in (56, 60, 64, 68):
            d.line([x0 + 1, y, x0 + 9, y], fill=RED if (y // 4) % 2 == 0 else GOLD)
    # the cuirass
    d.polygon([(18, 34), (45, 34), (47, 53), (16, 53)], fill=LQ, outline=INK)
    for y in range(37, 52, 3):
        d.line([18, y, 45, y], fill=RED)
        d.line([18, y + 1, 45, y + 1], fill=RED_DK)
    d.rectangle([28, 36, 35, 44], fill=GOLD, outline=GOLD_DK)     # breast plate
    d.point((29, 37), fill=GOLD_HI)
    d.line([19, 35, 19, 52], fill=LQ_HI)
    # shoulder guards
    for x0 in (6, 46):
        d.rectangle([x0, 33, x0 + 11, 52], fill=LQ, outline=INK)
        for y in range(36, 52, 4):
            d.line([x0 + 1, y, x0 + 10, y], fill=RED)
            d.line([x0 + 1, y + 1, x0 + 10, y + 1], fill=GOLD_DK)
        d.line([x0 + 1, 34, x0 + 10, 34], fill=GOLD)
    # the mask, the neck guard, the helmet
    d.rectangle([24, 25, 39, 34], fill=BARK_DK, outline=INK)
    d.rectangle([27, 27, 29, 28], fill=VOID)
    d.rectangle([34, 27, 36, 28], fill=VOID)
    d.line([27, 31, 36, 31], fill=WHITE)                           # its bristling moustache
    d.point((26, 32), fill=WHITE)
    d.point((37, 32), fill=WHITE)
    d.polygon([(17, 22), (46, 22), (50, 29), (40, 27), (23, 27), (13, 29)], fill=LQ, outline=INK)
    d.line([16, 26, 22, 25], fill=RED)
    d.line([41, 25, 47, 26], fill=RED)
    d.pieslice([19, 9, 44, 35], 180, 360, fill=LQ, outline=INK)
    d.arc([21, 11, 42, 33], 200, 260, fill=LQ_HI)
    d.rectangle([19, 21, 44, 23], fill=GOLD, outline=GOLD_DK)
    for x in range(22, 44, 4):
        d.line([x, 12, x, 20], fill=LQ_HI if x < 30 else LQ_DK)
    # the horns and the disc between them
    for s in (-1, 1):
        cx = 31.5
        pts = [(cx + s * 4, 14), (cx + s * 11, 9), (cx + s * 15, 1)]
        d.line(pts, fill=GOLD_DK, width=3, joint='curve')
        d.line([(cx + s * 4, 13), (cx + s * 11, 8), (cx + s * 15, 1)], fill=GOLD_HI)
    d.ellipse([28, 7, 35, 14], fill=GOLD, outline=GOLD_DK)
    d.point((30, 9), fill=GOLD_HI)
    return im


def swords():
    """A rack of three swords: long, long, short."""
    im, d = new(2 * C, 2 * C)
    shadow(d, 4, 54, 59, 63, 70)
    for x in (10, 50):                                             # the rack's two ends
        d.polygon([(x - 4, 60), (x + 4, 60), (x + 2, 14), (x - 2, 14)], fill=LQ, outline=INK)
        d.line([x - 1, 16, x - 2, 58], fill=LQ_HI)
        d.rectangle([x - 6, 58, x + 6, 61], fill=LQ, outline=INK)
        d.rectangle([x - 1, 20, x + 1, 22], fill=GOLD)
    bar(d, 10, 50, 50, 53, LQ, LQ_HI, LQ_DK)
    for y, x0, x1, sheath, shine in ((22, 3, 60, LQ, LQ_HI), (33, 3, 60, RED_DK, RED), (44, 10, 52, INDIGO, INDIGO_HI)):
        d.line([x0 + 14, y, x1 - 8, y - 1, x1, y - 3], fill=INK, width=5, joint='curve')
        d.line([x0 + 14, y, x1 - 8, y - 1, x1, y - 3], fill=sheath, width=3, joint='curve')
        d.line([x0 + 16, y - 1, x1 - 10, y - 2], fill=shine)
        d.rectangle([x0, y - 2, x0 + 12, y + 1], fill=WHITE, outline=INK)                # the hilt, bound
        for x in range(x0 + 2, x0 + 12, 3):
            d.point((x, y - 1), fill=LQ)
            d.point((x + 1, y), fill=LQ)
        d.rectangle([x0 + 12, y - 4, x0 + 14, y + 3], fill=GOLD, outline=GOLD_DK)        # guard
        d.rectangle([x1 - 22, y - 2, x1 - 20, y + 1], fill=GOLD)                         # the cord's ring
        d.line([x1 - 21, y + 1, x1 - 24, y + 5], fill=PURPLE)
        d.line([x1 - 21, y + 1, x1 - 18, y + 5], fill=PURPLE)
    return im


def andon():
    """A standing paper lamp in a lacquer frame."""
    im, d = new(C, 2 * C)
    shadow(d, 5, 55, 26, 63, 80)
    for x in (9, 21):                                              # legs
        d.rectangle([x, 44, x + 1, 59], fill=LQ)
    d.line([8, 59, 23, 59], fill=LQ)
    d.line([9, 52, 22, 52], fill=LQ)
    box(d, 7, 14, 24, 45, LAMP)                                    # the paper box
    d.rectangle([8, 15, 23, 18], fill=LAMP_SH)
    d.rectangle([8, 41, 23, 44], fill=LAMP_SH)
    d.rectangle([14, 27, 17, 33], fill=LAMP_HI)                    # the flame behind the paper
    for x in (12, 19):
        d.line([x, 15, x, 44], fill=LQ)
    for y in (24, 35):
        d.line([8, y, 23, y], fill=LQ)
    d.rectangle([7, 14, 24, 45], outline=INK)
    box(d, 5, 10, 26, 14, LQ)                                      # the cap
    d.line([6, 11, 25, 11], fill=LQ_HI)
    d.rectangle([14, 6, 17, 10], fill=GOLD, outline=INK)
    box(d, 6, 45, 25, 48, LQ)
    d.line([7, 46, 24, 46], fill=GOLD)
    return im


def lamp_hang():
    """A gilt bronze lamp hung from the ceiling on a chain (Tops)."""
    im, d = new(C, 2 * C)
    for y in range(0, 14, 3):                                      # the chain
        d.rectangle([15, y, 16, y + 1], fill=GOLD_DK)
    d.polygon([(15, 12), (16, 12), (27, 22), (4, 22)], fill=LQ, outline=INK)        # the roof
    d.line([15, 14, 8, 21], fill=LQ_HI)
    for x in (4, 27):
        d.point((x, 21), fill=GOLD_HI)
        d.point((x, 20), fill=GOLD)
    d.rectangle([14, 10, 17, 12], fill=GOLD, outline=INK)
    box(d, 8, 23, 23, 42, LAMP)                                    # the lit cage
    d.rectangle([9, 24, 22, 26], fill=LAMP_SH)
    d.rectangle([9, 39, 22, 41], fill=LAMP_SH)
    d.rectangle([13, 30, 18, 35], fill=LAMP_HI)
    for x in (11, 15, 16, 20):
        d.line([x, 24, x, 41], fill=BARK_DK)
    for y in (28, 37):
        d.line([9, y, 22, y], fill=BARK_DK)
    d.rectangle([8, 23, 23, 42], outline=INK)
    box(d, 6, 42, 25, 45, GOLD)
    d.line([7, 43, 24, 43], fill=GOLD_HI)
    d.line([15, 46, 15, 50], fill=RED)                             # the tassel
    d.line([16, 46, 16, 50], fill=RED_DK)
    d.rectangle([13, 50, 18, 58], fill=RED, outline=RED_DK)
    d.line([15, 51, 15, 57], fill=RED_HI)
    d.rectangle([14, 49, 17, 50], fill=GOLD)
    return im


def guardpost():
    """The guard's post: a rack of polearms, and his lamp with the watch's mark."""
    im, d = new(3 * C, 2 * C)
    shadow(d, 2, 55, 93, 63, 70)
    # the polearms, their heads up: spear, glaive, man-catcher, spear, staff
    arms = ((12, 'yari'), (24, 'naginata'), (36, 'sasumata'), (48, 'yari'), (60, 'bo'))
    for x, kind in arms:
        d.rectangle([x, 10, x + 1, 58], fill=BARK)
        d.line([x, 10, x, 58], fill=BARK_HI)
        d.rectangle([x - 1, 30, x + 2, 32], fill=RED)             # a lacquered band
        if kind == 'yari':
            d.polygon([(x, 0), (x + 1, 0), (x + 3, 9), (x - 2, 9)], fill=STEEL, outline=INK)
            d.line([x, 2, x, 8], fill=STEEL_HI)
            d.rectangle([x - 2, 10, x + 3, 11], fill=GOLD)
        elif kind == 'naginata':
            d.polygon([(x + 1, 11), (x - 1, 11), (x - 1, 5), (x + 2, 0), (x + 5, 2), (x + 3, 6)], fill=STEEL, outline=INK)
            d.line([x, 9, x + 2, 3], fill=STEEL_HI)
            d.rectangle([x - 2, 11, x + 3, 12], fill=GOLD)
        elif kind == 'sasumata':
            d.arc([x - 6, 0, x + 7, 14], 0, 180, fill=INK, width=3)
            d.arc([x - 5, 0, x + 6, 13], 0, 180, fill=STEEL)
            for bx in range(x - 3, x + 6, 3):
                d.point((bx, 13), fill=STEEL_HI)
        else:
            d.rectangle([x - 1, 8, x + 2, 10], fill=LQ)
    # the rack: two rails on two feet
    bar(d, 4, 38, 68, 42, LQ, LQ_HI, LQ_DK)
    bar(d, 4, 52, 68, 56, LQ, LQ_HI, LQ_DK)
    for x in (4, 64):
        box(d, x, 36, x + 4, 60, LQ)
        d.line([x + 1, 37, x + 1, 59], fill=LQ_HI)
        d.rectangle([x - 2, 59, x + 6, 62], fill=LQ, outline=INK)
    # the lamp: a paper box on a post, marked for the watch
    d.rectangle([81, 44, 82, 60], fill=LQ)
    d.rectangle([76, 59, 87, 62], fill=LQ, outline=INK)
    box(d, 74, 18, 90, 44, LAMP)
    d.rectangle([75, 19, 89, 22], fill=LAMP_SH)
    d.rectangle([75, 40, 89, 43], fill=LAMP_SH)
    text(d, 77, 25, '番', kana(), RED_DK)
    d.rectangle([74, 18, 90, 44], outline=INK)
    box(d, 72, 14, 92, 18, LQ)
    d.line([73, 15, 91, 15], fill=LQ_HI)
    box(d, 73, 44, 91, 47, LQ)
    return im


def guestbook():
    """The visitors' book, open on a writing stand, a brush laid beside it."""
    im, d = new(C, 2 * C)
    shadow(d, 3, 55, 28, 63, 70)
    for x in (6, 23):                                              # legs
        d.rectangle([x, 40, x + 2, 59], fill=LQ)
        d.line([x, 40, x, 59], fill=LQ_HI)
    d.rectangle([4, 58, 27, 60], fill=LQ, outline=INK)
    d.line([7, 50, 24, 50], fill=LQ)
    d.polygon([(2, 40), (29, 40), (27, 24), (4, 24)], fill=RED_DK, outline=INK)      # the sloped top
    d.line([5, 25, 26, 25], fill=RED_HI)
    box(d, 2, 40, 29, 43, LQ)
    d.line([3, 41, 28, 41], fill=GOLD)
    d.polygon([(6, 38), (15, 38), (15, 27), (7, 27)], fill=WHITE, outline=PAPER_SH)  # the open book
    d.polygon([(16, 38), (25, 38), (24, 27), (16, 27)], fill=PAPER, outline=PAPER_SH)
    d.line([15, 27, 15, 38], fill=INK)
    for y in (29, 31, 33):                                         # names already in it
        d.line([8, y, 13, y], fill=STEEL_DK)
    d.line([17, 29, 22, 29], fill=STEEL_DK)
    d.line([17, 31, 20, 31], fill=STEEL_DK)
    d.line([26, 30, 21, 37], fill=BARK)                            # the brush
    d.point((21, 37), fill=LQ)
    d.point((20, 38), fill=LQ)
    d.rectangle([3, 15, 28, 22], fill=PAPER, outline=INK)          # what it is
    for x in range(6, 26, 4):                                      # (a line of brushed characters)
        d.rectangle([x, 17, x + 2, 20], fill=LQ)
        d.point((x + 1, 18), fill=PAPER)
    d.line([15, 22, 15, 24], fill=LQ)
    return im


def byobu():
    """A six-fold screen: red maples over a stream, on gold."""
    W = 3 * C
    im, d = new(W, 2 * C)
    shadow(d, 2, 55, W - 3, 63, 70)
    rnd = random.Random(2153)
    for i in range(6):                                             # the folds: each leaf leans the other way
        x0, x1 = 3 + i * 15, 3 + (i + 1) * 15
        up = 4 if i % 2 == 0 else 0
        top = [(x0, 8 - up + 4), (x1, 8 + up)] if i % 2 == 0 else [(x0, 8 + 4), (x1, 8)]
        ya, yb = (8, 12) if i % 2 == 0 else (12, 8)
        d.polygon([(x0, ya), (x1, yb), (x1, yb + 48), (x0, ya + 48)], fill=LEAF_B if i % 2 == 0 else LEAF_C)
        for _ in range(5):
            d.point((rnd.randrange(x0 + 1, x1), 14 + rnd.randrange(40)), fill=GOLD_HI)
        d.line([x0, ya, x1, yb], fill=LQ, width=2)
        d.line([x0, ya + 48, x1, yb + 48], fill=LQ, width=2)
        d.line([x0, ya, x0, ya + 48], fill=LQ if i == 0 else GOLD_DK)
    d.line([W - 3, 8, W - 3, 56], fill=LQ)
    d.line([3, 8, 3, 56], fill=LQ)
    # the stream, winding down the leaves
    pts = [(6, 40), (24, 44), (44, 40), (62, 47), (80, 44), (90, 49)]
    d.line(pts, fill=INDIGO, width=5, joint='curve')
    d.line([(x, y - 1) for x, y in pts], fill=INDIGO_HI)
    # two maples and their fallen leaves
    for tx, ty in ((22, 40), (66, 44)):
        d.line([tx, ty, tx - 2, ty - 14, tx + 3, ty - 22], fill=BARK_DK, width=2)
        d.line([tx - 2, ty - 14, tx - 9, ty - 19], fill=BARK_DK)
        for _ in range(26):
            lx, ly = tx - 12 + rnd.randrange(26), ty - 30 + rnd.randrange(16)
            d.rectangle([lx, ly, lx + 1, ly + 1], fill=MAPLE if rnd.random() < 0.6 else MAPLE_HI)
    for _ in range(9):
        lx, ly = 8 + rnd.randrange(80), 46 + rnd.randrange(8)
        d.point((lx, ly), fill=MAPLE)
    return im


def table():
    """A low lacquer table with tea set out."""
    im, d = new(2 * C, C)
    shadow(d, 4, 22, 59, 31, 70)
    for x in (8, 53):
        d.rectangle([x, 18, x + 2, 28], fill=LQ)
        d.line([x, 18, x, 28], fill=LQ_HI)
    d.polygon([(4, 18), (59, 18), (55, 7), (8, 7)], fill=RED_DK, outline=INK)
    d.line([9, 8, 54, 8], fill=RED_HI)
    box(d, 4, 18, 59, 21, LQ)
    d.line([5, 19, 58, 19], fill=GOLD)
    d.ellipse([25, 6, 37, 15], fill=BRONZE, outline=INK)           # the pot
    d.line([27, 8, 31, 7], fill=BRONZE_HI)
    d.arc([27, 0, 35, 10], 180, 360, fill=INK)
    d.line([37, 10, 41, 8], fill=INK)
    for x in (14, 44):                                             # cups
        d.rectangle([x, 10, x + 5, 14], fill=WHITE, outline=INK)
        d.line([x + 1, 11, x + 4, 11], fill=BAMBOO_HI)
    d.rectangle([48, 12, 55, 14], fill=PEONY, outline=INK)   # a sweet on a dish
    return im


def sprites():
    return {
        'palace-in-board-a': board(0), 'palace-in-board-b': board(15),
        'palace-in-board-h-a': board(0, True), 'palace-in-board-h-b': board(15, True),
        'palace-in-tatami-l': tatami('l'), 'palace-in-tatami-r': tatami('r'),
        'palace-in-zabuton': zabuton,
        'palace-in-side-w': wall_side('w'), 'palace-in-side-e': wall_side('e'),
        'palace-in-sun-w': sun('w'), 'palace-in-sun-e': sun('e'),
        'palace-in-wall-front': wall_front,
        'palace-in-threshold-w': threshold('w'), 'palace-in-threshold-e': threshold('e'),
        'palace-in-doorlight': doorlight,
        'palace-in-wall-shoji': wall_shoji, 'palace-in-wall-plain': wall_plain,
        'palace-in-alcove-shelves': alcove_shelves, 'palace-in-alcove-doors': alcove_doors,
        'palace-in-mural': mural,
        'palace-in-dais': dais,
        'palace-in-pillar': pillar,
        'palace-in-fusuma-tiger': fusuma_tiger, 'palace-in-fusuma-waves': fusuma_waves,
        'palace-in-armour': armour, 'palace-in-swords': swords,
        'palace-in-andon': andon, 'palace-in-lamp-hang': lamp_hang,
        'palace-in-guardpost': guardpost, 'palace-in-guestbook': guestbook,
        'palace-in-byobu': byobu, 'palace-in-table': table,
    }


# The hanging lamps are Tops under four rows tall: lifted in front of whatever
# taller thing stands behind them. The light through a door lies on the floor.
DEPTH_BIAS = {'palace-in-lamp-hang': 10, 'palace-in-doorlight': -40}


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
        if name in DEPTH_BIAS:
            cfg['spriteMetadata'][key]['depthBias'] = DEPTH_BIAS[name]
        cfg.setdefault('tileNames', {})[key] = name
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
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


if __name__ == '__main__':
    main()
