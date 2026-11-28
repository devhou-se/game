# 385: Kanazawa's castle walls, gate, turret, storehouse and the Tsuzumi-mon in the house look

Part 1 of 3 of #312. All paths are under `gamev2/`; commands run from `gamev2/`. Coordinates are the tool's
half-size pixels (32 a cell), y from the top.

## Context

`tools/generate_kanazawa_art.py` draws nine sprites this ticket redraws in the GuttyKreum house look
("House look: GuttyKreum" in `docs/generators-and-checks.md`, helpers in `tools/house_look.py`):

| Key (`assets/sprites/<key>.png`) | Cells | Drawn by today | Now: colours / not in a sheet |
|---|---|---|---|
| `kanazawa-castle-gate_0_0` | 4x4 | `castle_gate()` | 28 / 19, and 1200 half-clear pixels (the passage shadow) |
| `kanazawa-castle-turret_0_0` | 4x5 | `castle_turret()` | 30 / 24 |
| `kanazawa-castle-storehouse_0_0` | 6x3 | `castle_storehouse()` | 32 / 25 |
| `kanazawa-castle-wall_0_0`, `-wall-corner-e`, `-wall-corner-w`, `-wall-v`, `-wall-end` | 1x2 each | `wall('castle', kind)` | 15 to 19 / 11 to 15 |
| `kanazawa-tsuzumi-gate_0_0` | 6x5 | `tsuzumi_gate()`, `drum_pillar()` | 10 / 6 |

What is wrong with them: the three buildings have a flat front-elevation roof (the trapezoid of `roof()`), the
turret's hood and gable are a `chord`, `arc`s and a `polygon`, the Tsuzumi roof is a slab in perspective, the
palette is the tool's own (`LEAD_P`, `PLASTER*`, `TIMBER*`, `SOOT`, `STONES`), and the gate blends a
translucent shadow.

Found while designing:

- **None of the nine is registered or placed**: no key is in `config.json`, `tiled/`, `src/` or another tool,
  and `check_generators.py` does not run this tool. So no room render, world map, `play.js` output or in-game
  `?tod=night` view changes; the pictures to look at are the tool's own `--sheet` and `--scenes` (the `castle`
  and `station` scenes and their `_night.png`).
