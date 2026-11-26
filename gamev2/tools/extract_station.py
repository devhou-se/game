#!/usr/bin/env python3
"""extract_station.py — the station interior's floors, tracks and platform
furniture, cut from the GuttyKreum Train Station pack
(Assets/GuttyKreum/Train_Stationv8, the pack the trains come from — see
extract_train.py) into gamev2 sprites (issue #206).

The pack is 16px-native and a gamev2 cell is 64px, so everything is upscaled
4x NEAREST, like the trains that park beside it. Crop rectangles were read off
the sheet by hand (grid-overlay inspection).

  crops        station-floor, -ballast, -track-n / -track-s
               (one track is two rows: north rail, south rail), -stairs (2x2),
               -bench / -bench-back (2x2, the bench in the lower row),
               -board-map / -board-times (2x3 notice boards on legs),
               -postbox (2x3), -planter-a / -b (2x2), -cat (2x1, the station
               master)
  composed     station-platform-edge   the platform's north edge: coping,
                                       white line, yellow tactile strip
               station-tactile-v / -h / -stop   the yellow guide path laid on
                                       a floor (Over Floor overlays)
               station-railing-post / -mid / -end   tube railing, 1 cell each

A sprite that is wider than one cell anchors on the centre of its top-left
cell; one drawn smaller than its cells stands on the bottom of them.
The procedural half of the station art (walls, gates, kiosk, signs) is
tools/generate_station_art.py.

Run from gamev2/:  python3 tools/extract_station.py [--preview out.png]
Needs Pillow. Registers the sprites in config.json spriteMetadata + tileNames.
"""
import json
import sys

from PIL import Image

SHEET = '../Assets/GuttyKreum/Train_Stationv8/Tilemaps/Non-RPGMaker/Maintilemap.png'
K = 4       # 16px pack tile -> 64px cell

# key: (crop box on the sheet, canvas size in cells or None for the crop as it is)
CROPS = {
    'station-floor':       ((32, 0, 48, 16), None),
    'station-ballast':     ((0, 416, 16, 432), None),
    'station-track-n':     ((0, 448, 16, 464), None),
    'station-track-s':     ((0, 464, 16, 480), None),
    'station-stairs':      ((192, 96, 224, 128), None),
    'station-bench':       ((608, 32, 640, 56), (2, 2)),
    'station-bench-back':  ((576, 32, 608, 56), (2, 2)),
    'station-board-map':   ((544, 76, 576, 112), (2, 3)),
    'station-board-times': ((576, 76, 608, 112), (2, 3)),
    'station-postbox':     ((260, 63, 284, 90), (2, 3)),
    'station-planter-a':   ((550, 132, 571, 150), (2, 2)),
    'station-planter-b':   ((582, 135, 603, 150), (2, 2)),
    'station-cat':         ((326, 237, 348, 253), (2, 1)),
}

# the pack's colours, for the pieces composed here
INK = (38, 43, 68)
WHITE, WHITE_SHADE = (255, 232, 232), (201, 201, 228)
COPING, COPING_SHADE = (171, 177, 194), (126, 134, 158)
YELLOW, YELLOW_DARK, YELLOW_LIGHT = (214, 164, 62), (160, 116, 48), (236, 196, 96)


def crop(sheet, box, cells):
    im = sheet.crop(box)
    if cells:
        im = im.crop(im.getbbox())
        canvas = Image.new('RGBA', (cells[0] * 16, cells[1] * 16), (0, 0, 0, 0))
        canvas.alpha_composite(im, ((canvas.width - im.width) // 2, canvas.height - im.height))
        im = canvas
    return im


def platform_edge(floor):
    """The platform's north edge (the track side): a shadow line where the
    platform drops to the ballast, the coping stone, the white line and the
    yellow tactile strip you stand behind."""
    im = floor.copy()
    px = im.load()
    for x in range(16):
        px[x, 0] = INK + (255,)
        px[x, 1] = px[x, 2] = COPING + (255,)
        px[x, 3] = COPING_SHADE + (255,)
        px[x, 5] = WHITE + (255,)
        px[x, 6] = WHITE_SHADE + (255,)
        for y in range(8, 14):                      # tactile strip: raised bars
            px[x, y] = (YELLOW_LIGHT if y == 8 else YELLOW_DARK if y == 13 else
                        YELLOW_DARK if x % 4 == 3 else YELLOW) + (255,)
    px[0, 1] = px[0, 2] = COPING_SHADE + (255,)     # a joint per stone
    return im


def tactile(kind):
    """A yellow tactile paving overlay (transparent round it): 'v' / 'h' the
    guide path with its long bars, 'stop' the dotted block at a turn, the
    gates and the head of the stairs."""
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = im.load()
    for a in range(16):             # along the path
        for b in range(4, 12):      # across it
            x, y = (b, a) if kind == 'v' else (a, b)
            if kind == 'stop':
                x, y = a, b
                if not (4 <= a < 12):
                    continue
                dot = (a % 2 == 1 and b % 2 == 1)
                c = YELLOW_DARK if dot else YELLOW
            else:
                c = YELLOW_DARK if b in (6, 9) else YELLOW
            if b == 4 and kind != 'v':
                c = YELLOW_LIGHT
            px[x, y] = c + (255,)
    return im


def railing(sheet, piece):
    """One cell of tube railing: 'post' has its post at the left and the rails
    running on, 'mid' is rails only, 'end' is 'post' mirrored (the last cell
    of a run, post at the right)."""
    src = sheet.crop((288, 127, 304, 138)) if piece != 'mid' else sheet.crop((304, 127, 320, 138))
    if piece == 'end':
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    im.alpha_composite(src, (0, 16 - src.height - 1))
    return im


def build():
    sheet = Image.open(SHEET).convert('RGBA')
    out = {name: crop(sheet, box, cells) for name, (box, cells) in CROPS.items()}
    out['station-platform-edge'] = platform_edge(out['station-floor'])
    for kind in ('v', 'h', 'stop'):
        out[f'station-tactile-{kind}'] = tactile(kind)
    for piece in ('post', 'mid', 'end'):
        out[f'station-railing-{piece}'] = railing(sheet, piece)
    return {name: im.resize((im.width * K, im.height * K), Image.NEAREST) for name, im in out.items()}


def register(built):
    """Save the sprites and list them in config.json (spriteMetadata, tileNames)."""
    cfg = json.load(open('config.json'))
    for name, im in built.items():
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = name
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)


def preview(built, path):
    sheet = Image.new('RGBA', (sum(i.width + 16 for i in built.values()) + 16,
                               max(i.height for i in built.values()) + 32), (233, 238, 246, 255))
    x = 16
    for im in built.values():
        sheet.alpha_composite(im, (x, sheet.height - 16 - im.height))
        x += im.width + 16
    sheet.save(path)
    print('preview ->', path)


def main():
    built = build()
    register(built)
    for name, im in built.items():
        print(f'{name}: {im.width // 64}x{im.height // 64} cells')
    if '--preview' in sys.argv:
        preview(built, sys.argv[sys.argv.index('--preview') + 1])


if __name__ == '__main__':
    main()
