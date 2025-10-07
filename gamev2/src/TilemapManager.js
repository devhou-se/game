/**
 * TilemapManager - Handles multi-layer tilemap rendering and collision detection for v2
 *
 * Supports multiple layers:
 * - floor: Base ground tiles
 * - decoration: Decorative tiles (non-collidable)
 * - collision: Invisible collision layer
 * - overhead: Tiles that render above characters
 * - effects: Special effect tiles
 */
class TilemapManager {
    constructor(scene, gridSize) {
        this.scene = scene;
        this.gridSize = gridSize;

        // Store active tilemaps per room
        this.tilemaps = new Map();
        this.currentRoomTilemap = null;

        // Layer configuration
        this.layerConfig = {
            floor: { depth: -1, collidable: false },
            decoration: { depth: 0, collidable: false },
            collision: { depth: -2, collidable: true, visible: false },
            overhead: { depth: 100, collidable: false },
            effects: { depth: 50, collidable: false }
        };
    }

    /**
     * Load tilemap data for a room
     * @param {string} roomName - Name of the room
     * @param {object} tilemapData - Tilemap configuration
     * @returns {Phaser.Tilemaps.Tilemap|null}
     */
    loadTilemap(roomName, tilemapData) {
        // Clear existing tilemap for this room if it exists
        this.clearRoomTilemap(roomName);

        if (!tilemapData || !tilemapData.tilesetImage) {
            console.warn(`No tilemap data provided for room: ${roomName}`);
            return null;
        }

        try {
            // Create the tilemap from data
            const map = this.scene.make.tilemap({
                data: tilemapData.layers,
                tileWidth: this.gridSize,
                tileHeight: this.gridSize,
                width: tilemapData.width,
                height: tilemapData.height
            });

            // Add the tileset image
            const tileset = map.addTilesetImage(
                tilemapData.tilesetName,
                tilemapData.tilesetImage,
                this.gridSize,
                this.gridSize
            );

            if (!tileset) {
                console.error(`Failed to add tileset image for room: ${roomName}`);
                return null;
            }

            // Create layers from the tilemap data
            const layers = {};

            for (const [layerName, layerData] of Object.entries(tilemapData.layers)) {
                const config = this.layerConfig[layerName];
                if (!config) {
                    console.warn(`Unknown layer type: ${layerName}`);
                    continue;
                }

                // Create the layer
                const layer = map.createLayer(layerName, tileset, 0, 0);

                if (layer) {
                    // Set layer depth
                    layer.setDepth(config.depth);

                    // Set visibility
                    if (config.visible === false) {
                        layer.setVisible(false);
                    }

                    // Set collision if needed
                    if (config.collidable) {
                        // Set collision on all tiles in this layer
                        layer.setCollisionByExclusion([-1]);
                    }

                    layers[layerName] = layer;
                }
            }

            // Store the tilemap and layers
            const tilemapObj = {
                map,
                tileset,
                layers
            };

            this.tilemaps.set(roomName, tilemapObj);
            this.currentRoomTilemap = tilemapObj;

            return map;

        } catch (error) {
            console.error(`Error loading tilemap for room ${roomName}:`, error);
            return null;
        }
    }

