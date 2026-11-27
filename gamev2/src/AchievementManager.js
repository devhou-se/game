/**
 * AchievementManager - tracks achievements. First one: "Paint the board" —
 * step on every reachable walkable tile across all rooms.
 *
 * Painted tiles are recorded per room as the player moves and persist across
 * reloads (localStorage). The DENOMINATOR is the reachable walkable tiles,
 * computed by a flood-fill from each room's starting position (spawn for the
 * start room, the transporter arrival cell for the others) — so unreachable
 * unblocked tiles don't inflate the total.
 *
 * Districts of a stitched city (issues #40/#41) are still counted and saved
 * per district in the district's own cells, so progress from before the
 * stitch stays valid — but they are flood-filled together as the one map they
 * now are, and a cell two districts share counts once, for the district that
 * draws it (computeCityReachable).
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

        const rm = this.scene.roomManager;
        for (const city of Object.values((rm && rm.cities) || {})) {
            this.computeCityReachable(city, seeds);
        }
    }

    /**
     * Food & drink achievements (issue #46), read live from the shop's
     * consumption counters (saved in its `gamev2_shop` blob):
     *   Taste Tester     — use every consumable in the catalogue at least once
     *   Regular Customer — eat or drink 25 things in total
     */
    consumptionProgress() {
        const shop = this.scene.shop;
        if (!shop) return [];
        const all = shop.consumables();
        const tried = all.filter(i => shop.used[i.id]).length;
        const total = all.reduce((sum, i) => sum + (shop.used[i.id] || 0), 0);
        const goal = AchievementManager.REGULAR_CUSTOMER;
        return [
            { name: 'Taste Tester', desc: 'Try every food and drink',
              value: tried, total: all.length, complete: all.length > 0 && tried >= all.length },
            { name: 'Regular Customer', desc: `Eat or drink ${goal} things`,
              value: Math.min(total, goal), total: goal, complete: total >= goal },
        ];
    }

    /**
     * Fishing achievement (issue #83), from the shop's `caught` counters:
     *   Big Catch — land a rare fish (Fishing.isRare: Unagi, Golden Koi)
     */
    fishingProgress() {
        const shop = this.scene.shop;
        if (!shop || typeof Fishing === 'undefined') return [];
        const rare = Fishing.CATCHES.filter(Fishing.isRare);
        const landed = rare.reduce((sum, c) => sum + (shop.caught[c.id] || 0), 0);
        return [
            { name: 'Big Catch', desc: `Land a rare fish (${rare.map(c => c.name).join(' or ')})`,
              value: Math.min(landed, 1), total: 1, complete: landed >= 1 },
        ];
    }

    /**
     * Stamp card achievement (issue #209), from the shop's `stamps`:
     *   Konbini Pilgrim — buy something at every konbini and discount store
     *   (the list is every store room in config, so a new town's count by themselves)
     */
    stampProgress() {
        const shop = this.scene.shop;
        return [Stamps.progress(this.scene.config, shop ? shop.stamps : {})];
    }

    /**
     * Career achievements (issue #226), from the shop's `career` (null until hired):
     *   First Paycheck     — merge a ticket on a shift
     *   Principal Engineer — climb every step of Career.LEVELS
     */
    careerProgress() {
        const shop = this.scene.shop;
        if (!shop || typeof Career === 'undefined') return [];
        const merged = shop.career ? shop.career.merged : 0;
        const step = Career.LEVELS.indexOf(Career.levelOf(merged)), top = Career.LEVELS.length - 1;
        return [
            { name: 'First Paycheck', desc: 'Merge a ticket at work',
              value: Math.min(merged, 1), total: 1, complete: merged >= 1 },
            { name: 'Principal Engineer', desc: 'Reach the top of the ladder',
              value: step, total: top, complete: step >= top },
        ];
    }

    /** Every achievement the shop's save feeds, in the order the overlay lists them. */
    itemProgress() {
        return this.consumptionProgress().concat(this.fishingProgress(), this.stampProgress(), this.careerProgress());
    }

    /** Record a tile the player has stepped on. */
    markVisited(room, x, y) {
        if (!room) return;
        const set = this.painted[room] || (this.painted[room] = new Set());
        const k = `${x},${y}`;
        if (!set.has(k)) { set.add(k); this.save(); }
    }

    /**
     * A stitched city is ONE walkable map: flood it whole (from every
     * district's seeds), then hand each reached cell to the district that
     * owns it, in that district's own coordinates.
     */
    computeCityReachable(city, seeds) {
        const rm = this.scene.roomManager;
        const floor = new Set(), coll = new Set();
        for (const layer of (rm.rooms[city.key].layers || [])) {
            for (const pos in layer.tiles) {
                if (layer.name === 'Floor') floor.add(pos);
                if (layer.collision) coll.add(pos);
            }
        }
        const walkable = (x, y) => floor.has(`${x},${y}`) && !coll.has(`${x},${y}`) &&
            rm.checkBoundary(x, y, city.key);

        const reach = new Set();
        const q = [];
        const add = (x, y) => {
            const k = `${x},${y}`;
            if (!reach.has(k) && walkable(x, y)) { reach.add(k); q.push([x, y]); }
        };
        for (const m of city.members) {
            for (const [sx, sy] of (seeds[m.key] || [])) add(sx + m.x, sy + m.y);
        }
        if (!q.length) {
            for (const k of floor) { const [x, y] = k.split(',').map(Number); add(x, y); if (q.length) break; }
        }
        while (q.length) {
            const [x, y] = q.pop();
            add(x + 1, y); add(x - 1, y); add(x, y + 1); add(x, y - 1);
        }

        for (const m of city.members) this.reachable[m.key] = new Set();
        for (const k of reach) {
            const [x, y] = k.split(',').map(Number);
            const at = rm.districtsAt(x, y, city.key)[0];
            this.reachable[at.room].add(`${at.x},${at.y}`);
        }

        // a shared cell painted (before the stitch) only in the district that
        // no longer owns it is the owner's now too
        for (const m of city.members) {
            for (const k of (this.painted[m.key] || [])) {
                const [x, y] = k.split(',').map(Number);
                const at = rm.districtsAt(x + m.x, y + m.y, city.key)[0];
                if (at && at.room !== m.key) this.markVisited(at.room, at.x, at.y);
            }
        }
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

AchievementManager.REGULAR_CUSTOMER = 25;
