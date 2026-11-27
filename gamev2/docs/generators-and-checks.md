# Generators, check_generators, the world map and asset generation

Room generators as the source of truth, `tools/check_generators.py`, `tools/make_worldmap.py` and the tile / art generators.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## check_generators.py

`python3 tools/check_generators.py [generator ...]` checks that the room generators still rebuild the
committed world: it runs each one in a scratch copy and fails, naming the rooms and cells, if `config.json`
would change (issue #107, see "Generated rooms stay regenerable"). It also re-seeds every room with
`config_to_tiled.py` and fails if a committed `tiled/*.tmj` would change (a config edit whose map was not
re-seeded), and runs the art / prefab tools (`make_prefabs`, `generate_hokkaido`, `_sendai_art`, `_fukuoka_art`, `_hokuriku_art`, `_sapporo_art`, `_sanfranbourne_art`, `_tsutenkaku`,
`_discount_art`, `_cooler_art`, `_station_art`, `_house_art`, `_shrine_art`, `make_snow_tiles`, `make_road_tiles`, `generate_ads`, `generate_cast`, the
`extract_*.py` scripts, `extract_station` among them) and fails if `assets/sprites`, `assets/ads`, `assets/map`, `tiled/prefabs` or `config.json` would
change (issues #186, #193). Run it after any edit to a
generated room, a map or a generator. The room and map checks take a few seconds and need no Pillow; the
art tools are listed as `skip` without it, so use `/Library/Developer/CommandLineTools/usr/bin/python3
tools/check_generators.py` to cover them (ten seconds; `generate_ads` and `extract_city` also need a Japanese system font,
see `generate_ads.find_font`, and are listed as `skip`, not checked, where none is readable — a sandboxed shell).

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
- **The baseline** (26 Nov 2026, buildings / sprites / own): Tokyo 0.22 / 0.32 / 52%, Hokuriku 0.27 / 0.54 / 40%,
  Sendai 0.23 / 0.54 / 29%, Fukuoka 0.29 / 0.45 / 26%, Sapporo 0.07 / 0.20 / 77% (after stages 1-3 of its rebuild: it passes all three targets; it was 0.50 / 0.49 / 12%, and 0.30 / 0.29 / 63% after stage 2), Osaka 0.50 / 0.45 / 11%,
  Asahikawa 0.67 / 0.75 / 10%. `--update` records today's numbers: do it when a rebuild made a city better or
  a new town landed, and say so in the commit. Never to hide a city getting worse.
- Machi, Inaka and Yukimura (being deleted) are compared against, as the audit did, and not judged: several
  cities' worst pair today is Machi, so deleting it improves them.
- A new town's own landmark art counts as building sprites once its sprite prefix is in `LANDMARK_ART`.
- It is not one of the five gates: run it after a town's map or generator changes. Unit test: `test_distinct`
  in `tools/test_blog_to_npc.py`.

## Generated rooms

- **Generated rooms stay regenerable** (issue #107): a room generator re-run on an unchanged world leaves
  `config.json` byte-identical, and `python3 tools/check_generators.py` fails when one would not. That
  holds for `generate_machi`, `_inaka`, `_yukimura`, `_osaka`, `_sapporo`, `_asahikawa`, `_sendai`, `_fukuoka`,
  `_kanazawa`, `_shirakawago`, `_toyama`, `_airports`, `_sanfranbourne`, `_konbinis`,
  `_discount_stores`, `_stations`, `_izakaya` (the Izakaya interior plus its street door,
  lantern pair and two pinned ad boards in Market, see Shop, Food and Drink), `_houses` (every house
  interior and its door, see House interiors) and `_shrines` (the worship halls and the doors into
  them, see "Shrine worship halls" in `landmarks-and-towns.md`), each run on its own. (The four that take
  town names - `_houses`, `_shrines`, `_konbinis`, `_discount_stores` - read their command line through
  `roomgen.cli`: `--help` / `-h` prints the tool's docstring and an unknown option is an error, exit 2,
  both before the config is loaded, so neither is taken for "no town named" and run for real, issue
  #220. The town generators take no arguments and ignore any.) What keeps a re-run a no-op:
  - a town generator ends with `b.finish()` (`roomgen.Builder`), which runs the picket-fence and
    solid-track passes itself — `fix_fences.py` / `seal_tracks.py` are the same code
    (`roomgen.picket_fences` / `roomgen.seal_tracks`) for a room named on the command line, and are no
    longer a step to remember after a town generator;
  - it keeps what it does not own from the room as it stands: NPCs (the blog pipeline's states), Machi's
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
  edit the next time someone runs it. (That is what had happened to `generate_machi.py`: it wiped the blog
  NPCs, the signage and the stitched city's gate colliders, and resurrected the legacy `Konbini` room.)
  Ported rooms (Tokyo, Market, Park, Palace) have no generator; their map is the source of truth.
- `tools/generate_stations.py` keeps an existing station room's NPCs (the blog pipeline parks dated NPC
  states there), and `tools/seal_tracks.py` takes room names; a track cell with a road under it (Palace's level
  crossing) is left open.

## The world map

- **The world map shows the stitched city** (issue #146): after the rooms are drawn, `tools/make_worldmap.py`
  renders each config `cities` entry with `node tools/play.js render <City>` — the room the game plays,
  woodland and seam patches included — and pastes it over the city's bounding box. **The train-only towns
  stand clear of that box in `devhouse.world`** (issue #174: Yukimura above Machi, Inaka and Osaka in a
  column west of it; they used to sit inside the box and showed as clearings in Tokyo's woods). The tool
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
maps that already place it - change the art, not the footprint. Needs Pillow.
