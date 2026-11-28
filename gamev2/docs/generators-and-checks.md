# Generators, check_generators, the world map and asset generation

Room generators as the source of truth, `tools/check_generators.py`, `tools/make_worldmap.py` and the tile / art generators.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## check_generators.py

`python3 tools/check_generators.py [generator ...]` checks that the room generators still rebuild the
committed world: it runs each one in a scratch copy and fails, naming the rooms and cells, if `config.json`
would change (issue #107, see "Generated rooms stay regenerable"). It also re-seeds every room with
`config_to_tiled.py` and fails if a committed `tiled/*.tmj` would change (a config edit whose map was not
re-seeded), and runs the art / prefab tools (`make_prefabs`, `generate_hokkaido`, `_sendai_art`, `_fukuoka_art`, `_hokuriku_art`, `_sapporo_art`, `_sanfranbourne_art`, `_tsutenkaku`,
`_discount_art`, `_cooler_art`, `_konbini_art`, `_seven_eleven_art`, `_station_art`, `_house_art`, `_shrine_art`, `make_snow_tiles`, `make_road_tiles`, `generate_ads`, `generate_cast`, the
`extract_*.py` scripts, `extract_station` among them) and fails if `assets/sprites`, `assets/ads`, `assets/map`, `tiled/prefabs` or `config.json` would
change (issues #186, #193). Run it after any edit to a
generated room, a map or a generator. The room and map checks take a few seconds and need no Pillow; the
art tools are listed as `skip` without it, so use `/Library/Developer/CommandLineTools/usr/bin/python3
tools/check_generators.py` to cover them (ten seconds; `generate_ads` and `extract_city` also need a Japanese system font,
see `generate_ads.find_font`, and are listed as `skip`, not checked, where none is readable — a sandboxed shell).

The `extract_*.py` tools cut their sprites from the source sheets in `../art-source/GuttyKreum` (the
repository's `art-source/`, beside `gamev2/`; its `README.md` lists the sheets and how to bring back another
one from history). `check_generators.py` links that folder beside its scratch copy, so the tools find it there
too. A sheet a tool reads is added to `art-source/` and to `SHEETS` in `tools/tests/repo-layout.test.js`.

**A PNG is compared by its decoded pixels, not its bytes** (`same_picture`, issue #230): the same size and the
same RGBA values. The bytes of a PNG also depend on the zlib that Pillow was built with, so the same picture
is a different file from one machine to the next, and a byte comparison passed only on the machine that wrote
the art. `config.json`, the `.tmj` maps and the prefabs are still compared byte for byte. So any `python3`
with a Pillow that draws the same pixels will do, not only the macOS one:

- The Checks workflow installs the release pinned in `tools/requirements-art.txt` (`pip install -r tools/requirements-art.txt`);
  move the pin only together with the art it changes.
- **Pillow 11.2 to 13.0 rebuild the committed art** (11.2.1, 11.3.0, 12.0.0, 12.1.1, 12.3.0 and 13.0.0 were
  run on Linux on 27 Nov 2026, every art tool but the two that need a Japanese font).
- **Pillow 11.1 and older do not**: they draw some curves and slanted lines a pixel off, and the check reports
  `DRIFT` for 8 to 15 sprites (`sendai-cedar`, `palace-in-fusuma-tiger`, ...). That is Pillow, not the tool:
  use a newer one. When an art tool drifts the check prints the Pillow version it ran on.
- A new Pillow can move a pixel too. Pillow 13 fills the one-column middle of a rounded rectangle that older
  ones left empty, which changed the cabin windows of `plane-interior`; `generate_sanfranbourne_art.py` now
  draws that column itself, so the picture is the committed one on either. Do the same when a new Pillow
  moves something: draw the committed pixels with rectangles and points, do not regenerate the art to suit one
  version.

**Rooms and maps are one to one** (`unmatched_maps`, issue #243): under `config_to_tiled` the check also fails
for a `tiled/<name>.tmj` that no room in `config.json` has (`... has no room in config.json: delete it`) and
for a room with no map (`room <Key> has no tiled/<key>.tmj: run config_to_tiled.py <Key>`). A map nobody
loads is otherwise invisible: Tiled and `devhouse.world` still show it, and nothing else fails. The interior
generators delete the map themselves when a building goes (see "Interior building blocks"), so the first
line means a room was deleted by hand.

`tools/districts.py` is one of the generators checked: it writes config `districts` (the named areas of every
town, `landmarks-and-towns.md` "Districts") from its own `DISTRICTS` list and each landmark's standing cell,
so a map change that moves a landmark across a district's edge shows as `DRIFT districts.py`: re-run it.

## check_distinct.py: is each city still its own?

`python3 tools/check_distinct.py` prints, per city (a stitched city's districts as one; stations and
interiors left out), the measure from the city audit (issues #210, #219):

| Number | What it is | Target |
|---|---|---|
| `buildings` | the highest Jaccard overlap (shared / all of the pair) of its building sprites with any other city's, and which city | 0.25 or less |
| `sprites` | the same over every sprite, ground and shared kit included | 0.40 or less |
| `own` | the share of its building and scenery sprites (no ground, no shared kit) used in no other city | a third or more |

A sprite is a tile family (`grass-autotile_edge-n` -> `grass-autotile`, `torii-red-top` + `-feet` ->
`torii-red`, `building-roof-blue` -> `house-blue`); the shared kit (7-Eleven, vending machines, roads,
crossings, traffic lights, track) counts neither for nor against a city.

- **It does not fail on the targets.** Today only Tokyo passes them; the others miss by design until each is
  rebuilt (issue #219). It exits 1 only when a city is **worse than the baseline**, `tools/distinct_baseline.json`:
  a higher overlap or a lower own share than recorded. A city that is not in the baseline (a new town) is
  printed against the targets and does not fail.
- **The baseline** (27 Nov 2026, buildings / sprites / own): Tokyo 0.16 / 0.32 / 55%, Hokuriku 0.27 / 0.54 / 40%,
  Sendai 0.23 / 0.54 / 29%, Fukuoka 0.25 / 0.45 / 26%, Sapporo 0.07 / 0.19 / 77% (after stages 1-3 of its rebuild: it passes all three targets; it was 0.50 / 0.49 / 12%), Osaka 0.20 / 0.45 / 11%,
  Asahikawa 0.27 / 0.20 / 10%, San Franbourne 0.20 / 0.32 / 69%. `--update` records today's numbers: do it when a rebuild made a city better or
  a new town landed, and say so in the commit. Never to hide a city getting worse.
- Every town is judged: the made-up towns (Machi, Inaka, Yukimura), which were compared against and not judged,
  are deleted (issue #68). Several cities' worst pair was one of them, which is why the building overlaps of
  Asahikawa, Osaka, Sapporo, Fukuoka and Tokyo fell in the 27 Nov baseline with no map of theirs changing.
- A new town's own landmark art counts as building sprites once its sprite prefix is in `LANDMARK_ART`.
- It is not one of the five gates: run it after a town's map or generator changes. Unit test: `test_distinct`
  in `tools/test_blog_to_npc.py`.

## Generated rooms

- **Generated rooms stay regenerable** (issue #107): a room generator re-run on an unchanged world leaves
  `config.json` byte-identical, and `python3 tools/check_generators.py` fails when one would not. That
  holds for `generate_osaka`, `_sapporo`, `_asahikawa`, `_sendai`, `_fukuoka`,
  `_kanazawa`, `_shirakawago`, `_toyama`, `_airports`, `_sanfranbourne`, `_konbinis`,
  `_discount_stores`, `_stations`, `_izakaya` (the Izakaya interior plus its street door,
  lantern pair and two pinned ad boards in Market, see Shop, Food and Drink), `_houses` (every house
  interior and its door, see House interiors) and `_shrines` (the worship halls and the doors into
  them, see "Shrine worship halls" in `landmarks-and-towns.md`) and `_devhouses` (the ten floors of
  the two Devhouses, their stairs and their street doors in Park and Osaka, issue #69, see "The Devhouses of
  Tokyo and Osaka" there), each run on its own. (The four that take
  town names - `_houses`, `_shrines`, `_konbinis`, `_discount_stores` - read their command line through
  `roomgen.cli`: `--help` / `-h` prints the tool's docstring and an unknown option is an error, exit 2,
  both before the config is loaded, so neither is taken for "no town named" and run for real, issue
  #220. The town generators take no arguments and ignore any.) What keeps a re-run a no-op:
  - a town generator ends with `b.finish()` (`roomgen.Builder`), which runs the picket-fence and
    solid-track passes itself — `fix_fences.py` / `seal_tracks.py` are the same code
    (`roomgen.picket_fences` / `roomgen.seal_tracks`) for a room named on the command line, and are no
    longer a step to remember after a town generator;
  - it keeps what it does not own from the room as it stands: NPCs (the blog pipeline's states), a room's
    ad `signage`, and a 7-Eleven door wired by `generate_konbinis.py` (`roomgen.kept_door`; with none to
    keep, on a first build, the door is sealed until `generate_konbinis.py <Host>` runs). Doors are listed in
    the order the room already has them (`roomgen.kept_order`; the shop generators replace their door in
    place), so a first build followed by the shop generators also passes the check. House doors and
    shrine-hall doors are the one thing a town generator keeps without knowing it: `roomgen.save_config`
    puts them back (`keep_house_doors`, which keeps the door of every kind of interior in
    `roomgen.OWNED_DOORS`; issues #208 and #212, see House interiors and Shrine worship halls).
  So a generated room may be changed either way — edit the generator and re-run it, or make a surgical
  edit (`/adjust-game`, `stamp_prefab.py`) **and mirror it in the generator** — and the check tells you if
  the two have come apart. Never leave it failing: a generator that has drifted silently drops the hand
  edit the next time someone runs it. (That is what had happened to the generator of Machi, a town since deleted: it wiped the blog
  NPCs, the signage and the stitched city's gate colliders, and resurrected the legacy `Konbini` room.)
  Ported rooms (Tokyo, Market, Park, Palace) have no generator; their map is the source of truth.
- `tools/generate_stations.py` keeps an existing station room's NPCs (the blog pipeline parks dated NPC
  states there), and `tools/seal_tracks.py` takes room names; a track cell with a road under it (Palace's level
  crossing) is left open.

### Interior building blocks

A new interior is a short script that puts shared blocks together and adds only its own art and layout
(issue #224). Three layers, the lowest first:

1. **Primitives on `roomgen.Builder`** (room coordinates; towns use them too): `solid(x, y, w, h)`, a collider
   over a rect; `place(layer, x, y, key, solid)`, a sprite and a collider on each listed offset
   (`rg.block(w, h, y0)` makes the offsets); `prop(key, x, y, w, h)`, a sprite on its top-left cell with a
   `w`x`h` footprint, always given (`*rg.sprite_cells(key)` is the sprite's own size, rounded);
   `stand(key, x, foot, w, h)`, a piece `h` rows tall of which only the `foot` row is solid, so it is walked
   behind; `railing_row(y, taken)`, the tube railing in every gap of a row (stations, airports). Beside them
   `rg.png_size`, `rg.register_metadata(cfg, keys)` and `rg.find_sprites(room, keys)` (every tile of a room
   with one of those keys, in the `(y, x)` order stores and halls are numbered in). One meaning per name: a
   generator defines no `solid`, `prop` or `stand` of its own, and the only local `place` is a town
   generator's one line that adds `_0_0`.
2. **The door in the host room**, in `roomgen.py` beside the kept-door rules: `rg.open_door(host_room, cell,
   target, arrive)` takes the doorway's collider off and pins a hidden transporter onto it; `rg.pin(items,
   item)` is the rule under it (replace the entry on that cell where it sits, delete later ones, append only
   a new one, so a re-run moves nothing); `rg.shut_door(host_room, cell, prefix)` takes the transporter
   into a `<prefix>...` room off the cell, and seals the cell only where a doorway of that kind
   (`OWNED_DOORS`) still stands on it and no other door is left there, so the cell of a building that is
   gone stays as the town left it. **When a building goes** (issue #243): a generator that numbers its rooms
   per town ends its run with `rg.drop_stale(cfg, host, prefix, opened, stale)`, which shuts every door of
   that prefix on a cell the run did not open (`opened`), deletes the rooms in `stale` (the ones of that host
   the run did not build: the highest numbers, since the rest are renumbered) and returns the `shut` /
   `removed` lines to print, a room's NPCs named if it had any. `rg.save_config` then deletes
   `tiled/<key>.tmj` of every room that was loaded and is not saved (`deleted  tiled/...`). It never deletes
   through a symlinked `tiled/` (a test's scratch copy linking the committed maps): the map is printed as
   `kept` instead. Nothing is deleted on a `--dry-run`, which does not save.
3. **The shell, `tools/interiors.py`**: `Interior(fw, fh)` is a room of void with a `fw`x`fh` floor, and every
   call on it is in **floor coordinates** (`(0, 0)` the floor's top-left cell, row `-1` the wall above it, row
   `fh` the row below it). A generator calls, in this order: `floor(key_of)`; `back_wall(pieces, depth)`,
   `side_walls(west, east, above)`, `front_wall(key, gap, thresholds)` if it has them (the two wall tops are
   Floor tiles in place of the void, or with `layer='Over Floor'` art laid over it, as a 7-Eleven's); `prop` /
   `stand` / `place` / `put` for its furniture (the Builder's calls, moved to the floor; `put` takes whole
   palette keys, so a piece-name mapper stays in the generator); `doorway(fx, host, front)`, which adds the
   exit cells and returns where you arrive from the street; and `room(name, **flags)`, which lists the exits
   in the order `doorway` was called, draws the boundary round `walk` (`interiors.outline`) and fails if a
   floor cell cannot be reached from the exits (a cell closed on purpose goes in `pockets=`). The room is at
   least 20x15 and a small floor is centred in it; `ox`, `oy`, `w`, `h` place it by hand. `it.walk` (room
   cells) is the generator's to add to: a genkan, the arcade's corridors, the storeys and stairs over a
   pagoda's ground floor. `back_wall(..., view=True)` puts the wall inside the boundary too (`it.view`,
   solid cells nobody walks): a phone's camera holds a room no taller than its view to the boundary, so
   round the floor alone it cuts a tall back wall off the top of the screen (the 7-Elevens). Also there:
   `interiors.named(cfg, label, host, n)` for "Label · Town 2" and `interiors.seed_of(text)`.

The whole of a new interior but its art and its `OWNED_DOORS` row (`tools/tests/generator-blocks.test.js`
builds exactly this block, without the save, so it cannot rot):

```python
import roomgen as rg
from interiors import Interior

cfg = rg.load_config()
HOST, DOOR, KEY = 'Market', (7, 37), 'TeaRoomMarket1'          # an example, not a room to add
it = Interior(10, 6)                                           # a 10x6 floor, centred in a 20x15 room
it.floor(lambda fx, fy: 'office-warm-autotile_center')
it.back_wall([(fx, 'office-wall-white_0_0', 1) for fx in range(10)], depth=1)
it.prop('office-counter2_0_0', 6, 0, *rg.sprite_cells('office-counter2_0_0'))
inside = it.doorway(4, HOST, (DOOR[0], DOOR[1] + 1), mat='office-warm-autotile_center')
cfg['rooms'][KEY] = it.room('Tea Room', npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
                            shopEnabled=False, tearoom={'host': HOST, 'door': list(DOOR)})
rg.open_door(cfg['rooms'][HOST], DOOR, KEY, inside[0])
rg.save_config(cfg)
```

What a new interior has to decide beyond that:

- **Who keeps its door through a town rebuild**: a row in `roomgen.OWNED_DOORS` and a `{host, door}` marker on
  the room (the `tearoom=` above), or `roomgen.kept_door` in the town's own generator.
- **What happens when its building is removed**: if its rooms are numbered per town, it calls
  `rg.drop_stale` before it saves (above), and a run with no argument also visits a host that a marker
  names and no door is wired in any more (`generate_shrines.wired_hosts`), so the town that lost its only
  one is cleaned up too. `tools/tests/stale-interiors.test.js` has a case per generator: add one.
- **`shopEnabled=False`, unless it is a store.** `interior: true` alone makes every counter a konbini's
  (`Interactions.js`, `Energy.isStore`). `room()` sets `interior` and nothing else.
- `lanternLight` / `shopMenu` if it wants them, and a rule in `Shop.VENUES` / `Interactions.js` for anything a
  bump should open. `daylight` for a room that is all window (Fukuoka Tower's deck): it is graded by the hour
  as the street is (`DayNight.gradeFor`).
- **Who draws the mat**: a `front_wall` threshold, or `doorway(mat=<Floor key>)` (or `mat=key_of`, as
  `floor` takes, where the cells differ). `doorway` draws nothing otherwise, and an exit cell left on the
  void is invisible.
- Its generator goes in `check_generators.GENERATORS`. Every file listed there is read by
  `generator-blocks.test.js`, which fails on a hand-wired door, a PNG header read, or a local `outline`,
  `stand` or void fill.

Changing a block changes every generator on it: `check_generators.py` proves the committed rooms, not the
rooms the next town will ask for (a konbini's plan is dealt from its door). Before changing `Interior` or a
primitive, build rooms from made-up inputs with the old code (`build_interior` of the konbinis, discount
stores, houses and shrines takes any door or seed), keep their digests, and compare after.

## The world map

- **The world map shows the stitched city** (issue #146): after the rooms are drawn, `tools/make_worldmap.py`
  renders each config `cities` entry with `node tools/play.js render <City>` — the room the game plays,
  woodland and seam patches included — and pastes it over the city's bounding box. **The train-only towns
  stand clear of that box in `devhouse.world`** (issue #174: Osaka used to sit inside the box and showed as a clearing in Tokyo's woods). The tool
  warns if a town is ever placed back inside (it is still redrawn on top), and `tools/test_game.js` fails.
  **The world file is laid out like Japan** (issue #68, north up; compass order, not true distance): Asahikawa
  north-east of Sapporo, both north of the Tokyo city, Osaka west-south-west of Tokyo, and no two detached
  maps overlapping — `tools/tests/map-data.test.js` holds it (Fukuoka, far south-west of Osaka: `fukuoka.test.js`). A new town goes at its compass position; moving
  a detached town changes nothing but the Map (`cities` offsets are the stitched districts' only).
  Widening the world costs nothing on the Map screen while it stays wider than about 1.47:1 - the
  overlay is height-limited. `world-map.json` keeps the same contract (one rect per room). **The game's Map overlay no longer shows
  this picture** (issue #211: it is a map of Japan, below); the studio's world layout, `CityStitcher`'s boot check,
  `TrainTravel.dirTo` and the map-data tests still read it. Regenerate
  `assets/map` with the tool whenever a district, `cities.<City>.backdrop` or `patch` changes.
- **The Map overlay's picture of Japan** (issue #211): `tools/make_japan_map.py` (Pillow, in `ART_TOOLS`;
  `assets/map` is one of `check_generators`' compared `OUTPUTS`) draws `assets/map/japan.png` from
  hand-authored coastlines in the tool (`ISLANDS`: Hokkaido, Honshu, Shikoku, Kyushu and ten small islands,
  as simplified lon / lat polygons — nothing is downloaded): sea with shallows, an ink coast, lowland / hill /
  mountain greens from the distance inland plus hash noise, a little snow on the highest ground, in the
  beach and grass tiles' colours. `assets/map/japan.json` is the contract `Places.project` reads —
  `lon0`, `lat0` (the NORTH edge), `pxPerLon`, `pxPerLat` (equirectangular, squeezed east-west by
  cos 38°), and the `islands` outlines, which `japan-map.test.js` uses to hold every town's `geo` on
  land. Change a coastline or the bounds there and re-run it; the dots follow the json. `--preview out.png`
  writes a 3x picture and nothing else.
- **World map without Tiled**: `tools/make_worldmap.py` uses `tmxrasterizer` when Tiled is installed and
  otherwise (or with `--pil`) draws the rooms itself via `node tools/play.js render`, which is also the
  "look at the render" step for a new room: `node tools/play.js render <Room> out.png [--scale .5] [--colliders]`.

## Asset Generation

Python scripts in `tools/` directory generate 64×64 PNG tiles saved to `assets/`:
- `generate_tile.py` - Player tile (yellow border) → `assets/single-tile.png`
- `generate_npc_tile.py` - NPC tile → `assets/npc-tile.png`
- `generate_transporter_tile.py` - Transporter tile (green border) → `assets/transporter.png`
- `generate_object_tile.py` - Object tile (black border) → `assets/object-tile.png`
- `generate_grid.py` - Background grid → `assets/background-grid.png`

Run with: `python3 tools/generate_<type>.py`

`tools/generate_cooler_art.py [--preview out.png]` draws `office-fridge_0_0`, the konbini's upright
glass-door drinks cooler (issue #140): 1x2 cells, fully procedural (no source image or font, so a re-run is
byte-identical), in the steel greys and glass blues of the `office-shelf-*` / `office-freezer` furniture
and, like them, drawn at half size and pixel-doubled. Size (64x128) and anchor (0.5, 0.25) are fixed by the
maps that already place it - change the art, not the footprint. Needs Pillow. In a 7-Eleven it stands
against the back wall, its upper cell over the wall's lower row (issue #221).

`tools/generate_konbini_art.py [--preview out.png]` draws the rest of a 7-Eleven's interior, the 26
`konbini-*` sprites (issue #221): the checkered floor, the wall-top edges, the two-row back wall (plain,
with the clock, with the tobacco rack), the counter nook with its clerk (`-w`, and `-e` its mirror), the
open chillers, the coffee machine, the water dispenser, the cash machine, the copier, the four shelf
blocks, the ice-cream chest, the magazine rack, the baskets and the mat. Fully procedural, so a re-run is
byte-identical; it writes each sprite's `spriteMetadata` and `tileNames` and `generate_konbinis.py`
appends the keys to the palette as it places them. Sizes are whole cells and are what the plans in
`generate_konbinis.py` assume - change the art, not the footprint. Needs Pillow.

`tools/generate_seven_eleven_art.py [--preview out.png]` draws `seven-eleven_0_0`, the 7-Eleven on the
street (issue #89): 3x4 cells, a two-storey store front on - a flat roof, an upstairs flat, the white fascia
with the orange / green / red stripes and the 7 of the back wall inside, a lit glass shopfront and the
sliding doors on the middle cell of the bottom row, the cell the `seven-eleven` prefab leaves open. **It is a
placeholder**: it took the place of the white line drawing ported from the Godot game, and the store is
still waiting for hand-made art (the issue stays open, `needs-art`). A PNG drawn by hand replaces
`assets/sprites/seven-eleven_0_0.png` at the same 192x256; take the tool out of `check_generators.ART_TOOLS`
(and delete it) in the same commit, or the check reports the hand-made picture as drift, and keep only the
size, anchor and door of its case in `tools/tests/konbini.test.js`, which also counts this picture's colours.
Fully procedural,
in the konbini kit's palette, and drawn with rectangles and points only, so a re-run draws the same pixels on
any Pillow. Size and anchor are fixed by the maps of every town that places it - change the art, not the
footprint - and the tool does not touch `config.json`. Needs Pillow.

`tools/generate_devhouse_art.py [--preview out.png]` draws the 37 `devhouse-*` sprites (issue #69): the two
buildings (`devhouse-tokyo_0_0` 5x8, `devhouse-osaka_0_0` 3x7; their prefabs are in `make_prefabs.py`), the
stair tiles, the wet-room tile, gravel and stepping stone, the partitions, the locked door and the bamboo
fence of the back wall, and the furniture and garden pieces the home kit did not have. Fully procedural, and
drawn with rectangles and points only (no Pillow ellipse, polygon or slanted line, which move by a pixel
between Pillow versions), so a re-run draws the same pixels on any Pillow; it writes each sprite's
`spriteMetadata` and `tileNames`, and `generate_devhouses.py` appends the keys to the palette as it places
them. Sizes are whole cells and are what the floor grids assume. Needs Pillow.
