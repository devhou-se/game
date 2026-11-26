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
        // Japanese glyphs for all three (2 MB, so fetched after boot, not in this queue)
        this.load.once('complete', () => JapaneseFont.load(this.game));

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

        // Advertisement signage (issue #26): the generated ad pool that
        // RoomManager.placeSignage mounts on building walls — regenerate
        // with tools/generate_ads.py
        this.load.json('adsManifest', `assets/ads/manifest.json?t=${Date.now()}`);
        this.load.once('filecomplete-json-adsManifest', (key, type, data) => {
            for (const ad of (data.ads || [])) this.load.image(ad.key, `assets/ads/${ad.file}`);
        });

        // Item icon art (issue #82): a PNG listed here replaces the icon
        // ItemIcons would otherwise draw — see assets/items/README.md
        this.load.json('itemIconManifest', `assets/items/manifest.json?t=${Date.now()}`);
        this.load.once('filecomplete-json-itemIconManifest', (key, type, data) => {
            const ids = Array.isArray(data && data.icons) ? data.icons : [];
            for (const id of ids) {
                if (typeof id === 'string' && /^[\w-]+$/.test(id)) this.load.image(`item-${id}`, `assets/items/${id}.png?t=${Date.now()}`);
            }
        });

        // Hand-drawn character portraits (issue #9): only the names listed in
        // the manifest are requested, so a character without art never 404s.
        // Dialogue and the title screen use `portrait-<name>` when it exists
        // and fall back to the character's sprite — see assets/portraits/README.md
        this.load.json('portraitManifest', `assets/portraits/manifest.json?t=${Date.now()}`);
        this.load.once('filecomplete-json-portraitManifest', (key, type, data) => {
            // tolerate a hand-edited manifest that isn't { "portraits": [names] }
            const names = Array.isArray(data && data.portraits) ? data.portraits : [];
            const t = Date.now(); // replaced art must not be served stale
            for (const name of names) {
                if (typeof name !== 'string' || !/^[\w-]+$/.test(name)) continue;
                this.load.image(`portrait-${name}`, `assets/portraits/${name}.png?t=${t}`);
            }
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

            // Blog-post photos: dated NPC states may carry "photo": <post id>
            // (written by tools/blog_to_npc.py alongside assets/photos/<id>.png);
            // the dialogue box hangs the photo in a frame next to the author
            const photoIds = new Set();
            for (const room of Object.values(data.rooms || {})) {
                for (const npc of room.npcs || []) {
                    if (npc.photo) photoIds.add(npc.photo);
                    for (const st of Object.values(npc.states || {})) {
                        if (st.photo) photoIds.add(st.photo);
                    }
                }
            }
            for (const id of photoIds) {
                this.load.image(`photo-${id}`, `assets/photos/${id}.png`);
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
            setTripDates(this.config);   // content days + config.trips: the default game date, NPC scoping

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
            CharacterCreator.applySaved(this.config);

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
            // a saved custom character's recoloured frames must exist before
            // createAnimations builds the custom walk cycles from them
            CharacterCreator.buildSavedTextures(this);
            this.spriteSystem.createAnimations();

            this.roomManager = new RoomManager(this);
            this.collisionSystem = new CollisionSystem(this);
            this.occlusion = new Occlusion(this);   // scenery fades when someone is behind it
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

            // Cities (issues #40/#41): the districts listed in config `cities`
            // are stitched into ONE continuous room (?stitch=0 keeps them
            // apart). Everything that names a district — the start position
            // here, NPC homes, door targets — goes through roomManager.resolve
            this.roomManager.setupCities(this.config, this.cache.json.get('worldMap'));
            this.achievementManager.computeReachable();

            // where the game date's trip starts a player (see startPosition:
            // beside the cast, new player or not): a district cell, like a
            // door target, so through resolve
            this.newPlayer = Intro.isNewPlayer();
            this.bootStart = this.startPosition();
            const start = this.roomManager.resolve(this.bootStart.room, this.bootStart.x, this.bootStart.y);
            this.roomManager.currentRoom = start.room;

            // Create player
            const playerStartX = start.x;
            const playerStartY = start.y;

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
            // default today or its trip day — see src/utils/NpcStates.js). Also excludes the
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
            this.voice = new Voice();   // spoken dialogue + the shared mute setting
            this.menuManager = new MenuManager(this);
            this.datePicker = new DatePicker(this);
            this.stationPicker = new StationPicker(this);
            this.trainTravel = new TrainTravel(this);
            this.trainTravel.onRoomChange(this.roomManager.currentRoom);
            this.ambientTrains = new AmbientTrains(this);
            this.ambientBoats = new AmbientBoats(this);
            this.trafficLights = new TrafficLights(this);   // decorative signal cycle
            this.dialogueManager = new DialogueManager(this);
            this.shop = new Shop(this);
            this.fishing = new Fishing(this);
            this.drinkingGame = new DrinkingGame(this);
            this.characterSelect = new CharacterSelect(this);
            this.characterCreator = new CharacterCreator(this);
            this.titleScreen = new TitleScreen(this);
            this.intro = new Intro(this);
            this.dayNight = new DayNight(this);
            this.debugManager = new DebugManager(this);
            this.touchControls = new TouchControls(this); // on-screen d-pad (touch / ?touch=1)
            this.uiScale = new UIScale(this); // magnifies overlays on small viewports
            this.rotatePrompt = new RotatePrompt(this); // "rotate your phone", briefly, on a portrait phone
            this.landmarkView = new LandmarkView(this); // the camera looks up in front of a landmark

            // Create HUD
            this.createHUD();

            // custom characters wear their chosen name above their head
            this.playerNameLabel = null;
            this.syncPlayerNameLabel();

            // playable — drop the loading screen
            if (window.hideLoader) window.hideLoader();

            // title screen first (every load; ?notitle=1 skips it), then on
            // the first ever visit: make your own character before you set
            // off, and once the creator closes (confirmed or not) the intro
            // (?nointro=1 skips it) — strictly one after the other
            const begin = () => {
                const firstVisit = CharacterCreator.shouldAutoShow();
                const intro = Intro.shouldAutoShow(firstVisit) ? () => this.intro.show({ firstRun: true }) : null;
                if (firstVisit) {
                    this.characterCreator.show({ firstRun: true, onClose: intro });
                    if (this.characterCreator.isVisible()) return;
                }
                if (intro) intro();
            };
            if (TitleScreen.shouldShow()) {
                this.titleScreen.show(begin);
            } else {
                begin();
            }

        } catch (error) {
            console.error('Error creating game scene:', error);
            if (window.failLoader) window.failLoader();
            throw error;
        }
    }

    /**
     * Where this player starts on the game date — { room, x, y } in the same
     * terms as a door target (Trips.startFor): next to the cast, new
     * player or returning (issue #166), and the home of the date's trip
     * when nobody is anywhere. Never the member the player is playing as.
     */
    startPosition() {
        const sprite = (this.player && this.player.baseSpriteKey) || this.config.player.sprite;
        const at = Trips.startFor(this.config, gameDate(), { played: Trips.baseOf(sprite) });
        // a start with no cell (config.player.startX/Y null) is the middle of the world
        return {
            room: at.room,
            x: at.x != null ? at.x : Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2),
            y: at.y != null ? at.y : Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2),
        };
    }

    /** Is the player standing on a startPosition() cell (a district's, so through resolve)? */
    playerIsAt(spot) {
        const rm = this.roomManager, at = rm.resolve(spot.room, spot.x, spot.y);
        return rm.currentRoom === at.room && this.player.gridX === at.x && this.player.gridY === at.y;
    }

    /**
     * A player who has not moved yet is put where startPosition() says
     * now, when becoming one of the cast (the first-run creator's name
     * Easter egg, or Menu → Character before taking a step) left the place
     * they were started in with nobody to talk to. With somebody still near
     * they stay put. CharacterSelect.become calls this; once the player has
     * taken a step (see update) it does nothing. (Named for the new player
     * it was written for, #59; a returning one starts beside the cast too
     * since #166.)
     */
    resettleNewPlayer() {
        const from = this.bootStart, rm = this.roomManager;
        if (!from || !this.playerIsAt(from)) return;
        const played = Trips.baseOf(this.player.baseSpriteKey);
        if (Trips.hasCompany(this.config, gameDate(), from.room, from.x, from.y, played)) return;
        const to = this.startPosition();
        if (to.room === from.room && to.x === from.x && to.y === from.y) return;
        this.bootStart = to;
        rm.switchRoomInstant(to.room, to.x, to.y);
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
        // On a phone the view is narrower than the canvas (zoomed in, or a
        // portrait slice of it). A room whose outline is narrower still (an
        // interior) is held centred in it, not scrolled after the player:
        // following would push part of a room that fits off the screen.
        const cam = this.cameras.main, viewW = cam.width / cam.zoom;
        let bx = 0, bw = ww;
        if (viewW < this.scale.width) {
            const cols = this.roomManager.contentColumns(roomKey);
            if (cols && cols.x1 - cols.x0 <= viewW) { bx = (cols.x0 + cols.x1 - viewW) / 2; bw = viewW; }
        }
        // Down the screen likewise, when the view is shorter than the canvas
        // (zoomed in): a room no taller than the view keeps to the part of
        // it under the HUD bar - centred there if it fits, else scrolled no
        // further than from its back wall under the bar to its door.
        const viewH = cam.height / cam.zoom;
        let by = 0, bh = wh;
        if (viewH < this.scale.height) {
            const held = RoomManager.heldRows(this.roomManager.contentRows(roomKey), viewH, this.hudCover());
            if (held) { by = held.y; bh = held.height; }
        }
        cam.setBounds(bx, by, bw, bh);
        this.physics.world.setBounds(0, 0, ww, wh);
        if (this.player) {
            this.player.minGridX = 0;
            this.player.minGridY = 0;
            this.player.maxGridX = (ww / this.GRID_SIZE) - 1;
            this.player.maxGridY = (wh / this.GRID_SIZE) - 1;
        }
    }

    /** How far down the world view the HUD bar reaches, in world px (it is magnified apart from the world). */
    hudCover() {
        const ui = this.uiScale;
        return (this.hudBarHeight || UI.HUD_HEIGHT) * (ui ? ui.hudZoom : 1) / this.cameras.main.zoom;
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
        const drinkingOpponent = DrinkingGame.opponentFor(played);
        const centerGridX = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        const centerGridY = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        for (const roomKey in this.config.rooms) {
            // NPCs are authored per room in that room's own coordinates; a
            // district of a stitched city keeps its NPCs in the city room, at
            // the district's offset (homeRoom remembers which district)
            const home = this.roomManager.resolve(roomKey, 0, 0);
            const room = this.roomManager.rooms[home.room];
            const member = (this.roomManager.memberOf[roomKey] || {}).member;
            for (const raw of this.config.rooms[roomKey].npcs) {
                const resolved = resolveNpc(raw, npcDate);
                const shouldExist = !!resolved && baseOf(resolved.sprite) !== played &&
                    (!resolved.drinkingGameOpponent || baseOf(resolved.sprite) === drinkingOpponent);
                const idx = room.npcs.findIndex(n => n.name === raw.name && n.homeRoom === roomKey);

                if (shouldExist && idx === -1) {
                    const gx = home.x + (resolved.gridX !== null ? resolved.gridX : centerGridX + resolved.gridOffsetX);
                    const gy = home.y + (resolved.gridY !== null ? resolved.gridY : centerGridY + resolved.gridOffsetY);
                    const npc = this.npcManager.spawnNPC(gx, gy, resolved.sprite, resolved.name, {
                        dialogue: resolved.dialogue,
                        stationary: resolved.stationary,
                        photo: resolved.photo,
                        voice: resolved.voice,
                        posts: resolved.posts,
                    });
                    npc.homeRoom = roomKey;
                    if (member) {
                        // wandering stops at the district's edge, as it did
                        // when the district was a room of its own
                        npc.minGridX = Math.max(npc.minGridX, member.x);
                        npc.minGridY = Math.max(npc.minGridY, member.y);
                        npc.maxGridX = Math.min(npc.maxGridX, member.x + member.w - 1);
                        npc.maxGridY = Math.min(npc.maxGridY, member.y + member.h - 1);
                    }
                    const here = home.room === this.roomManager.currentRoom;
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

    /**
     * A player using a created character shows their chosen name above their
     * head (NPC-label style). Cast characters stay unlabelled, as before.
     * Idempotent; runs at boot and after every character switch.
     */
    syncPlayerNameLabel() {
        const isCustom = (this.player.baseSpriteKey || '').startsWith('custom_');
        const name = isCustom ? (this.config.player.name || '') : '';
        if (name && !this.playerNameLabel) {
            this.playerNameLabel = this.add.text(0, 0, name, {
                fontSize: '16px',
                fill: '#ffe97f',
                fontFamily: 'PixelOperatorMonoBold',
                backgroundColor: '#000000'
            });
            this.playerNameLabel.setOrigin(0.5, 1);
            this.playerNameLabel.setDepth(900);
            this.playerNameLabel.setResolution(1);
        } else if (!name && this.playerNameLabel) {
            this.playerNameLabel.destroy();
            this.playerNameLabel = null;
        }
        // the name is typed by the player, so it may be Japanese; the label hangs from
        // its bottom edge, so only the top grows and the name stays as close to the head
        if (this.playerNameLabel) JapaneseFont.fit(this.playerNameLabel.setText(name), { below: false });
    }

    createHUD() {
        // Semi-transparent background bar (drawn by layoutHUD)
        this.hudBackground = this.add.graphics();
        this.hudBackground.setScrollFactor(0);
        this.hudBackground.setDepth(DEPTH.HUD_BACKGROUND);

        const segment = (color) => {
            const t = this.add.text(0, 0, '', { fontSize: FONTS.HUD_SIZE, fill: color, fontFamily: FONTS.HUD });
            t.setScrollFactor(0);
            t.setDepth(DEPTH.HUD_TEXT);
            t.setResolution(1);
            return t;
        };
        const button = (t, onTap) => {
            t.setInteractive({ useHandCursor: true });
            t.on('pointerdown', onTap);
            return t;
        };

        // Game info text; the date segment is the LIVE game date (?date=YYYY-MM-DD,
        // else today or its trip day) and clicking it opens a date picker — NPC states
        // re-resolve to the picked date on reload.
        this.hudText = segment(COLORS.HUD_TEXT);
        this.hudDateText = button(segment(COLORS.HUD_TEXT), () => this.datePicker.show());
        // Wallet (issue #12) — gold, after the date; clicking it opens the items screen
        this.hudMoneyText = button(segment('#ffd700'), () => this.shop.showInventory());
        // Menu button (right aligned)
        this.menuButton = button(segment(COLORS.HUD_TEXT).setText('menu'), () => this.menuManager.toggle());

        this.layoutHUD();
        // the bar is magnified on small screens (UIScale), which leaves it less width
        this.events.on('hudscalechange', this.layoutHUD, this);
        // ...and a zoomed or cropped world view has its own camera bounds (applyRoomBounds)
        this.events.on('worldviewchange', () => this.applyRoomBounds(this.roomManager.currentRoom));
    }

    /**
     * Lay the HUD bar out for the width it has. At 1:1 that is the canvas
     * and the bar reads `title | room | date | wallet ... menu` on one row.
     * On a small screen UIScale draws the HUD layer magnified (so its text
     * stays legible), and a portrait phone shows only a slice of the canvas;
     * either leaves the bar narrower: it drops the game's title first, then
     * (landscape only) abbreviates the date and the room's name, then moves
     * the date and wallet to a second row.
     * The date is the bare date, on a trip's own days too (issue #163: the
     * trip's name is never in the bar). Only a lead-in day's countdown
     * ("devhouse 3 in 8 days · February 10 2027", Trips.dateLabel) leads it,
     * as long a form of it as still ends two paddings clear of the menu
     * button, or as the second row has room for.
     * `hudWidth` / `hudBarHeight` are the bar's size in HUD coordinates, for
     * whatever else sits on the HUD layer (the shop's effect chips).
     */
    layoutHUD() {
        const zoom = this.uiScale.hudZoom, pad = UI.HUD_PADDING;
        const width = this.cameras.main.width / zoom, full = width >= this.scale.width;
        const room = this.hudRoomName();
        const bare = formatGameDate(gameDate());
        const counting = Trips.dateLabel(Trips.of(this.config), gameDate(), formatGameDate) !== bare;
        this.hudMoneyText.setText(` | ${this.shop.fmt(this.shop.money)}`);
        // does `lead` + `date` + wallet end `gap` short of the menu button?
        const fits = (lead, date, gap) => {
            JapaneseFont.fit(this.hudText.setText(lead));   // room for a Japanese room name
            this.hudDateText.setText(date);
            return pad + this.hudText.width + this.hudDateText.width + this.hudMoneyText.width +
                gap + this.menuButton.width + pad <= width;
        };
        const long = `${this.config.game.title} | ${room} | `, short = `${room} | `;
        // with the whole canvas to itself the bar is always the one authored row.
        // The date after `lead` is the bare date; on a lead-in day it is the longest
        // countdown that fits ("in 8 days", "in 8d", "soon", issue #164), else bare
        const row = (lead) => {
            const label = counting ? Trips.dateLabel(Trips.of(this.config), gameDate(), formatGameDate,
                (l) => fits(lead, l, 2 * pad)) : bare;
            return label !== bare ? fits(lead, label, 2 * pad) : fits(lead, bare, pad);
        };
        // a magnified bar on a landscape phone is too narrow for a long room name (a
        // konbini, a station) and 60px of two rows is a lot of a 390px screen (issue
        // #202): there the row is kept by abbreviating instead — the month ("Nov 11
        // 2025"), then the name to its first part ("7-Eleven · Park 1" -> "7-Eleven"),
        // then the date's year. A portrait slice has the height and keeps its two rows.
        const brief = room.split(' · ')[0], whole = this.cameras.main.width >= this.scale.width;
        const compact = () => whole && [[room, true], [brief, true], [room, false], [brief, false]]
            .some(([name, year]) => fits(`${name} | `, shortGameDate(gameDate(), year), pad));
        let rows = 1;
        if (!row(long) && !full && !row(short) && !compact()) {
            rows = 2;
            JapaneseFont.fit(this.hudText.setText(room));
            this.hudDateText.setText(Trips.dateLabel(Trips.of(this.config), gameDate(), formatGameDate,
                (l) => pad + this.hudDateText.setText(l).width + this.hudMoneyText.width + pad <= width));
        }
        const rowHeight = rows === 1 ? UI.HUD_HEIGHT : UI.HUD_ROW_HEIGHT;

        this.hudWidth = width;
        this.hudBarHeight = rows * rowHeight;
        this.hudBackground.clear();
        this.hudBackground.fillStyle(COLORS.HUD_BACKGROUND, UI.HUD_ALPHA);
        this.hudBackground.fillRect(0, 0, width, this.hudBarHeight);

        const first = rowHeight / 2, last = this.hudBarHeight - rowHeight / 2;
        this.hudText.setOrigin(0, 0.5).setPosition(pad, first);
        this.hudDateText.setOrigin(0, 0.5).setPosition(rows === 1 ? pad + this.hudText.width : pad, last);
        this.hudMoneyText.setOrigin(0, 0.5).setPosition(this.hudDateText.x + this.hudDateText.width, last);
        this.menuButton.setOrigin(1, 0.5).setPosition(width - pad, first);
        // the buttons take taps over the whole height of their row, not just their glyphs
        for (const t of [this.hudDateText, this.hudMoneyText, this.menuButton]) {
            t.input.hitArea.setTo(0, (t.height - rowHeight) / 2, t.width, rowHeight);
        }
        if (this.shop) this.shop.updateEffectChip();
        // a bar that covers more or less of the world moves a held room (applyRoomBounds)
        if (this.hudBarHeight * zoom !== this.hudBarCover) {
            this.hudBarCover = this.hudBarHeight * zoom;
            this.applyRoomBounds(this.roomManager.currentRoom);
        }
    }

    /**
     * What the HUD calls the room the player is in: its display `name` from
     * config ("7-Eleven · Sapporo", "Sapporo Station"), never the bare room
     * key unless the room has no name. Inside a stitched city that is the
     * district underfoot (`hudDistrict`; update() re-asks when it changes).
     */
    hudRoomName() {
        const key = this.hudDistrict = this.roomManager.currentDistrict();
        const room = this.config.rooms[key];
        return (room && room.name) || key;
    }

    /**
     * Update HUD text
     */
    updateHUD() {
        this.layoutHUD();
    }

    /**
     * Show the achievements overlay (first achievement: "Paint the Board").
     */
    showAchievements() {
        if (this.achievementsVisible) return;   // only one overlay at a time
        const cam = this.cameras.main, W = cam.width, H = cam.height;
        const extra = this.achievementManager.itemProgress();   // food & drink (issue #46), fishing (#83)
        const pw = 560, ph = 260 + extra.length * 64 + (extra.length ? 14 : 0), px = (W - pw) / 2, py = (H - ph) / 2;
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
        extra.forEach((a, i) => {
            const y = barY + barH + 70 + i * 64;
            text(cx, y, (a.complete ? '★ ' : '') + a.name, '24px', true, a.complete ? '#ffd700' : '#ffffff');
            text(cx, y + 28, `${a.desc} — ${a.value}/${a.total}`, '18px', false, '#bbbbbb');
        });
        text(cx, py + ph - 26, Hints.text(this, '(click or ESC to close)'), '16px', false, '#888888');
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

        // fit the overworld into the viewport (never upscale past 1:1); a
        // portrait phone's cropped view is the narrow one, so it keeps less margin
        const s = UIScale.mapFit(W, H, meta.width, meta.height, W < this.scale.width);
        const dw = meta.width * s, dh = meta.height * s;
        const px = (W - dw) / 2, py = (H - dh) / 2 + 14;

        const img = this.add.image(px, py, 'world-map');
        img.setOrigin(0, 0); img.setDisplaySize(dw, dh);
        img.setScrollFactor(0); img.setDepth(2001); objs.push(img);
        const frame = this.add.graphics();
        frame.lineStyle(2, 0x666666, 1); frame.strokeRect(px, py, dw, dh);
        frame.setScrollFactor(0); frame.setDepth(2002); objs.push(frame);

        // click a spot on the map to travel there (nearest walkable cell) —
        // debug-only: off unless enabled in the hidden ``` debug menu, so the
        // map is normally just a viewer. The image always swallows its clicks
        // so clicking the map never falls through to the close-overlay:
        // closing is the dark surround, ESC, or actually travelling.
        const mapTravel = this.debugManager && this.debugManager.settings.mapTravel;
        img.setInteractive(mapTravel ? { useHandCursor: true } : undefined);
        img.on('pointerdown', (pointer, localX, localY, event) => {
            if (event) event.stopPropagation();
            if (!mapTravel) return;
            // image px, from the hit point local to the image (holds under UIScale's zoom)
            const ix = localX * meta.width / img.width, iy = localY * meta.height / img.height;
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
            const o = this.add.text(x, y, t, { fontSize: this.uiScale.textSize(size), fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono',
                backgroundColor: bg });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2003); objs.push(o); return o;
        };
        // on a small screen the map is magnified until its title is up in the
        // (magnified) HUD row, which shows through the dimmer: blank it there
        const title = text(W / 2, py - 24, 'MAP', '26px', true, null, this.uiScale.hudZoom > 1 ? '#000000' : undefined);
        if (this.uiScale.hudZoom > 1) title.setPadding(14, 2, 14, 2);

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
        // (in a stitched city: the district underfoot, in its own cells)
        const at = this.roomManager.localize(this.player.gridX, this.player.gridY);
        const here = at.room;
        let markRoom = meta.rooms[here] && here;
        let markX = at.x, markY = at.y;
        if (!markRoom) {
            const exit = ((this.config.rooms[here] || {}).transporters || [])
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
            for (const { npc, x, y } of this.roomManager.npcsIn(roomName)) {
                const [mx, my] = cellToMap(meta.rooms[roomName], x, y);
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
        const travelHint = mapTravel ? '   ·   click a spot to travel there' : '';
        text(W / 2, py + dh + 20, Hints.text(this, `${footer}${travelHint}   ·   ESC to close`), '13px', false, '#bbbbbb');

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
        // The Izakaya's configured table owns the bump before generic
        // counter/shop detection sees its placeholder furniture.
        if (this.drinkingGame && !this.dialogueManager.isVisible() &&
            this.drinkingGame.checkStart(targetGridX, targetGridY)) return;
        this.npcManager.checkInteraction(targetGridX, targetGridY);
        // bumping a vending machine / konbini counter or shelf / izakaya bar opens its store
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
            if (this.roomManager.interactionAt(targetGridX, targetGridY, 'clock')) {
                this.datePicker.show();
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
        // in front of a landmark the camera looks up at it
        if (this.landmarkView) this.landmarkView.update();
        // a stitched city only keeps the tile sprites near the camera
        this.roomManager.updateStreaming();
        if (this.dayNight) this.dayNight.cullGlows();   // ...and the lamp halos
        this.npcManager.updateLabels();
        if (this.playerNameLabel && this.player) {
            this.playerNameLabel.setPosition(
                this.player.sprite.x,
                this.player.sprite.y - this.GRID_SIZE / 2 - 5
            );
            this.playerNameLabel.setVisible(this.player.sprite.visible && this.npcManager.labelsShown());
        }
        this.updateCharacterDepths();
        this.occlusion.update();
        if (this.debugManager) this.debugManager.update();
        // a player who has left their start cell is where they chose to be (resettleNewPlayer)
        const boot = this.bootStart;
        if (boot && this.player && !this.playerIsAt(boot)) this.bootStart = null;
        // Achievement "Paint the board": record the tile the player stands on.
        if (this.player && this.achievementManager) {
            const k = this.player.gridX + ',' + this.player.gridY;
            if (this._paintCell !== k) {
                this._paintCell = k;
                // painted per district, in the district's own cells — so
                // progress saved before the city was stitched still counts
                // (a cell two districts share is painted in both)
                for (const at of this.roomManager.districtsAt(this.player.gridX, this.player.gridY)) {
                    this.achievementManager.markVisited(at.room, at.x, at.y);
                }
                // walking into another district of a stitched city
                if (this.hudText && this.roomManager.currentDistrict() !== this.hudDistrict) this.updateHUD();
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
        const feetDepth = (sprite) => this.roomManager.yDepth(((sprite.y + GS / 2) / GS) * 10 + 5);
        // While riding, TrainTravel owns the player's depth (it renders him in the
        // train doorway, above the train, as he steps off) — don't sink him back.
        if (this.player && !(this.trainTravel && this.trainTravel.riding))
            this.player.sprite.setDepth(feetDepth(this.player.sprite));
        const npcs = this.roomManager.rooms[this.roomManager.currentRoom].npcs;
        npcs.forEach(npc => npc.sprite.setDepth(feetDepth(npc.sprite)));
    }
}
