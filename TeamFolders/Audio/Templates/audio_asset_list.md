# Audio Asset List Template

## Music Tracks

### Completed
- [ ] Title Screen - `music_title.ogg`
- [ ] Main Menu - `music_menu.ogg`

### In Progress
- [ ] Tokyo Overworld (Day) - `music_tokyo_day.ogg`
  - Status: Composing
  - BPM: 120
  - Key: C Major
  - Loop point: 32 bars

### Needed
- [ ] Tokyo Overworld (Night)
- [ ] Shop Interior
- [ ] Boss Battle
- [ ] Victory Fanfare
- [ ] Game Over

## Sound Effects

### Player Actions
- [ ] Footstep (normal) - `sfx_footstep_normal.ogg`
- [ ] Footstep (grass) - `sfx_footstep_grass.ogg`
- [ ] Jump - `sfx_player_jump.ogg`
- [ ] Land - `sfx_player_land.ogg`
- [ ] Interact - `sfx_interact.ogg`

### UI Sounds
- [ ] Menu Open - `sfx_menu_open.ogg`
- [ ] Menu Close - `sfx_menu_close.ogg`
- [ ] Button Hover - `sfx_button_hover.ogg`
- [ ] Button Click - `sfx_button_click.ogg`
- [ ] Error/Invalid - `sfx_error.ogg`
- [ ] Success/Confirm - `sfx_confirm.ogg`

### Environment
- [ ] Door Open - `sfx_door_open.ogg`
- [ ] Door Close - `sfx_door_close.ogg`
- [ ] Wind (ambient) - `sfx_wind_loop.ogg`
- [ ] Birds (ambient) - `sfx_birds_loop.ogg`
- [ ] City (ambient) - `sfx_city_ambient.ogg`

### NPCs
- [ ] NPC Notice Player - `sfx_npc_notice.ogg`
- [ ] NPC Greeting - `sfx_npc_greeting.ogg`
- [ ] NPC Collision - `sfx_npc_bump.ogg`

## Voice Lines

### Character: [Character Name]
- [ ] Greeting variations (3)
- [ ] Quest dialogue
- [ ] Idle comments (5)
- [ ] Collision reactions (3)

## Implementation Notes

### Priority Levels
1. **Critical** - Game doesn't feel complete without
2. **Important** - Significantly improves experience  
3. **Nice to Have** - Polish and variety

### Current Priorities
1. Critical:
   - Player footsteps
   - UI confirmation sounds
   - Background music for main areas

2. Important:
   - Ambient sounds
   - NPC interaction sounds
   - Menu music

3. Nice to Have:
   - Multiple footstep variations
   - Weather sounds
   - Additional ambient layers

## Technical Requirements

### Music
- Format: OGG Vorbis
- Bitrate: 128-192 kbps
- Seamless looping required
- Provide loop points in filename or metadata

### SFX
- Format: OGG or WAV
- Length: < 5 seconds
- Normalized to -12 dB
- No silence at start/end

### Voice
- Format: OGG Vorbis
- Clear recording, no background noise
- Consistent volume across lines
- Light compression applied

## Version Tracking

| Asset | Version | Date | Notes |
|-------|---------|------|-------|
| music_title.ogg | v1 | 2024-01-15 | Initial version |
| music_title.ogg | v2 | 2024-01-16 | Extended intro |

## Communication Log

- 2024-01-15: Requested city ambient sounds from team
- 2024-01-16: Title music v2 uploaded, awaiting feedback
- 2024-01-17: Need clarification on boss battle intensity