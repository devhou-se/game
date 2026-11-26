/**
 * AmbientTrams - a streetcar that runs a room's tram line (issue #219).
 *
 * AmbientTrains sends station liveries along `train-track*` rows. A tram line
 * is declared instead, in the room's config (`rooms.<Room>.tramways`), so a
 * room with no `tramways` gets nothing and costs nothing:
 *
 *   { "row": 21,                       // the rail row (the tram's wheels stand on it)
 *     "from": 0, "to": 55,             // first and last rail cell (optional: the `tram-rail-*` cells of the row)
 *     "sprite": "sapporo-streetcar_0_0",   // or a list, taken in turn (two cars sharing one track)
 *     "speed": 160,                    // px a second (default)
 *     "headway": 30,                   // seconds between one car finishing and the next setting off
 *     "stops": [12, { "x": 40, "dwell": 6 }],   // cells it stops at, centred on the cell
 *     "dwell": 4 }                     // seconds at a stop (default)
 *
 * One car is on a line at a time. It runs west to east, waits `headway`, and
 * the next runs east to west, mirrored. An end on the room's edge is open:
 * the car comes in from, and leaves to, off the map. Any other end is a
 * terminus and the car fades in / out standing on the last of the rails, as a
 * passing train does at the end of the Palace track.
 *
 * Like a passing train it is decoration: it adds nothing to collision and
 * never stops for anyone. Its depth is that of something standing on the
 * rail row, one under a character on that row - so a player on the rails is
 * drawn over the car as it passes through, one a row above is behind it, and
 * the night grade (a layer over the whole world) dims it like everything else.
 *
 * The timetable is a pure function of time (plan / at), so the car is where
 * the clock says whether or not anyone is looking; off camera it is hidden
 * and only that arithmetic runs.
 */
class AmbientTrams {
    constructor(scene) {
        this.scene = scene;
        this.lines = [];
        this.onRoomChange(scene.roomManager.currentRoom);
    }

    /** The room's lines, moved to the district's place in a stitched city. */
    declared(roomKey) {
        const scene = this.scene, GS = scene.GRID_SIZE;
        const room = scene.roomManager.rooms[roomKey];
        if (!room) return [];
        const configRooms = (scene.config && scene.config.rooms) || {};
        const members = room.city ? room.city.members : [{ key: roomKey, x: 0, y: 0 }];
        const cols = Math.round((room.worldWidth || scene.WORLD_WIDTH) / GS);
        const lines = [];
        for (const m of members) {
            for (const def of ((configRooms[m.key] || {}).tramways || [])) {
                const line = AmbientTrams.line(def, room.layers, m, cols);
                if (line) lines.push(line);
            }
        }
        return lines;
    }

    onRoomChange(roomKey) {
        this.clear();
        this.lines = this.declared(roomKey).map((line, i) => ({
            line, trip: 0, plan: null, image: null, t: 0,
            // the first car comes soon, and two lines do not set off together
            wait: 2000 + Math.random() * 4000 + i * 1500,
        }));
    }

    /** Send a car now on line `index` (testing); `dir` 1 east, -1 west. */
    cross(index = 0, dir) {
        const state = this.lines[index];
        if (!state) return null;
        if (state.image) { state.image.destroy(); state.image = null; }
        return this.depart(state, dir);
    }

    depart(state, dir) {
        const scene = this.scene, line = state.line;
        const key = line.sprites[state.trip % line.sprites.length];
        if (!scene.textures.exists(key)) { state.wait = line.headway * 1000; return null; }
        const tex = scene.textures.get(key).getSourceImage();
        const room = scene.roomManager.rooms[scene.roomManager.currentRoom];
        state.plan = AmbientTrams.plan(line, {
            GS: scene.GRID_SIZE, width: tex.width, worldWidth: room.worldWidth || scene.WORLD_WIDTH,
            dir: dir || AmbientTrams.direction(state.trip),
        });
        state.t = 0;
        state.trip++;
        const img = scene.add.image(state.plan.fromX, (line.row + 1) * scene.GRID_SIZE - tex.height, key);
        img.setOrigin(0, 0);
        img.setFlipX(state.plan.dir < 0);   // the art heads east
        img.setDepth(scene.roomManager.yDepth(AmbientTrams.depthAt(line.row)));
        state.image = img;
        this.show(state);
        return img;
    }

