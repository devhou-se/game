// Tower lobbies (issue #216): the second kind of building tools/generate_houses.py opens (`--lobbies`),
// the door keeping in tools/roomgen.py, the directory / lift lines in src/utils/Interactions.js and the
// lint that holds a lobby to a home's rules.
module.exports = ({ test, assert, fs, path, GV2, game, worldWith }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const lobbies = (c) => Object.entries(c.rooms).filter(([, r]) => r.lobby);
    // the towers and where their doors are on the sprite (roomgen.TOWER_DOORS)
    const TOWERS = {
        'highrise-yellow_0_0': [[1, 7]], 'highrise-blue_0_0': [[2, 10]], 'highrise-glass_0_0': [[1, 9], [2, 9]],
        'highrise-apartment_0_0': [[2, 7]], 'midrise-apartment_0_0': [[2, 5]],
        'sapporo-office-brick_0_0': [[2, 6]], 'sapporo-office-glass_0_0': [[2, 5]],     // Sapporo's own (#219)
    };
    const python = (args, cwd) => spawnSync('python3', args, { cwd: cwd || GV2, encoding: 'utf8', maxBuffer: 1 << 26 });
    const scratch = (fn) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-lobbies-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            return fn(tmp, () => fs.readFileSync(path.join(tmp, 'config.json'), 'utf8'));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };
    // the tower sprite of `host` that has a door on (x, y), if any
    const towerAt = (c, host, x, y) => {
        const sprites = tiles(host, 'Collidables');
        for (const [key, doors] of Object.entries(TOWERS)) {
            for (const [dx, dy] of doors) if (c.tilePalette[sprites[`${x - dx},${y - dy}`]] === key) return key;
        }
        return null;
    };

    test('the tower table is the prefabs\' own doors, and no landmark tower is in it (#216)', () => {
        const src = fs.readFileSync(path.join(GV2, 'tools', 'roomgen.py'), 'utf8');
        for (const [key, doors] of Object.entries(TOWERS)) {
            const prefab = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', key.replace('_0_0', '') + '.tmj'), 'utf8'));
            const points = prefab.layers.find((l) => l.name === 'Meta').objects.map((o) => [Math.floor(o.x / 64), Math.floor(o.y / 64)]);
            assert.deepStrictEqual(points, doors, key);
            const row = new RegExp(`'${key}': \\[${doors.map(([x, y]) => `\\(${x}, ${y}\\)`).join(', ')}\\]`);
            assert.ok(row.test(src), `roomgen.TOWER_DOORS has no ${key} with those doors`);
        }
        const table = src.slice(src.indexOf('TOWER_DOORS = {'), src.indexOf('LOBBY_PREFIX ='));
        assert.ok(!/tower|tsutenkaku|castle|discount|shrine|pagoda/.test(table), 'a landmark is listed as a tower');
        assert.strictEqual((table.match(/_0_0'/g) || []).length, Object.keys(TOWERS).length);
    });

    test('every lobby is behind the doors of a tower, with a free cell outside and nobody standing there (#216)', () => {
        const c = cfg();
        assert.deepStrictEqual(lobbies(c).map(([k]) => k).filter((k) => /Osaka/.test(k)), ['LobbyOsaka1', 'LobbyOsaka2', 'LobbyOsaka3']);
        for (const [key, room] of lobbies(c)) {
            const host = c.rooms[room.lobby.host], doors = room.lobby.doors;
            assert.ok(/^Lobby[A-Z][A-Za-z]+\d+$/.test(key) && key.startsWith('Lobby' + room.lobby.host), key);
            assert.deepStrictEqual(room.lobby.door, doors[0], key);
            const ways = host.transporters.filter((t) => t.targetRoom === key);
            assert.deepStrictEqual(ways.map((t) => [t.gridX, t.gridY]).sort(), doors.map((d) => [...d]).sort(), `${key}: one way in per door`);
            const solid = tiles(host, 'Colliders');
            const tower = towerAt(c, host, ...doors[0]);
            assert.ok(tower, `${key}: the door at ${doors[0]} is not a tower's`);
            for (const [dx, dy] of doors) {
                assert.strictEqual(towerAt(c, host, dx, dy), tower, `${key}: ${dx},${dy} is not a door of the same tower`);
                assert.ok(!(`${dx},${dy}` in solid), `${key}: the doorway ${dx},${dy} is sealed`);
                const out = `${dx},${dy + 1}`;
                assert.ok(out in tiles(host, 'Floor') && !(out in solid), `${key}: the cell in front of the door is not free`);
                assert.ok(!host.transporters.some((t) => `${t.gridX},${t.gridY}` === out), `${key}: a door in front of the door`);
                const taken = host.npcs.flatMap((n) => [n, ...Object.values(n.states || {})])
                    .filter((s) => s.gridX === dx && (s.gridY === dy || s.gridY === dy + 1));
                assert.deepStrictEqual(taken, [], `${key}: someone stands at the door`);
            }
            for (const t of ways) assert.strictEqual(t.hidden, true, key);
            // the way out: one mat, onto the pavement outside the first door, and you arrive a cell above it
            assert.strictEqual(room.transporters.length, 1, key);
            const mat = room.transporters[0];
            assert.deepStrictEqual([mat.targetRoom, mat.targetX, mat.targetY], [room.lobby.host, doors[0][0], doors[0][1] + 1], key);
            for (const t of ways) assert.deepStrictEqual([t.targetX, t.targetY], [mat.gridX, mat.gridY - 1], `${key}: arrival is above the mat`);
        }
        // Osaka: the office block, the flats and the glass tower with its pair of doors; Tsutenkaku stays sealed
        const osaka = c.rooms.Osaka;
        assert.deepStrictEqual(lobbies(c).filter(([k]) => /Osaka/.test(k)).map(([, r]) => r.lobby.doors.length), [1, 1, 2]);
        assert.ok(!osaka.transporters.some((t) => /^Lobby/.test(t.targetRoom) && !towerAt(c, osaka, t.gridX, t.gridY)));
        // every tower sprite standing in a town with lobbies either has one or was skipped on purpose: none in Osaka
        const standing = Object.values(tiles(osaka, 'Collidables')).filter((t) => c.tilePalette[t] in TOWERS).length;
        assert.strictEqual(standing, 3);
        // Marunouchi (room Palace): its two towers, the yellow high-rise and the midrise flats, and no other
        const palace = c.rooms.Palace, mine = lobbies(c).filter(([, r]) => r.lobby.host === 'Palace');
        assert.deepStrictEqual(mine.map(([k, r]) => [k, r.name, r.lobby.doors, towerAt(c, palace, ...r.lobby.door)]), [
            ['LobbyPalace1', 'Lobby · Marunouchi 1', [[49, 13]], 'highrise-yellow_0_0'],
            ['LobbyPalace2', 'Lobby · Marunouchi 2', [[42, 15]], 'midrise-apartment_0_0']]);
        assert.strictEqual(Object.values(tiles(palace, 'Collidables')).filter((t) => c.tilePalette[t] in TOWERS).length, 2, 'a tower of Marunouchi is still sealed');
        assert.deepStrictEqual(palace.transporters.filter((t) => /^Lobby/.test(t.targetRoom)).map((t) => [t.gridX, t.gridY, t.targetRoom, t.hidden]),
            [[49, 13, 'LobbyPalace1', true], [42, 15, 'LobbyPalace2', true]]);
        // nobody is at either door or the cell in front of it on any day the world changes, nor is the game's start
        const days = [...game('contentChangeDates')(c)].sort().concat('2026-11-27', '2027-02-10', '2027-02-20');
        for (const [key, room] of mine) {
            const [dx, dy] = room.lobby.door, at = (x, y) => x === dx && (y === dy || y === dy + 1);
            assert.ok(!(c.player.startRoom === 'Palace' && at(c.player.startX, c.player.startY)), `${key}: the game starts at its door`);
            for (const iso of days) {
                for (const npc of palace.npcs) {
                    const s = game('resolveNpc')(npc, iso, game('Trips').of(c));
                    assert.ok(!(s && s.present !== false && at(s.gridX, s.gridY)), `${key}: ${npc.name} is at the door on ${iso}`);
                }
            }
        }
        // every town with a lobby, to date: the redesigned ones and Marunouchi; the rest wait for their rebuild
        assert.deepStrictEqual([...new Set(lobbies(c).map(([, r]) => r.lobby.host))].sort(), ['Osaka', 'Palace', 'Sapporo']);
        assert.strictEqual(lobbies(c).length, 7);
    });

    test('a lobby is one design: a desk, two lifts, plants, seating and a directory, nobody in it, nothing sold (#216)', () => {
        const c = cfg(), name = (t) => c.tilePalette[t];
        const looks = new Set();
        for (const [key, room] of lobbies(c)) {
            assert.strictEqual(room.interior, true, `${key}: not an interior - the blog pipeline could place a post in it`);
            assert.strictEqual(room.shopEnabled, false, key);
            assert.deepStrictEqual(room.npcs, [], key);
            assert.ok(!room.house, `${key}: a lobby is not a house`);
            const town = c.rooms[room.lobby.host].name || room.lobby.host;
            assert.ok(new RegExp(`^Lobby · ${town}( \\d+)?$`).test(room.name), room.name);
            assert.strictEqual(game('hudName')(room.name).split(' | ')[0], 'Lobby', room.name);
            assert.ok(fs.existsSync(path.join(GV2, 'tiled', key.toLowerCase() + '.tmj')), `${key} has no Tiled map`);
            const count = {};
            for (const t of Object.values(tiles(room, 'Collidables'))) count[name(t)] = (count[name(t)] || 0) + 1;
            assert.strictEqual(count['lobby-desk_0_0'], 1, key);
            assert.strictEqual(count['lobby-lift_0_0'], 2, key);
            assert.strictEqual(count['lobby-directory_0_0'], 1, key);
            assert.strictEqual(count['lobby-plant_0_0'], 4, key);
            assert.ok(count['lobby-sofa_0_0'] >= 1 && count['lobby-sofa-back_0_0'] >= 1, `${key}: nowhere to sit`);
            assert.ok(!Object.keys(count).some((k) => /^(home|office)-/.test(k)), `${key}: a home's or a konbini's furniture in a lobby`);
            looks.add(JSON.stringify(room.layers));
        }
        assert.strictEqual(looks.size, 1, 'the lobbies are not identical');
        const names = lobbies(c).map(([, r]) => r.name);
        assert.strictEqual(new Set(names).size, names.length, names.join(', '));
    });

    test('you can walk into every lobby by each of its doors, bump the directory and a lift, and leave (#216)', () => {
        const { world, config } = worldWith(false);
        for (const [key, room] of Object.entries(config.rooms).filter(([, r]) => r.lobby)) {
            const host = room.lobby.host, mat = room.transporters[0], [fx, fy] = room.lobby.doors[0];
            for (const [dx, dy] of room.lobby.doors) {
                world.enter(host, dx, dy + 1);
                const inn = world.step('n');
                assert.strictEqual(inn.transported && inn.transported.to, key, `${host} ${dx},${dy + 1}: the door does not open`);
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [key, mat.gridX, mat.gridY - 1]);
                const out = world.step('s');
                assert.ok(out.transported, `${key}: the mat is the way out`);
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [host, fx, fy + 1]);
            }
            const lint = world.lint(key);
            assert.strictEqual(JSON.stringify([lint.errors, lint.warns]), '[{},{}]', key);
            // every free cell can be walked to, and what can be bumped from them says the two lines
            world.enter(key, mat.gridX, mat.gridY - 1);
            const floor = tiles(room, 'Floor'), solid = tiles(room, 'Colliders');
            const free = new Set(Object.keys(floor).filter((cell) => floor[cell] !== 'office-void-autotile_center' && !(cell in solid)));
            const seen = new Set([`${mat.gridX},${mat.gridY - 1}`]), todo = [[mat.gridX, mat.gridY - 1]];
            const said = {};
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [tx, ty] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    const cell = `${tx},${ty}`;
                    if (free.has(cell) && !seen.has(cell)) { seen.add(cell); todo.push([tx, ty]); }
                    const hit = world.interactionAt(tx, ty);
                    if (hit) { assert.strictEqual(hit.group, 'flavour', `${key}: ${hit.kind}`); said[hit.kind] = hit.say; }
                }
            }
            assert.strictEqual(seen.size, free.size, `${key}: floor nobody can reach`);
            assert.ok(free.size >= 50, `${key}: only ${free.size} cells to walk on`);
            assert.deepStrictEqual(Object.keys(said).sort(), ['directory', 'lift'], key);
        }
    });

    test('the directory and the lifts say one line each, and the lint holds a lobby to a home\'s rules (#216)', () => {
        const { run } = worldWith(false);
        const Interactions = run('Interactions'), venues = run('Shop.VENUES');
        const lobby = { interior: true, shopEnabled: false, lobby: { host: 'Osaka' } };
        const lines = ['lobby-directory_0_0', 'lobby-lift_0_0'].map((key) => {
            const hit = Interactions.match(key, lobby, venues);
            assert.ok(hit && hit.group === 'flavour' && hit.footprint, key);
            assert.ok(typeof hit.say === 'string' && hit.say.length > 10 && hit.say.length <= 60, `${key}: "${hit.say}"`);
            return hit.say;
        });
        assert.notStrictEqual(lines[0], lines[1]);
        for (const key of ['lobby-desk_0_0', 'lobby-sofa_0_0', 'lobby-sofa-back_0_0', 'lobby-table_0_0', 'lobby-plant_0_0', 'lobby-wall_0_0']) {
            assert.strictEqual(Interactions.match(key, lobby, venues), null, key);
        }
        const key = 'LobbyOsaka1';
        const walled = worldWith(false, (config) => {
            const room = config.rooms[key], mat = room.transporters[0];
            // a wall across the lobby two rows above the mat: the directory and the lifts are behind it
            for (let x = 0; x < 20; x++) room.layers.find((l) => l.collision).tiles[`${x},${mat.gridY - 2}`] = 'gk_blank';
        }).world.lint(key);
        assert.ok((walled.errors['house-sealed-floor'] || []).length > 10, JSON.stringify(walled.errors));
        assert.ok((walled.errors['flavour-no-front'] || []).some((e) => /^lobby-directory/.test(e)), JSON.stringify(walled.errors));
        assert.ok(!('shop-no-front' in walled.errors) && !('shop-sealed-floor' in walled.errors));
    });

    test('generate_houses.py leaves lobbies alone on a re-run, a house run and a town rebuild; --dry-run writes nothing (#216)', () => {
        scratch((tmp, read) => {
            const before = read();
            for (const args of [['tools/generate_houses.py'], ['tools/generate_houses.py', '--lobbies'], ['tools/generate_houses.py', '--lobbies', 'Osaka'],
                ['tools/generate_osaka.py'], ['tools/generate_houses.py', '--dry-run', '--lobbies', 'Sapporo'], ['tools/generate_houses.py', '--dry-run', 'Osaka']]) {
                const run = python(args, tmp);
                assert.strictEqual(run.status, 0, `${args.join(' ')}: ${run.stderr}`);
                assert.ok(read() === before, `${args.join(' ')} changed config.json`);
            }
            const dry = python(['tools/generate_houses.py', '--dry-run', '--lobbies', 'Sapporo'], tmp).stdout;
            assert.ok(/dry run: \d+ interior\(s\) would be written, nothing was/.test(dry), dry);
            // opening a town's houses (the #208 rollout) neither removes nor rebuilds its lobbies...
            const orig = JSON.parse(before);
            assert.strictEqual(python(['tools/generate_houses.py', 'Osaka'], tmp).status, 0);
            const housed = JSON.parse(read());
            for (const [key, room] of lobbies(orig)) assert.deepStrictEqual(housed.rooms[key], room, key);
            const into = (c) => c.rooms.Osaka.transporters.filter((t) => /^Lobby/.test(t.targetRoom));
            assert.deepStrictEqual(into(housed), into(orig));
            // ...and a lobby run does not touch the houses that run opened
            const mid = read();
            assert.strictEqual(python(['tools/generate_houses.py', '--lobbies', 'Osaka'], tmp).status, 0);
            assert.ok(read() === mid, 'a lobby run changed a town with houses');
        });
        assert.ok(!/Lobby/.test(fs.readFileSync(path.join(GV2, 'tools', 'generate_osaka.py'), 'utf8')), 'the town generator knows about lobbies');
    });

    test('a tower is skipped and sealed when someone stands at its door; a pair of doors opens the one that is free (#216)', () => {
        scratch((tmp, read) => {
            const before = read(), orig = JSON.parse(before);
            const stand = (cells) => {
                const c = JSON.parse(before), npc = c.rooms.Osaka.npcs[0];
                npc.states = Object.assign({}, npc.states);
                cells.forEach(([x, y], i) => { npc.states[`2031-01-0${i + 1}`] = { gridX: x, gridY: y }; });
                fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(c, null, 2));
                const run = python(['tools/generate_houses.py', '--lobbies', 'Osaka'], tmp);
                assert.strictEqual(run.status, 0, run.stderr);
                return { out: run.stdout, after: JSON.parse(read()), npcs: c.rooms.Osaka.npcs };
            };
            const [[ax, ay], [bx, by]] = orig.rooms.LobbyOsaka3.lobby.doors;
            const [ox, oy] = orig.rooms.LobbyOsaka1.lobby.door;
            // one of the glass tower's two doors: the other still opens, and is where you come out
            let { after, npcs } = stand([[ax, ay + 1]]);
            assert.deepStrictEqual(after.rooms.LobbyOsaka3.lobby.doors, [[bx, by]]);
            assert.ok(`${ax},${ay}` in tiles(after.rooms.Osaka, 'Colliders') && !(`${bx},${by}` in tiles(after.rooms.Osaka, 'Colliders')));
            assert.deepStrictEqual(after.rooms.Osaka.transporters.filter((t) => t.targetRoom === 'LobbyOsaka3').map((t) => [t.gridX, t.gridY]), [[bx, by]]);
            assert.deepStrictEqual([after.rooms.LobbyOsaka3.transporters[0].targetX, after.rooms.LobbyOsaka3.transporters[0].targetY], [bx, by + 1]);
            assert.deepStrictEqual(after.rooms.Osaka.npcs, npcs, 'someone was moved to make way');
            // both of them, and the office block's one door: both towers are sealed and lose their rooms
            let out;
            ({ out, after } = stand([[ax, ay + 1], [bx, by + 1], [ox, oy + 1]]));
            assert.ok(/skipped {2}LobbyOsaka3 .* stands in front of its door/.test(out) && /skipped {2}LobbyOsaka1 /.test(out), out);
            assert.ok(!('LobbyOsaka3' in after.rooms) && !('LobbyOsaka1' in after.rooms));
            for (const cell of [`${ax},${ay}`, `${bx},${by}`, `${ox},${oy}`]) assert.ok(cell in tiles(after.rooms.Osaka, 'Colliders'), `${cell} is not sealed`);
            assert.deepStrictEqual(after.rooms.Osaka.transporters.filter((t) => /^Lobby/.test(t.targetRoom)).map((t) => t.targetRoom), ['LobbyOsaka2']);
            assert.deepStrictEqual(after.rooms.LobbyOsaka2, orig.rooms.LobbyOsaka2, 'the flats were renumbered or rebuilt');
            // they leave: the same lobbies come back
            after.rooms.Osaka.npcs = orig.rooms.Osaka.npcs;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(after, null, 2));
            assert.strictEqual(python(['tools/generate_houses.py', '--lobbies', 'Osaka'], tmp).status, 0);
            const again = JSON.parse(read());
            for (const key of ['LobbyOsaka1', 'LobbyOsaka2', 'LobbyOsaka3']) assert.deepStrictEqual(again.rooms[key], orig.rooms[key], key);
            assert.deepStrictEqual(tiles(again.rooms.Osaka, 'Colliders'), tiles(orig.rooms.Osaka, 'Colliders'));
        });
    });
};
