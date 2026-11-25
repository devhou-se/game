/**
 * RoomManager - Handles room loading, transitions, and room-specific content
 */
class RoomManager {
    /**
     * @param {GameScene} scene - The parent game scene
     */
    constructor(scene) {
        this.scene = scene;
        this.rooms = {};
        this.currentRoom = null;
        this.isTransitioning = false;
        this.transporterSprites = [];
        this.transporterLabels = [];
        this.objectSprites = [];
        this.floorSprites = [];      // the tile sprites + signs that exist right now

        // Cities (issues #40/#41): districts stitched into one room at load —
        // see CityStitcher. Empty when ?stitch=0 or config has no `cities`.
        this.cities = {};            // cityKey -> planned city
        this.memberOf = {};          // district room key -> { city, member }

        // Everything the current room draws, as data (see loadFloorTiles)
        this.tileRecords = [];       // one per tile: where, what, depth, bounds, live sprite
        this.blockedCells = new Set();   // "x,y" of every collision-layer tile
        this.interactionIndex = null;    // "x,y" -> interactions, built on the first bump (interactionAt)
        this.signSprites = [];
        this.signArt = [];           // the signs as art records (Occlusion fades them like tiles)
        this.liveTiles = new Set();  // records that currently have a sprite
        this.spritePool = [];        // hidden sprites of retired streamed tiles, for reuse
        this.depthScale = 1;
        this.streamed = false;       // true: sprites exist only near the camera
        this.chunks = null;
        this.activeChunks = null;
    }

    // ------------------------------------------------------------ cities

    /**
     * Stitch every city in config `cities` into one runtime room, registered
     * under the city's key next to its districts (which stay in `rooms` as
     * data but are never entered). Call after initializeRooms().
     */
    setupCities(config, worldMap) {
        if (typeof CityStitcher === 'undefined' || !CityStitcher.enabled()) return;
        for (const city of this.stitchCities(config, worldMap)) {
            console.log(`[stitch] city "${city.key}": ${city.members.map(m => m.key).join(' + ')} ` +
                `-> one ${city.width}x${city.height} room`);
        }
    }

    /**
     * The stitch itself, with no page around it: plan config `cities`, build
     * each one's room and register it. tools/world-model.js (play.js, the
     * studio) calls this directly, so the tools model exactly the room the
     * game plays. Returns the planned cities.
     */
    stitchCities(config, worldMap) {
        this.cities = CityStitcher.plan(config, worldMap);
        for (const city of Object.values(this.cities)) {
            this.rooms[city.key] = CityStitcher.build(city, this.rooms, this.scene.GRID_SIZE);
            for (const member of city.members) this.memberOf[member.key] = { city, member };
        }
        return Object.values(this.cities);
    }

    /**
     * Where a (room, cell) really is at runtime. Config data, door
     * transporters and train arrivals all still say ('Market', x, y); when
     * Market is a district of a stitched city that is the city room at the
     * district's offset. Anything else comes back unchanged.
     */
    resolve(roomKey, x, y) {
        const at = this.memberOf[roomKey];
        if (!at) return { room: roomKey, x, y };
        return { room: at.city.key, x: x + at.member.x, y: y + at.member.y };
    }

    /**
     * The inverse: every district containing a cell of a room (the current
     * one unless named), in that district's own coordinates — the owner (the
     * one whose tiles are drawn there) first. In an ordinary room: just the
     * room and the cell.
     */
    districtsAt(x, y, roomKey = this.currentRoom) {
        const city = this.rooms[roomKey] && this.rooms[roomKey].city;
        if (!city) return [{ room: roomKey, x, y }];
        const out = [];
        for (let i = city.members.length - 1; i >= 0; i--) {
            const m = city.members[i];
            if (x >= m.x && x < m.x + m.w && y >= m.y && y < m.y + m.h) {
                out.push({ room: m.key, x: x - m.x, y: y - m.y });
            }
        }
        return out;
    }

    /** The district owning a cell, in its own coordinates (the room itself outside a city). */
    localize(x, y) {
        return this.districtsAt(x, y)[0] || { room: this.currentRoom, x, y };
    }

