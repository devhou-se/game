#!/usr/bin/env python3
"""make_japan_map.py — draw the Map overlay's picture of Japan (issue #211).

The menu's Map is a map of Japan with a dot per town in the game. This draws
the map: the four main islands (and a few small ones, for the silhouette) as
shaded pixel art in the game's palette — sea with shallows along the coast, an
ink coastline, lowland / hill / mountain greens and a little snow on the
highest ground. Everything comes from the hand-authored outlines below
(simplified coastlines in longitude / latitude); nothing is downloaded.

Writes assets/map/japan.png and assets/map/japan.json. The JSON is the
CONTRACT the game projects a town's `geo` through (src/utils/Places.js):

  { "image": "assets/map/japan.png", "width": W, "height": H,
    "lon0": west edge, "lat0": NORTH edge, "pxPerLon": .., "pxPerLat": ..,
    "islands": { "<name>": [[lon, lat], ...] } }

  x = (lon - lon0) * pxPerLon        y = (lat0 - lat) * pxPerLat

an equirectangular projection squeezed east-west by cos(38 N), so the country
keeps its shape. `islands` is the outline the art was filled from: the unit
test checks every town's geo falls on land with it. One drawn pixel is a
degree / 16 of latitude (about 7 km); the overlay magnifies it in half steps
(UIScale.mapFit: 3x on a desktop), so the pixels stay even.

Deterministic and idempotent (check_generators.py re-runs it). Needs Pillow.

Run from gamev2/:
    /Library/Developer/CommandLineTools/usr/bin/python3 tools/make_japan_map.py [--preview out.png]
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

OUT_DIR = 'assets/map'
LON0, LON1 = 129.0, 146.2
LAT0, LAT1 = 46.0, 30.0            # north edge, south edge
PX_LAT = 16.0
PX_LON = round(PX_LAT * math.cos(math.radians(38)), 2)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# the game's own colours: the sea and shallows of the beach tiles, the grass
# and leaf greens of the town tiles, the ink the generated art is outlined in
SEA, SEA_DEEP, SEA_NEAR, SHALLOW = rgb('425faa'), rgb('3a5499'), rgb('5377bf'), rgb('8ec2fa')
INK = rgb('0a1627')
LOW, LAND, HILL, MOUNTAIN, PEAK = rgb('89af78'), rgb('678e57'), rgb('4f7a55'), rgb('395050'), rgb('e8eef0')

# Clockwise from the northern tip, (lon, lat). Simplified by hand: enough
# capes and bays to read as Japan at a glance, and the towns of the game on
# the right side of the coast.
ISLANDS = {
    'Hokkaido': [
        (141.94, 45.52), (142.50, 45.00), (143.30, 44.40), (144.30, 44.00), (144.67, 43.92),
        (145.33, 44.34), (145.19, 44.02), (145.13, 43.66), (145.82, 43.38), (145.50, 43.25),
        (144.85, 43.03), (144.38, 42.98), (143.80, 42.75), (143.32, 42.28), (143.25, 41.93),
        (142.77, 42.16), (142.00, 42.47), (141.60, 42.63), (141.00, 42.31), (140.86, 42.47),
        (140.70, 42.58), (140.38, 42.51), (140.27, 42.25), (140.57, 42.10), (140.82, 42.03),
        (141.18, 41.81), (140.73, 41.77), (140.20, 41.40), (140.10, 41.43), (140.13, 41.87),
        (139.85, 42.45), (140.23, 42.79), (140.35, 43.33), (140.78, 43.20), (141.00, 43.20),
        (141.30, 43.25), (141.37, 43.42), (141.52, 43.85), (141.65, 43.94), (141.70, 44.36),
        (141.74, 44.88), (141.64, 45.45),
    ],
    'Honshu': [
        (140.91, 41.53), (141.46, 41.43), (141.40, 41.10), (141.40, 40.70), (141.53, 40.53),
        (141.80, 40.20), (141.97, 39.64), (141.90, 39.27), (141.73, 39.05), (141.60, 38.90),
        (141.55, 38.30), (141.30, 38.42), (141.07, 38.37), (141.03, 38.25), (140.95, 37.80),
        (140.97, 37.00), (140.65, 36.60), (140.60, 36.30), (140.87, 35.73), (140.40, 35.30),
        (140.30, 35.13), (139.88, 34.90), (139.83, 35.00), (139.82, 35.31), (140.05, 35.55),
        (139.82, 35.52), (139.66, 35.40), (139.67, 35.14), (139.55, 35.30), (139.17, 35.25),
        (139.12, 34.95), (138.95, 34.65), (138.85, 34.60), (138.77, 34.95), (138.87, 35.10),
        (138.40, 34.95), (138.23, 34.60), (137.73, 34.67), (137.02, 34.58), (137.33, 34.75),
        (136.88, 35.05), (136.65, 34.95), (136.53, 34.70), (136.90, 34.48), (136.87, 34.25),
        (136.20, 34.07), (136.00, 33.72), (135.76, 33.44), (135.35, 33.67), (135.15, 33.88),
        (135.10, 34.22), (135.40, 34.50), (135.38, 34.67), (135.20, 34.68), (135.00, 34.64),
        (134.65, 34.77), (133.95, 34.58), (133.38, 34.45), (132.45, 34.36), (132.22, 34.15),
        (132.10, 33.95), (131.55, 34.03), (131.25, 33.93), (130.93, 33.95), (130.87, 34.30),
        (131.18, 34.40), (131.40, 34.43), (131.83, 34.68), (132.08, 34.90), (132.65, 35.43),
        (132.95, 35.55), (133.30, 35.58), (133.35, 35.45), (134.23, 35.54), (134.80, 35.65),
        (135.22, 35.78), (135.20, 35.55), (135.40, 35.50), (135.75, 35.50), (136.07, 35.67),
        (135.97, 35.98), (136.12, 36.22), (136.50, 36.58), (136.68, 36.85), (136.72, 37.15),
        (136.90, 37.40), (137.35, 37.53), (137.25, 37.30), (137.00, 37.05), (137.00, 36.85),
        (137.10, 36.80), (137.22, 36.78), (137.40, 36.83), (137.86, 37.04), (138.25, 37.18),
        (138.55, 37.37), (139.05, 37.93), (139.45, 38.23), (139.83, 38.92), (140.07, 39.72),
        (139.70, 39.93), (139.95, 40.00), (140.02, 40.20), (139.93, 40.65), (140.30, 40.78),
        (140.35, 41.26), (140.65, 41.05), (140.75, 40.83), (141.13, 40.87), (141.20, 41.28),
        (140.80, 41.13),
    ],
    'Shikoku': [
        (132.02, 33.34), (132.70, 33.85), (133.00, 34.07), (133.30, 33.97), (133.63, 34.13),
        (134.05, 34.35), (134.40, 34.25), (134.62, 34.20), (134.60, 34.05), (134.75, 33.83),
        (134.18, 33.25), (133.55, 33.50), (133.28, 33.38), (133.00, 32.73), (132.70, 32.92),
        (132.50, 33.20), (132.40, 33.45),
    ],
    'Kyushu': [
        (130.95, 33.95), (131.00, 33.72), (131.20, 33.60), (131.73, 33.60), (131.50, 33.30),
        (131.70, 33.25), (131.90, 33.25), (131.95, 32.95), (131.68, 32.58), (131.45, 31.90),
        (131.35, 31.37), (131.10, 31.47), (130.67, 31.00), (130.78, 31.35), (130.75, 31.70),
        (130.55, 31.58), (130.65, 31.23), (130.30, 31.27), (130.12, 31.42), (130.20, 31.82),
        (130.20, 32.02), (130.40, 32.20), (130.60, 32.50), (130.60, 32.80), (130.45, 33.10),
        (130.25, 33.15), (130.07, 32.85), (130.37, 32.75), (130.20, 32.60), (129.87, 32.73),
        (129.73, 32.57), (129.70, 33.15), (129.55, 33.35), (129.97, 33.50), (130.15, 33.62),
        (130.40, 33.70), (130.50, 33.87), (130.80, 33.95),
    ],
    # small ones, for the silhouette only
    'Sado': [(138.25, 38.32), (138.52, 38.30), (138.58, 38.07), (138.45, 37.82), (138.22, 37.85), (138.32, 38.05)],
    'Awaji': [(135.02, 34.60), (134.95, 34.30), (134.70, 34.20), (134.80, 34.45)],
    'Tsushima': [(129.48, 34.70), (129.42, 34.35), (129.20, 34.10), (129.30, 34.50)],
    'Oki': [(133.10, 36.35), (133.38, 36.25), (133.25, 36.12), (133.02, 36.18)],
    'Rishiri': [(141.15, 45.25), (141.33, 45.22), (141.30, 45.10), (141.15, 45.12)],
    'Okushiri': [(139.45, 42.25), (139.55, 42.20), (139.52, 42.05), (139.42, 42.08)],
    'Amakusa': [(130.00, 32.52), (130.22, 32.45), (130.15, 32.25), (129.98, 32.20)],
    'Tanegashima': [(131.02, 30.82), (131.08, 30.60), (130.95, 30.35), (130.88, 30.55)],
    'Yakushima': [(130.42, 30.42), (130.62, 30.42), (130.66, 30.28), (130.50, 30.22), (130.40, 30.30)],
    'Oshima': [(139.35, 34.80), (139.45, 34.78), (139.44, 34.68), (139.36, 34.69)],
}


def project(lon, lat):
    return (lon - LON0) * PX_LON, (LAT0 - lat) * PX_LAT


def noise(x, y):
    """Smooth value noise in 0..1, from an integer hash (no random module)."""
    def h(i, j):
        n = (i * 374761393 + j * 668265263) & 0xffffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
        return ((n ^ (n >> 16)) & 0xffff) / 65535.0

    def layer(scale):
        fx, fy = x / scale, y / scale
        i, j = int(math.floor(fx)), int(math.floor(fy))
        u, v = fx - i, fy - j
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        top = h(i, j) * (1 - u) + h(i + 1, j) * u
        bot = h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u
        return top * (1 - v) + bot * v
    return 0.65 * layer(7.0) + 0.35 * layer(3.0)


def distances(mask, w, h, inside, cap):
    """Chebyshev steps from each `inside` pixel to the nearest pixel that is
    not (0 for the others), capped. The picture's edge is not a coast."""
    dist = [[0] * w for _ in range(h)]
    edge = [(x, y) for y in range(h) for x in range(w) if mask[y][x] == inside and any(
        0 <= x + dx < w and 0 <= y + dy < h and mask[y + dy][x + dx] != inside
        for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    for x, y in edge:
        dist[y][x] = 1
    step = 1
    while edge and step < cap:
        step += 1
        nxt = []
        for x, y in edge:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] == inside and not dist[ny][nx]:
                        dist[ny][nx] = step
                        nxt.append((nx, ny))
        edge = nxt
    for y in range(h):
        for x in range(w):
            if mask[y][x] == inside and not dist[y][x]:
                dist[y][x] = cap
    return dist


def draw():
    w = int(round((LON1 - LON0) * PX_LON))
    h = int(round((LAT0 - LAT1) * PX_LAT))
    shape = Image.new('1', (w, h), 0)
    d = ImageDraw.Draw(shape)
    for pts in ISLANDS.values():
        d.polygon([project(*p) for p in pts], fill=1)
    px = shape.load()
    land = [[1 if px[x, y] else 0 for x in range(w)] for y in range(h)]
    up = distances(land, w, h, 1, 12)        # how far inland
    out = distances(land, w, h, 0, 12)       # how far out to sea

    def height(x, y):
        if not (0 <= x < w and 0 <= y < h) or not land[y][x]:
            return 0.0
        return up[y][x] + 5.0 * (noise(x, y) - 0.5)

    im = Image.new('RGB', (w, h), SEA)
    p = im.load()
    for y in range(h):
        for x in range(w):
            if land[y][x]:
                e = height(x, y)
                c = LOW if e < 1.6 else LAND if e < 3.4 else HILL if e < 5.4 else MOUNTAIN
                # the highest ground carries snow; a slope facing away from
                # the light (north-west) is a tone darker
                if e >= 10.6 and noise(x + 40, y + 90) > 0.5:
                    c = PEAK
                elif c is not LOW and height(x - 1, y - 1) > e + 0.9:
                    c = {LAND: HILL, HILL: MOUNTAIN, MOUNTAIN: MOUNTAIN}[c]
                p[x, y] = c
            else:
                o = out[y][x]
                if o == 1:
                    p[x, y] = INK                      # the coastline
                elif o == 2:
                    p[x, y] = SHALLOW
                elif o <= 4:
                    p[x, y] = SEA_NEAR
                elif o >= 12 and (x + 2 * y) % 4 == 0 and noise(x + 300, y) > 0.5:
                    p[x, y] = SEA_DEEP                 # open water: a dither of deeper blue
                elif (x * 3 + y * 7) % 23 == 0 and noise(x, y + 500) > 0.62:
                    p[x, y] = SEA_NEAR                 # a wave glint here and there
    return im


def main(argv):
    im = draw()
    if '--preview' in argv:
        path = argv[argv.index('--preview') + 1]
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(path)
        print(f'preview {path}')
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    im.save(f'{OUT_DIR}/japan.png', optimize=True)
    meta = {'image': f'{OUT_DIR}/japan.png', 'width': im.width, 'height': im.height,
            'lon0': LON0, 'lat0': LAT0, 'pxPerLon': PX_LON, 'pxPerLat': PX_LAT,
            'islands': {k: [list(pt) for pt in v] for k, v in ISLANDS.items()}}
    open(f'{OUT_DIR}/japan.json', 'w').write(json.dumps(meta, indent=1, sort_keys=True) + '\n')
    print(f'japan.png {im.width}x{im.height} ({os.path.getsize(OUT_DIR + "/japan.png")} bytes), '
          f'{len(ISLANDS)} islands')


if __name__ == '__main__':
    main(sys.argv[1:])
