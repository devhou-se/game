# 313: the Don Takote signage and the konbini drinks cooler in the house look

Part 1 of 7 of #295. Commit the implementation as `gamev2: ... (#295)`.

## Context

Six generated sprites are still in their first palette: flat fills, black outlines, a lit yellow, a lit
cyan cooler.

| Sprite | Size | Tool | Placed in |
|---|---|---|---|
| `don-takote-sign_0_0` | 5x2 | `tools/generate_discount_art.py` | `DonTakoteOsaka`, `DonTakoteMarket`, `DonTakoteSapporo` (1 each) |
| `don-takote-wall-top_0_0`, `don-takote-wall_0_0` | 1x1 | same | the same three rooms (19 each) |
| `don-takote-pop-yen_0_0`, `don-takote-pop-sale_0_0` | 1x1 | same | the same three rooms (2 each) |
| `office-fridge_0_0` | 1x2 | `tools/generate_cooler_art.py` | the 14 `Konbini*` rooms (3 or 4 each) |

They are redrawn in place in the house look (worked examples: `generate_seven_eleven_art.py`, `pub` in
`generate_sendai_art.py`). Keys, sizes, anchors, `depthBias` and `tileNames` do not change, so
`config.json`, the maps, the prefabs and the room generators are untouched. #279 has not merged, so the
helpers come from `generate_sendai_art.py`.

A prototype of this design was drawn and rendered in the rooms. Look at it before starting; it is the
target, not the finished art (its mascot is lumpy, see below):
`/work/media/313-design-sprites-before-after.png`, `313-design-dontakote-wall-before-after.png`,
`313-design-konbini-coolers-before-after.png`.

## Approach

Rewrite the drawing functions of the two tools; keep their `main()`, key list, registration and
`--preview` as they are.

- **Rectangles and points only** (`d.rectangle(fill=...)`, `d.point`), at half size, pixel-doubled, as
  now. No ellipse, polygon, slanted `line` or float maths, so every Pillow draws the same pixels.
- **One palette, all of it in the art-source sheets** (each was counted there). Both tools define these as
  `rgb('hex')` constants the way `generate_seven_eleven_art.py` does:

  | Name | Hex | Name | Hex |
  |---|---|---|---|
  | `INK` / `EDGE` (outline navy) | `0a1627` / `172459` | `WHITE` / `WHITE_LO` | `fafcfd` / `dae2e4` |
  | `GOLD_LIT` / `GOLD_HI` / `GOLD` / `GOLD_LO` | `f3d890` / `e3c587` / `c6a663` / `a7843b` | `STEEL_HI` / `STEEL_MID` / `STEEL` / `STEEL_LO` | `d1e2eb` / `a4b0b5` / `94a2a8` / `575c6d` |
  | `RED_LIT` / `RED_HI` / `RED` / `RED_LO` | `e78d7b` / `d16b56` / `aa4d31` / `8a3a22` | `SLATE` / `SLATE_LO` | `5b6c79` / `444f5e` |
  | `SKY` / `BLUE_HI` / `BLUE` / `BLUE_LO` | `7db9fa` / `588cc6` / `425faa` / `314b8e` | `GREEN` / `GREEN_LO` / `TEAL` / `TEAL_LO` | `83af6f` / `678e57` / `508582` / `4a6262` |
  | glass, from `pane` | `2c2d51`, `2a3151`, `4b6396` | `SHELF` (a shelf board through glass) | `8689a6` |

  The shop's yellow becomes the pack's dim gold: `GOLD` on the wall, `GOLD_HI` on the sign board and the
  yen card so they stand off the wall. `GOLD_LIT` is a one-pixel lit edge only, never a fill.
- **Light from the upper left**: a lit top and left edge, a shade on the bottom and right, on every piece.
- **The sign's lettering is still cut from the facade** (`assets/sprites/discount-store_0_0.png`), but
  as a mask, not as pixels: the tool has no Japanese font and must not need one. Everything else on the
  sign, the mascot included, is drawn. (Hand-setting the two lines as bitmaps was the alternative; the
  hook line has kanji at 9px, and the mask keeps "re-run after `extract_city.py` changes the sign" true.)
- `extract_city.py` and the facade sprite are not touched.

## Changes

### `gamev2/tools/generate_discount_art.py`

Half-size coordinates; the sign is 160x64, the others 32x32. Remove `YELLOW, BLUE, INK, RED, WHITE, SHADE`
and `mascot()`.

