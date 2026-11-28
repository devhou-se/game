# Design: the Izakaya interior rebuilt off the office kit (#286)

## Context

`gamev2/tools/generate_izakaya.py` builds the room `Izakaya` (in Tokyo, behind the red house at Market
`(7,37)`) from the old `office-*` kit: the checkered `office-warm-autotile` floor, a one-row
`office-wall-white` wall with `office-poster-menu` and `office-clock`, `office-shelf-drinks` / `-glass`,
three `office-counter2` as the bar with an `office-register`, `office-counter` tables, `office-plant-a/-b`,
and two `lantern-red` shrine lanterns standing indoors. It is the last interior drawn that way.

Outcome: the same room (key, 20x15, floor box, door, host cell, arrival, exits, counter cells and what
they sell, bar stools, tables and their stools, the nomikai table and opponents) drawn as an izakaya:
timber floor, a two-row plaster-and-timber back wall, a back bar of bottles, a timber bar counter, low
tables, paper lanterns hung overhead, sake casks in the corners. No `office-*` sprite is left in it except
the void every `Interior` is filled with.

A design-stage prototype of everything below was built in a scratch copy and played in the browser
(images on the ticket: `286-izakaya-before.png`, `286-izakaya-prototype-day/-night/-phone.png`,
`286-izakaya-prototype-sprites.png`). It is not in the repository; the specification below is what it drew.
There: lint 0 errors on Izakaya, Market and TokyoCity; `check_generators.py`, `play.js check` and the unit
tests pass with no existing test changed.

## Approach

