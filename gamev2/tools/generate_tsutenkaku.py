#!/usr/bin/env python3
"""generate_tsutenkaku.py — save the Tsutenkaku Tower landmark sprite.

There is no Tsutenkaku art anywhere in the asset packs. The landmark was white
line art drawn here; until the team's own art arrives (issue #70) it is the
shaded tower that tools/generate_osaka_art.py draws as `tsutenkaku()`: open
steel lattice you see through, copper roofs, a glazed deck, the OSAKA neon
band, a lamp on the mast. That drawing was made on the line art's own
silhouette, so nothing moves: the same 8x13 cells (256x416 at half size,
pixel-doubled to 512x832), the same legs and the same open archway between
them, and the lamp on the mast still ends below the avenue's kerb (issue
#181). The picture is a placeholder still; a PNG of the same size dropped over
it needs no code or map change.

Deterministic and idempotent: rewrites assets/sprites/tsutenkaku_0_0.png and
registers it in config.json spriteMetadata + tileNames (the game only loads a
tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_osaka.py:
    python3 tools/generate_tsutenkaku.py
"""
import json
from PIL import Image

from generate_osaka_art import tsutenkaku

KEY = 'tsutenkaku_0_0'

im = tsutenkaku()                     # half size; doubled to 512x832 = 8x13 cells
big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
big.save(f'assets/sprites/{KEY}.png')

# register so the game loads it: multi-cell sprites anchor on the centre of
# their top-left cell (same rule as the Godot port / the train sprites)
cfg = json.load(open('config.json'))
cfg['spriteMetadata'][KEY] = {'frameCount': 1,
                              'anchorX': round(32 / big.width, 4),
                              'anchorY': round(32 / big.height, 4)}
cfg.setdefault('tileNames', {})[KEY] = 'placeholder-tsutenkaku'
json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

print(f'{KEY}: {big.width}x{big.height}px ({big.width // 64}x{big.height // 64} cells)')
