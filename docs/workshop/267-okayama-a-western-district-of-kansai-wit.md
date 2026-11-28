# Okayama: a western district of Kansai with the black keep and Korakuen (#267; #68, run 4)

## Context

Damian's post of 12 Nov 2025 (745: Hakata to Okayama by shinkansen, Korakuen, the castle, Bizen ware) stands
on Hakata's platform (`FukuokaStation` 1,5) because Okayama does not exist. #68's plan
(`docs/workshop/68-…md`, "Plan for the later tickets") makes Okayama the westernmost district of the
stitched `KansaiCity`: 44x40 at city cell (0, 36), west of Himeji, reached on foot along the avenue.
`tools/kansai.py` already holds its `AT` / `SIZE`, and Himeji's west edge is solid wood until it is built.

Outcome: `KansaiCity` is Okayama + Himeji + Osaka, one walkable room; Okayama has the black keep, Korakuen
on a river island over the Tsukimi bridge, a Momotaro statue and a Bizen-ware stall; Damian's post stands
in Korakuen; Okayama is a small place on the Map. Okayama's own west edge stays closed (nothing is planned
beyond it). Owner's rules: walked to, no station; only real places; no ordinary sealed buildings; no bins.

Everything below was built as a blockout on a copy of this branch (placeholder art, the cells in this
file) and measured: `play.js lint` is clean for Okayama, Himeji and KansaiCity, `play.js check`,
`test_blog_to_npc.py` (with the one pin changed), `check_generators.py`, `sync_cities.py --check` and
`rehearse_blog.py` (313/313) pass, and the unit tests that fail are exactly the ones listed under Tests.
The browser regression was not run on it, and it was not played in a browser. A render of the blockout is in the
ticket's media (`267-okayama-blockout.png`).

## Approach

Build Okayama the way #255 built Himeji: one generator on `roomgen.Builder` + `ks.Kit`, art drawn by
`generate_kansai_art.py`, the seam declared once in `kansai.py`, and Himeji's generator opening its west
edge through `ks.is_open('Himeji', 'w')`. The district is laid out on one north-south axis (columns 21-22):
keep, steps down the stone wall, across the avenue, the Tsukimi bridge, the island. The avenue ends west in
a paved plaza with the statue: there is no "town" of sealed buildings to draw.

Three choices that were close:

