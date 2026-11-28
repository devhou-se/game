# Design: the Flinders concourse art in the house look (#309, part 1 of 5 of #292)

## Context

`gamev2/tools/generate_flinders_art.py` draws the 14 `flinders-in-*` sprites of the concourse inside the
station with the clocks (room `FlindersSanFranbourne1`, the only room that places them). They were drawn
before the house look existed: colours made with `mix()` (none is a GuttyKreum colour), an outline in
`INK=(38,43,68)`, a pale-blue daylit arch window, lit yellow lamps and a lit orange LED board, smooth
ellipses, polygons and gradients, and a frame (side walls, front wall, thresholds, door light) borrowed
from `generate_pub_art.py`, whose own colours are not the pack's either.

Outcome: the same 14 keys at the same sizes, anchors, depth bias and `lookUp` rows, redrawn so the room
reads like the pack: pack colours only, navy outline, dark glass with a slanted glare, unlit lamps in the
pack's dim gold, shading by hue-shifted ramps with the light from the upper left. No map, config or
placement change. Flinders is not Japanese: the building stays an Edwardian station in mustard, maroon and
copper green; only the drawing changes.

A design-stage prototype was drawn and rendered to settle the palette (images on the ticket:
`309-flinders-concourse-before/-prototype.png`, `309-flinders-sprites-before/-prototype.png`). It is not in
the repository; the specification below is what it drew.

## Approach

**Rewrite `generate_flinders_art.py` in place, and make it own every pixel it paints.** From
`generate_pub_art` import only the plumbing, `C, new, text, latin, register`. Do not import its colour
constants, `mix`, `box`, `bar`, `post`, `shadow`, or the frame functions `wall_side`, `wall_front`,
`threshold`, `doorlight`: they hard-code non-pack colours and a gradient, and #334 is about to rewrite them.
The frame is redrawn here in the same cells and shapes. With no shared pixels, #334 and this change can
merge in either order without DRIFT or a conflicting PNG. (Keeping the pub frame and repainting its output
was the alternative; it ties these sprites to a file another ticket is rewriting.)

**Shared helpers.** #279 is not merged. If, when implementing, `origin/master` has its shared look module,
import `pane` from there; otherwise `from generate_sendai_art import pane` (importing it has no side
effects). `foliage`, `roof_tile`, `repaint`, `flat_roof` are not needed: the room has no roof or plants of
its own. Do not call `generate_fukuoka_art.glaze` here: it keys on `4b6396`, which is also the glare
colour, so it would re-glaze a pane that `pane()` already drew.

**Drawing rules** (as `generate_seven_eleven_art.py` and `generate_sendai_art.py` do):

- Colours are local constants made by a local `rgb('hex', a=255)`; every one is in the table below. No
  `mix()`, no colour computed at run time.
- Rectangles and points only. No `ellipse`, `pieslice`, `arc`, `polygon` or slanted `line` (they move a
  pixel between Pillow versions). Discs are drawn a row at a time, slants a point at a time, with integer
  maths.
- Every object is closed by a 1 px `EDGE` outline, lit along its top and left, shaded along its bottom and
  right, and casts a 2-3 px shade to its lower right in the next colour down the ramp of what it falls on.
- Shade on the floor is `2a3151` at alpha 90 on transparent pixels, in whole rows with stepped corners (no
  ellipse). An alpha fill replaces pixels, it does not blend: draw floor shade first, objects over it.
- Glass is `pane()` for rectangles; for the arch the same rule per pixel: `GLARE if (x + y) % 13 == 0 else
  GLASS`, with the top two rows under the frame `GLASS_LO`. Glare is clipped inside its panel.
- Text stays `text(d, x, y, s, latin(8), fill)` (1-bit, as now).

