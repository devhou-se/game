// Initialize
const configManager = new ConfigManager();
const canvas = document.getElementById('grid-canvas');
const gridEditor = new GridEditor(canvas, configManager);

// Connect selection callback
gridEditor.setSelectionCallback(() => {
    updatePropertiesPanel();
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
    loadDefaultSprites();

    updateUI();
    const rooms = configManager.getRooms();
    if (rooms.length > 0) {
        switchRoom(rooms[0]);
    }
}

async function loadDefaultSprites() {
    const defaultSprites = [
        { key: 'tile', path: '../assets/single-tile.png' },
        { key: 'npc-tile', path: '../assets/npc-tile.png' },
        { key: 'object-tile', path: '../assets/object-tile.png' },
        { key: 'transporter', path: '../assets/transporter.png' }
    ];

    for (const sprite of defaultSprites) {
        try {
            const response = await fetch(sprite.path);
            if (response.ok) {
                const blob = await response.blob();
                const reader = new FileReader();
                reader.onload = (e) => {
                    configManager.addSprite(sprite.key, e.target.result);
                };
                reader.readAsDataURL(blob);
            }
        } catch (e) {
            console.log(`Could not load sprite: ${sprite.key}`);
        }
    }
}

// UI Updates
function updateUI() {
    const config = configManager.getConfig();

    // Update game settings
    document.getElementById('game-title').value = config.game.title;
    document.getElementById('game-date').value = config.game.date;
    document.getElementById('game-gridsize').value = config.game.gridSize;
    document.getElementById('game-width').value = config.game.worldWidth;
    document.getElementById('game-height').value = config.game.worldHeight;

    // Update room selector
    updateRoomSelector();

    // Update sprite list
    updateSpriteList();
}

function updateRoomSelector() {
    const select = document.getElementById('room-select');
    const rooms = configManager.getRooms();

    select.innerHTML = '';
    rooms.forEach(roomKey => {
        const option = document.createElement('option');
        option.value = roomKey;
        option.textContent = roomKey;
        if (roomKey === currentRoom) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function updateSpriteList() {
    const container = document.getElementById('sprite-list');
    const sprites = configManager.getAllSprites();

    container.innerHTML = '';
    sprites.forEach(({ key, data }) => {
        const item = document.createElement('div');
        item.className = 'sprite-item';
        item.innerHTML = `
            <div class="sprite-preview">
                <img src="${data}" alt="${key}">
            </div>
            <div class="sprite-info">
                <div class="sprite-name">${key}</div>
                <div class="sprite-key">Key: ${key}</div>
            </div>
        `;
        container.appendChild(item);
    });
}

function switchRoom(roomKey) {
    currentRoom = roomKey;
    gridEditor.setRoom(roomKey);
    updatePropertiesPanel();
}

function updatePropertiesPanel() {
    const panel = document.getElementById('properties-content');
    const selected = gridEditor.getSelectedItem();

    if (!selected) {
        panel.innerHTML = '<p class="empty-state">Select an item to edit properties</p>';
        return;
    }

    let html = '';

    switch (selected.type) {
        case 'npc':
            html = buildNPCProperties(selected);
            break;
        case 'object':
            html = buildObjectProperties(selected);
            break;
        case 'transporter':
            html = buildTransporterProperties(selected);
            break;
        case 'player':
            html = buildPlayerProperties(selected);
            break;
    }

    panel.innerHTML = html;
    attachPropertyEventListeners(selected);
}

function buildNPCProperties(selected) {
    const npc = selected.data;
    const center = configManager.getCenterPosition();
    const gridX = npc.gridX !== null ? npc.gridX : center.x + npc.gridOffsetX;
    const gridY = npc.gridY !== null ? npc.gridY : center.y + npc.gridOffsetY;

    return `
        <div class="property-group">
            <div class="property-label">NPC</div>
            <div class="form-group">
                <label>Name:</label>
                <input type="text" class="form-control" id="prop-npc-name" value="${npc.name}">
            </div>
            <div class="form-group">
                <label>Sprite:</label>
                <input type="text" class="form-control" id="prop-npc-sprite" value="${npc.sprite}">
            </div>
            <div class="form-group">
                <label>Position:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="number" class="form-control" id="prop-npc-x" value="${gridX}" style="width: 50%;" placeholder="X">
                    <input type="number" class="form-control" id="prop-npc-y" value="${gridY}" style="width: 50%;" placeholder="Y">
                </div>
            </div>
            <button class="btn btn-primary" id="edit-dialogue" style="width: 100%; margin-top: 8px;">
                Edit Dialogue (${npc.dialogue.length} lines)
            </button>
        </div>
        <button class="btn btn-danger" id="delete-item" style="width: 100%;">Delete NPC</button>
    `;
}

function buildObjectProperties(selected) {
    const obj = selected.data;
    const center = configManager.getCenterPosition();
    const gridX = obj.gridX !== null ? obj.gridX : center.x + obj.gridOffsetX;
    const gridY = obj.gridY !== null ? obj.gridY : center.y + obj.gridOffsetY;

    return `
        <div class="property-group">
            <div class="property-label">Object</div>
            <div class="form-group">
                <label>Position:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="number" class="form-control" id="prop-obj-x" value="${gridX}" style="width: 50%;" placeholder="X">
                    <input type="number" class="form-control" id="prop-obj-y" value="${gridY}" style="width: 50%;" placeholder="Y">
                </div>
            </div>
        </div>
        <button class="btn btn-danger" id="delete-item" style="width: 100%;">Delete Object</button>
    `;
}

function buildTransporterProperties(selected) {
    const trans = selected.data;
    const center = configManager.getCenterPosition();
    const gridX = trans.gridX !== null ? trans.gridX : center.x + trans.gridOffsetX;
    const gridY = trans.gridY !== null ? trans.gridY : center.y + trans.gridOffsetY;
    const targetX = trans.targetX !== null ? trans.targetX : center.x + trans.targetOffsetX;
    const targetY = trans.targetY !== null ? trans.targetY : center.y + trans.targetOffsetY;

    const rooms = configManager.getRooms();
    const roomOptions = rooms.map(r =>
        `<option value="${r}" ${r === trans.targetRoom ? 'selected' : ''}>${r}</option>`
    ).join('');

    return `
        <div class="property-group">
            <div class="property-label">Transporter</div>
            <div class="form-group">
                <label>Position:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="number" class="form-control" id="prop-trans-x" value="${gridX}" style="width: 50%;" placeholder="X">
                    <input type="number" class="form-control" id="prop-trans-y" value="${gridY}" style="width: 50%;" placeholder="Y">
                </div>
            </div>
            <div class="form-group">
                <label>Target Room:</label>
                <select class="form-control" id="prop-trans-room">${roomOptions}</select>
            </div>
            <div class="form-group">
                <label>Target Position:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="number" class="form-control" id="prop-trans-targetx" value="${targetX}" style="width: 50%;" placeholder="X">
                    <input type="number" class="form-control" id="prop-trans-targety" value="${targetY}" style="width: 50%;" placeholder="Y">
                </div>
            </div>
        </div>
        <button class="btn btn-danger" id="delete-item" style="width: 100%;">Delete Transporter</button>
    `;
}

function buildPlayerProperties(selected) {
    const player = selected.data;
    const center = configManager.getCenterPosition();
    const gridX = player.startX !== null ? player.startX : center.x;
    const gridY = player.startY !== null ? player.startY : center.y;

    return `
        <div class="property-group">
            <div class="property-label">Player Start</div>
            <div class="form-group">
                <label>Name:</label>
                <input type="text" class="form-control" id="prop-player-name" value="${player.name}">
            </div>
            <div class="form-group">
                <label>Sprite:</label>
                <input type="text" class="form-control" id="prop-player-sprite" value="${player.sprite}">
            </div>
            <div class="form-group">
                <label>Start Position:</label>
                <div style="display: flex; gap: 8px;">
                    <input type="number" class="form-control" id="prop-player-x" value="${gridX}" style="width: 50%;" placeholder="X">
                    <input type="number" class="form-control" id="prop-player-y" value="${gridY}" style="width: 50%;" placeholder="Y">
                </div>
            </div>
        </div>
    `;
}

function attachPropertyEventListeners(selected) {
    const center = configManager.getCenterPosition();

    // Delete button
    const deleteBtn = document.getElementById('delete-item');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            gridEditor.deleteSelected();
            updatePropertiesPanel();
        });
    }

    // NPC properties
    if (selected.type === 'npc') {
        const nameInput = document.getElementById('prop-npc-name');
        const spriteInput = document.getElementById('prop-npc-sprite');
        const xInput = document.getElementById('prop-npc-x');
        const yInput = document.getElementById('prop-npc-y');
        const dialogueBtn = document.getElementById('edit-dialogue');

        const updateNPC = () => {
            const updatedNPC = { ...selected.data };
            updatedNPC.name = nameInput.value;
            updatedNPC.sprite = spriteInput.value;
            const newX = parseInt(xInput.value);
            const newY = parseInt(yInput.value);
            updatedNPC.gridOffsetX = newX - center.x;
            updatedNPC.gridOffsetY = newY - center.y;
            configManager.updateNPC(currentRoom, selected.index, updatedNPC);
            gridEditor.refreshSelectedItemData();
        };

        nameInput.addEventListener('input', updateNPC);
        spriteInput.addEventListener('input', updateNPC);
        xInput.addEventListener('change', updateNPC);
        yInput.addEventListener('change', updateNPC);

        dialogueBtn.addEventListener('click', () => {
            showDialogueEditor(selected.data.dialogue, (newDialogue) => {
                const updatedNPC = { ...selected.data };
                updatedNPC.dialogue = newDialogue;
                configManager.updateNPC(currentRoom, selected.index, updatedNPC);
                gridEditor.refreshSelectedItemData();
            });
        });
    }

    // Object properties
    if (selected.type === 'object') {
        const xInput = document.getElementById('prop-obj-x');
        const yInput = document.getElementById('prop-obj-y');

        const updateObject = () => {
            const updatedObj = { ...selected.data };
            const newX = parseInt(xInput.value);
            const newY = parseInt(yInput.value);
            updatedObj.gridOffsetX = newX - center.x;
            updatedObj.gridOffsetY = newY - center.y;
            configManager.updateObject(currentRoom, selected.index, updatedObj);
            gridEditor.refreshSelectedItemData();
        };

        xInput.addEventListener('change', updateObject);
        yInput.addEventListener('change', updateObject);
    }

    // Transporter properties
    if (selected.type === 'transporter') {
        const xInput = document.getElementById('prop-trans-x');
        const yInput = document.getElementById('prop-trans-y');
        const roomSelect = document.getElementById('prop-trans-room');
        const targetXInput = document.getElementById('prop-trans-targetx');
        const targetYInput = document.getElementById('prop-trans-targety');

        const updateTransporter = () => {
            const updatedTrans = { ...selected.data };
            const newX = parseInt(xInput.value);
            const newY = parseInt(yInput.value);
            const targetX = parseInt(targetXInput.value);
            const targetY = parseInt(targetYInput.value);

            updatedTrans.gridOffsetX = newX - center.x;
            updatedTrans.gridOffsetY = newY - center.y;
            updatedTrans.targetRoom = roomSelect.value;
            updatedTrans.targetOffsetX = targetX - center.x;
            updatedTrans.targetOffsetY = targetY - center.y;

            configManager.updateTransporter(currentRoom, selected.index, updatedTrans);
            gridEditor.refreshSelectedItemData();
        };

        xInput.addEventListener('change', updateTransporter);
        yInput.addEventListener('change', updateTransporter);
        roomSelect.addEventListener('change', updateTransporter);
        targetXInput.addEventListener('change', updateTransporter);
        targetYInput.addEventListener('change', updateTransporter);
    }

    // Player properties
    if (selected.type === 'player') {
        const nameInput = document.getElementById('prop-player-name');
        const spriteInput = document.getElementById('prop-player-sprite');
        const xInput = document.getElementById('prop-player-x');
        const yInput = document.getElementById('prop-player-y');

        const updatePlayer = () => {
            configManager.updatePlayerSettings({
                name: nameInput.value,
                sprite: spriteInput.value,
                startX: parseInt(xInput.value),
                startY: parseInt(yInput.value)
            });
            gridEditor.refreshSelectedItemData();
        };

        nameInput.addEventListener('input', updatePlayer);
        spriteInput.addEventListener('input', updatePlayer);
        xInput.addEventListener('change', updatePlayer);
        yInput.addEventListener('change', updatePlayer);
    }
}

// Dialogue editor
function showDialogueEditor(dialogue, onSave) {
    const modal = document.getElementById('dialogue-modal');
    const container = document.getElementById('dialogue-lines');
    const addBtn = document.getElementById('add-dialogue-line');
    const saveBtn = document.getElementById('save-dialogue');

    container.innerHTML = '';
    dialogue.forEach((line, index) => {
        addDialogueLine(container, line, index);
    });

    addBtn.onclick = () => {
        addDialogueLine(container, '', dialogue.length);
    };

    saveBtn.onclick = () => {
        const lines = Array.from(container.querySelectorAll('input'))
            .map(input => input.value)
            .filter(line => line.trim() !== '');
        onSave(lines);
        modal.style.display = 'none';
    };

    modal.style.display = 'flex';
}

function addDialogueLine(container, text, index) {
    const div = document.createElement('div');
    div.className = 'dialogue-line';
    div.innerHTML = `
        <input type="text" class="form-control" value="${text}" placeholder="Dialogue line ${index + 1}">
        <button type="button">×</button>
    `;
    div.querySelector('button').addEventListener('click', () => div.remove());
    container.appendChild(div);
}

// Event listeners
document.getElementById('load-config').addEventListener('click', () => {
    document.getElementById('config-file-input').click();
});

document.getElementById('config-file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        if (configManager.importConfig(event.target.result)) {
            updateUI();
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
            updateUI();
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
        updateUI();
        switchRoom(key);
    } else {
        alert('Room with this key already exists');
    }
});

// Tool buttons
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        gridEditor.setTool(btn.dataset.tool);
    });
});

// Game settings
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

// Sprite upload
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
            updateSpriteList();
        }
    };
    reader.readAsDataURL(file);
});

// Modal close buttons
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.modal').style.display = 'none';
    });
});

// Config manager listeners
configManager.addEventListener((event, data) => {
    if (event.includes('added') || event.includes('updated') || event.includes('deleted')) {
        gridEditor.render();
    }
    if (event === 'room-added' || event === 'room-deleted') {
        updateRoomSelector();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (!e.target.matches('input, textarea')) {
            e.preventDefault();
            gridEditor.deleteSelected();
            updatePropertiesPanel();
        }
    }
});

// Initialize on load
initialize();
