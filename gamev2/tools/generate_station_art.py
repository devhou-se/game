#!/usr/bin/env python3
"""generate_station_art.py — the station interior's walls, ticket gates, signs
and the in-station 7-Eleven kiosk (issue #206): the pieces the GuttyKreum Train
Station pack does not have (tools/extract_station.py cuts the ones it has).

Shaded pixel art in the pack's palette with a 1px ink outline, drawn at half
size (32px a cell) and pixel-doubled, the way tools/generate_hokkaido.py draws
its landmarks. Nothing here is line art, and nothing reads a system font: the
text is set in the game's own fonts (fonts/PressStart2P-Regular.ttf, and
fonts/PixelMplus12-Grid.ttf for Japanese at its native 12px), so a re-run is
byte-identical on any machine.

  station-wall-orange / -green   back wall behind the track, 1x2, the line's
                                 colour as its band (main line / branch line)
  station-wall-front             the front wall seen from inside, 1x2
  station-concourse              the concourse's floor tile
  station-gate, -gate-end-w/-e   a ticket gate you walk through (1x2, feet on
                                 the gate row) and the cabinet halves that end
                                 a row of them
  station-ticket-machines        3x2 bank of ticket machines under a fare map
  station-kiosk                  4x3 7-Eleven kiosk: its counter sells
                                 (src/utils/Interactions.js)
  station-pillar                 1x2 concourse column
  station-lamp-post              1x2 platform lamp (lit at night: DayNight
                                 puts a halo on every *lamp-post* tile)
  station-clock, -departures, -exit-sign, -platform-sign
                                 hanging signs (Tops layer)
  station-door-mark              where the train's doors stop (Over Floor)
  station-lockers                2x2 coin lockers
  station-name-<town>            3x1 name board for EVERY station in
                                 generate_stations.py's STATIONS table, with
                                 the Japanese name from STATION_JA when it has
                                 one — a new station gets its board by
                                 re-running this tool

Run from gamev2/:  python3 tools/generate_station_art.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import ast
import json
import sys

from PIL import Image, ImageDraw, ImageFont

C = 32      # canvas px per cell (doubled on save)

INK = (38, 43, 68)
SLATE, SLATE_DARK = (95, 107, 133), (74, 84, 110)
STEEL_LIGHT, STEEL, STEEL_DARK = (198, 203, 216), (150, 158, 178), (104, 113, 140)
CREAM, CREAM_SHADE, CREAM_DARK = (236, 229, 210), (208, 199, 180), (170, 162, 150)
WHITE, OFFWHITE = (250, 250, 246), (226, 228, 234)
VOID = (16, 18, 30)
ORANGE, ORANGE_DARK = (217, 106, 60), (168, 76, 48)
GREEN, GREEN_DARK = (112, 150, 84), (78, 112, 66)
RED, RED_DARK = (206, 62, 58), (150, 44, 52)
YELLOW, YELLOW_DARK = (240, 196, 60), (190, 146, 44)
BLUE, BLUE_DARK, CYAN = (62, 96, 168), (44, 66, 122), (126, 200, 232)
LED_AMBER, LED_GREEN = (255, 170, 40), (120, 230, 110)
LINE = {'train-orange': (ORANGE, ORANGE_DARK), 'train-green': (GREEN, GREEN_DARK)}

_FONTS = {}


def font(name, size):
    if (name, size) not in _FONTS:
        _FONTS[name, size] = ImageFont.truetype(f'fonts/{name}.ttf', size)
    return _FONTS[name, size]


def latin(size=8):
    return font('PressStart2P-Regular', size)


def kana(size=12):
    return font('PixelMplus12-Grid', size)


def new(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'        # no anti-aliasing: pixel fonts stay pixels
    return im, d


def box(d, x0, y0, x1, y1, fill, outline=INK):
    """A filled rectangle with an ink outline; corners inclusive."""
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)


def text_w(d, s, f):
    return int(d.textlength(s, font=f))


def text(d, x, y, s, f, fill):
    """Text with its top-left ink pixel at (x, y), whatever the font's bearings."""
    l, t, _, _ = d.textbbox((0, 0), s, font=f)
    d.text((x - l, y - t), s, font=f, fill=fill)


