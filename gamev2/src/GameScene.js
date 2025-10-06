class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');
    }

    preload() {
        this.load.image("background", "assets/background-grid.png");
        this.load.image("tile", "assets/single-tile.png");
        this.load.image("npc-tile", "assets/npc-tile.png");
        this.load.image("transporter", "assets/transporter.png");
        this.load.image("object-tile", "assets/object-tile.png");
        this.load.json("config", "config.json");
    }

    create() {
        // Load configuration from JSON
        this.config = this.cache.json.get('config');

        // Apply game settings from config
        this.GRID_SIZE = this.config.game.gridSize;
        this.WORLD_WIDTH = this.config.game.worldWidth;
        this.WORLD_HEIGHT = this.config.game.worldHeight;
        this.DEADZONE_CELLS = this.config.game.deadzoneCells;
        this.DEADZONE_SIZE = this.DEADZONE_CELLS * this.GRID_SIZE;
        this.MOVE_DURATION = this.config.game.moveDuration;

        // Room system (will be initialized after centerGrid is calculated)
        this.currentRoom = this.config.player.startRoom;
        this.transporterSprites = [];
        this.objectSprites = [];
        this.isTransitioning = false;

        // Player can move to any cell in the world
        const minGridX = 0;
        const maxGridX = (this.WORLD_WIDTH / this.GRID_SIZE) - 1; // 0-14
        const minGridY = 0;
        const maxGridY = (this.WORLD_HEIGHT / this.GRID_SIZE) - 1; // 0-9

        // Set world bounds to background size
        this.physics.world.setBounds(0, 0, this.WORLD_WIDTH, this.WORLD_HEIGHT);

        // Add background - origin at top-left (0,0)
        const bg = this.add.image(0, 0, 'background');
        bg.setOrigin(0, 0);

        // Calculate center coordinates
        const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        // Initialize rooms from config
        this.rooms = {};
        for (let roomKey in this.config.rooms) {
            const roomConfig = this.config.rooms[roomKey];
            this.rooms[roomKey] = {
                name: roomConfig.name,
                npcs: [],
                objects: roomConfig.objects.map(obj => ({
                    gridX: obj.gridX !== null ? obj.gridX : centerGridX + obj.gridOffsetX,
                    gridY: obj.gridY !== null ? obj.gridY : centerGridY + obj.gridOffsetY
                })),
                transporters: roomConfig.transporters.map(trans => ({
                    gridX: trans.gridX !== null ? trans.gridX : centerGridX + trans.gridOffsetX,
                    gridY: trans.gridY !== null ? trans.gridY : centerGridY + trans.gridOffsetY,
                    targetRoom: trans.targetRoom,
                    targetX: trans.targetX !== null ? trans.targetX : centerGridX + trans.targetOffsetX,
                    targetY: trans.targetY !== null ? trans.targetY : centerGridY + trans.targetOffsetY
                }))
            };
        }

        // Create player from config
        const playerStartX = this.config.player.startX !== null ? this.config.player.startX : centerGridX;
        const playerStartY = this.config.player.startY !== null ? this.config.player.startY : centerGridY;

        this.player = new Character(this, playerStartX, playerStartY, this.config.player.sprite, {
            gridSize: this.GRID_SIZE,
            worldSize: this.WORLD_WIDTH,
            moveDuration: this.MOVE_DURATION,
            isPlayer: true,
            name: this.config.player.name,
            minGridX: minGridX,
            maxGridX: maxGridX,
            minGridY: minGridY,
            maxGridY: maxGridY
        });

        // Array to hold all characters (NPCs will be added here later)
        this.characters = [this.player];

        // Spawn NPCs from config
        for (let roomKey in this.config.rooms) {
            const roomConfig = this.config.rooms[roomKey];
            roomConfig.npcs.forEach(npcConfig => {
                const npcGridX = npcConfig.gridX !== null ? npcConfig.gridX : centerGridX + npcConfig.gridOffsetX;
                const npcGridY = npcConfig.gridY !== null ? npcConfig.gridY : centerGridY + npcConfig.gridOffsetY;

                const npc = this.spawnNPC(npcGridX, npcGridY, npcConfig.sprite, npcConfig.name, {
                    dialogue: npcConfig.dialogue
                });
                this.rooms[roomKey].npcs.push(npc);
            });
        }

        // Hide NPCs that are not in the current starting room
        for (let roomKey in this.rooms) {
            if (roomKey !== this.currentRoom) {
                this.rooms[roomKey].npcs.forEach(npc => {
                    npc.sprite.setVisible(false);
                    if (npc.nameLabel) npc.nameLabel.setVisible(false);
                });
            }
        }

        // Load current room transporters and objects
        this.loadRoomTransporters();
        this.loadRoomObjects();

        // Set up NPC wandering timer from config
        this.time.addEvent({
            delay: this.config.game.npcWanderInterval,
            callback: this.handleNPCWander,
            callbackScope: this,
            loop: true
        });

        // Set up camera to follow player with deadzone
        // No camera bounds - camera can pan beyond world to show black void
        this.cameras.main.startFollow(this.player.sprite);
        this.cameras.main.setDeadzone(this.DEADZONE_SIZE, this.DEADZONE_SIZE);
        this.cameras.main.setBackgroundColor('#000000');

        // Set up keyboard controls
        this.cursors = this.input.keyboard.createCursorKeys();
        this.shiftKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SHIFT);
        this.escKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
        this.enterKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
        this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

        // WASD keys
        this.wKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
        this.aKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
        this.sKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
        this.dKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);

        // Track key states for press detection
        this.lastKeyState = {
            left: false,
            right: false,
            up: false,
            down: false,
            esc: false,
            enter: false,
            space: false
        };

        // Create managers
        this.menuManager = new MenuManager(this);
        this.dialogueManager = new DialogueManager(this);

        // Create HUD
        this.createHUD();
    }

    createHUD() {
        const hudHeight = 40;
        const hudColor = 0x000000;
        const hudAlpha = 0.8;

        // Create semi-transparent background bar
        this.hudBackground = this.add.graphics();
        this.hudBackground.fillStyle(hudColor, hudAlpha);
        this.hudBackground.fillRect(0, 0, this.cameras.main.width, hudHeight);
        this.hudBackground.setScrollFactor(0);
        this.hudBackground.setDepth(1000);

        // Game info (left aligned)
        const hudText = `${this.config.game.title} | ${this.currentRoom} | ${this.config.game.date}`;

        // Create HUD text (left aligned)
        this.hudText = this.add.text(
            10,
            hudHeight / 2,
            hudText,
            {
                fontSize: '18px',
                fill: '#ffffff',
                fontFamily: 'monospace'
            }
        );
        this.hudText.setOrigin(0, 0.5);
        this.hudText.setScrollFactor(0);
        this.hudText.setDepth(1001);
        this.hudText.setResolution(window.devicePixelRatio || 2);

        // Menu button (right aligned)
        this.menuButton = this.add.text(
            this.cameras.main.width - 10,
            hudHeight / 2,
            'menu',
            {
                fontSize: '18px',
                fill: '#ffffff',
                fontFamily: 'monospace'
            }
        );
        this.menuButton.setOrigin(1, 0.5);
        this.menuButton.setScrollFactor(0);
        this.menuButton.setDepth(1001);
        this.menuButton.setResolution(window.devicePixelRatio || 2);
        this.menuButton.setInteractive({ useHandCursor: true });
        this.menuButton.on('pointerdown', () => this.menuManager.toggle());
    }

    updateHUD() {
        const hudText = `${this.config.game.title} | ${this.currentRoom} | ${this.config.game.date}`;
        this.hudText.setText(hudText);
    }

    showAchievements() {
        console.log('Achievements feature coming soon!');
    }

    showMap() {
        console.log('Map feature coming soon!');
    }

    showCredits() {
        console.log('Credits: Built with Phaser 3.90.0');
    }

    loadRoomTransporters() {
        // Clear existing transporter sprites and labels
        this.transporterSprites.forEach(sprite => sprite.destroy());
        this.transporterSprites = [];
        if (this.transporterLabels) {
            this.transporterLabels.forEach(label => label.destroy());
        }
        this.transporterLabels = [];

        // Create transporter sprites for current room
        const room = this.rooms[this.currentRoom];
        room.transporters.forEach(trans => {
            const pixelX = trans.gridX * this.GRID_SIZE + this.GRID_SIZE / 2;
            const pixelY = trans.gridY * this.GRID_SIZE + this.GRID_SIZE / 2;
            const sprite = this.add.sprite(pixelX, pixelY, 'transporter');
            sprite.setDepth(0); // Above background, below characters
            this.transporterSprites.push(sprite);

            // Add label above transporter
            const label = this.add.text(
                pixelX,
                pixelY - this.GRID_SIZE / 2 - 5,
                `Goto ${trans.targetRoom}`,
                {
                    fontSize: '12px',
                    fill: '#00ff00',
                    fontFamily: 'monospace',
                    backgroundColor: '#000000'
                }
            );
            label.setOrigin(0.5, 1);
            label.setDepth(10);
            label.setResolution(window.devicePixelRatio || 2);
            this.transporterLabels.push(label);
        });
    }

    loadRoomObjects() {
        // Clear existing object sprites
        this.objectSprites.forEach(sprite => sprite.destroy());
        this.objectSprites = [];

        // Create object sprites for current room
        const room = this.rooms[this.currentRoom];
        if (room.objects) {
            room.objects.forEach(obj => {
                const pixelX = obj.gridX * this.GRID_SIZE + this.GRID_SIZE / 2;
                const pixelY = obj.gridY * this.GRID_SIZE + this.GRID_SIZE / 2;
                const sprite = this.add.sprite(pixelX, pixelY, 'object-tile');
                sprite.setDepth(0); // Above background, below characters
                this.objectSprites.push(sprite);

                // Store grid position on sprite for collision detection
                sprite.gridX = obj.gridX;
                sprite.gridY = obj.gridY;
            });
        }
    }

    checkTransporter() {
        const room = this.rooms[this.currentRoom];
        const playerPos = this.player.getGridPosition();

        for (let trans of room.transporters) {
            if (trans.gridX === playerPos.x && trans.gridY === playerPos.y) {
                this.switchRoom(trans.targetRoom, trans.targetX, trans.targetY);
                return true;
            }
        }
        return false;
    }

    checkNPCInteraction(targetGridX, targetGridY) {
        // Don't interact if dialogue is already visible
        if (this.dialogueManager.isVisible()) {
            return;
        }

        // Get NPCs in current room
        const currentRoomNPCs = this.rooms[this.currentRoom].npcs;

        // Check if the target position has an NPC
        for (let npc of currentRoomNPCs) {
            if (npc.gridX === targetGridX && npc.gridY === targetGridY) {
                // Found an NPC at the target position
                if (npc.canInteract) {
                    this.dialogueManager.show(npc);
                }
                return;
            }
        }
    }

    switchRoom(newRoom, targetX, targetY) {
        // Block input during transition
        this.isTransitioning = true;

        // Fade to black
        this.cameras.main.fadeOut(250, 0, 0, 0);

        this.cameras.main.once('camerafadeoutcomplete', () => {
            // Hide current room NPCs and their labels
            const oldRoom = this.rooms[this.currentRoom];
            oldRoom.npcs.forEach(npc => {
                npc.sprite.setVisible(false);
                if (npc.nameLabel) npc.nameLabel.setVisible(false);
            });

            // Update current room
            this.currentRoom = newRoom;

            // Move player to target position
            this.player.gridX = targetX;
            this.player.gridY = targetY;
            const pixelX = targetX * this.GRID_SIZE + this.GRID_SIZE / 2;
            const pixelY = targetY * this.GRID_SIZE + this.GRID_SIZE / 2;
            this.player.sprite.setPosition(pixelX, pixelY);

            // Center camera on player
            this.cameras.main.centerOn(pixelX, pixelY);

            // Show new room NPCs and their labels
            const room = this.rooms[this.currentRoom];
            room.npcs.forEach(npc => {
                npc.sprite.setVisible(true);
                if (npc.nameLabel) npc.nameLabel.setVisible(true);
            });

            // Load new room transporters and objects
            this.loadRoomTransporters();
            this.loadRoomObjects();

            // Update HUD
            this.updateHUD();

            // Wait 0.25 seconds on black, then fade in
            this.time.delayedCall(250, () => {
                this.cameras.main.fadeIn(250, 0, 0, 0);

                // Re-enable input after fade-in completes
                this.cameras.main.once('camerafadeincomplete', () => {
                    this.isTransitioning = false;
                });
            });
        });
    }

    update() {
        this.handlePlayerInput();
        this.updateNPCLabels();
    }

    updateNPCLabels() {
        // Update NPC name labels to follow their sprites
        const currentRoomNPCs = this.rooms[this.currentRoom].npcs;
        currentRoomNPCs.forEach(npc => {
            if (npc.nameLabel) {
                npc.nameLabel.setPosition(
                    npc.sprite.x,
                    npc.sprite.y - this.GRID_SIZE / 2 - 5
                );
            }
        });
    }

    handlePlayerInput() {
        // If dialogue is visible, handle dialogue input
        if (this.dialogueManager.isVisible()) {
            const spacePressed = this.spaceKey.isDown && !this.lastKeyState.space;
            const enterPressed = this.enterKey.isDown && !this.lastKeyState.enter;
            const escPressed = this.escKey.isDown && !this.lastKeyState.esc;

            // ESC to close dialogue
            if (escPressed) {
                this.dialogueManager.close();
            }
            // Space or Enter to advance dialogue
            else if (spacePressed || enterPressed) {
                this.dialogueManager.advance();
            }

            this.lastKeyState.space = this.spaceKey.isDown;
            this.lastKeyState.enter = this.enterKey.isDown;
            this.lastKeyState.esc = this.escKey.isDown;
            return; // Block other input
        }

        // Handle ESC key for menu toggle
        if (this.escKey.isDown && !this.lastKeyState.esc) {
            this.menuManager.toggle();
        }
        this.lastKeyState.esc = this.escKey.isDown;

        // If menu is visible, handle menu navigation
        if (this.menuManager.isVisible()) {
            // Arrow up - previous option
            if (this.cursors.up.isDown && !this.lastKeyState.up) {
                this.menuManager.selectPrevious();
            }

            // Arrow down - next option
            if (this.cursors.down.isDown && !this.lastKeyState.down) {
                this.menuManager.selectNext();
            }

            // Enter - activate selected option
            if (this.enterKey.isDown && !this.lastKeyState.enter) {
                this.menuManager.activate();
            }

            // Update key states for menu navigation
            this.lastKeyState.up = this.cursors.up.isDown;
            this.lastKeyState.down = this.cursors.down.isDown;
            this.lastKeyState.enter = this.enterKey.isDown;

            return; // Block player movement
        }

        // If currently moving or transitioning, don't accept input
        if (this.player.isMoving || this.isTransitioning) return;

        // Check if any directional keys are currently held (arrows or WASD)
        const anyKeyHeld = this.cursors.left.isDown || this.cursors.right.isDown ||
                           this.cursors.up.isDown || this.cursors.down.isDown ||
                           this.aKey.isDown || this.dKey.isDown ||
                           this.wKey.isDown || this.sKey.isDown;

        // Update last key states
        this.lastKeyState.left = this.cursors.left.isDown;
        this.lastKeyState.right = this.cursors.right.isDown;
        this.lastKeyState.up = this.cursors.up.isDown;
        this.lastKeyState.down = this.cursors.down.isDown;

        // If any directional key is held, move based on ALL currently held keys
        if (anyKeyHeld) {
            let moveX = 0;
            let moveY = 0;

            if (this.cursors.left.isDown || this.aKey.isDown) moveX -= 1;
            if (this.cursors.right.isDown || this.dKey.isDown) moveX += 1;
            if (this.cursors.up.isDown || this.wKey.isDown) moveY -= 1;
            if (this.cursors.down.isDown || this.sKey.isDown) moveY += 1;

            const speedMultiplier = this.shiftKey.isDown ? 2 : 1;

            if (moveX !== 0 || moveY !== 0) {
                this.player.startMovement(moveX, moveY, speedMultiplier);
            }
        }
    }

    // Helper method to spawn NPCs
    spawnNPC(gridX, gridY, spriteKey, name, options = {}) {
        // NPCs can only move within a box centered on their starting position
        const wanderRadius = this.config.game.npcWanderRadius;
        const npc = new Character(this, gridX, gridY, spriteKey, {
            gridSize: this.GRID_SIZE,
            worldSize: this.WORLD_SIZE,
            moveDuration: this.MOVE_DURATION,
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
        const pixelX = gridX * this.GRID_SIZE + this.GRID_SIZE / 2;
        const pixelY = gridY * this.GRID_SIZE + this.GRID_SIZE / 2;
        const label = this.add.text(
            pixelX,
            pixelY - this.GRID_SIZE / 2 - 5,
            name,
            {
                fontSize: '12px',
                fill: '#ffffff',
                fontFamily: 'monospace',
                backgroundColor: '#000000'
            }
        );
        label.setOrigin(0.5, 1);
        label.setDepth(10);
        label.setResolution(window.devicePixelRatio || 2);

        // Store label reference on NPC
        npc.nameLabel = label;

        return npc;
    }

    // Collision detection
    checkCollision(character, targetGridX, targetGridY, fromGridX, fromGridY) {
        const deltaX = targetGridX - fromGridX;
        const deltaY = targetGridY - fromGridY;
        const isDiagonal = deltaX !== 0 && deltaY !== 0;

        // Cells to check for collision
        const cellsToCheck = [{ x: targetGridX, y: targetGridY }];

        // For diagonal movement, check all cells along the path
        if (isDiagonal) {
            const steps = Math.max(Math.abs(deltaX), Math.abs(deltaY));
            const stepX = Math.sign(deltaX);
            const stepY = Math.sign(deltaY);

            // Check all intermediate cells along both axis paths
            for (let i = 1; i <= steps; i++) {
                // Check horizontal then vertical path
                cellsToCheck.push({ x: fromGridX + (stepX * i), y: fromGridY });
                // Check vertical then horizontal path
                cellsToCheck.push({ x: fromGridX, y: fromGridY + (stepY * i) });
                // Check diagonal path
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

        // Check collision with objects first
        for (let obj of this.objectSprites) {
            for (let cell of cellsToCheck) {
                if (obj.gridX === cell.x && obj.gridY === cell.y) {
                    return false; // Collision with object
                }
            }
        }

        // Get characters in current room only
        const currentRoomNPCs = this.rooms[this.currentRoom].npcs;
        const charactersInRoom = [this.player, ...currentRoomNPCs];

        for (let other of charactersInRoom) {
            if (other === character) continue; // Skip self

            const otherTarget = other.getTargetPosition();

            // Check all cells in the path
            for (let cell of cellsToCheck) {
                // Check if cell is occupied by another character's current position
                if (other.gridX === cell.x && other.gridY === cell.y) {
                    return false; // Collision with stationary character
                }

                // Check if cell is the destination of another moving character
                if (otherTarget.x === cell.x && otherTarget.y === cell.y) {
                    return false; // Collision with moving character's destination
                }
            }

            // Check for path crossing (swap detection)
            // If other character is moving FROM our target TO our current position
            if (other.isMoving) {
                if (other.startGridX === targetGridX && other.startGridY === targetGridY &&
                    otherTarget.x === fromGridX && otherTarget.y === fromGridY) {
                    return false; // Paths would cross (swap)
                }
            }
        }

        return true; // No collision
    }

    // Handle NPC wandering behavior
    handleNPCWander() {
        // Get NPCs in current room
        const currentRoomNPCs = this.rooms[this.currentRoom].npcs;

        currentRoomNPCs.forEach(npc => {
            // Skip if this NPC is currently in dialogue
            if (this.dialogueManager.isVisible() && this.dialogueManager.getCurrentNPC() === npc) {
                return;
            }

            // Only move if NPC is not currently moving
            if (!npc.isMoving) {
                // Randomly pick a direction: 0 = stay, 1 = left, 2 = right, 3 = up, 4 = down
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
                    // case 0: stay in place (no movement)
                }

                // Attempt to move (collision detection will prevent invalid moves)
                if (deltaX !== 0 || deltaY !== 0) {
                    npc.startMovement(deltaX, deltaY);
                }
            }
        });
    }
}
