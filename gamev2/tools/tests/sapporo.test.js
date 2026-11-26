// Sapporo's rebuild (issue #219). Stage 1 is the north of the town: the Sapporo Station front and the
// Clock Tower block. Stage 2 is Odori Park. All of it is data the generators write (tools/generate_sapporo.py,
// generate_sapporo_art.py, make_prefabs.py, generate_stations.py, generate_houses.py --lobbies).
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const room = cfg.rooms.Sapporo;
    const layer = (n, r = room) => ((r.layers.find((l) => l.name === n) || {}).tiles) || {};
    const W = room.worldWidth / 64, H = room.worldHeight / 64;
    const solid = (x, y) => `${x},${y}` in layer('Colliders');
    const floor = (x, y) => name(layer('Floor')[`${x},${y}`]);
    const at = (key) => Object.entries(layer('Collidables')).filter(([, t]) => name(t) === key).map(([xy]) => xy.split(',').map(Number));
    const doorAt = (x, y) => room.transporters.find((t) => t.gridX === x && t.gridY === y);
    const KITA = 20;        // Kita-Odori's top row: everything north of it is stage 1
    // cells that can be walked to from where the station puts you
    const reach = (() => {
        const start = cfg.rooms.SapporoStation.transporters[0];
        const seen = new Set([`${start.targetX},${start.targetY}`]), todo = [[start.targetX, start.targetY]];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const nx = x + dx, ny = y + dy, k = `${nx},${ny}`;
                if (nx < 0 || ny < 0 || nx >= W || ny >= H || seen.has(k) || solid(nx, ny)) continue;
                seen.add(k); todo.push([nx, ny]);
            }
        }
        return seen;
    })();
    const prefab = (key) => {
        const p = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', key + '.tmj'), 'utf8'));
        const cells = new Set();
        const lay = p.layers.find((l) => l.name === 'Colliders');
        lay.data.forEach((g, i) => { if (g) cells.add(`${i % p.width},${Math.floor(i / p.width)}`); });
        const doors = p.layers.find((l) => l.name === 'Meta').objects.map((o) => [Math.floor(o.x / 64), Math.floor(o.y / 64)]);
        return { w: p.width, h: p.height, cells, doors };
    };

    test('Sapporo: the station is the station front with the star clock, and its pair of doors pairs both ways (#219)', () => {
        assert.deepStrictEqual(at('sapporo-station-front_0_0'), [[24, 4]]);
        const entry = cfg.stations.SapporoStation.entry;
        const doors = room.transporters.filter((t) => t.targetRoom === 'SapporoStation');
        assert.deepStrictEqual(doors.map((t) => [t.gridX, t.gridY]).sort(), [[28, 10], [29, 10]], 'the two cells under the clock');
        for (const t of doors) {
            assert.ok(t.hidden && !solid(t.gridX, t.gridY));
            assert.deepStrictEqual([t.targetX, t.targetY], entry, 'into the station at its entry cell');
            assert.ok(!solid(t.gridX, t.gridY + 1) && !doorAt(t.gridX, t.gridY + 1), 'a free cell in front that is not a door');
        }
        // the way out of the station: the cell in front of the west door, on the plaza
        const out = cfg.rooms.SapporoStation.transporters;
        assert.ok(out.length >= 1);
        for (const t of out) {
            assert.strictEqual(t.targetRoom, 'Sapporo');
            assert.deepStrictEqual([t.targetX, t.targetY], [28, 11]);
        }
        // no townhouse is the station any more, here or anywhere north of Kita-Odori
        for (const [xy, t] of Object.entries(layer('Collidables'))) {
            const y = Number(xy.split(',')[1]);
            if (y < KITA) assert.ok(!/^building-(entrance|rafter|tier)|^machiya-|^highrise-|^midrise-/.test(name(t)), `${name(t)} at ${xy}`);
        }
        for (const [xy, t] of Object.entries(layer('Tops'))) {
            if (Number(xy.split(',')[1]) < KITA) assert.ok(!/^building-roof/.test(name(t)), `${name(t)} at ${xy}`);
        }
    });

    test('Sapporo: the north has its own buildings, the towers and the street grid stay where they were (#219)', () => {
        assert.deepStrictEqual(at('sapporo-akarenga_0_0'), [[2, 11]]);
        assert.deepStrictEqual(at('sapporo-office-glass_0_0'), [[10, 11]]);
        assert.deepStrictEqual(at('sapporo-office-brick_0_0'), [[49, 9]]);
        assert.deepStrictEqual(at('sapporo-clock-tower_0_0'), [[37, 11]], 'the Clock Tower has not moved');
        assert.deepStrictEqual(at('sapporo-tv-tower_0_0'), [[47, 17]], 'the TV Tower has not moved');
        assert.deepStrictEqual(at('seven-eleven_0_0'), [[44, 15]]);
        assert.deepStrictEqual(at('discount-store_0_0'), [[16, 11]]);
        // the grid: two east-west streets and three north-south, three cells wide each, none moved or narrowed
        const road = (x, y) => /^road-/.test(floor(x, y));
        for (let x = 2; x <= 53; x++) for (const y0 of [20, 31]) for (let y = y0; y < y0 + 3; y++) assert.ok(road(x, y), `${x},${y}`);
        for (const [x0, top] of [[14, 20], [30, 11], [44, 20]]) {
            for (let y = top; y <= 40; y++) for (let x = x0; x < x0 + 3; x++) assert.ok(road(x, y), `${x},${y}`);
            assert.ok(!road(x0 - 1, 25) && !road(x0 + 3, 25), `the street at column ${x0} is three cells wide`);
        }
        // the government hall is a landmark: sealed, no way in
        assert.ok(solid(5, 16) && !doorAt(5, 16));
        // the way in to the other interiors of the north is untouched
        assert.strictEqual(doorAt(45, 18).targetRoom, 'KonbiniSapporo1');
        assert.strictEqual(doorAt(18, 18).targetRoom, 'DonTakoteSapporo');
        // every door of the town is one of: the station's pair, the konbini, the store, a house, a lobby
        const kinds = room.transporters.map((t) => t.targetRoom.replace(/\d+$/, '')).sort();
        assert.deepStrictEqual([...new Set(kinds)], ['DonTakoteSapporo', 'HouseSapporo', 'KonbiniSapporo', 'LobbySapporo', 'SapporoStation']);
    });

    test('Sapporo: the two northern districts stand on ground of their own (#219)', () => {
        const fam = (x, y) => floor(x, y).replace(/_[a-z-]+$/, '');
        // Station front: the plaza, the strip by the station and the forecourt of the west row
        for (const [x, y] of [[23, 11], [29, 18], [26, 14], [28, 11], [29, 11], [36, 9], [5, 17], [12, 18]]) {
            assert.strictEqual(fam(x, y), 'arcade-brick-autotile', `${x},${y}`);
        }
        // Clock Tower block: from the avenue to the east hedge
        for (const [x, y] of [[34, 12], [39, 18], [43, 15], [47, 14], [53, 18], [51, 16]]) {
            assert.strictEqual(fam(x, y), 'flat-grey-brick-autotile', `${x},${y}`);
        }
        // neither is the paving of anywhere else in town, and the two differ
        for (let y = KITA; y < H; y++) for (let x = 0; x < W; x++) assert.notStrictEqual(fam(x, y), 'arcade-brick-autotile', `${x},${y}`);
        for (let y = 0; y < KITA; y++) for (let x = 0; x < W; x++) assert.notStrictEqual(fam(x, y), 'grey-brick-autotile', `${x},${y}`);
        // the pavement along Kita-Odori is still pavement
        for (let x = 2; x <= 53; x++) if (x < 30 || x > 32) assert.strictEqual(fam(x, 19), 'light-concrete-autotile', `${x},19`);    // 30-32: the avenue
    });

    test('Sapporo: the office blocks have lobbies, and nobody can walk behind a building of the north (#219)', () => {
        const lobby = (k) => cfg.rooms[k].lobby;
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^LobbySapporo/.test(k)), ['LobbySapporo1', 'LobbySapporo2']);
        assert.deepStrictEqual(lobby('LobbySapporo1'), { host: 'Sapporo', door: [51, 15], doors: [[51, 15]] });   // the brick block
        assert.deepStrictEqual(lobby('LobbySapporo2'), { host: 'Sapporo', door: [12, 16], doors: [[12, 16]] });   // the glass block
        for (const k of ['LobbySapporo1', 'LobbySapporo2']) {
            const [dx, dy] = lobby(k).door, t = doorAt(dx, dy);
            assert.ok(t && t.targetRoom === k && t.hidden && !solid(dx, dy), `${k}: its door is open`);
            assert.ok(reach.has(`${dx},${dy + 1}`), `${k}: the cell in front of its door can be walked to`);
            for (const back of cfg.rooms[k].transporters) assert.deepStrictEqual([back.targetRoom, back.targetX, back.targetY], ['Sapporo', dx, dy + 1]);
        }
        // footprints: the station and the hall are solid wherever they are drawn tall enough to hide someone,
        // an office block everywhere but its top row
        const st = prefab('sapporo-station-front');
        assert.deepStrictEqual(st.doors, [[4, 6], [5, 6]]);
        for (let y = 2; y < 7; y++) for (let x = 0; x < 10; x++) assert.ok(st.cells.has(`${x},${y}`), `station ${x},${y}`);
        const hall = prefab('sapporo-akarenga');
        assert.deepStrictEqual(hall.doors, [[3, 5]]);
        for (let y = 2; y < 6; y++) for (let x = 0; x < 7; x++) assert.ok(hall.cells.has(`${x},${y}`), `hall ${x},${y}`);
        for (const [key, w, h] of [['sapporo-office-brick', 4, 7], ['sapporo-office-glass', 5, 6]]) {
            const p = prefab(key);
            for (let y = 1; y < h; y++) for (let x = 0; x < w; x++) assert.ok(p.cells.has(`${x},${y}`), `${key} ${x},${y}`);
        }
        // in the town: no reachable cell inside the box of a northern building, bar its open door
        const boxes = [[24, 4, 10, 7], [2, 11, 7, 6], [10, 11, 5, 6], [49, 9, 4, 7]];
        for (const [x0, y0, w, h] of boxes) {
            for (let y = y0 + (w === 4 || w === 5 ? 1 : 0); y < y0 + h; y++) {
                for (let x = x0; x < x0 + w; x++) {
                    if (doorAt(x, y)) continue;
                    assert.ok(!reach.has(`${x},${y}`), `${x},${y} is inside a building and can be walked to`);
                }
            }
        }
        // ...and the ground behind the west row cannot be reached at all
        for (let y = 7; y <= 16; y++) for (let x = 2; x <= 15; x++) assert.ok(doorAt(x, y) || !reach.has(`${x},${y}`), `${x},${y} behind the west row`);
    });

    test('Sapporo: the devhouse 3 base cast still stands on free ground, at nobody\'s door (#219)', () => {
        const cast = room.npcs.filter((n) => n.trip === 'devhouse3' && n.stay === 'Sapporo');
        assert.deepStrictEqual(cast.map((n) => n.name).sort(), ['Bailey', 'Damian', 'Dylan', 'Julia', 'Khoi', 'Sam', 'Xander']);
        const seen = new Set();
        for (const n of cast) {
            const k = `${n.gridX},${n.gridY}`;
            assert.ok(reach.has(k), `${n.name} at ${k} cannot be walked to`);
            assert.ok(!doorAt(n.gridX, n.gridY) && !doorAt(n.gridX, n.gridY - 1), `${n.name} at ${k} is on or in front of a door`);
            assert.ok(!seen.has(k), `two of the cast on ${k}`);
            seen.add(k);
        }
        // spread over both northern districts and the park: stage 2 stood Sam beside the corn tent and
        // Julia at the snow castle (she was on the Clock Tower's own stand cell); nobody else moved
        const where = Object.fromEntries(cast.map((n) => [n.name, [n.gridX, n.gridY]]));
        assert.deepStrictEqual(where, { Khoi: [38, 8], Sam: [20, 26], Xander: [35, 17], Bailey: [30, 11], Damian: [36, 12], Dylan: [24, 15], Julia: [6, 27] });
        // and Julia's line names what is behind her now, not the Clock Tower she left
        const julia = cast.find((n) => n.name === 'Julia');
        assert.ok(julia.dialogue.some((l) => /snow castle/.test(l)) && !julia.dialogue.some((l) => /Clock Tower/.test(l)), julia.dialogue.join(' | '));
        // the trip's start cell is free too, and still beside the avenue
        const home = cfg.trips.find ? cfg.trips.find((t) => t.id === 'devhouse3') : null;
        assert.ok(reach.has('33,12') && !doorAt(33, 12) && !doorAt(33, 11));
        if (home && home.home) assert.deepStrictEqual([home.home.room, home.home.x, home.home.y], ['Sapporo', 33, 12]);
    });

    test('Sapporo: its art is registered by its own tool, which check_generators runs (#219)', () => {
        const check = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/ART_TOOLS \+= \['generate_sapporo_art'\]/.test(check));
        const size = (key) => {
            const b = fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
            return [b.readUInt32BE(16), b.readUInt32BE(20)];
        };
        const keys = ['sapporo-station-front_0_0', 'sapporo-akarenga_0_0', 'sapporo-office-brick_0_0', 'sapporo-office-glass_0_0',
            'tanukikoji-gate_0_0', 'susukino-neon-corner_0_0', 'snow-sculpture-castle_0_0', 'sapporo-streetcar_0_0',
            'arcade-brick-autotile_center', 'arcade-brick-autotile_corner-se', 'snow-path-autotile_edge-n'];
        for (const key of keys) {
            const m = cfg.spriteMetadata[key], [w, h] = size(key);
            assert.ok(m, `${key} has no spriteMetadata`);
            assert.strictEqual(m.frameCount, 1);
            assert.ok(Math.abs(m.anchorX - 32 / w) < 1e-9 && Math.abs(m.anchorY - 32 / h) < 1e-9, `${key}: the anchor is the centre of its top-left cell`);
            assert.ok(cfg.tileNames[key], `${key} has no tileNames entry`);
        }
        // what stage 1 placed is in the palette
        for (const key of keys.slice(0, 4).concat(['arcade-brick-autotile_center'])) assert.ok(cfg.tilePalette.includes(key), key);
    });

    // ---- stage 2: Odori Park, rows 23-30 between Kita-Odori and Minami-Odori ----
    const fam = (x, y) => floor(x, y).replace(/_[a-z-]+$/, '');
    const BLOCKS = [[2, 13], [17, 29], [33, 43]];           // the three blocks the streets cut the park into
    const inPark = (x, y) => y >= 23 && y <= 30 && BLOCKS.some(([x0, x1]) => x >= x0 && x <= x1);
    const placed = () => Object.entries(layer('Collidables')).map(([xy, t]) => [...xy.split(',').map(Number), name(t)]);
    const footprint = (key, x0, y0) => [...prefab(key).cells].map((c) => c.split(',').map(Number)).map(([dx, dy]) => [x0 + dx, y0 + dy]);

    test('Odori Park: its own ground is a packed-snow path on snow, block to block (#219)', () => {
        // the path down the middle crosses all three blocks and reaches the TV Tower's plaza
        for (let x = 9; x <= 43; x++) {
            if (!BLOCKS.some(([x0, x1]) => x >= x0 && x <= x1)) continue;
            for (const y of [26, 27]) if (!solid(x, y)) assert.strictEqual(fam(x, y), 'snow-path-autotile', `${x},${y}`);
        }
        // the park's ground is snow and that path, nothing else: not the Clock Tower block's setts
        for (let y = 23; y <= 30; y++) for (let x = 2; x <= 43; x++) {
            if (inPark(x, y)) assert.ok(['snow-autotile', 'snow-path-autotile'].includes(fam(x, y)), `${x},${y} is ${floor(x, y)}`);
        }
        // and the path is the park's alone
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
            if (fam(x, y) === 'snow-path-autotile') assert.ok(y >= 23 && y <= 30 && x >= 2 && x <= 46, `${x},${y}`);
        }
        // the TV Tower's plaza is what it was
        for (const [x, y] of [[47, 23], [53, 30], [50, 26]]) assert.strictEqual(fam(x, y), 'grey-brick-autotile', `${x},${y}`);
    });

    test('Odori Park: a sculpture court, the fountain and the stalls, the TV Tower lawn - no two blocks alike (#219)', () => {
        assert.deepStrictEqual(at('snow-sculpture-castle_0_0'), [[4, 23]]);
        assert.deepStrictEqual(at('snow-sculpture-tanuki_0_0'), [[12, 23]]);
        assert.deepStrictEqual(at('odori-fountain_0_0'), [[22, 25]]);
        assert.deepStrictEqual(at('snowfest-stall-corn_0_0'), [[17, 23]]);
        assert.deepStrictEqual(at('snowfest-stall-drinks_0_0'), [[27, 23]]);
        assert.deepStrictEqual(at('snow-sculpture-bear_0_0'), [[38, 24]]);
        // what stands in each block, lamps, benches, banks and trees aside
        const own = BLOCKS.map(([x0, x1]) => placed().filter(([x, y, k]) => x >= x0 && x <= x1 && y >= 23 && y <= 30
            && !/^(odori-lamp-post|odori-bench|snowbank-|tree-3-)/.test(k)).map(([, , k]) => k.replace(/_0_0$/, '')).sort());
        assert.deepStrictEqual(own, [['snow-sculpture-castle', 'snow-sculpture-tanuki'],
            ['odori-fountain', 'snowfest-stall-corn', 'snowfest-stall-drinks'], ['snow-sculpture-bear']]);
        // every block is lit and has somewhere to sit, and the old rows of red lanterns are gone
        for (const [x0, x1] of BLOCKS) {
            const here = placed().filter(([x, y]) => x >= x0 && x <= x1 && y >= 23 && y <= 30).map(([, , k]) => k);
            assert.ok(here.filter((k) => k === 'odori-lamp-post_0_0').length >= 2, `block ${x0}: lamps`);
            assert.ok(here.filter((k) => k === 'odori-bench_0_0').length >= 2, `block ${x0}: benches`);
            assert.ok(here.some((k) => /^snowbank-/.test(k)), `block ${x0}: snowbanks`);
            assert.ok(!here.some((k) => /^red-lanterns/.test(k)), `block ${x0}: no red lanterns`);
        }
        // the lamps are lit by the lamp rule (their key says so), the tents by the glow table
        assert.ok(/lamp-post/.test('odori-lamp-post_0_0'));
        // you can get into every block from both streets and along the path
        for (const [x, y] of [[9, 23], [6, 30], [23, 23], [23, 30], [35, 23], [38, 30], [13, 26], [17, 27], [29, 26], [33, 27], [43, 26]]) {
            assert.ok(reach.has(`${x},${y}`), `${x},${y} is a way into the park`);
        }
        // the frozen pond went (Asahikawa keeps the frozen water), and the sakura with it
        for (const l of ['Water', 'Collidables', 'Tops']) {
            for (const t of Object.values(layer(l))) assert.ok(!/^ice-pond|^sakura/.test(name(t)), name(t));
        }
        // nothing of stages 3-4 moved: the south lane's houses are where they were
        const houses = room.transporters.filter((t) => /^HouseSapporo/.test(t.targetRoom)).map((t) => t.targetRoom).sort();
        assert.deepStrictEqual(houses, ['HouseSapporo1', 'HouseSapporo2', 'HouseSapporo3', 'HouseSapporo4', 'HouseSapporo5', 'HouseSapporo6']);
    });

    test('Odori Park: nobody walks inside a sculpture, a tent or the fountain, and each can be walked up to (#219)', () => {
        const things = [['snow-sculpture-castle', 4, 23, 5, 4], ['snow-sculpture-tanuki', 12, 23, 2, 3], ['snow-sculpture-bear', 38, 24, 3, 2],
            ['snowfest-stall-corn', 17, 23, 3, 3], ['snowfest-stall-drinks', 27, 23, 3, 3], ['odori-fountain', 22, 25, 3, 3]];
        for (const [key, x0, y0, w, h] of things) {
            const p = prefab(key);
            assert.deepStrictEqual([p.w, p.h], [w, h], key);
            for (const [x, y] of footprint(key, x0, y0)) assert.ok(solid(x, y) && !reach.has(`${x},${y}`), `${key}: ${x},${y}`);
            // the bottom two rows are solid all the way across; a tent, the tanuki and the bear all over
            for (let dx = 0; dx < w; dx++) for (let dy = Math.max(0, h - 2); dy < h; dy++) assert.ok(p.cells.has(`${dx},${dy}`), `${key} ${dx},${dy}`);
            if (!/castle|fountain/.test(key)) assert.strictEqual(p.cells.size, w * h, `${key} is solid all over`);
            // the row in front of it (south) is free ground
            for (let dx = 0; dx < w; dx++) assert.ok(reach.has(`${x0 + dx},${y0 + h}`), `${key}: ${x0 + dx},${y0 + h} in front of it`);
        }
        // the castle collides up its keep (the middle three columns) and the fountain up its stem
        const castle = prefab('snow-sculpture-castle'), fountain = prefab('odori-fountain');
        for (const dy of [0, 1]) for (const dx of [1, 2, 3]) assert.ok(castle.cells.has(`${dx},${dy}`), `castle ${dx},${dy}`);
        assert.ok(fountain.cells.has('1,0') && !fountain.cells.has('0,0') && !fountain.cells.has('2,0'));
        // no lamp, bench, bank or tree stands on the path's two rows
        for (const [x, y, k] of placed()) {
            if (!inPark(x, y) || !/^(odori-|snowbank-|tree-3-base)/.test(k) || k === 'odori-fountain_0_0') continue;
            assert.ok(y !== 26 && y !== 27 || k === 'odori-lamp-post_0_0' && x === 2, `${k} at ${x},${y} is on the path`);
        }
        for (let x = 9; x <= 43; x++) if (inPark(x, 26) && !(x >= 22 && x <= 24)) assert.ok(reach.has(`${x},26`) && reach.has(`${x},27`), `the path at column ${x}`);
    });

    test('Odori Park: the tents and the things to look at answer a bump, and the blog pipeline has their spots (#219)', () => {
        const ctx = require('vm').createContext({ window: {} });
        for (const f of ['utils/Interactions.js']) require('vm').runInContext(fs.readFileSync(path.join(GV2, 'src', f), 'utf8') + '\nthis.Interactions = Interactions;', ctx);
        const I = ctx.Interactions;
        const hit = (key) => I.match(key, room, {});
        // the hot-drinks tent sells over its counter (Shop.VENUES.stall); the rest say a line
        assert.deepStrictEqual({ ...hit('snowfest-stall-drinks_0_0') }, { kind: 'stall', group: 'shop', footprint: true });
        const shop = fs.readFileSync(path.join(GV2, 'src', 'Shop.js'), 'utf8');
        const row = /stall:\s*\{ title: 'HOT DRINKS',\s*sells: i => i\.id === '([a-z-]+)' \|\| i\.id === '([a-z-]+)' \}/.exec(shop);
        assert.ok(row, 'Shop.VENUES.stall');
        for (const id of [row[1], row[2]]) assert.ok(new RegExp(`\\{ id: '${id}',[^\\n]*category: 'drink'`).test(shop), `${id} is a drink in the catalogue`);
        const says = {};
        for (const key of ['snowfest-stall-corn_0_0', 'snow-sculpture-castle_0_0', 'snow-sculpture-tanuki_0_0', 'snow-sculpture-bear_0_0', 'odori-fountain_0_0']) {
            const h = hit(key);
            assert.ok(h && h.group === 'flavour' && h.footprint && h.say, key);
            says[h.say] = key;
        }
        assert.strictEqual(Object.keys(says).length, 5, 'each has a line of its own');
        // the placement spots: LANDMARKS rows scoped to Sapporo, and the district lists them
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        for (const [prefix, label] of [['snow-sculpture-castle_', 'the snow castle'], ['snow-sculpture-tanuki_', 'the snow tanuki'],
            ['snow-sculpture-bear_', 'the snow bear'], ['snowfest-stall-corn_', 'the snow festival stalls'],
            ['odori-fountain_', 'the Odori fountain'], ['snowfest-stall-drinks_', 'Odori Park']]) {
            assert.ok(new RegExp(`\\('${prefix}', '${label}', \\(-?\\d+, -?\\d+\\), \\{'rooms': \\('Sapporo',\\)\\}\\)`).test(py), label);
        }
        const odori = cfg.districts.Sapporo.find((d) => d.key === 'odori-park');
        assert.deepStrictEqual(odori.bounds, [2, 23, 53, 30]);
        assert.deepStrictEqual(odori.spots, ['Odori Park', 'the Odori fountain', 'the Sapporo TV Tower', 'the snow bear', 'the snow castle',
            'the snow festival stalls', 'the snow tanuki']);
        const [sx, sy] = odori.stand;
        assert.ok(reach.has(`${sx},${sy}`) && fam(sx, sy) === 'snow-path-autotile', 'the district stands its visitor on the path');
        assert.ok(/snow castle/.test(odori.description) && /stalls/.test(odori.description) && /TV Tower/.test(odori.description));
        // the art stage 2 placed is registered and in the palette
        for (const key of ['snow-sculpture-castle_0_0', 'snow-sculpture-tanuki_0_0', 'snow-sculpture-bear_0_0', 'snowfest-stall-corn_0_0',
            'snowfest-stall-drinks_0_0', 'odori-fountain_0_0', 'odori-lamp-post_0_0', 'odori-bench_0_0', 'snowbank-h_0_0', 'snowbank-v_0_0',
            'snowbank-pile_0_0', 'snow-path-autotile_center']) {
            assert.ok(cfg.spriteMetadata[key] && cfg.tileNames[key] && cfg.tilePalette.includes(key), key);
        }
    });
};
