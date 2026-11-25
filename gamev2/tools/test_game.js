#!/usr/bin/env node
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const GV2 = path.dirname(__dirname);
const fired = [];
const ctx = vm.createContext({
    console, URLSearchParams, setTimeout,
    location: { search: '' },
    performance: { now: () => Date.now() },
    KeyboardEvent: class { constructor(type, init) { Object.assign(this, init, { type }); } },
    window: { dispatchEvent: (e) => fired.push(e.type + ':' + e.code) },
});
const load = (f) => vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), ctx, { filename: f });
['utils/ConfigCodec.js', 'systems/TiledAdapter.js', 'utils/Trips.js', 'utils/NpcStates.js', 'TrainTravel.js', 'StationPicker.js', 'DialogueManager.js', 'systems/TouchControls.js',
    'utils/Hints.js', 'utils/JapaneseFont.js', 'ItemIcons.js', 'Shop.js', 'Fishing.js', 'DrinkingGame.js', 'AchievementManager.js', 'CharacterCreator.js', 'CharacterSelect.js', 'Intro.js', 'systems/NPCManager.js', 'systems/UIScale.js',
    'systems/RoomManager.js', 'systems/CollisionSystem.js', '../tools/world-model.js'].forEach(load);
const game = (expr) => vm.runInContext(expr, ctx);

// The shipped world as the game sees it: config.json decoded, rooms from tiled/*.tmj.
let shipped = null;
const realConfig = () => {
    if (shipped) return shipped;
    ctx.__raw = fs.readFileSync(path.join(GV2, 'config.json'), 'utf8');
    const config = game('decodeConfig(JSON.parse(__raw))');
    for (const key of Object.keys(config.rooms)) {
        const file = path.join(GV2, 'tiled', key.toLowerCase() + '.tmj');
        if (!fs.existsSync(file)) continue;
        ctx.__tmj = fs.readFileSync(file, 'utf8');
        const built = game('TiledAdapter.toRoom(JSON.parse(__tmj))');
        const r = config.rooms[key];
        r.layers = built.layers;
        if (built.transporters.length) r.transporters = built.transporters;
        if (built.worldWidth) r.worldWidth = built.worldWidth;
        if (built.worldHeight) r.worldHeight = built.worldHeight;
        if (built.boundary) r.boundary = built.boundary;
    }
    return (shipped = config);
};
// Boot the date code as the page does, on a stubbed clock and URL.
const bootOn = (today, search) => {
    ctx.__today = today;
    game('todayIso = () => __today');
    ctx.location.search = search || '';
    ctx.__cfg = realConfig();
    game('setTripDates(__cfg)');
    return game('gameDate()');
};
// The travelling cast on a date: "Room/Name" (the izakaya's opponents and Yukimura's villager are fixtures).
const castOn = (config, date) => {
    const resolveNpc = game('resolveNpc'), trips = game('Trips.of')(config);
    const out = [];
    for (const [room, def] of Object.entries(config.rooms)) {
        for (const raw of def.npcs || []) {
            const npc = resolveNpc(raw, date, trips);
            if (npc && !npc.drinkingGameOpponent && npc.name !== 'James') out.push(`${room}/${npc.name}`);
        }
    }
    return out.sort();
};

// A Shop with no Phaser behind it: the save blob comes from (and goes to) `store`.
const shopWith = (saved) => {
    const store = { gamev2_shop: saved == null ? null : (typeof saved === 'string' ? saved : JSON.stringify(saved)) };
    ctx.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
    const shop = game('Object.create(Shop.prototype)');
    const toasts = [];
    Object.assign(shop, {
        STORE_KEY: 'gamev2_shop', clockOffset: 0, startingMoney: 5000, woreOff: [], effects: {},
        catalogue: Array.from(game('Shop.DEFAULT_ITEMS.concat(Shop.fishItems())')),
        scene: { updateHUD() {}, achievementManager: game('Object.create(AchievementManager.prototype)') },
        toast: (m) => toasts.push(m), updateEffectChip() {}, repaint() { this.refreshStock(); },
    });
    shop.scene.shop = shop;
    shop.scene.achievementManager.scene = shop.scene;
    shop.load();
    return { shop, toasts, saved: () => JSON.parse(store.gamev2_shop) };
};

// A DrinkingGame at the izakaya table with `money` in the wallet and stubbed text objects.
const showdownWith = (money, player, bonus) => {
    const text = () => ({ setText() {}, setVisible() {}, setFill() {} });
    const shop = { money, save() {}, fmt: (n) => '¥' + n, buff: (k) => (k === 'prizeBonus' ? (bonus || 1) : 0),
        activeEffects: () => [], toast() {} };
    const g = game('Object.create(DrinkingGame.prototype)');
    Object.assign(g, {
        scene: { shop, updateHUD() {}, player: { baseSpriteKey: player + '_front' },
            time: { now: 0, addEvent: () => ({ remove() {} }), delayedCall: () => ({ remove() {} }) } },
        objs: [], stakeIndex: 0, staked: 0, durationMs: 15000, state: 'ready',
        opponent: game('DrinkingGame.opponentFor')(player),
        statusText: text(), hintText: text(), prizeText: text(), timerText: text(), rulesText: text(),
    });
    g.resetScores();
    return { g, shop };
};

// The world as tools/play.js and /studio/ model it (tools/world-model.js), in a context of its own:
// config.json + the .tmj maps, stitched like the game unless `stitch` is false. `edit(config)` may
// change the decoded config first.
const worldWith = (stitch, edit) => {
    const w = vm.createContext({ console, URLSearchParams, location: { search: '' } });
    for (const f of ['utils/ConfigCodec.js', 'utils/Trips.js', 'utils/NpcStates.js', 'utils/Interactions.js', 'systems/TiledAdapter.js',
        'systems/RoomManager.js', 'systems/CollisionSystem.js', 'systems/CityStitcher.js', 'systems/Occlusion.js', 'Shop.js', 'TrainTravel.js',
        '../tools/world-model.js']) {
        vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), w, { filename: f });
    }
    const run = (expr) => vm.runInContext(expr, w);
    const config = run('decodeConfig')(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')));
    run('WorldModel').applyTiled(config, (key) => {
        const file = path.join(GV2, 'tiled', key.toLowerCase() + '.tmj');
        return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
    });
    if (edit) edit(config);
    const exists = (key) => fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
    const sizeOf = (key) => {
        const b = Buffer.alloc(24), fd = fs.openSync(path.join(GV2, 'assets', 'sprites', key + '.png'), 'r');
        fs.readSync(fd, b, 0, 24, 0);
        fs.closeSync(fd);
        return [Math.max(1, Math.round(b.readUInt32BE(16) / 64)), Math.max(1, Math.round(b.readUInt32BE(20) / 64))];
    };
    const world = new (run('WorldModel'))(config, { exists, sizeOf }, { date: '2025-11-11' }, { stitch });
    return { world, run, config };
};

