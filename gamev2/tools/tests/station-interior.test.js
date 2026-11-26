// The station interiors (issue #206): one template in tools/generate_stations.py, checked here on
// every station of the shipped registry - including ones added after this file was written.
module.exports = ({ test, assert, fs, path, GV2, load, game, realConfig }) => {
    const K = (x, y) => x + ',' + y;
    // values from the game's vm realm compare by content (deepStrictEqual also compares prototypes)
    const plain = (v) => JSON.parse(JSON.stringify(v));
    const same = (a, b, msg) => assert.deepStrictEqual(plain(a), plain(b), msg);
    const SIZES = { small: { w: 24, h: 15, gates: 2 }, large: { w: 36, h: 20, gates: 4 } };
    const layer = (room, name) => (room.layers.find((l) => l.name === name) || { tiles: {} }).tiles;
    // the room as cells: what is solid, where a sprite family stands, what can be walked to from a cell
    const model = (room) => {
        const solid = new Set(Object.keys(layer(room, 'Colliders')));
        const w = room.worldWidth / 64, h = room.worldHeight / 64;
        const free = (x, y) => x >= 0 && y >= 0 && x < w && y < h && !solid.has(K(x, y));
        const where = (re) => room.layers.flatMap((l) => Object.entries(l.tiles || {})
            .filter(([, key]) => re.test(key)).map(([xy]) => xy.split(',').map(Number)));
        const reach = (from, blocked = new Set()) => {
            const seen = new Set([K(...from)]), queue = [from];
            while (queue.length) {
                const [x, y] = queue.shift();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    if (seen.has(K(nx, ny)) || !free(nx, ny) || blocked.has(K(nx, ny))) continue;
                    seen.add(K(nx, ny));
                    queue.push([nx, ny]);
                }
            }
            return seen;
        };
        return { w, h, free, where, reach };
    };
    const each = (fn) => {
        const config = realConfig();
        const keys = Object.keys(config.stations);
        assert.ok(keys.length >= 6, 'the registry lists the stations');
        for (const key of keys) fn(key, config.stations[key], config.rooms[key], model(config.rooms[key]), config);
    };

    test('a station is its size: small by default, the five city stations large, each with its row of gates (#206)', () => {
        each((key, st, room, m) => {
            const size = SIZES[st.size];
            assert.ok(size, `${key}: size "${st.size}" is not a station size`);
            same([m.w, m.h], [size.w, size.h], `${key} is not the size its registry entry says`);
            // the gate row is closed but for the gates, and the gates are side by side
            const gates = m.where(/^station-gate_/).map(([x, y]) => [x, y + 1]);    // a gate stands on the row below its tile
            assert.strictEqual(gates.length, size.gates, `${key}: gates`);
            const row = gates[0][1];
            const open = [];
            for (let x = 0; x < m.w; x++) if (m.free(x, row)) open.push(x);
            same(open, gates.map(([x]) => x).sort((a, b) => a - b), `${key}: the gate row is open only at the gates`);
            assert.strictEqual(open[open.length - 1] - open[0], open.length - 1, `${key}: the gates stand in one row`);
        });
        const { stations } = realConfig();
        for (const key of ['TokyoStation', 'OsakaStation', 'SendaiStation', 'SapporoStation', 'FukuokaStation']) assert.strictEqual(stations[key].size, 'large', key);
        for (const key of ['InakaStation', 'YukimuraStation', 'AsahikawaStation']) assert.strictEqual(stations[key].size, 'small', key);
    });

    test('the train contract: door cells on the track, the platform under them, the only way there through the gates (#206)', () => {
        each((key, st, room, m) => {
            const [tx, ty] = st.trainCell;
            assert.strictEqual(st.board.length, 2, `${key}: two doors`);
            // the doors of both liveries: one and eight cells along the ten-cell train, on its bottom row
            same(st.board, [[tx + 1, ty - 1], [tx + 8, ty - 1]], `${key}: board cells are the train's doors`);
            assert.ok(tx >= 1 && tx + 10 <= m.w - 1, `${key}: the train stands inside the room`);
            for (const [bx, by] of st.board) {
                assert.ok(m.free(bx, by), `${key}: door cell ${bx},${by} is walled`);
                assert.ok(m.free(bx, by + 1), `${key}: no platform under door ${bx}`);
                assert.strictEqual(layer(room, 'Over Floor')[K(bx, by)], 'station-track-s_0_0', `${key}: the door cell is on the track`);
                assert.strictEqual(layer(room, 'Floor')[K(bx, by + 1)], 'station-platform-edge_0_0', `${key}: you step off onto the platform edge`);
                assert.strictEqual(layer(room, 'Over Floor')[K(bx, by + 2)], 'station-door-mark_0_0', `${key}: the door is marked on the platform`);
            }
            // the rest of the track is solid: both rows, wall to wall
            for (let x = 0; x < m.w; x++) {
                for (const y of [ty - 2, ty - 1]) {
                    const door = st.board.some(([bx, by]) => bx === x && by === y);
                    assert.strictEqual(m.free(x, y), door, `${key}: track cell ${x},${y}`);
                    assert.ok(/^station-track-[ns]_/.test(layer(room, 'Over Floor')[K(x, y)]), `${key}: no rail at ${x},${y}`);
                }
            }
            // from where the town door puts you, both doors can be walked to - and not round the gates
            const from = m.reach(st.entry);
            for (const [bx, by] of st.board) assert.ok(from.has(K(bx, by)), `${key}: door ${bx},${by} cannot be walked to from ${st.entry}`);
            assert.ok(from.has(K(...st.arrive)), `${key}: arrive cell`);
            const gates = new Set(m.where(/^station-gate_/).map(([x, y]) => K(x, y + 1)));
            const round = m.reach(st.entry, gates);
            assert.ok(!st.board.some(([bx, by]) => round.has(K(bx, by))), `${key}: the platform can be reached without passing a gate`);
            assert.ok(st.arrive[1] < [...gates][0].split(',')[1], `${key}: arrive is on the platform side`);
        });
    });

    test('every station door works both ways: the town door lands on the entry cell, the exit beside the town door (#206)', () => {
        each((key, st, room, m, config) => {
            const town = config.rooms[st.town];
            assert.ok(town, `${key}: town ${st.town}`);
            assert.ok(m.free(...st.entry), `${key}: entry cell ${st.entry} is blocked`);
            const into = town.transporters.filter((t) => t.targetRoom === key);
            // an airport's rail stop (#218): its "town" is the airport hall, whose way out (two mats, like a
            // station's own) is the door, and the station's exit lands on the hall's entry cell
            const hall = (config.airports || {})[st.town];
            if (hall) {
                assert.strictEqual(into.length, 2, `${key}: the hall's two exit mats lead here`);
                for (const t of into) same([t.targetX, t.targetY], st.entry, `${key}: the hall's way out misses the entry cell`);
                const hallSolid = new Set(Object.keys(layer(town, 'Colliders')));
                assert.strictEqual(room.transporters.length, 2, `${key}: exit mats`);
                for (const t of room.transporters) {
                    same([t.targetRoom, t.targetX, t.targetY], [st.town, ...hall.entry], `${key}: exit target`);
                    assert.ok(!hallSolid.has(K(t.targetX, t.targetY)), `${key}: the exit lands on a blocked cell of ${st.town}`);
                    assert.ok(m.reach(st.entry).has(K(t.gridX, t.gridY)), `${key}: the exit cannot be walked to`);
                }
                same(into.map((t) => t.gridX).sort(), [hall.entry[0], hall.entry[0] + 1], `${key}: the hall's mats are below its entry cell`);
                return;
            }
            assert.strictEqual(into.length, 1, `${key}: one door in ${st.town}`);
            same([into[0].targetX, into[0].targetY], st.entry, `${key}: the town door misses the entry cell`);
            // the exit: two mats under the front wall, straight below the entry cell, out to the cell in front of the door
            const mats = room.transporters;
            assert.strictEqual(mats.length, 2, `${key}: exit mats`);
            same(mats.map((t) => [t.gridX, t.gridY]), [[st.entry[0], m.h - 1], [st.entry[0] + 1, m.h - 1]], `${key}: mats`);
            const townSolid = new Set(Object.keys(layer(town, 'Colliders')));
            for (const t of mats) {
                same([t.targetRoom, t.targetX, t.targetY], [st.town, into[0].gridX, into[0].gridY + 1], `${key}: exit target`);
                assert.ok(!townSolid.has(K(t.targetX, t.targetY)), `${key}: the exit lands on a blocked cell of ${st.town}`);
                assert.ok(m.reach(st.entry).has(K(t.gridX, t.gridY)), `${key}: the exit cannot be walked to`);
            }
            for (let y = st.entry[1]; y < m.h; y++) assert.ok(m.free(st.entry[0], y), `${key}: the way from the entry cell down to the exit is blocked at row ${y}`);
            assert.ok(!townSolid.has(K(into[0].gridX, into[0].gridY)), `${key}: the town door is sealed`);
        });
    });

    test('the in-station 7-Eleven kiosk is one booth whose counter sells the konbini list, bumped from the concourse (#206)', () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const Interactions = game('Interactions'), venues = game('Shop.VENUES');
        const sizeOf = (key) => (/^station-kiosk/.test(key) ? [4, 3] : [1, 1]);
        each((key, st, room, m, config) => {
            const roomConfig = config.rooms[key];
            assert.ok(!roomConfig.interior, `${key}: a station is not an interior (the blog pipeline and the night grade rely on it)`);
            const booths = m.where(/^station-kiosk/);
            assert.strictEqual(booths.length, 1, `${key}: one kiosk`);
            const [kx, ky] = booths[0];
            const from = m.reach(st.entry);
            for (let dx = 0; dx < 4; dx++) {
                for (let dy = 0; dy < 3; dy++) {
                    assert.ok(!m.free(kx + dx, ky + dy), `${key}: kiosk cell ${kx + dx},${ky + dy} can be walked into`);
                    const hit = Interactions.find(room, roomConfig, kx + dx, ky + dy, { sizeOf, venues, group: 'shop' });
                    same(hit && [hit.kind, hit.group], ['counter', 'shop'], `${key}: kiosk cell ${kx + dx},${ky + dy} sells nothing`);
                }
                assert.ok(from.has(K(kx + dx, ky + 3)), `${key}: the cell in front of the counter (${kx + dx},${ky + 3}) cannot be walked to from the door`);
            }
            // nothing else in the station became a shop by it: only the kiosk and the vending machines sell
            const kinds = new Set(Interactions.all(room, roomConfig, { sizeOf, venues, group: 'shop' }).map((i) => i.kind));
            same([...kinds].sort(), ['counter', 'vending'], key);
        });
        // the rule is the kiosk's own: a konbini counter still sells only inside a konbini
        assert.strictEqual(Interactions.match('office-counter_0_0', {}, venues), null);
        assert.strictEqual(Interactions.match('station-kiosk_0_0', {}, venues).kind, 'counter');
        assert.strictEqual(game('Shop.VENUES').counter.buys, true, 'the kiosk buys your catch like any konbini till');
    });

    test('a station keeps the west end of its platform for the blog cast, by its one white vending machine (#206, #73)', () => {
        each((key, st, room, m) => {
            same(m.where(/^white-vending-machine-top/), [[2, 6]], `${key}: the platform's white machine`);
            const from = m.reach(st.entry);
            for (const [x, y] of [[1, 5], [1, 6], [1, 7], [2, 5], [0, 6], [2, 8]]) {
                assert.ok(from.has(K(x, y)), `${key}: ${x},${y} at the west end of the platform cannot be stood on`);
            }
            // nobody stood there is under a hanging sign
            const tops = Object.keys(layer(room, 'Tops')).map((xy) => xy.split(',').map(Number));
            assert.ok(!tops.some(([x]) => x <= 3), `${key}: a sign hangs over the west end`);
        });
    });

    test('every station is signed: name boards drawn for it, the departures board, the exit, a clock, benches (#206)', () => {
        const art = (key) => fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
        const ja = { TokyoStation: '東京', OsakaStation: '大阪', SapporoStation: '札幌', AsahikawaStation: '旭川', InakaStation: 'いなか', YukimuraStation: '雪村', SendaiStation: '仙台', FukuokaStation: '博多' };
        each((key, st, room, m, config) => {
            const board = `station-name-${key.replace(/Station$/, '').toLowerCase()}_0_0`;
            assert.ok(art(board), `${key}: no name board art (${board}) - run tools/generate_station_art.py`);
            assert.ok(config.spriteMetadata[board], `${key}: ${board} is not registered`);
            const boards = m.where(/^station-name-/);
            assert.ok(boards.length >= 2, `${key}: name boards`);
            const others = room.layers.flatMap((l) => Object.values(l.tiles || {})).filter((k) => /^station-name-/.test(k) && k !== board);
            same(others, [], `${key} shows another station's name`);
            // clear of the parked train (ten cells from trainCell), so they can be read
            for (const [x] of boards) assert.ok(x + 2 < st.trainCell[0] || x > st.trainCell[0] + 10, `${key}: a name board at ${x} is behind the train`);
            for (const [re, what] of [[/^station-departures/, 'departures board'], [/^station-exit-sign/, 'exit sign'], [/^station-clock/, 'clock'],
                [/^station-bench/, 'bench'], [/^station-ticket-machines/, 'ticket machines'], [/^station-lamp-post/, 'platform lamp'],
                [/^station-tactile-/, 'tactile path'], [/^(red|white)-vending-machine-top/, 'vending machine']]) {
                assert.ok(m.where(re).length >= 1, `${key}: no ${what}`);
            }
            if (ja[key]) assert.strictEqual(st.ja, ja[key], `${key}: Japanese name`);
            // the wall is in the line's colour: orange main line, green branch
            const wall = layer(room, 'Collidables')['0,0'];
            assert.strictEqual(wall, st.train === 'train-green' ? 'station-wall-green_0_0' : 'station-wall-orange_0_0', `${key}: wall`);
            // none of the old placeholder platform is left
            const old = room.layers.flatMap((l) => Object.values(l.tiles || {})).filter((k) => /^(train-track|castle-wall|pavers|blue-shrine-platform|light-concrete|gravel-autotile)/.test(k));
            same(old, [], `${key}: old platform tiles`);
        });
    });
};
