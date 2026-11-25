/**
 * AmbientBoats - boats that periodically drift along the waterways (issue #29).
 *
 * The water half of AmbientTrains. Any room whose Tiled map contains straight
 * moat tiles gets an ambient boat: every so often one fades in at one end of a
 * clear stretch of water, is poled slowly to the other end with a gentle bob,
 * and fades out again (a moat is a closed channel, so unlike a train a boat
 * cannot leave by the screen edge).
 *
 * Waterways come from the map DATA, never from coordinates: a "run" is a line
 * of consecutive cells holding the same plain `moat-<side>` tile. Rock tiles,
 * corner pieces and gaps (the bridge over Tokyo's south moat) end a run, so a
 * boat never crosses rocks, a bridge or the stone bank. The strip of open
 * water inside the tile is measured from the tile's own pixels (waterBand),
 * so the boat sits in the water whatever the tile's bank art looks like, and
 * water hidden behind scenery standing in front of it is left out
 * (clearWater), so a boat is never half covered by a wall on the near bank.
 *
 * Boats are decoration only: no collision, no interaction. They draw one step
 * above the flat ground/water layers and below everything Y-sorted.
 *
 * Art: there is no hand-drawn boat yet, so the textures are drawn procedurally
 * (buildTexture) on the tile art's 4x pixel grid. To replace one with real
 * art, load a texture under the same key — `boat-<livery>-<right|left|down|up>`
 * — before the first boat appears; ensureTexture() only draws what is missing.
 */
class AmbientBoats {
    constructor(scene) {
        this.scene = scene;
        this.active = null;
        this.tween = null;
        this.timer = null;
        this.runs = [];
        this.bandCache = {};
        this.maskCache = {};
        this.onRoomChange(scene.roomManager.currentRoom);
    }

    // ------------------------------------------------------------ waterways

    /**
     * Clear stretches of water in a room, in world pixels:
     * [{ axis: 'h'|'v', from, to, band0, band1 }] — `from`/`to` bound the run
     * along its axis, `band0`/`band1` bound the open water across it.
     */
    findRuns(roomKey) {
        const scene = this.scene;
        const GS = scene.GRID_SIZE;
        const room = scene.roomManager.rooms[roomKey];
        const runs = [];
        if (!room) return runs;

        // cells of each plain straight moat tile, grouped by the line they lie on
        const lines = {};
        for (const layer of (room.layers || [])) {
            for (const xy in (layer.tiles || {})) {
                const key = layer.tiles[xy];
                const m = AmbientBoats.WATER_TILE.exec(key);
                if (!m || !scene.textures.exists(key)) continue;
                const [x, y] = xy.split(',').map(Number);
                const axis = (m[1] === 'north' || m[1] === 'south') ? 'h' : 'v';
                const id = `${key}|${axis === 'h' ? y : x}`;
                const line = lines[id] || (lines[id] = { key, axis, cross: axis === 'h' ? y : x, cells: [] });
                line.cells.push(axis === 'h' ? x : y);
            }
        }

        const size = AmbientBoats.size();
        for (const line of Object.values(lines)) {
            const band = this.waterBand(line.key, line.axis);
            if (!band || band[1] - band[0] < size.across) continue;   // channel too narrow

            // where the tile's sprite sits relative to its cell (see RoomManager.loadLayer)
            const tex = scene.textures.get(line.key).getSourceImage();
            const cfg = scene.getSpriteConfig(line.key);
            const alongSize = line.axis === 'h' ? tex.width : tex.height;
            const alongOff = GS / 2 - (line.axis === 'h' ? cfg.anchorX * tex.width : cfg.anchorY * tex.height);
            const crossOff = GS / 2 - (line.axis === 'h' ? cfg.anchorY * tex.height : cfg.anchorX * tex.width);

            line.cells.sort((a, b) => a - b);
            let start = 0;
            for (let i = 1; i <= line.cells.length; i++) {
                if (i < line.cells.length && line.cells[i] === line.cells[i - 1] + 1) continue;
                const from = line.cells[start] * GS + alongOff;
                const to = line.cells[i - 1] * GS + alongOff + alongSize;
                if (to - from >= size.along + AmbientBoats.MIN_TRAVEL) {
                    // keep only the water that scenery standing in front leaves in view
                    const run = this.clearWater({
                        axis: line.axis, from, to,
                        band0: line.cross * GS + crossOff + band[0],
                        band1: line.cross * GS + crossOff + band[1],
                    });
                    if (run.band1 - run.band0 >= size.across) runs.push(run);
                }
                start = i;
            }
        }
        return runs;
    }

