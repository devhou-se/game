const DIRS = { n: [0, -1], s: [0, 1], e: [1, 0], w: [-1, 0] };
const baseOf = (key) => (key || '').replace(/_(front|back|side)$/, '');

const BIN_RE = /(^|[-_])(bin|dustbin|dumpster|trash|trashcan|rubbish|garbage|litter)([-_]|$)/i;

class WorldModel {
    static applyTiled(config, tmjFor) {
        for (const key of Object.keys(config.rooms)) {
            const tmj = tmjFor(key);
            if (!tmj) continue;
            const built = TiledAdapter.toRoom(tmj);
            const r = config.rooms[key];
            r.layers = built.layers;
            if (built.transporters.length) r.transporters = built.transporters;
            if (built.worldWidth) r.worldWidth = built.worldWidth;
            if (built.worldHeight) r.worldHeight = built.worldHeight;
            if (built.boundary) r.boundary = built.boundary;
        }
        return config;
    }

    static defaultDate(config) {
        return defaultGameDate(todayIso(), [...contentChangeDates(config)].sort());
    }

    constructor(config, env, state) {
        this.env = env;
        this.config = config;
        this.GRID_SIZE = config.game.gridSize;
        this.WORLD_WIDTH = config.game.worldWidth;
        this.WORLD_HEIGHT = config.game.worldHeight;
        this.cx = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        this.cy = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        this.roomManager = new RoomManager(this);
        this.roomManager.initializeRooms(config, this.cx, this.cy,
            this.WORLD_WIDTH / this.GRID_SIZE, this.WORLD_HEIGHT / this.GRID_SIZE);
        this.collisionSystem = new CollisionSystem(this);

        const s = Object.assign({
            room: config.player.startRoom, x: config.player.startX, y: config.player.startY,
            date: WorldModel.defaultDate(config), as: baseOf(config.player.sprite),
        }, state || {});
        this.date = s.date;
        this.as = s.as;
        this.livery = s.livery || null;
        this.player = this.character('you', s.x, s.y);
        this.player.isPlayer = true;
        this.enter(s.room, s.x, s.y);
    }

    state() {
        return { room: this.roomManager.currentRoom, x: this.player.gridX, y: this.player.gridY, date: this.date, as: this.as, livery: this.livery };
    }

    character(name, x, y, extra) {
        return Object.assign({
            name, gridX: x, gridY: y, isMoving: false,
            getTargetPosition() { return { x: this.gridX, y: this.gridY }; },
        }, extra);
    }

    exists(key) { return this.env.exists(key); }

    cells(key) { return this.env.sizeOf(key); }

    npcsIn(roomKey) {
        const opponent = this.as === 'damian' ? 'bailey' : 'damian';
        const list = [];
        for (const raw of this.config.rooms[roomKey].npcs || []) {
            const r = resolveNpc(raw, this.date);
            if (!r || baseOf(r.sprite) === this.as) continue;
            if (r.drinkingGameOpponent && baseOf(r.sprite) !== opponent) continue;
            list.push(this.character(r.name,
                r.gridX !== null ? r.gridX : this.cx + r.gridOffsetX,
                r.gridY !== null ? r.gridY : this.cy + r.gridOffsetY,
                { canInteract: true, dialogue: r.dialogue || [], photo: r.photo || null, posts: r.posts || null }));
        }
        return list;
    }

