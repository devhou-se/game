#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const png = require('./png');

const GV2 = path.dirname(__dirname);
// `--config=<file>` plays another config.json (a scratch copy, e.g. the blog dress rehearsal's)
// against this checkout's maps and sprites; it keeps its own session.
let CONFIG = path.join(GV2, 'config.json');
const sessionFile = () => path.join(os.tmpdir(), 'gamev2-play-' +
    crypto.createHash('sha1').update(CONFIG === path.join(GV2, 'config.json') ? GV2 : CONFIG).digest('hex').slice(0, 8) + '.json');

const ctx = vm.createContext({ console, URLSearchParams, location: { search: '' } });
for (const f of ['utils/ConfigCodec.js', 'utils/Trips.js', 'utils/NpcStates.js', 'utils/Interactions.js', 'systems/TiledAdapter.js',
    'systems/RoomManager.js', 'systems/CollisionSystem.js', 'systems/CityStitcher.js', 'Shop.js', 'TrainTravel.js',
    '../tools/world-model.js']) {
    vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), ctx, { filename: f });
}
const { decodeConfig, contentChangeDates, Shop, WorldModel, DIRS, Trips } =
    vm.runInContext('({decodeConfig, contentChangeDates, Shop, WorldModel, DIRS, Trips})', ctx);

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

// a config room, or (stitched) a city
function roomKey(world, name) {
    const key = Object.keys(world.roomManager.rooms).find(k => k.toLowerCase() === String(name).toLowerCase());
    if (!key) throw new Error(`no room "${name}" (try: rooms)`);
    return key;
}

// The game stitches the districts of config `cities` into one room, and so does the model.
// `--stitch=0` (like the game's ?stitch=0) keeps them as separate rooms joined by seam teleports.
let STITCH = true;

function newWorld(state, stitch = STITCH) {
    const config = decodeConfig(JSON.parse(fs.readFileSync(CONFIG, 'utf8')));
    WorldModel.applyTiled(config, (key) => {
        const file = path.join(GV2, 'tiled', key.toLowerCase() + '.tmj');
        return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
    });
    return new WorldModel(config, env, state, { stitch });
}

// one glyph for each group of src/utils/Interactions.js; a group with none of its own draws as OTHER
const GLYPH = { shop: '$', pond: '~', clock: '?', 'drinking-game': 'D', career: 'J', flights: '^', water: '%',
    shrine: '+', temple: '+', palace: '+', flavour: '*' };
const OTHER = '*';

// x0..y1 are cells of the room being played (city cells inside a stitched city); the rulers and
// notes are printed in the coordinates of `origin` ({ox, oy}: the district underfoot by default),
// which are the ones config, the maps and every command use.
function draw(world, x0, y0, x1, y1, origin) {
    const p = world.player;
    const { ox, oy } = origin || world.here();
    const at = (x, y) => `${x - ox},${y - oy}`;
    const special = new Set();
    for (const i of world.interactions()) {
        for (let x = i.x; x < i.x + i.w; x++) for (let y = i.y; y < i.y + i.h; y++) special.add(x + ',' + y);
    }
    const board = new Set(((world.station() || {}).board || []).map(c => c.join(',')));
    const lines = [];
    const notes = [];
    for (let y = y0; y <= y1; y++) {
        let row = String(y - oy).padStart(3) + ' ';
        for (let x = x0; x <= x1; x++) {
            const k = x + ',' + y;
            const npc = world.room.npcs.find(n => n.gridX === x && n.gridY === y);
            const t = world.room.transporters.find(t => t.gridX === x && t.gridY === y);
            let c;
            if (x < 0 || y < 0 || x >= world.w || y >= world.h) c = ' ';
            else if (p.gridX === x && p.gridY === y) c = '@';
            else if (npc) { c = npc.name[0].toUpperCase(); notes.push(`${c} ${npc.name} at ${at(x, y)}`); }
            else if (t) { c = '>'; notes.push(`> ${at(x, y)} to ${t.targetRoom} ${t.targetX},${t.targetY}${t.hidden ? ' (hidden)' : ''}`); }
            else if (board.has(k)) { c = 'T'; notes.push(`T ${at(x, y)} train boarding`); }
            else if (special.has(k)) {
                const i = world.interactionAt(x, y);
                c = i ? (GLYPH[i.group] || OTHER) : (world.blocked.has(k) ? '#' : '.');
                if (i) notes.push(`${c} ${at(x, y)} ${i.kind}`);
            }
            else if (world.blocked.has(k) || !world.roomManager.checkBoundary(x, y)) c = '#';
            else c = '.';
            row += c;
        }
        lines.push(row);
    }
    const ruler = (f) => '    ' + Array.from({ length: x1 - x0 + 1 }, (_, i) => f(x0 + i - ox)).join('');
    const head = [ruler(x => x % 10 === 0 ? String(Math.abs(Math.floor(x / 10)) % 10) : ' '), ruler(x => String(((x % 10) + 10) % 10))];
    return head.concat(lines, [...new Set(notes)]).join('\n');
}

