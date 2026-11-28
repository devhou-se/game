# Tiled maps — the source of truth for gamev2 rooms

Rooms are authored in [Tiled](https://www.mapeditor.org/) (1.11+). At runtime
GameScene loads `tiled/<room>.tmj` for every room listed in `config.json` and
`src/systems/TiledAdapter.js` converts it into the exact room shape the
renderer already consumes — per-sprite placement, feet-based Y-sort and
collision all work unchanged.

`config.json` still owns everything that isn't map geometry: game settings,
the player, NPCs, sprite metadata and achievements. Its baked-in room layers
are only a fallback (`?maps=config`, or any room whose `.tmj` fails to load).

## Workflow

1. Open **`devhouse.world` at the repo root** (`open -a Tiled devhouse.world`) —
   it shows every outdoor map in one view (interiors are not in it): Tokyo's
   five districts in their true overworld positions (roads line up across the
   map seams), the other towns around them. Click a room to edit it.
   Individual maps also open directly (e.g. `tiled/tokyo.tmj`), and
   `devhouse.tiled-project` at the root gives a project sidebar.
2. Edit and save (keep the JSON `.tmj` format).
3. Refresh the browser — maps are fetched cache-busted, no build step.

The `.tmj` files themselves must stay in `gamev2/tiled/` — Firebase deploys the
`gamev2/` folder and the tileset references sprites by relative path.

## Map conventions (what the adapter expects)

- **One image-collection tileset** whose per-tile `image` filename **is** the
  sprite key (`../assets/sprites/<key>.png`). To use a new sprite, add its PNG
  to `assets/sprites/` and add it to the tileset in Tiled.
- **Tile layers** hold flat 1×1 ground (floor/path/water/colliders) — paint
  freely. **For floors, use the Terrain Brush** (View → Toolbars, or press
  `T`): every autotile family (gravel, grass, pond, the brick floors…) is a
  wang set in the tileset, so painting "grass" places the right edge/corner
  pieces automatically — same feel as Godot's autotile. The individual pieces
  are also named by role (`gravel-autotile_edge-n`, `_corner-nw`, `_center`)
  if you ever need to place one by hand. The roles come from the Godot
  autotile bitmasks (`tools/autotile.py` converts both ways).
- **Object layers** named `<layer> ·obj` hold multi-cell sprites
  (trees/statues/buildings) as tile-objects. The tileset is
  `objectalignment=topleft`, so an object's position is its top-left cell —
  snap to the 64px grid.
- Both kinds carry custom properties `gv2layer` (logical layer name), `z`
  (draw depth band) and `collision` (bool). A tile layer and its `·obj`
  companion with the same `gv2layer` merge back into one game layer.
- A **`Meta` object layer** (property `gv2meta=true`) holds:
  - `transporter` point objects with `kind=transporter`, `targetRoom`,
    `targetX`, `targetY`, `hidden` properties;
  - one `boundary` polygon object (`kind=boundary`) for non-rectangular
    walkable areas.
- Map custom properties `gv2room`, `gv2worldWidth`, `gv2worldHeight` carry the
  room name and pixel size.

## Prefabs — build objects in Tiled, place them procedurally

`tiled/prefabs/*.tmj` is the object library: each prefab (house, pagoda,
lantern, torii, shrine, vending machine, ...) is a small ordinary Tiled map you
edit in the Tiled app. A prefab carries:

- its **sprites** on object layers tagged with the room layer they belong to
  (`gv2layer` = Collidables / Tops / Other / Over Floor);
- its **collision** painted with the translucent red `collider-marker` tile on
  a `Colliders` layer (converted to the game's invisible collider on stamp —
  room maps show the same marker, so collision is visible and paintable
  everywhere in Tiled);
- its **doors** as `kind=door` point objects on a `Meta` layer — the default
  transporter location. Generators leave a wired door open and attach a hidden
  transporter to it (the Sapporo 7-Eleven's door leads into the
  `KonbiniSapporo1` interior room this way); unwired doors are sealed solid
  automatically.

`tools/prefab.py` loads and stamps prefabs; `tools/make_prefabs.py` re-seeds
the initial library; a town generator such as `tools/generate_asahikawa.py`
shows the full pattern — it builds a whole town from prefabs + autotiled
floors. An interior is built from the shared shell in `tools/interiors.py`
(`tools/generate_temple.py` is the example; `docs/generators-and-checks.md`,
"Interior building blocks").

### Stamping a prefab into an existing (ported) room

Generators call `b.stamp()`. For the ported rooms (Tokyo / Market / Park / Palace), which have no generator
and whose map lives in `config.json`, use `tools/stamp_prefab.py`:

    python3 tools/stamp_prefab.py Market --add discount-store 46 22
    python3 tools/stamp_prefab.py Park --remove sakura-small 5 20 --add machiya-black 4 17 --dry-run

It writes nothing unless the placement is clean: inside the room, not over another standing sprite
(`--allow-overlap` to permit), no solid cell on a cell that is already solid, no transporter or dated NPC
position anywhere under its sprites (solid rows or the walk-behind roof rows), and every walkable cell that
was reachable from the transporters still is. Follow with `config_to_tiled.py <Room>` and then
`node tools/play.js lint <Room>` (lint reads the Tiled map). `--remove` lifts the colliders of the prefab as it is defined NOW (so when
changing a prefab's collision: remove it from the rooms, re-run `make_prefabs.py`, add it back) and keeps
any collider cell another standing sprite still covers.

The city buildings (`highrise-*`, `discount-store`, `machiya-*`) come from `tools/extract_city.py` - see
"Generic city buildings" in `gamev2/docs/buildings-and-street-props.md`.

The Hokkaido prefabs (`sapporo-clock-tower`, `sapporo-tv-tower`, `asahikawa-bridge`, `ramen-banner`) are
drawn by `tools/generate_hokkaido.py` - see "Hokkaido: Sapporo and Asahikawa" in `gamev2/docs/landmarks-and-towns.md`.
`asahikawa-bridge` (no town places it since Asahikawa got `asahibashi-deck`, laid the same way, #219) is the pattern for a flat multi-cell sprite laid over water: a `Non-Collidables` object
whose sprite carries a negative `depthBias` in `config.json` `spriteMetadata` (an `Over Floor` object would
be drawn under the `Water` tiles).

`devhouse.world` also holds the towns you cannot walk to from Tokyo (train or plane only) at detached
offsets, laid out like Japan (north up; compass order, not true distance) and all CLEAR of a stitched city's
bounding box (the Map draws the city's woodland over that whole box - issue #174): Sapporo, Asahikawa and
Sendai to the north, Osaka to the west and Fukuoka far to the south-west of it, the Hokuriku city (Kanazawa,
Shirakawa-go and Toyama, stitched like Tokyo's districts) to the north-west, San Franbourne far to the
south-east.

Street accessories (issue #19) come from `tools/extract_street.py` - see "Street accessories" in
`gamev2/docs/buildings-and-street-props.md`: `traffic-light` (1x3, give stamp_prefab the TOP cell; the base two rows down is the solid
one), `crossing-h` / `crossing-v` (zebra crossing on `Over Floor`, origin on the road's top / left kerb cell),
`utility-pole`, `road-mirror`, `bus-stop`, `bicycle-blue|orange`, `scooter-grey|red`, `traffic-cone`
(`vending-white` / `vending-red` are 1x2 and solid on both cells - issue #101):

    python3 tools/stamp_prefab.py Park --add crossing-h 25 39 --add crossing-h 26 39 \
        --add traffic-light 24 36 --add traffic-light 27 40

## Adding a new room

1. Copy an existing `.tmj` (or seed one from a config room with
   `python3 tools/config_to_tiled.py <RoomName>`), save it as
   `tiled/<roomname>.tmj`.
2. Add a `rooms.<RoomName>` entry to `config.json` (npcs/objects can be empty;
   layers can be empty — the `.tmj` supplies the map).
3. Point a transporter at it from another room's `Meta` layer.

## Seeding a room's map from config

A room that a generator (or a hand edit) wrote into `config.json` gets its map this way:

1. `python3 tools/config_to_tiled.py <Name> [<Other> ...]` — seed `tiled/<name>.tmj`. It takes any
   number of rooms (name every room the generator or its post-passes touched) and exits 2, writing
   nothing, if a name is not a room in `config.json` (room keys are case-sensitive).
   Re-running it on an existing map keeps every sprite's tile id (new sprites are numbered after the
   highest one), so a map change shows up in the `.tmj` diff as just the cells that changed.
2. `node tools/play.js lint <Name>` — QA gate (it reads the Tiled map); fix any ERRORs before shipping.

Once seeded, Tiled is the editor — don't hand-edit the generated `.tmj` back
into config.

Four of the Tokyo districts (Tokyo, Market, Palace, Park) were ported once from the old Godot project's
overworld, with tools that were removed together with that project (#229, in git history). They have no
generator: their maps are the source of truth. (The fifth, Karuizawa, is generated by
`tools/generate_karuizawa.py`, which also owns the two cells of Tokyo's west gate, `(0, 41..42)`.)
Shinjuku, a sixth, is generated too (`tools/generate_shinjuku.py`, issue #94); the three seam transporters
it pins on Palace are the only thing a generator writes to a ported map.

## Rendering a map without the Tiled app

`node tools/play.js render <Room> out.png [--scale 0.5] [--colliders]` draws
`tiled/<room>.tmj` in the game's own draw order (feet Y-sort, Tops bias; no
dependencies) — use it wherever these docs say `tmxrasterizer` if Tiled isn't
installed. `tools/make_worldmap.py` falls back to it automatically, and always
uses it with `--pil` — which is how the committed `assets/map/world-map.png` is
made: `tools/check_generators.py` rebuilds the map that way and fails if the
committed one differs.

## Gotcha ledger

- **A generated room and its generator must agree** (issue #107) — a
  generator rebuilds its room from scratch, so a change made only in
  `config.json` is dropped the next time it runs. `python3
  tools/check_generators.py` runs every room generator in a scratch copy and
  fails if `config.json` would change, naming the rooms and cells. The same
  run re-seeds every room with `config_to_tiled.py` and fails if a committed
  `tiled/*.tmj` would change, and (with a Pillow python3) checks that the art /
  prefab tools still rebuild `assets/sprites` and `tiled/prefabs` (#186). Make a
  surgical change (config edit + `config_to_tiled.py <Room>`) AND mirror it in
  the generator source, then run the check. Generators keep what they do not
  own — NPCs, a 7-Eleven door wired by `generate_konbinis.py`, the doors of
  house and shrine interiors — and run their own fence / track passes
  (`b.finish()`), so each is a no-op on its own.
- **World seams are road-aligned by design** (`devhouse.world`): every
  adjacent room pair draws the same connecting road on both sides of the
  seam. A crossing is just hidden transporters on the edge cells of that road
  (arrive one cell inside the twin's trigger) plus dressing — lantern pairs,
  or a torii straddling the road (legs collide, top on Tops). Never build a
  crossing as a door-band "building"; transit must continue in the walking
  direction.
- **The Tokyo districts are stitched into one map at runtime** (config
  `cities`, `src/systems/CityStitcher.js` — see "Stitched cities" in
  `gamev2/docs/stitched-city.md`). The four maps stay separate files and you keep
  editing them one at a time, in their own cell coordinates, but in the game:
  - the seam transporters are ignored (keep them: `?stitch=0` uses them, and
    `play.js check` surveys that fallback too) and the player simply walks
    across, so **whatever stands on a map's edge is now visible from the
    neighbour** — an edge fence, a half-drawn road, a sprite hanging over the
    border;
  - `node tools/play.js` and `/studio/` show the stitched city too (they run
    the game's own stitcher): `lint <District>` still checks one map at a
    time, `lint TokyoCity` (also run by a bare `lint`) checks the merged room
    — a collider lost to an overlap, a hole a `patch` left — and
    `render TokyoCity out.png` draws it with the woods. Coordinates stay the
    district's own everywhere (`where` -> `Market 5,24 (TokyoCity 111,24)`);
    `--stitch=0` / `/studio/?stitch=0` give the five separate rooms;
  - where two maps overlap (Tokyo/Market 1 column, Market/Palace 1 row,
    Palace/Park 4 rows) only the LATER map in `cities.<City>.rooms` is drawn
    and collides; the other map's tiles on those cells are dropped. Edit the
    owner's copy (Market's column 0, Palace's row 0, Park's rows 0-3);
  - a tile that only reads wrong with the neighbour in view (a road corner
    where the road now carries straight on) can be fixed for the stitched
    game alone with `cities.<City>.patch` in config.json
    (`{district: {layer: {"x,y": tile | null}}}`) instead of a map edit;
  - a map's position comes from `devhouse.world`. After moving or resizing a
    district there run `python3 tools/sync_cities.py` (then
    `tools/make_worldmap.py`) — the game refuses to stitch a city whose
    offsets disagree with the world map and falls back to separate rooms.
    `make_worldmap.py` also draws the stitched city (woods included) into
    the Map screen's image, so re-run it after any district edit.
- **Nobody is lost behind tall art any more** (`src/systems/Occlusion.js`):
  a roof, tower, torii top or tree crown that covers most of a character
  fades to 40% while they are behind it. The Colliders layer is only for
  where you cannot stand — do not add colliders to keep the player out of a
  walk-behind strip, and note that the layer's `collider-marker` tiles are
  never drawn by the game (they only feed the blocked-cell set; the debug
  overlay shows them).
- **Track rows in ported rooms are sealed cell-by-cell** (`gk_blank` under
  the `train-track` Over Floor sprite). A road crossing the tracks needs its
  two cells unsealed — that's a level crossing, precedent exists.
- **Pass `seal_tracks.py` the rooms you mean**: `seal_tracks.py Osaka`. (It leaves a track cell with a
  road under it open, which is what keeps Palace's level crossing - cells 0,3 and 1,3 - walkable.)
- **Palace's track is row 3, not row 5** (issue #63): behind Tokyo Station's roof line, where the
  station sprite's two empty top rows let the rails and the whole ambient train show, passing behind
  the domes. On row 5 the track ran into the building's side half way up and the train was a strip of
  roof above it. If the station art is ever replaced, keep the track on a row its top leaves clear.
- **A vending machine is solid down to its foot** (issue #101): cabinet tile + foot tile, colliders on
  BOTH (the two lowest cells of the column). The foot tile is only the cabinet's last 14-18px, so an
  open foot cell puts the player on top of the machine. `play.js lint` fails with `vending-walkable`;
  `python3 tools/seal_vending.py [Room ...]` adds the missing colliders to room data, and the
  `vending-white` / `vending-red` prefabs already carry them. The shop opens from the cell in front.
- **The discount store has an interior** (issue #91): `tools/generate_discount_stores.py [Host ...]`
  builds `DonTakote<Host>` and wires the facade door (door = column 2 of the bottom row; the cell
  in front of it must stay free - no bicycle, no NPC spot). Osaka and Sapporo wire the door in their
  own generators (`seal=False` + `don.door_transporter`), Market gets it surgically from the script.
- **Osaka's main street is four cells wide** (issues #106 / #151), because the arch's opening is:
  `crossing-v` is a three-cell prefab, so its crossing is the same tiles laid by hand in
  `generate_osaka.py` with the middle one repeated, and its centre line is the pair
  `road-lane-left` / `road-lane-right` (half the line each, on their shared edge), which stops for the
  crossing's stripes (`road-plain` under the two middle crossing cells). Those and the
  two-kerb corner pieces `road-corner-nw|ne|sw|se` (a road's square end, the outer corner of a
  junction box) come from `tools/make_road_tiles.py`, which derives them from the sheet's own road
  tiles. An odd-width road uses `road-div-vertical` / `road-div-horizontal` as before.
- **A road junction is a plain 3x3 box** (issues #147 / #179): `road-plain` inside, the kerb only along
  a side no road leaves by, a `road-corner-*` on the outside of a bend. Never run `road-edge-*` across
  the mouth of a joining road or a centre line into the box. A road leaves a box only if it leads
  somewhere: beside the edge of a map that side is closed and paved, not a two-cell stub (issue
  #240). The ported districts' boxes are listed in `tools/square_junctions.py` (idempotent: add the
  junction there and re-run it); generators lay theirs by hand (Osaka's avenue, Sapporo).
- **A bridge deck over water gets a parapet and a shadow** (issue #180): `bridge-parapet-w|e` on the
  deck's two edge cells and `bridge-shade-w|e` on the water cells beside them, all on
  `Non-Collidables` (flat sprites with a negative `depthBias`, from `tools/make_bridge_tiles.py`). No
  colliders: the coping is the outer 14px of the cell. They are for a deck that runs north-south.
- **Water is navigable only where a room says so**: `rooms.<Room>.waterways` in config.json
  (written by the generator - see "Ambient Traffic" in `gamev2/docs/ambient-traffic.md`) gives a canal its
  boats; `under` names the cells where a bridge deck crosses, and those cells must be plain
  walkable floor with NO water tile (the boat is cut off at the deck's edge). Osaka's canal is laid
  by hand in `generate_osaka.py` (three rows, edge to edge, `edge-n` / `center` / `edge-s` - the pond
  set has no `edge-w`, so a channel wider than two rows must not have a west end cap). Moat tiles
  need no declaration. Frozen water gets no entry.
- **A shop fixture needs the cell under it** (issue #152): shelves and coolers are bumped from
  the cell below, the till from any side. `play.js lint` fails a store with `shop-no-front`
  otherwise; `generate_konbinis.py` stands what sells against the back wall or in shelf blocks with an
  aisle below them, and its `check_store()` fails a plan with a fixture nobody can reach. Nothing boxes
  in bare floor either (`shop-sealed-floor`, issue #182).
- **GuttyKreum sheets are 2x, not 4x**: one 32px RPG Maker tile is one 64px cell (the ported houses are
  pixel-identical 2x crops). Only the Dotonbori arch / ferris wheel were extracted at 4x, as oversized
  landmarks. A building extracted at 4x gets a two-cell-wide door and pixels twice the size of its neighbours.
- **City buildings are solid up to the roof line**: `building()` prefabs collide on every row except the
  top two, which are walk-behind like a house roof. The first cut left the whole upper half open and the
  player vanished into a pocket up to 5x6 cells behind a tower. Keep doors, NPC spots and paths out of
  those two rows (`stamp_prefab.py` refuses a transporter or NPC there).
- **A building's feet belong on the plaza / kerb edge, not across it**: an 8-row block on Palace's
  forecourt reached over the kerb and walled off the pavement. Where the gap is short use the lower
  variant (`midrise-apartment`, 5x6) rather than letting a tall one overhang.
- **Anchors are not rounded**: `anchorY = 32/height` to 4 places put the 11-row tower 0.03px off the grid.
- **One tile per cell per layer**: a big landmark sprite occupies only its
  top-left cell on `Collidables`, so a lantern post stamped on that exact cell
  is silently replaced (its collider stays). Keep small props off the top-left
  cell of tall sprites.
- **A shrine hall is two sprites, and the hall alone is never complete**:
  `shrine-building_0_0` (3x6, Collidables) is cut 3 cells wide, so its own roof
  rows are a slice with the eaves chopped off. The whole roof is a 5x6 Tops
  sprite — `shrine-top_0_0` (blue) or `red-shrine-top_0_0` — placed at the
  building's cell **(-1, -2)**; it needs two free rows above the hall and a free
  column each side. Stamp the `shrine` prefab (5x8, origin = the roof's cell)
  rather than the building. The roof hides anyone standing behind it, so the
  prefab also makes the cells it would hide solid (the row behind the hall and
  the eave columns, rows 1-4 of the 5x8) and NPC spots go below the steps
  (`blog_to_npc.py` LANDMARKS stand offset). NPCs wander 2 cells from home —
  an open cell under a Tops roof within that box means a floating name label.
  The two bottom-row eave cells (row 5, the outer columns) stay open on purpose: the roof has
  only its upturned tip there, a sliver above a head, so lint's `under-overhead` skips them
  (`OPEN_EAVES` in `tools/world-model.js`, #157) and still checks the three columns between.
  `tools/extract_shrine.py` re-cuts the blue roof from the atlas using the
  rect it carries (`SPRITES` in the tool: `shrine-top`, 160x192 like the
  red one — it used to be 160x160, which cut the eaves flat) and refuses a
  section whose art touches its edge. `shrine-top_0_0` carries `depthBias: 1`
  so it wins the depth tie with the `temple-hallway` roofs either side of the
  Tokyo hall (without it one eave corner drew over the hallway and the other
  under it, by creation order).
- **No rubbish bins** (issue #19): `node tools/play.js lint` fails with `rubbish-bin` if ANY room places a bin / dumpster /
  trash-can sprite (it scans the whole config and every `tiled/*.tmj` on every run, whatever `--room` says). The interior pack's `office-bin` is retired (no PNG, no `spriteMetadata`; only its positional `tilePalette` slot remains) -
  use `izakaya-stool_0_0` for a seat and a plant, `office-watercooler` or a 7-Eleven's `konbini-baskets_0_0` for a corner filler.
- **Traffic lights are one 1x3 sprite whose map key is the green frame** (`traffic-light_0_0`);
  `src/TrafficLights.js` swaps the texture at runtime, so never place the `-amber` / `-stop` / `-stop-blink`
  keys in a map. A signal needs its two upper cells inside the room: on a road hugging the top map edge put both
  signals on the south kerb.
- **Zebra crossings come from `GK_TS_A5`** (the sheet the road tiles were cut from). The lookalikes in
  `GK_JC_A5_2` sit on a darker asphalt and show as a dark patch on the road.
- **`tmxrasterizer` draws collider markers and Meta pins** — red boxes/pins
  in renders are debug art, not in-game visuals.
- A probe that prints `?` for "any sprite" hides colliders stacked under
  sprites — check per-layer before assuming a cell is walkable.
