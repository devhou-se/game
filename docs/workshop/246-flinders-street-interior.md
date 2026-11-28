# Design: the inside of the station with the clocks in San Franbourne (#246)

All paths are under `gamev2/` unless they start with `docs/workshop/`. Read `gamev2/CLAUDE.md`,
`docs/generators-and-checks.md` ("Interior building blocks") and `docs/landmarks-and-towns.md` ("The Sendai pub",
"Canal City's atrium") first: this is one more room of that kind (#217), and `tools/generate_mall.py` (two door
cells, station-kit furniture) is the file to copy.

## Context

The owner's ticket is "Flinders Street interior": the yellow station with the clocks in San Franbourne
(`sfb-clocks-station_0_0`, 12x7 cells, standing at `(13, 39)` in room `SanFranbourne`) is a sealed box. Its three
door leaves are drawn in the bottom row of the sprite, cells `(5, 6)` and `(6, 6)` = room cells `(18, 45)` and
`(19, 45)`; both carry a `gk_blank` collider today and a bump anywhere on the building says "everybody meets under
the clocks. nobody has ever caught a train here". The cells in front, `(18, 46)` and `(19, 46)`, are open boardwalk;
the town has no NPCs (`blog: False`).

Outcome: you walk in through the doors under the clocks into a room of its own, a station concourse in the
building's mustard and maroon, with the clocks inside too, ticket gates, a platform and an empty track; you walk
back out onto the boardwalk in front of the door you came in by. No train: San Franbourne stays reachable only by
air and on no departures board.

## Approach

Follow the #217 pattern exactly; the town generator's logic is not edited.

- The door is found from the sprite (`rg.sprite_doors`) and wired by `rg.open_door`; a row in
  `roomgen.OWNED_DOORS` plus a `flinders: {host, doors}` marker on the room keeps it through a rebuild of the town.
- The room is built in the `interiors.Interior` shell by a new generator, `tools/generate_flinders.py`, from a new
  art tool, `tools/generate_flinders_art.py` (the pub's frame functions with a mustard palette, as the distillery
  and the mall do), plus the existing station kit (`station-*` floors, track, gates, railing, benches, planters:
  the mall already reuses the kit). The Japanese-labelled kit pieces are not used (`station-kiosk`,
  `-ticket-machines`, `-departures`, `-platform-sign`, `-postbox`, `-name-*`, `-exit-sign`, `-board-*`), nor is
  `station-lamp-post`.
- It is an `interior`, not a `config.stations` room: nothing to ride, no `stations` entry, no board row.
- What a bump does is three rows in `src/utils/Interactions.js`. The clocks inside open Time Travel, as every other
  clock in the game does (`group: 'clock'`); the building outside keeps its line.
- No lantern light, no `Glows.js` rows, no Shop venue, no new overlay, key or save field (the mall has none either).

Names: room key `FlindersSanFranbourne1`, room name `Flinders St` (11 characters: the HUD's one-row limit), key
prefix `Flinders`, marker `flinders`, sprite prefix `flinders-in-`.

## Changes

### `tools/roomgen.py`

Beside the mall's rows:

```python
FLINDERS_DOORS = {'sfb-clocks-station_0_0': [(5, 6), (6, 6)]}
FLINDERS_PREFIX = 'Flinders'          # rooms.Flinders<Host><n>
```

and `FLINDERS_PREFIX: ('flinders', FLINDERS_DOORS)` as the last row of `OWNED_DOORS`. Write both exactly so: the
test greps for them.

### `tools/generate_flinders_art.py` (new, needs Pillow)

Modelled on `generate_mall_art.py`: imports the frame (`wall_side`, `wall_front`, `threshold`, `doorlight`), the
drawing helpers and `register` from `generate_pub_art`; half size (32px a cell), 1px ink outline, pixel-doubled by
`register`; nothing random; text in the game's own font via the pub tool's `text`; Latin only, no brand marks; a
docstring listing the sprites; `--preview out.png`. Colours are the building's, copied as values (do not import the
town's art tool): mustard `e0b040` / hi `f2d070` / lo `b07c2c`, maroon `8a3a34`, copper green `5fa58a` / `8fd0b0`
/ `3c7462`. A palette dict `CONCOURSE` with the keys `PUB` / `ATRIUM` have (mustard face, maroon trim).

Fourteen sprites, all `flinders-in-<piece>`:

| Piece | Cells | What |
|---|---|---|
| `floor-a`, `floor-b` | 1x1 | cream terrazzo; `a` has a maroon diamond inlay |
| `side-w`, `side-e`, `wall-front`, `threshold-w`, `threshold-e` | 1x1 | the pub's frame in `CONCOURSE` |
| `doorlight` | 2x3 | the pub's, flat (`DEPTH_BIAS` -40 as `mall-in-doorlight`) |
| `wall-bay` | 3x3 | back wall: mustard, maroon bands, a pilaster |
| `wall-arch` | 4x3 | back wall with an arched window, pale daylight glass |
| `wall-name` | 6x3 | back wall with a name board reading `FLINDERS ST` |
| `clocks` | 4x3 | the board of nine dials from over the door outside (same order of hands), on two posts; the bottom row is the posts' feet |
| `tickets` | 3x2 | two ticket machines side by side, a fare card slot, no text but `TICKETS` |
| `board` | 3x2 | a departures board on a stand: every row reads `BUS` |

### `tools/generate_flinders.py` (new)

Copy `generate_mall.py`'s structure (`rg.cli`, `rg.load_config`, `HOST = 'SanFranbourne'`,
`KEY = f'{rg.FLINDERS_PREFIX}{HOST}1'`, `NAME = 'Flinders St'`, `s = lambda p: f'flinders-in-{p}_0_0'`,
`doors = rg.sprite_doors(cfg, HOST, rg.FLINDERS_DOORS)`, `from interiors import Interior`). The room is
`Interior(20, 11, 2, 4)`: 24x18 cells, floor cell `(0, 0)` at room `(2, 4)`. Floor rows (`fy`), top to bottom:

