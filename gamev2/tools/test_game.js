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
['utils/NpcStates.js', 'TrainTravel.js', 'StationPicker.js', 'DialogueManager.js', 'systems/TouchControls.js'].forEach(load);
const game = (expr) => vm.runInContext(expr, ctx);

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
