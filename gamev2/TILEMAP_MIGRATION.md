# Tilemap Migration Progress

## Overview
Migrating Tokyo and Osaka overworld rooms from Godot v1 to Phaser v2.

## Completed

### Phase 1: Core Infrastructure
- ✅ Created `TilemapManager.js` - Multi-layer tilemap system for Phaser 3
  - Supports floor, decoration, collision, overhead, and effects layers
  - Handles tilemap loading from JSON
  - Provides collision detection API

### Phase 2: Data Extraction
- ✅ Created `godot_tilemap_parser.py` - Extracts tilemap data from Godot .tscn files
  - Parses Godot's TileMap nodes
  - Converts Godot coordinate encoding to standard grid positions
  - Outputs Phaser-compatible JSON format

- ✅ Created `extract_tilemap_section.py` - Extracts manageable sections from large tilemaps
  - Extracts centered sections (default 30x20 tiles)
  - Generates tile usage statistics
  - Creates v2-compatible room configurations

- ✅ Extracted Tokyo and Osaka tilemap data:
  - **Tokyo**: 307x109 tiles total, extracted 30x20 section
    - Floor tiles: 456
    - Collision objects: 34
    - Unique tiles: 12
    - Files: `tokyo_section.json`, `tokyo_section_room.json`

  - **Osaka**: 175x108 tiles total, extracted 30x20 section
    - Floor tiles: 120
    - Collision objects: 0
    - Unique tiles: 4
    - Files: `osaka_section.json`, `osaka_section_room.json`

## Remaining Work

### Phase 3: Asset Preparation
1. **Create tileset image** - Generate a tileset atlas containing all tile graphics
   - Extract tiles from Godot tilesets or create placeholder tiles
   - Combine into single tileset image (64x64 per tile)
   - Tiles needed for Tokyo: IDs [100, 8, 157, 9, 164, 163, 4, 1, 7, 2, ...]
   - Tiles needed for Osaka: IDs [9, 8, 0, 11]

2. **Create tileset JSON** - Tiled-format JSON describing the tileset
   - Map tile IDs to positions in tileset image
   - Define tile properties (collision, etc.)

### Phase 4: Integration
3. **Update `config.json`** - Add Tokyo and Osaka room definitions
   - Add room entries with tilemap references
   - Configure starting positions
   - Add transporters between rooms

4. **Update `GameScene.js`** - Integrate TilemapManager
   - Import TilemapManager
   - Initialize in create()
   - Load tilemaps in preload()
   - Replace floor sprite rendering with tilemap rendering
   - Handle room transitions with tilemaps

5. **Update collision system** - Use tilemap collision layers
   - Integrate TilemapManager.hasCollisionAt() into movement validation
   - Remove sprite-based collision for tilemap rooms

### Phase 5: Testing
6. **Test Tokyo room**
   - Visual rendering correct
   - Collision detection working
   - Transitions working
   - NPCs can navigate

7. **Test Osaka room**
   - Visual rendering correct
   - Collision detection working
   - Transitions working
   - NPCs can navigate

## Technical Details

### Tile ID Mapping
Tokyo uses these tiles (most common):
- Tile 100: 224 occurrences (primary floor tile)
- Tile 8: 149 occurrences
- Tile 157: 145 occurrences
- Tile 9: 83 occurrences

Osaka uses these tiles (most common):
- Tile 9: 410 occurrences (primary floor tile)
- Tile 8: 190 occurrences
- Tile 0: 120 occurrences
- Tile 11: 84 occurrences

### File Structure
```
gamev2/
├── src/
│   ├── TilemapManager.js          ✅ Created
│   └── GameScene.js               ⏳ Needs update
├── assets/
│   ├── tokyo_tilemap.json        ✅ Full map data
│   ├── tokyo_section.json        ✅ 30x20 section
│   ├── tokyo_section_room.json   ✅ Room config
│   ├── osaka_tilemap.json        ✅ Full map data
│   ├── osaka_section.json        ✅ 30x20 section
│   ├── osaka_section_room.json   ✅ Room config
│   ├── overworld_tileset.png     ⏳ TODO: Create
│   └── overworld_tileset.json    ⏳ TODO: Create
├── tools/
│   ├── godot_tilemap_parser.py        ✅ Created
│   └── extract_tilemap_section.py     ✅ Created
└── config.json                    ⏳ Needs room entries
```

## Next Steps

The most practical next step is to create a simple tileset image with placeholder tiles:

1. Generate a tileset PNG with numbered tiles (0-200)
2. Create basic Tiled JSON for the tileset
3. Add Tokyo and Osaka to config.json
4. Update GameScene.js to use TilemapManager
5. Test the rooms

This will get the rooms functional quickly, and tiles can be improved iteratively.
