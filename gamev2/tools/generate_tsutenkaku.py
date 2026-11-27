#!/usr/bin/env python3
"""generate_tsutenkaku.py — draw the Tsutenkaku Tower placeholder sprite.

There is no Tsutenkaku art anywhere in the asset packs, so — like the Tokyo
Tower / Tokyo Station placeholders (assets/sprites/tokyo-tower_0_0.png) — it is
white line-art with one red accent: drawn here at half size with 1px black
lines and pixel-doubled, which is exactly how the Tokyo Tower sprite is built
(256x480 doubled to 512x960). Same 8-cell width, 13 cells tall (it is the
shorter tower), same 3-colour palette.

What is drawn, top to bottom: the mast, the two-storey observation head, the
lattice shaft with the vertical neon-sign band (the red accent), the wide lower
deck, and the four splayed legs with the archway between them.

Deterministic and idempotent: rewrites assets/sprites/tsutenkaku_0_0.png and
registers it in config.json spriteMetadata + tileNames (the game only loads a
tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py / generate_osaka.py:
    python3 tools/generate_tsutenkaku.py
"""
import json
from PIL import Image, ImageDraw

KEY = 'tsutenkaku_0_0'
W, H = 256, 416                       # half size; doubled to 512x832 = 8x13 cells
WHITE, BLACK, RED = (255, 255, 255, 255), (0, 0, 0, 255), (246, 49, 59, 255)
CLEAR = (0, 0, 0, 0)
CX = W // 2

im = Image.new('RGBA', (W, H), CLEAR)
d = ImageDraw.Draw(im)


def shape(points, fill=WHITE):
    d.polygon(points, fill=fill, outline=BLACK)


def lattice(points, rows, cols):
    """A white panel with a truss drawn on it: `rows` horizontal members and
    crossed diagonals in each of `cols` bays. points = TL, TR, BR, BL."""
    (x0, y0), (x1, _), (x2, y2), (x3, _) = points
    panel = Image.new('RGBA', (W, H), CLEAR)
    pd = ImageDraw.Draw(panel)
    pd.polygon(points, fill=WHITE)
    edge = lambda t: (x0 + (x3 - x0) * t, x1 + (x2 - x1) * t, y0 + (y2 - y0) * t)
    for r in range(rows):
        la, ra, ya = edge(r / rows)
        lb, rb, yb = edge((r + 1) / rows)
        pd.line([(la, ya), (ra, ya)], fill=BLACK)
        for c in range(cols):
            a0, a1 = la + (ra - la) * c / cols, la + (ra - la) * (c + 1) / cols
            b0, b1 = lb + (rb - lb) * c / cols, lb + (rb - lb) * (c + 1) / cols
            pd.line([(a0, ya), (b1, yb)], fill=BLACK)
            pd.line([(a1, ya), (b0, yb)], fill=BLACK)
            pd.line([(a0, ya), (b0, yb)], fill=BLACK)
    pd.polygon(points, outline=BLACK)
    im.alpha_composite(panel)


def windows(x0, y0, x1, y1, step):
    """A glazed band: a framed box with mullions every `step` px and a rail."""
    d.rectangle([x0, y0, x1, y1], fill=WHITE, outline=BLACK)
    for x in range(x0 + step, x1, step):
        d.line([(x, y0), (x, y1)], fill=BLACK)
    d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=BLACK)


# ---- legs + archway (drawn first; everything above sits on top of them) ------
lattice([(66, 282), (190, 282), (232, 414), (24, 414)], rows=8, cols=6)
arch = Image.new('L', (W, H), 0)
ad = ImageDraw.Draw(arch)
ad.ellipse([86, 316, 170, 400], fill=255)            # the arch crown...
ad.rectangle([86, 358, 170, H], fill=255)            # ...and the opening below it
im.paste(CLEAR, (0, 0), arch)
d.arc([86, 316, 170, 400], 180, 360, fill=BLACK)
d.line([(86, 358), (86, 414)], fill=BLACK)
d.line([(170, 358), (170, 414)], fill=BLACK)
d.line([(24, 414), (86, 414)], fill=BLACK)
d.line([(170, 414), (232, 414)], fill=BLACK)

# ---- lower deck: the wide viewing platform the legs carry --------------------
shape([(58, 270), (198, 270), (190, 282), (66, 282)])
windows(52, 248, 204, 270, 8)
shape([(60, 240), (196, 240), (204, 248), (52, 248)])

# ---- shaft: a gently flaring lattice with the neon-sign band down its face ---
lattice([(98, 112), (158, 112), (176, 240), (80, 240)], rows=9, cols=4)
d.rectangle([CX - 9, 116, CX + 9, 236], fill=RED, outline=BLACK)
for y in range(132, 236, 16):                        # the sign's letter panels
    d.line([(CX - 9, y), (CX + 9, y)], fill=BLACK)

# ---- observation head: two glazed storeys under a stepped cap ----------------
shape([(84, 96), (172, 96), (158, 112), (98, 112)])  # corbelled underside
windows(84, 76, 172, 96, 8)
windows(92, 56, 164, 76, 8)
shape([(104, 44), (152, 44), (164, 56), (92, 56)])   # roof
d.rectangle([116, 34, 140, 44], fill=WHITE, outline=BLACK)   # lantern room
d.rectangle([124, 16, 132, 34], fill=WHITE, outline=BLACK)   # mast base
# a short one (issue #181): the sprite's top row lies on the first row of paving
# south of the avenue, whose rim reads as the avenue's kerb - a mast drawn from
# the very top of the sprite poked onto it
d.line([(CX, 9), (CX, 16)], fill=BLACK)                      # mast

big = im.resize((W * 2, H * 2), Image.NEAREST)
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
