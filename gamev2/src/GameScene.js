/**
 * GameScene - Main game scene managing the game world
 */
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

        // Load config with cache-busting
        this.load.json("config", `config.json?t=${Date.now()}`);

        // Dynamically load sprite frames for animations when config loads
        this.load.once('filecomplete-json-config', (key, type, data) => {
            const spriteMetadata = data.spriteMetadata || {};

            // Initialize sprite system early for asset loading
            const tempSpriteSystem = {
                scene: this,
                loadSpriteAssets: SpriteSystem.prototype.loadSpriteAssets
            };

            // Load each sprite's assets
            for (const [spriteKey, metadata] of Object.entries(spriteMetadata)) {
                tempSpriteSystem.loadSpriteAssets.call(tempSpriteSystem, spriteKey, metadata);
            }
        });
    }

    create() {
        try {
            // Load configuration
            this.config = this.cache.json.get('config');

            // Apply game settings from config
            this.GRID_SIZE = this.config.game.gridSize;
            this.WORLD_WIDTH = this.config.game.worldWidth;
            this.WORLD_HEIGHT = this.config.game.worldHeight;
            this.DEADZONE_CELLS = this.config.game.deadzoneCells;
            this.DEADZONE_SIZE = this.DEADZONE_CELLS * this.GRID_SIZE;
            this.MOVE_DURATION = this.config.game.moveDuration;
            this.objectTypes = this.config.objectTypes || {};

            // Initialize systems
            this.spriteSystem = new SpriteSystem(this);
            this.spriteSystem.initialize(this.config);
            this.spriteSystem.createAnimations();

            this.roomManager = new RoomManager(this);
            this.collisionSystem = new CollisionSystem(this);
            this.npcManager = new NPCManager(this);
            this.inputHandler = new InputHandler(this);

            // Credits state
            this.creditsVisible = false;
            this.creditsCloseCallback = null;

            // Calculate grid boundaries
            const minGridX = 0;
            const maxGridX = (this.WORLD_WIDTH / this.GRID_SIZE) - 1;
            const minGridY = 0;
            const maxGridY = (this.WORLD_HEIGHT / this.GRID_SIZE) - 1;

            // Set world bounds
            this.physics.world.setBounds(0, 0, this.WORLD_WIDTH, this.WORLD_HEIGHT);

            // Add background
            const bg = this.add.image(0, 0, 'background');
            bg.setOrigin(0, 0);
            bg.setDepth(DEPTH.BACKGROUND);

            // Calculate center coordinates
            const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
            const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

            // Initialize rooms
            this.roomManager.initializeRooms(this.config, centerGridX, centerGridY, maxGridX, maxGridY);
            this.roomManager.currentRoom = this.config.player.startRoom;

            // Create player
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

            // Spawn NPCs
            for (let roomKey in this.config.rooms) {
                const roomConfig = this.config.rooms[roomKey];
                roomConfig.npcs.forEach(npcConfig => {
                    const npcGridX = npcConfig.gridX !== null ? npcConfig.gridX : centerGridX + npcConfig.gridOffsetX;
                    const npcGridY = npcConfig.gridY !== null ? npcConfig.gridY : centerGridY + npcConfig.gridOffsetY;

                    const npc = this.npcManager.spawnNPC(npcGridX, npcGridY, npcConfig.sprite, npcConfig.name, {
                        dialogue: npcConfig.dialogue
                    });
                    this.roomManager.rooms[roomKey].npcs.push(npc);
                });
            }

            // Hide NPCs not in starting room
            for (let roomKey in this.roomManager.rooms) {
                if (roomKey !== this.roomManager.currentRoom) {
                    this.roomManager.rooms[roomKey].npcs.forEach(npc => {
                        npc.sprite.setVisible(false);
                        if (npc.nameLabel) npc.nameLabel.setVisible(false);
                    });
                }
            }

            // Load current room content
            this.roomManager.loadTransporters();
            this.roomManager.loadObjects();
            this.roomManager.loadFloorTiles();

            // Set up NPC wandering timer
            this.time.addEvent({
                delay: this.config.game.npcWanderInterval,
                callback: () => this.npcManager.handleWander(),
                callbackScope: this,
                loop: true
            });

            // Set up camera
            this.cameras.main.startFollow(this.player.sprite);
            this.cameras.main.setDeadzone(this.DEADZONE_SIZE, this.DEADZONE_SIZE);
            this.cameras.main.setBackgroundColor(COLORS.CAMERA_BACKGROUND);

            // Set up input
            this.inputHandler.setupKeys();

            // Create managers
            this.menuManager = new MenuManager(this);
            this.dialogueManager = new DialogueManager(this);

            // Create HUD
            this.createHUD();

        } catch (error) {
            console.error('Error creating game scene:', error);
            throw error;
        }
    }

    /**
     * Create the HUD overlay
     */
    createHUD() {
        // Create semi-transparent background bar
        this.hudBackground = this.add.graphics();
        this.hudBackground.fillStyle(COLORS.HUD_BACKGROUND, UI.HUD_ALPHA);
        this.hudBackground.fillRect(0, 0, this.cameras.main.width, UI.HUD_HEIGHT);
        this.hudBackground.setScrollFactor(0);
        this.hudBackground.setDepth(DEPTH.HUD_BACKGROUND);

        // Game info text
        const hudText = `${this.config.game.title} | ${this.roomManager.currentRoom} | ${this.config.game.date}`;

        this.hudText = this.add.text(
            UI.HUD_PADDING,
            UI.HUD_HEIGHT / 2,
            hudText,
            {
                fontSize: FONTS.HUD_SIZE,
                fill: COLORS.HUD_TEXT,
                fontFamily: FONTS.HUD
            }
        );
        this.hudText.setOrigin(0, 0.5);
        this.hudText.setScrollFactor(0);
        this.hudText.setDepth(DEPTH.HUD_TEXT);
        this.hudText.setResolution(1);

        // Menu button (right aligned)
        this.menuButton = this.add.text(
            this.cameras.main.width - UI.HUD_PADDING,
            UI.HUD_HEIGHT / 2,
            'menu',
            {
                fontSize: FONTS.HUD_SIZE,
                fill: COLORS.HUD_TEXT,
                fontFamily: FONTS.HUD
            }
        );
        this.menuButton.setOrigin(1, 0.5);
        this.menuButton.setScrollFactor(0);
        this.menuButton.setDepth(DEPTH.HUD_TEXT);
        this.menuButton.setResolution(1);
        this.menuButton.setInteractive({ useHandCursor: true });
        this.menuButton.on('pointerdown', () => this.menuManager.toggle());
    }

    /**
     * Update HUD text
     */
    updateHUD() {
        const hudText = `${this.config.game.title} | ${this.roomManager.currentRoom} | ${this.config.game.date}`;
        this.hudText.setText(hudText);
    }

    /**
     * Show achievements (placeholder)
     */
    showAchievements() {
        console.log('Achievements feature coming soon!');
    }

    /**
     * Show map (placeholder)
     */
    showMap() {
        console.log('Map feature coming soon!');
    }

    /**
     * Show credits overlay
     */
    showCredits() {
        // Create overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(COLORS.CREDITS_OVERLAY, UI.CREDITS_OVERLAY_ALPHA);
        overlay.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);
        overlay.setScrollFactor(0);
        overlay.setDepth(DEPTH.CREDITS_OVERLAY);
        overlay.setInteractive(
            new Phaser.Geom.Rectangle(0, 0, this.cameras.main.width, this.cameras.main.height),
            Phaser.Geom.Rectangle.Contains
        );

        // Create panel
        const panelX = (this.cameras.main.width - UI.CREDITS_PANEL_WIDTH) / 2;
        const panelY = (this.cameras.main.height - UI.CREDITS_PANEL_HEIGHT) / 2;

        const panel = this.add.graphics();
        panel.fillStyle(COLORS.CREDITS_PANEL, 1);
        panel.fillRect(panelX, panelY, UI.CREDITS_PANEL_WIDTH, UI.CREDITS_PANEL_HEIGHT);
        panel.lineStyle(UI.CREDITS_BORDER_WIDTH, COLORS.CREDITS_BORDER, 1);
        panel.strokeRect(panelX, panelY, UI.CREDITS_PANEL_WIDTH, UI.CREDITS_PANEL_HEIGHT);
        panel.setScrollFactor(0);
        panel.setDepth(DEPTH.CREDITS_PANEL);

        // Title
        const title = this.add.text(
            this.cameras.main.width / 2,
            panelY + 30,
            'CREDITS',
            {
                fontSize: FONTS.CREDITS_TITLE_SIZE,
                fill: COLORS.HUD_TEXT,
                fontFamily: FONTS.CREDITS_TITLE
            }
        );
        title.setOrigin(0.5, 0.5);
        title.setResolution(1);
        title.setScrollFactor(0);
        title.setDepth(DEPTH.CREDITS_TEXT);

        // Credits content
        const startY = panelY + 80;

        const creditsTexts = this.config.credits.map((line, index) => {
            const text = this.add.text(
                this.cameras.main.width / 2,
                startY + (index * UI.CREDITS_LINE_HEIGHT),
                line,
                {
                    fontSize: FONTS.CREDITS_TEXT_SIZE,
                    fill: COLORS.HUD_TEXT,
                    fontFamily: index === 0 ? FONTS.CREDITS_TEXT : FONTS.CREDITS_TEXT_BOLD
                }
            );
            text.setOrigin(0.5, 0.5);
            text.setResolution(1);
            text.setScrollFactor(0);
            text.setDepth(DEPTH.CREDITS_TEXT);
            return text;
        });

        // Close handler
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

    /**
     * Check if player is trying to interact with an NPC
     * @param {number} targetGridX - Target grid X position
     * @param {number} targetGridY - Target grid Y position
     */
    checkNPCInteraction(targetGridX, targetGridY) {
        this.npcManager.checkInteraction(targetGridX, targetGridY);
    }

    /**
     * Check if player is on a transporter
     */
    checkTransporter() {
        const playerPos = this.player.getGridPosition();
        return this.roomManager.checkTransporter(playerPos);
    }

    /**
     * Collision detection wrapper
     * @param {Character} character - Character to check collision for
     * @param {number} targetGridX - Target grid X
     * @param {number} targetGridY - Target grid Y
     * @param {number} fromGridX - Starting grid X
     * @param {number} fromGridY - Starting grid Y
     * @returns {boolean} True if movement is allowed
     */
    checkCollision(character, targetGridX, targetGridY, fromGridX, fromGridY) {
        return this.collisionSystem.checkCollision(character, targetGridX, targetGridY, fromGridX, fromGridY);
    }

    /**
     * Get sprite configuration from sprite system
     * @param {string} spriteKey - Sprite key
     * @returns {Object} Sprite configuration
     */
    getSpriteConfig(spriteKey) {
        return this.spriteSystem.getSpriteConfig(spriteKey);
    }

    /**
     * Get directional sprite key
     * @param {string} baseSpriteKey - Base sprite key
     * @param {string} direction - Direction
     * @returns {string} Directional sprite key
     */
    getDirectionalSpriteKey(baseSpriteKey, direction) {
        return this.spriteSystem.getDirectionalSpriteKey(baseSpriteKey, direction);
    }

    /**
     * Get directional flip information
     * @param {string} baseSpriteKey - Base sprite key
     * @param {string} direction - Direction
     * @returns {Object} Flip info {flipX, flipY}
     */
    getDirectionalFlipInfo(baseSpriteKey, direction) {
        return this.spriteSystem.getDirectionalFlipInfo(baseSpriteKey, direction);
    }

    /**
     * Main update loop
     */
    update() {
        this.inputHandler.handleInput();
        this.npcManager.updateLabels();
    }
}
