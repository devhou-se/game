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
        // the Map is Japan since #211 (pixel art, drawn larger than 1:1): the same fit, with a ceiling
        assert.ok(/const s = UIScale\.mapFit\(W, H, meta\.width, meta\.height, W < this\.scale\.width, UIScale\.MAP_MAX_SCALE\);/.test(
            fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8')));
    });

    test('a landscape phone keeps a long room name on one HUD row by abbreviating (#202)', () => {
        const short = game('shortGameDate');
        assert.strictEqual(short('2025-11-11'), 'Nov 11 2025');
        assert.strictEqual(short('2027-02-02', false), 'Feb 2');
        assert.strictEqual(short('2026-05-31'), 'May 31 2026');
        // tried in order before the bar wraps, and only where the whole canvas is across the view
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('const brief = hudBrief(room), whole = this.cameras.main.width >= this.scale.width;'));
        assert.ok(src.includes('whole && [[room, true], [brief, true], [room, false], [brief, false]]'));
        assert.ok(src.includes('if (!row(long) && !full && !count() && !row(short) && !compact()) {'));
    });

    test('on a landscape phone a lead-in day\'s countdown stands in place of the date', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate'), hudName = game('hudName');
        // the countdown on its own, longest form that fits; null off a lead-in day or when nothing fits
        assert.strictEqual(T.countdown(trips, '2027-02-10'), 'devhouse 3 in 8 days');
        assert.strictEqual(T.countdown(trips, '2027-02-10', (l) => l.length <= 16), 'devhouse 3 in 8d');
        assert.strictEqual(T.countdown(trips, '2027-02-10', (l) => l.length <= 15), 'devhouse 3 soon');
        assert.strictEqual(T.countdown(trips, '2027-02-10', () => false), null);
        assert.strictEqual(T.countdown(trips, '2027-02-17'), 'devhouse 3 tomorrow');
        assert.strictEqual(T.countdown(trips, '2027-01-19', (l) => !/days/.test(l)), 'devhouse 3 in 30d');
        for (const iso of ['2027-02-18', '2027-02-20', '2025-11-02', '2026-11-25']) assert.strictEqual(T.countdown(trips, iso), null, iso);
        // it is the date label's own countdown, with no date and so no separator of its own
        for (const iso of ['2027-01-19', '2027-02-04', '2027-02-10', '2027-02-17']) {
            for (const fits of [undefined, (l) => !/days|tomorrow/.test(l), (l) => /soon/.test(l)]) {
                const count = T.countdown(trips, iso, fits);
                assert.ok(!count.includes('|') && !count.includes('·'), count);
                assert.strictEqual(T.dateLabel(trips, iso, fmt, fits && ((l) => fits(l.split(' | ')[0]))), `${count} | ${fmt(iso)}`);
            }
        }
        // the phone bars: PixelOperatorMono 16px is 16px a character, 10px padding, "menu" right-aligned;
        // 844x390 lays the bar out 744 wide and 667x375 715 wide. `name | count | wallet` ends a padding short of menu
        const CH = 16, PAD = 10;
        const bar = (width, name, money, iso) => {
            const fits = (lead) => (l) => PAD + CH * `${lead} | ${l} | ${money}`.length + PAD + 4 * CH + PAD <= width;
            // layoutHUD's order: the whole name, then its cut ("7-Eleven"); but a short form that leads with
            // the town ("Tokyo shrine") before the whole name, so every shrine reads the same way (#220)
            const brief = game('hudBrief')(name);
            for (const lead of name.startsWith(brief) ? [name, brief] : [brief, name]) {
                const count = T.countdown(trips, iso, fits(lead));
                if (count) return `${lead} | ${count} | ${money}`;
            }
            return null;
        };
        assert.strictEqual(bar(744, 'Sapporo', '¥5,000', '2027-02-10'), 'Sapporo | devhouse 3 in 8 days | ¥5,000');
        assert.strictEqual(bar(715, 'Sapporo', '¥5,000', '2027-02-10'), 'Sapporo | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(715, 'Sapporo', '¥5,000', '2027-01-19'), 'Sapporo | devhouse 3 in 30d | ¥5,000');
        assert.strictEqual(bar(715, 'Sapporo', '¥999,999', '2027-02-04'), 'Sapporo | devhouse 3 in 14d | ¥999,999');
        assert.strictEqual(bar(715, hudName('7-Eleven · Sapporo'), '¥5,000', '2027-02-10'), '7-Eleven | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(744, 'Sapporo Station', '¥5,000', '2027-02-10'), null, 'too long a name for any form: the date, as on any day');
        // every room at both phone widths with the starting wallet. The rule, not a ratio and not a kind of
        // room: a bar shows the date alone only when the room's name (its first part) leaves no room for the
        // shortest countdown, "devhouse 3 soon" - more than 13 characters at 844x390, more than 11 at 667x375
        let shown = 0;
        const bare = { 744: new Set(), 715: new Set() }, LIMIT = { 744: 13, 715: 11 };
        for (const def of Object.values(config.rooms)) {
            for (const width of [744, 715]) {
                const counted = bar(width, hudName(def.name), '¥5,000', '2027-02-10');
                // the bar tries the whole name, then its short form (hudBrief: "7-Eleven", "Sapporo house")
                const shortest = Math.min(hudName(def.name).length, game('hudBrief')(hudName(def.name)).length);
                assert.strictEqual(!!counted, shortest <= LIMIT[width], `${def.name} at ${width}: ${counted}`);
                if (counted) shown++; else bare[width].add(def.name);
            }
        }
        // which rooms that is today: on the larger phone the stations with a name longer than "Tokyo Station"
        // (13), on the smaller one every station and Shirakawa-go (12); and a house, whose short form keeps
        // its town ("Sapporo house", #208) and so can be as long as a station's - as do a lobby and a
        // shrine since #220 ("Tokyo shrine", "Market shrine": 12 and 13, the date at 667x375). Since #218 also, at
        // both widths, the two airports and the home city, whose names are as long as a station's (14 and more)
        const stations = Object.keys(config.stations).map(k => config.rooms[k].name).sort();
        const abroad = Object.keys(config.airports).map(k => config.rooms[k].name).concat(config.rooms.SanFranbourne.name);
        assert.ok(abroad.length === 3 && abroad.every(n => n.length > 13 && game('hudBrief')(hudName(n)) === hudName(n)), abroad.join());
        const notHouses = (set) => Array.from(set).filter(n => !/^(House|Lobby|Shrine) · /.test(n)).sort();
        const kinds = (set, kind) => Array.from(set).filter(n => n.startsWith(kind + ' · ')).sort();
        assert.deepStrictEqual(kinds(bare[744], 'Shrine').concat(kinds(bare[744], 'Lobby')), [], 'every shrine and lobby counts down at 844x390');
        assert.deepStrictEqual(kinds(bare[715], 'Shrine'), ['Shrine · Market', 'Shrine · Tokyo']);
        assert.deepStrictEqual(kinds(bare[715], 'Lobby'), []);
        assert.deepStrictEqual(notHouses(bare[744]), stations.filter(n => n.length > 13).concat(abroad).sort());
        assert.ok(bare[744].has('Kanazawa Station') && !bare[744].has('Tokyo Station'));
        assert.deepStrictEqual(notHouses(bare[715]), stations.concat('Shirakawa-go', abroad).sort());
        assert.ok(shown > bare[744].size + bare[715].size, `the countdown shows in ${shown} room bars`);
        assert.strictEqual(bar(744, 'Shirakawa-go', '¥5,000', '2027-02-10'), 'Shirakawa-go | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(715, 'Shirakawa-go', '¥5,000', '2027-02-10'), null, '3px too wide for "soon": the date, as in a station');
        assert.strictEqual(bar(744, hudName('House · Sapporo 3'), '¥5,000', '2027-02-10'), 'Sapporo house | devhouse 3 soon | ¥5,000');
        assert.strictEqual(bar(715, hudName('House · Sapporo 3'), '¥5,000', '2027-02-10'), null, 'the date, as in a station');
        // a shrine and a lobby read as a house does, in every town (#220): it was "Shrine | devhouse 3 in 8 days"
        // in Tokyo beside "Shrine | Park | devhouse 3 soon" in the Park, and a bare "Lobby"
        assert.strictEqual(bar(744, hudName('Shrine · Tokyo'), '¥5,000', '2027-02-10'), 'Tokyo shrine | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(744, hudName('Shrine · Park'), '¥5,000', '2027-02-10'), 'Park shrine | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(744, hudName('Shrine · Market'), '¥5,000', '2027-02-10'), 'Market shrine | devhouse 3 soon | ¥5,000');
        assert.strictEqual(bar(744, hudName('Lobby · Osaka 1'), '¥5,000', '2027-02-10'), 'Osaka lobby | devhouse 3 in 8d | ¥5,000');
        assert.strictEqual(bar(715, hudName('Shrine · Park'), '¥5,000', '2027-02-10'), 'Park shrine | devhouse 3 soon | ¥5,000');
        assert.strictEqual(bar(715, hudName('Lobby · Osaka 2'), '¥5,000', '2027-02-10'), 'Osaka lobby | devhouse 3 soon | ¥5,000');
        assert.strictEqual(bar(715, hudName('Shrine · Tokyo'), '¥5,000', '2027-02-10'), null, 'the date, as in a house');
        assert.strictEqual(bar(744, hudName('Kushida Shrine'), '¥5,000', '2027-02-10'), null, 'a hall with its own name is not reworded');
        // layoutHUD: only where the whole canvas is across a magnified view, on a countdown day, before the bare date
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('const names = room.startsWith(brief) ? [room, brief] : [brief, room];'));
        assert.ok(src.includes('const count = () => whole && counting && (row(short, true) || names.some((name) =>'));
        assert.ok(src.includes('!!Trips.countdown(Trips.of(this.config), gameDate(), (l) => fits(`${name} | `, l, pad))));'));
        assert.ok(src.includes('return label !== bare ? fits(lead, label, 2 * pad) : !counted && fits(lead, bare, pad);'));
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
        // the short form (hudBrief): the first part, but a house keeps its town - "House" alone says nothing (#208)
        const hudBrief = game('hudBrief');
        assert.strictEqual(hudBrief('7-Eleven | Park 1'), '7-Eleven');
        assert.strictEqual(hudBrief('Don Takote | Osaka'), 'Don Takote');
        assert.strictEqual(hudBrief('Sapporo Station'), 'Sapporo Station');
        assert.strictEqual(hudBrief('House | Sapporo 3'), 'Sapporo house');
        assert.strictEqual(hudBrief('House | Asahikawa 2'), 'Asahikawa house');
        assert.strictEqual(hudBrief('House | Market 1'), 'Market house');
        assert.strictEqual(hudBrief('House'), 'House');
        // and so do a tower's lobby and a shrine's hall: "Lobby" or "Shrine" alone says nothing either (#220)
        assert.strictEqual(hudBrief('Lobby | Osaka 1'), 'Osaka lobby');
        assert.strictEqual(hudBrief('Lobby | Osaka 3'), 'Osaka lobby');
        assert.strictEqual(hudBrief('Shrine | Tokyo'), 'Tokyo shrine');
        assert.strictEqual(hudBrief('Shrine | Park'), 'Park shrine');
        assert.strictEqual(hudBrief('Shrine | Market'), 'Market shrine');
        assert.strictEqual(hudBrief('Shrine'), 'Shrine');
        assert.strictEqual(hudBrief('Lobby'), 'Lobby');
        assert.strictEqual(hudBrief('Kushida Shrine'), 'Kushida Shrine', 'a hall with a name of its own keeps it');
        assert.strictEqual(hudBrief('Izakaya | Market'), 'Izakaya', 'only the kinds: any other name is cut at its first part');
        // every lobby and shrine in the world: the town leads, no bare kind, and the short date fits both phones
        const kindRooms = Object.values(config.rooms).filter((r) => /^(Lobby|Shrine) · /.test(r.name || ''));
        assert.ok(kindRooms.length >= 6, 'the three Osaka lobbies and the three Tokyo shrines');
        for (const def of kindRooms) {
            const brief = hudBrief(hudName(def.name)), [kind, town] = def.name.split(' · ');
            assert.strictEqual(brief, `${town.replace(/ \d+$/, '')} ${kind.toLowerCase()}`, def.name);
            for (const width of [744, 715]) assert.ok(10 + 16 * `${brief} | Feb 10 2027 | ¥5,000`.length + 10 + 64 + 10 <= width, `${brief} at ${width}`);
        }
        for (const def of Object.values(config.rooms).filter((r) => r.house)) {
            const brief = hudBrief(hudName(def.name)), town = config.rooms[def.house.host].name || def.house.host;
            assert.strictEqual(brief, `${town} house`, def.name);
            // and it fits the one-row bar of both phones with the short date and a full wallet's worth of room
            for (const width of [744, 715]) assert.ok(10 + 16 * `${brief} | Feb 10 2027 | ¥5,000`.length + 10 + 64 + 10 <= width, `${brief} at ${width}`);
        }
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

    test('a single line of overlay text is never shown under 10 CSS px on a small landscape phone, a hint line as before (#200)', () => {
        const U = game('UIScale'), g = U.textGrowth;
        const css = (font, zoom, down, room, hint) => font * zoom * g(font, zoom, down, room, hint) / down;
        // what the phones measured: the konbini's list (zoom 1.35, 1.21 once a toast has shown), the map
        // (1.02), the creator (1.41), the dialogue's caption (1.58), at 667x375 (2.56 canvas px per CSS px) and 844x390
        for (const down of [1280 / 500, 1280 / 520]) {
            for (const [font, zoom] of [[18, 1.35], [18, 1.21], [20, 1.21], [22, 1.02], [16, 1.41], [16, 1.58]]) {
                assert.ok(css(font, zoom, down, 3, false) >= U.MIN_TEXT - 1e-9, `${font}px at ${zoom} / ${down}`);
                assert.ok(g(font, zoom, down, 3, false) <= U.MAX_TEXT_FLOOR_GROWTH);
            }
        }
        // exactly to the floor, no further; nothing at all for text that is big enough, and on a desktop
        assert.ok(Math.abs(css(18, 1.21, 2.56, 3, false) - 10) < 1e-9);
        assert.strictEqual(g(24, 1.58, 2.56, 3, false), 1);
        assert.strictEqual(g(16, 1, 1, 3, false), 1);
        assert.strictEqual(g(12, 1, 1, 3, true), 1);
        // body text has neighbours: a quarter at most (a 568x320 phone gets most of the way), and never wider than its panel
        assert.strictEqual(g(16, 1.41, 3, 3, false), U.MAX_TEXT_FLOOR_GROWTH);
        assert.strictEqual(g(18, 1.21, 2.56, 1.1, false), 1.1);
        assert.strictEqual(g(18, 1.21, 2.56, 0.8, false), 1);
        // a hint line is what it was (#110): to 10 CSS px, up to 1.6x
        assert.strictEqual(U.MIN_HINT, 10);
        assert.ok(Math.abs(g(14, 1.41, 2.56, 3, true) - 10 / (14 * 1.41 / 2.56)) < 1e-9);
        assert.strictEqual(g(14, 1, 3, 3, true), U.MAX_HINT_GROWTH);
        assert.strictEqual(g(14, 1, 3, 1.2, true), 1.2);
        // ... and it stops short of the text beside it, which grows too: the shop's "[ buy ]" (right edge at 418) and
        // "[ buy & use now ]" (170 wide, right edge at 610) are 22px apart, so 1.25 would run them together
        const row = (grow) => [
            { box: { x0: 358, y0: 0, x1: 418, y1: 20 }, x: 418, y: 10, grow },
            { box: { x0: 440, y0: 0, x1: 610, y1: 20 }, x: 610, y: 10, grow },
        ];
        const edge = (t, g) => t.x + (t.box.x0 - t.x) * g;
        for (const [want, most] of [[1.06, 1.06], [1.1, 1.1], [1.18, 1.08], [1.25, 1.1]]) {      // down from what it wants in steps of 0.05
            const r = row(want), got = U.clearGrowth(r[1], r);
            assert.ok(got <= want && got >= 1 && edge(r[1], got) >= 418, `${want} -> ${got}`);
            assert.strictEqual(got, most);
            assert.strictEqual(U.clearGrowth(r[0], r), most);      // the one beside it comes its way just as far
        }
        // nothing beside it: all it wants; a plate it already sits on is not in its way; a neighbour that stays put still counts
        const lone = { box: { x0: 100, y0: 0, x1: 200, y1: 18 }, x: 150, y: 9, grow: 1.25 };
        assert.strictEqual(U.clearGrowth(lone, [lone]), 1.25);
        assert.strictEqual(U.clearGrowth(lone, [lone, { box: { x0: 90, y0: -4, x1: 210, y1: 22 }, x: 150, y: 9, grow: 1 }]), 1.25);
        assert.strictEqual(U.clearGrowth(lone, [lone, { box: { x0: 204, y0: 0, x1: 260, y1: 18 }, x: 204, y: 9, grow: 1 }]), 1.05);
        assert.strictEqual(U.clearGrowth(lone, [lone, { box: { x0: 201, y0: 0, x1: 260, y1: 18 }, x: 201, y: 9, grow: 1 }]), 1);
        // wrapped paragraphs and the cropped portrait view are left alone, and the loop is the one place it is applied
        const src = fs.readFileSync(path.join(GV2, 'src', 'systems', 'UIScale.js'), 'utf8');
        assert.ok(/if \(!hint && \(cropped \|\| o\.style\.wordWrapWidth \|\| o\.text\.indexOf\('\\n'\) >= 0\)\) continue;/.test(src));
    });
};
