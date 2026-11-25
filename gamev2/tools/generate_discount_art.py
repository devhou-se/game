#!/usr/bin/env python3
"""generate_discount_art.py — interior signage for the Don Takote discount
store (issue #91): the pieces tools/generate_discount_stores.py dresses the
shop floor with.

  don-takote-sign_0_0      5x2  the facade's own sign board, hung on the back wall
  don-takote-wall_0_0      1x1  back-wall panel, lower row: yellow over the blue price band
  don-takote-wall-top_0_0  1x1  back-wall panel, upper row: plain yellow under a red trim
  don-takote-pop-yen_0_0   1x1  wall POP card: red ¥ on a yellow burst
  don-takote-pop-sale_0_0  1x1  wall POP card: the octopus mascot on blue

Nothing is invented: the sign and the mascot are CUT from the facade sprite
(assets/sprites/discount-store_0_0.png, drawn by tools/extract_city.py), and
the panels use that sign's four colours, so inside and outside are one shop.
Because it starts from the finished facade it needs no Japanese font (unlike
extract_city.py) - re-run it after extract_city.py changes the sign.

Like the facade's, the art is drawn at half size and pixel-doubled, so its
pixels are the size of the furniture next to it. Registers every key in
config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/:  python3 tools/generate_discount_art.py [--preview out.png]
"""
import json, sys
from PIL import Image, ImageDraw

FACADE = 'assets/sprites/discount-store_0_0.png'
YELLOW, BLUE, INK, RED, WHITE = '#f9c22e', '#1155a8', '#1c1c22', '#c62828', '#ffffff'
SHADE = '#d9a21c'                       # the yellow, one step down (panel seams)


def double(im):
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def sign():
    """The whole rooftop board: the top two cells of the facade."""
    return Image.open(FACADE).convert('RGBA').crop((0, 0, 320, 128))


def mascot():
    """The red octopus off the sign, at half size (as it was drawn), on transparent."""
    im = Image.open(FACADE).convert('RGBA').crop((16, 24, 68, 84)).resize((26, 30), Image.NEAREST)
    px = im.load()
    bg = tuple(int(YELLOW[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][:3] == bg:
                px[x, y] = (0, 0, 0, 0)
    return im


def wall():
    """One cell of back wall: yellow panel, blue band with white price dashes
    along the bottom, a skirting line where it meets the floor."""
    im = Image.new('RGBA', (32, 32), YELLOW)
    d = ImageDraw.Draw(im)
    d.line([31, 0, 31, 20], fill=SHADE)                    # panel seam
    d.rectangle([0, 21, 31, 28], fill=BLUE)
    for x in range(3, 30, 8):
        d.rectangle([x, 24, x + 3, 25], fill=WHITE)
    d.rectangle([0, 29, 31, 31], fill=INK)
    return double(im)


def wall_top():
    """The panel row above it: plain yellow, trimmed in red along the ceiling."""
    im = Image.new('RGBA', (32, 32), YELLOW)
    d = ImageDraw.Draw(im)
    d.line([0, 0, 31, 0], fill=INK)
    d.rectangle([0, 1, 31, 2], fill=RED)
    d.line([31, 3, 31, 31], fill=SHADE)                    # panel seam
    return double(im)


def card(fill, edge):
    """A POP card hanging on two strings; returns (image, draw)."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in (9, 22):
        d.line([x, 0, x, 5], fill=INK)
    d.rectangle([4, 5, 27, 27], fill=fill, outline=INK)
    d.rectangle([5, 6, 26, 26], outline=edge)
    return im, d


def pop_yen():
    im, d = card(YELLOW, RED)
    # a chunky yen sign: the Y, then the two bars
    for i in range(5):
        d.rectangle([10 + i, 9 + i, 11 + i, 10 + i], fill=RED)
        d.rectangle([20 - i, 9 + i, 21 - i, 10 + i], fill=RED)
    d.rectangle([15, 14, 16, 23], fill=RED)
    d.rectangle([11, 16, 20, 17], fill=RED)
    d.rectangle([11, 20, 20, 21], fill=RED)
    return double(im)


def pop_sale():
    im, d = card(BLUE, WHITE)
    m = mascot().resize((18, 20), Image.NEAREST)
    im.alpha_composite(m, (7, 7))
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
