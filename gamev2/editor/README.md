# Game Editor

A visual editor for editing your Phaser grid game configuration.

## Features

- **Visual Grid Editor**: Click to place NPCs, objects, and transporters with actual game sprites
- **WYSIWYG Interface**: See exactly what your game will look like with real sprites and background
- **Room Management**: Create, delete, and switch between rooms
- **NPC Editor**: Add NPCs with custom names, sprites, and multi-line dialogue
- **Object Placement**: Add blocking objects to create obstacles
- **Transporter System**: Create portals between rooms with visual targeting
- **Sprite Management**: Upload and manage custom sprites
- **Config Import/Export**: Load existing configs and save your changes
- **Live Preview**: See changes in real-time with actual game graphics

## How to Use

### Opening the Editor

1. Start a local server in the project root:
   ```bash
   python3 -m http.server 8000
   ```

2. Navigate to: `http://localhost:8000/editor/`

The editor will automatically load your existing `config.json` from the parent directory.

### Interface Overview

#### Left Sidebar
- **Game Settings**: Edit global game properties (title, date, grid size, world dimensions)
- **Current Room**: Select room to edit, add new rooms, or delete rooms
- **Tool**: Choose what to place on the grid
  - **Select**: Click items to edit their properties
  - **Add NPC**: Click grid cells to place NPCs
  - **Add Object**: Click to place blocking obstacles
  - **Add Transporter**: Click to create room portals
  - **Set Player Start**: Click to set player spawn point
- **Properties**: Edit selected item properties

#### Center Canvas
- Visual representation showing the actual game background and sprites
- Click to place items or select them
- **Drag-and-drop**: Click and drag selected items to reposition them on the grid
- Shows exactly what the game will look like (WYSIWYG)
- **Mouse Controls**:
  - Left click: Place/select items
  - Click + drag: Move selected items
  - Shift + drag: Pan the view
  - Mouse wheel: Zoom in/out
- **Keyboard Shortcuts**:
  - Delete/Backspace: Remove selected item

#### Right Sidebar
- **Sprites**: View and upload sprite images
- Click "Upload Sprite" to add new sprite images

### Workflow

1. **Load Your Config**
   - Click "Load Config" to import an existing config.json
   - Or start with the default template

2. **Edit Rooms**
   - Select a room from the dropdown
   - Click "Add Room" to create new rooms
   - Use "Delete Room" to remove unwanted rooms

3. **Place Items**
   - Select a tool (NPC, Object, Transporter, Player Start)
   - Click on the grid to place items
   - Switch to "Select" tool to edit existing items

4. **Edit Properties**
   - Click an item with the Select tool
   - Edit properties in the left sidebar (changes apply instantly)
   - For NPCs: Click "Edit Dialogue" to add/edit conversation lines
   - For Transporters: Change target room and destination
   - Drag items on the grid to reposition them visually

5. **Save Your Work**
   - Click "Save Config" to download config.json
   - Replace the game's config.json with your new file

## Tips

- **Drag-and-Drop**: Select an item and drag it to quickly reposition it on the grid
- **Live Editing**: All property changes apply immediately - you'll see updates in real-time
- **Center-Relative Positioning**: Items use center-relative offsets by default, making it easy to keep layouts centered
- **Grid Coordinates**: Hover over the grid to see coordinates in the bottom info bar
- **Transporters**: Edit target room and position in the properties panel to create working portals
- **Dialogue**: NPCs can have multiple dialogue lines - click "Edit Dialogue" to manage them
- **Player Start**: Each room can be a player start location, but only one is active (set in config)
- **Visual Feedback**: Selected items show a white border, making it easy to see what you're editing

## Exporting Sprites

The editor can manage sprites, but you'll need to manually save uploaded sprites to your `assets/` folder for the game to load them.

## Troubleshooting

- **Config won't load**: Make sure you're running from a web server (not file://)
- **Sprites not showing**: Upload sprites through the editor or ensure they exist in `../assets/`
- **Can't place items**: Make sure you've selected a tool other than "Select"
- **Grid not visible**: Check that world dimensions are set correctly in Game Settings
