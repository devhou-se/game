#!/usr/bin/env python3
"""extract_street.py — the street accessories of issue #19: zebra crossings,
traffic lights, a handful of iconic kerbside props, and the izakaya stool.

  crossing-h-top/-mid/-bottom_0_0   zebra crossing over a HORIZONTAL road (one
                                    piece per road row: kerb, centre, kerb)
  crossing-v-left/-mid/-right_0_0   the same over a VERTICAL road
      GuttyKreum Temples & Shrines GK_TS_A5 — the sheet the game's road-edge /
      road-div tiles were cut from, so the asphalt and kerb match exactly.
      (The Japanese City pack's GK_JC_A5_2 has the same crossings on a much
      darker asphalt; do not use that one.)

  road-mirror_0_0    1x2  orange convex traffic mirror   (Urban Accessories)
  bus-stop_0_0       1x1  bus-stop pole with its timetable box
  bicycle-blue/-orange_0_0, scooter-grey/-red_0_0   1x1  parked two-wheelers
  traffic-cone_0_0   1x1  striped cone
  utility-pole_0_0   1x3  wooden pole with a transformer (Japanese City GK_JC_B_2)
  nara-deer-doe_0_0, nara-deer-stag_0_0   1x1  the two deer resting on the
                     grass, for Nara's park (issue #268)
      All at the 2x scale of every other GuttyKreum prop (one 32px sheet tile =
      one 64px cell), bottom-aligned in their cell(s) so they stand on the
      ground row. No bins: the packs' rubbish bins / dumpsters are deliberately
      not extracted (issue #19, "definitely no rubbish bins") and
      `node tools/play.js lint` fails a room that places one.

  traffic-light_0_0 (+ -amber, -stop, -stop-blink)   1x3
      DRAWN here, not extracted: no GuttyKreum sheet has a traffic signal, and
      the only signal art in the repo (LimeZu Modern Exteriors) is a western
      vertical head in 16px art, twice the pixel size of everything around it.
      This is a Japanese signal in the GuttyKreum palette on the same 2x pixel
      grid: a horizontal three-lamp vehicle head (blue-green on the LEFT, red
      on the right) on a pole, with the two-lamp pedestrian signal and a push
      button box below it. The four keys are the frames src/TrafficLights.js
      swaps between; maps place `traffic-light_0_0` only.

  izakaya-stool_0_0  1x1  a round wooden stool for the Izakaya, drawn in the
      interior pack's 4x pixel style and counter palette (it replaces the
      office-bin sprite that used to stand in for one).

Registers every key in config.json spriteMetadata + tileNames (the game only
loads a tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py:
    python3 tools/extract_street.py [--preview out.png]
"""
import json, sys
from PIL import Image, ImageDraw

GK = '../art-source/GuttyKreum/'
SHEETS = {
    'road':  GK + 'TemplesandShrinesv2/RPGMakerVXAce/GK_TS_A5.png',
    'urban': GK + 'UrbanAccessoriesv2/Tilemap.png',
    'city':  GK + 'JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_B_2.png',
}
T = 32          # one sheet tile = one game cell, in sheet pixels
SCALE = 2       # sheet pixel -> game pixel
_sheet = {}


def sheet(name):
    if name not in _sheet:
        _sheet[name] = Image.open(SHEETS[name]).convert('RGBA')
    return _sheet[name]


# ---- zebra crossings: whole road tiles, (column, row) on GK_TS_A5 ------------
#      The sheet's own top / left kerb tiles (1,2) and (3,5) carry heavy worn-paint
#      detail: their second stripe is chewed into a row of diagonal holes that reads
#      as a rendering glitch at game scale. The bottom / right kerb tiles are clean
#      and their kerb is the exact mirror image, so the top / left tiles are those,
#      flipped (third field: a PIL transpose). ----
CROSSINGS = {
    'crossing-h-top':    (1, 4, Image.FLIP_TOP_BOTTOM),
    'crossing-h-mid':    (1, 3, None),
    'crossing-h-bottom': (1, 4, None),
    'crossing-v-left':   (5, 5, Image.FLIP_LEFT_RIGHT),
    'crossing-v-mid':    (4, 5, None),
    'crossing-v-right':  (5, 5, None),
}

