# Design: the ad pool redrawn in a GuttyKreum house look (#279)

Part 1 of 6 of #278. #280 to #284 apply the recipe and the module written here to the rest of the art.

## Context

`tools/generate_ads.py` draws the 44 ad boards in `assets/ads/` (12 square, 12 tall, 14 wide, 6 big, plus
`manifest.json`) that `RoomManager.placeSignage` hangs on Market's ten `signage` spots. They do not look like
the GuttyKreum art they hang on:

- one flat colour covers 75 to 80% of a board; a `#141017` 2px edge and a 1px keyline are the only shading;
- the text is the Mac's Hiragino, drawn large and thresholded, on the 64px grid: no other art in the game has
  pixels that fine (everything else is 32px art, pixel-doubled);
- the colours (`#c62828`, `#1155a8`, `#f9c22e` ...) are in no GuttyKreum sheet.

And the tool cannot be run except on a Mac: `find_font()` accepts only the Mac's fonts, so `check_generators.py`
lists it as `skip` everywhere else, Workshop's container included.

Outcome: a written recipe for the house look, measured from the sheets; one module of shared helpers; the
ad pool redrawn with them, by a tool that runs anywhere and is checked like every other art tool. Shapes,
file names, keys and `manifest.json` do not change, so `RoomManager` and Market's map are untouched.
No rooms are touched (art, tools, tests and docs only).

## Approach

**Draw the boards the way the sheets draw theirs.** The models are the sign boards in
`art-source/GuttyKreum/UrbanAccessoriesv2/Tilemap.png` (the ビール light box at (11,32) 21x32, the スナック board
at (33,81) 30x14, the 寿司 boxes) and Dotonbori's billboards (`GK_DB_B.png`). Each is: an ink outline with the
corner pixel left clear; a steel housing, lightest along the top; a one-row cast shadow under the top lip; a
face that is never one flat colour (alternating rows of two neighbouring tones on a lit box, a lighter rim row
and a darker lower part on a painted board); glyphs one pixel thick in a light tone. The new boards are
built from those parts at half size (32px per cell) and doubled with `Image.NEAREST`, as every other
generated sprite is.

