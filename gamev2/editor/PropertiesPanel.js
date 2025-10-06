// PropertiesPanel - Handles properties panel UI
class PropertiesPanel {
    constructor(configManager, gridEditor, dialogueEditor, getCurrentRoom) {
        this.configManager = configManager;
        this.gridEditor = gridEditor;
        this.dialogueEditor = dialogueEditor;
        this.getCurrentRoom = getCurrentRoom;
        this.panel = document.getElementById('properties-content');
    }

    // Update properties panel based on selected item
    update() {
        const selected = this.gridEditor.getSelectedItem();

        if (!selected) {
            this.panel.innerHTML = '<p class="empty-state">Select an item to edit properties</p>';
            return;
        }

        let html = '';

        switch (selected.type) {
            case 'npc':
                html = this.buildNPCProperties(selected);
                break;
            case 'object':
                html = this.buildObjectProperties(selected);
                break;
            case 'transporter':
                html = this.buildTransporterProperties(selected);
                break;
            case 'player':
                html = this.buildPlayerProperties(selected);
                break;
        }

        this.panel.innerHTML = html;
        this.attachPropertyEventListeners(selected);
    }

    // Build NPC properties HTML
    buildNPCProperties(selected) {
        const npc = selected.data;
        const center = this.configManager.getCenterPosition();
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
                    <div style="display: flex; gap: 4px;">
                        <input type="text" class="form-control" id="prop-npc-sprite" value="${npc.sprite}" style="flex: 1;">
                        <button class="btn btn-secondary btn-small" id="configure-sprite" title="Configure sprite scaling, alignment, and animation">⚙️</button>
                    </div>
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

    // Build object properties HTML
    buildObjectProperties(selected) {
        const obj = selected.data;
        const center = this.configManager.getCenterPosition();
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

    // Build transporter properties HTML
    buildTransporterProperties(selected) {
        const trans = selected.data;
        const center = this.configManager.getCenterPosition();
        const gridX = trans.gridX !== null ? trans.gridX : center.x + trans.gridOffsetX;
        const gridY = trans.gridY !== null ? trans.gridY : center.y + trans.gridOffsetY;
        const targetX = trans.targetX !== null ? trans.targetX : center.x + trans.targetOffsetX;
        const targetY = trans.targetY !== null ? trans.targetY : center.y + trans.targetOffsetY;

        const rooms = this.configManager.getRooms();
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

    // Build player properties HTML
    buildPlayerProperties(selected) {
        const player = selected.data;
        const center = this.configManager.getCenterPosition();
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
                    <div style="display: flex; gap: 4px;">
                        <input type="text" class="form-control" id="prop-player-sprite" value="${player.sprite}" style="flex: 1;">
                        <button class="btn btn-secondary btn-small" id="configure-sprite" title="Configure sprite scaling, alignment, and animation">⚙️</button>
                    </div>
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

    // Attach event listeners to property inputs
    attachPropertyEventListeners(selected) {
        const center = this.configManager.getCenterPosition();
        const currentRoom = this.getCurrentRoom();

        // Delete button
        const deleteBtn = document.getElementById('delete-item');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.gridEditor.deleteSelected();
                this.update();
            });
        }

        // NPC properties
        if (selected.type === 'npc') {
            const nameInput = document.getElementById('prop-npc-name');
            const spriteInput = document.getElementById('prop-npc-sprite');
            const xInput = document.getElementById('prop-npc-x');
            const yInput = document.getElementById('prop-npc-y');
            const dialogueBtn = document.getElementById('edit-dialogue');
            const configureSpriteBtn = document.getElementById('configure-sprite');

            const updateNPC = () => {
                const updatedNPC = { ...selected.data };
                updatedNPC.name = nameInput.value;
                updatedNPC.sprite = spriteInput.value;
                const newX = parseInt(xInput.value);
                const newY = parseInt(yInput.value);
                updatedNPC.gridOffsetX = newX - center.x;
                updatedNPC.gridOffsetY = newY - center.y;
                this.configManager.updateNPC(currentRoom, selected.index, updatedNPC);
                this.gridEditor.refreshSelectedItemData();
            };

            nameInput.addEventListener('input', updateNPC);
            spriteInput.addEventListener('input', updateNPC);
            xInput.addEventListener('change', updateNPC);
            yInput.addEventListener('change', updateNPC);

            dialogueBtn.addEventListener('click', () => {
                this.dialogueEditor.show(selected.data.dialogue, (newDialogue) => {
                    const updatedNPC = { ...selected.data };
                    updatedNPC.dialogue = newDialogue;
                    this.configManager.updateNPC(currentRoom, selected.index, updatedNPC);
                    this.gridEditor.refreshSelectedItemData();
                });
            });

            configureSpriteBtn.addEventListener('click', () => {
                const spriteKey = spriteInput.value;
                if (spriteKey && window.spriteManager) {
                    window.spriteManager.createSpriteModal(spriteKey);
                } else {
                    alert('Please enter a sprite key first');
                }
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
                this.configManager.updateObject(currentRoom, selected.index, updatedObj);
                this.gridEditor.refreshSelectedItemData();
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

                this.configManager.updateTransporter(currentRoom, selected.index, updatedTrans);
                this.gridEditor.refreshSelectedItemData();
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
            const configureSpriteBtn = document.getElementById('configure-sprite');

            const updatePlayer = () => {
                this.configManager.updatePlayerSettings({
                    name: nameInput.value,
                    sprite: spriteInput.value,
                    startX: parseInt(xInput.value),
                    startY: parseInt(yInput.value)
                });
                this.gridEditor.refreshSelectedItemData();
            };

            nameInput.addEventListener('input', updatePlayer);
            spriteInput.addEventListener('input', updatePlayer);
            xInput.addEventListener('change', updatePlayer);
            yInput.addEventListener('change', updatePlayer);

            configureSpriteBtn.addEventListener('click', () => {
                const spriteKey = spriteInput.value;
                if (spriteKey && window.spriteManager) {
                    window.spriteManager.createSpriteModal(spriteKey);
                } else {
                    alert('Please enter a sprite key first');
                }
            });
        }
    }
}
