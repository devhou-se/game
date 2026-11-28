# Nara: an eastern district of Kansai with the Great Buddha Hall and deer (#268; #68, run 5)

## Context

Damian's post of 14 Nov 2025 (764: the day trip to Nara, the Great Buddha, the deer) stands on Osaka's
canal bank (`Osaka` 39,19) because Nara does not exist. #68's plan (`docs/workshop/68-…md`, "Plan for the
later tickets", the "Nara" paragraph) makes Nara the east district of the stitched `KansaiCity`: 52x40 at
city cell (138, 36), east of Osaka, reached on foot along the avenue. `tools/kansai.py` already holds its
`AT` / `SIZE`; Osaka's east edge is closed until it is built.

Outcome: `KansaiCity` is Okayama + Himeji + Osaka + Nara, one walkable room 190x46. Osaka's canal runs on
east as a river that bends north with a towpath beside it; the avenue ends in a plaza below the Nandaimon
gate, with the Great Buddha Hall behind it; deer rest on the lawn, the court and the plaza; Kasuga Taisha
is a shrine you go into, up an approach lined with stone lanterns. Damian's post stands in front of the
hall. Nara is a small place on the Map. The river and the towpath stop two rows short of the top edge
until Lake Biwa (#269) exists. Owner's rules: walked to, no station; only real places; no ordinary sealed
buildings; no bins.

Everything below was built as a blockout on a copy of this branch (placeholder art, the cells in this
file) and measured. On it: `play.js lint` is clean for Nara, Osaka, KansaiCity and ShrineNara1; `play.js
check`, `test_blog_to_npc.py`, `check_generators.py`, `sync_cities.py --check`, `check_distinct.py` and
`rehearse_blog.py` (313/313) pass; the unit tests that fail are exactly the ones listed under Tests. It was
looked at in a browser (desktop, portrait and landscape phone: the hall, the towpath's end, the plaza,
Kasuga Taisha, the seam, the Map), not played with keys, and the browser regression was not run. The
renders and screenshots are in the ticket's media (`268-*.png`); every landmark in them is a placeholder
box.

The design was then reviewed against a second blockout built from this file alone (Review, at the end).
Three things changed in the body because of it: the Map rule is narrower and lives in `Places.order`, a
nineteenth lantern closes a pocket behind the shrine, and what is said about Osaka's seam order, the
railway strip, 14 Nov on the Map, occlusion and night lights is now what the code does.

## Approach

Build Nara the way #255 and #267 built Himeji and Okayama: one generator on `roomgen.Builder` + `ks.Kit`,
art drawn by `generate_kansai_art.py`, the seams declared once in `kansai.py`, Osaka's generator opening
its east edge through `ks.is_open('Osaka', 'e')`. Todaiji stands on one north-south axis (columns 36-37):
hall, gravel court, gate, plaza. Kasuga Taisha is the existing `shrine-red` prefab, so
`generate_shrines.py` wires its interior with one `NAMES` row and no new code.

Choices that were close, or that differ from the plan:

- **The torii is own art (`nara-kasuga-torii`), not the kit's `torii-red`.** With `torii-red` and
  `shrine-red` together `check_distinct.py` reports Kansai WORSE than its baseline (building overlap with
  Fukuoka 0.14, was 0.12), and the baseline may not be updated to hide that. With its own torii and the
  kit hall it measures 0.11 / 0.35 / 45% own: not worse.
- **The closed head of the river is not a pond corner.** A `pond-autotile_corner-nw` tile makes the
  pipeline's generic "the pond" spot, which resolved three cells away and failed `test_spots`. The head is
  `edge-n` + `corner-ne`, with an `okayama-bank-rock` over its west corner (and one over the inside of the
  bend, where the set has no inner corner). #269 removes the head when it opens the edge.
- **A narrow rule in `Places.layout`** (below): without one Nara's dot, 13 px from Osaka's on a landscape
  phone, makes Osaka the most crowded dot, and the knock-on puts Karuizawa's lit label on a leader on
  2 Nov 2025 (the #263 test fails). The rule is only that a small place whose dot *touches* a town's does
  not change when that town chooses its label's spot. The first draft of this design dropped every small
  place from every town's count; that fixes the same test and reorders a quarter of the Maps the game
  already draws (Review 1), so it is not what is built. Moving Nara's `geo` was the other alternative: it
  is no longer Todaiji's, and the plan keeps it for a dot that cannot be seen, which is not the case
  (media: the Map at three sizes; both dots read, lit or not).
- **`nara-fingerpost` is its own key**, as `okayama-fingerpost` is: `Interactions` picks a line by sprite
  key, and this seam's line differs.

## Changes

All paths under `gamev2/` unless they start with `../`. Cells are Nara's own unless a room is named.

### `tools/kansai.py`

```python
BUILT = ('Himeji', 'Nara', 'Okayama', 'Osaka')
N_AVENUE = tuple(y + AT['Osaka'][1] - AT['Nara'][1] for y in O_AVENUE)            # Nara: 18-22, at x = 0
N_RIVER = tuple(y + AT['Osaka'][1] - AT['Nara'][1] for y in O_CANAL)              # Nara: 14-16, the river in from Osaka
N_BEND = (20, 22)                        # Nara: the columns the river turns north up
N_TOWPATH = (23, 24)                     # Nara: the towpath's columns, at y = 0
L_TOWPATH = tuple(x + AT['Nara'][0] - AT['LakeBiwa'][0] for x in N_TOWPATH)       # Lake Biwa: 9-10, at y = 35
JOINS += ('Osaka', 'e', O_AVENUE, 'Nara', N_AVENUE), ('Nara', 'n', N_TOWPATH, 'LakeBiwa', L_TOWPATH)
```

(`JOINS` is a list literal: add the two rows to it.) The second row is inert until `LakeBiwa` is in
`BUILT`; it is what #269 opens. Docstring: Nara is built; its north edge opens with Lake Biwa.

### Art: `tools/extract_street.py`, `tools/generate_kansai_art.py`, `tools/make_prefabs.py`

`extract_street.py` `PROPS` (the two resting deer of UrbanAccessoriesv2, as the ticket asks):

```python
'nara-deer-doe':  ('urban', (0, 128, 32, 160), 1, 1),
'nara-deer-stag': ('urban', (32, 128, 64, 160), 1, 1),
```

`generate_kansai_art.py` `SPRITES` (half-size canvas, doubled, like the others); prefab rows beside
Okayama's, each one sprite on `Collidables` at (0,0), `doors=[]`:

| key (`_0_0`) | cells | colliders | what is drawn |
|---|---|---|---|
| `nara-daibutsuden` | 12x8 (768x512) | rows 2-7 (the generator closes the rest) | the Great Buddha Hall: two hipped grey-tile roofs, the two gold horn finials on the ridge, white walls between dark posts, the curved gable over the middle doors, a low stone platform. Fills its footprint, nothing above it |
| `nara-nandaimon` | 6x4 | columns 0, 1, 4, 5, all rows | the Great South Gate: a two-tier roof on bare dark timber; columns 2-3 are the gateway, transparent below the roof (walked through as `himeji-kokoen-gate` is) |
| `nara-kasuga-torii` | 4x4 | columns 0 and 3, all rows | a vermilion torii: posts on columns 0 and 3, the lintels across the top row, nothing else in columns 1-2. Not `torii-red` redrawn: a black cap on the lintel and black post feet, Kasuga's own |
| `nara-deer-doe`, `nara-deer-stag` | 1x1 | (0,0) | extracted, above |
| `nara-deer-bow` | 1x1 | (0,0) | a standing deer, head down in a bow, in the sheet deer's colours (`aa775f` `7f513b` `4d3326` `bb8971` `e4cecc` `be9e8c` `827265`, outline `080d16` `1b1e2a` `5a3827`) |
| `nara-senbei-stall` | 2x2 | all four | a small cart under a red parasol, stacks of round crackers tied with paper bands. No lettering |
| `nara-stone-lantern` | 1x2 | (0,1) | a tall mossy stone lantern, hexagonal cap: not `sendai-stone-lantern` |
| `nara-fingerpost` | 1x2 | (0,1) | the `fingerpost` builder again |

`LOOK_UP` gains `'nara-daibutsuden': 0`. Look at `--preview` before going on: each must read at a glance
at phone zoom, and the hall must not read as Himeji's keep.

### `tools/generate_nara.py` (new)

Header and tail as `generate_okayama.py`. `rng = random.Random(268)`; `b.fill('grass-autotile')`.
`NORTH = ks.is_open('Nara', 'n')`, `TOP = 0 if NORTH else 2`. `AUTUMN = ['sendai-maple', 'sendai-pine',
'sendai-cedar', 'sendai-maple', 'sendai-pine']`, `CEDARS = ['sendai-cedar', 'sendai-cedar',
'sendai-pine']`. In this order:

| part | what | cells |
|---|---|---|
| avenue, plaza | `flat-grey-brick-autotile` over `rect(0,18,42,22)` + the plaza `rect(31,16,42,23)` in one call; `(0,18)` = `edge-n`, `(0,22)` = `edge-s` (the seam); `k.road_h(0, 29, 19, cap_e=True)` | rows 18-22 |
| river | `pond-autotile` on `Water`, every cell solid, over `rect(0,14,22,16)` + `rect(20,TOP,22,13)`. Rows 14-16: `corner-se` at (22,16), `edge-e` on x 22, `edge-s` on row 16, `edge-n` on row 14 for x < 20, else `center`. Above: `edge-w` on x 20, `edge-e` on x 22, `center` on 21; when closed, row `TOP` is `edge-n`, `edge-n`, `corner-ne` | in on rows 14-16, north up columns 20-22 |
| bank rocks | `okayama-bank-rock` at (19,13); when closed, also at (19,1) | the bend; the closed head |
| towpath | `gravel-autotile` over `rect(23,TOP,24,17)`: it meets the avenue's pavement at row 18 | columns 23-24 |
| court | `gravel-autotile` over `rect(28,10,45,13)` + `rect(36,13,37,15)` | |
| hall | `b.stamp('nara-daibutsuden', 31, 2)`; `k.solid_rect(31, 2, 42, 9)` | rows 0-1 behind it are wood |
| wall, gate | `k.wall(25, 33, 14)`, `k.wall(40, 46, 14)` (`sendai-earthen-wall`, rows 14-15); `b.stamp('nara-nandaimon', 34, 12)` | crossed at columns 36-37 only |
| stall | `nara-senbei-stall` at (41,16): bumped from row 18 and column 40 | the plaza's north-east corner |
| Kasuga Taisha | `gravel-autotile` over `rect(32,24,33,36)` + `rect(32,35,45,36)` + `rect(44,31,45,36)`; `nara-kasuga-torii` at (31,24) (walked through on columns 32-33); `shrine-red` at (42,24): door (44,30), front (44,31) | south of the plaza, round a cedar wood |
| lanterns | `nara-stone-lantern`, feet at (31,29) (31,31) (31,33) (34,29) (34,31) (34,33) (36,34) (38,34) (40,34) (34,37) (36,37) (38,37) (40,37) (42,37) (43,32) (46,32) (43,34) (46,34), and (42,24): stamp at y - 1 | either side of the approach; the last stands at the plaza's south-east corner and closes the cell behind the shrine (Review 3) |
| deer | does (8,26) (17,30) (25,27) (30,12) (26,17); stags (12,29) (22,25) (43,11) (25,8), in that order; bowing (40,17) (33,17) (19,23) | lawn, court, plaza, pavement |
| lawn | `k.trees('sendai-maple', [(6,31), (14,26), (27,31)])`, `k.trees('sendai-pine', [(10,33), (20,28), (24,32)])` | (4..29, 24..33) |
| fingerpost | `b.stamp('nara-fingerpost', 3, 22)`: foot (3,23) | |
| closed edges | `shrub-small` at (0,17) (1,17) (0,23) (1,23), then `k.woods` over, in order: (0,0,19,13); if closed (20,0,24,1); (25,0,51,1); (25,2,30,9); (25,10,27,13); (43,2,51,9); (46,10,51,13); (47,14,51,39) `CEDARS`; (43,21,46,25) `CEDARS`; (35,24,41,33) `CEDARS`; (0,24,3,39); (4,34,30,39); (31,38,46,39) `CEDARS`. The rest `AUTUMN` | all but (0, 18..22) |
| plants | `k.plants(rng, 26, 4, 24, 29, 33)`, `k.plants(rng, 8, 2, 17, 22, 17)`, `k.plants(rng, 6, 25, 16, 30, 17)` | |

Tail: `k.dress(); b.finish()`; `b.room('Nara', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev,
ks.seams('Nara')))`; `waterways = [{'axis': 'h', 'row': 14, 'rows': 3, 'from': 0, 'to': 19}]`;
`rg.save_config`. No `train-track*`, no other town's art but the `sendai-` trees and wall the kit already
uses, no bin, no `pond-autotile_corner-nw` while the north is closed. The first stag in `"x,y"` string
order must stay (12,29): the `LANDMARKS` row below anchors on it.

Nineteen lanterns. The one with its foot on (42,24) is there because that cell is otherwise open: the
`shrine-red` prefab's top row has no collider, the cedar woods either side stop at columns 41 and 43, and
the plaza's corner (42,23) is right above it, so it was a one-cell pocket of grass behind the shrine's
roof that reads as a way round the back (media: `268-review-pocket-42-24.png`, and
`268-review-pocket-closed.png` with the lantern). The shrine's own sprite sits on `Collidables` at
(42,24), so a shrub cannot go there; the lantern is stamped at (42,23) and only its foot is solid. It
changes two cells and no tree (the stamp draws nothing from `rng`).

Nothing here needs a row in `Occlusion.js`, `Glows.js` or `DayNight.js`. The gate and the torii are
walked under and fade like `himeji-kokoen-gate` does (`docs/occlusion.md`: any sprite drawn over more than
half of a character fades); the hall is solid over its whole footprint and rows 0-1 behind it are wood, so
nobody stands behind it. The lanterns are unlit at night, as `sendai-stone-lantern` is: the halo rule in
`DayNight.js` matches `lamp-post` and `-lanterns`, not `-lantern`. Keep the key singular.

### `tools/generate_osaka.py`

- The east rail cap (`shrub-small` at `(W - 1, 3..5)`, line 105) only `if not ks.is_open('Osaka', 'e')`:
  the track then reaches the edge and `backdrop.extend` carries it on.
- When open, after the avenue is laid: `(W - 1, O_AVENUE[0])` = `flat-grey-brick-autotile_edge-n`,
  `(W - 1, O_AVENUE[-1])` = `…_edge-s`, and `b.stamp('nara-fingerpost', W - 3, ks.O_AVENUE[-1])` (foot
  Osaka (47,29)).
- `ks.seams('Osaka')` then returns the west five and the east five ((49, 24..28) to Nara (3, 18..22)),
  in that order because `joins()` walks `JOINS` in row order: the new `('Osaka', 'e', …)` row must come
  after `('Osaka', 'w', …)`, as in the snippet above. Osaka's generator does not call `rg.kept_order` (it
  writes `[the station door, Don Takote's door] + ks.seams('Osaka')`): the order is `JOINS`' order, and
  the seam test below pins it. Docstring: the east edge is the avenue on to Nara.

### Config, the world file, the shrine (by hand, then the tools)

- `../devhouse.world`: `gamev2/tiled/nara.tmj` at x -7680, y 4288, 3328x2560 (cell (-120, 67)).
- `config.json`: `cities.KansaiCity.rooms` gains `{"room": "Nara", "x": -120, "y": 67}`;
  `places.Nara = {"geo": [135.84, 34.69], "label": "Nara", "minor": true}`.
- `tools/generate_shrines.py` `NAMES`: `('Nara', 'shrine-building_0_0'): 'Kasuga Taisha'`. Running it for
  `Nara` makes `ShrineNara1` (20x16, standard, red; mats (9,13) (10,13) back to Nara (44,31)) and the door
  transporter Nara (44,30) to `ShrineNara1` (9,12), which `rg.save_config` keeps through a rebuild.

### `tools/districts.py`, `tools/blog_to_npc.py`

Before `# --- Tohoku ---`:

```python
# Nara: walked to from Osaka, the east end of KansaiCity (issue #268)
'Nara': [
    d('todaiji', 'Todaiji',
      'the Great Buddha Hall behind the Nandaimon gate, its gravel court, and the plaza where the avenue ends: '
      'the deer cracker stall',
      (30, 2, 46, 23), stand=(35, 11)),
    d('nara-park', 'Nara Park',
      'the deer park: the lawn and its maples south of the avenue in from Osaka, deer resting on the grass, '
      'the river and its towpath',
      (2, 17, 29, 33), stand=(16, 25)),
    d('kasuga', 'Kasuga Taisha',
      'the vermilion shrine in the cedar wood: the torii, the approach lined with stone lanterns, the hall',
      (30, 24, 46, 37), stand=(40, 35)),
],
```

`LANDMARKS`, before the `karuizawa-fingerpost_` row:

```python
('nara-daibutsuden_', 'the Great Buddha Hall', (4, 8), {'rooms': ('Nara',)}),   # (35, 10): the court in front of the hall, off the axis
('nara-nandaimon_', 'the Nandaimon gate', (1, 4), {'rooms': ('Nara',)}),       # (35, 16): the plaza below its west post, off the gateway
('nara-senbei-stall_', 'the deer cracker stall', (0, 2), {'rooms': ('Nara',)}),   # (41, 18): the plaza at its counter
('nara-deer-stag_', 'the deer of Nara Park', (1, 0), {'rooms': ('Nara',)}),    # (13, 29): the lawn beside the first stag
('shrine-building', 'Kasuga Taisha', (2, 6), {'rooms': ('Nara',)}),            # (45, 32): the approach, east of the door's column
```

`districts.py` then reports 48 districts in 17 rooms, with spots `todaiji`: the three above; `nara-park`:
the deer; `kasuga`: `Kasuga Taisha` and the generic `the shrine`.

### `src/utils/Interactions.js`

`flavour` rows with `footprint: true`, after Okayama's:

| kind | pattern | say |
|---|---|---|
| `fingerpost` | `/^nara-fingerpost/` | `west: osaka, dotonbori. east: nara, the great buddha and the deer` |
| `deer` | `/^nara-deer-(doe\|stag)/` | `a deer, resting. it has seen ten thousand visitors today and you are not the interesting one` |
| `deer-bow` | `/^nara-deer-bow/` | `the deer bows. it wants a cracker. it bows again, lower, and stands on your foot` |
| `senbei-stall` | `/^nara-senbei-stall/` | `deer crackers, 200 yen a stack. every deer in the park knows the sound of the paper band` |
| `stone-lantern` | `/^nara-stone-lantern/` | `a stone lantern, furred with moss. there are two thousand along this path, each one given by somebody` |
| `nandaimon` | `/^nara-nandaimon/` | `the great south gate. two wooden guardians, eight metres tall, glare out of the dark either side` |
| `great-buddha-hall` | `/^nara-daibutsuden/` | `the great buddha hall. fifteen metres of bronze sit inside, and a pillar with a hole the size of his nostril` |
| `torii` | `/^nara-kasuga-torii/` | `the vermilion gate of kasuga taisha. the deer walk through without bowing` |

### `src/utils/Places.js`

The order the dots choose in moves out of `layout()` into a static, so that it can be tested, and gains
one condition: a small place whose dot touches a town's does not hem that town in.

```js
/** The order the dots choose their label's spot in: the most hemmed-in first (the distance to the
 *  nearest other dot), every `minor` dot after the others. A small place whose dot touches a town's
 *  does not hem that town in (issue #268); one that stands clear of it still counts. */
static order(dots) {
    const apart = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    const crowd = (d) => Math.min(...dots.filter(o => o !== d && !(o.minor && !d.minor && apart(o, d) < o.r + d.r)).map(o => apart(o, d)), Infinity);
    return dots.slice().sort((a, b) => (!!a.minor - !!b.minor) || crowd(a) - crowd(b) || (a.key < b.key ? -1 : 1));
}
```

and in `layout()`, `const sorted = Places.order(dots);` replaces the `crowd` and `sorted` lines. Add the
sentence to `layout()`'s doc comment too. Nothing else in `layout()` changes: a small place's dot is still
a dot no label may cover.

Why not the wider rule (`o !== d && (d.minor || !o.minor)`: no small place counts for any town). Both
were measured on the blockout and on today's world, every trip day (2025-10-02 to 11-18, 2027-02-18 to
28) for James and each member, standing where they start, in the seven views the label test uses (3304
layouts each):

