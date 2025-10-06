class Character {
    constructor(scene, gridX, gridY, spriteKey, config = {}) {
        this.scene = scene;
        this.gridX = gridX;
        this.gridY = gridY;
        this.gridSize = config.gridSize || 64;
        this.worldSize = config.worldSize || 1024;
        this.moveDuration = config.moveDuration || 200;

        // Movement bounds (default to full world)
        this.minGridX = config.minGridX || 0;
        this.maxGridX = config.maxGridX || (this.worldSize / this.gridSize - 1);
        this.minGridY = config.minGridY || 0;
        this.maxGridY = config.maxGridY || (this.worldSize / this.gridSize - 1);

        // Get sprite configuration (scale, anchor, animation)
        const spriteConfig = scene.getSpriteConfig ? scene.getSpriteConfig(spriteKey) : {
            scale: 1, anchorX: 0.5, anchorY: 0.5, hasAnimation: false
        };

        // Debug: log sprite config
        console.log(`Character ${spriteKey}:`, spriteConfig);

        // Create sprite
        const pixelX = this.gridX * this.gridSize + this.gridSize / 2;
        const pixelY = this.gridY * this.gridSize + this.gridSize / 2;

        // Determine texture key - for multi-frame sprites, use frame_0
        let textureKey = spriteKey;
        if (spriteConfig.frameCount > 1 && !spriteConfig.spriteSheet) {
            textureKey = `${spriteKey}_frame_0`;
        }

        this.sprite = scene.add.sprite(pixelX, pixelY, textureKey);
        this.sprite.setDepth(1); // Above floor tiles (transporters, objects)

        // Apply sprite configuration
        this.sprite.setScale(spriteConfig.scale);
        this.sprite.setOrigin(spriteConfig.anchorX, spriteConfig.anchorY);

        console.log(`Applied scale ${spriteConfig.scale} to ${spriteKey}, actual scale:`, this.sprite.scale);

        // Play animation if available
        if (spriteConfig.hasAnimation && scene.anims.exists(spriteKey + '_anim')) {
            this.sprite.play(spriteKey + '_anim');
        }

        // Movement state
        this.isMoving = false;
        this.currentTween = null;
        this.startGridX = gridX;
        this.startGridY = gridY;
        this.targetDeltaX = 0;
        this.targetDeltaY = 0;

        // Character properties
        this.isPlayer = config.isPlayer || false;
        this.name = config.name || 'Character';

        // Facing direction (for player interaction detection)
        this.facingX = 0;
        this.facingY = 0;

        // Directional sprite support
        this.currentDirection = spriteConfig.defaultDirection || 'down';
        this.baseSpriteKey = spriteKey;
        this.isDirectional = spriteConfig.isDirectional || false;
    }

    updateDirectionSprite(deltaX, deltaY) {
        if (!this.isDirectional) return;

        // Determine new direction based on movement
        let newDirection = this.currentDirection;

        if (deltaY < 0) {
            newDirection = 'up';
        } else if (deltaY > 0) {
            newDirection = 'down';
        } else if (deltaX < 0) {
            newDirection = 'left';
        } else if (deltaX > 0) {
            newDirection = 'right';
        }

        // Only update if direction changed
        if (newDirection !== this.currentDirection) {
            this.currentDirection = newDirection;

            // Get the directional sprite key from scene
            const directionSpriteKey = this.scene.getDirectionalSpriteKey(this.baseSpriteKey, newDirection);

            if (directionSpriteKey) {
                // Get sprite config to determine texture key
                const directionSpriteConfig = this.scene.getSpriteConfig(directionSpriteKey);

                // Determine texture key - for multi-frame sprites, use frame_0
                let textureKey = directionSpriteKey;
                if (directionSpriteConfig.frameCount > 1 && !directionSpriteConfig.spriteSheet) {
                    textureKey = `${directionSpriteKey}_frame_0`;
                }

                // Update sprite texture
                this.sprite.setTexture(textureKey);

                // Check if we need to flip the sprite
                const flipInfo = this.scene.getDirectionalFlipInfo(this.baseSpriteKey, newDirection);
                if (flipInfo) {
                    this.sprite.setFlipX(flipInfo.flipX);
                    this.sprite.setFlipY(flipInfo.flipY);
                }

                // Update animation if it exists
                const animKey = directionSpriteKey + '_anim';
                if (this.scene.anims.exists(animKey)) {
                    this.sprite.play(animKey);
                }
            }
        }
    }

    startMovement(deltaX, deltaY, speedMultiplier = 1) {
        const targetGridX = this.gridX + deltaX;
        const targetGridY = this.gridY + deltaY;

        // Update facing direction
        if (deltaX !== 0 || deltaY !== 0) {
            this.facingX = Math.sign(deltaX);
            this.facingY = Math.sign(deltaY);

            // Update directional sprite
            this.updateDirectionSprite(deltaX, deltaY);
        }

        // Check collision before moving
        if (!this.canMoveTo(targetGridX, targetGridY, this.gridX, this.gridY)) {
            // If this is the player and collision happened, check for NPC interaction
            if (this.isPlayer) {
                this.scene.checkNPCInteraction(targetGridX, targetGridY);
            }
            return; // Movement blocked
        }

        this.isMoving = true;
        this.startGridX = this.gridX;
        this.startGridY = this.gridY;
        this.targetDeltaX = deltaX;
        this.targetDeltaY = deltaY;
        this.speedMultiplier = speedMultiplier;
        this.executeMovement();
    }

    addToMovement(deltaX, deltaY) {
        if (!this.isMoving) {
            this.startMovement(deltaX, deltaY);
            return;
        }

        const newTargetGridX = this.startGridX + this.targetDeltaX + deltaX;
        const newTargetGridY = this.startGridY + this.targetDeltaY + deltaY;

        // Check collision for new target
        if (!this.canMoveTo(newTargetGridX, newTargetGridY, this.startGridX, this.startGridY)) {
            return; // Movement blocked
        }

        this.targetDeltaX += deltaX;
        this.targetDeltaY += deltaY;
        this.updateMovementTarget();
    }

    canMoveTo(targetGridX, targetGridY, fromGridX, fromGridY) {
        // Ask the scene to check collision
        return this.scene.checkCollision(this, targetGridX, targetGridY, fromGridX, fromGridY);
    }

    updateMovementTarget() {
        if (this.currentTween) {
            this.currentTween.remove();
        }
        this.executeMovement();
    }

    executeMovement() {
        const targetGridX = this.startGridX + this.targetDeltaX;
        const targetGridY = this.startGridY + this.targetDeltaY;

        // Clamp to movement bounds
        const clampedGridX = Math.max(this.minGridX, Math.min(this.maxGridX, targetGridX));
        const clampedGridY = Math.max(this.minGridY, Math.min(this.maxGridY, targetGridY));

        const targetX = clampedGridX * this.gridSize + this.gridSize / 2;
        const targetY = clampedGridY * this.gridSize + this.gridSize / 2;

        // Apply speed multiplier (higher multiplier = shorter duration = faster movement)
        const duration = this.moveDuration / (this.speedMultiplier || 1);

        this.currentTween = this.scene.tweens.add({
            targets: this.sprite,
            x: targetX,
            y: targetY,
            duration: duration,
            ease: 'Linear',
            onComplete: () => {
                this.gridX = clampedGridX;
                this.gridY = clampedGridY;
                this.isMoving = false;
                this.currentTween = null;
                this.targetDeltaX = 0;
                this.targetDeltaY = 0;
                this.speedMultiplier = 1;

                // Check for transporter if this is the player
                if (this.isPlayer) {
                    this.scene.checkTransporter();
                }
            }
        });
    }

    getTargetPosition() {
        if (!this.isMoving) {
            return { x: this.gridX, y: this.gridY };
        }
        return {
            x: this.startGridX + this.targetDeltaX,
            y: this.startGridY + this.targetDeltaY
        };
    }

    getPixelPosition() {
        return { x: this.sprite.x, y: this.sprite.y };
    }

    getGridPosition() {
        return { x: this.gridX, y: this.gridY };
    }

    destroy() {
        if (this.currentTween) {
            this.currentTween.remove();
        }
        this.sprite.destroy();
    }
}
