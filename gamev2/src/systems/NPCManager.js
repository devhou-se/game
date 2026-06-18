/**
 * NPCManager - Handles NPC spawning, wandering, and interactions
 */
class NPCManager {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;
        this.characters = [];
    }

    /**
     * Spawn an NPC at the specified grid position
     * @param {number} gridX - Grid X position
     * @param {number} gridY - Grid Y position
     * @param {string} spriteKey - Sprite key for the NPC
     * @param {string} name - NPC name
     * @param {Object} options - Additional options (dialogue, etc.)
     * @returns {Character} The spawned NPC character
     */
    spawnNPC(gridX, gridY, spriteKey, name, options = {}) {
        const wanderRadius = this.scene.config.game.npcWanderRadius;
        const npc = new Character(this.scene, gridX, gridY, spriteKey, {
            gridSize: this.scene.GRID_SIZE,
            worldSize: this.scene.WORLD_WIDTH,
            moveDuration: this.scene.MOVE_DURATION,
            isPlayer: false,
            name: name,
            minGridX: gridX - wanderRadius,
            maxGridX: gridX + wanderRadius,
            minGridY: gridY - wanderRadius,
            maxGridY: gridY + wanderRadius
        });
        this.characters.push(npc);

        // Add dialogue if provided
        if (options.dialogue && options.dialogue.length > 0) {
            npc.dialogue = options.dialogue;
            npc.canInteract = true;
        } else {
            npc.canInteract = false;
        }

        // Add name label above NPC
        const pixelX = gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
        const pixelY = gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
        const label = this.scene.add.text(
            pixelX,
            pixelY - this.scene.GRID_SIZE / 2 - 5,
            name,
            {
                fontSize: '16px',
                fill: '#ffffff',
                fontFamily: 'PixelOperatorMonoBold',
                backgroundColor: '#000000'
            }
        );
        label.setOrigin(0.5, 1);
        label.setDepth(10);
        label.setResolution(1);

        npc.nameLabel = label;

        return npc;
    }

    /**
     * Check if player is trying to interact with an NPC
     * @param {number} targetGridX - Target grid X position
     * @param {number} targetGridY - Target grid Y position
     */
    checkInteraction(targetGridX, targetGridY) {
        // Don't interact if dialogue is already visible
        if (this.scene.dialogueManager.isVisible()) {
            return;
        }

        // Get NPCs in current room
        const currentRoomNPCs = this.scene.roomManager.rooms[this.scene.roomManager.currentRoom].npcs;

        // Check if the target position has an NPC
        for (let npc of currentRoomNPCs) {
            if (npc.gridX === targetGridX && npc.gridY === targetGridY) {
                if (npc.canInteract) {
                    this.scene.dialogueManager.show(npc);
                }
                return;
            }
        }
    }

    /**
     * Handle NPC wandering behavior
     */
    handleWander() {
        // Get NPCs in current room
        const currentRoomNPCs = this.scene.roomManager.rooms[this.scene.roomManager.currentRoom].npcs;

        currentRoomNPCs.forEach(npc => {
            // Skip if this NPC is currently in dialogue
            if (this.scene.dialogueManager.isVisible() && this.scene.dialogueManager.getCurrentNPC() === npc) {
                return;
            }

            // Only move if NPC is not currently moving
            if (!npc.isMoving) {
                // Randomly pick a direction: 0 = stay, 1-4 = cardinal directions
                const direction = Phaser.Math.Between(0, 4);

                let deltaX = 0;
                let deltaY = 0;

                switch (direction) {
                    case 1: // Left
                        deltaX = -1;
                        break;
                    case 2: // Right
                        deltaX = 1;
                        break;
                    case 3: // Up
                        deltaY = -1;
                        break;
                    case 4: // Down
                        deltaY = 1;
                        break;
                    // case 0: stay in place
                }

                // Attempt to move
                if (deltaX !== 0 || deltaY !== 0) {
                    npc.startMovement(deltaX, deltaY);
                }
            }
        });
    }

    /**
     * Update NPC labels to follow their sprites
     */
    updateLabels() {
        const currentRoomNPCs = this.scene.roomManager.rooms[this.scene.roomManager.currentRoom].npcs;
        currentRoomNPCs.forEach(npc => {
            if (npc.nameLabel) {
                npc.nameLabel.setPosition(
                    npc.sprite.x,
                    npc.sprite.y - this.scene.GRID_SIZE / 2 - 5
                );
            }
        });
    }
}