    /**
     * The open-water strip across a moat tile, as [start, end) pixel offsets
     * into the tile image: the longest unbroken stretch of the tile's dominant
     * colour along its middle cross-section. Null when it cannot be read.
     */
    waterBand(key, axis) {
        if (key in this.bandCache) return this.bandCache[key];
        const textures = this.scene.textures;
        const img = textures.get(key).getSourceImage();
        const n = axis === 'h' ? img.height : img.width;
        const mid = Math.floor((axis === 'h' ? img.width : img.height) / 2);

        const line = [];
        const count = {};
        for (let i = 0; i < n; i++) {
            const c = axis === 'h' ? textures.getPixel(mid, i, key) : textures.getPixel(i, mid, key);
            const v = (c && c.alpha === 255) ? c.color : -1;
            line.push(v);
            if (v >= 0) count[v] = (count[v] || 0) + 1;
        }
        const water = Number(Object.keys(count).sort((a, b) => count[b] - count[a])[0]);

        let best = null;
        for (let i = 0, start = -1; i <= n; i++) {
            if (i < n && line[i] === water) { if (start < 0) start = i; continue; }
            if (start >= 0 && (!best || i - start > best[1] - best[0])) best = [start, i];
            start = -1;
        }
        return (this.bandCache[key] = best);
    }

    /**
     * Narrow a run's band to the water that is actually in view. The tile's
     * water strip can be partly covered by Y-sorted scenery drawn over it (the
     * palace wall on the near bank of Tokyo's north moat hides the lower half
     * of the channel), and a boat there would show as half a boat. Any lane
     * across the band that scenery covers for more than COVER_LIMIT of the
     * run's length counts as hidden; the widest stretch of lanes left is the
     * band. The caller drops the run when that is narrower than a boat.
     */
    clearWater(run) {
        const scene = this.scene;
        const STEP = AmbientBoats.ART.PX;
        const h = run.axis === 'h';
        const lanes = Math.floor((run.band1 - run.band0) / STEP);
        const steps = Math.floor((run.to - run.from) / STEP);
        const covered = new Uint8Array(lanes * steps);
        const boatDepth = scene.roomManager.calculateLayerDepth(1) + 1;
        const x0 = h ? run.from : run.band0, y0 = h ? run.band0 : run.from;
        const x1 = h ? run.to : run.band1, y1 = h ? run.band1 : run.to;

        // every piece of art the room draws, as data — not the live sprites:
        // a stitched city only has sprites near the camera
        for (const art of scene.roomManager.standingArt()) {
            if (art.depth <= boatDepth) continue;
            const b = { x: art.left, y: art.top, width: art.width, height: art.height,
                        right: art.left + art.width, bottom: art.top + art.height };
            if (b.right <= x0 || b.x >= x1 || b.bottom <= y0 || b.y >= y1) continue;
            const mask = this.alphaMask(art.key);
            if (!mask) continue;
            for (let l = 0; l < lanes; l++) {
                for (let s = 0; s < steps; s++) {
                    const along = run.from + (s + 0.5) * STEP, across = run.band0 + (l + 0.5) * STEP;
                    const wx = h ? along : across, wy = h ? across : along;
                    if (wx < b.x || wx >= b.right || wy < b.y || wy >= b.bottom) continue;
                    const tx = Math.floor((wx - b.x) / b.width * mask.width);
                    const ty = Math.floor((wy - b.y) / b.height * mask.height);
                    if (mask.data[(ty * mask.width + tx) * 4 + 3] > 127) covered[l * steps + s] = 1;
                }
            }
        }

        let best = [0, 0];
        for (let l = 0, start = -1; l <= lanes; l++) {
            let n = 0;
            if (l < lanes) for (let s = 0; s < steps; s++) n += covered[l * steps + s];
            if (l < lanes && n <= steps * AmbientBoats.COVER_LIMIT) { if (start < 0) start = l; continue; }
            if (start >= 0 && l - start > best[1] - best[0]) best = [start, l];
            start = -1;
        }
        // an untouched band keeps its exact edges; a trimmed one snaps to the lane grid
        const full = best[0] === 0 && best[1] === lanes;
        return Object.assign({}, run, full ? {} : {
            band0: run.band0 + best[0] * STEP,
            band1: run.band0 + best[1] * STEP,
        });
    }