    /** Every frame (GameScene.update): `delta` ms since the last. */
    update(delta) {
        if (!this.lines.length) return;
        for (const state of this.lines) {
            if (!state.image) {
                state.wait -= delta;
                if (state.wait <= 0) this.depart(state);
                continue;
            }
            state.t += delta;
            if (state.t >= state.plan.duration) {
                state.image.destroy();
                state.image = null;
                state.wait = state.line.headway * 1000;
                continue;
            }
            this.show(state);
        }
    }

    /** Put the car where the timetable says, hidden when the camera cannot see it. */
    show(state) {
        const img = state.image, at = AmbientTrams.at(state.plan, state.t);
        const view = this.scene.cameras.main.worldView;
        img.x = Math.round(at.x);
        const seen = at.alpha > 0 && img.x < view.right && img.x + img.width > view.x &&
            img.y < view.bottom && img.y + img.height > view.y;
        img.setVisible(seen);
        if (seen) img.setAlpha(at.alpha);
    }

    clear() {
        for (const state of this.lines) if (state.image) state.image.destroy();
        this.lines = [];
    }
}

AmbientTrams.SPEED = 160;     // px a second
AmbientTrams.HEADWAY = 30;    // seconds
AmbientTrams.DWELL = 4;       // seconds
AmbientTrams.RAIL = /^tram-rail-(h|cross)/;

/** Odd trips run back the way the last one came. */
AmbientTrams.direction = (trip) => (trip % 2 === 0 ? 1 : -1);

/**
 * Depth units (RoomManager.yDepth) of a car on rail row `row`: with the things
 * standing on that row, one under a character there (feet (row + 1) * 10 + 5) -
 * the passing train's rule on a level crossing, without its cap of 48 (a
 * train is kept under the buildings beside its embankment; a tram is in the
 * street and sorts like anything else on it).
 */
AmbientTrams.depthAt = (row) => (row + 1) * 10 + 4;

/**
 * A declared tramway as the runtime wants it, or null when it cannot run:
 * `{ row, from, to, sprites, speed, headway, dwell, stops: [{ x, dwell }] }`
 * in the room's cells, moved by `offset` ({x, y}: the district's place in a
 * stitched city). With no `from` / `to` the line is the row's `tram-rail-*`
 * cells in `layers`. Stops off the line are dropped; a line shorter than
 * three cells is not a line.
 */
AmbientTrams.line = (def, layers, offset, cols) => {
    if (!def || !Number.isInteger(def.row)) return null;
    const dx = (offset && offset.x) || 0, dy = (offset && offset.y) || 0;
    const row = def.row + dy;
    let from = Number.isInteger(def.from) ? def.from + dx : null;
    let to = Number.isInteger(def.to) ? def.to + dx : null;
    if (from === null || to === null) {
        let lo = null, hi = null;
        for (const layer of (layers || [])) {
            for (const xy in (layer.tiles || {})) {
                if (!AmbientTrams.RAIL.test(layer.tiles[xy])) continue;
                const [x, y] = xy.split(',').map(Number);
                if (y !== row) continue;
                lo = lo === null ? x : Math.min(lo, x);
                hi = hi === null ? x : Math.max(hi, x);
            }
        }
        if (lo === null) return null;
        if (from === null) from = lo;
        if (to === null) to = hi;
    }
    if (to - from < 2) return null;
    const sprites = (Array.isArray(def.sprite) ? def.sprite : [def.sprite]).filter((k) => typeof k === 'string' && k);
    if (!sprites.length) return null;
    const positive = (v, fallback) => (Number.isFinite(v) && v > 0 ? v : fallback);
    const dwell = positive(def.dwell, AmbientTrams.DWELL);
    const stops = (def.stops || [])
        .map((s) => (typeof s === 'number' ? { x: s } : s))
        .filter((s) => s && Number.isInteger(s.x))
        .map((s) => ({ x: s.x + dx, dwell: positive(s.dwell, dwell) }))
        .filter((s) => s.x >= from && s.x <= to)
        .sort((a, b) => a.x - b.x);
    return {
        row, from, to, sprites, stops, dwell,
        speed: positive(def.speed, AmbientTrams.SPEED),
        headway: positive(def.headway, AmbientTrams.HEADWAY),
        open: [from <= 0, Number.isInteger(cols) ? to >= cols - 1 : false],
    };
};

