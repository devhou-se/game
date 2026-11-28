# Asahikawa's own art in the house look (#310, part 3 of #289)

## Context

`gamev2/tools/generate_asahikawa_art.py` draws Asahikawa's 52 sprites: 34 pieces (`PIECES`: the station,
Heiwa-dori's four shops, lamp, bench and ice sculptures, the ramen alley, the Asahibashi kit, the riverbank
houses and the zoo gate) and two ground families of nine tiles. Measured against the 14 sheets in
`art-source/GuttyKreum`, 338 of its 358 colours are in no sheet (71% of its opaque pixels; the ground tiles
100%). Windows and lamps are lit `f6dc8c` with white cores, signs bright `f9c22e`, snow is `f2f5fb` /
`c9d6ea` under a pure white crest, and the two flat-roofed shops have no roof, only a parapet line.

Outcome: the same 52 keys at the same sizes, anchors, door, solid and glow data, in the house look
("House look: GuttyKreum" in `docs/generators-and-checks.md` on master): sheet colours only, dark glass with
a slanted glare, lamps the pack's dim gold `c6a663`, snow shaded in the pack's blues, roofs seen from above
on the shop row. No map, config or `devhouse.world` change. `generate_hokkaido.py`,
`generate_sapporo_art.py`, the snow tiles and the pack art are not touched.

The direction was prototyped outside the repository (old above or left of new):
`/work/media/310-direction-station-heiwa.png`, `310-direction-ramen.png`, `310-direction-bridge-zoo.png`;
the town before any change is `/work/media/310-asahikawa-before.png`.

## Approach

Recolour everything, redraw where the ticket asks. Five moves, all inside the one tool:

1. **The palette under the same names.** The tool's palette constants take sheet hexes (table below), so
   every builder keeps its drawing. A blanket "nearest sheet colour" pass alone was tried and is wrong: timber
   and lit windows both land on `c6a663`, the polar bear turns pink, plaster lands on rare greys.
2. **One finisher, called from `build()`** on each of the 34 pieces before doubling, so no builder's ending
   changes: snow becomes a lit form in the pack's snow ramp, glass becomes the pack's pane, the off-sheet
   colours that imported helpers paint are swapped, and anything left is settled to the tool's closed colour
   list (`mix()` remains, Pillow curve edges, alpha layers). Shared modules are not edited; the ink stays
   `generate_hokkaido.INK` `0a1627`, which is the recipe's.
3. **No lit glass by day.** Every lit pane and door becomes `GLASS`; what stood in the window stays in front
   of it. Night light is the unchanged `glow` lists and `DayNight`'s `lamp-post` / `-lanterns` rule, so no lit
   feature moves. Lamps become `c6a663` with `a7843b` shade and a small `f3d890` core, never white.
4. **Roofs and shading on the shop row**: the bookshop and the woodcraft shop get a flat roof seen from
   above in the rows that are empty today, the kura the pack's kawara, plaster and charred walls a shaded
   face.
5. **The ground families** in sheet colours, the pixels copied from the snow tile left exactly as copied.

