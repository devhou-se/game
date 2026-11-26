module.exports = ({ test, assert, fs, path, GV2, load, game, worldWith }) => {
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const tiles = (room, layer) => (room.layers.find((l) => l.name === layer) || { tiles: {} }).tiles;
    // every transporter in the world that leads into the Izakaya: [room key, transporter]
    const doorsInto = (rooms) => Object.entries(rooms).flatMap(([key, room]) =>
        (room.transporters || []).filter((t) => t.targetRoom === 'Izakaya').map((t) => [key, t]));

    test('the Izakaya has one street door, in a Tokyo district that is staying, lit by a lantern pair (#68)', () => {
        const c = cfg(), rooms = c.rooms, name = (t) => c.tilePalette[t];
        const doors = doorsInto(rooms);
        assert.strictEqual(doors.length, 1, 'exactly one way in');
        const [host, door] = doors[0];
        const districts = c.cities.TokyoCity.rooms.map((r) => r.room);
        assert.ok(districts.includes(host), `${host} is not a district of the stitched Tokyo`);
        assert.notStrictEqual(host, 'Machi', 'Machi is to be deleted');
        assert.deepStrictEqual([host, door.gridX, door.gridY, door.targetX, door.targetY, door.hidden], ['Market', 7, 37, 9, 12, true]);

        const room = rooms[host], solid = tiles(room, 'Colliders'), front = `${door.gridX},${door.gridY + 1}`;
        assert.ok(!(`${door.gridX},${door.gridY}` in solid), 'the doorway is not sealed');
        assert.ok(!(front in solid), 'the cell in front of the door is free');
        assert.ok(/^grey-brick-autotile/.test(name(tiles(room, 'Floor')[front])), 'the door opens off the pavement');
        // the door is in a house front, one cell in from either end of it
        assert.strictEqual(name(tiles(room, 'Collidables')[`${door.gridX - 1},${door.gridY}`]), 'building-entrance-3_0_0');
        // a red lantern either side of the house: head on Tops, solid foot on the door's row
        for (const x of [door.gridX - 2, door.gridX + 2]) {
            assert.strictEqual(name(tiles(room, 'Tops')[`${x},${door.gridY - 1}`]), 'red-lanterns_6_3', `lantern head at ${x}`);
            assert.strictEqual(name(tiles(room, 'Collidables')[`${x},${door.gridY}`]), 'red-lanterns_4_1', `lantern foot at ${x}`);
            assert.ok(`${x},${door.gridY}` in solid, `the lantern at ${x} is solid`);
        }
        // nobody's base or dated position is on the doorway or the cell in front of it
        const taken = room.npcs.flatMap((n) => [n, ...Object.values(n.states || {})])
            .filter((s) => s.gridX === door.gridX && (s.gridY === door.gridY || s.gridY === door.gridY + 1));
        assert.deepStrictEqual(taken, []);

        // both exit mats put the player on the pavement outside, never on the door itself
        const exits = rooms.Izakaya.transporters;
        assert.strictEqual(exits.length, 2);
        for (const t of exits) {
            assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], [host, door.gridX, door.gridY + 1]);
        }
        // the room itself is what it was: the bar sells, the table starts the game, two fixture opponents
        assert.strictEqual(rooms.Izakaya.shopMenu, 'izakaya');
        assert.deepStrictEqual(rooms.Izakaya.drinkingGame.triggerCells, [[4, 7], [5, 7]]);
        assert.deepStrictEqual(rooms.Izakaya.npcs.map((n) => [n.name, !!n.drinkingGameOpponent]), [['Damian', true], ['Bailey', true]]);
    });

    test('the Izakaya house carries its own sign: its two ad boards are pinned, every other board is random', () => {
        const c = cfg(), adFor = game('RoomManager.adFor');
        const ads = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'ads', 'manifest.json'), 'utf8')).ads;
        const door = doorsInto(c.rooms)[0][1], signage = c.rooms.Market.signage;
        // the boards on the wall above the house front (6..8,37): a wide one and a square one
        const own = signage.filter((s) => s.gridY === door.gridY - 1 && s.gridX >= door.gridX - 1 && s.gridX <= door.gridX + 1);
        assert.deepStrictEqual(own.map((s) => [s.gridX, s.gridY, s.shape, s.ad]), [[6, 36, 'wide', 'ad-wide-03'], [8, 36, 'square', 'ad-square-01']]);
        assert.strictEqual(signage.filter((s) => s.ad).length, 2, 'only the Izakaya pins an ad');
        assert.strictEqual(signage.length, 10, 'no board added or lost');
        // the pinned ad is in the pool, of the board's shape, and is the drinking sign the generator means:
        // the pool's files are numbered in SPECS order, per shape
        const specs = [...fs.readFileSync(path.join(GV2, 'tools', 'generate_ads.py'), 'utf8').matchAll(/dict\(shape='(\w+)', text='([^']+)'/g)];
        const nth = (shape, n) => specs.filter((m) => m[1] === shape)[n - 1][2];
        assert.strictEqual(nth('wide', 3), 'のみほうだい');
        assert.strictEqual(nth('square', 1), '酒');
        for (const spot of own) {
            const ad = ads.find((a) => a.key === spot.ad);
            assert.ok(ad && ad.shape === spot.shape && fs.existsSync(path.join(GV2, 'assets', 'ads', ad.file)), spot.ad);
            // whatever the roll, the same sign; with the pin gone, the roll decides again
            for (const roll of [0, 0.37, 0.5, 0.999]) assert.strictEqual(adFor(spot, ads, roll).key, spot.ad);
            const free = { gridX: spot.gridX, gridY: spot.gridY, shape: spot.shape };
            const seen = new Set([0, 0.2, 0.4, 0.6, 0.8, 0.999].map((roll) => adFor(free, ads, roll).key));
            assert.ok(seen.size > 3, 'an unpinned board draws from the pool');
            assert.ok([...seen].every((k) => ads.find((a) => a.key === k).shape === spot.shape));
        }
        // a pin that is not in the pool (or is another shape) falls back to a random ad of the shape; no ads, no sign
        assert.strictEqual(adFor({ shape: 'wide', ad: 'ad-square-01' }, ads, 0).key, 'ad-wide-01');
        assert.strictEqual(adFor({ shape: 'wide', ad: 'nope' }, ads, 0.999).key, 'ad-wide-14');
        assert.strictEqual(adFor({ shape: 'wide' }, [], 0.5), null);
        // the generator owns the pin
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'generate_izakaya.py'), 'utf8');
        assert.ok(tool.includes("((6, 36), 'wide', 'ad-wide-03')") && tool.includes("((8, 36), 'square', 'ad-square-01')"));
    });

    test("Inaka's farmhouse is a sealed house again: no door, no way to the Izakaya from Inaka (#68)", () => {
        const c = cfg(), inaka = c.rooms.Inaka, name = (t) => c.tilePalette[t];
        assert.deepStrictEqual(inaka.transporters.map((t) => t.targetRoom), ['InakaStation']);
        // the red farmhouse still stands beside the pond, and its doorway (13,16) is solid like its walls
        assert.strictEqual(name(tiles(inaka, 'Collidables')['12,16']), 'building-entrance-3_0_0');
        for (const x of [12, 13, 14]) assert.ok(`${x},16` in tiles(inaka, 'Colliders'), `farmhouse front ${x},16 is open`);
        assert.ok(!JSON.stringify(c.rooms.Izakaya.transporters).includes('Inaka'));
        // the generators agree: Inaka's no longer builds or names the Izakaya, the Izakaya has its own
        const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
        assert.ok(!/rooms'\]\['Izakaya'\]|targetRoom.*Izakaya|'Izakaya',/.test(tool('generate_inaka.py')));
        assert.ok(/'generate_izakaya'/.test(tool('check_generators.py')), 'check_generators.py does not run generate_izakaya');
    });

    test('you can walk from the Tokyo start into the Izakaya and back out onto the pavement, stitched or not', () => {
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            if (stitch) {
                // one walk, no fade: the start (Tokyo 29,38) to the cell in front of the door
                const to = rm.resolve('Market', 7, 38);
                const route = world.path(to.x, to.y);
                assert.ok(route && route.length > 0, 'no path from the Tokyo start to the Izakaya door');
                for (const dir of route) assert.ok(world.step(dir).moved, `blocked on the way (${dir})`);
                // the door is a doorway of the city room, so NPCManager.atDoorway keeps wanderers off its front cell
                const door = rm.resolve('Market', 7, 37);
                assert.ok(rm.rooms.TokyoCity.transporters.some((t) => t.gridX === door.x && t.gridY === door.y && t.targetRoom === 'Izakaya'));
            } else {
                world.enter('Market', 7, 38);
            }
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 7, 38], tag);
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, 'Izakaya', tag);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Izakaya', 9, 12], tag);
            const out = world.step('s');
            assert.ok(out.transported, `${tag}: the mat below the arrival cell is the way out`);
            assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], ['Market', 7, 38], tag);
            assert.strictEqual(world.step('s').moved, true, `${tag}: boxed in outside the door`);
        }
    });
};