- `wall()` also draws the seven `nagamachi-wall*` sprites (#300), through `_naga_coping`, `_naga_face`,
  `komo_mats`, `_fall`, `_v_coping`; `barred()` and `roof()` are used by `samurai_gate` and others, and
  `roof`/`shade`/`curve_rows`/`night`/`h3`/`text` are imported by three other tools. `stonework()`, `namako()`,
  `STONES`, `LEAD_P`, `_castle_coping`, `_castle_face` and `drum_pillar()` are used by these nine only.
- Rerunning the tool rewrites about 50 other PNGs with the same pixels and a different encoding (#384).
- A design-stage prototype (the code in the appendix) was run through the tool's own scenes. Images on the
  ticket: `385-castle-scene-before-after.png`, `385-tsuzumi-gate-before-after.png`,
  `385-castle-scene-night-prototype.png`, `385-prototype-gate-turret-storehouse.png`,
  `385-prototype-walls-tsuzumi.png`. It gives 11 to 23 colours a sprite, all sheet colours, no half-clear
  pixel, and leaves every other sprite and scene of the tool pixel-identical.

## Approach

Redraw the nine in place, same keys, canvases, anchors and cells, with **the appendix's code as the starting
point** (it is the prototype, already in the tool's names). The implementer looks at the result beside the
sheets and adjusts tones or details; the rules below and the tests are what must hold.

1. **Split the wall code rather than branch it.** A new `castle_wall(kind)` draws the five castle pieces with
   its own helpers; `wall()` loses its castle arms and stays Nagamachi's alone. `_fall`, `_v_coping`,
   `_naga_coping`, `_naga_face`, `komo_mats`, `barred`, `roof`, `cobbles`, `shade` are not edited, so
   `nagamachi-wall*` cannot move; a test holds them to the tool.
2. **Roofs are seen from above** (the hip roof of `fukuoka-kushida-hall`, #350, in rectangles and pixels only):
   `lead_hip()` draws a ridge bar at the back, the front slope between two hips that run to the eave's
   corners, the hip ends beside them (west lit, east in shade, tiles running down them) and a three-row eave
   lip. Tiles are the pack's kawara pattern, `generate_sendai_art.roof_tile(x, y, tones)`, in three lead tone
   sets from the steel ramp. Wall copings and the storehouse's door hood are straight bands of the same tile
   (`lead_band()`); a north-south coping is the same tile turned (`_lead_fall()`).
3. **The wall family keeps its rows**, so pieces join each other and the gate as they do now: coping rows
   12-24 with the shadow row 25, plaster 26-35, namako 36-47, row 48, stone 49-63; a north-south coping is
   x 2-29 with its ridge at x 15-16; the south end face is x 5-26 from row 32. Periods stay 32 in x (tile 4,
   namako 8, stone 32) and 4 down a north-south coping.
4. **Materials** (palette block in the appendix; every hex is a sheet colour):
   - lead: `a4b0b5` base, `949bb2` shade, `d1e2eb` lit lip, `848295` joint, `575f79` course line; lit fall
     one step lighter (`bcc7cc`, lip `fafcfd`), shaded fall one step darker (`848295`, course `47485d`);
   - plaster: `fafcfd`, `e4cecc` on the east end and under an eave (one `be9e8c` row, one `e4cecc` row, one
     dithered row);
   - namako: joints `fafcfd` raised over `47485d` slate, each joint's shadow `2a2636` on the tile;
   - Tomuro stone: `a4b0b5`/`bcc7cc` blocks with the odd `e4cecc` (red) and `d1e2eb`/`949bb2` (blue) one,
     `fafcfd` lit top, `848295` joints;
   - musha-mado: an opening `2c2d51` with a `2a3151` head row behind plaster bars. It is unglazed, so it has
     no glare and nothing to light at night; no `lit` is added to any `PIECES` row;
   - timber `71412a` / `aa775f` / `5a3827` / `3f210f`, iron `2a2636` with `848295` studs, the plum crest in
     the pack's dim gold `c6a663` with one `f3d890` pixel;
   - Tsuzumi timber `ab7656` / `c18e75` / `904a37` / `5a3827`, coffers `4d3326` / `312522`.
5. **Outline**: `hl.outline(im)` last in every builder (ink `0a1627`), nothing drawn after it. The gate's
   passage shadow becomes an opaque soffit (rows 88-92, above the walk cells' row), so there is no blended
   pixel. One clear row is left between an eave lip and the wall under it; `outline` inks it.
6. **Shapes without curves or slopes**: the turret's bowed hood and its gable are stepped rows; its battered
   base is a per-row inset; the Tsuzumi roof is a straight slab seen from above (x 3-188, y 4-47), beams on an
   8px grid lit on their north and west edges over dark coffers, a fascia of beam ends (48-56) and a shaded
   underside (57-58); the drums keep their profile, cells (cx 48 and 144, y 63-150) and plinths.

Per sprite (boxes are in the appendix; these are what a reviewer should see):

| Sprite | Picture |
|---|---|
| castle gate | piers flush to x 0 and 127 (the wall joins), reveals shaded west / lit east; gatehouse plaster 44-62 with three musha-mado, namako 63-73, sill beam 74-77; `lead_hip(im, 1, 126, 12, 39, 24, 9)`; lintel with studs and the crest, iron-bound posts, folded leaves, soffit |
| turret | battered base 118-157 with its east arris in shade; first storey 79-101, namako 102-112, sill 113-117, the bay (x 46-81) under a stepped hood (rows 79-88); skirt roof `lead_hip(im, 2, 125, 66, 74, 18, 4, caps=False)`; second storey 42-65; top roof `lead_hip(im, 11, 116, 13, 37, 30, 9)` with a stepped plaster gable (rows 22-37) |
| storehouse | stone foot 78-95; plaster 36-59 with five musha-mado, namako 60-70, sill 74-77; the iron-bound door in column 2 (x 65-94) under a `lead_band` hood; `lead_hip(im, 1, 190, 9, 31, 18, 8)` |
| wall `h` | `lead_band` coping, plaster, namako, stone, edge to edge |
| wall `v` / `end` | the coping from above over rows 0-31 (lit fall x 3-14, ridge 15-16, shaded fall 17-28), the south end face below; `end` hips the coping over rows 18-29 with an eave on 30-31 |
| wall `corner-e` / `-w` | the east-west coping and face stopped at long-and-short corner stones (shaded east, lit west), the coping turning north over a one-in-one hip on rows 12-25 |
| Tsuzumi gate | as rule 6 |

## Changes

### `tools/generate_kanazawa_art.py`

- **Replace** `STONES`, `stonework()` and `namako()` (now before the Station section) with the appendix's
  palette block (`C_*`), `rect()`, `lead_band()`, `lead_hip()`, `plaster()`, `musha()`, `namako()`,
  `stonework()`, `sill_beam()`, `iron_post()`. They sit there so `drum_pillar()` finds `C_ST*` and `rect`
  defined above it. `namako` and `stonework` keep their names and take `im` instead of `d`.
- **Replace** `drum_pillar()` and `tsuzumi_gate()` in place, with the `TS_*` block above `drum_pillar`.
  `drum_pillar` now takes `im`; its only callers are in `tsuzumi_gate`.
- **Replace** `castle_gate()`, `castle_turret()`, `castle_storehouse()` in place.
- **Replace** `_castle_coping()` and `_castle_face()` with `_lead_fall()`, `_lead_v_coping()` and
  `castle_wall(kind)`.
- **`wall(style, kind)`**: delete only the castle arms (`castle`, the `if castle:` halves of `face` and
  `end_face`, the corner stones' `if castle:` block, so `elif east:` becomes `if east:`); `coping` is
  `_naga_coping`, `pal` is `SHINGLE_P`, `top` is 15. Its docstring loses "plaster, namako and stone; or".
  No other line of it changes.
- **Delete** `LEAD_P`.
- **`PIECES`**: the five castle wall rows call `castle_wall('h')`, `('corner-e')`, `('corner-w')`, `('v')`,
  `('end')`. Sizes and `solid` / `walk` / `door` stay. Descriptions: the gate's "a pale lead-tile roof"
  becomes "a hipped lead-tile roof seen from above"; say the same of the turret's two roofs and the
  storehouse's; nothing else.
- **Do not change**: `text`, `kana`, `text_w`, `h3`, `shade`, `curve_rows`, `roof`, `night`, `FONT`, `KANA`
  (other tools import them), `barred`, `cobbles`, `paper_lantern`, `_naga_coping`, `_naga_face`, `komo_mats`,
  `_fall`, `_v_coping`, every other builder, the `H_*` block, `FAMILIES`, `sheet()`, `scenes()`, `main()`.

### `assets/sprites/`

The nine PNGs above, rewritten by the tool. Nothing else: after running the tool, `git checkout --` every
other PNG it touched (#384).

### `tools/tests/kanazawa-art.test.js`

The tests below, beside #307's, reusing its `load`, `hex` and `sheets`. The file's header comment gains a line
for #385.

### `docs/generators-and-checks.md`

One sentence after the paragraph on Kanazawa's ten fronts: the castle's gate, turret, storehouse and five
wall pieces and the Tsuzumi-mon (#385, part of #312) are drawn the same way, their roofs hipped and seen
from above in the pack's tile, and held by the same test file.

## Data and interfaces

None. No key, size, anchor, `solid` / `walk` / `door` cell, `config.json`, `tiled/` map, palette index or
`devhouse.world` entry changes, so no room is touched. `stonework`, `namako` and `drum_pillar` change their
first argument from `d` to `im`; nothing outside this tool imports them.

## Tests

Add to `tools/tests/kanazawa-art.test.js` (names end `(#385)`; `CASTLE` maps the nine keys to their cells,
`WALLS` is the five 1x2 keys, `NAGA` the seven `nagamachi-wall*` keys):

1. **Sizes**: each of the nine is cells x 64, every pixel a 2x2 block, alpha 0 or 255.
2. **Colours**: only sheet colours; at most 16 for `WALLS`, 24 for the other four; none on more than half
   the opaque pixels; none of `f6dc8c`, `f2c66a`, `f9c22e`, `2b373c`, `000000`; `f3d890` under 3%.
3. **Silhouette**: every opaque pixel with a clear 4-neighbour inside the canvas is `0a1627`. (The canvas edge
   does not count as clear: wall pieces and the gate's piers run to it so that they join.)
4. **Joins** (committed PNGs, doubled pixels): column 0 of `-corner-e` equals column 0 of the `h` piece on
   rows 22-127, and column 63 of `-corner-w` equals its column 63; rows 0-35 and 64-127 of `-end` equal
   `-v`'s; rows 0-21 of both corners equal `-v`'s.
5. **Rectangles and pixels only**: the source of `castle_gate`, `castle_turret`, `castle_storehouse`,
   `castle_wall`, `tsuzumi_gate`, `drum_pillar`, `lead_band`, `lead_hip`, `plaster`, `musha`, `namako`,
   `stonework` (cut as #307's test cuts a builder) has none of `.polygon(`, `.ellipse(`, `.arc(`,
   `.pieslice(`, `.chord(`, `.line(`, `shade(im`, and no `/\broof\(/`.
6. **The tool draws what is committed**: #307's rebuild snippet over the nine keys and `NAGA` (skips without
   Pillow). For `NAGA` this is the guard that the split left Nagamachi's walls alone.

The implementer, in order:

```bash
mkdir -p /tmp/385/before && cp assets/sprites/kanazawa-castle-*.png assets/sprites/kanazawa-tsuzumi-gate_0_0.png \
    assets/sprites/nagamachi-wall*.png /tmp/385/before/
python3 tools/generate_kanazawa_art.py --sheet /tmp/385/before/sheet.png --scenes /tmp/385/before/scenes
git checkout -- assets/sprites                        # before any edit: the "before" pictures
# ... edit the tool ...
python3 tools/generate_kanazawa_art.py --sheet /tmp/385/sheet.png --scenes /tmp/385/scenes
git status --short assets/sprites                     # then git checkout -- every PNG that is not one of the nine
python3 tools/house_look.py --sheet /tmp/385/contact.png --scale 2 assets/sprites/kanazawa-castle-*.png \
    assets/sprites/kanazawa-tsuzumi-gate_0_0.png
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
    && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

- Compare each `nagamachi-wall*` PNG with `/tmp/385/before/` by decoded pixels (Pillow `tobytes()`): all seven
  equal. `kanazawa_art_nagamachi.png`, `_chaya`, `_katamachi`, `_kenrokuen` and their nights are also
  pixel-equal before and after.
- Look at `/tmp/385/scenes/kanazawa_art_castle.png` and `_station.png` beside the "before" ones, at their
  `_night.png` (no window may glow), and at the contact sheet beside a done model
  (`fukuoka-kushida-hall_0_0.png`, `sendai-earthen-wall_0_0.png`). Save before/after images to `/work/media/`
  and name in the summary any sprite that still reads flat.
- `git status` shows only the tool, the nine PNGs, the test file and the doc. No town's picture changes, so
  `check_generators.py` reports no drift and the world map is not rebuilt.
- The browser regression (`tools/browser/regress.js`) cannot see these sprites, since no room places them:
  run it as the house rule asks, or say it was not run and why. There is no in-game `?tod=night` view of them
  either; the tool's night scenes are the check.
- Commit as `gamev2: ... (#385)`; rooms touched: none.

## Risks and open questions

- **Same file as #300, #386, #387** (Nagamachi walls, Kenrokuen, the rest of the station front): touch only
  what Changes lists, and rebase before committing. If #300 has already rewritten `wall()`, drop whatever
  castle arms remain and keep `castle_wall` separate. #387 is told to leave `drum_pillar` alone.
- **Taste calls made in the prototype**, all in the palette block or one call's arguments: the lead reads
  bluer and darker than the old pale grey (lighten by moving each `C_LEAD*` set one step up the steel ramp);
  the Tsuzumi roof is a plain rectangle, no longer tapered; the stone has one red block in seven.
- **`drum_pillar` still places its timbers with `math.sin` / `cos` and `round`**, as it does today. A
  platform whose libm differs in the last bit could move a pixel and fail test 6; if that ever shows, turn the
  two timber families into a table of x per row.
- **`roof_tile` belongs to `generate_sendai_art.py`** (already imported here; #307's fronts reach it through `kawara`): a
  change to its pattern would redraw these roofs, and test 6 would say so.
- **Night is only previewed in Pillow** (`night()` in the tool); the game judges once a ticket places the
  sprites. Nothing here has a lamp or a lit window, so `Glows` has nothing to add.
- `samurai_gate` keeps the old `barred()` and `roof()`; it is not in this ticket.

## Appendix: the prototype's drawing code

Run through the tool as written here (with `CLEAR`, `rgb`, `canvas`, `roof_tile`, `hl`, `math` as the tool
already imports them). `im, d = canvas(w, h)` is the tool's; `d` is unused by the new builders.

```python
# ---- the castle's colours: every one a GuttyKreum sheet colour ---------------------------
# lead tiles in roof_tile's order: course line, joint, lit lip, shade, base
C_LEAD = [rgb(c) for c in ('575f79', '848295', 'd1e2eb', '949bb2', 'a4b0b5')]
C_LEAD_LIT = [rgb(c) for c in ('646e86', '949bb2', 'fafcfd', 'a4b0b5', 'bcc7cc')]      # a fall facing west
C_LEAD_SH = [rgb(c) for c in ('47485d', '575f79', '949bb2', '646e86', '848295')]       # a fall facing east
C_RIDGE, C_RIDGE_HI, C_EAVE, C_EAVE_DK = rgb('a4b0b5'), rgb('dae2e4'), rgb('646e86'), rgb('47485d')
C_PL, C_PL_LO, C_PL_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('be9e8c')    # white plaster, its shade, an eave's shadow on it
C_NK, C_NK_LO = rgb('47485d'), rgb('2a2636')                            # namako slate
C_DARK, C_DARK_LO = rgb('2c2d51'), rgb('2a3151')                        # an opening: never lit
C_ST = [rgb(c) for c in ('bcc7cc', 'a4b0b5', 'd1e2eb', 'bcc7cc', 'e4cecc', 'a4b0b5', '949bb2')]   # Tomuro stone, the odd red and blue block
C_ST_HI, C_ST_LO, C_ST_JOINT, C_ST_DK = rgb('fafcfd'), rgb('949bb2'), rgb('848295'), rgb('646e86')
C_TB, C_TB_HI, C_TB_LO, C_TB_DK = rgb('71412a'), rgb('aa775f'), rgb('5a3827'), rgb('3f210f')
C_IRON, C_IRON_HI, C_SOFFIT = rgb('2a2636'), rgb('848295'), rgb('191c2a')
C_GILT, C_GILT_HI = rgb('c6a663'), rgb('f3d890')


def rect(im, x0, y0, x1, y1, c):
    hl.fill(im, (x0, y0, x1, y1), c)


def lead_band(im, x0, y0, x1, y1, ridge=3):
    """A straight band of lead tiles: a ridge course of `ridge` rows, the tiles, a dark eave of two."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = roof_tile(x, y - y0 - ridge, C_LEAD)
    rect(im, x0, y0, x1, y0 + ridge - 1, C_RIDGE)
    rect(im, x0, y0, x1, y0, C_RIDGE_HI)
    rect(im, x0, y0 + ridge - 1, x1, y0 + ridge - 1, C_EAVE)
    rect(im, x0, y1 - 1, x1, y1 - 1, C_EAVE)
    rect(im, x0, y1, x1, y1, C_EAVE_DK)


def lead_hip(im, x0, x1, top, eave, run, side_rows, caps=True):
    """A hipped lead roof seen from above. The ridge bar is the 4 rows above `top`,
    `run` in from either end; the front slope falls from `top` to `eave` between two
    hips that reach the eave's corners; outside them the hip ends (the west lit, the
    east in shade, their tiles running down them) widen to the full width in
    `side_rows` rows; an eave lip of 3 rows lies under `eave`."""
    px = im.load()
    n = eave - top
    for y in range(top, eave + 1):
        hip = (y - top) * run // n
        side = min(run, (y - top) * run // side_rows)
        hw, he, ow, oe = x0 + run - hip, x1 - run + hip, x0 + run - side, x1 - run + side
        for x in range(ow, oe + 1):
            if x < hw - 1:
                c = roof_tile(y - top, x - ow, C_LEAD_LIT)
            elif x > he + 1:
                c = roof_tile(y - top, oe - x, C_LEAD_SH)
            elif x <= hw + 1:
                c = C_LEAD_LIT[2] if x <= hw else C_LEAD[0]            # the west hip's cap, lit
            elif x >= he - 1:
                c = C_LEAD[2] if x == he - 1 else (C_LEAD_SH[0] if x == he + 1 else C_LEAD_SH[1])
            else:
                c = roof_tile(x, y - top, C_LEAD)
                if x > he - 9 and c == C_LEAD[4]:
                    c = C_LEAD[3]                                      # the slope's east end turns from the light
            px[x, y] = c
    rect(im, x0, eave + 1, x1, eave + 1, C_LEAD[2])
    rect(im, x0, eave + 2, x1, eave + 2, C_EAVE)
    rect(im, x0, eave + 3, x1, eave + 3, C_EAVE_DK)
    a, b = x0 + run - 2, x1 - run + 2
    rect(im, a, top - 4, b, top - 1, C_RIDGE)
    rect(im, a, top - 4, b, top - 4, C_RIDGE_HI)
    rect(im, a, top - 1, b, top - 1, C_LEAD[0])
    for x in range(a + 3, b - 1, 6):
        rect(im, x, top - 3, x, top - 2, C_LEAD[1])
    if caps:                                                           # an end tile either end of the ridge
        for cx in (a - 4, b - 1):
            rect(im, cx, top - 6, cx + 5, top, C_LEAD[4])
            rect(im, cx, top - 6, cx, top, C_LEAD_LIT[2])
            rect(im, cx + 1, top - 6, cx + 5, top - 6, C_LEAD_LIT[2])
            rect(im, cx + 5, top - 5, cx + 5, top, C_EAVE)


def plaster(im, x0, y0, x1, y1, east=6):
    """White plaster: the eave's shadow along its top (one row, a lighter row, a dithered
    row), its `east` end columns turned from the light."""
    rect(im, x0, y0, x1, y1, C_PL)
    rect(im, x1 - east + 1, y0, x1, y1, C_PL_LO)
    rect(im, x0, y0, x1, y0, C_PL_SH)
    rect(im, x0, y0 + 1, x1, y0 + 1, C_PL_LO)
    px = im.load()
    for x in range(x0, x1 - east + 1):
        if (x + y0) % 2:
            px[x, y0 + 2] = C_PL_LO


def musha(im, x0, y0, x1, y1):
    """A musha-mado: a dark opening behind stout plaster bars. No glass, so no glare, and never lit."""
    rect(im, x0 - 1, y0 - 1, x1 + 1, y1 + 1, C_PL_SH)
    rect(im, x0, y0, x1, y1, C_DARK)
    rect(im, x0, y0, x1, y0, C_DARK_LO)
    for x in range(x0 + 2, x1, 4):
        rect(im, x, y0, x, y1, C_PL)
        rect(im, x, y0, x, y0, C_PL_LO)
    rect(im, x0 - 1, y1 + 1, x1 + 1, y1 + 1, C_PL)                     # the sill, lit


def namako(im, x0, y0, x1, y1, shade_from=None):
    """Namako-kabe: slate tiles set on the diagonal, their joints raised in white
    plaster (period 8 in x), each joint's shadow on the tile below and east of it."""
    px = im.load()
    for y in range(y0, y1 + 1):
        v = y - y0
        for x in range(x0, x1 + 1):
            a, b = (x + v) % 8, (x - v) % 8
            if v == 0 or y == y1 or a == 0 or b == 0:
                c = C_PL_LO if y == y1 or (shade_from is not None and x >= shade_from) else C_PL
            else:
                c = C_NK_LO if a == 7 or b == 1 else C_NK
            px[x, y] = c


def stonework(im, x0, y0, x1, y1, seed=0, ch=8):
    """Kanazawa Castle's fitted Tomuro stone in courses of `ch`: pale grey with the odd
    red and blue block, each block lit along its top, its joints below and to the east.
    Period 32 in x, so runs of wall tile."""
    px = im.load()
    for y in range(y0, y1 + 1):
        j, yy = (y - y0) // ch, (y - y0) % ch
        off = (j * 13 + seed * 7) % 32
        for x in range(x0, x1 + 1):
            u = (x - off) % 32
            seg = 2 if u >= 21 else (1 if u >= 11 else 0)
            if u in (0, 11, 21) or yy == ch - 1:
                c = C_ST_JOINT
            elif yy == 0:
                c = C_ST_HI
            elif u in (10, 20, 31):
                c = C_ST_LO
            else:
                c = C_ST[(seg * 3 + j * 5 + ((x - off) // 32) * 2 + seed) % 7]
            px[x, y] = c


def sill_beam(im, x0, y0, x1, y1):
    rect(im, x0, y0, x1, y1, C_TB_LO)
    rect(im, x0, y0, x1, y0, C_TB_HI)
    rect(im, x0, y1, x1, y1, C_TB_DK)


def iron_post(im, x0, y0, x1, y1, bands):
    rect(im, x0, y0, x1, y1, C_TB)
    rect(im, x0, y0, x0, y1, C_TB_HI)
    rect(im, x1 - 1, y0, x1, y1, C_TB_LO)
    for y in bands:
        rect(im, x0, y, x1, y + 2, C_IRON)
        rect(im, x0 + 2, y + 1, x0 + 2, y + 1, C_IRON_HI)
        rect(im, x1 - 2, y + 1, x1 - 2, y + 1, C_IRON_HI)


def castle_gate():
    im, d = canvas(4, 4)                 # 128 x 128; the gateway is columns 1-2 (x 32-95)
    # ---- the stone piers, flush to the canvas so the wall joins them
    stonework(im, 0, 78, 33, 127, 1)
    stonework(im, 94, 78, 127, 127, 4)
    rect(im, 29, 78, 33, 127, C_ST_JOINT); rect(im, 29, 78, 29, 127, C_ST_LO)      # the west pier's reveal, in shade
    rect(im, 94, 78, 95, 127, C_ST_HI)                                             # the east pier's, lit
    rect(im, 0, 78, 33, 78, C_ST_DK); rect(im, 94, 78, 127, 78, C_ST_DK)           # the gatehouse's shadow
    # ---- the gatehouse: white plaster, barred openings, a namako dado, the sill beam on the stone
    plaster(im, 3, 44, 124, 62, east=8)
    musha(im, 12, 50, 31, 58); musha(im, 46, 50, 81, 58); musha(im, 96, 50, 115, 58)
    namako(im, 3, 63, 124, 73, shade_from=117)
    sill_beam(im, 2, 74, 125, 77)
    lead_hip(im, 1, 126, 12, 39, 24, 9)
    # ---- the gateway: a lintel with the plum crest, iron-bound posts, the leaves folded back
    rect(im, 34, 78, 93, 87, C_TB)
    rect(im, 34, 78, 93, 78, C_TB_DK); rect(im, 34, 79, 93, 79, C_TB_HI); rect(im, 34, 86, 93, 87, C_TB_LO)
    for x in range(40, 90, 8):
        if x != 64:
            rect(im, x, 82, x + 1, 84, C_IRON); rect(im, x, 82, x, 82, C_IRON_HI)
    for x, y in ((64, 80), (62, 82), (66, 82), (63, 84), (65, 84)):
        rect(im, x, y, x, y, C_GILT)
    rect(im, 64, 82, 64, 82, C_GILT_HI)
    iron_post(im, 34, 88, 41, 127, (94, 108, 121))
    iron_post(im, 86, 88, 93, 127, (94, 108, 121))
    for x0 in (42, 80):
        rect(im, x0, 88, x0 + 5, 126, C_TB_DK)
        rect(im, x0 + 2, 90, x0 + 2, 125, C_TB_LO)
        for y in range(92, 124, 6):
            rect(im, x0 + 4, y, x0 + 4, y, C_IRON_HI)
    rect(im, 48, 88, 79, 92, C_SOFFIT)                                             # the passage's ceiling: opaque
    rect(im, 48, 88, 79, 88, C_IRON)
    hl.outline(im)
    return im


def castle_turret():
    im, d = canvas(4, 5)                 # 128 x 160
    px = im.load()
    # ---- the battered stone base
    stonework(im, 2, 118, 125, 157, 2)
    for y in range(118, 158):
        inset = 9 * (157 - y) // 39
        for x in list(range(2, 2 + inset)) + list(range(126 - inset, 126)):
            px[x, y] = CLEAR
        px[2 + inset, y] = C_ST_HI
        for x in range(119 - inset, 126 - inset):                                  # the east arris, turned from the light
            if px[x, y] != C_ST_JOINT:
                px[x, y] = C_ST[1] if px[x, y] == C_ST_HI else C_ST_LO
    rect(im, 2, 158, 125, 159, C_ST_JOINT)
    rect(im, 11, 118, 116, 118, C_ST_DK)
    # ---- the first storey, its bay window
    plaster(im, 13, 79, 114, 101, east=8)
    musha(im, 20, 88, 39, 96); musha(im, 88, 88, 107, 96)
    namako(im, 13, 102, 114, 112, shade_from=107)
    sill_beam(im, 12, 113, 115, 117)
    rect(im, 46, 89, 81, 112, C_PL); rect(im, 79, 89, 81, 112, C_PL_LO)
    rect(im, 46, 89, 81, 89, C_PL_SH); rect(im, 46, 90, 81, 90, C_PL_LO)
    musha(im, 51, 94, 76, 104)
    rect(im, 46, 109, 81, 112, C_PL_LO); rect(im, 46, 112, 81, 112, C_PL_SH)
    rect(im, 82, 90, 83, 112, C_PL_SH)                                             # the bay's shadow on the wall
    # ---- the lower roof, a skirt round the second storey; the bay's bowed hood breaks through its eave
    lead_hip(im, 2, 125, 66, 74, 18, 4, caps=False)
    for i, (xa, xb) in enumerate(((57, 70), (51, 76), (47, 80), (44, 83)) + ((43, 84),) * 6):
        for x in range(xa, xb + 1):
            lit = i == 0 or (i < 4 and x <= xa + 1)
            px[x, 79 + i] = C_LEAD_LIT[2] if lit else (
                C_LEAD[1] if (x - 43) % 6 == 3 else (C_LEAD[3] if x > 76 else C_LEAD[4]))
    rect(im, 43, 87, 84, 87, C_EAVE); rect(im, 43, 88, 84, 88, C_EAVE_DK)
    # ---- the second storey
    plaster(im, 27, 42, 100, 65, east=7)
    musha(im, 35, 49, 50, 57); musha(im, 56, 49, 71, 57); musha(im, 77, 49, 92, 57)
    rect(im, 27, 62, 93, 65, C_PL_LO); rect(im, 94, 62, 100, 65, C_PL_SH)
    # ---- the top roof, a plastered gable in its front slope: stepped rows
    lead_hip(im, 11, 116, 13, 37, 30, 9)
    for i in range(15):
        y, w = 22 + i, i + 2
        rect(im, 64 - w, y, 63 + w, y, C_LEAD[0] if i < 2 else C_PL)
        rect(im, 64 - w, y, 65 - w, y, C_LEAD_LIT[2])
        rect(im, 62 + w, y, 63 + w, y, C_LEAD_SH[0])
        if i >= 2:
            rect(im, 66 - w, y, 66 - w, y, C_PL_SH)
    rect(im, 47, 37, 80, 37, C_LEAD[0])
    rect(im, 62, 30, 65, 35, C_DARK); rect(im, 62, 30, 65, 30, C_DARK_LO)
    hl.outline(im)
    return im


def castle_storehouse():
    im, d = canvas(6, 3)                 # 192 x 96; the door is column 2 (x 64-95)
    stonework(im, 2, 78, 189, 95, 5)
    rect(im, 182, 78, 189, 95, C_ST_LO)
    rect(im, 182, 86, 189, 86, C_ST_JOINT)
    rect(im, 2, 78, 189, 78, C_ST_DK)
    plaster(im, 4, 36, 187, 59, east=8)
    for x0 in (12, 38, 106, 132, 158):
        musha(im, x0, 46, x0 + 19, 54)
    namako(im, 4, 60, 187, 70, shade_from=180)
    rect(im, 4, 71, 187, 73, C_PL_LO)
    sill_beam(im, 3, 74, 188, 77)
    # ---- the door: iron-bound leaves under a little lead hood
    rect(im, 65, 52, 94, 95, C_TB_DK)
    rect(im, 67, 55, 92, 95, C_TB)
    rect(im, 67, 55, 67, 95, C_TB_HI); rect(im, 79, 55, 79, 95, C_TB_DK); rect(im, 80, 55, 80, 95, C_TB_HI)
    rect(im, 91, 55, 92, 95, C_TB_LO)
    for y in (61, 75, 88):
        rect(im, 67, y, 92, y + 2, C_IRON)
        for x in (70, 76, 83, 89):
            rect(im, x, y + 1, x, y + 1, C_IRON_HI)
    lead_band(im, 61, 44, 98, 51, ridge=2)
    rect(im, 62, 52, 97, 52, C_PL_SH)
    lead_hip(im, 1, 190, 9, 31, 18, 8)
    hl.outline(im)
    return im


def _lead_fall(im, x0, x1, y0, y1, tones, lit, clip=None):
    """One fall of a north-south coping: lead tiles whose courses run down the map."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if clip is None or clip(x):
                px[x, y] = roof_tile(y, (x1 - x) if lit else (x - x0), tones)


def _lead_v_coping(im, y0, y1):
    _lead_fall(im, 3, 14, y0, y1, C_LEAD_LIT, True)
    _lead_fall(im, 17, 28, y0, y1, C_LEAD_SH, False)
    rect(im, 2, y0, 2, y1, C_LEAD_LIT[2])
    rect(im, 29, y0, 29, y1, C_EAVE_DK)
    rect(im, 15, y0, 15, y1, C_LEAD_LIT[2])
    rect(im, 16, y0, 16, y1, C_EAVE)


def castle_wall(kind):
    """One piece of the castle's wall, 1x2 cells: wall()'s kinds h, v, end, corner-e
    and corner-w, on its rows, in lead, white plaster, namako and Tomuro stone."""
    im, d = canvas(1, 2)
    px = im.load()

    def coping(x0, x1):
        lead_band(im, x0, 12, x1, 24)
        rect(im, x0, 25, x1, 25, C_PL_SH)

    def face(x0, x1):
        rect(im, x0, 26, x1, 35, C_PL)
        rect(im, x0, 26, x1, 26, C_PL_LO)
        namako(im, x0, 36, x1, 47)
        rect(im, x0, 48, x1, 48, C_ST_DK)
        stonework(im, x0, 49, x1, 63)

    def end_face():
        rect(im, 5, 32, 26, 39, C_PL)
        rect(im, 24, 32, 26, 39, C_PL_LO)
        rect(im, 5, 32, 26, 32, C_PL_SH); rect(im, 5, 33, 26, 33, C_PL_LO)
        namako(im, 5, 40, 26, 49, shade_from=24)
        rect(im, 5, 50, 26, 50, C_ST_DK)
        stonework(im, 5, 51, 26, 63, 3)
        rect(im, 5, 51, 5, 63, C_ST_HI); rect(im, 26, 51, 26, 63, C_ST_JOINT)

    if kind == 'h':
        coping(0, 31); face(0, 31)
    elif kind in ('v', 'end'):
        _lead_v_coping(im, 0, 31)
        if kind == 'end':                                          # the coping's hipped south end
            for y in range(18, 30):
                t = y - 18
                for x in range(max(3, 15 - t), min(28, 16 + t) + 1):
                    px[x, y] = roof_tile(x, t, C_LEAD)
                if 15 - t >= 3:
                    px[15 - t, y] = C_LEAD_LIT[2]; px[16 + t, y] = C_EAVE
            rect(im, 2, 30, 29, 30, C_EAVE); rect(im, 2, 31, 29, 31, C_EAVE_DK)
        end_face()
    else:
        east = kind == 'corner-e'
        fx0, fx1 = (0, 27) if east else (4, 31)
        coping(0 if east else 2, 29 if east else 31)
        face(fx0, fx1)
        _lead_v_coping(im, 0, 11)
        rect(im, 15, 12, 15, 14, C_LEAD_LIT[2]); rect(im, 16, 12, 16, 14, C_EAVE)
        for y in range(12, 26):                                    # the hip between the two roofs
            reach = y - 12
            if east:
                _lead_fall(im, 17, 28, y, y, C_LEAD_SH, False, clip=lambda x, r=reach: x > 16 + r)
                px[29, y] = C_EAVE_DK
                if reach:
                    px[16 + reach, y] = C_LEAD_LIT[2]
            else:
                _lead_fall(im, 3, 14, y, y, C_LEAD_LIT, True, clip=lambda x, r=reach: x < 15 - r)
                px[2, y] = C_LEAD_LIT[2]
                if reach:
                    px[15 - reach, y] = C_EAVE
        for i, y in enumerate(range(26, 62, 6)):                   # the corner's long-and-short stones
            w = 7 if i % 2 else 4
            xa, xb = (fx1 - w, fx1) if east else (fx0, fx0 + w)
            rect(im, xa, y, xb, y + 5, C_ST[(i * 2 + (0 if east else 3)) % 7])
            rect(im, xa, y, xb, y, C_ST_HI)
            rect(im, xa, y + 5, xb, y + 5, C_ST_JOINT)
            if east:
                rect(im, xb - 1, y + 1, xb, y + 5, C_ST_JOINT)
                rect(im, xa, y + 1, xa, y + 4, C_ST_LO)
            else:
                rect(im, xa, y, xa, y + 5, C_ST_HI)
                rect(im, xb, y + 1, xb, y + 4, C_ST_LO)
        rect(im, fx1 - 6 if east else fx0, 62, fx1 if east else fx0 + 6, 63, C_ST_JOINT)
    hl.outline(im)
    return im


# ---- the Tsuzumi-mon's timber: sheet colours ----------------------------------------------
TS, TS_HI, TS_LO, TS_DK = rgb('ab7656'), rgb('c18e75'), rgb('904a37'), rgb('5a3827')
TS_COFFER, TS_COFFER_DK = rgb('4d3326'), rgb('312522')


def drum_pillar(im, cx, y0, y1):
    """One drum of the Tsuzumi-mon: two families of leaning timbers that cross,
    narrow at the waist, as the cords of a hand drum do."""
    px = im.load()
    mid, half = (y0 + y1) / 2, (y1 - y0) / 2

    def hw(y):
        return 6.5 + 9.5 * ((y - mid) / half) ** 2

    for y in range(y0, y1 + 1):
        w = round(hw(y))
        rect(im, cx - w, y, cx + w, y, TS_DK)
        rect(im, cx - w, y, cx - w, y, TS_HI)
        rect(im, cx + w, y, cx + w, y, TS_COFFER)
    for dirn in (1, -1):
        for k in range(9):
            th0 = 2 * math.pi * k / 9 + (0.2 if dirn < 0 else 0)
            for y in range(y0, y1 + 1):
                th = th0 + dirn * (y - y0) / (y1 - y0) * math.pi * 0.95
                if math.cos(th) <= 0.08:
                    continue                                       # round the back
                s = math.sin(th)
                x = round(cx + (hw(y) - 0.5) * s)
                px[x, y] = TS_HI if s < -0.35 else (TS if s < 0.45 else TS_LO)
                if abs(s) < 0.8:
                    px[x + dirn, y] = TS_LO if s > 0.2 else TS
    rect(im, cx - 17, y0 - 4, cx + 17, y0 - 1, TS_LO)              # the collar under the roof
    rect(im, cx - 17, y0 - 4, cx + 17, y0 - 4, TS_DK)
    rect(im, cx - 17, y0 - 3, cx + 10, y0 - 3, TS)
    rect(im, cx - 18, y1 + 1, cx + 18, y1 + 5, C_ST[1])            # the stone plinth
    rect(im, cx - 18, y1 + 1, cx + 18, y1 + 1, C_ST_HI)
    rect(im, cx - 18, y1 + 2, cx - 18, y1 + 5, C_ST[2])
    rect(im, cx - 18, y1 + 4, cx + 18, y1 + 5, C_ST_JOINT)
    rect(im, cx + 13, y1 + 2, cx + 18, y1 + 5, C_ST_JOINT)


def tsuzumi_gate():
    im, d = canvas(6, 5)                 # 192 x 160; pillars stand in columns 1 and 4
    px = im.load()
    # ---- the roof, seen from above: one flat slab of crossed timbers over dark coffers, 8px a bay
    x0, x1, y0, y1 = 3, 188, 4, 47
    rect(im, x0, y0, x1, y1, TS)
    for y in range(y0 + 2, y1 - 1):
        for x in range(x0 + 2, x1 - 1):
            u, v = (x - x0 - 2) % 8, (y - y0 - 2) % 8
            if u < 6 and v < 6:                                    # a coffer: the beams' shadow on its top row and west column
                c = TS_COFFER_DK if u == 0 or v == 0 else TS_COFFER
            elif (u == 6 and v < 6) or (v == 6 and u < 6):
                c = TS_HI                                          # a beam's lit edge
            elif (u == 7 and v < 6) or (v == 7 and u < 6):
                c = TS_LO                                          # and its far one
            else:
                c = TS
            px[x, y] = c
    rect(im, x0, y0, x1, y0, TS_HI); rect(im, x0, y0, x0, y1, TS_HI)
    rect(im, x1 - 1, y0 + 1, x1, y1, TS_LO)
    # ---- its front edge: the fascia, a beam end at every bay; the underside in shade
    rect(im, x0, 48, x1, 56, TS)
    rect(im, x0, 48, x1, 48, TS_DK); rect(im, x0, 49, x1, 49, TS_HI)
    rect(im, x0, 55, x1, 56, TS_LO)
    rect(im, 184, 49, 188, 56, TS_LO)
    for x in range(x0 + 8, x1 - 4, 8):
        rect(im, x, 51, x + 1, 54, TS_LO)
        rect(im, x, 51, x + 1, 51, TS_DK)
    rect(im, 8, 57, 183, 58, TS_DK)
    drum_pillar(im, 48, 63, 150)
    drum_pillar(im, 144, 63, 150)
    hl.outline(im)
    return im
```
