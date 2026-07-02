---
name: generate-room
description: Generate a new gamev2 room (outdoor area or interior) from a prompt like "a bathhouse courtyard with a pond, lanterns and two houses, connected to the Park". Composes autotiled floors + Tiled-authored prefabs into a QA-clean, playable room wired into the world. Use whenever the user asks for a new room, area, town, garden, or shop interior for the game.
---

# Generate a game room from a description

You are generating a room for the Phaser game in `gamev2/`. Everything below
runs from the `gamev2/` directory. The exemplar for ALL of this is
`tools/generate_machi.py` (town + shop interior) — read it first, mimic it.

## 1. Understand the request

Extract from the user's prompt: room **name** (PascalCase, becomes the HUD
title), **size** (default ~48x34 outdoor, ~20x15 interior; minimum 20x15 —
the camera viewport is 1280x960), **objects wanted**, **mood/theme**, and
**which room it connects to** (default: pick the nearest sensible edge/road of
an existing room). If the user names objects that don't exist yet, say so and
substitute the closest available prefab rather than inventing sprites.

## 2. Discover the vocabulary (do not assume)

- Prefabs: `ls tiled/prefabs/` — houses (blue/red/black), seven-eleven,
  sign-7-11, shrine, torii-red, pagoda-small, bell-blue, fox-statue,
  lantern-red, lamp-blue, sakura-large/small, tree-green, shrub-large/small,
  vending-white/red, and whatever has been added since. Each prefab knows its
  sprites, collision, and `door` cells.
- Floor terrains (autotiled, paint with `b.autotile`): grass, dirt-outside,
  gravel, grey-brick, brown-brick, flat-grey-brick, light-concrete (all
  `<name>-autotile`). Water via `b.pond` (exactly 2 rows tall). 2x2 flower
  patches via `b.flowers`.
- Decor helpers on Builder: `plants`, `paver`, `fence`, `stairs`,
  `wall_stone` / `wall_panel` (1x2 solid wall segments, for interiors),
  `counter`. New composite objects belong in the prefab library: add a spec to
  `tools/make_prefabs.py`, rerun it, and the object is editable in Tiled.

## 3. Write the generator script

Create `tools/generate_<slug>.py` modeled on `generate_machi.py`:

```python
import roomgen as rg
from roomgen import rect
cfg = rg.load_config()
b = rg.Builder(W, H)
b.fill('grass-autotile')                    # outdoor base (interiors: autotile
                                            # light-concrete over the full rect)
b.autotile('gravel-autotile', rect(...))    # paths/streets/plazas
b.pond(x0, y0, x1)
b.stamp('house-blue', x, y)                 # doors seal solid by default
door = b.stamp('seven-eleven', x, y, seal=False)[0]   # open door for wiring
cfg['rooms']['Name'] = b.room('Name', npcs=[...], transporters=[...])
rg.save_config(cfg)
```

Composition principles that make rooms read well:
- Solid border ring (shrubs/trees/fences) so the player can't hug the void;
  leave gaps only at exits.
- Streets 2 cells wide; plazas modest (huge empty slabs look barren — fill
  with pavers, plants, lanterns at corners, a centrepiece prefab).
- Keep autotile regions chunky (9-piece sets have no inner corners).
- Trees/canopies must not overlap each other's footprints (QA catches it).
- Deterministic randomness only: `random.Random(<fixed seed>)`.
- NPCs via `rg.make_npc` on a free cell (they wander 2 cells).

## 4. Doors and connections

- A prefab door stamped with `seal=False` returns its cell: put a **hidden**
  transporter ON that cell into the interior; the interior's exit is hidden
  transporters on the door-mat cells, targeting the cell in FRONT of the door
  outside. Arrival cells must never be transporter cells (bounce loop).
- Room-to-room edges: visible transporters (`hidden=False`) on walkable edge
  cells, with a matching pair added to the other room's `transporters`.
- **CRITICAL**: the game reads transporters from each room's `.tmj` Meta
  layer, NOT config — after touching ANY room's transporters, regenerate that
  room's tmj too (`python3 tools/config_to_tiled.py <Room>`).

## 5. Build loop (iterate at least twice on looks)

```
python3 tools/generate_<slug>.py
python3 tools/qa_port.py --room <Name>        # must reach 0 errors; fix warnings
python3 tools/config_to_tiled.py <Name>       # + every room whose transporters changed
/Applications/Tiled.app/Contents/MacOS/tmxrasterizer tiled/<name>.tmj /tmp/<name>.png
```
LOOK at the render. Fix what reads badly (empty slabs, floating objects,
disconnected paths, banding floors). Known traps: `pagoda-floor` is a blue
ROOF texture; repeated single slab variants (brown/grey-brick-floor-tiles_*)
band badly — interiors want `light-concrete-autotile`.

For outdoor rooms, add the map to `devhouse.world` at a sensible non-
overlapping offset (64px cells; align connecting roads across the seam).
Interiors stay out of the world file.

## 6. Verify by playing (never skip)

Serve `gamev2/` (a server is usually already on :8000, else
`python3 -m http.server 8000`), then with Playwright:
- load the game: every room logs `[tiled] room ... loaded`, zero console
  errors/warnings (a "Sprite not found" warning means a missing
  spriteMetadata entry or bad key);
- config<->tmj parity for all rooms (`TiledAdapter.toRoom` vs `decodeConfig`
  room — compare layer tile maps; must be IDENTICAL);
- walk in through the real portal using held-key events (synthetic taps get
  swallowed: dispatch keydown, wait ~400ms/cell, keyup);
- collision probes via `!scene.collisionSystem.checkTileCollision([{x,y}])`
  on visually-solid and visually-open cells;
- screenshot the room's key vistas and actually look at them.

## 7. Ship

Commit directly to master (repo rules: no attribution, no PRs, no branches)
with the room script + config.json + tiled/*.tmj (+ devhouse.world), then
push. Leave the local server running and tell the user where to walk to reach
the new room.
