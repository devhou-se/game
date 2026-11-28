// The concourse inside the station with the clocks in San Franbourne (issue #246): tools/generate_flinders.py,
// tools/generate_flinders_art.py. The checks it shares with the pub, the distillery and the mall are
// tools/tests/interiors.js. (The blog stands nobody at the station, so there is no STAND and no visitor's cell.)
module.exports = (helpers) => {
    const { test, assert, game, load } = helpers;
    const HOST = 'SanFranbourne', KEY = 'FlindersSanFranbourne1', NAME = 'Flinders St';
    const I = require('./interiors')(helpers, { HOST, KEY, NAME, MARK: 'flinders', SPRITE: 'sfb-clocks-station_0_0', DOORS: [[5, 6], [6, 6]], PREFIX: 'flinders-in-', BEHIND: 2 });
    const { cfg, tiles, plain, src, K } = I;
    const KINDS = ['clock', 'replacement-buses', 'ticket-machine'];
    // the gate line, from where the pieces stand: its row, the cells you walk through, the clocks between the banks
    const gateLine = (room, c) => {
        const gates = I.placed(room, c, 'station-gate_0_0').map(([x, y]) => [x, y + 1]).sort((a, b) => a[0] - b[0]);   // a gate is drawn from the row above
        const [cx, cy] = I.one(room, c, 'clocks'), [cw, ch] = I.size(c, 'flinders-in-clocks_0_0');
        return { gates, row: gates[0][1], clocks: { x: cx, y: cy, w: cw, h: ch, foot: cy + ch - 1 } };
    };

    test('the station with the clocks in San Franbourne opens: the two cells under its clocks lead into the concourse, and each mat inside back to the boardwalk in front of its own door (#246)', () => {
        const c = cfg();
        const { doors, mats, ways } = I.doorsOpen(c);
        assert.strictEqual(doors.length, 2);
        assert.strictEqual(mats.length, 2, 'a mat for each door');
        // the doors are the sixth and seventh columns of the station's front row: the two under the board of clocks
        const { sprite } = I.outside(c), [w, h] = I.size(c, 'sfb-clocks-station_0_0');
        assert.deepStrictEqual([w, h], [12, 7]);
        assert.deepStrictEqual(doors, [[sprite[0] + 5, sprite[1] + h - 1], [sprite[0] + 6, sprite[1] + h - 1]]);
        // the west door puts you on the west half of the doorway, the east on the east: you do not swap sides
        assert.deepStrictEqual(ways.map((t) => [t.targetX, t.targetY]), mats.map((m) => [m.gridX, m.gridY - 1]));
        assert.ok(mats[0].gridX + 1 === mats[1].gridX && mats[0].gridY === mats[1].gridY);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Flinders/.test(k)), [KEY]);
        // a concourse is lit: it is not a lantern-lit room; nothing is sold in it and nobody lives in it
        const room = c.rooms[KEY];
        assert.deepStrictEqual([room.interior, room.lanternLight, room.shopEnabled, room.npcs], [true, undefined, false, []]);
        // ...and no train is caught from it: it is no station of the departures board, and no station names it or its town
        assert.ok(!(KEY in c.stations));
        assert.ok(!/Flinders|SanFranbourne/.test(JSON.stringify(c.stations)), 'San Franbourne is reached by air');
    });

    test('nobody stands in the station\'s doorway in San Franbourne on any date, and no wanderer steps into it (#246)', () => {
        const c = cfg(), host = c.rooms[HOST], { doors, fronts } = I.outside(c);
        const cells = doors.concat(fronts).map(([x, y]) => K(x, y));
        const inWay = host.npcs.flatMap((n) => [['base', n], ...Object.entries(n.states || {})]
            .filter(([, s]) => cells.includes(K(s.gridX, s.gridY))).map(([date]) => `${n.name} ${date}`));
        assert.deepStrictEqual(inWay, []);
        // a wanderer keeps off a doorway and the cells beside it (NPCManager.atDoorway)
        const mgr = game('Object.create(NPCManager.prototype)');
        mgr.scene = { roomManager: { currentRoom: 'here', rooms: { here: host } } };
        for (const cell of cells) assert.ok(mgr.atDoorway(...cell.split(',').map(Number)), `a wanderer may stand on ${cell}`);
    });

    test('Flinders St is a station nobody catches a train from: the wall and its name, an empty track, a platform behind two banks of gates, the clocks between them, a terrazzo concourse (#246)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 24, 18]);
        const cells = I.floor(room), xs = [...new Set(cells.map(([x]) => x))].sort((a, b) => a - b), top = Math.min(...cells.map(([, y]) => y));
        assert.deepStrictEqual([xs[0], xs[xs.length - 1], top], [2, 21, 4]);
        // the back wall, three rows tall and solid from end to end: a bay, a window, the name board, a window, a bay
        assert.deepStrictEqual(['wall-bay', 'wall-arch', 'wall-name'].map((p) => I.size(c, `flinders-in-${p}_0_0`)), [[3, 3], [4, 3], [6, 3]]);
        const wall = ['wall-bay', 'wall-arch', 'wall-name'].flatMap((p) => I.at(room, c, p).map(([x, y]) => [x, y, p])).sort((a, b) => a[0] - b[0]);
        assert.deepStrictEqual(wall, [[2, 1, 'wall-bay'], [5, 1, 'wall-arch'], [9, 1, 'wall-name'], [15, 1, 'wall-arch'], [19, 1, 'wall-bay']]);
        for (const x of xs) for (let y = 1; y <= 3; y++) assert.ok(K(x, y) in solid, `back wall ${x},${y}`);
        // the track: two rows under the wall, the kit's rails over ballast, in the way from end to end. No train
        const floor = tiles(room, 'Floor'), over = tiles(room, 'Over Floor');
        for (const x of xs) {
            assert.deepStrictEqual([top, top + 1].map((y) => c.tilePalette[over[K(x, y)]]), ['station-track-n_0_0', 'station-track-s_0_0'], `track ${x}`);
            assert.deepStrictEqual([top, top + 1].map((y) => [c.tilePalette[floor[K(x, y)]], K(x, y) in solid]), [['station-ballast_0_0', true], ['station-ballast_0_0', true]], `track ${x}`);
            assert.strictEqual(c.tilePalette[floor[K(x, top + 2)]], 'station-platform-edge_0_0', `the platform's edge ${x}`);
        }
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /train|shinkansen|carriage|loco/.test(k)), 'a train');
        // the gate line: of its whole row only the four gate cells are open...
        const { gates, row, clocks } = gateLine(room, c);
        assert.strictEqual(gates.length, 4);
        assert.ok(gates.every(([, y]) => y === row) && row > top + 2);
        assert.deepStrictEqual(xs.filter((x) => !(K(x, row) in solid)), gates.map(([x]) => x), 'the only ways through are the gates');
        assert.ok(gates[0][0] + 1 === gates[1][0] && gates[2][0] + 1 === gates[3][0], 'two banks of two');
        for (const end of ['station-gate-end-w_0_0', 'station-gate-end-e_0_0']) assert.strictEqual(I.placed(room, c, end).length, 2, end);
        // ...the clocks stand between the banks, in line with the doorway: the foot row in the way, the dials walked behind
        assert.deepStrictEqual([clocks.w, clocks.h, clocks.foot], [4, 3, row]);
        assert.ok(gates[1][0] < clocks.x && clocks.x + clocks.w - 1 < gates[2][0], 'between the banks');
        const mats = room.transporters.map((t) => t.gridX).sort((a, b) => a - b), last = room.transporters[0].gridY - 1;
        assert.deepStrictEqual(mats, [clocks.x + 1, clocks.x + 2], 'in line with the doorway');
        for (let x = clocks.x; x < clocks.x + clocks.w; x++) {
            assert.deepStrictEqual([clocks.y, clocks.y + 1, clocks.foot].map((y) => K(x, y) in solid), [false, false, true], `clocks ${x}`);
        }
        assert.ok(K(clocks.x, clocks.y) in tiles(room, 'Collidables'), 'the clocks are depth-sorted with whoever walks behind them');
        // the machines against the west wall and the board against the east one, on the gate line
        const [tickets, board] = [I.one(room, c, 'tickets'), I.one(room, c, 'board')];
        assert.deepStrictEqual([tickets, board], [[xs[0], row], [xs[xs.length - 1] - 2, row]]);
        // terrazzo underfoot south of the gate line, the concourse's own; the platform is the kit's
        for (const [x, y] of cells) {
            const key = c.tilePalette[floor[K(x, y)]];
            if (y > row) assert.ok(/^flinders-in-floor-[ab]_/.test(key), `floor ${x},${y}: ${key}`);
            else if (y > top + 2) assert.strictEqual(key, 'station-floor_0_0', `platform ${x},${y}`);
        }
        // none of another interior's pieces, none of the kit's Japanese ones (its kiosk, its machines, its boards
        // and signs, its lantern-headed lamp), and no bins
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-|temple-in-|pub-in-|distillery-in-|mall-in-|office-(?!void)|konbini-)/.test(k)), 'none of another interior\'s pieces');
        assert.ok(![...used].some((k) => /^station-(kiosk|ticket-machines|departures|platform-sign|postbox|name-|exit-sign|board-|lamp-post)/.test(k)), 'none of the kit\'s Japanese pieces');
        assert.ok(![...used].some((k) => /bin/.test(k)), 'no bins');
        // every cell of the floor that is not solid can be walked to from the door: the concourse and the platform
        const { seen, open } = I.reach(c);
        const lost = [...open].filter((k) => !(k in solid) && !seen.has(k));
        assert.deepStrictEqual(lost, []);
        assert.ok(seen.size >= 120, `${seen.size} cells to walk on`);
        assert.ok(xs.every((x) => seen.has(K(x, top + 2))), 'the platform\'s edge, end to end');
        // ...and the gates are the only ways onto the platform: either bank alone still reaches it, neither does not
        const platform = (shut) => {
            const todo = [[mats[0], last]], got = new Set([K(mats[0], last)]);
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    const k = K(nx, ny);
                    if (got.has(k) || !open.has(k) || k in solid || (ny === row && shut.includes(nx))) continue;
                    got.add(k);
                    todo.push([nx, ny]);
                }
            }
            return [...got].some((k) => Number(k.split(',')[1]) < row);
        };
        const [west, east] = [gates.slice(0, 2).map(([x]) => x), gates.slice(2).map(([x]) => x)];
        assert.deepStrictEqual([platform([]), platform(west), platform(east), platform(west.concat(east))], [true, true, true, false]);
        // benches on the platform face the track; benches, pillars and planters stand in the concourse, the
        // planters either side of the doorway and not in it
        const benches = I.placed(room, c, 'station-bench-back_0_0'), seats = I.placed(room, c, 'station-bench_0_0');
        assert.ok(benches.length === 2 && benches.every(([, y]) => y + 1 < row) && seats.length === 2 && seats.every(([, y]) => y > row));
        const planters = I.placed(room, c, 'station-planter-a_0_0').concat(I.placed(room, c, 'station-planter-b_0_0'));
        assert.ok(planters.length === 2 && planters.every(([x, y]) => y + 1 === last && (x + 1 < mats[0] || x > mats[1])));
        assert.strictEqual(I.placed(room, c, 'station-pillar_0_0').length, 2);
        // nothing of the concourse glows at night: it is lit, and Glows has no row for it
        if (!game('typeof Glows !== "undefined"')) require('vm').runInContext(src('utils/Glows.js'), helpers.ctx, { filename: 'Glows.js' });
        assert.deepStrictEqual(plain(Object.keys(game('Glows').SPRITES).filter((k) => /^flinders-in-/.test(k))), []);
    });

    test('you walk in under the clocks in San Franbourne, bump the clocks, the board and the machines, go through a gate and along the platform, and walk out by the door you came in by (#246)', () => {
        const { world, config } = helpers.worldWith(false);
        I.walkThrough(world, config, '2026-02-01', KINDS, /says: "|opens the time-travel date picker/);
        const room = config.rooms[KEY], { gates, row, clocks } = gateLine(room, config);
        // through each gate, north onto the platform and back: nothing bumped, a gate is walked through
        for (const [gx] of gates) {
            world.enter(KEY, gx, row + 1);
            for (const dir of ['n', 'n', 's', 's']) {
                const step = world.step(dir);
                assert.deepStrictEqual(plain([step.moved, step.interaction || null]), [true, null], `gate at ${gx}: ${dir}`);
            }
            assert.deepStrictEqual([world.here().x, world.here().y], [gx, row + 1]);
        }
        // beside a bank the gate's end is in the way, and says nothing
        world.enter(KEY, gates[0][0] - 1, row + 1);
        const end = world.step('n');
        assert.deepStrictEqual(plain([end.moved, end.interaction || null]), [false, null]);
        // along the platform, from one end to the other, behind the dials of the clocks: nothing in the way
        world.enter(KEY, 2, row - 3);
        for (let x = 3; x <= 21; x++) {
            const step = world.step('e');
            assert.deepStrictEqual(plain([step.moved, step.interaction || null]), [true, null], `the platform's edge at ${x}`);
        }
        // the track is in the way, and says nothing: no train comes
        const track = world.step('n');
        assert.deepStrictEqual(plain([track.moved, track.interaction || null, track.transported || null]), [false, null, null]);
        // behind the clocks' head you walk; a step south into its foot is a bump, and it is a clock from either side
        world.enter(KEY, clocks.x, clocks.foot - 1);
        const behind = world.step('e');
        assert.deepStrictEqual(plain([behind.moved, behind.interaction || null]), [true, null]);
        for (const [y, dir] of [[clocks.foot - 1, 's'], [clocks.foot + 1, 'n']]) {
            world.enter(KEY, clocks.x + 1, y);
            const bump = world.step(dir);
            assert.deepStrictEqual(plain([bump.moved, bump.interaction.kind, bump.interaction.group]), [false, 'clock', 'clock']);
            assert.ok(/time-travel date picker/.test(world.describe(bump.interaction)));
        }
        // the board and the machines say their lines
        const [bx, by] = I.one(room, config, 'board'), [tx, ty] = I.one(room, config, 'tickets');
        world.enter(KEY, bx + 1, by + 2);
        assert.ok(/buses replace trains/.test(world.describe(world.step('n').interaction)));
        world.enter(KEY, tx + 1, ty + 2);
        assert.ok(/a card you do not have/.test(world.describe(world.step('n').interaction)));
    });

    test('the clocks inside the station are a clock, its board and its machines each say a line, and nothing else of the concourse is bumped; the clocks outside still say theirs (#246)', () => {
        const Rules = game('Interactions');
        const concourse = { interior: true, shopEnabled: false };
        const hit = (key) => plain(Rules.match(key, concourse, game('Shop.VENUES')));
        const clock = hit('flinders-in-clocks_0_0');
        assert.deepStrictEqual([clock.kind, clock.group, clock.footprint, clock.say || null], ['clock', 'clock', true, null]);
        const says = { board: 'replacement-buses', tickets: 'ticket-machine' };
        for (const [piece, kind] of Object.entries(says)) {
            const rule = hit(`flinders-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint && rule.say && rule.say.length <= 100, piece);
            assert.strictEqual(rule.say, rule.say.toLowerCase(), 'lower case, like every other line');
        }
        assert.ok(/buses replace trains/.test(hit('flinders-in-board_0_0').say) && /sold by the machine/.test(hit('flinders-in-tickets_0_0').say));
        for (const kind of Object.values(says)) assert.strictEqual(Rules.RULES.filter((r) => r.kind === kind).length, 1, kind);
        // every sprite the room is made of: the three above are bumped, the rest nothing at all
        const c = cfg(), room = c.rooms[KEY];
        const used = [...new Set(room.layers.filter((l) => l.name !== 'Colliders').flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]))];
        const groups = {};
        for (const key of used) { const rule = hit(key); if (rule) groups[key] = rule.group; }
        assert.deepStrictEqual(groups, { 'flinders-in-board_0_0': 'flavour', 'flinders-in-clocks_0_0': 'clock', 'flinders-in-tickets_0_0': 'flavour' });
        for (const piece of ['side-w', 'side-e', 'wall-front', 'threshold-w', 'threshold-e', 'floor-a', 'floor-b', 'wall-bay', 'wall-arch', 'wall-name', 'doorlight']) {
            assert.strictEqual(hit(`flinders-in-${piece}_0_0`), null, piece);
        }
        // the station on the street is what it was: its clocks say where everybody meets
        const outside = hit('sfb-clocks-station_0_0');
        assert.deepStrictEqual([outside.kind, outside.group], ['clocks', 'flavour']);
        assert.ok(/under the clocks/.test(outside.say));
        assert.ok(!game('Stamps').stores(game('decodeConfig')(c)).some((s) => s.id === KEY), 'not a store on the stamp card');
        // nothing new is saved, pressed or loaded for it
        assert.ok(!/flinders|replacement-buses|ticket-machine/i.test(src('GameScene.js')), 'three rows in one table');
    });

    test('the room is "Flinders St" on the bar, short enough to count down on a phone, and the map says it is in San Franbourne (#246)', () => {
        const c = cfg();
        I.named(c, `${NAME} (in ${c.rooms[HOST].name}, overseas)`);
        assert.strictEqual(c.rooms[HOST].name, 'San Franbourne');
    });

    test('on a phone the camera looks up at the station\'s back wall and its name from the platform, and in the concourse it is the ordinary camera (#246)', () => {
        const c = cfg(), room = c.rooms[KEY], look = c.game.lookUp, G = 64;
        if (!game('typeof LandmarkView !== "undefined"')) load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView');
        // the wall's three pieces are marked, by the art tool, with the track's two rows under them
        const WALL = ['wall-bay', 'wall-arch', 'wall-name'].map((p) => `flinders-in-${p}`);
        assert.deepStrictEqual(Object.keys(look.sprites).filter((k) => /^flinders-in-/.test(k)).sort(), [...WALL].sort());
        for (const family of WALL) assert.strictEqual(look.sprites[family], 2, family);
        assert.ok(/LOOK_UP = \{'flinders-in-wall-bay': 2, 'flinders-in-wall-arch': 2, 'flinders-in-wall-name': 2\}/.test(I.tool('generate_flinders_art.py')));
        const marks = plain(LandmarkView.index(WALL.flatMap((family) => I.placed(room, c, `${family}_0_0`).map(([x, y]) => {
            const [w, h] = I.size(c, `${family}_0_0`);
            return { key: `${family}_0_0`, left: x * G, top: y * G, width: w * G, height: h * G };
        })), look.sprites, G));
        assert.strictEqual(marks.length, 5);
        // their foot, for the camera, is the platform's edge: the first row you can stand on
        const xs = [...new Set(I.floor(room).map(([x]) => x))], edge = marks[0].feet / G, { row } = gateLine(room, c);
        assert.ok(marks.every((m) => m.feet === edge * G && m.top === G));
        assert.ok(xs.every((x) => c.tilePalette[tiles(room, 'Floor')[K(x, edge)]] === 'station-platform-edge_0_0'));
        // a landscape phone: the world at 2x, 7.5 rows of it in view, the room 18 rows tall
        const aim = (x, y) => plain(LandmarkView.aim({ x: x * G + 32, y: y * G + 32, landmarks: marks, grid: G, cells: look.cells, fade: look.fade,
            side: look.side, viewH: 480, bar: 20, deadzone: 128, foot: 128 }));
        // anywhere on the platform, end to end, the camera is as far up as it goes with two rows kept under you...
        for (const x of xs) for (let y = edge; y < row; y++) assert.deepStrictEqual(aim(x, y), { weight: 1, offset: 480 / 2 - 128 }, `platform ${x},${y}`);
        // ...so at the platform's edge the view's top is the wall's: the board with the name, the windows and the
        // lamps are all in it, where the ordinary camera showed the track and the wall's skirting
        assert.strictEqual(edge * G + 32 - aim(xs[5], edge).offset - 480 / 2, marks[0].top);
        assert.ok(edge * G + 32 + 128 / 2 - 480 / 2 >= marks[0].top + 2 * G, 'the ordinary camera can sit two rows lower');
        // ...it lets go as you walk south from the gates, and where you come in it is the ordinary camera
        assert.ok(aim(xs[5], row + 1).weight > aim(xs[5], row + 2).weight && aim(xs[5], row + 2).weight > 0);
        const mats = room.transporters.map((t) => t.gridY);
        for (const x of xs) for (let y = row + 3; y < Math.min(...mats); y++) assert.deepStrictEqual(aim(x, y), { weight: 0, offset: 0 }, `concourse ${x},${y}`);
        // a desktop window is tall enough for the wall and you: it follows you no higher, and only gives up the slack
        // of its deadzone, which could leave the wall's top row under the bar
        const desk = plain(LandmarkView.aim({ x: xs[5] * G + 32, y: edge * G + 32, landmarks: marks, grid: G, cells: look.cells, fade: look.fade,
            side: look.side, viewH: 960, bar: 40, deadzone: 256, foot: 128 }));
        assert.ok(desk.offset === 0 && desk.weight > 0.5, JSON.stringify(desk));
        assert.ok(edge * G + 32 + 256 * (1 - desk.weight) / 2 - 960 / 2 <= marks[0].top - 40, 'the wall\'s top is clear of the bar');
    });

    test('the station generator and its art tool are checked, own the doors through roomgen, and rebuild the same concourse from a sealed building (#246)', () => {
        I.plumbing({ generator: 'generate_flinders', art: 'generate_flinders_art', sprites: 14, after: 'mall-in-palm_0_0',
            owned: "FLINDERS_PREFIX: ('flinders', FLINDERS_DOORS)", table: "FLINDERS_DOORS = {'sfb-clocks-station_0_0': [(5, 6), (6, 6)]}" });
        assert.ok(/rg\.FLINDERS_DOORS/.test(I.tool('generate_flinders.py')), 'the generator has no door sprites of its own');
        // the frame is the pub's: the art tool draws none of its own
        const art = I.tool('generate_flinders_art.py');
        assert.ok(/from generate_pub_art import/.test(art) && !/def wall_side|def threshold/.test(art));
        // the town's generator knows nothing of the room: roomgen keeps the doors through a rebuild
        assert.ok(!/Flinders|flinders-in/.test(I.tool('generate_sanfranbourne.py')));
    });
};
