#!/usr/bin/env python3
"""house_look.py — the shared helpers of the GuttyKreum house look (issue #279).

The recipe is written in docs/generators-and-checks.md ("House look:
GuttyKreum"): colours of the sheets only, taken as ramps whose shadows turn in
hue rather than darken toward black; a 1px ink silhouette; light from the
upper left; 8 to 16 colours for a sprite of a cell or two; no flat face. This
module is what a tool draws that look with. tools/generate_ads.py is the
first; the redraws after it (#280 to #284) use it too.

It is a leaf: it imports the standard library and Pillow only, never line_art
or a generator (line_art imports three generators for its palette, and the
generators will import this). It reuses by shape instead: a material is
line_art's (base, hi, lo, line) tuple, so line_art.paint takes it as it is,
and outline() is generate_hokkaido.outline's rule.

Rectangles, pixel access and 1-bit text only: no polygon, ellipse, arc or line
in the output path, so every Pillow paints the same pixels. Importing this has
no side effects. Draw at half size (32px a cell) and double().

Run from gamev2/, for a contact sheet to look at a redraw beside the sheets:

    python3 tools/house_look.py --sheet OUT.png [--scale N] PNG...
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont


def rgb(hex_):
    """'0a1627' -> (10, 22, 39, 255)."""
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


CLEAR = (0, 0, 0, 0)
INK = rgb('0a1627')             # the silhouette: every GuttyKreum object is edged in it
INK_DEEP = rgb('080d16')

# Ramps, dark to light. Every tone is a colour of the sheets in ../art-source/GuttyKreum
# (tools/tests/house-look.test.js holds it). The shadows turn in hue, not toward black.
RAMPS = {name: [rgb(t) for t in tones.split()] for name, tones in {
    'red':    '8a3a22 aa4d31 d16b56 e78d7b ffe2e0',
    'orange': '904a37 aa4d31 ce6a42 f6a583 ffe2e0',
    'gold':   '86624f a7843b c6a663 f3d890 fafcfd',
    'green':  '2e4040 395050 506b6b 6c8e7f 93c297',
    'blue':   '172459 314b8e 425faa 5a86de 7db9fa bbe9ff',
    'purple': '2a233b 3c396d 444679 8f72b6 bfabd7 c9cbff',
    'pink':   '83374f bb6479 ff9b92 ffe2e0',
    'steel':  '2a2636 47485d 575f79 848295 a4b0b5 dae2e4',
    'cream':  '8e7366 be9e8c e4cecc fafcfd',
    'night':  '080d16 0a1627 191c2a 2c2d51 444679',
}.items()}


def tone(ramp, i):
    """RAMPS[ramp][i], clamped to the ramp."""
    tones = RAMPS[ramp]
    return tones[max(0, min(len(tones) - 1, i))]


def material(ramp, i):
    """(base, hi, lo, line): tones i, i+1, i-1 and i-2 of the ramp, line_art's order."""
    return tone(ramp, i), tone(ramp, i + 1), tone(ramp, i - 1), tone(ramp, i - 2)


def palette():
    """Every tone of every ramp, and the ink."""
    return {t for tones in RAMPS.values() for t in tones} | {INK, INK_DEEP}


# ---- canvases ----------------------------------------------------------------------
def canvas(w, h):
    """A clear RGBA image."""
    return Image.new('RGBA', (w, h), CLEAR)


def double(im):
    """Half size to the game's size: every pixel a 2x2 block."""
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def fill(im, box, colour):
    """Paint the box (x0, y0, x1, y1), corners inclusive."""
    x0, y0, x1, y1 = box
    if x1 >= x0 and y1 >= y0:
        im.paste(colour, (x0, y0, x1 + 1, y1 + 1))


