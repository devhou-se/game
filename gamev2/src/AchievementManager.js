/**
 * AchievementManager - tracks achievements. First one: "Paint the board" —
 * step on every reachable walkable tile across all rooms.
 *
 * Painted tiles are recorded per room as the player moves and persist across
 * reloads (localStorage). The DENOMINATOR is the reachable walkable tiles,
 * computed by a flood-fill from each room's starting position (spawn for the
 * start room, the transporter arrival cell for the others) — so unreachable
 * unblocked tiles don't inflate the total.
 */
class AchievementManager {
    constructor(scene) {
        this.scene = scene;
        this.STORE_KEY = 'gamev2_painted_tiles';
        this.painted = this.load();          // { room: Set("x,y") }
        this.reachable = {};                  // { room: Set("x,y") }  (the denominator)
        this.computeReachable();
        this._saveTimer = null;
    }

    load() {
        try {
            const raw = JSON.parse(localStorage.getItem(this.STORE_KEY) || '{}');
            const out = {};
            for (const r in raw) out[r] = new Set(raw[r]);
            return out;
        } catch (e) { return {}; }
    }

    save() {
        // throttle writes; the painted set only grows on new cells
        if (this._saveTimer) return;
        this._saveTimer = setTimeout(() => {
            this._saveTimer = null;
            try {
                const obj = {};
                for (const r in this.painted) obj[r] = [...this.painted[r]];
                localStorage.setItem(this.STORE_KEY, JSON.stringify(obj));
            } catch (e) { /* ignore */ }
        }, 800);
    }

    /** Reachable walkable tiles per room, via flood-fill from the start cells. */
    computeReachable() {
        const cfg = this.scene.config;
        const GS = this.scene.GRID_SIZE;
        const rooms = cfg.rooms || {};

        // seeds: spawn for the start room + every transporter ARRIVAL into a room
        const seeds = {};
        const addSeed = (room, x, y) => { (seeds[room] = seeds[room] || []).push([x, y]); };
        if (cfg.player) addSeed(cfg.player.startRoom, cfg.player.startX, cfg.player.startY);
        for (const rk in rooms) {
            for (const t of (rooms[rk].transporters || [])) {
                if (t.targetRoom != null && t.targetX != null && t.targetY != null) addSeed(t.targetRoom, t.targetX, t.targetY);
            }
        }

        for (const rk in rooms) {
            const room = rooms[rk];
            const floor = new Set(), coll = new Set();
            let W = 0, H = 0;
            for (const layer of (room.layers || [])) {
                for (const pos in layer.tiles) {
                    const [x, y] = pos.split(',').map(Number);
                    W = Math.max(W, x + 1); H = Math.max(H, y + 1);
                    if (layer.name === 'Floor') floor.add(pos);
                    if (layer.collision) coll.add(pos);
                }
            }
            const boundary = room.boundary || [];
            const inPoly = (x, y) => {
                if (boundary.length < 3) return true;
                const px = x + 0.5, py = y + 0.5; let inside = false;
                for (let i = 0, j = boundary.length - 1; i < boundary.length; j = i++) {
                    const xi = boundary[i][0], yi = boundary[i][1], xj = boundary[j][0], yj = boundary[j][1];
                    if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) inside = !inside;
                }
                return inside;
            };
            const walkable = (x, y) => x >= 0 && x < W && y >= 0 && y < H &&
                floor.has(`${x},${y}`) && !coll.has(`${x},${y}`) && inPoly(x, y);

            const reach = new Set();
            const q = [];
            for (const [sx, sy] of (seeds[rk] || [])) {
                if (walkable(sx, sy) && !reach.has(`${sx},${sy}`)) { reach.add(`${sx},${sy}`); q.push([sx, sy]); }
            }
            // fallback seed: first walkable cell, if no valid seed
            if (!q.length) {
                for (const k of floor) { const [x, y] = k.split(',').map(Number); if (walkable(x, y)) { reach.add(k); q.push([x, y]); break; } }
            }
            while (q.length) {
                const [x, y] = q.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    const nk = `${nx},${ny}`;
                    if (!reach.has(nk) && walkable(nx, ny)) { reach.add(nk); q.push([nx, ny]); }
                }
            }
            this.reachable[rk] = reach;
        }
    }

    /** Record a tile the player has stepped on. */
    markVisited(room, x, y) {
        if (!room) return;
        const set = this.painted[room] || (this.painted[room] = new Set());
        const k = `${x},${y}`;
        if (!set.has(k)) { set.add(k); this.save(); }
    }

    /** Progress for "Paint the board": overall + per-room (painted∩reachable / reachable). */
    paintProgress() {
        const perRoom = {}; let totVisited = 0, totReach = 0;
        for (const rk in this.reachable) {
            const reach = this.reachable[rk];
            const painted = this.painted[rk] || new Set();
            let hit = 0;
            for (const k of painted) if (reach.has(k)) hit++;
            perRoom[rk] = { painted: hit, total: reach.size };
            totVisited += hit; totReach += reach.size;
        }
        return {
            painted: totVisited,
            total: totReach,
            percent: totReach ? Math.floor(100 * totVisited / totReach) : 0,
            complete: totReach > 0 && totVisited >= totReach,
            perRoom
        };
    }
}
