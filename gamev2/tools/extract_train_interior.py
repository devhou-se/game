#!/usr/bin/env python3
"""extract_train_interior.py — pull the car interiors out of the GuttyKreum
Train Interiors pack (Assets/GuttyKreum/TrainInteriors_v1) into gamev2 sprites.

The pack ships three ready-assembled car interiors as its preview images
(transparent background). We tight-crop each into a sprite the ride cutscene
(src/TrainTravel.js buildCutscene) shows behind the seated player:

  preview1 -> train-interior-metro   (blue/orange commuter car)
  preview2 -> train-interior-wood    (warm wood, green seats)
  preview3 -> train-interior-express (forward seat rows, luggage racks)

Kept at native (1x) resolution; the cutscene scales them with nearest-neighbour.

Run from gamev2/:  python3 tools/extract_train_interior.py
"""
from PIL import Image

PACK = '../Assets/GuttyKreum/TrainInteriors_v1'
CARS = {
    'train-interior-metro':   'preview1.png',
    'train-interior-wood':    'preview2.png',
    'train-interior-express': 'preview3.png',
}

for name, src in CARS.items():
    im = Image.open(f'{PACK}/{src}').convert('RGBA')
    im = im.crop(im.getbbox())          # drop the transparent margin
    im.save(f'assets/sprites/{name}.png')
    print(f'{name}: {im.size[0]}x{im.size[1]}px')
