# Fonts

| File | Family in the game | Used for |
|------|--------------------|----------|
| `PressStart2P-Regular.ttf` | `PressStart2P` | HUD bar, title screen, big overlay headings |
| `PixelOperatorMono.ttf` | `PixelOperatorMono` | dialogue, captions, menus and overlays |
| `PixelOperatorMono-Bold.ttf` | `PixelOperatorMonoBold` | name plates, labels, toasts, headings |
| `DotGothic16-Regular.ttf` | a second face of all three families | every Japanese character (kana, kanji, CJK and full-width punctuation) |

The three Latin fonts are loaded in `GameScene.preload`. They have no Japanese glyphs, so
`src/utils/JapaneseFont.js` adds DotGothic16 to each family with a `unicode-range` limited to the
Japanese blocks; see that file for how and when it is loaded.

## DotGothic16

- Designed by Fontworks Inc. — Copyright 2020 The DotGothic16 Project Authors
  (https://github.com/fontworks-fonts/DotGothic16).
- Licensed under the SIL Open Font License 1.1: `DotGothic16-OFL.txt`, shipped beside the font as the
  licence requires.
- The file is the unmodified `DotGothic16-Regular.ttf` from the Google Fonts repository
  (`github.com/google/fonts`, `ofl/dotgothic16/`), 2,069,236 bytes, SHA-256
  `3ad9af88726d42b40f7f365f0dcac785af73cf20ea6f1d5b44e57cc21150b8f1`.
  It is not subset: blog posts can bring any kanji, and the full JIS set is 2 MB fetched once after boot.

To update it, download the same two files again (`DotGothic16-Regular.ttf`, and `OFL.txt` saved as
`DotGothic16-OFL.txt`) and refresh the size and hash above.
