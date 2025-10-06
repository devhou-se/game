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

- `index.html` - Entry point, loads Phaser CDN and game scripts
- `game.js` - Phaser game configuration (viewport: 800×600, physics setup)
- `GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `Character.js` - Character movement class with grid-based tweening

### Core Constants (GameScene.js)

- `GRID_SIZE`: 64 pixels per cell
- `WORLD_SIZE`: 1024 pixels (16×16 grid)
- `DEADZONE_CELLS`: 4 (creates effective 5×5 cell camera deadzone)
- `MOVE_DURATION`: 200ms per cell movement

### Grid-Based Movement System

Characters move in discrete grid cells using Phaser tweens. Movement is collision-checked before execution. The system supports:
- Diagonal movement with path collision detection
- Speed multipliers (e.g., Shift key doubles speed by halving duration)
- Movement queuing during active tweens

Player movement bounds are calculated based on camera deadzone to prevent camera leaving world bounds.

### Room System

Rooms are defined in `GameScene.rooms` with:
- `name`: Display name
- `npcs`: Array of NPC character objects
- `objects`: Array of static objects with `{gridX, gridY}` (no labels, block movement)
- `transporters`: Array of transporter objects with `{gridX, gridY, targetRoom, targetX, targetY}`

Room transitions use camera fade effects (250ms fade out, 250ms hold, 250ms fade in) and block input during transition via `isTransitioning` flag.

### HUD System

Semi-transparent bar at top showing: `devhou.se | {currentRoom} | {date}`
- Uses `window.devicePixelRatio` for retina display text rendering
- Fixed to camera with `setScrollFactor(0)`
- Depth 1000+ to render above game elements

## Asset Generation

Python scripts in root generate 64×64 PNG tiles:
- `generate_tile.py` - Player tile (yellow border)
- `generate_npc_tile.py` - NPC tile
- `generate_transporter_tile.py` - Transporter tile (green border)
- `generate_object_tile.py` - Object tile (black border)
- `generate_grid.py` - Background grid

Run with: `python3 generate_<type>.py`

## Key Implementation Details

### Collision Detection
All intermediate cells in movement path are checked for:
- Objects (static obstacles)
- Stationary character positions
- Moving character destinations
- Path crossing (swap detection)

### Character Sprite Positioning
Sprites are centered at: `gridPos * GRID_SIZE + GRID_SIZE/2`

### Input Handling
Arrow keys move 1 cell, Shift doubles speed (not distance). Input blocked when `player.isMoving` or `isTransitioning`.
