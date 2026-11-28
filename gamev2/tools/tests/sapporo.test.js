// Sapporo's rebuild (issue #219). Stage 1 is the north of the town: the Sapporo Station front and the
// Clock Tower block. Stage 2 is Odori Park. Stage 3 is Tanukikoji, the covered arcade. Stage 4 is Susukino and
// the streetcar, in eight rows the room grew by. All of it is data the
// generators write (tools/generate_sapporo.py, generate_sapporo_art.py, make_prefabs.py, generate_stations.py,
// generate_konbinis.py, generate_houses.py --lobbies / --shops).
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
        assert.deepStrictEqual(at('seven-eleven_0_0'), [[38, 34]], 'the konbini moved to the arcade with stage 3');
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
        assert.strictEqual(doorAt(18, 18).targetRoom, 'DonTakoteSapporo');
        // every door of the town is one of: the station's pair, the konbini, the store, a lobby, a shop - no house is left
        const kinds = room.transporters.map((t) => t.targetRoom.replace(/\d+$/, '')).sort();
        assert.deepStrictEqual([...new Set(kinds)], ['ChikagaiSapporo', 'DonTakoteSapporo', 'KonbiniSapporo', 'LobbySapporo', 'SapporoStation', 'ShopSapporo']);
    });

    test('Sapporo: the two northern districts stand on ground of their own (#219)', () => {
        const fam = (x, y) => floor(x, y).replace(/_[a-z-]+$/, '');
        // Station front: the plaza, the strip by the station and the forecourt of the west row
        for (const [x, y] of [[23, 11], [29, 18], [26, 14], [28, 11], [29, 11], [36, 9], [5, 17], [12, 18]]) {
            assert.strictEqual(fam(x, y), 'brown-brick-autotile', `${x},${y}`);      // stone slabs: the red brick is Tanukikoji's alone (stage 3)
        }
        // Clock Tower block: from the avenue to the east hedge
        for (const [x, y] of [[34, 12], [39, 18], [43, 15], [47, 14], [53, 18], [51, 16]]) {
            assert.strictEqual(fam(x, y), 'flat-grey-brick-autotile', `${x},${y}`);
        }
        // neither is the paving of anywhere else in town, and the two differ
        for (let y = KITA; y < H; y++) for (let x = 0; x < W; x++) assert.notStrictEqual(fam(x, y), 'brown-brick-autotile', `${x},${y}`);
        for (let y = 0; y < KITA; y++) for (let x = 0; x < W; x++) assert.notStrictEqual(fam(x, y), 'arcade-brick-autotile', `${x},${y}`);
        for (let y = 0; y < KITA; y++) for (let x = 0; x < W; x++) assert.notStrictEqual(fam(x, y), 'grey-brick-autotile', `${x},${y}`);
        // the pavement along Kita-Odori is still pavement
        for (let x = 2; x <= 53; x++) if (x < 30 || x > 32) assert.strictEqual(fam(x, 19), 'light-concrete-autotile', `${x},19`);    // 30-32: the avenue
    });

    test('Sapporo: the office blocks have lobbies, and nobody can walk behind a building of the north (#219)', () => {
        const lobby = (k) => cfg.rooms[k].lobby;
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^LobbySapporo/.test(k)), ['LobbySapporo1', 'LobbySapporo2', 'LobbySapporo3']);    // 3: Susukino's (stage 4)
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
        // spread over all five districts: stage 2 stood Sam beside the corn tent and Julia at the snow castle (she
        // was on the Clock Tower's own stand cell); stage 3 stood Xander inside the Tanukikoji gate (from 35,17 by
        // the Clock Tower) and Khoi beside the crab shop's door (from 38,8); stage 4 stood Dylan under the fox board
        // (from 24,15 on the station plaza) and moved Khoi on to the ramen gate. Bailey is still at the station and
        // Damian at the Clock Tower
        const where = Object.fromEntries(cast.map((n) => [n.name, [n.gridX, n.gridY]]));
        assert.deepStrictEqual(where, { Khoi: [25, 47], Sam: [20, 26], Xander: [21, 38], Bailey: [30, 11], Damian: [36, 12], Dylan: [36, 47], Julia: [6, 27] });
        const districtOf = (n) => (cfg.districts.Sapporo.find((d) => n.gridX >= d.bounds[0] && n.gridX <= d.bounds[2] && n.gridY >= d.bounds[1] && n.gridY <= d.bounds[3]) || {}).key;
        assert.deepStrictEqual(Object.fromEntries(cast.map((n) => [n.name, districtOf(n)])), { Khoi: 'susukino', Dylan: 'susukino', Sam: 'odori-park',
            Julia: 'odori-park', Xander: 'tanukikoji', Bailey: 'station-front', Damian: 'clock-tower' });
        // none of the three says where they stand, so their lines are as they were
        for (const who of ['Khoi', 'Xander', 'Dylan']) {
            const lines = cast.find((n) => n.name === who).dialogue.join(' ');
            assert.ok(!/Clock Tower|station|behind me|here by|next to/i.test(lines), `${who}: ${lines}`);
        }
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
            ['odori-fountain', 'snowfest-stall-corn', 'snowfest-stall-drinks'], ['chikagai-entrance-snow', 'snow-sculpture-bear']]);
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

    // ---- stage 3: Tanukikoji, the covered arcade south of Minami-Odori --------------------------------
    const ARCADE = [[17, 29], [33, 43]];        // the two stretches of the street, either side of the avenue
    const inArcade = (x) => ARCADE.some(([x0, x1]) => x >= x0 && x <= x1);

    test('Tanukikoji: one street on red brick that is its alone, under a roof from both sides (#219)', () => {
        // rows 38-40 of both stretches, and the way in under the gate: arcade-brick, and nowhere else in town
        const brick = new Set();
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (fam(x, y) === 'arcade-brick-autotile') brick.add(`${x},${y}`);
        const want = new Set();
        for (const [x0, x1] of ARCADE) for (let x = x0; x <= x1; x++) for (let y = 38; y <= 40; y++) want.add(`${x},${y}`);
        for (const x of [22, 23]) for (let y = 34; y <= 37; y++) want.add(`${x},${y}`);
        assert.deepStrictEqual([...brick].sort(), [...want].sort());
        for (const k of want) assert.ok(reach.has(k), `${k} of the arcade street can be walked`);
        // the north row: shopfronts, the gate, the konbini, an upright sign at each end of each stretch
        assert.deepStrictEqual(at('tanukikoji-shop-souvenir_0_0'), [[18, 34]]);
        assert.deepStrictEqual(at('tanukikoji-gate_0_0'), [[21, 34]]);
        assert.deepStrictEqual(at('tanukikoji-shop-crab_0_0'), [[25, 34]]);
        assert.deepStrictEqual(at('tanukikoji-shop-drug_0_0'), [[35, 34]]);
        assert.deepStrictEqual(at('tanukikoji-end-sign_0_0').sort((a, b) => a[0] - b[0]), [[17, 34], [28, 34], [34, 34], [41, 34]]);
        // the south row: seven modules, never two alike side by side, their roof over the street's south row
        const south = [...at('tanukikoji-south-row-a_0_0').map((c) => [...c, 'a']), ...at('tanukikoji-south-row-b_0_0').map((c) => [...c, 'b'])]
            .sort((p, q) => p[0] - q[0]);
        assert.deepStrictEqual(south.map(([x, y]) => [x, y]), [[17, 40], [20, 40], [23, 40], [26, 40], [34, 40], [37, 40], [40, 40]]);
        south.forEach(([x, , v], i) => { if (i && south[i - 1][0] === x - 3) assert.notStrictEqual(south[i - 1][2], v, `two alike at ${x}`); });
        for (const [x] of south) for (let dx = 0; dx < 3; dx++) {
            assert.ok(!solid(x + dx, 40), `${x + dx},40 is walked under the roof`);
            assert.ok(solid(x + dx, 41) && solid(x + dx, 42), `${x + dx}: the south row is a wall`);
        }
        // no generic townhouse, anywhere in Sapporo, and no House interior left behind
        for (const t of Object.values(layer('Collidables'))) assert.ok(!/^(building-entrance|house-|machiya-)/.test(name(t)), name(t));
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^HouseSapporo/.test(k)), []);
        // the streets the arcade crosses are still streets; since stage 4 they run on down to Susukino's tram street
        for (let y = 34; y <= 46; y++) for (const x of [14, 15, 16, 30, 31, 32, 44, 45, 46]) assert.ok(/^road-/.test(floor(x, y)), `${x},${y}`);
        // and the rails are on that street only: none in the arcade or anywhere north of it
        for (const [xy, t] of Object.entries(layer('Floor'))) if (/^tram-rail/.test(name(t))) assert.strictEqual(Number(xy.split(',')[1]), 48, xy);
    });

    test('Tanukikoji: you come in under the gate or at either end, and nobody gets behind a shopfront (#219)', () => {
        // through the gate from Minami-Odori: two cells wide, its posts and the ends of its board solid
        const gate = prefab('tanukikoji-gate');
        assert.deepStrictEqual([...gate.cells].sort(), ['0,0', '0,1', '0,2', '0,3', '3,0', '3,1', '3,2', '3,3']);
        for (const x of [22, 23]) for (let y = 33; y <= 38; y++) assert.ok(reach.has(`${x},${y}`), `${x},${y} is the way in`);
        // at each end the street meets the road beside it
        for (const [x, y] of [[16, 39], [30, 39], [32, 39], [44, 39]]) assert.ok(reach.has(`${x},${y}`) && /^road-/.test(floor(x, y)), `${x},${y}`);
        // no cell of the north row but a door and the gate's way through can be stood on, roof row included, kerb to kerb
        const doors = [[19, 37], [26, 37], [36, 37], [39, 37]];
        for (let x = 17; x <= 43; x++) {
            if (!inArcade(x)) continue;
            for (let y = 34; y <= 37; y++) {
                const open = (x === 22 || x === 23) || doors.some(([dx, dy]) => dx === x && dy === y);
                assert.strictEqual(reach.has(`${x},${y}`), open, `${x},${y}`);
                if (!(x === 42 && y === 36)) assert.strictEqual(solid(x, y), !open, `${x},${y}`);      // 42,36: the 7-Eleven sign's top, walled in
            }
        }
        // nothing south of the street can be reached but down the three streets (stage 4 opened them to Susukino):
        // the south row, the corners' fence and the shrubs at the ends of the stretches are one closed line
        for (let x = 0; x < W; x++) assert.strictEqual(reach.has(`${x},42`), [14, 15, 16, 30, 31, 32, 44, 45, 46].includes(x), `${x},42`);
        for (let x = 17; x <= 43; x++) if (inArcade(x)) assert.ok(!reach.has(`${x},41`), `${x},41`);
        // the shop prefabs are solid all over (no walk-behind roof row) with the door in the middle of the bottom row
        for (const k of ['souvenir', 'crab', 'drug']) {
            const p = prefab(`tanukikoji-shop-${k}`);
            assert.strictEqual(p.cells.size, 12, k);
            assert.deepStrictEqual(p.doors, [[1, 3]], k);
        }
    });

    test('Tanukikoji: no sealed building - each shop opens into a shop floor that sells, the konbini is on the arcade (#219)', () => {
        const shops = { ShopSapporo1: [19, 37, 'Souvenirs · Sapporo', 'souvenirs'], ShopSapporo2: [26, 37, 'Crab shop · Sapporo', 'crab'],
            ShopSapporo3: [36, 37, 'Drugstore · Sapporo', 'drugstore'] };
        // (ShopSapporo4 is Susukino's karaoke bar, stage 4: tested with Susukino below)
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^ShopSapporo/.test(k)).sort(), [...Object.keys(shops), 'ShopSapporo4']);
        const ctx = require('vm').createContext({ window: {} });
        require('vm').runInContext(fs.readFileSync(path.join(GV2, 'src', 'utils', 'Interactions.js'), 'utf8') + '\nthis.Interactions = Interactions;', ctx);
        const src = fs.readFileSync(path.join(GV2, 'src', 'Shop.js'), 'utf8');
        const catalogue = new Set([...src.matchAll(/\{ id: '([a-z-]+)',\s+name:/g)].map((m) => m[1]));
        for (const [key, [x, y, title, menu]] of Object.entries(shops)) {
            const r = cfg.rooms[key];
            // the door pairs both ways: in to the cell above the mat, out to the street cell in front of the door
            const d = doorAt(x, y);
            assert.ok(d && d.targetRoom === key && !solid(x, y), `${key}: its door at ${x},${y}`);
            assert.deepStrictEqual(r.transporters.map((t) => [t.targetRoom, t.targetX, t.targetY]), [['Sapporo', x, y + 1]], key);
            assert.deepStrictEqual([d.targetX, d.targetY], [r.transporters[0].gridX, r.transporters[0].gridY - 1], key);
            assert.ok(reach.has(`${x},${y + 1}`), `${key}: the cell in front of its door`);
            // what it is: an interior named by its type, not a store (no stamp), with that type's list on the counter
            assert.strictEqual(r.name, title);
            assert.ok(r.interior === true && r.shopEnabled === false && r.shopMenu === menu, key);
            assert.deepStrictEqual(r.shop, { host: 'Sapporo', door: [x, y], type: menu });
            const hit = ctx.Interactions.match('office-counter2_0_0', r, { [menu]: {} });
            assert.deepStrictEqual({ ...hit }, { kind: menu, group: 'shop', footprint: true }, `${key}: a bump on the counter opens its list`);
            assert.strictEqual(ctx.Interactions.match('office-shelf-snacks_0_0', r, { [menu]: {} }), null, 'the shelves are only to look at');
            // one layout: a counter with a till, four shelves at the back wall, the mat
            const keys = Object.values(layer('Collidables', r)).map(name).concat(Object.values(layer('Tops', r)).map(name), Object.values(layer('Over Floor', r)).map(name));
            assert.strictEqual(keys.filter((k) => k === 'office-counter2_0_0').length, 1, key);
            assert.ok(keys.includes('office-register_0_0') && keys.includes('lobby-mat_0_0'), key);
            // its list: two or three things, every one of them in the catalogue
            const row = new RegExp(`${menu}:\\s*\\{ title: '[A-Z ]+',\\s*sells: i => \\[([^\\]]+)\\]\\.includes\\(i\\.id\\) \\}`).exec(src);
            assert.ok(row, `Shop.VENUES.${menu}`);
            const ids = row[1].split(',').map((s) => s.trim().replace(/'/g, ''));
            assert.ok(ids.length >= 2 && ids.length <= 3 && ids.every((id) => catalogue.has(id)), `${menu}: ${ids}`);
        }
        // the same floor plan in all three (one layout): only the shelves differ
        const plan = (k) => JSON.stringify(Object.keys(layer('Colliders', cfg.rooms[k])).sort());
        assert.ok(plan('ShopSapporo1') === plan('ShopSapporo2') && plan('ShopSapporo2') === plan('ShopSapporo3'));
        // the 7-Eleven: on the arcade, same room key and name (the Stamp Card's), its door pairs both ways
        const k = cfg.rooms.KonbiniSapporo1, kd = doorAt(39, 37);
        assert.strictEqual(k.name, '7-Eleven · Sapporo');
        assert.ok(kd && kd.targetRoom === 'KonbiniSapporo1' && !solid(39, 37) && fam(39, 38) === 'arcade-brick-autotile');
        for (const t of k.transporters) assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Sapporo', 39, 38]);
        assert.ok(k.transporters.some((t) => t.gridX === kd.targetX && t.gridY === kd.targetY + 1), 'you arrive just inside its mat');
        assert.ok(!doorAt(45, 18) && !solid(45, 18), 'nothing is left of the old door by the Clock Tower');
        assert.strictEqual(room.transporters.filter((t) => /^Konbini/.test(t.targetRoom)).length, 1);
    });

    test('Tanukikoji: its landmarks, its district and the glow of its gate (#219)', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        const spots = { 'Tanukikoji arcade': ['tanukikoji-gate_', 21, 38], 'the crab shop': ['tanukikoji-shop-crab_', 27, 38],
            'the souvenir shop': ['tanukikoji-shop-souvenir_', 18, 38] };
        for (const [label, [prefix, sx, sy]] of Object.entries(spots)) {
            const m = new RegExp(`\\('${prefix}', '${label}', \\((-?\\d+), (-?\\d+)\\), \\{'rooms': \\('Sapporo',\\)\\}\\)`).exec(py);
            assert.ok(m, label);
            const [[ox, oy]] = at(prefix + '0_0');
            assert.deepStrictEqual([ox + Number(m[1]), oy + Number(m[2])], [sx, sy], label);
            // a stand cell is on the arcade street, never a door or the cell in front of one
            assert.ok(reach.has(`${sx},${sy}`) && fam(sx, sy) === 'arcade-brick-autotile', label);
            assert.ok(!doorAt(sx, sy) && !doorAt(sx, sy - 1), `${label} stands at a door`);
        }
        const d = cfg.districts.Sapporo.find((x) => x.key === 'tanukikoji');
        assert.deepStrictEqual([d.name, d.bounds, d.stand], ['Tanukikoji', [17, 34, 43, 42], [24, 39]]);
        assert.deepStrictEqual(d.spots, ['Tanukikoji arcade', 'the 7-Eleven', 'the crab shop', 'the souvenir shop']);
        assert.ok(/covered shopping arcade/.test(d.description) && /souvenirs/.test(d.description) && /crab/.test(d.description) && /7-Eleven/.test(d.description));
        assert.ok(reach.has(d.stand.join(',')) && !doorAt(d.stand[0], d.stand[1] - 1));
        // the 7-Eleven left the Clock Tower block's list and words
        const clock = cfg.districts.Sapporo.find((x) => x.key === 'clock-tower');
        assert.deepStrictEqual(clock.spots, ['the Sapporo Clock Tower']);
        assert.ok(!/7-Eleven/.test(clock.description));
        // districts of one room never overlap
        const ds = cfg.districts.Sapporo;
        for (const a of ds) for (const b of ds) if (a !== b) {
            assert.ok(a.bounds[2] < b.bounds[0] || b.bounds[2] < a.bounds[0] || a.bounds[3] < b.bounds[1] || b.bounds[3] < a.bounds[1], `${a.key} / ${b.key}`);
        }
        // the gate glows at night from the Glows table; everything placed is registered
        assert.ok(/'tanukikoji-gate_0_0': \[/.test(fs.readFileSync(path.join(GV2, 'src', 'utils', 'Glows.js'), 'utf8')));
        for (const key of ['tanukikoji-gate_0_0', 'tanukikoji-shop-souvenir_0_0', 'tanukikoji-shop-crab_0_0', 'tanukikoji-shop-drug_0_0',
            'tanukikoji-end-sign_0_0', 'tanukikoji-south-row-a_0_0', 'tanukikoji-south-row-b_0_0']) {
            assert.ok(cfg.spriteMetadata[key] && cfg.tileNames[key] && cfg.tilePalette.includes(key), key);
        }
    });

    // ---- stage 4: Susukino and the streetcar, in the eight rows the room grew by (43-50) ------------------
    const STREETS = [14, 15, 16, 30, 31, 32, 44, 45, 46];
    const vmWith = (file, expose) => {
        const c = require('vm').createContext({ window: {} });
        require('vm').runInContext(fs.readFileSync(path.join(GV2, 'src', file), 'utf8') + `\nthis.${expose} = ${expose};`, c);
        return c[expose];
    };

    test('Susukino: the room grew eight rows south and is still closed, clear of every other map (#219)', () => {
        assert.deepStrictEqual([W, H], [56, 51]);
        assert.deepStrictEqual(room.boundary, [[0, 0], [56, 0], [56, 51], [0, 51]]);
        // the world file: the same slot, grown northward (its south edge and its columns are where they were),
        // and the Map's picture of it has the new size
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        const at_ = Object.fromEntries(world.maps.map((m) => [path.basename(m.fileName, '.tmj'), m]));
        const s = at_.sapporo;
        assert.deepStrictEqual([s.x, s.width, s.height, s.y + s.height], [256, 56 * 64, 51 * 64, -512]);
        for (const [k, m] of Object.entries(at_)) {
            if (k === 'sapporo') continue;
            assert.ok(s.x + s.width <= m.x || m.x + m.width <= s.x || s.y + s.height <= m.y || m.y + m.height <= s.y, `Sapporo overlaps ${k}`);
        }
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        assert.deepStrictEqual(map.rooms.Sapporo.cells, [56, 51]);
        const tmj = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'sapporo.tmj'), 'utf8'));
        assert.deepStrictEqual([tmj.width, tmj.height], [56, 51]);
        // closed all round: nobody reaches the outermost rows or columns, the rails run out through the hedge
        // (those four cells are shut), and the south kerb is one line of fence, poles, the bench and the stop sign
        for (let x = 0; x < W; x++) assert.ok(solid(x, 50) && !reach.has(`${x},50`), `${x},50`);
        for (let y = 0; y < H; y++) for (const x of [0, 1, 54, 55]) assert.ok(!reach.has(`${x},${y}`), `${x},${y}`);
        for (const x of [0, 1, 54, 55]) assert.ok(solid(x, 48) && /^tram-rail-h/.test(floor(x, 48)), `${x},48`);
        // every cell has a floor
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) assert.ok(floor(x, y), `${x},${y} has no floor`);
    });

    test('Susukino: dark wet asphalt and the rails are its ground, and nobody else\'s (#219)', () => {
        const wet = new Set();
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (fam(x, y) === 'susukino-asphalt-autotile') wet.add(`${x},${y}`);
        const want = new Set();
        for (let x = 2; x <= 53; x++) want.add(`${x},47`);                                       // the north side of the tram street
        for (const [x0, x1] of ARCADE) for (let x = x0; x <= x1; x++) for (let y = 43; y <= 46; y++) want.add(`${x},${y}`);
        for (const x of STREETS) for (let y = 43; y <= 46; y++) want.delete(`${x},${y}`);
        assert.deepStrictEqual([...wet].sort(), [...want].sort());
        // it is not a road tile (the blog pipeline stands people on it), and none of the other four grounds is down here
        assert.ok(!/^road/.test('susukino-asphalt-autotile'));
        for (let y = 43; y < H; y++) for (let x = 0; x < W; x++) {
            assert.ok(!['arcade-brick-autotile', 'snow-path-autotile', 'brown-brick-autotile', 'flat-grey-brick-autotile', 'grey-brick-autotile'].includes(fam(x, y)), `${x},${y}`);
        }
        // the track: row 48 from edge to edge, the crossing piece where the avenue meets it, and you can walk on it
        for (let x = 0; x < W; x++) {
            assert.strictEqual(floor(x, 48), x >= 30 && x <= 32 ? 'tram-rail-cross_0_0' : 'tram-rail-h_0_0', `${x},48`);
            if (x >= 2 && x <= 53) assert.ok(!solid(x, 48) && reach.has(`${x},48`), `${x},48 can be crossed`);
            assert.ok(/^road-edge-bottom|^light-concrete/.test(floor(x, 49)), `${x},49`);
        }
        for (let x = 2; x <= 53; x++) assert.ok(reach.has(`${x},47`), `${x},47`);
        // the three streets come down to it
        for (const x of STREETS) for (let y = 41; y <= 47; y++) assert.ok(reach.has(`${x},${y}`), `${x},${y}`);
        for (const key of ['susukino-asphalt-autotile_center', 'susukino-asphalt-autotile_edge-n', 'tram-rail-h_0_0', 'tram-rail-cross_0_0']) {
            assert.ok(cfg.spriteMetadata[key] && cfg.tileNames[key] && cfg.tilePalette.includes(key), key);
        }
    });

    test('Susukino: the neon corner, the karaoke bar and the ramen alley behind its gate - nobody gets behind them (#219)', () => {
        assert.deepStrictEqual(at('susukino-neon-corner_0_0'), [[33, 40]], 'on the corner of the avenue and the tram street');
        assert.deepStrictEqual(at('susukino-karaoke_0_0'), [[39, 42]]);
        assert.deepStrictEqual(at('susukino-ramen-gate_0_0'), [[27, 44]]);
        assert.deepStrictEqual(at('susukino-ramen-stall-a_0_0').sort((a, b) => a[0] - b[0]), [[18, 42], [24, 42]]);
        assert.deepStrictEqual(at('susukino-ramen-stall-b_0_0'), [[21, 42]], 'never two alike side by side');
        // the prefabs: the neon corner collides from its second row down, the karaoke bar and a counter all over,
        // the gate only at its posts
        const neon = prefab('susukino-neon-corner'), kara = prefab('susukino-karaoke');
        assert.deepStrictEqual([neon.w, neon.h, neon.doors, neon.cells.size], [5, 7, [[2, 6]], 30]);
        for (let x = 0; x < 5; x++) assert.ok(!neon.cells.has(`${x},0`));
        assert.deepStrictEqual([kara.w, kara.h, kara.doors, kara.cells.size], [4, 5, [[1, 4]], 20]);
        assert.deepStrictEqual([...prefab('susukino-ramen-gate').cells].sort(), ['0,2', '2,2']);
        for (const v of 'ab') assert.strictEqual(prefab(`susukino-ramen-stall-${v}`).cells.size, 9);
        // east of the avenue (columns 33-43, rows 41-46): nothing can be stood on but the two doors; the only cells
        // anybody is ever behind the neon corner on are the arcade street's last row, under the top of its board
        const doors = [[35, 46], [40, 46]];
        for (let x = 33; x <= 43; x++) for (let y = 41; y <= 46; y++) {
            const open = doors.some(([dx, dy]) => dx === x && dy === y);
            assert.strictEqual(reach.has(`${x},${y}`), open, `${x},${y}`);
        }
        for (let x = 33; x <= 37; x++) assert.ok(reach.has(`${x},40`) && fam(x, 40) === 'arcade-brick-autotile', `${x},40`);
        for (let x = 33; x <= 43; x++) assert.ok(reach.has(`${x},47`), `${x},47 in front of the row`);
        // west of it: the alley is row 45, columns 18-28, one cell wide, and the only way in is under the gate
        for (let x = 17; x <= 29; x++) for (let y = 41; y <= 46; y++) {
            const open = (y === 45 && x >= 18 && x <= 28) || (x === 28 && y === 46);
            assert.strictEqual(reach.has(`${x},${y}`), open, `${x},${y}`);
        }
        assert.ok(reach.has('28,47') && !doorAt(28, 46) && !doorAt(28, 47));
        // nobody is ever stood where they could wander into the gate's mouth and shut the alley (NPCManager: a
        // wanderer keeps within npcWanderRadius cells of home): not the cast, not a spot the blog pipeline offers
        const radius = cfg.game.npcWanderRadius;
        assert.ok(Number.isInteger(radius) && radius >= 1);
        const homes = room.npcs.map((n) => [n.name, n.gridX, n.gridY]).concat(cfg.districts.Sapporo.map((d) => [d.key, ...d.stand]));
        for (const [who, x, y] of homes) {
            for (const [gx, gy] of [[28, 46], [28, 45]]) assert.ok(Math.abs(x - gx) > radius || Math.abs(y - gy) > radius, `${who} at ${x},${y} can wander to ${gx},${gy}`);
        }
        // a lantern post either side lights it (the lamp rule: their keys say so), poles of neon signs light the rest
        assert.deepStrictEqual(at('ramen-alley-lanterns_0_0').sort((a, b) => a[0] - b[0]), [[21, 45], [26, 45]]);
        assert.deepStrictEqual(at('susukino-neon-lanterns_0_0').sort((a, b) => a[0] - b[0]), [[12, 45], [38, 45], [43, 45], [50, 45]]);
        for (const k of ['ramen-alley-lanterns_0_0', 'susukino-neon-lanterns_0_0']) assert.ok(/lamp-post|-lanterns/.test(k));
        // nothing of Asahikawa's ramen kit, and no generic house, is used down here
        for (const [x, y, k] of placed()) if (y >= 42) assert.ok(!/^(asahikawa-|ramen-(banner|crates|stockpot|miso|shoyu|narrow)|building-|house-|machiya-|yatai-)/.test(k), `${k} at ${x},${y}`);
        for (const key of ['susukino-neon-corner_0_0', 'susukino-karaoke_0_0', 'susukino-ramen-gate_0_0', 'susukino-ramen-stall-a_0_0',
            'susukino-ramen-stall-b_0_0', 'susukino-neon-lanterns_0_0', 'ramen-alley-lanterns_0_0', 'tram-pole_0_0', 'sapporo-streetcar_0_0']) {
            assert.ok(cfg.spriteMetadata[key] && cfg.tileNames[key], key);
            if (key !== 'sapporo-streetcar_0_0') assert.ok(cfg.tilePalette.includes(key), key);
        }
    });

    test('Susukino: no sealed building - a lobby, a bar and three counters that sell (#219)', () => {
        const src = fs.readFileSync(path.join(GV2, 'src', 'Shop.js'), 'utf8');
        const catalogue = new Set([...src.matchAll(/\{ id: '([a-z-]+)',\s+name:/g)].map((m) => m[1]));
        const I = vmWith('utils/Interactions.js', 'Interactions');
        const list = (menu) => {
            const row = new RegExp(`\\b${menu}:\\s*\\{ title: '([A-Z ]+)',\\s*sells: i => \\[([^\\]]+)\\]\\.includes\\(i\\.id\\) \\}`).exec(src);
            assert.ok(row, `Shop.VENUES.${menu}`);
            const ids = row[2].split(',').map((x) => x.trim().replace(/'/g, ''));
            assert.ok(ids.length >= 2 && ids.length <= 3 && ids.every((id) => catalogue.has(id)), `${menu}: ${ids}`);
            return ids;
        };
        // the neon corner: a tower's lobby, by the rules every lobby keeps
        const lobby = cfg.rooms.LobbySapporo3;
        assert.deepStrictEqual(lobby.lobby, { host: 'Sapporo', door: [35, 46], doors: [[35, 46]] });
        assert.ok(lobby.interior === true && lobby.shopEnabled === false);
        // the karaoke bar: the shop floor, its counter a bar
        const bar = cfg.rooms.ShopSapporo4;
        assert.strictEqual(bar.name, 'Karaoke bar · Sapporo');
        assert.deepStrictEqual(bar.shop, { host: 'Sapporo', door: [40, 46], type: 'bar' });
        assert.ok(bar.interior === true && bar.shopEnabled === false && bar.shopMenu === 'bar');
        assert.deepStrictEqual({ ...I.match('office-counter2_0_0', bar, { bar: {} }) }, { kind: 'bar', group: 'shop', footprint: true });
        assert.ok(list('bar').includes('highball') && list('bar').includes('nama-beer'));
        for (const [key, r, x, y] of [['LobbySapporo3', lobby, 35, 46], ['ShopSapporo4', bar, 40, 46]]) {
            const d = doorAt(x, y);
            assert.ok(d && d.targetRoom === key && d.hidden && !solid(x, y), `${key}: its door at ${x},${y}`);
            assert.deepStrictEqual(r.transporters.map((t) => [t.targetRoom, t.targetX, t.targetY]), [['Sapporo', x, y + 1]], key);
            assert.deepStrictEqual([d.targetX, d.targetY], [r.transporters[0].gridX, r.transporters[0].gridY - 1], key);
            assert.ok(reach.has(`${x},${y + 1}`) && fam(x, y + 1) === 'susukino-asphalt-autotile', `${key}: the cell in front of its door`);
        }
        // the ramen counters: no door - a bump anywhere on one opens its list, as the hot-drinks tent does, and
        // every one has the alley in front of it
        for (const v of 'ab') assert.deepStrictEqual({ ...I.match(`susukino-ramen-stall-${v}_0_0`, room, {}) }, { kind: 'ramen', group: 'shop', footprint: true });
        assert.ok(list('ramen').some((id) => new RegExp(`\\{ id: '${id}',[^\\n]*category: 'food'`).test(src)), 'something to eat');
        for (const [x, y] of [...at('susukino-ramen-stall-a_0_0'), ...at('susukino-ramen-stall-b_0_0')]) {
            for (let dx = 0; dx < 3; dx++) assert.ok(solid(x + dx, y + 2) && reach.has(`${x + dx},${y + 3}`), `${x + dx},${y + 3}`);
        }
        // neither is a store: no stamp for buying there (Stamps.placeFor gives one in a store or at a machine)
        const energy = fs.readFileSync(path.join(GV2, 'src', 'Energy.js'), 'utf8');
        assert.ok(energy.includes("return kind === 'vending' && room ? 'vending:' + room : null;"));
        // the only doors of the town: the station's pair, the konbini, the store, three lobbies, four shops, and
        // the underground arcade's four stairs, two cells each
        assert.strictEqual(room.transporters.filter((t) => t.targetRoom !== 'ChikagaiSapporo').length, 11);
        assert.strictEqual(room.transporters.length, 19);
    });

    test('Susukino: the streetcar is declared on its rails, with a stop outside the ramen alley (#219)', () => {
        assert.deepStrictEqual(room.tramways, [{ row: 48, sprite: 'sapporo-streetcar_0_0', speed: 160, headway: 20, stops: [23], dwell: 5 }]);
        const T = vmWith('AmbientTrams.js', 'AmbientTrams');
        const layers = room.layers.map((l) => ({ tiles: Object.fromEntries(Object.entries(l.tiles).map(([xy, t]) => [xy, name(t)])) }));
        const line = JSON.parse(JSON.stringify(T.line(room.tramways[0], layers, null, W)));
        // the line is the row's rails: edge to edge, so the car comes in from off the map and leaves the same way
        assert.deepStrictEqual([line.row, line.from, line.to, line.open, line.stops], [48, 0, 55, [true, true], [{ x: 23, dwell: 5 }]]);
        const GS = 64, width = 320;
        for (const dir of [1, -1]) {
            const plan = T.plan(line, { GS, width, worldWidth: W * GS, dir });
            assert.deepStrictEqual([plan.fromX, plan.toX], dir > 0 ? [-width, W * GS] : [W * GS, -width]);
            const dwell = plan.legs.filter((l) => l.x0 === l.x1);
            assert.deepStrictEqual(JSON.parse(JSON.stringify(dwell.map((l) => [l.x0, l.t1 - l.t0]))), [[(23 + 0.5) * GS - width / 2, 5000]], 'it stands at the stop, centred on it');
            assert.strictEqual(T.at(plan, 0).alpha, 1);
            assert.ok(plan.duration > 25000 && plan.duration < 45000, `a trip takes ${plan.duration} ms`);
        }
        // its depth: over whatever stands on the building line (row 46) and anybody on the north side of the
        // street, under somebody standing on the rails and the poles on the south kerb
        const feet = (row) => (row + 1) * 10 + 5;
        assert.ok(T.depthAt(48) > feet(46) && T.depthAt(48) > feet(47) && T.depthAt(48) < feet(48) && T.depthAt(48) < feet(50) - 5);
        // the stop: a strip of platform south of the rails beside the stop cell, a bench and the sign on the kerb
        for (let x = 20; x <= 26; x++) assert.ok(fam(x, 49) === 'light-concrete-autotile' && reach.has(`${x},49`), `${x},49`);
        assert.deepStrictEqual(at('odori-bench_0_0').filter(([, y]) => y >= 43), [[21, 50]]);
        assert.deepStrictEqual(at('bus-stop_0_0'), [[25, 50]]);
        // overhead-wire poles on the south kerb: the mast's foot collides there, its arm is over the rails
        assert.deepStrictEqual(at('tram-pole_0_0').sort((a, b) => a[0] - b[0]), [[6, 48], [18, 48], [34, 48], [48, 48]]);
        for (const [x] of at('tram-pole_0_0')) assert.ok(solid(x, 50) && !solid(x, 48) && !solid(x, 49), `the pole at ${x}`);
        // the car is art, not a tile: nothing of it is placed, so nothing of it collides
        for (const l of room.layers) for (const t of Object.values(l.tiles)) assert.notStrictEqual(name(t), 'sapporo-streetcar_0_0');
        // a rail tile is the track to the blog pipeline: nobody is stood on it
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        assert.ok(/NOT_PLAIN = \('road', 'toyama-tram-rail', 'tram-rail', 'train-track', 'crossing-'\)/.test(py));
        assert.ok(py.includes("key.startswith(('train-track', 'tram-rail'))"));
    });

    test('Susukino: its landmarks, its district and what glows there at night (#219)', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        const spots = { 'Susukino crossing': ['susukino-neon-corner_', 36, 47], 'ramen alley': ['susukino-ramen-gate_', 25, 47],
            'the streetcar stop': ['bus-stop_', 24, 49] };
        for (const [label, [prefix, sx, sy]] of Object.entries(spots)) {
            const m = new RegExp(`\\('${prefix}', '${label}', \\((-?\\d+), (-?\\d+)\\), \\{'rooms': \\('Sapporo',\\)\\}\\)`).exec(py);
            assert.ok(m, label);
            const [[ox, oy]] = at(prefix + '0_0');
            assert.deepStrictEqual([ox + Number(m[1]), oy + Number(m[2])], [sx, sy], label);
            // a stand cell is on Susukino's ground or the platform, never the rails, a door or the cell in front of one
            assert.ok(reach.has(`${sx},${sy}`) && /^(susukino-asphalt|light-concrete)-autotile$/.test(fam(sx, sy)), label);
            assert.ok(!doorAt(sx, sy) && !doorAt(sx, sy - 1) && !(sx === 28 && sy === 47), `${label} stands at a door or in the gate's mouth`);
        }
        // Asahikawa's ramen alley is its own row too, on its own gate (stage B): the generic ramen-banner row is gone
        assert.ok(py.includes("('asahikawa-ramen-gate_', 'ramen alley', (3, 3), {'rooms': ('Asahikawa',)}),") && !py.includes("('ramen-banner_'"));
        assert.deepStrictEqual(at('ramen-banner_0_0'), []);
        assert.ok(cfg.districts.Asahikawa.find((x) => x.key === 'ramen-alley').spots.includes('ramen alley'));
        const d = cfg.districts.Sapporo.find((x) => x.key === 'susukino');
        assert.deepStrictEqual([d.name, d.bounds, d.stand], ['Susukino', [2, 43, 53, 49], [37, 47]]);
        assert.deepStrictEqual(d.spots, ['Susukino crossing', 'ramen alley', 'the streetcar stop']);
        assert.ok(/neon/.test(d.description) && /karaoke/.test(d.description) && /ramen alley/.test(d.description) && /streetcar/.test(d.description));
        assert.ok(reach.has(d.stand.join(',')) && fam(...d.stand) === 'susukino-asphalt-autotile' && !doorAt(d.stand[0], d.stand[1] - 1));
        assert.deepStrictEqual(cfg.districts.Sapporo.map((x) => x.key), ['station-front', 'clock-tower', 'odori-park', 'tanukikoji', 'susukino']);
        // the arcade's district is what it was
        assert.deepStrictEqual(cfg.districts.Sapporo.find((x) => x.key === 'tanukikoji').spots, ['Tanukikoji arcade', 'the 7-Eleven', 'the crab shop', 'the souvenir shop']);
        // the glow table lights the neon corner, the karaoke bar, the gate and the counters; the poles are the lamp rule's
        const glows = fs.readFileSync(path.join(GV2, 'src', 'utils', 'Glows.js'), 'utf8');
        for (const key of ['susukino-neon-corner_0_0', 'susukino-karaoke_0_0', 'susukino-ramen-gate_0_0', 'susukino-ramen-stall-a_0_0', 'susukino-ramen-stall-b_0_0']) {
            assert.ok(glows.includes(`'${key}': [`), key);
        }
    });
};
