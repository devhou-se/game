# Kansai: Osaka becomes a stitched city, with Himeji walked to from it (#255; #68, run 2)

## Context

Osaka is a standalone room reached only by train. Damian's post of 13 Nov 2025 (754, Himeji Castle) stands
in Osaka because Himeji does not exist. #68's plan (`docs/workshop/68-…md` on branch
`origin/workshop/68-featured-locations-everywhere-else-anyon`, "Plan for the later tickets") makes Kansai
a third stitched city of five districts, one ticket each. This ticket is the first: the city itself, and
Himeji, a 44x40 outdoor district west of Osaka that you walk into along Osaka's Canal-side Avenue, with
the castle moat carried on from Osaka's canal. Outcome: `KansaiCity` (Osaka + Himeji) is one walkable room,
Damian's post stands in front of the keep, and the world file has room for Okayama, Nara and Lake Biwa later.

Owner's rules: a walkable place, not a train stop; only real places (the keep, the moat, the gate, Koko-en);
no ordinary sealed buildings; no rubbish bins; Himeji's west edge stays closed until Okayama is built.

**Step 0, before anything else.** The ticket needs #68's code stage: `Places` `minor` (a small place's
label is laid out after the towns'; every label is still drawn: #68's review took `optional` and `hidden`
out) and `AmbientBoats.joinRuns`. On `origin/master` at `ef4f6ead` **neither exists**, on no remote branch
either (the #68 branch holds only its design), although the ticket's sizing comment says they have landed.
A copy of master with this design built on it shows both are needed: with `places.Himeji` the Map label
test fails ("portrait phone, narrowest view … 5 of 12 dashes are left"), and the canal is two runs that
meet at the seam, so a boat fades out in mid-water there. On the branch as Workshop hands it over (merge
the local `origin/master` first: the branch is behind it), run

```bash
grep -n joinRuns gamev2/src/AmbientBoats.js; grep -n minor gamev2/src/utils/Places.js
grep -n "small(\|MAY_TOUCH" gamev2/tools/tests/japan-map.test.js; grep -n joinRuns gamev2/tools/tests/roads-waterways.test.js
```

All four must print something (the last two are #68's tests, which this ticket's tests lean on). If any
is silent, stop and return `needs_info` with this question: "#68's code stage (`Places` `minor`,
`AmbientBoats.joinRuns`) is not on master. Merge it and run this again, or should this ticket build those
two itself?" Do not write that code here unasked: it is #68's, with its own tests, and would collide with
it. If the owner answers "build it here", build exactly what "Changes" in #68's design says for `minor`
and `joinRuns`, with its tests, and nothing else of #68, as a first commit of its own.

## Approach

Hokuriku's pattern, exactly (`tools/hokuriku.py`, `generate_shirakawago.py`, `tools/tests/kanazawa.test.js`,
"Hokuriku" in `docs/landmarks-and-towns.md`): a layout module that owns where districts meet, one generator
per district, hidden seam transporters for `?stitch=0`, `CityStitcher` and every `src/` system unchanged
(one `Interactions` row is the only game-code change). The layout below was built as a blockout on a copy
of master (placeholder boxes for the new art): `play.js lint` is clean for `Osaka`, `Himeji` and
`KansaiCity` (94x46), `play.js check`, `check_generators.py` and `sync_cities.py --check` pass, the game
loads the city in Chromium with no console error, and `--rehome` puts Damian in Himeji by the keep.
`/work/media/255-*.png` show it. Keep the cells; the art and the dressing are the implementer's. The
design review built it a second time (see Review, at the end): what it found wrong is corrected below, and
what it confirmed is listed there, so none of that needs proving again.

Two departures from #68's sketch, both forced by the cells: (1) the moat is a **straight reach**, not a
ring: it must be on rows 14-16 to meet Osaka's canal, which leaves 14 rows north of it, and `pond-autotile`
has no inner corners; it ends in a rounded bank at x=6. (2) the castle hill is therefore two tiers of wall
rising from the north bank (a stone base, the white wall above it) with the gate built into them at the
bridgehead, and the keep on a gravel terrace above.

## Changes

All paths under `gamev2/` unless they start with `../`. Cells are district-local.

