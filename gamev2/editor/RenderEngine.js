// RenderEngine - Handles all rendering for the grid editor
class RenderEngine {
    constructor(gridEditor) {
        this.gridEditor = gridEditor;
        this.sprites = {};
        this.spritesLoaded = false;

        // Animation state
        this.animationState = {}; // { spriteKey: { currentFrame: 0, lastUpdateTime: 0 } }
        this.spriteFrames = {}; // { spriteKey: [Image, Image, ...] }

        // Start animation loop
        this.startAnimationLoop();
    }

    // Load sprite images
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
            this.spritesLoaded = true;
        } catch (e) {
            console.error('Failed to load sprites:', e);
        }
    }

    // Main render method
    render() {
        if (!this.spritesLoaded) return;

        const ctx = this.gridEditor.ctx;
        const config = this.gridEditor.configManager.getConfig();

        // Clear canvas
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, this.gridEditor.canvas.width, this.gridEditor.canvas.height);

        ctx.save();
        ctx.translate(this.gridEditor.offsetX, this.gridEditor.offsetY);
        ctx.scale(this.gridEditor.scale, this.gridEditor.scale);

        // Draw background
        this.drawBackground();

        if (this.gridEditor.currentRoom) {
            const room = this.gridEditor.configManager.getRoom(this.gridEditor.currentRoom);
            const center = this.gridEditor.configManager.getCenterPosition();

            // Draw objects
            room.objects.forEach((obj, index) => {
                const x = obj.gridX !== null ? obj.gridX : center.x + obj.gridOffsetX;
                const y = obj.gridY !== null ? obj.gridY : center.y + obj.gridOffsetY;
                const isSelected = this.gridEditor.selectedItem?.type === 'object' && this.gridEditor.selectedItem?.index === index;
                this.drawSprite(x, y, 'object-tile', isSelected);
            });

            // Draw transporters
            room.transporters.forEach((trans, index) => {
                const x = trans.gridX !== null ? trans.gridX : center.x + trans.gridOffsetX;
                const y = trans.gridY !== null ? trans.gridY : center.y + trans.gridOffsetY;
                const isSelected = this.gridEditor.selectedItem?.type === 'transporter' && this.gridEditor.selectedItem?.index === index;
                this.drawSprite(x, y, 'transporter', isSelected, `→ ${trans.targetRoom}`);
            });

            // Draw NPCs
            room.npcs.forEach((npc, index) => {
                const x = npc.gridX !== null ? npc.gridX : center.x + npc.gridOffsetX;
                const y = npc.gridY !== null ? npc.gridY : center.y + npc.gridOffsetY;
                const isSelected = this.gridEditor.selectedItem?.type === 'npc' && this.gridEditor.selectedItem?.index === index;
                const spriteKey = npc.sprite || 'npc-tile';
                this.drawSprite(x, y, spriteKey, isSelected, npc.name);
            });

            // Draw player start
            if (config.player.startRoom === this.gridEditor.currentRoom) {
                const x = config.player.startX !== null ? config.player.startX : center.x;
                const y = config.player.startY !== null ? config.player.startY : center.y;
                const isSelected = this.gridEditor.selectedItem?.type === 'player';
                const spriteKey = config.player.sprite || 'tile';
                this.drawSprite(x, y, spriteKey, isSelected, 'Player');
            }

            // Draw boundary if in boundary tool mode
            if (this.gridEditor.currentTool === 'boundary' && this.gridEditor.boundaryEditor.boundaryVertices.length > 0) {
                this.gridEditor.boundaryEditor.draw(ctx, this.gridEditor.gridSize);
            }
        }

        ctx.restore();
    }

    // Draw background grid
    drawBackground() {
        const ctx = this.gridEditor.ctx;

        // Draw the background grid image if loaded
        if (this.sprites['background']) {
            ctx.drawImage(this.sprites['background'], 0, 0, this.gridEditor.worldWidth, this.gridEditor.worldHeight);
        } else {
            // Fallback to black background if image not loaded
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, this.gridEditor.worldWidth, this.gridEditor.worldHeight);
        }

        // Draw border
        ctx.strokeStyle = '#444444';
        ctx.lineWidth = 2;
        ctx.strokeRect(0, 0, this.gridEditor.worldWidth, this.gridEditor.worldHeight);
    }

    // Draw a sprite at grid position
    drawSprite(gridX, gridY, spriteKey, isSelected, label = null) {
        const ctx = this.gridEditor.ctx;
        const gridSize = this.gridEditor.gridSize;
        const x = gridX * gridSize + gridSize / 2;
        const y = gridY * gridSize + gridSize / 2;

        // Get sprite metadata if available
        const metadata = this.gridEditor.configManager.getSpriteMetadata(spriteKey);
        const scale = metadata?.scale || 1;
        const anchorX = metadata?.anchorX !== undefined ? metadata.anchorX : 0.5;
        const anchorY = metadata?.anchorY !== undefined ? metadata.anchorY : 0.5;

        // Determine which sprite/frame to draw
        let spriteImage = this.sprites[spriteKey];

        // Check if this sprite has animation frames
        if (this.spriteFrames[spriteKey] && this.spriteFrames[spriteKey].length > 0) {
            const currentFrame = this.animationState[spriteKey]?.currentFrame || 0;
            spriteImage = this.spriteFrames[spriteKey][currentFrame];
        }

        // Draw sprite if loaded, otherwise draw colored rectangle fallback
        if (spriteImage) {
            // Calculate scaled size based on sprite's natural dimensions
            const scaledWidth = spriteImage.width * scale;
            const scaledHeight = spriteImage.height * scale;

            // Calculate position based on anchor
            // anchorX: 0 = left edge, 0.5 = center, 1 = right edge
            // anchorY: 0 = top edge, 0.5 = center, 1 = bottom edge
            const drawX = x - (scaledWidth * anchorX);
            const drawY = y - (scaledHeight * anchorY);

            ctx.drawImage(
                spriteImage,
                drawX,
                drawY,
                scaledWidth,
                scaledHeight
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
            ctx.fillRect(x - gridSize / 2 + 2, y - gridSize / 2 + 2, gridSize - 4, gridSize - 4);
        }

        // Draw selection highlight around the grid cell
        if (isSelected) {
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3;
            ctx.strokeRect(x - gridSize / 2, y - gridSize / 2, gridSize, gridSize);
        }

        // Draw label
        if (label) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.fillRect(x - gridSize / 2, y - gridSize / 2 - 16, gridSize, 16);
            ctx.fillStyle = '#ffffff';
            ctx.font = '10px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, x, y - gridSize / 2 - 8);
        }
    }

    // Load sprite frames from metadata
    async loadSpriteFrames(spriteKey) {
        const metadata = this.gridEditor.configManager.getSpriteMetadata(spriteKey);
        if (!metadata || !metadata.frames || metadata.frames.length <= 1) {
            return; // No animation frames
        }

        // Load all frames as Image objects
        const frames = [];
        for (const frameData of metadata.frames) {
            const img = new Image();
            img.src = frameData;
            await new Promise((resolve) => {
                img.onload = resolve;
                img.onerror = resolve; // Continue even if frame fails
            });
            frames.push(img);
        }

        this.spriteFrames[spriteKey] = frames;

        // Initialize animation state for this sprite
        if (!this.animationState[spriteKey]) {
            this.animationState[spriteKey] = {
                currentFrame: 0,
                lastUpdateTime: Date.now()
            };
        }
    }

    // Animation update loop
    startAnimationLoop() {
        const updateAnimations = () => {
            const now = Date.now();

            // Update each animated sprite
            for (const spriteKey in this.animationState) {
                const metadata = this.gridEditor.configManager.getSpriteMetadata(spriteKey);
                if (!metadata || !this.spriteFrames[spriteKey]) continue;

                const frameRate = metadata.frameRate || 10;
                const frameDuration = 1000 / frameRate; // milliseconds per frame

                const state = this.animationState[spriteKey];
                const timeSinceLastUpdate = now - state.lastUpdateTime;

                if (timeSinceLastUpdate >= frameDuration) {
                    // Advance to next frame
                    const frameCount = this.spriteFrames[spriteKey].length;
                    state.currentFrame = (state.currentFrame + 1) % frameCount;
                    state.lastUpdateTime = now;

                    // Trigger a re-render
                    this.render();
                }
            }

            // Continue loop
            requestAnimationFrame(updateAnimations);
        };

        requestAnimationFrame(updateAnimations);
    }

    // Call this when sprites are added/updated
    async refreshSpriteFrames() {
        const allMetadata = this.gridEditor.configManager.getAllSpriteMetadata();
        for (const { key } of allMetadata) {
            await this.loadSpriteFrames(key);
        }
    }
}
