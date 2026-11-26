#!/usr/bin/env python3
"""generate_shrine_art.py — everything inside a shrine's worship hall (issue
#212). The GuttyKreum temple packs are exteriors only (roofs, torii, statues),
so the interior is drawn here; tools/extract_shrine.py cuts the one piece the
pack does have, the thin garland rope with its paper streamers
(shrine-in-rope).

Shaded pixel art with a 1px ink outline, drawn at half size (32px a cell) and
pixel-doubled like tools/generate_station_art.py. Nothing is line art. The
only text is set in the game's own fonts (fonts/PixelMplus12-Grid.ttf), so a
re-run is byte-identical on any machine.

Two looks, picked by the hall's roof (tools/generate_shrines.py):
  red   vermilion lacquer and gilt fittings on a warm, dark floor
  blue  bare cypress, white plaster and indigo cloth on a cool, dark floor

Per look (shrine-in-<piece>-<look>):
  floor-a / floor-b     polished floorboards, two joint patterns
  wall                  back wall, 1x2: beam, plaster bay, wainscot
  wall-curtain          the same bay hung with the shrine's curtain
  wall-shoji            the same bay with a lit paper screen
  wall-front, side-w/-e the front wall's top from inside; the side walls
  pillar                1x3 column: only its foot is solid, walk behind it
  honden                6x3 inner sanctuary: doors open on the mirror, on a
                        raised floor with its offering stands and steps
  lattice               1x2 railing piece in front of the sanctuary
  lanterns              1x2 hanging paper lantern (lit at night: DayNight
                        puts a halo on every *-lanterns* tile)
  runner-l / runner-r   the cloth runner from the door to the offering box
Shared (shrine-in-<piece>):
  tatami-l / tatami-r   the two halves of a mat
  saisen                2x2 offering box (bump it: src/ShrineVisit.js)
  bell                  2x2 bell and its rope, hung over the box (Tops)
  ema                   3x2 rack of wooden wishing plaques
  omikuji               2x2 fortune stand (bump it)
  omikuji-rail          2x2 rail of tied paper fortunes
  counter               3x2 the miko's counter, charms laid out on it
  sakaki                1x2 evergreen branch in a white vase
  lanterns-floor        1x2 standing paper lamp
  zabuton               floor cushion (Over Floor)
  drum                  2x2 taiko on its stand
  shimenawa             6x1 the thick straw rope over the sanctuary's front (Tops)
  doorlight             2x3 daylight falling in through the door (lies flat)
  threshold-w / -e      the doorway's two cells

Run from gamev2/:  python3 tools/generate_shrine_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import random
import sys

from PIL import Image, ImageDraw, ImageFont

C = 32      # canvas px per cell (doubled on save)

INK = (38, 43, 68)
VOID = (16, 18, 30)
WHITE, PAPER, PAPER_SH = (250, 250, 246), (240, 238, 226), (206, 208, 220)
STRAW, STRAW_HI, STRAW_DK = (214, 186, 120), (240, 220, 160), (164, 132, 82)
GOLD, GOLD_HI, GOLD_DK = (232, 184, 74), (252, 228, 138), (168, 118, 52)
WOOD, WOOD_HI, WOOD_DK = (176, 128, 84), (212, 168, 116), (124, 84, 62)
PALE, PALE_HI, PALE_DK = (222, 190, 138), (244, 222, 172), (170, 134, 96)
DARK, DARK_HI, DARK_DK = (92, 60, 52), (124, 84, 68), (62, 40, 42)
RED, RED_HI, RED_DK = (204, 62, 50), (236, 104, 72), (146, 40, 46)
GREEN, GREEN_HI, GREEN_DK = (62, 112, 74), (102, 152, 92), (40, 74, 62)
TATAMI, TATAMI_HI, TATAMI_DK = (176, 180, 112), (198, 202, 136), (146, 152, 96)
HERI = (50, 72, 66)
STONE, STONE_HI, STONE_DK = (150, 158, 178), (198, 203, 216), (104, 113, 140)
GLOW, GLOW_HI = (255, 214, 130), (255, 244, 200)
PURPLE, PURPLE_HI, PURPLE_DK = (116, 76, 148), (156, 116, 186), (80, 50, 108)

LOOKS = {
    'red': dict(
        floor=(88, 54, 46), floor_alt=(98, 62, 50), floor_hi=(132, 88, 66), floor_dk=(64, 40, 40),
        post=RED, post_hi=RED_HI, post_dk=RED_DK,
        trim=GOLD, trim_hi=GOLD_HI, trim_dk=GOLD_DK,
        plaster=(238, 226, 200), plaster_sh=(212, 196, 170),
        board=(104, 64, 52), board_hi=(136, 90, 68), board_dk=(72, 44, 42),
        cloth=PURPLE, cloth_hi=PURPLE_HI, cloth_dk=PURPLE_DK, crest=GOLD_HI,
        lamp=(226, 70, 54), lamp_hi=(255, 150, 96), lamp_dk=(160, 44, 48), lamp_mark=(60, 30, 40),
        deep=(40, 22, 34), deep_hi=(74, 36, 44),
    ),
    'blue': dict(
        floor=(70, 64, 78), floor_alt=(80, 72, 86), floor_hi=(112, 104, 122), floor_dk=(50, 46, 62),
        post=PALE, post_hi=PALE_HI, post_dk=PALE_DK,
        trim=(150, 158, 178), trim_hi=(214, 220, 232), trim_dk=(96, 104, 132),
        plaster=(236, 238, 240), plaster_sh=(204, 210, 222),
        board=(86, 78, 92), board_hi=(120, 110, 126), board_dk=(58, 52, 70),
        cloth=(54, 76, 136), cloth_hi=(92, 118, 178), cloth_dk=(36, 50, 96), crest=WHITE,
        lamp=(244, 240, 224), lamp_hi=(255, 250, 220), lamp_dk=(196, 190, 180), lamp_mark=(54, 76, 136),
        deep=(24, 28, 52), deep_hi=(44, 54, 92),
    ),
}

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


def text_size(d, s, f):
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    return r - l, b - t


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


# ---- floors -----------------------------------------------------------------------

def floor(look, shift):
    P = LOOKS[look]

    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=P['floor'])
        for i in range(4):                      # four boards a cell, running towards the sanctuary
            x0 = i * 8
            if i % 2:
                d.rectangle([x0, 0, x0 + 7, 31], fill=P['floor_alt'])
            d.line([x0, 0, x0, 31], fill=P['floor_dk'])
            joint = (shift + (10 if i % 2 == 0 else 26) + i * 3) % 32
            d.line([x0 + 1, joint, x0 + 7, joint], fill=P['floor_dk'])
            # the polish: a short streak of reflected light on each board
            y = (joint + 9 + i * 5) % 32
            for k in range(6):
                d.point((x0 + 3, (y + k) % 32), fill=P['floor_hi'])
            d.point((x0 + 5, (y + 13) % 32), fill=P['floor_hi'])
            d.point((x0 + 5, (y + 14) % 32), fill=P['floor_hi'])
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
        d.rectangle([0, 0, 31, 2], fill=HERI)   # the cloth border down both long edges
        d.rectangle([0, 29, 31, 31], fill=HERI)
        d.line([0, 1, 31, 1], fill=GREEN)
        d.line([0, 30, 31, 30], fill=GREEN)
        x = 0 if side == 'l' else 31            # the mat's end
        d.line([x, 3, x, 28], fill=TATAMI_DK)
        return im
    return draw


def zabuton():
    im, d = new(C, C)
    d.rounded_rectangle([5, 10, 26, 25], radius=3, fill=PURPLE, outline=INK)
    d.line([7, 11, 24, 11], fill=PURPLE_HI)
    d.line([6, 12, 6, 22], fill=PURPLE_HI)
    d.line([7, 24, 24, 24], fill=PURPLE_DK)
    d.line([25, 13, 25, 23], fill=PURPLE_DK)
    d.rectangle([15, 16, 16, 18], fill=GOLD)
    d.point((15, 19), fill=PURPLE_DK)
    d.point((16, 19), fill=PURPLE_DK)
    for x, y in ((5, 10), (26, 10), (5, 25), (26, 25)):      # corner tassels
        d.point((x, y), fill=GOLD)
    return im


# ---- walls ------------------------------------------------------------------------

def _wall_bay(P):
    """A 1x2 bay of the back wall: ceiling beam, plaster between posts, a tie
    rail, and a boarded wainscot down to the floor."""
    im, d = new(C, 2 * C)
    d.rectangle([0, 0, 31, 63], fill=P['plaster'])
    for y in range(9, 48, 2):                               # soft shade under the beam
        if y < 15:
            d.line([0, y, 31, y], fill=P['plaster_sh'])
    d.line([0, 9, 31, 9], fill=P['plaster_sh'])
    d.line([0, 10, 31, 10], fill=P['plaster_sh'])
    bar(d, -1, 0, 32, 8, P['post'], P['post_hi'], P['post_dk'])              # the beam
    for x in (7, 23):
        d.rectangle([x, 3, x + 1, 5], fill=P['trim'])                           # nail covers
        d.point((x, 3), fill=P['trim_hi'])
    bar(d, -1, 26, 32, 30, P['post'], P['post_hi'], P['post_dk'])            # tie rail
    d.rectangle([0, 46, 31, 63], fill=P['board'])                               # wainscot
    for x in range(0, 32, 8):
        d.line([x, 47, x, 60], fill=P['board_dk'])
        d.line([x + 1, 47, x + 1, 60], fill=P['board_hi'])
    d.line([0, 46, 31, 46], fill=INK)
    d.line([0, 47, 31, 47], fill=P['board_hi'])
    d.rectangle([0, 60, 31, 63], fill=P['board_dk'])
    d.line([0, 60, 31, 60], fill=INK)
    d.line([0, 63, 31, 63], fill=INK)
    post(d, 0, 9, 3, 59, P['post'], P['post_hi'], P['post_dk'], outline=False)  # the bay's post
    d.line([4, 9, 4, 59], fill=INK)
    return im, d


def wall(look):
    return lambda: _wall_bay(LOOKS[look])[0]


def wall_curtain(look):
    P = LOOKS[look]

    def draw():
        im, d = _wall_bay(P)
        # the shrine's curtain, hung from the beam on cords, scalloped along its foot
        d.rectangle([5, 10, 31, 40], fill=P['cloth'])
        d.rectangle([0, 10, 4, 40], fill=P['cloth'])
        d.rectangle([0, 10, 31, 13], fill=P['cloth_dk'])
        d.line([0, 10, 31, 10], fill=INK)
        for x in (3, 13, 23):                               # folds
            d.line([x, 14, x, 39], fill=P['cloth_dk'])
            d.line([x + 1, 14, x + 1, 39], fill=P['cloth_hi'])
        d.ellipse([11, 18, 21, 28], fill=P['crest'], outline=P['cloth_dk'])     # the crest
        d.ellipse([14, 21, 18, 25], fill=P['cloth'])
        d.point((16, 19), fill=P['cloth'])
        d.point((12, 25), fill=P['cloth'])
        d.point((20, 25), fill=P['cloth'])
        for x0 in (0, 16):                                  # scallops
            d.polygon([(x0, 40), (x0 + 15, 40), (x0 + 12, 44), (x0 + 3, 44)], fill=P['cloth'])
            d.line([x0 + 3, 44, x0 + 12, 44], fill=INK)
            d.line([x0, 41, x0 + 2, 44], fill=INK)
            d.line([x0 + 15, 41, x0 + 13, 44], fill=INK)
            d.line([x0 + 4, 43, x0 + 11, 43], fill=P['cloth_dk'])
        for x in (7, 15, 23, 31):                           # white cords to the beam
            d.line([x, 9, x, 12], fill=WHITE)
        return im
    return draw


def wall_shoji(look):
    P = LOOKS[look]

    def draw():
        im, d = _wall_bay(P)
        d.rectangle([6, 12, 30, 58], fill=GLOW_HI)          # a lit paper screen
        for y in range(12, 58):
            t = abs(y - 34) / 24
            d.line([7, y, 29, y], fill=mix(GLOW_HI, PAPER, min(1, t)))
        for x in (12, 18, 24):                              # the lattice
            d.line([x, 13, x, 46], fill=P['board'])
        for y in (20, 28, 36, 46):
            d.line([7, y, 29, y], fill=P['board'])
        d.rectangle([7, 47, 29, 57], fill=P['board'])       # the solid foot of the screen
        d.line([7, 48, 29, 48], fill=P['board_hi'])
        d.rectangle([6, 12, 30, 58], outline=INK)
        return im
    return draw


def wall_front(look):
    """The front wall from inside: all you see is its head; below it is dark."""
    P = LOOKS[look]

    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        bar(d, -1, 0, 32, 9, P['post'], P['post_hi'], P['post_dk'])
        d.rectangle([0, 10, 31, 16], fill=P['board_dk'])
        d.line([0, 16, 31, 16], fill=INK)
        for x in (7, 23):
            d.rectangle([x, 4, x + 1, 6], fill=P['trim'])
        return im
    return draw


def wall_side(look, side):
    P = LOOKS[look]

    def draw():
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=VOID)
        x0 = 22 if side == 'w' else 0                       # the wall's inner face
        d.rectangle([x0, 0, x0 + 9, 31], fill=P['board'])
        for y in (7, 23):
            d.line([x0, y, x0 + 9, y], fill=P['board_dk'])
        edge = x0 + 9 if side == 'w' else x0
        d.line([edge, 0, edge, 31], fill=INK)
        lit = x0 + 8 if side == 'w' else x0 + 1
        d.line([lit, 0, lit, 31], fill=P['board_hi'])
        far = x0 if side == 'w' else x0 + 9
        d.line([far, 0, far, 31], fill=INK)
        return im
    return draw


def threshold(look, side):
    """One of the doorway's two cells: the sill in daylight, its jamb outside."""
    P = LOOKS[look]

    def draw():
        im, d = new(C, C)
        for y in range(32):
            d.line([0, y, 31, y], fill=mix(GLOW_HI, WHITE, y / 31))
        for y in range(0, 6):
            d.line([0, y, 31, y], fill=mix(P['floor_hi'], GLOW_HI, y / 5))
        d.line([0, 6, 31, 6], fill=STONE_HI)
        d.line([0, 20, 31, 20], fill=(236, 226, 190))
        d.line([0, 21, 31, 21], fill=WHITE)
        d.line([16 if side == 'w' else 8, 7, 16 if side == 'w' else 8, 19], fill=(236, 226, 190))
        d.line([10 if side == 'w' else 22, 22, 10 if side == 'w' else 22, 31], fill=(240, 232, 204))
        x0 = 0 if side == 'w' else 26                       # the jamb
        post(d, x0, 0, x0 + 5, 31, P['post'], P['post_hi'], P['post_dk'])
        return im
    return draw


