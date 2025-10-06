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

        // Sprite images
        this.sprites = {};
        this.spritesLoaded = false;

        // Callbacks
        this.onSelectionChanged = null;

        // Boundary editing
        this.boundaryVertices = [];
        this.selectedVertexIndex = null;
        this.hoveredVertexIndex = null;
        this.isDraggingVertex = false;

        this.setupCanvas();
        this.loadSprites().then(() => {
            this.spritesLoaded = true;
            this.render();
        });
        this.setupEventListeners();
    }

    async loadSprites() {
        const spriteFiles = {
            'background': '../assets/background-grid.png',
            'tile': '../assets/single-tile.png',
            'npc-tile': '../assets/npc-tile.png',
            'object-tile': '../assets/object-tile.png',
            'transporter': '../assets/transporter.png'
        };

        const loadImage = (src) => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = reject;
                img.src = src;
            });
        };

        try {
            for (const [key, src] of Object.entries(spriteFiles)) {
                this.sprites[key] = await loadImage(src);
            }
        } catch (e) {
            console.error('Failed to load sprites:', e);
        }
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
            this.loadBoundary();
        } else {
            this.boundaryVertices = [];
            this.selectedVertexIndex = null;
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
            this.loadBoundary();
        }
        if (this.onSelectionChanged) {
            this.onSelectionChanged();
        }
        this.render();
    }

    loadBoundary() {
        if (!this.currentRoom) {
            this.boundaryVertices = [];
            return;
        }

        const room = this.configManager.getRoom(this.currentRoom);
        if (room.boundary && Array.isArray(room.boundary)) {
            // Deep copy
            this.boundaryVertices = room.boundary.map(v => [v[0], v[1]]);
        } else {
            // Create default boundary
            const maxGridX = Math.floor(this.worldWidth / this.gridSize);
            const maxGridY = Math.floor(this.worldHeight / this.gridSize);
            this.boundaryVertices = [
                [0, 0],
                [maxGridX, 0],
                [maxGridX, maxGridY],
                [0, maxGridY]
            ];
        }
    }

    saveBoundary() {
        if (!this.currentRoom) return;

        const room = this.configManager.getRoom(this.currentRoom);
        room.boundary = this.boundaryVertices.map(v => [v[0], v[1]]);
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

    getBoundaryGridPosition(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (clientX - rect.left - this.offsetX) / this.scale;
        const y = (clientY - rect.top - this.offsetY) / this.scale;
        const gridX = Math.round(x / this.gridSize);
        const gridY = Math.round(y / this.gridSize);
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
            const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);

            // Check if clicking on a vertex
            const vertexRadius = 0.5; // In grid units
            for (let i = 0; i < this.boundaryVertices.length; i++) {
                const vertex = this.boundaryVertices[i];
                const dist = Math.sqrt(
                    Math.pow(gridX - vertex[0], 2) + Math.pow(gridY - vertex[1], 2)
                );
                if (dist < vertexRadius) {
                    this.selectedVertexIndex = i;
                    this.isDraggingVertex = true;
                    this.render();
                    return;
                }
            }

            // Otherwise add a new vertex
            this.boundaryVertices.push([gridX, gridY]);
            this.saveBoundary();
            this.render();
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

        if (this.isDraggingVertex && this.selectedVertexIndex !== null) {
            const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);
            this.boundaryVertices[this.selectedVertexIndex] = [gridX, gridY];
            this.saveBoundary();
            this.render();
            return;
        }

        // Check for vertex hover when in boundary mode
        if (this.currentTool === 'boundary' && !this.isDraggingVertex) {
            const { gridX, gridY } = this.getBoundaryGridPosition(e.clientX, e.clientY);
            const vertexRadius = 0.5;
            let foundHover = false;
            for (let i = 0; i < this.boundaryVertices.length; i++) {
                const vertex = this.boundaryVertices[i];
                const dist = Math.sqrt(
                    Math.pow(gridX - vertex[0], 2) + Math.pow(gridY - vertex[1], 2)
                );
                if (dist < vertexRadius) {
                    if (this.hoveredVertexIndex !== i) {
                        this.hoveredVertexIndex = i;
                        this.render();
                    }
                    foundHover = true;
                    break;
                }
            }
            if (!foundHover && this.hoveredVertexIndex !== null) {
                this.hoveredVertexIndex = null;
                this.render();
            }
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
        this.isDraggingVertex = false;
    }

    handleContextMenu(e) {
        e.preventDefault();

        if (this.currentTool === 'boundary' && this.hoveredVertexIndex !== null) {
            // Delete the hovered vertex (must have at least 3 vertices for a polygon)
            if (this.boundaryVertices.length > 3) {
                this.boundaryVertices.splice(this.hoveredVertexIndex, 1);
                this.hoveredVertexIndex = null;
                this.selectedVertexIndex = null;
                this.saveBoundary();
                this.render();
            }
        }
    }

    handleKeyDown(e) {
        if (this.currentTool === 'boundary') {
            // Delete key to remove selected or hovered vertex
            if ((e.key === 'Delete' || e.key === 'Backspace')) {
                const indexToDelete = this.selectedVertexIndex !== null ?
                    this.selectedVertexIndex : this.hoveredVertexIndex;

                if (indexToDelete !== null && this.boundaryVertices.length > 3) {
                    this.boundaryVertices.splice(indexToDelete, 1);
                    this.hoveredVertexIndex = null;
                    this.selectedVertexIndex = null;
                    this.saveBoundary();
                    this.render();
                }
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
        if (!this.spritesLoaded) return;

        const ctx = this.ctx;
        const config = this.configManager.getConfig();

        // Clear canvas
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        // Draw background
        this.drawBackground();

        if (this.currentRoom) {
            const room = this.configManager.getRoom(this.currentRoom);
            const center = this.configManager.getCenterPosition();

            // Draw objects
            room.objects.forEach((obj, index) => {
                const x = obj.gridX !== null ? obj.gridX : center.x + obj.gridOffsetX;
                const y = obj.gridY !== null ? obj.gridY : center.y + obj.gridOffsetY;
                const isSelected = this.selectedItem?.type === 'object' && this.selectedItem?.index === index;
                this.drawSprite(x, y, 'object-tile', isSelected);
            });

            // Draw transporters
            room.transporters.forEach((trans, index) => {
                const x = trans.gridX !== null ? trans.gridX : center.x + trans.gridOffsetX;
                const y = trans.gridY !== null ? trans.gridY : center.y + trans.gridOffsetY;
                const isSelected = this.selectedItem?.type === 'transporter' && this.selectedItem?.index === index;
                this.drawSprite(x, y, 'transporter', isSelected, `→ ${trans.targetRoom}`);
            });

            // Draw NPCs
            room.npcs.forEach((npc, index) => {
                const x = npc.gridX !== null ? npc.gridX : center.x + npc.gridOffsetX;
                const y = npc.gridY !== null ? npc.gridY : center.y + npc.gridOffsetY;
                const isSelected = this.selectedItem?.type === 'npc' && this.selectedItem?.index === index;
                const spriteKey = npc.sprite || 'npc-tile';
                this.drawSprite(x, y, spriteKey, isSelected, npc.name);
            });

            // Draw player start
            if (config.player.startRoom === this.currentRoom) {
                const x = config.player.startX !== null ? config.player.startX : center.x;
                const y = config.player.startY !== null ? config.player.startY : center.y;
                const isSelected = this.selectedItem?.type === 'player';
                const spriteKey = config.player.sprite || 'tile';
                this.drawSprite(x, y, spriteKey, isSelected, 'Player');
            }

            // Draw boundary if in boundary tool mode
            if (this.currentTool === 'boundary' && this.boundaryVertices.length > 0) {
                this.drawBoundary();
            }
        }

        ctx.restore();
    }

    drawBackground() {
        const ctx = this.ctx;

        // Draw the background grid image if loaded
        if (this.sprites['background']) {
            ctx.drawImage(this.sprites['background'], 0, 0, this.worldWidth, this.worldHeight);
        } else {
            // Fallback to black background if image not loaded
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, this.worldWidth, this.worldHeight);
        }

        // Draw border
        ctx.strokeStyle = '#444444';
        ctx.lineWidth = 2;
        ctx.strokeRect(0, 0, this.worldWidth, this.worldHeight);
    }

    drawSprite(gridX, gridY, spriteKey, isSelected, label = null) {
        const ctx = this.ctx;
        const x = gridX * this.gridSize + this.gridSize / 2;
        const y = gridY * this.gridSize + this.gridSize / 2;

        // Draw sprite if loaded, otherwise draw colored rectangle fallback
        const sprite = this.sprites[spriteKey];
        if (sprite) {
            // Center the sprite in the grid cell
            ctx.drawImage(
                sprite,
                x - this.gridSize / 2,
                y - this.gridSize / 2,
                this.gridSize,
                this.gridSize
            );
        } else {
            // Fallback: colored rectangle
            const fallbackColors = {
                'object-tile': '#333333',
                'transporter': '#00ff00',
                'npc-tile': '#ff69b4',
                'tile': '#ffff00'
            };
            ctx.fillStyle = fallbackColors[spriteKey] || '#ffffff';
            ctx.fillRect(x - this.gridSize / 2 + 2, y - this.gridSize / 2 + 2, this.gridSize - 4, this.gridSize - 4);
        }

        // Draw selection highlight
        if (isSelected) {
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3;
            ctx.strokeRect(x - this.gridSize / 2, y - this.gridSize / 2, this.gridSize, this.gridSize);
        }

        // Draw label
        if (label) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.fillRect(x - this.gridSize / 2, y - this.gridSize / 2 - 16, this.gridSize, 16);
            ctx.fillStyle = '#ffffff';
            ctx.font = '10px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, x, y - this.gridSize / 2 - 8);
        }
    }

    drawBoundary() {
        const ctx = this.ctx;

        if (this.boundaryVertices.length < 2) return;

        // Draw polygon lines
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.setLineDash([]);

        ctx.beginPath();
        const firstVertex = this.boundaryVertices[0];
        ctx.moveTo(firstVertex[0] * this.gridSize, firstVertex[1] * this.gridSize);

        for (let i = 1; i < this.boundaryVertices.length; i++) {
            const vertex = this.boundaryVertices[i];
            ctx.lineTo(vertex[0] * this.gridSize, vertex[1] * this.gridSize);
        }
        ctx.closePath();
        ctx.stroke();

        // Draw vertices
        for (let i = 0; i < this.boundaryVertices.length; i++) {
            const vertex = this.boundaryVertices[i];
            const x = vertex[0] * this.gridSize;
            const y = vertex[1] * this.gridSize;

            // Determine vertex color and size based on state
            let fillColor = '#00ff00'; // default green
            let radius = 6;
            let glowColor = null;

            if (i === this.selectedVertexIndex) {
                // Selected vertex - yellow with larger radius
                fillColor = '#ffff00';
                radius = 8;
            } else if (i === this.hoveredVertexIndex) {
                // Hovered vertex - cyan/light blue with glow
                fillColor = '#00ffff';
                radius = 7;
                glowColor = 'rgba(0, 255, 255, 0.5)';
            }

            // Draw glow for hovered vertex
            if (glowColor) {
                ctx.fillStyle = glowColor;
                ctx.beginPath();
                ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
                ctx.fill();
            }

            // Draw vertex circle
            ctx.fillStyle = fillColor;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            // Draw vertex number
            ctx.fillStyle = i === this.hoveredVertexIndex || i === this.selectedVertexIndex ? '#000000' : '#000000';
            ctx.font = 'bold 10px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(i.toString(), x, y);
        }
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
