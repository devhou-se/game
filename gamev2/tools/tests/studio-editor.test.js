module.exports = ({ test, assert, fs, path, GV2, game, load }) => {
    test('studio stacks overlapping districts the way the stitched city does: the later one on top', () => {
        const stackOrder = game('WorldModel.stackOrder');
        const cities = { C: { rooms: [{ room: 'Tokyo' }, { room: 'Market' }, { room: 'Gone' }, { room: 'Palace' }, { room: 'Park' }] } };
        const keys = ['Fukuoka', 'Market', 'Osaka', 'Palace', 'Park', 'Tokyo', 'Toyama'];
        assert.strictEqual(stackOrder({ cities }, keys).join(), 'Fukuoka,Tokyo,Osaka,Market,Palace,Park,Toyama', 'districts take the city order, other rooms stay put');
        assert.strictEqual(keys[1], 'Market', 'the list passed in is left alone');
        assert.strictEqual(stackOrder({}, keys).join(), keys.join());
        // the real world: wherever two rooms of the map overlap, the one stacked on top is the city's owner
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8')).rooms;
        const order = stackOrder(config, Object.keys(config.rooms));
        const rect = (k) => { const r = map[k], s = r.w / r.cells[0]; return { x: Math.round(r.x / s), y: Math.round(r.y / s), w: r.cells[0], h: r.cells[1] }; };
        const rank = Object.fromEntries(Object.values(config.cities).flatMap((c) => c.rooms.map((r, i) => [r.room, i])));
        let overlaps = 0;
        for (const a of Object.keys(map)) for (const b of Object.keys(map)) {
            const p = rect(a), q = rect(b);
            if (a >= b || p.x >= q.x + q.w || q.x >= p.x + p.w || p.y >= q.y + q.h || q.y >= p.y + p.h) continue;
            overlaps++;
            assert.ok(a in rank && b in rank, `${a} and ${b} overlap on the map but are not districts of one city`);
            assert.strictEqual(order.indexOf(a) < order.indexOf(b), rank[a] < rank[b], `${a} / ${b}`);
        }
        assert.ok(overlaps >= 3, 'Tokyo/Market, Market/Palace and Palace/Park overlap');
    });

    test('studio lays rooms out by where their towns are in Japan', () => {
        if (game('typeof Places') === 'undefined') load('utils/Places.js');
        const geoOf = game('WorldModel.geoOf');
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const keys = ['Asahikawa', 'Sapporo', 'Sendai', 'TokyoCity', 'HokurikuCity', 'Osaka', 'Fukuoka', 'SanFranbourne',
            'KonbiniFukuoka1', 'FukuokaStation', 'HanedaAirport', 'Kanazawa', 'Toyama', 'Shirakawago', 'Nowhere'];
        const at = geoOf(config, keys);
        const east = (...list) => list.forEach((k, i) => i && assert.ok(at[list[i - 1]][0] < at[k][0], `${list[i - 1]} is west of ${k}`));
        const south = (...list) => list.forEach((k, i) => i && assert.ok(at[list[i - 1]][1] < at[k][1], `${list[i - 1]} is north of ${k}`));
        east('Fukuoka', 'Osaka', 'HokurikuCity', 'TokyoCity', 'Sendai', 'Sapporo', 'Asahikawa');
        south('Asahikawa', 'Sapporo', 'Sendai', 'HokurikuCity', 'TokyoCity', 'Osaka', 'Fukuoka');
        east('TokyoCity', 'SanFranbourne');
        south('TokyoCity', 'SanFranbourne');
        assert.deepStrictEqual([at.KonbiniFukuoka1, at.FukuokaStation], [at.Fukuoka, at.Fukuoka], 'an interior and a station are where their town is');
        assert.deepStrictEqual(at.HanedaAirport, at.TokyoCity, 'an airport is where the town it serves is');
        east('Kanazawa', 'HokurikuCity', 'Toyama');
        south('Toyama', 'HokurikuCity', 'Shirakawago');
        assert.ok(!('Nowhere' in at), 'a room with no town is not pulled anywhere');
    });

    test('studio: a second click on the selected cell picks the district underneath', () => {
        const stackPick = game('WorldModel.stackPick');
        const palace = { room: 'Palace', x: 38, y: 21 }, park = { room: 'Park', x: 38, y: 3 };
        const cells = [palace, park]; // bottom first: Park is drawn over Palace
        assert.strictEqual(stackPick(cells, null), park, 'the top district takes the first click');
        assert.strictEqual(stackPick(cells, { room: 'Park', x: 37, y: 3 }), park, 'a different cell selected: still the top');
        assert.strictEqual(stackPick(cells, { ...park }), palace, 'clicking the selected cell again reaches the covered seam transporter');
        assert.strictEqual(stackPick(cells, { ...palace }), park, 'and once more wraps back to the top');
        assert.strictEqual(stackPick([park], { ...park }), park, 'one room: the cell stays selected');
        assert.strictEqual(stackPick([], park), null, 'empty space selects nothing');
    });

    test("the editor's Spawn tool moves the trip home that decides where the game opens", () => {
        const Trips = game('Trips'), WorldModel = game('WorldModel');
        const room = (name) => ({ name, objects: [], npcs: [], layers: [], transporters: [
            { gridX: 0, gridY: 0, targetRoom: name === 'North' ? 'South' : 'North', targetX: 1, targetY: 1 }] });
        const config = () => ({
            game: { gridSize: 64, worldWidth: 256, worldHeight: 192 },
            player: { startRoom: 'North', startX: 1, startY: 1, sprite: 'bailey_front' },
            rooms: { North: room('North'), South: room('South') },
            trips: [
                { id: 'a', name: 'trip a', start: '2031-01-01', end: '2031-01-09', members: [], home: { room: 'North', x: 1, y: 1 },
                    stays: [{ from: '2031-01-01', room: 'North', x: 1, y: 1 }] },
                { id: 'b', start: '2032-01-01', end: '2032-01-09', members: [], home: { room: 'South', x: 2, y: 1 } },
            ],
        });
        const cfg = config();
        assert.deepStrictEqual(Array.from(Trips.moveStart(cfg, 'North', 2, 2)), ['trip a'], 'the trip that started on the old cell moves');
        assert.deepStrictEqual([cfg.player.startRoom, cfg.player.startX, cfg.player.startY], ['North', 2, 2]);
        assert.deepStrictEqual({ ...Trips.homeFor(cfg, '2031-01-02') }, { room: 'North', x: 2, y: 2 }, 'the game opens on the new cell (home and stay)');
        assert.deepStrictEqual({ ...Trips.homeFor(cfg, '2032-01-02') }, { room: 'South', x: 2, y: 1 }, 'a trip that starts elsewhere stays put');
        assert.deepStrictEqual(Array.from(Trips.moveStart(cfg, 'South', 2, 1)), ['trip a'], 'moving onto another trip\'s home does not claim it');
        assert.deepStrictEqual(Array.from(Trips.moveStart({ player: {}, rooms: {} }, 'North', 1, 1)), [], 'no trips: just the player start');

        // and the world check fails when the two drift apart (a hand edit of one of them)
        const drift = (c) => new WorldModel(c, { exists: () => true, sizeOf: () => [1, 1] }, { date: '2031-01-02' })
            .survey(['2031-01-02']).problems.filter(p => /is not player\.start/.test(p.text));
        assert.strictEqual(drift(config()).length, 0, 'in step');
        const apart = config();
        apart.player.startX = 2;
        assert.strictEqual(drift(apart).length, 1, 'player.start moved without the first trip');
        assert.strictEqual(drift(cfg).length, 0, 'the Spawn tool keeps them together');
    });
};
