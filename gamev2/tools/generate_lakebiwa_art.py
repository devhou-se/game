#!/usr/bin/env python3
"""generate_lakebiwa_art.py — Lake Biwa's own art, in the house look (issue #380; #269, part 1).

The room is tools/generate_lakebiwa.py's, a district of the stitched KansaiCity.
Every sprite is drawn with tools/house_look.py by the recipe in
docs/generators-and-checks.md ("House look: GuttyKreum"): colours of the
GuttyKreum sheets only (house_look.RAMPS), a 1px ink silhouette, light from the
upper left, rectangles and pixels only, at half size (32px a cell) and doubled.

  biwa-hikone-keep_0_0    6x6  Hikone's keep: a coursed stone base, three white tiers
                               under dark tiled roofs, gables on the middle tier,
                               bell-shaped windows, gilt ridge ends. Looked up at
  biwa-torii_0_0          2x3  Shirahige's torii, standing in the lake: vermilion
                               posts and two lintels under a dark cap, wet at the foot
  biwa-tunnel_0_0         4x3  a concrete portal in a wooded hillside, the mouth on
                               columns 1-2, open to the bottom edge
  biwa-monkey_0_0         1x1  a sitting macaque
  biwa-cycle-sign_0_0     1x2  the Biwaichi's blue board, a bicycle on it, on a pole
  biwa-paddy_0_0          1x1  harvested stubble in rows: ground, opaque, tiles seamlessly
  biwa-station-sign_0_0   2x2  Takashima's nameboard, たかしま over a blue band, on two posts
  biwa-fingerpost_0_0     1x2  a wooden post with two arms, at the seam with Nara

Nothing is random and the only text is set in the game's own font
(fonts/PixelMplus12-Grid.ttf), so a re-run draws the same pixels.

Run from gamev2/:  python3 tools/generate_lakebiwa_art.py [--preview OUT.png]
Needs Pillow. Writes assets/sprites/<key>.png, registers the sprites in config.json
(spriteMetadata, tileNames) and marks the keep in game.lookUp.sprites.
"""
import json
import sys

import art_register
import house_look as hl
from house_look import fill, tone

C = 32                                  # a cell, at half size


def T(ramp, i):
    return tone(ramp, i)


