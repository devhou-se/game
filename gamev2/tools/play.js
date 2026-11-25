#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const GV2 = path.dirname(__dirname);
const SESSION = path.join(os.tmpdir(), 'gamev2-play-' +
    crypto.createHash('sha1').update(GV2).digest('hex').slice(0, 8) + '.json');

const ctx = vm.createContext({ console, URLSearchParams, location: { search: '' } });
for (const f of ['utils/ConfigCodec.js', 'utils/NpcStates.js', 'utils/Interactions.js', 'systems/TiledAdapter.js',
    'systems/RoomManager.js', 'systems/CollisionSystem.js', 'Shop.js']) {
    vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), ctx, { filename: f });
}
const { decodeConfig, resolveNpc, contentChangeDates, Interactions, TiledAdapter, RoomManager, CollisionSystem, Shop } =
    vm.runInContext('({decodeConfig, resolveNpc, contentChangeDates, Interactions, TiledAdapter, RoomManager, CollisionSystem, Shop})', ctx);

const DIRS = { n: [0, -1], s: [0, 1], e: [1, 0], w: [-1, 0] };
const ALIAS = { up: 'n', down: 's', left: 'w', right: 'e', north: 'n', south: 's', east: 'e', west: 'w' };
const baseOf = (key) => (key || '').replace(/_(front|back|side)$/, '');
const out = (s) => process.stdout.write(s + '\n');

