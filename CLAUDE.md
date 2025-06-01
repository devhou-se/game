# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Godot 3.6 game project that runs at https://devhou.se. It's a 2D pixel art game with a unique blog-to-NPC integration system where blog posts are automatically converted into game NPCs with AI-generated personalities and voice synthesis.

## Technology Stack

- **Engine**: Godot 3.6 with Mono/C# support
- **Languages**: C# (.NET Framework 4.7.2) and GDScript
- **Build Target**: HTML5/Web (WASM export)
- **Deployment**: Firebase Hosting (project: devhouse-80936)
- **CI/CD**: GitHub Actions

## Common Development Commands

### Running the Game
```bash
# Open in Godot Editor
godot project.godot

# Or run directly
godot --main-pack project.godot
```

### Building for Web
```bash
# Export to HTML5 (requires configured export templates)
godot --export "HTML5" ./public/index.html
```

### Local Testing
The game runs on port configured by Godot editor. Main entry point is `res://Scenes/menu.tscn`.

## Architecture Overview

### Core Systems

1. **Scene Hierarchy**
   - `menu.tscn` - Main menu entry point
   - `Main.tscn` - Primary game scene controller
   - `tokyo_overworld.tscn` - Main game world
   - `Player.tscn` - Player character
   - `NPC.tscn` - Non-player characters
   - `Character.tscn` - Base character template

2. **Global State Management**
   - `Global.cs` - Singleton autoload managing game state
   - Handles scene transitions, game data, and shared resources

3. **Mixed Language Architecture**
   - C# scripts (`.cs`) for core game logic and systems
   - GDScript (`.gd`) for environmental effects and simpler components
   - Both languages interoperate through Godot's node system

4. **NPC System**
   - NPCs have dynamic dialogue with 180+ collision responses
   - Can check "Bailey Butler office status" via API
   - Blog integration creates NPCs from blog posts using:
     - OpenAI API for personality generation
     - ElevenLabs for voice synthesis
     - Google Cloud Storage for audio assets

### Key Script Responsibilities

- `GameController.cs` - Main game loop and state management
- `NPC.cs` - NPC behavior, interactions, and dialogue system
- `Character.cs/gd` - Base character movement and animations
- `Player.cs` - Player-specific controls and interactions
- `DayNightCycle.gd` - Environmental time system
- `WindController.gd` - Wind effects system

## Development Notes

- Window size is 1280x720 with 2D stretch mode
- Touch input is emulated from mouse events
- The project uses both C# and GDScript - ensure changes maintain compatibility
- Assets are organized by type: sprites in `/Assets/16x16/`, tiles in `/Assets/Tiles/`
- Scene files (`.tscn`) should be edited in Godot editor, not manually

## Git Workflow

When making commits:
- Commit directly to master branch
- Use force push when needed
- Do NOT include Claude attribution in commit messages
- Do NOT create pull requests
- Do NOT create feature branches

## CI/CD Pipeline

The project automatically builds and deploys on push to master branch:
1. Uses `barichello/godot-ci:mono-3.6` Docker image
2. Exports to HTML5 format
3. Deploys to Firebase Hosting

Manual deployment can be triggered via workflow dispatch in GitHub Actions.