    /**
     * Load tilemap from JSON file
     * @param {string} roomName - Name of the room
     * @param {string} jsonKey - Phaser cache key for the JSON data
     */
    loadTilemapFromJSON(roomName, jsonKey) {
        // Clear existing tilemap
        this.clearRoomTilemap(roomName);

        try {
            // Create tilemap from Tiled JSON
            const map = this.scene.make.tilemap({ key: jsonKey });

            // Get the first tileset (assuming single tileset per room)
            const tilesetData = map.tilesets[0];
            if (!tilesetData) {
                console.error(`No tileset found in JSON for room: ${roomName}`);
                return null;
            }

            // Add the tileset image
            const tileset = map.addTilesetImage(
                tilesetData.name,
                tilesetData.name // Assuming the image key matches the tileset name
            );

            if (!tileset) {
                console.error(`Failed to add tileset image for room: ${roomName}`);
                return null;
            }

            // Create all layers from the Tiled JSON
            const layers = {};

            for (let i = 0; i < map.layers.length; i++) {
                const layerData = map.layers[i];
                const layerName = layerData.name;
                const config = this.layerConfig[layerName] || { depth: i, collidable: false };

                // Create the layer
                const layer = map.createLayer(i, tileset, 0, 0);

                if (layer) {
                    // Set layer depth
                    layer.setDepth(config.depth);

                    // Set visibility
                    if (config.visible === false) {
                        layer.setVisible(false);
                    }

                    // Set collision if needed
                    if (config.collidable) {
                        layer.setCollisionByExclusion([-1]);
                    }

                    layers[layerName] = layer;
                }
            }

            // Store the tilemap
            const tilemapObj = {
                map,
                tileset,
                layers
            };

            this.tilemaps.set(roomName, tilemapObj);
            this.currentRoomTilemap = tilemapObj;

            return map;

        } catch (error) {
            console.error(`Error loading tilemap JSON for room ${roomName}:`, error);
            return null;
        }
    }

    /**
     * Check if a grid position has a collision tile
     * @param {number} gridX - Grid X coordinate
     * @param {number} gridY - Grid Y coordinate
     * @returns {boolean}
     */
    hasCollisionAt(gridX, gridY) {
        if (!this.currentRoomTilemap || !this.currentRoomTilemap.layers.collision) {
            return false;
        }

        const layer = this.currentRoomTilemap.layers.collision;
        const tile = layer.getTileAt(gridX, gridY);

        return tile !== null && tile.index !== -1;
    }

    /**
     * Get all collision tiles in the current room
     * @returns {Array<{x: number, y: number}>}
     */
    getCollisionTiles() {
        const collisions = [];

        if (!this.currentRoomTilemap || !this.currentRoomTilemap.layers.collision) {
            return collisions;
        }

        const layer = this.currentRoomTilemap.layers.collision;
        const map = this.currentRoomTilemap.map;

        for (let y = 0; y < map.height; y++) {
            for (let x = 0; x < map.width; x++) {
                const tile = layer.getTileAt(x, y);
                if (tile !== null && tile.index !== -1) {
                    collisions.push({ x, y });
                }
            }
        }

        return collisions;
    }

    /**
     * Clear tilemap for a specific room
     * @param {string} roomName - Name of the room
     */
    clearRoomTilemap(roomName) {
        const tilemapObj = this.tilemaps.get(roomName);

        if (tilemapObj) {
            // Destroy all layers
            Object.values(tilemapObj.layers).forEach(layer => {
                if (layer) {
                    layer.destroy();
                }
            });

            // Destroy the map
            if (tilemapObj.map) {
                tilemapObj.map.destroy();
            }

            this.tilemaps.delete(roomName);

            if (this.currentRoomTilemap === tilemapObj) {
                this.currentRoomTilemap = null;
            }
        }
    }

    /**
     * Switch to a different room's tilemap
     * @param {string} roomName - Name of the room to switch to
     */
    switchToRoom(roomName) {
        const tilemapObj = this.tilemaps.get(roomName);

        if (tilemapObj) {
            // Hide current room's tilemap
            if (this.currentRoomTilemap) {
                Object.values(this.currentRoomTilemap.layers).forEach(layer => {
                    if (layer) {
                        layer.setVisible(false);
                    }
                });
            }

            // Show new room's tilemap
            Object.entries(tilemapObj.layers).forEach(([name, layer]) => {
                if (layer) {
                    const config = this.layerConfig[name];
                    const shouldBeVisible = config?.visible !== false;
                    layer.setVisible(shouldBeVisible);
                }
            });

            this.currentRoomTilemap = tilemapObj;
        }
    }

    /**
     * Clear all tilemaps
     */
    clearAll() {
        this.tilemaps.forEach((_, roomName) => {
            this.clearRoomTilemap(roomName);
        });
        this.currentRoomTilemap = null;
    }

    /**
     * Get the current room's tilemap object
     * @returns {object|null}
     */
    getCurrentTilemap() {
        return this.currentRoomTilemap;
    }
}
