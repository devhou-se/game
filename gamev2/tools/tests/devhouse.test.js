// The Devhouses of Tokyo and Osaka (issue #69): tools/generate_devhouses.py, tools/generate_devhouse_art.py,
// the Devhouse row of roomgen.OWNED_DOORS, and the flavour and glow rows of what stands in them.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, worldWith, require: need }) => {
    const { spawnSync } = need('child_process');
    const os = need('os');
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    const VOID = 'office-void-autotile_center';
    // city: its host room, the building's sprite, the door's offset on it (roomgen.DEVHOUSE_DOORS), its floors
    const HOUSES = {
        Tokyo: { host: 'Park', sprite: 'devhouse-tokyo_0_0', at: [10, 9], door: [13, 16], floors: 6, place: 'TokyoCity' },
        Osaka: { host: 'Osaka', sprite: 'devhouse-osaka_0_0', at: [9, 10], door: [10, 16], floors: 4, place: 'Osaka' },
    };
    const key = (city, n) => `Devhouse${city}${n}F`;
    const floors = (city) => Array.from({ length: HOUSES[city].floors }, (_, i) => i + 1);
    const ALL = Object.keys(HOUSES).flatMap((city) => floors(city).map((n) => key(city, n)));
    const DIRS = { n: [0, -1], s: [0, 1], e: [1, 0], w: [-1, 0] };
    // where every copy of a sprite stands in a room, whatever its layer: [[x, y], ...]
    const at = (room, c, sprite) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => c.tilePalette[id] === `${sprite}_0_0`).map(([cell]) => cell.split(',').map(Number));
    // a cell you can stand on, from the config alone: in the room, floored, nothing solid on it
    const free = (c, roomKey, x, y) => {
        const room = c.rooms[roomKey], floor = tiles(room, 'Floor')[`${x},${y}`];
        return x >= 0 && y >= 0 && x < room.worldWidth / 64 && y < room.worldHeight / 64 &&
            floor !== undefined && c.tilePalette[floor] !== VOID && !(`${x},${y}` in tiles(room, 'Colliders'));
    };
    const exit = (c, roomKey, x, y) => c.rooms[roomKey].transporters.some((t) => t.gridX === x && t.gridY === y);
    const stand = (c, roomKey, x, y) => free(c, roomKey, x, y) && !exit(c, roomKey, x, y);      // ...and stay on
    // the stair of floor n that leads to floor m, and the street mat (m = 0)
    const way = (c, city, n, m) => c.rooms[key(city, n)].transporters.filter((t) => t.targetRoom === (m ? key(city, m) : HOUSES[city].host));
    /**
     * THE HELD-KEY RULE. A room change does not let go of a held key, so the step that took you through an exit
     * is taken again from the cell you arrive on. Every exit of `rooms`, entered in each direction it can be
     * entered from, whose repeated step lands on another exit: ["DevhouseTokyo1F 16,12 s -> DevhouseTokyo2F 15,12"].
     */
    const bounces = (c, rooms) => {
        const out = [], entered = {};
        for (const [roomKey, list] of rooms) {
            for (const t of list) {
                const id = `${roomKey} ${t.gridX},${t.gridY}`;
                entered[id] = 0;
                for (const [dir, [dx, dy]] of Object.entries(DIRS)) {
                    if (!stand(c, roomKey, t.gridX - dx, t.gridY - dy)) continue;
                    entered[id]++;
                    if (exit(c, t.targetRoom, t.targetX + dx, t.targetY + dy)) out.push(`${id} ${dir} -> ${t.targetRoom} ${t.targetX + dx},${t.targetY + dy}`);
                }
            }
        }
        return { out, entered };
    };
    const exitsOf = (c) => ALL.map((k) => [k, c.rooms[k].transporters])
        .concat(Object.values(HOUSES).map((h) => [h.host, c.rooms[h.host].transporters.filter((t) => /^Devhouse/.test(t.targetRoom))]));
    // a scratch project a generator can be run in: its own config.json, everything else linked
    const scratch = (fn) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-devhouse-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            return fn(tmp, () => fs.readFileSync(path.join(tmp, 'config.json'), 'utf8'));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };
    const python = (args, cwd) => spawnSync('python3', args, { cwd: cwd || GV2, encoding: 'utf8', maxBuffer: 1 << 26,
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });

    test('the two Devhouses are a room a floor, six in Tokyo and four in Osaka; only the ground floor carries the street door, one door under the building (#69)', () => {
        const c = cfg();
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Devhouse/.test(k)).sort(), ALL.slice().sort());
        for (const [city, h] of Object.entries(HOUSES)) {
            const host = c.rooms[h.host], solid = tiles(host, 'Colliders');
            for (const n of floors(city)) {
                const room = c.rooms[key(city, n)];
                assert.strictEqual(room.name, `Devhouse ${n}F · ${city}`);
                // the street door is a kept door (roomgen.OWNED_DOORS) and the stairs are not: only 1F says `door`
                assert.deepStrictEqual(room.devhouse, n === 1 ? { door: h.door, floor: 1, host: h.host } : { floor: n, host: h.host }, key(city, n));
                assert.deepStrictEqual([room.interior, room.shopEnabled, room.npcs], [true, false, []], key(city, n));
                assert.ok(!room.house && !room.lobby, 'not a house of the roll-out, not a lobby');
            }
            // the building stands once, on Collidables, and its door is the one cell of its front that is open
            assert.deepStrictEqual(at(host, c, h.sprite.replace('_0_0', '')), [h.at]);
            assert.strictEqual(c.tilePalette[tiles(host, 'Collidables')[h.at.join(',')]], h.sprite);
            const doors = host.transporters.filter((t) => /^Devhouse/.test(t.targetRoom));
            assert.deepStrictEqual(doors.map((t) => [t.gridX, t.gridY, t.targetRoom, t.hidden]), [[...h.door, key(city, 1), true]]);
            const [dx, dy] = h.door;
            const { width, height } = need(path.join(GV2, 'tools', 'png')).decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', h.sprite + '.png')));
            assert.deepStrictEqual([dx, dy], [h.at[0] + (city === 'Tokyo' ? 3 : 1), h.at[1] + height / 64 - 1], 'the door is in the foot of the sprite');
            const open = [];
            for (let x = h.at[0]; x < h.at[0] + width / 64; x++) if (!(`${x},${dy}` in solid)) open.push(x);
            assert.deepStrictEqual(open, [dx], 'the rest of the front is sealed');
            assert.ok(stand(c, h.host, dx, dy + 1), 'a free cell outside the door');
            // you arrive beside the mat that leads back out, and it puts you on the cell outside the door
            const mat = way(c, city, 1, 0);
            assert.deepStrictEqual(mat.map((t) => [t.targetX, t.targetY]), [[dx, dy + 1]]);
            assert.deepStrictEqual([doors[0].targetX, doors[0].targetY], [mat[0].gridX, mat[0].gridY - 1]);
            assert.strictEqual(c.tilePalette[tiles(c.rooms[key(city, 1)], 'Over Floor')[`${mat[0].gridX},${mat[0].gridY}`]], 'home-doormat_0_0');
            // nobody stands on the door or in front of it on any date, and no blog spot is there
            const cells = [`${dx},${dy}`, `${dx},${dy + 1}`];
            const inWay = host.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
                .filter(([, s]) => cells.includes(`${s.gridX},${s.gridY}`)).map(([date]) => `${n.name} ${date}`));
            assert.deepStrictEqual(inWay, []);
            for (const d of (c.districts || {})[h.host] || []) assert.ok(!cells.includes(d.stand.join(',')), d.name);
        }
        // no other room has a door into a Devhouse
        const into = Object.entries(c.rooms).filter(([k, r]) => !/^Devhouse/.test(k) && (r.transporters || []).some((t) => /^Devhouse/.test(t.targetRoom)));
        assert.deepStrictEqual(into.map(([k]) => k).sort(), ['Osaka', 'Park']);
        // Osaka's Devhouse took the black townhouse's lot on Dotonbori: its house is gone, the other two renumbered
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^HouseOsaka/.test(k)), ['HouseOsaka1', 'HouseOsaka2']);
        assert.ok(c.rooms.Osaka.transporters.every((t) => !(t.gridX === 10 && t.gridY === 16) || t.targetRoom === 'DevhouseOsaka1F'));
        assert.deepStrictEqual(fs.readdirSync(path.join(GV2, 'tiled')).filter((f) => /^houseosaka3/.test(f)), [], 'the third house\'s map went with it');
        for (const k of ALL) assert.ok(fs.existsSync(path.join(GV2, 'tiled', k.toLowerCase() + '.tmj')), `${k} has its map`);
    });

    test('every Devhouse stair is a flight with two ends: up lands beside the way back down, down beside the way back up, and never on an exit (#69)', () => {
        const c = cfg();
        for (const [city, h] of Object.entries(HOUSES)) {
            for (const n of floors(city)) {
                const room = c.rooms[key(city, n)], floor = tiles(room, 'Floor');
                // exactly the exits a floor should have: the street on 1F, a stair down from 2F up, a stair up below the top
                const want = [n === 1 ? h.host : key(city, n - 1)].concat(n < h.floors ? [key(city, n + 1)] : []);
                assert.deepStrictEqual(room.transporters.map((t) => t.targetRoom).sort(), want.sort(), key(city, n));
                assert.ok(room.transporters.every((t) => t.hidden), 'a stair is a hidden exit, laid with its tile');
                if (n === h.floors) continue;
                const [up] = way(c, city, n, n + 1), [down] = way(c, city, n + 1, n);
                assert.strictEqual(c.tilePalette[floor[`${up.gridX},${up.gridY}`]], 'devhouse-stairs-up_0_0', `${key(city, n)} up`);
                assert.strictEqual(c.tilePalette[tiles(c.rooms[key(city, n + 1)], 'Floor')[`${down.gridX},${down.gridY}`]], 'devhouse-stairs-down_0_0', `${key(city, n + 1)} down`);
                for (const [stair, back, from, to] of [[up, down, n, n + 1], [down, up, n + 1, n]]) {
                    // the one free cell north or south of the other end
                    const beside = [-1, 1].map((dy) => [back.gridX, back.gridY + dy]).filter(([x, y]) => stand(c, key(city, to), x, y));
                    assert.deepStrictEqual(beside, [[stair.targetX, stair.targetY]], `${key(city, from)} -> ${key(city, to)}`);
                }
            }
        }
        // Tokyo: the ground floor and the one above are the stair hall of the floors over them, on the same room
        // cells - a stair up at 16,12 and a stair down at 15,10 on every floor that has one, 1F's mat at 15,12
        for (const n of floors('Tokyo')) {
            const cells = (m) => way(c, 'Tokyo', n, m).map((t) => [t.gridX, t.gridY, t.targetX, t.targetY]);
            if (n < 6) assert.deepStrictEqual(cells(n + 1), [[16, 12, 15, 11]], `Tokyo ${n}F up`);
            assert.deepStrictEqual(cells(n - 1), n === 1 ? [[15, 12, 13, 17]] : [[15, 10, 16, 11]], `Tokyo ${n}F down`);
            if (n > 1) assert.deepStrictEqual(at(c.rooms[key('Tokyo', n)], c, 'devhouse-stairwell'), [[15, 9]], 'the stairwell over the way down');
        }
        assert.deepStrictEqual(c.rooms.DevhouseTokyo1F.transporters.length + c.rooms.DevhouseTokyo2F.transporters.length, 4);
        assert.deepStrictEqual(Object.entries(HOUSES).map(([city]) => way(c, city, HOUSES[city].floors, HOUSES[city].floors + 1)), [[], []], 'no stair up from the top');
    });

    test('a key held down through a Devhouse stair or its street door never bounces you back: the same step from where you arrive is not an exit (#69)', () => {
        const c = cfg();
        const { out, entered } = bounces(c, exitsOf(c));
        assert.deepStrictEqual(out, []);
        // every one of them was looked at: 2 street doors, 2 mats and 8 flights with two ends, each walked into
        assert.strictEqual(Object.keys(entered).length, 2 + 2 + 2 * (5 + 3));
        for (const [id, n] of Object.entries(entered)) assert.ok(n >= 1, `${id} cannot be walked into`);
        // the rule has teeth: Tokyo's first draft had the way down on the front row beside the way up, so that
        // holding DOWN on 1F's stair took you up to 2F, straight back down, and so on for ever
        const draft = cfg(), two = draft.rooms.DevhouseTokyo2F, down = two.transporters.find((t) => t.targetRoom === 'DevhouseTokyo1F');
        const up = draft.rooms.DevhouseTokyo1F.transporters.find((t) => t.targetRoom === 'DevhouseTokyo2F');
        [down.gridX, down.gridY] = [15, 12];
        tiles(two, 'Floor')['15,12'] = tiles(two, 'Floor')['16,12'];
        [up.targetX, up.targetY] = [15, 11];
        assert.deepStrictEqual(bounces(draft, exitsOf(draft)).out, ['DevhouseTokyo1F 16,12 s -> DevhouseTokyo2F 15,12', 'DevhouseTokyo2F 15,12 s -> DevhouseTokyo1F 16,12']);
        // the generator says so where the stairs are drawn
        assert.ok(/THE HELD-KEY RULE/.test(tool('generate_devhouses.py')) && /devhouse\.test\.js/.test(tool('generate_devhouses.py')));
    });

    test('you walk in off the street, climb to the top floor of each Devhouse and come back out on the cell you went in by (#69)', () => {
        for (const stitch of [true, false]) {
            const { world, config } = worldWith(stitch);
            for (const [city, h] of Object.entries(HOUSES)) {
                const stairs = (n, m) => config.rooms[key(city, n)].transporters.find((t) => t.targetRoom === (m ? key(city, m) : h.host));
                const take = (t, to) => {
                    const steps = world.path(t.gridX, t.gridY);
                    assert.ok(steps && steps.length, `no way to the exit at ${t.gridX},${t.gridY} of ${world.here().room} (stitch ${stitch})`);
                    let last;
                    for (const dir of steps) last = world.step(dir);
                    assert.strictEqual(last.transported && last.transported.to, to);
                    const here = world.here();
                    assert.deepStrictEqual([here.room, here.x, here.y], [to, t.targetX, t.targetY]);
                    assert.ok(!world.room.transporters.some((x) => x.gridX === world.player.gridX && x.gridY === world.player.gridY), 'arrives off the exits');
                };
                world.enter(h.host, h.door[0], h.door[1] + 1);
                const inn = world.step('n');
                assert.strictEqual(inn.transported && inn.transported.to, key(city, 1), `${city} (stitch ${stitch})`);
                for (let n = 1; n < h.floors; n++) take(stairs(n, n + 1), key(city, n + 1));
                assert.strictEqual(world.here().room, key(city, h.floors));
                for (let n = h.floors; n > 1; n--) take(stairs(n, n - 1), key(city, n - 1));
                take(stairs(1, 0), h.host);
                assert.deepStrictEqual([world.here().x, world.here().y], [h.door[0], h.door[1] + 1]);
            }
        }
    });

    test('every cell of every Devhouse floor is walked to from where you arrive, and the maps lint clean, the two hosts too (#69)', () => {
        const { world, config } = worldWith(false);
        const c = cfg();
        for (const k of ALL) {
            const first = config.rooms[k].transporters[0];
            const beside = [-1, 1].map((dy) => [first.gridX, first.gridY + dy]).find(([x, y]) => stand(c, k, x, y));
            world.enter(k, ...beside);
            const seen = world.reachable();
            const room = c.rooms[k], lost = [];
            for (const cell of Object.keys(tiles(room, 'Floor'))) {
                const [x, y] = cell.split(',').map(Number);
                if (free(c, k, x, y) && !seen.has(cell)) lost.push(cell);
            }
            assert.deepStrictEqual(lost, [], `${k}: cells nobody can stand on`);
            // every flavour fixture can be bumped: it says its line from a cell you can get to
            for (const i of world.interactions().filter((x) => x.group === 'flavour')) {
                const sides = [];
                for (let x = i.x; x < i.x + i.w; x++) for (let y = i.y; y < i.y + i.h; y++) for (const [dx, dy] of Object.values(DIRS)) sides.push([x + dx, y + dy, x, y]);
                const side = sides.find(([x, y, fx, fy]) => seen.has(`${x},${y}`) && world.interactionAt(fx, fy) && world.interactionAt(fx, fy).kind === i.kind);
                assert.ok(side, `${k}: no way to bump the ${i.kind} at ${i.x},${i.y}`);
            }
        }
        for (const k of ALL.concat(['Park', 'Osaka', 'HouseOsaka1', 'HouseOsaka2'])) {
            const lint = world.lint(k);
            assert.deepStrictEqual(plain([lint.errors, lint.warns]), [{}, {}], `lint ${k}`);
        }
    });

    test('the Devhouse floors hold what their floor plans show: kitchens, tables and chairs, beds, baths, and nothing on the two floors that are not ours (#69)', () => {
        const c = cfg();
        const count = (k, sprite) => at(c.rooms[k], c, sprite).length;
        // floor: what must be there, by sprite key (design: docs/workshop/69-..., the fixture table)
        const PLAN = {
            DevhouseTokyo3F: { 'home-kitchen': 2, 'home-fridge': 1, 'devhouse-table-wide': 1, 'devhouse-chair-n': 4, 'devhouse-chair-s': 4, 'devhouse-sofa': 1,
                'devhouse-counter': 2, 'devhouse-stool': 4, 'devhouse-basin': 1, 'devhouse-toilet': 1 },
            DevhouseTokyo4F: { 'home-bed': 3, 'devhouse-bunk': 1, 'home-tansu': 1, 'lobby-sofa': 1, 'devhouse-basin': 1, 'devhouse-toilet': 1 },
            DevhouseTokyo5F: { 'home-futon-blue': 2, 'home-futon-rose': 1, 'home-zabuton-indigo': 1, 'home-zabuton-red': 1, 'home-tansu': 1, 'home-andon': 1,
                'devhouse-bath': 1, 'devhouse-basin': 1, 'devhouse-toilet': 1, 'devhouse-door': 1, 'home-wall-fusuma': 4 },
            DevhouseTokyo6F: { 'home-bed': 2, 'devhouse-table-small': 1, 'devhouse-chair-w': 2, 'devhouse-chair-e': 2, 'devhouse-counter': 3,
                'devhouse-basin': 1, 'devhouse-washer': 1 },
            DevhouseOsaka1F: { 'home-kitchen': 1, 'home-fridge': 1, 'devhouse-table-tall': 1, 'devhouse-chair-n': 1, 'devhouse-chair-s': 1, 'devhouse-chair-w': 3,
                'devhouse-chair-e': 3, 'devhouse-shower': 1, 'devhouse-basin': 1, 'devhouse-toilet': 1, 'home-getabako': 1, 'home-tansu': 1 },
            DevhouseOsaka2F: { 'home-bed': 2, 'devhouse-armchair': 2, 'devhouse-side-table': 1, 'devhouse-shower': 1, 'devhouse-basin': 1, 'devhouse-toilet': 1 },
            DevhouseOsaka3F: { 'home-bed': 2, 'devhouse-washer': 1, 'devhouse-shower': 1, 'devhouse-basin': 1, 'devhouse-toilet': 2 },
            DevhouseOsaka4F: { 'devhouse-rock': 1, 'devhouse-shrub': 4, 'devhouse-lantern': 1, 'devhouse-garden-seat': 2, 'devhouse-water-bowl': 1,
                'devhouse-fence': 9, 'home-bed': 3, 'devhouse-basin': 1, 'devhouse-clothes-rack': 1 },
        };
        for (const [k, plan] of Object.entries(PLAN)) {
            for (const [sprite, n] of Object.entries(plan)) assert.strictEqual(count(k, sprite), n, `${k}: ${sprite}`);
        }
        // Tokyo 1F and 2F: the stairs, a locked door on the wall, a plant by the mat, and nothing else at all
        const things = (k) => {
            const n = {};
            for (const l of c.rooms[k].layers) {
                for (const id of Object.values(l.tiles)) {
                    const name = c.tilePalette[id].replace(/_0_0$/, '');
                    if (!/^(office-void|gk_blank|home-wood-floor|home-wall-sand)/.test(name)) n[name] = (n[name] || 0) + 1;
                }
            }
            return n;
        };
        assert.deepStrictEqual(things('DevhouseTokyo1F'), { 'home-genkan': 1, 'home-doormat': 1, 'devhouse-stairs-up': 1, 'devhouse-door': 1, 'home-plant': 1 });
        assert.deepStrictEqual(things('DevhouseTokyo2F'), { 'devhouse-stairs-down': 1, 'devhouse-stairs-up': 1, 'devhouse-door': 1, 'devhouse-stairwell': 1 });
        const stood = (k) => Object.keys(tiles(c.rooms[k], 'Floor')).filter((cell) => free(c, k, ...cell.split(',').map(Number))).length;
        assert.deepStrictEqual([stood('DevhouseTokyo1F'), stood('DevhouseTokyo2F')], [9, 8], 'a stair hall two cells wide, the mat and the stairs');
        // what lies on what: futons and Osaka's beds on tatami, Tokyo's top-floor beds end to end down the west wall
        const floorAt = (k, [x, y]) => c.tilePalette[tiles(c.rooms[k], 'Floor')[`${x},${y}`]];
        for (const sprite of ['home-futon-blue', 'home-futon-rose']) {
            for (const cell of at(c.rooms.DevhouseTokyo5F, c, sprite)) assert.ok(/^home-tatami-green_/.test(floorAt('DevhouseTokyo5F', cell)), `futon ${cell}`);
        }
        for (const k of ['DevhouseOsaka2F', 'DevhouseOsaka4F']) {
            for (const cell of at(c.rooms[k], c, 'home-bed')) assert.ok(/^home-tatami-green_/.test(floorAt(k, cell)), `${k} bed ${cell}`);
        }
        const rooms2F = at(c.rooms.DevhouseOsaka2F, c, 'home-bed').sort((a, b) => a[1] - b[1]);
        assert.ok(at(c.rooms.DevhouseOsaka2F, c, 'devhouse-wall-h').some(([, y]) => y > rooms2F[0][1] && y < rooms2F[1][1]), 'a wall between Osaka 2F\'s two bedrooms');
        assert.deepStrictEqual(at(c.rooms.DevhouseTokyo6F, c, 'home-bed').sort((a, b) => a[1] - b[1]), [[3, 4], [3, 6]]);
        // the wet rooms are tiled: the bath, the showers and the toilets stand on tile
        for (const k of ALL) {
            for (const sprite of ['devhouse-bath', 'devhouse-shower', 'devhouse-toilet']) {
                for (const cell of at(c.rooms[k], c, sprite)) assert.strictEqual(floorAt(k, cell), 'devhouse-tile_0_0', `${k} ${sprite} ${cell}`);
            }
        }
    });

    test('the top of Osaka\'s Devhouse is a tatami room that opens onto a zen garden on the roof: gravel, stepping stones, a fence for a wall, and a night (#69)', () => {
        const c = cfg(), k = 'DevhouseOsaka4F', room = c.rooms[k], floor = tiles(room, 'Floor'), solid = tiles(room, 'Colliders');
        // the garden: the top four rows of the floor, nine cells wide
        const stones = [];
        for (let y = 4; y <= 7; y++) {
            for (let x = 5; x <= 13; x++) {
                const name = c.tilePalette[floor[`${x},${y}`]];
                assert.ok(name === 'devhouse-gravel_0_0' || name === 'devhouse-stepping-stone_0_0', `garden ${x},${y}: ${name}`);
                if (name === 'devhouse-stepping-stone_0_0') stones.push([x, y]);
            }
        }
        assert.strictEqual(stones.length, 9);
        for (const [x, y] of stones) assert.ok(!(`${x},${y}` in solid), `a stepping stone is stepped on: ${x},${y}`);
        assert.ok(!Object.entries(floor).some(([cell, id]) => /^devhouse-(gravel|stepping-stone)/.test(c.tilePalette[id]) && Number(cell.split(',')[1]) > 7), 'no gravel indoors');
        // its back wall is the garden fence, all nine columns of it, and no indoor wall piece
        assert.deepStrictEqual(at(room, c, 'devhouse-fence').sort((a, b) => a[0] - b[0]), Array.from({ length: 9 }, (_, i) => [5 + i, 2]));
        assert.ok(!room.layers.some((l) => Object.values(l.tiles).some((id) => /^home-wall-/.test(c.tilePalette[id]))));
        // a wall with one opening divides it from the tatami room, where the beds and the stair down are
        const gap = [];
        for (let x = 5; x <= 13; x++) if (!(`${x},8` in solid)) gap.push(x);
        assert.deepStrictEqual(gap, [6], 'one way out to the garden');
        const { world } = worldWith(false);
        const down = room.transporters[0];
        world.enter(k, down.gridX, down.gridY + 1);
        assert.deepStrictEqual([world.here().x, world.here().y], [13, 13], 'beside the stair down');
        const seen = world.reachable();
        for (const [x, y] of stones) assert.ok(seen.has(`${x},${y}`), `stone ${x},${y} is reached from the stair`);
        // the lantern, the bowl and the seats are in the garden, and you can stand beside each
        for (const sprite of ['devhouse-lantern', 'devhouse-water-bowl', 'devhouse-garden-seat', 'devhouse-rock']) {
            for (const [x, y] of at(room, c, sprite)) {
                assert.ok(y >= 4 && y <= 7 && `${x},${y}` in solid, `${sprite} ${x},${y}`);
                assert.ok(Object.values(DIRS).some(([dx, dy]) => seen.has(`${x + dx},${y + dy}`)), `${sprite} ${x},${y} is walked up to`);
            }
        }
        // it is the one floor with a night: it dims (DayNight) and its stone lantern is a light (Glows)
        assert.deepStrictEqual(ALL.filter((r) => c.rooms[r].lanternLight), [k]);
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        const spots = game('Glows').spotsFor('devhouse-lantern_0_0', c.spriteMetadata['devhouse-lantern_0_0']);
        assert.ok(spots.length === 1 && Number.isInteger(spots[0].color) && spots[0].r <= 2.5, JSON.stringify(spots));
    });

    test('what you can bump in a Devhouse says one dry line: the locked door, the bath, the washer, the goldfish, the bunk - not the chairs or the tables (#69)', () => {
        const I = game('Interactions');
        const hit = (sprite) => plain(I.match(sprite, { interior: true, shopEnabled: false, devhouse: { host: 'Park', floor: 3 } }));
        const kinds = { 'devhouse-door_0_0': 'locked-door', 'devhouse-bath_0_0': 'bath', 'devhouse-washer_0_0': 'washer',
            'devhouse-water-bowl_0_0': 'goldfish', 'devhouse-bunk_0_0': 'bunk' };
        const said = [];
        for (const [sprite, kind] of Object.entries(kinds)) {
            const rule = hit(sprite);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint === true, sprite);
            // the house voice: lowercase, one line, short enough for a toast
            assert.ok(rule.say && rule.say.length <= 100 && rule.say === rule.say.toLowerCase() && !/\n/.test(rule.say), rule.say);
            said.push(rule.say);
        }
        assert.strictEqual(new Set(said).size, said.length);
        // twenty chairs ring the tables you walk round: a line on each would toast again and again
        for (const sprite of ['devhouse-chair-n_0_0', 'devhouse-chair-s_0_0', 'devhouse-chair-e_0_0', 'devhouse-chair-w_0_0', 'devhouse-stool_0_0',
            'devhouse-table-wide_0_0', 'devhouse-table-tall_0_0', 'devhouse-table-small_0_0', 'devhouse-stairwell_0_0', 'devhouse-wall-h_0_0',
            'devhouse-tokyo_0_0', 'devhouse-osaka_0_0']) assert.strictEqual(hit(sprite), null, sprite);
        // on the floors themselves: the locked door on Tokyo's ground floor is what you bump there, and nothing is a shop
        const { world } = worldWith(false);
        const seen = {};
        for (const k of ALL) {
            world.enter(k, 0, 0);
            const all = world.interactions();
            assert.ok(all.every((i) => i.group === 'flavour'), `${k}: ${plain(all.map((i) => i.group))}`);
            seen[k] = plain(all.map((i) => i.kind)).sort();
        }
        assert.deepStrictEqual(seen.DevhouseTokyo1F, ['locked-door']);
        assert.deepStrictEqual(seen.DevhouseTokyo2F, ['locked-door']);
        assert.ok(seen.DevhouseTokyo5F.includes('bath') && seen.DevhouseTokyo5F.includes('locked-door'));
        assert.ok(seen.DevhouseTokyo4F.includes('bunk') && seen.DevhouseTokyo6F.includes('washer') && seen.DevhouseOsaka3F.includes('washer'));
        assert.ok(seen.DevhouseOsaka4F.includes('goldfish'));
    });

    test('a Devhouse floor is "Devhouse 3F" on a phone\'s bar, beside the countdown, and the map knows which city every floor is in (#69)', () => {
        const c = cfg(), hudName = game('hudName'), hudBrief = game('hudBrief');
        const names = ALL.map((k) => c.rooms[k].name);
        assert.strictEqual(new Set(names).size, names.length);
        for (const [city] of Object.entries(HOUSES)) {
            for (const n of floors(city)) {
                const name = c.rooms[key(city, n)].name;
                assert.strictEqual(hudName(name), `Devhouse ${n}F | ${city}`);
                // hud-phone-layout.test.js's rule: a short form of 11 characters or fewer leaves room for
                // "devhouse 3 soon" on the one-row bar at 667x375, so the floor is always on the bar
                const brief = hudBrief(hudName(name));
                assert.strictEqual(brief, `Devhouse ${n}F`);
                assert.ok(brief.length <= 11);
                assert.ok(10 + 16 * `${brief} | devhouse 3 soon | ¥5,000`.length + 10 + 64 + 10 <= 715);
            }
        }
        // six stairs and a street door from the district: Places.of follows that many doors
        if (!game('typeof Places !== "undefined"')) vm.runInContext(src('utils/Places.js'), ctx, { filename: 'Places.js' });
        const P = game('Places'), config = game('decodeConfig')(c);
        for (const [city, h] of Object.entries(HOUSES)) {
            for (const n of floors(city)) assert.strictEqual(P.of(config, key(city, n)), h.place, key(city, n));
        }
        // the name already says the city: "you are here" does not say it twice
        assert.strictEqual(P.whereText(config, 'DevhouseTokyo6F'), 'Devhouse 6F · Tokyo');
        assert.strictEqual(P.whereText(config, 'DevhouseOsaka4F'), 'Devhouse 4F · Osaka');
    });

    test('the Devhouse generator and its art tool are checked, own the street door through roomgen, and no other generator knows the rooms (#69)', () => {
        const check = tool('check_generators.py');
        for (const name of ['generate_devhouses', 'generate_devhouse_art']) assert.ok(check.includes(`'${name}'`), name);
        const rg = tool('roomgen.py'), gen = tool('generate_devhouses.py');
        assert.ok(/DEVHOUSE_PREFIX: \('devhouse', DEVHOUSE_DOORS\)/.test(rg), 'OWNED_DOORS');
        assert.ok(/DEVHOUSE_DOORS = \{'devhouse-tokyo_0_0': \[\(3, 7\)\], 'devhouse-osaka_0_0': \[\(1, 6\)\]\}/.test(rg));
        assert.ok(/rg\.DEVHOUSE_DOORS/.test(gen) && /rg\.DEVHOUSE_PREFIX/.test(gen), 'the generator has no door cells or room prefix of its own');
        assert.ok(gen.indexOf('rg.cli(__doc__') < gen.indexOf('rg.load_config()'), '--help runs nothing');
        // the town generator stamps the building and says nothing of what is inside it
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !/^generate_devhouse/.test(n))) {
            assert.ok(!/Devhouse[A-Z]|DEVHOUSE_/.test(tool(f)), f);
        }
        assert.ok(/b\.stamp\('devhouse-osaka', 9, 10\)/.test(tool('generate_osaka.py')));
        const c = cfg();
        // the palette was appended to: every Devhouse sprite is in it once, after everything that was there before
        const mine = c.tilePalette.map((k, i) => [k, i]).filter(([k]) => k.startsWith('devhouse-'));
        assert.ok(mine.length === 37 && new Set(mine.map(([k]) => k)).size === mine.length, `${mine.length} devhouse sprites`);
        assert.ok(mine[0][1] > c.tilePalette.indexOf('konbini-gondola-snacks_0_0'));
        assert.deepStrictEqual(mine.map(([, i]) => i), mine.map((_, n) => mine[0][1] + n), 'one run of new slots at the end');
        // every sprite the art tool draws is on disk at a whole number of cells, has its name, and is placed
        const png = need(path.join(GV2, 'tools', 'png'));
        const used = new Set(Object.values(c.rooms).flatMap((r) => (r.layers || []).flatMap((l) => Object.values(l.tiles))).map((id) => c.tilePalette[id]));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith('devhouse-'));
        assert.deepStrictEqual(keys.sort(), mine.map(([k]) => k).sort());
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
            assert.ok(c.tileNames[k] && used.has(k), `${k} is drawn but not named or not placed`);
        }
        for (const prefab of ['devhouse-tokyo', 'devhouse-osaka']) assert.ok(fs.existsSync(path.join(GV2, 'tiled', 'prefabs', prefab + '.tmj')), prefab);
        // roomgen keeps the street door of each house and is not asked to keep a stair
        const asked = python(['-c', [
            'import json, sys', "sys.path.insert(0, 'tools')", 'import roomgen as rg', 'cfg = rg.load_config()',
            "print(json.dumps({k: [[t['gridX'], t['gridY'], rg.owned_door(cfg, t) is not None] for t in r.get('transporters', [])",
            "    if t['targetRoom'].startswith(rg.DEVHOUSE_PREFIX)] for k, r in cfg['rooms'].items()}))"].join('\n')]);
        assert.strictEqual(asked.status, 0, asked.stderr);
        const kept = Object.entries(JSON.parse(asked.stdout)).flatMap(([k, list]) => list.filter(([, , own]) => own).map(([x, y]) => `${k} ${x},${y}`));
        assert.deepStrictEqual(kept.sort(), ['Osaka 10,16', 'Park 13,16']);
    });

    test('rebuilding Osaka keeps the Devhouse door, and a re-run of the Devhouse generator changes nothing - nor from a sealed house (#69)', () => {
        scratch((tmp, read) => {
            const before = read();
            const run = python(['tools/generate_devhouses.py'], tmp);
            assert.strictEqual(run.status, 0, run.stderr);
            assert.ok(read() === before, 'generate_devhouses.py changed config.json on a re-run');
            // the town generator rebuilds Osaka from nothing: the building is stamped sealed and the door comes back
            const town = python(['tools/generate_osaka.py'], tmp);
            assert.strictEqual(town.status, 0, town.stderr);
            assert.ok(read() === before, 'generate_osaka.py changed config.json: the Devhouse door was not kept');
            // ...and with both houses sealed and their floors gone, the generator builds the same world
            const sealed = JSON.parse(before), blank = sealed.tilePalette.indexOf('gk_blank');
            for (const h of Object.values(HOUSES)) {
                const host = sealed.rooms[h.host];
                tiles(host, 'Colliders')[h.door.join(',')] = blank;
                host.transporters = host.transporters.filter((t) => !/^Devhouse/.test(t.targetRoom));
            }
            for (const k of ALL) delete sealed.rooms[k];
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(sealed, null, 2));
            const again = python(['tools/generate_devhouses.py'], tmp);
            assert.strictEqual(again.status, 0, again.stderr);
            assert.deepStrictEqual(JSON.parse(read()), JSON.parse(before));
            // --help says how to run it and runs nothing
            fs.writeFileSync(path.join(tmp, 'config.json'), before);
            const help = python(['tools/generate_devhouses.py', '--help'], tmp);
            assert.ok(help.status === 0 && /THE HELD-KEY RULE/.test(help.stdout) && read() === before);
        });
    });
};
