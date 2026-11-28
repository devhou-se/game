// Issue #68, last stage: the game shows only real places. The made-up towns (Machi, Inaka, Yukimura)
// are deleted, with their stations, Machi's 7-Eleven and the Tokyo/Machi seam; the posts that stood
// in them stand at the real place they are about, or the nearest one that exists.
module.exports = ({ test, assert, fs, path, GV2, game, realConfig }) => {
    const GONE = ['Machi', 'Inaka', 'Yukimura', 'InakaStation', 'YukimuraStation', 'KonbiniMachi1'];
    const raw = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));

    test('the made-up towns are gone from the world: rooms, stations, the city, the world file, the maps (#68)', () => {
        const cfg = raw();
        for (const k of GONE) {
            assert.ok(!(k in cfg.rooms), `${k} is still a room`);
            assert.ok(!fs.existsSync(path.join(GV2, 'tiled', k.toLowerCase() + '.tmj')), `tiled/${k.toLowerCase()}.tmj is still there`);
        }
        for (const part of ['stations', 'cities', 'districts', 'places', 'trips', 'airports', 'player']) {
            assert.ok(!/Machi|Inaka|Yukimura/.test(JSON.stringify(cfg[part])), `config.${part} still names one`);
        }
        // nothing leads to one, and nobody's display name is one
        for (const [key, room] of Object.entries(cfg.rooms)) {
            for (const t of room.transporters || []) assert.ok(!GONE.includes(t.targetRoom), `${key} has a door into ${t.targetRoom}`);
            assert.ok(!/Machi\b|Inaka|Yukimura/.test(room.name || ''), `${key} is named ${room.name}`);
        }
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        assert.ok(!world.maps.some((m) => /machi|inaka|yukimura/.test(m.fileName)), 'devhouse.world still places one');
        assert.deepStrictEqual(cfg.cities.TokyoCity.rooms.map((m) => m.room), ['Tokyo', 'Market', 'Palace', 'Park', 'Karuizawa'], 'Tokyo is five districts');
        // the generators went with them, and the positional palette was not shortened for it
        for (const town of ['machi', 'inaka', 'yukimura']) assert.ok(!fs.existsSync(path.join(GV2, 'tools', `generate_${town}.py`)));
        const pal = new Set(cfg.tilePalette);
        for (const key of ['station-name-inaka_0_0', 'station-name-yukimura_0_0', 'ice-pond-autotile_corner-nw']) {
            assert.ok(pal.has(key), `${key} left the palette: a retired sprite keeps its slot`);
        }
        // the villager went with Yukimura; the player sprite and the credits are untouched
        assert.strictEqual(cfg.player.sprite, 'james_front');
        assert.ok(!Object.values(cfg.rooms).some((r) => (r.npcs || []).some((n) => n.name === 'James')), 'James is still an NPC somewhere');
    });

    test('the posts that stood in a made-up town stand in a real one, with everything the post gave them (#68)', () => {
        const cfg = raw();
        const state = (room, name, date) => ((cfg.rooms[room].npcs || []).find((n) => n.name === name) || { states: {} }).states[date];
        const moved = [
            ['Osaka', 'Dylan', '2025-11-02', '568', /Lake Biwa/],          // out of Osaka along the river
            ['Osaka', 'Dylan', '2025-11-03', '590', /flat tyre/],
            ['Osaka', 'Dylan', '2025-11-04', '615', /Biwaichi/],
            ['Osaka', 'Dylan', '2025-11-05', '636', /Nagahama/],
            ['Osaka', 'Dylan', '2025-11-07', '681', /Lake Biwa/],
            ['FukuokaStation', 'Dylan', '2025-11-08', '694', /Fukuoka/],   // off the train at Hakata, where the others are
            ['TokyoStation', 'Julia', '2025-11-02', '572', /Karuizawa/],   // the morning train out of Tokyo
        ];
        for (const [room, name, date, post, says] of moved) {
            const st = state(room, name, date);
            assert.ok(st && st.present === true, `${name} ${date} is not in ${room}`);
            assert.deepStrictEqual([st.photo, st.posts.map((p) => p.id).join()], [post, post], `${name} ${date}`);
            assert.ok(says.test(st.dialogue.join(' ')) && st.dialogue.length === 4, `${name} ${date}: the lines went along`);
            // ... and nowhere else that day
            for (const [key, r] of Object.entries(cfg.rooms)) {
                if (key === room) continue;
                const other = ((r.npcs || []).find((n) => n.name === name) || {}).states;
                assert.ok(!other || !other[date] || other[date].present === false, `${name} ${date} is also in ${key}`);
            }
        }
        // the ride itself is not parked on a platform (#121)
        for (const date of ['2025-11-02', '2025-11-03', '2025-11-04', '2025-11-05', '2025-11-07']) {
            assert.ok(!state('OsakaStation', 'Dylan', date) || state('OsakaStation', 'Dylan', date).present === false, date);
        }
        // the last days of the trip still open where the trip was: Dylan's last state does not outvote them
        const startFor = game('Trips.startFor'), shipped = realConfig();
        assert.strictEqual(startFor(shipped, '2025-11-16', { newPlayer: true }).room, 'Osaka');
        assert.strictEqual(startFor(shipped, '2025-11-18', { newPlayer: true }).room, 'Tokyo');
        // every dated placement in the game is in a room that exists (the resolver the game uses)
        const config = realConfig(), byRoom = game('Trips.membersByRoom');
        const days = new Set();
        for (const r of Object.values(cfg.rooms)) for (const n of r.npcs || []) for (const d of Object.keys(n.states || {})) days.add(d);
        assert.ok(days.size > 20, `${days.size} content days`);
        for (const d of days) for (const g of byRoom(config, d)) assert.ok(g.room in cfg.rooms && !GONE.includes(g.room), `${d}: ${g.room}`);
    });

    test('no day starts anyone in a room that is gone, whoever they play: every trip, lead-in and content day, and each month 2023-2027 (#68)', () => {
        const config = realConfig(), startFor = game('Trips.startFor'), rm = config.rooms;
        const cast = [undefined, 'james', 'custom'].concat(Array.from(config.members));
        const day = (t) => new Date(t).toISOString().slice(0, 10), DAY = 86400000;
        const dates = new Set();
        for (let y = 2023; y <= 2027; y++) for (let m = 0; m < 12; m++) dates.add(day(Date.UTC(y, m, 1)));
        for (const trip of config.trips) {
            const from = Date.parse(trip.start) - ((trip.lead || 0) + 2) * DAY, to = Date.parse(trip.end) + 2 * DAY;
            for (let t = from; t <= to; t += DAY) dates.add(day(t));
        }
        for (const r of Object.values(rm)) for (const n of r.npcs || []) for (const d of Object.keys(n.states || {})) dates.add(d);
        const seen = new Set();
        for (const date of dates) {
            for (const played of cast) {
                for (const newPlayer of [false, true]) {
                    const at = startFor(config, date, { played, newPlayer });
                    assert.ok(at && at.room in rm && !GONE.includes(at.room), `${date} as ${played}: starts in ${at && at.room}`);
                    seen.add(at.room);
                }
            }
        }
        assert.ok(dates.size > 100 && seen.has('Tokyo') && seen.has('Sapporo') && seen.has('Asahikawa'), [...seen].join());
    });

    test('a station platform loses a tie for the start room to a room outdoors, and still wins a majority (#68)', () => {
        // Dylan's lingering post on Hakata's platform (8 Nov on) is one hop nearer home than Fukuoka town,
        // so on hops alone it took every 1-v-1 and 2-v-2 tie and the game opened on the platform.
        const config = realConfig(), startFor = game('Trips.startFor');
        const room = (date, played) => startFor(config, date, { played }).room;
        assert.strictEqual(room('2025-11-13', 'bailey'), 'Fukuoka');
        assert.strictEqual(room('2025-11-13', 'julia'), 'Fukuoka');
        assert.strictEqual(room('2025-11-08', 'bailey'), 'Fukuoka');
        assert.strictEqual(room('2025-11-12'), 'Fukuoka');
        assert.strictEqual(room('2025-11-05'), 'Kanazawa');
        // the tie rule is only the tie rule: hops still decide between two towns ...
        assert.strictEqual(room('2025-11-16'), 'Osaka');
        assert.strictEqual(room('2025-11-18'), 'Tokyo');
        // ... and a platform with more people on it than anywhere else is still where you start
        assert.strictEqual(room('2025-11-12', 'bailey'), 'FukuokaStation');
        assert.strictEqual(room('2025-10-20'), 'TokyoStation');
    });
};
