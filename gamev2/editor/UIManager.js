// UIManager - Handles UI updates for the editor
class UIManager {
    constructor(configManager, getCurrentRoom) {
        this.configManager = configManager;
        this.getCurrentRoom = getCurrentRoom;
    }

    // Update all UI elements
    updateUI() {
        const config = this.configManager.getConfig();

        // Update game settings
        document.getElementById('game-title').value = config.game.title;
        document.getElementById('game-date').value = config.game.date;
        document.getElementById('game-gridsize').value = config.game.gridSize;
        document.getElementById('game-width').value = config.game.worldWidth;
        document.getElementById('game-height').value = config.game.worldHeight;

        // Update room selector
        this.updateRoomSelector();

        // Update sprite list
        this.updateSpriteList();
    }

    // Update room selection dropdown
    updateRoomSelector() {
        const select = document.getElementById('room-select');
        const rooms = this.configManager.getRooms();
        const currentRoom = this.getCurrentRoom();

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

    // Update sprite list display
    updateSpriteList() {
        const container = document.getElementById('sprite-list');
        const sprites = this.configManager.getAllSpriteMetadata();

        container.innerHTML = '';
        sprites.forEach(({ key, frames, scale, anchorX, anchorY }) => {
            const item = document.createElement('div');
            item.className = 'sprite-item';
            item.style.cursor = 'pointer';
            item.innerHTML = `
                <div class="sprite-preview">
                    <img src="${frames[0]}" alt="${key}" style="image-rendering: pixelated;">
                </div>
                <div class="sprite-info">
                    <div class="sprite-name">${key}</div>
                    <div class="sprite-meta" style="font-size: 10px; color: #888;">
                        ${frames.length > 1 ? `${frames.length} frames` : 'Static'} |
                        Scale: ${scale}x
                    </div>
                </div>
            `;

            // Make sprite clickable to edit
            item.addEventListener('click', () => {
                // Get the sprite manager from window (will be set in editor.js)
                if (window.spriteManager) {
                    window.spriteManager.createSpriteModal(key);
                }
            });

            container.appendChild(item);
        });
    }

    // Load default sprites from assets folder
    async loadDefaultSprites() {
        const config = this.configManager.getConfig();
        const spriteMetadata = config.spriteMetadata || {};

        // 1. Load sprites based on config metadata
        for (const [key, metadata] of Object.entries(spriteMetadata)) {
            const frameCount = metadata.frameCount || 1;

            if (frameCount === 1) {
                // Single frame sprite - try to load single image
                await this.loadSingleSprite(key);
            } else {
                // Multi-frame animation - try to load individual frames
                await this.loadMultiFrameSprite(key, frameCount);
            }
        }

        // 2. Load hardcoded defaults if not already loaded
        const defaultSprites = [
            { key: 'tile', path: '../assets/single-tile.png' },
            { key: 'npc-tile', path: '../assets/npc-tile.png' },
            { key: 'object-tile', path: '../assets/object-tile.png' },
            { key: 'transporter', path: '../assets/transporter.png' }
        ];

        for (const sprite of defaultSprites) {
            const metadata = this.configManager.getSpriteMetadata(sprite.key);
            if (!metadata || metadata.frames.length === 0) {
                await this.loadSingleSpriteFromPath(sprite.key, sprite.path);
            }
        }
    }

    // Load a single-frame sprite
    async loadSingleSprite(key) {
        const possiblePaths = [
            `../assets/sprites/${key}.png`,
            `../assets/${key}.png`
        ];

        for (const path of possiblePaths) {
            if (await this.loadSingleSpriteFromPath(key, path)) {
                return true;
            }
        }

        console.warn(`Could not load sprite: ${key}`);
        return false;
    }

    // Load a sprite from a specific path
    async loadSingleSpriteFromPath(key, path) {
        try {
            const response = await fetch(path);
            if (response.ok) {
                const blob = await response.blob();
                const dataUrl = await this.blobToDataURL(blob);

                // Check if sprite metadata exists
                const metadata = this.configManager.getSpriteMetadata(key);
                if (metadata && metadata.frames.length === 0) {
                    // Add frame to existing metadata
                    this.configManager.addSpriteFrame(key, dataUrl);
                } else {
                    // Create new sprite
                    this.configManager.addSprite(key, dataUrl);
                }

                console.log(`Loaded sprite: ${key} from ${path}`);
                return true;
            }
        } catch (e) {
            // Path not found, continue
        }
        return false;
    }

    // Load a multi-frame animation sprite
    async loadMultiFrameSprite(key, frameCount) {
        const frames = [];
        let successCount = 0;

        // Try to load each frame
        for (let i = 0; i < frameCount; i++) {
            const possiblePaths = [
                `../assets/sprites/${key}_frame_${i}.png`,
                `../assets/sprites/sprites/${key}_frame_${i}.png`
            ];

            let frameLoaded = false;
            for (const path of possiblePaths) {
                try {
                    const response = await fetch(path);
                    if (response.ok) {
                        const blob = await response.blob();
                        const dataUrl = await this.blobToDataURL(blob);
                        frames.push(dataUrl);
                        successCount++;
                        frameLoaded = true;
                        console.log(`Loaded frame ${i} for ${key} from ${path}`);
                        break;
                    }
                } catch (e) {
                    // Try next path
                }
            }

            if (!frameLoaded) {
                console.warn(`Could not load frame ${i} for sprite: ${key}`);
            }
        }

        // Add frames to sprite metadata
        if (successCount > 0) {
            const metadata = this.configManager.getSpriteMetadata(key);
            if (metadata && metadata.frames.length === 0) {
                // Add frames to existing metadata
                for (const frame of frames) {
                    this.configManager.addSpriteFrame(key, frame);
                }
                console.log(`Loaded ${successCount}/${frameCount} frames for ${key}`);
            }
        } else {
            console.warn(`No frames loaded for sprite: ${key}`);
        }
    }

    // Helper to convert blob to data URL
    blobToDataURL(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
}
