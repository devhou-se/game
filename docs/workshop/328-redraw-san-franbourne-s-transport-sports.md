# Design: San Franbourne's transport, sports, terrain and creature sprites in the house look (#328, part 4 of 5 of #292)

## Context

`gamev2/tools/generate_sanfranbourne_art.py` draws every `sfb-*` sprite. Seventeen of them are this
ticket's: `sfb-cable-car`, `sfb-tram`, `sfb-rail-h`, `sfb-oval`, `sfb-goalposts`, `sfb-oval-lamp-post`,
`sfb-fog-a/-b`, `sfb-terminal`, `sfb-pier`, `sfb-sea-lions`, `sfb-palm`, `sfb-rock`, `sfb-lean-a..d`. They
were drawn before the house look (`docs/generators-and-checks.md`, "House look: GuttyKreum"): 47 of their
colours are not in the GuttyKreum sheets (the tram's greens and ambers, the turf, the seals, the palm's
trunk, the cable car's maroon, the fog's `ecf0f6`, the lamps' `fff4c8`, and the leaners' clothes, skin and
black ink), the glass is pale blue and the terminal's doors are lit, the lamps are lit yellow, and the
shapes are smooth ellipses, arcs and polygons with one flat fill each.

Outcome: the same 17 keys at the same sizes, anchors and `depthBias`, redrawn in the house look: sheet
colours only, ink silhouette, light from the upper left, roofs seen from above, dark glass with a slanted
glare, lamps unlit in dim gold, the palm a ragged crown shaded pale green to teal to blue to purple. Only
the room `SanFranbourne` places them. San Franbourne is not Japanese: a cable car, a W-class tram, a
footy oval, an airport and a prison island stay what they are; only the drawing changes.

A design-stage prototype drew all 17 and was rendered in the room (images on the ticket:
`328-sprites-before-and-prototype.png`, `328-room-crops-before-and-prototype.png`,
`328-sanfranbourne-before.png` / `-prototype.png`). It is not in the repository; the specification below
is what it drew.

## Approach

**Rewrite the 14 builder functions in place** (`wheels` to `rock`, lines 500-826 today) and leave the rest
of the file alone: part 1's sprites (#322), the airport sprites and the plane pictures (#332),
`plane_icon`'s shape, `box`, `label`, `main()`, `SPRITES`, `FLAT`, `LOOK_UP`. Three tickets edit this
file, so keep the diff inside one block: put this part's palette and helpers in one new section directly
above `wheels()`, with every name prefixed `P_`. If #322 or #332 has landed first and already defines the
same sheet colour or helper, use theirs instead of adding a second.

**Shared helpers.** #279 is merged, but `tools/house_look.py` holds none of the six helpers the ticket
names, and this file draws through `ImageDraw` on `generate_hokkaido.canvas`, so nothing in `house_look`
is needed (`generate_hokkaido.outline` is the same rule as `house_look.outline`). Import
`foliage, pane, speck, ground_shade, LEAF as P_LEAF` from `generate_sendai_art` (no side effects on
import; `check_generators` already runs both tools). Not used, on purpose: `roof_tile` (kawara: no
Japanese roof here), `repaint` (these are redrawn, not recoloured), `generate_fukuoka_art.flat_roof`
(paints `2b373c`, not a sheet colour: #375, #378) and `glaze` (keys on `4b6396`, the glare `pane()` has
just drawn).

**Drawing rules**

- Every colour is a constant from the table below. Nothing computed at run time (today `far_leg` darkens
  by `* 0.75`).
- Rectangles, points and per-pixel integer maths only in the redrawn functions: no `ellipse`, `arc`,
  `rounded_rectangle`, `polygon`, slanted `line`, `math.sin`. Two exceptions, kept as they are: the
  leaners' three `polygon` bodies and their four slanted highlight lines, and the call to `plane_icon`.
- Silhouette: `outline(im)`, ink `0a1627`, as now and as the recipe says. Lines inside take the darkest
  tone of the family they cross (`172459` in blue and glass, `8a3a22` in red, `594b45` in wood).
- Light from the upper left: lit top row and left column, shaded bottom row and right columns; an eave
  or lip casts one row of shadow on what is under it.
