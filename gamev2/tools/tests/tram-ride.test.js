// Riding a streetcar (src/TramRide.js) and the standing car's collision (CollisionSystem), issue #245.
// The mover itself (src/AmbientTrams.js) and the towns' lines: glows-trams.test.js.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game, worldWith }) => {
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const ride = () => {
        if (!game('typeof AmbientTrams !== "undefined"')) vm.runInContext(src('AmbientTrams.js'), ctx, { filename: 'AmbientTrams.js' });
        if (!game('typeof TramRide !== "undefined"')) vm.runInContext(src('TramRide.js'), ctx, { filename: 'TramRide.js' });
        return game('TramRide');
    };
    const NONE = { x: 0, y: 0 }, UP = { x: 0, y: -1 }, DOWN = { x: 0, y: 1 }, LEFT = { x: -1, y: 0 }, RIGHT = { x: 1, y: 0 };

    test('on a tram the key that boarded does not get off; let go, then up or down at a halt does (#245)', () => {
        const R = ride();
        const step = (carried, heading, halted) => plain(R.step(carried, heading, halted));
        // the key that walked the player into the car is still down: on board, whatever it is, halted or not
        for (const held of [UP, DOWN, LEFT, RIGHT, { x: 1, y: 1 }]) {
            assert.deepStrictEqual(step(true, held, true), { carried: true, side: 0 });
            assert.deepStrictEqual(step(true, held, false), { carried: true, side: 0 });
        }
        // letting go ends that, and does nothing else
        assert.deepStrictEqual(step(true, NONE, true), { carried: false, side: 0 });
        assert.deepStrictEqual(step(false, NONE, true), { carried: false, side: 0 });
        // then up / down at a halt is a side to get off on
        assert.deepStrictEqual(step(false, UP, true), { carried: false, side: -1 });
        assert.deepStrictEqual(step(false, DOWN, true), { carried: false, side: 1 });
        assert.deepStrictEqual(step(false, { x: 1, y: -1 }, true), { carried: false, side: -1 }, 'up with right held too is still up');
        // nothing while the car moves; left and right never
        for (const held of [UP, DOWN, LEFT, RIGHT]) assert.deepStrictEqual(step(false, held, false), { carried: false, side: 0 });
        assert.deepStrictEqual(step(false, LEFT, true), { carried: false, side: 0 });
        assert.deepStrictEqual(step(false, RIGHT, true), { carried: false, side: 0 });
        // a whole ride, frame by frame: down walks in and stays held, is let go, the car leaves and halts, up is pressed
        const frames = [[DOWN, true], [DOWN, true], [NONE, true], [NONE, false], [UP, false], [UP, true]];
        let carried = true;
        const sides = frames.map(([heading, halted]) => { const out = R.step(carried, heading, halted); carried = out.carried; return out.side; });
        assert.deepStrictEqual(sides, [0, 0, 0, 0, 0, -1], 'an up held before the stop gets off as the car draws up');
    });

    test('a rider is put off beside the middle of the car, on the side asked and never the other (#245)', () => {
        const R = ride();
        const cell = (foot, side, blocked) => plain(R.alightCell(foot, side, (x, y) => !(blocked || []).includes(`${x},${y}`)));
        const five = { x0: 19, x1: 23, y0: 20, y1: 21 }, four = { x0: 47, x1: 50, y0: 15, y1: 16 }, three = { x0: 10, x1: 12, y0: 15, y1: 16 };
        // the middle column, on the row beyond the car: above its upper row going north, under the rails going south
        assert.deepStrictEqual(cell(five, -1), { x: 21, y: 19 });
        assert.deepStrictEqual(cell(five, 1), { x: 21, y: 22 });
        assert.deepStrictEqual(cell(three, -1), { x: 11, y: 14 });
        assert.deepStrictEqual(cell(four, 1), { x: 48, y: 17 }, 'an even car: the west of its two middle columns');
        // a blocked cell moves the rider along the same row: nearest the middle, west first of two as near
        assert.deepStrictEqual(cell(three, -1, ['11,14']), { x: 10, y: 14 });
        assert.deepStrictEqual(cell(three, -1, ['11,14', '10,14']), { x: 12, y: 14 });
        assert.deepStrictEqual(cell(five, 1, ['21,22', '20,22', '22,22']), { x: 19, y: 22 });
        assert.deepStrictEqual(cell(four, -1, ['48,14']), { x: 47, y: 14 });
        assert.deepStrictEqual(cell(four, -1, ['48,14', '47,14']), { x: 49, y: 14 });
        // the whole side walled in: nowhere, though the other side is open
        assert.strictEqual(cell(three, -1, ['10,14', '11,14', '12,14']), null);
        assert.deepStrictEqual(cell(three, 1, ['10,14', '11,14', '12,14']), { x: 11, y: 17 });
        // only that row is ever asked about
        const asked = [];
        R.alightCell(three, -1, (x, y) => { asked.push(`${x},${y}`); return false; });
        assert.deepStrictEqual(asked, ['11,14', '10,14', '12,14']);
    });

    // A ride with no Phaser behind it: a car (a line state of AmbientTrams, on a real plan), a player, a scene of stubs.
    const aboard = (opts = {}) => {
        const R = ride(), T = game('AmbientTrams');
        const GS = 64, image = { x: 0, width: 192, height: 128 };
        const line = T.line({ row: 16, from: 4, to: 27, sprite: 'c', shuttle: true, name: 'cable car', stops: [11, 20] }, [], null, 60);
        const plan = T.plan(line, { GS, width: 192, worldWidth: 60 * GS, dir: 1 });
        const car = { line, plan, image, t: T.firstHalt(plan) + 100 };
        const place = () => { image.x = Math.round(T.at(car.plan, car.t).x); };
        place();
        const toasts = [], log = [];
        const sprite = { x: 11 * GS + 32, y: 14 * GS + 32, visible: true, setVisible(v) { this.visible = v; } };
        const player = { gridX: 11, gridY: 14, sprite, facingX: 0, facingY: 1,
            updateDirectionSprite: (dx, dy) => log.push(`face ${dx},${dy}`), setIdleFrame: () => log.push('idle') };
        const blocked = opts.blocked || [];
        const scene = {
            GRID_SIZE: GS, player, touchControls: opts.touch ? { enabled: true } : null,
            ambientTrams: { carAt: (x, y) => (T.at(car.plan, car.t).stopped && x >= 10 && x <= 12 && y >= 15 && y <= 16 && car.image ? car : null) },
            roomManager: { isTransitioning: !!opts.transitioning },
            shop: { toast: (m) => toasts.push(m) },
            checkCollision: (who, x, y, fx, fy) => { assert.deepStrictEqual([who, fx, fy], [player, x, y]); return !blocked.includes(`${x},${y}`); },
            checkTransporter: () => log.push('transporter'),
        };
        return { R, T, GS, car, place, player, sprite, scene, toasts, log, ride: new R(scene) };
    };

    test('bumping the standing car boards it: the player is hidden and goes where the car goes (#245)', () => {
        const a = aboard();
        const { ride: r, car, player, sprite, toasts, T, GS } = a;
        assert.strictEqual(r.riding, false);
        // not the car's cells: nothing; nor while the room is fading out
        assert.strictEqual(r.check(11, 14), false);
        assert.strictEqual(aboard({ transitioning: true }).ride.check(11, 15), false);
        assert.ok(!r.riding && sprite.visible && toasts.length === 0);
        // the bump
        assert.strictEqual(r.check(11, 15), true);
        assert.ok(r.riding && !sprite.visible);
        assert.deepStrictEqual(toasts, ['On the cable car · ↑/↓: get off at a stop']);
        assert.deepStrictEqual([player.gridX, player.gridY, sprite.x, sprite.y], [11, 16, 10 * GS + 96, 16.5 * GS], 'at the car\'s middle, on the rail row');
        // the key that boarded is still down: still aboard; nothing new is said while it stands
        r.handleInput(DOWN); r.update();
        assert.ok(r.riding);
        r.handleInput(NONE);
        assert.strictEqual(toasts.length, 1);
        // the car pulls away: the rider's cell is the one under its middle, every frame; up and down do nothing
        const leaves = car.plan.legs.find((l) => l.t0 > car.t && l.x0 !== l.x1);
        let last = player.gridX;
        for (car.t = leaves.t0 + 16; car.t < leaves.t1; car.t += 160) {
            a.place(); r.update();
            r.handleInput(UP); r.handleInput(NONE);
            assert.ok(r.riding && !sprite.visible, 'still aboard between stops');
            assert.strictEqual(sprite.x, car.image.x + 96);
            assert.deepStrictEqual([player.gridX, player.gridY], [Math.floor(sprite.x / GS), 16]);
            assert.ok(player.gridX >= last);
            last = player.gridX;
        }
        assert.strictEqual(toasts.length, 1, 'nothing is said on the way');
        // it draws up at the next stop: told once, however long it stands
        car.t = leaves.t1 + 16; a.place(); r.update();
        car.t += 500; r.update();
        assert.deepStrictEqual(toasts.slice(1), ['↑/↓: get off']);
        assert.deepStrictEqual([player.gridX, player.gridY], [20, 16], 'under the middle of the car at the second stop (19-21)');
        // something else showed the sprite (a new character picked from the menu): hidden again next frame
        sprite.visible = true; r.update();
        assert.strictEqual(sprite.visible, false);
        // on a phone the keys are worded as the pad
        const phone = aboard({ touch: true });
        phone.ride.check(11, 15);
        assert.deepStrictEqual(phone.toasts, ['On the cable car · d-pad: get off at a stop']);
    });

    test('getting off: beside the car on the side asked, back to it; a blocked side keeps the rider (#245)', () => {
        const a = aboard({ blocked: ['11,14', '10,17', '11,17', '12,17'] });
        const { ride: r, player, sprite, toasts, log, GS } = a;
        r.check(11, 15);
        r.handleInput(DOWN);                    // the boarding key, still held
        r.handleInput(NONE);
        log.length = 0;
        // the south side is walled in: told so, still aboard, and asking again says it again
        r.handleInput(DOWN);
        assert.ok(r.riding && !sprite.visible);
        assert.strictEqual(toasts[toasts.length - 1], 'No room to get off on this side');
        assert.deepStrictEqual(log, [], 'not moved, not turned');
        // north: the middle cell is taken, so the next along that row
        r.handleInput(UP);
        assert.ok(!r.riding && sprite.visible);
        assert.deepStrictEqual([player.gridX, player.gridY, sprite.x, sprite.y], [10, 14, 10 * GS + 32, 14 * GS + 32]);
        assert.deepStrictEqual([player.facingX, player.facingY], [0, -1], 'their back to the car');
        assert.deepStrictEqual(log, ['face 0,-1', 'idle', 'transporter'], 'turned, standing, and the cell acts as if stepped onto');
        // off the car, the keys are the walker's again: nothing here moves or hides the player
        r.update(); r.handleInput(UP);
        assert.deepStrictEqual([player.gridX, player.gridY, sprite.visible], [10, 14, true]);
    });

    test('a ride ends where the rider is when its car is taken away or the room changes (#245)', () => {
        // the line was re-sent or cleared under the rider (AmbientTrams.retire): no image, no plan
        for (const gone of ['image', 'plan']) {
            const a = aboard();
            a.ride.check(11, 15);
            const before = [a.player.gridX, a.player.gridY];
            a.car[gone] = null;
            a.ride.update();
            assert.ok(!a.ride.riding && a.sprite.visible, `${gone} gone`);
            assert.deepStrictEqual([a.player.gridX, a.player.gridY], before);
            assert.ok(a.log.includes('idle') && !a.log.includes('transporter'));
        }
        // a room swap (which places the player itself)
        const a = aboard();
        a.ride.onRoomChange();
        assert.deepStrictEqual(a.log, [], 'nobody riding: nothing to end');
        a.ride.check(11, 15);
        a.ride.onRoomChange();
        assert.ok(!a.ride.riding && a.sprite.visible);
        a.ride.update();
        assert.ok(a.sprite.visible, 'and it stays ended');
    });

    test('a standing streetcar blocks a step; with no cars (the terminal game, these tests) nothing is asked (#245)', () => {
        const { world, config } = worldWith(true);
        // beside the first stop of a declared shuttle, on the row above the car: found from the config, not written here
        const [roomKey, def] = Object.entries(config.rooms).flatMap(([k, r]) => (r.tramways || []).filter((t) => t.shuttle).map((t) => [k, t]))[0];
        const meta = config.spriteMetadata[def.sprite], tall = Math.round(0.5 / meta.anchorY);
        world.enter(roomKey, def.stops[0], def.row - tall);
        const p = world.player, top = p.gridY + 1, rails = p.gridY + tall;
        assert.strictEqual(world.ambientTrams, undefined, 'the world model has no streetcars');
        // no mover: the street is open road, and asking does not crash
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX, top), true);
        assert.strictEqual(world.canStep(p.gridX, top, p.gridX, rails), true);
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX + 1, p.gridY), true);
        // a car standing on exactly these cells
        const car = new Set([`${p.gridX},${top}`, `${p.gridX + 1},${top}`, `${p.gridX},${rails}`, `${p.gridX + 1},${rails}`]);
        const asked = [];
        world.ambientTrams = { carAt: (x, y) => { asked.push(`${x},${y}`); return car.has(`${x},${y}`) ? {} : null; } };
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX, top), false, 'into the car');
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX + 1, top), false, 'diagonally into it');
        assert.strictEqual(world.canStep(p.gridX - 1, p.gridY, p.gridX - 1, top), true, 'past its end');
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX - 1, top), false, 'cutting its corner, as with any solid cell');
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX + 1, p.gridY), true, 'along its side');
        assert.strictEqual(world.canStep(p.gridX - 1, p.gridY, p.gridX, top), false, 'a diagonal that ends in it');
        assert.strictEqual(world.canStep(p.gridX - 1, top, p.gridX, top), false, 'along the street into its end');
        // someone the car stopped on can step out: only the cells stepped to are asked about
        assert.strictEqual(world.canStep(p.gridX, top, p.gridX, p.gridY), true);
        assert.strictEqual(world.canStep(p.gridX, top, p.gridX, rails), false, 'further in is a bump');
        assert.ok(asked.length > 0 && !asked.includes(`${p.gridX},${p.gridY - 1}`));
        // an NPC is stopped by it too
        const npc = world.character('npc', p.gridX - 1, top);
        assert.strictEqual(world.collisionSystem.checkCollision(npc, p.gridX, top, p.gridX - 1, top), false);
        // and with the car gone the street is open again
        world.ambientTrams = { carAt: () => null };
        assert.strictEqual(world.canStep(p.gridX, p.gridY, p.gridX, top), true);
    });

    test('the ride is loaded and hooked up: the bump, the frame, the keys, the room swap (#245)', () => {
        const html = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        assert.ok(html.includes("'src/TramRide.js'") && html.indexOf('src/AmbientTrams.js') < html.indexOf('src/TramRide.js'));
        const scene = src('GameScene.js'), input = src('systems/InputHandler.js'), rooms = src('systems/RoomManager.js');
        assert.ok(scene.includes('this.tramRide = new TramRide(this);'));
        // after the NPC check, and never under a dialogue: an NPC the car stopped on is talked to, not also boarded
        assert.ok(scene.includes('this.npcManager.checkInteraction(targetGridX, targetGridY);\n        // bumping a streetcar standing at a stop is getting on it (issue #245)\n' +
            '        if (this.tramRide && !this.dialogueManager.isVisible() && this.tramRide.check(targetGridX, targetGridY)) return;'));
        // the rider is moved after the cars
        assert.ok(/ambientTrams\.update\(this\.game\.loop\.delta\);\n\s+if \(this\.tramRide\) this\.tramRide\.update\(\);/.test(scene));
        // the keys: after the menu, before walking; the latched heading; the menu's two key states kept in step
        const branch = input.slice(input.indexOf('if (tramRide && tramRide.riding) {'), input.indexOf('// Priority 5: Player movement'));
        assert.ok(input.indexOf('this.handleMenuInput();\n            return;') < input.indexOf('if (tramRide && tramRide.riding) {') && branch.length > 0);
        assert.ok(branch.includes('tramRide.handleInput(this.heading(true));') && branch.includes('return;'));
        assert.ok(branch.includes('this.lastKeyState.up = this.cursors.up.isDown || this.wKey.isDown;') &&
            branch.includes('this.lastKeyState.down = this.cursors.down.isDown || this.sKey.isDown;'));
        assert.ok(input.includes('const down = (key) => (latched ? this.held(key) : key.isDown);'));
        // a room swap ends the ride before the lines are rebuilt
        assert.ok(rooms.indexOf('this.scene.tramRide.onRoomChange();') > 0 &&
            rooms.indexOf('this.scene.tramRide.onRoomChange();') < rooms.indexOf('this.scene.ambientTrams.onRoomChange(newRoom);'));
        // the collision rule is guarded: the same class runs where there are no cars
        assert.ok(src('systems/CollisionSystem.js').includes('if (trams && cellsToCheck.some((cell) => trams.carAt(cell.x, cell.y))) {'));
    });
};
