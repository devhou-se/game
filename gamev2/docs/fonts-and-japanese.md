# Fonts and Japanese text

The three pixel fonts and the Japanese face added to each.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Fonts and Japanese Text (issue #78)

The game draws text in three pixel fonts, loaded in `GameScene.preload` and used by family name
everywhere: `PressStart2P` (HUD, title), `PixelOperatorMono` (dialogue, captions, overlays) and
`PixelOperatorMonoBold` (name plates, labels, toasts). None has kana or kanji, and blog-derived dialogue
and post titles are sometimes Japanese.

- **One Japanese face for all three**: `fonts/PixelMplus12-Grid.ttf` (PixelMplus12, M+ FONT LICENSE, every
  JIS level 1 and 2 kanji - credit, licence and hashes in `fonts/README.md`). It is the M+ 12px bitmap
  font, so it is pixel-exact at 12px and at the 24px the dialogue and name plate use (#153;
  DotGothic16, which it replaced, is a 16px design and was soft there). The shipped file is the original
  moved onto an exact pixel grid by `tools/regrid_pixelmplus.py` - the original's grid sits 0.4px off the
  baseline, which blurs every horizontal stroke; do not swap the original back in. At 14, 16, 20 and
  32px it is scaled and soft, as the PixelOperator faces (16px grid) are at 24px: text that should be
  crisp in Japanese wants a size that is a multiple of 12. `src/utils/JapaneseFont.js`
  registers it as a second `FontFace` of each family, limited by `unicode-range` to the Japanese blocks
  (`JapaneseFont.RANGES`), so the browser picks it per character. Every existing
  `fontFamily: 'PixelOperatorMono'`, the canvas measuring in `DialogueManager`, and the creator's DOM
  input get Japanese glyphs with no change at the call site - **do not add a font stack or a second
  family name for Japanese**; a new family needs only a `load.font` line and an entry in
  `JapaneseFont.FAMILIES` (a unit test keeps the two in step). Latin text, arrows and the d-pad glyphs
  are outside the ranges and render exactly as before; a character PixelMplus12 lacks falls back to the
  system font.
- **Loading**: 1.3 MB, so it is not in the boot queue. `GameScene.preload` starts `JapaneseFont.load` when
  the Phaser loader completes; it fetches the file once (one buffer shared by the three faces) and then
  `JapaneseFont.refresh` redraws any Text object already showing Japanese (canvas text drawn before a font
  is ready stays in the fallback otherwise). If the fetch fails the game warns and carries on with the
  system font, and `JapaneseFont.retry` (called by `DialogueManager.show`) fetches again the next time a
  dialogue opens. Kana and kanji are one em wide in both, so wrapping does not change when it arrives.
- **Metrics**: Phaser sizes a line box from the Latin font (ascent 18px at 24px); the Japanese cell is 11
  rows of 12 above the baseline and 2 below, so its glyphs stand up to 4px taller at 24px. Text with
  padding (name plate, caption, toasts) has room; the dialogue text has
  `DialogueManager.TEXT_PAD_TOP` blank rows above its first line for this (and `TEXT_PAD_BOTTOM`, one row
  under the last line for the full-width brackets, which layout does not count), and `layout()` still adds 8px
  of leading to a line with Japanese in it so rows do not touch. An unpadded Text that may show Japanese
  needs the same top padding - and in `PressStart2P`, whose box has no descent, a row of bottom padding:
  call `JapaneseFont.fit(text)` after its text is set (and after a `setText` that may change it). It pads
  top and bottom by `padRows` (a sixth of an em) only while the text has Japanese in it, so Latin text is
  untouched and a vertically centred Text does not move; a bottom-anchored Text in a PixelOperator face
  (the descent holds the glyphs, bar the lowest row of a full-width bracket) passes `{ below: false }` so its baseline does not lift. The HUD
  room name, the Character screen rows and the created player's name label (top only) use it (#155); the other overlay `text()` helpers show Latin only today.
- Signage is not text: the ad pool and the Don Takote sign are pre-rendered sprites. Both are set in
  PixelMplus12 at 12px, the ads by `tools/generate_ads.py` (#279), the sign by `tools/extract_city.py` (#346):
  no tool reads a system font.
