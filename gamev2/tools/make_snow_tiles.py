#!/usr/bin/env python3
"""make_snow_tiles.py — recolour existing terrain/tree sprites into a winter
"snow" set for the Yukimura room (a quiet snowy village reached only by train).

There is no snow art in the pack, so we derive it: each new sprite is a
luminance-remap of an existing one (grass -> snow field, pond -> frozen ice,
evergreen -> snow-dusted pine), which keeps the original edge/corner geometry
so the autotile pieces and prefabs Just Work. Deterministic (seeded noise) and
idempotent: rewrites assets/sprites/{snow,ice,*-snow}.png and registers every
new key in config.json spriteMetadata + tileNames (the game loads a tile only
if it has a spriteMetadata entry).

Run from gamev2/ BEFORE make_prefabs.py and generate_yukimura.py:
    python3 tools/make_snow_tiles.py
"""
import glob, json, os, random, re
from PIL import Image

SRC = 'assets/sprites'


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def ramp(stops, L):
    """Piecewise-linear map from luminance L to an (r,g,b) on the ramp."""
    if L <= stops[0][0]:
        return stops[0][1]
    if L >= stops[-1][0]:
        return stops[-1][1]
    for (l0, c0), (l1, c1) in zip(stops, stops[1:]):
        if l0 <= L <= l1:
            t = (L - l0) / (l1 - l0)
            return tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


# fresh snow: cool near-white, faint blue in the shadows/banks
SNOW = [(0, (150, 166, 190)), (70, (196, 208, 224)), (124, (230, 238, 247)),
        (160, (244, 248, 252)), (255, (255, 255, 255))]
# frozen pond: pale cyan ice, darker cracks, white glare
ICE = [(0, (120, 150, 175)), (80, (176, 206, 222)), (120, (203, 226, 238)),
       (180, (228, 242, 248)), (255, (255, 255, 255))]
# snow-dusted evergreen: deep pine in shadow, snow on the lit tops
PINE = [(0, (26, 42, 40)), (60, (44, 74, 64)), (110, (74, 110, 96)),
        (140, (150, 180, 175)), (175, (226, 238, 244)), (255, (252, 255, 255))]
# a tree's shadow cast on snow: a soft, cold blue-grey
SNOWSHADOW = [(0, (150, 163, 188)), (60, (176, 189, 210)), (255, (206, 218, 232))]


def stable_seed(s):
    return sum(ord(c) * (i + 1) for i, c in enumerate(s))


def recolor(src, dst, stops, noise=0):
    im = Image.open(f'{SRC}/{src}.png').convert('RGBA')
    px = im.load()
    w, h = im.size
    rng = random.Random(stable_seed(dst))
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            nr, ng, nb = ramp(stops, lum(r, g, b))
            if noise:
                j = rng.randint(-noise, noise)
                nr = max(0, min(255, nr + j))
                ng = max(0, min(255, ng + j))
                nb = max(0, min(255, nb + j))
            px[x, y] = (nr, ng, nb, a)
    im.save(f'{SRC}/{dst}.png')


# (dst_key, src_key, ramp, noise) — src provides the geometry + spriteMetadata
JOBS = []

# snow ground: every grass-autotile role -> snow-autotile role
for p in sorted(glob.glob(f'{SRC}/grass-autotile_*.png')):
    role = re.match(r'.*grass-autotile_(.+)\.png$', p).group(1)
    JOBS.append((f'snow-autotile_{role}', f'grass-autotile_{role}', SNOW, 5))

# frozen pond: every pond-autotile role -> ice-pond-autotile role
for p in sorted(glob.glob(f'{SRC}/pond-autotile_*.png')):
    role = re.match(r'.*pond-autotile_(.+)\.png$', p).group(1)
    JOBS.append((f'ice-pond-autotile_{role}', f'pond-autotile_{role}', ICE, 3))

# snowy trees / shrubs (prefab sprites)
JOBS += [
    ('tree-3-top-snow_0_0',           'tree-3-top_0_0',           PINE, 4),
    ('tree-3-base-shadow-snow_0_0',   'tree-3-base-shadow_0_0',   SNOWSHADOW, 0),
    ('shrub-large-circle-snow_0_0',   'shrub-large-circle_0_0',   PINE, 3),
    ('shrub-small-circle-snow_0_0',   'shrub-small-circle_0_0',   PINE, 3),
]

for dst, src, stops, noise in JOBS:
    recolor(src, dst, stops, noise)

# register each new key so the game will load it (copy the source's metadata:
# same dimensions -> same anchor). tileNames is the debug/label map.
cfg = json.load(open('config.json'))
sm = cfg['spriteMetadata']
tn = cfg.setdefault('tileNames', {})
for dst, src, _stops, _noise in JOBS:
    sm[dst] = dict(sm[src])
    tn[dst] = dst
json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

print(f'recoloured {len(JOBS)} snow sprites; registered {len(JOBS)} spriteMetadata keys')
