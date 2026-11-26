# Architecture

The file map of `src/`, the core constants, grid movement and collision.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## Architecture

### File Structure

- `index.html` - Entry point, loads Phaser CDN and game scripts from `src/`
- `config.json` - JSON configuration file defining game constants, rooms, NPCs, and objects
- `tiled/*.tmj` - Room maps, authored in the Tiled editor (the map source of truth at
  runtime — see `tiled/README.md`; config.json's room layers are only a fallback)
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/systems/Viewport.js` - Where the canvas sits in the window, and where the touch controls go (see Small Viewports and Touch)
- `src/systems/UIScale.js` - World zoom, HUD magnification and overlay fitting for small, cropped or touch-covered canvases (see Small Viewports and Touch)
- `src/systems/LandmarkView.js` - The camera looks up in front of a landmark marked in config `game.lookUp` (see Small Viewports and Touch)
- `src/utils/Hints.js` - The one helper that words key hints for keyboard or touch (see Small Viewports and Touch)
- `src/utils/JapaneseFont.js` + `fonts/` - The pixel fonts, and the Japanese face added to each of them (see Fonts and Japanese Text)
- `src/utils/Places.js` - The towns as real places in Japan for the Map overlay: config `places`, which town a room is in, who is where, label layout (see The Map overlay in `hud-input-touch.md`)
- `src/utils/Trips.js` - The devhouse trips as data: which trip a date belongs to, and everything that follows (see Trips)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/systems/Occlusion.js` - Scenery fades while someone stands hidden behind it, and their name label
  with it (see "Walking behind things" in `occlusion.md`)
- `src/utils/Interactions.js` - The one table of what a bump opens (shops, ponds, clocks, a home's flavour lines, the drinking
  table, a shrine's offering box and fortune stand). `Shop`, `Fishing`, `DrinkingGame`, `ShrineVisit`, `GameScene` and `tools/play.js` all read it; add a rule here
  rather than a tile-name check in a feature file
- `src/ShrineVisit.js` - The offering box and the fortune stand inside a shrine's worship hall (see "Shrine worship halls"
  in `landmarks-and-towns.md`)
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
- `src/Energy.js` - The rules of the energy meter and the konbini stamp card (`Energy`, `Stamps`: pure functions, no Phaser);
  `Shop` holds the state and draws the meter (see "Energy and the stamp card" in `shop-and-economy.md`)
- `src/DatePicker.js` - Time Travel calendar (menu, or the HUD date). Marks three different days: today (gold), the day the
  game is on (blue — a trip day, usually a year of months from today) and the cursor (green box). The legend names only
  colours that are on the month shown; the jump row under the selected date moves the cursor to today / the game's day (click, tap, or SHIFT + up / down), and the trips row above it to a trip
- `src/TitleScreen.js` - Title / splash screen shown at boot (cast line-up, press SPACE / tap to start)
- `src/Intro.js` - New-player intro (who devhouse is, controls as keycaps, where to start); replayable from the menu as How to Play
- `src/RotatePrompt.js` - "Rotate your phone for a better experience": a brief toast on a portrait phone (see `hud-input-touch.md`)
- `assets/portraits/` - Optional hand-drawn character portraits (`manifest.json` + `<name>.png`, see its README)
- `src/Voice.js` - Spoken NPC dialogue (lazy per-line audio clips) and the shared mute setting
- `src/AmbientTrains.js` / `src/AmbientBoats.js` - Decorative passing trains and moat boats (see Ambient Traffic)
- `src/TrafficLights.js` - Decorative traffic-signal cycle (see Street accessories)
- `editor/` - Canvas editor for `config.json` room data (see `editor/README.md`)
- `studio/` - Read-only view of the whole world (see Studio in `tools-play-test-studio.md`)

### Core Constants (config.json)

All game constants are loaded from `config.json` and applied in GameScene.create():
- `gridSize`: 64 pixels per cell
- `worldWidth`: 960 pixels (15 grid cells wide)
- `worldHeight`: 640 pixels (10 grid cells tall)
- `deadzoneCells`: 4 (creates effective 5×5 cell camera deadzone)
- `moveDuration`: 200ms per cell movement
- `npcWanderInterval`: 5000ms between NPC wander attempts
- `npcWanderRadius`: 2 cells from NPC spawn point (a wandering NPC never steps onto a transporter or the cell beside one — `NPCManager.atDoorway` — so nobody blocks the cell in front of a door)

### Grid-Based Movement System

Characters move in discrete grid cells using Phaser tweens. Movement is collision-checked before execution. The system supports:
- Diagonal movement with path collision detection
- Speed multipliers (e.g., Shift key doubles speed by halving duration)
- Movement queuing during active tweens

Player movement bounds are calculated based on camera deadzone to prevent camera leaving world bounds.

## Key Implementation Details

### Collision Detection
All intermediate cells in movement path are checked for:
- Room boundaries (polygon containment check; in a stitched city: inside any district's boundary)
- Collision-layer tiles (`roomManager.isBlocked(x, y)` — a set lookup; collider markers have no sprite)
- Objects (static obstacles)
- Stationary character positions
- Moving character destinations
- Path crossing (swap detection)

### Character Sprite Positioning
Sprites are centered at: `gridPos * GRID_SIZE + GRID_SIZE/2`
