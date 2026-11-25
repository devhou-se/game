#!/usr/bin/env python3
"""extract_dotonbori.py — slice the Osaka landmarks out of the GuttyKreum
Dotonbori City pack (Assets/GuttyKreum/DotonboriCity_v3) into gamev2 sprites.

  dotonbori-arch_0_0   the Dotonbori street entrance arch (道頓堀 sign on two
                       posts) — 8x6 cells, you walk under it
  dotonbori-wheel_0_0  the oval ferris wheel (the Don Quijote Dotonbori wheel)
                       — 12x12 cells

Like tools/extract_train.py: the pack is 16px-native and gamev2 cells are 64px,
so the art upscales 4x NEAREST. Crop rectangles were read off the sheet by hand
(grid-overlay inspection) and are cell-aligned on purpose: each sprite is
bottom-aligned on a canvas that is a whole number of cells, so the posts / legs
land exactly on cell columns (arch posts = columns 0 and 7; wheel legs =
columns 2-3 and 8-9).

Registers both keys in config.json spriteMetadata + tileNames (the game only
loads a tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_osaka.py:
    python3 tools/extract_dotonbori.py
"""
import json
from PIL import Image

SHEET = '../Assets/GuttyKreum/DotonboriCity_v3/RPGMakerVXAce/GK_DB_F.png'
# key -> (tile name, crop rect on the sheet in native px; w and h multiples of 16)
CROPS = {
    'dotonbori-arch_0_0':  ('dotonbori-arch',  (0, 384, 128, 480)),
    'dotonbori-wheel_0_0': ('dotonbori-wheel', (0, 32, 192, 224)),
}

im = Image.open(SHEET).convert('RGBA')
cfg = json.load(open('config.json'))
for key, (name, region) in CROPS.items():
    big = im.crop(region)
    big = big.resize((big.width * 4, big.height * 4), Image.NEAREST)
    assert big.width % 64 == 0 and big.height % 64 == 0, (key, big.size)
    big.save(f'assets/sprites/{key}.png')
    # multi-cell sprites anchor on the centre of their top-left cell
    cfg['spriteMetadata'][key] = {'frameCount': 1,
                                  'anchorX': round(32 / big.width, 4),
                                  'anchorY': round(32 / big.height, 4)}
    cfg.setdefault('tileNames', {})[key] = name
    print(f'{key}: {big.width}x{big.height}px ({big.width // 64}x{big.height // 64} cells)')
json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