def text_size(d, s, f):
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    return r - l, b - t


def centred(d, cx, y, s, f, fill):
    w, _ = text_size(d, s, f)
    text(d, cx - w // 2, y, s, f, fill)


# ---- walls and floor -----------------------------------------------------------

def wall(line):
    main, dark = LINE[line]

    def draw():
        im, d = new(C, 2 * C)
        d.rectangle([0, 0, 31, 3], fill=STEEL_DARK)
        d.line([0, 0, 31, 0], fill=INK)
        d.rectangle([0, 4, 31, 27], fill=CREAM)                 # upper tiles
        d.line([0, 4, 31, 4], fill=WHITE)
        d.line([0, 16, 31, 16], fill=CREAM_SHADE)
        for x in (0, 16):
            d.line([x, 5, x, 27], fill=CREAM_SHADE)
        d.rectangle([0, 28, 31, 35], fill=main)                 # the line's band
        d.line([0, 28, 31, 28], fill=INK)
        d.line([0, 35, 31, 35], fill=INK)
        d.line([0, 34, 31, 34], fill=dark)
        d.rectangle([0, 36, 31, 55], fill=OFFWHITE)             # dado
        d.line([0, 46, 31, 46], fill=STEEL_LIGHT)
        for x in (8, 24):
            d.line([x, 36, x, 55], fill=STEEL_LIGHT)
        d.rectangle([0, 56, 31, 63], fill=STEEL_DARK)           # skirting
        d.line([0, 56, 31, 56], fill=INK)
        d.line([0, 63, 31, 63], fill=INK)
        return im
    return draw


def wall_front():
    """The front wall from inside: all you see is its top; the rest is dark."""
    im, d = new(C, 2 * C)
    d.rectangle([0, 0, 31, 63], fill=VOID)
    d.rectangle([0, 0, 31, 9], fill=STEEL)
    d.line([0, 0, 31, 0], fill=INK)
    d.line([0, 1, 31, 1], fill=STEEL_LIGHT)
    d.rectangle([0, 8, 31, 9], fill=STEEL_DARK)
    d.line([0, 10, 31, 10], fill=INK)
    d.line([0, 1, 0, 7], fill=STEEL_DARK)
    return im


def concourse():
    im, d = new(C, C)
    d.rectangle([0, 0, 31, 31], fill=(206, 208, 216))
    for a in (0, 16):
        d.line([a, 0, a, 31], fill=(184, 187, 200))
        d.line([0, a, 31, a], fill=(184, 187, 200))
    for x, y in ((5, 6), (22, 3), (11, 21), (27, 26), (19, 12), (3, 28)):   # terrazzo flecks
        d.point((x, y), fill=(190, 193, 205))
    for x, y in ((9, 10), (25, 19), (6, 24)):
        d.point((x, y), fill=(220, 222, 228))
    return im


# ---- ticket gates --------------------------------------------------------------

def _cabinet(d, x0, x1):
    """One gate cabinet between x0..x1 (canvas columns, may run off the tile)."""
    box(d, x0, 26, x1, 47, STEEL_LIGHT)                         # top
    d.line([x0 + 1, 27, x1 - 1, 27], fill=WHITE)
    d.rectangle([x0 + 2, 40, x1 - 2, 44], fill=BLUE)            # IC reader
    d.rectangle([x0 + 2, 40, x1 - 2, 40], fill=CYAN)
    d.rectangle([x0 + 2, 30, x1 - 2, 33], fill=INK)             # ticket slot
    box(d, x0, 47, x1, 60, STEEL)                               # front
    d.rectangle([x0 + 1, 57, x1 - 1, 59], fill=STEEL_DARK)
    d.rectangle([x0 + 3, 50, x1 - 3, 54], fill=LED_GREEN)       # go light
    d.line([x0, 61, x1, 61], fill=SLATE_DARK)                   # shadow on the floor


def gate():
    """A ticket gate: half a cabinet either side (two gates side by side make
    one whole cabinet between them), the open flaps, and the walk-through."""
    im, d = new(C, 2 * C)
    _cabinet(d, -7, 6)
    _cabinet(d, 25, 38)
    for x0, x1 in ((7, 10), (21, 24)):                          # retracted flaps
        box(d, x0, 36, x1, 45, CYAN)
        d.line([x0 + 1, 37, x1 - 1, 37], fill=WHITE)
    return im


def gate_end(side):
    """The cell beside a row of gates: the other half of the last cabinet and
    a tube railing (the pack's colours) running on from it."""
    def draw():
        im, d = new(C, 2 * C)
        for y in (49, 53, 57):
            d.line([0, y, 31, y], fill=INK)
            d.line([0, y + 1, 31, y + 1], fill=OFFWHITE if y == 49 else STEEL_DARK)
        if side == 'w':
            _cabinet(d, 25, 38)
            d.rectangle([0, 47, 1, 60], fill=INK)
        else:
            _cabinet(d, -7, 6)
            d.rectangle([30, 47, 31, 60], fill=INK)
        return im
    return draw


# ---- furniture -----------------------------------------------------------------

def ticket_machines():
    im, d = new(3 * C, 2 * C)
    box(d, 0, 0, 95, 30, OFFWHITE)                              # the fare map
    d.rectangle([1, 1, 94, 13], fill=BLUE)
    text(d, 4, 2, 'きっぷ', kana(), WHITE)
    text(d, 46, 4, 'TICKET', latin(), WHITE)
    for y, col, xs in ((18, ORANGE, (6, 20, 36, 52, 70, 88)), (22, GREEN, (12, 28, 44)),
                       (26, BLUE, (30, 48, 62, 80))):
        d.line([xs[0], y, xs[-1], y], fill=col)
        for x in xs:
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=WHITE, outline=INK)
    d.line([28, 22, 36, 18], fill=GREEN)
    d.line([62, 26, 70, 18], fill=BLUE)
    for i in range(3):                                          # three machines
        x = i * 32
        box(d, x, 30, x + 31, 63, STEEL_LIGHT)
        d.line([x + 1, 31, x + 30, 31], fill=WHITE)
        box(d, x + 4, 33, x + 19, 45, BLUE_DARK)                # touch screen
        d.rectangle([x + 5, 34, x + 18, 36], fill=CYAN)
        for bx in (6, 11, 16):
            d.rectangle([x + bx, 38, x + bx + 2, 40], fill=YELLOW)
            d.rectangle([x + bx, 42, x + bx + 2, 44], fill=WHITE)
        box(d, x + 22, 33, x + 28, 37, INK)                     # coin slot, note slot
        d.rectangle([x + 23, 34, x + 27, 34], fill=YELLOW)
        box(d, x + 22, 40, x + 28, 45, STEEL)
        d.rectangle([x + 23, 42, x + 27, 42], fill=INK)
        box(d, x + 4, 48, x + 27, 54, INK)                      # ticket / change tray
        d.rectangle([x + 5, 52, x + 26, 53], fill=STEEL_DARK)
        d.rectangle([x + 1, 57, x + 30, 60], fill=GREEN)
        d.rectangle([x + 1, 60, x + 30, 60], fill=GREEN_DARK)
    return im