    enter(roomKey, x, y) {
        const rm = this.roomManager;
        if (!rm.rooms[roomKey]) throw new Error(`no room "${roomKey}" (try: rooms)`);
        rm.currentRoom = roomKey;
        const room = rm.rooms[roomKey];
        const st = (this.config.stations || {})[roomKey];
        this.livery = st ? TrainTravel.liveryFor(st, this.livery) : null;
        room.npcs = this.npcsIn(roomKey);
        rm.objectSprites = room.objects;
        rm.floorSprites = [];
        for (const layer of room.layers) {
            if (!layer.collision) continue;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (!this.exists(key)) continue;
                const [gridX, gridY] = xy.split(',').map(Number);
                const data = { layerCollision: true, gridX, gridY };
                rm.floorSprites.push({ getData: (k) => data[k] });
            }
        }
        this.player.gridX = x;
        this.player.gridY = y;
        this.w = (room.worldWidth || this.WORLD_WIDTH) / this.GRID_SIZE;
        this.h = (room.worldHeight || this.WORLD_HEIGHT) / this.GRID_SIZE;
        this.blocked = new Set(rm.floorSprites.map(s => s.getData('gridX') + ',' + s.getData('gridY')));
    }

    get room() { return this.roomManager.rooms[this.roomManager.currentRoom]; }
    get roomConfig() { return this.config.rooms[this.roomManager.currentRoom]; }

    canStep(fx, fy, tx, ty) {
        if (tx < 0 || ty < 0 || tx >= this.w || ty >= this.h) return false;
        return this.collisionSystem.checkCollision(this.player, tx, ty, fx, fy);
    }

    tilesAt(x, y) {
        const hits = [];
        for (const layer of this.room.layers) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                const [tx, ty] = xy.split(',').map(Number);
                if (tx > x || ty > y) continue;
                const [w, h] = (tx === x && ty === y) ? [1, 1] : this.cells(key);
                if (x < tx + w && y < ty + h) hits.push({ layer: layer.name, z: layer.z, collision: !!layer.collision, key, at: [tx, ty] });
            }
        }
        return hits;
    }

    interactions() {
        return Interactions.all(this.room, this.roomConfig, { sizeOf: (key) => this.cells(key), venues: Shop.VENUES });
    }

    interactionAt(x, y) {
        const covers = (i) => x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h;
        const all = this.interactions();
        const table = all.find(i => i.group === 'drinking-game' && covers(i));
        if (table) return table;
        const npc = this.room.npcs.find(n => n.gridX === x && n.gridY === y);
        if (npc) return { kind: 'npc', group: 'npc', npc };
        return ['shop', 'pond', 'clock'].map(g => all.find(i => i.group === g && covers(i))).find(Boolean) || null;
    }

    describe(i) {
        if (!i) return 'solid, nothing to interact with';
        if (i.kind === 'npc') {
            const n = i.npc;
            const lines = n.dialogue.length ? n.dialogue.map(l => `  "${l}"`).join('\n') : '  (nothing to say)';
            // the posts the lines came from, as the dialogue box captions them
            const from = [];
            n.dialogue.forEach((_, i) => {
                const post = postForLine(n.posts, i, n.dialogue.length);
                if (post && !from.includes(post)) from.push(post);
            });
            return `${n.name} says:\n${lines}` + (n.photo ? `\n  photo: assets/photos/${n.photo}.png` : '') +
                from.map(p => `\n  from: ${p.title}` + (postLink(p) ? ` <${p.url}>` : '')).join('');
        }
        if (i.group === 'shop') {
            const venue = Shop.VENUES[i.kind];
            const items = (this.config.items || Shop.DEFAULT_ITEMS).filter(venue.sells);
            return `opens the ${venue.title} shop: ` + items.map(it => `${it.name} ¥${it.price}`).join(', ');
        }
        if (i.kind === 'pond') return 'casts a fishing line (needs the fishing rod)';
        if (i.kind === 'clock') return 'opens the time-travel date picker';
        if (i.kind === 'drinking-game') return 'starts the izakaya drinking game';
    }

    station() { return (this.config.stations || {})[this.roomManager.currentRoom]; }

    onBoardCell() {
        const st = this.station();
        return !!st && st.board.some(([bx, by]) => bx === this.player.gridX && by === this.player.gridY);
    }

    step(dir) {
        const [dx, dy] = DIRS[dir];
        const p = this.player;
        const tx = p.gridX + dx, ty = p.gridY + dy;
        if (!this.canStep(p.gridX, p.gridY, tx, ty)) {
            return { moved: false, bumped: [tx, ty], interaction: this.interactionAt(tx, ty) };
        }
        p.gridX = tx; p.gridY = ty;
        const t = this.room.transporters.find(t => t.gridX === tx && t.gridY === ty);
        if (t) {
            const from = this.roomManager.currentRoom;
            this.enter(t.targetRoom, t.targetX, t.targetY);
            return { moved: true, transported: { from, to: t.targetRoom } };
        }
        return { moved: true, board: this.onBoardCell() };
    }

    path(gx, gy) {
        const p = this.player;
        const start = p.gridX + ',' + p.gridY, goal = gx + ',' + gy;
        const prev = new Map([[start, null]]);
        const queue = [[p.gridX, p.gridY]];
        const stops = new Set(this.room.transporters.map(t => t.gridX + ',' + t.gridY));
        while (queue.length) {
            const [x, y] = queue.shift();
            if (x + ',' + y === goal) break;
            if (stops.has(x + ',' + y) && x + ',' + y !== start) continue;
            for (const d of 'nsew') {
                const nx = x + DIRS[d][0], ny = y + DIRS[d][1], k = nx + ',' + ny;
                if (prev.has(k) || !this.canStep(x, y, nx, ny)) continue;
                prev.set(k, [x + ',' + y, d]);
                queue.push([nx, ny]);
            }
        }
        if (!prev.has(goal)) return null;
        const steps = [];
        for (let k = goal; prev.get(k); k = prev.get(k)[0]) steps.unshift(prev.get(k)[1]);
        return steps;
    }

    reachable() {
        const seen = new Set();
        const queue = [[this.player.gridX, this.player.gridY]];
        seen.add(queue[0].join(','));
        while (queue.length) {
            const [x, y] = queue.shift();
            for (const d of 'nsew') {
                const nx = x + DIRS[d][0], ny = y + DIRS[d][1], k = nx + ',' + ny;
                if (seen.has(k) || !this.canStep(x, y, nx, ny)) continue;
                seen.add(k);
                queue.push([nx, ny]);
            }
        }
        return seen;
    }

    drawOrder(roomKey) {
        const room = this.roomManager.rooms[roomKey];
        const meta = this.config.spriteMetadata || {};
        const ground = [], standing = [];
        room.layers.forEach((layer, order) => {
            if (layer.collision) return;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (!this.exists(key)) continue;
                const [x, y] = xy.split(',').map(Number);
                if (layer.z < 2) { ground.push({ key, x, y }); continue; }
                const depth = (y + this.cells(key)[1]) * 10 + (layer.z >= 7 ? 11 : 0) + ((meta[key] || {}).depthBias || 0);
                standing.push({ key, x, y, depth, order });
            }
        });
        standing.sort((a, b) => a.depth - b.depth || a.order - b.order || a.y - b.y || a.x - b.x);
        return ground.concat(standing);
    }

    lint(roomKey) {
        const room = this.roomManager.rooms[roomKey];
        const names = this.config.tileNames || {};
        const nm = (key) => names[key] || key;
        const K = (x, y) => x + ',' + y;
        const floor = new Set(), overFloor = new Set(), colliders = new Set();
        const objects = [];
        let W = 0, H = 0;
        const foot = (x, y, key) => {
            const [w, h] = this.cells(key);
            const cells = [];
            for (let a = 0; a < w; a++) for (let b = 0; b < h; b++) cells.push([x + a, y + b]);
            return { cells, w, h };
        };
        for (const layer of room.layers) {
            const z = layer.z || 0;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                const [x, y] = xy.split(',').map(Number);
                W = Math.max(W, x + 1); H = Math.max(H, y + 1);
                if (layer.name === 'Floor') floor.add(xy);
                if (layer.name === 'Over Floor') for (const [cx, cy] of foot(x, y, key).cells) overFloor.add(K(cx, cy));
                if (layer.collision) { colliders.add(xy); continue; }
                if (z >= 1 && layer.name !== 'Floor') objects.push(Object.assign({ layer: layer.name, z, x, y, key }, foot(x, y, key)));
            }
        }
        const doors = new Set(room.transporters.map(t => K(t.gridX, t.gridY)));
        const inside = (x, y) => !room.boundary || room.boundary.length < 3 ||
            this.roomManager.isPointInPolygon(x + 0.5, y + 0.5, room.boundary);
        const walkable = (x, y) => x >= 0 && x < W && y >= 0 && y < H && floor.has(K(x, y)) && !colliders.has(K(x, y)) && inside(x, y);

        let seed = [this.config.player.startX || 0, this.config.player.startY || 0];
        if (!walkable(...seed)) {
            const first = [...floor].map(c => c.split(',').map(Number)).sort((a, b) => a[0] - b[0] || a[1] - b[1]).find(c => walkable(...c));
            if (first) seed = first;
        }
        const reachable = new Set();
        if (walkable(...seed)) {
            const queue = [seed];
            reachable.add(K(...seed));
            while (queue.length) {
                const [cx, cy] = queue.shift();
                for (const [nx, ny] of [[cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]]) {
                    if (reachable.has(K(nx, ny)) || !walkable(nx, ny)) continue;
                    reachable.add(K(nx, ny));
                    queue.push([nx, ny]);
                }
            }
        }

        const errors = {}, warns = {};
        const push = (bag, kind, item) => (bag[kind] = bag[kind] || []).push(item);

        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!floor.has(K(x, y))) push(errors, 'floor-hole', K(x, y));

        // "definitely no rubbish bins!!" (issue #19): any bin / dumpster / trash sprite on any
        // layer is an error, so one can never be placed again. Whole-word match between - and _,
        // so office-cabinet is fine.
        for (const layer of room.layers) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (BIN_RE.test(String(key))) push(errors, 'rubbish-bin', `${String(key)} @${xy} (${layer.name})`);
            }
        }
        for (const xy of colliders) {
            const [x, y] = xy.split(',').map(Number);
            if (!(x >= 0 && x < W && y >= 0 && y < H)) push(errors, 'oob-collider', xy);
        }

        const covered = new Set();
        for (const o of objects) for (const [cx, cy] of o.cells) { covered.add(K(cx, cy)); covered.add(K(cx, cy - 1)); }
        const sortedColliders = [...colliders].map(c => c.split(',').map(Number)).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        for (const [x, y] of sortedColliders) if (!covered.has(K(x, y))) push(warns, 'stray-collision', K(x, y));

        for (const o of objects) {
            if (o.layer !== 'Collidables') continue;
            if (o.cells.some(([cx, cy]) => doors.has(K(cx, cy)))) continue;
            if (!o.cells.some(([cx, cy]) => colliders.has(K(cx, cy)))) push(errors, 'missing-collision', `${nm(o.key)} @${o.x},${o.y}`);
        }

        for (const o of objects) {
            if (o.z < 7 || o.h < 4) continue;
            let pavilion = o.cells.some(([cx, cy]) => overFloor.has(K(cx, cy)));
            for (let a = 0; a < o.w; a++) if (overFloor.has(K(o.x + a, o.y + o.h))) pavilion = true;
            if (pavilion) continue;
            let under = false;
            for (let a = 0; a < o.w; a++) {
                const c = K(o.x + a, o.y + o.h - 1);
                if (!colliders.has(c) && reachable.has(c)) under = true;
            }
            if (under) push(warns, 'under-overhead', `${nm(o.key)} @${o.x},${o.y} (${o.w}x${o.h})`);
        }

        const tops = {};
        for (const o of objects) if (o.z >= 7) (tops[o.key] = tops[o.key] || new Set()).add(K(o.x, o.y));
        for (const [key, cells] of Object.entries(tops)) {
            const seen = new Set();
            for (const c of cells) {
                if (seen.has(c)) continue;
                const comp = [], queue = [c];
                seen.add(c);
                while (queue.length) {
                    const cur = queue.shift();
                    comp.push(cur);
                    const [cx, cy] = cur.split(',').map(Number);
                    for (const nb of [K(cx + 1, cy), K(cx - 1, cy), K(cx, cy + 1), K(cx, cy - 1)]) {
                        if (cells.has(nb) && !seen.has(nb)) { seen.add(nb); queue.push(nb); }
                    }
                }
                if (comp.length > 15) push(warns, 'ground-on-tops', `${nm(key)} x${comp.length} contiguous (e.g. @${comp[0]})`);
            }
        }

        const isCanopy = (n) => (n.endsWith('-top') && (n.includes('sakura') || n.startsWith('tree-'))) || n === 'sakura-small';
        const isTrunk = (n) => n.includes('base') && (n.includes('sakura') || n.startsWith('tree-'));
        const depthOf = (z, y, h) => z < 2 ? -1000 : (y + h) * 10 + (z >= 7 ? 11 : 0);
        const canopies = objects.filter(o => o.z >= 7 && isCanopy(nm(o.key)));
        const trunks = objects.filter(o => o.layer === 'Collidables' && isTrunk(nm(o.key)));
        const cover = {};
        for (const o of canopies) for (const [cx, cy] of o.cells) (cover[K(cx, cy)] = cover[K(cx, cy)] || new Set()).add(`${nm(o.key)}@${o.x},${o.y}`);
        for (const [c, list] of Object.entries(cover)) if (list.size > 1) push(errors, 'canopy-overlap', `${c}: ${[...list].sort().join(' + ')}`);
        const trunkCells = new Set();
        for (const t of trunks) {
            const cells = new Set(t.cells.map(([cx, cy]) => K(cx, cy)));
            for (const c of cells) trunkCells.add(c);
            const td = depthOf(5, t.y, t.h);
            for (const o of canopies) {
                if (!o.cells.some(([cx, cy]) => cells.has(K(cx, cy)))) continue;
                const cd = depthOf(7, o.y, o.h);
                if (td > cd) push(errors, 'trunk-over-canopy', `${nm(t.key)}@${t.x},${t.y}(d${td}) over ${nm(o.key)}@${o.x},${o.y}(d${cd})`);
            }
        }
        for (const o of canopies) {
            if (nm(o.key) === 'sakura-small') continue;
            let trunk = false;
            for (let a = 0; a < o.w; a++) if (trunkCells.has(K(o.x + a, o.y + o.h))) trunk = true;
            if (!trunk) push(warns, 'floating-canopy', `${nm(o.key)} @${o.x},${o.y}`);
        }

        return { room: roomKey, width: W, height: H, objects: objects.length, colliders: colliders.size, floor: floor.size, errors, warns };
    }

    survey(dates) {
        dates = dates || [this.date];
        const problems = [];
        const reach = {};
        const saved = this.state();
        const rooms = this.roomManager.rooms;
        const arrivals = {};
        const arrive = (room, x, y, via) => (arrivals[room] = arrivals[room] || []).push({ x, y, via });
        arrive(this.config.player.startRoom, this.config.player.startX, this.config.player.startY, 'spawn');
        for (const [k, r] of Object.entries(rooms)) {
            for (const t of r.transporters) {
                if (!rooms[t.targetRoom]) problems.push({ room: k, x: t.gridX, y: t.gridY, text: `targets missing room "${t.targetRoom}"` });
                else arrive(t.targetRoom, t.targetX, t.targetY, `${k} ${t.gridX},${t.gridY}`);
            }
        }
        for (const [k, st] of Object.entries(this.config.stations || {})) arrive(k, st.arrive[0], st.arrive[1], 'train');
        for (const k of Object.keys(this.config.rooms)) {
            reach[k] = new Set();
            if (!arrivals[k]) { problems.push({ room: k, text: 'nothing leads here' }); continue; }
            for (const a of arrivals[k]) {
                this.enter(k, a.x, a.y);
                if (this.blocked.has(a.x + ',' + a.y) || !this.roomManager.checkBoundary(a.x, a.y)) {
                    problems.push({ room: k, x: a.x, y: a.y, text: `arrival from ${a.via} lands on a blocked cell` });
                    continue;
                }
                for (const c of this.reachable()) reach[k].add(c);
            }
            this.enter(k, arrivals[k][0].x, arrivals[k][0].y);
            for (const t of this.room.transporters) {
                if (!reach[k].has(t.gridX + ',' + t.gridY)) problems.push({ room: k, x: t.gridX, y: t.gridY, text: `transporter to ${t.targetRoom} cannot be walked to` });
            }
        }
        const seen = new Set();
        for (const date of dates) {
            this.date = date;
            for (const k of Object.keys(this.config.rooms)) {
                if (!arrivals[k]) continue;
                this.enter(k, arrivals[k][0].x, arrivals[k][0].y);
                for (const n of this.room.npcs) {
                    const id = `${k} ${n.gridX},${n.gridY} ${n.name}`;
                    if (seen.has(id)) continue;
                    const near = 'nsew'.split('').some(d => reach[k].has((n.gridX + DIRS[d][0]) + ',' + (n.gridY + DIRS[d][1])));
                    const bad = this.blocked.has(n.gridX + ',' + n.gridY) ? 'stands on a collider' : !near ? 'cannot be walked up to' : null;
                    if (!bad) continue;
                    seen.add(id);
                    problems.push({ room: k, x: n.gridX, y: n.gridY, date, text: `${n.name} ${bad} (${date})` });
                }
            }
        }
        this.date = saved.date;
        this.enter(saved.room, saved.x, saved.y);
        return { problems, reach };
    }
}

if (typeof window !== 'undefined') window.WorldModel = WorldModel;
