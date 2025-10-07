/**
 * GameObject - Base class for all interactive objects in the game
 * Supports modular behaviors for flexible object types
 */
class GameObject {
    constructor(config) {
        this.id = config.id || `obj_${Date.now()}_${Math.random()}`;
        this.type = config.type;
        this.gridX = config.gridX;
        this.gridY = config.gridY;
        this.sprite = config.sprite;
        this.properties = config.properties || {};
        this.behaviors = config.behaviors || [];
        this.state = config.initialState || {};
        this.interactionRange = config.interactionRange || 0; // 0 = collision only, 1+ = adjacent cells

        // Phaser sprite reference (set by scene when spawned)
        this.spriteObject = null;

        // Track if object has been removed
        this.destroyed = false;
    }

    /**
     * Called when player collides with this object
     * Executes all behaviors that don't require explicit interaction
     */
    onCollision(player, scene) {
        if (this.destroyed) return;

        this.behaviors.forEach(behaviorName => {
            const behavior = scene.getBehavior(behaviorName);
            if (behavior && !behavior.requiresInteraction) {
                behavior.execute(player, scene, this);
            }
        });
    }

    /**
     * Called when player explicitly interacts with object (spacebar/enter)
     * Executes behaviors that require player action
     */
    onInteract(player, scene) {
        if (this.destroyed) return;

        this.behaviors.forEach(behaviorName => {
            const behavior = scene.getBehavior(behaviorName);
            if (behavior && behavior.requiresInteraction) {
                behavior.execute(player, scene, this);
            }
        });
    }

    /**
     * Check if player is in range to interact with this object
     */
    canInteract(player) {
        if (this.destroyed) return false;

        const distX = Math.abs(this.gridX - player.gridX);
        const distY = Math.abs(this.gridY - player.gridY);
        const manhattanDist = distX + distY;

        return manhattanDist <= this.interactionRange;
    }

    /**
     * Check if player is colliding with this object (same cell)
     */
    isCollidingWith(player) {
        if (this.destroyed) return false;
        return this.gridX === player.gridX && this.gridY === player.gridY;
    }

    /**
     * Update object state (called each frame)
     */
    update(time, delta) {
        // Override in subclasses or use behaviors for custom update logic
    }

    /**
     * Get pixel position based on grid position
     */
    getPixelPosition(gridSize) {
        return {
            x: this.gridX * gridSize + gridSize / 2,
            y: this.gridY * gridSize + gridSize / 2
        };
    }

    /**
     * Mark object for removal
     */
    destroy() {
        this.destroyed = true;
        if (this.spriteObject) {
            this.spriteObject.destroy();
            this.spriteObject = null;
        }
    }

    /**
     * Serialize object state for saving
     */
    serialize() {
        return {
            id: this.id,
            type: this.type,
            gridX: this.gridX,
            gridY: this.gridY,
            state: { ...this.state }
        };
    }

    /**
     * Restore object state from saved data
     */
    deserialize(data) {
        this.gridX = data.gridX;
        this.gridY = data.gridY;
        this.state = { ...data.state };
    }
}
