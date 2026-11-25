# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a browser-based 2D grid game built with Phaser 4.2.0. It features grid-based movement, a room/teleportation system, and Python-generated sprite tiles.

## Technology Stack

- **Engine**: Phaser 4.2.0 (loaded via CDN — jsdelivr, since cdnjs does not yet host 4.x)
- **Languages**: JavaScript (ES6+ classes)
- **Asset Generation**: Python 3 with PIL/Pillow
- **No Build Process**: Direct HTML file execution

## Running the Game

**Option 1: Direct file access**
Open `index.html` directly in a web browser. No build step required.

**Option 2: Local server (recommended)**
```bash
python3 -m http.server 8000
```
Then navigate to `http://localhost:8000` in your browser.

## Architecture

### File Structure

- `index.html` - Entry point, loads Phaser CDN and game scripts from `src/`
- `config.json` - JSON configuration file defining game constants, rooms, NPCs, and objects
- `tiled/*.tmj` - Room maps, authored in the Tiled editor (the map source of truth at
  runtime — see `tiled/README.md`; config.json's room layers are only a fallback)
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
- `src/TitleScreen.js` - Title / splash screen shown at boot (cast line-up, press SPACE / tap to start)
- `src/Intro.js` - New-player intro (who devhouse is, controls as keycaps, where to start); replayable from the menu as How to Play
- `assets/portraits/` - Optional hand-drawn character portraits (`manifest.json` + `<name>.png`, see its README)
- `src/Voice.js` - Spoken NPC dialogue (lazy per-line audio clips) and the shared mute setting
- `src/AmbientTrains.js` / `src/AmbientBoats.js` - Decorative passing trains and moat boats (see Ambient Traffic)
- `editor/` - Visual editor for editing game configuration
  - `editor/index.html` - Entry point for the visual editor (access at `/editor/`)
  - `editor/GridEditor.js` - Main editor grid and placement logic
  - `editor/ConfigManager.js` - Config loading/saving functionality
  - `editor/editor.js` - Editor UI and interaction handling

### Visual Editor

A WYSIWYG visual editor is available for editing game configuration without manually editing JSON. Access it by running a local server and navigating to `/editor/`:

```bash
python3 -m http.server 8000
# Navigate to http://localhost:8000/editor/
```

**Features:**
- Visual grid editing with actual game sprites and background
- Room management (create, delete, switch between rooms)
- NPC placement and dialogue editing
- Object placement for obstacles
- Transporter system with visual targeting
- Custom boundary polygon editing (define non-rectangular room shapes)
- Sprite management and upload
- Config import/export
- Drag-and-drop item repositioning

### Core Constants (config.json)

All game constants are loaded from `config.json` and applied in GameScene.create():
- `gridSize`: 64 pixels per cell
- `worldWidth`: 960 pixels (15 grid cells wide)
- `worldHeight`: 640 pixels (10 grid cells tall)
- `deadzoneCells`: 4 (creates effective 5×5 cell camera deadzone)
- `moveDuration`: 200ms per cell movement
- `npcWanderInterval`: 5000ms between NPC wander attempts
- `npcWanderRadius`: 2 cells from NPC spawn point

### Grid-Based Movement System

Characters move in discrete grid cells using Phaser tweens. Movement is collision-checked before execution. The system supports:
- Diagonal movement with path collision detection
- Speed multipliers (e.g., Shift key doubles speed by halving duration)
- Movement queuing during active tweens

Player movement bounds are calculated based on camera deadzone to prevent camera leaving world bounds.

### Room System

Rooms are defined in `config.json` and loaded into `GameScene.rooms`. Each room has:
- `name`: Display name
- `boundary`: Array of [x, y] points defining a polygon boundary (optional, defaults to rectangular world bounds)
- `npcs`: Array of NPC definitions with position (absolute or offset from center), sprite, name, and dialogue.
  An NPC may also carry dated state updates under `states` (`{"YYYY-MM-DD": {fields}}`): at load, every
  state dated on-or-before the game date is applied over the base definition in chronological order —
  so viewing July 27 shows the July 26 update if the next one is July 28. The game date defaults to
  today and can be overridden with `?date=YYYY-MM-DD`; a state of `{"present": false}` removes the NPC
  from that date. Author states with `python3 tools/npc_state.py <Room> <Npc> <date> --dialogue ... --pos X,Y`
  (see `src/utils/NpcStates.js`)
- `objects`: Array of static obstacles with position (absolute or offset from center) that block movement
- `transporters`: Array of teleport points with position, targetRoom, and target position

Position system supports both absolute grid coordinates (`gridX`/`gridY`) or center-relative offsets (`gridOffsetX`/`gridOffsetY`).

Room transitions use camera fade effects (250ms fade out, 250ms hold, 250ms fade in) and block input during transition via `isTransitioning` flag.

**Boundary System:**
- Each room can define a custom polygon boundary to restrict player movement
- Boundaries are arrays of grid coordinate points: `[[x1,y1], [x2,y2], [x3,y3], ...]`
- If no boundary is specified, defaults to rectangular bounds matching world dimensions
- Player movement is validated using point-in-polygon detection (cell center must be inside boundary)
- Boundaries can create non-rectangular rooms (L-shapes, hexagons, irregular polygons, etc.)
- The visual editor provides a boundary editing tool for creating custom shapes

### Ambient Traffic (issue #29)

Purely decorative movers that make a room feel alive. Both are built in `GameScene.create()`, re-armed by
`RoomManager.switchRoom()` through `onRoomChange(roomKey)` (which also destroys whatever is on screen), find
their route in the room's map data rather than in coordinates, have no collision, and send the first one
3-10s after you enter a room and another every 15-40s after it finishes.

- **`AmbientTrains`** - any room with `train-track*` tiles that is not a `stations` room (Palace, Inaka,
  Yukimura) gets a train running the topmost track row, off-screen edge to off-screen edge, depth 48.
- **`AmbientBoats`** - any room with straight moat tiles (today: the Tokyo moat) gets a boat. A "run" is a
  line of consecutive cells holding the same plain `moat-<north|south|east|west>` tile; `-rocks` tiles,
  corner pieces and gaps end a run, so a boat never crosses rocks, the bridge gap in the south moat or the
  stone bank. Runs too short for a boat to travel `MIN_TRAVEL` are dropped. The open-water strip inside the
  tile is measured from the tile image itself (`waterBand`: the longest stretch of the dominant colour
  across the middle of the tile), so no per-tile offsets are hard-coded. A boat fades in at one end of a
  run, drifts to the other at `SPEED` with a small bob and fades out - it cannot leave by the screen edge
  the way a train does. Runs with a boat's length of water on camera (below the HUD bar) are preferred.
  Depth is `calculateLayerDepth(1) + 1`: above the flat ground/water layers, below everything Y-sorted.
  Because scenery standing on the near bank is drawn over the water, `clearWater()` narrows each run's band
  to the lanes that room sprites of higher depth leave in view (a lane covered for more than `COVER_LIMIT`
  of the run is hidden) and the run is dropped if what is left is narrower than a boat. That is why Tokyo's
  north moat has no boats: the `blue-wall-short` palace wall hides the lower half of its channel. Tokyo ends
  up with 8 runs (5 south, 1 west, 2 east). A tree crown overhanging one end of a run is allowed.
- **Boat art is procedural** (`AmbientBoats.buildTexture`): no boat sprite exists, so each livery
  (`AmbientBoats.LIVERIES`: `wood`, `lacquer`, `white`) is drawn to a canvas on the tile art's 4x pixel
  grid, once per facing, under the key `boat-<livery>-<right|left|down|up>`. `ensureTexture()` only draws a
  key that is not already loaded, so real art replaces it by loading a sprite under the same key (keep it
  within `AmbientBoats.size()`, or update `ART`, since run fitting uses that size).
- **Testing** - both expose `cross()` to send one immediately (a no-op in a room with no track / no water):
  `game.scene.keys.GameScene.ambientTrains.cross()` / `.ambientBoats.cross(run, dir, livery)` (all optional;
  `run` is an entry of `ambientBoats.runs`, `dir` is `1` or `-1`). A new water tile family needs its name
  added to `AmbientBoats.WATER_TILE`; ponds are not waterways.

### HUD System

Semi-transparent bar at top showing: `{game.title} | {currentRoom} | {game.date}` with clickable menu button
- Title and date loaded from `config.json`
- Uses `window.devicePixelRatio` for retina display text rendering
- Fixed to camera with `setScrollFactor(0)`
- Depth 1000+ to render above game elements
- Menu button (right-aligned) opens MenuManager on click

### Title Screen and Character Portraits (issue #9)

**Title screen** (`src/TitleScreen.js`, `scene.titleScreen`): shown on every page load, after
`window.hideLoader()` and BEFORE the first-run character creator — `GameScene.create()` passes the rest of
the boot flow (the `CharacterCreator.shouldAutoShow()` check) as the `show(onStart)` callback. It draws the
game title (`config.game.title`), the cast (`CharacterSelect.available()`) lined up at 5x with a small hop
travelling along the line, and a blinking start prompt, at depth 9000 on an opaque backdrop the colour of
the HTML loader.
- SPACE / ENTER / ESC (so touch A and B too) or a tap/click anywhere dismisses it. While it is up it is
  **priority 0 in `InputHandler.handleInput()`**: no movement, menu or overlay input reaches the game.
  The triple-backtick debug chord is ignored too (`DebugManager.onBacktick` checks `titleScreen.isVisible()`).
- **`?notitle=1` skips it** — use it in tests and dev URLs that drive input straight after boot
  (the loader contract is unchanged: `#loader` is removed as before and the scene is live underneath).
- **In-game reloads skip it once**: `setGameDate()` (Time Travel / the HUD date) navigates with a full page
  load, so it sets the one-shot `sessionStorage` flag `gamev2_skip_title` first and `TitleScreen.shouldShow()`
  consumes it — a date hop lands straight back in the world, while a manual refresh of that URL shows the
  title again. Any future in-game action that reloads the page should set the same flag.

### New-Player Intro (issue #39)

`src/Intro.js` (`scene.intro`): a three-page overlay in the usual panel style (depth 2000-2003).
1. **Welcome to devhouse** — the friends (names parsed from `config.credits` "Role: Name" lines), the
   Japan trip, NPC lines coming from the trip's blog posts, and the HUD date picking the day ("Time Travel
   in the menu" to visit a day of the trip — the default date is today's, which is not a trip day, so the
   copy must not imply the player starts on one).
