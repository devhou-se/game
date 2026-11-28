// Kansai (issue #255; #68, run 2): Osaka the town, and Himeji walked to from it along Canal-side Avenue -
// two districts of a third stitched city, KansaiCity. Three more districts are planned (tools/kansai.py).
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig, worldWith }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const DISTRICTS = ['Himeji', 'Osaka'];
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
    const O_AVENUE = [24, 25, 26, 27, 28], H_AVENUE = [18, 19, 20, 21, 22];

    test('Kansai is a third stitched city: Osaka and Himeji, placed as tools/kansai.py lays them out, with room left for the districts to come (#255)', () => {
        const city = cfg.cities.KansaiCity;
        assert.ok(city, 'config cities has no KansaiCity');
        assert.deepStrictEqual(city.rooms.map((m) => m.room).sort(), BUILT.slice().sort(), 'the city is the districts kansai.py says are built');
        assert.deepStrictEqual(BUILT.slice().sort(), DISTRICTS);
        assert.strictEqual(city.name, 'Kansai');
        assert.ok(city.backdrop && city.backdrop.floor && city.backdrop.tree, 'the gaps between the districts need a woodland backdrop');
        assert.deepStrictEqual(DISTRICTS.map((r) => cfg.rooms[r].name), ['Himeji', 'Osaka'], 'the HUD names');
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
        assert.deepStrictEqual(unbuilt.sort(), ['LakeBiwa', 'Nara', 'Okayama']);
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

    test('Kansai: the seam lines up - the avenue and the canal carry straight across into Himeji, and each seam cell has its ?stitch=0 transporter both ways (#255)', () => {
        const pairs = DISTRICTS.flatMap((r) => seams(r).map((t) => [r, t]));
        assert.strictEqual(pairs.length, 5 + 5, 'the five avenue cells Osaka<->Himeji, each way');
        assert.deepStrictEqual(seams('Osaka').map((t) => [t.gridX, t.gridY]), O_AVENUE.map((y) => [0, y]));
        assert.deepStrictEqual(seams('Himeji').map((t) => [t.gridX, t.gridY]), H_AVENUE.map((y) => [size('Himeji')[0] - 1, y]));
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
        // the only open cells on a district's edge are the seam cells - and the east end of Osaka's avenue,
        // where there is nothing to step out to. Himeji's west edge is closed until Okayama is built
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
        assert.ok(!edgeOpen('Himeji').some((xy) => xy.startsWith('0,')), "Himeji's west edge is open");
        assert.deepStrictEqual(edgeOpen('Osaka'), mine('Osaka').concat(O_AVENUE.map((y) => `49,${y}`)).sort(), 'Osaka: an edge cell is open that is not a seam or the east end of the avenue');
        const { world } = worldWith(true);
        for (const y of O_AVENUE) {
            world.enter('Osaka', 49, y);
            assert.strictEqual(world.step('e').moved, false, `a step east off Osaka (49,${y}) moves the player`);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Osaka', 49, y]);
        }
    });

    test('Kansai: the moat is the west end of Osaka\'s canal - the two declared waterways sail as one run across the seam (#255)', () => {
        if (game('typeof AmbientBoats') === 'undefined') load('AmbientBoats.js');
        const plain = (v) => JSON.parse(JSON.stringify(v));
        const runs = DISTRICTS.flatMap((r) => (cfg.rooms[r].waterways || []).map((w) => {
            assert.strictEqual(w.axis, 'h', `${r}'s waterway`);
            return { axis: 'h', from: w.from + AT[r][0], to: w.to + 1 + AT[r][0], band0: w.row + AT[r][1], band1: w.row + AT[r][1] + w.rows,
                under: (w.under || []).map(([a, b]) => [a + AT[r][0], b + 1 + AT[r][0]]) };
        }));
        assert.strictEqual(runs.length, 2, 'one waterway in each district');
        const [moat, canal] = runs;
        assert.deepStrictEqual([moat.to, moat.band0, moat.band1], [canal.from, canal.band0, canal.band1], 'the moat ends where the canal starts, on its rows');
        const joined = plain(game('AmbientBoats').joinRuns(runs, 1));
        assert.strictEqual(joined.length, 1, 'a boat would fade out at the seam');
        assert.deepStrictEqual([joined[0].from, joined[0].to, joined[0].band0, joined[0].band1], [AT.Himeji[0] + 7, AT.Osaka[0] + SIZE.Osaka[0], canal.band0, canal.band1]);
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

    test('Kansai is one walkable room: Osaka -> the keep terrace -> Koko-en -> Osaka on foot, stitched and with ?stitch=0 (#255)', () => {
        const [kx, ky] = at('Himeji', 'himeji-keep_0_0'), [gx, gy] = at('Himeji', 'himeji-kokoen-gate_0_0');
        const stops = [['Osaka', 3, 26],                                // on the avenue, by the fingerpost
            ['Himeji', kx + 4, ky + 9],                                  // the terrace in front of the keep: over the bridge, up the steps
            ['Himeji', gx + 2, gy + 5],                                  // inside Koko-en, through its gate
            ['Osaka', 3, 26]];
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            world.enter(...stops[0]);
            if (stitch) {
                assert.strictEqual(world.here().city, 'KansaiCity', 'Osaka is entered as the city room');
                const city = rm.rooms.KansaiCity;
                assert.deepStrictEqual([city.worldWidth / 64, city.worldHeight / 64], [SIZE.Himeji[0] + SIZE.Osaka[0], SIZE.Osaka[1]]);
                assert.strictEqual(city.depthScale, 1, 'the city is short enough that Y-sorted depths need no squeeze');
                // the railway is Osaka's: it carries on west over the wood above Himeji, in the city's backdrop
                const track = city.layers.filter((l) => /^Backdrop/.test(l.name)).flatMap((l) => Object.entries(l.tiles))
                    .filter(([, t]) => /^train-track/.test(t)).map(([xy]) => xy.split(',').map(Number));
                assert.strictEqual(track.length, SIZE.Himeji[0], 'the track is not carried on to the city\'s west edge');
                assert.ok(track.every(([x, y]) => x < SIZE.Himeji[0] && y === 4), 'the track runs two rows above Himeji\'s top row');
            } else {
                assert.strictEqual(world.here().city, null);
            }
            let fades = 0, crossings = 0;
            const walk = (room, x, y) => {
                if (!stitch && world.here().room !== room) {
                    // not there yet: walk to the nearest seam (stitched, the path below does it in one)
                    const seam = seams(world.here().room).map((t) => ({ t, route: world.path(t.gridX, t.gridY) })).filter((s) => s.route)
                        .sort((a, b) => a.route.length - b.route.length)[0];
                    assert.ok(seam, `${tag}: no seam can be walked to from ${world.here().room}`);
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
            // out along the avenue and home the same way: two district changes
            assert.deepStrictEqual([fades, crossings], stitch ? [0, 2] : [2, 0], `${tag}: fades, crossings`);
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

    test('Himeji: Koko-en is a walled garden through its gate, with a pond that is the garden\'s and not the moat (#255)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        world.enter('Osaka', 3, 26);
        const seen = world.reachable();
        const walkable = (x, y) => { const c = rm.resolve('Himeji', x, y); return seen.has(`${c.x},${c.y}`); };
        const [gx, gy] = at('Himeji', 'himeji-kokoen-gate_0_0');
        assert.deepStrictEqual([gx, gy], [20, 23]);
        // the wall runs the garden's whole north side; the gateway (two cells) is the only way in
        for (let x = 5; x <= 41; x++) {
            const way = x === gx + 1 || x === gx + 2;
            assert.strictEqual(walkable(x, 24) || walkable(x, 25), way, `Koko-en's wall at column ${x}`);
        }
        assert.ok(walkable(gx + 1, gy + 5), 'LANDMARKS stands Koko-en\'s visitor here');
        // the loop round the pond, and over it by the bridge
        for (const [x, y] of [[8, 27], [38, 27], [8, 35], [38, 35], [22, 29], [22, 31], [23, 32], [22, 34]]) assert.ok(walkable(x, y), `Koko-en: nobody can walk to ${x},${y}`);
        const pond = Object.entries(layer('Himeji', 'Water')).filter(([xy]) => Number(xy.split(',')[1]) > 22);
        assert.ok(pond.length >= 40 && pond.every(([, t]) => /^pond-autotile_/.test(name(t))), 'the garden has no pond');
        assert.ok(pond.filter(([xy]) => !solid('Himeji', ...xy.split(',').map(Number))).map(([xy]) => xy).sort().join(' ') === '22,31 22,32 23,31 23,32', 'the pond is crossed by its bridge alone');
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

    test('Kansai: a fingerpost stands by the seam on each side and says where the avenue goes; Himeji is its own place (#255)', () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const I = game('Interactions');
        const { world, config } = worldWith(false);
        const sizeOf = (key) => world.cells(key);
        const line = 'west: himeji castle and koko-en. east: osaka, dotonbori';
        for (const [room, edge] of [['Osaka', 0], ['Himeji', size('Himeji')[0] - 1]]) {
            const posts = sprites[room]['kansai-fingerpost_0_0'] || [];
            assert.strictEqual(posts.length, 1, `${room} has ${posts.length} fingerposts`);
            const [x, y] = posts[0];
            assert.ok(Math.abs(x - edge) <= 4, `${room}'s fingerpost at ${x},${y} is not by the seam`);
            assert.deepStrictEqual(sizeOf('kansai-fingerpost_0_0'), [1, 2]);
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
        assert.ok(cfg.rooms.Himeji.transporters.every((t) => t.targetRoom === 'Osaka' && t.hidden), 'Himeji has a door that is not a seam');
        assert.ok(!Object.keys(sprites.Himeji).some((k) => /^train-track/.test(k)), 'Himeji has a railway');
        assert.deepStrictEqual(Object.keys(sprites.Himeji).filter((k) => /^(hokuriku|kanazawa|shirakawa|toyama)-/.test(k)), [], 'Himeji wears another town\'s art');
        assert.deepStrictEqual(Object.keys(sprites.Himeji).filter((k) => /rubbish-bin/.test(k)), []);
        for (const k of ['himeji-keep', 'himeji-turret', 'himeji-gate', 'himeji-bridge', 'himeji-kokoen-gate', 'himeji-wall']) {
            assert.ok(sprites.Himeji[`${k}_0_0`] && `${k}_0_0` in cfg.spriteMetadata, `Himeji has no ${k}`);
        }
        // Osaka's railway runs off its west edge now: no bushes on the corridor's end, track to the edge
        for (const y of [3, 4, 5]) {
            for (const l of cfg.rooms.Osaka.layers) assert.ok(!/^shrub/.test(name((l.tiles || {})[`0,${y}`])), `a bush caps Osaka's railway at (0,${y}) in ${l.name}`);
        }
        assert.ok(/^train-track/.test(name(layer('Osaka', 'Over Floor')['0,4'])), 'no track on Osaka (0,4)');
        // on the Map it is a small place of its own, where it is in Japan: west of Osaka, on Honshu
        const place = cfg.places.Himeji;
        assert.deepStrictEqual(place, { geo: [134.69, 34.82], label: 'Himeji', minor: true });
        assert.ok(place.geo[0] < cfg.places.Osaka.geo[0], 'Himeji is west of Osaka');
        assert.ok(!('KansaiCity' in cfg.places), 'the stitched city has no dot of its own: its towns do');
    });
};