# ---- props: name -> (sheet, crop rect in sheet px, cells wide, cells tall).
#      The art inside the rect is re-seated: centred, feet 2px above the cell's
#      bottom edge, so a prop stands in its cell instead of floating in it. ----
PROPS = {
    'road-mirror':    ('urban', (128, 64, 160, 128), 1, 2),
    'bus-stop':       ('urban', (64, 256, 96, 288), 1, 1),
    'bicycle-blue':   ('urban', (96, 256, 128, 288), 1, 1),
    'bicycle-orange': ('urban', (128, 256, 160, 288), 1, 1),
    'scooter-grey':   ('urban', (160, 224, 192, 256), 1, 1),
    'scooter-red':    ('urban', (192, 224, 224, 256), 1, 1),
    'traffic-cone':   ('urban', (96, 384, 128, 416), 1, 1),
    'utility-pole':   ('city',  (480, 160, 512, 256), 1, 3),
    # Nara's deer (issue #268): the two resting on the grass
    'nara-deer-doe':  ('urban', (0, 128, 32, 160), 1, 1),
    'nara-deer-stag': ('urban', (32, 128, 64, 160), 1, 1),
}


def crossing(col, row, flip=None):
    tile = sheet('road').crop((col * T, row * T, col * T + T, row * T + T))
    return tile.transpose(flip) if flip is not None else tile


