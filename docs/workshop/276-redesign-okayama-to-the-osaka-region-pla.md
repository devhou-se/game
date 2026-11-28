# Okayama rebuilt to the Kansai plan: a stroll (#276)

## Context

Okayama is still the room Himeji used to be (`gamev2/docs/landmarks-and-towns.md`, "Kansai: one plan for
Osaka, Himeji and Okayama", list "What repeated"): a castle band, the avenue straight through, a garden
band; a gravel terrace as wide as the room above one wall with one stair; a garden that is a gravel loop
round a two-row pond, entered on columns 21-22. #276 is the second of three builds: **room `Okayama`
only**, rebuilt to its part of that plan ("Okayama (#276): a stroll"). Himeji (#275, built) and Osaka
(#277, next) are not touched; `tools/kansai.py`, `devhouse.world` and `cities.KansaiCity` do not change.

Outcome: the road runs ten cells in from Himeji and stops at a plaza on a river. The river bends through
the room; the black keep stands low on its north bank beside a small court; the Tsukimi bridge beside the
keep is the only way into Korakuen, which is the inside of the bend: open lawn, one cranked path, a
hill, a pond, the cranes, and the castle across the water. The seam, the fingerpost, the keep's art,
Momotaro, the stall, the cranes and all four `LANDMARKS` labels stay; Damian's 12 November post stays in
`Korakuen garden` beside the first crane, which is now (13,27).

## Approach

Rewrite the body of `tools/generate_okayama.py` to the cells below, draw one new sprite (the hill), and
regenerate. All of it was built as a blockout in a scratch copy and played in headless Chromium (pictures
on the pull request). There, with every edit under Changes:

- the five checks pass (523 unit tests; `rehearse_blog.py` 313/313), `play.js lint Okayama` and
  `lint KansaiCity` give 0 errors and 0 warnings, `devhouse.world` is unchanged;
- `config.json` changes only in `rooms.Okayama`, `districts.Okayama`, the new sprite's `spriteMetadata` /
  `tileNames` entries and one appended `tilePalette` slot (1073 -> 1074);
- `check_distinct.py` gives Kansai 0.11 / 0.35 / 48% (0.11 / 0.35 / 47% before; baseline 0.119 / 0.409 /
  27.3%), with no new `sendai-*` kind.

The plan's fixed cells are kept and its targets fit, with four shifts a blockout is allowed to make:

1. **The plaza is paved on (34..40, 14..22)**, not down to row 23. Row 23 stays the avenue's grass verge,
   which the fixed fingerpost (stamped (39,22), feet (39,23)) stands on, as at every other seam.
2. **The garden is x 3..28** (plan 3..27): column 28 is the lawn along the bend's west bank (water starts
   at 29). Leaving it wood would put trees on the bank.
3. **The bank rock is stamped at (28,21)**: it is 2x2 and centred where its four cells meet, so that
   puts it over the inner corner at the garden's tip (the plan names the tip cell, (28,22)).
4. **The stall's top row (37..39, 14) is made solid**: the plaza's top row would otherwise let the
   player stand behind its awning.

**The look-up, measured** (the plan asked): the keep is in `game.lookUp.sprites`; `lookUp.cells` 3,
`fade` 3. From the garden's bank, row 22 under the keep's columns (x 14..21), four cells south of its
foot:

| View | Weight | Offset | What shows |
|---|---|---|---|
| Desktop 1280x960 | 0.83 | 207px | the whole keep across the water; about 25px of its top row is behind the 40px bar |
| Phone, portrait 390x844 | 0.83 | 228px | the whole keep |
| Phone, landscape 844x390 | 0.83 | 101px (capped by `foot`) | the stone base and the foot of the first storey only |

Row 23 gives 0.5 (the top roof is cut off), the bridge 0.75, the court beside the keep 0 (no look-up
there: it is beside the keep, not in front). A landscape phone's view is 7.5 cells tall and the keep's top
is 10 rows north of the bank, so no cell shows all of it there; Himeji's keep has the same limit. The
camera is not changed by this ticket. Rows 22-23 west of the bridge carry no tree or prop.

### The river (all `pond-autotile` on layer `Water`, written by hand; all solid but the bridge's cells)

| What | Cells |
|---|---|
| East-west reach | (0..32, 19..21) |
| South reach | (29..32, 22..39) |
| Roles | row 19 `edge-n`; (32,19) `corner-ne`; column 32 below it `edge-e`; row 21 for x < 29 `edge-s`; column 29 from row 22 down `edge-w`; the rest `center` |
| Bank rock `okayama-bank-rock` 2x2, flat | stamped (28,21) |
| Tsukimi bridge `okayama-bridge` 2x4, flat | **(22,19)** (was (21,24)); open cells (22..23, 19..21); lands on row 22 |

No `corner-nw` on the river, so the garden pond's is the room's only one and "the pond" is the garden's
whatever column it is in. Not a `waterways` run. It leaves by the west and bottom edges only.

### East bank

| What | Cells |
|---|---|
| Pavement `flat-grey-brick-autotile` | avenue (34..43, 18..22) + plaza (34..40, 14..22); seam pieces on (43,18) `edge-n` and (43,22) `edge-s` as today |
| Road `k.road_h(38, 43, 19, cap_w=True)` | (38..43, 19..21): six cells, capped west |
| Momotaro 2x3 | **(35,16)** (was (8,17)); plinth (35..36, 18) |
| Bizen-ware stall 3x3 | **(37,14)** (was (15,15)); bumped from row 17; (37..39, 14) solid |
| Fingerpost | stamped (39,22), as today |
| Verge | row 23, x 33..41 grass with plants; `shrub-small` on (42,23), (43,23) as today; x = 33, rows 19-23 is grass bank |

### North bank

| What | Cells |
|---|---|
| Keep `okayama-keep` 8x7, solid over all of it | **(14,12)** (was (18,2)); foot row 18, the river on row 19 under it |
| Court `gravel-autotile` | (22..33, 14..18): open to the plaza at x = 34 on all five rows; no terrace, wall or steps |
| The court's pine | trunk (31,15) |

### Korakuen: the inside of the bend, (3..28, 22..37), lawn

| What | Cells |
|---|---|
| Path `gravel-autotile`, two cells wide, one region with the court and the bridge deck | (22..23, 22..25) + (10..23, 24..25) + (10..11, 24..31) |
| Mound `okayama-mound` 5x4 (new), solid over all of it | (4,25) |
| Pond 8x4, solid | (6..13, 32..35), corners and edges by position |
| Cranes (feet) | (14,27), (16,28) |
| Maples (trunks) | (26,29), (19,33), (5,31) |
| Cedars (trunks) | (26,36), (23,36) |
| The pond's pine (trunk) | (15,35) |
| One stone lantern (feet) | (12,31), where the path meets the pond |

### Edges

Solid `k.woods` of maple and cedar (`AUTUMN = ['sendai-maple', 'sendai-cedar', 'sendai-maple']`: no pine
in the border) on (0..43, 0..11), (0..13, 12..18), (22..43, 12..13), (41..43, 14..17), (33..43, 24..39),
(0..2, 22..39), (3..28, 38..39). Open edge cells: the five seam cells on x = 43 only.

## Changes

All paths under `gamev2/`. The prototyped generator body and the hill's drawing are in the Appendix: use
them as they are.

- **`tools/generate_okayama.py`**: replace everything between `rng = random.Random(267)` and the
  `# ---- write` block with the Appendix body. The write block is unchanged (NPCs kept, seams through
  `rg.kept_order`). Rewrite the docstring to the layout above (no axis, terrace, stone wall, island or
  ring; "the river is one bend ... one inner corner"), and the final `print` to name the keep and bridge.
- **`tools/generate_kansai_art.py`**: `import math`; add `mound()` (Appendix) before `crane()`; add
  `'okayama-mound_0_0': (mound, 2, 'okayama-mound'),` to `SPRITES` before the `okayama-fingerpost_0_0`
  row; in the header list add `okayama-mound_0_0  5x4  Yuishinzan, Korakuen's hill: a bell of turf,
  clipped azaleas and rocks, stone steps up the south face to a stone on top`, and reword
  `okayama-bank-rock`'s "each corner of Korakuen's island" to "the inner corner of a river's bend".
  It is not in `FLAT` or `LOOK_UP`. Result: 320x256px, 10 colours, all from the GuttyKreum sheets.
- **`tools/make_prefabs.py`**: before the `okayama-fingerpost` entry

  ```python
  # Yuishinzan, the garden's hill (issue #276): solid over all of it
  'okayama-mound':          dict(w=5, h=4, sprites=[('Collidables', 0, 0, 'okayama-mound_0_0')],
                                 colliders=[(x, y) for x in range(5) for y in range(4)], doors=[]),
  ```

  and reword the comment above `okayama-bridge` ("the rocks at the corners of Korakuen's island").
- **`tools/blog_to_npc.py` `LANDMARKS`**: `okayama-keep_` offset `(2, 7)` -> **`(10, 4)`**, comment
  "(24, 16): the court beside the keep, off the bridge's columns". The other three rows keep their
  offsets; only their comments' cells change: crane (13,27), Momotaro (35,19) "the plaza in front of
  him", stall (38,17) "the plaza at its counter".
- **`tools/districts.py`**, Okayama (keys, names and order unchanged):

  | Key | Description | Bounds | Stand |
  |---|---|---|---|
  | `castle` | the black "crow" castle at the water: the keep on the north bank of the river and the gravel court beside it | (22, 14, 33, 18) | (27, 16) |
  | `momotaro` | the avenue in from Himeji and the plaza it ends in on the east bank: the Momotaro statue and a stall of Bizen ware | (34, 14, 43, 23) | (36, 20) |
  | `korakuen` | the strolling garden inside the bend of the river, over the Tsukimi bridge: open lawn, a hill, a pond, red-crowned cranes, the castle across the water | (3, 22, 28, 37) | (18, 30) |

  Spots come out as today: `Okayama Castle`; `the Bizen-ware stall`, `the Momotaro statue`; `Korakuen
  garden`, `the pond`.
- **`src/utils/Interactions.js`**: after the `crane` row,
  `{ kind: 'mound', group: 'flavour', pattern: /^okayama-mound/, footprint: true, say: 'yuishinzan: six metres of hill, heaped up so a lord could look down on his own garden' },`
- **Regenerate, in this order** (art tools with a Pillow python), and commit what they write:
  `generate_kansai_art.py`, `make_prefabs.py`, `generate_okayama.py`, `districts.py`,
  `blog_to_npc.py --rehome Damian 2025-11-12 "Okayama · Korakuen garden"` (prints
  `Okayama (27,31) -> Okayama · Korakuen garden (13, 27)`), `config_to_tiled.py Okayama`,
  `make_worldmap.py --pil`. New files: `assets/sprites/okayama-mound_0_0.png`,
  `tiled/prefabs/okayama-mound.tmj`. Changed: `config.json`, `tiled/okayama.tmj`,
  `assets/map/world-map.png`. `check_distinct.py` is run without `--update`.
- **`tools/test_blog_to_npc.py`**: the pin `('Damian', '2025-11-12')` -> `('Okayama', (13, 27))`.
- **`tools/tests/kansai.test.js`**: see Tests.
- **Docs**
  - `docs/landmarks-and-towns.md`: rewrite the **Okayama** bullet to what is built (the tables above,
    the four shifts, the look-up measurements and the landscape-phone limit, "rows 22-23 west of the
    bridge stay clear", the mound and its bump). In the landmark table, Korakuen's row becomes "the
    Tsukimi bridge, the red-crowned cranes, Yuishinzan (the hill), the stones at the bend's inner
    corner" with `okayama-mound_0_0` added. In "Districts and the blog pipeline": the visitor cells are
    (24,16) on the court beside the keep, (13,27), (35,19), (38,17); replace the "keep the garden pond's
    first column between 10 and 43" rule with "the river has no `corner-nw`: keep it so". In the plan
    section: delete the "Okayama (#276): a stroll" bullet; reword the lead of "What repeated" (neither
    room is that room now; the list is history); the Posts table's Okayama row becomes "(13,27),
    unchanged (fixed)"; "Build order" item 2 becomes "**Built**: see the Okayama bullet". Keep the
    "Fixed for all three tickets" bullet and the seam tables: #277 needs them.
  - `docs/blog-pipeline.md` (about line 145): "on the island's lawn" -> "on the garden's lawn".

One commit: `gamev2: Okayama is rebuilt to the Kansai plan - the road stops at a plaza on a river that bends through the room, the keep at the water beside a court, Korakuen inside the bend with a hill (#276)`.

## Data and interfaces

- `config.json`: `rooms.Okayama` layers (size 44x40, transporters and their order unchanged; Damian's
  2025-11-12 state moves to (13,27)); `districts.Okayama` bounds, stands, descriptions; `spriteMetadata`
  and `tileNames` gain `okayama-mound_0_0`; `tilePalette` gains it at the end (append only).
- New prefab `okayama-mound` (5x4, layer `Collidables`, twenty colliders). New bump kind `mound`.
- `LANDMARKS`: one offset changes; no label, room scope or key changes. No change to `kansai.py`,
  `cities`, `places`, `game.lookUp`, `stations`, `waterways`, `devhouse.world` or any other room.

## Tests

`tools/tests/kansai.test.js`: the four Okayama tests are rewritten to the new cells, and the walk test's
stops become `['Okayama', 24, 16]` (the court) and `['Okayama', 18, 30]` (the lawn). They assert:

1. **Keep** (title: "...stands at the water on the north bank, its court beside it and no wall across
   the room; nobody walks behind it, and it is looked up at from the garden across the river (#267,
   #276)"): keep at (14,12), PNG 512x448, footprint unwalkable, `pond-autotile` on (14..21, 19); nothing
   walkable on rows 0..11 or on (0..13, 12..18); (22..33, 14..18) all `gravel-autotile`, and (22,y),
   (33,y), (34,y) walkable for y 14..18; no sprite key matching
   `^(castle-wall|stairs|sendai-earthen-wall|himeji-)`. For x 14..21: (x,22) and (x,23) walkable;
   `LandmarkView.aim` from (x,22) has `weight > 0.8 && offset > 0` for
   `{viewH:960, bar:40, deadzone:256, foot:128}` and `{viewH:480, bar:46, deadzone:128, foot:188}`; on
   desktop `top = 22*64+32 - offset - 480` satisfies `top <= 12*64 && top + 40 < 13*64`; nothing on
   `Collidables`, `Tops` or `Other` at (x, 22..23). `aim(24,16)` on desktop has weight 0. The four
   `LANDMARKS` row strings (offsets (10,4), (-1,1), (0,3), (1,3)), each visitor cell walkable, and the
   cells exactly `Okayama Castle` (24,16), `Korakuen garden` (13,27), `the Momotaro statue` (35,19),
   `the Bizen-ware stall` (38,17).
2. **Korakuen** (title: "...is the inside of a bend of the river, reached by the Tsukimi bridge alone,
   with a pond that is the garden's and not the river (#267, #276)"): `Water` cells outside the pond
   number 33*3 + 4*18 = 171 and all lie in the two reaches; the non-solid ones are exactly
   `22,19 22,20 22,21 23,19 23,20 23,21`; bridge at (22,19), one of it; roles at (0,19) `edge-n`, (32,19)
   `corner-ne`, (32,30) `edge-e`, (10,21) `edge-s`, (29,30) `edge-w`, (30,21) and (29,21) `center`; bank
   rock exactly `[[28,21]]`; walkable (22,22), (23,25), (10,24), (11,31), (3,22), (28,22), (3,37),
   (28,37), (18,30); gravel at (22,22), (22,25), (10,25), (10,31); no walkable cell with x < 29 and
   y >= 22 outside (3..28, 22..37); at most 60 gravel cells inside the garden; the pond's 32 cells all
   `pond-autotile` and solid; `pond-autotile_corner-nw` only at `[[6,32]]`; mound at (4,25), 5x4, all
   solid; cranes' feet `[[14,27],[16,28]]`, each solid with an open cell above; exactly two
   `sendai-pine_0_0`; at most one `sendai-stone-lantern_0_0`; district keys and spots as today, bounds
   `[[22,14,33,18],[34,14,43,23],[3,22,28,37]]`; no `waterways`; `Interactions.find` at (10,21) is kind
   `pond` (the river is fished).
3. **Damian**: cell (13,27); the first crane sprite cell in string order is `14,26`; he is inside
   (3..28, 22..37). The rest of the test is unchanged.
4. **Bumps** (title adds "the hill" and "the road ends in a plaza on the east bank", #276): (34..43,
   18..22) and (34..40, 14..22) are pavement or road; road tiles are 18 cells, least x 38, rows 19..21,
   and (38,20) is `road-edge-left_0_0`; no pavement or road on rows 18..22 for x < 33; Momotaro
   `[35,16,2,3]`; stall `[37,14,3,3]` with rows 14 and 16 solid and row 17 open; the mound says
   `['mound', 'yuishinzan: ...']` at (4,28), (8,28), (6,25), (8,26); the sprite list gains
   `okayama-mound`.

Also reword the message on the `waterways` count ("none in Okayama: no arm of its river leads anywhere")
to "its river is not sailed". No other test file changes but the pin in `test_blog_to_npc.py`.

Run from `gamev2/` (Pillow python): `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
`node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`;
then `python3 tools/rehearse_blog.py`, `node tools/play.js lint Okayama`, `node tools/play.js lint
KansaiCity`, `python3 tools/check_distinct.py`, and look at `node tools/play.js render Okayama out.png`.
`git diff --stat` must show no change to `devhouse.world`, `tools/kansai.py` or another room's `.tmj`.

Browser regression: `tools/browser/regress.js` has no Okayama case and none is added; run it for what it
covers, and say so if it cannot be run.

By playing, with real keys and touches, at 1280x960 and at phone size (`&touch=1`, 844x390 and 390x844),
`?notitle=1&nointro=1&date=2025-11-12&tod=day`, once more with `?stitch=0`. Start on Okayama's avenue
(debug map travel lands on (40,18)), then on foot:

- west along the road: it stops; the plaza, the statue and the stall each answer a bump; nobody gets
  behind the stall; the river is ahead and cannot be walked into;
- along the court to the keep: no way behind or west of it;
- over the bridge and onto the bank at rows 22-23 under the keep: the camera lifts and the views match
  the table above; look at a screenshot of each size;
- along the path to the pond: Damian stands beside the first crane and talks; the cranes and the hill
  answer a bump; the hill cannot be walked onto or behind; the pond and river can be fished;
- the lawn's corners (3,22), (28,22), (3,37), (28,37): no way out but the bridge;
- back east into Himeji and on: the seam is unchanged; with `?stitch=0` the five seam cells still carry
  you to Himeji.

## Risks and open questions

- **Landscape phones see only the keep's base from the garden.** Measured, not fixable by moving cells
  in a 7.5-cell-tall view, and the same as Himeji. The keep is seen whole there only in passing, east
  columns first, from the court. Changing `lookUp` or the phone camera is not this ticket; the doc
  bullet records the limit.
- **The hill is a first drawing.** It reads as a turfed hill with steps at game size in the blockout; if
  it does not in play, redraw inside `mound()` only (same key, size and footprint).
- **Map data is serial.** This rebuilds `rooms.Okayama`, `tiled/okayama.tmj`, the world map and one
  palette slot. Name `Okayama` in the summary. Rebase conflicts in `config.json` are resolved by
  re-running the regenerate list, not by hand.
- **Blog placements.** Only Damian's 12 November post is in the room; `rehearse_blog.py` and the pin
  hold it. The keep's label now stands a visitor beside the keep, not in front, with no look-up: a
  later castle post gets the court, and the view is from the garden.
- **#277 (Osaka)** needs nothing from this room; the seam cells and the fixed list in the plan stay.
- No open question for the owner.

## Appendix: prototyped code

### `tools/generate_okayama.py`, between `rng = random.Random(267)` and `# ---- write`

```python
AVE0, AVE1 = ks.OK_AVENUE[0], ks.OK_AVENUE[-1]    # the avenue in from Himeji: rows 18-22
PLAZA = (34, 14, 40, AVE1)                        # where the avenue ends, on the east bank
REACH = (0, 19, 32, 21)                           # the river: in at the west edge, east to the bend...
BEND = (29, 22, 32, H - 1)                        # ...and south out of the bottom edge
KEEP = (14, 12)                                   # 8x7: its stone base stands on the north bank, row 18
COURT = (22, 14, 33, 18)                          # the gravel court beside it
BRIDGE = (22, REACH[1])                           # 2x4: the Tsukimi bridge, beside the keep, landing on row 22
GARDEN = (3, 22, 28, 37)                          # Korakuen: the inside of the bend
MOUND = (4, 25)                                   # 5x4: Yuishinzan
POND = (6, 32, 13, 35)                            # the garden's pond
PATH = rect(22, 22, 23, 25) + rect(10, 24, 23, 25) + rect(10, 24, 11, 31)    # from the landing: south, west, south to the pond
AUTUMN = ['sendai-maple', 'sendai-cedar', 'sendai-maple']

b.fill('grass-autotile')

# ---- the avenue, in from Himeji, and the plaza it ends in -----------------------------
b.autotile('flat-grey-brick-autotile', rect(PLAZA[0], AVE0, W - 1, AVE1) + rect(*PLAZA))
b.put('Floor', W - 1, AVE0, 'flat-grey-brick-autotile_edge-n')    # the pavement runs on into Himeji:
b.put('Floor', W - 1, AVE1, 'flat-grey-brick-autotile_edge-s')    # no rounded corner at the seam
k.road_h(38, W - 1, AVE0 + 1, cap_w=True)                         # six cells of it, and the road stops
b.stamp('okayama-momotaro', 35, 16)                               # feet on (35..36, 18)
b.stamp('okayama-bizen-stall', 37, 14)                            # bumped from the plaza, row 17
k.solid_rect(37, 14, 39, 14)                                      # its awning's row: nobody walks in behind it

# ---- the river: one bend of water, solid but for the bridge's two columns ---------------
rx0, ry0, rx1, ry1 = REACH
bx0, by0, bx1, by1 = BEND


def bank(x, y):
    """The pond piece of a cell of the river: rimmed on the side its bank is."""
    if (x, y) == (rx1, ry0):
        return 'corner-ne'
    if y == ry0:
        return 'edge-n'
    if x == rx1:
        return 'edge-e'
    if y == ry1 and x < bx0:
        return 'edge-s'
    if x == bx0 and y >= by0:
        return 'edge-w'
    return 'center'


for x, y in rect(*REACH) + rect(*BEND):
    b.put('Water', x, y, f'pond-autotile_{bank(x, y)}')
    if x not in (BRIDGE[0], BRIDGE[0] + 1) or y > ry1:
        b.solid(x, y)                                             # the bridge is the only way over
b.stamp('okayama-bank-rock', bx0 - 1, ry1)                        # 2x2, over the inner corner at the garden's tip

# ---- the north bank: the keep at the water, the court beside it ---------------------------
# One gravel region: the court, under the bridge, and the garden's path from its landing.
b.autotile('gravel-autotile', rect(*COURT) + rect(BRIDGE[0], ry0, BRIDGE[0] + 1, ry1) + PATH)
b.stamp('okayama-keep', *KEEP)
k.solid_rect(KEEP[0], KEEP[1], KEEP[0] + 7, KEEP[1] + 6)          # its roof rows too: nobody walks in behind it
b.stamp('okayama-bridge', *BRIDGE)
k.trees('sendai-pine', [(31, 15)])                                # the court's one pine

# ---- Korakuen: lawn, the path, the mound, the pond, the cranes ----------------------------
b.stamp('okayama-mound', *MOUND)
px0, py0, px1, py1 = POND
for x, y in rect(*POND):
    ns = 'n' if y == py0 else 's' if y == py1 else ''
    we = 'w' if x == px0 else 'e' if x == px1 else ''
    b.put('Water', x, y, 'pond-autotile_' + ('corner-' + ns + we if ns and we else 'edge-' + (ns or we) if ns or we else 'center'))
    b.solid(x, y)
for x, y in ((14, 27), (16, 28)):                                 # feet: the cranes on the lawn
    b.stamp('okayama-crane', x, y - 1)
# None of these on rows 22-23 west of the bridge: that bank is where the keep is looked at from.
k.trees('sendai-maple', [(26, 29), (19, 33), (5, 31)])
k.trees('sendai-cedar', [(26, 36), (23, 36)])
k.trees('sendai-pine', [(15, 35)])                                # the pond's pine
b.stamp('sendai-stone-lantern', 12, 30)                           # feet on (12, 31): where the path meets the pond

# ---- the fingerpost by the seam ------------------------------------------------------------
b.stamp('okayama-fingerpost', 39, AVE1)                           # feet on (39, 23), on the verge

# ---- closed all round, but for the avenue into Himeji ----------------------------------------
for x in (W - 2, W - 1):
    b.stamp('shrub-small', x, AVE1 + 1)                           # the verge south of the avenue, at the seam
k.woods(0, 0, W - 1, KEEP[1] - 1, AUTUMN, rng)                    # the north, behind the keep
k.woods(0, KEEP[1], KEEP[0] - 1, ry0 - 1, AUTUMN, rng)            # west of the keep, down to the river
k.woods(COURT[0], KEEP[1], W - 1, COURT[1] - 1, AUTUMN, rng)      # north of the court and the plaza
k.woods(PLAZA[2] + 1, PLAZA[1], W - 1, AVE0 - 1, AUTUMN, rng)     # east of the plaza, north of the avenue
k.woods(bx1 + 1, AVE1 + 2, W - 1, H - 1, AUTUMN, rng)             # the east bank, south of the avenue
k.woods(0, ry1 + 1, GARDEN[0] - 1, H - 1, AUTUMN, rng)            # the west edge: nothing is planned beyond it
k.woods(GARDEN[0], GARDEN[3] + 1, GARDEN[2], H - 1, AUTUMN, rng)  # south of the garden
k.plants(rng, 22, 12, 26, 28, 37)                                 # the garden's lawn
k.plants(rng, 5, bx1 + 1, AVE1 + 1, 41, AVE1 + 1)                 # the verge
```

The order of the calls matters: `rng` is shared, and the committed room is whatever this order draws.

### `tools/generate_kansai_art.py`: `mound()`

```python
def mound():
    """Yuishinzan, the hill heaped up in Korakuen: a bell of turf lit from the upper left,
    clipped azaleas and rocks on its slope, and stone steps up the south face to the stone on top."""
    im, d = canvas(5, 4)                 # 160 x 128
    TURF, TURF_HI, TURF_LO, TURF_DK = rgb('83af6f'), rgb('93c297'), rgb('6c8e7f'), rgb('506b6b')
    top, base, cx, half = 20, 122, 80, 77
    span = {}
    for y in range(top, base + 1):
        t = (base - y) / (base - top)                             # 0 at the foot, 1 at the top
        w = half * (0.55 * math.acos(2 * t - 1) / math.pi + 0.45 * (1 - t ** 2) ** 0.5)
        span[y] = (cx - round(w), cx + round(w))
    for y, (x0, x1) in span.items():
        wide = x1 - x0
        for x in range(x0, x1 + 1):
            f = (x - x0) / max(1, wide)
            c = TURF
            if f > 0.72 + ((x + y) % 2) * 0.03:
                c = TURF_LO                                       # the flank turned from the light
            if f > 0.93 or y >= base - 2:
                c = TURF_DK
            elif y >= base - 5 and (x + y) % 2:
                c = TURF_DK if f > 0.72 else TURF_LO              # the foot, dithered into its shade
            d.point((x, y), fill=c)
        for x in range(x0, x0 + 2 + (y < top + 12) * 4):
            d.point((x, y), fill=TURF_HI)                         # the lit rim
    for i in range(110):                                          # tufts: short dashes, staggered
        y = top + 6 + (i * 37) % (base - top - 12)
        x0, x1 = span[y]
        x = x0 + 5 + (i * 53) % max(1, x1 - x0 - 12)
        f = (x - x0) / (x1 - x0)
        d.rectangle([x, y, x + 2, y], fill=TURF_DK if f > 0.72 else TURF_HI if i % 3 == 0 else TURF_LO)

    def azalea(x, y, w, h):
        """A clipped azalea: a low dome, lit on top, dark under, its shadow on the turf."""
        for j in range(h):
            inset = (3, 1, 0)[j] if j < 3 else (1 if j == h - 1 else 0)
            d.rectangle([x + inset, y + j, x + w - 1 - inset, y + j],
                        fill=rgb('395050') if j >= h - 2 else rgb('506b6b') if j >= h - 5 or j == 0 else rgb('6c8e7f'))
        d.rectangle([x + w - 3, y + 2, x + w - 1, y + h - 3], fill=rgb('395050'))
        d.rectangle([x + 4, y + 1, x + w // 2 + 1, y + 1], fill=rgb('93c297'))
        d.rectangle([x + 2, y + 2, x + 4, y + 2], fill=rgb('93c297'))
        d.rectangle([x + 1, y + h, x + w, y + h], fill=rgb('506b6b'))

    def rock(x, y, w, h):
        d.rectangle([x + 1, y, x + w - 2, y], fill=rgb('dae2e4'))
        d.rectangle([x, y + 1, x + w - 1, y + h - 1], fill=rgb('a4b0b5'))
        d.rectangle([x, y + 1, x + w * 2 // 3, y + 2], fill=rgb('dae2e4'))
        d.rectangle([x + w - 3, y + 2, x + w - 1, y + h - 1], fill=rgb('848295'))
        d.rectangle([x, y + h - 2, x + w - 1, y + h - 1], fill=rgb('575f79'))
        d.rectangle([x, y + h, x + w, y + h], fill=rgb('506b6b'))

    for x, y, w, h in ((14, 104, 16, 9), (34, 108, 20, 10), (30, 84, 15, 8), (48, 66, 14, 8), (58, 92, 13, 7),
                       (60, 44, 12, 7), (100, 58, 14, 8), (104, 84, 16, 9), (122, 104, 18, 9), (100, 108, 15, 8),
                       (134, 110, 12, 7)):
        azalea(x, y, w, h)
    for x, y, w, h in ((22, 96, 8, 6), (118, 94, 9, 6), (92, 40, 7, 5)):
        rock(x, y, w, h)
    # the steps: slabs up the south face, turning once
    for i, (x, y) in enumerate(((75, 113), (76, 105), (78, 97), (81, 89), (84, 81), (86, 73), (85, 65), (82, 57),
                                (79, 49), (77, 41), (76, 34))):
        w = 10 - i // 3
        d.rectangle([x, y, x + w, y + 2], fill=rgb('dae2e4'))
        d.rectangle([x, y + 3, x + w, y + 3], fill=rgb('a4b0b5'))
        d.rectangle([x + w, y + 1, x + w, y + 3], fill=rgb('848295'))
        d.rectangle([x, y + 4, x + w, y + 4], fill=rgb('506b6b'))
    rock(72, 21, 16, 10)                                          # the stone on top
    outline(im)
    return im
```