/**
 * One trip's timetable. `opts`: { GS, width (the car's art, px), worldWidth,
 * dir }. Returns { dir, fromX, toX, westX, eastX, fade, open, legs, duration }
 * where x is the car's LEFT edge and a leg is { t0, t1, x0, x1, easeIn,
 * easeOut } (ms; x0 === x1 is a stop). The car pulls away from and draws up
 * to a stop or a terminus (eased), and runs at `speed` through an open end.
 */
AmbientTrams.plan = (line, opts) => {
    const { GS, width, worldWidth } = opts, dir = opts.dir < 0 ? -1 : 1;
    const [openW, openE] = line.open || [false, false];
    const westX = openW ? -width : line.from * GS;
    const eastX = openE ? worldWidth : (line.to + 1) * GS - width;
    const fromX = dir > 0 ? westX : eastX, toX = dir > 0 ? eastX : westX;
    const lo = Math.min(westX, eastX), hi = Math.max(westX, eastX);
    // a stop: the car's middle over the middle of the cell, kept on the line
    const stops = line.stops
        .map((s) => ({ x: Math.max(lo, Math.min(hi, (s.x + 0.5) * GS - width / 2)), dwell: s.dwell * 1000 }))
        .filter((s) => (s.x - fromX) * dir > 0 && (toX - s.x) * dir > 0)
        .sort((a, b) => (a.x - b.x) * dir);
    const legs = [];
    let t = 0, x = fromX, easeIn = !(dir > 0 ? openW : openE);
    const run = (x1, easeOut) => {
        const cruise = Math.abs(x1 - x) / line.speed * 1000;
        // an eased end costs time, so the car never goes faster than `speed` for long
        const t1 = t + cruise * (1 + 0.25 * (easeIn ? 1 : 0) + 0.25 * (easeOut ? 1 : 0));
        legs.push({ t0: t, t1, x0: x, x1, easeIn, easeOut });
        t = t1; x = x1;
    };
    for (const stop of stops) {
        if (stop.x !== x) run(stop.x, true);
        legs.push({ t0: t, t1: t + stop.dwell, x0: x, x1: x, easeIn: false, easeOut: false });
        t += stop.dwell;
        easeIn = true;
    }
    run(toX, !(dir > 0 ? openE : openW));
    return { dir, fromX, toX, westX, eastX, fade: width / 2, open: [openW, openE], legs, duration: t };
};

/**
 * Where the car of a plan is `ms` into its trip: { x, stopped, alpha, done }.
 * Alpha is 1 except near a terminus (a closed end), where the car fades over
 * half its length, as a passing train does.
 */
AmbientTrams.at = (plan, ms) => {
    const t = Math.max(0, Math.min(plan.duration, ms));
    let leg = plan.legs[plan.legs.length - 1];
    for (const l of plan.legs) { if (t < l.t1) { leg = l; break; } }
    let u = leg.t1 > leg.t0 ? (t - leg.t0) / (leg.t1 - leg.t0) : 1;
    if (leg.easeIn && leg.easeOut) u = u * u * (3 - 2 * u);
    else if (leg.easeIn) u = u * u * (2 - u);
    else if (leg.easeOut) u = 1 - (1 - u) * (1 - u) * (1 + u);
    const x = leg.x0 + (leg.x1 - leg.x0) * u;
    const alpha = Math.max(0, Math.min(1,
        plan.open[0] ? 1 : (x - plan.westX) / plan.fade,
        plan.open[1] ? 1 : (plan.eastX - x) / plan.fade));
    return { x, stopped: leg.x0 === leg.x1, alpha, done: ms >= plan.duration };
};

if (typeof window !== 'undefined') window.AmbientTrams = AmbientTrams;
