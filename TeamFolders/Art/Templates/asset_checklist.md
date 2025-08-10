# Asset Checklist

## Character Sprite Requirements

### Player Character
- [ ] Idle animations (4 directions)
  - [ ] Front
  - [ ] Back
  - [ ] Left
  - [ ] Right (can mirror left)
- [ ] Walk animations (4 directions)
  - [ ] Front (4-6 frames)
  - [ ] Back (4-6 frames)
  - [ ] Side (4-6 frames)
- [ ] Special animations
  - [ ] Jump
  - [ ] Interact/Talk
  - [ ] Item pickup

### NPC Template
- [ ] Idle sprite (minimum 1 direction)
- [ ] Walk cycle (optional, 4 frames)
- [ ] Talk animation (optional, 2 frames)
- [ ] Unique identifier/colors

## Environment Assets

### Tileset Requirements
- [ ] Ground tiles
  - [ ] Grass/dirt variations (at least 3)
  - [ ] Path/road tiles
  - [ ] Transition tiles (edges)
- [ ] Building tiles
  - [ ] Walls (straight and corners)
  - [ ] Roof tiles
  - [ ] Doors (closed and open states)
  - [ ] Windows
- [ ] Props
  - [ ] Trees/vegetation
  - [ ] Rocks/obstacles
  - [ ] Decorative elements

## UI Elements

### Essential UI
- [ ] Health/energy bars
- [ ] Dialogue box
  - [ ] Background
  - [ ] Character portrait frame
  - [ ] Continue indicator
- [ ] Menu buttons
  - [ ] Normal state
  - [ ] Hover state
  - [ ] Pressed state
- [ ] Inventory slots
- [ ] Map indicators

## Technical Specifications

### Sprite Guidelines
- Size: 16x16 or 32x32 pixels
- Format: PNG with transparency
- Palette: Consistent across assets
- Padding: 1px transparent border (prevents bleeding)

### Animation Guidelines
- Frame rate: 8-12 FPS for most animations
- Consistent timing across similar actions
- Clear key poses for readability

### Color Palette
- Maximum 32 colors per scene (retro style)
- Consistent lighting direction (top-left)
- Reserved colors:
  - Pure black (#000000) for outlines
  - Pure magenta (#FF00FF) for transparency (if needed)

## File Organization

```
Art/Characters/[character_name]/
├── idle/
│   ├── front.png
│   ├── back.png
│   └── side.png
├── walk/
│   ├── front_01-04.png
│   ├── back_01-04.png
│   └── side_01-04.png
└── source/
    └── character.pixaki
```

## Export Settings

From Pixaki/Aseprite:
1. Scale: 100% (no interpolation)
2. Color mode: RGBA
3. Transparency: Enabled
4. Trim: Disabled (maintain canvas size)

## Quality Checklist

Before marking as complete:
- [ ] Consistent pixel size (no mixed resolutions)
- [ ] Clean edges (no stray pixels)
- [ ] Proper transparency
- [ ] Follows color palette
- [ ] Animates smoothly
- [ ] Matches existing art style
- [ ] Tested at multiple zoom levels