#!/usr/bin/env python3
"""extract_train.py — slice the train cars from the GuttyKreum Train Station
pack (Assets/GuttyKreum/Train_Stationv8) into gamev2 sprites.

The pack is 16px-native; gamev2 cells are 64px, so trains upscale 4x NEAREST.
Crop rectangles were read off the sheet by hand (grid-overlay inspection).

Run from gamev2/:  python3 tools/extract_train.py
"""
from PIL import Image

SHEET = '../Assets/GuttyKreum/Train_Stationv8/Tilemaps/Non-RPGMaker/Maintilemap.png'
CROPS = {
    'train-green':  (258, 256, 414, 312),
    'train-orange': (508, 323, 676, 379),
}

im = Image.open(SHEET).convert('RGBA')
for name, region in CROPS.items():
    crop = im.crop(region)
    crop = crop.crop(crop.getbbox())
    big = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
    big.save(f'assets/sprites/{name}.png')
    print(f'{name}: {big.size[0]}x{big.size[1]}px')
