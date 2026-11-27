#!/usr/bin/env python3
"""generate_tower_deck_art.py — Fukuoka Tower's observation deck, and the view
the lift shows on the way up to it (issue #242).

In the manner of tools/generate_pub_art.py, whose frame (the side walls, the
front wall, the light through a door), drawing helpers and register() it
imports: shaded pixel art with a 1px ink outline, drawn at half size (32px a
cell) and pixel-doubled. Nothing is random between runs (every scatter is
seeded) and nothing is lettered, so a re-run is identical on any machine.

ONE VIEW, DRAWN ONCE. The panorama north from the tower is three canvases as
wide as the deck's wall (576px as drawn, 18 cells):
  near     the tower's plaza at the bottom, then the road, Seaside Momochi's
           park, the promenade and the beach, Marizon on its pier, and the
           town either side of the bay. Transparent above its skyline.
  far      Hakata Bay, the islands, the horizon and the day sky in flat bands.
           Opaque.
  lights   the lit pixels of `near` and nothing else: windows, lamps, cars.
The lift's ride (src/ViewRide.js) pans `near` and `far` behind its window as
you rise, each bottom-aligned at the ground and top-aligned at the top, tints
both with the hour's grade (DayNight.GRADES) and draws `lights` over `near`
when that grade has lights. The deck's six panes are the same canvases as the
lift shows them at the top (PANE_BAND: the rows that hold the horizon), so
what you rode up to is what the windows show. The room is `daylight`, graded
by the hour as the street is: the panes are drawn by day, once.

Pictures for the ride (whole images, centred, no tile name; saved pixel-doubled):
  view-lift               640x640 the glass lift from inside: steel walls, the
                          counter's dark panel over the window, the cabin floor
                          (the window is a hole: ViewRide.RIDES.lift.window)
  view-fukuoka-near / -far / -lights
                          the middle 384 columns of the three canvases (the
                          lift comes up in the middle of the deck)

Sprites, all `deck-in-<piece>`:
  floor-a / floor-b       dark carpet tiles
  side-w / side-e         the side walls seen along their length
  wall-front              the front wall's head from inside
  lift-w / lift-e         the lift's sill, the doorway's two cells; doorlight:
                          the cabin's light on the carpet (2x3, flat)
  window-1 .. window-6    3x5 a pane of the back wall, floor to ceiling (bump one)
  binoculars              1x2 a coin-operated viewer on its post (bump it)
  compass                 2x1 a plinth with a brass map of what is where (bump it)
  locks                   2x2 the fence the padlocks are left on (bump it)
  bench                   2x1 a bench to look out from
  lift-sign               1x2 the sign by the lift (bump it)
  downlight               1x2 a pendant lamp, over your head

The helpers at the top (sky, water, block, tree, lamp, car, cut, picture,
register_pictures) are plain functions: tools/generate_wheel_art.py draws the
view from the Dotonbori wheel with them.

Run from gamev2/:  python3 tools/generate_tower_deck_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames,
the pictures in spriteMetadata alone.
"""
import json
import math
import random
import sys

from PIL import Image

from generate_pub_art import (
    C, INK, VOID, WHITE, BRASS, BRASS_HI, BRASS_DK, STEEL, STEEL_HI, STEEL_DK, BLACK, GLOW, GLOW_HI,
    new, box, mix, bar, post, shadow, wall_side, wall_front, doorlight, register,
)

# ---- the palette of a view ------------------------------------------------------------------
SKY = [(96, 150, 232), (112, 168, 242), (129, 184, 248), (150, 198, 250), (174, 212, 251), (198, 226, 252), (220, 237, 252)]
HAZE = (206, 226, 246)                                             # what distance fades to
SEA_FAR, SEA, SEA_DEEP, GLINT = (142, 190, 240), (98, 146, 226), (66, 104, 190), (214, 236, 255)
SAND, SAND_HI, SAND_DK, WET, SURF = (232, 214, 170), (244, 232, 196), (206, 186, 140), (186, 172, 142), (246, 250, 254)
GRASS, GRASS_HI, GRASS_DK = (103, 142, 87), (137, 175, 120), (72, 108, 76)
PAVE, PAVE_HI, PAVE_DK = (176, 180, 216), (202, 206, 234), (146, 150, 190)
ROAD, ROAD_DK, LINE = (78, 80, 104), (58, 60, 82), (232, 232, 238)
GLASS, GLASS_HI, GLASS_DK = (75, 99, 150), (125, 185, 250), (44, 45, 81)
WALLS = [(188, 199, 204), (214, 208, 196), (160, 164, 184), (198, 170, 113), (224, 196, 170), (150, 160, 150), (201, 120, 100)]
RED, RED_HI, RED_DK = (209, 107, 86), (246, 165, 131), (150, 70, 70)
LIT, LIT_HI, LIT_COOL, LIT_RED = (255, 206, 110), (255, 240, 190), (214, 232, 255), (244, 96, 84)

# what the night's grade multiplies the street by (src/DayNight.js GRADES.night): only for the
# preview sheet's night frames, which show what ViewRide will draw. The game reads its own.
NIGHT = (0x74, 0x80, 0xc0)


# ---- helpers a view is drawn with -----------------------------------------------------------

def sky(d, w, y0, y1, bands=SKY):
    """The day sky from row y0 down to y1 (the horizon): flat bands, the last the palest,
    each a little shallower than the one above it."""
    n = len(bands)
    weights = [n - i * 0.6 for i in range(n)]
    total, y = sum(weights), float(y0)
    for band, wt in zip(bands, weights):
        nxt = y + (y1 - y0 + 1) * wt / total
        d.rectangle([0, round(y), w - 1, max(round(y), round(nxt) - 1)], fill=band)
        y = nxt
    d.rectangle([0, round(y) - 1, w - 1, y1], fill=bands[-1])


