# Karuizawa, part 1: the room, the reopened west gate and the generator wiring (#260)

Part 1 of 4 of #256. The plan is `docs/workshop/68-featured-locations-everywhere-else-anyon.md` (paragraph
"Karuizawa", the seam tables, "Rules every place ticket keeps"). Everything below was built as a prototype
on a scratch copy and checked there; the numbers are measured, not estimated.

## Context

Karuizawa has no place in the game: Julia's post 572 stands on Tokyo Station's platform as a stand-in. Tokyo's
west gate (Tokyo cells `(0,41)`, `(0,42)`) was fenced by `e3cb4d0d` when Machi was deleted.

Outcome of this part: a new outdoor room `Karuizawa` (48x40), the fifth district of `TokyoCity`, at world
cell (-48, 8), reached on foot through the reopened gate, stitched and with `?stitch=0`. A packed-dirt road
in from the gate, woods, a fingerpost inside the gate. **No shops, no falls, no real art, no re-homed posts,
no start-room change**: those are parts 2 to 4. Rooms touched: **Karuizawa** (new) and **Tokyo** (two edge
cells and two transporters). `TokyoCity` grows from 117x109 to **165x109**; every merged x shifts by +48
(Tokyo is at city `(48,1)`), height and `depthScale` do not change.

## Approach

- **One generator, `tools/generate_karuizawa.py`**, on the Hokuriku pattern (`generate_shirakawago.py`:
  `roomgen.Builder` + `hokuriku.Kit`). It builds the room and owns the edit to the ported Tokyo map, as
  `generate_palace.py` owns its doors there. Idempotent; in `check_generators.GENERATORS`.
