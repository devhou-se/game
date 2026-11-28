module.exports = ({ test, assert, fs, path, GV2, load, game, worldWith }) => {
    test('a road over a train track is an open level crossing, in every room', () => {
        // tools/seal_tracks.py leaves a track cell with a road under it unsealed; Palace has two (#138)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const sealed = [], crossings = {};
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const layer = (n) => ((room.layers || []).find((l) => l.name === n) || {}).tiles || {};
            const floor = layer('Floor'), colliders = layer('Colliders');
            for (const l of room.layers || []) {
                for (const [xy, t] of Object.entries(l.tiles || {})) {
                    if (!name(t).startsWith('train-track') || !name(floor[xy]).startsWith('road-')) continue;
                    (crossings[key] = crossings[key] || []).push(xy);
                    if (xy in colliders) sealed.push(`${key} @${xy}`);
                }
            }
        }
        assert.deepStrictEqual(sealed, []);
        assert.deepStrictEqual(crossings.Palace.sort(), ['0,3', '1,3', '54,3', '55,3', '56,3'], 'west and east roads cross the track');
    });

    test('Osaka: both pavements pass the signal posts at the bridgehead without the road', () => {
        // the posts stand on the kerb at (22,19) and (27,19); the bridge pavement is two cells wide round them (#139)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const layer = (n) => (cfg.rooms.Osaka.layers.find((l) => l.name === n) || {}).tiles || {};
        const floor = layer('Floor'), colliders = layer('Colliders');
        const open = (xy) => xy in floor && !(xy in colliders) && !name(floor[xy]).startsWith('road-');
        const reach = (from, to) => {
            const seen = new Set([from]), todo = [from];
            while (todo.length) {
                const [x, y] = todo.pop().split(',').map(Number);
                if (y < 17 || y > 23) continue;                    // round the post, not round the town
                for (const n of [`${x + 1},${y}`, `${x - 1},${y}`, `${x},${y + 1}`, `${x},${y - 1}`]) {
                    if (open(n) && !seen.has(n)) { seen.add(n); todo.push(n); }
                }
            }
            return seen.has(to);
        };
        for (const x of [22, 27]) {
            assert.ok(`${x},19` in colliders, `signal post base at ${x},19`);
            assert.ok(reach(`${x},18`, `${x},22`), `pavement at column ${x} is cut off by its signal post`);
        }
    });

    test('Osaka: the ferris wheel is two legs and a ring, with nothing drawn or solid between the legs (#241)', () => {
        // the sheet parks a loose 2x1 tile in the gap, against the left leg: extract_dotonbori.py clears it (CLEAR),
        // and the prefab no longer makes those two cells solid
        const png = require(path.join(GV2, 'tools', 'png.js'));
        const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'dotonbori-wheel_0_0.png')));
        assert.deepStrictEqual([width, height], [768, 768]);
        const opaque = (col, row) => {
            let n = 0;
            for (let y = row * 64; y < row * 64 + 64; y++) for (let x = col * 64; x < col * 64 + 64; x++) if (data[(y * width + x) * 4 + 3]) n++;
            return n;
        };
        for (let row = 4; row < 12; row++) {
            for (let col = 4; col < 8; col++) assert.strictEqual(opaque(col, row), 0, `sprite cell ${col},${row} between the legs is not empty`);
            for (const col of [2, 3, 8, 9]) assert.ok(opaque(col, row) > 1024, `sprite cell ${col},${row}: the leg is gone`);
        }
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const layer = (n) => (cfg.rooms.Osaka.layers.find((l) => l.name === n) || {}).tiles || {};
        const at = Object.keys(layer('Collidables')).filter((xy) => name(layer('Collidables')[xy]) === 'dotonbori-wheel_0_0');
        assert.strictEqual(at.length, 1, 'one wheel in Osaka');
        const [wx, wy] = at[0].split(',').map(Number), colliders = layer('Colliders'), solid = [];
        for (let dy = 0; dy < 12; dy++) for (let dx = 0; dx < 12; dx++) if (`${wx + dx},${wy + dy}` in colliders) solid.push(`${dx},${dy}`);
        const legs = [];
        for (let dy = 9; dy < 12; dy++) for (const dx of [2, 3, 8, 9]) legs.push(`${dx},${dy}`);
        // ...and the gondola you board (#242), which stands outside the legs, under the three on the wheel's west side
        const boarding = Object.keys(layer('Collidables')).filter((xy) => name(layer('Collidables')[xy]) === 'wheel-boarding_0_0');
        assert.deepStrictEqual(boarding, [`${wx},${wy + 10}`], 'one gondola to board, at the foot of the west side');
        const gondola = ['0,10', '0,11', '1,10', '1,11'];
        assert.deepStrictEqual(solid.sort(), legs.concat(gondola).sort(), 'only the feet of the two legs and the boarding gondola are solid');
        for (let dy = 0; dy < 12; dy++) for (let dx = 4; dx < 8; dx++) assert.ok(!solid.includes(`${dx},${dy}`), `cell ${dx},${dy} between the legs is solid`);
    });

    test('Osaka: the canal is a declared waterway, open water except under the bridge, and the streets have centre lines', () => {
        // #61: AmbientBoats sails the room's `waterways`; #151: the four-cell street's line is the lane pair's shared edge
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const room = cfg.rooms.Osaka;
        const layer = (n) => (room.layers.find((l) => l.name === n) || {}).tiles || {};
        const floor = layer('Floor'), water = layer('Water'), colliders = layer('Colliders');
        assert.strictEqual(room.waterways.length, 1);
        const w = room.waterways[0];
        assert.deepStrictEqual([w.axis, w.from, w.to], ['h', 0, room.worldWidth / 64 - 1], 'the canal runs edge to edge');
        const under = (x) => w.under.some(([a, b]) => x >= a && x <= b);
        for (let x = w.from; x <= w.to; x++) {
            for (let y = w.row; y < w.row + w.rows; y++) {
                const xy = `${x},${y}`;
                if (under(x)) {
                    assert.ok(!(xy in water) && !(xy in colliders), `bridge deck cell ${xy} is walkable paving, not water`);
                } else {
                    assert.ok(name(water[xy]).startsWith('pond-autotile_') && xy in colliders, `canal cell ${xy} is solid water`);
                    assert.ok(!/corner|edge-[ew]/.test(name(water[xy])), `canal cell ${xy} is an end cap: the channel is not open`);
                }
            }
        }
        const rows = Object.keys(floor).filter((xy) => name(floor[xy]) === 'road-lane-left_0_0').map((xy) => xy.split(',').map(Number));
        assert.ok(rows.length >= 12, 'the main street is a street, not a stub');
        for (const [x, y] of rows) {
            assert.deepStrictEqual([name(floor[`${x - 1},${y}`]), name(floor[`${x + 1},${y}`]), name(floor[`${x + 2},${y}`])],
                ['road-edge-left_0_0', 'road-lane-right_0_0', 'road-edge-right_0_0'], `street row ${y}: kerb, lane | lane, kerb`);
        }
        const lines = Object.keys(floor).filter((xy) => name(floor[xy]) === 'road-div-horizontal_0_0').map((xy) => Number(xy.split(',')[0]));
        assert.ok(lines.includes(0) && lines.includes(room.worldWidth / 64 - 1), 'the avenue leaves town at both edges');
        for (const key of ['road-lane-left_0_0', 'road-lane-right_0_0', 'road-corner-nw_0_0', 'road-corner-ne_0_0', 'road-corner-sw_0_0']) {
            assert.ok(key in cfg.spriteMetadata && fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), `${key} is loadable`);
        }
    });

    test('a boat is picked to fit the water left in view, and is cut off at a bridge deck', () => {
        // #62: the north moat shows a 32px lane above the palace wall - skiff only; #61: `under` spans hide the boat
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');   // once: the tests below use it too
        const boats = game('Object.create(AmbientBoats.prototype)');
        const run = (width, length) => boats.fit({ axis: 'h', from: 0, to: length, band0: 100, band1: 100 + width });
        assert.deepStrictEqual(Array.from(run(50, 400).hulls), ['punt', 'skiff']);
        assert.deepStrictEqual(Array.from(run(32, 400).hulls), ['skiff'], 'a narrow lane takes the skiff');
        assert.strictEqual(run(24, 400), null, 'no boat is squeezed into less water than its beam');
        assert.strictEqual(run(50, 150), null, 'nor into a run it could not travel along');
        for (const livery of Object.keys(game('AmbientBoats.LIVERIES'))) {
            assert.ok(game('AmbientBoats.HULLS')[game('AmbientBoats.hullOf')(livery)], `${livery} is painted on a known hull`);
        }
        const boat = { width: 116, height: 44, visible: true, crop: null,
            setVisible(v) { this.visible = v; }, setCrop(x, y, w, h) { this.crop = [x, y, w, h]; } };
        const deck = { axis: 'h', under: [[1000, 1500]] };
        boats.hideUnder(boat, deck, 500, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [0, 0, 116, 44]], 'clear of the bridge: drawn whole');
        boats.hideUnder(boat, deck, 990, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [0, 0, 68, 44]], 'bow under the deck: cut at its edge');
        boats.hideUnder(boat, deck, 1250, 116);
        assert.strictEqual(boat.visible, false, 'wholly under the deck: not drawn');
        boats.hideUnder(boat, deck, 1520, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [38, 0, 78, 44]], 'stern still under the deck');
    });

    test('the placeholder boat art: every livery is drawn whole in all four facings, at the size the runs are fitted to (#60)', () => {
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');
        const A = game('AmbientBoats'), plain = (v) => JSON.parse(JSON.stringify(v));
        // hand-drawn sprites are to drop in at these sizes, and fit() measures the water with them
        assert.deepStrictEqual(plain([A.size('punt'), A.size('skiff')]), [{ along: 116, across: 44 }, { along: 80, across: 28 }]);
        const PX = A.ART.PX, crew = 'cHhgfjnp';   // the boatman and his oar, in the hull pictures
        for (const [name, hull] of Object.entries(plain(A.HULLS))) {
            const { along, across } = A.size(name);
            for (const view of ['side', 'down', 'up']) {
                const [w, h] = view === 'side' ? [along, across] : [across, along];
                assert.strictEqual(hull[view].length * PX, h, `${name} ${view}: height`);
                hull[view].forEach((row, y) => assert.strictEqual(row.length * PX, w, `${name} ${view}: row ${y} is as wide as the rest`));
                assert.ok(hull[view].some((row) => /[c]/.test(row)), `${name} ${view}: someone is sculling it`);
            }
        }
        for (const [part, art] of Object.entries(plain(A.ABOARD))) {
            for (const [view, rows] of Object.entries(art)) {
                rows.forEach((row) => assert.strictEqual(row.length, rows[0].length, `${part} ${view}: rows of one width`));
            }
            assert.ok(art.side && art.down, `${part} is drawn from the side and from the front`);
        }
        for (const [livery, pal] of Object.entries(plain(A.LIVERIES))) {
            const name = A.hullOf(livery), hull = plain(A.HULLS[name]), { along, across } = A.size(name);
            for (const [part, station] of pal.aboard || []) {
                assert.ok(A.ABOARD[part], `${livery} carries a known part (${part})`);
                assert.ok(Number.isInteger(station), `${livery}: ${part} has a station`);
            }
            const bare = Object.assign({}, pal, { aboard: [] });
            for (const facing of ['right', 'left', 'down', 'up']) {
                const rows = plain(A.pixels(livery, facing)), view = facing === 'down' || facing === 'up' ? facing : 'side';
                const [w, h] = view === 'side' ? [along, across] : [across, along];
                assert.strictEqual(rows.length * PX, h, `${livery} ${facing}: height`);
                rows.forEach((row) => {
                    assert.strictEqual(row.length * PX, w, `${livery} ${facing}: width`);
                    // a letter with no colour would be painted as its own name
                    row.forEach((colour) => assert.ok(colour === null || /^(#[0-9a-f]{6}|rgba\([\d.,]+\))$/.test(colour), `${livery} ${facing}: ${colour} is a colour`));
                });
                // what is aboard is drawn on the hull, and never over the boatman
                A.LIVERIES.__bare = bare;
                let empty;
                try { empty = plain(A.pixels('__bare', facing)); } finally { delete A.LIVERIES.__bare; }
                const picture = facing === 'left' ? hull[view].map((row) => Array.from(row).reverse().join('')) : hull[view];
                picture.forEach((row, y) => Array.from(row, (ch, x) => {
                    if (crew.includes(ch)) assert.strictEqual(rows[y][x], empty[y][x], `${livery} ${facing}: the boatman is in view at ${x},${y}`);
                }));
                if ((pal.aboard || []).length) assert.notDeepStrictEqual(rows, empty, `${livery} ${facing}: what it carries is drawn`);
            }
            assert.deepStrictEqual(plain(A.pixels(livery, 'left')), plain(A.pixels(livery, 'right')).map((row) => row.reverse()),
                `${livery}: sailing left is sailing right mirrored`);
        }
    });

    test('declared waterways that meet end to end are one run: a canal carried on by the next district sails as one (#68)', () => {
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');
        const A = game('AmbientBoats'), plain = (v) => JSON.parse(JSON.stringify(v));
        const across = Math.min(...Object.keys(A.HULLS).map((h) => A.size(h).across));
        assert.strictEqual(across, A.size('skiff').across, 'the narrowest hull is the skiff');
        const run = (from, to, more) => Object.assign({ axis: 'h', from, to, band0: 1300, band1: 1360, under: [], open: [false, false] }, more);
        // two that abut: the first's start, the second's end, both lists of bridges, and one end open each
        const west = run(0, 640, { open: [true, false], under: [[128, 256]] }), east = run(640, 1920, { open: [false, true], under: [[1280, 1408]] });
        const before = plain([west, east]);
        assert.deepStrictEqual(plain(A.joinRuns([west, east])),
            [{ axis: 'h', from: 0, to: 1920, band0: 1300, band1: 1360, under: [[128, 256], [1280, 1408]], open: [true, true] }]);
        assert.deepStrictEqual(plain([west, east]), before, 'the runs given are left as they were');
        // ...in whichever order the districts list them, and the joined run stands where its first part stood
        const moat = run(0, 640, { axis: 'v', band0: 64, band1: 128 });
        assert.deepStrictEqual(plain(A.joinRuns([east, moat, west])),
            [plain(moat), { axis: 'h', from: 0, to: 1920, band0: 1300, band1: 1360, under: [[128, 256], [1280, 1408]], open: [true, true] }]);
        // three in a row are one, and the ends that met in the middle are not open
        const three = A.joinRuns([run(640, 1280, { open: [true, true] }), run(1280, 1920), run(0, 640, { open: [true, false] })]);
        assert.deepStrictEqual(plain(three.map((r) => [r.from, r.to, r.open])), [[0, 1920, [true, false]]]);
        // each district measures its own band, so a few pixels of bank may differ: the joined band is the water both have
        const banks = A.joinRuns([run(0, 640, { band0: 1296, band1: 1356 }), run(640, 1280, { band0: 1300, band1: 1364 })]);
        assert.deepStrictEqual(plain(banks.map((r) => [r.from, r.to, r.band0, r.band1])), [[0, 1280, 1300, 1356]]);
        // the narrowest boat must fit the water they share: exactly its width joins, a pixel less does not
        const offset = (by) => [run(0, 640), run(640, 1280, { band0: 1360 - by, band1: 1420 - by })];
        assert.strictEqual(A.joinRuns(offset(across)).length, 1);
        assert.deepStrictEqual(plain(A.joinRuns(offset(across - 1))), plain(offset(across - 1)), 'too little water in common');
        assert.strictEqual(A.joinRuns(offset(across - 1), across - 1).length, 1, 'the width asked for is the one given');
        // nothing else joins, and a list where nothing joins comes back as it was
        for (const [why, apart] of [['a gap between them', [run(0, 640), run(704, 1280)]], ['they overlap', [run(0, 704), run(640, 1280)]],
            ['one is across the other', [run(0, 640), run(640, 1280, { axis: 'v' })]],
            ['side by side', [run(0, 640), run(0, 640, { band0: 1400, band1: 1460 })]], ['one run', [run(0, 640)]], ['none', []]]) {
            assert.deepStrictEqual(plain(A.joinRuns(apart)), plain(apart), why);
        }
        // a run with no `under` or `open` of its own (as fit() is given in the test above) joins too
        const bare = A.joinRuns([{ axis: 'v', from: 0, to: 320, band0: 0, band1: 64 }, { axis: 'v', from: 320, to: 640, band0: 0, band1: 64 }]);
        assert.deepStrictEqual(plain(bare), [{ axis: 'v', from: 0, to: 640, band0: 0, band1: 64, open: [false, false], under: [] }]);
    });

    test('the only waterways declared today that meet end to end are Himeji\'s moat, Osaka\'s canal and Nara\'s river, which sail as one run; every other boat sails the run it sailed (#68, #255, #268)', () => {
        // what "joining changes nothing else today" rests on: cells, each district's moved by its place in its city
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const inCity = {};
        for (const city of Object.values(cfg.cities)) for (const m of city.rooms) inCity[m.room] = m;
        const groups = {};
        let declared = 0;
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const m = inCity[key] || { x: 0, y: 0 }, group = Object.keys(cfg.cities).find((c) => cfg.cities[c].rooms.includes(inCity[key])) || key;
            for (const w of room.waterways || []) {
                const h = w.axis !== 'v', off = h ? m.x : m.y, cross = h ? w.row + m.y : w.col + m.x;
                (groups[group] = groups[group] || []).push({ key, axis: h ? 'h' : 'v', from: w.from + off, to: w.to + 1 + off, band0: cross, band1: cross + ((h ? w.rows : w.cols) || 1) });
                declared++;
            }
        }
        assert.ok(declared >= 5, 'the canals of Osaka and Fukuoka, the moat at Himeji, the bay at Sendai and the sea at Toyama are declared');
        const meet = [];
        for (const [group, runs] of Object.entries(groups)) {
            let met = 0;
            for (const a of runs) for (const b of runs) {
                if (a === b || a.axis !== b.axis || a.to !== b.from) continue;
                if (Math.min(a.band1, b.band1) <= Math.max(a.band0, b.band0)) continue;
                meet.push(`${group}: ${a.key}'s waterway is carried on by ${b.key}'s`);
                met++;
            }
            // ...which is what joinRuns makes of them (here in cells: one cell in common would join them)
            assert.strictEqual(game('AmbientBoats').joinRuns(runs, 1).length, runs.length - met, group);
        }
        // Osaka's canal runs on west as the castle moat (#255): the same three rows either side of the seam
        // ...and on east as Nara's river (#268)
        assert.deepStrictEqual(meet, ["KansaiCity: Himeji's waterway is carried on by Osaka's", "KansaiCity: Osaka's waterway is carried on by Nara's"]);
        const run = (key) => groups.KansaiCity.find((r) => r.key === key);
        const moat = run('Himeji'), canal = run('Osaka'), river = run('Nara');
        assert.strictEqual(groups.KansaiCity.length, 3);
        assert.deepStrictEqual([moat.band0, moat.band1, river.band0, river.band1], [canal.band0, canal.band1, canal.band0, canal.band1]);
        const [one] = game('AmbientBoats').joinRuns(groups.KansaiCity, 1);
        assert.deepStrictEqual([one.from, one.to, one.band0, one.band1], [moat.from, river.to, canal.band0, canal.band1]);
    });

    test("Tokyo's west gate leads to Karuizawa: the fence e3cb4d0d ran across it is open again, two cells wide (#68, #260)", () => {
        // #147 paved a two-cell gate here for the lane from Machi; with that town gone #68 fenced the gap, and
        // #260 opened it again for the road to Karuizawa (tools/generate_karuizawa.py owns the two cells)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const tiles = (room, n) => (cfg.rooms[room].layers.find((l) => l.name === n) || {}).tiles || {};
        assert.ok(!('Machi' in cfg.rooms) && !cfg.cities.TokyoCity.rooms.some((m) => m.room === 'Machi'));
        assert.deepStrictEqual(cfg.rooms.Tokyo.transporters.filter((t) => t.gridX === 0), [41, 42].map((y) => (
            { gridX: 0, gridY: y, targetRoom: 'Karuizawa', targetX: 44, targetY: y - 7, hidden: true })), 'the only doors in the west edge');
        for (const y of [40, 43]) {
            assert.strictEqual(name(tiles('Tokyo', 'Collidables')[`0,${y}`]), 'fence-barriers_0_2', `the fence at 0,${y}`);
            assert.ok(`0,${y}` in tiles('Tokyo', 'Colliders'), `0,${y} is solid`);
            assert.strictEqual(name(tiles('Tokyo', 'Floor')[`0,${y}`]), 'flat-grey-brick-autotile_edge-w');
        }
        for (const y of [41, 42]) {
            assert.strictEqual(name(tiles('Tokyo', 'Floor')[`0,${y}`]), 'flat-grey-brick-autotile_center', `the gate at 0,${y} is plain brick`);
            assert.ok(!(`0,${y}` in tiles('Tokyo', 'Collidables')) && !(`0,${y}` in tiles('Tokyo', 'Colliders')), `0,${y} is fenced`);
            assert.ok(!(`1,${y}` in tiles('Tokyo', 'Colliders')), 'the pavement inside the fence is still walked on');
            assert.ok(name(tiles('Tokyo', 'Floor')[`2,${y}`]).startsWith('road-edge-left'), 'the road keeps its kerb');
        }
        assert.strictEqual(name(tiles('Tokyo', 'Floor')['2,43']), 'road-corner-sw_0_0', 'the junction box has its corner');
        // stitched or not, the gate is the only way off the west edge of the district
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager;
            if (!stitch) world.enter('Tokyo', 1, 41);
            const open = [];
            for (let y = 0; y < 46; y++) {
                const at = stitch ? rm.resolve('Tokyo', 0, y) : { x: 1, y };   // stitched: off column 0; not: onto it, where the doors are
                if (world.canStep(at.x, at.y, at.x - 1, at.y)) open.push(y);
            }
            assert.deepStrictEqual(open, [41, 42], stitch ? 'stitched' : '?stitch=0');
            if (stitch) assert.strictEqual(rm.resolve('Tokyo', 0, 0).x, 48, 'Karuizawa is west of Tokyo: the city starts 48 columns before it');
        }
    });

    test('road junctions are plain boxes: no kerb across a joining road, no centre line through one (#179)', () => {
        const { world } = worldWith(true);
        const city = world.roomManager.rooms.TokyoCity;
        const road = {};
        for (const layer of city.layers) {
            if (layer.z >= 2 || layer.collision) continue;
            for (const [xy, key] of Object.entries(layer.tiles)) if (/^road-/.test(key)) road[xy] = key.replace(/_0_0$/, '');
        }
        const at = (x, y) => road[`${x},${y}`] || '';
        const bad = [];
        let lines = 0;
        for (const xy of Object.keys(road)) {
            const [x, y] = xy.split(',').map(Number), t = road[xy];
            if (t === 'road-div-vertical') {
                lines++;
                for (const ny of [y - 1, y + 1]) {
                    if (/^road-(edge-(top|bottom)|div-horizontal)$/.test(at(x, ny))) bad.push(`${xy}: the line meets ${at(x, ny)} at ${x},${ny}`);
                }
            }
            if (t === 'road-div-horizontal') {
                lines++;
                for (const nx of [x - 1, x + 1]) {
                    if (/^road-(edge-(left|right)|div-vertical)$/.test(at(nx, y))) bad.push(`${xy}: the line meets ${at(nx, y)} at ${nx},${y}`);
                }
            }
        }
        assert.ok(lines > 500, `the city's roads were read (${lines} centre-line cells)`);
        assert.deepStrictEqual(bad, []);
        // a bend has its mitred outer corner: Tokyo's north-west one, and Park's south-west one,
        // whose west kerb and corner stand in the woods (cities.backdrop.edges)
        const rm = world.roomManager;
        const nw = rm.resolve('Tokyo', 2, 2), sw = rm.resolve('Park', 0, 41);
        assert.strictEqual(at(nw.x, nw.y), 'road-corner-nw');
        assert.strictEqual(at(nw.x + 1, nw.y + 1), 'road-plain');
        assert.strictEqual(at(sw.x - 1, sw.y), 'road-corner-sw');
        assert.strictEqual(at(sw.x - 1, sw.y - 1), 'road-edge-left');
        // on its own (?stitch=0) Park's top row is the far kerb of a T-junction, a bend at its east end
        // (#240); stitched, Palace's roads run into it and the patch opens it, up to the east road's kerb
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const park = cfg.rooms.Park.layers.find((l) => l.name === 'Floor').tiles;
        for (const [x, own, stitched] of [[0, 'road-edge-top', 'road-plain'], [1, 'road-edge-top', 'road-plain'],
            [54, 'road-edge-top', 'road-plain'], [55, 'road-edge-top', 'road-plain'], [56, 'road-corner-ne', 'road-edge-right']]) {
            assert.strictEqual(cfg.tilePalette[park[`${x},0`]], own + '_0_0', `Park ${x},0`);
            const c = rm.resolve('Park', x, 0);
            assert.strictEqual(at(c.x, c.y), stitched, `stitched Park ${x},0`);
        }
    });

    test('each district on its own (?stitch=0) has plain junction boxes too: Palace keeps a copy of both of Park\'s top ones (#247)', () => {
        // the stitched city draws Park's rows there, so the test above never reads Palace's rows 18..20
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const bad = [];
        const roads = {};
        for (const room of cfg.cities.TokyoCity.rooms.map((m) => m.room)) {
            const road = roads[room] = {};
            for (const layer of cfg.rooms[room].layers) {
                for (const [xy, t] of Object.entries(layer.tiles || {})) {
                    const key = (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
                    if (/^road-/.test(key)) road[xy] = key.replace(/_0_0$/, '');
                }
            }
            const at = (x, y) => road[`${x},${y}`] || '';
            for (const xy of Object.keys(road)) {
                const [x, y] = xy.split(',').map(Number), t = road[xy];
                if (t === 'road-div-vertical') {
                    for (const ny of [y - 1, y + 1]) {
                        if (/^road-(edge-(top|bottom)|div-horizontal)$/.test(at(x, ny))) bad.push(`${room} ${xy}: the line meets ${at(x, ny)} at ${x},${ny}`);
                    }
                }
                if (t === 'road-div-horizontal') {
                    for (const nx of [x - 1, x + 1]) {
                        if (/^road-(edge-(left|right)|div-vertical)$/.test(at(nx, y))) bad.push(`${room} ${xy}: the line meets ${at(nx, y)} at ${nx},${y}`);
                    }
                }
            }
        }
        assert.deepStrictEqual(bad, []);
        // Palace's west road runs into the box from the north and out of it to the south: no kerb on either
        // side of it, where Park's own top row is one, and the Palace/Park road opens into it from the east
        const palace = (x, y) => roads.Palace[`${x},${y}`] || '';
        for (const y of [18, 19, 20]) {
            assert.deepStrictEqual([palace(0, y), palace(1, y)], ['road-plain', 'road-plain'], `Palace 0..1,${y}`);
        }
        for (const y of [17, 21]) {
            assert.deepStrictEqual([palace(0, y), palace(1, y)], ['road-div-vertical', 'road-edge-right'], `Palace 0..1,${y}`);
        }
        assert.deepStrictEqual([18, 19, 20].map((y) => palace(2, y)), ['road-edge-top', 'road-div-horizontal', 'road-edge-bottom']);
    });

    test("the east road is the city's edge: no road leaves it for the edge of the map (#240)", () => {
        // the port ran the avenue, the road from the Tokyo/Market crossroads, the Palace/Park road and
        // Park's south road on across the east pavement, two cells to the edge of the map and nothing
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const own = (room, x, y) => {
            const t = cfg.rooms[room].layers.find((l) => l.name === 'Floor').tiles[`${x},${y}`];
            return (cfg.tilePalette[t] || '').replace(/_0_0$/, '');
        };
        const rows = (room) => cfg.rooms[room].worldHeight / 64;
        const brick = 'flat-grey-brick-autotile_';
        // each district on its own (?stitch=0): the kerb runs down column 56 from the bend at the top
        // of Market to the bend at the bottom of Park, with nothing but pavement east of it
        const kerb = { Market: [3, rows('Market') - 1], Palace: [0, rows('Palace') - 1], Park: [0, 41] };
        const corner = { 'Market 56,3': 'road-corner-ne', 'Park 56,0': 'road-corner-ne', 'Park 56,41': 'road-corner-se' };
        const lanes = ['Market 15', 'Market 24', 'Market 32'];       // three side lanes cross the pavement; the kerb passes them
        for (const [room, [y0, y1]] of Object.entries(kerb)) {
            for (let y = y0; y <= y1; y++) {
                assert.strictEqual(own(room, 56, y), corner[`${room} 56,${y}`] || 'road-edge-right', `${room} 56,${y}`);
                if (lanes.includes(`${room} ${y}`)) continue;
                assert.ok(own(room, 57, y).startsWith(brick) && own(room, 58, y).startsWith(brick), `${room} 57..58,${y} is pavement`);
            }
        }
        // where a road ran through it the pavement is the straight run it is everywhere else: no corner
        // pieces left turning into a road that is gone
        for (const [room, y0, y1] of [['Market', 3, 7], ['Market', 40, 46], ['Palace', 16, 21], ['Park', 0, 4], ['Park', 37, 41]]) {
            for (let y = y0; y <= y1; y++) {
                assert.deepStrictEqual([own(room, 57, y), own(room, 58, y)], [brick + 'edge-w', brick + 'edge-e'], `${room} 57..58,${y}`);
            }
        }
        // round the two bends the pavement turns with the road, as at Tokyo's western ones
        assert.deepStrictEqual([own('Market', 57, 1), own('Market', 58, 1), own('Market', 57, 2), own('Market', 58, 2)],
            ['edge-n', 'corner-ne', 'center', 'edge-e'].map((r) => brick + r));
        assert.deepStrictEqual([own('Park', 57, 42), own('Park', 58, 42), own('Park', 57, 43), own('Park', 58, 43)],
            ['center', 'edge-e', 'edge-s', 'corner-se'].map((r) => brick + r));
        // the boxes are still boxes: plain inside, up to that kerb
        for (const [room, y] of [['Market', 3], ['Market', 42], ['Palace', 18], ['Park', 0], ['Park', 39]]) {
            assert.deepStrictEqual([own(room, 54, y + 1), own(room, 55, y + 1)], ['road-plain', 'road-plain'], `${room} box row ${y + 1}`);
        }
        // the city the game plays: nothing but pavement (and the three lanes) on its east edge, and
        // the cells that were road are still walked on
        const { world } = worldWith(true);
        const rm = world.roomManager, city = rm.rooms.TokyoCity;
        const floor = city.layers.find((l) => l.name === 'Floor').tiles;
        const east = city.worldWidth / 64 - 1;
        const roads = [];
        for (let y = 0; y < city.worldHeight / 64; y++) {
            for (const x of [east - 1, east]) {
                const key = floor[`${x},${y}`] || '';
                if (/^road-/.test(key) && !/^road-2-tile-vertical/.test(key)) roads.push(`${x},${y} ${key}`);
            }
        }
        assert.deepStrictEqual(roads, []);
        for (const [room, y] of [['Market', 3], ['Market', 42], ['Park', 0], ['Park', 39]]) {
            for (let dy = 0; dy < 3; dy++) {
                const a = rm.resolve(room, 57, y + dy), b = rm.resolve(room, 58, y + dy);
                assert.ok(b.x === east && world.canStep(a.x, a.y, b.x, b.y) && world.canStep(b.x, b.y, a.x, a.y), `${room} 57..58,${y + dy} is open pavement`);
            }
        }
    });

    test('the avenue runs up to the Tokyo/Market crossroads as road, not a strip of pavement (#194)', () => {
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const rows = ['road-edge-top_0_0', 'road-div-horizontal_0_0', 'road-edge-bottom_0_0'];
        for (const [room, xs, y0] of [['Tokyo', [54, 55, 56], 41], ['Market', [2, 3, 4], 42], ['Market', [52, 53], 42]]) {
            const floor = cfg.rooms[room].layers.find((l) => l.name === 'Floor').tiles;
            for (const x of xs) {
                rows.forEach((want, dy) => assert.strictEqual(cfg.tilePalette[floor[`${x},${y0 + dy}`]], want, `${room} ${x},${y0 + dy}`));
            }
        }
    });
};
