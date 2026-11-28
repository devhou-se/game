#!/usr/bin/env python3
"""generate_discount_art.py — interior signage for the Don Takote discount
store (issue #91): the pieces tools/generate_discount_stores.py dresses the
shop floor with.

  don-takote-sign_0_0      5x2  the facade's own sign board, hung on the back wall
  don-takote-wall_0_0      1x1  back-wall panel, lower row: gold over the blue price band
  don-takote-wall-top_0_0  1x1  back-wall panel, upper row: plain gold under a red trim
  don-takote-pop-yen_0_0   1x1  wall POP card: red ¥ on a gold card
  don-takote-pop-sale_0_0  1x1  wall POP card: the octopus mascot on blue

The look is the house look of the GuttyKreum pack (the approved Sendai /
Kanazawa / Fukuoka art): every colour is one the pack's own sheets use
(art-source/GuttyKreum), the outline is the pack's navy, not black, the light
comes from the upper left on every piece, and the shop's loud yellow is the
pack's dim gold. Only the sign's LETTERING comes from the facade sprite
(assets/sprites/discount-store_0_0.png, drawn by tools/extract_city.py), and
only as a mask: which cells are ink, by luminance, recoloured here. The board,
its band and studs, the octopus mascot, the panels and the cards are drawn.
So it needs no Japanese font (unlike extract_city.py) - re-run it after
extract_city.py changes the sign.

Like the facade's, the art is drawn at half size and pixel-doubled, so its
pixels are the size of the furniture next to it, with rectangles and points
only (no Pillow ellipse, polygon or slanted line, which move by a pixel
between Pillow versions). Registers every key in config.json spriteMetadata +
tileNames. Needs Pillow.

Run from gamev2/:  python3 tools/generate_discount_art.py [--preview out.png]
"""
import json, math, sys
from PIL import Image, ImageDraw

from generate_hokkaido import outline, rgb
from generate_sendai_art import P_SHADE

FACADE = 'assets/sprites/discount-store_0_0.png'
INK, EDGE = rgb('0a1627'), rgb('172459')
WHITE, WHITE_LO = rgb('fafcfd'), rgb('dae2e4')
GOLD_LIT, GOLD_HI, GOLD, GOLD_LO = rgb('f3d890'), rgb('e3c587'), rgb('c6a663'), rgb('a7843b')
RED_LIT, RED_HI, RED, RED_LO = rgb('e78d7b'), rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')
BLUE_HI, BLUE, BLUE_LO = rgb('588cc6'), rgb('425faa'), rgb('314b8e')
SLATE = rgb('5b6c79')


def double(im):
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def lettering():
    """The two lines of the facade's sign, as cells: (name, hook). Dark on the
    light board, light on the dark band, so it holds if the facade is recoloured."""
    im = Image.open(FACADE).convert('RGB').crop((0, 0, 320, 128)).resize((160, 64), Image.NEAREST)
    px = im.load()
    lum = lambda x, y: (299 * px[x, y][0] + 587 * px[x, y][1] + 114 * px[x, y][2]) // 1000
    name = [(x, y) for y in range(9, 45) for x in range(38, 156) if lum(x, y) < 110]
    hook = [(x, y) for y in range(47, 57) for x in range(4, 156) if lum(x, y) > 150]
    return name, hook