    /** A texture's pixels ({ width, height, data: RGBA }), read once per key; null if unreadable. */
    alphaMask(key) {
        if (key in this.maskCache) return this.maskCache[key];
        let mask = null;
        try {
            const img = this.scene.textures.get(key).getSourceImage();
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            mask = ctx.getImageData(0, 0, img.width, img.height);
        } catch (e) {
            mask = null;
        }
        return (this.maskCache[key] = mask);
    }

    // ------------------------------------------------------------ scheduling

    onRoomChange(roomKey) {
        this.clear();
        this.runs = this.findRuns(roomKey);
        // first boat comes fairly quickly so the water feels alive on arrival
        if (this.runs.length) this.schedule(3000 + Math.random() * 7000);
    }

    schedule(delay) {
        this.timer = this.scene.time.delayedCall(delay, () => this.cross());
    }

    /**
     * Runs with a boat's length of water on camera (so a boat is not wasted
     * off-screen), else all. The strip under the HUD bar does not count as on
     * camera.
     */
    candidateRuns() {
        const cam = this.scene.cameras.main;
        const view = cam.worldView;
        const top = view.y + (typeof UI !== 'undefined' ? UI.HUD_HEIGHT : 0) / cam.zoom;
        const need = AmbientBoats.size().along;
        const seen = this.runs.filter(r => {
            const h = r.axis === 'h';
            const along = Math.min(r.to, h ? view.right : view.bottom) - Math.max(r.from, h ? view.x : top);
            return along >= need && r.band0 >= (h ? top : view.x) && r.band1 <= (h ? view.bottom : view.right);
        });
        return seen.length ? seen : this.runs;
    }

    /**
     * One boat along one run, end to end. All three arguments are optional
     * (random when omitted) — tests and the console pass them to stage a
     * particular crossing: `run` is an entry of this.runs, `dir` is +1
     * (right/down) or -1 (left/up), `livery` a key of AmbientBoats.LIVERIES.
     */
    cross(run, dir, livery) {
        const scene = this.scene;
        if (!this.runs.length) return;
        if (this.timer) { this.timer.remove(); this.timer = null; }
        if (this.tween) { this.tween.stop(); this.tween = null; }
        if (this.active) { this.active.destroy(); this.active = null; }

        const pick = (list) => list[Math.floor(Math.random() * list.length)];
        run = run || pick(this.candidateRuns());
        dir = dir || (Math.random() < 0.5 ? 1 : -1);
        livery = AmbientBoats.LIVERIES[livery] ? livery : pick(Object.keys(AmbientBoats.LIVERIES));

        const facing = run.axis === 'h' ? (dir > 0 ? 'right' : 'left') : (dir > 0 ? 'down' : 'up');
        const key = this.ensureTexture(livery, facing);
        const boat = this.active = scene.add.image(0, 0, key);
        const along = run.axis === 'h' ? boat.width : boat.height;
        const across = run.axis === 'h' ? boat.height : boat.width;

        // travel between the run's ends (whole sprite stays inside the run),
        // on a lane somewhere in the open water
        const a0 = run.from + along / 2, a1 = run.to - along / 2;
        const start = dir > 0 ? a0 : a1, end = dir > 0 ? a1 : a0;
        const slack = Math.max(0, (run.band1 - run.band0 - across) / 2 - AmbientBoats.BANK_GAP);
        const lane = (run.band0 + run.band1) / 2 + (Math.random() * 2 - 1) * slack;
        const dist = Math.abs(end - start);
        const fade = Math.min(AmbientBoats.FADE, dist / 2);

        // just above the flat ground/water layers (z<2), below everything Y-sorted
        boat.setDepth(scene.roomManager.calculateLayerDepth(1) + 1);
        boat.setAlpha(0);

        const place = (t, elapsed) => {
            const a = start + (end - start) * t;
            const bob = Math.sin(elapsed / AmbientBoats.BOB_PERIOD * Math.PI * 2) * AmbientBoats.BOB;
            if (run.axis === 'h') boat.setPosition(a, lane + bob);
            else boat.setPosition(lane + bob, a);
            boat.setAlpha(Math.min(1, t * dist / fade, (1 - t) * dist / fade));
        };
        place(0, 0);

        this.tween = scene.tweens.addCounter({
            from: 0, to: 1,
            duration: dist / AmbientBoats.SPEED,
            ease: 'Linear',
            onUpdate: (tween) => place(tween.getValue(), tween.elapsed),
            onComplete: () => {
                if (this.active) this.active.destroy();
                this.active = null;
                this.tween = null;
                this.schedule(15000 + Math.random() * 25000);
            },
        });
    }

