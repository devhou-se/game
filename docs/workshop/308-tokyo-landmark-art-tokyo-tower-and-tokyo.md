# Design: Tokyo Tower and Tokyo Station in the house look (#308)

Part 1 of 8 of #293. Rooms whose look changes: **Palace** (both sprites) and **Park** (the feet copy). No
map, config or placement data changes.

## Context

`gamev2/tools/generate_tokyo_art.py` paints three sprites from the team's line drawings
(`art-source/line-art/`) through `tools/line_art.py`: `tokyo-tower_0_0` (512x960, Palace (8,6)),
`tokyo-tower-feet` (512x192, its bottom three rows, Park's copy) and `tokyo-station_0_0` (2624x512, Palace
(7,2)). They are in the old house palette and stand out from the GuttyKreum art round them:

- 10 of the tower's 17 colours and 10 of the station's 23 are in no GuttyKreum sheet (73% and 59% of their
  pixels).
- The station's roof is two flat slate tones; its brick is one flat tone a face.
- A pane is flat mid-blue `4b6396`; about one window in ten, the dome's oculus and marks on the tower's main
  deck are lit yellow `f6dc8c`.
- The tower's decks are white drums with no roof.

Wanted (the house look, `gamev2/docs/generators-and-checks.md` "House look: GuttyKreum"): only sheet
colours, a building shows its roof, windows are dark glass with a slanted glare and never lit, the outline is
the pack's navy ink. Same keys, sizes, anchors and alpha, so nothing on the map moves.

## Approach

Prototyped end to end at `origin/master` (`adc5c45c`); the figures below are measured from that prototype
and the code is in the appendix. Before and after pictures are on the ticket (`308-*.png`).