| `fy` | What | Calls |
|---|---|---|
| -3..-1 | back wall, solid | `it.back_wall([(0, s('wall-bay'), 3), (3, s('wall-arch'), 4), (7, s('wall-name'), 6), (13, s('wall-arch'), 4), (17, s('wall-bay'), 3)], 3)` |
| 0, 1 | the track, empty, solid end to end | floor `station-ballast_0_0`; `it.put('Over Floor', fx, 0, 'station-track-n_0_0')`, `... 1, 'station-track-s_0_0'`; `it.solid(0, 0, 20, 2)` (`Interior.room` does not seal tracks) |
| 2 | platform edge | floor `station-platform-edge_0_0` |
| 3, 4 | platform | floor `station-floor_0_0`; `it.stand('station-bench-back_0_0', fx, 4, w=2)` at `fx` 1 and 17 |
| 5 | gate line (floor `station-floor_0_0`) | below |
| 6..10 | concourse | floor `s('floor-a')` where `fx % 2 == 0 and fy % 2 == 0`, else `s('floor-b')` |
| 11 | front wall, doorway at `fx` 9, 10 | `it.front_wall(s('wall-front'), (9, 10), (s('threshold-w'), s('threshold-e')))` |

Gate line, by `fx`: `tickets` 0-2 (`it.prop(s('tickets'), 0, 5, 3, 2)`: rows 5-6 solid); railing 3; `gate-end-w` 4;
gates 5, 6; `gate-end-e` 7; `clocks` 8-11 (`it.stand(s('clocks'), 8, 5, w=4, h=3)`: only its foot row is solid, you
walk behind its head on the platform); `gate-end-w` 12; gates 13, 14; `gate-end-e` 15; railing 16; `board` 17-19
(`it.prop(s('board'), 17, 5, 3, 2)`). Gates and ends as `generate_stations.py` places them, a row up because they
are 1x2: `it.put('Other', fx, 4, 'station-gate_0_0')` (no collider),
`it.place('Collidables', fx, 4, 'station-gate-end-w_0_0', [(0, 1)])`. Railing:
`it.b.railing_row(it.oy + 5, taken)`, where `taken` is in ROOM columns and must hold every column that is not one
of the two railing cells (`railing_row` runs the whole width of the room, void included). The four gate cells are
the only way onto the platform.

Concourse: `it.side_walls(s('side-w'), s('side-e'), 3)`; `it.put('Non-Collidables', 9, 8, s('doorlight'))`;
`it.stand('station-bench_0_0', fx, 9, w=2)` at `fx` 3 and 15; `it.stand('station-planter-a_0_0', 6, 10, w=2)` and
`'station-planter-b_0_0'` at 12; `it.stand('station-pillar_0_0', fx, 8)` at `fx` 6 and 13. Furniture may move a
cell if the render looks wrong; the table above, the gate line and the doorway may not (the tests pin them).

Then, as the mall: `inside = it.doorway(9, HOST, [front for _, front in doors])`,
`room = it.room(NAME, npcs=[], flinders={'host': HOST, 'doors': [list(d) for d, _ in doors]}, shopEnabled=False)`,
`cfg['rooms'][KEY] = room`, `rg.open_door(cfg['rooms'][HOST], door, KEY, cell)` for each door and its `inside` cell,
`rg.save_config(cfg)`, and a one-line print. A re-run must leave `config.json` byte-identical.

### `tools/check_generators.py`

