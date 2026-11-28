# Palace interior sprites in the house look (#341)

## Context

The audience hall's 32 sprites (`palace-in-*`, `gamev2/tools/generate_palace_art.py`, room `PalaceHallTokyo1`)
agree with each other but not with the GuttyKreum pack the rest of the game is drawn in. Measured on the
committed sprites: 171 colours, none of them a colour of the pack's sheets; the outline is `262b44`; cast
shadows are black; `mix()` makes ramps of in-between colours; and the lamps, the shoji, the doorways and the
daylight on the floor are lit yellow (`GLOW (255,222,150)`, `GLOW_HI (255,246,208)` and four yellow literals).

Wanted: the same shapes in the pack's colours, the pack's navy outline, no lit yellow, lamps in the dim gold
`c6a663`. Keys, sizes, anchors and `depthBias` do not change, so no map, config or `Glows.js` change.

This is the temple hall's change (#326, merged on `master`) done to the palace's tool, and it follows that
design. The tool keeps its own palette; `tools/house_look.py` (#279) is not needed, and is not on this branch
(the branch is 28 commits behind `master`; nothing there touches the files below).

## Approach

1. **Re-point the palette block** to pack hexes under the same names (plus a few new names for the literals).
2. **Replace every inline colour and every `mix()`** with a named pack colour; `mix()` is deleted, so no
   in-between colour can come back. Ramps become two or three flat bands.
3. **Lit yellow goes.** A lamp's paper is `c6a663` with `a7843b` top and bottom rows and a small `f3d890`
   core; paper with the day behind it is neutral (`e4cecc` / `ffe2e0` / `fafcfd`); daylight on the floor is
   `e4cecc` at the alphas it has now. The night glow stays where it is, in `Glows.js`, untouched.
4. **A test holds it**: every pixel of every `palace-in-*` sprite is a sheet colour, and nothing is brighter
   yellow than the lamp core. No `settle()` backstop as in the temple tool: with `mix()` gone the tool cannot
   make an off-pack colour (prototype: 0 off-pack pixels), and the test catches a new literal.

Outline: `1f1f3b`, the temple sheets' outline navy and what the merged temple hall uses (the old `262b44` is
nearest to it). `0a1627`, the recipe's other navy, was tried: heavier on the lattices and the lacquer; it is a
one-constant change if the owner prefers it.

This exact change was prototyped outside the repo: 53 colours over the 32 sprites (dais and mural 24 each,
the largest), every one in the sheets, silhouettes (alpha) identical, `config.json` byte-identical,
`check_generators.py` clean (the world map is not stale). Captures are with the ticket (before / prototype:
sprite sheet, room render, night in the browser).

## Changes

### `gamev2/tools/generate_palace_art.py`

Replace the palette block (lines 50-71, `INK = …` to `BRONZE… = …`) with:

```python
def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; palace.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy
VOID = rgb('080d16')
SHADE = rgb('080d16')                    # cast shadows, with alpha
DAY = rgb('e4cecc')                      # daylight lying on the floor, with alpha
WHITE, PAPER, PAPER_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('bcc7cc')
SHOJI, SHOJI_SH = rgb('ffe2e0'), rgb('d7b6ab')                               # paper screens with the day behind them
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')         # a lamp's paper; its small core
LQ, LQ_HI, LQ_DK = rgb('2a2636'), rgb('524b59'), rgb('171831')               # black lacquer
RED, RED_MID, RED_HI, RED_DK = rgb('aa4d31'), rgb('c66347'), rgb('d16b56'), rgb('8a3a22')   # vermilion lacquer
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')         # gilt fittings
LEAF_A, LEAF_B, LEAF_C = rgb('c6aa71'), rgb('c6a663'), rgb('b2a168')         # squares of gold leaf
CLOUD, CLOUD_HI = rgb('e3c587'), rgb('e4cecc')                               # gold mist, lit on top
PINE, PINE_HI, PINE_DK = rgb('506b6b'), rgb('83af6f'), rgb('2e4040')
BARK, BARK_HI, BARK_DK = rgb('7f513b'), rgb('aa775f'), rgb('4d3326')
TATAMI, TATAMI_MID, TATAMI_HI, TATAMI_DK = rgb('b2ad73'), rgb('b2a168'), rgb('b0c276'), rgb('928372')
HERI, HERI_HI = rgb('2e4040'), rgb('506b6b')
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = rgb('7f513b'), rgb('85553e'), rgb('aa775f'), rgb('5a3827')
PLASTER, PLASTER_SH, PLASTER_DK = rgb('e4cecc'), rgb('d7b6ab'), rgb('c69f96')
PURPLE, PURPLE_HI, PURPLE_DK = rgb('5c527d'), rgb('8f72b6'), rgb('3f3651')
INDIGO, INDIGO_HI, INDIGO_DK = rgb('314b8e'), rgb('588cc6'), rgb('172459')
WATER, WATER_HI = rgb('4b6396'), rgb('7db9fa')
STEEL, STEEL_HI, STEEL_DK = rgb('a4b0b5'), rgb('dae2e4'), rgb('575f79')
BAMBOO, BAMBOO_HI, BAMBOO_DK = rgb('678e57'), rgb('83af6f'), rgb('395050')
TIGER, TIGER_HI, TIGER_DK = rgb('ce6a42'), rgb('f6a583'), rgb('904a37')
MAPLE, MAPLE_HI = rgb('d16b56'), rgb('e78d7b')
BRONZE, BRONZE_HI, BRONZE_DK = rgb('826f60'), rgb('a68777'), rgb('594b45')
EARTH, MOSS = rgb('a7843b'), rgb('678e57')
CELADON, CELADON_HI = rgb('a0bbc2'), rgb('dae2e4')
PEONY = rgb('e78d7b')
COFFER_A, COFFER_B = rgb('4b6396'), rgb('83374f')                            # the ceiling's painted panels
```

