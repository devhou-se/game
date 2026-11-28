// Kansai (issues #255, #267, #268; #68, runs 2, 4 and 5): Osaka the town, Himeji walked to from it along
// Canal-side Avenue, Okayama further along the same avenue, and Nara east of Osaka along it the other way -
// four districts of a third stitched city, KansaiCity. One more district is planned (tools/kansai.py).
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig, worldWith }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const DISTRICTS = ['Himeji', 'Nara', 'Okayama', 'Osaka'];
    const layer = (room, n) => ((cfg.rooms[room].layers || []).find((l) => l.name === n) || {}).tiles || {};
    const size = (room) => [cfg.rooms[room].worldWidth / 64, cfg.rooms[room].worldHeight / 64];
    const solid = (room, x, y) => `${x},${y}` in layer(room, 'Colliders');
    const sprites = {};                                   // room -> sprite key -> its top-left cells
    for (const r of DISTRICTS) {
        sprites[r] = {};
        for (const l of (cfg.rooms[r] || {}).layers || []) {
            for (const [xy, t] of Object.entries(l.tiles || {})) (sprites[r][name(t)] = sprites[r][name(t)] || []).push(xy.split(',').map(Number));
        }
    }
    const at = (room, key) => { assert.ok(sprites[room][key], `${room} has no ${key}`); return sprites[room][key][0]; };
    const offset = Object.fromEntries(((cfg.cities.KansaiCity || {}).rooms || []).map((m) => [m.room, m]));
    // tools/kansai.py is where the generators agree on the layout: plain literals, read from its text
    const py = fs.readFileSync(path.join(GV2, 'tools', 'kansai.py'), 'utf8');
    const table = (v) => Object.fromEntries([...py.match(new RegExp(`^${v} = \\{(.*)\\}`, 'm'))[1].matchAll(/'(\w+)': \((-?\d+), (-?\d+)\)/g)]
        .map((m) => [m[1], [Number(m[2]), Number(m[3])]]));
    const AT = table('AT'), SIZE = table('SIZE');
    const BUILT = [...py.match(/^BUILT = \((.*?)\)/m)[1].matchAll(/'(\w+)'/g)].map((m) => m[1]);
    const IN = Number(py.match(/^CITY, IN = '\w+', (\d+)/m)[1]);
    // where the city's own (0,0) is in devhouse.world, in cells: Osaka's old y, moved west to make room
    const ORIGIN = [-258, 31];
    const seams = (room) => cfg.rooms[room].transporters.filter((t) => DISTRICTS.includes(t.targetRoom));
    const O_AVENUE = [24, 25, 26, 27, 28], H_AVENUE = [18, 19, 20, 21, 22], OK_AVENUE = H_AVENUE;   // Okayama's rows are Himeji's
    const N_AVENUE = H_AVENUE;                            // ...and Nara's, which sits on the same city rows

    test('Kansai is a third stitched city: Osaka, Himeji, Okayama and Nara, placed as tools/kansai.py lays them out, with room left for the district to come (#255, #267, #268)', () => {
        const city = cfg.cities.KansaiCity;
        assert.ok(city, 'config cities has no KansaiCity');
        assert.deepStrictEqual(city.rooms.map((m) => m.room).sort(), BUILT.slice().sort(), 'the city is the districts kansai.py says are built');
        assert.deepStrictEqual(BUILT.slice().sort(), DISTRICTS);
        assert.strictEqual(city.name, 'Kansai');
        assert.ok(city.backdrop && city.backdrop.floor && city.backdrop.tree, 'the gaps between the districts need a woodland backdrop');
        assert.deepStrictEqual(DISTRICTS.map((r) => cfg.rooms[r].name), ['Himeji', 'Nara', 'Okayama', 'Osaka'], 'the HUD names');
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8')).maps;
        const key = (m) => path.basename(m.fileName, '.tmj');
        for (const r of DISTRICTS) {
            assert.deepStrictEqual(size(r), SIZE[r], `${r} is not the size kansai.py says`);
            assert.deepStrictEqual([offset[r].x, offset[r].y], [AT[r][0] + ORIGIN[0], AT[r][1] + ORIGIN[1]], `${r} is not where kansai.py puts it: devhouse.world / sync_cities.py`);
            const m = world.find((w) => key(w) === r.toLowerCase());
            assert.ok(m, `${r.toLowerCase()}.tmj is not in devhouse.world`);
            assert.deepStrictEqual([m.x, m.y, m.width, m.height], [offset[r].x * 64, offset[r].y * 64, SIZE[r][0] * 64, SIZE[r][1] * 64], `${r} in devhouse.world`);
        }
        // the Map draws the city over its whole box, woods included: nothing else may sit in it. Nor in the
        // rectangle of a district that is not built yet, so that the ticket that builds it moves nothing
        const mine = world.filter((m) => DISTRICTS.map((d) => d.toLowerCase()).includes(key(m)));
        const box = { x: Math.min(...mine.map((m) => m.x)), y: Math.min(...mine.map((m) => m.y)) };
        box.width = Math.max(...mine.map((m) => m.x + m.width)) - box.x;
        box.height = Math.max(...mine.map((m) => m.y + m.height)) - box.y;
        const apart = (a, b) => a.x + a.width <= b.x || b.x + b.width <= a.x || a.y + a.height <= b.y || b.y + b.height <= a.y;
        const rect = (d) => ({ x: (AT[d][0] + ORIGIN[0]) * 64, y: (AT[d][1] + ORIGIN[1]) * 64, width: SIZE[d][0] * 64, height: SIZE[d][1] * 64 });
        const unbuilt = Object.keys(AT).filter((d) => !BUILT.includes(d));
        assert.deepStrictEqual(unbuilt.sort(), ['LakeBiwa']);
        for (const m of world) {
            if (mine.includes(m)) continue;
            assert.ok(apart(box, m), `${key(m)} is inside Kansai's box`);
            for (const d of unbuilt) assert.ok(apart(rect(d), m), `${key(m)} is where ${d} is to be built`);
        }
        // the planned districts do not overlap each other or the built ones
        for (const a of Object.keys(AT)) for (const b of Object.keys(AT)) if (a < b) assert.ok(apart(rect(a), rect(b)), `${a} and ${b} overlap`);
        // no room is in two cities, and the city is on the world map
        const all = Object.values(cfg.cities).flatMap((c) => c.rooms.map((m) => m.room));
        assert.strictEqual(new Set(all).size, all.length);
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        for (const d of DISTRICTS) assert.deepStrictEqual(map.rooms[d] && map.rooms[d].cells, size(d), `world-map.json has no ${d}: run make_worldmap.py`);
    });

    test('Kansai: the seams line up - the avenue carries straight across into Himeji, on into Okayama and the other way into Nara, the canal into Himeji\'s moat and Nara\'s river, and each seam cell has its ?stitch=0 transporter both ways (#255, #267, #268)', () => {
        const pairs = DISTRICTS.flatMap((r) => seams(r).map((t) => [r, t]));
        assert.strictEqual(pairs.length, 6 * 5, 'the five avenue cells Osaka<->Himeji, Himeji<->Okayama and Osaka<->Nara, each way');
        // Osaka's west five first, where they were before Nara was built, then its east five: the row order of
        // kansai.py's JOINS, which generate_osaka.py writes as it is. They are the last ten of its transporters
        const OSAKA = O_AVENUE.map((y) => [0, y]).concat(O_AVENUE.map((y) => [size('Osaka')[0] - 1, y]));
        assert.deepStrictEqual(seams('Osaka').map((t) => [t.gridX, t.gridY]), OSAKA);
        assert.deepStrictEqual(seams('Osaka').map((t) => t.targetRoom), Array(5).fill('Himeji').concat(Array(5).fill('Nara')));
        assert.deepStrictEqual(cfg.rooms.Osaka.transporters.slice(-10).map((t) => [t.gridX, t.gridY]), OSAKA);
        assert.deepStrictEqual(seams('Nara').map((t) => [t.gridX, t.gridY]), N_AVENUE.map((y) => [0, y]));
        // Himeji's east five first, where they were before Okayama was built, then its west five
        assert.deepStrictEqual(seams('Himeji').map((t) => [t.gridX, t.gridY]), H_AVENUE.map((y) => [size('Himeji')[0] - 1, y]).concat(H_AVENUE.map((y) => [0, y])));
        assert.deepStrictEqual(seams('Himeji').map((t) => t.targetRoom), Array(5).fill('Osaka').concat(Array(5).fill('Okayama')));
        assert.deepStrictEqual(seams('Okayama').map((t) => [t.gridX, t.gridY]), OK_AVENUE.map((y) => [size('Okayama')[0] - 1, y]));
        const floorAt = (room, x, y) => name(layer(room, 'Floor')[`${x},${y}`]);
        for (const [room, t] of pairs) {
            const [w] = size(room);
            assert.ok(t.hidden && (t.gridX === 0 || t.gridX === w - 1), `${room} ${t.gridX},${t.gridY}: a seam is a hidden transporter on the district's edge`);
            assert.ok(!solid(room, t.gridX, t.gridY) && !solid(t.targetRoom, t.targetX, t.targetY), `${room} ${t.gridX},${t.gridY}: the seam or its target is solid`);
            // the cell across the edge, in the neighbour: the same city cell + 1, open, the same ground, and it leads back
            const dx = t.gridX === 0 ? -1 : 1;
            const nx = t.gridX + offset[room].x + dx - offset[t.targetRoom].x, ny = t.gridY + offset[room].y - offset[t.targetRoom].y;
            const back = cfg.rooms[t.targetRoom].transporters.find((b) => b.gridX === nx && b.gridY === ny);
            assert.ok(back && back.targetRoom === room && back.hidden, `${room} ${t.gridX},${t.gridY}: the cell across the seam (${t.targetRoom} ${nx},${ny}) has no transporter back`);
            assert.ok(/^(flat-grey-brick-autotile_edge-[ns]|road-)/.test(floorAt(room, t.gridX, t.gridY)), `${room} ${t.gridX},${t.gridY} is not the avenue: a pavement either side of its road`);
            assert.strictEqual(floorAt(room, t.gridX, t.gridY), floorAt(t.targetRoom, nx, ny), `the ground changes across the seam at ${room} ${t.gridX},${t.gridY}`);
            assert.deepStrictEqual([t.targetX, t.targetY], [nx + dx * IN, ny], `a seam lands ${IN} cells in from the neighbour's edge`);
        }
        // the canal is the moat: the same water tile on the same city rows either side of the edge, and no way across it
        const hw = size('Himeji')[0];
        for (const y of [20, 21, 22]) {
            const hy = y + offset.Osaka.y - offset.Himeji.y;
            const here = name(layer('Osaka', 'Water')[`0,${y}`]);
            assert.ok(/^pond-autotile_/.test(here), `Osaka's canal does not reach its west edge on row ${y}`);
            assert.strictEqual(name(layer('Himeji', 'Water')[`${hw - 1},${hy}`]), here, `the water changes across the seam on Osaka row ${y}`);
            assert.ok(solid('Osaka', 0, y) && solid('Himeji', hw - 1, hy), 'the water at the seam can be walked on');
        }
        assert.deepStrictEqual([14, 15, 16], [20, 21, 22].map((y) => y + offset.Osaka.y - offset.Himeji.y), 'the moat is Himeji rows 14-16');
        // ...and Nara's river the same at Osaka's east edge (#268): edge-n, center, edge-s on Nara rows 14-16
        const ow = size('Osaka')[0];
        for (const y of [20, 21, 22]) {
            const ny = y + offset.Osaka.y - offset.Nara.y;
            const here = name(layer('Osaka', 'Water')[`${ow - 1},${y}`]);
            assert.strictEqual(name(layer('Nara', 'Water')[`0,${ny}`]), here, `the water changes across the seam into Nara on Osaka row ${y}`);
            assert.ok(solid('Osaka', ow - 1, y) && solid('Nara', 0, ny), 'the water at the seam into Nara can be walked on');
        }
        assert.deepStrictEqual([20, 21, 22].map((y) => name(layer('Nara', 'Water')[`0,${y - 6}`])),
            ['pond-autotile_edge-n', 'pond-autotile_center', 'pond-autotile_edge-s']);
        // the avenue across that seam: pavement, the road's three rows, pavement
        assert.deepStrictEqual(N_AVENUE.map((y) => name(layer('Nara', 'Floor')[`0,${y}`])), ['flat-grey-brick-autotile_edge-n', 'road-edge-top_0_0',
            'road-div-horizontal_0_0', 'road-edge-bottom_0_0', 'flat-grey-brick-autotile_edge-s']);
        // the only open cells on a district's edge are the seam cells. Okayama's west, north and south edges
        // are closed: nothing is planned beyond it; Nara's east and south ones likewise, and its north edge
        // until Lake Biwa is built (#269)
        const edgeOpen = (room) => {                  // the edge cells that can be walked to from the district's ways in
            const [w, h] = size(room), todo = cfg.rooms[room].transporters.map((t) => [t.gridX, t.gridY]);
            const seen = new Set(todo.map((c) => c.join()));
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    if (nx < 0 || ny < 0 || nx >= w || ny >= h || solid(room, nx, ny) || seen.has(`${nx},${ny}`)) continue;
                    seen.add(`${nx},${ny}`); todo.push([nx, ny]);
                }
            }
            return [...seen].filter((xy) => { const [x, y] = xy.split(',').map(Number); return x === 0 || y === 0 || x === w - 1 || y === h - 1; }).sort();
        };
        const mine = (room) => seams(room).map((t) => `${t.gridX},${t.gridY}`);
        assert.deepStrictEqual(edgeOpen('Himeji'), mine('Himeji').sort(), 'Himeji: an edge cell is open that is not a seam');
        assert.deepStrictEqual(edgeOpen('Okayama'), mine('Okayama').sort(), 'Okayama: an edge cell is open that is not a seam into Himeji');
        assert.ok(edgeOpen('Okayama').every((xy) => xy.startsWith(`${size('Okayama')[0] - 1},`)), "Okayama is open on an edge that is not its east one");
        assert.deepStrictEqual(edgeOpen('Osaka'), mine('Osaka').sort(), 'Osaka: an edge cell is open that is not a seam');
        assert.strictEqual(edgeOpen('Osaka').length, 10);
        assert.deepStrictEqual(edgeOpen('Nara'), N_AVENUE.map((y) => `0,${y}`).sort(), 'Nara: an edge cell is open that is not a seam into Osaka');
    });

    test('Kansai: the moat is the west end of Osaka\'s canal and Nara\'s river its east end - the three declared waterways sail as one run across the seams (#255, #268)', () => {
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');
        const plain = (v) => JSON.parse(JSON.stringify(v));
        const runs = DISTRICTS.flatMap((r) => (cfg.rooms[r].waterways || []).map((w) => {
            assert.strictEqual(w.axis, 'h', `${r}'s waterway`);
            return { axis: 'h', from: w.from + AT[r][0], to: w.to + 1 + AT[r][0], band0: w.row + AT[r][1], band1: w.row + AT[r][1] + w.rows,
                under: (w.under || []).map(([a, b]) => [a + AT[r][0], b + 1 + AT[r][0]]) };
        }));
        assert.strictEqual(runs.length, 3, 'one waterway in Himeji, in Osaka and in Nara, none in Okayama: no arm of its river leads anywhere');
        const [moat, river, canal] = runs;                // in DISTRICTS order: Himeji, Nara, Osaka
        assert.deepStrictEqual([moat.to, moat.band0, moat.band1], [canal.from, canal.band0, canal.band1], 'the moat ends where the canal starts, on its rows');
        assert.deepStrictEqual([river.from, river.band0, river.band1], [canal.to, canal.band0, canal.band1], 'Nara\'s river starts where the canal ends, on its rows');
        assert.deepStrictEqual(river.under, [], 'nothing crosses Nara\'s river');
        const joined = plain(game('AmbientBoats').joinRuns(runs, 1));
        assert.strictEqual(joined.length, 1, 'a boat would fade out at a seam');
        // from the moat's bank to the river's bend: a boat fades out where the river turns north
        assert.deepStrictEqual([joined[0].from, joined[0].to, joined[0].band0, joined[0].band1], [AT.Himeji[0] + 7, AT.Nara[0] + 20, canal.band0, canal.band1]);
        assert.deepStrictEqual([joined[0].from, joined[0].to], [51, 158]);
        // every cell of Nara's river is water, and none of it is walked on: in from Osaka and north up the bend
        for (let x = 0; x <= 22; x++) for (let y = x < 20 ? 14 : 2; y <= 16; y++) {
            assert.ok(/^pond-autotile_/.test(name(layer('Nara', 'Water')[`${x},${y}`])) && solid('Nara', x, y), `Nara ${x},${y} is not the river`);
        }
        // ...under both bridges: the castle's and Dotonbori's
        assert.deepStrictEqual(joined[0].under, moat.under.concat(canal.under));
        assert.strictEqual(joined[0].under.length, 2);
        // the moat's run starts at the first cell with open water all round the hull: the bank is one column west of it
        const bank = name(layer('Himeji', 'Water')['6,14']);
        assert.strictEqual(bank, 'pond-autotile_corner-nw');
        assert.ok(!('5,15' in layer('Himeji', 'Water')) && name(layer('Himeji', 'Water')['7,15']) === 'pond-autotile_center');
        // every cell of the declared moat is water, and it is crossed by the bridge alone
        // (the same timber bridge crosses the garden's pond, further south)
        const [bx, by] = sprites.Himeji['himeji-bridge_0_0'].find(([, y]) => y < 20);
        for (let x = 6; x < SIZE.Himeji[0]; x++) for (const y of [14, 15, 16]) {
            assert.ok(/^pond-autotile_/.test(name(layer('Himeji', 'Water')[`${x},${y}`])), `no water at Himeji ${x},${y}`);
            assert.strictEqual(solid('Himeji', x, y), !(x === bx || x === bx + 1), `Himeji ${x},${y}`);
        }
        assert.deepStrictEqual([bx, by], [32, 14]);
        assert.deepStrictEqual(cfg.rooms.Himeji.waterways[0].under, [[bx, bx + 1]]);
    });

    test('Kansai is one walkable room: Osaka -> Himeji\'s keep terrace -> Koko-en -> Okayama\'s keep -> Korakuen -> the Great Buddha Hall -> Kasuga Taisha -> the towpath -> Nara Park -> Osaka on foot, stitched and with ?stitch=0 (#255, #267, #268)', () => {
        const [kx, ky] = at('Himeji', 'himeji-keep_0_0'), [gx, gy] = at('Himeji', 'himeji-kokoen-gate_0_0');
        const stops = [['Osaka', 3, 26],                                // on the avenue, by the fingerpost
            ['Himeji', kx + 4, ky + 9],                                  // the terrace in front of the keep: over the bridge, up the steps
            ['Himeji', gx + 2, gy + 5],                                  // inside Koko-en, through its gate
            ['Okayama', 20, 9],                                          // in front of the black keep: along the avenue, up the steps
            ['Okayama', 27, 32],                                         // on Korakuen's lawn: over the Tsukimi bridge
            ['Nara', 34, 10],                                            // in front of the hall: through the Nandaimon
            ['Nara', 44, 31],                                            // in front of Kasuga Taisha: through the torii, up the approach
            ['Nara', 23, 2],                                             // the towpath's end, by the river's head
            ['Nara', 16, 28],                                            // on the lawn among the deer
            ['Osaka', 3, 26]];
        const ORDER = Object.keys(AT).filter((d) => BUILT.includes(d)).sort((a, b) => AT[a][0] - AT[b][0]);   // west to east
        assert.deepStrictEqual(ORDER, ['Okayama', 'Himeji', 'Osaka', 'Nara']);
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            world.enter(...stops[0]);
            if (stitch) {
                assert.strictEqual(world.here().city, 'KansaiCity', 'Osaka is entered as the city room');
                const city = rm.rooms.KansaiCity;
                assert.deepStrictEqual([city.worldWidth / 64, city.worldHeight / 64], [AT.Nara[0] + SIZE.Nara[0], SIZE.Osaka[1]]);
                assert.deepStrictEqual([city.worldWidth / 64, city.worldHeight / 64], [190, 46]);
                assert.strictEqual(city.depthScale, 1, 'the city is short enough that Y-sorted depths need no squeeze');
                // the railway is Osaka's: it carries on west over the wood above Himeji and Okayama, and east over
                // the open strip above Nara, in the city's backdrop
                const track = city.layers.filter((l) => /^Backdrop/.test(l.name)).flatMap((l) => Object.entries(l.tiles))
                    .filter(([, t]) => /^train-track/.test(t)).map(([xy]) => xy.split(',').map(Number));
                assert.strictEqual(track.length, AT.Osaka[0] + SIZE.Nara[0], 'the track is not carried on to the city\'s west and east edges');
                assert.ok(track.every(([x, y]) => (x < AT.Osaka[0] || x >= AT.Nara[0]) && y === 4), 'the track runs two rows above Himeji\'s, Okayama\'s and Nara\'s top row');
            } else {
                assert.strictEqual(world.here().city, null);
            }
            let fades = 0, crossings = 0;
            const walk = (room, x, y) => {
                while (!stitch && world.here().room !== room) {
                    // not there yet: walk to the nearest seam into the next district on the way, and again from
                    // there (stitched, the path below does it in one)
                    const from = world.here().room, next = ORDER[ORDER.indexOf(from) + Math.sign(ORDER.indexOf(room) - ORDER.indexOf(from))];
                    const seam = seams(from).filter((t) => t.targetRoom === next).map((t) => ({ t, route: world.path(t.gridX, t.gridY) })).filter((s) => s.route)
                        .sort((a, b) => a.route.length - b.route.length)[0];
                    assert.ok(seam, `${tag}: no seam into ${next} can be walked to from ${from}`);
                    for (const dir of seam.route) {
                        const r = world.step(dir);
                        assert.ok(r.moved, `${tag}: blocked on the way to the seam`);
                        if (r.transported) {
                            fades++;
                            // it lands IN cells inside the neighbour, on the avenue
                            const [w] = size(world.here().room), x0 = world.here().x;
                            assert.ok(x0 === IN || x0 === w - 1 - IN, `${tag}: landed at ${world.here().room} ${x0},${world.here().y}`);
                        }
                    }
                    assert.strictEqual(world.here().room, next, `${tag}: the seam out of ${from} did not lead into ${next}`);
                }
                const to = rm.resolve(room, x, y);
                const route = world.path(to.x, to.y);
                assert.ok(route, `${tag}: no way on foot to ${room} ${x},${y} from ${world.here().room} ${world.here().x},${world.here().y}`);
                for (const dir of route) {
                    const r = world.step(dir);
                    assert.ok(r.moved, `${tag}: blocked on the way to ${room} ${x},${y}`);
                    assert.ok(!r.transported, `${tag}: a transporter fired on the way to ${room} ${x},${y}`);
                    if (r.crossed) crossings++;
                }
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [room, x, y], tag);
            };
            for (const stop of stops.slice(1)) walk(...stop);
            // out along the avenue to its west end, back east to Nara and home: six district changes
            assert.deepStrictEqual([fades, crossings], stitch ? [0, 6] : [6, 0], `${tag}: fades, crossings`);
        }
    });

    test('Himeji: the keep is looked up at from the terrace, Damian stands in front of it on 13 November 2025, and nobody walks behind it (#255)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Himeji', x, y); return seen.has(`${c.x},${c.y}`); };
        // the keep: ten cells by eight, on the district's top row, its art exactly its footprint (nothing overhangs
        // the row above, which is not Himeji's), solid all over
        const [kx, ky] = at('Himeji', 'himeji-keep_0_0');
        assert.deepStrictEqual([kx, ky], [8, 0]);
        const png = fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'himeji-keep_0_0.png'));
        assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [640, 512]);
        for (let x = kx; x < kx + 10; x++) for (let y = ky; y < ky + 8; y++) assert.ok(!walkable(x, y), `the keep can be walked onto at ${x},${y}`);
        const [tx, ty] = at('Himeji', 'himeji-turret_0_0');
        for (let x = tx; x < tx + 3; x++) for (let y = ty; y < ty + 4; y++) assert.ok(!walkable(x, y), `the turret can be walked onto at ${x},${y}`);
        // the only way up is the gatehouse: the bridge, the gateway, the steps
        const [gx, gy] = at('Himeji', 'himeji-gate_0_0');
        for (let y = gy; y <= 17; y++) assert.ok(walkable(gx + 2, y) && walkable(gx + 3, y), `the way up is shut at row ${y}`);
        for (let x = 6; x < 42; x++) if (x !== gx + 2 && x !== gx + 3) for (const y of [10, 11, 12, 13]) assert.ok(!walkable(x, y), `the hill's wall can be walked through at ${x},${y}`);
        assert.strictEqual(sprites.Himeji['himeji-wall_0_0'].length, 30, 'the white wall, either side of the gatehouse');
        // Damian's day at Himeji (post 754) is told here, in front of the keep: the row under it or the next, inside its columns
        const damian = cfg.rooms.Himeji.npcs.find((n) => n.name === 'Damian');
        const day = damian && damian.states['2025-11-13'];
        assert.ok(day && day.present && day.posts.map((p) => p.id).join() === '754', 'Damian is not in Himeji on 2025-11-13');
        assert.ok(day.gridX >= kx + 1 && day.gridX <= kx + 8 && day.gridY >= ky + 8 && day.gridY <= ky + 9, `Damian at ${day.gridX},${day.gridY} is not in front of the keep`);
        assert.ok(walkable(day.gridX, day.gridY) && !cfg.rooms.Himeji.interior, 'nobody can walk to him');
        assert.ok(!cfg.rooms.Himeji.transporters.some((t) => t.gridX === day.gridX && t.gridY === day.gridY), 'he stands on a seam');
        assert.ok(Object.entries(damian.states).every(([date, s]) => date === '2025-11-13' || !s.present) && damian.present === false, 'he is there that day only');
        // ...where the camera looks up at all of it, for him and for whoever stands beside him to talk
        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView'), look = realConfig().game.lookUp, G = 64;
        assert.strictEqual(look.sprites['himeji-keep'], 0, 'the keep is not a landmark the camera looks up at');
        const [mark] = LandmarkView.index([{ key: 'himeji-keep_0_0', left: kx * G, top: ky * G, width: 640, height: 512 }], look.sprites, G);
        const beside = [[0, 0], [-1, 0], [1, 0], [0, 1]].map(([dx, dy]) => [day.gridX + dx, day.gridY + dy]).filter(([x, y]) => walkable(x, y));
        assert.ok(beside.length >= 3, 'there is no room to stand beside him');
        for (const [x, y] of beside) {
            for (const view of [{ viewH: 960, bar: 40, deadzone: 256, foot: 128 }, { viewH: 480, bar: 46, deadzone: 128, foot: 188 }]) {
                const a = LandmarkView.aim(Object.assign({ x: x * G + 32, y: y * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side }, view));
                assert.ok(a.weight === 1 && a.offset > 0, `the camera does not look up from ${x},${y}`);
            }
        }
        // the desktop view holds the whole keep from his cell: its top is under the bar
        const desk = LandmarkView.aim({ x: day.gridX * G + 32, y: day.gridY * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side,
            viewH: 960, bar: 40, deadzone: 256, foot: 128 });
        assert.ok(day.gridY * G + 32 - desk.offset - 960 / 2 + 40 <= ky * G, 'the top of the keep is cut off on desktop');
        // the blog pipeline's label for it, and Koko-en's
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        assert.ok(/\('himeji-keep_', 'Himeji Castle', \(4, 8\), \{'rooms': \('Himeji',\)\}\)/.test(tool), 'LANDMARKS has no row for the keep');
        assert.ok(/\('himeji-kokoen-gate_', 'Koko-en garden', \(1, 5\), \{'rooms': \('Himeji',\)\}\)/.test(tool), 'LANDMARKS has no row for Koko-en');
        assert.ok(walkable(kx + 4, ky + 8), 'the keep\'s visitor cell');
    });

    test('Himeji: Koko-en is a walled garden through its gate, three rooms in a row, with a pond that is the garden\'s and not the moat (#255, #275)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Himeji', x, y); return seen.has(`${c.x},${c.y}`); };
        const [gx, gy] = at('Himeji', 'himeji-kokoen-gate_0_0');
        assert.deepStrictEqual([gx, gy], [8, 23]);
        // the wall runs the garden's whole north side; the gateway (two cells) is the only way in
        for (let x = 5; x <= 41; x++) {
            const way = x === gx + 1 || x === gx + 2;
            assert.strictEqual(walkable(x, 24) || walkable(x, 25), way, `Koko-en's wall at column ${x}`);
        }
        assert.ok(walkable(gx + 1, gy + 5), 'LANDMARKS stands Koko-en\'s visitor here');
        // three rooms, parted by north-south walls whose openings are staggered: in at the west, out of A on
        // rows 28-29, out of B on rows 34-35; the garden's west and east sides are the same wall, unbroken
        for (const [x, gap] of [[5, []], [18, [28, 29]], [31, [34, 35]], [41, []]]) {
            for (let y = 26; y <= 37; y++) assert.strictEqual(walkable(x, y), gap.includes(y), `Koko-en's wall on column ${x}, row ${y}`);
        }
        for (const [x, y] of [[6, 26], [17, 37], [19, 26], [30, 37], [32, 26], [40, 37], [24, 29], [25, 33]]) assert.ok(walkable(x, y), `Koko-en: nobody can walk to ${x},${y}`);
        const walls = Object.entries(sprites.Himeji).filter(([k]) => /^himeji-kokoen-wall-v/.test(k));
        assert.deepStrictEqual(walls.map(([k]) => k).sort(), ['himeji-kokoen-wall-v-end_0_0', 'himeji-kokoen-wall-v-top_0_0', 'himeji-kokoen-wall-v_0_0']);
        assert.ok(walls.every(([, cells]) => cells.every(([x]) => [5, 18, 31, 41].includes(x))), 'a garden wall off its columns');
        // its paths are stepping stones, not gravel; the maples are room C's
        assert.ok(!Object.values(layer('Himeji', 'Floor')).some((t) => /^gravel-autotile_/.test(name(t))), 'gravel on Himeji\'s floor');
        const maples = sprites.Himeji['sendai-maple_0_0'] || [];
        assert.ok(maples.length >= 4 && maples.every(([x, y]) => x >= 32 && x <= 40 && y >= 24), `the maples: ${maples.join(' ')}`);
        const pond = Object.entries(layer('Himeji', 'Water')).filter(([xy]) => Number(xy.split(',')[1]) > 22);
        assert.ok(pond.length === 24 && pond.every(([, t]) => /^pond-autotile_/.test(name(t))), 'the garden has no koi pond');
        assert.ok(pond.filter(([xy]) => !solid('Himeji', ...xy.split(',').map(Number))).map(([xy]) => xy).sort().join(' ') === '24,30 24,31 24,32 25,30 25,31 25,32', 'the pond is crossed by its bridge alone');
        // "the pond" is a spot of the garden, not of the castle: the label's tile (the pond's north-west corner) is
        // also the moat's bank, and must be found in the garden first
        const d = Object.fromEntries(cfg.districts.Himeji.map((x) => [x.key, x]));
        assert.deepStrictEqual(Object.keys(d).sort(), ['castle', 'kokoen']);
        assert.ok(d.kokoen.spots.includes('the pond') && d.kokoen.spots.includes('Koko-en garden'), `Koko-en's spots: ${d.kokoen.spots}`);
        assert.ok(!d.castle.spots.includes('the pond') && d.castle.spots.includes('Himeji Castle'), `the castle's spots: ${d.castle.spots}`);
        // the moat can be fished from the avenue's verge, like the canal it is
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const I = game('Interactions');
        const { world: apart, config } = worldWith(false);
        const sizeOf = (key) => apart.cells(key);
        const fish = I.find(config.rooms.Himeji, config.rooms.Himeji, 20, 16, { sizeOf });
        const canal = I.find(config.rooms.Osaka, config.rooms.Osaka, 5, 22, { sizeOf });
        assert.deepStrictEqual([fish && fish.kind, canal && canal.kind], ['pond', 'pond'], 'the moat is not fished');
    });

    test('Himeji: the keep is reached by a hairpin through three courts, on sand (#275)', () => {
        const { world } = worldWith(false);
        world.enter('Himeji', 32, 17);
        const seen = world.reachable();
        const open = (x, y) => seen.has(`${x},${y}`);
        // over the bridge, through the gate into Sannomaru, east to the steps, west along the upper walk,
        // down the lane into Honmaru: the long way round to the keep's visitor cell
        const route = world.path(12, 8);
        assert.ok(route && route.length >= 45, `the keep is ${route && route.length} steps from the bridge`);
        // the inner stone wall, rows 4-5, is climbed by its steps alone
        for (let x = 20; x <= 41; x++) for (const y of [4, 5]) assert.strictEqual(open(x, y), x === 38 || x === 39, `the inner wall at ${x},${y}`);
        // the turret stands against it and closes Honmaru from Sannomaru
        assert.deepStrictEqual(at('Himeji', 'himeji-turret_0_0'), [20, 6]);
        for (let x = 18; x <= 19; x++) for (let y = 2; y <= 7; y++) assert.ok(open(x, y), `the lane at ${x},${y}`);
        for (const [x, y] of [[12, 8], [19, 5], [30, 3], [30, 8]]) {
            assert.ok(/^sand-autotile_/.test(name(layer('Himeji', 'Floor')[`${x},${y}`])), `the court at ${x},${y} is not sand`);
        }
        assert.ok(!(sprites.Himeji['sendai-maple_0_0'] || []).some(([, y]) => y <= 22), 'a maple in the castle');
    });

    test('Kansai: a fingerpost stands by each seam on each side and says where the avenue goes; Himeji is its own place (#255, #267, #268)', () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const I = game('Interactions');
        const { world, config } = worldWith(false);
        const sizeOf = (key) => world.cells(key);
        // one sprite key for each seam: a flavour rule is matched by key, and the two seams say different things
        const OSAKA_HIMEJI = ['kansai-fingerpost_0_0', 'west: himeji castle and koko-en. east: osaka, dotonbori'];
        const HIMEJI_OKAYAMA = ['okayama-fingerpost_0_0', 'west: okayama, the black castle and korakuen. east: himeji castle, then osaka'];
        const OSAKA_NARA = ['nara-fingerpost_0_0', 'west: osaka, dotonbori. east: nara, the great buddha and the deer'];
        const sides = [['Osaka', 0, ...OSAKA_HIMEJI], ['Himeji', size('Himeji')[0] - 1, ...OSAKA_HIMEJI],
            ['Himeji', 0, ...HIMEJI_OKAYAMA], ['Okayama', size('Okayama')[0] - 1, ...HIMEJI_OKAYAMA],
            ['Osaka', size('Osaka')[0] - 1, ...OSAKA_NARA], ['Nara', 0, ...OSAKA_NARA]];
        for (const r of DISTRICTS) for (const key of [OSAKA_HIMEJI[0], HIMEJI_OKAYAMA[0], OSAKA_NARA[0]]) {
            assert.strictEqual((sprites[r][key] || []).length, sides.filter((s) => s[0] === r && s[2] === key).length, `${r}'s ${key}`);
        }
        for (const [room, edge, key, line] of sides) {
            const posts = sprites[room][key] || [];
            assert.strictEqual(posts.length, 1, `${room} has ${posts.length} fingerposts for its seam at x = ${edge}`);
            const [x, y] = posts[0];
            assert.ok(Math.abs(x - edge) <= 4, `${room}'s fingerpost at ${x},${y} is not by the seam`);
            assert.deepStrictEqual(sizeOf(key), [1, 2]);
            // beside the pavement, not on it: its foot is on the row under the avenue's last, and it is bumped from the avenue
            const last = room === 'Osaka' ? O_AVENUE[4] : H_AVENUE[4];
            assert.strictEqual(y + 1, last + 1, `${room}'s fingerpost stands on the avenue`);
            assert.ok(solid(room, x, y + 1) && !solid(room, x, last), `${room}'s fingerpost`);
            for (const cy of [y, y + 1]) {
                const hit = I.find(config.rooms[room], config.rooms[room], x, cy, { sizeOf, group: 'flavour' });
                assert.deepStrictEqual([hit && hit.kind, hit && hit.say], ['fingerpost', line], `${room} ${x},${cy}`);
            }
        }
        // Himeji has no station and no railway (the train's row is Osaka's), no door but the seam, and nothing
        // borrowed from Hokuriku's own art
        assert.deepStrictEqual(Object.values(cfg.stations).filter((s) => s.town === 'Himeji'), [], 'you walk to Himeji');
        assert.ok(cfg.rooms.Himeji.transporters.every((t) => ['Osaka', 'Okayama'].includes(t.targetRoom) && t.hidden), 'Himeji has a door that is not a seam');
        assert.ok(!Object.keys(sprites.Himeji).some((k) => /^train-track/.test(k)), 'Himeji has a railway');
        assert.deepStrictEqual(Object.keys(sprites.Himeji).filter((k) => /^(hokuriku|kanazawa|shirakawa|toyama)-/.test(k)), [], 'Himeji wears another town\'s art');
        assert.deepStrictEqual(Object.keys(sprites.Himeji).filter((k) => /rubbish-bin/.test(k)), []);
        for (const k of ['himeji-keep', 'himeji-turret', 'himeji-gate', 'himeji-bridge', 'himeji-kokoen-gate', 'himeji-wall']) {
            assert.ok(sprites.Himeji[`${k}_0_0`] && `${k}_0_0` in cfg.spriteMetadata, `Himeji has no ${k}`);
        }
        // Osaka's railway runs off its west edge now, and off its east edge since Nara (#268): no bushes on the
        // corridor's ends, track to each edge
        for (const x of [0, size('Osaka')[0] - 1]) {
            for (const y of [3, 4, 5]) {
                for (const l of cfg.rooms.Osaka.layers) assert.ok(!/^shrub/.test(name((l.tiles || {})[`${x},${y}`])), `a bush caps Osaka's railway at (${x},${y}) in ${l.name}`);
            }
            assert.ok(/^train-track/.test(name(layer('Osaka', 'Over Floor')[`${x},4`])), `no track on Osaka (${x},4)`);
        }
        // on the Map it is a small place of its own, where it is in Japan: west of Osaka, on Honshu
        const place = cfg.places.Himeji;
        assert.deepStrictEqual(place, { geo: [134.69, 34.82], label: 'Himeji', minor: true });
        assert.ok(place.geo[0] < cfg.places.Osaka.geo[0], 'Himeji is west of Osaka');
        assert.ok(!('KansaiCity' in cfg.places), 'the stitched city has no dot of its own: its towns do');
    });

    test('Okayama: the black keep stands on its terrace above the stone wall, is looked up at from in front, and nobody walks behind it (#267)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Okayama', x, y); return seen.has(`${c.x},${c.y}`); };
        // the keep: eight cells by seven, two rows of wood behind it, its art exactly its footprint, and solid
        // over all of it, roof rows too
        const [kx, ky] = at('Okayama', 'okayama-keep_0_0');
        assert.deepStrictEqual([kx, ky], [18, 2]);
        const png = fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'okayama-keep_0_0.png'));
        assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [512, 448]);
        for (let x = kx; x < kx + 8; x++) for (let y = ky; y < ky + 7; y++) assert.ok(!walkable(x, y), `the keep can be walked onto at ${x},${y}`);
        for (let x = 0; x < SIZE.Okayama[0]; x++) for (const y of [0, 1]) assert.ok(!walkable(x, y), `the wood behind the keep can be walked into at ${x},${y}`);
        // the terrace's stone wall runs its whole south side: the steps on the axis (two cells) are the only way up
        for (let x = 13; x <= 40; x++) {
            const way = x === 21 || x === 22;
            for (const y of [13, 14]) assert.strictEqual(walkable(x, y), way, `the terrace's wall at ${x},${y}`);
            if (!way) assert.strictEqual(name(layer('Okayama', 'Collidables')[`${x},13`]), 'castle-wall-siding_0_0', `no wall at column ${x}`);
        }
        for (let y = 9; y <= 23; y++) assert.ok(walkable(21, y) && walkable(22, y), `the axis from the keep to the bridge is shut at row ${y}`);
        // the camera looks up at all of it from the cell the blog pipeline stands a visitor on, and from beside it
        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView'), look = realConfig().game.lookUp, G = 64;
        assert.strictEqual(look.sprites['okayama-keep'], 0, 'the keep is not a landmark the camera looks up at');
        const [mark] = LandmarkView.index([{ key: 'okayama-keep_0_0', left: kx * G, top: ky * G, width: 512, height: 448 }], look.sprites, G);
        const [vx, vy] = [kx + 2, ky + 7];
        assert.deepStrictEqual([vx, vy], [20, 9]);
        const beside = [[0, 0], [-1, 0], [1, 0], [0, 1]].map(([dx, dy]) => [vx + dx, vy + dy]).filter(([x, y]) => walkable(x, y));
        assert.strictEqual(beside.length, 4, 'there is no room to stand in front of the keep');
        for (const [x, y] of beside) {
            for (const view of [{ viewH: 960, bar: 40, deadzone: 256, foot: 128 }, { viewH: 480, bar: 46, deadzone: 128, foot: 188 }]) {
                const a = LandmarkView.aim(Object.assign({ x: x * G + 32, y: y * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side }, view));
                assert.ok(a.weight === 1 && a.offset > 0, `the camera does not look up from ${x},${y}`);
            }
        }
        // the desktop view holds the whole keep from that cell: its top is under the bar
        const desk = LandmarkView.aim({ x: vx * G + 32, y: vy * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side,
            viewH: 960, bar: 40, deadzone: 256, foot: 128 });
        assert.ok(vy * G + 32 - desk.offset - 960 / 2 + 40 <= ky * G, 'the top of the keep is cut off on desktop');
        // the blog pipeline's labels for the keep, the garden, the statue and the stall
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        for (const [key, label, dx, dy] of [['okayama-keep_', 'Okayama Castle', 2, 7], ['okayama-crane_', 'Korakuen garden', -1, 1],
            ['okayama-momotaro_', 'the Momotaro statue', 0, 3], ['okayama-bizen-stall_', 'the Bizen-ware stall', 1, 3]]) {
            assert.ok(tool.includes(`('${key}', '${label}', (${dx}, ${dy}), {'rooms': ('Okayama',)})`), `LANDMARKS has no row for ${label}`);
            const [sx, sy] = Object.entries(sprites.Okayama).find(([k]) => k.startsWith(key))[1].slice().sort((a, b) => `${a}` < `${b}` ? -1 : 1)[0];
            assert.ok(walkable(sx + dx, sy + dy), `${label}: nobody can walk to its visitor's cell ${sx + dx},${sy + dy}`);
        }
    });

    test('Okayama: Korakuen is an island in a river crossed by the Tsukimi bridge alone, with a pond that is the garden\'s and not the river (#267)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Okayama', x, y); return seen.has(`${c.x},${c.y}`); };
        // the river: a ring of water round the island, three rows wide on the north side and two elsewhere
        const RIVER = [5, 24, 40, 37], ISLAND = [7, 27, 38, 35];
        const onIsland = (x, y) => x >= ISLAND[0] && x <= ISLAND[2] && y >= ISLAND[1] && y <= ISLAND[3];
        const open = [];
        for (let x = RIVER[0]; x <= RIVER[2]; x++) for (let y = RIVER[1]; y <= RIVER[3]; y++) {
            if (onIsland(x, y)) continue;
            assert.ok(/^pond-autotile_/.test(name(layer('Okayama', 'Water')[`${x},${y}`])), `no water at Okayama ${x},${y}`);
            if (!solid('Okayama', x, y)) open.push(`${x},${y}`);
        }
        assert.strictEqual(open.sort().join(' '), '21,24 21,25 21,26 22,24 22,25 22,26', 'the river is crossed by its bridge alone');
        assert.deepStrictEqual(at('Okayama', 'okayama-bridge_0_0'), [21, 24]);
        assert.deepStrictEqual(sprites.Okayama['okayama-bridge_0_0'].length, 1);
        // a steel footbridge, not Himeji's timber one; and it is walked on, not behind: drawn flat like the ground
        assert.ok(!sprites.Okayama['himeji-bridge_0_0'], 'the Tsukimi bridge is Himeji\'s timber bridge');
        assert.ok(cfg.spriteMetadata['okayama-bridge_0_0'].depthBias < 0 && cfg.spriteMetadata['okayama-bank-rock_0_0'].depthBias < 0);
        // the pond set has no inner corner: a heap of the rim's stones lies over each corner of the island
        assert.deepStrictEqual(sprites.Okayama['okayama-bank-rock_0_0'].map((c) => c.join()).sort(), ['38,26', '38,35', '6,26', '6,35']);
        // the island: in over the bridge, round the loop, and nowhere off it but back over the bridge
        for (const [x, y] of [[22, 27], [9, 28], [36, 28], [9, 34], [36, 34], [22, 30], [27, 32]]) assert.ok(walkable(x, y), `Korakuen: nobody can walk to ${x},${y}`);
        const garden = Object.entries(layer('Okayama', 'Water')).map(([xy, t]) => [xy.split(',').map(Number), name(t)]).filter(([[x, y]]) => onIsland(x, y));
        assert.strictEqual(garden.length, 12, 'the garden has no pond');
        assert.ok(garden.every(([[x, y], t]) => /^pond-autotile_/.test(t) && solid('Okayama', x, y)));
        // two cranes on the lawn, pines and maples, lanterns
        assert.strictEqual(sprites.Okayama['okayama-crane_0_0'].length, 2);
        for (const [x, y] of sprites.Okayama['okayama-crane_0_0']) assert.ok(onIsland(x, y + 1) && solid('Okayama', x, y + 1) && !solid('Okayama', x, y), `the crane at ${x},${y}`);
        // "the pond" is a spot of the garden, not of the castle or the avenue: the label's tile (a pond's
        // north-west corner) is also the river's, and must be found in the garden first
        const d = Object.fromEntries(cfg.districts.Okayama.map((x) => [x.key, x]));
        assert.deepStrictEqual(Object.keys(d).sort(), ['castle', 'korakuen', 'momotaro']);
        assert.deepStrictEqual(d.korakuen.spots.slice().sort(), ['Korakuen garden', 'the pond']);
        assert.deepStrictEqual(d.castle.spots, ['Okayama Castle']);
        assert.deepStrictEqual(d.momotaro.spots.slice().sort(), ['the Bizen-ware stall', 'the Momotaro statue']);
        assert.deepStrictEqual(d.korakuen.bounds, ISLAND);
        // no boat sails the river: no arm of it leads anywhere
        assert.ok(!('waterways' in cfg.rooms.Okayama), 'Okayama declares a waterway');
        // ...but it is fished from its bank, like the moat
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const { world: apart, config } = worldWith(false);
        const fish = game('Interactions').find(config.rooms.Okayama, config.rooms.Okayama, 15, 24, { sizeOf: (key) => apart.cells(key) });
        assert.strictEqual(fish && fish.kind, 'pond', 'the river is not fished');
    });

    test('Okayama: Damian\'s post of 12 November 2025 stands in Korakuen, not on Hakata\'s platform (#267)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Okayama', x, y); return seen.has(`${c.x},${c.y}`); };
        const damian = cfg.rooms.Okayama.npcs.find((n) => n.name === 'Damian');
        const day = damian && damian.states['2025-11-12'];
        assert.ok(day && day.present === true, 'Damian is not in Okayama on 2025-11-12');
        assert.deepStrictEqual([day.photo, day.posts.map((p) => p.id).join()], ['745', '745']);
        assert.ok(day.dialogue.length === 4 && /Korakuen/.test(day.dialogue.join(' ')) && /Bizen/.test(day.dialogue.join(' ')), 'the lines went along');
        // on the island's lawn, beside the first crane; somebody can walk up to him, and he is not on a seam
        assert.deepStrictEqual([day.gridX, day.gridY], [27, 31]);
        assert.ok(day.gridX >= 7 && day.gridX <= 38 && day.gridY >= 27 && day.gridY <= 35, 'he is not on the island');
        assert.ok(walkable(day.gridX, day.gridY) && !cfg.rooms.Okayama.interior, 'nobody can walk to him');
        assert.ok([[-1, 0], [1, 0], [0, 1], [0, -1]].filter(([dx, dy]) => walkable(day.gridX + dx, day.gridY + dy)).length >= 2, 'there is no room to stand beside him');
        assert.ok(!cfg.rooms.Okayama.transporters.some((t) => t.gridX === day.gridX && t.gridY === day.gridY), 'he stands on a seam');
        assert.ok(Object.entries(damian.states).every(([date, s]) => date === '2025-11-12' || !s.present) && damian.present === false, 'he is there that day only');
        // ...and nowhere else that day: Hakata's platform has let him go
        for (const [key, r] of Object.entries(cfg.rooms)) {
            if (key === 'Okayama') continue;
            const other = ((r.npcs || []).find((n) => n.name === 'Damian') || {}).states;
            assert.ok(!other || !other['2025-11-12'] || other['2025-11-12'].present === false, `Damian 2025-11-12 is also in ${key}`);
        }
        // the day after he is in front of Himeji's keep, as before
        const next = cfg.rooms.Himeji.npcs.find((n) => n.name === 'Damian').states['2025-11-13'];
        assert.ok(next.present && next.posts.map((p) => p.id).join() === '754');
        assert.ok(damian.states['2025-11-13'] && damian.states['2025-11-13'].present === false, 'he is still in Okayama the day after');
    });

    test('Okayama: Momotaro, the Bizen-ware stall and the cranes answer a bump; it is walked to, with no station, and is its own small place on the Map (#267)', () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const I = game('Interactions');
        const { world, config } = worldWith(false);
        const sizeOf = (key) => world.cells(key);
        const says = (x, y) => { const hit = I.find(config.rooms.Okayama, config.rooms.Okayama, x, y, { sizeOf, group: 'flavour' }); return hit && [hit.kind, hit.say]; };
        // the statue on the plaza where the avenue ends: bumped on its plinth, from the paving all round it
        const [mx, my] = at('Okayama', 'okayama-momotaro_0_0');
        assert.deepStrictEqual([mx, my, ...sizeOf('okayama-momotaro_0_0')], [8, 17, 2, 3]);
        const momotaro = ['momotaro', 'momotaro the peach boy, with his dog, monkey and pheasant. the ogres never stood a chance'];
        for (const x of [mx, mx + 1]) {
            assert.ok(solid('Okayama', x, my + 2) && !solid('Okayama', x, my + 3) && !solid('Okayama', x, my + 1), `the statue's plinth at ${x}`);
            assert.deepStrictEqual(says(x, my + 2), momotaro);
            assert.strictEqual(name(layer('Okayama', 'Floor')[`${x},${my + 3}`]).split('_')[0], 'flat-grey-brick-autotile', 'the statue is not on the plaza');
        }
        // the stall beside the pavement: an open counter, bumped from the avenue's north pavement
        const [sx, sy] = at('Okayama', 'okayama-bizen-stall_0_0');
        assert.deepStrictEqual([sx, sy, ...sizeOf('okayama-bizen-stall_0_0')], [15, 15, 3, 3]);
        const stall = ['bizen-stall', 'bizen ware: no glaze, two weeks in the kiln, no two alike. beer tastes better from it, they say'];
        for (let x = sx; x < sx + 3; x++) {
            assert.ok(solid('Okayama', x, sy + 2) && !solid('Okayama', x, sy + 3), `the stall's counter at ${x}`);
            assert.deepStrictEqual(says(x, sy + 2), stall);
        }
        // a crane on the lawn
        const crane = ['crane', 'a red-crowned crane. it looks at you, then at the pond, and chooses the pond'];
        for (const [x, y] of sprites.Okayama['okayama-crane_0_0']) assert.deepStrictEqual(says(x, y + 1), crane);
        // you walk to Okayama: no station, no railway (the train's row is Osaka's), no door but the seam into
        // Himeji, nothing borrowed from Hokuriku's own art, no ordinary sealed building, no bin
        assert.deepStrictEqual(Object.values(cfg.stations).filter((s) => s.town === 'Okayama'), [], 'you walk to Okayama');
        assert.ok(!Object.keys(cfg.rooms).some((k) => /^Okayama./.test(k)), 'Okayama has a station or an interior');
        assert.ok(cfg.rooms.Okayama.transporters.length === 5 && cfg.rooms.Okayama.transporters.every((t) => t.targetRoom === 'Himeji' && t.hidden), 'Okayama has a door that is not a seam');
        assert.ok(!Object.keys(sprites.Okayama).some((k) => /^train-track/.test(k)), 'Okayama has a railway');
        assert.deepStrictEqual(Object.keys(sprites.Okayama).filter((k) => /^(hokuriku|kanazawa|shirakawa|toyama)-/.test(k)), [], 'Okayama wears another town\'s art');
        assert.deepStrictEqual(Object.keys(sprites.Okayama).filter((k) => /rubbish-bin/.test(k)), []);
        assert.deepStrictEqual(Object.keys(sprites.Okayama).filter((k) => /^(house-|building-|machiya|highrise|seven-eleven|himeji-)/.test(k)), [], 'Okayama has a building that is not one of its own places');
        for (const k of ['okayama-keep', 'okayama-bridge', 'okayama-bank-rock', 'okayama-crane', 'okayama-momotaro', 'okayama-bizen-stall', 'okayama-fingerpost']) {
            assert.ok(sprites.Okayama[`${k}_0_0`] && `${k}_0_0` in cfg.spriteMetadata, `Okayama has no ${k}`);
        }
        // on the Map it is a small place of its own, where it is in Japan: west of Himeji, on Honshu
        const place = cfg.places.Okayama;
        assert.deepStrictEqual(place, { geo: [133.92, 34.66], label: 'Okayama', minor: true });
        assert.ok(place.geo[0] < cfg.places.Himeji.geo[0], 'Okayama is west of Himeji');
    });

    // Nara (#268): reached on foot from Osaka; `walkable` is what can be walked to from Osaka's avenue, stitched
    const fromOsaka = () => {
        const { world } = worldWith(true);
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        return (x, y) => { const c = world.roomManager.resolve('Nara', x, y); return seen.has(`${c.x},${c.y}`); };
    };

    test('Nara: the Great Buddha Hall stands over its court behind the Nandaimon, is looked up at from in front, and nobody walks behind it (#268)', () => {
        const walkable = fromOsaka();
        // the hall: twelve cells by eight, two rows of wood behind it, its art exactly its footprint, solid all over
        const [hx, hy] = at('Nara', 'nara-daibutsuden_0_0');
        assert.deepStrictEqual([hx, hy], [31, 2]);
        const png = fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'nara-daibutsuden_0_0.png'));
        assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [768, 512]);
        for (let x = hx; x < hx + 12; x++) for (let y = hy; y < hy + 8; y++) assert.ok(!walkable(x, y), `the hall can be walked onto at ${x},${y}`);
        for (let x = 0; x < SIZE.Nara[0]; x++) for (const y of [0, 1]) assert.ok(!walkable(x, y), `the wood behind the hall can be walked into at ${x},${y}`);
        // the earthen wall in front of the court is crossed through the gate's two middle columns alone
        assert.deepStrictEqual(at('Nara', 'nara-nandaimon_0_0'), [34, 12]);
        for (let x = 25; x <= 46; x++) {
            const way = x === 36 || x === 37;
            assert.strictEqual(walkable(x, 14) || walkable(x, 15), way, `the wall at column ${x}`);
        }
        for (let y = 10; y <= 17; y++) assert.ok(walkable(36, y) && walkable(37, y), `the axis from the court to the plaza is shut at row ${y}`);
        // the camera looks up at all of it from the cell the blog pipeline stands a visitor on, and from beside it
        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView'), look = realConfig().game.lookUp, G = 64;
        assert.strictEqual(look.sprites['nara-daibutsuden'], 0, 'the hall is not a landmark the camera looks up at');
        const [mark] = LandmarkView.index([{ key: 'nara-daibutsuden_0_0', left: hx * G, top: hy * G, width: 768, height: 512 }], look.sprites, G);
        const [vx, vy] = [hx + 4, hy + 8];
        assert.deepStrictEqual([vx, vy], [35, 10]);
        const cells = [[35, 10], [34, 10], [36, 10], [35, 11]];
        for (const [x, y] of cells) {
            assert.ok(walkable(x, y), `nobody can stand at ${x},${y} in front of the hall`);
            for (const view of [{ viewH: 960, bar: 40, deadzone: 256, foot: 128 }, { viewH: 480, bar: 46, deadzone: 128, foot: 188 }]) {
                const a = LandmarkView.aim(Object.assign({ x: x * G + 32, y: y * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side }, view));
                assert.ok(a.weight === 1 && a.offset > 0, `the camera does not look up from ${x},${y}`);
            }
        }
        // the desktop view holds the whole hall from that cell: its top is under the bar
        const desk = LandmarkView.aim({ x: vx * G + 32, y: vy * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade, side: look.side,
            viewH: 960, bar: 40, deadzone: 256, foot: 128 });
        assert.ok(vy * G + 32 - desk.offset - 960 / 2 + 40 <= hy * G, 'the top of the hall is cut off on desktop');
        // the blog pipeline's labels for the hall, the gate, the stall, the deer and the shrine
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        for (const [key, label, dx, dy, cell] of [['nara-daibutsuden_', 'the Great Buddha Hall', 4, 8, [35, 10]], ['nara-nandaimon_', 'the Nandaimon gate', 1, 4, [35, 16]],
            ['nara-senbei-stall_', 'the deer cracker stall', 0, 2, [41, 18]], ['nara-deer-stag_', 'the deer of Nara Park', 1, 0, [13, 29]],
            ['shrine-building', 'Kasuga Taisha', 2, 6, [45, 32]]]) {
            assert.ok(tool.includes(`('${key}', '${label}', (${dx}, ${dy}), {'rooms': ('Nara',)})`), `LANDMARKS has no row for ${label}`);
            const [sx, sy] = Object.entries(sprites.Nara).find(([k]) => k.startsWith(key))[1].slice().sort((a, b) => `${a}` < `${b}` ? -1 : 1)[0];
            assert.deepStrictEqual([sx + dx, sy + dy], cell, label);
            assert.ok(walkable(sx + dx, sy + dy), `${label}: nobody can walk to its visitor's cell ${sx + dx},${sy + dy}`);
        }
    });

    test('Nara: Kasuga Taisha is entered through its torii and up an approach of stone lanterns, and nothing leads round behind it (#268)', () => {
        const walkable = fromOsaka();
        // the door, into the worship hall named for it, and back out to the cell in front
        const door = cfg.rooms.Nara.transporters.find((t) => t.targetRoom === 'ShrineNara1');
        assert.deepStrictEqual(door && [door.gridX, door.gridY, door.hidden], [44, 30, true]);
        const hall = cfg.rooms.ShrineNara1;
        assert.strictEqual(hall.name, 'Kasuga Taisha');
        const out = hall.transporters.filter((t) => t.targetRoom === 'Nara');
        assert.ok(out.length && out.every((t) => t.targetX === 44 && t.targetY === 31), 'the worship hall does not lead back to the cell in front');
        assert.ok(walkable(44, 31), 'nobody can walk to Kasuga Taisha from Osaka');
        // nineteen lanterns, the last at the plaza's south-east corner: the cell behind the shrine's roof is closed
        assert.strictEqual(sprites.Nara['nara-stone-lantern_0_0'].length, 19);
        assert.ok(!walkable(42, 24) && walkable(42, 23), 'the lantern at the plaza\'s corner');
        for (let x = 35; x <= 46; x++) for (const y of [24, 25]) assert.ok(!walkable(x, y), `a way round behind the shrine at ${x},${y}`);
        // the torii: walked under on its middle two columns, its posts solid
        const [tx, ty] = at('Nara', 'nara-kasuga-torii_0_0');
        assert.deepStrictEqual([tx, ty], [31, 24]);
        for (let y = ty; y < ty + 4; y++) {
            assert.ok(walkable(tx + 1, y) && walkable(tx + 2, y), `the torii's way is shut at row ${y}`);
            assert.ok(solid('Nara', tx, y) && solid('Nara', tx + 3, y), `the torii's posts at row ${y}`);
        }
        // the district's three areas, for the blog pipeline
        assert.deepStrictEqual(cfg.districts.Nara.map((d) => d.key).sort(), ['kasuga', 'nara-park', 'todaiji']);
        const d = Object.fromEntries(cfg.districts.Nara.map((x) => [x.key, x]));
        assert.deepStrictEqual(d.kasuga.spots.slice().sort(), ['Kasuga Taisha', 'the shrine']);
        assert.deepStrictEqual(d['nara-park'].spots, ['the deer of Nara Park']);
        assert.deepStrictEqual(d.todaiji.spots.slice().sort(), ['the Great Buddha Hall', 'the Nandaimon gate', 'the deer cracker stall']);
    });

    test('Nara: Damian\'s post of 14 November 2025 stands in front of the Great Buddha Hall, not on Osaka\'s canal bank (#268)', () => {
        const walkable = fromOsaka();
        const damian = cfg.rooms.Nara.npcs.find((n) => n.name === 'Damian');
        const day = damian && damian.states['2025-11-14'];
        assert.ok(day && day.present === true, 'Damian is not in Nara on 2025-11-14');
        assert.deepStrictEqual([day.gridX, day.gridY, day.photo, day.posts.map((p) => p.id).join()], [35, 10, '764', '764']);
        assert.ok(walkable(day.gridX, day.gridY), 'nobody can walk to him');
        assert.ok([[-1, 0], [1, 0], [0, 1], [0, -1]].filter(([dx, dy]) => walkable(day.gridX + dx, day.gridY + dy)).length >= 2, 'there is no room to stand beside him');
        assert.ok(!cfg.rooms.Nara.transporters.some((t) => t.gridX === day.gridX && t.gridY === day.gridY), 'he stands on a seam');
        assert.ok(Object.entries(damian.states).every(([date, s]) => date === '2025-11-14' || !s.present) && damian.present === false, 'he is there that day only');
        for (const [key, r] of Object.entries(cfg.rooms)) {
            if (key === 'Nara') continue;
            const other = ((r.npcs || []).find((n) => n.name === 'Damian') || {}).states;
            assert.ok(!other || !other['2025-11-14'] || other['2025-11-14'].present === false, `Damian 2025-11-14 is also in ${key}`);
        }
    });

    test('Nara: the deer, the stall, the lanterns, the gate, the hall and the torii answer a bump; it is walked to, with no station, and is its own small place on the Map (#268)', () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const I = game('Interactions');
        const { world, config } = worldWith(false);
        const sizeOf = (key) => world.cells(key);
        const says = (x, y) => { const hit = I.find(config.rooms.Nara, config.rooms.Nara, x, y, { sizeOf, group: 'flavour' }); return hit && [hit.kind, hit.say]; };
        const resting = ['deer', 'a deer, resting. it has seen ten thousand visitors today and you are not the interesting one'];
        const LINES = {
            'nara-deer-doe_0_0': [resting, [0, 0]], 'nara-deer-stag_0_0': [resting, [0, 0]],
            'nara-deer-bow_0_0': [['deer-bow', 'the deer bows. it wants a cracker. it bows again, lower, and stands on your foot'], [0, 0]],
            'nara-senbei-stall_0_0': [['senbei-stall', 'deer crackers, 200 yen a stack. every deer in the park knows the sound of the paper band'], [0, 1]],
            'nara-stone-lantern_0_0': [['stone-lantern', 'a stone lantern, furred with moss. there are two thousand along this path, each one given by somebody'], [0, 1]],
            'nara-nandaimon_0_0': [['nandaimon', 'the great south gate. two wooden guardians, eight metres tall, glare out of the dark either side'], [1, 3]],
            'nara-daibutsuden_0_0': [['great-buddha-hall', 'the great buddha hall. fifteen metres of bronze sit inside, and a pillar with a hole the size of his nostril'], [4, 7]],
            'nara-kasuga-torii_0_0': [['torii', 'the vermilion gate of kasuga taisha. the deer walk through without bowing'], [0, 3]],
        };
        for (const [key, [line, [dx, dy]]] of Object.entries(LINES)) {
            const placed = sprites.Nara[key] || [];
            assert.ok(placed.length, `Nara has no ${key}`);
            for (const [x, y] of placed) {
                assert.ok(solid('Nara', x + dx, y + dy), `${key} at ${x},${y}: the cell bumped is not solid`);
                assert.deepStrictEqual(says(x + dx, y + dy), line, `${key} at ${x},${y}`);
            }
        }
        assert.deepStrictEqual([sprites.Nara['nara-deer-doe_0_0'].length, sprites.Nara['nara-deer-stag_0_0'].length, sprites.Nara['nara-deer-bow_0_0'].length], [5, 4, 3]);
        // you walk to Nara: no station, no railway, no door but the seams and the shrine's, nothing borrowed
        // from Hokuriku's own art, no ordinary sealed building, no bin
        assert.deepStrictEqual(Object.values(cfg.stations).filter((st) => st.town === 'Nara'), [], 'you walk to Nara');
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^Nara/.test(k)), ['Nara'], 'Nara has a station or an interior of its own name');
        assert.ok(cfg.rooms.Nara.transporters.every((t) => t.hidden && ['Osaka', 'ShrineNara1'].includes(t.targetRoom)), 'Nara has a door that is not a seam or the shrine\'s');
        assert.ok(!Object.keys(sprites.Nara).some((k) => /^train-track/.test(k)), 'Nara has a railway');
        assert.deepStrictEqual(Object.keys(sprites.Nara).filter((k) => /^(hokuriku|kanazawa|shirakawa|toyama)-/.test(k)), [], 'Nara wears another town\'s art');
        assert.deepStrictEqual(Object.keys(sprites.Nara).filter((k) => /rubbish-bin/.test(k)), []);
        assert.deepStrictEqual(Object.keys(sprites.Nara).filter((k) => /^(house-|building-|machiya|highrise|seven-eleven|himeji-|okayama-keep)/.test(k)), [], 'Nara has a building that is not one of its own places');
        // on the Map it is a small place of its own, Todaiji's place in Japan: east of Osaka, on Honshu
        assert.deepStrictEqual(cfg.places.Nara, { geo: [135.84, 34.69], label: 'Nara', minor: true });
        assert.ok(cfg.places.Nara.geo[0] > cfg.places.Osaka.geo[0], 'Nara is east of Osaka');
    });

    test('Nara: its north edge waits for Lake Biwa - the river and the towpath stop two rows short of it, and nothing is open there (#268)', () => {
        const walkable = fromOsaka();
        assert.ok(!BUILT.includes('LakeBiwa'), 'Lake Biwa is built: this test is #269\'s to change');
        assert.ok(/\('Nara', 'n', N_TOWPATH, 'LakeBiwa', L_TOWPATH\)/.test(py), 'kansai.py has no join from Nara\'s towpath to Lake Biwa');
        const water = layer('Nara', 'Water'), floor = layer('Nara', 'Floor');
        for (const x of [20, 21, 22]) {
            assert.ok(/^pond-autotile_/.test(name(water[`${x},2`])) && !(`${x},1` in water), `the river's head at column ${x}`);
        }
        assert.deepStrictEqual([20, 21, 22].map((x) => name(water[`${x},2`])), ['pond-autotile_edge-n', 'pond-autotile_edge-n', 'pond-autotile_corner-ne']);
        for (const x of [23, 24]) {
            assert.ok(/^gravel-autotile_/.test(name(floor[`${x},2`])) && !/^gravel/.test(name(floor[`${x},1`])), `the towpath's end at column ${x}`);
            assert.ok(walkable(x, 2), `the towpath's end at ${x},2 cannot be walked to`);
        }
        for (let x = 0; x < SIZE.Nara[0]; x++) for (const y of [0, 1]) assert.ok(!walkable(x, y), `Nara ${x},${y} is open on its north edge`);
        assert.ok(!Object.values(water).some((t) => name(t) === 'pond-autotile_corner-nw'), 'a pond corner the blog pipeline would read as "the pond"');
    });
};
