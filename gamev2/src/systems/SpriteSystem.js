/**
 * SpriteSystem - Manages sprite configuration, animations, and directional sprites
 */
class SpriteSystem {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;
        this.spriteMetadata = {};
    }

    /**
     * Initialize sprite metadata from configuration
     * @param {Object} config - Game configuration object
     */
    initialize(config) {
        this.spriteMetadata = config.spriteMetadata || {};

        // Apply player's directional sprites if defined
        if (config.player.directionalSprites) {
            const playerSpriteKey = config.player.sprite;
            if (this.spriteMetadata[playerSpriteKey]) {
                this.spriteMetadata[playerSpriteKey].isDirectional = true;
                this.spriteMetadata[playerSpriteKey].directions = config.player.directionalSprites;

                // Apply auto-flip settings if defined
                if (config.player.autoFlip) {
                    this.spriteMetadata[playerSpriteKey].autoFlip = config.player.autoFlip;
                }
            }
        }

        // Apply NPC directional sprites
        for (let roomKey in config.rooms) {
            const roomConfig = config.rooms[roomKey];
            roomConfig.npcs.forEach(npcConfig => {
                if (npcConfig.directionalSprites && this.spriteMetadata[npcConfig.sprite]) {
                    this.spriteMetadata[npcConfig.sprite].isDirectional = true;
                    this.spriteMetadata[npcConfig.sprite].directions = npcConfig.directionalSprites;

                    if (npcConfig.autoFlip) {
                        this.spriteMetadata[npcConfig.sprite].autoFlip = npcConfig.autoFlip;
                    }
                }
            });
        }
    }

    /**
     * Create Phaser animations from sprite metadata
     */
    createAnimations() {
        for (const [spriteKey, metadata] of Object.entries(this.spriteMetadata)) {
            const frameCount = metadata.frameCount || 1;
            const isSpriteSheet = metadata.spriteSheet === true;

            // Only create animation if there are multiple frames
            if (frameCount > 1) {
                const animKey = spriteKey + '_anim';

                // Don't recreate if animation already exists
                if (this.scene.anims.exists(animKey)) {
                    continue;
                }

                let frames = [];

                // Handle sprite sheet frames
                if (isSpriteSheet && this.scene.textures.exists(spriteKey)) {
                    const startFrame = metadata.startFrame || 0;
                    const endFrame = metadata.endFrame !== null && metadata.endFrame !== undefined
                        ? metadata.endFrame
                        : frameCount - 1;

                    frames = this.scene.anims.generateFrameNumbers(spriteKey, {
                        start: startFrame,
                        end: endFrame
                    });
                }
                // Handle separate frame images
                else {
                    for (let i = 0; i < frameCount; i++) {
                        const frameKey = `${spriteKey}_frame_${i}`;
                        if (this.scene.textures.exists(frameKey)) {
                            frames.push({ key: frameKey });
                        }
                    }
                }

                // Only create animation if we have frames
                if (frames.length > 0) {
                    this.scene.anims.create({
                        key: animKey,
                        frames: frames,
                        frameRate: metadata.frameRate || 10,
                        repeat: metadata.loop !== false ? -1 : 0
                    });
                }
            }
        }
    }

    /**
     * Get sprite configuration (scale and anchor) from metadata
     * @param {string} spriteKey - Sprite key to look up
     * @returns {Object} Sprite configuration object
     */
    getSpriteConfig(spriteKey) {
        const metadata = this.spriteMetadata[spriteKey];

        if (!metadata) {
            console.warn(`No metadata found for sprite: ${spriteKey}`);
        }

        return {
            scale: metadata?.scale || 1,
            anchorX: metadata?.anchorX !== undefined ? metadata.anchorX : 0.5,
            anchorY: metadata?.anchorY !== undefined ? metadata.anchorY : 0.5,
            hasAnimation: metadata?.frameCount > 1,
            frameCount: metadata?.frameCount || 1,
            frameRate: metadata?.frameRate || 10,
            loop: metadata?.loop !== undefined ? metadata.loop : true,
            spriteSheet: metadata?.spriteSheet || false,
            isDirectional: metadata?.isDirectional || false,
            directions: metadata?.directions || {},
            autoFlip: metadata?.autoFlip || { horizontal: false, vertical: false },
            defaultDirection: metadata?.defaultDirection || 'down'
        };
    }

    /**
     * Get the sprite key for a specific direction
     * @param {string} baseSpriteKey - Base sprite key
     * @param {string} direction - Direction (up, down, left, right)
     * @returns {string} Directional sprite key
     */
    getDirectionalSpriteKey(baseSpriteKey, direction) {
        const metadata = this.spriteMetadata[baseSpriteKey];

        if (!metadata || !metadata.isDirectional) {
            return baseSpriteKey;
        }

        const directionSprite = metadata.directions?.[direction];

        // If specific direction sprite exists, use it
        if (directionSprite) {
            return directionSprite;
        }

        // Check for auto-flip alternatives
        const autoFlip = metadata.autoFlip || {};

        if (direction === 'right' && autoFlip.horizontal && metadata.directions?.left) {
            return metadata.directions.left;
        } else if (direction === 'left' && autoFlip.horizontal && metadata.directions?.right) {
            return metadata.directions.right;
        } else if (direction === 'down' && autoFlip.vertical && metadata.directions?.up) {
            return metadata.directions.up;
        } else if (direction === 'up' && autoFlip.vertical && metadata.directions?.down) {
            return metadata.directions.down;
        }

        // Default to base sprite
        return baseSpriteKey;
    }

    /**
     * Get flip information for directional sprites
     * @param {string} baseSpriteKey - Base sprite key
     * @param {string} direction - Direction (up, down, left, right)
     * @returns {Object} Flip information {flipX, flipY}
     */
    getDirectionalFlipInfo(baseSpriteKey, direction) {
        const metadata = this.spriteMetadata[baseSpriteKey];

        if (!metadata || !metadata.isDirectional) {
            return { flipX: false, flipY: false };
        }

        const directionSprite = metadata.directions?.[direction];
        const autoFlip = metadata.autoFlip || {};

        // If specific direction sprite exists, no flipping needed
        if (directionSprite) {
            return { flipX: false, flipY: false };
        }

        // Check if we need to flip
        let flipX = false;
        let flipY = false;

        if (direction === 'right' && autoFlip.horizontal && metadata.directions?.left) {
            flipX = true;
        } else if (direction === 'left' && autoFlip.horizontal && metadata.directions?.right) {
            flipX = true;
        } else if (direction === 'down' && autoFlip.vertical && metadata.directions?.up) {
            flipY = true;
        } else if (direction === 'up' && autoFlip.vertical && metadata.directions?.down) {
            flipY = true;
        }

        return { flipX, flipY };
    }

    /**
     * Load sprite assets dynamically based on metadata
     * @param {string} spriteKey - Sprite key to load
     * @param {Object} metadata - Sprite metadata
     */
    loadSpriteAssets(spriteKey, metadata) {
        const frameCount = metadata.frameCount || 1;
        const isSpriteSheet = metadata.spriteSheet === true;

        // Check if this sprite uses a sprite sheet
        if (isSpriteSheet) {
            const spritePath = `assets/sprites/${spriteKey}.png`;

            // Configure sprite sheet frame dimensions
            const frameConfig = {
                frameWidth: metadata.frameWidth,
                frameHeight: metadata.frameHeight
            };

            // Optional parameters
            if (metadata.startFrame !== undefined) frameConfig.startFrame = metadata.startFrame;
            if (metadata.endFrame !== undefined) frameConfig.endFrame = metadata.endFrame;
            if (metadata.margin !== undefined) frameConfig.margin = metadata.margin;
            if (metadata.spacing !== undefined) frameConfig.spacing = metadata.spacing;

            this.scene.load.spritesheet(spriteKey, spritePath, frameConfig);
        }
        // Multiple frames as separate images
        else if (frameCount > 1) {
            for (let i = 0; i < frameCount; i++) {
                const framePath = `assets/sprites/${spriteKey}_frame_${i}.png`;
                this.scene.load.image(`${spriteKey}_frame_${i}`, framePath);
            }
        }
        // Single frame sprite
        else {
            const spritePath = `assets/sprites/${spriteKey}.png`;
            if (!this.scene.textures.exists(spriteKey)) {
                this.scene.load.image(spriteKey, spritePath);
            }
        }
    }
}