- Ground shade is `2a3151` at alpha 90, painted **after** the outline and only on pixels still clear
  (`cast`, below), as the Fukuoka yatai do. The palm uses `ground_shade` before its trunk, as the Sendai
  trees do.
- Glass is `pane()`; a window too small for it is `2c2d51` with a `2a3151` head row and two `4b6396`
  glare points on a diagonal.
- **Flat in function stays flat in drawing**: `sfb-oval`, `sfb-pier`, `sfb-rail-h` and the fog get no
  outline and no standing form; they are textured (stripes and tufts, alternating planks, a grooved
  rail) so no face is one colour. The implementer's summary should name these four as still reading flat.

**Palette** (every colour is in the `art-source/GuttyKreum` sheets; checked against all of them)

| Role | Colours |
|---|---|
| ink; inner navy | `0a1627`; `172459` |
| white and steel (roofs, posts, rock, rails) | `fafcfd`, `dae2e4`, `a4b0b5`, `848295`, `575f79`, `47485d`, `2a2636`; rock's top `bcc7cc`; `191c2a` (leaner d) |
| cream | `e4cecc`, `be9e8c`, `8e7366` |
| red | `d16b56`, `aa4d31` (base), `904a37`, `8a3a22`; blush `e78d7b` |
| gold: bands, bell, lamps (unlit) | `f3d890`, `c6a663` (base), `a7843b`, `86624f` |
| green: tram paint, turf | `93c297`, `83af6f`, `678e57` (the grass tile's colour), `508582`, `395050` |
| foliage ramp (`P_LEAF`) | `b1dfdc`, `93c297`, `83af6f`, `508582`, `425faa`, `3c396d` |
| wood | `be9e8c`, `bb8971` (base), `a68777`, `86624f`, `594b45` |
| fur and bark | `a68777`, `7f513b` (base), `594b45` |
| glass | `2c2d51`, head `2a3151`, glare `4b6396` |
| blue (pads, sign, jeans, backpack) | `425faa`, `314b8e`, `172459` |
| track slab joint | `413f53` (a colour of `road-plain`) |
| skin | `ffe2e0`, shade `d7b6ab` |
| translucent | shade `2a3151` a90; fog `dae2e4` a70 and a110, `fafcfd` a150 |

## Changes

### `gamev2/tools/generate_sanfranbourne_art.py`

Coordinates are half-size pixels (32 a cell), inclusive, and are the prototype's: move a pixel where the
render asks for it, but keep each canvas, what each cell covers, and the rules above. Update the module
docstring (these sprites are in the house look; the import from `generate_sendai_art`). Delete the
constants only these functions used: `TURF`, `TURF_HI`, `SEAL*`, `LEAF*`, `BLACK`. Keep `TRAM*`, `BROWN*`,
`MAROON`, `SKIN`, `AMBER`, `WOOD_HI` (part 1 and the airports use them).

Helpers (new, in this part's section):

```python
def R(d, x0, y0, x1, y1, c): d.rectangle([x0, y0, x1, y1], fill=c)
def disc(d, x, y, n, c):          # n x n, by rows; insets 6: (2,1,0,0,1,2)  8: (2,1,0,0,0,0,1,2)
def lump(im, cx, cy, rx, ry, base, hi, lo):   # a smooth body: dx, dy = (x-cx)*1000//rx, (y-cy)*1000//ry;
    # inside if dx*dx + dy*dy <= 1000000; t = dy*55//100 + dx*30//100; hi if t < -330, lo if t > 300
def cast(im, boxes):              # P_SHADE on the pixels of each box that are still clear (after outline)
```

- **`wheels`**: an 8x8 `disc` of `2a2636`, a 2x2 `848295` hub, one `575f79` point upper left.
- **`cable_car`** (3x2). Roof seen from above: deck x 6-89, y 13-19 cream, row 13 `fafcfd`, eave rows 18
  `be9e8c` and 19 `8e7366`; clerestory x 14-81, rows 7-10 `fafcfd`, its face rows 11-13 `be9e8c` with 4 px
  vents `8e7366` every 8; the bell a 6x6 gold `disc` at (45,2), lit upper left. Open ends (x 6-29, 66-89,
  y 20-45): `2a2636` shade under the roof, a bench back y 29-35 `86624f` (top row `bb8971`), seat y 36-39
  `bb8971` (top row `be9e8c`), red dash y 40-45, three 2 px cream posts. Closed middle x 30-65: red, lit
  left column, shaded right; a cream window frame (33,23)-(62,37) holding three `pane(d, x, 24, x+7, 36)`
  at x 34, 44, 54; a gold band y 40-43 (hi row, lo row) with 2x2 `86624f` dashes for lettering. Row 20
  under the eave is shadow (`8a3a22`; ink over the open ends). Running board x 4-91, y 46-51 `904a37`,
  lit top row; frame y 52-54 `594b45`; wheels at x 16, 70, y 54. Outline; `cast` rows 61-63.
- **`tram`** (4x2, faces west). Roof seen from above: x 8-119, y 5-13 `a4b0b5`, row 5 `dae2e4`, rows 12-13
  `848295`, `575f79`, a rib column every 10, corners stepped; the pole lies along it (base x 60-67, a
  `2a2636` row y 8 to x 104, a 3x3 head). Body x 4-123: cream y 14-29 (rows 14 and 29 `be9e8c`) with
  `pane(d, x, 17, x+9, 27)` at the eight window positions of today; gold band y 30-33; green y 34-49:
  `678e57`, row 34 `83af6f`, rows 44-49 `508582` joined by one dithered row (43), a gold pinstripe row 39;
  skirt y 50-54 `508582`, `395050`, `2a2636`. Lit west end column, shaded east end column, corners
  stepped. Centre doors x 57-71, y 15-53: `508582` frame, two `pane` leaves (59-63 and 65-69, y 18-49).
  Head lamp x 6-9, y 36-39 in gold (two `f3d890` pixels, `a7843b` bottom row), tail lamp x 118-121 in
  red: unlit (`AmbientTrams.lights` adds the night halos). Wheels at x 18, 34, 86, 102. Outline; `cast`.
- **`rail`** (1x1, no outline, tiles in x). Each rail three rows from y 5 and y 23: `a4b0b5` head, `2a2636`
  flangeway, `575f79` far lip. Cable slot rows 14-16: `848295`, ink, `47485d`. Slab joints: columns x 7
  and 23, rows 8-13 and 17-22, `413f53`.
- **`oval`** (12x7, flat, no outline). With `inside(x, y, a, b, cx2=383)` =
  `(2x-cx2)^2*b*b + (2y-223)^2*a*a <= a*a*b*b` and `A, B = 375, 211`: turf where `inside(A, B)`. Outside
  `inside(A-10, B-10)` a margin of plain `678e57` (so it meets the grass tile without an edge); between
  that and `inside(A-15, B-15)` the boundary line `fafcfd`; inside, mown stripes 16 px wide, `83af6f` and
  `678e57`, with tufts from `s = speck(x//2, y, 7)`: `s < 3` one tone lighter (`93c297` / `83af6f`),
  `s > 96` one darker (`678e57` / `508582`). Markings in `fafcfd`, clipped to the field: centre circle
  `37^2 < (2x-383)^2 + (2y-223)^2 <= 41^2`, centre line x 191-192, y 93-130, centre square (168,88)-(215,135),
  goal squares (10,96)-(33,127) and (350,96)-(373,127), fifty arcs `inside(220,179,c) and not
  inside(216,175,c)` for `c` = 19 and 747.
- **`goalposts`** (2x3). Four posts as now (x 8, 24, 38, 54; tops 44, 6, 6, 44), 3 px, `fafcfd` with the
  right column `a4b0b5`; pads y 74-92, 5 px: red on the tall pair, blue on the short, each lit on its top
  row and left column, shaded on its bottom row and right column. Outline; `cast` (x, 93)-(x+8, 95).
- **`light_tower`** (1x5). Mast x 14-17 `848295`, lit left column `dae2e4`, right `575f79`, rungs
  `47485d`; head x 3-28, y 6-30 `575f79`, lit top and left `a4b0b5`, shaded right and bottom; twelve 3x5
  lamps `c6a663`, top-left pixel `f3d890`, bottom row `a7843b`; foot `47485d`. No `fff4c8`: the key keeps
  `lamp-post`, so `DayNight` lights it. Outline; `cast` row 158-159.
- **`fog`** (5x2, no outline): today's two lump lists and three layers, but ragged, flat underneath, in
  sheet colours, each layer replacing (not blending) the one under it:

  ```python
  seed = 1 if kind == 'a' else 2
  for colour, grow in ((rgb('dae2e4', 70), 6), (rgb('dae2e4', 110), 0), (rgb('fafcfd', 150), -8)):
      for n, (cx, cy, r) in enumerate(lumps):
          rx = r + grow; up, down = rx * 55 // 100, rx * 35 // 100
          # for each pixel of the box, clipped to the canvas:
          dx, dy = (x - cx) * 1000 // rx, (y - cy) * 1000 // (up if y < cy else down)
          if dx * dx + dy * dy <= 1000 * (820 + speck(x // 2, y // 2, seed + n) * 3): px[x, y] = colour
  ```
- **`terminal`** (9x5). Glass wall x 40-283, y 78-157 `47485d`; one `pane(d, 44, 82, 281, 148, 31)` so the
  glare runs across the wall, then 2 px mullions every 14 and a transom y 113-114 over it; plinth y 150-157
  `848295`. Roof seen from above, a white wave: for x 36-287, `t = (x-36) % 100`,
  `h = 24*t*(50-t)//2500` if `t < 50` else `-(24*(t-50)*(100-t)//2500)`, the column from `58-h` to y 75 is
  `fafcfd` (t < 25), `dae2e4` (< 50), `a4b0b5` (< 75), `dae2e4`; standing seams where `(x-42) % 14 == 0`,
  one tone darker; the top pixel `fafcfd`. Fascia y 76-79 `a4b0b5` (lit row, dark row), its shadow rows
  80-81 `2a3151`. Doors: surround x 126-193, y 106-157 `47485d`, four `pane` leaves (dark, not lit);
  sign x 122-197, y 92-106 `172459`, lit top and left `314b8e`, `plane_icon(d, 160, 99, fafcfd)`. Tower:
  shaft x 12-30, y 44-157 cream, two lit columns, four shaded; six small windows; the cab rows 18-40
  from `x0 = 8 - (y-18)*6//22` to `x1 = 34 + (y-18)*6//22`, glass by `(x + y) % 13 == 0`, head rows
  `2a3151`, three `172459` mullions; cap and gallery `dae2e4` (lit row, dark row); mast `575f79`, its tip
  `d16b56`. Outline; `cast` rows 158-159.
- **`pier`** (4x9, flat, no outline). Planks 10 px wide along the pier, alternately `bb8971` and `a68777`,
  joint columns `86624f`, butt joints staggered as now with two `594b45` nails under each; west kerb
  `86624f` with a `be9e8c` lit column, east kerb and the end `594b45`; bollards `594b45` with an
  `a68777` cap, `e4cecc` top row and an ink right column; rope points `e4cecc`. Shade `2a3151` a90 on
  rows 284-287 and columns 126-127 (replacing today's `0a1627` a90).
- **`sea_lions`** (3x2). Raft: deck y 34-51 in alternating planks (`bb8971`, `a68777`), lit top row
  `be9e8c`; face y 52-58 `594b45` with `2a2636` gaps. Three lying, each a `lump` body (rx 13, ry 6) and
  head (rx 5, ry 4) in `7f513b` / `a68777` / `594b45`, flippers `594b45`, eye and nose ink; one sitting:
  a neck built by rows (lit left two pixels, shaded right), a `lump` head, a muzzle, the three bark
  lines `fafcfd`. Outline; ripples `fafcfd`; `cast` rows 60 and 62.
- **`leaner`**: pose, pieces, order, per-piece outline and flips unchanged; only colours and a little
  shading. Ink `0a1627` (was `000000`). Looks: a top (`aa4d31`, `d16b56`, `8a3a22`), legs `314b8e` /
  `172459`, shoes `e4cecc`, hair `594b45`; b top (`86624f`, `bb8971`, `594b45`), legs `47485d` / `2a2636`,
  shoes and hair `2a2636`, beanie `d16b56` with an `aa4d31` band; c top (`678e57`, `83af6f`, `508582`),
  legs `8e7366` / `594b45`, shoes `904a37`, hair `c6a663`, pack (`314b8e`, `425faa`, tag `f3d890`); d top
  (`2a2636`, `47485d`, `191c2a`), legs `848295` / `575f79`, shoes `dae2e4`, hair `7f513b`, cap `c6a663`
  with an `a7843b` row, cup `fafcfd` with a `d16b56` line. The second legs colour is the far leg and a
  shaded right column on the near one. Skin `ffe2e0` with a `d7b6ab` row under the hair; blush `e78d7b`.
  `cast` (14,29)-(27,30) before the flip.
- **`palm`** (3x4). `ground_shade(d, 50, 120, 13)`; trunk by rows y 40-123, 5 px from
  `x = 45 + 12*t*(83-t)//(83*83)` (`t = y-40`): `7f513b`, lit left pixel `a68777`, right `594b45`, every
  sixth row a `594b45` ring. Eight fronds from (47 or 48, 40), `(side, reach, rise, droop, seed)` =
  `(-1,30,2,30,1) (1,30,2,30,2) (-1,40,10,30,3) (1,40,10,30,4) (-1,34,26,22,5) (1,34,26,22,6)
  (-1,14,30,6,7) (1,12,32,6,8)`, then `foliage(im, [(48, 39, 6, 4)], P_LEAF, 4)` for the heart and two 3x3
  `594b45` nuts under it. Outline (no `cast`).

  ```python
  def frond(im, x0, y0, side, reach, rise, droop, seed):
      for t in range(reach + 1):
          x = x0 + side * t
          y = y0 - rise * t // reach + droop * t * t // (reach * reach)          # the rib
          ln = 3 + 28 * t * (reach - t) // (reach * reach) + speck(x, 0, seed) % 3 - (2 if x % 3 == 0 else 0)
          # leaflets hang from the rib: k = 0..max(ln, 1), f = k * 100 // max(ln, 1)
          #   k == 0 P_LEAF[1]; f < 40 P_LEAF[2]; f < 70 P_LEAF[3]; f < 95 P_LEAF[4]; else P_LEAF[5]
          # and one P_LEAF[0] pixel above the rib where speck(x // 2, 1, seed) < 45
  ```
- **`rock`** (5x3). The island's top edge is today's seven points joined by integer interpolation; each
  column from it to y 88 is banded by `depth = y - top + speck(x//3, y//2, 5) % 4 + (x-80)//30`:
  `bcc7cc` (< 4), `a4b0b5` (< 11), `848295` (< 21), `575f79` (< 31), `47485d`; a short `47485d` cleft
  every 9 px; three shrubs `foliage(im, [(26,58,8,5), (89,50,7,4), (140,62,6,4)], P_LEAF, 2)`. Cell block: a flat
  roof seen from above x 42-110, y 28-35 (`a4b0b5`, lit row, two dark rows, two vents), wall y 36-52
  cream with a shadow row under the roof, lit left column, shaded right and foot, eight 4x8 dark
  windows. Lighthouse x 120-127, y 14-54 `fafcfd`, three shaded columns, the red band, a `575f79`
  gallery, the lantern `pane(d, 118, 8, 129, 12, 7)` (dark), a stepped red cap lit on its left. Outline;
  ripples `fafcfd`; `cast` rows 89-90.

### Generated files (from `gamev2/`)

1. `python3 tools/generate_sanfranbourne_art.py` rewrites the 17 `assets/sprites/sfb-*.png` of this part.
   Every other PNG it writes and `config.json` must come out unchanged (`git status`): a diff there means
   a size or anchor moved, or another part's sprite was touched.
2. `python3 tools/make_worldmap.py --pil` and commit `assets/map/world-map.png` (the overworld picture is
   drawn from the rooms' sprites; `check_generators.py` fails on a stale one).
3. Do not rerun `generate_sanfranbourne.py`, `generate_airports.py` or `config_to_tiled.py`.

### `gamev2/tools/tests/airports.test.js`

One new test, decoding with `./png` as `house-look.test.js` does:

- the 17 sprites have today's sizes (cable car 192x128, tram 256x128, rail 64x64, oval 768x448, goalposts
  128x192, lamp post 64x320, fog 320x128, terminal 576x320, pier 256x576, sea lions 192x128, palm
  192x256, rock 320x192, leaners 64x64) and `sfb-oval_0_0` / `sfb-pier_0_0` keep `depthBias` -200;
- every pixel with alpha > 0 has an RGB from the table above, listed in the test as a set of hexes (so
  no `ffffff`, `000000`, `fff4c8`, `f9c22e`, `7db9fa`), and at most 24 opaque colours a sprite;
- alpha is 255 everywhere except `2a3151` at 90, and in the fog, which is only `dae2e4` at 70 and 110
  and `fafcfd` at 150;
- glass is dark and the lamps are dim gold: the terminal has at least 20000 pixels of `2c2d51` and 1000
  of `4b6396` (prototype: 48452 and 2148), the tram, the cable car and the rock have both, the lamp post
  has `c6a663`.

### `gamev2/docs/landmarks-and-towns.md`

In San Franbourne's **Art** bullet, add one sentence: the transport, sports, terrain and creature sprites
are in the house look (`generate_sendai_art`'s `foliage` and `pane`; roofs from above, dark glass, unlit
gold lamps), and the oval, pier, rail and fog are drawn flat on purpose.

## Data and interfaces

None. Keys, sizes, anchors, `depthBias`, `tileNames`, the `tilePalette`, placements, solid cells, the
tramways, `Interactions` rules and the `lamp-post` name `DayNight` matches are unchanged. Rooms touched:
none (art only; `SanFranbourne` shows it, and the world map picture is rebuilt).

## Tests

From `gamev2/`:

1. Before editing: `node tools/play.js render SanFranbourne /work/media/328-before.png`; after: the same to
   `328-after.png`, and `python3 tools/generate_sanfranbourne_art.py --preview <outside the repo>.png`.
   Look at both, and at the new sprites beside the sheets (`python3 tools/house_look.py --sheet`). The
   summary says which sprites still read as flat.
2. `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
   `python3 tools/check_generators.py` (no DRIFT; `generate_sanfranbourne_art`, `generate_sanfranbourne`
   and the world map all `ok`), `python3 tools/sync_cities.py --check`.
3. Browser regression per `tools/browser/README.md` (`REGRESS_TIME_SCALE=2` in the container); its
   streetcar ride is San Franbourne's cable car (`regress_tram.png`, `regress_phone_tram.png`: look at
   them). Then play it at desktop and a phone size, day and
   `?tod=night`: watch both cars pass in each direction (the art is mirrored) with their night halos,
   walk the oval under the fog and the lit towers, the pier to its end, bump the sea lions and a leaner,
   walk into the terminal's doors. Screenshots to `/work/media/`. If the regression cannot run, say so.
4. Commit: `gamev2: <what changed> (#292)`.

## Risks and open questions

- **"Outline in the pack's navy"** is read as the recipe's ink `0a1627`, which these sprites and the rest
  of the file already use; inner lines are `172459`. Two approved redraws (the Fukuoka yatai, the Flinders
  design) outline in `172459` instead. If the owner wants that here it is one argument, `outline(im, NAVY)`,
  but it should then be the same in #322 and #332.
- **Same file as #322 and #332.** Either order works; whoever lands second rebases, reruns the tool and
  `make_worldmap.py --pil` (the map PNG conflicts as a binary: regenerate, do not merge).
- **The leaners keep their shape**, the one place "redraw the shape" is not followed: they are people in
  the cast's proportions and the joke is the pose. They are recoloured to the sheets and re-inked. Their
  ink was the cast's black on purpose (`BLACK`, "the cast's ink"); `0a1627` beside a black-inked NPC is a
  difference too small to see, and the ticket asks for no colour outside the sheets. Skin `ffe2e0` /
  `d7b6ab` was chosen by eye from the sheets' pinks.
- **The tram's green is the grass tile's** (`678e57`): the sheets have no stronger mid green. It runs on
  the road, so it does not merge; `506b6b` was tried and read grey.
- **The fog is slightly greyer** (`dae2e4`, was `ecf0f6`) and ragged at its edge; check it over the oval
  and over the water, where it sits on the `Tops` layer above the player.
- **The terminal reads darker**: all glass, now dark. It is the look, but it is the biggest change in the
  room; the after render should be looked at for it.
- `2b373c` in `generate_sendai_art` / `generate_fukuoka_art` roofs (#375, #378) does not reach these
  sprites: neither `roof_tile` nor `flat_roof` is called.
