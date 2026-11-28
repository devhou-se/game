# Himeji rebuilt to the Kansai plan: a climb (#275)

## Context

Himeji and Okayama are the same room twice (`gamev2/docs/landmarks-and-towns.md`, "Kansai: one plan for
Osaka, Himeji and Okayama", written by #274): castle band, avenue, garden band on the same rows, a gravel
terrace above one full-width wall with one way up, a garden that is a gravel loop round a two-row pond,
entered on columns 21-22. #275 is the first of three builds: **room `Himeji` only**, rebuilt to its part of
that plan ("Himeji (#275): a climb"). Okayama and Osaka are not touched; `tools/kansai.py`,
`devhouse.world` and `cities.KansaiCity` do not change.

Outcome: north of the moat the keep is earned by a hairpin through three sand courts (51 steps from the
bridge landing to the visitor's cell, 29 today); south of the avenue Koko-en is three walled rooms in a
row, entered at the Okayama end. Seams, moat, avenue, fingerposts, the keep, Damian's 13 Nov post at
(12,8) and both `LANDMARKS` rows stay exactly as they are.

## Approach

Rewrite `tools/generate_himeji.py` to the cells below and regenerate. Everything here was built as a
blockout in a scratch copy (pictures on the pull request), with the art, generator, districts and test
edits listed under Changes: the five checks pass there (486 unit tests), `play.js lint Himeji` and
`lint KansaiCity` give 0 errors and 0 warnings, and `check_distinct.py` gives Kansai 0.10 / 0.37 / 40%
(0.10 / 0.38 / 37% before; baseline 0.119 / 0.409 / 27.3%), so **`sand-autotile` is used as it is and no
court family is recoloured**. It was not played in a browser: that is the implementation's to do.

The plan's fixed cells are kept. Its targets north of the moat fit as written. Three targets in Koko-en
are shifted, as the plan allows a ticket's blockout to do:

1. **The partitions are a drawn wall, not tree lines.** In the blockout two-cell tree lines read as wood,
   not rooms (the risk #274 named, with this remedy). A north-south earthen wall, one cell thick, is
   drawn in `generate_kansai_art.py` (three `himeji-kokoen-wall-v*` sprites: Himeji's own art, no new
   `sendai-*` kind). The same wall closes the garden's west and east sides, in place of border trees.
2. **The rooms are therefore** A x 6..17, B x 19..30, C x 32..40 (plan: 7..16, 19..30, 33..40), rows
   26-37, walls on columns 5, 18, 31, 41. The openings stay on the plan's rows.
3. **Paths are stepping stones** (`b.paver`, the `pavers_*` set, one cell wide), not `k.paved`: grey
   brick is the avenue's pavement and made the garden read as street. Still "one cell, not gravel".

### North of the moat (unchanged unless said)

| What | Cells |
|---|---|
| Sand (`sand-autotile`, replaces `gravel-autotile` on the same cells) | (6..41, 8..13) + (18..41, 2..7) + (32..33, 14..17) |
| Moat, bridge `himeji-bridge` (32,14), white wall + stone base rows 10-13, gatehouse (30,10), gateway steps | as today |
| **Inner stone wall** (new): `b.wall_stone(x, 4)`, rows 4-5 | x 20..41 except 38, 39 |
| **Steps** (new): `k.paved` then `b.stairs` on each cell | (38..39, 4..5) |
| Keep `himeji-keep`, solid 10x8 | (8,0), as today |
| **Turret** `himeji-turret`, solid 3x4 | **(20,6)** (was (38,3)): rows 6-9 under the inner wall, down to the white wall |
| Pines (`k.trees('sendai-pine', ...)`, trunk cells) | (24,7), (27,9), (40,3) |
| Lanterns (`sendai-stone-lantern`, foot cells) | (36,7), (41,7), (6,9), (18,9) |

The walk: bridge (32..33, 14..17), gateway (32..33, 10..13), **Sannomaru** (23..41, 6..9), east to the
steps, **upper walk** (18..41, 2..3) back west, the **lane** (18..19, 2..7) down the keep's east flank,
**Honmaru** (6..19, 8..9). Nothing stands on (9..16, 8..9).

### South of the avenue: Koko-en

| What | Cells |
|---|---|
| Earthen wall `k.wall(x0, x1, 24)` (rows 24-25) | x 5..7 and 12..41 |
| Gate `himeji-kokoen-gate` 4x3 | **(8,23)** (was (20,23)); gateway `k.paved` (9..10, 24..25) |
| North-south walls, rows 26-37 | x = 5 and 41 unbroken; x = 18 open on rows 28-29; x = 31 open on rows 34-35 |
| Stepping stones `b.paver(x, y, i)`, `i` the running index | (10, 26..33), (11..24, 28), (24,29), (11..14, 33), (25,34), (26..36, 34), (36, 29..33) |
| Koi pond, `pond-autotile` on `Water`, 8x3 | (21..28, 30..32), solid except columns 24-25 |
| Timber bridge `himeji-bridge` 2x4 | (24,30): deck rows 30-33 |
| Pines (trunk cells) | A: (7,31), (14,31), (12,36), (15,27); B: (20,36), (28,28) |
| Maples `sendai-maple` (trunk cells), room C only | (33,29), (38,31), (33,37), (38,36), (38,27) |
| Lanterns (foot cells) | (8,27), (12,29), (15,33), (22,29), (29,33), (35,28) |

A north-south wall segment on column `x`, rows `y0..y1`, is: `himeji-kokoen-wall-v-end` (1x2) on
`(x, y1-1)`; `himeji-kokoen-wall-v` on every row above it; except that a segment starting below an
opening (`y0 > 26`) has `himeji-kokoen-wall-v-top` on its first row. Each is `b.prop` (on `Collidables`,
its footprint solid). The segments: x=5 and x=41 rows 26-37; x=18 rows 26-27 and 30-37; x=31 rows 26-33
and 36-37.

The pond is written by hand (three rows; `b.pond` makes two): role `corner-<n|s><w|e>` at the four
corners, `edge-<n|s|w|e>` on the sides, `center` inside. Its `corner-nw` is on "21,30", which sorts
before the moat bank's "6,14", so "the pond" stays the garden's.

### Edges

`AUTUMN` and `GARDEN` go; one list `PINES = ['sendai-pine', 'sendai-cedar', 'sendai-pine']` for every
`k.woods`: (0,0,7,7), (0,8,5,17), (0,24,4,39) [west open; the `else` branch keeps (0,18,4,39)],
(18,0,43,1), (42,2,43,13), (42,24,43,39), (5,38,41,39). The two inner garden woods (5..6 and 40..41) are
removed. Shrubs on the seam verges, the fingerposts at (39,22) and (4,22), `k.plants` on the verges, the
write block and `waterways` are as today; the lawn's plants become `k.plants(rng, 16, 6, 26, 40, 37)`.

## Changes

- **`gamev2/tools/generate_kansai_art.py`**: add `SLATE, SLATE_HI` to the `generate_sendai_art` import;
  add the function below and three `SPRITES` rows after `himeji-wall_0_0`; list the three in the header
  docstring. Run `python3 tools/generate_kansai_art.py` (writes the PNGs, `spriteMetadata`, `tileNames`).

  ```python
  def kokoen_wall_v(part):
      """Koko-en's earthen wall running north-south, seen from above: its tiled
      coping, 16px wide down the middle of the cell. 'v' tiles into a run, 'top'
      is a run's north end, 'end' (1x2) its south end, where the wall's end face shows."""
      im, d = canvas(1, 2 if part == 'end' else 1)
      x0, x1 = 8, 23
      y0, y1 = (1 if part == 'top' else 0), (13 if part == 'end' else 31)
      d.rectangle([x0, y0, x1, y1], fill=SLATE)
      for y in range(y0, y1 + 1):
          if y % 4 == 3:
              d.line([(x0, y), (x1, y)], fill=SLATE_LO)             # the courses of tiles, falling east and west
      d.line([(x0, y0), (x0, y1)], fill=SLATE_LO); d.line([(x1, y0), (x1, y1)], fill=SLATE_LO)
      d.line([(x0 + 1, y0), (x0 + 1, y1)], fill=SLATE_HI)
      d.rectangle([15, y0, 16, y1], fill=SLATE_LO); d.line([(15, y0), (15, y1)], fill=SLATE_HI)   # the ridge
      if part == 'top':
          d.line([(x0, 1), (x1, 1)], fill=SLATE_LO)
      if part == 'end':
          coping(d, x0, x1, 12)
          plaster(d, x0, x1, 26, 55)
          footing(d, x0, x1, 56, 63)
      outline(im)
      return im

  'himeji-kokoen-wall-v_0_0': (lambda: kokoen_wall_v('v'), 2, 'himeji-kokoen-wall-v'),
  'himeji-kokoen-wall-v-top_0_0': (lambda: kokoen_wall_v('top'), 2, 'himeji-kokoen-wall-v-top'),
  'himeji-kokoen-wall-v-end_0_0': (lambda: kokoen_wall_v('end'), 2, 'himeji-kokoen-wall-v-end'),
  ```

  No prefab is needed (`b.prop`), so `make_prefabs.py` is not edited.
- **`gamev2/tools/generate_himeji.py`**: the layout above. Constants `TURRET = (20, 6)`,
  `KOKOEN_GATE = (8, 23)`, `POND = (21, 30, 28, 32)`, `POND_BRIDGE = (24, 30)`, `PINES`, and new ones for
  the inner wall's row, the steps' columns and the garden walls' columns and openings. Keep the sections
  in today's order (ground before walls) and `random.Random(2551)`. Rewrite the header docstring's
  north / south paragraphs. Run it, then `python3 tools/config_to_tiled.py Himeji`.
- **`gamev2/tools/districts.py`**, `Himeji`: `castle` keeps bounds (6,2,41,13), `stand=(30, 8)` (today's
  (22,8) is under the turret), description "the white castle on its hill: over the moat by the bridge
  and the gate, then three courts climbed as a hairpin to the keep"; `kokoen` bounds (6,26,40,37),
  `stand=(27, 28)` (off the stones and the bridge's ends, and no longer Korakuen's (22,28)), description
  "the walled garden beside the castle, three rooms in a row: pines and lanterns, the koi pond and its
  bridge, maples". Run `python3 tools/districts.py` after the room is generated; `--report` must show
  `Himeji Castle` in `castle`, `Koko-en garden` and `the pond` in `kokoen`.
- **`gamev2/tools/blog_to_npc.py`**: no change. `('himeji-keep_', ..., (4, 8))` is (12,8);
  `('himeji-kokoen-gate_', ..., (1, 5))` becomes (9,28), a stepping stone's neighbour in room A.
- **Regenerated, committed**: `gamev2/config.json` (`rooms.Himeji`, `districts.Himeji`, three
  `spriteMetadata` / `tileNames` entries, palette appended), `gamev2/tiled/himeji.tmj`, three PNGs in
  `gamev2/assets/sprites/`, `gamev2/assets/map` via `python3 tools/make_worldmap.py --pil`.
- **`gamev2/tools/tests/kansai.test.js`**:
  - Koko-en test: gate `[8, 23]`; replace the loop's cell list with (a) for walls
    `[[5, []], [18, [28, 29]], [31, [34, 35]], [41, []]]`, every row 26..37 is walkable only on the
    opening's rows, (b) walkable cells `[6,26] [17,37] [19,26] [30,37] [32,26] [40,37] [24,29] [25,33]`,
    (c) the `himeji-kokoen-wall-v*` sprites exist and stand only on columns 5, 18, 31, 41, (d) no
    `gravel-autotile_*` on Himeji's `Floor`, (e) at least four `sendai-maple_0_0`, all with x 32..40 and
    y >= 24; `pond.length === 24`; the pond's open cells `'24,30 24,31 24,32 25,30 25,31 25,32'`. The
    north wall loop (x 5..41, rows 24-25, open only at `gx+1`, `gx+2`) and the districts asserts stay.
  - New test "Himeji: the keep is reached by a hairpin through three courts, on sand (#275)": with
    `worldWith(false)`, `world.enter('Himeji', 32, 17)`, `world.path(12, 8).length >= 45`; rows 4-5 on
    x 20..41 are walkable only on 38 and 39; the turret is at `[20, 6]`; (18..19, 2..7) is walkable;
    `Floor` is `sand-autotile_*` on (12,8), (19,5), (30,3), (30,8); no maple has y <= 22.
  - The keep test passes unchanged (it reads the turret's cell from the map).
- **Docs**: `gamev2/docs/landmarks-and-towns.md` - rewrite the **Himeji** bullet in "Kansai: Osaka, with
  Himeji and Okayama on foot" to what is built (courts, inner wall, steps, turret (20,6), sand, Koko-en's
  rooms, walls, gate (8,23), stones, pond, the three wall sprites); in the plan section delete the
  "Himeji (#275): a climb" bullet, say in "What repeats today" that Himeji no longer does, and mark #275
  built in "Build order". Keep the plan's fixed-cell and seam tables: #276 and #277 read them.

One commit: `gamev2: Himeji is rebuilt to the Kansai plan - <what a player sees> (#275)`.

## Data and interfaces

- `config.json`: three `spriteMetadata` + `tileNames` keys (`himeji-kokoen-wall-v_0_0`, `-top_0_0` 64x64;
  `-end_0_0` 64x128), palette entries appended only; `rooms.Himeji` layers; `districts.Himeji` bounds,
  stands, descriptions. `rooms.Himeji.npcs`, `transporters` (ten, same order), `waterways`, size: unchanged.
- No change to `cities`, `places`, `game.lookUp`, `LANDMARKS`, `kansai.py`, `devhouse.world`, or any `src/`.
- `tools/distinct_baseline.json` is not re-recorded (`--update` is not run).

## Tests

From `gamev2/`: `node tools/test_game.js`; `python3 tools/test_blog_to_npc.py`; `node tools/play.js check`;
`python3 tools/check_generators.py`; `python3 tools/sync_cities.py --check`; and
`node tools/play.js lint Himeji`, `node tools/play.js lint KansaiCity`, `python3 tools/check_distinct.py`
(Kansai not worse than the baseline), `node tools/play.js render Himeji <png>` looked at.

Browser regression: `tools/browser/regress.js` (`tools/browser/README.md`); it has no Himeji case, so it
is run for what it does cover and nothing in it should change.

By playing, desktop and a phone size (`?notitle=1&nointro=1&date=2025-11-13`, `&touch=1` on the phone),
stitched and once with `?stitch=0`, with screenshots looked at:
- in from Osaka along the avenue, over the bridge, through the gate, the whole hairpin to Damian at
  (12,8); talk to him; the camera looks up at the keep from (12,8) and the cells beside it;
- the lane (18..19, 2..7) and Honmaru: the player is not hidden by the keep or the turret, and the turret
  against the inner wall leaves no visible way through;
- Koko-en from the gate through both openings to room C and back over the pond's bridge; the wall pieces
  join without seams and the player is drawn correctly in both openings;
- on west to Okayama and back; a boat passes on the moat; both fingerposts answer a bump.

## Risks and open questions

- **Plan wording.** The plan says the keep "is not seen until the upper walk". On a wide desktop view its
  east end can come into view from the west end of Sannomaru, over the turret, with no way through. That
  is accepted; do not add screening to hide it.
- **Wall art.** The north-south wall is a first drawing. If, in the browser, its join under the row-24
  wall or its end face reads wrong, adjust `kokoen_wall_v` only: sizes (1x1, 1x1, 1x2) and cells stay.
  The border wood's canopies overlap the south end faces on row 37; that is intended (the wall runs into
  the trees).
- **Map data is serial.** This rebuilds `Himeji` and rewrites `config.json`, `tiled/himeji.tmj` and
  `assets/map`. Name `Himeji` in the summary; #276 (Okayama) starts only after this is merged.
- **Blog placements.** A new post placed in Himeji before this lands is kept by the generator (`npcs` are
  carried over) but its cell may now be under a wall: `play.js check` reports it, and
  `blog_to_npc.py --rehome` moves it. Today the room has Damian's one post.
- No open question for the owner.
