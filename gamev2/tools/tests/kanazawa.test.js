// Hokuriku (issue #68, stage 3): Kanazawa the full town, Shirakawa-go and Toyama walked to from it -
// three districts of a second stitched city, HokurikuCity.
module.exports = ({ test, assert, fs, path, GV2, game, worldWith }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const DISTRICTS = ['Kanazawa', 'Shirakawago', 'Toyama'];
    const layer = (room, n) => ((cfg.rooms[room].layers || []).find((l) => l.name === n) || {}).tiles || {};
    const size = (room) => [cfg.rooms[room].worldWidth / 64, cfg.rooms[room].worldHeight / 64];
    const solid = (room, x, y) => `${x},${y}` in layer(room, 'Colliders');
    const sprites = {};                                   // room -> sprite key -> its top-left cells
    for (const r of DISTRICTS) {
        sprites[r] = {};
        for (const l of (cfg.rooms[r] || {}).layers || []) {
            for (const [xy, t] of Object.entries(l.tiles || {})) (sprites[r][name(t)] = sprites[r][name(t)] || []).push(xy.split(',').map(Number));
        }
    }
    const at = (room, key) => { assert.ok(sprites[room][key], `${room} has no ${key}`); return sprites[room][key][0]; };
    const cells = (key) => { const m = cfg.spriteMetadata[key]; return [Math.round(0.5 / m.anchorX), Math.round(0.5 / m.anchorY)]; };
    const offset = Object.fromEntries(((cfg.cities.HokurikuCity || {}).rooms || []).map((m) => [m.room, m]));
    // a district cell in the city's own cells (relative to Kanazawa's corner - only differences matter)
    const inCity = (room, x, y) => [x + offset[room].x, y + offset[room].y];

    test('Hokuriku is a second stitched city: Kanazawa, Shirakawa-go and Toyama, placed as the generators lay them out (#68)', () => {
        const city = cfg.cities.HokurikuCity;
        assert.ok(city, 'config cities has no HokurikuCity');
        assert.deepStrictEqual(city.rooms.map((m) => m.room), DISTRICTS);
        assert.strictEqual(city.name, 'Hokuriku');
        assert.ok(city.backdrop && city.backdrop.floor && city.backdrop.tree, 'the gaps between the districts need a woodland backdrop');
        assert.deepStrictEqual(DISTRICTS.map((r) => cfg.rooms[r].name), ['Kanazawa', 'Shirakawa-go', 'Toyama'], 'the HUD names');
        // tools/hokuriku.py is where the three generators agree on the layout: the world file must match it
        const py = fs.readFileSync(path.join(GV2, 'tools', 'hokuriku.py'), 'utf8');
        const table = (v) => Object.fromEntries([...py.match(new RegExp(`^${v} = \\{(.*)\\}`, 'm'))[1].matchAll(/'(\w+)': \((-?\d+), (-?\d+)\)/g)]
            .map((m) => [m[1], [Number(m[2]), Number(m[3])]]));
        const AT = table('AT'), SIZE = table('SIZE');
        for (const r of DISTRICTS) {
            assert.deepStrictEqual(size(r), SIZE[r], `${r} is not the size hokuriku.py says`);
            assert.deepStrictEqual([offset[r].x - offset.Kanazawa.x, offset[r].y - offset.Kanazawa.y],
                [AT[r][0] - AT.Kanazawa[0], AT[r][1] - AT.Kanazawa[1]], `${r} is not where hokuriku.py puts it: devhouse.world / sync_cities.py`);
        }
        // no district overlaps another (each owns all of its own cells), and Toyama does not touch Kanazawa
        const box = (r) => { const [x, y] = inCity(r, 0, 0), [w, h] = size(r); return { x, y, w, h }; };
        const apart = (a, b, gap = 0) => a.x + a.w + gap <= b.x || b.x + b.w + gap <= a.x || a.y + a.h + gap <= b.y || b.y + b.h + gap <= a.y;
        for (const a of DISTRICTS) for (const b of DISTRICTS) if (a < b) assert.ok(apart(box(a), box(b)), `${a} and ${b} overlap`);
        assert.ok(apart(box('Kanazawa'), box('Toyama'), 1), 'Kanazawa and Toyama touch: nothing but the walk through Shirakawa-go joins them');
        // no room is in two cities
        const all = Object.values(cfg.cities).flatMap((c) => c.rooms.map((m) => m.room));
        assert.strictEqual(new Set(all).size, all.length);
    });

    test('Hokuriku: the seams line up - the road, the mountain path and the river carry straight across, and each seam cell has its ?stitch=0 transporter both ways (#68)', () => {
        const seams = DISTRICTS.flatMap((r) => cfg.rooms[r].transporters.filter((t) => DISTRICTS.includes(t.targetRoom)).map((t) => [r, t]));
        assert.strictEqual(seams.length, 3 + 3 + 2 + 2, 'three road cells Kanazawa<->Shirakawa-go, two path cells Shirakawa-go<->Toyama, each way');
        const floorAt = (room, x, y) => name(layer(room, 'Floor')[`${x},${y}`]);
        for (const [room, t] of seams) {
            const [w, h] = size(room);
            assert.ok(t.hidden && (t.gridX === 0 || t.gridY === 0 || t.gridX === w - 1 || t.gridY === h - 1), `${room} ${t.gridX},${t.gridY}: a seam is a hidden transporter on the district's edge`);
            assert.ok(!solid(room, t.gridX, t.gridY) && !solid(t.targetRoom, t.targetX, t.targetY), `${room} ${t.gridX},${t.gridY}: the seam or its target is solid`);
            // the cell across the edge, in the neighbour: it is the same city cell + 1, it is open, same ground, and it leads back
            const [cx, cy] = inCity(room, t.gridX, t.gridY);
            const [dx, dy] = t.gridX === 0 ? [-1, 0] : t.gridY === 0 ? [0, -1] : t.gridX === w - 1 ? [1, 0] : [0, 1];
            const nx = cx + dx - offset[t.targetRoom].x, ny = cy + dy - offset[t.targetRoom].y;
            const back = cfg.rooms[t.targetRoom].transporters.find((b) => b.gridX === nx && b.gridY === ny);
            assert.ok(back && back.targetRoom === room, `${room} ${t.gridX},${t.gridY}: the cell across the seam (${t.targetRoom} ${nx},${ny}) has no transporter back`);
            assert.strictEqual(floorAt(room, t.gridX, t.gridY), floorAt(t.targetRoom, nx, ny), `the ground changes across the seam at ${room} ${t.gridX},${t.gridY}`);
            // it lands three cells past the neighbour's edge cell, along the same line
            assert.deepStrictEqual([t.targetX, t.targetY], [nx + dx * 3, ny + dy * 3], 'a seam lands three cells in from the neighbour\'s edge');
        }
        assert.ok(/^road-/.test(floorAt('Kanazawa', size('Kanazawa')[0] - 1, 31)), 'the way out of Kanazawa is its road');
        // the only open cells on a shared edge are the seam cells: nothing else is walkable across stitched but not with ?stitch=0
        const edgeOpen = (room) => {                  // the edge cells that can be walked to from the district's ways in
            const [w, h] = size(room), todo = cfg.rooms[room].transporters.map((t) => [t.gridX, t.gridY]);
            const seen = new Set(todo.map((c) => c.join()));
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    if (nx < 0 || ny < 0 || nx >= w || ny >= h || solid(room, nx, ny) || seen.has(`${nx},${ny}`)) continue;
                    seen.add(`${nx},${ny}`); todo.push([nx, ny]);
                }
            }
            return [...seen].filter((xy) => { const [x, y] = xy.split(',').map(Number); return x === 0 || y === 0 || x === w - 1 || y === h - 1; }).sort();
        };
        for (const r of DISTRICTS) {
            const mine = cfg.rooms[r].transporters.filter((t) => DISTRICTS.includes(t.targetRoom)).map((t) => `${t.gridX},${t.gridY}`).sort();
            assert.deepStrictEqual(edgeOpen(r), mine, `${r}: an edge cell is open that is not a seam`);
        }
        // the Sho river: water in the same city columns either side of the Shirakawa-go / Toyama edge
        const water = (room, x, y) => name(layer(room, 'Water')[`${x},${y}`]).startsWith('pond-autotile_');
        const [sw] = size('Shirakawago'), th = size('Toyama')[1];
        const cols = [];
        for (let x = 0; x < sw; x++) if (water('Shirakawago', x, 0)) cols.push(x);
        assert.ok(cols.length >= 4, 'no river at Shirakawa-go\'s north edge');
        for (let x = 0; x < sw; x++) {
            const tx = inCity('Shirakawago', x, 0)[0] - offset.Toyama.x;
            if (tx < 0 || tx >= size('Toyama')[0]) continue;
            assert.strictEqual(water('Toyama', tx, th - 1), cols.includes(x), `the river does not carry across at Shirakawa-go column ${x}`);
        }
    });

    test('Hokuriku is one walkable room: Kanazawa -> Shirakawa-go -> Toyama and back on foot, stitched and with ?stitch=0 (#68)', () => {
        const into = cfg.rooms.Kanazawa.transporters.find((t) => t.targetRoom === 'KanazawaStation');
        const [bx, by] = at('Shirakawago', 'shirakawa-bridge_0_0'), [tx, ty] = at('Toyama', 'toyama-port-tower_0_0');
        const stops = [['Kanazawa', into.gridX, into.gridY + 1],        // out of the station house
            ['Shirakawago', bx - 1, by + 1],                             // the west bridgehead
            ['Shirakawago', bx + 8, by + 1],                             // ...and over the river
            ['Toyama', tx - 1, ty + 6],                                  // the quay under the port tower
            ['Shirakawago', bx + 8, by + 1], ['Kanazawa', into.gridX, into.gridY + 1]];
        for (const stitch of [true, false]) {
            const { world } = worldWith(stitch);
            const rm = world.roomManager, tag = stitch ? 'stitched' : '?stitch=0';
            world.enter(...stops[0]);
            if (stitch) {
                assert.strictEqual(world.here().city, 'HokurikuCity', 'Kanazawa is entered as the city room');
                assert.deepStrictEqual([rm.rooms.HokurikuCity.worldWidth / 64, rm.rooms.HokurikuCity.worldHeight / 64], [110, 66]);
                assert.strictEqual(rm.rooms.HokurikuCity.depthScale, 1, 'the city is short enough that Y-sorted depths need no squeeze');
                assert.strictEqual(Object.keys(rm.cities).length, 2, 'both cities are stitched');
            } else {
                assert.strictEqual(world.here().city, null);
            }
            let fades = 0, crossings = 0;
            const walk = (room, x, y) => {
                for (let guard = 0; guard < 4 && world.here().room !== room; guard++) {
                    // not there yet: walk to the nearest seam that leads on (stitched, the path below does it in one)
                    if (stitch) break;
                    const seam = world.room.transporters.filter((t) => DISTRICTS.includes(t.targetRoom))
                        .map((t) => ({ t, route: world.path(t.gridX, t.gridY) })).filter((s) => s.route)
                        .sort((a, b) => (a.t.targetRoom === room ? 0 : 1) - (b.t.targetRoom === room ? 0 : 1) || a.route.length - b.route.length)[0];
                    assert.ok(seam, `${tag}: no seam can be walked to from ${world.here().room}`);
                    for (const dir of seam.route) {
                        const r = world.step(dir);
                        assert.ok(r.moved, `${tag}: blocked on the way to the seam`);
                        if (r.transported) fades++;
                    }
                }
                const to = rm.resolve(room, x, y);
                const route = world.path(to.x, to.y);
                assert.ok(route, `${tag}: no way on foot to ${room} ${x},${y} from ${world.here().room} ${world.here().x},${world.here().y}`);
                for (const dir of route) {
                    const r = world.step(dir);
                    assert.ok(r.moved, `${tag}: blocked on the way to ${room} ${x},${y}`);
                    assert.ok(!r.transported, `${tag}: a transporter fired on the way to ${room} ${x},${y}`);
                    if (r.crossed) crossings++;
                }
                assert.deepStrictEqual([world.here().room, world.here().x, world.here().y], [room, x, y], tag);
            };
            for (const stop of stops.slice(1)) walk(...stop);
            // out by road, over the bridge, up the pass, and the same way home: four district changes
            assert.deepStrictEqual([fades, crossings], stitch ? [0, 4] : [4, 0], `${tag}: fades, crossings`);
            // back at the station house door: one step north is the way in to the trains
            const inn = world.step('n');
            assert.strictEqual(inn.transported && inn.transported.to, 'KanazawaStation', tag);
        }
    });

    test('Kanazawa: the station is a city stop on the line from Tokyo; Shirakawa-go and Toyama have none (#68)', () => {
        const st = cfg.stations.KanazawaStation;
        assert.deepStrictEqual([st.label, st.town, st.train, st.parent], ['Kanazawa', 'Kanazawa', 'train-orange', undefined]);
        assert.ok(st.order > cfg.stations.HanedaStation.order && st.order < cfg.stations.OsakaStation.order, "after Tokyo and Haneda on the board, before Osaka");
        // a main-line city stop takes the large station (#206), with its name board in Japanese
        assert.deepStrictEqual([st.size, st.ja], ['large', '金沢']);
        const boards = cfg.rooms.KanazawaStation.layers.flatMap((l) => Object.values(l.tiles || {})).filter((t) => name(t) === 'station-name-kanazawa_0_0');
        assert.ok(boards.length >= 1, 'the 金沢 / KANAZAWA name board hangs in the station');
        assert.strictEqual(cfg.rooms.KanazawaStation.name, 'Kanazawa Station');
        const into = cfg.rooms.Kanazawa.transporters.find((t) => t.targetRoom === 'KanazawaStation');
        const back = cfg.rooms.KanazawaStation.transporters.filter((t) => t.targetRoom === 'Kanazawa');
        assert.ok(into && back.length === 2, 'station house door and the two door mats');
        assert.deepStrictEqual([into.targetX, into.targetY], st.entry, "the town door lands on the station's entry cell");
        for (const t of back) assert.deepStrictEqual([t.targetX, t.targetY], [into.gridX, into.gridY + 1], 'you step out in front of the station house door');
        assert.deepStrictEqual(Object.values(cfg.stations).filter((s) => ['Shirakawago', 'Toyama'].includes(s.town)), [], 'you walk to the small places');
        for (const r of ['Shirakawago', 'Toyama']) {
            assert.ok(cfg.rooms[r].transporters.every((t) => DISTRICTS.includes(t.targetRoom)), `${r} has a door that is not a seam`);
            assert.ok(!Object.keys(sprites[r]).some((k) => k.startsWith('train-track')), `${r} has a railway`);
        }
    });

    test('Kanazawa: the 7-Eleven has its own interior, wired both ways (#68)', () => {
        const [kx, ky] = at('Kanazawa', 'seven-eleven_0_0');
        const door = cfg.rooms.Kanazawa.transporters.find((t) => t.targetRoom === 'KonbiniKanazawa1');
        assert.ok(door, 'the konbini door is not wired: run generate_konbinis.py Kanazawa');
        assert.deepStrictEqual([door.gridX, door.gridY], [kx + 1, ky + 3]);
        assert.ok(!solid('Kanazawa', door.gridX, door.gridY) && !(`${door.gridX},${door.gridY}` in layer('Kanazawa', 'Collidables')), 'something stands in the doorway');
        const shop = cfg.rooms.KonbiniKanazawa1;
        assert.strictEqual(shop.name, '7-Eleven · Kanazawa');
        assert.strictEqual(shop.interior, true);
        for (const t of shop.transporters) assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Kanazawa', kx + 1, ky + 4], 'you step out in front of the shop door');
    });

    test('Hokuriku: every landmark is there, its visitor stands in the open in front of it, and nobody walks behind a building (#68)', () => {
        const { world } = worldWith(true);
        const rm = world.roomManager;
        const into = cfg.rooms.Kanazawa.transporters.find((t) => t.targetRoom === 'KanazawaStation');
        world.enter('Kanazawa', into.gridX, into.gridY + 1);
        const seen = world.reachable();
        const walkable = (room, x, y) => { const c = rm.resolve(room, x, y); return seen.has(`${c.x},${c.y}`); };
        // room -> sprite -> the cell its visitor stands on, relative to the sprite's top-left (LANDMARKS in tools/blog_to_npc.py)
        const stand = {
            Kanazawa: { 'kanazawa-ishikawa-gate_0_0': [6, 6], 'kanazawa-kotoji_0_0': [-1, 1], 'kanazawa-chaya-a_0_0': [2, 4],
                'kanazawa-whisky-bar_0_0': [2, 4], 'sendai-gate_0_0': [-1, -2], 'seven-eleven_0_0': [0, 4] },
            Shirakawago: { 'shirakawa-bridge_0_0': [10, 2], 'shirakawa-lookout_0_0': [1, -1], 'shirakawa-gassho_0_0': [3, 5] },
            Toyama: { 'toyama-glass-museum_0_0': [1, 6], 'toyama-tram-stop_0_0': [3, 1], 'toyama-ramen_0_0': [2, 4], 'toyama-port-tower_0_0': [-1, 6] },
        };
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'blog_to_npc.py'), 'utf8');
        for (const [room, list] of Object.entries(stand)) {
            // every cell a sprite of this room is drawn across: a visitor must not be on, under or behind one
            const drawn = new Set();
            for (const l of cfg.rooms[room].layers) {
                if (l.z < 2) continue;
                for (const [xy, t] of Object.entries(l.tiles || {})) {
                    if (!(name(t) in cfg.spriteMetadata) || cfg.spriteMetadata[name(t)].depthBias) continue;
                    const [x, y] = xy.split(',').map(Number), [w, h] = cells(name(t));
                    for (let i = 0; i < w; i++) for (let j = 0; j < h; j++) drawn.add(`${x + i},${y + j}`);
                }
            }
            for (const [key, [dx, dy]] of Object.entries(list)) {
                const [x, y] = at(room, key);
                assert.ok(key in cfg.spriteMetadata, `${key} is not in spriteMetadata (not loaded at boot)`);
                assert.ok(walkable(room, x + dx, y + dy), `${room} ${key}: nobody can walk to (${x + dx},${y + dy})`);
                assert.ok(!drawn.has(`${x + dx},${y + dy}`), `${room} ${key}: the visitor at (${x + dx},${y + dy}) stands on or behind a sprite`);
                assert.ok(!cfg.rooms[room].transporters.some((t) => t.gridX === x + dx && t.gridY === y + dy), `${room} ${key}: the visitor stands in a doorway`);
                if (key !== 'seven-eleven_0_0') {
                    const row = new RegExp(`\\('${key.replace(/_0_0$/, '_')}', [^\\n]*\\(${dx}, ${dy}\\), \\{'rooms': \\('${room}',\\)\\}\\)`);
                    assert.ok(row.test(tool), `LANDMARKS has no ${room} row for ${key} standing at (${dx}, ${dy})`);
                }
            }
        }
        // buildings are solid over their whole footprint, roof rows included. The one cell of a building you
        // can step onto is the doorway of a machiya that is a house (#208): the middle of its front row,
        // a hidden door into a House room of that district, with the street in front of it
        const doorway = (room, key, x, y, w, h, cx, cy) => /^machiya/.test(key) && cx === x + (w - 1) / 2 && cy === y + h - 1 &&
            walkable(room, cx, cy + 1) && cfg.rooms[room].transporters.some((t) => t.hidden && t.gridX === cx && t.gridY === cy &&
                ((cfg.rooms[t.targetRoom] || {}).house || {}).host === room);
        // or a tower's door (#216): on its ground-floor row, a hidden door into a Lobby room of this town,
        // with the street in front of it - Kanazawa's yellow high-rise (15,28) and its midrise flats (28,28)
        const lobbyDoor = (room, key, y, h, cx, cy) => /^(highrise|midrise)/.test(key) && cy === y + h - 1 &&
            walkable(room, cx, cy + 1) && cfg.rooms[room].transporters.some((t) => t.hidden && t.gridX === cx && t.gridY === cy &&
                ((cfg.rooms[t.targetRoom] || {}).lobby || {}).host === room);
        const opened = [];
        for (const room of DISTRICTS) {
            for (const key of Object.keys(sprites[room]).filter((k) => /^(highrise|midrise|machiya|kanazawa-chaya|kanazawa-whisky|shirakawa-gassho|toyama-glass|toyama-ramen)/.test(k))) {
                const [w, h] = cells(key);
                for (const [x, y] of sprites[room][key]) {
                    for (let cx = x; cx < x + w; cx++) for (let cy = y; cy < y + h; cy++) {
                        if (doorway(room, key, x, y, w, h, cx, cy)) continue;
                        if (lobbyDoor(room, key, y, h, cx, cy)) { opened.push(`${room} ${key} ${cx},${cy}`); continue; }
                        assert.ok(!walkable(room, cx, cy), `${room} ${key}: (${cx},${cy}) can be walked onto, behind the building`);
                    }
                }
            }
        }
        assert.deepStrictEqual(opened.sort(), ['Kanazawa highrise-yellow_0_0 15,28', 'Kanazawa midrise-apartment_0_0 28,28'], 'the tower doors that open');
        // Kanazawa is what the posts saw: a row of teahouses, a castle gate you walk THROUGH to grounds with no keep,
        // a garden pond with the Kotoji lantern on its bank, a samurai lane between earthen walls along a canal
        const K = sprites.Kanazawa;
        assert.ok(K['kanazawa-chaya-a_0_0'].length + K['kanazawa-chaya-b_0_0'].length >= 4, 'the teahouse row');
        const [gx, gy] = at('Kanazawa', 'kanazawa-ishikawa-gate_0_0');
        for (let y = gy - 1; y <= gy + 4; y++) assert.ok(walkable('Kanazawa', gx + 3, y) && walkable('Kanazawa', gx + 4, y), `the gateway is shut at row ${y}`);
        assert.ok(K['traffic-cone_0_0'].every(([, y]) => y < gy), 'the castle grounds are beyond the gate');
        const [lx, ly] = at('Kanazawa', 'kanazawa-kotoji_0_0');
        assert.ok(name(layer('Kanazawa', 'Water')[`${lx},${ly + 2}`]).startsWith('pond-autotile_'), 'the Kotoji lantern stands on the pond\'s bank');
        assert.ok(K['sendai-earthen-wall_0_0'].length >= 60 && K['sendai-pine_0_0'].length >= 15, 'earthen walls and pines');
        const [cbx, cby] = at('Kanazawa', 'kanazawa-canal-bridge_0_0');
        assert.strictEqual(cfg.spriteMetadata['kanazawa-canal-bridge_0_0'].depthBias, -200, 'the canal bridge lies flat, under whoever is on it');
        for (let y = cby; y < cby + 4; y++) assert.ok(walkable('Kanazawa', cbx, y) && walkable('Kanazawa', cbx + 1, y), 'the canal bridge can be crossed');
        assert.ok(walkable('Kanazawa', cbx, cby + 5), 'the bridge leads through the samurai gate into the court');
        assert.strictEqual(cfg.game.lookUp.sprites['toyama-port-tower'], 0, 'the camera looks up at the port tower');
    });

    test('Shirakawa-go: the suspension bridge is the only way over the river; Toyama: the sea is the north edge, with a boat lane (#68)', () => {
        const [bx, by] = at('Shirakawago', 'shirakawa-bridge_0_0');
        assert.strictEqual(cfg.spriteMetadata['shirakawa-bridge_0_0'].depthBias, -200, 'the deck lies flat, under whoever is on it');
        const water = layer('Shirakawago', 'Water'), [, sh] = size('Shirakawago');
        const river = Object.keys(water).map((xy) => xy.split(',').map(Number));
        assert.ok(new Set(river.map(([, y]) => y)).size === sh, 'the river runs the whole height of the map');
        const open = river.filter(([x, y]) => !solid('Shirakawago', x, y));
        assert.ok(open.length >= 4 && open.every(([x, y]) => y === by + 1 && x > bx && x < bx + 7), 'water is walkable only on the bridge deck: ' + JSON.stringify(open));
        assert.ok(!solid('Shirakawago', bx, by + 1) && !solid('Shirakawago', bx + 7, by + 1), 'the bridgeheads are open');
        assert.ok(sprites.Shirakawago['shirakawa-gassho_0_0'].length + sprites.Shirakawago['shirakawa-gassho-small_0_0'].length >= 4, 'gassho farmhouses');
        assert.ok(sprites.Shirakawago['shirakawa-paddy_0_0'].length >= 40 && sprites.Shirakawago['shirakawa-peak_0_0'].length >= 3, 'paddies and peaks');
        assert.ok(Object.keys(sprites.Shirakawago).some((k) => k.startsWith('sendai-maple')) && sprites.Shirakawago['hokuriku-ginkgo_0_0'], 'autumn colour');
        // the viewpoint is up a flight of steps
        const stairs = Object.entries(layer('Shirakawago', 'Over Floor')).filter(([, t]) => name(t).startsWith('castle-stairs')).map(([xy]) => Number(xy.split(',')[1]));
        const [, ly] = at('Shirakawago', 'shirakawa-lookout_0_0');
        assert.ok(new Set(stairs).size >= 4 && Math.min(...stairs) >= ly, 'a flight of steps up to the viewpoint');

        const sea = layer('Toyama', 'Water'), [tw] = size('Toyama');
        const room = cfg.rooms.Toyama, w = room.waterways[0];
        assert.strictEqual(room.waterways.length, 1);
        assert.deepStrictEqual([w.axis, w.to], ['h', tw - 1], 'the lane runs off the east edge: boats sail in and out there');
        for (let x = w.from; x <= w.to; x++) for (let y = w.row; y < w.row + w.rows; y++) {
            assert.strictEqual(name(sea[`${x},${y}`]), 'pond-autotile_center', `lane cell ${x},${y} is not open water`);
        }
        for (const xy of Object.keys(sea)) assert.ok(xy in layer('Toyama', 'Colliders'), `Toyama water cell ${xy} is walkable`);
        const [px, py] = at('Toyama', 'toyama-port-tower_0_0');
        assert.ok(name(sea[`${px + 1},${py + 3}`]).startsWith('pond-autotile_') && !name(sea[`${px + 1},${py + 6}`]), 'the port tower stands on the quay, the sea behind it');
        const rails = sprites.Toyama['toyama-tram-rail_0_0'], [trx, try_] = at('Toyama', 'toyama-tram_0_0');
        assert.ok(rails.length >= 20 && rails.every(([, y]) => y === try_ + 1), 'the tram stands on its rails');
        assert.ok(Math.abs(at('Toyama', 'toyama-tram-stop_0_0')[0] - trx) <= 2, 'the tram is at its stop');
    });

    test('Hokuriku stands north-west of Tokyo, clear of every other map in devhouse.world, and is on the world map (#68)', () => {
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8')).maps;
        const key = (m) => path.basename(m.fileName, '.tmj');
        const mine = world.filter((m) => DISTRICTS.map((d) => d.toLowerCase()).includes(key(m)));
        assert.strictEqual(mine.length, 3, 'the three maps are not all in devhouse.world');
        const box = { x: Math.min(...mine.map((m) => m.x)), y: Math.min(...mine.map((m) => m.y)) };
        box.width = Math.max(...mine.map((m) => m.x + m.width)) - box.x;
        box.height = Math.max(...mine.map((m) => m.y + m.height)) - box.y;
        const apart = (a, b) => a.x + a.width <= b.x || b.x + b.width <= a.x || a.y + a.height <= b.y || b.y + b.height <= a.y;
        // the Map draws the city over its whole box, woods included: nothing else may sit in it
        for (const m of world) if (!mine.includes(m)) assert.ok(apart(box, m), `${key(m)} is inside Hokuriku's box`);
        const mid = (m) => [m.x + m.width / 2, m.y + m.height / 2];
        const tokyo = world.find((m) => key(m) === 'tokyo'), sendai = world.find((m) => key(m) === 'sendai');
        assert.ok(mid(box)[0] < tokyo.x && mid(box)[1] < tokyo.y, 'Hokuriku is north-west of Tokyo');
        assert.ok(box.x + box.width <= sendai.x && box.y < sendai.y + sendai.height && box.y + box.height > sendai.y, 'west of Sendai, in its band of latitude');
        // Toyama is the coast (north-east), Shirakawa-go inland to its south, Kanazawa to the west
        const [k, s, t] = DISTRICTS.map((d) => mid(mine.find((m) => key(m) === d.toLowerCase())));
        assert.ok(k[0] < s[0] && k[0] < t[0] && t[1] < s[1], 'Kanazawa west; Toyama north of Shirakawa-go');
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        for (const d of DISTRICTS) assert.deepStrictEqual(map.rooms[d] && map.rooms[d].cells, size(d), `world-map.json has no ${d}: run make_worldmap.py`);
    });

    test('the Map has a dot for each Hokuriku town, labelled as the HUD names it: Shirakawa-go, not its key (#68)', () => {
        // the Map is a map of Japan (#211): its labels are config `places`, tested in japan-map.test.js. What
        // Hokuriku owes it: an entry per district, keyed by the room, whose label is the room's display name
        for (const d of DISTRICTS) {
            const place = cfg.places[d];
            assert.ok(place && Array.isArray(place.geo), `config.places has no ${d}`);
            assert.strictEqual(place.label, cfg.rooms[d].name, `${d}: the Map and the HUD name it differently`);
        }
        assert.strictEqual(cfg.places.Shirakawago.label, 'Shirakawa-go');
        assert.ok(!cfg.places.HokurikuCity, 'the region is three towns on the map, not one dot');
        // debug map travel lands on open ground in each: outside Kanazawa Station, and for the two towns with
        // no station on the road in from the town before (Places.arrival)
        const P = game('Places');
        for (const d of DISTRICTS) {
            const to = P.arrival(cfg, d);
            assert.ok(to && to.room === d, `${d} has no arrival cell`);
            assert.ok(`${to.x},${to.y}` in layer(d, 'Floor') && !solid(d, to.x, to.y), `${d}: ${to.x},${to.y} cannot be stood on`);
        }
        // west to east as in Japan: Kanazawa, Shirakawa-go, Toyama; Toyama the furthest north, Shirakawa-go south
        const geo = (d) => cfg.places[d].geo;
        assert.ok(geo('Kanazawa')[0] < geo('Shirakawago')[0] && geo('Shirakawago')[0] < geo('Toyama')[0]);
        assert.ok(geo('Toyama')[1] > geo('Kanazawa')[1] && geo('Kanazawa')[1] > geo('Shirakawago')[1]);
    });

    test('the Toyama, Shirakawa-go and Kanazawa posts stand at the spot each is about (#68)', () => {
        const where = {};                                 // 'Name date' -> 'Room x,y'
        for (const [key, r] of Object.entries(cfg.rooms)) {
            for (const npc of r.npcs || []) {
                for (const [date, s] of Object.entries(npc.states || {})) {
                    if (s.present !== false && 'gridX' in s && date >= '2025-11-02' && date <= '2025-11-09') where[`${npc.name} ${date}`] = `${key} ${s.gridX},${s.gridY} ${s.photo}`;
                }
            }
        }
        const near = (who, post, room, sprite, reachN = 3) => {
            const [room_, cell, photo] = (where[who] || '').split(' ');
            assert.strictEqual(room_, room, `${who} (post ${post}) is in ${room_ || 'no room'}`);
            assert.strictEqual(photo, String(post), `${who}: the state is not post ${post}'s`);
            const [x, y] = cell.split(',').map(Number), [sx, sy] = at(room, sprite), [w, h] = cells(sprite);
            const dx = Math.max(sx - x, 0, x - (sx + w - 1)), dy = Math.max(sy - y, 0, y - (sy + h - 1));
            assert.ok(dx + dy <= reachN, `${who} at ${cell} is not at ${sprite} (${sx},${sy})`);
            assert.ok(!solid(room, x, y), `${who} stands on a solid cell`);
        };
        near('Damian 2025-11-02', 576, 'Toyama', 'toyama-glass-museum_0_0');       // "Glass museum was gorgeous"
        near('Julia 2025-11-03', 583, 'Toyama', 'toyama-tram-stop_0_0');           // "Glass museum by tram"
        near('Damian 2025-11-03', 610, 'Shirakawago', 'shirakawa-bridge_0_0', 4);  // "a genuinely scary bridge"
        near('Julia 2025-11-04', 611, 'Toyama', 'toyama-port-tower_0_0');          // "climbed a tower ... ocean on the other"
        near('Julia 2025-11-05', 631, 'Shirakawago', 'shirakawa-lookout_0_0');     // the mountains, the snow on the peaks
        near('Damian 2025-11-05', 635, 'Kanazawa', 'kanazawa-whisky-bar_0_0');     // "ended the night with whiskey at a bar"
        near('Julia 2025-11-06', 653, 'Kanazawa', 'kanazawa-whisky-bar_0_0');      // "ended up at a whiskey bar"
        near('Damian 2025-11-06', 652, 'Kanazawa', 'sendai-gate_0_0', 4);          // "started the day in Nagamachi"
        near('Bailey 2025-11-06', 662, 'Kanazawa', 'kanazawa-ishikawa-gate_0_0');  // "Kanazawa Castle grounds were huge"
        near('Julia 2025-11-07', 677, 'Kanazawa', 'kanazawa-kotoji_0_0');          // "all gardens and rebuilt halls"
        near('Damian 2025-11-07', 669, 'Kanazawa', 'kanazawa-chaya-a_0_0');        // Higashi Chaya
        near('Julia 2025-11-08', 686, 'Kanazawa', 'seven-eleven_0_0');             // "a berry smoothie from 711"
        near('Bailey 2025-11-09', 707, 'Kanazawa', 'shrine-building_0_0');         // "this forest full of shrines"
        // nobody's wander (a box of npcWanderRadius cells round where they stand) reaches the deck of the
        // suspension bridge: it is one cell wide and the only way over the river, so a wanderer on it shuts the road
        const R = cfg.game.npcWanderRadius, [bx, by] = at('Shirakawago', 'shirakawa-bridge_0_0');
        for (const [who, at_] of Object.entries(where)) {
            const [room_, cell] = at_.split(' ');
            if (room_ !== 'Shirakawago') continue;
            const [x, y] = cell.split(',').map(Number);
            assert.ok(Math.abs(y - (by + 1)) > R || x - R > bx + 7 || x + R < bx, `${who} at ${cell} can wander onto the bridge deck`);
        }
        // 642 is the train ride to Kanazawa, and ends there: Kanazawa's platform, not Tokyo's
        assert.ok((where['Bailey 2025-11-05'] || '').startsWith('KanazawaStation '), where['Bailey 2025-11-05']);
        assert.ok(where['Bailey 2025-11-05'].endsWith(' 642'));
        // nobody of those days is left in a made-up room or on Tokyo's platform
        for (const [who, at_] of Object.entries(where)) {
            if (/^Damian 2025-11-0[2-7]|^Julia 2025-11-0[3-8]|^Bailey 2025-11-0[5-69]/.test(who)) {       // (Julia's 2 Nov post is Karuizawa's)
                assert.ok(/^(Kanazawa|KanazawaStation|Shirakawago|Toyama) /.test(at_), `${who} is still in ${at_}`);
            }
        }
    });
};
