// The pub in Sendai (issue #217): tools/generate_pub.py, tools/generate_pub_art.py, Shop.VENUES.taproom.
// The checks it shares with the distillery and Canal City are tools/tests/interiors.js.
module.exports = (helpers) => {
    const { test, assert, game } = helpers;
    const HOST = 'Sendai', KEY = 'PubSendai1', NAME = 'The Pub';
    const I = require('./interiors')(helpers, { HOST, KEY, NAME, MARK: 'pub', SPRITE: 'sendai-pub_0_0', DOORS: [[2, 4]], STAND: [3, 5], PREFIX: 'pub-in-' });
    const { cfg, tiles, plain, src, K } = I;

    test('the pub in Sendai opens: the door in the middle of its front leads into a room of its own, and the mat inside back to the street (#217)', () => {
        const c = cfg();
        const { doors, mats } = I.doorsOpen(c);
        assert.strictEqual(doors.length, 1);
        assert.strictEqual(mats.length, 2, 'a doorway two cells wide');
        // the door is the middle of the building's front row
        const { sprite } = I.outside(c), [w, h] = I.size(c, 'sendai-pub_0_0');
        assert.deepStrictEqual(doors[0], [sprite[0] + (w - 1) / 2, sprite[1] + h - 1]);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Pub/.test(k)), [KEY]);
        assert.deepStrictEqual([c.rooms[KEY].interior, c.rooms[KEY].lanternLight, c.rooms[KEY].shopEnabled, c.rooms[KEY].npcs], [true, true, false, []]);
    });

    test('nobody stands in the pub\'s doorway on any date: Julia, who watched the baseball there, is on the pavement beside the door (#217)', () => {
        const c = cfg();
        const { stand } = I.nobodyInTheWay(c);
        const julia = c.rooms[HOST].npcs.find((n) => n.name === 'Julia').states['2025-10-29'];
        assert.deepStrictEqual([julia.gridX, julia.gridY], stand);
    });

    test('the pub is a pub: the back bar, the screen and the dartboard on the wall, a bar with stools, tables, booths, the specials, lamps (#217)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 20, 17]);
        // the back wall, three rows tall and solid from end to end
        const [bx, by] = I.one(room, c, 'wall-backbar'), [tx, ty] = I.one(room, c, 'wall-tv'), [dx] = I.one(room, c, 'wall-darts');
        assert.deepStrictEqual([bx, by, ty], [1, 1, 1]);
        assert.ok(tx > bx + 7 && dx > tx + 4, 'the back bar, then the screen, then the darts');
        for (let x = 1; x <= 18; x++) for (let y = 1; y <= 3; y++) assert.ok(K(x, y) in solid, `back wall ${x},${y}`);
        // the bar: under the back bar, flush to the west wall (nobody gets behind it), solid, two rows deep
        const [barX, barY] = I.one(room, c, 'bar'), [barW, barH] = I.size(c, 'pub-in-bar_0_0');
        assert.deepStrictEqual([barX, barY, barW, barH], [bx, by + 3, 7, 2]);
        for (let x = barX; x < barX + barW; x++) for (let y = barY; y < barY + barH; y++) assert.ok(K(x, y) in solid, `bar ${x},${y}`);
        // stools along its front, with a gap between each to reach the bar through
        const stools = I.at(room, c, 'stool').sort((a, b) => a[0] - b[0]);
        assert.ok(stools.length >= 3 && stools.every(([x, y]) => y === barY + barH && x < barX + barW && K(x, y) in solid));
        const gaps = [];
        for (let x = barX; x < barX + barW; x++) if (!(K(x, barY + barH) in solid)) gaps.push(x);
        assert.ok(gaps.length >= 3, 'places to stand at the bar');
        // tables with a chair either side, booths on the east wall, the chalkboard: all in the way, none walked through
        const tables = I.at(room, c, 'table');
        assert.ok(tables.length >= 3);
        for (const [x, y] of tables) {
            for (const cx of [x - 1, x, x + 1, x + 2]) assert.ok(K(cx, y) in solid, `table ${x},${y}`);
            assert.ok(I.at(room, c, 'chair-w').some(([a, b]) => a === x - 1 && b === y) && I.at(room, c, 'chair-e').some(([a, b]) => a === x + 2 && b === y));
        }
        const booths = I.at(room, c, 'booth');
        assert.strictEqual(booths.length, 2);
        for (const [x, y] of booths) {
            assert.strictEqual(x + 2, 19, 'against the east wall');
            for (let cx = x; cx < x + 2; cx++) for (let cy = y; cy < y + 3; cy++) assert.ok(K(cx, cy) in solid, `booth ${cx},${cy}`);
        }
        const [sx, sy] = I.one(room, c, 'chalkboard');
        assert.deepStrictEqual([K(sx, sy) in solid, K(sx, sy + 1) in solid], [false, true], 'the board\'s head is walked behind, its feet are not');
        // boards underfoot, the pub's own: none of another interior's pieces
        const floor = tiles(room, 'Floor');
        for (const [x, y] of I.floor(room)) assert.ok(/^pub-in-floor-[ab]_/.test(c.tilePalette[floor[K(x, y)]]), `floor ${x},${y}`);
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-|temple-in-|office-(?!void)|konbini-)/.test(k)), 'none of another interior\'s pieces');
        assert.ok(![...used].some((k) => /bin/.test(k)), 'no bins');
        // every cell of the floor that is not solid can be walked to from the door
        const { seen, open } = I.reach(c);
        const lost = [...open].filter((k) => !(k in solid) && !seen.has(k));
        assert.deepStrictEqual(lost, []);
        assert.ok(seen.size >= 100, `${seen.size} cells to walk on`);
        // lamps hang overhead, over the bar and over every table; they, the back bar and the screen glow at night
        const lamps = I.at(room, c, 'lamp-hang');
        assert.ok(lamps.length >= tables.length + 3 && lamps.every(([x, y]) => K(x, y) in tiles(room, 'Tops')));
        for (const [x, y] of tables) assert.ok(lamps.some(([a, b]) => a === x && b === y - 2), `a lamp over the table at ${x},${y}`);
        I.glow(c, 'lamp-hang');
        I.glow(c, 'wall-backbar');
        const [screen] = I.glow(c, 'wall-tv');
        assert.deepStrictEqual(screen.pulse, { period: 2600, depth: 0.25 }, 'the screen swells slowly; it does not strobe');
        assert.strictEqual(screen.color, game('Glows').COOL);
    });

    test('you walk in off the street in Sendai on the day of the baseball, order at the bar, bump the screen, the darts and the specials, and walk out again (#217)', () => {
        const { world, config } = helpers.worldWith(false);
        I.walkThrough(world, config, '2025-10-29', ['baseball', 'darts', 'specials', 'taproom'], /opens the THE PUB shop: |says: "/);
        // the bar is ordered at from the stools' row, between the stools
        world.enter(KEY, 1, 6);
        const bump = world.step('n');
        assert.deepStrictEqual(plain([bump.moved, bump.interaction.kind, bump.interaction.group]), [false, 'taproom', 'shop']);
        assert.ok(/^opens the THE PUB shop: Highball ¥\d+, Nama Beer ¥\d+, Edamame ¥\d+, Karaage ¥\d+$/.test(world.describe(bump.interaction)), world.describe(bump.interaction));
    });

    test('the bar is the taproom venue: the izakaya\'s four things, nothing bought, no stamp; the screen, the darts and the chalkboard each say a line (#217)', () => {
        const Rules = game('Interactions');
        const pub = { interior: true, shopEnabled: false };
        const hit = (key) => plain(Rules.match(key, pub, game('Shop.VENUES')));
        assert.deepStrictEqual(hit('pub-in-bar_0_0'), { kind: 'taproom', group: 'shop', footprint: true });
        const says = { 'wall-tv': 'baseball', 'wall-darts': 'darts', chalkboard: 'specials' };
        for (const [piece, kind] of Object.entries(says)) {
            const rule = hit(`pub-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint && rule.say && rule.say.length <= 100, piece);
        }
        assert.ok(/baseball/.test(hit('pub-in-wall-tv_0_0').say) && /gold chain/.test(hit('pub-in-wall-tv_0_0').say), 'post 505\'s own words');
        for (const piece of ['wall-backbar', 'wall-panel', 'wall-print', 'stool', 'table', 'chair-w', 'chair-e', 'booth', 'lamp-hang', 'floor-a', 'doorlight']) {
            assert.strictEqual(hit(`pub-in-${piece}_0_0`), null, piece);
        }
        // one rule each, and the airport's bar is still the only `pub`
        for (const kind of ['taproom', 'baseball', 'darts', 'specials', 'pub']) assert.strictEqual(Rules.RULES.filter((r) => r.kind === kind).length, 1, kind);
        const venue = game('Shop.VENUES').taproom, items = plain(game('Shop.DEFAULT_ITEMS'));
        assert.deepStrictEqual(items.filter((i) => venue.sells(i)).map((i) => i.name), ['Highball', 'Nama Beer', 'Edamame', 'Karaage']);
        assert.ok(!venue.buys && !venue.grills);
        const c = cfg();
        assert.strictEqual(game('Shop.titleFor')('taproom', c.rooms[KEY]), 'THE PUB');
        assert.strictEqual(game('Stamps').placeFor('taproom', KEY, c.rooms[KEY]), null);
        assert.ok(!game('Stamps').stores(game('decodeConfig')(c)).some((s) => s.id === KEY), 'not a store on the stamp card');
        // nothing new is saved, pressed or loaded for it
        assert.ok(!/taproom|pub-in-/.test(src('GameScene.js')), 'the scene knows nothing about it: one row in two tables');
    });

    test('the room is "The Pub" on the bar, short enough to count down on a phone, and the map says it is in Sendai (#217)', () => {
        I.named(cfg(), 'The Pub (in Sendai)');
    });

    test('the pub generator and its art tool are checked, own the door through roomgen, and rebuild the same pub from a sealed building (#217)', () => {
        I.plumbing({ generator: 'generate_pub', art: 'generate_pub_art', sprites: 21, after: 'temple-in-kuden_0_0',
            owned: "PUB_PREFIX: ('pub', PUB_DOORS)", table: "PUB_DOORS = {'sendai-pub_0_0': [(2, 4)]}" });
        assert.ok(/rg\.PUB_DOORS/.test(I.tool('generate_pub.py')), 'the generator has no door sprites of its own');
        // the town's generator knows nothing of the door: roomgen keeps it through a rebuild
        assert.ok(!/Pub|pub-in/.test(I.tool('generate_sendai.py').replace(/sendai-pub/g, '')));
    });
};
