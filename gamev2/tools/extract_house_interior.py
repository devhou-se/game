#!/usr/bin/env python3
"""extract_house_interior.py — the two pieces of a home that the asset packs
do have (issue #208).

None of the GuttyKreum packs is a home interior: they are exteriors
(Japanese City, Osaka, Dotonbori, Temples & Shrines, Train Station, Overgrown
Backstreets, Urban Accessories) plus the Train Interiors car, and there is no
LimeZu Modern_Interiors (Modern_Exteriors is 16px art in another style - see
buildings-and-street-props.md). So this takes what fits and
tools/generate_house_art.py draws the rest (tatami, shoji, futon, kotatsu...):

  home-wood-floor_0_0   1x1   plain floorboards - the wooden car floor of the
                              Train Interiors pack (GK_TI_A5), for the kitchen
                              corner and the boards round the hearth
  home-plant_0_0        1x1   a potted house plant - the Japanese City pack's
                              doorstep pot (GK_JC_B_2)

Both are cut at the packs' 32px tile and upscaled 2x NEAREST, like every
ported tile, and registered in config.json spriteMetadata + tileNames. The
plant is moved to stand on the bottom of its cell. Deterministic and
idempotent. Needs Pillow. Run from gamev2/:
    python3 tools/extract_house_interior.py [--preview out.png]
"""
import json
import sys
from PIL import Image

GK = '../art-source/GuttyKreum/'
# key: (sheet, crop box in native px, tileNames label, stand on the cell's bottom edge?)
SPRITES = {
    'home-wood-floor_0_0': (GK + 'TrainInteriors_v1/RPGMakerVXAce/GK_TI_A5.png', (0, 448, 32, 480), 'home-wood-floor', False),
    'home-plant_0_0': (GK + 'JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_B_2.png', (224, 192, 256, 224), 'home-plant', True),
}


def cut(sheet, box, stand):
    im = Image.open(sheet).convert('RGBA').crop(box)
    if stand:                       # the art alone, centred, feet two pixels above the cell's bottom edge
        art = im.crop(im.getbbox())
        assert art.width <= 32 and art.height <= 32, f'{sheet} {box}: the art is larger than a cell'
        im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        im.alpha_composite(art, ((32 - art.width) // 2, 30 - art.height))
    assert im.getbbox(), f'{sheet} {box}: nothing there'
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def main():
    built = {}
    for key, (sheet, box, _, stand) in SPRITES.items():
        built[key] = cut(sheet, box, stand)
        built[key].save(f'assets/sprites/{key}.png')
        print(f'{key}: {built[key].width}x{built[key].height}px from {sheet.split("/")[-1]} {box}')

    cfg = json.load(open('config.json'))
    for key, (_, _, label, _) in SPRITES.items():
        im = built[key]
        cfg['spriteMetadata'][key] = {'frameCount': 1, 'anchorX': 32 / im.width, 'anchorY': 32 / im.height}
        cfg.setdefault('tileNames', {})[key] = label
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        sheet = Image.new('RGBA', (16 + 80 * len(built), 96), (195, 201, 140, 255))
        for i, im in enumerate(built.values()):
            sheet.alpha_composite(im, (16 + 80 * i, 16))
        sheet.save(out)
        print('preview ->', out)


if __name__ == '__main__':
    main()