Rewriting all 34 builders with rectangles only (as #307 did for ten fronts) was the alternative; it is
several times the work for a size-M ticket and would move silhouettes the map depends on. New drawing here
is rectangles, points and integer maths only; the existing ellipses, polygons and lines stay (the check
pins Pillow 11.3.0).

`tools/house_look.py` (#279) is on master but has no `foliage`, `roof_tile`, `pane`, `glaze` or
`flat_roof`, so those come from where the ticket says: `repaint`, `roof_tile` from `generate_sendai_art`,
`glaze`, `flat_roof` from `generate_fukuoka_art` (both draw nothing on import). If the checkout has
`house_look.py`, new faces may use its `fill` / `shade`; nothing here needs it.

## Changes

### `gamev2/tools/generate_asahikawa_art.py`

**a. Palette** (same names; hexes are the prototype's and may be tuned by eye, but only to sheet colours):

| Names | Hexes |
|---|---|
| `TIMBER`, `_HI`, `_LO`, `_DK` | `bb8971 d7b6ab aa775f 7f513b` |
| `CHAR`, `_LO`, `_HI` | `493938 2a2636 6d574e` |
| `PLASTER`, `_LO`, `_DK` | `fafcfd dae2e4 a4b0b5` |
| `BG`, `_HI`, `_LO`, `_DK` | `6c8e7f 93c297 506b6b 395050` |
| `ICE`, `_HI`, `_LO`, `_DK` | `bbe9ff ecfaff 8ec2fa 588cc6` |
| `ROOF_R`, `_HI`, `_LO` | `aa4d31 d16b56 8a3a22` |
| `ROOF_B`, `_HI`, `_LO` | `425faa 5a86de 314b8e` |
| `ROOF_G`, `_HI`, `_LO` | `508582 6c8e7f 395050` |
| `KAWARA`, `_LO`, `_HI` | `53596d 39374c 78768a` |
| `ORANGE`; `PEN`, `PEN_HI` | `ce6a42`; `191c2a 2c2d51` |
| `MINT`, `_LO`, `_HI`, `_DK` | `8fb2b0 6c8e7f b1dfdc 506b6b` |
| `PAVE` (five); `PAVE_ROSE`, `_ROSE_LO`, `_JOINT`, `_HI` | `d2bab0 b3aaa0 bebaba ac9f96 c2ac9e`; `c69f96 ac9f96 9e9e9e e4cecc` |
| `ASPH`, `_HI`, `_DK`, `_WET`; `SLUSH`, `_HI` | `5f6177 726f86 504e65 413f53`; `adb2c2 d1e2eb` |
| `DECK`, `_LO`, `_HI` | `848295 78768a 94a2a8` |
| `CRACK_HI`, `CRACK_LO` | `fafcfd 8ec2fa` |
| new `LAMP`, `LAMP_HI`, `LAMP_LO` | `c6a663 f3d890 a7843b` |

Inline literals named here; every other `rgb('…')` literal and RGB tuple in a builder is replaced in the
source by the colour `settle` maps it to (print the map once while working), so the source says what is
painted: house_red siding `e4cecc`, lo `be9e8c`, hi `fafcfd`; house_blue wall `dae2e4 a4b0b5 fafcfd`, gable
`575f79 47485d 848295`; the zoo's blue (every `3a8fd8`, the board's hi and lo) `5a86de 7db9fa 425faa`; the
bear `e4cecc`, lo `be9e8c`; the bookshop's tile `8085b1`, lo `575f79`, hi `99a1ca`, parapet line `47485d`;
the narrow ramen shop's mustard `c6aa71`, lo `a7843b`, hi `e3c587`; the shoyu shop's tin roof
`7f513b aa775f 594b45`; crate and board yellows `fde38a` → `LAMP_HI`, `c8941c` → `LAMP_LO`; the tent
`ORANGE`, hi `f6a583`, lo `aa4d31`, dk `904a37`.

**b. The finisher** (new, above `build()`; `build()` calls `finish(fn())` for the 34 `PIECES`, not for the
ground families):

```python
from generate_sendai_art import repaint, roof_tile
from generate_fukuoka_art import glaze, flat_roof

A_SNOW = [rgb(c) for c in ('fafcfd', 'ecfaff', 'd1e2eb', 'b7c3e3', '99a1ca', '8085b1')]
A_SNOW_OLD = {SNOW: 1, SNOW_LO: 3, SNOW_SH: 4, SNOW_DK: 5}
A_SWAP = {rgb(a): rgb(b) for a, b in (                 # what the imported helpers and constants paint
    ('ffffff', 'fafcfd'), ('f6dc8c', 'c6a663'), ('f9c22e', 'c6a663'), ('2a2330', '2a2636'),
    ('d2a58c', 'be9e8c'), ('89af78', '93c297'), ('2b373c', '39374c'))}   # 2b373c: flat_roof's, until #375
A_PACK = [rgb(c)[:3] for c in '''
    8a3a22 aa4d31 d16b56 e78d7b ffe2e0 904a37 ce6a42 f6a583 86624f a7843b c6a663 f3d890 fafcfd
    2e4040 395050 506b6b 6c8e7f 93c297 172459 314b8e 425faa 5a86de 7db9fa bbe9ff 2a233b 3c396d
    444679 8f72b6 bfabd7 c9cbff 83374f bb6479 ff9b92 2a2636 47485d 575f79 848295 a4b0b5 dae2e4
    8e7366 be9e8c e4cecc 080d16 0a1627 191c2a 2c2d51 ecfaff d1e2eb b7c3e3 99a1ca 8085b1 8ec2fa
    588cc6 bcc7cc 94a2a8 bb8971 d7b6ab aa775f 7f513b 594b45 493938 6d574e 53596d 39374c 78768a
    c6aa71 e3c587 508582 8fb2b0 b1dfdc 2a3151 4b6396 5b6c79 698592 444f5e 4a6262 434857 d2bab0
    b3aaa0 bebaba ac9f96 c2ac9e c69f96 9e9e9e 5f6177 726f86 504e65 413f53 adb2c2'''.split()]


def form(im, ramp, old):
    """Snow as a lit form: one tone lighter on a rim facing up or left, one darker facing down or right."""
    px = im.load(); W, H = im.size
    idx = {(x, y): old[px[x, y]] for y in range(H) for x in range(W) if px[x, y] in old}
    bare = lambda x, y: not (0 <= x < W and 0 <= y < H) or px[x, y][3] == 0 or px[x, y] == INK
    for (x, y), i in idx.items():
        if bare(x - 1, y) or bare(x, y - 1):
            i = max(0, i - 1)
        elif bare(x + 1, y) or bare(x, y + 1):
            i = min(len(ramp) - 1, i + 1)
        px[x, y] = ramp[i]


def settle(im):
    """Any pixel not in A_PACK takes its nearest A_PACK colour (the first listed wins a tie); alpha is kept."""
    px = im.load(); near = {c: c for c in A_PACK}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) not in near:
                near[(r, g, b)] = min(A_PACK, key=lambda c: 2 * (c[0] - r) ** 2 + 4 * (c[1] - g) ** 2
                                      + 3 * (c[2] - b) ** 2)
            if a:
                px[x, y] = near[(r, g, b)] + (a,)


def finish(im):
    form(im, A_SNOW, A_SNOW_OLD); glaze(im); repaint(im, A_SWAP); settle(im)
    return im
```

`A_PACK` is the ramps of `house_look.RAMPS` (all sheet colours) plus the table
above, the snow ramp, the pane and `flat_roof` / `roof_tile`'s tones; add a hex when the palette is tuned.
`mix()` is not called by any builder afterwards (delete it if unused).

**c. Glass and lamps** (all positions as now):

- `lit_window`: the pane is `GLASS`, its head line `GLASS_HI`, whatever `lit` says (the parameter stays; the
  lone highlight line of the unlit case is dropped, the glare is `glaze`'s). Curtains `e78d7b`, `7db9fa`.
- Every other `WARM` or `mix(WARM, …)` pane or door fill becomes `GLASS`, and a `WHITE` head line on it
  `GLASS_HI`: the kura's slatted window and door, the woodcraft showroom and door pane, the bakery window and
  door pane, the bookshop window and door pane, the three ramen shops' windows and doors (shoyu's counter
  window loses its paler upper band), miso's round gable window, house_red's inner door and its pane,
  house_blue's door pane, the ticket booth window. Goods, furniture, the cook and the clerk are drawn over
  the glass as now.
- `sliding_doors`: both leaves plain `GLASS`; the per-pixel `mix` and its streaks go.
- `wood_glass` (the station's glass wall), no `mix`: the lining seen dim through dark glass. Ceiling (top
  13%) `CHAR` on `(x + ry) % 3 == 0` else `CHAR_LO`; wall boards by `x % 4`: `TIMBER_DK` on 0, `CHAR` on 3,
  else `CHAR_HI`; below 62% `CHAR_HI` on 0 else `CHAR`; floor (below 80%) `CHAR_LO`, `2c2d51` every fifth;
  then the sky: with `s = (x - x0 + y - y0 + phase) % 52`, `4b6396` where `s < 2` and `2c2d51` where
  `s == 24`. Compare the fractions with integers (`ry * 100 < h * 13`). Pendant lamps `LAMP` with a
  `LAMP_HI` point; the mullion's light line `STONE_LO`.
- Lamps are `LAMP`: `heiwa_lamp`'s pane `[11,11,20,20]` with `LAMP_LO` on rows 11 and 19-20 and a `LAMP_HI`
  core `[14,14,17,16]` (no `mix`, no white); the arch piers' lamps, house_blue's porch light, the tent's
  lamp; the station board's `ASAHIKAWA`. Amber signs, nobori, crates and `ZOO` become gold through `A_SWAP`.
  Paper lanterns stay unlit paper (`fafcfd` / `e4cecc`).

**d. Roofs and shading, the shop row** (drawn pixels, before doubling):

- New `snowy_roof(im, x0, y0, x1, y1, seed)`: `flat_roof(px, x0, y0, x1, y1)`, then snow over the slate
  inside the coping (`SNOW`; `WHITE` on its top row and left column; `SNOW_LO` on its right five columns and
  on a hashed speckle; `SNOW_SH` on its last row), leaving the slate bare along the front two or three rows
  (ragged by a hash of `x`) and in a few hashed patches. Integer hashes only.
- `shop_books`: `snowy_roof(im, 3, 1, 92, 15, seed=3)` replaces the `snow_slab` at rows 7-11; the parapet is
  rows 16-17. Spines in five colours (`RED`, `NAVY`, `ROOF_G`, `LAMP`, `CREAM`); `mix(c, tile_lo, .5)` on the
  right edge is `tile_lo`.
- `shop_woodcraft`: `snowy_roof(im, 3, 1, 124, 15, seed=6)`, a `CHAR` fascia on rows 16-18 (`CHAR_HI` top
  row, `CHAR_LO` bottom), a steel vent with snow on it at `[20,4,31,10]`. The charred ground floor
  `[5,46,122,91]` (under its `CHAR_LO` shadow rows 43-45) is
  `boards_v(…, CHAR, CHAR_LO, CHAR_HI, step=6)`, not one fill. The showroom floor seen through the glass
  (rows 78-85) is `TIMBER_DK` under a `TIMBER_LO` line.
- `shop_sake`: the main roof (scan rows 26-49) and the pent roof (73-79) are `roof_tile(x, y)` per pixel in
  place of `tiles()`; eave lines `39374c`. Each plaster face keeps its `PLASTER_DK` eave shade and
  `PLASTER_LO` right edge and gets its lowest third `PLASTER_LO`, joined by one checker row (the recipe's
  `shade`).
- `shop_bakery`: the white step caps become steel coping (`dae2e4`, top row `fafcfd`, the row under each
  `MINT_DK`), two rows of `MINT_LO` eave shade under each cap; chimney brick `aa4d31` with `8a3a22` courses.
- `station_front`: the two white roof slabs become steel copings (`94a2a8`, top row `d1e2eb`, bottom row
  `47485d`) under their snow.
- `fishing_tent`: a band of the lo tone along rows 55-60 of the lit side, so no colour covers half of it.

Everything else (bench, ice sculptures, ramen gate, lantern post, crates, stock pot, the houses, fences,
ice crack and hole, the zoo pieces) changes through the palette, the listed literals and the finisher only.
**The Asahibashi kit** (`asahibashi-deck`, `-arch-w`, `-arch-e`, `-brace`) is recoloured only:
`BRIDGE_ROWS`, `PIER_LAMP_Y`, `_arch_pts`, the canvases and every coordinate stay; deck literals `666c7e` →
`575f79`, `bcc1cc` → `bcc7cc`, `a9afbd` → `a4b0b5`.

**e. Ground** (`paving_px`, `alley_px`, `ground`): the lit arris is `PAVE_HI` (no `mix`), snow in a joint
`d1e2eb`, the alley's `6f7f9c` is `575f79`. In `ground()` the lit lip is `fafcfd`, scuffed snow `ecfaff`,
and the bank's shadow keeps its multiply but each result goes through `settle`'s nearest-colour rule.
Pixels copied from `snow-autotile_center.png` are written unchanged (the seam with the snow tile, which
#357 owns, must stay invisible).

**f. Registry**: `PIECES` keys, sizes, `door`, `solid`, `walk`, `glow`, `layer`, `FAMILIES`, `FLAT`,
`glow_spots()`, `manifest()`, `main()` unchanged. Descriptions and the docstring say "window" where they say
"lit" / "lamplit" and name the house look.

### Other files

- `gamev2/assets/sprites/`: the PNGs of the 52 keys that changed; commit only those.
- `gamev2/tools/tests/asahikawa-art.test.js` (new; see Tests).
- `gamev2/docs/landmarks-and-towns.md`: one sentence in the Asahikawa bullet (drawn in the house look by a
  finisher: sheet colours, dark glass lit only by glow spots, dim-gold lamps, snow in the pack's blues;
  ground edge tiles copy the snow tile).
- `gamev2/assets/map/`: `python3 tools/make_worldmap.py --pil`, in its own commit.

Commits: `gamev2: <what changed> (#289)`, the tool, PNGs, test and doc in one, the world map in the next.

## Data and interfaces

None. `config.json` (`spriteMetadata` anchors and glow), `tiled/`, prefabs and `devhouse.world` must come
out of the rerun unchanged; `git status` after `python3 tools/generate_asahikawa_art.py` shows only PNGs.

## Tests

New `tools/tests/asahikawa-art.test.js`, decoding with `tools/png` and reading the sheets' colours as
`tools/tests/house-look.test.js` does on master (walk `art-source/GuttyKreum`, skip `preview*`):

1. The 34 piece keys have their sizes (cells × 64, the table in the test) and are pixel-doubled (every
   2×2 block one colour); the 18 ground tiles are 64×64.
2. Every pixel with alpha > 0 of the 34 pieces and the two `_center` tiles is a sheet colour; on the 16 edge
   tiles every colour is a sheet colour or one of `snow-autotile_center.png`'s.
3. Each piece has at most 32 opaque colours and none covers more than half its opaque pixels.
4. No piece holds `f6dc8c`, `f9c22e`, `ffffff`, `f2f5fb` or `c9d6ea`; `heiwa-lamp-post_0_0` holds `c6a663`;
   `heiwa-shop-books_0_0` and `heiwa-shop-woodcraft_0_0` hold `5b6c79` (slate) above row 32 and at least four
   tones of the snow ramp.
5. The source has no `mix(` call inside a builder and does not assign into `generate_hokkaido` or
   `generate_sapporo_art`.

From `gamev2/`:

```bash
node tools/play.js render Asahikawa /work/media/310-before.png      # before editing (or reuse 310-asahikawa-before.png)
python3 tools/generate_asahikawa_art.py --sheet /tmp/sheet.png --scenes /tmp/scenes && git status --short
node tools/play.js render Asahikawa /work/media/310-after.png
python3 tools/make_worldmap.py --pil
node tools/test_game.js; python3 tools/test_blog_to_npc.py; node tools/play.js check
python3 tools/check_generators.py; python3 tools/sync_cities.py --check
```

The generator writes the same 52 keys at the same sizes as before. Look at both renders and the sheet zoomed, and
say in the summary which sprites still read as flat (expected candidates: the ice sculptures, penguins, ice
cracks, the bakery's false front, and the gabled houses and miso shop, whose roofs stay edge-on). Then the
browser regression (`tools/browser/regress.js`, `tools/browser/README.md`) and play it at desktop and a
phone size, by day and with `?tod=night`: every glow still sits on its window, door, lantern or lamp, the
lamp posts and lantern posts get their halos, and no pane reads as lit without its glow. Screenshots to
`/work/media/`. Say what could not be run.

## Risks and open questions

- The approved look (#278's comment) could not be read from here; the direction follows the recipe in
  `docs/generators-and-checks.md` and the worked examples on master. The prototypes in `/work/media/` show
  it; the hexes are a starting point, the tests hold the rule.
- Until #355 and #357 land, the redrawn snow (top tone `fafcfd`, shaded blue) stands on the old snow tiles
  (`e1e9f2`-`ebf3fc`) and beside shared Hokkaido sprites in the old whites. The ground edge tiles copy the
  snow tile at generation time: when #357 changes it, this tool must be rerun (`check_generators` will show
  DRIFT), and the world map with it.
- `flat_roof` paints `2b373c`, in no sheet (#375, in review); `A_SWAP` covers it either way.
- Most builders keep Pillow curves and lines; their edges are settled to the list, stable on the pinned
  Pillow only (as today).
- The 32-colour cap is above the recipe's 24 for a large sprite: the fronts carry goods behind glass (the
  prototype's fronts ran 23 to 35, the bookshop highest before its spines were cut). Lower it if they fit.
- `assets/map` conflicts with any sibling redraw that lands first: rebuild it after rebasing, never merge
  it. This branch is 24 commits behind master: there `generate_sapporo_art.py` (#302) has its own `form`
  (it runs before the outline, so it does not treat ink as bare: keep this tool's) and `house_look.py`
  exists; the names this tool imports from Sapporo's and Fukuoka's tools are unchanged there.
- Art-only: no room is rebuilt. Rooms that show the change: Asahikawa (and the world map).