    clear() {
        if (this.timer) { this.timer.remove(); this.timer = null; }
        if (this.tween) { this.tween.stop(); this.tween = null; }
        if (this.active) { this.active.destroy(); this.active = null; }
    }

    // ------------------------------------------------------------ art

    /** Texture key for a livery + facing, drawing it first if nothing is loaded under that key. */
    ensureTexture(livery, facing) {
        const key = `boat-${livery}-${facing}`;
        if (!this.scene.textures.exists(key)) {
            this.scene.textures.addCanvas(key, AmbientBoats.buildTexture(livery, facing));
        }
        return key;
    }

    /** On-screen size of a boat sprite: `along` its heading, `across` it. */
    static size() {
        const A = AmbientBoats.ART;
        return { along: (A.WAKE + A.LENGTH + 2) * A.PX, across: (A.BEAM + 2) * A.PX };
    }

    /**
     * Draw one boat, seen from above, as a canvas.
     *
     * The boat is laid out in hull space — u runs from the tail of the wake to
     * the bow, v across the beam — then turned to its facing and shaded in
     * screen space, so the shadow always falls on the screen-south side
     * whichever way the boat points.
     */
    static buildTexture(livery, facing) {
        const A = AmbientBoats.ART;
        const pal = AmbientBoats.LIVERIES[livery];
        const U = A.WAKE + A.LENGTH + 2, V = A.BEAM + 2;       // 1px margin all round
        const mid = (V - 1) / 2;
        const grid = [];                                        // grid[u][v] = colour | undefined
        for (let u = 0; u < U; u++) grid.push(new Array(V));
        const hu = (u) => u - 1 - A.WAKE;                       // u -> position along the hull
        const inHull = (u, v) => {
            const h = hu(u);
            return h >= 0 && h < A.LENGTH && Math.abs(v - mid) <= A.HALF_BEAM[h];
        };
        const edge = (u, v) => !inHull(u - 1, v) || !inHull(u + 1, v) || !inHull(u, v - 1) || !inHull(u, v + 1);
        const put = (h, v, colour) => {
            const u = h + 1 + A.WAKE;
            if (u >= 0 && u < U && v >= 0 && v < V) grid[u][v] = colour;
        };

        // hull: dark outline, gunwale rim, plank deck
        for (let u = 0; u < U; u++) {
            for (let v = 0; v < V; v++) {
                if (!inHull(u, v)) continue;
                if (edge(u, v)) grid[u][v] = pal.outline;
                else if (edge(u - 1, v) || edge(u + 1, v) || edge(u, v - 1) || edge(u, v + 1)) grid[u][v] = pal.rim;
                else grid[u][v] = (hu(u) % 4 === 2) ? pal.deckDark : pal.deck;   // plank seams
            }
        }
        const deck0 = mid - 2, deck1 = mid + 2;                 // deck rows inside the rim

        // wake: ripples spreading out behind the stern
        for (const [h, dv, a] of [[-1, -3, 0.9], [-1, 3, 0.9], [-2, 0, 0.9], [-3, -2, 0.7], [-3, 2, 0.7],
                                  [-4, 0, 0.5], [-5, -3, 0.4], [-5, 3, 0.4]]) {
            put(h, mid + dv, `rgba(142,194,250,${a})`);
        }

        // seat thwarts
        for (const h of (pal.thwarts || [])) {
            for (let v = deck0; v <= deck1; v++) put(h, v, pal.rim);
        }

        // seated passengers: shoulders across the beam, head in the middle
        (pal.passengers || []).forEach(([h, robe, hair]) => {
            for (let v = mid - 2; v <= mid + 2; v++) { put(h, v, robe); put(h + 1, v, robe); }
            for (let v = mid - 1; v <= mid + 1; v++) { put(h, v, hair); put(h + 1, v, hair); }
        });

        // roofed cabin (yakatabune): tiled roof with a ridge and corner lanterns
        if (pal.cabin) {
            const [h0, h1] = pal.cabin;
            for (let h = h0; h <= h1; h++) {
                for (let v = mid - 3; v <= mid + 3; v++) {
                    const border = h === h0 || h === h1 || v === mid - 3 || v === mid + 3;
                    put(h, v, border ? pal.roofDark : (v === mid ? pal.roofLight : pal.roof));
                }
            }
            for (const h of [h0, h1]) for (const v of [mid - 3, mid + 3]) put(h, v, pal.lantern);
        }

        // boatman at the stern under a straw hat, sculling pole trailing in the wake
        for (const [h, dv] of [[0, 2], [-1, 2], [-2, 3], [-3, 3], [-4, 4]]) put(h, mid + dv, pal.pole);
        const bh = 3;
        for (let dh = -2; dh <= 2; dh++) {
            for (let dv = -2; dv <= 2; dv++) {
                if (Math.abs(dh) === 2 && Math.abs(dv) === 2) continue;
                const ring = Math.max(Math.abs(dh), Math.abs(dv));
                put(bh + dh, mid + dv, ring === 2 ? pal.hatDark : (ring === 1 ? pal.hat : pal.hatLight));
            }
        }

        // turn hull space into screen space for this facing
        const horiz = facing === 'right' || facing === 'left';
        const W = horiz ? U : V, H = horiz ? V : U;
        const at = (x, y) => {
            if (x < 0 || y < 0 || x >= W || y >= H) return undefined;
            const u = horiz ? x : y, v = horiz ? y : x;
            return grid[(facing === 'left' || facing === 'up') ? U - 1 - u : u][v];
        };

        const canvas = document.createElement('canvas');
        canvas.width = W * A.PX;
        canvas.height = H * A.PX;
        const ctx = canvas.getContext('2d');
        for (let y = 0; y < H; y++) {
            for (let x = 0; x < W; x++) {
                let colour = at(x, y);
                // the hull's shadow on the water, one pixel to the screen-south
                if (!colour && at(x, y - 1) === pal.outline) colour = 'rgba(31,31,59,0.45)';
                if (!colour) continue;
                ctx.fillStyle = colour;
                ctx.fillRect(x * A.PX, y * A.PX, A.PX, A.PX);
            }
        }
        return canvas;
    }
}

