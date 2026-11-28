module.exports = ({ test, assert, fs, path, GV2, load, game, worldWith }) => {
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    // every transporter in the world that leads into the Izakaya: [room key, transporter]
    const doorsInto = (rooms) => Object.entries(rooms).flatMap(([key, room]) =>
        (room.transporters || []).filter((t) => t.targetRoom === 'Izakaya').map((t) => [key, t]));

    test('the Izakaya has one street door, in a Tokyo district that is staying, lit by a lantern pair (#68)', () => {
        const c = cfg(), rooms = c.rooms, name = (t) => c.tilePalette[t];
        const doors = doorsInto(rooms);
        assert.strictEqual(doors.length, 1, 'exactly one way in');
        const [host, door] = doors[0];
        const districts = c.cities.TokyoCity.rooms.map((r) => r.room);
        assert.ok(districts.includes(host), `${host} is not a district of the stitched Tokyo`);
        assert.deepStrictEqual([host, door.gridX, door.gridY, door.targetX, door.targetY, door.hidden], ['Market', 7, 37, 9, 12, true]);

        const room = rooms[host], solid = tiles(room, 'Colliders'), front = `${door.gridX},${door.gridY + 1}`;
        assert.ok(!(`${door.gridX},${door.gridY}` in solid), 'the doorway is not sealed');
        assert.ok(!(front in solid), 'the cell in front of the door is free');
        assert.ok(/^grey-brick-autotile/.test(name(tiles(room, 'Floor')[front])), 'the door opens off the pavement');
        // the door is in a house front, one cell in from either end of it
        assert.strictEqual(name(tiles(room, 'Collidables')[`${door.gridX - 1},${door.gridY}`]), 'building-entrance-3_0_0');
        // a red lantern either side of the house: head on Tops, solid foot on the door's row
        for (const x of [door.gridX - 2, door.gridX + 2]) {
            assert.strictEqual(name(tiles(room, 'Tops')[`${x},${door.gridY - 1}`]), 'red-lanterns_6_3', `lantern head at ${x}`);
            assert.strictEqual(name(tiles(room, 'Collidables')[`${x},${door.gridY}`]), 'red-lanterns_4_1', `lantern foot at ${x}`);
            assert.ok(`${x},${door.gridY}` in solid, `the lantern at ${x} is solid`);
        }
        // nobody's base or dated position is on the doorway or the cell in front of it
        const taken = room.npcs.flatMap((n) => [n, ...Object.values(n.states || {})])
            .filter((s) => s.gridX === door.gridX && (s.gridY === door.gridY || s.gridY === door.gridY + 1));
        assert.deepStrictEqual(taken, []);

        // both exit mats put the player on the pavement outside, never on the door itself
        const exits = rooms.Izakaya.transporters;
        assert.strictEqual(exits.length, 2);
        for (const t of exits) {
            assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], [host, door.gridX, door.gridY + 1]);
        }
        // the room itself is what it was: the bar sells, the table starts the game, two fixture opponents
        assert.strictEqual(rooms.Izakaya.shopMenu, 'izakaya');
        assert.deepStrictEqual(rooms.Izakaya.drinkingGame.triggerCells, [[4, 7], [5, 7]]);
        assert.deepStrictEqual(rooms.Izakaya.npcs.map((n) => [n.name, !!n.drinkingGameOpponent]), [['Damian', true], ['Bailey', true]]);
    });

    test('the Izakaya house carries its own sign: its two ad boards are pinned, every other board is random', () => {
        const c = cfg(), adFor = game('RoomManager.adFor');
        const ads = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'ads', 'manifest.json'), 'utf8')).ads;
        const door = doorsInto(c.rooms)[0][1], signage = c.rooms.Market.signage;
        // the boards on the wall above the house front (6..8,37): a wide one and a square one
        const own = signage.filter((s) => s.gridY === door.gridY - 1 && s.gridX >= door.gridX - 1 && s.gridX <= door.gridX + 1);
        assert.deepStrictEqual(own.map((s) => [s.gridX, s.gridY, s.shape, s.ad]), [[6, 36, 'wide', 'ad-wide-03'], [8, 36, 'square', 'ad-square-01']]);
        assert.strictEqual(signage.filter((s) => s.ad).length, 2, 'only the Izakaya pins an ad');
        assert.strictEqual(signage.length, 10, 'no board added or lost');
        // the pinned ad is in the pool, of the board's shape, and is the drinking sign the generator means:
        // the pool's files are numbered in SPECS order, per shape
        const specs = [...fs.readFileSync(path.join(GV2, 'tools', 'generate_ads.py'), 'utf8').matchAll(/dict\(shape='(\w+)', text='([^']+)'/g)];
        const nth = (shape, n) => specs.filter((m) => m[1] === shape)[n - 1][2];
        assert.strictEqual(nth('wide', 3), '飲み放題');
        assert.strictEqual(nth('square', 1), '酒');
        for (const spot of own) {
            const ad = ads.find((a) => a.key === spot.ad);
            assert.ok(ad && ad.shape === spot.shape && fs.existsSync(path.join(GV2, 'assets', 'ads', ad.file)), spot.ad);
            // whatever the roll, the same sign; with the pin gone, the roll decides again
            for (const roll of [0, 0.37, 0.5, 0.999]) assert.strictEqual(adFor(spot, ads, roll).key, spot.ad);
            const free = { gridX: spot.gridX, gridY: spot.gridY, shape: spot.shape };
            const seen = new Set([0, 0.2, 0.4, 0.6, 0.8, 0.999].map((roll) => adFor(free, ads, roll).key));
            assert.ok(seen.size > 3, 'an unpinned board draws from the pool');
            assert.ok([...seen].every((k) => ads.find((a) => a.key === k).shape === spot.shape));
        }
        // a pin that is not in the pool (or is another shape) falls back to a random ad of the shape; no ads, no sign
        assert.strictEqual(adFor({ shape: 'wide', ad: 'ad-square-01' }, ads, 0).key, 'ad-wide-01');
        assert.strictEqual(adFor({ shape: 'wide', ad: 'nope' }, ads, 0.999).key, 'ad-wide-14');
        assert.strictEqual(adFor({ shape: 'wide' }, [], 0.5), null);
        // the generator owns the pin
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'generate_izakaya.py'), 'utf8');
        assert.ok(tool.includes("((6, 36), 'wide', 'ad-wide-03')") && tool.includes("((8, 36), 'square', 'ad-square-01')"));
    });

    test('the Izakaya has its own generator, and no made-up town leads to it (#68)', () => {
        const c = cfg();
        assert.ok(!/Inaka|Machi|Yukimura/.test(JSON.stringify(c.rooms.Izakaya.transporters)));
        const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
        assert.ok(!fs.existsSync(path.join(GV2, 'tools', 'generate_inaka.py')), 'the town it used to be in is deleted');
        assert.ok(/'generate_izakaya'/.test(tool('check_generators.py')), 'check_generators.py does not run generate_izakaya');
    });

    test('you can walk from the Tokyo start into the Izakaya and back out onto the pavement, stitched or not', () => {
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            if (stitch) {
                // one walk, no fade: the start (Tokyo 29,38) to the cell in front of the door
                const to = rm.resolve('Market', 7, 38);
                const route = world.path(to.x, to.y);
                assert.ok(route && route.length > 0, 'no path from the Tokyo start to the Izakaya door');
                for (const dir of route) assert.ok(world.step(dir).moved, `blocked on the way (${dir})`);
                // the door is a doorway of the city room, so NPCManager.atDoorway keeps wanderers off its front cell
                const door = rm.resolve('Market', 7, 37);
                assert.ok(rm.rooms.TokyoCity.transporters.some((t) => t.gridX === door.x && t.gridY === door.y && t.targetRoom === 'Izakaya'));
            } else {
                world.enter('Market', 7, 38);
            }
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 7, 38], tag);
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, 'Izakaya', tag);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Izakaya', 9, 12], tag);
            const out = world.step('s');
            assert.ok(out.transported, `${tag}: the mat below the arrival cell is the way out`);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 7, 38], tag);
            assert.strictEqual(world.step('s').moved, true, `${tag}: boxed in outside the door`);
        }
    });

    // ---- the room rebuilt off the office kit, in its own izakaya-in-* kit (#286) -------------------------------
    const K = (x, y) => `${x},${y}`;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));
    const PIECES = { 'floor-a': [1, 1], 'floor-b': [1, 1], 'side-w': [1, 1], 'side-e': [1, 1], 'wall-front': [1, 1],
        'threshold-w': [1, 1], 'threshold-e': [1, 1], wall: [1, 2], 'wall-menu': [2, 2], 'wall-clock': [1, 2],
        backbar: [6, 2], bar: [6, 1], table: [2, 1], chochin: [1, 2], casks: [1, 2] };
    const STANDING = ['backbar', 'bar', 'table', 'chochin', 'casks'];
    const TABLES = [[4, 7], [4, 11], [12, 10]];
    // where every copy of a sprite stands in the room: [[x, y], ...]
    const placed = (c, room, key) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => c.tilePalette[id] === key).map(([cell]) => cell.split(',').map(Number));
    // a cell is inside the room's outline (its centre, by ray casting)
    const inside = (boundary, x, y) => {
        const px = x + 0.5, py = y + 0.5;
        let n = 0;
        boundary.forEach(([ax, ay], i) => {
            const [bx, by] = boundary[(i + 1) % boundary.length];
            if ((ay > py) !== (by > py) && px < ax + (py - ay) * (bx - ax) / (by - ay)) n++;
        });
        return n % 2 === 1;
    };

    test('the Izakaya is drawn with its own kit: boards, a two-row back wall, the bar on the counter\'s cells, tables, hung lanterns, lantern-lit (#286)', () => {
        const c = cfg(), room = c.rooms.Izakaya, solid = tiles(room, 'Colliders'), name = (id) => c.tilePalette[id];
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map(name));
        for (const re of [/^office-(?!void)/, /^(lantern-red|red-lanterns)/, /^(pub-in-|home-|konbini-)/, /bin/]) {
            assert.deepStrictEqual([...used].filter((k) => re.test(k)), [], `${re}`);
        }
        const floor = tiles(room, 'Floor');
        for (let x = 2; x <= 17; x++) for (let y = 3; y <= 12; y++) {
            assert.ok(/^izakaya-in-floor-[ab]_0_0$/.test(name(floor[K(x, y)])), `floor ${x},${y}`);
        }
        // the back wall: two rows, solid end to end, inside the boundary so a phone's camera keeps it on screen
        for (let x = 2; x <= 17; x++) for (const y of [1, 2]) {
            assert.ok(K(x, y) in solid && inside(room.boundary, x, y), `back wall ${x},${y}`);
        }
        // the bar on the counter's cells, its stools with a place to stand between each
        const size = (key) => { const m = c.spriteMetadata[key]; return [Math.round(0.5 / m.anchorX), Math.round(0.5 / m.anchorY)]; };
        assert.deepStrictEqual(placed(c, room, 'izakaya-in-bar_0_0'), [[11, 5]]);
        assert.deepStrictEqual(size('izakaya-in-bar_0_0'), [6, 1]);
        for (let x = 11; x <= 16; x++) assert.ok(K(x, 5) in solid, `bar ${x},5`);
        const stools = placed(c, room, 'izakaya-stool_0_0').map(([x, y]) => K(x, y));
        for (const x of [11, 13, 15]) assert.ok(stools.includes(K(x, 6)) && K(x, 6) in solid, `stool ${x},6`);
        for (const x of [12, 14, 16]) assert.ok(!(K(x, 6) in solid), `a place at the bar at ${x},6`);
        // the back bar stands on row 3 behind it; the staff aisle (row 4) is open
        assert.deepStrictEqual(placed(c, room, 'izakaya-in-backbar_0_0'), [[11, 2]]);
        for (let x = 11; x <= 16; x++) assert.ok(K(x, 3) in solid, `back bar ${x},3`);
        for (let x = 2; x <= 17; x++) assert.ok(!(K(x, 4) in solid), `row 4 at ${x}`);
        // the tables, a stool north and south of each, a lantern hung two rows over each one's east cell
        const tables = placed(c, room, 'izakaya-in-table_0_0').map(([x, y]) => K(x, y)).sort();
        assert.deepStrictEqual(tables, TABLES.map(([x, y]) => K(x, y)).sort());
        const tops = tiles(room, 'Tops'), lanterns = placed(c, room, 'izakaya-in-chochin_0_0');
        assert.strictEqual(lanterns.length, 6);
        assert.ok(lanterns.every(([x, y]) => name(tops[K(x, y)]) === 'izakaya-in-chochin_0_0'), 'hung, on Tops');
        for (const [tx, ty] of TABLES) {
            for (let x = tx; x < tx + 2; x++) assert.ok(K(x, ty) in solid, `table ${x},${ty}`);
            assert.ok(stools.includes(K(tx, ty - 1)) && stools.includes(K(tx, ty + 1)), `stools at the table ${tx},${ty}`);
            assert.ok(lanterns.some(([x, y]) => x === tx + 1 && y === ty - 2), `a lantern over the table at ${tx},${ty}`);
        }
        const glow = c.spriteMetadata['izakaya-in-chochin_0_0'].glow;
        assert.ok(glow && glow.length === 1 && Number.isInteger(glow[0].color) && glow[0].r <= 2.5, 'the lantern glows at night');
        assert.deepStrictEqual([room.lanternLight, room.shopEnabled, room.shopMenu], [true, false, 'izakaya']);
        // every free floor cell can be walked to from the exits
        const free = new Set();
        for (let x = 2; x <= 17; x++) for (let y = 3; y <= 12; y++) if (!(K(x, y) in solid)) free.add(K(x, y));
        const seen = new Set(), todo = room.transporters.map((t) => [t.gridX, t.gridY]);
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (!free.has(K(nx, ny)) || seen.has(K(nx, ny))) continue;
                seen.add(K(nx, ny));
                todo.push([nx, ny]);
            }
        }
        assert.deepStrictEqual([...free].filter((k) => !seen.has(k)), []);
    });

    test('in the Izakaya the bar sells the izakaya menu, the wall clock opens Time Travel and the menu strips say a line (#286)', () => {
        const Rules = game('Interactions'), room = cfg().rooms.Izakaya;
        const hit = (key) => plain(Rules.match(key, room, game('Shop.VENUES')));
        assert.deepStrictEqual(hit('izakaya-in-bar_0_0'), { kind: 'izakaya', group: 'shop', footprint: true });
        assert.deepStrictEqual(hit('office-counter2_0_0'), hit('izakaya-in-bar_0_0'), 'the other shops\' counters still sell');
        assert.strictEqual(hit('izakaya-in-wall-clock_0_0').group, 'clock');
        const menu = hit('izakaya-in-wall-menu_0_0');
        assert.ok(menu && menu.group === 'flavour' && menu.footprint && menu.say && menu.say.length <= 100, 'the menu strips');
        for (const piece of ['wall', 'backbar', 'table', 'chochin', 'casks', 'floor-a']) {
            assert.strictEqual(hit(`izakaya-in-${piece}_0_0`), null, piece);
        }
        assert.strictEqual(Rules.RULES.filter((r) => r.kind === 'menu-strips').length, 1);
    });

    test('in the Izakaya you order at the bar from between the stools, bump the clock and the menu, and sit down to the nomikai (#286)', () => {
        const { world } = worldWith(false);
        const bump = (x, y, dir) => {
            world.enter('Izakaya', x, y);
            const r = world.step(dir);
            assert.strictEqual(r.moved, false, `${x},${y} ${dir}`);
            return r.interaction;
        };
        assert.ok(/^opens the IZAKAYA shop: Highball ¥\d+, Nama Beer ¥\d+, Edamame ¥\d+, Karaage ¥\d+/.test(world.describe(bump(12, 6, 'n'))));
        assert.strictEqual(world.describe(bump(9, 3, 'n')), 'opens the time-travel date picker');
        assert.ok(/^says: "beer, edamame, karaage/.test(world.describe(bump(4, 3, 'n'))));
        assert.strictEqual(bump(5, 8, 'n').kind, 'drinking-game');
        assert.strictEqual(bump(3, 7, 'e').kind, 'drinking-game');
    });

    test('the Izakaya\'s kit is drawn in the house look: doubled pixels, sheet colours, a small palette, inked silhouettes (#286)', () => {
        const png = require(path.join(GV2, 'tools', 'png'));
        const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
        const sheets = new Set();
        const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
            const p = path.join(dir, e.name);
            if (e.isDirectory()) walk(p);
            else if (e.name.endsWith('.png') && !e.name.startsWith('preview')) {
                const { data } = png.decode(fs.readFileSync(p));
                for (let i = 0; i < data.length; i += 4) if (data[i + 3] === 255) sheets.add(hex(data, i));
            }
        });
        walk(path.join(GV2, '..', 'art-source', 'GuttyKreum'));
        for (const [piece, [cw, ch]] of Object.entries(PIECES)) {
            const key = `izakaya-in-${piece}_0_0`;
            const { width: w, height: h, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
            assert.deepStrictEqual([w, h], [64 * cw, 64 * ch], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const v = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === v), `${key}: (${x},${y}) is not a 2x2 block`);
            }
            const colours = new Set();
            for (let i = 0; i < data.length; i += 4) {
                assert.ok(data[i + 3] === 0 || data[i + 3] === 255, `${key}: alpha ${data[i + 3]}`);
                if (data[i + 3] === 255) colours.add(hex(data, i));
            }
            assert.deepStrictEqual([...colours].filter((col) => !sheets.has(col)), [], `${key}: colours in no GuttyKreum sheet`);
            assert.ok(colours.size <= (['bar', 'backbar'].includes(piece) ? 24 : 16), `${key}: ${colours.size} colours`);
            if (!STANDING.includes(piece)) continue;
            const clear = (x, y) => x < 0 || y < 0 || x >= w || y >= h || data[at(x, y) + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (!clear(x, y) && [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) {
                    assert.strictEqual(hex(data, at(x, y)), '0a1627', `${key}: (${x},${y}) is on the silhouette and not ink`);
                }
            }
        }
        const check = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(check.includes("'generate_izakaya_art'") && check.indexOf("'generate_izakaya_art'") < check.indexOf('ART_TOOLS += [WORLDMAP]'),
            'check_generators.py runs the art tool, before the world map');
    });
};
