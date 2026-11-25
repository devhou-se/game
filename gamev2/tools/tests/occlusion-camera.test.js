module.exports = ({ test, assert, path, game, worldWith }) => {
    test('a bump looks its cell up in an index built once per room load', () => {
        const { world, run } = worldWith(true);
        const Interactions = run('Interactions'), Shop = run('Shop');
        const opts = { sizeOf: (key) => world.cells(key), venues: Shop.VENUES };
        let cells = 0, hits = 0;
        for (const key of ['TokyoCity', 'KonbiniMarket1', 'Izakaya', 'Osaka']) {
            const room = world.roomManager.rooms[key], roomConfig = world.config.rooms[key] || {};
            const index = Interactions.index(room, roomConfig, opts);
            // find() scans every tile of the room per call: use it as written for the small rooms and
            // around every interaction; elsewhere compare against its definition (the first of all()
            // covering the cell)
            const all = Interactions.all(room, roomConfig, opts);
            const small = room.worldWidth * room.worldHeight < 64 * 64 * 800;
            for (let y = 0; y < room.worldHeight / 64; y++) {
                for (let x = 0; x < room.worldWidth / 64; x++) {
                    const near = small || all.some(i => i.group !== 'pond' && x >= i.x - 1 && x <= i.x + i.w && y >= i.y - 1 && y <= i.y + i.h);
                    for (const group of ['shop', 'pond', 'clock', 'drinking-game']) {
                        const scan = near ? Interactions.find(room, roomConfig, x, y, Object.assign({ group }, opts))
                            : all.find(i => i.group === group && x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h) || null;
                        assert.strictEqual(JSON.stringify(Interactions.lookup(index, x, y, group)), JSON.stringify(scan), `${key} ${x},${y} ${group}`);
                        if (scan) hits++;
                    }
                    assert.strictEqual(JSON.stringify(Interactions.lookup(index, x, y)),
                        JSON.stringify(all.find(i => x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h) || null));
                    cells++;
                }
            }
        }
        assert.ok(cells > 15000 && hits > 100, `${hits} interactions over ${cells} cells`);

        // RoomManager.interactionAt: built on the first bump, kept until the room's tiles are reloaded
        const rm = world.roomManager;
        rm.scene.textures = { exists: (k) => world.exists(k), get: (k) => ({ getSourceImage: () => ({ width: world.cells(k)[0] * 64, height: world.cells(k)[1] * 64 }) }) };
        let built = 0;
        const index = Interactions.index;
        Interactions.index = function () { built++; return index.apply(this, arguments); };
        const vending = rm.resolve('Tokyo', 27, 38);
        assert.strictEqual(rm.interactionAt(vending.x, vending.y, 'shop').kind, 'vending');
        assert.strictEqual(rm.interactionAt(vending.x, vending.y, 'clock'), null);
        assert.strictEqual(rm.interactionAt(vending.x + 1, vending.y, 'shop'), null);
        for (let i = 0; i < 50; i++) rm.interactionAt(i, i);
        assert.strictEqual(built, 1);
        rm.clearFloorTiles();
        rm.interactionAt(vending.x, vending.y, 'shop');
        assert.strictEqual(built, 2, 'a room change throws the index away');
        Interactions.index = index;
    });

    test('collider markers feed the blocked set and never become a sprite', () => {
        const { world, run } = worldWith(true);
        const RoomManager = run('RoomManager');
        const made = [];
        const sprite = (key) => {
            const s = { key, alpha: 1, data: {} };
            for (const f of ['setOrigin', 'setScale', 'setDepth', 'setTexture', 'setPosition', 'addToDisplayList', 'removeFromDisplayList', 'destroy']) s[f] = () => s;
            s.setAlpha = (a) => { s.alpha = a; return s; };
            s.setData = (k, v) => { s.data[k] = v; return s; };
            made.push(s);
            return s;
        };
        const scene = {
            GRID_SIZE: 64, config: world.config,
            textures: { exists: (k) => world.exists(k), getFrame: (k) => ({ realWidth: world.cells(k)[0] * 64, realHeight: world.cells(k)[1] * 64 }) },
            getSpriteConfig: () => ({ anchorX: 0.5, anchorY: 0.5, scale: 1 }),
            add: { sprite: (x, y, key) => sprite(key) },
            cache: { json: { get: () => null } },
        };
        for (const key of ['Tokyo', 'KonbiniMarket1', 'Osaka']) {
            const rm = new RoomManager(scene);
            rm.rooms = world.roomManager.rooms;
            rm.currentRoom = key;
            made.length = 0;
            rm.loadFloorTiles();
            const colliders = new Set();
            for (const layer of rm.rooms[key].layers) if (layer.collision) for (const xy in layer.tiles) colliders.add(xy);
            assert.ok(colliders.size > 20, key);
            assert.strictEqual([...rm.blockedCells].sort().join(' '), [...colliders].sort().join(' '), key);
            assert.ok(rm.tileRecords.length > 100 && rm.tileRecords.every(r => !r.layer.collision), key);
            assert.ok(made.every(s => s.key !== RoomManager.COLLIDER), 'no sprite for a collider marker');
            assert.strictEqual(made.length, rm.tileRecords.length);
            assert.ok(rm.chunks && rm.chunks.size > 0, 'every room is bucketed for Occlusion');
        }
        // art painted on a collision layer still blocks AND is drawn
        const rm = new RoomManager(scene);
        const fence = Object.values(world.roomManager.rooms.Tokyo.layers.find(l => l.name === 'Collidables').tiles)[0];
        rm.loadLayer({ name: 'Colliders', z: 9, collision: true, tiles: { '1,1': RoomManager.COLLIDER, '2,2': fence } });
        assert.strictEqual([...rm.blockedCells].sort().join(' '), '1,1 2,2');
        assert.strictEqual(rm.tileRecords.map(r => r.key).join(), fence);
    });

    test('scenery fades while it hides someone, and their name label with it', () => {
        const { run } = worldWith(true);
        const Occlusion = run('Occlusion');
        const art = (key, left, top, width, height, depth) => {
            const rec = { key, left, top, width, height, depth, sprite: { alpha: 1, setAlpha(a) { this.alpha = a; } } };
            return rec;
        };
        const label = () => ({ alpha: 1, setAlpha(a) { this.alpha = a; } });
        const roof = art('roof', 0, 0, 256, 192, 60), ground = art('path', 0, 0, 256, 256, -400);
        const fence = art('fence', 64, 96, 64, 64, 60);        // covers the lower half of someone at (96, 96)
        const torii = art('torii', 256, 0, 192, 192, 60);      // drawn over, but open in the middle
        const sign = art('ad', 448, 0, 128, 128, 60);
        const player = { sprite: { x: 96, y: 96, depth: 25, visible: true } };
        const npc = { sprite: { x: 1000, y: 96, depth: 25, visible: true }, nameLabel: label() };
        const far = { sprite: { x: 9000, y: 96, depth: 25, visible: true }, nameLabel: label() };
        const records = [roof, ground, fence, torii];
        const scene = {
            GRID_SIZE: 64, player, playerNameLabel: label(), game: { loop: { delta: 16 } },
            cameras: { main: { worldView: { x: 0, y: 0, right: 1280, bottom: 960 } } },
            roomManager: { tileRecords: records, signArt: [sign], currentRoom: 'R', rooms: { R: { npcs: [npc, far] } },
                artNear: () => records },
        };
        const oc = new Occlusion(scene);
        // every texture is solid, except the torii: only its outer thirds are
        oc.mask = (key) => key === 'torii' ? { w: 3, h: 1, bits: [1, 0, 1] } : { w: 1, h: 1, bits: [1] };
        const frames = (n) => { for (let i = 0; i < n; i++) oc.update(); };

        // behind the roof: it fades to ALPHA and the label to LABEL_ALPHA; the fence (which only
        // covers what the roof already does... and the ground under everyone) are judged apart
        const hid = (who) => oc.look(who).hits.map(r => r.key).sort().join();
        assert.strictEqual(hid(player), 'fence,roof');
        frames(30);
        assert.strictEqual(roof.fade, Occlusion.ALPHA);
        assert.strictEqual(roof.sprite.alpha, Occlusion.ALPHA);
        assert.strictEqual(scene.playerNameLabel.alpha, Occlusion.LABEL_ALPHA);
        assert.strictEqual(ground.fade, undefined, 'the ground is drawn under him');
        assert.strictEqual(npc.nameLabel.alpha, 1);
        // a streamed sprite that is re-made keeps the fade: it lives on the record
        roof.sprite = { alpha: 1, setAlpha(a) { this.alpha = a; } };
        frames(1);
        assert.strictEqual(roof.sprite.alpha, Occlusion.ALPHA);

        // half hidden (legs behind a fence, roof gone): nothing fades
        records.splice(records.indexOf(roof), 1);
        player.sprite.x = 97;
        assert.strictEqual(hid(player), '');
        frames(30);
        assert.strictEqual(fence.fade, undefined);
        assert.strictEqual(fence.sprite.alpha, 1);
        assert.strictEqual(scene.playerNameLabel.alpha, 1);
        assert.strictEqual(oc.fading.size, 0);

        // in the opening of a torii: its rectangle covers him, its pixels do not
        player.sprite.x = 352;
        assert.strictEqual(hid(player), '');
        player.sprite.x = 290;                     // ...behind a leg
        assert.strictEqual(hid(player), 'torii');
        // in front of it (drawn over it): never
        player.sprite.depth = 70;
        assert.strictEqual(hid(player), '');
        player.sprite.depth = 25;

        // an NPC behind a wall sign fades the sign and its own label, not the player's
        npc.sprite.x = 500; npc.sprite.y = 60;
        player.sprite.x = 800;
        frames(30);
        assert.strictEqual(sign.sprite.alpha, Occlusion.ALPHA);
        assert.strictEqual(npc.nameLabel.alpha, Occlusion.LABEL_ALPHA);
        assert.strictEqual(scene.playerNameLabel.alpha, 1);
        assert.strictEqual(torii.sprite.alpha, 1, 'restored once he left');
        // an NPC off camera is not looked at
        far.sprite.x = 500; far.sprite.y = 60;
        npc.sprite.x = 1000;
        scene.cameras.main.worldView = { x: 2000, y: 0, right: 3280, bottom: 960 };
        player.sprite.x = 2100;
        frames(30);
        assert.strictEqual(sign.sprite.alpha, 1);
        // ...and a label that was part-faded when its NPC left the camera is not left that way
        scene.cameras.main.worldView = { x: 0, y: 0, right: 1280, bottom: 960 };
        frames(3);
        assert.ok(far.nameLabel.alpha < 1 && far.nameLabel.alpha > Occlusion.LABEL_ALPHA, 'mid-fade');
        scene.cameras.main.worldView = { x: 2000, y: 0, right: 3280, bottom: 960 };
        frames(1);
        assert.strictEqual(far.nameLabel.alpha, 1);
        assert.strictEqual(oc.dimmed.size, 0);

        // another room: its records are new, nothing is carried over
        scene.cameras.main.worldView = { x: 0, y: 0, right: 1280, bottom: 960 };
        frames(30);
        assert.ok(oc.fading.has(sign));
        scene.roomManager.tileRecords = [];
        scene.roomManager.signArt = [];
        scene.roomManager.artNear = () => [];
        frames(1);
        assert.strictEqual(oc.fading.size, 0);
    });

    test('a roof laid from tiles fades whole, one building at a time (#172)', () => {
        const { world, run } = worldWith(true);
        const RoomManager = run('RoomManager'), Occlusion = run('Occlusion');
        const scene = {
            GRID_SIZE: 64, config: world.config,
            textures: { exists: (k) => world.exists(k), getFrame: (k) => ({ realWidth: world.cells(k)[0] * 64, realHeight: world.cells(k)[1] * 64 }) },
            getSpriteConfig: (k) => world.config.spriteMetadata[k] || { anchorX: 0.5, anchorY: 0.5 },
            add: { sprite: () => { const s = { alpha: 1, setAlpha(a) { s.alpha = a; return s; } }; for (const f of ['setOrigin', 'setScale', 'setDepth', 'setData', 'destroy']) s[f] = () => s; return s; } },
            cache: { json: { get: () => null } },
        };
        const rm = scene.roomManager = new RoomManager(scene);
        rm.rooms = world.roomManager.rooms;
        const oc = new Occlusion(scene);
        const cells = (roof) => roof.map(r => `${r.gridX},${r.gridY}`);
        const at = (x, y) => rm.tileRecords.find(r => r.layer.name === 'Tops' && r.gridX === x && r.gridY === y);

        rm.currentRoom = 'Market';
        rm.loadFloorTiles();
        // the hall: every roof tile of it, and nothing of the gate eight rows south
        const hall = oc.roof(at(23, 10));
        assert.ok(hall.length > 60, `the hall's roof is ${hall.length} tiles`);
        assert.ok(hall.every(r => r.gridY <= 15 && r.gridX >= 22 && r.gridX <= 33), cells(hall).join(' '));
        assert.strictEqual(oc.roof(at(28, 7)), hall, 'the ridge tile belongs to the same roof');
        const gate = oc.roof(at(27, 21)), west = oc.roof(at(21, 30)), east = oc.roof(at(32, 30));
        assert.strictEqual(new Set([hall, gate, west, east]).size, 4, 'four buildings, four roofs');
        assert.ok(cells(gate).includes('20,24') && cells(gate).includes('34,21'), 'the gate with both its pavilions');
        assert.ok(west.every(r => r.gridX <= 24 && r.gridY >= 27) && east.every(r => r.gridX >= 31 && r.gridY >= 27));
        // one sprite is its own roof; a tree crown, a lantern and the ground are nobody's
        assert.strictEqual(oc.roof(at(42, 9)), null, 'the single-sprite shrine roof');
        assert.strictEqual(oc.roof(rm.tileRecords.find(r => r.key.startsWith('sakura-large-top'))), null);
        assert.strictEqual(oc.roof(rm.tileRecords.find(r => r.layer.name === 'Floor')), null);
        // someone behind one tile of it fades the lot
        const who = { sprite: { x: 24 * 64 + 32, y: 10 * 64 + 32, depth: at(23, 10).depth - 20, visible: true } };
        oc.mask = () => ({ w: 1, h: 1, bits: [1] });
        const hits = oc.look(who).hits;
        assert.strictEqual(hits.length, hall.length);
        assert.ok(hall.every(r => hits.includes(r)));
        // corners that only meet at a point are not one roof
        const rec = (left, top) => ({ left, top, width: 64, height: 64 });
        assert.ok(Occlusion.touching(rec(0, 0), rec(64, 0)) && Occlusion.touching(rec(0, 0), rec(32, 32)));
        assert.ok(!Occlusion.touching(rec(0, 0), rec(64, 64)) && !Occlusion.touching(rec(0, 0), rec(128, 0)));

        // Tokyo's shrine hall: the roof, its six hallways and the two end pagodas
        rm.currentRoom = 'Tokyo';
        rm.loadFloorTiles();
        const shrine = oc.roof(at(28, 14));
        assert.strictEqual(shrine.length, 9, cells(shrine).join(' '));
        assert.strictEqual(oc.roof(at(40, 15)), shrine);
    });

    test('a room change fades the camera drawn last, so the HUD goes dark with the world (#110)', () => {
        const RM = game('RoomManager');
        const camera = (name) => ({ name, calls: [], fadeOut() { this.calls.push('out'); }, fadeIn() { this.calls.push('in'); },
            once(event, fn) { this.calls.push(event); this.fn = fn; } });
        const run = (uiScale) => {
            const main = camera('main');
            const rm = { scene: { cameras: { main }, uiScale, time: { delayedCall: (ms, fn) => fn() } }, swapped: 0, applyRoomSwap() { this.swapped++; } };
            RM.prototype.switchRoom.call(rm, 'Machi', 1, 1);
            const cam = uiScale && uiScale.active ? uiScale.camera : main;
            assert.strictEqual(rm.isTransitioning, true);
            cam.fn();                                   // fade-out complete: swap, hold, fade in
            assert.strictEqual(rm.swapped, 1);
            cam.fn();                                   // fade-in complete
            assert.strictEqual(rm.isTransitioning, false);
            return { main, cam };
        };
        // one camera (a desktop-sized window): the main camera, as ever
        let r = run({ active: false, camera: camera('ui') });
        assert.deepStrictEqual(r.main.calls, ['out', 'camerafadeoutcomplete', 'in', 'camerafadeincomplete']);
        r = run(undefined);
        assert.strictEqual(r.main.calls.length, 4);
        // three cameras (phone, small window): the overlay camera, which is drawn over the HUD's
        r = run({ active: true, camera: camera('ui') });
        assert.deepStrictEqual(r.cam.calls, ['out', 'camerafadeoutcomplete', 'in', 'camerafadeincomplete']);
        assert.deepStrictEqual(r.main.calls, []);
    });
};
