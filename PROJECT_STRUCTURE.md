# Godot Project Structure Guide

## Overview
This document outlines the proper Godot project organization for team development. This structure separates concerns and makes it easy for multiple developers to work without conflicts.

## 📁 Root Directory Structure

```
game/
├── Scenes/           # All .tscn files organized by type
├── Scripts/          # All .cs and .gd files organized by feature
├── Assets/           # Final, integrated game assets
├── Resources/        # Godot resources (.tres files)
├── TeamFolders/      # Raw asset dumps from non-technical teams
├── addons/           # Godot plugins and extensions
├── docs/             # Project documentation
└── project.godot     # Project configuration
```

## 🎬 Scenes/ Organization

```
Scenes/
├── Characters/       # Character scenes
│   ├── Player.tscn
│   ├── NPC.tscn
│   └── Character.tscn (base scene)
│
├── Levels/          # Game levels/maps
│   ├── tokyo/
│   │   ├── tokyo_overworld.tscn
│   │   └── tokyo_outside.tscn
│   ├── osaka/
│   │   └── osaka_outside.tscn
│   └── Town.tscn
│
├── Objects/         # Interactive objects
│   ├── Door.tscn
│   ├── DrinkCan.tscn
│   └── vendingMachine.tscn
│
├── UI/              # User interface elements
│   ├── HUD.tscn
│   ├── InteractionScreen.tscn
│   └── SpeedBoostUI.tscn
│
├── Systems/         # System-level scenes
│   ├── Environment.tscn
│   ├── Props.tscn
│   └── World.tscn
│
└── Menus/           # Menu screens
    ├── menu.tscn (main menu)
    └── Main.tscn (game controller)
```

## 📝 Scripts/ Organization

```
Scripts/
├── Characters/      # Character behaviors
│   ├── Player.cs
│   ├── NPC.cs
│   ├── Character.cs
│   └── Character.gd
│
├── Systems/         # Core game systems
│   ├── Global.cs (singleton)
│   ├── GameController.cs
│   ├── DayNightController.cs
│   ├── EnvironmentController.cs
│   ├── NPCLocationManager.cs
│   ├── AudioManager.gd
│   └── WindController.gd
│
├── UI/              # UI controllers
│   ├── HUD.cs
│   ├── Menu.cs
│   ├── InteractionScreen.cs
│   ├── SpeedBoostUI.cs
│   └── TimeWeatherHUD.cs
│
├── Objects/         # Object behaviors
│   ├── Door.cs
│   ├── DrinkCan.cs
│   ├── VendingMachine.cs
│   └── PropsController.gd
│
├── Levels/          # Level-specific scripts
│   └── (level controllers)
│
└── Utils/           # Utility scripts
    └── (helper functions)
```

## 🎨 Assets/ Organization

```
Assets/
├── Audio/
│   ├── Music/       # Background music
│   ├── SFX/         # Sound effects
│   └── Voice/       # Voice lines
│
├── Sprites/
│   ├── Characters/  # Character sprites
│   │   └── 16x16/   # Current character sprites
│   ├── Environment/ # Tiles and backgrounds
│   │   ├── Tiles/
│   │   └── Tilemap/
│   ├── UI/          # UI elements
│   └── Items/       # Pickups and objects
│
└── Fonts/           # Text fonts
```

## 📦 Resources/ Organization

```
Resources/
├── Themes/          # UI themes (.tres)
├── Materials/       # Visual materials
├── Shaders/         # Custom shaders
└── (other .tres resource files)
```

## 👥 Team Development Guidelines

### For Engineers
- Work primarily in `Scripts/` and `Scenes/`
- Pull processed assets from `Assets/`
- Create prefabs in appropriate `Scenes/` subfolder

### For Level Designers
- Create levels in `Scenes/Levels/[area]/`
- Use existing prefabs from `Scenes/Objects/`
- Document level requirements in `TeamFolders/Design/`

### For Artists
- Dump raw assets in `TeamFolders/Art/`
- Engineers will process and move to `Assets/Sprites/`
- Follow naming conventions in team folder

### For Audio Team
- Dump raw audio in `TeamFolders/Audio/`
- Engineers will process and move to `Assets/Audio/`
- Provide loop points and metadata

## 🔄 Asset Pipeline

1. **Raw Assets** → `TeamFolders/[Team]/`
2. **Processing** → Engineers review and optimize
3. **Integration** → Move to `Assets/`
4. **Implementation** → Reference in `Scenes/` and `Scripts/`

## 📋 Naming Conventions

### Scenes (.tscn)
- PascalCase: `PlayerCharacter.tscn`
- Prefabs: `Prefab_Enemy.tscn`
- Levels: `Level_Tokyo_Street.tscn`

### Scripts (.cs/.gd)
- Match scene name: `PlayerCharacter.cs`
- Systems: `SystemName.cs`
- Utilities: `UtilityName.cs`

### Assets
- Sprites: `sprite_name_variant.png`
- Audio: `audio_category_name.ogg`
- Lowercase with underscores

## ⚠️ Important Notes

1. **Scene Dependencies**
   - Keep scene references relative
   - Use `res://` paths
   - Avoid absolute paths

2. **Script Attachments**
   - Scripts go in matching `Scripts/` subfolder
   - One script per scene (generally)
   - Use composition over inheritance

3. **Version Control**
   - `.import` files should be committed
   - Large binary files go in TeamFolders first
   - Use Git LFS for large assets if needed

## 🚀 Getting Started

### Setting Up Your Workspace

1. **Choose your primary work area:**
   - Level Designer → `Scenes/Levels/`
   - Gameplay Programmer → `Scripts/Systems/`
   - UI Developer → `Scenes/UI/` and `Scripts/UI/`

2. **Follow the pattern:**
   - Scene in `Scenes/[category]/`
   - Script in `Scripts/[category]/`
   - Assets in `Assets/[type]/`

3. **Test locally:**
   ```bash
   godot project.godot
   ```

## 🎯 Best Practices

1. **Small, Focused Scenes**
   - One responsibility per scene
   - Compose complex objects from simple scenes
   - Use scene inheritance for variants

2. **Clear Separation**
   - Logic in scripts
   - Layout in scenes
   - Data in resources

3. **Consistent Organization**
   - Mirror structure between Scenes/ and Scripts/
   - Group related functionality
   - Keep dependencies minimal

This structure scales well from small teams to large projects and makes it easy to find and modify any part of the game.