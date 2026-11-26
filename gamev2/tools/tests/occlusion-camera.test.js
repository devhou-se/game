module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig, worldWith }) => {
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

    test('the camera looks up in front of a marked landmark, and only there (#176 / #90)', () => {
        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView');
        const look = realConfig().game.lookUp, G = 64;
        assert.ok(look && look.sprites['shrine-top'] === 2 && look.sprites['tokyo-tower'] === 0, 'the landmarks are data');
        for (const plain of ['highrise-yellow', 'highrise-glass', 'midrise-apartment', 'shrine-building', 'torii-red-feet']) {
            assert.ok(!(plain in look.sprites), plain + ' is not a landmark');
        }
        assert.strictEqual(LandmarkView.family('shrine-top_0_0'), 'shrine-top');
        assert.strictEqual(LandmarkView.family('tokyo-tower-feet'), 'tokyo-tower-feet');

        // indexing: only marked families, with the foot `rows` cells under the marked sprite
        const rec = (key, x, y, w, h) => ({ key, left: x * G, top: y * G, width: w * G, height: h * G });
        const marks = LandmarkView.index([
            rec('shrine-top_0_0', 22, 0, 5, 6), rec('shrine-building_0_0', 23, 2, 3, 6),
            rec('highrise-yellow_0_0', 40, 0, 4, 8), rec('grass_0_0', 0, 0, 1, 1), rec('tokyo-tower_0_0', 60, 0, 8, 15),
        ], look.sprites, G);
        assert.deepStrictEqual(JSON.parse(JSON.stringify(marks)), [
            { key: 'shrine-top_0_0', left: 22 * G, right: 27 * G, top: 0, feet: 8 * G },
            { key: 'tokyo-tower_0_0', left: 60 * G, right: 68 * G, top: 0, feet: 15 * G },
        ]);
        assert.deepStrictEqual(Array.from(LandmarkView.index([rec('shrine-top_0_0', 0, 0, 5, 6)], undefined, G)), []);

        // the Machi hall, lifted clear of the room's top so the numbers are the camera's alone
        const hall = { left: 22 * G, right: 27 * G, top: 20 * G, feet: 28 * G };
        const at = (cx, cy, more) => Object.assign({ x: cx * G + 32, y: cy * G + 32, landmarks: [hall], grid: G,
            cells: look.cells, fade: look.fade, side: look.side, viewH: 960, bar: 40, deadzone: 256, foot: 128 }, more);
        const aim = (cx, cy, more) => LandmarkView.aim(at(cx, cy, more));
        const same = (got, want, why) => assert.deepStrictEqual(JSON.parse(JSON.stringify(got)), want, why);

        // desktop, south of the steps: all of the deadzone goes and the camera sits with the roof's
        // peak a quarter cell under the bar
        const steps = aim(24, 29);
        assert.strictEqual(steps.weight, 1);
        const camY = 29 * G + 32 - steps.offset;
        assert.strictEqual(camY - 480 + 40 + 16, hall.top, 'the top is just under the HUD bar');
        // ... and the ordinary camera would have cut it off (it trails by half the deadzone)
        assert.ok(29 * G + 32 + 128 - 480 + 40 > hall.top);

        // it fades out with distance, continuously: no step bigger than a walking pace allows
        let last = aim(24, 28.5), far = null;
        for (let cy = 28.5; cy <= 36; cy += 1 / 16) {
            const a = aim(24, cy);
            assert.ok(Math.abs(a.weight - last.weight) <= 0.07 && Math.abs(a.offset - last.offset) <= 40, `no jump at row ${cy}`);
            last = far = a;
        }
        same(far, { weight: 0, offset: 0 }, 'six cells south it has let go');
        // ... and to either side, and behind its foot
        assert.strictEqual(aim(27, 29).weight, 0.75);
        same(aim(29, 29), { weight: 0, offset: 0 });
        same(aim(19, 29), { weight: 0, offset: 0 });
        same(aim(24, 26.5), { weight: 0, offset: 0 });
        for (let cx = 19; cx <= 30; cx += 1 / 16) {
            const a = aim(cx, 29), b = aim(cx + 1 / 16, 29);
            assert.ok(Math.abs(a.weight - b.weight) <= 0.07 && Math.abs(a.offset - b.offset) <= 40, `no jump at column ${cx}`);
        }

        // nothing marked, nothing changes: a high-rise is not in the list, so it is never indexed
        same(aim(24, 29, { landmarks: [] }), { weight: 0, offset: 0 });
        // a landmark the ordinary camera always shows whole (four rows) changes nothing either; a torii
        // (five) can lose its beam when the camera trails, so it only narrows the deadzone a little
        const low = { left: 21 * G, right: 27 * G, top: 32 * G, feet: 36 * G };
        same(aim(24, 36, { landmarks: [low] }), { weight: 0, offset: 0 });
        const torii = { left: 21 * G, right: 27 * G, top: 31 * G, feet: 36 * G };
        same(aim(24, 36, { landmarks: [torii] }), { weight: 0.875, offset: 0 });

        // the player always keeps `foot` of view below them and never goes under the bar, at any
        // weight and wherever the camera sits in what is left of its deadzone
        const tower = { left: 20 * G, right: 28 * G, top: 0, feet: 40 * G };
        for (const view of [{ viewH: 960, bar: 40, deadzone: 256 }, { viewH: 480, bar: 34, deadzone: 128 }, { viewH: 480, bar: 46, deadzone: 128, foot: 128 + 60 }]) {
            for (const mark of [hall, tower]) {
                for (let cy = mark.feet / G - 1; cy <= mark.feet / G + 7; cy += 0.25) {
                    for (let cx = 17; cx <= 31; cx += 0.5) {
                        const o = at(cx, cy, Object.assign({ landmarks: [mark] }, view)), a = LandmarkView.aim(o);
                        assert.ok(a.weight >= 0 && a.weight <= 1 && a.offset >= 0);
                        const slack = o.deadzone * (1 - a.weight) / 2;
                        const lowest = o.y - (o.y - a.offset - slack);   // the player below the view's centre, at most
                        // (where the view is too short for `foot` even as it is, no lower than the ordinary camera lets them go)
                        assert.ok(lowest <= Math.max(o.viewH / 2 - o.foot, o.deadzone / 2) + 1e-9, `feet in view at ${cx},${cy}`);
                        assert.ok(o.y - a.offset + slack - o.viewH / 2 + o.bar <= o.y - 32, `not under the bar at ${cx},${cy}`);
                    }
                }
            }
        }
        // a 2x landscape phone (7.5 cells tall) cannot hold the hall: the shift is capped, not the player lost
        const phone = aim(24, 29, { viewH: 480, bar: 34, deadzone: 128 });
        same(phone, { weight: 1, offset: 240 - 128 });
        // with all of the weight and no cap the answer does not depend on the deadzone
        assert.strictEqual(aim(24, 29, { deadzone: 128 }).offset, steps.offset);
    });

    test('chunk streaming covers the point the camera follows, above the player while it looks up (#176)', () => {
        const RoomManager = game('RoomManager');
        const rm = Object.create(RoomManager.prototype);
        const cam = { width: 1280, height: 960, zoom: 1, scrollX: 1000, scrollY: 3000, followOffset: { x: 0, y: 0 } };
        rm.scene = { GRID_SIZE: 64, cameras: { main: cam }, player: { sprite: { x: 1640, y: 3480 } } };
        const size = RoomManager.CHUNK * 64, margin = RoomManager.STREAM_MARGIN * 64;
        const plain = rm.streamRect();
        assert.strictEqual(plain.y0, Math.floor((3480 - 480 - margin) / size));
        cam.followOffset.y = 352;   // the camera is on its way up
        const up = rm.streamRect();
        assert.strictEqual(up.y0, Math.floor((3480 - 352 - 480 - margin) / size));
        assert.ok(up.y0 < plain.y0, 'the rows it is about to show have sprites');
        assert.deepStrictEqual([up.x0, up.x1, up.y1], [plain.x0, plain.x1, plain.y1]);
        delete cam.followOffset;    // a camera stub without one (the tools)
        assert.deepStrictEqual(rm.streamRect(), plain);
    });

    test('the look-up narrows the follow deadzone in place, and a zoom change keeps it ours (#176)', () => {
        const UIScale = game('UIScale');
        const ui = Object.create(UIScale.prototype);
        let recentred = 0;
        const main = { zoom: 1, width: 1280, deadzone: { x: 0, y: 100, width: 256, height: 256 },
            setZoom(z) { this.zoom = z; },
            setDeadzone(w, h) { recentred++; this.deadzone.width = w; this.deadzone.height = h; } };
        ui.scene = { cameras: { main }, scale: { width: 1280 }, events: { emit() {} } };
        ui.deadzoneShare = 1;
        ui.setWorldZoom(1);
        assert.strictEqual(ui.deadzoneHeight(), 256);
        ui.setDeadzoneShare(0.25);
        assert.deepStrictEqual([main.deadzone.height, main.deadzone.y, main.deadzone.width], [64, 196, 256], 'narrowed about its centre');
        assert.strictEqual(recentred, 0, 'Camera.setDeadzone (which re-centres the camera on the player) is not called');
        assert.strictEqual(ui.deadzoneHeight(), 256);
        ui.setWorldZoom(2);         // a phone turned round while the camera looks up
        assert.deepStrictEqual([main.deadzone.width, main.deadzone.height, ui.deadzoneHeight()], [128, 32, 128]);
        ui.setDeadzoneShare(1);
        assert.strictEqual(main.deadzone.height, 128, 'the full height comes back, not the narrowed one taken for a new size');
        ui.setWorldZoom(1);
        assert.deepStrictEqual([main.deadzone.width, main.deadzone.height], [256, 256]);
    });

    test('the first look-up of a session narrows the deadzone in place too (#220)', () => {
        // a desktop window never zooms: UIScale.update releases before setWorldZoom has ever sized the
        // deadzone, so the first narrowing found one that was not "ours" and took it over through
        // Camera.setDeadzone - which re-centres the camera on the player, a jump of however far it trailed
        const UIScale = game('UIScale');
        const fresh = (zoom, width) => {
            const ui = Object.create(UIScale.prototype);
            const main = { zoom, width, recentred: 0, deadzone: { x: 512, y: 352, width: 256, height: 256 },
                setZoom(z) { this.zoom = z; },
                setDeadzone(w, h) { this.recentred++; this.deadzone.width = w; this.deadzone.height = h; } };
            ui.scene = { cameras: { main }, scale: { width: 1280 }, events: { emit() {} } };
            ui.deadzoneShare = 1;
            ui.worldZoom = zoom;
            return { ui, main };
        };
        const { ui, main } = fresh(1, 1280);
        assert.strictEqual(ui.deadzoneHeight(), 256, 'the owner\'s deadzone, before anything is ours');
        ui.setDeadzoneShare(0.9);       // the first frame of the first ease
        assert.strictEqual(main.recentred, 0, 'Camera.setDeadzone is not called');
        assert.deepStrictEqual([main.deadzone.width, main.deadzone.height], [256, 256 * 0.9]);
        assert.ok(Math.abs(main.deadzone.y + main.deadzone.height / 2 - (352 + 128)) < 1e-9 && main.deadzone.x === 512, 'about its own centre');
        assert.strictEqual(ui.deadzoneHeight(), 256, 'the full height is remembered');
        for (const share of [0.7, 0.5, 0.5, 0.8, 1]) ui.setDeadzoneShare(share);
        assert.strictEqual(main.recentred, 0);
        assert.deepStrictEqual([main.deadzone.x, main.deadzone.y, main.deadzone.width, main.deadzone.height], [512, 352, 256, 256], 'and comes back as it was');
        // a size its owner set meanwhile is taken as the new full size, still without a re-centre
        Object.assign(main.deadzone, { width: 320, height: 200 });
        ui.setDeadzoneShare(0.5);
        assert.deepStrictEqual([main.deadzone.width, main.deadzone.height, ui.deadzoneHeight(), main.recentred], [320, 100, 200, 0]);
        // the same share again is nothing; no deadzone (no camera follow yet) is nothing
        const before = JSON.stringify(main.deadzone);
        ui.setDeadzoneShare(0.5);
        assert.strictEqual(JSON.stringify(main.deadzone), before);
        const none = fresh(1, 1280);
        none.main.deadzone = null;
        none.ui.setDeadzoneShare(0.5);
        assert.strictEqual(none.ui.deadzoneShare, 0.5);
        // a zoom or view change still goes through Camera.setDeadzone (the picture is redrawn anyway), and keeps the share
        const phone = fresh(1, 1280);
        phone.ui.setDeadzoneShare(0.5);
        phone.ui.setWorldZoom(2);
        assert.deepStrictEqual([phone.main.deadzone.width, phone.main.deadzone.height, phone.main.recentred], [128, 64, 1]);
        // the look-up is the only caller, every frame of its ease
        const look = fs.readFileSync(path.join(GV2, 'src', 'systems', 'LandmarkView.js'), 'utf8');
        assert.ok(look.includes('this.scene.uiScale.setDeadzoneShare(1 - this.weight);'));
    });
};