/** Plain straight moat tiles are open water; `-rocks` and `-corner` variants are not. */
AmbientBoats.WATER_TILE = /^moat-(north|south|east|west)_/;

AmbientBoats.SPEED = 0.03;        // px/ms — a lazy punt, ~half a tile a second
AmbientBoats.MIN_TRAVEL = 96;     // a run must let a boat move at least this far (px)
AmbientBoats.FADE = 56;           // px of travel spent fading in / out at each end
AmbientBoats.BOB = 1.5;           // px of sway across the heading
AmbientBoats.BOB_PERIOD = 2600;   // ms per sway
AmbientBoats.BANK_GAP = 4;        // px kept clear between hull and bank when picking a lane
AmbientBoats.COVER_LIMIT = 0.25;  // a lane hidden by scenery for more than this share of a run is not open water

/** Boat geometry in art pixels (PX screen pixels each, matching the 16px-native tiles at 64px). */
AmbientBoats.ART = {
    PX: 4,
    WAKE: 5,          // wake drawn behind the stern
    LENGTH: 22,       // stern to bow
    BEAM: 9,          // widest point
    // half-width of the hull at each step from stern (0) to bow (LENGTH-1)
    HALF_BEAM: [3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 1, 0],
};

/** Liveries: hull colours plus what is aboard. Colours sit in the tile art's palette range. */
AmbientBoats.LIVERIES = {
    // plain wooden punt carrying two passengers
    wood: {
        outline: '#3b2a26', rim: '#b9774a', deck: '#8f5c3c', deckDark: '#7a4c33',
        hat: '#e2c275', hatLight: '#f3d890', hatDark: '#9c7a3c', pole: '#d8c89a',
        thwarts: [8, 12],
        passengers: [[9, '#b5535a', '#2b2236'], [13, '#4f7fb0', '#5a3a2a']],
    },
    // red-lacquered pleasure boat with a tiled cabin roof and lanterns
    lacquer: {
        outline: '#3a1c24', rim: '#d0524a', deck: '#a8623f', deckDark: '#8f5136',
        hat: '#e2c275', hatLight: '#f3d890', hatDark: '#9c7a3c', pole: '#d8c89a',
        cabin: [7, 15], roof: '#4c8c7a', roofLight: '#7fbf9f', roofDark: '#2f5d5a', lantern: '#f3d890',
    },
    // white hire boat with a blue stripe, one passenger up front
    white: {
        outline: '#2d3350', rim: '#e9eef2', deck: '#5d86c2', deckDark: '#4a70a8',
        hat: '#e2c275', hatLight: '#f3d890', hatDark: '#9c7a3c', pole: '#d8c89a',
        thwarts: [8, 16],
        passengers: [[11, '#e0b354', '#2b2236']],
    },
};

if (typeof window !== 'undefined') window.AmbientBoats = AmbientBoats;