| | today's Map: layouts changed | today's Map: Fukuoka's label on a leader | with Nara: town labels on a leader |
|---|---|---|---|
| no change to `layout()` | 0 | 48 | 2778 (and the #263 test fails) |
| the wider rule | 872 | 893 | 3409 |
| the touching rule (this design) | 54 | 78 | 2717 |

The wider rule fixes Nara by dropping Karuizawa, Himeji and Okayama from every town's count as well,
which changes when Fukuoka chooses: at 320x780 and 360x840 its label, beside its dot today, goes onto a
leader on 441 and 452 of the 472 trip-day layouts, and Okayama's and San Franbourne's move with it (media:
`268-review-map-360x840-today.png`, `…-design-rule.png`, `…-narrower-rule.png`, the same day and place).
No test sees that: the Map tests assert that labels fit and do not overlap, not where they are. The
touching rule passes the same tests (all of `japan-map.test.js` and `airports.test.js` with the edits
below, the Lake Biwa stub stage included), gives the same result on desktop and a landscape phone (a town
on a leader in 46 of 944 layouts; 83 with no rule), and with it today's Map differs from what is live in
54 layouts instead of 872.

### Other tools

- `tools/check_generators.py`: `GENERATORS += ['generate_nara']` after `generate_okayama`.
- `tools/check_distinct.py`: add `nara-` to `LANDMARK_ART`. Do not run `--update`.

### Build order

```bash
cd gamev2                                   # art tools need Pillow
python3 tools/extract_street.py
python3 tools/generate_kansai_art.py --preview /tmp/kansai.png
python3 tools/make_prefabs.py
python3 tools/generate_nara.py              # after the devhouse.world and config.json edits above
python3 tools/generate_osaka.py
python3 tools/generate_shrines.py Nara
python3 tools/sync_cities.py
python3 tools/districts.py
python3 tools/blog_to_npc.py --rehome Damian 2025-11-14 "Nara · the Great Buddha Hall" --dry-run   # expect (35, 10); then without --dry-run
python3 tools/config_to_tiled.py Nara Osaka ShrineNara1
python3 tools/make_worldmap.py --pil
for r in Nara Osaka KansaiCity ShrineNara1; do node tools/play.js lint $r; done
node tools/play.js render Nara /tmp/nara.png          # and look at it, and at KansaiCity's seam
python3 tools/check_distinct.py
```

`--rehome` adds Damian's hidden base def to Nara, puts him at (35,10) on 2025-11-14 with photo 764, makes
him absent from Osaka that day and from Nara from 2025-11-15 (he moves on to Osaka); nothing else is
edited by hand.

### Docs (same commit)

`docs/landmarks-and-towns.md` (the landmark and districts tables; "Kansai": Nara's paragraph, `BUILT`, the
city is 190x46, the third seam and its fingerposts, the north edge waiting on Lake Biwa, build order, the
shrine's name), `docs/stitched-city.md` (four districts, 190x46), `docs/blog-pipeline.md` (line 140: 764
moved from Osaka's canal bank to `Nara · the Great Buddha Hall`), `docs/ambient-traffic.md` (the canal is
one run from Himeji's moat to Nara's bend; the track is carried east across the bare strip above Nara),
`docs/hud-input-touch.md` (the small places; the stub is Lake Biwa alone; `Places.order`: a small place
whose dot touches a town's does not hem it in), `docs/trains-and-stations.md` (Nara has no station),
`docs/generators-and-checks.md` (Kansai's distinctness figures as measured). `docs/trips-and-dates.md`
needs nothing: no start changes.

## Data and interfaces

- `config.json`: `rooms.Nara` and `rooms.ShrineNara1` (new); `rooms.Osaka` (east rail cap gone, two
  pavement tiles, a fingerpost, ten seams); `cities.KansaiCity.rooms` (+ Nara); `places.Nara`;
  `districts.Nara` (three); `game.lookUp.sprites['nara-daibutsuden'] = 0`; `spriteMetadata` / `tileNames`
  / `tilePalette` (appended only) for the nine sprites; Damian's 2025-11-14 state moves from `Osaka`
  (39,19) to `Nara` (35,10).
- `../devhouse.world`: one map added, none moved. New: `tiled/nara.tmj`, `tiled/shrinenara1.tmj` (as
  `config_to_tiled.py` names it), nine `tiled/prefabs/*.tmj`, nine PNGs. Rebuilt: `tiled/osaka.tmj`,
  `assets/map/*`.
- Runtime, from the data alone: the city room is 190x46 (`depthScale` 1). The backdrop's track is 140
  tiles on city row 4: 88 west of Osaka and 52 two rows above Nara's top edge, to the map's east edge, on
  the six rows of open ground the backdrop keeps clear of trees there (`extendClear: 4`): not through a
  wood. The three `waterways` join into one run, city x 51 to 158, `under` the two existing bridges;
  it ends at the bend, so a boat fades in and out there (the plan: no waterway north of the bend).
- `Places.order(dots)` (new static, the order `layout()` already used): differs from today's order only
  where an unlit small place's dot overlaps a town's (the distance between them is less than the two
  radii). `layout()`'s arguments and result are unchanged.
- No new source file, no script-list change, no localStorage, no API.
- Start rooms, measured before and after for James and the seven members on every day 2025-10-25 to
  2025-12-03: none changes. Nothing to pin.

## Tests

`tools/tests/kansai.test.js`:

- `DISTRICTS = ['Himeji', 'Nara', 'Okayama', 'Osaka']` (the `seams` helper filters on it); HUD names
  likewise; `unbuilt` is `['LakeBiwa']`; titles name Nara.
- Seams: 30 pairs. `seams('Osaka')` is (0, 24..28) then (49, 24..28), in that order, and the last ten of
  `rooms.Osaka.transporters` are those (the west five did not move); `seams('Nara')` is (0, 18..22).
  Across Osaka x 49 / Nara x 0 the floors are equal on the five avenue rows (`edge-n`, `road-edge-top`,
  `road-div-horizontal`, `road-edge-bottom`, `edge-s`) and the water on Osaka rows 20-22 / Nara rows 14-16
  (`edge-n`, `center`, `edge-s`), solid both sides. `edgeOpen('Osaka')` is its ten seam cells;
  `edgeOpen('Nara')` is `0,18 … 0,22` only. Drop the block that expects a step east off Osaka to fail.
- Waterways: three runs (Himeji, Osaka, Nara); Nara's starts where Osaka's ends, on its rows; joined, one
  run `[AT.Himeji[0] + 7, AT.Nara[0] + 20]` (51, 158) with the same two `under`. Every cell of
  (0..19, 14..16) and (20..22, 2..16) is `pond-autotile` and solid.
- The walk: add `['Nara', 34, 10]`, `['Nara', 44, 31]`, `['Nara', 23, 2]`, `['Nara', 16, 28]` after
  Korakuen; `ORDER` is `['Okayama', 'Himeji', 'Osaka', 'Nara']`; the city is
  `[AT.Nara[0] + SIZE.Nara[0], SIZE.Osaka[1]]` = `[190, 46]`; the track is `AT.Osaka[0] + SIZE.Nara[0]`
  (140) tiles, each `y === 4` and `x < AT.Osaka[0] || x >= AT.Nara[0]`; `[fades, crossings]` is `[0, 6]`
  stitched and `[6, 0]` with `?stitch=0`. Passed on the blockout as written here.
- Fingerposts: add Osaka x 49 and Nara x 0 with `nara-fingerpost_0_0` and its line; one of each key per
  room it belongs in. Osaka (49, 3..5) carries no shrub and (49,4) has track, as the west test does.
- New, Nara, on the shape of Okayama's four: (1) the hall is at (31,2), its PNG 768x512, no cell of
  (31..42, 2..9) walkable and rows 0-1 not reachable; the wall (25..46, 14..15) is crossed at columns
  36-37 only; `lookUp.sprites['nara-daibutsuden'] === 0` and `LandmarkView.aim` gives weight 1 from
  (35,10), (34,10), (36,10) and (35,11) in both views, the whole hall on desktop; the five `LANDMARKS`
  rows are in `blog_to_npc.py` and their cells are walkable. (2) Kasuga Taisha: the door (44,30) leads to
  `ShrineNara1`, named `Kasuga Taisha`, and back to (44,31); nineteen lanterns; (42,24) is not walkable and (42,23)
  is, and no cell of rows 24-25 between columns 35 and 46 can be reached (nothing leads round the back of
  the shrine); the torii is walked through on columns 32-33 and its posts are solid; (44,31) is reached from Osaka; `districts.Nara` keys
  are `kasuga, nara-park, todaiji`. (3) Damian on 2025-11-14: present in Nara at (35,10) with post 764,
  reachable, not on a seam, that day only, and in no other room. (4) a deer of each kind, the stall, a
  lantern, the gate, the hall and the torii answer a bump with their line; no room key starts `Nara` but
  `Nara`, no station names it, no `train-track`, Hokuriku art, bin or ordinary building
  (`/^(house-|building-|machiya|highrise|seven-eleven|himeji-|okayama-keep)/`); `places.Nara` is exactly
  the entry above. (5) while `LakeBiwa` is not in `BUILT`: `JOINS` has the `('Nara', 'n', …)` row, the
  river and the towpath stop at row 2, no cell of row 0 or 1 is walkable, and Nara has no
  `pond-autotile_corner-nw`.

Other files:

- `tools/tests/japan-map.test.js`: `SMALL` and `KANSAI` keep Lake Biwa only (one stage; the lengths at
  335-336 follow: `P.list(realConfig()).length + 1`, `[1]`); add `Nara` to the label list (106), to the
  minor places (332, 334: `['Himeji', 'Karuizawa', 'Nara', 'Okayama']`) and to the places with no station
  (474); `dots.length` is 14 (382); `P.arrival(config, 'Nara')` is `{ room: 'Nara', x: 3, y: 18 }`;
  `MAY_TOUCH` keeps `['Nara', 'Osaka']`. The #263 Karuizawa test must pass unchanged. Two new cases:
  - `Places.order`, on made-up dots (radius 5; towns A, B, C, D at x 100, 130, 150, 300 on one row, whose
    order is B, C, A, D): with a `minor` dot at x 108 (touching A) the towns' order is still B, C, A, D
    and the small place is last; with it at x 112 (clear of A) the order is A, B, C, D; with the dot at
    108 not `minor` (lit) it is A, m, B, C, D. And `layout()` calls `Places.order(dots)`. Passed on the
    blockout as written here.
  - The Map on 2025-11-14 (Damian in Nara, so Nara's dot is lit and not `minor`, and no rule above
    applies): on the shape of the #263 test, for James and each member, standing in their start room, in
    Osaka and in Nara, in every view: every label fits, none covers another or a dot. It does not assert
    "no leader": Osaka's label stands off its dot that day on every phone (Risks).
- `tools/tests/dates-trips.test.js` (365): `where('2025-11-14').Damian` is `'Nara 35,10'` and
  `posts('Damian', '2025-11-14', 'Nara')` is `764`; fix the comment above it.
- `tools/tests/hud-phone-layout.test.js` (213): the 715 list gains `'Kasuga Taisha'` beside
  `'Palace Shrine'` (13 characters: it counts down at 744 and shows the date at 715).
- `tools/tests/roads-waterways.test.js` (258): the list gains
  `"KansaiCity: Osaka's waterway is carried on by Nara's"`.
- `tools/tests/shrines.test.js`: `WIRED` gains `ShrineNara1: { host: 'Nara', look: 'red', size:
  'standard', name: 'Kasuga Taisha' }`; the count at 44 is 7.
- `tools/test_blog_to_npc.py`: `REPLACED_219[('Damian', '2025-11-14')] = ('Nara', (35, 10))`. Nothing in
  it failed on the blockout.
- `tools/tests/map-data.test.js` and the world-map assertions pass once `make_worldmap.py --pil` has run.

Run, from `gamev2/` (all must pass):

```bash
node tools/test_game.js                # several minutes in the container
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # with Pillow, so the art tools are covered
python3 tools/sync_cities.py --check
python3 tools/rehearse_blog.py         # blog_to_npc.py changed
python3 tools/check_distinct.py
```

then the browser regression (`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in the container).

**Play it** (desktop 1280x800 and a phone, 390x844 portrait and 844x390 landscape; `?notitle=1&nointro=1`,
`&date=2025-11-14`): walk east out of Osaka into Nara with no fade and nothing changing at the seam; read
both fingerposts; along the towpath to its end (closed, the river's head beside it); through the Nandaimon
into the court, stand in front of the hall (the camera looks up, the whole hall in view on desktop), talk
to Damian; bump a deer of each kind, the stall, a lantern, the hall; through the torii, round the approach
and into Kasuga Taisha and out again; try the east, north and south edges (closed); watch a boat come
along the river from Osaka; the same walk with `&stitch=0` (one fade each way). Stand in the gateway
(36..37, 12..13) and under the torii's lintel (32..33, 24): the roof fades and the character is seen. Try
to step south off the plaza's corner (42,23): the lantern stops you. Once at `&tod=night`: the plaza, the
approach and the court read; the lanterns are unlit on purpose. Open the Map at 320x780, 360x840, 390x844
and 844x390, standing in Osaka and in Nara, on 2025-11-14 and 2025-11-02: Nara's dot and label are drawn,
Osaka's and Nara's dots are both seen, no label is hidden; on 2025-11-14 Osaka's label is the one that
stands off (above its dot on a landscape phone: `268-review-map-landscape-2025-11-14.png`) and must still
read as Osaka's. At 360x840 on 2025-10-20 from Tokyo, compare with the live game: only Nara's label is
new, Fukuoka's is still beside its dot (`268-review-map-360x840-narrower-rule.png` against
`…-today.png`). Look at the screenshots; save them to `/work/media/`.

## Risks and open questions

- **The hall is the district.** It must read as the Daibutsuden (the broad double roof, the gold horns),
  not as a keep. On a landscape phone the view is under eight rows tall, so from the court the camera
  shows the walls and the lower roof, as with Himeji's keep; the whole hall is seen on desktop. If it does
  not read on a phone, fix the art, not the map.
- **The rock at the river's head** is a patch for one ticket: the head has a round east corner and a rock
  on its west one. If it looks stuck on in the browser, plant a `sendai-pine` beside it; do not use
  `corner-nw` (it becomes a pipeline spot).
- **The railway runs behind Nara**: with the cap off Osaka's east edge the backdrop carries the track
  to the map's east edge two rows above Nara's top row. It does not run through a wood: the backdrop
  keeps the six rows above Nara clear of trees (`extendClear`), so from the north end of the towpath a
  bare track on open grass is in view above the trees of rows 0-1 (media:
  `268-blockout-desk-towpath.png`), in a town with no station. It is what the plan asks for and what
  Himeji and Okayama already show, and no train stops there. If it reads wrong when played, the fix is
  the east cap back on Osaka (one line), not a taller wood: Nara's top edge is where #269 joins. #269
  ends the track short of the lake (`extendStop`).
- **`Places.order` is for every Map**, not only Nara's, which is why the rule is the narrow one: it
  changes today's Map in 54 of 3304 trip-day layouts (all at 320x780 and 360x840 on days with
  friends in Osaka, where Himeji's unlit dot overlaps Osaka's larger lit one); the first draft's rule
  changed 872. Every Map test
  passed with it on the blockout, including the stage with the Lake Biwa stub; look at the Map on the
  days in "Play it". Lake Biwa's dot (#269) will come under the same rule where it touches Osaka's or
  Nara's.
- **On 14 Nov 2025 the rule does not apply**: Damian is in Nara, so its dot is lit and chooses with the
  towns, and Osaka's label is the one that gives way. From the day's start room (Fukuoka) it stands off its dot on every phone,
  landscape and portrait, for everyone but Damian himself (played as Damian, Nara is not lit), and not on
  desktop: 42 of that day's 56 layouts. Standing in Nara it stands off on desktop too; standing in Osaka
  it never does. All of that is the same with or without any change to `layout()`. Every label still fits and none overlaps (0 problems in 560 layouts of that day);
  on a landscape phone it sits just above its dot and reads. It is the one day a town's label moves for
  Nara: accepted, and covered by the 2025-11-14 test and "Play it". Do not widen the rule to cover it
  without measuring every other day again.
- **Osaka's trees do not move**: the east edge had no wood on the avenue rows, and the seeded calls keep
  their order. The Osaka tests passed unchanged on the blockout apart from the ones listed.
- **Rooms touched** (map data is serial): Nara (new), ShrineNara1 (new), Osaka (east edge), `KansaiCity`,
  `../devhouse.world`. Lake Biwa (#269) rebuilds Nara's north edge and `kansai.py` after this: land this
  first.
- No open question for the owner.

## Review

Design adversary pass. The design was rebuilt from this file alone on a scratch copy of the branch
(placeholder art, every cell and row as written above) and attacked there; nothing in the repository but
this file was changed. Most of it held: the cells, the seams, the shrine wiring, the pipeline rows, the
re-homing and the list of failing tests all came out as the design says. Seven criticisms, each with what
was measured.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **The `Places.layout` rule was far wider than its purpose, and worse for the Maps the game already draws.** "A small place does not crowd a town" drops Karuizawa, Himeji and Okayama from every town's count on every Map, not only Nara from Osaka's. Measured on today's world (no Nara), every trip day, James and each member, seven views, from the start room: 872 of 3304 layouts change; Fukuoka's label goes onto a leader in 893 (48 today), all at 320x780 and 360x840; town labels on a leader 2581 to 3325. The design said "the label order changes only where a small place is the nearest dot to a town", which is true and is a quarter of all layouts. No test sees it: the Map tests assert fit and overlap, not position. | A small place stops counting for a town only when the two dots touch (`apart(o, d) < o.r + d.r`). Same result where the problem was (the #263 test passes; desktop and landscape: a town on a leader in 46 of 944 layouts under either rule, 83 under none), 54 of 3304 of today's layouts change instead of 872, Fukuoka on a leader 78 times, and with Nara fewer town labels on a leader (2717) than with no rule (2778) or the wide one (3409). Media: `268-review-map-360x840-*.png`. | Yes: "`src/utils/Places.js`", Approach, Risks |
| 2 | **The rule could not be tested as the design described it.** "A town's order in the layout is the same with and without a minor dot beside it" is not observable through `layout()`: the order is a local, and the small place's dot still blocks spots, so positions differ either way. | Pull the order into `static Places.order(dots)` (the repo's rule: a decision in a Phaser-side class becomes a static with a case) and test that: a touching small place leaves the towns' order alone, one standing clear still counts, a lit one counts. Written and run on the scratch copy: 18 of 18 in `japan-map.test.js` + `airports.test.js`. | Yes: Tests |
| 3 | **14 Nov 2025, the day the ticket is about, is the one day no rule covers, and the design did not say so.** Damian is in Nara, so its dot is lit, is not `minor`, and chooses with the towns. Osaka's label then stands off its dot on every phone for everyone but Damian (42 of the day's 56 layouts from the start room; on desktop too when standing in Nara). The designer's media has that day on desktop and a portrait phone, not landscape. | Looked at it (`268-review-map-landscape-2025-11-14.png`: Osaka's label sits just above its dot and reads; nothing overlaps, 0 problems in the 560 layouts of that day surveyed, standing in Fukuoka, Osaka, Nara, Tokyo and Karuizawa). Say it under Risks, add a 2025-11-14 Map test on the shape of #263's without the "no leader" assertion, and put the landscape Map of that day in "Play it". | Yes, as a recorded and tested limit. No rule change: making Osaka choose before a lit Nara was not measured, and criticism 1 is what an unmeasured order change costs |
| 4 | **A one-cell pocket behind the shrine.** Nara (42,24) is walkable from the plaza's corner (42,23): the `shrine-red` prefab has no collider on its top row and the two cedar woods stop at columns 41 and 43. It reads as a way round the back of Kasuga Taisha and goes nowhere. | A nineteenth `nara-stone-lantern` with its foot on (42,24) (stamped at (42,23)). A shrub cannot go there (the shrine's sprite holds that `Collidables` cell); widening a wood would reshuffle the seeded trees and plant on the plaza. On the scratch copy it changes two cells, lint stays clean, `play.js check` passes. Media: `268-review-pocket-42-24.png`, `268-review-pocket-closed.png`. A test asserts the cell is closed. | Yes: the lanterns row, Tests |
| 5 | **A wrong statement about Osaka's generator**: "`rg.kept_order` keeps the first five where they are". `generate_osaka.py` never calls `kept_order`; the west seams come first only because `joins()` walks `JOINS` in row order. Someone tidying `JOINS` by district would reorder Osaka's transporters without meaning to. | Say what the order depends on, and pin it in the seam test (the last ten transporters: west five, then east five). | Yes: "`tools/generate_osaka.py`", Tests |
| 6 | **"The track is carried across the wood" is not what is drawn.** The backdrop keeps the six rows above Nara clear of trees, so the track runs on bare grass in plain view from the towpath's end, in a town the owner wants walked to with no station. The designer's own capture shows it. | Describe it as it is in Risks, Data and the docs line, and name the one-line way back (the cap on Osaka's east edge) if it reads wrong when played. | Wording: yes. Keeping the cap: no. The plan carries the track east so #269 can end it at the lake, Himeji and Okayama show the same strip, and no train stops in it |
| 7 | **Occlusion and night lights were not mentioned**, though the plan's rules ask every tall sprite to be checked against `docs/occlusion.md` and every lit prop to have its `Glows` row. Two walked-under sprites and eighteen lanterns are exactly those cases. | Checked: `Occlusion.js` is generic (the gate and the torii fade as `himeji-kokoen-gate` does), the hall hides nobody (solid footprint, wood behind), and `nara-stone-lantern` is unlit because `DayNight.js` halos `lamp-post` and `-lanterns` only, as with `sendai-stone-lantern`. Written into the generator section, with a gateway, torii and `?tod=night` step in "Play it". | Yes |

**Considered and not raised.** The cell (2,23) beside the fingerpost and the grass east of the plaza
(43..46, 16..20) are open and empty: loose grass beside the pavement, as the other districts have, not
pockets behind anything. The pipeline has two spots a cell apart at the shrine (`the shrine` and `Kasuga
Taisha`, between the lantern feet (43,32) and (46,32)): the approach stays open round them and
`walls_in` guards placement. `test_blog_to_npc.py` passes on the blockout before the `REPLACED_219` row
is added, so that row is what makes it assert anything about Damian: the design already adds it. The
towpath is a dead end until #269: the ticket asks for it. Own art for the torii instead of the kit's
`torii-red` costs a sprite; the design's reason is a `check_distinct.py` measurement that was not
repeated here.

**Checked, not assumed** (on the scratch copy, built from this file): `play.js lint` clean for Nara,
Osaka, KansaiCity (190x46) and ShrineNara1; `play.js check` no problems, before and after the lantern;
`test_blog_to_npc.py`, `sync_cities.py --check` (13 rooms) and `check_distinct.py` (Kansai 0.11 / 0.35 /
45%, no city worse than the baseline) pass; `districts.py` reports 48 districts in 17 rooms; `--rehome`
moves Damian from Osaka (39,19) to Nara (35,10) and makes him absent from Nara from 15 Nov;
`generate_shrines.py` wires `ShrineNara1` at door (44,30), front (44,31); the deer are where the sheet
coordinates say; `node tools/test_game.js` before any test edit fails in exactly the twelve tests the
design lists and no other; start rooms for James and the seven members are the same before and after on
every day 2025-09-28 to 2025-12-05; rows 0-1 cannot be reached, the gate is crossed on columns 36-37
only and the torii on 32-33. The Map figures are from `Places.layout` run outside the browser on the
real config and `japan.json` with the views of the label test, and four Maps were looked at in Chromium.
**Not run**: the browser regression, a walk with real keys, `check_generators.py`, `rehearse_blog.py`,
the kit-torii comparison, and the unit tests other than the Map's after their edits (the design's own
blockout covers those). The implementer runs all of them.
