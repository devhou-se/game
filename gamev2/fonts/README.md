# Fonts

| File | Family in the game | Used for |
|------|--------------------|----------|
| `PressStart2P-Regular.ttf` | `PressStart2P` | HUD bar, title screen, big overlay headings |
| `PixelOperatorMono.ttf` | `PixelOperatorMono` | dialogue, captions, menus and overlays |
| `PixelOperatorMono-Bold.ttf` | `PixelOperatorMonoBold` | name plates, labels, toasts, headings |
| `PixelMplus12-Grid.ttf` | a second face of all three families | every Japanese character (kana, kanji, CJK and full-width punctuation) |

The three Latin fonts are loaded in `GameScene.preload`. They have no Japanese glyphs, so
`src/utils/JapaneseFont.js` adds PixelMplus12 to each family with a `unicode-range` limited to the
Japanese blocks; see that file for how and when it is loaded.

## PixelMplus12

- PixelMplus by itouhiro (https://github.com/itouhiro/PixelMplus) - Copyright (C) 2013 itouhiro,
  Copyright (C) 2002-2013 M+ FONTS PROJECT. It is the M+ 12px bitmap font (M+ BITMAP FONTS) traced as
  outlines: every JIS level 1 and level 2 kanji, kana, and the JIS symbols.
- Licensed under the M+ FONT LICENSE: `PixelMplus12-LICENSE.txt` (the `mplus_bitmap_fonts/LICENSE_E`
  of the release, unchanged), shipped beside the font. It allows use, copying and distribution
  "with or without modification, either commercially or noncommercially".
- **The file is modified.** The original is `PixelMplus12-Regular.ttf` from release v1.0.0
  (`PixelMplus-20130602.zip`, the same file as in the repository root), 1,274,396 bytes, SHA-256
  `02f19467ea7cc235cc06c570b7f6c3b0a12a6f682bc8d74c43f2d323d97bcd12`. It has a 1000-unit em, so a pixel
  is 83.33 units and the pixel grid sits 0.4px off the baseline; a browser snaps the baseline to a whole
  pixel, which blurred every horizontal stroke. `tools/regrid_pixelmplus.py` moves each outline point
  onto an exact grid (1200-unit em, 100 units a pixel, baseline where the M+ bitmap has it: 11 rows
  above, 2 below), redraws nothing, and names the result "PixelMplus12 Grid". The result is
  `PixelMplus12-Grid.ttf`, 1,311,776 bytes, SHA-256
  `a90a6d3c75697b636853d8008c88b3fb6690e15be0b4c1a8ab00d44cf81fb132`.
- It is not subset: blog posts can bring any kanji, and the full JIS set is 1.3 MB fetched once after boot.
- It is crisp where the text size is a multiple of 12px (the 24px dialogue and name plate).
  At 14, 16, 20 and 32px it is scaled like any outline font and its edges are soft, as the
  PixelOperator faces (a 16px grid) are at 24px.

To rebuild it, download the original, then (needs fontTools, `python3 -m pip install fonttools`):

```bash
python3 tools/regrid_pixelmplus.py /path/to/PixelMplus12-Regular.ttf
```

The tool checks the original's hash and writes the same bytes every time; a unit test
(`tools/tests/fonts.test.js`) checks that the glyphs the game ships are on the grid.
