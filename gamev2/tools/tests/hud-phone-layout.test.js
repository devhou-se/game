module.exports = ({ test, assert, fs, path, GV2, game, realConfig }) => {
    test('the HUD date is bare on a trip day in every room, and a countdown never runs under the menu button (#118, #163)', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate');
        // the HUD's metrics: PixelOperatorMono at 16px is 16px a character; 1280 wide, 10px padding, "menu" right-aligned
        const CH = 16, PAD = 10, MENU_LEFT = 1280 - PAD - 4 * CH;
        const right = (room, label, money) => PAD + CH * `${config.game.title} | ${room} | ${label} | ${money}`.length;
        const days = [...game('contentChangeDates')(config)].sort().concat('2027-02-20', '2027-02-26', '2026-11-25', '2027-01-18', '2027-01-19', '2027-02-04', '2027-02-17');
        let tripDays = 0, counted = 0, uncounted = 0;
        for (const def of Object.values(config.rooms)) {
            for (const iso of days) {
                for (const money of ['¥0', '¥5,000', '¥999,999']) {
                    const fits = (label) => right(def.name, label, money) <= MENU_LEFT - 2 * PAD;
                    const label = T.dateLabel(trips, iso, fmt, fits);
                    assert.ok(fits(label), `${def.name} on ${iso} with ${money}: "${label}" ends at ${right(def.name, label, money)}`);
                    assert.ok(label.endsWith(fmt(iso)));
                    if (T.leadIn(trips, iso)) {
                        assert.ok(label === fmt(iso) || /^devhouse 3 (in 30 days|in 30d|in 14 days|in 14d|tomorrow|in 1d|soon) \| /.test(label), label);
                        (label === fmt(iso) ? uncounted++ : counted++);
                    } else {
                        // a trip's own day reads like any other: the same in a short-named room and a long-named one
                        assert.strictEqual(label, fmt(iso), `${def.name} on ${iso}`);
                        assert.strictEqual(T.dateLabel(trips, iso, fmt), fmt(iso));
                        if (T.during(T.forDate(trips, iso), iso)) tripDays++;
                    }
                }
            }
        }
        assert.ok(tripDays > 0 && counted > 0 && uncounted > 0, `trip days were checked (${tripDays}); the countdown is kept where there is room (${counted}), dropped where not (${uncounted})`);
        for (const fits of [undefined, () => true, () => false]) {
            assert.strictEqual(T.dateLabel(trips, '2027-02-20', fmt, fits), 'February 20 2027');
            assert.strictEqual(T.dateLabel(trips, '2027-02-18', fmt, fits), 'February 18 2027');
            assert.strictEqual(T.dateLabel(trips, '2027-02-28', fmt, fits), 'February 28 2027');
            assert.strictEqual(T.dateLabel(trips, '2025-11-02', fmt, fits), 'November 2 2025');
        }
        // layoutHUD only asks for a fitted label on a countdown day
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('const counting = Trips.dateLabel(Trips.of(this.config), gameDate(), formatGameDate) !== bare;'));
        assert.ok(!/devhouse \d+ · /.test(src));
    });

    test('a room narrower than a phone view is measured by its boundary (#110)', () => {
        const RM = game('RoomManager');
        const rm = { scene: { GRID_SIZE: 64 }, rooms: {
            Konbini: { boundary: [[6, 4], [14, 4], [14, 10], [11, 10], [11, 11], [9, 11], [9, 10], [6, 10]] },
            City: { boundary: null } } };
        assert.strictEqual(JSON.stringify(RM.prototype.contentColumns.call(rm, 'Konbini')), '{"x0":384,"x1":896}');
        assert.strictEqual(RM.prototype.contentColumns.call(rm, 'City'), null);
        assert.strictEqual(RM.prototype.contentColumns.call(rm, 'Nowhere'), null);
        // the camera bounds only change when the view is narrower than the canvas
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(/if \(viewW < this\.scale\.width\) \{\s*const cols = this\.roomManager\.contentColumns\(roomKey\)/.test(src));
    });

    test('a room shorter than a zoomed view is held under the HUD bar (#205)', () => {
        const RM = game('RoomManager');
        const rm = { scene: { GRID_SIZE: 64 }, rooms: {
            Konbini: { boundary: [[6, 4], [14, 4], [14, 10], [11, 10], [11, 11], [9, 11], [9, 10], [6, 10]] },
            City: { boundary: null } } };
        const rows = RM.prototype.contentRows.call(rm, 'Konbini');
        assert.strictEqual(JSON.stringify(rows), '{"y0":256,"y1":704}');
        assert.strictEqual(RM.prototype.contentRows.call(rm, 'City'), null);
        // fits under the bar: one camera position, the room centred in the 550px below a 50px bar
        let held = RM.heldRows(rows, 600, 50);
        assert.deepStrictEqual([held.y, held.height], [155, 600]);
        assert.strictEqual(held.y + 50 + (600 - 50) / 2, (256 + 704) / 2);
        // fits the view but not under the bar (a 2x landscape phone): scrolls only from
        // its back wall just under the bar to its door at the foot of the view
        held = RM.heldRows(rows, 480, 50);
        assert.deepStrictEqual([held.y, held.height], [206, 498]);
        assert.strictEqual(held.y + 50, 256);
        assert.strictEqual(held.y + held.height, 704);
        // taller than the view, or no outline: the camera follows as ever
        assert.strictEqual(RM.heldRows(rows, 400, 50), null);
        assert.strictEqual(RM.heldRows(null, 480, 50), null);
        // only a zoomed view is held, and a HUD bar that changes height re-applies the bounds
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(/if \(viewH < this\.scale\.height\) \{\s*const held = RoomManager\.heldRows\(this\.roomManager\.contentRows\(roomKey\), viewH, this\.hudCover\(\)\)/.test(src));
        assert.ok(/this\.hudBarCover = this\.hudBarHeight \* zoom;\s*this\.applyRoomBounds\(/.test(src));
    });

    test('the Map overlay draws the towns larger on a portrait phone, and as before elsewhere (#197)', () => {
        const fit = game('UIScale.mapFit');
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        const before = (W, H) => Math.min((W - 120) / map.width, (H - 170) / map.height, 1);
        // the full canvas (desktop, landscape phone) is limited by its height: unchanged
        assert.strictEqual(fit(1280, 960, map.width, map.height, false), before(1280, 960));
        // a cropped portrait view is limited by its width: only the frame's margin is kept
        for (const W of [game('Viewport.MIN_VISIBLE'), 612]) {
            const s = fit(W, 960, map.width, map.height, true);
            assert.strictEqual(s, (W - 24) / map.width);
            assert.ok(s >= before(W, 960) * 1.19, `rooms at least 19% larger at ${W}`);
            assert.ok(map.width * s <= W - 24 && map.height * s <= 960 - 170);
        }
        // never past 1:1, whatever the image
        assert.strictEqual(fit(1280, 960, 400, 300, false), 1);
        assert.ok(/const s = UIScale\.mapFit\(W, H, meta\.width, meta\.height, W < this\.scale\.width\);/.test(
            fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8')));
    });

    test('a landscape phone keeps a long room name on one HUD row by abbreviating (#202)', () => {
        const short = game('shortGameDate');
        assert.strictEqual(short('2025-11-11'), 'Nov 11 2025');
        assert.strictEqual(short('2027-02-02', false), 'Feb 2');
        assert.strictEqual(short('2026-05-31'), 'May 31 2026');
        // tried in order before the bar wraps, and only where the whole canvas is across the view
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes("const brief = room.split(' | ')[0], whole = this.cameras.main.width >= this.scale.width;"));
        assert.ok(src.includes('whole && [[room, true], [brief, true], [room, false], [brief, false]]'));
        assert.ok(src.includes('if (!row(long) && !full && !row(short) && !compact()) {'));
    });

    test('every separator on the HUD bar is a pipe (#207)', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate'), hudName = game('hudName');
        assert.strictEqual(hudName('7-Eleven · Park 1'), '7-Eleven | Park 1');
        assert.strictEqual(hudName('Don Takote · Osaka'), 'Don Takote | Osaka');
        assert.strictEqual(hudName('Sapporo Station'), 'Sapporo Station');
        assert.strictEqual(hudName('a · b · c'), 'a | b | c');
        // every room's name as the bar writes it, and every form of the countdown
        const dotted = Object.values(config.rooms).filter((r) => r.name && r.name.includes('·'));
        assert.ok(dotted.length >= 10, 'the konbinis and Don Takotes keep their dotted names in config');
        for (const [key, def] of Object.entries(config.rooms)) assert.ok(!hudName(def.name || key).includes('·'), key);
        for (const fits of [undefined, (l) => !/days|tomorrow/.test(l), (l) => !/in \d/.test(l) && !/tomorrow/.test(l)]) {
            for (const iso of ['2027-01-19', '2027-02-04', '2027-02-10', '2027-02-17']) {
                const label = T.dateLabel(trips, iso, fmt, fits);
                assert.ok(/^devhouse 3 .+ \| /.test(label) && !label.includes('·'), label);
            }
        }
        // the bar is composed with pipes only: the name through hudName, the abbreviation cut at the first pipe
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('return hudName((room && room.name) || key);'));
        assert.ok(src.includes('const long = `${this.config.game.title} | ${room} | `, short = `${room} | `;'));
        assert.ok(src.includes('this.hudMoneyText.setText(` | ${this.shop.fmt(this.shop.money)}`);'));
        assert.strictEqual('7-Eleven | Park 1'.split(' | ')[0], '7-Eleven');
    });

    test('the rotate prompt is for a portrait phone, once per turn into portrait, twice a session (#111, #199)', () => {
        // not in the runner's load list: the class is loaded here, as index.html does
        if (game('typeof RotatePrompt') === 'undefined') game(fs.readFileSync(path.join(GV2, 'src', 'RotatePrompt.js'), 'utf8'));
        const R = game('RotatePrompt');
        // who: a touch-first phone held upright, and nothing else
        assert.strictEqual(R.wanted(390, 844, true), true, 'portrait phone');
        assert.strictEqual(R.wanted(430, 932, true), true, 'big portrait phone');
        assert.strictEqual(R.wanted(844, 390, true), false, 'landscape phone');
        assert.strictEqual(R.wanted(1024, 768, true), false, 'landscape tablet');
        assert.strictEqual(R.wanted(768, 1024, true), false, 'portrait tablet');
        assert.strictEqual(R.wanted(1280, 960, false), false, 'desktop');
        assert.strictEqual(R.wanted(390, 844, false), false, 'a narrow mouse / keyboard window, or a touchscreen laptop');
        assert.strictEqual(R.wanted(390, 844, undefined), false);

        // when: a fresh session shows it at once, if the title or the plain world is all there is
        const plain = (o) => JSON.parse(JSON.stringify(o));
        const fresh = R.parse(null);
        assert.deepStrictEqual(plain(fresh), { shown: 0, armed: true });
        let step = R.next(fresh, true, false);
        assert.strictEqual(step.show, false, 'an overlay is up: it waits');
        assert.strictEqual(step.state, fresh, 'and the turn is not spent');
        step = R.next(fresh, true, true);
        assert.deepStrictEqual(plain(step), { state: { shown: 1, armed: false }, show: true });
        // dismissed or timed out: not again while the phone stays upright, however long
        let s = step.state;
        for (let i = 0; i < 5; i++) {
            step = R.next(s, true, true);
            assert.strictEqual(step.show, false);
            assert.strictEqual(step.state, s);
        }
        // it survives a Time Travel reload (sessionStorage), still spent
        s = R.parse(JSON.stringify(s));
        assert.strictEqual(R.next(s, true, true).show, false);
        // landscape re-arms it; back in portrait it shows once more, and that is the last
        s = R.next(s, false, true).state;
        assert.deepStrictEqual(plain(s), { shown: 1, armed: true });
        assert.strictEqual(R.next(s, false, true).state, s, 'nothing to store while it stays in landscape');
        step = R.next(s, true, true);
        assert.deepStrictEqual(plain(step), { state: { shown: 2, armed: false }, show: true });
        assert.strictEqual(R.MAX, 2);
        s = R.next(step.state, false, true).state;
        assert.strictEqual(R.next(s, true, true).show, false, 'never a third time in a session');
        // a desktop never shows it and stays as it was
        assert.strictEqual(R.next(fresh, false, true).show, false);
        assert.strictEqual(R.next(fresh, false, true).state, fresh);
        // junk in storage is a fresh session
        for (const junk of ['', 'x', '1', '{"shown":-3}', '{"shown":"2"}', 'null']) assert.deepStrictEqual(plain(R.parse(junk)), { shown: 0, armed: true }, junk);
        assert.deepStrictEqual(plain(R.parse('{"shown":2,"armed":false}')), { shown: 2, armed: false });

        // "free": anything visible at overlay depth that is not a float or opted out is an overlay
        const o = (depth, extra) => Object.assign({ depth, visible: true }, extra);
        assert.strictEqual(R.overlayUp([o(0), o(1000), o(1999)]), false, 'world and HUD');
        assert.strictEqual(R.overlayUp([o(0), o(2000)]), true, 'a panel');
        assert.strictEqual(R.overlayUp([o(2000, { visible: false }), o(3500, { uiFloat: true }), o(5000, { uiScaleSkip: true })]), false,
            'a hidden menu, a toast (or the prompt itself), the debug grid');
        assert.strictEqual(R.OVERLAY_DEPTH, game('UIScale.MIN_DEPTH'));
        assert.strictEqual(R.KEY, 'gamev2_rotate_prompt');
        assert.ok(/Rotate your phone\s+for a better experience/.test(R.TEXT));

        // wired in: in the page's script list, built after UIScale, and not an input-owning overlay
        assert.ok(fs.readFileSync(path.join(GV2, 'index.html'), 'utf8').includes("'src/RotatePrompt.js',"));
        const scene = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(scene.indexOf('new RotatePrompt(this)') > scene.indexOf('new UIScale(this)'));
        assert.ok(!/rotatePrompt/.test(fs.readFileSync(path.join(GV2, 'src', 'systems', 'InputHandler.js'), 'utf8')));
    });
};