- `lettering()`: crop the facade's top `(0, 0, 320, 128)`, `resize((160, 64), NEAREST)`, and return two
  lists of cells by luminance `(299r + 587g + 114b) // 1000`: the **name**, `lum < 110` in x 38..155,
  y 9..44; the **hook line**, `lum > 150` in x 4..155, y 47..56. (Dark on a light board, light on a dark
  band: holds if the facade's sign is recoloured later.)
- `octopus(im, cx, cy, r)`: the mascot, drawn. Same figure as the facade's: a round head (row spans from
  a hand-set table of half-widths or `math.isqrt`, bottom two rows cut flat), legs 3 wide every 5 with a
  2px gap, alternately short and long, square white eyes with an `INK` pupil, a one-row `INK` mouth.
  Shading by `(x - cx) + (y - cy)`: `RED_HI` upper left, `RED` body, `RED_LO` lower right and the right
  column of each leg, a 2px `RED_LIT` glint. Draw it on its own transparent layer, edge it with
  `generate_hokkaido.outline(layer, EDGE)`, then `alpha_composite`. Used at `r=11`, centre `(21, 25)` on
  the sign and `r=6` (legs 2 wide every 4, eyes 2x2) on the sale card. The prototype's version merges
  its legs and loses the face at `r=6`: fix both, it must read as the facade's octopus.
- `sign()`: board `GOLD_HI`. Row and column 0 and the last: `EDGE`. Inside it a 1px red frame, `RED_HI`
  top and left, `RED_LO` bottom and right. Board rows 2..45: lit `GOLD_LIT` rows 2..3 and column 2, shade
  `GOLD` rows 43..45 and columns 156..157. Marquee studs 2x2 every 8 from x=8 at rows 6..7: `RED` with a
  `RED_HI` top-left and `RED_LO` bottom-right pixel. Row 46 `EDGE`; band rows 47..61 `BLUE`, row 47
  `BLUE_HI`, rows 60..61 `BLUE_LO`. Name: each cell's shade at `(x+1, y+1)` in `GOLD` first, then the
  cells in `INK`. Hook line: shade in `BLUE_LO`, then `WHITE`. Then the octopus.
- `panel(d, y0, y1)`, shared by both walls: `GOLD`, column 0 `GOLD_HI`, column 31 `GOLD_LO` (the seam).
- `wall_top()`: panel rows 0..31; row 0 `EDGE`; the trim rows 1 `RED_HI`, 2..3 `RED`, 4 `RED_LO`; its
  shade on the panel rows 5..6 `GOLD_LO`, breaking up on row 7 (every other pixel).
- `wall()`: panel rows 0..19, row 19 `GOLD_LO`; row 20 `EDGE`; band rows 21..28 `BLUE`, row 21 `BLUE_HI`,
  rows 27..28 `BLUE_LO`; dashes 4 wide every 8 from x=3, row 24 `WHITE`, row 25 `WHITE_LO`; skirting row
  29 `SLATE`, rows 30..31 `INK`.
- `card(fill, hi, lo, edge_hi, edge_lo)`: transparent. First its shade on the wall in
  `generate_sendai_art.P_SHADE` (translucent navy): row 28, x 6..29, and columns 28..29, y 8..27. Strings
  at x 9 and 22, rows 0..5, `EDGE`. Card `[4, 5, 27, 27]`, outline `EDGE`; row 6 `hi`; rows 25..26 `lo`;
  inner border `[6, 7, 25, 25]` in `edge_hi` with its bottom and right in `edge_lo`.
- `pop_yen()`: `card(GOLD_HI, GOLD_LIT, GOLD, RED, RED_LO)`; the yen sign where it is now, in `RED`, the
  tops of its two arms `RED_HI`, the lower row of each bar and the foot of the stem `RED_LO`.
- `pop_sale()`: `card(BLUE, BLUE_HI, BLUE_LO, WHITE, WHITE_LO)`; `octopus(im, 16, 14, 6)`.
- Docstring: the look, that only the lettering comes from the facade, and the colour rule.

### `gamev2/tools/generate_cooler_art.py`

The layout does not move (32x64; lid rows 1..6, header 8..12, door 14..56, glass `[5, 15, 28, 55]`, four
shelves 10 rows apart, kick plate 58..61, handle rows 30..41). Replace the palette and what fills each part:

- Cabinet outline `EDGE` (was `INK` grey); last row `INK` (the shadow line).
- Lid: `STEEL`, row 1 and column 1 `STEEL_HI`, row 6 and column 30 `STEEL_LO`.
- Header: surround `STEEL_LO`; plate `BLUE` with row 9 `BLUE_HI`, row 11 `BLUE_LO`; the dashes `WHITE`.
  A plate, not a light box.
- Door frame `STEEL_MID`, column 1 `STEEL_HI`, columns 29..30 `STEEL` / `STEEL_LO`, row 56 `STEEL_LO`.
  Handle: `INK` column 2, `STEEL_HI` column 3.
- Glass: `EDGE` surround, then `pane(d, 5, 15, 28, 55, 11)` imported from `generate_sendai_art` (dark
  pane, slanted glare, shaded head). No strip light, no pale interior, no white diagonals.
