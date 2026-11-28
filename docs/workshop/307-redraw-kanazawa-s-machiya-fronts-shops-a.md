# 307 — Redraw Kanazawa's machiya fronts, shops and lit windows in the house look

Part 2 of 3 of #290. All paths are under `gamev2/`; commands run from `gamev2/`. Coordinates are the tool's
half-size pixels (32 a cell), y from the top.

## Context

`tools/generate_kanazawa_art.py` draws Kanazawa's own art (#219). Ten of its building fronts are still in the
old look: 17 to 49 colours each that no GuttyKreum sheet has, front elevations (trapezoid roofs with end caps,
a parapet line, the samurai house's plastered gable as a polygon), windows and paper doors filled with lit
yellow (`f6dc8c`, `f2c66a`, `f9c22e`), and curves drawn with `ellipse` / `arc` / `pieslice` / `polygon`.

In scope (keys, sizes in cells, door cell — none of which change):

| key | builder | size | door |
|---|---|---|---|
| `chaya-front-a/-b/-c_0_0` | `chaya(v)` | 3x4 | [1,3] |
| `chaya-gold-leaf-shop_0_0` | `gold_shop` | 4x4 | [1,3] |
| `chaya-phono-museum_0_0` | `phono_museum` | 3x4 | [1,3] |
| `katamachi-whisky-bar_0_0` | `whisky_bar` | 3x5 | [1,4] |
| `katamachi-izakaya_0_0` | `izakaya` | 4x4 | [1,3] |
| `katamachi-kissaten_0_0` | `kissaten` | 3x4 | [1,3] |
| `katamachi-yakitori_0_0` | `yakitori` | 3x3 | [1,2] |
| `nagamachi-samurai-house_0_0` | `samurai_house` | 5x4 | [2,3] |

Out of scope, and their PNGs must come out pixel-identical: `nagamachi-wall`, `nagamachi-wall-bare` (#300) and
every other sprite of the tool (#312); `kanazawa-whisky-bar` (#304).

Outcome: the ten are redrawn — shape and shading, not a recolour — to sit beside the pack's machiya and the
sprites already done (`kanazawa-chaya-a/-b` from `generate_hokuriku_art.py`, `sendai-pub`, `seven-eleven`,
the yatai), by the recipe in `docs/generators-and-checks.md` "House look: GuttyKreum".

Three facts found while exploring that change what "done" can mean here:

- **None of the ten is registered or placed.** No key of this tool is in `config.json`, `tiled/` or `src/`
  (the tool only writes PNGs; the map change of #219 registers them through `tools/art_register.py`). So no
  room render, world map or in-game `?tod=night` view changes, and the game does not even load the files.
  The tool's own `--scenes` (day and `_night.png`) and a contact sheet are the pictures to look at.
- **`check_generators.py` does not run this tool** (it is not in `ART_TOOLS`), so nothing guards its PNGs
  today. With Pillow 11.3.0 it currently rebuilds every committed PNG exactly.
- **`2b373c` is in no sheet**, yet `generate_fukuoka_art.flat_roof` (`P_SLATE_LO`) and
  `generate_sendai_art.P_ROOF_LO` / `P_JOIN_LO` paint it. Do not import those three.

## Approach

Rewrite the eight builders in place, each from scratch on its existing canvas, in two families. Layout bands
and door columns stay where they are so the sprites still tile and the doors still line up.

**Machiya family** (`chaya` a/b/c, `gold_shop`, `izakaya`, `yakitori`, `samurai_house`) follows the done
model, `generate_hokuriku_art.chaya`: roofs are the pack's kawara in straight courses, drawn as full-width
bands with `kawara()` (ridge course on top, dark eave, `172459` at both ends) — the main roof and the pent
roof — never the trapezoid `roof()`. Under each eave one row of the wall's darkest tone. Walls are the pack's
bengara browns in boards or courses; openings are `bars()` lattice over dark `2c2d51`, reed blinds, or
`pane()`; doors are dark lattice leaves.

**Flat-roofed shops** (`phono_museum`, `whisky_bar`, `kissaten`) follow `seven-eleven` and `sendai-pub`: the
top of the sprite is the roof seen from above — slate panels inside a steel coping, with what stands on it
seen from above — and the front starts under it. The roof takes the rows above the solid rows that the old
parapet, sky and tall upper wall took (about y 2–34 on the 3x4 shops, y 2–44 on the 3x5 bar).

Rules for every one of the ten (the recipe, plus the ticket's):

- **Colours**: only sheet colours, at most 24 a sprite, none over half of it; all pixels alpha 0 or 255.
  Take them from `house_look.RAMPS` / `material()` and the model's verified set: ink `0a1627`; edge `172459`;
  kawara = `roof_tile()` tones + ridge `434857`/`53596d` + eave `191c2a`; bengara `71412a` hi `aa775f` lo
  `5a3827` line `3f210f`; glass `2c2d51` head `2a3151` glare `4b6396`; reed / earth `be9e8c`/`aa775f`/`8e7366`;
  paper `e4cecc`/`fafcfd`; red `aa4d31`/`d16b56`/`8a3a22`; stone and steel `848295`/`53596d`/`a4b0b5`/`dae2e4`;
  slate `5b6c79`/`698592`/`444f5e` with **`2e4040`** as its dark; coping `94a2a8`/`d1e2eb`; lamp `c6a663`
  core `f3d890`; gold leaf = the gold ramp `86624f`/`a7843b`/`c6a663`/`f3d890`. None of the file's old
  constants (`WARM`, `LIT`, `KAWARA_P`, `KIM*`, `LEAF*`, `DBRICK*`, `WHITE` `ffffff`, …) in these builders.
- **Windows**: `pane()` — dark glass, a slanted glare, a shaded head. What a shop shows (bottles, bowls, a
  gramophone, wax samples) is a few pixels of pack colour against the dark glass, as the 7-Eleven's shelves
  are. No window, door or paper is filled with a gold or yellow.
- **Lamps and lanterns**: a paper lantern is cream or red paper (as the yatai's) with its bands in `c6a663`;
  a lamp is `c6a663` with at most a 1–2px `f3d890` core. A painted sign board that was `AMBER` is unlit:
  ground `c6a663` in scanlines with `a7843b`, lettering in `3f210f`.
- **Outline**: `outline(im)` (ink `0a1627`). A sprite drawn to its canvas edge ends in an ink or `172459`
  column there, as the model does. Inside, a line takes the darkest tone of the family it crosses.
- **Light** from the upper left; no face one colour edge to edge (`house_look.scanlines` / `shade` /
  `bevel`, or courses and boards).
- **Primitives**: `rectangle`, `point`, axis-aligned `line`, pixel access. No `polygon`, `ellipse`, `arc`,
  `pieslice`, `chord`, sloped `line`, and not this file's alpha-blending `shade()`. Round things (lanterns,
  the roundel, arched window heads, the cask, the awning's scallops) are stepped rows of rectangles or a
  `house_look.pixmap`.
- **Sign text** stays in the tool's hand-set 5x7 `text()` / `kana()` glyphs (rectangles; the boards are 8 to
  12px tall, too low for PixelMplus12), lighter than its ground with a (+1,+1) shadow in the ground's line
  tone, or darker with none. Same words: HAKU, PHONO, MALT BAR, SAKE, COFFEE, nomihodai, yakitori.

What each becomes (motifs kept; when 24 colours or the rows run out, drop from the end of a line):

| sprite | redraw |
|---|---|
| `chaya-front-a` | kawara main roof from its ridge row (a 9, b 13, c 7: three heights still) to y 34, pent kawara y 69–78; bengara `71412a`; upper floor all lattice with two reed blinds and the rail; indigo noren (`172459`/`314b8e`, cream mark) over dark lattice doors; lattice bays; white paper lantern |
| `chaya-front-b` | walls a tone darker (`5a3827` base); three lattice windows, all dark; green noren (`506b6b`/`6c8e7f`); red lantern on a bracket; name board; stone step |
| `chaya-front-c` | walls in the red ramp (`8a3a22`/`aa4d31`); two wide `pane` windows between shutter boxes (no guests' shadows); persimmon noren (`ce6a42`/`aa4d31`); boarded bay with a small `pane` and the bench under red cloth |
| `chaya-gold-leaf-shop` | kawara roofs; upper wall of leaf squares in the gold ramp (joints `a7843b`, far side `86624f`, a `f3d890` pixel on some squares' lit corner) round the HAKU board (`191c2a`, letters `c6a663`); ground floor black lacquer (`191c2a`/`2a2636`/`2c2d51`); two `pane` windows (a gilded screen; bowls and boxes); cream noren with one gold square; the gold cone sign |
| `chaya-phono-museum` | roof from above with a skylight (a `pane` in a steel frame); stone front in courses (`848295`/`a4b0b5`/`575f79`) under a cornice lip with its shadow row; the roundel (stepped) with the horn gramophone in the gold ramp; PHONO board; slit `pane`s; ground floor: a `pane` with a gramophone and records, glass doors drawn here (not sapporo's `glass_door`), the record poster |
| `katamachi-whisky-bar` | roof from above with the water tank and flue seen from above, each with a shadow; brick in `71412a`/`5a3827`, joints `3f210f`; MALT BAR board with the tumbler; two `pane` windows with stepped arched heads and bottle silhouettes; the bracket lamp in `c6a663`; canopy in the green ramp; timber door, bottle `pane`, cask, chalk board |
| `katamachi-izakaya` | kawara roofs; the nomihodai board unlit (above) with the mug and a red SAKE tab; small `pane`s; a row of red and cream lanterns under the eave; red noren over dark doors; a `pane` with paper menu strips, a `pane` with heads as `2a3151` shapes; crates |
| `katamachi-kissaten` | roof from above with the flue; cream stucco (`e4cecc`/`be9e8c`); COFFEE board; three `pane`s each with a strip of coloured top lights (`aa4d31`, `506b6b`, `314b8e`); green and cream scalloped awning with its shadow row; brown tile courses; a `pane` with siphons and the lace half-curtain, a timber door with a clipped-corner `pane`, a `pane` sample case |
| `katamachi-yakitori` | steel flue (no smoke); kawara roof; the great red lantern (red ramp, `c6a663` bands, kana in cream); indigo noren with skewers over dark doors; the grill window as a dark opening with the cook as a `2a3151` shape, skewers, and three or four coal pixels in `ce6a42`/`aa4d31`; crate |
| `nagamachi-samurai-house` | no gable elevation: a deep kawara main roof (about y 6–40), under it a low plastered upper storey (`e4cecc`, lit top row `fafcfd`, `be9e8c` below) squared by dark posts and one tie — the gable's motif kept as a band — then the pent kawara, earthen walls (`be9e8c`/`8e7366`) over boards on river stones (`848295`/`53596d`/`a4b0b5`, drawn here, not `cobbles()`), unlit paper shoji on the veranda, a barred dark window, dark lattice doors in the middle cell up a stone step |

**Night.** The `lit` lists in `PIECES` are glow spots for the engine (`Glows.js`), added at night only; they
are not sprite pixels, so their colours stay. Keep a spot wherever its window or lantern still is, move its
`x`/`y` to the redrawn opening's centre, and delete a spot whose thing is gone. Check them in the
`_night.png` scenes.

Alternatives not taken: `repaint()` with a colour swap (the ticket rules out a recolour; the elevations and
lit windows would remain); importing `flat_roof` (paints `2b373c`).

## Changes

- **`tools/generate_kanazawa_art.py`**
  - Imports: `import house_look as hl`; `roof_tile`, `pane` from `generate_sendai_art`; `kawara`, `bars` from
    `generate_hokuriku_art` (the done model's own; importing it draws nothing and makes no cycle).
  - A block "the house look (#290)" above `chaya`: the palette above as constants, and local helpers used
    only by the ten — `roof_plan(im, x0, y0, x1, y1)` (`flat_roof`'s pattern with `2e4040` for its dark), a
    lantern, a noren, lattice doors, a brick / course fill, as needed. In-scope-only helpers may be
    rewritten or removed: `kimusuko`, `sudare`, `noren`, `sliding_doors`, `dbrick`, `gold_cone`, `sparkle`,
    `gramophone`, `tumbler`, `bottle`, `mug`.
  - **Do not change** anything an out-of-scope sprite or another tool uses: `text`, `kana`, `text_w`, `h3`,
    `shade`, `curve_rows`, `roof`, `night`, `FONT`, `KANA` (imported by `generate_osaka_art`,
    `generate_sendai_town_art`, `generate_fukuoka_town_art`), `barred`, `cobbles`, `paper_lantern`,
    `stonework`, `namako`; nor `wall`, `_naga_*`, `komo_mats` (#300's).
  - Rewrite `chaya`, `gold_shop`, `phono_museum`, `whisky_bar`, `izakaya`, `kissaten`, `yakitori`,
    `samurai_house` as above. Same names, same `canvas(w, h)` sizes.
  - `PIECES`: for the ten, keep key, size, district, `door`, `solid`; update `lit` (above) and the
    description to what is drawn (no "lit", "lamplit", "guests' shadows", "great white-plastered gable").
    Module docstring lines for the ten likewise, and "imports … generate_hokuriku_art, house_look".
- **`assets/sprites/`**: the ten PNGs, rewritten by `python3 tools/generate_kanazawa_art.py`. No other file
  under `assets/` may change.
- **`tools/tests/kanazawa-art.test.js`** (new; if #300 has landed a file of that name, add to it) — see Tests.
- **`docs/generators-and-checks.md`**: one sentence at the end of "House look: GuttyKreum" — the ten Kanazawa
  fronts are drawn by it and held to it by `tools/tests/kanazawa-art.test.js`.

Not changed: `config.json`, `tiled/`, `devhouse.world`, `assets/map`, `src/`, `check_generators.py`. No rooms
are touched.

## Data and interfaces

None. Keys, file names, sizes, anchors (derived from size), door and solid cells are unchanged. The
`--manifest` JSON keeps its shape; only the ten sprites' `glow` positions and descriptions in it change.

## Tests

New `tools/tests/kanazawa-art.test.js`, modelled on `house-look.test.js` (same sheet-colour walk over
`../art-source/GuttyKreum`, skipping `preview*`; `tools/png.js` to decode), over the ten keys:

1. each file is `cells x 64` in size and every pixel is a 2x2 block, alpha 0 or 255;
2. every colour is a sheet colour; at most 24; none covers half the opaque pixels;
3. every silhouette pixel (opaque with a clear or out-of-canvas 4-neighbour) above the bottom eight rows
   of the file is `0a1627` or `172459` (those rows are the stone foot, which runs to the canvas edge in its
   own tones, as on the model);
4. `f3d890` covers under 3% of the opaque pixels (a lamp's core, not a lit window), except on
   `chaya-gold-leaf-shop` (its wall is leaf);
5. the source of the eight builders (each from its `def` to the next top-level `def`) contains none of
   `.polygon(`, `.ellipse(`, `.arc(`, `.pieslice(`, `.chord(`;
6. with Pillow (else return, as `house-look.test.js` does): a spawned `python3` imports
   `generate_kanazawa_art`, calls `SPRITES[key]()` for the ten, doubles each and finds the committed PNG's
   pixels — the guard this tool lacks while it is outside `ART_TOOLS`.

Implementer's checks, in order:

```bash
cp -r assets/sprites /tmp/sprites-before
python3 tools/generate_kanazawa_art.py --sheet /tmp/kz/sheet.png --scenes /tmp/kz/scenes
git status --short assets/        # exactly the ten PNGs
python3 tools/house_look.py --sheet /work/media/307-after.png --scale 2 <the ten> \
    assets/sprites/kanazawa-chaya-a_0_0.png assets/sprites/machiya-black_0_0.png assets/sprites/seven-eleven_0_0.png
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
    && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

Look at the contact sheet, and at `/tmp/kz/scenes/kanazawa_art_{chaya,katamachi,nagamachi}.png` and their
`_night.png`, before and after (the befores are in the ticket's media); copy the afters to `/work/media/`.
Run the tool twice and compare (deterministic). Confirm `grep -c` finds none of the ten keys in `config.json`
and `tiled/`, then say in the summary that no room places them, so there is no `play.js render` difference,
no world-map rebuild (`check_generators.py` shows `make_worldmap` ok) and no in-game `?tod=night` view; run
`tools/browser/regress.js` once to show nothing else moved, or say it was not run. Name any sprite that
still reads flat. Commit as `gamev2: … (#290)`.

## Risks and open questions

- **Same file as #300 and #312.** Rebase before committing; touch only the eight builders, their in-scope-only
  helpers, their `PIECES` rows and docstring lines. If #300 changed a shared helper, keep theirs.
- **24 colours is tight** for the izakaya, kissaten and whisky bar (they have 29 to 51 today;
  `kanazawa-chaya-a/-b` have 20 and 18, `sendai-pub` 24). Kawara, walls, glass, stone and ink take about 17; spend the rest on one sign and
  one accent, and drop motifs rather than raise the bound.
- **`kawara` / `bars` are Hokuriku's.** If #304 changes them, test 6 fails there and the ten PNGs must be
  regenerated with it; that is intended (the fronts stay one family), but it is a coupling.
- **The samurai house loses its gable front**, the one shape that said "Kanazawa". The plastered storey keeps
  the posts-and-ties motif; if the owner wants the gable back it has to be as a roof seen from above, not an
  elevation.
- **Night is only previewed.** The spots are checked in Pillow's `_night.png`, not the game, until the map
  change places these sprites; that change should also add the tool to `ART_TOOLS` (the other 50-odd
  sprites still use curves, so that waits for #312).