def kiosk():
    """The in-station 7-Eleven: a striped fascia, the open booth with stocked
    shelves, and the counter you buy at. 4x3 cells, solid."""
    im, d = new(4 * C, 3 * C)
    W = 4 * C
    # roof edge + fascia
    box(d, 0, 0, W - 1, 4, STEEL_DARK)
    box(d, 0, 4, W - 1, 27, WHITE)
    d.rectangle([1, 7, W - 2, 10], fill=ORANGE)
    d.rectangle([1, 12, W - 2, 16], fill=GREEN)
    d.rectangle([1, 18, W - 2, 21], fill=RED)
    d.rectangle([1, 25, W - 2, 26], fill=OFFWHITE)
    # the logo plate: a red-and-orange 7 with the green name across it
    box(d, 22, 5, 42, 26, WHITE)
    d.rectangle([26, 8, 38, 10], fill=ORANGE)
    d.rectangle([34, 11, 37, 14], fill=RED)
    d.rectangle([32, 15, 35, 18], fill=RED)
    d.rectangle([30, 19, 33, 23], fill=RED)
    d.rectangle([24, 13, 40, 17], fill=WHITE)
    d.rectangle([24, 14, 40, 16], fill=GREEN)
    box(d, 46, 8, 110, 22, WHITE)
    centred(d, 78, 12, 'ELEVEn', latin(), GREEN_DARK)
    # booth: side posts, dark inside, three shelves of stock
    box(d, 0, 27, W - 1, 66, (52, 58, 86))
    box(d, 0, 27, 5, 95, OFFWHITE)
    box(d, W - 6, 27, W - 1, 95, OFFWHITE)
    d.line([1, 28, 4, 28], fill=WHITE)
    d.line([W - 5, 28, W - 2, 28], fill=WHITE)
    stock = [RED, YELLOW, CYAN, GREEN, ORANGE, WHITE, BLUE, YELLOW, RED, GREEN, CYAN, ORANGE]
    for row, y in enumerate((30, 42, 54)):
        d.rectangle([7, y + 9, W - 8, y + 10], fill=STEEL)
        d.line([7, y + 11, W - 8, y + 11], fill=INK)
        x, i = 9, row * 5
        while x < W - 14:
            wdt = (3, 4, 2, 5)[(i + row) % 4]
            hgt = (7, 6, 8, 5)[(i * 3 + row) % 4]
            col = stock[i % len(stock)]
            d.rectangle([x, y + 9 - hgt, x + wdt - 1, y + 8], fill=col)
            d.line([x, y + 9 - hgt, x + wdt - 1, y + 9 - hgt], fill=WHITE)
            x += wdt + 1
            i += 1
    # the lit strip under the fascia
    d.rectangle([6, 28, W - 7, 28], fill=(255, 244, 200))
    # counter: top, then the front with its stripe; register, hot case, papers
    box(d, 3, 66, W - 4, 74, CREAM)
    d.line([4, 67, W - 5, 67], fill=WHITE)
    box(d, 3, 74, W - 4, 95, OFFWHITE)
    d.rectangle([4, 78, W - 5, 80], fill=ORANGE)
    d.rectangle([4, 82, W - 5, 84], fill=GREEN)
    d.rectangle([4, 86, W - 5, 88], fill=RED)
    d.rectangle([4, 93, W - 5, 94], fill=STEEL)
    box(d, 12, 58, 30, 70, STEEL_DARK)                          # register
    box(d, 14, 54, 26, 60, INK)
    d.rectangle([15, 55, 25, 58], fill=LED_GREEN)
    d.rectangle([14, 63, 28, 67], fill=STEEL_LIGHT)
    box(d, 84, 52, 116, 70, STEEL_LIGHT)                        # hot food case
    d.rectangle([86, 54, 114, 66], fill=(255, 214, 140))
    for x in (89, 97, 105):
        d.rectangle([x, 59, x + 5, 64], fill=WHITE)
        d.rectangle([x, 63, x + 5, 64], fill=CREAM_SHADE)
    d.line([86, 60, 114, 60], fill=(255, 240, 200))
    for i, col in enumerate((WHITE, CREAM, WHITE, CYAN, YELLOW)):   # papers on the counter
        x = 40 + i * 8
        box(d, x, 62, x + 6, 70, col)
        d.line([x + 2, 65, x + 4, 65], fill=INK)
    box(d, 40, 76, 88, 91, BLUE_DARK)                           # the sign on the counter front
    centred(d, 64, 78, 'キオスク', kana(), WHITE)
    return im


