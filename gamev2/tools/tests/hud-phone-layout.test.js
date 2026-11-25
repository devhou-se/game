module.exports = ({ test, assert, fs, path, GV2, game, realConfig }) => {
    test('the HUD drops the trip name rather than run under the menu button, in every room (#118)', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate');
        // the HUD's metrics: PixelOperatorMono at 16px is 16px a character; 1280 wide, 10px padding, "menu" right-aligned
        const CH = 16, PAD = 10, MENU_LEFT = 1280 - PAD - 4 * CH;
        const right = (room, label, money) => PAD + CH * `${config.game.title} | ${room} | ${label} | ${money}`.length;
        const days = [...game('contentChangeDates')(config)].sort().concat('2027-02-20', '2027-02-26', '2026-11-25', '2027-01-18', '2027-01-19', '2027-02-04', '2027-02-17');
        let dropped = 0, kept = 0;
        for (const def of Object.values(config.rooms)) {
            for (const iso of days) {
                for (const money of ['¥0', '¥5,000', '¥999,999']) {
                    const fits = (label) => right(def.name, label, money) <= MENU_LEFT - 2 * PAD;
                    const label = T.dateLabel(trips, iso, fmt, fits);
                    assert.ok(fits(label), `${def.name} on ${iso} with ${money}: "${label}" ends at ${right(def.name, label, money)}`);
                    assert.ok(label.endsWith(fmt(iso)));
                    if (T.during(T.forDate(trips, iso), iso)) (label === fmt(iso) ? dropped++ : kept++);
                    else if (T.leadIn(trips, iso)) assert.ok(label === fmt(iso) || /^devhouse 3 (in 30 days|in 30d|in 14 days|in 14d|tomorrow|in 1d|soon) · /.test(label), label);
                    else assert.strictEqual(label, fmt(iso));
                }
            }
        }
        assert.ok(dropped > 0 && kept > dropped, `the name is kept where there is room (${kept}) and dropped where there is not (${dropped})`);
        assert.strictEqual(T.dateLabel(trips, '2027-02-20', fmt, () => false), 'February 20 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-20', fmt, () => true), 'devhouse 3 · February 20 2027');
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
        assert.ok(src.includes("const brief = room.split(' · ')[0], whole = this.cameras.main.width >= this.scale.width;"));
        assert.ok(src.includes('whole && [[room, true], [brief, true], [room, false], [brief, false]]'));
        assert.ok(src.includes('if (!row(long) && !full && !row(short) && !compact()) {'));
    });
};
