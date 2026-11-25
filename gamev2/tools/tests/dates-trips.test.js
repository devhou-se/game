module.exports = ({ test, assert, ctx, game, realConfig, bootOn }) => {
    test('the Time Travel legend explains every mark on a day, the trip underline included', () => {
        const legend = game('DatePicker.legend');
        assert.ok(/underline = trip/.test(legend(true)[0]), 'trip days are underlined, and the legend says so');
        assert.ok(!/underline/.test(legend(false)[0]), 'no trips, nothing underlined, nothing to explain');
        for (const hasTrips of [true, false]) {
            const [marks, keys] = legend(hasTrips);
            assert.ok(/dot = blog post/.test(marks) && /gold = today/.test(marks));
            assert.ok(/arrows: day\/week/.test(keys) && /ESC: close/.test(keys));
            // 16px PixelOperatorMono is 8.8px a character: 52 fit the 480px panel with a margin
            for (const line of [marks, keys]) assert.ok(line.length <= 52, `${line.length} chars: ${line}`);
        }
    });

    test('the Time Travel legend only names the colours on the month shown, and still fits (#98)', () => {
        const legend = game('DatePicker.legend');
        // a trip month a year from today: the game day is here, today is not
        assert.strictEqual(legend(true, { today: false, live: true })[0], 'dot = post · underline = trip · blue = you are here');
        // today's month, the game elsewhere; and a month with neither
        assert.strictEqual(legend(true, { today: true, live: false })[0], 'dot = blog post · underline = trip · gold = today');
        assert.strictEqual(legend(true, { today: false, live: false })[0], 'dot = blog post · underline = trip');
        assert.strictEqual(legend(false, { today: false, live: true })[0], 'dot = blog post · blue = you are here');
        // both on one month (?date= a day of this month)
        assert.ok(/blue = you/.test(legend(true, { today: true, live: true })[0]) && /gold = today/.test(legend(true, { today: true, live: true })[0]));
        for (const hasTrips of [true, false]) for (const today of [true, false]) for (const live of [true, false]) {
            const [marks] = legend(hasTrips, { today, live });
            assert.ok(marks.length <= 52, `${marks.length} chars: ${marks}`);
            assert.strictEqual(/gold/.test(marks), today);
            assert.strictEqual(/blue/.test(marks), live);
            assert.strictEqual(/trip/.test(marks), hasTrips);
        }
    });

    test('outside the trip the game opens on a trip day, and cycles through them', () => {
        const defaultGameDate = game('defaultGameDate');
        const dates = ['2025-10-02', '2025-10-03', '2025-11-18'];
        assert.strictEqual(defaultGameDate('2025-10-10', dates), '2025-10-10');
        assert.strictEqual(defaultGameDate('2025-11-19', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2025-11-21', dates), '2025-11-18');
        assert.strictEqual(defaultGameDate('2025-11-22', dates), '2025-10-02');
        assert.strictEqual(defaultGameDate('2030-01-01', []), '2030-01-01');
    });

    test('trips are separate ranges: today during one, a day of the last one with posts between them (#118)', () => {
        const defaultGameDate = game('defaultGameDate'), T = game('Trips');
        const trips = T.of(realConfig());
        assert.deepStrictEqual(Array.from(trips, t => t.id), ['devhouse2', 'devhouse3']);
        const d2 = ['2025-10-02', '2025-10-03', '2025-11-18'];
        // during devhouse 2, as before trips were data
        assert.strictEqual(defaultGameDate('2025-10-10', d2, trips), '2025-10-10');
        // between the trips: devhouse 2's days, cycled exactly as the one-trip rule did
        for (const today of ['2025-11-19', '2025-11-21', '2025-11-22', '2026-11-25', '2027-02-17']) {
            assert.strictEqual(defaultGameDate(today, d2, trips), defaultGameDate(today, d2, []), today);
        }
        // during devhouse 3 the game is live, before anyone has posted and after
        assert.strictEqual(defaultGameDate('2027-02-18', d2, trips), '2027-02-18');
        assert.strictEqual(defaultGameDate('2027-02-28', d2, trips), '2027-02-28');
        assert.strictEqual(defaultGameDate('2027-02-20', d2.concat('2027-02-19'), trips), '2027-02-20');
        // after devhouse 3: its own post days when it has any, else devhouse 2's — never one 15-month span
        assert.strictEqual(defaultGameDate('2027-03-01', d2, trips), defaultGameDate('2027-03-01', d2, []));
        const both = d2.concat('2027-02-19', '2027-02-26');
        assert.strictEqual(defaultGameDate('2027-03-01', both, trips), '2027-02-19');
        assert.strictEqual(defaultGameDate('2027-03-02', both, trips), '2027-02-26');
        assert.strictEqual(defaultGameDate('2027-03-03', both, trips), '2027-02-19');
        assert.strictEqual(defaultGameDate('2026-06-01', both, trips), defaultGameDate('2026-06-01', d2, []), 'the gap is not a trip');
        // a config with no posts at all opens on today
        assert.strictEqual(defaultGameDate('2026-06-01', [], trips), '2026-06-01');
        // which trip a date belongs to, and where the group is based
        const trip = (d) => T.forDate(trips, d).id;
        assert.deepStrictEqual(['2025-01-01', '2025-11-02', '2026-11-25', '2027-02-03', '2027-02-04', '2027-02-18', '2027-06-01'].map(trip),
            ['devhouse2', 'devhouse2', 'devhouse2', 'devhouse2', 'devhouse3', 'devhouse3', 'devhouse3']);
        const d3 = trips[1];
        assert.deepStrictEqual(['2027-02-18', '2027-02-24', '2027-02-25', '2027-02-28'].map(d => T.stayFor(d3, d).room),
            ['Sapporo', 'Sapporo', 'Asahikawa', 'Asahikawa']);
        assert.strictEqual(T.windowFor(trips, '2027-02-26').from, '2027-02-25');
        assert.strictEqual(T.windowFor(trips, '2027-02-20').from, '2027-02-18');
        assert.strictEqual(T.windowFor(trips, '2026-11-25').from, '2025-10-02');
        assert.strictEqual(T.of({ trips: [{ id: 'x' }, { id: 'y', start: '2027-02-18', end: '2027-02-01' }] }).length, 0, 'bad trips are dropped');
    });

    test('a trip opens a fortnight before it starts: a travel-day post is its own, not the last trip\'s', () => {
        const defaultGameDate = game('defaultGameDate'), T = game('Trips'), resolveNpc = game('resolveNpc');
        const trips = T.of(realConfig());
        const d2 = [...game('contentChangeDates')(realConfig())].filter(d => d < '2027').sort();
        assert.strictEqual(trips[1].opens, '2027-02-04');
        assert.strictEqual(T.of({ trips: [{ id: 'a', start: '2027-02-18', end: '2027-02-20', lead: 2 }] })[0].opens, '2027-02-16');
        assert.strictEqual(T.addDays('2027-03-01', -1), '2027-02-28');
        // the lead-in window: open, not started
        const w = T.windowFor(trips, '2027-02-10');
        assert.deepStrictEqual([w.trip.id, w.early, w.from], ['devhouse3', true, '2027-02-04']);
        assert.strictEqual(T.windowFor(trips, '2027-02-18').early, false);
        assert.strictEqual(T.windowFor(trips, '2025-09-01').early, false, 'before the first trip is not a lead-in');
        assert.strictEqual(T.during(trips[1], '2027-02-10'), false, 'not a trip day: no underline, and the HUD counts down to it instead');
        // a post on the way there is a devhouse 3 day, and leaves devhouse 2's days — and today's default — alone
        const withPost = d2.concat('2027-02-10');
        assert.deepStrictEqual(Array.from(T.daysOf(trips, trips[0], withPost)), d2);
        assert.deepStrictEqual(Array.from(T.daysOf(trips, trips[1], withPost)), ['2027-02-10']);
        for (const today of ['2026-11-25', '2027-02-03']) {
            assert.strictEqual(defaultGameDate(today, withPost, trips), defaultGameDate(today, d2, trips), today);
        }
        assert.strictEqual(defaultGameDate('2027-02-12', withPost, trips), '2027-02-10', 'in the lead-in, with a post: that post');
        assert.strictEqual(defaultGameDate('2027-02-12', d2, trips), defaultGameDate('2027-02-12', d2, []), 'in the lead-in, no post: devhouse 2');
        assert.strictEqual(defaultGameDate('2027-02-18', withPost, trips), '2027-02-18');
        // once the trip is over it is shown by its own days, never the day on the road before it
        const after = withPost.concat('2027-02-19', '2027-02-26');
        assert.deepStrictEqual(['2027-03-01', '2027-03-02', '2027-03-03', '2027-03-04'].map(t => defaultGameDate(t, after, trips)),
            ['2027-02-19', '2027-02-26', '2027-02-19', '2027-02-26']);
        assert.strictEqual(defaultGameDate('2027-03-01', withPost, trips), '2027-02-10', 'unless that is all there is');
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, withPost), '2027-02-18', 'Time Travel lands on a day of the trip itself');
        // the post places its author on the lead-in days; from day one everyone is at the base
        const base = { name: 'Sam', sprite: 'sam_front', gridX: 21, gridY: 27, dialogue: ['base'], trip: 'devhouse3', stay: 'Sapporo',
            states: { '2027-02-10': { present: false } } };
        const away = { name: 'Sam', sprite: 'sam_front', gridX: 3, gridY: 3, dialogue: [], present: false,
            states: { '2027-02-10': { present: true, dialogue: ['at the airport'] }, '2025-11-01': { present: true, dialogue: ['old'] } } };
        const at = (npc, d) => { const r = resolveNpc(npc, d, trips); return r && r.dialogue[0]; };
        assert.deepStrictEqual(['2027-02-09', '2027-02-10', '2027-02-17', '2027-02-18'].map(d => at(away, d)), [null, 'at the airport', 'at the airport', null]);
        assert.deepStrictEqual(['2027-02-09', '2027-02-10', '2027-02-17', '2027-02-18'].map(d => at(base, d)), [null, null, null, 'base']);
        assert.strictEqual(at(away, '2026-11-25'), 'old');
    });

    test('the lead-in days say the trip has not started: HUD countdown, intro, and a start at the base to come (#164)', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config), fmt = game('formatGameDate');
        const lead = (d) => { const l = T.leadIn(trips, d); return l && [l.trip.id, l.days, l.stay.room]; };
        assert.deepStrictEqual(lead('2027-02-04'), ['devhouse3', 14, 'Sapporo']);
        assert.deepStrictEqual(lead('2027-02-17'), ['devhouse3', 1, 'Sapporo']);
        for (const d of ['2027-02-03', '2027-02-18', '2027-02-26', '2027-03-01', '2025-09-01', '2025-11-02']) assert.strictEqual(lead(d), null, d);
        assert.strictEqual(T.upcoming(trips, '2027-02-10').id, 'devhouse3');
        assert.strictEqual(T.upcoming(trips, '2027-02-18'), null);
        assert.strictEqual(T.upcoming(trips, '2026-11-25'), null);
        // the HUD: a countdown, "soon" where the count does not fit, the bare date where nothing does
        assert.strictEqual(T.dateLabel(trips, '2027-02-10', fmt), 'devhouse 3 in 8 days · February 10 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-17', fmt), 'devhouse 3 tomorrow · February 17 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-10', fmt, (l) => !/in 8 days/.test(l)), 'devhouse 3 in 8d · February 10 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-10', fmt, (l) => !/in 8/.test(l)), 'devhouse 3 soon · February 10 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-17', fmt, (l) => !/tomorrow/.test(l)), 'devhouse 3 in 1d · February 17 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-10', fmt, () => false), 'February 10 2027');
        // in Sapporo with the starting wallet (16px a character, see the HUD test below) the short count is what fits
        const inSapporo = (label) => 10 + 16 * `${config.game.title} | Sapporo | ${label} | ¥5,000`.length <= 1280 - 10 - 64 - 20;
        assert.strictEqual(T.dateLabel(trips, '2027-02-10', fmt, inSapporo), 'devhouse 3 in 8d · February 10 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-04', fmt, inSapporo), 'devhouse 3 in 14d · February 4 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-02-03', fmt), 'February 3 2027');
        assert.strictEqual(T.dateLabel(trips, '2027-03-01', fmt), 'March 1 2027');
        // nobody is anywhere, so everyone starts at the base the group will arrive at
        for (const d of ['2027-02-04', '2027-02-10', '2027-02-17']) {
            assert.strictEqual(T.membersByRoom(config, d).length, 0, d);
            for (const played of [undefined, 'james', 'khoi']) {
                assert.deepStrictEqual({ ...T.startFor(config, d, { played }) }, { room: 'Sapporo', x: 33, y: 12 }, d);
            }
        }
        // the intro: page 1 says when it starts, page 3 where — and not to "walk into one"
        assert.strictEqual(T.arrivalText(config, '2027-02-10', 'Sapporo'), 'devhouse 3 starts here in Sapporo on February 18.');
        assert.strictEqual(T.arrivalText(config, '2027-02-10', 'Tokyo'), 'devhouse 3 starts in Sapporo on February 18.');
        assert.strictEqual(T.arrivalText(config, '2027-02-18', 'Sapporo'), '');
        assert.strictEqual(T.arrivalText(config, '2025-11-02', 'Tokyo'), '');
        const meet = game('Intro.meetCopy');
        const arrival = T.arrivalText(config, '2027-02-10', 'Sapporo');
        assert.strictEqual(meet([], 'Sapporo', arrival),
            'They have not arrived yet: devhouse 3 starts here in Sapporo on February 18. Have a look around before they get here.');
        assert.strictEqual(meet(T.membersByRoom(config, '2027-02-20'), 'Sapporo', ''), 'Today everyone is here in Sapporo. Walk into one to say hello.');
        assert.strictEqual(meet([], 'Tokyo', ''), 'They are out and about. Go and find one to say hello.');
        const welcome = game('Intro.welcomeCopy');
        const early = welcome(config, '2027-02-10', '2027-02-10');
        assert.strictEqual(early[0], 'devhouse is a group of friends: Bailey, Damian, Dylan, Julia, Khoi, Sam and Xander.');
        assert.strictEqual(early[1], 'devhouse 3, their trip to Hokkaido, starts on February 18. This is the little world they will be walking around.');
        assert.ok(/once they start writing/.test(early[2]));
        // a real visitor that week is shown a devhouse 2 day: it says the next trip is about to start
        const d2day = welcome(config, '2025-11-11', '2027-02-10');
        assert.ok(/^This is devhouse 2, their trip to Japan: .* devhouse 3 starts on February 18\.$/.test(d2day[1]), d2day[1]);
        assert.ok(!/starts on/.test(welcome(config, '2025-11-11', '2026-11-25')[1]), 'not months ahead');
        assert.ok(!/starts on/.test(welcome(config, '2025-11-11', '2027-02-20')[1]), 'not once it has started');

        // somebody posts from the road: they are placed, the player starts beside them, and the intro says both
        const posted = JSON.parse(JSON.stringify(config));
        posted.rooms.Tokyo.npcs.push({ name: 'Sam', sprite: 'sam_front', gridX: 30, gridY: 36, dialogue: [], present: false,
            states: { '2027-02-12': { present: true, dialogue: ['At the airport.'] } } });
        const groups = T.membersByRoom(posted, '2027-02-13');
        assert.strictEqual(groups.map(g => `${g.room}: ${g.members.map(m => m.name).join()}`).join('; '), 'Tokyo: Sam');
        const spot = T.startFor(posted, '2027-02-13', { played: 'james' });
        assert.strictEqual(spot.room, 'Tokyo');
        assert.ok(Math.max(Math.abs(spot.x - 30), Math.abs(spot.y - 36)) <= 6, `${spot.x},${spot.y}`);
        assert.deepStrictEqual({ ...T.startFor(posted, '2027-02-13', { played: 'sam' }) }, { room: 'Sapporo', x: 33, y: 12 }, 'playing Sam: nobody else is anywhere');
        assert.strictEqual(meet(groups, 'Tokyo', T.arrivalText(posted, '2027-02-13', 'Tokyo')),
            'Today Sam is here in Tokyo. devhouse 3 starts in Sapporo on February 18. Walk into Sam to say hello.');
        assert.deepStrictEqual({ ...T.startFor(posted, '2027-02-11', { played: 'james' }) }, { room: 'Sapporo', x: 33, y: 12 }, 'the day before the post');
        assert.deepStrictEqual({ ...T.startFor(posted, '2027-02-18', { played: 'james' }) }, { room: 'Sapporo', x: 33, y: 12 }, 'day one: the lead-in post is history');
    });

    test('the game date on a stubbed clock: live in devhouse 3, a devhouse 2 day between trips, ?date= wins (#118)', () => {
        const days = [...game('contentChangeDates')(realConfig())].sort();
        assert.strictEqual(bootOn('2027-02-20'), '2027-02-20');
        assert.strictEqual(bootOn('2027-02-26'), '2027-02-26');
        const between = bootOn('2026-11-25');
        assert.ok(days.includes(between) && between < '2026', `between trips opens on a devhouse 2 post day, got ${between}`);
        assert.strictEqual(bootOn('2026-11-25', '?date=2025-11-02'), '2025-11-02');
        assert.strictEqual(bootOn('2027-02-20', '?date=2025-11-02'), '2025-11-02');
        assert.strictEqual(bootOn('2026-11-25', '?date=2027-02-26'), '2027-02-26');
        // the HUD names the trip on its own days only
        const label = (d) => game('Trips.dateLabel')(game('Trips.of')(realConfig()), d, game('formatGameDate'));
        assert.strictEqual(label('2027-02-20'), 'devhouse 3 · February 20 2027');
        assert.strictEqual(label('2025-11-02'), 'devhouse 2 · November 2 2025');
        assert.strictEqual(label('2026-11-25'), 'November 25 2026');
        bootOn('2026-11-25');
    });

    test('a player, new or returning, starts next to the cast, never counting who they play (#96, #59, #166)', () => {
        const config = realConfig(), startFor = game('Trips.startFor'), byRoom = game('Trips.membersByRoom');
        const near = (spot, date, played) => {
            const g = byRoom(config, date, { played }).find(r => r.room === spot.room);
            return g ? Math.min(...g.members.map(m => Math.max(Math.abs(m.x - spot.x), Math.abs(m.y - spot.y)))) : Infinity;
        };
        const days = [...game('contentChangeDates')(config)].filter(d => d < '2027').sort();
        let moved = 0;
        for (const date of days) {
            // a returning player is started exactly as a new one is (#166), and with no opts at all
            assert.deepStrictEqual({ ...startFor(config, date, { newPlayer: false }) }, { ...startFor(config, date, { newPlayer: true }) }, date);
            assert.deepStrictEqual({ ...startFor(config, date) }, { ...startFor(config, date, { played: undefined }) }, date);
            for (const played of [undefined, 'james', 'bailey', 'damian', 'dylan', 'julia']) {
                const spot = startFor(config, date, { newPlayer: true, played });
                const anyone = byRoom(config, date, { played }).length > 0;
                assert.ok(anyone, `${date} as ${played}: someone is out there`);
                const gap = near(spot, date, played);
                assert.ok(gap >= 1 && gap <= 6, `${date} as ${played}: starts ${gap} cells from someone, at ${spot.room} ${spot.x},${spot.y}`);
                assert.deepStrictEqual({ ...startFor(config, date, { newPlayer: true, played }) }, { ...spot }, 'deterministic');
                if (spot.room !== 'Tokyo') moved++;
            }
        }
        assert.ok(moved > 0, 'on some devhouse 2 days a new player starts outside Tokyo');
        // devhouse 3: Sapporo, then Asahikawa — new or returning, whoever you play
        for (const played of [undefined, 'bailey', 'khoi']) {
            for (const newPlayer of [false, true]) {
                assert.deepStrictEqual({ ...startFor(config, '2027-02-20', { newPlayer, played }) }, { room: 'Sapporo', x: 33, y: 12 });
                assert.deepStrictEqual({ ...startFor(config, '2027-02-26', { newPlayer, played }) }, { room: 'Asahikawa', x: 31, y: 12 });
            }
            assert.ok(near({ room: 'Sapporo', x: 33, y: 12 }, '2027-02-20', played) <= 6);
            assert.ok(near({ room: 'Asahikawa', x: 31, y: 12 }, '2027-02-26', played) <= 6);
        }
        // the one member in the room is who you are playing: go where somebody else is
        const tiny = { game: { gridSize: 64, worldWidth: 640, worldHeight: 640 }, player: { startRoom: 'A', startX: 1, startY: 1 },
            trips: [{ id: 't', start: '2030-01-01', end: '2030-01-09', members: ['ann', 'bob'], home: { room: 'A', x: 1, y: 1 } }],
            rooms: {
                A: { npcs: [{ name: 'Ann', sprite: 'ann_front', gridX: 3, gridY: 1, dialogue: [] }], transporters: [{ gridX: 0, gridY: 0, targetRoom: 'B', targetX: 1, targetY: 1 }],
                    layers: [{ name: 'Floor', tiles: Object.fromEntries([...Array(100)].map((_, i) => [`${i % 10},${Math.floor(i / 10)}`, 'f'])) }] },
                B: { npcs: [{ name: 'Bob', sprite: 'bob_front', gridX: 8, gridY: 8, dialogue: [] }], transporters: [],
                    layers: [{ name: 'Floor', tiles: Object.fromEntries([...Array(100)].map((_, i) => [`${i % 10},${Math.floor(i / 10)}`, 'f'])) },
                        { name: 'Walls', collision: true, tiles: { '6,9': 'w', '6,8': 'w', '6,7': 'w', '6,6': 'w', '7,6': 'w', '8,6': 'w', '9,6': 'w' } }] },
            } };
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true }) }, { room: 'A', x: 1, y: 1 }, 'home wins a tie');
        assert.deepStrictEqual({ ...game('Trips.hopsFrom')(realConfig(), 'Tokyo') }.Machi, 1);
        assert.ok(game('Trips.hopsFrom')(realConfig(), 'Tokyo').Inaka > game('Trips.hopsFrom')(realConfig(), 'Tokyo').Palace, 'a train ride is further than next door');
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true, played: 'ann' }) }, { room: 'B', x: 5, y: 5 },
            'Bob is walled in: the nearest cell that can be walked to');
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { played: 'ann' }) }, { room: 'B', x: 5, y: 5 }, 'returning or new');
        tiny.rooms.B.npcs = [];
        assert.deepStrictEqual({ ...startFor(tiny, '2030-01-02', { newPlayer: true, played: 'ann' }) }, { room: 'A', x: 1, y: 1 }, 'nobody else anywhere: home');
        // company: a member within NEAR cells of a cell, not counting who you play (resettleNewPlayer's guard)
        const company = game('Trips.hasCompany');
        assert.strictEqual(company(config, '2027-02-20', 'Sapporo', 33, 12, 'bailey'), true, 'Damian is still next to the Sapporo start');
        assert.strictEqual(company(config, '2027-02-20', 'Tokyo', 29, 38, undefined), false);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, undefined), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'ann'), false, 'the only one there is who you play');
        tiny.rooms.A.npcs.push({ name: 'Bob', sprite: 'bob_front', gridX: 2, gridY: 4, dialogue: [] });
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'ann'), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 1, 1, 'bob'), true);
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 8, 8, 'ann'), true, 'Bob at 2,4 is 6 cells off');
        assert.strictEqual(company(tiny, '2030-01-02', 'A', 8, 8, 'bob'), false, 'Ann at 3,1 is more than 6 cells off');
        // a new player is one who has not finished the intro
        const store = {};
        ctx.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
        const isNew = game('Intro.isNewPlayer');
        assert.strictEqual(isNew(), true, 'fresh profile');
        store.gamev2_intro_seen = 'pending'; store.gamev2_character = 'custom';
        assert.strictEqual(isNew(), true, 'half way through the intro');
        store.gamev2_intro_seen = '1';
        assert.strictEqual(isNew(), false, 'finished it');
        delete store.gamev2_intro_seen;
        assert.strictEqual(isNew(), false, 'a player from before the intro existed');
    });

    test('Time Travel jumps between trips (#118)', () => {
        const T = game('Trips'), trips = T.of(realConfig());
        const posts = ['2025-10-04', '2025-11-18'];
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, posts), '2027-02-18', 'no posts yet: the first day');
        assert.strictEqual(T.jump(trips, '2025-11-02', 1, posts.concat('2027-02-19')), '2027-02-19');
        assert.strictEqual(T.jump(trips, '2027-02-20', -1, posts), '2025-10-04');
        assert.strictEqual(T.jump(trips, '2026-05-01', -1, posts), '2025-10-04');
        assert.strictEqual(T.jump(trips, '2026-05-01', 1, posts), '2027-02-18');
        assert.strictEqual(T.jump(trips, '2027-02-20', 1, posts), null);
        assert.strictEqual(T.jump(trips, '2025-10-04', -1, posts), null);
    });
};