def pillar():
    im, d = new(C, 2 * C)
    box(d, 5, 2, 26, 7, STEEL_LIGHT)                            # capital
    box(d, 8, 7, 23, 56, CREAM)
    d.rectangle([19, 8, 22, 55], fill=CREAM_SHADE)
    d.line([9, 8, 9, 55], fill=WHITE)
    box(d, 8, 18, 23, 25, BLUE)                                 # the band the signs hang on
    d.rectangle([9, 19, 22, 19], fill=CYAN)
    box(d, 6, 54, 25, 62, STEEL)                                # plinth
    d.line([7, 55, 24, 55], fill=STEEL_LIGHT)
    d.line([4, 63, 27, 63], fill=SLATE_DARK)
    return im


def lamp_post():
    """A platform lamp: a slim steel post with a twin lit head."""
    im, d = new(C, 2 * C)
    box(d, 4, 6, 27, 13, STEEL_DARK)
    d.rectangle([5, 10, 26, 12], fill=(255, 244, 200))
    d.line([5, 12, 26, 12], fill=YELLOW)
    box(d, 14, 13, 17, 58, STEEL)
    d.line([15, 14, 15, 57], fill=STEEL_LIGHT)
    box(d, 11, 56, 20, 62, STEEL_DARK)
    d.line([9, 63, 22, 63], fill=SLATE_DARK)
    return im


