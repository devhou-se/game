// Views (issue #242): the lift up Fukuoka Tower and the observation deck at the top of it
// (tools/generate_tower_deck.py, tools/generate_tower_deck_art.py, src/ViewRide.js, RoomManager.liftFor,
// the `daylight` room flag), and a turn on Osaka's ferris wheel (tools/generate_wheel_art.py, the gondola
// generate_osaka.py stands at its foot, the `ride` group). The checks the deck shares with the other
// owned-door interiors are tools/tests/interiors.js.
module.exports = (helpers) => {
    const { test, assert, fs, path, GV2, game, load } = helpers;
    for (const [name, file] of [['Interactions', 'utils/Interactions.js'], ['DayNight', 'DayNight.js'], ['ViewRide', 'ViewRide.js']]) {
        if (game(`typeof ${name}`) === 'undefined') load(file);
    }
    const HOST = 'Fukuoka', KEY = 'DeckFukuoka1', NAME = 'Tower Deck';
    // BEHIND: of the tower's twelve rows only the base, the last two, was ever solid from side to side
    const I = require('./interiors')(helpers, { HOST, KEY, NAME, MARK: 'deck', SPRITE: 'fukuoka-tower_0_0', DOORS: [[1, 11], [2, 11]], STAND: [0, 12], PREFIX: 'deck-in-', BEHIND: 10 });
    const { cfg, tiles, plain, src, K } = I;
    const V = game('ViewRide'), DN = game('DayNight'), RM = game('RoomManager');
    const KINDS = ['binoculars', 'binoculars', 'binoculars', 'compass', 'deck-window', 'deck-window', 'deck-window', 'deck-window', 'deck-window', 'deck-window', 'lift-sign', 'padlocks'];
    const PERIODS = ['dawn', 'day', 'dusk', 'night'];
    const png = require(path.join(GV2, 'tools', 'png'));
    const picture = (key) => png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
    const alpha = (im, x, y) => im.data[(y * im.width + x) * 4 + 3];

    test('Fukuoka Tower opens: the two leaves of the door in its foot lead up to the observation deck, and each cell of the lift\'s sill back down in front of its own leaf (#242)', () => {
        const c = cfg();
        const { doors, mats, ways } = I.doorsOpen(c);
        assert.strictEqual(doors.length, 2);
        assert.strictEqual(mats.length, 2, 'a cell of the sill for each leaf');
        // the doors are the middle two cells of the tower's last row
        const { sprite } = I.outside(c), [w, h] = I.size(c, 'fukuoka-tower_0_0');
        assert.deepStrictEqual(doors, [[sprite[0] + w / 2 - 1, sprite[1] + h - 1], [sprite[0] + w / 2, sprite[1] + h - 1]]);
        // the west leaf puts you on the west half of the lift, the east on the east: you do not swap sides
        assert.deepStrictEqual(ways.map((t) => [t.targetX, t.targetY]), mats.map((m) => [m.gridX, m.gridY - 1]));
        assert.ok(mats[0].gridX + 1 === mats[1].gridX && mats[0].gridY === mats[1].gridY);
        assert.deepStrictEqual(Object.keys(c.rooms).filter((k) => /^Deck/.test(k)), [KEY]);
        // all window: its light is the sky's, not a lantern's; nothing is sold; nobody lives there
        const room = c.rooms[KEY];
        assert.deepStrictEqual([room.interior, room.daylight, 'lanternLight' in room, room.shopEnabled, room.npcs], [true, true, false, false, []]);
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64], [NAME, 20, 15]);
    });

    test('nobody stands in Fukuoka Tower\'s doorway on any date: Damian, who wrote about the tower, is on the plaza beside the door (#242)', () => {
        const c = cfg();
        const { stand } = I.nobodyInTheWay(c);
        const damian = c.rooms[HOST].npcs.find((n) => n.name === 'Damian').states['2025-11-10'];
        assert.deepStrictEqual([damian.gridX, damian.gridY], stand);
    });

    test('the deck is a deck: six panes of glass from wall to wall, three binoculars and the padlocks along them, the brass map, two benches, the sign by the lift, lamps overhead (#242)', () => {
        const c = cfg(), room = c.rooms[KEY], solid = tiles(room, 'Colliders');
        // the back wall, five rows of glass, solid from end to end and inside the room's outline: a phone's
        // camera, which stops at the outline, shows all of the view
        assert.deepStrictEqual([1, 2, 3, 4, 5, 6].map((n) => I.size(c, `deck-in-window-${n}_0_0`)), [1, 2, 3, 4, 5, 6].map(() => [3, 5]));
        const panes = [1, 2, 3, 4, 5, 6].map((n) => I.one(room, c, `window-${n}`));
        assert.deepStrictEqual(panes, [1, 4, 7, 10, 13, 16].map((x) => [x, 1]), 'west to east, in order');
        for (let x = 1; x <= 18; x++) for (let y = 1; y <= 5; y++) assert.ok(K(x, y) in solid, `glass ${x},${y}`);
        const ys = room.boundary.map(([, y]) => y), xs = room.boundary.map(([x]) => x);
        assert.deepStrictEqual([Math.min(...xs), Math.min(...ys), Math.max(...xs)], [1, 1, 19], 'the outline takes in the wall of glass');
        // along the glass: the viewers (1x2) and the padlock fence (2x2), their feet on the floor's first row
        const floorY = 6;
        assert.deepStrictEqual([I.size(c, 'deck-in-binoculars_0_0'), I.size(c, 'deck-in-locks_0_0'), I.size(c, 'deck-in-lift-sign_0_0')], [[1, 2], [2, 2], [1, 2]]);
        const viewers = I.at(room, c, 'binoculars').sort((a, b) => a[0] - b[0]);
        assert.strictEqual(viewers.length, 3);
        for (const [x, y] of viewers) assert.ok(y + 1 === floorY && K(x, floorY) in solid, `binoculars ${x},${y}`);
        const [lx, ly] = I.one(room, c, 'locks');
        assert.ok(ly + 1 === floorY && K(lx, floorY) in solid && K(lx + 1, floorY) in solid && lx > viewers[2][0], 'the padlocks, at the east end');
        // on the floor: the brass map and two benches, each two cells wide and in the way
        assert.deepStrictEqual([I.size(c, 'deck-in-compass_0_0'), I.size(c, 'deck-in-bench_0_0')], [[2, 1], [2, 1]]);
        const [cx, cy] = I.one(room, c, 'compass'), benches = I.at(room, c, 'bench');
        assert.strictEqual(benches.length, 2);
        for (const [x, y] of benches.concat([[cx, cy]])) assert.ok(K(x, y) in solid && K(x + 1, y) in solid && y > floorY, `${x},${y}`);
        // the lift is the doorway, in the front wall; nothing stands in its two columns, and the sign is beside it
        const mats = room.transporters.map((t) => t.gridX).sort((a, b) => a - b), sill = room.transporters[0].gridY;
        assert.deepStrictEqual([I.one(room, c, 'lift-w'), I.one(room, c, 'lift-e')], [[mats[0], sill], [mats[1], sill]]);
        for (const x of mats) for (let y = floorY; y < sill; y++) assert.ok(!(K(x, y) in solid), `the way to the lift ${x},${y}`);
        const [sx, sy] = I.one(room, c, 'lift-sign');
        assert.ok(sx === mats[1] + 1 && sy + 2 === sill && K(sx, sy + 1) in solid);
        // the lamps hang over the floor, in nobody's way, lifted in front of what stands behind them
        const lamps = I.at(room, c, 'downlight');
        assert.ok(lamps.length >= 4 && lamps.every(([x, y]) => K(x, y) in tiles(room, 'Tops') && !(K(x, y + 1) in solid)));
        assert.ok(c.spriteMetadata['deck-in-downlight_0_0'].depthBias > 0);
        // its own carpet underfoot, and none of another interior's pieces; no bins
        const floor = tiles(room, 'Floor');
        for (const [x, y] of I.floor(room).filter(([, fy]) => fy >= floorY)) assert.ok(/^deck-in-floor-[ab]_/.test(c.tilePalette[floor[K(x, y)]]), `floor ${x},${y}`);
        const used = new Set(room.layers.flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]));
        assert.ok(![...used].some((k) => /^(shrine-in-|palace-in-|temple-in-|pub-in-|distillery-in-|mall-in-|office-(?!void)|konbini-)/.test(k)), 'none of another interior\'s pieces');
        assert.ok(![...used].some((k) => /bin(?!oculars)/.test(k)), 'no bins');
        // every cell of the floor that is not solid can be walked to from the lift
        const { seen, open } = I.reach(c);
        assert.deepStrictEqual([...open].filter((k) => !(k in solid) && !seen.has(k)), []);
        assert.ok(seen.size >= 80, `${seen.size} cells to walk on`);
        // at night the lamps are lit and the town below the glass: every pane has its lights
        I.glow(c, 'downlight');
        for (let n = 1; n <= 6; n++) I.glow(c, `window-${n}`).forEach((s) => assert.ok(s.x >= 0 && s.x <= 3 && s.y >= 1 && s.y <= 4.6, `pane ${n}: a light in the view, not on the sill`));
    });

    test('you walk in at the foot of Fukuoka Tower, ride up, bump every pane of the view and everything that stands on the deck, and ride down by the leaf you came in by (#242)', () => {
        const { world, config } = helpers.worldWith(false);
        I.walkThrough(world, config, '2025-11-10', KINDS, /says: "/);
        // a bench is somewhere to sit (Seats): in the way of everything but your own step onto it, where you
        // turn to the glass, and it says nothing
        const [bx, by] = I.at(config.rooms[KEY], config, 'bench')[0];
        world.enter(KEY, bx, by + 1);
        assert.strictEqual(world.canStep(bx, by + 1, bx, by), false);
        const bench = world.step('n');
        assert.deepStrictEqual(plain([bench.moved, bench.seat.kind, bench.seat.pose.face, !!bench.seat.pose.cover, bench.interaction || null]), [true, 'bench', 'up', true, null]);
        assert.deepStrictEqual([world.player.gridX, world.player.gridY], [bx, by]);
    });

    test('nothing is sold on the deck: the glass, the binoculars, the brass map, the padlocks and the sign each say a line, and nothing else of it says anything (#242)', () => {
        const Rules = game('Interactions');
        const deck = { interior: true, daylight: true, shopEnabled: false };
        const hit = (key) => plain(Rules.match(key, deck, game('Shop.VENUES')));
        const says = { 'window-1': 'deck-window', 'window-6': 'deck-window', binoculars: 'binoculars', compass: 'compass', locks: 'padlocks', 'lift-sign': 'lift-sign' };
        for (const [piece, kind] of Object.entries(says)) {
            const rule = hit(`deck-in-${piece}_0_0`);
            assert.ok(rule && rule.kind === kind && rule.group === 'flavour' && rule.footprint && rule.say && rule.say.length <= 100, piece);
            assert.strictEqual(rule.say, rule.say.toLowerCase(), 'the table\'s voice');
        }
        for (const kind of new Set(KINDS)) assert.strictEqual(Rules.RULES.filter((r) => r.kind === kind).length, 1, kind);
        // the two facts: the deck is 123 m up a tower of 234
        assert.ok(/123 metres/.test(hit('deck-in-window-3_0_0').say) && /123 metres up a tower of 234/.test(hit('deck-in-lift-sign_0_0').say));
        assert.strictEqual(V.RIDES.lift.top, 123);
        // every sprite the room is made of: those say a line, the rest nothing at all
        const c = cfg(), room = c.rooms[KEY];
        const used = [...new Set(room.layers.filter((l) => l.name !== 'Colliders').flatMap((l) => Object.values(l.tiles)).map((id) => c.tilePalette[id]))];
        const speaking = used.filter((key) => hit(key));
        assert.deepStrictEqual(speaking.sort(), ['binoculars', 'compass', 'lift-sign', 'locks', 'window-1', 'window-2', 'window-3', 'window-4', 'window-5', 'window-6'].map((p) => `deck-in-${p}_0_0`));
        for (const piece of ['bench', 'downlight', 'floor-a', 'lift-w', 'lift-e', 'doorlight', 'wall-front', 'side-w']) assert.strictEqual(hit(`deck-in-${piece}_0_0`), null, piece);
        // the lift is not a thing you bump (the sill says nothing, above): it is the door, and the ride is
        // the room pair's (RoomManager.liftFor). The job's lift in a tower lobby is another table row
        assert.deepStrictEqual(plain(Rules.RULES.filter((r) => r.kind === 'lift').map((r) => r.group)), ['career']);
        assert.ok(!game('Stamps').stores(game('decodeConfig')(c)).some((s) => s.id === KEY), 'not a store on the stamp card');
        assert.ok(!/deck-in-|DeckFukuoka/.test(src('GameScene.js')) && !/deck-in-|DeckFukuoka/.test(src('ViewRide.js')), 'the rows are in one table, the room is data');
    });

    test('the room is "Tower Deck" on the bar, short enough to count down on a phone, and the map says it is in Fukuoka (#242)', () => {
        I.named(cfg(), 'Tower Deck (in Fukuoka)');
    });

    test('the deck generator and its art tool are checked, own the doors through roomgen, and rebuild the same deck from a sealed tower (#242)', () => {
        I.plumbing({ generator: 'generate_tower_deck', art: 'generate_tower_deck_art', sprites: 20, after: 'mall-in-palm_0_0',
            owned: "DECK_PREFIX: ('deck', DECK_DOORS)", table: "DECK_DOORS = {'fukuoka-tower_0_0': [(1, 11), (2, 11)]}" });
        assert.ok(/rg\.DECK_DOORS/.test(I.tool('generate_tower_deck.py')), 'the generator has no door sprites of its own');
        // the walls are the pub's frame; the lamps are lifted by the art tool
        const art = I.tool('generate_tower_deck_art.py');
        assert.ok(/from generate_pub_art import/.test(art) && !/def wall_side|def wall_front/.test(art));
        assert.ok(/DEPTH_BIAS = \{'deck-in-downlight': 10/.test(art));
        // the town's generator knows nothing of the room: roomgen keeps the doors through a rebuild
        assert.ok(!/Deck|deck-in/.test(I.tool('generate_fukuoka.py')) && !/Deck|deck-in/.test(I.tool('generate_fukuoka_town_art.py')));
    });

    test('a key held through the lift does not ride it again: north of where you step out on the deck is floor, south of where you step out on the plaza is plaza (#242)', () => {
        const c = cfg(), host = c.rooms[HOST], room = c.rooms[KEY];
        const is = (r, x, y) => r.transporters.some((t) => t.gridX === x && t.gridY === y);
        for (const t of host.transporters.filter((x) => x.targetRoom === KEY)) {
            // up: the key held is north. The cell north of the arrival cell is open floor, not a way anywhere
            assert.ok(!is(room, t.targetX, t.targetY - 1) && !(K(t.targetX, t.targetY - 1) in tiles(room, 'Colliders')), `north of ${t.targetX},${t.targetY}`);
        }
        for (const t of room.transporters) {
            // down: the key held is south. The cell south of the plaza cell is not a door
            assert.ok(!is(host, t.targetX, t.targetY + 1), `south of ${t.targetX},${t.targetY}`);
        }
    });

    test('a door into a room that is a deck is a lift going up, a door out of one a lift going down, and no other door in the world is a lift (#242)', () => {
        const config = helpers.realConfig(), rooms = config.rooms;
        const lifts = [];
        for (const [key, room] of Object.entries(rooms)) {
            for (const t of room.transporters || []) {
                const dir = RM.liftFor(rooms, key, t.targetRoom);
                if (dir) lifts.push([key, t.targetRoom, dir]);
            }
        }
        assert.deepStrictEqual(lifts.sort((a, b) => a[2].localeCompare(b[2])).reverse(), [[HOST, KEY, 'up'], [HOST, KEY, 'up'], [KEY, HOST, 'down'], [KEY, HOST, 'down']]);
        // rooms that are not there, and no rooms at all
        assert.deepStrictEqual([RM.liftFor(rooms, HOST, 'Nowhere'), RM.liftFor(rooms, 'Nowhere', HOST), RM.liftFor(rooms, 'Nowhere', KEY), RM.liftFor(null, HOST, KEY), RM.liftFor({}, HOST, KEY)],
            [null, null, 'up', null, null]);
        // the marker is all it reads: any room that carries `deck` is the top of a lift
        assert.deepStrictEqual([RM.liftFor({ A: {}, B: { deck: { host: 'A' } } }, 'A', 'B'), RM.liftFor({ A: {}, B: { deck: { host: 'A' } } }, 'B', 'A'), RM.liftFor({ A: {}, B: {} }, 'A', 'B')], ['up', 'down', null]);
        // the game asks with the config's rooms (the runtime rooms carry no `deck`: the ride would silently never play),
        // before the ordinary room switch, and hands the door to the ride
        const rm = src('systems/RoomManager.js');
        assert.ok(rm.includes('RoomManager.liftFor(this.scene.config.rooms, this.currentRoom, trans.targetRoom)'));
        assert.ok(rm.indexOf('this.scene.viewRide.lift(dir, trans)') > 0 && rm.indexOf('this.scene.viewRide.lift(dir, trans)') < rm.indexOf('this.switchRoom(trans.targetRoom'));
        // ...and while it plays, the ride owns the keys, as a flight does
        const input = src('systems/InputHandler.js');
        assert.ok(/if \(this\.scene\.viewRide && this\.scene\.viewRide\.riding\) \{\s+this\.scene\.viewRide\.handleInput\(\);/.test(input));
        assert.ok(src('GameScene.js').includes('this.viewRide = new ViewRide(this);'));
        assert.ok(fs.readFileSync(path.join(GV2, 'index.html'), 'utf8').includes("'src/ViewRide.js',"));
    });

    test('the terminal game says which way the lift goes: a step onto a leaf of the tower\'s door is transported up, a step onto the sill down, any other door neither (#242)', () => {
        const { world, config } = helpers.worldWith(false);
        const ways = config.rooms[HOST].transporters.filter((t) => t.targetRoom === KEY);
        world.date = '2025-11-10';
        world.enter(HOST, ways[0].gridX, ways[0].gridY + 1);
        const up = world.step('n');
        assert.deepStrictEqual(plain(up.transported), { from: HOST, to: KEY, lift: 'up' });
        const down = world.step('s');
        assert.deepStrictEqual(plain(down.transported), { from: KEY, to: HOST, lift: 'down' });
        // an ordinary door: no `lift` key at all, so what read `transported` before reads the same
        const other = config.rooms[HOST].transporters.find((t) => t.targetRoom !== KEY && !t.hidden) || config.rooms[HOST].transporters.find((t) => t.targetRoom !== KEY);
        world.enter(HOST, other.gridX, other.gridY + 1);
        const step = world.step('n');
        if (step.transported) assert.deepStrictEqual(Object.keys(plain(step.transported)).sort(), ['from', 'to']);
        assert.ok(/the lift goes \$\{r\.transported\.lift\}/.test(fs.readFileSync(path.join(GV2, 'tools', 'play.js'), 'utf8')));
    });

    test('a daylight interior is graded by the hour as the street is: the deck goes dark at night with its lights on, and a plain interior or a lantern-lit one is graded as before (#242)', () => {
        for (const p of PERIODS) {
            assert.deepStrictEqual(plain(DN.gradeFor({ interior: true, daylight: true }, p)), plain(DN.GRADES[p] || null), p);
            assert.deepStrictEqual(plain(DN.gradeFor({}, p)), plain(DN.GRADES[p] || null), `the street at ${p}`);
            assert.strictEqual(DN.gradeFor({ interior: true }, p), null, `a lit interior at ${p}`);
            assert.deepStrictEqual(plain(DN.gradeFor({ interior: true, lanternLight: true }, p)), p === 'night' ? plain(DN.LANTERN_NIGHT) : null, `a lantern-lit interior at ${p}`);
        }
        // daylight wins over lanternLight, and means nothing on a room that is not an interior
        assert.deepStrictEqual(plain(DN.gradeFor({ interior: true, daylight: true, lanternLight: true }, 'night')), plain(DN.GRADES.night));
        assert.deepStrictEqual(plain(DN.gradeFor({ daylight: true }, 'dusk')), plain(DN.GRADES.dusk));
        // the deck's own room
        const deck = cfg().rooms[KEY];
        assert.deepStrictEqual(plain([DN.gradeFor(deck, 'night'), DN.gradeFor(deck, 'day')]), plain([DN.GRADES.night, null]));
        assert.ok(DN.GRADES.night.lights && !DN.GRADES.day);
        // the mall next door, lit: never graded
        assert.strictEqual(DN.gradeFor(cfg().rooms.MallFukuoka1, 'night'), null);
    });

    test('the view from the lift is the hour\'s: white by day, the street\'s night colour with the town\'s lights on at night, its dawn and dusk between - what the deck is graded by (#242)', () => {
        assert.deepStrictEqual(plain(V.tint('day')), { tint: 0xffffff, lights: false });
        assert.deepStrictEqual(plain(V.tint('nonsense')), { tint: 0xffffff, lights: false });
        // night: the grade is opaque, so the tint is its colour
        assert.deepStrictEqual(plain(V.tint('night')), { tint: DN.GRADES.night.color, lights: true });
        // dawn and dusk: the grade's colour at its alpha over white - lighter than the colour, not white
        for (const p of ['dawn', 'dusk']) {
            const g = DN.GRADES[p], t = V.tint(p);
            assert.strictEqual(t.lights, false);
            for (const shift of [16, 8, 0]) {
                const ch = (t.tint >> shift) & 255, of = (g.color >> shift) & 255;
                assert.strictEqual(ch, Math.round(255 - (255 - of) * g.alpha), `${p} ${shift}`);
                assert.ok(ch >= of && ch <= 255);
            }
            assert.ok(t.tint !== 0xffffff && t.tint !== g.color);
        }
        // period by period it is the deck's grade: lights when the deck's are lit, a tint when the deck has one
        const deck = cfg().rooms[KEY];
        for (const p of PERIODS) {
            const g = DN.gradeFor(deck, p), t = V.tint(p);
            assert.deepStrictEqual([t.lights, t.tint === 0xffffff], [!!(g && g.lights), !g], p);
        }
    });

    test('the lift eases from the ground to 123 m and back: height, the counter, the skip rule (#242)', () => {
        const lift = V.RIDES.lift;
        assert.deepStrictEqual([lift.ms, lift.top], [4500, 123]);
        // up: 0 -> 1, never back; slow at both ends; down is the same ride backwards
        let last = -1;
        for (let ms = 0; ms <= lift.ms; ms += 50) {
            const h = V.height(lift, 'up', ms);
            assert.ok(h >= last && h >= 0 && h <= 1, `${ms} ms: ${h}`);
            assert.ok(Math.abs(V.height(lift, 'down', ms) - (1 - h)) < 1e-9);
            assert.ok(Math.abs(V.height(lift, 'down', ms) - V.height(lift, 'up', lift.ms - ms)) < 1e-9, 'the way down is the way up run backwards');
            last = h;
        }
        assert.deepStrictEqual([V.height(lift, 'up', 0), V.height(lift, 'up', lift.ms), V.height(lift, 'down', 0), V.height(lift, 'down', lift.ms)], [0, 1, 1, 0]);
        assert.ok(Math.abs(V.height(lift, 'up', lift.ms / 2) - 0.5) < 1e-9);
        assert.ok(V.height(lift, 'up', 450) < 0.05 && V.height(lift, 'up', lift.ms - 450) > 0.95, 'eased in and out');
        // clamped: before it starts, after it ends
        assert.deepStrictEqual([V.height(lift, 'up', -100), V.height(lift, 'up', 99999), V.height(lift, 'down', 99999)], [0, 1, 0]);
        assert.deepStrictEqual([V.progress(lift, -5), V.progress(lift, 2250), V.progress(lift, 1e6)], [0, 0.5, 1]);
        // the counter: whole metres, 0 on the ground, 123 at the top
        assert.deepStrictEqual([V.metres(lift, 0), V.metres(lift, 1), V.metres(lift, 0.5), V.metres(lift, V.height(lift, 'down', 0))], [0, 123, 62, 123]);
        // skipped by a press, but not by the step that boarded and not once it is ending
        assert.ok(V.SKIP_AFTER >= 500 && V.SKIP_AFTER < lift.ms / 2);
        assert.deepStrictEqual([0, V.SKIP_AFTER - 1, V.SKIP_AFTER, lift.ms - 1, lift.ms, lift.ms + 500].map((ms) => V.canSkip(lift, ms)), [false, false, true, true, false, false]);
        // the skip is the flight's: the same keys, and a tap
        const ride = src('ViewRide.js');
        assert.ok(/JD\(k\.space\) \|\| JD\(k\.enter\) \|\| JD\(k\.esc\)/.test(ride) && /tap\.on\('pointerdown', \(\) => this\.skip\(\)\)/.test(ride));
        assert.ok(/Hints\.text\(scene, 'SPACE: skip the ride', \{ tap: true \}\)/.test(ride), 'the hint is worded by Hints');
        assert.ok(!/addKey\(|KeyCodes\.(?!ENTER|SPACE|ESC)/.test(ride.replace(/const K = Phaser\.Input\.Keyboard\.KeyCodes;/, '')) && !/K\.(?!ENTER|SPACE|ESC)[A-Z]/.test(ride), 'no new bindings');
    });

    test('the view pans with the height and never runs out: each picture is bottom-aligned on the ground, top-aligned at the top, and the far one is whole and moves less (#242)', () => {
        const c = cfg();
        for (const [name, ride] of Object.entries(V.RIDES)) {
            const win = ride.window;
            const layers = ['far', 'near', 'lights'].map((n) => [n, picture(`${ride.view}-${n}`)]);
            for (const [n, im] of layers) {
                assert.ok(im.width >= win.w && im.height >= win.h, `${name} ${n}: ${im.width}x${im.height} behind a ${win.w}x${win.h} window`);
                // the rows of the picture the window shows at every height: all of them rows the picture has
                // ...and the columns, where the view slides sideways as well (the wheel): the far picture by a third
                for (let ms = 0; ms <= ride.ms; ms += 25) {
                    for (const dir of ['up', 'down']) {
                        const top = im.height - win.h - V.pan(V.height(ride, dir, ms), im.height, win.h);
                        assert.ok(top >= 0 && top + win.h <= im.height, `${name} ${n} at ${ms} ms: rows ${top}..${top + win.h}`);
                    }
                    const left = Math.round((im.width - win.w) / 2) + V.drift(ride, ms, n === 'far' ? V.FAR_DRIFT : 1);
                    assert.ok(left >= 0 && left + win.w <= im.width, `${name} ${n} at ${ms} ms: columns ${left}..${left + win.w}`);
                }
                assert.ok(im.width - win.w >= 2 * (ride.drift || 0), `${name} ${n}: ${im.width} px wide for a drift of ${ride.drift || 0} either way`);
                assert.deepStrictEqual([V.pan(0, im.height, win.h), V.pan(1, im.height, win.h)], [0, im.height - win.h]);
            }
            const [far, near, lights] = layers.map(([, im]) => im);
            assert.ok(far.height < near.height, 'the far picture has less to pan through: it moves less');
            assert.deepStrictEqual([lights.width, lights.height], [near.width, near.height], 'the lights lie over the near picture');
            // far is the sky and the horizon: opaque. near is cut out against it; the lights are mostly nothing
            let holes = 0, clear = 0, lit = 0;
            for (let i = 3; i < far.data.length; i += 4) if (far.data[i] !== 255) holes++;
            for (let i = 3; i < near.data.length; i += 4) { if (near.data[i] === 0) clear++; if (lights.data[i] > 0) lit++; }
            assert.strictEqual(holes, 0, `${name}: the far picture is opaque`);
            assert.ok(clear > near.width * 64, `${name}: the near picture lets the far one show`);
            assert.ok(lit > 200 && lit < near.data.length / 4 / 5, `${name}: ${lit} lit pixels`);
            for (const [n] of layers) assert.ok(c.spriteMetadata[`${ride.view}-${n}`], `${ride.view}-${n} is loaded`);
            assert.ok(c.spriteMetadata[ride.frame], `${ride.frame} is loaded`);
        }
        // pictures are not tiles: no palette slot, no name in the editor
        for (const key of Object.keys(c.spriteMetadata).filter((k) => /^view-/.test(k))) {
            assert.ok(!c.tilePalette.includes(key) && !(key in (c.tileNames || {})), key);
            assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), key);
        }
        // the tower's beams pass the window on the way, and none is across it on the ground or at the top
        const win = V.RIDES.lift.window;
        assert.deepStrictEqual(plain([V.beams(0, win.h), V.beams(1, win.h)]), [[], []]);
        const mid = plain(V.beams(0.5, win.h));
        assert.ok(mid.length >= 1 && mid.every((b) => b.y0 >= 0 && b.y1 <= win.h && b.y1 > b.y0 && b.y1 - b.y0 <= V.BEAM_H));
        let seen = 0;
        for (let h = 0; h <= 1; h += 0.01) {
            const bs = plain(V.beams(h, win.h));
            assert.ok(bs.every((b) => b.y0 >= 0 && b.y1 <= win.h && b.y1 > b.y0), `beams at ${h}`);
            seen += bs.length ? 1 : 0;
        }
        assert.ok(seen > 50, 'beams go by for most of the ride');
        // going up, a beam moves down the window (you pass it)
        const a = plain(V.beams(0.48, win.h)).map((b) => b.y0), b = plain(V.beams(0.5, win.h)).map((x) => x.y0);
        assert.ok(Math.min(...b) > Math.min(...a) || b.length !== a.length);
    });

    test('the picture is as big as the world is drawn and never bigger than the view: 1 on a desktop, the phone\'s zoom until it would not fit, 1 on a portrait phone (#242)', () => {
        assert.strictEqual(V.scale(1, 1280, 960, 640, 640), 1, 'a desktop');
        assert.strictEqual(V.scale(undefined, 1280, 960, 640, 640), 1, 'no zoom known');
        assert.strictEqual(V.scale(1.25, 1280, 960, 640, 640), 1.25, 'a tablet: the world\'s zoom');
        assert.strictEqual(V.scale(2, 1280, 960, 640, 640), 1.5, 'a landscape phone: held down by the height');
        assert.strictEqual(V.scale(2, 1280, 960 - V.HINT_ROOM, 640, 640), (960 - V.HINT_ROOM) / 640, '...and by the room the hint needs under it');
        assert.strictEqual(V.scale(2, 1280, 1280, 640, 640), 2, 'never more than the world');
        assert.strictEqual(V.scale(1, 612, 960, 640, 640), 1, 'a portrait phone: never under 1, though the view is narrower than the frame');
        assert.strictEqual(V.scale(2, 612, 960, 640, 640), 1);
        assert.strictEqual(V.scale(0.5, 1280, 960, 640, 640), 1);
        // so on a portrait phone the frame overhangs the view: what matters is in its middle, the columns the
        // narrowest phone still shows (Viewport.MIN_VISIBLE)
        assert.strictEqual(V.SAFE_W, game('Viewport.MIN_VISIBLE'));
        for (const [name, ride] of Object.entries(V.RIDES)) {
            const frame = picture(ride.frame), edge = (frame.width - V.SAFE_W) / 2;
            assert.deepStrictEqual([frame.width, frame.height], [640, 640], name);
            // (a ride with a counter has a `panel` for it: the lift. A gondola has none)
            for (const box of [ride.window, ride.panel].filter(Boolean)) {
                assert.ok(box.x >= edge && box.x + box.w <= frame.width - edge && box.y >= 0 && box.y + box.h <= frame.height, `${name}: ${JSON.stringify(box)}`);
            }
            assert.strictEqual(!!ride.panel, !!ride.top, `${name}: a counter has a plate to be drawn on, and a plate a counter`);
            if (ride.panel) assert.ok(ride.panel.y + ride.panel.h <= ride.window.y || ride.panel.y >= ride.window.y + ride.window.h, `${name}: the counter is not on the glass`);
            // the picture, the hint under it and the counter are sized from the same numbers
            assert.ok(V.HINT_ROOM >= 48 && frame.height + V.HINT_ROOM <= 960);
        }
        // where it goes: in the middle of a desktop's view; on a landscape phone against the top, the hint's room
        // under it; on a portrait phone at 1, overhanging the sides evenly
        assert.deepStrictEqual({ ...V.layout(1, 1280, 960, 640, 640, V.HINT_ROOM) }, { k: 1, left: 320, top: 160, bottom: 800, hintY: 800 + V.HINT_ROOM / 2 });
        const phone = V.layout(2, 1280, 960, 640, 640, V.HINT_ROOM);
        assert.deepStrictEqual([phone.k, phone.top, phone.bottom, phone.hintY], [(960 - V.HINT_ROOM) / 640, 0, 960 - V.HINT_ROOM, 960 - V.HINT_ROOM / 2]);
        assert.ok(phone.left >= 0 && phone.left + 640 * phone.k <= 1280);
        for (const W of [game('Viewport.MIN_VISIBLE'), 612]) {
            const tall = V.layout(1, W, 960, 640, 640, V.hintRoom(27, 1.57));
            assert.deepStrictEqual([tall.k, tall.left, tall.top], [1, Math.round(W / 2 - 320), 160]);
            for (const [name, ride] of Object.entries(V.RIDES)) {
                for (const box of [ride.window, ride.panel].filter(Boolean)) assert.ok(tall.left + box.x >= 0 && tall.left + box.x + box.w <= W, `${name} at ${W}: ${JSON.stringify(box)}`);
            }
        }
        // the hint's room: 64 px on a desktop; on a phone the hint is magnified with the overlays, so the room is
        // what the line takes at that zoom with UIScale's margin on both sides - and the picture gives it up
        assert.strictEqual(V.HINT_MARGIN, game('UIScale.MARGIN'));
        assert.strictEqual(V.hintRoom(27, 1), V.HINT_ROOM);
        assert.strictEqual(V.hintRoom(27, undefined), V.HINT_ROOM);
        assert.strictEqual(V.hintRoom(27, 2.5), Math.ceil(27 * 2.5) + 24);
        assert.strictEqual(V.hintRoom(27, 3), 105);
        const small = V.layout(2, 1280, 960, 640, 640, V.hintRoom(27, 3));
        assert.deepStrictEqual([small.k, small.top, small.bottom, small.hintY], [(960 - 105) / 640, 0, 855, 855 + 52.5]);
        const ride = src('ViewRide.js');
        assert.ok(ride.includes('ViewRide.hintRoom(hint.height, scene.uiScale ? scene.uiScale.wanted() : 1)'));
        assert.ok(ride.includes('ViewRide.layout(scene.uiScale && scene.uiScale.worldZoom, W, H, frame.width, frame.height, room)'));
        // to UIScale the picture is a cover, drawn 1:1 (the plane's cabin's rule)
        assert.ok(ride.includes('c.getBounds = (out) => (out || new Phaser.Geom.Rectangle()).setTo(0, 0, W, H);'));
    });

    test('the lift is drawn round the window the game cuts the view to: glass where ViewRide says the window is, cabin all round it, a plain plate where the counter goes (#242)', () => {
        const lift = V.RIDES.lift, frame = picture(lift.frame), win = lift.window, panel = lift.panel;
        // just inside each corner of the window: clear or glazed, never opaque cabin... the middle of it is clear
        assert.strictEqual(alpha(frame, win.x + win.w / 2 - 40, win.y + win.h / 2 - 60), 0, 'the middle of the glass is clear');
        let clear = 0;
        for (let y = win.y; y < win.y + win.h; y++) for (let x = win.x; x < win.x + win.w; x++) if (alpha(frame, x, y) === 0) clear++;
        assert.ok(clear > win.w * win.h * 0.8, `${clear} of ${win.w * win.h} window pixels are clear`);
        // just outside it, on every side, and everywhere else: opaque. Nothing of the view can show round the frame
        let leaks = 0;
        for (let y = 0; y < frame.height; y++) {
            for (let x = 0; x < frame.width; x++) {
                const inside = x >= win.x && x < win.x + win.w && y >= win.y && y < win.y + win.h;
                if (!inside && alpha(frame, x, y) !== 255) {
                    // the frame's own rounded corners, at the edge of the picture, show the black behind: not the view
                    const corner = (x < 16 || x >= frame.width - 16) && (y < 16 || y >= frame.height - 16);
                    if (!corner) leaks++;
                }
            }
        }
        assert.strictEqual(leaks, 0, 'the cabin is opaque round the window');
        for (const [x, y] of [[win.x - 2, win.y + 40], [win.x + win.w + 1, win.y + 40], [win.x + 40, win.y - 2], [win.x + 40, win.y + win.h + 1]]) {
            assert.strictEqual(alpha(frame, x, y), 255, `${x},${y}`);
        }
        // the plate: one flat dark colour under the counter, so the digits read
        const at = (x, y) => Array.from(frame.data.subarray((y * frame.width + x) * 4, (y * frame.width + x) * 4 + 4));
        const plate = at(panel.x + panel.w / 2, panel.y + panel.h / 2);
        assert.ok(plate[3] === 255 && plate[0] + plate[1] + plate[2] < 120, `the plate is dark: ${plate}`);
        for (let y = panel.y + 12; y < panel.y + panel.h - 12; y += 4) for (let x = panel.x + 12; x < panel.x + panel.w - 12; x += 4) assert.deepStrictEqual(at(x, y), plate, `plate ${x},${y}`);
        // the art tool and the game agree by these numbers, drawn at half size and doubled
        const art = I.tool('generate_tower_deck_art.py');
        assert.ok(art.includes(`LIFT_WIN = (${win.x / 2}, ${win.y / 2}, ${win.w / 2}, ${win.h / 2})`) && art.includes(`LIFT_PANEL = (${panel.x / 2}, ${panel.y / 2}, ${panel.w / 2}, ${panel.h / 2})`));
        // the lift's view is the middle of the deck's: what you rode up through is what the panes show
        const near = picture('view-fukuoka-near');
        assert.strictEqual(near.width, win.w);
        assert.ok(/LIFT_X = \(PAN_W - LIFT_WIN\[2\]\) \/\/ 2|LIFT_X = 192/.test(art));
    });

    // ---------------------------------------------------------------- the wheel
    const TOWN = 'Osaka', WHEEL = 'dotonbori-wheel_0_0', GONDOLA = 'wheel-boarding_0_0';
    /** Where the wheel and the gondola you board stand in Osaka, and the cells the gondola is bumped from. */
    const wheelAt = (c) => {
        const room = c.rooms[TOWN], wheels = I.placed(room, c, WHEEL), gondolas = I.placed(room, c, GONDOLA);
        assert.deepStrictEqual([wheels.length, gondolas.length], [1, 1]);
        const [gx, gy] = gondolas[0], cells = [[gx, gy], [gx + 1, gy], [gx, gy + 1], [gx + 1, gy + 1]];
        const own = new Set(cells.map(([x, y]) => K(x, y))), sides = [];
        for (const [x, y] of cells) for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) if (!own.has(K(nx, ny))) sides.push([nx, ny, x, y]);
        return { wheel: wheels[0], gondola: gondolas[0], cells, sides };
    };

    test('a gondola waits at the foot of Osaka\'s wheel: two cells square under the three that hang on its west side, outside the legs, and the way under the wheel is as open as it was (#242)', () => {
        const c = cfg(), room = c.rooms[TOWN], { wheel, gondola, cells } = wheelAt(c);
        assert.deepStrictEqual(I.size(c, GONDOLA), [2, 2]);
        assert.deepStrictEqual(I.size(c, WHEEL), [12, 12]);
        // west edge of the wheel, on its last two rows: the legs are columns 2..3 and 8..9 of it (#241)
        assert.deepStrictEqual(gondola, [wheel[0], wheel[1] + 10]);
        const solid = tiles(room, 'Colliders');
        for (const [x, y] of cells) assert.ok(K(x, y) in solid, `the gondola's cell ${x},${y} is solid`);
        // between the legs nothing is solid, and the walk under the wheel from the row above its feet to the row below is open
        for (let x = wheel[0] + 4; x < wheel[0] + 8; x++) for (let y = wheel[1] + 9; y <= wheel[1] + 12; y++) assert.ok(!(K(x, y) in solid), `${x},${y} under the wheel`);
        // the generator places it from the wheel, so it moves with it
        const gen = I.tool('generate_osaka.py');
        assert.ok(/BOARDING = \(WHEEL\[0\], WHEEL\[1\] \+ 10\)/.test(gen) && gen.includes("b.prop('wheel-boarding_0_0', *BOARDING, 2, 2)"));
        // its art is cut from the wheel's own sprite by a tool the generator check runs; pictures are that tool's too
        assert.ok(/ART_TOOLS \+= \['generate_wheel_art'\]/.test(I.tool('check_generators.py')));
        const art = I.tool('generate_wheel_art.py');
        assert.ok(art.includes("WHEEL = 'assets/sprites/dotonbori-wheel_0_0.png'"));
        // (interiors.js reads every other generator for the deck's names: this one has none of them)
        assert.ok(!art.includes('DeckFukuoka') && !art.includes("'deck-in-"));
    });

    test('bumping the gondola is a ride on the wheel: its four cells answer the ride and nothing else of the wheel does, and the terminal game says what it is (#242)', () => {
        const { world, config } = helpers.worldWith(false);
        const { wheel, cells, sides } = wheelAt(config);
        world.unpeopled = true;
        world.enter(TOWN, sides[0][0], sides[0][1]);
        const rides = world.interactions().filter((i) => i.group === 'ride');
        assert.deepStrictEqual(plain(rides.map((i) => [i.kind, i.x, i.y, i.w, i.h])), [['wheel', cells[0][0], cells[0][1], 2, 2]]);
        for (const [x, y] of cells) {
            const hit = world.interactionAt(x, y);
            assert.deepStrictEqual(plain([hit.kind, hit.group]), ['wheel', 'ride'], `${x},${y}`);
            assert.strictEqual(world.describe(hit), 'rides the wheel: one turn, the view over Dotonbori, and back on this cell');
        }
        // the wheel itself - its legs, its ring, the air between them - is not something to ride: only the gondola is
        for (let y = wheel[1]; y < wheel[1] + 12; y++) {
            for (let x = wheel[0]; x < wheel[0] + 12; x++) {
                if (cells.some(([cx, cy]) => cx === x && cy === y)) continue;
                const hit = world.interactionAt(x, y);
                assert.ok(!hit || hit.group !== 'ride', `${x},${y} of the wheel answers a ride`);
            }
        }
        // a step into it from every side it can be reached from is a bump that answers the ride, and you have not moved
        let bumped = 0;
        for (const [fx, fy, tx, ty] of sides) {
            world.enter(TOWN, fx, fy);
            if (world.blocked.has(K(fx, fy))) continue;                 // the wheel's leg is on its east side
            const dir = tx > fx ? 'e' : tx < fx ? 'w' : ty > fy ? 's' : 'n';
            const step = world.step(dir);
            assert.deepStrictEqual(plain([step.moved, step.bumped, step.interaction.kind]), [false, [tx, ty], 'wheel'], `from ${fx},${fy}`);
            assert.deepStrictEqual([world.player.gridX, world.player.gridY], [fx, fy]);
            bumped++;
        }
        assert.ok(bumped >= 4, `${bumped} cells to board from`);
        // the rule is one row of the bump table, on the gondola and not on the wheel
        const rules = plain(game('Interactions.RULES').filter((r) => r.group === 'ride').map((r) => [r.kind, r.footprint]));
        assert.deepStrictEqual(rules, [['wheel', true]]);
        assert.deepStrictEqual(plain([game('Interactions').match(GONDOLA, {}).kind, game('Interactions').match(WHEEL, {})]), ['wheel', null]);
    });

    test('the gondola can be boarded on every date: on each day surveyed a cell it is bumped from is free and can be walked to, and you can still walk under the wheel (#242)', () => {
        const { world, config } = helpers.worldWith(false);
        const { wheel, sides } = wheelAt(config);
        // somewhere the game puts you in Osaka: where a door from another room lets you out
        const way = Object.values(config.rooms).flatMap((r) => r.transporters || []).find((t) => t.targetRoom === TOWN);
        assert.ok(way, 'a way into Osaka');
        const under = K(wheel[0] + 6, wheel[1] + 10);                  // Osaka (39,17): between the legs
        const dates = game('WorldModel.surveyDates')(config);
        assert.ok(dates.length > 20);
        for (const date of dates) {
            world.date = date;
            world.enter(TOWN, way.targetX, way.targetY);
            const reach = world.reachable();
            const free = sides.filter(([x, y]) => reach.has(K(x, y)));
            assert.ok(free.length >= 1, `${date}: nowhere to board the wheel from`);
            assert.ok(reach.has(under), `${date}: no way under the wheel`);
        }
    });

    test('one turn of the wheel: up to the top half-way through and down again, slow at both, the view sliding out and back - and it has no counter and passes no beams (#242)', () => {
        const wheel = V.RIDES.wheel;
        assert.deepStrictEqual(plain(wheel), { frame: 'view-gondola', view: 'view-dotonbori', ms: 14000, turn: true, drift: 32, window: { x: 64, y: 224, w: 512, h: 320 } });
        // 0, 1, 0: on the ground, at the top, on the ground; the same going up as coming down; either way it is asked for
        assert.deepStrictEqual([0, wheel.ms / 2, wheel.ms].map((ms) => V.height(wheel, 'up', ms)), [0, 1, 0]);
        let last = -1;
        for (let ms = 0; ms <= wheel.ms / 2; ms += 50) {
            const h = V.height(wheel, 'up', ms);
            assert.ok(h >= last && h >= 0 && h <= 1, `${ms} ms: ${h}`);
            assert.ok(Math.abs(h - V.height(wheel, 'up', wheel.ms - ms)) < 1e-9, `${ms} ms: the way down is the way up`);
            assert.strictEqual(V.height(wheel, 'down', ms), h);
            last = h;
        }
        assert.ok(Math.abs(V.height(wheel, 'up', wheel.ms / 4) - 0.5) < 1e-9);
        assert.ok(V.height(wheel, 'up', 700) < 0.05 && V.height(wheel, 'up', wheel.ms / 2 - 700) > 0.95, 'slow off the ground and over the top');
        assert.deepStrictEqual([V.height(wheel, 'up', -100), V.height(wheel, 'up', 1e6)], [0, 0]);
        // the view slides out as you climb, is back in the middle at the top, out the other way coming down, and
        // in the middle again when you get off; never more than `drift`, the far picture a third of it
        assert.deepStrictEqual([0, wheel.ms / 2, wheel.ms].map((ms) => Math.abs(V.drift(wheel, ms))), [0, 0, 0]);
        assert.deepStrictEqual([V.drift(wheel, wheel.ms / 4), V.drift(wheel, 3 * wheel.ms / 4)], [32, -32]);
        assert.deepStrictEqual([V.drift(wheel, wheel.ms / 4, V.FAR_DRIFT), V.drift(wheel, 3 * wheel.ms / 4, V.FAR_DRIFT)], [11, -11]);
        for (let ms = -200; ms <= wheel.ms + 200; ms += 50) {
            assert.ok(Math.abs(V.drift(wheel, ms)) <= wheel.drift && Number.isInteger(V.drift(wheel, ms)), `${ms} ms`);
            assert.ok(Math.abs(V.drift(wheel, ms, V.FAR_DRIFT)) <= Math.abs(V.drift(wheel, ms)), 'what is further off slides less');
            // a lift goes straight up
            assert.strictEqual(V.drift(V.RIDES.lift, ms), 0);
        }
        // skipped as the lift is; long enough to look, short enough to sit through
        assert.deepStrictEqual([0, V.SKIP_AFTER, wheel.ms - 1, wheel.ms].map((ms) => V.canSkip(wheel, ms)), [false, true, true, false]);
        // a gondola has no floor counter and no tower going by: those are drawn for a ride with a `top` and a `panel`
        assert.ok(!('top' in wheel) && !('panel' in wheel));
        const ride = src('ViewRide.js');
        assert.ok(ride.includes('const beams = !ride.top ? [] : ViewRide.BEAMS.map(') && ride.includes('if (ride.panel) {'));
        assert.ok(ride.includes("this.run(ViewRide.RIDES.wheel, 'up', null)"), 'no room is swapped behind the curtain');
        // every picture a ride names is loaded and on disk
        const c = cfg();
        for (const r of Object.values(V.RIDES)) {
            for (const key of [r.frame, `${r.view}-far`, `${r.view}-near`, `${r.view}-lights`]) {
                assert.ok(c.spriteMetadata[key], `${key} is not loaded`);
                assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), `${key}.png`);
            }
        }
    });

    test('one ride for one bump: a key held against the gondola boards once, and is still that bump when you step off; let go and pressed again it is another turn (#242)', () => {
        const cells = new Set(['33,17']);
        const scene = { player: { gridX: 32, gridY: 17 }, roomManager: { interactionAt: (x, y, group) => (group === 'ride' && cells.has(`${x},${y}`) ? { kind: 'wheel', group: 'ride' } : null) } };
        const v = game('Object.create(ViewRide.prototype)');
        let rides = 0;
        Object.assign(v, { scene, bump: null, riding: false, wheel() { rides++; this.riding = true; } });
        const east = { x: 1, y: 0 }, none = { x: 0, y: 0 };
        // a cell with nothing to ride: not ours, and nothing is remembered
        assert.deepStrictEqual([v.check(31, 17), rides, v.bump], [false, 0, null]);
        // the bump: one ride
        assert.deepStrictEqual([v.check(33, 17), rides], [true, 1]);
        assert.deepStrictEqual(plain(v.bump), { cell: '33,17', dx: 1, dy: 0 });
        // 14 s of ride with the key down: every frame it is still that bump (GameScene.update), nothing bumps
        for (let f = 0; f < 14000 / 16; f++) v.hold(east);
        v.riding = false;
        // off the wheel with the key still down: the same bump, bumping again every frame - not another ride.
        // The game bumps before it asks what is held (GameScene.update), and it is not the clock that keeps
        // the bump (this scene has none): a frame however long is the same one, where the offering box's
        // 250 ms would have boarded again
        for (let f = 0; f < 120; f++) { assert.strictEqual(v.check(33, 17), true); v.hold(east); }
        assert.strictEqual(rides, 1, 'a held key rode again');
        // a second key down beside it is still that bump; the other way, or nothing, is not
        assert.deepStrictEqual([{ x: 1, y: -1 }, { x: 1, y: 1 }, east].map(h => V.held(v.bump, h) === v.bump), [true, true, true]);
        assert.deepStrictEqual([none, { x: -1, y: 0 }, { x: 0, y: 1 }, null].map(h => V.held(v.bump, h)), [null, null, null, null]);
        assert.strictEqual(V.held(null, east), null);
        // let go for one frame and pressed again: a new bump, a second turn
        v.hold(none);
        assert.strictEqual(v.bump, null);
        assert.deepStrictEqual([v.check(33, 17), rides], [true, 2]);
        // let go during the ride and pressed again while it still turns: that is a press of its own when you are off
        for (let f = 0; f < 200; f++) v.hold(none);
        for (let f = 0; f < 200; f++) v.hold(east);
        v.riding = false;
        assert.deepStrictEqual([v.check(33, 17), rides], [true, 3], 'a fresh press after getting off rides again');
        // bumped from the north with the key held, then the west side: another cell is another bump
        cells.add('33,18');
        v.riding = false;
        v.hold(east);
        scene.player = { gridX: 32, gridY: 18 };
        assert.deepStrictEqual([v.check(33, 18), rides], [true, 4]);
        // the game asks after the flights board and before the shops, not while a ride, a dialogue or a shop is up, and
        // carries the bump every frame
        const gs = src('GameScene.js');
        assert.ok(/if \(this\.viewRide && !this\.viewRide\.riding && !this\.dialogueManager\.isVisible\(\) &&\s+!\(this\.shop && this\.shop\.isVisible\(\)\) && this\.viewRide\.check\(targetGridX, targetGridY\)\) return;/.test(gs));
        assert.ok(gs.indexOf("'flights')") < gs.indexOf('this.viewRide.check(') && gs.indexOf('this.viewRide.check(') < gs.indexOf('this.shop.checkShopInteraction('));
        assert.ok(gs.includes('if (this.viewRide) this.viewRide.hold(this.inputHandler.heading());'));
    });

    test('the gondola is drawn round the window the game cuts the view to, and the one you board is cut from the wheel\'s own (#242)', () => {
        const wheel = V.RIDES.wheel, frame = picture(wheel.frame), win = wheel.window;
        let clear = 0;
        for (let y = win.y; y < win.y + win.h; y++) for (let x = win.x; x < win.x + win.w; x++) if (alpha(frame, x, y) === 0) clear++;
        assert.ok(clear > win.w * win.h * 0.85, `${clear} of ${win.w * win.h} window pixels are clear`);
        // the shell all round the window is opaque: the view shows through the glass and nowhere else
        for (let x = win.x - 8; x < win.x + win.w + 8; x++) for (const y of [win.y - 8, win.y - 1, win.y + win.h, win.y + win.h + 7]) assert.strictEqual(alpha(frame, x, y), 255, `${x},${y}`);
        for (let y = win.y - 8; y < win.y + win.h + 8; y++) for (const x of [win.x - 8, win.x - 1, win.x + win.w, win.x + win.w + 7]) assert.strictEqual(alpha(frame, x, y), 255, `${x},${y}`);
        // (outside the shell the picture is clear - the hanger above it, its rounded corners - and what shows there is the
        // black behind, because each layer of the view is cut to the window)
        assert.ok(src('ViewRide.js').includes('o.setCrop(cx, cy, win.w, win.h);'));
        const art = I.tool('generate_wheel_art.py');
        assert.ok(art.includes(`WIN = (${win.x / 2}, ${win.y / 2}, ${win.w / 2}, ${win.h / 2})`), 'the art tool and the game agree on the window');
        // the layers: the window and the drift either side, drawn at half size
        const near = picture('view-dotonbori-near'), far = picture('view-dotonbori-far');
        assert.deepStrictEqual([near.width, far.width], [win.w + 2 * wheel.drift, win.w + 2 * wheel.drift]);
        // the gondola at the foot of the wheel: two cells square, in the wheel's own colours (it is one of its gondolas)
        const pod = picture(GONDOLA), sprite = picture(WHEEL);
        assert.deepStrictEqual([pod.width, pod.height], [128, 128]);
        const rgb = (im, i) => (im.data[i] << 16) | (im.data[i + 1] << 8) | im.data[i + 2];
        const theirs = new Set();
        for (let i = 0; i < sprite.data.length; i += 4) if (sprite.data[i + 3] === 255) theirs.add(rgb(sprite, i));
        let opaque = 0, shared = 0;
        for (let i = 0; i < pod.data.length; i += 4) if (pod.data[i + 3] === 255) { opaque++; if (theirs.has(rgb(pod, i))) shared++; }
        assert.ok(opaque > 4000 && shared > opaque * 0.9, `${shared} of the gondola's ${opaque} pixels are in the wheel's colours`);
        let foot = 0;
        for (let x = 0; x < pod.width; x++) if (alpha(pod, x, pod.height - 12) > 0) foot++;
        assert.ok(foot > 40, 'it stands on the ground');
    });
};