def doorlight():
    """Daylight falling in through the door: a soft fan on the floor. It lies
    flat (Non-Collidables with a negative depthBias, like the bridges)."""
    im = Image.new('RGBA', (2 * C, 3 * C), (0, 0, 0, 0))
    px = im.load()
    for y in range(96):
        t = y / 95                                          # 0 far from the door, 1 at it
        half = 12 + 19 * t
        for x in range(64):
            dx = abs(x - 31.5)
            if dx > half:
                continue
            a = (0.04 + 0.52 * t ** 1.6) * min(1.0, (half - dx) / 7)
            if (x + y) % 2 and a < 0.3:                     # dithered where it thins out
                a *= 0.6
            a = round(a * 16) / 16                          # stepped, so it stays pixel art
            if a > 0:
                px[x, y] = (255, 232, 170, int(a * 255))
    return im


def runner(look, side):
    """Half of the cloth runner laid from the door to the offering box."""
    P = LOOKS[look]

    def draw():
        im, d = new(C, C)
        x0, x1 = (6, 31) if side == 'l' else (0, 25)
        d.rectangle([x0, 0, x1, 31], fill=P['cloth'] if look == 'blue' else RED)
        body, dk, hi = (P['cloth'], P['cloth_dk'], P['cloth_hi']) if look == 'blue' else (RED, RED_DK, RED_HI)
        for y in range(0, 32, 8):                           # a woven diamond every half cell
            for x in range(x0 + 6, x1 - 4, 8):
                d.point((x, y + 2), fill=hi)
                d.point((x - 1, y + 3), fill=hi)
                d.point((x + 1, y + 3), fill=hi)
                d.point((x, y + 4), fill=hi)
                d.point((x + 4, y + 7), fill=dk)
        edge = x0 if side == 'l' else x1                    # the gilt border down the outer edge
        inner = 1 if side == 'l' else -1
        d.line([edge, 0, edge, 31], fill=INK)
        d.line([edge + inner, 0, edge + inner, 31], fill=P['trim'])
        d.line([edge + 2 * inner, 0, edge + 2 * inner, 31], fill=P['trim_hi'])
        d.line([edge + 3 * inner, 0, edge + 3 * inner, 31], fill=dk)
        return im
    return draw