`'generate_flinders'` in `GENERATORS` straight after `'generate_mall'`; `ART_TOOLS += ['generate_flinders_art']`
with a one-line comment, after the mall's.

### `src/utils/Interactions.js`

After the mall's rows, with a comment naming the issue and the generator:

```js
{ kind: 'clock', group: 'clock', pattern: /^flinders-in-clocks/, footprint: true },
{ kind: 'replacement-buses', group: 'flavour', pattern: /^flinders-in-board/, footprint: true, say: 'every line on the board says the same thing: buses replace trains' },
{ kind: 'ticket-machine', group: 'flavour', pattern: /^flinders-in-tickets/, footprint: true, say: 'the machine wants a card you do not have. the card is sold by the machine' },
```

The existing `clocks` row (`/^sfb-clocks-station/`) is unchanged. Nothing in `GameScene.js` changes.

### Generated data (by running the tools, never by hand)

From `gamev2/`, with a Pillow venv (`python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -r
tools/requirements-art.txt`; plain `python3` has no Pillow here):

```bash
/tmp/venv/bin/python3 tools/generate_flinders_art.py --preview /tmp/flinders.png   # look at the sheet
python3 tools/generate_flinders.py
python3 tools/config_to_tiled.py FlindersSanFranbourne1 SanFranbourne
node tools/play.js lint FlindersSanFranbourne1 SanFranbourne
node tools/play.js render FlindersSanFranbourne1 /tmp/room.png                     # look at it
```

This adds `assets/sprites/flinders-in-*_0_0.png`, `tiled/flinderssanfranbourne1.tmj`, the room and palette entries
in `config.json` (appended after `mall-in-palm_0_0`), and changes `SanFranbourne` only by two colliders off and two
hidden transporters on (`config.json`, `tiled/sanfranbourne.tmj`). Nothing visible on the town map moves, so
`make_worldmap.py` is not run; `check_generators.py` confirms it. Rooms touched: `SanFranbourne` (door cells
`(18, 45)`, `(19, 45)` only) and the new `FlindersSanFranbourne1`.

### Docs and comments

- `docs/landmarks-and-towns.md`: a section "Flinders Street's concourse (issue #246)" after "Canal City's atrium",
  in that section's shape (what it is, the door, the layout, the bumps, art, build order); in the San Franbourne
  section (about line 421) the station is no longer "sealed": it opens into the concourse, still with no train.
- `tools/generate_sanfranbourne.py`: the docstring's line about the station says the doors open into a room built
  by `tools/generate_flinders.py`. Do not write the room key or `'flinders-in-` in it (the plumbing test forbids
  both in any other generator).

## Data and interfaces

- `config.rooms.FlindersSanFranbourne1`: `name: 'Flinders St'`, `interior: true`, `shopEnabled: false`, `npcs: []`,
  `flinders: { host: 'SanFranbourne', doors: [[18, 45], [19, 45]] }`, two hidden transporters on room cells
  `(11, 15)` and `(12, 15)` to `(18, 46)` and `(19, 46)`. No `lanternLight`, no `shopMenu`.
- `config.rooms.SanFranbourne.transporters`: two more, hidden, on `(18, 45)` and `(19, 45)`, to room cells
  `(11, 14)` and `(12, 14)`.
- `tilePalette`: appended only. `spriteMetadata` / `tileNames`: fourteen `flinders-in-*` entries.
- `roomgen.FLINDERS_DOORS`, `FLINDERS_PREFIX`, one `OWNED_DOORS` row. Three `Interactions.RULES` rows.
- No change to `config.stations`, `airports`, `places`, `devhouse.world`, saves or URL parameters.

## Tests

New `tools/tests/flinders.test.js`, modelled on `mall.test.js`, on the shared `tools/tests/interiors.js` with
`{ HOST: 'SanFranbourne', KEY: 'FlindersSanFranbourne1', NAME: 'Flinders St', MARK: 'flinders',
SPRITE: 'sfb-clocks-station_0_0', DOORS: [[5, 6], [6, 6]], PREFIX: 'flinders-in-', BEHIND: 2 }`. There is no
`STAND` (the town takes no blog NPCs, so no `LANDMARKS` row): in `interiors.js` make `outside()` return
`stand: STAND ? [...] : null`, and do not call `nobodyInTheWay`. Tests (each name ends `(#246)`):

1. The station opens: `I.doorsOpen` (two doors, two mats); the doors are under the clocks board, sprite columns 5
   and 6; exactly one room key starts with `Flinders`; `[interior, lanternLight, shopEnabled, npcs]` is
   `[true, undefined, false, []]`; the room is not in `config.stations` and no `stations` entry names it or the town.