2. **How to play** — move / sprint / interact / talk / menu drawn as keycaps; when
   `touchControls.enabled` the same rows are drawn as the on-screen d-pad, sprint pill and A / B buttons,
   plus a one-line keyboard reminder (touch controls are also on for touchscreen laptops).
3. **Where to start** — there is no quest system, so it points at real things: the friends around
   Tokyo (same word as page 1), exploring, and Paint the Board (with the live progress bar from `achievementManager`).

Fishing controls and map travel are **deliberately absent** (fishing is learned when a rod is bought; map
travel is a debug feature) — keep them out when editing the copy.
- **Input**: SPACE / ENTER (touch A) or a tap anywhere turns the page and the last page closes it; ESC
  (touch B) skips the lot. It is the first entry in `InputHandler`'s overlay list, so nothing moves or
  opens underneath, and `DebugManager.onBacktick` ignores the debug chord while it is up.
- **Boot flow is strictly sequential, never stacked**: loader → title → (first visit) character creator →
  intro → world. `CharacterCreator.show({ onClose })` runs the callback once from `hide()` — confirmed or
  cancelled — and `GameScene.create()` uses it to open the intro.
- **Gate**: localStorage `gamev2_intro_seen`. `Intro.shouldAutoShow(firstVisit)` sets it to `pending` when a
  first visit begins (so a reload half way through the creator or the intro still gets the intro) and
  `hide()` sets it to `1` (finished or skipped). A returning player — a character already saved, key absent
  — is never shown it automatically, and a Time Travel reload does not replay it.
