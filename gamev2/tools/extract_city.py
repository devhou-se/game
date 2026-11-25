#!/usr/bin/env python3
"""extract_city.py — assemble the generic city buildings (issue #18) out of the
GuttyKreum tile sheets in ../Assets/GuttyKreum into gamev2 sprites.

  highrise-yellow_0_0     4x8   ochre office block      (Osaka pack, GK_Osaka_C_2)
  highrise-blue_0_0       5x11  blue-grey office block  (Osaka pack, GK_Osaka_C_2)
  highrise-glass_0_0      4x10  glass curtain-wall tower (Dotonbori pack, GK_DB_B)
  highrise-apartment_0_0  5x8   tiled-balcony apartment block (Japanese City, GK_JC_C_2)
  midrise-apartment_0_0   5x6   the same block two floors lower (fits a forecourt)
  discount-store_0_0      5x8   the multi-storey discount store ("Don Quijote"):
                                Dotonbori department-store facade + glass doors
                                under a generated yellow/blue parody sign
  machiya-black/red/blue_0_0  5x5  two-storey Kyoto townhouse shopfront
                                (Japanese City, GK_JC_C_2 — three roof colours)

Unlike extract_dotonbori.py these are not single crops: the sheets are RPG
Maker tile kits (a roof cap, one window floor, a ground floor, roof edges...),
so each building is ASSEMBLED here from named pieces — window floors are
repeated to make a block as tall as wanted, the middle column is repeated to
make it wider, and the machiya roof is tiled from its edge/ridge/body pieces.
Every piece rectangle was read off the sheet by hand (grid-overlay
inspection) and is in sheet pixels.

SCALE IS 2x, NOT 4x. One 32px RPG Maker tile is one 64px game cell — that is
the scale every ported building already uses (assets/sprites/building-roof-*
is pixel-identical to a 2x crop of GK_JC_B_2.png), so a door is one cell wide
and the pixels are the same size as the houses, konbini and floors next door.
(The Dotonbori arch / ferris wheel from extract_dotonbori.py are deliberately
4x — oversized landmarks — do not copy that scale for street buildings.)

The discount store's sign is drawn here in the style of tools/generate_ads.py
(same font / pixel-text helpers) and, like that pool, carries no real
branding: ドン・タコーテ ("Don Takote", an octopus instead of a penguin).

Registers every key in config.json spriteMetadata + tileNames (the game only
loads a tile that has a spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE make_prefabs.py:
    python3 tools/extract_city.py [--preview out.png]
"""
import json, sys
from PIL import Image, ImageDraw
import generate_ads as ads

GK = '../Assets/GuttyKreum/'
SHEETS = {
    'osaka': GK + 'Osaka_V5/RPGMakerVXAce/GK_Osaka_C_2.png',
    'city':  GK + 'JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_C_2.png',
    'doton': GK + 'DotonboriCity_v3/RPGMakerVXAce/GK_DB_B.png',
}
T = 32          # one RPG Maker tile = one game cell, in sheet pixels
SCALE = 2       # sheet pixel -> game pixel (64px cells)
_sheet = {}


def sheet(name):
    if name not in _sheet:
        _sheet[name] = Image.open(SHEETS[name]).convert('RGBA')
    return _sheet[name]


