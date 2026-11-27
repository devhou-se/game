// The Nikka distillery's tasting bar in Sendai (issue #217): tools/generate_distillery.py,
// tools/generate_distillery_art.py, Shop.VENUES.tasting. The checks it shares with the pub and Canal City
// are tools/tests/interiors.js.
module.exports = (helpers) => {
    const { test, assert, game } = helpers;
    const HOST = 'Sendai', KEY = 'DistillerySendai1', NAME = 'Distillery';
    const I = require('./interiors')(helpers, { HOST, KEY, NAME, MARK: 'distillery', SPRITE: 'sendai-kiln_0_0', DOORS: [[2, 5]], STAND: [3, 6], PREFIX: 'distillery-in-' });
    const { cfg, tiles, plain, src, K } = I;

    test('the distillery in Sendai opens: the kiln\'s door under the WHISKY sign leads into a room of its own, and the mat inside back to the lane (#217)', () => {
        const c = cfg();
        const { doors, mats } = I.doorsOpen(c);
        assert.strictEqual(doors.length, 1);
        assert.strictEqual(mats.length, 2, 'a doorway two cells wide');
        // the door is the middle of the kiln's front row
        const { sprite } = I.outside(c), [w, h] = I.size(c, 'sendai-kiln_0_0');
        assert.deepStrictEqual(doors[0], [sprite[0] + (w - 1) / 2, sprite[1] + h - 1]);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Distillery/.test(k)), [KEY]);
        assert.deepStrictEqual([c.rooms[KEY].interior, c.rooms[KEY].lanternLight, c.rooms[KEY].shopEnabled, c.rooms[KEY].npcs], [true, true, false, []]);
    });

    test('nobody stands in the kiln\'s doorway on any date: Damian and Julia, who wrote about the day out, are in the lane beside the door (#217)', () => {
        const c = cfg();
        const { stand } = I.nobodyInTheWay(c);
        for (const [who, date] of [['Damian', '2025-10-29'], ['Julia', '2025-10-30']]) {
            const s = c.rooms[HOST].npcs.find((n) => n.name === who).states[date];
            assert.deepStrictEqual([s.gridX, s.gridY], stand, who);
        }
    });

    test('the distillery is a tasting bar: one copper pot still, casks racked on the wall and stood on the floor, a counter under the bottles, stools, lamps (#217)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 20, 15]);
        // the back wall, three rows tall and solid from end to end: the casks, the windows, the shelf
        const [cx, cy] = I.one(room, c, 'wall-casks'), [wx] = I.one(room, c, 'wall-window'), [sx, sy] = I.one(room, c, 'wall-shelf');
        assert.deepStrictEqual([cx, cy, sy, sx + 5], [1, 1, 1, 19]);
        assert.ok(wx > cx + 4 && wx + 2 < sx, 'the casks, then the windows, then the shelf');
        for (let x = 1; x <= 18; x++) for (let y = 1; y <= 3; y++) assert.ok(K(x, y) in solid, `back wall ${x},${y}`);
        // one still, and only one: its pot and condenser are in the way, its neck and arm are walked behind
        const [stx, sty] = I.one(room, c, 'still');
        assert.deepStrictEqual(I.size(c, 'distillery-in-still_0_0'), [3, 4]);
        for (let x = stx; x < stx + 3; x++) {
            assert.deepStrictEqual([0, 1, 2, 3].map((dy) => K(x, sty + dy) in solid), [false, false, true, true], `still column ${x}`);
        }
        assert.strictEqual(sty, cy + 3, 'it stands against the back wall');
        // the counter: under the shelf, flush to the east wall (nobody gets behind it), solid, two rows deep
        const [barX, barY] = I.one(room, c, 'counter'), [barW, barH] = I.size(c, 'distillery-in-counter_0_0');
        assert.deepStrictEqual([barX, barY, barW, barH], [sx, sy + 3, 5, 2]);
        for (let x = barX; x < barX + barW; x++) for (let y = barY; y < barY + barH; y++) assert.ok(K(x, y) in solid, `counter ${x},${y}`);
        // stools along its front, a place to stand either side of each
        const stools = I.at(room, c, 'stool').sort((a, b) => a[0] - b[0]);
        assert.ok(stools.length >= 2 && stools.every(([x, y]) => y === barY + barH && x >= barX && K(x, y) in solid));
        const gaps = [];
        for (let x = barX; x < barX + barW; x++) if (!(K(x, barY + barH) in solid)) gaps.push(x);
        assert.ok(gaps.length >= 3, 'places to stand at the counter');
        // casks on end, each in the way, none in front of the door or the counter
        const casks = I.at(room, c, 'cask');
        assert.ok(casks.length >= 3 && casks.every(([x, y]) => K(x, y) in solid && y > barY + barH));
        const mats = room.transporters.map((t) => t.gridX);
        assert.ok(!casks.some(([x]) => mats.includes(x)), 'the way in from the door is clear');
        // flags underfoot, the distillery's own: none of another interior's pieces
        const floor = tiles(room, 'Floor');
        for (const [x, y] of I.floor(room)) assert.ok(/^distillery-in-floor-[ab]_/.test(c.tilePalette[floor[K(x, y)]]), `floor ${x},${y}`);
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-|temple-in-|pub-in-|office-(?!void)|konbini-)/.test(k)), 'none of another interior\'s pieces');
        assert.ok(![...used].some((k) => /bin/.test(k)), 'no bins');
        // every cell of the floor that is not solid can be walked to from the door
        const { seen, open } = I.reach(c);
        const lost = [...open].filter((k) => !(k in solid) && !seen.has(k));
        assert.deepStrictEqual(lost, []);
        assert.ok(seen.size >= 100, `${seen.size} cells to walk on`);
        // lamps hang overhead, over the counter and by the still; they and the windows glow at night
        const lamps = I.at(room, c, 'lamp-hang');
        assert.ok(lamps.length >= 4 && lamps.every(([x, y]) => K(x, y) in tiles(room, 'Tops')));
        assert.ok(lamps.filter(([x]) => x >= barX).length >= 2, 'over the counter');
        assert.ok(lamps.some(([x]) => x === stx - 1) && lamps.some(([x]) => x === stx + 3), 'either side of the still');
        I.glow(c, 'lamp-hang');
        const [pane] = I.glow(c, 'wall-window');
        assert.ok(pane.color === game('Glows').COOL && pane.a <= 0.5 && !pane.pulse, 'the windows are faint and still');
    });

    test('you walk in off the lane in Sendai on the day of the distillery, order at the counter, bump the still and every cask, and walk out again (#217)', () => {
        const { world, config } = helpers.worldWith(false);
        const casks = I.at(config.rooms[KEY], config, 'cask').length + 1;       // those on the floor, and the rack on the wall
        I.walkThrough(world, config, '2025-10-30', [...Array(casks).fill('casks'), 'pot-still', 'tasting'], /opens the TASTING BAR shop: |says: "/);
        // the counter is ordered at from the stools' row, between the stools
        const [barX, barY] = I.one(config.rooms[KEY], config, 'counter');
        world.enter(KEY, barX, barY + 2);
        const bump = world.step('n');
        assert.deepStrictEqual(plain([bump.moved, bump.interaction.kind, bump.interaction.group]), [false, 'tasting', 'shop']);
        assert.ok(/^opens the TASTING BAR shop: Highball ¥\d+$/.test(world.describe(bump.interaction)), world.describe(bump.interaction));
        // behind the still's neck you are walking, not bumping: the line comes from pushing into the pot
        const [stx, sty] = I.one(config.rooms[KEY], config, 'still');
        world.enter(KEY, stx - 1, sty + 1);
        const behind = world.step('e');
        assert.deepStrictEqual(plain([behind.moved, behind.interaction || null]), [true, null]);
        const pot = world.step('s');
        assert.deepStrictEqual(plain([pot.moved, pot.interaction.kind]), [false, 'pot-still']);
    });

    test('the counter is the tasting venue: a Highball and nothing else, nothing bought, no stamp; the still and the casks each say a line (#217)', () => {
        const Rules = game('Interactions');
        const bar = { interior: true, shopEnabled: false };
        const hit = (key) => plain(Rules.match(key, bar, game('Shop.VENUES')));
        assert.deepStrictEqual(hit('distillery-in-counter_0_0'), { kind: 'tasting', group: 'shop', footprint: true });
        const says = { still: 'pot-still', 'wall-casks': 'casks', cask: 'casks' };
        for (const [piece, kind] of Object.entries(says)) {
            const rule = hit(`distillery-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint && rule.say && rule.say.length <= 100, piece);
        }
        assert.ok(/twelve years/.test(hit('distillery-in-still_0_0').say) && /2037/.test(hit('distillery-in-cask_0_0').say));
        for (const piece of ['wall-shelf', 'wall-brick', 'wall-window', 'stool', 'lamp-hang', 'floor-a', 'doorlight']) {
            assert.strictEqual(hit(`distillery-in-${piece}_0_0`), null, piece);
        }
        for (const kind of ['tasting', 'pot-still', 'casks']) assert.strictEqual(Rules.RULES.filter((r) => r.kind === kind).length, 1, kind);
        const venue = game('Shop.VENUES').tasting, items = plain(game('Shop.DEFAULT_ITEMS'));
        assert.deepStrictEqual(items.filter((i) => venue.sells(i)).map((i) => i.name), ['Highball']);
        assert.ok(!venue.buys && !venue.grills);
        const c = cfg();
        assert.strictEqual(game('Shop.titleFor')('tasting', c.rooms[KEY]), 'TASTING BAR');
        assert.strictEqual(game('Stamps').placeFor('tasting', KEY, c.rooms[KEY]), null);
        assert.ok(!game('Stamps').stores(game('decodeConfig')(c)).some((s) => s.id === KEY), 'not a store on the stamp card');
        // nothing new is saved, pressed or loaded for it
        assert.ok(!/tasting|distillery-in-/.test(src('GameScene.js')), 'the scene knows nothing about it: one row in two tables');
    });

    test('the room is "Distillery" on the bar, short enough to count down on a phone, and the map says it is in Sendai (#217)', () => {
        I.named(cfg(), 'Distillery (in Sendai)');
    });

    test('the distillery generator and its art tool are checked, own the door through roomgen, and rebuild the same tasting bar from a sealed kiln (#217)', () => {
        I.plumbing({ generator: 'generate_distillery', art: 'generate_distillery_art', sprites: 17, after: 'pub-in-lamp-hang_0_0',
            owned: "DISTILLERY_PREFIX: ('distillery', DISTILLERY_DOORS)", table: "DISTILLERY_DOORS = {'sendai-kiln_0_0': [(2, 5)]}" });
        assert.ok(/rg\.DISTILLERY_DOORS/.test(I.tool('generate_distillery.py')), 'the generator has no door sprites of its own');
        // the frame is the pub's: the art tool draws none of its own
        assert.ok(/from generate_pub_art import/.test(I.tool('generate_distillery_art.py')) && !/def wall_side|def threshold/.test(I.tool('generate_distillery_art.py')));
        // the town's generator knows nothing of the door: roomgen keeps it through a rebuild
        assert.ok(!/Distillery|distillery-in/.test(I.tool('generate_sendai.py')));
    });
};
