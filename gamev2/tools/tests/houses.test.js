// House interiors (issue #208): tools/generate_houses.py, the house-door keeping in tools/roomgen.py,
// the flavour rules in src/utils/Interactions.js and the house rules of `play.js lint`.
module.exports = ({ test, assert, fs, path, GV2, game, worldWith }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const houses = (c) => Object.entries(c.rooms).filter(([, r]) => r.house);
    // the door sprites a house may be opened by, and where the door is on each (roomgen.HOUSE_DOORS)
    const FRONTS = { 'building-entrance-1_0_0': 1, 'building-entrance-2_0_0': 1, 'building-entrance-3_0_0': 1 };
    const MACHIYA = ['machiya-black_0_0', 'machiya-red_0_0', 'machiya-blue_0_0'];
    const VOID = 'office-void-autotile_center';
    const python = (args, cwd) => spawnSync('python3', args, { cwd: cwd || GV2, encoding: 'utf8', maxBuffer: 1 << 26 });

    // every cell of a home's lit floor, and the ones a walk from `start` gets to
    const walked = (room, name, start) => {
        const floor = tiles(room, 'Floor'), solid = tiles(room, 'Colliders');
        const free = new Set(Object.keys(floor).filter((c) => name(floor[c]) !== VOID && !(c in solid)));
        const seen = new Set([start.join(',')]), todo = [start];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const c of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (free.has(c.join(',')) && !seen.has(c.join(','))) { seen.add(c.join(',')); todo.push(c); }
            }
        }
        return { free, seen };
    };
    // the generator's layouts, built but not written: { name: { room, arrive } } with tile names
    let built = null;
    const variants = () => {
        if (built) return built;
        const run = python(['tools/generate_houses.py', '--variants']);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout);
        for (const v of Object.values(out.variants)) {
            for (const layer of v.room.layers) {
                for (const c of Object.keys(layer.tiles)) layer.tiles[c] = out.tilePalette[layer.tiles[c]];
            }
        }
        return (built = out.variants);
    };
    // a scratch project a generator can be run in: its own config.json, everything else linked
    const scratch = (fn) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-houses-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            return fn(tmp, () => fs.readFileSync(path.join(tmp, 'config.json'), 'utf8'));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };

    test('every house has a front door on a house, a free cell outside it, and nobody standing there (#208)', () => {
        const c = cfg(), name = (t) => c.tilePalette[t];
        assert.ok(houses(c).length >= 3, 'Asahikawa has three houses');
        for (const [key, room] of houses(c)) {
            const host = c.rooms[room.house.host], [dx, dy] = room.house.door;
            assert.ok(/^House[A-Z][A-Za-z]+\d+$/.test(key) && key.startsWith('House' + room.house.host), key);
            const doors = host.transporters.filter((t) => t.targetRoom === key);
            assert.strictEqual(doors.length, 1, `${key}: exactly one way in`);
            const door = doors[0];
            assert.deepStrictEqual([door.gridX, door.gridY, door.hidden], [dx, dy, true], key);
            // the door is the middle of a townhouse front (or of a machiya's), nothing else
            const sprites = tiles(host, 'Collidables');
            const front = name(sprites[`${dx - 1},${dy}`]) in FRONTS || MACHIYA.includes(name(sprites[`${dx - 2},${dy - 4}`]));
            assert.ok(front, `${key}: the door at ${dx},${dy} is not in a house front`);
            const solid = tiles(host, 'Colliders'), out = `${dx},${dy + 1}`;
            assert.ok(!(`${dx},${dy}` in solid), `${key}: the doorway is sealed`);
            assert.ok(out in tiles(host, 'Floor') && !(out in solid), `${key}: the cell in front of the door is not free`);
            assert.ok(!host.transporters.some((t) => `${t.gridX},${t.gridY}` === out), `${key}: a door in front of the door`);
            // nobody's base or dated position, on any content date, is on the doorway or in front of it
            const taken = host.npcs.flatMap((n) => [n, ...Object.values(n.states || {})])
                .filter((s) => s.gridX === dx && (s.gridY === dy || s.gridY === dy + 1));
            assert.deepStrictEqual(taken, [], `${key}: someone stands at the door`);
            // the way out: one mat, onto the pavement cell outside, and you arrive a cell above it
            assert.strictEqual(room.transporters.length, 1, key);
            const mat = room.transporters[0];
            assert.deepStrictEqual([mat.targetRoom, mat.targetX, mat.targetY], [room.house.host, dx, dy + 1], key);
            assert.deepStrictEqual([door.targetX, door.targetY], [mat.gridX, mat.gridY - 1], `${key}: arrival is above the mat`);
        }
    });

    test('a house is an interior nobody lives in and nothing is sold in, named the way a konbini is (#208)', () => {
        const c = cfg();
        for (const [key, room] of houses(c)) {
            assert.strictEqual(room.interior, true, `${key}: not an interior - the blog pipeline could place a post in it`);
            assert.strictEqual(room.shopEnabled, false, key);
            assert.deepStrictEqual(room.npcs, [], `${key}: nobody lives here yet`);
            const town = c.rooms[room.house.host].name || room.house.host;
            assert.ok(new RegExp(`^House · ${town}( \\d+)?$`).test(room.name), room.name);
            assert.strictEqual(game('hudName')(room.name).split(' | ')[0], 'House', room.name);
            assert.ok(fs.existsSync(path.join(GV2, 'tiled', key.toLowerCase() + '.tmj')), `${key} has no Tiled map`);
        }
        // no two houses of a town share a name
        const names = houses(c).map(([, r]) => r.name);
        assert.strictEqual(new Set(names).size, names.length, names.join(', '));
    });

    test('you can walk into every house from its town and back out onto the cell you came from (#208)', () => {
        const { world, config } = worldWith(false);
        for (const [key, room] of Object.entries(config.rooms).filter(([, r]) => r.house)) {
            const [dx, dy] = room.house.door, host = room.house.host;
            world.enter(host, dx, dy + 1);
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, key, `${host} ${dx},${dy + 1}: the door does not open`);
            const mat = room.transporters[0];
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [key, mat.gridX, mat.gridY - 1]);
            assert.strictEqual(world.step('n').moved, true, `${key}: no way up out of the genkan`);
            world.step('s');
            const out = world.step('s');
            assert.ok(out.transported, `${key}: the mat below the genkan is the way out`);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [host, dx, dy + 1]);
            assert.ok(['s', 'e', 'w'].some((d) => world.canStep(dx, dy + 1, dx + { s: 0, e: 1, w: -1 }[d], dy + 1 + (d === 's' ? 1 : 0))),
                `${key}: boxed in outside the door`);
        }
    });

    test('no house has floor its furniture has sealed off, and every flavour object can be bumped (#208)', () => {
        const c = cfg(), name = (t) => c.tilePalette[t];
        const { world } = worldWith(false);
        for (const [key, room] of houses(c)) {
            const mat = room.transporters[0];
            const { free, seen } = walked(room, name, [mat.gridX, mat.gridY - 1]);
            assert.deepStrictEqual([...free].filter((cell) => !seen.has(cell)), [], `${key}: unreachable floor`);
            assert.ok(free.size >= 30, `${key}: only ${free.size} cells to walk on`);
            const lint = world.lint(key);
            assert.strictEqual(JSON.stringify([lint.errors, lint.warns]), '[{},{}]', key);
            // bump every piece of furniture from every free cell beside it: at least one says a line
            world.enter(key, mat.gridX, mat.gridY - 1);
            const said = new Set();
            for (const cell of seen) {
                const [x, y] = cell.split(',').map(Number);
                for (const [tx, ty] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    const hit = world.interactionAt(tx, ty);
                    if (!hit) continue;
                    assert.strictEqual(hit.group, 'flavour', `${key}: ${hit.kind} at ${tx},${ty} is not a home's`);
                    said.add(hit.say);
                }
            }
            assert.ok(said.size >= 1 && ![...said].some((s) => !s), `${key}: nothing to bump`);
        }
    });

    test('neighbouring houses have different layouts, and Asahikawa shows three of the four (#208)', () => {
        const c = cfg();
        const byTown = {};
        for (const [key, room] of houses(c)) (byTown[room.house.host] = byTown[room.house.host] || []).push([key, room.house]);
        for (const list of Object.values(byTown)) {
            for (const [a, ha] of list) {
                for (const [b, hb] of list) {
                    const near = Math.max(Math.abs(ha.door[0] - hb.door[0]), Math.abs(ha.door[1] - hb.door[1])) <= 12;
                    if (a < b && near) assert.notStrictEqual(ha.layout, hb.layout, `${a} and ${b} are neighbours`);
                }
            }
        }
        assert.strictEqual(new Set(byTown.Asahikawa.map(([, h]) => h.layout)).size, 3);
        // and no two of them are furnished or coloured alike
        const look = byTown.Asahikawa.map(([key]) => JSON.stringify(c.rooms[key].layers));
        assert.strictEqual(new Set(look).size, 3);
    });

    test('each of the four layouts is a whole Japanese home, plain or mirrored (#208)', () => {
        const all = variants();
        assert.deepStrictEqual(Object.keys(all).map((k) => k.replace('-mirrored', '')).filter((k, i, a) => a.indexOf(k) === i),
            ['kotatsu', 'futon', 'flat', 'hearth']);
        assert.strictEqual(Object.keys(all).length, 8);
        const identity = (t) => t;
        const looks = new Set();
        for (const [label, { room, arrive }] of Object.entries(all)) {
            const keys = new Set(room.layers.flatMap((l) => Object.values(l.tiles)));
            const has = (re) => [...keys].some((k) => re.test(k));
            for (const [what, re] of [
                ['a tatami floor', /^home-tatami-/], ['a tokonoma', /^home-tokonoma/], ['a shoji or fusuma', /^home-wall-(shoji|fusuma)/],
                ['a kitchen', /^home-kitchen/], ['a futon or a bed', /^home-(futon|bed)/], ['a television or a bookshelf', /^home-(tv|bookshelf)/],
                ['a kotatsu, a low table or a hearth', /^home-(kotatsu|table|irori)/], ['floor cushions', /^home-zabuton/],
                ['a genkan with shoes in it', /^home-shoes/], ['a step up from the genkan', /^home-agari/],
                ['something to bump', /^home-(kotatsu|irori|stove|tv|bookshelf)/],
            ]) assert.ok(has(re), `${label}: no ${what}`);
            assert.ok(!has(/^office-(?!void)/), `${label}: konbini furniture in a home`);
            const { free, seen } = walked(room, identity, arrive);
            assert.deepStrictEqual([...free].filter((cell) => !seen.has(cell)), [], `${label}: unreachable floor`);
            // the door approach is clear: the genkan cell, the mat under it and the three cells of the step above
            const [ax, ay] = arrive, solid = tiles(room, 'Colliders');
            for (const cell of [[ax, ay], [ax, ay + 1], [ax - 1, ay - 1], [ax, ay - 1], [ax + 1, ay - 1]]) {
                assert.ok(!(cell.join(',') in solid), `${label}: ${cell} by the door is blocked`);
            }
            assert.deepStrictEqual(room.transporters.map((t) => [t.gridX, t.gridY]), [[ax, ay + 1]], label);
            assert.strictEqual(room.interior, true);
            looks.add(JSON.stringify(room.layers));
        }
        assert.strictEqual(looks.size, 8, 'two variants came out the same');
        // a mirrored home is the same home the other way round
        const cols = (room) => Object.keys(tiles(room, 'Collidables')).length;
        assert.strictEqual(cols(all.kotatsu.room), cols(all['kotatsu-mirrored'].room));
    });

    test('the lint knows a home: furniture that seals off floor, or a kotatsu nobody can reach, is an error (#208)', () => {
        const key = 'HouseAsahikawa1';
        const walled = worldWith(false, (config) => {
            const room = config.rooms[key], mat = room.transporters[0];
            // a wall across the row above the step: the genkan still works, the room behind it is cut off
            for (let x = 0; x < 20; x++) room.layers.find((l) => l.collision).tiles[`${x},${mat.gridY - 3}`] = 'gk_blank';
        }).world.lint(key);
        assert.ok((walled.errors['house-sealed-floor'] || []).length > 10, JSON.stringify(walled.errors));
        assert.ok((walled.errors['flavour-no-front'] || []).some((e) => /^home-kotatsu/.test(e)), JSON.stringify(walled.errors));
        assert.ok(!('shop-no-front' in walled.errors) && !('shop-sealed-floor' in walled.errors), 'the shop rules misfired on a house');
        // and the committed world, houses included, is clean
        assert.strictEqual(JSON.stringify(worldWith(false).world.lintProblems()), '[]');
    });

    test('a bump on a home\'s furniture says one line, and only there (#208)', () => {
        const { run } = worldWith(false);
        const Interactions = run('Interactions'), venues = run('Shop.VENUES');
        const home = { interior: true, shopEnabled: false, house: { host: 'Asahikawa' } };
        const said = {};
        for (const key of ['home-kotatsu-red_0_0', 'home-kotatsu-indigo_0_0', 'home-irori_0_0', 'home-stove_0_0', 'home-tv_0_0', 'home-bookshelf_0_0']) {
            const hit = Interactions.match(key, home, venues);
            assert.ok(hit && hit.group === 'flavour' && hit.footprint, key);
            assert.ok(typeof hit.say === 'string' && hit.say.length > 10 && hit.say.length <= 60, `${key}: "${hit.say}"`);
            said[hit.kind] = hit.say;
        }
        assert.strictEqual(new Set(Object.values(said)).size, 5, 'five things, five lines');
        // the rest of the room is furniture, and nothing in a home is a shop
        for (const key of ['home-futon-blue_0_0', 'home-kitchen_0_0', 'home-tansu_0_0', 'home-table_0_0', 'home-fridge_0_0', 'home-tokonoma_0_0']) {
            assert.strictEqual(Interactions.match(key, home, venues), null, key);
        }
        assert.strictEqual(Interactions.match('office-shelf-drinks_0_0', home, venues), null);
        // the other rules return what they always did: no `say` on them
        assert.strictEqual(Object.keys(Interactions.match('office-clock_0_0', { interior: true })).join(), 'kind,group,footprint');
        // the game shows it through the one toast, and does not restart it while it is up (GameScene.checkNPCInteraction)
        const scene = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(/interactionAt\(targetGridX, targetGridY, 'flavour'\)/.test(scene) && /toastText\(\) !== flavour\.say/.test(scene));
    });

    test('generate_houses.py is a no-op on a re-run, and a town rebuild keeps the house doors (#208)', () => {
        scratch((tmp, read) => {
            const before = read();
            for (const args of [['tools/generate_houses.py'], ['tools/generate_houses.py', 'Asahikawa'], ['tools/generate_asahikawa.py']]) {
                const run = python(args, tmp);
                assert.strictEqual(run.status, 0, `${args.join(' ')}: ${run.stderr}`);
                assert.ok(read() === before, `${args.join(' ')} changed config.json on an unchanged world`);
            }
        });
        const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
        assert.ok(/'generate_houses'/.test(tool('check_generators.py')), 'check_generators.py does not run generate_houses');
        for (const art of ['extract_house_interior', 'generate_house_art']) {
            assert.ok(new RegExp(`'${art}'`).test(tool('check_generators.py')), `check_generators.py does not run ${art}`);
        }
        // the town generator itself knows nothing about them: roomgen.save_config puts them back
        assert.ok(!/House/.test(tool('generate_asahikawa.py')));
    });

    test('a house is skipped, and sealed again, when someone stands at its door - and opened again when they leave (#208)', () => {
        scratch((tmp, read) => {
            const before = read(), orig = JSON.parse(before), c = JSON.parse(before);
            const [dx, dy] = c.rooms.HouseAsahikawa2.house.door;
            const samOf = (config) => config.rooms.Asahikawa.npcs.find((n) => n.name === 'Sam');
            samOf(c).states = Object.assign({}, samOf(c).states, { '2027-02-26': { gridX: dx, gridY: dy + 1 } });   // one dated visit is enough
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(c, null, 2));
            const run = python(['tools/generate_houses.py', 'Asahikawa'], tmp);
            assert.strictEqual(run.status, 0, run.stderr);
            assert.ok(new RegExp(`skipped  HouseAsahikawa2 .*Sam \\(2027-02-26\\) stands in front of its door \\(${dx}, ${dy + 1}\\)`).test(run.stdout), run.stdout);
            const after = JSON.parse(read()), town = after.rooms.Asahikawa;
            assert.ok(!('HouseAsahikawa2' in after.rooms), 'the skipped house kept its room');
            assert.ok(`${dx},${dy}` in tiles(town, 'Colliders'), 'the skipped house is not sealed');
            assert.deepStrictEqual(town.transporters.map((t) => t.targetRoom), ['AsahikawaStation', 'HouseAsahikawa1', 'HouseAsahikawa3']);
            // the other two keep their numbers and their rooms, and nobody was moved to make way
            assert.deepStrictEqual(after.rooms.HouseAsahikawa1, orig.rooms.HouseAsahikawa1);
            assert.deepStrictEqual(after.rooms.HouseAsahikawa3, orig.rooms.HouseAsahikawa3);
            assert.deepStrictEqual(town.npcs, c.rooms.Asahikawa.npcs);
            // Sam leaves: the same house comes back exactly as it was
            after.rooms.Asahikawa.npcs = orig.rooms.Asahikawa.npcs;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(after, null, 2));
            assert.strictEqual(python(['tools/generate_houses.py', 'Asahikawa'], tmp).status, 0);
            const again = JSON.parse(read());
            assert.deepStrictEqual(again.rooms.HouseAsahikawa2, orig.rooms.HouseAsahikawa2);
            assert.deepStrictEqual(new Set(again.rooms.Asahikawa.transporters.map((t) => t.targetRoom)),
                new Set(['AsahikawaStation', 'HouseAsahikawa1', 'HouseAsahikawa2', 'HouseAsahikawa3']));
            assert.ok(!(`${dx},${dy}` in tiles(again.rooms.Asahikawa, 'Colliders')), 'the door did not open again');
        });
    });

    test('what is not a house stays sealed: ramen alley, the shrine, the station house keeps its own door (#208)', () => {
        const c = cfg(), name = (t) => c.tilePalette[t], town = c.rooms.Asahikawa;
        const sprites = tiles(town, 'Collidables'), solid = tiles(town, 'Colliders');
        const at = (x, y) => town.transporters.filter((t) => t.gridX === x && t.gridY === y).map((t) => t.targetRoom);
        // the three machiya of ramen alley are shops (a ramen nobori at each front): door (x + 2, y + 4) solid, no way in
        let alley = 0;
        for (const [cell, t] of Object.entries(sprites)) {
            if (!MACHIYA.includes(name(t))) continue;
            const [x, y] = cell.split(',').map(Number);
            assert.ok(`${x + 2},${y + 4}` in solid, `the ramen shop at ${cell} is open`);
            assert.deepStrictEqual(at(x + 2, y + 4), []);
            alley++;
        }
        assert.strictEqual(alley, 3);
        // the shrine hall's doorway (the building's 1,4) is solid
        const shrine = Object.keys(sprites).find((cell) => name(sprites[cell]) === 'shrine-building_0_0').split(',').map(Number);
        assert.ok(`${shrine[0] + 1},${shrine[1] + 4}` in solid && at(shrine[0] + 1, shrine[1] + 4).length === 0, 'the shrine is open');
        // every townhouse front is a house or the station - and the station's still leads to the station
        const fronts = Object.entries(sprites).filter(([, t]) => name(t) in FRONTS).map(([cell]) => cell.split(',').map(Number));
        const targets = fronts.map(([x, y]) => at(x + 1, y)).flat().sort();
        assert.deepStrictEqual(targets, ['AsahikawaStation', 'HouseAsahikawa1', 'HouseAsahikawa2', 'HouseAsahikawa3']);
        // the generator's own account of what it leaves alone
        const src = fs.readFileSync(path.join(GV2, 'tools', 'generate_houses.py'), 'utf8');
        assert.ok(/SHOP_SIGNS = \('ramen-banner_0_0',\)/.test(src));
    });
};
