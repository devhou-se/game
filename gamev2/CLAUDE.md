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
- `assets/portraits/` - Optional hand-drawn character portraits (`manifest.json` + `<name>.png`, see its README)
- `src/Voice.js` - Spoken NPC dialogue (lazy per-line audio clips) and the shared mute setting
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
- **Hidden debug menu**: triple-press backtick (``` within a second) — rows for
  the grid view/inspector, the N/E/X flag keys, map-click travel, a time-of-day
  pin (AUTO/day/dusk/night/dawn, same effect as `?tod=`), exact wallet amount
  (prompt), and noclip (all default off, persisted in localStorage). Deliberately
  absent from the Controls overlay. Map-click travel on the menu's Map overlay
  only works when its toggle is on.
- Input blocked when `player.isMoving` or `isTransitioning`
- Supports diagonal movement with simultaneous key presses