2. Nobody is in the way: no NPC base or dated state of `SanFranbourne` is on a door cell or the cell in front.
3. The room is a station: name and size `['Flinders St', 24, 18]`; back wall solid across rows 1-3; both track rows
   solid for the whole width and laid with `station-track-n` / `-s`; on the gate line only the four gate cells are
   open, and with them made solid no platform cell is reachable; one `clocks` between the two gate banks, in line
   with the doorway; concourse floor is `flinders-in-floor-[ab]`; no sprite of another interior
   (`/^(shrine-in-|palace-in-|temple-in-|pub-in-|distillery-in-|mall-in-|office-(?!void)|konbini-)/`), no Japanese
   kit piece (the list in Approach), no `bin`; `I.reach`: nothing open is lost, at least 120 cells.
4. Walk in and out by both doors: `I.walkThrough(world, config, <any date>, ['clock', 'replacement-buses',
   'ticket-machine'], /says: "|opens the time-travel date picker/)`; behind the clocks' head (platform row) you
   walk, and stepping south into its foot bumps `clock`.
5. The rules: `Interactions.match` for `clocks`, `board`, `tickets` (kind, group, `footprint`, `say` at most 100
   characters); `null` for the frame, floors, wall pieces and `doorlight`; one rule each for the two new kinds;
   `sfb-clocks-station_0_0` still matches `clocks` / `flavour`; `GameScene.js` mentions neither `flinders` nor
   the new kinds.
6. `I.named(cfg(), 'Flinders St (in San Franbourne, overseas)')` (build the string from
   `config.rooms.SanFranbourne.name`; the town's name is written once in config).
7. `I.plumbing({ generator: 'generate_flinders', art: 'generate_flinders_art', sprites: 14,
   after: 'mall-in-palm_0_0', owned: "FLINDERS_PREFIX: ('flinders', FLINDERS_DOORS)",
   table: "FLINDERS_DOORS = {'sfb-clocks-station_0_0': [(5, 6), (6, 6)]}" })`; the art tool imports the pub's
   frame and defines no `wall_side` / `threshold`; `generate_sanfranbourne.py` has no `Flinders` room key.

Existing assertions to update, strictly, in `tools/tests/airports.test.js` ("the home city" test): the list of
allowed transporter targets (about line 375) gains `FlindersSanFranbourne1`, and the "under the clocks" bump
(line 360) moves from the door cell `clocks[0] + 5` to the wall beside it, `clocks[0] + 4`. Fix any other test the
new room trips (a count of interiors, rules or rooms) the same way; none is known.

Browser (`tools/browser/README.md`): add a case to `tools/browser/regress.js` in the style of `konbini-enter`:
place the player on `(18, 47)` in `SanFranbourne`, walk north twice with real keys, need the room to be
`FlindersSanFranbourne1`, the HUD to say `Flinders St`, a fade seen and the player on screen; walk south, need
`SanFranbourne` `(18, 46)`. Then play it by hand at desktop size and a phone size (`?notitle=1&nointro=1`, a
landscape and a portrait phone with touch): in by each door, through a gate, along the platform, bump the clocks
(Time Travel opens and closes), the board and the machine, out again; at night (`?tod=night`) the room is not
graded. Look at the screenshots (back wall whole, nothing drawn over the player wrongly at the gates and behind
the clocks, no train on the track) and save them to `/work/media/`.

Run, from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
`/tmp/venv/bin/python3 tools/check_generators.py` (the art tools are `skip` without Pillow), `python3
tools/sync_cities.py --check`, then the browser regression.

## Risks and open questions

- **The name.** The game is coy elsewhere ("the station with the clocks", San Franbourne, Tullafrisco Airport); this
  design uses the owner's own words, `Flinders St`, on the HUD and the name board. If the owner would rather keep it
  coy, it is two strings (`NAME` and the board's text) and test 6.
- **No train.** Assumed from the town's rule (air only) and the line outside. Making it rideable would be a
  `config.stations` room from `generate_stations.py` instead, and a different ticket.
- **Time Travel on the clocks** is consistent with the game's other clocks, but the building outside only says a
  line. If it reads wrong when played, make the row a `flavour` line; do not change the outside rule here.
- **Phone camera**: the room is taller than a phone's view, so `back_wall(view=True)` should not be needed (the pub
  and the mall do without). If a phone screenshot from the platform cuts the back wall off, pass `view=True`.
- **Kit and drawn art side by side**: the station kit is a different hand from the half-size art. The mall does the
  same with benches and planters; if the gates or railing look wrong against the mustard, say so in the summary
  rather than redrawing the kit.
- `AmbientTrains` runs on `train-track*` tiles only, so the `station-track-*` rows get no passing train; confirm in
  the browser.
- Art is compared by pixels under the pinned Pillow (`tools/requirements-art.txt`); generate with that venv.
