/**
 * RoomManager - Handles room loading, transitions, and room-specific content
 */
class RoomManager {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;
        this.rooms = {};
        this.currentRoom = null;
        this.isTransitioning = false;
        this.transporterSprites = [];
        this.transporterLabels = [];
        this.objectSprites = [];
        this.floorSprites = [];
    }

    /**
     * Initialize rooms from configuration
     * @param {Object} config - Game configuration object
     * @param {number} centerGridX - Center grid X coordinate
     * @param {number} centerGridY - Center grid Y coordinate
     * @param {number} maxGridX - Maximum grid X value
     * @param {number} maxGridY - Maximum grid Y value
     */
    initializeRooms(config, centerGridX, centerGridY, maxGridX, maxGridY) {
        for (let roomKey in config.rooms) {
            const roomConfig = config.rooms[roomKey];

            // Set up boundary polygon (default to world bounds if not specified)
            let boundary;
            if (roomConfig.boundary && roomConfig.boundary.length >= 3) {
                boundary = roomConfig.boundary;
            } else {
                // Default rectangular boundary matching world bounds
                boundary = [
                    [0, 0],
                    [maxGridX, 0],
                    [maxGridX, maxGridY],
                    [0, maxGridY]
                ];
            }

            this.rooms[roomKey] = {
                name: roomConfig.name,
                boundary: boundary,
                npcs: [],
                objects: roomConfig.objects.map(obj => ({
                    type: obj.type || 'box',
                    gridX: obj.gridX !== null ? obj.gridX : centerGridX + obj.gridOffsetX,
                    gridY: obj.gridY !== null ? obj.gridY : centerGridY + obj.gridOffsetY
                })),
                transporters: roomConfig.transporters.map(trans => ({
                    gridX: trans.gridX !== null ? trans.gridX : centerGridX + trans.gridOffsetX,
                    gridY: trans.gridY !== null ? trans.gridY : centerGridY + trans.gridOffsetY,
                    targetRoom: trans.targetRoom,
                    targetX: trans.targetX !== null ? trans.targetX : centerGridX + trans.targetOffsetX,
                    targetY: trans.targetY !== null ? trans.targetY : centerGridY + trans.targetOffsetY
                })),
                floor: roomConfig.floor || {},
                layers: roomConfig.layers || []
            };
        }
    }

    /**
     * Load transporters for the current room
     */
    loadTransporters() {
        // Clear existing transporter sprites and labels
        this.transporterSprites.forEach(sprite => sprite.destroy());
        this.transporterSprites = [];
        if (this.transporterLabels) {
            this.transporterLabels.forEach(label => label.destroy());
        }
        this.transporterLabels = [];

        // Create transporter sprites for current room
        const room = this.rooms[this.currentRoom];
        room.transporters.forEach(trans => {
            const pixelX = trans.gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const pixelY = trans.gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const sprite = this.scene.add.sprite(pixelX, pixelY, 'transporter');
            sprite.setDepth(0);
            this.transporterSprites.push(sprite);

            // Add label above transporter
            const label = this.scene.add.text(
                pixelX,
                pixelY - this.scene.GRID_SIZE / 2 - 5,
                `Goto ${trans.targetRoom}`,
                {
                    fontSize: '16px',
                    fill: '#00ff00',
                    fontFamily: 'PixelOperatorMonoBold',
                    backgroundColor: '#000000'
                }
            );
            label.setOrigin(0.5, 1);
            label.setDepth(10);
            label.setResolution(1);
            this.transporterLabels.push(label);
        });
    }

    /**
     * Load objects for the current room
     */
    loadObjects() {
        // Clear existing object sprites
        this.objectSprites.forEach(sprite => sprite.destroy());
        this.objectSprites = [];

        // Create object sprites for current room
        const room = this.rooms[this.currentRoom];
        if (room.objects) {
            room.objects.forEach(obj => {
                const pixelX = obj.gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
                const pixelY = obj.gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;

                // Get sprite key from object type
                const objType = this.scene.objectTypes[obj.type];
                const spriteKey = objType ? objType.sprite : 'object-tile';

                const sprite = this.scene.add.sprite(pixelX, pixelY, spriteKey);
                sprite.setDepth(0);
                this.objectSprites.push(sprite);

                // Store grid position and type on sprite for collision detection
                sprite.gridX = obj.gridX;
                sprite.gridY = obj.gridY;
                sprite.objectType = obj.type;
            });
        }
    }

    /**
     * Load floor tiles for the current room
     */
    loadFloorTiles() {
        // Clear existing floor sprites
        this.floorSprites.forEach(sprite => sprite.destroy());
        this.floorSprites = [];

        const room = this.rooms[this.currentRoom];

        // Support both old format (room.floor) and new format (room.layers)
        if (room.layers) {
            for (const layer of room.layers) {
                this.loadLayer(layer);
            }
        } else if (room.floor) {
            const legacyLayer = {
                name: "Floor",
                z: 0,
                collision: false,
                tiles: room.floor
            };
            this.loadLayer(legacyLayer);
        } else {
            console.warn(`Room ${this.currentRoom} has no floor or layers data`);
        }
    }

    /**
     * Load a single tilemap layer
     * @param {Object} layer - Layer configuration object
     */
    loadLayer(layer) {
        const tiles = layer.tiles || {};
        let skippedCount = 0;

        for (const [key, spriteKey] of Object.entries(tiles)) {
            const [gridX, gridY] = key.split(',').map(Number);
            const pixelX = gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const pixelY = gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;

            // Check if the sprite texture exists
            if (!this.scene.textures.exists(spriteKey)) {
                if (skippedCount === 0) {
                    console.warn(`Sprite not found in layer "${layer.name}": ${spriteKey}`);
                }
                skippedCount++;
                continue;
            }

            const sprite = this.scene.add.sprite(pixelX, pixelY, spriteKey);

            // Apply sprite configuration
            const spriteConfig = this.scene.getSpriteConfig(spriteKey);
            sprite.setOrigin(spriteConfig.anchorX, spriteConfig.anchorY);
            if (spriteConfig.scale !== 1) {
                sprite.setScale(spriteConfig.scale);
            }

            // Set depth based on layer z-index AND y-position.
            // maxRows must cover the world height so the per-row Y-sort offset
            // stays < the spacing between layers (otherwise layers bleed).
            const baseDepth = this.calculateLayerDepth(layer.z);
            const maxRows = (this.scene.WORLD_HEIGHT / this.scene.GRID_SIZE) || 30;
            const yOffset = (gridY / maxRows) * 99;
            const spriteDepth = baseDepth + yOffset;
            sprite.setDepth(spriteDepth);

            // Store collision info on sprite
            sprite.setData('layerCollision', layer.collision);
            sprite.setData('layerZ', layer.z);
            sprite.setData('gridX', gridX);
            sprite.setData('gridY', gridY);

            this.floorSprites.push(sprite);
        }
    }

    /**
     * Calculate Phaser depth from layer z-index
     * @param {number} layerZ - Layer z-index
     * @returns {number} Phaser depth value
     */
    calculateLayerDepth(layerZ) {
        if (layerZ < 2) {
            return (layerZ - 5) * 100;
        } else {
            return layerZ * 100;
        }
    }

    /**
     * Check if player is on a transporter
     * @param {Object} playerPos - Player grid position {x, y}
     * @returns {boolean} True if transporter was triggered
     */
    checkTransporter(playerPos) {
        const room = this.rooms[this.currentRoom];

        for (let trans of room.transporters) {
            if (trans.gridX === playerPos.x && trans.gridY === playerPos.y) {
                this.switchRoom(trans.targetRoom, trans.targetX, trans.targetY);
                return true;
            }
        }
        return false;
    }

    /**
     * Switch to a different room
     * @param {string} newRoom - Target room name
     * @param {number} targetX - Target grid X position
     * @param {number} targetY - Target grid Y position
     */
    switchRoom(newRoom, targetX, targetY) {
        // Block input during transition
        this.isTransitioning = true;

        // Fade to black
        this.scene.cameras.main.fadeOut(250, 0, 0, 0);

        this.scene.cameras.main.once('camerafadeoutcomplete', () => {
            // Hide current room NPCs and their labels
            const oldRoom = this.rooms[this.currentRoom];
            oldRoom.npcs.forEach(npc => {
                npc.sprite.setVisible(false);
                if (npc.nameLabel) npc.nameLabel.setVisible(false);
            });

            // Update current room
            this.currentRoom = newRoom;

            // Move player to target position
            this.scene.player.gridX = targetX;
            this.scene.player.gridY = targetY;
            const pixelX = targetX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const pixelY = targetY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            this.scene.player.sprite.setPosition(pixelX, pixelY);

            // Center camera on player
            this.scene.cameras.main.centerOn(pixelX, pixelY);

            // Show new room NPCs and their labels
            const room = this.rooms[this.currentRoom];
            room.npcs.forEach(npc => {
                npc.sprite.setVisible(true);
                if (npc.nameLabel) npc.nameLabel.setVisible(true);
            });

            // Load new room content
            this.loadTransporters();
            this.loadObjects();
            this.loadFloorTiles();

            // Update HUD
            this.scene.updateHUD();

            // Wait 0.25 seconds on black, then fade in
            this.scene.time.delayedCall(250, () => {
                this.scene.cameras.main.fadeIn(250, 0, 0, 0);

                // Re-enable input after fade-in completes
                this.scene.cameras.main.once('camerafadeincomplete', () => {
                    this.isTransitioning = false;
                });
            });
        });
    }

    /**
     * Point-in-polygon test using ray casting algorithm
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @param {Array} polygon - Array of [x, y] points
     * @returns {boolean} True if point is inside polygon
     */
    isPointInPolygon(x, y, polygon) {
        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const xi = polygon[i][0];
            const yi = polygon[i][1];
            const xj = polygon[j][0];
            const yj = polygon[j][1];

            const intersect = ((yi > y) !== (yj > y)) &&
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    /**
     * Check if position is within room boundary
     * @param {number} gridX - Grid X coordinate
     * @param {number} gridY - Grid Y coordinate
     * @returns {boolean} True if position is within boundary
     */
    checkBoundary(gridX, gridY) {
        const room = this.rooms[this.currentRoom];
        if (!room || !room.boundary) {
            return true;
        }

        return this.isPointInPolygon(gridX + 0.5, gridY + 0.5, room.boundary);
    }
}