# ---- timber -----------------------------------------------------------------------

def pillar(look):
    P = LOOKS[look]

    def draw():
        im, d = new(C, 3 * C)
        d.ellipse([5, 86, 26, 95], fill=STONE_DK, outline=INK)                 # plinth
        d.ellipse([6, 84, 25, 92], fill=STONE, outline=INK)
        d.line([9, 86, 20, 86], fill=STONE_HI)
        for x in range(9, 23):                                                 # the round shaft
            t = (x - 9) / 13
            col = P['post_hi'] if t < 0.22 else P['post'] if t < 0.68 else P['post_dk']
            d.line([x, 10, x, 87], fill=col)
        d.line([12, 12, 12, 84], fill=mix(P['post_hi'], WHITE, 0.35))        # the lacquer's shine
        d.line([8, 10, 8, 87], fill=INK)
        d.line([23, 10, 23, 87], fill=INK)
        d.line([9, 88, 22, 88], fill=INK)
        for y in (16, 78):                                                     # fitted bands
            d.rectangle([8, y, 23, y + 4], fill=P['trim'], outline=INK)
            d.line([9, y + 1, 13, y + 1], fill=P['trim_hi'])
            d.line([18, y + 3, 22, y + 3], fill=P['trim_dk'])
        bar(d, 3, 0, 28, 5, P['post'], P['post_hi'], P['post_dk'])             # bracket block
        bar(d, 6, 5, 25, 10, P['post'], P['post_hi'], P['post_dk'])
        d.rectangle([14, 2, 17, 3], fill=P['trim'])
        return im
    return draw


def lattice(look):
    """A piece of the railing in front of the sanctuary: you see through it."""
    P = LOOKS[look]

    def draw():
        im, d = new(C, 2 * C)
        for x in range(6, 32, 5):                                              # the bars
            d.rectangle([x, 30, x + 1, 56], fill=P['post'])
            d.line([x + 2, 30, x + 2, 56], fill=INK)
            d.line([x - 1, 30, x - 1, 56], fill=INK)
            d.point((x, 31), fill=P['post_hi'])
        bar(d, -1, 26, 32, 30, P['post'], P['post_hi'], P['post_dk'])          # rails
        bar(d, -1, 42, 32, 45, P['post'], P['post_hi'], P['post_dk'])
        bar(d, -1, 56, 32, 61, P['post'], P['post_hi'], P['post_dk'])
        post(d, 0, 22, 4, 62, P['post'], P['post_hi'], P['post_dk'])           # the post
        d.rectangle([0, 19, 4, 22], fill=P['trim'], outline=INK)               # its cap
        d.point((1, 20), fill=P['trim_hi'])
        d.line([0, 63, 31, 63], fill=(0, 0, 0, 70))
        return im
    return draw


# ---- the inner sanctuary ------------------------------------------------------------

