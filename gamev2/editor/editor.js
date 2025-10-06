// Initialize core components
const configManager = new ConfigManager();
const canvas = document.getElementById('grid-canvas');
const gridEditor = new GridEditor(canvas, configManager);
const spriteManager = new SpriteManager(configManager);

// Expose sprite manager for UI
window.spriteManager = spriteManager;

// Initialize UI modules
const uiManager = new UIManager(configManager, () => currentRoom);
const dialogueEditor = new DialogueEditor();
const propertiesPanel = new PropertiesPanel(configManager, gridEditor, dialogueEditor, () => currentRoom);

// Connect selection callback
gridEditor.setSelectionCallback(() => {
    propertiesPanel.update();
});

let currentRoom = null;

// Load initial config or create default
async function initialize() {
    // Try to load the game's config.json
    try {
        const response = await fetch('../config.json');
        if (response.ok) {
            const config = await response.json();
            configManager.loadConfig(config);
        }
    } catch (e) {
        console.log('Using default config');
    }

    // Try to load sprites from assets folder
    await uiManager.loadDefaultSprites();

    uiManager.updateUI();
    const rooms = configManager.getRooms();
    if (rooms.length > 0) {
        switchRoom(rooms[0]);
    }
}

// Switch to a different room
function switchRoom(roomKey) {
    currentRoom = roomKey;
    gridEditor.setRoom(roomKey);
    propertiesPanel.update();
}

// Event listeners - Config management
document.getElementById('load-config').addEventListener('click', () => {
    document.getElementById('config-file-input').click();
});

document.getElementById('config-file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        if (configManager.importConfig(event.target.result)) {
            uiManager.updateUI();
            const rooms = configManager.getRooms();
            if (rooms.length > 0) {
                switchRoom(rooms[0]);
            }
            alert('Config loaded successfully!');
        } else {
            alert('Failed to load config. Please check the file format.');
        }
    };
    reader.readAsText(file);
});

document.getElementById('save-config').addEventListener('click', () => {
    const configJSON = configManager.exportConfig();
    const blob = new Blob([configJSON], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'config.json';
    a.click();
    URL.revokeObjectURL(url);
});

document.getElementById('export-sprites').addEventListener('click', () => {
    spriteManager.exportSprites();
});

// Event listeners - Room management
document.getElementById('room-select').addEventListener('change', (e) => {
    switchRoom(e.target.value);
});

document.getElementById('add-room').addEventListener('click', () => {
    document.getElementById('room-modal').style.display = 'flex';
});

document.getElementById('delete-room').addEventListener('click', () => {
    if (confirm(`Delete room "${currentRoom}"?`)) {
        if (configManager.deleteRoom(currentRoom)) {
            const rooms = configManager.getRooms();
            if (rooms.length > 0) {
                switchRoom(rooms[0]);
            }
            uiManager.updateUI();
        }
    }
});

document.getElementById('create-room').addEventListener('click', () => {
    const key = document.getElementById('new-room-key').value.trim();
    const name = document.getElementById('new-room-name').value.trim();

    if (!key || !name) {
        alert('Please enter both room key and name');
        return;
    }

    if (configManager.addRoom(key, name)) {
        document.getElementById('room-modal').style.display = 'none';
        document.getElementById('new-room-key').value = '';
        document.getElementById('new-room-name').value = '';
        uiManager.updateUI();
        switchRoom(key);
    } else {
        alert('Room with this key already exists');
    }
});

// Event listeners - Tool buttons
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        gridEditor.setTool(btn.dataset.tool);

        // Show/hide floor paint panel based on tool
        const floorPaintPanel = document.getElementById('floor-paint-panel');
        if (btn.dataset.tool === 'paint' || btn.dataset.tool === 'erase') {
            floorPaintPanel.style.display = 'block';
            updateFloorSpriteSelector();
        } else {
            floorPaintPanel.style.display = 'none';
        }
    });
});

// Event listeners - Game settings
document.getElementById('game-title').addEventListener('input', (e) => {
    configManager.updateGameSettings({ title: e.target.value });
});

