/**
 * CollisionSystem - Handles collision detection for characters and objects
 */
class CollisionSystem {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;
    }

    /**
     * Check collision for a character moving to a target position
     * @param {Character} character - The character attempting to move
     * @param {number} targetGridX - Target grid X position
     * @param {number} targetGridY - Target grid Y position
     * @param {number} fromGridX - Starting grid X position
     * @param {number} fromGridY - Starting grid Y position
     * @returns {boolean} True if movement is allowed, false if collision detected
     */
    checkCollision(character, targetGridX, targetGridY, fromGridX, fromGridY) {
        const deltaX = targetGridX - fromGridX;
        const deltaY = targetGridY - fromGridY;
        const isDiagonal = deltaX !== 0 && deltaY !== 0;

        // Cells to check for collision
        const cellsToCheck = [{ x: targetGridX, y: targetGridY }];

        // First check if target position is within room boundary
        if (!this.scene.roomManager.checkBoundary(targetGridX, targetGridY)) {
            return false;
        }

        // For diagonal movement, check all cells along the path
        if (isDiagonal) {
            const steps = Math.max(Math.abs(deltaX), Math.abs(deltaY));
            const stepX = Math.sign(deltaX);
            const stepY = Math.sign(deltaY);

            for (let i = 1; i <= steps; i++) {
                cellsToCheck.push({ x: fromGridX + (stepX * i), y: fromGridY });
                cellsToCheck.push({ x: fromGridX, y: fromGridY + (stepY * i) });
                if (Math.abs(deltaX) === Math.abs(deltaY)) {
                    cellsToCheck.push({ x: fromGridX + (stepX * i), y: fromGridY + (stepY * i) });
                }
            }
        } else {
            // For straight movement, check all intermediate cells
            const steps = Math.max(Math.abs(deltaX), Math.abs(deltaY));
            const stepX = deltaX === 0 ? 0 : Math.sign(deltaX);
            const stepY = deltaY === 0 ? 0 : Math.sign(deltaY);

            for (let i = 1; i < steps; i++) {
                cellsToCheck.push({ x: fromGridX + (stepX * i), y: fromGridY + (stepY * i) });
            }
        }

        // Check that all cells in path are within boundary
        for (let cell of cellsToCheck) {
            if (!this.scene.roomManager.checkBoundary(cell.x, cell.y)) {
                return false;
            }
        }

        // Debug noclip (hidden ``` menu): the player ignores tiles, objects
        // and characters, but the room boundary above still applies
        if (character.isPlayer && this.scene.debugManager &&
            this.scene.debugManager.settings.noclip) {
            return true;
        }

        // Check collision with layer tiles
        if (!this.checkTileCollision(cellsToCheck)) {
            return false;
        }

        // Check collision with objects
        if (!this.checkObjectCollision(cellsToCheck)) {
            return false;
        }

        // Check collision with characters
        if (!this.checkCharacterCollision(character, targetGridX, targetGridY, fromGridX, fromGridY, cellsToCheck)) {
            return false;
        }

        return true;
    }

    /**
     * Check collision with layer tiles
     * @param {Array} cellsToCheck - Array of {x, y} cells to check
     * @returns {boolean} True if no collision
     */
    checkTileCollision(cellsToCheck) {
        for (let tile of this.scene.roomManager.floorSprites) {
            const tileCollision = tile.getData('layerCollision');
            if (tileCollision) {
                const tileGridX = tile.getData('gridX');
                const tileGridY = tile.getData('gridY');

                for (let cell of cellsToCheck) {
                    if (tileGridX === cell.x && tileGridY === cell.y) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    /**
     * Check collision with objects
     * @param {Array} cellsToCheck - Array of {x, y} cells to check
     * @returns {boolean} True if no collision
     */
    checkObjectCollision(cellsToCheck) {
        for (let obj of this.scene.roomManager.objectSprites) {
            for (let cell of cellsToCheck) {
                if (obj.gridX === cell.x && obj.gridY === cell.y) {
                    return false;
                }
            }
        }
        return true;
    }

    /**
     * Check collision with other characters
     * @param {Character} character - The character attempting to move
     * @param {number} targetGridX - Target grid X position
     * @param {number} targetGridY - Target grid Y position
     * @param {number} fromGridX - Starting grid X position
     * @param {number} fromGridY - Starting grid Y position
     * @param {Array} cellsToCheck - Array of {x, y} cells to check
     * @returns {boolean} True if no collision
     */
    checkCharacterCollision(character, targetGridX, targetGridY, fromGridX, fromGridY, cellsToCheck) {
        const currentRoomNPCs = this.scene.roomManager.rooms[this.scene.roomManager.currentRoom].npcs;
        const charactersInRoom = [this.scene.player, ...currentRoomNPCs];

        for (let other of charactersInRoom) {
            if (other === character) continue;

            const otherTarget = other.getTargetPosition();

            // Check all cells in the path
            for (let cell of cellsToCheck) {
                // Check if cell is occupied by another character's current position
                if (other.gridX === cell.x && other.gridY === cell.y) {
                    return false;
                }

                // Check if cell is the destination of another moving character
                if (otherTarget.x === cell.x && otherTarget.y === cell.y) {
                    return false;
                }
            }

            // Check for path crossing (swap detection)
            if (other.isMoving) {
                if (other.startGridX === targetGridX && other.startGridY === targetGridY &&
                    otherTarget.x === fromGridX && otherTarget.y === fromGridY) {
                    return false;
                }
            }
        }

        return true;
    }
}
