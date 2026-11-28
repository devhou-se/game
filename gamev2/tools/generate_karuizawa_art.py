#!/usr/bin/env python3
"""generate_karuizawa_art.py — draw Karuizawa's sprites (issues #68, #256).

Karuizawa is the fifth district of the stitched `TokyoCity`, out of Tokyo's
west gate (tools/generate_karuizawa.py). No asset pack has its art, so it is
drawn here the way tools/generate_hokuriku_art.py draws Hokuriku: shaded pixel
art in the GuttyKreum palette, at half size and pixel-doubled, with a 1px ink
outline.

  karuizawa-fingerpost_0_0     1x2  the fingerpost inside the gate: a wooden
                                    post on a stone foot, one cream arm pointing
                                    east (Tokyo), one west (up the road)

That is all of it for now (issue #260, part 1 of #256: the room and the gate).
The falls, the larches, the corn stall and the three shopfronts are added to
SPRITES by the tickets that build them.

Deterministic and idempotent: rewrites the PNGs in assets/sprites/ and
registers them in config.json spriteMetadata + tileNames. Needs Pillow.

Run from gamev2/ BEFORE generate_karuizawa.py:
    python3 tools/generate_karuizawa_art.py [--preview out.png]
"""
import json
import sys
from PIL import Image

from generate_hokkaido import (rgb, canvas, outline,
                               CREAM, CREAM_LO, CREAM_DK, WHITE, WOOD, WOOD_LO, WOOD_DK, STONE, STONE_LO)


def fingerpost():
    im, d = canvas(1, 2)                 # 32 x 64; it stands on the lower cell
    d.rectangle([14, 6, 17, 60], fill=WOOD); d.line([(17, 6), (17, 60)], fill=WOOD_LO)
    d.rectangle([13, 4, 18, 6], fill=WOOD_LO); d.line([(13, 4), (18, 4)], fill=WOOD)     # the cap
    d.rectangle([11, 59, 20, 62], fill=STONE_LO); d.line([(11, 59), (20, 59)], fill=STONE)
    # the arms: a board with a pointed end, a line of lettering, its lower edge in shadow
    for y, tip, back in ((10, 29, 9), (21, 2, 22)):         # east (Tokyo) above, west (the road) below
        x0, x1 = sorted((back, tip + (-4 if tip > back else 4)))
        d.rectangle([x0, y, x1, y + 7], fill=CREAM)
        d.polygon([(tip, y + 3), (tip, y + 4), (x1 if tip > back else x0, y + 7),
                   (x1 if tip > back else x0, y)], fill=CREAM)
        d.line([(x0, y), (x1, y)], fill=WHITE)
        d.line([(x0, y + 7), (x1, y + 7)], fill=CREAM_LO)
        for x in range(x0 + 2, x1 - 1, 2):                  # the name, too small to read
            d.point((x, y + 3), fill=WOOD_DK); d.point((x, y + 4), fill=CREAM_DK)
        d.point((15, y + 2), fill=WOOD_DK); d.point((16, y + 5), fill=WOOD_DK)           # the nails
    outline(im)
    return im


SPRITES = {      # key: (builder, scale, tileNames label)
    'karuizawa-fingerpost_0_0': (fingerpost, 2, 'karuizawa-fingerpost'),
}


def main():
    built = {}
    for key, (fn, scale, _) in SPRITES.items():
        im = fn()
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(f'assets/sprites/{key}.png')
        built[key] = im
        print(f'{key}: {im.width}x{im.height}px ({im.width // 64}x{im.height // 64} cells)')

    cfg = json.load(open('config.json'))
    for key, (_, _, label) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = label
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (sum(im.width + 16 for im in built.values()) + 16,
                                   max(im.height for im in built.values()) + 32), rgb('83af6f'))
        x = 16
        for im in built.values():
            sheet.alpha_composite(im, (x, sheet.height - 16 - im.height)); x += im.width + 16
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
