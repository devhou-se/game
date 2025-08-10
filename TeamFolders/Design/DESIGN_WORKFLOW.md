# Design Team Workflow

## Getting Started

1. **Your Workspace**: `TeamFolders/Design/`
2. **Tools**: Text editors, spreadsheets, Godot editor (for levels)

## Directory Structure

```
Design/
├── Levels/           # Level designs and layouts
├── GameDesign/       # Core gameplay documents
├── Narrative/        # Story, dialogue, characters
├── Balance/          # Stats, economy, progression
├── UI_UX/           # Interface flows and mockups
└── References/       # Inspiration and research
```

## File Types & Conventions

### Design Documents
- **Format**: Markdown (.md) or Plain Text (.txt)
- **Naming**: `[feature]_design.md`
- Example: `combat_system_design.md`

### Level Designs
- **Initial Design**: Markdown or image mockups
- **Implementation**: Coordinate with engineering for .tscn files
- **Naming**: `level_[area]_[number].md`

### Dialogue & Story
- **Format**: Plain text or CSV for bulk dialogue
- **Structure**:
  ```
  CHARACTER_NAME: Dialogue text here
  [EMOTION: happy/sad/angry]
  [ACTION: walks away]
  ```

### Balance Sheets
- **Format**: CSV or simple text tables
- **Include**: Item stats, enemy HP, damage values
- **Version**: Keep history of balance changes

## NPC Dialogue System

Current system expects CSV format:
```csv
npc_id,dialogue_type,text,emotion
bailey,greeting,"Hey there!",happy
bailey,collision_1,"Watch where you're going!",annoyed
```

## Level Design Process

1. **Concept Phase**
   - Sketch layout in any tool
   - Define objectives and flow
   - List required assets

2. **Documentation**
   - Create `level_[name]_design.md`
   - Include asset requirements
   - Specify NPC placements

3. **Handoff**
   - Share with art team for assets
   - Coordinate with engineering for implementation

## Integration Guidelines

- Design docs stay in Design/ folder
- Implementation happens in main Scenes/ folder
- Use clear headers and sections in documents
- Include visual references when possible

## Balancing Workflow

1. Create initial values in Balance/ folder
2. Test in-game (coordinate with engineering)
3. Document changes with reasoning
4. Keep old versions for rollback

## Communication

- Major design changes: Discuss in #design channel
- Asset requests: Tag @artists with specifics
- Implementation requests: Create clear tickets for engineering

## Templates

### Feature Design Template
```markdown
# [Feature Name]

## Overview
Brief description

## Player Experience
What the player sees/does

## Technical Requirements
- List systems involved
- Asset needs
- UI elements

## Balance Considerations
- Difficulty curve
- Resource costs
- Progression impact
```

## Tips

- Keep documents concise and scannable
- Use bullet points over paragraphs
- Include mockups/sketches even if rough
- Version your documents (v1, v2, etc.)
- Test your ideas with paper prototypes first