def octopus(im, cx, cy, r):
    """The red octopus off the facade, drawn: a round head cut flat at the
    bottom, a hem, legs every few pixels alternately long and short, square
    eyes and a straight mouth; lit from the upper left and edged in navy."""
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    big = r > 8
    hw = lambda dy: math.isqrt(r * r - dy * dy + r) if -r <= dy < r - 2 else -1
    inside = lambda x, dy: abs(x - cx) <= hw(dy)
    for dy in range(-r, r - 2):
        for x in range(cx - hw(dy), cx + hw(dy) + 1):
            # a ball: a lit rim on the upper left, a shaded one on the lower right
            c = RED_HI if not inside(x - 2, dy - 2) else RED_LO if not inside(x + 2, dy + 2) else RED
            d.point((x, cy + dy), c)
    # the legs: 2 wide every 5, a gap showing between them (every 4 when small), off a hem row
    leg, step, n = (2, 5, 5) if big else (2, 4, 4)
    x0 = cx - (n * step - (step - leg)) // 2
    hem = cy + r - 2
    d.rectangle([x0, hem, x0 + n * step - (step - leg) - 1, hem], fill=RED)
    d.point((x0, hem), RED_HI)
    long_, short = (8, 5) if big else (4, 2)
    for i in range(n):
        x = x0 + i * step
        y1 = hem + (long_ if i % 2 == 0 else short)
        d.rectangle([x, hem + 1, x + leg - 1, y1], fill=RED)
        d.rectangle([x + leg - 1, hem + 1, x + leg - 1, y1], fill=RED_LO)
        if big:
            d.point((x, hem + 1), RED_HI)
    # the face
    if big:
        for ex in (cx - 6, cx + 4):
            d.rectangle([ex, cy - 3, ex + 2, cy], fill=WHITE)
            d.rectangle([ex, cy, ex + 2, cy], fill=WHITE_LO)
            d.point((ex + 1, cy - 1), INK)
        d.rectangle([cx - 3, cy + 4, cx + 3, cy + 4], fill=INK)
        d.rectangle([cx - 6, cy - 6, cx - 5, cy - 6], fill=RED_LIT)
    else:
        for ex in (cx - 4, cx + 3):
            d.rectangle([ex, cy - 1, ex + 1, cy], fill=WHITE)
        d.point((cx - 3, cy), INK)
        d.point((cx + 3, cy), INK)
        d.rectangle([cx - 1, cy + 2, cx + 1, cy + 2], fill=INK)
        d.rectangle([cx - 3, cy - 4, cx - 2, cy - 4], fill=RED_LIT)
    outline(layer, EDGE)
    im.alpha_composite(layer)


def sign():
    """The rooftop board, hung on the back wall: gold board in a red frame with
    its marquee studs, the name in ink, the blue band with the hook line, the
    octopus."""
    W, H = 160, 64
    im = Image.new('RGBA', (W, H), GOLD_HI)
    d = ImageDraw.Draw(im)
    box = lambda x0, y0, x1, y1, c: d.rectangle([x0, y0, x1, y1], fill=c)
    box(0, 0, W - 1, H - 1, EDGE)
    box(1, 1, W - 2, H - 2, RED_LO)                         # the red frame, lit top and left
    box(1, 1, W - 3, H - 3, RED_HI)
    box(2, 2, W - 3, H - 3, GOLD_HI)
    box(2, 2, W - 3, 2, GOLD_LIT)                           # the board: lit top and left, shaded bottom and right
    box(2, 2, 2, 45, GOLD_LIT)
    box(3, 43, W - 3, 45, GOLD)
    box(W - 4, 3, W - 3, 45, GOLD)
    for x in range(8, W - 6, 8):                            # marquee studs
        box(x, 6, x + 1, 7, RED)
        d.point((x, 6), RED_HI)
        d.point((x + 1, 7), RED_LO)
    box(2, 46, W - 3, 46, EDGE)                             # the band
    box(2, 47, W - 3, 61, BLUE)
    box(2, 47, W - 3, 47, BLUE_HI)
    box(2, 60, W - 3, 61, BLUE_LO)
    name, hook = lettering()
    for cells, shade, ink in ((name, GOLD, INK), (hook, BLUE_LO, WHITE)):
        for x, y in cells:
            d.point((x + 1, y + 1), shade)
        for x, y in cells:
            d.point((x, y), ink)
    octopus(im, 21, 25, 11)
    return double(im)


def panel(d, y0, y1):
    """A cell's width of gold wall panel, lit on the left, its seam on the right."""
    d.rectangle([0, y0, 31, y1], fill=GOLD)
    d.rectangle([0, y0, 0, y1], fill=GOLD_HI)
    d.rectangle([31, y0, 31, y1], fill=GOLD_LO)