def _sanbo(d, cx, y, load):
    """A small white-wood offering stand with something on it; (cx, y) is the
    middle of its foot."""
    box(d, cx - 4, y - 6, cx + 4, y, PALE, INK)
    d.line([cx - 3, y - 5, cx + 3, y - 5], fill=PALE_HI)
    d.rectangle([cx - 1, y - 3, cx + 1, y - 2], fill=DARK)                     # the cut-out
    box(d, cx - 6, y - 9, cx + 6, y - 6, PALE_HI, INK)
    if load == 'sake':                                                         # two white flasks
        for dx in (-3, 3):
            d.rectangle([cx + dx - 1, y - 15, cx + dx + 1, y - 10], fill=WHITE, outline=INK)
            d.point((cx + dx, y - 16), fill=INK)
            d.point((cx + dx, y - 13), fill=PAPER_SH)
    elif load == 'rice':                                                       # a mound of rice
        d.polygon([(cx - 4, y - 10), (cx, y - 15), (cx + 4, y - 10)], fill=WHITE, outline=INK)
        d.point((cx + 1, y - 12), fill=PAPER_SH)
    else:                                                                      # fruit
        for dx, col in ((-3, (236, 150, 60)), (3, (236, 150, 60)), (0, (224, 86, 60))):
            yy = y - 12 if dx else y - 15
            d.ellipse([cx + dx - 2, yy - 1, cx + dx + 2, yy + 3], fill=col, outline=INK)


def honden(look):
    P = LOOKS[look]

    def draw():
        W, H = 6 * C, 3 * C
        im, d = new(W, H)
        # the room behind the open doors, dark, lit from the mirror
        d.rectangle([4, 4, W - 5, 66], fill=P['deep'])
        for r in range(34, 6, -4):
            t = (34 - r) / 28
            d.ellipse([96 - r * 1.5, 34 - r * 0.8, 96 + r * 1.5, 34 + r * 0.8],
                      fill=mix(P['deep'], P['deep_hi'], t))
        # side bays: closed lattice doors on plaster
        for x0 in (10, 150):
            d.rectangle([x0, 14, x0 + 31, 62], fill=P['plaster_sh'])
            for x in range(x0 + 3, x0 + 31, 4):
                d.line([x, 14, x, 62], fill=P['post_dk'])
                d.line([x + 1, 14, x + 1, 62], fill=P['post'])
            for y in (24, 38, 52):
                d.line([x0, y, x0 + 31, y], fill=P['post_dk'])
            d.rectangle([x0, 14, x0 + 31, 62], outline=INK)
        # the open door leaves, folded back against the bays
        for x0, lit in ((44, P['trim_hi']), (136, P['trim'])):
            d.rectangle([x0, 14, x0 + 11, 62], fill=P['post'])
            d.rectangle([x0 + 2, 18, x0 + 9, 36], fill=P['post_dk'])
            d.rectangle([x0 + 2, 40, x0 + 9, 58], fill=P['post_dk'])
            d.rectangle([x0 + 3, 19, x0 + 8, 35], fill=mix(P['post'], P['post_dk'], 0.5))
            d.rectangle([x0 + 3, 41, x0 + 8, 57], fill=mix(P['post'], P['post_dk'], 0.5))
            for y in (16, 38, 60):
                d.point((x0 + 2, y), fill=lit)
                d.point((x0 + 9, y), fill=lit)
            d.rectangle([x0 + 5, 37, x0 + 6, 39], fill=P['trim'])
            d.rectangle([x0, 14, x0 + 11, 62], outline=INK)
        # the white inner curtain, tied back either side of the mirror
        for sx in (1, -1):
            x = 96 - sx * 38
            d.polygon([(x, 14), (x + sx * 14, 14), (x + sx * 3, 40), (x, 46)], fill=PAPER)
            d.line([x + sx * 14, 14, x + sx * 3, 40], fill=PAPER_SH)
            d.line([x + sx * 10, 14, x + sx * 2, 36], fill=PAPER_SH)
            d.line([x + sx * 3, 40, x, 46], fill=INK)
            d.rectangle([min(x, x + sx * 4), 38, max(x, x + sx * 4), 40], fill=P['cloth'])
        # the mirror on its carved stand
        for r, col in ((15, mix(P['deep_hi'], GLOW, 0.25)), (13, mix(P['deep_hi'], GLOW, 0.5))):
            d.ellipse([96 - r, 31 - r, 96 + r, 31 + r], fill=col)
        d.ellipse([86, 21, 106, 41], fill=GOLD, outline=INK)
        d.ellipse([88, 23, 104, 39], fill=(214, 228, 240), outline=GOLD_DK)
        d.pieslice([88, 23, 104, 39], 200, 300, fill=WHITE)
        d.line([92, 35, 100, 27], fill=WHITE)
        d.line([94, 37, 101, 30], fill=(236, 244, 250))
        d.polygon([(84, 50), (90, 41), (102, 41), (108, 50)], fill=DARK, outline=INK)   # the stand
        d.line([91, 43, 101, 43], fill=DARK_HI)
        d.arc([86, 40, 96, 50], 180, 270, fill=GOLD_DK)
        d.arc([96, 40, 106, 50], 270, 360, fill=GOLD_DK)
        box(d, 80, 50, 112, 54, P['post'], INK)
        d.line([81, 51, 111, 51], fill=P['post_hi'])
        # gohei: folded white paper wands either side of the stand
        for x in (70, 122):
            d.line([x, 30, x, 56], fill=PALE_DK)
            for i, y in enumerate(range(30, 46, 4)):
                dx = 3 if i % 2 else -3
                d.rectangle([min(x, x + dx), y, max(x, x + dx), y + 3], fill=WHITE, outline=PAPER_SH)
        # the bamboo blind rolled up under the lintel, with its tassels
        d.rectangle([40, 9, 151, 15], fill=(150, 168, 96))
        for x in range(42, 151, 3):
            d.point((x, 11), fill=(104, 124, 76))
            d.point((x + 1, 13), fill=(190, 204, 130))
        d.rectangle([40, 9, 151, 15], outline=INK)
        for x in (60, 96, 132):
            d.rectangle([x - 1, 15, x + 1, 22], fill=RED)
            d.point((x, 16), fill=RED_HI)
            d.rectangle([x - 2, 22, x + 2, 24], fill=GOLD)
        # frame: lintel, posts, and the sill the doors stand on
        bar(d, 2, 0, W - 3, 9, P['post'], P['post_hi'], P['post_dk'])
        for x in range(14, W - 10, 20):
            d.rectangle([x, 3, x + 3, 6], fill=P['trim'])
            d.point((x, 3), fill=P['trim_hi'])
            d.point((x + 3, 6), fill=P['trim_dk'])
        for x0 in (4, 38, 148, 182):
            post(d, x0, 9, x0 + 5, 62, P['post'], P['post_hi'], P['post_dk'])
            d.rectangle([x0, 30, x0 + 5, 33], fill=P['trim'], outline=INK)
        # the raised floor in front of the doors, its edge and its face
        d.rectangle([0, 62, W - 1, 76], fill=P['floor_hi'])
        for x in range(0, W, 12):
            d.line([x, 63, x, 75], fill=P['floor'])
        d.line([0, 63, W - 1, 63], fill=mix(P['floor_hi'], WHITE, 0.3))
        d.rectangle([0, 62, W - 1, 76], outline=INK)
        d.rectangle([0, 76, W - 1, 95], fill=P['board'])
        for x in range(8, W, 16):
            d.line([x, 77, x, 93], fill=P['board_dk'])
        d.line([0, 77, W - 1, 77], fill=P['board_hi'])
        d.rectangle([0, 76, W - 1, 95], outline=INK)
        for x in range(4, W, 16):
            d.rectangle([x, 84, x + 1, 85], fill=P['trim'])
        # the steps up, in the middle
        for i, (y0, y1) in enumerate(((74, 80), (80, 87), (87, 95))):
            x0, x1 = 74 - i * 2, 117 + i * 2
            d.rectangle([x0, y0, x1, y1], fill=mix(P['floor_hi'], P['floor'], i * 0.25), outline=INK)
            d.line([x0 + 1, y0 + 1, x1 - 1, y0 + 1], fill=mix(P['floor_hi'], WHITE, 0.25))
            d.line([x0 + 1, y1 - 1, x1 - 1, y1 - 1], fill=P['floor_dk'])
        # the offerings, set out on the raised floor
        _sanbo(d, 84, 73, 'sake')
        _sanbo(d, 96, 71, 'rice')
        _sanbo(d, 108, 73, 'fruit')
        for x in (24, 168):                                                    # paper lamps on the raised floor
            d.rectangle([x - 4, 50, x + 4, 66], fill=GLOW_HI, outline=INK)
            d.rectangle([x - 2, 53, x + 2, 63], fill=WHITE)
            d.line([x, 51, x, 65], fill=P['board'])
            d.line([x - 3, 58, x + 3, 58], fill=P['board'])
            d.rectangle([x - 5, 47, x + 5, 50], fill=P['board'], outline=INK)
            d.rectangle([x - 3, 66, x - 2, 71], fill=P['board'], outline=INK)
            d.rectangle([x + 2, 66, x + 3, 71], fill=P['board'], outline=INK)
        return im
    return draw


