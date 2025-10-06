// GridEditor - Main coordinator for the visual grid editor
class GridEditor {
    constructor(canvas, configManager) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.configManager = configManager;
        this.currentRoom = null;
        this.currentTool = 'select';
        this.selectedItem = null;
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.isDraggingItem = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.dragStartGridX = 0;
        this.dragStartGridY = 0;

        // Callbacks
        this.onSelectionChanged = null;

        // Initialize sub-modules
        this.renderEngine = new RenderEngine(this);
        this.boundaryEditor = new BoundaryEditor(this);

        this.setupCanvas();
        this.renderEngine.loadSprites().then(() => {
            // Load animation frames after initial sprites are loaded
            this.renderEngine.refreshSpriteFrames();
            this.render();
        });
        this.setupEventListeners();
    }

    setupCanvas() {
        const config = this.configManager.getConfig();
        this.gridSize = config.game.gridSize;
        this.worldWidth = config.game.worldWidth;
        this.worldHeight = config.game.worldHeight;

        // Set canvas size with some padding
        this.canvas.width = this.worldWidth + 100;
        this.canvas.height = this.worldHeight + 100;

        this.offsetX = 50;
        this.offsetY = 50;

        // Disable image smoothing for pixel-perfect rendering
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.msImageSmoothingEnabled = false;
    }

    setupEventListeners() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
        this.canvas.addEventListener('contextmenu', (e) => this.handleContextMenu(e));
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    setTool(tool) {
        this.currentTool = tool;
        this.selectedItem = null;
        if (tool === 'boundary') {
            this.boundaryEditor.loadBoundary();
        } else {
            this.boundaryEditor.reset();
        }
        if (this.onSelectionChanged) {
            this.onSelectionChanged();
        }
        this.render();
    }

    setRoom(roomKey) {
        this.currentRoom = roomKey;
        this.selectedItem = null;
        if (this.currentTool === 'boundary') {
            this.boundaryEditor.loadBoundary();
        }
        if (this.onSelectionChanged) {
            this.onSelectionChanged();
        }
        this.render();
    }

    setSelectionCallback(callback) {
        this.onSelectionChanged = callback;
    }

    getGridPosition(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (clientX - rect.left - this.offsetX) / this.scale;
        const y = (clientY - rect.top - this.offsetY) / this.scale;
        const gridX = Math.floor(x / this.gridSize);
        const gridY = Math.floor(y / this.gridSize);
        return { gridX, gridY };
    }

    isValidGridPosition(gridX, gridY) {
        const maxGridX = Math.floor(this.worldWidth / this.gridSize) - 1;
        const maxGridY = Math.floor(this.worldHeight / this.gridSize) - 1;
        return gridX >= 0 && gridX <= maxGridX && gridY >= 0 && gridY <= maxGridY;
    }

    handleMouseDown(e) {
        if (e.button === 1 || e.shiftKey) {
            // Middle mouse or shift+click for panning
            this.isDragging = true;
            this.dragStartX = e.clientX - this.offsetX;
            this.dragStartY = e.clientY - this.offsetY;
            return;
        }

        if (this.currentTool === 'boundary') {
            if (this.boundaryEditor.handleMouseDown(e)) {
                this.render();
            }
            return;
        }

        const { gridX, gridY } = this.getGridPosition(e.clientX, e.clientY);

        if (!this.isValidGridPosition(gridX, gridY)) return;

        if (this.currentTool === 'select') {
            this.handleSelect(gridX, gridY);

            // If we selected an item, prepare for dragging
            if (this.selectedItem) {
                this.isDraggingItem = true;
                this.dragStartGridX = gridX;
                this.dragStartGridY = gridY;
            }
        } else {
            this.handlePlace(gridX, gridY);
        }
    }

    handleMouseMove(e) {
        if (this.isDragging) {
            this.offsetX = e.clientX - this.dragStartX;
            this.offsetY = e.clientY - this.dragStartY;
            this.render();
            return;
        }

        if (this.currentTool === 'boundary') {
            if (this.boundaryEditor.handleMouseMove(e)) {
                this.render();
            }
            return;
        }

        const { gridX, gridY } = this.getGridPosition(e.clientX, e.clientY);

        if (this.isDraggingItem && this.selectedItem) {
            // Only update if we've moved to a different grid cell
            if (gridX !== this.dragStartGridX || gridY !== this.dragStartGridY) {
                if (this.isValidGridPosition(gridX, gridY)) {
                    this.updateItemPosition(gridX, gridY);
                    this.dragStartGridX = gridX;
                    this.dragStartGridY = gridY;
                }
            }
        }

        // Update cursor info
        const cursorInfo = document.getElementById('cursor-info');
        if (this.isValidGridPosition(gridX, gridY)) {
            cursorInfo.textContent = `Position: ${gridX}, ${gridY}`;
        } else {
            cursorInfo.textContent = 'Position: -';
        }
    }

    handleMouseUp(e) {
        this.isDragging = false;
        this.isDraggingItem = false;
        if (this.currentTool === 'boundary') {
            this.boundaryEditor.handleMouseUp(e);
        }
    }

    handleContextMenu(e) {
        e.preventDefault();

        if (this.currentTool === 'boundary') {
            if (this.boundaryEditor.handleContextMenu(e)) {
                this.render();
            }
        }
    }

    handleKeyDown(e) {
        if (this.currentTool === 'boundary') {
            if (this.boundaryEditor.handleKeyDown(e)) {
                this.render();
            }
        }
    }

    handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.scale = Math.max(0.5, Math.min(2, this.scale * delta));

        const zoomInfo = document.getElementById('zoom-info');
        zoomInfo.textContent = `Zoom: ${Math.round(this.scale * 100)}%`;

        this.render();
    }

    handleSelect(gridX, gridY) {
        if (!this.currentRoom) return;

        const room = this.configManager.getRoom(this.currentRoom);
        const center = this.configManager.getCenterPosition();

        // Check NPCs
        for (let i = 0; i < room.npcs.length; i++) {
            const npc = room.npcs[i];
            const npcX = npc.gridX !== null ? npc.gridX : center.x + npc.gridOffsetX;
            const npcY = npc.gridY !== null ? npc.gridY : center.y + npc.gridOffsetY;
            if (npcX === gridX && npcY === gridY) {
                this.selectedItem = { type: 'npc', index: i, data: npc };
                this.render();
                if (this.onSelectionChanged) {
                    this.onSelectionChanged();
                }
                return;
            }
        }

        // Check objects
        for (let i = 0; i < room.objects.length; i++) {
            const obj = room.objects[i];
            const objX = obj.gridX !== null ? obj.gridX : center.x + obj.gridOffsetX;
            const objY = obj.gridY !== null ? obj.gridY : center.y + obj.gridOffsetY;
            if (objX === gridX && objY === gridY) {
                this.selectedItem = { type: 'object', index: i, data: obj };
                this.render();
                if (this.onSelectionChanged) {
                    this.onSelectionChanged();
                }
                return;
            }
        }

        // Check transporters
        for (let i = 0; i < room.transporters.length; i++) {
            const trans = room.transporters[i];
            const transX = trans.gridX !== null ? trans.gridX : center.x + trans.gridOffsetX;
            const transY = trans.gridY !== null ? trans.gridY : center.y + trans.gridOffsetY;
            if (transX === gridX && transY === gridY) {
                this.selectedItem = { type: 'transporter', index: i, data: trans };
                this.render();
                if (this.onSelectionChanged) {
                    this.onSelectionChanged();
                }
                return;
            }
        }

        // Check player start
        const config = this.configManager.getConfig();
        const playerX = config.player.startX !== null ? config.player.startX : center.x;
        const playerY = config.player.startY !== null ? config.player.startY : center.y;
        if (playerX === gridX && playerY === gridY && config.player.startRoom === this.currentRoom) {
            this.selectedItem = { type: 'player', data: config.player };
            this.render();
            if (this.onSelectionChanged) {
                this.onSelectionChanged();
            }
            return;
        }

        // Nothing selected
        this.selectedItem = null;
        this.render();
        if (this.onSelectionChanged) {
            this.onSelectionChanged();
        }
    }

    handlePlace(gridX, gridY) {
        if (!this.currentRoom) return;

        const center = this.configManager.getCenterPosition();

        switch (this.currentTool) {
            case 'npc':
                this.configManager.addNPC(this.currentRoom, {
                    gridX: null,
                    gridY: null,
                    gridOffsetX: gridX - center.x,
                    gridOffsetY: gridY - center.y,
                    sprite: "npc-tile",
                    name: "New NPC",
                    dialogue: []
                });
                break;

            case 'object':
                this.configManager.addObject(this.currentRoom, {
                    gridX: null,
                    gridY: null,
                    gridOffsetX: gridX - center.x,
                    gridOffsetY: gridY - center.y
                });
                break;

            case 'transporter':
                const rooms = this.configManager.getRooms();
                const targetRoom = rooms.find(r => r !== this.currentRoom) || rooms[0];
                this.configManager.addTransporter(this.currentRoom, {
                    gridX: null,
                    gridY: null,
                    gridOffsetX: gridX - center.x,
                    gridOffsetY: gridY - center.y,
                    targetRoom: targetRoom,
                    targetX: null,
                    targetY: null,
                    targetOffsetX: 0,
                    targetOffsetY: 0
                });
                break;

            case 'player':
                this.configManager.updatePlayerSettings({
                    startRoom: this.currentRoom,
                    startX: gridX,
                    startY: gridY
                });
                break;
        }

        this.render();
    }

    render() {
        this.renderEngine.render();
    }

    getSelectedItem() {
        return this.selectedItem;
    }

    deleteSelected() {
        if (!this.selectedItem || !this.currentRoom) return;

        const { type, index } = this.selectedItem;

        switch (type) {
            case 'npc':
                this.configManager.deleteNPC(this.currentRoom, index);
                break;
            case 'object':
                this.configManager.deleteObject(this.currentRoom, index);
                break;
            case 'transporter':
                this.configManager.deleteTransporter(this.currentRoom, index);
                break;
        }

        this.selectedItem = null;
        this.render();
    }

    updateItemPosition(gridX, gridY) {
        if (!this.selectedItem || !this.currentRoom) return;

        const center = this.configManager.getCenterPosition();
        const { type, index } = this.selectedItem;

        switch (type) {
            case 'npc':
                const updatedNPC = { ...this.selectedItem.data };
                updatedNPC.gridOffsetX = gridX - center.x;
                updatedNPC.gridOffsetY = gridY - center.y;
                this.configManager.updateNPC(this.currentRoom, index, updatedNPC);
                this.refreshSelectedItemData();
                break;

            case 'object':
                const updatedObj = { ...this.selectedItem.data };
                updatedObj.gridOffsetX = gridX - center.x;
                updatedObj.gridOffsetY = gridY - center.y;
                this.configManager.updateObject(this.currentRoom, index, updatedObj);
                this.refreshSelectedItemData();
                break;

            case 'transporter':
                const updatedTrans = { ...this.selectedItem.data };
                updatedTrans.gridOffsetX = gridX - center.x;
                updatedTrans.gridOffsetY = gridY - center.y;
                this.configManager.updateTransporter(this.currentRoom, index, updatedTrans);
                this.refreshSelectedItemData();
                break;

            case 'player':
                this.configManager.updatePlayerSettings({
                    startX: gridX,
                    startY: gridY
                });
                this.refreshSelectedItemData();
                break;
        }

        this.render();
    }

    refreshSelectedItemData() {
        if (!this.selectedItem || !this.currentRoom) return;

        const { type, index } = this.selectedItem;
        const room = this.configManager.getRoom(this.currentRoom);

        switch (type) {
            case 'npc':
                if (room.npcs[index]) {
                    this.selectedItem.data = room.npcs[index];
                }
                break;
            case 'object':
                if (room.objects[index]) {
                    this.selectedItem.data = room.objects[index];
                }
                break;
            case 'transporter':
                if (room.transporters[index]) {
                    this.selectedItem.data = room.transporters[index];
                }
                break;
            case 'player':
                this.selectedItem.data = this.configManager.getConfig().player;
                break;
        }

        // Don't call onSelectionChanged here - that should only fire when
        // a different item is selected, not when the current item's data is updated
        // Calling it here causes input fields to lose focus when editing properties
    }
}