def cloud(d, x, y, w, fill=WHITE, under=(226, 236, 248)):
    """A flat-bottomed cloud `w` long with its foot on row y."""
    h = max(3, w // 6)
    d.rectangle([x, y - 1, x + w - 1, y], fill=under)
    for i, (a, b, up) in enumerate(((0.08, 0.92, 1), (0.2, 0.55, 2), (0.48, 0.84, 2), (0.3, 0.7, 3))):
        top = y - 1 - round(h * up / 3)
        d.rectangle([x + round(w * a), top, x + round(w * b), y - 2], fill=fill)


def water(d, rnd, w, y0, y1, far=SEA_FAR, near=SEA_DEEP, glints=0.012, x0=0):
    """Open water from the horizon (row y0, pale) down to row y1 (deep): bands, and
    short glints of light that get longer and fewer as the water gets nearer."""
    bands = 9
    for i in range(bands):
        a, b = y0 + (y1 - y0 + 1) * (i / bands) ** 1.6, y0 + (y1 - y0 + 1) * ((i + 1) / bands) ** 1.6
        d.rectangle([x0, round(a), x0 + w - 1, max(round(a), round(b) - 1)], fill=mix(far, near, (i / (bands - 1)) ** 0.8))
    for y in range(y0 + 1, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        for x in range(x0, x0 + w):
            if rnd.random() < glints * (1 - 0.6 * t):
                d.line([x, y, x + 1 + round(t * 5), y], fill=mix(GLINT, far, 0.35 * (1 - t)))


def block(d, dl, rnd, x, foot, w, h, wall, roof=3, pitch=(4, 4), pane=(2, 2), lit=0.45, haze=0.0, ink=True,
          glass=GLASS, lamps=(LIT, LIT, LIT_HI, LIT_COOL)):
    """A building as the town's maps draw one: its front `w` x `h` standing on row
    `foot`, its roof `roof` rows deep above that. Windows every `pitch`, each `pane`
    big; `lit` of them are also drawn on `dl`, the lights picture (None: no lights).
    `haze` fades it into the distance. Returns the row of its roof's top."""
    wall, glass = mix(wall, HAZE, haze), mix(glass, HAZE, haze)
    hi, dk, edge = mix(wall, WHITE, 0.4), mix(wall, INK, 0.3), mix(INK, HAZE, haze)
    top = foot - h + 1
    d.rectangle([x, top - roof, x + w - 1, top - 1], fill=hi)
    d.rectangle([x, top, x + w - 1, foot], fill=wall)
    d.line([x, top, x + w - 1, top], fill=mix(wall, WHITE, 0.2))
    d.line([x + w - 1, top, x + w - 1, foot], fill=dk)
    if roof >= 5:                                                    # plant on a roof you look down on
        d.rectangle([x + 2, top - roof + 1, x + 2 + max(2, w // 5), top - roof + 2], fill=dk)
        d.rectangle([x + w - 4 - w // 6, top - 3, x + w - 3, top - 2], fill=mix(wall, INK, 0.15))
    if ink:
        d.rectangle([x, top - roof, x + w - 1, foot], outline=edge)
        d.line([x, top - 1, x + w - 1, top - 1], fill=mix(edge, wall, 0.5))
    px, py = pitch
    pw, ph = pane
    cols = max(1, (w - 3) // px)
    left = x + (w - (cols * px - (px - pw))) // 2
    for wy in range(top + 2, foot - ph, py):
        for i in range(cols):
            wx = left + i * px
            d.rectangle([wx, wy, wx + pw - 1, wy + ph - 1], fill=glass)
            if dl is not None and rnd.random() < lit:
                dl.rectangle([wx, wy, wx + pw - 1, wy + ph - 1], fill=rnd.choice(lamps))
    return top - roof


def tree(d, x, foot, r, leaf=GRASS, ink=True):
    """A round tree with its trunk's foot on (x, foot), `r` the radius of its crown."""
    hi, dk = mix(leaf, WHITE, 0.3), mix(leaf, INK, 0.35)
    cy = foot - r - max(1, r // 3)
    if r >= 4:
        d.ellipse([x - r + 1, foot - 1, x + r - 1, foot + max(1, r // 3)], fill=mix(dk, INK, 0.2))   # its shade
        d.rectangle([x - max(0, r // 6), cy, x + max(0, r // 6), foot], fill=(110, 82, 70))
    d.ellipse([x - r, cy - r, x + r, cy + r], fill=leaf, outline=mix(INK, leaf, 0.0 if ink else 0.6))
    d.ellipse([x - r + 2, cy - r + 2, x + r - 3, cy + r - 3], fill=leaf)
    d.chord([x - r + 1, cy - r + 1, x + r - 1, cy + r - 1], 20, 150, fill=dk)
    d.ellipse([x - r + 2, cy - r + 1, x + r - 2, cy + r - 3], fill=leaf)
    if r >= 3:
        d.ellipse([x - r // 2 - 1, cy - r + 2, x, cy - r // 3], fill=hi)


def palm(d, x, foot, h):
    """A palm `h` tall: a leaning trunk and a star of fronds."""
    lean = 1 if h < 12 else 2
    d.line([x, foot, x + lean, foot - h], fill=(142, 112, 86), width=1 if h < 14 else 2)
    cx, cy, f = x + lean, foot - h, max(3, h // 3)
    for ang in (200, 235, 270, 305, 340, 165, 15):
        ex, ey = cx + round(f * math.cos(math.radians(ang))), cy + round(f * 0.7 * math.sin(math.radians(ang))) + (1 if ang in (165, 15) else 0)
        d.line([cx, cy, ex, ey], fill=GRASS_DK)
        d.point((ex, ey + 1), fill=GRASS)
    d.point((cx, cy), fill=GRASS_HI)


def lamp(d, dl, x, foot, h, glow=LIT_HI):
    """A street lamp `h` tall; on `dl` its head is lit, with a small halo."""
    d.line([x, foot, x, foot - h], fill=STEEL_DK)
    d.rectangle([x - 1, foot - h - 1, x + 1, foot - h], fill=STEEL_HI, outline=None)
    if h >= 12:
        d.rectangle([x - 2, foot - h - 3, x + 2, foot - h], fill=STEEL_HI, outline=INK)
        d.point((x, foot), fill=INK)
    if dl is not None:
        r = 1 if h < 12 else 2
        dl.rectangle([x - r, foot - h - r - 1, x + r, foot - h], fill=glow)
        for dx, dy, a in ((0, -r - 2, 110), (0, 1, 150), (-r - 1, -1, 110), (r + 1, -1, 110), (0, 2, 90), (0, 3, 50)):
            dl.point((x + dx, foot - h + dy), fill=glow + (a,))


def car(d, dl, x, y, w, body, east=True):
    """A car `w` long seen from above, its roof on row y; headlights (and tail lights) on `dl`."""
    h = max(3, w // 2)
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=body, outline=INK)
    d.rectangle([x + w // 4, y + 1, x + w - 1 - w // 4, y + h - 2], fill=mix(body, WHITE, 0.35))
    glass_x = x + w - 1 - w // 4 if east else x + w // 4
    d.line([glass_x, y + 1, glass_x, y + h - 2], fill=GLASS_DK)
    if dl is not None:
        front, back = (x + w, x - 1) if east else (x - 1, x + w)
        for yy in (y + 1, y + h - 2):
            dl.point((front, yy), fill=LIT_HI)
            dl.point((front + (1 if east else -1), yy), fill=LIT_HI + (120,))
            dl.point((back + (1 if east else -1), yy), fill=LIT_RED)


def person(d, x, foot, shirt, s=1):
    """Somebody standing on (x, foot), `s` px to the unit."""
    d.rectangle([x, foot - 3 * s + 1, x + s, foot], fill=(60, 62, 90))
    d.rectangle([x - (s > 1), foot - 6 * s + 1, x + s + (s > 1), foot - 3 * s], fill=shirt)
    d.rectangle([x, foot - 8 * s + 1, x + s, foot - 6 * s], fill=(240, 204, 170))
    d.line([x, foot - 8 * s + 1, x + s, foot - 8 * s + 1], fill=(60, 44, 44))


def cut(im, x, w, y=0, h=None):
    """The part of a canvas a window shows: `w` columns from x (and `h` rows from y)."""
    return im.crop((x, y, x + w, y + (im.height - y if h is None else h)))


def picture(key, im):
    """Save a whole picture for a cutscene, pixel-doubled, as assets/sprites/<key>.png."""
    big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    big.save(f'assets/sprites/{key}.png')
    print(f'{key}: {big.width}x{big.height}px')
    return big


def register_pictures(keys):
    """Put cutscene pictures in config.json's spriteMetadata: centred, one frame, and no
    tile name (they are not tiles), as the train's and the plane's cabins are."""
    cfg = json.load(open('config.json'))
    for key in keys:
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 0.5, 'anchorY': 0.5}
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)


def night(im, grade=NIGHT):
    """`im` as the night's grade leaves it: every channel multiplied (the preview only)."""
    r, g, b, a = im.split()
    return Image.merge('RGBA', [ch.point(lambda v, m=m: v * m // 255) for ch, m in zip((r, g, b), grade)] + [a])


def framed(frame, window, layers, hs, pans=None):
    """What a ride shows at height `hs` (0..1): each (picture, as tall as it is) of
    `layers` moved down as ViewRide.pan moves it, behind `frame`, whose hole is
    `window` (x, y, w, h). For the preview sheet."""
    x, y, w, h = window
    out = Image.new('RGBA', frame.size, VOID + (255,))
    for layer in layers:
        moved = round(hs * (layer.height - h))
        top = layer.height - h - moved
        out.alpha_composite(layer.crop(((layer.width - w) // 2, top, (layer.width - w) // 2 + w, top + h)), (x, y))
    out.alpha_composite(frame)
    return out


def sheet(ims, out, width=1600):
    """A contact sheet of images, as register()'s --preview makes of sprites."""
    rows, x, y, rowh = [], 16, 16, 0
    for im in ims:
        if x + im.width + 16 > width and x > 16:
            x, y, rowh = 16, y + rowh + 16, 0
        rows.append((im, x, y))
        x += im.width + 16
        rowh = max(rowh, im.height)
    page = Image.new('RGBA', (max(width, max(im.width for im in ims) + 32), y + rowh + 16), (95, 107, 133, 255))
    for im, x, y in rows:
        page.alpha_composite(im.convert('RGBA'), (x, y))
    page.save(out)
    print('preview ->', out)


# ---- the panorama north from Fukuoka Tower ---------------------------------------------------
PAN_W = 18 * C              # as wide as the deck's wall
NEAR_H, FAR_H = 512, 320    # the two layers; the taller one moves further (ViewRide.pan)
LIFT_WIN = (64, 64, 192, 224)       # the hole in view-lift: x, y, w, h as drawn (doubled: ViewRide.RIDES.lift.window)
LIFT_X = (PAN_W - LIFT_WIN[2]) // 2   # the lift's columns of the panorama: its middle
HORIZON = 84                # far's row where the bay meets the sky
PANE_BAND = 24              # the top row of the 160 a pane shows, of the view from the top
SHORE = 150                 # near's row where the beach meets the water, in the middle
PROM, PARK, ROADS, FORE, PLAZA = 204, 216, 276, 306, 398    # near's rows: promenade, park, road, forecourt, plaza
MARIZON = 262               # the pier's middle column
AXIS = (250, 274)           # the paved way from the tower to the pier


def shore(x):
    """near's top row at column x: the beach's edge, rising either side where the bay's
    shores run away to the west and the east."""
    if x < 132:
        return SHORE - round((132 - x) * 0.34)
    if x > 404:
        return SHORE - round((x - 404) * 0.3)
    return SHORE + round(2 * math.sin(x / 23))


def far_layer():
    rnd = random.Random(2421)
    im, d = new(PAN_W, FAR_H)
    sky(d, PAN_W, 0, HORIZON)
    for x, y, w in ((40, 30, 46), (150, 52, 30), (236, 22, 58), (352, 44, 40), (452, 28, 52), (540, 58, 26), (300, 66, 22), (96, 68, 18)):
        cloud(d, x, y, w)
    # the hills behind the far shore, palest of all
    hill = mix(SEA_FAR, HAZE, 0.55)
    for x in range(PAN_W):
        top = HORIZON - 4 - round(5 * math.sin(x / 41) + 3 * math.sin(x / 13 + 1) + 2 * math.sin(x / 7))
        d.line([x, max(top, HORIZON - 12), x, HORIZON], fill=hill)
    water(d, rnd, PAN_W, HORIZON + 1, FAR_H - 1)
    # Uminonakamichi, the long spit across the mouth of the bay, and Shikanoshima at its end
    spit, wood = mix(SAND, HAZE, 0.45), mix(GRASS_DK, HAZE, 0.5)
    d.rectangle([318, HORIZON - 1, PAN_W - 1, HORIZON + 1], fill=spit)
    d.rectangle([340, HORIZON - 3, PAN_W - 1, HORIZON - 1], fill=wood)
    for x in range(268, 336):
        top = HORIZON - round(9 * math.sin((x - 268) / 68 * math.pi) ** 0.8)
        d.line([x, top, x, HORIZON + 1], fill=wood)
    d.line([268, HORIZON + 2, 335, HORIZON + 2], fill=mix(SEA_FAR, WHITE, 0.4))
    # Nokonoshima, nearer and greener
    isle, isle_hi = mix(GRASS_DK, HAZE, 0.22), mix(GRASS, HAZE, 0.25)
    for x in range(62, 196):
        t = (x - 62) / 134
        top = HORIZON + 6 - round(21 * math.sin(t * math.pi) ** 0.7 + 2 * math.sin(x / 9))
        d.line([x, top, x, HORIZON + 7], fill=isle)
        d.line([x, top, x, top + 2 + round(3 * math.sin(x / 5) ** 2)], fill=isle_hi)
    d.line([60, HORIZON + 8, 198, HORIZON + 8], fill=mix(SAND, HAZE, 0.2))
    d.line([58, HORIZON + 9, 200, HORIZON + 9], fill=mix(SEA_FAR, WHITE, 0.45))
    # what is on the water: the island ferry and its wake, a freighter far out, sails
    d.rectangle([318, 112, 339, 116], fill=WHITE, outline=INK)
    d.rectangle([322, 108, 334, 112], fill=WHITE, outline=INK)
    d.line([324, 110, 332, 110], fill=GLASS)
    d.line([319, 115, 338, 115], fill=RED)
    d.rectangle([330, 104, 332, 108], fill=RED, outline=INK)
    for i in range(9):
        d.line([340 + i * 4, 117 + i // 3, 343 + i * 4, 117 + i // 3], fill=SURF)
    d.rectangle([420, HORIZON + 3, 440, HORIZON + 5], fill=mix(RED_DK, HAZE, 0.35))
    d.rectangle([434, HORIZON, 439, HORIZON + 2], fill=mix(WHITE, HAZE, 0.3))
    for x, y, s in ((214, 126, 7), (236, 134, 5), (392, 124, 6), (120, 122, 5), (506, 110, 4), (40, 132, 6)):
        d.polygon([(x, y - s * 2), (x, y - 1), (x + s, y - 1)], fill=WHITE)
        d.polygon([(x - 1, y - s * 2 + 2), (x - 1, y - 1), (x - s + 1, y - 1)], fill=(232, 238, 248))
        d.line([x - s, y, x + s, y], fill=INK)
    return im


def near_layers():
    """The near layer and its lights: (near, lights)."""
    rnd = random.Random(242)
    im, d = new(PAN_W, NEAR_H)
    li, dl = new(PAN_W, NEAR_H)

    # ---- the ground, from the water's edge down to the tower's foot ----------------------
    for x in range(PAN_W):
        top = shore(x)
        beach = 132 <= x <= 404
        d.line([x, top, x, NEAR_H - 1], fill=SAND if beach else PAVE_DK)
        if beach:
            d.line([x, top, x, top + 1], fill=SURF)
            d.point((x, top + 2), fill=SURF if (x // 3) % 3 else WET)
            d.line([x, top + 3, x, top + 6], fill=WET)
            d.point((x, top + 7), fill=SAND_DK if x % 2 else WET)
        else:                                                        # a sea wall, and the town behind it
            d.line([x, top, x, top + 2], fill=(214, 214, 222))
            d.point((x, top + 3), fill=INK)
    for _ in range(520):                                             # the sand's grain, and who is on it
        x, y = rnd.randrange(134, 403), rnd.randrange(SHORE + 10, PROM - 2)
        d.point((x, y), fill=rnd.choice((SAND_HI, SAND_HI, SAND_DK)))
    for x, y, col in ((170, 176, (236, 96, 96)), (196, 186, (90, 150, 230)), (300, 172, (250, 200, 70)), (322, 190, (236, 96, 96)),
                      (352, 178, (96, 190, 150)), (384, 186, (250, 200, 70)), (224, 192, (96, 190, 150)), (150, 190, (250, 200, 70))):
        d.ellipse([x - 3, y + 1, x + 4, y + 3], fill=SAND_DK)        # a parasol and its shade
        d.ellipse([x - 3, y - 3, x + 3, y], fill=col, outline=INK)
        d.line([x - 2, y - 2, x + 1, y - 2], fill=mix(col, WHITE, 0.5))
    for x, y in ((208, 174), (340, 168)):                            # beach volleyball
        d.rectangle([x, y, x + 15, y + 9], outline=SAND_HI)
        d.line([x + 7, y - 2, x + 7, y + 9], fill=WHITE)
        d.point((x + 7, y - 2), fill=INK)
    for i, (x, y) in enumerate(((160, 185), (186, 171), (238, 181), (292, 187), (312, 166), (366, 173), (374, 195), (218, 199), (334, 199), (394, 180))):
        person(d, x, y, ((236, 96, 96), (90, 150, 230), WHITE, (250, 200, 70))[i % 4])
    # two beach houses under the promenade, lit after dark
    for x, wall in ((176, WALLS[1]), (346, WALLS[4])):
        block(d, dl, rnd, x, PROM - 3, 22, 8, wall, roof=4, pitch=(5, 4), pane=(3, 3), lit=1.0, lamps=(LIT, LIT_HI))
        d.rectangle([x, PROM - 15, x + 21, PROM - 12], fill=RED, outline=INK)

    # the promenade: a pale walk, palms and lamps along it
    d.rectangle([0, PROM, PAN_W - 1, PARK - 1], fill=(214, 212, 222))
    d.line([0, PROM, PAN_W - 1, PROM], fill=WHITE)
    d.line([0, PARK - 1, PAN_W - 1, PARK - 1], fill=PAVE_DK)
    for x in range(8, PAN_W, 12):
        d.point((x, PROM + 5), fill=PAVE_DK)

    # the park: lawns, the paved way down its middle, paths, trees
    d.rectangle([0, PARK, PAN_W - 1, ROADS - 1], fill=GRASS)
    for _ in range(900):
        x, y = rnd.randrange(PAN_W), rnd.randrange(PARK + 1, ROADS - 1)
        d.line([x, y, x + rnd.randrange(1, 4), y], fill=rnd.choice((GRASS_HI, GRASS_HI, GRASS_DK)))
    for x in range(PAN_W):                                           # a path that wanders across
        y = PARK + 28 + round(9 * math.sin(x / 37) + 4 * math.sin(x / 11))
        d.line([x, y, x, y + 3], fill=(222, 214, 196))
        d.point((x, y + 4), fill=GRASS_DK)

    # the road: kerbs, lanes, a crossing on the tower's axis
    d.rectangle([0, ROADS, PAN_W - 1, FORE - 1], fill=ROAD)
    d.rectangle([0, ROADS, PAN_W - 1, ROADS + 2], fill=(206, 206, 216))
    d.line([0, ROADS + 3, PAN_W - 1, ROADS + 3], fill=ROAD_DK)
    d.rectangle([0, FORE - 3, PAN_W - 1, FORE - 1], fill=(206, 206, 216))
    d.line([0, FORE - 4, PAN_W - 1, FORE - 4], fill=ROAD_DK)
    for x in range(0, PAN_W, 14):
        d.line([x, ROADS + 14, x + 6, ROADS + 14], fill=(244, 206, 96))
    for x in range(AXIS[0] - 4, AXIS[1] + 5, 4):
        d.rectangle([x, ROADS + 5, x + 1, FORE - 6], fill=LINE)

    # the forecourt: paving between the two buildings at the tower's foot, and the plaza itself
    d.rectangle([0, FORE, PAN_W - 1, NEAR_H - 1], fill=PAVE)
    for y in range(FORE + 4, NEAR_H, 16):
        d.line([0, y, PAN_W - 1, y], fill=PAVE_DK)
    for x in range(0, PAN_W, 16):
        d.line([x, FORE, x, NEAR_H - 1], fill=PAVE_DK)
    for _ in range(150):                                             # the plaza's odd pale flags
        x, y = rnd.randrange(0, PAN_W, 16), FORE + 4 + 16 * rnd.randrange((NEAR_H - FORE) // 16)
        d.rectangle([x + 1, y + 1, x + 15, y + 15], fill=rnd.choice((PAVE_HI, PAVE_HI, mix(PAVE, PAVE_DK, 0.4))))
    # the way from the tower to the pier, through all of it
    d.rectangle([AXIS[0], PARK, AXIS[1], ROADS - 1], fill=(222, 214, 196))
    d.line([AXIS[0] - 1, PARK, AXIS[0] - 1, ROADS - 1], fill=GRASS_DK)
    d.line([AXIS[1] + 1, PARK, AXIS[1] + 1, ROADS - 1], fill=GRASS_DK)
    for y in range(PARK + 4, ROADS - 2, 8):
        d.line([AXIS[0] + 3, y, AXIS[1] - 3, y], fill=(204, 194, 176))

    # ---- the far shores: the town to the west, the city and the dome to the east ----------
    # (back rows first; each row's feet a little lower, its blocks a little bigger and clearer)
    def town(x0, x1, rows, top_of, gap=(0, 0)):
        for n, (dy, hs, ws, haze) in enumerate(rows):
            x = x0 + rnd.randrange(0, 4)
            while x < x1:
                w = rnd.randrange(*ws)
                foot = top_of(x + w // 2) + dy + rnd.randrange(0, 3)
                if gap[0] < x + w and x < gap[1]:                    # left clear: something stands here
                    x = gap[1]
                    continue
                block(d, dl, rnd, x, foot, w, rnd.randrange(*hs), rnd.choice(WALLS), roof=rnd.choice((1, 2, 2, 3)),
                      pitch=(3, 3) if n < 2 else (4, 4), pane=(1, 1) if n < 2 else (2, 2), lit=0.4, haze=haze, ink=n >= 2)
                x += w + rnd.randrange(0, 3)

    west = [(6, (5, 11), (5, 9), 0.5), (15, (7, 16), (6, 11), 0.34), (27, (9, 20), (8, 14), 0.18)]
    east = [(6, (6, 14), (5, 9), 0.5), (15, (9, 22), (6, 11), 0.34), (27, (12, 28), (8, 14), 0.2), (42, (14, 30), (10, 17), 0.08)]
    town(0, 122, west, shore)
    town(414, PAN_W, east[:3], shore)
    # the baseball dome: a low silver shell on a drum, a ring of lights under its rim
    dx, dy = 470, shore(470) + 30
    d.rectangle([dx - 33, dy - 4, dx + 33, dy + 8], fill=(170, 176, 196), outline=INK)
    for x in range(dx - 30, dx + 31, 6):
        d.line([x, dy - 2, x, dy + 6], fill=(128, 134, 160))
        dl.rectangle([x + 2, dy + 1, x + 3, dy + 3], fill=LIT_COOL)
    d.chord([dx - 36, dy - 25, dx + 36, dy + 15], 180, 360, fill=(206, 212, 226), outline=INK)
    for k in (-24, -12, 0, 12, 24):
        d.line([dx + k, dy - 5, dx + k * 0.25, dy - 24], fill=(170, 178, 200))
    d.arc([dx - 30, dy - 22, dx + 20, dy + 8], 190, 260, fill=WHITE)
    d.line([dx - 36, dy - 5, dx + 36, dy - 5], fill=INK)
    # the hotel beside it: a tall blue slab with a rounded head, the tallest thing on the shore
    hx, hf = 524, shore(524) + 34
    d.rectangle([hx, hf - 74, hx + 15, hf], fill=mix(GLASS, HAZE, 0.25), outline=INK)
    d.chord([hx, hf - 82, hx + 15, hf - 66], 180, 360, fill=mix(GLASS_HI, HAZE, 0.2), outline=INK)
    d.line([hx + 2, hf - 72, hx + 2, hf - 2], fill=mix(GLASS_HI, HAZE, 0.2))
    for wy in range(hf - 70, hf - 3, 4):
        for wx in range(hx + 4, hx + 13, 3):
            d.point((wx, wy), fill=GLASS_DK)
            if rnd.random() < 0.55:
                dl.point((wx, wy), fill=rnd.choice((LIT, LIT_HI)))
    dl.point((hx + 7, hf - 83), fill=LIT_RED)
    town(404, PAN_W, east[3:], shore, gap=(dx - 40, dx + 40))
    for x in range(dx - 34, dx + 36, 10):                            # the trees round the dome
        tree(d, x, dy + 14 + (x % 3), 3, ink=False)
    for x in range(410, PAN_W, 17):                                  # trees along the sea wall
        tree(d, x, shore(x) + 62 + (x % 5), 4, ink=False)
    town(0, 126, [(52, (14, 26), (12, 18), 0.05)], shore)
    for x in range(6, 130, 19):
        tree(d, x, shore(x) + 70 + (x % 4), 4, ink=False)

    # ---- Marizon: the pier out from the middle of the beach, the hall and the chapel on it --
    mx = MARIZON
    d.rectangle([mx - 6, 126, mx + 6, PROM], fill=(214, 196, 160), outline=INK)       # the boardwalk
    for y in range(128, PROM, 4):
        d.line([mx - 5, y, mx + 5, y], fill=(186, 166, 132))
    for y in range(132, PROM - 4, 12):
        lamp(d, dl, mx - 7, y + 4, 5)
        lamp(d, dl, mx + 7, y + 4, 5)
    d.polygon([(mx - 26, 100), (mx + 26, 100), (mx + 31, 106), (mx + 31, 124), (mx + 24, 130), (mx - 24, 130), (mx - 31, 124), (mx - 31, 106)],
              fill=(226, 214, 190), outline=INK)                    # the deck it all stands on
    d.line([mx - 30, 125, mx - 24, 131], fill=(150, 132, 110))
    d.line([mx + 30, 125, mx + 24, 131], fill=(150, 132, 110))
    for x in range(mx - 28, mx + 29, 7):                             # its piles, in the water
        d.line([x, 131, x, 134], fill=(110, 96, 96))
    block(d, dl, rnd, mx - 24, 122, 30, 12, (244, 238, 224), roof=6, pitch=(4, 5), pane=(2, 3), lit=0.9, lamps=(LIT, LIT_HI))
    d.rectangle([mx - 24, 105, mx + 5, 110], fill=RED, outline=INK)                  # terracotta roofs
    d.line([mx - 23, 106, mx + 4, 106], fill=RED_HI)
    block(d, dl, rnd, mx + 9, 122, 16, 10, (244, 238, 224), roof=4, pitch=(4, 4), pane=(2, 3), lit=0.9, lamps=(LIT, LIT_HI))
    d.rectangle([mx + 9, 109, mx + 24, 112], fill=RED, outline=INK)
    d.polygon([(mx + 13, 108), (mx + 17, 92), (mx + 21, 108)], fill=RED_HI, outline=INK)  # the chapel's spire
    d.line([mx + 17, 88, mx + 17, 92], fill=INK)
    d.line([mx + 15, 90, mx + 19, 90], fill=INK)
    dl.point((mx + 17, 96), fill=LIT_HI)
    for x in (mx - 28, mx - 14, mx, mx + 14, mx + 28):
        lamp(d, dl, x, 129, 5)
    d.rectangle([mx + 32, 114, mx + 46, 118], fill=WHITE, outline=INK)                 # the ferry at its landing
    d.rectangle([mx + 35, 111, mx + 42, 114], fill=WHITE, outline=INK)
    d.line([mx + 33, 117, mx + 45, 117], fill=GLASS)
    dl.line([mx + 36, 112, mx + 41, 112], fill=LIT_HI)

    # ---- along the promenade and through the park ------------------------------------------
    for x in range(10, PAN_W, 26):
        if not AXIS[0] - 8 < x < AXIS[1] + 8:
            palm(d, x, PROM + 3, 11)
    for x in range(23, PAN_W, 26):
        if not AXIS[0] - 8 < x < AXIS[1] + 8:
            lamp(d, dl, x, PROM + 8, 9)
    for x, y, r in ((204, 244, 6), (222, 236, 5), (236, 262, 7), (296, 240, 6), (312, 258, 7), (334, 236, 5), (350, 262, 7), (372, 244, 6),
                    (196, 268, 7), (286, 268, 7), (30, 240, 6), (64, 262, 7), (110, 244, 6), (150, 264, 7), (420, 244, 6), (460, 262, 7),
                    (510, 240, 6), (548, 264, 7), (176, 238, 5), (396, 266, 6)):
        tree(d, x, y, r)
    for y in (PARK + 14, PARK + 38):
        lamp(d, dl, AXIS[0] - 3, y, 11)
        lamp(d, dl, AXIS[1] + 3, y, 11)
    for i, (x, y) in enumerate(((256, 232), (266, 250), (258, 268), (214, 252), (326, 250), (300, 228))):
        person(d, x, y, ((236, 96, 96), WHITE, (90, 150, 230))[i % 3])

    # ---- the road's traffic ------------------------------------------------------------------
    for x, col, east_bound in ((200, (236, 96, 96), True), (232, WHITE, True), (300, (90, 150, 230), True), (356, (250, 200, 70), True),
                               (40, WHITE, True), (120, (96, 190, 150), True), (470, (236, 96, 96), True), (540, WHITE, True)):
        car(d, dl, x, ROADS + 17, 12, col, east=True)
    for x, col in ((214, (250, 200, 70)), (282, WHITE), (330, (160, 164, 184)), (372, (236, 96, 96)), (70, (90, 150, 230)), (160, WHITE),
                   (430, (96, 190, 150)), (500, (250, 200, 70))):
        car(d, dl, x, ROADS + 6, 12, col, east=False)
    d.rectangle([318, ROADS + 16, 343, ROADS + 23], fill=(96, 190, 150), outline=INK)     # a bus
    d.rectangle([321, ROADS + 18, 340, ROADS + 21], fill=WHITE)
    d.line([318, ROADS + 16, 343, ROADS + 16], fill=INK)

    # ---- the tower's foot: two buildings either side of the forecourt, then the plaza --------
    block(d, dl, rnd, 150, FORE + 78, 86, 46, WALLS[0], roof=26, pitch=(9, 11), pane=(6, 7), lit=0.6)
    block(d, dl, rnd, 292, FORE + 70, 100, 38, WALLS[3], roof=24, pitch=(10, 11), pane=(7, 7), lit=0.6)
    block(d, dl, rnd, 0, FORE + 74, 130, 42, WALLS[2], roof=24, pitch=(9, 11), pane=(6, 7), lit=0.6)
    block(d, dl, rnd, 412, FORE + 80, 164, 48, WALLS[1], roof=24, pitch=(9, 11), pane=(6, 7), lit=0.6)
    for x in (246, 280):                                             # trees up the forecourt
        for y in (FORE + 22, FORE + 50, FORE + 78):
            tree(d, x, y, 8)
    lamp(d, dl, 263, FORE + 40, 16)
    lamp(d, dl, 263, FORE + 82, 18)
    for x, y, r in ((206, 430, 11), (338, 436, 12), (232, 476, 13), (366, 486, 13), (60, 440, 12), (130, 480, 13), (450, 436, 12), (520, 482, 13)):
        tree(d, x, y, r)
    for x, y in ((276, 440), (304, 496), (196, 500), (372, 444)):
        lamp(d, dl, x, y, 26)
    for x, y in ((250, 452), (318, 468)):                            # benches
        box(d, x, y, x + 18, y + 4, (150, 110, 84))
        d.line([x + 1, y + 1, x + 17, y + 1], fill=(196, 150, 110))
        d.line([x + 2, y + 5, x + 2, y + 7], fill=INK)
        d.line([x + 16, y + 5, x + 16, y + 7], fill=INK)
    for i, (x, y) in enumerate(((262, 470), (290, 452), (300, 486), (226, 504), (346, 506), (270, 506), (212, 456))):
        person(d, x, y, ((236, 96, 96), WHITE, (90, 150, 230), (250, 200, 70))[i % 4], s=2)
    return im, li


# ---- the lift ----------------------------------------------------------------------------------
CAB, CAB_HI, CAB_DK = (84, 92, 122), (120, 130, 160), (56, 62, 90)
PANEL = (14, 16, 28)
LIFT_PANEL = (100, 18, 120, 32)     # the counter's panel: x, y, w, h as drawn (doubled: ViewRide.RIDES.lift.panel)


def lift_frame():
    """The lift from inside, 320x320: you stand facing the glass."""
    im, d = new(320, 320)
    wx, wy, ww, wh = LIFT_WIN
    d.rounded_rectangle([0, 0, 319, 319], radius=10, fill=CAB_DK, outline=INK)
    # the ceiling, with its two lamps
    d.rectangle([1, 1, 318, 12], fill=(46, 50, 74))
    d.line([10, 12, 309, 12], fill=INK)
    for x in (70, 236):
        d.rectangle([x, 4, x + 13, 9], fill=GLOW_HI, outline=INK)
        d.line([x + 2, 10, x + 11, 10], fill=GLOW)
    # the walls either side of the glass: brushed steel panels
    for x0, x1 in ((6, wx - 8), (wx + ww + 7, 313)):
        d.rectangle([x0, 14, x1, 292], fill=CAB)
        for x in range(x0 + 3, x1 - 2, 3):
            d.line([x, 16, x, 290], fill=CAB_HI if (x // 3) % 4 == 0 else mix(CAB, CAB_HI, 0.25))
        for y in (104, 200):
            d.line([x0, y, x1, y], fill=CAB_DK)
            d.line([x0, y + 1, x1, y + 1], fill=CAB_HI)
        d.rectangle([x0, 14, x1, 292], outline=INK)
    # the buttons, on the right wall; a notice on the left
    box(d, 276, 136, 298, 196, (40, 44, 66))
    for i, y in enumerate(range(142, 190, 9)):
        d.ellipse([280, y, 286, y + 6], fill=GLOW_HI if i == 0 else STEEL, outline=INK)
        d.ellipse([289, y, 295, y + 6], fill=STEEL, outline=INK)
    box(d, 20, 136, 44, 168, (236, 232, 220))
    d.polygon([(32, 141), (27, 163), (37, 163)], fill=GLASS, outline=INK)         # the tower, on the notice
    d.line([32, 137, 32, 141], fill=RED)
    # above the glass: the head of the wall, and the counter's panel
    d.rectangle([wx - 8, 14, wx + ww + 7, wy - 8], fill=CAB)
    d.rectangle([wx - 8, 14, wx + ww + 7, wy - 8], outline=INK)
    px, py, pw, ph = LIFT_PANEL
    bar(d, px - 4, py - 4, px + pw + 3, py + ph + 3, STEEL, STEEL_HI, STEEL_DK)
    box(d, px, py, px + pw - 1, py + ph - 1, PANEL)
    # the window's steel frame, and the glass: a hole
    bar(d, wx - 8, wy - 8, wx + ww + 7, wy + wh + 7, STEEL, STEEL_HI, STEEL_DK)
    d.rectangle([wx - 2, wy - 2, wx + ww + 1, wy + wh + 1], fill=STEEL_DK, outline=INK)
    im.paste((0, 0, 0, 0), (wx, wy, wx + ww, wy + wh))
    for x in (wx + ww // 3, wx + 2 * ww // 3):                       # two glazing bars
        d.rectangle([x - 1, wy, x + 1, wy + wh - 1], fill=STEEL_DK)
        d.line([x - 1, wy, x - 1, wy + wh - 1], fill=STEEL)
    for x0, y0, n in ((wx + 14, wy + 6, 30), (wx + 22, wy + 6, 18), (wx + 150, wy + 40, 26)):   # light on the glass
        for i in range(n):
            d.point((x0 + i // 2, y0 + i), fill=(255, 255, 255, 46))
    # the handrail across it
    for x in (wx + 10, wx + ww - 14):
        box(d, x, wy + wh - 52, x + 3, wy + wh - 40, STEEL_DK)
    bar(d, wx - 2, wy + wh - 58, wx + ww + 1, wy + wh - 52, BRASS, BRASS_HI, BRASS_DK)
    # the floor: dark rubber, studded, a lit strip along the sill
    d.rectangle([4, 293, 315, 315], fill=(52, 54, 74))
    d.line([4, 293, 315, 293], fill=INK)
    d.rectangle([wx - 8, 294, wx + ww + 7, 296], fill=STEEL_HI)
    for y in range(300, 315, 5):
        for x in range(10 + (y % 2) * 3, 312, 7):
            d.point((x, y), fill=(84, 88, 112))
    d.rounded_rectangle([0, 0, 319, 319], radius=10, outline=INK)
    return im


# ---- the deck's own pieces -----------------------------------------------------------------------
CARPET, CARPET_ALT, CARPET_HI, CARPET_DK = (58, 62, 98), (52, 56, 90), (78, 84, 124), (42, 44, 74)
DECK = {'head': (76, 82, 112), 'head_hi': (112, 120, 152), 'head_dk': (50, 54, 82), 'face': (104, 112, 146), 'face_hi': (136, 146, 178),
        'face_dk': (78, 84, 118), 'trim': STEEL, 'post': STEEL, 'post_hi': STEEL_HI, 'post_dk': STEEL_DK, 'sill': STEEL_DK}


def carpet(alt):
    """A carpet tile: flecked, a seam along two of its edges."""
    def draw():
        rnd = random.Random(7 + alt)
        im, d = new(C, C)
        d.rectangle([0, 0, 31, 31], fill=CARPET_ALT if alt else CARPET)
        for _ in range(46):
            x, y = rnd.randrange(32), rnd.randrange(32)
            d.point((x, y), fill=rnd.choice((CARPET_HI, CARPET_DK, CARPET_DK)))
        d.line([0, 31, 31, 31], fill=CARPET_DK)
        d.line([31, 0, 31, 31], fill=CARPET_DK)
        return im
    return draw


def lift_sill(side):
    """Half of the lift's open doorway: its steel sill, the cabin's lit floor beyond, a door post."""
    def draw():
        im, d = new(C, C)
        for y in range(32):                                          # the cabin's floor, lit
            d.line([0, y, 31, y], fill=mix((214, 218, 232), WHITE, y / 31))
        for x in range(3, 32, 6):
            for y in range(15, 32, 5):
                d.point((x + (y % 2) * 3, y), fill=(176, 182, 204))
        bar(d, -1, 0, 32, 9, STEEL, STEEL_HI, STEEL_DK)             # the sill, grooved for the doors
        d.line([0, 4, 31, 4], fill=STEEL_DK)
        d.line([0, 6, 31, 6], fill=INK)
        x0 = 0 if side == 'w' else 26                               # the door post
        post(d, x0, -1, x0 + 5, 32, DECK['post'], DECK['post_hi'], DECK['post_dk'])
        d.rectangle([x0 + 1, 12, x0 + 4, 14], fill=(250, 200, 70))  # its light curtain
        return im
    return draw


def pane(n, view):
    """Pane `n` (1..6) of the back wall, 3x5: its 96 columns of the view from the top,
    between mullions, on a low steel sill."""
    def draw():
        im, d = new(3 * C, 5 * C)
        im.paste(cut(view, (n - 1) * 3 * C, 3 * C), (0, 0))
        for x0, y0, length in ((18, 8, 44), (26, 8, 26), (70, 30, 36)) if n % 2 else ((58, 12, 40), (12, 40, 24)):
            for i in range(length):                                 # light on the glass
                x, y = x0 + i // 2, y0 + i
                im.putpixel((x, y), mix(im.getpixel((x, y))[:3], WHITE, 0.16) + (255,))
        d.rectangle([0, 0, 95, 5], fill=DECK['head'])               # the head of the wall
        d.line([0, 4, 95, 4], fill=DECK['head_hi'])
        d.line([0, 5, 95, 5], fill=INK)
        d.rectangle([0, 148, 95, 159], fill=STEEL_DK)               # the sill
        d.line([0, 148, 95, 148], fill=INK)
        d.line([0, 150, 95, 150], fill=STEEL)
        d.line([0, 159, 95, 159], fill=INK)
        for x in range(6, 96, 12):
            d.line([x, 153, x + 5, 153], fill=(70, 76, 104))        # the heating grille in it
            d.line([x, 156, x + 5, 156], fill=(70, 76, 104))
        for x0 in (0, 93):                                          # half a mullion each side
            d.rectangle([x0, 6, x0 + 2, 147], fill=STEEL)
            d.line([x0 + (2 if x0 == 0 else 0), 6, x0 + (2 if x0 == 0 else 0), 147], fill=INK)
            d.line([x0 + (0 if x0 == 0 else 2), 6, x0 + (0 if x0 == 0 else 2), 147], fill=STEEL_HI if x0 else STEEL_DK)
        bar(d, 2, 118, 93, 121, STEEL, STEEL_HI, STEEL_DK)          # a rail to lean on
        return im
    return draw


def binoculars():
    """A coin-operated viewer, 1x2: you see its back; it looks out of the window."""
    im, d = new(C, 2 * C)
    shadow(d, 7, 55, 25, 61)
    d.ellipse([8, 53, 23, 60], fill=STEEL_DK, outline=INK)          # the foot plate
    post(d, 13, 30, 18, 56, STEEL, STEEL_HI, STEEL_DK)
    box(d, 11, 38, 20, 46, BRASS)                                   # the coin box
    d.line([14, 41, 17, 41], fill=INK)
    d.point((12, 39), fill=BRASS_HI)
    d.rounded_rectangle([5, 14, 26, 31], radius=4, fill=(92, 128, 190), outline=INK)   # the head
    d.line([8, 16, 23, 16], fill=(150, 184, 232))
    d.line([7, 29, 24, 29], fill=(62, 90, 150))
    for x in (8, 18):                                               # the eyepieces, towards you
        d.ellipse([x, 20, x + 6, 26], fill=BLACK, outline=INK)
        d.point((x + 2, 22), fill=STEEL_HI)
    d.rectangle([14, 10, 17, 14], fill=STEEL, outline=INK)          # the sight on top
    return im


def compass():
    """A plinth with a brass map of the bay let into its top, 2x1."""
    im, d = new(2 * C, C)
    shadow(d, 3, 26, 61, 31)
    box(d, 4, 16, 59, 28, (96, 102, 132))                           # the plinth's front
    d.line([5, 26, 58, 26], fill=(66, 72, 100))
    d.polygon([(8, 3), (55, 3), (59, 16), (4, 16)], fill=(150, 156, 184), outline=INK)   # its top
    d.ellipse([13, 4, 50, 15], fill=BRASS, outline=INK)
    d.arc([15, 5, 48, 14], 180, 300, fill=BRASS_HI)
    d.line([31, 5, 31, 14], fill=BRASS_DK)
    d.line([16, 9, 47, 9], fill=BRASS_DK)
    d.polygon([(31, 5), (29, 9), (33, 9)], fill=(209, 107, 86))     # north
    d.point((31, 9), fill=INK)
    for x, y in ((21, 7), (40, 7), (24, 12), (39, 12), (44, 10)):
        d.point((x, y), fill=BRASS_DK)
    return im


def locks():
    """The lovers' fence, 2x2: a heart of padlocks on a mesh between two posts."""
    rnd = random.Random(11)
    im, d = new(2 * C, 2 * C)
    shadow(d, 3, 56, 61, 62)
    box(d, 6, 12, 57, 52, (70, 76, 106))                            # the mesh
    for x in range(10, 56, 4):
        d.line([x, 13, x, 51], fill=(96, 104, 136))
    for y in range(16, 52, 4):
        d.line([7, y, 56, y], fill=(96, 104, 136))
    heart, rest = [(226, 92, 100), (226, 92, 100), (246, 140, 150), (209, 107, 86)], [BRASS, BRASS_HI, STEEL_HI, BRASS_DK]
    for y in range(15, 50, 3):                                      # the heart, in locks
        for x in range(9, 55, 3):
            u, v = (x - 31.5) / 17, (30 - y) / 15 + 0.2
            inside = (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0
            if inside or rnd.random() < 0.22:
                col = rnd.choice(heart if inside else rest)
                d.rectangle([x, y, x + 1, y + 1], fill=col)
                d.point((x, y - 1), fill=mix(col, INK, 0.5))
    for x in (2, 56):
        post(d, x, 6, x + 5, 59, STEEL, STEEL_HI, STEEL_DK)
        d.rectangle([x - 1, 4, x + 6, 7], fill=STEEL_HI, outline=INK)
    bar(d, 6, 10, 57, 13, STEEL, STEEL_HI, STEEL_DK)
    return im


def bench():
    """A backless bench, 2x1: upholstered, on steel legs."""
    im, d = new(2 * C, C)
    shadow(d, 4, 25, 60, 31)
    for x in (9, 51):
        box(d, x, 20, x + 3, 28, STEEL_DK)
    box(d, 4, 15, 59, 22, (40, 84, 96))                             # the cushion's front
    d.polygon([(7, 5), (56, 5), (59, 15), (4, 15)], fill=(58, 118, 128), outline=INK)   # its top
    d.line([9, 7, 54, 7], fill=(96, 158, 164))
    for x in (22, 41):
        d.line([x, 6, x - 1, 14], fill=(40, 84, 96))
        d.line([x - 1, 16, x - 1, 21], fill=(28, 62, 76))
    return im


def lift_sign():
    """The sign that stands by the lift, 1x2: up and down, and the tower."""
    im, d = new(C, 2 * C)
    shadow(d, 8, 56, 24, 61)
    d.ellipse([9, 54, 22, 60], fill=STEEL_DK, outline=INK)
    post(d, 14, 34, 17, 56, STEEL, STEEL_HI, STEEL_DK)
    box(d, 4, 8, 27, 36, (36, 44, 78))
    d.rectangle([5, 9, 26, 10], fill=(64, 76, 120))
    d.polygon([(11, 13), (6, 21), (16, 21)], fill=(250, 200, 70))   # up
    d.polygon([(11, 32), (6, 24), (16, 24)], fill=WHITE)            # down
    d.polygon([(22, 12), (19, 32), (25, 32)], fill=(125, 185, 250), outline=None)   # the tower
    d.line([22, 9, 22, 12], fill=(209, 107, 86))
    return im


def downlight():
    """A pendant lamp, 1x2: hung from the ceiling, over your head."""
    im, d = new(C, 2 * C)
    d.line([15, 0, 15, 30], fill=BLACK)
    d.line([16, 0, 16, 30], fill=(60, 62, 84))
    d.rectangle([11, 30, 20, 43], fill=(44, 46, 66), outline=INK)   # the can
    d.line([12, 31, 12, 42], fill=(84, 88, 116))
    d.rectangle([10, 43, 21, 45], fill=STEEL_DK, outline=INK)
    d.ellipse([11, 44, 20, 49], fill=GLOW_HI, outline=GLOW)         # the light under it
    return im


def panorama():
    """(near, far, lights) and the view from the top that the panes are cut from."""
    near, lights = near_layers()
    far = far_layer()
    top = Image.new('RGBA', (PAN_W, 5 * C))
    top.alpha_composite(cut(far, 0, PAN_W, PANE_BAND, 5 * C))
    top.alpha_composite(cut(near, 0, PAN_W, PANE_BAND, 5 * C))
    return near, far, lights, top


def sprites(view):
    p = 'deck-in-'
    out = {
        p + 'floor-a': carpet(0), p + 'floor-b': carpet(1),
        p + 'side-w': wall_side(DECK, 'w'), p + 'side-e': wall_side(DECK, 'e'),
        p + 'wall-front': wall_front(DECK),
        p + 'lift-w': lift_sill('w'), p + 'lift-e': lift_sill('e'),
        p + 'doorlight': doorlight,
        p + 'binoculars': binoculars, p + 'compass': compass, p + 'locks': locks, p + 'bench': bench,
        p + 'lift-sign': lift_sign, p + 'downlight': downlight,
    }
    for n in range(1, 7):
        out[f'{p}window-{n}'] = pane(n, view)
    return out


# The pendant lamps are Tops under four rows tall: lifted in front of whatever taller
# thing stands behind them. The light out of the lift lies on the carpet.
DEPTH_BIAS = {'deck-in-downlight': 10, 'deck-in-doorlight': -40}


def main(argv):
    near, far, lights, top = panorama()
    register(sprites(top), DEPTH_BIAS)
    frame = lift_frame()
    pictures = {'view-lift': frame}
    for name, layer in (('near', near), ('far', far), ('lights', lights)):
        pictures[f'view-fukuoka-{name}'] = cut(layer, LIFT_X, LIFT_WIN[2])
    for key, im in pictures.items():
        picture(key, im)
    register_pictures(pictures)

    if '--preview' in argv:
        # the ride as ViewRide draws it, at the foot, half way and the top, by day and by night;
        # then the wall of panes, the canvases, and the pieces
        day = [pictures['view-fukuoka-far'], pictures['view-fukuoka-near']]
        dark = [night(pictures['view-fukuoka-far']), night(pictures['view-fukuoka-near']), pictures['view-fukuoka-lights']]
        ims = [framed(frame, LIFT_WIN, layers, h) for layers in (day, dark) for h in (0, 0.5, 1)]
        wall = Image.new('RGBA', (PAN_W, 5 * C))
        built = {name: fn() for name, fn in sprites(top).items()}
        for n in range(1, 7):
            wall.alpha_composite(built[f'deck-in-window-{n}'], ((n - 1) * 3 * C, 0))
        glow = night(wall)
        glow.alpha_composite(cut(lights, 0, PAN_W, PANE_BAND, 5 * C))
        ims += [wall, glow, near, far, lights]
        ims += [im.resize((im.width * 2, im.height * 2), Image.NEAREST) for name, im in built.items() if 'window' not in name]
        sheet(ims, argv[argv.index('--preview') + 1], width=2000)


if __name__ == '__main__':
    main(sys.argv)