def sakaki():
    im, d = new(C, 2 * C)
    rnd = random.Random(7)
    d.line([16, 20, 16, 46], fill=WOOD_DK)                                    # the branch
    d.line([15, 28, 10, 20], fill=WOOD_DK)
    d.line([17, 30, 23, 22], fill=WOOD_DK)
    leaves = []
    for _ in range(46):
        x, y = rnd.randint(6, 25), rnd.randint(5, 36)
        if abs(x - 16) > 4 + (y - 4) * 0.35:
            continue
        leaves.append((x, y))
    for x, y in leaves:
        d.ellipse([x - 2, y - 1, x + 2, y + 2], fill=GREEN_DK)
    for x, y in leaves:
        d.ellipse([x - 2, y - 2, x + 1, y + 1], fill=GREEN)
        d.point((x - 1, y - 1), fill=GREEN_HI)
    outline_alpha(im)
    d = ImageDraw.Draw(im)
    for i, y in enumerate(range(30, 42, 4)):                                   # the paper streamer tied on
        dx = 2 if i % 2 else -2
        d.rectangle([14 + dx, y, 17 + dx, y + 3], fill=WHITE, outline=PAPER_SH)
    d.polygon([(11, 44), (21, 44), (23, 50), (21, 58), (11, 58), (9, 50)], fill=WHITE, outline=INK)   # the vase
    d.line([11, 46, 11, 56], fill=PAPER_SH)
    d.line([20, 47, 20, 55], fill=PAPER_SH)
    d.rectangle([13, 42, 19, 44], fill=WHITE, outline=INK)
    box(d, 7, 58, 25, 62, PALE, INK)                                           # its stand
    d.line([8, 59, 24, 59], fill=PALE_HI)
    return im


# ---- the worship hall ------------------------------------------------------------------