def outline(im, ink=INK):
    """A 1px ink line on the clear pixels 4-adjacent to drawn ones (the rule of
    generate_hokkaido.outline): the silhouette, corners left clear."""
    px, (w, h) = im.load(), im.size
    edge = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 0 and any(
        0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px[x, y] = ink


def bevel(im, box, mat):
    """Light from the upper left: `hi` on the box's top row and left column, `lo`
    on its bottom row and right column (`lo` wins the corners)."""
    _, hi, lo, _ = mat
    x0, y0, x1, y1 = box
    fill(im, (x0, y0, x1, y0), hi)
    fill(im, (x0, y0, x0, y1), hi)
    fill(im, (x0, y1, x1, y1), lo)
    fill(im, (x1, y0, x1, y1), lo)


def scanlines(im, box, a, b):
    """Rows alternate a, b from the top: a lit box, courses, planks."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        fill(im, (x0, y, x1, y), a if (y - y0) % 2 == 0 else b)


def shade(im, box, mat, part=3):
    """A painted face: `base`, its top row `hi`, the lowest 1/part of the rows
    `lo`, joined to the rest by exactly one checker-dithered row."""
    base, hi, lo, _ = mat
    x0, y0, x1, y1 = box
    fill(im, box, base)
    fill(im, (x0, y0, x1, y0), hi)
    low = (y1 - y0 + 1) // part
    if low:
        fill(im, (x0, y1 - low + 1, x1, y1), lo)
        y = y1 - low
        if y > y0:
            px = im.load()
            for x in range(x0, x1 + 1):
                if (x + y) % 2:
                    px[x, y] = lo


def pixmap(rows, colours):
    """A hand-set picture: one character a pixel, '.' clear, every other
    character a key of `colours` (the way generate_hokkaido.GLYPHS is written)."""
    im = canvas(max(len(r) for r in rows), len(rows))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                px[x, y] = colours[ch]
    return im


def stamp(im, picture, x, y, colour=None):
    """Paste a picture's drawn pixels at (x, y), all in `colour` if one is given
    (a shadow, a silhouette)."""
    mask = picture.getchannel('A').point(lambda v: 255 if v else 0)
    im.paste(colour if colour else picture, (x, y), mask)


# ---- text: the game's Japanese pixel font at its own size ------------------------------
FONT = 'fonts/PixelMplus12-Grid.ttf'      # from gamev2/, as generate_station_art.py reads it
SMALL_KANA = set('ッャュョァィゥェォ')
_FONT = []


def _font():
    if not _FONT:
        _FONT.append(ImageFont.truetype(FONT, 12))
    return _FONT[0]


def _ink(s):
    """s set in one line, 1-bit, cropped to its ink: an 'L' mask of 0 and 255."""
    f = _font()
    im = Image.new('L', (int(f.getlength(s)) + 4, 18), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'        # no anti-aliasing: pixel fonts stay pixels
    d.text((0, 0), s, font=f, fill=255)
    box = im.getbbox()
    return im.crop(box) if box else Image.new('L', (0, 0), 0)


def _glyph_cell(ch):
    """One glyph in its em cell (12 or 6 wide, 13 high), as vertical text sets it."""
    f = _font()
    w = int(f.getlength(ch))
    im = Image.new('L', (max(w, 1), 13), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((0, 0), ch, font=f, fill=255)
    if ch == 'ー':          # stands upright in vertical text, as the sheets' ビール does
        sq = Image.new('L', (12, 12), 0)
        sq.paste(im.crop((0, 0, 12, 12)), (0, 0))
        im = sq.transpose(Image.ROTATE_90)
    elif ch in SMALL_KANA:  # sits in the upper right of its cell
        moved = Image.new('L', im.size, 0)
        moved.paste(im, (2, -2))
        im = moved
    return im


def _vertical(s, pitch):
    cells = [_glyph_cell(ch) for ch in s]
    w = max(c.width for c in cells)
    im = Image.new('L', (w, pitch * (len(s) - 1) + 13), 0)
    for i, c in enumerate(cells):
        im.paste(c, ((w - c.width) // 2, i * pitch), c)
    box = im.getbbox()
    return im.crop(box) if box else Image.new('L', (0, 0), 0)


def text_mask(s, vertical=False, pitch=12):
    """The ink of s: one line, or one glyph a `pitch` rows when vertical."""
    return _vertical(s, pitch) if vertical else _ink(s)


def text_size(s, vertical=False, pitch=12):
    """The (w, h) of s's ink box."""
    return text_mask(s, vertical, pitch).size


def text(im, x, y, s, colour, shadow=None, vertical=False, pitch=12):
    """Set s with its ink box's top left at (x, y); `shadow` is stamped first at
    (+1, +1). Returns the ink box's (w, h)."""
    mask = text_mask(s, vertical, pitch)
    if shadow:
        im.paste(shadow, (x + 1, y + 1), mask)
    im.paste(colour, (x, y), mask)
    return mask.size


# ---- contact sheets ------------------------------------------------------------------
def sheet(images, out, width=960, pad=8, scale=1, bg=(90, 96, 104)):
    """Images (or paths) flowed left to right in the order given, wrapping at
    `width`, on a plain ground: for looking at a redraw beside the sheets."""
    ims = [Image.open(i).convert('RGBA') if isinstance(i, str) else i for i in images]
    ims = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in ims]
    rows, row, x = [], [], pad
    for i in ims:
        if row and x + i.width + pad > width:
            rows.append(row)
            row, x = [], pad
        row.append(i)
        x += i.width + pad
    if row:
        rows.append(row)
    w = max([pad + sum(i.width + pad for i in r) for r in rows] or [pad])
    h = pad + sum(max(i.height for i in r) + pad for r in rows)
    out_im = Image.new('RGBA', (w, h), bg + (255,))
    y = pad
    for r in rows:
        x = pad
        for i in r:
            out_im.alpha_composite(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in r) + pad
    if os.path.dirname(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
    out_im.save(out)
    return out_im


def main():
    ap = argparse.ArgumentParser(description='a contact sheet of PNGs, in the order given')
    ap.add_argument('--sheet', required=True, metavar='OUT.png')
    ap.add_argument('--scale', type=int, default=1)
    ap.add_argument('--width', type=int, default=960)
    ap.add_argument('pngs', nargs='+')
    args = ap.parse_args()
    sheet(args.pngs, args.sheet, width=args.width * args.scale, scale=args.scale)
    print(f'{len(args.pngs)} image(s) -> {args.sheet}')


if __name__ == '__main__':
    main()
