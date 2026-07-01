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

1. Open the room's `.tmj` in Tiled (e.g. `tiled/tokyo.tmj`).
2. Edit and save (keep the JSON `.tmj` format).
3. Refresh the browser — maps are fetched cache-busted, no build step.

## Map conventions (what the adapter expects)

- **One image-collection tileset** whose per-tile `image` filename **is** the
  sprite key (`../assets/sprites/<key>.png`). To use a new sprite, add its PNG
  to `assets/sprites/` and add it to the tileset in Tiled.
- **Tile layers** hold flat 1×1 ground (floor/path/water/colliders) — paint
  freely.
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

## Adding a new room

1. Copy an existing `.tmj` (or seed one from a config room with
   `python3 tools/config_to_tiled.py <RoomName>`), save it as
   `tiled/<roomname>.tmj`.
2. Add a `rooms.<RoomName>` entry to `config.json` (npcs/objects can be empty;
   layers can be empty — the `.tmj` supplies the map).
3. Point a transporter at it from another room's `Meta` layer.

## Porting more Godot .tscn maps

The old pipeline still exists for seeding: `tools/parse_godot_scene.py` and
friends (repo root `tools/`) go `.tscn → config room`, then
`tools/config_to_tiled.py` goes `config room → .tmj`. Once seeded, Tiled is
the editor — don't hand-edit the generated `.tmj` back into config.
