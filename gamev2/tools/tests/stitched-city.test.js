module.exports = ({ test, assert, fs, path, GV2, game, worldWith }) => {
    test("Palace's east road crosses into Market and back when the city is not stitched", () => {
        // the road over the east level crossing (54..56) needs its own seam transporters, like the west road's
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const seam = (from, x, y) => rooms[from].transporters.find(t => t.gridX === x && t.gridY === y);
        for (const x of [0, 1, 54, 55, 56]) {
            assert.deepStrictEqual(seam('Palace', x, 0), { gridX: x, gridY: 0, hidden: true, targetRoom: 'Market', targetX: x, targetY: 46 });
            assert.deepStrictEqual(seam('Market', x, 47), { gridX: x, gridY: 47, hidden: true, targetRoom: 'Palace', targetX: x, targetY: 1 });
        }
    });

    test('play.js and the studio model the stitched Tokyo the game plays', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        assert.strictEqual(rm.currentRoom, 'TokyoCity');
        assert.deepStrictEqual([world.here().room, world.here().x, world.here().y, world.here().city], ['Tokyo', 29, 38, 'TokyoCity']);
        assert.deepStrictEqual(world.state().room, 'Tokyo', 'sessions are saved in district cells');
        assert.strictEqual(world.runtimeRooms().filter(k => /^(Tokyo|Market|Palace|Park|Machi)(City)?$/.test(k)).join(), 'TokyoCity');

        // colliders block (the model once walked through them): the vending machine two cells west
        assert.ok(world.step('w').moved);
        const bump = world.step('w');
        assert.strictEqual(bump.moved, false);
        assert.strictEqual(bump.interaction.kind, 'vending');

        // one walk from Tokyo into Market: no teleport, the district changes underfoot
        const to = rm.resolve('Market', 5, 24);
        const steps = world.path(to.x, to.y);
        assert.ok(steps && steps.length > 20);
        const crossings = [];
        for (const dir of steps) {
            const r = world.step(dir);
            assert.ok(r.moved && !r.transported, 'walked, never teleported');
            if (r.crossed) crossings.push(r.crossed.from + '>' + r.crossed.to);
        }
        assert.strictEqual(crossings.join(), 'Tokyo>Market');
        assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 5, 24]);
        // the woodland between the districts is scenery
        assert.strictEqual(world.canStep(to.x, to.y, to.x, -1), false);
        assert.strictEqual(rm.checkBoundary(10, 80), false);

        // check + lint run on the stitched room, and still on each district
        const { problems, reach } = world.survey(null, { npcs: false });
        assert.strictEqual(problems.length, 0, JSON.stringify(problems));
        const byRoom = world.reachByRoom(reach);
        for (const k of ['Tokyo', 'Market', 'Palace', 'Park', 'Machi']) {
            assert.ok(byRoom[k].length > 300, k);
            assert.strictEqual(JSON.stringify(world.lint(k).errors), '{}', k);
        }
        const city = world.lint('TokyoCity');
        assert.strictEqual(JSON.stringify(city.errors), '{}');
        assert.deepStrictEqual([city.width, city.height], [rm.cities.TokyoCity.width, rm.cities.TokyoCity.height]);
        // no open cell of the city is cut off (#196): the yard behind the Tokyo shrine hall and the
        // floor under Market's wing roofs are solid, and lint does not call those colliders stray
        const solid = new Set(), pockets = [];
        for (const l of rm.rooms.TokyoCity.layers) if (l.collision) for (const xy of Object.keys(l.tiles)) solid.add(xy);
        for (const l of rm.rooms.TokyoCity.layers) {
            if (l.name !== 'Floor') continue;
            for (const xy of Object.keys(l.tiles)) {
                const [x, y] = xy.split(',').map(Number);
                if (!solid.has(xy) && rm.checkBoundary(x, y, 'TokyoCity') && !reach.TokyoCity.has(xy)) pockets.push(world.spot('TokyoCity', x, y));
            }
        }
        assert.deepStrictEqual(pockets, []);
        assert.strictEqual(JSON.stringify(city.warns), '{}');
        assert.ok(world.drawOrder('TokyoCity').some(t => /^tree-3-top/.test(t.key)), 'the woods are part of the render');
        assert.ok(world.npcsIn('TokyoCity').every(n => n.homeRoom && rm.checkBoundary(n.gridX, n.gridY, 'TokyoCity')));
        assert.strictEqual(world.npcsIn('TokyoCity').length, ['Tokyo', 'Market', 'Palace', 'Park', 'Machi'].reduce((n, k) => n + world.npcsIn(k).length, 0));

        // --stitch=0: the five rooms, joined by seam teleports, as ?stitch=0 plays them
        const legacy = worldWith(false).world;
        assert.strictEqual(legacy.roomManager.currentRoom, 'Tokyo');
        assert.strictEqual(legacy.here().city, null);
        assert.strictEqual(Object.keys(legacy.roomManager.cities).length, 0);
        legacy.enter('Tokyo', 57, 22);
        assert.strictEqual(JSON.stringify(legacy.step('e').transported), '{"from":"Tokyo","to":"Market"}');
        assert.strictEqual(legacy.survey(null, { npcs: false }).problems.length, 0);
        // both agree on what can be reached, district by district
        const legacyReach = legacy.reachByRoom(legacy.survey(null, { npcs: false }).reach);
        for (const k of Object.keys(byRoom)) assert.strictEqual(Array.from(legacyReach[k]).sort().join(' '), Array.from(byRoom[k]).sort().join(' '), k);
    });

    test('a cell two districts share is walkable by the later district\'s map', () => {
        // the same case tools/test_blog_to_npc.py makes for the python port: Palace is listed
        // after Market, so a collider on Palace's copy of their shared row closes that cell
        const base = worldWith(true).world;
        const palace = base.roomManager.memberOf.Palace.member, market = base.roomManager.memberOf.Market.member;
        const open = new Set(base.reachByRoom(base.survey(null, { npcs: false }).reach).Market);
        const shared = base.reachByRoom(base.survey(null, { npcs: false }).reach).Palace.map(c => c.split(',').map(Number))
            .map(([x, y]) => [x, y, x + palace.x - market.x, y + palace.y - market.y])
            .find(([, , mx, my]) => open.has(mx + ',' + my));
        assert.ok(shared, 'Market and Palace share a walkable cell');
        const cut = worldWith(true, (config) => {
            config.rooms.Palace.layers.find(l => l.collision).tiles[shared[0] + ',' + shared[1]] = 'gk_blank';
        }).world;
        const after = cut.reachByRoom(cut.survey(null, { npcs: false }).reach);
        assert.ok(!after.Market.includes(shared[2] + ',' + shared[3]));
        assert.ok(!after.Palace.includes(shared[0] + ',' + shared[1]));
        // ...while Market's own collider there changes nothing: its tiles in that cell are left out
        const kept = worldWith(true, (config) => {
            config.rooms.Market.layers.find(l => l.collision).tiles[shared[2] + ',' + shared[3]] = 'gk_blank';
        }).world;
        assert.ok(kept.reachByRoom(kept.survey(null, { npcs: false }).reach).Market.includes(shared[2] + ',' + shared[3]));
    });
};