const tests = {
    'a station parks its own train, and keeps the one you rode in on'() {
        const liveryFor = game('TrainTravel.liveryFor');
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        for (const st of Object.values(stations)) assert.strictEqual(liveryFor(st, null), st.train);
        assert.strictEqual(liveryFor(stations.YukimuraStation, 'train-orange'), 'train-orange');
    },

    'the departures board is ordered from data, groups day trips, and starts somewhere sensible'() {
        const board = game('StationPicker.board');
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        const show = (from, cameFrom) => {
            const b = board(stations, from, cameFrom);
            // Array.from: rows come from the vm realm, deepStrictEqual compares prototypes
            return Array.from(b.rows, (r, i) => (i === b.selected ? '>' : '') + '  '.repeat(r.indent) + r.label + (r.here ? ' (here)' : ''));
        };
        // the real registry: Tokyo first, day trips under their city, never alphabetical
        assert.deepStrictEqual(show('TokyoStation'),
            ['Tokyo Station (here)', '>  Inaka', '  Yukimura', 'Osaka', 'Sapporo', '  Asahikawa']);
        assert.deepStrictEqual(show('OsakaStation'),
            ['>Tokyo Station', '  Inaka', '  Yukimura', 'Sapporo', '  Asahikawa']);
        // a day-trip station starts on its city; the way you came wins over that
        assert.deepStrictEqual(show('AsahikawaStation'),
            ['Tokyo Station', '  Inaka', '  Yukimura', 'Osaka', '>Sapporo']);
        assert.deepStrictEqual(show('AsahikawaStation', 'OsakaStation'),
            ['Tokyo Station', '  Inaka', '  Yukimura', '>Osaka', 'Sapporo']);
        assert.deepStrictEqual(show('SapporoStation', 'TokyoStation'),
            ['>Tokyo Station', '  Inaka', '  Yukimura', 'Osaka', 'Sapporo (here)', '  Asahikawa']);
        // where you came from is ignored when it is where you are, or not a station
        assert.strictEqual(board(stations, 'TokyoStation', 'TokyoStation').selected, 1);
        assert.strictEqual(board(stations, 'TokyoStation', 'Nowhere').selected, 1);

        // every station is on every board exactly once, and the heading is never the selection
        for (const from of Object.keys(stations)) {
            const b = board(stations, from, null);
            const dests = Array.from(b.rows).filter(r => !r.here).map(r => r.key).sort();
            assert.deepStrictEqual(dests, Object.keys(stations).filter(k => k !== from).sort(), from);
            assert.ok(b.selected >= 0 && !b.rows[b.selected].here, from);
        }

        // no order / parent fields: a stable alphabetical-by-label board, as flat cities
        const bare = { B: { label: 'Beta' }, A: { label: 'alpha' }, C: { label: 'Gamma' } };
        assert.deepStrictEqual(Array.from(board(bare, 'C').rows, r => r.key), ['A', 'B']);
        // bad parents (unknown, itself, a cycle, a day trip of a day trip) never hide a station
        const odd = {
            A: { label: 'A', order: 0 }, B: { label: 'B', order: 1, parent: 'Nope' },
            C: { label: 'C', order: 2, parent: 'C' }, D: { label: 'D', order: 3, parent: 'E' },
            E: { label: 'E', order: 4, parent: 'D' }, F: { label: 'F', order: 5, parent: 'A' },
            G: { label: 'G', order: 6, parent: 'F' },
        };
        assert.deepStrictEqual(Array.from(board(odd, 'X').rows, r => r.key + r.indent),
            ['A0', 'F1', 'B0', 'C0', 'D0', 'E0', 'G0']);
        // nowhere to go
        assert.strictEqual(board({ A: { label: 'A' } }, 'A').selected, -1);
        assert.strictEqual(board(undefined, 'A').selected, -1);
    },

    'the departures board skips its heading and scrolls to keep the selection in view'() {
        const step = game('StationPicker.step'), scrollTop = game('StationPicker.scrollTop');
        const rows = [{ here: true }, { indent: 1 }, { indent: 1 }, {}, {}, { indent: 1 }];
        assert.strictEqual(step(rows, 1, -1), 5, 'up from the first destination wraps past the heading');
        assert.strictEqual(step(rows, 5, 1), 1);
        assert.strictEqual(step(rows, 2, 1), 3);
        assert.strictEqual(step([{}], 0, 1), 0);

        assert.strictEqual(scrollTop(0, 3, 6, 7), 0, 'a board that fits never scrolls');
        assert.strictEqual(scrollTop(0, 9, 14, 7), 3, 'down: the selection becomes the last row shown');
        assert.strictEqual(scrollTop(3, 5, 14, 7), 3, 'moving inside the window leaves it alone');
        assert.strictEqual(scrollTop(5, 4, 14, 7), 4, 'up: the selection becomes the first row shown');
        assert.strictEqual(scrollTop(5, 13, 14, 7), 7);
        assert.strictEqual(scrollTop(99, 13, 14, 7), 7, 'clamped to the end');
        assert.strictEqual(scrollTop(5, 1, 14, 7, rows), 0, 'a day trip brings its heading into view');
        assert.strictEqual(scrollTop(5, 2, 14, 7, rows), 0, 'the second trip of a city brings the city too, not its sibling');
        assert.strictEqual(scrollTop(1, 1, 14, 7, rows), 0, 'also when the trip is already the first row shown');
        assert.strictEqual(scrollTop(5, 5, 14, 7, rows), 4);
        assert.strictEqual(scrollTop(5, 4, 14, 7, rows), 4, 'a city needs nothing above it');
        const many = [{}].concat(Array(9).fill({ indent: 1 }));
        assert.strictEqual(scrollTop(9, 8, 10, 3, many), 7, 'a city too far up to fit is left behind');

        // scrolled by wheel / arrows / drag: the selection may not be left off screen
        const clamp = game('StationPicker.clampSelection');
        const long = [{ here: true }, { indent: 1 }, {}, {}, {}, {}, {}, {}, {}, {}];
        assert.strictEqual(clamp(long, 3, 0, 7), 3, 'still in view: unchanged');
        assert.strictEqual(clamp(long, 1, 3, 7), 3, 'scrolled past it: the first row shown');
        assert.strictEqual(clamp(long, 9, 0, 7), 6, 'scrolled back above it: the last row shown');
        assert.strictEqual(clamp(long, 9, 0, 1), 9, 'nothing selectable in view: left alone');
        assert.strictEqual(clamp(long, 8, 0, 2), 1, 'never the heading');
    },

    'a train ride remembers where it came from, for the board at the other end'() {
        const travel = game('Object.create(TrainTravel.prototype)');
        travel.lastRide = null;
        assert.strictEqual(travel.cameFrom('SapporoStation'), null);
        travel.lastRide = { from: 'TokyoStation', to: 'SapporoStation' };
        assert.strictEqual(travel.cameFrom('SapporoStation'), 'TokyoStation');
        assert.strictEqual(travel.cameFrom('OsakaStation'), null);
    },

    'every room has a display name for the HUD, and no interior shows its key'() {
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        for (const [key, room] of Object.entries(rooms)) {
            assert.ok(room.name && room.name.trim(), `${key} has no name`);
            if (/^Konbini|Station$/.test(key)) assert.notStrictEqual(room.name, key, `${key} shows its room key`);
        }
        assert.strictEqual(rooms.KonbiniSapporo1.name, '7-Eleven · Sapporo');
        assert.strictEqual(rooms.SapporoStation.name, 'Sapporo Station');
        assert.strictEqual(rooms.TokyoStation.name, 'Tokyo Station');
    },

    'a snowed-in town lays no grass-fringed path: gravel and dirt use their snow families'() {
        // gravel-autotile / dirt-outside-autotile edges carry a green fringe (tools/generate_hokkaido.py SNOW_FAMILIES)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const bad = [], snowTowns = [];
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const floor = (room.layers || []).find((l) => l.name === 'Floor');
            const cells = Object.entries((floor && floor.tiles) || {});
            if (!cells.some(([, t]) => name(t).startsWith('snow-autotile'))) continue;
            snowTowns.push(key);
            for (const [xy, t] of cells) {
                if (/^(gravel|dirt-outside)-autotile_/.test(name(t))) bad.push(`${key} @${xy} ${name(t)}`);
            }
        }
        assert.deepStrictEqual(bad, []);
        for (const town of ['Yukimura', 'Sapporo', 'Asahikawa']) {
            assert.ok(snowTowns.includes(town), `${town} is no longer on snow ground`);
            const floor = cfg.rooms[town].layers.find((l) => l.name === 'Floor');
            assert.ok(Object.values(floor.tiles).some((t) => name(t).startsWith('gravel-snow-autotile_')), `${town} has no rail-corridor gravel`);
        }
        for (const role of ['center', 'edge-n', 'edge-s', 'edge-e', 'edge-w', 'corner-ne', 'corner-nw', 'corner-se', 'corner-sw']) {
            const k = `gravel-snow-autotile_${role}`;
            assert.ok(k in cfg.spriteMetadata, `${k} is not in spriteMetadata (not loaded at boot)`);
            assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', k + '.png')), `${k}.png is missing`);
        }
    },

    'a road over a train track is an open level crossing, in every room'() {
        // tools/seal_tracks.py leaves a track cell with a road under it unsealed; Palace has two (#138)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const sealed = [], crossings = {};
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const layer = (n) => ((room.layers || []).find((l) => l.name === n) || {}).tiles || {};
            const floor = layer('Floor'), colliders = layer('Colliders');
            for (const l of room.layers || []) {
                for (const [xy, t] of Object.entries(l.tiles || {})) {
                    if (!name(t).startsWith('train-track') || !name(floor[xy]).startsWith('road-')) continue;
                    (crossings[key] = crossings[key] || []).push(xy);
                    if (xy in colliders) sealed.push(`${key} @${xy}`);
                }
            }
        }
        assert.deepStrictEqual(sealed, []);
        assert.deepStrictEqual(crossings.Palace.sort(), ['0,3', '1,3', '54,3', '55,3', '56,3'], 'west and east roads cross the track');
    },

    'Osaka: both pavements pass the signal posts at the bridgehead without the road'() {
        // the posts stand on the kerb at (22,19) and (27,19); the bridge pavement is two cells wide round them (#139)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const layer = (n) => (cfg.rooms.Osaka.layers.find((l) => l.name === n) || {}).tiles || {};
        const floor = layer('Floor'), colliders = layer('Colliders');
        const open = (xy) => xy in floor && !(xy in colliders) && !name(floor[xy]).startsWith('road-');
        const reach = (from, to) => {
            const seen = new Set([from]), todo = [from];
            while (todo.length) {
                const [x, y] = todo.pop().split(',').map(Number);
                if (y < 17 || y > 23) continue;                    // round the post, not round the town
                for (const n of [`${x + 1},${y}`, `${x - 1},${y}`, `${x},${y + 1}`, `${x},${y - 1}`]) {
                    if (open(n) && !seen.has(n)) { seen.add(n); todo.push(n); }
                }
            }
            return seen.has(to);
        };
        for (const x of [22, 27]) {
            assert.ok(`${x},19` in colliders, `signal post base at ${x},19`);
            assert.ok(reach(`${x},18`, `${x},22`), `pavement at column ${x} is cut off by its signal post`);
        }
    },

    'a dated state that marks an NPC absent carries no placement'() {
        // tools/blog_to_npc.py PLACEMENT_KEYS: a leftover photo is still preloaded, leftover dialogue reads as a post
        const placementKeys = ['gridX', 'gridY', 'dialogue', 'photo', 'voice', 'drunk', 'posts'];
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const stale = [];
        for (const [key, room] of Object.entries(rooms)) {
            for (const npc of room.npcs || []) {
                for (const [date, st] of Object.entries(npc.states || {})) {
                    if (st.present !== false) continue;
                    const left = placementKeys.filter((k) => k in st);
                    if (left.length) stale.push(`${key} ${npc.name} ${date}: ${left.join(', ')}`);
                }
            }
        }
        assert.deepStrictEqual(stale, []);
    },

    'the title and intro line-ups show the listed devhouse members that have sprites, never james'() {
        const lineup = game('CharacterSelect.lineup'), available = game('CharacterSelect.available');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        assert.deepStrictEqual(cfg.members, ['bailey', 'damian', 'dylan', 'julia', 'khoi', 'sam', 'xander']);
        assert.deepStrictEqual(Array.from(lineup(cfg)), cfg.members.slice().sort(), 'every member has a sprite set, alphabetical');
        assert.deepStrictEqual(Array.from(available(cfg)), Array.from(available(cfg)).slice().sort(), 'Menu -> Character is alphabetical, james included');
        assert.ok(Array.from(available(cfg)).includes('james'), 'james stays playable (Menu -> Character)');
        assert.strictEqual(cfg.player.sprite, 'james_front', 'james stays the default player sprite');
        // a listed name without a sprite set is skipped; an unlisted sprite set never appears
        const set = (...names) => Object.fromEntries(names.flatMap(n => ['front', 'back', 'side'].map(d => [`${n}_${d}`, {}])));
        const fake = { members: ['sam', 'gloria', 'james_front', 'bailey'], spriteMetadata: set('james', 'bailey', 'sam', 'custom') };
        assert.deepStrictEqual(Array.from(lineup(fake)), ['bailey', 'sam'], 'alphabetical whatever the list order');
        assert.deepStrictEqual(Array.from(lineup({ spriteMetadata: set('james', 'bailey') })), [], 'no list, no line-up');
        // the intro's sentence under the row names the same people as the row
        // (Intro.cast: the line-up of the game date's trip, see the trips tests)
        const cast = game('Intro.cast');
        assert.deepStrictEqual(Array.from(cast(cfg, '2027-02-20')), ['bailey', 'damian', 'dylan', 'julia', 'khoi', 'sam', 'xander']);
        assert.deepStrictEqual(Array.from(cast(cfg, '2025-11-02')), ['bailey', 'damian', 'dylan', 'julia']);
        assert.deepStrictEqual(Array.from(cast({ ...cfg, trips: undefined }, '2025-11-02')), Array.from(lineup(cfg)), 'no trips: config.members');
        assert.ok(/friends: Bailey, Damian, Dylan and Julia\.$/.test(game('Intro.welcomeCopy')(cfg, '2025-11-02', '2026-11-25')[0]));
        for (const f of ['TitleScreen.js', 'Intro.js']) {
            const src = fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
            assert.ok(src.includes('CharacterSelect.lineup('), `${f} draws CharacterSelect.lineup()`);
        }
    },
    'creator donor sprites have no see-through holes, and every clothing colour is in their palette'() {
        const png = require('./png');
        const donors = JSON.parse(game('JSON.stringify(CharacterCreator.DONORS)'));
        const cuts = JSON.parse(game('JSON.stringify(CharacterCreator.CUTS)'));
        const hex = (d, i) => '#' + [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
        const bad = [];
        for (const [name, def] of Object.entries(donors)) {
            for (const [dir, cut] of Object.entries(cuts)) {
                cut.top.forEach((topStart, frame) => {
                    const file = `${name}_${dir}_frame_${frame}`;
                    const { width: W, height: H, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', file + '.png')));
                    // flood the transparent background in from the border: what is left is a hole
                    const outside = new Uint8Array(W * H), stack = [];
                    for (let x = 0; x < W; x++) stack.push(x, (H - 1) * W + x);
                    for (let y = 0; y < H; y++) stack.push(y * W, y * W + W - 1);
                    while (stack.length) {
                        const p = stack.pop();
                        if (outside[p] || data[p * 4 + 3] !== 0) continue;
                        outside[p] = 1;
                        const x = p % W;
                        if (x > 0) stack.push(p - 1);
                        if (x < W - 1) stack.push(p + 1);
                        if (p >= W) stack.push(p - W);
                        if (p < W * (H - 1)) stack.push(p + W);
                    }
                    let holes = 0;
                    const stray = new Set();
                    for (let p = 0; p < W * H; p++) {
                        if (data[p * 4 + 3] === 0) { if (!outside[p]) holes++; continue; }
                        const y = (p - p % W) / W, c = hex(data, p * 4);
                        // the torso band holds only outline, skin, hair and the donor's top/legs colours
                        if (y >= topStart && y < cut.bottom[frame] && c !== '#000000'
                            && !['skin', 'hair', 'top', 'legs'].some((slot) => def[slot].includes(c))) stray.add(c);
                    }
                    if (holes) bad.push(`${file}: ${holes} transparent pixel(s) inside the sprite`);
                    if (stray.size) bad.push(`${file}: torso colour(s) ${[...stray].join(' ')} not in DONORS.${name}`);
                });
            }
        }
        assert.deepStrictEqual(bad, []);
    },

    'the creator composes a mixed-donor character without holes, ticks or a flickering moustache (#128)'() {
        const png = require('./png');
        const frames = { front: 4, back: 4, side: 2 };
        const load = (name, dir, f) => png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', `${name}_${dir}_frame_${f}.png`)));
        const compose = (look, dir, f) => {
            const src = {};
            for (const part of ['hair', 'top', 'legs', 'beard']) if (look.parts[part]) src[part] = load(look.parts[part], dir, f);
            return game('CharacterCreator.composePixels')(src, look, dir, f);
        };
        const at = (img, x, y) => Array.from(img.data.subarray((y * img.width + x) * 4, (y * img.width + x) * 4 + 4));
        // same picture: same alpha everywhere, same colour wherever something is drawn
        const same = (a, b) => {
            for (let i = 0; i < a.data.length; i += 4) {
                if (a.data[i + 3] !== b.data[i + 3]) return false;
                if (a.data[i + 3] && (a.data[i] !== b.data[i] || a.data[i + 1] !== b.data[i + 1] || a.data[i + 2] !== b.data[i + 2])) return false;
            }
            return true;
        };
        const look = (hair, top, legs, colors) => ({ parts: { hair, top, legs, beard: null },
            colors: Object.assign({ skin: '#f6c39a', hair: '#3c2e20', top: '#3a6fd8', legs: '#2b2b33', beard: null }, colors) });

        // one donor for every part, nothing recoloured: the composite IS the donor sprite (the tidy rules touch nothing)
        for (const name of game('Object.keys(CharacterCreator.DONORS)')) {
            const own = { parts: { hair: name, top: name, legs: name, beard: null }, colors: {} };
            for (const [dir, n] of Object.entries(frames)) {
                for (let f = 0; f < n; f++) {
                    assert.ok(same(compose(own, dir, f), load(name, dir, f)), `${name}_${dir}_${f} composed from itself changed`);
                }
            }
        }

        // 1. damian's top over someone else's legs: his own trouser pixels in the torso band are filled, not holes
        const cuts = JSON.parse(game('JSON.stringify(CharacterCreator.CUTS)'));
        for (const [dir, n] of Object.entries(frames)) {
            for (let f = 0; f < n; f++) {
                const out = compose(look('james', 'damian', 'bailey'), dir, f), top = load('damian', dir, f);
                for (let y = cuts[dir].top[f]; y < cuts[dir].bottom[f]; y++) {
                    for (let x = 0; x < out.width; x++) {
                        if (at(top, x, y)[3]) assert.ok(at(out, x, y)[3], `hole at ${x},${y} of ${dir} frame ${f}`);
                    }
                }
            }
        }
        // 2. james's head on another top, side frame 1: the outline of his own high sleeve is gone
        const side = compose(look('james', 'bailey', 'bailey'), 'side', 1);
        const wearsIt = load('bailey', 'side', 1);
        for (let y = 32; y < 36; y++) {
            for (let x = 16; x < 20; x++) assert.ok(!at(side, x, y)[3] || at(wearsIt, x, y)[3], `stray sleeve outline at ${x},${y}`);
        }
        // 3. dylan's head with dyed hair: the inside of his open mouth keeps its colour in every frame
        const dark = [0x1c, 0x15, 0x0e, 255];
        let mouths = 0;
        for (const [dir, f] of [['front', 1], ['front', 3], ['side', 0], ['side', 1]]) {
            const out = compose(look('dylan', 'dylan', 'dylan', { hair: '#ff7eb6' }), dir, f), own = load('dylan', dir, f);
            for (let p = 0; p < out.width * out.height; p++) {
                const x = p % out.width, y = (p - x) / out.width;
                if (at(own, x, y).join() !== '229,59,68,255') continue;      // a mouth pixel
                for (const [nx, ny] of [[x - 2, y], [x + 2, y], [x, y - 2], [x, y + 2]]) {
                    if (at(own, nx, ny).join() === dark.join()) { mouths++; assert.deepStrictEqual(at(out, nx, ny), dark, `${dir} ${f}: mouth interior at ${nx},${ny} dyed`); }
                }
            }
        }
        assert.ok(mouths > 0, 'dylan has no open-mouth pixels to check');
        // 4. the shoulder line is closed: an outline pixel the top donor draws right above its own shirt is there,
        //    however narrow the head donor's shoulders are
        const donors = JSON.parse(game('JSON.stringify(CharacterCreator.DONORS)'));
        const hex = (px) => '#' + px.slice(0, 3).map((v) => v.toString(16).padStart(2, '0')).join('');
        let closed = 0;
        for (const hair of Object.keys(donors)) {
            for (const top of Object.keys(donors).filter((t) => t !== hair)) {
                for (const [dir, n] of Object.entries(frames)) {
                    for (let f = 0; f < n; f++) {
                        const out = compose(look(hair, top, top), dir, f), t = load(top, dir, f), h = load(hair, dir, f);
                        for (let y = cuts[dir].top[f] - 2; y < cuts[dir].top[f]; y++) {
                            for (let x = 0; x < out.width; x++) {
                                if (hex(at(t, x, y)) !== '#000000' || !at(t, x, y)[3] || !donors[top].top.includes(hex(at(t, x, y + 2)))) continue;
                                assert.ok(at(out, x, y)[3], `${hair} head / ${top} top ${dir} ${f}: open shoulder line at ${x},${y}`);
                                if (hex(at(h, x, y)) !== '#000000') closed++;      // not simply the head donor's own outline
                            }
                        }
                    }
                }
            }
        }
        assert.ok(closed > 0, 'no donor pair has shoulders of different widths: the check tests nothing');
        // 5. julia's top on another head (#160): her long hair is not worn with it. Side view: the strand of outline
        //    behind the shoulder is gone. Back view: no see-through hole where the hair was, and the hair's lower
        //    outline is shirt, not a dark band — and no mixed composite at all has a hole.
        assert.strictEqual(at(compose(look('james', 'julia', 'julia'), 'side', 0), 14, 36)[3], 0, 'stray strand outline behind the shoulder (side 0)');
        assert.strictEqual(at(compose(look('dylan', 'julia', 'julia'), 'side', 1), 14, 36)[3], 0, 'stray strand outline behind the shoulder (side 1)');
        const shirt = Array.from(game('CharacterCreator.hslToRgb')(...Object.values(game('CharacterCreator.rgbToHsl')(0x3a, 0x6f, 0xd8)))).concat(255);
        const back = compose(look('james', 'julia', 'julia'), 'back', 0);
        for (let x = 22; x < 40; x++) {
            for (const y of [36, 38]) assert.deepStrictEqual(at(back, x, y), shirt, `back of julia's top at ${x},${y} is not shirt`);
        }
        const holed = [];
        for (const hair of Object.keys(donors)) {
            for (const top of Object.keys(donors)) {
                for (const [dir, n] of Object.entries(frames)) {
                    for (let f = 0; f < n; f++) {
                        const { width: W, height: H, data } = compose(look(hair, top, top), dir, f);
                        // flood the transparent background in from the border: what is left is a hole
                        const outside = new Uint8Array(W * H), stack = [];
                        for (let x = 0; x < W; x++) stack.push(x, (H - 1) * W + x);
                        for (let y = 0; y < H; y++) stack.push(y * W, y * W + W - 1);
                        while (stack.length) {
                            const p = stack.pop();
                            if (outside[p] || data[p * 4 + 3] !== 0) continue;
                            outside[p] = 1;
                            const x = p % W;
                            if (x > 0) stack.push(p - 1);
                            if (x < W - 1) stack.push(p + 1);
                            if (p >= W) stack.push(p - W);
                            if (p < W * (H - 1)) stack.push(p + W);
                        }
                        if (outside.some((o, p) => !o && data[p * 4 + 3] === 0)) holed.push(`${hair} head / ${top} top ${dir} ${f}`);
                    }
                }
            }
        }
        assert.deepStrictEqual(holed, [], 'see-through hole inside a composed character');

        // tools/generate_cast.py is a port of the same compose: the frames it baked are what the creator draws
        const py = fs.readFileSync(path.join(__dirname, 'generate_cast.py'), 'utf8');
        const looks = JSON.parse(py.match(/^LOOKS = (\{[\s\S]*?\n\})\n/m)[1].replace(/'/g, '"').replace(/\bNone\b/g, 'null').replace(/,(\s*[}\]])/g, '$1'));
        assert.ok(Object.keys(looks).length > 0);
        for (const [name, l] of Object.entries(looks)) {
            for (const [dir, n] of Object.entries(frames)) {
                for (let f = 0; f < n; f++) {
                    assert.ok(same(compose(l, dir, f), load(name, dir, f)), `${name}_${dir}_frame_${f}.png is not what the creator composes for that look`);
                }
            }
        }
    },

    'the retired office-bin sprite is gone, and nothing still points at its palette slot'() {
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const key = 'office-bin_0_0';
        assert.ok(!(key in cfg.spriteMetadata), 'still in spriteMetadata (loaded at boot, offered in the editor)');
        assert.ok(!(key in (cfg.tileNames || {})), 'still in tileNames');
        assert.ok(!fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), 'the PNG is still there');
        // tilePalette is positional: the slot stays so every later index keeps its meaning
        const slot = cfg.tilePalette.indexOf(key);
        assert.ok(slot >= 0, 'the palette slot was removed: every later tile index has shifted');
        for (const [name, room] of Object.entries(cfg.rooms)) {
            for (const layer of room.layers || []) {
                for (const [xy, t] of Object.entries(layer.tiles || {})) {
                    assert.ok(t !== slot && t !== key, `${name} ${layer.name} @${xy} places the retired ${key}`);
                }
            }
        }
    },

    'dialogue hint names the keys, or the touch controls'() {
        const hintText = game('DialogueManager.hintText');
        assert.strictEqual(hintText(false, ''), 'SPACE/ENTER: continue | ESC: close');
        assert.strictEqual(hintText(false, ' (2/3)'), 'SPACE/ENTER: continue (2/3) | ESC: close');
        assert.strictEqual(hintText(true, ' (2/3)'), 'TAP: continue (2/3) | B: close');
    },

    'world name labels are put away while a dialogue is open'() {
        const label = () => ({ visible: true, setPosition() {}, setVisible(v) { this.visible = v; } });
        const here = { sprite: { x: 0, y: 0, visible: true }, nameLabel: label() };
        const riding = { sprite: { x: 0, y: 0, visible: false }, nameLabel: label() };
        const mgr = game('Object.create(NPCManager.prototype)');
        let talking = false;
        mgr.scene = { GRID_SIZE: 32, dialogueManager: { isVisible: () => talking },
            roomManager: { currentRoom: 'Tokyo', rooms: { Tokyo: { npcs: [here, riding, { sprite: {} }] } } } };
        mgr.updateLabels();
        assert.deepStrictEqual([here.nameLabel.visible, riding.nameLabel.visible], [true, false]);
        talking = true;
        mgr.updateLabels();
        assert.deepStrictEqual([here.nameLabel.visible, riding.nameLabel.visible], [false, false]);
        talking = false;
        mgr.updateLabels();
        assert.deepStrictEqual([here.nameLabel.visible, riding.nameLabel.visible], [true, false]);
    },

    'a touch on a control is cancelled before Phaser can read it as a tap'() {
        const listeners = {};
        const btn = {
            classList: { toggle() {} },
            addEventListener: (type, fn, opts) => (listeners[type] = { fn, opts }),
        };
        const controls = game('Object.create(TouchControls.prototype)');
        controls.state = {};
        controls._bind(btn, 'a', { key: ' ', code: 'Space', keyCode: 32 });

        assert.ok(listeners.touchstart, 'no touchstart listener on the button');
        assert.strictEqual(listeners.touchstart.opts.passive, false, 'a passive listener cannot cancel the touch');
        const touch = { defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } };
        listeners.touchstart.fn(touch);
        assert.ok(touch.defaultPrevented, "Phaser's window handler only skips a touchstart that is defaultPrevented");

        fired.length = 0;
        listeners.pointerdown.fn({ preventDefault() {} });
        assert.deepStrictEqual(fired, ['keydown:Space'], 'the button still sends its key exactly once');
    },

    'a dialogue line is captioned with the post it came from, when that is recorded'() {
        const postForLine = game('postForLine'), postLink = game('postLink');
        const ramen = { id: '10', lines: 2, title: 'Ramen again', url: 'https://devhou.se/posts/10' };
        const trains = { id: '11', lines: 1, title: 'Trains' };
        assert.deepStrictEqual([0, 1, 2].map(i => postForLine([ramen, trains], i, 3)), [ramen, ramen, trains]);
        // states from before titles were kept say nothing, and nothing is made up for them
        assert.strictEqual(postForLine(undefined, 0, 2), null);
        assert.strictEqual(postForLine(null, 0, 2), null);
        assert.strictEqual(postForLine([{ id: '10', lines: 2 }], 0, 2), null);
        assert.strictEqual(postForLine([{ id: '10', lines: 2, title: '  ' }], 0, 2), null);
        assert.deepStrictEqual([0, 1].map(i => postForLine([{ id: '9', lines: 1 }, trains], i, 2)), [null, trains]);
        // counts that do not add up to the dialogue (a hand-edited state) credit nobody
        assert.strictEqual(postForLine([ramen, trains], 0, 4), null);
        assert.strictEqual(postForLine([{ id: '10', title: 'x' }], 0, 1), null);
        assert.strictEqual(postForLine(['10'], 0, 1), null);
        // only a web address is a link
        assert.strictEqual(postLink(ramen), 'https://devhou.se/posts/10');
        assert.strictEqual(postLink(trains), null);
        assert.strictEqual(postLink({ url: 'javascript:alert(1)' }), null);
        assert.strictEqual(postLink(null), null);

        // posts belong to the dialogue they were written with: a later state
        // that changes the lines without naming posts does not inherit them
        const resolveNpc = game('resolveNpc');
        const npc = { name: 'B', dialogue: ['base'], states: {
            '2031-01-01': { dialogue: ['a', 'b'], posts: [ramen] },
            '2031-01-02': { gridX: 4 },
            '2031-01-03': { dialogue: ['c', 'd'] },
        } };
        assert.strictEqual(resolveNpc(npc, '2031-01-02').posts[0], ramen);
        assert.strictEqual(resolveNpc(npc, '2031-01-03').posts, null);
        assert.strictEqual(resolveNpc(npc, '2030-12-31').posts, undefined);
    },

    'a long post title is cut to fit its caption'() {
        const captionText = game('DialogueManager.captionText');
        const measure = (s) => Array.from(s).length * 8;      // a monospace font
        assert.strictEqual(captionText({ title: '  Ramen,\n again ' }, 320, measure), 'from: Ramen, again');
        const long = captionText({ title: 'A very long title about nothing much at all, really, honestly' }, 320, measure);
        assert.ok(measure(long) <= 320 && long.startsWith('from: A very long title') && long.endsWith('…'), long);
        assert.ok(!long.endsWith(' …'), long);
        const ja = captionText({ title: 'あ'.repeat(80) }, 320, measure);
        assert.ok(measure(ja) <= 320 && ja.endsWith('…'), ja);
        assert.strictEqual(captionText({ title: 'Exactly forty characters wide, this one.'.slice(0, 34) }, 320, measure).endsWith('…'), false);
    },

    'every catalogue item and every fish has an icon that draws'() {
        const SHAPES = game('ItemIcons.SHAPES'), pixels = game('ItemIcons.pixels'), specFor = game('ItemIcons.specFor');
        for (const [name, rows] of Object.entries(SHAPES)) {
            assert.strictEqual(rows.length, 16, name);
            for (const row of rows) assert.ok(/^[.oweakbcd]{16}$/.test(row), `${name}: "${row}"`);
        }
        const items = Array.from(game('Shop.DEFAULT_ITEMS.concat(Shop.fishItems())'));
        const drawn = new Set();
        for (const item of items) {
            assert.ok(item.icon && SHAPES[item.icon.shape], `${item.id} names no icon shape`);
            const px = Array.from(pixels(item), row => Array.from(row));
            assert.ok(px.flat().filter(Boolean).length > 40, `${item.id} icon is nearly empty`);
            for (const c of px.flat()) assert.ok(c === null || /^#[0-9a-f]{6}$/.test(c), `${item.id}: ${c}`);
            drawn.add(JSON.stringify(px));
        }
        assert.strictEqual(drawn.size, items.length, 'two items share an identical icon');
        // an item from a config catalogue with no icon gets its category's default
        assert.strictEqual(specFor({ id: 'x', category: 'food' }).shape, game('ItemIcons.DEFAULTS.food.shape'));
        assert.strictEqual(specFor({ id: 'x', effect: {} }).shape, game('ItemIcons.DEFAULTS.drink.shape'));
        assert.strictEqual(specFor({ id: 'x', permanent: true }).shape, game('ItemIcons.DEFAULTS.gear.shape'));
        assert.strictEqual(specFor({ id: 'x', category: 'fish', icon: { shape: 'nope' } }).shape, 'fish');
        assert.strictEqual(specFor({ id: 'x', category: 'mystery' }).shape, game('ItemIcons.DEFAULTS.gear.shape'));
        assert.strictEqual(game('ItemIcons.key')({ id: 'koi' }), 'item-koi');
    },

    'a catch goes into the bag, sells for its value, and a boot is thrown back'() {
        const CATCHES = Array.from(game('Fishing.CATCHES')), sellValue = game('Shop.sellValue');
        const byId = (id) => CATCHES.find(c => c.id === id);
        assert.ok(Math.abs(CATCHES.reduce((s, c) => s + c.odds, 0) - 1) < 1e-9, 'odds sum to 1');
        // the value table is the one from before fish were items
        assert.deepStrictEqual(CATCHES.map(c => [c.name, c.value]),
            [['an old boot', 0], ['Funa', 80], ['Koi', 240], ['Unagi', 520], ['Golden Koi', 1500]]);

        const { shop, toasts, saved } = shopWith({ v: 2, money: 1000, items: { 'fishing-rod': 1 }, effects: {}, used: {} });
        assert.deepStrictEqual(Array.from(shop.addCatch(byId('old-boot'))), []);
        assert.deepStrictEqual(Object.keys(shop.items), ['fishing-rod'], 'the boot never reaches the bag');
        shop.addCatch(byId('koi')); shop.addCatch(byId('koi')); shop.addCatch(byId('funa'));
        assert.strictEqual(shop.money, 1000, 'catching pays nothing by itself');
        assert.deepStrictEqual({ ...shop.items }, { 'fishing-rod': 1, koi: 2, funa: 1 });
        assert.deepStrictEqual({ ...saved().items }, { 'fishing-rod': 1, koi: 2, funa: 1 });
        assert.strictEqual(saved().v, 3);
        assert.deepStrictEqual(Array.from(shop.sellable(), i => i.id), ['funa', 'koi'], 'only fish sell');

        for (const c of CATCHES.filter(c => c.value > 0)) assert.strictEqual(sellValue(shop.itemById(c.id), 1), c.value);
        assert.strictEqual(sellValue(shop.itemById('koi'), 3), 720);
        assert.strictEqual(sellValue(shop.itemById('onigiri'), 2), 0, 'shops do not buy their own stock back');
        assert.strictEqual(sellValue(undefined, 2), 0);

        // sell both koi at a counter: the wallet gains exactly their value
        Object.assign(shop, { visible: true, mode: 'sell', kind: 'counter', selected: 0, qty: 1 });
        shop.refreshStock();
        shop.selected = shop.stock.findIndex(i => i.id === 'koi');
        shop.qty = 5;                                  // more than held: clamped
        shop.sell();
        assert.strictEqual(shop.money, 1480);
        assert.strictEqual(shop.items.koi, undefined);
        assert.strictEqual(saved().money, 1480);
        assert.ok(toasts.pop().includes('sold 2× Koi for ¥480'));
        shop.sell(); shop.sell();                      // funa, then nothing left to sell
        assert.strictEqual(shop.money, 1560);
        assert.deepStrictEqual({ ...shop.items }, { 'fishing-rod': 1 });

        // the toast says what it was and where it went
        const msg = game('Fishing.catchMessage');
        assert.ok(/Koi!.*in your bag.*¥240/.test(msg(byId('koi'), '¥240')));
        assert.ok(/old boot.*throw it back/.test(msg(byId('old-boot'), '¥0')));
    },

    "a room's shopTitle renames its counter list: the Don Takote tills say DON TAKOTE, konbinis KONBINI (#136)"() {
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const titleFor = game('Shop.titleFor');
        const stores = Object.keys(rooms).filter(k => k.startsWith('DonTakote'));
        assert.ok(stores.length >= 3);
        for (const k of stores) {
            assert.strictEqual(titleFor('counter', rooms[k]), 'DON TAKOTE', k);
            assert.strictEqual(titleFor('drinks', rooms[k]), 'DRINKS', 'shelves keep their own title');
            assert.strictEqual(titleFor('vending', rooms[k]), 'VENDING MACHINE');
        }
        const konbini = Object.keys(rooms).find(k => k.startsWith('Konbini'));
        assert.strictEqual(titleFor('counter', rooms[konbini]), 'KONBINI');
        assert.strictEqual(titleFor('izakaya', rooms.Izakaya), 'IZAKAYA');
        assert.strictEqual(titleFor('counter', undefined), 'KONBINI');
    },

    'a fish is only eaten grilled, as a food effect, and the first rare one is an achievement'() {
        const CATCHES = Array.from(game('Fishing.CATCHES'));
        const { shop, toasts } = shopWith({ money: 200, items: {} });
        shop.scene.player = { sprite: { setTint() {}, clearTint() {}, setScale() {}, scale: 1 } };
        shop.scene.tweens = { add: () => ({ stop() {} }) };
        shop.scene.time = { delayedCall() {} };
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'funa'))), []);
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'unagi'))), ['Big Catch']);
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'golden-koi'))), [], 'only the first time');
        const progress = Array.from(shop.scene.achievementManager.itemProgress(), a => a.name);
        assert.deepStrictEqual(progress, ['Taste Tester', 'Regular Customer', 'Big Catch']);

        shop.use('unagi');                               // from the Items screen: raw
        assert.strictEqual(shop.items.unagi, 1);
        assert.ok(/sell it/.test(toasts.pop()));
        assert.deepStrictEqual(Object.keys(shop.effects), []);
        shop.use('unagi', { grilled: true });
        assert.strictEqual(shop.items.unagi, undefined);
        assert.strictEqual(shop.effects.food.name, 'Grilled Unagi');
        assert.strictEqual(shop.buff('speed'), 1.4);
        assert.ok(/Grilled Unagi: speed \+40% for 3:00/.test(toasts.pop()));
        // fish are not part of "try every food and drink"
        assert.strictEqual(shop.consumables().length, 12);
        assert.ok(shop.consumables().every(i => !i.sell));
    },

    'saves from before fish load untouched, and nobody loses money'() {
        // issue #12 blob
        let s = shopWith({ money: 1234, items: { 'zone-energy': 2 } });
        assert.strictEqual(s.shop.money, 1234);
        assert.deepStrictEqual({ ...s.shop.items }, { 'zone-energy': 2 });
        assert.deepStrictEqual({ ...s.shop.caught }, {});
        // issue #46 blob, with a running effect and counters
        const until = Date.now() + 20000;
        s = shopWith({ v: 2, money: 77, items: { 'fishing-rod': 1, onigiri: 3 }, used: { onigiri: 4 },
            effects: { food: { id: 'onigiri', until } } });
        assert.strictEqual(s.shop.money, 77);
        assert.deepStrictEqual({ ...s.shop.items }, { 'fishing-rod': 1, onigiri: 3 });
        assert.deepStrictEqual({ ...s.shop.used }, { onigiri: 4 });
        assert.strictEqual(s.shop.effects.food.until, until);
        assert.deepStrictEqual(Array.from(s.shop.sellable()), []);
        s.shop.save();
        assert.deepStrictEqual({ ...s.saved() }.money, 77);
        // v3 round trip, including a grilled-fish effect
        s = shopWith({ v: 3, money: 10, items: { koi: 2 }, caught: { koi: 5, unagi: 1 },
            effects: { food: { id: 'koi', until } } });
        assert.deepStrictEqual({ ...s.shop.caught }, { koi: 5, unagi: 1 });
        assert.strictEqual(s.shop.effects.food.name, 'Grilled Koi');
        assert.ok(s.shop.scene.achievementManager.fishingProgress()[0].complete);
        // no save at all, and a corrupt one: the starting wallet
        assert.strictEqual(shopWith(null).shop.money, 5000);
        assert.strictEqual(shopWith('{not json').shop.money, 5000);
    },

    'the showdown stake: the pool scales, and only what the wallet covers is on offer'() {
        const STAKES = Array.from(game('DrinkingGame.STAKES')), pool = game('DrinkingGame.pool');
        const next = game('DrinkingGame.nextStake'), affordable = game('DrinkingGame.affordable');
        assert.deepStrictEqual(STAKES.map(o => o.stake), [0, 500, 2000]);
        assert.deepStrictEqual(STAKES.map(o => pool(o, 1)), [100, 1000, 4000]);
        assert.deepStrictEqual(STAKES.map(o => pool(o, 1.5)), [150, 1250, 5000], 'Karaage adds to the winnings, not the stake');
        for (const o of STAKES) assert.ok(pool(o, 1) > o.stake, 'a win always beats getting the stake back');
        assert.deepStrictEqual(STAKES.map(o => affordable(o, 499)), [true, false, false]);
        assert.deepStrictEqual(STAKES.map(o => affordable(o, 500)), [true, true, false]);
        assert.strictEqual(next(0, 1, 5000), 1);
        assert.strictEqual(next(1, 1, 5000), 2);
        assert.strictEqual(next(2, 1, 5000), 2, 'no wrap');
        assert.strictEqual(next(0, -1, 5000), 0);
        assert.strictEqual(next(0, 1, 499), 0, 'nothing affordable to the right');
        assert.strictEqual(next(1, 1, 1999), 1);
        assert.strictEqual(next(2, -1, 5000), 1);
    },

    'the showdown: losing costs exactly the stake, winning pays the pool, leaving first is free'() {
        const STAKES = Array.from(game('DrinkingGame.STAKES'));
        const round = (stakeIndex, money, how, opts = {}) => {
            const { g, shop } = showdownWith(money, opts.player || 'bailey', opts.bonus);
            g.setStake(stakeIndex);
            if (how === 'leave-first') { g.leave(); return shop.money - money; }
            g.begin();
            if (how === 'walk-out') { g.leave(); return shop.money - money; }
            const presses = { win: 200, lose: 0 }[how];
            if (how === 'draw') g.playerScore = g.opponentScore = 7;
            else for (let i = 0; i < presses; i++) g.press();
            if (how !== 'draw' && g.opponent === 'damian') g.opponentScore = 75;
            g.scene.time.now = g.deadline;             // the buzzer
            g.finish();
            assert.strictEqual(g.staked, 0);
            return shop.money - money;
        };
        STAKES.forEach((o, i) => {
            assert.strictEqual(round(i, 5000, 'win'), o.winnings, `${o.id} win`);
            assert.strictEqual(round(i, 5000, 'win', { bonus: 1.5 }), o.winnings * 1.5, `${o.id} win with Karaage`);
            assert.strictEqual(round(i, 5000, 'lose'), 0 - o.stake, `${o.id} loss`);
            assert.strictEqual(round(i, 5000, 'draw'), 0, `${o.id} draw`);
            assert.strictEqual(round(i, 5000, 'walk-out'), 0 - o.stake, `${o.id} walked out mid-round`);
            assert.strictEqual(round(i, 5000, 'leave-first'), 0, `${o.id} left before the round`);
            // the Bailey mirror: as Damian you always lose by ten, and it costs the stake
            assert.strictEqual(round(i, 5000, 'win', { player: 'damian' }), 0 - o.stake, `${o.id} vs Bailey`);
        });
        // the buzzer can ring with the clock a hair short of the deadline: Bailey still finds all ten (#132)
        const early = showdownWith(5000, 'damian').g;
        early.begin();
        for (let i = 0; i < 40; i++) early.press();
        early.scene.time.now = early.deadline - 3;
        early.finish();
        assert.deepStrictEqual([early.playerScore, early.opponentScore, early.baileyBonus], [40, 50, 10]);
        // a stake the wallet cannot cover is never taken: the pick stays on the friendly round
        assert.strictEqual(round(2, 1999, 'lose'), 0);
        assert.strictEqual(round(1, 499, 'win'), 100);
        assert.strictEqual(round(1, 500, 'lose'), -500, 'the whole wallet can ride on it');
        // picking a stake the wallet cannot cover says why, and changes nothing
        const { g, shop } = showdownWith(1500, 'bailey');
        const said = [];
        shop.toast = (m) => said.push(m);
        g.setStake(2);
        assert.strictEqual(g.stakeIndex, 0);
        assert.ok(/BIG TAB needs .*2,?000.*1,?500/.test(said[0]), said[0]);
        // the result screen: ENTER leaves at once, SPACE (the touch A button) only after a beat
        g.begin(); g.scene.time.now = g.deadline; g.finish();
        g.keys = { space: {}, enter: {}, esc: {}, left: {}, right: {}, a: {}, d: {} };
        ctx.Phaser = { Input: { Keyboard: { JustDown: (k) => k === g.keys.space } } };
        try {
            g.handleInput();
            assert.strictEqual(g.state, 'result', 'a late mash does not dismiss the result');
            g.scene.time.now += game('DrinkingGame.RESULT_GRACE_MS');
            g.handleInput();
            assert.strictEqual(g.state, 'idle');
        } finally { delete ctx.Phaser; }
        // a toast stays up long enough to read: the achievement waits for the whole catch line
        const toastMs = game('Shop.toastMs');
        assert.strictEqual(toastMs('ok'), 1800);
        assert.ok(toastMs(game('Fishing.catchMessage')({ name: 'Unagi', value: 520 }, '¥520')) > 3000);
    },

    'touch hints name both d-pad axes: up/down is the d-pad, left/right its arrows'() {
        const text = game('Hints.text');
        const touch = { touchControls: { enabled: true } };
        const shopLine = '↑/↓ pick · ←/→ quantity · ESC step away';
        assert.strictEqual(text({}, shopLine), shopLine, 'the keyboard wording is untouched');
        assert.strictEqual(text(touch, shopLine), 'd-pad pick · ◀ ▶ quantity · B step away');
        assert.strictEqual(text(touch, '←/→: stake · SPACE/ENTER: start · ESC: leave'), '◀ ▶: stake · A: start · B: leave');
        // no hint in the game is left with a keyboard arrow once touch has reworded it
        const fs = require('fs'), path = require('path');
        const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap(e =>
            e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.js') ? [path.join(d, e.name)] : []);
        let seen = 0;
        for (const f of walk(path.join(__dirname, '..', 'src'))) {
            for (const m of fs.readFileSync(f, 'utf8').matchAll(/Hints\.text\([^,]+,\s*(?:[^'`]*\?\s*)?'([^']*)'/g)) {
                seen++;
                assert.ok(!/[←→↑↓]/.test(text(touch, m[1])), `${path.basename(f)}: ${text(touch, m[1])}`);
            }
        }
        assert.ok(seen > 10, 'found the hint lines');
    },

    'a toast slides off the overlay panel it would cover, when there is room'() {
        const clearOf = game('UIScale.clearOf');
        const toast = { x0: 310, y0: 856, x1: 970, y1: 904 };          // 48px tall, authored near the bottom
        const showdown = { x0: 13, y0: 76, x1: 1267, y1: 884 };        // 844x390: 76px strips over and under
        assert.strictEqual(clearOf(toast, showdown, 960), 42, 'centred in the strip under the panel');
        assert.strictEqual(clearOf({ ...toast, y0: 100, y1: 148 }, showdown, 960), -86, 'the strip over it when that is nearer');
        assert.strictEqual(clearOf(toast, { ...showdown, y1: 940 }, 960), -842, 'over it when the strip under is too thin');
        assert.strictEqual(clearOf(toast, { ...showdown, y0: 12, y1: 948 }, 960), 0, 'stays put when the panel fills the canvas');
        assert.strictEqual(clearOf(toast, { ...showdown, y1: 850 }, 960), 0, 'stays put when it covers nothing');
        assert.strictEqual(clearOf(toast, { ...showdown, x1: 300 }, 960), 0, 'beside the panel is not on it');
    },

    'the Japanese pixel font covers every family the game loads and every Japanese character it shows'() {
        const families = game('JapaneseFont.FAMILIES'), covers = game('JapaneseFont.covers');
        // every family GameScene.preload loads gets the Japanese face, and the font + its licence ship
        const loaded = Array.from(fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8')
            .matchAll(/this\.load\.font\('([^']+)'/g), (m) => m[1]);
        assert.deepStrictEqual(Array.from(families).sort(), loaded.sort());
        const font = fs.readFileSync(path.join(GV2, game('JapaneseFont.URL')));
        assert.strictEqual(font.readUInt32BE(0), 0x00010000, 'a TrueType file');
        assert.ok(fs.existsSync(path.join(GV2, 'fonts', 'DotGothic16-OFL.txt')), 'the OFL text ships beside the font');
        assert.strictEqual(game('JapaneseFont.unicodeRange()').split(', ')[1], 'U+3000-30FF');
        // Latin, digits, arrows and the d-pad glyphs stay with the Latin fonts
        for (const s of ['Kanpai!', '¥1,200', '←/→ ◀ ▶ ↑/↓', '…', '', null]) assert.strictEqual(covers(s), false, String(s));
        for (const s of ['あ', 'カ', '郷', '、', '「', '！', 'ＡＢ', 'ｶﾞ', 'from: 富山から白川郷まで']) assert.strictEqual(covers(s), true, s);
        // whatever the dialogue wrapper treats as Japanese, the font's unicode-range takes
        const CJK = game('DialogueManager.CJK');
        const walk = (v) => {
            if (typeof v === 'string') { for (const ch of v) if (CJK.test(ch)) assert.ok(covers(ch), `${ch} in ${v}`); }
            else if (v && typeof v === 'object') Object.values(v).forEach(walk);
        };
        walk(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms);
        // the studio page has its own families (CSS, not JapaneseFont.load): each Latin face has a Japanese twin
        const faces = Array.from(fs.readFileSync(path.join(GV2, 'studio', 'index.html'), 'utf8').matchAll(/@font-face\s*{([^}]*)}/g), (m) => ({
            key: /font-family:\s*'([^']+)'/.exec(m[1])[1] + (/font-weight:\s*bold/.test(m[1]) ? ' bold' : ''),
            japanese: m[1].includes(path.basename(game('JapaneseFont.URL'))),
            range: (/unicode-range:\s*([^;]+);/.exec(m[1]) || [])[1],
        }));
        const latin = faces.filter((f) => !f.japanese).map((f) => f.key).sort();
        assert.ok(latin.length > 0, 'the studio declares its fonts');
        assert.deepStrictEqual(faces.filter((f) => f.japanese).map((f) => f.key).sort(), latin);
        for (const f of faces) assert.strictEqual(f.range, f.japanese ? game('JapaneseFont.unicodeRange()') : undefined, f.key);
        // retry() only acts after a failed load (loading === null), never before the first one
        assert.strictEqual(game('JapaneseFont.loading'), undefined);
        assert.strictEqual(game('JapaneseFont.retry({})'), undefined);
    },

    'a Text showing Japanese gets rows above and below its Latin line box, Latin text none'() {
        const fit = game('JapaneseFont.fit'), rows = game('JapaneseFont.padRows');
        // 2.4px over the 24px ascent, 1.4px under PressStart2P's 16px box: an eighth of an em covers both
        assert.deepStrictEqual(['16px', '24px', '32px', 20].map(rows), [2, 3, 4, 3]);
        const text = (str, fontSize, padding) => ({
            text: str, style: { fontSize }, padding: { left: 0, right: 0, top: 0, bottom: 0, ...padding }, sets: 0,
            setText(v) { this.text = v; return this; },
            setPadding(left, top, right, bottom) { this.padding = { left, top, right, bottom }; this.sets++; return this; },
        });
        const name = text('グミ', '16px', { left: 5, right: 7 });
        assert.strictEqual(fit(name), name, 'chains');
        assert.deepStrictEqual({ ...name.padding }, { left: 5, top: 2, right: 7, bottom: 2 }, 'same above and below, sides kept');
        fit(name);
        assert.strictEqual(name.sets, 1, 'no redraw when nothing changes');
        assert.deepStrictEqual({ ...fit(name.setText('Gumi')).padding }, { left: 5, top: 0, right: 7, bottom: 0 }, 'gone with the Japanese');
        const latin = fit(text('devhou.se | Shibuya | ', '16px'));
        assert.strictEqual(latin.sets, 0, 'Latin text is never touched');
        assert.strictEqual(fit(text('Kanpai 東京 ✦', '24px')).padding.top, 3);
        // a bottom-anchored label pads the top only, so its baseline stays put
        const label = fit(text('グミ東京', '16px'), { below: false });
        assert.deepStrictEqual([label.padding.top, label.padding.bottom, label.sets], [2, 0, 1]);
        assert.deepStrictEqual([fit(label, { below: false }).sets, fit(label.setText('Gumi'), { below: false }).padding.top], [1, 0]);
        // the places that show a typed name or a room name ask for it
        const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
        assert.ok(/playerNameLabel\.setText\(name\), \{ below: false \}\)/.test(src('GameScene.js')) && /JapaneseFont\.fit\(this\.hudText\.setText/.test(src('GameScene.js')));
        assert.ok(/JapaneseFont\.fit\(o\)/.test(src('CharacterSelect.js')));
    },

    'the konbini drinks cooler fills its two cells and keeps its size and anchor'() {
        const png = require('./png');
        const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'office-fridge_0_0.png')));
        assert.deepStrictEqual([width, height], [64, 128]);
        let x0 = width, x1 = -1, y0 = height, y1 = -1, glass = 0;
        for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
            const p = (y * width + x) * 4;
            if (data[p + 3] === 0) continue;
            x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
            if (data[p] === 0xb3 && data[p + 1] === 0xe5 && data[p + 2] === 0xfc) glass++;      // the lit interior
        }
        assert.deepStrictEqual([x0, x1, y0, y1], [0, 63, 0, 127], 'art reaches every edge of the 1x2 footprint');
        assert.ok(glass > 500, 'a lit glass door, not a blank cabinet');
        const meta = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).spriteMetadata['office-fridge_0_0'];
        assert.deepStrictEqual([meta.anchorX, meta.anchorY], [0.5, 0.25]);
    },

    'lint reachability starts where the player arrives, not at a fixed cell'() {
        const walkedFrom = game('WorldModel.walkedFrom');
        // A sealed 1-cell pocket at 0,0 (the old seed), a 2x3 hall, and a 2-cell closet.
        const cells = new Set(['0,0', '2,0', '3,0', '2,1', '3,1', '2,2', '3,2', '6,0', '6,1']);
        const sorted = (set) => [...set].sort().join(' ');
        const hall = '2,0 2,1 2,2 3,0 3,1 3,2';
        assert.strictEqual(sorted(walkedFrom(cells, [[3, 2]])), hall, 'floods from the arrival cell');
        assert.strictEqual(sorted(walkedFrom(cells, [[3, 2], [6, 1]])), hall + ' 6,0 6,1', 'every arrival counts');
        assert.strictEqual(sorted(walkedFrom(cells, [[5, 5]])), hall, 'a blocked arrival falls back to the largest area');
        assert.strictEqual(sorted(walkedFrom(cells, [])), hall, 'so does a room nothing leads to');
        assert.strictEqual(walkedFrom(new Set(), [[0, 0]]).size, 0);
    },

    'studio stacks overlapping districts the way the stitched city does: the later one on top'() {
        const stackOrder = game('WorldModel.stackOrder');
        const cities = { C: { rooms: [{ room: 'Tokyo' }, { room: 'Market' }, { room: 'Gone' }, { room: 'Palace' }, { room: 'Park' }] } };
        const keys = ['Inaka', 'Market', 'Osaka', 'Palace', 'Park', 'Tokyo', 'Yukimura'];
        assert.strictEqual(stackOrder({ cities }, keys).join(), 'Inaka,Tokyo,Osaka,Market,Palace,Park,Yukimura', 'districts take the city order, other rooms stay put');
        assert.strictEqual(keys[1], 'Market', 'the list passed in is left alone');
        assert.strictEqual(stackOrder({}, keys).join(), keys.join());
        // the real world: wherever two rooms of the map overlap, the one stacked on top is the city's owner
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8')).rooms;
        const order = stackOrder(config, Object.keys(config.rooms));
        const rect = (k) => { const r = map[k], s = r.w / r.cells[0]; return { x: Math.round(r.x / s), y: Math.round(r.y / s), w: r.cells[0], h: r.cells[1] }; };
        const rank = Object.fromEntries(Object.values(config.cities).flatMap((c) => c.rooms.map((r, i) => [r.room, i])));
        let overlaps = 0;
        for (const a of Object.keys(map)) for (const b of Object.keys(map)) {
            const p = rect(a), q = rect(b);
            if (a >= b || p.x >= q.x + q.w || q.x >= p.x + p.w || p.y >= q.y + q.h || q.y >= p.y + p.h) continue;
            overlaps++;
            assert.ok(a in rank && b in rank, `${a} and ${b} overlap on the map but are not districts of one city`);
            assert.strictEqual(order.indexOf(a) < order.indexOf(b), rank[a] < rank[b], `${a} / ${b}`);
        }
        assert.ok(overlaps >= 3, 'Tokyo/Market, Market/Palace and Palace/Park overlap');
    },

    'studio: a second click on the selected cell picks the district underneath'() {
        const stackPick = game('WorldModel.stackPick');
        const palace = { room: 'Palace', x: 38, y: 21 }, park = { room: 'Park', x: 38, y: 3 };
        const cells = [palace, park]; // bottom first: Park is drawn over Palace
        assert.strictEqual(stackPick(cells, null), park, 'the top district takes the first click');
        assert.strictEqual(stackPick(cells, { room: 'Park', x: 37, y: 3 }), park, 'a different cell selected: still the top');
        assert.strictEqual(stackPick(cells, { ...park }), palace, 'clicking the selected cell again reaches the covered seam transporter');
        assert.strictEqual(stackPick(cells, { ...palace }), park, 'and once more wraps back to the top');
        assert.strictEqual(stackPick([park], { ...park }), park, 'one room: the cell stays selected');
        assert.strictEqual(stackPick([], park), null, 'empty space selects nothing');
    },

    'lint lets the player stand at a shrine roof\'s eave tips, but not under the roof'() {
        const overheadCols = game('WorldModel.overheadCols');
        assert.strictEqual(overheadCols('shrine-top', 5).join(), '1,2,3', 'the eave columns are not under the roof');
        assert.strictEqual(overheadCols('red-shrine-top', 5).join(), '1,2,3');
        assert.strictEqual(overheadCols('temple-hallway-top', 4).join(), '0,1,2,3', 'any other overhead sprite is checked edge to edge');
        // ...and the art agrees: those two bottom-row corner cells are all but empty
        const png = require('./png');
        for (const key of ['shrine-top_0_0', 'red-shrine-top_0_0']) {
            const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
            assert.deepStrictEqual([width, height], [320, 384]);
            for (const col of [0, 4]) {
                let opaque = 0;
                for (let y = height - 64; y < height; y++) for (let x = col * 64; x < col * 64 + 64; x++) if (data[(y * width + x) * 4 + 3]) opaque++;
                assert.ok(opaque < 64 * 64 * 0.15, `${key} column ${col}: ${opaque}px of roof in the bottom cell`);
            }
        }
    },

    'every shrine roof (blue and red) seals the cells it hides, as the shrine prefab does'() {
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const prefab = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', 'shrine.tmj'), 'utf8'));
        const seal = prefab.layers.find((l) => l.name === 'Colliders').data;
        let roofs = 0;
        for (const [name, room] of Object.entries(cfg.rooms)) {
            const solid = room.layers.find((l) => l.name === 'Colliders');
            for (const layer of room.layers) {
                for (const [cell, id] of Object.entries(layer.tiles)) {
                    if (!/^(red-)?shrine-top_0_0$/.test(cfg.tilePalette[id])) continue;
                    roofs++;
                    const [ox, oy] = cell.split(',').map(Number);
                    const open = [];
                    seal.forEach((gid, i) => {
                        const at = `${ox + i % prefab.width},${oy + Math.floor(i / prefab.width)}`;
                        if (gid && !(solid && at in solid.tiles)) open.push(at);
                    });
                    assert.deepStrictEqual(open, [], `${name}: the roof at ${cell} leaves cells behind it open`);
                }
            }
        }
        assert.strictEqual(roofs, 5, 'found every shrine roof: Tokyo, Machi, Asahikawa (blue), Market, Park (red)');
    },

    "Palace's east road crosses into Market and back when the city is not stitched"() {
        // the road over the east level crossing (54..56) needs its own seam transporters, like the west road's
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const seam = (from, x, y) => rooms[from].transporters.find(t => t.gridX === x && t.gridY === y);
        for (const x of [0, 1, 54, 55, 56]) {
            assert.deepStrictEqual(seam('Palace', x, 0), { gridX: x, gridY: 0, hidden: true, targetRoom: 'Market', targetX: x, targetY: 46 });
            assert.deepStrictEqual(seam('Market', x, 47), { gridX: x, gridY: 47, hidden: true, targetRoom: 'Palace', targetX: x, targetY: 1 });
        }
    },

    'the headless world model is stopped by collision tiles, like the game'() {
        const WorldModel = game('WorldModel');
        // a 4x3 room: a wall tile at 2,1 on a collision layer, a rug at 1,2 on a plain one
        const config = {
            game: { gridSize: 64, worldWidth: 256, worldHeight: 192 },
            player: { startRoom: 'Hall', startX: 1, startY: 1, sprite: 'bailey_front' },
            rooms: { Hall: { name: 'Hall', objects: [], transporters: [], npcs: [], layers: [
                { name: 'floor', z: 0, tiles: { '1,2': 'rug' } },
                { name: 'walls', z: 1, collision: true, tiles: { '2,1': 'wall' } },
            ] } },
        };
        const w = new WorldModel(config, { exists: () => true, sizeOf: () => [1, 1] }, { date: '2025-10-10' });
        assert.strictEqual(w.roomManager.isBlocked(2, 1), true, 'the room manager knows the collider');
        assert.strictEqual(w.canStep(1, 1, 2, 1), false, 'a collision tile blocks the step');
        assert.strictEqual(w.canStep(1, 1, 1, 2), true, 'a tile on a non-collision layer does not');
        assert.strictEqual(w.canStep(1, 1, 0, 1), true, 'nor does bare floor');
        assert.strictEqual(w.canStep(0, 1, -1, 1), false, 'the room edge still does');
    },
    'the world check flags a trip stay with no cell (players would start at the trip home instead)'() {
        const WorldModel = game('WorldModel');
        const room = (name) => ({ name, objects: [], npcs: [], layers: [], transporters: [
            { gridX: 0, gridY: 0, targetRoom: name === 'North' ? 'South' : 'North', targetX: 1, targetY: 1 }] });
        const config = (south) => ({
            game: { gridSize: 64, worldWidth: 256, worldHeight: 192 },
            player: { startRoom: 'North', startX: 1, startY: 1, sprite: 'bailey_front' },
            rooms: { North: room('North'), South: room('South') },
            trips: [{ id: 't', start: '2031-01-01', end: '2031-01-09', members: [], home: { room: 'North', x: 1, y: 1 },
                stays: [{ from: '2031-01-01', room: 'North', x: 1, y: 1 }, south] }],
        });
        const found = (south) => new WorldModel(config(south), { exists: () => true, sizeOf: () => [1, 1] }, { date: '2031-01-02' })
            .survey(['2031-01-02']).problems.filter(p => /has no cell/.test(p.text));
        assert.strictEqual(found({ from: '2031-01-06', room: 'South', x: 2, y: 1 }).length, 0, 'a stay with a cell is fine');
        const bad = found({ from: '2031-01-06', room: 'South' });
        assert.strictEqual(bad.length, 1, 'one problem for the stay without x, y');
        assert.strictEqual(bad[0].room, 'South');
        // which is what the game would do with it: fall back to the trip's home, in the other room
        assert.strictEqual(game('Trips').homeFor(config({ from: '2031-01-06', room: 'South' }), '2031-01-07').room, 'North');
    },

    'play.js and the studio model the stitched Tokyo the game plays'() {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        assert.strictEqual(rm.currentRoom, 'TokyoCity');
        assert.deepStrictEqual([world.here().room, world.here().x, world.here().y, world.here().city], ['Tokyo', 29, 38, 'TokyoCity']);
        assert.deepStrictEqual(world.state().room, 'Tokyo', 'sessions are saved in district cells');
        assert.strictEqual(world.runtimeRooms().filter(k => /^(Tokyo|Market|Palace|Park|Machi)(City)?$/.test(k)).join(), 'TokyoCity');

        // colliders block (the model once walked through them): the vending machine two cells west
        assert.ok(world.step('w').moved);
        const bump = world.step('w');
        assert.strictEqual(bump.moved, false);
        assert.strictEqual(bump.interaction.kind, 'vending');

        // one walk from Tokyo into Market: no teleport, the district changes underfoot
        const to = rm.resolve('Market', 5, 24);
        const steps = world.path(to.x, to.y);
        assert.ok(steps && steps.length > 20);
        const crossings = [];
        for (const dir of steps) {
            const r = world.step(dir);
            assert.ok(r.moved && !r.transported, 'walked, never teleported');
            if (r.crossed) crossings.push(r.crossed.from + '>' + r.crossed.to);
        }
        assert.strictEqual(crossings.join(), 'Tokyo>Market');
        assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 5, 24]);
        // the woodland between the districts is scenery
        assert.strictEqual(world.canStep(to.x, to.y, to.x, -1), false);
        assert.strictEqual(rm.checkBoundary(10, 80), false);

        // check + lint run on the stitched room, and still on each district
        const { problems, reach } = world.survey(null, { npcs: false });
        assert.strictEqual(problems.length, 0, JSON.stringify(problems));
        const byRoom = world.reachByRoom(reach);
        for (const k of ['Tokyo', 'Market', 'Palace', 'Park', 'Machi']) {
            assert.ok(byRoom[k].length > 300, k);
            assert.strictEqual(JSON.stringify(world.lint(k).errors), '{}', k);
        }
        const city = world.lint('TokyoCity');
        assert.strictEqual(JSON.stringify(city.errors), '{}');
        assert.deepStrictEqual([city.width, city.height], [rm.cities.TokyoCity.width, rm.cities.TokyoCity.height]);
        assert.ok(world.drawOrder('TokyoCity').some(t => /^tree-3-top/.test(t.key)), 'the woods are part of the render');
        assert.ok(world.npcsIn('TokyoCity').every(n => n.homeRoom && rm.checkBoundary(n.gridX, n.gridY, 'TokyoCity')));
        assert.strictEqual(world.npcsIn('TokyoCity').length, ['Tokyo', 'Market', 'Palace', 'Park', 'Machi'].reduce((n, k) => n + world.npcsIn(k).length, 0));

        // --stitch=0: the five rooms, joined by seam teleports, as ?stitch=0 plays them
        const legacy = worldWith(false).world;
        assert.strictEqual(legacy.roomManager.currentRoom, 'Tokyo');
        assert.strictEqual(legacy.here().city, null);
        assert.strictEqual(Object.keys(legacy.roomManager.cities).length, 0);
        legacy.enter('Tokyo', 57, 22);
        assert.strictEqual(JSON.stringify(legacy.step('e').transported), '{"from":"Tokyo","to":"Market"}');
        assert.strictEqual(legacy.survey(null, { npcs: false }).problems.length, 0);
        // both agree on what can be reached, district by district
        const legacyReach = legacy.reachByRoom(legacy.survey(null, { npcs: false }).reach);
        for (const k of Object.keys(byRoom)) assert.strictEqual(Array.from(legacyReach[k]).sort().join(' '), Array.from(byRoom[k]).sort().join(' '), k);
    },

    'a cell two districts share is walkable by the later district\'s map'() {
        // the same case tools/test_blog_to_npc.py makes for the python port: Palace is listed
        // after Market, so a collider on Palace's copy of their shared row closes that cell
        const base = worldWith(true).world;
        const palace = base.roomManager.memberOf.Palace.member, market = base.roomManager.memberOf.Market.member;
        const open = new Set(base.reachByRoom(base.survey(null, { npcs: false }).reach).Market);
        const shared = base.reachByRoom(base.survey(null, { npcs: false }).reach).Palace.map(c => c.split(',').map(Number))
            .map(([x, y]) => [x, y, x + palace.x - market.x, y + palace.y - market.y])
            .find(([, , mx, my]) => open.has(mx + ',' + my));
        assert.ok(shared, 'Market and Palace share a walkable cell');
        const cut = worldWith(true, (config) => {
            config.rooms.Palace.layers.find(l => l.collision).tiles[shared[0] + ',' + shared[1]] = 'gk_blank';
        }).world;
        const after = cut.reachByRoom(cut.survey(null, { npcs: false }).reach);
        assert.ok(!after.Market.includes(shared[2] + ',' + shared[3]));
        assert.ok(!after.Palace.includes(shared[0] + ',' + shared[1]));
        // ...while Market's own collider there changes nothing: its tiles in that cell are left out
        const kept = worldWith(true, (config) => {
            config.rooms.Market.layers.find(l => l.collision).tiles[shared[2] + ',' + shared[3]] = 'gk_blank';
        }).world;
        assert.ok(kept.reachByRoom(kept.survey(null, { npcs: false }).reach).Market.includes(shared[2] + ',' + shared[3]));
    },

    'a bump looks its cell up in an index built once per room load'() {
        const { world, run } = worldWith(true);
        const Interactions = run('Interactions'), Shop = run('Shop');
        const opts = { sizeOf: (key) => world.cells(key), venues: Shop.VENUES };
        let cells = 0, hits = 0;
        for (const key of ['TokyoCity', 'KonbiniMarket1', 'Izakaya', 'Osaka']) {
            const room = world.roomManager.rooms[key], roomConfig = world.config.rooms[key] || {};
            const index = Interactions.index(room, roomConfig, opts);
            // find() scans every tile of the room per call: use it as written for the small rooms and
            // around every interaction; elsewhere compare against its definition (the first of all()
            // covering the cell)
            const all = Interactions.all(room, roomConfig, opts);
            const small = room.worldWidth * room.worldHeight < 64 * 64 * 800;
            for (let y = 0; y < room.worldHeight / 64; y++) {
                for (let x = 0; x < room.worldWidth / 64; x++) {
                    const near = small || all.some(i => i.group !== 'pond' && x >= i.x - 1 && x <= i.x + i.w && y >= i.y - 1 && y <= i.y + i.h);
                    for (const group of ['shop', 'pond', 'clock', 'drinking-game']) {
                        const scan = near ? Interactions.find(room, roomConfig, x, y, Object.assign({ group }, opts))
                            : all.find(i => i.group === group && x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h) || null;
                        assert.strictEqual(JSON.stringify(Interactions.lookup(index, x, y, group)), JSON.stringify(scan), `${key} ${x},${y} ${group}`);
                        if (scan) hits++;
                    }
                    assert.strictEqual(JSON.stringify(Interactions.lookup(index, x, y)),
                        JSON.stringify(all.find(i => x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h) || null));
                    cells++;
                }
            }
        }
        assert.ok(cells > 15000 && hits > 100, `${hits} interactions over ${cells} cells`);

        // RoomManager.interactionAt: built on the first bump, kept until the room's tiles are reloaded
        const rm = world.roomManager;
        rm.scene.textures = { exists: (k) => world.exists(k), get: (k) => ({ getSourceImage: () => ({ width: world.cells(k)[0] * 64, height: world.cells(k)[1] * 64 }) }) };
        let built = 0;
        const index = Interactions.index;
        Interactions.index = function () { built++; return index.apply(this, arguments); };
        const vending = rm.resolve('Tokyo', 27, 38);
        assert.strictEqual(rm.interactionAt(vending.x, vending.y, 'shop').kind, 'vending');
        assert.strictEqual(rm.interactionAt(vending.x, vending.y, 'clock'), null);
        assert.strictEqual(rm.interactionAt(vending.x + 1, vending.y, 'shop'), null);
        for (let i = 0; i < 50; i++) rm.interactionAt(i, i);
        assert.strictEqual(built, 1);
        rm.clearFloorTiles();
        rm.interactionAt(vending.x, vending.y, 'shop');
        assert.strictEqual(built, 2, 'a room change throws the index away');
        Interactions.index = index;
    },

    'collider markers feed the blocked set and never become a sprite'() {
        const { world, run } = worldWith(true);
        const RoomManager = run('RoomManager');
        const made = [];
        const sprite = (key) => {
            const s = { key, alpha: 1, data: {} };
            for (const f of ['setOrigin', 'setScale', 'setDepth', 'setTexture', 'setPosition', 'addToDisplayList', 'removeFromDisplayList', 'destroy']) s[f] = () => s;
            s.setAlpha = (a) => { s.alpha = a; return s; };
            s.setData = (k, v) => { s.data[k] = v; return s; };
            made.push(s);
            return s;
        };
        const scene = {
            GRID_SIZE: 64, config: world.config,
            textures: { exists: (k) => world.exists(k), getFrame: (k) => ({ realWidth: world.cells(k)[0] * 64, realHeight: world.cells(k)[1] * 64 }) },
            getSpriteConfig: () => ({ anchorX: 0.5, anchorY: 0.5, scale: 1 }),
            add: { sprite: (x, y, key) => sprite(key) },
            cache: { json: { get: () => null } },
        };
        for (const key of ['Tokyo', 'KonbiniMarket1', 'Osaka']) {
            const rm = new RoomManager(scene);
            rm.rooms = world.roomManager.rooms;
            rm.currentRoom = key;
            made.length = 0;
            rm.loadFloorTiles();
            const colliders = new Set();
            for (const layer of rm.rooms[key].layers) if (layer.collision) for (const xy in layer.tiles) colliders.add(xy);
            assert.ok(colliders.size > 20, key);
            assert.strictEqual([...rm.blockedCells].sort().join(' '), [...colliders].sort().join(' '), key);
            assert.ok(rm.tileRecords.length > 100 && rm.tileRecords.every(r => !r.layer.collision), key);
            assert.ok(made.every(s => s.key !== RoomManager.COLLIDER), 'no sprite for a collider marker');
            assert.strictEqual(made.length, rm.tileRecords.length);
            assert.ok(rm.chunks && rm.chunks.size > 0, 'every room is bucketed for Occlusion');
        }
        // art painted on a collision layer still blocks AND is drawn
        const rm = new RoomManager(scene);
        const fence = Object.values(world.roomManager.rooms.Tokyo.layers.find(l => l.name === 'Collidables').tiles)[0];
        rm.loadLayer({ name: 'Colliders', z: 9, collision: true, tiles: { '1,1': RoomManager.COLLIDER, '2,2': fence } });
        assert.strictEqual([...rm.blockedCells].sort().join(' '), '1,1 2,2');
        assert.strictEqual(rm.tileRecords.map(r => r.key).join(), fence);
    },

    'scenery fades while it hides someone, and their name label with it'() {
        const { run } = worldWith(true);
        const Occlusion = run('Occlusion');
        const art = (key, left, top, width, height, depth) => {
            const rec = { key, left, top, width, height, depth, sprite: { alpha: 1, setAlpha(a) { this.alpha = a; } } };
            return rec;
        };
        const label = () => ({ alpha: 1, setAlpha(a) { this.alpha = a; } });
        const roof = art('roof', 0, 0, 256, 192, 60), ground = art('path', 0, 0, 256, 256, -400);
        const fence = art('fence', 64, 96, 64, 64, 60);        // covers the lower half of someone at (96, 96)
        const torii = art('torii', 256, 0, 192, 192, 60);      // drawn over, but open in the middle
        const sign = art('ad', 448, 0, 128, 128, 60);
        const player = { sprite: { x: 96, y: 96, depth: 25, visible: true } };
        const npc = { sprite: { x: 1000, y: 96, depth: 25, visible: true }, nameLabel: label() };
        const far = { sprite: { x: 9000, y: 96, depth: 25, visible: true }, nameLabel: label() };
        const records = [roof, ground, fence, torii];
        const scene = {
            GRID_SIZE: 64, player, playerNameLabel: label(), game: { loop: { delta: 16 } },
            cameras: { main: { worldView: { x: 0, y: 0, right: 1280, bottom: 960 } } },
            roomManager: { tileRecords: records, signArt: [sign], currentRoom: 'R', rooms: { R: { npcs: [npc, far] } },
                artNear: () => records },
        };
        const oc = new Occlusion(scene);
        // every texture is solid, except the torii: only its outer thirds are
        oc.mask = (key) => key === 'torii' ? { w: 3, h: 1, bits: [1, 0, 1] } : { w: 1, h: 1, bits: [1] };
        const frames = (n) => { for (let i = 0; i < n; i++) oc.update(); };

        // behind the roof: it fades to ALPHA and the label to LABEL_ALPHA; the fence (which only
        // covers what the roof already does... and the ground under everyone) are judged apart
        const hid = (who) => oc.look(who).hits.map(r => r.key).sort().join();
        assert.strictEqual(hid(player), 'fence,roof');
        frames(30);
        assert.strictEqual(roof.fade, Occlusion.ALPHA);
        assert.strictEqual(roof.sprite.alpha, Occlusion.ALPHA);
        assert.strictEqual(scene.playerNameLabel.alpha, Occlusion.LABEL_ALPHA);
        assert.strictEqual(ground.fade, undefined, 'the ground is drawn under him');
        assert.strictEqual(npc.nameLabel.alpha, 1);
        // a streamed sprite that is re-made keeps the fade: it lives on the record
        roof.sprite = { alpha: 1, setAlpha(a) { this.alpha = a; } };
        frames(1);
        assert.strictEqual(roof.sprite.alpha, Occlusion.ALPHA);

        // half hidden (legs behind a fence, roof gone): nothing fades
        records.splice(records.indexOf(roof), 1);
        player.sprite.x = 97;
        assert.strictEqual(hid(player), '');
        frames(30);
        assert.strictEqual(fence.fade, undefined);
        assert.strictEqual(fence.sprite.alpha, 1);
        assert.strictEqual(scene.playerNameLabel.alpha, 1);
        assert.strictEqual(oc.fading.size, 0);

        // in the opening of a torii: its rectangle covers him, its pixels do not
        player.sprite.x = 352;
        assert.strictEqual(hid(player), '');
        player.sprite.x = 290;                     // ...behind a leg
        assert.strictEqual(hid(player), 'torii');
        // in front of it (drawn over it): never
        player.sprite.depth = 70;
        assert.strictEqual(hid(player), '');
        player.sprite.depth = 25;

        // an NPC behind a wall sign fades the sign and its own label, not the player's
        npc.sprite.x = 500; npc.sprite.y = 60;
        player.sprite.x = 800;
        frames(30);
        assert.strictEqual(sign.sprite.alpha, Occlusion.ALPHA);
        assert.strictEqual(npc.nameLabel.alpha, Occlusion.LABEL_ALPHA);
        assert.strictEqual(scene.playerNameLabel.alpha, 1);
        assert.strictEqual(torii.sprite.alpha, 1, 'restored once he left');
        // an NPC off camera is not looked at
        far.sprite.x = 500; far.sprite.y = 60;
        npc.sprite.x = 1000;
        scene.cameras.main.worldView = { x: 2000, y: 0, right: 3280, bottom: 960 };
        player.sprite.x = 2100;
        frames(30);
        assert.strictEqual(sign.sprite.alpha, 1);
        // ...and a label that was part-faded when its NPC left the camera is not left that way
        scene.cameras.main.worldView = { x: 0, y: 0, right: 1280, bottom: 960 };
        frames(3);
        assert.ok(far.nameLabel.alpha < 1 && far.nameLabel.alpha > Occlusion.LABEL_ALPHA, 'mid-fade');
        scene.cameras.main.worldView = { x: 2000, y: 0, right: 3280, bottom: 960 };
        frames(1);
        assert.strictEqual(far.nameLabel.alpha, 1);
        assert.strictEqual(oc.dimmed.size, 0);

        // another room: its records are new, nothing is carried over
        scene.cameras.main.worldView = { x: 0, y: 0, right: 1280, bottom: 960 };
        frames(30);
        assert.ok(oc.fading.has(sign));
        scene.roomManager.tileRecords = [];
        scene.roomManager.signArt = [];
        scene.roomManager.artNear = () => [];
        frames(1);
        assert.strictEqual(oc.fading.size, 0);
    },

    'outside the trip the game opens on a trip day, and cycles through them'() {
        const defaultGameDate = game('defaultGameDate');
        const dates = ['2025-10-02', '2025-10-03', '2025-11-18'];
        assert.strictEqual(defaultGameDate('2025-10-10', dates), '2025-10-10');
        assert.strictEqual(defaultGameDate('2025-11-19', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2025-11-21', dates), '2025-11-18');
        assert.strictEqual(defaultGameDate('2025-11-22', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2030-01-01', []), '2030-01-01');
    },

    'trips are separate ranges: today during one, a day of the last one with posts between them (#118)'() {
        const defaultGameDate = game('defaultGameDate'), T = game('Trips');
        const trips = T.of(realConfig());
        assert.deepStrictEqual(Array.from(trips, t => t.id), ['devhouse2', 'devhouse3']);
        const d2 = ['2025-10-02', '2025-10-03', '2025-11-18'];
        // during devhouse 2, as before trips were data
        assert.strictEqual(defaultGameDate('2025-10-10', d2, trips), '2025-10-10');
        // between the trips: devhouse 2's days, cycled exactly as the one-trip rule did
        for (const today of ['2025-11-19', '2025-11-21', '2025-11-22', '2026-11-25', '2027-02-17']) {
            assert.strictEqual(defaultGameDate(today, d2, trips), defaultGameDate(today, d2, []), today);
        }
        // during devhouse 3 the game is live, before anyone has posted and after
        assert.strictEqual(defaultGameDate('2027-02-18', d2, trips), '2027-02-18');
        assert.strictEqual(defaultGameDate('2027-02-28', d2, trips), '2027-02-28');
        assert.strictEqual(defaultGameDate('2027-02-20', d2.concat('2027-02-19'), trips), '2027-02-20');
        // after devhouse 3: its own post days when it has any, else devhouse 2's — never one 15-month span
        assert.strictEqual(defaultGameDate('2027-03-01', d2, trips), defaultGameDate('2027-03-01', d2, []));
        const both = d2.concat('2027-02-19', '2027-02-26');
        assert.strictEqual(defaultGameDate('2027-03-01', both, trips), '2027-02-19');
        assert.strictEqual(defaultGameDate('2027-03-02', both, trips), '2027-02-26');
        assert.strictEqual(defaultGameDate('2027-03-03', both, trips), '2027-02-19');
        assert.strictEqual(defaultGameDate('2026-06-01', both, trips), defaultGameDate('2026-06-01', d2, []), 'the gap is not a trip');
        // a config with no posts at all opens on today
        assert.strictEqual(defaultGameDate('2026-06-01', [], trips), '2026-06-01');
        // which trip a date belongs to, and where the group is based
        const trip = (d) => T.forDate(trips, d).id;
        assert.deepStrictEqual(['2025-01-01', '2025-11-02', '2026-11-25', '2027-02-03', '2027-02-04', '2027-02-18', '2027-06-01'].map(trip),
            ['devhouse2', 'devhouse2', 'devhouse2', 'devhouse2', 'devhouse3', 'devhouse3', 'devhouse3']);
        const d3 = trips[1];
        assert.deepStrictEqual(['2027-02-18', '2027-02-24', '2027-02-25', '2027-02-28'].map(d => T.stayFor(d3, d).room),
            ['Sapporo', 'Sapporo', 'Asahikawa', 'Asahikawa']);
        assert.strictEqual(T.windowFor(trips, '2027-02-26').from, '2027-02-25');
        assert.strictEqual(T.windowFor(trips, '2027-02-20').from, '2027-02-18');
        assert.strictEqual(T.windowFor(trips, '2026-11-25').from, '2025-10-02');
        assert.strictEqual(T.of({ trips: [{ id: 'x' }, { id: 'y', start: '2027-02-18', end: '2027-02-01' }] }).length, 0, 'bad trips are dropped');
    },

    'a trip opens a fortnight before it starts: a travel-day post is its own, not the last trip\'s'() {
        const defaultGameDate = game('defaultGameDate'), T = game('Trips'), resolveNpc = game('resolveNpc');
        const trips = T.of(realConfig());
        const d2 = [...game('contentChangeDates')(realConfig())].filter(d => d < '2027').sort();
        assert.strictEqual(trips[1].opens, '2027-02-04');
        assert.strictEqual(T.of({ trips: [{ id: 'a', start: '2027-02-18', end: '2027-02-20', lead: 2 }] })[0].opens, '2027-02-16');
        assert.strictEqual(T.addDays('2027-03-01', -1), '2027-02-28');
        // the lead-in window: open, not started
        const w = T.windowFor(trips, '2027-02-10');
        assert.deepStrictEqual([w.trip.id, w.early, w.from], ['devhouse3', true, '2027-02-04']);
        assert.strictEqual(T.windowFor(trips, '2027-02-18').early, false);
        assert.strictEqual(T.windowFor(trips, '2025-09-01').early, false, 'before the first trip is not a lead-in');
        assert.strictEqual(T.during(trips[1], '2027-02-10'), false, 'not a trip day: no HUD prefix, no underline');
        // a post on the way there is a devhouse 3 day, and leaves devhouse 2's days — and today's default — alone
        const withPost = d2.concat('2027-02-10');
        assert.deepStrictEqual(Array.from(T.daysOf(trips, trips[0], withPost)), d2);
        assert.deepStrictEqual(Array.from(T.daysOf(trips, trips[1], withPost)), ['2027-02-10']);
        for (const today of ['2026-11-25', '2027-02-03']) {
            assert.strictEqual(defaultGameDate(today, withPost, trips), defaultGameDate(today, d2, trips), today);
        }
        assert.strictEqual(defaultGameDate('2027-02-12', withPost, trips), '2027-02-10', 'in the lead-in, with a post: that post');
        assert.strictEqual(defaultGameDate('2027-02-12', d2, trips), defaultGameDate('2027-02-12', d2, []), 'in the lead-in, no post: devhouse 2');
        assert.strictEqual(defaultGameDate('2027-02-18', withPost, trips), '2027-02-18');
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, withPost), '2027-02-18', 'Time Travel lands on a day of the trip itself');
        // the post places its author on the lead-in days; from day one everyone is at the base
        const base = { name: 'Sam', sprite: 'sam_front', gridX: 21, gridY: 27, dialogue: ['base'], trip: 'devhouse3', stay: 'Sapporo',
            states: { '2027-02-10': { present: false } } };
        const away = { name: 'Sam', sprite: 'sam_front', gridX: 3, gridY: 3, dialogue: [], present: false,
            states: { '2027-02-10': { present: true, dialogue: ['at the airport'] }, '2025-11-01': { present: true, dialogue: ['old'] } } };
        const at = (npc, d) => { const r = resolveNpc(npc, d, trips); return r && r.dialogue[0]; };
        assert.deepStrictEqual(['2027-02-09', '2027-02-10', '2027-02-17', '2027-02-18'].map(d => at(away, d)), [null, 'at the airport', 'at the airport', null]);
        assert.deepStrictEqual(['2027-02-09', '2027-02-10', '2027-02-17', '2027-02-18'].map(d => at(base, d)), [null, null, null, 'base']);
        assert.strictEqual(at(away, '2026-11-25'), 'old');
    },

    'the HUD drops the trip name rather than run under the menu button, in every room (#118)'() {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate');
        // the HUD's metrics: PixelOperatorMono at 16px is 16px a character; 1280 wide, 10px padding, "menu" right-aligned
        const CH = 16, PAD = 10, MENU_LEFT = 1280 - PAD - 4 * CH;
        const right = (room, label, money) => PAD + CH * `${config.game.title} | ${room} | ${label} | ${money}`.length;
        const days = [...game('contentChangeDates')(config)].sort().concat('2027-02-20', '2027-02-26', '2026-11-25');
        let dropped = 0, kept = 0;
        for (const def of Object.values(config.rooms)) {
            for (const iso of days) {
                for (const money of ['¥0', '¥5,000', '¥999,999']) {
                    const fits = (label) => right(def.name, label, money) <= MENU_LEFT - 2 * PAD;
                    const label = T.dateLabel(trips, iso, fmt, fits);
                    assert.ok(fits(label), `${def.name} on ${iso} with ${money}: "${label}" ends at ${right(def.name, label, money)}`);
                    assert.ok(label.endsWith(fmt(iso)));
                    if (T.during(T.forDate(trips, iso), iso)) (label === fmt(iso) ? dropped++ : kept++);
                    else assert.strictEqual(label, fmt(iso));
                }
            }
        }
        assert.ok(dropped > 0 && kept > dropped, `the name is kept where there is room (${kept}) and dropped where there is not (${dropped})`);
        assert.strictEqual(T.dateLabel(trips, '2027-02-20', fmt, () => false), 'February 20 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-20', fmt, () => true), 'devhouse 3 · February 20 2027');
    },

    'the game date on a stubbed clock: live in devhouse 3, a devhouse 2 day between trips, ?date= wins (#118)'() {
        const days = [...game('contentChangeDates')(realConfig())].sort();
        assert.strictEqual(bootOn('2027-02-20'), '2027-02-20');
        assert.strictEqual(bootOn('2027-02-26'), '2027-02-26');
        const between = bootOn('2026-11-25');
        assert.ok(days.includes(between) && between < '2026', `between trips opens on a devhouse 2 post day, got ${between}`);
        assert.strictEqual(bootOn('2026-11-25', '?date=2025-11-02'), '2025-11-02');
        assert.strictEqual(bootOn('2027-02-20', '?date=2025-11-02'), '2025-11-02');
        assert.strictEqual(bootOn('2026-11-25', '?date=2027-02-26'), '2027-02-26');
        // the HUD names the trip on its own days only
        const label = (d) => game('Trips.dateLabel')(game('Trips.of')(realConfig()), d, game('formatGameDate'));
        assert.strictEqual(label('2027-02-20'), 'devhouse 3 · February 20 2027');
        assert.strictEqual(label('2025-11-02'), 'devhouse 2 · November 2 2025');
        assert.strictEqual(label('2026-11-25'), 'November 25 2026');
        bootOn('2026-11-25');
    },

    'base NPCs are trip-scoped: devhouse 3 stands in Sapporo then Asahikawa, and nowhere in 2025 (#131)'() {
        const config = realConfig();
        const seven = ['Bailey', 'Damian', 'Dylan', 'Julia', 'Khoi', 'Sam', 'Xander'];
        for (const d of ['2027-02-18', '2027-02-20', '2027-02-24']) {
            assert.deepStrictEqual(castOn(config, d), seven.map(n => `Sapporo/${n}`), d);
        }
        for (const d of ['2027-02-25', '2027-02-26', '2027-02-28', '2027-03-15']) {
            assert.deepStrictEqual(castOn(config, d), seven.map(n => `Asahikawa/${n}`), d);
        }
        const days = [...game('contentChangeDates')(config)].filter(d => d < '2027').sort();
        assert.ok(days.length > 20);
        for (const d of days.concat('2025-09-01', '2026-11-25', '2027-02-03')) {
            const cast = castOn(config, d);
            assert.ok(!cast.some(c => /\/(Khoi|Sam|Xander)$/.test(c)), `${d}: ${cast}`);
            assert.ok(cast.some(c => /\/(Bailey|Damian|Dylan|Julia)$/.test(c)), `${d}: devhouse 2 is there`);
        }
        // the fortnight before devhouse 3 is its lead-in: devhouse 2 is history and nobody stands at the base yet
        for (const d of ['2027-02-04', '2027-02-10', '2027-02-17']) assert.deepStrictEqual(castOn(config, d), [], d);
        // the base lines are neutral: nobody is still waiting for a trip they are on
        const resolveNpc = game('resolveNpc'), trips = game('Trips.of')(config);
        for (const room of ['Sapporo', 'Asahikawa']) {
            for (const raw of config.rooms[room].npcs) {
                const npc = resolveNpc(raw, room === 'Sapporo' ? '2027-02-20' : '2027-02-26', trips);
                assert.ok(npc && npc.dialogue.length >= 2, `${room}/${raw.name} has lines`);
                assert.ok(!/can't wait|looking forward to devhouse/i.test(npc.dialogue.join(' ')), `${room}/${raw.name}: ${npc.dialogue}`);
            }
        }
        // James is the default player sprite, never a member; the credits are left alone
        for (const t of trips) assert.ok(!t.members.includes('james'), t.id);
        assert.ok(config.credits.includes('Audio: Gloria') && config.credits.includes('Slacker: Yashuk'));
    },

    'a post inside a trip still moves its author, and history from another trip or stay does not apply'() {
        const resolveNpc = game('resolveNpc');
        const trips = game('Trips.of')({ trips: [
            { id: 'a', start: '2030-01-01', end: '2030-01-10', members: ['kim'] },
            { id: 'b', start: '2031-01-01', end: '2031-01-10', members: ['kim'],
                stays: [{ from: '2031-01-01', room: 'North' }, { from: '2031-01-06', room: 'South' }] },
        ] });
        const north = { name: 'Kim', sprite: 'kim_front', gridX: 1, gridY: 1, dialogue: ['base north'], trip: 'b', stay: 'North',
            states: { '2031-01-03': { present: true, gridX: 5, gridY: 5, dialogue: ['posted'] } } };
        const south = { name: 'Kim', sprite: 'kim_front', gridX: 2, gridY: 2, dialogue: ['base south'], trip: 'b', stay: 'South',
            states: { '2031-01-03': { present: false } } };
        const old = { name: 'Kim', sprite: 'kim_front', gridX: 9, gridY: 9, dialogue: ['base a'], trip: 'a',
            states: { '2030-01-04': { gridX: 8, dialogue: ['a post'] }, '2031-01-08': { present: true, gridX: 7, dialogue: ['back at a'] } } };
        const hidden = { name: 'Kim', sprite: 'kim_front', gridX: 3, gridY: 3, dialogue: [], present: false,
            states: { '2030-01-05': { present: true, dialogue: ['a hop'] } } };
        const at = (npc, d) => { const r = resolveNpc(npc, d, trips); return r && `${r.gridX},${r.gridY} ${r.dialogue[0]}`; };
        // trip a, and the gap after it: its own base and posts
        assert.strictEqual(at(old, '2030-01-02'), '9,9 base a');
        assert.strictEqual(at(old, '2030-06-01'), '8,9 a post');
        assert.strictEqual(at(hidden, '2030-01-06'), '3,3 a hop');
        assert.strictEqual(at(north, '2030-01-06'), null);
        // trip b before the post: base in the north, nothing of trip a
        assert.strictEqual(at(north, '2031-01-02'), '1,1 base north');
        assert.strictEqual(at(south, '2031-01-02'), null);
        assert.strictEqual(at(old, '2031-01-02'), null);
        assert.strictEqual(at(hidden, '2031-01-02'), null);
        // the post moves them, until the group moves base
        assert.strictEqual(at(north, '2031-01-04'), '5,5 posted');
        assert.strictEqual(at(north, '2031-01-06'), null);
        assert.strictEqual(at(south, '2031-01-06'), '2,2 base south');
        // a post from somewhere else entirely — even another trip's room — still places them
        assert.strictEqual(at(old, '2031-01-08'), '7,9 back at a');
        // with no trips configured nothing is scoped
        assert.strictEqual(resolveNpc(old, '2031-01-02', []).gridX, 8);
        assert.strictEqual(resolveNpc(north, '2030-01-06', []).gridX, 1);
    },

    'a returning player starts at the trip home; a new one next to the cast, never counting who they play (#96, #59)'() {
        const config = realConfig(), startFor = game('Trips.startFor'), byRoom = game('Trips.membersByRoom');
        const near = (spot, date, played) => {
            const g = byRoom(config, date, { played }).find(r => r.room === spot.room);
            return g ? Math.min(...g.members.map(m => Math.max(Math.abs(m.x - spot.x), Math.abs(m.y - spot.y)))) : Infinity;
        };
        const days = [...game('contentChangeDates')(config)].filter(d => d < '2027').sort();
        let moved = 0;
        for (const date of days) {
            // returning: Tokyo, as ever
            assert.deepStrictEqual({ ...startFor(config, date, { newPlayer: false }) }, { room: 'Tokyo', x: 29, y: 38 }, date);
            assert.deepStrictEqual({ ...startFor(config, date) }, { room: 'Tokyo', x: 29, y: 38 }, date);
            for (const played of [undefined, 'james', 'bailey', 'damian', 'dylan', 'julia']) {
                const spot = startFor(config, date, { newPlayer: true, played });
                const anyone = byRoom(config, date, { played }).length > 0;
                assert.ok(anyone, `${date} as ${played}: someone is out there`);
                const gap = near(spot, date, played);
                assert.ok(gap >= 1 && gap <= 6, `${date} as ${played}: starts ${gap} cells from someone, at ${spot.room} ${spot.x},${spot.y}`);
                assert.deepStrictEqual({ ...startFor(config, date, { newPlayer: true, played }) }, { ...spot }, 'deterministic');
                if (spot.room !== 'Tokyo') moved++;
            }
        }
        assert.ok(moved > 0, 'on some devhouse 2 days a new player starts outside Tokyo');
        // devhouse 3: Sapporo, then Asahikawa — new or returning, whoever you play
        for (const played of [undefined, 'bailey', 'khoi']) {
            for (const newPlayer of [false, true]) {
                assert.deepStrictEqual({ ...startFor(config, '2027-02-20', { newPlayer, played }) }, { room: 'Sapporo', x: 33, y: 12 });
                assert.deepStrictEqual({ ...startFor(config, '2027-02-26', { newPlayer, played }) }, { room: 'Asahikawa', x: 31, y: 12 });
            }
            assert.ok(near({ room: 'Sapporo', x: 33, y: 12 }, '2027-02-20', played) <= 6);
            assert.ok(near({ room: 'Asahikawa', x: 31, y: 12 }, '2027-02-26', played) <= 6);
        }
        // the one member in the room is who you are playing: go where somebody else is
        const tiny = { game: { gridSize: 64, worldWidth: 640, worldHeight: 640 }, player: { startRoom: 'A', startX: 1, startY: 1 },
            trips: [{ id: 't', start: '2030-01-01', end: '2030-01-09', members: ['ann', 'bob'], home: { room: 'A', x: 1, y: 1 } }],
            rooms: {
                A: { npcs: [{ name: 'Ann', sprite: 'ann_front', gridX: 3, gridY: 1, dialogue: [] }], transporters: [{ gridX: 0, gridY: 0, targetRoom: 'B', targetX: 1, targetY: 1 }],
                    layers: [{ name: 'Floor', tiles: Object.fromEntries([...Array(100)].map((_, i) => [`${i % 10},${Math.floor(i / 10)}`, 'f'])) }] },
                B: { npcs: [{ name: 'Bob', sprite: 'bob_front', gridX: 8, gridY: 8, dialogue: [] }], transporters: [],
                    layers: [{ name: 'Floor', tiles: Object.fromEntries([...Array(100)].map((_, i) => [`${i % 10},${Math.floor(i / 10)}`, 'f'])) },
                        { name: 'Walls', collision: true, tiles: { '6,9': 'w', '6,8': 'w', '6,7': 'w', '6,6': 'w', '7,6': 'w', '8,6': 'w', '9,6': 'w' } }] },
            } };
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true }) }, { room: 'A', x: 1, y: 1 }, 'home wins a tie');
        assert.deepStrictEqual({ ...game('Trips.hopsFrom')(realConfig(), 'Tokyo') }.Machi, 1);
        assert.ok(game('Trips.hopsFrom')(realConfig(), 'Tokyo').Inaka > game('Trips.hopsFrom')(realConfig(), 'Tokyo').Palace, 'a train ride is further than next door');
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true, played: 'ann' }) }, { room: 'B', x: 5, y: 5 },
            'Bob is walled in: the nearest cell that can be walked to');
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: false, played: 'ann' }) }, { room: 'A', x: 1, y: 1 });
        tiny.rooms.B.npcs = [];
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true, played: 'ann' }) }, { room: 'A', x: 1, y: 1 }, 'nobody else anywhere: home');
        // company: a member within NEAR cells of a cell, not counting who you play (resettleNewPlayer's guard)
        const company = game('Trips.hasCompany');
        assert.strictEqual(company(config, '2027-02-20', 'Sapporo', 33, 12, 'bailey'), true, 'Damian is still next to the Sapporo start');
        assert.strictEqual(company(config, '2027-02-20', 'Tokyo', 29, 38, undefined), false);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, undefined), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'ann'), false, 'the only one there is who you play');
        tiny.rooms.A.npcs.push({ name: 'Bob', sprite: 'bob_front', gridX: 2, gridY: 4, dialogue: [] });
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'ann'), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'bob'), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 8, 8, 'ann'), true, 'Bob at 2,4 is 6 cells off');
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 8, 8, 'bob'), false, 'Ann at 3,1 is more than 6 cells off');
        // a new player is one who has not finished the intro
        const store = {};
        ctx.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
        const isNew = game('Intro.isNewPlayer');
        assert.strictEqual(isNew(), true, 'fresh profile');
        store.gamev2_intro_seen = 'pending'; store.gamev2_character = 'custom';
        assert.strictEqual(isNew(), true, 'half way through the intro');
        store.gamev2_intro_seen = '1';
        assert.strictEqual(isNew(), false, 'finished it');
        delete store.gamev2_intro_seen;
        assert.strictEqual(isNew(), false, 'a player from before the intro existed');
    },

    'the intro names the trip members and says where they are today (#130)'() {
        const config = realConfig(), T = game('Trips'), trips = T.of(config);
        assert.strictEqual(T.list(T.memberNames(T.forDate(trips, '2027-02-20'))), 'Bailey, Damian, Dylan, Julia, Khoi, Sam and Xander');
        assert.strictEqual(T.list(T.memberNames(T.forDate(trips, '2025-11-02'))), 'Bailey, Damian, Dylan and Julia');
        const where = (date, here, played) => T.whereText(T.membersByRoom(config, date, { played }), here);
        assert.strictEqual(where('2027-02-20', 'Sapporo'), 'Today everyone is here in Sapporo.');
        assert.strictEqual(where('2027-02-26', 'Asahikawa', 'bailey'), 'Today everyone is here in Asahikawa.');
        assert.strictEqual(where('2027-02-26', 'Tokyo'), 'Today they are in Asahikawa.');
        const g = (room, name, ...people) => ({ room, name, members: people.map(n => ({ name: n })) });
        assert.strictEqual(T.whereText([], 'Tokyo'), 'They are out and about.');
        assert.strictEqual(T.whereText([g('Machi', 'Machi', 'Damian', 'Bailey')], 'Machi'), 'Today Bailey and Damian are here in Machi.');
        assert.strictEqual(T.whereText([g('Machi', 'Machi', 'Bailey'), g('Inaka', 'Inaka', 'Dylan')], 'Machi'),
            'Today Bailey is here in Machi, and Dylan is in Inaka.');
        assert.strictEqual(T.whereText([g('Machi', 'Machi', 'Bailey'), g('Inaka', 'Inaka', 'Dylan'), g('TokyoStation', 'Tokyo Station', 'Julia')], 'Machi'),
            'Today Bailey is here in Machi, and the others are in Inaka and Tokyo Station.');
        assert.strictEqual(T.whereText([g('A', 'A', 'x'), g('B', 'B', 'y'), g('C', 'C', 'z'), g('D', 'D', 'w')], 'Tokyo'), 'Today they are in A, B and C.');
        const copy = game('Intro.tripCopy');
        assert.ok(/on devhouse 3 right now, in Hokkaido/.test(copy(trips[1], true, false)[0]));
        assert.ok(/once they start writing/.test(copy(trips[1], true, false)[1]));
        assert.ok(/This is devhouse 2, their trip to Japan/.test(copy(trips[0], false, true)[0]));
        assert.ok(/come from the blog posts/.test(copy(trips[0], false, true)[1]));
        // the whole page, as the game words it
        const welcome = game('Intro.welcomeCopy');
        const live = welcome(config, '2027-02-20', '2027-02-20');
        assert.strictEqual(live[0], 'devhouse is a group of friends: Bailey, Damian, Dylan, Julia, Khoi, Sam and Xander.');
        assert.ok(/on devhouse 3 right now, in Hokkaido/.test(live[1]) && /once they start writing/.test(live[2]), live);
        assert.ok(!/James|Gloria|Yashuk/.test(live.join(' ')));
        const past = welcome(config, '2025-11-11', '2026-11-25');
        assert.strictEqual(past[0], 'devhouse is a group of friends: Bailey, Damian, Dylan and Julia.');
        assert.ok(/This is devhouse 2, their trip to Japan/.test(past[1]) && /come from the blog posts/.test(past[2]), past);
        assert.ok(/another day or another trip/.test(past[3]));
        // looking ahead at devhouse 3 from today is not "right now"
        assert.ok(/This is devhouse 3, their trip to Hokkaido/.test(welcome(config, '2027-02-20', '2026-11-25')[1]));
        // the cast row draws the same people
        const lineup = game('CharacterSelect.lineup');
        assert.deepStrictEqual(Array.from(lineup(config, trips[0].members)), ['bailey', 'damian', 'dylan', 'julia']);
        assert.strictEqual(lineup(config).length, 7);
    },

    'Time Travel jumps between trips (#118)'() {
        const T = game('Trips'), trips = T.of(realConfig());
        const posts = ['2025-10-04', '2025-11-18'];
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, posts), '2027-02-18', 'no posts yet: the first day');
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, posts.concat('2027-02-19')), '2027-02-19');
        assert.strictEqual(T.jump(trips, '2027-02-20', -1, posts), '2025-10-04');
        assert.strictEqual(T.jump(trips, '2026-05-01', -1, posts), '2025-10-04');
        assert.strictEqual(T.jump(trips, '2026-05-01', 1, posts), '2027-02-18');
        assert.strictEqual(T.jump(trips, '2027-02-20', 1, posts), null);
        assert.strictEqual(T.jump(trips, '2025-10-04', -1, posts), null);
    },
};

let failed = 0;
for (const [name, fn] of Object.entries(tests)) {
    try { fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + e.message); }
}
console.log(failed ? `${failed} failed` : `${Object.keys(tests).length} passed`);
process.exitCode = failed ? 1 : 0;