    /**
     * The room key everything district-specific should use: the district the
     * player is standing in inside a city, otherwise the current room.
     */
    currentDistrict() {
        const p = this.scene.player;
        return p ? this.localize(p.gridX, p.gridY).room : this.currentRoom;
    }

    /** NPCs standing in a room or district, as { npc, x, y } in that room's own coordinates. */
    npcsIn(roomKey) {
        const at = this.resolve(roomKey, 0, 0);
        const room = this.rooms[at.room];
        if (!room) return [];
        return room.npcs
            .filter(npc => at.room === roomKey || npc.homeRoom === roomKey)
            .map(npc => ({ npc, x: npc.gridX - at.x, y: npc.gridY - at.y }));
    }

    /** Y-sorted depth for the current room (a stitched city squeezes its rows — see CityStitcher.build). */
    yDepth(depth) {
        return depth * this.depthScale;
    }

    /**
     * Initialize rooms from configuration
     * @param {Object} config - Game configuration object
     * @param {number} centerGridX - Center grid X coordinate
     * @param {number} centerGridY - Center grid Y coordinate
     * @param {number} maxGridX - Maximum grid X value
     * @param {number} maxGridY - Maximum grid Y value
     */
    initializeRooms(config, centerGridX, centerGridY, maxGridX, maxGridY) {
        for (let roomKey in config.rooms) {
            const roomConfig = config.rooms[roomKey];

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
                worldWidth: roomConfig.worldWidth || this.scene.WORLD_WIDTH,
                worldHeight: roomConfig.worldHeight || this.scene.WORLD_HEIGHT,
                npcs: [],
                objects: roomConfig.objects.map(obj => ({
                    type: obj.type || 'box',
                    gridX: obj.gridX !== null ? obj.gridX : centerGridX + obj.gridOffsetX,
                    gridY: obj.gridY !== null ? obj.gridY : centerGridY + obj.gridOffsetY
                })),
                transporters: roomConfig.transporters.map(trans => ({
                    gridX: trans.gridX !== null ? trans.gridX : centerGridX + trans.gridOffsetX,
                    gridY: trans.gridY !== null ? trans.gridY : centerGridY + trans.gridOffsetY,
                    targetRoom: trans.targetRoom,
                    targetX: trans.targetX !== null ? trans.targetX : centerGridX + trans.targetOffsetX,
                    targetY: trans.targetY !== null ? trans.targetY : centerGridY + trans.targetOffsetY,
                    hidden: !!trans.hidden   // hidden transporters still teleport, but draw no tile/label
                })),
                floor: roomConfig.floor || {},
                layers: roomConfig.layers || [],
                signage: roomConfig.signage || []
            };
        }
    }

    /**
     * Load transporters for the current room
     */
    loadTransporters() {
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
            if (trans.hidden) return;   // invisible gateway (e.g. a shrine door) — no tile/label, still teleports
            const pixelX = trans.gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const pixelY = trans.gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
            const sprite = this.scene.add.sprite(pixelX, pixelY, 'transporter');
            sprite.setDepth(0);
            this.transporterSprites.push(sprite);

            // Add label above transporter
            const label = this.scene.add.text(
                pixelX,
                pixelY - this.scene.GRID_SIZE / 2 - 5,
                `Goto ${trans.targetRoom}`,
                {
                    fontSize: '16px',
                    fill: '#00ff00',
                    fontFamily: 'PixelOperatorMonoBold',
                    backgroundColor: '#000000'
                }
            );
            label.setOrigin(0.5, 1);
            label.setDepth(900); // above all Y-sorted world objects, below the HUD
            label.setResolution(1);
            this.transporterLabels.push(label);
        });
    }

    /**
     * Load objects for the current room
     */
    loadObjects() {
        // Clear existing object sprites
        this.objectSprites.forEach(sprite => sprite.destroy());
        this.objectSprites = [];

        // Create object sprites for current room
        const room = this.rooms[this.currentRoom];
        if (room.objects) {
            room.objects.forEach(obj => {
                const pixelX = obj.gridX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
                const pixelY = obj.gridY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;

                // Get sprite key from object type
                const objType = this.scene.objectTypes[obj.type];
                const spriteKey = objType ? objType.sprite : 'object-tile';

                const sprite = this.scene.add.sprite(pixelX, pixelY, spriteKey);
                sprite.setDepth(0);
                this.objectSprites.push(sprite);

                // Store grid position and type on sprite for collision detection
                sprite.gridX = obj.gridX;
                sprite.gridY = obj.gridY;
                sprite.objectType = obj.type;
            });
        }
    }

    /**
     * Load floor tiles for the current room.
     *
     * Every tile is first indexed as a RECORD (cell, sprite key, depth, pixel
     * bounds) and its collision noted in `blockedCells`; sprites are made from
     * records. An ordinary room makes them all at once, as it always did. A
     * stitched city (~20k tiles) is STREAMED: records are bucketed into
     * CHUNK-cell squares and only those near the camera have a sprite
     * (updateStreaming, every frame). `?cull=0` turns streaming off.
     */
    loadFloorTiles() {
        this.clearFloorTiles();

        const room = this.rooms[this.currentRoom];
        this.depthScale = room.depthScale || 1;
        this.streamed = !!room.stitched &&
            new URLSearchParams(window.location.search).get('cull') !== '0';

        // Support both old format (room.floor) and new format (room.layers)
        if (room.layers) {
            for (const layer of room.layers) {
                this.loadLayer(layer);
            }
        } else if (room.floor) {
            const legacyLayer = {
                name: "Floor",
                z: 0,
                collision: false,
                tiles: room.floor
            };
            this.loadLayer(legacyLayer);
        } else {
            console.warn(`Room ${this.currentRoom} has no floor or layers data`);
        }

        // every room is bucketed (Occlusion looks art up by place); only a
        // streamed one creates its sprites chunk by chunk
        this.buildChunks();
        if (this.streamed) {
            this.updateStreaming();
        } else {
            for (const rec of this.tileRecords) this.spawnTile(rec);
        }

        this.placeSignage(room);
        this.refreshFloorSprites();
    }

    /** Destroy the current room's tile sprites and signs and forget its records. */
    clearFloorTiles() {
        for (const rec of this.liveTiles) rec.sprite.destroy();
        this.spritePool.forEach(sprite => sprite.destroy());
        this.signSprites.forEach(sprite => sprite.destroy());
        this.spritePool = [];
        this.tileRecords = [];
        this.blockedCells = new Set();
        this.interactionIndex = null;
        this.signSprites = [];
        this.signArt = [];
        this.liveTiles = new Set();
        this.floorSprites = [];
        this.chunks = null;
        this.activeChunks = null;
    }

    /** floorSprites = every tile sprite that exists right now, then the signs. */
    refreshFloorSprites() {
        const sprites = [];
        for (const rec of this.liveTiles) sprites.push(rec.sprite);
        this.floorSprites = sprites.concat(this.signSprites);
    }

    /**
     * Advertisement signage (issue #26): each configured wall spot gets a
     * random ad of its shape from the generated pool (assets/ads — see
     * tools/generate_ads.py), so the street reads a little different on
     * every visit. Signs join floorSprites and are cleaned up with the room.
     */
    placeSignage(room) {
        const manifest = this.scene.cache.json.get('adsManifest');
        if (!manifest || !room.signage || !room.signage.length) return;
        const GS = this.scene.GRID_SIZE;
        for (const spot of room.signage) {
            const pool = manifest.ads.filter(ad =>
                ad.shape === spot.shape && this.scene.textures.exists(ad.key));
            if (!pool.length) continue;
            const ad = pool[Math.floor(Math.random() * pool.length)];
            const img = this.scene.add.image(spot.gridX * GS, spot.gridY * GS, ad.key);
            img.setOrigin(0, 0);
            // mounted on a wall band: feet-based depth of the sign's bottom
            // row, +1 so it draws just over the band it hangs on
            img.setDepth(this.yDepth((spot.gridY + ad.h) * 10 + 1));
            this.signSprites.push(img);
            this.signArt.push({ key: ad.key, depth: img.depth, left: img.x, top: img.y,
                                width: img.displayWidth, height: img.displayHeight, sprite: img });
        }
    }

    /**
     * Index a single tilemap layer: one record per tile (and its collision).
     * A collision layer's tiles are invisible markers (RoomManager.COLLIDER,
     * the game's name for Tiled's collider-marker): they only feed
     * `blockedCells` and never become a record or a sprite (issue #148) —
     * the debug overlay draws colliders from the set. Anything else painted
     * on a collision layer is art that also blocks, and is drawn.
     * @param {Object} layer - Layer configuration object
     */
    loadLayer(layer) {
        const tiles = layer.tiles || {};
        const GS = this.scene.GRID_SIZE;
        let skippedCount = 0;

        for (const [key, spriteKey] of Object.entries(tiles)) {
            const [gridX, gridY] = key.split(',').map(Number);

            // Check if the sprite texture exists
            if (!this.scene.textures.exists(spriteKey)) {
                if (skippedCount === 0) {
                    console.warn(`Sprite not found in layer "${layer.name}": ${spriteKey}`);
                }
                skippedCount++;
                continue;
            }

            if (layer.collision) {
                this.blockedCells.add(key);
                if (spriteKey === RoomManager.COLLIDER) continue;
            }

            const spriteConfig = this.scene.getSpriteConfig(spriteKey);
            const frame = this.scene.textures.getFrame(spriteKey);

            // Depth: ground layers (z<2: floor/over-floor/water) render flat and
            // below everything via fixed negative depths. Everything that
            // "stands" (z>=2: trunks, walls, statues, buildings, canopies...)
            // is Y-sorted by its FEET (bottom row) so objects and the player
            // sort by position. Overhead parts (canopies/roofs on the Tops
            // layer) get a small bias so they draw at ~their trunk's feet and
            // over it — making each whole object sort as one unit.
            let spriteDepth;
            if (layer.z < 2) {
                spriteDepth = this.calculateLayerDepth(layer.z);
            } else {
                const heightCells = Math.max(1, Math.round(frame.realHeight / GS));
                const feetRow = gridY + heightCells;
                const overheadBias = layer.z >= 7 ? 11 : 0;
                // optional per-sprite depth nudge (e.g. a tall building lowered so the
                // player stays visible on its steps and only disappears in the doorway)
                spriteDepth = this.yDepth(feetRow * 10 + overheadBias + (spriteConfig.depthBias || 0));
            }
            // Equal depths draw in creation order, which for a whole room is
            // layer-then-tile order. Streamed sprites are created whenever
            // their chunk comes into range, so that order is baked into the
            // depth instead (far smaller than any real depth step).
            if (this.streamed) spriteDepth += this.tileRecords.length * 1e-6;

            const scale = spriteConfig.scale || 1;
            const x = gridX * GS + GS / 2, y = gridY * GS + GS / 2;
            const width = frame.realWidth * scale, height = frame.realHeight * scale;
            this.tileRecords.push({
                key: spriteKey, layer, gridX, gridY, x, y,
                config: spriteConfig,
                depth: spriteDepth,
                // what sprite.getBounds() would report, without needing the sprite
                left: x - spriteConfig.anchorX * width,
                top: y - spriteConfig.anchorY * height,
                width, height,
                sprite: null,
            });
        }
    }

    /**
     * Give a tile record its sprite: a new one, or — while streaming — one a
     * retired tile handed back (retireTile), re-dressed.
     */
    spawnTile(rec) {
        let sprite = this.spritePool.pop();
        if (sprite) {
            sprite.setTexture(rec.key);
            sprite.setPosition(rec.x, rec.y);
            sprite.addToDisplayList();
        } else {
            sprite = this.scene.add.sprite(rec.x, rec.y, rec.key);
        }

        // Apply sprite configuration
        sprite.setOrigin(rec.config.anchorX, rec.config.anchorY);
        sprite.setScale(rec.config.scale || 1);
        sprite.setDepth(rec.depth);
        // a pooled sprite may have been faded by Occlusion in its last life
        sprite.setAlpha(rec.fade === undefined ? 1 : rec.fade);

        // Store collision info on sprite
        sprite.setData('layerCollision', rec.layer.collision);
        sprite.setData('layerZ', rec.layer.z);
        sprite.setData('gridX', rec.gridX);
        sprite.setData('gridY', rec.gridY);

        rec.sprite = sprite;
        this.liveTiles.add(rec);
    }

    /**
     * Everything the room draws that has a place and a depth, whether or not
     * its sprite exists right now: { key, depth, left, top, width, height }
     * (world pixels). AmbientBoats uses it to see what hides the water.
     */
    standingArt() {
        const extra = [...this.signSprites, ...this.objectSprites].map(sprite => {
            const b = sprite.getBounds();
            return { key: sprite.texture.key, depth: sprite.depth, left: b.x, top: b.y, width: b.width, height: b.height };
        });
        return this.tileRecords.concat(extra);
    }

    /**
     * Take a streamed tile's sprite away. It is kept for the next spawnTile,
     * but off the scene's display (and update) list, so a pooled sprite costs
     * the renderer nothing.
     */
    retireTile(rec) {
        rec.sprite.removeFromDisplayList();
        this.spritePool.push(rec.sprite);
        rec.sprite = null;
        this.liveTiles.delete(rec);
    }

    /** True when a collision-layer tile sits on the cell. */
    isBlocked(gridX, gridY) {
        return this.blockedCells.has(`${gridX},${gridY}`);
    }

    /**
     * What bumping a cell of the current room does: the vending machine /
     * shop fixture / pond / clock on it (see Interactions), optionally of one
     * `group`, or null. The room's interactive cells are indexed on the
     * first bump after a room load, so this is a single lookup however big
     * the room is (issue #145) — a held key against a wall asks every frame.
     */
    interactionAt(gridX, gridY, group) {
        if (!this.interactionIndex) {
            const textures = this.scene.textures;
            const cells = (px) => Math.max(1, Math.round(px / this.scene.GRID_SIZE));
            const sizeOf = (key) => {
                if (!textures.exists(key)) return [1, 1];
                const image = textures.get(key).getSourceImage();
                return [cells(image.width), cells(image.height)];
            };
            this.interactionIndex = Interactions.index(this.rooms[this.currentRoom],
                this.scene.config.rooms[this.currentRoom] || {}, { sizeOf, venues: Shop.VENUES });
        }
        return Interactions.lookup(this.interactionIndex, gridX, gridY, group);
    }

    /**
     * The art records whose sprite may touch a pixel rectangle of the room —
     * every record of the chunks the rectangle touches, so a record can come
     * up more than once and some lie outside it: callers test bounds.
     */
    artNear(left, top, right, bottom) {
        const out = [];
        if (!this.chunks) return out;
        const size = RoomManager.CHUNK * this.scene.GRID_SIZE;
        for (let cy = Math.floor(top / size); cy <= Math.floor(bottom / size); cy++) {
            for (let cx = Math.floor(left / size); cx <= Math.floor(right / size); cx++) {
                const list = this.chunks.get(`${cx},${cy}`);
                if (list) for (const rec of list) out.push(rec);
            }
        }
        return out;
    }

    // ------------------------------------------------------------ streaming

    /** Bucket every record into each CHUNK-cell square its art touches. */
    buildChunks() {
        const size = RoomManager.CHUNK * this.scene.GRID_SIZE;
        this.chunks = new Map();
        for (const rec of this.tileRecords) {
            rec.cx0 = Math.floor(rec.left / size);
            rec.cy0 = Math.floor(rec.top / size);
            rec.cx1 = Math.floor((rec.left + rec.width - 1) / size);
            rec.cy1 = Math.floor((rec.top + rec.height - 1) / size);
            for (let cy = rec.cy0; cy <= rec.cy1; cy++) {
                for (let cx = rec.cx0; cx <= rec.cx1; cx++) {
                    const id = `${cx},${cy}`;
                    let list = this.chunks.get(id);
                    if (!list) this.chunks.set(id, list = []);
                    list.push(rec);
                }
            }
        }
    }

    /**
     * The chunks that must have sprites: whatever the camera shows now or
     * will after catching up with the player (it trails by the deadzone, and
     * is not centred yet right after a room swap), plus a margin so nothing
     * is created inside the view.
     */
    streamRect() {
        const cam = this.scene.cameras.main, p = this.scene.player.sprite;
        const size = RoomManager.CHUNK * this.scene.GRID_SIZE;
        const margin = RoomManager.STREAM_MARGIN * this.scene.GRID_SIZE;
        const hw = cam.width / 2 / cam.zoom, hh = cam.height / 2 / cam.zoom;
        let cx = cam.scrollX + cam.width / 2, cy = cam.scrollY + cam.height / 2;
        // a camera nowhere near the player (boot, before it starts following)
        // is about to jump to him — only he matters
        if (Math.abs(cx - p.x) > hw || Math.abs(cy - p.y) > hh) { cx = p.x; cy = p.y; }
        return {
            x0: Math.floor((Math.min(cx, p.x) - hw - margin) / size),
            y0: Math.floor((Math.min(cy, p.y) - hh - margin) / size),
            x1: Math.floor((Math.max(cx, p.x) + hw + margin) / size),
            y1: Math.floor((Math.max(cy, p.y) + hh + margin) / size),
        };
    }

    /**
     * Give the tiles of chunks that came into range a sprite and take it away
     * from those whose art no longer touches a chunk in range (retired first,
     * so the newcomers reuse their sprites). Cheap when the chunk
     * range has not changed (every frame the player stands still or walks
     * within a chunk). No-op in rooms that are not streamed.
     */
    updateStreaming() {
        if (!this.streamed || !this.chunks) return;
        const r = this.streamRect(), prev = this.activeChunks;
        if (prev && r.x0 === prev.x0 && r.y0 === prev.y0 && r.x1 === prev.x1 && r.y1 === prev.y1) return;
        this.activeChunks = r;

        const inside = (q, cx, cy) => q && cx >= q.x0 && cx <= q.x1 && cy >= q.y0 && cy <= q.y1;
        if (prev) {
            for (let cy = prev.y0; cy <= prev.y1; cy++) {
                for (let cx = prev.x0; cx <= prev.x1; cx++) {
                    if (inside(r, cx, cy)) continue;
                    for (const rec of (this.chunks.get(`${cx},${cy}`) || [])) {
                        if (!rec.sprite) continue;
                        // a big sprite stays while any chunk it touches is in range
                        if (rec.cx1 >= r.x0 && rec.cx0 <= r.x1 && rec.cy1 >= r.y0 && rec.cy0 <= r.y1) continue;
                        this.retireTile(rec);
                    }
                }
            }
        }
        for (let cy = r.y0; cy <= r.y1; cy++) {
            for (let cx = r.x0; cx <= r.x1; cx++) {
                if (inside(prev, cx, cy)) continue;
                for (const rec of (this.chunks.get(`${cx},${cy}`) || [])) {
                    if (!rec.sprite) this.spawnTile(rec);
                }
            }
        }
        // a long jump (map travel) retires far more than it respawns
        while (this.spritePool.length > RoomManager.POOL_MAX) this.spritePool.pop().destroy();
        this.refreshFloorSprites();
    }

    /**
     * Calculate Phaser depth from layer z-index
     * @param {number} layerZ - Layer z-index
     * @returns {number} Phaser depth value
     */
    calculateLayerDepth(layerZ) {
        if (layerZ < 2) {
            return (layerZ - 5) * 100;
        } else {
            return layerZ * 100;
        }
    }

    /**
     * Check if player is on a transporter
     * @param {Object} playerPos - Player grid position {x, y}
     * @returns {boolean} True if transporter was triggered
     */
    checkTransporter(playerPos) {
        const room = this.rooms[this.currentRoom];

        for (let trans of room.transporters) {
            if (trans.gridX === playerPos.x && trans.gridY === playerPos.y) {
                this.switchRoom(trans.targetRoom, trans.targetX, trans.targetY);
                return true;
            }
        }
        return false;
    }

    /**
     * Switch to a different room
     * @param {string} newRoom - Target room name
     * @param {number} targetX - Target grid X position
     * @param {number} targetY - Target grid Y position
     */
    switchRoom(newRoom, targetX, targetY) {
        // Block input during transition
        this.isTransitioning = true;

        // Fade to black
        this.scene.cameras.main.fadeOut(250, 0, 0, 0);

        this.scene.cameras.main.once('camerafadeoutcomplete', () => {
            this.applyRoomSwap(newRoom, targetX, targetY);

            // Wait 0.25 seconds on black, then fade in
            this.scene.time.delayedCall(250, () => {
                this.scene.cameras.main.fadeIn(250, 0, 0, 0);

                // Re-enable input after fade-in completes
                this.scene.cameras.main.once('camerafadeincomplete', () => {
                    this.isTransitioning = false;
                });
            });
        });
    }

    /**
     * Swap the room's contents (NPCs, player position, camera, tiles, HUD, train)
     * with no fade of its own. `switchRoom` calls this on black between its camera
     * fades; the train ride (TrainTravel) calls it directly under its own curtain
     * so the room can change invisibly and the train never flashes on the platform.
     */
    applyRoomSwap(newRoom, targetX, targetY) {
        // legacy targets — ('Market', x, y) from a konbini door, a station
        // exit, the map — land in the stitched city at the district's offset
        ({ room: newRoom, x: targetX, y: targetY } = this.resolve(newRoom, targetX, targetY));

        // Hide current room NPCs and their labels
        const oldRoom = this.rooms[this.currentRoom];
        oldRoom.npcs.forEach(npc => {
            npc.sprite.setVisible(false);
            if (npc.nameLabel) npc.nameLabel.setVisible(false);
        });

        // Update current room
        this.currentRoom = newRoom;

        // Resize camera/physics/player movement bounds to the new room
        this.scene.applyRoomBounds(newRoom);

        // Move player to target position
        this.scene.player.gridX = targetX;
        this.scene.player.gridY = targetY;
        const pixelX = targetX * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
        const pixelY = targetY * this.scene.GRID_SIZE + this.scene.GRID_SIZE / 2;
        this.scene.player.sprite.setPosition(pixelX, pixelY);

        // Center camera on player
        this.scene.cameras.main.centerOn(pixelX, pixelY);

        // Show new room NPCs and their labels
        const room = this.rooms[this.currentRoom];
        room.npcs.forEach(npc => {
            npc.sprite.setVisible(true);
            if (npc.nameLabel) npc.nameLabel.setVisible(true);
        });

        // Load new room content
        this.loadTransporters();
        this.loadObjects();
        this.loadFloorTiles();

        // Update HUD
        this.scene.updateHUD();

        // Park (or hide) the station train for the new room
        if (this.scene.trainTravel) this.scene.trainTravel.onRoomChange(newRoom);

        // Restart (or stop) the ambient passing trains for the new room
        if (this.scene.ambientTrains) this.scene.ambientTrains.onRoomChange(newRoom);

        // ...and the ambient boats on its waterways
        if (this.scene.ambientBoats) this.scene.ambientBoats.onRoomChange(newRoom);

        // Re-grade day/night for the new room (interiors are never graded)
        if (this.scene.dayNight) this.scene.dayNight.onRoomChange();
    }

    /** Swap rooms immediately, no camera fade (used under the train-ride curtain). */
    switchRoomInstant(newRoom, targetX, targetY) {
        this.applyRoomSwap(newRoom, targetX, targetY);
    }

    /**
     * Point-in-polygon test using ray casting algorithm
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @param {Array} polygon - Array of [x, y] points
     * @returns {boolean} True if point is inside polygon
     */
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

    /**
     * Check if position is within room boundary
     * @param {number} gridX - Grid X coordinate
     * @param {number} gridY - Grid Y coordinate
     * @param {string} [roomKey] - Room to test (default: the current room)
     * @returns {boolean} True if position is within boundary
     */
    checkBoundary(gridX, gridY, roomKey = this.currentRoom) {
        const room = this.rooms[roomKey];
        if (room && room.city) {
            // a stitched city: inside ANY district's own boundary — the
            // woodland between the districts is scenery
            return this.districtsAt(gridX, gridY, roomKey).some(at => {
                const boundary = this.rooms[at.room].boundary;
                return !boundary || this.isPointInPolygon(at.x + 0.5, at.y + 0.5, boundary);
            });
        }
        if (!room || !room.boundary) {
            return true;
        }

        return this.isPointInPolygon(gridX + 0.5, gridY + 0.5, room.boundary);
    }
}

/** Streaming grain: chunks are CHUNK x CHUNK cells; sprites exist STREAM_MARGIN cells beyond the view. */
RoomManager.CHUNK = 4;
RoomManager.STREAM_MARGIN = 3;
/** Most hidden sprites kept for reuse between chunk changes. */
RoomManager.POOL_MAX = 600;
/** The invisible tile a collision layer is painted with (TiledAdapter maps Tiled's collider-marker to it). */
RoomManager.COLLIDER = 'gk_blank';
