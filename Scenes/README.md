# Scenes Directory Structure

This directory contains all Godot scene files (.tscn) organized by type.

## 📁 Folder Structure

### Characters/
All character-related scenes including player, NPCs, and base character templates.
- `Player.tscn` - Player character scene
- `NPC.tscn` - Base NPC template
- `Character.tscn` - Base character class

### Levels/
Game levels and maps organized by area.
- `tokyo/` - Tokyo area levels
- `osaka/` - Osaka area levels
- Each level should be self-contained with its own tilemap

### Objects/
Interactive objects and props that can be placed in levels.
- Doors, items, vending machines, etc.
- Should be instanced, not inherited

### UI/
User interface scenes.
- HUD elements
- Menus and dialogs
- Interaction screens

### Systems/
Core system scenes that manage game state.
- Environment controller
- Game manager
- World container

### Menus/
Menu screens separate from in-game UI.
- Main menu
- Settings menu
- Credits

## 🎯 Best Practices

1. **One Scene, One Purpose**
   - Each scene should have a single, clear responsibility
   - Compose complex objects from simple scenes

2. **Use Scene Inheritance**
   - Create base scenes for common functionality
   - Inherit for variations (e.g., different enemy types)

3. **Prefab Pattern**
   - Create reusable prefabs in Objects/
   - Instance them in levels, don't copy

4. **Relative References**
   - Always use `res://` paths
   - Never use absolute file paths

5. **Script Attachment**
   - Attach scripts from corresponding Scripts/ folder
   - Keep script names matching scene names

## 🔧 Common Tasks

### Creating a New Level
1. Create scene in `Levels/[area]/Level_Name.tscn`
2. Use existing tilesets from Assets/
3. Instance objects from Objects/ folder
4. Add to scene manager for transitions

### Adding a New NPC
1. Inherit from `Characters/NPC.tscn`
2. Override properties and sprites
3. Save as `Characters/NPC_[Name].tscn`

### Creating UI Elements
1. Create in `UI/` folder
2. Use Godot's Control nodes
3. Connect to UI scripts in Scripts/UI/