**Set the text in the game's own Japanese pixel font**, `fonts/PixelMplus12-Grid.ttf` at 12px without
anti-aliasing, as `generate_station_art.py` already does (`kana()`, `d.fontmode = '1'`). At half size a
12px glyph is 24px in the game: pixel-true, the same density as the rest of the art, and the same on every
machine. All 164 characters of today's copy are in the font (checked). This is forced as well as better:
"`python3 tools/generate_ads.py` regenerates the pool" cannot be met in the container with a system font, and
installing one is ruled out (`check-generators.test.js`: any font but the Mac's draws other pixels).
Consequence, and a deliberate difference from the ticket's note: **`generate_ads` leaves `FONT_TOOLS`**, so
`check_generators.py` checks it instead of listing it as `skip`. `extract_city` (the Don Takote sign) stays
the one font tool, and keeps using `generate_ads.find_font`, `FONT_PATH`, `FONT_INDEX`, `text_bitmap`,
`fit_text` and `paste_center`, which therefore stay in `generate_ads.py` exactly as they are.

**12px glyphs hold less copy than scaled text did**, so a board has a fixed layout and budget, and seven
boards' copy is shortened (table below). Scaling glyphs up instead would mix pixel sizes, which the look
forbids.

**The shared module is a leaf**: `tools/house_look.py` imports only the standard library and Pillow. It
must not import `line_art` or a generator: `line_art` imports three generators for its palette, and #280 to
#284 will make generators import `house_look`, so anything else is an import cycle. It reuses by shape
instead: its materials are `line_art`'s `(base, hi, lo, line)` tuples, so `line_art.paint` takes them as
they are, and its `outline` is `generate_hokkaido.outline`'s rule. Existing generators and `line_art.py` are
not edited here; their own palette constants move over as each is redrawn in #280 to #284.

## Changes

### `gamev2/tools/house_look.py` (new)

Importing it has no side effects. No numpy; no Pillow polygon, ellipse, arc or line in the output path
(rectangles, pixel access and 1-bit text only), so every supported Pillow paints the same pixels.

- `rgb(hex)` -> `(r, g, b, 255)`; `INK = rgb('0a1627')`, `INK_DEEP = rgb('080d16')`.
- `RAMPS`: name -> tones, dark to light. Every tone is a colour of the sheets (verified; a test holds it):

  | ramp | tones |
  |---|---|
  | `red` | `8a3a22 aa4d31 d16b56 e78d7b ffe2e0` |
  | `orange` | `904a37 aa4d31 ce6a42 f6a583 ffe2e0` |
  | `gold` | `86624f a7843b c6a663 f3d890 fafcfd` |
  | `green` | `2e4040 395050 506b6b 6c8e7f 93c297` |
  | `blue` | `172459 314b8e 425faa 5a86de 7db9fa bbe9ff` |
  | `purple` | `2a233b 3c396d 444679 8f72b6 bfabd7 c9cbff` |
  | `pink` | `83374f bb6479 ff9b92 ffe2e0` |
  | `steel` | `2a2636 47485d 575f79 848295 a4b0b5 dae2e4` |
  | `cream` | `8e7366 be9e8c e4cecc fafcfd` |
  | `night` | `080d16 0a1627 191c2a 2c2d51 444679` |

- `material(ramp, i)` -> `(base, hi, lo, line)` = tones `i`, `i+1`, `i-1`, `i-2`, clamped to the ramp
  (`line_art`'s order). `palette()` -> the set of every tone, for tests.
- `canvas(w, h)` -> clear RGBA image. `double(im)` -> 2x `Image.NEAREST`.
- `outline(im, ink=INK)`: a 1px ink line on the clear pixels 4-adjacent to drawn ones (the rule of
  `generate_hokkaido.outline`).
- `bevel(im, box, material)`: `hi` on the box's top row and left column, `lo` on its bottom row and right
  column (`lo` wins the corners): light from the upper left.
- `scanlines(im, box, a, b)`: rows alternate `a`, `b` from the top.
- `shade(im, box, material, part=3)`: `base`; the top row `hi`; the lowest `1/part` of the rows `lo`, joined
  to the rest by exactly one checker-dithered row.
- `text(im, x, y, s, fill, shadow=None, vertical=False, pitch=12)` and `text_size(s, vertical=False,
  pitch=12)`: PixelMplus12 at 12px (`fonts/PixelMplus12-Grid.ttf`, relative to `gamev2/` as in
  `generate_station_art.py`), 1-bit, placed by its ink box. `shadow` is stamped first at (+1, +1).
  Vertical text stacks one glyph per `pitch` rows, centred on the column; ー is drawn upright (rotated, as the
  sheets' ビール and `generate_hokkaido`'s banner do) and small kana (ッャュョァィゥェォ) are moved 2px up and right.
- `pixmap(rows, colours)`: a hand-set picture, one character per pixel (`.` clear), as
  `generate_hokkaido.GLYPHS` is written.
- `sheet(paths_or_images, out, width=960, pad=8, scale=1, bg=(90, 96, 104))`: a contact sheet, images flowed
  left to right in the order given. Also the module's command line, for before/after sheets in this ticket
  and the next five: `python3 tools/house_look.py --sheet OUT.png [--scale N] PNG...`.

### `gamev2/tools/generate_ads.py` (rewritten below `SPECS`; `SPECS` order, shapes and counts unchanged)

A board, on the half-size canvas (`C = 32` per cell; square 32x32, tall 32x64, wide 64x32, big 64x64):

| rows / columns | what |
|---|---|
| outer row and column | `INK`, the four corner pixels clear |
| row 1, column 1, row h-2, column w-2 | steel housing: `dae2e4` lip, `a4b0b5` left, `47485d` bottom, `575f79` right |
| row 2 | the lip's cast shadow: the face's `line` tone (a lit face: the darker of its two row tones) |
| rows 3 to h-3, columns 2 to w-3 | the face: 28 or 60 wide, 27 or 59 high |
| the lowest 13 rows of the face, when there is a `sub` | the band: its top row the band's `hi`, the sub on its 12 rows |

`PALETTES` keeps its ten names (the specs and the `--claude` schema use them) and becomes parts. A `lit`
face is `scanlines` of two tones (a light box); a `painted` one is `shade` (a board):

| pal | face | title, its shadow | band, sub text |
|---|---|---|---|
| `aka` | painted `red` 2 | `fafcfd`, `8a3a22` | `gold` 2, `172459` |
| `shiro` | painted `cream` 2 | `aa4d31`, none | `red` 2, `fafcfd` |
| `kuro` | lit `night` `191c2a`/`0a1627` | `f3d890`, `080d16` | `red` 2, `fafcfd` |
| `ao` | lit `blue` `425faa`/`314b8e` | `fafcfd`, `172459` | `gold` 2, `172459` |
| `midori` | painted `green` 2 | `fafcfd`, `2e4040` | `cream` 2, `2e4040` |
| `kiiro` | painted `gold` 2 | `172459`, none | `red` 2, `fafcfd` |
| `murasaki` | lit `purple` `444679`/`3c396d` | `c9cbff`, `2a233b` | `orange` 2, `ffe2e0` |
| `orenji` | painted `orange` 2 | `fafcfd`, `904a37` | `night` 2, `f3d890` |
| `pinku` | painted `pink` 1 | `ffe2e0`, `83374f` | `cream` 2, `83374f` |
| `konai` | lit `night` `2c2d51`/`191c2a` | `7db9fa`, `0a1627` | `blue` 2, `bbe9ff` |

A title darker than its face has no shadow (it turns muddy). After looking at the contact sheet a tone may
move one step along its ramp; ramps and roles may not change.

Layout (advance: 12 per full-width glyph, 6 per half-width; a spec that does not fit raises, naming it):

| shape | title | motif | sub |
|---|---|---|---|
| square | 1 or 2 glyphs, one line | 10x10 at most: above the title; beside a 1-glyph title when there is a sub; dropped when a 2-glyph title has a sub | band, 24 at most |
| tall | 2 to 4 glyphs, vertical, at the largest pitch of 14, 13, 12 at which title, motif and band fit the face's 59 rows | above the title, 1 row clear of it | band, 24 at most, and only under 3 glyphs or fewer (4 at pitch 12 need 47 rows of the 46 left) |
| wide | 60 at most, one line | left of the title when title + 12 fits in 60, else dropped | band, 60 at most |
| big | 60 at most, on the 13 rows above the band | a picture panel, the face's top 33 rows: `scanlines` of the band ramp's two darkest tones, a `line` row under it, one hand-set picture (30x28 at most) centred | band, 60 at most |

- Motifs are `pixmap`s, redrawn by hand: the eleven small ones (`lantern bowl mug fish note flame star steam
  cross bolt coin`, 10x10 at most, the title colour plus at most two tones of the board's ramps) and six
  pictures for the bigs, `PICTURES`: `can` (ストロング), `lantern` (ノミカイ), `glass` (ウイスキー), `onsen`, the ♨
  mark (温泉旅館), `burst` (歳末セール), `reel` (映画祭). The six big specs name them in `motif`. A big whose
  motif has no picture (only from `--claude`) shows its small motif three times across the panel.
- Copy that changes, because it does not fit (everything else is kept, character for character):

  | ad | now | becomes |
  |---|---|---|
  | `tall-03` sub | 24h | none (カラオケ keeps its note; 歌 24h is still `square-07`) |
  | `wide-01` | ラーメン一番 | 麺屋一番 |
  | `wide-03` | のみほうだい | 飲み放題 |
  | `wide-04` sub | フリータイム | 歌い放題 |
  | `wide-06` | 純喫茶ローズ | 喫茶ローズ |
  | `wide-11` | ゲーセンUFO | ゲーセン |
  | `wide-14` | 歯科クリニック | 歯科医院 |

  Motifs dropped by the layout rule: `square-02` (fish) and the wides whose title is five glyphs
  (`wide-04`, `-05`, `-06`, `-10`). `tall-12` (ビール, ¥290, mug) fits with no row to spare.
- Removed: `render`'s frame, keyline and marquee bulbs, `draw_motif`, the `random` use and `--seed` (nothing
  passes it). `main()` no longer calls `find_font()`. Kept untouched for `extract_city.py`: `find_font`,
  `FONT_PATH`, `FONT_INDEX`, `text_bitmap`, `fit_text`, `paste_center`, under a comment saying who uses them.
- `--claude`: the system prompt states the new limits (tall 4; square 2; wide and big 5 full-width; sub 5
  full-width, half-width counting half); a returned spec that does not fit is skipped with a printed line.
- New `--sheet PNG`: after rendering, writes `house_look.sheet` of the pool in manifest order.
- The module docstring says what a board is made of and points at the recipe.

### `gamev2/assets/ads/*.png`

All 44 regenerated and committed. `manifest.json` must come out byte-identical (check with `git diff`).

### `gamev2/tools/check_generators.py`

`FONT_TOOLS = ['extract_city']`; the comment above it, the docstring's "The two that draw Japanese text" and
`have_jp_font`'s wording follow. `have_jp_font` still asks `generate_ads.find_font`.

### Docs and wording

- `gamev2/docs/generators-and-checks.md`: new section **"House look: GuttyKreum"** before "Asset Generation":
  the recipe under Data and interfaces, the `house_look.py` helpers, the board anatomy in three lines, and
  "compare a redraw against the sheets, on a contact sheet (`house_look.py --sheet`), not from memory".
  In "check_generators.py": only `extract_city` needs the system font; `generate_ads` is checked wherever
  Pillow is. In "Asset Generation": a paragraph for `generate_ads.py` (`--sheet`, the font, the budgets).
- `gamev2/CLAUDE.md` index row for `generators-and-checks.md`: add "House look: GuttyKreum
  (`house_look.py`)" to Covers and "drawing or redrawing generated art" to Read before.
- `gamev2/docs/fonts-and-japanese.md` (last bullet): the ad pool is pre-rendered in PixelMplus12 by
  `generate_ads.py`; only the Don Takote sign still uses a system font.
- `gamev2/docs/shop-and-economy.md` and `tools/generate_izakaya.py`'s `SIGNS` comment: のみほうだい -> 飲み放題.
- One-word fixes where "the two font tools" or "generate_ads and extract_city are skip" is said:
  `gamev2/tiled/README.md:279` (still true, check the wording), `.github/workflows/checks.yml` (comment),
  `.workshop/Dockerfile` (the comment and the LABEL text only; the LABEL stays the last line and keeps
  "Pillow 11.3.0"), root `CLAUDE.md` ("the two that need a Japanese system font" -> the one),
  `tools/tests/check-generators.test.js:199` (comment), `tools/test_blog_to_npc.py`
  `test_generator_check_skips` (docstring).

## Data and interfaces

No schema, API or config change. `manifest.json`, the texture keys (`ad-<shape>-<nn>`), image sizes and
`RoomManager.placeSignage` / `adFor` are unchanged. `generate_ads.py` loses `--seed` and gains `--sheet`.
`check_generators.FONT_TOOLS` shrinks to `['extract_city']`.

**The recipe** (the text of the new doc section; every number is measured from the 11 sheets):

- **Grid**: draw at half size, 32px per cell, and double. Never mix pixel sizes in one sprite.
- **Palette**: only colours of the sheets (516 between them; 55 to 189 per sheet), taken as ramps of 4 to 6
  tones from `house_look.RAMPS`. A shadow is not the base mixed with black: it moves in hue toward
  red-brown, indigo or navy (gold `c6a663` h41 -> `86624f` h21; green `6c8e7f` h154 -> `506b6b` h180; blue
  `5a86de` h220 -> `172459` h228), and a highlight toward cream, pink or cyan (red `d16b56` -> `ffe2e0`;
  blue -> `bbe9ff` h199). The darkest tones are `2a2636`, `2c2d51`, `0a1627`; pure black is not used.
- **Outline**: the silhouette is 1px of ink, `0a1627` (or `080d16`): 100% of UrbanAccessories' silhouette
  pixels, 81 to 90% of `GK_JC_B` and `GK_DB_B`'s (the rest, and half of `GK_DB_F`'s, is `2a2636`). Never
  black. Lines inside the silhouette take the darkest tone of the family they cross (`8a3a22` in red,
  `172459` in blue, `2c2d51` in glass, browns in wood), ink only between two families. This is `line_art`'s
  rule 6.
- **Light**: from the upper left. Top and left edges take the `hi` tone, bottom and right the `lo`; a lip
  casts one row of shadow on what is under it.
- **Colours per sprite**: 8 to 16 for a sprite of one or two cells (the sheets' signs use 10 to 12), up to
  24 for a larger one (the sheets' objects: median 17, quartiles 12 and 25). Two or three ramps and ink.
- **Flat areas**: a face is never one colour from edge to edge, and no colour covers half a sprite. Either
  texture it with alternating rows of two neighbouring tones (scanlines, courses, planks), or shade it: a
  lighter row along the lit edge and a darker part on the far side, joined by a single dithered row. Dither
  is an edge, never a gradient (at most 1.6% of a sheet's 2x2 blocks are checkered).
- **Text**: PixelMplus12 at 12px, 1-bit, one pixel thick, lighter than its ground with a (+1, +1) shadow in
  the ground's `line` tone, or darker with none.

## Tests

New `gamev2/tools/tests/house-look.test.js` (pure Node with `tools/png.js`, except the last, which returns
early without Pillow as `check-generators.test.js` does):

1. The pool is what it was: `manifest.json` lists 12 square, 12 tall, 14 wide, 6 big, keys `ad-<shape>-<nn>`
   in order, and every PNG is `w*64` x `h*64`.
2. Every ad is pixel-doubled (each 2x2 block one colour) and its four corner blocks are clear.
3. Every opaque pixel on the picture's edge or 4-adjacent to a clear one is `0a1627`.
4. Every ad has 8 to 16 colours (a big: up to 24), and no colour covers more than half its opaque pixels.
5. Every colour of every ad is an opaque colour of a sheet under `../art-source/GuttyKreum` (previews left out).
6. `house_look`: every `palette()` tone is in a sheet; `material('red', 2)` is `line_art`'s order; `shade`
   has exactly one dithered row; `text` draws ー upright when vertical; `python3 tools/generate_ads.py --out
   <tmp>` twice gives the committed pixels.

Changed: `izakaya.test.js` expects `nth('wide', 3) === '飲み放題'`; `test_generator_check_skips` also asserts
`'generate_ads' not in cg.FONT_TOOLS`.

Run from `gamev2/`: `node tools/test_game.js`; `python3 tools/test_blog_to_npc.py`; `node tools/play.js
check`; `python3 tools/check_generators.py` (expect `generate_ads` ok, `extract_city` still `skip`: say so in
the summary); `python3 tools/sync_cities.py --check`. Then the browser regression (`tools/browser/README.md`;
`REGRESS_TIME_SCALE=2 PORT=8000` in the container).

By eye, with Read, saved to `/work/media/`:

- Contact sheets: `python3 tools/house_look.py --sheet /work/media/279-ads-before.png assets/ads/*.png`
  before regenerating, `--sheet` again after. Put a crop of the sheets' own signs beside them while working,
  outside the repository and outside `/work/media/` (the packs may not be redistributed).
- In the game, Market by day and by night, desktop and a phone size: `?notitle=1&nointro=1&stitch=0&tod=day`,
  then `game.scene.keys.GameScene.roomManager.switchRoom('Market', 9, 39)` (the Izakaya's two pinned boards;
  `(41, 38)` for the east row); `roomManager.signArt` names the ads on screen. Reload until each shape is seen.

## Risks and open questions

- **`generate_ads` becomes a checked tool**, which the ticket did not expect ("listed as `skip`"). It is the
  only way the tool can run in the container, and it is what the other art tools already are. The summary
  must say so.
- **Smaller text.** Glyphs are 24px in the game where 居酒屋 was about 48px. That is the sheets' scale (their
  glyphs are smaller still), but the boards read as quieter. If the owner wants louder boards the fix is
  bolder faces and pictures, not scaled glyphs.
- **Seven boards change their words** (table above), `wide-03` among them: the Izakaya's pinned sign reads 飲み放題.
- **The six big pictures and eleven motifs are hand-set pixels**: the bulk of the work and the part most
  likely to need a second pass. Judge them on the contact sheet at 1x and in the game, not zoomed in.
- **16 colours is tight** for a board with a band and a motif; motifs take their tones from the board.
- **The budgets are computed, not yet drawn** (a rough prototype of squares, talls and wides exists as
  `279-design-mock.png` on the ticket; the bigs' panels are untried). Where a board looks cramped on the
  contact sheet, drop its motif before changing the layout rules.
- **`extract_city.py`'s Don Takote sign** still uses the old text helpers and the Mac's font, so it stays
  `skip` and outside the look. It cannot be run or verified in the container; do not touch it here.
- **Text rendering across Pillow releases**: 1-bit PixelMplus12 already reproduces on Pillow 11.2 to 13.0 for
  `generate_station_art.py`; `check_generators.py` in CI (pinned 11.3.0) is the guard.
- **`.workshop/Dockerfile`** changes in comment and LABEL text only; if editing the agent image from a ticket
  is unwelcome, leave it and report the stale sentence instead.