function where(world) {
    const p = world.player, h = world.here();
    return `${h.room} ${h.x},${h.y}` + (h.city ? ` (${h.city} ${p.gridX},${p.gridY})` : '') + ` on ${world.date} as ${world.as}` +
        (world.livery ? `\nparked train: ${world.livery}` : '') +
        (world.onBoardCell() ? '\non a train boarding cell: ride <' +
            Object.keys(world.config.stations).filter(k => k !== world.roomManager.currentRoom).join('|') + '>' : '') +
        ((world.config.airports || {})[world.roomManager.currentRoom] ? '\nin an airport: bump the gate, or fly <' +
            Object.keys(world.config.airports).filter(k => k !== world.roomManager.currentRoom).join('|') + '>' : '');
}

function report(world, r, dir) {
    if (r.transported) return `${dir}: transported ${r.transported.from} -> ${where(world)}`;
    if (!r.moved) {
        const h = world.here();
        return `${dir}: blocked at ${r.bumped[0] - h.ox},${r.bumped[1] - h.oy}: ${world.describe(r.interaction)}`;
    }
    return null;
}

const COMMANDS = {
    help() {
        return [
            'where                      room, cell, date, character',
            'look [radius=10]           text map around you',
            'map [city]                 text map of the whole room (in a stitched city: the district you are in; "map city" draws all of it)',
            'move <n|s|e|w> [count]...  walk; a blocked step bumps (talks, opens shops) like the game',
            'goto [room] <x> <y>        pathfind and walk; stops if a transporter takes you. Districts of a city are one walk: goto Market 5 24',
            'warp <room> [x y]          teleport (debug)',
            'ride <station>             take the train from a boarding cell',
            'fly <airport>              take a flight from inside an airport (in the game: bump the gate)',
            'inspect <x> <y>            every tile, collider and interaction on a cell',
            'rooms                      all rooms with sizes and counts',
            'transporters [room]        where every teleport leads',
            'npcs                       everyone in the world on the current date',
            'dates                      days that have blog content',
            'date <YYYY-MM-DD|today>    time travel; today is the day the game opens on',
            'trips                      the trips, and where a player starts on the current date',
            'start                      go where the game starts a player on the current date (beside the cast)',
            'as <name>                  play as a cast member (their NPC leaves the world)',
            'check                      transporter targets and unreachable rooms, NPC placement and player starts on every content and trip day, and every room\'s lint errors (stitched, then ?stitch=0); exits 1 when it finds a problem',
            'lint [room]...             map QA: floor holes, missing or stray colliders, tree and overhang layering (a district, or a whole city)',
            'render <room> <out.png>    draw a room - or a stitched city, woods and all - to a PNG [--scale 0.5] [--colliders]',
            'reach [room]...            JSON: the cells of each room that can be walked to, in its own coordinates',
            'reset                      back to the start (the trip home), on the day the game opens on',
            '',
            'Legend: @ you  # blocked  . walkable  > transporter  T train  $ shop  ~ pond  ? clock  ^ flights  % water  + shrine, temple or palace  * anything else a bump answers  D drinking game  J job  letters are NPCs',
            'Coordinates are always a room\'s own (a district\'s inside the stitched Tokyo city; cells of a neighbour are just past its edge).',
            'State persists between runs. With no arguments, commands are read from stdin, one per line.',
            '--stitch=0 (anywhere on the command line) models what ?stitch=0 plays: the districts as separate rooms joined by seam teleports.',
            '--config=<file> plays another config.json (a scratch copy) against this checkout\'s maps and sprites, with its own session.',
        ].join('\n');
    },
    where: (w) => where(w),
    look(w, [r = '10']) {
        const n = Number(r), p = w.player;
        return where(w) + '\n' + draw(w, p.gridX - n, p.gridY - n, p.gridX + n, p.gridY + n);
    },
    map(w, [what]) {
        const h = w.here();
        if (!h.city || what === 'city') return where(w) + '\n' + draw(w, 0, 0, w.w - 1, w.h - 1, { ox: 0, oy: 0 });
        const r = w.roomManager.rooms[h.room];
        return where(w) + '\n' + draw(w, h.ox, h.oy, h.ox + r.worldWidth / 64 - 1, h.oy + r.worldHeight / 64 - 1);
    },
    move(w, args) {
        const lines = [];
        for (let i = 0; i < args.length; i++) {
            const dir = ALIAS[args[i]] || args[i];
            if (!DIRS[dir]) throw new Error(`unknown direction "${args[i]}"`);
            let count = 1;
            if (/^\d+$/.test(args[i + 1] || '')) count = Number(args[++i]);
            for (let c = 0; c < count; c++) {
                const r = w.step(dir);
                if (r.crossed) lines.push(`${dir}: walked from ${r.crossed.from} into ${r.crossed.to}`);
                const msg = report(w, r, dir);
                if (msg) { lines.push(msg); break; }
            }
        }
        lines.push(where(w));
        return lines.join('\n');
    },
    goto(w, args) {
        const h = w.here();
        const room = args.length > 2 ? roomKey(w, args[0]) : h.room;
        const [x, y] = args.slice(-2).map(Number);
        const to = w.roomManager.resolve(room, x, y);
        if (to.room !== w.roomManager.currentRoom) return `${room} is another room: walk to a door, or warp ${room} ${x} ${y}`;
        const steps = w.path(to.x, to.y);
        if (!steps) return `no walkable path to ${room} ${x},${y} from ${where(w)}`;
        const lines = [`walked ${steps.length} steps`];
        for (const dir of steps) {
            const r = w.step(dir);
            if (r.crossed) lines.push(`walked from ${r.crossed.from} into ${r.crossed.to}`);
            const msg = report(w, r, dir);
            if (msg) { lines.push(msg); break; }
        }
        lines.push(where(w));
        return lines.join('\n');
    },
    warp(w, [room, x, y]) {
        const key = roomKey(w, room);
        if (x === undefined) {
            const t = Object.values(w.roomManager.rooms).flatMap(r => r.transporters).find(t => t.targetRoom === key);
            const st = (w.config.stations || {})[key];
            if (t) [x, y] = [t.targetX, t.targetY];
            else if (st) [x, y] = st.arrive;
            else {
                // the spawn point is written in its own room's cells; a stitched city holds that room
                // somewhere inside it (warp TokyoCity -> Tokyo 29,38, not the city's own cell 29,38)
                const p = w.config.player, at = w.roomManager.resolve(p.startRoom, p.startX, p.startY);
                [x, y] = at.room === key ? [at.x, at.y] : [p.startX, p.startY];
            }
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
    fly(w, [dest]) {
        const airports = w.config.airports || {}, here = w.roomManager.currentRoom;
        if (!airports[here]) return 'not in an airport';
        const others = Object.keys(airports).filter(k => k !== here);
        const name = (k) => airports[k].label || w.config.rooms[airports[k].serves].name;
        const key = others.find(k => [k, name(k), airports[k].serves].some(n => n.toLowerCase() === String(dest).toLowerCase()));
        if (!key) return 'flights: ' + others.join(', ');
        w.enter(key, airports[key].arrive[0], airports[key].arrive[1]);
        return 'flew -> ' + where(w);
    },
    inspect(w, [x, y]) {
        // the cell is named in the coordinates of the district underfoot; the model works in the room's
        const h = w.here();
        const lines = [`${h.room} ${x},${y}` + (h.city ? ` (${h.city} ${Number(x) + h.ox},${Number(y) + h.oy}; ${w.spot(h.city, Number(x) + h.ox, Number(y) + h.oy)})` : '')];
        x = Number(x) + h.ox; y = Number(y) + h.oy;
        lines.push(w.roomManager.checkBoundary(x, y) ? 'inside the boundary' : 'OUTSIDE the boundary');
        lines.push(w.blocked.has(x + ',' + y) ? 'blocked by a collider' : 'no collider');
        for (const t of w.tilesAt(x, y)) {
            lines.push(`  ${t.layer} (z ${t.z}${t.collision ? ', collision' : ''}): ${t.key}` +
                (t.at[0] !== x || t.at[1] !== y ? ` anchored at ${t.at[0] - h.ox},${t.at[1] - h.oy}` : ''));
        }
        const tr = w.room.transporters.find(t => t.gridX === x && t.gridY === y);
        if (tr) lines.push(`transporter to ${tr.targetRoom} ${tr.targetX},${tr.targetY}`);
        const i = w.interactionAt(x, y);
        if (i) lines.push('bumping it: ' + w.describe(i));
        return lines.join('\n');
    },
    rooms(w) {
        const rm = w.roomManager;
        const size = (r) => `${String(r.worldWidth / 64).padStart(3)}x${String(r.worldHeight / 64).padEnd(3)}`;
        return Object.keys(w.config.rooms).map(k => {
            const r = rm.rooms[k];
            return `${k.padEnd(16)} ${size(r)} ` +
                `${w.npcsIn(k).length} npcs, ${r.transporters.length} transporters` +
                (w.config.rooms[k].interior ? ', interior' : '') + ((w.config.stations || {})[k] ? ', station' : '') +
                (rm.memberOf[k] ? `, district of ${rm.memberOf[k].city.key} at ${rm.memberOf[k].member.x},${rm.memberOf[k].member.y}` : '');
        }).concat(Object.values(rm.cities).map(c => `${c.key.padEnd(16)} ${size(rm.rooms[c.key])} ` +
            `city: ${c.members.map(m => m.key).join(' + ')} stitched into one room, woods between them`)).join('\n');
    },
    transporters(w, [room]) {
        const lines = [];
        const rm = w.roomManager;
        const city = (k) => rm.memberOf[k] && rm.memberOf[k].city;
        for (const k of Object.keys(w.config.rooms)) {
            if (room && k.toLowerCase() !== room.toLowerCase()) continue;
            for (const t of rm.rooms[k].transporters) {
                lines.push(`${k} ${t.gridX},${t.gridY} -> ${t.targetRoom} ${t.targetX},${t.targetY}${t.hidden ? ' (hidden)' : ''}` +
                    (city(k) && city(k) === city(t.targetRoom) ? ' (seam: stitched away, you just walk; a teleport only with --stitch=0)' : ''));
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
    trips(w) {
        const fmt = (s) => `${s.room} ${s.x},${s.y}`;
        const lines = w.trips.map(t => `${t.id.padEnd(10)} ${t.start} to ${t.end}  ${t.name}, ${t.where || '?'}: ${t.members.join(' ')}` +
            t.stays.map(s => `\n             from ${s.from} based in ${s.room}`).join(''));
        const trip = Trips.forDate(w.trips, w.date);
        const lead = Trips.leadIn(w.trips, w.date);
        lines.push(`on ${w.date}${trip ? ` (${trip.name}${lead ? ` ${Trips.inDays(lead.days)}` : ''})` : ''}: ` +
            `a player starts at ${fmt(WorldModel.startFor(w.config, w.date, { played: w.as }))}` +
            ` (the trip's own cell is ${fmt(Trips.homeFor(w.config, w.date))})`);
        return lines.join('\n');
    },
    start(w) {
        const s = WorldModel.startFor(w.config, w.date, { played: w.as });
        w.enter(s.room, s.x, s.y);
        return where(w);
    },
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
        // every room as authored, then every stitched city as played
        const keys = rooms.length ? rooms.map(r => roomKey(w, r)) : Object.keys(w.roomManager.rooms);
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
        const dates = WorldModel.surveyDates(w.config);
        if (!dates.includes(w.date)) dates.push(w.date);
        dates.sort();
        const line = (q) => (q.where ? q.where + (q.where.startsWith(q.room + ' ') ? '' : ` (${q.room} ${q.x},${q.y})`) : q.room) + `: ${q.text}`;
        // ...and the map lint's errors for every room: a store cut off from its door passes the survey
        const lines = w.survey(dates).problems.concat(w.lintProblems()).map(line);
        // the world as the game plays it, then - when that is stitched - the separate rooms
        // ?stitch=0 falls back to (their seam teleports exist nowhere else)
        if (w.stitched && Object.keys(w.roomManager.cities).length) {
            const legacy = newWorld(w.state(), false);
            for (const q of legacy.survey(dates).problems.concat(legacy.lintProblems())) if (!lines.includes(line(q))) lines.push('[--stitch=0] ' + line(q));
        }
        if (!lines.length) return 'no problems found';
        // like lint: a problem is a failure, so the exit code gates a script or CI step
        throw new Error(lines.join('\n') + `\n${lines.length} problems`);
    },
    reach(w, rooms) {
        const all = w.reachByRoom(w.survey(null, { npcs: false }).reach);
        const keys = rooms.length ? rooms.map(r => roomKey(w, r)) : Object.keys(all);
        return JSON.stringify(Object.fromEntries(keys.map(k => [k, (all[k] || []).sort()])));
    },
};

function main() {
    const argv = process.argv.slice(2).filter(a => {
        const config = /^--config=(.+)$/.exec(a);
        if (config) { CONFIG = path.resolve(config[1]); return false; }
        if (!/^--(stitch=0|no-stitch)$/.test(a)) return true;
        STITCH = false;
        return false;
    });
    const SESSION = sessionFile();
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