`GLOW` and `GLOW_HI` are gone. Delete `mix()`. Then, by function (line numbers are today's; coordinates do
not change, only fills, except where rows are named):

| Where | Now | Becomes |
|---|---|---|
| `shadow` 140 | `(0, 0, 0, a)` | `SHADE + (a,)` |
| `wall_side` 256, 260 | `GLOW_HI`; `mix(GLOW_HI, BOARD, 0.45)` | `SHOJI`; `SHOJI_SH` |
| `sun` 281 | `(255, 232, 160, a)` | `DAY + (a,)` |
| `threshold` 302-304 | `GLOW_HI` fill, then a `mix()` line per row | fill `[0,0,31,31]` `WHITE`; `[0,0,31,2]` `PAPER`; a `SHOJI` line on rows 3-11, 13, 15, 18 |
| `doorlight` 325 | `(255, 236, 176, a)` | `DAY + (a,)` |
| `_wall_head` 336-337 | `(60, 84, 110)`, `(112, 60, 62)` | `COFFER_A`, `COFFER_B` |
| `wall_shoji` 367-370 | `GLOW_HI` fill, `mix()` rows 24-71 | fill `[1,23,30,87]` `PAPER`; `[2,32,29,62]` `SHOJI`; `[2,40,29,54]` `WHITE` |
| `alcove_shelves` 410, 411 | `(196, 180, 150)`, `(168, 152, 130)` | `PLASTER_SH`, `PLASTER_DK` |
| `alcove_shelves` 425-427 | `(150, 196, 176)` twice, `(204, 232, 214)` | `CELADON`, `CELADON_HI` |
| peonies 474, the sweet 1120 | `(236, 150, 150)` | `PEONY` |
| `mural` 568, 569; tiger screen 790 | `(150, 128, 78)`, `(120, 132, 80)` | `EARTH`, `MOSS`; `EARTH` |
| `mural` 592, 594 | `(74, 110, 150)`, `(150, 184, 212)` | `WATER`, `WATER_HI` |
| `mural` reeds 596, 597 | `BAMBOO_DK`, `(196, 170, 110)` | `PINE_DK`, `BARK_HI` |
| `_candle` 614-616 | `(255, 190, 80)`, `(255, 240, 180)`, `WHITE` | `LAMP`, `LAMP_SH`, `LAMP_HI` |
| `_brazier` 623, 625, 627-628 | `(206, 200, 190)`, `(240, 110, 60)`, tongs `STEEL_DK` | `PAPER_SH`, `RED_HI`, `LQ_HI` |
| `dais` 639 | `mix(TATAMI_HI, TATAMI, 0.6)` | `TATAMI` |
| `dais` 640-641 | `mix(TATAMI_DK, TATAMI_HI, y / 6)` on rows 0-5 | rows 0-1 `TATAMI_DK`, 2-3 `TATAMI_MID`, 4-5 `TATAMI` |
| `dais` 659, 660 | `(0, 0, 0, 90)`, `(0, 0, 0, 40)` | `SHADE + (90,)`, `SHADE + (40,)` |
| `dais` 669; papers on the desks 710 | `(214, 206, 150)`; `PAPER` | `TATAMI_MID`; `WHITE` |
| `pillar` 721 | `mix(RED, RED_HI, 0.5)` | `RED_MID` |
| moon 822 | `(244, 240, 222)` | `PAPER` (outline stays `CLOUD`) |
| `armour` mask 882 | `(70, 44, 44)` | `BARK_DK` |
| `swords` 917, 920 | sheaths `LQ`, `(120, 44, 50)`, `(40, 60, 110)`; shine `mix(sheath, WHITE, 0.35)` | loop over `(y, x0, x1, sheath, shine)`: `LQ`/`LQ_HI`, `RED_DK`/`RED`, `INDIGO`/`INDIGO_HI` (`i` and `enumerate` go) |
| `andon` 940-944 | `GLOW_HI` box, `mix()` rows, white flame ellipse | `box(d, 7, 14, 24, 45, LAMP)`; `[8,15,23,18]` and `[8,41,23,44]` `LAMP_SH`; `[14,27,17,33]` `LAMP_HI` |
| `lamp_hang` 969-976 | `GLOW_HI` box, `mix()` rows, bars `GOLD_DK` | `box(d, 8, 23, 23, 42, LAMP)`; `[9,24,22,26]` and `[9,39,22,41]` `LAMP_SH`; `[13,30,18,35]` `LAMP_HI`; the cage bars `BARK_DK` (they vanish on the dim gold otherwise) |
| `guardpost` 1023-1026 | `GLOW_HI` box, `mix()` rows | `box(d, 74, 18, 90, 44, LAMP)`; `[75,19,89,22]` and `[75,40,89,43]` `LAMP_SH` (no core: the `番` stays `RED_DK`) |

