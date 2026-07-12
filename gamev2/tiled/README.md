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
   of the Godot overworld (`Scenes/tokyo/tokyo_outside.tscn`) to pick a
   district's bounds.
2. `PORT_ROOM=<Name> PORT_RECT="RX0,RX1,RY0,RY1" python3 tools/doport.py` —
   port that rect `.tscn → config.json` room (slices atlas tiles into
   `assets/sprites/`, builds layers/collision/Y-sort data, merges into the
   existing config preserving other rooms and hand-added transporters).
3. `python3 tools/qa_port.py` — QA gate; fix any ERRORs before shipping.
4. `python3 tools/config_to_tiled.py <Name>` — seed `tiled/<name>.tmj`.

Once seeded, Tiled is the editor — don't hand-edit the generated `.tmj` back
into config. (The repo-root `tools/parse_godot_scene.py` scripts are an older
stale v1 pipeline; prefer `doport.py`.)

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
- **`tmxrasterizer` draws collider markers and Meta pins** — red boxes/pins
  in renders are debug art, not in-game visuals.
- A probe that prints `?` for "any sprite" hides colliders stacked under
  sprites — check per-layer before assuming a cell is walkable.
