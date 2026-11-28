# Design: the Japanese home kit and the tower lobby in the house look (#330, part 4 of #295)

## Context

`gamev2/tools/generate_house_art.py` draws 45 sprites: 34 `home-*` (the furniture of a Japanese home, #208)
and 11 `lobby-*` (a tower's lobby, #216). They are placed in 67 rooms: every `House*` and `Lobby*` room, the
ten Devhouse floors, and `lobby-mat` in eleven `Shop*` rooms. They are coherent with each other but not with
the pack: of the 92 colours they use, 73 are not colours of the GuttyKreum sheets; standing pieces are edged
in `0a1627`, not the navy the redrawn towns use; and the lamp, the stove, the hearth, the lift, the directory
and the windows are drawn lit (`f2c66a`, `fbe6a4`, `f9c22e`, `f0943a`, `e8623a`, sky-blue glass).

Wanted (the ticket, and the recipe in `gamev2/docs/generators-and-checks.md`, "House look: GuttyKreum"):
every colour a sheet colour, the outline in navy `172459`, no lit yellow, shading on the outdoor-facing pieces,
and **nothing else moved**: the same 45 keys, sizes, anchors and shapes, the same names for the four tools
that import this file, pack art from `extract_house_interior.py` (`home-wood-floor`, `home-plant`) untouched.

The constraint that shapes the design: `generate_devhouse_art.py` imports 26 colour constants and four
helpers (`box`, `speckle`, `wall_frame`, `plaster`) from this file and draws its 37 sprites with them. Those
sprites belong to #319 and #325. If a constant's value or a helper's pixels change here, they all drift.

## Approach

**Repaint at save, plus a few builder edits.** The constants keep their names *and their values*, and the
four shared helpers keep their bodies, so `generate_devhouse_art.py` rebuilds exactly as it is. This file
gains one table, `SWAP` (old colour to sheet colour), and `main()` runs
`generate_sendai_art.repaint(im, SWAP)` on each of its own sprites before doubling it: the
`generate_fukuoka_art.PACK_SWAP` pattern. Builders are edited only where a swap cannot do the job: the
outline, the window glass and the lamp.

The other way, changing the constants where they are defined, is shorter but recolours the Devhouse art in
this ticket and collides with #319 / #325 on 37 binary PNGs. Rejected.

Helpers: `house_look.py` (#279) is on master but has no `repaint` or `pane`, so those two come from
`generate_sendai_art.py` as the ticket says (importing it has no side effects). `foliage`, `roof_tile`,
`glaze` and `flat_roof` are not needed: there is no roof, and the palm keeps its shape and its pack greens.

This was prototyped in a scratch copy with exactly the changes below (pictures on the ticket). Result: all
45 sprites keep their size and their alpha mask pixel for pixel; `config.json` is byte-identical; the other
1593 sprites, the 37 Devhouse ones included, are pixel-identical; every colour is a sheet colour;
`home-doormat_0_0` does not change at all (it is already pack colours and has no outline), so this ticket
and #300 do not touch the same PNG whichever lands first.

## Changes

### `gamev2/tools/generate_house_art.py`

1. **Imports**: add `NAVY` to the `generate_hokkaido` import; add `from generate_sendai_art import repaint, pane`.
2. **Do not change** the value of any module constant (`WOOD_HI` … `ORANGE`, `MARBLE`, `PANEL*`, `SLATE*`),
   the bodies of `box`, `speckle`, `wall_frame`, `plaster`, the `SPRITES` keys and labels, or what `main()`
   writes to `config.json`. Add a comment above the constants: they are also `generate_devhouse_art.py`'s,
   and this file's sprites reach the pack through `SWAP`.
3. **`SWAP`**, above `SPRITES`, with `LAMP, LAMP_HI, LAMP_LO = GOLD, rgb('f3d890'), rgb('a7843b')`:

   ```python
   SWAP = {rgb(a): rgb(b) for a, b in (pair.split('>') for pair in """
       d7a98c>ebbca2 c99a80>c18e75 a87861>aa775f e6bfa3>ebbca2
       5e4a42>594b45 7c6455>7c5d56 3d302e>493938
       f7f1e3>fafcfd e6dcc6>e4cecc cbbfa6>d2bab0
       c3c98c>b0c276 b2ba7d>b2ad73 98a26b>83af6f dccb8e>e3c587 cdb97c>c6aa71 b39d66>b2a168
       2f4a44>2e4040 46695c>506b6b 6f7a52>718a45
       e7d8b9>e4cecc d6c4a0>d2bab0 bfab86>be9e8c c3cbab>bec2c1 aeb894>97acaa 95a07c>6c8e7f
       3c4f86>314b8e 6480bd>425faa 26335c>232449
       d98f96>ff9b92 efb9b7>ffe2e0 b4686f>bb6479
       7fa6d6>5a86de a9c8ec>7db9fa 5c80b4>425faa
       b9c4cf>bcc7cc e2e9ef>dae2e4 7f8ea0>848295 e4ebf2>dae2e4 d9dfe5>dae2e4 a9b2bb>a4b0b5 9099a6>919ea4
       aab6c2>a4b0b5 cfe2ee>d1e2eb
       2c2d3a>2a2636 4b4f63>47485d a9a59c>b3aaa0 8a857d>8d8883
       e6e3dc>dae2e4 d5d1c8>bcc7cc f4f2ee>fafcfd c9c6c1>bcc7cc b8b4ae>a4b0b5 dad7d2>dae2e4
       d9d4c7>e4cecc bdb6a6>d2bab0 ece8de>fafcfd 3f4658>47485d 5c6680>575f79 2a2f3e>2a2636
       eeeae2>dae2e4 a89674>a68777 7f6f58>826f60 8f7f64>8e7366 9c8a6a>967f79
       7c8088>848295 5a5e68>575f79 7a9a55>83af6f e2c98a>f3d890
       f2c66a>e78d7b e8623a>aa4d31 f0943a>ce6a42 f9c22e>c6a663
   """.split())}
   ```

   Rows, in order: wood; beam; paper; rush (green, gold); tatami border and mat end; plaster (sand, moss);
   indigo; rose; sky; steel and stone; lift lines and table glass; iron and ash; marble (a, b); lobby panel
   and slate; desk top and the alcove; the scroll's mountain, tea, brass; ember, mantle, mikan, indicator.
   Targets are the `house_look.RAMPS` tone where one is near (blue, pink, steel, cream, green, gold, orange),
   else the nearest well-used sheet colour. The 19 colours already in the sheets are not in the table.
4. **`main()`**: `repaint(im, SWAP)` between `im = fn()` and the resize.
5. **Outline**: every `outline(im)` becomes `outline(im, NAVY)` (19 calls, 25 sprites). The 20 flat or
   tiling pieces that have no outline today still have none: the four tatami, `genkan`, `agari`, the six
   `home-wall-*`, `tokonoma`, `doormat`, `lobby-floor_a/_b`, `lobby-mat`, `lobby-wall`, `lobby-lift`,
   `lobby-directory`.
6. **`wall_window`**: replace the `SKY_HI` rectangle, the `SKY` loop and the two `WHITE` glints with
   `pane(d, 5, 24, 26, 46)` (the pack's dark glass, slanted glare, shaded head). Frame, mullion, transom and
   sill lines stay after it, unchanged.
7. **`shoji`**: the two bands of daylight are joined by one dithered row. In the leaf loop, after the
   `PAPER_LO` rows and before the lattice: `for x in range(x0 + (46 + x0) % 2, x0 + 14, 2): d.point((x, 46), fill=PAPER_LO)`.
8. **`andon`**: unlit paper. `LIT_HI` → `LAMP`, `LIT` → `LAMP_LO`, then one glint
   `d.rectangle([10, 6, 14, 6], fill=LAMP_HI)` before the frame lines.
9. **`bookshelf`**: `spines = (RED, INDIGO, GREEN_HI, GOLD, CREAM, SKY, ROSE, GREEN, RED_LO)` (drops
   `INDIGO_HI`, `AMBER`, `STONE`): 16 colours instead of 18, the recipe's limit for a 1x2 sprite.
10. **Docstring**: say the sprites are in the house look (sheet colours through `SWAP`, navy outline, no lit
    yellow), "a window in that plaster" instead of "a frosted window", and that the constants and four helpers
    are shared with `generate_devhouse_art.py`.

No other builder changes. What the swap alone does to the other lit pieces: the hearth's charcoal and the
stove's mantle are pack reds (`aa4d31`, `e78d7b`, `ce6a42`); the lift's indicator and call button, the
directory's floor marks, the rice cooker's light and the television's sun are dim gold `c6a663`; the mikan
are `ce6a42`. The television keeps its weather map and the desk its screen, in the pack's blues.

### `gamev2/assets/sprites/`

Rerun `python3 tools/generate_house_art.py` from `gamev2/`: 44 PNGs change (`home-doormat_0_0.png` must not).
If #300 has landed first and redrew the doormat, leave its builder alone. `config.json` must come out
byte-identical (`git diff --stat` shows PNGs only); no `tiled/`, room, palette or world-map change.

### `gamev2/tools/tests/house-art.test.js` (new)

See Tests.

### `gamev2/docs/landmarks-and-towns.md`

- House interiors, **Art** bullet (line ~999): "in the `generate_hokkaido.py` style (… GuttyKreum palette,
  1px ink outline …)" becomes the house look: drawn with the file's own colours and repainted to sheet
  colours by `SWAP` as each is saved, 1px navy outline on what stands, dark pack glass in the windows,
  no lit yellow; the constants and `box` / `speckle` / `wall_frame` / `plaster` are shared with
  `generate_devhouse_art.py`, so change a colour in `SWAP`, not in the constant.
- Tower lobbies, **Art** bullet (line ~1105): "in the same style" stays true; leave it.

## Data and interfaces

None. Same 45 keys, PNG sizes, `spriteMetadata` (`frameCount`, `anchorX`, `anchorY` only, no glow), and
`tileNames`. New module names `SWAP`, `LAMP`, `LAMP_HI`, `LAMP_LO`; every existing name keeps its value, so
`generate_houses.py`, `generate_devhouses.py`, `extract_house_interior.py` and `generate_devhouse_art.py`
need no edit. Door cells, collision and seats are untouched (no map data changes).

## Tests

New `gamev2/tools/tests/house-art.test.js`, in the manner of `house-look.test.js` (decode with `tools/png`;
the sheet colours by walking `art-source/GuttyKreum`, skipping `preview*`). The 45 keys and their cell sizes
are written out in the test.

1. Each key's PNG is `cells × 64` px, pixel-doubled (every 2x2 block one colour), with no half-transparent
   pixel; its `spriteMetadata` is exactly `{frameCount: 1, anchorX: 32/w, anchorY: 32/h}` and its
   `tileNames` label is unchanged.
2. Every opaque colour of the 45 is a sheet colour.
3. None of them holds `f2c66a`, `fbe6a4`, `f9c22e`, `f0943a` or `e8623a` (the lit colours; implied by 2,
   named for the message).
4. For the 25 outlined keys (all but the 20 listed in Changes 5), every opaque pixel with a clear
   4-neighbour is `172459`.
5. `home-wall-window-sand` and `-moss` hold `2c2d51` and `4b6396` (pack glass and glare).
6. Source check: `generate_house_art.py` still defines every name on `generate_devhouse_art.py`'s
   `from generate_house_art import (...)` line (parse the import with a regex, look for `NAME` followed by
   `=` or `def NAME`).

Run, from `gamev2/`:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # generate_house_art ok, generate_devhouse_art ok, no DRIFT
python3 tools/sync_cities.py --check
```

and the browser regression (`tools/browser/README.md`), since players see this.

By eye, before and after (`node tools/play.js render <Room> out.png`, and
`python3 tools/generate_house_art.py --preview out.png`): `HouseAsahikawa2`, `HouseKanazawa1`,
`LobbyFukuoka1`, `DevhouseTokyo4F`, `DevhouseOsaka2F`; between them they place every sprite but two
(`home-irori` is in `HouseAsahikawa1`, `home-kotatsu-indigo` in `HouseMarket3`). In a browser, a house and a lobby on desktop and at a
phone size, by day and with `?tod=night`: interiors are not graded and no `home-*` / `lobby-*` sprite has
glow metadata, so night must look the same as day and no window may be lit.

The summary must name the sprites that still read flat. Measure: one colour on more than half the opaque
pixels. In the prototype: `home-agari` (0.73), `home-wall-sand` / `-moss` (0.69), `home-fridge` (0.63),
`home-table` (0.51), the three `home-zabuton` (0.64), `lobby-floor_a` / `_b` (0.82), `lobby-wall` (0.62),
`lobby-sofa-back` (0.76). They are left so on purpose: the ticket asks for shading on the outdoor-facing
pieces only.

Commit as `gamev2: … (#295)`, as the ticket says.

## Risks and open questions

- **Devhouse floors are half redrawn until #325.** `home-wall-sand` and `home-wall-window-sand` turn from
  yellow cream to the pack's pink cream `e4cecc`, while the Devhouse's own wall pieces, drawn by
  `generate_devhouse_art.py` with `plaster('sand')`, stay yellow: a visible join on all ten Devhouse floors
  (picture on the ticket). #325 closes it by running the same `SWAP` over its sprites. Say so in the summary.
- **Hue shifts the sheets force.** They have no pale yellow cream, pale moss or warm marble. Sand plaster and
  the lobby panelling become `e4cecc`, moss becomes grey-green `bec2c1` / `97acaa`, the lobby floor becomes
  cool grey `dae2e4` / `bcc7cc`. If a render shows one of these wrong, change that entry in `SWAP` to another
  sheet colour (test 2 holds it); do not touch the constant.
- **"Outdoor-facing pieces"** is read as the two windows and the shoji. The mats and the palm already carry
  their own bands and are pack colours.
- **Windows are dark by day**, as Sendai's are (`pane`) and Flinders' will be (#309). The screens are not
  switched off: the television's bump line is "the weather: snow in the north, and more tomorrow"
  (`Interactions.js`), so it keeps showing it.
- **The hearth and the stove still glow**, in pack reds rather than yellow. Read "no lit yellow" literally;
  dimmer would be `8a3a22` / `aa4d31`.
- **Old Pillow primitives stay** (`ellipse`, `rounded_rectangle`, `polygon`, `arc`, slanted `line`): redrawing
  them as rectangles would change shapes the ticket keeps. They reproduce on the pinned Pillow 11.3 today.
  New drawing here is rectangles and points only (`pane`, `repaint`).
- **`SWAP` is by exact colour**: a builder later given a colour outside the sheets fails test 2, by design.
- **Map data**: none touched. Rooms whose look changes: every `House*` and `Lobby*`, the Devhouse floors, and
  the `Shop*` rooms of Asahikawa, Sapporo and Karuizawa (`lobby-mat` only).
