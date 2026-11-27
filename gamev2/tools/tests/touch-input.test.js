module.exports = ({ test, assert, fs, path, GV2, ctx, fired, load, game, require, __dirname }) => {
    test('a touch on a control is cancelled before Phaser can read it as a tap', () => {
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
    });

    test('touch controls never cost the canvas any size, and desktop windows are centred', () => {
        const layout = game('Viewport.layout');
        for (const [w, h] of [[844, 390], [667, 375], [1024, 768], [1180, 820], [1366, 1024], [1280, 960]]) {
            const bare = layout(w, h, false), touch = layout(w, h, true);
            assert.deepStrictEqual([touch.width, touch.height], [bare.width, bare.height], `${w}x${h} canvas`);
        }
        // room in the side bars: controls beside the canvas, nothing under them
        const land = layout(844, 390, true);
        assert.deepStrictEqual([land.mode, land.controls, land.insets.left, land.insets.right], ['side', 0.8, 0, 0]);
        // none: over the bottom corners, at the floor (lower on a small phone), and how far in they reach
        const small = layout(667, 375, true), tablet = layout(1024, 768, true);
        assert.deepStrictEqual([small.mode, small.controls, tablet.mode, tablet.controls], ['over', 0.6, 'over', 0.75]);
        assert.ok(small.insets.left > 0 && small.insets.right > 0 && small.insets.bottom > 0);
        assert.strictEqual(tablet.insets.left, Math.round((16 + 174 * 0.75 + 6) / 0.8));
        // portrait: the canvas fills the height above the controls and the window crops its sides
        const port = layout(390, 844, true);
        assert.strictEqual(port.mode, 'portrait');
        assert.ok(port.height > 600 && port.top + port.height <= 844 - 16 - 210 - 6 + 0.5, 'fills the space above the controls');
        assert.strictEqual(port.crop.left + port.crop.right + Math.round(390 / port.scale), 1280, 'crop + visible = canvas');
        assert.ok(1280 - port.crop.left - port.crop.right >= 560, 'a useful width stays in view');
        // without touch controls a portrait window is just a small canvas
        assert.strictEqual(layout(390, 844, false).width, 390);
        // desktop: 1:1 where it fits, centred both ways (issue #114)
        assert.deepStrictEqual([layout(1280, 960, false).left, layout(1280, 960, false).top], [0, 0]);
        const tall = layout(1440, 1200, false);
        assert.deepStrictEqual([tall.scale, tall.left, tall.top, tall.mode], [1, 80, 120, 'none']);
    });

    test('the touch buttons: sprint is the big one on the bottom row, B the small one above A (#225)', () => {
        const K = game('TouchControls.CLUSTER'), C = game('Viewport.CONTROLS');
        // measured from the cluster's bottom-right corner, where the thumb is
        const box = (k) => ({ x0: k.right, y0: k.bottom, x1: k.right + k.w, y1: k.bottom + k.h });
        const boxes = Object.entries(K).map(([name, k]) => [name, box(k)]);
        assert.deepStrictEqual(boxes.map(([name]) => name).sort(), ['a', 'b', 'sprint']);
        // the canvas is laid out around Viewport.CONTROLS: the buttons fill that box and none sticks out of it
        for (const [name, b] of boxes) assert.ok(b.x0 >= 0 && b.y0 >= 0 && b.x1 <= C.clusterW && b.y1 <= C.clusterH, `${name} is outside the cluster`);
        assert.strictEqual(Math.max(...boxes.map(([, b]) => b.x1)), C.clusterW, 'the cluster is as wide as the layout allows for');
        assert.strictEqual(Math.max(...boxes.map(([, b]) => b.y1)), C.clusterH, 'and as tall');
        // a thumb on one is not on the next: 10px between any two
        for (const [n1, p] of boxes) for (const [n2, q] of boxes) {
            if (n1 >= n2) continue;
            const apart = Math.max(p.x0 - q.x1, q.x0 - p.x1, p.y0 - q.y1, q.y0 - p.y1);
            assert.ok(apart >= 10, `${n1} and ${n2} are ${apart}px apart`);
        }
        // sprint is held while you walk: on the bottom edge, no further from the corner than A, and bigger than B
        // both ways; B is tapped now and then: the smallest, and the furthest out
        const reach = (k) => Math.hypot(k.right + k.w / 2, k.bottom + k.h / 2);
        assert.strictEqual(K.sprint.bottom, 0);
        assert.ok(reach(K.sprint) <= reach(K.a) && reach(K.a) < reach(K.b), 'sprint and A are nearest the thumb, B beyond them');
        assert.ok(K.sprint.w > K.a.w && K.sprint.w > K.b.w && K.sprint.h > K.b.h, 'sprint is the widest, and taller than B');
        assert.ok(K.b.w < K.a.w && K.b.h < K.a.h && K.b.w === K.b.h && K.a.w === K.a.h, 'A and B are circles, B the smaller');
        assert.ok(K.b.w * 0.6 >= 30, 'B is still a target at the smallest the controls get (0.6x)');
        assert.strictEqual(game('Viewport.MIN_CONTROL_SCALE_SMALL'), 0.6);
        // the buttons are placed from the table, not from numbers in the stylesheet
        const src = fs.readFileSync(path.join(GV2, 'src', 'systems', 'TouchControls.js'), 'utf8');
        for (const name of Object.keys(K)) assert.ok(src.includes(`at(TouchControls.CLUSTER.${name})`), `${name} is not placed from the table`);
    });

    test('overlays are fitted beside or above the touch controls, and shrink only when something is in the way', () => {
        const fit = game('UIScale.fit');
        const placed = (box, f) => [f.offsetX + box.x0 * f.zoom, f.offsetY + box.y0 * f.zoom, f.offsetX + box.x1 * f.zoom, f.offsetY + box.y1 * f.zoom];
        const panel = { x0: 400, y0: 230, x1: 880, y1: 730 };         // 480x500, centred
        const wide = { x0: 20, y0: 150, x1: 1260, y1: 830 };           // nearly the whole canvas
        // nothing in the way: magnified up to what is wanted, never shrunk
        assert.strictEqual(fit(panel, 2.46, 1280, 960).zoom, 1.87);
        assert.strictEqual(fit(wide, 2.46, 1280, 960).zoom, 1.01);
        assert.strictEqual(fit({ x0: 0, y0: 0, x1: 1280, y1: 950 }, 2.46, 1280, 960).zoom, 1);
        // controls over the bottom corners: the wide box goes above them or between them
        const insets = { left: 191, right: 173, bottom: 224 };
        const full = { x0: 20, y0: 60, x1: 1260, y1: 900 };
        const f = fit(full, 1.25, 1280, 960, insets), at = placed(full, f);
        assert.ok(f.zoom < 1, 'shrunk to fit');
        const between = at[0] >= insets.left - 0.01 && at[2] <= 1280 - insets.right + 0.01;
        const above = at[3] <= 960 - insets.bottom + 0.01;
        assert.ok(between || above, `clear of the controls: ${at}`);
        // the shorter one fits above them without shrinking, slid up
        const up = fit(wide, 1.25, 1280, 960, insets);
        assert.ok(up.zoom >= 1 && placed(wide, up)[3] <= 960 - insets.bottom + 0.01);
        // a panel that fits between them is not touched at 1:1
        assert.deepStrictEqual([fit(panel, 1, 1280, 960, insets).zoom, fit(panel, 1, 1280, 960, insets).offsetX], [1, 0]);
        // room kept for a toast under the panel
        const r = fit(panel, 2.46, 1280, 960, null, false, 846);
        assert.ok(placed(panel, r)[3] <= 846 + 0.01 && r.zoom < 1.87);
        // a cropped portrait view: a panel wider than the view shrinks into it
        const narrow = fit({ x0: 320, y0: 155, x1: 960, y1: 805 }, 1.57, 612, 960, null, true, null, { width: 1280, height: 960 });
        const n = placed({ x0: 320, y0: 155, x1: 960, y1: 805 }, narrow);
        assert.ok(narrow.zoom < 1 && n[0] >= 12 - 0.01 && n[2] <= 600 + 0.01, `inside the view: ${n}`);
    });

    test('hints are worded for the input in use, and remembered under both wordings', () => {
        const Hints = game('Hints');
        const scene = { touchControls: { enabled: false } };
        assert.strictEqual(Hints.text(scene, 'ENTER/click: travel · ESC: close'), 'ENTER/click: travel · ESC: close');
        scene.touchControls.enabled = true;
        assert.strictEqual(Hints.text(scene, 'ENTER/click: travel · ESC: close'), 'A/tap: travel · B: close');
        assert.strictEqual(Hints.text(scene, 'SPACE/ENTER: continue | ESC: close', { tap: true }), 'TAP or A: continue | B: close');
        assert.ok(Hints.isHint('A/tap: travel · B: close') && Hints.isHint('ENTER/click: travel · ESC: close'));
        assert.ok(!Hints.isHint('November 2025'));
        // a line on screen is reworded in place when the input changes
        const line = { type: 'Text', text: 'TAP or A: continue | B: close', setText(t) { this.text = t; } };
        const other = { type: 'Text', text: 'Dylan', setText() { throw new Error('not a hint'); } };
        scene.children = { list: [{ type: 'Container', list: [line] }, other] };
        scene.touchControls.enabled = false;
        Hints.refresh(scene);
        assert.strictEqual(line.text, 'SPACE/ENTER: continue | ESC: close');
    });

    test('a touchscreen laptop is a keyboard until it is touched', () => {
        const touchFirst = () => game('TouchControls.touchFirst()');
        const win = game('window'), nav = game('navigator');
        nav.maxTouchPoints = 0;
        assert.strictEqual(touchFirst(), false, 'no touch screen');
        nav.maxTouchPoints = 10;
        win.matchMedia = (q) => ({ matches: q === '(pointer: coarse)' });
        assert.strictEqual(touchFirst(), true, 'phone / tablet: the main pointer is a finger');
        win.matchMedia = () => ({ matches: false });
        assert.strictEqual(touchFirst(), false, 'touchscreen laptop: the main pointer is a mouse');
        const keys = game('TouchControls.GAME_KEYS');
        assert.ok(['KeyW', 'ArrowLeft', 'Space', 'Enter', 'Escape', 'ShiftLeft'].every(k => keys.test(k)));
        assert.ok(!['KeyQ', 'Tab', 'F5', 'MetaLeft'].some(k => keys.test(k)));
    });

    test('touch hints name both d-pad axes: up/down is the d-pad, left/right its arrows', () => {
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
    });

    test('a toast slides off the overlay panel it would cover, when there is room', () => {
        const clearOf = game('UIScale.clearOf');
        const toast = { x0: 310, y0: 856, x1: 970, y1: 904 };          // 48px tall, authored near the bottom
        const showdown = { x0: 13, y0: 76, x1: 1267, y1: 884 };        // 844x390: 76px strips over and under
        assert.strictEqual(clearOf(toast, showdown, 960), 42, 'centred in the strip under the panel');
        assert.strictEqual(clearOf({ ...toast, y0: 100, y1: 148 }, showdown, 960), -86, 'the strip over it when that is nearer');
        assert.strictEqual(clearOf(toast, { ...showdown, y1: 940 }, 960), -842, 'over it when the strip under is too thin');
        assert.strictEqual(clearOf(toast, { ...showdown, y0: 12, y1: 948 }, 960), 0, 'stays put when the panel fills the canvas');
        assert.strictEqual(clearOf(toast, { ...showdown, y1: 850 }, 960), 0, 'stays put when it covers nothing');
        assert.strictEqual(clearOf(toast, { ...showdown, x1: 300 }, 960), 0, 'beside the panel is not on it');
    });

    test('a key held as a picker opens does nothing in it until it is released (#220)', () => {
        if (game('typeof InputHandler') === 'undefined') load('systems/InputHandler.js');
        const swallow = game('InputHandler.swallow');
        // Phaser's Key and JustDown, as the pickers use them: a press raises _justDown once (key repeat
        // does not), and it stays raised until someone reads it
        const key = () => ({ isDown: false, _justDown: false });
        const press = (k) => { if (!k.isDown) { k.isDown = true; k._justDown = true; } };
        const release = (k) => { k.isDown = false; };
        const JD = (k) => { if (k._justDown) { k._justDown = false; return true; } return false; };
        const keys = { up: key(), down: key(), w: key(), s: key(), enter: key(), space: key(), esc: key() };
        const moved = () => (JD(keys.up) || JD(keys.w) ? -1 : 0) + (JD(keys.down) || JD(keys.s) ? 1 : 0);
        // W walks the player onto the board cell: nobody reads its JustDown on the way, so it is still raised
        press(keys.w);
        assert.strictEqual(keys.w._justDown, true);
        swallow(keys, JD);                                   // the board opens
        assert.strictEqual(moved(), 0, 'the held W does not move the selection as the board opens');
        press(keys.w);                                       // key repeat while it stays down
        assert.strictEqual(moved(), 0, 'nor on any later frame while it is held');
        release(keys.w); press(keys.w);
        assert.strictEqual(moved(), -1, 'released and pressed again, it moves one row');
        assert.strictEqual(moved(), 0, 'once');
        // every key of the overlay, whatever it is called: the S that stepped down the menu, and the ENTER that chose
        press(keys.s); press(keys.enter); press(keys.down);
        swallow(keys, JD);
        assert.ok(Object.values(keys).every((k) => !k._justDown));
        assert.strictEqual(keys.enter.isDown, true, 'the key itself is untouched: only its pending press is read');
        // the lists a direction key walks or steps you into all open through it; without it the board opened
        // one row up (W held), the Character list one row down (S from the menu), Time Travel a week off
        const read = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
        for (const [file, open] of [['StationPicker.js', 'show(fromKey, opts) {'], ['DatePicker.js', 'show() {'], ['CharacterSelect.js', 'show() {'], ['Shop.js', 'showInventory() {']]) {
            const body = read(file).split('\n    ' + open)[1].split('\n    }\n')[0];
            assert.ok(body.includes('InputHandler.swallow(this.keys);'), `${file} ${open}`);
            assert.ok(body.indexOf('InputHandler.swallow(this.keys);') < body.search(/this\.(visible|invVisible) = true;/), `${file}: before it is visible`);
        }
        // the shop's own list (a bump on a shelf) already read every direction key; the overlays that do not
        // list, and are opened by a key they do not use, read all of theirs
        assert.ok(read('Shop.js').includes('[k.enter, k.space, k.esc, k.left, k.right, k.a, k.d, k.up, k.down, k.w, k.s].forEach(JD);'));
        assert.ok(read('DrinkingGame.js').includes('Object.values(this.keys).forEach(JD);'));
    });

    test('a key tapped between two frames is still read on the next one (#195)', () => {
        if (game('typeof InputHandler') === 'undefined') load('systems/InputHandler.js');
        // a Phaser key as the handler uses it: isDown, and a 'down' event on keydown
        const key = () => ({ isDown: false, on(ev, fn) { this[ev] = fn; } });
        const press = (k) => { k.isDown = true; k.down(); };
        const tap = (k) => { press(k); k.isDown = false; };          // keydown + keyup inside one frame
        const calls = [];
        const scene = {
            input: { keyboard: { createCursorKeys: () => ({ up: key(), down: key(), left: key(), right: key() }), addKey: key } },
            dialogueManager: { visible: false, isVisible() { return this.visible; }, advance: () => calls.push('advance'), close: () => calls.push('close') },
            menuManager: { visible: false, isVisible() { return this.visible; }, toggle() { this.visible = !this.visible; calls.push('toggle'); },
                selectPrevious: () => calls.push('prev'), selectNext: () => calls.push('next'), activate: () => calls.push('activate') },
            player: { isMoving: false, startMovement: (x, y) => calls.push(`move ${x},${y}`) },
            roomManager: { isTransitioning: false },
        };
        ctx.Phaser = { Input: { Keyboard: { KeyCodes: {} } } };
        ctx.__scene = scene;
        const ih = game('new InputHandler(__scene)');
        ih.setupKeys();
        const frame = () => { calls.length = 0; ih.handleInput(); return calls.join(' | '); };

        assert.strictEqual(frame(), '');
        tap(ih.dKey);
        assert.strictEqual(frame(), 'move 1,0', 'a sub-frame D tap takes one step');
        assert.strictEqual(frame(), '', 'and only one');
        tap(ih.escKey);
        assert.strictEqual(frame(), 'toggle', 'a sub-frame ESC tap opens the menu');
        assert.strictEqual(frame(), '', 'once');
        tap(ih.cursors.down); assert.strictEqual(frame(), 'next');
        tap(ih.wKey); assert.strictEqual(frame(), 'prev');
        tap(ih.enterKey); assert.strictEqual(frame(), 'activate');
        tap(ih.escKey); assert.strictEqual(frame(), 'toggle');
        assert.strictEqual(scene.menuManager.visible, false);
        scene.dialogueManager.visible = true;
        tap(ih.spaceKey); assert.strictEqual(frame(), 'advance');
        tap(ih.spaceKey); assert.strictEqual(frame(), 'advance', 'two taps on consecutive frames are two presses');
        tap(ih.escKey); assert.strictEqual(frame(), 'close');
        scene.dialogueManager.visible = false;
        // a held key is still one press, and a tap nobody may act on is dropped, not saved up
        press(ih.escKey);
        assert.strictEqual(frame(), 'toggle'); assert.strictEqual(frame(), '');
        ih.escKey.isDown = false; assert.strictEqual(frame(), '');
        tap(ih.escKey); assert.strictEqual(frame(), 'toggle');
        scene.trainTravel = { riding: true };
        tap(ih.escKey); tap(ih.aKey);
        assert.strictEqual(frame(), '');
        scene.trainTravel.riding = false;
        assert.strictEqual(frame(), '', 'a tap during a train ride does not fire after it');
    });

    test('a skip key tapped between two frames still skips the flight and the ride, and starts the game from the title (#253)', () => {
        for (const [name, file] of [['InputHandler', 'systems/InputHandler.js'], ['AirTravel', 'AirTravel.js'], ['DayNight', 'DayNight.js'],
            ['ViewRide', 'ViewRide.js'], ['TitleScreen', 'TitleScreen.js']]) {
            if (game(`typeof ${name}`) === 'undefined') load(file);
        }
        // Phaser 4.2's keyboard, as far as these screens use it: one Key per key code, whoever asks for it; a
        // keydown raises _justDown and emits 'down', once per press (key repeat does neither); a keyup takes
        // _justDown back (Key.onUp), so JustDown never sees a press that is already up again
        const made = {};
        const key = (code) => made[code] || (made[code] = { isDown: false, _justDown: false, fns: [], on(ev, fn) { if (ev === 'down') this.fns.push(fn); } });
        const press = (k) => { if (!k.isDown) { k.isDown = true; k._justDown = true; k.fns.forEach((fn) => fn()); } };
        const release = (k) => { k.isDown = false; k._justDown = false; };
        const tap = (k) => { press(k); release(k); };               // keydown + keyup inside one frame
        const JD = (k) => { if (k._justDown) { k._justDown = false; return true; } return false; };
        const calls = [];
        const scene = {
            input: { keyboard: {
                createCursorKeys: () => ({ up: key(38), down: key(40), left: key(37), right: key(39) }), addKey: key,
                addKeys: (map) => Object.fromEntries(Object.entries(map).map(([name, code]) => [name, key(code)])),
            } },
            time: { now: 0 },
            dialogueManager: { isVisible: () => false },
            menuManager: { visible: false, isVisible() { return this.visible; }, toggle() { this.visible = !this.visible; calls.push('toggle'); },
                selectPrevious: () => calls.push('prev'), selectNext: () => calls.push('next'), activate: () => calls.push('activate') },
            player: { isMoving: false, startMovement: (x, y) => calls.push(`move ${x},${y}`) },
            roomManager: { isTransitioning: false },
        };
        ctx.Phaser = { Input: { Keyboard: { KeyCodes: { SHIFT: 16, ESC: 27, ENTER: 13, SPACE: 32, W: 87, A: 65, S: 83, D: 68 }, JustDown: JD } } };
        ctx.__scene = scene;
        try {
            const ih = scene.inputHandler = game('new InputHandler(__scene)');
            ih.setupKeys();
            const air = scene.airTravel = game('new AirTravel(__scene)');
            const view = scene.viewRide = game('new ViewRide(__scene)');
            const title = scene.titleScreen = game('new TitleScreen(__scene)');
            assert.strictEqual(air.keys.space, ih.spaceKey, 'the screens read the keys the handler latches');
            const frame = () => { calls.length = 0; ih.handleInput(); return calls.join(' | '); };
            const A = game('AirTravel'), V = game('ViewRide');
            let ended = 0;
            const end = () => { ended++; };
            const count = (what) => { ended = 0; assert.strictEqual(frame(), '', `${what}: nothing else acts`); return ended; };

            // the flight, as go() leaves it once the cabin is up
            air.flying = true; air._started = 0; air._land = end;
            tap(air.keys.space);
            assert.strictEqual(count('flight'), 0, 'not before SKIP_AFTER');
            scene.time.now = A.SKIP_AFTER;
            assert.strictEqual(count('flight'), 0, 'and the early tap is dropped, not saved up');
            for (const name of ['space', 'enter', 'esc']) {
                tap(air.keys[name]);
                assert.strictEqual(count('flight'), 1, `a sub-frame ${name} tap skips the flight`);
                assert.strictEqual(count('flight'), 0, 'once');
            }
            assert.strictEqual(air.skipped, true);
            // a key that stays down is one press, however the two ways of seeing it add up...
            press(air.keys.space); press(air.keys.enter);
            assert.strictEqual(count('flight'), 1, 'two keys in one frame are one skip');
            assert.strictEqual(count('flight'), 0);
            assert.ok(Object.values(air.keys).every((k) => !k._justDown), 'every JustDown was read: none is left for the next overlay');
            release(air.keys.space); release(air.keys.enter);
            assert.strictEqual(count('flight'), 0, 'letting go is nothing');
            // ...and the press that boarded is none: what go() forgets, held or already up again
            press(air.keys.enter); tap(air.keys.space);
            ih.forget(air.keys);
            assert.strictEqual(count('flight'), 0, 'the press from before the flight does not skip it');
            assert.strictEqual(count('flight'), 0, 'nor while it stays down');
            release(air.keys.enter); tap(air.keys.enter);
            assert.strictEqual(count('flight'), 1, 'released and pressed again, it does');
            // the ESC that skipped does not open the menu on landing
            tap(air.keys.esc);
            assert.strictEqual(count('flight'), 1);
            air.flying = false;
            assert.strictEqual(frame(), '');

            // the ride with a view, as run() leaves it once the picture is up
            const lift = V.RIDES.lift;
            view.riding = true; view._ride = lift; view._elapsed = V.SKIP_AFTER - 1; view._end = end;
            tap(view.keys.space);
            assert.strictEqual(count('ride'), 0, 'not before SKIP_AFTER');
            view._elapsed = V.SKIP_AFTER;
            for (const name of ['space', 'enter', 'esc']) {
                tap(view.keys[name]);
                assert.strictEqual(count('ride'), 1, `a sub-frame ${name} tap skips the ride`);
                assert.strictEqual(count('ride'), 0, 'once');
            }
            assert.strictEqual(view.skipped, true);
            press(view.keys.space);
            assert.strictEqual(count('ride'), 1); assert.strictEqual(count('ride'), 0, 'a held key is one skip');
            release(view.keys.space);
            view._elapsed = lift.ms;
            tap(view.keys.space);
            assert.strictEqual(count('ride'), 0, 'not once it is ending');
            view.riding = false;
            assert.strictEqual(frame(), '');

            // the title: any of the three starts the game, and the press does nothing else after it
            for (const name of ['space', 'enter', 'esc']) {
                title.visible = true; title.onStart = end;
                assert.strictEqual(count('title'), 0);
                tap(title.keys[name]);
                assert.strictEqual(count('title'), 1, `a sub-frame ${name} tap starts the game`);
                assert.strictEqual(title.isVisible(), false);
                assert.strictEqual(count('title'), 0, 'and is over: no menu, no step');
            }
            title.visible = true; title.onStart = end;
            press(title.keys.esc);
            assert.strictEqual(count('title'), 1, 'a held key starts it too');
            assert.strictEqual(count('title'), 0, 'and does not open the menu while it stays down');
            release(title.keys.esc);
            assert.strictEqual(count('title'), 0);
        } finally { delete ctx.Phaser; delete ctx.__scene; }

        // the three read their keys through the handler, and what they swallow as they begin is forgotten there too
        const read = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
        for (const [file, begin, input] of [['AirTravel.js', 'go(fromKey, toKey) {', 'this.skip()'], ['ViewRide.js', 'run(ride, dir, behind) {', 'this.skip()'],
            ['TitleScreen.js', 'show(onStart) {', 'this.start()']]) {
            const body = (open) => read(file).split('\n    ' + open)[1].split('\n    }\n')[0];
            assert.ok(body('handleInput() {').includes(`if (this.scene.inputHandler.pressed(this.keys)) ${input};`), `${file} handleInput`);
            assert.ok(/(this\.)?scene\.inputHandler\.forget\(this\.keys\);/.test(body(begin)), `${file} ${begin}`);
            assert.ok(!read(file).includes('JustDown'), `${file} reads no key past the latch`);
        }
    });
};
