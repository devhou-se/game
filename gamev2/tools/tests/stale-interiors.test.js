// Issue #243: when a building is taken out of a town, the next run of its interior generator drops the
// building's room, the room's tiled/*.tmj and its old door (roomgen.drop_stale, shut_door, save_config).
// Buildings are numbered per town in (y, x) order of their doors, so the room that goes is the highest
// number: the rest move down one.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const cell = (x, y) => `${x},${y}`;
    const byDoor = (a, b) => a[1] - b[1] || a[0] - b[0];                   // (y, x): how a town's buildings are numbered
    // the building's sprite -> its door cells from the sprite's own cell (roomgen's *_DOORS tables, and
    // DOOR_DX / DOOR_DY of generate_konbinis.py and generate_discount_stores.py)
    const HOUSES = { 'machiya-black_0_0': [[2, 4]], 'machiya-red_0_0': [[2, 4]], 'machiya-blue_0_0': [[2, 4]] };
    for (const n of [1, 2, 3]) HOUSES[`building-entrance-${n}_0_0`] = [[1, 0]];
    for (const look of ['red', 'blue']) HOUSES[`hokkaido-house-${look}_0_0`] = [[1, 3]];   // Asahikawa's riverside row (#219)
    const TOWERS = { 'highrise-yellow_0_0': [[1, 7]], 'highrise-blue_0_0': [[2, 10]], 'highrise-glass_0_0': [[1, 9], [2, 9]],
        'highrise-apartment_0_0': [[2, 7]], 'midrise-apartment_0_0': [[2, 5]], 'sapporo-office-brick_0_0': [[2, 6]], 'sapporo-office-glass_0_0': [[2, 5]] };
    const HALLS = { 'shrine-building_0_0': [[1, 4]], 'dazaifu-hall_0_0': [[3, 4]] };
    const PAGODAS = { 'pagoda-floor_0_0': [[1, 2]], 'red-pagoda-small-base_0_0': [[0, 2], [1, 2]] };
    const SEVEN = { 'seven-eleven_0_0': [[1, 3]] };
    const DON = { 'discount-store_0_0': [[2, 7]] };

    // A scratch project a generator can prune in: its own config.json and its own tiled/ (the maps copied,
    // prefabs linked), tools and assets linked. `linked` makes tiled/ a symlink instead, to a copy of the
    // maps (never to the committed ones: this file's whole subject is deleting them).
    const scratch = (fn, linked = false) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-stale-'));
        try {
            const root = path.join(tmp, 'gamev2'), maps = linked ? path.join(tmp, 'maps') : path.join(root, 'tiled');
            fs.mkdirSync(root);
            fs.mkdirSync(maps);
            for (const d of ['tools', 'assets']) fs.symlinkSync(path.join(GV2, d), path.join(root, d));
            for (const f of fs.readdirSync(path.join(GV2, 'tiled')).filter((n) => n.endsWith('.tmj'))) {
                fs.copyFileSync(path.join(GV2, 'tiled', f), path.join(maps, f));
            }
            fs.symlinkSync(path.join(GV2, 'tiled', 'prefabs'), path.join(maps, 'prefabs'));
            if (linked) fs.symlinkSync(maps, path.join(root, 'tiled'));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(root, 'config.json'));
            const file = path.join(root, 'config.json');
            return fn({
                root,
                text: () => fs.readFileSync(file, 'utf8'),
                read: () => JSON.parse(fs.readFileSync(file, 'utf8')),
                write: (c) => fs.writeFileSync(file, JSON.stringify(c, null, 2)),
                maps: () => fs.readdirSync(maps).filter((n) => n.endsWith('.tmj')).sort(),
                run: (...args) => {
                    const run = spawnSync('python3', args, { cwd: root, encoding: 'utf8', maxBuffer: 1 << 26, timeout: 120000,
                        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
                    assert.ok(!run.error, `${args.join(' ')} did not finish: ${run.error}`);
                    assert.strictEqual(run.status, 0, `${args.join(' ')}: ${run.stderr}`);
                    return run.stdout;
                },
            });
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };
    // Take the building whose door is on `door` off the map of `host`: the one sprite that carries it.
    // `unwire` also takes the door's transporter (what a town generator's rebuild leaves); without it the
    // door still leads where it did (a ported town edited by hand).
    const demolish = (c, host, door, table, unwire) => {
        const room = c.rooms[host];
        let taken = 0;
        for (const layer of room.layers) {
            for (const [xy, idx] of Object.entries(layer.tiles)) {
                const [x, y] = xy.split(',').map(Number);
                if ((table[c.tilePalette[idx]] || []).some(([dx, dy]) => x + dx === door[0] && y + dy === door[1])) {
                    delete layer.tiles[xy];
                    taken++;
                }
            }
        }
        assert.strictEqual(taken, 1, `${host}: one building has its door on ${door}`);
        if (unwire) room.transporters = room.transporters.filter((t) => cell(t.gridX, t.gridY) !== cell(...door));
    };
    // the doors of `host` into rooms named `prefix`..., as { 'x,y': room key }
    const doorsInto = (c, host, prefix) => Object.fromEntries(c.rooms[host].transporters
        .filter((t) => t.targetRoom.startsWith(prefix)).map((t) => [cell(t.gridX, t.gridY), t.targetRoom]));
    // a town's rooms of one kind, by their marker: [[key, room]] in key order, and the town's buildings
    // as [door cells] in the order they are numbered
    const marked = (c, marker, host) => Object.entries(c.rooms).filter(([, r]) => r[marker] && r[marker].host === host)
        .sort(([a], [b]) => a.localeCompare(b, 'en', { numeric: true }));
    const hostsOf = (c, marker) => [...new Set(Object.values(c.rooms).filter((r) => r[marker]).map((r) => r[marker].host))].sort();
    // what every prune must leave: a room for every map and a map for every room (check_generators.unmatched_maps)
    const unmatched = (root) => {
        const run = spawnSync('python3', ['-c', 'import json, sys, check_generators as cg; print(json.dumps(cg.unmatched_maps(sys.argv[1])))', root],
            { cwd: GV2, encoding: 'utf8', env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.strictEqual(run.status, 0, run.stderr);
        return JSON.parse(run.stdout);
    };
    // After a prune: `gone` (room keys) and their maps went and nothing else did, the generator said so,
    // maps and rooms are in step, and a second run changes nothing.
    const pruned = (s, before, out, gone, ...again) => {
        const after = s.read();
        const lost = Object.keys(before.c.rooms).filter((k) => !(k in after.rooms)).sort();
        assert.deepStrictEqual(lost, [...gone].sort(), 'the rooms that went');
        assert.deepStrictEqual(Object.keys(after.rooms).filter((k) => !(k in before.c.rooms)), [], 'no room was added');
        const maps = gone.map((k) => `${k.toLowerCase()}.tmj`);
        assert.deepStrictEqual(s.maps(), before.maps.filter((f) => !maps.includes(f)), 'the maps that went, and no other');
        for (const k of gone) {
            assert.ok(out.includes(`removed  ${k} - nothing in`), `the run names ${k} as removed:\n${out}`);
            assert.ok(out.includes(`deleted  tiled/${k.toLowerCase()}.tmj`), `the run names ${k}'s map as deleted:\n${out}`);
        }
        assert.deepStrictEqual(unmatched(s.root), []);
        const text = s.text(), left = s.maps();
        const second = s.run(...again);
        assert.ok(s.text() === text, 'a second run changed config.json');
        assert.deepStrictEqual(s.maps(), left, 'a second run changed tiled/');
        assert.ok(!/^(removed|shut|deleted) /m.test(second), `a second run still found something to drop:\n${second}`);
        return after;
    };
    const start = (s) => ({ c: s.read(), maps: s.maps() });

    // a town with three or more houses numbered 1..n: [host, [door, ...] in house order]
    const houseTown = (c) => {
        for (const host of hostsOf(c, 'house')) {
            const rooms = marked(c, 'house', host);
            if (rooms.length >= 3 && rooms.every(([k], i) => k === `House${host}${i + 1}`)) return [host, rooms.map(([, r]) => r.house.door)];
        }
        throw new Error('no town has three houses numbered from 1');
    };
    // the town's first house is gone: the last house's room and map go, and every door leads to the room that is its own
    const houseGone = (s, unwire) => {
        const before = start(s), c = s.read();
        const [host, doors] = houseTown(c), n = doors.length;
        demolish(c, host, doors[0], HOUSES, unwire);
        s.write(c);
        const out = s.run('tools/generate_houses.py', host);
        const after = pruned(s, before, out, [`House${host}${n}`], 'tools/generate_houses.py', host);
        const old = cell(...doors[0]);
        assert.ok(!(old in tiles(after.rooms[host], 'Colliders')), 'a collider was left on the old door cell');
        assert.ok(!after.rooms[host].transporters.some((t) => cell(t.gridX, t.gridY) === old), 'a door was left on the old door cell');
        const want = {};
        doors.slice(1).forEach((d, i) => { want[cell(...d)] = `House${host}${i + 1}`; });
        assert.deepStrictEqual(doorsInto(after, host, 'House'), want, 'the houses that still stand, renumbered');
        for (const [xy, key] of Object.entries(want)) assert.strictEqual(cell(...after.rooms[key].house.door), xy, `${key} is the house on ${xy}`);
        return { out, host, old };
    };

    test('a house taken out of a town by its generator: the next generate_houses.py run drops its room and its map (#243)', () => {
        scratch((s) => {
            const { out } = houseGone(s, true);
            assert.ok(!/^shut /m.test(out), 'the town generator had dropped the door already: nothing to shut');
        });
    });

    test('a house taken out of a ported town by hand: its old door is dropped too, and the cell is not sealed (#243)', () => {
        scratch((s) => {
            const { out, host, old } = houseGone(s, false);
            assert.ok(out.includes(`shut     ${host} door (${old.replace(',', ', ')}) - it led into House${host}1; no House door is there now`), out);
        });
    });

    test('generate_houses.py --dry-run on a town that lost a house writes neither config.json nor a map (#243)', () => {
        scratch((s) => {
            const c = s.read(), [host, doors] = houseTown(c);
            demolish(c, host, doors[0], HOUSES, true);
            s.write(c);
            const text = s.text(), maps = s.maps();
            const out = s.run('tools/generate_houses.py', host, '--dry-run');
            assert.ok(out.includes(`removed  House${host}${doors.length} - nothing in ${host} claims it any more`), out);
            assert.ok(!out.includes('deleted  '), out);
            assert.ok(s.text() === text, 'a dry run wrote config.json');
            assert.deepStrictEqual(s.maps(), maps, 'a dry run deleted a map');
        });
    });

    test('a tower with a pair of doors taken out of a town: both doors are dropped with its lobby (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            // the last tower of a town whose lobby has two doors: nothing is renumbered
            const [key, room] = Object.entries(c.rooms).filter(([, r]) => r.lobby && r.lobby.doors.length === 2)
                .filter(([k, r]) => marked(c, 'lobby', r.lobby.host).pop()[0] === k)[0];
            const host = room.lobby.host;
            demolish(c, host, room.lobby.door, TOWERS, false);
            s.write(c);
            const out = s.run('tools/generate_houses.py', '--lobbies', host);
            const after = pruned(s, before, out, [key], 'tools/generate_houses.py', '--lobbies', host);
            for (const d of room.lobby.doors) {
                assert.ok(!(cell(...d) in tiles(after.rooms[host], 'Colliders')), `a collider was left on ${d}`);
                assert.ok(out.includes(`shut     ${host} door (${d.join(', ')}) - it led into ${key}`), out);
            }
            const left = { ...doorsInto(before.c, host, 'Lobby') };
            for (const d of room.lobby.doors) delete left[cell(...d)];
            assert.deepStrictEqual(doorsInto(after, host, 'Lobby'), left, 'the other towers keep their doors');
        });
    });

    test('a shrine hall taken out of a town: generate_shrines.py drops the last hall\'s room, its map and the old door (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            // a town with two halls loses its first: the second becomes Shrine<Host>1
            const host = hostsOf(c, 'shrine').find((h) => marked(c, 'shrine', h).length === 2);
            const [first, second] = marked(c, 'shrine', host).map(([, r]) => r.shrine.door);
            demolish(c, host, first, HALLS, false);
            s.write(c);
            const out = s.run('tools/generate_shrines.py', host);
            const after = pruned(s, before, out, [`Shrine${host}2`], 'tools/generate_shrines.py', host);
            assert.deepStrictEqual(after.rooms[`Shrine${host}1`].shrine.door, second);
            assert.deepStrictEqual(doorsInto(after, host, 'Shrine'), { [cell(...second)]: `Shrine${host}1` }, 'one door, into the hall that stands');
            assert.ok(!(cell(...first) in tiles(after.rooms[host], 'Colliders')), 'a collider was left on the old door cell');
            // the mats of the hall that stands lead out in front of its own door
            for (const t of after.rooms[`Shrine${host}1`].transporters) {
                assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], [host, second[0], second[1] + 1]);
            }
        });
    });

    test('a town that lost its only shrine hall, and the door with it, is still visited by generate_shrines.py with no argument (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            const host = hostsOf(c, 'shrine').find((h) => marked(c, 'shrine', h).length === 1);
            const [[key, room]] = marked(c, 'shrine', host);
            demolish(c, host, room.shrine.door, HALLS, true);
            s.write(c);
            const out = s.run('tools/generate_shrines.py');
            const after = pruned(s, before, out, [key], 'tools/generate_shrines.py');
            assert.deepStrictEqual(doorsInto(after, host, 'Shrine'), {});
            // every other hall is as it was
            for (const k of Object.keys(before.c.rooms).filter((r) => before.c.rooms[r].shrine && r !== key)) {
                assert.deepStrictEqual(after.rooms[k], before.c.rooms[k], k);
            }
        });
    });

    // the 7-Elevens of the hosts, from the room keys: { host: [[door, key], ...] in store order }
    const konbinis = (c) => {
        const out = {};
        for (const [host, room] of Object.entries(c.rooms)) {
            const stores = room.transporters.filter((t) => new RegExp(`^Konbini${host}\\d+$`).test(t.targetRoom))
                .map((t) => [[t.gridX, t.gridY], t.targetRoom]).sort(([a], [b]) => byDoor(a, b));
            if (stores.length) out[host] = stores;
        }
        return out;
    };

    test('a 7-Eleven taken out of a host: generate_konbinis.py drops the last store\'s room, its map and the old door (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            // a host with several stores loses its first: every other store moves down one
            const [host, stores] = Object.entries(konbinis(c)).find(([, list]) => list.length >= 3);
            const n = stores.length;
            assert.deepStrictEqual(stores.map(([, k]) => k), stores.map((_, i) => `Konbini${host}${i + 1}`), 'numbered in (y, x) order');
            demolish(c, host, stores[0][0], SEVEN, false);
            s.write(c);
            const out = s.run('tools/generate_konbinis.py', host);
            const after = pruned(s, before, out, [`Konbini${host}${n}`], 'tools/generate_konbinis.py', host);
            const want = {};
            stores.slice(1).forEach(([d], i) => { want[cell(...d)] = `Konbini${host}${i + 1}`; });
            assert.deepStrictEqual(doorsInto(after, host, 'Konbini'), want, 'the stores that still stand, renumbered in (y, x) order');
            assert.ok(!(cell(...stores[0][0]) in tiles(after.rooms[host], 'Colliders')), 'a collider was left on the old door cell');
            // each store is the one behind its door: its mat leads out in front of it
            stores.slice(1).forEach(([d], i) => {
                for (const t of after.rooms[`Konbini${host}${i + 1}`].transporters) {
                    assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], [host, d[0], d[1] + 1]);
                }
            });
        });
    });

    test('a host that lost its only 7-Eleven loses the store\'s room and map (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            const [host, [[door, key]]] = Object.entries(konbinis(c)).find(([, list]) => list.length === 1);
            demolish(c, host, door, SEVEN, true);
            s.write(c);
            const out = s.run('tools/generate_konbinis.py', host);
            const after = pruned(s, before, out, [key], 'tools/generate_konbinis.py', host);
            assert.deepStrictEqual(doorsInto(after, host, 'Konbini'), {});
        });
    });

    test('a discount store taken out of a host: generate_discount_stores.py drops its room, its map and its door (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            const host = Object.keys(c.rooms).filter((h) => `DonTakote${h}` in c.rooms).sort().pop();
            const key = `DonTakote${host}`, door = c.rooms[host].transporters.find((t) => t.targetRoom === key);
            demolish(c, host, [door.gridX, door.gridY], DON, false);
            s.write(c);
            const out = s.run('tools/generate_discount_stores.py', host);
            const after = pruned(s, before, out, [key], 'tools/generate_discount_stores.py', host);
            assert.deepStrictEqual(doorsInto(after, host, 'DonTakote'), {});
            assert.ok(!(cell(door.gridX, door.gridY) in tiles(after.rooms[host], 'Colliders')), 'a collider was left on the old door cell');
        });
    });

    test('a pagoda taken out of a town: generate_pagodas.py drops its room, its map and its doors (#243)', () => {
        scratch((s) => {
            const before = start(s), c = s.read();
            // the last (or only) pagoda of a town: nothing is renumbered
            const host = hostsOf(c, 'pagoda')[0];
            const [key, room] = marked(c, 'pagoda', host).pop();
            demolish(c, host, room.pagoda.door, PAGODAS, false);
            s.write(c);
            const out = s.run('tools/generate_pagodas.py', host);
            const after = pruned(s, before, out, [key], 'tools/generate_pagodas.py', host);
            assert.deepStrictEqual(doorsInto(after, host, 'Pagoda'), {});
            for (const d of room.pagoda.doors) assert.ok(!(cell(...d) in tiles(after.rooms[host], 'Colliders')), `a collider was left on ${d}`);
        });
    });

    test('save_config never deletes a map through a symlinked tiled/: the pruned room\'s map is kept, and said to be (#243)', () => {
        scratch((s) => {
            const c = s.read(), [host, doors] = houseTown(c), maps = s.maps();
            demolish(c, host, doors[0], HOUSES, true);
            s.write(c);
            const out = s.run('tools/generate_houses.py', host);
            const key = `House${host}${doors.length}`, map = `${key.toLowerCase()}.tmj`;
            assert.ok(!(key in s.read().rooms), `${key} was pruned`);
            assert.deepStrictEqual(s.maps(), maps, 'a map was deleted through the link');
            assert.ok(out.includes(`kept     tiled/${map} (tiled is a symlink)`), out);
            assert.ok(!out.includes('deleted  '), out);
            assert.deepStrictEqual(unmatched(s.root), [`tiled/${map} has no room in config.json: delete it`]);
        }, true);
    });
};
