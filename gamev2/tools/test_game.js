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
['utils/NpcStates.js', 'TrainTravel.js', 'StationPicker.js', 'DialogueManager.js', 'systems/TouchControls.js',
    'utils/Hints.js', 'ItemIcons.js', 'Shop.js', 'Fishing.js', 'DrinkingGame.js', 'AchievementManager.js'].forEach(load);
const game = (expr) => vm.runInContext(expr, ctx);

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

    'outside the trip the game opens on a trip day, and cycles through them'() {
        const defaultGameDate = game('defaultGameDate');
        const dates = ['2025-10-02', '2025-10-03', '2025-11-18'];
        assert.strictEqual(defaultGameDate('2025-10-10', dates), '2025-10-10');
        assert.strictEqual(defaultGameDate('2025-11-19', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2025-11-21', dates), '2025-11-18');
        assert.strictEqual(defaultGameDate('2025-11-22', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2030-01-01', []), '2030-01-01');
    },
};

let failed = 0;
for (const [name, fn] of Object.entries(tests)) {
    try { fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + e.message); }
}
console.log(failed ? `${failed} failed` : `${Object.keys(tests).length} passed`);
process.exitCode = failed ? 1 : 0;