# ---- Hikone's keep --------------------------------------------------------------------
def roof(im, cx, y0, y1, hw0, hw1):
    """A tiled hip roof seen from the front, `hw0` half wide at its top row and
    `hw1` at its eave: laid in courses, the west end lit and the east in shade,
    a dark eave lip, its corners turned up."""
    n = y1 - y0
    for y in range(y0, y1 + 1):
        hw = hw0 + (hw1 - hw0) * (y - y0) // max(1, n)
        x0, x1 = cx - hw, cx + hw - 1
        r = y - y0
        if y >= y1 - 1:
            fill(im, (x0, y, x1, y), T('steel', 0))                     # the eave's lip
            continue
        if r == 0:
            fill(im, (x0, y, x1, y), T('steel', 3))                     # the ridge row, lit
            continue
        fill(im, (x0, y, x1, y), T('steel', 1) if r % 3 == 0 else T('steel', 2))
        if r % 3:
            px = im.load()
            for x in range(x0 + (r // 3) % 2, x1 + 1, 4):                # the tiles' rolls
                px[x, y] = T('steel', 3)
        fill(im, (x0, y, x0 + 1, y), T('steel', 3))                     # the lit west hip
        fill(im, (x1 - 1, y, x1, y), T('steel', 1))                     # the east in shade
    for dy, out in ((0, 2), (1, 2), (2, 1)):                            # the upturned corners
        y = y1 - dy
        hw = hw1 + out
        fill(im, (cx - hw, y - 1, cx - hw1 - 1, y), T('steel', 0))
        fill(im, (cx + hw1, y - 1, cx + hw - 1, y), T('steel', 0))


def wall(im, cx, y0, y1, hw):
    """A white plastered tier: lit along the top-left, the roof's lip shading its top row."""
    x0, x1 = cx - hw, cx + hw - 1
    hl.shade(im, (x0, y0, x1, y1), hl.material('cream', 3), part=4)
    fill(im, (x0, y0, x1, y0 + 1), T('cream', 1))                       # the eave's shadow
    fill(im, (x1, y0, x1, y1), T('cream', 2))


def gable(im, gx, top, h):
    """A triangular gable on a roof: a white face under dark barge boards, a gilt boss at its apex."""
    for i in range(h):
        y, hw = top + i, 1 + i * 3 // 2
        fill(im, (gx - hw, y, gx + hw - 1, y), T('steel', 0))
        if hw > 2 and i < h - 1:
            fill(im, (gx - hw + 2, y, gx + hw - 3, y), T('cream', 2) if i % 2 else T('cream', 3))
    fill(im, (gx - 1, top + 2, gx, top + 3), T('gold', 3))
    fill(im, (gx - 1, top + h - 5, gx, top + h - 3), T('night', 2))     # a window in the gable


BELL = hl.pixmap(['..fff..',
                  '.fgggf.',
                  '.fglgf.',
                  '.fgggf.',
                  'fgggggf',
                  'fffffff'], {'f': tone('steel', 0), 'g': tone('night', 2), 'l': tone('night', 4)})
SLOT = hl.pixmap(['fff',
                  'fgf',
                  'fgf',
                  'fgf',
                  'fff'], {'f': tone('steel', 0), 'g': tone('night', 2)})


def stone_base(im, cx, y0, y1, hw0, hw1):
    """The coursed stone base, battered: wider at its foot, light from the west."""
    px = im.load()
    for y in range(y0, y1 + 1):
        hw = hw0 + (hw1 - hw0) * (y - y0) // max(1, y1 - y0)
        x0, x1 = cx - hw, cx + hw - 1
        course, r = (y - y0) // 6, (y - y0) % 6
        if r == 5:
            fill(im, (x0, y, x1, y), T('steel', 2))                      # the bed joint
            continue
        fill(im, (x0, y, x1, y), T('steel', 4) if r else T('steel', 5))
        for x in range(x0 + (course % 2) * 7, x1 + 1, 14):              # the head joints
            px[x, y] = T('steel', 2)
            if r and x + 1 <= x1:
                px[x + 1, y] = T('steel', 5)
        if r in (3, 4):
            for x in range(x0 + 3 + (course % 2) * 7, x1 - 1, 14):
                px[x + 4, y] = T('steel', 3)
        fill(im, (x0, y, x0, y), T('steel', 5))
        fill(im, (x1 - 1, y, x1, y), T('steel', 2))


def hikone_keep():
    im = hl.canvas(6 * C, 6 * C)
    cx = 96
    stone_base(im, cx, 146, 190, 64, 74)
    # the first tier: square windows, then its roof
    wall(im, cx, 122, 145, 60)
    for x in range(cx - 52, cx + 52, 12):
        hl.stamp(im, SLOT, x, 130)
    roof(im, cx, 102, 121, 46, 74)
    # the second tier: bell windows, and the roof with its two gables
    wall(im, cx, 78, 101, 44)
    for x in range(cx - 38, cx + 38, 16):
        hl.stamp(im, BELL, x, 88)
    roof(im, cx, 56, 77, 30, 58)
    for gx in (cx - 26, cx + 26):
        gable(im, gx, 58, 14)
    # the top tier: its rail, its bell windows, the top roof and its gilt ridge ends
    wall(im, cx, 34, 55, 28)
    for x in range(cx - 20, cx + 20, 14):
        hl.stamp(im, BELL, x, 40)
    fill(im, (cx - 30, 50, cx + 29, 51), T('night', 1))                 # the balcony's rail
    for x in range(cx - 29, cx + 29, 3):
        fill(im, (x, 52, x, 55), T('night', 3))
    fill(im, (cx - 30, 52, cx + 29, 52), T('night', 4))
    roof(im, cx, 14, 33, 16, 40)
    fill(im, (cx - 18, 10, cx + 17, 13), T('steel', 1))                 # the ridge
    fill(im, (cx - 18, 10, cx + 17, 10), T('steel', 3))
    for x in (cx - 20, cx + 16):                                        # the shachihoko
        fill(im, (x, 5, x + 3, 12), T('gold', 2))
        fill(im, (x, 5, x, 12), T('gold', 3))
        fill(im, (x + 3, 7, x + 3, 12), T('gold', 1))
        fill(im, (x + 1, 4, x + 2, 4), T('gold', 3))
    hl.outline(im)
    return im


# ---- the Shirahige torii ----------------------------------------------------------------
def torii():
    im = hl.canvas(2 * C, 3 * C)
    red = lambda i: T('red', i)
    # the posts, wet at the foot
    for x0 in (10, 47):
        x1 = x0 + 6
        fill(im, (x0, 14, x1, 93), red(2))
        fill(im, (x0, 14, x0, 93), red(3))
        fill(im, (x1 - 1, 14, x1, 93), red(1))
        fill(im, (x0, 80, x1, 93), red(1))                              # wet
        fill(im, (x1 - 1, 80, x1, 93), red(0))
        fill(im, (x0, 80, x0, 93), red(2))
        fill(im, (x0 - 2, 86, x1 + 2, 86), T('blue', 4))                # the ripple round it
        fill(im, (x0 - 1, 87, x1 + 1, 87), T('blue', 5))
    # the second lintel, its wedges, the strut
    fill(im, (5, 24, 58, 28), red(2))
    fill(im, (5, 24, 58, 24), red(3))
    fill(im, (5, 28, 58, 28), red(1))
    for x in (8, 55):
        fill(im, (x, 25, x, 27), red(0))
    fill(im, (29, 14, 34, 23), red(2))
    fill(im, (29, 14, 29, 23), red(3))
    fill(im, (34, 14, 34, 23), red(1))
    fill(im, (30, 16, 33, 21), T('night', 3))                           # the plaque
    fill(im, (30, 16, 33, 16), T('night', 4))
    # the top lintel under its dark cap, the ends swept up
    fill(im, (3, 10, 60, 13), red(2))
    fill(im, (3, 10, 60, 10), red(3))
    fill(im, (3, 13, 60, 13), red(1))
    fill(im, (2, 6, 61, 9), T('night', 2))
    fill(im, (2, 6, 61, 6), T('night', 4))
    fill(im, (2, 4, 5, 6), T('night', 2))
    fill(im, (58, 4, 61, 6), T('night', 2))
    fill(im, (2, 4, 3, 4), T('night', 4))
    fill(im, (58, 4, 59, 4), T('night', 4))
    hl.outline(im)
    return im


# ---- the tunnel at the north end --------------------------------------------------------
CLUMP = ['.hhh..',
         'hhbbb.',
         'hbbbbl',
         'bbbbll',
         '.blll.']


def tunnel():
    im = hl.canvas(4 * C, 3 * C)
    # the hillside: a mound of woodland down to the bottom edge
    for y in range(3, 3 * C):
        inset = max(0, 18 - y) // 2
        bump = (y * 5) % 3 if y < 20 else 0
        fill(im, (1 + inset + bump, y, 126 - inset - bump, y), T('green', 1))
    clump = hl.pixmap(CLUMP, {'h': T('green', 4), 'b': T('green', 3), 'l': T('green', 2)})
    for j, y in enumerate(range(4, 92, 5)):
        for x in range(2 + (j % 2) * 3 + (j * 7) % 4, 122, 7):
            if im.getpixel((min(127, x + 2), min(95, y + 2)))[3]:
                hl.stamp(im, clump, x, y)
    # the concrete portal and its headwall
    fill(im, (22, 26, 105, 95), T('steel', 4))
    hl.scanlines(im, (23, 29, 104, 95), T('steel', 4), T('steel', 3))
    fill(im, (22, 26, 105, 27), T('steel', 5))
    fill(im, (22, 28, 105, 28), T('steel', 2))                          # the coping's shadow
    fill(im, (22, 26, 22, 95), T('steel', 5))
    fill(im, (104, 26, 105, 95), T('steel', 2))
    # the mouth, two cells wide, arched, open to the bottom edge
    for y in range(38, 3 * C):
        step = {38: 12, 39: 8, 40: 5, 41: 3, 42: 2, 43: 1}.get(y, 0)
        fill(im, (31 + step, y, 96 - step, y), T('steel', 1))           # the ring
        if y > 39:
            s = {40: 9, 41: 6, 42: 4, 43: 3, 44: 2, 45: 1}.get(y, 0)
            fill(im, (33 + s, y, 94 - s, y), T('night', 0) if y > 52 else T('night', 2))
    fill(im, (34, 53, 93, 54), T('night', 1))
    for y in range(80, 3 * C):                                          # the road running in
        w = (y - 80) // 2
        fill(im, (52 - w, y, 75 + w, y), T('night', 3) if y % 4 else T('night', 2))
    fill(im, (63, 82, 64, 85), T('gold', 2))                            # its centre line
    fill(im, (63, 90, 64, 95), T('gold', 2))
    # something is moving on the roof
    monkey = hl.pixmap(['.bb.', 'bpbb', 'bbbb', '.bb.'], {'b': T('gold', 1), 'p': T('pink', 2)})
    hl.stamp(im, monkey, 84, 22)
    hl.outline(im)
    return im


# ---- a monkey ----------------------------------------------------------------------------
MONKEY = ['....hhhhh.....',
          '...hhbbbbb....',
          '..hbfffffbl...',
          '..hfPPPPPfl...',
          '..hfePPePfl...',
          '..hfPPpPPfl...',
          '...hfPPPfl....',
          '...hhfffbl....',
          '..hhbbbbbll...',
          '.hhbbbbbbbll..',
          '.hbbbbbbbbbl..',
          'hbbbbbbbbbbbl.',
          'hbbffbbbbffbl.',
          'hbbPPbbbbPPbl.',
          '.bblllllllll.l',
          '..lll..llll..l',
          '............ll']


def monkey():
    im = hl.canvas(C, C)
    pic = hl.pixmap(MONKEY, {'h': T('gold', 3), 'b': T('gold', 2), 'l': T('gold', 1), 'f': T('cream', 2),
                             'P': T('pink', 2), 'p': T('pink', 1), 'e': T('night', 2)})
    hl.stamp(im, pic, 9, 12)
    hl.outline(im)
    return im


# ---- the Biwaichi sign ------------------------------------------------------------------
BIKE = ['......xxx...xx...',
        '.......x.....x...',
        '.......xxxxxxx...',
        '..xxx.x.x...x.xxx.',
        '.x...x...x.x.x...x',
        'x...x.x...xx.x....x',
        'x...xxxxxxxx.x....x',
        'x.....x......x....x',
        '.x...x........x..x.',
        '..xxx..........xx..']


def cycle_sign():
    im = hl.canvas(C, 2 * C)
    fill(im, (14, 26, 17, 60), T('steel', 3))                           # the pole
    fill(im, (14, 26, 14, 60), T('steel', 4))
    fill(im, (17, 26, 17, 60), T('steel', 2))
    fill(im, (12, 59, 19, 61), T('steel', 2))
    fill(im, (12, 59, 19, 59), T('steel', 4))
    fill(im, (3, 4, 28, 27), T('blue', 2))                              # the board
    hl.scanlines(im, (4, 5, 27, 26), T('blue', 2), T('blue', 3))
    hl.bevel(im, (3, 4, 28, 27), hl.material('blue', 2))
    fill(im, (5, 21, 26, 24), T('blue', 1))                             # the band along its foot
    fill(im, (7, 22, 24, 23), T('blue', 5))
    pic = hl.pixmap(BIKE, {'x': T('cream', 3)})
    hl.stamp(im, pic, 7, 8, T('blue', 0))                               # its shadow, then the bicycle
    hl.stamp(im, pic, 6, 7)
    hl.outline(im)
    return im


# ---- the stubble of a harvested paddy -----------------------------------------------------
def paddy():
    im = hl.canvas(C, C)
    px = im.load()
    for y in range(C):
        for x in range(C):
            r, s = y % 4, (x + (y // 4) % 2 * 2) % 4
            if r == 0:
                c = T('gold', 0)                                        # the furrow's shade
            elif r == 1:
                c = T('gold', 3) if s == 0 else T('gold', 2) if s == 1 else T('gold', 1)
            elif r == 2:
                c = T('gold', 2) if s in (0, 1) else T('gold', 1)
            else:
                c = T('gold', 1) if s != 3 else T('cream', 0)
            px[x, y] = c
    for x, y in ((5, 6), (21, 14), (13, 26), (29, 2)):                  # straw left on the field
        px[x, y] = T('gold', 4)
        px[(x + 1) % C, y] = T('gold', 3)
    return im


# ---- Takashima's station sign -------------------------------------------------------------
def station_sign():
    im = hl.canvas(2 * C, 2 * C)
    for x0 in (11, 49):                                                 # the posts
        fill(im, (x0, 34, x0 + 3, 61), T('steel', 3))
        fill(im, (x0, 34, x0, 61), T('steel', 4))
        fill(im, (x0 + 3, 34, x0 + 3, 61), T('steel', 2))
    fill(im, (2, 4, 61, 35), T('steel', 3))                             # the frame
    fill(im, (2, 4, 61, 4), T('steel', 5))
    fill(im, (2, 4, 2, 35), T('steel', 5))
    fill(im, (61, 4, 61, 35), T('steel', 2))
    fill(im, (2, 35, 61, 35), T('steel', 1))
    hl.shade(im, (4, 6, 59, 25), hl.material('cream', 2), part=5)       # the white face
    fill(im, (4, 6, 59, 6), T('cream', 3))
    fill(im, (4, 26, 59, 33), T('blue', 2))                             # the blue band
    fill(im, (4, 26, 59, 26), T('blue', 3))
    fill(im, (4, 33, 59, 33), T('blue', 1))
    for x in (7, 50):                                                   # the neighbours, either way
        fill(im, (x, 29, x + 6, 30), T('cream', 3))
    fill(im, (6, 29, 6, 30), T('cream', 3))
    fill(im, (57, 29, 57, 30), T('cream', 3))
    w, _ = hl.text_size('たかしま')
    hl.text(im, (64 - w) // 2, 10, 'たかしま', T('night', 3))
    hl.outline(im)
    return im


# ---- the fingerpost by the seam -------------------------------------------------------------
def fingerpost():
    im = hl.canvas(C, 2 * C)
    fill(im, (14, 6, 17, 60), T('cream', 1))                            # the post
    fill(im, (14, 6, 14, 60), T('cream', 2))
    fill(im, (17, 6, 17, 60), T('cream', 0))
    fill(im, (13, 4, 18, 5), T('cream', 0))
    fill(im, (12, 58, 19, 61), T('steel', 3))                           # its footing
    fill(im, (12, 58, 19, 58), T('steel', 4))
    for y0, x0, x1, tip in ((10, 8, 26, 'e'), (22, 4, 22, 'w')):        # the arms: north, south
        fill(im, (x0, y0, x1, y0 + 6), T('gold', 2))
        fill(im, (x0, y0, x1, y0), T('gold', 3))
        fill(im, (x0, y0 + 6, x1, y0 + 6), T('gold', 0))
        hl.scanlines(im, (x0 + 2, y0 + 2, x1 - 2, y0 + 4), T('gold', 1), T('gold', 2))
        for i in range(4):                                              # the pointed end
            x = x1 + 1 + i if tip == 'e' else x0 - 1 - i
            fill(im, (x, y0 + i, x, y0 + 6 - i), T('gold', 2) if i < 3 else T('gold', 1))
    hl.outline(im)
    return im


SPRITES = {
    'biwa-hikone-keep_0_0': hikone_keep,
    'biwa-torii_0_0': torii,
    'biwa-tunnel_0_0': tunnel,
    'biwa-monkey_0_0': monkey,
    'biwa-cycle-sign_0_0': cycle_sign,
    'biwa-paddy_0_0': paddy,
    'biwa-station-sign_0_0': station_sign,
    'biwa-fingerpost_0_0': fingerpost,
}
# worth looking up at (config game.lookUp.sprites: family -> 0 for a one-sprite landmark)
LOOK_UP = {'biwa-hikone-keep': 0}


def main():
    built = {}
    for key, fn in SPRITES.items():
        im = hl.double(fn())
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')
    art_register.register(built)
    cfg = json.load(open('config.json'))
    looks = cfg['game'].setdefault('lookUp', {}).setdefault('sprites', {})
    if any(looks.get(k) != v for k, v in LOOK_UP.items()):
        looks.update(LOOK_UP)
        open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        hl.sheet(list(built.values()), out, width=1400)
        print('preview ->', out)


if __name__ == '__main__':
    main()
