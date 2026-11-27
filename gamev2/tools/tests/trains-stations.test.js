module.exports = ({ test, assert, fs, path, vm, GV2, game }) => {
    test('a station parks its own train, and keeps the one you rode in on', () => {
        const liveryFor = game('TrainTravel.liveryFor');
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        for (const st of Object.values(stations)) assert.strictEqual(liveryFor(st, null), st.train);
        assert.strictEqual(liveryFor(stations.AsahikawaStation, 'train-orange'), 'train-orange');
    });

    test('the departures board is ordered from data, groups day trips, and starts somewhere sensible', () => {
        const board = game('StationPicker.board');
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        const show = (from, cameFrom) => {
            const b = board(stations, from, cameFrom);
            // Array.from: rows come from the vm realm, deepStrictEqual compares prototypes
            return Array.from(b.rows, (r, i) => (i === b.selected ? '>' : '') + '  '.repeat(r.indent) + r.label + (r.here ? ' (here)' : ''));
        };
        // the real registry: in line order, day trips under their city, never alphabetical. Tokyo has no day
        // trips since the made-up towns went (#68), so its own board has no "(here)" heading: Sapporo's still does
        assert.deepStrictEqual(show('TokyoStation'),
            ['>Haneda Airport', 'Kanazawa', 'Osaka', 'Sendai', 'Sapporo', '  Asahikawa', 'Hakata']);
        assert.deepStrictEqual(show('OsakaStation'),
            ['>Tokyo Station', 'Haneda Airport', 'Kanazawa', 'Sendai', 'Sapporo', '  Asahikawa', 'Hakata']);
        // a day-trip station starts on its city; the way you came wins over that
        assert.deepStrictEqual(show('AsahikawaStation'),
            ['Tokyo Station', 'Haneda Airport', 'Kanazawa', 'Osaka', 'Sendai', '>Sapporo', 'Hakata']);
        assert.deepStrictEqual(show('AsahikawaStation', 'OsakaStation'),
            ['Tokyo Station', 'Haneda Airport', 'Kanazawa', '>Osaka', 'Sendai', 'Sapporo', 'Hakata']);
        assert.deepStrictEqual(show('SapporoStation', 'TokyoStation'),
            ['>Tokyo Station', 'Haneda Airport', 'Kanazawa', 'Osaka', 'Sendai', 'Sapporo (here)', '  Asahikawa', 'Hakata']);
        // Kanazawa (#68) stands between Tokyo's side of the line (Haneda Airport, #218) and Osaka; from it the board starts on Tokyo
        assert.deepStrictEqual(show('KanazawaStation'),
            ['>Tokyo Station', 'Haneda Airport', 'Osaka', 'Sendai', 'Sapporo', '  Asahikawa', 'Hakata']);
        // where you came from is ignored when it is where you are, or not a station
        assert.strictEqual(board(stations, 'TokyoStation', 'TokyoStation').selected, 0);
        assert.strictEqual(board(stations, 'TokyoStation', 'Nowhere').selected, 0);

        // every station is on every board exactly once, and the heading is never the selection
        assert.ok(!Object.keys(stations).some(k => /Inaka|Yukimura/.test(k + stations[k].label + stations[k].town)), 'a made-up town is still a stop');
        for (const from of Object.keys(stations)) {
            const b = board(stations, from, null);
            const dests = Array.from(b.rows).filter(r => !r.here).map(r => r.key).sort();
            assert.deepStrictEqual(dests, Object.keys(stations).filter(k => k !== from).sort(), from);
            assert.ok(b.selected >= 0 && !b.rows[b.selected].here, from);
        }

        // no order / parent fields: a stable alphabetical-by-label board, as flat cities
        const bare = { B: { label: 'Beta' }, A: { label: 'alpha' }, C: { label: 'Gamma' } };
        assert.deepStrictEqual(Array.from(board(bare, 'C').rows, r => r.key), ['A', 'B']);
        // bad parents (unknown, itself, a cycle, a day trip of a day trip) never hide a station
        const odd = {
            A: { label: 'A', order: 0 }, B: { label: 'B', order: 1, parent: 'Nope' },
            C: { label: 'C', order: 2, parent: 'C' }, D: { label: 'D', order: 3, parent: 'E' },
            E: { label: 'E', order: 4, parent: 'D' }, F: { label: 'F', order: 5, parent: 'A' },
            G: { label: 'G', order: 6, parent: 'F' },
        };
        assert.deepStrictEqual(Array.from(board(odd, 'X').rows, r => r.key + r.indent),
            ['A0', 'F1', 'B0', 'C0', 'D0', 'E0', 'G0']);
        // nowhere to go
        assert.strictEqual(board({ A: { label: 'A' } }, 'A').selected, -1);
        assert.strictEqual(board(undefined, 'A').selected, -1);
    });

    test('the departures board skips its heading and scrolls to keep the selection in view', () => {
        const step = game('StationPicker.step'), scrollTop = game('StationPicker.scrollTop');
        const rows = [{ here: true }, { indent: 1 }, { indent: 1 }, {}, {}, { indent: 1 }];
        assert.strictEqual(step(rows, 1, -1), 5, 'up from the first destination wraps past the heading');
        assert.strictEqual(step(rows, 5, 1), 1);
        assert.strictEqual(step(rows, 2, 1), 3);
        assert.strictEqual(step([{}], 0, 1), 0);

        assert.strictEqual(scrollTop(0, 3, 6, 7), 0, 'a board that fits never scrolls');
        assert.strictEqual(scrollTop(0, 9, 14, 7), 3, 'down: the selection becomes the last row shown');
        assert.strictEqual(scrollTop(3, 5, 14, 7), 3, 'moving inside the window leaves it alone');
        assert.strictEqual(scrollTop(5, 4, 14, 7), 4, 'up: the selection becomes the first row shown');
        assert.strictEqual(scrollTop(5, 13, 14, 7), 7);
        assert.strictEqual(scrollTop(99, 13, 14, 7), 7, 'clamped to the end');
        assert.strictEqual(scrollTop(5, 1, 14, 7, rows), 0, 'a day trip brings its heading into view');
        assert.strictEqual(scrollTop(5, 2, 14, 7, rows), 0, 'the second trip of a city brings the city too, not its sibling');
        assert.strictEqual(scrollTop(1, 1, 14, 7, rows), 0, 'also when the trip is already the first row shown');
        assert.strictEqual(scrollTop(5, 5, 14, 7, rows), 4);
        assert.strictEqual(scrollTop(5, 4, 14, 7, rows), 4, 'a city needs nothing above it');
        const many = [{}].concat(Array(9).fill({ indent: 1 }));
        assert.strictEqual(scrollTop(9, 8, 10, 3, many), 7, 'a city too far up to fit is left behind');

        // scrolled by wheel / arrows / drag: the selection may not be left off screen
        const clamp = game('StationPicker.clampSelection');
        const long = [{ here: true }, { indent: 1 }, {}, {}, {}, {}, {}, {}, {}, {}];
        assert.strictEqual(clamp(long, 3, 0, 7), 3, 'still in view: unchanged');
        assert.strictEqual(clamp(long, 1, 3, 7), 3, 'scrolled past it: the first row shown');
        assert.strictEqual(clamp(long, 9, 0, 7), 6, 'scrolled back above it: the last row shown');
        assert.strictEqual(clamp(long, 9, 0, 1), 9, 'nothing selectable in view: left alone');
        assert.strictEqual(clamp(long, 8, 0, 2), 1, 'never the heading');
    });

    test('a train ride remembers where it came from, for the board at the other end', () => {
        const travel = game('Object.create(TrainTravel.prototype)');
        travel.lastRide = null;
        assert.strictEqual(travel.cameFrom('SapporoStation'), null);
        travel.lastRide = { from: 'TokyoStation', to: 'SapporoStation' };
        assert.strictEqual(travel.cameFrom('SapporoStation'), 'TokyoStation');
        assert.strictEqual(travel.cameFrom('OsakaStation'), null);
    });

    test('you step off by the door you boarded by, wherever the destination parks its train (#206)', () => {
        const exitDoor = game('TrainTravel.exitDoor');
        const small = { board: [[8, 3], [15, 3]] }, large = { board: [[14, 3], [21, 3]] };
        assert.strictEqual(exitDoor(small, small, 15), 15, 'same size: the same column, as before');
        assert.strictEqual(exitDoor(small, large, 8), 14, 'first door to first door');
        assert.strictEqual(exitDoor(small, large, 15), 21);
        assert.strictEqual(exitDoor(large, small, 21), 15);
        assert.strictEqual(exitDoor(large, small, 20), 15, 'not on a door: the nearest one');
        assert.strictEqual(exitDoor(large, {}, 21), 21, 'a destination with no doors listed: unchanged');
        // the real registry: from every door of every station, every destination's cell is one of its own doors
        const stations = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).stations;
        for (const [a, from] of Object.entries(stations)) {
            for (const [b, to] of Object.entries(stations)) {
                from.board.forEach(([x], i) => assert.strictEqual(exitDoor(from, to, x), to.board[i][0], `${a} door ${i} -> ${b}`));
            }
        }
    });

    test('the train-ride cutscene is magnified with the world, never past the height of the view', () => {
        const scale = game('TrainTravel.cutsceneScale');
        assert.strictEqual(scale(1, 960, 480), 1, 'desktop: as authored');
        assert.strictEqual(scale(undefined, 960, 480), 1, 'no UIScale: as authored');
        assert.strictEqual(scale(1.5, 960, 480), 1.5, 'tablet: as far as the world is zoomed');
        assert.strictEqual(scale(2, 960, 480), 2, 'landscape phone: the car fills the height');
        assert.strictEqual(scale(2, 960, 600), 1.6, 'a taller car stops at the height of the view');
        assert.strictEqual(scale(2, 400, 480), 1, 'never shrunk');
    });
};
