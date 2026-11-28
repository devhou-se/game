# Redraw the station interior art in the house look (#327, part 3 of #294)

## Context

`gamev2/tools/generate_station_art.py` draws what the Train Station pack lacks for the station interiors: two
walls, the front wall, the concourse floor, the gate and its two ends, ticket machines, the 7-Eleven kiosk, a
pillar, a lamp post, a clock, three hanging signs, the door mark, lockers and one `station-name-<town>` board per
row of `STATIONS` (17 fixed sprites and 8 boards today). It predates the house look ("House look: GuttyKreum" in
`gamev2/docs/generators-and-checks.md`): none of its 25 palette constants is a colour of the sheets, faces are
flat, the kiosk's case and lamp strip and the departures board are lit yellow and amber, and the clock and the
platform roundel are Pillow ellipses.

Outcome: the same sprites (keys, sizes, anchors, text and its layout) redrawn in the pack's colours with shape
and shading. No map, config or placement change. `generate_konbini_art.py` and `generate_chikagai_art.py`, which
import from this file, produce exactly what they do now.

Facts found while designing:

- The tool writes no `train*` sprite (the ticket's list mentions them): the trains are the pack's own, cut by
  `extract_train.py`, and are left alone.
- `station-name-inaka` and `station-name-yukimura` are retired sprites that keep their palette slot
  (`madeup-towns.test.js`); the tool no longer writes them. Leave both PNGs as they are.
- #279's helpers have landed (`tools/house_look.py`). #316 (chikagai) and #309 (Flinders) have landed too:
  chikagai now imports only `C, new, text, text_size, kana, latin` from this file. The konbini (#340) is not
  redrawn yet and still imports this file's colours and `box`.
- Rooms that place these sprites: the eight stations (`TokyoStation`, `HanedaStation`, `KanazawaStation`,
  `OsakaStation`, `SendaiStation`, `SapporoStation`, `AsahikawaStation`, `FukuokaStation`), `ChikagaiSapporo`
  (pillar, lockers), `FlindersSanFranbourne1` (gate, gate ends, pillar), `HanedaAirport` and
  `SanFranbourneAirport` (concourse, front wall, pillar, kiosk, exit sign). None is on the world map, so
  `assets/map` is not rebuilt.

A prototype of this design was run at design time on a copy of the repository: `config.json` came out
byte-identical, only the 25 sprites changed, every pixel is a sheet colour, no sprite has more than 24 colours,
`check_generators.py` and `test_game.js` passed, and the lamp post keeps its night halo. Its renders are on the
ticket (`327-*-prototype.png`); the numbers below are the prototype's.

## Approach

Rewrite the drawing in place, as #316 and #309 did: same file, same builder names, same `sprites()` table and
`main()`.

- **The old constants keep their names and their values.** The palette block at the top (`INK` … `LINE`) and
  `box()` stay exactly as they are, under a comment saying they are the old palette, kept only for
  `generate_konbini_art.py` until #340 redraws it, and that nothing in this file may use them (`--preview`'s
  `SLATE` background excepted). The station draws with a new palette under new names. So the konbini's sprites
  do not change, there is no DRIFT to explain, and the answer to "which constants changed" is none. (Changing
  the values instead would repaint the konbini with an untested mix a few days before #340 redraws it.)
- **The plumbing stays**: `C`, `font`, `latin`, `kana`, `new`, `text_w`, `text`, `text_size`, `stations_table`,
  `short_label`, `name_key`, `sprites`, `main`. `centred` gains an optional last argument (below).
- **Helpers**: `rgb` from `house_look`; `pane` (dark glass with a slanted glare) from `generate_sendai_art`, as
  chikagai and Flinders do. `foliage`, `roof_tile`, `repaint`, `glaze`, `flat_roof` are not needed: nothing here
  is a plant or a roof.
- **Outline** is the pack's navy `172459` (`EDGE`), as the ticket asks and as Flinders, chikagai and the street
  7-Eleven do; `0a1627` is used only for the gate ends' rails, which continue the pack's railing.
- **Drawing rules** (the recipe's): rectangles and points only, integer coordinates, no Pillow ellipse, polygon,
  arc or slanted line; light from the upper left; nothing lit (a lamp is `c6a663`, a status light `83af6f`, a
  screen is `pane`); a shadow on the floor or wall is `2a3151` at alpha 90 on clear pixels only; text stays
  1-bit `PixelMplus12` / `PressStart2P`, light text with a (+1,+1) shadow, dark text with none; at most 24
  opaque colours a sprite.

## Changes

### `gamev2/tools/generate_station_art.py`

Docstring: say the kit is in the house look, with its own palette, and why the old constants remain. Add
`import math`, `import random`, `from house_look import rgb`, `from generate_sendai_art import pane`.

New palette, after the plumbing:

```python
EDGE, NIGHT = rgb('172459'), rgb('080d16')                  # the outline; the dark behind the front wall
RAIL_INK, RAIL = rgb('0a1627'), rgb('d4c9f4')               # the pack's tube railing (extract_station.py)
TILE_HI, TILE, TILE_LO, TILE_DK = rgb('fafcfd'), rgb('dae2e4'), rgb('bcc7cc'), rgb('a4b0b5')
STONE_HI, STONE, STONE_LO, STONE_DK = rgb('fafcfd'), rgb('e4cecc'), rgb('d7b6ab'), rgb('be9e8c')
METAL_HI, METAL, METAL_LO, METAL_DK = rgb('ecfaff'), rgb('adb2c2'), rgb('848295'), rgb('646e86')   # the trains' steel
IRON_HI, IRON, IRON_LO = rgb('78768a'), rgb('5f6177'), rgb('47485d')
GOLD_HI, GOLD, GOLD_LO = rgb('f3d890'), rgb('c6a663'), rgb('a7843b')
SKY_HI, SKY, NAVY, NAVY_LO = rgb('7db9fa'), rgb('588cc6'), rgb('425faa'), rgb('314b8e')
RUST_HI, RUST, RUST_LO, RUST_DK = rgb('e78d7b'), rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')       # the 7-Eleven's
TEAL_HI, TEAL, TEAL_LO = rgb('93c297'), rgb('508582'), rgb('4a6262')
GO, GO_HI = rgb('83af6f'), rgb('93c297')                    # a signal that is on, not glowing
GLASS, GLASS_LO, GLARE = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396')                               # pane()'s
PANEL, PANEL_HI = rgb('1b1e2a'), rgb('3c3a4c')
PAINT, PAINT_LO = rgb('ecfaff'), rgb('b7c3e3')
SHADE = rgb('2a3151')[:3] + (90,)
# a line's colour is its train's (extract_train.py): (lit, base, shaded)
BAND = {'train-orange': (rgb('ef9c78'), rgb('c66347'), rgb('8d3d29')),
        'train-green': (rgb('b2ad73'), rgb('718a45'), rgb('506d33'))}
```

New helpers:

- `R(d, x0, y0, x1, y1, fill)`: `d.rectangle`, nothing when empty.
- `block(d, x0, y0, x1, y1, base, hi, lo, edge=EDGE)`: the box outlined in `edge`, filled `base`, its inner top
  row and left column `hi`, its inner bottom row and right column `lo`.
- `label(d, x, y, s, f, fill, shadow=None)`: `text`, first at (+1,+1) in `shadow` when given.
  `centred(d, cx, y, s, f, fill, shadow=None)` uses it.
- `disc(d, cx, cy, r, fill)`: rows `dy = -r..r`, each `cx ± isqrt(r*r + r - dy*dy)`.
- `hangers(d, xs, y1)`: for each `x`, rows 0..`y1`: column `x` `IRON`, column `x+1` `IRON_LO`.

Builders. Coordinates are half-size pixels, inclusive, from the sprite's top left; "block (a,b)-(c,d) X/Y/Z" is
`block` with base X, hi Y, lo Z. Later items are drawn over earlier ones.

- **`wall(line)`** 32x64, opaque, tiles sideways. Rows 0-3 `EDGE`, `IRON_HI`, `IRON`, `IRON_LO` (the ceiling's
  edge). Rows 4-27 `STONE` tile in running bond: row 4 `STONE_DK` and row 5 `STONE_LO` (the edge's shade),
  joint row 16 `STONE_LO` with row 17 `STONE_HI`, upright joints `STONE_LO` at x 15, 31 (rows 6-15) and x 7, 23
  (rows 18-27). Rows 28-35 the line's band: `EDGE`, lit, base x4, shaded, `EDGE`. Rows 36-55 `TILE` dado: row
  36 `TILE_DK`, row 37 `TILE_LO`, joint row 46 `TILE_LO` with row 47 `TILE_HI`, uprights `TILE_LO` at x 7, 23
  (rows 38-45) and x 15, 31 (rows 48-55). Rows 56-63 skirting: `EDGE`, `IRON_HI`, `IRON` x4, `IRON_LO`, `EDGE`.
- **`wall_front()`** 32x64, opaque. All `NIGHT`; coping rows 0-9: row 0 `EDGE`, row 1 `TILE_HI`, rows 2-7
  `TILE` with column 0 `TILE_LO`, row 8 `TILE_DK`, row 9 `EDGE`; its face in shade rows 10-13 `METAL_DK`, row
  14 `IRON_LO`, row 15 `EDGE`.
- **`concourse()`** 32x32, opaque. `TILE_LO`; rows 1 and 17 `TILE` (each paver's lit edge); joints `TILE_DK` on
  rows and columns 0 and 16 (drawn after the lit rows); nine flecks from `random.Random(327)` at cells with
  `x % 16 > 1 and y % 16 > 1`, every third `TILE`, the others `TILE_DK`.
- **`_cabinet(d, x0, x1)`**: `SHADE` on row 61 from `x0+1` to `x1+1`; top block (x0,26)-(x1,47)
  `METAL`/`METAL_HI`/`METAL_LO`; ticket slot `EDGE` (x0+2,30)-(x1-2,33) holding `GLASS` (x0+3,31)-(x1-3,32); IC
  reader `EDGE` (x0+2,39)-(x1-2,44) holding `NAVY` rows 40-43, row 40 `SKY_HI`, row 43 `NAVY_LO`; front block
  (x0,47)-(x1,60) `METAL_LO`/`METAL`/`METAL_DK` with rows 57-59 `METAL_DK`; go light `EDGE` (x0+3,50)-(x1-3,54)
  holding `GO` rows 51-53, row 51 `GO_HI`.
- **`gate()`**: cabinets at -7..6 and 25..38; flaps at x 7-10 and 21-24, rows 36-45: `EDGE` box, `SKY` inside,
  inner left column `SKY_HI`, inner top row `TILE_HI`, inner bottom row `NAVY`.
- **`gate_end(side)`**: two rails across the whole cell on the pack railing's rows, 42-47 and 52-57: each
  `RAIL_INK` with its middle two rows `RAIL` (the same pixels as `station-railing-mid`'s rows 20-31 and 40-51
  in its 64px cell). Then the cabinet (west end 25..38, east end -7..6). The three thin rails and the outer post
  go.
- **`ticket_machines()`** 96x64. Fare map: block (0,0)-(95,30) `TILE`/`TILE_HI`/`TILE_LO`; header (1,1)-(94,13)
  `NAVY`, row 1 `SKY`, row 13 `NAVY_LO`; `きっぷ` (kana) at (4,2) and `TICKET` (latin) at (46,4) in `TILE_HI`
  with shadow `NAVY_LO`; row 14 `TILE_DK`. Three lines, each a row from its first stop to its last: y 18 orange
  base, stops x 6, 20, 36, 52, 70, 88; y 22 green base, stops 12, 28, 44; y 26 `SKY`, stops 30, 48, 62, 80. Two
  branches join the line above, by points, i in 0..8: green (28+i, 22-(i+1)//2), `SKY` (62+i, 26-i). Each stop
  a 3x3 `EDGE` with a `TILE_HI` centre, drawn last. Three machines at x = 32i: block (x,30)-(x+31,63)
  `METAL`/`METAL_HI`/`METAL_LO`, then its lit row 31 repainted `METAL` (the map's shade); screen `EDGE`
  (x+4,33)-(x+19,45), `pane(d, x+5, 34, x+18, 44, 9)`, title bar (x+6,35)-(x+17,36) `SKY`, three buttons at
  x+6, x+11, x+16: 3 wide, rows 38-40 `GOLD` with row 38 `GOLD_HI`, and rows 42-43 `TILE`; coin slot `EDGE`
  (x+22,33)-(x+28,37) holding `GLASS` with its top row `GOLD`; note slot block (x+22,40)-(x+28,45)
  `METAL_LO`/`METAL`/`METAL_DK` with a `GLASS` slit (x+24..x+26, 42); tray `EDGE` (x+4,48)-(x+27,54) holding
  `PANEL`, its rows 52-53 `IRON_LO`; stripe (x+2,57)-(x+29,60) green base, row 57 lit, row 60 shaded.
- **`kiosk()`** 128x96 (W = 128). `stripes(d, x0, x1, y)` draws the street store's three: rows y..y+3 `RUST_HI`
  (last row `RUST`), y+5..y+9 `TEAL` (last row `TEAL_LO`), y+11..y+14 `RUST_LO` (last row `RUST_DK`).
  - Roof edge block (0,0)-(127,4) `METAL_LO`/`METAL`/`METAL_DK`. Fascia block (0,4)-(127,27)
    `TILE_HI`/`TILE_HI`/`TILE`; `stripes(1, 126, 7)`; rows 25-26 `TILE`.
  - Logo plate block (22,5)-(42,26) `TILE_HI`/`TILE_HI`/`TILE`; the 7: bar (26,8)-(38,10) `RUST_HI` with row 10
    `RUST_LO`, stem `RUST_LO` in three steps (34,11)-(37,14), (32,15)-(35,18), (30,19)-(33,23); across it
    (24,13)-(40,17) `TILE_HI` holding `TEAL` rows 14-16, row 16 `TEAL_LO`. Name plate block (46,8)-(110,22)
    `TILE_HI`/`TILE_HI`/`TILE`, `ELEVEn` (latin) centred on x 78 at y 12 in `TEAL_LO`.
  - Booth: (0,27)-(127,66) `EDGE`, (1,28)-(126,65) `IRON_LO` (dark inside; the lit strip goes), the fascia's
    shade (6,28)-(121,30) `PANEL_HI`. Three shelves at y = 30, 42, 54, x 7..120: board row y+9 `METAL`, y+10
    `METAL_DK`, y+11 `PANEL_HI`. Stock stands on each board: from x = 9 while x < 114, item `i` (starting at
    `row * 5`) is `(3, 4, 2, 5)[(i + row) % 4]` wide and `(7, 6, 8, 5)[(i * 3 + row) % 4]` tall, its body and
    top row the pair `STOCK[i % 7]`, one clear column between items. `STOCK = ((RUST_LO, RUST_HI), (GOLD,
    GOLD_HI), (NAVY, SKY), (TEAL, TEAL_HI), (RUST_HI, TILE_HI), (TILE, TILE_HI), (SKY, TILE_HI))`.
  - Side posts: blocks (0,27)-(5,95) and (122,27)-(127,95) `TILE`/`TILE_HI`/`TILE_LO`.
  - Counter top block (3,66)-(124,74) and front block (3,74)-(124,95), both `TILE`/`TILE_HI`/`TILE_LO`;
    `stripes(5, 122, 77)`; row 93 (x 5..122) `TILE_LO`.
  - Register: block (12,58)-(30,70) `METAL_DK`/`METAL_LO`/`IRON_LO`; display `EDGE` (14,54)-(26,60) holding
    `GLASS` with its top row `GLASS_LO`, three 2x2 lamps `TEAL_HI` at x 17, 20, 23, rows 57-58; keys
    (14,63)-(28,67) `METAL` with `METAL_LO` columns x 16, 19, 22, 25 and row 65.
  - Hot case: block (84,52)-(116,70) `METAL`/`TILE_HI`/`METAL_LO`; `EDGE` (86,54)-(114,66);
    `pane(d, 87, 55, 113, 65, 11)`; shelf row 60 `IRON_LO`; six buns 6x3 at x 89, 97, 105 by y 57, 62: `GOLD`,
    top row (x+1..x+4) `GOLD_HI`, bottom row `GOLD_LO`. No lit case.
  - Five papers at x = 40 + 8i: `EDGE` (x,62)-(x+6,70) holding `TILE_HI`, `TILE`, `TILE_HI`, `SKY`, `GOLD`;
    lines (x+2..x+4) on row 65 `IRON_LO` and row 67 `TILE_LO`.
  - Sign: block (40,76)-(88,91) `NAVY`/`SKY`/`GLASS`; `キオスク` (kana) centred on x 64 at y 78, `TILE_HI` with
    shadow `EDGE`.
- **`pillar()`**: `SHADE` on row 63 (x 5..28) and (26,60)-(28,62). Shaft `EDGE` (8,7)-(23,56), round: columns
  x 9..22, rows 8-55: 2 `STONE_HI`, 6 `STONE`, 3 `STONE_LO`, 3 `STONE_DK`; row 8 `STONE_DK` (the capital's
  shade). Band `EDGE` (8,18)-(23,25), columns x 9..22, rows 19-24: `SKY_HI`, `SKY`, 8 `NAVY`, 4 `NAVY_LO`.
  Capital block (5,2)-(26,7) `METAL`/`METAL_HI`/`METAL_LO`; plinth block (6,54)-(25,62)
  `METAL_LO`/`METAL`/`METAL_DK`.
- **`lamp_post()`**: `SHADE` row 63 (x 10..23). Post `EDGE` (14,13)-(17,58), column 15 `METAL`, column 16
  `METAL_DK` (rows 14-57). Head block (4,6)-(27,13) `METAL_DK`/`METAL_LO`/`IRON_LO`; the lamp (5,10)-(26,12)
  `GOLD`, row 10 `GOLD_HI`, row 12 `GOLD_LO`, its middle (15,10)-(16,12) `METAL_DK`. Base block (11,56)-(20,62)
  `METAL_DK`/`METAL_LO`/`IRON_LO`. The key is unchanged, so `DayNight` still gives it its halo.
- **`clock()`** 32x32: `hangers((15,), 4)`; body block (6,5)-(25,28) `IRON`/`IRON_HI`/`IRON_LO`; face
  `disc(15, 16, 9, EDGE)` then `disc(15, 16, 8, TILE_HI)`; the rim's shade `TILE_LO` lower right: for dy 1..8,
  w = isqrt(72 - dy*dy), the point (15+w, 16+dy), and for dy > 4 the run from 15+max(w-2, 0) to 15+w; ticks
  `IRON_LO` at (15,9), (15,23), (8,16), (22,16); ten past ten in `EDGE` points: hour (15-i, 16-(3i+2)//5) for i
  1..5, minute (15+(2i+1)//3, 16-i) for i 1..6; second hand `RUST_LO` (15+i, 16+(i+1)//2) for i 1..5; hub
  (15,16) `EDGE`.
- **`departures()`** 128x32: `hangers((10, 117), 3)`; block (0,3)-(127,31) `METAL_DK`/`METAL`/`IRON_LO`; `EDGE`
  (2,5)-(125,29) holding `PANEL` (3,6)-(124,28); a glare, two slants of 23 `GLASS` points (k+t, 28-t) for k =
  40 and 86; then `発車` (kana) at (5,7) and `DEPARTURES` (latin) at (33,9) in `GOLD`; divider row 18 (x
  4..123) `PANEL_HI`; `電車がまいります` (kana) at (5,19) and `>>` (latin) at (105,21) in `GO`. Same words and
  arrangement as now; no amber, no bright green.
- **`exit_sign()`** 64x32: `hangers((8, 54), 6)`; block (1,6)-(62,24) `GOLD`/`GOLD_HI`/`GOLD_LO`; `出口` (kana)
  at (4,9) and `EXIT` (latin) at (30,11) in `EDGE`.
- **`platform_sign()`** 64x32: `hangers((8, 54), 6)`; block (1,6)-(62,24) `NAVY`/`SKY`/`NAVY_LO`; roundel
  `disc(11, 15, 7, EDGE)`, `disc(11, 15, 6, TILE_HI)`, `1` (latin) at (9,12) in `EDGE`; `のりば` (kana) at
  (22,9) in `TILE_HI` with shadow `EDGE`.
- **`door_mark()`** 32x32, paint on the platform. `PAINT`: (4,2)-(27,3), (4,2)-(5,16), (26,2)-(27,16); worn
  `PAINT_LO`: (6,3)-(25,3), (5,4)-(5,16), (27,4)-(27,16). Two arrows at cx 11 and 20: head rows 7+i for i 0..3,
  from cx-i to cx+i in `PAINT` with the east end `PAINT_LO`; shaft (cx-1,11)-(cx+1,15) `PAINT`, its east
  column and bottom row `PAINT_LO`.
- **`lockers()`** 64x64: `SHADE` on row 62 (x 2..63) and column 63 (rows 16-61). Top block (1,6)-(62,14)
  `METAL`/`METAL_HI`/`METAL_LO`. Body `EDGE` (1,14)-(62,61) holding `METAL_DK` (2,15)-(61,60). Twelve doors
  14x14 at x = 3+15cx, y = 16+15cy: the upper two rows of doors `TILE` (top row and left column `TILE_HI`,
  bottom row and right column `TILE_DK`), the bottom row of doors `METAL` (`METAL_HI`, `METAL_LO`); number plate
  (x+3..x+6, y+3) `METAL_LO`; lock `EDGE` (x+9,y+5)-(x+12,y+9) holding (x+10,y+6)-(x+11,y+8) in the green base
  with its top-left point lit when `(cx + cy) % 3 == 0` (free), else the orange base and its lit tone.
- **`name_board(label, ja, line)`** 96x32: `SHADE` on row 31 (x 4..94) and column 94 (rows 3-31); block
  (2,1)-(93,30) `TILE_HI`/`TILE_HI`/`TILE`; band (3,24)-(92,28) the line's base, row 24 lit, row 28 shaded; the
  two arrows `TILE_HI` at x 6 and x 89, three columns each 1, 3 and 5 tall about row 26, pointing outward.
  The text is exactly as now (same strings, faces, fallback rule and positions: ja centred on x 48 at y 2,
  romaji at y 15 latin / 13 kana, a board with no ja at y 8 / 6), in `EDGE`.

`main()` is unchanged apart from nothing: it still doubles, saves, registers and dumps `config.json` the same
way, so `config.json` must come out byte-identical (`git diff --stat` shows only the 25 PNGs, the tool, the test
and the docs).

### Generated files

`gamev2/assets/sprites/station-{wall-orange,wall-green,wall-front,concourse,gate,gate-end-w,gate-end-e,ticket-machines,kiosk,pillar,lamp-post,clock,departures,exit-sign,platform-sign,door-mark,lockers}_0_0.png`
and `station-name-{tokyo,haneda,kanazawa,osaka,sendai,sapporo,asahikawa,fukuoka}_0_0.png`, by
`python3 tools/generate_station_art.py`. Nothing else: no `.tmj`, no `config.json`, no world map.

### `gamev2/tools/tests/station-interior.test.js`

One new test, modelled on #316's in `chikagai.test.js` (`require('./png')`): "the station kit is in the pack's
colours at the sizes the stations place it by (#327)".

- The 17 fixed keys and one `station-name-<town>` per station of the registry each have a PNG of the expected
  size in cells (walls, gate, gate ends, pillar, lamp post 1x2; concourse, clock, door mark 1x1; ticket machines
  3x2; kiosk 4x3; departures 4x1; exit and platform signs 2x1; lockers 2x2; name boards 3x1) and metadata
  `frameCount 1`, `anchorX 32/width`, `anchorY 32/height`.
- Every pixel is clear, or opaque in the palette above (the hexes listed once in the test), or `2a3151` at
  alpha 90; the two walls, the front wall and the concourse have no clear pixel; no sprite has more than 24
  opaque colours.
- Nothing lit: the ticket machines and the kiosk contain `2c2d51`; `c6a663` is more than a quarter of the exit
  sign and present in the lamp post; the departures board contains `1b1e2a`, `c6a663` and `83af6f`.
- The gate ends join the railing: on rows 20-31 and 40-51 of the lower cell, column 0 of `station-gate-end-w`
  and column 63 of `station-gate-end-e` equal column 0 of `station-railing-mid`.
- The two walls differ only on the band's rows (full-size rows 56-71).

### Docs

- `gamev2/docs/trains-and-stations.md`, the **Art** bullet: the generated kit is in the house look (#327):
  sheet colours only under its own palette, navy outline, light from the upper left, dark glass and unlit gold,
  the gate ends carrying the pack railing's rails; the old constants remain only for the konbini (#340).
- `gamev2/docs/generators-and-checks.md`, "House look: GuttyKreum": add the station kit beside the other
  redrawn tools if that section lists them when this lands (one sentence, naming the test).

## Data and interfaces

None. Sprite keys, sizes, anchors, `tilePalette`, `spriteMetadata`, `tileNames`, the rooms and the door cells
are unchanged. Module interface: every name importable today is still there with the same value and behaviour;
`centred` accepts one more optional argument; new names are added (the palette above, `R`, `block`, `label`,
`disc`, `hangers`, `stripes`, `STOCK`).

## Tests

From `gamev2/`:

```bash
python3 tools/generate_station_art.py --preview /tmp/station.png   # look at it; rerun: no further change
python3 tools/generate_konbini_art.py && python3 tools/generate_chikagai_art.py   # still run; git shows no change from them
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # no DRIFT; about two minutes
python3 tools/sync_cities.py --check
```

Then, as the ticket asks:

- Before and after renders, looked at, of every room that places the kit:
  `node tools/play.js render <Room> out.png` for the twelve rooms listed in Context (render the "before" set
  from `origin/master` first). Keep them out of the repository; put the ones worth showing in `/work/media/`.
- In a browser (`tools/browser/README.md`), a station by day and at `?tod=night`, on desktop and at a phone
  size: the lamp posts keep their halo, the kiosk, the ticket machines and the departures board are not lit,
  the kiosk counter still opens the shop, the gates are still walked through. Run `tools/browser/regress.js`,
  or say in the summary that it was not run.
- The summary says: constants changed: none (the old ones kept for the konbini, new ones added); rooms
  touched: none; and honestly which sprites still read flat. At design time the candidates were the door mark
  (paint on a floor), the name boards (enamel plates, by layout), the front wall and the concourse.

Commit as `gamev2: … (#294)`, one commit, no attribution line.

## Risks and open questions

- **Mixed look until the neighbours land.** The konbini interior (#340) keeps the old colours, and the pack's
  4x props and railing (#287, #297) sit beside this 2x kit. The gate ends are drawn to the railing's present
  rows; if #287/#297 redraw the railing, the join test here says so.
- **The upper wall is the pack's plaster `e4cecc`, which reads pinker than the old cream.** It matches the
  arcade's band and the pillars. If it looks wrong in the renders, the fallback is the white-tile ramp for both
  halves with only the band coloured; say which was used.
- **The concourse is `bcc7cc`, not the lighter `dae2e4`**: at `dae2e4` the white machines, lockers and kiosk
  lose their edge against the floor (compared by render at design time). The airports share this floor.
- **Two imports are new** (`house_look`, `generate_sendai_art`). Both are imported by landed tools the same way
  and neither has side effects; `check_generators.py` already runs this tool with Pillow.
- **The numbers above are a tested starting point, not a contract**: the keys, sizes, anchors, text, palette
  rule and the test are. Adjust a shape by a pixel where a render says so.
- When #340 lands, the old palette block and `box()` can be deleted from this file; not part of this ticket.
