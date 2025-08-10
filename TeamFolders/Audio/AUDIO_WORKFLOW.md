# Audio Team Workflow

## Getting Started

1. **Your Workspace**: `TeamFolders/Audio/`
2. **Formats**: OGG Vorbis preferred (MP3/WAV acceptable)

## Directory Structure

```
Audio/
├── Music/
│   ├── Menu/         # Title screen, menus
│   ├── Ambient/      # Background/area themes
│   ├── Combat/       # Battle music
│   └── Cutscenes/    # Story moments
├── SFX/
│   ├── Player/       # Footsteps, actions
│   ├── Environment/  # Doors, weather, ambient
│   ├── UI/          # Clicks, notifications
│   └── NPCs/        # Character voices, reactions
├── Voice/            # Voice acting files
└── WIP/             # Works in progress
```

## Naming Conventions

### Music
- `music_[location/mood]_[variant].ogg`
- Example: `music_tokyo_day.ogg`, `music_battle_boss.ogg`

### Sound Effects
- `sfx_[category]_[action]_[variant].ogg`
- Example: `sfx_player_jump_01.ogg`, `sfx_door_open.ogg`

### Voice Lines
- `voice_[character]_[emotion/context]_[number].ogg`
- Example: `voice_bailey_greeting_01.ogg`

## Technical Specifications

### Music
- **Format**: OGG Vorbis (preferred) or MP3
- **Bitrate**: 128-192 kbps
- **Looping**: Seamless loop points required
- **Length**: 1-3 minutes per track (will loop)

### Sound Effects
- **Format**: OGG or WAV
- **Sample Rate**: 44.1 kHz
- **Bit Depth**: 16-bit
- **Length**: Keep under 5 seconds
- **Volume**: Normalize to -12 dB

### Voice Acting
- **Format**: OGG Vorbis
- **Quality**: Clear, no background noise
- **Processing**: Light compression, de-essing

## Integration Notes

1. Place final audio in appropriate subdirectory
2. Include metadata file with:
   - BPM (for music)
   - Loop points
   - Intended use/location
3. Test volume levels against existing audio
4. Notify #audio channel when ready

## Godot Audio Guidelines

- Background music: -10 to -15 dB
- Sound effects: -5 to -10 dB  
- UI sounds: -15 to -20 dB
- Voice: -5 to -8 dB

## Version Control

- Keep project files (.flp, .als, .logic) in personal storage
- Only commit final exported audio
- Version as: `track_v1.ogg`, `track_v2.ogg`

## Tips

- Test audio at different volume levels
- Consider dynamic range for web playback
- Keep file sizes reasonable (< 5MB per track)
- Provide both looping and one-shot versions when applicable