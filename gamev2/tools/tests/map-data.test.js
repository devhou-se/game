module.exports = ({ test, assert, fs, path, GV2, load, game, realConfig, worldWith, require }) => {
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
        for (const town of ['Sapporo', 'Asahikawa']) {
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
        if (game('typeof Interactions') === 'undefined') load('utils/Interactions.js');   // once: other tests load it too
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
        // every 7-Eleven has its one water dispenser standing against the back wall (over the wall's
        // lower row, solid on the floor's first), and the cell under it can be walked to from the door (#221)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const konbinis = stores.filter((k) => k.startsWith('Konbini'));
        assert.ok(konbinis.length >= 13, konbinis.join());
        for (const k of konbinis) {
            // the outline takes in the back wall: the floor starts two rows under its top
            const room = cfg.rooms[k], top = Math.min(...room.boundary.map((p) => p[1])) + 2;
            const layer = room.layers.find((l) => l.name === 'Collidables').tiles;
            const solid = room.layers.find((l) => l.name === 'Colliders').tiles;
            const at = Object.keys(layer).filter((xy) => cfg.tilePalette[layer[xy]] === 'konbini-water_0_0');
            assert.strictEqual(at.length, 1, `${k}: ${at.length} water dispensers`);
            const [x, y] = at[0].split(',').map(Number);
            assert.strictEqual(y, top - 1, `${k}: the water dispenser at ${at[0]} does not stand against the back wall`);
            assert.ok(`${x},${top}` in solid && !(`${x},${top + 1}` in solid), `${k}: the dispenser's foot is solid, the cell under it free`);
            // the floor is the boundary's box above the mat row; the mat is the two exit cells
            const xs = room.boundary.map((p) => p[0]), x0 = Math.min(...xs), x1 = Math.max(...xs), mat = room.transporters[0].gridY;
            const seen = new Set(room.transporters.map((t) => `${t.gridX},${t.gridY}`)), todo = room.transporters.map((t) => [t.gridX, t.gridY]);
            while (todo.length) {
                const [cx, cy] = todo.pop();
                for (const [nx, ny] of [[cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]]) {
                    const c = `${nx},${ny}`;
                    if (seen.has(c) || c in solid || nx < x0 || nx >= x1 || ny < top || ny >= mat) continue;
                    seen.add(c); todo.push([nx, ny]);
                }
            }
            assert.ok(seen.has(`${x},${top + 1}`), `${k}: nobody can walk up to the water dispenser at ${at[0]}`);
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
            if (data[p] === 0x2c && data[p + 1] === 0x2d && data[p + 2] === 0x51) glass++;      // the pack's dark glass
        }
        assert.deepStrictEqual([x0, x1, y0, y1], [0, 63, 0, 127], 'art reaches every edge of the 1x2 footprint');
        assert.ok(glass > 500, 'a glass door, not a blank cabinet');
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

    test('Tokyo Station is solid where it stands and no further: the paving in front of its wings is walked on (#259)', () => {
        // the sprite is 41x8 cells, but only the two pavilions and the entrance come down into its bottom row:
        // the wings end in the row above. The whole rectangle was solid, so a player walking north stopped a
        // cell and a half short of a wing with nothing in the way. The forecourt gardens, lamps and vending
        // machine stand in that bottom row too and stay solid
        const png = require('./png');
        const KEY = 'tokyo-station_0_0', G = 64, room = realConfig().rooms.Palace;
        const at = Object.entries(room.layers.find((l) => l.name === 'Collidables').tiles).find(([, k]) => k === KEY)[0];
        const [sx, sy] = at.split(',').map(Number);
        const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', KEY + '.png')));
        assert.deepStrictEqual([sx, sy, width / G, height / G], [7, 2, 41, 8]);
        const art = (x, y) => {
            for (let py = (y - sy) * G; py < (y - sy + 1) * G; py++) for (let px = (x - sx) * G; px < (x - sx + 1) * G; px++) {
                if (data[(py * width + px) * 4 + 3]) return true;
            }
            return false;
        };
        const solid = new Set(room.layers.filter((l) => l.collision).flatMap((l) => Object.keys(l.tiles)));
        // something else standing in the cell: a shrub, a lamp's top, the vending machine
        const other = (xy) => room.layers.some((l) => !l.collision && l.z >= 2 && l.tiles[xy] && l.tiles[xy] !== KEY);
        const door = room.transporters.find((t) => t.targetRoom === 'TokyoStation');
        assert.deepStrictEqual([door.gridX, door.gridY], [27, 9]);
        const bottom = sy + height / G - 1, free = [], bad = [];
        for (let y = sy; y <= bottom; y++) for (let x = sx; x < sx + width / G; x++) {
            const xy = `${x},${y}`;
            if (!solid.has(xy)) {
                free.push(xy);
                if (art(x, y) && xy !== '27,9') bad.push(xy + ' is open under the station');
            } else if (y === bottom && !art(x, y) && !other(xy)) bad.push(xy + ' is solid with nothing standing on it');
        }
        assert.deepStrictEqual(bad, []);
        // the west wing either side of its pavilion, the door, and the same on the east
        const cols = [7, 8, 9, 15, 16, 17, 18, 19, 20, 21, 22, 27, 32, 33, 34, 35, 36, 37, 38, 39, 45, 46, 47];
        assert.deepStrictEqual(free, cols.map((x) => `${x},9`));
        for (const xy of ['23,9', '24,9', '25,9', '29,9', '30,9', '31,9', '29,10']) assert.ok(solid.has(xy), xy + ': the forecourt stays solid');
        // ...and a player gets onto every one of them, in the city and with the districts apart (?stitch=0)
        for (const stitch of [true, false]) {
            const world = worldWith(stitch).world;
            const reach = new Set(world.reachByRoom(world.survey(null, { npcs: false }).reach).Palace);
            assert.deepStrictEqual(free.filter((xy) => !reach.has(xy)), [], stitch ? 'stitched' : 'not stitched');
        }
    });
};