def saisen():
    """The offering box: slatted top, the dedication in gold on its face."""
    im, d = new(2 * C, 2 * C)
    d.ellipse([3, 56, 60, 63], fill=(0, 0, 0, 70))                             # its shadow on the floor
    d.polygon([(8, 24), (55, 24), (60, 38), (3, 38)], fill=WOOD_DK, outline=INK)   # the top, seen from above
    for i in range(7):                                                         # the slats the coins fall through
        xt, xb = 12 + i * 6, 8 + i * 7
        d.line([xt, 26, xb, 36], fill=WOOD_HI)
        d.line([xt + 1, 26, xb + 1, 36], fill=WOOD)
        d.line([xt + 3, 26, xb + 4, 36], fill=(36, 26, 34))
    d.line([8, 24, 55, 24], fill=INK)
    d.line([9, 25, 54, 25], fill=WOOD_HI)
    box(d, 3, 38, 60, 59, WOOD, INK)                                           # the face
    for x in (17, 31, 45):
        d.line([x, 40, x, 57], fill=WOOD_DK)
        d.line([x + 1, 40, x + 1, 57], fill=WOOD_HI)
    d.line([4, 39, 59, 39], fill=WOOD_HI)
    d.line([4, 58, 59, 58], fill=WOOD_DK)
    box(d, 18, 41, 45, 56, DARK, INK)                                          # the plate
    f = kana()
    w, h = text_size(d, '奉納', f)
    text(d, 32 - w // 2, 43, '奉納', f, GOLD_HI)
    for x in (5, 57):                                                          # iron corner straps
        d.rectangle([x, 40, x + 1, 57], fill=STONE_DK)
        d.point((x, 44), fill=STONE_HI)
        d.point((x, 53), fill=STONE_HI)
    box(d, 5, 59, 12, 62, WOOD_DK, INK)                                        # feet
    box(d, 51, 59, 58, 62, WOOD_DK, INK)
    return im


def bell():
    """The suzu bell and its thick braided rope, hung over the offering box."""
    im, d = new(2 * C, 2 * C)
    cx = 32
    d.rectangle([cx - 9, 0, cx + 9, 3], fill=DARK, outline=INK)                # its hanger on the beam
    d.rectangle([cx - 2, 3, cx + 1, 6], fill=RED, outline=INK)
    d.ellipse([cx - 9, 5, cx + 8, 22], fill=GOLD, outline=INK)                 # the bell
    d.ellipse([cx - 7, 7, cx - 1, 13], fill=GOLD_HI)
    d.point((cx - 5, 9), fill=WHITE)
    d.arc([cx - 8, 6, cx + 7, 21], 20, 110, fill=GOLD_DK)
    d.line([cx - 8, 15, cx + 7, 15], fill=GOLD_DK)                             # the seam and the slit
    d.line([cx - 4, 18, cx + 3, 18], fill=INK)
    d.point((cx - 5, 17), fill=INK)
    d.point((cx + 4, 17), fill=INK)
    # the rope: three strands, red, white and purple, wound round each other
    strands = (RED, WHITE, PURPLE)
    for y in range(22, 58):
        sway = round(1.5 * ((y - 22) / 36) ** 2)
        x0 = cx - 4 + sway
        for k in range(7):
            band = ((y + k) // 3) % 3
            col = strands[band]
            if k == 0:
                col = mix(col, WHITE, 0.35)
            elif k >= 5:
                col = mix(col, INK, 0.35)
            d.point((x0 + k, y), fill=col)
        d.point((x0 - 1, y), fill=INK)
        d.point((x0 + 7, y), fill=INK)
    x0 = cx - 4 + 2
    d.rectangle([x0 - 1, 54, x0 + 7, 58], fill=GOLD, outline=INK)             # the knot
    d.line([x0, 55, x0 + 3, 55], fill=GOLD_HI)
    for k in range(-1, 8, 2):                                                  # the tassel
        d.line([x0 + k, 59, x0 + k, 63], fill=RED if k % 4 == 3 else PURPLE)
        d.line([x0 + k + 1, 59, x0 + k + 1, 62], fill=WHITE if k % 4 == 3 else RED_HI)
    return im


def hanging_lantern(look):
    P = LOOKS[look]

    def draw():
        im, d = new(C, 2 * C)
        d.line([15, 0, 15, 12], fill=INK)                                      # the cord
        d.line([16, 0, 16, 12], fill=DARK)
        box(d, 10, 12, 21, 15, DARK, INK)                                      # top ring
        d.line([11, 13, 20, 13], fill=DARK_HI)
        for y in range(16, 46):                                                # the paper body
            t = (y - 16) / 29
            half = 7 + round(5 * (1 - (2 * t - 1) ** 2))
            for x in range(16 - half, 16 + half):
                u = (x - (16 - half)) / max(1, 2 * half - 1)
                glow = max(0.0, 1 - ((u - 0.4) ** 2 + (t - 0.45) ** 2) * 5)
                col = mix(P['lamp'], P['lamp_hi'], glow)
                if u > 0.82:
                    col = mix(col, P['lamp_dk'], 0.7)
                d.point((x, y), fill=col)
            d.point((16 - half - 1, y), fill=INK)
            d.point((16 + half, y), fill=INK)
            if y % 5 == 1:                                                     # the ribs
                d.line([16 - half + 1, y, 16 + half - 2, y], fill=mix(P['lamp'], P['lamp_dk'], 0.6))
        # the brushed mark on its face
        d.line([13, 24, 19, 24], fill=P['lamp_mark'])
        d.line([16, 22, 16, 36], fill=P['lamp_mark'])
        d.line([12, 30, 20, 30], fill=P['lamp_mark'])
        d.line([13, 36, 19, 36], fill=P['lamp_mark'])
        d.point((13, 33), fill=P['lamp_mark'])
        d.point((19, 33), fill=P['lamp_mark'])
        box(d, 10, 46, 21, 49, DARK, INK)                                      # bottom ring
        d.line([11, 47, 20, 47], fill=DARK_HI)
        d.line([15, 50, 15, 56], fill=RED)                                     # tassel
        d.line([16, 50, 16, 56], fill=RED_DK)
        d.rectangle([14, 56, 17, 59], fill=GOLD, outline=INK)
        return im
    return draw


def floor_lantern():
    """A standing paper lamp (andon): a lit paper box in a dark frame, on legs."""
    im, d = new(C, 2 * C)
    d.ellipse([6, 56, 25, 63], fill=(0, 0, 0, 70))
    for x in (9, 21):                                                          # legs
        d.rectangle([x, 20, x + 1, 60], fill=DARK, outline=INK)
    box(d, 8, 24, 23, 48, GLOW_HI, INK)                                        # the paper
    for y in range(25, 48):
        t = abs(y - 38) / 12
        d.line([9, y, 22, y], fill=mix(WHITE, GLOW, min(1, t * 0.9)))
    d.ellipse([13, 33, 18, 42], fill=WHITE)                                    # the flame behind it
    d.line([15, 25, 15, 47], fill=DARK)
    d.line([16, 25, 16, 47], fill=DARK_HI)
    d.line([9, 36, 22, 36], fill=DARK)
    box(d, 6, 20, 25, 24, DARK, INK)                                           # the cap
    d.line([7, 21, 24, 21], fill=DARK_HI)
    box(d, 7, 48, 24, 51, DARK, INK)
    d.line([8, 49, 23, 49], fill=DARK_HI)
    box(d, 12, 16, 19, 20, DARK, INK)
    return im


def ema():
    """A roofed rack hung thick with wooden wishing plaques."""
    im, d = new(3 * C, 2 * C)
    rnd = random.Random(212)
    d.ellipse([4, 57, 91, 63], fill=(0, 0, 0, 70))
    for x in (8, 84):                                                          # posts
        post(d, x, 12, x + 4, 60, DARK, DARK_HI, DARK_DK)
    box(d, 12, 16, 84, 52, (70, 48, 50), INK)                                  # the board behind
    bar(d, 6, 22, 90, 25, DARK, DARK_HI, DARK_DK)                              # the two rails
    bar(d, 6, 38, 90, 41, DARK, DARK_HI, DARK_DK)
    woods = ((226, 190, 132), (212, 172, 116), (238, 206, 150))
    for row, y0 in enumerate((24, 40)):
        x = 13
        while x < 80:
            w, col = 9, rnd.choice(woods)
            y = y0 + rnd.randint(0, 3)
            d.line([x + 4, y0, x + 4, y], fill=RED)                            # its cord
            d.polygon([(x, y + 3), (x + 4, y), (x + 8, y + 3), (x + 8, y + 10), (x, y + 10)],
                      fill=col, outline=INK)
            d.line([x + 1, y + 4, x + 7, y + 4], fill=mix(col, WHITE, 0.4))
            for k in range(2):                                                 # somebody's wish
                yy = y + 6 + k * 2
                d.line([x + 2, yy, x + 2 + rnd.randint(2, 4), yy], fill=mix(col, INK, 0.65))
            if rnd.random() < 0.3:
                d.point((x + 6, y + 6), fill=RED)
            x += rnd.randint(7, 9)
    # the little roof over it
    d.polygon([(2, 12), (10, 3), (86, 3), (94, 12)], fill=(74, 84, 110), outline=INK)
    for x in range(12, 86, 6):
        d.line([x, 4, x - 3 + (x - 48) // 10, 11], fill=(52, 60, 86))
    d.line([10, 4, 86, 4], fill=(120, 132, 160))
    bar(d, 2, 11, 94, 14, DARK, DARK_HI, DARK_DK)
    box(d, 5, 58, 16, 62, DARK_DK, INK)
    box(d, 80, 58, 91, 62, DARK_DK, INK)
    return im


def omikuji():
    """The fortune stand: a signboard, the six-sided shaker, and the drawers
    the numbered slips are kept in."""
    im, d = new(2 * C, 2 * C)
    d.ellipse([3, 57, 60, 63], fill=(0, 0, 0, 70))
    f = kana()
    box(d, 6, 1, 57, 17, RED, INK)                                             # the signboard
    d.rectangle([7, 2, 56, 3], fill=RED_HI)
    d.rectangle([7, 15, 56, 16], fill=RED_DK)
    w, _ = text_size(d, 'おみくじ', f)
    text(d, 32 - w // 2, 4, 'おみくじ', f, WHITE)
    for x in (9, 53):
        d.rectangle([x, 17, x + 1, 30], fill=DARK, outline=INK)
    box(d, 3, 30, 60, 36, PALE_HI, INK)                                        # the table top
    d.line([4, 31, 59, 31], fill=WHITE)
    box(d, 5, 36, 58, 60, RED, INK)                                            # its cloth
    d.line([6, 37, 57, 37], fill=RED_HI)
    for x in (18, 32, 46):
        d.line([x, 38, x, 59], fill=RED_DK)
    d.rectangle([5, 56, 58, 58], fill=GOLD)
    d.line([5, 59, 58, 59], fill=GOLD_DK)
    # the shaker: a six-sided wooden tube with a hole in its end
    d.polygon([(11, 20), (15, 18), (23, 18), (27, 20), (27, 31), (23, 33), (15, 33), (11, 31)],
              fill=WOOD, outline=INK)
    d.line([15, 19, 15, 32], fill=WOOD_HI)
    d.line([23, 19, 23, 32], fill=WOOD_DK)
    d.rectangle([17, 22, 21, 29], fill=PAPER, outline=WOOD_DK)
    d.line([19, 23, 19, 28], fill=RED)
    d.ellipse([17, 16, 21, 19], fill=INK)
    d.line([19, 12, 21, 17], fill=PALE_HI)                                     # a stick on its way out
    # the chest of numbered drawers
    box(d, 33, 19, 56, 33, PALE, INK)
    for r in range(3):
        for c in range(4):
            x, y = 35 + c * 5, 21 + r * 4
            d.rectangle([x, y, x + 3, y + 2], fill=PALE_HI, outline=PALE_DK)
            d.point((x + 2, y + 1), fill=DARK)
    return im


def omikuji_rail():
    """Paper fortunes tied to the lines of a rail: leave the bad luck behind."""
    im, d = new(2 * C, 2 * C)
    rnd = random.Random(1212)
    d.ellipse([2, 57, 61, 63], fill=(0, 0, 0, 70))
    for x in (4, 56):
        post(d, x, 8, x + 3, 61, RED, RED_HI, RED_DK)
        d.rectangle([x - 1, 5, x + 4, 8], fill=DARK, outline=INK)
    for y in (16, 28, 40):
        d.line([8, y, 55, y], fill=STRAW_DK)
        d.line([8, y + 1, 55, y + 1], fill=INK)
        x = 9 + rnd.randint(0, 2)
        while x < 53:
            tilt = rnd.choice((-1, 0, 1))
            d.rectangle([x, y - 2, x + 2, y + 2], fill=WHITE, outline=PAPER_SH)   # the knot
            d.line([x + 1, y + 3, x + 1 + tilt, y + 7], fill=WHITE)             # the two ends
            d.line([x + 2, y + 3, x + 2 + tilt, y + 6], fill=PAPER_SH)
            d.point((x + 1, y), fill=PAPER_SH)
            x += rnd.randint(3, 5)
    bar(d, 2, 52, 61, 55, RED, RED_HI, RED_DK)
    return im


def counter():
    """The miko's counter: charms laid out in trays, and the miko behind it."""
    im, d = new(3 * C, 2 * C)
    d.ellipse([2, 57, 93, 63], fill=(0, 0, 0, 70))
    # the back of the booth
    box(d, 4, 2, 91, 30, (232, 222, 200), INK)
    bar(d, 2, 0, 93, 5, DARK, DARK_HI, DARK_DK)
    for x in (4, 87):
        post(d, x, 5, x + 4, 30, DARK, DARK_HI, DARK_DK)
    # a short curtain along the head of the booth
    for i, x in enumerate(range(10, 86, 19)):
        d.rectangle([x, 6, x + 17, 13], fill=WHITE, outline=INK)
        d.ellipse([x + 6, 7, x + 11, 12], fill=RED)
    # the miko: black hair tied back, white robe, red collar
    d.rectangle([40, 12, 55, 30], fill=WHITE, outline=INK)                     # shoulders
    d.polygon([(44, 18), (48, 24), (52, 18)], fill=RED)
    d.line([43, 20, 43, 29], fill=PAPER_SH)
    d.line([53, 20, 53, 29], fill=PAPER_SH)
    d.rectangle([42, 8, 53, 19], fill=(40, 34, 48), outline=INK)               # hair
    d.rectangle([44, 11, 51, 18], fill=(246, 214, 186))                        # face
    d.rectangle([44, 10, 51, 11], fill=(40, 34, 48))
    d.point((46, 14), fill=INK)
    d.point((49, 14), fill=INK)
    d.line([47, 17, 48, 17], fill=(204, 110, 100))
    d.rectangle([54, 13, 55, 22], fill=(40, 34, 48))
    d.point((54, 12), fill=RED)
    # shelves of boxed charms behind her
    for x0 in (11, 62):
        for r, y in enumerate((16, 23)):
            box(d, x0, y, x0 + 22, y + 5, PALE_HI, PALE_DK)
            for c in range(4):
                col = (RED, GOLD, PURPLE, GREEN, (72, 116, 196))[(c + r * 2 + x0) % 5]
                d.rectangle([x0 + 2 + c * 5, y + 1, x0 + 4 + c * 5, y + 4], fill=col)
    # the counter: pale top, boarded front
    box(d, 1, 30, 94, 40, PALE_HI, INK)
    d.line([2, 31, 93, 31], fill=WHITE)
    d.line([2, 39, 93, 39], fill=PALE_DK)
    box(d, 3, 40, 92, 60, PALE, INK)
    for x in range(14, 92, 13):
        d.line([x, 41, x, 59], fill=PALE_DK)
        d.line([x + 1, 41, x + 1, 59], fill=PALE_HI)
    d.rectangle([3, 57, 92, 59], fill=PALE_DK)
    # trays of charms on the counter top
    cols = (RED, GOLD, PURPLE, GREEN, (72, 116, 196), WHITE)
    for i, x0 in enumerate((6, 28, 62)):
        box(d, x0, 32, x0 + 18, 38, DARK, INK)
        for c in range(4):
            col = cols[(c + i) % len(cols)]
            d.rectangle([x0 + 2 + c * 4, 33, x0 + 4 + c * 4, 37], fill=col)
            d.point((x0 + 3 + c * 4, 33), fill=WHITE)
    box(d, 50, 32, 58, 38, WHITE, INK)                                         # a stack of slips
    d.line([52, 34, 56, 34], fill=PAPER_SH)
    d.line([52, 36, 56, 36], fill=PAPER_SH)
    f = kana()
    box(d, 30, 43, 65, 57, WHITE, INK)                                         # what the counter is
    w, _ = text_size(d, 'お守り', f)
    text(d, 48 - w // 2, 44, 'お守り', f, RED_DK)
    return im


def drum():
    """A taiko on its stand, the head towards you."""
    im, d = new(2 * C, 2 * C)
    d.ellipse([6, 56, 57, 63], fill=(0, 0, 0, 70))
    for x0, x1 in ((12, 22), (51, 41)):                                        # the stand's legs
        d.line([x0, 61, x1, 30], fill=INK, width=5)
        d.line([x0, 61, x1, 30], fill=DARK, width=3)
    bar(d, 10, 50, 53, 54, DARK, DARK_HI, DARK_DK)
    d.ellipse([8, 2, 55, 49], fill=(150, 60, 48), outline=INK)                 # the body's rim
    d.ellipse([11, 5, 52, 46], fill=(120, 44, 44))
    for i in range(16):                                                        # the studs that pin the head
        import math
        a = i * math.pi / 8
        x, y = 31.5 + 21.5 * math.cos(a), 25.5 + 21.5 * math.sin(a)
        d.rectangle([round(x) - 1, round(y) - 1, round(x), round(y)], fill=GOLD)
    d.ellipse([14, 8, 49, 43], fill=(240, 228, 196), outline=INK)             # the head
    d.ellipse([16, 10, 40, 34], fill=(250, 242, 216))
    d.arc([15, 9, 48, 42], 20, 120, fill=(206, 190, 160))
    # the three-comma crest
    import math
    for k in range(3):
        a = k * 2 * math.pi / 3 - math.pi / 2
        x, y = 31.5 + 6 * math.cos(a), 25.5 + 6 * math.sin(a)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=INK)
        tx, ty = 31.5 + 9 * math.cos(a + 1.1), 25.5 + 9 * math.sin(a + 1.1)
        d.line([x, y, tx, ty], fill=INK, width=2)
    return im


def shimenawa():
    """The sacred rope across the sanctuary's front: twisted rice straw, thick
    in the middle, with folded paper streamers and straw tassels hung from it."""
    W = 6 * C
    im, d = new(W, C)
    mid = lambda x: 8 + 7 * (1 - ((x - (W - 1) / 2) / (W / 2)) ** 2)           # it sags
    thick = lambda x: 2.2 + 3.2 * (1 - abs((x - (W - 1) / 2) / (W / 2)) ** 1.5)
    for x in range(3, W - 3):
        c, t = mid(x), thick(x)
        y0, y1 = round(c - t), round(c + t)
        for y in range(y0, y1 + 1):
            u = (y - y0) / max(1, y1 - y0)
            twist = ((x + (y - y0) * 2) // 4) % 2                              # the lay of the strands
            col = STRAW_HI if u < 0.3 else STRAW if u < 0.7 else STRAW_DK
            if twist and 0.15 < u < 0.9:
                col = mix(col, STRAW_DK, 0.55)
            d.point((x, y), fill=col)
    outline_alpha(im)
    d = ImageDraw.Draw(im)
    for x in (30, 74, 117, 161):                                               # shide: folded paper
        y = round(mid(x) + thick(x)) + 1
        for i in range(4):
            dx = (0, 3, 0, 3)[i]
            d.rectangle([x + dx - 2, y + i * 4, x + dx + 2, y + i * 4 + 4], fill=WHITE, outline=PAPER_SH)
        d.line([x - 2, y, x + 2, y], fill=INK)
    for x in (52, 139):                                                        # straw tassels
        y = round(mid(x) + thick(x)) + 1
        for k in (-3, -1, 1, 3):
            d.line([x, y, x + k, y + 9], fill=STRAW_DK if k in (-3, 3) else STRAW)
        d.rectangle([x - 1, y, x + 1, y + 2], fill=STRAW_HI, outline=INK)
    return im


def sprites():
    out = {}
    for look in LOOKS:
        out[f'shrine-in-floor-a-{look}'] = floor(look, 0)
        out[f'shrine-in-floor-b-{look}'] = floor(look, 15)
        out[f'shrine-in-wall-{look}'] = wall(look)
        out[f'shrine-in-wall-curtain-{look}'] = wall_curtain(look)
        out[f'shrine-in-wall-shoji-{look}'] = wall_shoji(look)
        out[f'shrine-in-wall-front-{look}'] = wall_front(look)
        out[f'shrine-in-side-w-{look}'] = wall_side(look, 'w')
        out[f'shrine-in-side-e-{look}'] = wall_side(look, 'e')
        out[f'shrine-in-threshold-w-{look}'] = threshold(look, 'w')
        out[f'shrine-in-threshold-e-{look}'] = threshold(look, 'e')
        out[f'shrine-in-pillar-{look}'] = pillar(look)
        out[f'shrine-in-honden-{look}'] = honden(look)
        out[f'shrine-in-lattice-{look}'] = lattice(look)
        out[f'shrine-in-lanterns-{look}'] = hanging_lantern(look)
        out[f'shrine-in-runner-l-{look}'] = runner(look, 'l')
        out[f'shrine-in-runner-r-{look}'] = runner(look, 'r')
    out.update({
        'shrine-in-tatami-l': tatami('l'),
        'shrine-in-tatami-r': tatami('r'),
        'shrine-in-zabuton': zabuton,
        'shrine-in-doorlight': doorlight,
        'shrine-in-saisen': saisen,
        'shrine-in-bell': bell,
        'shrine-in-ema': ema,
        'shrine-in-omikuji': omikuji,
        'shrine-in-omikuji-rail': omikuji_rail,
        'shrine-in-counter': counter,
        'shrine-in-sakaki': sakaki,
        'shrine-in-lanterns-floor': floor_lantern,
        'shrine-in-drum': drum,
        'shrine-in-shimenawa': shimenawa,
    })
    return out


# Two Tops pieces hang in front of a taller piece that stands behind them, and
# Tops sort by their own foot row: the rope over the sanctuary's lintel, and
# the bell rope that comes down in front of the offering box.
DEPTH_BIAS = {'shrine-in-shimenawa': 20, 'shrine-in-bell': 10, 'shrine-in-doorlight': -40}


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
        rows, x, y, rowh, width = [], 16, 16, 0, 1500
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
