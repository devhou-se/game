# World Editor

A canvas editor for the room data in `config.json`, served at `/editor/`
(`python3 -m http.server 8000`, then `http://localhost:8000/editor/`).

It draws a room with the game's depth rules and has four tools:

- **Inspect** - click a cell to list every tile on it, with layer, depth and collision.
- **Collision** - paint or erase solid cells on the `Colliders` layer.
- **Transporter** - place a transporter, or click one to edit its target room, target cell and hidden flag.
- **Spawn** - set the player's start cell (`player.startRoom/X/Y`). Since trips are data the game starts a
  player at the `home` (or current `stays` cell) of the game date's trip in `config.trips`; `player.start*`
  is only the fallback for a config with no trips, and the seed the achievements / `play.js check`
  reachability use. So the tool moves both (`Trips.moveStart`): every trip `home` / `stays` cell that stood
  on the old start moves with it, and the status line names those trips. A trip that starts somewhere else
  (devhouse 3 in Sapporo) is left alone - edit its `home` in `config.json`. `play.js check` fails when
  `player.start*` and the first trip's `home` drift apart.

The left panel switches rooms, changes a room's size in cells, and toggles
layers, the collision overlay and the grid. Wheel zooms; shift-drag or
middle-drag pans.

## Saving

**Save config.json** downloads the edited file; replace `gamev2/config.json`
with it. The game loads rooms from `tiled/*.tmj`, so a change made here only
shows up in the game after:

```bash
python3 tools/config_to_tiled.py <Room>
node tools/play.js lint <Room>
```

## Files

- `index.html` - the page and its load order
- `app.js` - bootstrap and the tool registry
- `core/Config.js` - load, model and save the config
- `core/Depth.js` - the game's render geometry and depth maths; keep in step with `src/systems/RoomManager.js`
- `core/Textures.js` - loads the tile PNGs
- `render/RoomCanvas.js` - the canvas, pan and zoom, overlays
- `panels/` - room, layer, inspector and properties panels
- `styles/editor2.css` - the stylesheet

To look at the whole world rather than edit one room, use the read-only
studio at `/studio/`.
