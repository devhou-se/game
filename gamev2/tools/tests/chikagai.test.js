// Underground arcades (chikagai): tools/chikagai.py, tools/generate_chikagai.py, tools/generate_chikagai_art.py.
module.exports = ({ test, assert, fs, path, GV2, game }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const placed = (room, key) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, t]) => name(t) === key).map(([xy]) => xy.split(',').map(Number));
    const arcades = Object.entries(cfg.rooms).filter(([, r]) => r.chikagai);
    const inside = (poly, x, y) => {        // the cell's centre, against the room's outline
        let hit = false;
        for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
            const [xi, yi] = poly[i], [xj, yj] = poly[j];
            if ((yi > y + 0.5) !== (yj > y + 0.5) && x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi) + xi) hit = !hit;
        }
        return hit;
    };
    const reach = (room, from) => {
        const solid = tiles(room, 'Colliders');
        const seen = new Set([from.join(',')]), todo = [from];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const k = `${x + dx},${y + dy}`;
                if (seen.has(k) || k in solid || !inside(room.boundary, x + dx, y + dy)) continue;
                seen.add(k); todo.push([x + dx, y + dy]);
            }
        }
        return seen;
    };

    test('Sapporo has an underground arcade, Aurora Town, with four entrances on the street', () => {
        assert.deepStrictEqual(arcades.map(([k]) => k), ['ChikagaiSapporo']);
        const [, room] = arcades[0];
        assert.strictEqual(room.name, 'Aurora Town');
        assert.ok(room.interior && room.shopEnabled === false);
        // beside the station's doors, in Odori Park, by the TV Tower, east of Tanukikoji
        assert.deepStrictEqual(placed(cfg.rooms.Sapporo, 'chikagai-entrance-snow_0_0').sort((a, b) => a[1] - b[1]),
            [[28, 13], [33, 23], [52, 24], [47, 37]]);
        assert.strictEqual(room.chikagai.doors.length, 8);
    });

    test('an arcade entrance is solid but for the foot of its steps, and each step leads down and back up to the cell in front', () => {
        for (const [key, room] of arcades) {
            const host = cfg.rooms[room.chikagai.host], solid = tiles(host, 'Colliders');
            const entrances = placed(host, 'chikagai-entrance-snow_0_0');
            assert.strictEqual(entrances.length * 2, room.chikagai.doors.length);
            for (const [x, y] of entrances) {
                for (const [dx, dy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) assert.ok(`${x + dx},${y + dy}` in solid, `${key} ${x + dx},${y + dy}`);
                assert.ok(!(`${x},${y + 3}` in solid), `${key}: the cell in front of ${x},${y}`);
                const down = [0, 1].map((dx) => host.transporters.find((t) => t.gridX === x + dx && t.gridY === y + 2));
                for (const t of down) {
                    assert.ok(t && t.targetRoom === key && t.hidden, `${key}: door at ${x},${y + 2}`);
                    assert.ok(!(`${t.gridX},${t.gridY}` in solid));
                    // you arrive on the arcade's floor, not on a way out, under the stairs that lead back here
                    assert.ok(!room.transporters.some((u) => u.gridX === t.targetX && u.gridY === t.targetY));
                    const back = room.transporters.filter((u) => Math.abs(u.gridX - t.targetX) <= 1 && Math.abs(u.gridY - t.targetY) === 1);
                    assert.strictEqual(back.length, 2, `${key}: the stairs over ${t.targetX},${t.targetY}`);
                    for (const u of back) assert.deepStrictEqual([u.targetRoom, u.targetX, u.targetY], [room.chikagai.host, x, y + 3]);
                }
                assert.deepStrictEqual([down[0].targetX, down[0].targetY], [down[1].targetX, down[1].targetY]);
            }
            assert.strictEqual(room.transporters.length, room.chikagai.doors.length);
        }
    });

    test('every exit of an arcade can be walked to from every other, and nothing in it is walled off', () => {
        for (const [key, room] of arcades) {
            const host = cfg.rooms[room.chikagai.host];
            const arrive = host.transporters.filter((t) => t.targetRoom === key).map((t) => [t.targetX, t.targetY]);
            const seen = reach(room, arrive[0]);
            for (const [x, y] of arrive) assert.ok(seen.has(`${x},${y}`), `${key}: ${x},${y}`);
            for (const t of room.transporters) assert.ok(seen.has(`${t.gridX},${t.gridY}`), `${key}: exit ${t.gridX},${t.gridY}`);
            const solid = tiles(room, 'Colliders'), W = room.worldWidth / 64, H = room.worldHeight / 64;
            for (let x = 0; x < W; x++) {
                for (let y = 0; y < H; y++) {
                    if (inside(room.boundary, x, y) && !(`${x},${y}` in solid)) assert.ok(seen.has(`${x},${y}`), `${key}: ${x},${y} cannot be reached`);
                }
            }
        }
    });

    test('an arcade\'s shopfronts answer a bump from the apron in front: three sell a short list, the rest say a line', () => {
        const Interactions = game('Interactions'), venues = game('Shop.VENUES'), items = Array.from(game('Shop.DEFAULT_ITEMS'));
        const sells = (kind) => items.filter((i) => venues[kind].sells(i)).map((i) => i.id).sort();
        assert.deepStrictEqual(sells('bakery'), ['canned-coffee', 'melon-pan', 'nikuman']);
        assert.deepStrictEqual(sells('kissa'), ['canned-coffee', 'green-tea', 'melon-pan']);
        assert.deepStrictEqual(sells('standbar'), ['edamame', 'highball', 'karaage', 'nama-beer']);
        for (const kind of ['bakery', 'kissa', 'standbar']) assert.ok(!venues[kind].buys && !venues[kind].grills);
        const want = { 'chika-shop-bakery': 'bakery', 'chika-shop-kissa': 'kissa', 'chika-shop-bar': 'standbar', 'chika-shop-books': 'bookshop',
            'chika-shop-flowers': 'florist', 'chika-shop-shutter': 'shutter', 'chika-gacha': 'gacha', 'chika-map': 'floor-map' };
        for (const [key, room] of arcades) {
            const seen = reach(room, [room.transporters[0].gridX, room.transporters[0].gridY]);
            const found = {};
            for (const [family, kind] of Object.entries(want)) {
                for (const [x, y] of placed(room, family + '_0_0')) {
                    const hit = Interactions.match(family + '_0_0', room, venues);
                    assert.strictEqual(hit.kind, kind);
                    assert.strictEqual(hit.group, ['bakery', 'kissa', 'standbar'].includes(kind) ? 'shop' : 'flavour');
                    if (hit.group === 'flavour') assert.ok(hit.say);
                    const png = fs.readFileSync(path.join(GV2, 'assets', 'sprites', family + '_0_0.png'));
                    const w = png.readUInt32BE(16) / 64, h = png.readUInt32BE(20) / 64;
                    const front = Array.from({ length: w }, (_, dx) => `${x + dx},${y + h}`);
                    assert.ok(front.some((c) => seen.has(c)), `${key}: ${family} at ${x},${y} has no cell in front`);
                    found[kind] = true;
                }
            }
            for (const kind of ['bakery', 'kissa', 'standbar']) assert.ok(found[kind], `${key}: no ${kind}`);
            // no stamp for a counter here: the arcade is not a store
            assert.strictEqual(game('Stamps.placeFor')('bakery', key, room), null);
        }
    });

    test('an arcade\'s street doors are kept through a rebuild of its town', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'roomgen.py'), 'utf8');
        assert.ok(/CHIKAGAI_PREFIX: \('chikagai', CHIKAGAI_DOORS\)/.test(py), 'roomgen.OWNED_DOORS');
        const checks = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/'generate_chikagai'/.test(checks) && /'generate_chikagai_art'/.test(checks));
        const prefab = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', 'chikagai-entrance-snow.tmj'), 'utf8'));
        const doors = prefab.layers.find((l) => l.name === 'Meta').objects.map((o) => [Math.floor(o.x / 64), Math.floor(o.y / 64)]);
        assert.deepStrictEqual(doors.sort(), [[0, 2], [1, 2]]);
        for (const [, room] of arcades) {
            const host = cfg.rooms[room.chikagai.host];
            for (const [x, y] of room.chikagai.doors) {
                assert.ok(placed(host, 'chikagai-entrance-snow_0_0').some(([ex, ey]) => ey + 2 === y && (ex === x || ex + 1 === x)), `${x},${y}`);
            }
        }
    });

    test('you come out of a door with your back to it: up from an arcade you face the street', () => {
        const faceAway = game('RoomManager.faceAway');
        const plain = (v) => (v ? Array.from(v) : v);
        for (const [key, room] of arcades) {
            const host = cfg.rooms[room.chikagai.host];
            // up to the street: the entrance is behind you (north), so you face south
            for (const t of room.transporters) assert.deepStrictEqual(plain(faceAway(host.transporters, key, t.targetX, t.targetY)), [0, 1]);
            // down into the arcade: away from the stairs you came down, whichever wall they are in
            for (const t of host.transporters.filter((d) => d.targetRoom === key)) {
                const south = room.transporters.some((u) => u.gridX === t.targetX && u.gridY === t.targetY + 1);
                assert.deepStrictEqual(plain(faceAway(room.transporters, room.chikagai.host, t.targetX, t.targetY)), south ? [0, -1] : [0, 1]);
            }
        }
        // no door back beside you: nothing to turn from
        assert.strictEqual(faceAway(cfg.rooms.Sapporo.transporters, 'ChikagaiSapporo', 10, 20), null);
        assert.strictEqual(faceAway(cfg.rooms.Sapporo.transporters, 'SapporoStation', 28, 16), null);
    });
};
