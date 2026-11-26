// The home city, the two airports and the flights between them (issue #218): config `airports`
// and the rooms tools/generate_airports.py and tools/generate_sanfranbourne.py write, the rules in
// src/AirTravel.js, and the places the rest of the game has to know that a city is overseas.
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig }) => {
    for (const [name, file] of [['Interactions', 'utils/Interactions.js'], ['Places', 'utils/Places.js'], ['AirTravel', 'AirTravel.js']]) {
        if (game(`typeof ${name}`) === 'undefined') load(file);
    }
    const A = game('AirTravel'), Interactions = game('Interactions'), T = game('Trips');
    const plain = (v) => JSON.parse(JSON.stringify(v));
    const CITY = 'SanFranbourne', HOME = 'SanFranbourneAirport', HANEDA = 'HanedaAirport';
    const K = (x, y) => `${x},${y}`;
    const tiles = (room, name) => ((room.layers.find((l) => l.name === name) || {}).tiles) || {};
    const size = (room) => [room.worldWidth / 64, room.worldHeight / 64];
    const sizeOf = (key) => {
        const b = fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
        return [Math.max(1, Math.round(b.readUInt32BE(16) / 64)), Math.max(1, Math.round(b.readUInt32BE(20) / 64))];
    };
    // every cell that can be walked to from `start`, never stepping on `without` cells
    const reach = (room, start, without = []) => {
        const [W, H] = size(room), solid = tiles(room, 'Colliders'), floor = tiles(room, 'Floor');
        const shut = new Set(without.map((c) => K(...c)));
        const seen = new Set([K(...start)]), todo = [start];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const nx = x + dx, ny = y + dy, k = K(nx, ny);
                if (nx < 0 || ny < 0 || nx >= W || ny >= H || seen.has(k) || k in solid || !(k in floor) || shut.has(k)) continue;
                seen.add(k); todo.push([nx, ny]);
            }
        }
        return seen;
    };
    const where = (room, re) => {
        const out = [];
        for (const l of room.layers) for (const [xy, key] of Object.entries(l.tiles)) if (re.test(key)) out.push([...xy.split(',').map(Number), key]);
        return out;
    };
    const bump = (config, roomKey, x, y) => Interactions.find(config.rooms[roomKey], config.rooms[roomKey], x, y, { sizeOf, venues: game('Shop.VENUES') });

    test('who can fly where: the two airports pair up, each the other\'s only destination (#218)', () => {
        const config = realConfig();
        assert.deepStrictEqual(Object.keys(config.airports).sort(), [HANEDA, HOME].sort());
        assert.deepStrictEqual(plain(A.destinations(config, HANEDA)), [HOME]);
        assert.deepStrictEqual(plain(A.destinations(config, HOME)), [HANEDA]);
        assert.ok(A.canFly(config, HANEDA, HOME) && A.canFly(config, HOME, HANEDA));
        // nowhere from a room that is no airport, never to yourself, never to a room that is no airport
        for (const room of Object.keys(config.rooms)) {
            if (config.airports[room]) continue;
            assert.deepStrictEqual(plain(A.destinations(config, room)), [], room);
            assert.ok(!A.canFly(config, HANEDA, room) && !A.canFly(config, room, HOME), room);
        }
        assert.ok(!A.canFly(config, HANEDA, HANEDA) && !A.canFly(config, HOME, 'Nowhere'));
        // an airport whose room or city is not built is not on the board (and nothing can fly to it)
        const half = Object.assign({}, config, { airports: Object.assign({}, config.airports, { Ghost: { serves: 'Osaka', order: 9, arrive: [1, 1] } }) });
        assert.deepStrictEqual(plain(A.destinations(half, HANEDA)), [HOME]);
        const noCity = Object.assign({}, config, { rooms: Object.assign({}, config.rooms) });
        delete noCity.rooms[CITY];
        assert.deepStrictEqual(plain(A.destinations(noCity, HANEDA)), []);
        // the board: Tokyo first; the home airport is called by its city's name, which is written once
        const reg = A.registry(config);
        assert.strictEqual(reg[HANEDA].label, 'Tokyo');
        assert.strictEqual(reg[HOME].label, config.rooms[CITY].name);
        assert.ok(!('label' in config.airports[HOME]), 'the home city\'s name is not copied into the registry');
        assert.ok(reg[HANEDA].order < reg[HOME].order);
        assert.strictEqual(A.routeText(config, HANEDA, HOME), `Tokyo to ${config.rooms[CITY].name}`);
        assert.strictEqual(A.direction(config, HANEDA, HOME), 1);
        assert.strictEqual(A.direction(config, HOME, HANEDA), -1);
        // the same board as the trains' (StationPicker.board), over the airports
        const board = game('StationPicker.board')(reg, HANEDA, null);
        assert.deepStrictEqual(Array.from(board.rows, (r) => [r.key, r.label, r.here]), [[HOME, config.rooms[CITY].name, false]]);
        assert.strictEqual(board.selected, 0);
        const src = fs.readFileSync(path.join(GV2, 'src', 'StationPicker.js'), 'utf8');
        assert.ok(src.includes('return this.flights ? AirTravel.registry(this.scene.config) : this.scene.config.stations;'));
        assert.ok(src.includes('(this.flights ? this.scene.airTravel : this.scene.trainTravel).go(this.fromKey, row.key);'));
    });

    test('no train reaches the home city: it is on no departures board, and the air is the only way (#218)', () => {
        const config = realConfig();
        const board = game('StationPicker.board');
        for (const [key, st] of Object.entries(config.stations)) {
            assert.ok(st.town !== CITY && st.town !== HOME, `${key} is a station in the home city`);
            const rows = Array.from(board(config.stations, key, null).rows, (r) => r.label);
            assert.ok(!rows.includes(config.rooms[CITY].name), `${key}'s board lists the home city`);
        }
        // Tokyo's airport is a stop on Tokyo Station's board, and its stairs lead into the hall
        const tokyo = Array.from(board(config.stations, 'TokyoStation', null).rows, (r) => r.label);
        assert.ok(tokyo.includes('Haneda Airport'));
        assert.strictEqual(config.stations.HanedaStation.town, HANEDA);
        assert.deepStrictEqual(plain(config.rooms.HanedaStation.transporters.map((t) => [t.targetRoom, t.targetX, t.targetY])),
            [[HANEDA, ...config.airports[HANEDA].entry], [HANEDA, ...config.airports[HANEDA].entry]]);
        assert.ok(config.rooms[HANEDA].transporters.every((t) => t.targetRoom === 'HanedaStation'), 'Haneda leads nowhere but its station');
        // the only doors into the city are its own airport's and its own konbini's
        for (const [key, room] of Object.entries(config.rooms)) {
            for (const t of room.transporters || []) {
                if (t.targetRoom === CITY) assert.ok(key === HOME || key === 'KonbiniSanFranbourne1', `${key} has a door into the home city`);
                if (t.targetRoom === HOME) assert.strictEqual(key, CITY, `${key} has a door into the home airport`);
            }
        }
        // reachable from where the game starts, by door + train + flight; without the flights, not at all
        const start = config.player.startRoom;
        const hops = T.hopsFrom(config, start);
        assert.ok(hops[CITY] > hops[HANEDA] && hops[HANEDA] > hops.TokyoStation, 'start -> Tokyo Station -> Haneda -> flight -> the city');
        assert.strictEqual(hops[HOME], hops[HANEDA] + 1, 'a flight is one hop');
        const grounded = T.hopsFrom(Object.assign({}, config, { airports: {} }), start);
        assert.ok(!(CITY in grounded) && !(HOME in grounded) && HANEDA in grounded);
        // and back: every Japan town can be reached from the city
        const back = T.hopsFrom(config, CITY);
        for (const town of ['Tokyo', 'Osaka', 'Sapporo', 'Asahikawa', 'Sendai', 'Fukuoka']) assert.ok(town in back, `${town} from the home city`);
    });

    test('one airport template: gate and board, the security line you walk through, the kiosk and the pub (#218)', () => {
        const config = realConfig();
        const venues = game('Shop.VENUES'), items = game('Shop.DEFAULT_ITEMS');
        const signature = (room) => JSON.stringify(room.layers.map((l) => [l.name, Object.keys(l.tiles).sort().map((xy) => xy + l.tiles[xy])]));
        assert.strictEqual(signature(config.rooms[HANEDA]), signature(config.rooms[HOME]), 'both airports are the one template');
        for (const key of [HANEDA, HOME]) {
            const room = config.rooms[key], a = config.airports[key], [W, H] = size(room);
            assert.ok(room.interior && room.shopEnabled === false, `${key}: an interior, not a konbini`);
            const walk = reach(room, a.entry);
            // the way in and out: two mats under the front wall, straight below the entry cell
            assert.deepStrictEqual(plain(room.transporters.map((t) => [t.gridX, t.gridY])), [[a.entry[0], H - 1], [a.entry[0] + 1, H - 1]]);
            for (const t of room.transporters) assert.ok(walk.has(K(t.gridX, t.gridY)), `${key}: the way out cannot be walked to`);
            // THE GATE: you arrive in front of it, and it and the board beside it open the flights
            const [gate] = where(room, /^airport-gate/), [boardAt] = where(room, /^airport-board/);
            assert.ok(gate && boardAt, `${key}: a gate and a departures board`);
            assert.deepStrictEqual(plain(a.arrive), [gate[0], gate[1] + 2], `${key}: you step off in front of the gate`);
            assert.ok(walk.has(K(...a.arrive)), `${key}: the gate cannot be walked to from the door`);
            for (const [x, y] of [[gate[0], gate[1] + 1], [gate[0] + 1, gate[1] + 1], [boardAt[0], boardAt[1] + 1], [boardAt[0] + 1, boardAt[1] + 1]]) {
                assert.strictEqual(bump(config, key, x, y).group, 'flights', `${key}: ${x},${y} opens the flights`);
                assert.ok(K(x, y) in tiles(room, 'Colliders') && walk.has(K(x, y + 1)), `${key}: ${x},${y} is bumped from the lounge`);
            }
            // THE SECURITY LINE: the arches are the only way from the hall to the gate
            const arches = where(room, /^airport-security/).map(([x, y]) => [x, y + 1]);
            assert.strictEqual(arches.length, 2, `${key}: two scanner arches`);
            for (const [x, y] of arches) assert.ok(walk.has(K(x, y)), `${key}: arch ${x},${y} is walked through`);
            assert.ok(!reach(room, a.entry, arches).has(K(...a.arrive)), `${key}: the gate can be reached round the security line`);
            assert.ok(where(room, /^airport-xray/).length === 2 && where(room, /^airport-checkin/).length >= 3, `${key}: belts and check-in desks`);
            // THE 7-ELEVEN: the station's booth and its rule - the konbini list - bumped from the hall
            const [kiosk] = where(room, /^station-kiosk/);
            assert.strictEqual(where(room, /^station-kiosk/).length, 1, `${key}: one kiosk`);
            const till = bump(config, key, kiosk[0] + 1, kiosk[1] + 2);
            assert.deepStrictEqual([till.kind, till.group], ['counter', 'shop']);
            assert.ok(walk.has(K(kiosk[0] + 1, kiosk[1] + 3)) && kiosk[1] > a.arrive[1] + 4, `${key}: the kiosk is in the hall`);
            // THE PUB: the izakaya's drinks and food through the shop, bumped from the lounge side
            const [bar] = where(room, /^airport-bar/);
            const pub = bump(config, key, bar[0] + 2, bar[1] + 2);
            assert.deepStrictEqual([pub.kind, pub.group, pub.w, pub.h], ['pub', 'shop', 5, 3]);
            assert.ok(walk.has(K(bar[0] + 2, bar[1] + 3)), `${key}: the bar has no free side`);
            const sold = items.filter(venues.pub.sells).map((i) => i.id);
            assert.ok(sold.includes('nama-beer') && sold.includes('karaage') && !sold.includes('onigiri'), 'the pub pours beer and fries chicken; it is no konbini');
            assert.ok(!venues.pub.buys && !venues.pub.grills && game('Shop.titleFor')('pub', room) === 'AIRPORT PUB');
            // neither till stamps the card (a station's kiosk does not either), and neither airport is a store
            const Stamps = game('Stamps');
            assert.strictEqual(Stamps.placeFor('counter', key, room), null);
            assert.strictEqual(Stamps.placeFor('pub', key, room), null);
            assert.ok(!Stamps.stores(config).some((s) => s.id === key));
            // no konbini shelf rule fires here, and nothing is a bin
            assert.ok(!where(room, /^office-|bin/).length);
        }
        // the hall's rail stop keeps the kiosk rule too: one rule, three rooms
        const rules = Interactions.RULES.filter((r) => r.pattern.test('station-kiosk_0_0'));
        assert.strictEqual(rules.length, 1);
        assert.strictEqual(Interactions.RULES.filter((r) => r.group === 'flights').length, 1);
        assert.strictEqual(Interactions.RULES.filter((r) => r.kind === 'pub').length, 1);
    });

    test('the flight: nine seconds of cabin, skippable after a beat, magnified like the train ride (#218)', () => {
        assert.strictEqual(A.DURATION, 9000);
        assert.ok(A.SKIP_AFTER >= 500 && A.SKIP_AFTER <= 1000, 'the press that boarded cannot skip, a deliberate one soon can');
        assert.strictEqual(A.canSkip(0), false);
        assert.strictEqual(A.canSkip(A.SKIP_AFTER - 1), false);
        assert.strictEqual(A.canSkip(A.SKIP_AFTER), true);
        assert.strictEqual(A.canSkip(A.DURATION - 1), true);
        assert.strictEqual(A.canSkip(A.DURATION), false, 'it is already landing');
        assert.deepStrictEqual([A.progress(-5), A.progress(0), A.progress(4500), A.progress(9000), A.progress(99999)], [0, 0, 0.5, 1, 1]);
        // the sky goes by once: day to dusk flying out, dusk to day flying home, never past either end
        assert.deepStrictEqual([A.skyShift(0, 1, 1000), A.skyShift(0.5, 1, 1000), A.skyShift(1, 1, 1000), A.skyShift(2, 1, 1000)], [0, 500, 1000, 1000]);
        assert.deepStrictEqual([A.skyShift(0, -1, 1000), A.skyShift(0.25, -1, 1000), A.skyShift(1, -1, 1000)], [1000, 750, 0]);
        // the pictures: the cabin is the train interiors' size (so the same magnification applies), its
        // windows are holes, and the sky behind is wider than the cabin and opaque
        const png = require(path.join(GV2, 'tools', 'png.js'));
        const size = (name) => { const b = fs.readFileSync(path.join(GV2, 'assets', 'sprites', name + '.png')); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
        assert.deepStrictEqual(size('plane-interior'), size('train-interior-metro'));
        assert.ok(size('plane-sky')[0] > size('plane-interior')[0]);
        const config = realConfig();
        for (const name of ['plane-interior', 'plane-sky']) assert.ok(config.spriteMetadata[name], `${name} is loaded`);
        const cabin = png.decode ? png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'plane-interior.png'))) : null;
        if (cabin) {
            const alpha = (x, y) => cabin.data[(y * cabin.width + x) * 4 + 3];
            const y = Math.round(cabin.height * A.WINDOW_BAND);
            let holes = 0;
            for (let x = 1; x < cabin.width; x++) if (alpha(x, y) === 0 && alpha(x - 1, y) !== 0) holes++;
            assert.ok(holes >= 10, `the cabin wall has ${holes} windows cut through it`);
            assert.ok(alpha(Math.round(cabin.width / 2), Math.round(cabin.height * A.SEAT_LINE)) > 0, 'the seat is solid');
        }
        const src = fs.readFileSync(path.join(GV2, 'src', 'AirTravel.js'), 'utf8');
        // the train ride's magnification (#201): as big as the world, never taller than the view
        assert.ok(src.includes('TrainTravel.cutsceneScale(scene.uiScale && scene.uiScale.worldZoom, H, cabin.height * 2);'));
        const scale = game('TrainTravel.cutsceneScale');
        for (const [worldZoom, shown] of [[1, 1], [1.5, 1.5], [2, 2], [3, 2]]) assert.strictEqual(scale(worldZoom, 960, 480), shown);
        // ...and the picture is a view-sized backdrop to UIScale, so its overflow is never squeezed in
        assert.ok(src.includes('c.getBounds = (out) => (out || new Phaser.Geom.Rectangle()).setTo(0, 0, W, H);'));
        assert.ok(src.includes("Hints.text(scene, 'SPACE: skip the flight', { tap: true })"), 'the hint is worded for touch');
        assert.strictEqual(game('Hints.word')('SPACE: skip the flight', { tap: true }), 'TAP or A: skip the flight');
        // input: nothing but the skip while flying, and the gate bump is the one way to board
        const input = fs.readFileSync(path.join(GV2, 'src', 'systems', 'InputHandler.js'), 'utf8');
        assert.ok(/if \(this\.scene\.airTravel && this\.scene\.airTravel\.flying\) \{\s+this\.scene\.airTravel\.handleInput\(\);[^}]+return;/.test(input));
        const scene = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(scene.includes("this.roomManager.interactionAt(targetGridX, targetGridY, 'flights')"));
        assert.ok(fs.readFileSync(path.join(GV2, 'index.html'), 'utf8').includes('src/AirTravel.js'));
    });

    test('the home city: one name, every landmark standing and walkable-to, sealed houses, a lit night (#218)', () => {
        const config = realConfig(), room = config.rooms[CITY];
        assert.deepStrictEqual(size(room), [60, 60]);
        // the name is written once in config: the room's. The Map, the board and the footer read it from there
        const raw = fs.readFileSync(path.join(GV2, 'config.json'), 'utf8');
        const uses = raw.split(JSON.stringify(room.name)).length - 1;
        assert.strictEqual(uses, 1, 'rooms.SanFranbourne.name is the only place the bare name is written');
        const gen = fs.readFileSync(path.join(GV2, 'tools', 'generate_sanfranbourne.py'), 'utf8');
        assert.ok(gen.includes(`NAME = '${room.name}'`) && gen.split(`'${room.name}'`).length === 2, 'one constant in the generator');
        // out of the terminal's doors, and every landmark can be walked up to
        const door = config.rooms[HOME].transporters[0];
        assert.strictEqual(door.targetRoom, CITY);
        const walk = reach(room, [door.targetX, door.targetY]);
        const into = room.transporters.filter((t) => t.targetRoom === HOME);
        assert.strictEqual(into.length, 2, 'the terminal has double doors');
        for (const t of into) {
            assert.deepStrictEqual([t.targetX, t.targetY], plain(config.airports[HOME].entry));
            assert.ok(walk.has(K(t.gridX, t.gridY)), 'the terminal door cannot be walked to');
        }
        assert.deepStrictEqual([door.targetX, door.targetY], [into[0].gridX, into[0].gridY + 1], 'you come out in front of the doors');
        const beside = (x, y, w, h) => {
            for (let cx = x - 1; cx <= x + w; cx++) for (let cy = y - 1; cy <= y + h; cy++) if (walk.has(K(cx, cy))) return true;
            return false;
        };
        const LANDMARKS = {
            'sfb-clocks-station': 1, 'sfb-bridge-tower': 2, 'sfb-lady-': 6, 'sfb-mural-': 4, 'sfb-coffee': 2, 'sfb-pyramid': 1,
            'sfb-spire': 1, 'sfb-cable-car': 1, 'sfb-tram': 1, 'sfb-oval_': 1, 'sfb-goalposts': 2, 'sfb-oval-lamp-post': 4,
            'sfb-terminal': 1, 'sfb-pier': 1, 'sfb-sea-lions': 1, 'sfb-rowers': 3, 'sfb-rock': 1, 'seven-eleven': 1,
        };
        for (const [prefix, count] of Object.entries(LANDMARKS)) {
            const found = where(room, new RegExp('^' + prefix));
            assert.strictEqual(found.length, count, `${prefix}: ${found.length} placed`);
            for (const [x, y, key] of found) {
                if (/rowers|rock/.test(key)) continue;          // out on the water: looked at, not walked to
                const [w, h] = sizeOf(key);
                assert.ok(beside(x, y, w, h), `${key} at ${x},${y} cannot be walked up to`);
            }
        }
        assert.ok(where(room, /^sfb-fog-/).length >= 5 && where(room, /^sfb-fog-/).every(([, , , ]) => true));
        // the bridge: the avenue crosses the brown river between the legs of both towers; no water under the deck
        const river = where(room, /^sfb-river_/);
        const rows = [...new Set(river.map(([, y]) => y))].sort((a, b) => a - b);
        assert.ok(rows.length >= 4 && river.every(([x, y]) => K(x, y) in tiles(room, 'Colliders')), 'the river is solid water');
        const deck = [];
        for (let x = 0; x < 60; x++) if (rows.every((y) => walk.has(K(x, y)))) deck.push(x);
        assert.deepStrictEqual(deck, [28, 29, 30, 31], 'the one way over the river is the bridge deck');
        for (const [x, y] of where(room, /^sfb-bridge-tower/)) {
            assert.ok(K(x, y + 6) in tiles(room, 'Colliders') && K(x + 5, y + 6) in tiles(room, 'Colliders'), 'a tower stands on its two legs');
            for (let cx = x + 1; cx <= x + 4; cx++) for (let cy = y; cy <= y + 6; cy++) assert.ok(!(K(cx, cy) in tiles(room, 'Colliders')), `tower blocks the deck at ${cx},${cy}`);
        }
        // the pier is walked on to its end, and the sea lions are bumped from it
        const [pier] = where(room, /^sfb-pier/);
        assert.ok(walk.has(K(pier[0] + 1, pier[1] + 7)) && !walk.has(K(pier[0] + 1, pier[1] + 9)));
        const [lions] = where(room, /^sfb-sea-lions/);
        assert.strictEqual(lions[0] + 3, pier[0], 'the raft is against the pier');
        // (the raft floats on pond water, so the cell is also a fishing spot: ask for the line it says)
        const says = (x, y) => (Interactions.find(room, room, x, y, { sizeOf, group: 'flavour' }) || {}).say || '';
        assert.ok(/sea lions/.test(says(lions[0] + 2, lions[1])) && /sea lions/.test(says(lions[0] + 2, lions[1] + 1)));
        const clocks = where(room, /^sfb-clocks-station/)[0];
        assert.ok(/under the clocks/.test(says(clocks[0] + 5, clocks[1] + 6)));
        // the vehicles share the street's rails; the oval is flat (walked on), the towers are looked up at
        const rails = where(room, /^sfb-rail-h/);
        assert.ok(rails.length > 40 && rails.every(([, y]) => y === rails[0][1]));
        for (const [x, y, key] of where(room, /^sfb-(cable-car|tram)/)) assert.strictEqual(y + 1, rails[0][1], `${key} is on the rails`);
        const [oval] = where(room, /^sfb-oval_/);
        assert.ok(walk.has(K(oval[0] + 6, oval[1] + 3)) && config.spriteMetadata['sfb-oval_0_0'].depthBias < 0);
        for (const tall of ['sfb-pyramid', 'sfb-spire']) assert.ok(tall in config.game.lookUp.sprites, `${tall} is looked up at`);
        // night: street lamps and the ground's light towers glow (DayNight lights `lamp-post`)
        const lit = where(room, /lamp-post|-lanterns/);
        assert.ok(lit.length >= 30 && lit.some(([, , k]) => /^sfb-oval-lamp-post/.test(k)), `${lit.length} lamps`);
        assert.ok(!room.interior, 'the city has a day and a night');
        // houses stay sealed, no bins, and the konbini is the usual interior
        assert.ok(!Object.keys(config.rooms).some((k) => k.startsWith('House' + CITY)), 'no house interiors yet');
        assert.ok(room.transporters.every((t) => t.targetRoom === HOME || t.targetRoom === 'KonbiniSanFranbourne1'));
        assert.ok(!where(room, /bin/).length);
        assert.ok(config.rooms.KonbiniSanFranbourne1.interior && game('Stamps').isStore(config.rooms.KonbiniSanFranbourne1));
    });

    test('the leaners: four people folded at the waist, solid street props that block no door and no route, each with its own line', () => {
        const config = realConfig(), room = config.rooms[CITY];
        const solid = tiles(room, 'Colliders'), floor = tiles(room, 'Floor');
        const found = where(room, /^sfb-lean-/);
        assert.deepStrictEqual(found.map(([, , key]) => key).sort(), ['a', 'b', 'c', 'd'].map((k) => `sfb-lean-${k}_0_0`), 'one of each look');
        const start = config.rooms[HOME].transporters[0];
        const walk = reach(room, [start.targetX, start.targetY]);
        const fronts = new Set();
        for (const t of room.transporters) for (const [dx, dy] of [[0, 0], [0, 1], [1, 0], [-1, 0], [0, -1]]) fronts.add(K(t.gridX + dx, t.gridY + dy));
        const lines = new Set();
        for (const [x, y, key] of found) {
            assert.deepStrictEqual(sizeOf(key), [1, 1], `${key} is one cell`);
            assert.strictEqual(config.tileNames[key], 'sfb-lean');
            assert.ok(K(x, y) in tiles(room, 'Collidables') && K(x, y) in solid, `${key} is a solid prop`);
            assert.ok(!fronts.has(K(x, y)), `${key} stands on a door or in front of one`);
            assert.ok(!(x >= 28 && x <= 31), `${key} stands on the avenue`);
            // bumped from a free cell beside it, and it says its line there and nothing else does
            const beside = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dx, dy]) => [x + dx, y + dy]).filter((c) => walk.has(K(...c)));
            assert.ok(beside.length >= 2, `${key} at ${x},${y} has ${beside.length} free cells beside it`);
            const hit = Interactions.find(room, room, x, y, { sizeOf, group: 'flavour' });
            assert.ok(hit && hit.kind === 'leaner' && hit.say && hit.say.length <= 60, `${key} says nothing`);
            assert.strictEqual(bump(config, CITY, x, y).kind, 'leaner');
            lines.add(hit.say);
            // not a pinch point: whoever could pass before can still pass (its neighbours are joined without it)
            const round = reach(room, beside[0], [[x, y]]);
            for (const c of beside) assert.ok(round.has(K(...c)), `${key} closes a path at ${c}`);
            // on paving, not on the road or the grass
            assert.ok(/(concrete|brick)-autotile/.test(floor[K(x, y)]), `${key} stands on ${floor[K(x, y)]}`);
        }
        assert.strictEqual(lines.size, 4, 'each has its own line');
        // the way from the airport over the bridge to the end of the pier is as it was: the avenue,
        // the deck and the pier have nothing new on them, and it is still walked end to end
        const [pier] = where(room, /^sfb-pier/);
        for (let y = 18; y <= pier[1] + 7; y++) for (let x = 28; x <= 31; x++) assert.ok(walk.has(K(x, y)), `the avenue is shut at ${x},${y}`);
        const [tower] = where(room, /^sfb-bridge-tower/);
        assert.ok(walk.has(K(tower[0] + 2, tower[1] + 6)) && walk.has(K(pier[0] + 1, pier[1] + 7)));
        for (const t of room.transporters) assert.ok(walk.has(K(t.gridX, t.gridY)) && walk.has(K(t.gridX, t.gridY + 1)), 'a door is shut off');
        // deadpan and nobody's name: lower case like every other line, no cast member in it
        const cast = ['bailey', 'dylan', 'damian', 'julia', 'james', 'khoi', 'sam', 'xander'];
        for (const line of lines) assert.ok(line === line.toLowerCase() && !cast.some((n) => line.includes(n)), line);
    });

    test('the home city is on no trip: nobody stands there, no player starts there, the blog never offers it (#218)', () => {
        const config = realConfig();
        const away = new Set([CITY, HOME, HANEDA, 'HanedaStation', 'KonbiniSanFranbourne1']);
        for (const key of away) assert.deepStrictEqual(plain(config.rooms[key].npcs || []), [], `${key} has NPCs`);
        const trips = T.of(config);
        assert.ok(trips.length >= 2);
        for (const trip of trips) {
            assert.ok(!away.has((T.cell(config, trip.home) || {}).room), `${trip.name} is based in the home city`);
            for (const stay of trip.stays || []) assert.ok(!away.has(stay.room), `${trip.name} stays in the home city`);
            const lead = Number.isFinite(trip.lead) ? trip.lead : T.LEAD;
            for (let day = T.addDays(trip.start, -lead - 1); day <= T.addDays(trip.end, 1); day = T.addDays(day, 1)) {
                for (const g of T.membersByRoom(config, day)) assert.ok(!away.has(g.room), `${g.room} has trip members on ${day}`);
                for (const played of [undefined, ...trip.members]) {
                    const at = T.startFor(config, day, { played });
                    assert.ok(at && !away.has(at.room), `a player starts in ${at && at.room} on ${day}`);
                }
            }
        }
        assert.ok(!away.has(config.player.startRoom));
        // the blog pipeline's opt-out: `interior` for the airports, `"blog": false` for the city and the rail stop
        assert.ok(config.rooms[HOME].interior && config.rooms[HANEDA].interior && config.rooms.KonbiniSanFranbourne1.interior);
        assert.strictEqual(config.rooms[CITY].blog, false);
        assert.strictEqual(config.rooms.HanedaStation.blog, false);
        for (const [key, room] of Object.entries(config.rooms)) if (!away.has(key)) assert.ok(room.blog !== false, `${key} is closed to the blog`);
        const py = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        assert.ok(py.includes("if not r.get('interior') and r.get('blog') is not False}"));
    });

    test('the Map and the world file: an overseas marker for the home city, Haneda in Tokyo\'s dot, far to the south-east (#218)', () => {
        const config = realConfig(), P = game('Places');
        const home = P.list(config).find((p) => p.key === CITY);
        assert.ok(home && home.overseas && home.label === config.rooms[CITY].name);
        assert.ok(P.list(config).filter((p) => p.overseas).length === 1);
        assert.strictEqual(P.of(config, CITY), CITY);
        assert.strictEqual(P.of(config, HOME), CITY);
        assert.strictEqual(P.of(config, 'KonbiniSanFranbourne1'), CITY);
        assert.strictEqual(P.of(config, HANEDA), 'TokyoCity');
        assert.strictEqual(P.of(config, 'HanedaStation'), 'TokyoCity');
        assert.strictEqual(P.whereText(config, CITY), `${config.rooms[CITY].name} (overseas)`);
        assert.strictEqual(P.whereText(config, HOME), `${config.rooms[HOME].name} (in ${config.rooms[CITY].name}, overseas)`);
        assert.strictEqual(P.whereText(config, HANEDA), 'Haneda Airport (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'HanedaStation'), 'Haneda Station (in Tokyo)');
        assert.deepStrictEqual(plain(P.arrival(config, CITY)), { room: CITY, x: 9, y: 13 });
        // nobody is ever there, so its marker is never the red dot; the ring is the player's
        for (const day of ['2025-10-27', '2027-02-20', '2027-02-10']) assert.ok(!P.present(config, day).has(CITY));
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('} else if (d.overseas) {') && src.includes('overseas: p.overseas'));
        // devhouse.world: south and east of every other map, touching none (the overlap rule is map-data's)
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        const mine = world.maps.find((m) => path.basename(m.fileName) === 'sanfranbourne.tmj');
        assert.ok(mine, 'the home city is in devhouse.world');
        assert.deepStrictEqual([mine.width, mine.height], [60 * 64, 60 * 64]);
        for (const m of world.maps) {
            if (m === mine) continue;
            assert.ok(mine.x >= m.x + m.width + 1024 && mine.y >= m.y + m.height + 1024, `${path.basename(m.fileName)} is not north-west of the home city`);
        }
    });
};
