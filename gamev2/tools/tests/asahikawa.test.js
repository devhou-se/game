// Asahikawa rebuilt from its own art (issue #219, stage B): the glass station front on the old door cell,
// Heiwa-dori and its shops, ramen alley two cells wide behind its gate, Asahibashi's flat deck over the
// frozen river, three Hokkaido houses and the Asahiyama Zoo gate. All of it is data the generators write
// (tools/generate_asahikawa.py, generate_asahikawa_art.py, art_register.py, make_prefabs.py,
// generate_konbinis.py, generate_houses.py and its --shops).
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const room = cfg.rooms.Asahikawa;
    const layer = (n, r = room) => ((r.layers.find((l) => l.name === n) || {}).tiles) || {};
    const W = room.worldWidth / 64, H = room.worldHeight / 64;
    const solid = (x, y) => `${x},${y}` in layer('Colliders');
    const fam = (x, y) => name(layer('Floor')[`${x},${y}`]).replace(/_[a-z-]+$/, '');
    const on = (l, key) => Object.entries(layer(l)).filter(([, t]) => name(t) === key).map(([xy]) => xy.split(',').map(Number));
    const at = (key) => on('Collidables', key);
    const doorAt = (x, y) => room.transporters.find((t) => t.gridX === x && t.gridY === y);
    // cells that can be walked to from where the station puts you, with `blocked` ('x,y' keys) stood on
    const walk = (blocked = new Set()) => {
        const start = cfg.rooms.AsahikawaStation.transporters[0];
        const seen = new Set([`${start.targetX},${start.targetY}`]), todo = [[start.targetX, start.targetY]];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const nx = x + dx, ny = y + dy, k = `${nx},${ny}`;
                if (nx < 0 || ny < 0 || nx >= W || ny >= H || seen.has(k) || solid(nx, ny) || blocked.has(k)) continue;
                seen.add(k); todo.push([nx, ny]);
            }
        }
        return seen;
    };
    const reach = walk();

    test('Asahikawa: the glass station front stands on the old door cell, and its pair of doors pairs both ways (#219)', () => {
        assert.deepStrictEqual([W, H], [42, 32]);
        assert.deepStrictEqual(at('asahikawa-station-front_0_0'), [[28, 5]]);
        assert.deepStrictEqual(at('building-entrance-1_0_0').concat(at('building-entrance-2_0_0'), at('building-entrance-3_0_0')), [], 'the station house is gone');
        const st = cfg.stations.AsahikawaStation;
        for (const x of [32, 33]) {
            const d = doorAt(x, 9);
            assert.ok(d && d.hidden && !solid(x, 9), `the door at ${x},9`);
            assert.deepStrictEqual([d.targetRoom, d.targetX, d.targetY], ['AsahikawaStation', ...st.entry]);
            assert.ok(reach.has(`${x},10`) && fam(x, 10) === 'heiwa-paving-autotile', `the paving in front of ${x},9`);
        }
        // out again: the station's mats land in front of the west door, where they always did
        for (const t of cfg.rooms.AsahikawaStation.transporters) assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Asahikawa', 32, 10]);
        // the rest of the hall is sealed, feet and glass alike
        for (let x = 28; x <= 37; x++) {
            for (let y = 7; y <= 9; y++) assert.ok(solid(x, y) || (y === 9 && (x === 32 || x === 33)), `${x},${y}`);
        }
        // a stay that starts here stands on the paving south of the doors
        assert.ok(reach.has('31,12') && fam(31, 12) === 'heiwa-paving-autotile');
        // the platform strip went with the station house: the rail corridor is fenced off from the street
        for (let x = 0; x < W; x++) assert.ok(!reach.has(`${x},4`) && !reach.has(`${x},5`), `the track side at ${x}`);
    });

    test('Asahikawa: Heiwa-dori is one row of fronts on its own setts - a 7-Eleven and three shops you can enter, a bookshop you cannot (#219)', () => {
        for (let x = 11; x <= 38; x++) for (let y = 10; y <= 12; y++) assert.strictEqual(fam(x, y), 'heiwa-paving-autotile', `${x},${y}`);
        for (let x = 19; x <= 22; x++) for (let y = 13; y <= 15; y++) assert.strictEqual(fam(x, y), 'heiwa-paving-autotile', `the leg at ${x},${y}`);
        const fronts = [['seven-eleven_0_0', 12, 6], ['heiwa-shop-books_0_0', 15, 7], ['heiwa-shop-sake_0_0', 18, 6],
            ['heiwa-shop-bakery_0_0', 21, 6], ['heiwa-shop-woodcraft_0_0', 24, 7]];
        for (const [key, x, y] of fronts) assert.deepStrictEqual(at(key), [[x, y]], key);
        const ctx = require('vm').createContext({ window: {} });
        require('vm').runInContext(fs.readFileSync(path.join(GV2, 'src', 'utils', 'Interactions.js'), 'utf8') + '\nthis.Interactions = Interactions;', ctx);
        const src = fs.readFileSync(path.join(GV2, 'src', 'Shop.js'), 'utf8');
        const shops = { ShopAsahikawa1: [19, 9, 'Sake bar · Asahikawa', 'standbar'], ShopAsahikawa2: [22, 9, 'Bakery · Asahikawa', 'bakery'],
            ShopAsahikawa3: [27, 9, 'Woodcraft · Asahikawa', 'souvenirs'], ShopAsahikawa4: [5, 13, 'Ramen · Asahikawa', 'ramen'] };
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^ShopAsahikawa/.test(k)).sort(), Object.keys(shops));
        for (const [key, [x, y, title, menu]] of Object.entries(shops)) {
            const r = cfg.rooms[key], d = doorAt(x, y);
            assert.ok(d && d.targetRoom === key && !solid(x, y), `${key}: its door at ${x},${y}`);
            assert.deepStrictEqual(r.transporters.map((t) => [t.targetRoom, t.targetX, t.targetY]), [['Asahikawa', x, y + 1]], key);
            assert.deepStrictEqual([d.targetX, d.targetY], [r.transporters[0].gridX, r.transporters[0].gridY - 1], key);
            assert.ok(reach.has(`${x},${y + 1}`) && !at('heiwa-lamp-post_0_0').some(([lx, ly]) => lx === x && ly + 1 === y + 1), `${key}: the cell in front of its door`);
            assert.strictEqual(r.name, title);
            assert.ok(r.interior === true && r.shopEnabled === false && r.shopMenu === menu, key);
            assert.deepStrictEqual(r.shop, { host: 'Asahikawa', door: [x, y], type: menu });
            assert.ok(new RegExp(`${menu}:\\s*\\{ title: '[A-Z ]+'`).test(src), `Shop.VENUES.${menu}`);
            const hit = ctx.Interactions.match('office-counter2_0_0', r, { [menu]: {} });
            assert.deepStrictEqual({ ...hit }, { kind: menu, group: 'shop', footprint: true }, `${key}: a bump on the counter opens its list`);
        }
        // the 7-Eleven: its door pairs both ways, and it is the town's one store
        const k = cfg.rooms.KonbiniAsahikawa1, kd = doorAt(13, 9);
        assert.ok(kd && kd.targetRoom === 'KonbiniAsahikawa1' && !solid(13, 9) && reach.has('13,10'));
        assert.strictEqual(k.name, '7-Eleven · Asahikawa');
        for (const t of k.transporters) assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Asahikawa', 13, 10]);
        assert.ok(/ALL_HOSTS \+= \['Asahikawa'\]/.test(fs.readFileSync(path.join(GV2, 'tools', 'generate_konbinis.py'), 'utf8')));
        // the bookshop has no door: its whole foot is sealed
        for (let x = 15; x <= 17; x++) assert.ok(solid(x, 9) && !doorAt(x, 9), `the bookshop at ${x},9`);
        // on the setts: two ice sculptures, benches and the street's own lamps, and nothing on a door front
        assert.deepStrictEqual(at('ice-sculpture-crane_0_0'), [[15, 10]]);
        assert.deepStrictEqual(at('ice-sculpture-owl_0_0'), [[25, 10]]);
        assert.strictEqual(at('heiwa-bench_0_0').length, 2);
        assert.strictEqual(at('heiwa-lamp-post_0_0').length, 3);
        for (const x of [13, 19, 22, 27, 32, 33]) assert.ok(reach.has(`${x},10`), `the door front ${x},10`);
        // the yard behind the ramen shops is closed: nobody walks in behind the fronts
        for (let x = 2; x <= 10; x++) for (let y = 7; y <= 9; y++) assert.ok(!reach.has(`${x},${y}`), `the yard at ${x},${y}`);
    });

    test('Asahikawa: ramen alley is two cells wide behind its gate, and anyone can be stood on any cell of its south row (#219)', () => {
        for (const [key, x] of [['ramen-shoyu-front_0_0', 2], ['ramen-narrow-front_0_0', 6], ['ramen-miso-front_0_0', 8]]) assert.deepStrictEqual(at(key), [[x, 10]], key);
        assert.deepStrictEqual(at('asahikawa-ramen-gate_0_0'), [[11, 11]]);
        for (const key of ['machiya-black_0_0', 'machiya-red_0_0', 'machiya-blue_0_0', 'ramen-banner_0_0']) assert.deepStrictEqual(at(key), [], key);
        // through the gate off Heiwa-dori: its posts collide, its middle cell is the way
        assert.ok(solid(11, 13) && solid(13, 13) && reach.has('12,13') && reach.has('12,12') && reach.has('12,14'));
        // ... and round its open east end: the gate is not the only way in
        assert.ok(walk(new Set(['12,13'])).has('8,15'), 'the alley with the gate stood in');
        for (let x = 2; x <= 16; x++) {
            for (const y of [14, 15]) assert.strictEqual(fam(x, y), 'ramen-alley-autotile', `${x},${y}`);
            // the pipeline's rule (blog_to_npc.walls_in): with someone on the cell, everything else is still walked to
            assert.ok(reach.has(`${x},15`), `${x},15`);
            assert.strictEqual(walk(new Set([`${x},15`])).size, reach.size - 1, `someone on ${x},15 is in the way`);
        }
        // what keeps it so: they are walked round along row 14 or along the bank, so no prop's foot on
        // row 14 stands within two columns of a bank shrub of row 16
        const shrubs = at('shrub-small-circle-snow_0_0').filter(([, y]) => y === 16).map(([x]) => x);
        assert.deepStrictEqual(shrubs.filter((x) => x <= 16).sort((a, b) => a - b), [13, 16]);
        for (const x of shrubs.filter((s) => s <= 16)) for (let dx = -2; dx <= 2; dx++) assert.ok(!solid(x + dx, 14), `a prop's foot at ${x + dx},14 by the shrub at ${x}`);
        // the shoyu counter's door front is clear; the other two fronts are sealed
        assert.ok(reach.has('5,14') && solid(7, 13) && solid(9, 13) && !doorAt(7, 13) && !doorAt(9, 13));
    });

    test('Asahikawa: Asahibashi is a flat deck you walk on, the only way over the frozen river (#219)', () => {
        assert.deepStrictEqual(on('Non-Collidables', 'asahibashi-deck_0_0'), [[20, 16]]);
        assert.deepStrictEqual(at('asahikawa-bridge_0_0'), []);
        // flat: drawn under whoever stands on it (RoomManager reads depthBias), and none of its cells collides
        assert.strictEqual(cfg.spriteMetadata['asahibashi-deck_0_0'].depthBias, -200);
        for (let y = 16; y <= 20; y++) for (const x of [20, 21]) assert.ok(reach.has(`${x},${y}`), `the deck at ${x},${y}`);
        // a rib each side, solid top to bottom, and the brace over the middle on Tops
        assert.deepStrictEqual([at('asahibashi-arch-w_0_0'), at('asahibashi-arch-e_0_0')], [[[19, 16]], [[22, 16]]]);
        for (let y = 16; y <= 20; y++) assert.ok(solid(19, y) && solid(22, y), `the ribs on row ${y}`);
        assert.deepStrictEqual(on('Tops', 'asahibashi-brace_0_0'), [[19, 18]]);
        // the river is ice bank to bank, and solid everywhere but under the deck
        for (let x = 0; x < W; x++) {
            for (const y of [17, 18, 19]) {
                assert.ok(/^ice-pond-autotile_/.test(name(layer('Water')[`${x},${y}`])), `${x},${y}`);
                assert.strictEqual(solid(x, y), x !== 20 && x !== 21, `${x},${y}`);
            }
        }
        const north = walk(new Set(['20,18', '21,18']));
        assert.ok(reach.has('23,21') && !north.has('23,21') && !north.has('20,28'), 'the south bank without the bridge');
        // on the ice: a fishing tent, holes and cracks, none of them in the way of anything
        assert.strictEqual(at('ice-fishing-tent_0_0').length, 1);
        assert.ok(on('Non-Collidables', 'ice-fishing-hole_0_0').length >= 2 && on('Non-Collidables', 'ice-crack-a_0_0').length >= 1 && on('Non-Collidables', 'ice-crack-b_0_0').length >= 1);
        // the arches' lamps are lit at night, the deck is not
        for (const key of ['asahibashi-arch-w_0_0', 'asahibashi-arch-e_0_0']) {
            const glow = cfg.spriteMetadata[key].glow;
            assert.ok(glow.length === 2 && glow.every((s) => s.y >= 0 && s.y <= 5 && s.r <= 2.5), key);
        }
        assert.ok(!cfg.spriteMetadata['asahibashi-deck_0_0'].glow);
    });

    test('Asahikawa: three Hokkaido houses you can reach on the south bank, and nothing to walk to behind the zoo gate (#219)', () => {
        const row = [...at('hokkaido-house-red_0_0'), ...at('hokkaido-house-blue_0_0')].sort((a, b) => a[0] - b[0]);
        assert.deepStrictEqual(row, [[4, 23], [9, 23], [14, 23]]);
        row.forEach(([x, y], i) => {
            const key = `HouseAsahikawa${i + 1}`, d = doorAt(x + 1, y + 3);
            assert.ok(d && d.targetRoom === key && !solid(x + 1, y + 3), key);
            assert.deepStrictEqual(cfg.rooms[key].house.door, [x + 1, y + 3]);
            assert.ok(reach.has(`${x + 1},${y + 4}`), `${key}: the cell in front of its door`);
        });
        assert.strictEqual(Object.keys(cfg.rooms).filter((k) => /^HouseAsahikawa/.test(k)).length, 3);
        // the shrine, its foxes and the torii went: no hall, no room, no map
        for (const key of ['shrine-building_0_0', 'torii-red_0_0']) assert.deepStrictEqual(at(key), [], key);
        assert.ok(!('ShrineAsahikawa1' in cfg.rooms) && !fs.existsSync(path.join(GV2, 'tiled', 'shrineasahikawa1.tmj')));
        // the zoo gate: its feet and the row behind its arch collide, so the arch is a porch one cell deep
        assert.deepStrictEqual(at('zoo-gate_0_0'), [[29, 22]]);
        assert.ok(solid(29, 25) && solid(33, 25));
        for (const x of [30, 31, 32]) assert.ok(reach.has(`${x},25`) && solid(x, 24), `the porch at ${x}`);
        // the wood behind it: not one cell of rows 20-24 east of the hedge can be walked to
        for (let x = 26; x <= 39; x++) for (let y = 20; y <= 24; y++) assert.ok(!reach.has(`${x},${y}`), `behind the gate at ${x},${y}`);
        assert.deepStrictEqual(at('zoo-ticket-booth_0_0'), [[34, 23]]);
        assert.ok(at('zoo-fence-h_0_0').length >= 4 && at('zoo-fence-end_0_0').length === 1);
        assert.ok(at('penguin-walk-a_0_0').length === 1 && at('penguin-walk-b_0_0').length === 1 && at('zoo-seal-statue_0_0').length === 1);
        // Julia's line follows the town
        const julia = room.npcs.find((n) => n.name === 'Julia');
        assert.ok(julia.dialogue.some((l) => /zoo gate/.test(l)) && !julia.dialogue.some((l) => /shrine/.test(l)));
    });

    test('Asahikawa: its landmarks and districts, each with a cell to stand on that is no door front (#219)', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        const spots = { 'Asahikawa Station': ['asahikawa-station-front_', 'Collidables', 29, 10], 'the bridge over the frozen river': ['asahibashi-deck_', 'Non-Collidables', 21, 16],
            'ramen alley': ['asahikawa-ramen-gate_', 'Collidables', 14, 14], 'the Asahiyama Zoo gate': ['zoo-gate_', 'Collidables', 31, 26] };
        const doorFront = (x, y) => !!doorAt(x, y) || !!doorAt(x, y - 1);
        for (const [label, [prefix, l, sx, sy]] of Object.entries(spots)) {
            const m = new RegExp(`\\('${prefix}', '${label}', \\((-?\\d+), (-?\\d+)\\), \\{'rooms': \\('Asahikawa',\\)\\}\\)`).exec(py);
            assert.ok(m, label);
            const [[ox, oy]] = on(l, prefix + '0_0');
            assert.deepStrictEqual([ox + Number(m[1]), oy + Number(m[2])], [sx, sy], label);
            assert.ok(reach.has(`${sx},${sy}`) && !doorFront(sx, sy), `${label} stands at ${sx},${sy}`);
        }
        assert.ok(!py.includes("'asahikawa-bridge_'") && !py.includes("('ramen-banner_'"), 'the rows of what is gone');
        const d = cfg.districts.Asahikawa;
        assert.deepStrictEqual(d.map((x) => [x.key, x.bounds, x.stand]), [['station-front', [11, 5, 39, 12], [28, 11]],
            ['ramen-alley', [2, 13, 16, 15], [8, 15]], ['riverbank', [2, 16, 39, 27], [23, 21]]]);
        for (const x of d) assert.ok(reach.has(x.stand.join(',')) && !doorFront(...x.stand), `${x.key}: its stand`);
        // they do not overlap
        for (const a of d) {
            for (const b of d) {
                if (a === b) continue;
                assert.ok(a.bounds[2] < b.bounds[0] || b.bounds[2] < a.bounds[0] || a.bounds[3] < b.bounds[1] || b.bounds[3] < a.bounds[1], `${a.key} and ${b.key}`);
            }
        }
        assert.ok(/zoo gate/i.test(d[2].description) && /houses/.test(d[2].description));
        assert.ok(d[0].spots.includes('Asahikawa Station') && d[1].spots.includes('ramen alley') && d[2].spots.includes('the Asahiyama Zoo gate'));
        // the cast's base cells: all walked to, none a door front
        for (const n of room.npcs) assert.ok(reach.has(`${n.gridX},${n.gridY}`) && !doorFront(n.gridX, n.gridY), `${n.name} at ${n.gridX},${n.gridY}`);
    });

    test('Asahikawa: its art is registered by its own art tool, which the generator check runs (#219)', () => {
        const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
        assert.ok(/ART_TOOLS \+= \['generate_asahikawa_art'\]/.test(tool('check_generators.py')));
        assert.ok(/art_register\.register\(built, glow_spots\(\), FLAT\)/.test(tool('generate_asahikawa_art.py')));
        assert.ok(/BRIDGE_ROWS = 5\b/.test(tool('generate_asahikawa_art.py')));
        // every sprite the town places is in spriteMetadata, anchored on the centre of its first cell
        const png = require(path.join(GV2, 'tools', 'png'));
        const own = /^(asahikawa-|asahibashi-|heiwa-|ramen-(shoyu|narrow|miso|crates|stockpot)|hokkaido-house-|zoo-|ice-(sculpture|fishing|crack)|penguin-walk|snow-fence)/;
        const placed = new Set(room.layers.flatMap((l) => Object.values(l.tiles).map(name)).filter((k) => own.test(k) && !/autotile/.test(k)));
        assert.ok(placed.size >= 30, `${placed.size} sprites of its own`);
        for (const key of placed) {
            const meta = cfg.spriteMetadata[key], im = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
            assert.ok(meta, key);
            assert.deepStrictEqual([meta.anchorX, meta.anchorY], [Number((32 / im.width).toFixed(4)), Number((32 / im.height).toFixed(4))], key);
            for (const s of meta.glow || []) assert.ok(s.r <= 2.5 && (s.ry || 0) <= 2.5 && s.x >= 0 && s.y >= 0 && s.x <= im.width / 64 && s.y <= im.height / 64, `${key}: a glow spot off the sprite`);
        }
        // lit at night: the station hall, the shopfronts, the ramen fronts and the gate; lamp posts are the lamp rule's
        for (const key of ['asahikawa-station-front_0_0', 'heiwa-shop-sake_0_0', 'ramen-shoyu-front_0_0', 'asahikawa-ramen-gate_0_0']) {
            assert.ok((cfg.spriteMetadata[key].glow || []).length >= 1, key);
        }
        assert.ok(!cfg.spriteMetadata['heiwa-lamp-post_0_0'].glow && !cfg.spriteMetadata['asahikawa-ramen-lanterns_0_0'].glow);
    });
};
