# Team Folders - Collaboration Guidelines

This directory structure is designed to minimize merge conflicts and make collaboration easier for teams with varying technical experience.

## 📁 Folder Structure

### Engineering/
**Owner**: Engineers & Tech Architects
- Core game logic and scripts
- System integrations and APIs  
- Performance optimizations
- Technical documentation

### Design/
**Owner**: Game Designers & Level Designers
- Level layouts and configurations
- Game balance spreadsheets
- Design documents
- Gameplay prototypes

### Art/
**Owner**: Artists & Animators
- Character sprites and animations
- Environment assets
- UI elements
- Visual effects
- **Note**: Raw `.pixaki` files go here, exported PNGs go to main Assets/

### Audio/
**Owner**: Music Producers & Sound Designers
- Music tracks
- Sound effects
- Ambient sounds
- Audio configuration files

### Architecture/
**Owner**: Tech Architects
- System design documents
- Architecture diagrams
- API specifications
- Integration guides

## 🔄 Workflow Guidelines

### For Non-Technical Team Members

1. **Work in Your Team Folder**
   - Always save your work in your designated team folder first
   - Use clear, descriptive filenames (e.g., `player_walk_animation_v2.png`)
   - Create subfolders for different features/areas

2. **Version Your Work**
   - Instead of overwriting files, save new versions with numbers
   - Example: `background_music_v1.mp3`, `background_music_v2.mp3`

3. **Communicate Changes**
   - Use the team chat to announce when you've added new assets
   - Include a brief description of what changed

### For Technical Team Members

1. **Integration Process**
   - Review team folders regularly for new assets
   - Move finalized assets to appropriate engine folders
   - Update references in code/scenes

2. **Maintain Import Files**
   - Keep `.import` files updated when moving assets
   - Test assets in-game before committing

## ⚠️ Important Rules

1. **Don't Edit Outside Your Folder** - Unless you're doing integration work
2. **Don't Delete Others' Work** - Archive old versions instead
3. **Communicate Before Major Changes** - Use team channels
4. **Test Before Pushing** - Especially for code changes

## 🎯 Quick Reference

| If you are...           | Work in...        | File Types                    |
|------------------------|-------------------|-------------------------------|
| Artist                 | Art/              | .png, .pixaki, .aseprite      |
| Musician               | Audio/            | .mp3, .ogg, .wav              |
| Designer               | Design/           | .txt, .md, .xlsx, .tscn       |
| Engineer               | Engineering/      | .cs, .gd, .tscn               |
| Tech Architect         | Architecture/     | .md, .drawio, .pdf            |

## 💡 Tips for Git Beginners

- **Pull before you start working**: `git pull`
- **Commit often with clear messages**: `git commit -m "Added new enemy sprite"`
- **Push your changes**: `git push`
- **If you see conflicts**: Ask for help in the team chat!

## 🆘 Need Help?

Contact the tech lead or post in the #help channel if you:
- See merge conflicts
- Can't find where to put files
- Need assets integrated into the game
- Have questions about the workflow