- **Still the drawing, painted by rule.** Nothing is redrawn: the alpha stays the drawing's, pixel for
  pixel (rule 7 and the existing tests). The look comes from two things only:
  1. **the materials** in `generate_tokyo_art.py` become ramps of sheet colours (it no longer imports the
     old palette constants), and
  2. **two keyword arguments on `line_art.paint`**, both defaulting to today's behaviour:
     - `glass=(GLAZED, LAMPLIT)`: the two materials a pane becomes, and what rule 6 treats as glass;
     - `texture=None`: `{material: f(x, y) -> colour}`, which replaces that material's base tone where the
       fill is not a `hi` / `lo` bevel. A line pixel that touches only glass takes the glass texture's
       colour where it differs from the base (so a glare runs across a window's glazing bars) and the
       glass's line tone elsewhere.
- **Tsutenkaku does not change.** It calls `paint` without the new arguments; its sprite came out
  byte-identical in the prototype. It is redrawn under #296.
- **Roof**: the station's three slate faces are the pack's kawara, laid by
  `generate_sendai_art.roof_tile(x, y, tones)` with its `ROOF_TILE` / `ROOF_LIT` / `ROOF_SHADE` (all sheet
  colours) as the three faces' textures. Importing `generate_sendai_art` has no side effects.
  Do **not** use `flat_roof` (fukuoka) or `P_ROOF_LO` (sendai): they use `2b373c`, which is in no sheet
  (#375, #378). The dark roof tone here is `293038`.
- **Tower decks show their roofs, seen from above**: the main deck's top (rows 205..241 outside the shaft),
  the lower ring's top and the upper box's top are zoned a slate-blue `DECK_ROOF`, with the shaft's and the
  mast's shade (`DECK_ROOF_SHADE`) to their right. No texture: the drawing's lines cross them already.
- **Glass**: one material, `T_GLASS` (`2c2d51` pane, `3c396d` bars), with `glare(step)` as its texture
  (`4b6396` where `(x + y) % step == 0`; step 9 on the station, 13 on the tower). `lit` is not passed, so
  nothing is lamplit; the dome's oculus becomes glass. The tower's two glazed bands are zoned glass directly
  (rows 242..268 and the top deck's 100..114) and `walls` is dropped from the tower's call: with it, small
  white regions on the drums turned into stray panes.
- **Brick**: `courses(m, joint)` as the texture of the three brick faces: every third row a bed joint, one
  tone down.
- **Ink**: `line_art` already draws the silhouette in `generate_hokkaido.INK`, which is the pack's `0a1627`;
  no change. Inside lines take each material's `line` tone, all sheet colours now.
- **Lamps**: the drawings have none, so `c6a663` is not used.
- **Names**: the tool's new materials are `T_*` (`T_BRICK`, `T_GLASS`, ...). The string `TEMPLE_` must not
  appear (`tools/tests/temple.test.js`).
- **Not used**: `foliage` (no trees), `repaint` / a colour swap after painting (it would give sheet colours
  but no tile, courses or glare), `glaze` / `pane` (they draw on a finished picture with Pillow; `texture`
  does the same inside the rules, keeping the drawing's lines). `tools/house_look.py` is not needed.

Result of the prototype: tower 23 colours, feet 13, station 35, none off the sheets; the commonest colour
covers 12.8% / 18.3% / 13.9%; lines against fills (mean luma) 72 vs 160 on the tower and 55 vs 96 on the
station (the existing test needs a gap of 30).

**Still flat, to say in the summary**: the tower's lattice panels and its legs (flat orange and white
between the drawing's members: the lattice is their texture, and the legs in Park are the plainest part);
the station's stone bands, granite foot and copper caps (small). Left as they are on purpose.

## Changes

Before starting: render the rooms as they are (`node tools/play.js render Palace before-palace.png`, same
for `Park`), outside the repository.

1. **`gamev2/tools/line_art.py`**: `paint` gains `glass` and `texture` (appendix A). Update the module
   docstring: rule 4 (a pane becomes `glass[0]`, or `glass[1]` where `lit`), rule 5 (a material in
   `texture` takes `texture[m](x, y)` in place of its base, bevels kept), rule 6 (glass is the `glass`
   pair; a line touching only glass carries its texture), and its last sentence (the default materials are
   the old house palette's; a caller may bring its own).
2. **`gamev2/tools/generate_tokyo_art.py`**: appendix B. Imports become `rgb` from `generate_hokkaido`,
   `roof_tile, ROOF_LIT, ROOF_SHADE` from `generate_sendai_art`, `template, paint, Plan` from `line_art`.
   New palette, `glare`, `courses`, `tower_zone`, `tower`, `FACES`, the end of `station`. `station_plan` is
   unchanged but for the oculus: `p.box('lit', 171, 57, 181, 68)` becomes `'glass'`. The sheet's ground
   becomes `rgb('a4b0b5')`. Rewrite the docstring: issue #308 added, "in the house palette" becomes the
   GuttyKreum look, the three sprite descriptions (decks roofed, kawara, dark glass, nothing lit), and the
   imports it names.
3. **`gamev2/assets/sprites/tokyo-tower_0_0.png`, `tokyo-tower-feet.png`, `tokyo-station_0_0.png`**:
   rewritten by `python3 tools/generate_tokyo_art.py`.
4. **`gamev2/assets/map/world-map.png`**: rebuilt with `python3 tools/make_worldmap.py --pil` (the map is
   drawn from the sprites; `check_generators.py` fails on a stale one). `world-map.json` should not change.
5. **`gamev2/tools/tests/landmark-placeholders.test.js`**: one new test (Tests).
6. **Docs**:
   - `gamev2/docs/landmarks-and-towns.md`: the Tokyo Tower and Tokyo Station rows of the landmark table
     ("painted in the GuttyKreum house look by ...", #308), and one sentence in "The three placeholders are
     line drawings with colour laid on" saying the Tokyo two bring pack materials, `glass` and `texture`,
     and Tsutenkaku is in the old palette until #296.
   - `gamev2/docs/generators-and-checks.md`, "House look: GuttyKreum": one line that a line-art sprite
     gets the pack's glass, tile and courses through `line_art.paint(glass=, texture=)`, with
     `generate_tokyo_art.py` as the worked example.

Not touched: `config.json`, `tiled/`, `devhouse.world`, `generate_tsutenkaku.py`, `check_generators.py`,
the line drawings.

## Data and interfaces

- `line_art.paint(tpl, zone, by_region=True, pane=0, walls=(), lit=None, bar=0, glass=(GLAZED, LAMPLIT),
  texture=None)`. `texture` is keyed by the material tuple, so two materials that need different textures
  must be different tuples (the three roof faces carry stand-in tones for that; their `hi` / `lo` / `line`
  are still painted at bevels and lines, and are sheet colours).
- Sprite keys, sizes (512x960, 512x192, 2624x512), `spriteMetadata` anchors and alpha: unchanged.
- No schema, API or configuration change.

## Tests

New, in `landmark-placeholders.test.js` (a unique name, e.g. `landmark placeholders: Tokyo Tower and Tokyo
Station are in the house look (#308)`), over `tokyo-tower_0_0`, `tokyo-tower-feet` and `tokyo-station_0_0`
(not Tsutenkaku). The sheet colours are every opaque colour of the PNGs under `art-source/GuttyKreum` whose
name does not start with `preview` (the `sheets()` helper of `house-look.test.js` /
`kanazawa-art.test.js`: copy it, cached). Coordinates are the saved sprite's pixels.

1. Every opaque colour is a sheet colour; `f6dc8c` (the old lamplight) is in none of the three.
2. Every 2x2 block from an even origin is one colour (pixel-doubled).
3. At least 99% of the opaque pixels that touch a clear pixel are `0a1627` (measured: 99.5% and up; the
   drawing has a few fill pixels on its edge).
4. No colour covers more than a quarter of a sprite's opaque pixels (measured: at most 18.3%).
5. Station roof, box (856,160)-(900,240): at least four colours, all of `0a1627 172459 2e4040 395050
   434857` (the kawara; it was two flat tones).
6. Station brick, box (860,290)-(900,300): has both `aa4d31` and its joint `904a37`.
7. Tower main deck's glazing, box (200,490)-(460,530): only `2c2d51 3c396d 4b6396 0a1627`, `2c2d51` the
   commonest, `4b6396` present.
8. Tower deck roof: `5b6c79` is in `tokyo-tower_0_0`.

Existing tests that must still pass unchanged: the rest of `landmark-placeholders.test.js` (sizes, anchors,
alpha equal to the drawing, lines darker than fills by 30, 12 colours or more, feet equal to the tower's
bottom 192 rows, the open cells), `map-data.test.js`, `temple.test.js`. That Tsutenkaku is untouched is
held by `check_generators.py` (`generate_tsutenkaku.py reproduces ...`).

Run, from `gamev2/`:

```bash
python3 tools/generate_tokyo_art.py --sheet /tmp/tokyo-sheet.png   # look at the sheet
python3 tools/generate_tsutenkaku.py && git status --short assets/sprites/tsutenkaku_0_0.png   # prints nothing
python3 tools/make_worldmap.py --pil
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py        # no DRIFT
python3 tools/sync_cities.py --check
node tools/play.js render Palace /tmp/after-palace.png ; node tools/play.js render Park /tmp/after-park.png
python3 -m http.server 8000 &            # then, with a Chromium for tools/browser (its README):
REGRESS_TIME_SCALE=2 PORT=8000 node tools/browser/regress.js
```

In the prototype: `test_game.js` 535 passed, `check_generators.py` exit 0 with no DRIFT (after the map
rebuild). The other three checks and the browser regression were not run at design time.

As a player (browser, desktop and a phone size, day and `?tod=night`): the station from Palace's forecourt,
the tower from the road under it, and Park's feet with `?stitch=0`. Check the roof tile does not shimmer at
the phone's zoom, the passing train still shows behind the roof, and the player still fades the tower.
Put before and after crops in `/work/media/` and name the sprites that still read flat in the summary.

## Risks and open questions

- **The branch is 26 commits behind `origin/master`**, which has since rebuilt `world-map.png` and rewritten
  both docs this change edits (the house look section exists only there). Merge `origin/master` into the
  branch before starting (`git merge origin/master`, locally) or the pull request conflicts on the map, a
  binary. The code itself needs nothing from master: every import exists at both.
- **`line_art.py` is shared with Tsutenkaku (#296)**. The new arguments are additive; #296 can use them.
  If #296 lands first, keep its changes and add these.
- **35 colours on the station** is over the recipe's 24 for a large sprite. It is 41x8 cells with five
  material families in three faces each; the tower is within it (23). Accepted; trimming means dropping the
  lit and shaded faces, which is what gives the building its form.
- **Glare and tile at small zoom**: the steps (9, 13) and the tile were judged on `play.js render` at full
  size only. If the glare reads as noise on a phone, widen the step; do not light the windows.
- **The glazed band of the tower** is dense with bars, so it reads as a violet block (`3c396d` nearly as
  common as the pane). Acceptable next to the pack's glass high-rises; darkening the bars to `2a2636` loses
  them.
- These are still placeholders for the team's art (#70): a PNG of the same size dropped over one needs no
  code or map change, and the new test's colour rules would then need loosening for that key.

## Appendix A: `line_art.paint` (the whole change)

```python
def paint(tpl, zone, by_region=True, pane=0, walls=(), lit=None, bar=0, glass=(GLAZED, LAMPLIT), texture=None):
    glazed, lamplit = glass
    texture = texture or {}
    ...
    # ---- 4
        of[i] = lamplit if lit and lit(x, y) else glazed
    ...
            if i >= 0:                                           # ---- 5: fill
                m = material(x, y)
                base, hi, lo, _ = m
                if i not in flat and (kind(x + 1, y) == -1 or kind(x, y + 1) == -1):
                    px[x, y] = lo
                elif i not in flat and (kind(x - 1, y) == -1 or kind(x, y - 1) == -1):
                    px[x, y] = hi
                else:
                    px[x, y] = texture[m](x, y) if m in texture else base
                continue
            # ---- 6: line (the INK test for a clear neighbour is unchanged)
            ...
                    m = material(nx, ny)
                    if m in glass:
                        frame = m                                # the material now, not its line tone
                    elif m not in round_it:
                        round_it.append(m)
            if frame:
                c = texture[frame](x, y) if frame in texture and not round_it else frame[0]
                px[x, y] = c if c != frame[0] else frame[3]
            else:
                px[x, y] = round_it[0][3] if len(round_it) == 1 else INK
```

## Appendix B: `generate_tokyo_art.py` (everything that changes but the docstring)

```python
from generate_hokkaido import rgb                                                        # noqa: E402
from generate_sendai_art import roof_tile, ROOF_LIT, ROOF_SHADE                          # noqa: E402
from line_art import template, paint, Plan                                               # noqa: E402

# ---- the pack's colours: a material is line_art's (base, hi, lo, line) ----------
T_INK = rgb('0a1627')
T_BRICK = (rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22'), rgb('5b283b'))
T_BRICK_LIT = (rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31'), rgb('8a3a22'))     # a face turned to the light
T_BRICK_SHADE = (rgb('8a3a22'), rgb('aa4d31'), rgb('5b283b'), rgb('2a2636'))   # and one turned from it
T_STONE = (rgb('e4cecc'), rgb('fafcfd'), rgb('be9e8c'), rgb('8e7366'))
T_STONE_SHADE = (rgb('be9e8c'), rgb('e4cecc'), rgb('8e7366'), rgb('7c5d56'))
T_COPPER = (rgb('6c8e7f'), rgb('93c297'), rgb('506b6b'), rgb('395050'))        # verdigris
T_COPPER_SHADE = (rgb('506b6b'), rgb('6c8e7f'), rgb('395050'), rgb('2e4040'))
T_GRANITE = (rgb('a4b0b5'), rgb('dae2e4'), rgb('848295'), rgb('575f79'))
T_HOLLOW = (rgb('191c2a'), rgb('191c2a'), rgb('191c2a'), T_INK)                # an unlit opening
T_CLOCK = (rgb('fafcfd'), rgb('fafcfd'), rgb('dae2e4'), rgb('2a2636'))         # a clock's face; its hands are the lines on it
T_GLASS = (rgb('2c2d51'), rgb('2c2d51'), rgb('2c2d51'), rgb('3c396d'))         # the pack's dark pane; glare() is its texture
T_GLARE = rgb('4b6396')
# the pack's kawara, as generate_sendai_art.roof_tile lays it: the tuple's base is a stand-in, the tile its texture
T_ROOF = (rgb('395050'), rgb('53596d'), rgb('2e4040'), T_INK)
T_ROOF_LIT = (rgb('434857'), rgb('646e86'), rgb('395050'), T_INK)
T_ROOF_SHADE = (rgb('293038'), rgb('2e4040'), rgb('21272d'), rgb('080d16'))


def glare(step):
    """The texture of T_GLASS: a glare slanting up across the dark pane every `step` pixels."""
    return lambda x, y: T_GLARE if (x + y) % step == 0 else T_GLASS[0]


def courses(m, joint):
    """The texture of a brick face: every third row is a bed joint, a tone down."""
    return lambda x, y: joint if y % 3 == 2 else m[0]


# ---- Tokyo Tower: the pack's orange, a step off the station's brick
VERMILION = (rgb('ce6a42'), rgb('f6a583'), rgb('aa4d31'), rgb('904a37'))
VERM_LIT = (rgb('f6a583'), rgb('ffe2e0'), rgb('ce6a42'), rgb('904a37'))        # the face turned to us
VERM_SHADE = (rgb('aa4d31'), rgb('ce6a42'), rgb('904a37'), rgb('5b283b'))
WHITE_STEEL = (rgb('dae2e4'), rgb('fafcfd'), rgb('bcc7cc'), rgb('848295'))     # the white bands
PAINT_LIT = (rgb('fafcfd'), rgb('fafcfd'), rgb('dae2e4'), rgb('a4b0b5'))       # and on that face
WHITE_SHADE = (rgb('bcc7cc'), rgb('dae2e4'), rgb('a4b0b5'), rgb('646e86'))
DECK = (rgb('d1e2eb'), rgb('fafcfd'), rgb('a4b0b5'), rgb('646e86'))            # the mast and the decks' walls
DECK_SHADE = (rgb('a4b0b5'), rgb('d1e2eb'), rgb('848295'), rgb('575f79'))
DECK_ROOF = (rgb('5b6c79'), rgb('698592'), rgb('444f5e'), rgb('293038'))       # a deck's roof, seen from above
DECK_ROOF_SHADE = (rgb('444f5e'), rgb('5b6c79'), rgb('293038'), rgb('21272d'))
CONCRETE = T_GRANITE
RED_BANDS = ((126, 156), (190, 234), (268, 312), (346, 378), (414, 469))   # rows; edges on the drawing's members
FOOTING = 470
PANEL = 114
# a drum's top face ends on its front arc: (the last full row, {row: half the face's width there}), about x 128
ARCS = ((70, {71: 14, 72: 11, 73: 7}), (118, {119: 17, 120: 14, 121: 11, 122: 8}))


def tower_zone(x, y, accent):
    """The material of a fill pixel of the tower; `accent` is the drawing's red panel."""
    lattice = 97 <= x <= 165 and y <= 234                        # the shaft, standing on the main deck's roof
    if y < 126:
        if 113 <= x <= 143 and 100 <= y <= 114:
            return T_GLASS                                       # the top deck's windows
        if 123 <= x <= 132 and y <= 61:
            return DECK                                          # the mast's foot
        top = 55 <= y <= 67 and 112 <= x <= 144 or 99 <= y <= 118 or any(
            full < y and abs(x - 128) <= arc.get(y, -1) for full, arc in ARCS)
        if top:
            return DECK_ROOF_SHADE if x > 132 and y < 99 else DECK_ROOF     # seen from above; the mast's shade
        return DECK_SHADE if x > 140 else DECK
    if 205 <= y <= 241 and not lattice:
        return DECK_ROOF_SHADE if x > 165 else DECK_ROOF         # the main deck's roof, the shaft's shade across it
    if 242 <= y <= 268:
        return T_GLASS                                           # and its two glazed storeys
    if y >= FOOTING:
        return CONCRETE
    red = any(a <= y <= b for a, b in RED_BANDS)
    if accent:
        return VERM_LIT if red else PAINT_LIT
    if x < PANEL:
        return VERMILION if red else WHITE_STEEL
    return VERM_SHADE if red else WHITE_SHADE


def tower():
    tpl = template('tokyo-tower_0_0')    # 256 x 480
    # by the pixel: the bands cut across the lattice's triangles. pane=12 keeps the small cells flat;
    # no `walls`: the glass is zoned, nothing becomes a pane by its size
    return paint(tpl, tower_zone, by_region=False, pane=12,
                 glass=(T_GLASS, T_GLASS), texture={T_GLASS: glare(13)})


# ---- Tokyo Station
FACES = {                                # a material as it faces us, the light (<) and away from it (>)
    'brick': (T_BRICK_LIT, T_BRICK, T_BRICK_SHADE),
    'stone': (T_STONE, T_STONE, T_STONE_SHADE),
    'slate': (T_ROOF_LIT, T_ROOF, T_ROOF_SHADE),
    'copper': (T_COPPER, T_COPPER, T_COPPER_SHADE),
    'granite': (T_GRANITE, T_GRANITE, T_GRANITE),
    'dark': (T_HOLLOW, T_HOLLOW, T_HOLLOW),
    'glass': (T_GLASS, T_GLASS, T_GLASS),
    'clock': (T_CLOCK, T_CLOCK, T_CLOCK),
}                                        # the 'lit' entry is gone: station_plan's oculus is 'glass'

# station(): name_at and zone as they are; the `lit` function is removed; then
    walls = {m for name in ('brick', 'stone') for m in FACES[name]}
    texture = {T_GLASS: glare(9),
               T_BRICK: courses(T_BRICK, rgb('904a37')),
               T_BRICK_LIT: courses(T_BRICK_LIT, rgb('ce6a42')),
               T_BRICK_SHADE: courses(T_BRICK_SHADE, rgb('83374f')),
               T_ROOF: roof_tile,
               T_ROOF_LIT: lambda x, y: roof_tile(x, y, ROOF_LIT),
               T_ROOF_SHADE: lambda x, y: roof_tile(x, y, ROOF_SHADE)}
    return paint(tpl, zone, pane=6, walls=walls, bar=2, glass=(T_GLASS, T_GLASS), texture=texture)
```

`tower_zone` is given whole: replace the function (the second red band and the shaft now end at row 234,
rows 235..241 being the deck's roof). Delete what this replaces: the old imports, `VERM`, `VERM_HI`,
`VERM_LO`, `VERM_DK`, `BRICK_LIT`, `SLATE_LIT`, `CLOCK`, the two `lit` functions and the `'lit'` face.
