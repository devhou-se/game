// Pagoda interiors (issue #214): tools/generate_pagodas.py, tools/generate_pagoda_art.py, the pagoda row of
// roomgen.OWNED_DOORS and the pagoda rules of src/utils/Interactions.js.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, load, worldWith }) => {
    const { spawnSync } = require('child_process');
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    // the three that open: room -> [host, storeys, name, its host doors, the cell you come back out on]
    const OPEN = {
        PagodaMarket1: ['Market', 5, 'Pagoda · Asakusa', [[11, 12]], [11, 13]],
        PagodaPark3: ['Park', 5, 'Pagoda · Park', [[34, 17], [35, 17]], [34, 18]],
        PagodaFukuoka1: ['Fukuoka', 3, 'Pagoda · Fukuoka', [[57, 31], [58, 31]], [57, 32]],
    };
    // the generator's geometry (generate_pagodas.py): the room is 21 wide round column 10, a storey is eight rows
    const W = 21, CX = 10, WIDTHS = { 5: [9, 9, 7, 7, 5], 3: [9, 7, 5] };
    const top = (S, k) => 6 + 8 * (S - 1 - k);
    const stairX = (k) => (k % 2 === 0 ? CX + 2 : CX - 2);
    // where every copy of a piece stands in a room: [[x, y], ...] in reading order
    const at = (room, c, piece, layer) => room.layers.filter((l) => !layer || l.name === layer).flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => c.tilePalette[id] === `pagoda-in-${piece}_0_0`).map(([cell]) => cell.split(',').map(Number))
        .sort((a, b) => a[1] - b[1] || a[0] - b[0]);
    const walk = (world, x, y) => {
        const way = world.path(x, y);
        assert.ok(way, `no way to ${x},${y} from ${world.here().x},${world.here().y}`);
        for (const dir of way) world.step(dir);
        return way;
    };

    test('five pagodas stand in the towns and three can be walked into: Asakusa\'s, the Park\'s front one and Fukuoka\'s (#214)', () => {
        const c = cfg(), name = (id) => c.tilePalette[id];
        // counted from the map data: a pagoda is its base sprite standing on Collidables
        const found = {};
        for (const [key, room] of Object.entries(c.rooms)) {
            const bases = Object.entries(tiles(room, 'Collidables')).filter(([, id]) => /^(pagoda-floor|red-pagoda-small-base)_0_0$/.test(name(id)))
                .map(([cell, id]) => `${name(id).replace(/_0_0$/, '')} ${cell}`);
            if (bases.length) found[key] = bases.sort();
        }
        assert.deepStrictEqual(found, {
            Market: ['pagoda-floor 10,10'],
            Park: ['red-pagoda-small-base 34,11', 'red-pagoda-small-base 34,15', 'red-pagoda-small-base 34,7'],
            Fukuoka: ['red-pagoda-small-base 57,29'],
        });
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Pagoda/.test(k)).sort(), Object.keys(OPEN).sort());
        for (const [key, [host, storeys, label, doors, front]] of Object.entries(OPEN)) {
            const room = c.rooms[key], solid = tiles(c.rooms[host], 'Colliders');
            assert.deepStrictEqual(room.pagoda, { host, door: doors[0], doors, storeys }, key);
            assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [label, W, 7 + 8 * storeys], key);
            assert.deepStrictEqual([room.interior, room.lanternLight, room.shopEnabled, room.npcs], [true, true, false, []], key);
            // each door cell of the host: open, a hidden transporter in place, onto the cell above the mat
            const into = c.rooms[host].transporters.filter((t) => t.targetRoom === key);
            assert.deepStrictEqual(into.map((t) => [t.gridX, t.gridY, t.hidden, t.targetX, t.targetY]),
                doors.map(([x, y]) => [x, y, true, CX, top(storeys, 0) + 6]), key);
            for (const [x, y] of doors) assert.ok(!(`${x},${y}` in solid) && !(`${x},${y + 1}` in solid), `${key} door ${x},${y}`);
            // the mat puts you back in front of the first door, whichever you came in by
            assert.deepStrictEqual(room.transporters.map((t) => [t.gridX, t.gridY, t.targetRoom, t.targetX, t.targetY, t.hidden]),
                [[CX, top(storeys, 0) + 7, host, ...front, true]], key);
            assert.deepStrictEqual(Object.entries(c.rooms).filter(([, r]) => (r.transporters || []).some((t) => t.targetRoom === key)).map(([k]) => k), [host]);
        }
        // the Park's two behind stand with the next pagoda's roof across their doors: they stay sealed
        const park = c.rooms.Park, shut = tiles(park, 'Colliders');
        for (const cell of ['34,9', '35,9', '34,13', '35,13']) {
            assert.ok(cell in shut, `Park ${cell} is open`);
            assert.ok(!park.transporters.some((t) => `${t.gridX},${t.gridY}` === cell), `Park ${cell} has a door`);
        }
        assert.ok('34,10' in shut && '34,14' in shut, 'the cell in front of a sealed pagoda can be stood on: open it');
        // the palace's end towers are pagoda-floor too, laid flat: they are the palace hall's doors, as they were
        const tokyo = c.rooms.Tokyo;
        assert.ok(Object.values(tiles(tokyo, 'Over Floor')).some((id) => name(id) === 'pagoda-floor_0_0'));
        assert.deepStrictEqual(tokyo.transporters.filter((t) => /^(PalaceHall|Pagoda)/.test(t.targetRoom)).map((t) => [t.gridX, t.gridY, t.targetRoom]),
            [[19, 22, 'PalaceHallTokyo1'], [41, 22, 'PalaceHallTokyo1']]);
    });

    test('a pagoda\'s room is the whole tower cut open: storeys one above the other and narrower as they rise, the heart pillar on each, a stair on alternate sides (#214)', () => {
        const c = cfg();
        for (const [key, [, S]] of Object.entries(OPEN)) {
            const room = c.rooms[key], solid = tiles(room, 'Colliders'), floor = tiles(room, 'Floor'), name = (id) => c.tilePalette[id];
            const widths = WIDTHS[S];
            for (let k = 0; k < S; k++) {
                const t = top(S, k), x0 = CX - (widths[k] - 1) / 2, x1 = CX + (widths[k] - 1) / 2;
                // two rows of back wall, five of boards, the floor's cut edge - all flat on Floor
                for (let x = x0; x <= x1; x++) {
                    assert.ok(/^pagoda-in-wall-head_/.test(name(floor[`${x},${t}`])) && /^pagoda-in-wall_/.test(name(floor[`${x},${t + 1}`])), `${key} wall ${x},${t}`);
                    for (let y = t + 2; y <= t + 6; y++) assert.ok(/^pagoda-in-(board-[ab]|hatch)_/.test(name(floor[`${x},${y}`])), `${key} boards ${x},${y}`);
                    assert.ok((k === 0 ? /^pagoda-in-(base|threshold)_/ : /^pagoda-in-edge_/).test(name(floor[`${x},${t + 7}`])), `${key} edge ${x},${t + 7}`);
                }
                // outside it: the side walls, then the dark
                for (let y = t + 2; y <= t + 6; y++) {
                    assert.deepStrictEqual([name(floor[`${x0 - 1},${y}`]), name(floor[`${x1 + 1},${y}`])], ['pagoda-in-side-w_0_0', 'pagoda-in-side-e_0_0'], `${key} sides ${y}`);
                    assert.strictEqual(name(floor[`${x0 - 2},${y}`]), 'office-void-autotile_center');
                }
            }
            // the heart pillar on every storey but the ground floor, where it rises out of the dais: you walk behind it, only its foot is solid
            assert.deepStrictEqual(at(room, c, 'pillar', 'Collidables'), Array.from({ length: S - 1 }, (_, i) => [CX, top(S, S - 1 - i) + 2]), key);
            for (const [x, y] of at(room, c, 'pillar')) assert.deepStrictEqual([`${x},${y}` in solid, `${x},${y + 1}` in solid, `${x},${y + 2}` in solid], [false, false, true]);
            const g = top(S, 0);
            assert.deepStrictEqual([at(room, c, 'shumidan'), at(room, c, 'saisen'), at(room, c, 'shokudai')],
                [[[CX - 1, g + 2]], [[CX, g + 5]], [[CX - 3, g + 3], [CX + 3, g + 3]]], key);
            for (let x = CX - 1; x <= CX + 1; x++) assert.deepStrictEqual([`${x},${g + 3}` in solid, `${x},${g + 4}` in solid], [false, true], `${key} dais ${x}`);
            assert.ok(`${CX},${g + 5}` in solid && `${CX - 3},${g + 4}` in solid && `${CX + 3},${g + 4}` in solid);
            // a stair up from every storey but the top, on alternate sides, out of a hatch in the boards above
            assert.deepStrictEqual(at(room, c, 'stair', 'Over Floor'), Array.from({ length: S - 1 }, (_, i) => [stairX(S - 2 - i), top(S, S - 2 - i) - 1]), key);
            assert.deepStrictEqual(at(room, c, 'hatch', 'Floor'), Array.from({ length: S - 1 }, (_, i) => [stairX(S - 2 - i), top(S, S - 2 - i) - 2]), key);
            for (const [x, y] of at(room, c, 'stair')) {
                for (const cell of [`${x},${y}`, `${x},${y + 1}`, `${x},${y + 2}`]) assert.ok(!(cell in solid), `${key} stair ${cell} is solid`);
                // nothing hangs over a stair or stands across it: you are seen all the way up
                const over = room.layers.filter((l) => l.z >= 2 && !l.collision).flatMap((l) => Object.keys(l.tiles)).map((cell) => cell.split(',').map(Number));
                assert.ok(!over.some(([ox, oy]) => ox === x && oy >= y - 2 && oy <= y + 3), `${key}: something is drawn over the stair at ${x},${y}`);
            }
            // what is on the walls: a fitting on each middle storey away from the stair, the window on the top one; all four cells (six) solid
            const fittings = at(room, c, 'kyozo').concat(at(room, c, 'senbutsu')).sort((a, b) => a[1] - b[1]);
            assert.deepStrictEqual(fittings.map(([, y]) => y), Array.from({ length: S - 2 }, (_, i) => top(S, S - 2 - i)), key);
            fittings.forEach(([x, y]) => {
                const k = S - 1 - (y - 6) / 8;
                assert.ok(x !== stairX(k) && x + 1 !== stairX(k) && x >= CX - (widths[k] - 1) / 2 && x + 1 <= CX + (widths[k] - 1) / 2, `${key} fitting ${x},${y}`);
                for (const cell of [`${x},${y}`, `${x + 1},${y}`, `${x},${y + 1}`, `${x + 1},${y + 1}`]) assert.ok(cell in solid, cell);
            });
            assert.deepStrictEqual(at(room, c, 'window'), [[CX - 1, 6]], key);
            // one hung lantern a storey, overhead, clear of that storey's stair and hatch
            const lamps = at(room, c, 'toro-hang');
            assert.deepStrictEqual(lamps.map(([, y]) => y), Array.from({ length: S }, (_, i) => top(S, S - 1 - i) + 1), key);
            lamps.forEach(([x, y], i) => {
                const k = S - 1 - i, taken = [k < S - 1 ? stairX(k) : null, k > 0 ? stairX(k - 1) : null];
                assert.ok(`${x},${y}` in tiles(room, 'Tops') && !taken.includes(x), `${key} lantern ${x},${y}`);
            });
            // the roofs: a skirt either side of every floor above the ground, the top roof and its spire one sprite over the last
            assert.deepStrictEqual([at(room, c, 'eave-w', 'Over Floor').length, at(room, c, 'eave-e', 'Over Floor').length, at(room, c, 'roof', 'Over Floor')],
                [S - 1, S - 1, [[CX - 4, 0]]], key);
            // nothing flat has a collider but the wall behind a fitting or the window: the room's outline holds
            // you to the floors, the stairs and the mat
            const hung = new Set(fittings.flatMap(([x, y]) => [`${x},${y}`, `${x + 1},${y}`, `${x},${y + 1}`, `${x + 1},${y + 1}`])
                .concat([0, 1, 2].flatMap((i) => [`${CX - 1 + i},6`, `${CX - 1 + i},7`])));
            const flat = room.layers.filter((l) => l.z < 2 && !l.collision).flatMap((l) => Object.entries(l.tiles)).filter(([, id]) => /^pagoda-in-(wall|side|edge|base|eave|roof)/.test(name(id)));
            assert.ok(flat.length > 60 && !flat.some(([cell]) => cell in solid && !hung.has(cell)), key);
            assert.ok(room.boundary.length >= 20 && room.boundary.every(([x, y]) => x >= CX - 5 && x <= CX + 5 && y >= 7 && y <= 7 + 8 * S), key);
            const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map(name));
            assert.ok(![...used].some((k) => /^(temple-in-|shrine-in-|palace-in-)/.test(k)), 'none of the temple\'s, the shrines\' or the palace\'s pieces');
        }
        // the two smaller pagodas are told apart by what is on their walls
        const order = (key) => at(c.rooms[key], c, 'kyozo').map(([x, y]) => `kyozo ${x},${y}`).concat(at(c.rooms[key], c, 'senbutsu').map(([x, y]) => `senbutsu ${x},${y}`)).sort();
        assert.notDeepStrictEqual(order('PagodaMarket1'), order('PagodaPark3'));
        // every light has its spots in the Glows table, in numbers
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        for (const piece of ['toro-hang', 'shokudai']) {
            const spots = game('Glows').spotsFor(`pagoda-in-${piece}_0_0`, c.spriteMetadata[`pagoda-in-${piece}_0_0`]);
            assert.ok(spots.length >= 1 && spots.every((s) => Number.isInteger(s.color) && s.r <= 2.5), piece);
        }
        assert.deepStrictEqual([c.spriteMetadata['pagoda-in-toro-hang_0_0'].depthBias, c.spriteMetadata['pagoda-in-doorlight_0_0'].depthBias], [10, -40]);
    });

    test('you walk into each pagoda by every door, climb every stair to the window at the top, and come back down and out in front of it (#214)', () => {
        for (const stitch of [true, false]) {
            const { world, config } = worldWith(stitch);
            for (const [key, [host, S, , doors, front]] of Object.entries(OPEN)) {
                const arrive = [CX, top(S, 0) + 6];
                for (const [dx, dy] of doors) {
                    world.enter(host, dx, dy + 1);
                    const inn = world.step('n');
                    assert.strictEqual(inn.transported && inn.transported.to, key, `${key} door ${dx},${dy} (stitch ${stitch})`);
                    assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [key, ...arrive]);
                    // up: each stair is three cells through the back wall and the floor above, onto its hatch
                    for (let k = 0; k < S - 1; k++) {
                        const sx = stairX(k), t = top(S, k);
                        walk(world, sx, t + 2);
                        for (const y of [t + 1, t, t - 1, t - 2]) {
                            assert.ok(world.step('n').moved, `${key} stair ${k} at ${sx},${y}`);
                            assert.deepStrictEqual([world.here().x, world.here().y], [sx, y]);
                            assert.ok(!world.step('e').moved || !world.step('w').moved || y === t - 2, 'a stair is one cell wide');
                            walk(world, sx, y);
                        }
                        // and the only way on from here is across the floor: the next stair is on the other side of the pillar
                        assert.ok(walk(world, 2 * CX - sx, t - 4).length >= 4);
                    }
                    walk(world, CX - 1, 8);
                    const look = world.step('n');
                    assert.deepStrictEqual([look.moved, look.interaction && look.interaction.kind], [false, 'pagoda-window'], key);
                    // down again, every stair the other way, and out over the mat
                    const down = walk(world, ...arrive);
                    assert.strictEqual(down.filter((d) => d === 's').length - down.filter((d) => d === 'n').length, arrive[1] - 8);
                    const out = world.step('s');
                    assert.strictEqual(out.transported && out.transported.to, host, `${key} mat`);
                    assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [host, ...front]);
                    assert.ok(!world.blocked.has(`${world.player.gridX},${world.player.gridY}`), 'put down on a solid cell');
                }
                // every board, hatch and stair cell is walked to from the door, and nothing else is
                world.enter(key, ...arrive);
                const room = config.rooms[key], c = cfg(), raw = c.rooms[key], solid = tiles(raw, 'Colliders');
                const want = new Set(Object.entries(tiles(raw, 'Floor')).filter(([cell, id]) => /^pagoda-in-(board-[ab]|hatch|threshold)_/.test(c.tilePalette[id]) && !(cell in solid)).map(([cell]) => cell));
                for (const [x, y] of at(raw, c, 'stair')) for (const cell of [`${x},${y}`, `${x},${y + 1}`, `${x},${y + 2}`]) want.add(cell);
                assert.deepStrictEqual([...world.reachable()].sort(), [...want].sort(), `${key} (stitch ${stitch})`);
                assert.ok(room && want.size > 20 * S);
                // everything there is to bump, from the cell below its foot
                const things = world.interactions();
                const kinds = things.map((i) => i.kind).sort();
                const mid = raw.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]);
                const count = (piece) => mid.filter((k) => k === `pagoda-in-${piece}_0_0`).length;
                assert.deepStrictEqual(plain(kinds), [].concat(Array(S - 1).fill('heart-pillar'), ['four-buddhas', 'offering', 'pagoda-window'],
                    Array(count('kyozo')).fill('sutra-chests'), Array(count('senbutsu')).fill('thousand-buddhas')).sort(), key);
                assert.ok(things.every((i) => i.group === 'flavour' || (i.kind === 'offering' && i.group === 'temple')), 'nothing in here is a shop');
                for (const i of things) {
                    const foot = i.y + i.h - 1;
                    let cell = null;
                    for (let x = i.x; x < i.x + i.w && !cell; x++) if (world.path(x, foot + 1)) cell = [x, foot + 1];
                    assert.ok(cell, `${key}: no way to the ${i.kind} at ${i.x},${i.y}`);
                    walk(world, ...cell);
                    const bump = world.step('n');
                    assert.deepStrictEqual([bump.moved, bump.interaction && bump.interaction.kind], [false, i.kind], `${key} ${i.kind}`);
                    assert.ok(/palms together|says: "/.test(world.describe(bump.interaction)), world.describe(bump.interaction));
                }
                const lint = world.lint(key);
                assert.deepStrictEqual(plain([lint.errors, lint.warns]), [{}, {}], `lint ${key}`);
            }
        }
    });

    test('a pagoda\'s doors are doorways of the stitched city at the district\'s own cells, and nobody is ever put on one or in front of it (#214)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager, c = cfg();
        for (const [key, [host, , , doors]] of Object.entries(OPEN).filter(([, [h]]) => h !== 'Fukuoka')) {
            const city = rm.rooms.TokyoCity.transporters.filter((t) => t.targetRoom === key);
            assert.deepStrictEqual(plain(city.map((t) => [t.gridX, t.gridY, t.hidden])), doors.map(([x, y]) => { const to = rm.resolve(host, x, y); return [to.x, to.y, true]; }), key);
            assert.ok(city.length && rm.resolve(host, 0, 0).room === 'TokyoCity', key);
        }
        for (const [key, [host, , , doors]] of Object.entries(OPEN)) {
            const cells = doors.flatMap(([x, y]) => [`${x},${y}`, `${x},${y + 1}`]);
            const inWay = c.rooms[host].npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
                .filter(([, s]) => cells.includes(`${s.gridX},${s.gridY}`)).map(([date]) => `${n.name} ${date}`));
            assert.deepStrictEqual(inWay, [], key);
            for (const d of c.districts[host]) assert.ok(!cells.includes(d.stand.join(',')), `${host} · ${d.name}`);
        }
        // "the pagoda" is a place a blog post can be put: its visitor stands where they did, off the doors
        const run = spawnSync('python3', ['-c', [
            'import json, blog_to_npc as b',
            "cfg = json.load(open('../config.json'))",
            'spots = b.all_spots(cfg)',
            "print(json.dumps({k: b.stand_cell(cfg, k, spots)[1] for k in spots if k.endswith('the pagoda')}))",
        ].join('\n')], { cwd: path.join(GV2, 'tools'), encoding: 'utf8', maxBuffer: 1 << 26, env: Object.assign({}, process.env, { PYTHONDONTWRITEBYTECODE: '1' }) });
        assert.strictEqual(run.status, 0, run.stderr);
        assert.deepStrictEqual(JSON.parse(run.stdout), { 'Fukuoka · the pagoda': [56, 27], 'Market · the pagoda': [9, 4], 'Park · the pagoda': [33, 10] });
    });

    test('the pagoda\'s offering box is the temple\'s rule, and the pillar, the Buddhas, the chests, the niches and the window each say a line (#214)', () => {
        const I = game('Interactions');
        const hit = (key, room) => plain(I.match(key, room || { interior: true, shopEnabled: false }));
        assert.deepStrictEqual(hit('pagoda-in-saisen_0_0'), { kind: 'offering', group: 'temple', footprint: true });
        assert.deepStrictEqual(hit('temple-in-saisen_0_0'), { kind: 'offering', group: 'temple', footprint: true });
        assert.strictEqual(hit('shrine-in-saisen-red_0_0').group, 'shrine');
        const says = {};
        for (const [piece, kind] of [['pillar', 'heart-pillar'], ['shumidan', 'four-buddhas'], ['kyozo', 'sutra-chests'], ['senbutsu', 'thousand-buddhas'], ['window', 'pagoda-window']]) {
            const rule = hit(`pagoda-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.say && rule.say.length <= 96, piece);
            says[rule.say] = piece;
        }
        assert.strictEqual(Object.keys(says).length, 5, 'five different lines');
        for (const piece of ['shokudai', 'toro-hang', 'stair', 'hatch', 'roof', 'doorlight', 'threshold', 'wall', 'board-a']) {
            assert.strictEqual(hit(`pagoda-in-${piece}_0_0`), null, piece);
        }
        // nothing of the pagoda's own in the code: no new file, key, save field or item
        const index = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        assert.ok(!/pagoda/i.test(index) && !/pagoda/i.test(src('TempleVisit.js')) && !/pagoda/i.test(src('Shop.js')));
    });

    test('the bar says whose pagoda it is, and from the top storey the camera looks up at the roof and its spire (#214)', () => {
        const c = cfg(), hudName = game('hudName'), hudBrief = game('hudBrief');
        assert.strictEqual(hudName(c.rooms.PagodaMarket1.name), 'Pagoda | Asakusa');
        assert.deepStrictEqual(Object.keys(OPEN).map((k) => hudBrief(hudName(c.rooms[k].name))), ['Asakusa pagoda', 'Park pagoda', 'Fukuoka pagoda']);
        // hud-phone-layout.test.js's rule: 16 px a character on the one-row bar at 667x375 (715 wide)
        for (const k of Object.keys(OPEN)) assert.ok(10 + 16 * `${hudBrief(hudName(c.rooms[k].name))} | Nov 11 2025 | ¥5,000`.length + 10 + 64 + 10 <= 715, k);
        if (!game('typeof Places !== "undefined"')) vm.runInContext(src('utils/Places.js'), ctx, { filename: 'Places.js' });
        const where = (k) => game('Places').whereText(game('decodeConfig')(c), k);
        assert.deepStrictEqual([where('PagodaMarket1'), where('PagodaFukuoka1')], ['Pagoda · Asakusa (in Tokyo)', 'Pagoda · Fukuoka']);

        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView'), look = c.game.lookUp, G = 64;
        assert.strictEqual(look.sprites['pagoda-in-roof'], 2, 'two rows of back wall stand under the roof sprite');
        const png = require(path.join(GV2, 'tools', 'png'));
        const roof = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'pagoda-in-roof_0_0.png')));
        assert.deepStrictEqual([roof.width / G, roof.height / G], [9, 6]);
        const [mark] = LandmarkView.index([{ key: 'pagoda-in-roof_0_0', left: (CX - 4) * G, top: 0, width: roof.width, height: roof.height }], look.sprites, G);
        assert.deepStrictEqual(plain(mark), { key: 'pagoda-in-roof_0_0', left: 6 * G, right: 15 * G, top: 0, feet: 8 * G });
        const aim = (x, y) => LandmarkView.aim({ x: x * G + 32, y: y * G + 32, landmarks: [mark], grid: G, cells: look.cells, fade: look.fade,
            side: look.side, viewH: 960, bar: 40, deadzone: 256, foot: 128 });
        // anywhere across the top storey's back rows the camera sits on the roof: the view's top is the room's
        for (let x = CX - 2; x <= CX + 2; x++) {
            const a = aim(x, 8);
            assert.strictEqual(a.weight, 1, `column ${x}`);
            assert.ok(8 * G + 32 - a.offset - 480 <= 0, `column ${x}: the spire is off the top`);
        }
        // ...and on the storey below it is the ordinary camera again
        for (let y = 16; y <= 20; y++) assert.deepStrictEqual(plain(aim(CX, y)), { weight: 0, offset: 0 }, `row ${y}`);
        // the spire's tip is drawn clear of the HUD bar (40 px at desktop size) when the view is at the room's top
        const firstRow = Array.from({ length: roof.height }, (_, y) => y).find((y) => {
            for (let x = 0; x < roof.width; x++) if (roof.data[(y * roof.width + x) * 4 + 3]) return true;
            return false;
        });
        assert.ok(firstRow >= 42 && firstRow <= 64, `the spire starts ${firstRow} px down the sprite`);
    });

    test('the pagoda generator and its art tool are checked, own their doors through roomgen, and a rebuild of Fukuoka keeps its pagoda open (#214)', () => {
        const check = tool('check_generators.py');
        for (const name of ['generate_pagodas', 'generate_pagoda_art']) assert.ok(check.includes(`'${name}'`), name);
        const rg = tool('roomgen.py'), gen = tool('generate_pagodas.py');
        assert.ok(/PAGODA_PREFIX: \('pagoda', PAGODA_DOORS\)/.test(rg), 'OWNED_DOORS');
        assert.ok(/PAGODA_DOORS = \{'pagoda-floor_0_0': \[\(1, 2\)\], 'red-pagoda-small-base_0_0': \[\(0, 2\), \(1, 2\)\]\}/.test(rg));
        assert.ok((rg.match(/^def keep_\w+/gm) || []).length === 1, 'a second door keeper');
        // finding pagodas and the stay-sealed rules are the houses', reused; the door sprites are roomgen's
        assert.ok(/gh\.find_houses\(cfg, host, KIND\)/.test(gen) && /doors=rg\.PAGODA_DOORS/.test(gen) && !/def find_/.test(gen));
        // the room is the shared shell's (#224, generator-blocks.test.js): its boundary and its reachability
        // check are Interior.room's, and the host's doors are opened and shut by roomgen
        assert.ok(/it = Interior\(/.test(gen) && /it\.room\(/.test(gen) && /it\.doorway\(/.test(gen), 'built on interiors.Interior');
        assert.ok(/rg\.open_door\(room, cell, p\['key'\], arrive\)/.test(gen) && /rg\.shut_door\(room, cell, PREFIX\)/.test(gen));
        assert.ok(!/\['boundary'\]|\.outline\(|rg\.Builder\(|rg\.transporter\(/.test(gen), 'a shell, a boundary or a door of its own');
        // the palette was appended to after the konbini kit's, which landed first (#221)
        assert.ok(cfg().tilePalette.indexOf('pagoda-in-board-a_0_0') > cfg().tilePalette.indexOf('konbini-floor-a_0_0'));
        // no other generator knows about a pagoda's room
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !/^generate_pagoda/.test(n))) {
            assert.ok(!/Pagoda[A-Z]|PAGODA_|pagoda-in-/.test(tool(f)), f);
        }
        // the palette was appended to: every pagoda sprite is in it once, after the temple's
        const c = cfg();
        const mine = c.tilePalette.map((k, i) => [k, i]).filter(([k]) => k.startsWith('pagoda-in-'));
        assert.ok(mine.length >= 30 && new Set(mine.map(([k]) => k)).size === mine.length);
        assert.ok(mine[0][1] > c.tilePalette.indexOf('temple-in-slab-a_0_0'));
        // every sprite the art tool registers is on disk at a whole number of cells, and is used by a pagoda
        const png = require(path.join(GV2, 'tools', 'png'));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith('pagoda-in-'));
        assert.ok(keys.length >= 30, `${keys.length} pagoda sprites`);
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
            assert.ok(mine.some(([name]) => name === k), `${k} is drawn but not placed`);
        }
        assert.deepStrictEqual(fs.readdirSync(path.join(GV2, 'assets', 'sprites')).filter((f) => f.startsWith('pagoda-in-')).sort(), keys.map((k) => k + '.png').sort());

        const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gamev2-pagodas-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            const read = () => fs.readFileSync(path.join(tmp, 'config.json'), 'utf8');
            const python = (...args) => {
                const run = spawnSync('python3', args, { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
                assert.strictEqual(run.status, 0, `${args.join(' ')}: ${run.stderr}`);
                return run.stdout;
            };
            const before = read();
            // a re-run (every wired town) changes nothing, and neither does a rebuild of Fukuoka or a run of the houses
            for (const args of [['tools/generate_pagodas.py'], ['tools/generate_fukuoka.py'], ['tools/generate_houses.py'], ['tools/generate_shrines.py']]) {
                python(...args);
                assert.ok(read() === before, `${args[0]} changed config.json: a pagoda door was not kept`);
            }
            // from sealed pagodas it builds the same world: seal every door, drop the rooms, name the towns
            const sealed = JSON.parse(before), blank = sealed.tilePalette.indexOf('gk_blank');
            for (const [key, [host]] of Object.entries(OPEN)) {
                const room = sealed.rooms[host];
                for (const t of room.transporters.filter((x) => x.targetRoom === key)) tiles(room, 'Colliders')[`${t.gridX},${t.gridY}`] = blank;
                room.transporters = room.transporters.filter((x) => x.targetRoom !== key);
                delete sealed.rooms[key];
            }
            const shut = JSON.stringify(sealed, null, 2);
            fs.writeFileSync(path.join(tmp, 'config.json'), shut);
            const dry = python('tools/generate_pagodas.py', 'Market', 'Park', 'Fukuoka', 'Tokyo', '--dry-run');
            assert.ok(read() === shut, '--dry-run wrote config.json');
            assert.ok(/skipped  PagodaPark1 /.test(dry) && /skipped  PagodaPark2 /.test(dry) && /built    PagodaPark3 /.test(dry) && /no pagoda in Tokyo/.test(dry), dry);
            python('tools/generate_pagodas.py', 'Market', 'Park', 'Fukuoka', 'Tokyo');
            // (a door wired afresh goes to the end of its host's list, after any door opened since)
            const unordered = (text) => {
                const c = JSON.parse(text);
                for (const [host] of Object.values(OPEN)) c.rooms[host].transporters.sort((p, q) => p.gridY - q.gridY || p.gridX - q.gridX);
                return c;
            };
            assert.deepStrictEqual(unordered(read()), unordered(before));
            // a town whose pagoda has no room is rebuilt with it sealed: the door is the room's, not the town's
            const gone = JSON.parse(before);
            delete gone.rooms.PagodaFukuoka1.pagoda;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(gone, null, 2));
            python('tools/generate_fukuoka.py');
            const after = JSON.parse(read());
            assert.ok(!after.rooms.Fukuoka.transporters.some((t) => t.targetRoom === 'PagodaFukuoka1'), 'an unowned door was kept');
            assert.ok('57,31' in tiles(after.rooms.Fukuoka, 'Colliders') && '58,31' in tiles(after.rooms.Fukuoka, 'Colliders'), 'an unowned door stayed open');
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });
};