def wall():
    """One cell of back wall: gold panel, the blue band with white price dashes
    along the bottom, a skirting line where it meets the floor."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    panel(d, 0, 19)
    d.rectangle([0, 19, 31, 19], fill=GOLD_LO)
    d.rectangle([0, 20, 31, 20], fill=EDGE)
    d.rectangle([0, 21, 31, 28], fill=BLUE)
    d.rectangle([0, 21, 31, 21], fill=BLUE_HI)
    d.rectangle([0, 27, 31, 28], fill=BLUE_LO)
    for x in range(3, 30, 8):
        d.rectangle([x, 24, x + 3, 24], fill=WHITE)
        d.rectangle([x, 25, x + 3, 25], fill=WHITE_LO)
    d.rectangle([0, 29, 31, 29], fill=SLATE)
    d.rectangle([0, 30, 31, 31], fill=INK)
    return double(im)


def wall_top():
    """The panel row above it: plain gold under a red trim along the ceiling,
    the trim's shade on the panel."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    panel(d, 0, 31)
    d.rectangle([0, 0, 31, 0], fill=EDGE)
    d.rectangle([0, 1, 31, 1], fill=RED_HI)
    d.rectangle([0, 2, 31, 3], fill=RED)
    d.rectangle([0, 4, 31, 4], fill=RED_LO)
    d.rectangle([0, 5, 31, 6], fill=GOLD_LO)
    for x in range(0, 32, 2):
        d.point((x, 7), GOLD_LO)
    return double(im)


def card(fill, hi, lo, edge_hi, edge_lo):
    """A POP card hanging on two strings, its shade on the wall; returns (image, draw)."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 28, 29, 28], fill=P_SHADE)
    d.rectangle([28, 8, 29, 27], fill=P_SHADE)
    for x in (9, 22):
        d.rectangle([x, 0, x, 5], fill=EDGE)
    d.rectangle([4, 5, 27, 27], fill=fill, outline=EDGE)
    d.rectangle([5, 6, 26, 6], fill=hi)
    d.rectangle([5, 25, 26, 26], fill=lo)
    d.rectangle([6, 7, 25, 25], outline=edge_hi)
    d.rectangle([6, 25, 25, 25], fill=edge_lo)
    d.rectangle([25, 7, 25, 25], fill=edge_lo)
    return im, d


def pop_yen():
    im, d = card(GOLD_HI, GOLD_LIT, GOLD, RED, RED_LO)
    # a chunky yen sign: the Y, then the two bars
    for i in range(5):
        d.rectangle([10 + i, 9 + i, 11 + i, 10 + i], fill=RED)
        d.rectangle([20 - i, 9 + i, 21 - i, 10 + i], fill=RED)
    for i in range(5):                                      # the arms' lit tops
        d.point((11 + i, 9 + i), RED_HI)
        d.point((20 - i, 9 + i), RED_HI)
    d.point((10, 9), RED_HI)
    d.point((21, 9), RED_HI)
    d.rectangle([15, 14, 16, 23], fill=RED)
    d.rectangle([11, 16, 20, 17], fill=RED)
    d.rectangle([11, 20, 20, 21], fill=RED)
    d.rectangle([11, 17, 20, 17], fill=RED_LO)
    d.rectangle([11, 21, 20, 21], fill=RED_LO)
    d.rectangle([15, 23, 16, 23], fill=RED_LO)
    return double(im)


def pop_sale():
    im, d = card(BLUE, BLUE_HI, BLUE_LO, WHITE, WHITE_LO)
    octopus(im, 16, 15, 6)
    return double(im)


ART = {
    'don-takote-sign': sign,
    'don-takote-wall': wall,
    'don-takote-wall-top': wall_top,
    'don-takote-pop-yen': pop_yen,
    'don-takote-pop-sale': pop_sale,
}


def main():
    preview = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    cfg = json.load(open('config.json'))
    out = []
    for name, make in ART.items():
        im = make()
        assert im.width % 64 == 0 and im.height % 64 == 0, (name, im.size)
        key = f'{name}_0_0'
        im.save(f'assets/sprites/{key}.png')
        # depthBias 1: these hang ON the wall panel behind them, which Y-sorts to
        # the same depth - the bias settles the tie (see shrine-top in tiled/README.md)
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        if not name.startswith('don-takote-wall'):
            cfg['spriteMetadata'][key]['depthBias'] = 1
        cfg.setdefault('tileNames', {})[key] = name
        out.append(im)
        print(f'{key}: {im.width // 64}x{im.height // 64} cells')
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    if preview:
        sheet = Image.new('RGBA', (sum(i.width + 16 for i in out) + 16, max(i.height for i in out) + 32), (60, 60, 70, 255))
        x = 16
        for i in out:
            sheet.alpha_composite(i, (x, 16)); x += i.width + 16
        sheet.save(preview)


if __name__ == '__main__':
    main()
