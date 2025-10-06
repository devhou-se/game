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
    }

    create() {
        this.GRID_SIZE = 64; // Each grid cell is 64x64 pixels
        this.WORLD_WIDTH = 960; // 15 cells wide (15 * 64)
        this.WORLD_HEIGHT = 640; // 10 cells tall (10 * 64)
        this.DEADZONE_CELLS = 4; // 5x5 grid cells (4*64 + player cell = 5 cells)
        this.DEADZONE_SIZE = this.DEADZONE_CELLS * this.GRID_SIZE;
        this.MOVE_DURATION = 200; // milliseconds for smooth movement

        // Room system (will be initialized after centerGrid is calculated)
        this.currentRoom = 'Tokyo';
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

        // Create player character in center of world with restricted bounds
        const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        // Initialize rooms with center coordinates
        this.rooms = {
            Tokyo: {
                name: 'Tokyo',
                npcs: [],
                objects: [
                    { gridX: centerGridX - 4, gridY: centerGridY - 3 },
                    { gridX: centerGridX + 4, gridY: centerGridY - 2 },
                    { gridX: centerGridX - 3, gridY: centerGridY + 3 }
                ],
                transporters: [
                    { gridX: centerGridX - 2, gridY: centerGridY - 2, targetRoom: 'Osaka', targetX: centerGridX + 3, targetY: centerGridY + 2 }
                ]
            },
            Osaka: {
                name: 'Osaka',
                npcs: [],
                objects: [
                    { gridX: centerGridX + 1, gridY: centerGridY + 1 },
                    { gridX: centerGridX - 4, gridY: centerGridY + 2 },
                    { gridX: centerGridX + 4, gridY: centerGridY - 3 }
                ],
                transporters: [
                    { gridX: centerGridX + 3, gridY: centerGridY + 2, targetRoom: 'Tokyo', targetX: centerGridX - 2, targetY: centerGridY - 2 }
                ]
            }
        };

        this.player = new Character(this, centerGridX, centerGridY, 'tile', {
            gridSize: this.GRID_SIZE,
            worldSize: this.WORLD_WIDTH, // Use width for compatibility
            moveDuration: this.MOVE_DURATION,
            isPlayer: true,
            name: 'Player',
            minGridX: minGridX,
            maxGridX: maxGridX,
            minGridY: minGridY,
            maxGridY: maxGridY
        });

        // Array to hold all characters (NPCs will be added here later)
        this.characters = [this.player];

        // Spawn Bailey NPC in Tokyo
        const bailey = this.spawnNPC(centerGridX + 2, centerGridY + 1, 'npc-tile', 'Bailey');
        this.rooms.Tokyo.npcs.push(bailey);

        // Load current room transporters and objects
        this.loadRoomTransporters();
        this.loadRoomObjects();

        // Set up NPC wandering timer (every 5 seconds)
        this.time.addEvent({
            delay: 5000,
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

        // Track key states for press detection
        this.lastKeyState = {
            left: false,
            right: false,
            up: false,
            down: false,
            esc: false,
            enter: false
        };

        // Menu state
        this.menuVisible = false;
        this.selectedMenuIndex = 0;
        this.menuOptions = [];

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
        const date = "October 6 2025";
        const hudText = `game.devhou.se | ${this.currentRoom} | ${date}`;

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
        this.menuButton.on('pointerdown', () => this.toggleMenu());

        // Create menu overlay (hidden initially)
        this.createMenu();
    }

    updateHUD() {
        const date = "October 6 2025";
        const hudText = `game.devhou.se | ${this.currentRoom} | ${date}`;
        this.hudText.setText(hudText);
    }

    createMenu() {
        // Semi-transparent background overlay (separate from container to allow clicks through)
        this.menuOverlay = this.add.graphics();
        this.menuOverlay.fillStyle(0x000000, 0.85);
        this.menuOverlay.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);
        this.menuOverlay.setScrollFactor(0);
        this.menuOverlay.setDepth(2000);
        this.menuOverlay.setInteractive(
            new Phaser.Geom.Rectangle(0, 0, this.cameras.main.width, this.cameras.main.height),
            Phaser.Geom.Rectangle.Contains
        );
        this.menuOverlay.on('pointerdown', () => this.hideMenu());

        // Menu overlay container
        this.menuContainer = this.add.container(0, 0);
        this.menuContainer.setScrollFactor(0);
        this.menuContainer.setDepth(2001);

        // Menu panel
        const panelWidth = 300;
        const panelHeight = 250;
        const panelX = (this.cameras.main.width - panelWidth) / 2;
        const panelY = (this.cameras.main.height - panelHeight) / 2;

        const panel = this.add.graphics();
        panel.fillStyle(0x1a1a1a, 1);
        panel.fillRect(panelX, panelY, panelWidth, panelHeight);
        panel.lineStyle(2, 0x666666, 1);
        panel.strokeRect(panelX, panelY, panelWidth, panelHeight);
        this.menuContainer.add(panel);

        // Menu title
        this.menuTitle = this.add.text(
            this.cameras.main.width / 2,
            panelY + 30,
            'MENU',
            {
                fontSize: '24px',
                fill: '#ffffff',
                fontFamily: 'monospace'
            }
        );
        this.menuTitle.setOrigin(0.5, 0.5);
        this.menuTitle.setResolution(window.devicePixelRatio || 2);
        this.menuTitle.setScrollFactor(0);
        this.menuTitle.setDepth(2002);
        this.menuTitle.setVisible(false);

        // Menu options
        const options = [
            { text: 'Achievements', action: () => this.showAchievements() },
            { text: 'Map', action: () => this.showMap() },
            { text: 'Credits', action: () => this.showCredits() }
        ];

        const startY = panelY + 80;
        const spacing = 50;

        this.menuOptions = []; // Reset menu options array

        options.forEach((option, index) => {
            const optionText = this.add.text(
                this.cameras.main.width / 2,
                startY + (index * spacing),
                option.text,
                {
                    fontSize: '20px',
                    fill: '#ffffff',
                    fontFamily: 'monospace'
                }
            );
            optionText.setOrigin(0.5, 0.5);
            optionText.setResolution(window.devicePixelRatio || 2);
            optionText.setScrollFactor(0);
            optionText.setDepth(2002);
            optionText.setInteractive({ useHandCursor: true });
            optionText.setVisible(false);

            // Store reference with action
            this.menuOptions.push({
                textObject: optionText,
                action: option.action,
                index: index
            });

            // Hover effects
            optionText.on('pointerover', () => {
                this.selectMenuOption(index);
            });
            optionText.on('pointerdown', () => {
                this.activateMenuOption();
            });
        });

        // Hide menu initially
        this.menuContainer.setVisible(false);
        this.menuOverlay.setVisible(false);
    }

    toggleMenu() {
        if (this.menuVisible) {
            this.hideMenu();
        } else {
            this.showMenu();
        }
    }

    showMenu() {
        this.menuVisible = true;
        this.menuOverlay.setVisible(true);
        this.menuContainer.setVisible(true);
        this.menuTitle.setVisible(true);
        this.menuOptions.forEach(option => option.textObject.setVisible(true));
        this.selectedMenuIndex = 0;
        this.updateMenuSelection();
    }

    hideMenu() {
        this.menuVisible = false;
        this.menuOverlay.setVisible(false);
        this.menuContainer.setVisible(false);
        this.menuTitle.setVisible(false);
        this.menuOptions.forEach(option => option.textObject.setVisible(false));
    }

    selectMenuOption(index) {
        this.selectedMenuIndex = index;
        this.updateMenuSelection();
    }

    updateMenuSelection() {
        // Update visual feedback for all menu options
        this.menuOptions.forEach((option, index) => {
            if (index === this.selectedMenuIndex) {
                option.textObject.setFill('#ffff00');
            } else {
                option.textObject.setFill('#ffffff');
            }
        });
    }

    activateMenuOption() {
        const selectedOption = this.menuOptions[this.selectedMenuIndex];
        if (selectedOption) {
            selectedOption.action();
            this.hideMenu();
        }
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
        // Handle ESC key for menu toggle
        if (this.escKey.isDown && !this.lastKeyState.esc) {
            this.toggleMenu();
        }
        this.lastKeyState.esc = this.escKey.isDown;

        // If menu is visible, handle menu navigation
        if (this.menuVisible) {
            // Arrow up - previous option
            if (this.cursors.up.isDown && !this.lastKeyState.up) {
                this.selectedMenuIndex = (this.selectedMenuIndex - 1 + this.menuOptions.length) % this.menuOptions.length;
                this.updateMenuSelection();
            }

            // Arrow down - next option
            if (this.cursors.down.isDown && !this.lastKeyState.down) {
                this.selectedMenuIndex = (this.selectedMenuIndex + 1) % this.menuOptions.length;
                this.updateMenuSelection();
            }

            // Enter - activate selected option
            if (this.enterKey.isDown && !this.lastKeyState.enter) {
                this.activateMenuOption();
            }

            // Update key states for menu navigation
            this.lastKeyState.up = this.cursors.up.isDown;
            this.lastKeyState.down = this.cursors.down.isDown;
            this.lastKeyState.enter = this.enterKey.isDown;

            return; // Block player movement
        }

        // If currently moving or transitioning, don't accept input
        if (this.player.isMoving || this.isTransitioning) return;

        // Check if any directional keys are currently held
        const anyKeyHeld = this.cursors.left.isDown || this.cursors.right.isDown ||
                           this.cursors.up.isDown || this.cursors.down.isDown;

        // Update last key states
        this.lastKeyState.left = this.cursors.left.isDown;
        this.lastKeyState.right = this.cursors.right.isDown;
        this.lastKeyState.up = this.cursors.up.isDown;
        this.lastKeyState.down = this.cursors.down.isDown;

        // If any directional key is held, move based on ALL currently held keys
        if (anyKeyHeld) {
            let moveX = 0;
            let moveY = 0;

            if (this.cursors.left.isDown) moveX -= 1;
            if (this.cursors.right.isDown) moveX += 1;
            if (this.cursors.up.isDown) moveY -= 1;
            if (this.cursors.down.isDown) moveY += 1;

            const speedMultiplier = this.shiftKey.isDown ? 2 : 1;

            if (moveX !== 0 || moveY !== 0) {
                this.player.startMovement(moveX, moveY, speedMultiplier);
            }
        }
    }

    // Helper method to spawn NPCs
    spawnNPC(gridX, gridY, spriteKey, name) {
        // NPCs can only move within a 5x5 box centered on their starting position
        const wanderRadius = 2; // 5x5 box = ±2 cells in each direction
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
