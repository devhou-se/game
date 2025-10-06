class ConfigManager {
    constructor() {
        this.config = this.getDefaultConfig();
        this.sprites = new Map();
        this.spriteMetadata = new Map(); // Store animation frames, scaling, alignment
        this.listeners = [];
    }

    getDefaultConfig() {
        return {
            game: {
                title: "game.devhou.se",
                date: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
                gridSize: 64,
                worldWidth: 960,
                worldHeight: 640,
                deadzoneCells: 4,
                moveDuration: 200,
                npcWanderInterval: 5000,
                npcWanderRadius: 2
            },
            player: {
                startRoom: "Room1",
                startX: null,
                startY: null,
                sprite: "tile",
                name: "Player"
            },
            rooms: {
                "Room1": {
                    name: "Room1",
                    npcs: [],
                    objects: [],
                    transporters: []
                }
            }
        };
    }

    loadConfig(configData) {
        try {
            this.config = JSON.parse(JSON.stringify(configData));

            // Load sprite metadata from config if it exists
            if (configData.spriteMetadata) {
                this.spriteMetadata.clear(); // Clear existing metadata

                for (const [key, metadata] of Object.entries(configData.spriteMetadata)) {
                    // Initialize sprite metadata with empty frames array
                    // The actual sprite image data needs to be loaded separately from assets/
                    this.spriteMetadata.set(key, {
                        frames: [], // Empty initially - will be populated when sprites are loaded
                        scale: metadata.scale || 1,
                        anchorX: metadata.anchorX !== undefined ? metadata.anchorX : 0.5,
                        anchorY: metadata.anchorY !== undefined ? metadata.anchorY : 0.5,
                        frameRate: metadata.frameRate || 10,
                        loop: metadata.loop !== undefined ? metadata.loop : true,
                        spriteSheet: metadata.spriteSheet || false,
                        frameWidth: metadata.frameWidth || null,
                        frameHeight: metadata.frameHeight || null,
                        startFrame: metadata.startFrame || 0,
                        endFrame: metadata.endFrame || null,
                        margin: metadata.margin || 0,
                        spacing: metadata.spacing || 0,
                        isDirectional: metadata.isDirectional || false,
                        directions: metadata.directions || {
                            up: null,
                            down: null,
                            left: null,
                            right: null
                        },
                        autoFlip: metadata.autoFlip || {
                            horizontal: false,
                            vertical: false
                        },
                        defaultDirection: metadata.defaultDirection || 'down'
                    });
                }
            }

            this.notifyListeners('config-loaded');
            return true;
        } catch (e) {
            console.error('Failed to load config:', e);
            return false;
        }
    }

    getConfig() {
        return this.config;
    }

    updateGameSettings(settings) {
        Object.assign(this.config.game, settings);
        this.notifyListeners('game-settings-updated');
    }

    updatePlayerSettings(settings) {
        Object.assign(this.config.player, settings);
        this.notifyListeners('player-settings-updated');
    }

    getRooms() {
        return Object.keys(this.config.rooms);
    }

    getRoom(roomKey) {
        return this.config.rooms[roomKey];
    }

    addRoom(roomKey, roomName) {
        if (this.config.rooms[roomKey]) {
            return false;
        }
        this.config.rooms[roomKey] = {
            name: roomName,
            npcs: [],
            objects: [],
            transporters: []
        };
        this.notifyListeners('room-added', roomKey);
        return true;
    }

    deleteRoom(roomKey) {
        if (Object.keys(this.config.rooms).length <= 1) {
            alert('Cannot delete the last room!');
            return false;
        }
        delete this.config.rooms[roomKey];

        // If this was the player start room, update it
        if (this.config.player.startRoom === roomKey) {
            this.config.player.startRoom = Object.keys(this.config.rooms)[0];
        }

        this.notifyListeners('room-deleted', roomKey);
        return true;
    }

    addNPC(roomKey, npc) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].npcs.push(npc);
        this.notifyListeners('npc-added', { roomKey, npc });
        return true;
    }

    updateNPC(roomKey, index, npc) {
        if (!this.config.rooms[roomKey] || !this.config.rooms[roomKey].npcs[index]) return false;
        this.config.rooms[roomKey].npcs[index] = npc;
        this.notifyListeners('npc-updated', { roomKey, index, npc });
        return true;
    }

    deleteNPC(roomKey, index) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].npcs.splice(index, 1);
        this.notifyListeners('npc-deleted', { roomKey, index });
        return true;
    }

    addObject(roomKey, obj) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].objects.push(obj);
        this.notifyListeners('object-added', { roomKey, obj });
        return true;
    }

    updateObject(roomKey, index, obj) {
        if (!this.config.rooms[roomKey] || !this.config.rooms[roomKey].objects[index]) return false;
        this.config.rooms[roomKey].objects[index] = obj;
        this.notifyListeners('object-updated', { roomKey, index, obj });
        return true;
    }

    deleteObject(roomKey, index) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].objects.splice(index, 1);
        this.notifyListeners('object-deleted', { roomKey, index });
        return true;
    }

    addTransporter(roomKey, trans) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].transporters.push(trans);
        this.notifyListeners('transporter-added', { roomKey, trans });
        return true;
    }

    updateTransporter(roomKey, index, trans) {
        if (!this.config.rooms[roomKey] || !this.config.rooms[roomKey].transporters[index]) return false;
        this.config.rooms[roomKey].transporters[index] = trans;
        this.notifyListeners('transporter-updated', { roomKey, index, trans });
        return true;
    }

    deleteTransporter(roomKey, index) {
        if (!this.config.rooms[roomKey]) return false;
        this.config.rooms[roomKey].transporters.splice(index, 1);
        this.notifyListeners('transporter-deleted', { roomKey, index });
        return true;
    }

    exportConfig() {
        // Create a copy of config with sprite metadata
        const configWithMetadata = {
            ...this.config,
            spriteMetadata: {}
        };

        // Add sprite metadata to export
        for (const [key, metadata] of this.spriteMetadata.entries()) {
            configWithMetadata.spriteMetadata[key] = {
                scale: metadata.scale,
                anchorX: metadata.anchorX,
                anchorY: metadata.anchorY,
                frameRate: metadata.frameRate,
                loop: metadata.loop,
                frameCount: metadata.frames.length, // Include frame count for game to load
                // Directional sprite metadata
                isDirectional: metadata.isDirectional,
                directions: metadata.directions,
                autoFlip: metadata.autoFlip,
                defaultDirection: metadata.defaultDirection
                // Note: frames (base64 data) are excluded from config export
                // They should be exported separately using exportSprites()
            };
        }

        return JSON.stringify(configWithMetadata, null, 2);
    }

    importConfig(jsonString) {
        try {
            const config = JSON.parse(jsonString);
            this.loadConfig(config);
            return true;
        } catch (e) {
            console.error('Failed to import config:', e);
            return false;
        }
    }

    addSprite(key, imageData) {
        this.sprites.set(key, imageData);
        // Initialize metadata if not exists, or add frame to existing metadata
        if (!this.spriteMetadata.has(key)) {
            this.spriteMetadata.set(key, {
                frames: [imageData], // Array of image data (for animations)
                scale: 1,
                anchorX: 0.5, // 0 = left, 0.5 = center, 1 = right
                anchorY: 0.5, // 0 = top, 0.5 = center, 1 = bottom
                frameRate: 10, // Frames per second for animations
                loop: true,
                spriteSheet: false, // Whether to use a sprite sheet (single PNG with multiple frames)
                frameWidth: null, // Width of each frame in sprite sheet
                frameHeight: null, // Height of each frame in sprite sheet
                startFrame: 0, // Starting frame index
                endFrame: null, // Ending frame index (null = all frames)
                margin: 0, // Margin around sprite sheet
                spacing: 0, // Spacing between frames in sprite sheet

                // Directional sprite support
                isDirectional: false, // Whether this sprite has directional variants
                directions: {
                    up: null,    // Sprite key for up direction
                    down: null,  // Sprite key for down direction
                    left: null,  // Sprite key for left direction
                    right: null  // Sprite key for right direction
                },
                autoFlip: {
                    horizontal: false, // Auto-flip left<->right
                    vertical: false    // Auto-flip up<->down
                },
                defaultDirection: 'down' // Default facing direction
            });
        } else {
            // Metadata exists (loaded from config), add frame to it
            const metadata = this.spriteMetadata.get(key);
            if (metadata.frames.length === 0) {
                // First frame being added
                metadata.frames = [imageData];
            }
        }
        this.notifyListeners('sprite-added', { key, imageData });
    }

    getSprite(key) {
        return this.sprites.get(key);
    }

    getAllSprites() {
        return Array.from(this.sprites.entries()).map(([key, data]) => ({ key, data }));
    }

    // Sprite metadata management
    getSpriteMetadata(key) {
        return this.spriteMetadata.get(key);
    }

    updateSpriteMetadata(key, metadata) {
        if (!this.spriteMetadata.has(key)) {
            console.error(`Sprite ${key} not found`);
            return false;
        }
        const existing = this.spriteMetadata.get(key);
        this.spriteMetadata.set(key, { ...existing, ...metadata });
        this.notifyListeners('sprite-metadata-updated', { key, metadata });
        return true;
    }

    addSpriteFrame(key, frameData) {
        if (!this.spriteMetadata.has(key)) {
            console.error(`Sprite ${key} not found`);
            return false;
        }
        const metadata = this.spriteMetadata.get(key);
        metadata.frames.push(frameData);
        this.notifyListeners('sprite-frame-added', { key, frameData });
        return true;
    }

    removeSpriteFrame(key, frameIndex) {
        if (!this.spriteMetadata.has(key)) {
            console.error(`Sprite ${key} not found`);
            return false;
        }
        const metadata = this.spriteMetadata.get(key);
        if (frameIndex < 0 || frameIndex >= metadata.frames.length) {
            return false;
        }
        metadata.frames.splice(frameIndex, 1);
        // Keep at least one frame
        if (metadata.frames.length === 0) {
            metadata.frames.push(this.sprites.get(key));
        }
        this.notifyListeners('sprite-frame-removed', { key, frameIndex });
        return true;
    }

    deleteSprite(key) {
        this.sprites.delete(key);
        this.spriteMetadata.delete(key);
        this.notifyListeners('sprite-deleted', { key });
        return true;
    }

    getAllSpriteMetadata() {
        return Array.from(this.spriteMetadata.entries()).map(([key, metadata]) => ({
            key,
            ...metadata,
            thumbnail: this.sprites.get(key)
        }));
    }

    // Export sprites as downloadable files
    exportSprites() {
        const sprites = [];
        for (const [key, metadata] of this.spriteMetadata.entries()) {
            sprites.push({
                key,
                frames: metadata.frames,
                scale: metadata.scale,
                anchorX: metadata.anchorX,
                anchorY: metadata.anchorY,
                frameRate: metadata.frameRate,
                loop: metadata.loop
            });
        }
        return sprites;
    }

    // Character management methods
    getAllCharacters() {
        const characters = [];

        // Add player as first character
        const player = this.config.player;
        if (player) {
            characters.push({
                id: 'player',
                isPlayer: true,
                roomKey: player.startRoom,
                name: player.name || 'Player',
                sprite: player.sprite,
                directionalSprites: player.directionalSprites || null,
                autoFlip: player.autoFlip || null,
                startX: player.startX,
                startY: player.startY
            });
        }

        // Add NPCs from rooms
        const rooms = this.getRooms();
        rooms.forEach(roomKey => {
            const room = this.getRoom(roomKey);
            room.npcs.forEach((npc, index) => {
                characters.push({
                    id: `${roomKey}_${index}`,
                    roomKey,
                    roomIndex: index,
                    ...npc
                });
            });
        });

        return characters;
    }

    getCharacter(roomKey, index) {
        if (!this.config.rooms[roomKey]) return null;
        return this.config.rooms[roomKey].npcs[index];
    }

    updateCharacterDirectionalSprites(roomKey, index, directionalSprites) {
        if (!this.config.rooms[roomKey] || !this.config.rooms[roomKey].npcs[index]) return false;

        const npc = this.config.rooms[roomKey].npcs[index];
        npc.directionalSprites = directionalSprites;

        this.notifyListeners('character-updated', { roomKey, index });
        return true;
    }

    // Player management methods
    getPlayer() {
        return this.config.player;
    }

    updatePlayer(playerData) {
        // Update player properties
        if (playerData.name !== undefined) this.config.player.name = playerData.name;
        if (playerData.sprite !== undefined) this.config.player.sprite = playerData.sprite;
        if (playerData.directionalSprites !== undefined) {
            this.config.player.directionalSprites = playerData.directionalSprites;
        }
        if (playerData.autoFlip !== undefined) {
            this.config.player.autoFlip = playerData.autoFlip;
        }
        if (playerData.startX !== undefined) this.config.player.startX = playerData.startX;
        if (playerData.startY !== undefined) this.config.player.startY = playerData.startY;
        if (playerData.startRoom !== undefined) this.config.player.startRoom = playerData.startRoom;

        this.notifyListeners('player-updated', {});
        return true;
    }

    addEventListener(listener) {
        this.listeners.push(listener);
    }

    removeEventListener(listener) {
        this.listeners = this.listeners.filter(l => l !== listener);
    }

    notifyListeners(event, data) {
        this.listeners.forEach(listener => listener(event, data));
    }

    getCenterPosition() {
        const gridCols = Math.floor(this.config.game.worldWidth / this.config.game.gridSize);
        const gridRows = Math.floor(this.config.game.worldHeight / this.config.game.gridSize);
        return {
            x: Math.floor(gridCols / 2),
            y: Math.floor(gridRows / 2)
        };
    }
}
