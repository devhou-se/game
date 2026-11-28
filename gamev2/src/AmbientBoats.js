/**
 * AmbientBoats - boats that periodically drift along the waterways (issue #29).
 *
 * The water half of AmbientTrains. Any room whose Tiled map contains straight
 * moat tiles gets an ambient boat: every so often one fades in at one end of a
 * clear stretch of water, is poled slowly to the other end with a gentle bob,
 * and fades out again (a moat is a closed channel, so unlike a train a boat
 * cannot leave by the screen edge).
 *
 * Waterways come from the map DATA, never from coordinates, in two ways:
 *   - moat tiles: a "run" is a line of consecutive cells holding the same
 *     plain `moat-<side>` tile. Rock tiles, corner pieces and gaps (the bridge
 *     over Tokyo's south moat) end a run, so a boat never crosses rocks, a
 *     bridge or the stone bank;
 *   - a room's `waterways` list in config.json (issue #61), written by the
 *     room's generator: `{ axis: 'h'|'v', from, to, row|col, rows|cols,
 *     under: [[a, b], ...] }` in cells - a canal or river of any water tiles,
 *     `from`..`to` along it and `rows` (or `cols`) wide. `under` lists the
 *     cells where a bridge deck lies over the water: the boat carries on
 *     beneath and is not drawn there (cropped at the deck's edge), so it goes
 *     under the bridge and under whoever stands on it. An end on the room's
 *     edge is open - the boat comes in from off the map, as a train does.
 *     Declared runs that meet end to end are one run (joinRuns, issue #68):
 *     in a stitched city a canal that carries on into the next district is
 *     one waterway, and a boat sails across the seam instead of fading at it.
 *     Frozen water simply declares no waterway.
 * The strip of open water is measured from the tiles' own pixels (waterBand /
 * stackBand), so the boat sits in the water whatever the bank art looks like,
 * and water hidden behind scenery standing in front of it is left out
 * (clearWater), so a boat is never half covered by a wall on the near bank.
 * What is left decides which hulls fit (AmbientBoats.HULLS): Tokyo's north
 * moat shows only a 32px lane above the palace wall, which takes the skiff
 * and not the punt (issue #62).
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

        for (const line of Object.values(lines)) {
            const band = this.waterBand(line.key, line.axis);
            if (!band) continue;

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
                // keep only the water that scenery standing in front leaves in view
                const whole = {
                    axis: line.axis, from, to,
                    band0: line.cross * GS + crossOff + band[0],
                    band1: line.cross * GS + crossOff + band[1],
                };
                const run = this.fit(whole) && this.fit(this.clearWater(whole));
                if (run) runs.push(run);
                start = i;
            }
        }
        return runs.concat(this.declaredRuns(roomKey));
    }

    /**
     * A run with the hulls it can carry (`hulls`: keys of AmbientBoats.HULLS
     * narrow and short enough for it), or null when no boat fits at all.
     */
    fit(run) {
        const hulls = Object.keys(AmbientBoats.HULLS).filter(hull => {
            const size = AmbientBoats.size(hull);
            return run.band1 - run.band0 >= size.across && run.to - run.from >= size.along + AmbientBoats.MIN_TRAVEL;
        });
        return hulls.length ? Object.assign(run, { hulls }) : null;
    }

    /**
     * The waterways a room declares in config.json (`rooms.<Room>.waterways`,
     * see the header) as runs. In a stitched city each district's list is
     * moved to the district's place. A run gets `under` (pixel spans along it
     * where a bridge hides the boat) and `open` ([start, end]: that end is on
     * the room's edge, so the boat sails in / out there instead of fading).
     * Runs that meet end to end are joined (joinRuns) before the water left
     * in view is measured and the hulls are fitted, so those are of the whole
     * waterway.
     */
    declaredRuns(roomKey) {
        const scene = this.scene;
        const GS = scene.GRID_SIZE;
        const room = scene.roomManager.rooms[roomKey];
        const configRooms = (scene.config && scene.config.rooms) || {};
        const members = room.city ? room.city.members : [{ key: roomKey, x: 0, y: 0 }];
        const runs = [];
        for (const m of members) {
            for (const w of ((configRooms[m.key] || {}).waterways || [])) {
                const h = w.axis !== 'v';
                const cross0 = (h ? w.row + m.y : w.col + m.x), n = (h ? w.rows : w.cols) || 1;
                const off = h ? m.x : m.y;
                const under = (w.under || []).map(([a, b]) => [(a + off) * GS, (b + 1 + off) * GS]);
                // measure the water across the channel on the first cell no bridge covers
                let sample = w.from + off;
                while (under.some(([a, b]) => sample * GS >= a && sample * GS < b)) sample++;
                const stack = [];
                for (let i = 0; i < n; i++) stack.push(this.groundTile(room, h ? sample : cross0 + i, h ? cross0 + i : sample));
                const band = this.stackBand(stack, h ? 'h' : 'v');
                if (!band) continue;
                const from = (w.from + off) * GS, to = (w.to + 1 + off) * GS;
                const length = h ? room.worldWidth : room.worldHeight;
                runs.push({
                    axis: h ? 'h' : 'v', from, to, under,
                    open: [from <= 0, to >= length],
                    band0: cross0 * GS + band[0], band1: cross0 * GS + band[1],
                });
            }
        }
        return AmbientBoats.joinRuns(runs).map(r => this.fit(this.clearWater(r))).filter(Boolean);
    }

    /**
     * Runs that meet end to end, as one run each (issue #68: a district's
     * canal carried on by its neighbour's). Two runs join when they lie on
     * the same axis, one's `to` is the other's `from`, and the water they
     * share across the channel (the overlap of their bands) is at least
     * `across` px wide: the narrowest hull's width unless given. The bands
     * are not compared for equality, since each district measures its own
     * and a few pixels of bank art may differ. The joined run keeps the
     * first's `from` and `open[0]`, the second's `to` and `open[1]`, the band
     * they share and both `under` lists, and stands where its first part
     * stood; this repeats until nothing joins, so three in a row become one.
     * Runs that do not join come back as they were, in their order. Pure:
     * `runs` is not changed.
     */
    static joinRuns(runs, across = Math.min(...Object.keys(AmbientBoats.HULLS).map(h => AmbientBoats.size(h).across))) {
        const out = runs.slice();
        const shared = (a, b) => [Math.max(a.band0, b.band0), Math.min(a.band1, b.band1)];
        for (let i = 0; i < out.length; i++) {
            const a = out[i];
            const j = out.findIndex(b => b !== a && b.axis === a.axis && b.from === a.to && shared(a, b)[1] - shared(a, b)[0] >= across);
            if (j < 0) continue;
            const b = out[j], [band0, band1] = shared(a, b);
            out[i] = Object.assign({}, a, {
                to: b.to, band0, band1,
                open: [!!(a.open || [])[0], !!(b.open || [])[1]],
                under: (a.under || []).concat(b.under || []),
            });
            out.splice(j, 1);
            i = -1;                                       // from the top: the joined run may meet another
        }
        return out;
    }

    /** The topmost flat (ground / water) tile drawn on a cell: its texture key, or null. */
    groundTile(room, x, y) {
        let key = null;
        for (const layer of (room.layers || [])) {
            if (layer.collision || (layer.z || 0) >= 2) continue;
            const k = (layer.tiles || {})[`${x},${y}`];
            if (k && this.scene.textures.exists(k)) key = k;
        }
        return key;
    }

    /**
     * The open water across a channel several tiles wide: `keys` are the tiles
     * of one cross-section, bank to bank, drawn a cell each. Returns [start,
     * end) pixel offsets from the first tile's edge: the longest run of pixel
     * rows (columns, for a 'v' channel) that are the water colour along the
     * WHOLE tile, so a rock rim that bulges anywhere in the tile is outside
     * it. Null when a tile is missing or no water is found.
     */
    stackBand(keys, axis) {
        if (!keys.length || keys.some(k => !k)) return null;
        const id = axis + '|' + keys.join('|');
        if (id in this.bandCache) return this.bandCache[id];
        const GS = this.scene.GRID_SIZE, STEP = AmbientBoats.ART.PX;
        const masks = keys.map(k => this.alphaMask(k));
        let best = null;
        if (masks.every(Boolean)) {
            const at = (mask, along, across) => {       // cell pixels -> texture pixel colour
                const x = Math.floor((axis === 'h' ? along : across) / GS * mask.width);
                const y = Math.floor((axis === 'h' ? across : along) / GS * mask.height);
                const i = (y * mask.width + x) * 4;
                return mask.data[i + 3] === 255 ? (mask.data[i] << 16) | (mask.data[i + 1] << 8) | mask.data[i + 2] : -1;
            };
            const count = {};
            const lines = [];                            // per pixel line across: the colours along the tile
            masks.forEach(mask => {
                for (let c = 0; c < GS; c++) {
                    const line = [];
                    for (let a = STEP / 2; a < GS; a += STEP) {
                        const v = at(mask, a, c);
                        line.push(v);
                        if (v >= 0) count[v] = (count[v] || 0) + 1;
                    }
                    lines.push(line);
                }
            });
            const water = Number(Object.keys(count).sort((a, b) => count[b] - count[a])[0]);
            for (let i = 0, start = -1; i <= lines.length; i++) {
                if (i < lines.length && lines[i].every(v => v === water)) { if (start < 0) start = i; continue; }
                if (start >= 0 && (!best || i - start > best[1] - best[0])) best = [start, i];
                start = -1;
            }
        }
        return (this.bandCache[id] = best);
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
     * Runs with enough water on camera for a boat to be seen travelling - its
     * own length plus MIN_TRAVEL, so one is not wasted off-screen or on a
     * sliver of a run at the screen's edge - else all. The strip under the HUD
     * bar does not count as on camera.
     */
    candidateRuns() {
        const cam = this.scene.cameras.main;
        const view = cam.worldView;
        const top = view.y + (typeof UI !== 'undefined' ? UI.HUD_HEIGHT : 0) / cam.zoom;
        const seen = this.runs.filter(r => {
            const h = r.axis === 'h';
            const need = Math.min(...r.hulls.map(hull => AmbientBoats.size(hull).along)) + AmbientBoats.MIN_TRAVEL;
            const along = Math.min(r.to, h ? view.right : view.bottom) - Math.max(r.from, h ? view.x : top);
            return along >= need && r.band0 >= (h ? top : view.x) && r.band1 <= (h ? view.bottom : view.right);
        });
        return seen.length ? seen : this.runs;
    }

    /**
     * One boat along one run, end to end. All three arguments are optional
     * (random when omitted) — tests and the console pass them to stage a
     * particular crossing: `run` is an entry of this.runs, `dir` is +1
     * (right/down) or -1 (left/up), `livery` a key of AmbientBoats.LIVERIES
     * (ignored when its hull does not fit the run).
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
        const fits = Object.keys(AmbientBoats.LIVERIES).filter(l => run.hulls.includes(AmbientBoats.hullOf(l)));
        livery = fits.includes(livery) ? livery : pick(fits);

        const facing = run.axis === 'h' ? (dir > 0 ? 'right' : 'left') : (dir > 0 ? 'down' : 'up');
        const key = this.ensureTexture(livery, facing);
        const boat = this.active = scene.add.image(0, 0, key);
        const along = run.axis === 'h' ? boat.width : boat.height;
        const across = run.axis === 'h' ? boat.height : boat.width;

        // travel between the run's ends, on a lane somewhere in the open water.
        // At a closed end the whole sprite stays inside the run and fades; at
        // an open one (the room's edge) it starts / finishes just off the map.
        const open = run.open || [false, false];
        const a0 = run.from + (open[0] ? -along / 2 : along / 2);
        const a1 = run.to + (open[1] ? along / 2 : -along / 2);
        let start = dir > 0 ? a0 : a1;
        const end = dir > 0 ? a1 : a0;
        let fadeIn = !open[dir > 0 ? 0 : 1];
        const fadeOut = !open[dir > 0 ? 1 : 0];
        // a waterway longer than the screen: do not make the player wait while
        // the boat crosses water nobody can see - it sets off just out of view
        const view = scene.cameras.main.worldView;
        const lo = (run.axis === 'h' ? view.x : view.y) - along;
        const hi = (run.axis === 'h' ? view.right : view.bottom) + along;
        if (lo < run.to && hi > run.from) {
            // (not when that would leave it less than MIN_TRAVEL to go: a run
            // that ends just outside the view keeps its whole length)
            const near = dir > 0 ? lo : hi;
            if ((dir > 0 ? near > start : near < start) && Math.abs(end - near) >= AmbientBoats.MIN_TRAVEL) {
                start = near;
                fadeIn = false;
            }
        }
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
            boat.setAlpha(Math.min(1, fadeIn ? t * dist / fade : 1, fadeOut ? (1 - t) * dist / fade : 1));
            this.hideUnder(boat, run, a, along);
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

    /**
     * Draw only the part of the boat that is not under a bridge: the sprite is
     * cropped at the deck's edge (the larger piece, should a deck be shorter
     * than the boat) and hidden while it is wholly underneath.
     */
    hideUnder(boat, run, a, along) {
        if (!run.under || !run.under.length) return;
        const lo = a - along / 2, hi = a + along / 2;
        let pieces = [[lo, hi]];
        for (const [u0, u1] of run.under) {
            pieces = pieces.flatMap(([p0, p1]) => (u1 <= p0 || u0 >= p1) ? [[p0, p1]]
                : [[p0, Math.min(p1, u0)], [Math.max(p0, u1), p1]].filter(([q0, q1]) => q1 - q0 > 0));
        }
        const piece = pieces.sort((p, q) => (q[1] - q[0]) - (p[1] - p[0]))[0];
        boat.setVisible(!!piece);
        if (!piece) return;
        if (run.axis === 'h') boat.setCrop(piece[0] - lo, 0, piece[1] - piece[0], boat.height);
        else boat.setCrop(0, piece[0] - lo, boat.width, piece[1] - piece[0]);
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

    /** On-screen size of a boat sprite of one hull: `along` its heading, `across` it. */
    static size(hull = 'punt') {
        const A = AmbientBoats.HULLS[hull], PX = AmbientBoats.ART.PX;
        return { along: (A.WAKE + A.LENGTH + 2) * PX, across: (A.BEAM + 2) * PX };
    }

    /** The hull a livery is painted on. */
    static hullOf(livery) {
        return (AmbientBoats.LIVERIES[livery] || {}).hull || 'punt';
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
        const pal = AmbientBoats.LIVERIES[livery];
        const A = Object.assign({ PX: AmbientBoats.ART.PX }, AmbientBoats.HULLS[AmbientBoats.hullOf(livery)]);
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
        // everything aboard is sized off the widest half-beam: 4 on the punt
        // (the figures below are drawn for it), 2 on the skiff
        const half = Math.max(...A.HALF_BEAM);
        const inner = half - 2;                                 // deck half-width inside outline + rim
        const deck0 = mid - inner, deck1 = mid + inner;         // deck rows inside the rim
        const narrow = (dv) => Math.sign(dv) * Math.round(Math.abs(dv) * half / 4);

        // wake: ripples spreading out behind the stern
        for (const [h, dv, a] of [[-1, -3, 0.9], [-1, 3, 0.9], [-2, 0, 0.9], [-3, -2, 0.7], [-3, 2, 0.7],
                                  [-4, 0, 0.5], [-5, -3, 0.4], [-5, 3, 0.4]]) {
            if (h >= -A.WAKE) put(h, mid + narrow(dv), `rgba(142,194,250,${a})`);
        }

        // seat thwarts
        for (const h of (pal.thwarts || [])) {
            for (let v = deck0; v <= deck1; v++) put(h, v, pal.rim);
        }

        // seated passengers: shoulders across the beam, head in the middle
        const shoulder = Math.max(1, inner);
        (pal.passengers || []).forEach(([h, robe, hair]) => {
            for (let v = mid - shoulder; v <= mid + shoulder; v++) { put(h, v, robe); put(h + 1, v, robe); }
            for (let v = mid - shoulder + 1; v <= mid + shoulder - 1; v++) { put(h, v, hair); put(h + 1, v, hair); }
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
        for (const [h, dv] of [[0, 2], [-1, 2], [-2, 3], [-3, 3], [-4, 4]]) {
            if (h >= -A.WAKE) put(h, mid + Math.max(1, dv - (4 - half)), pal.pole);
        }
        const bh = A.HAT + 1, R = A.HAT;                        // hat radius: 2 on the punt, 1 on the skiff
        for (let dh = -R; dh <= R; dh++) {
            for (let dv = -R; dv <= R; dv++) {
                if (R > 1 && Math.abs(dh) === R && Math.abs(dv) === R) continue;
                const ring = Math.max(Math.abs(dh), Math.abs(dv));
                put(bh + dh, mid + dv, ring === R ? pal.hatDark : (ring === 0 ? pal.hatLight : pal.hat));
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
AmbientBoats.MIN_TRAVEL = 128;    // a run must let a boat move at least this far (px): four cells for either hull
AmbientBoats.FADE = 56;           // px of travel spent fading in / out at each end
AmbientBoats.BOB = 1.5;           // px of sway across the heading
AmbientBoats.BOB_PERIOD = 2600;   // ms per sway
AmbientBoats.BANK_GAP = 4;        // px kept clear between hull and bank when picking a lane
AmbientBoats.COVER_LIMIT = 0.25;  // a lane hidden by scenery for more than this share of a run is not open water

/** One art pixel is PX screen pixels, matching the 16px-native tiles at 64px. */
AmbientBoats.ART = { PX: 4 };

/**
 * Hull shapes, in art pixels. A run takes every hull that fits its open water
 * (AmbientBoats.fit), so a narrow lane still gets a boat.
 */
AmbientBoats.HULLS = {
    // the pleasure punt: 116 x 44px on screen
    punt: {
        WAKE: 5,          // wake drawn behind the stern
        LENGTH: 22,       // stern to bow
        BEAM: 9,          // widest point
        HAT: 2,           // radius of the boatman's straw hat
        // half-width of the hull at each step from stern (0) to bow (LENGTH-1)
        HALF_BEAM: [3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 1, 0],
    },
    // a one-man skiff for narrow water: 80 x 28px (Tokyo's north moat, issue #62)
    skiff: {
        WAKE: 4,
        LENGTH: 14,
        BEAM: 5,
        HAT: 1,
        HALF_BEAM: [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
    },
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
    // skiffs: a lone boatman, one with a basket of the day's catch amidships
    skiff: {
        hull: 'skiff',
        outline: '#3b2a26', rim: '#b9774a', deck: '#8f5c3c', deckDark: '#7a4c33',
        hat: '#e2c275', hatLight: '#f3d890', hatDark: '#9c7a3c', pole: '#d8c89a',
        thwarts: [7],
        passengers: [[8, '#c9b48a', '#7fa3c4']],
    },
    skiffGreen: {
        hull: 'skiff',
        outline: '#1f3330', rim: '#5f9c7c', deck: '#c9a66b', deckDark: '#a88650',
        hat: '#e2c275', hatLight: '#f3d890', hatDark: '#9c7a3c', pole: '#d8c89a',
        thwarts: [6, 10],
    },
};

if (typeof window !== 'undefined') window.AmbientBoats = AmbientBoats;
