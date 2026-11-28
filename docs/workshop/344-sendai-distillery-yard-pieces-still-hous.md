# 344: Sendai's distillery yard pieces (still house, cask rack, red maple, Yamadera) in the house look

Part 2 of 3 of #339. All paths are under `gamev2/`; commands run from `gamev2/`. Coordinates are the tool's
half-size pixels (32 a cell), y from the top. Written against `origin/master` at `63a0d22f` (the ticket branch
is behind it; Workshop merges master in before implementation).

## Context

`tools/generate_sendai_town_art.py` draws four distillery-yard sprites in the old look (flat faces, a front
elevation's slate roof, lit yellow windows, colours no GuttyKreum sheet has, half-clear pixels). This ticket
redraws them in place in the house look ("House look: GuttyKreum" in `docs/generators-and-checks.md`):

| Key (`assets/sprites/<key>.png`) | Cells | Builder | Now: colours / half-clear pixels |
|---|---|---|---|
| `sendai-distillery-warehouse_0_0` | 6x4 | `distillery_warehouse` | 52 / 0 |
| `sendai-cask-rack_0_0` | 3x2 | `cask_rack` | 10 / 536 |
| `sendai-red-maple_0_0` | 3x4 | `red_maple` | 9 / 2396 |
| `sendai-yamadera_0_0` | 6x6 | `yamadera` | 46 / 1408 |

Keys, sizes, anchors, `door`, `solid`, `walk_through` and glow data stay. The other pieces of the file belong
to #333, #336, #342, #343 and #345.

Found while designing:

- **The ticket's "helpers shared with `generate_distillery_art.py`" is not so.** `brick_px`, `pot_still`,
  `cask_end` and `SLATE_P` are defined in this tool's distillery section and used nowhere else (that tool has
  its own `_bricks` / `_cask_end`). They can be rewritten freely; `check_generators.py` still covers
  `generate_distillery_art`.
- **No room shows these sprites.** The four keys are not in `config.json` (no `tilePalette` or
  `spriteMetadata` entry) and are placed nowhere, so no room render, world map, `play.js` output or in-game
  `?tod=night` view can show them. The "rooms rendered before and after, by day and at night" are the tool's
  own `--scenes` pictures: `sendai_art_distillery.png` and its `_night.png` (and `sendai_art_samurai.png`,
  which stands one red maple).
- **The tool is not in `check_generators.ART_TOOLS`, and a run rewrites about 102 PNGs** with the same pixels
  in another encoding (Pillow 11.3.0). Only the four may be committed.