- Shelves: board `SHELF`, no shadow row. Each drink is 2 wide: left column the body, right column its
  shade. `SHELVES` keeps its heights and groups of three/two/three; the bodies become pairs from
  `GREEN/GREEN_LO`, `TEAL/TEAL_LO`, `WHITE/WHITE_LO`, `RED_HI/RED`, `RED/RED_LO`, `GOLD_HI/GOLD`,
  `BLUE_HI/BLUE`, `SKY/BLUE_HI`, `RED_LIT/RED_HI`, `STEEL/STEEL_LO`. A bottle's cap is one `WHITE` (or
  `TEAL`) pixel top left with the glass showing top right; labels `WHITE`, `WHITE_LO`, `GOLD`, `RED`,
  `GREEN` or `BLUE`.
- Kick plate `SLATE`, top row `STEEL`, grille slots `SLATE_LO`.
- Docstring: the look; drop "lit header, four lit shelves" and "the colours of the furniture it stands
  beside".

### Regenerated art

`assets/sprites/don-takote-{sign,wall,wall-top,pop-yen,pop-sale}_0_0.png` and `office-fridge_0_0.png`,
by running the two tools from `gamev2/`. `git diff --stat` must show `config.json` unchanged.

### Docs

- `gamev2/docs/shop-and-economy.md`, the Don Takote paragraph ("is cut from the facade sprite"): the
  lettering is taken from the facade, the rest is drawn in the pack's colours.
- `gamev2/docs/generators-and-checks.md`, the `generate_cooler_art.py` paragraph: the pack's steel and
  dark glass in place of "the steel greys and glass blues of the `office-shelf-*` furniture".

### Test

New `gamev2/tools/tests/shop-art.test.js` (found by name), one test, decoding with `require('./png')` as
`konbini.test.js` does:

- each of the six: its size (320x128, 64x64 four times, 64x128) and its `spriteMetadata` exactly as
  today (sign `0.1 / 0.25`, 1x1s `0.5 / 0.5`, cooler `0.5 / 0.25`; `depthBias: 1` on the sign and the two
  cards and absent on the walls and the cooler);
- every opaque pixel's colour is in the palette table above (the list written out in the test); none is
  `ffffff`, `000000` or an old colour (`f9c22e`, `1155a8`, `1c1c22`, `c62828`, `b3e5fc`, `039be5`);
- pixel (0, 0) of the sign and of the cooler is `172459`; the walls and the sign have no see-through
  pixel; a card's only translucent pixels are `2a3151` at alpha 90;
- at least four colours of each ramp a piece uses are present (gold on the walls, red on the sign's
  mascot area, steel on the cooler), so a recolour without shading fails.

## Data and interfaces

None. No `config.json`, map, prefab, palette-index or interaction change; no room is rebuilt.

## Tests

From `gamev2/`:

```bash
python3 tools/generate_discount_art.py --preview /tmp/don.png
python3 tools/generate_cooler_art.py --preview /tmp/cooler.png
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py        # no DRIFT; generate_ads and extract_city are skip (no font)
python3 tools/sync_cities.py --check
```

- Run each tool twice: the second run changes nothing (`git status`).
- Before and after, with `node tools/play.js render <Room> out.png`: `DonTakoteOsaka`, `DonTakoteMarket`,
  `DonTakoteSapporo`, `KonbiniMarket3` (four coolers), `KonbiniSapporo1` (three). Take the befores from
  `origin/master`'s sprites before regenerating. Look at them, save them to `/work/media/`, and say in the
  summary which sprites still read as flat (expect the two wall panels to be the flattest).
- In a browser (desktop and a phone size): walk into the Don Takote in Osaka and into a konbini, look at
  the back wall and the coolers at game zoom, bump a cooler and check the drinks list still opens.
  Then `tools/browser/regress.js` (`tools/browser/README.md`).

## Risks and open questions

- **The facade's sign stays as it is** (lit yellow, black ink): it is drawn by `extract_city.py`, which
  needs a Japanese font this image does not have and which no open ticket covers. Inside and outside
  will differ in colour until it is redrawn. Reported as noticed work, not done here.
- **The shop loses its loud yellow.** That is the look's rule (no lit yellow); if the owner finds the wall
  too tan, moving the panels from `GOLD` to `GOLD_HI` is a one-constant change.
- **The cooler goes dark among old-palette neighbours** until #340 (the konbini kit) and the office kit
  are redrawn. Its drinks must still read through the dark glass at game zoom: check in the browser.
- The lettering mask depends on the committed facade; `check_generators.py` runs the tool against it in
  its scratch copy, as today.
- `generate_cooler_art.py` is run from anywhere: importing `generate_sendai_art` from `tools/` was
  checked from another directory and has no side effect.
- No open question blocks this.
