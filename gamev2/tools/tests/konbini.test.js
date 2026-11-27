// 7-Eleven interiors (issues #23, #221): tools/generate_konbinis.py, the konbini-* kit of
// tools/generate_konbini_art.py, and the kit's rules in src/utils/Interactions.js.
module.exports = ({ test, assert, fs, path, GV2, game, load, require }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const stores = Object.entries(cfg.rooms).filter(([k]) => k.startsWith('Konbini'));
    const sprite = (key) => path.join(GV2, 'assets', 'sprites', key + '.png');
    const sizeOf = (key) => {
        const b = fs.readFileSync(sprite(key));
        return [Math.max(1, Math.round(b.readUInt32BE(16) / 64)), Math.max(1, Math.round(b.readUInt32BE(20) / 64))];
    };
    const interactions = () => {
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');   // once: other tests load it too
        return game('Interactions');
    };
    // the floor: the outline's box under the back wall (its top two rows) and above the mat row, and the two mat cells
    const floorOf = (room) => {
        const xs = room.boundary.map((p) => p[0]), top = Math.min(...room.boundary.map((p) => p[1])) + 2;
        const mat = room.transporters.map((t) => `${t.gridX},${t.gridY}`), row = room.transporters[0].gridY;
        return { x0: Math.min(...xs), x1: Math.max(...xs), top, row,
            has: (x, y) => mat.includes(`${x},${y}`) || (x >= Math.min(...xs) && x < Math.max(...xs) && y >= top && y < row) };
    };
    // the cells a walk from the mat gets to
    const walked = (room) => {
        const solid = tiles(room, 'Colliders'), floor = floorOf(room);
        const todo = room.transporters.map((t) => [t.gridX, t.gridY]), seen = new Set(todo.map((c) => c.join(',')));
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                const c = `${nx},${ny}`;
                if (seen.has(c) || c in solid || !floor.has(nx, ny)) continue;
                seen.add(c); todo.push([nx, ny]);
            }
        }
        return seen;
    };
    const placed = (room) => room.layers.flatMap((l) => Object.values(l.tiles).map(name));
    // the kit: what each sprite covers in cells, and what a bump on it is (nothing: not in KINDS)
    const CELLS = { 'konbini-mat': [2, 1], 'konbini-wall': [1, 2], 'konbini-wall-clock': [1, 2], 'konbini-wall-tobacco': [2, 2],
        'konbini-counter-w': [2, 3], 'konbini-counter-e': [2, 3], 'konbini-chiller-a': [1, 2], 'konbini-chiller-b': [1, 2],
        'konbini-coffee': [1, 2], 'konbini-water': [1, 2], 'konbini-atm': [1, 2], 'konbini-copier': [1, 2],
        'konbini-gondola-snacks': [2, 2], 'konbini-gondola-noodles': [2, 2], 'konbini-gondola-bread': [2, 2], 'konbini-gondola-daily': [2, 2],
        'konbini-freezer': [2, 1], 'konbini-magazines': [2, 1] };
    const KINDS = { 'konbini-counter-w': 'counter', 'konbini-counter-e': 'counter', 'konbini-chiller-a': 'snacks', 'konbini-chiller-b': 'snacks',
        'konbini-coffee': 'drinks', 'konbini-water': 'water', 'konbini-wall-clock': 'clock', 'konbini-atm': 'atm', 'konbini-copier': 'copier',
        'konbini-gondola-snacks': 'snacks', 'konbini-gondola-noodles': 'snacks', 'konbini-gondola-bread': 'snacks',
        'konbini-gondola-daily': 'sundries', 'konbini-freezer': 'ice-cream', 'konbini-magazines': 'magazines' };
    const kit = Object.keys(cfg.spriteMetadata).filter((k) => k.startsWith('konbini-')).sort();

    test('every 7-Eleven is a 20x15 interior: its mat leads out to the cell below its door, its door in to the cell above the mat (#221)', () => {
        assert.strictEqual(stores.length, 13, stores.map(([k]) => k).join());
        for (const [key, room] of stores) {
            assert.deepStrictEqual([room.worldWidth, room.worldHeight], [20 * 64, 15 * 64], key);
            assert.strictEqual(room.interior, true, key);
            assert.ok(!('shopEnabled' in room), `${key}: a konbini's shelves sell`);
            assert.ok(/^7-Eleven · /.test(room.name), `${key}: ${room.name}`);
            const doors = Object.entries(cfg.rooms).flatMap(([host, r]) => (r.transporters || [])
                .filter((t) => t.targetRoom === key).map((t) => [host, t]));
            assert.strictEqual(doors.length, 1, `${key}: one door on the street`);
            const [host, door] = doors[0];
            assert.strictEqual(room.transporters.length, 2, key);
            const [left, right] = [...room.transporters].sort((a, b) => a.gridX - b.gridX);
            assert.deepStrictEqual([right.gridX, right.gridY], [left.gridX + 1, left.gridY], `${key}: the mat is two cells side by side`);
            for (const t of [left, right]) {
                assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], [host, door.gridX, door.gridY + 1], `${key}: the way out`);
                assert.ok(t.hidden, key);
            }
            assert.deepStrictEqual([door.targetX, door.targetY], [left.gridX, left.gridY - 1], `${key}: you arrive just inside the mat`);
            // the mat is under the middle of the floor, and the art for it lies on its two cells
            const floor = floorOf(room);
            assert.strictEqual(left.gridX - floor.x0, floor.x1 - right.gridX - 1, `${key}: the doors are in the middle of the front`);
            assert.strictEqual(name(tiles(room, 'Over Floor')[`${left.gridX},${left.gridY}`]), 'konbini-mat_0_0', key);
            // the outline takes in the two rows of back wall over the floor, so a landscape phone (a view 7.5
            // rows tall) follows the player up to the wall: held to the floor alone, the wall and the top half
            // of every cooler against it would be off the top of the screen
            const ys = room.boundary.map((p) => p[1]);
            assert.deepStrictEqual([Math.min(...ys), Math.max(...ys)], [floor.top - 2, left.gridY + 1], key);
            for (let x = floor.x0; x < floor.x1; x++) {
                assert.ok(/^konbini-wall/.test(name(tiles(room, 'Collidables')[`${x},${floor.top - 2}`]) || name(tiles(room, 'Collidables')[`${x - 1},${floor.top - 2}`])), `${key}: no wall over column ${x}`);
            }
            assert.strictEqual(game('RoomManager.heldRows')({ y0: Math.min(...ys) * 64, y1: Math.max(...ys) * 64 }, 480, 20), null, key);
        }
    });

    test('every 7-Eleven has a till, coolers, chillers, water, a clock and something that only says a line, each bumped from floor the door leads to (#221)', () => {
        const all = interactions().all;
        for (const [key, room] of stores) {
            const layers = room.layers.map((l) => ({ name: l.name, collision: l.collision,
                tiles: Object.fromEntries(Object.entries(l.tiles).map(([xy, t]) => [xy, name(t)])) }));
            const solid = tiles(room, 'Colliders'), seen = walked(room), floor = floorOf(room);
            // every free cell of the floor is walked to: no aisle is sealed
            for (let y = floor.top; y < floor.row; y++) {
                for (let x = floor.x0; x < floor.x1; x++) {
                    assert.ok(`${x},${y}` in solid || seen.has(`${x},${y}`), `${key}: nobody can reach ${x},${y}`);
                }
            }
            const count = {};
            for (const f of all({ layers }, room, { sizeOf })) {
                // a bump is a step into a solid cell of the piece from a cell beside it
                let bumped = false;
                for (let y = f.y; y < f.y + f.h; y++) {
                    for (let x = f.x; x < f.x + f.w; x++) {
                        if (!(`${x},${y}` in solid)) continue;
                        if ([[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]].some((c) => seen.has(c.join(',')))) bumped = true;
                    }
                }
                assert.ok(bumped, `${key}: ${f.key} at ${f.x},${f.y} cannot be bumped`);
                const kind = f.group === 'flavour' ? 'flavour' : f.kind;
                if (f.group === 'flavour') assert.ok(f.say, `${key}: ${f.key} says nothing`);
                count[kind] = (count[kind] || 0) + 1;
            }
            assert.strictEqual(count.counter, 1, `${key}: ${JSON.stringify(count)}`);
            assert.strictEqual(count.water, 1, `${key}: ${JSON.stringify(count)}`);
            assert.strictEqual(count.clock, 1, `${key}: ${JSON.stringify(count)}`);
            assert.ok(count.drinks >= 3 && count.snacks >= 2 && count.flavour >= 1, `${key}: ${JSON.stringify(count)}`);
        }
    });

    test('a 7-Eleven is built from its own kit: the only office art left in one is the drinks cooler and the void around it (#221)', () => {
        for (const [key, room] of stores) {
            const keys = new Set(placed(room));
            for (const k of keys) {
                assert.ok(/^konbini-/.test(k) || k === 'office-fridge_0_0' || /^office-void-autotile/.test(k) || k === 'gk_blank',
                    `${key} places ${k}`);
            }
            for (const k of ['konbini-wall-tobacco_0_0', 'konbini-wall-clock_0_0', 'konbini-water_0_0', 'konbini-atm_0_0', 'konbini-magazines_0_0',
                'konbini-baskets_0_0', 'konbini-mat_0_0', 'office-fridge_0_0']) assert.ok(keys.has(k), `${key} has no ${k}`);
            // the wall is two rows above the floor, the clerk's counter in a back corner under the tobacco rack
            const floor = floorOf(room), on = tiles(room, 'Collidables');
            const at = (k) => Object.keys(on).filter((xy) => name(on[xy]).startsWith(k)).map((xy) => xy.split(',').map(Number));
            const [counter] = at('konbini-counter'), [rack] = at('konbini-wall-tobacco');
            assert.deepStrictEqual([counter[1], rack[1]], [floor.top, floor.top - 2], key);
            assert.ok(counter[0] === rack[0] && (counter[0] === floor.x0 || counter[0] === floor.x1 - 2), `${key}: the counter is at ${counter}`);
            const west = counter[0] === floor.x0;
            assert.strictEqual(name(on[counter.join(',')]), west ? 'konbini-counter-w_0_0' : 'konbini-counter-e_0_0', `${key}: the nook opens the wrong way`);
            for (let x = floor.x0; x < floor.x1; x++) {
                const wall = [floor.top - 2, floor.top - 1].every((y) => `${x},${y}` in tiles(room, 'Colliders'));
                assert.ok(wall, `${key}: no back wall over column ${x}`);
            }
        }
    });

    test('the 7-Elevens are not one plan: more than one layout, both mirrors, and Asakusa\'s six differ among themselves (#221)', () => {
        // a store's plan is its solid cells; turned so its counter is in the west corner, it is its layout
        const plan = (room) => Object.keys(tiles(room, 'Colliders')).sort().join(' ');
        const east = (room) => placed(room).includes('konbini-counter-e_0_0');
        const width = cfg.rooms.KonbiniMarket1.worldWidth / 64;
        const layout = (room) => (east(room)
            ? Object.keys(tiles(room, 'Colliders')).map((xy) => { const [x, y] = xy.split(',').map(Number); return `${width - 1 - x},${y}`; }).sort().join(' ')
            : plan(room));
        assert.ok(new Set(stores.map(([, r]) => layout(r))).size >= 2, 'every store has the same layout');
        assert.deepStrictEqual([...new Set(stores.map(([, r]) => east(r)))].sort(), [false, true], 'the counter is always in the same corner');
        const asakusa = stores.filter(([k]) => k.startsWith('KonbiniMarket'));
        assert.strictEqual(asakusa.length, 6);
        assert.ok(new Set(asakusa.map(([, r]) => plan(r))).size >= 2, 'Asakusa\'s six stores are one plan');
        // and the generator that deals them is held to its committed output, with the kit's art tool
        const checks = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/'generate_konbinis'/.test(checks) && /'generate_konbini_art'/.test(checks));
    });

    test('the konbini kit: every sprite is whole cells anchored on its first, the floor is opaque, the east counter is the west one mirrored (#221)', () => {
        const png = require('./png');
        assert.strictEqual(kit.length, 26, kit.join());
        for (const key of kit) {
            const { width, height, data } = png.decode(fs.readFileSync(sprite(key)));
            const [w, h] = CELLS[key.replace(/_0_0$/, '')] || [1, 1];
            assert.deepStrictEqual([width, height], [w * 64, h * 64], key);
            const meta = cfg.spriteMetadata[key];
            assert.deepStrictEqual([meta.frameCount, meta.anchorX, meta.anchorY], [1, 32 / width, 32 / height], key);
            assert.ok((cfg.tileNames || {})[key], `${key} has no name in the editors`);
            assert.ok(cfg.tilePalette.includes(key), `${key} is drawn but no store places it`);
            if (/^konbini-floor-/.test(key)) {
                for (let p = 3; p < data.length; p += 4) assert.strictEqual(data[p], 255, `${key}: a see-through floor`);
            }
        }
        const west = png.decode(fs.readFileSync(sprite('konbini-counter-w_0_0')));
        const east = png.decode(fs.readFileSync(sprite('konbini-counter-e_0_0')));
        let differ = 0, same = 0;
        for (let y = 0; y < west.height; y++) {
            for (let x = 0; x < west.width; x++) {
                const a = (y * west.width + x) * 4, b = (y * west.width + west.width - 1 - x) * 4;
                if (west.data.readUInt32BE(a) !== east.data.readUInt32BE(b)) differ++;
                if (west.data.readUInt32BE(a) === east.data.readUInt32BE(a)) same++;
            }
        }
        assert.strictEqual(differ, 0, 'konbini-counter-e is not konbini-counter-w mirrored');
        assert.ok(same < west.width * west.height, 'the two counters are one picture');
    });

    test('a bump on the konbini kit: the counter, chillers, shelf blocks and coffee sell, the water pours, the wall clock travels, the rest say a line or nothing (#221)', () => {
        const match = interactions().match;
        const lines = new Set();
        for (const key of kit) {
            const hit = match(key, { interior: true }), want = KINDS[key.replace(/_0_0$/, '')];
            assert.strictEqual(hit ? hit.kind : undefined, want, key);
            if (!hit) continue;
            assert.ok(hit.footprint, `${key}: bumped on every cell it covers`);
            if (hit.group === 'flavour') { assert.ok(hit.say && !lines.has(hit.say), key); lines.add(hit.say); }
        }
        assert.strictEqual(lines.size, 5);
        for (const key of ['konbini-counter-e_0_0', 'konbini-chiller-b_0_0', 'konbini-gondola-noodles_0_0', 'konbini-coffee_0_0']) {
            assert.strictEqual(match(key, { interior: true }).group, 'shop', key);
        }
        assert.strictEqual(match('konbini-water_0_0', { interior: true }).group, 'water');
        assert.strictEqual(match('konbini-wall-clock_0_0', { interior: true }).group, 'clock');
        // the drinks cooler is still the one the konbini had
        assert.strictEqual(match('office-fridge_0_0', { interior: true }).kind, 'drinks');
        // nothing sells in a room that is not a shop, or out of doors
        for (const room of [{ interior: true, shopEnabled: false }, {}]) {
            for (const key of ['konbini-chiller-a_0_0', 'konbini-counter-w_0_0', 'konbini-coffee_0_0', 'konbini-gondola-bread_0_0', 'konbini-water_0_0']) {
                assert.strictEqual(match(key, room), null, `${key} in ${JSON.stringify(room)}`);
            }
        }
    });
};
