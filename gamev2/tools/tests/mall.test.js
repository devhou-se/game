// Canal City's atrium in Fukuoka (issue #217): tools/generate_mall.py, tools/generate_mall_art.py. The
// checks it shares with the pub and the distillery are tools/tests/interiors.js.
module.exports = (helpers) => {
    const { test, assert, game } = helpers;
    const HOST = 'Fukuoka', KEY = 'MallFukuoka1', NAME = 'Canal City';
    const I = require('./interiors')(helpers, { HOST, KEY, NAME, MARK: 'mall', SPRITE: 'canal-city_0_0', DOORS: [[3, 5], [4, 5]], STAND: [2, 6], PREFIX: 'mall-in-', BEHIND: 2 });
    const { cfg, tiles, plain, src, K } = I;
    const FRONTS = ['fashion', 'toys', 'okonomiyaki', 'cafe', 'ramen'];
    const KINDS = ['mall-cafe', 'mall-fashion', 'mall-fountain', 'mall-okonomiyaki', 'mall-ramen', 'mall-toys'];
    // the canal's three rows and the columns the bridges and the fountain take, from where the pieces stand
    const water = (room, c) => {
        const bridges = I.at(room, c, 'bridge').sort((a, b) => a[0] - b[0]), [fx, fy] = I.one(room, c, 'fountain');
        const under = new Set(bridges.flatMap(([x]) => [x, x + 1]));
        return { bridges, under, fx, fy, rows: [fy, fy + 1, fy + 2] };
    };

    test('Canal City in Fukuoka opens: the two leaves of the door under its arch lead into the atrium, and each mat inside back to the plaza in front of its own leaf (#217)', () => {
        const c = cfg();
        const { doors, mats, ways } = I.doorsOpen(c);
        assert.strictEqual(doors.length, 2);
        assert.strictEqual(mats.length, 2, 'a mat for each leaf');
        // the doors are the middle two cells of the mall's front row
        const { sprite } = I.outside(c), [w, h] = I.size(c, 'canal-city_0_0');
        assert.deepStrictEqual(doors, [[sprite[0] + w / 2 - 1, sprite[1] + h - 1], [sprite[0] + w / 2, sprite[1] + h - 1]]);
        // (the mall's top two rows are roof, walked behind as they always were: nothing else of it opened)
        const solid = tiles(c.rooms[HOST], 'Colliders');
        for (let x = sprite[0]; x < sprite[0] + w; x++) assert.deepStrictEqual([0, 1, 2, 3, 4].map((dy) => K(x, sprite[1] + dy) in solid), [false, false, true, true, true], `column ${x}`);
        // the west leaf puts you on the west half of the doorway, the east on the east: you do not swap sides
        assert.deepStrictEqual(ways.map((t) => [t.targetX, t.targetY]), mats.map((m) => [m.gridX, m.gridY - 1]));
        assert.ok(mats[0].gridX + 1 === mats[1].gridX && mats[0].gridY === mats[1].gridY);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Mall/.test(k)), [KEY]);
        // an atrium is lit: it is not a lantern-lit room, as the pub and the distillery are
        assert.deepStrictEqual([c.rooms[KEY].interior, 'lanternLight' in c.rooms[KEY], c.rooms[KEY].shopEnabled, c.rooms[KEY].npcs], [true, false, false, []]);
    });

    test('nobody stands in Canal City\'s doorway on any date: Julia, who wrote about the mall, is on the plaza beside the doors (#217)', () => {
        const c = cfg();
        const { stand } = I.nobodyInTheWay(c);
        const julia = c.rooms[HOST].npcs.find((n) => n.name === 'Julia').states['2025-11-10'];
        assert.deepStrictEqual([julia.gridX, julia.gridY], stand);
    });

    test('Canal City is an atrium: five shopfronts between piers under two gallery levels, the canal through the floor, the fountain in it, two bridges, benches, palms, planters (#217)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 28, 23]);
        // the back wall, five rows tall and solid from end to end: pier, shop, pier ... pier
        assert.deepStrictEqual([I.size(c, 'mall-in-wall-pier_0_0'), ...FRONTS.map((f) => I.size(c, `mall-in-front-${f}_0_0`))], [[1, 5], ...FRONTS.map(() => [4, 5])]);
        assert.deepStrictEqual(I.at(room, c, 'wall-pier').sort((a, b) => a[0] - b[0]), [1, 6, 11, 16, 21, 26].map((x) => [x, 1]));
        assert.deepStrictEqual(FRONTS.map((f) => I.one(room, c, `front-${f}`)), [2, 7, 12, 17, 22].map((x) => [x, 1]));
        for (let x = 1; x <= 26; x++) for (let y = 1; y <= 5; y++) assert.ok(K(x, y) in solid, `back wall ${x},${y}`);
        // the canal: three rows from wall to wall on the Water layer, in the way everywhere but under the bridges
        const { bridges, under, fx, fy, rows } = water(room, c), wet = tiles(room, 'Water');
        assert.deepStrictEqual([I.size(c, 'mall-in-bridge_0_0'), I.size(c, 'mall-in-fountain_0_0')], [[2, 3], [4, 3]]);
        assert.strictEqual(bridges.length, 2);
        assert.ok(bridges.every(([x, y]) => y === fy && K(x, y) in tiles(room, 'Non-Collidables')), 'the bridges lie on the canal, under whoever crosses');
        assert.strictEqual(c.spriteMetadata['mall-in-bridge_0_0'].depthBias, -200);
        assert.ok(bridges[0][0] + 2 < fx && fx + 4 < bridges[1][0], 'a bridge either side of the fountain');
        const pieces = ['canal-n', 'canal', 'canal-s'];
        for (let x = 1; x <= 26; x++) {
            rows.forEach((y, n) => {
                const inFountain = x >= fx && x < fx + 4;
                const key = c.tilePalette[wet[K(x, y)]];
                if (inFountain) assert.strictEqual(key, undefined, `the fountain carries its own water at ${x},${y}`);
                else assert.ok(new RegExp(`^mall-in-${pieces[n]}-[ab]_0_0$`).test(key), `canal ${x},${y}: ${key}`);
                assert.strictEqual(K(x, y) in solid, !under.has(x), `canal ${x},${y}`);
            });
        }
        assert.ok(K(fx, fy) in tiles(room, 'Collidables'), 'the fountain stands in the canal');
        // drawn water, not a pond: nobody fishes indoors, and it is not the street canal's sprites (they are #219's)
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /^pond-autotile|^fukuoka-canal/.test(k)));
        // benches on both banks, each two cells wide: the foot row is in the way, the row above is walked behind
        const benches = (key) => I.placed(room, c, key);
        const north = benches('station-bench_0_0'), south = benches('station-bench-back_0_0');
        assert.ok(north.length >= 2 && north.every(([, y]) => y + 1 < rows[0] - 1), 'the north bank\'s benches face the water, a promenade between');
        assert.ok(south.length >= 4 && south.every(([, y]) => y === rows[2] + 1), 'the south bank\'s benches have their backs to you');
        const planters = benches('station-planter-a_0_0').concat(benches('station-planter-b_0_0'));
        assert.ok(planters.length >= 4);
        for (const [x, y] of north.concat(south, planters)) {
            assert.deepStrictEqual([K(x, y) in solid, K(x + 1, y) in solid, K(x, y + 1) in solid, K(x + 1, y + 1) in solid], [false, false, true, true], `${x},${y}`);
            assert.ok(!under.has(x) && !under.has(x + 1), `${x},${y} stands in a bridge's way`);
        }
        // planters either side of the door, not in it
        const mats = room.transporters.map((t) => t.gridX).sort((a, b) => a - b), last = room.transporters[0].gridY - 1;
        assert.ok(planters.some(([x, y]) => x + 2 === mats[0] && y + 1 === last) && planters.some(([x, y]) => x === mats[1] + 1 && y + 1 === last));
        // palms in tubs: the tub is in the way, the fronds are not; none where a bench or a bridge is
        const palms = I.at(room, c, 'palm');
        assert.ok(palms.length >= 2 && palms.every(([x, y]) => !(K(x, y) in solid) && K(x, y + 1) in solid && !under.has(x)));
        // pale paving underfoot, the atrium's own, under the canal too: none of another interior's pieces
        const floor = tiles(room, 'Floor');
        for (const [x, y] of I.floor(room)) assert.ok(/^mall-in-floor-[ab]_/.test(c.tilePalette[floor[K(x, y)]]), `floor ${x},${y}`);
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-|temple-in-|pub-in-|distillery-in-|office-(?!void)|konbini-)/.test(k)), 'none of another interior\'s pieces');
        assert.ok(![...used].some((k) => /bin/.test(k)), 'no bins');
        // every cell of the floor that is not solid can be walked to from the door: both banks and both bridges
        const { seen, open } = I.reach(c);
        const lost = [...open].filter((k) => !(k in solid) && !seen.has(k));
        assert.deepStrictEqual(lost, []);
        assert.ok(seen.size >= 250, `${seen.size} cells to walk on`);
        for (const [x, y] of bridges) for (let dx = 0; dx < 2; dx++) for (let dy = 0; dy < 3; dy++) assert.ok(seen.has(K(x + dx, y + dy)), `bridge ${x + dx},${y + dy}`);
        assert.ok(seen.has(K(fx, fy - 1)) && seen.has(K(fx, fy + 3)), 'the north bank and the south bank');
        // ...and the bridges are the only ways across: each one alone still reaches the north bank, neither does not
        const across = (shut) => {
            const todo = [[mats[0], last]], got = new Set([K(mats[0], last)]);
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    const k = K(nx, ny);
                    if (got.has(k) || !open.has(k) || k in solid || (rows.includes(ny) && shut.includes(nx))) continue;
                    got.add(k);
                    todo.push([nx, ny]);
                }
            }
            return got.has(K(fx, fy - 1));
        };
        const [west, east] = bridges.map(([x]) => [x, x + 1]);
        assert.deepStrictEqual([across([]), across(west), across(east), across(west.concat(east))], [true, true, true, false]);
        // nothing of the atrium glows at night: it is lit, and Glows has no row for it
        if (!game('typeof Glows !== "undefined"')) require('vm').runInContext(src('utils/Glows.js'), helpers.ctx, { filename: 'Glows.js' });
        assert.deepStrictEqual(plain(Object.keys(game('Glows').SPRITES).filter((k) => /^mall-in-/.test(k))), []);
    });

    test('you walk in off the plaza in Fukuoka on the day of the mall, bump the fountain and every shopfront, cross both bridges, and walk out by the leaf you came in by (#217)', () => {
        const { world, config } = helpers.worldWith(false);
        I.walkThrough(world, config, '2025-11-10', KINDS, /says: "/);
        const room = config.rooms[KEY], { bridges, fx, fy } = water(room, config);
        // over each bridge, north to south and back: four steps each way, nothing bumped
        for (const [bx] of bridges) {
            world.enter(KEY, bx, fy - 1);
            for (const dir of ['s', 's', 's', 's', 'e', 'n', 'n', 'n', 'n']) {
                const step = world.step(dir);
                assert.deepStrictEqual(plain([step.moved, step.interaction || null]), [true, null], `bridge at ${bx}: ${dir}`);
            }
            assert.deepStrictEqual([world.here().x, world.here().y], [bx + 1, fy - 1]);
            // beside it the water is in the way, and says nothing: there is no fishing here
            world.enter(KEY, bx - 1, fy - 1);
            const wet = world.step('s');
            assert.deepStrictEqual(plain([wet.moved, wet.interaction || null]), [false, null]);
        }
        // the fountain is bumped from either bank
        for (const [y, dir] of [[fy - 1, 's'], [fy + 3, 'n']]) {
            world.enter(KEY, fx + 1, y);
            const bump = world.step(dir);
            assert.deepStrictEqual(plain([bump.moved, bump.interaction.kind, bump.interaction.group]), [false, 'mall-fountain', 'flavour']);
            assert.ok(/water performance/.test(world.describe(bump.interaction)));
        }
        // a shop is not gone into: its doorway is part of the wall, and bumping it says its line
        const [sx, sy] = I.one(room, config, 'front-cafe');
        world.enter(KEY, sx + 2, sy + 5);
        const cafe = world.step('n');
        assert.deepStrictEqual(plain([cafe.moved, cafe.interaction.kind]), [false, 'mall-cafe']);
    });

    test('nothing is sold in the atrium: the fountain and the five shopfronts each say a line, and no piece of it is a shop or a pond (#217)', () => {
        const Rules = game('Interactions');
        const atrium = { interior: true, shopEnabled: false };
        const hit = (key) => plain(Rules.match(key, atrium, game('Shop.VENUES')));
        const says = Object.assign({ fountain: 'mall-fountain' }, ...FRONTS.map((f) => ({ [`front-${f}`]: `mall-${f}` })));
        for (const [piece, kind] of Object.entries(says)) {
            const rule = hit(`mall-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint && rule.say && rule.say.length <= 100, piece);
        }
        assert.ok(/water performance/.test(hit('mall-in-fountain_0_0').say) && /five floors up/.test(hit('mall-in-front-ramen_0_0').say));
        for (const kind of KINDS) assert.strictEqual(Rules.RULES.filter((r) => r.kind === kind).length, 1, kind);
        assert.deepStrictEqual(Object.values(says).sort(), KINDS);
        // every sprite the room is made of: the six above say a line, the rest nothing at all
        const c = cfg(), room = c.rooms[KEY];
        const used = [...new Set(room.layers.filter((l) => l.name !== 'Colliders').flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]))];
        const groups = {};
        for (const key of used) { const rule = hit(key); if (rule) groups[key] = rule.group; }
        assert.deepStrictEqual(Object.keys(groups).sort(), Object.keys(says).map((p) => `mall-in-${p}_0_0`).sort());
        assert.ok(Object.values(groups).every((g) => g === 'flavour'), 'no shop, no pond');
        for (const piece of ['wall-pier', 'canal-n-a', 'canal-a', 'canal-s-b', 'bridge', 'palm', 'floor-a', 'doorlight']) {
            assert.strictEqual(hit(`mall-in-${piece}_0_0`), null, piece);
        }
        assert.ok(!game('Stamps').stores(game('decodeConfig')(c)).some((s) => s.id === KEY), 'not a store on the stamp card');
        // nothing new is saved, pressed or loaded for it
        assert.ok(!/mall-in-|MallFukuoka/.test(src('GameScene.js')) && !/mall/i.test(src('Shop.js')), 'six rows in one table');
    });

    test('on a landscape phone the camera looks up at Canal City\'s back wall from the north bank: all five rows of it from against it, and south of the canal it is the ordinary camera (#258)', () => {
        const c = cfg(), room = c.rooms[KEY], look = c.game.lookUp, G = 64;
        if (!game('typeof LandmarkView !== "undefined"')) helpers.load('systems/LandmarkView.js');
        const LandmarkView = game('LandmarkView');
        // every piece of the wall is marked, by the art tool, and stands on the floor (no rows under it); nothing else of the atrium is
        const WALL = ['wall-pier', ...FRONTS.map((f) => `front-${f}`)].map((p) => `mall-in-${p}`);
        assert.deepStrictEqual(Object.keys(look.sprites).filter((k) => /^mall-in-/.test(k)).sort(), [...WALL].sort());
        for (const family of WALL) assert.strictEqual(look.sprites[family], 0, family);
        const art = I.tool('generate_mall_art.py');
        assert.ok(/^LOOK_UP = \{'mall-in-wall-pier': 0, \*\*\{f'mall-in-front-\{name\}': 0 for name in FRONTS\}\}$/m.test(art));
        assert.ok(/cfg\['game'\]\['lookUp'\]\['sprites'\]\.update\(LOOK_UP\)/.test(art), 'the art tool writes them');
        const marks = plain(LandmarkView.index(WALL.flatMap((family) => I.placed(room, c, `${family}_0_0`).map(([x, y]) => {
            const [w, h] = I.size(c, `${family}_0_0`);
            return { key: `${family}_0_0`, left: x * G, top: y * G, width: w * G, height: h * G };
        })), look.sprites, G));
        assert.strictEqual(marks.length, 6 + FRONTS.length);
        // together they are the wall: five rows from one side wall to the other, their foot the floor's first row
        const cells = I.floor(room), xs = [...new Set(cells.map(([x]) => x))], first = Math.min(...cells.map(([, y]) => y));
        assert.ok(marks.every((m) => m.top === G && m.feet === first * G && m.feet - m.top === 5 * G));
        assert.deepStrictEqual([Math.min(...marks.map((m) => m.left)), Math.max(...marks.map((m) => m.right))], [xs[0] * G, (xs[xs.length - 1] + 1) * G]);
        // a landscape phone (844x390): the world at 2x, 7.5 rows of it in view, the bar over half a row, the room 23 rows tall
        const phone = { viewH: 480, bar: 34.4, deadzone: 128, foot: 128 }, desk = { viewH: 960, bar: 40, deadzone: 256, foot: 128 };
        const aim = (x, y, view = phone) => plain(LandmarkView.aim(Object.assign({ x: x * G + 32, y: y * G + 32, landmarks: marks, grid: G,
            cells: look.cells, fade: look.fade, side: look.side }, view)));
        // against the wall and two rows back from it, end to end, the camera is as far up as it goes with two rows kept under you...
        for (const x of xs) for (let y = first; y < first + look.cells; y++) assert.deepStrictEqual(aim(x, y), { weight: 1, offset: 480 / 2 - 128 }, `north bank ${x},${y}`);
        // ...so against the wall the view's top is the wall's: both gallery levels and the shop signs are in it, where the
        // ordinary camera, trailing you north, left its top more than two rows down the wall
        assert.strictEqual(first * G + 32 - aim(xs[5], first).offset - 480 / 2, marks[0].top);
        assert.ok(first * G + 32 + 128 / 2 - 480 / 2 > marks[0].top + 2 * G, 'the ordinary camera sat more than two rows lower');
        // it lets go as you walk down to the quay, is all but gone on the canal's first row, and from there south
        // (the rest of the bridges, the south bank, the door) it is the ordinary camera
        const { rows, under } = water(room, c), bridge = [...under][0];
        for (let y = first + look.cells; y <= rows[0]; y++) assert.ok(aim(bridge, y).weight < aim(bridge, y - 1).weight && aim(bridge, y).weight > 0, `row ${y}`);
        assert.ok(aim(bridge, rows[0]).weight < 0.2);
        for (const [x, y] of cells) if (y > rows[0]) assert.deepStrictEqual(aim(x, y), { weight: 0, offset: 0 }, `south of the quay ${x},${y}`);
        // a desktop window is tall enough for the wall and you: against the wall it follows you no higher and only gives
        // up the slack of its deadzone, and over those same rows the wall's top stays clear of the bar
        const near = aim(xs[5], first, desk);
        assert.ok(near.offset === 0 && near.weight > 0.5, JSON.stringify(near));
        for (let y = first; y < first + look.cells; y++) {
            const a = aim(xs[5], y, desk);
            assert.ok(y * G + 32 - a.offset + 256 * (1 - a.weight) / 2 - 960 / 2 <= marks[0].top - 40, `desktop row ${y}: ${JSON.stringify(a)}`);
        }
    });

    test('the room is "Canal City" on the bar, short enough to count down on a phone, and the map says it is in Fukuoka (#217)', () => {
        I.named(cfg(), 'Canal City (in Fukuoka)');
    });

    test('the mall generator and its art tool are checked, own the doors through roomgen, and rebuild the same atrium from a sealed building (#217)', () => {
        I.plumbing({ generator: 'generate_mall', art: 'generate_mall_art', sprites: 23, after: 'distillery-in-lamp-hang_0_0',
            owned: "MALL_PREFIX: ('mall', MALL_DOORS)", table: "MALL_DOORS = {'canal-city_0_0': [(3, 5), (4, 5)]}" });
        assert.ok(/rg\.MALL_DOORS/.test(I.tool('generate_mall.py')), 'the generator has no door sprites of its own');
        // the frame is the pub's: the art tool draws none of its own; the shopfronts are one function and a table
        const art = I.tool('generate_mall_art.py');
        assert.ok(/from generate_pub_art import/.test(art) && !/def wall_side|def threshold/.test(art));
        assert.ok(/^FRONTS = \{/m.test(art) && (art.match(/^def front/gm) || []).length === 1);
        // the bridge is laid flat by the art tool, as the taiko bridge is by its own
        assert.ok(/DEPTH_BIAS = \{'mall-in-bridge': -200/.test(art));
        // the town's generator and the street canal's art tool know nothing of the room: roomgen keeps the doors through a rebuild
        assert.ok(!/Mall|mall-in/.test(I.tool('generate_fukuoka.py')) && !/Mall|mall-in/.test(I.tool('generate_fukuoka_town_art.py')));
    });
};
