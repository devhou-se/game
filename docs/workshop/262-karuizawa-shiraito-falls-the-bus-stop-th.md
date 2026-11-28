# Karuizawa part 3: Shiraito Falls, the bus stop, the corn stall and the larch art (#262)

Part of #256. Plan: `docs/workshop/68-featured-locations-everywhere-else-anyon.md`, "Karuizawa". Part 1 (#260)
is on master. Room touched: **Karuizawa** only (map data is serial: not at the same time as part 2, #261).
All paths are under `gamev2/`; all cells are Karuizawa's own.

## Context

Part 1 left a 48x40 room: the gate on the east edge, a dirt road west then north (columns 14-15, to row 10),
an empty clearing `(10..21, 5..11)` at its head, a fingerpost, and solid woods of `tree-green`, Tokyo's tree.
This ticket fills the clearing with what Damian and Julia came for (Shiraito Falls; "corn from a bus stop
vendor") and makes the woods larch. Outcome: you walk up the road to a waterfall over a pool with a bus stop
and a corn stall beside it, all three reachable; bumping the falls and the stall says a line, bumping the pool
fishes; the blog pipeline has two new named spots; every tree is Karuizawa's own.

## Approach

Prototyped in a scratch copy with draft art; the cells and numbers below are measured, not guessed
(`play.js lint Karuizawa`: 0 errors, 0 warnings; 276 walkable cells; all five no-browser checks and
`rehearse_blog.py` pass; no console error in a browser, desktop and phone).

- **Larch first.** Part 2 is not merged, so this ticket draws `karuizawa-larch` and swaps the generator's
  `LARCH` (the ticket lists the sprite). Two sprites of one family, a 2x3 and a 2x4, so the wood has a skyline.
- **The falls** is one static 8x3 sprite, solid all over, set into the north wood; the **pool** is the shared
  `pond-autotile` on the Water layer, three rows, the top one under the sprite's bottom row. The pool has **no
  north rim** (`edge-w`/`center`/`edge-e` where a rim would be): the white rocks would show through the falling
  water, and with no `pond-autotile_corner-nw` tile the generic `the pond` landmark row adds no second spot
  beside `Shiraito Falls`. The sprite's two end cells of its bottom row are rock arms on the bank, the cells a
  player can bump for the line; no cell that is both pool and falls has a walkable neighbour, so a bump never
  both fishes and talks.
- **The bus stop** is the shared `bus-stop` prefab (`bus-stop_0_0`): it is already in Tokyo, Market, Palace,
  Park and seven other towns, so it is common kit, not a borrow from one town, and the ticket lists no
  bus-stop art. No bump line (no town's stop has one).
- **The corn stall** is a 3x2 flavour prop with a line, not a shop (the catalogue has no corn; the plan asks
  for a stall, not a venue).
- **Posts are not moved here.** 544 and 572 are re-homed by the last part of #256; this ticket adds the
  `LANDMARKS` rows they will go to.
- Nothing is placed on the road north (rows 12..33) or its verges: part 2 lines it with shops.

`check_distinct.py`, Tokyo's row: buildings 0.155 -> 0.145, sprites 0.317 -> 0.308, own 55.7% -> 58.1%. Do
not run `--update`.

## Changes

**`tools/generate_karuizawa_art.py`** — add to `SPRITES` (half size, doubled, `outline`, as `fingerpost`;
reuse `blob`, `trunk` from `generate_sendai_art`, palette from `generate_hokkaido`; pond blues `425faa`,
`36508f`, `8ec2fa` as in `generate_kanazawa_art.py`; no lettering, the tool must not need a font):

| key | cells | px | what |
|---|---|---|---|
| `karuizawa-larch_0_0` | 2x3 | 128x192 | a November larch: a narrow cone of drooping tiers in gold (about `d9a441`, light `f2cf6b`, shade `a8742f`), bare trunk in the bottom cell, ground shadow and a few fallen needles as `ginkgo()` has. It must read as a conifer, not as `hokuriku-ginkgo` |
| `karuizawa-larch_0_1` | 2x4 | 128x256 | the same tree a row taller |
| `karuizawa-falls_0_0` | 8x3 | 512x192 | a low, wide rock face, mossy on top; hundreds of thin white threads come out of the face (not over its top) across the middle six columns and end in foam in the bottom row. Bottom row: columns 0 and 7 are rounded rock arms down to the ground; under columns 1..6 the last few pixel rows are transparent so the pool shows |
| `karuizawa-corn-stall_0_0` | 3x2 | 192x128 | a roadside stand, counter to the south: striped awning on two posts, a charcoal grill with cobs, a basket of corn in the husk |

`tileNames` label = the family (`karuizawa-larch` for both). Update the docstring's sprite list. The design
stage's prototype pictures on the ticket show sizes and placement only: their larch is too round, draw it
better.

**`tools/make_prefabs.py`** — `PREFABS`, beside the Hokuriku trees:

```python
'karuizawa-larch':      dict(w=2, h=3, sprites=[('Collidables', 0, 0, 'karuizawa-larch_0_0')], colliders=[(0, 2), (1, 2)], doors=[]),
'karuizawa-larch-tall': dict(w=2, h=4, sprites=[('Collidables', 0, 0, 'karuizawa-larch_0_1')], colliders=[(0, 3), (1, 3)], doors=[]),
'karuizawa-falls':      dict(w=8, h=3, sprites=[('Collidables', 0, 0, 'karuizawa-falls_0_0')], colliders=[(x, y) for y in range(3) for x in range(8)], doors=[]),
'karuizawa-corn-stall': dict(w=3, h=2, sprites=[('Collidables', 0, 0, 'karuizawa-corn-stall_0_0')], colliders=[(x, y) for y in range(2) for x in range(3)], doors=[]),
```

**`tools/hokuriku.py`** — `Kit.TALL` gains `'karuizawa-larch': 3, 'karuizawa-larch-tall': 4`.

**`tools/generate_karuizawa.py`** — keep `random.Random(260)` and the order of calls:

```python
LARCH = ['karuizawa-larch', 'karuizawa-larch', 'karuizawa-larch-tall']
FALLS = (12, 3)                   # the falls' tile cell: columns 12..19, rows 3..5
POOL = (13, 5, 18, 7)             # its pool; row 5 lies under the falls
BAY = (11, 9, 20, 10)             # where the bus turns, at the head of the road
STALL = (19, 6)                   # the corn stall's tile cell: its counter is row 7, bumped from row 8
STOP = (18, 8)                    # the bus stop

b.autotile('dirt-outside-autotile', sorted(set(<the two road rects> + rect(*BAY))))
...
b.stand('karuizawa-fingerpost_0_0', *POST)
b.stamp('karuizawa-falls', *FALLS)
x0, y0, x1, y1 = POOL
for x, y in rect(*POOL):          # no north rim: see the docstring
    we = 'w' if x == x0 else 'e' if x == x1 else ''
    role = (f'corner-s{we}' if we else 'edge-s') if y == y1 else (f'edge-{we}' if we else 'center')
    b.put('Water', x, y, f'pond-autotile_{role}')
    b.solid(x, y)
b.stamp('karuizawa-corn-stall', *STALL)
b.stamp('bus-stop', *STOP)
k.woods(0, 0, W - 1, 4, LARCH, rng)                 # as now
k.woods(0, 5, 9, H - 1, LARCH, rng)                 # as now
k.woods(20, 5, 21, 5, LARCH, rng, over=2)           # new: closes the two cells east of the falls' arm
...                                                 # the other four woods, the plants, dress, finish: as now
```

Docstring: `head` and `woods` rewritten (the falls, pool, bay, stop, stall; why no north rim; larch), the
"part 2" notes about larch dropped, `python3 tools/make_prefabs.py` added to the build order after the art
tool. Resulting open ground at the head: `(10..11, 5)`, `(10..12, 6..7)`, row 8 except `(18, 8)`, rows 9..11
of columns 10..21.

**`src/utils/Interactions.js`** — two rules beside the fingerpost's:

```js
{ kind: 'waterfall', group: 'flavour', pattern: /^karuizawa-falls/, footprint: true, say: 'hundreds of white threads slip out of the rock itself. no river above: the mountain just leaks' },
{ kind: 'corn-stall', group: 'flavour', pattern: /^karuizawa-corn-stall/, footprint: true, say: 'corn off the charcoal, brushed with soy sauce. next bus in forty minutes, which is about right' },
```

**`tools/blog_to_npc.py`** — `LANDMARKS`, after the fingerpost row:

```python
('karuizawa-falls_', 'Shiraito Falls', (1, 5), {'rooms': ('Karuizawa',)}),       # (13, 8): the bank, at the pool's south-west corner
('karuizawa-corn-stall_', 'the corn stall', (2, 2), {'rooms': ('Karuizawa',)}),  # (21, 8): at the east end of the counter
```

**`tools/districts.py`** — the `larch-road` description becomes "the packed-dirt road in from Tokyo's west
gate, through golden larch woods to Shiraito Falls, where the bus stops and a stall grills corn". Same key,
bounds and stand.

**`tools/check_generators.py`** — the `generate_karuizawa_art` comment names the new art and #262.

**Generated, committed with the above**: `config.json` (room, `spriteMetadata`, `tileNames`, palette appended,
`districts`), `assets/sprites/karuizawa-*.png`, `tiled/prefabs/karuizawa-*.tmj`, `tiled/karuizawa.tmj`,
`assets/map/world-map.{json,png}`. Build order:

```bash
python3 tools/generate_karuizawa_art.py && python3 tools/make_prefabs.py && python3 tools/generate_karuizawa.py
python3 tools/districts.py && python3 tools/config_to_tiled.py Karuizawa Tokyo && python3 tools/make_worldmap.py
```

**Docs** — `docs/landmarks-and-towns.md`, Karuizawa: "What is there now" (larch woods, the falls, pool, bay,
stop, stall with cells; the two bump kinds; fishing), "Blog pipeline" (three spots), build order
(`make_prefabs.py`). No `game.lookUp` entry (3 rows), no `Glows` row, no `train-track*` tile.

## Data and interfaces

- `config.json`: five new `spriteMetadata`/`tileNames` keys (`frameCount: 1`, anchors `32/w`, `32/h`), palette
  entries appended only, `rooms.Karuizawa` rebuilt (its NPCs and transporters kept), `districts.Karuizawa[0]`
  gets the new description and `spots: ['Shiraito Falls', 'the corn stall', 'the road from Tokyo']`.
- Interaction kinds `waterfall` and `corn-stall` (group `flavour`). Blog spots `Karuizawa · Shiraito Falls`
  `(13, 8)` and `Karuizawa · the corn stall` `(21, 8)`.
- No change to transporters, Tokyo, `devhouse.world`, `cities`, stations, the shop or the save.

## Tests

Extend `tools/tests/karuizawa.test.js` (helpers `tilesOf`, `solid`, `layer`, `worldWith` are there):

1. **Tiles**: exactly one each of `karuizawa-falls_0_0` at `12,3`, `karuizawa-corn-stall_0_0` at `19,6`,
   `bus-stop_0_0` at `18,8`, all on Collidables; `spriteMetadata` anchors for the four new sizes; the Water
   layer is exactly the 18 cells `(13..18, 5..7)`, all `pond-autotile_*`, none `corner-n*` or `edge-n`.
2. **Solid**: every cell of the falls `(12..19, 3..5)`, the pool, the stall `(19..21, 6..7)`, `(18, 8)` and
   `(20..21, 5)`.
3. **Reachable on foot** (the ticket's test): flood-fill from the gate's landing cell over non-solid cells, as
   the gate test does; it contains `(12, 6)` and `(11, 5)` (beside the falls' arm), `(13..17, 8)` (the pool's
   bank), `(19..21, 8)` (the stall's counter), `(17, 8)`, `(18, 9)` (beside and below the bus stop), and both
   spot cells `(13, 8)`, `(21, 8)`.
4. **Bumps**, stitched and `?stitch=0` (`world.enter(KEY, x, y); world.step(dir)`), each `moved === false`:
   `(12, 6)` n and `(11, 5)` e -> `waterfall`/`flavour`; `(15, 8)` n and `(12, 6)` e -> `pond`/`pond`;
   `(20, 8)` n -> `corn-stall`/`flavour`; `(18, 9)` n -> no interaction. Both lines are 100 characters or less.
5. **Never both**: no cell that is on the Water layer and inside the falls' footprint has a non-solid
   neighbour.
6. **Own art**: no tile of the room starts `tree-`; every Collidables key is `karuizawa-*`,
   `shrub-small-circle_0_0` or `bus-stop_0_0`; both larch sprites are used.
7. **Pipeline**: `blog_to_npc.py` holds the two rows verbatim; `cfg.districts.Karuizawa` is
   `[['larch-road', ['Shiraito Falls', 'the corn stall', 'the road from Tokyo']]]`.
8. **Two assertions of the #260 fingerpost test change on purpose**: the `/sign|bus-stop/` list becomes
   `[['bus-stop_0_0', '18,8', 'Collidables']]`, and the districts line as in 7. The other #260 tests (gate,
   road cells, the walk to `(14, 12)`) must pass unchanged.

`tools/test_blog_to_npc.py` needs no new case: `test_spots` and `test_districts` already require every
room-scoped label to be found and the districts to be regenerated.

Run from `gamev2/` (art tools need Pillow: a venv with `pip install -r tools/requirements-art.txt`):

```bash
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check
<venv>/bin/python tools/check_generators.py && python3 tools/sync_cities.py --check
python3 tools/rehearse_blog.py && python3 tools/check_distinct.py
node tools/play.js lint Karuizawa Tokyo TokyoCity && node tools/play.js render Karuizawa out.png
REGRESS_TIME_SCALE=2 PORT=<port> node tools/browser/regress.js     # tools/browser/README.md
```

The regression names no Karuizawa cell; no check is added to it. Then play it: in a browser at 1280x960 and at
a landscape phone size with touch (844x390, `?touch=1`), put the player in the room
(`game.scene.keys.GameScene.roomManager.switchRoomInstant('Karuizawa', x, y)`, or walk in from Tokyo's west
gate), walk to `(12, 6)` and `(20, 8)`, bump the falls and the stall, and look at the screenshots of both on
both sizes (save them to `/work/media/`).

## Risks and open questions

- **The art is the risk.** The falls must read as water coming out of a rock face over a pool, and the larch
  as a gold conifer; judge both on the screenshots, at the phone size too, and redraw rather than ship a
  draft.
- **Part 2 (#261)** rebuilds the same room: whichever lands second rebases and re-runs the generator. It
  should use this ticket's `LARCH` and leave the head `(10..21, 3..11)` alone.
- **The pool's missing north rim is deliberate.** Completing it adds a `the pond` spot to the room and puts
  rocks under the water; test 1 pins it.
- Karuizawa's gold wood meets the city's green backdrop trees past its north and south edges, as Hokuriku's
  woods do. Seen in the prototype: the room's top rows are mostly shrubs, a grass strip lies south of it, and
  neither edge reads as a fault.
- Assumed, not asked: posts 544 and 572 stay where they are until the last part of #256, and the stall sells
  nothing. Either can be added later without moving anything built here.
