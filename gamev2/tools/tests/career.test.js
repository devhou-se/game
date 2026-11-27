// The job in the office towers (issue #226): src/Career.js, its two rules in src/utils/Interactions.js,
// the `career` field and the `focus` effect kind in src/Shop.js, the two achievements, and how
// tools/world-model.js describes and lints the desk and the lifts.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, realConfig, shopWith, worldWith }) => {
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    // src/Career.js is in the runner's list; src/ShrineVisit.js (its bump rule) is not: load it once, here
    const career = () => {
        if (!game('typeof ShrineVisit !== "undefined"')) vm.runInContext(src('ShrineVisit.js'), ctx, { filename: 'ShrineVisit.js' });
        return game('Career');
    };
    // a rand that walks a list of numbers in 0..1, round and round
    const seeded = (list) => { let i = 0; return () => list[i++ % list.length]; };
    const KEYS = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right', 'space', 'enter', 'esc'];
    // Phaser's Key and JustDown, as far as Career.read uses them: a press raises _justDown until it is read
    const keyboard = () => {
        const keys = {};
        for (const name of KEYS) keys[name] = { isDown: false, _justDown: false };
        const justDown = (k) => { if (k._justDown) { k._justDown = false; return true; } return false; };
        const down = (...names) => names.forEach((n) => { if (!keys[n].isDown) { keys[n].isDown = true; keys[n]._justDown = true; } });
        const up = (...names) => names.forEach((n) => { keys[n].isDown = false; });
        return { keys, justDown, down, up };
    };
    // A Career on the ready screen with no Phaser behind it: `career` is the saved one, `focus` the
    // coffee's seconds. `tap(...keys)` is one frame with those keys pressed (and let go after it);
    // `type()` taps the arrow the row wants; `ticket()` types a row to its end.
    const shiftWith = (saved, focus, touch) => {
        const Career = career();
        const text = () => ({ text: '', visible: true, setText(v) { this.text = v; }, setVisible(v) { this.visible = v; }, setFill() {} });
        const row = { clear() {}, fillStyle() {}, fillTriangle() {}, fillRect() {}, lineStyle() {}, strokeRect() {} };
        const board = keyboard(), toasts = [], timers = [];
        const timer = (extra) => { const t = Object.assign({ removed: false, remove() { this.removed = true; } }, extra); timers.push(t); return t; };
        const shop = { money: 1000, career: saved, saves: 0, save() { this.saves++; }, fmt: (n) => '¥' + n,
            buff: (k) => (k === 'focus' ? (focus || 0) : 0), toast: (m) => toasts.push(m) };
        const scene = { shop, updateHUD() {}, touchControls: { enabled: !!touch },
            time: { now: 0, addEvent: (o) => timer(o), delayedCall: (delay, callback) => timer({ delay, callback }) },
            achievementManager: game('Object.create(AchievementManager.prototype)') };
        scene.achievementManager.scene = scene;
        const g = game('Object.create(Career.prototype)');
        Object.assign(g, { scene, keys: board.keys, justDown: board.justDown, objs: [], bump: null, state: 'ready',
            level: Career.LEVELS[0], merged: 0, names: [], seq: [], at: 0, flashUntil: 0, outcome: null,
            row, rowGeometry: { x: 640, y: 400 } });
        for (const name of ['head', 'name', 'terms', 'rules', 'coffee', 'clock', 'status', 'pay', 'bonus', 'next', 'hint']) g[name + 'Text'] = text();
        g.paint();
        const tap = (...names) => { board.down(...names); g.handleInput(); board.up(...names); };
        const type = (wasd) => tap(Career.KEYS[g.seq[g.at]][wasd ? 1 : 0]);
        const ticket = () => { const n = g.seq.length - g.at; for (let i = 0; i < n; i++) type(i % 2); };
        const wrong = () => Career.KEYS[Career.DIRS.find((d) => d !== g.seq[g.at] && d !== g.seq[g.at - 1] && d !== Career.OPPOSITE[g.seq[g.at]])][0];
        // the shift's own clock: the one delayedCall that is still pending
        const timeUp = () => timers.filter((t) => t.callback && t.delay && !t.loop).slice(-1)[0];
        return { g, shop, board, toasts, timers, tap, type, ticket, wrong, timeUp, Career };
    };

    test('the ladder is six titles by lifetime tickets merged, and every step pays more a key press (#226)', () => {
        const Career = career(), L = plain(Career.LEVELS);
        assert.deepStrictEqual(L.map((l) => l.title), ['Intern', 'Junior Engineer', 'Engineer', 'Senior Engineer', 'Staff Engineer', 'Principal Engineer']);
        assert.deepStrictEqual(L.map((l) => [l.at, l.len, l.pay, l.bonus]),
            [[0, 3, 10, 30], [10, 4, 20, 50], [25, 5, 35, 75], [50, 6, 55, 100], [90, 7, 80, 125], [150, 8, 110, 200]]);
        const title = (n) => Career.levelOf(n).title;
        assert.deepStrictEqual([0, 9, 10, 149, 150, 9999].map(title),
            ['Intern', 'Intern', 'Junior Engineer', 'Staff Engineer', 'Principal Engineer', 'Principal Engineer']);
        assert.deepStrictEqual(plain([0, 9, 10, 149].map(Career.next)), [
            { title: 'Junior Engineer', left: 10 }, { title: 'Junior Engineer', left: 1 },
            { title: 'Engineer', left: 15 }, { title: 'Principal Engineer', left: 1 }]);
        assert.strictEqual(Career.next(150), null);
        assert.strictEqual(Career.next(9999), null);
        for (let i = 1; i < L.length; i++) {
            const a = L[i - 1], b = L[i];
            assert.ok(b.at > a.at && b.len > a.len && b.pay > a.pay, b.title);
            assert.ok(b.pay / b.len > a.pay / a.len, `${b.title}: a ticket's key presses pay less than ${a.title}'s`);
            assert.ok((5 * b.pay + b.bonus) / (5 * b.len) > (5 * a.pay + a.bonus) / (5 * a.len), `${b.title}: a clean shift pays less a press than ${a.title}'s`);
        }
        assert.strictEqual(Career.TICKETS, 5);
    });

    test('the balance model is pinned: an Intern earns under ¥800 a minute on a keyboard, a Principal under ¥3,000 (#226)', () => {
        const Career = career(), L = plain(Career.LEVELS), T = Career.TICKETS;
        // docs/shop-and-economy.md: a clean shift is T x len presses at 3 a second, plus 2 s of result and ready screens
        const perMinute = (l) => (T * l.pay + l.bonus) / (T * l.len / 3 + 2) * 60;
        assert.deepStrictEqual(L.map((l) => T * l.pay + l.bonus), [80, 150, 250, 375, 525, 750]);
        assert.ok(perMinute(L[0]) < 800 && perMinute(L[0]) > 600, String(perMinute(L[0])));
        assert.ok(perMinute(L[5]) < 3000 && perMinute(L[5]) > 2500, String(perMinute(L[5])));
        // the way up: 150 tickets in clean shifts
        let paid = 0;
        for (let merged = 0; merged < 150; merged += T) { const l = Career.levelOf(merged); paid += T * l.pay + l.bonus; }
        assert.strictEqual(paid, 11160);
    });

    test('a shift\'s clock is one second an arrow, never under twenty, and a coffee adds its seconds (#226)', () => {
        const Career = career();
        assert.strictEqual(Career.clockMs(3, 0), 20000);
        assert.strictEqual(Career.clockMs(4), 20000);
        assert.strictEqual(Career.clockMs(5, 0), 25000);
        assert.strictEqual(Career.clockMs(8, 0), 40000);
        assert.strictEqual(Career.clockMs(8, 5), 45000);
        assert.deepStrictEqual(plain(Career.LEVELS).map((l) => Career.clockMs(l.len, 0) / 1000), [20, 20, 25, 30, 35, 40]);
        const fmt = (n) => '¥' + n;
        assert.strictEqual(Career.terms(Career.LEVELS[0], 0, fmt), '5 tickets · 20s · ¥10 a ticket · +¥30 for a clean shift');
        assert.strictEqual(Career.terms(Career.LEVELS[5], 5, fmt), '5 tickets · 45s · ¥110 a ticket · +¥200 for a clean shift');
    });

    test('a row is the right length, only the four directions, never three the same running, and the same for the same rand (#226)', () => {
        const Career = career(), DIRS = plain(Career.DIRS);
        assert.deepStrictEqual(DIRS, ['up', 'down', 'left', 'right']);
        const rands = [seeded([0]), seeded([0.999999]), seeded([1]), seeded([0.1, 0.1, 0.1, 0.6, 0.6, 0.6, 0.6]), seeded([0.3, 0.9, 0.3, 0.3, 0.3])];
        let n = 7;
        const lcg = () => { n = (n * 1103515245 + 12345) % 2147483648; return n / 2147483648; };
        for (const rand of rands.concat(Array(40).fill(lcg))) {
            for (const len of [3, 4, 5, 6, 7, 8, 30]) {
                const seq = plain(Career.sequence(len, rand));
                assert.strictEqual(seq.length, len);
                assert.ok(seq.every((d) => DIRS.includes(d)), seq.join(' '));
                assert.ok(!seq.some((d, i) => i >= 2 && d === seq[i - 1] && d === seq[i - 2]), seq.join(' '));
            }
        }
        const list = [0.05, 0.3, 0.55, 0.8, 0.8, 0.8, 0.05];
        assert.deepStrictEqual(plain(Career.sequence(8, seeded(list))), plain(Career.sequence(8, seeded(list))));
        assert.deepStrictEqual(plain(Career.sequence(8, seeded(list))), ['up', 'down', 'left', 'right', 'right', 'left', 'up', 'up']);
    });

    test('a shift\'s five ticket names are all different, and every name is a short lower-case ASCII commit line (#226)', () => {
        const Career = career(), all = plain(Career.TICKET_NAMES);
        assert.ok(all.length >= 16);
        assert.strictEqual(new Set(all).size, all.length);
        for (const name of all) {
            assert.ok(name.length <= 40 && /^[a-z]+: [ -~]+$/.test(name) && name === name.toLowerCase(), name);
        }
        for (const rand of [seeded([0]), seeded([0.999999]), seeded([1]), seeded([0.5, 0.5, 0.2]), Math.random]) {
            const names = plain(Career.names(rand));
            assert.strictEqual(names.length, 5);
            assert.strictEqual(new Set(names).size, 5, names.join(' | '));
            assert.ok(names.every((name) => all.includes(name)));
        }
    });

    test('a press is judged as directions: the five rules, one case each side of them (#226)', () => {
        const press = career().press, seq = ['up', 'right', 'down'];
        // 1. nothing went down
        assert.strictEqual(press(seq, 0, []), null);
        assert.strictEqual(press(seq, 1, [], ['up']), null);
        // 3. the one wanted, alone; the last one merges the ticket
        assert.strictEqual(press(seq, 0, ['up']), 'step');
        assert.strictEqual(press(seq, 1, ['right']), 'step');
        assert.strictEqual(press(seq, 2, ['down']), 'merged');
        assert.strictEqual(press(['left'], 0, ['left']), 'merged');
        // 5. a wrong one
        assert.strictEqual(press(seq, 0, ['left']), 'miss');
        assert.strictEqual(press(seq, 1, ['up']), 'miss');
        // 3. a touch on a diagonal is a perpendicular pair: it scores when it holds the one wanted...
        assert.strictEqual(press(seq, 0, ['up', 'right']), 'step');
        assert.strictEqual(press(seq, 2, ['down', 'left']), 'merged');
        // ...and misses when it does not
        assert.strictEqual(press(seq, 0, ['down', 'left']), 'miss');
        // 2. two opposite directions are a miss even when one is wanted; so are three or four
        assert.strictEqual(press(seq, 0, ['up', 'down']), 'miss');
        assert.strictEqual(press(seq, 1, ['left', 'right']), 'miss');
        assert.strictEqual(press(seq, 0, ['up', 'left', 'right']), 'miss');
        assert.strictEqual(press(seq, 0, ['up', 'down', 'left', 'right']), 'miss');
        assert.strictEqual(press(seq, 0, ['up', 'down', 'left', 'right'], ['up']), 'miss');
        // 4. the arrow just typed (up) is still held and the thumb rolls into the diagonal beside it: not a press
        const row = ['up', 'down', 'up'];
        assert.strictEqual(press(row, 1, ['left'], ['up']), null);
        assert.strictEqual(press(row, 1, ['right'], ['up']), null);
        // ...but with nothing held, at the start of the row, or under a held key that is not the arrow just typed, it is a miss
        assert.strictEqual(press(row, 1, ['left']), 'miss');
        assert.strictEqual(press(row, 1, ['left'], []), 'miss');
        assert.strictEqual(press(row, 0, ['left'], ['up']), 'miss');
        assert.strictEqual(press(row, 1, ['left'], ['right']), 'miss');
        assert.strictEqual(press(row, 1, ['left'], ['down']), 'miss');
        // the forgiveness is for a direction across the held arrow only: its own axis is a press
        assert.strictEqual(press(['up', 'left', 'left'], 1, ['down'], ['up']), 'miss');
        assert.strictEqual(press(['up', 'left', 'left'], 1, ['up'], ['up']), 'miss');
        // the one wanted under a held key is a step all the same
        assert.strictEqual(press(seq, 1, ['right'], ['up']), 'step');
        assert.strictEqual(press(row, 1, ['down'], ['up']), 'step');
    });

    test('settling a shift adds its tickets, pays the bonus only when clean, and promotes exactly on a threshold (#226)', () => {
        const Career = career(), L = Career.LEVELS;
        const before = { merged: 3, shifts: 1, earned: 30 }, frozen = JSON.stringify(before);
        assert.deepStrictEqual(plain(Career.settle(before, L[0], 5, true)),
            { career: { merged: 8, shifts: 2, earned: 110 }, pay: 50, bonus: 30, promoted: null });
        assert.strictEqual(JSON.stringify(before), frozen, 'settle changed the career it was given');
        assert.deepStrictEqual(plain(Career.settle(before, L[0], 3, false)),
            { career: { merged: 6, shifts: 2, earned: 60 }, pay: 30, bonus: 0, promoted: null });
        // nothing merged: nothing paid, and it was still a shift
        assert.deepStrictEqual(plain(Career.settle(before, L[0], 0, false)),
            { career: { merged: 3, shifts: 2, earned: 30 }, pay: 0, bonus: 0, promoted: null });
        // 9 -> 10 is the promotion; 8 -> 9 is not; the pay is the level the shift was played at
        assert.strictEqual(Career.settle({ merged: 8, shifts: 0, earned: 0 }, L[0], 1, false).promoted, null);
        const up = plain(Career.settle({ merged: 9, shifts: 4, earned: 100 }, L[0], 1, false));
        assert.deepStrictEqual(up, { career: { merged: 10, shifts: 5, earned: 110 }, pay: 10, bonus: 0, promoted: 'Junior Engineer' });
        assert.strictEqual(Career.settle({ merged: 145, shifts: 0, earned: 0 }, L[4], 5, true).promoted, 'Principal Engineer');
        assert.strictEqual(Career.settle({ merged: 150, shifts: 0, earned: 0 }, L[5], 5, true).promoted, null);
        assert.deepStrictEqual(plain(Career.settle({ merged: 150, shifts: 0, earned: 0 }, L[5], 5, true)).career, { merged: 155, shifts: 1, earned: 750 });
    });

    test('the reception desk hires once, then reads the title back (#226)', () => {
        const Career = career();
        const first = plain(Career.signOn(null));
        assert.deepStrictEqual(first, { fresh: true, career: { merged: 0, shifts: 0, earned: 0 },
            line: 'You fill in a form. Staff pass: Intern. The lifts go up to engineering now.' });
        const again = plain(Career.signOn(first.career));
        assert.deepStrictEqual(again, { fresh: false, line: 'Intern · 0 tickets merged · 10 more to Junior Engineer' });
        assert.strictEqual(Career.status({ merged: 1, shifts: 1, earned: 10 }), 'Intern · 1 ticket merged · 9 more to Junior Engineer');
        assert.strictEqual(Career.status({ merged: 60, shifts: 12, earned: 2000 }), 'Senior Engineer · 60 tickets merged · 30 more to Staff Engineer');
        assert.strictEqual(Career.status({ merged: 150, shifts: 30, earned: 11160 }), 'Principal Engineer · 150 tickets merged · nowhere left to go but meetings');
        // a toast, like the other visits' lines: nothing in it a phone has to wrap twice
        for (const merged of [0, 9, 150, 99999]) assert.ok(Career.status({ merged }).length <= 80);
    });

    test('the career is saved in the shop\'s blob once hired; anything without a usable count of tickets is not a job (#226)', () => {
        const none = shopWith({ money: 700, items: {} });
        assert.strictEqual(none.shop.career, null);
        none.shop.save();
        assert.ok(!('career' in none.saved()), 'a player who was never hired saves no career');
        assert.strictEqual(none.saved().v, 4);

        const hired = shopWith({ v: 4, money: 700, items: {}, career: { merged: 12, shifts: 3, earned: 240 } });
        assert.deepStrictEqual(plain(hired.shop.career), { merged: 12, shifts: 3, earned: 240 });
        assert.strictEqual(hired.shop.money, 700);
        hired.shop.save();
        assert.deepStrictEqual(hired.saved().career, { merged: 12, shifts: 3, earned: 240 });
        assert.deepStrictEqual(plain(shopWith(hired.saved()).shop.career), { merged: 12, shifts: 3, earned: 240 });

        for (const junk of ['x', -1, {}, { merged: 'x' }, { merged: -1 }, { merged: null, shifts: 3 }, [], true]) {
            const { shop } = shopWith({ money: 700, items: {}, career: junk });
            assert.strictEqual(shop.career, null, JSON.stringify(junk));
            assert.strictEqual(shop.money, 700);
        }
        // the tickets are the title: a damaged counter beside them reads as nothing and does not cost the ladder
        for (const dented of [{ merged: 40 }, { merged: 40, shifts: null, earned: -3 }, { merged: 40.9, shifts: 'x', earned: {} }]) {
            const { shop } = shopWith({ money: 700, items: {}, career: dented });
            assert.deepStrictEqual(plain(shop.career), { merged: 40, shifts: 0, earned: 0 }, JSON.stringify(dented));
            assert.strictEqual(shop.money, 700);
        }
    });

    test('a canned coffee is five seconds more on the work clock while it lasts (#226)', () => {
        const { shop, toasts } = shopWith({ money: 1000, items: { 'canned-coffee': 1 } });
        shop.scene.player = { sprite: { setTint() {}, clearTint() {}, setScale() {}, scale: 1 } };
        shop.scene.tweens = { add: () => ({ stop() {} }) };
        shop.scene.time = { delayedCall() {} };
        const coffee = shop.itemById('canned-coffee');
        assert.strictEqual(shop.effectSummary(coffee), 'speed +30%, work clock +5s for 1:30');
        assert.strictEqual(coffee.desc, 'the long haul: speed +30% and 5s more on the work clock, for 90s.');
        const longest = Math.max(...Array.from(game('Shop.DEFAULT_ITEMS')).map((i) => (i.desc || '').length));
        assert.ok(longest <= 66, `an item's description is ${longest} characters`);
        assert.strictEqual(shop.buff('focus'), 0);
        shop.use('canned-coffee');
        assert.ok(/work clock \+5s/.test(toasts.pop()));
        assert.strictEqual(shop.buff('focus'), 5);
        assert.strictEqual(shop.buff('speed'), 1.3);
        shop.clockOffset += 91000;
        assert.strictEqual(shop.buff('focus'), 0);
        assert.strictEqual(game('Shop.EFFECT_KINDS.focus.additive'), true);
    });

    test('the keys are read as directions, each press once, and W with ↑ is one up (#226)', () => {
        const Career = career(), { keys, justDown, down, up } = keyboard();
        const read = () => plain(Career.read(keys, justDown));
        assert.deepStrictEqual(read(), { dirs: [], held: [], confirm: false, esc: false });
        down('left');
        assert.deepStrictEqual(read(), { dirs: ['left'], held: [], confirm: false, esc: false });
        assert.deepStrictEqual(read(), { dirs: [], held: ['left'], confirm: false, esc: false }, 'still down: held, not pressed again');
        up('left');
        assert.deepStrictEqual(read(), { dirs: [], held: [], confirm: false, esc: false });
        // an arrow and its WASD key are one direction, and neither is left raised for the next read
        down('w', 'up');
        assert.deepStrictEqual(read(), { dirs: ['up'], held: [], confirm: false, esc: false });
        assert.deepStrictEqual(read(), { dirs: [], held: ['up'], confirm: false, esc: false });
        // the d-pad's diagonal: the second key of the pair goes down under the first
        down('d');
        assert.deepStrictEqual(read(), { dirs: ['right'], held: ['up'], confirm: false, esc: false });
        up('w', 'up', 'd');
        // a tap that came and went between two frames is still a press, once
        down('s'); up('s');
        assert.deepStrictEqual(read(), { dirs: ['down'], held: [], confirm: false, esc: false });
        assert.deepStrictEqual(read(), { dirs: [], held: [], confirm: false, esc: false });
        for (const name of ['space', 'enter']) {
            down(name);
            assert.strictEqual(read().confirm, true, name);
            assert.strictEqual(read().confirm, false, name);
            up(name);
        }
        down('space', 'enter', 'esc');
        assert.deepStrictEqual(read(), { dirs: [], held: [], confirm: true, esc: true });
        assert.ok(Object.values(keys).every((k) => !k._justDown), 'a key was left raised');
        // every one of the eleven keys is read on every call
        const seen = new Set();
        Career.read(keys, (k) => { seen.add(k); return false; });
        assert.strictEqual(seen.size, KEYS.length);
        // the class has the one reader: nothing else in the file asks Phaser what was just pressed
        const body = src('Career.js');
        assert.strictEqual((body.match(/Phaser\.Input\.Keyboard\.JustDown/g) || []).length, 1);
        assert.ok(body.includes('read() { return Career.read(this.keys, this.justDown); }'));
        assert.ok(body.includes('handleInput() { this.act(this.read()); }'));
    });

    test('a clean shift pays five tickets and the bonus into the wallet once, and counts one shift (#226)', () => {
        const { g, shop, tap, type, ticket, timers, timeUp, toasts } = shiftWith({ merged: 0, shifts: 0, earned: 0 });
        assert.strictEqual(g.isActive(), true);
        assert.strictEqual(g.headText.text, 'ENGINEERING');
        assert.strictEqual(g.nameText.text, 'Intern');
        assert.strictEqual(g.termsText.text, '5 tickets · 20s · ¥10 a ticket · +¥30 for a clean shift');
        assert.strictEqual(g.coffeeText.visible, false);
        tap('space');
        assert.strictEqual(g.state, 'playing');
        assert.strictEqual(g.clockMs, 20000);
        assert.strictEqual(timeUp().delay, 20000);
        assert.strictEqual(g.clockText.text, '20.0s');
        assert.strictEqual(g.headText.text, 'TICKET 1/5');
        assert.strictEqual(g.seq.length, 3);
        assert.strictEqual(new Set(g.names).size, 5);
        for (let n = 0; n < 5; n++) {
            assert.strictEqual(g.nameText.text, g.names[n]);
            assert.strictEqual(g.headText.text, `TICKET ${n + 1}/5`);
            type(); assert.strictEqual(g.at, 1);
            type(true); assert.strictEqual(g.at, 2);
            assert.strictEqual(shop.money, 1000, 'paid before the shift ended');
            type();
            if (n < 4) assert.deepStrictEqual([g.merged, g.at, g.statusText.text], [n + 1, 0, 'MERGED']);
        }
        assert.strictEqual(g.state, 'result');
        assert.strictEqual(shop.money, 1080);
        assert.deepStrictEqual(plain(shop.career), { merged: 5, shifts: 1, earned: 80 });
        assert.strictEqual(shop.saves, 1, 'saved once, as the shift ended');
        assert.deepStrictEqual([g.headText.text, g.nameText.text, g.payText.text, g.bonusText.text, g.nextText.text],
            ['SHIFT COMPLETE', '5/5 merged', '+¥50', 'clean shift +¥30', '5 more to Junior Engineer']);
        assert.ok(timers.every((t) => t.removed), 'a timer outlived the shift');
        assert.deepStrictEqual(toasts, ['★ achievement: First Paycheck']);
        // the clock's own finish landing after the fifth merge pays nothing more
        timeUp().callback();
        g.finish(false);
        g.finish(true);
        assert.strictEqual(shop.money, 1080);
        assert.strictEqual(shop.career.shifts, 1);
        // another shift from the result screen: the ready screen again, then a second pay packet and no second toast
        tap('enter');
        assert.strictEqual(g.state, 'ready');
        assert.strictEqual(g.headText.text, 'ENGINEERING');
        tap('space');
        for (let n = 0; n < 5; n++) ticket();
        assert.strictEqual(shop.money, 1160);
        assert.deepStrictEqual(plain(shop.career), { merged: 10, shifts: 2, earned: 160 });
        assert.strictEqual(g.nextText.text, 'PROMOTED: Junior Engineer');
        assert.strictEqual(toasts.length, 1);
        // ESC leaves: the overlay is gone and no press is left for the world
        tap('esc');
        assert.strictEqual(g.state, 'idle');
        assert.strictEqual(g.isActive(), false);
    });

    test('a wrong arrow fails the build and the row starts again; the ticket and the pay are not lost (#226)', () => {
        const { g, shop, tap, type, ticket, wrong } = shiftWith({ merged: 30, shifts: 6, earned: 900 });
        tap('enter');
        assert.strictEqual(g.level.title, 'Engineer');
        assert.strictEqual(g.seq.length, 5);
        assert.strictEqual(g.clockMs, 25000);
        ticket();
        assert.strictEqual(g.merged, 1);
        type(); type(); type();
        assert.strictEqual(g.at, 3);
        const row = plain(g.seq);
        tap(wrong());
        assert.deepStrictEqual([g.at, g.merged, g.statusText.text], [0, 1, 'BUILD FAILED']);
        assert.deepStrictEqual(plain(g.seq), row, 'the row changed under the player');
        // the line comes down by itself, 600 ms on
        g.scene.time.now += 599; g.updateClock();
        assert.strictEqual(g.statusText.text, 'BUILD FAILED');
        g.scene.time.now += 1; g.updateClock();
        assert.strictEqual(g.statusText.text, '');
        // every key at once is a miss, not five steps
        type();
        tap('up', 'down', 'left', 'right');
        assert.strictEqual(g.at, 0);
        // a frame with nothing pressed is nothing
        type();
        g.handleInput();
        assert.strictEqual(g.at, 1);
        ticket();
        assert.strictEqual(g.merged, 2);
        assert.strictEqual(shop.money, 1000);
    });

    test('ESC mid-shift clocks off with what is merged and no bonus; the clock running out does the same (#226)', () => {
        const quit = shiftWith({ merged: 0, shifts: 0, earned: 0 });
        quit.tap('space');
        quit.ticket(); quit.ticket(); quit.type();
        quit.tap('esc');
        assert.strictEqual(quit.g.state, 'result');
        assert.strictEqual(quit.shop.money, 1020);
        assert.deepStrictEqual(plain(quit.shop.career), { merged: 2, shifts: 1, earned: 20 });
        assert.deepStrictEqual([quit.g.headText.text, quit.g.nameText.text, quit.g.payText.text, quit.g.bonusText.visible],
            ['CLOCKED OFF', '2/5 merged', '+¥20', false]);
        quit.tap('esc');
        assert.strictEqual(quit.g.state, 'idle');

        const slow = shiftWith({ merged: 0, shifts: 0, earned: 0 });
        slow.tap('space');
        slow.g.scene.time.now += 20000;
        slow.timeUp().callback();
        assert.strictEqual(slow.g.state, 'result');
        assert.deepStrictEqual([slow.g.headText.text, slow.g.nameText.text, slow.g.payText.text], ['TIME\'S UP', '0/5 merged', '+¥0']);
        assert.strictEqual(slow.shop.money, 1000);
        assert.deepStrictEqual(plain(slow.shop.career), { merged: 0, shifts: 1, earned: 0 });
        assert.deepStrictEqual(slow.toasts, [], 'nothing merged is no paycheck');
        // ESC and the fifth merge on one frame: the ESC is the frame's answer and nothing is paid twice
        const both = shiftWith({ merged: 0, shifts: 0, earned: 0 });
        both.tap('space');
        for (let n = 0; n < 4; n++) both.ticket();
        both.type(); both.type();
        both.tap(both.Career.KEYS[both.g.seq[2]][0], 'esc');
        assert.strictEqual(both.g.state, 'result');
        assert.strictEqual(both.shop.money, 1040);
        assert.strictEqual(both.shop.career.shifts, 1);
    });

    test('a player nine tickets in is promoted on the result, and plays the next shift at the new title (#226)', () => {
        const { g, shop, tap, ticket } = shiftWith({ merged: 9, shifts: 3, earned: 90 });
        tap('space');
        assert.strictEqual(g.level.title, 'Intern');
        ticket();
        // promoted in the middle of a shift: the rows and the pay stay the Intern's until it ends
        assert.strictEqual(g.seq.length, 3);
        for (let n = 0; n < 4; n++) ticket();
        assert.strictEqual(shop.money, 1080);
        assert.deepStrictEqual(plain(shop.career), { merged: 14, shifts: 4, earned: 170 });
        assert.strictEqual(g.nextText.text, 'PROMOTED: Junior Engineer');
        tap('space');
        assert.deepStrictEqual([g.state, g.nameText.text, g.termsText.text],
            ['ready', 'Junior Engineer', '5 tickets · 20s · ¥20 a ticket · +¥50 for a clean shift']);
        tap('space');
        assert.strictEqual(g.seq.length, 4);
        // the top of the ladder has nothing under its result
        const top = shiftWith({ merged: 150, shifts: 30, earned: 11160 });
        top.tap('space');
        assert.strictEqual(top.g.seq.length, 8);
        assert.strictEqual(top.g.clockMs, 40000);
        for (let n = 0; n < 5; n++) top.ticket();
        assert.strictEqual(top.shop.money, 1750);
        assert.deepStrictEqual([top.g.nextText.text, top.g.nextText.visible], ['', false]);
        assert.deepStrictEqual(top.toasts, [], 'the top was reached before this shift');
        // ...and getting there says so, once
        const nearly = shiftWith({ merged: 149, shifts: 30, earned: 0 });
        nearly.tap('space');
        nearly.ticket();
        nearly.tap('esc');
        assert.deepStrictEqual(nearly.toasts, ['★ achievement: Principal Engineer']);
        assert.strictEqual(nearly.g.nextText.text, 'PROMOTED: Principal Engineer');
    });

    test('no press outlives its screen: an arrow on the ready screen is not typed, SPACE while typing does not skip the result (#226)', () => {
        const { g, board, tap, type, ticket } = shiftWith({ merged: 0, shifts: 0, earned: 0 });
        // every arrow tapped on the ready screen, then SPACE: the row is untouched
        tap('up'); tap('left'); tap('s'); tap('d');
        assert.strictEqual(g.state, 'ready');
        tap('space');
        assert.deepStrictEqual([g.state, g.at, g.statusText.text], ['playing', 0, '']);
        // an arrow pressed with the SPACE that starts the shift is used up on that frame
        g.finish(false); tap('space');
        assert.strictEqual(g.state, 'ready');
        tap('space', 'up', 'left');
        g.handleInput();
        assert.deepStrictEqual([g.state, g.at, g.statusText.text], ['playing', 0, '']);
        // SPACE and ENTER tapped while typing are nothing, then and later
        type();
        tap('space'); tap('enter');
        assert.strictEqual(g.at, 1);
        for (let n = 0; n < 5; n++) ticket();
        assert.strictEqual(g.state, 'result');
        g.handleInput();
        assert.strictEqual(g.state, 'result', 'a SPACE from the shift skipped the result');
        // an arrow on the result screen is not the first press of the next shift
        tap('down'); tap('w');
        tap('space'); tap('space');
        assert.deepStrictEqual([g.state, g.at], ['playing', 0]);
        // leaving swallows what is pending: nothing raised goes back to the world
        board.down('esc', 'up', 'space');
        g.handleInput();
        board.down('enter', 'a');
        g.leave();
        assert.ok(Object.values(board.keys).every((k) => !k._justDown), 'a press was left for the world');
    });

    test('a coffee\'s seconds are on the ready screen and on the clock, locked in as the shift starts (#226)', () => {
        const { g, tap, timeUp } = shiftWith({ merged: 0, shifts: 0, earned: 0 }, 5);
        assert.strictEqual(g.termsText.text, '5 tickets · 25s · ¥10 a ticket · +¥30 for a clean shift');
        assert.deepStrictEqual([g.coffeeText.text, g.coffeeText.visible], ['coffee: +5s on the clock', true]);
        tap('space');
        assert.strictEqual(g.clockMs, 25000);
        assert.strictEqual(timeUp().delay, 25000);
        assert.strictEqual(g.clockText.text, '25.0s');
        g.scene.time.now += 1234; g.updateClock();
        assert.strictEqual(g.clockText.text, '23.8s');
    });

    test('the shift\'s three hints are worded for the touch pad: A, B and the d-pad, no key names left (#226)', () => {
        const lines = (touch) => {
            const { g, tap } = shiftWith({ merged: 0, shifts: 0, earned: 0 }, 0, touch);
            const out = [g.hintText.text];
            tap('space'); out.push(g.hintText.text);
            tap('esc'); out.push(g.hintText.text);
            return out;
        };
        const keyboardLines = lines(false);
        assert.deepStrictEqual(keyboardLines, ['SPACE to start    ESC to leave', 'arrows to type    ESC to clock off', 'SPACE for another shift    ESC to leave']);
        assert.deepStrictEqual(lines(true), ['A to start    B to leave', 'd-pad to type    B to clock off', 'A for another shift    B to leave']);
        const Hints = game('Hints');
        for (const line of keyboardLines) {
            const touch = Hints.word(line);
            assert.ok(!/ARROWS|arrows|SPACE|ENTER|ESC/.test(touch), touch);
            assert.ok(Hints.isHint(line) && Hints.isHint(touch), line);
        }
        // the rules line is not a hint: "the arrows" in it are the ones on the screen
        assert.ok(src('Career.js').includes("ready && 'press the arrows in order. a wrong one fails the build and the ticket starts again'"));
    });

    test('who is hiring is every room with a lobby, under its town\'s name (#226)', () => {
        const Career = career(), config = realConfig();
        const where = plain(Career.where(config));
        const lobbies = Object.keys(config.rooms).filter((k) => config.rooms[k].lobby).sort();
        assert.ok(lobbies.length >= 5);
        assert.deepStrictEqual(where.map((w) => w.room), lobbies);
        for (const w of where) assert.strictEqual(w.name, game('hudName')(config.rooms[config.rooms[w.room].lobby.host].name), w.room);
        const towns = Array.from(new Set(where.map((w) => w.name)));
        for (const t of ['Osaka', 'Sapporo']) assert.ok(towns.includes(t), t);
        assert.deepStrictEqual(plain(Career.where({ rooms: { A: {}, L: { lobby: { host: 'Gone' } } } })), [{ room: 'L', name: 'Gone' }]);
        assert.deepStrictEqual(plain(Career.where({})), []);
    });

    test('the two career achievements: the first ticket, and the top of the ladder (#226)', () => {
        const rows = (saved) => {
            const { shop } = shopWith({ money: 100, items: {}, career: saved });
            return plain(shop.scene.achievementManager.careerProgress()).map((a) => [a.name, a.value, a.total, a.complete]);
        };
        assert.deepStrictEqual(rows(undefined), [['First Paycheck', 0, 1, false], ['Principal Engineer', 0, 5, false]]);
        assert.deepStrictEqual(rows({ merged: 0, shifts: 2, earned: 0 }), [['First Paycheck', 0, 1, false], ['Principal Engineer', 0, 5, false]]);
        assert.deepStrictEqual(rows({ merged: 1, shifts: 1, earned: 10 }), [['First Paycheck', 1, 1, true], ['Principal Engineer', 0, 5, false]]);
        assert.deepStrictEqual(rows({ merged: 60, shifts: 1, earned: 10 }), [['First Paycheck', 1, 1, true], ['Principal Engineer', 3, 5, false]]);
        assert.deepStrictEqual(rows({ merged: 150, shifts: 30, earned: 11160 }), [['First Paycheck', 1, 1, true], ['Principal Engineer', 5, 5, true]]);
        const { shop } = shopWith({ money: 100, items: {} });
        const all = plain(shop.scene.achievementManager.itemProgress());
        assert.deepStrictEqual(all.slice(-2).map((a) => a.desc), ['Merge a ticket at work', 'Reach the top of the ladder']);
        for (const a of all) assert.deepStrictEqual(Object.keys(a).sort(), ['complete', 'desc', 'name', 'total', 'value'], a.name);
    });

    test('in every lobby the desk and both lifts are the job and the directory says a line; the lint is clean (#226)', () => {
        const { world, config } = worldWith(false);
        const lobbies = Object.entries(config.rooms).filter(([, r]) => r.lobby);
        assert.ok(lobbies.length >= 5);
        for (const [key, room] of lobbies) {
            const mat = room.transporters[0];
            world.enter(key, mat.gridX, mat.gridY - 1);
            const found = { 'lobby-desk_0_0': [], 'lobby-lift_0_0': [], 'lobby-directory_0_0': [] };
            for (const layer of room.layers) {
                for (const [cell, sprite] of Object.entries(layer.tiles)) if (sprite in found) found[sprite].push(cell.split(',').map(Number));
            }
            assert.deepStrictEqual(Object.values(found).map((cells) => cells.length), [1, 2, 1], key);
            const kinds = {};
            // every cell of each one's footprint answers, not only its anchor
            for (let y = 0; y < 15; y++) {
                for (let x = 0; x < 20; x++) {
                    const hit = world.interactionAt(x, y);
                    if (hit) (kinds[`${hit.group}/${hit.kind}`] = kinds[`${hit.group}/${hit.kind}`] || []).push([x, y]);
                }
            }
            assert.deepStrictEqual(Object.keys(kinds).sort(), ['career/desk', 'career/lift', 'flavour/directory'], key);
            for (const [x, y] of found['lobby-desk_0_0']) assert.strictEqual(world.interactionAt(x, y).kind, 'desk', key);
            for (const [x, y] of found['lobby-lift_0_0']) assert.strictEqual(world.interactionAt(x, y).kind, 'lift', key);
            assert.ok(kinds['career/desk'].length >= 2 && kinds['career/lift'].length >= 4, `${key}: ${JSON.stringify(kinds)}`);
            assert.strictEqual(world.describe(world.interactionAt(...kinds['career/desk'][0])),
                'the reception desk: signs you on for a job in the tower (free); afterwards reads your title back');
            assert.strictEqual(world.describe(world.interactionAt(...kinds['career/lift'][0])),
                'the lift up to work: a shift of tickets for pay (needs the staff pass from the reception desk)');
            assert.strictEqual(world.describe(world.interactionAt(...kinds['flavour/directory'][0])),
                'says: "engineering is hiring, the directory says. ask at the desk"');
            const lint = world.lint(key);
            assert.strictEqual(JSON.stringify([lint.errors, lint.warns]), '[{},{}]', key);
        }
        // tools/play.js draws the job's cells with a glyph of their own, and says so in its legend
        const play = fs.readFileSync(path.join(GV2, 'tools', 'play.js'), 'utf8');
        assert.ok(/const GLYPH = \{[^}]*career: 'J'/.test(play));
        assert.ok(play.includes('D drinking game  J job  letters are NPCs'));
    });

    test('a bump at the desk or a lift: hired once, a pass asked for, one answer a bump, and the overlay only with the pass (#226)', () => {
        const Career = career(), board = keyboard();
        const toasts = [], cells = { '5,6': { kind: 'desk', group: 'career' }, '5,3': { kind: 'lift', group: 'career' } };
        const shop = { money: 1000, career: null, saves: 0, save() { this.saves++; }, fmt: (n) => '¥' + n, buff: () => 0,
            toast: (m) => toasts.push(m), isVisible: () => false };
        const scene = { shop, time: { now: 1000 }, player: { gridX: 5, gridY: 4 }, dialogueManager: { isVisible: () => false },
            roomManager: { isTransitioning: false, interactionAt: (x, y, group) => (group === 'career' && cells[`${x},${y}`]) || null } };
        const g = game('Object.create(Career.prototype)');
        let rendered = 0;
        Object.assign(g, { scene, keys: board.keys, justDown: board.justDown, objs: [], bump: null, state: 'idle', render() { rendered++; } });
        assert.strictEqual(g.check(9, 9), false, 'floor is not the job');
        // the lift before the desk: no pass, no overlay
        assert.strictEqual(g.check(5, 3), true);
        assert.deepStrictEqual(toasts.splice(0), ['the lift wants a pass. the reception desk hands them out']);
        assert.deepStrictEqual([g.state, rendered, shop.career, shop.saves], ['idle', 0, null, 0]);
        // the key still held against it is the same bump: no second toast
        scene.time.now += 100; g.hold({ x: 0, y: -1 });
        assert.strictEqual(g.check(5, 3), true);
        assert.deepStrictEqual(toasts, []);
        // the desk hires, and saves
        scene.time.now += 1000; g.hold({ x: 0, y: 0 });
        scene.player = { gridX: 5, gridY: 5 };
        assert.strictEqual(g.check(5, 6), true);
        assert.deepStrictEqual(toasts.splice(0), ['You fill in a form. Staff pass: Intern. The lifts go up to engineering now.']);
        assert.deepStrictEqual([plain(shop.career), shop.saves], [{ merged: 0, shifts: 0, earned: 0 }, 1]);
        // a second bump reads the title back and saves nothing
        scene.time.now += 1000; g.hold({ x: 0, y: 0 });
        assert.strictEqual(g.check(5, 6), true);
        assert.deepStrictEqual(toasts.splice(0), ['Intern · 0 tickets merged · 10 more to Junior Engineer']);
        assert.strictEqual(shop.saves, 1);
        // the lift with the pass: the ready screen, and the key held to bump it is not a press in it
        scene.time.now += 1000; g.hold({ x: 0, y: 0 });
        scene.player = { gridX: 5, gridY: 4 };
        board.down('up', 'w');
        assert.strictEqual(g.check(5, 3), true);
        assert.deepStrictEqual([g.state, rendered, toasts.length], ['ready', 1, 0]);
        assert.ok(Object.values(board.keys).every((k) => !k._justDown));
        // open: a bump is not answered twice; nor in a room fade, a conversation or a shop
        assert.strictEqual(g.check(5, 6), false);
        g.state = 'idle';
        scene.time.now += 1000; g.hold({ x: 0, y: 0 });
        for (const block of [() => { scene.roomManager.isTransitioning = true; }, () => { scene.dialogueManager.isVisible = () => true; }, () => { shop.isVisible = () => true; }]) {
            block();
            assert.strictEqual(g.check(5, 6), false);
            scene.roomManager.isTransitioning = false; scene.dialogueManager.isVisible = () => false; shop.isVisible = () => false;
        }
        assert.deepStrictEqual(toasts, []);
        // leaving with the direction still held against the lift does not open it again
        g.state = 'ready'; g.clockEvent = null; g.finishEvent = null;
        g.bump = { cell: '5,3', at: scene.time.now - 5000, dx: 0, dy: -1 };
        g.leave();
        assert.strictEqual(g.bump.at, scene.time.now);
        g.hold({ x: 0, y: -1 });
        assert.strictEqual(g.check(5, 3), true);
        assert.deepStrictEqual([g.state, rendered], ['idle', 1]);
    });
};
