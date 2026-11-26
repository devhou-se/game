#!/usr/bin/env python3
"""Rebuild fonts/PixelMplus12-Grid.ttf from the original PixelMplus12-Regular.ttf (issue #153).

PixelMplus12 is the M+ 12px bitmap font traced as outlines, but on a 1000-unit em: one pixel is
83.33 units, rounded, and the pixel grid sits 0.4px off the baseline. A browser snaps the baseline
to a whole pixel, so every horizontal stroke came out as a blurred row at 12px and at 24px.

This moves every outline point onto an exact grid: a 1200-unit em, 100 units per pixel, with the
baseline where the M+ bitmap has it (11 rows above, 2 below). The shapes are the same pixels;
nothing is redrawn. At 12px and its multiples every glyph edge now lands on a pixel boundary.

    python3 tools/regrid_pixelmplus.py /path/to/PixelMplus12-Regular.ttf

Needs fontTools (`python3 -m pip install fonttools`). The original is the file in
https://github.com/itouhiro/PixelMplus (release v1.0.0); its hash is checked. The M+ FONT LICENSE
(fonts/PixelMplus12-LICENSE.txt) allows distribution with modification.
"""
import hashlib
import os
import sys

SOURCE_SHA256 = '02f19467ea7cc235cc06c570b7f6c3b0a12a6f682bc8d74c43f2d323d97bcd12'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'PixelMplus12-Grid.ttf')
PIXEL = 1000 / 12       # units per pixel in the original
BOTTOM = -200           # the original's lowest pixel row starts here
ROWS_BELOW = 2          # rows under the baseline in the M+ bitmap (and in the result)
UNIT = 100              # units per pixel in the result
NAME = 'PixelMplus12 Grid'
# .notdef is the one glyph FontForge drew off the grid (a thin box): the same box, a pixel thick
NOTDEF_X = {33: 100, 66: 200, 265: 400, 298: 500}
NOTDEF_Y = {0: 0, 33: 100, 633: 800, 666: 900}


def cell(value, origin):
    """An original coordinate as a whole number of pixels from `origin`; fails if it is not on the grid."""
    k = (value - origin) / PIXEL
    if abs(k - round(k)) > 0.02:
        raise SystemExit(f'coordinate {value} is not on the 12px grid')
    return round(k)


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    from fontTools.ttLib import TTFont
    with open(argv[1], 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f'{argv[1]} is not the PixelMplus12-Regular.ttf this tool was written for ({digest})')
    font = TTFont(argv[1])
    glyf, hmtx = font['glyf'], font['hmtx']
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.isComposite():
            raise SystemExit(f'{name} is a composite glyph; this tool only handles simple outlines')
        if glyph.numberOfContours > 0:
            if not all(flag & 1 for flag in glyph.flags):
                raise SystemExit(f'{name} has a curve; a pixel font should have none')
            for i, (x, y) in enumerate(glyph.coordinates):
                if name == '.notdef':
                    glyph.coordinates[i] = (NOTDEF_X[x], NOTDEF_Y[y])
                else:
                    glyph.coordinates[i] = (cell(x, 0) * UNIT, (cell(y, BOTTOM) - ROWS_BELOW) * UNIT)
            glyph.recalcBounds(glyf)
        advance, _ = hmtx[name]
        advance = 6 * UNIT if name == '.notdef' else cell(advance, 0) * UNIT
        hmtx[name] = (advance, glyph.xMin if glyph.numberOfContours > 0 else 0)
    rows = 13               # the M+ cell is 12 wide and 13 tall
    font['head'].unitsPerEm = 12 * UNIT
    hhea, os2 = font['hhea'], font['OS/2']
    hhea.ascent = os2.sTypoAscender = os2.usWinAscent = (rows - ROWS_BELOW) * UNIT
    hhea.descent = os2.sTypoDescender = -ROWS_BELOW * UNIT
    os2.usWinDescent = ROWS_BELOW * UNIT
    hhea.lineGap = os2.sTypoLineGap = 0
    os2.xAvgCharWidth = round(os2.xAvgCharWidth * 1.2)
    for tag in ('FFTM', 'cvt '):        # FontForge's timestamp, and hinting values nothing reads
        if tag in font:
            del font[tag]
    for record in font['name'].names:   # a changed font should not carry the original's name
        if record.nameID in (1, 4, 16):
            record.string = NAME
        elif record.nameID == 6:
            record.string = NAME.replace(' ', '-')
        elif record.nameID == 3:
            record.string = NAME + ' (regridded for devhou.se from PixelMplus12-Regular 1.0.0)'
    font['head'].modified = font['head'].created         # the same bytes on every run
    font.recalcTimestamp = False
    font.save(OUT)
    with open(OUT, 'rb') as f:
        data = f.read()
    print(f'{os.path.relpath(OUT)}: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main(sys.argv)