- **`tools/house_look.py` (#279) is on master** but has no `foliage`, `roof_tile` or `pane`; those are still
  `generate_sendai_art.py`'s, and `bricks` is `generate_kanazawa_art.py`'s. `glaze` and `flat_roof` are not
  needed.
- **The tool has a `limb()` of its own** (other pieces use it), so `generate_sendai_art.limb` cannot be
  imported by name. It also has `yard_tex` / `yard_kerb` (#342's brick yard).

## Approach

Replace the section's helpers and four builders with the appendix's code, which was run through the tool as a
prototype: every rule below holds for it, and the manifest it writes equals today's.

- **Colours** are the section's own `DY_*` block: all sheet colours, at most 24 a sprite. Ink is
  `house_look.INK` (`0a1627`), laid by `hl.outline(im)` as the last call of each builder.
- **Rectangles, pixels and whole numbers only** (`hl.fill`, `px[x, y]`, `math.isqrt`): no Pillow shape call,
  no `sin` / `cos` / `round`, so every Pillow and platform paints the same pixels.
- **Helpers come in as module aliases, imported at the head of the section**, not in the file's top import
  block: `hl` (`house_look`), `sa` (`generate_sendai_art`: `roof_tile`, `foliage`, `ground_shade`, `stem`,
  `limb`, `speck`, `P_*`, `AUTUMN`, `NEEDLE`) and `ka` (`generate_kanazawa_art`: `bricks`). New helpers are
  `dy_*`, new constants `DY_*`. This keeps the change inside one section of a file five other tickets edit.
- **Ground shadow**: the rack and the maple get `sa.ground_shade` (navy `2a3151` at alpha 90, drawn before
  the outline so the ink rings it), as the approved `sendai-maple` / `-pine` / `-cedar` do. The still house
  and Yamadera have none. Those are the only pixels that are neither clear nor opaque.

| Sprite | Picture (prototype: colours) |
|---|---|
| Still house | 24. Roof seen from above in the pack's tile (`sa.roof_tile`): ridge, lit west verge, eave lip, two brick stacks with their shade, and a cross roof over the still room (lit west fall, shaded east fall, ink valleys). Brick body (`ka.bricks`) with the eave's shade, stone plinth. Three arched windows of dark glass with a slanted glare and louvred green shutters; the second has a blind drawn where the lit window was. The great arched window shows the copper pot still shaded in five bands from upper left, with a glint, riveted seam, lyne arm, condenser pipe and a dim ember in the hearth, behind an ink rail. Green panelled doors under a dark fanlight, a `c6a663` lamp with a small `f3d890` core, a pale step. DISTILLERY board; two small shaded casks. |
| Cask rack | 9. Five cask ends (iron hoop, chime, boards lit from the upper left, stencil, bung) on a rail with stepped chocks; the upper pair shades the lower three. |
| Red maple | 10. Thirteen ragged clumps (`sa.foliage`) in `DY_FLAME` (`f6a583` to `5b283b`), a shaded trunk with a root flare and three boughs. |
| Yamadera | 23. Pale rock with slanted clefts and broken ledges, west faces lit; the lookout stage on stilts and the red hall, each under a small hipped tile roof seen from above; a canopy of small clumps in drifts of maple red, ochre and fir green, cedars through it; the stone stair on its old zig-zag; a red gate, bushes and boulders at the foot. Same skyline role and footprint: a backdrop. |

Kept from the old drawings so the manifest's data still fits: the still house's windows (x 16, 42, 164), still
window (x 70-121), door (cell 4) and step; the rack's cask centres; the maple's trunk in cell (1, 3);
Yamadera's stair path and gate. The three glow spots are unchanged and land on the pot still (96, 93), the
blind (48, 78) and the door lamp and fanlight (144, 74). Dropped because they do not survive the look (lit
yellow, or loose single pixels): the gable's cask roundel, the lit window and fanlight, the red ivy, the
maple's fallen leaves. Only the description strings follow.

## Changes

### `tools/generate_sendai_town_art.py`

Only the section "The distillery yard, and Yamadera on the hill behind" (from its banner to the banner of the
next section) and three description strings in `PIECES`.

- **Replace the section's body** (`SLATE_P`, `brick_px`, `pot_still`, `cask_end`, `distillery_warehouse`,
  `cask_rack`, `red_maple`, `yamadera`) with the appendix, as written. `SLATE_P` and `brick_px` go; `pot_still`
  and `cask_end` keep their names and take `im` in place of `d`. Nothing outside the section calls any of
  them.
- **`PIECES`**: the four rows keep key, builder, size, district and the `dict(...)` exactly. Descriptions:
  - still house: "red brick under slate, a centre gable with a cask roundel, arched windows with green iron
    shutters," becomes "red brick under a tile roof seen from above (a cross roof over the still room, two
    brick stacks), arched windows of dark glass with green iron shutters (a blind drawn in the second),";
    "pot, tall neck, lyne arm, a fire under it" becomes "pot, neck, lyne arm, an ember under it"; "under a lit
    fanlight and a lamp" becomes "under a dark fanlight and a dim lamp"; "Ivy gone red up the east corner, two
    casks by the west window." becomes "Two casks by the west window."
  - red maple: drop ", red leaves fallen under it".
  - Yamadera: "(a canopy of small maple, keyaki and russet pads with cedars standing through it)" becomes
    "(a canopy of small ragged clumps in maple red, ochre and fir green with cedars standing through it)".
  - cask rack: unchanged.
- **Do not change**: the top import block, the shared colour constants, `limb`, `yard_tex`, `yard_kerb`, any
  other builder, `FAMILIES`, `halo`, `glow_spots`, `manifest()` (its notes still hold), `sheet()`, `scenes()`,
  `main()`, the module docstring (its distillery-yard entries are still true).

### `assets/sprites/`

The four PNGs above, rewritten by the tool. Nothing else: after running the tool, `git checkout --` every
other PNG it touched.

### `tools/tests/sendai-distillery-yard-art.test.js` (new)

The tests below. Copy `hex`, `load`, `sheets` and the way a builder's source is cut from
`tools/tests/kanazawa-art.test.js` (test files do not share helpers). Its own file, so it does not collide
with the sibling tickets' tests.

### `docs/generators-and-checks.md`

One sentence after the Kanazawa paragraph that ends "House look: GuttyKreum": Sendai's distillery-yard pieces
in `tools/generate_sendai_town_art.py` (the still house, the cask rack, the red maple and Yamadera; #344, part
of #339) are drawn in the look with `house_look` and `generate_sendai_art`'s `roof_tile` / `foliage`, and held
by `tools/tests/sendai-distillery-yard-art.test.js`.

## Data and interfaces

None. No key, size, anchor, `door` / `solid` / `walk` cell, glow spot, `config.json`, `tiled/` map, palette
index or `devhouse.world` entry changes, so no room is touched. The manifest (`--manifest`) differs only in
three `description` strings. `pot_still` and `cask_end` change their first argument from `d` to `im`; nothing
imports them.

## Tests

`tools/tests/sendai-distillery-yard-art.test.js`; names start `sendai yard art:` and end `(#344)`; `YARD` maps
the four keys to their cells:

1. **Sizes**: each is cells x 64 and every pixel a 2x2 block. Alpha is 0 or 255, except `2a3151` at alpha 90,
   which only the rack and the maple may have.
2. **Colours** (opaque pixels): only sheet colours; at most 24 for the still house and Yamadera, 16 for the
   rack and the maple; none on more than half; none of `f6dc8c`, `f2c66a`, `f9c22e`, `2b373c`, `000000`;
   `f3d890` under 3%.
3. **Silhouette**: every pixel that is not clear and has a clear 4-neighbour inside the canvas is opaque
   `0a1627`.
4. **Rectangles, pixels and whole numbers only**: the source of `dy_disc`, `dy_arch`, `dy_glazed`, `cask_end`,
   `pot_still`, `dy_stack`, `distillery_warehouse`, `cask_rack`, `red_maple`, `dy_top`, `dy_hill_roof`,
   `yamadera` has none of `.polygon(`, `.ellipse(`, `.arc(`, `.pieslice(`, `.chord(`, `.line(`, `shade(im`,
   `round(`, no `/\broof\(/` and no `/math\.(?!isqrt)/`.
5. **Placement data is what it was**: a Python snippet (run as test 6's is; skips without Pillow) imports the
   tool and prints, for each of the four rows of `PIECES`, `size`, `m.get('door') or []`, `m.get('solid', [])`,
   `m.get('walk', [])`, `m.get('layer', 'standing')`, `halo(key)` and `glow_spots(m)`. Pinned in the test:
   - still house: `[6, 4]`; door `[[4, 3]]`; solid every cell of rows 2 and 3; glow
     `{x: 3, y: 2.9, r: 1.1, color: 16039292, a: 0.55}`, `{x: 1.5, y: 2.45, r: 0.7, color: 16178316, a: 0.5}`,
     `{x: 4.5, y: 2.3, r: 0.6, color: 16178316, a: 0.6}`;
   - rack: `[3, 2]`; solid `[[0, 1], [1, 1], [2, 1]]`; maple: `[3, 4]`; solid `[[1, 3]]`; Yamadera: `[6, 6]`;
     solid every cell of rows 1 to 5 (row 0 is the only row walked behind);
   - all four: no `walk`, layer `standing`, halo false; the last three no door and no glow.
6. **The tool draws what is committed**: `kanazawa-art.test.js`'s `rebuild` snippet with
   `generate_sendai_town_art` (builds `SPRITES[key]()`, doubles, compares `tobytes()` with the committed PNG;
   skips without Pillow), over the four keys. The tool is not in `ART_TOOLS`, so this is its guard.

The implementer, in order:

```bash
mkdir -p /tmp/344/before
cp assets/sprites/sendai-{distillery-warehouse,cask-rack,red-maple,yamadera}_0_0.png /tmp/344/before/
python3 tools/generate_sendai_town_art.py --scenes /tmp/344/before/scenes --manifest /tmp/344/before/manifest.json
git checkout -- assets/sprites                        # before any edit: the "before" pictures
# ... edit the tool ...
python3 tools/generate_sendai_town_art.py --scenes /tmp/344/scenes --manifest /tmp/344/manifest.json
git status --short assets/sprites                     # then git checkout -- every PNG that is not one of the four
python3 tools/house_look.py --sheet /tmp/344/contact.png --scale 2 \
    assets/sprites/sendai-{distillery-warehouse,cask-rack,red-maple,yamadera}_0_0.png \
    assets/sprites/sendai-pub_0_0.png assets/sprites/sendai-maple_0_0.png assets/sprites/sendai-cedar_0_0.png
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
    && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

- **Transcription check**: the SHA-256 of each doubled sprite's RGBA bytes
  (`hashlib.sha256(Image.open(p).convert('RGBA').tobytes())`) begins `e7bfd8e156798f0c` (still house),
  `7903a2f1dbc2d984` (rack), `fdacb9136bca6199` (maple), `1a50c003e2a16db2` (Yamadera) at master `63a0d22f`.
  A difference is a slip in copying the appendix, or `roof_tile` / `foliage` / `bricks` / `ground_shade` /
  `stem` / `limb` changed upstream (#324 and #329 edit `generate_sendai_art.py`): then judge the picture and
  the tests, not the hash.
- The two manifests differ only in the three descriptions. `sendai_art_station.png`, `_downtown.png`,
  `_bay.png` and their nights are pixel-equal before and after; `_samurai.png` differs only at its red maple.
- **Look at** `/tmp/344/scenes/sendai_art_distillery.png` and `_distillery_night.png` beside the "before"
  ones (at night the three glow spots sit on the still, the blind and the door lamp, and no window is a lit
  yellow), and at the contact sheet beside the done models. Save before/after images to `/work/media/` and
  name in the summary any sprite that still reads flat. In the prototype none does; the weakest are the
  maple's plain trunk and Yamadera's rock, which is busier than the pack's stone.
- `git status` shows only the tool, the four PNGs, the new test file and the doc. `check_generators.py`
  reports no drift and the world map is not rebuilt.
- The browser regression (`tools/browser/regress.js`) cannot show these sprites, since no room places them:
  run it as the house rule asks and say so, or say it was not run and why.
- Commit as `gamev2: ... (#344)`; rooms touched: none.

## Risks and open questions

- **Same file as #333, #336, #342, #343, #345.** Touch only the section and the three descriptions, and merge
  or rebase before committing. A sibling may add `import house_look as hl` at the top: the section's own
  imports are then repeats and harmless; keep them. `dy_*` / `DY_*` stay clear of #342's `yard_*`.
- **The still house is at the 24-colour limit.** Any added detail must reuse a colour already in it.
- **Taste calls in the prototype**, each one constant or one call: the blind in the second window (delete the
  `if i == 1:` block for plain dark glass; the glow spot then lights a dark pane); the roof is the pack's
  slate-green tile, not a red or grey one; Yamadera's gold is ochre (`DY_ICHO`) so that it carries no lamp
  yellow; the roundel, ivy and fallen leaves are gone.
- **The kiln and barrels beside them in the scene are still in the old look** until #324; judge the four
  against `sendai-pub`, `-maple`, `-cedar`, not against those.
- **Night is only previewed in Pillow** (`night()` in the scenes); the game judges once a ticket registers and
  places the sprites. The glow colours in the manifest (`f6dc8c`, `f4bd7c`) are light colours for
  `Glows.js`, not pixels, and stay.
- **The run's other ~102 rewritten PNGs** must not be committed; the tool has no unchanged-pixels guard (the
  Sendai counterpart of #379).

## Appendix: the prototype's drawing code

The whole body of the section, under its banner. Run through the tool as written here; `math`, `rgb`,
`canvas`, `text` and `text_w` are the tool's own imports (`im, d = canvas(w, h)`).

```python
import house_look as hl                 # noqa: E402
import generate_sendai_art as sa        # noqa: E402  (as modules: this file has a limb() of its own)
import generate_kanazawa_art as ka      # noqa: E402

DY_INK = hl.INK
DY_BRICK, DY_BRICK_HI, DY_BRICK_LO = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
DY_STONE, DY_STONE_HI, DY_STONE_LO, DY_STONE_DK = rgb('e4cecc'), rgb('fafcfd'), rgb('be9e8c'), rgb('8e7366')
DY_GREEN, DY_GREEN_HI, DY_GREEN_LO = rgb('395050'), rgb('506b6b'), rgb('2e4040')
DY_CU = [rgb(c) for c in ('f6a583', 'f6a583', 'ce6a42', 'aa4d31', '8a3a22')]          # copper, lit to shade
DY_OAK, DY_OAK_HI, DY_OAK_LO, DY_OAK_DK = rgb('aa775f'), rgb('bb8971'), rgb('86624f'), rgb('71412a')
DY_HOOP, DY_HOOP_HI, DY_HOOP_LO = rgb('53596d'), rgb('be9e8c'), rgb('434857')
DY_ROOF_LIT = [rgb(c) for c in ('0a1627', '172459', '53596d', '395050', '434857')]    # a fall facing west
DY_ROOF_SH = [rgb(c) for c in ('0a1627', '0a1627', '395050', '2e4040', '2e4040')]     # a fall facing east
DY_RIDGE, DY_RIDGE_HI = rgb('434857'), rgb('53596d')
DY_FLAME = [rgb(c) for c in ('f6a583', 'e77f6a', 'ce6a42', 'aa4d31', '8a3a22', '5b283b')]   # the red maple
DY_GINKGO = [rgb(c) for c in ('f3d890', 'c6a663', 'c6a663', 'a7843b', '86624f', '5b283b')]
DY_ICHO = DY_GINKGO[1:4] + DY_GINKGO[3:]                                 # the hill's gold: no lamp yellow in it
DY_FIR = sa.NEEDLE[1:]
DY_MOMIJI = sa.AUTUMN[1:]
DY_HILL_ROOF = [rgb(c) for c in ('0a1627', '172459', '434857', '2e4040', '2e4040')]
DY_TIMBER, DY_TIMBER_LO = rgb('86624f'), rgb('5b283b')


def dy_disc(r):
    """A disc's half-widths, a row at a time from the top (2r + 1 rows): whole numbers only."""
    return [math.isqrt(r * r - dy * dy + r) for dy in range(-r, r + 1)]


def dy_arch(im, x0, y0, x1, y1, c):
    """A round-headed box, in rows."""
    r = (x1 - x0 + 1) // 2
    for k in range(r):
        inset = r - (math.isqrt(4 * r * r - (2 * (r - k) - 1) ** 2) + 1) // 2
        hl.fill(im, (x0 + inset, y0 + k, x1 - inset, y0 + k), c)
    hl.fill(im, (x0, y0 + r, x1, y1), c)


def dy_glazed(im, x0, y0, x1, y1, step=9):
    """generate_sendai_art.pane under a round head: dark glass, a slanted glare, a shaded head."""
    dy_arch(im, x0, y0, x1, y1, sa.P_GLASS)
    px = im.load()
    for x in range(x0, x1 + 1):
        top = next(y for y in range(y0, y1 + 1) if px[x, y] == sa.P_GLASS)
        for y in range(top, y1 + 1):
            px[x, y] = sa.P_GLASS_LO if y < top + 2 else sa.P_GLARE if (x - x0 + y1 - y) % step == 0 else sa.P_GLASS


def cask_end(im, cx, cy, r, mark=0):
    """A cask seen end on: an iron hoop, the chime, the head's boards lit from the upper left, a stencil."""
    px = im.load()
    for dy, hw in zip(range(-r, r + 1), dy_disc(r)):
        for dx in range(-hw, hw + 1):
            q, lean = dx * dx + dy * dy, dx + dy
            if q > (r - 2) * (r - 2) + 2:                         # the hoop
                c = DY_HOOP_HI if lean * 2 < -r else DY_HOOP_LO if lean * 2 > r else DY_HOOP
            elif q > (r - 3) * (r - 3) + 2:                       # the chime
                c = DY_OAK_DK
            elif (dx + r) % 4 == 1:                               # a joint between two boards
                c = DY_OAK_DK if lean > 0 or r <= 10 else DY_OAK_LO
            else:
                c = DY_OAK_HI if lean * 10 < -5 * r else (DY_OAK_LO if r > 10 else DY_OAK_DK) if lean * 10 > 6 * r else DY_OAK
            px[cx + dx, cy + dy] = c
    if r > 10:                                                    # the stencil, and the bung
        hl.fill(im, (cx - 4, cy - 3, cx + 3, cy + 1), DY_STONE if mark % 2 == 0 else DY_OAK_DK)
        hl.fill(im, (cx - 3, cy - 1, cx + 2, cy - 1), DY_INK if mark % 2 == 0 else DY_STONE)
        hl.fill(im, (cx + (2 if mark % 2 else -3), cy + 5, cx + (3 if mark % 2 else -2), cy + 6), DY_OAK_DK)
    else:
        hl.fill(im, (cx - 2, cy - 1, cx + 1, cy), DY_STONE if mark % 2 == 0 else DY_OAK_DK)


DY_NECK = (2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9)


def pot_still(im, cx, base):
    """A copper pot still in rows: the lyne arm, the tapering neck, the round pot on a brick hearth,
    banded from a lit upper left to a shaded lower right."""
    px = im.load()

    def cu(dx, dy, r):
        return DY_CU[max(0, min(4, (dx * 3 + dy * 4 + 5 * r) * 5 // (10 * r)))]
    for n in range(20):                                           # the lyne arm, bending away east
        y = base - 48 + n * n // 70
        hl.fill(im, (cx + n, y, cx + n, y + 2), DY_CU[2])
        px[cx + n, y] = DY_CU[1]; px[cx + n, y + 2] = DY_CU[4]
    for k, w in enumerate(DY_NECK):                                  # the neck
        y = base - 45 + k
        for dx in range(-w, w + 1):
            px[cx + dx, y] = DY_CU[1] if dx <= -w + 1 else DY_CU[4] if dx == w else DY_CU[3] if dx >= w - 1 - w // 3 else DY_CU[2]
    hl.fill(im, (cx - 9, base - 31, cx + 9, base - 31), DY_CU[4])  # the collar
    r = 14
    for dy, hw in zip(range(-r, r + 1), dy_disc(r)):                 # the pot
        for dx in range(-hw, hw + 1):
            px[cx + dx, base - 17 + dy] = cu(dx, dy, r)
    hl.fill(im, (cx - 9, base - 26, cx - 8, base - 23), DY_STONE_HI)  # a glint
    for dx in range(-13, 14):                                     # a riveted seam
        px[cx + dx, base - 15] = DY_CU[4]
        if dx % 3 == 0:
            px[cx + dx, base - 16] = DY_CU[1]
    for dy, hw in zip(range(-3, 4), dy_disc(3)):                     # the manhole
        hl.fill(im, (cx + 5 - hw, base - 9 + dy, cx + 5 + hw, base - 9 + dy), DY_CU[4])
    hl.fill(im, (cx + 4, base - 10, cx + 5, base - 9), DY_CU[2])
    hl.fill(im, (cx - 16, base - 4, cx + 16, base), DY_BRICK_LO)   # the hearth, a fire door in it
    hl.fill(im, (cx - 16, base - 4, cx + 16, base - 4), DY_BRICK)
    hl.fill(im, (cx - 5, base - 2, cx + 5, base), DY_INK)
    hl.fill(im, (cx - 3, base - 1, cx + 2, base - 1), sa.P_LAMP); px[cx - 1, base - 1] = sa.P_LAMP_HI


def dy_stack(im, x, y):
    """A brick chimney stack on the roof, seen from above, and its shade on the tiles."""
    px = im.load()
    for yy in range(y + 4, y + 22):                               # the shade, east and south of it
        for xx in range(x + 3, x + 18):
            if yy > y + 16 or xx > x + 12:
                px[xx, yy] = sa.roof_tile(xx, yy, DY_ROOF_SH)
    hl.fill(im, (x, y, x + 12, y + 16), DY_INK)
    hl.fill(im, (x + 1, y + 4, x + 11, y + 15), DY_BRICK)
    for yy in range(y + 6, y + 16, 3):
        hl.fill(im, (x + 1, yy, x + 11, yy), DY_BRICK_LO)
    hl.fill(im, (x + 9, y + 4, x + 11, y + 15), DY_BRICK_LO)
    hl.fill(im, (x + 1, y + 1, x + 11, y + 3), DY_STONE_LO)        # the cap, and its flue
    hl.fill(im, (x + 1, y + 1, x + 11, y + 1), DY_STONE)
    hl.fill(im, (x + 4, y + 2, x + 8, y + 3), DY_INK)


def distillery_warehouse():
    im, d = canvas(6, 4)                 # 192 x 128
    px = im.load()
    # ---- the roof, seen from above: tile courses under a ridge, two brick stacks ----
    for y in range(6, 44):
        for x in range(1, 191):
            px[x, y] = sa.roof_tile(x, y, DY_ROOF_SH if x > 183 else None)
    hl.fill(im, (1, 2, 190, 5), DY_RIDGE); hl.fill(im, (1, 2, 190, 2), DY_RIDGE_HI)
    hl.fill(im, (1, 5, 190, 5), DY_INK)
    for x in range(6, 190, 8):
        hl.fill(im, (x, 3, x, 4), DY_GREEN_LO)
    hl.fill(im, (1, 6, 2, 43), DY_RIDGE_HI)                        # the west verge, lit
    hl.fill(im, (1, 44, 190, 44), DY_RIDGE_HI); hl.fill(im, (1, 45, 190, 45), DY_GREEN_LO)   # the eave's lip
    hl.fill(im, (1, 46, 190, 46), DY_INK)
    dy_stack(im, 26, 9); dy_stack(im, 150, 9)
    # ---- the cross roof over the still room: a ridge coming south, a fall either side ----
    for y in range(6, 48):
        half = min(29, (y - 5) * 29 // 38)
        for x in range(96 - half, 97 + half):
            c = sa.roof_tile(y, x, DY_ROOF_LIT) if x < 95 else sa.roof_tile(y, 192 - x, DY_ROOF_SH)
            px[x, y] = c
        px[96 - half, y] = DY_INK if y < 44 else DY_RIDGE_HI        # the valleys, then the verges
        px[96 + half, y] = DY_INK
    hl.fill(im, (95, 3, 97, 47), DY_RIDGE); hl.fill(im, (95, 3, 95, 47), DY_RIDGE_HI)
    hl.fill(im, (97, 6, 97, 47), DY_INK)
    hl.fill(im, (67, 48, 125, 48), DY_RIDGE_HI); hl.fill(im, (67, 49, 125, 49), DY_GREEN_LO)
    hl.fill(im, (67, 50, 125, 50), DY_INK)
    # ---- the brick body, the eave's shade along its top, a stone plinth ----
    ka.bricks(px, 4, 47, 187, 115, DY_BRICK, DY_BRICK_HI, DY_BRICK_LO, DY_BRICK_LO)
    hl.fill(im, (4, 47, 66, 48), DY_BRICK_LO); hl.fill(im, (126, 47, 187, 48), DY_BRICK_LO)
    hl.fill(im, (67, 51, 125, 52), DY_BRICK_LO)
    for x in range(4, 188):
        if (x + 49) % 2 and not 67 <= x <= 125:
            px[x, 49] = DY_BRICK_LO
    hl.fill(im, (4, 116, 187, 121), DY_STONE_LO); hl.fill(im, (4, 116, 187, 116), DY_STONE)
    hl.fill(im, (4, 121, 187, 121), DY_STONE_DK); hl.fill(im, (181, 117, 187, 121), DY_STONE_DK)
    # ---- arched windows with iron shutters folded back (cells 0, 1 and 5) ----
    for i, x in enumerate((16, 42, 164)):
        dy_arch(im, x - 2, 58, x + 13, 98, DY_STONE)
        hl.fill(im, (x - 2, 66, x - 2, 98), DY_STONE_HI); hl.fill(im, (x + 13, 66, x + 13, 98), DY_STONE_LO)
        dy_arch(im, x, 60, x + 11, 96, DY_GREEN_LO)
        dy_glazed(im, x + 1, 61, x + 10, 95, 7)
        if i == 1:                                                # a blind drawn in the second: the room in use
            for y in range(66, 86):
                hl.fill(im, (x + 1, y, x + 10, y), DY_STONE_LO if y % 3 else DY_STONE_DK)
            hl.fill(im, (x + 1, 86, x + 10, 86), DY_STONE_DK)
        hl.fill(im, (x + 5, 61, x + 6, 95), DY_GREEN_LO)
        for y in (75, 85):
            hl.fill(im, (x + 1, y, x + 10, y), DY_GREEN_LO)
        hl.fill(im, (x - 3, 97, x + 14, 98), DY_STONE_HI); hl.fill(im, (x - 3, 99, x + 14, 99), DY_BRICK_LO)
        for sx in (x - 8, x + 14):
            hl.fill(im, (sx, 66, sx + 5, 96), DY_GREEN)
            hl.fill(im, (sx, 66, sx, 96), DY_GREEN_HI); hl.fill(im, (sx + 5, 66, sx + 5, 96), DY_GREEN_LO)
            for y in range(69, 96, 3):
                hl.fill(im, (sx + 1, y, sx + 4, y), DY_GREEN_LO)
            hl.fill(im, (sx, 66, sx + 5, 66), DY_GREEN_HI)
    # ---- the still room's great arched window (cells 2-3): the pot still behind a rail ----
    dy_arch(im, 70, 53, 121, 112, DY_STONE)
    hl.fill(im, (70, 79, 70, 112), DY_STONE_HI); hl.fill(im, (121, 79, 121, 112), DY_STONE_LO)
    dy_arch(im, 73, 56, 118, 112, DY_STONE_LO)
    dy_arch(im, 74, 57, 117, 112, sa.P_GLASS)
    for y in range(60, 110, 6):                                   # the back wall's courses, in the dark
        for x in range(74, 118):
            if px[x, y] == sa.P_GLASS:
                px[x, y] = sa.P_GLASS_LO
    for x in range(74, 118):                                      # the glass: a glare here and there
        for y in range(57, 100):
            if px[x, y] in (sa.P_GLASS, sa.P_GLASS_LO) and (x + y) % 19 == 0 and sa.speck(x // 6, y // 6, 4) < 70:
                px[x, y] = sa.P_GLARE
    pot_still(im, 93, 109)
    hl.fill(im, (110, 70, 113, 109), DY_CU[3]); hl.fill(im, (110, 70, 110, 109), DY_CU[2])     # the condenser pipe
    hl.fill(im, (113, 70, 113, 109), DY_CU[4])
    hl.fill(im, (74, 99, 117, 99), DY_INK)                         # an iron rail across the opening
    for x in range(75, 118, 4):
        hl.fill(im, (x, 99, x, 109), DY_INK)
    hl.fill(im, (69, 110, 122, 112), DY_STONE_HI); hl.fill(im, (69, 112, 122, 112), DY_STONE_LO)   # its stone sill
    # ---- the door (cell 4): green double doors in a stone surround, a fanlight, a lamp ----
    dy_arch(im, 131, 63, 156, 115, DY_STONE)
    hl.fill(im, (131, 76, 131, 115), DY_STONE_HI); hl.fill(im, (156, 76, 156, 115), DY_STONE_LO)
    dy_glazed(im, 134, 66, 153, 76, 7)
    for x in (138, 143, 144, 149):
        hl.fill(im, (x, 66 + (3 if x in (138, 149) else 0), x, 76), DY_GREEN_LO)
    hl.fill(im, (134, 77, 153, 115), DY_GREEN_LO)
    for x0 in (135, 144):                                         # two panelled leaves
        hl.fill(im, (x0, 78, x0 + 8, 115), DY_GREEN)
        hl.fill(im, (x0, 78, x0, 115), DY_GREEN_HI)
        hl.fill(im, (x0 + 2, 81, x0 + 6, 93), DY_GREEN_LO); hl.fill(im, (x0 + 2, 97, x0 + 6, 112), DY_GREEN_LO)
        hl.fill(im, (x0 + 3, 82, x0 + 6, 93), DY_GREEN); hl.fill(im, (x0 + 3, 98, x0 + 6, 112), DY_GREEN)
    px[142, 96] = sa.P_LAMP; px[145, 96] = sa.P_LAMP
    hl.fill(im, (143, 54, 144, 57), DY_INK)                        # the lamp over it: dim gold, never lit yellow
    hl.fill(im, (140, 57, 147, 64), DY_INK)
    hl.fill(im, (141, 58, 146, 63), sa.P_LAMP); hl.fill(im, (142, 59, 144, 61), sa.P_LAMP_HI)
    hl.fill(im, (130, 116, 157, 121), DY_STONE); hl.fill(im, (130, 116, 157, 116), DY_STONE_HI)   # the step
    hl.fill(im, (130, 121, 157, 121), DY_STONE_LO)
    # ---- the board, two casks by the west window ----
    hl.fill(im, (64, 51, 127, 61), sa.P_LAMP); hl.fill(im, (65, 52, 126, 60), sa.P_GLASS)
    text(d, 'DISTILLERY', 96 - text_w('DISTILLERY') // 2, 53, DY_STONE)
    cask_end(im, 15, 107, 8, 0); cask_end(im, 33, 107, 8, 1)
    hl.outline(im)
    return im


def cask_rack():
    im, d = canvas(3, 2)                 # 96 x 64: five casks end-on, on chocks
    sa.ground_shade(d, 48, 57, 46)
    hl.fill(im, (3, 56, 92, 59), DY_OAK_LO); hl.fill(im, (3, 56, 92, 56), DY_OAK)
    hl.fill(im, (3, 59, 92, 59), DY_OAK_DK)
    for x in (4, 33, 63, 91):                                     # the chocks
        for k in range(5):
            hl.fill(im, (x - k, 51 + k, x + k, 51 + k), DY_OAK_LO if k else DY_OAK)
    for i, cx in enumerate((18, 48, 78)):
        cask_end(im, cx, 43, 13, i)
    for i, cx in enumerate((33, 63)):
        cask_end(im, cx, 20, 13, i + 1)
    px = im.load()
    for cx in (33, 63):                                           # the upper pair's shade on the three under them
        for dx in range(-9, 10):
            for y in range(31, 35):
                if px[cx + dx, y] in (DY_OAK, DY_OAK_HI):
                    px[cx + dx, y] = DY_OAK_LO
    hl.outline(im)
    return im


def red_maple():
    im, d = canvas(3, 4)                 # 96 x 128
    sa.ground_shade(d, 49, 119, 30)
    sa.stem(d, 44, 82, 123, 8)
    for k in range(3):                                            # the roots' flare
        hl.fill(im, (43 - k, 118 + k * 2, 43, 123), sa.P_BARK); hl.fill(im, (52, 118 + k * 2, 52 + k, 123), sa.P_BARK_LO)
    sa.limb(d, 45, 96, 26, 74, 4); sa.limb(d, 48, 92, 70, 70, 4); sa.limb(d, 46, 84, 47, 56, 5)
    sa.foliage(im, [(20, 62, 17, 13), (76, 62, 17, 13), (48, 68, 16, 10), (34, 50, 20, 14), (63, 50, 20, 14),
                 (14, 44, 12, 10), (82, 44, 12, 10), (26, 30, 18, 13), (70, 30, 18, 13), (48, 36, 18, 13),
                 (38, 17, 16, 11), (60, 16, 16, 11), (48, 11, 13, 9)], DY_FLAME, 21)
    hl.outline(im)
    return im


DY_CRAG = ((4, 176), (14, 150), (26, 118), (36, 96), (44, 80), (52, 68), (60, 68), (68, 82), (78, 94), (88, 98),
        (98, 90), (108, 70), (118, 58), (126, 54), (136, 56), (146, 72), (156, 94), (166, 118), (178, 150), (187, 176))


def dy_top(x):
    """The hill's skyline: two crags, by straight runs between whole-number points."""
    for (xa, ya), (xb, yb) in zip(DY_CRAG, DY_CRAG[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) // (xb - xa) + sa.speck(x // 2, 0, 31) % 3 - 1
    return 186


def dy_hill_roof(im, x0, y0, x1, y1):
    """A small hipped roof seen from above: tile courses, a ridge along the top, a lip along the eave."""
    px = im.load()
    for y in range(y0, y1 + 1):
        inset = max(0, 3 - (y - y0))
        for x in range(x0 + inset, x1 - inset + 1):
            px[x, y] = sa.roof_tile(x - x0, y - y0, DY_HILL_ROOF)
    hl.fill(im, (x0 + 5, y0 - 3, x1 - 5, y0 - 1), DY_HILL_ROOF[2])
    hl.fill(im, (x0 + 5, y0 - 1, x1 - 5, y0 - 1), DY_INK)
    hl.fill(im, (x0, y1 + 1, x1, y1 + 1), DY_HILL_ROOF[2]); hl.fill(im, (x0, y1 + 2, x1, y1 + 2), DY_INK)


def yamadera():
    """The hill behind the distillery, a backdrop for the room's north edge: a wooded mountain in
    autumn colour, two pale crags above the trees, the red hall on the higher one and the lookout
    stage on stilts on the other, the stone stair climbing through the wood from a gate at the foot."""
    im, d = canvas(6, 6)                 # 192 x 192
    px = im.load()
    # ---- the rock: pale tuff, its west faces lit, its east faces and its clefts in shade ----
    for x in range(4, 188):
        t = dy_top(x)
        fall = dy_top(min(187, x + 3)) - dy_top(max(4, x - 3))
        for y in range(t, 186):
            cleft = (x + y // 3 + sa.speck(y // 6, 0, 3) % 3) % 13
            ledge = (y + sa.speck(x // 16, 0, 5) % 9) % 23 if sa.speck(x // 16, y // 23, 7) < 45 else 9
            if cleft == 0 or (ledge == 0 and y - t > 6):
                c = DY_STONE_DK
            elif y - t < 2 or ledge == 1 or cleft == 1:
                c = DY_STONE_HI
            elif fall > 2 or cleft > 9:
                c = DY_STONE_LO
            elif fall < -2 or cleft < 5:
                c = DY_STONE_HI if (x + y) % 2 and cleft == 2 else DY_STONE
            else:
                c = DY_STONE if (x + y) % 2 or cleft < 8 else DY_STONE_LO
            px[x, y] = c
    # ---- the lookout stage on the west crag: a timber hall on a stage on tall stilts ----
    lx, ly = 56, 70
    for x in (lx - 14, lx - 5, lx + 4, lx + 13):
        hl.fill(im, (x, ly - 12, x + 1, ly + 8 + abs(x - lx) // 4), DY_TIMBER)
        hl.fill(im, (x + 1, ly - 12, x + 1, ly + 8 + abs(x - lx) // 4), DY_TIMBER_LO)
    hl.fill(im, (lx - 14, ly - 2, lx + 14, ly - 2), DY_TIMBER_LO)
    hl.fill(im, (lx - 18, ly - 16, lx + 18, ly - 12), DY_TIMBER); hl.fill(im, (lx - 18, ly - 16, lx + 18, ly - 16), DY_GINKGO[2])
    hl.fill(im, (lx - 18, ly - 12, lx + 18, ly - 12), DY_TIMBER_LO)
    hl.fill(im, (lx - 15, ly - 28, lx + 15, ly - 17), DY_TIMBER_LO)            # the open hall: posts, a rail
    for x in range(lx - 15, lx + 16, 6):
        hl.fill(im, (x, ly - 28, x, ly - 17), DY_TIMBER)
    hl.fill(im, (lx - 17, ly - 21, lx + 17, ly - 21), DY_GINKGO[2])
    dy_hill_roof(im, lx - 19, ly - 40, lx + 19, ly - 31)
    # ---- the red hall on the east pinnacle ----
    hx, hy = 128, 58
    hl.fill(im, (hx - 19, hy - 4, hx + 19, hy), DY_STONE_LO); hl.fill(im, (hx - 19, hy - 4, hx + 19, hy - 4), DY_STONE_HI)
    hl.fill(im, (hx - 19, hy, hx + 19, hy), DY_STONE_DK)
    hl.fill(im, (hx - 16, hy - 22, hx + 16, hy - 5), DY_BRICK)
    hl.fill(im, (hx - 16, hy - 22, hx + 16, hy - 21), DY_BRICK_LO)             # the eave's shade
    hl.fill(im, (hx - 16, hy - 20, hx - 15, hy - 5), DY_BRICK_HI); hl.fill(im, (hx + 11, hy - 20, hx + 16, hy - 5), DY_BRICK_LO)
    hl.fill(im, (hx - 6, hy - 18, hx + 5, hy - 5), DY_TIMBER_LO)               # the doors
    hl.fill(im, (hx - 1, hy - 18, hx, hy - 5), DY_TIMBER)
    for x0 in (hx - 14, hx + 8):
        hl.fill(im, (x0, hy - 18, x0 + 5, hy - 10), DY_STONE if x0 < hx else DY_STONE_LO)
        hl.fill(im, (x0 + 3, hy - 18, x0 + 3, hy - 10), DY_BRICK_LO); hl.fill(im, (x0, hy - 14, x0 + 5, hy - 14), DY_BRICK_LO)
    dy_hill_roof(im, hx - 21, hy - 37, hx + 21, hy - 25)
    hl.fill(im, (hx - 1, hy - 45, hx + 1, hy - 41), DY_GINKGO[1]); px[hx - 1, hy - 45] = DY_GINKGO[0]
    # ---- the wood: a canopy of small clumps in drifts of colour, upper rows first ----
    ramps = (DY_MOMIJI, DY_ICHO, DY_FIR, DY_MOMIJI, DY_ICHO, DY_FIR, DY_MOMIJI)
    clumps = []
    for j in range(14):
        for i in range(-1, 25):
            x = 4 + i * 8 + (j % 2) * 4 + sa.speck(i, j, 3) % 3 - 1
            y = 102 + j * 6 + sa.speck(j, i, 5) % 3
            if not 9 <= x <= 183 or y < dy_top(x) + 22 - (10 if 84 < x < 100 else 0) + sa.speck(i // 2, 1, 9) % 14:
                continue
            drift = sa.speck((i + j % 2) // 3, j // 2, 11) % 7 if sa.speck(i, j, 29) > 30 else sa.speck(i, j, 13) % 7
            clumps.append((y, x, drift, i * 13 + j))
    for x, y in ((40, 104), (72, 104), (150, 96), (104, 92), (168, 122), (24, 136), (112, 98), (84, 108)):   # trees in the clefts
        clumps.append((y, x, (x + y) % 7, x))
    for y, x, drift, seed in sorted(clumps):
        sa.foliage(im, [(x, y, 7, 6)], ramps[drift], seed)
    for x, y in ((16, 156), (34, 134), (50, 150), (74, 130), (118, 128), (142, 142), (160, 126), (176, 156),
                 (130, 166), (62, 172), (22, 178), (154, 178)):                # cedars standing through it
        sa.foliage(im, [(x, y - 3 - k * 4, 6 - k, 3) for k in range(5)], DY_FIR, x)
    # ---- the stair: stone treads zig-zagging up from the gate ----
    path = [(96, 180), (96, 164), (74, 150), (108, 136), (86, 122), (104, 108), (92, 97), (112, 82), (118, 66)]
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x, y = xa + (xb - xa) * i // n, ya + (yb - ya) * i // n
            hl.fill(im, (x - 2, y, x + 2, y), DY_STONE_HI if y % 2 == 0 else DY_STONE_LO)
            px[x - 3, y] = DY_TIMBER; px[x + 3, y] = DY_TIMBER
    for i, (x, y) in enumerate(((82, 160), (96, 146), (100, 128), (92, 115), (110, 142), (80, 136))):     # boughs over it
        sa.foliage(im, [(x, y, 6, 5)], ramps[(i * 2) % 7], i + 50)
    # ---- the gate at the foot: red posts under a little roof ----
    for x0 in (86, 103):
        hl.fill(im, (x0, 164, x0 + 3, 184), DY_BRICK); hl.fill(im, (x0, 164, x0, 184), DY_BRICK_HI)
        hl.fill(im, (x0 + 3, 164, x0 + 3, 184), DY_BRICK_LO)
    hl.fill(im, (84, 162, 108, 165), DY_BRICK_LO); hl.fill(im, (84, 162, 108, 162), DY_BRICK)
    dy_hill_roof(im, 80, 152, 112, 159)
    hl.fill(im, (91, 180, 101, 186), DY_STONE); hl.fill(im, (91, 180, 101, 180), DY_STONE_HI)
    hl.fill(im, (91, 183, 101, 183), DY_STONE_LO)
    # ---- its foot breaks into the ground: bushes and boulders, no straight edge ----
    for i, x in enumerate(range(6, 190, 9)):
        if not 82 < x < 110:
            sa.foliage(im, [(x, 182 + (i * 5) % 4, 7 + i % 2, 5)], ramps[(i * 3 + 1) % 7], i + 70)
    for x, w in ((30, 9), (66, 7), (120, 8), (164, 10)):
        for k, inset in enumerate((2, 1, 0, 0, 0, 0, 1)):
            hl.fill(im, (x + inset, 182 + k, x + w - inset, 182 + k), DY_STONE_HI if k < 1 else DY_STONE if k < 4 else DY_STONE_LO)
        hl.fill(im, (x + w - 1, 184, x + w, 187), DY_STONE_LO)
    hl.outline(im)
    return im
```
