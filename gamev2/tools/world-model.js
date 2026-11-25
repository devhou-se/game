const DIRS = { n: [0, -1], s: [0, 1], e: [1, 0], w: [-1, 0] };
const baseOf = (key) => (key || '').replace(/_(front|back|side)$/, '');

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

    static today() {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
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
            date: WorldModel.today(), as: baseOf(config.player.sprite),
        }, state || {});
        this.date = s.date;
        this.as = s.as;
        this.player = this.character('you', s.x, s.y);
        this.player.isPlayer = true;
        this.enter(s.room, s.x, s.y);
    }

    state() {
        return { room: this.roomManager.currentRoom, x: this.player.gridX, y: this.player.gridY, date: this.date, as: this.as };
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
                { canInteract: true, dialogue: r.dialogue || [], photo: r.photo || null }));
        }
        return list;
    }

    enter(roomKey, x, y) {
        const rm = this.roomManager;
        if (!rm.rooms[roomKey]) throw new Error(`no room "${roomKey}" (try: rooms)`);
        rm.currentRoom = roomKey;
        const room = rm.rooms[roomKey];
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
            return `${n.name} says:\n${lines}` + (n.photo ? `\n  photo: assets/photos/${n.photo}.png` : '');
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

    survey() {
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
            for (const n of this.room.npcs) {
                const near = 'nsew'.split('').some(d => reach[k].has((n.gridX + DIRS[d][0]) + ',' + (n.gridY + DIRS[d][1])));
                if (this.blocked.has(n.gridX + ',' + n.gridY)) problems.push({ room: k, x: n.gridX, y: n.gridY, text: `${n.name} stands on a collider (${this.date})` });
                else if (!near) problems.push({ room: k, x: n.gridX, y: n.gridY, text: `${n.name} cannot be walked up to (${this.date})` });
            }
        }
        this.enter(saved.room, saved.x, saved.y);
        return { problems, reach };
    }
}

if (typeof window !== 'undefined') window.WorldModel = WorldModel;
