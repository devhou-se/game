/**
 * GameScene - Main game scene managing the game world
 */
class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');
    }

    preload() {
        // Drive the HTML loading screen (index.html) with real progress
        this.load.on('progress', (v) => { if (window.updateLoader) window.updateLoader(v); });

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

        // Map screen: world-map.json is the contract (a replaceable overworld
        // image + per-room rects) — regenerate with tools/make_worldmap.py, or
        // ship hand-drawn art and set "custom": true
        this.load.json('worldMap', `assets/map/world-map.json?t=${Date.now()}`);
        this.load.once('filecomplete-json-worldMap', (key, type, data) => {
            if (data.image) this.load.image('world-map', `${data.image}?t=${Date.now()}`);
        });

        // Dynamically load sprite frames for animations when config loads
        this.load.once('filecomplete-json-config', (key, type, data) => {
            // Maps are authored in Tiled: enqueue every room's .tmj (files added
            // during a load event join the same preload pass). ?maps=config skips
            // this and renders the rooms baked into config.json instead.
            if (new URLSearchParams(location.search).get('maps') !== 'config') {
                for (const roomKey of Object.keys(data.rooms || {})) {
                    this.load.json(`tiled-${roomKey}`, `tiled/${roomKey.toLowerCase()}.tmj?t=${Date.now()}`);
                }
            }

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
            // Load configuration (expand the v2 tile-palette format to the
            // runtime "x,y" -> tileKey shape before anything reads it)
            this.config = decodeConfig(this.cache.json.get('config'));

            // Rooms are authored in Tiled (tiled/*.tmj is the map source of truth).
            // TiledAdapter outputs the exact room shape RoomManager renders, so the
            // whole existing renderer + Y-sort + collision is reused unchanged.
            // config.json still owns game settings, NPCs, sprite metadata and
            // achievements, and is the map fallback (?maps=config, or any room
            // whose .tmj failed to load).
            for (const key of Object.keys(this.config.rooms)) {
                if (!this.cache.json.exists(`tiled-${key}`)) continue;
                const built = TiledAdapter.toRoom(this.cache.json.get(`tiled-${key}`));
                const r = this.config.rooms[key];
                r.layers = built.layers;
                if (built.transporters.length) r.transporters = built.transporters;
                if (built.worldWidth) r.worldWidth = built.worldWidth;
                if (built.worldHeight) r.worldHeight = built.worldHeight;
                if (built.boundary) r.boundary = built.boundary;
                console.log(`[tiled] room "${key}" loaded from tiled/${key.toLowerCase()}.tmj — ${built.layers.length} layers, ${built.transporters.length} transporters`);
            }

            // A saved character choice replaces the default player sprite
            // (must happen before SpriteSystem reads config.player)
            CharacterSelect.applySaved(this.config);

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
            this.achievementManager = new AchievementManager(this);

            // Credits state
            this.creditsVisible = false;
            this.creditsCloseCallback = null;
            this.achievementsVisible = false;
            this.achievementsCloseCallback = null;
            this.mapVisible = false;
            this.mapCloseCallback = null;

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

            // Spawn NPCs, resolved to their dated state (states on-or-before
            // the game date apply in order; ?date=YYYY-MM-DD time-travels,
            // default today — see src/utils/NpcStates.js). Also excludes the
            // character the player is playing as.
            this.syncNpcPresence();

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
            // Clamp the camera to the world so it never reveals the black void
            // outside the map at the edges.
            this.cameras.main.setBounds(0, 0, this.WORLD_WIDTH, this.WORLD_HEIGHT);
            this.cameras.main.startFollow(this.player.sprite);
            this.cameras.main.setDeadzone(this.DEADZONE_SIZE, this.DEADZONE_SIZE);
            this.cameras.main.setBackgroundColor(COLORS.CAMERA_BACKGROUND);

            // Size camera/physics/player bounds to the starting room (rooms can differ in size)
            this.applyRoomBounds(this.roomManager.currentRoom);

            // Set up input
            this.inputHandler.setupKeys();

            // Create managers
            this.menuManager = new MenuManager(this);
            this.datePicker = new DatePicker(this);
            this.stationPicker = new StationPicker(this);
            this.trainTravel = new TrainTravel(this);
            this.trainTravel.onRoomChange(this.roomManager.currentRoom);
            this.ambientTrains = new AmbientTrains(this);
            this.dialogueManager = new DialogueManager(this);
            this.shop = new Shop(this);
            this.fishing = new Fishing(this);
            this.characterSelect = new CharacterSelect(this);
            this.dayNight = new DayNight(this);
            this.debugManager = new DebugManager(this);
            this.touchControls = new TouchControls(this); // on-screen d-pad (touch / ?touch=1)

            // Create HUD
            this.createHUD();

            // playable — drop the loading screen
            if (window.hideLoader) window.hideLoader();

        } catch (error) {
            console.error('Error creating game scene:', error);
            if (window.failLoader) window.failLoader();
            throw error;
        }
    }

    /**
     * Create the HUD overlay
     */
    /**
     * Resize camera, physics, and player-movement bounds to a room's own size.
     * Rooms can differ in dimensions, so this is applied on init and every switch.
     */
    applyRoomBounds(roomKey) {
        const room = this.roomManager.rooms[roomKey];
        if (!room) return;
        const ww = room.worldWidth || this.WORLD_WIDTH;
        const wh = room.worldHeight || this.WORLD_HEIGHT;
        this.cameras.main.setBounds(0, 0, ww, wh);
        this.physics.world.setBounds(0, 0, ww, wh);
        if (this.player) {
            this.player.minGridX = 0;
            this.player.minGridY = 0;
            this.player.maxGridX = (ww / this.GRID_SIZE) - 1;
            this.player.maxGridY = (wh / this.GRID_SIZE) - 1;
        }
    }

    /**
     * Spawn/despawn NPCs so the world cast matches the game date AND the
     * player's chosen character: playing as Bailey removes the Bailey NPC
     * entirely — no sprite, no wandering, no collision, no map dot.
     * Idempotent; runs at boot and again after a character switch.
     */
    syncNpcPresence() {
        const npcDate = gameDate();
        const baseOf = (key) => (key || '').replace(/_(front|back|side)$/, '');
        const played = baseOf(this.player.baseSpriteKey);
        const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        for (const roomKey in this.config.rooms) {
            const room = this.roomManager.rooms[roomKey];
            for (const raw of this.config.rooms[roomKey].npcs) {
                const resolved = resolveNpc(raw, npcDate);
                const shouldExist = !!resolved && baseOf(resolved.sprite) !== played;
                const idx = room.npcs.findIndex(n => n.name === raw.name);

                if (shouldExist && idx === -1) {
                    const gx = resolved.gridX !== null ? resolved.gridX : centerGridX + resolved.gridOffsetX;
                    const gy = resolved.gridY !== null ? resolved.gridY : centerGridY + resolved.gridOffsetY;
                    const npc = this.npcManager.spawnNPC(gx, gy, resolved.sprite, resolved.name, {
                        dialogue: resolved.dialogue
                    });
                    const here = roomKey === this.roomManager.currentRoom;
                    npc.sprite.setVisible(here);
                    if (npc.nameLabel) npc.nameLabel.setVisible(here);
                    room.npcs.push(npc);
                } else if (!shouldExist && idx !== -1) {
                    const npc = room.npcs[idx];
                    room.npcs.splice(idx, 1);
                    const ci = this.npcManager.characters.indexOf(npc);
                    if (ci !== -1) this.npcManager.characters.splice(ci, 1);
                    if (npc.nameLabel) npc.nameLabel.destroy();
                    npc.destroy();
                }
            }
        }
    }

    createHUD() {
        // Create semi-transparent background bar
        this.hudBackground = this.add.graphics();
        this.hudBackground.fillStyle(COLORS.HUD_BACKGROUND, UI.HUD_ALPHA);
        this.hudBackground.fillRect(0, 0, this.cameras.main.width, UI.HUD_HEIGHT);
        this.hudBackground.setScrollFactor(0);
        this.hudBackground.setDepth(DEPTH.HUD_BACKGROUND);

        // Game info text; the date segment is the LIVE game date (today, or
        // ?date=YYYY-MM-DD) and clicking it opens a date picker — NPC states
        // re-resolve to the picked date on reload.
        const hudText = `${this.config.game.title} | ${this.roomManager.currentRoom} | `;

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

        this.hudDateText = this.add.text(
            UI.HUD_PADDING + this.hudText.width,
            UI.HUD_HEIGHT / 2,
            formatGameDate(gameDate()),
            {
                fontSize: FONTS.HUD_SIZE,
                fill: COLORS.HUD_TEXT,
                fontFamily: FONTS.HUD
            }
        );
        this.hudDateText.setOrigin(0, 0.5);
        this.hudDateText.setScrollFactor(0);
        this.hudDateText.setDepth(DEPTH.HUD_TEXT);
        this.hudDateText.setResolution(1);
        this.hudDateText.setInteractive({ useHandCursor: true });
        this.hudDateText.on('pointerdown', () => this.datePicker.show());

        // Wallet (issue #12) — gold, after the date; clicking it opens the items screen
        this.hudMoneyText = this.add.text(
            UI.HUD_PADDING + this.hudText.width + this.hudDateText.width,
            UI.HUD_HEIGHT / 2,
            ` | ${this.shop.fmt(this.shop.money)}`,
            {
                fontSize: FONTS.HUD_SIZE,
                fill: '#ffd700',
                fontFamily: FONTS.HUD
            }
        );
        this.hudMoneyText.setOrigin(0, 0.5);
        this.hudMoneyText.setScrollFactor(0);
        this.hudMoneyText.setDepth(DEPTH.HUD_TEXT);
        this.hudMoneyText.setResolution(1);
        this.hudMoneyText.setInteractive({ useHandCursor: true });
        this.hudMoneyText.on('pointerdown', () => this.shop.showInventory());

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
        const hudText = `${this.config.game.title} | ${this.roomManager.currentRoom} | `;
        this.hudText.setText(hudText);
        this.hudDateText.setText(formatGameDate(gameDate()));
        this.hudDateText.setX(UI.HUD_PADDING + this.hudText.width);
        if (this.hudMoneyText) {
            this.hudMoneyText.setText(` | ${this.shop.fmt(this.shop.money)}`);
            this.hudMoneyText.setX(UI.HUD_PADDING + this.hudText.width + this.hudDateText.width);
        }
    }

    /**
     * Show the achievements overlay (first achievement: "Paint the Board").
     */
    showAchievements() {
        if (this.achievementsVisible) return;   // only one overlay at a time
        const cam = this.cameras.main, W = cam.width, H = cam.height;
        const pw = 560, ph = 260, px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = [];
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.85); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        objs.push(overlay);
        const panel = this.add.graphics();
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001); objs.push(panel);
        const text = (x, y, t, size, bold, color, origin) => {
            const o = this.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(origin != null ? origin : 0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };
        const cx = W / 2;
        text(cx, py + 34, 'ACHIEVEMENTS', '32px', true);
        const p = this.achievementManager.paintProgress();
        text(cx, py + 88, (p.complete ? '★ ' : '') + 'Paint the Board', '24px', true, p.complete ? '#ffd700' : '#ffffff');
        text(cx, py + 118, 'Step on every reachable tile in the world', '18px', false, '#bbbbbb');
        const barW = pw - 80, barX = px + 40, barY = py + 142, barH = 26;
        const bar = this.add.graphics(); bar.setScrollFactor(0); bar.setDepth(2002);
        bar.fillStyle(0x333333, 1); bar.fillRect(barX, barY, barW, barH);
        bar.fillStyle(p.complete ? 0xffd700 : 0x33cc66, 1);
        bar.fillRect(barX, barY, barW * (p.total ? Math.min(1, p.painted / p.total) : 0), barH);
        bar.lineStyle(2, 0x666666, 1); bar.strokeRect(barX, barY, barW, barH);
        objs.push(bar);
        text(cx, barY + barH + 22, `${p.percent}% painted`, '20px', true);
        text(cx, py + ph - 26, '(click or ESC to close)', '16px', false, '#888888');
        const close = () => {
            this.achievementsVisible = false;
            this.achievementsCloseCallback = null;
            objs.forEach(o => o.destroy());
        };
        this.achievementsVisible = true;
        this.achievementsCloseCallback = close;
        overlay.on('pointerdown', close);
    }

    /**
     * Show map (placeholder)
     */
    /**
     * Nearest walkable cell to (gx, gy) in a room (spiral search): must have
     * floor, no collider, inside bounds, and not sit on a transporter (that
     * would immediately teleport the arriving player).
     */
    findWalkableNear(roomName, gx, gy) {
        const r = this.config.rooms[roomName];
        const cellsW = Math.round((r.worldWidth || this.config.game.worldWidth) / this.GRID_SIZE);
        const cellsH = Math.round((r.worldHeight || this.config.game.worldHeight) / this.GRID_SIZE);
        const blocked = new Set(), floored = new Set();
        for (const L of r.layers) {
            const target = L.collision ? blocked : (L.name === 'Floor' ? floored : null);
            if (target) for (const xy in L.tiles) target.add(xy);
        }
        const portals = new Set((r.transporters || []).map(t => `${t.gridX},${t.gridY}`));
        const ok = (x, y) => x >= 0 && x < cellsW && y >= 0 && y < cellsH &&
            floored.has(`${x},${y}`) && !blocked.has(`${x},${y}`) && !portals.has(`${x},${y}`);
        for (let rad = 0; rad <= 8; rad++) {
            for (let dx = -rad; dx <= rad; dx++) {
                for (let dy = -rad; dy <= rad; dy++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) !== rad) continue;
                    if (ok(gx + dx, gy + dy)) return [gx + dx, gy + dy];
                }
            }
        }
        return null;
    }

    showMap() {
        if (this.mapVisible) return;   // only one overlay at a time
        const meta = this.cache.json.get('worldMap');
        if (!meta || !meta.rooms || !this.textures.exists('world-map')) {
            console.warn('world map assets missing — run tools/make_worldmap.py');
            return;
        }
        const cam = this.cameras.main, W = cam.width, H = cam.height;
        const objs = [];

        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.85); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        objs.push(overlay);

        // fit the overworld into the viewport (never upscale past 1:1)
        const s = Math.min((W - 120) / meta.width, (H - 170) / meta.height, 1);
        const dw = meta.width * s, dh = meta.height * s;
        const px = (W - dw) / 2, py = (H - dh) / 2 + 14;

        const img = this.add.image(px, py, 'world-map');
        img.setOrigin(0, 0); img.setDisplaySize(dw, dh);
        img.setScrollFactor(0); img.setDepth(2001); objs.push(img);
        const frame = this.add.graphics();
        frame.lineStyle(2, 0x666666, 1); frame.strokeRect(px, py, dw, dh);
        frame.setScrollFactor(0); frame.setDepth(2002); objs.push(frame);

        // click a spot on the map to travel there (nearest walkable cell)
        img.setInteractive({ useHandCursor: true });
        img.on('pointerdown', (pointer) => {
            const ix = (pointer.x - px) / s, iy = (pointer.y - py) / s;  // image px
            for (const name in meta.rooms) {
                const r = meta.rooms[name];
                if (ix < r.x || ix >= r.x + r.w || iy < r.y || iy >= r.y + r.h) continue;
                const gx = Math.floor((ix - r.x) / (r.w / r.cells[0]));
                const gy = Math.floor((iy - r.y) / (r.h / r.cells[1]));
                const cell = this.findWalkableNear(name, gx, gy);
                if (cell) {
                    close();
                    this.roomManager.switchRoom(name, cell[0], cell[1]);
                }
                return;  // clicked inside a room (even if no landing found)
            }
        });

        const text = (x, y, t, size, bold, color, bg) => {
            const o = this.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono',
                backgroundColor: bg });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2003); objs.push(o); return o;
        };
        text(W / 2, py - 24, 'MAP', '26px', true);

        // labels dodge each other: try offsets around the anchor until the
        // label's bounds don't intersect anything already placed
        const placed = [];
        const placeLabel = (x, y, t, size, bold, color) => {
            const o = text(x, y, t, size, bold, color, 'rgba(0,0,0,0.65)');
            const tries = [[0, 0], [0, -16], [0, 16], [22, 0], [-22, 0],
                           [0, -32], [0, 32], [26, -16], [-26, -16], [26, 16], [-26, 16]];
            for (const [dx, dy] of tries) {
                o.setPosition(x + dx, y + dy);
                const b = o.getBounds();
                if (!placed.some(p => Phaser.Geom.Rectangle.Overlaps(p, b))) break;
            }
            placed.push(o.getBounds());
            return o;
        };

        // grid cell -> screen, through the room's OWN rect (so replacement
        // map art doesn't need to be to scale — each room maps independently)
        const cellToMap = (r, gx, gy) => [
            px + (r.x + (gx + 0.5) * (r.w / r.cells[0])) * s,
            py + (r.y + (gy + 0.5) * (r.h / r.cells[1])) * s,
        ];
        const mkDot = (mx, my, color, radius) => {
            const dot = this.add.graphics();
            dot.fillStyle(color, 1); dot.fillCircle(0, 0, radius);
            dot.lineStyle(2, 0x000000, 1); dot.strokeCircle(0, 0, radius);
            dot.setPosition(mx, my); dot.setScrollFactor(0); dot.setDepth(2004);
            objs.push(dot); return dot;
        };

        // an interior isn't ON the map — the player is marked at its entrance
        // (where the interior's exit transporter lands in the overworld)
        const here = this.roomManager.currentRoom;
        let markRoom = meta.rooms[here] && here;
        let markX = this.player.gridX, markY = this.player.gridY;
        if (!markRoom) {
            const exit = (this.config.rooms[here].transporters || [])
                .find(t => meta.rooms[t.targetRoom]);
            if (exit) { markRoom = exit.targetRoom; markX = exit.targetX; markY = exit.targetY; }
        }

        // room labels (current/containing room in gold)
        for (const name in meta.rooms) {
            const r = meta.rooms[name];
            placeLabel(px + (r.x + r.w / 2) * s, py + (r.y + r.h / 2) * s,
                       name, '18px', true, name === markRoom ? '#ffd700' : '#ffffff');
        }

        // every NPC in overworld rooms, at their live (dated, wandering) position
        for (const roomName in meta.rooms) {
            const rRoom = this.roomManager.rooms[roomName];
            if (!rRoom) continue;
            for (const npc of rRoom.npcs) {
                const [mx, my] = cellToMap(meta.rooms[roomName], npc.gridX, npc.gridY);
                mkDot(mx, my, 0x66bbff, 4);
                placeLabel(mx, my - 15, npc.name, '14px', false, '#aaddff');
            }
        }

        // "you are here" — gold pulsing dot
        let footer = `you are here: ${here}`;
        if (markRoom) {
            const [mx, my] = cellToMap(meta.rooms[markRoom], markX, markY);
            const dot = mkDot(mx, my, 0xffd700, 6);
            placeLabel(mx, my - 16, 'You', '14px', true, '#ffd700');
            const pulse = this.tweens.add({ targets: dot, scale: 1.6, duration: 500,
                                            yoyo: true, repeat: -1 });
            objs.push({ destroy: () => pulse.stop() });
            if (markRoom !== here) footer = `you are here: ${here} (in ${markRoom})`;
        }
        text(W / 2, py + dh + 20, `${footer}   ·   click a spot to travel there   ·   ESC to close`, '13px', false, '#bbbbbb');

        const close = () => {
            this.mapVisible = false;
            this.mapCloseCallback = null;
            objs.forEach(o => o.destroy());
        };
        this.mapVisible = true;
        this.mapCloseCallback = close;
        overlay.on('pointerdown', close);
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
        // bumping a vending machine / konbini counter opens its store
        if (this.shop && !this.dialogueManager.isVisible()) {
            this.shop.checkShopInteraction(targetGridX, targetGridY);
        }
        // bumping pond water casts a line (the fishing mini game)
        if (this.fishing && !this.dialogueManager.isVisible() && !this.shop.isVisible()) {
            this.fishing.checkStart(targetGridX, targetGridY);
        }
        // bumping a wall clock or calendar opens the time-travel picker
        if (!this.dialogueManager.isVisible() && !this.shop.isVisible() &&
            this.datePicker && !this.datePicker.isVisible()) {
            const room = this.roomManager.rooms[this.roomManager.currentRoom];
            const xy = `${targetGridX},${targetGridY}`;
            for (const layer of (room.layers || [])) {
                const key = (layer.tiles || {})[xy];
                if (key && /^(office-clock|office-poster-menu)/.test(key)) {
                    this.datePicker.show();
                    break;
                }
            }
        }
    }

    /**
     * Check if player is on a transporter
     */
    checkTransporter() {
        const playerPos = this.player.getGridPosition();
        if (this.roomManager.checkTransporter(playerPos)) return true;
        // walking up to the train (a board cell in a station) opens departures —
        // but never mid-ride (e.g. while the player is stepping off at arrival)
        const st = (this.config.stations || {})[this.roomManager.currentRoom];
        if (st && this.stationPicker && !(this.trainTravel && this.trainTravel.riding) &&
            st.board.some(([bx, by]) => bx === playerPos.x && by === playerPos.y)) {
            this.stationPicker.show(this.roomManager.currentRoom);
        }
        return false;
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
        // stop walk cycles on characters that didn't chain another step this
        // frame (player's own depth/anim are left to TrainTravel while riding)
        if (this.player && !(this.trainTravel && this.trainTravel.riding)) {
            this.player.settleIdle();
        }
        this.roomManager.rooms[this.roomManager.currentRoom].npcs.forEach(npc => npc.settleIdle());
        this.npcManager.updateLabels();
        this.updateCharacterDepths();
        if (this.debugManager) this.debugManager.update();
        // Achievement "Paint the board": record the tile the player stands on.
        if (this.player && this.achievementManager) {
            const k = this.player.gridX + ',' + this.player.gridY;
            if (this._paintCell !== k) {
                this._paintCell = k;
                this.achievementManager.markVisited(this.roomManager.currentRoom, this.player.gridX, this.player.gridY);
            }
        }
    }

    /**
     * Y-sort the player and NPCs by their feet position so they render in
     * front of objects below them and behind objects above them. Matches the
     * feet-based depth used for standing tiles in RoomManager.loadLayer.
     */
    updateCharacterDepths() {
        const GS = this.GRID_SIZE;
        const feetDepth = (sprite) => ((sprite.y + GS / 2) / GS) * 10 + 5;
        // While riding, TrainTravel owns the player's depth (it renders him in the
        // train doorway, above the train, as he steps off) — don't sink him back.
        if (this.player && !(this.trainTravel && this.trainTravel.riding))
            this.player.sprite.setDepth(feetDepth(this.player.sprite));
        const npcs = this.roomManager.rooms[this.roomManager.currentRoom].npcs;
        npcs.forEach(npc => npc.sprite.setDepth(feetDepth(npc.sprite)));
    }
}
