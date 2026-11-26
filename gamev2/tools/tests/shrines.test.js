// Shrine worship halls (issue #212): tools/generate_shrines.py, tools/generate_shrine_art.py, src/ShrineVisit.js.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, shopWith, worldWith }) => {
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    // src/ShrineVisit.js and src/DayNight.js are not in the runner's list: load them once, here
    const visit = () => {
        if (!game('typeof ShrineVisit !== "undefined"')) vm.runInContext(src('ShrineVisit.js'), ctx, { filename: 'ShrineVisit.js' });
        return game('ShrineVisit');
    };
    // every shrine hall in the world: its host, the cell of its building tile, its roof, its door
    const halls = (c) => Object.entries(c.rooms).flatMap(([host, room]) =>
        Object.entries(tiles(room, 'Collidables')).filter(([, id]) => c.tilePalette[id] === 'shrine-building_0_0').map(([cell]) => {
            const [x, y] = cell.split(',').map(Number);
            const roof = c.tilePalette[tiles(room, 'Tops')[`${x - 1},${y - 2}`]];
            const door = (room.transporters || []).find((t) => t.gridX === x + 1 && t.gridY === y + 4);
            return { host, room, x, y, look: roof === 'shrine-top_0_0' ? 'blue' : 'red', door, doorCell: [x + 1, y + 4] };
        }));
    const WIRED = { Tokyo: 'ShrineTokyo1', Market: 'ShrineMarket1', Park: 'ShrinePark1' };
    const at = (room, c, piece) => Object.entries(room.layers.flatMap((l) => Object.entries(l.tiles)))
        .map(([, [cell, id]]) => [cell, c.tilePalette[id]]).filter(([, key]) => key === piece).map(([cell]) => cell.split(',').map(Number));

    test('a shrine hall is sealed everywhere except its one door cell, which leads into its worship hall (#212)', () => {
        const c = cfg();
        const prefab = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'prefabs', 'shrine.tmj'), 'utf8'));
        const seal = prefab.layers.find((l) => l.name === 'Colliders').data;
        const found = halls(c);
        assert.strictEqual(found.length, 7, 'Tokyo, Machi, Asahikawa, Kanazawa, Market, Park, Fukuoka');
        for (const h of found) {
            const solid = tiles(h.room, 'Colliders'), [dx, dy] = h.doorCell, ox = h.x - 1, oy = h.y - 2;
            // the prefab's own seal, cell for cell: only the door is left out of it
            const open = [];
            seal.forEach((gid, i) => {
                const cell = `${ox + i % prefab.width},${oy + Math.floor(i / prefab.width)}`;
                if (gid && !(cell in solid)) open.push(cell);
            });
            assert.deepStrictEqual(open, [], `${h.host}: the hall is open somewhere other than its door`);
            assert.strictEqual(seal[(dy - oy) * prefab.width + (dx - ox)], 0, 'the door cell is the one the prefab leaves out');
            // no way in through any other cell under the roof or the hall
            const others = (h.room.transporters || []).filter((t) => t !== h.door &&
                t.gridX >= ox && t.gridX < ox + 5 && t.gridY >= oy && t.gridY < oy + 8);
            assert.deepStrictEqual(others, [], `${h.host}: a second transporter in the hall`);
            if (h.host in WIRED) {
                assert.ok(h.door, `${h.host}: the hall has no door`);
                assert.deepStrictEqual([h.door.targetRoom, h.door.hidden], [WIRED[h.host], true]);
                assert.ok(!(`${dx},${dy}` in solid), `${h.host}: the door cell is solid`);
                assert.ok(!(`${dx},${dy + 1}` in solid), `${h.host}: the cell in front of the door is solid`);
            } else if (h.door) {
                // rolled out later: a wired door is always an open one into a Shrine room
                assert.ok(/^Shrine/.test(h.door.targetRoom) && h.door.hidden && !(`${dx},${dy}` in solid), `${h.host}: a half-wired door`);
            }
        }
        assert.deepStrictEqual(found.filter((h) => h.door).map((h) => h.host).filter((k) => k in WIRED).sort(), ['Market', 'Park', 'Tokyo']);
    });

    test('nobody stands on a shrine door or the cell in front of it, on any date (#212)', () => {
        const c = cfg();
        for (const h of halls(c).filter((x) => x.door)) {
            const [dx, dy] = h.doorCell;
            const inWay = h.room.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
                .filter(([, s]) => s.gridX === dx && (s.gridY === dy || s.gridY === dy + 1))
                .map(([date]) => `${n.name} ${date}`));
            assert.deepStrictEqual(inWay, [], `${h.host}: in the doorway`);
        }
    });

    test('each worship hall is the hall of its roof: blue is cypress and indigo, red is vermilion, mirror images of each other (#212)', () => {
        const c = cfg();
        const want = { Tokyo: 'blue', Market: 'red', Park: 'red' };
        const sides = {};
        for (const h of halls(c).filter((x) => x.host in WIRED)) {
            assert.strictEqual(h.look, want[h.host], `${h.host}: roof`);
            const room = c.rooms[WIRED[h.host]], look = h.look, other = look === 'red' ? 'blue' : 'red';
            assert.deepStrictEqual([room.interior, room.lanternLight, room.shopEnabled, room.name],
                [true, true, false, { Tokyo: 'Palace Shrine' }[h.host] || `Shrine · ${h.room.name || h.host}`]);
            // a hall is named for its town by the town's DISPLAY name ("Shrine · Asakusa", room key Market);
            // the palace's hall has a name of its own, because "Imperial Palace shrine" is too long for a
            // phone's one-row HUD bar - and stays a standard hall: only Kushida and Dazaifu are large (#219)
            assert.strictEqual(room.worldWidth / 64, 20, `${h.host}: a standard hall`);
            const keys = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
            for (const piece of ['honden', 'lattice', 'pillar', 'lanterns', 'wall', 'wall-curtain', 'wall-shoji', 'floor-a', 'floor-b', 'runner-l']) {
                assert.ok(keys.has(`shrine-in-${piece}-${look}_0_0`), `${h.host}: no ${piece} in ${look}`);
                assert.ok(!keys.has(`shrine-in-${piece}-${other}_0_0`), `${h.host}: a ${other} ${piece} in a ${look} hall`);
            }
            for (const piece of ['saisen', 'bell', 'shimenawa', 'rope', 'ema', 'omikuji', 'omikuji-rail', 'counter', 'sakaki',
                'lanterns-floor', 'drum', 'zabuton', 'tatami-l', 'doorlight']) {
                assert.ok(keys.has(`shrine-in-${piece}_0_0`), `${h.host}: no ${piece}`);
            }
            const mid = room.worldWidth / 64 / 2;
            sides[look] = at(room, c, 'shrine-in-counter_0_0')[0][0] < mid ? 'west' : 'east';
            // the red hall has a second pair of pillars by the offering box; the blue one stands lamps there
            assert.strictEqual(at(room, c, `shrine-in-pillar-${look}_0_0`).length, look === 'red' ? 4 : 2);
            assert.strictEqual(at(room, c, 'shrine-in-lanterns-floor_0_0').length, look === 'red' ? 2 : 4);
            // depth: a pillar is solid at its foot only, so its shaft is walked behind
            const solid = tiles(room, 'Colliders');
            for (const [x, y] of at(room, c, `shrine-in-pillar-${look}_0_0`)) {
                assert.deepStrictEqual([`${x},${y}` in solid, `${x},${y + 1}` in solid, `${x},${y + 2}` in solid], [false, false, true]);
            }
            // the railing stands a row in front of the sanctuary and is drawn over it (feet one row lower)
            const [hx, hy] = at(room, c, `shrine-in-honden-${look}_0_0`)[0];
            const rail = at(room, c, `shrine-in-lattice-${look}_0_0`);
            assert.ok(rail.length >= 8 && rail.every(([, y]) => y + 2 === hy + 3 + 1), 'the railing is one row in front of the sanctuary');
            assert.ok(rail.every(([x, y]) => `${x},${y + 1}` in solid), 'the railing is solid');
            // the hanging pieces sort in front of what stands behind them
            assert.ok(c.spriteMetadata['shrine-in-shimenawa_0_0'].depthBias > 0 && c.spriteMetadata['shrine-in-bell_0_0'].depthBias > 0);
            assert.ok(c.spriteMetadata['shrine-in-doorlight_0_0'].depthBias < 0, 'the daylight lies flat');
            // every lantern is one the night halo finds (DayNight.buildGlows)
            assert.ok([...keys].filter((k) => /lanterns/.test(k)).every((k) => /lamp-post|-lanterns/.test(k)));
        }
        assert.deepStrictEqual(sides, { blue: 'west', red: 'east' });
    });

    test('you walk in by the door, up to the offering box, the fortune stand and the counter, and out to the cell in front (#212)', () => {
        const { world, config } = worldWith(false);
        for (const [host, key] of Object.entries(WIRED)) {
            const door = config.rooms[host].transporters.find((t) => t.targetRoom === key);
            world.enter(host, door.gridX, door.gridY + 1);
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, key, `${host}: the door`);
            const here = world.here();
            assert.deepStrictEqual([here.x, here.y], [door.targetX, door.targetY]);
            assert.ok(!config.rooms[key].transporters.some((t) => t.gridX === here.x && t.gridY === here.y), 'arrives off the exit mats');
            // bump each thing from a cell that can be walked to
            const things = world.interactions().filter((i) => i.group === 'shrine');
            assert.deepStrictEqual(plain(things.map((i) => i.kind).sort()), ['offering', 'omikuji']);
            for (const i of things) {
                const route = world.path(i.x, i.y + i.h);
                assert.ok(route, `${key}: no way to the front of the ${i.kind}`);
                for (const dir of route) world.step(dir);
                const bump = world.interactionAt(i.x, i.y + i.h - 1);
                assert.strictEqual(bump && bump.kind, i.kind);
                assert.ok(/offering|fortune/.test(world.describe(bump)));
            }
            // nothing in a shrine is a shop fixture (the counter is the miko's, not a konbini's)
            assert.deepStrictEqual(plain(world.interactions().filter((i) => i.group === 'shop')), []);
            const lint = world.lint(key);
            assert.deepStrictEqual(plain([lint.errors, lint.warns]), [{}, {}], `${key}: lint`);
            // and out again: both mats lead to the cell in front of the door
            for (const t of config.rooms[key].transporters) {
                assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY, t.hidden], [host, door.gridX, door.gridY + 1, true]);
            }
            const mat = config.rooms[key].transporters[0];
            const back = world.path(mat.gridX, mat.gridY - 1);
            for (const dir of back) world.step(dir);
            const out = world.step('s');
            assert.strictEqual(out.transported && out.transported.to, host);
            assert.deepStrictEqual([world.here().x, world.here().y], [door.gridX, door.gridY + 1]);
        }
    });

    test('the shrine doors are doorways of the stitched city, so wanderers keep off the cells in front (#212)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        for (const [host, key] of Object.entries(WIRED)) {
            const t = rm.rooms.TokyoCity.transporters.filter((x) => x.targetRoom === key);
            assert.strictEqual(t.length, 1, `${host}: one door in the city`);
            const local = world.config.rooms[host].transporters.find((x) => x.targetRoom === key);
            const cell = rm.resolve(host, local.gridX, local.gridY);
            assert.deepStrictEqual([t[0].gridX, t[0].gridY], [cell.x, cell.y]);
        }
    });

    test('an offering costs five yen, rings the bell and says a blessing; an empty wallet only bows (#212)', () => {
        const V = visit();
        const ok = V.offer(5000, 0);
        assert.deepStrictEqual([ok.ok, ok.money], [true, 4995]);
        assert.ok(ok.line.startsWith('¥5 in the box. The bell rings') && ok.line.endsWith(V.BLESSINGS[0]), ok.line);
        assert.ok(V.offer(5, 0.999).line.endsWith(V.BLESSINGS[V.BLESSINGS.length - 1]));
        assert.strictEqual(V.offer(5, 0.5).money, 0);
        const broke = V.offer(4, 0.5);
        assert.deepStrictEqual([broke.ok, broke.money], [false, 4]);
        assert.ok(/bow/.test(broke.line));
        // every line fits one toast: the longest the shop already shows is about 90 characters
        for (let i = 0; i < V.BLESSINGS.length; i++) assert.ok(V.offer(100, i / V.BLESSINGS.length).line.length <= 90);
    });

    test('an omikuji is drawn once a game day, costs a hundred yen, and is read back until the date changes (#212)', () => {
        const V = visit();
        assert.strictEqual(V.FORTUNES.reduce((n, f) => n + f.weight, 0), 100);
        assert.deepStrictEqual([V.FORTUNES[0].means, V.FORTUNES[V.FORTUNES.length - 1].means], ['great blessing', 'great curse']);
        assert.deepStrictEqual([0, 0.159, 0.16, 0.5, 0.97, 0.999, 1].map(V.rankFor), [0, 0, 1, 2, 6, 6, 6]);
        const first = V.fortune(null, '2025-11-11', 5000, 0);
        assert.deepStrictEqual(plain([first.fresh, first.i, first.money, first.omikuji]), [true, 0, 4900, { date: '2025-11-11', i: 0 }]);
        assert.ok(/Dai-kichi \(great blessing\)/.test(first.line));
        // the same day: the same slip, whatever the roll, and no charge
        const again = V.fortune(first.omikuji, '2025-11-11', 4900, 0.99);
        assert.deepStrictEqual([again.fresh, again.i, again.money, again.omikuji], [false, 0, 4900, undefined]);
        assert.ok(/^Drawn already today: Dai-kichi/.test(again.line));
        // another day (time travel either way): a new draw
        const next = V.fortune(first.omikuji, '2025-11-10', 4900, 0.99);
        assert.deepStrictEqual([next.fresh, next.i, next.money], [true, 6, 4800]);
        // not enough yen: nothing drawn, nothing saved
        const broke = V.fortune(null, '2025-11-11', 99, 0);
        assert.deepStrictEqual([broke.fresh, broke.money, broke.omikuji], [false, 99, undefined]);
        // junk in the save blob is no fortune
        for (const junk of [undefined, 'x', {}, { date: '2025-11-11' }, { date: 'today', i: 1 }, { date: '2025-11-11', i: 7 }, { date: '2025-11-11', i: -1 }]) {
            assert.strictEqual(V.saved(junk), null);
        }
        for (const f of V.FORTUNES) assert.ok(`Drawn already today: ${f.rank} (${f.means}). ${f.text}`.length <= 96, f.rank);
    });

    test("the day's omikuji lives in the shop's save blob, and an old blob without one still loads (#212)", () => {
        visit();
        const old = shopWith({ v: 3, money: 1234, items: { coffee: 1 } });
        assert.deepStrictEqual([old.shop.money, old.shop.omikuji], [1234, null]);
        old.shop.save();
        assert.ok(!('omikuji' in old.saved()), 'nothing is added until a fortune is drawn');
        old.shop.omikuji = { date: '2025-11-11', i: 3 };
        old.shop.save();
        assert.deepStrictEqual(old.saved().omikuji, { date: '2025-11-11', i: 3 });
        const again = shopWith(old.saved());
        assert.deepStrictEqual(plain([again.shop.money, again.shop.omikuji, again.shop.items.coffee]), [1234, { date: '2025-11-11', i: 3 }, 1]);
        assert.strictEqual(shopWith({ money: 10, omikuji: { date: 'x', i: 99 } }).shop.omikuji, null);
        // the v4 blob (energy meter and stamp card, #209): a v3 save with a fortune gains a full meter and an
        // empty card and keeps the fortune; a v4 save keeps its energy, stamps and hints when a fortune is added
        const v3 = shopWith({ v: 3, money: 800, items: { onigiri: 2 }, omikuji: { date: '2025-11-11', i: 2 } });
        v3.shop.save();
        assert.deepStrictEqual(v3.saved(), { v: 4, money: 800, items: { onigiri: 2 }, effects: {}, used: {}, caught: {},
            energy: 100, stamps: {}, hints: {}, omikuji: { date: '2025-11-11', i: 2 } });
        const v4 = shopWith({ v: 4, money: 800, items: {}, energy: 37.5, stamps: { KonbiniPark1: 1 }, hints: { low: 1 } });
        assert.strictEqual(v4.shop.omikuji, null);
        const drawn = game('ShrineVisit').fortune(v4.shop.omikuji, '2027-02-20', v4.shop.money, 0.5);
        Object.assign(v4.shop, { money: game('ShrineVisit').offer(drawn.money, 0).money, omikuji: drawn.omikuji });
        v4.shop.save();
        assert.deepStrictEqual(v4.saved(), { v: 4, money: 695, items: {}, effects: {}, used: {}, caught: {},
            energy: 37.5, stamps: { KonbiniPark1: 1 }, hints: { low: 1 }, omikuji: { date: '2027-02-20', i: drawn.i } });
        const back = shopWith(v4.saved()).shop;
        assert.deepStrictEqual(plain([back.energy, back.stamps, back.hints, back.omikuji]),
            [37.5, { KonbiniPark1: 1 }, { low: 1 }, { date: '2027-02-20', i: drawn.i }]);
        // an offering or a fortune is not a purchase: ShrineVisit touches the wallet and the fortune, nothing else
        const code = src('ShrineVisit.js');
        assert.ok(!/stamp|energy|\.buy\(|\.use\(|Energy\.|Stamps\./i.test(code.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '')), 'ShrineVisit reaches past the wallet');
        // a fortune this build does not have (an index past the list) is kept in the blob but never read back
        assert.strictEqual(game('ShrineVisit').saved(shopWith({ money: 10, omikuji: { date: '2025-11-11', i: 99 } }).shop.omikuji), null);
    });

    test('the offering box and the fortune stand are rules of the Interactions table, in any room; the rail and the counter are not (#212)', () => {
        const I = worldWith(false).run('Interactions');
        const hall = { interior: true, shopEnabled: false, lanternLight: true };
        assert.deepStrictEqual(plain(I.match('shrine-in-saisen_0_0', hall)), { kind: 'offering', group: 'shrine', footprint: true });
        assert.deepStrictEqual(plain(I.match('shrine-in-omikuji_0_0', hall)), { kind: 'omikuji', group: 'shrine', footprint: true });
        for (const key of ['shrine-in-omikuji-rail_0_0', 'shrine-in-counter_0_0', 'shrine-in-ema_0_0', 'shrine-in-bell_0_0']) {
            assert.strictEqual(I.match(key, hall), null, key);
        }
        // one call site, after the shop's, and no key of its own
        const scene = src('GameScene.js'), code = src('ShrineVisit.js');
        assert.ok(/this\.shrineVisit\.check\(targetGridX, targetGridY\)/.test(scene));
        assert.ok(!/addKey|KeyCodes|pointerdown/.test(code), 'ShrineVisit binds no input');
        assert.ok(/interactionAt\(gridX, gridY, 'shrine'\)/.test(code));
        assert.ok(src('../index.html').includes("'src/ShrineVisit.js'"));
    });

    test('one offering per bump: a key held against the box pays once, until it is let go (#220)', () => {
        const S = visit(), fresh = S.fresh;
        // the first bump, a bump of another cell, and a bump after the key was let go are new ones
        assert.strictEqual(fresh(null, '10,7', 5000), true);
        assert.strictEqual(fresh({ cell: '10,7', at: 5000 }, '11,7', 5016), true, 'the next cell of the box is another bump');
        assert.strictEqual(fresh({ cell: '10,7', at: 5000 }, '10,7', 5000 + S.HELD_MS + 1), true, 'released and bumped again');
        // a held key bumps every frame: never new, at 60 or at 10 frames a second
        assert.strictEqual(fresh({ cell: '10,7', at: 5000 }, '10,7', 5016), false);
        assert.strictEqual(fresh({ cell: '10,7', at: 5000 }, '10,7', 5100), false);
        assert.ok(S.HELD_MS >= 150 && S.HELD_MS <= 400, 'longer than a slow frame, shorter than letting go and pressing again');
        // the visit itself, as check() runs it: ten seconds of a held key at 60 fps is one offering, not seven
        const spend = (frames, gapAt) => {
            let bump = null, money = 100, now = 0;
            for (let i = 0; i < frames; i++) {
                now += gapAt && gapAt.includes(i) ? 400 : 1000 / 60;
                const isNew = fresh(bump, '10,7', now);
                bump = { cell: '10,7', at: now };
                if (isNew) money = S.offer(money, 0).money;
            }
            return 100 - money;
        };
        assert.strictEqual(spend(600), S.OFFERING, 'held for ten seconds');
        assert.strictEqual(spend(600, [200, 400]), 3 * S.OFFERING, 'let go and bumped again twice');
        // check() keeps the last bump whether or not it paid, and has no timer left to pay by
        const code = src('ShrineVisit.js');
        assert.ok(code.includes("const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell, scene.time.now);"));
        assert.ok(code.includes('this.bump = { cell, at: scene.time.now, dx: Math.sign(gridX - from.gridX), dy: Math.sign(gridY - from.gridY) };\n        if (!fresh) return true;'));
        assert.ok(!/COOLDOWN/.test(code), 'the 1.5 s cooldown that paid a held key again is gone');
    });

    test('a menu opened and closed with the key still held is the same bump: no second offering (#220)', () => {
        const S = visit(), fresh = S.fresh, carried = S.carried;
        const UP = { x: 0, y: -1 }, NONE = { x: 0, y: 0 }, LEFT = { x: -1, y: 0 };
        const bump = { cell: '10,7', at: 5000, dx: 0, dy: -1 };
        // while the direction that bumped is down the bump's time moves with the clock; let go, or turned, it ages
        assert.deepStrictEqual(plain(carried(bump, 5016, UP)), { cell: '10,7', at: 5016, dx: 0, dy: -1 });
        assert.strictEqual(carried(bump, 5016, NONE), bump);
        assert.strictEqual(carried(bump, 5016, LEFT), bump);
        assert.strictEqual(carried(bump, 5016, { x: -1, y: -1 }), bump, 'up and left together is another way to be heading');
        assert.strictEqual(carried(null, 5016, UP), null);
        assert.strictEqual(carried(bump, 5016, null), bump);
        assert.strictEqual(carried({ cell: '10,7', at: 5000, dx: 0, dy: 0 }, 5016, NONE).at, 5000, 'a bump with no direction is never carried');
        assert.strictEqual(carried(bump, 5000 + S.HELD_MS + 1, UP), bump, 'a bump let go for that long is over: the key coming down again does not revive it');
        // the game's frames: bumps while the player has the input, none while the menu has it (frames
        // `menu[0]`..`menu[1]`), and the key down for the frames of `held`
        const spend = (frames, menu, held, useHold = true) => {
            let last = null, money = 100, now = 0;
            for (let i = 0; i < frames; i++) {
                now += 1000 / 60;
                const down = held(i), inMenu = i >= menu[0] && i < menu[1];
                if (down && !inMenu) {
                    const isNew = fresh(last, '10,7', now);
                    last = { cell: '10,7', at: now, dx: 0, dy: -1 };
                    if (isNew) money = S.offer(money, 0).money;
                }
                if (useHold) last = carried(last, now, down ? UP : NONE);
            }
            return 100 - money;
        };
        const always = () => true;
        assert.strictEqual(spend(600, [120, 300], always), S.OFFERING, 'the menu open for three seconds, Up held throughout: one offering');
        assert.strictEqual(spend(600, [120, 300], always, false), 2 * S.OFFERING, 'the bug: without the carry the box is paid again as the menu closes');
        assert.strictEqual(spend(600, [120, 300], (i) => i < 200 || i >= 280), 2 * S.OFFERING, 'let go inside the menu and pressed again: a new bump');
        assert.strictEqual(spend(600, [0, 0], (i) => i < 200 || i >= 230), 2 * S.OFFERING, 'let go and bumped again with no menu: as before');
        assert.strictEqual(spend(600, [0, 0], always), S.OFFERING);
        // the heading is read off the keys and the touch pad every frame, whoever owns the input
        if (!game('typeof InputHandler !== "undefined"')) vm.runInContext(src('systems/InputHandler.js'), ctx, { filename: 'InputHandler.js' });
        const H = game('InputHandler.headingOf');
        assert.deepStrictEqual(plain([H({ up: true }), H({ down: true, right: true }), H({ left: true, right: true }), H({})]),
            [{ x: 0, y: -1 }, { x: 1, y: 1 }, { x: 0, y: 0 }, { x: 0, y: 0 }]);
        const scene = src('GameScene.js'), input = src('systems/InputHandler.js');
        assert.ok(scene.includes('this.inputHandler.handleInput();\n        // a key still held against the offering box is the same bump, menu or no menu\n        if (this.shrineVisit) this.shrineVisit.hold(this.inputHandler.heading());'));
        assert.ok(/heading\(\) \{[\s\S]{0,400}touchControls\.state/.test(input), 'the touch pad counts as a held key');
        assert.ok(src('ShrineVisit.js').includes('if (this.bump) this.bump = ShrineVisit.carried(this.bump, this.scene.time.now, heading);'));
    });

    test('a lantern-lit interior dims at night and lights its lanterns; every other interior ignores the hour (#212)', () => {
        if (!game('typeof DayNight !== "undefined"')) vm.runInContext(src('DayNight.js'), ctx, { filename: 'DayNight.js' });
        const D = game('DayNight');
        const hall = { interior: true, lanternLight: true }, konbini = { interior: true }, street = {};
        assert.deepStrictEqual(['dawn', 'day', 'dusk', 'night'].map((p) => D.gradeFor(hall, p)), [null, null, null, D.LANTERN_NIGHT]);
        assert.strictEqual(D.LANTERN_NIGHT.lights, true);
        assert.deepStrictEqual(['dawn', 'day', 'dusk', 'night'].map((p) => D.gradeFor(konbini, p)), [null, null, null, null]);
        assert.deepStrictEqual(['dawn', 'day', 'dusk', 'night'].map((p) => D.gradeFor(street, p)), [D.GRADES.dawn, null, D.GRADES.dusk, D.GRADES.night]);
        assert.strictEqual(D.gradeFor(undefined, 'night'), D.GRADES.night);
    });

    test('a worship hall says whose it is, and a town rebuild keeps its door beside the house doors (#212, #208)', () => {
        const c = cfg();
        for (const [host, key] of Object.entries(WIRED)) {
            const mark = c.rooms[key].shrine, door = c.rooms[host].transporters.find((t) => t.targetRoom === key);
            assert.deepStrictEqual([mark.host, mark.door], [host, [door.gridX, door.gridY]], key);
            assert.ok(['red', 'blue'].includes(mark.look) && mark.size === 'standard', key);
        }
        // Asahikawa is a generated town with a sealed hall and three houses: wire its hall in a scratch
        // copy, then rebuild the town - its generator stamps the hall and the houses sealed again
        const { spawnSync } = require('child_process');
        const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gamev2-shrines-'));
        try {
            for (const d of ['tools', 'assets', 'tiled']) fs.symlinkSync(path.join(GV2, d), path.join(tmp, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(tmp, 'config.json'));
            const read = () => fs.readFileSync(path.join(tmp, 'config.json'), 'utf8');
            const python = (...args) => {
                const run = spawnSync('python3', args, { cwd: tmp, encoding: 'utf8', maxBuffer: 1 << 26 });
                assert.strictEqual(run.status, 0, `${args.join(' ')}: ${run.stderr}`);
            };
            const doors = (text) => JSON.parse(text).rooms.Asahikawa.transporters.map((t) => t.targetRoom);
            assert.ok(!doors(read()).some((r) => /^Shrine/.test(r)), 'Asahikawa is wired: pick another town for this test');
            python('tools/generate_shrines.py', 'Asahikawa');
            const wired = read(), w = JSON.parse(wired), hall = w.rooms.ShrineAsahikawa1.shrine;
            assert.deepStrictEqual(doors(wired), ['AsahikawaStation', 'HouseAsahikawa1', 'HouseAsahikawa2', 'HouseAsahikawa3', 'ShrineAsahikawa1']);
            assert.ok(!(hall.door.join(',') in tiles(w.rooms.Asahikawa, 'Colliders')), 'the door was not opened');
            for (const args of [['tools/generate_asahikawa.py'], ['tools/generate_shrines.py'], ['tools/generate_houses.py']]) {
                python(...args);
                assert.ok(read() === wired, `${args[0]} changed config.json: the shrine door or a house door was not kept`);
            }
            // the hall's room gone (or no longer a hall's): the town rebuild leaves the hall sealed, the houses open
            const gone = JSON.parse(wired);
            delete gone.rooms.ShrineAsahikawa1.shrine;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(gone, null, 2));
            python('tools/generate_asahikawa.py');
            const after = JSON.parse(read());
            assert.deepStrictEqual(doors(read()), ['AsahikawaStation', 'HouseAsahikawa1', 'HouseAsahikawa2', 'HouseAsahikawa3']);
            assert.ok(hall.door.join(',') in tiles(after.rooms.Asahikawa, 'Colliders'), 'an unowned door stayed open');
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('the shrine generator and both art tools are checked, and a town rebuild keeps a shrine door (#212)', () => {
        const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
        const check = tool('check_generators.py');
        for (const name of ['generate_shrines', 'generate_shrine_art', 'extract_shrine']) assert.ok(check.includes(`'${name}'`), name);
        // one door-keeping mechanism in roomgen for houses and shrines: a row of OWNED_DOORS each
        const rg = tool('roomgen.py');
        assert.ok(/SHRINE_PREFIX: \('shrine', SHRINE_DOORS\)/.test(rg) && /HOUSE_PREFIX: \('house', /.test(rg), 'OWNED_DOORS');
        assert.ok(!/keep_interior_doors|KEPT_DOORS/.test(rg) && (rg.match(/^def keep_\w+/gm) || []).length === 1, 'a second door keeper');
        assert.ok(/rg\.SHRINE_DOORS/.test(tool('generate_shrines.py')), 'the generator has door cells of its own');
        // no town generator knows about a shrine room
        for (const f of fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^generate_.*\.py$/.test(n) && !/^generate_shrine/.test(n))) {
            assert.ok(!/Shrine[A-Z]|SHRINE_/.test(tool(f)), f);
        }
        // every sprite the art tools register is on disk, at a whole number of cells
        const c = cfg(), png = require(path.join(GV2, 'tools', 'png'));
        const keys = Object.keys(c.spriteMetadata).filter((k) => k.startsWith('shrine-in-'));
        assert.ok(keys.length >= 45, `${keys.length} shrine interior sprites`);
        for (const k of keys) {
            const { width, height } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', k + '.png')));
            assert.ok(width % 64 === 0 && height % 64 === 0, `${k}: ${width}x${height}`);
        }
    });
};