class World {
    constructor(state) {
        const config = decodeConfig(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')));
        for (const key of Object.keys(config.rooms)) {
            const file = path.join(GV2, 'tiled', key.toLowerCase() + '.tmj');
            if (!fs.existsSync(file)) continue;
            const built = TiledAdapter.toRoom(JSON.parse(fs.readFileSync(file, 'utf8')));
            const r = config.rooms[key];
            r.layers = built.layers;
            if (built.transporters.length) r.transporters = built.transporters;
            if (built.worldWidth) r.worldWidth = built.worldWidth;
            if (built.worldHeight) r.worldHeight = built.worldHeight;
            if (built.boundary) r.boundary = built.boundary;
        }
        this.config = config;
        this.GRID_SIZE = config.game.gridSize;
        this.WORLD_WIDTH = config.game.worldWidth;
        this.WORLD_HEIGHT = config.game.worldHeight;
        this.cx = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        this.cy = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);
        this.sizes = {};

        this.roomManager = new RoomManager(this);
        this.roomManager.initializeRooms(config, this.cx, this.cy,
            this.WORLD_WIDTH / this.GRID_SIZE, this.WORLD_HEIGHT / this.GRID_SIZE);
        this.collisionSystem = new CollisionSystem(this);

        const today = new Date();
        const iso = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') +
            '-' + String(today.getDate()).padStart(2, '0');
        const s = Object.assign({
            room: config.player.startRoom, x: config.player.startX, y: config.player.startY,
            date: iso, as: baseOf(config.player.sprite),
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

    exists(key) {
        return fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
    }

    cells(key) {
        if (this.sizes[key]) return this.sizes[key];
        let w = 1, h = 1;
        try {
            const b = Buffer.alloc(24);
            const fd = fs.openSync(path.join(GV2, 'assets', 'sprites', key + '.png'), 'r');
            fs.readSync(fd, b, 0, 24, 0);
            fs.closeSync(fd);
            w = Math.max(1, Math.round(b.readUInt32BE(16) / 64));
            h = Math.max(1, Math.round(b.readUInt32BE(20) / 64));
        } catch (e) {}
        return (this.sizes[key] = [w, h]);
    }

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
}

const GLYPH = { shop: '$', pond: '~', clock: '?', 'drinking-game': 'D' };

function draw(world, x0, y0, x1, y1) {
    const p = world.player;
    const special = new Set();
    for (const i of world.interactions()) {
        for (let x = i.x; x < i.x + i.w; x++) for (let y = i.y; y < i.y + i.h; y++) special.add(x + ',' + y);
    }
    const board = new Set(((world.station() || {}).board || []).map(c => c.join(',')));
    const lines = [];
    const notes = [];
    for (let y = y0; y <= y1; y++) {
        let row = String(y).padStart(3) + ' ';
        for (let x = x0; x <= x1; x++) {
            const k = x + ',' + y;
            const npc = world.room.npcs.find(n => n.gridX === x && n.gridY === y);
            const t = world.room.transporters.find(t => t.gridX === x && t.gridY === y);
            let c;
            if (x < 0 || y < 0 || x >= world.w || y >= world.h) c = ' ';
            else if (p.gridX === x && p.gridY === y) c = '@';
            else if (npc) { c = npc.name[0].toUpperCase(); notes.push(`${c} ${npc.name} at ${x},${y}`); }
            else if (t) { c = '>'; notes.push(`> ${x},${y} to ${t.targetRoom} ${t.targetX},${t.targetY}${t.hidden ? ' (hidden)' : ''}`); }
            else if (board.has(k)) { c = 'T'; notes.push(`T ${x},${y} train boarding`); }
            else if (special.has(k)) {
                const i = world.interactionAt(x, y);
                c = i ? GLYPH[i.group] : (world.blocked.has(k) ? '#' : '.');
                if (i) notes.push(`${c} ${x},${y} ${i.kind}`);
            }
            else if (world.blocked.has(k) || !world.roomManager.checkBoundary(x, y)) c = '#';
            else c = '.';
            row += c;
        }
        lines.push(row);
    }
    const ruler = (f) => '    ' + Array.from({ length: x1 - x0 + 1 }, (_, i) => f(x0 + i)).join('');
    const head = [ruler(x => x % 10 === 0 ? String(Math.floor(x / 10) % 10) : ' '), ruler(x => String(((x % 10) + 10) % 10))];
    return head.concat(lines, [...new Set(notes)]).join('\n');
}

function describe(world, i) {
    if (!i) return 'solid, nothing to interact with';
    if (i.kind === 'npc') {
        const n = i.npc;
        const lines = n.dialogue.length ? n.dialogue.map(l => `  "${l}"`).join('\n') : '  (nothing to say)';
        return `${n.name} says:\n${lines}` + (n.photo ? `\n  photo: assets/photos/${n.photo}.png` : '');
    }
    if (i.group === 'shop') {
        const venue = Shop.VENUES[i.kind];
        const items = (world.config.items || Shop.DEFAULT_ITEMS).filter(venue.sells);
        return `opens the ${venue.title} shop: ` + items.map(it => `${it.name} ¥${it.price}`).join(', ');
    }
    if (i.kind === 'pond') return 'casts a fishing line (needs the fishing rod)';
    if (i.kind === 'clock') return 'opens the time-travel date picker';
    if (i.kind === 'drinking-game') return 'starts the izakaya drinking game';
}

function where(world) {
    const p = world.player;
    return `${world.roomManager.currentRoom} ${p.gridX},${p.gridY} on ${world.date} as ${world.as}` +
        (world.onBoardCell() ? '\non a train boarding cell: ride <' +
            Object.keys(world.config.stations).filter(k => k !== world.roomManager.currentRoom).join('|') + '>' : '');
}

function report(world, r, dir) {
    if (r.transported) return `${dir}: transported ${r.transported.from} -> ${where(world)}`;
    if (!r.moved) return `${dir}: blocked at ${r.bumped.join(',')}: ${describe(world, r.interaction)}`;
    return null;
}

const COMMANDS = {
    help() {
        return [
            'where                      room, cell, date, character',
            'look [radius=10]           text map around you',
            'map                        text map of the whole room',
            'move <n|s|e|w> [count]...  walk; a blocked step bumps (talks, opens shops) like the game',
            'goto <x> <y>               pathfind and walk; stops if a transporter takes you',
            'warp <room> [x y]          teleport (debug)',
            'ride <station>             take the train from a boarding cell',
            'inspect <x> <y>            every tile, collider and interaction on a cell',
            'rooms                      all rooms with sizes and counts',
            'transporters [room]        where every teleport leads',
            'npcs                       everyone in the world on the current date',
            'dates                      days that have blog content',
            'date <YYYY-MM-DD|today>    time travel',
            'as <name>                  play as a cast member (their NPC leaves the world)',
            'check                      transporter targets, NPC placement, unreachable rooms',
            'reset                      back to the spawn point, today',
            '',
            'Legend: @ you  # blocked  . walkable  > transporter  T train  $ shop  ~ pond  ? clock  D drinking game  letters are NPCs',
            'State persists between runs. With no arguments, commands are read from stdin, one per line.',
        ].join('\n');
    },
    where: (w) => where(w),
    look(w, [r = '10']) {
        const n = Number(r), p = w.player;
        return where(w) + '\n' + draw(w, p.gridX - n, p.gridY - n, p.gridX + n, p.gridY + n);
    },
    map: (w) => where(w) + '\n' + draw(w, 0, 0, w.w - 1, w.h - 1),
    move(w, args) {
        const lines = [];
        for (let i = 0; i < args.length; i++) {
            const dir = ALIAS[args[i]] || args[i];
            if (!DIRS[dir]) throw new Error(`unknown direction "${args[i]}"`);
            let count = 1;
            if (/^\d+$/.test(args[i + 1] || '')) count = Number(args[++i]);
            for (let c = 0; c < count; c++) {
                const r = w.step(dir);
                const msg = report(w, r, dir);
                if (msg) { lines.push(msg); break; }
            }
        }
        lines.push(where(w));
        return lines.join('\n');
    },
    goto(w, [x, y]) {
        const steps = w.path(Number(x), Number(y));
        if (!steps) return `no walkable path to ${x},${y} from ${where(w)}`;
        const lines = [`walked ${steps.length} steps`];
        for (const dir of steps) {
            const r = w.step(dir);
            const msg = report(w, r, dir);
            if (msg) { lines.push(msg); break; }
        }
        lines.push(where(w));
        return lines.join('\n');
    },
    warp(w, [room, x, y]) {
        const key = Object.keys(w.config.rooms).find(k => k.toLowerCase() === String(room).toLowerCase());
        if (!key) throw new Error(`no room "${room}" (try: rooms)`);
        if (x === undefined) {
            const t = Object.values(w.roomManager.rooms).flatMap(r => r.transporters).find(t => t.targetRoom === key);
            const st = (w.config.stations || {})[key];
            [x, y] = t ? [t.targetX, t.targetY] : st ? st.arrive : [w.config.player.startX, w.config.player.startY];
        }
        w.enter(key, Number(x), Number(y));
        return where(w);
    },
    ride(w, [dest]) {
        if (!w.onBoardCell()) return 'not on a train boarding cell (T on the map)';
        const stations = w.config.stations;
        const key = Object.keys(stations).find(k => k !== w.roomManager.currentRoom &&
            [k, stations[k].label, stations[k].town].some(n => n.toLowerCase() === String(dest).toLowerCase()));
        if (!key) return 'destinations: ' + Object.keys(stations).filter(k => k !== w.roomManager.currentRoom).join(', ');
        w.enter(key, stations[key].arrive[0], stations[key].arrive[1]);
        return 'rode the train -> ' + where(w);
    },
    inspect(w, [x, y]) {
        x = Number(x); y = Number(y);
        const lines = [`${w.roomManager.currentRoom} ${x},${y}`];
        lines.push(w.roomManager.checkBoundary(x, y) ? 'inside the boundary' : 'OUTSIDE the boundary');
        lines.push(w.blocked.has(x + ',' + y) ? 'blocked by a collider' : 'no collider');
        for (const t of w.tilesAt(x, y)) {
            lines.push(`  ${t.layer} (z ${t.z}${t.collision ? ', collision' : ''}): ${t.key}` +
                (t.at[0] !== x || t.at[1] !== y ? ` anchored at ${t.at.join(',')}` : ''));
        }
        const tr = w.room.transporters.find(t => t.gridX === x && t.gridY === y);
        if (tr) lines.push(`transporter to ${tr.targetRoom} ${tr.targetX},${tr.targetY}`);
        const i = w.interactionAt(x, y);
        if (i) lines.push('bumping it: ' + describe(w, i));
        return lines.join('\n');
    },
    rooms(w) {
        return Object.keys(w.config.rooms).map(k => {
            const r = w.roomManager.rooms[k];
            return `${k.padEnd(16)} ${String(r.worldWidth / 64).padStart(3)}x${String(r.worldHeight / 64).padEnd(3)} ` +
                `${w.npcsIn(k).length} npcs, ${r.transporters.length} transporters` +
                (w.config.rooms[k].interior ? ', interior' : '') + ((w.config.stations || {})[k] ? ', station' : '');
        }).join('\n');
    },
    transporters(w, [room]) {
        const lines = [];
        for (const [k, r] of Object.entries(w.roomManager.rooms)) {
            if (room && k.toLowerCase() !== room.toLowerCase()) continue;
            for (const t of r.transporters) {
                lines.push(`${k} ${t.gridX},${t.gridY} -> ${t.targetRoom} ${t.targetX},${t.targetY}${t.hidden ? ' (hidden)' : ''}`);
            }
        }
        for (const [k, st] of Object.entries(w.config.stations || {})) {
            if (room && k.toLowerCase() !== room.toLowerCase()) continue;
            lines.push(`${k} board at ${st.board.map(c => c.join(',')).join(' or ')} -> any other station (arrive ${st.arrive.join(',')})`);
        }
        return lines.join('\n');
    },
    npcs(w) {
        const lines = [];
        for (const k of Object.keys(w.config.rooms)) {
            for (const n of w.npcsIn(k)) {
                lines.push(`${k} ${n.gridX},${n.gridY} ${n.name}: ${n.dialogue.length} lines` +
                    (n.dialogue[0] ? ` "${n.dialogue[0].slice(0, 70)}${n.dialogue[0].length > 70 ? '...' : ''}"` : ''));
            }
        }
        return `on ${w.date}, playing as ${w.as}\n` + lines.join('\n');
    },
    dates: (w) => [...contentChangeDates(w.config)].sort().join(' '),
    date(w, [d]) {
        if (d === 'today') d = new World({}).date;
        if (!/^\d{4}-\d{2}-\d{2}$/.test(d || '')) throw new Error('date <YYYY-MM-DD|today>');
        w.date = d;
        w.enter(w.roomManager.currentRoom, w.player.gridX, w.player.gridY);
        return where(w);
    },
    as(w, [name]) {
        w.as = String(name).toLowerCase();
        w.enter(w.roomManager.currentRoom, w.player.gridX, w.player.gridY);
        return where(w);
    },
    check(w) {
        const problems = [];
        const saved = w.state();
        const arrivals = {};
        const arrive = (room, x, y, via) => (arrivals[room] = arrivals[room] || []).push({ x, y, via });
        arrive(w.config.player.startRoom, w.config.player.startX, w.config.player.startY, 'spawn');
        for (const [k, r] of Object.entries(w.roomManager.rooms)) {
            for (const t of r.transporters) {
                if (!w.roomManager.rooms[t.targetRoom]) problems.push(`${k} ${t.gridX},${t.gridY}: targets missing room "${t.targetRoom}"`);
                else arrive(t.targetRoom, t.targetX, t.targetY, `${k} ${t.gridX},${t.gridY}`);
            }
        }
        for (const [k, st] of Object.entries(w.config.stations || {})) arrive(k, st.arrive[0], st.arrive[1], 'train');
        for (const k of Object.keys(w.config.rooms)) {
            if (!arrivals[k]) { problems.push(`${k}: nothing leads here`); continue; }
            const reach = new Set();
            for (const a of arrivals[k]) {
                w.enter(k, a.x, a.y);
                if (w.blocked.has(a.x + ',' + a.y) || !w.roomManager.checkBoundary(a.x, a.y)) {
                    problems.push(`${k} ${a.x},${a.y}: arrival from ${a.via} lands on a blocked cell`);
                    continue;
                }
                for (const c of w.reachable()) reach.add(c);
            }
            w.enter(k, arrivals[k][0].x, arrivals[k][0].y);
            for (const t of w.room.transporters) {
                if (!reach.has(t.gridX + ',' + t.gridY)) problems.push(`${k} ${t.gridX},${t.gridY}: transporter to ${t.targetRoom} cannot be walked to`);
            }
            for (const n of w.room.npcs) {
                const near = 'nsew'.split('').some(d => reach.has((n.gridX + DIRS[d][0]) + ',' + (n.gridY + DIRS[d][1])));
                if (w.blocked.has(n.gridX + ',' + n.gridY)) problems.push(`${k} ${n.gridX},${n.gridY}: ${n.name} stands on a collider (${w.date})`);
                else if (!near) problems.push(`${k} ${n.gridX},${n.gridY}: ${n.name} cannot be walked up to (${w.date})`);
            }
        }
        w.enter(saved.room, saved.x, saved.y);
        return problems.length ? problems.join('\n') + `\n${problems.length} problems` : 'no problems found';
    },
};

function main() {
    const argv = process.argv.slice(2);
    const lines = argv.length ? [argv.join(' ')] : fs.readFileSync(0, 'utf8').split('\n');
    let state = null;
    try { state = JSON.parse(fs.readFileSync(SESSION, 'utf8')); } catch (e) {}
    let world;
    try { world = new World(state); } catch (e) { world = new World(null); }
    let failed = false;
    for (const line of lines) {
        const [cmd, ...args] = line.trim().split(/\s+/);
        if (!cmd || cmd.startsWith('#')) continue;
        if (lines.length > 1) out('> ' + line.trim());
        try {
            if (cmd === 'reset') { world = new World(null); out(where(world)); }
            else if (!COMMANDS[cmd]) throw new Error(`unknown command "${cmd}" (try: help)`);
            else out(COMMANDS[cmd](world, args));
        } catch (e) {
            out('error: ' + e.message);
            failed = true;
        }
    }
    fs.writeFileSync(SESSION, JSON.stringify(world.state()));
    if (failed) process.exitCode = 1;
}

main();