**Palette** (all present in the `art-source/GuttyKreum` sheets; 35 colours in the prototype's output):

| Role | Colours (light to dark) |
|---|---|
| ink, outline | `INK 080d16` (void side of walls, hands, slots), `EDGE 172459` |
| mustard render | `e3c587`, `c6a663` (base), `a7843b`, `86624f` |
| maroon bands, window frame, sign | `aa4d31`, `904a37` (base), `5b283b` |
| copper green | `93c297`, `508582` (base), `4a6262`; enamel `395050`, `2e4040` |
| stone (cornice, pilaster, sill, side walls) | `fafcfd`, `e4cecc` (base), `d7b6ab`, `be9e8c` |
| bluestone foot | `78768a`, `5f6177` (base), `47485d` |
| terrazzo | `fafcfd`, `d7d0ba` (base), `be9e8c` (joint); chips `c69f96`, `e3c587`, `a4b0b5` and the ramp's ends |
| steel | `d1e2eb`, `94a2a8`, `575c6d` |
| glass | `GLASS 2c2d51`, `GLASS_LO 2a3151`, `GLARE 4b6396` |
| screens | title bar `588cc6`, text `d1e2eb`; board panel `1b1e2a` |
| lamps and LEDs (unlit) | `LAMP c6a663`, hi `f3d890`, lo `a7843b`; the board's one green lamp `83af6f` |
| daylight at the door | `fafcfd`, `ffe2e0`, `e4cecc` in flat bands |

## Changes

### `gamev2/tools/generate_flinders_art.py` (rewritten; coordinates are half-size pixels, 32 a cell)

Keep `sprites()` (same 14 keys, same order), `DEPTH_BIAS`, `LOOK_UP`, the `__main__` block and
`BAND, DADO, FOOT = 14, 62, 86`. Update the docstring: what the look is, and that the frame is drawn here.
Local helpers: `rgb`, `R` (rectangle), `box` (outlined, lit, shaded block), `ground_shade`, `disc`, `slant`,
`centred`. Coordinates below are the prototype's; adjust a pixel where the render asks for it, but keep
sizes and what each sprite's cells cover.

- **`floor-a`, `floor-b`** (1x1): terrazzo base; 46 single-pixel chips from `random.Random(246)` / `(247)`
  choosing from the chip list; joint in row 0 and column 0, a highlight in row 1 and column 1. `floor-a`
  adds the diamond inlay (half-width 8 round (16,16), maroon, lit on its upper-left edge, dark on its lower
  and right edges) with a mustard diamond of half-width 3 inside.
- **`side-w` / `side-e`** (1x1, `e` is `w` flipped): from the outside in, `INK` x 0-11, a stone pier
  x 12-21 (edge, highlight, shaded right column), mustard x 22-29 (edge, a highlight column, 3 shaded
  columns), a bluestone strip x 30-31; a maroon band at y 15-17 across the mustard.
- **`wall-front`** (1x1): stone coping y 0-9 with edge lines top and bottom and a maroon line at y 5, its
  face `be9e8c` y 10-15, an edge at y 16, `INK` below.
- **`threshold-w` / `-e`** (1x1): daylight in three flat bands (y 0-3, 4-9, 10-31, darkest at the top), two
  step lines (y 10, 22) and a 6 px maroon door post on the outer side, outlined, with a dark head and a
  stone line under it.
- **`doorlight`** (2x3, transparent): four flat steps of `fafcfd`, widening and strengthening to the sill:
  `(y0, y1, inset, alpha)` = `(28,47,9,28)`, `(48,67,6,56)`, `(68,83,3,84)`, `(84,95,0,112)`. No gradient, no
  yellow.
- **`_wall(d, w)`**, the back wall all three wall sprites start from: mustard, lined out as render courses
  (a joint every 10 rows from y 22 to the dado: a dark row and a light row under it, vertical joints every
  32 px staggered by 16 between courses); stone cornice y 0-8 with edge lines and a 3-row shade under it;
  maroon bands at `BAND` and `DADO`, 4 rows, lit top row, dark bottom row; under the dado band a darker
  field with one inset panel a cell (lit lower right, dark upper left); bluestone y `FOOT`-95 with an edge,
  a highlight row, a joint every 16 px and an `INK` last row. It must tile across the three sprites and
  across a cell seam.
- **`_lamp(d, x, y)`**: a copper bracket over an opal globe 10 px across drawn by rows: upper half stone
  with a `fafcfd` glint upper left, lower half `LAMP` with `f3d890` and `a7843b` points; outlined; a shade
  on the wall to its right and under it. Unlit: no halo, no glow.
- **`wall-bay`** (3x3): `_wall`, then a stone pilaster x 38-57 from cornice to foot with three flute lines
  and a shaded right side, a capital and a foot block 3 px wider each side, both bands carried round it, its
  shade down the wall on its right, and a `_lamp` on its face.
- **`wall-arch`** (4x3): `_wall`, then a round-headed window computed per pixel: centre x 63.5, springing
  y 45; with `r2 = (2x-127)^2 + (2(y-45)-1)^2`, glass where `r2 <= 59^2`, maroon frame to `67^2`, `EDGE` to
  `70^2`; below the springing a straight part to y 56 (glass x 34-93). Frame lit on its upper-left arc, dark
  on its right. Glass by the rule above. Over the glass in maroon: a 2 px centre mullion, a 3 px transom at
  y 44-46 with a `GLASS_LO` row under it, four fan bars from the centre by `slant`, a small boss, two short
  mullions under the transom. A stone sill `box` x 26-101, y 57-61, with a shade row under it.
- **`wall-name`** (6x3): `_wall`, two copper rods from the cornice, a copper-framed board x 40-151,
  y 26-50 with a dark enamel field, a highlight row, rivets, `FLINDERS ST` centred in stone, its shade on
  the wall below and right, and a `_lamp` either side (x 16 and 168, y 28).
- **`clocks`** (4x3): floor shade; two outlined copper posts with a collar and a bluestone foot; a rail
  with balusters between their feet; the board, a copper frame round dark enamel (x 3-124, y 8-42) with a
  stepped cresting; nine dials in threes, each a `disc` r 5 `EDGE` over r 4 `fafcfd` with a shaded lower
  right rim, an `INK` minute hand up and a maroon hour hand at 3, 6 or 9; under each a stone line plate and
  a 2x2 `LAMP`. One translucent shade row under the board, drawn before the posts.
- **`tickets`** (3x2): floor shade; two copper-green machines (`box`), each with a screen (`EDGE` then
  `pane(..., 17)`), a `588cc6` title bar, three fare lines in `d1e2eb` with a `LAMP` mark, a steel card
  slot with a card left in it, six stone keys, a dark tray; a bluestone plinth; the maroon `TICKETS` sign
  with stone letters over them.
- **`board`** (3x2): floor shade; two steel legs with feet; a steel case round a `1b1e2a` panel; three
  slanted glare streaks in `2c2d51` by `slant`, clipped at the panel's right edge; four rows, each a 5x5
  lamp (the first `83af6f`, the rest `a7843b`), short destination dashes in `a7843b`, and `BUS` in `LAMP`;
  a `GLASS_LO` rule between rows. No orange, nothing lit.

### Generated files (by rerunning the tool, from `gamev2/`)

`python3 tools/generate_flinders_art.py` rewrites the 14 `assets/sprites/flinders-in-*_0_0.png`.
`config.json` must come out byte-identical (the prototype's did): if `git diff config.json` shows anything,
a size or anchor moved, which is a bug. Do not rerun `generate_flinders.py` or `config_to_tiled.py`; the
interior is not on the world map, so `make_worldmap.py` is not rerun unless `check_generators.py` says the
map is stale.

### `gamev2/tools/tests/flinders.test.js`

Add one test, modelled on the 7-Eleven case in `konbini.test.js` (decode with `./png`):

- each of the 14 sprites has exactly its size today (board 192x128, clocks 256x192, doorlight 128x192,
  tickets 192x128, wall-arch 256x192, wall-bay 192x192, wall-name 384x192, the other seven 64x64), and its
  `spriteMetadata` row is the committed one: `frameCount` 1; anchors 0.5/0.5 for the seven 1x1 pieces,
  1/6, 1/4 for `board` and `tickets`, 1/8, 1/6 for `clocks` and `wall-arch`, 1/6, 1/6 for `wall-bay`,
  1/12, 1/6 for `wall-name`, 1/4, 1/6 with `depthBias` -40 for `doorlight`; `game.lookUp.sprites` is 2 for
  the three wall pieces;
- every pixel with alpha > 0 has an RGB in the palette table above, listed in the test as a set of hexes
  (so no `ffffff`, `000000`, and none of the old LED orange, lamp glow or pale daylight glass);
- the glass is dark and nothing is lit: `wall-arch` has at least 4000 pixels of `2c2d51` and at least 200
  of `4b6396` (the prototype: 5472 and 456), `tickets` has both, `board` has `c6a663` and no `f3d890`,
  and `doorlight` is only `fafcfd`, at alphas 28, 56, 84 and 112.

### `gamev2/docs/landmarks-and-towns.md`

In "Flinders Street's concourse (issue #246)", replace the **Art** bullet's "the frame is the pub art
tool's, in the building's colours" with what is now true: the tool draws its own frame, in GuttyKreum
colours, in the house look (dark glass, unlit lamps, navy outline), and imports only plumbing from
`generate_pub_art.py`.

## Data and interfaces

None. Sprite keys, sizes, anchors, `depthBias`, `lookUp`, the `tilePalette`, the room, its `.tmj`, door
cells and the bump rules in `Interactions.js` are unchanged. Rooms touched: none (art only;
`FlindersSanFranbourne1` shows it).

## Tests

From `gamev2/`:

1. Before editing: `node tools/play.js render FlindersSanFranbourne1 /work/media/309-before.png`; after:
   the same to `309-after.png`, and `python3 tools/generate_flinders_art.py --preview <sheet>.png` for a
   contact sheet (write previews outside the repo). Look at both; the summary says which sprites still
   read as flat.
2. `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
   `python3 tools/check_generators.py` (no DRIFT; `generate_flinders_art` and `generate_flinders` both
   `ok`), `python3 tools/sync_cities.py --check`.
3. Browser regression per `tools/browser/README.md` (`REGRESS_TIME_SCALE=2` in the container); it has a
   Flinders walk-through. Then play it: walk in from San Franbourne, bump the clocks, the board and the
   machines, at desktop and a phone size, day and `?tod=night`, with screenshots to `/work/media/`. If the
   regression cannot run, say so.
4. Commit: `gamev2: <what changed> (#292)`.

## Risks and open questions

- **The exterior's colours.** #322 redraws `sfb-clocks-station` and picks its own pack colours. If its
  mustard or maroon differs from `c6a663` / `904a37`, align the constants here in a follow-up; not blocking.
- **`d7d0ba` (terrazzo base) is rare in the pack** (one Osaka sheet, 140 px). It is the only cream that is
  not pink; if it is judged not "a pack colour", fall back to the stone ramp (`e4cecc`), which makes the
  floor pinker and closer to the pilasters. `e3c587`, `5b283b`, `575c6d` are uncommon but present.
- **Mixed room until #327.** The gates, benches, pillars, planters and track are the station kit, redrawn
  by #327; the after render will show old and new side by side.
- **#334** changes the pub frame's look; the concourse no longer follows it. That is intended, and the
  doc line says so.
- The void tile round the room is near-black (`office-void-autotile`); the walls' outer half is `080d16`,
  slightly bluer. Check the seam in the render; it was not visible in the prototype.
