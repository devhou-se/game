# 386: Kanazawa's Kenrokuen garden pieces in the house look

Part 2 of 3 of #312. All paths are under `gamev2/`; commands run from `gamev2/`. Coordinates are the tool's
half-size pixels (32 a cell), y from the top.

## Context

`tools/generate_kanazawa_art.py` draws fifteen sprites this ticket redraws in the GuttyKreum house look
("House look: GuttyKreum" in `docs/generators-and-checks.md`, helpers in `tools/house_look.py`):

| Key (`assets/sprites/<key>.png`) | Cells | Drawn by | Now: colours / not in a sheet |
|---|---|---|---|
| `kenrokuen-kotoji_0_0`, `kenrokuen-kotoji-water_0_0` | 2x3 | `kotoji(water)` | 14 / 12 and 11; the water one has 908 half-clear pixels |
| `kenrokuen-yukitsuri_0_0`, `-yukitsuri-small_0_0` | 3x4, 2x3 | `yukitsuri(cw, ch, pads, n)` | 15 / 14 |
| `kenrokuen-teahouse_0_0` | 4x3 | `teahouse()` | 26 / 20, 2684 half-clear pixels |
| `kenrokuen-bridge_0_0` | 3x1 | `stone_bridge()` | 10 / 9 |
| `garden-moss_0_0` | 1x1 | `garden_moss()`, `moss_px` | 4 / 4 |
| `garden-path-autotile_<role>` (9 roles) | 1x1 | `garden_path(role)`, `_edge_dist` | 4 to 12 / all |

What is wrong with them: the tool's own palette (`GRAN*`, `STRAW*`, `PINE*`, `PAPER*`, `SOOT`, `SHINGLE_P`,
`MOSS_*`), `polygon` / `ellipse` / `arc` / `line` shapes, the pine pads smooth `blob()` ellipses with an arc
under each, the tea house's roof the flat trapezoid of `roof()`, cream-white lantern and screen panes that
read as lit, soot black in the room, flat faces.

Found while designing:

- **None of the fifteen is registered or placed**: no key is in `config.json`, `tiled/`, `src/` or another
  tool, there is no Kenrokuen room, and `check_generators.py` does not run this tool. So no room render, world
  map, `play.js` output or in-game `?tod=night` view changes; the pictures to look at are the tool's `--sheet`
  and `--scenes` (the `kenrokuen` scene and its `_night.png`; `castle` and `nagamachi` each stand one
  `yukitsuri-small`). The same was true of #385.
