class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');
    }

    preload() {
        // Load pixel fonts
        this.load.font('PressStart2P', 'fonts/PressStart2P-Regular.ttf');
        this.load.font('PixelOperatorMono', 'fonts/PixelOperatorMono.ttf');
        this.load.font('PixelOperatorMonoBold', 'fonts/PixelOperatorMono-Bold.ttf');

        // Load default sprites
        this.load.image("background", "assets/background-grid.png");
        this.load.image("tile", "assets/single-tile.png");
        this.load.image("npc-tile", "assets/npc-tile.png");
        this.load.image("transporter", "assets/transporter.png");
        this.load.image("object-tile", "assets/object-tile.png");

        // Load config first
        this.load.json("config", "config.json");

        // When config loads, dynamically load sprite frames for animations
        this.load.once('filecomplete-json-config', (key, type, data) => {
            const spriteMetadata = data.spriteMetadata || {};

            // For each sprite with multiple frames, load animation frames
            for (const [spriteKey, metadata] of Object.entries(spriteMetadata)) {
                const frameCount = metadata.frameCount || 1;
                const isSpriteSheet = metadata.spriteSheet === true;

                // Check if this sprite uses a sprite sheet (single PNG with multiple frames)
                if (isSpriteSheet) {
                    // Load sprite sheet
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

                    this.load.spritesheet(spriteKey, spritePath, frameConfig);
                }
                // Multiple frames as separate images
                else if (frameCount > 1) {
                    // Load each frame from assets/sprites/ folder
                    for (let i = 0; i < frameCount; i++) {
                        const framePath = `assets/sprites/${spriteKey}_frame_${i}.png`;
                        this.load.image(`${spriteKey}_frame_${i}`, framePath);
                    }
                }
                // Single frame sprite
                else {
                    const spritePath = `assets/sprites/${spriteKey}.png`;
                    // Only load if not already loaded from assets/
                    if (!this.textures.exists(spriteKey)) {
                        this.load.image(spriteKey, spritePath);
                    }
                }
            }
        });
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

        // Store sprite metadata for later use
        this.spriteMetadata = this.config.spriteMetadata || {};

        // Store object types for later use
        this.objectTypes = this.config.objectTypes || {};

        // Apply player's directional sprites if defined
        if (this.config.player.directionalSprites) {
            const playerSpriteKey = this.config.player.sprite;
            if (this.spriteMetadata[playerSpriteKey]) {
                // Update the player sprite metadata with directional sprites
                this.spriteMetadata[playerSpriteKey].isDirectional = true;
                this.spriteMetadata[playerSpriteKey].directions = this.config.player.directionalSprites;

                // Apply auto-flip settings if defined
                if (this.config.player.autoFlip) {
                    this.spriteMetadata[playerSpriteKey].autoFlip = this.config.player.autoFlip;
                }
            }
        }

        // Debug: log loaded sprite metadata
        console.log('Loaded sprite metadata:', this.spriteMetadata);

        // Create animations from sprite metadata
        this.createAnimations();

        // Room system (will be initialized after centerGrid is calculated)
        this.currentRoom = this.config.player.startRoom;
        this.transporterSprites = [];
        this.objectSprites = [];
        this.floorSprites = [];
        this.isTransitioning = false;
        this.creditsVisible = false;
        this.creditsCloseCallback = null;

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
        bg.setDepth(-10); // Lowest depth - below floor tiles

        // Calculate center coordinates
        const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        // Initialize rooms from config
        this.rooms = {};
        for (let roomKey in this.config.rooms) {
            const roomConfig = this.config.rooms[roomKey];

            // Set up boundary polygon (default to world bounds if not specified)
            let boundary;
            if (roomConfig.boundary && roomConfig.boundary.length >= 3) {
                boundary = roomConfig.boundary;
            } else {
                // Default rectangular boundary matching world bounds
                boundary = [
                    [0, 0],
                    [maxGridX, 0],
                    [maxGridX, maxGridY],
                    [0, maxGridY]
                ];
            }

            this.rooms[roomKey] = {
                name: roomConfig.name,
                boundary: boundary,
                npcs: [],
                objects: roomConfig.objects.map(obj => ({
                    type: obj.type || 'box', // Default to 'box' if no type specified
                    gridX: obj.gridX !== null ? obj.gridX : centerGridX + obj.gridOffsetX,
                    gridY: obj.gridY !== null ? obj.gridY : centerGridY + obj.gridOffsetY
                })),
                transporters: roomConfig.transporters.map(trans => ({
                    gridX: trans.gridX !== null ? trans.gridX : centerGridX + trans.gridOffsetX,
                    gridY: trans.gridY !== null ? trans.gridY : centerGridY + trans.gridOffsetY,
                    targetRoom: trans.targetRoom,
                    targetX: trans.targetX !== null ? trans.targetX : centerGridX + trans.targetOffsetX,
                    targetY: trans.targetY !== null ? trans.targetY : centerGridY + trans.targetOffsetY
                })),
                floor: roomConfig.floor || {} // Floor tiles
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

                // Apply NPC's directional sprites if defined
                if (npcConfig.directionalSprites && this.spriteMetadata[npcConfig.sprite]) {
                    this.spriteMetadata[npcConfig.sprite].isDirectional = true;
                    this.spriteMetadata[npcConfig.sprite].directions = npcConfig.directionalSprites;

                    // Apply auto-flip settings if defined
                    if (npcConfig.autoFlip) {
                        this.spriteMetadata[npcConfig.sprite].autoFlip = npcConfig.autoFlip;
                    }
                }

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

        // Load current room transporters, objects, and floor tiles
        this.loadRoomTransporters();
        this.loadRoomObjects();
        this.loadRoomFloorTiles();

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
                fontSize: '16px',
                fill: '#ffffff',
                fontFamily: 'PressStart2P'
            }
        );
        this.hudText.setOrigin(0, 0.5);
        this.hudText.setScrollFactor(0);
        this.hudText.setDepth(1001);
        this.hudText.setResolution(1);

        // Menu button (right aligned)
        this.menuButton = this.add.text(
            this.cameras.main.width - 10,
            hudHeight / 2,
            'menu',
            {
                fontSize: '16px',
                fill: '#ffffff',
                fontFamily: 'PressStart2P'
            }
        );
        this.menuButton.setOrigin(1, 0.5);
        this.menuButton.setScrollFactor(0);
        this.menuButton.setDepth(1001);
        this.menuButton.setResolution(1);
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
        // Create overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.85);
        overlay.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);
        overlay.setScrollFactor(0);
        overlay.setDepth(2000);
        overlay.setInteractive(
            new Phaser.Geom.Rectangle(0, 0, this.cameras.main.width, this.cameras.main.height),
            Phaser.Geom.Rectangle.Contains
        );

        // Create panel
        const panelWidth = 400;
        const panelHeight = 300;
        const panelX = (this.cameras.main.width - panelWidth) / 2;
        const panelY = (this.cameras.main.height - panelHeight) / 2;

        const panel = this.add.graphics();
        panel.fillStyle(0x1a1a1a, 1);
        panel.fillRect(panelX, panelY, panelWidth, panelHeight);
        panel.lineStyle(2, 0x666666, 1);
        panel.strokeRect(panelX, panelY, panelWidth, panelHeight);
        panel.setScrollFactor(0);
        panel.setDepth(2001);

        // Title
        const title = this.add.text(
            this.cameras.main.width / 2,
            panelY + 30,
            'CREDITS',
            {
                fontSize: '32px',
                fill: '#ffffff',
                fontFamily: 'PixelOperatorMonoBold'
            }
        );
        title.setOrigin(0.5, 0.5);
        title.setResolution(1);
        title.setScrollFactor(0);
        title.setDepth(2002);

        // Credits content
        const startY = panelY + 80;
        const lineHeight = 24;

        const creditsTexts = this.config.credits.map((line, index) => {
            const text = this.add.text(
                this.cameras.main.width / 2,
                startY + (index * lineHeight),
                line,
                {
                    fontSize: '24px',
                    fill: '#ffffff',
                    fontFamily: index === 0 ? 'PixelOperatorMono' : 'PixelOperatorMonoBold'
                }
            );
            text.setOrigin(0.5, 0.5);
            text.setResolution(1);
            text.setScrollFactor(0);
            text.setDepth(2002);
            return text;
        });

        // Close on click or ESC
        const closeCredits = () => {
            this.creditsVisible = false;
            this.creditsCloseCallback = null;
            overlay.destroy();
            panel.destroy();
            title.destroy();
            creditsTexts.forEach(text => text.destroy());
        };

        this.creditsVisible = true;
        this.creditsCloseCallback = closeCredits;

        overlay.on('pointerdown', closeCredits);
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
                    fontSize: '16px',
                    fill: '#00ff00',
                    fontFamily: 'PixelOperatorMonoBold',
                    backgroundColor: '#000000'
                }
            );
            label.setOrigin(0.5, 1);
            label.setDepth(10);
            label.setResolution(1);
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

                // Get sprite key from object type
                const objType = this.objectTypes[obj.type];
                const spriteKey = objType ? objType.sprite : 'object-tile';

                const sprite = this.add.sprite(pixelX, pixelY, spriteKey);
                sprite.setDepth(0); // Above background, below characters
                this.objectSprites.push(sprite);

                // Store grid position and type on sprite for collision detection
                sprite.gridX = obj.gridX;
                sprite.gridY = obj.gridY;
                sprite.objectType = obj.type;
            });
        }
    }

    loadRoomFloorTiles() {
        // Clear existing floor sprites
        this.floorSprites.forEach(sprite => sprite.destroy());
        this.floorSprites = [];

        // Create floor tile sprites for current room
        const room = this.rooms[this.currentRoom];
        if (room.floor) {
            for (const [key, spriteKey] of Object.entries(room.floor)) {
                const [gridX, gridY] = key.split(',').map(Number);
                const pixelX = gridX * this.GRID_SIZE + this.GRID_SIZE / 2;
                const pixelY = gridY * this.GRID_SIZE + this.GRID_SIZE / 2;

                // Check if the sprite texture exists
                if (!this.textures.exists(spriteKey)) {
                    console.warn(`Floor sprite not found: ${spriteKey}, using fallback`);
                    // Use a fallback sprite if the requested one doesn't exist
                    const fallbackKey = this.textures.exists('object-tile') ? 'object-tile' : 'tile';
                    if (this.textures.exists(fallbackKey)) {
                        const sprite = this.add.sprite(pixelX, pixelY, fallbackKey);
                        sprite.setDepth(-1);
                        sprite.setAlpha(0.5);
                        sprite.setTint(0x88ff88); // Green tint to indicate missing sprite
                        this.floorSprites.push(sprite);
                    }
                    continue;
                }

                const sprite = this.add.sprite(pixelX, pixelY, spriteKey);
                sprite.setDepth(-5); // Above background (-10), below objects (0)
                this.floorSprites.push(sprite);
            }
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

            // Load new room transporters, objects, and floor tiles
            this.loadRoomTransporters();
            this.loadRoomObjects();
            this.loadRoomFloorTiles();

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

        // If credits are visible, handle ESC to close
        if (this.creditsVisible) {
            const escPressed = this.escKey.isDown && !this.lastKeyState.esc;
            if (escPressed && this.creditsCloseCallback) {
                this.creditsCloseCallback();
            }
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
                fontSize: '16px',
                fill: '#ffffff',
                fontFamily: 'PixelOperatorMonoBold',
                backgroundColor: '#000000'
            }
        );
        label.setOrigin(0.5, 1);
        label.setDepth(10);
        label.setResolution(1);

        // Store label reference on NPC
        npc.nameLabel = label;

        return npc;
    }

    // Point-in-polygon test using ray casting algorithm
    isPointInPolygon(x, y, polygon) {
        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const xi = polygon[i][0];
            const yi = polygon[i][1];
            const xj = polygon[j][0];
            const yj = polygon[j][1];

            const intersect = ((yi > y) !== (yj > y)) &&
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    // Check if position is within room boundary
    checkBoundary(gridX, gridY) {
        const room = this.rooms[this.currentRoom];
        if (!room || !room.boundary) {
            return true; // No boundary defined, allow movement
        }

        // Check if cell center is within polygon
        // Cell center is at (gridX + 0.5, gridY + 0.5) in continuous grid coordinates
        return this.isPointInPolygon(gridX + 0.5, gridY + 0.5, room.boundary);
    }

    // Collision detection
    checkCollision(character, targetGridX, targetGridY, fromGridX, fromGridY) {
        const deltaX = targetGridX - fromGridX;
        const deltaY = targetGridY - fromGridY;
        const isDiagonal = deltaX !== 0 && deltaY !== 0;

        // Cells to check for collision
        const cellsToCheck = [{ x: targetGridX, y: targetGridY }];

        // First check if target position is within room boundary
        if (!this.checkBoundary(targetGridX, targetGridY)) {
            return false; // Target is outside boundary
        }

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

        // Check that all cells in path are within boundary
        for (let cell of cellsToCheck) {
            if (!this.checkBoundary(cell.x, cell.y)) {
                return false; // Path crosses boundary
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

    // Get sprite configuration (scale and anchor) from metadata
    getSpriteConfig(spriteKey) {
        const metadata = this.spriteMetadata[spriteKey];

        // Debug log
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

    // Get the sprite key for a specific direction
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

    // Get flip information for directional sprites
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

    // Create Phaser animations from sprite metadata
    createAnimations() {
        for (const [spriteKey, metadata] of Object.entries(this.spriteMetadata)) {
            const frameCount = metadata.frameCount || 1;
            const isSpriteSheet = metadata.spriteSheet === true;

            // Only create animation if there are multiple frames
            if (frameCount > 1) {
                const animKey = spriteKey + '_anim';

                // Don't recreate if animation already exists
                if (this.anims.exists(animKey)) {
                    continue;
                }

                let frames = [];

                // Handle sprite sheet frames
                if (isSpriteSheet && this.textures.exists(spriteKey)) {
                    // Use Phaser's sprite sheet frame numbers
                    const startFrame = metadata.startFrame || 0;
                    const endFrame = metadata.endFrame !== null && metadata.endFrame !== undefined
                        ? metadata.endFrame
                        : frameCount - 1;

                    frames = this.anims.generateFrameNumbers(spriteKey, {
                        start: startFrame,
                        end: endFrame
                    });
                }
                // Handle separate frame images
                else {
                    for (let i = 0; i < frameCount; i++) {
                        const frameKey = `${spriteKey}_frame_${i}`;
                        if (this.textures.exists(frameKey)) {
                            frames.push({ key: frameKey });
                        }
                    }
                }

                // Only create animation if we have frames
                if (frames.length > 0) {
                    this.anims.create({
                        key: animKey,
                        frames: frames,
                        frameRate: metadata.frameRate || 10,
                        repeat: metadata.loop !== false ? -1 : 0 // -1 = loop forever, 0 = play once
                    });
                }
            }
        }
    }
}