**The room gets its own kit, `izakaya-in-*`, drawn by a new `tools/generate_izakaya_art.py` in the house
look** (`docs/generators-and-checks.md`, "House look: GuttyKreum"; helpers from `tools/house_look.py`).
It does not place `pub-in-*` or `home-*` sprites and does not import the pub's frame: those tools' colours
are not the pack's yet, #334 and #330 are redrawing them now (shared pixels would conflict or drift), and
a British pub's or a home's furniture is the wrong furniture. The only sprite kept from elsewhere is
`izakaya-stool_0_0` (`extract_street.py`; `Seats.js` knows it; #300 redraws it).

**The layout keeps every cell the game and the tests name.** What changes is the art, plus:

- The back wall is two rows (room rows 1-2) inside the boundary, `back_wall(..., view=True)`, as a
  7-Eleven's is, so a phone's camera does not cut it off.
- The clock is a wall piece (`izakaya-in-wall-clock`) bumped from the floor under it, `(9,3)` north; it
  still opens Time Travel. The menu is three paper strips on the wall; bumped, they say a line. (The old
  `office-poster-menu` opened Time Travel only because it shares the office clock's rule.)
- The bar is one 6x1 sprite on the cells the three `office-counter2` stood on, `(11..16, 5)`. It is the
  `venue` rule's second pattern, so it sells `shopMenu: 'izakaya'` exactly as before. No register.
- The room is `lanternLight`, as the pub is: at night it dims and the six hung lanterns glow.
- The closed pocket `(15,0)` is gone: the staff aisle (row 4) is open at its west end.

**Drawing rules** (the recipe; the checks in Tests hold the tool to them):

- Draw at 32 px a cell on `hl.canvas`, return through `hl.double`. Rectangles, single pixels and
  `hl.text` only (PixelMplus12, 1-bit); no ellipse, polygon, slanted line, gradient or alpha other than
  0/255. Round shapes are drawn a row at a time. Seeds are fixed `random.Random(n)`: a re-run is identical.
- Every colour is one of the table's. Light from the upper left: top and left edges one step lighter,
  bottom and right one step darker. Standing sprites are closed with `hl.outline` (ink `0a1627`); frame
  and ground tiles are not outlined. Lanterns are drawn unlit; the glow is the engine's.
- 1-2 cell sprites use at most 16 colours, the `bar` and `backbar` at most 24.

| Name | Colours (dark to light) | Used for |
|---|---|---|
| `W[0..5]` (local constant) | `3f210f 5a3827 71412a 7f513b aa775f bb8971` | all timber |
| `P` = `hl.RAMPS['cream']` | `8e7366 be9e8c e4cecc fafcfd` | plaster, paper, china, beer head |
| `RED, GOLD, GREEN, BLUE, STEEL, NIGHT` = `hl.RAMPS[...]` | as `house_look` has them | lantern, straw and beer, bottles and edamame, bottles and china bands, pavement and mug handles, lantern rings and clock glass |
| `hl.INK`, `hl.INK_DEEP` | `0a1627`, `080d16` | outline; the void side of the frame, cast rows |

`house_look.RAMPS` has no timber ramp. Keep `W` local to the tool (all six are sheet colours; the test
proves it) rather than editing `house_look.py`, which the redraw tickets in flight also touch.

## Changes

All paths under `gamev2/`.

### `tools/generate_izakaya_art.py` (new)

Imports `random, sys, art_register, house_look as hl`. `SPRITES` maps a piece name to a draw function;
`main()` doubles each, saves `assets/sprites/izakaya-in-<name>_0_0.png`, prints `key: WxH cells`, calls
`art_register.register(built, GLOW)`, and with `--sheet OUT.png` writes `hl.sheet(...)`. Run from
`gamev2/`. Helpers: `dot(im, x, y, c)`; `rows(im, cx2, y, widths, c)`, one row per width, each centred on
`cx2 / 2` (`x0 = (cx2 - w + 1) // 2`).

Coordinates are half-size pixels, inclusive, `(x0, y0)-(x1, y1)`; later lines paint over earlier ones.

Frame and ground (1x1 each, not outlined):

- **`floor-a`, `floor-b`** (`boards(seed, shift)`: 286/0 and 287/1). Fill `W[2]`. Four boards of 8 rows
  (`a = 8i`): row `a` `W[3]`, row `a+7` `W[1]`; three grain dashes per board at `x = randrange(32)`,
  `y = a + randrange(2, 6)`, length `randrange(3, 7)` + 1 (clipped at x 31), colour `choice((W[1], W[3]))`;
  where `i % 2 == shift` a butt joint at `j = (10, 4, 22, 26)[i]`: column `j` rows `a..a+6` `W[1]`, column
  `j+1` rows `a+1..a+6` `W[3]`. Laid `floor-a` where `(fx + fy) % 2 == 0`.
- **`side-w`**. x 0-15 `INK_DEEP`; x 16 `INK`; x 17-28 `W[1]` with x 17 `W[3]`, x 18 `W[2]`, x 28 `W[0]`,
  and a grain column x 22 on rows 5-12 and 21-28 `W[0]`; x 29 `INK`; x 30-31 `W[1]` (the wall's shade on
  the floor). **`side-e`** is its mirror, then x 0-1 `W[3]` (that face is lit).
- **`wall-front`**. Fill `INK_DEEP`; y 0 `INK`; y 1-11 `W[1]` with y 1 `W[3]`, y 2 `W[2]`, y 11 `W[0]`,
  dashes on y 6 at x 6-13 and 22-29 `W[0]`; y 12 `INK`.
- **`threshold-w`** (`-e` is its mirror). Sill y 0-12 `W[4]`, y 0 `W[5]`, y 11-12 `W[3]`; y 13 `INK`;
  pavement y 14-31 `STEEL[1]`, y 14-17 `STEEL[2]`, even x on y 18 `STEEL[2]`, y 26-31 `STEEL[0]`, odd x on
  y 25 `STEEL[0]`; door post x 0-4 full height `W[1]`, x 0 `W[3]`, x 4 `W[0]`, x 5 `INK`.

Back wall, two cells tall (64 rows), from `bay(im, x0, w)`, `BEAM, RAIL, FOOT = 6, 42, 62`:
y 0 `INK`; beam y 1-6 `W[1]`, y 1 `W[3]`, y 6 `W[0]`; plaster y 7-41 `P[2]`, y 7-8 `P[1]`, on y 9 every
`x` with `(x + 9) % 2` `P[1]`, on y 40 every `x` with `(x + 42) % 2` `P[3]`, y 41 `P[3]`; rail y 42-44
`W[1]`, y 42 `W[3]`, y 44 `W[0]`; boards y 45-61 `W[1]`, y 45 `W[0]`, and every 8 px from `x0` a `W[0]`
column with a `W[2]` column right of it on y 46-61; y 62 `W[0]`; y 63 `INK`; a post over the plaster at
`x0..x0+3`, y 7-41: `W[1]`, `x0` `W[3]`, `x0+3` `W[0]`, its shade `x0+4` on y 9-41 `P[1]`.

- **`wall`** (1x2): `bay(0, 32)`.
- **`wall-menu`** (2x2): `bay(0, 64)`, then `strip(x, 9, text, paper)` for `(8, 'ビール', P[3])`,
  `(26, '枝豆', GOLD[3])`, `(44, '唐揚げ', P[3])`. A strip is 14 wide; `w, h = hl.text_size(s,
  vertical=True, pitch=11)`, `y1 = y + h + 4`: shade `(x+1, y+1)-(x+14, y1+1)` `P[0]`; frame
  `(x, y)-(x+13, y1)` `W[0]`; paper `(x+1, y+1)-(x+12, y1-1)`; its bottom row `P[1]` on white, `GOLD[2]`
  on gold; a pin `(x+6..x+7, y+1)` `RED[1]`; the text in `INK` at `(x + 1 + (12 - w) // 2, y + 3)`.
- **`wall-clock`** (1x2): `bay(0, 32)`, then a pendulum clock: shade `(11,10)-(26,40)` `P[1]`; case
  `(9,8)-(24,38)` `W[0]`, inside `(10,9)-(23,37)` `W[2]`, its top row `W[4]`, left column `W[3]`, right
  column (from y 10) `W[1]`; dial `rows(33, 11, (6,8,10,10,10,10,10,10,8,6), W[0])` then
  `rows(33, 12, (4,8,8,8,8,8,8,4), P[3])`, two `P[2]` 2x2 marks at `(18,14)` and `(19,17)`; minute hand
  `(16,13)-(16,16)` `INK`; hour hand `(16,16)-(19,16)` `RED[0]`; pendulum window `(12,23)-(21,35)` `W[0]`,
  glass `(13,24)-(20,34)` `NIGHT[3]`, glare the five points `(14+i, 30-i)` `NIGHT[4]`; rod
  `(16,24)-(16,29)` `GOLD[1]`; bob `(15,30)-(17,32)` `GOLD[2]` with `(15,30)` `GOLD[3]`.

Small pictures, shared by the bar, the back bar and the table (`base` is the row they stand on):

- `bottle(x, base, kind, cap, h=16)`, 5 wide, `top = base - h + 1`. `GLASS[kind] = (body, hi, lo)`: green
  `(GREEN[2], GREEN[3], GREEN[1])`, brown `(W[2], W[4], W[1])`, blue `(BLUE[1], BLUE[3], BLUE[0])`, gold
  `(GOLD[2], GOLD[3], GOLD[1])`. Cap `(x+1, top)-(x+3, top+1)`; neck `(x+1, top+2)-(x+3, top+4)` body,
  `(x+1, top+2)` hi; body `(x, top+5)-(x+4, base)`, column `x` from `top+6` hi, column `x+4` lo; label
  `(x, base-6)-(x+4, base-2)` `P[3]`, its right column `P[2]`, a mark `(x+1, base-5)-(x+2, base-3)`
  `RED[1]` (`INK` on a gold bottle).
- `flask(x, base)`: `rows(2x+3, base-6, (2,2,4,4,4,4,4), P[2])`; column `x` rows `base-4..base` `P[3]`,
  column `x+3` `P[1]`; band row `base-2` `BLUE[2]`; a cup `(x+6, base-1)-(x+8, base)` `P[3]`, `(x+8, base)`
  `P[1]`.
- `mug(x, base)`: beer `(x, base-6)-(x+3, base)` `GOLD[2]`, column `x` `GOLD[3]`, column `x+3` from
  `base-5` `GOLD[1]`; head `(x, base-7)-(x+3, base-6)` `P[3]`, `(x+3, base-6)` `P[1]`; handle `STEEL[4]`:
  `(x+4..x+5, base-4)`, `(x+4..x+5, base-1)`, `(x+5, base-3..base-2)`.
- `plate(x, base, food)`: `rows(2x+8, base-3, (7,9,9,7), P[3])`; `(x+1..x+7, base)` `P[1]`; eight dots at
  `(2,-3) (4,-3) (6,-3) (3,-2) (5,-2) (1,-2) (7,-2) (4,-4)` from `(x, base)`, the i-th coloured
  `(GREEN[4], GREEN[3], GREEN[2])[i % 3]` for edamame, `(GOLD[2], GOLD[1], W[3])[i % 3]` for karaage.

Furniture:

- **`backbar`** (6x2, 192x64; `rnd = random.Random(286)`). Fill `INK`. Top `(1,1)-(190,3)` `W[2]`, y 1
  `W[4]`, y 3 `W[0]`. Shelf back `(1,4)-(190,49)` `W[0]`. Shelf boards at y 23 and y 46, 3 rows each:
  `W[3]`, top row `W[5]`, bottom row `W[1]`. Rows y 4 and y 26 `INK_DEEP` (the board above casts them).
  Cupboard `(1,49)-(190,62)` `W[2]`, y 49 and y 62 `W[0]`. Per bay `b` (0-5, `x0 = 32b`), in this order:
  if `b`, a divider `x0-1..x0` on y 4-62 `W[1]` with column `x0-1` `W[3]`; a sliding door
  `(x0+3,51)-(x0+28,60)` `W[3]`, top row `W[4]`, bottom row and right column `W[1]`, a pull
  `(x0+14,55)-(x0+17,56)` `W[0]`; top shelf four bottles on base 22 from `x = x0+3`, each
  `kind = rnd.choice(('green','brown','green','blue','brown'))`, `cap = rnd.choice((GOLD[2], RED[1],
  P[3]))`, then `x += 6 + rnd.randrange(2)`; lower shelf, base 45: even bays three `h=13` bottles at
  `x0+3+7i` of `rnd.choice(('gold','brown','gold'))` with a `RED[1]` cap, and (not bay 4) a flask at
  `x0+23`; odd bays flasks at `x0+3` and `x0+13` and two stacked cups, `i` in 0-1:
  `(x0+24, 43-4i)-(x0+27, 45-4i)` `P[3]`, column `x0+27` `P[1]`, band `(x0+24..x0+26, 44-4i)` `BLUE[3]`.
  22 colours.
- **`bar`** (6x1, 192x32; `rnd = random.Random(2860)`). `(0,0)-(191,30)` `INK` (row 31 clear). Top
  `(1,1)-(190,12)` `W[4]`, y 1 `W[5]`; 26 grain dashes at `x = randrange(2, 182)`, `y = randrange(3, 10)`,
  length `randrange(4, 9)` + 1, `choice((W[5], W[3]))`; then y 11 `W[3]`, y 12 `W[2]`, y 13 `W[0]`. Front
  `(1,14)-(190,28)` `W[1]`; every 16 px from x 1 a `W[0]` column with a `W[2]` column right of it; y 22
  `W[0]`, y 23 `W[2]` (the foot rail); y 29 `W[0]`; column 190 on y 14-29 `W[0]`. On the top: `mug(14, 9)`,
  `plate(38, 9, 'edamame')`, `flask(68, 9)`, `mug(98, 9)`, `plate(120, 9, 'karaage')`, `flask(150, 9)`,
  `bottle(176, 10, 'green', GOLD[2], h=10)`, `bottle(182, 10, 'brown', RED[1], h=10)`. 20 colours.
- **`table`** (2x1, 64x32; `rnd = random.Random(28600)`). Top `(2,4)-(61,17)` `W[4]`, top row and left
  column `W[5]`; 9 dashes at `x = randrange(4, 50)`, `y = randrange(6, 16)`, length `randrange(4, 9)` + 1,
  `choice((W[5], W[3]))`; apron y 18 `W[3]`, y 19 `W[2]`, y 20 `W[1]` (x 2-61); legs at x 4-7 and 56-59,
  y 21-28: `W[1]`, left column `W[2]`, right column `W[0]`; `(8,21)-(55,21)` `W[0]`; `mug(12, 13)`,
  `mug(44, 12)`, `plate(26, 14, 'edamame')`; `hl.outline`. 16 colours.
- **`chochin`** (1x2, 32x64; hung, on Tops). With `WD = (12,16,18,20,20,20,20,20,20,20,20,20,18,16,12)`:
  `rows(33, 37, WD, RED[1])`; per row `i` (`y = 37+i`, `x0 = (34 - wd) // 2`): `x0..x0+wd//4` `RED[2]`,
  the last `wd//5 + 1` px `RED[0]`, and where `i % 3 == 2` a rib `x0+1..x0+wd-2` `RED[0]` with
  `x0+1..x0+wd//4` back to `RED[1]`; glints `(9,40) (9,41) (10,39)` `RED[3]`; rings at y 34 and y 52, 3
  rows, x 11-21: `NIGHT[2]`, top row `NIGHT[4]`, x 20-21 `NIGHT[1]`; tassel knob `(15,55)-(17,57)`
  `GOLD[1]`, `(15,55)` `GOLD[2]`; `hl.outline`; then the cord: column 16 on y 0-33 `INK`, and columns 15
  and 17 on y 0-32 cleared (the cord is one pixel, not an outlined bar). 9 colours.
- **`casks`** (1x2, 32x64; two stacked straw-wrapped sake casks, `cask(34)` then `cask(6)`, then
  `hl.outline`). `cask(y)`, 27 rows: `rows(31, y, (22, 24) + (26,) * 23 + (24, 22), GOLD[2])`; on every
  row the first 2 px `GOLD[3]`, the last 3 `GOLD[1]`; `(4..27, y)` `GOLD[3]`; ropes at `y+4` and `y+22`,
  2 rows on x 3-28: `W[2]`, top row `W[4]`, a `W[0]` knot on the lower row every 3 px from x 4; brand
  panel `(8, y+7)-(23, y+20)` `P[3]`, bottom row `P[1]`, right column `P[2]`; `hl.text(im, 10, y+8, '酒',
  RED[1])`; `(3, y+25)-(28, y+26)` `GOLD[0]`. 12 colours.

`GLOW = {'izakaya-in-chochin_0_0': [{'x': 0.5, 'y': 1.4, 'r': 1.3, 'color': 0xff8a5a, 'a': 0.5}]}`. (The
key must not contain `-lanterns` or `lamp-post`: `art_register` gives those no spots.)

### `tools/generate_izakaya.py` (rewrite the interior block; the street-door block is untouched)

Keep `HOST`, `DOOR`, `LANTERNS` (the two on the street in Market), `SIGNS`, the opponents, the
`drinkingGame` flag and everything after `it.room(...)`. Update the docstring: what the room is drawn
with, and that `generate_izakaya_art.py` runs first. The interior becomes:

```python
LAMPS = (3, 7, 10)                       # room columns of the lanterns hung along the back wall
CASKS = ((2, 12), (17, 12), (17, 5))     # the feet of the cask stacks
s = lambda piece: f'izakaya-in-{piece}_0_0'

it = Interior(16, 10, ox=2, oy=3, w=20, h=15)
it.floor(lambda fx, fy: s('floor-a' if (fx + fy) % 2 == 0 else 'floor-b'))
it.side_walls(s('side-w'), s('side-e'), 2)
it.front_wall(s('wall-front'), (7, 8), (s('threshold-w'), s('threshold-e')))
WALL = {2: ('wall-menu', 2), 7: ('wall-clock', 1)}     # floor columns: the menu on room x 4-5, the clock on 9
pieces, fx = [], 0
while fx < it.fw:
    piece, w = WALL.get(fx, ('wall', 1))
    pieces.append((fx, s(piece), w))
    fx += w
it.back_wall(pieces, 2, view=True)                     # room rows 1-2

ib = it.b                                              # room coordinates from here
ib.stand(s('backbar'), 11, 3, 6)                       # head over wall row 2, solid on (11..16, 3)
ib.prop(s('bar'), 11, 5, 6)                            # (11..16, 5): the counter's cells
for x in (11, 13, 15):
    ib.prop('izakaya-stool_0_0', x, 6)
for tx, ty in TABLES:                                  # [(4, 7), (4, 11), (12, 10)], unchanged
    ib.prop(s('table'), tx, ty, 2)
    for sx, sy in ((tx, ty - 1), (tx, ty + 1)):
        ib.prop('izakaya-stool_0_0', sx, sy)
    ib.put('Tops', tx + 1, ty - 2, s('chochin'))       # (5,5), (5,9), (13,8): over each table
for x in LAMPS:
    ib.put('Tops', x, 2, s('chochin'))                 # cord down the wall, paper over floor row 3
for x, y in CASKS:
    ib.stand(s('casks'), x, y)
ARRIVE = it.doorway(7, HOST, outside)[0]               # no mat: the thresholds draw the exit cells
cfg['rooms']['Izakaya'] = it.room('Izakaya', npcs=..., lanternLight=True, shopEnabled=False,
                                  shopMenu='izakaya', drinkingGame={...})   # no pockets
```

Nothing else is placed: no `office-*`, no `ib.stamp('lantern-red', ...)` indoors, no plants, no register.
Expected: boundary `[[2,1],[18,1],[18,13],[11,13],[11,14],[9,14],[9,13],[2,13]]`; exits `(9,13)`,
`(10,13)` to Market `(7,38)`; arrival `(9,12)`; Market and `devhouse.world` byte-identical.

### `src/utils/Interactions.js`

- venue rule: `pattern: /^(office-counter2|izakaya-in-bar)/` (other shops still use `office-counter2`).
- konbini clock rule: `pattern: /^(konbini|izakaya-in)-wall-clock/` (it is already `footprint: true`).
- new, beside the other flavour rules: `{ kind: 'menu-strips', group: 'flavour', pattern:
  /^izakaya-in-wall-menu/, footprint: true, say: 'beer, edamame, karaage, in a hand that has written them
  ten thousand times. order at the counter' }`.

### `tools/check_generators.py`

`ART_TOOLS += ['generate_izakaya_art']` on its own line before the `make_worldmap` comment and
`ART_TOOLS += [WORLDMAP]` (the world map stays last). `generate_izakaya` is already in `GENERATORS`.

### Generated (commit what the tools write)

`python3 tools/generate_izakaya_art.py`, `python3 tools/generate_izakaya.py`,
`python3 tools/config_to_tiled.py Izakaya Market`: 15 new PNGs in `assets/sprites/`; `config.json`
(15 `spriteMetadata` and `tileNames` entries, 15 keys appended to `tilePalette`, room `Izakaya`);
`tiled/izakaya.tmj`. `tiled/market.tmj` and `assets/map` do not change (the check confirms it).

### `tools/tests/izakaya.test.js` (add; the existing tests stay as they are and pass)

See Tests 1-4. Use `tools/tests/interiors.js`-style lookups (`pub.test.js`) and the PNG decoding and
sheet-colour set of `house-look.test.js`.

### Docs

- `docs/shop-and-economy.md`: the table row `office-counter2*` (the bar) becomes `izakaya-in-bar` (the
  bar); the Izakaya bullets say what the room is drawn with and by which tool, that the wall clock opens
  Time Travel and the menu strips say a line, and that it is `lanternLight`.
- `docs/generators-and-checks.md`, "Asset Generation": a paragraph for
  `tools/generate_izakaya_art.py [--sheet out.png]` (15 `izakaya-in-*` sprites, house look, procedural,
  writes `spriteMetadata` / `tileNames`; `generate_izakaya.py` appends the palette keys), beside the
  konbini one.

## Data and interfaces

- New sprite keys (cells): `izakaya-in-floor-a`, `-floor-b`, `-side-w`, `-side-e`, `-wall-front`,
  `-threshold-w`, `-threshold-e` (1x1); `-wall`, `-wall-clock`, `-chochin`, `-casks` (1x2); `-wall-menu`
  (2x2); `-table` (2x1); `-bar` (6x1); `-backbar` (6x2); each `_0_0`. Anchors as `art_register` computes
  them; the only `glow` is the lantern's. No `depthBias`.
- `tilePalette`: 15 appended, none removed or reordered (the office keys stay; other rooms use them).
- Room `Izakaya`: gains `lanternLight: true`; boundary now starts at row 1; `shopEnabled`, `shopMenu`,
  `drinkingGame`, `transporters`, `npcs` unchanged. Market: unchanged.
- `Interactions.RULES`: two patterns widened, one flavour rule (`menu-strips`) added. No save data, no
  `Shop`, `Seats` or `GameScene` change.

## Tests

Add to `tools/tests/izakaya.test.js`, each named with `(#286)`:

1. **The room is the izakaya's own.** No key in the room's layers matches `/^office-(?!void)/`,
   `/^(lantern-red|red-lanterns)/`, `/^(pub-in-|home-|konbini-)/` or `/bin/`; every floor cell
   `(2..17, 3..12)` is `izakaya-in-floor-[ab]`; `(x, 1)` and `(x, 2)` are solid for x 2-17 and inside the
   boundary; `izakaya-in-bar_0_0` is at `(11,5)`, 6x1, solid on `(11..16, 5)`; stools at `(11,6)`,
   `(13,6)`, `(15,6)` with `(12,6)`, `(14,6)`, `(16,6)` free; the back bar's foot solid on `(11..16, 3)`
   and row 4 free; a table at each of `(4,7)`, `(4,11)`, `(12,10)` with a stool north and south; six
   `chochin` on Tops, one two rows above each table's east cell, with a glow spot in `spriteMetadata`;
   `lanternLight === true`, `shopEnabled === false`, `shopMenu === 'izakaya'`; every free floor cell is
   reached from the exits.
2. **What a bump opens.** With the room's own config and `Shop.VENUES`: `Interactions.match` gives
   `izakaya-in-bar_0_0` `{ kind: 'izakaya', group: 'shop', footprint: true }` (the venue rule takes the
   room's `shopMenu` as its kind); `izakaya-in-wall-clock_0_0` group `clock`;
   `izakaya-in-wall-menu_0_0` group `flavour`, `footprint`, a `say` of at most 100 characters; `null` for
   `wall`, `backbar`, `table`, `chochin`, `casks`, `floor-a`; `office-counter2_0_0` matches as the bar does;
   exactly one rule of kind `menu-strips`.
3. **Played** (`helpers.worldWith`): from `(12,6)` a step north does not move and
   `world.describe` matches `/^opens the IZAKAYA shop: Highball ¥\d+, Nama Beer ¥\d+, Edamame ¥\d+,
   Karaage ¥\d+/`; from `(9,3)` north opens the date picker; from `(4,3)` north says the menu line; from
   `(5,7)` west starts the drinking game.
4. **The art.** The 15 PNGs exist at the sizes above; every 2x2 block from even coordinates is one colour;
   alpha is 0 or 255; every opaque colour is in a sheet under `art-source/GuttyKreum` (not `preview*`);
   at most 16 colours, 24 for `bar` and `backbar`; the standing five (`backbar`, `bar`, `table`, `chochin`,
   `casks`) have ink on every silhouette pixel. Do not assert "no colour over half" (a floor board tile
   and `wall-front` are mostly one tone by design). `'generate_izakaya_art'` is in `check_generators.py`
   before the world map.

Run, from `gamev2/` (all must pass; `test_game.js` takes several minutes here):

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
node tools/play.js lint Izakaya Market TokyoCity      # 0 errors
node tools/play.js render Izakaya /work/media/286-izakaya.png   # and look at it
REGRESS_TIME_SCALE=2 node tools/browser/regress.js    # tools/browser/README.md; it has no Izakaya check of its own
```

Play it in a browser (Playwright, real keys; desktop 1280x800 and a phone, 844x390 with `?touch=1`): walk
in from Market `(7,38)`, bump the bar from between the stools and buy something, bump the clock and the
menu strips, sit on a stool, play the nomikai from `(5,7)`, walk out; then `?tod=night` for the dimmed room
and the lantern glow. Screenshots to `/work/media/`. Check on the phone that the top of the back wall is on
screen at the north end and that the hung lanterns draw over a player standing under them.

## Risks and open questions

- **`office-void-autotile` stays.** It is `interiors.VOID`, the shell of every generated interior, and
  other rooms' tests already exempt it. "No `office-*` sprite" is read as "none but the void". Moving the
  void off the office name is #301's kind of work, not this ticket's.
- **`lanternLight` changes the room at night** (dimmer, warm, six halos), as in the pub. It was not asked
  for by name; if the owner prefers the room as bright at night as before, drop the flag and `GLOW` (two
  lines and two assertions); nothing else depends on them.
- **The menu strips no longer open Time Travel**; the clock beside them does. Deliberate (above).
- **The stool is the old drawing** until #300; its tan is lighter than the kit's timber. Not a blocker
  (the ticket's comment says so). If #300 lands first, nothing here changes: same key, same size.
- **Tickets in flight.** #334 (pub and its frame), #330 (home kit), #340 (konbini kit) touch other tools
  only; this tool shares no pixels and no code with them. All append to `tilePalette`, `spriteMetadata`
  and `tileNames` and add an `ART_TOOLS` line: a rebase conflict there is resolved by re-running the two
  izakaya tools on top (map data is serial). Rooms touched: `Izakaya` (Market is re-run, unchanged).
- **Colour budget.** `table` sits at exactly 16 colours and `backbar` at 22; adding a detail needs a
  colour already in the sprite.
- **Pillow.** Only `fill`, `putpixel`-style points and the 1-bit bitmap font are used, so the PNGs do not
  move between the Pillow versions `check_generators.py` allows.