document.getElementById('game-date').addEventListener('input', (e) => {
    configManager.updateGameSettings({ date: e.target.value });
});

document.getElementById('game-gridsize').addEventListener('change', (e) => {
    configManager.updateGameSettings({ gridSize: parseInt(e.target.value) });
    gridEditor.setupCanvas();
    gridEditor.render();
});

document.getElementById('game-width').addEventListener('change', (e) => {
    configManager.updateGameSettings({ worldWidth: parseInt(e.target.value) });
    gridEditor.setupCanvas();
    gridEditor.render();
});

document.getElementById('game-height').addEventListener('change', (e) => {
    configManager.updateGameSettings({ worldHeight: parseInt(e.target.value) });
    gridEditor.setupCanvas();
    gridEditor.render();
});

// Event listeners - Sprite upload
document.getElementById('upload-sprite').addEventListener('click', () => {
    document.getElementById('sprite-file').click();
});

document.getElementById('sprite-file').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        const key = prompt('Enter sprite key:', file.name.replace(/\.[^/.]+$/, ''));
        if (key) {
            configManager.addSprite(key, event.target.result);
            uiManager.updateSpriteList();
        }
    };
    reader.readAsDataURL(file);
});

// Event listeners - Modal close buttons
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.modal').style.display = 'none';
    });
});

// Config manager listeners
configManager.addEventListener((event, data) => {
    if (event.includes('added') || event.includes('updated') || event.includes('deleted') || event.includes('floor')) {
        gridEditor.render();
    }
    if (event === 'room-added' || event === 'room-deleted') {
        uiManager.updateRoomSelector();
    }
    if (event.includes('sprite')) {
        uiManager.updateSpriteList();
        // Refresh animation frames when sprite data changes
        gridEditor.renderEngine.refreshSpriteFrames();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (!e.target.matches('input, textarea')) {
            e.preventDefault();
            gridEditor.deleteSelected();
            propertiesPanel.update();
        }
    }
});

// Tab navigation
const spritesPage = new SpritesPage(configManager, gridEditor);
const charactersPage = new CharactersPage(configManager, gridEditor);
const objectTypesPage = new ObjectTypesPage(configManager, gridEditor);

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetView = btn.dataset.view;

        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update views
        document.querySelectorAll('.view-container').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(targetView).classList.add('active');

        // Initialize sprites page when switching to it
        if (targetView === 'sprites-view') {
            spritesPage.render();
        }

        // Initialize characters page when switching to it
        if (targetView === 'characters-view') {
            charactersPage.render();
        }

        // Initialize object types page when switching to it
        if (targetView === 'object-types-view') {
            objectTypesPage.render();
        }
    });
});

// Event listeners - Floor painting
function updateFloorSpriteSelector() {
    const select = document.getElementById('floor-tile-sprite');
    const sprites = configManager.getAllSpriteMetadata();

    select.innerHTML = '<option value="">-- Select Sprite --</option>';
    sprites.forEach(({ key }) => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = key;
        if (key === gridEditor.currentFloorSprite) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

document.getElementById('floor-tile-sprite')?.addEventListener('change', (e) => {
    const spriteKey = e.target.value;
    gridEditor.setFloorSprite(spriteKey);

    // Update preview
    const preview = document.getElementById('floor-tile-preview');
    if (spriteKey) {
        const spriteData = configManager.getSprite(spriteKey);
        const metadata = configManager.getSpriteMetadata(spriteKey);
        const frameData = spriteData || (metadata?.frames?.[0]);

        if (frameData) {
            preview.innerHTML = `<img src="${frameData}" style="max-width: 100%; max-height: 100%; image-rendering: pixelated;">`;
        } else {
            preview.innerHTML = '<span style="color: #666; font-size: 12px;">No sprite data</span>';
        }
    } else {
        preview.innerHTML = '<span style="color: #666; font-size: 12px;">No sprite selected</span>';
    }
});

document.getElementById('clear-floor')?.addEventListener('click', () => {
    if (confirm('Clear all floor tiles in this room?')) {
        configManager.clearFloorTiles(currentRoom);
        gridEditor.render();
    }
});

// Initialize on load
initialize();
