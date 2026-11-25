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
   it shows all four rooms in one view, laid out in their true overworld
   positions (roads line up across the map seams). Click a room to edit it.
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
  transporter to it (the Machi 7-Eleven's door leads into the `Konbini`
  interior room this way); unwired doors are sealed solid automatically.

`tools/prefab.py` loads and stamps prefabs; `tools/make_prefabs.py` re-seeds
the initial library; `tools/generate_machi.py` shows the full pattern — it
builds the whole Machi town and the Konbini shop interior from prefabs +
autotiled floors. Same recipe works for interiors: make `shelf` / `counter`
prefabs and let a generator lay out the room.

### Stamping a prefab into an existing (ported) room

Generators call `b.stamp()`. For Tokyo / Market / Park / Palace and Machi, whose map lives in `config.json`,
use `tools/stamp_prefab.py`:

    python3 tools/stamp_prefab.py Market --add discount-store 46 22
    python3 tools/stamp_prefab.py Machi --remove sakura-small 5 20 --add machiya-black 4 17 --dry-run

It writes nothing unless the placement is clean: inside the room, not over another standing sprite
(`--allow-overlap` to permit), no solid cell on a cell that is already solid, no transporter or dated NPC
position anywhere under its sprites (solid rows or the walk-behind roof rows), and every walkable cell that
was reachable from the transporters still is. Follow with `config_to_tiled.py <Room>` and then
`node tools/play.js lint <Room>` (lint reads the Tiled map). `--remove` lifts the colliders of the prefab as it is defined NOW (so when
changing a prefab's collision: remove it from the rooms, re-run `make_prefabs.py`, add it back) and keeps
any collider cell another standing sprite still covers.

The city buildings (`highrise-*`, `discount-store`, `machiya-*`) come from `tools/extract_city.py` - see
"Generic city buildings" in `gamev2/CLAUDE.md`.

The Hokkaido prefabs (`sapporo-clock-tower`, `sapporo-tv-tower`, `asahikawa-bridge`, `ramen-banner`) are
drawn by `tools/generate_hokkaido.py` - see "Hokkaido: Sapporo and Asahikawa" in `gamev2/CLAUDE.md`.
`asahikawa-bridge` is the pattern for a flat multi-cell sprite laid over water: a `Non-Collidables` object
whose sprite carries a negative `depthBias` in `config.json` `spriteMetadata` (an `Over Floor` object would
be drawn under the `Water` tiles).

`devhouse.world` also holds the train-only towns at detached offsets: Yukimura and Osaka to the west,
Sapporo and Asahikawa to the north.

Street accessories (issue #19) come from `tools/extract_street.py` - see "Street accessories" in
`gamev2/CLAUDE.md`: `traffic-light` (1x3, give stamp_prefab the TOP cell; the base two rows down is the solid
one), `crossing-h` / `crossing-v` (zebra crossing on `Over Floor`, origin on the road's top / left kerb cell),
`utility-pole`, `road-mirror`, `bus-stop`, `bicycle-blue|orange`, `scooter-grey|red`, `traffic-cone`:

    python3 tools/stamp_prefab.py Park --add crossing-h 25 39 --add crossing-h 26 39 \
        --add traffic-light 24 36 --add traffic-light 27 40

## Adding a new room

1. Copy an existing `.tmj` (or seed one from a config room with
   `python3 tools/config_to_tiled.py <RoomName>`), save it as
   `tiled/<roomname>.tmj`.
2. Add a `rooms.<RoomName>` entry to `config.json` (npcs/objects can be empty;
   layers can be empty — the `.tmj` supplies the map).
3. Point a transporter at it from another room's `Meta` layer.

## Porting more Godot .tscn maps

The pipeline that produced all four rooms is committed in `tools/`:

1. `tools/render_rect.py RX0 RX1 RY0 RY1 out.png` — render a candidate rect
   of the Godot overworld (`Scenes/tokyo/tokyo_outside.tscn`, or the scene
   named by `PORT_SCENE`) to pick a district's bounds.
2. `PORT_ROOM=<Name> PORT_RECT="RX0,RX1,RY0,RY1" python3 tools/doport.py` —
   port that rect `.tscn → config.json` room (slices atlas tiles into
   `assets/sprites/`, builds layers/collision/Y-sort data, merges into the
   existing config preserving other rooms and hand-added transporters).
3. `python3 tools/config_to_tiled.py <Name> [<Other> ...]` — seed `tiled/<name>.tmj`. It takes any
   number of rooms (name every room the generator or its post-passes touched) and exits 2, writing
   nothing, if a name is not a room in `config.json` (room keys are case-sensitive).
4. `node tools/play.js lint <Name>` — QA gate (it reads the Tiled map); fix any ERRORs before shipping.

Once seeded, Tiled is the editor — don't hand-edit the generated `.tmj` back
into config. (The repo-root `tools/parse_godot_scene.py` scripts are an older
stale v1 pipeline; prefer `doport.py`.)

## Rendering a map without the Tiled app

`node tools/play.js render <Room> out.png [--scale 0.5] [--colliders]` draws
`tiled/<room>.tmj` in the game's own draw order (feet Y-sort, Tops bias; no
dependencies) — use it wherever these docs say `tmxrasterizer` if Tiled isn't
installed. `tools/make_worldmap.py` falls back to it automatically.

## Gotcha ledger

- **`generate_machi.py` is out of sync with the live config** — Machi has
  accumulated hand/pipeline edits the generator doesn't know about (blog-NPC
  dated states, ad signage, hidden seam transporters as data). Re-running it
  wholesale WIPES those and resurrects the legacy `Konbini` room. Until the
  generator learns them, make Machi changes surgically (config edit +
  `config_to_tiled.py Machi`) and mirror the intent in the generator source.
- **World seams are road-aligned by design** (`devhouse.world`): every
  adjacent room pair draws the same connecting road on both sides of the
  seam. A crossing is just hidden transporters on the edge cells of that road
  (arrive one cell inside the twin's trigger) plus dressing — lantern pairs,
  or a torii straddling the road (legs collide, top on Tops). Never build a
  crossing as a door-band "building"; transit must continue in the walking
  direction.
- **Track rows in ported rooms are sealed cell-by-cell** (`gk_blank` under
  the `train-track` Over Floor sprite). A road crossing the tracks needs its
  two cells unsealed — that's a level crossing, precedent exists.
- **`Scenes/osaka/osaka_outside.tscn` is not Osaka** — it is an older copy of
  the Tokyo overworld (garden, market, Tokyo Station placeholder). The Osaka
  room is generated (`tools/generate_osaka.py`). `doport.py` / `render_rect.py`
  accept `PORT_SCENE=<repo-relative .tscn>` should a real second scene appear.
- **`seal_tracks.py` with no arguments re-seals Palace's level crossing**
  (cells 0,5 and 1,5). Pass the rooms you mean: `seal_tracks.py Osaka`.
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
- **`extract_city.py` needs a Japanese font** for the discount-store sign (`generate_ads.find_font()`); in
  a sandbox that hides `/System/Library/Fonts` it stops before writing that sprite.
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
  `tools/extract_shrine.py` re-cuts the blue roof from the atlas using the
  rect in `Assets/Tilemap/GuttyKreum.tres` (tile `shrine-top`, 160x192 like the
  red one — it used to be 160x160, which cut the eaves flat) and refuses a
  section whose art touches its edge. `shrine-top_0_0` carries `depthBias: 1`
  so it wins the depth tie with the `temple-hallway` roofs either side of the
  Tokyo hall (without it one eave corner drew over the hallway and the other
  under it, by creation order).
- **No rubbish bins** (issue #19): `node tools/play.js lint` fails with `rubbish-bin` if ANY room places a bin / dumpster /
  trash-can sprite (it scans the whole config and every `tiled/*.tmj` on every run, whatever `--room` says). The interior pack's `office-bin` is retired -
  use `izakaya-stool_0_0` for a seat and a plant / `office-watercooler` for a corner filler.
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
