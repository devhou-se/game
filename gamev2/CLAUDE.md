# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a browser-based 2D grid game built with Phaser 3.90.0. It features grid-based movement, a room/teleportation system, and Python-generated sprite tiles.

## Technology Stack

- **Engine**: Phaser 3.90.0 (loaded via CDN)
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
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
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
- `npcs`: Array of NPC definitions with position (absolute or offset from center), sprite, name, and dialogue
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
- **Movement**: Arrow keys or WASD move 1 cell, Shift doubles speed (not distance)
- **Menu**: ESC toggles menu, arrow keys navigate, Enter activates
- **Dialogue**: Space/Enter advances, ESC closes
- Input blocked when `player.isMoving` or `isTransitioning`
- Supports diagonal movement with simultaneous key presses
