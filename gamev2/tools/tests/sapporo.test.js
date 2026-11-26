// Sapporo's rebuild (issue #219). Stage 1 is the north of the town: the Sapporo Station front and the
// Clock Tower block. All of it is data the generators write (tools/generate_sapporo.py,
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
        // spread over both districts and the park, as before the rebuild (nobody had to move)
        const where = Object.fromEntries(cast.map((n) => [n.name, [n.gridX, n.gridY]]));
        assert.deepStrictEqual(where, { Khoi: [38, 8], Sam: [21, 27], Xander: [35, 17], Bailey: [30, 11], Damian: [36, 12], Dylan: [24, 15], Julia: [39, 19] });
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
};
