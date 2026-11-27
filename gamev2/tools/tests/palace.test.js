// The palace's audience hall (issue #215): tools/generate_palace.py, tools/generate_palace_art.py, src/PalaceVisit.js.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, shopWith, worldWith }) => {
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    const HOST = 'Tokyo', KEY = 'PalaceHallTokyo1';
    // src/ShrineVisit.js and src/PalaceVisit.js are not in the runner's list: load them once, here
    const visit = () => {
        if (!game('typeof ShrineVisit !== "undefined"')) vm.runInContext(src('ShrineVisit.js'), ctx, { filename: 'ShrineVisit.js' });
        if (!game('typeof PalaceVisit !== "undefined"')) vm.runInContext(src('PalaceVisit.js'), ctx, { filename: 'PalaceVisit.js' });
        return game('PalaceVisit');
    };
    // where every copy of a piece stands in a room: [[x, y], ...]
    const at = (room, c, piece) => room.layers.flatMap((l) => Object.entries(l.tiles))
        .filter(([, id]) => c.tilePalette[id] === `palace-in-${piece}_0_0`).map(([cell]) => cell.split(',').map(Number));
    // the palace building's two end towers: the cell of each `pagoda-floor`, west first
    const towers = (c) => Object.entries(tiles(c.rooms[HOST], 'Over Floor'))
        .filter(([, id]) => c.tilePalette[id] === 'pagoda-floor_0_0').map(([cell]) => cell.split(',').map(Number)).sort((a, b) => a[0] - b[0]);

    test('the palace is the long building inside the moat: its two end towers each have a door into the one audience hall (#215)', () => {
        const c = cfg(), host = c.rooms[HOST], solid = tiles(host, 'Colliders');
        const found = towers(c);
        assert.strictEqual(found.length, 2, 'a tower at each end of the wings');
        // each tower stands under its own roof, and the six hallway pieces and the central hall run between them
        const tops = Object.entries(tiles(host, 'Tops')).map(([cell, id]) => [c.tilePalette[id], ...cell.split(',').map(Number)]);
        for (const [x, y] of found) assert.ok(tops.some(([k, tx, ty]) => k === 'pagoda-roof_0_0' && tx === x && ty === y - 5), `tower ${x},${y}: its roof`);
        const wings = tops.filter(([k]) => k === 'temple-hallway_0_0');
        assert.strictEqual(wings.length, 6);
        assert.ok(wings.every(([, x]) => x > found[0][0] && x < found[1][0]), 'the wings run from tower to tower');
        const doors = host.transporters.filter((t) => t.targetRoom === KEY);
        assert.deepStrictEqual(doors.map((t) => [t.gridX, t.gridY, t.hidden]), found.map(([x, y]) => [x + 1, y + 2, true]));
        assert.deepStrictEqual(doors.map((t) => [t.gridX, t.gridY]), [[19, 22], [41, 22]]);
        for (const t of doors) {
            assert.ok(!(`${t.gridX},${t.gridY}` in solid), 'the door cell is open');
            assert.ok(!(`${t.gridX},${t.gridY + 1}` in solid), 'the cell in front of it can be stood on');
        }
        // the towers are sealed everywhere else: each 3x8 block is solid but for its one door
        for (const [x, y] of found) {
            const open = [];
            for (let cx = x; cx < x + 3; cx++) for (let cy = y - 5; cy <= y + 2; cy++) if (!(`${cx},${cy}` in solid)) open.push(`${cx},${cy}`);
            assert.deepStrictEqual(open, [`${x + 1},${y + 2}`]);
        }
        // the shrine hall in the middle keeps its own door and its own room: the palace did not take it
        const shrine = host.transporters.filter((t) => t.targetRoom === 'ShrineTokyo1');
        assert.deepStrictEqual(shrine.map((t) => [t.gridX, t.gridY]), [[30, 20]]);
        assert.strictEqual(c.rooms.ShrineTokyo1.name, 'Palace Shrine');
        // and the host's other ways out are the seams it always had
        assert.deepStrictEqual(host.transporters.map((t) => t.targetRoom), ['Market', 'Market', 'ShrineTokyo1', KEY, KEY]);
    });

    test('nobody stands on a palace door or the cell in front of it on any date, and no blog spot stands a visitor there (#215)', () => {
        const c = cfg(), host = c.rooms[HOST];
        const cells = host.transporters.filter((t) => t.targetRoom === KEY).flatMap((t) => [`${t.gridX},${t.gridY}`, `${t.gridX},${t.gridY + 1}`]);
        assert.strictEqual(cells.length, 4);
        const inWay = host.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
            .filter(([, s]) => cells.includes(`${s.gridX},${s.gridY}`)).map(([date]) => `${n.name} ${date}`));
        assert.deepStrictEqual(inWay, []);
        // the district's own stand cell, and the two room-scoped spots (their stand cells are asserted in
        // test_blog_to_npc.py: the gate at 28,34 and the moat at 20,33)
        for (const d of c.districts[HOST]) assert.ok(!cells.includes(d.stand.join(',')), d.name);
        for (const stand of ['28,34', '20,33']) assert.ok(!cells.includes(stand));
        const spots = tool('blog_to_npc.py');
        assert.ok(spots.includes("('blue-wall-gate', 'the Imperial Palace gate', (-1, 6), {'rooms': ('Tokyo',)})"));
        assert.ok(spots.includes("('moat-south', 'the palace moat', (10, 2), {'rooms': ('Tokyo',)})"));
        assert.ok(!/pagoda-floor/.test(spots), 'no landmark hangs on a tower');
        // the hall is an interior: the pipeline never offers it
        assert.deepStrictEqual([c.rooms[KEY].interior, c.rooms[KEY].lanternLight, c.rooms[KEY].shopEnabled, c.rooms[KEY].npcs], [true, true, false, []]);
    });

    test('the audience hall has its dais under the painted wall, screens you walk behind, two side corridors and the long one between the doors (#215)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], ['Palace Hall', 26, 22]);
        const one = (piece) => { const all = at(room, c, piece); assert.strictEqual(all.length, 1, piece); return all[0]; };
        const [mx, my] = one('mural'), [dx, dy] = one('dais');
        assert.deepStrictEqual([dx, dy], [mx, my + 3], 'the dais stands at the foot of the painted screens, the same twelve cells wide');
        for (let x = dx; x < dx + 12; x++) for (let y = dy; y < dy + 3; y++) assert.ok(`${x},${y}` in solid, `dais ${x},${y}`);
        // shelves to its left, tasselled doors to its right; the armour on one side, the swords on the other
        assert.deepStrictEqual([one('alcove-shelves'), one('alcove-doors')], [[mx - 3, my], [mx + 12, my]]);
        assert.ok(one('armour')[0] < dx && one('swords')[0] >= dx + 12);
        // eight pillars; the shaft of each is walked behind: only the foot (the third cell down) is solid
        const pillars = at(room, c, 'pillar');
        assert.strictEqual(pillars.length, 8);
        for (const [x, y] of pillars) assert.deepStrictEqual([`${x},${y}` in solid, `${x},${y + 1}` in solid, `${x},${y + 2}` in solid], [false, false, true]);
        // the two runs of painted screens: their head row is walked behind, their foot row is solid, and
        // the way through is between them
        const [tx, ty] = one('fusuma-tiger'), [wx, wy] = one('fusuma-waves');
        assert.strictEqual(ty, wy);
        for (const x0 of [tx, wx]) {
            for (let x = x0; x < x0 + 6; x++) assert.deepStrictEqual([`${x},${ty}` in solid, `${x},${ty + 1}` in solid], [false, true], `screen ${x}`);
        }
        for (let x = tx + 7; x < wx - 1; x++) assert.ok(!(`${x},${ty + 1}` in solid), `the way through at ${x}`);
        assert.strictEqual(wx - 1 - (tx + 7), 4, 'four cells wide');
        // floors: boards in the side corridors and the long corridor, tatami in the hall
        const floor = tiles(room, 'Floor'), name = (x, y) => c.tilePalette[floor[`${x},${y}`]];
        assert.ok(/^palace-in-board-[ab]_/.test(name(1, dy + 4)) && /^palace-in-board-[ab]_/.test(name(24, dy + 4)), 'the side corridors');
        assert.ok(/^palace-in-tatami-/.test(name(12, dy + 5)), 'the hall');
        assert.ok(/^palace-in-board-h-/.test(name(12, ty + 3)), 'the long corridor');
        assert.strictEqual(at(room, c, 'sun-w').length, at(room, c, 'sun-e').length);
        assert.ok(at(room, c, 'sun-w').length >= 5, 'daylight through the screens of both side corridors');
        // hung and standing lamps, cushions set out, the corridor's furniture
        assert.ok(at(room, c, 'lamp-hang').length >= 6 && at(room, c, 'andon').length >= 5);
        assert.ok(at(room, c, 'lamp-hang').every(([x, y]) => `${x},${y}` in tiles(room, 'Tops')), 'the hung lamps are overhead');
        assert.strictEqual(at(room, c, 'zabuton').length, 16);
        for (const piece of ['guestbook', 'guardpost', 'byobu', 'table']) one(piece);
        // every lamp has its spots in the Glows table, in numbers
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        const G = game('Glows');
        for (const piece of ['andon', 'lamp-hang', 'dais', 'guardpost']) {
            const spots = G.spotsFor(`palace-in-${piece}_0_0`, c.spriteMetadata[`palace-in-${piece}_0_0`]);
            assert.ok(spots.length >= 1 && spots.every((s) => Number.isInteger(s.color) && s.r <= 2.5), piece);
        }
    });

    test('you walk in by either tower, up to the dais, the armour and the book, and out by the door you choose (#215)', () => {
        const { world, config } = worldWith(false);
        const doors = config.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY);
        const mats = config.rooms[KEY].transporters;
        assert.strictEqual(mats.length, 4, 'two mats a door');
        doors.forEach((door, n) => {
            world.enter(HOST, door.gridX, door.gridY + 1);
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, KEY, `door ${n}`);
            const here = world.here();
            assert.deepStrictEqual([here.x, here.y], [door.targetX, door.targetY]);
            assert.ok(!mats.some((t) => t.gridX === here.x && t.gridY === here.y), 'arrives off the exit mats');
            // the mats under you lead back to the tower you came by
            const mine = mats.filter((t) => Math.abs(t.gridX - here.x) <= 1 && t.gridY === here.y + 1);
            assert.strictEqual(mine.length, 2);
            for (const t of mine) assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY, t.hidden], [HOST, door.gridX, door.gridY + 1, true]);
            // every thing with something to say or do can be bumped from a cell you can walk to (and none is a shop)
            const things = world.interactions();
            assert.deepStrictEqual(plain(things.map((i) => i.kind).sort()), ['armour', 'audience', 'guard-post', 'guestbook', 'swords']);
            for (const i of things) {
                // from below it, or (the pieces that stand against the front wall) from beside its foot
                const foot = i.y + i.h - 1;
                const sides = [[i.x, foot + 1, i.x, foot], [i.x - 1, foot, i.x, foot], [i.x + i.w, foot, i.x + i.w - 1, foot]];
                const side = sides.find(([x, y]) => world.path(x, y));
                assert.ok(side, `no way to the ${i.kind}`);
                for (const dir of world.path(side[0], side[1])) world.step(dir);
                assert.deepStrictEqual([world.here().x, world.here().y], [side[0], side[1]]);
                const bump = world.interactionAt(side[2], side[3]);
                assert.strictEqual(bump && bump.kind, i.kind);
                assert.ok(/audience|visitors' book|says: "/.test(world.describe(bump)), world.describe(bump));
            }
            // across the hall and out by the OTHER door: onto the cell in front of the other tower
            const other = doors[1 - n], far = mats.find((t) => t.targetX === other.gridX);
            for (const dir of world.path(far.gridX, far.gridY - 1)) world.step(dir);
            const out = world.step('s');
            assert.strictEqual(out.transported && out.transported.to, HOST);
            assert.deepStrictEqual([world.here().x, world.here().y], [other.gridX, other.gridY + 1]);
        });
        const lint = world.lint(KEY);
        assert.deepStrictEqual(plain([lint.errors, lint.warns]), [{}, {}], 'lint');
    });

    test('the palace doors are doorways of the stitched city, at the district\'s own cells (#215)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        const city = rm.rooms.TokyoCity.transporters.filter((x) => x.targetRoom === KEY);
        const local = world.config.rooms[HOST].transporters.filter((x) => x.targetRoom === KEY);
        assert.strictEqual(city.length, 2);
        local.forEach((t, i) => {
            const cell = rm.resolve(HOST, t.gridX, t.gridY);
            assert.deepStrictEqual([city[i].gridX, city[i].gridY], [cell.x, cell.y]);
        });
        // in by the west tower from the city, and out again: back in the city, in front of that tower
        world.enter(HOST, local[0].gridX, local[0].gridY + 1);
        assert.strictEqual(world.step('n').transported.to, KEY);
        const out = world.step('s');
        assert.ok(out.transported, 'the mat under the arrival cell leads out');
        const here = world.here();
        assert.deepStrictEqual([here.room, here.x, here.y], [HOST, local[0].gridX, local[0].gridY + 1]);
    });

    test('requesting an audience answers drily, each answer in turn; the dais and the book are rules of the Interactions table (#215)', () => {
        const V = visit();
        assert.ok(V.AUDIENCES.length >= 5 && V.AUDIENCES.every((l) => l.startsWith('You request an audience. ')));
        assert.strictEqual(new Set(V.AUDIENCES).size, V.AUDIENCES.length);
        assert.deepStrictEqual([0, 1, V.AUDIENCES.length, V.AUDIENCES.length + 1, -1, 'x'].map((n) => V.audience(n)),
            [V.AUDIENCES[0], V.AUDIENCES[1], V.AUDIENCES[0], V.AUDIENCES[1], V.AUDIENCES[V.AUDIENCES.length - 1], V.AUDIENCES[0]]);
        // a toast holds them: the longest is no longer than the shrine's longest blessing line
        const longest = Math.max(...V.AUDIENCES.map((l) => l.length), V.sign(null, '2027-02-20').line.length, V.sign({ date: '2027-02-20', n: 1 }, '2027-02-20').line.length);
        assert.ok(longest <= 96, `${longest} characters`);
        const I = game('Interactions');
        const hit = (key, room) => plain(I.match(key, room || { interior: true, shopEnabled: false }));
        assert.deepStrictEqual(hit('palace-in-dais_0_0'), { kind: 'audience', group: 'palace', footprint: true });
        assert.deepStrictEqual(hit('palace-in-guestbook_0_0'), { kind: 'guestbook', group: 'palace', footprint: true });
        assert.deepStrictEqual(hit('palace-in-armour_0_0').group, 'flavour');
        assert.ok(hit('palace-in-armour_0_0').say && hit('palace-in-swords_0_0').say && hit('palace-in-guardpost_0_0').say);
        for (const key of ['palace-in-mural_0_0', 'palace-in-pillar_0_0', 'palace-in-byobu_0_0', 'palace-in-table_0_0', 'palace-in-andon_0_0']) assert.strictEqual(hit(key), null, key);
        // one answer per bump, by the offering box's rule, and nothing new to press
        const code = src('PalaceVisit.js'), scene = src('GameScene.js');
        assert.ok(code.includes("const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell);"));
        assert.ok(code.includes('if (!fresh) return true;') && code.includes('this.bump = ShrineVisit.held(this.bump, heading);'));
        assert.ok(!/addKey|KeyCodes|pointerdown|input\.on/.test(code), 'no key or pointer of its own');
        assert.ok(scene.includes('this.palaceVisit = new PalaceVisit(this);') && scene.includes('this.palaceVisit.check(targetGridX, targetGridY);') &&
            scene.includes('if (this.palaceVisit) this.palaceVisit.hold(this.inputHandler.heading());'));
        const index = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        assert.ok(index.indexOf("'src/ShrineVisit.js'") < index.indexOf("'src/PalaceVisit.js'") && index.indexOf("'src/Shop.js'") < index.indexOf("'src/PalaceVisit.js'"));
    });

    test('the visitors\' book is signed once a game day and counts your visits (#215)', () => {
        const V = visit();
        const first = V.sign(null, '2027-02-20');
        assert.deepStrictEqual(plain([first.fresh, first.n, first.guestbook]), [true, 1, { date: '2027-02-20', n: 1 }]);
        assert.ok(/^You sign the visitors' book\./.test(first.line));
        const again = V.sign(first.guestbook, '2027-02-20');
        assert.deepStrictEqual([again.fresh, again.n, again.guestbook], [false, 1, undefined]);
        assert.ok(/today already/.test(again.line));
        const next = V.sign(first.guestbook, '2027-02-21');
        assert.deepStrictEqual(plain([next.fresh, next.n, next.guestbook]), [true, 2, { date: '2027-02-21', n: 2 }]);
        assert.ok(next.line.includes('visit 2'));
        // Time Travel to an earlier day is another day too
        assert.deepStrictEqual(plain(V.sign(next.guestbook, '2025-11-01').guestbook), { date: '2025-11-01', n: 3 });
        // junk in the save is no book at all
        for (const junk of [undefined, 'x', 7, {}, { date: 'soon', n: 2 }, { date: '2027-02-20', n: 0 }, { date: '2027-02-20', n: 'many' }]) {
            assert.strictEqual(V.sign(junk, '2027-02-20').n, 1, JSON.stringify(junk));
        }
    });

    test('the signed book lives in the shop\'s save blob beside the omikuji, and an old save loses nothing (#215)', () => {
        visit();
        // a blob from before the palace: everything it holds comes back, and nothing is added until the book is signed
        const before = { v: 4, money: 4321, items: { onigiri: 2, coffee: 1 }, effects: {}, used: { onigiri: 3 }, caught: { koi: 1 },
            energy: 42.5, stamps: { KonbiniMarket1: 1 }, hints: { hungry: 1 }, omikuji: { date: '2025-11-11', i: 2 } };
        const old = shopWith(before);
        assert.strictEqual(old.shop.guestbook, null);
        old.shop.save();
        assert.deepStrictEqual(old.saved(), before, 'saved again exactly as it was');
        // signing adds the one field
        const out = game('PalaceVisit').sign(old.shop.guestbook, '2027-02-20');
        old.shop.guestbook = out.guestbook;
        old.shop.save();
        assert.deepStrictEqual(old.saved(), Object.assign({}, before, { guestbook: { date: '2027-02-20', n: 1 } }));
        // ...and it is read back, with everything else, on the next load
        const again = shopWith(old.saved());
        assert.deepStrictEqual(plain([again.shop.money, again.shop.items, again.shop.used, again.shop.caught, again.shop.energy, again.shop.stamps,
            again.shop.hints, again.shop.omikuji, again.shop.guestbook]),
        [4321, { onigiri: 2, coffee: 1 }, { onigiri: 3 }, { koi: 1 }, 42.5, { KonbiniMarket1: 1 }, { hungry: 1 }, { date: '2025-11-11', i: 2 }, { date: '2027-02-20', n: 1 }]);
        // the oldest blobs, and no blob at all
        const v1 = shopWith({ money: 800, items: { onigiri: 2 } });
        assert.deepStrictEqual(plain([v1.shop.money, v1.shop.items, v1.shop.guestbook, v1.shop.omikuji]), [800, { onigiri: 2 }, null, null]);
        v1.shop.save();
        assert.ok(!('guestbook' in v1.saved()) && v1.saved().v === 4 && v1.saved().money === 800);
        assert.strictEqual(shopWith(null).shop.guestbook, null);
        assert.strictEqual(shopWith({ money: 10, guestbook: { date: 'x', n: 4 } }).shop.guestbook, null);
        assert.ok(src('Shop.js').includes("v: 4, money: this.money"), 'the blob is still v4');
    });

    test('the hall is "Palace Hall" on the bar, short enough to count down on a phone, and the map says it is in Tokyo (#215)', () => {
        const c = cfg();
        assert.strictEqual(c.rooms[KEY].name, 'Palace Hall');
        assert.ok(!Object.entries(c.rooms).some(([k, r]) => k !== KEY && r.name === 'Palace Hall'), 'no other room has the name');
        assert.notStrictEqual(c.rooms[KEY].name, c.rooms.ShrineTokyo1.name);
        // hud-phone-layout.test.js's rule: a name of 11 characters or fewer leaves room for "devhouse 3 soon"
        // on the one-row bar at 667x375 (715 wide: 10 + 16 a character + 10 + "menu" + 10)
        assert.ok(c.rooms[KEY].name.length <= 11);
        assert.ok(10 + 16 * `${c.rooms[KEY].name} | devhouse 3 soon | ¥5,000`.length + 10 + 64 + 10 <= 715);
        assert.strictEqual(game('hudBrief')(c.rooms[KEY].name), 'Palace Hall');
        if (!game('typeof Places !== "undefined"')) vm.runInContext(src('utils/Places.js'), ctx, { filename: 'Places.js' });
        assert.strictEqual(game('Places').whereText(game('decodeConfig')(c), KEY), 'Palace Hall (in Tokyo)');
    });

    test('the palace generator and its art tool are checked, own the door through roomgen, and touch no other room (#215)', () => {
        const check = tool('check_generators.py');
        for (const name of ['generate_palace', 'generate_palace_art']) assert.ok(check.includes(`'${name}'`), name);
        const rg = tool('roomgen.py');
        assert.ok(/PALACE_PREFIX: \('palace', PALACE_DOORS\)/.test(rg) && /PALACE_DOORS = \{'pagoda-floor_0_0': \[\(1, 2\)\]\}/.test(rg), 'OWNED_DOORS');
        assert.ok(/rg\.PALACE_DOORS/.test(tool('generate_palace.py')), 'the generator has door cells of its own');
        const c = cfg(), mark = c.rooms[KEY].palace;
        assert.deepStrictEqual(mark, { host: HOST, doors: c.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY).map((t) => [t.gridX, t.gridY]) });
        // no other generator knows about the hall, and no other room has a door into it
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !/^generate_palace/.test(n))) {
            assert.ok(!/PalaceHall|PALACE_/.test(tool(f)), f);
        }
        assert.deepStrictEqual(Object.entries(c.rooms).filter(([, r]) => (r.transporters || []).some((t) => t.targetRoom === KEY)).map(([k]) => k), [HOST]);
        // the palette was appended to: every palace sprite is in it once, after the shrine's
        const mine = c.tilePalette.map((k, i) => [k, i]).filter(([k]) => k.startsWith('palace-in-'));
        assert.ok(mine.length >= 28 && new Set(mine.map(([k]) => k)).size === mine.length);
        assert.ok(mine[0][1] > c.tilePalette.indexOf('shrine-in-saisen_0_0'));
        // every sprite the art tool registers is on disk at a whole number of cells, and is used by the hall
        const png = require(path.join(GV2, 'tools', 'png'));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith('palace-in-'));
        assert.ok(keys.length >= 30, `${keys.length} palace sprites`);
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
            assert.ok(mine.some(([name]) => name === k), `${k} is drawn but not placed`);
        }
        // a re-run of the generator on a scratch copy changes nothing
        const { spawnSync } = require('child_process');
        const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gamev2-palace-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            const before = fs.readFileSync(path.join(tmp, 'config.json'), 'utf8');
            const run = spawnSync('python3', ['tools/generate_palace.py'], { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
            assert.strictEqual(run.status, 0, run.stderr);
            assert.ok(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8') === before, 'generate_palace.py changed config.json on a re-run');
            // ...and from a sealed palace it builds the same world: seal both doors, drop the hall, run it
            const sealed = JSON.parse(before), host = sealed.rooms[HOST];
            const blank = sealed.tilePalette.indexOf('gk_blank');
            for (const t of host.transporters.filter((x) => x.targetRoom === KEY)) tiles(host, 'Colliders')[`${t.gridX},${t.gridY}`] = blank;
            host.transporters = host.transporters.filter((x) => x.targetRoom !== KEY);
            delete sealed.rooms[KEY];
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(sealed, null, 2));
            const again = spawnSync('python3', ['tools/generate_palace.py'], { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
            assert.strictEqual(again.status, 0, again.stderr);
            assert.deepStrictEqual(JSON.parse(fs.readFileSync(path.join(tmp, 'config.json'), 'utf8')), JSON.parse(before));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });
};
