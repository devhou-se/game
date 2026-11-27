// What the interiors of issue #217 have in common (pub.test.js, distillery.test.js, mall.test.js): a building
// that is one sprite on its town's map, a door found from where that sprite stands, a room of its own behind
// it. Not a test file (the runner loads *.test.js): each of the three asks for these checks by name.
//
// No host coordinate is written down here or in those files: the door, the cell in front of it and the cell
// the blog pipeline stands a visitor on all come from the sprite's own cell, so a rebuild of the town may
// move the building without an edit to the tests.
//   spec = { HOST, KEY, NAME, MARK (the room's marker), SPRITE (the building), DOORS ([dx, dy] of each door
//            cell from the sprite's cell), STAND ([dx, dy] of blog_to_npc.LANDMARKS' cell), PREFIX (sprites),
//            BEHIND (how many of the sprite's top rows are roof you walk behind and were never solid; 0) }
module.exports = ({ assert, fs, path, vm, GV2, ctx, game }, spec) => {
    const { HOST, KEY, MARK, SPRITE, DOORS, STAND, PREFIX } = spec;
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    const K = (x, y) => `${x},${y}`;
    // where every copy of a sprite stands in a room: [[x, y], ...] (config.json as it is on disk, or decoded)
    const placed = (room, c, key) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => (typeof id === 'number' ? c.tilePalette[id] : id) === key).map(([cell]) => cell.split(',').map(Number));
    const at = (room, c, piece) => placed(room, c, `${PREFIX}${piece}_0_0`);
    const one = (room, c, piece) => { const all = at(room, c, piece); assert.strictEqual(all.length, 1, piece); return all[0]; };
    const size = (c, key) => { const m = c.spriteMetadata[key]; return [Math.round(0.5 / m.anchorX), Math.round(0.5 / m.anchorY)]; };

    /** The building on the street: its sprite's cell, its door cells, the cell in front of each, the visitor's cell. */
    const outside = (c) => {
        const all = placed(c.rooms[HOST], c, SPRITE);
        assert.strictEqual(all.length, 1, `${HOST} has one ${SPRITE}`);
        const [sx, sy] = all[0];
        const doors = DOORS.map(([dx, dy]) => [sx + dx, sy + dy]);
        return { sprite: [sx, sy], doors, fronts: doors.map(([x, y]) => [x, y + 1]), stand: [sx + STAND[0], sy + STAND[1]] };
    };

    /** The floor of the room: every cell inside its outline, less the doorway's row. */
    const floor = (room) => {
        const xs = room.boundary.map(([x]) => x), ys = room.boundary.map(([, y]) => y);
        const mats = room.transporters.map((t) => t.gridY);
        const cells = [];
        for (let x = Math.min(...xs); x < Math.max(...xs); x++) for (let y = Math.min(...ys); y < Math.min(...mats); y++) cells.push([x, y]);
        return cells;
    };

    /** Every floor cell you can walk to from where you arrive: a flood fill of the room's own colliders. */
    const reach = (c) => {
        const room = c.rooms[KEY], solid = tiles(room, 'Colliders'), open = new Set(floor(room).map(([x, y]) => K(x, y)));
        const [door] = c.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY);
        const seen = new Set([K(door.targetX, door.targetY)]), todo = [[door.targetX, door.targetY]];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                const k = K(nx, ny);
                if (seen.has(k) || !open.has(k) || k in solid) continue;
                seen.add(k);
                todo.push([nx, ny]);
            }
        }
        return { seen, open, solid };
    };

    /** The doors are where the sprite puts them, open, hidden, and lead to free floor; the mats lead back out in front of them. */
    const doorsOpen = (c) => {
        const host = c.rooms[HOST], room = c.rooms[KEY], solid = tiles(host, 'Colliders');
        const { sprite, doors, fronts } = outside(c);
        const ways = host.transporters.filter((t) => t.targetRoom === KEY);
        assert.deepStrictEqual(ways.map((t) => [t.gridX, t.gridY, t.hidden]), doors.map(([x, y]) => [x, y, true]));
        assert.deepStrictEqual(room[MARK], { doors, host: HOST });
        const inside = tiles(room, 'Colliders'), mats = room.transporters;
        doors.forEach(([x, y], i) => {
            assert.ok(!(K(x, y) in solid) && !(K(...fronts[i]) in solid), `door ${x},${y} or the cell in front of it is solid`);
            const t = ways[i];
            assert.ok(!(K(t.targetX, t.targetY) in inside), 'you arrive on free floor');
            assert.ok(!mats.some((m) => m.gridX === t.targetX && m.gridY === t.targetY), '...and not on an exit');
            assert.ok(mats.some((m) => m.gridX === t.targetX && m.gridY === t.targetY + 1), '...with the mat behind you');
        });
        // every mat leads to the cell in front of a door; a mat for each door, in order, where there are as many
        for (const m of mats) {
            assert.deepStrictEqual([m.targetRoom, m.hidden], [HOST, true]);
            assert.ok(fronts.some(([x, y]) => x === m.targetX && y === m.targetY), `mat ${m.gridX},${m.gridY} leads to ${m.targetX},${m.targetY}`);
        }
        if (mats.length === doors.length) assert.deepStrictEqual(mats.map((m) => [m.targetX, m.targetY]), fronts);
        // the rest of the building is as shut as it was: of its whole footprint (below any roof that is
        // walked behind), only the door cells are open
        const [w, h] = size(c, SPRITE), open = [];
        for (let y = sprite[1] + (spec.BEHIND || 0); y < sprite[1] + h; y++) for (let x = sprite[0]; x < sprite[0] + w; x++) if (!(K(x, y) in solid)) open.push([x, y]);
        assert.deepStrictEqual(open, doors, 'only the door is open');
        // and no other room has a way in
        assert.deepStrictEqual(Object.entries(c.rooms).filter(([, r]) => (r.transporters || []).some((t) => t.targetRoom === KEY)).map(([k]) => k), [HOST]);
        return { doors, fronts, ways, mats };
    };

    /** Nobody is put on a door or in front of one on any date, no wanderer steps there, and the landmark's visitor keeps their cell. */
    const nobodyInTheWay = (c) => {
        const host = c.rooms[HOST], { doors, fronts, stand } = outside(c);
        const cells = doors.concat(fronts).map(([x, y]) => K(x, y));
        const inWay = host.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
            .filter(([, s]) => cells.includes(K(s.gridX, s.gridY))).map(([date]) => `${n.name} ${date}`));
        assert.deepStrictEqual(inWay, []);
        // a wanderer keeps off a doorway and the cells beside it (NPCManager.atDoorway)
        const mgr = game('Object.create(NPCManager.prototype)');
        mgr.scene = { roomManager: { currentRoom: 'here', rooms: { here: host } } };
        for (const cell of cells) assert.ok(mgr.atDoorway(...cell.split(',').map(Number)), `a wanderer may stand on ${cell}`);
        // the cell the blog pipeline stands a visitor on is beside the door, not in it, and nothing is built on it
        assert.ok(!cells.includes(K(...stand)) && !(K(...stand) in tiles(host, 'Colliders')), `the stand ${stand}`);
        for (const d of (c.districts || {})[HOST] || []) assert.ok(!cells.includes(d.stand.join(',')), d.name);
        const row = new RegExp(`\\('${SPRITE.replace(/_0_0$/, '_')}', '[^']+', \\(${STAND[0]}, ${STAND[1]}\\), \\{'rooms': \\('${HOST}',\\)\\}\\)`);
        assert.ok(row.test(tool('blog_to_npc.py')), `LANDMARKS has no ${SPRITE} row standing at +${STAND}`);
        return { cells, stand };
    };

    /**
     * Walk in by each door on `date`, reach and bump everything there is to bump (`kinds`, sorted), and
     * leave by the mat behind you: you are back in front of the door you came in by.
     */
    const walkThrough = (world, config, date, kinds, says) => {
        const { doors, fronts } = outside(config);
        const mats = config.rooms[KEY].transporters;
        world.date = date;
        doors.forEach(([dx, dy], n) => {
            world.enter(HOST, fronts[n][0], fronts[n][1] + 1);                      // the street, a step back from the door
            assert.ok(!world.step('n').transported, 'up to the door');
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, KEY, `door ${n}`);
            const start = world.here();
            const things = world.interactions();
            assert.deepStrictEqual(plain(things.map((i) => i.kind).sort()), kinds);
            for (const i of things) {
                // from below it, or (what stands against a side wall) from beside its foot
                const foot = i.y + i.h - 1, sides = [];
                for (let x = i.x; x < i.x + i.w; x++) sides.push([x, foot + 1, x, foot]);
                sides.push([i.x - 1, foot, i.x, foot], [i.x + i.w, foot, i.x + i.w - 1, foot]);
                const side = sides.find(([x, y]) => world.path(x, y));
                assert.ok(side, `no way to the ${i.kind} at ${i.x},${i.y}`);
                for (const dir of world.path(side[0], side[1])) world.step(dir);
                assert.deepStrictEqual([world.here().x, world.here().y], [side[0], side[1]]);
                const bump = world.interactionAt(side[2], side[3]);
                assert.strictEqual(bump && bump.kind, i.kind);
                assert.ok(says.test(world.describe(bump)), world.describe(bump));
            }
            for (const dir of world.path(start.x, start.y)) world.step(dir);
            const out = world.step('s');
            assert.strictEqual(out.transported && out.transported.to, HOST);
            assert.deepStrictEqual([world.here().x, world.here().y], fronts[n], 'out in front of the door you went in by');
            assert.ok(mats.some((m) => m.gridX === start.x && m.gridY === start.y + 1));
        });
        const lint = world.lint(KEY), town = world.lint(HOST);
        assert.deepStrictEqual(plain([lint.errors, lint.warns, town.errors]), [{}, {}, {}], 'lint');
    };

    /** The name on the HUD bar fits a phone's one row beside the countdown, and the map says which town it is in. */
    const named = (c, where) => {
        const NAME = spec.NAME;
        assert.strictEqual(c.rooms[KEY].name, NAME);
        assert.ok(!Object.entries(c.rooms).some(([k, r]) => k !== KEY && r.name === NAME), 'no other room has the name');
        // hud-phone-layout.test.js's rule: a name of 11 characters or fewer leaves room for "devhouse 3 soon"
        assert.ok(NAME.length <= 11);
        assert.strictEqual(game('hudBrief')(NAME), NAME);
        if (!game('typeof Places !== "undefined"')) vm.runInContext(src('utils/Places.js'), ctx, { filename: 'Places.js' });
        assert.strictEqual(game('Places').whereText(game('decodeConfig')(c), KEY), where);
    };

    /** A sprite's night spots (src/utils/Glows.js), checked to be drawable. */
    const glow = (c, piece) => {
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        const spots = plain(game('Glows').spotsFor(`${PREFIX}${piece}_0_0`, c.spriteMetadata[`${PREFIX}${piece}_0_0`]));
        assert.ok(spots.length >= 1 && spots.every((s) => Number.isInteger(s.color) && s.r <= 2.5), piece);
        return spots;
    };

    /**
     * The generator and its art tool are checked, the door is roomgen's to keep, the palette was appended
     * to, every sprite is on disk and placed, and the generator is a no-op on a re-run and rebuilds the
     * same world from a sealed building. (`after`: a sprite the palette already held before this room.)
     */
    const plumbing = ({ generator, art, owned, table, after, sprites }) => {
        const check = tool('check_generators.py');
        for (const name of [generator, art]) assert.ok(check.includes(`'${name}'`), name);
        assert.ok(check.indexOf(`'${generator}'`) > check.indexOf("'generate_temple'") && check.indexOf(`'${generator}'`) < check.indexOf("GENERATORS += ['districts']"),
            'after the town generators, before the districts');
        const rg = tool('roomgen.py');
        assert.ok(rg.includes(owned) && rg.includes(table), 'OWNED_DOORS');
        // ...and it is put together from the shared blocks (#224): the Interior shell, the door found by sprite
        // and wired by roomgen.open_door, which is the one way a door is wired
        const gen = tool(`${generator}.py`);
        for (const block of ['from interiors import Interior', 'rg.sprite_doors(', 'rg.open_door(']) assert.ok(gen.includes(block), `${generator}.py: ${block}`);
        assert.ok(!rg.includes('def open_doors('), 'roomgen has a second way to wire a door');
        const own =new RegExp(`^${generator}(_art)?\\.py$`);
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !own.test(n))) {
            assert.ok(!tool(f).includes(KEY) && !tool(f).includes(`'${PREFIX}`), f);
        }
        const c = cfg();
        const mine = c.tilePalette.map((k, i) => [k, i]).filter(([k]) => k.startsWith(PREFIX));
        assert.ok(mine.length >= sprites && new Set(mine.map(([k]) => k)).size === mine.length);
        assert.ok(mine[0][1] > c.tilePalette.indexOf(after), 'appended');
        const png = require(path.join(GV2, 'tools', 'png'));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith(PREFIX));
        assert.ok(keys.length >= sprites, `${keys.length} sprites`);
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
            assert.ok(mine.some(([name]) => name === k), `${k} is drawn but not placed`);
        }
        const { spawnSync } = require('child_process');
        const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), `gamev2-${MARK}-`));
        const run = () => spawnSync('python3', [`tools/${generator}.py`], { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26,
            env: Object.assign({}, process.env, { PYTHONDONTWRITEBYTECODE: '1' }) });
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            const before = fs.readFileSync(path.join(tmp, 'config.json'), 'utf8');
            const first = run();
            assert.strictEqual(first.status, 0, first.stderr);
            assert.ok(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8') === before, `${generator}.py changed config.json on a re-run`);
            // ...and from a sealed building it builds the same world: seal the door, drop the room, run it
            const sealed = JSON.parse(before), host = sealed.rooms[HOST];
            const blank = sealed.tilePalette.indexOf('gk_blank');
            for (const t of host.transporters.filter((x) => x.targetRoom === KEY)) tiles(host, 'Colliders')[K(t.gridX, t.gridY)] = blank;
            host.transporters = host.transporters.filter((x) => x.targetRoom !== KEY);
            delete sealed.rooms[KEY];
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(sealed, null, 2));
            const again = run();
            assert.strictEqual(again.status, 0, again.stderr);
            // (the door is wired back at the end of the town's list: the same doors, whatever their order)
            const world = (text) => {
                const w = JSON.parse(text);
                w.rooms[HOST].transporters.sort((a, b) => K(a.targetRoom, K(a.gridX, a.gridY)).localeCompare(K(b.targetRoom, K(b.gridX, b.gridY))));
                return w;
            };
            assert.deepStrictEqual(world(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8')), world(before));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };

    return { cfg, tiles, plain, src, tool, K, placed, at, one, size, outside, floor, reach, doorsOpen, nobodyInTheWay, walkThrough, named, glow, plumbing };
};
