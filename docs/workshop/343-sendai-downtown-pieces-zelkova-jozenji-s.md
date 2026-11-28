# Design: Sendai's downtown pieces redrawn in the house look (#343)

Part 1 of 3 of #339 (parent #288). Rooms touched: none.

## Context

`gamev2/tools/generate_sendai_town_art.py` (#219) draws 48 sprites and six ground families "ahead of
Sendai's rebuild". Seven of them are this ticket's: `sendai-zelkova-a_0_0`, `sendai-zelkova-b_0_0`,
`sendai-jozenji-statue_0_0`, `sendai-gyutan_0_0`, `sendai-zunda_0_0`, `sendai-izakaya_0_0`,
`sendai-midrise_0_0`. They are in the older Sapporo-kit style and must be redrawn in the house look
(`gamev2/docs/generators-and-checks.md`, "House look: GuttyKreum"; helpers in `tools/house_look.py`), with
keys, sizes, anchors, doors, solid cells and glow data unchanged.

The committed sprites today (PNG pixels; 516 colours are in the sheets under `art-source/GuttyKreum`):

| key | PNG | colours | not in a sheet | half-clear pixels | what breaks the recipe |
|---|---|---|---|---|---|
| zelkova-a / -b | 192x256 | 13 / 13 | 12 / 12 | 2232 / 1624 | flat `blob` pads, `d.line` limbs, soft shadow |
| jozenji-statue | 128x192 | 14 | 12 | 392 | polygon, ellipse, arc, line; soft shadow |
| gyutan | 256x256 | 52 | 40 | 552 | lit `f6dc8c` hood and shoji, smoke in alpha |
| zunda | 192x192 | 23 | 18 | 0 | lit `f6dc8c` window, white `ffffff` |
| izakaya | 192x256 | 37 | 28 | 0 | `f6dc8c` is its commonest colour; front-elevation `roof()` |
| midrise | 256x384 | 31 | 23 | 0 | lit windows, `f9c22e` door band, no roof |

Found while designing:

- **None of the seven is registered or placed.** No key is in `config.json`, `tiled/*.tmj`, a room
  generator, `make_prefabs.py` or `src/`. So no room, world map, `play.js` render or in-game `?tod=night`
  view shows them, and the browser regression cannot see them. The ticket's "rooms rendered before and
  after, by day and at night" is met with the tool's own previews: `--scenes DIR` writes
  `sendai_art_downtown.png` and `sendai_art_downtown_night.png` (all seven, the night one through
  `night()` and the pieces' glow spots), and `--sheet`.
- The tool is not in `check_generators.ART_TOOLS`, and `main()` saves all 102 PNGs on every run. On
  master a run changes no pixel but re-encodes every file, so the other 95 must be put back with
  `git checkout --` before committing.
- The #279 helpers are merged (`tools/house_look.py`), so they are used; `foliage`, `roof_tile`, `pane`,
  `ground_shade`, `speck` come from `generate_sendai_art.py`. `glaze`/`flat_roof` of
  `generate_fukuoka_art.py` are **not** used: `flat_roof` paints `2b373c`, which is in no sheet (#375, #378).
- The manifest is not a committed file (`--manifest out.json` writes it from `PIECES`). Each row's prose
  description goes into it, so `PIECES` is not edited at all and the redraw keeps everything a
  description names.
- A prototype (recipe below, scratch code not committed) drew both trees in 12 colours and the izakaya in
  25: the recipe reads as the pack beside `sendai-maple` and `katamachi-izakaya`.

## Approach

Rewrite the six builders in place (`zelkova`, `jozenji_statue`, `gyutan`, `zunda`, `izakaya`, `midrise`),
same canvases, same layout bands, so every door cell and glow spot still lands on what it lit. Rules for
all seven (coordinates are the sprite's own 32px-per-cell pixels, before doubling; boxes inclusive):

1. **Colours**: only the ones listed under "Palette". At most 16 on a tree or the statue, 24 on a
   building; none on half the opaque pixels. Never `2b373c`, `f6dc8c`, `f2c66a`, `f9c22e`, `ffffff`, `000000`.
2. **Drawing**: `hl.fill`, `hl.scanlines`, `hl.shade`, `hl.bevel`, `d.rectangle`, `d.point`, pixel access,
   `hl.text`. No `polygon`, `ellipse`, `arc`, `line`, `blob`, `roof`, `puff`, `grounded`.
3. **Edge**: `hl.outline(im)` last (ink `0a1627`). Light from the upper left: west columns and top rows
   lit, east columns and bottom rows dark.
4. **Alpha** is 0 or 255, except the ground shade under the two trees and the statue: `ground_shade`
   (`2a3151` at alpha 90, as `maple()` has), drawn on a fresh canvas onto which the outlined sprite is
   `alpha_composite`d, so the shade has no ink edge. No shade under the buildings; the flue's smoke is opaque.
5. **Roofs are seen from above**: kawara (`roof_tile`) on gyutan and izakaya, a flat slate roof inside a
   steel coping on zunda and midrise. **Windows** are `pane` (dark glass `2c2d51`, head `2a3151`, slanted
   glare `4b6396`), nothing lit. **Lamps, gilt and lettering in gold** are `c6a663` (shade `a7843b`).
6. **No flat face**: a wall is boards, courses or tile joints; a plain panel is `hl.shade`.
7. **Text** is `hl.text` (PixelMplus12, 12px). Where today's lettering is double size, set the glyphs one
   by one at a wider pitch instead of scaling. The words stay: 牛タン, 牛, ZUNDA, サケ, AOBA (generic).
8. `PIECES`, `SPRITES`, `scenes()`, `sheet()`, `manifest()`, `main()`, the old palette constants and every
   helper another builder or `generate_fukuoka_town_art.py` uses (`bar`, `glyph`, `puff`, `grounded`,
   `family`, `ashlar`, `shoji`, `coals`, `text`, `kana`, …) are left exactly as they are.

### Palette (a `D_` block above the downtown builders; all checked against the sheets)

| role | colours |
|---|---|
| ink, shade | `0a1627`; `2a3151` at alpha 90 |
| keyaki gold (ramp, lit to dark) | `f3d890 f3d890 c6a663 c6a663 c6a663 a7843b a7843b 93c297 508582 425faa 3c396d` |
| keyaki russet (ramp) | `f6a583 f6a583 ce6a42 ce6a42 ce6a42 aa4d31 aa4d31 6c8e7f 508582 314b8e 3c396d` |
| keyaki bark, granite, steel, step | base `848295`, lit `a4b0b5`, brightest `dae2e4`, dark `575f79` |
| bronze, wood | base `7f513b`, lit `a68777`, dark `594b45` |
| kawara | `roof_tile`'s `0a1627 172459 434857 2e4040 395050` |
| slate roof | `5b6c79`, lit row `698592`, joints `444f5e` |
| charred cedar, dark interior | base `2a2636`, lit `47485d`, dark `191c2a` |
| glass | `2c2d51`, `2a3151`, `4b6396` |
| paper, pale tile, white | `e4cecc`, lit `fafcfd`, joint `d7b6ab`, shade `be9e8c` |
| red (tab, lantern, banner, noren) | `aa4d31`, lit `d16b56`, dark `8a3a22` |
| gold (lamp, gilt, crates) | `c6a663`, dark `a7843b`; `f3d890` only as a lit top row, under 3% of a building |
| indigo | `314b8e`, lit `425faa`, dark `172459` |
| sage and canopy green | `b1dfdc 93c297 6c8e7f 508582`; dark `395050`, `2e4040`, lit `506b6b` |
| skin, coals | `f6a583`; `ce6a42` |

### The seven

| sprite | canvas | drawing |
|---|---|---|
| zelkova-a | `canvas(3, 4)`, trunk at x 48, foot at y 122 | Trunk 9 wide y86-122 with a root flare (half-widths 8,7,7,6,6,5,5,5 up from y122), five boughs through today's points (widths 5,5,5,5,4), all by a new `bough(d, pts, w, base, hi, lo)`: one rectangle a row, lit west pixel, dark east pixel. Then `foliage(im, clumps, D_KEYAKI_GOLD, 3)` with clumps `(20,62,11,8) (76,64,11,8) (32,56,12,8) (64,57,12,8) (14,51,13,11) (82,53,13,11) (48,46,16,11) (26,36,17,13) (70,36,17,13) (48,25,21,14) (34,16,15,10) (62,15,15,10) (48,10,13,8)`. Outline. Shade `ground_shade(d, 48, 119, 30)`. Fallen leaves: single opaque pixels of `c6a663`/`a7843b` on shade pixels of rows 120-123 with `abs(x - 48) <= 25` where `speck(x, y, 5) < 9`. |
| zelkova-b | `canvas(3, 4)` directly (no 2-cell canvas pasted in), trunk at x 48 | Trunk 7 wide y80-122 (flare 6,5,5,4,4,4,4), boughs `(47,84)(38,58)(32,40)`, `(48,82)(46,50)(44,24)`, `(49,84)(58,56)(64,36)` at width 4. `foliage(…, D_KEYAKI_RUSSET, 11)` with `(34,58,9,7) (62,58,9,7) (48,45,12,9) (30,46,12,10) (66,44,12,10) (40,30,14,11) (58,28,14,11) (48,17,15,11) (48,9,11,7)`. Shade `(48, 119, 22)`, leaves in `ce6a42`/`aa4d31` with `abs(x - 48) <= 17`. |
| jozenji-statue | `canvas(2, 3)` | Granite as today: block (13,68-50,89) in courses 11 high and stones 19 wide, staggered (`a4b0b5`, joints `848295`, lit west column `dae2e4`, east four columns `848295`); cap (11,64-52,67) `dae2e4` over a `848295` row; foot (10,90-53,92); plate (24,75-39,82) `594b45` with one `c6a663` and one `a7843b` row. The dancer in today's pose and points (base plate, two legs, swung skirt, torso, left arm up, right arm out with the bird, head with a knot): limbs by `bough` in bronze, skirt and head as row spans; verdigris specks `508582`, the bird's eye `c6a663`. Outline. Shade rows y90-95 across x6-58 (`ground_shade(d, 32, 90, 26)`). |
| gyutan | `canvas(4, 4)` | y4-27 kawara over x2-125 with a ridge cap y4-6 (`434857`, top row `395050`) and an ink eave row. y28-71 charred-cedar boards 6 wide (`2a2636`, lit column `47485d`, dark column and two eave-shadow rows `191c2a`). Name board (20,32-83,62): face `191c2a`, frame `c6a663`, inner frame `a7843b`, 牛 タ ン one glyph each at x 28, 46, 64, y 41, in `c6a663`. Red tab (90,34-99,60) with three `e4cecc` squares. Steel flue x104-111, y10-76, banded, capped; an opaque stepped puff of `dae2e4`/`a4b0b5` above it within y1-9. Pent y72-83: two kawara courses x1-126, a `c6a663` pixel every 5 px on its last row, ink eave. Ground floor y84-122 on `191c2a`, posts at x 6, 62, 92, 118. Cells 0-1, grill window (10,88-61,116), open: hood lamp rows y88-90 `c6a663`, the cook in `fafcfd`/`dae2e4` with a `f6a583` face, mesh row `848295`, slices `d16b56`, coal bed (12,110-59,115) `191c2a` with `aa4d31`/`ce6a42` pieces by `speck`. Cell 2, door (66,88-91,122): two `e4cecc` paper leaves with `594b45` lattice under a `8a3a22` noren (lit columns `aa4d31`) with 牛 in `e4cecc`. Cell 3: red lantern at (98,88), menu (110,92-117,108) `e4cecc` with `be9e8c` lines, sacks `be9e8c`/`594b45`. Step y122-126. |
| zunda | `canvas(3, 3)` | y2-15 slate roof x3-92 with a green vent box (62,4-76,11). Wall to y90 in sage `93c297`, lit `b1dfdc`, a `6c8e7f` course row every 8, east columns `6c8e7f`. Board (8,18-87,35): `e4cecc`, top row `fafcfd`, frame `508582`; Z U N D A one glyph each, 10 px apart from x 30, y 22, in `395050`; two pods (the `edamame` shape) at its west end. Awning y38-46: 6 px stripes `6c8e7f`/`fafcfd`, their lowest two rows `508582`/`e4cecc`, scallops on row 46. Cells 0-1, window (9,50-55,84): `fafcfd` frame, `pane` (10,51-54,73), in front of it the clerk (`508582` cap, `f6a583` face, `93c297` apron), two shakes, the counter (10,74-54,83) `e4cecc` with three plates of mochi (`93c297` on `fafcfd`). Cell 2, door (62,50-85,90): `fafcfd` frame and mullion at x73, `pane` (63,61-84,89), noren (63,51-84,60) `508582` with slits `395050` and a `b1dfdc` pod. Riser (5,84-61,90). Step y90-94. |
| izakaya | `canvas(3, 4)` | y3-26 kawara x2-93 (ridge cap y3-5, ink eave row 26). y27-66 weathered boards 7 wide (`848295`, lit column `a4b0b5`, dark column and two eave-shadow rows `575f79`). Two windows, `pane` (9,33-37,54) and (58,33-86,54) in `594b45` frames with mullions every 7 px and a rail y56-63 below. Upright board (41,30-54,59): `e4cecc`, サケ vertical in `aa4d31` at (43,33). Pent y67-75: two kawara courses, ink row 76. Ground floor y77-122 on `2a2636`, posts at x 6, 35, 62, 87. Eight unlit paper lanterns y78-88 from x 9 every 10 (`e4cecc`, lit column `fafcfd`, marks `aa4d31` and `314b8e` in turn). Cell 0, counter (8,91-35,121): dark back, three bottles (`508582`, `7f513b`, `314b8e`), the cook (`f6a583`, `314b8e` band), a `7f513b` top, boarded front in `hl.scanlines`. Cell 1, door (38,90-61,122): `e4cecc` paper leaves with `594b45` lattice under the long noren (37,89-62,104) `314b8e` with a `fafcfd` wave. Cell 2: red lantern (66,89-74,107) with an `e4cecc` label, two crates (66,108-86,121) `c6a663`/`a7843b`. Step y123-126. |
| midrise | `canvas(4, 6)` | y2-23 slate roof x4-123; on it the AOBA board (24,5-103,19): `395050`, top row `506b6b`, bottom row `2e4040`, frame `c6a663`; A O B A one glyph each, 14 px apart from x 40, y 8, in `c6a663`; a 7 px stepped leaf roundel at x 30 and 97. Cornice y24-25 `be9e8c`. Body (6,26-121,150) pale tile: `e4cecc`, joints `d7b6ab` every 6 rows and every 12 columns, lit west column `fafcfd`, east pier x114-121 `d7b6ab`. Five ribbon windows (10,y-91,y+14) at y = 30 + 24f: `395050` frame and mullions every 10 px over `pane`; a blind (`e4cecc`, bottom row `d7b6ab`) half down where `(i + f) % 3 == 0`; sill rows `fafcfd`, `be9e8c`. Banner (97,30-110,134) red, AOBA vertical in `fafcfd` at (101,38) with `pitch=14`, a 12 px stepped `c6a663` roundel at (98,108), a small `pane` (98,138-109,148). Canopy y150-157 x2-125 `395050` (top `506b6b`, bottom two rows `2e4040`, a `c6a663` stud every 6 px). Ground floor y158-186 on `2c2d51`: show windows (9,161-30,184) and (98,161-119,184) as `pane` with two dressed figures each (`f6a583` heads, clothes `aa4d31`, `c6a663`, `395050`), sale banners at x 33 (`aa4d31`) and 88 (`c6a663`), door header (42,158-85,161) `c6a663` over `a7843b`, two door pairs (42,162-62,186) and (65,162-85,186) in steel frames over `pane`, piers at x 6, 30, 40, 86, 96, 119. Step y186-189. |

The coordinates are today's bands and the prototype's; move a detail by a pixel or two where the drawing
needs it, but keep the trunk and foot rows, the door cells and what each glow spot sits on.

## Changes

`gamev2/tools/generate_sendai_town_art.py`
- Imports: `import house_look as hl`; `from generate_sendai_art import foliage, roof_tile, ground_shade,
  speck, pane as dark_pane` (`pane` is a local name in `stained_glass`).
- A `D_` palette block and three helpers at the top of the "Downtown / Jozenji-dori" section:
  `bough(d, pts, w, base, hi, lo)`; `kawara(im, x0, y0, x1, y1)` (`roof_tile(x, y - y0)` over the box);
  `slab_roof(im, x0, y0, x1, y1)` (a 3 px steel coping, `a4b0b5` with a `dae2e4` top row and west column
  and a `848295` bottom row and east column, a `444f5e` line inside it, then slate panels 9 wide with
  staggered joints and a `698592` row under the top coping; the shape of
  `generate_devhouse_art.flat_roof`, in this block's colours).
- `zelkova`, `jozenji_statue`, `gyutan`, `zunda`, `izakaya`, `midrise` rewritten as above; `edamame` and
  `chochin` redrawn in `D_` colours or folded into their one caller.
- Removed only if `grep` shows no other user: `limb` (l.743), `DBRONZE*`, `MID*`. Nothing else is deleted,
  moved or reordered: #336, #333, #342, #344 and #345 edit the same file.

`gamev2/assets/sprites/`: the seven PNGs, regenerated. No other PNG is committed.

`gamev2/tools/tests/sendai-town-art.test.js`: new, modelled on `kanazawa-art.test.js` (below).

`gamev2/docs/generators-and-checks.md`, end of "House look: GuttyKreum": one paragraph saying the seven
downtown pieces of `generate_sendai_town_art.py` (#343) are drawn by the recipe, the trees' autumn ramps
running gold or russet into green, teal, blue and purple, and are held by `sendai-town-art.test.js`.

## Data and interfaces

None change. No `config.json`, Tiled, world map or `src/` edit. `PIECES` is untouched, so for the seven
keys the manifest's `size`, `px`, `anchor`, `door(s)`, `solid`, `walk_through`, `night_halo`, `glow`,
`layer`, `district` and `description` are what they were. "Lit" in a description now means what the
unchanged glow spots do at night; by day the glass is dark.

## Tests

`gamev2/tools/tests/sendai-town-art.test.js` (test names prefixed `sendai town art:`; reuse the
`load` / `hex` / `sheets` / `rebuild` shapes of `kanazawa-art.test.js`):

1. Sizes `[192,256] [192,256] [128,192] [256,256] [192,192] [192,256] [256,384]`; every pixel a 2x2
   block; alpha 0 or 255, except `2a3151` at alpha 90 on the two trees and the statue only.
2. Every colour is in a GuttyKreum sheet; opaque colours at most 16 (trees, statue) or 24 (buildings);
   none over half the opaque pixels; none of `f6dc8c f2c66a f9c22e 2b373c 000000 ffffff`; `f3d890`
   under 3% of the opaque pixels on the statue and the buildings.
3. Every opaque pixel with a fully clear 4-neighbour inside the canvas is `0a1627`.
4. Dark glass: `2c2d51` / `4b6396` pixel counts of at least 3000 / 200 on zunda, 2000 / 150 on izakaya,
   10000 / 800 on midrise; `c6a663` present on gyutan, izakaya and midrise; both trees hold `3c396d`
   and `508582`, -a `c6a663`, -b `ce6a42`.
5. Source: the bodies of the six builders and of `bough`, `kawara`, `slab_roof`, `edamame`, `chochin`
   (those that remain) hold none of `.polygon(`, `.ellipse(`, `.arc(`, `.pieslice(`, `.chord(`, `.line(`,
   `blob(`, `puff(`, `grounded(`, and no bare `roof(` call (`/\broof\(/`).
6. `PIECES` still gives the seven their size, `door`, `solid` and `lit` (the literal values of today's
   rows, read through a `python3 -c` snippet that prints them as JSON).
7. The tool draws what is committed: for every key of `SPRITES` (all 102), the built image doubled equals
   the committed PNG's pixels (skipped without Pillow, as `rebuild` does). This holds on master today.

The implementer's run, from `gamev2/`:

```bash
mkdir -p /tmp/343/before /tmp/343/after
python3 tools/generate_sendai_town_art.py --sheet /tmp/343/before/sheet.png --scenes /tmp/343/before --manifest /tmp/343/before/manifest.json
git checkout -- assets/sprites                      # the run re-encodes all 102 PNGs
# ... rewrite the builders ...
python3 tools/generate_sendai_town_art.py --sheet /tmp/343/after/sheet.png --scenes /tmp/343/after --manifest /tmp/343/after/manifest.json
git checkout -- $(git status --short assets/sprites | awk '{print $2}' | grep -vE 'sendai-(zelkova-[ab]|jozenji-statue|gyutan|zunda|izakaya|midrise)_0_0\.png')
git status --short                                  # the seven PNGs, the tool, the test, the doc
python3 tools/house_look.py --sheet /work/media/343-after-seven.png assets/sprites/sendai-{zelkova-a,zelkova-b,jozenji-statue,gyutan,zunda,izakaya,midrise,pub,maple}_0_0.png
node tools/test_game.js; python3 tools/test_blog_to_npc.py; node tools/play.js check
python3 tools/check_generators.py; python3 tools/sync_cities.py --check
```

- Compare the seven `sprites` entries of the two manifests: they must be equal.
- Copy `sendai_art_downtown.png` and `sendai_art_downtown_night.png` from before and after to
  `/work/media/` and look at them, and at the station, samurai and distillery scenes (zelkova-b stands in
  them). Say in the summary which of the seven still read as flat, and that the in-game `?tod=night`
  view does not exist because nothing is placed.
- Browser regression (`tools/browser/README.md`): run it once and report; it cannot show these sprites,
  so it should be unchanged.

## Risks and open questions

- **Not placed anywhere**: the look in a room, under the real night grade and at phone size cannot be
  checked until Sendai's rebuild places them; `night()` is a preview only.
- **Night**: the glow spots stay (ticket), now over dark glass and dim gold. If one looks wrong in
  `_night.png`, say so in the summary rather than editing `lit`.
- **Colour budget**: the izakaya prototype came to 25 and midrise is counted at 23; one more detail colour
  breaks the cap. Reuse a listed colour before adding one.
- **Gold that reads gold**: four of the eleven ramp tones are cool, as the ticket asks. If the avenue row
  reads too blue in the scene, drop `425faa` (gold) / `314b8e` (russet) from the ramp; test 4 still passes.
- **12px lettering** is smaller than today's double-size signs; the boards keep their size so the glow
  spots still fit, and the glyphs are spaced out.
- **Same file as #336, #333, #342, #344, #345**: expect merge conflicts if edits stray outside the six
  builders, the `D_` block and the import lines. Test 7 catches a merge that leaves a builder and its PNG
  out of step.
- Descriptions are left as written: "green-glass ribbon window" becomes dark glass in green frames.
