# Engineering Team Workflow

## Overview

Engineering team handles code, integrations, and bringing together assets from all teams.

## Responsibilities

### Core Development
- Game logic (C# and GDScript)
- System integration
- Performance optimization
- Asset pipeline management

### Integration Tasks
- Moving assets from team folders to engine folders
- Configuring import settings
- Setting up scenes and prefabs
- Connecting design data to game systems

## Code Organization

```
Scripts/
├── Core/           # Game systems (singleton, save/load)
├── Player/         # Player controller and mechanics
├── NPCs/           # NPC behaviors and dialogue
├── UI/             # User interface controllers
├── Environment/    # World systems (day/night, weather)
└── Utils/          # Helper functions and utilities
```

## Language Guidelines

### C# (.cs files)
- Primary language for complex systems
- Used for: NPCs, Game Controller, Player logic
- Follow .NET naming conventions

### GDScript (.gd files)
- Used for simpler components
- Environmental effects, animations
- Quick prototyping

## Integration Workflow

### Asset Integration Process

1. **Check Team Folders Daily**
   ```bash
   git pull
   ls TeamFolders/*/
   ```

2. **Move Assets to Engine Folders**
   - Art → Assets/16x16/ or Assets/Tiles/
   - Audio → Create audio/ if needed
   - Keep source files in team folders

3. **Update Import Settings**
   - Configure texture filtering (pixel art = nearest)
   - Set audio bus routing
   - Update .import files

4. **Test in Engine**
   - Load in Godot editor
   - Verify rendering/playback
   - Check performance impact

### Design Implementation

1. Read design docs from Design/ folder
2. Create/modify scenes (.tscn files)
3. Implement mechanics in appropriate scripts
4. Connect to existing systems (Global.cs singleton)

## Code Standards

### File Headers
```csharp
// [Brief description]
// Team: Engineering
// Last Modified: [Date]
```

### Commit Messages
```
[Category]: Brief description

- Detailed change 1
- Detailed change 2
```

Categories: feat, fix, refactor, perf, docs

## Testing Checklist

Before pushing:
- [ ] Build succeeds
- [ ] Game runs without errors
- [ ] New features tested
- [ ] Assets display correctly
- [ ] No performance regression

## Common Tasks

### Adding New NPC
1. Get sprite from Art/Characters/
2. Create NPC scene instance
3. Configure dialogue in NPC.cs
4. Place in world scene

### Implementing New Level
1. Review Design/Levels/ documentation
2. Create new scene file
3. Import required tilesets
4. Set up collision layers
5. Add to scene transition system

### Audio Integration
1. Import from Audio/ folder
2. Create AudioStreamPlayer nodes
3. Configure bus routing
4. Trigger via code or animation

## Performance Guidelines

- Keep texture sizes appropriate
- Use object pooling for projectiles
- Optimize collision shapes
- Profile before optimizing
- Target 60 FPS for web build

## Debugging Tools

- Godot debugger
- Print statements (GD.Print)
- Remote debugging for web builds
- Performance monitors

## Git Workflow

```bash
# Start work
git pull origin master

# Make changes
git add .
git commit -m "feat: added new enemy type"

# Push changes
git push origin master
```

## Build & Deploy

### Local Testing
```bash
godot --path ./ 
```

### Web Export
```bash
godot --export "HTML5" ./public/index.html
```

### CI/CD
- Automatic on push to master
- Check GitHub Actions for status
- Deploys to Firebase Hosting

## Coordination

- Review team folders daily
- Communicate integration status
- Document any asset issues
- Help non-technical team members with Git