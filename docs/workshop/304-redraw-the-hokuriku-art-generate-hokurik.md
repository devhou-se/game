# 304 — Redraw the Hokuriku art (generate_hokuriku_art.py) in the house look

Part 1 of 3 of #290. All paths are under `gamev2/`; commands run from `gamev2/`. Coordinates are the tool's
half-size pixels (32 a cell), y from the top.

## Context

`tools/generate_hokuriku_art.py` draws 21 sprites for Kanazawa, Shirakawa-go and Toyama. Two
(`kanazawa-chaya-a/-b`) are already in the house look (docs/generators-and-checks.md, "House look:
GuttyKreum") and are the model. The other 19 are in the old look. Measured on the committed PNGs: 2 to 12
colours each that no GuttyKreum sheet has (53% of the gate's pixels, 90% of the whisky bar's); front
elevations with trapezoid roofs; lit amber windows (`whisky_bar`, `ramen_shop`, the port tower's lamp room,
the farmhouses' paper); the ginkgo as three smooth ellipses; flat thatch; one colour on 76% of the canal
bridge and 81% of the paddy; translucent shadows and glass; `polygon`, `ellipse`, sloped `line` and float
arithmetic throughout.

In scope (key `<name>_0_0`, size in cells, what must stay where it is):

| key | builder | size | fixed |
|---|---|---|---|
| `kanazawa-ishikawa-gate` | `ishikawa_gate` | 8x4 | gateway cols 3–4 (x 96–159) clear below its lintel; posts x 92–99, 156–163 |
| `kanazawa-kotoji` | `kotoji` | 2x2 | |
| `kanazawa-whisky-bar` | `whisky_bar` | 4x4 | door col 1 (x 32–63); stone foot y 124–127 |
| `kanazawa-canal-bridge` | `canal_bridge` | 2x4 | full bleed, walked N–S, kerbs x 2–7 and 56–61; depthBias −200 |
| `hokuriku-ginkgo` | `ginkgo` | 2x3 | trunk centred, its foot at y 92 |
| `shirakawa-gassho`, `-gassho-small` | `gassho(cw, ch)` | 5x5, 4x4 | door centred (cx−13..cx+12); stone foot x 12..W−13, y H−5..H−1 |
| `shirakawa-paddy` | `paddy` | 1x1 | full-bleed Floor tile, tiles in both directions |
| `shirakawa-hasa` | `hasa` | 3x2 | |
| `shirakawa-bridge` | `suspension_bridge` | 8x2 | deck x 8–247, 23 rows deep from y 36 (sagging 3 at mid-span), opaque end to end; towers x 2–9 and 246–253; depthBias −200 |
| `shirakawa-lookout` | `lookout` | 4x1 | |
| `shirakawa-peak` | `peak` | 6x4 | the `RIDGE` silhouette table |
| `shirakawa-bear-sign` | `bear_sign` | 1x2 | |
| `toyama-glass-museum` | `glass_museum` | 6x6 | doors cols 2–3 (x 64–127) |
| `toyama-tram` | `tram` | 5x2 | heads **west** (head lamp at the west end; `glows-trams.test.js`) |
| `toyama-tram-rail` | `tram_rail` | 1x1 | scale 1, drawn over the pack's `road-plain_0_0.png`; rails y 18–21 and 44–47 |
| `toyama-tram-stop` | `tram_stop` | 3x2 | platform y 54–62 |
| `toyama-ramen` | `ramen_shop` | 4x4 | door col 1 (x 32–63); stone foot y 124–127 |
| `toyama-port-tower` | `port_tower` | 3x7 | door at centre bottom; `game.lookUp` |

Out of scope: `chaya` and its two PNGs (pixel-identical after), the map, `config.json` rooms, placements.

Outcome: the 19 are redrawn, shape and shading, not a recolour, to sit beside `chaya`, `seven-eleven`,
`sendai-pub`, the maple and #385's castle; keys, sizes, anchors, `depthBias`, labels and `lookUp` unchanged.

## Approach

Rewrite the 19 builders in place. Every one follows the house-look rules; the ones that bite here:

- Only colours the sheets in `../art-source/GuttyKreum` use. Ink `0a1627` on the silhouette via `hl.outline`
  (drawn last), never black. At most 24 colours a sprite (16 for paddy, rail, bear sign); none on half the
  opaque pixels (the rail tile aside: it is the pack's road).
- `hl.fill` rectangles and pixel writes only: no `polygon`, `ellipse`, `arc`, `pieslice`, `chord`,
  `rounded_rectangle`, sloped `line`; integer arithmetic only (slopes and sags as stepped runs); alpha 0 or
  255. The one exception is the ginkgo's `ground_shade` (`2a3151` at alpha 90), as on the maple, pine and cedar.
- A building shows its roof from above; no trapezoid front roofs. Glass is dark (`pane`, or `2c2d51` under a
  `2a3151` head with a `4b6396` slanted glare); paper is unlit `e4cecc`/`fafcfd`. Nothing is lit by day:
  lamps and lanterns are `c6a663` with at most a 2x2 `f3d890` core. No `glow` metadata is added.
- Lettering is `hl.text` (PixelMplus12): `BAR`, `GLASS`, `ラーメン`. The local 5x7 `FONT` goes.

Helpers, reused rather than rewritten:

- `house_look` (`import house_look as hl`): `fill`, `outline`, `text`, `pixmap`, `stamp`.
- This file's model: `kawara`, `bars`, the `T_*` colours.
- `generate_sendai_art`: `foliage`, `stem`, `limb`, `ground_shade`, `speck`, `pane`, `roof_tile`, `NEEDLE`,
  `AUTUMN`.
- `generate_kanazawa_art` (#385, #307): `lead_hip`, `lead_band`, `plaster`, `musha`, `namako`, `stonework`,
  `sill_beam`, `iron_post`, `roof_plan`, `lantern_h`, `noren_h`, `lattice_doors`, `stone_foot`, `bottles`,
  `save_png`. That file imports `kawara` and `bars` from this one, so reach it lazily:

  ```python
  def _ka():
      """generate_kanazawa_art's castle and shopfront helpers. Imported when a builder
      runs, not at the top: that file imports kawara and bars from this one."""
      import generate_kanazawa_art
      return generate_kanazawa_art
  ```
  (Checked: works with this tool as `__main__`.) Moving those helpers into a shared module would be cleaner
  but rewrites a file three open tickets are in; not here.
- Not `flat_roof` (generate_fukuoka_art) nor sendai's `P_ROOF_LO`/`P_JOIN_LO`: they paint `2b373c`, which no
  sheet has (#375, #378). Use `roof_plan`, whose dark is `2e4040`.

Palette, added beside the `T_*` block as `K_*` (all verified in the sheets):

| use | colours, light to dark |
|---|---|
| ginkgo | `ffecb8 f3d890 c6a663 a7843b 86624f 5b283b` |
| thatch | `be9e8c a68777 8e7366 775d4e 6b5241 584a43` |
| timber | `aa775f 71412a 5a3827 3f210f` |
| straw (sheaves, stubble, sign board) | `f3da98 e3c587 c6aa71 a7843b 86624f` |
| black boards, iron, cable | `47485d 2a2636 191c2a` |
| stone, rock | `a4b0b5 848295 575f79 53596d 47485d`, joints `2e4040` |
| snow | `fafcfd dae2e4 a4b0b5 949bb2` |
| paddy earth; water | `a68777 968576 8e7366 775d4e`; `d3f4ff a0bbc2` |
| teal livery | `8fb2b0 4a9488 508582 357570`, line `2e4040` |
| museum glass | `bbe9ff 7db9fa 5a86de 314b8e`; steel `d1e2eb bcc7cc 949bb2 646e86` |
| red | `d16b56 aa4d31 8a3a22` |
| paper; lamp | `fafcfd e4cecc be9e8c`; `c6a663`, core `f3d890` |

The builders (each keeps the fixed cells above; "as #385" means the helper calls of `castle_gate` /
`whisky_bar` in `generate_kanazawa_art.py`):

| sprite | redraw |
|---|---|
| ishikawa-gate | Castle look as #385. Turret x 0–87: `stonework` base, `sill_beam`, `namako` dado, `plaster` storey with `musha` windows, `lead_hip` roof seen from above. Gateway: its own `lead_hip` over cols 3–4, timber lintel, `iron_post`s, leaves folded back against the posts, 3 opaque soffit rows (`191c2a`) under the lintel, clear below. Walls x 84–95 and 160–255: `stonework`, `namako`, plaster with dark loopholes, `lead_band` coping. |
| kotoji | Stone tones; cap, fire box, platform and the two unequal legs as stepped rectangles, lit west faces, shaded east. Fire box dark (`2c2d51`) with a 2x2 `c6a663` core. No shadow. |
| whisky-bar | As #385's `whisky_bar`, at 4x4: `roof_plan` from above (tank, flue) over the top ~36 rows; black-board upper floor with two `pane` windows and `bottles` behind; unlit board lettered `BAR` in `c6a663`; canopy; timber ground floor, `lattice_doors` in col 1, a `pane` window east of it; cask as stepped rows; one `c6a663` lamp on a bracket; `stone_foot`. |
| canal-bridge | Slabs 3 across with joints every 16 rows, staggered; three stone tones by `speck` per slab, lit top row and shaded bottom row on each; kerbs with capstones every 16 rows. No colour over 40%. |
| ginkgo | Appendix. |
| gassho ×2 | Appendix `thatch(im, cw, ch)`: the roof seen from above and in front, ridge running back, lit west slope and shaded east, combed, thick cut edge over the gable and along the eaves, ridge bundles. Then the gable's tiers of unlit shoji under beams, the boarded ground floor with eave shadow, a dark doorway behind `bars`, two shoji screens, the stone foot (the prototype's numbers are in the appendix note). |
| paddy | Period 8 rows: furrow bands in two earth tones (neither over 45%), a stubble row per band as 1x2 tufts in straw tones placed by `speck`, 3–4 puddles (`a0bbc2`, `d3f4ff` glint). Left and right, top and bottom edges match. |
| hasa | Two posts and three rails in timber; sheaves as stepped columns (narrow tie, flared skirt) in straw tones, lit west, the row below overlapping the rail. No shadow. |
| bridge | Sag as an integer table (the present curve, rounded, as stepped runs). Deck planks in timber tones with a joint every 6 columns and lit top row; rope rails `8e7366`; hangers every 12 columns; cables `2a2636` with `47485d` on top; towers red (`aa4d31`, lit west `d16b56`, shaded east `8a3a22`) with dark caps. |
| lookout | Timber posts and two rails with lit tops; the signboard's picture (peaks, a roof) by `hl.pixmap`, framed in timber. |
| peak | `top(x)` from `RIDGE` by integer interpolation. Snow cap lit west / shaded east of each ridge line, rock below shaded in runs along stepped strata (not speckle), gullies as 1px stepped runs. Forest: `foliage` clumps drawn on a second image and copied only where the mountain is opaque, in bands from the tree line (which follows the silhouette, about 55 rows under `top(x)`) to the foot, cycling `NEEDLE`, `AUTUMN` and three ginkgo tones. Must come in at 24 colours: drop the ginkgo clumps first. |
| bear-sign | Timber post; board `f3da98` with lit top and `c6aa71` shade, red band `aa4d31`; the bear by `hl.pixmap` in `2a2636`. |
| glass-museum | Top ~40 rows: `roof_plan` from above. Below, the façade's vertical strips alternating steel and glass tones in runs of unequal width by `speck`, each glass strip dark-headed with a glare; the atrium slot over the doors in timber tones; steel fascia with `GLASS` by `hl.text`; `pane` doors in cols 2–3; `stone_foot`. |
| tram | Roof seen from above over the top ~12 rows (teal, equipment boxes, stepped pantograph); body in teal livery with a pale band; `pane` windows; stepped ends; head lamp `c6a663` west, tail `aa4d31` east; doors as dark panes; wheels as stepped discs (`_ka().disc`). No shadow. |
| tram-rail | Unchanged but for the rail colours: `2a2636` groove, `dae2e4` top, `848295` side. |
| tram-stop | Shelter roof seen from above (teal, lit west edge, dark east), posts, an opaque `pane` back, timber bench, timetable board in paper with `2a2636` lines; platform in stone tones with a pale edge. |
| ramen | As `chaya`: `kawara` main roof and pent roof; black-board front; unlit paper board with `ラーメン` vertical beside the door; counter window as `pane` with stool and bowl silhouettes; dark `noren_h` over `lattice_doors` in col 1; red `lantern_h` with `c6a663` bands; `stone_foot`. |
| port-tower | Stepped, bottom to top: `stonework` podium with the door, plaster shaft with course lines every 8 rows and a shaded east third, a railed gallery, the lamp room as dark glass with glare, a `kawara`-toned cap stepped in, a `c6a663` finial. |

`main()`: write through `_ka().save_png(im, f'{SPR}/{key}.png')` with a module `SPR = 'assets/sprites'`
(`tram_rail` reads the road through it too), so a rerun does not re-encode unchanged PNGs (#384). The rest of
`main()` stays.

## Changes

- `tools/generate_hokuriku_art.py`: the 19 builders, the `K_*` palette, `_ka()`, `SPR`, `main()`'s save, the
  docstring's sprite lines. Delete what nothing uses afterwards (`FONT`/`text`/`text_width`, `lead_roof`, its
  own `namako`, `lattice`, `LEAD*`, `BLIND*`, `THATCH*`, `GINKGO*`, `ROCKY*`, `SNOW*`, `TEAL*`, `ALU*`, unused
  imports). **Keep**, untouched: `chaya`, `kawara`, `bars`, `T_*`; `SPRITES`, `FLAT`, `LOOK_UP`; and what
  `generate_kansai_art.py` imports, with a comment saying so: `masonry`, `PLASTER`, `PLASTER_LO`, `BOARD`,
  `BOARD_LO`, `SOOT`, `SOOT_HI`, `SOOT_LO`, `INDIGO`, `INDIGO_HI` (also `BENGARA`, `CREAM`, `WHITE`: `T_NOREN` keys).
- `assets/sprites/`: the 19 PNGs. `assets/map/*`: rebuilt by `python3 tools/make_worldmap.py --pil`.
- `tools/tests/hokuriku-art.test.js`: new (below).
- `docs/generators-and-checks.md`: one sentence at the end of the house-look section naming this tool and its
  test. `docs/landmarks-and-towns.md`: nothing needed.

Not changed: `config.json` (the tool rewrites identical metadata), `tiled/`, `devhouse.world`, `src/`,
`check_generators.py`, `generate_kansai_art.py`, `generate_kanazawa_art.py`, the three room generators.

## Data and interfaces

None. No key, size, anchor, `depthBias`, `tileNames`, `lookUp` or `glow` changes.

## Tests

`tools/tests/hokuriku-art.test.js`, modelled on `tools/tests/kanazawa-art.test.js` (same `sheets()`, `load`,
`rebuild`), over the 21 keys unless said:

1. Size is cells x 64; `spriteMetadata` is `frameCount` 1, anchors `32/width`, `32/height`, `depthBias` −200
   on the two bridges only, no `glow`. Every pixel is a 2x2 block (not the rail). Alpha is 0 or 255, except
   `2a3151` at alpha 90 on the ginkgo.
2. Opaque colours are all sheet colours; at most 24 (16 for paddy, rail, bear sign); none on half (not the
   rail); none of `f6dc8c f2c66a f9c22e 2b373c 000000`; `f3d890` under 3% of opaque (not the ginkgo).
3. Every opaque pixel with a clear 4-neighbour inside the canvas is `0a1627`.
4. The tool's source has no `.polygon(`, `.ellipse(`, `.arc(`, `.pieslice(`, `.chord(`,
   `.rounded_rectangle(`, `lit_window`, `tiled_roof`, `blob(`, `trunk(`; `.line(` only inside `masonry`.
5. `chaya` untouched: sha1 of the decoded RGBA of `kanazawa-chaya-a_0_0` is
   `6809a8245bd31d6a83613a7f95bef96cb17571ae`, of `-b` `5e412fec5160dfbb6e0b4d396ba314b7ed526b38`.
6. With Pillow (skipped without): a spawned python builds every `SPRITES` entry (builder, scale) and its
   pixels equal the committed PNG's.
7. With Pillow: #384's test, for this tool: `main()` run with `SPR` pointed at a temp copy of the committed
   sprites (one removed, one overwritten, one re-encoded) leaves every file byte for byte the committed one
   and the re-encoded one alone. (`main()` rewrites `config.json` with identical content; checked.)

If `chaya` fails a rule in 1–3, scope that rule to the 19; do not redraw `chaya`.

Implementer's checks, in order:

```bash
for r in Kanazawa Shirakawago Toyama; do node tools/play.js render $r /work/media/304-before-$r.png; done
python3 tools/generate_hokuriku_art.py && python3 tools/generate_hokuriku_art.py
git status --short assets/ config.json      # 19 sprite PNGs; no chaya, no config.json
python3 tools/house_look.py --sheet /work/media/304-sheet.png --scale 2 assets/sprites/{kanazawa-ishikawa,kanazawa-kotoji,kanazawa-whisky,kanazawa-canal,kanazawa-chaya,hokuriku,shirakawa,toyama}-*.png assets/sprites/sendai-pub_0_0.png assets/sprites/sendai-maple_0_0.png
python3 tools/make_worldmap.py --pil
for r in Kanazawa Shirakawago Toyama; do node tools/play.js render $r /work/media/304-after-$r.png; done
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
  && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
python3 -m http.server 8000 &               # then, per tools/browser/README.md:
REGRESS_TIME_SCALE=2 PORT=8000 node tools/browser/regress.js
```

Look at every before/after pair and the sheet; in a browser walk the three rooms at desktop and phone size,
by day and with `?tod=night` (nothing should glow; say what was seen); ride past the tram. The summary names
any sprite that still reads flat, says whether the regression ran, and names the rooms whose pictures changed
(Kanazawa, Shirakawago, Toyama: art only, no map data). Commit as `gamev2: … (#290)`.

## Risks and open questions

- **Helpers from `generate_kanazawa_art.py`**: a later change to one of them there (#386, #300, #387 are open
  on that file) moves these PNGs; `check_generators.py` reports it as DRIFT and the fix is a rerun. The lazy
  import is the price of not moving shared code now.
- **The farmhouses lose some steepness**: showing the roof from above shortens the gable. The prototype
  (`/work/media/304-prototype-ginkgo-gassho-before-after.png`) keeps the silhouette's size and the praying-hands
  outline; if the owner wants the gable taller, lower `depth` in `thatch`.
- **The ginkgo is dim gold, not bright yellow**: the sheets have no saturated yellow. `f3d890` is one of its
  six tones, which is why test 2 exempts it; it is foliage, not a lit surface.
- **24 colours** is tight on the peak, the museum and the gate (the castle helpers alone use about 16). Trim
  accents, not ramps.
- **The peak** is the least settled: the prototype (`/work/media/304-prototype-peak.png`) proves the palette and
  the masked `foliage` forest, but its rock was noisy and its tree line wrong; the table row above says what to
  do instead. Judge it in the Shirakawago render, where five overlap.
- `kanazawa-ishikawa-gate` and `kanazawa-kotoji` are placed today and so are redrawn, though #219's own
  castle pieces may replace them later.
- The Kansai tool still imports this file's old off-sheet colours; they stay until that tool is redrawn.

## Appendix: prototyped builders

Run and looked at (`R(im, x0, y0, x1, y1, c)` is `hl.fill(im, (x0, y0, x1, y1), c)`). Ginkgo: 10 colours;
farmhouses: 18 colours each, largest share 33%.

```python
K_GINKGO = [rgb(c) for c in ('ffecb8', 'f3d890', 'c6a663', 'a7843b', '86624f', '5b283b')]
K_THATCH = [rgb(c) for c in ('be9e8c', 'a68777', '8e7366', '775d4e', '6b5241', '584a43')]
K_TB, K_TB_HI, K_TB_LO, K_TB_DK = rgb('71412a'), rgb('aa775f'), rgb('5a3827'), rgb('3f210f')


def ginkgo():
    im, d = canvas(2, 3)                 # 64 x 96
    ground_shade(d, 33, 88, 16)
    stem(d, 30, 58, 92, 5)
    limb(d, 31, 70, 22, 58); limb(d, 33, 68, 43, 56)
    foliage(im, [(21, 54, 12, 10), (44, 52, 12, 10), (32, 44, 16, 11), (24, 33, 13, 10), (41, 31, 13, 10),
                 (32, 22, 12, 10), (32, 11, 8, 8)], K_GINKGO, 4)
    px = im.load()
    for x, y in ((20, 90), (25, 92), (41, 90), (46, 92), (38, 91)):   # fallen leaves, on the shade
        px[x, y] = K_GINKGO[1]; px[x + 1, y] = K_GINKGO[3]
    hl.outline(im)
    return im


def thatch(im, cw, ch):
    """A gassho roof seen from above and in front: the ridge runs back `depth` rows from
    the gable, the west slope lit and the east in shade, the thatch combed down each, its
    thick cut edge over the gable and along the eaves. Returns (g0, eave, half): the
    gable's peak row, the eave row and the half-width at the eave."""
    px = im.load()
    W, H = cw * 32, ch * 32
    cx, half, depth = W // 2, W // 2 - 2, 22 + 2 * cw
    apex, eave = 5, H - 42
    g0, rise = apex + depth, eave - apex - depth
    T = K_THATCH
    for y in range(apex, eave + 1):
        wo = min(half, (y - apex) * half // rise)                  # the silhouette's half-width
        wi = (y - g0) * half // rise if y >= g0 else -1            # the gable's
        for x in range(cx - wo, cx + wo):
            west = x < cx
            dx = cx - 1 - x if west else x - cx                    # columns out from the ridge
            if dx < wi:
                continue                                           # the gable wall, below
            k = wo - dx                                            # columns in from the verge
            if west:
                c = T[0] if k < 2 or (k % 6 == 0 and speck(x, y // 3, 1) < 45) else (T[2] if k % 6 == 5 else T[1])
            else:
                c = T[4] if k < 2 or k % 6 == 5 else (T[2] if k % 6 == 2 and speck(x, y // 3, 2) < 35 else T[3])
            if 0 <= dx - wi < 5 and wi >= 0:                       # the cut edge over the gable, in layers
                j = dx - wi
                c = T[5] if j in (0, 4) or (y + j) % 4 == 0 else (T[2] if west and j == 2 and y % 4 == 2 else
                                                                 T[3] if west and j == 2 else T[4])
            px[x, y] = c
    for y in range(eave + 1, eave + 7):                            # the eaves' cut ends
        for x in list(range(cx - half, cx - half + 14)) + list(range(cx + half - 14, cx + half)):
            px[x, y] = T[5] if y >= eave + 5 or (x + y) % 3 == 0 else T[4]
    R(im, cx - 4, apex - 3, cx + 3, g0 + 2, T[2])                  # the ridge, and the bundles lashed over it
    R(im, cx - 4, apex - 3, cx - 3, g0 + 2, T[0]); R(im, cx + 2, apex - 3, cx + 3, g0 + 2, T[4])
    for y in range(apex, g0 + 1, 5):
        R(im, cx - 6, y, cx + 5, y + 1, T[1]); R(im, cx - 6, y + 2, cx + 5, y + 2, T[5])
        R(im, cx - 6, y, cx - 5, y + 1, T[0]); R(im, cx + 4, y, cx + 5, y + 1, T[3])
    for y in range(g0 + 1, eave + 1):                              # the gable's boards
        w = (y - g0) * half // rise
        for x in range(cx - w, cx + w):
            px[x, y] = K_TB_DK if x < cx - w + 3 else (K_TB_LO if (x - cx) % 5 == 0 or x >= cx + w - 3 else K_TB)
    return g0, eave, half
```

`gassho(cw, ch)` after `thatch`, as prototyped: shoji tiers of 1, 2, 3, 4 at y = `g0 + 14, 33, 52, 71`
(a tier is skipped when `y + 13 > eave - 3`), each window 10x13 at 13 pitch, centred: frame `K_TB_DK`, paper
`e4cecc`, top row `be9e8c`, left column `fafcfd`, a 2-wide mullion and a transom in `K_TB_LO`; over each tier
a beam (`K_TB_HI` row on two `K_TB_DK` rows) 5 short of the gable's edge each side. Ground floor
`eave + 1..H - 6`, x 14..W−15: `K_TB` boards with a `K_TB_LO` line every 5 columns, 3 rows of `K_TB_DK` eave
shadow, lit west column, 4 shaded east columns. Doorway `cx − 13..cx + 12` framed `K_TB_DK`, glass `2c2d51`
under a `2a3151` head, two leaves of `bars(…, K_TB_LO, glass, 3)` over 6-row kick boards. Shoji screens 22
wide at x = 20 and W−42, from `eave + 9` to `H − 14`, with a mullion every 5 columns and a transom. Stone foot
`53596d`, top row `848295`, joints `2e4040` every 12 columns. Then `hl.outline`.
