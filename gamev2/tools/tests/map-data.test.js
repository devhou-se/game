module.exports = ({ test, assert, fs, path, GV2, load, game, worldWith, require }) => {
    test('every room has a display name for the HUD, and no interior shows its key', () => {
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        for (const [key, room] of Object.entries(rooms)) {
            assert.ok(room.name && room.name.trim(), `${key} has no name`);
            if (/^Konbini|Station$/.test(key)) assert.notStrictEqual(room.name, key, `${key} shows its room key`);
        }
        assert.strictEqual(rooms.KonbiniSapporo1.name, '7-Eleven · Sapporo');
        assert.strictEqual(rooms.SapporoStation.name, 'Sapporo Station');
        assert.strictEqual(rooms.TokyoStation.name, 'Tokyo Station');
    });

    test('a snowed-in town lays no grass-fringed path: gravel and dirt use their snow families', () => {
        // gravel-autotile / dirt-outside-autotile edges carry a green fringe (tools/generate_hokkaido.py SNOW_FAMILIES)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const bad = [], snowTowns = [];
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const floor = (room.layers || []).find((l) => l.name === 'Floor');
            const cells = Object.entries((floor && floor.tiles) || {});
            if (!cells.some(([, t]) => name(t).startsWith('snow-autotile'))) continue;
            snowTowns.push(key);
            for (const [xy, t] of cells) {
                if (/^(gravel|dirt-outside)-autotile_/.test(name(t))) bad.push(`${key} @${xy} ${name(t)}`);
            }
        }
        assert.deepStrictEqual(bad, []);
        for (const town of ['Yukimura', 'Sapporo', 'Asahikawa']) {
            assert.ok(snowTowns.includes(town), `${town} is no longer on snow ground`);
            const floor = cfg.rooms[town].layers.find((l) => l.name === 'Floor');
            assert.ok(Object.values(floor.tiles).some((t) => name(t).startsWith('gravel-snow-autotile_')), `${town} has no rail-corridor gravel`);
        }
        for (const role of ['center', 'edge-n', 'edge-s', 'edge-e', 'edge-w', 'corner-ne', 'corner-nw', 'corner-se', 'corner-sw']) {
            const k = `gravel-snow-autotile_${role}`;
            assert.ok(k in cfg.spriteMetadata, `${k} is not in spriteMetadata (not loaded at boot)`);
            assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', k + '.png')), `${k}.png is missing`);
        }
    });

    test('every shelf, cooler and till in a konbini or Don Takote can be bumped from a free cell the door leads to', () => {
        // #152: a fixture is used from the cell below it (the till, against the front wall, from any side)
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const sizeOf = (key) => {
            const b = fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'));
            return [Math.max(1, Math.round(b.readUInt32BE(16) / 64)), Math.max(1, Math.round(b.readUInt32BE(20) / 64))];
        };
        const inside = (poly, px, py) => {
            let hit = false;
            for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
                const [xi, yi] = poly[i], [xj, yj] = poly[j];
                if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) hit = !hit;
            }
            return hit;
        };
        const bad = [];
        let stores = 0, fixtures = 0;
        for (const [key, room] of Object.entries(cfg.rooms)) {
            if (!/^(Konbini|DonTakote)/.test(key)) continue;
            stores++;
            const layers = room.layers.map((l) => ({ name: l.name, collision: l.collision,
                tiles: Object.fromEntries(Object.entries(l.tiles).map(([xy, t]) => [xy, name(t)])) }));
            const solid = new Set(layers.filter((l) => l.collision).flatMap((l) => Object.keys(l.tiles)));
            const open = (x, y) => !solid.has(`${x},${y}`) && inside(room.boundary, x + 0.5, y + 0.5);
            const reach = new Set(), todo = room.transporters.map((t) => [t.gridX, t.gridY]);
            todo.forEach((c) => reach.add(c.join()));
            while (todo.length) {
                const [x, y] = todo.pop();
                for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                    if (open(nx, ny) && !reach.has(`${nx},${ny}`)) { reach.add(`${nx},${ny}`); todo.push([nx, ny]); }
                }
            }
            for (const f of game('Interactions.all')({ layers }, room, { sizeOf, group: 'shop' })) {
                fixtures++;
                if (f.kind === 'counter') {
                    const sides = [];
                    for (let a = 0; a < f.w; a++) sides.push([f.x + a, f.y - 1], [f.x + a, f.y + f.h]);
                    sides.push([f.x - 1, f.y], [f.x + f.w, f.y]);
                    if (!sides.some(([x, y]) => reach.has(`${x},${y}`))) bad.push(`${key}: till @${f.x},${f.y}`);
                    continue;
                }
                for (let a = 0; a < f.w; a++) {
                    if (!reach.has(`${f.x + a},${f.y + f.h}`)) bad.push(`${key}: ${f.key} @${f.x + a},${f.y} has no free cell in front`);
                }
            }
        }
        assert.ok(stores >= 13 && fixtures > 150, `expected every store and its fixtures, saw ${stores} / ${fixtures}`);
        assert.deepStrictEqual(bad, []);
    });

    test('no store has floor its furniture seals off (#182)', () => {
        const { world } = worldWith(true);
        const stores = Object.keys(world.config.rooms).filter((k) => /^(Konbini|DonTakote|Izakaya)/.test(k));
        assert.ok(stores.length >= 14, stores.join());
        for (const k of stores) assert.strictEqual(JSON.stringify(world.lint(k).errors), '{}', k);
        // the corner filler stands on the back row, never one row below it with the corner cell boxed in
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        let dispensers = 0;
        for (const k of stores.filter((k) => k.startsWith('Konbini'))) {
            const room = cfg.rooms[k], top = Math.min(...room.boundary.map((p) => p[1]));
            const layer = room.layers.find((l) => l.name === 'Collidables').tiles;
            for (const [xy, t] of Object.entries(layer)) {
                if (cfg.tilePalette[t] !== 'office-watercooler_0_0') continue;
                dispensers++;
                const y = Number(xy.split(',')[1]), bottom = Math.max(...room.boundary.map((p) => p[1])) - 2;
                assert.ok(y === top || y === bottom, `${k}: water dispenser at ${xy} is on neither the back row (${top}) nor the counter row (${bottom})`);
            }
        }
        assert.ok(dispensers >= 5, `saw ${dispensers} water dispensers`);
        // ...and the dispenser leaves no one-cell nook beside it on the back row either (between it
        // and the coolers, or between it and the side wall)
        for (const k of stores.filter((k) => k.startsWith('Konbini'))) {
            const room = cfg.rooms[k], xs = room.boundary.map((p) => p[0]);
            const top = Math.min(...room.boundary.map((p) => p[1])), x0 = Math.min(...xs), x1 = Math.max(...xs) - 1;
            const layer = room.layers.find((l) => l.name === 'Collidables').tiles;
            const free = (x) => x >= x0 && x <= x1 && !(`${x},${top}` in layer);
            const dispenser = (x) => cfg.tilePalette[layer[`${x},${top}`]] === 'office-watercooler_0_0';
            for (let x = x0; x <= x1; x++) {
                if (!free(x) || !(dispenser(x - 1) || dispenser(x + 1))) continue;
                assert.ok(free(x - 1) || free(x + 1), `${k}: back-row cell ${x},${top} is a one-cell nook beside the dispenser`);
            }
        }
    });

    test('the retired office-bin sprite is gone, and nothing still points at its palette slot', () => {
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const key = 'office-bin_0_0';
        assert.ok(!(key in cfg.spriteMetadata), 'still in spriteMetadata (loaded at boot, offered in the editor)');
        assert.ok(!(key in (cfg.tileNames || {})), 'still in tileNames');
        assert.ok(!fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), 'the PNG is still there');
        // tilePalette is positional: the slot stays so every later index keeps its meaning
        const slot = cfg.tilePalette.indexOf(key);
        assert.ok(slot >= 0, 'the palette slot was removed: every later tile index has shifted');
        for (const [name, room] of Object.entries(cfg.rooms)) {
            for (const layer of room.layers || []) {
                for (const [xy, t] of Object.entries(layer.tiles || {})) {
                    assert.ok(t !== slot && t !== key, `${name} ${layer.name} @${xy} places the retired ${key}`);
                }
            }
        }
    });

    test('the konbini drinks cooler fills its two cells and keeps its size and anchor', () => {
        const png = require('./png');
        const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'office-fridge_0_0.png')));
        assert.deepStrictEqual([width, height], [64, 128]);
        let x0 = width, x1 = -1, y0 = height, y1 = -1, glass = 0;
        for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
            const p = (y * width + x) * 4;
            if (data[p + 3] === 0) continue;
            x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
            if (data[p] === 0xb3 && data[p + 1] === 0xe5 && data[p + 2] === 0xfc) glass++;      // the lit interior
        }
        assert.deepStrictEqual([x0, x1, y0, y1], [0, 63, 0, 127], 'art reaches every edge of the 1x2 footprint');
        assert.ok(glass > 500, 'a lit glass door, not a blank cabinet');
        const meta = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).spriteMetadata['office-fridge_0_0'];
        assert.deepStrictEqual([meta.anchorX, meta.anchorY], [0.5, 0.25]);
    });

    test('the train-only towns stand clear of the city and its woodland on the world map (#174)', () => {
        // the Map draws a stitched city over its whole bounding box, woods included: a town placed
        // inside that box showed as a clearing in Tokyo's woods, though you cannot walk to it
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        const placed = Object.fromEntries(world.maps.map((m) => [path.basename(m.fileName, '.tmj'), m]));
        for (const [key, city] of Object.entries(config.cities)) {
            const members = city.rooms.map((r) => r.room);
            for (const [name, rects] of [['world-map.json', map.rooms],
                ['devhouse.world', Object.fromEntries(Object.keys(map.rooms).map((k) => {
                    const m = placed[k.toLowerCase()];
                    return [k, { x: m.x, y: m.y, w: m.width, h: m.height }];
                }))]]) {
                const box = members.map((k) => rects[k]);
                const x0 = Math.min(...box.map((r) => r.x)), y0 = Math.min(...box.map((r) => r.y));
                const x1 = Math.max(...box.map((r) => r.x + r.w)), y1 = Math.max(...box.map((r) => r.y + r.h));
                const inside = Object.keys(rects).filter((k) => !members.includes(k)).filter((k) => {
                    const r = rects[k];
                    return r.x < x1 - 0.5 && r.x + r.w > x0 + 0.5 && r.y < y1 - 0.5 && r.y + r.h > y0 + 0.5;
                });
                assert.deepStrictEqual(inside, [], `${name}: inside ${key}'s box`);
            }
        }
        // and the map image has room for them: the JSON's rects all lie on it
        for (const [k, r] of Object.entries(map.rooms)) {
            assert.ok(r.x >= 0 && r.y >= 0 && r.x + r.w <= map.width + 0.5 && r.y + r.h <= map.height + 0.5, k);
        }
    });

    test('the world file is laid out like Japan: Hokkaido at the top, Osaka south-west of Tokyo, no two maps overlapping (#68)', () => {
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8'));
        const at = Object.fromEntries(world.maps.map((m) => [path.basename(m.fileName, '.tmj'), m]));
        const mid = (k) => ({ x: at[k].x + at[k].width / 2, y: at[k].y + at[k].height / 2 });
        // north is up: Asahikawa is north-east of Sapporo, and all of Hokkaido is north of the whole Tokyo city
        const cityTop = Math.min(...config.cities.TokyoCity.rooms.map((r) => at[r.room.toLowerCase()].y));
        for (const k of ['sapporo', 'asahikawa']) assert.ok(at[k].y + at[k].height <= cityTop, `${k} is north of Tokyo`);
        assert.ok(mid('asahikawa').x > mid('sapporo').x && mid('asahikawa').y < mid('sapporo').y, 'Asahikawa is north-east of Sapporo');
        assert.ok(Math.abs(mid('sapporo').x - mid('tokyo').x) < at.tokyo.width / 2, 'Sapporo is about due north of Tokyo');
        // Osaka is west of every Tokyo district and south of Tokyo itself, further west than it is south
        const cityWest = Math.min(...config.cities.TokyoCity.rooms.map((r) => at[r.room.toLowerCase()].x));
        assert.ok(at.osaka.x + at.osaka.width <= cityWest, 'Osaka is west of the Tokyo city');
        assert.ok(mid('osaka').y > mid('tokyo').y, 'and south of Tokyo');
        assert.ok(mid('tokyo').x - mid('osaka').x > mid('osaka').y - mid('tokyo').y, 'west-south-west, not south');
        // the detached towns (the made-up ones included, while they last) touch nothing
        const maps = Object.keys(at), inCity = new Set(config.cities.TokyoCity.rooms.map((r) => r.room.toLowerCase()));
        for (const a of maps) for (const b of maps) {
            if (a >= b || (inCity.has(a) && inCity.has(b))) continue;
            const A = at[a], B = at[b];
            assert.ok(A.x + A.width <= B.x || B.x + B.width <= A.x || A.y + A.height <= B.y || B.y + B.height <= A.y, `${a} and ${b} overlap`);
        }
    });
};
