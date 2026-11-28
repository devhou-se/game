// Karuizawa (issues #68, #256; #260 is part 1): the fifth district of the stitched TokyoCity, out of
// Tokyo's west gate. tools/generate_karuizawa.py builds the room and reopens the gate e3cb4d0d fenced.
// Part 2 (#261) is Kyu-Karuizawa Ginza: three shopfronts where the road in turns north, each with a shop
// floor behind its door (tools/generate_houses.py --shops Karuizawa).
// #262 is part 3: Shiraito Falls over its pool, the bus stop, the corn stall and the larch woods.
// #263 is part 4: the two posts about the place are told there, and Bailey starts 2 November beside Julia.
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig, worldWith }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const KEY = 'Karuizawa', HOST = 'Tokyo', BRICK = 'flat-grey-brick-autotile_center';
    const W = 48, H = 40;
    const layer = (room, n) => ((cfg.rooms[room].layers || []).find((l) => l.name === n) || {}).tiles || {};
    const solid = (room, x, y) => `${x},${y}` in layer(room, 'Colliders');
    const tilesOf = (room) => (cfg.rooms[room].layers || []).flatMap((l) => Object.entries(l.tiles || {}).map(([xy, t]) => [name(t), xy, l.name]));
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const offset = Object.fromEntries(cfg.cities.TokyoCity.rooms.map((m) => [m.room, m]));
    const seam = (x, y, targetRoom, targetX, targetY) => ({ gridX: x, gridY: y, targetRoom, targetX, targetY, hidden: true });
    const SPOTS = ['Shiraito Falls', 'the corn stall', 'the road from Tokyo'];      // what the blog pipeline can name here

    test('Karuizawa is the fifth district of TokyoCity, west of Tokyo, and a small place with a dot of its own on the Map (#260)', () => {
        assert.deepStrictEqual(cfg.cities.TokyoCity.rooms.map((m) => m.room), ['Tokyo', 'Market', 'Palace', 'Park', KEY, 'Shinjuku']);
        const room = cfg.rooms[KEY];
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [KEY, W, H]);
        assert.ok(!room.interior, 'it is an outdoor room');
        // where it stands: its east edge on Tokyo's west edge, its gate rows 34-35 on Tokyo's rows 41-42
        assert.deepStrictEqual([offset[KEY].x - offset[HOST].x, offset[KEY].y - offset[HOST].y], [-W, 7]);
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        assert.deepStrictEqual(world.maps.find((m) => m.fileName === 'gamev2/tiled/karuizawa.tmj'),
            { fileName: 'gamev2/tiled/karuizawa.tmj', x: -W * 64, y: 8 * 64, width: W * 64, height: H * 64 });
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        assert.deepStrictEqual(map.rooms[KEY] && map.rooms[KEY].cells, [W, H], 'world-map.json has no Karuizawa: run make_worldmap.py');
        // the Map: a room that is its own place wins over the city it is stitched into
        assert.deepStrictEqual(cfg.places[KEY], { geo: [138.63, 36.35], label: KEY, minor: true });
        if (game('typeof Places') === 'undefined') load('utils/Places.js');
        const P = game('Places'), config = realConfig();
        assert.strictEqual(P.of(config, KEY), KEY);
        assert.strictEqual(P.of(config, HOST), 'TokyoCity', 'Tokyo is still Tokyo\'s dot');
        const dot = P.list(config).find((p) => p.key === KEY);
        assert.deepStrictEqual(plain([dot.label, dot.minor, dot.rooms]), [KEY, true, [KEY]]);
        // the studio keeps the city at Tokyo's dot: the district that is a place of its own does not pull it west
        const at = game('WorldModel.geoOf')(config, ['TokyoCity', HOST, KEY]);
        assert.deepStrictEqual(plain(at.TokyoCity), plain(at[HOST]));
        assert.ok(at[KEY][0] < at[HOST][0] && at[KEY][1] < at[HOST][1], 'Karuizawa is north-west of Tokyo');
        // it is walked to, not ridden to: no station serves it, and a traveller sets foot inside the gate
        assert.ok(!Object.values(cfg.stations).some((st) => st.town === KEY), 'a station serves Karuizawa');
        assert.deepStrictEqual(plain(P.arrival(config, KEY)), { room: KEY, x: 44, y: 34 });
        // no track tile: the city's ambient train runs on the topmost track row of the whole city room
        assert.deepStrictEqual(tilesOf(KEY).filter(([k]) => k.startsWith('train-track')), []);
        assert.deepStrictEqual(room.transporters.map((t) => t.targetRoom), [HOST, HOST, 'ShopKaruizawa1', 'ShopKaruizawa2', 'ShopKaruizawa3'],
            'the gate and the three shop doors are the only ways in or out');
        // one generator builds the room and owns the gate cells of the ported Tokyo map
        const py = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/GENERATORS \+= \['generate_karuizawa'\]/.test(py) && /ART_TOOLS \+= \['generate_karuizawa_art'\]/.test(py));
    });

    test('Karuizawa: the gate is Tokyo\'s west gate, open both ways on the same brick, and the only open cells on the room\'s edge (#260)', () => {
        const gate = cfg.rooms[KEY].transporters.filter((t) => t.targetRoom === HOST);
        assert.deepStrictEqual(gate, [seam(W - 1, 34, HOST, 3, 41), seam(W - 1, 35, HOST, 3, 42)]);
        assert.deepStrictEqual(cfg.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY),
            [seam(0, 41, KEY, W - 4, 34), seam(0, 42, KEY, W - 4, 35)]);
        const floor = (room, x, y) => name(layer(room, 'Floor')[`${x},${y}`]);
        for (const [room, other] of [[KEY, HOST], [HOST, KEY]]) {
            for (const t of cfg.rooms[room].transporters.filter((s) => s.targetRoom === other)) {
                assert.ok(!solid(room, t.gridX, t.gridY) && !solid(other, t.targetX, t.targetY), `${room} ${t.gridX},${t.gridY}: the seam or its landing cell is solid`);
                // the cell across the edge is the same city cell + 1, the same ground, and it leads back
                const dx = t.gridX === 0 ? -1 : 1;
                const nx = t.gridX + offset[room].x + dx - offset[other].x, ny = t.gridY + offset[room].y - offset[other].y;
                const back = cfg.rooms[other].transporters.find((b) => b.gridX === nx && b.gridY === ny);
                assert.ok(back && back.targetRoom === room, `${room} ${t.gridX},${t.gridY}: no transporter back from ${other} ${nx},${ny}`);
                assert.deepStrictEqual([floor(room, t.gridX, t.gridY), floor(other, nx, ny)], [BRICK, BRICK], 'the same brick either side of the gate');
                assert.deepStrictEqual([t.targetX, t.targetY], [nx + dx * 3, ny], 'a seam lands three cells in from the neighbour\'s edge');
            }
        }
        // the brick turns to the packed-dirt road, which runs west and then north
        for (const [x, y] of [[46, 34], [46, 35], [30, 34], [14, 35], [14, 20], [15, 10]]) {
            assert.ok(floor(KEY, x, y).startsWith('dirt-outside-autotile_'), `no road at ${x},${y}`);
            assert.ok(!solid(KEY, x, y), `the road is blocked at ${x},${y}`);
        }
        // from the gate: plenty of room to walk in, and the only edge cells that can be reached are the gate's
        const todo = gate.map((t) => [t.gridX, t.gridY]);
        const seen = new Set(todo.map((c) => c.join()));
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (nx < 0 || ny < 0 || nx >= W || ny >= H || solid(KEY, nx, ny) || seen.has(`${nx},${ny}`)) continue;
                seen.add(`${nx},${ny}`); todo.push([nx, ny]);
            }
        }
        assert.ok(seen.size > 150, `only ${seen.size} cells can be walked`);
        const onEdge = (xy) => { const [x, y] = xy.split(',').map(Number); return x === 0 || y === 0 || x === W - 1 || y === H - 1; };
        assert.deepStrictEqual([...seen].filter(onEdge).sort(), [`${W - 1},34`, `${W - 1},35`]);
        // every cell is floored, and no road tile lies on an edge (the backdrop would grow a road out of it)
        for (let x = 0; x < W; x++) for (let y = 0; y < H; y++) assert.ok(floor(KEY, x, y), `no floor at ${x},${y}`);
        assert.deepStrictEqual(Object.keys(layer(KEY, 'Floor')).filter((xy) => onEdge(xy) && /^road-/.test(floor(KEY, ...xy.split(',').map(Number)))), []);
    });

    test('Karuizawa: Tokyo -> through the west gate -> up the road -> back on foot, stitched and with ?stitch=0 (#260)', () => {
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            const here = () => [world.here().room, world.here().x, world.here().y];
            let fades = 0, crossings = 0;
            const walk = (room, x, y) => {
                const to = rm.resolve(room, x, y);
                const route = world.path(to.x, to.y);
                assert.ok(route, `${tag}: no way on foot to ${room} ${x},${y} from ${here()}`);
                for (const dir of route) {
                    const r = world.step(dir);
                    assert.ok(r.moved, `${tag}: blocked on the way to ${room} ${x},${y}`);
                    if (r.transported) fades++;
                    if (r.crossed) crossings++;
                }
                assert.deepStrictEqual(here(), [room, x, y], tag);
            };
            world.enter(HOST, 6, 41);
            if (stitch) {
                assert.strictEqual(world.here().city, 'TokyoCity');
                const city = rm.rooms.TokyoCity;
                assert.deepStrictEqual([city.worldWidth / 64, city.worldHeight / 64], [165, 109], 'the city is 48 columns wider and no taller');
                assert.strictEqual(rm.resolve(HOST, 0, 0).x, W, 'Tokyo starts where Karuizawa ends');
                assert.strictEqual(rm.resolve(KEY, 0, 0).x, 0, 'Karuizawa is the west edge of the city');
                walk(KEY, 14, 12);
                assert.deepStrictEqual([fades, crossings], [0, 1], `${tag}: one district change on the way out, no fade`);
                walk(HOST, 6, 42);
                assert.deepStrictEqual([fades, crossings], [0, 2], `${tag}: and one on the way back`);
            } else {
                assert.strictEqual(world.here().city, null);
                walk(HOST, 1, 41);
                const out = world.step('w');
                assert.deepStrictEqual(plain(out.transported), { from: HOST, to: KEY }, `${tag}: the gate cell is the door`);
                assert.deepStrictEqual(here(), [KEY, 44, 34]);
                walk(KEY, 14, 12);
                walk(KEY, 46, 35);
                const back = world.step('e');
                assert.deepStrictEqual(plain(back.transported), { from: KEY, to: HOST });
                assert.deepStrictEqual(here(), [HOST, 3, 42]);
                assert.deepStrictEqual([fades, crossings], [0, 0], `${tag}: nothing else on the way is a door`);
            }
        }
    });

    test('Karuizawa: the fingerpost stands inside the gate and says what lies each way when bumped (#260)', () => {
        const posts = tilesOf(KEY).filter(([k]) => /fingerpost/.test(k));
        assert.deepStrictEqual(posts, [['karuizawa-fingerpost_0_0', '44,32', 'Collidables']], 'one fingerpost, the room\'s own');
        // its foot is on the verge beside the cell the gate lands you on: bumped from the road
        assert.deepStrictEqual([solid(KEY, 44, 33), solid(KEY, 44, 34)], [true, false]);
        assert.deepStrictEqual(cfg.spriteMetadata['karuizawa-fingerpost_0_0'], { anchorX: 0.5, anchorY: 0.25, frameCount: 1 }, 'one cell wide, two tall');
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const at = world.roomManager.resolve(KEY, 44, 34);
            world.enter(KEY, 44, 34);
            const bump = world.step('n');
            assert.deepStrictEqual(plain([bump.moved, bump.interaction.kind, bump.interaction.group]), [false, 'fingerpost', 'flavour']);
            assert.ok(/Tokyo/.test(bump.interaction.say) && /Karuizawa/.test(bump.interaction.say) && bump.interaction.say.length <= 100, bump.interaction.say);
            assert.deepStrictEqual([world.player.gridX, world.player.gridY], [at.x, at.y], 'the bump does not move you');
        }
        // no other town's sign is borrowed (the bus stop at the head of the road is the one eleven rooms share, #262),
        // and the blog pipeline has a named spot to stand somebody at
        assert.deepStrictEqual(tilesOf(KEY).filter(([k]) => /sign|bus-stop/.test(k)), [['bus-stop_0_0', '18,8', 'Collidables']]);
        const spots = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        assert.ok(spots.includes("('karuizawa-fingerpost_', 'the road from Tokyo', (-1, 1), {'rooms': ('Karuizawa',)})"));
        assert.deepStrictEqual(cfg.districts[KEY].map((d) => [d.key, d.spots]), [['larch-road', SPOTS]]);
    });

    // ---- #262: the head of the road. Cells are the room's own -------------------------------------------
    const FALLS = { x0: 12, y0: 3, x1: 19, y1: 5 }, POOL = { x0: 13, y0: 5, x1: 18, y1: 7 }, STALL = { x0: 19, y0: 6, x1: 21, y1: 7 };
    const cells = ({ x0, y0, x1, y1 }) => { const out = []; for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) out.push([x, y]); return out; };
    const near = (x, y) => [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]].filter(([nx, ny]) => nx >= 0 && ny >= 0 && nx < W && ny < H);
    // every cell that can be walked to from the gate, as the gate test counts them
    const onFoot = () => {
        const todo = cfg.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY).map((t) => [t.targetX, t.targetY]);   // where the gate lands you
        const seen = new Set(todo.map((c) => c.join()));
        while (todo.length) {
            for (const [nx, ny] of near(...todo.pop())) {
                if (solid(KEY, nx, ny) || seen.has(`${nx},${ny}`)) continue;
                seen.add(`${nx},${ny}`); todo.push([nx, ny]);
            }
        }
        return seen;
    };

    test('Karuizawa: Shiraito Falls stands over its pool at the head of the road, with the corn stall and the bus stop beside it (#262)', () => {
        const one = (key) => tilesOf(KEY).filter(([k]) => k === key).map(([, xy, l]) => [xy, l]);
        assert.deepStrictEqual(one('karuizawa-falls_0_0'), [['12,3', 'Collidables']]);
        assert.deepStrictEqual(one('karuizawa-corn-stall_0_0'), [['19,6', 'Collidables']]);
        assert.deepStrictEqual(one('bus-stop_0_0'), [['18,8', 'Collidables']]);
        const meta = (key, w, h) => assert.deepStrictEqual(cfg.spriteMetadata[key], { anchorX: 0.5 / w, anchorY: 0.5 / h, frameCount: 1 }, `${key} is not ${w}x${h} cells`);
        meta('karuizawa-falls_0_0', 8, 3); meta('karuizawa-corn-stall_0_0', 3, 2);
        meta('karuizawa-larch_0_0', 2, 3); meta('karuizawa-larch_0_1', 2, 4);
        for (const key of ['karuizawa-falls_0_0', 'karuizawa-corn-stall_0_0', 'karuizawa-larch_0_0', 'karuizawa-larch_0_1']) {
            assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', `${key}.png`)), `${key}.png is not drawn`);
            assert.ok(cfg.tileNames[key], `${key} has no name in the editor`);
        }
        // the pool: the shared pond, three rows, the top one under the falls. No north rim: its rocks would show
        // through the falling water, and a corner-nw tile would add the generic `the pond` spot beside the falls
        const water = layer(KEY, 'Water');
        assert.deepStrictEqual(Object.keys(water).sort(), cells(POOL).map((c) => c.join()).sort());
        for (const [xy, t] of Object.entries(water)) {
            assert.ok(/^pond-autotile_/.test(name(t)) && !/corner-n|edge-n/.test(name(t)), `${xy}: ${name(t)}`);
        }
        // nobody walks into the rock, the water, the stall or the stop, or round behind the stall
        for (const [x, y] of [...cells(FALLS), ...cells(POOL), ...cells(STALL), [18, 8], [20, 5], [21, 5]]) {
            assert.ok(solid(KEY, x, y), `${x},${y} can be walked into`);
        }
        // the road ends in the bay where the bus turns, under the stop
        for (const [x, y] of [[11, 9], [20, 10], [18, 9]]) {
            assert.ok(name(layer(KEY, 'Floor')[`${x},${y}`]).startsWith('dirt-outside-autotile_') && !solid(KEY, x, y), `no bay at ${x},${y}`);
        }
    });

    test('Karuizawa: the falls, the corn stall and the bus stop are reached on foot from the gate (#262)', () => {
        const seen = onFoot();
        const reached = (what, list) => { for (const [x, y] of list) assert.ok(seen.has(`${x},${y}`), `${what}: ${x},${y} cannot be walked to from the gate`); };
        reached('beside the falls\' west arm', [[12, 6], [11, 5]]);
        reached('the pool\'s bank', [[13, 8], [14, 8], [15, 8], [16, 8], [17, 8]]);
        reached('the stall\'s counter', [[19, 8], [20, 8], [21, 8]]);
        reached('beside and below the bus stop', [[17, 8], [18, 9]]);
        reached('the blog spots', [[13, 8], [21, 8]]);
        // each of the three has a cell to stand on beside it
        for (const [what, box] of [['falls', FALLS], ['stall', STALL], ['bus stop', { x0: 18, y0: 8, x1: 18, y1: 8 }]]) {
            assert.ok(cells(box).some(([x, y]) => near(x, y).some((c) => seen.has(c.join()))), `nobody can stand beside the ${what}`);
        }
        // ...and the walk is a real one, stitched and not: Tokyo's side of the gate to the falls, the stall, the stop
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager;
            world.enter(KEY, W - 4, 34);
            for (const [x, y] of [[12, 6], [20, 8], [18, 9]]) {
                const to = rm.resolve(KEY, x, y);
                const route = world.path(to.x, to.y);
                assert.ok(route, `${stitch ? 'stitched' : '?stitch=0'}: no way on foot to ${x},${y}`);
                for (const dir of route) assert.ok(world.step(dir).moved);
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [KEY, x, y]);
            }
        }
    });

    test('Karuizawa: bumping the falls\' rock arms and the stall says a line, bumping the pool fishes, and no bump does both (#262)', () => {
        const bumps = [
            [12, 6, 'n', 'waterfall', 'flavour'], [11, 5, 'e', 'waterfall', 'flavour'],      // the west arm, from below and from beside
            [15, 8, 'n', 'pond', 'pond'], [12, 6, 'e', 'pond', 'pond'],                      // the pool, from its bank and its west side
            [20, 8, 'n', 'corn-stall', 'flavour'],                                           // the stall's counter
            [18, 9, 'n', null, null],                                                        // the bus stop says nothing, as in every town
        ];
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            for (const [x, y, dir, kind, group] of bumps) {
                world.enter(KEY, x, y);
                const bump = world.step(dir);
                const tag = `${stitch ? 'stitched' : '?stitch=0'} ${x},${y} ${dir}`;
                assert.strictEqual(bump.moved, false, tag);
                assert.deepStrictEqual(plain(bump.interaction ? [bump.interaction.kind, bump.interaction.group] : [null, null]), [kind, group], tag);
                if (group === 'flavour') assert.ok(bump.interaction.say && bump.interaction.say.length <= 100, bump.interaction.say);
            }
        }
        // never both: a cell that is pool and falls at once (the pool's top row) has no open cell beside it
        const water = layer(KEY, 'Water');
        const both = cells(FALLS).filter(([x, y]) => `${x},${y}` in water);
        assert.strictEqual(both.length, 6);
        for (const [x, y] of both) assert.deepStrictEqual(near(x, y).filter(([nx, ny]) => !solid(KEY, nx, ny)), [], `${x},${y} is pool and falls, and can be bumped`);
    });

    test('Karuizawa: the woods are its own larches, and nothing in the room is one other town\'s (#262)', () => {
        const tiles = tilesOf(KEY);
        assert.deepStrictEqual(tiles.filter(([k]) => k.startsWith('tree-')), [], 'Tokyo\'s tree is still in the wood');
        const borrowed = tiles.filter(([k, , l]) => l === 'Collidables' && !/^karuizawa-/.test(k) && !['shrub-small-circle_0_0', 'bus-stop_0_0'].includes(k));
        assert.deepStrictEqual(borrowed, []);
        const count = (key) => tiles.filter(([k]) => k === key).length;
        assert.ok(count('karuizawa-larch_0_0') > 50 && count('karuizawa-larch_0_1') > 20, 'both larches make the wood');
        // the kit that is not its own is common to many rooms, not one town's
        for (const key of ['bus-stop_0_0', 'shrub-small-circle_0_0']) {
            const rooms = Object.keys(cfg.rooms).filter((r) => r !== KEY && tilesOf(r).some(([k]) => k === key));
            assert.ok(rooms.length >= 5, `${key} is in only ${rooms}`);
        }
        // the larches are stamped: their prefabs are built, and the wood kit knows how tall each stands
        const prefabs = fs.readFileSync(path.join(GV2, 'tools', 'make_prefabs.py'), 'utf8');
        for (const p of ['karuizawa-larch', 'karuizawa-larch-tall', 'karuizawa-falls', 'karuizawa-corn-stall']) {
            assert.ok(prefabs.includes(`'${p}':`) && fs.existsSync(path.join(GV2, 'tiled', 'prefabs', `${p}.tmj`)), `no prefab ${p}`);
        }
        assert.ok(/'karuizawa-larch': 3, 'karuizawa-larch-tall': 4/.test(fs.readFileSync(path.join(GV2, 'tools', 'hokuriku.py'), 'utf8')));
    });

    test('Karuizawa: the blog pipeline can stand somebody at Shiraito Falls and at the corn stall (#262)', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        assert.ok(py.includes("('karuizawa-falls_', 'Shiraito Falls', (1, 5), {'rooms': ('Karuizawa',)})"));
        assert.ok(py.includes("('karuizawa-corn-stall_', 'the corn stall', (2, 2), {'rooms': ('Karuizawa',)})"));
        assert.deepStrictEqual(cfg.districts[KEY].map((d) => [d.key, d.spots]), [['larch-road', SPOTS]]);
        assert.ok(/Shiraito Falls/.test(cfg.districts[KEY][0].description) && /corn/.test(cfg.districts[KEY][0].description));
        // where those rows put them: the tile cell plus the offset, an open cell inside the district that is not the road
        const seen = onFoot();
        const [bx0, by0, bx1, by1] = cfg.districts[KEY][0].bounds;
        for (const [x, y] of [[FALLS.x0 + 1, FALLS.y0 + 5], [STALL.x0 + 2, STALL.y0 + 2]]) {
            assert.ok(seen.has(`${x},${y}`) && x >= bx0 && x <= bx1 && y >= by0 && y <= by1, `${x},${y}`);
            assert.ok(name(layer(KEY, 'Floor')[`${x},${y}`]).startsWith('grass'), `${x},${y} is on the road`);
        }
    });

    test('Karuizawa: Damian\'s day at Shiraito Falls (544) and Julia\'s at the corn stall (572) are told there, and Bailey starts 2 November beside her (#263)', () => {
        const config = realConfig(), T = game('Trips');
        // [who, the day, the post, the cell the pipeline's row gives (the test above), a line only that post has]
        const told = [['Damian', '2025-11-01', '544', [FALLS.x0 + 1, FALLS.y0 + 5], /saw Shiraito Falls/],
            ['Julia', '2025-11-02', '572', [STALL.x0 + 2, STALL.y0 + 2], /Corn from a bus stop vendor/]];
        const seen = onFoot();
        const state = (room, who, date) => (((cfg.rooms[room].npcs || []).find((n) => n.name === who) || {}).states || {})[date];
        for (const [who, date, post, [x, y], says] of told) {
            const st = state(KEY, who, date);
            assert.ok(st, `${who} ${date} is not in ${KEY}`);
            assert.deepStrictEqual([st.present, st.gridX, st.gridY, st.photo, st.posts.map((p) => p.id).join()], [true, x, y, post, post], `${who} ${date}`);
            assert.ok(st.dialogue.length === 4 && says.test(st.dialogue.join(' ')), `${who} ${date}: the lines went along`);
            assert.ok(fs.existsSync(path.join(GV2, 'assets', 'photos', `${post}.png`)), `${post}.png`);
            // open grass walked to from the gate, off the road, and not a door or the cell in front of one
            assert.ok(seen.has(`${x},${y}`) && name(layer(KEY, 'Floor')[`${x},${y}`]).startsWith('grass'), `${x},${y}`);
            assert.ok(!cfg.rooms[KEY].transporters.some((t) => Math.abs(t.gridX - x) + Math.abs(t.gridY - y) <= 1), `${who} stands at a doorway`);
            // nowhere else that day: Tokyo Station's platform, where both stood in, keeps a bare "absent"
            assert.deepStrictEqual(state('TokyoStation', who, date), { present: false });
            for (const key of Object.keys(cfg.rooms)) {
                const other = key === KEY ? null : state(key, who, date);
                assert.ok(!other || other.present === false, `${who} ${date} is also in ${key}`);
            }
            // as the game resolves the day: the one person in Karuizawa, and gone the day after (Toyama)
            const here = (d) => T.membersByRoom(config, d, {}).filter((g) => g.room === KEY).flatMap((g) => g.members.map((m) => [m.name, m.x, m.y]));
            assert.deepStrictEqual(plain(here(date)), [[who, x, y]]);
            const next = T.addDays(date, 1);
            assert.ok(!here(next).some(([n]) => n === who), `${who} is still in ${KEY} on ${next}`);
            assert.ok(T.membersByRoom(config, next, {}).some((g) => g.room === 'Toyama' && g.members.some((m) => m.name === who)), `${who} is not in Toyama on ${next}`);
            // walk up from the gate and bump them: the post's lines, its photo and its caption
            for (const stitch of [true, false]) {
                const { world } = worldWith(stitch);
                world.date = date;
                world.enter(KEY, W - 4, 34);
                const to = world.roomManager.resolve(KEY, x, y + 1);
                const route = world.path(to.x, to.y), tag = `${stitch ? 'stitched' : '?stitch=0'} ${who}`;
                assert.ok(route, `${tag}: no way on foot to the cell below`);
                for (const dir of route) assert.ok(world.step(dir).moved, tag);
                const bump = world.step('n');
                assert.ok(!bump.moved && bump.interaction && bump.interaction.kind === 'npc', `${tag}: nobody to bump`);
                const npc = bump.interaction.npc;
                assert.deepStrictEqual(plain([npc.name, npc.dialogue, npc.photo, npc.posts.map((p) => p.id)]), [who, st.dialogue, post, [post]], tag);
            }
        }
        assert.ok(!T.membersByRoom(config, '2025-11-03', {}).some((g) => g.room === KEY), 'somebody stays on after the 2nd');

        // 2 November, playing Bailey: Julia here, Dylan in Osaka and Damian in Toyama are one each, all outdoors,
        // and Karuizawa is the nearest to home (one walk through the gate), so the day opens beside Julia.
        // Until this ticket it opened in Osaka, beside Dylan. Measured over every devhouse 2 day and
        // character: this is the only start that moved
        const hops = T.hopsFrom(config, HOST);
        assert.ok(hops[KEY] === 1 && hops[KEY] < hops.Osaka && hops[KEY] < hops.Toyama, JSON.stringify([hops[KEY], hops.Osaka, hops.Toyama]));
        for (const newPlayer of [false, true]) {
            const at = T.startFor(config, '2025-11-02', { played: 'bailey', newPlayer });
            assert.deepStrictEqual({ ...at }, { room: KEY, x: 19, y: 10 });
            const [, , , [jx, jy]] = told[1];
            assert.ok(Math.max(Math.abs(at.x - jx), Math.abs(at.y - jy)) <= 2 && seen.has(`${at.x},${at.y}`), 'beside Julia, on a cell the gate reaches');
            assert.ok(!cfg.rooms[KEY].transporters.some((t) => t.gridX === at.x && t.gridY === at.y) && !(at.x === jx && at.y === jy));
        }
        // nobody else's start moves: the four are one to a room that day and Bailey's is the home room, which
        // wins the tie; and on the 1st Damian alone at the falls does not outvote the three in Asakusa
        for (const played of [undefined, 'james', 'damian', 'dylan', 'julia']) {
            assert.deepStrictEqual({ ...T.startFor(config, '2025-11-02', { played }) }, { room: HOST, x: 32, y: 21 }, `2 November as ${played}`);
        }
        for (const played of [undefined, 'james', 'bailey', 'damian', 'dylan', 'julia']) {
            assert.strictEqual(T.startFor(config, '2025-11-01', { played }).room, 'Market', `1 November as ${played}`);
        }
    });

    test('Kyu-Karuizawa Ginza: a bakery, a souvenir shop and a lounge you can enter, each with its list (#261)', () => {
        // the fronts: three of the room's own, side by side on the north side of the road in, lit at night
        const fronts = [['karuizawa-shop-bakery_0_0', 17], ['karuizawa-shop-jam_0_0', 21], ['karuizawa-shop-lounge_0_0', 25]];
        assert.deepStrictEqual(tilesOf(KEY).filter(([k]) => /^karuizawa-shop-/.test(k)), fronts.map(([key, x]) => [key, `${x},29`, 'Collidables']));
        for (const [key] of fronts) {
            const meta = cfg.spriteMetadata[key];
            assert.deepStrictEqual([meta.anchorX, meta.anchorY, meta.frameCount], [32 / 192, 32 / 256, 1], `${key}: three cells wide, four tall`);
            assert.ok(Array.isArray(meta.glow) && meta.glow.length, `${key}: no glow spots for the night`);
            assert.strictEqual(cfg.tileNames[key], key.replace(/_0_0$/, ''));
        }
        // only real places: no sealed ordinary building stands in the room
        assert.deepStrictEqual(tilesOf(KEY).filter(([k]) => /^(house-|machiya-|highrise-|midrise-|discount-store|seven-eleven)/.test(k)), []);
        // the cells the gate reaches on foot
        const seen = new Set(), todo = [[W - 1, 34]];
        while (todo.length) {
            const [x, y] = todo.pop();
            if (x < 0 || y < 0 || x >= W || y >= H || solid(KEY, x, y) || seen.has(`${x},${y}`)) continue;
            seen.add(`${x},${y}`);
            todo.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
        }
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const Interactions = game('Interactions'), venues = game('Shop.VENUES'), items = Array.from(game('Shop.DEFAULT_ITEMS'));
        const shops = { ShopKaruizawa1: [18, 'Bakery · Karuizawa', 'bakery'], ShopKaruizawa2: [22, 'Souvenirs · Karuizawa', 'souvenirs'],
            ShopKaruizawa3: [26, 'Lounge · Karuizawa', 'lounge'] };
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^ShopKaruizawa/.test(k)).sort(), Object.keys(shops));
        // (everywhere anybody is put: the def's own cell and each dated state's)
        const stood = new Set(cfg.rooms[KEY].npcs.flatMap((n) => [n, ...Object.values(n.states || {})].map((st) => `${st.gridX},${st.gridY}`)));
        assert.ok(stood.has('13,8') && stood.has('21,8'), 'the two posts told here are counted');
        for (const [key, [x, title, menu]] of Object.entries(shops)) {
            const r = cfg.rooms[key], d = cfg.rooms[KEY].transporters.find((t) => t.gridX === x && t.gridY === 32);
            // the door is the one open cell of the front's 3x4 footprint
            for (let fx = x - 1; fx <= x + 1; fx++) {
                for (let fy = 29; fy <= 32; fy++) assert.strictEqual(solid(KEY, fx, fy), !(fx === x && fy === 32), `${key}: the front's cell ${fx},${fy}`);
            }
            // the door and the mat lead to each other; you come back out on the cell in front of the door
            assert.ok(d && d.targetRoom === key && d.hidden, `${key}: its door at ${x},32`);
            assert.deepStrictEqual(r.transporters.map((t) => [t.targetRoom, t.targetX, t.targetY]), [[KEY, x, 33]], key);
            assert.deepStrictEqual([d.targetX, d.targetY], [r.transporters[0].gridX, r.transporters[0].gridY - 1], `${key}: you land one above the way out`);
            assert.ok(name(layer(KEY, 'Floor')[`${x},33`]).startsWith('dirt-outside-autotile_') && seen.has(`${x},33`), `${key}: the street reaches its door`);
            assert.ok(!stood.has(`${x},32`) && !stood.has(`${x},33`), `${key}: somebody stands in its doorway`);
            // the room: a shop floor named by what the front sells, whose counter opens that list
            assert.strictEqual(r.name, title);
            assert.ok(r.interior === true && r.shopEnabled === false && r.shopMenu === menu, key);
            assert.deepStrictEqual(r.shop, { host: KEY, door: [x, 32], type: menu });
            assert.deepStrictEqual({ ...Interactions.match('office-counter2_0_0', r, venues) }, { kind: menu, group: 'shop', footprint: true },
                `${key}: a bump on the counter opens its list`);
        }
        // the lists: the bakery's and the souvenir shop's are the ones other towns have, the lounge's is new
        const sells = (kind) => items.filter((i) => venues[kind].sells(i)).map((i) => i.id).sort();
        assert.deepStrictEqual(sells('bakery'), ['canned-coffee', 'melon-pan', 'nikuman']);
        assert.deepStrictEqual(sells('souvenirs'), ['green-tea', 'melon-pan', 'ramune']);
        assert.deepStrictEqual(sells('lounge'), ['highball', 'nama-beer', 'vodka-redbull']);
        assert.strictEqual(game('Shop.titleFor')('lounge', cfg.rooms.ShopKaruizawa3), 'LOUNGE');
        assert.ok(!venues.lounge.buys && !venues.lounge.grills, 'the lounge buys no fish and grills none');
        // walking it: in from Tokyo, into each shop through its door and out again onto the street
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            const here = () => [world.here().room, world.here().x, world.here().y];
            const walk = (room, x, y) => {
                const to = rm.resolve(room, x, y);
                const route = world.path(to.x, to.y);
                assert.ok(route, `${tag}: no way on foot to ${room} ${x},${y} from ${here()}`);
                for (const dir of route) assert.ok(world.step(dir).moved, `${tag}: blocked on the way to ${room} ${x},${y}`);
                assert.deepStrictEqual(here(), [room, x, y], tag);
            };
            world.enter(HOST, 6, 41);
            if (!stitch) {
                walk(HOST, 1, 41);
                assert.ok(world.step('w').transported, `${tag}: the gate cell is the door`);
            }
            for (const [key, [x]] of Object.entries(shops)) {
                walk(KEY, x, 33);
                const into = world.step('n');
                assert.ok(into.moved && into.transported, `${tag}: ${key}'s door does not take you in`);
                assert.deepStrictEqual(here(), [key, 9, 9], tag);
                const out = world.step('s');
                assert.ok(out.moved && out.transported, `${tag}: ${key}'s mat does not take you out`);
                assert.deepStrictEqual(here(), [KEY, x, 33], tag);
            }
        }
        // the two tables the shop generator opens the doors from
        const doors = fs.readFileSync(path.join(GV2, 'tools', 'roomgen.py'), 'utf8'), types = fs.readFileSync(path.join(GV2, 'tools', 'generate_houses.py'), 'utf8');
        for (const [key] of fronts) {
            assert.ok(new RegExp(`'${key}': \\[\\(1, 3\\)\\]`).test(doors), `roomgen.SHOP_DOORS has no ${key}`);
            assert.ok(new RegExp(`'${key.replace(/_0_0$/, '')}': \\('`).test(types), `generate_houses.SHOP_TYPES has no ${key}`);
        }
    });
};