def clock():
    im, d = new(C, C)
    d.rectangle([15, 0, 16, 5], fill=INK)
    box(d, 6, 5, 25, 28, STEEL_DARK)
    d.ellipse([8, 7, 23, 26], fill=WHITE, outline=INK)
    for x, y in ((15, 9), (16, 9), (15, 24), (16, 24), (10, 16), (10, 17), (21, 16), (21, 17)):
        d.point((x, y), fill=INK)
    d.line([16, 17, 16, 11], fill=INK)          # ten past ten, like every clock in a shop
    d.line([15, 17, 11, 14], fill=INK)
    d.line([16, 17, 20, 13], fill=RED)
    return im


def departures():
    """The hanging LED departures board over the gates."""
    im, d = new(4 * C, C)
    for x in (10, 117):
        d.rectangle([x, 0, x + 1, 3], fill=INK)
    box(d, 0, 3, 127, 31, (20, 22, 30))
    d.rectangle([1, 4, 126, 4], fill=STEEL_DARK)
    text(d, 4, 6, '発車', kana(), LED_AMBER)
    text(d, 32, 8, 'DEPARTURES', latin(), LED_AMBER)
    d.line([3, 18, 124, 18], fill=(60, 64, 80))
    text(d, 4, 19, '電車がまいります', kana(), LED_GREEN)
    text(d, 104, 22, '>>', latin(), LED_GREEN)
    return im


def exit_sign():
    im, d = new(2 * C, C)
    for x in (8, 54):
        d.rectangle([x, 0, x + 1, 6], fill=INK)
    box(d, 1, 6, 62, 24, YELLOW)
    d.line([2, 23, 61, 23], fill=YELLOW_DARK)
    text(d, 4, 9, '出口', kana(), INK)
    text(d, 30, 11, 'EXIT', latin(), INK)
    return im


def platform_sign():
    im, d = new(2 * C, C)
    for x in (8, 54):
        d.rectangle([x, 0, x + 1, 6], fill=INK)
    box(d, 1, 6, 62, 24, BLUE_DARK)
    d.line([2, 7, 61, 7], fill=BLUE)
    d.ellipse([4, 8, 18, 22], fill=WHITE, outline=INK)
    text(d, 9, 11, '1', latin(), INK)
    text(d, 22, 9, 'のりば', kana(), WHITE)
    return im


def door_mark():
    """Painted on the platform where a door of the train stops."""
    im, d = new(C, C)
    d.rectangle([4, 2, 27, 3], fill=WHITE)
    d.rectangle([4, 2, 5, 16], fill=WHITE)
    d.rectangle([26, 2, 27, 16], fill=WHITE)
    for cx in (11, 20):
        for i in range(4):
            d.line([cx - i, 7 + i, cx + i, 7 + i], fill=WHITE)
        d.rectangle([cx - 1, 11, cx + 1, 15], fill=WHITE)
    return im


