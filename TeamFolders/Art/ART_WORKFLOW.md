# Art Team Workflow

## Getting Started

1. **Your Workspace**: `TeamFolders/Art/`
2. **Final Assets Go To**: `Assets/` (handled by --engineering-- Damian)

## Directory Structure

```
Art/
├── Characters/        # Character sprites and animations
├── Environments/      # Backgrounds, tiles, props
├── UI/               # Buttons, menus, HUD elements
├── VFX/              # Visual effects and particles
├── Concepts/         # Concept art and sketches
└── WIP/              # Work in progress - not for integration
```

## Naming Conventions

### Characters
- `[character_name]_[action]_[direction].png`
- Example: `player_walk_left.png`, `npc_bailey_idle_front.png`

### Tiles/Environment
- `tile_[type]_[variant].png`
- Example: `tile_grass_01.png`, `tile_building_roof.png`

### UI Elements
- `ui_[element]_[state].png`
- Example: `ui_button_normal.png`, `ui_button_pressed.png`

## File Formats

- **Sprites**: PNG (transparent background)
- **Source Files**: Keep .pixaki/.aseprite files in subdirectories
- **Animations**: Sprite sheets or frame sequences

## Size Guidelines

- **Characters**: 16x16 or 32x32 pixels
- **Tiles**: 16x16 pixels (can be combined)
- **UI Elements**: Variable, but keep consistent padding

## Integration Process

1. Save your work in the appropriate Art/ subdirectory
2. Export PNG versions for game use
3. Notify in #art channel when assets are ready
4. Engineering team will move to Assets/ and configure

## Version Control

- Save iterations: `character_v1.png`, `character_v2.png`
- Keep source files (.pixaki) with exports
- Don't delete old versions - archive in WIP/ folder

## Tips

- Test your sprites at 1x, 2x, and 4x zoom
- Keep consistent color palettes
- Align to pixel grid for crisp rendering
- Use transparency, not white backgrounds