def prop(src, box, w, h):
    art = sheet(src).crop(box)
    art = art.crop(art.getbbox())
    assert art.width <= w * T and art.height <= h * T, (box, art.size)
    out = Image.new('RGBA', (w * T, h * T), (0, 0, 0, 0))
    out.alpha_composite(art, ((w * T - art.width) // 2, h * T - 2 - art.height))
    return out


# ---- the traffic light, drawn at sheet scale (32x96) in the pack's palette ----
OUT   = (10, 22, 39, 255)        # the packs' prop outline
POLE  = (120, 118, 138, 255)
POLEL = (162, 163, 189, 255)
POLED = (65, 63, 83, 255)
HOUSE = (44, 45, 81, 255)        # signal housing
HOOD  = (31, 31, 59, 255)
OFF   = (65, 63, 83, 255)        # an unlit lamp
OFFL  = (86, 92, 122, 255)
WHITE = (225, 233, 235, 255)
LAMPS = {                        # lit lamp: (body, highlight)
    'green': ((84, 196, 160, 255), (177, 235, 214, 255)),
    'amber': ((240, 190, 84, 255), (252, 232, 170, 255)),
    'red':   ((226, 84, 66, 255), (245, 160, 140, 255)),
}
BUTTON = (198, 170, 113, 255)
BUTTOND = (167, 132, 59, 255)

# the two figures of the pedestrian signal, 6x7
STAND = ['..##..', '..##..', '.####.', '.####.', '..##..', '..##..', '..##..']
WALK  = ['..##..', '..##..', '.###..', '#.###.', '..##..', '.#..#.', '#...#.']

# frame -> (vehicle lamp lit, pedestrian lamp lit)
FRAMES = {
    'traffic-light':            ('green', 'red'),
    'traffic-light-amber':      ('amber', 'red'),
    'traffic-light-stop':       ('red', 'green'),
    'traffic-light-stop-blink': ('red', None),
}


def traffic_light(vehicle, ped):
    im = Image.new('RGBA', (T, 3 * T), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    R = lambda x0, y0, x1, y1, c: d.rectangle([x0, y0, x1, y1], fill=c)

    # concrete foot + pole (bottom cell is the solid one)
    R(10, 88, 21, 93, OUT); R(11, 89, 20, 92, POLE); R(11, 89, 20, 89, POLEL)
    R(13, 16, 18, 88, OUT); R(14, 16, 17, 88, POLE); R(14, 16, 14, 88, POLEL); R(17, 16, 17, 88, POLED)

    # vehicle head: hooded horizontal housing, three lamps - green, amber, red
    R(1, 3, 30, 17, OUT); R(2, 4, 29, 16, HOUSE); R(2, 4, 29, 5, HOOD)
    for i, name in enumerate(('green', 'amber', 'red')):
        x = 4 + i * 9
        R(x - 1, 6, x + 6, 15, OUT)
        body, hi = LAMPS[name] if name == vehicle else (OFF, OFFL)
        R(x, 8, x + 5, 14, body); R(x, 7, x + 5, 7, HOOD)        # the visor's shadow
        R(x + 1, 9, x + 2, 10, hi)

    # pedestrian head: red standing figure over green walking figure
    R(9, 26, 22, 51, OUT); R(10, 27, 21, 50, HOUSE)
    for y, name, fig in ((28, 'red', STAND), (40, 'green', WALK)):
        lit = name == ped
        R(11, y, 20, y + 9, LAMPS[name][0] if lit else OFF)
        for j, line in enumerate(fig):
            for i, ch in enumerate(line):
                if ch == '#':
                    im.putpixel((13 + i, y + 1 + j), WHITE if lit else OFFL)
    R(11, 38, 20, 39, OUT)

    # push-button box
    R(11, 60, 20, 68, OUT); R(12, 61, 19, 67, BUTTON); R(12, 66, 19, 67, BUTTOND)
    R(15, 63, 16, 64, LAMPS['red'][0])
    return im


# ---- the izakaya stool: 16px art (4x), in the office-counter palette ----------
WOOD, WOODL, WOODD, WOODO = (199, 135, 73, 255), (233, 189, 142, 255), (163, 96, 67, 255), (71, 48, 48, 255)
STOOL = [
    '................',
    '................',
    '................',
    '....oooooooo....',
    '...ollllllllo...',
    '..olllwwwwwwwo..',
    '..owwwwwwwwwwo..',
    '..owwwwwwwwwdo..',
    '...oddddddddo...',
    '...oooooooooo...',
    '...ow......wo...',
    '...ow.oooo.wo...',
    '...owoddddowo...',
    '...ow.oooo.wo...',
    '...od......do...',
    '...oo......oo...',
]


def stool():
    pal = {'o': WOODO, 'w': WOOD, 'l': WOODL, 'd': WOODD}
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, line in enumerate(STOOL):
        for x, ch in enumerate(line):
            if ch in pal:
                im.putpixel((x, y), pal[ch])
    return im.resize((64, 64), Image.NEAREST)


def build():
    """-> {key: (tile name, 64px-cell image)}"""
    up = lambda im: im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
    out = {}
    for name, (col, row, flip) in CROSSINGS.items():
        out[f'{name}_0_0'] = (name, up(crossing(col, row, flip)))
    for name, spec in PROPS.items():
        out[f'{name}_0_0'] = (name, up(prop(*spec)))
    for name, (vehicle, ped) in FRAMES.items():
        out[f'{name}_0_0'] = (name, up(traffic_light(vehicle, ped)))
    out['izakaya-stool_0_0'] = ('izakaya-stool', stool())
    return out


def main(argv):
    sprites = build()
    if '--preview' in argv:
        path = argv[argv.index('--preview') + 1]
        sheet_w = sum(im.width + 16 for _, im in sprites.values()) + 16
        prev = Image.new('RGBA', (sheet_w, 192 + 32), (83, 89, 109, 255))
        x = 16
        for _, im in sprites.values():
            prev.alpha_composite(im, (x, 16 + 192 - im.height)); x += im.width + 16
        prev.save(path)
        print(f'preview -> {path}'); return
    cfg = json.load(open('config.json'))
    for key, (name, im) in sprites.items():
        assert im.width % 64 == 0 and im.height % 64 == 0, (key, im.size)
        im.save(f'assets/sprites/{key}.png')
        # multi-cell sprites anchor on the centre of their top-left cell (not rounded:
        # a rounded anchor puts a tall sprite a fraction of a pixel off the grid)
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = name
        print(f'{key}: {im.width // 64}x{im.height // 64} cells')
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


if __name__ == '__main__':
    main(sys.argv)