**`tools/kansai.py`** (new; docstring like `hokuriku.py`'s). `Kit` is imported from `hokuriku`.

```python
AT = {'Okayama': (0, 36), 'Himeji': (44, 36), 'Osaka': (88, 30), 'Nara': (138, 36), 'LakeBiwa': (152, 0)}
SIZE = {'Okayama': (44, 40), 'Himeji': (44, 40), 'Osaka': (50, 46), 'Nara': (52, 40), 'LakeBiwa': (46, 36)}
CITY, IN = 'KansaiCity', 3
BUILT = ('Himeji', 'Osaka')                  # each later ticket adds its district
O_AVENUE = (24, 25, 26, 27, 28); H_AVENUE = (18, 19, 20, 21, 22)   # derived: y + AT['Osaka'][1] - AT['Himeji'][1]
O_CANAL = (20, 22);              H_MOAT = (14, 16)                 # first and last row, derived the same way
JOINS = [('Osaka', 'w', O_AVENUE, 'Himeji', H_AVENUE)]             # (district, side, its cells, neighbour, its cells)
def is_open(district, side): ...  # True when a JOINS row touches that side (from either end: the neighbour's
                                  # side is the opposite one) and both its ends are in BUILT
def seams(district): ...          # hidden rg.transporter rows, only for joins with both ends in BUILT
```

Write `AT = {` and `SIZE = {` with single spaces, each on one line: the test reads them as text, as
`kanazawa.test.js` reads `hokuriku.py`'s. The helper is `is_open`, not the `open` of #68's plan, which
would replace Python's builtin `open` inside the module.

`seams('Osaka')` = (0, y) → Himeji (40, y-6) for y 24..28; `seams('Himeji')` = (43, y) → Osaka (3, y+6) for
y 18..22. `AT` holds all five so later tickets move nothing; world cell = `AT` + (-258, 31).

**`tools/generate_kansai_art.py`** (new; the shape of `generate_hokuriku_art.py`: `SPRITES`, `FLAT`,
`LOOK_UP`, `--preview`, writes `assets/sprites/*.png`, `spriteMetadata`, `tileNames`, `game.lookUp.sprites`)
and matching **`tools/make_prefabs.py`** `PREFABS` rows. Shaded pixel art in the Hokuriku sprites' style;
this is most of the ticket's work. Art stays inside its footprint; the turret, the two gates and the
fingerpost may overhang upward by up to a cell, the keep may not (it stands on the district's top row: an
overhang is cut off in `?stitch=0` and reaches toward the passing train's row in the city).

| Sprite | Cells | Layer | Prefab colliders | What |
|---|---|---|---|---|
| `himeji-keep` | 10x8 | Collidables | rows 2-7, all columns | the white main keep on its stone base, the small keep joined to it; `LOOK_UP` 0. The roofs fill footprint rows 0-1. A portrait phone shows 7 columns of it at a time: the main keep's tiers go in the middle columns, the small keep at one end |
| `himeji-turret` | 3x4 | Collidables | rows 1-3 | a white corner turret |
| `himeji-gate` | 6x4 | Collidables | columns 0,1,4,5, all rows | the gatehouse over the bridgehead; you walk through columns 2-3 (the `kanazawa-ishikawa-gate` recipe) |
| `himeji-bridge` | 2x4 | Non-Collidables, `FLAT` -200 | none | a flat deck you walk on (the `shirakawa-bridge` recipe); also Koko-en's pond bridge |
| `himeji-kokoen-gate` | 4x3 | Collidables | columns 0,3, rows 1-2 | the garden's roofed gate; you walk through columns 1-2 |
| `himeji-wall` | 1x2 | Collidables | both cells | one column of the castle's white plaster wall: tiled coping, a loophole, a stone footing; repeats sideways with no seam and fills both cells (no ground shows through) |
| `kansai-fingerpost` | 1x2 | Collidables | (0,1) | a wooden fingerpost, arms west and east |

**`tools/generate_himeji.py`** (new; header and ending as `generate_shirakawago.py`: `k.dress(); b.finish();
b.room('Himeji', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, ks.seams('Himeji')))`, then
`waterways`, `rg.save_config`). On `b.fill('grass-autotile')`:

- **Avenue**: `flat-grey-brick-autotile` on `rect(5,18,43,22)`, then Floor (43,18) → `_edge-n` and (43,22) →
  `_edge-s` (no rounded corner at the seam); `k.road_h(6, 43, 19, cap_w=True)` (road rows 19-21). West of
  x=5 it is closed while `not ks.is_open('Himeji','w')`: (4,18..22) solid, wood on x 0-4.
- **Moat**: Water rows 14-16, x 6..43, `pond-autotile` `edge-n` / `center` / `edge-s` (x=6:
  `corner-nw` / `edge-w` / `corner-sw`), solid except columns 32-33. `himeji-bridge` at (32,14); gravel on
  (32..33,17). `waterways = [{'axis':'h','row':14,'rows':3,'from':7,'to':43,'under':[[32,33]]}]`: `from` is
  7, not 6, because `AmbientBoats.declaredRuns` measures the band on the first cell and the bank column
  gives none (the run is dropped). With that it has Osaka's band and abuts Osaka's run, so `joinRuns` makes
  one run from the moat's west end to Osaka's east edge.
- **Walls and gate**: for x 6..41 except 30..35, the upper tier is `b.stamp('himeji-wall', x, 10)` (rows
  10-11, both solid) and the lower `b.wall_stone(x,12)` (the stone base, rows 12-13); `himeji-gate` at
  (30,10); columns 32-33, rows 10-13 paved, `b.stairs` on rows 10-12. The gateway is the only way up. The
  upper tier is Himeji's own white wall because two tiers of `castle-wall-siding` over gravel with steps,
  pines and lanterns is Sendai's Aoba Castle ruin, cell for cell (`generate_sendai.py`), and in the
  blockout it read as two fences with a strip of lawn between
  (`/work/media/255-review-no-lookup-beside-keep.png`).
- **Terrace**: `gravel-autotile` on `rect(6,8,41,13) + rect(18,2,41,7)`, laid before the walls and the
  paving, so the ground under and between the tiers is the terrace's and nothing green shows there;
  `himeji-keep` at (8,0), its whole footprint solid; `himeji-turret` at (38,3), solid; pines and
  `sendai-stone-lantern`s, none on (9..16, 8..9) (Damian's cell and the cells beside it); solid wood
  behind and to the west (rows 0-1; x 4-7 beside the keep on rows 2-7; x 4-5 from there down to row 13).
- **Koko-en**: `k.wall(5,19,24); k.wall(24,41,24)` (the earthen wall) with `himeji-kokoen-gate` at (20,23);
  gravel entry `rect(21,24,22,26)` and loop `rect(8,27,38,28) + rect(8,27,9,35) + rect(8,34,38,35) +
  rect(37,27,38,35)`; `b.pond(13,31,33)` with `himeji-bridge` at (22,30) and the pond's colliders removed on
  (22..23,31..32); lanterns, pines, maples; solid wood round it (x 5-6 and 40-41, rows 26-35; rows 36-39).
- **Fingerpost**: `kansai-fingerpost` at (39,22) (feet on (39,23), beside the pavement).
- **East edge**: closed off the avenue and the moat (hedge or wood on x 42-43, `shrub-small` on rows 17 and
  23); Osaka's own hedge is the next two columns, so look at the stitched render and thin it if it reads as
  a wall of shrubs.
- Trees and props only from the shared kit (`sendai-pine`, `sendai-maple`, `sendai-cedar`,
  `sendai-stone-lantern`, `shrub-*`) or Kansai's own. **Nothing that only another city uses**
  (`hokuriku-*`, `kanazawa-*`, `shirakawa-*`, `toyama-*`): the blockout made Hokuriku fail `check_distinct`
  with one ginkgo. No `train-track*`, no `road-plain` / `road-div-vertical` / `road-edge-bottom` on an edge
  cell beside void, no building with a door, no bin.

**`tools/generate_osaka.py`**: `import kansai as ks`; before `b.finish()`:
`b.put('Floor', 0, 24, 'flat-grey-brick-autotile_edge-n')`, `b.put('Floor', 0, 28, '…_edge-s')` (corner
tiles today), `b.stamp('kansai-fingerpost', 2, 28)`; the room's `transporters=[…] + ks.seams('Osaka')`
(run twice, the config does not change: `keep_house_doors` puts the kept doors back in their order).
**The railway's west end loses its caps**: today `for y in (3, 4, 5): b.stamp('shrub-small', 0, y);
b.stamp('shrub-small', W - 1, y)` closes both ends of the corridor; with the rail carried on west by the
city's backdrop, the three at x=0 are bushes standing on the line in mid-city, which the train drives
through (`/work/media/255-review-osaka-west-track-caps-before.png`, `…-after.png`). Stamp the west three
only `if not ks.is_open('Osaka', 'w')`; the east three stay until Nara. Tried: lint stays clean and no new
edge cell can be reached (the fences on rows 2 and 6 still close the corridor). Nothing else in Osaka
moves; its east avenue end stays as it is.

**`src/utils/Interactions.js`**: one flavour row beside the other signs:
`{ kind: 'fingerpost', group: 'flavour', pattern: /^kansai-fingerpost/, footprint: true, say: 'west: himeji castle and koko-en. east: osaka, dotonbori' }`.

**`../devhouse.world`** (pixels = cells x 64; keep the file's formatting): `osaka.tmj` x -10880, y 3904
(cell -170,61; was -102,61); new `himeji.tmj` x -13696, y 4288, width 2816, height 2560 (cell -214,67);
`fukuoka.tmj` x -21120, y 5760 (cell -330,90; was -175,85: it would overlap Osaka's new place).

**`config.json`** (by hand, then the tools): `cities.KansaiCity = { name: 'Kansai', backdrop: <a copy of
HokurikuCity's>, rooms: [{room:'Osaka'}, {room:'Himeji'}] }` with x/y written by `sync_cities.py`;
`places.Himeji = { geo: [134.69, 34.82], label: 'Himeji', minor: true }`. Palette entries are appended by
the tools only.

**`tools/districts.py`**: `'Himeji': [d('castle', 'Himeji Castle', 'the white castle on its hill: the keep,
the stone walls, the gate and the bridge over the moat', (6,2,41,13), stand=(22,8)), d('kokoen', 'Koko-en
garden', 'the walled strolling garden beside the castle: its pond and bridge, lanterns, pines and maples',
(5,26,41,35), stand=(22,28))]`.
**`tools/blog_to_npc.py`** `LANDMARKS`: `('himeji-keep_', 'Himeji Castle', (4, 8), {'rooms': ('Himeji',)})`,
`('himeji-kokoen-gate_', 'Koko-en garden', (1, 5), {'rooms': ('Himeji',)})`. The keep's stand is (4, 8)
from its corner, Himeji (12,8): on the terrace's first row, in front of the keep's middle. Not (11, 8),
the first draft's: that is (19,8), two columns east of the keep, where the camera does not look up at all
(measured in Chromium: 0 px at (20,8) and (20,9), where you stand to talk to him; 120-184 px on desktop and
146-210 px on a phone at (12,8) and (12,9); `/work/media/255-review-lookup-in-front-of-keep.png`,
`…-no-lookup-beside-keep.png`). `game.lookUp` reaches 2 columns either side of a landmark and 3 rows south.
**`tools/check_generators.py`**: `GENERATORS += ['generate_himeji']` (before `districts`),
`ART_TOOLS += ['generate_kansai_art']`. **`tools/check_distinct.py`**: `himeji-|kansai-` in `LANDMARK_ART`.

**Build order** (from `gamev2/`; art tools with a Pillow python): `generate_kansai_art.py`,
`make_prefabs.py`, `generate_himeji.py`, `generate_osaka.py`, the world file and the two config entries,
`sync_cities.py`, `districts.py`, `blog_to_npc.py --rehome Damian 2025-11-13 "Himeji · Himeji Castle"`
(`--dry-run` first; expect "Osaka (17,35) -> Himeji · Himeji Castle (12, 8)", a hidden base def in Himeji,
absent from 2025-11-14, Osaka restored from then), `config_to_tiled.py Osaka Himeji`, `play.js lint` and
`render` for `Osaka`, `Himeji`, `KansaiCity`, `make_worldmap.py`, then `check_distinct.py` **before**
`--update`: it must say no city is worse and that Kansai is not in the baseline; compare Kansai with
Osaka's row (buildings 0.2, sprites 0.451, own 0.107) by hand. Only then `--update`, once. It rewrites
every city's row, because each is measured against the others and Kansai is new among them (on the review
build Fukuoka's, SanFranbourne's, Sapporo's and Tokyo's rows moved as well, all for the better). In that
diff: the key `Osaka` becomes `Kansai`, and no other city's buildings or sprites number goes up nor its
own-art share down. If one does, a Himeji sprite is one that city relies on: take it out, do not accept it.

**Docs, same commit**: `landmarks-and-towns.md` (a "Kansai" section like Hokuriku's: layout, seams, `BUILT`,
build order; the landmark and district tables; Osaka no longer "detached"), `stitched-city.md` (the third
city), `ambient-traffic.md` (the canal runs on as the moat, why `from` is 7), `trains-and-stations.md`
(Himeji is walked to from Osaka, not on the board), `hud-input-touch.md` (Himeji is a `minor` dot),
`generators-and-checks.md` (the baseline line), `blog-pipeline.md` (its re-homing history still says
Himeji 754 stands in at Osaka's sakura trees until the town exists: Himeji now does; Nara's stand-in stays).
No browser check is added (see Review 12), so `tools/browser/README.md` does not change.

## Data and interfaces

- New room `Himeji` (name `Himeji`, 44x40, `waterways` as above, five hidden seam transporters); Osaka gains
  five. New `cities.KansaiCity`; runtime room for both is `KansaiCity`, coordinates stay district-local.
- New `places.Himeji` (`minor`). No station, so `Places.arrival(config, 'Himeji')` is `{room:'Himeji', x:40, y:18}`.
- Seven sprites, seven prefabs, their `spriteMetadata` / `tileNames`, `game.lookUp.sprites['himeji-keep'] = 0`.
- `config.districts.Himeji` (two), two `LANDMARKS` labels, one `Interactions` rule. No save-data change.

## Tests

- **New `tools/tests/kansai.test.js`**, mirroring `kanazawa.test.js`: `cities.KansaiCity.rooms` are exactly
  `kansai.py`'s `BUILT` (read from its text, like `AT` and `SIZE`: plain literals), their offsets and sizes
  equal `AT` / `SIZE`, and every one sits in `devhouse.world` at `AT` + the same offset, (-258, 31); the
  city is clear of every other map in `devhouse.world` and on the world map, **and so is the rectangle of
  each district not built yet** (`AT` / `SIZE` of Okayama, Nara, LakeBiwa at that offset: the room this
  ticket is to leave for them, which nothing else checks); every seam cell is a hidden,
  non-solid transporter landing `IN` cells inside the neighbour, with one back; the same Floor tile name on
  both sides of each seam cell, and the same Water tile on rows 20-22 / 14-16; in each district the only
  reachable edge cells are seam cells, plus Osaka's east avenue end (49, 24..28), where a step out does not
  move the player; Himeji's west edge has no reachable cell; the declared `waterways` of the two districts,
  placed and passed through `AmbientBoats.joinRuns`, are one run; no `train-track*` tile in Himeji and the
  train's row is Osaka's; a walk from Osaka (3,26) to the keep terrace and into Koko-en, stitched and with
  `--stitch=0`; depth scale 1; Damian on 2025-11-13 is in Himeji on a reachable outdoor cell that is not a
  seam, **in front of the keep** (the row under its footprint or the next, inside its columns: 9..16,
  8..9), where `LandmarkView` looks up in full for him and for whoever stands beside him to talk; a
  `kansai-fingerpost` within 4 cells of each seam and its bump says its line; no sprite in Himeji
  whose family starts `hokuriku-`, `kanazawa-`, `shirakawa-` or `toyama-`; no `shrub-*` on Osaka's cells
  (0, 3..5) while the west join is open, and `train-track` on (0,4); `himeji-keep`'s PNG is exactly 640x512
  (its header, as `airports.test.js` reads one); `config.districts.Himeji`'s `kokoen` lists `the pond` in its `spots` and
  `castle` does not (the moat's bank tile at (6,14) is the same `pond-autotile_corner-nw` the pond's label
  looks for: the label must land on the garden's pond, not the moat).
- **Existing tests that change** (each failed on the blockout): `dates-trips.test.js`
  `where('2025-11-13').Damian` `'Osaka 17,35'` → the cell `--rehome` chose (`'Himeji 12,8'` on the review build);
  `japan-map.test.js`: `'Himeji'` joins the label list and the places with no station (with the arrival
  above pinned) and leaves the `small(…)` stubs #68 added; `kanazawa.test.js` "both cities are stitched":
  2 → 3; `test_blog_to_npc.py` `test_city_reach`: `city_districts(cfg, 'Osaka') is None` → use `'Sendai'`;
  `distinct_baseline.json` via `--update` (`test_distinct` wants its keys to be the measured cities). On the
  review build these and `test_districts` (it wants `districts.py` to know Himeji) were the only failures.
- **Tests that would pass but no longer mean what they say**: they use `Osaka` as "a town that is not
  stitched". `occlusion-camera.test.js`: in the `Interactions.index` list `'Osaka'` → `'KansaiCity',
  'Sendai'` (Osaka's bumps where they are now played, and a standalone town), in the `loadFloorTiles` list
  `'Osaka'` → `'Sendai'`; `stitched-city.test.js`: `keepsIndex(rm.rooms.Osaka, false)` → `rm.rooms.Sendai`.
  Its `?stitch=0` list (`['Osaka', 20, 20]`) is right as it is. All three substitutions pass on the review build.
- **Run** (all must pass): `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
  `node tools/play.js check`, `python3 tools/check_generators.py` (Pillow python), `python3 tools/sync_cities.py
  --check`, `python3 tools/check_distinct.py`, `python3 tools/rehearse_blog.py`, and the browser regression
  (`tools/browser/README.md`; its `seam-stitched` / `seam-unstitched` and `menu-map` checks are generic and
  must pass with three cities).
- **Play it** (Playwright, desktop 1280x800 and a 390x844 phone with `?touch=1`, `?date=2025-11-13`, real
  keys and the d-pad, screenshots looked at; press Escape past the character creator first, or it covers
  every shot). The browser regression walks one seam, the boot city's, so **this is the only place Kansai's
  seam is walked in a browser**: script it and assert, do not only look. From Osaka (3,26) hold left to
  Himeji (38,20): the room stays `KansaiCity`, no switch and no fade on the way, the HUD's name changes
  from Osaka to Himeji, and back again; the same with `?stitch=0`, where each crossing is one fade landing
  3 cells inside. Then: arrive at Osaka Station by train and walk it; bump both fingerposts; cross the
  bridge, through the gate, up the steps, talk to Damian in front of the keep, and the whole keep is in view
  top to bottom on desktop and its roof on the phone (the camera looks up); walk Koko-en's loop and over its
  bridge; fish in the moat; wait for a boat to pass the seam without fading and for a train to pass above
  Himeji (it runs two rows above the keep's roof: neither may cover the other); take a turn on Osaka's
  wheel (its first run inside a stitched city); open the Map: Himeji's dot and its label, drawn on every
  size, and a click on it from the debug Map lands on Himeji (40,18); ride Kanazawa → Osaka and Osaka →
  Hakata once and look at which way the train leaves (the world-file move flips Kanazawa-Osaka; it is now
  the right way round).

## Risks and open questions

- **The prerequisite has not landed** (step 0; still so at `ef4f6ead`). The ticket says it has. If the
  owner would rather fold #68's code stage into this ticket, that is their call; it makes this ticket
  larger than L. There is no honest way round it: without `joinRuns` a boat vanishes in mid-canal at the
  seam, without `minor` the Map's label test fails, and the ticket asks for both by name.
- **Map data is serial**: this rebuilds `Osaka`, adds `Himeji`, moves `Osaka` and `Fukuoka` in
  `devhouse.world`, and touches `config.json` cities, places, palette and `tiled/`. It must not run beside
  #256 (Karuizawa) or #219's Osaka rebuild; a later Osaka redesign must keep rows 20-22 (canal) and 24-28
  (avenue) at the west edge.
- **The art is the bulk and the risk.** The blockout proves cells, not looks: the keep must read as Himeji
  (white, tiered) at 10x8, and the walls as a castle hill rather than two fences. Check tall sprites against
  `docs/occlusion.md` (Damian's cell is in front of the keep, not behind it).
- Distinctness on the blockout: Kansai 0.17 / 0.41 / 26% against Osaka's 0.2 / 0.451 / 10.7%, better on all
  three; real art should not worsen it. `--update` rewrites every city's row, so read the diff (Build order
  says what it may and may not show).
- The moat's west end is closed, so a boat fades in and out there, in open water beside the bank: that is
  what `AmbientBoats` does at any closed end. Look at it; if it reads badly, the cure is dressing (a
  landing stage on the north bank at x 7-9 for it to come from), not code.
- The 6-row void north of Himeji is the stitcher's wood with Osaka's track carried west across it
  (`backdrop.extend`); the train enters from the city's west edge. Nothing to build, but look at it.
- Open, for the owner only if they care: the fingerpost's line names Dotonbori; the moat is a reach rather
  than a ring (see Approach).

## Review

Design adversary, on `origin/master` at `ef4f6ead`. The design was built a second time on a scratch copy
(placeholder art, nothing committed): `kansai.py`, `generate_himeji.py` to the cells above, the Osaka edits,
the world-file moves, the config entries, the districts, the re-home and the baseline. Pictures:
`/work/media/255-review-*.png`.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **Step 0 describes an interface #68 no longer has** (`minor` / `optional` / `hidden`), and Play it allows Himeji's label to be "left out on the narrowest phone". #68's review removed `optional` and `hidden`: every label is drawn. Step 0 also greps only the two source files, not #68's test helpers (`small(…)`, `MAY_TOUCH`, the `joinRuns` test) that this ticket's tests are told to use, and names an old master. | Step 0 says what `minor` is, greps the two tests as well, names `ef4f6ead`, and gives the question to return. Play it expects the label on every size. | Yes |
| 2 | **The prerequisite is still missing**, on master and on every remote branch, and the ticket's sizing comment says it has landed. The implement stage will stop at step 0. | Looked for a way to do without it: there is none that keeps the ticket (a boat would vanish in mid-canal; the label test fails; the ticket names both). Step 0 now also says what to build if the owner answers "do it here", so that answer needs no new design. Whether to do so stays the owner's call. | Yes (the gate stays) |
| 3 | **Damian stands where the camera does not look up.** The stand `(11, 8)` is Himeji (19,8), two columns east of the keep. Measured in Chromium: beside him at (20,8) / (20,9) the look-up is 0 px and the keep's top is off screen; Play it expects "the camera looks up at it". | Stand `(4, 8)`: Himeji (12,8), in front of the keep's middle, where the look-up is full on desktop and phone (`--rehome --dry-run` confirms the cell). A test pins him in front of the keep; the terrace keeps props off the cells round him. | Yes |
| 4 | **"Nothing else in Osaka moves" leaves three bushes on the railway.** Osaka caps both ends of its rail corridor with `shrub-small`; once the backdrop carries the rail west, the west three stand on the line inside the city and the train drives through them. Kanazawa's open end has no caps. | The west caps are stamped only while `not ks.is_open('Osaka','w')`. Tried: lint clean, no new reachable edge cell. A test checks it. | Yes |
| 5 | **The baseline instruction cannot be followed.** "`--update` … no other city's numbers may change in that diff": they do, every time a city is added (four other rows moved on the review build), as the design's own Risks say. An implementer who obeys it is stuck; one who ignores it has no rule left. | Run `check_distinct.py` before `--update` (it must report no city worse); in the diff no other city may get worse. | Yes |
| 6 | **"Art stays inside its footprint except upward" for a keep on row 0.** An overhang leaves the district: cut off in `?stitch=0`, and in the city it reaches toward the rail two rows above. | The keep's PNG is exactly its 10x8 footprint, roofs in rows 0-1; a test reads the PNG's size. Smaller sprites may overhang a cell. | Yes |
| 7 | **The castle hill is Sendai's castle ruin.** Two tiers of `castle-wall-siding`, gravel, steps, pines and `sendai-stone-lantern` is `generate_sendai.py`'s Aoba Castle, and in the browser the tiers read as two fences with lawn between: the risk the design names and leaves to the implementer. | A seventh sprite, `himeji-wall` (the white plaster wall, 1x2, repeating), for the upper tier; the stone siding stays as the base; the terrace's gravel runs under and between the tiers. | Yes |
| 8 | **Three tests keep passing while losing their point**: they use `Osaka` as the town that is not stitched (`occlusion-camera.test.js` twice, `stitched-city.test.js` `keepsIndex`). | Use `Sendai` there, and `KansaiCity` beside it where Osaka's bumps were the reason. Tried: they pass. | Yes |
| 9 | **`kansai.test.js` does not test what the ticket promises for later**, nor several things the design relies on: that the unbuilt districts' places in `devhouse.world` are free; that `cities.KansaiCity.rooms` is `BUILT`; that "the pond" is the garden's and not the moat's bank (the same tile name; it comes out right today only by the order of two strings); the `AT = {` text the mirrored regex needs (the design's own block was written `AT   = {`, which it would not match). | All added to the test list; the block is written as the test reads it. | Yes |
| 10 | **Docs list misses `blog-pipeline.md`**, which says post 754 stands in at Osaka until Himeji exists. | Added. | Yes |
| 11 | **`def open(district, side)`** replaces the builtin inside `kansai.py`, and `JOINS` rows name only one side, so "the row on that side" is undefined for the neighbour. | `is_open`, looked up from either end of a join. A deliberate difference from the name in #68's plan. | Yes |
| 12 | **No browser check walks Kansai's seam.** `seam-stitched` walks one seam, the boot city's first. | Play it is now a scripted, asserted walk both ways, stitched and not. A per-city seam check in `regress.js` is **not** added: Hokuriku has none, the unit test walks the same cells in both modes, and the regression's run time is already a problem (#238). | In part |
| 13 | **A 10-column keep does not fit a portrait phone** (7 columns are in view; `/work/media/255-review-lookup-phone.png`). | No change of size: 10-column station fronts and the 12-column wheel are the precedent, and a smaller keep stops reading as Himeji. The art row now says where the main keep goes so the middle reads on its own. | Note only |
| 14 | **A boat appears from nowhere at the moat's closed west end.** | Existing behaviour at any closed end; no code. Listed under Risks with a dressing cure if it reads badly. | Note only |

Checked on the review build, not assumed (so the implementer need not prove them again):

- `node tools/test_game.js`: 401 pass on master; on the build the only failures are the ones listed under
  "Existing tests that change". `test_blog_to_npc.py` prints `ok` once its three are done
  (`test_city_reach`, `test_districts`, `test_distinct`).
  `play.js check`: no problems. `play.js lint`: clean for Osaka, Himeji, KansaiCity. `rehearse_blog.py`:
  313 of 313. `sync_cities.py --check`: ok. The game boots in Chromium with no console error, and was
  walked at 1280x800 and at 390x844 with touch (`/work/media/255-review-seam-phone.png`).
- The player's start room is the same on every trip day, for no player, Damian and Bailey: the re-home
  moves nobody's start.
- The rectangles of all five districts (built or not) are clear of every map in `devhouse.world` after the
  two moves. The seam's tiles match on both sides (pavement and water). The only edge cells that can be
  reached are the seam's and Osaka's east avenue end.
- `[…] + ks.seams('Osaka')` regenerates to the same config on a second run.
- The world map still lists Osaka, so the trains' direction (`TrainTravel.dirTo`) still has it.
- The moat can be fished: its tiles are the canal's `pond-autotile`, which `Interactions` already knows.

Outside this ticket, noticed and not changed: Bailey's post 769 of 2025-11-16 ("Okayama, Himeji, Osaka,
Tokyo") stays in Osaka; `roomgen.Builder.pond`'s docstring says there is no `edge-w` piece, and there is.
