// Tower lobbies (issue #216): the second kind of building tools/generate_houses.py opens (`--lobbies`),
// the door keeping in tools/roomgen.py, the directory's line and the job's desk and lifts (#226) in
// src/utils/Interactions.js and the lint that holds a lobby to a home's rules.
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
        // every town's towers (#216): the room, its name (a town's only lobby has no number), the tower and its
        // door cells - a glass tower's pair lead into the one lobby
        const table = {
            Market: [['LobbyMarket1', 'Lobby · Asakusa', 'highrise-yellow_0_0', [[16, 29]]]],
            Palace: [['LobbyPalace1', 'Lobby · Marunouchi 1', 'highrise-yellow_0_0', [[49, 13]]],
                ['LobbyPalace2', 'Lobby · Marunouchi 2', 'midrise-apartment_0_0', [[42, 15]]]],
            Fukuoka: [['LobbyFukuoka1', 'Lobby · Fukuoka 1', 'highrise-glass_0_0', [[17, 18], [18, 18]]],
                ['LobbyFukuoka2', 'Lobby · Fukuoka 2', 'highrise-blue_0_0', [[22, 18]]],
                ['LobbyFukuoka3', 'Lobby · Fukuoka 3', 'highrise-yellow_0_0', [[26, 18]]],
                ['LobbyFukuoka4', 'Lobby · Fukuoka 4', 'midrise-apartment_0_0', [[38, 18]]]],
            Sendai: [['LobbySendai1', 'Lobby · Sendai', 'highrise-yellow_0_0', [[23, 20]]]],
            Kanazawa: [['LobbyKanazawa1', 'Lobby · Kanazawa 1', 'highrise-yellow_0_0', [[15, 28]]],
                ['LobbyKanazawa2', 'Lobby · Kanazawa 2', 'midrise-apartment_0_0', [[28, 28]]]],
            SanFranbourne: [['LobbySanFranbourne1', 'Lobby · San Franbourne', 'highrise-glass_0_0', [[47, 27], [48, 27]]]],
        };
        // Sendai's block of flats is the 7-Eleven's: the store stands across its door, so it has no lobby of its own
        const inUse = { Sendai: 1 };
        const days = [...game('contentChangeDates')(c)].sort().concat('2026-11-27', '2027-02-10', '2027-02-20');
        for (const [town, rows] of Object.entries(table)) {
            const host = c.rooms[town], mine = lobbies(c).filter(([, r]) => r.lobby.host === town);
            assert.deepStrictEqual(mine.map(([k, r]) => [k, r.name, towerAt(c, host, ...r.lobby.door), r.lobby.doors]), rows, town);
            assert.deepStrictEqual(host.transporters.filter((t) => /^Lobby/.test(t.targetRoom)).map((t) => [t.gridX, t.gridY, t.targetRoom, t.hidden]).sort(),
                rows.flatMap(([key, , , doors]) => doors.map(([x, y]) => [x, y, key, true])).sort(), town);
            // no tower is skipped: every one standing has its lobby, but for a store's block
            const standing = Object.values(tiles(host, 'Collidables')).filter((t) => c.tilePalette[t] in TOWERS).length;
            assert.strictEqual(standing, rows.length + (inUse[town] || 0), `a tower of ${town} is still sealed`);
            // nobody is at a door or the cell in front of it on any day the world changes, nor is the game's start
            for (const [key, room] of mine) {
                for (const [dx, dy] of room.lobby.doors) {
                    const at = (x, y) => x === dx && (y === dy || y === dy + 1);
                    assert.ok(!(c.player.startRoom === town && at(c.player.startX, c.player.startY)), `${key}: the game starts at its door`);
                    for (const iso of days) {
                        for (const npc of host.npcs) {
                            const s = game('resolveNpc')(npc, iso, game('Trips').of(c));
                            assert.ok(!(s && s.present !== false && at(s.gridX, s.gridY)), `${key}: ${npc.name} is at the door on ${iso}`);
                        }
                    }
                }
            }
        }
        // every town with a tower, and every lobby there is
        assert.deepStrictEqual([...new Set(lobbies(c).map(([, r]) => r.lobby.host))].sort(),
            ['Fukuoka', 'Kanazawa', 'Market', 'Osaka', 'Palace', 'SanFranbourne', 'Sapporo', 'Sendai']);
        assert.strictEqual(lobbies(c).length, 16);
        const towered = Object.keys(c.rooms).filter((k) => !c.rooms[k].interior && Object.values(tiles(c.rooms[k], 'Collidables')).some((t) => c.tilePalette[t] in TOWERS));
        assert.deepStrictEqual(towered.sort(), ['Fukuoka', 'Kanazawa', 'Market', 'Osaka', 'Palace', 'SanFranbourne', 'Sapporo', 'Sendai'], 'a town has a tower and no lobby');
    });

    test('a block of flats with a 7-Eleven across its door is the store\'s, not a tower: Sendai\'s has no lobby and stays shut (#216)', () => {
        const c = cfg(), sendai = c.rooms.Sendai, name = (t) => c.tilePalette[t];
        // the flats at (38,9), door (40,16), and the store standing on the row in front of it, across the door's column
        assert.strictEqual(name(tiles(sendai, 'Collidables')['38,9']), 'highrise-apartment_0_0');
        assert.strictEqual(towerAt(c, sendai, 40, 16), 'highrise-apartment_0_0');
        assert.strictEqual(name(tiles(sendai, 'Collidables')['38,17']), 'seven-eleven_0_0');
        assert.ok('40,16' in tiles(sendai, 'Colliders'), 'the flats\' door is open');
        assert.ok(!sendai.transporters.some((t) => t.gridX === 40 && t.gridY === 16), 'the flats\' door leads somewhere');
        assert.deepStrictEqual(lobbies(c).filter(([, r]) => r.lobby.host === 'Sendai').map(([k]) => k), ['LobbySendai1']);
        // the generator says so, as "not a tower" rather than "skipped", and the other tower is the town's only lobby
        const dry = python(['tools/generate_houses.py', '--dry-run', '--lobbies', 'Sendai']);
        assert.strictEqual(dry.status, 0, dry.stderr);
        assert.ok(/not a tower {2}Sendai highrise-apartment at \(38, 9\) - in use: the 7-Eleven standing across its door is its ground floor/.test(dry.stdout), dry.stdout);
        assert.ok(/built {4}LobbySendai1 "Lobby · Sendai" - highrise-yellow, door \(23, 20\)/.test(dry.stdout), dry.stdout);
        assert.ok(!/skipped/.test(dry.stdout), dry.stdout);
        // no other town's roll-out skips or excludes a tower
        const rest = python(['tools/generate_houses.py', '--dry-run', '--lobbies', 'Fukuoka', 'Kanazawa', 'Market', 'Osaka', 'Palace', 'SanFranbourne', 'Sapporo']);
        assert.strictEqual(rest.status, 0, rest.stderr);
        assert.ok(!/skipped|not a tower/.test(rest.stdout) && /dry run: 15 interior\(s\)/.test(rest.stdout), rest.stdout);
        // a 7-Eleven beside a tower, not across its door, does not make it the store's: take Sendai's away from the
        // door's row and the flats are a tower again (skipped there: the store's own ground is in front of the door)
        scratch((tmp, read) => {
            const moved = JSON.parse(read()), layer = moved.rooms.Sendai.layers.find((l) => l.name === 'Collidables');
            const store = layer.tiles['38,17'];
            delete layer.tiles['38,17'];
            layer.tiles['38,30'] = store;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(moved, null, 2));
            const run = python(['tools/generate_houses.py', '--dry-run', '--lobbies', 'Sendai'], tmp);
            assert.strictEqual(run.status, 0, run.stderr);
            assert.ok(!/not a tower/.test(run.stdout) && /skipped {2}LobbySendai1 \(highrise-apartment, door \(40, 16\)\)/.test(run.stdout), run.stdout);
            assert.ok(/built {4}LobbySendai2 "Lobby · Sendai 2" - highrise-yellow/.test(run.stdout), run.stdout);
        });
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

    test('you can walk into every lobby by each of its doors, bump the directory, the desk and a lift, and leave (#216, #226)', () => {
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
            // every free cell can be walked to, and what can be bumped from them is the directory (a line) and the job (the desk, a lift)
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
                    if (hit) { assert.strictEqual(hit.group, hit.kind === 'directory' ? 'flavour' : 'career', `${key}: ${hit.kind}`); said[hit.kind] = hit.say; }
                }
            }
            assert.strictEqual(seen.size, free.size, `${key}: floor nobody can reach`);
            assert.ok(free.size >= 50, `${key}: only ${free.size} cells to walk on`);
            assert.deepStrictEqual(Object.keys(said).sort(), ['desk', 'directory', 'lift'], key);
            assert.deepStrictEqual([typeof said.directory, said.desk, said.lift], ['string', undefined, undefined], key);
        }
    });

    test('the directory says one line, the desk and the lifts are the job, and the lint holds a lobby to a home\'s rules (#216, #226)', () => {
        const { run } = worldWith(false);
        const Interactions = run('Interactions'), venues = run('Shop.VENUES');
        const lobby = { interior: true, shopEnabled: false, lobby: { host: 'Osaka' } };
        const board = Interactions.match('lobby-directory_0_0', lobby, venues);
        assert.ok(board && board.kind === 'directory' && board.group === 'flavour' && board.footprint);
        assert.ok(typeof board.say === 'string' && board.say.length > 10 && board.say.length <= 60, `"${board.say}"`);
        for (const [key, kind] of [['lobby-lift_0_0', 'lift'], ['lobby-desk_0_0', 'desk']]) {
            const hit = Interactions.match(key, lobby, venues);
            assert.ok(hit && hit.kind === kind && hit.group === 'career' && hit.footprint, key);
            assert.ok(!('say' in hit), `${key}: the job answers for it, not a line`);
        }
        for (const key of ['lobby-sofa_0_0', 'lobby-sofa-back_0_0', 'lobby-table_0_0', 'lobby-plant_0_0', 'lobby-wall_0_0']) {
            assert.strictEqual(Interactions.match(key, lobby, venues), null, key);
        }
        const key = 'LobbyOsaka1';
        const walled = worldWith(false, (config) => {
            const room = config.rooms[key], mat = room.transporters[0];
            // a wall across the lobby two rows above the mat: the directory, the lifts and the desk are behind it
            for (let x = 0; x < 20; x++) room.layers.find((l) => l.collision).tiles[`${x},${mat.gridY - 2}`] = 'gk_blank';
        }).world.lint(key);
        assert.ok((walled.errors['house-sealed-floor'] || []).length > 10, JSON.stringify(walled.errors));
        for (const sprite of [/^lobby-directory/, /^lobby-lift/, /^lobby-desk/]) {
            assert.ok((walled.errors['flavour-no-front'] || []).some((e) => sprite.test(e)), `${sprite}: ${JSON.stringify(walled.errors)}`);
        }
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
