module.exports = ({ test, assert, fs, path, ctx, fired, load, game, require, __dirname }) => {
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

    test('a key tapped between two frames is still read on the next one (#195)', () => {
        load('systems/InputHandler.js');
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
};
