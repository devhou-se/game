// Issue #248: the browser regression's two time limits (the whole run, any one check) can be stretched on a
// slow machine with REGRESS_TIME_SCALE; unset, they are what they were. No browser is needed here: the limits
// are read by tools/browser/limits.js, and regress.js is run against a playwright-core that refuses to connect.
//
// Issue #252: the menu checks lost a press on a slow machine. tools/browser/menu.js moves the menu's cursor;
// it is run here against a page whose game is the real InputHandler, reading its keys once a frame.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const { limits } = require(path.join(GV2, 'tools', 'browser', 'limits.js'));

    // regress.js with `env` added, and no browser to connect to: { status, lines }
    const regress = (env) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'browser-regress-'));
        try {
            const stub = path.join(tmp, 'node_modules', 'playwright-core');
            fs.mkdirSync(stub, { recursive: true });
            fs.writeFileSync(path.join(stub, 'index.js'), "module.exports = { chromium: { connect: async () => { throw new Error('stub: no browser'); } } };\n");
            const base = { ...process.env, NODE_PATH: path.join(tmp, 'node_modules'), SHOTS: path.join(tmp, 'shots') };
            delete base.REGRESS_TIME_SCALE;
            const run = spawnSync(process.execPath, [path.join(GV2, 'tools', 'browser', 'regress.js')], { cwd: GV2, encoding: 'utf8', timeout: 60000, env: { ...base, ...env } });
            assert.ok(!run.error, `regress.js did not finish: ${run.error}`);
            return { status: run.status, lines: run.stdout.trim().split('\n') };
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };

    test('browser regression: REGRESS_TIME_SCALE multiplies the run and the per-check limit, and unset they are 80s and 25s (#248)', () => {
        assert.deepStrictEqual(limits({}), { scale: 1, deadlineMs: 80000, checkMs: 25000 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '' }), limits({}));
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '1' }), limits({}));
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '2' }), { scale: 2, deadlineMs: 160000, checkMs: 50000 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '1.5' }), { scale: 1.5, deadlineMs: 120000, checkMs: 37500 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '100' }), { scale: 100, deadlineMs: 8000000, checkMs: 2500000 });
    });

    test('browser regression: a REGRESS_TIME_SCALE that would shorten the limits, or is not a plain number, is refused (#248)', () => {
        for (const bad of ['0', '0.5', '0.99', '-2', '100.5', '101', 'abc', '2x', '2s', ' 2', '1e1', '0x10', 'Infinity', 'NaN', 'true']) {
            assert.throws(() => limits({ REGRESS_TIME_SCALE: bad }), /REGRESS_TIME_SCALE must be a number from 1 to 100/, `accepted ${JSON.stringify(bad)}`);
        }
    });

    test('browser regression: regress.js says when its limits are stretched, and fails at once on a bad REGRESS_TIME_SCALE (#248)', () => {
        const said = (lines) => lines.filter((l) => /REGRESS_TIME_SCALE/.test(l));
        // as committed: no word about a scale, and with no browser every profile fails
        const plain = regress({});
        assert.strictEqual(plain.status, 1, plain.lines.join('\n'));
        assert.deepStrictEqual(said(plain.lines), []);
        assert.ok(plain.lines.some((l) => /^FAIL desktop-profile stub: no browser/.test(l)), plain.lines.join('\n'));
        // stretched: the first line gives both limits; the run itself is the same
        const slow = regress({ REGRESS_TIME_SCALE: '3' });
        assert.strictEqual(slow.status, 1, slow.lines.join('\n'));
        assert.strictEqual(slow.lines[0], 'REGRESS_TIME_SCALE=3: the run may take 240s and a check 75s; the assertions are unchanged');
        assert.deepStrictEqual(slow.lines.slice(1).filter((l) => /^(ok|FAIL) /.test(l)).map((l) => l.replace(/\(\d+ms\)$/, '')),
            plain.lines.filter((l) => /^(ok|FAIL) /.test(l)).map((l) => l.replace(/\(\d+ms\)$/, '')));
        // refused: one harness failure, in the run's own words, and no check is started
        const bad = regress({ REGRESS_TIME_SCALE: '0.5' });
        assert.strictEqual(bad.status, 1, bad.lines.join('\n'));
        assert.deepStrictEqual(bad.lines, ['FAIL harness REGRESS_TIME_SCALE must be a number from 1 to 100 (1 is the usual limits), not "0.5"', '0/1 checks passed']);
    });

    // tools/browser/menu.js against a page with no browser behind it. The game is src/systems/InputHandler.js
    // itself, reading keys that page.keyboard sets, over a menu of 11 rows that wraps; it runs a frame every
    // `frameMs` of a clock that only the page's own waits and calls move. Run with node -e in a process of its
    // own (the helpers are async, the tests are not), so it takes everything it needs as arguments.
    const simulate = async (GV2, frameMs, fault) => {
        const fs = require('fs'), path = require('path'), vm = require('vm');
        const menu = require(path.join(GV2, 'tools', 'browser', 'menu.js'));
        const ctx = vm.createContext({ Phaser: { Input: { Keyboard: { KeyCodes: {} } } } });
        vm.runInContext(fs.readFileSync(path.join(GV2, 'src', 'systems', 'InputHandler.js'), 'utf8'), ctx, { filename: 'InputHandler.js' });
        // a Phaser key as the handler uses it: isDown, and a 'down' event on keydown
        const key = () => ({ isDown: false, on(ev, fn) { this[ev] = fn; } });
        const N = 11;
        let moves = 0;
        // `fault`: the cursor's own moves go wrong - 'lost' drops the second one, 'far' makes it two rows, 'dead' drops them all
        const move = (m, by) => {
            moves++;
            if (fault === 'dead' || (fault === 'lost' && moves === 2)) return;
            m.selectedIndex = (m.selectedIndex + (fault === 'far' && moves === 2 ? 2 * by : by) + 2 * N) % N;
        };
        const m = { visible: true, selectedIndex: 0, options: new Array(N).fill(null), isVisible() { return this.visible; }, toggle() { this.visible = !this.visible; },
            selectNext() { move(this, 1); }, selectPrevious() { move(this, -1); }, activate() {} };
        ctx.scene = { input: { keyboard: { createCursorKeys: () => ({ up: key(), down: key(), left: key(), right: key() }), addKey: key } },
            dialogueManager: { isVisible: () => false }, menuManager: m };
        const ih = vm.runInContext('new InputHandler(scene)', ctx);
        ih.setupKeys();
        const keys = { ArrowDown: ih.cursors.down, ArrowUp: ih.cursors.up, s: ih.sKey, w: ih.wKey };
        const __t = { frames: 0, s: ctx.scene };
        let now = 0;
        const pass = (ms) => {
            for (const to = now + ms; now < to;) {
                now = Math.min(to, (Math.floor(now / frameMs) + 1) * frameMs);
                if (now % frameMs === 0) { ih.handleInput(); __t.frames++; }
            }
        };
        const read = (expr) => new Function('__t', `return (${expr});`)(__t);
        const page = {
            keyboard: {
                down: async (k) => { pass(2); if (!keys[k].isDown) { keys[k].isDown = true; keys[k].down(); } },
                up: async (k) => { pass(2); keys[k].isDown = false; },
            },
            evaluate: async (expr) => { pass(2); return read(expr); },
            waitForTimeout: async (ms) => pass(ms),
            // true now, or on a frame to come
            waitForFunction: async (expr, arg, { timeout }) => {
                for (const t0 = now; !read(expr);) {
                    if (now - t0 >= timeout) throw new Error('timeout');
                    pass(Math.min(frameMs - now % frameMs, timeout - (now - t0)));
                }
            },
        };
        const out = {};
        // the way the checks moved the cursor before #252: the key held until the cursor is on the row, then a fixed 120ms
        const old = async (k, want) => {
            await page.keyboard.down(k);
            try { await page.waitForFunction(`__t.s.menuManager.selectedIndex === ${want}`, null, { timeout: 1500 }); } catch (e) { /* read below */ }
            await page.keyboard.up(k);
            await page.waitForTimeout(120);
            return m.selectedIndex;
        };
        const reset = () => { m.selectedIndex = 0; moves = 0; };
        out.old = [await old('s', 1), await old('s', 2), await old('ArrowDown', 3)];
        await menu.frames(page);
        reset();
        // menu-entries: down every row with the two keys in turn, round the end, and back up over it
        out.down = [];
        for (let i = 1; i <= N; i++) out.down.push(await menu.step(page, i % 2 ? 'ArrowDown' : 's'));
        out.up = [await menu.step(page, 'w'), await menu.step(page, 'ArrowUp'), await menu.step(page, 'ArrowUp')];
        out.presses = moves;
        // menuTo: the rows the menu checks go to, from the top
        reset();
        out.to7 = await menu.moveTo(page, 7);
        out.to3 = await menu.moveTo(page, 3);
        out.stay = await menu.moveTo(page, 3);
        out.ms = now;
        return out;
    };
    const simulated = (frameMs, fault) => {
        const run = spawnSync(process.execPath, ['-e', `(${simulate})(${JSON.stringify(GV2)}, ${frameMs}, ${JSON.stringify(fault || null)})
            .then((out) => console.log(JSON.stringify(out)), (e) => console.log(JSON.stringify({ error: e.message })));`], { encoding: 'utf8', timeout: 60000 });
        assert.ok(!run.error && run.status === 0, `the simulated page did not finish: ${run.error || run.stderr}`);
        return JSON.parse(run.stdout);
    };

    test('browser regression: the short way round the menu, down on a tie (#252)', () => {
        const { route } = require(path.join(GV2, 'tools', 'browser', 'menu.js'));
        assert.deepStrictEqual(route(0, 0, 11), { dir: 1, steps: 0 });
        assert.deepStrictEqual(route(0, 5, 11), { dir: 1, steps: 5 });
        assert.deepStrictEqual(route(0, 6, 11), { dir: -1, steps: 5 });
        assert.deepStrictEqual(route(0, 7, 11), { dir: -1, steps: 4 });
        assert.deepStrictEqual(route(9, 1, 11), { dir: 1, steps: 3 });
        assert.deepStrictEqual(route(1, 9, 11), { dir: -1, steps: 3 });
        assert.deepStrictEqual(route(0, 5, 10), { dir: 1, steps: 5 });
        assert.deepStrictEqual(route(7, 2, 10), { dir: 1, steps: 5 });
    });

    test('browser regression: a menu key is a new press at any frame rate, one row a press (#252)', () => {
        const rows = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0];
        for (const frameMs of [16, 100, 400, 1200, 2400]) {
            const out = simulated(frameMs);
            assert.ok(!out.error, `${frameMs}ms frames: ${out.error}`);
            assert.deepStrictEqual(out.down, rows, `${frameMs}ms frames: down each row and round the end`);
            assert.deepStrictEqual(out.up, [10, 9, 8], `${frameMs}ms frames: up over the end`);
            assert.strictEqual(out.presses, 14, `${frameMs}ms frames: the game moved the cursor once a press`);
            assert.deepStrictEqual(out.to7, { at: 7, rows: [0, 10, 9, 8, 7] }, `${frameMs}ms frames`);
            assert.deepStrictEqual(out.to3, { at: 3, rows: [7, 6, 5, 4, 3] }, `${frameMs}ms frames`);
            assert.deepStrictEqual(out.stay, { at: 3, rows: [3] }, `${frameMs}ms frames: already there, no press`);
        }
        // what it replaces, on the same page: fine at 60 frames a second, and on a slow frame the second press
        // of the key lands before the game has seen the first one let go, and is not a press
        assert.deepStrictEqual(simulated(16).old, [1, 2, 3]);
        assert.deepStrictEqual(simulated(400).old, [1, 1, 1]);
        // a game that runs no frames is said, not waited on
        assert.strictEqual(simulated(6000).error, 'the game ran fewer than 2 frames in 5s');
    });

    test('browser regression: the walk to a menu row reads the cursor after every press (#252)', () => {
        // a press the menu did not take is sent again; one that moved two rows is walked back
        assert.deepStrictEqual(simulated(100, 'lost').to7, { at: 7, rows: [0, 10, 10, 9, 8, 7] });
        assert.deepStrictEqual(simulated(100, 'far').to7, { at: 7, rows: [0, 10, 8, 7] });
        // a cursor that never moves: a press per row of the menu and no more, and where it stopped is returned
        const dead = simulated(100, 'dead');
        assert.deepStrictEqual(dead.to7, { at: 0, rows: new Array(12).fill(0) });
        // ...and the checks' steps do not take a press on trust either
        assert.deepStrictEqual(dead.down, new Array(11).fill(0));
        assert.deepStrictEqual(simulated(100, 'lost').down.slice(0, 3), [1, 1, 2]);
    });

    test('browser regression: the menu checks move the cursor through menu.js alone (#252)', () => {
        const src = fs.readFileSync(path.join(GV2, 'tools', 'browser', 'regress.js'), 'utf8');
        assert.ok(src.includes("const menu = require('./menu');"));
        assert.ok(src.includes('await menu.step(page, key)') && src.includes('await menu.moveTo(page, ix)'));
        // no key held until the cursor is on a given row: that is what lost the press
        const held = src.split('\n').filter((l) => /\b(press|hold)\(page,/.test(l) && /menuManager\.selectedIndex|\$\{lit\}/.test(l));
        assert.deepStrictEqual(held, []);
    });
};
