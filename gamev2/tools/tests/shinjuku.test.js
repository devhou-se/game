// Shinjuku, the street of high-rises (issue #94): a fifth district of the stitched TokyoCity, west of the
// Palace/Park west road, where that road's junction carries on as an avenue of nine towers. It is data
// tools/generate_shinjuku.py writes (and generate_houses.py --lobbies Shinjuku, sync_cities.py, districts.py).
module.exports = ({ test, assert, fs, path, GV2, worldWith }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const room = cfg.rooms.Shinjuku;
    const layer = (n, r = room) => ((r.layers.find((l) => l.name === n) || {}).tiles) || {};
    const size = (r) => [r.worldWidth / 64, r.worldHeight / 64];
    const [W, H] = size(room);
    const solid = (x, y, r = room) => `${x},${y}` in layer('Colliders', r);
    const floor = (x, y, r = room) => name(layer('Floor', r)[`${x},${y}`]);
    const open = (x, y, r = room) => !!floor(x, y, r) && !solid(x, y, r);
    const at = (key) => Object.entries(layer('Collidables')).filter(([, t]) => name(t) === key).map(([xy]) => xy.split(',').map(Number));
    const doorAt = (x, y, r = room) => r.transporters.find((t) => t.gridX === x && t.gridY === y);
    const prefab = (key) => {
        const p = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', key + '.tmj'), 'utf8'));
        const doors = p.layers.find((l) => l.name === 'Meta').objects.map((o) => [Math.floor(o.x / 64), Math.floor(o.y / 64)]);
        return { w: p.width, h: p.height, doors };
    };
    const KERB = W - 1, AVE = [14, 15, 16];
    // the towers: the prefab and its top-left cell, in the order their lobbies are numbered (north row, then south)
    const TOWERS = [['highrise-apartment', 4, 4], ['highrise-glass', 10, 2], ['highrise-blue', 15, 1], ['highrise-yellow', 21, 4],
        ['midrise-apartment', 26, 6], ['highrise-blue', 5, 19], ['highrise-glass', 12, 20], ['highrise-apartment', 18, 22],
        ['highrise-yellow', 25, 22]];
    const lobbyDoors = () => TOWERS.map(([key, x, y], i) => ({ lobby: `LobbyShinjuku${i + 1}`, key, x, y, doors: prefab(key).doors.map(([dx, dy]) => [x + dx, y + dy]) }));

    test('Shinjuku is a fifth district of the stitched Tokyo, in the wood west of the west road, and moves nobody (#94)', () => {
        assert.strictEqual(room.name, 'Shinjuku');
        assert.deepStrictEqual([W, H], [34, 36]);
        const members = cfg.cities.TokyoCity.rooms;
        assert.deepStrictEqual(members[members.length - 1], { room: 'Shinjuku', x: 24, y: 51 }, 'listed last: it owns its own cells');
        // the four ported districts (and Karuizawa) are where they were
        assert.deepStrictEqual(members.slice(0, -1), [{ room: 'Tokyo', x: 0, y: 1 }, { room: 'Market', x: 58, y: 0 },
            { room: 'Palace', x: 58, y: 47 }, { room: 'Park', x: 58, y: 65 }, { room: 'Karuizawa', x: -48, y: 8 }]);
        // devhouse.world places it there too: 64px cells, measured from Palace
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8')).maps;
        const map = (k) => world.find((m) => m.fileName === `gamev2/tiled/${k}.tmj`);
        assert.deepStrictEqual([(map('shinjuku').x - map('palace').x) / 64, (map('shinjuku').y - map('palace').y) / 64], [24 - 58, 51 - 47]);
        assert.deepStrictEqual([map('shinjuku').width, map('shinjuku').height], [room.worldWidth, room.worldHeight]);
        // it overlaps no other district: its east edge is the column beside Palace's and Park's west edge
        const rect = (m) => { const [w, h] = size(cfg.rooms[m.room]); return [m.x, m.y, m.x + w - 1, m.y + h - 1]; };
        const mine = rect(members[members.length - 1]);
        for (const m of members.slice(0, -1)) {
            const r = rect(m);
            assert.ok(r[0] > mine[2] || r[2] < mine[0] || r[1] > mine[3] || r[3] < mine[1], `Shinjuku overlaps ${m.room}`);
        }
        assert.strictEqual(mine[2] + 1, members.find((m) => m.room === 'Palace').x);
        // and the city is no bigger for it
        const { world: model } = worldWith(true);
        const city = model.roomManager.cities.TokyoCity;
        assert.deepStrictEqual([city.width, city.height], [165, 109]);
        assert.deepStrictEqual(city.members.map((m) => m.key), ['Tokyo', 'Market', 'Palace', 'Park', 'Karuizawa', 'Shinjuku']);
    });

    test('Shinjuku\'s last column is the west road\'s kerb, plain road where the avenue leaves the junction (#94)', () => {
        // the kerb the city's backdrop drew in the wood until now (cities.TokyoCity.backdrop.edges): part of the road, so open
        const kerb = cfg.cities.TokyoCity.backdrop.edges.find((e) => /plain/.test(e.beside)).tile;
        assert.strictEqual(kerb, 'road-edge-left_0_0');
        for (let y = 0; y < H; y++) {
            assert.strictEqual(floor(KERB, y), AVE.includes(y) ? 'road-plain_0_0' : kerb, `column ${KERB}, row ${y}`);
            assert.ok(open(KERB, y), `column ${KERB}, row ${y} is solid`);
        }
        // the avenue is the Palace/Park road carried on: the same three rows of the city, asphalt from the kerb to its west end
        const members = cfg.cities.TokyoCity.rooms, off = (k) => members.find((m) => m.room === k);
        assert.deepStrictEqual(AVE.map((y) => y + off('Shinjuku').y - off('Palace').y), [18, 19, 20]);
        for (const y of AVE) for (let x = 4; x < KERB; x++) assert.ok(/^road-|^crossing-/.test(floor(x, y)) && open(x, y), `${x},${y} is ${floor(x, y)}`);
        // it ends at a kerb, with pavement round the end: a road that leaves a junction leads somewhere, the bus bay
        assert.deepStrictEqual(AVE.map((y) => floor(4, y)), ['road-corner-nw_0_0', 'road-edge-left_0_0', 'road-corner-sw_0_0']);
        for (const y of AVE) for (const x of [2, 3]) assert.ok(/^flat-grey-brick-autotile/.test(floor(x, y)) && open(x, y), `${x},${y}`);
        assert.deepStrictEqual(at('bus-stop_0_0'), [[4, 17]]);
        // no track tile: the city's backdrop would run a railway out into the wood from one (cities.backdrop.extend)
        const extend = new RegExp(cfg.cities.TokyoCity.backdrop.extend);
        for (const l of room.layers) for (const [xy, t] of Object.entries(l.tiles)) {
            assert.ok(!extend.test(name(t)), `${name(t)} at ${xy}`);
            assert.ok(!/rubbish-bin/.test(name(t)), `a rubbish bin at ${xy}`);
        }
    });

    test('the avenue has a zebra crossing under two signals, one on each pavement (#94)', () => {
        assert.deepStrictEqual(Object.entries(layer('Over Floor')).filter(([, t]) => /^crossing-h/.test(name(t))).map(([xy]) => xy).sort(),
            ['22,14', '22,15', '22,16', '23,14', '23,15', '23,16']);
        // no centre line under the stripes, nor into the kerb at the avenue's west end (the turning box)
        for (const x of [5, 6, 22, 23]) assert.strictEqual(floor(x, 15), 'road-plain_0_0', `${x},15`);
        // a signal is 1x3 with its base on the bottom cell: the pavement row beside the avenue, clear of the zebra
        const feet = at('traffic-light_0_0').map(([x, y]) => [x, y + 2]).sort((a, b) => a[1] - b[1]);
        assert.deepStrictEqual(feet, [[21, 13], [24, 17]]);
        for (const [x, y] of feet) assert.ok(solid(x, y) && /^flat-grey-brick-autotile/.test(floor(x, y)), `${x},${y}`);
        // you can walk across it, pavement to pavement
        for (const x of [22, 23]) for (let y = 13; y <= 17; y++) assert.ok(open(x, y), `${x},${y}`);
    });

    test('Shinjuku and Palace have each other\'s seam: three hidden transporters each way, onto open road (#94)', () => {
        const palace = cfg.rooms.Palace;
        const out = room.transporters.filter((t) => t.targetRoom === 'Palace'), back = palace.transporters.filter((t) => t.targetRoom === 'Shinjuku');
        assert.deepStrictEqual(out, AVE.map((y, i) => ({ gridX: KERB, gridY: y, hidden: true, targetRoom: 'Palace', targetX: 3, targetY: 18 + i })));
        assert.deepStrictEqual(back, AVE.map((y, i) => ({ gridX: 0, gridY: 18 + i, hidden: true, targetRoom: 'Shinjuku', targetX: KERB - 3, targetY: y })));
        for (const t of out) assert.ok(open(t.gridX, t.gridY) && open(t.targetX, t.targetY, palace) && !doorAt(t.targetX, t.targetY, palace), JSON.stringify(t));
        for (const t of back) assert.ok(open(t.gridX, t.gridY, palace) && open(t.targetX, t.targetY) && !doorAt(t.targetX, t.targetY), JSON.stringify(t));
        // nothing else leaves the district but its tower doors, and Palace's other doors are untouched in number
        assert.strictEqual(room.transporters.filter((t) => !/^LobbyShinjuku\d$/.test(t.targetRoom)).length, 3);
        // not stitched (?stitch=0), the seam is a teleport both ways
        const legacy = worldWith(false).world;
        legacy.enter('Palace', 1, 19);
        assert.strictEqual(JSON.stringify(legacy.step('w').transported), '{"from":"Palace","to":"Shinjuku"}');
        assert.deepStrictEqual([legacy.here().room, legacy.here().x, legacy.here().y], ['Shinjuku', KERB - 3, 15]);
        assert.ok(legacy.step('e').moved && legacy.step('e').moved);
        assert.strictEqual(JSON.stringify(legacy.step('e').transported), '{"from":"Shinjuku","to":"Palace"}');
        assert.deepStrictEqual([legacy.here().room, legacy.here().x, legacy.here().y], ['Palace', 3, 19]);
    });

    test('nine towers stand on the avenue and the promenade, and every one opens into its own lobby (#94)', () => {
        const towers = lobbyDoors();
        // every tower sprite of the district is one of the nine: none is sealed, none is missing
        const standing = Object.entries(layer('Collidables')).filter(([, t]) => /^(highrise|midrise)-/.test(name(t)))
            .map(([xy, t]) => [name(t).replace('_0_0', ''), ...xy.split(',').map(Number)]);
        const order = (a, b) => (a[2] > 12) - (b[2] > 12) || a[1] - b[1];        // the north row west to east, then the south
        assert.deepStrictEqual(standing.sort(order), TOWERS);
        // the two rows stand on rows 11 and 29: a tower's door row is its bottom row
        assert.deepStrictEqual(TOWERS.map(([key, , y]) => y + prefab(key).h - 1), [11, 11, 11, 11, 11, 29, 29, 29, 29]);
        // all five kinds of tower are here
        assert.deepStrictEqual([...new Set(TOWERS.map(([key]) => key))].sort(),
            ['highrise-apartment', 'highrise-blue', 'highrise-glass', 'highrise-yellow', 'midrise-apartment']);
        for (const { lobby, doors } of towers) {
            const inside = cfg.rooms[lobby];
            assert.ok(inside && inside.lobby && inside.lobby.host === 'Shinjuku', lobby);
            assert.deepStrictEqual(inside.lobby.doors, doors, lobby);
            for (const [x, y] of doors) {
                const t = doorAt(x, y);
                assert.ok(t && t.targetRoom === lobby && t.hidden && !solid(x, y), `${lobby}: no way in at ${x},${y}`);
                assert.ok(/^flat-grey-brick-autotile/.test(floor(x, y + 1)) && open(x, y + 1) && !doorAt(x, y + 1), `${lobby}: no pavement in front of ${x},${y}`);
            }
            // the way out is the pavement cell below the first door
            assert.strictEqual(inside.transporters.length, 1, lobby);
            const mat = inside.transporters[0];
            assert.deepStrictEqual([mat.targetRoom, mat.targetX, mat.targetY], ['Shinjuku', doors[0][0], doors[0][1] + 1], lobby);
        }
        assert.strictEqual(room.transporters.filter((t) => /^Lobby/.test(t.targetRoom)).length, towers.reduce((n, t) => n + t.doors.length, 0));
        assert.deepStrictEqual(Object.keys(cfg.rooms).filter((k) => /^LobbyShinjuku/.test(k)), towers.map((t) => t.lobby));
    });

    test('in the stitched city you walk from the Palace/Park road onto the avenue, into every tower and out again (#94)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        // the junction: the cell west of Palace (0,19) is Shinjuku's kerb column, on the avenue's middle row
        const edge = rm.resolve('Palace', 0, 19);
        const west = rm.localize(edge.x - 1, edge.y);
        assert.deepStrictEqual([west.room, west.x, west.y], ['Shinjuku', KERB, 15]);
        world.enter('Palace', 3, 19);
        assert.strictEqual(world.roomManager.currentRoom, 'TokyoCity');
        const from = world.here().room;
        const crossings = [];
        for (let i = 0; i < 6; i++) {
            const r = world.step('w');
            assert.ok(r.moved && !r.transported, 'walked west, never teleported');
            if (r.crossed) crossings.push(r.crossed.from + '>' + r.crossed.to);
        }
        assert.deepStrictEqual(crossings, [from + '>Shinjuku'], 'one seam, crossed once');
        assert.deepStrictEqual([world.here().room, world.here().x, world.here().y, world.here().city], ['Shinjuku', KERB - 2, 15, 'TokyoCity']);
        // the district lints clean in the city and on its own map, and no open cell of it is cut off
        assert.strictEqual(JSON.stringify(world.lint('Shinjuku').errors), '{}');
        assert.strictEqual(JSON.stringify(world.lint('Shinjuku').warns), '{}');
        const reach = world.reachByRoom(world.survey(null, { npcs: false }).reach).Shinjuku;
        const walkable = [];
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (open(x, y)) walkable.push(`${x},${y}`);
        assert.deepStrictEqual([...reach].sort(), walkable.sort(), 'every open cell of Shinjuku can be walked to');
        // every tower, by each of its doors: up to the pavement in front, in through the door, and back out onto it
        for (const { lobby, doors } of lobbyDoors()) {
            for (const [x, y] of doors) {
                const front = rm.resolve('Shinjuku', x, y + 1);
                const steps = world.path(front.x, front.y);
                assert.ok(steps, `${lobby}: no walk to the pavement in front of ${x},${y}`);
                for (const dir of steps) assert.ok(world.step(dir).moved, `${lobby}: the walk to ${x},${y + 1} stopped`);
                assert.strictEqual(JSON.stringify(world.step('n').transported), JSON.stringify({ from: 'Shinjuku', to: lobby }));
                assert.strictEqual(JSON.stringify(world.step('s').transported), JSON.stringify({ from: lobby, to: 'Shinjuku' }));
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Shinjuku', doors[0][0], doors[0][1] + 1], lobby);
            }
        }
    });

    test('the Shinjuku generator is checked, before the districts are written, and the district is somewhere to stand (#94)', () => {
        const src = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        const listed = src.indexOf("'generate_shinjuku'"), last = src.indexOf("GENERATORS += ['districts']");
        assert.ok(listed > 0 && listed < last, 'tools/check_generators.py does not run generate_shinjuku.py before districts.py');
        assert.strictEqual(cfg.districts.Shinjuku.length, 1);
        const d = cfg.districts.Shinjuku[0];
        assert.deepStrictEqual([d.key, d.name], ['shinjuku', 'Shinjuku']);
        const [x0, y0, x1, y1] = d.bounds, [sx, sy] = d.stand;
        assert.ok(x0 >= 0 && y0 >= 0 && x1 < W && y1 < H && sx >= x0 && sx <= x1 && sy >= y0 && sy <= y1);
        assert.ok(open(sx, sy) && /^flat-grey-brick-autotile/.test(floor(sx, sy)), 'the stand is not on a pavement');
    });
};