- **The gate's transporters go back among Tokyo's seams, not at the end of the list.** `rg.open_door` / a
  plain `rg.pin` appends, and then `palace.test.js` "seal the palace and rebuild gives the same world" fails
  (the palace doors are re-appended after Karuizawa's). So: pin in place if the cell already has a
  transporter, otherwise insert right after the last transporter whose target is a `TokyoCity` district.
  Tokyo's list becomes `Market, Market, Karuizawa, Karuizawa, ShrineTokyo1, PalaceHallTokyo1 x2`.
- **Art**: placeholder, except the fingerpost. The plan requires each city's own fingerpost with a bump line,
  and an `Interactions` rule cannot be hung on another town's sprite, so a small new
  `tools/generate_karuizawa_art.py` draws `karuizawa-fingerpost_0_0` (1x2) now; part 2 adds the rest of the
  kit to the same tool. The woods are `tree-green` (Tokyo's own `tree-3`, already in Tokyo and Park), so
  `check_distinct.py` gets no worse (Tokyo measured: buildings 0.155 -> 0.153, sprites 0.317 -> 0.315, own
  0.557 -> 0.563); part 2 swaps in `karuizawa-larch`.
- **Layout** (leaves room for parts 2 and 3; they re-cut the woods in the generator): a 2-wide dirt road,
  rows 34-35 from the gate west to x=14, then columns 14-15 north to row 10 ("west then north", the future
  Kyu-Karuizawa Ginza), one-cell grass verges, an open clearing `(10..21, 5..11)` at its head where the falls
  will stand, solid woods everywhere else.
- **`config.places.Karuizawa` makes the room its own Map dot** (`minor: true`). One consequence in tooling:
  `world-model.js` `geoOf('TokyoCity')` would become the mean of Tokyo and Karuizawa; a key that is itself a
  place must use its own geo (one-line fix below).

## Changes

All paths under `gamev2/` unless they start with `devhouse.world` or `docs/`.

### New: `tools/generate_karuizawa_art.py`

Model: `generate_hokuriku_art.py` (`SPRITES` table, `main()`, `--preview`; helpers `rgb, canvas, outline`
from `generate_hokkaido`). One sprite: `'karuizawa-fingerpost_0_0': (fingerpost, 2, 'karuizawa-fingerpost')`,
drawn on `canvas(1, 2)` (32x64, doubled to 64x128) like `bear_sign()`: a wooden post on a stone foot, one
cream arm pointing east, one west. Writes `assets/sprites/karuizawa-fingerpost_0_0.png`,
`spriteMetadata` (`frameCount 1, anchorX 32/w, anchorY 32/h`) and `tileNames`; saves config with
`indent=2, sort_keys=True`. Add `ART_TOOLS += ['generate_karuizawa_art']` in `check_generators.py`.

### New: `tools/generate_karuizawa.py`

The prototype, which lints clean and reproduces itself; keep the calls and their order (the seeded scatter
depends on it), add a docstring in the style of `generate_shirakawago.py` (what the room is, the seam, how to
run, the build order below).

```python
import random
import roomgen as rg
from roomgen import rect
from hokuriku import Kit

HOST = 'Tokyo'
W, H = 48, 40
GATE, HOST_GATE, IN = (34, 35), (41, 42), 3     # Karuizawa rows at x=47, Tokyo rows at x=0, cells a seam lands in
BRICK = 'flat-grey-brick-autotile_center'
POST = (44, 33)                                  # the fingerpost's foot, on the verge north of the road
LARCH = ['tree-green']                           # part 2: karuizawa-larch
RX0, RX1 = 14, 15                                # the road north

cfg = rg.load_config()
host = cfg['rooms'][HOST]
b = rg.Builder(W, H); k = Kit(b); rng = random.Random(260)
b.fill('grass-autotile')
b.autotile('dirt-outside-autotile', rect(RX0, GATE[0], W - 2, GATE[1]) + rect(RX0, 10, RX1, GATE[0] - 1))
b.put('Floor', W - 2, GATE[0], 'dirt-outside-autotile_edge-n')    # open to the brick, not a closed end
b.put('Floor', W - 2, GATE[1], 'dirt-outside-autotile_edge-s')
for y in GATE:
    b.put('Floor', W - 1, y, BRICK)                               # the same brick as Tokyo's apron
b.stand('karuizawa-fingerpost_0_0', *POST)
k.woods(0, 0, W - 1, 4, LARCH, rng)                       # north
k.woods(0, 5, 9, H - 1, LARCH, rng)                       # west
k.woods(22, 5, W - 1, GATE[0] - 2, LARCH, rng)            # east block, north of the road
k.woods(10, 12, RX0 - 2, H - 1, LARCH, rng)               # west of the road north
k.woods(RX1 + 2, 12, 21, GATE[0] - 2, LARCH, rng)
k.woods(RX0 - 1, GATE[1] + 2, W - 1, H - 1, LARCH, rng)   # south
k.solid_rect(W - 1, GATE[0] - 1, W - 1, GATE[0] - 1)      # the verge cells on the edge: only the gate is open
k.solid_rect(W - 1, GATE[1] + 1, W - 1, GATE[1] + 1)
k.plants(rng, 40, 10, 5, 21, 11)                          # the clearing
k.plants(rng, 30, RX0 - 1, GATE[0] - 1, W - 2, GATE[1] + 1)
prev = cfg['rooms'].get('Karuizawa', {})
k.dress(); b.finish()
seams = [rg.transporter(W - 1, y, HOST, IN, hy, hidden=True) for y, hy in zip(GATE, HOST_GATE)]
cfg['rooms']['Karuizawa'] = b.room('Karuizawa', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, seams))

# Tokyo: the reverse of e3cb4d0d
DISTRICTS = [m['room'] for m in cfg['cities']['TokyoCity']['rooms']]
def seam(items, t):
    if any((i['gridX'], i['gridY']) == (t['gridX'], t['gridY']) for i in items):
        return rg.pin(items, t)
    at = max((n for n, i in enumerate(items) if i['targetRoom'] in DISTRICTS), default=-1) + 1
    items.insert(at, t)
layers = {l['name']: l['tiles'] for l in host['layers']}
for y, hy in zip(GATE, HOST_GATE):
    layers['Floor'][f'0,{hy}'] = rg.pidx(BRICK)
    layers['Collidables'].pop(f'0,{hy}', None)            # fence-barriers_0_2
    layers['Colliders'].pop(f'0,{hy}', None)
    seam(host['transporters'], rg.transporter(0, hy, 'Karuizawa', W - 1 - IN, y, hidden=True))
rg.save_config(cfg)
```

Result: Karuizawa `(47,34)` -> Tokyo `(3,41)`, `(47,35)` -> Tokyo `(3,42)`; Tokyo `(0,41)` -> Karuizawa
`(44,34)`, `(0,42)` -> `(44,35)`; all hidden. The fingerpost tile is at `(44,32)`, solid on `(44,33)`. The
fence, collider and `edge-w` brick at Tokyo `(0,40)` and `(0,43)` and the lantern pair stay. The palette
gains one entry (`karuizawa-fingerpost_0_0`, appended by the Builder).

### Edited by hand

- **`config.json`**: append `{"room": "Karuizawa", "x": -48, "y": 8}` to `cities.TokyoCity.rooms` (last: the
  order is authored, and the generator reads it); add
  `places.Karuizawa = {"geo": [138.63, 36.35], "label": "Karuizawa", "minor": true}`.
- **`devhouse.world`**: after the `park.tmj` entry,
  `{"fileName": "gamev2/tiled/karuizawa.tmj", "x": -3072, "y": 512, "width": 3072, "height": 2560}`. The file
  has no trailing newline: keep it that way.
- **`tools/check_generators.py`**: `GENERATORS += ['generate_karuizawa']` before the
  `GENERATORS += ['districts']` line (districts stays last); the art tool as above.
- **`tools/districts.py`** `DISTRICTS`:
  `'Karuizawa': [d('larch-road', 'Larch road', "the packed-dirt road in from Tokyo's west gate, through the larch woods to a quiet clearing", (10, 5, 46, 36), stand=(30, 33))]`.
- **`tools/blog_to_npc.py`** `LANDMARKS`, before the "Inside a station" rows:
  `('karuizawa-fingerpost_', 'the road from Tokyo', (-1, 1), {'rooms': ('Karuizawa',)})` (spot cell `(43,33)`;
  `test_spots` needs every outdoor room to offer one).
- **`src/utils/Interactions.js`** `RULES`, beside the `shirakawa-bear-sign` flavour row:
  `{ kind: 'fingerpost', group: 'flavour', pattern: /^karuizawa-fingerpost/, footprint: true, say: 'east, through the gate: Tokyo. west, up the road through the larches: Karuizawa' }`.
- **`tools/check_distinct.py`**: add `karuizawa-` to `LANDMARK_ART`. Do **not** run `--update` (see Risks).
- **`tools/world-model.js`** `geoOf`: `const towns = places[k] ? [k] : [...new Set(...)].filter((t) => t);`
  (a key that is a place sits at its own dot; without it `studio-editor.test.js` "an airport is where the
  town it serves is" fails).
- **`src/systems/CityStitcher.js`** header comment: five districts.

### Build order (from `gamev2/`, Pillow python for the art and map tools)

```bash
python3 tools/generate_karuizawa_art.py
# hand edits to config.json (cities, places) and ../devhouse.world
python3 tools/generate_karuizawa.py
python3 tools/districts.py
python3 tools/config_to_tiled.py Karuizawa Tokyo
python3 tools/sync_cities.py
python3 tools/make_worldmap.py
node tools/play.js lint Karuizawa Tokyo TokyoCity      # 0 errors, 0 warnings; TokyoCity 165x109
node tools/play.js render Karuizawa out.png && node tools/play.js render TokyoCity city.png --scale 0.25   # look at both
```

Generated and committed: `config.json`, `tiled/karuizawa.tmj` (new), `tiled/tokyo.tmj`,
`assets/map/world-map.{json,png}`, `assets/sprites/karuizawa-fingerpost_0_0.png`.

### Docs (same commit)

- `docs/stitched-city.md`: five districts; the union's top-left ("Tokyo is at 48,1, Market at 106,0"); 18
  seam transporters -> 22; replace the bullet "The west gate is closed" with the gate to Karuizawa (cells,
  brick, who owns the edit); the railway sentence (the cutting now runs west under Karuizawa, which ends at
  world row 47, north of the track at row 50); "Tokyo's column 0 is the west edge" is no longer true.
- `gamev2/CLAUDE.md` rule "The four Tokyo districts ..." -> five (or "Tokyo's districts"); the ported-rooms
  rule gains "Tokyo's west gate cells are written by `generate_karuizawa.py`".
- `docs/landmarks-and-towns.md`: a short Karuizawa entry (generator, layout, what parts 2-4 add);
  `docs/generators-and-checks.md` if it lists generators that edit a ported map;
  `docs/tools-play-test-studio.md` line 48 ("the four districts outlined").

## Data and interfaces

- `config.rooms.Karuizawa`: outdoor room, `name: 'Karuizawa'`, 48x40, two hidden transporters, no NPCs.
- `config.rooms.Tokyo`: Floor `0,41` and `0,42` = `flat-grey-brick-autotile_center`; no Collidables or
  Colliders there; two hidden transporters inserted after the Market seams.
- `config.cities.TokyoCity.rooms[4] = {room: 'Karuizawa', x: -48, y: 8}`; `config.places.Karuizawa` (above);
  `config.districts.Karuizawa` (one district, written by `districts.py`); `spriteMetadata`, `tileNames`,
  `tilePalette` gain `karuizawa-fingerpost_0_0`.
- Derived, no code change: `Places.of(config, 'Karuizawa') === 'Karuizawa'`;
  `Places.arrival(config, 'Karuizawa')` is `{room: 'Karuizawa', x: 44, y: 34}`; `Places.list` has eleven dots.
- No save-format, shop, station, trip or start-room change.

## Tests

New **`tools/tests/karuizawa.test.js`** (helpers as in `kanazawa.test.js`; all verified on the prototype):

1. District and place: `cities.TokyoCity.rooms` keys are `Tokyo, Market, Palace, Park, Karuizawa`; size
   48x40; offset from Tokyo `(-48, 7)`; the `devhouse.world` entry; `places.Karuizawa`; `Places.of` /
   `Places.arrival` as above; no `train-track*` tile; every transporter targets `Tokyo`; no station serves
   it; `assets/map/world-map.json` names it.
2. The gate: the four transporters exactly (cells, targets, hidden); seam and landing cells not solid; the
   Floor name is the same either side (`flat-grey-brick-autotile_center`); flood-fill from the transporters
   over non-collider cells: the only edge cells reached are `47,34` and `47,35`, and more than 150 cells are
   reached; no `road-*` Floor tile on an edge cell.
3. The walk, `worldWith(true)` and `worldWith(false)`: enter Tokyo `(6,41)`; stitched, the city is 165x109,
   `rm.resolve('Tokyo', 0, 0).x === 48`, `world.path` to Karuizawa `(14,12)` and back to Tokyo `(6,42)` with 0
   fades and 1 crossing each way; unstitched, walk to Tokyo `(1,41)`, one step west arrives at Karuizawa
   `(44,34)`, walk to `(14,12)`, back to `(46,35)`, one step east arrives at Tokyo `(3,42)`.
4. The fingerpost: one `karuizawa-fingerpost_0_0` at `44,32`; `(44,33)` solid, `(44,34)` not; stepping north
   from `(44,34)` does not move and returns a `flavour` interaction of kind `fingerpost` whose `say` names
   Tokyo and Karuizawa in at most 100 characters; no other town's sign in the room.

Edits to existing tests (each is an intended change):

- **`roads-waterways.test.js`** "Tokyo's west gate is closed ..." (the fenced-gate test is here, not in
  `madeup-towns.test.js`): rename to "... leads to Karuizawa". Transporters with `gridX === 0` are exactly
  `{gridX: 0, gridY: 41|42, targetRoom: 'Karuizawa', targetX: 44, targetY: 34|35, hidden: true}`; fence,
  collider and `edge-w` only at `0,40` and `0,43`; `0,41..42` centre brick, no Collidables, no collider; the
  `(1,y)`, `(2,y)`, `(2,43)` assertions stay. Stitched: for Tokyo rows 0..45 the step west off column 0
  (`canStep(at.x, at.y, at.x - 1, at.y)`) is open only for 41 and 42, and `rm.resolve('Tokyo', 0, 0).x === 48`.
  Unstitched (after `world.enter('Tokyo', 1, 41)`): column 0 can be stepped onto only at rows 41 and 42.
- **`madeup-towns.test.js:24`**: five districts.
- **`palace.test.js:50`**: `['Market', 'Market', 'Karuizawa', 'Karuizawa', 'ShrineTokyo1', KEY, KEY]`. Its
  seal-and-rebuild test must pass unchanged.
- **`japan-map.test.js`**: drop `Karuizawa` from `SMALL`; `LANDING = STAGES` (lengths `[1, 2, 3, 4]`, "the
  four Maps the tickets still pass through"); the label list gains `'Karuizawa'`; "no place is minor yet"
  becomes "the minor places are `['Karuizawa']`" (drop the `'minor' in p` assertion); the stub list's minor
  keys are `SMALL` plus Karuizawa; `P.list(realConfig()).length + 4`; the Himeji-alone case has 12 dots
  ("all twelve have a spot": they do); in the map-click test the no-station branch allows Karuizawa.
- **`test_blog_to_npc.py`** `test_city_reach`: the five names; Tokyo at `(48, 1)`.
- For accuracy (they pass as they are): the `['Tokyo', 'Market', 'Palace', 'Park']` loops in
  `stitched-city.test.js` (lines 46, 68) include Karuizawa (305 cells can be walked today, just over the
  300 asked of the others: give it a bound of its own, 150, since parts 2 and 3 change it).

Run, from `gamev2/` (prototype results in brackets):

```bash
node tools/test_game.js                  # [430 passed]
python3 tools/test_blog_to_npc.py        # [ok]
node tools/play.js check                 # [no problems found]
python3 tools/check_generators.py        # with Pillow [all ok; generate_ads / extract_city skip without a Japanese font]
python3 tools/sync_cities.py --check     # [in sync, 8 rooms]
python3 tools/rehearse_blog.py           # [313/313; 38 districts in 13 towns]
python3 tools/check_distinct.py          # Tokyo's row must not say WORSE (see Risks)
node tools/browser/regress.js            # not run in design: no browser
```

The browser regression names no Tokyo cell (its seam checks pick a seam at run time), so no assertion there
should need a change. By playing, desktop and a phone size, with screenshots: Tokyo -> through the gate ->
up the road -> back, stitched and with `?stitch=0`; bump the fingerpost; the Map with the Karuizawa dot at
320x780 and 390x844 (label does not cover Tokyo's); the camera at the city's new west edge.

## Risks and open questions

- **Serial map data**: this must not run alongside #255. If another place ticket lands first, its edits to
  `japan-map.test.js` (`SMALL`, `LANDING`, dot counts) and `districts` counts must be merged by hand, and
  `config.json` regenerated rather than merged.
- **Not checked here (no browser)**: the regression, the gate on screen, the Map labels on phones, frame
  time in the wider city (48 more columns of backdrop wood; chunk streaming should absorb it). The ticket
  should carry `workshop/needs:browser`.
- **`check_distinct.py` already exits 1 on `master`** (Asahikawa, Hokuriku, SanFranbourne, Sendai are worse
  than `distinct_baseline.json`; not caused by this). Running `--update` here would record that drift, so
  leave the baseline alone and judge Tokyo's row only.
- **Placeholder woods**: parts 2 and 3 change the generator's wood rectangles and tree kind; the seeded
  scatter will reshuffle then, which is expected. The district bounds and the LANDMARK row are theirs to
  extend.
- The backdrop leaves two bare grass rows between Karuizawa's south edge and the railway cutting; it reads
  as a cleared verge beside the line in the render. If it looks wrong in the browser, it is a `backdrop`
  matter for a later part, not a reason to move the room.
- No open question for the owner.
