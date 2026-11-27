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
        assert.strictEqual(world.runtimeRooms().filter(k => /^(Tokyo|Market|Palace|Park)(City)?$/.test(k)).join(), 'TokyoCity');

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
        for (const k of ['Tokyo', 'Market', 'Palace', 'Park']) {
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
        assert.strictEqual(world.npcsIn('TokyoCity').length, ['Tokyo', 'Market', 'Palace', 'Park'].reduce((n, k) => n + world.npcsIn(k).length, 0));

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
    test("a streamed city's tile index is built once and kept across room switches (#175)", () => {
        const sceneFor = (world, run, search) => {
            run('globalThis').window = { location: { search } };
            const sprite = () => {
                const s = { alpha: 1 };
                for (const f of ['setOrigin', 'setScale', 'setDepth', 'setData', 'setTexture', 'setPosition', 'addToDisplayList', 'removeFromDisplayList']) s[f] = () => s;
                s.setAlpha = (a) => { s.alpha = a; return s; };
                s.destroy = () => { s.destroyed = true; };
                return s;
            };
            const scene = {
                GRID_SIZE: 64, config: world.config,
                textures: { exists: (k) => world.exists(k), getFrame: (k) => ({ realWidth: world.cells(k)[0] * 64, realHeight: world.cells(k)[1] * 64 }) },
                getSpriteConfig: (k) => world.config.spriteMetadata[k] || { anchorX: 0.5, anchorY: 0.5 },
                add: { sprite },
                cache: { json: { get: () => null } },
                cameras: { main: { scrollX: 0, scrollY: 0, width: 1280, height: 960, zoom: 1 } },
                player: { sprite: { x: 0, y: 0 } },
            };
            const RoomManager = run('RoomManager');
            const rm = scene.roomManager = new RoomManager(scene);
            rm.rooms = world.roomManager.rooms;
            rm.cities = world.roomManager.cities;
            rm.memberOf = world.roomManager.memberOf;
            rm.indexed = 0;
            const loadLayer = rm.loadLayer;
            rm.loadLayer = function (layer) { rm.indexed++; return loadLayer.call(rm, layer); };
            rm.enter = (room, x, y) => {
                const at = rm.resolve(room, x, y);
                rm.currentRoom = at.room;
                scene.player.sprite.x = at.x * 64 + 32;
                scene.player.sprite.y = at.y * 64 + 32;
                scene.cameras.main.scrollX = scene.player.sprite.x - 640;
                scene.cameras.main.scrollY = scene.player.sprite.y - 480;
                rm.loadFloorTiles();
            };
            return { rm, RoomManager };
        };
        const shape = (rm) => rm.tileRecords.map(r => `${r.key}@${r.gridX},${r.gridY}:${r.depth}:${r.sprite ? 1 : 0}:${r.fade}`).join('|');
        const { world, run } = worldWith(true);
        const { rm, RoomManager } = sceneFor(world, run, '');
        const city = rm.rooms.TokyoCity, layers = city.layers.length;

        rm.enter('Market', 38, 24);
        assert.strictEqual(rm.currentRoom, 'TokyoCity');
        assert.ok(rm.streamed && rm.indexed === layers && rm.tileRecords.length > 15000);
        const records = rm.tileRecords, blocked = rm.blockedCells, chunks = rm.chunks, first = shape(rm);
        const live = rm.liveTiles.size;
        assert.ok(live > 300 && live < 3000, `${live} sprites in view`);
        // somebody stands behind a roof, then the player leaves through a konbini door
        const faded = [...rm.liveTiles][0], sprites = [...rm.liveTiles].map(r => r.sprite);
        faded.fade = 0.4;
        rm.enter('KonbiniMarket1', 8, 8);
        assert.ok(rm.tileRecords !== records && rm.tileRecords.length < 2000 && !rm.streamed);
        assert.ok(sprites.every(s => s.destroyed), "the city's sprites went with it");
        assert.ok(records.every(r => r.sprite === null && r.fade === undefined), 'kept records hold no sprite and no fade');
        const afterKonbini = rm.indexed;
        // back out: the same index, nothing re-indexed, only the view's sprites made again
        rm.enter('Market', 38, 24);
        assert.strictEqual(rm.indexed, afterKonbini, 'no layer was indexed again');
        assert.ok(rm.tileRecords === records && rm.blockedCells === blocked && rm.chunks === chunks);
        assert.strictEqual(shape(rm), first, 'the room is exactly what the first visit built');
        assert.strictEqual(rm.liveTiles.size, live);
        assert.ok([...rm.liveTiles].every(r => !r.sprite.destroyed));
        // ...and what a manager that never kept anything builds (another door, another view)
        rm.enter('Palace', 27, 10);
        const fresh = sceneFor(world, run, '').rm;
        fresh.enter('Palace', 27, 10);
        assert.strictEqual(shape(rm), shape(fresh));
        assert.strictEqual([...rm.blockedCells].join(' '), [...fresh.blockedCells].join(' '));
        assert.strictEqual(rm.indexed, afterKonbini);

        // a map edit, the way the game, the studio and the editor apply one: a layer gets a new
        // tile table / the room a new layer list / the city is stitched again -> rebuilt
        const rebuilt = (why) => {
            const before = rm.indexed;
            rm.enter('Market', 38, 24);
            assert.strictEqual(rm.indexed - before, rm.rooms.TokyoCity.layers.length, why);
            assert.ok(rm.tileRecords !== records, why);
            return rm.tileRecords.length;
        };
        const floor = city.layers.find(l => !l.collision && Object.keys(l.tiles).length > 1000);
        const gone = Object.keys(floor.tiles)[0];
        floor.tiles = Object.assign({}, floor.tiles);
        delete floor.tiles[gone];
        assert.strictEqual(rebuilt('a new tile table'), records.length - 1);
        city.layers = city.layers.slice(0, -1).concat(Object.assign({}, city.layers[city.layers.length - 1]));
        rebuilt('a new layer list');
        rm.rooms.TokyoCity = Object.assign({}, city);
        rebuilt('the city stitched again');
        // a tile changed in place cannot be seen: the editor of it says so
        const kept = rm.tileRecords, other = Object.keys(floor.tiles)[0];
        delete rm.rooms.TokyoCity.layers.find(l => l.tiles === floor.tiles).tiles[other];
        rm.enter('Market', 38, 24);
        assert.ok(rm.tileRecords === kept);
        rm.forgetTileIndex('TokyoCity');
        assert.strictEqual(rebuilt('forgetTileIndex'), kept.length - 1);

        // the rule itself
        const room = rm.rooms.TokyoCity, entry = rm.tileIndexes.get('TokyoCity');
        assert.ok(RoomManager.indexFits(entry, room, true));
        assert.ok(!RoomManager.indexFits(entry, room, false), '?cull=0');
        assert.ok(!RoomManager.indexFits(entry, Object.assign({}, room, { stitched: false }), true));
        assert.ok(!RoomManager.indexFits(undefined, room, true));
        assert.ok(!RoomManager.keepsIndex(rm.rooms.Osaka, false) && !RoomManager.keepsIndex(rm.rooms.KonbiniMarket1, false));

        // ?cull=0: stitched but every sprite made at once - nothing is kept, every entry rebuilds
        const all = sceneFor(world, run, '?cull=0').rm;
        all.enter('Market', 38, 24);
        assert.ok(!all.streamed && all.liveTiles.size === all.tileRecords.length);
        all.enter('KonbiniMarket1', 8, 8);
        const n = all.indexed;
        all.enter('Market', 38, 24);
        assert.strictEqual(all.indexed - n, all.rooms.TokyoCity.layers.length);
        assert.strictEqual(all.tileIndexes.size, 0);

        // ?stitch=0: no city, the districts are ordinary rooms - nothing is kept
        const apart = worldWith(false);
        const sep = sceneFor(apart.world, apart.run, '').rm;
        assert.ok(!sep.rooms.TokyoCity);
        for (const [room, x, y] of [['Market', 38, 24], ['KonbiniMarket1', 8, 8], ['Market', 38, 24], ['Osaka', 20, 20]]) {
            const before = sep.indexed;
            sep.enter(room, x, y);
            assert.strictEqual(sep.currentRoom, room);
            assert.strictEqual(sep.indexed - before, sep.rooms[room].layers.length, room);
        }
        assert.strictEqual(sep.tileIndexes.size, 0);
    });
};