class Canvas:
    """A building under assembly, w x h cells, in sheet pixels."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w * T, h * T), (0, 0, 0, 0))

    def blit(self, src, box, at):
        """Copy sheet rectangle box=(x0, y0, x1, y1) to at=(x, y), alpha-composited."""
        self.im.alpha_composite(sheet(src).crop(box), at)

    def row(self, src, y0, y1, xs, y, x=0):
        """Lay the column strips xs=[(x0, x1), ...] of sheet rows y0..y1 left to
        right, starting at canvas (x, y)."""
        for (x0, x1) in xs:
            self.blit(src, (x0, y0, x1, y1), (x, y))
            x += x1 - x0


def cols(x0, width):
    """left, middle, right 32px columns of a 3-tile-wide kit starting at x0,
    stretched to `width` cells by repeating the middle one."""
    return [(x0, x0 + T)] + [(x0 + T, x0 + 2 * T)] * (width - 2) + [(x0 + 2 * T, x0 + 3 * T)]


# ---- office blocks (GK_Osaka_C_2: yellow at x=0, blue at x=128) -----------------
def office(x0, w, floors, door_col):
    """Roof cap + `floors` window floors (alternating the lit and the dark
    window band) + the two-cell ground floor with the door in column door_col."""
    c = Canvas(w, 1 + floors + 2)
    c.row('osaka', 288, 320, cols(x0, w), 0)
    for i in range(floors):
        band = 320 if i % 2 == 0 else 352
        c.row('osaka', band, band + T, cols(x0, w), T * (1 + i))
    plain = (x0 + 96, x0 + 128)                     # windowless wall filler
    ground = [(x0, x0 + T)] + [plain] * (w - 2) + [(x0 + 64, x0 + 96)]
    ground[door_col] = (x0 + T, x0 + 2 * T)          # the window + double door column
    c.row('osaka', 384, 448, ground, T * (1 + floors))
    return c, door_col


# ---- glass tower (GK_DB_B, the 3-tile curtain wall at x=256) -------------------
def glass(w, bands):
    """Flat roof slab + curtain-wall bands (B lit, X mixed, G blinds, O orange
    spandrel) + a glass lobby. The sheet's roof piece is a top-down rim with a
    hollow middle; one cell of it (top edge over bottom edge) makes the cap."""
    X0 = 256
    c = Canvas(w, 1 + len(bands) + 1)
    slab = Image.new('RGBA', (w * T - 8, 20), (104, 112, 138, 255))   # the roof deck inside the rim
    c.im.alpha_composite(slab, (4, 6))
    c.row('doton', 0, 16, cols(X0, w), 0)
    c.row('doton', 80, 96, cols(X0, w), 16)
    ys = {'B': 96, 'X': 128, 'G': 160, 'O': 192}
    for i, b in enumerate(bands):
        c.row('doton', ys[b], ys[b] + T, cols(X0, w), T * (1 + i))
    # lobby: emblem glass, the sliding double door, emblem glass
    door = (w - 2) // 2
    lobby = [(0, 32)] * w
    lobby[door], lobby[door + 1] = (32, 64), (64, 96)
    c.row('doton', 480, 512, lobby, T * (1 + len(bands)))
    return c, door


# ---- apartment block (GK_JC_C_2, 5 tiles wide at x=256) ------------------------
def apartment(floors):
    """Blue tiled roof + balcony floors (plants / laundry / windows, cycled) +
    a ground floor with the entrance in the middle."""
    X0, W = 256, 5
    c = Canvas(W, 1 + floors + 1)
    c.row('city', 224, 256, cols(416, W), 0)
    kinds = [256, 288, 320]
    for i in range(floors):
        y = kinds[i % 3]
        c.blit('city', (X0, y, X0 + W * T, y + T), (0, T * (1 + i)))
    gy = T * (1 + floors)
    c.blit('city', (X0, 320, X0 + W * T, 352), (0, gy))
    c.blit('city', (X0, 352, X0 + T, 384), (2 * T, gy))      # the dark double door
    return c, 2


# ---- discount store (GK_DB_B department-store facade + generated sign) ---------
SIGN = dict(text='ドン・タコーテ', sub='なんでも激安  24h', yellow='#f9c22e', blue='#1155a8',
            ink='#1c1c22', red='#c62828')


def store_sign(w, h):
    """The rooftop sign, drawn at sheet resolution so its pixels match the
    facade's once everything is scaled: yellow board, blue price band, red
    octopus mascot. generate_ads.py style — parody name, no real branding."""
    ads.FONT_PATH, ads.FONT_INDEX = ads.find_font()
    s = SIGN
    im = Image.new('RGBA', (w, h), s['yellow'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=s['ink'], width=2)
    d.rectangle([2, 2, w - 3, h - 3], outline=s['red'], width=1)
    band = 15                                              # blue hook band along the bottom
    d.rectangle([3, h - 3 - band, w - 4, h - 4], fill=s['blue'])
    ads.paste_center(im, ads.fit_text(s['sub'], w - 16, band - 4, '#ffffff'), w / 2, h - 4 - band / 2)
    for x in range(8, w - 8, 8):                           # marquee bulbs
        d.rectangle([x, 5, x + 1, 6], fill=s['red'])
    # mascot: a round red octopus on the left
    cx, cy, r = 21, 25, 11
    d.ellipse([cx - r, cy - r, cx + r, cy + r - 2], fill=s['red'], outline=s['ink'])
    for i, lx in enumerate(range(cx - r + 1, cx + r, 5)):
        d.rectangle([lx, cy + r - 4, lx + 2, cy + r + (1 if i % 2 else 3)], fill=s['red'], outline=s['ink'])
    for ex in (cx - 5, cx + 3):
        d.rectangle([ex, cy - 4, ex + 2, cy - 1], fill='#ffffff')
        d.point([ex + 1, cy - 2], fill=s['ink'])
    d.line([cx - 3, cy + 3, cx + 3, cy + 3], fill=s['ink'])
    name = ads.fit_text(s['text'], w - 46, 26, s['ink'])
    ads.paste_center(im, name, 38 + (w - 44) / 2, 9 + (h - band - 14) / 2)
    return im


def store():
    """Sign (2 cells) over the five-storey glass facade over a row of glass doors."""
    W = 5
    c = Canvas(W, 8)
    c.im.alpha_composite(store_sign(W * T, 2 * T), (0, 0))
    c.blit('doton', (0, 320, 160, 480), (0, 2 * T))
    # ground floor: emblem glass | sliding doors | emblem glass
    c.row('doton', 480, 512, [(0, 32), (0, 32), (192, 224), (0, 32), (0, 32)], 7 * T)
    return c, 2


# ---- machiya (GK_JC_C_2: black at y=32, red at y=192, blue at y=352) -----------
def machiya(oy):
    """Two-storey townhouse, 5 cells wide — machiya are narrow, and three of
    them make a lane. The sheet lays the kit out as a 7-tile house (ground
    floor + pent roof ready-made, the upper storey 6 tiles, the main roof only
    as its edge / ridge / body pieces), so the narrow house is cut from it:
    drop one tile of plaster from the upper wall and pull its right hip in,
    tile the main roof to that width, and keep the shop, door, lattice and end
    wall of the ground floor. oy = the variant's y offset on the sheet."""
    c = Canvas(5, 5)
    Y = lambda y: y + oy                                  # sheet y for this variant
    # main roof, canvas rows 0-1 (12px of sky above the ridge)
    c.blit('city', (24, Y(12), 64, Y(32)), (24, 12))                  # ridge: left corner + first tile
    for x in (64, 96):
        c.blit('city', (32, Y(12), 64, Y(32)), (x, 12))               # ridge tiles
    c.blit('city', (160, Y(12), 168, Y(32)), (128, 12))               # ridge right corner
    c.blit('city', (24, Y(32), 32, Y(64)), (24, 32))                  # body left edge
    for x in (32, 64, 96):
        c.blit('city', (128, Y(32), 160, Y(64)), (x, 32))             # body tiles
    c.blit('city', (160, Y(32), 168, Y(64)), (128, 32))               # body right edge
    # upper storey: left hip + lattice window, the plaster wall, right hip
    c.blit('city', (0, Y(40), 64, Y(96)), (0, 40))
    c.blit('city', (96, Y(64), 168, Y(96)), (64, 64))
    c.blit('city', (168, Y(40), 192, Y(96)), (136, 40))
    # lower pent roof: left hip, tiles, the shop sign, right hip
    c.row('city', Y(96), Y(120), [(0, 32), (64, 96), (96, 128), (128, 160), (192, 224)], 96)
    # ground floor: open shopfront (2), door, lattice, end wall
    c.row('city', Y(120), Y(160), [(32, 160), (192, 224)], 120)
    return c, 2


