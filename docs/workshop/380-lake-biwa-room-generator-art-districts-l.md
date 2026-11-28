# Lake Biwa: the room, its art, districts, landmarks and the Nara seam (#380; #269, part 1 of 3)

## Context

Dylan's five posts from Shiga (568, 590, 615, 636, 681) stand in on Osaka's streets because Lake Biwa does
not exist. #68's plan (`docs/workshop/68-…md`, the "Lake Biwa" paragraph, the layout and seam tables,
"Rules every place ticket keeps") makes it a district of the stitched `KansaiCity`: 46x36 at city cell
(152, 0), north of Nara, reached on foot up the towpath. `tools/kansai.py` already holds its `AT`, `SIZE`
and both joins; they are inert until `BUILT` names it. Nara's river and towpath stop two rows short of its
top edge.

Outcome: `KansaiCity` is Okayama + Himeji + Osaka + Nara + Lake Biwa, one walkable room 198x76. Nara's
river and towpath run on north into the room `LakeBiwa`, where the river widens into the lake; the towpath
reaches the Otsu quay and goes on as the Biwaichi cycle path up the east shore to a tunnel mouth, with
Hikone Castle on a wooded knoll and a hill viewpoint over paddies off it, and the Shirahige torii
standing in the water. Four districts and four landmark spots exist for #382 to re-home the posts to.
**No post moves here** (#382), and `config.places` does not change (#381): until #381 the Map says "Lake
Biwa (not on this map)".

Everything below was built as a blockout on a copy of this branch (placeholder art, the cells in this
file) and measured. On it: `play.js lint` is clean for LakeBiwa, Nara and KansaiCity; `play.js check`,
`test_blog_to_npc.py`, `check_generators.py` (one `skip`: `extract_city.py` needs a Japanese system font),
`sync_cities.py --check`, `check_distinct.py` and `rehearse_blog.py` (313/313) pass; the unit tests that
fail (7 of 499) are exactly the ones listed under Tests. It was walked with keys in a browser, desktop and
portrait phone: across the seam both ways stitched and with `?stitch=0`, up the castle's steps, up the
hill, over the paddies; no console errors. Not run: the browser regression. Renders and screenshots are in the ticket's media (`380-*.png`);
every `biwa-*` sprite in them is a placeholder box.

## Approach

Build it the way #268 built Nara: one generator on `roomgen.Builder` + `ks.Kit`, the seam declared once in
`kansai.py`, Nara's generator opening its north edge through the `NORTH` it already computes. The art is a
new tool, `generate_lakebiwa_art.py`, drawn with `house_look.py`.

Decisions that were close:

- **Hikone is not a third terrace.** `docs/landmarks-and-towns.md` ("Later districts") asks this design to
  say how Hikone differs, and bans "the terrace above a full-width wall with one stair". The room has no
  wall sprite at all.

  | | Himeji | Okayama | Hikone |
  |---|---|---|---|
  | Ground | walled `sand-autotile` courts | riverbank lawn, gravel only as paths | a wooded knoll: grass under pines, no court. The only paving is a stone apron 4 cells wide under the keep |
  | Approach | a hairpin climb through the courts | a level stroll along the bank | one straight flight of stone steps, 2 wide and 5 rows long, up through the pines from a spur of the cycle path |
  | Water | a moat under a white wall | the river, the keep's stone base on its bank | none of its own: the open lake, below and west of the cycle path. No moat, bridge or bank |

  The hill viewpoint is not a terrace either: a grass hilltop with a picket rail (`b.fence`, the pack's
  fence Osaka already uses) on its brow, a slope of shrubs under the rail, and its steps up the **west
  flank**, beside the rail, not through it. No `sendai-*` kind beyond the pine, cedar and maple Kansai
  already plants.
- **The railway's closed end moves one cell: `backdrop.extendStop` 5 → 4.** Lake Biwa makes the city 198
  wide, so Osaka's track (city row 34) no longer runs to the city's east edge: it stops short of Lake Biwa
  under a cap shrub. With 5 the cap is at city (146, 34) and half of it shows at the screen's right edge
  from 13 cells in Osaka's north-east corner. Every reachable cell with every camera offset (the camera
  trails ±2 cells) was searched: with 4 (cap at 147) or 3 (148) the end is never in view; with 2 it is seen
  from the towpath. 4 keeps the wider margin on the towpath side. Kansai is the only city where a line
  ends this way (Hokuriku's city has its own `backdrop`).
- **Nara keeps its seeded scatter.** Opening the north edge removes one `woods()` call, which would
  reshuffle every tree and shrub planted after it (255 Collidables cells). The open branch makes the same
  draws on a throwaway builder, and the fingerpost is stamped after the woods into cells they left clear.
  Nara then differs from the committed room only at its north edge (Data and interfaces).
- **A fingerpost of its own, `biwa-fingerpost`.** The seam needs one each side; `nara-fingerpost` has three
  colours that are not on the GuttyKreum sheets, and this ticket's palette test would have to excuse it.
  Eight sprites, not seven.
- **Never `pond-autotile_corner-nw`.** `blog_to_npc.py` reads that tile as "the pond" (a spot). The lake's
  north-west corner is `edge-n` under an `okayama-bank-rock`, as Nara's river does it.
- **`biwa-(?!paddy)` in `LANDMARK_ART`**, as `shirakawa-(?!paddy)`: the paddy is ground, not a landmark.
- **The torii has no bump line.** It stands a row off the shore so that it reads as standing in the lake;
  no cell beside it can be stood on. The six solid kinds a player can reach answer a bump.

## Changes

Paths are from `gamev2/`. Cells are district-local `(x, y)`; `(x0..x1, y0..y1)` is a rectangle, corners
inclusive.

### `tools/kansai.py`

- `BUILT = ('Himeji', 'LakeBiwa', 'Nara', 'Okayama', 'Osaka')`.
- Before `L_TOWPATH`: `L_RIVER = tuple(x + AT['Nara'][0] - AT['LakeBiwa'][0] for x in N_BEND)   # Lake Biwa: 6-8, at y = 35`.
- The docstring and the `JOINS` comment ("inert until Lake Biwa is built (#269)") say it is built.

Nothing else: `seams('LakeBiwa')` then gives (9,35), (10,35) → Nara (23,3), (24,3), and `seams('Nara')`
gains (23,0), (24,0) → LakeBiwa (9,32), (10,32), all hidden.

### `tools/generate_lakebiwa_art.py` (new), `tools/make_prefabs.py`

House look (`docs/generators-and-checks.md`): `house_look` ramps only, a 1px ink outline (`hl.outline`),
light from the upper left, rectangles and pixels only, drawn at 32px a cell and `hl.double()`d. One
function a sprite; `main()` saves `assets/sprites/<key>.png`, calls `art_register.register(built)` (no
glow, no `flat`), then sets `game.lookUp.sprites['biwa-hikone-keep'] = 0` the way
`generate_flinders_art.py` writes its `LOOK_UP`; `--preview OUT.png` writes a contact sheet.

| Key (`_0_0`) | Cells | Drawn |
|---|---|---|
| `biwa-hikone-keep` | 6x6 | a coursed stone base (steel) on the bottom 1.5 cells; three white tiers (cream), each under a dark tiled roof laid in courses, with gables on the middle tier; bell-shaped windows as pixmaps; gilt ridge ends (gold) |
| `biwa-torii` | 2x3 | vermilion posts and two lintels (red) under a dark cap (night); the posts' lowest rows wet (a darker tone) with one pale ripple row |
| `biwa-tunnel` | 4x3 | a wooded hillside (green) round a concrete portal (steel) with a dark mouth 2 cells wide on columns 1-2, open to the bottom edge |
| `biwa-monkey` | 1x1 | a sitting macaque: cream and gold fur, a pink face |
| `biwa-cycle-sign` | 1x2 | a blue Biwaichi board with a white bicycle pictogram, on a steel pole |
| `biwa-paddy` | 1x1 | harvested stubble in rows (gold). A `Floor` tile: opaque to every edge, no outline, tiles seamlessly |
| `biwa-station-sign` | 2x2 | a white nameboard on two posts with a blue band, `たかしま` set 1-bit by `hl.text` (45x11 px at half size) |
| `biwa-fingerpost` | 1x2 | a wooden post with two arms |

`make_prefabs.py`, before `# ---- street accessories (issue #19`: one row each except the paddy, every
sprite on `Collidables` at (0, 0), `doors=[]`. Colliders: keep rows 2-5 of all six columns; torii (0,2),
(1,2); tunnel all twelve cells; monkey (0,0); cycle sign and fingerpost (0,1); station sign (0,1), (1,1).

### `tools/generate_lakebiwa.py` (new)

Header and tail as `generate_nara.py`: `rng = random.Random(380)`, `k.dress()`, `b.finish()`,
`b.room('Lake Biwa', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, ks.seams('LakeBiwa')))`,
then `sentenceName = 'Shiga, by Lake Biwa'`. No `waterways`, doors, road tiles or `train-track`. The body,
in this order (the woods are seeded, so order is part of the result):

```python
RX0, RX1 = ks.L_RIVER; TX0, TX1 = ks.L_TOWPATH      # 6-8, 9-10
LAKE, BASIN = (RX0, 7, 24, 22), (RX0, 23, 13, 29)
BX0, BX1 = 27, 28                                   # the Biwaichi up the east shore
KEEP, TUNNEL = (33, 6), (26, 0)
AX0, AX1 = 35, 36                                   # the castle's steps
HX0, HX1, BROW = 31, 32, 25                         # the hill's steps; the row of its rail
PINES = ['sendai-pine', 'sendai-pine', 'sendai-cedar']
MIXED = ['sendai-pine', 'sendai-cedar', 'sendai-maple', 'sendai-pine']

assert not any(ks.is_open('LakeBiwa', side) for side in 'wne')   # a new join there needs this room rebuilt
b.fill('grass-autotile')
water = set(rect(*LAKE) + rect(*BASIN) + rect(RX0, 30, RX1, H - 1))
# every water cell: b.put('Water', x, y, 'pond-autotile_<role>') and b.solid(x, y). The role is from its
# four neighbours (below row H-1 counts as water): no water north and none west -> 'edge-n' (never
# corner-nw); then corner-ne, corner-se, corner-sw; then edge-n, edge-s, edge-w, edge-e; else center
for at in ((5, 6), (13, 22), (8, 29)): b.stamp('okayama-bank-rock', *at)   # the NW corner, the inside corners
for x, y in ((6, 6), (14, 23), (9, 30)): b.solid(x, y)                     # the land cell under each heap

b.autotile('gravel-autotile', rect(TX0, 32, TX1, H - 1))                   # the towpath
b.put('Floor', TX0, H - 1, 'gravel-autotile_edge-w'); b.put('Floor', TX1, H - 1, 'gravel-autotile_edge-e')
b.autotile('flat-grey-brick-autotile', rect(TX0, 30, 17, 31) + rect(14, 23, 17, 29))   # the Otsu quay
b.stamp('biwa-cycle-sign', 18, 26); b.stamp('biwa-fingerpost', 11, 31)
b.autotile('gravel-autotile', rect(18, 24, BX1, 25) + rect(BX0, 3, BX1, 29) + rect(6, 4, BX1, 5)
           + rect(29, 18, AX1, 19) + rect(29, 28, HX1, 29))                # the Biwaichi and its spurs

b.stamp('biwa-tunnel', *TUNNEL); b.stamp('biwa-station-sign', 21, 2)       # Takashima
for at in ((24, 3), (19, 6), (26, 7)): b.stamp('biwa-monkey', *at)
b.stamp('biwa-torii', 9, 8)

b.stamp('biwa-hikone-keep', *KEEP); k.solid_rect(33, 6, 38, 11)            # Hikone: all 36 cells solid
k.paved(rect(34, 12, 37, 12) + rect(AX0, 13, AX1, 17))                     # the apron, the flight
for x, y in rect(AX0, 13, AX1, 17): b.stairs(x, y)

k.paved(rect(HX0, BROW, HX1, BROW + 2))                                    # the hill: the flight up its flank
for x, y in rect(HX0, BROW, HX1, BROW + 2): b.stairs(x, y)
for i, x in enumerate(range(33, 42)): b.fence(x, BROW, i)                  # the rail on the brow
k.solid_rect(33, BROW + 1, 41, BROW + 2)                                   # the slope under it
for x, y in rect(30, 28, 43, 33):                                         # walkable stubble in four plots,
    if not (x <= HX1 and y <= 29) and x != 37 and y != 31:                 # parted by grass levees on
        b.put('Floor', x, y, 'biwa-paddy_0_0')                             # column 37 and row 31
k.trees('sendai-pine', [(39, 22)])
k.trees('sendai-pine', [(20, 29), (24, 32), (14, 33)]); k.trees('sendai-maple', [(22, 27)])   # the lawn

k.woods(0, 0, 5, H - 1, MIXED, rng); k.woods(6, 0, 25, 1, MIXED, rng)      # west shore, north edge
k.woods(30, 0, W - 1, 5, MIXED, rng); k.woods(29, 3, 29, 5, MIXED, rng)    # behind the castle
k.woods(29, 6, 32, 11, PINES, rng); k.woods(39, 6, W - 1, 11, PINES, rng)  # either side of the keep
k.woods(29, 12, 34, 17, PINES, rng, clear=[(34, 12)])                      # ...of the apron and the flight
k.woods(37, 12, W - 1, 17, PINES, rng, clear=[(37, 12)])
k.woods(37, 18, W - 1, 19, PINES, rng)                                     # east of the castle's spur
k.woods(29, 20, 41, 21, PINES, rng); k.woods(29, 22, 30, 27, PINES, rng)   # the hilltop's back, its west flank
k.woods(42, 20, W - 1, 27, MIXED, rng); k.woods(44, 28, W - 1, H - 1, MIXED, rng)   # its east end, the east edge
k.woods(11, 34, W - 1, H - 1, MIXED, rng)                                  # the south edge
k.plants(rng, 14, 18, 26, 26, 33); k.plants(rng, 8, 6, 2, 20, 3); k.plants(rng, 5, 33, 22, 41, 24)
```

Open cells on the room's edge are the towpath's two, (9,35) and (10,35), and nothing else: the west,
north and east edges are wood, and the tunnel is twelve solid cells. The hilltop (31..41, 22..24) is
reached only by its flight; the paddies only from the spur at (29..32, 28..29). The paddy field is four
plots of `biwa-paddy` parted by grass levees (column 37, row 31), so one repeated tile does not read as a
single flat slab; the levees are walkable grass, in no `plants` rectangle, and draw nothing from `rng`.

### `tools/generate_nara.py`

Only where `NORTH` (`ks.is_open('Nara', 'n')`) is true; the closed branch stays as it is.

- After the towpath's `b.autotile`: `b.put('Floor', TX0, 0, 'gravel-autotile_edge-w')` and
  `b.put('Floor', TX1, 0, 'gravel-autotile_edge-e')` (no rounded end at the seam).
- `if not NORTH: k.woods(BX0, 0, TX1, TOP - 1, AUTUMN, rng)` gains
  `else: ks.Kit(rg.Builder(W, H)).woods(BX0, 0, TX1, 1, AUTUMN, rng)` — the same draws, planted nowhere.
- `k.woods(25, 2, 30, 9, AUTUMN, rng)` gains `clear=rect(TX1 + 1, 2, TX1 + 1, 5) if NORTH else ()`.
- After the last `k.plants`, before the room is written: `b.stamp('biwa-fingerpost', TX1 + 1, 2)` (feet on
  (25, 3)). It must come after every `woods()`: stamped earlier, the wood plants round it and reshuffles.
- The docstring's lines about waiting for Lake Biwa say what is there now.

### Config and the world file (by hand, then the tools)

- `config.json` `cities.KansaiCity.rooms` gains `{"room": "LakeBiwa", "x": -106, "y": 31}`;
  `cities.KansaiCity.backdrop.extendStop` becomes `4`.
- `../devhouse.world`: after the `nara.tmj` entry, in the file's own two-space format and key order,
  `gamev2/tiled/lakebiwa.tmj` at `x` -6784, `y` 1984, `width` 2944, `height` 2304. Do not let a tool
  re-indent the file; `sync_cities.py --check` then agrees.

### `tools/districts.py`, `tools/blog_to_npc.py`

`districts.py`, before `# --- Tohoku ---`:

```python
# Lake Biwa: walked to from Nara up the towpath, the north-east of KansaiCity (issue #380)
'LakeBiwa': [
    d('otsu', 'Otsu lakefront', 'the quay where the river from Nara widens into Lake Biwa: the start of the Biwaichi cycle path, a lawn of pines', (9, 23, 28, 33), stand=(15, 27)),
    d('hikone', 'Hikone Castle', 'the white keep on its wooded knoll above the east shore: one flight of stone steps up through the pines to the apron under it', (29, 6, 43, 19), stand=(33, 18)),
    d('viewpoint', 'Hill viewpoint', 'a hill inland of the lake, looking out over the plains of Shiga: a rail on the brow, harvested rice paddies below, steps up its west flank', (29, 20, 43, 33), stand=(37, 24)),
    d('takashima', 'Takashima', 'the north shore: the cycle path into a tunnel mouth, monkeys on the verge, a station sign, a torii standing in the lake', (6, 2, 28, 6), stand=(15, 5)),
],
```

`blog_to_npc.py` `LANDMARKS`, after the `nara-deer-stag_` row:

```python
('biwa-cycle-sign_', 'the Otsu lakefront', (-1, 1), {'rooms': ('LakeBiwa',)}),   # (17, 27): the quay beside the sign
('biwa-hikone-keep_', 'Hikone Castle', (1, 6), {'rooms': ('LakeBiwa',)}),         # (34, 12): the apron, off the steps
('biwa-tunnel_', 'the lakeside tunnel', (-1, 3), {'rooms': ('LakeBiwa',)}),       # (25, 3): beside the mouth
('biwa-torii_', 'the Shirahige torii', (1, -2), {'rooms': ('LakeBiwa',)}),        # (10, 6): the shore above it
```

Every label is 20 characters or fewer. No `PLACEMENTS` / `REHOME` row changes: the posts stay.

### `src/utils/Interactions.js`

After the `nara-kasuga-torii` row, under `// Lake Biwa (issue #380)`, all `group: 'flavour', footprint: true`:

| `kind` | `pattern` | `say` |
|---|---|---|
| `fingerpost` | `/^biwa-fingerpost/` | north: lake biwa, otsu and the cycle path round the lake. south: nara, the deer and the great buddha |
| `hikone-keep` | `/^biwa-hikone-keep/` | hikone castle. one of twelve keeps left from the age of castles, said to have come here in pieces from otsu |
| `tunnel` | `/^biwa-tunnel/` | a road tunnel through the hill. no pavement, no shoulder, and something is moving on the roof |
| `monkey` | `/^biwa-monkey/` | a monkey. it looks at your bag, then at you, then at your bag |
| `cycle-sign` | `/^biwa-cycle-sign/` | biwaichi: once round the lake, 200 kilometres. keep the water on your left |
| `station-sign` | `/^biwa-station-sign/` | omi-takashima. the next train is in fifty minutes. there is no bicycle shop |

Fishing needs nothing: the `pond` rule matches `pond-autotile`.

### `tools/check_generators.py`, `tools/check_distinct.py`

- `GENERATORS += ['generate_lakebiwa']` on the line after `generate_nara`; `generate_lakebiwa_art` joins
  `ART_TOOLS` beside the other house-look tools.
- `LANDMARK_ART`: `…|nara-|biwa-(?!paddy)|`. Never run `check_distinct.py --update`.

### Build order

```bash
python3 tools/generate_lakebiwa_art.py --preview /tmp/biwa.png   # look at the sheet
python3 tools/make_prefabs.py
python3 tools/generate_lakebiwa.py && python3 tools/generate_nara.py
python3 tools/sync_cities.py --check
python3 tools/districts.py
python3 tools/config_to_tiled.py LakeBiwa Nara
python3 tools/make_worldmap.py --pil
node tools/play.js lint LakeBiwa && node tools/play.js lint Nara && node tools/play.js lint KansaiCity
node tools/play.js render LakeBiwa /tmp/lakebiwa.png             # and look at it
python3 tools/check_distinct.py && python3 tools/rehearse_blog.py
```

### Docs (same commit)

- `docs/landmarks-and-towns.md`, the Kansai section: its title and `BUILT`; 190x46 → 198x76; Nara's north
  edge is open; the track now stops in the wood short of Lake Biwa (`extendStop: 4`, why); the build
  order; the landmark and district tables; a "Lake Biwa" paragraph (the layout above in prose, the bump
  lines, the torii out of reach); under "Later districts", the Hikone column of the table in Approach.
- `docs/stitched-city.md` ("190x46 with four districts"), `docs/ambient-traffic.md` (the track's east end),
  `docs/generators-and-checks.md` (the distinctness figures `check_distinct.py` prints, the new art tool).

## Data and interfaces

- `config.json`: `rooms.LakeBiwa` (new; `name` "Lake Biwa", `sentenceName`, two hidden seams, no NPCs);
  `rooms.Nara` (north edge only: the river on columns 20-22 and the towpath on 23-24 reach row 0; cells
  (23..24, 0..1) and (25, 2), (25, 4), (25, 5) open; the fingerpost at (25, 2); two more hidden seams,
  written last); `districts.LakeBiwa`; `cities.KansaiCity` as above; `game.lookUp.sprites`; eight
  `biwa-*` entries appended to `tilePalette`, `spriteMetadata` and `tileNames`.
- `KansaiCity` at runtime: 198x76. Its track is 98 tiles on city row 34 (x < 88, and 138..147), capped by
  a shrub at (147, 34).
- Spot ids #382 will use: `LakeBiwa · the Otsu lakefront` (568, 681), `LakeBiwa · Hill viewpoint (area)`
  (590), `LakeBiwa · Hikone Castle` (615), `LakeBiwa · the lakeside tunnel` (636).
- Unchanged: `config.places`, `trips`, every NPC, the start rooms, `src/` other than the six rules.
- Map data touched (serial): rooms `LakeBiwa` (new) and `Nara`, `cities.KansaiCity`, `devhouse.world`,
  `assets/map`.

## Tests

Existing tests that change (each fails on the blockout for the reason given, and for no other):

| Test | Change |
|---|---|
| `dates-trips.test.js`, the lead-in test | rooms with a `sentenceName`: `['LakeBiwa', 'Tokyo']` |
| `kansai.test.js` "Kansai is a third stitched city…" | `DISTRICTS` gains `'LakeBiwa'`; the HUD names gain `Lake Biwa`; `unbuilt` is `[]` |
| "Kansai: the seams line up…" | 6*5 + 4 seam pairs; a pair on a top or bottom edge is checked along y (the floor is `gravel-autotile_edge-[we]`, the landing is `IN` rows in); `seams('Nara')` and Nara's open edge gain (23,0), (24,0); LakeBiwa's open edge is (9,35), (10,35) only; the water carries across: Nara (20..22, 0) and LakeBiwa (6..8, 35) are `edge-w`, `center`, `edge-e`, solid |
| "Kansai is one walkable room…" | the city is 198x76; 98 track tiles, all on row 34, x < 88 or 138..147; the walk goes on from Nara's towpath to the quay, the apron (35,12), the hilltop (37,24) and the tunnel mouth (27,3), stitched and with `?stitch=0`; the seam and fade counts follow; a landing may be `IN` rows in |
| "Nara: the Great Buddha Hall…" | the wood behind the hall excludes the towpath's cells |
| "Nara: the deer, the stall…" | Nara's hidden seams may target `LakeBiwa` |
| "Nara: its north edge waits for Lake Biwa…" | replaced: the river and towpath reach row 0; (23,0), (24,0) are the only open cells on Nara's north edge; still no `pond-autotile_corner-nw` |

The fingerpost test gains the Nara–Lake Biwa pair: one `biwa-fingerpost_0_0` in Nara at (25,2) and one in
LakeBiwa at (11,31), each beside the towpath within 4 rows of the seam.

New, in `kansai.test.js`:

- **The room**: 46x36; `sentenceName`; its only transporters are the two hidden Nara seams; the north,
  east and west edges have no open cell; no `train-track`, no station in `config.stations`, no rubbish
  bin, no door, and no building (every `Collidables` sprite is `biwa-*`, a `sendai-` tree, a shrub or the
  picket fence); no `hokuriku-`, `kanazawa-`, `shirakawa-` or `toyama-` art (so
  `biwa-paddy`, not `shirakawa-paddy`); no `pond-autotile_corner-nw`.
- **The lake**: a bump west from the quay cell (14,27) into (13,27) is `kind: 'pond'` (fishing); every
  water cell is solid.
- **Hikone**: the keep at (33,6), 6x6, all solid, in `game.lookUp.sprites`. From each apron cell
  `LandmarkView.aim` has weight 1 (as the Okayama keep's test calls it): the 960 view holds the whole keep
  with its top under the bar (the offset is 0 there: the keep is only 6 rows tall), the 480 view looks up
  (offset > 0). No sprite in the room matches `/wall/`; the apron is (34..37, 12)
  with (33,12) and (38,12) solid; every `castle-stairs_0_0` cell is in a flight at least 3 rows long whose
  outer sides are solid on every row.
- **The hill**: the hilltop is reached from (31,28) and from nowhere else; the rail is nine solid fence
  cells on row 25; paddies are walkable; no `biwa-paddy` on column 37 or row 31 (the levees), and each of
  the four plots has at least one.
- **Distinctness**: `spawnSync('python3', ['-I', 'tools/check_distinct.py'], { cwd: GV2 })` (as
  `check-generators.test.js` calls Python); the line starting `Kansai ` is present and has no `WORSE`. Only
  Kansai's line is asserted, so another city's regression does not fail a Lake Biwa test. No Pillow needed
  (0.1 s).
- **Districts and spots**: the four districts, each `stand` open and inside its bounds; the four
  `LANDMARKS` spots resolve to open cells (17,27), (34,12), (25,3), (10,6); labels ≤ 20 characters.
- **Bumps**: each of the six rules answers from a cell a player can stand on; the torii has no rule.

New file `tools/tests/lakebiwa-art.test.js`, modelled on `house-look.test.js` and `flinders.test.js`:
every opaque colour of every `biwa-*` PNG, **and of every tile key `rooms.LakeBiwa`'s layers use**
(`assets/sprites/<key>.png`; a key with no file fails), is a colour of the sheets under
`art-source/GuttyKreum` (skipping `preview*`) — the room's palette, not only its new art. Checked on
`master`: the other sprites the room uses (`sendai-pine`/`-cedar`/`-maple`, `shrub-small-circle`,
`okayama-bank-rock`, `castle-stairs`, `fence-barriers_*`, `ground-plants-1_*`, the `pond`, `grass`,
`gravel` and `flat-grey-brick` autotiles) are all on the sheets (`shrub-small-circle-snow` is not, and is
not used); each PNG is 64 px a cell at the sizes in the table and made of 2x2 blocks;
`biwa-paddy` has no transparent pixel; `check_distinct.py`'s `LANDMARK_ART` matches the seven landmark
keys and not `biwa-paddy_0_0`.

Run, from `gamev2/`: the five checks in `CLAUDE.md`; `node tools/play.js lint LakeBiwa` and `render
LakeBiwa`; `python3 tools/check_distinct.py`; `python3 tools/rehearse_blog.py` (313/313 on the blockout; no post moves);
the browser regression (`tools/browser/README.md`). Then play it with real keys and touches, desktop and
a phone size, stitched and `?stitch=0`: Nara's avenue → up the towpath → the quay (fish) → the Biwaichi →
the castle steps (the whole keep in view from the apron) → the hill → the paddies → the tunnel, bumping each thing;
from Osaka's north-east corner (48,7) the track must run off screen with no end in view.

## Risks and open questions

- **The track end's margin is half a cell** on the Osaka side (cap at 147; the view from Osaka (48,7)
  reaches x 146.5). The walk test's track assertion and the play-through above hold it; a change to the
  camera deadzone, `AT`, or Osaka's north-east corner needs the search redone.
- **Art is the bulk of the work** and only placeholders were looked at. The keep is 6x6 and looked up at:
  draw it first, look at it beside `himeji-keep` and `okayama-keep` on a contact sheet, and keep the three
  distinct in outline (Hikone: small, three tiers, gables on the middle tier). The fence, steps and
  paving are existing tiles.
- **`check_distinct.py`** passed on the blockout (Kansai: buildings 0.10, sprites 0.33, own art 51%); real
  art changes the figures a little. If it fails, fix the art, not the baseline.
- **Until #381**, the Map names the room "Lake Biwa (not on this map)". Expected; nothing errors.
- **The city's backdrop grows** to 198x76, most of it wood north of Osaka. No slowdown was seen (chunks
  stream); the browser regression is the check.
- **Nara changes only at its north edge.** If `check_generators.py` or a diff shows more of Nara moving,
  the throwaway draw or the stamp order is wrong.
- **A portrait phone draws a long bump line very small** (existing behaviour, same as Nara's hall line);
  not this ticket's to fix.
- No open question for the owner.

## Review

Design review (adversary). The load-bearing claims were checked against the code rather than taken from the
blockout: Nara's open branch was applied to a scratch copy of `generate_nara.py` with `BUILT` gaining
LakeBiwa, and the rebuilt `rooms.Nara` differs from the committed one only at cells (19..25, 0..5) — the
seeded scatter does hold (note `Kit.woods` draws `rng.random()` only for untaken cells, so this was a real
risk). The `cities` entry (-106, 31) and the world-file rectangle (-6784, 1984, 2944x2304) follow from
Nara's (-120, 67) and (-7680, 4288) and `AT`. `seams()` gives the stated landings. The game always renders
1280x960 (`Viewport`), so the half-cell track-end margin does not depend on the window. `hl.text` sets
`たかしま` in the committed `fonts/PixelMplus12-Grid.ttf`, so the art tool needs no system font and is
checked in CI. Duplicate `kind: 'fingerpost'` rules already exist (Karuizawa, Kansai, Okayama, Nara).

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | The ticket asks for a test in `tools/tests/` that `check_distinct` holds; the design only ran `check_distinct.py` by hand, and none of the five checks runs it on the real world (`test_blog_to_npc.py` only checks the baseline's keys). | A `kansai.test.js` case spawns `check_distinct.py` and asserts Kansai's line is not `WORSE` (Tests). | Yes |
| 2 | "The palette holds to the GuttyKreum sheets" was tested only for the eight `biwa-*` PNGs; the room's palette is every sprite it uses, and a later edit could bring in an off-sheet one (e.g. `shrub-small-circle-snow`, 28 off-sheet colours). | The art test also walks every tile key in `rooms.LakeBiwa`. Verified today's non-`biwa` sprites all pass, so this costs nothing now. | Yes |
| 3 | The paddies are one 1x1 tile repeated over 14x6 cells: in the blockout render they read as a flat mustard slab, not fields. | Grass levees on column 37 and row 31 part the field into four plots; no rng, district, spot or reach changes. | Yes |
| 4 | "The far edges stay closed until a neighbour exists (`kansai.is_open`)": the generator hardcodes woods on the west, north and east, so a future join on those sides would silently open onto a wood. | `assert not any(ks.is_open('LakeBiwa', side) for side in 'wne')` at the top of the body. | Yes |
| 5 | Hikone's bump line says it "never burned"; the twelve are the keeps *surviving* from the Edo period, and the relocation story is from Otsu Castle. | "hikone castle. one of twelve keeps left from the age of castles, said to have come here in pieces from otsu" (104 characters, one shorter than before). | Yes |
| 6 | The north edge wood is rows 0-1, too shallow for `Kit.woods` to plant any tree (a 3-tall pine's top would be row -1), so Takashima is backed by a single hedge of shrubs. | Widen it to rows 0-2. | No: it reshuffles the measured scatter and swallows the plants and the station sign's top row; the hedge reads acceptably in the render. Look at it on the real-art render and widen it only if it looks bare. |
| 7 | While in Lake Biwa the HUD/Map says "Lake Biwa (not on this map)" until #381. | None here. | No: the split into #380/#381 is the ticket's; `Places.whereText` handles it without error. |
| 8 | The torii answers no bump. | None. | No: nothing beside it can be stood on (intended: it stands in the lake), and the ticket does not ask for a line. |

No question for the owner.