- **`?nointro=1`** suppresses the automatic showing (and leaves the gate untouched) — combine with
  `?notitle=1` in tests that start from a fresh profile. Tests that pre-seed `gamev2_character` never see it.
- **How to Play** in the ESC menu replays it at any time (`scene.intro.show()`).

**Dialogue portrait** (`DialogueManager.showPortrait`): the speaker is shown dating-sim style as a large
bust in the same wooden frame as the blog photo (`drawFrame`, shared by both), standing on the panel's
top-left corner with the name plate bridging frame and panel. The blog-photo frame keeps the top-right;
the two never overlap (20px gap) and share a bottom edge (`panelY - 12`). The bust is the head-and-shoulders band of `<name>_front_frame_0`
(`DialogueManager.BUST`, a 48x40 crop) at 5x in a 240x200 window. A speaker whose sprite is not a
directional `<name>_front` 64px character sprite falls back to the old look (`showFullSprite`: whole sprite
at 2x centred above the panel, name above it).

**Real art drop-in, no code change**: put `assets/portraits/<name>.png` in place and add `<name>` to
`assets/portraits/manifest.json` (`{"portraits": ["bailey", ...]}`, shipped empty). `preload()` loads only
the listed names as textures `portrait-<name>` (so a character without art never 404s; a malformed
manifest is treated as empty; a listed name with no PNG logs one 404 and falls back to the sprite), and both the dialogue
frame and the title line-up use that texture instead of the sprite when it exists. Size/format rules are in
`assets/portraits/README.md` (240x200 window, 6:5; 240x200, 120x100 or 48x40 PNGs scale cleanly).
No hand-drawn portraits exist yet — everything shown today is derived from the overworld sprites.