BUILDINGS = {
    'highrise-yellow':    lambda: office(0, 4, 5, 1),
    'highrise-blue':      lambda: office(128, 5, 8, 2),
    'highrise-glass':     lambda: glass(4, 'BXGBXGBO'),
    'highrise-apartment': lambda: apartment(6),
    'midrise-apartment':  lambda: apartment(4),      # the same block, two floors lower
    'discount-store':     store,
    'machiya-black':      lambda: machiya(32),
    'machiya-red':        lambda: machiya(192),
    'machiya-blue':       lambda: machiya(352),
}


def main():
    preview = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    cfg = json.load(open('config.json'))
    out = []
    for name, make in BUILDINGS.items():
        c, door = make()
        big = c.im.resize((c.im.width * SCALE, c.im.height * SCALE), Image.NEAREST)
        assert big.width % 64 == 0 and big.height % 64 == 0, (name, big.size)
        key = f'{name}_0_0'
        big.save(f'assets/sprites/{key}.png')
        # multi-cell sprites anchor on the centre of their top-left cell. Not
        # rounded: 32/704 to 4 places put the 11-cell tower 0.03px off the grid.
        cfg['spriteMetadata'][key] = {'frameCount': 1,
                                      'anchorX': 32 / big.width,
                                      'anchorY': 32 / big.height}
        cfg.setdefault('tileNames', {})[key] = name
        out.append(big)
        print(f'{key}: {c.w}x{c.h} cells, door column {door}')
    json.dump(cfg, open('config.json', 'w'), indent=2, sort_keys=True)
    if preview:                                            # contact sheet for eyeballing
        sheet_im = Image.new('RGBA', (sum(b.width + 32 for b in out) + 32, max(b.height for b in out) + 64),
                             (120, 160, 120, 255))
        x = 32
        for b in out:
            sheet_im.alpha_composite(b, (x, sheet_im.height - 32 - b.height))
            x += b.width + 32
        sheet_im.save(preview)


if __name__ == '__main__':
    main()
