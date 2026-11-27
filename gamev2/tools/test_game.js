#!/usr/bin/env node
// The unit tests' runner: `node tools/test_game.js` (from gamev2/). It loads the game's own source into a
// vm context, then runs every test registered by the files in tools/tests/*.test.js (found by name, in
// sorted order; `--reverse` runs files and tests backwards, to show that no test leans on another).
//
// A test file is `module.exports = ({ test, assert, game, ... }) => { test('name', () => { ... }); };`
// and takes what it needs from the helpers below (listed in `helpers` at the bottom). A new file needs no
// edit here. Test names are unique across all files: a second test of the same name is an error.
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
    navigator: { maxTouchPoints: 0 },
    window: { dispatchEvent: (e) => fired.push(e.type + ':' + e.code) },
});
const load = (f) => vm.runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8'), ctx, { filename: f });
['utils/ConfigCodec.js', 'systems/TiledAdapter.js', 'utils/Trips.js', 'utils/NpcStates.js', 'utils/Hints.js', 'TrainTravel.js', 'StationPicker.js', 'DatePicker.js', 'DialogueManager.js', 'systems/Viewport.js', 'systems/UIScale.js', 'systems/TouchControls.js',
    'utils/JapaneseFont.js', 'ItemIcons.js', 'Energy.js', 'Shop.js', 'Fishing.js', 'DrinkingGame.js', 'AchievementManager.js', 'CharacterCreator.js', 'CharacterSelect.js', 'Intro.js', 'systems/NPCManager.js',
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
// The travelling cast on a date: "Room/Name" (the izakaya's opponents are fixtures).
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
        STORE_KEY: 'gamev2_shop', clockOffset: 0, startingMoney: 5000, woreOff: [], notices: [], energyDrain: 1, effects: {},
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

// What a test file can ask for. `require` and `__dirname` are this file's, so `require('./png')` and
// paths under tools/ read the same from a test file as they did when the tests lived here.
const tests = new Map();
let file = null;
const test = (name, fn) => {
    if (typeof name !== 'string' || !name || typeof fn !== 'function') throw new Error(`${file}: test(name, fn) wants a name and a function`);
    if (tests.has(name)) throw new Error(`duplicate test name in ${file}${tests.get(name).file === file ? '' : ' and ' + tests.get(name).file}: ${name}`);
    tests.set(name, { fn, file });
};
const helpers = { test, assert, fs, path, vm, GV2, ctx, fired, load, game, realConfig, bootOn, castOn, shopWith, showdownWith, worldWith,
    require, __dirname };

const TESTS = path.join(__dirname, 'tests');
const reverse = process.argv.includes('--reverse');
const files = fs.readdirSync(TESTS).filter((f) => f.endsWith('.test.js')).sort();
if (!files.length) throw new Error('no test files in ' + TESTS);
for (file of files) {
    const register = require(path.join(TESTS, file));
    if (typeof register !== 'function') throw new Error(`${file}: module.exports must be a function taking the helpers`);
    const before = tests.size;
    register(helpers);
    if (tests.size === before) throw new Error(`${file}: registers no test`);
}
file = null;

let failed = 0;
const entries = Array.from(tests);
for (const [name, { fn }] of reverse ? entries.reverse() : entries) {
    try { fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + e.message); }
}
console.log(failed ? `${failed} failed` : `${tests.size} passed`);
process.exitCode = failed ? 1 : 0;