### Playing as the Cast: Character Menu and the Name Easter Egg (issues #15, #45)

`src/CharacterSelect.js` (Menu → Character) swaps the player to a cast member with a full sprite set
(`CharacterSelect.available(config)`: james, bailey, damian, dylan, julia). The whole swap lives in ONE
place, `CharacterSelect.become(scene, name)`: it writes `localStorage.gamev2_character = <name>`, swaps the
live player sprite, and calls `syncNpcPresence()` (that person's NPC leaves the world) and
`syncPlayerNameLabel()`. `CharacterSelect.applySaved` restores it on reload.

`src/CharacterCreator.js` (first-run, or Menu → Create Character) has an Easter egg on top of that: type one
of those names as your own (`castMatch()` — whole name, trimmed, case-insensitive; "baileyx" and the
sprite-less credits names Gloria/Yashuk do nothing) and the live preview flips to that person's own sprite,
the part/colour rows and RANDOM dim and lock, and a "hey, it's Bailey!" hint appears; it all reverts as soon
as the name stops matching. A creation that was already saved under one of those names opens as itself
(`eggArmed` is false until the name box is edited). START/ENTER then calls `CharacterSelect.become` and toasts "You are Bailey!"
instead of saving a composite. It deliberately skips `CharacterCreator.save()`, so an earlier creation in
`gamev2_custom_character` survives and is still offered as the custom row in Menu → Character.

### Voiced Dialogue (text-to-speech)

NPC dialogue can be read aloud. A resolved NPC state carrying `"voice": <voiceId>` (passed through
`syncNpcPresence` → `NPCManager.spawnNPC` exactly like `"photo"`) has one clip per dialogue line at
`assets/voice/<voiceId>/<lineIndex>.mp3` (0-based index into that state's `dialogue`).

- **Client** (`src/Voice.js`, `scene.voice`): `DialogueManager.updateText()` calls `voice.playLine()` as each
  line is shown (which stops the previous line's clip) and `close()` calls `voice.stop()`. Clips are NOT
  preloaded — the source is set at dialogue time on ONE shared `HTMLAudioElement`, which is created and
  unlocked (10 ms of silence played inside the first key press / tap, capture-phase listeners removed once
  it succeeds) because `playLine()` runs from Phaser's update loop and iOS Safari only lets a
  gesture-played element start from there (the unlock is untested on a real iOS device). An NPC without `voice`, a clip
  that fails to load/decode, or a rejected `play()` is a silent no-op (the only trace of a 404 is the
  browser's own network log line, which is why the pipeline never records a partial clip set).
- **Mute**: the ESC menu's `Voices: ON/OFF` row (flips in place, menu stays open) persists in localStorage
  `gamev2_voice_muted` (`'1'` = muted; default ON). It is the game's shared audio setting — other audio
  features should read `scene.voice.isMuted()` / subscribe with `scene.voice.onMuteChange(fn)`.
- **State merging**: clips belong to the exact lines they were generated from, so in `resolveNpc` a state
  that sets `dialogue` without naming `voice` clears the inherited voice (and `tools/npc_state.py --dialogue`
  drops a state's `voice`).
- **Pipeline** (`tools/post_voice.py`, called by `tools/blog_to_npc.py` after the photo import): with
  `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_<NPC>` (e.g. `ELEVENLABS_VOICE_BAILEY`, `_DAMIAN`, `_DYLAN`,
  `_JULIA`) set, each dialogue line is POSTed to the ElevenLabs text-to-speech REST API (stdlib `urllib`)
  and the dated state gets `"voice": "<npc>-<date>-<hash>"`. Optional: `ELEVENLABS_VOICE_<NPC>_DRUNK` (used
  when the LLM's new `drunk` boolean says the post reads as drunk; the state then also carries
  `"drunk": true`) and `ELEVENLABS_MODEL` (default `eleven_multilingual_v2`). Best-effort like photos:
  unconfigured or failing, it logs one `voice: ... — skipped` line and the placement lands with
  `"voice": null`. A clip set is all-or-nothing, and an unchanged re-run reuses the clips on disk.
  After every config write `prune_voices()` deletes clip directories no state references any more, so the
  pipeline workflow must commit `gamev2/assets/voice` (additions and deletions, e.g. `git add -A`) together
  with `config.json` — a recorded `voice` whose clips were not deployed 404s on every line.
- **Backfill**: `python3 tools/blog_to_npc.py --voice-backfill [--dry-run]` voices existing dated states
  that have dialogue but no voice (no LLM call, no placement). `--dry-run` prints the line/character
  totals ElevenLabs would bill for.
- **Not live yet**: no API key or cloned voice ids exist, so no state has a `voice` and the game is silent.

### Featured locations / landmarks (issue #17)

Named landmarks are ordinary multi-cell sprites on a room's `Collidables` layer (Y-sorted by their feet:
solid at the base, walk-behind above), each wrapped in a prefab so generators can `b.stamp()` them:

| Landmark | Room | Sprite key | Art |
|---|---|---|---|
| Tokyo Tower | Palace (feet continue into Park) | `tokyo-tower_0_0` | line-art placeholder (ported from Godot) |
| Tokyo Station | Palace | `tokyo-station_0_0` | line-art placeholder (ported from Godot) |
| Tsutenkaku Tower | Osaka | `tsutenkaku_0_0` | line-art placeholder drawn by `tools/generate_tsutenkaku.py` |
| Dotonbori entrance arch | Osaka | `dotonbori-arch_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Dotonbori ferris wheel | Osaka | `dotonbori-wheel_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |

- **Osaka** (`tools/generate_osaka.py`, 50x40) is a generated town reachable only by train, like Yukimura:
  station house -> arch over the main street -> the canal bridge -> Tsutenkaku on its plaza, with the ferris
  wheel on the north bank. The tower stands on the street's axis, so a shrub garden fills the ground behind
  it and the street forks round (otherwise the player walks hidden behind the sprite for ten cells); the
  platform-edge fence and the continuous border hedges keep the player off the ballast and out from behind
  the fences. `OsakaStation` is registered in `tools/generate_stations.py`
  (`STATIONS` / `TOWN_DOORS`) and so in config `stations`; Osaka sits detached in `devhouse.world`.
  The legacy `Scenes/osaka/osaka_outside.tscn` is an old copy of the Tokyo overworld, not Osaka — do not
  port it (`tools/doport.py` / `render_rect.py` do take `PORT_SCENE=<path>` for a genuinely different scene).
- **Adding a landmark**: put a cell-aligned PNG in `assets/sprites/` (register `spriteMetadata` with
  `anchorX = 32/width`, `anchorY = 32/height`, plus `tileNames`), add a prefab spec to
  `tools/make_prefabs.py` (colliders = the base cells only), stamp it from the room generator, and add it to
  `LANDMARKS` in `tools/blog_to_npc.py` so blog NPCs can be placed there. A landmark entry may carry a third
  element `(dx, dy)`: the cell, relative to the sprite's top-left, where a visitor stands (tall sprites'
  own cell is their tip, not their foot).
- **World map without Tiled**: `tools/make_worldmap.py` uses `tmxrasterizer` when Tiled is installed and
  otherwise (or with `--pil`) draws the rooms itself via `tools/render_room.py`, which is also the
  "look at the render" step for a new room: `python3 tools/render_room.py <Room> out.png [--scale .5] [--colliders]`.
- `tools/generate_stations.py` keeps an existing station room's NPCs (the blog pipeline parks dated NPC
  states there), and `tools/seal_tracks.py` takes room names — run it bare and it re-seals Palace's level
  crossing.

## Asset Generation

Python scripts in `tools/` directory generate 64×64 PNG tiles saved to `assets/`:
- `generate_tile.py` - Player tile (yellow border) → `assets/single-tile.png`
- `generate_npc_tile.py` - NPC tile → `assets/npc-tile.png`
- `generate_transporter_tile.py` - Transporter tile (green border) → `assets/transporter.png`
- `generate_object_tile.py` - Object tile (black border) → `assets/object-tile.png`
- `generate_grid.py` - Background grid → `assets/background-grid.png`

Run with: `python3 tools/generate_<type>.py`

## Key Implementation Details

### Collision Detection
All intermediate cells in movement path are checked for:
- Room boundaries (polygon containment check)
- Objects (static obstacles)
- Stationary character positions
- Moving character destinations
- Path crossing (swap detection)

### Character Sprite Positioning
Sprites are centered at: `gridPos * GRID_SIZE + GRID_SIZE/2`

### Input Handling
The whole game runs on WASD/arrows + SPACE/ENTER + SHIFT, with ESC as the single
system key — no other bindings (no T shortcut, no ,/. month keys). Touch controls
synthesize the same keys (d-pad → WASD, A → SPACE, B → ESC).
- **Movement**: WASD or arrows move 1 cell, Shift doubles speed (not distance)
- **Menu / overlays**: ESC toggles the menu (and closes any overlay), W/S or ↑/↓ navigate, SPACE/ENTER activates
- **Dialogue**: SPACE/ENTER advances, ESC closes
- **Title screen**: SPACE/ENTER/ESC or a tap starts the game (`?notitle=1` skips the screen)
- **Intro**: SPACE/ENTER or a tap turns the page, ESC skips (`?nointro=1` skips the first-visit intro)
- **Hidden debug menu**: triple-press backtick (``` within a second) — rows for
  the grid view/inspector, the N/E/X flag keys, map-click travel, a time-of-day
  pin (AUTO/day/dusk/night/dawn, same effect as `?tod=`), exact wallet amount
  (prompt), and noclip (all default off, persisted in localStorage). Deliberately
  absent from the Controls overlay. Map-click travel on the menu's Map overlay
  only works when its toggle is on.
- Input blocked when `player.isMoving` or `isTransitioning`
- Supports diagonal movement with simultaneous key presses
