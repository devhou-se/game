#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const png = require('./png');

const GV2 = path.dirname(__dirname);
const SESSION = path.join(os.tmpdir(), 'gamev2-play-' +
    crypto.createHash('sha1').update(GV2).digest('hex').slice(0, 8) + '.json');

const ctx = vm.createContext({ console, URLSearchParams, location: { search: '' } });
for (const f of ['utils/ConfigCodec.js', 'utils/NpcStates.js', 'utils/Interactions.js', 'systems/TiledAdapter.js',
    'systems/RoomManager.js', 'systems/CollisionSystem.js', 'Shop.js', 'TrainTravel.js', '../tools/world-model.js']) {
    vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), ctx, { filename: f });
}
const { decodeConfig, contentChangeDates, Shop, WorldModel, DIRS } =
    vm.runInContext('({decodeConfig, contentChangeDates, Shop, WorldModel, DIRS})', ctx);

const ALIAS = { up: 'n', down: 's', left: 'w', right: 'e', north: 'n', south: 's', east: 'e', west: 'w' };
const out = (s) => process.stdout.write(s + '\n');

const sizes = {};
const env = {
    exists: (key) => fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')),
    sizeOf(key) {
        if (sizes[key]) return sizes[key];
        let w = 1, h = 1;
        try {
            const b = Buffer.alloc(24);
            const fd = fs.openSync(path.join(GV2, 'assets', 'sprites', key + '.png'), 'r');
            fs.readSync(fd, b, 0, 24, 0);
            fs.closeSync(fd);
            w = Math.max(1, Math.round(b.readUInt32BE(16) / 64));
            h = Math.max(1, Math.round(b.readUInt32BE(20) / 64));
        } catch (e) {}
        return (sizes[key] = [w, h]);
    },
};

const sprites = {};
function sprite(key) {
    return sprites[key] || (sprites[key] = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'))));
}

function roomKey(world, name) {
    const key = Object.keys(world.config.rooms).find(k => k.toLowerCase() === String(name).toLowerCase());
    if (!key) throw new Error(`no room "${name}" (try: rooms)`);
    return key;
}

function newWorld(state) {
    const config = decodeConfig(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')));
    WorldModel.applyTiled(config, (key) => {
        const file = path.join(GV2, 'tiled', key.toLowerCase() + '.tmj');
        return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
    });
    return new WorldModel(config, env, state);
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

function where(world) {
    const p = world.player;
    return `${world.roomManager.currentRoom} ${p.gridX},${p.gridY} on ${world.date} as ${world.as}` +
        (world.livery ? `\nparked train: ${world.livery}` : '') +
        (world.onBoardCell() ? '\non a train boarding cell: ride <' +
            Object.keys(world.config.stations).filter(k => k !== world.roomManager.currentRoom).join('|') + '>' : '');
}

function report(world, r, dir) {
    if (r.transported) return `${dir}: transported ${r.transported.from} -> ${where(world)}`;
    if (!r.moved) return `${dir}: blocked at ${r.bumped.join(',')}: ${world.describe(r.interaction)}`;
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
            'date <YYYY-MM-DD|today>    time travel; today is the day the game opens on',
            'as <name>                  play as a cast member (their NPC leaves the world)',
            'check                      transporter targets and unreachable rooms, plus NPC placement on every content day',
            'lint [room]...             map QA: floor holes, missing or stray colliders, tree and overhang layering',
            'render <room> <out.png>    draw a room to a PNG [--scale 0.5] [--colliders]',
            'reset                      back to the spawn point, on the day the game opens on',
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
        if (i) lines.push('bumping it: ' + w.describe(i));
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
        if (d === 'today') d = WorldModel.defaultDate(w.config);
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
    lint(w, rooms) {
        const keys = rooms.length ? rooms.map(r => roomKey(w, r)) : Object.keys(w.config.rooms);
        const lines = [];
        let errorCount = 0;
        for (const k of keys) {
            const r = w.lint(k);
            const count = (bag) => Object.values(bag).reduce((n, v) => n + v.length, 0);
            lines.push(`${k} ${r.width}x${r.height}: ${count(r.errors)} errors, ${count(r.warns)} warnings`);
            for (const [tag, bag] of [['ERR', r.errors], ['WARN', r.warns]]) {
                for (const kind of Object.keys(bag).sort()) {
                    lines.push(`  [${tag}] ${kind}: ${bag[kind].length}`);
                    for (const item of bag[kind].slice(0, 8)) lines.push(`        ${item}`);
                    if (bag[kind].length > 8) lines.push(`        ... +${bag[kind].length - 8} more`);
                }
            }
            errorCount += count(r.errors);
        }
        if (errorCount) throw new Error(lines.join('\n') + `\n${errorCount} errors`);
        return lines.join('\n');
    },
    render(w, args) {
        const rest = args.slice();
        const colliders = rest.includes('--colliders');
        if (colliders) rest.splice(rest.indexOf('--colliders'), 1);
        let scale = 1;
        if (rest.includes('--scale')) scale = Number(rest.splice(rest.indexOf('--scale'), 2)[1]);
        const [room, file] = rest;
        if (!room || !file) throw new Error('render <room> <out.png> [--scale 0.5] [--colliders]');
        const k = roomKey(w, room);
        const r = w.roomManager.rooms[k];
        let img = png.blank(r.worldWidth, r.worldHeight);
        for (const t of w.drawOrder(k)) png.paste(img, sprite(t.key), t.x * 64, t.y * 64);
        if (colliders) {
            const saved = w.state();
            w.enter(k, 0, 0);
            for (const xy of w.blocked) {
                const [x, y] = xy.split(',').map(Number);
                png.wash(img, x * 64, y * 64, 64, 64, [255, 0, 0, 90]);
            }
            w.enter(saved.room, saved.x, saved.y);
        }
        if (scale !== 1) img = png.scale(img, scale);
        fs.writeFileSync(file, png.encode(img));
        return `${k}: ${img.width}x${img.height}px -> ${file}`;
    },
    check(w) {
        const dates = [...contentChangeDates(w.config)];
        if (!dates.includes(w.date)) dates.push(w.date);
        const { problems } = w.survey(dates.sort());
        if (!problems.length) return 'no problems found';
        return problems.map(q => `${q.room}${q.x === undefined ? '' : ` ${q.x},${q.y}`}: ${q.text}`).join('\n') + `\n${problems.length} problems`;
    },
};

function main() {
    const argv = process.argv.slice(2);
    const lines = argv.length ? [argv.join(' ')] : fs.readFileSync(0, 'utf8').split('\n');
    let state = null;
    try { state = JSON.parse(fs.readFileSync(SESSION, 'utf8')); } catch (e) {}
    let world;
    try { world = newWorld(state); } catch (e) { world = newWorld(null); }
    let failed = false;
    for (const line of lines) {
        const [cmd, ...args] = line.trim().split(/\s+/);
        if (!cmd || cmd.startsWith('#')) continue;
        if (lines.length > 1) out('> ' + line.trim());
        try {
            if (cmd === 'reset') { world = newWorld(null); out(where(world)); }
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
