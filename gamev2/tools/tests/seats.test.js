// Sitting on furniture (#227): the table (src/utils/Seats.js), the seat step (CollisionSystem.checkSeatStep),
// the headless model's side of it (tools/world-model.js) and where the shipped world's seats are.
module.exports = ({ test, assert, fs, path, GV2, game, worldWith }) => {
    const Seats = () => game('Seats');
    // a sprite's size in pixels, from its PNG header
    const pixels = (key) => {
        const b = Buffer.alloc(24), fd = fs.openSync(path.join(GV2, 'assets', 'sprites', key + '.png'), 'r');
        fs.readSync(fd, b, 0, 24, 0);
        fs.closeSync(fd);
        return [b.readUInt32BE(16), b.readUInt32BE(20)];
    };
    // one model of the shipped world for this file, with nobody in it; every test enters its own room
    let shipped = null;
    const worldIn = (room, x, y) => {
        if (!shipped) shipped = worldWith(true).world;
        shipped.unpeopled = true;
        shipped.enter(room, x, y);
        return shipped;
    };
    const cell = (seat) => seat && [seat.kind, seat.key, seat.x + ',' + seat.y, 'row ' + seat.row, seat.solid ? 'solid' : 'open'].join(' ');

    test('seats: every family of furniture to sit on has its kind and pose in the table (#227)', () => {
        const S = Seats();
        // [sprite key, kind, the way you face on it (none: the way you came), whether a piece of it is drawn over you]
        const families = [
            ['izakaya-stool_0_0', 'stool', undefined, false],
            ['devhouse-stool_0_0', 'stool', undefined, false],
            ['devhouse-garden-seat_0_0', 'stool', undefined, false],
            ['devhouse-chair-n_0_0', 'chair', 'down', false],
            ['devhouse-chair-s_0_0', 'chair', 'up', true],
            ['devhouse-chair-w_0_0', 'chair', 'right', false],
            ['devhouse-chair-e_0_0', 'chair', 'left', false],
            ['devhouse-armchair_0_0', 'armchair', 'down', false],
            ['devhouse-toilet_0_0', 'toilet', 'down', false],
            ['lobby-sofa_0_0', 'sofa', 'down', false],
            ['lobby-sofa-back_0_0', 'sofa', 'up', true],
            ['devhouse-sofa_0_0', 'sofa', 'right', false],
            ['station-bench_0_0', 'bench', 'down', false],
            ['station-bench-back_0_0', 'bench', 'up', false],
            ['odori-bench_0_0', 'bench', 'down', false],
            ['temple-in-bench_0_0', 'bench', undefined, false],
            ['deck-in-bench_0_0', 'bench', 'up', true],
            ['airport-seats_0_0', 'seats', 'down', false],
        ];
        for (const [key, kind, face, cover] of families) {
            const rule = S.match(key);
            assert.ok(rule, key + ' is a seat');
            assert.strictEqual(rule.kind, kind, key);
            assert.strictEqual(rule.pose.face, face, key + ' faces');
            assert.strictEqual(!!rule.pose.cover, cover, key + ' cover');
        }
        // the ones you lie in: the pillow row carries the pose and the blanket, the foot row is only stood on
        for (const [key, kind] of [['home-bed_0_0', 'bed'], ['home-futon-blue_0_0', 'futon'], ['home-futon-rose_0_0', 'futon'], ['devhouse-bunk_0_0', 'bunk']]) {
            const rule = S.match(key);
            assert.strictEqual(rule && rule.kind, kind, key);
            assert.strictEqual(rule.pose[0].face, 'down', key);
            assert.ok(rule.pose[0].dy > 0 && rule.pose[0].cover, key + ': tucked in on the pillow row');
            assert.strictEqual(JSON.stringify(rule.pose[1]), '{}', key + ': nothing on the foot row');
        }
        const bath = S.match('devhouse-bath_0_0');
        assert.strictEqual(bath.kind, 'bath');
        assert.ok(bath.pose[0].cover && bath.pose[1].cover, 'the bath\'s rim is over you on both rows');
        // the sofa seen from the front and from behind are two rows, whichever comes first in the table
        assert.notStrictEqual(S.match('lobby-sofa_0_0'), S.match('lobby-sofa-back_0_0'));
        assert.ok(!S.match('station-bench_0_0').open && S.match('station-bench-back_0_0').open, 'only the bench with its back to you is on open floor');
        // not seats: you sit AT a kotatsu, a table is a table, a zabuton is flat on the floor already
        for (const key of ['home-kotatsu-indigo_0_0', 'home-kotatsu-red_0_0', 'home-table_0_0', 'lobby-table_0_0', 'devhouse-table-small_0_0',
            'devhouse-table-wide_0_0', 'devhouse-side-table_0_0', 'palace-in-table_0_0', 'home-zabuton-red_0_0', 'shrine-in-zabuton_0_0',
            'palace-in-zabuton_0_0', 'gk_blank', 'home-tv_0_0', '', null, undefined, 7]) {
            assert.strictEqual(S.match(key), null, String(key));
        }
    });

    test('seats: every row of the table is furniture the shipped world has, and its pose fits the sprite (#227)', () => {
        const S = Seats();
        const placed = new Set();
        for (const room of Object.values(worldWith(true).config.rooms)) {
            for (const layer of room.layers || []) for (const key of Object.values(layer.tiles || {})) placed.add(key);
        }
        for (const rule of S.RULES) {
            const keys = [...placed].filter(k => S.match(k) === rule);
            assert.ok(keys.length, `no sprite in the world for ${rule.pattern}: a dead row`);
            for (const key of keys) {
                const [w, h] = pixels(key);
                assert.ok(w % 64 === 0 && h % 64 === 0, `${key} is ${w}x${h}: not whole cells`);
                const poses = Array.isArray(rule.pose) ? rule.pose : [rule.pose];
                if (Array.isArray(rule.pose)) assert.strictEqual(rule.pose.length, h / 64, `${key}: one pose per row of the sprite`);
                for (const pose of poses) {
                    assert.ok(pose.face === undefined || ['up', 'down', 'left', 'right'].includes(pose.face), `${key}: face ${pose.face}`);
                    assert.ok(pose.dy === undefined || (Number.isInteger(pose.dy) && Math.abs(pose.dy) < 64), `${key}: dy ${pose.dy}`);
                    if (rule.at) for (const [c, r] of rule.at) assert.ok(c >= 0 && r >= 0 && c < w / 64 && r < h / 64, `${key}: the seat cell ${c},${r} is outside the sprite`);
                    if (!pose.cover) continue;
                    const [cx, cy, cw, ch] = pose.cover;
                    assert.ok(cx >= 0 && cy >= 0 && cw > 0 && ch > 0 && cx + cw <= w && cy + ch <= h, `${key}: cover ${pose.cover} is outside the ${w}x${h} sprite`);
                }
            }
        }
    });

    test('seats: the index gives the blocked cells of a seat, or the open ones of a bench seen from behind (#227)', () => {
        const house = worldIn('HouseFukuoka1', 6, 6);
        const pillow = house.seatAt(5, 6), foot = house.seatAt(5, 7);
        assert.strictEqual(cell(pillow), 'bed home-bed_0_0 5,6 row 0 solid');
        assert.strictEqual(cell(foot), 'bed home-bed_0_0 5,6 row 1 solid');
        assert.ok(pillow.pose.cover && pillow.pose.face === 'down', 'the pillow row has the bed\'s pose');
        assert.strictEqual(JSON.stringify(foot.pose), '{}', 'the foot row has none');
        assert.deepStrictEqual([pillow.w, pillow.h], [1, 2]);
        assert.strictEqual(house.seatAt(6, 6), null, 'the floor beside the bed is not a seat');
        assert.strictEqual(house.seatAt(9, 3), null, 'nor is other blocked furniture (the television)');

        // the station bench is a 2x2 sprite whose top row is its back, over floor you walk on: only the seat row counts
        const station = worldIn('AsahikawaStation', 6, 6);
        const bench = (x, y) => { const s = station.seatAt(x, y); return s && s.key === 'station-bench_0_0' && s.x === 5 && s.y === 11 ? cell(s) : null; };
        assert.strictEqual(bench(5, 12), 'bench station-bench_0_0 5,11 row 1 solid');
        assert.strictEqual(bench(6, 12), 'bench station-bench_0_0 5,11 row 1 solid');
        assert.strictEqual(bench(5, 11), null);
        assert.strictEqual(bench(6, 11), null);
        // ...and the bench with its back to you is the other way round: its walkable cells, never a step onto anything
        assert.strictEqual(cell(station.seatAt(6, 7)), 'bench station-bench-back_0_0 6,7 row 0 open');
        assert.strictEqual(cell(station.seatAt(7, 7)), 'bench station-bench-back_0_0 6,7 row 0 open');
        assert.strictEqual(station.blocked.has('6,7') || station.blocked.has('7,7'), false);

        // where two pieces overlap, the first to claim a cell keeps it; a cell with no collider is not a solid seat's
        const S = Seats();
        const room = { layers: [{ tiles: { '1,1': 'home-bed_0_0', '1,2': 'devhouse-stool_0_0', '4,1': 'devhouse-stool_0_0' } }] };
        const index = S.index(room, { sizeOf: (k) => (/bed/.test(k) ? [1, 2] : [1, 1]), isBlocked: (x) => x === 1 });
        assert.strictEqual([...index.keys()].join(' '), '1,1 1,2');
        assert.strictEqual(S.lookup(index, 1, 2).kind, 'bed');
        assert.strictEqual(S.lookup(index, 4, 1), null);
    });

    test('seats: only the player\'s own straight step is let onto a seat, and collision is as it was (#227)', () => {
        const world = worldIn('HouseFukuoka1', 6, 6);
        const cs = world.collisionSystem, bed = world.seatAt(5, 6);
        assert.strictEqual(cs.checkSeatStep(world.player, bed, 5, 6, 6, 6), true, 'the player, straight onto the bed');
        assert.strictEqual(cs.checkSeatStep(world.player, bed, 5, 6, 6, 5), false, 'not diagonally');
        assert.strictEqual(cs.checkSeatStep(world.player, bed, 5, 6, 7, 6), false, 'not from two cells away');
        assert.strictEqual(cs.checkSeatStep(world.player, null, 5, 5, 6, 5), false, 'not onto furniture that is no seat');
        assert.strictEqual(cs.checkSeatStep(world.character('Hana', 6, 6), bed, 5, 6, 6, 6), false, 'not an NPC');
        const sleeper = world.character('Hana', 5, 6);
        world.room.npcs.push(sleeper);
        assert.strictEqual(cs.checkSeatStep(world.player, bed, 5, 6, 6, 6), false, 'not when somebody is on it');
        world.room.npcs.splice(world.room.npcs.indexOf(sleeper), 1);
        assert.strictEqual(cs.checkSeatStep(world.player, bed, 5, 6, 6, 6), true);
        // the collision check itself has not moved: the bed blocks, paths and reach stay off it
        assert.strictEqual(cs.checkCollision(world.player, 5, 6, 6, 6), false);
        assert.strictEqual(world.canStep(6, 6, 5, 6), false);
        assert.strictEqual(world.canSit(6, 6, 5, 6), true);
        const reach = world.reachable();
        assert.ok(reach.has('6,6') && reach.size > 20);
        for (const c of reach) {
            const [x, y] = c.split(',').map(Number), seat = world.seatAt(x, y);
            assert.ok(!seat || !seat.solid, 'reach holds the seat cell ' + c);
        }

        // an open seat cell is plain floor to the step: walked onto as ever, never through the seat step
        const station = worldIn('AsahikawaStation', 6, 6);
        const back = station.seatAt(6, 7);
        assert.strictEqual(back.solid, false);
        assert.strictEqual(station.collisionSystem.checkSeatStep(station.player, back, 6, 7, 6, 6), false);
        assert.strictEqual(station.canStep(6, 6, 6, 7), true);
        assert.strictEqual(station.canSit(6, 6, 6, 7), false);
    });

    test('seats: the model steps onto a seat and off it, and its paths go round (#227)', () => {
        const world = worldIn('HouseFukuoka1', 6, 6);
        const on = world.step('w');
        assert.strictEqual(on.moved, true);
        assert.strictEqual(on.seat.kind, 'bed');
        assert.strictEqual(on.interaction, null, 'this bed has nothing to say');
        assert.deepStrictEqual([world.player.gridX, world.player.gridY], [5, 6]);
        const along = world.step('s');
        assert.ok(along.moved && along.seat.row === 1, 'from the pillow to the foot of the bed');
        const wall = world.step('w');
        assert.ok(!wall.moved && !wall.seat, 'the wall behind the bed still stops you');
        const off = world.step('e');
        assert.ok(off.moved && !off.seat, 'and a step off is a step');
        assert.deepStrictEqual([world.player.gridX, world.player.gridY], [6, 7]);

        // furniture with a line says it when you get on, once: not again from its other cell
        const dorm = worldIn('DevhouseTokyo4F', 7, 4);
        const bunk = dorm.step('w');
        assert.ok(bunk.moved && bunk.seat.kind === 'bunk');
        assert.ok(bunk.interaction && bunk.interaction.group === 'flavour' && bunk.interaction.say, 'the bunk has its line');
        const down = dorm.step('s');
        assert.ok(down.moved && down.seat.kind === 'bunk');
        assert.strictEqual(down.interaction, null);

        // the stool at 4,6 stands between 4,7 and 4,5: two steps over it by hand, four round it for goto
        const bar = worldIn('Izakaya', 4, 7);
        assert.strictEqual(bar.seatAt(4, 6).kind, 'stool');
        assert.strictEqual(bar.path(4, 5).join(''), 'wnne');
        assert.strictEqual(bar.path(4, 6), null, 'and no path ends on a seat');
        assert.ok(bar.step('n').seat && bar.step('n').moved);
        assert.deepStrictEqual([bar.player.gridX, bar.player.gridY], [4, 5]);
    });

    test('seats: every seat in the shipped world can be got onto, and they open no floor but one cell in Sapporo (#227)', () => {
        const world = worldIn('HouseFukuoka1', 6, 6);
        const { reach } = world.survey(null, { npcs: false });
        world.unpeopled = true;
        let seats = 0;
        const missed = [], opened = [];
        for (const room of world.runtimeRooms()) {
            if (!reach[room].size) continue;
            const [fx, fy] = [...reach[room]][0].split(',').map(Number);
            world.enter(room, fx, fy);
            // everywhere the player gets to once seats can be stepped onto (and over)
            const seen = new Set(reach[room]), queue = [...seen].map(c => c.split(',').map(Number));
            while (queue.length) {
                const [x, y] = queue.shift();
                for (const [dx, dy] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
                    const c = (x + dx) + ',' + (y + dy);
                    if (seen.has(c) || !(world.canStep(x, y, x + dx, y + dy) || world.canSit(x, y, x + dx, y + dy))) continue;
                    seen.add(c);
                    queue.push([x + dx, y + dy]);
                }
            }
            world.seatAt(0, 0);
            for (const [c, seat] of world.seats) {
                if (!seat.solid) continue;
                seats++;
                if (!seen.has(c)) missed.push(`${room} ${c} ${seat.key}`);
            }
            for (const c of seen) {
                const [x, y] = c.split(',').map(Number), seat = world.seatAt(x, y);
                if (!reach[room].has(c) && !(seat && seat.solid)) opened.push(world.spot(room, x, y));
            }
        }
        assert.ok(seats > 200, `only ${seats} seat cells in the world`);
        assert.strictEqual(missed.join('; '), '', 'seat cells nobody can get onto');
        // the snowed-in cell behind an Odori bench: harmless, and the only floor a seat leads to
        assert.strictEqual(opened.join('; '), 'Sapporo 41,29');
    });

    test('seats: the lift slides from one cell\'s to the next, and you sort at the foot of what you are on (#227)', () => {
        const S = Seats();
        const seat = (dy, more) => Object.assign({ pose: dy === undefined ? {} : { dy }, solid: true, x: 5, y: 6, w: 1, h: 1 }, more);
        assert.strictEqual(S.dyAt(null, null, 0.5), 0, 'floor to floor');
        assert.strictEqual(S.dyAt(null, seat(14), 0), 0, 'floor to bed: starts on the floor');
        assert.strictEqual(S.dyAt(null, seat(14), 0.5), 7);
        assert.strictEqual(S.dyAt(null, seat(14), 1), 14);
        assert.strictEqual(S.dyAt(seat(-12), null, 0.25), -9, 'seat to floor');
        assert.strictEqual(S.dyAt(seat(-12), null, 1), 0);
        assert.strictEqual(S.dyAt(seat(-10), seat(14), 0.5), 2, 'seat to seat');
        assert.strictEqual(S.dyAt(seat(14), seat(), 1), 0, 'a pose with no dy is the cell itself');
        assert.strictEqual(S.dyAt(null, seat(14), 1.4), 14, 't is held to 0..1');
        assert.strictEqual(S.dyAt(null, seat(14), -0.2), 0);

        // feet on the pillow row of a bed at 5,6 are on row 7; the bed's foot is row 8
        const pillow = seat(14, { h: 2 });
        assert.strictEqual(S.footRow([pillow], 7), 8);
        assert.strictEqual(S.footRow([seat(0, { h: 2, row: 1 })], 8), 8, 'the same on its foot row');
        assert.strictEqual(S.footRow([seat(-10)], 7), 7, 'a one-cell chair: your own feet');
        assert.strictEqual(S.footRow([seat(-10), pillow], 6.5), 8, 'between two seats: the lower of them');
        assert.strictEqual(S.footRow([seat(6, { solid: false, h: 2 })], 7), 7, 'an open seat does not change the sort');
        assert.strictEqual(S.footRow([], 7.25), 7.25);
        assert.strictEqual(S.footRow([null, pillow], 7), 8);

        assert.strictEqual(S.canStepOn(pillow, 6, 6, 5, 6), true);
        assert.strictEqual(S.canStepOn(pillow, 6, 5, 5, 6), false);
        assert.strictEqual(S.canStepOn(pillow, 5, 6, 5, 6), false);
        assert.strictEqual(S.canStepOn(seat(6, { solid: false }), 6, 6, 5, 6), false);
        assert.strictEqual(S.canStepOn(null, 6, 6, 5, 6), false);
    });

    test('seats: `at` keeps only the listed cells, and a ramen counter\'s middle stool is the seat (#367)', () => {
        const S = Seats();
        // a made-up room: a 3x3 stall with every cell blocked, and the rule keeps the one cell it lists
        const rule = { kind: 'stool', pattern: /^yatai-ramen_/, at: [[1, 2]], pose: { face: 'up' } };
        S.RULES.unshift(rule);
        try {
            const room = { layers: [{ tiles: { '2,3': 'yatai-ramen_0_0' } }] };
            const index = S.index(room, { sizeOf: () => [3, 3], isBlocked: () => true });
            assert.strictEqual([...index.keys()].join(' '), '3,5');
        } finally { S.RULES.splice(S.RULES.indexOf(rule), 1); }

        const check = (room, stalls, label) => {
            const world = worldIn(room, stalls[0][0] + 1, stalls[0][1] + 4);
            for (const [x, y] of stalls) {
                for (let dx = 0; dx < 3; dx++) for (let dy = 0; dy < 3; dy++) {
                    const seat = world.seatAt(x + dx, y + dy);
                    if (dx === 1 && dy === 2) {
                        assert.ok(seat && seat.kind === 'stool' && seat.solid && seat.pose.face === 'up', `${label} ${x},${y}: the middle stool`);
                    } else assert.strictEqual(seat, null, `${label} ${x},${y}: ${x + dx},${y + dy} is no seat`);
                }
                assert.strictEqual(world.canSit(x + 1, y + 3, x + 1, y + 2), true, `${label} ${x},${y}: got onto from below`);
                assert.strictEqual(world.canStep(x + 1, y + 3, x + 1, y + 2), false, `${label} ${x},${y}: and still a wall to everything else`);
            }
        };
        check('Sapporo', [[18, 42], [21, 42], [24, 42]], 'the Susukino stall at');
        check('Fukuoka', [[10, 34], [22, 34], [38, 34], [50, 34]], 'the ramen yatai at');
    });
};