Afterwards `GLOW`, `mix(` and `fill=(<digits>` must not appear before `main()` (the preview background at
1178 is not a sprite and stays). Docstring: after "1px ink outline" say the colours are the GuttyKreum
sheets' and the lamps are dim, the glow being `Glows.js`'s. `sprites()`, `DEPTH_BIAS` and `main()` are untouched.

### `gamev2/assets/sprites/palace-in-*_0_0.png` (32 files)

Regenerated: `python3 tools/generate_palace_art.py` from `gamev2/`. `git status` must show the tool and these
32 PNGs only; `config.json` must come out unchanged (if it does not, a size or anchor moved: stop and fix).

### `gamev2/tools/tests/palace.test.js`

Add `test('the audience hall is drawn in the GuttyKreum pack\'s colours, with dim lamps (#341)', …)`, the
temple's #326 test (`tools/tests/temple.test.js` on `master`) with the palace's names:

- `pack` = the RGB of every fully opaque pixel of every PNG under `art-source/GuttyKreum` (walk the folders,
  `tools/png.js` `decode`), minus `000000` and `ffffff`.
- `keys` = `spriteMetadata` keys starting `palace-in-`; exactly 32.
- For each sprite's PNG, every pixel with alpha > 0: its RGB is in `pack`; if `r >= 0xf3 && g >= 0xd0 &&
  b < 0xc8` it is `f3d890`; `f3d890` is at most 8% of the sprite's non-clear pixels.
- `palace-in-andon_0_0`, `palace-in-lamp-hang_0_0`, `palace-in-guardpost_0_0` have more `c6a663` than `f3d890`.
- `1f1f3b` appears in at least 20 sprites (prototype: 22; the floors and the light overlays have no outline).

### `gamev2/docs/landmarks-and-towns.md`

The **Art** bullet of "The palace's audience hall (issue #215)" (line 1277): add that every colour is one of
the GuttyKreum sheets' (the tool's palette block; `palace.test.js` checks it), the outline is the navy
`1f1f3b`, lamps and candles are the dim gold `c6a663` with a small `f3d890` core, and the night glow is
`Glows.js`'s alone.

## Data and interfaces

None. No sprite key, size, anchor, `depthBias`, `tilePalette` entry, room, Tiled map, world map or `Glows.js`
row changes. Only `PalaceHallTokyo1` looks different; no room's map data is touched.

## Tests

From `gamev2/`:

- `python3 tools/generate_palace_art.py --preview /work/media/341-sprites-after.png` and
  `node tools/play.js render PalaceHallTokyo1 /work/media/341-hall-after.png`; look at both beside the
  "before" captures on the ticket.
- The five checks: `node tools/test_game.js` (the new test), `python3 tools/test_blog_to_npc.py`,
  `node tools/play.js check`, `python3 tools/check_generators.py` (no DRIFT: the tool rebuilds what is
  committed), `python3 tools/sync_cities.py --check`.
- Browser regression: `tools/browser/regress.js` (`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in the
  container).
- Play it: enter the hall by a tower door of the palace (Tokyo), desktop and a landscape phone, by day and
  with `?tod=night`. At night the lamps, the dais candles and the guard's lamp glow (`Glows.js`) over dim
  panes, and no shoji, doorway or patch of floor reads as a lit window. Save the screenshots to `/work/media/`.

## Risks and open questions

- **Daylight pieces at night.** `sun-*`, `doorlight`, the thresholds and the shoji are daylight and are drawn
  the same at night, as today. In the prototype they are neutral paper under the night tint and do not read
  as lit; hiding them at night would be a game change and is not in this ticket.
- **Which navy**: `1f1f3b` (chosen, as the temple hall) or `0a1627`: `INK` and the test's last assertion.
- **Hues shift**: vermilion is the pack's `aa4d31` (browner than today's red; the brighter `d16b56` base was
  tried and reads salmon), the dais mats are the pack's `b0c276` (greener), plaster and shoji are the pack's
  pinkish creams. These are the nearest sheet colours; the owner sees them in the captures.
- **Ticket says "about 34 keys"**: the tool draws 32, all interior. It has no outdoor sprite, so #338 has
  nothing to change in this file and the two cannot collide.
- `2b373c`, `9bb870` and `a3b867` are in no sheet (#378 covers the first): do not use them if a colour is adjusted.
- Pillow 11.2-13.0 draw the same pixels (`docs/generators-and-checks.md`); no shape changes, so no new curve
  to drift.
