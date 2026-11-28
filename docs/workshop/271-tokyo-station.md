# 271 — Tokyo Station, Tokyo Tower and Tsutenkaku: the line art, painted

## Context

#70 replaced three white line-art landmarks with shaded placeholders drawn from nothing by code
(`tools/generate_tokyo_art.py`; Tsutenkaku saved from `generate_osaka_art.tsutenkaku()`). The owner: that
was a complete redesign. The placeholder should have used the black-and-white line drawing as its
template, for Tokyo Station and for the other swap-ins too (Tokyo Tower, Tsutenkaku), but not the 7-Eleven
(#89 stays as it is).

Outcome: each of the three sprites is its old line drawing, pixel for pixel, with colour and shading laid
on it: the same outline, the same lines, the same windows. Same keys and sizes; no map, prefab, config or
game-code change. They are still placeholders until the team's art arrives (#70). All paths below are
under `gamev2/` unless they start with `art-source/`.

Checked while designing (pictures in the ticket's media, `271-*.png`: line art, today's art, and a
first-pass paint-over made with the method below):

- The line art is pixel-doubled, so it has a half-size grid like every art tool: station 1312x256,
  tower 256x480, Tsutenkaku 256x416. Three kinds of pixel: clear, black (lines), fill (white, and one
  red accent on each tower).
- The two Tokyo drawings are the team's own Pixaki documents: `art-source/pixaki/Landmarks/Tokyo
  Station.pixaki/images/preview.png` cropped at (32,32) and `Tokyo Tower.pixaki/images/preview.png`
  cropped at (32,0) equal the old sprites exactly. Tsutenkaku's was drawn by the old
  `generate_tsutenkaku.py`.
- With the old PNGs put back, `node tools/test_game.js` fails only "none of them is line art" and the
  ground-line assertion written for #70's art (see Tests). Every other rule that keeps the map honest
  (#63, #259, the tower's feet, the archway) is already met by the line art's own silhouette.

## Approach

**Keep the three line drawings as source art and paint them by rule.** The old PNGs go into
`art-source/line-art/` (not deployed). A small painter, `tools/line_art.py`, turns a template into the
sprite; the two tools only say which part of the drawing is which material. The output's alpha is the
template's alpha exactly, which is both the proof that the drawing is the base and what keeps the map
fitting.

The painter, `paint(template, zone, ...)`, on the half-size template:

1. Classify: clear (alpha 0), **line** (opaque black), **fill** (any other opaque pixel; `accent` when it
   is the template's red).
2. Regions: 4-connected groups of fill pixels (the station has 2845, most of them window panes).
3. Material: `zone(x, y, accent)` names a material for a fill pixel. A region takes the material most of
   its pixels get, so a zone need not trace the drawing's lines and a region is never split.
   `by_region=False` paints per pixel instead (the tower's bands cut across its triangles).
4. Panes: a region of at most `pane` pixels whose material is in `walls` becomes glass; `lit(x, y)`
   (deterministic, no `random`) picks the ones that are lamplit (`WARM`).
5. Fill colour: a material is `(base, hi, lo, line)`. `hi` where the pixel to the left or above is a
   line, `lo` where the pixel to the right or below is one (`lo` wins): light from the top left, as the
   other art. Pane-sized regions are flat.
6. Line colour: `INK` where the line touches clear or the picture's edge (4 neighbours) or separates two
   materials; the window-frame colour (`GLASS_DK`) where it touches a pane (8 neighbours); otherwise the
   `line` shade of the one material round it, so brick courses read as joints and not black bars.
7. Assert the result's alpha equals the template's and return it. The caller doubles it with
   `Image.NEAREST`.

A tool may recolour opaque pixels after `paint` (a cast shadow under an eave, the clock face, a lamp on a
mast). It may not change alpha, and a line pixel stays darker than the fill beside it.

Pure Pillow pixel access, no numpy, no polygon or ellipse drawing in the output path, so every Pillow
draws the same pixels. The prototype painted all three in under a second.

Materials are tuples of the house palette; import the colours (`generate_hokkaido`,
`generate_sapporo_art`, `generate_osaka_art`'s `STEEL*`, the `VERM*` already in `generate_tokyo_art.py`),
do not retype hex values the palette has. Starting set:

| Material | base, hi, lo, line |
|---|---|
| brick | `BRICK`, `BRICK_HI`, `BRICK_LO`, `BRICK_DK` |
| brick in shade (faces turned from the light) | `BRICK_LO`, `BRICK`, `BRICK_DK`, `DARK` |
| stone | `CREAM`, `WHITE`, `CREAM_LO`, `CREAM_DK` |
| slate (and slate in shade, one step down) | `SLATE`, `STONE_LO`, `SLATE_LO`, `GLASS_DK` |
| glass / lit glass | `GLASS` / `WARM`, flat; frame `GLASS_DK` |
| white steel (and in shade) | `SNOW`, `WHITE`, `SNOW_LO`, `STONE_LO` |
| vermilion (and in shade) | `VERM`, `VERM_HI`, `VERM_LO`, `VERM_DK` |
| grey steel (and in shade) | `STEEL`, `STEEL_HI`, `STEEL_LO`, `STEEL_DK` |
| copper green | `GREEN_HI`, a lighter step, `GREEN`, `GREEN_LO` |
| neon red | `RED`, `RED_HI`, `RED_LO`, `RED_DK` |

Zones to start from (half-size px; this is what the media mock used, plus the parts it left out). The
pictures are judged by eye: refine the zones until each reads well beside its neighbours.

**Tokyo Station** (1312x256, mirror-symmetric about x = 655.5: write the west half, mirror it).
- Wings, by height: ridge y <= 76 slate in shade; roof 78..125 slate; cornice 127..136 stone; the two
  upper storeys 139..178 brick; band 181..185 stone; base storey 186..210 brick, its stripes at
  191..193 and 201..202 stone (the granite bands). Panes on brick and stone; about one window in ten lit.
- The mock stopped there. Still to zone: the end turrets (x 0..31), the domed pavilions (about
  x 96..252), the small towers (x 384..425 and the pair by the centre block), the centre block
  (x 589..722) and its porch. For each: domes and caps slate with a copper-green finial, the drums'
  and upper stages' bands stone, faces turned to the right brick in shade, the clock faces cream, the
  doorway under the porch dark with glass.

**Tokyo Tower** (256x480), `by_region=False`, panes up to 8 px on white steel.
- Mast and the two top decks (y < 126) and the main observatory (214..267): white steel, in shade right
  of x = 140; their grid cells become glass by the pane rule.
- Lattice: the real tower's bands, with edges on the drawing's own horizontal members (y = 143, 157,
  173, 190, 207, 280, 313, 346, 379, 413): vermilion for y 126..156, 190..213, 268..312, 346..378 and
  the feet (y >= 414), white between. Left of x = 114 lit; the centre panel (the template's red,
  x 114..142) lit, one step brighter in the vermilion bands; right of it in shade.
- `tokyo-tower-feet` stays the bottom 192 rows of the doubled picture, saved by the same run.

**Tsutenkaku** (256x416), no pane rule (its window cells are larger: zone them).
- Lattice and mast grey steel, in shade from x = 128; corbels (y 97..111, 271..282) steel in shade.
- Roofs (y 44..55, 240..247) copper green; glazed storeys (y 56..96, 248..270) glass, every fourth bay
  lit; the sign (the template's red) neon red.

Alternative considered: reading the two Pixaki previews directly. Not chosen: Tsutenkaku has no Pixaki
document, and three PNGs in one folder give the tools and the test one rule.

## Changes

- **`art-source/line-art/tokyo-station_0_0.png`, `tokyo-tower_0_0.png`, `tsutenkaku_0_0.png`** (new):
  the old sprites, byte for byte:
  `git show 422b40ec:gamev2/assets/sprites/<key>.png > art-source/line-art/<key>.png`
  (2624x512, 512x960, 512x832). No feet file: it is a crop.
- **`art-source/README.md`**: a `line-art/` section: what the three are, the command above, that
  `gamev2/tools/generate_tokyo_art.py` and `generate_tsutenkaku.py` paint them, that the Tokyo two are
  the Pixaki documents' pictures doubled, and that a change to one changes the sprite's outline and so
  must still fit the map. In the `pixaki/` section, "no tool reads them" stays true.
- **`tools/line_art.py`** (new): `template(key)` (opens `../art-source/line-art/<key>.png`, halves it
  with `NEAREST`, asserts only black, white, the accent red and clear occur), `paint()` as above, the
  materials. No side effects on import, no file writes. Docstring: the seven rules.
- **`tools/generate_tokyo_art.py`**: rewritten. The drawn tower and station (and their helpers) go;
  `tower()` and `station()` become zone functions plus `paint(template(...))`. `build()`, `sheet()`,
  `main()`, `--sheet` and the three output keys stay; still no `config.json` write. Docstring: these are
  the team's line drawings painted by rule, placeholders still (#70, #271), and the one hard rule
  (alpha equals the template).
- **`tools/generate_tsutenkaku.py`**: paint `template('tsutenkaku_0_0')` instead of importing
  `tsutenkaku` from `generate_osaka_art`. The registration block stays exactly as it is.
- **`tools/generate_osaka_art.py`**: `tsutenkaku()`'s docstring only: drop the sentence saying
  `generate_tsutenkaku.py` saves this drawing. `osaka-tsutenkaku_0_0` is untouched.
- **`assets/sprites/tokyo-station_0_0.png`, `tokyo-tower_0_0.png`, `tokyo-tower-feet.png`,
  `tsutenkaku_0_0.png`**: regenerated.
- **`tools/tests/landmark-placeholders.test.js`**: see Tests.
- **Docs**: `docs/landmarks-and-towns.md`: the three table rows ("the team's line drawing
  (`art-source/line-art/`) painted by `tools/generate_tokyo_art.py` / `generate_tsutenkaku.py`; the
  team's art is still wanted (#70)"), and in the paragraph under the table replace "nothing below the
  ground line beside the porch" with what is true of the drawing: the forecourt cells of the bottom row
  are clear, and the small towers either side of the centre block come down to the foot of the row
  above. `docs/generators-and-checks.md`: one sentence where the art tools are described: the two tools
  read `../art-source/line-art` through `tools/line_art.py`. `tools/generate_osaka.py` docstring:
  "the line drawing, painted" for "a shaded placeholder".
- **Not changed**: `tools/check_generators.py` (both tools are in `ART_TOOLS`; it already links
  `art-source` beside its scratch copy), `config.json`, `tiled/`, prefabs, `src/`,
  `assets/map/world-map.png` (as in #70: nothing moved and the game does not show it).

## Data and interfaces

None. `git diff --stat` shows only the files above.

## Tests

`tools/tests/landmark-placeholders.test.js` (retitle its header comment for #271):

- **New: each sprite is its line drawing, painted.** For the three keys, decode
  `art-source/line-art/<key>.png` and the sprite: same size, and alpha equal at every pixel. Also the
  lines are still lines: mean luma (0.299 R + 0.587 G + 0.114 B) of the sprite over the template's black
  pixels is at least 30 below its mean over the template's fill pixels (the mock: 56 against 118 for the
  station, 86 against 173 for the tower).
- Keep unchanged: sizes and anchors; the feet are the tower's bottom 192 rows; at least 12 opaque
  colours each; the tower's walked-through cells and Tsutenkaku's archway; the train rows; cells
  (16..18, 7) and (22..24, 7) clear; door cell (20, 7) more than half drawn; the pavilions' feet (#259);
  `check_generators` lists both tools.
- Change: the ground-line assertion. The line art's wing ends 40 px into row 6, not 34, and the small
  towers in columns 17..18 and 22..23 reach the foot of row 6. Assert only columns 16 and 24, from
  `6 * CELL + 40`; update the comment.
- `tools/tests/map-data.test.js` (#259) needs no edit and must still pass.

Run from `gamev2/`, with the pinned Pillow (`pip install -r tools/requirements-art.txt` in a venv):

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
<venv>/bin/python tools/check_generators.py     # the art tools must not be listed as `skip`
python3 tools/sync_cities.py --check
<venv>/bin/python tools/generate_tokyo_art.py --sheet /work/media/271-sheet.png
node tools/play.js render Palace /work/media/271-palace.png   # and Park, Osaka: look at them
REGRESS_TIME_SCALE=2 node tools/browser/regress.js            # tools/browser/README.md
```

Then play it in a browser (`?notitle=1&nointro=1`), desktop and both phone sizes, by day and
`?tod=night`, screenshots looked at: walk between the tower's feet and behind it (it fades, the player
is not lost), through Tsutenkaku's archway (Osaka 25,42), in and out of the station's door (Palace 27,10
going up), wait for a train behind the station's roof, and `?stitch=0` at Park (12,4) for the feet.

## Risks and open questions

- **Looks are a judgement.** The mock is a first pass with crude zones, not the target. The implementer
  looks at the sheet and the renders and refines zones and shades; what may not change is the drawing.
- **The towers are solid again.** The line art fills its lattice, so the see-through steel of #70 goes
  and the towers hide what is behind them, as before #70 (the game fades them over the player). Cutting
  the lattice open would be redrawing, which the ticket rules out.
- **The gardens' top edge is covered again** by the bases of the two small towers beside the centre
  block, as before #70. Trimming the drawing or moving the gardens is not this ticket.
- **Colour choices are mine, not the drawing's**: brick, slate and stone for the station; the real
  tower's vermilion and white bands in place of the drawing's single red panel; grey steel, green roofs
  and a red sign for Tsutenkaku. Cheap to change: they are the zone functions and the materials table.
- **Two Tsutenkaku pictures remain** (`tsutenkaku_0_0` from the line drawing, `osaka-tsutenkaku_0_0`
  from `generate_osaka_art.py`, in no map yet). Osaka's rebuild (#219) decides between them.
- **#70 stays open** for the team's art; say so in the summary.
- Rooms that look different, none of whose data is touched: Palace, Park, Osaka.
- No open question blocks the work.
