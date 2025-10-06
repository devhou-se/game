class ConfigManager {
    constructor() {
        this.config = this.getDefaultConfig();
        this.sprites = new Map();
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
        return JSON.stringify(this.config, null, 2);
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
        this.notifyListeners('sprite-added', { key, imageData });
    }

    getSprite(key) {
        return this.sprites.get(key);
    }

    getAllSprites() {
        return Array.from(this.sprites.entries()).map(([key, data]) => ({ key, data }));
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
