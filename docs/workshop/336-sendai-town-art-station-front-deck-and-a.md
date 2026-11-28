# Design: Sendai's station front, deck, arcade and tanabata pieces in the house look (#336, part 4 of 6 of #288)

## Context

`gamev2/tools/generate_sendai_town_art.py` draws 102 `sendai-*` sprites. Fourteen of them are the
station front, the pedestrian deck, the arcade and the tanabata decorations:

| Group | Keys (each `_0_0`) |
|---|---|
| Station front | `sendai-station-front`, `sendai-deck-span`, `sendai-deck-span-v`, `sendai-deck-end-e`, `-end-w`, `-end-s`, `sendai-deck-stair-e`, `-stair-w` |
| Arcade | `sendai-arcade-gate`, `sendai-arcade-roof`, `sendai-kokeshi-shop`, `sendai-sasakama-shop` |
| Tanabata | `sendai-tanabata-a`, `sendai-tanabata-b` |

They are not in the house look (GuttyKreum, #288): 3 to 43 of each sprite's 7 to 50 colours are in no
GuttyKreum sheet, the windows and the stained glass are lit yellow and bright primaries, the deck's glass is
flat sky blue, curves are Pillow ellipses and polygons, and every building is a bare front with no roof.

Outcome: the same 14 keys, sizes, anchors, door, solid, walk-through and glow data, redrawn in place in the
look. Nothing else in the tool changes.

**None of the 14 is placed**: no key is in `config.json`, `tiled/` or `src/`. So "the station and arcade
rooms rendered before and after, day and `?tod=night`" can only be the tool's own previews
(`--scenes DIR` writes `sendai_art_station.png`, `sendai_art_downtown.png` and a `_night.png` of each, the
night drawn by Pillow from the same glow spots the game would use). The game itself shows no change.

A design-stage prototype drew all 14 and was rendered in both scenes, day and night (images on the ticket:
`336-before-*` and `336-prototype-*`). It is not in the repository; the specification below is what it drew.
Measured on it: every colour in the sheets; 24, 15, 11, 14, 14, 14, 14, 14, 24, 6, 23, 24, 16, 20 colours
(station, span, span-v, end-e, end-w, end-s, stair-e, stair-w, gate, roof, kokeshi, sasakama, tanabata-a,
-b); no colour over 42% of a sprite.

## Approach

Rewrite the eleven builders in place (`station_front`, `deck_span`, `deck_end`, `deck_span_v`, `deck_end_s`,
`deck_stair`, `tanabata`, `arcade_gate`, `arcade_roof`, `kokeshi_shop`, `sasakama_shop`), each still one
function per sprite, same names, same `PIECES` rows. Their palette and helpers go in **one new section**,
`# ---- station, deck and arcade in the house look (#336) ----`, directly above `station_front`, with every
constant named `SA_*` and every helper `sa_*`. The prefix matters: the module's `GLASS`, `GOLD`, `WOOD`,
`STONE`, `WHITE` and the rest are the old colours and the other 88 sprites still use them.

**Geometry is kept.** Unless a line below says otherwise, every rectangle, x and y of today's builder stays
where it is and only what fills it changes. That is what keeps the anchors, the doors, the glow spots and the
joins between deck pieces true.

**Shared helpers.** Import `pane` and `roof_tile` from `generate_sendai_art` (the pack's dark window with a
slanted glare; the pack's kawara by pixel). Keep using `canvas`, `outline`, `rgb`, `CLEAR` (hokkaido), `text`,
`kana`, `text_w`, `h3` (kanazawa) and this module's `glyph`. Do **not** use `house_look.py` (#279; this
branch does not have it), `flat_roof` or `glaze` from `generate_fukuoka_art` (they paint `2b373c`, which is
in no sheet, #378), or this module's `puff`, `grounded`, `shoji`, `arch_window`, `coals`, `bar`,
`generate_sapporo_art.glass_door` and kanazawa's `roof` in these builders. Do not edit any of those: other
sprites use them. Delete what only these builders used once nothing refers to it (grep first): `kusudama`,
`STAINED`, `stained_glass`, the `deck_*` helpers and their colours, `TREAD`, `BAMBOO*`, `KUSU_A/B/C`,
`bamboo`, `PANES`, `RAFTER`, `kokeshi`, `sasa_cake`, `CAKE*`, `INDIGO_S*`. Keep `WARM_HEX` and the other
`*_HEX` strings: they are glow colours in `lit=`.

### Drawing rules (the look, as the tests hold it)

- Half-size canvas, doubled by `build()` as now. Rectangles, points and pixel access only, whole numbers
  only: no `.line(`, `.polygon(`, `.ellipse(`, `.arc(`, `.chord(`, `.pieslice(`, no floats, no `round(`.
- Only `SA_*` colours (table below), all from the GuttyKreum sheets. Never `000000`, `2b373c`, `f6dc8c`,
  `f2c66a`, `f9c22e`. At most 24 colours a sprite, no colour over half of it.
- Silhouette: `outline(im)` (ink `0a1627`), run before any shade. Inside, a line takes the darkest tone of
  the family it crosses; ink only between two families.
- Light from the upper left: hi on top and west, lo on bottom and east; a lip casts one row of shade.
- Glass is dark: `SA_GLASS` with a slanted `SA_GLARE` and a `SA_GLASS_LO` head. Nothing is lit yellow. A lamp
  is `SA_GOLD` with at most a few `SA_GOLD_HI` pixels (under 3% of the sprite).
- Opaque everywhere except: ground shade, `2a3151` at alpha 140 or 90, painted after the outline on pixels
  still clear (`sa_cast`); and the arcade roof's panes.
- Lettering: lighter than its ground with a (+1,+1) shadow in the ground's dark tone (`sa_label`), or darker
  with none.

### Palette

| Role | Constants | Hex |
|---|---|---|
| Ink, navy | `SA_INK`, `SA_NAVY` | `0a1627`, `172459` |
| Steel and concrete | `SA_WHITE`, `SA_STEEL_HI`, `SA_STEEL`, `SA_STEEL_LO`, `SA_STEEL_DK`, `SA_STEEL_DEEP` | `fafcfd`, `dae2e4`, `a4b0b5`, `848295`, `575f79`, `47485d` |
| Tile, plaster, paper | `SA_TILE_HI`, `SA_TILE`, `SA_TILE_LO`, `SA_TILE_DK` | `ffe2e0`, `e4cecc`, `be9e8c`, `8e7366` |
| Glass | `SA_GLASS`, `SA_GLASS_LO`, `SA_GLARE` | `2c2d51`, `2a3151`, `4b6396` |
| Slate roof | `SA_SLATE`, `SA_SLATE_LO` | `5b6c79`, `2e4040` |
| Kawara ridge | `SA_KAWARA_HI` | `434857` |
| Paving | `SA_PAVE_HI`, `SA_PAVE`, `SA_PAVE_J` | `d2d2d2`, `bebaba`, `aaaaaa` |
| Gold | `SA_GOLD_HI`, `SA_GOLD`, `SA_GOLD_LO` | `f3d890`, `c6a663`, `a7843b` |
| Vermilion | `SA_RED_HI`, `SA_RED`, `SA_RED_LO` | `d16b56`, `aa4d31`, `8a3a22` |
| Blue | `SA_BLUE_DK`, `SA_BLUE`, `SA_BLUE_HI`, `SA_BLUE_PALE`, `SA_BLUE_ICE` | `314b8e`, `425faa`, `5a86de`, `7db9fa`, `bbe9ff` |
| Moss | `SA_MOSS_HI`, `SA_MOSS`, `SA_MOSS_LO`, `SA_MOSS_DK` | `93c297`, `6c8e7f`, `506b6b`, `395050` |
| Timber | `SA_WOOD_HI`, `SA_WOOD`, `SA_WOOD_LO` | `a68777`, `7f513b`, `594b45` |
| Indigo | `SA_IND_HI`, `SA_IND`, `SA_IND_LO` | `444679`, `3c396d`, `2e2f54` |
| Bamboo | `SA_BAM_HI`, `SA_BAM`, `SA_BAM_LO`, `SA_BAM_DK` | `b0c276`, `83af6f`, `678e57`, `506d33` |
| Pink | `SA_PINK`, `SA_PINK_LO`, `SA_PINK_DK` (hi is `SA_TILE_HI`) | `ff9b92`, `bb6479`, `83374f` |
| Skin | `SA_SKIN` | `ffd4b9` |
| Shade (translucent only) | `SA_SHADE` | `2a3151` |

### Helpers (all in the new section)

- `sa_face(d, x0, y0, x1, y1, base, hi=None, lo=None)`: `bar` with rectangles: base, west column hi, east
  column lo.
- `sa_seg(x0, y0, x1, y1)`: the cells of a stepped line, `n = max(|dx|, |dy|, 1)`, cell k at
  `x0 + (dx*2*k + n) // (2*n)`, same for y.
- `sa_cast(im, rects, checker=())`: for each `(x0, y0, x1, y1, alpha)` set every still-clear pixel to
  `SA_SHADE` at that alpha; `checker` rects only where `(x + y) % 2 == 0`. Called after `outline`.
- `sa_label(d, s, x, y, fill, shadow, scale=2)`: `text` at (+1,+1) in `shadow`, then at (x, y) in `fill`.
- `sa_kawara(d, x0, y0, x1, y1)`: `roof_tile(x, y - y0)` per pixel.
- `sa_flat_roof(d, x0, y0, x1, y1)`: a flat roof seen from above. Box in navy; inside it by 1 steel, its
  north row and west column `STEEL_HI`, its south row `STEEL_LO`; inside by 3 slate, with `SLATE_LO` joints
  where `(y - b) % 9 == 8 or (x - a + ((y - b) // 9) * 7) % 14 == 13` (a, b the slate's corner), and the
  slate's north row and west column `SLATE_LO` (the coping's shade).
- `sa_roof_unit(d, x, y)`: plant, 14 x 8: shade `SLATE_LO` at (+2,+2); box `STEEL_LO`; face `STEEL` with a
  `STEEL_HI` top row; grille `STEEL_DEEP` at x+3..x+8, y+3..y+5 and two 2px marks at x+10, y+3 and y+5.
- `sa_arch(d, x, y0, y1)`: 11 wide. Head rows y0..y0+2 inset 3, 2, 1 in `TILE_DK`; frame box below in
  `TILE_DK`; `pane(x+1, y0+4, x+9, y1-1)`; head glass `GLASS_LO` at (x+3..x+7, y0+1) and (x+2..x+8,
  y0+2..y0+3); a `TILE_DK` mullion at x+5 and transoms every 13 rows from y0+13.
- `sa_stained(d, x0, y0, x1, y1)`: fill ink. `cx = (x0+x1)//2`, `cy = y1 - 22`. Field of a pixel: river (4)
  if `y > y1 - 9 + WAVE[(x-x0)//3 % 16]`; else hills (3) if `y > y1 - 19 - HILL[(x-x0)//3 % 28]`; else with
  `r2 = 100*(x-cx)**2 + 121*(y-cy)**2`: sun (2) if `r2 < 22500`, ring (1) if `r2 < 48400`, else sky (0).
  `HILL = (0,1,2,3,4,5,5,6,6,6,5,5,4,3,2,1,0,-1,-2,-3,-3,-4,-4,-4,-3,-3,-2,-1)`,
  `WAVE = (0,0,1,1,2,2,1,1,0,0,-1,-1,-2,-2,-1,-1)`. Mullions 2px wide at `x0 + (x1-x0)*k//4`, k = 1, 2, 3.
  For x0+2..x1-2, y0+2..y1-2: leave ink on a mullion or where the field east or south differs (the leading);
  else the field's tone, its glare where `(x + y) % 13 == 0`: sky `BLUE_DK`/`BLUE`, ring `RED`/`RED_HI`, sun
  `GOLD_LO`/`GOLD`, hills `MOSS_LO`/`MOSS`, river `BLUE`/`BLUE_HI`. Then rows y0+2..y0+3 `GLASS_LO` between
  mullions.
- Deck (same signatures and y offsets as today's `deck_*`):
  - `sa_deck_px(x, y)`: today's rule, `PAVE_J` / `PAVE_HI` / `PAVE`. `sa_paving(..., strip=None)`: strip is
    3 rows `GOLD` over 1 row `GOLD_LO` where `x % 16 < 10`.
  - `sa_rail(d, x0, x1, y)`: row y `STEEL_HI`; rows y+1..y+5 `GLASS`, row y+1 `GLASS_LO`; where `x % 8 == 0`
    a `STEEL_LO` post y+1..y+5; where `x % 8` is 3, 4, 5 a `GLARE` pixel at `y + 7 - x % 8`.
  - `sa_back_rail`: the same 4px tall: glass y+1..y+3, posts, glare where `x % 8` is 4, 5 at `y + 7 - x % 8`.
  - `sa_slab`: rows y..y+4 `STEEL` with row y `STEEL_HI`; y+5..y+6 `STEEL_LO`; y+7..y+10 `STEEL_DEEP`.
  - `sa_pier`: today's shapes: head `STEEL_LO`, its top row `STEEL`, bottom row `STEEL_DK`; columns
    `sa_face(STEEL, STEEL_HI, STEEL_LO)` with column x+5 and the top two rows `STEEL_LO`; feet `STEEL_LO`
    with a `STEEL` top row.
  - `sa_rail_above(d, x, y0, y1, west)`: a side rail seen from above, 3 columns: `STEEL_DK, STEEL_HI,
    STEEL_LO` (west rail) or `STEEL, STEEL_HI, STEEL_DK` (east); a `STEEL_DK` tick across it on every row
    with `y % 8 == 0`.
  - `sa_deck_shade(im, x0, x1)`: `sa_cast(im, [(x0,51,x1,58,140), (x0,59,x1,93,90)], [(x0,94,x1,95,90)])`.
- `sa_kusudama(d, cx, y, cols, r=7, length=44, n=7)`, `cols = ((hi, base, lo, line), strips)` with `strips`
  pairs of (paper, fold). Today's layout (`top`, `x0`, each strip's length). Strip i: 2 columns of paper and a
  third of fold one pixel shorter; a fold-tone dot every 7 rows from `top + 3 + i % 3` at column
  `x + (yy // 7) % 2`. Hoop as today in `line`. Ball: for dy in -r..r, `half = isqrt(r*r + r - dy*dy)`, dx in
  -half..half, `t = dx + dy`: `hi` if `t < -r + 2`, `lo` if `t > r - 3`, else `base`; where
  `(2*dx + 3*dy) % 5 == 0 and abs(t) < r` swap base and hi (the folded flowers).
  `SA_KUSU_PINK = ((TILE_HI, PINK, PINK_LO, PINK_DK), ((PINK, PINK_LO), (GOLD, GOLD_LO), (TILE_HI, PINK), (RED_HI, RED)))`,
  `SA_KUSU_BLUE = ((BLUE_ICE, BLUE_PALE, BLUE_HI, BLUE), ((BLUE_PALE, BLUE_HI), (WHITE, STEEL), (BLUE_HI, BLUE), (BLUE_ICE, BLUE_PALE)))`,
  `SA_KUSU_MOSS = ((BAM_HI, MOSS_HI, MOSS, MOSS_LO), ((MOSS_HI, MOSS), (GOLD, GOLD_LO), (WHITE, STEEL), (MOSS, MOSS_LO)))`.
- `sa_doll(d, x, y, band, s=1, body=TILE, body_lo=TILE_LO, ink=False)`: today's `kokeshi` shapes: head
  `SKIN`, hair and eyes ink, body with an east column of `body_lo`, bands at rows 6 and 11 and a mark at row 8
  in `band`, a `MOSS_LO` mark at row 9; `ink=True` first lays an ink box one pixel wider round head and body.
- `sa_shop_roof(d)`: `sa_kawara(d, 2, 2, 93, 16)`, then row 2 `KAWARA_HI`. `sa_posts(d, xs, y0)`: 3 columns
  `WOOD_HI, WOOD, WOOD_LO` to y90. `sa_foot(d)`: 3..92 x 90..94 `STEEL`, top row `STEEL_HI`, bottom
  `STEEL_LO`. `sa_door_pair(d, x0, y0, x1, y1, frame)`: frame box, a `pane` each side of the middle column,
  a `GOLD` pixel 2 either side of it at mid height.

### The sprites

**`station_front`** (9x5). New: roofs seen from above, in rows that were empty or parapet.
- Walls `TILE`: wings x4..91 and x196..283, y36..97; centre x92..195, y13..102. Courses `TILE_LO` every 8
  rows (from y40; y16 and y24 on the centre), a `TILE_LO` upright every 16px in alternate courses. Row 36 of
  the wings `TILE_LO` (the coping's shade). Lit edge `WHITE` at x4..5 (y37..97) and x92..93 (y13..35); east
  edge x281..283 `TILE_LO` with x283 `TILE_DK`; x194..195 (y13..35) `TILE_LO`.
- Roofs: `sa_flat_roof` at (2,14,91,35), (196,14,285,35), (90,2,197,12); the centre's shade on the east roof,
  `SLATE_LO` at 199..203 x 17..32; `sa_roof_unit` at x 18, 58, 222, 258, y19.
- Name board 104..183 x 15..31 navy, 105..182 x 16..30 `BLUE_DK`, row 16 `BLUE`;
  `sa_label('SENDAI', 144 - text_w('SENDAI'), 17, WHITE, NAVY)`.
- Ten windows: `sa_arch(x, 44, 96)` at today's x's.
- Frame 98..189 x 36..102 `sa_face(STEEL_HI, WHITE, STEEL)`, top row `WHITE`, bottom `STEEL_LO`;
  `sa_stained(103, 40, 184, 97)`.
- `sa_slab(0, 287, 104)`, `sa_rail(0, 287, 98)`.
- Ground floor 4..283 x 115..151 `GLASS`. Six shop windows at today's x0: fascia x0..x0+24, y120..125 in
  `RED`, `MOSS_LO`, `BLUE_DK` in turn (top row the next tone up); `pane(x0, 126, x0+24, 150)`; two shelves
  (`STEEL_LO` row at y139 and y148) of seven 2px goods 3..4 tall in `RED_HI`, `WHITE`, `MOSS`, `GOLD`,
  `BLUE_HI` in rotation; a `STEEL_LO` mullion at x0+12.
- Three door pairs at today's x0: `STEEL` box y120..151 with a `STEEL_HI` top row; two leaves 12 wide,
  y122..151, `BLUE_DK` with one stepped `BLUE_HI` glare from bottom-left to top-right broken every 9 cells,
  head rows y122..123 navy; `GOLD` handles at y137.
- Sign band 97..190 x 115..119 `GOLD`, bottom row and 6px dashes on row 117 `TILE_DK`. Not lit.
- Columns at today's x's, y111..151: `sa_face(STEEL_HI, WHITE, STEEL)`, column x+4 and rows 111..114 `STEEL`.
  Base 2..285 x 152..157 `STEEL`, top row `STEEL_HI`, rows 156..157 `STEEL_LO`.

**Deck pieces** (3 rows tall; today's layout, with the `sa_` helpers; `outline`, then `sa_deck_shade` with
today's x ranges).
- `deck_span`: lamps under the slab at x10 and x78, y49..50, `GOLD` with `GOLD_HI` on the middle 4px of
  row 49.
- `deck_end`: the end rail is `sa_rail_above(d, b-2 if east else a, 4, 39, west=not east)`.
- `deck_span_v`, `deck_end_s`: centre strip 3 columns `GOLD` (x14..16) and one `GOLD_LO` (x17) where
  `y % 16 < 10`; side rails `sa_rail_above` at x0 (west) and x29 (east).
- `deck_stair`: landing, warning dots (`GOLD`), pier and prop as today. Each tread column (k = 0 at the
  uphill side): far balustrade row `STEEL_HI`, then 3 rows `GLASS` (`STEEL_LO` on a post); tread rows
  `PAVE`, with k = 0 `STEEL_LO` on the east stair and `PAVE_J` on the west (the riser's shade), k = 4
  `PAVE_HI` (the nosing) with 3 rows `GOLD` at each end, and a `PAVE_J` joint on row `21 + drop` for
  k = 1..3; near balustrade row `STEEL_HI` over 5 rows `GLASS` (`STEEL_LO` on a post) with a `GLARE` pixel
  at `37 + drop` (k = 2) and `36 + drop` (k = 3); stringer `STEEL_HI`, 4 `STEEL`, 2 `STEEL_LO`, 2
  `STEEL_DEEP`. Newels `STEEL_DK`. Mat `GOLD` with `GOLD_LO` studs where x is even and y odd. The flight's
  shade replaces the polygon: after the outline, `sa_cast` each tread column from `49 + drop` to 93 at
  alpha 90.

**`tanabata`**. Pole: columns x-1, x, x+1 in `BAM_HI`, `BAM`, `BAM_LO`; node rows `BAM_DK`, same y's as
today. `'a'`: the bent tip along `sa_seg(6,10,10,5) + sa_seg(10,5,18,4)`, each cell 2 rows `BAM` under one
`BAM_HI`; leaves (2px `BAM_LO`, then 2px `BAM_DK` one row down and 2 right) at (9,2), (12,0), (2,7), (1,13);
string `TILE_LO`; `sa_kusudama(18, 8, SA_KUSU_PINK, r=7, length=58, n=7)`; foot `STEEL_LO` with a `STEEL` top
row. `'b'`: cross pole along `sa_seg(12,10,84,7)`, 3 rows hi/base/lo; leaves at (51,2), (42,3), (8,6),
(84,3); `sa_kusudama(22, 13, SA_KUSU_BLUE, length=52)` and `(74, 14, SA_KUSU_MOSS, length=46)`; the wish
strips at today's cells, 2 wide, in (`WHITE`, `STEEL`), (`GOLD`, `GOLD_LO`), (`PINK`, `PINK_LO`),
(`WHITE`, `STEEL`) by `i % 4` (the east column the dark tone). Ground shade after the outline: six rows from y88, half-widths 10 (a, centre
x12) and 12 (b, centre x48), inset 4, 1, 0, 0, 1, 4, alpha 90.

**`arcade_gate`** (4x5).
- Gable, y6..40: `half = ((y - 5) * 124 + 35) // 70`; for `u = x - 64` in -half..half-1: rake where
  `2*half - abs(2*u + 1) < 7` (`WHITE` west, `STEEL` east); bars where `u % 14 in (0, 13)` or
  `(40 - y) % 12 == 0` (`STEEL_HI` west, `STEEL_LO` east); `GLASS_LO` where `(40 - y) % 12 == 11`; else
  `GLASS`, `GLARE` where `(x + y) % 11 == 0`. Finial `STEEL_HI` with its east half `STEEL`, cap `GOLD`.
- Tie beam `STEEL_HI`, top row `WHITE`, rows 44 and 45 `STEEL` and `STEEL_LO`, a `STEEL_LO` rivet every 10px
  on row 42.
- Pylons `sa_face(STEEL_HI, WHITE, STEEL_LO)` with columns x0+11..x0+13 `STEEL`, row 46 `STEEL`, a
  `STEEL_LO` course every 22 rows from y64; bands at y50 and y144 `GOLD` with a `GOLD_LO` third row; poster
  case navy with a `GOLD` and a `RED` sheet, two rules on each in the next tone; foot `STEEL_LO`, top row
  `STEEL`.
- Board 18..109 x 46..71 `GOLD_LO`; inside by 1 `IND_LO`, its top two rows navy (the beam's shade), bottom
  two `IND`; `sa_label('KEYAKI', 29, 52, GOLD, NAVY)`; a 7x7 `GOLD` diamond mark, hollow at its centre, centred on
  x24 and x103, rows 55..61. Strip y72..74 `STEEL_LO`, top row `STEEL_HI`, `GOLD` bulbs as today.
- Banners at today's x's, y75..101, in `RED`, `GOLD`, `MOSS_LO`, `RED` (west column hi, east lo: `RED_HI`/
  `RED_LO`, `GOLD_HI`/`GOLD_LO`, `MOSS`/`MOSS_DK`), three 4x4 `TILE_HI` squares, a notched tail to y104.
  `sa_kusudama(64, 75, SA_KUSU_PINK, r=7, length=36, n=9)`.

**`arcade_roof`** (4x4). Posts `sa_face(STEEL_HI, WHITE, STEEL_LO)`, column x0+4 `STEEL`, band `GOLD`, foot
`STEEL_LO` with a `STEEL` top row. South edge `ys = 77 + (28 * abs(2*x - 127) + 123) // 246` (equal to
today's float formula for every x). Per pixel, `v = y - (ys - 64)`: eave beams (x < 6: `STEEL_HI`, x5
`STEEL`; x > 121: `STEEL`, x122 `STEEL_LO`); ridge x61..62 `WHITE`, 63..64 `STEEL`, 65..66 `STEEL_LO`;
rafters (`v % 16 == 0` or x in 33, 94) `STEEL_HI` west of x64, `STEEL` east. **The panes stay translucent**
(the floor and the player show through): `bbe9ff` alpha 70 west, `7db9fa` alpha 95 east, and a slanted
glare `fafcfd` alpha 130 where `(x + v) % 16 == 5 and v % 16 not in (1, 15)`. Lamps `GOLD`. After
`outline`, clear the ink on the north joining edge exactly as today.

**`kokeshi_shop`** (3x3). New roof: `sa_shop_roof`. Plaster 5..90 x 17..90 `sa_face(TILE, WHITE, TILE_LO)`,
x88..90 and row 17 `TILE_LO`. Board 6..89 x 19..36 `RED_LO`, inside by 1 `RED`, its top row and west column
`RED_HI`; `sa_label('KOKESHI', 7, 21, WHITE, RED_LO)`. Beam 3..92 x 38..41 `WOOD_LO`, top row `WOOD`. Window
frame 9..43 x 44..85 `WOOD_LO`, `pane(10, 45, 42, 84)`, shelves at y+13 (2 rows `WOOD`, 1 `WOOD_LO`) for y in
49, 69, four `sa_doll` each at `12 + 8*i` with bands `RED`, `MOSS_LO`, `RED_HI` in rotation. Great doll
`sa_doll(46, 51, RED, 2, WHITE, STEEL_HI, ink=True)` on a stand: ink 44..59 x 77..89, `WOOD` inside with a
`WOOD_HI` top row, `WOOD_LO` east columns and two rules. Door 62..86 x 44..90 `WOOD_LO`,
`sa_door_pair(63, 54, 85, 90, WOOD_LO)`; noren 62..86 x 44..56 `RED`, top row `RED_HI`, bottom row and slits
(x70, x78, to y57) `RED_LO`, a 7x7 `WHITE` ring at (71, 46). `sa_posts((5, 59, 87), 42)`. Sill 9..43 x 86..90
`TILE`, top row `TILE_LO`, `RED` dots every 5px on row 88. `sa_foot`.

**`sasakama_shop`** (3x3). New roof: `sa_shop_roof`. Boards x5..90, y17..37, 6px pitch: `IND_HI`, 4 `IND`,
`IND_LO`; row 17 `IND_LO`. Sign 12..83 x 19..36 `IND_LO`, inside by 1 `TILE`, top row `WHITE`, bottom
`TILE_LO`; the four glyphs as today at y21 in `IND`, no shadow. Pent: `sa_kawara(4, 38, 91, 39)` and
`(2, 40, 93, 47)`, row 38 `KAWARA_HI` (replaces kanazawa's `roof`). Front 5..90 x 48..90 `WOOD_LO`, row 48
ink. Hatch 9..57 x 50..80 `GLASS`, rows 50..51 `GLASS_LO`, row 52 `GOLD` (the lamp, unlit). Cook: face
36..45 x 55..66 `SKIN`, kerchief 35..46 x 53..56 `WHITE`, ink eyes at (38,60), (43,60), apron 33..48 x 65..73
`IND` with an `IND_HI` top row, an arm along `sa_seg(33,68,27,71)` 2 rows `SKIN`. Charcoal 11..55 x 75..79
ink, with `k = h3(x, y, 8)`: `RED` if k < 30, `RED_HI` if k < 48, `GOLD` if k < 60; grill bar row 74
`STEEL_LO`. Cakes (`sa_cake`: the 10x5 leaf pixmap in `TILE`, a `TILE_LO` row under its middle, three
`WOOD_HI` toast marks, a 3px `WOOD` skewer) where today's are; tray `WOOD`. A wisp of smoke inside the
hatch, 12 single pixels rising from (51,72) to (51,61), `STEEL_LO` with every fourth `STEEL` (no `puff`).
Counter 7..59 x 80..83 `WOOD`, top row `WOOD_HI`, bottom ink. Leaf frieze: `BAM_LO` at
`(x, 86 + (x // 3) % 2)` where `x % 6 < 4`. Door 63..86 x 50..90 `WOOD_LO`; two paper leaves 64..74 and
75..85 x 60..89: `WOOD_LO` frame, `TILE` paper with the bottom third `TILE_LO`, `WOOD` lattice (cells 3 x 6);
noren 62..87 x 49..61 `IND`, top row `IND_HI`, bottom row and slits (x70, x79) `IND_LO`, an 8x7 `BAM_LO` leaf
at (71, 52) with an `IND_LO` vein. `sa_posts((5, 60, 88), 48)`, `sa_foot`.

## Changes

- `gamev2/tools/generate_sendai_town_art.py`: the new section; the eleven builders rewritten; the helpers
  and constants listed above deleted; imports that nothing uses any more removed. In `PIECES`, only the
  description text of these 14 rows changes (say dark glass, roofs seen from above; nothing "lit" or
  "glowing"); `door`, `solid`, `walk`, `lit` and sizes are not touched. Update the module docstring and the
  manifest's `notes` where they describe these pieces. `main()`, `build()`, `scenes()` unchanged.
- `gamev2/assets/sprites/`: the 14 PNGs. The tool rewrites the bytes of all 102 of its sprites; restore the
  other 88 (`git checkout -- <file>` for every modified sprite outside the 14) so the commit holds only the
  14.
- `gamev2/tools/tests/sendai-station-art.test.js`: new (below).
- `gamev2/docs/generators-and-checks.md`: if the checkout has the section "House look: GuttyKreum" (master
  has it, this branch did not when the design was written), add one paragraph there naming these 14 sprites
  and the test that holds them. If it does not, leave the file alone and say so in the summary.
- Not changed: `config.json`, `tiled/`, `devhouse.world`, `check_generators.py` (`ART_TOOLS` does not list
  this tool, and 88 of its sprites are not in the look yet), any other tool.

## Data and interfaces

No schema, config or map change. Pinned, and asserted by the test (cells; glow as x, y, r, colour, alpha):

| Key | Size | Doors | Solid | Walk-through | Glow |
|---|---|---|---|---|---|
| station-front | 9x5 | (3,4) (4,4) (5,4) | rows 2..4, all 9 | – | six at x 0.7, 1.65, 2.6, 6.5, 7.45, 8.4, y 4.2, r 0.8, `f6dc8c`, 0.5; (4.5, 3.7, 1.3, `f9c22e`, 0.6); (4.5, 2.15, 2.0, `fff0c0`, 0.9); (3.6, 2.2, 1.0, `7fa6ff`, 0.5); (5.4, 2.2, 1.0, `ffb040`, 0.5) |
| deck-span | 3x3 | – | (1,2) | (0,2) (2,2) | (0.45, 1.6) and (2.55, 1.6), r 0.7, `f6dc8c`, 0.5 |
| deck-span-v | 1x3 | – | – | (0,2) | – |
| deck-end-e, -w, -s | 1x3 | – | (0,2) | – | – |
| deck-stair-e, -w | 3x3 | – | row 2, all 3 | – | – |
| tanabata-a | 1x3 | – | (0,2) | – | (0.56, 0.5, 0.7, `ff8fc0`, 0.4) |
| tanabata-b | 3x3 | – | (1,2) | – | (0.69, 0.62, `8fc4ff`) and (2.31, 0.66, `9fe6a0`), r 0.7, 0.4 |
| arcade-gate | 4x5 | – | (0,4) (3,4) | (1,4) (2,4) | (2.0, 1.85, 1.6, `ffd24a`, 0.7); (2.0, 2.75, 0.7, `ff8fc0`, 0.4); (2.0, 0.8, 1.4, `bfd4ff`, 0.35) |
| arcade-roof | 4x4 | – | (0,3) (3,3) | (1,3) (2,3) | (1.0, 2.5) and (3.0, 2.5), r 1.0, `f6dc8c`, 0.35 |
| kokeshi-shop | 3x3 | (2,2) | rows 1..2, all 3 | – | (0.8, 2.0, 1.0, `f6dc8c`, 0.5); (1.5, 0.75, 1.2, `ff8a6a`, 0.3) |
| sasakama-shop | 3x3 | (2,2) | rows 1..2, all 3 | – | (1.0, 2.4, 0.9, `f0903a`, 0.55); (2.35, 2.3, 0.7, `f6dc8c`, 0.5) |

Before editing, save `python3 tools/generate_sendai_town_art.py --manifest /tmp/before.json` (then restore
the sprites); after, the 14 entries of a new manifest must be equal to it apart from `description`.

## Tests

New `gamev2/tools/tests/sendai-station-art.test.js`, on the pattern of `kanazawa-art.test.js` on master
(`module.exports = ({ test, assert, fs, path, GV2 }) => …`, `tools/png` to read pixels, the sheet colours
read from `art-source/GuttyKreum/*.png` without `preview*`; the Python cases return early without Pillow).
Every test name starts `sendai station art:`. For the 14 PNGs:

1. Size is the table's cells x 64; every 2x2 block is one colour.
2. Opaque colours are all sheet colours; none of `000000`, `2b373c`, `f6dc8c`, `f2c66a`, `f9c22e`; at most 24
   a sprite; none over half the opaque pixels; `f3d890` under 3%.
3. Alpha is 0 or 255, except: `2a3151` at 140 or 90 (deck pieces), at 90 (tanabata), and on the arcade roof
   `bbe9ff`@70, `7db9fa`@95, `fafcfd`@130 only.
4. Silhouette: every opaque pixel next to (4-way) a clear or shade pixel is `0a1627`, the canvas edge aside;
   the arcade roof is checked against fully clear pixels only, and the topmost opaque pixel of its columns
   x6..121 (half-size) is exempt: that is the edge the next roof joins.
5. Joins: on the half-size grid, the span's rows 4..7 and 34..46 repeat every 8px; the station's rows 98..110
   equal the span's rows 34..46 (x mod 96); `deck-end-e` columns 0..19 and `deck-end-w` columns 12..31 equal
   the span's same columns on rows 4..46; the stair landings (`-e` columns 0..14, `-w` columns 81..95) equal
   the span's on rows 4..18 and 23..46 (the landing has no tactile strip); `deck-end-s` rows 34..46 equal the
   span's; `deck-span-v` and `deck-end-s` agree on rows 0..25.
6. Source: the bodies of the eleven builders and of every `def sa_` contain none of `.line(`, `.polygon(`,
   `.ellipse(`, `.arc(`, `.chord(`, `.pieslice(`, `round(`, `puff(`, `grounded(`.
7. Python: `SPRITES[key]()` doubled equals the committed PNG's pixels for the 14 keys; and each key's size
   and `META` (`door`, `solid`, `walk`, `lit`) equal the table above, written out in the test.

Run, from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
`node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`.
Then `python3 tools/generate_sendai_town_art.py --scenes /tmp/after --manifest /tmp/after.json`, compare the
manifest, and look at `sendai_art_station.png`, `sendai_art_downtown.png` and both `_night.png` beside the
same four from the untouched tool. Save both sets and a contact sheet of the 14 to `/work/media/`; say in the
summary what still reads as flat (on the prototype: the deck's slab edge, the gate's pylons, the kokeshi
shop's plaster). Run the browser regression (`tools/browser/regress.js`) once: it should not change, since
nothing placed is touched.

## Risks and open questions

- **Not in the game yet.** Night is judged on the tool's Pillow preview, not `?tod=night`; the first in-game
  look comes with the Sendai rebuild that places these.
- **Same file as #333, #342, #343, #344, #345.** Touch only the eleven builders, the new section, the 14
  `PIECES` descriptions and the docstring lines about them; leave shared helpers alone, so either order merges.
- **This branch is behind `master`**; nothing here needs what it lacks.
- **Colour budget.** Station, gate and sasakama shop sit at exactly 24; a new tone there must replace one.
- **The arcade roof's panes are translucent on purpose** (the ticket keeps the floor under the roof): the
  one exception to opaque pixels besides ground shade, and why its silhouette test is looser.
- **Roofs now fill the top rows** of the station (y2..35) and both shops (y2..16), which were clear or
  parapet. Sizes, anchors and solid cells are the same; the buildings read a little taller.
- **Glow colours are unchanged** though the art under them is no longer yellow; at night the engine's glow
  supplies the light, as on the pub and the 7-Eleven.
