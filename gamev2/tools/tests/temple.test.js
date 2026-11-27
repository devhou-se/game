// A temple's main hall (issue #213, Senso-ji): tools/generate_temple.py, tools/generate_temple_art.py, src/TempleVisit.js.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, shopWith, worldWith }) => {
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    const HOST = 'Market', KEY = 'TempleMarket1', NAME = 'Senso-ji';
    // src/ShrineVisit.js and src/TempleVisit.js are not in the runner's list: load them once, here
    const visit = () => {
        if (!game('typeof ShrineVisit !== "undefined"')) vm.runInContext(src('ShrineVisit.js'), ctx, { filename: 'ShrineVisit.js' });
        if (!game('typeof TempleVisit !== "undefined"')) vm.runInContext(src('TempleVisit.js'), ctx, { filename: 'TempleVisit.js' });
        return game('TempleVisit');
    };
    // where every copy of a piece stands in a room: [[x, y], ...]
    const at = (room, c, piece) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => c.tilePalette[id] === `temple-in-${piece}_0_0`).map(([cell]) => cell.split(',').map(Number));

    test('the temple is the great hall at the head of the stall street, not the shrine: its double door at the top of the steps opens into one main hall (#213)', () => {
        const c = cfg(), host = c.rooms[HOST], solid = tiles(host, 'Colliders');
        const doors = host.transporters.filter((t) => t.targetRoom === KEY);
        assert.deepStrictEqual(doors.map((t) => [t.gridX, t.gridY, t.hidden]), [[27, 15, true], [28, 15, true]]);
        const wall = tiles(host, 'Collidables'), over = tiles(host, 'Over Floor');
        for (const t of doors) {
            // a leaf of the hall's own door, a step below it, and both can be stood on
            assert.strictEqual(c.tilePalette[wall[`${t.gridX},${t.gridY}`]], 'shrine-walls_2_2');
            assert.strictEqual(c.tilePalette[over[`${t.gridX},${t.gridY + 1}`]], 'castle-stairs_0_0');
            assert.ok(!(`${t.gridX},${t.gridY}` in solid) && !(`${t.gridX},${t.gridY + 1}` in solid));
            assert.deepStrictEqual([t.targetX, t.targetY], [t.gridX - 27 + 12, 18], 'in by the leaf you walked through');
        }
        // the rest of the hall's front is sealed as it was: ten cells of wall either side of the two leaves
        const front = [];
        for (let x = 23; x <= 32; x++) if (!(`${x},15` in solid)) front.push(x);
        assert.deepStrictEqual(front, [27, 28]);
        // it stands under the hall's own roof: red-shrine-top-parts over the door, not the shrine prefab's
        const tops = tiles(host, 'Tops');
        assert.ok(/^red-shrine-top-parts_/.test(c.tilePalette[tops['27,14']]) && /^red-shrine-top-parts_/.test(c.tilePalette[tops['28,14']]));
        // the district's shrine is another building, keeps its own door and its own worship hall
        const shrine = host.transporters.filter((t) => t.targetRoom === 'ShrineMarket1');
        assert.deepStrictEqual(shrine.map((t) => [t.gridX, t.gridY]), [[44, 15]]);
        assert.strictEqual(c.tilePalette[wall['43,11']], 'shrine-building_0_0');
        assert.strictEqual(c.rooms.ShrineMarket1.name, 'Shrine · Asakusa');
        assert.ok(!c.rooms.ShrineMarket1.temple && c.rooms.ShrineMarket1.shrine.host === HOST);
        // and the district gained exactly these two doors
        assert.deepStrictEqual(host.transporters.filter((t) => /^(Temple|Shrine|PalaceHall)/.test(t.targetRoom)).map((t) => t.targetRoom), ['ShrineMarket1', KEY, KEY]);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Temple/.test(k)), [KEY], 'Senso-ji only: Zuihoden and the others wait for their city');
    });

    test('nobody stands on the temple door or the step in front of it on any date, and the Senso-ji spot stands its visitor beside the steps (#213)', () => {
        const c = cfg(), host = c.rooms[HOST];
        const cells = host.transporters.filter((t) => t.targetRoom === KEY).flatMap((t) => [`${t.gridX},${t.gridY}`, `${t.gridX},${t.gridY + 1}`]);
        assert.deepStrictEqual(cells, ['27,15', '27,16', '28,15', '28,16']);
        const inWay = host.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
            .filter(([, s]) => cells.includes(`${s.gridX},${s.gridY}`)).map(([date]) => `${n.name} ${date}`));
        assert.deepStrictEqual(inWay, []);
        // Bailey's post of 1 November 2025 is at the foot of the steps, at their west end: not in the doorway
        const bailey = host.npcs.find((n) => n.name === 'Bailey').states['2025-11-01'];
        assert.deepStrictEqual([bailey.gridX, bailey.gridY], [26, 17]);
        assert.ok(!cells.includes('26,17'));
        for (const d of c.districts[HOST]) assert.ok(!cells.includes(d.stand.join(',')), d.name);
        assert.ok(tool('blog_to_npc.py').includes("('castle-stairs', 'Senso-ji temple', (0, 1), {'rooms': ('Market',)})"));
        // the hall is an interior: the pipeline never offers it
        assert.deepStrictEqual([c.rooms[KEY].interior, c.rooms[KEY].lanternLight, c.rooms[KEY].shopEnabled, c.rooms[KEY].npcs], [true, true, false, []]);
    });

    test('Bailey wandering at the foot of the temple steps never closes the doors: wherever he may stand, both leaves are walked into from the street (#213)', () => {
        const mgr = game('Object.create(NPCManager.prototype)');
        for (const stitch of [true, false]) {
            const { world, config } = worldWith(stitch);
            world.date = '2025-11-01';
            const street = [27, 20];
            world.enter(HOST, ...street);
            const { ox, oy } = world.here();
            const bailey = world.room.npcs.find((n) => n.name === 'Bailey');
            assert.deepStrictEqual([bailey.gridX - ox, bailey.gridY - oy], [26, 17], 'at the foot of the steps that day');
            // where the game lets him wander: within npcWanderRadius of where he was put (NPCManager.spawnNPC),
            // on cells nothing blocks, never onto a doorway (NPCManager.atDoorway)
            mgr.scene = { roomManager: { currentRoom: 'here', rooms: { here: world.room } } };
            const r = config.game.npcWanderRadius, home = [bailey.gridX, bailey.gridY], spots = [];
            for (let y = home[1] - r; y <= home[1] + r; y++) {
                for (let x = home[0] - r; x <= home[0] + r; x++) {
                    if (!world.blocked.has(`${x},${y}`) && !mgr.atDoorway(x, y)) spots.push([x, y]);
                }
            }
            const local = spots.map(([x, y]) => `${x - ox},${y - oy}`);
            assert.ok(local.includes('27,17') && local.includes('28,17'), 'he can stand on the steps below either leaf');
            for (const cell of ['27,15', '28,15', '27,16', '28,16']) assert.ok(!local.includes(cell), `he can stand on ${cell}`);
            const doors = config.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY);
            for (const [x, y] of spots) {
                for (const door of doors) {
                    world.enter(HOST, ...street);
                    const him = world.room.npcs.find((n) => n.name === 'Bailey');
                    [him.gridX, him.gridY] = [x, y];
                    assert.ok(!world.canStep(x, y + 1, x, y), 'he is in the way where he stands');
                    const way = world.path(door.gridX + ox, door.gridY + 1 + oy);
                    assert.ok(way, `Bailey on ${x - ox},${y - oy} shuts the leaf at ${door.gridX},${door.gridY} (stitch ${stitch})`);
                    for (const dir of way) world.step(dir);
                    assert.strictEqual(world.step('n').transported.to, KEY);
                }
            }
        }
    });

    test('the main hall has its sanctum behind a lattice under the cabinet, the box, the burner and the great lantern down the middle, columns you walk behind (#213)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 26, 22]);
        const one = (piece) => { const all = at(room, c, piece); assert.strictEqual(all.length, 1, piece); return all[0]; };
        // the back wall, west to east, three rows tall and solid: charms, panel, cabinet, panel, fortune drawers
        const back = ['wall-charms', 'wall-tennin-l', 'kuden', 'wall-tennin-r', 'omikuji'].map(one);
        assert.deepStrictEqual(back, [[1, 1], [5, 1], [10, 1], [16, 1], [21, 1]]);
        for (let x = 1; x <= 24; x++) for (let y = 1; y <= 3; y++) assert.ok(`${x},${y}` in solid, `back wall ${x},${y}`);
        // the sanctum: sixteen cells by four at the foot of the cabinet and its panels, all of it shut to you
        const [nx, ny] = one('naijin');
        assert.deepStrictEqual([nx, ny], [5, 4]);
        for (let x = nx; x < nx + 16; x++) for (let y = ny; y < ny + 4; y++) assert.ok(`${x},${y}` in solid, `sanctum ${x},${y}`);
        // ...with an aisle of four cells either side of it that runs up to the counter and the drawers
        for (const x of [1, 2, 3, 4, 21, 22, 23, 24]) for (let y = 4; y <= 7; y++) assert.ok(!(`${x},${y}` in solid), `aisle ${x},${y}`);
        // down the middle, on the door's own two columns: offering box, burner, lantern, door
        const [sx, sy] = one('saisen'), [jx, jy] = one('jokoro'), [lx, ly] = one('chochin');
        assert.deepStrictEqual([sx, jx, lx], [11, 11, 11]);
        assert.ok(sy === ny + 4 && jy > sy + 2 && ly > jy + 3, 'in that order from the sanctum to the door, a clear row between each');
        assert.ok('11,' + ly in tiles(room, 'Tops'), 'the great lantern hangs overhead');
        for (let x = lx; x < lx + 4; x++) for (let y = ly; y < ly + 3; y++) assert.ok(!(`${x},${y}` in solid), `you walk under the lantern at ${x},${y}`);
        // the burner's smoke is walked behind: its top row is open, its bowl is not
        for (let x = jx; x < jx + 4; x++) assert.deepStrictEqual([`${x},${jy}` in solid, `${x},${jy + 2}` in solid], [false, true], `burner ${x}`);
        const exits = room.transporters;
        assert.deepStrictEqual(exits.map((t) => [t.gridX, t.gridY, t.targetRoom, t.targetX, t.targetY, t.hidden]),
            [[12, 19, HOST, 27, 16, true], [13, 19, HOST, 28, 16, true]]);
        // eight columns; the shaft of each is walked behind: only the foot (the third cell down) is solid
        const pillars = at(room, c, 'pillar');
        assert.strictEqual(pillars.length, 8);
        for (const [x, y] of pillars) assert.deepStrictEqual([`${x},${y}` in solid, `${x},${y + 1}` in solid, `${x},${y + 2}` in solid], [false, false, true]);
        // a stone floor, not the palace's boards or mats and not the shrine's
        const floor = tiles(room, 'Floor');
        for (let x = 1; x <= 24; x++) for (let y = 4; y <= 18; y++) assert.ok(/^temple-in-slab-[ab]_/.test(c.tilePalette[floor[`${x},${y}`]]), `floor ${x},${y}`);
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-)/.test(k)), 'none of the shrine\'s or the palace\'s pieces');
        // lights, the instruments, what stands in the aisles
        assert.ok(at(room, c, 'toro-hang').length >= 6 && at(room, c, 'shokudai').length >= 4);
        assert.ok(at(room, c, 'toro-hang').concat(at(room, c, 'haze')).every(([x, y]) => `${x},${y}` in tiles(room, 'Tops')), 'hung lanterns and haze are overhead');
        for (const piece of ['drum', 'keisu', 'candles', 'musubi']) one(piece);
        // every light has its spots in the Glows table, in numbers
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        const G = game('Glows');
        for (const piece of ['toro-hang', 'shokudai', 'candles', 'chochin', 'jokoro', 'naijin', 'kuden']) {
            const spots = G.spotsFor(`temple-in-${piece}_0_0`, c.spriteMetadata[`temple-in-${piece}_0_0`]);
            assert.ok(spots.length >= 1 && spots.every((s) => Number.isInteger(s.color) && s.r <= 2.5), piece);
        }
    });

    test('you walk up the temple steps and in, reach everything there is to bump, and come out on the step you went in by (#213)', () => {
        const { world, config } = worldWith(false);
        const doors = config.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY);
        const mats = config.rooms[KEY].transporters;
        doors.forEach((door, n) => {
            world.enter(HOST, door.gridX, door.gridY + 2);                       // the foot of the steps
            assert.ok(!world.step('n').transported, 'onto the step');
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, KEY, `leaf ${n}`);
            const here = world.here();
            assert.deepStrictEqual([here.x, here.y], [door.targetX, door.targetY]);
            assert.ok(!mats.some((t) => t.gridX === here.x && t.gridY === here.y), 'arrives off the exit mats');
            const things = world.interactions();
            assert.deepStrictEqual(plain(things.map((i) => i.kind).sort()),
                ['bowl-bell', 'charms', 'drawers', 'incense', 'offering', 'sanctum', 'temple-drum', 'tied-fortunes', 'votive-candles']);
            assert.ok(things.every((i) => i.group === 'temple' || i.group === 'flavour'), 'nothing in here is a shop');
            for (const i of things) {
                // from below it, or (what stands against a side wall) from beside its foot
                const foot = i.y + i.h - 1;
                const sides = [];
                for (let x = i.x; x < i.x + i.w; x++) sides.push([x, foot + 1, x, foot]);
                sides.push([i.x - 1, foot, i.x, foot], [i.x + i.w, foot, i.x + i.w - 1, foot]);
                const side = sides.find(([x, y]) => world.path(x, y));
                assert.ok(side, `no way to the ${i.kind}`);
                for (const dir of world.path(side[0], side[1])) world.step(dir);
                assert.deepStrictEqual([world.here().x, world.here().y], [side[0], side[1]]);
                const bump = world.interactionAt(side[2], side[3]);
                assert.strictEqual(bump && bump.kind, i.kind);
                assert.ok(/wafts the incense|palms together|shakes a numbered stick|says: "/.test(world.describe(bump)), world.describe(bump));
            }
            const mat = mats[n];
            for (const dir of world.path(mat.gridX, mat.gridY - 1)) world.step(dir);
            const out = world.step('s');
            assert.strictEqual(out.transported && out.transported.to, HOST);
            assert.deepStrictEqual([world.here().x, world.here().y], [door.gridX, door.gridY + 1]);
        });
        const lint = world.lint(KEY);
        assert.deepStrictEqual(plain([lint.errors, lint.warns]), [{}, {}], 'lint');
    });

    test('the temple doors are doorways of the stitched city, at the district\'s own cells (#213)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        const city = rm.rooms.TokyoCity.transporters.filter((x) => x.targetRoom === KEY);
        const local = world.config.rooms[HOST].transporters.filter((x) => x.targetRoom === KEY);
        assert.strictEqual(city.length, 2);
        local.forEach((t, i) => {
            const cell = rm.resolve(HOST, t.gridX, t.gridY);
            assert.deepStrictEqual([city[i].gridX, city[i].gridY], [cell.x, cell.y]);
        });
        world.enter(HOST, local[0].gridX, local[0].gridY + 1);
        assert.strictEqual(world.step('n').transported.to, KEY);
        const out = world.step('s');
        assert.ok(out.transported, 'the mat under the arrival cell leads out');
        const here = world.here();
        assert.deepStrictEqual([here.room, here.x, here.y], [HOST, local[0].gridX, local[0].gridY + 1]);
    });

    test('the smoke is wafted for nothing, a line in turn; the burner, the box and the drawers are rules of the Interactions table (#213)', () => {
        const V = visit();
        assert.ok(V.WAFTS.length >= 4 && V.WAFTS.every((l) => l.startsWith('You waft the smoke over your ')));
        assert.strictEqual(new Set(V.WAFTS).size, V.WAFTS.length);
        assert.deepStrictEqual([0, 1, V.WAFTS.length, V.WAFTS.length + 1, -1, 'x'].map((n) => V.waft(n)),
            [V.WAFTS[0], V.WAFTS[1], V.WAFTS[0], V.WAFTS[1], V.WAFTS[V.WAFTS.length - 1], V.WAFTS[0]]);
        const I = game('Interactions');
        const hit = (key, room) => plain(I.match(key, room || { interior: true, shopEnabled: false }));
        assert.deepStrictEqual(hit('temple-in-jokoro_0_0'), { kind: 'incense', group: 'temple', footprint: true });
        assert.deepStrictEqual(hit('temple-in-saisen_0_0'), { kind: 'offering', group: 'temple', footprint: true });
        assert.deepStrictEqual(hit('temple-in-omikuji_0_0'), { kind: 'drawers', group: 'temple', footprint: true });
        // the shrine's own box and stand are still the shrine's
        assert.deepStrictEqual([hit('shrine-in-saisen-red_0_0').group, hit('shrine-in-omikuji_0_0').group], ['shrine', 'shrine']);
        for (const piece of ['wall-charms', 'naijin', 'drum', 'keisu', 'candles', 'musubi']) {
            const rule = hit(`temple-in-${piece}_0_0`);
            assert.ok(rule && rule.group === 'flavour' && rule.say && rule.say.length <= 100, piece);
        }
        // the charm counter sells nothing: the catalogue has no charm, and none was invented for it
        assert.ok(!/omamori|charm/i.test(src('Shop.js')));
        for (const key of ['temple-in-kuden_0_0', 'temple-in-pillar_0_0', 'temple-in-chochin_0_0', 'temple-in-toro-hang_0_0', 'temple-in-bench_0_0', 'temple-in-haze_0_0']) assert.strictEqual(hit(key), null, key);
        // one answer per bump, by the offering box's rule, and nothing new to press
        const code = src('TempleVisit.js'), scene = src('GameScene.js');
        assert.ok(code.includes("const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell);"));
        assert.ok(code.includes('if (!fresh) return true;') && code.includes('this.bump = ShrineVisit.held(this.bump, heading);'));
        assert.ok(!/addKey|KeyCodes|pointerdown|input\.on/.test(code), 'no key or pointer of its own');
        assert.ok(!/localStorage|shop\.(guestbook|stamps)/.test(code), 'nothing of its own is saved');
        assert.ok(scene.includes('this.templeVisit = new TempleVisit(this);') && scene.includes('this.templeVisit.check(targetGridX, targetGridY);') &&
            scene.includes('if (this.templeVisit) this.templeVisit.hold(this.inputHandler.heading());'));
        const index = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        assert.ok(index.indexOf("'src/ShrineVisit.js'") < index.indexOf("'src/TempleVisit.js'") && index.indexOf("'src/Shop.js'") < index.indexOf("'src/TempleVisit.js'"));
    });

    test('the temple\'s fortune is the shrines\' omikuji: one a game day across all of them, the same price and odds, its own wording (#213)', () => {
        const V = visit(), S = game('ShrineVisit');
        const day = '2025-11-01';
        // a fresh one at the temple: the shrine's rule decides it, to the yen and the rank
        for (const roll of [0, 0.2, 0.5, 0.77, 0.999]) {
            const mine = V.fortune(null, day, 500, roll), theirs = S.fortune(null, day, 500, roll);
            assert.deepStrictEqual(plain([mine.fresh, mine.i, mine.money, mine.omikuji]), plain([theirs.fresh, theirs.i, theirs.money, theirs.omikuji]), `roll ${roll}`);
            assert.ok(mine.fresh && mine.money === 500 - S.FORTUNE_PRICE);
            const f = S.FORTUNES[mine.i];
            assert.strictEqual(mine.line, `Shake, ¥100, stick ${V.stick(roll)}: ${f.rank} (${f.means}). ${f.text}`);
            assert.notStrictEqual(mine.line, theirs.line);
        }
        assert.deepStrictEqual([0, 0.004, 0.5, 0.999, 1, -3, undefined].map(V.stick), [1, 1, 51, 100, 100, 1, 1], 'a stick for each of the hundred drawers');
        // drawn here, then a shrine the same day: already drawn, nothing taken, the same slip
        const here = V.fortune(null, day, 500, 0.5);
        const shrine = S.fortune(here.omikuji, day, here.money, 0.01);
        assert.deepStrictEqual([shrine.fresh, shrine.i, shrine.money, shrine.omikuji], [false, here.i, 400, undefined]);
        assert.ok(shrine.line.startsWith('Drawn already today: '));
        // drawn at a shrine, then here the same day: the drawer stays shut
        const first = S.fortune(null, day, 500, 0.9);
        const temple = V.fortune(first.omikuji, day, first.money, 0.01);
        assert.deepStrictEqual([temple.fresh, temple.i, temple.money, temple.omikuji], [false, first.i, 400, undefined]);
        assert.ok(temple.line.startsWith('The drawer stays shut: ') && temple.line.includes(S.FORTUNES[first.i].rank));
        // another game day (Time Travel counts), and an empty wallet
        assert.ok(V.fortune(first.omikuji, '2025-11-02', 400, 0.3).fresh);
        const broke = V.fortune(null, day, 99, 0.3);
        assert.deepStrictEqual([broke.fresh, broke.i, broke.money, broke.omikuji], [false, -1, 99, undefined]);
        assert.ok(/¥100/.test(broke.line) && /cylinder/.test(broke.line));
        // the offering: the shrine's price and blessings, the temple's manner
        const gave = V.offer(100, 0.4), poor = V.offer(4, 0.4);
        assert.deepStrictEqual([gave.ok, gave.money, poor.ok, poor.money], [true, 100 - S.OFFERING, false, 4]);
        assert.ok(gave.line.startsWith('¥5 in the box. Palms together') && gave.line.endsWith(S.pick(S.BLESSINGS, 0.4)) && !/bell|garan/.test(gave.line));
        assert.ok(/palms together anyway/.test(poor.line));
        // a toast is one line: nothing the temple says is longer than the palace's longest
        const lines = V.WAFTS.concat(S.FORTUNES.flatMap((f, i) => [V.fortune(null, day, 500, 0.999).line, V.fortune({ date: day, i }, day, 0, 0).line]),
            S.BLESSINGS.map((b, i) => V.offer(50, i / S.BLESSINGS.length).line), poor.line, broke.line);
        for (let i = 0; i < 1; i += 0.03) lines.push(V.fortune(null, day, 500, i).line);
        const longest = Math.max(...lines.map((l) => l.length));
        assert.ok(longest <= 96, `${longest} characters`);
        // one save field, the shrine's: a fortune drawn here is in the blob as the shrine wrote it, and nothing else is added
        const before = { v: 4, money: 500, items: {}, effects: {}, used: {}, caught: {}, energy: 80, stamps: {}, hints: {} };
        const s = shopWith(before);
        const out = V.fortune(s.shop.omikuji, day, s.shop.money, 0.5);
        s.shop.money = out.money;
        s.shop.omikuji = out.omikuji;
        s.shop.save();
        assert.deepStrictEqual(s.saved(), Object.assign({}, before, { money: 400, omikuji: { date: day, i: out.i } }));
        assert.ok(src('Shop.js').includes("v: 4, money: this.money"), 'the blob is still v4');
        assert.ok(!/omikuji\s*=\s*\{/.test(src('TempleVisit.js')), 'the temple builds no fortune of its own');
    });

    test('the hall is "Senso-ji" on the bar, short enough to count down on a phone, and the map says it is in Tokyo (#213)', () => {
        const c = cfg();
        assert.strictEqual(c.rooms[KEY].name, NAME);
        assert.ok(!Object.entries(c.rooms).some(([k, r]) => k !== KEY && r.name === NAME), 'no other room has the name');
        // hud-phone-layout.test.js's rule: a name of 11 characters or fewer leaves room for "devhouse 3 soon"
        // on the one-row bar at 667x375 (715 wide: 10 + 16 a character + 10 + "menu" + 10)
        assert.ok(c.rooms[KEY].name.length <= 11);
        assert.ok(10 + 16 * `${NAME} | devhouse 3 in 8d | ¥5,000`.length + 10 + 64 + 10 <= 715);
        assert.strictEqual(game('hudBrief')(NAME), NAME);
        if (!game('typeof Places !== "undefined"')) vm.runInContext(src('utils/Places.js'), ctx, { filename: 'Places.js' });
        assert.strictEqual(game('Places').whereText(game('decodeConfig')(c), KEY), 'Senso-ji (in Tokyo)');
    });

    test('the temple generator and its art tool are checked, own the door through roomgen, and touch no other room (#213)', () => {
        const check = tool('check_generators.py');
        for (const name of ['generate_temple', 'generate_temple_art']) assert.ok(check.includes(`'${name}'`), name);
        const rg = tool('roomgen.py');
        assert.ok(/TEMPLE_PREFIX: \('temple', TEMPLE_DOORS\)/.test(rg) && /TEMPLE_DOORS = \{'shrine-walls_2_2': \[\(0, 0\)\]\}/.test(rg), 'OWNED_DOORS');
        assert.ok(/rg\.TEMPLE_DOORS/.test(tool('generate_temple.py')), 'the generator has no door sprites of its own');
        const c = cfg(), mark = c.rooms[KEY].temple;
        assert.deepStrictEqual(mark, { host: HOST, doors: c.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY).map((t) => [t.gridX, t.gridY]) });
        // no other generator knows about the hall, and no other room has a door into it
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !/^generate_temple/.test(n))) {
            assert.ok(!/TempleMarket|TEMPLE_|temple-in-/.test(tool(f)), f);
        }
        assert.deepStrictEqual(Object.entries(c.rooms).filter(([, r]) => (r.transporters || []).some((t) => t.targetRoom === KEY)).map(([k]) => k), [HOST]);
        // the palette was appended to: every temple sprite is in it once, after the palace's
        const mine = c.tilePalette.map((k, i) => [k, i]).filter(([k]) => k.startsWith('temple-in-'));
        assert.ok(mine.length >= 28 && new Set(mine.map(([k]) => k)).size === mine.length);
        assert.ok(mine[0][1] > c.tilePalette.indexOf('palace-in-dais_0_0'));
        // every sprite the art tool registers is on disk at a whole number of cells, and is used by the hall
        const png = require(path.join(GV2, 'tools', 'png'));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith('temple-in-'));
        assert.ok(keys.length >= 28, `${keys.length} temple sprites`);
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
            assert.ok(mine.some(([name]) => name === k), `${k} is drawn but not placed`);
        }
        // a re-run of the generator on a scratch copy changes nothing
        const { spawnSync } = require('child_process');
        const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gamev2-temple-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            const before = fs.readFileSync(path.join(tmp, 'config.json'), 'utf8');
            const run = spawnSync('python3', ['tools/generate_temple.py'], { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
            assert.strictEqual(run.status, 0, run.stderr);
            assert.ok(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8') === before, 'generate_temple.py changed config.json on a re-run');
            // ...and from a sealed temple it builds the same world: seal both leaves, drop the hall, run it
            const sealed = JSON.parse(before), host = sealed.rooms[HOST];
            const blank = sealed.tilePalette.indexOf('gk_blank');
            for (const t of host.transporters.filter((x) => x.targetRoom === KEY)) tiles(host, 'Colliders')[`${t.gridX},${t.gridY}`] = blank;
            host.transporters = host.transporters.filter((x) => x.targetRoom !== KEY);
            delete sealed.rooms[KEY];
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(sealed, null, 2));
            const again = spawnSync('python3', ['tools/generate_temple.py'], { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
            assert.strictEqual(again.status, 0, again.stderr);
            // the same world, but for where the hall's two doors stand in the district's list of doors: a
            // rebuilt door goes to the end of it, past the door of a room opened since (the tower's lobby, #216)
            const doorsInOrder = (world) => {
                world.rooms[HOST].transporters.sort((a, b) => a.gridY - b.gridY || a.gridX - b.gridX || (a.targetRoom < b.targetRoom ? -1 : 1));
                return world;
            };
            assert.deepStrictEqual(doorsInOrder(JSON.parse(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8'))), doorsInOrder(JSON.parse(before)));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });
};
