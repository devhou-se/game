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
['utils/NpcStates.js', 'TrainTravel.js', 'DialogueManager.js', 'systems/TouchControls.js'].forEach(load);
const game = (expr) => vm.runInContext(expr, ctx);

const tests = {
    'a station parks its own train, and keeps the one you rode in on'() {
        const liveryFor = game('TrainTravel.liveryFor');
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        for (const st of Object.values(stations)) assert.strictEqual(liveryFor(st, null), st.train);
        assert.strictEqual(liveryFor(stations.YukimuraStation, 'train-orange'), 'train-orange');
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