- `main()` saves every sprite, and that rewrites about 40 unrelated PNG encodings (#384): revert them.
- #385 (landed) left `lead_hip()`, the `C_*` castle colours and `rect()` in this file; this design reuses
  them. #387 edits other functions of the same file.

The whole redrawn section was prototyped through the tool's own `build()` and `scenes()` and looked at; the
code is in the appendix. Measured on it: 13 / 14 colours for the two lanterns, 14 for both pines, 23 for the
tea house, 7 for the bridge, 4 for the moss, 4 to 13 for the path roles; nothing outside the sheets.

## Approach

Rewrite the Kenrokuen section in place from the appendix. Keys, sizes, `PIECES` meta (`solid`, `walk`, `lit`,
`layer`), the pad tables and rope counts, `ROLES` and `_edge_dist` are unchanged. The rules:

1. **Recipe**: half size, doubled by `build()`; `rect()` and pixel access only; whole-number arithmetic
   (`math.isqrt` places the rope ends; `_edge_dist` keeps its `math.hypot`, see Risks); light from the upper
   left; `hl.outline(im)` last.
2. **Colours**: one block of `G_*` sheet colours. Granite `fafcfd dae2e4 bcc7cc a4b0b5 848295 646e86 47485d`;
   lichen `83af6f 678e57 506b6b`; straw and bamboo in the gold ramp `f3d890 c6a663 a7843b 86624f`; shingles
   in the cream-brown ramp; paper `fafcfd e4cecc be9e8c`; moss `357570 488582 6c8e7f 2e4040` (blue-green, so it
   is not the pack's grass `678e57`); gravel `d7d0ba eae9e8 cdc8c5 b3aaa0`; timber and the dark room are
   #385's `C_TB*`, `C_DARK*`; bark, needles and `speck` / `foliage` are `generate_sendai_art`'s.
3. **Nothing lit**: the lantern's light box is dim gold `c6a663` with a 2x2 `f3d890` corner behind `646e86`
   bars; the tea house's open room is `2c2d51` (no glass, so no glare, as #385's openings); its screens are
   paper with daylight across them on a slant, no yellow. The `lit` meta stays, so the night preview still
   puts a halo on the lantern and the room.
4. **Shadows**: the one translucent colour is `P_SHADE` (`2a3151` at alpha 90, the pack trees' ground shade),
   painted by `cast()` after the outline and only on clear pixels (as #328's `cast`), so a shadow is never
   inked. Water marks (`8ec2fa`, pond-autotile's highlight) go on after the outline too.
5. **Ground tiles are exempt from "no colour on half"**: the moss floor is 61% of its tile and gravel 45 to
   78% of a path tile, as the pack's own grass is one colour. A busier moss was tried and read as noise.

| Sprite | What is drawn |
|---|---|
| `kotoji` | The same lantern: a faceted rock (three tones by a diagonal, a crack, a ragged moss band at its foot), two bowed legs with a lit west edge, platform, light box, a six-sided roof (lit fall, front, shaded fall, upturned corners), jewel. Dry: a stepping stone with a shaded side. Water: the leg is cut at y 88, a `8ec2fa` waterline and ring, the ring's inside in shade. |
| `yukitsuri` | Back ropes `a7843b`, a leaning trunk and two boughs in bark tones, the bamboo pole with nodes, the pads as `foliage(..., NEEDLE, cw)` (ragged, pale green to teal to blue to purple), front ropes `c6a663` with two glints and a peg knot, the straw knot, a ground shade. The trunk stops at the topmost pad. |
| `teahouse` | A hipped cedar-shingle roof seen from above (`lead_hip(..., pal=G_SHINGLE)`) with moss in its courses, the eave's shadow, paper screens either side of the open room (tatami, scroll, table, bowl), rail, veranda boards, posts on stones, the floor's shadow and ripples on the water. |
| `stone_bridge` | Flat, from above: six slabs toned `a4b0b5 bcc7cc dae2e4 dae2e4 bcc7cc a4b0b5` for the arch, each with lit west and north edges and a joint, two kerbs with joints, four corner posts. Ink on rows 0 and 31 only: the two ends are open, they meet the path. No `hl.outline`. |
| `garden_moss` | A floor heaped into the eight `MOUNDS` (unchanged table), each ragged, with a lit rim to the upper left and a dark one to the lower right. Periodic at 32. |
| `garden_path` | `_path_part` (from `_edge_dist`: under 3.2 moss, under 6.2 stone, else gravel, the thresholds of today) is read past the tile's edge, so stones are lit on their north and west, shaded south and east, and throw 1px of shade on the gravel or moss whatever tile they are in. Joints at `PATH_JOINTS` along a side. Moss is `moss_px`, so the outer 3 pixels of a moss side equal `garden-moss`. |

Flat on purpose: the bridge and the ten ground tiles (they are walked on).

## Changes

### `tools/generate_kanazawa_art.py`

- Import line 119: add `speck, foliage, NEEDLE, P_SHADE, P_BARK, P_BARK_HI, P_BARK_LO` from
  `generate_sendai_art`; drop `blob, PINE, PINE_HI, PINE_LO, PINE_DK, BARK, BARK_LO` (only the old
  `yukitsuri` used them; grep before dropping).
- After line 241 (`C_RIDGE, ... = ...`): `LEAD_PAL = (C_LEAD, C_LEAD_LIT, C_LEAD_SH, C_RIDGE, C_RIDGE_HI,
  C_EAVE, C_EAVE_DK)`.
- `lead_hip`: the signature gains `pal=None`, and the body's first line becomes
  `C_LEAD, C_LEAD_LIT, C_LEAD_SH, C_RIDGE, C_RIDGE_HI, C_EAVE, C_EAVE_DK = pal or LEAD_PAL`; one sentence in
  its docstring. Nothing else in it changes, so the castle pieces are byte-equal (#385's rebuild test holds it).
- Replace lines 1041-1332 (the Kenrokuen section: `kotoji` to `garden_path`, with `MOSS_B/M/H/S`) by the
  appendix. `_edge_dist` and `MOUNDS` are kept as they are.
- `PIECES` / `FAMILIES` descriptions, wording only: kotoji "its light box unlit, dim gold"; kotoji-water "a
  ring on the water round it"; yukitsuri unchanged; teahouse "a hipped cedar-shingle roof seen from above,
  moss in its courses"; moss and path unchanged. No meta changes.
- Docstring: the sentence at line 100 ("The ten building fronts ... are drawn in the house look") also names
  the garden pieces (#386); the Kenrokuen lines stay true.
- Do not touch any other builder, the old palette constants other builders use (`GRAN*`, `MOSS`, `PAPER*`,
  `SOOT*`, `STRAW*`, `ROPE`, `WATER*`, `SHINGLE_P`), or the names other tools import (`text, kana, text_w,
  h3, shade, curve_rows, roof, night, FONT, KANA`).

### `assets/sprites/`

The fifteen PNGs, rewritten by the tool. Every other PNG the run touches is reverted.

### `tools/tests/kanazawa-art.test.js`

The tests below, and a line for #386 in the header comment.

### `docs/generators-and-checks.md`

One sentence after the #385 one in the Kanazawa paragraph of "House look: GuttyKreum": Kenrokuen's lantern,
pines, tea house, bridge, moss and path (#386) are drawn the same way; the ground tiles and the bridge are
flat, and `2a3151` at alpha 90 is the only translucent colour.

## Data and interfaces

None. No key, size, anchor, cell, meta, `config.json`, map or placement changes. `lead_hip` gains an optional
argument.

## Tests

Add to `tools/tests/kanazawa-art.test.js` (names end `(#386)`; `GARDEN` maps the fifteen keys to their
cells, `STANDING` is the two lanterns, the two pines and the tea house):

1. **Sizes**: each is cells x 64, every pixel a 2x2 block; alpha is 0, 255, or 90 with the colour `2a3151`;
   the bridge and the ten tiles are fully opaque.
2. **Colours** (alpha 255 pixels): only sheet colours; at most 24 for the tea house, 16 for the rest; none of
   `f6dc8c`, `f2c66a`, `f9c22e`, `2b373c`, `000000`; `f3d890` under 3%; for `STANDING` and the bridge, none on
   more than half.
3. **Silhouette**: in `STANDING`, every alpha 255 pixel with a 4-neighbour inside the canvas that is not
   alpha 255 is `0a1627` or `8ec2fa`. The bridge's rows 0-1 and 62-63 are all `0a1627`.
4. **Joins** (committed PNGs): for every role and every side its name has (`n`, `s`, `e`, `w`), the outer 6
   rows or columns on that side equal `garden-moss_0_0`'s. With a pixel's kind as moss (`357570 488582 6c8e7f
   2e4040`), gravel (`d7d0ba eae9e8 cdc8c5 b3aaa0`) or stone (anything else), the last column of A has the
   kinds of the first column of B for `corner-nw|edge-n`, `edge-n|edge-n`, `edge-n|corner-ne`,
   `corner-sw|edge-s`, `edge-s|edge-s`, `edge-s|corner-se`, `edge-w|center`, `center|edge-e`; the last row of
   A has the kinds of the first row of B for `corner-nw/edge-w`, `edge-w/edge-w`, `edge-w/corner-sw`,
   `corner-ne/edge-e`, `edge-e/edge-e`, `edge-e/corner-se`, `edge-n/center`, `center/edge-s`.
5. **Rectangles and pixels only**: the source of `kotoji`, `g_rope`, `yukitsuri`, `teahouse`, `stone_bridge`,
   `moss_px`, `garden_moss`, `_path_part`, `garden_path`, `spans`, `lerp_rows`, `cast`, `dots` (cut as #307's
   test cuts a builder) has none of #385's list, nor `blob(`, `math.sin`, `math.cos`.
6. **The tool draws what is committed**: `rebuild(Object.keys(GARDEN))`.

The implementer, in order:

```bash
mkdir -p /tmp/386/before && cp assets/sprites/kenrokuen-*.png assets/sprites/garden-*.png /tmp/386/before/
python3 tools/generate_kanazawa_art.py --sheet /tmp/386/before/sheet.png --scenes /tmp/386/before/scenes
git checkout -- assets/sprites                        # before any edit: the "before" pictures
# ... edit the tool ...
python3 tools/generate_kanazawa_art.py --sheet /tmp/386/sheet.png --scenes /tmp/386/scenes
git status --short assets/sprites                     # then git checkout -- every PNG that is not one of the fifteen
python3 tools/house_look.py --sheet /tmp/386/contact.png --scale 2 assets/sprites/kenrokuen-*.png \
    assets/sprites/garden-moss_0_0.png assets/sprites/garden-path-autotile_*.png
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
    && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

- The `station`, `chaya` and `katamachi` scenes and their nights are pixel-equal before and after; `castle`
  and `nagamachi` differ only where their one `yukitsuri-small` stands.
- Look at `kanazawa_art_kenrokuen.png` beside the "before" one (every path role beside its neighbours, the
  moss against the pond and the pack trees), at its `_night.png` (no window or screen may read as lit; the
  two halos are the `lit` meta), and at the contact sheet beside a done model (`sendai-pine_0_0.png`). Save
  before/after images to `/work/media/`, and name in the summary any sprite that still reads flat.
- `git status` shows only the tool, the fifteen PNGs, the test file and the doc. No town's picture changes,
  so `check_generators.py` reports no drift and the world map is not rebuilt.
- The browser regression (`tools/browser/regress.js`) cannot see these sprites: run it as the house rule
  asks, or say it was not run and why. There is no in-game `?tod=night` view of them either.
- Commit as `gamev2: ... (#386)`; rooms touched: none.

## Risks and open questions

- **Same file as #387 and #300**: touch only the functions and lines named above, so a rebase is mechanical.
- **Not seen in the game**: nothing places these sprites; a later map ticket should look at them once with
  `?tod=night` and against the real pond and grass.
- **Borrowed helpers**: `foliage`, `speck`, `roof_tile`, `NEEDLE`, `P_SHADE` and `P_BARK*` are
  `generate_sendai_art.py`'s; a change there redraws these, and test 6 says so.
- **`_edge_dist` uses `math.hypot`**: kept, as the ticket asks. Its result is compared with 3.2, 6.2 and 8,
  and 9 minus the root of a whole number can only meet 8 exactly (at root 1, which is exact), so no machine
  rounds a pixel to the other side.
- **Taste, for the review**: the moss is bluer than the pack's grass on purpose; the rope cone makes ink 21
  to 24% of the pines; the lantern's light box is gold by day (a lamp, by the ticket's rule), not dark.

## Appendix: the prototype's drawing code

The Kenrokuen section as it stands in the tool after the change (the prototype ran exactly this, with
`lead_hip` changed as above).

```python
# ==============================================================================
# Kenrokuen
# ==============================================================================
# ---- the garden's colours: every one a GuttyKreum sheet colour -------------------------------
G_ST_HI, G_ST_LT, G_ST, G_ST_MD = rgb('fafcfd'), rgb('dae2e4'), rgb('bcc7cc'), rgb('a4b0b5')   # granite
G_ST_LO, G_ST_DK, G_ST_DEEP = rgb('848295'), rgb('646e86'), rgb('47485d')
G_LICHEN, G_LICHEN_LO, G_LICHEN_DK = rgb('83af6f'), rgb('678e57'), rgb('506b6b')
G_ROPE, G_ROPE_HI, G_ROPE_LO, G_ROPE_DK = rgb('c6a663'), rgb('f3d890'), rgb('a7843b'), rgb('86624f')
G_RING = rgb('8ec2fa')                                           # pond-autotile's own highlight
# cedar-bark shingles in roof_tile's order (course line, joint, lit lip, shade, base), then a
# fall facing west and one facing east; ridge, its lit row, the eave and its dark row
G_SHINGLE = ([rgb(c) for c in ('594b45', '7c5d56', 'be9e8c', '8e7366', 'a68777')],
             [rgb(c) for c in ('6d574e', '8e7366', 'e4cecc', 'a68777', 'be9e8c')],
             [rgb(c) for c in ('3c3029', '594b45', '8e7366', '6d574e', '7c5d56')],
             rgb('8e7366'), rgb('be9e8c'), rgb('594b45'), rgb('3c3029'))
G_PAPER, G_PAPER_HI, G_PAPER_LO = rgb('e4cecc'), rgb('fafcfd'), rgb('be9e8c')
G_MOSS = [rgb(c) for c in ('357570', '488582', '6c8e7f', '2e4040')]     # floor, cushion, lit rim, shade
G_GRAVEL, G_GRAVEL_HI, G_GRAVEL_LO, G_GRAVEL_SH = rgb('d7d0ba'), rgb('eae9e8'), rgb('cdc8c5'), rgb('b3aaa0')


def spans(im, y0, rows, tones):
    """A stepped shape: one (x0, x1) a row from y0 down, each row `tones` =
    (lit left edge, base, shaded right edge) with the edge 1px and the shade 2."""
    lit, base, lo = tones
    for n, (x0, x1) in enumerate(rows):
        rect(im, x0, y0 + n, x1, y0 + n, base)
        rect(im, x0, y0 + n, x0, y0 + n, lit)
        rect(im, max(x0 + 1, x1 - 1), y0 + n, x1, y0 + n, lo)


def lerp_rows(knots):
    """(y, x) for every row of a stepped line through (x, y) knots, whole numbers only."""
    out = []
    for (xa, ya), (xb, yb) in zip(knots, knots[1:]):
        for y in range(ya, yb + (1 if (xb, yb) == knots[-1] else 0)):
            out.append((y, xa + (xb - xa) * (y - ya) // (yb - ya)))
    return out


def cast(im, y0, rows):
    """The shadow on the ground or the water: P_SHADE on the pixels still clear
    (so it goes on after the outline, and is not inked)."""
    px = im.load()
    for n, (x0, x1) in enumerate(rows):
        for x in range(max(0, x0), min(im.width - 1, x1) + 1):
            if px[x, y0 + n][3] == 0:
                px[x, y0 + n] = P_SHADE


def dots(im, pts, c):
    px = im.load()
    for x, y in pts:
        px[x, y] = c


KOTOJI_ROOF = ((30, 34), (28, 36), (26, 38), (24, 40), (22, 42), (20, 44), (18, 46), (16, 48),      # y 10 on
               (14, 50), (13, 51), (12, 52), (9, 55), (9, 55), (9, 55))
KOTOJI_JEWEL = ((32, 32), (30, 34), (29, 35), (28, 36), (28, 36), (28, 36), (29, 35), (30, 34))     # y 1 on
STEP_STONE = ((8, 21), (5, 24), (4, 25), (3, 26), (3, 26), (3, 26), (4, 25), (5, 24), (8, 21))      # y 84 on
RING = ((9, 19), (5, 23), (3, 25), (2, 26), (2, 26), (2, 26), (2, 26), (2, 26), (3, 25), (5, 23), (9, 19))   # y 84 on


def kotoji(water=False):
    im, d = canvas(2, 3)                 # 64 x 96
    px = im.load()
    # ---- the rock on the bank the short leg stands on: three facets, moss up its foot
    left = dict(lerp_rows([(47, 66), (41, 70), (36, 80), (34, 94)]))
    right = dict(lerp_rows([(54, 66), (60, 74), (63, 84), (63, 94)]))
    for y in range(66, 94):
        l, r = left[y], right[y]
        for x in range(l, r + 1):
            t = (x - l) * 100 // (r - l + 1) + (y - 66)
            c = G_ST_LT if t < 30 else (G_ST_MD if t < 64 else G_ST_LO)
            top = 91 - speck(x // 2, 0, 2) % 4                    # moss up its foot, its upper edge ragged
            if y >= top:
                c = G_LICHEN if y == top else (G_LICHEN_DK if x > r - 6 or speck(x, y, 5) < 12 else G_LICHEN_LO)
            px[x, y] = c
        px[l, y] = G_ST_HI if y < 80 else px[l, y]
    for y, x in lerp_rows([(45, 76), (49, 85), (47, 93)]):        # a crack down it
        px[x, y] = G_ST_DK
    dots(im, ((42, 72), (45, 69), (50, 68), (38, 81), (58, 76)), G_LICHEN)
    dots(im, ((43, 72), (46, 69), (51, 68), (39, 81), (59, 76)), G_LICHEN_LO)
    # ---- what the long leg stands on: a low stone in the shallows (dry) or the pond itself
    if not water:
        spans(im, 84, STEP_STONE, (G_ST_LT, G_ST, G_ST_LO))
        rect(im, 8, 84, 21, 84, G_ST_HI)
        for n, (x0, x1) in enumerate(STEP_STONE[5:]):             # its side, in shade
            rect(im, x0, 89 + n, x1, 89 + n, G_ST_LO)
            rect(im, x0, 89 + n, x0 + 1, 89 + n, G_ST_MD)
        rect(im, 8, 92, 21, 92, G_ST_DK)
        spans(im, 88, ((25, 37), (23, 39), (22, 40), (22, 40), (23, 39), (26, 36)), (G_ST, G_ST_MD, G_ST_LO))
        rect(im, 23, 92, 39, 92, G_ST_LO); rect(im, 26, 93, 36, 93, G_ST_DK)
    # ---- the two legs, bowed: the long one to the stone, the short one to the rock
    for knots in ([(25, 46), (22, 58), (18, 71), (14, 89 if water else 87)], [(39, 46), (43, 54), (47, 61), (50, 68)]):
        for y, x in lerp_rows(knots):
            rect(im, x - 3, y, x + 2, y, G_ST)
            rect(im, x - 3, y, x - 3, y, G_ST_HI); rect(im, x - 2, y, x - 2, y, G_ST_LT)
            rect(im, x + 1, y, x + 2, y, G_ST_LO)
    if not water:
        rect(im, 9, 84, 19, 87, G_ST); rect(im, 9, 84, 19, 84, G_ST_HI); rect(im, 18, 85, 19, 87, G_ST_LO)   # its foot
    # ---- the platform, the light box (a window in dim gold: never lit), the roof, the jewel
    rect(im, 21, 38, 43, 40, G_ST_LO); rect(im, 21, 38, 43, 38, G_ST_MD); rect(im, 40, 38, 43, 40, G_ST_DK)
    rect(im, 18, 41, 46, 46, G_ST)
    rect(im, 18, 41, 46, 41, G_ST_HI); rect(im, 18, 42, 18, 46, G_ST_LT)
    rect(im, 42, 42, 46, 46, G_ST_MD); rect(im, 18, 45, 46, 46, G_ST_LO); rect(im, 42, 45, 46, 46, G_ST_DK)
    rect(im, 24, 27, 40, 37, G_ST)
    rect(im, 24, 27, 24, 37, G_ST_LT); rect(im, 37, 27, 40, 37, G_ST_MD); rect(im, 24, 27, 40, 27, G_ST_LO)
    rect(im, 27, 29, 35, 36, G_ST_DK)
    rect(im, 28, 30, 34, 35, G_ROPE); rect(im, 28, 30, 29, 31, G_ROPE_HI)
    rect(im, 31, 30, 31, 35, G_ST_DK); rect(im, 28, 33, 34, 33, G_ST_DK)
    for n, (x0, x1) in enumerate(KOTOJI_ROOF):                    # six-sided: a lit fall, the front, a shaded fall
        y = 10 + n
        a, b = 32 - n * 2 // 3 - 1, 32 + n * 2 // 3 + 1
        rect(im, x0, y, x1, y, G_ST)
        rect(im, x0, y, a, y, G_ST_LT); rect(im, b, y, x1, y, G_ST_MD)
        rect(im, a, y, a, y, G_ST_HI); rect(im, b, y, b, y, G_ST_LO)
        rect(im, x0, y, x0, y, G_ST_HI); rect(im, x1 - 1, y, x1, y, G_ST_LO)
    rect(im, 9, 24, 55, 24, G_ST_LO); rect(im, 9, 24, 22, 24, G_ST_MD)          # the eave's face
    rect(im, 11, 25, 53, 26, G_ST_DK); rect(im, 14, 26, 50, 26, G_ST_DEEP)      # under it
    dots(im, ((9, 20), (10, 20), (9, 19), (54, 20), (55, 20), (55, 19)), G_ST_MD)    # the corners turn up
    dots(im, ((9, 19), (9, 20)), G_ST_HI)
    dots(im, ((18, 20), (26, 16), (38, 17), (46, 21), (30, 13)), G_LICHEN)      # lichen on the roof
    dots(im, ((19, 21), (27, 17), (39, 18), (47, 22), (31, 14)), G_LICHEN_LO)
    spans(im, 1, KOTOJI_JEWEL, (G_ST_LT, G_ST, G_ST_LO))
    rect(im, 30, 9, 34, 9, G_ST_DK)
    dots(im, ((30, 3), (31, 3), (30, 4)), G_ST_HI)
    rect(im, 30, 7, 34, 8, G_ST_MD); rect(im, 33, 7, 34, 8, G_ST_LO)
    hl.outline(im)
    if water:                            # the leg goes down into the pond: cut at the waterline, its shadow, a ring
        for y in range(89, 96):
            for x in range(0, 30):
                px[x, y] = CLEAR
        rect(im, 10, 89, 17, 89, G_RING)                              # the water against the leg
        cast(im, 84, RING)
        for n, (x0, x1) in enumerate(RING):
            y = 84 + n
            ring = range(x0, x1 + 1) if n in (0, len(RING) - 1) else (
                [x for x in range(x0, x1 + 1) if x < RING[n - 1][0] or x > RING[n - 1][1]
                 or x < RING[n + 1][0] or x > RING[n + 1][1]])
            for x in ring:
                if px[x, y][3] != 255:
                    px[x, y] = G_RING
    else:
        cast(im, 93, ((6, 23), (9, 24)))
    return im


def g_rope(im, x0, y0, x1, y1, c, glint=None):
    """A rope from the pole's top to the rim, a pixel a step; `glint` lights two points on it."""
    px = im.load()
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for n in range(steps + 1):
        x, y = x0 + (x1 - x0) * n // steps, y0 + (y1 - y0) * n // steps
        px[x, y] = glint if glint and n in (steps // 6, steps // 3) else c


def yukitsuri(cw, ch, pads, n):
    def build():
        im, d = canvas(cw, ch)
        px = im.load()
        W, H = cw * 32, ch * 32
        cx = W // 2
        rim_y, rx, ry = H - 20, W // 2 - 3, 7 + cw
        ends = []                                                 # n rope ends round the rim: (x, y, in front)
        for k in range(n // 2):
            dx = -rx + (2 * k + 1) * rx * 2 // n
            dy = math.isqrt(ry * ry * (rx * rx - dx * dx)) // rx
            ends += [(cx + dx, rim_y - dy, False), (cx + dx, rim_y + dy, True)]
        for x, y, front in ends:                                  # the ropes round the back
            if not front:
                g_rope(im, cx, 5, x, y, G_ROPE_LO)
        # the trunk, leaning, and two boughs
        for knots, w in (([(cx - 3, H - 6), (cx - 5, H - 30), (cx + 2, H // 2), (cx + 5, min(p[1] for p in pads))], 5),):
            for y, x in lerp_rows(knots[::-1]):
                rect(im, x - 2, y, x + w - 3, y, P_BARK)
                rect(im, x - 2, y, x - 2, y, P_BARK_HI); rect(im, x + w - 4, y, x + w - 3, y, P_BARK_LO)
        for x0, y0, x1, y1 in ((cx - 5, H - 30, cx - rx + 12, H - 40), (cx, H - 34, cx + rx - 12, H - 44)):
            steps = abs(x1 - x0)
            for s in range(steps + 1):
                x, y = x0 + (x1 - x0) * s // steps, y0 + (y1 - y0) * s // steps
                rect(im, x, y, x, y + 1, P_BARK); rect(im, x, y + 2, x, y + 2, P_BARK_LO)
        rect(im, cx - 7, H - 8, cx + 1, H - 5, P_BARK_LO); rect(im, cx - 7, H - 8, cx - 4, H - 7, P_BARK)   # the root
        # the bamboo pole the ropes hang from
        rect(im, cx + 1, 6, cx + 2, H - 6, G_ROPE); rect(im, cx + 2, 6, cx + 2, H - 6, G_ROPE_LO)
        for y in range(18, H - 10, 14):
            rect(im, cx + 1, y, cx + 2, y, G_ROPE_DK)
        foliage(im, [(cx + ox, y, prx, pry) for ox, y, prx, pry in pads], NEEDLE, cw)   # the pads, back to front
        for x, y, front in ends:                                  # the ropes in front, a knot where each is pegged
            if front:
                g_rope(im, cx, 5, x, y, G_ROPE, G_ROPE_HI if abs(x - cx) * 4 < rx * 3 else None)
                px[x, y] = G_ROPE_DK
                px[x, y + 1] = G_ROPE_DK
        rect(im, cx - 2, 1, cx + 3, 7, G_ROPE)                    # the straw knot at the top
        rect(im, cx - 2, 1, cx - 2, 7, G_ROPE_HI); rect(im, cx + 3, 2, cx + 3, 7, G_ROPE_LO)
        rect(im, cx - 2, 5, cx + 3, 5, G_ROPE_DK)
        rect(im, cx, 0, cx + 1, 0, G_ROPE)
        hl.outline(im)
        cast(im, H - 13, [(cx - rx + 6 + i, cx + rx - 6 - i) for i in (6, 3, 1, 0, 0, 0, 0, 0, 1, 3, 6)])
        return im
    return build


def teahouse():
    im, d = canvas(4, 3)                 # 128 x 96; it stands on posts in the bottom row
    px = im.load()
    # ---- the posts in the water, each on a stone
    for x in (14, 46, 79, 111):
        rect(im, x, 76, x + 3, 90, C_TB)
        rect(im, x, 76, x, 90, C_TB_HI); rect(im, x + 3, 76, x + 3, 90, C_TB_DK)
        rect(im, x - 2, 89, x + 5, 93, G_ST_MD); rect(im, x - 2, 89, x + 5, 89, G_ST_LT)
        rect(im, x - 2, 93, x + 5, 93, G_ST_DK); rect(im, x + 4, 90, x + 5, 92, G_ST_LO)
    rect(im, 18, 79, 110, 80, C_TB_DK)                            # the tie under the floor
    for x in (14, 46, 79, 111):
        rect(im, x, 79, x, 80, C_TB_LO)
    # ---- the veranda: its boards from above, its edge, the shade under it
    rect(im, 6, 69, 121, 75, C_TB)
    rect(im, 6, 69, 121, 70, C_TB_HI); rect(im, 6, 69, 121, 69, G_PAPER_LO)
    rect(im, 6, 74, 121, 75, C_TB_DK); rect(im, 6, 73, 121, 73, C_TB_LO)
    for x in range(11, 120, 8):
        rect(im, x, 70, x, 72, C_TB_LO)
    # ---- the room: paper screens either side, the middle slid open on a dark room
    rect(im, 12, 37, 115, 68, C_TB)
    rect(im, 12, 37, 115, 39, C_TB_DK)                            # the eave's shadow
    rect(im, 12, 40, 115, 44, C_TB); rect(im, 12, 40, 115, 40, C_TB_LO); rect(im, 12, 44, 115, 44, C_TB_LO)
    for x0, x1 in ((15, 43), (84, 112)):
        rect(im, x0, 46, x1, 67, G_PAPER)
        for y in range(48, 68):                                   # the light falls across it on a slant
            rect(im, x0, y, x0 + 11 - (y - 48) // 2, y, G_PAPER_HI)
            rect(im, x1 - 3 - (y - 48) // 3, y, x1, y, G_PAPER_LO)
        rect(im, x0, 46, x1, 47, G_PAPER_LO)                      # the lintel's shade
        for x in range(x0 + 7, x1, 7):
            rect(im, x, 46, x, 67, C_TB_HI)
        for y in (54, 61):
            rect(im, x0, y, x1, y, C_TB_HI)
    rect(im, 47, 46, 80, 67, C_DARK)
    rect(im, 47, 46, 80, 48, C_DARK_LO)
    rect(im, 47, 60, 80, 67, G_PAPER_LO)                          # tatami
    rect(im, 47, 60, 80, 60, G_PAPER); rect(im, 63, 61, 63, 67, H_EARTH); rect(im, 47, 66, 80, 67, H_EARTH)
    rect(im, 68, 48, 76, 58, G_PAPER); rect(im, 70, 50, 74, 56, G_PAPER_LO)      # a hanging scroll
    rect(im, 72, 51, 72, 55, C_TB_DK)
    rect(im, 52, 55, 60, 59, C_TB_LO); rect(im, 52, 55, 60, 55, C_TB_HI)         # a low table, a tea bowl
    rect(im, 55, 52, 57, 54, G_LICHEN_DK); rect(im, 55, 52, 57, 52, G_LICHEN_LO)
    for x in (12, 45, 81, 114):                                   # the posts of the frame
        rect(im, x, 40, x + 1, 68, C_TB_LO)
    rect(im, 12, 40, 12, 68, C_TB_HI)
    rect(im, 8, 62, 119, 62, C_TB_LO)                             # the rail
    for x in (8, 26, 44, 83, 101, 119):
        rect(im, x, 62, x, 68, C_TB_LO)
    # ---- the shingled roof, hipped, seen from above; moss in its courses
    lead_hip(im, 1, 126, 11, 32, 22, 9, pal=G_SHINGLE)
    for x, y in ((20, 29), (40, 21), (58, 27), (86, 17), (97, 30), (70, 31), (47, 15)):
        dots(im, ((x, y), (x + 1, y)), G_LICHEN_LO)
        dots(im, ((x, y + 1),), G_LICHEN_DK)
    hl.outline(im)
    cast(im, 77, [(8, 119)] * 9 + [(9, 118)])                     # the floor's shadow on the water
    for x0, x1, y in ((22, 34, 91), (56, 70, 93), (90, 100, 91), (36, 42, 94)):
        for x in range(x0, x1 + 1):
            if px[x, y][3] == 0:
                px[x, y] = G_RING                                 # ripples
    return im


BRIDGE_DECK = (G_ST_MD, G_ST, G_ST_LT, G_ST_LT, G_ST, G_ST_MD)    # a slab each: the crown of the arch catches the light


def stone_bridge():
    """The garden's arched stone bridge from straight above, as
    kanazawa-canal-bridge is drawn: kerbs along its two sides, the slabs of the
    deck between, lighter over the crown of the arch and darker where it comes
    down to the banks. Inked along the two sides over the water, open at the
    two ends that meet the path."""
    im, d = canvas(3, 1)                 # 96 x 32, flat: walked ON, east-west
    px = im.load()
    for y in range(6, 26):
        for x in range(96):
            base = BRIDGE_DECK[x // 16]
            lit = G_ST_HI if base == G_ST_LT else (G_ST_LT if base == G_ST else G_ST)
            lo = G_ST_LO if base == G_ST_MD else G_ST_MD
            c = base
            if x % 16 == 15:
                c = G_ST_LO if base != G_ST_MD else G_ST_DK       # the joint between two slabs
            elif x % 16 == 0 or y == 7:
                c = lit                                           # a slab's lit edges
            elif y == 25 or x % 16 == 14:
                c = lo
            elif y == 16 and x // 16 % 2 == 0:
                c = lo                                            # a slab cut in two
            elif speck(x, y, 5) < 3:
                c = lo
            if y == 6:
                c = G_ST_LO if x % 16 != 15 else G_ST_DK          # the north kerb's shadow on the deck
            px[x, y] = c
    for y0 in (1, 26):                                            # the kerbs: a lit top, joints, a dark foot
        rect(im, 0, y0, 95, y0 + 4, G_ST)
        rect(im, 0, y0, 95, y0, G_ST_HI); rect(im, 0, y0 + 1, 95, y0 + 1, G_ST_LT)
        rect(im, 0, y0 + 4, 95, y0 + 4, G_ST_DK)
        for x in range(11 if y0 == 1 else 5, 96, 12):
            rect(im, x, y0 + 1, x, y0 + 3, G_ST_LO)
    for x0 in (0, 90):                                            # a post at each corner
        for y0 in (1, 25):
            rect(im, x0, y0, x0 + 5, y0 + 5, G_ST_MD)
            rect(im, x0, y0, x0 + 5, y0, G_ST_HI); rect(im, x0, y0, x0, y0 + 5, G_ST_HI)
            rect(im, x0 + 1, y0 + 1, x0 + 4, y0 + 1, G_ST_LT)
            rect(im, x0 + 5, y0 + 1, x0 + 5, y0 + 5, G_ST_DK); rect(im, x0, y0 + 5, x0 + 5, y0 + 5, G_ST_DK)
    rect(im, 0, 0, 95, 0, hl.INK); rect(im, 0, 31, 95, 31, hl.INK)
    return im


MOUNDS = ((6, 5, 5, 3), (20, 3, 6, 3), (13, 12, 6, 4), (28, 14, 5, 3),          # cx, cy, rx, ry
          (4, 20, 5, 3), (21, 22, 7, 4), (11, 28, 5, 3), (30, 28, 4, 3))


def moss_px(x, y):
    """Kenrokuen's moss at drawn pixel (x, y) of a 32px tile: a deep floor
    heaped into ragged cushions, each with a lit rim to the upper left and a
    dark one under its lower right edge. Periodic at 32 both ways; whole
    numbers only."""
    floor, cushion, lit, lo = G_MOSS
    x, y = x % 32, y % 32
    for n, (cx, cy, rx, ry) in enumerate(MOUNDS):
        dx = (x - cx + 16) % 32 - 16
        dy = (y - cy + 16) % 32 - 16
        q = (dx * dx * ry * ry + dy * dy * rx * rx) * 100 // (rx * rx * ry * ry)
        if q <= 80 + speck(x // 2, y, n) // 5:
            s = (dx * ry + dy * rx) * 100 // (rx * ry)
            return lo if s > 72 else (lit if s < -50 and q > 30 else cushion)
    return floor


def garden_moss():
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    for y in range(32):
        for x in range(32):
            px[x, y] = moss_px(x, y)
    return im


def _edge_dist(role, x, y, r=9):
    """How far inside the patch a pixel is, from the sides the role names
    (a rounded corner of radius r where two meet)."""
    tail = '' if role == 'center' else role.split('-')[-1]
    a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
    b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
    if a < r and b < r:
        return r - math.hypot(r - a, r - b)
    return min(a, b)


PATH_JOINTS = (4, 10, 15, 21, 26, 31)                             # where one edging stone ends, along a side


def _path_part(role, x, y):
    """0 moss, 1 an edging stone, 2 gravel. Good past the tile's edge too: the next tile's part."""
    dist = _edge_dist(role, x, y)
    return 0 if dist < 3.2 else (1 if dist < 6.2 else 2)


def garden_path(role):
    """Kenrokuen's paths: pale raked gravel between lines of edging stones,
    moss beyond them. The stones are lit on their north and west sides and
    throw a shade south and east, whichever side of the path they edge."""
    im = Image.new('RGBA', (32, 32), CLEAR)
    px = im.load()
    tail = '' if role == 'center' else role.split('-')[-1]
    for y in range(32):
        for x in range(32):
            part = _path_part(role, x, y)
            above, left = _path_part(role, x, y - 1), _path_part(role, x - 1, y)
            if part == 0:
                c = moss_px(x, y)
                if 1 in (above, left):
                    c = G_MOSS[3]                                 # the stone's shade on the moss
            elif part == 1:
                a = min(y if 'n' in tail else 99, 31 - y if 's' in tail else 99)
                b = min(x if 'w' in tail else 99, 31 - x if 'e' in tail else 99)
                if (x if a <= b else y) in PATH_JOINTS:
                    c = G_ST_LO
                elif above != 1 or left != 1:
                    c = G_ST_HI if (above != 1 and left != 1) else G_ST_LT
                elif _path_part(role, x, y + 1) != 1 or _path_part(role, x + 1, y) != 1:
                    c = G_ST_MD
                else:
                    c = G_ST
            else:
                k = speck(x, y, 7)
                c = G_GRAVEL_HI if k < 5 else (G_GRAVEL_LO if k < 12 else (G_GRAVEL_SH if k < 14 else G_GRAVEL))
                if y % 6 == 2 and (x + y // 6 * 3) % 5 < 3 and _edge_dist(role, x, y) > 8:
                    c = G_GRAVEL_LO                               # the rake's lines
                if 1 in (above, left):
                    c = G_GRAVEL_SH                               # the stone's shade on the gravel
            px[x, y] = c
    return im
```