- **The river is `pond-autotile`** (rock-rimmed, solid), as the moat and the canal are. The set has no
  inner-corner piece, so the island's four corners show a notch in the rim; one new 2x2 sprite of the rim's
  own white stones (`okayama-bank-rock`, flat, the bridge's recipe) is stamped over each. Drawing a second
  water set was the alternative: more art for the same result.
- **No `waterways` row.** No arm of the ring leads anywhere, so a boat would fade in and out in full view
  beside the bridge; the plan does not ask for boats here. It also keeps the two waterway tests untouched.
- **The Himeji/Okayama fingerposts are a second sprite key, `okayama-fingerpost`** (the same drawing).
  `Interactions` matches a flavour rule by sprite key only, so the existing `kansai-fingerpost` cannot say
  two different lines. Not `kansai-fingerpost-…`: the `/^kansai-fingerpost/` rule would match it first.

## Changes

All paths under `gamev2/` unless they start with `../`. Cells are Okayama's own unless a room is named.

### `tools/kansai.py`

- `BUILT = ('Himeji', 'Okayama', 'Osaka')`.
- `OK_AVENUE = tuple(y + AT['Himeji'][1] - AT['Okayama'][1] for y in H_AVENUE)` (18-22, at x = 43) and a
  second row in `JOINS`: `('Himeji', 'w', H_AVENUE, 'Okayama', OK_AVENUE)`.
- Docstring: Okayama is built; its west edge has no join.

### `tools/generate_kansai_art.py`, `tools/make_prefabs.py`

New sprites in `SPRITES` (half-size canvas, doubled, like the others) and prefab rows beside Himeji's:

| key (`_0_0`) | cells | layer, colliders | what is drawn |
|---|---|---|---|
| `okayama-keep` | 8x7 (512x448) | Collidables; rows 2-6 solid (the generator closes the rest) | Okayama's "crow castle": black boarded walls with a white band under each eave, grey tiled roofs, gold shachi on the ridge, a low stone base (`masonry`). The art fills its footprint, nothing above it. `storeys` / `white_wall` need a wall-colour argument |
| `okayama-bridge` | 2x4 | Non-Collidables, no collider, `FLAT` -200 | the Tsukimi bridge, walked north-south: a grey steel footbridge deck with rails, not Himeji's timber |
| `okayama-bank-rock` | 2x2 | Non-Collidables, no collider, `FLAT` -200 | a heap of the pond rim's white stones, centred where its four cells meet, about 40 px across |
| `okayama-crane` | 1x2 | Collidables; (0,1) | a red-crowned crane |
| `okayama-momotaro` | 2x3 | Collidables; (0,2), (1,2) | the bronze Momotaro with dog, monkey and pheasant on a stone plinth |
| `okayama-bizen-stall` | 3x3 | Collidables; rows 1-2 | an open stall: awning, counter, rows of brown unglazed pots |
| `okayama-fingerpost` | 1x2 | Collidables; (0,1) | the `fingerpost` builder again |

`LOOK_UP` gains `'okayama-keep': 0`. Look at `--preview` before going on; every landmark must read at a
glance at phone zoom.

### `tools/generate_okayama.py` (new)

Header and build order as `generate_himeji.py`. `rng = random.Random(267)`; `b.fill('grass-autotile')`;
ends with `k.dress(); b.finish()`, `b.room('Okayama', npcs=prev.get('npcs', []),
transporters=rg.kept_order(prev, ks.seams('Okayama')))`, no `waterways`, `rg.save_config`.

| part | what | cells |
|---|---|---|
| avenue | `flat-grey-brick-autotile` over `rect(6,18,43,22)` + the plaza `rect(6,15,12,23)` in one call; `(43,18)` = `edge-n`, `(43,22)` = `edge-s` (the seam, as Himeji's); `k.road_h(13, 43, 19, cap_w=True)` | rows 18-22 |
| axis | `k.paved` on `(21..22, 15..17)` and `(21..22, 23)` | columns 21-22 |
| terrace | `gravel-autotile` over `rect(13,3,40,12)`, laid before the keep and the wall | |
| wall | `b.wall_stone(x, 13)` for x 13..40 except 21, 22; there `k.paved` + `b.stairs` on rows 13-14 | rows 13-14 |
| keep | `b.stamp('okayama-keep', 18, 2)`; `k.solid_rect(18, 2, 25, 8)` | not on the top row: rows 0-1 are wood |
| terrace dressing | `sendai-pine` trunks (14,6) (29,5) (36,7) (38,11); `sendai-stone-lantern` feet (16,10) (27,10). Nothing on (18..25, 9..10): the keep's visitor and whoever talks to them | |
| plaza | `okayama-momotaro` at (8,17): feet (8..9, 19) | |
| stall | `okayama-bizen-stall` at (15,15): bumped from the pavement, row 18 | |
| river | `pond-autotile` on `Water` over `rect(5,24,40,37)` minus the island `rect(7,27,38,35)`: outer ring `corner-*` / `edge-n` (row 24) / `edge-s` (row 37) / `edge-w` (x 5) / `edge-e` (x 40); the island's banks `edge-s` (7..38, 26), `edge-n` (7..38, 36), `edge-e` (6, 27..35), `edge-w` (39, 27..35); `center` elsewhere. Every cell solid except (21..22, 24..26) | three rows wide north, two elsewhere |
| bridge | gravel on Floor under `rect(21,24,22,26)`; `b.stamp('okayama-bridge', 21, 24)`: lands on row 27 | |
| bank rocks | `okayama-bank-rock` at (6,26) (38,26) (6,35) (38,35) | the island's corners |
| island | gravel: `rect(21,27,22,29)` + the loop `rect(9,28,36,29)`, `rect(9,28,10,34)`, `rect(9,33,36,34)`, `rect(35,28,36,34)`; `b.pond(14, 31, 19)`; `sendai-maple` trunks (12,31) (31,31) (25,32); `sendai-pine` (7,28) (37,28) (22,32) (7,35) (37,35); **cranes** feet (28,31) (30,32), stamped in that order; lanterns feet (20,27) (23,27) (33,31); `k.plants` on the lawn | (7..38, 27..35) |
| fingerpost | `b.stamp('okayama-fingerpost', 39, 22)`: foot (39,23), beside the pavement | |
| closed edges | `shrub-small` at (42,23) (43,23) **before** the woods; `k.woods` over (0,0,43,1), (0,2,12,14), (0,15,4,39), (41,2,43,17), (41,24,43,39), (5,38,40,39) | all but (43, 18..22) |

Kinds as Himeji's (`AUTUMN` for the woods). No `train-track*`, no `hokuriku-|kanazawa-|shirakawa-|toyama-`
sprite, no bin.

### `tools/generate_himeji.py`

`WEST = ks.is_open('Himeji', 'w')`; the closed branch stays as it is. When open:

- the avenue's brick starts at x = 0, not 5; `(0,18)` = `edge-n` and `(0,22)` = `edge-s` like the east
  seam; `k.road_h(0, W - 1, AVE0 + 1, cap_w=False)`;
- the west woods keep their order and rectangles, but the third stops short of the avenue:
  `k.woods(0, 0, 7, 7)`, `k.woods(0, 8, 5, AVE0 - 1)`, then `b.stamp('okayama-fingerpost', 4, AVE1)` (foot
  (4,23)) and `shrub-small` at (0,23) (1,23), then `k.woods(0, AVE1 + 2, 4, H - 1)`;
- `ks.seams('Himeji')` now returns ten transporters (east five, then west five); `rg.kept_order` keeps
  the first five where they are.

Docstring: the west edge is the avenue on to Okayama.

### Config and the world file (by hand, then the tools)

- `../devhouse.world`: `gamev2/tiled/okayama.tmj` at x -16512, y 4288, 2816x2560 (cell (-258, 67)).
- `config.json`: `cities.KansaiCity.rooms` gains `{"room": "Okayama", "x": -258, "y": 67}` after Himeji;
  `places.Okayama = {"geo": [133.92, 34.66], "label": "Okayama", "minor": true}`.

### `tools/districts.py`, `tools/blog_to_npc.py`

```python
'Okayama': [
    d('castle', 'Okayama Castle',
      'the black "crow" castle on its stone wall above the river: the keep, the gravel terrace, pines and lanterns',
      (13, 2, 40, 14), stand=(22, 10)),
    d('momotaro', 'Momotaro Avenue',
      'the avenue in from Himeji and the plaza it ends in: the Momotaro statue and a stall of Bizen ware',
      (5, 15, 40, 23), stand=(14, 22)),
    d('korakuen', 'Korakuen garden',
      'the strolling garden on its island in the river, over the Tsukimi bridge: lawns, a pond, red-crowned cranes',
      (7, 27, 38, 35), stand=(22, 28)),
],
```

`LANDMARKS`, beside Himeji's rows:

```python
('okayama-keep_', 'Okayama Castle', (2, 7), {'rooms': ('Okayama',)}),         # (20, 9): in front of the keep, off the steps' columns
('okayama-crane_', 'Korakuen garden', (-1, 1), {'rooms': ('Okayama',)}),      # (27, 31): the lawn beside the first crane
('okayama-momotaro_', 'the Momotaro statue', (0, 3), {'rooms': ('Okayama',)}),    # (8, 20)
('okayama-bizen-stall_', 'the Bizen-ware stall', (1, 3), {'rooms': ('Okayama',)}),  # (16, 18)
```

`districts.py` then gives `korakuen.spots = ['Korakuen garden', 'the pond']`: the generic pond label
anchors on the first `pond-autotile_corner-nw` in `"x,y"` string order, which is the garden's pond
(`"14,31"`), not the river's corner (`"5,24"`). Keep the garden pond's x0 between 10 and 43.

### `src/utils/Interactions.js`

Four `flavour` rows with `footprint: true`, beside the Kansai row (order among them does not matter):

| kind | pattern | say |
|---|---|---|
| `fingerpost` | `/^okayama-fingerpost/` | `west: okayama, the black castle and korakuen. east: himeji castle, then osaka` |
| `momotaro` | `/^okayama-momotaro/` | `momotaro the peach boy, with his dog, monkey and pheasant. the ogres never stood a chance` |
| `bizen-stall` | `/^okayama-bizen-stall/` | `bizen ware: no glaze, two weeks in the kiln, no two alike. beer tastes better from it, they say` |
| `crane` | `/^okayama-crane/` | `a red-crowned crane. it looks at you, then at the pond, and chooses the pond` |

### Other tools

- `tools/check_generators.py`: `GENERATORS += ['generate_okayama']` after `generate_himeji`.
- `tools/check_distinct.py`: add `okayama-` to `LANDMARK_ART`. Do not run `--update`. The blockout measured
  Kansai at 0.11 / 0.38 / 37% (from 0.12 / 0.41 / 27%), no city worse than the baseline.

### Build order

```bash
cd gamev2                                   # art tools need Pillow: a venv with tools/requirements-art.txt
python3 tools/generate_kansai_art.py --preview /tmp/kansai.png
python3 tools/make_prefabs.py
python3 tools/generate_okayama.py           # after the devhouse.world and config.json edits above
python3 tools/generate_himeji.py
python3 tools/sync_cities.py
python3 tools/districts.py
python3 tools/blog_to_npc.py --rehome Damian 2025-11-12 "Okayama · Korakuen garden" --dry-run   # expect (27, 31); then without --dry-run
python3 tools/config_to_tiled.py Okayama Himeji
python3 tools/make_worldmap.py
node tools/play.js lint Okayama && node tools/play.js lint Himeji && node tools/play.js lint KansaiCity
node tools/play.js render Okayama /tmp/okayama.png    # and look at it, and at KansaiCity's seam
python3 tools/check_distinct.py
```

`--rehome` takes the state off `FukuokaStation` and re-times Damian's presence in Himeji and Osaka on the
days after; nothing else is edited by hand.

### Docs (same commit)

`docs/landmarks-and-towns.md` (the landmark table, the districts table, "Kansai": Okayama's paragraph,
`BUILT`, the city is 138x46, the second seam and its fingerposts, build order), `docs/stitched-city.md`
(three districts), `docs/blog-pipeline.md` (745 moved from `FukuokaStation · the platform` to
`Okayama · Korakuen garden`), `docs/trips-and-dates.md` (the start rooms below), `docs/hud-input-touch.md`
(the small places: Himeji, Karuizawa, Okayama), `docs/trains-and-stations.md` (Okayama has no station
either), `docs/generators-and-checks.md` (Kansai's distinctness figures as measured).

## Data and interfaces

- `config.json`: `rooms.Okayama` (new), `rooms.Himeji` (west edge, ten seams, a second fingerpost),
  `cities.KansaiCity.rooms` (+ Okayama), `places.Okayama`, `districts.Okayama` (three),
  `game.lookUp.sprites['okayama-keep'] = 0`, `spriteMetadata` / `tileNames` / `tilePalette` (appended only)
  for the seven sprites; Damian's 2025-11-12 state moves from `FukuokaStation` to `Okayama` (27,31).
- `../devhouse.world`: one map added, none moved. `tiled/okayama.tmj` and seven `tiled/prefabs/*.tmj` new;
  `tiled/himeji.tmj` and `assets/map/*` rebuilt.
- No new source file, no script-list change, no localStorage, no API.
- Start rooms, measured over every trip, lead-in and content day and every cast member: only 2025-11-12
  changes. As Bailey it is `Fukuoka` (30,10), as Julia `Fukuoka` (9,35) (both were `FukuokaStation` 3,7:
  Damian no longer makes the platform a majority). With no character chosen it is `Fukuoka`, as before.

## Tests

`tools/tests/kansai.test.js`:

- `DISTRICTS = ['Himeji', 'Okayama', 'Osaka']`; HUD names likewise; `unbuilt` is `['LakeBiwa', 'Nara']`.
- Seams: 20 pairs; `seams('Himeji')` is the east five then `H_AVENUE.map((y) => [0, y])`;
  `seams('Okayama')` is `[43, y]`. Replace "Himeji's west edge is open" with: `edgeOpen('Okayama')` equals
  its five seam cells (so none on x = 0, y = 0 or y = 39).
- The walk: the city is `[AT.Osaka[0] + SIZE.Osaka[0], SIZE.Osaka[1]]` (138x46, `depthScale` 1); the track
  is `AT.Osaka[0]` (88) cells, `x < AT.Osaka[0]`, `y === 4`. Add the stops Okayama (20,9) and Okayama
  (27,32) between Koko-en and Osaka. With `?stitch=0` the helper must take the nearest seam *into the next
  district on the way* and repeat until it is in the stop's room (Osaka to Okayama is two fades). Expected
  `[fades, crossings]`: stitched `[0, 4]`, `?stitch=0` `[4, 0]`.
- Fingerposts: one row per seam side: Osaka x 0 and Himeji x 43 with `kansai-fingerpost_0_0` and the #255
  line; Himeji x 0 and Okayama x 43 with `okayama-fingerpost_0_0` and the new line; each room has exactly
  one of each key it should have. Himeji's transporters all lead to Osaka or Okayama, hidden.
- New, Okayama: (1) the keep is at (18,2), its PNG 512x448, no cell of (18..25, 2..8) walkable; the wall
  (13..40, 13..14) is crossed at columns 21-22 only; `lookUp.sprites['okayama-keep'] === 0` and
  `LandmarkView.aim` gives weight 1 from (20,9) and its walkable neighbours in both views, the whole keep
  on desktop (the Himeji test's shape); the four `LANDMARKS` rows are in `blog_to_npc.py`. (2) Korakuen:
  every cell of the ring is `pond-autotile`, the only ones not solid are `21,24 … 22,26`; (9,28), (36,34)
  and (22,27) are walkable from Osaka; `districts.Okayama` keys are `castle, korakuen, momotaro`, `the
  pond` is a spot of `korakuen` only; no `waterways`. (3) Damian on 2025-11-12: present in Okayama with
  post 745 and four lines, on the island, reachable, not on a seam, that day only, and in no other room
  (the `madeup-towns.test.js` shape). (4) the statue, the stall and a crane each answer a bump with their
  line; no station names Okayama, no `train-track`, Hokuriku art or bin; `places.Okayama` is exactly the
  entry above and west of Himeji's.

Other files:

- `tools/tests/japan-map.test.js`: drop `Okayama` from `SMALL` and `KANSAI` (`LANDING` lengths `[1, 2]`);
  add `Okayama` to the label list, to the minor places (`['Himeji', 'Karuizawa', 'Okayama']`, both
  assertions) and to the places with no station; `P.arrival(config, 'Okayama')` is
  `{ room: 'Okayama', x: 40, y: 18 }`.
- `tools/tests/madeup-towns.test.js`: `room('2025-11-12', 'bailey')` is `'Fukuoka'`; add the same for
  `'julia'`. The "platform still wins a majority" case keeps `room('2025-10-20') === 'TokyoStation'`.
- `tools/test_blog_to_npc.py`: `REPLACED_219[('Damian', '2025-11-12')] = ('Okayama', (27, 31))`. Nothing
  else in it failed in the blockout (`test_spots` and `test_districts` cover the new rows).
- `tools/tests/map-data.test.js` and the world-map assertions pass once `make_worldmap.py` has run.

Run, from `gamev2/` (all must pass):

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # with Pillow, so the art tools are covered
python3 tools/sync_cities.py --check
python3 tools/rehearse_blog.py         # blog_to_npc.py changed
```

then the browser regression (`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in the container).

**Play it** (desktop 1280x800 and a phone, 390x844 portrait and a landscape one; `?notitle=1&nointro=1`,
`&date=2025-11-12`): walk from Osaka through Himeji into Okayama with no fade and nothing changing at the
seam; read both new fingerposts; up the steps, stand in front of the keep (the camera looks up, the whole
keep in view on desktop); bump the statue, the stall and a crane; over the Tsukimi bridge, round the
island, talk to Damian; try the west edge and the river banks (closed); the same walk with `&stitch=0`
(two fades each way). Open the Map at 320x780 and 390x844: Okayama's dot and label are drawn and no town's
label is hidden. Start `&date=2025-11-12` as Bailey and as Julia: the game opens in Fukuoka. Look at the
screenshots; save them to `/work/media/`.

## Risks and open questions

- **The keep is the district.** It is the only new landmark-sized drawing, and it must not read as
  Himeji's keep painted black: black boards, a broader and lower outline, gold on the ridge. If it does
  not read on a phone, fix the art, not the map.
- **The bank rocks** are a patch over a missing autotile piece. If they look stuck on in the browser, the
  fallback is four pines planted over the corners; do not leave the notch.
- **Himeji's trees move a little.** Opening the west edge changes what the seeded woods draw after it.
  The Himeji and Koko-en tests passed unchanged in the blockout, with Damian still at (12,8).
- **The walk is long**: Korakuen is about 100 cells from the middle of Osaka. Accepted in #68's plan.
- **Rooms touched** (map data is serial): Okayama (new), Himeji (west edge), `KansaiCity`,
  `../devhouse.world`; `FukuokaStation` loses one dated NPC state and no tile. Nara (#268) and Lake Biwa
  (#269) rebuild Osaka's edges and `kansai.py` after this: land this first.
- No open question for the owner.
