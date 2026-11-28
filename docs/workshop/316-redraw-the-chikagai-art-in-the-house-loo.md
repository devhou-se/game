# Design: the underground arcade art in the house look (#316, part 2 of 5 of #292)

## Context

`gamev2/tools/generate_chikagai_art.py` draws 25 sprites: the 24 `chika-*` sprites of the arcade under
Sapporo (room `ChikagaiSapporo`, the only room that places them) and `chikagai-entrance-snow`, the stairs
down from the street (four in room `Sapporo`, at (28,13), (33,23), (52,24), (47,37)). They were drawn before
the house look existed: the station interior's palette (`generate_station_art.py`, none of it GuttyKreum
colours) plus a dozen local ones, an outline in `INK=(38,43,68)`, lit yellow exit signs and step nosings,
lit lamps and a lit orange bar, pale-blue glass (bakery case, capsule globes, siphon, the entrance's
canopy), flat fills, and `ellipse` / `polygon` / `rounded_rectangle` / `arc` shapes.

Outcome: the same 25 keys at the same sizes and anchors, redrawn so the arcade and its entrances read like
the pack: pack colours only, navy outline, dark glass with a slanted glare, nothing lit (signs, nosings and
lamps in the pack's dim gold), ragged foliage for the florist, tiled surfaces with joints and lit edges,
the entrance's canopy as a glass roof seen from above under the pack's snow. No map, config or placement
change. An arcade is not Japanese architecture: the shops stay what they are; only the drawing changes.

A design-stage prototype was drawn and rendered to settle the palette and shapes (images on the ticket:
`316-chikagai-before/-prototype.png`, `316-sprites-before/-prototype.png`,
`316-entrances-before/-prototype.png`). It is not in the repository; the specification below is what it drew.

## Approach

**Rewrite `generate_chikagai_art.py` in place, and make it own every colour it paints.** Keep `sprites()`
(keys, order, how exits come from `chikagai.TOWNS`), `half()`, `main()` (doubling, save, registration,
`--preview`; the preview sheet's background becomes `rgb('5f6177')`) and every sprite's geometry: what each
cell shows, where the fascia, counter, stairwell, sign and steps are. From `generate_station_art` import
only plumbing: `C, new, text, text_size, kana, latin`. Do not import its colours or `box`: none is a pack
colour, and #327 is about to redraw that module; with no shared pixels the two can merge in either order.

**Shared helpers.** #279 is not merged. `from generate_sendai_art import pane, foliage, speck` (importing
it has no side effects); if `origin/master` has #279's shared module when you implement and it exports
them, import from there instead. `roof_tile`, `repaint`, `glaze`, `flat_roof` are not needed (`glaze` keys
on another file's glass colours).

**Drawing rules** (as `generate_seven_eleven_art.py` and `generate_sendai_art.py` do):

- Colours are local constants made by a local `rgb('hex', a=255)`; every one is in the table below. No
  colour computed at run time.
- Rectangles and points only: no `ellipse`, `polygon`, `rounded_rectangle`, `arc` or slanted `line` (they
  move a pixel between Pillow versions). Discs and peaks are drawn a row at a time with integer maths.
- Light from the upper left. An object is closed by a 1 px `EDGE` outline, lit along its top and left,
  shaded along its bottom and right. Something standing proud of a wall (poster, exit sign, notice, map
  board) casts 1 px of shade below and to its right: the next colour down the ramp of what it falls on.
- Glass is `pane()`: bakery case, capsule globes, the entrance's canopy; the till's screen and the siphon's
  globe are `GLASS` with one or two `GLARE` pixels. Nothing is lit.
- Text is 1-bit in the game's fonts as now (`kana()` 12 px, `latin()` 8 px). Lighter than its ground: a
  shadow at (+1,+1) in the ground's dark; darker than its ground: none.
- Scatter uses `random.Random(seed)` as the tool does today, or `speck()`.

**Local helpers** (half-size pixels, inclusive coordinates):

```python
def R(d, x0, y0, x1, y1, fill):                      # a rectangle; nothing if empty
def box(d, x0, y0, x1, y1, base, hi, lo, edge=EDGE): # EDGE ring; base; hi on the top row and left column
                                                     # inside it; lo on the bottom row and right column
def cast(im, x0, y0, x1, y1):                        # shade: each pixel -> DOWN[pixel] if it has one;
                                                     # a transparent pixel -> SHADE. Call before drawing
                                                     # the object that casts it.
def label(d, x, y, s, f, fill, shadow=None)          # text(), with the (+1,+1) shadow first
def centred(d, cx, y, s, f, fill, shadow=None)
def ring(im)                                         # every transparent pixel with an opaque 4-neighbour
                                                     # becomes EDGE (a plain pixel loop)
```

`DOWN` maps each colour to the next one down its ramp, for the white, stone, teal, gold, wood, slate and
steel ramps of the table. `SHADE = rgb('2a3151', 90)` is the only non-opaque colour, used on transparent
pixels under the capsule machines and the map stand.

**Palette** (all in the `art-source/GuttyKreum` sheets; the prototype's output uses 62):

| Role | Colours (light to dark) |
|---|---|
| void, outline | `INK 080d16`, `EDGE 172459` |
| white tile, parapets, slats, steps | `fafcfd`, `dae2e4`, `bcc7cc`, `a4b0b5`, `848295`, `646e86` |
| stone: dado, apron, plan, bakery wall | `e4cecc`, `d7b6ab`, `be9e8c`, `8e7366` |
| slate: ceiling edge, skirting, street steps | `78768a`, `5f6177`, `47485d` |
| steel: frames, rails, posts, legs | `d1e2eb`, `94a2a8`, `575c6d` |
| teal band, florist, map; chalk board | `93c297`, `508582`, `4a6262`, `395050`, `2e4040` |
| gold: exit signs, nosings, lamps, beer | `f3d890`, `c6a663` (base), `a7843b`, `86624f` |
| red: lanterns, curtain, posters | `d16b56`, `aa4d31`, `8a3a22` |
| orange: bakery | `f6a583`, `ce6a42`, `aa4d31`, `904a37` |
| blue: bookshop, street sign, poster sky | `7db9fa`, `588cc6`, `425faa`, `314b8e` |
| wood: kissa, shelves, counters | `be9e8c`, `a68777`, `7c5d56`, `594b45`, `5a3827`; `7f513b` |
| bread, the bar's back wall | `e3c587`, `bb8971`, `86624f` |
| night: the bar's fascia, chutes | `3c3a4c`, `1b1e2a` |
| pink, purple, sage (blooms, spines, machines) | `d78bc1 bb6479 83374f`; `bfabd7 8f72b6 444679`; `93c297 6c8e7f 506b6b`; `83af6f` |
| glass | `GLASS 2c2d51`, `GLASS_LO 2a3151`, `GLARE 4b6396` |
| snow | `fafcfd`, `ecfaff` (base), `b7c3e3` |
| foliage ramp `LEAF` | `b1dfdc 93c297 83af6f 508582 425faa 3c396d` |

## Changes

### `gamev2/tools/generate_chikagai_art.py` (rewritten in place)

Coordinates are half-size pixels (32 a cell), x right, y down, inclusive. "As now" means today's geometry.

**Floor, 1x1** `floor(base, hi, joint, seed)`: four 16 px tiles: `base`; joints at `x % 16 == 15` and
`y % 16 == 15`; each tile's top row (`y % 16 == 0`, not on a joint) `hi`; seven single specks of `joint`
from `random.Random(seed)`, off the joints and top rows. `chika-floor-a` = (`dae2e4`, `fafcfd`, `bcc7cc`,
316), the cool white hall; `chika-floor-b` = (`e4cecc`, `fafcfd`, `d7b6ab`, 317), the stone apron in front
of the shops.

**Back wall** `paint_wall(d, x0, x1)`, 64 rows, the same rows in the walls, the exits and (rows 0-3) the
shops, so they join; joints are placed by the sprite's own x (every width is a multiple of 16):

| Rows | What |
|---|---|
| 0-3 | ceiling edge: `EDGE`, `78768a`, `5f6177`, `47485d` |
| 4-39 | white tile `fafcfd`: rows 4-5 `bcc7cc` and row 6 `dae2e4` (the ceiling's shade); course joints `dae2e4` at rows 16 and 28; upright joints `dae2e4` at `x % 16 == 15` in rows 7-15 and 29-39, at `x % 16 == 7` in rows 17-27 (running bond) |
| 40-45 | the band: `EDGE`, `93c297`, `508582` x2, `4a6262`, `EDGE` |
| 46-57 | dado `e4cecc`: row 46 `be9e8c`, row 57 `d7b6ab`, upright joints `d7b6ab` at `x % 8 == 7` |
| 58-63 | skirting: `EDGE`, `78768a`, `5f6177` x2, `47485d`, `EDGE` |

**`chika-wall`, `-wall-poster-a/-b`, 1x2**: the wall; a poster is a steel frame `box(5, 8, 26, 36)` with an
`EDGE` inner line at (7,10)-(24,34), casting on the wall, picture at (8,11)-(23,33). a (ski season): sky
`588cc6` with `7db9fa` over its top five rows, a white peak stepped a row at a time from (15,14) to row 28
(`ecfaff`, its right flank `b7c3e3`), a red band rows 28-33 with a white line and a dark one, a 3x3 gold
sun. b (a sale): `c6a663` ground, a red disc drawn by rows (half-widths 3,5,6,6,7,7,7,7,6,6,5,3 from row
13) with a `d16b56` glint upper left and `8a3a22` lower-right rim, two dark text bars beneath.

**`chika-side-w/-e`, `-front`, `-front-w/-e`, 1x1** `edge(top, left, right)`: `INK`, with the same 6 px
strips as now (left x0-5, right x26-31, top y0-5). Across a strip: one `EDGE` pixel on its void side; of the
other five the first (left or top) `dae2e4`, the last (right or bottom) `848295`, between them `bcc7cc`.
Corners join as now.

**Shopfronts, 3x2** `shop_frame(fascia, name, ink, shadow, back, back_lo)`: rows 0-3 the wall's ceiling
edge; the fascia `box(0, 4, 95, 21)` in the shop's (base, hi, lo) with rows 19-20 `lo`; the name laid out
as now (kana at y7, latin at y9, 6 px apart, centred on x48); the opening rows 22-63 `back`, with
(4,22)-(91,24) `back_lo` (the fascia's shade); pilasters x0-3 and x92-95, rows 21-63: `EDGE` with a
`fafcfd` and a `bcc7cc` column inside; row 63 `EDGE`. `counter(d, y, base, hi, lo)`: (4,y)-(91,62) `base`,
row y `EDGE`, y+1 `hi`, y+2 `lo`, panel joints `lo` every 12 px from x15 down to row 58, rows 59-62 `lo`.
All six counters at y46 as now.

| Shop | Fascia (base, hi, lo); name | Inside |
|---|---|---|
| bakery | `ce6a42 f6a583 aa4d31`; white, shadow `904a37` | back `d7b6ab`/`be9e8c`. Awning: eleven 8 px stripes rows 22-27, orange and white by turns, each with a scalloped foot in its dark over an `EDGE` row. Two shelves (`7c5d56`, rows 37 and 45) of eight loaves, 8x5: `bb8971`, top `e3c587`, foot and right `86624f`, every third a tin loaf. Counter `a68777`/`be9e8c`/`7c5d56`. The case (8,48)-(60,58): `EDGE` frame, `pane(9, 49, 59, 57, 11)`, five buns seen through it, a steel foot. The till: a steel box, a `GLASS` screen with one `GLARE` pixel, a gold key. |
| kissa | `7f513b a68777 594b45`; `c6a663`, shadow `5a3827` | back `7c5d56`, panel joints `594b45`. Three hanging lamps, not lit: a shade stepped out over four rows in `c6a663` (`f3d890` left pixel, `a7843b` right, `86624f` rim), a 3x2 `f3d890` bulb. A back shelf of white cups and jars. Counter `7f513b`/`a68777`/`594b45`. The siphon: steel stand, a `GLASS` globe with two `GLARE` pixels and coffee `5a3827` in its lower rows. Two cups. The chalk board `2e4040` with three `a4b0b5` lines. |
| bar | `1b1e2a 3c3a4c 080d16`; white, no shadow | a red lantern at each end of the name (7x13: `aa4d31`, left `d16b56`, right and two ribs `8a3a22`, caps `594b45`). Back `bb8971`/`86624f` (warm wood, where the lit orange was). A shelf of bottles (`EDGE`, filled `506b6b`, `7f513b`, `dae2e4`, `a7843b`). The curtain: five red panels rows 23-30, lit top row, dark foot and right edge, a white ring on each. Counter `be9e8c`/`e4cecc`/`8e7366`. Three glasses of beer `c6a663` with a white head; a dish of edamame `83af6f`. |
| books | `425faa 588cc6 314b8e`; white, shadow `EDGE` | back `594b45`. Two shelves of spines 2-3 px wide (red, gold, teal, blue, stone, orange, purple, pale green, wood, pink), boards `a68777` over `5a3827`. Counter `a68777`/`be9e8c`/`7c5d56`. Seven magazines face up: `EDGE` frame, a cover colour, a white title block, a dark line. |
| flowers | `508582 93c297 395050`; white, shadow `2e4040` | back `dae2e4`/`a4b0b5`, a sage pelmet rows 22-24. Two tiers of buckets (six, then seven) each on a wood board: a bucket is galvanised (`a4b0b5`, left pixel and rim `dae2e4`, right `848295`, a pixel narrower in its lower half, `EDGE` outline) under `foliage(im, [(x + 4, y - 8, 6, 5)], LEAF, seed=n)` with six 2x2 blooms of one colour per bucket (red, pink, gold, white, purple, orange; top-left pixel in its light). |
| shutter | `94a2a8 d1e2eb 575c6d`; none | slats rows 23-58 repeating `dae2e4`, `bcc7cc`, `848295`, the top three rows `cast`; a bottom bar `646e86`; the handle; the notice (21,32)-(74,47): `EDGE`, `fafcfd`, `テナント` in `314b8e`, casting on the slats. |

**Exit sign** `paint_sign(im, d, x0, y0, ja, en)`, 112x26, layout as now: `box` in `c6a663`/`f3d890`/
`a7843b`; the `出口` block `EDGE` with `f3d890` characters; the name and the English in `EDGE`. On a wall it
casts first.

**`chika-exit-<slug>`, 4x2** (north): the wall; the well (30,29)-(97,63) `EDGE` with `INK` inside; daylight
(34,30)-(93,32) `fafcfd`; six 5 px steps from row 33, `ecfaff`, `dae2e4`, `bcc7cc`, `a4b0b5`, `848295`,
`646e86` from the top: a `c6a663` nosing row (`f3d890` on the top step), two rows of tread, two of riser in
the next colour down; side walls x31-33 and x94-96 `bcc7cc` with a `dae2e4` outer column; the handrail
x62-65 `EDGE` round `d1e2eb`, `94a2a8`; the sign at (8,2).

**`chika-sign-<slug>`, 4x1** (south): two hangers x22-23 and x104-105, rows 0-5, `575c6d`; the sign at (8,5),
no cast (it hangs over open floor).

**`chika-exit-south-w/-e`**: one 2x1 drawing cut in halves as now: `INK`; four 8 px steps x3-60, `848295`,
`a4b0b5`, `bcc7cc`, `dae2e4` from the top, each with a `c6a663` nosing row and its two bottom rows a tone
down; side walls x0-2 and x61-63 `bcc7cc` with an `EDGE` inner column; the handrail x30-33.

**`chika-gacha`, 2x2**: eight machines 14x29 at x = 1 + 16·col, y = 3 + 30·row, as now: `EDGE` outline, a
white cabinet shaded `bcc7cc` on its right; the globe (x+2,y+2)-(x+11,y+13) `EDGE` with
`pane(x + 3, y + 3, x + 10, y + 12, 7)` and seven 2x2 capsules in its lower rows (`random.Random(5)`); the
front rows y+15 to y+27 in the machine's colour (red, blue, gold, teal, orange, purple, sage, pink: base,
lit top row, dark right and foot); the crank, a 6x6 stepped disc in steel with a dark centre; the chute
`1b1e2a`. Row 62 `EDGE`, row 63 `SHADE`.

**`chika-map`, 1x2**: legs x7-8 and x23-24, rows 44-61, `575c6d`, with `EDGE` feet over two rows of `SHADE`;
the board `box(2, 10, 29, 44)` in steel; a teal header (4,12)-(27,17) with a white title bar; the plan
(4,19)-(27,42) on `e4cecc`: the arcade's cross in `508582`, four exits `c6a663`, you-are-here `aa4d31`.

**`chikagai-entrance-snow`, 2x3** (door cells stay the bottom row, the foot of the steps):

- The mouth (8,44)-(55,66) `INK`. Six 6 px steps x12-51 from row 60, lighter towards you: `47485d`,
  `5f6177`, `78768a`, `848295`, `a4b0b5`, `bcc7cc`; top row of each the next lighter (upper three) or a
  `c6a663` nosing (lower three), bottom row the next darker. The handrail x30-33, rows 50-95.
- Parapets `box(2, 58, 11, 95)` and `box(52, 58, 61, 95)` in `dae2e4`/`fafcfd`/`bcc7cc`, a teal band rows
  59-62, one joint; a snow cap rows 53-58 on each (`ecfaff`, top `fafcfd`, foot and right `b7c3e3`). Posts
  x4-7 and x56-59, rows 42-57, `EDGE` round `94a2a8`, `575c6d`.
- The canopy, seen from above: `EDGE` (1,6)-(62,29); a steel frame lit top and left, dark along its two
  bottom rows; `pane(4, 9, 59, 25, 13)` split by a mullion every 10 px (`94a2a8`, then a `GLASS_LO`
  column).
- Snow lying on all of it but the front edge: per column from row 4 (row 5 at the two end columns) down to a
  ragged foot at row `19 + speck(x // 3, 1, 316) % 4`: `ecfaff`, its top two rows `fafcfd`, its bottom two
  and the columns x ≥ 56 `b7c3e3`; one pixel of shade under the foot (`GLASS_LO` on glass, `575c6d` on
  steel); a few `b7c3e3` specks.
- The sign `box(3, 30, 60, 44)` in `425faa`/`588cc6`/`314b8e`, `地下街` white with an `EDGE` shadow,
  centred at y32. Then `ring(im)`.

Update the module docstring: the house look, the pack's colours, what it imports and why; "yellow exit
sign" becomes "gold", "tan apron" becomes "stone".

### Generated files

- `gamev2/assets/sprites/chika-*_0_0.png` (24) and `chikagai-entrance-snow_0_0.png`: rewritten by
  `python3 tools/generate_chikagai_art.py`.
- `gamev2/config.json`: must come out byte-identical (same keys, sizes, anchors). If `git diff` shows a
  change, something moved: fix the tool, do not commit the diff.
- `gamev2/assets/map/world-map.png`: the entrances are on Sapporo's street, so rerun
  `python3 tools/make_worldmap.py --pil` (the prototype changed it).

### `gamev2/tools/tests/chikagai.test.js`

Add one test (below).

### `gamev2/docs/landmarks-and-towns.md`

In "Underground arcades (chikagai)": "tan apron" → "stone apron", "yellow exit sign" → "gold exit sign",
and one sentence after the three files are named: the art is drawn in the house look, in the pack's colours
only, owning its palette (it takes only the canvas and text helpers from `generate_station_art.py`, and
`pane`, `foliage` from `generate_sendai_art.py`).

## Data and interfaces

None. Sprite keys, sizes, anchors (`32 / width`, `32 / height`), `tileNames`, `chikagai.ENTRANCE` and its
door cells, `Interactions.RULES` patterns, the rooms and `tiled/*.tmj` are untouched.

## Tests

New test in `tools/tests/chikagai.test.js`, modelled on the 7-Eleven one (`konbini.test.js`, `require('./png')`):
"the arcade's art is in the pack's colours at the sizes the maps place it by (#316)".

- The keys in `spriteMetadata` matching `/^(chika-|chikagai-entrance-snow)/` are exactly the 25 expected
  (listed in the test: the fifteen fixed ones, the six shops, `chika-exit-sapporo-station`, `-odori-park`,
  `-tv-tower` and `chika-sign-tanukikoji`); each
  PNG's size is its footprint (1x1 64x64; walls and map 64x128; gacha 128x128; shops 192x128; north exits
  256x128; south sign 256x64; entrance 128x192) and its metadata is `frameCount 1`, `anchorX 32 / width`,
  `anchorY 32 / height`.
- Every pixel is transparent, or opaque in a colour of the palette table (the test holds the hex set), or
  `2a3151` at alpha 90; the last only in `chika-gacha` and `chika-map`. The floors, walls, wall tops, shops and
  every `chika-exit-*` have no transparent pixel.
- Glass is dark and nothing is lit: `2c2d51` is present in `chika-shop-bakery`, `chika-gacha` and
  `chikagai-entrance-snow`; `c6a663` covers more than a quarter of `chika-sign-tanukikoji`.
- The wall joins: pixel column 0 of every `chika-exit-<slug>` equals column 0 of `chika-wall`, and rows 0-7
  of column 0 of every shop equal the wall's.

Run, from `gamev2/`: the five checks (`node tools/test_game.js`; `python3 tools/test_blog_to_npc.py`;
`node tools/play.js check`; `python3 tools/check_generators.py`, no DRIFT for `generate_chikagai_art` and no
stale world map; `python3 tools/sync_cities.py --check`), then the browser regression
(`tools/browser/README.md`; nothing in it names these sprites).

Look at it: `node tools/play.js render ChikagaiSapporo out.png` and `render Sapporo out.png` before and
after, saved to `/work/media/`, and `--preview` for the sheet; in a browser walk down an entrance in Sapporo,
along the hall and up another exit, at desktop and phone size. The summary says which sprites still read as
flat (in the prototype: the shutter's slats and the plain wall are the quietest).

Commit: `gamev2: … (#292)`, as the ticket asks. No rooms or map data are touched.

## Risks and open questions

- **A mixed room until the station kit is redrawn.** The arcade also places `station-pillar` and
  `station-lockers` (`generate_station_art.py`, #327) and the bench, planters and tactile paving
  `extract_station.py` cuts; they keep their old colours beside the new walls. Not this ticket's to change.
- **`world-map.png` conflicts** with any other open change to Sapporo's picture (#302 at least). Whoever
  merges second reruns `make_worldmap.py --pil`.
- **Borrowed helpers.** `pane`, `foliage` and `speck` live in `generate_sendai_art.py`; a later change to
  their output would show as DRIFT here in `check_generators.py`, which is the wanted alarm.
- **Outline colour.** #279's unmerged recipe names `0a1627` for outlines; the ticket and master's worked
  examples use navy `172459`, which this follows. A one-constant change if #279 lands differently.
- **Neighbours.** The entrance's snow is the pack's (`ecfaff`), next to Sapporo snow still in the old
  Hokkaido palette until those tickets land; the walls' void is `080d16` beside the room's void tile
  (`0c0c11`), a difference not visible in the prototype render.
- No open question blocks the work.