def lockers():
    im, d = new(2 * C, 2 * C)
    box(d, 1, 6, 62, 14, STEEL_LIGHT)                           # top
    d.line([2, 7, 61, 7], fill=WHITE)
    box(d, 1, 14, 62, 61, STEEL)
    for cx in range(4):
        for cy in range(3):
            x, y = 3 + cx * 15, 16 + cy * 15
            box(d, x, y, x + 13, y + 13, OFFWHITE if cy < 2 else STEEL_LIGHT)
            d.line([x + 1, y + 1, x + 12, y + 1], fill=WHITE)
            d.rectangle([x + 10, y + 6, x + 11, y + 8], fill=ORANGE if (cx + cy) % 3 else GREEN)
            d.point((x + 2, y + 7), fill=INK)
    d.line([0, 62, 63, 62], fill=SLATE_DARK)
    return im


def name_board(label, ja, line):
    """A station name board: Japanese over romaji when there is a Japanese
    name, the line's colour along the bottom, an arrow each way."""
    main, dark = LINE[line]

    def draw():
        im, d = new(3 * C, C)
        box(d, 2, 1, 93, 30, WHITE)
        d.line([3, 29, 92, 29], fill=OFFWHITE)
        d.rectangle([3, 24, 92, 28], fill=main)
        d.line([3, 28, 92, 28], fill=dark)
        for x, s in ((6, -1), (89, 1)):                         # the next-stop arrows
            for i in range(3):
                d.line([x - s * i, 26 - i, x - s * i, 26 + i], fill=WHITE)
        name = label.upper()
        if text_size(d, name, latin())[0] > 86:                 # a long name: mixed case, narrower face
            name, f = label, kana()
        else:
            f = latin()
        if ja:
            centred(d, 48, 2, ja, kana(), INK)
            centred(d, 48, 15 if f is latin() else 13, name, f, INK)
        else:
            centred(d, 48, 8 if f is latin() else 6, name, f, INK)
        return im
    return draw


# ---- the stations table ----------------------------------------------------------

def stations_table():
    """(STATIONS, STATION_JA) as written in generate_stations.py, read without
    running it (it rebuilds rooms on import)."""
    tree = ast.parse(open('tools/generate_stations.py').read())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                getattr(node.targets[0], 'id', None) in ('STATIONS', 'STATION_JA'):
            found[node.targets[0].id] = ast.literal_eval(node.value)
    return found['STATIONS'], found.get('STATION_JA', {})


def short_label(label):
    return label[:-len(' Station')] if label.endswith(' Station') else label


def name_key(station_key):
    """Sprite family of a station's name board: TokyoStation -> station-name-tokyo."""
    town = station_key[:-len('Station')] if station_key.endswith('Station') else station_key
    return f'station-name-{town.lower()}'


def sprites():
    out = {
        'station-wall-orange': wall('train-orange'),
        'station-wall-green': wall('train-green'),
        'station-wall-front': wall_front,
        'station-concourse': concourse,
        'station-gate': gate,
        'station-gate-end-w': gate_end('w'),
        'station-gate-end-e': gate_end('e'),
        'station-ticket-machines': ticket_machines,
        'station-kiosk': kiosk,
        'station-pillar': pillar,
        'station-lamp-post': lamp_post,
        'station-clock': clock,
        'station-departures': departures,
        'station-exit-sign': exit_sign,
        'station-platform-sign': platform_sign,
        'station-door-mark': door_mark,
        'station-lockers': lockers,
    }
    stations, ja = stations_table()
    for key, st in stations.items():
        out[name_key(key)] = name_board(short_label(st['label']), st.get('ja') or ja.get(key),
                                        st.get('train', 'train-orange'))
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
        ims = list(built.values())
        rows, x, y, rowh, width = [], 16, 16, 0, 1600
        for im in ims:
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
