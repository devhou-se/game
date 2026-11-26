// Fukuoka (issue #67): the town, its station ("Hakata"), its konbini, the ramen river street, the
// landmarks and the eight posts that were re-homed there. All of it is data the generators write
// (tools/generate_fukuoka.py, generate_fukuoka_art.py, generate_stations.py, generate_konbinis.py).
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const room = cfg.rooms.Fukuoka;
    const layer = (n, r = room) => ((r.layers.find((l) => l.name === n) || {}).tiles) || {};
    const W = room.worldWidth / 64, H = room.worldHeight / 64;
    const solid = (x, y) => `${x},${y}` in layer('Colliders');
    // every tile of the room as [x, y, key, layer]
    const placed = [];
    for (const l of room.layers) {
        for (const [xy, t] of Object.entries(l.tiles)) placed.push([...xy.split(',').map(Number), name(t), l.name]);
    }
    const where = (re) => placed.filter(([, , k]) => re.test(k));
    const sizeOf = (key) => {
        const b = fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
        return [b.readUInt32BE(16) / 64, b.readUInt32BE(20) / 64];
    };
    // cells that can be walked to from where the station door puts you
    const reach = (() => {
        const start = cfg.rooms.FukuokaStation.transporters[0];
        const seen = new Set([`${start.targetX},${start.targetY}`]), todo = [[start.targetX, start.targetY]];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const nx = x + dx, ny = y + dy, k = `${nx},${ny}`;
                if (nx < 0 || ny < 0 || nx >= W || ny >= H || seen.has(k) || solid(nx, ny)) continue;
                seen.add(k); todo.push([nx, ny]);
            }
        }
        return seen;
    })();
    const reachable = (x, y) => reach.has(`${x},${y}`);

    test('Fukuoka: Hakata station is a main-line stop after the existing stations, and its doors pair up', () => {
        const st = cfg.stations.FukuokaStation;
        assert.strictEqual(st.label, 'Hakata');
        assert.strictEqual(st.town, 'Fukuoka');
        assert.strictEqual(st.train, 'train-orange');
        assert.ok(!('parent' in st), 'a city, not a day trip');
        for (const k of ['TokyoStation', 'InakaStation', 'YukimuraStation', 'OsakaStation', 'SapporoStation', 'AsahikawaStation']) {
            assert.ok(st.order > cfg.stations[k].order, `Hakata is listed after ${k}`);
        }
        assert.strictEqual(cfg.rooms.FukuokaStation.name, 'Hakata Station');
        // town -> station: the station house door; station -> town: the cell in front of that door
        const door = room.transporters.find((t) => t.targetRoom === 'FukuokaStation');
        assert.ok(door && door.hidden, 'the station house door is a hidden transporter');
        assert.ok(where(/^building-entrance-1/).some(([x, y]) => x + 1 === door.gridX && y === door.gridY), 'on the station house doorway');
        for (const t of cfg.rooms.FukuokaStation.transporters) {
            assert.strictEqual(t.targetRoom, 'Fukuoka');
            assert.deepStrictEqual([t.targetX, t.targetY], [door.gridX, door.gridY + 1]);
        }
        assert.ok(!solid(door.gridX, door.gridY + 1) && !room.transporters.some((t) => t.gridX === door.gridX && t.gridY === door.gridY + 1),
            'you arrive on a free cell that is not a door');
        // the only ways out of town are the station and the konbini; every other door is a house's own front
        // door (#208): hidden, on the doorway of a house that stands there, into a House room of this town
        const isHouse = (t) => ((cfg.rooms[t.targetRoom] || {}).house || {}).host === 'Fukuoka';
        assert.deepStrictEqual(room.transporters.filter((t) => !isHouse(t)).map((t) => t.targetRoom).sort(), ['FukuokaStation', 'KonbiniFukuoka1']);
        const homes = room.transporters.filter(isHouse);
        assert.deepStrictEqual(homes.map((t) => t.targetRoom).sort(), ['HouseFukuoka1', 'HouseFukuoka2', 'HouseFukuoka3', 'HouseFukuoka4']);
        for (const t of homes) {
            assert.ok(t.hidden && /^HouseFukuoka\d+$/.test(t.targetRoom), `${t.targetRoom}: a hidden door`);
            assert.ok(where(/^building-entrance-[123]_/).some(([x, y]) => x + 1 === t.gridX && y === t.gridY) ||
                where(/^machiya-/).some(([x, y]) => x + 2 === t.gridX && y + 4 === t.gridY), `${t.targetRoom}: on a house's doorway`);
            assert.ok(reachable(t.gridX, t.gridY + 1), `${t.targetRoom}: the cell in front of its door can be walked to`);
        }
    });

    test('Fukuoka: the 7-Eleven on the downtown street has its own interior, wired both ways', () => {
        const store = cfg.rooms.KonbiniFukuoka1;
        assert.ok(store && store.interior, 'KonbiniFukuoka1 is an interior');
        assert.strictEqual(store.name, '7-Eleven · Fukuoka');
        const [[sx, sy]] = where(/^seven-eleven_/);
        const door = room.transporters.find((t) => t.targetRoom === 'KonbiniFukuoka1');
        assert.deepStrictEqual([door.gridX, door.gridY], [sx + 1, sy + 3], 'the door is the store front\'s middle cell');
        assert.ok(!solid(door.gridX, door.gridY) && reachable(door.gridX, door.gridY + 1), 'and can be walked into from the pavement');
        for (const t of store.transporters) {
            assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Fukuoka', door.gridX, door.gridY + 1]);
        }
        // the pavement it opens onto is the downtown street's: asphalt two rows on
        assert.ok(/^road-/.test(name(layer('Floor')[`${door.gridX},${door.gridY + 2}`])), 'the store fronts the street');
        assert.ok(where(/vending-machine-top/).length >= 6, 'vending machines about town');
    });

    test('Fukuoka: the ramen river street is a row of yatai with lanterns between them, facing the river', () => {
        const stalls = where(/^yatai-(ramen|yakitori|oden)_/);
        assert.ok(stalls.length >= 10, `night-market scale: ${stalls.length} stalls`);
        assert.strictEqual(new Set(stalls.map(([, y]) => y)).size, 1, 'one row');
        assert.deepStrictEqual([...new Set(stalls.map(([, , k]) => k.split('_')[0]))].sort(), ['yatai-oden', 'yatai-ramen', 'yatai-yakitori']);
        const y0 = stalls[0][1], river = room.waterways[0];
        assert.ok(river.row - (y0 + 3) >= 2 && river.row - (y0 + 3) <= 4, 'the stalls stand a promenade back from the water');
        for (const [x, y, k] of stalls) {
            assert.deepStrictEqual(sizeOf(k), [3, 3], k);
            for (let dx = 0; dx < 3; dx++) {
                assert.ok(solid(x + dx, y + 1) && solid(x + dx, y + 2), `${k} @${x},${y}: the cart and stools are solid`);
                assert.ok(reachable(x + dx, y + 3), `${k} @${x},${y}: you can walk up to the stools at ${x + dx},${y + 3}`);
                // nobody gets behind a stall's roof: its roof row is closed off
                assert.ok(!reachable(x + dx, y), `${k} @${x},${y}: the roof row can be walked into at ${x + dx},${y}`);
            }
        }
        // lanterns: the posts between the stalls are lit at night by the rule every lantern is lit by
        const posts = where(/^yatai-lanterns_/);
        assert.ok(posts.length >= 8, `${posts.length} lantern posts`);
        const lit = /\/([^/]*lamp-post[^/]*)\/\.test\(key\)/.exec(fs.readFileSync(path.join(GV2, 'src', 'DayNight.js'), 'utf8'));
        assert.ok(lit, 'DayNight.buildGlows still picks its lamps by tile key');
        const glows = new RegExp(lit[1]);
        assert.ok(glows.test('yatai-lanterns_0_0'), 'a yatai lantern post glows at night');
        for (const [x, y] of posts) {
            assert.strictEqual(y, y0 + 1, 'the lanterns hang at the stalls\' noren');
            assert.ok(solid(x, y + 1) && !stalls.some(([sx]) => x >= sx && x < sx + 3), `post @${x},${y} stands between stalls`);
        }
        assert.ok(where(/lamp-post/).filter(([, y]) => y === river.row - 1).length >= 6, 'lamps along the bank');
    });

    test('Fukuoka: the river is one declared waterway from the beach to the east edge, open except under the bridge', () => {
        assert.strictEqual(room.waterways.length, 1);
        const w = room.waterways[0];
        assert.strictEqual(w.axis, 'h');
        assert.strictEqual(w.rows, 3);
        assert.strictEqual(w.to, W - 1, 'the east end is on the map edge: boats sail in and out there');
        assert.strictEqual(w.under.length, 1);
        const [u0, u1] = w.under[0];
        assert.ok(u1 - u0 + 1 >= 4, 'the deck is at least four cells wide');
        const water = layer('Water'), floor = layer('Floor'), flat = layer('Non-Collidables');
        for (let x = w.from; x <= w.to; x++) {
            for (let i = 0; i < w.rows; i++) {
                const at = `${x},${w.row + i}`;
                if (x >= u0 && x <= u1) {
                    assert.ok(!(at in water) && !solid(x, w.row + i) && /brick/.test(name(floor[at])), `deck cell ${at} is walkable paving`);
                } else {
                    assert.strictEqual(name(water[at]), `pond-autotile_${['edge-n', 'center', 'edge-s'][i]}`, at);
                    assert.ok(solid(x, w.row + i), `water ${at} is solid`);
                }
            }
        }
        // a boat needs every cross-section to be the same rimmed channel, starting with the one it is measured on
        assert.strictEqual(name(water[`${w.from},${w.row}`]), 'pond-autotile_edge-n');
        // the deck is dressed as a bridge: parapets on its outer cells, its shadow on the water beside it
        for (let i = 0; i < w.rows; i++) {
            assert.strictEqual(name(flat[`${u0},${w.row + i}`]), 'bridge-parapet-w_0_0');
            assert.strictEqual(name(flat[`${u1},${w.row + i}`]), 'bridge-parapet-e_0_0');
            assert.strictEqual(name(flat[`${u0 - 1},${w.row + i}`]), 'bridge-shade-w_0_0');
            assert.strictEqual(name(flat[`${u1 + 1},${w.row + i}`]), 'bridge-shade-e_0_0');
        }
        // both banks are joined by it and by nothing else
        assert.ok(reachable(u0, w.row - 1) && reachable(u0, w.row + w.rows), 'the bridge joins the banks');
    });

    test('Fukuoka: the landmarks stand where the town says, with real art, and can be walked up to', () => {
        const one = (re) => { const hits = where(re); assert.strictEqual(hits.length, 1, String(re)); return hits[0]; };
        const river = room.waterways[0];
        // Fukuoka Tower by the water: the sea is the west edge, the tower within a few cells of the beach
        const [tx, ty, tkey] = one(/^fukuoka-tower_/);
        assert.deepStrictEqual(sizeOf(tkey), [4, 12]);
        for (let y = 8; y < H; y++) assert.ok(solid(0, y) && name(layer('Water')[`0,${y}`]) === 'pond-autotile_center', `sea at 0,${y}`);
        const shore = where(/^beach-shore-e_/);
        assert.ok(shore.length > 40 && shore.every(([x, y]) => solid(x, y)), 'a waterline down the west side');
        assert.ok(tx - shore[0][0] <= 6 && ty + 12 < river.row, 'the tower is on the shore, north of the river');
        assert.ok(where(/^sand-autotile_/).length > 100, 'Momochi beach is sand');
        assert.ok(reachable(tx, ty + 12) && reachable(tx + 1, ty + 12), 'you can stand at its foot');
        assert.strictEqual(cfg.game.lookUp.sprites['fukuoka-tower'], 0, 'the camera looks up at it');
        // Canal City and Kushida shrine between the street and the stalls
        const [cx, cy] = one(/^canal-city_/), [kx, ky] = one(/^hakata-yamakasa_/);
        const [rx, ry] = one(/^red-shrine-top_/);
        assert.ok(cy > 22 && cy + 6 < river.row && ky + 4 < river.row && ry + 8 < river.row);
        assert.ok(Math.abs(kx - (rx + 5)) <= 3, 'the Yamakasa float stands beside the shrine hall');
        assert.ok(reachable(cx + 2, cy + 6) && reachable(kx, ky + 4) && reachable(rx + 2, ry + 8));
        one(/^canal-fountain_/);
        // Dazaifu Tenmangu, south of the river: lane -> torii -> arched bridge over the pond -> hall, plum trees round it
        const [hx, hy, hkey] = one(/^dazaifu-hall_/), [bx, by, bkey] = one(/^dazaifu-bridge_/), [gx, gy] = one(/^torii-red-top_/);
        assert.ok(hy > river.row + 2, 'Dazaifu is over the river');
        assert.ok(hy < by && by < gy, 'north to south: hall, bridge, torii - a shrine is walked up to from the south');
        assert.deepStrictEqual(sizeOf(hkey), [6, 5]);
        assert.deepStrictEqual(sizeOf(bkey), [2, 4]);
        assert.strictEqual(cfg.spriteMetadata[bkey].depthBias, -200, 'the bridge lies flat: you walk on it');
        const pond = where(/^pond-autotile_/).filter(([x, y]) => y === by + 1 || y === by + 2);
        assert.ok(pond.some(([x]) => x < bx) && pond.some(([x]) => x > bx + 1), 'the bridge has pond either side');
        for (let y = by; y < by + 4; y++) for (const x of [bx, bx + 1]) assert.ok(reachable(x, y), `bridge cell ${x},${y}`);
        assert.ok(bx >= hx && bx + 1 <= hx + 5 && bx >= gx && bx + 1 <= gx + 5, 'torii, bridge and hall are on one axis');
        const plums = where(/^plum-tree_/);
        assert.ok(plums.length >= 4 && plums.every(([, y]) => y > river.row), `${plums.length} plum trees in the precinct`);
        // every Fukuoka sprite is drawn art that the game loads (not a placeholder: more than a handful of colours)
        for (const k of ['fukuoka-tower_0_0', 'yatai-ramen_0_0', 'yatai-yakitori_0_0', 'yatai-oden_0_0', 'yatai-lanterns_0_0',
            'hakata-yamakasa_0_0', 'canal-city_0_0', 'canal-fountain_0_0', 'dazaifu-hall_0_0', 'dazaifu-bridge_0_0', 'plum-tree_0_0']) {
            assert.ok(k in cfg.spriteMetadata, `${k} is not in spriteMetadata`);
            assert.ok(fs.statSync(path.join(GV2, 'assets', 'sprites', k + '.png')).size > 400, `${k}.png`);
            const [cw, ch] = sizeOf(k);
            assert.ok(Number.isInteger(cw) && Number.isInteger(ch), `${k} is cell-aligned`);
            assert.ok(Math.abs(cfg.spriteMetadata[k].anchorX - 0.5 / cw) < 1e-9 && Math.abs(cfg.spriteMetadata[k].anchorY - 0.5 / ch) < 1e-9, `${k} anchors on its top-left cell`);
        }
    });

    test('Fukuoka: its eight posts are told there, each at the place it is about, and nowhere else (#67)', () => {
        const stalls = where(/^yatai-ramen_/), [tx, ty] = where(/^fukuoka-tower_/)[0], [cx, cy] = where(/^canal-city_/)[0];
        const [kx, ky] = where(/^hakata-yamakasa_/)[0], [hx, hy] = where(/^dazaifu-hall_/)[0];
        const door = room.transporters.find((t) => t.targetRoom === 'FukuokaStation');
        const near = (x, y, ax, ay, d = 2) => Math.abs(x - ax) + Math.abs(y - ay) <= d;
        const want = {      // post id: [who, the day in Japan, where they should be standing]
            693: ['Damian', '2025-11-08', (x, y) => stalls.some(([sx, sy]) => near(x, y, sx + 1, sy + 3))],
            719: ['Julia', '2025-11-09', (x, y) => near(x, y, door.gridX + 2, door.gridY + 1)],
            712: ['Damian', '2025-11-09', (x, y) => near(x, y, kx, ky + 4)],
            727: ['Julia', '2025-11-10', (x, y) => near(x, y, cx + 2, cy + 6)],
            731: ['Damian', '2025-11-10', (x, y) => near(x, y, tx, ty + 12)],
            740: ['Damian', '2025-11-11', (x, y) => near(x, y, hx + 1, hy + 5)],
            746: ['Julia', '2025-11-12', (x, y) => near(x, y, door.gridX + 2, door.gridY + 1)],
            750: ['Bailey', '2025-11-12', (x, y) => stalls.some(([sx, sy]) => near(x, y, sx + 1, sy + 3))],
        };
        const told = {};
        for (const [key, r] of Object.entries(cfg.rooms)) {
            for (const npc of r.npcs || []) {
                for (const [date, st] of Object.entries(npc.states || {})) {
                    for (const p of st.posts || []) (told[p.id] = told[p.id] || []).push({ room: key, npc: npc.name, date, st });
                }
            }
        }
        for (const [id, [who, date, placeOk]] of Object.entries(want)) {
            assert.strictEqual((told[id] || []).length, 1, `post ${id} is told once`);
            const t = told[id][0];
            assert.deepStrictEqual([t.room, t.npc, t.date], ['Fukuoka', who, date], `post ${id}`);
            assert.strictEqual(t.st.present, true);
            assert.ok(placeOk(t.st.gridX, t.st.gridY), `post ${id}: ${who} stands at ${t.st.gridX},${t.st.gridY}`);
            assert.ok(reachable(t.st.gridX, t.st.gridY), `post ${id}: ${t.st.gridX},${t.st.gridY} is open ground you can walk to`);
            assert.ok(!room.transporters.some((d) => Math.abs(d.gridX - t.st.gridX) + Math.abs(d.gridY - t.st.gridY) <= 1), `post ${id} is not at a doorway`);
            assert.ok(t.st.dialogue && t.st.dialogue.length, `post ${id} kept its dialogue`);
            // that day they are nowhere else
            for (const [key, r] of Object.entries(cfg.rooms)) {
                if (key === 'Fukuoka') continue;
                const other = (r.npcs || []).find((n) => n.name === who);
                const st = other && (other.states || {})[date];
                assert.ok(!st || st.present === false, `${who} is also in ${key} on ${date}`);
            }
        }
        // nobody stands on a Fukuoka visitor's cell under a roof or canopy
        const tops = new Set();
        for (const [x, y, k, l] of placed) {
            if (l !== 'Tops') continue;
            const [w, h] = sizeOf(k);
            for (let dx = 0; dx < w; dx++) for (let dy = 0; dy < h; dy++) tops.add(`${x + dx},${y + dy}`);
        }
        for (const id of Object.keys(want)) assert.ok(!tops.has(`${told[id][0].st.gridX},${told[id][0].st.gridY}`), `post ${id} stands under a canopy`);
    });

    test('Fukuoka sits far south-west of Osaka in the world file, clear of every map, and is on the Map', () => {
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        const at = Object.fromEntries(world.maps.map((m) => [path.basename(m.fileName, '.tmj'), m]));
        const f = at.fukuoka, o = at.osaka;
        assert.ok(f, 'fukuoka.tmj is in devhouse.world');
        assert.deepStrictEqual([f.width, f.height], [room.worldWidth, room.worldHeight]);
        assert.ok(f.x + f.width <= o.x - 320, 'west of Osaka, with a gap');
        assert.ok(f.y + f.height / 2 > o.y + o.height / 2, 'and south of it');
        for (const [k, m] of Object.entries(at)) {
            if (k === 'fukuoka') continue;
            assert.ok(f.x + f.width <= m.x, `Fukuoka is west of ${k}`);
        }
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        const r = map.rooms.Fukuoka;
        assert.ok(r, 'the Map has a Fukuoka rect (labels, the You marker and map-click travel use it)');
        assert.deepStrictEqual(r.cells, [W, H]);
        assert.ok(r.x >= 0 && r.y >= 0 && r.x + r.w <= map.width + 0.5 && r.y + r.h <= map.height + 0.5);
        assert.ok(r.x + r.w <= map.rooms.Osaka.x && r.y + r.h / 2 > map.rooms.Osaka.y + map.rooms.Osaka.h / 2, 'drawn south-west of Osaka');
    });
};
