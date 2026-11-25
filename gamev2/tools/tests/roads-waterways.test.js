module.exports = ({ test, assert, fs, path, GV2, load, game, worldWith }) => {
    test('a road over a train track is an open level crossing, in every room', () => {
        // tools/seal_tracks.py leaves a track cell with a road under it unsealed; Palace has two (#138)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const sealed = [], crossings = {};
        for (const [key, room] of Object.entries(cfg.rooms)) {
            const layer = (n) => ((room.layers || []).find((l) => l.name === n) || {}).tiles || {};
            const floor = layer('Floor'), colliders = layer('Colliders');
            for (const l of room.layers || []) {
                for (const [xy, t] of Object.entries(l.tiles || {})) {
                    if (!name(t).startsWith('train-track') || !name(floor[xy]).startsWith('road-')) continue;
                    (crossings[key] = crossings[key] || []).push(xy);
                    if (xy in colliders) sealed.push(`${key} @${xy}`);
                }
            }
        }
        assert.deepStrictEqual(sealed, []);
        assert.deepStrictEqual(crossings.Palace.sort(), ['0,3', '1,3', '54,3', '55,3', '56,3'], 'west and east roads cross the track');
    });

    test('Osaka: both pavements pass the signal posts at the bridgehead without the road', () => {
        // the posts stand on the kerb at (22,19) and (27,19); the bridge pavement is two cells wide round them (#139)
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const layer = (n) => (cfg.rooms.Osaka.layers.find((l) => l.name === n) || {}).tiles || {};
        const floor = layer('Floor'), colliders = layer('Colliders');
        const open = (xy) => xy in floor && !(xy in colliders) && !name(floor[xy]).startsWith('road-');
        const reach = (from, to) => {
            const seen = new Set([from]), todo = [from];
            while (todo.length) {
                const [x, y] = todo.pop().split(',').map(Number);
                if (y < 17 || y > 23) continue;                    // round the post, not round the town
                for (const n of [`${x + 1},${y}`, `${x - 1},${y}`, `${x},${y + 1}`, `${x},${y - 1}`]) {
                    if (open(n) && !seen.has(n)) { seen.add(n); todo.push(n); }
                }
            }
            return seen.has(to);
        };
        for (const x of [22, 27]) {
            assert.ok(`${x},19` in colliders, `signal post base at ${x},19`);
            assert.ok(reach(`${x},18`, `${x},22`), `pavement at column ${x} is cut off by its signal post`);
        }
    });

    test('Osaka: the canal is a declared waterway, open water except under the bridge, and the streets have centre lines', () => {
        // #61: AmbientBoats sails the room's `waterways`; #151: the four-cell street's line is the lane pair's shared edge
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const room = cfg.rooms.Osaka;
        const layer = (n) => (room.layers.find((l) => l.name === n) || {}).tiles || {};
        const floor = layer('Floor'), water = layer('Water'), colliders = layer('Colliders');
        assert.strictEqual(room.waterways.length, 1);
        const w = room.waterways[0];
        assert.deepStrictEqual([w.axis, w.from, w.to], ['h', 0, room.worldWidth / 64 - 1], 'the canal runs edge to edge');
        const under = (x) => w.under.some(([a, b]) => x >= a && x <= b);
        for (let x = w.from; x <= w.to; x++) {
            for (let y = w.row; y < w.row + w.rows; y++) {
                const xy = `${x},${y}`;
                if (under(x)) {
                    assert.ok(!(xy in water) && !(xy in colliders), `bridge deck cell ${xy} is walkable paving, not water`);
                } else {
                    assert.ok(name(water[xy]).startsWith('pond-autotile_') && xy in colliders, `canal cell ${xy} is solid water`);
                    assert.ok(!/corner|edge-[ew]/.test(name(water[xy])), `canal cell ${xy} is an end cap: the channel is not open`);
                }
            }
        }
        const rows = Object.keys(floor).filter((xy) => name(floor[xy]) === 'road-lane-left_0_0').map((xy) => xy.split(',').map(Number));
        assert.ok(rows.length >= 12, 'the main street is a street, not a stub');
        for (const [x, y] of rows) {
            assert.deepStrictEqual([name(floor[`${x - 1},${y}`]), name(floor[`${x + 1},${y}`]), name(floor[`${x + 2},${y}`])],
                ['road-edge-left_0_0', 'road-lane-right_0_0', 'road-edge-right_0_0'], `street row ${y}: kerb, lane | lane, kerb`);
        }
        const lines = Object.keys(floor).filter((xy) => name(floor[xy]) === 'road-div-horizontal_0_0').map((xy) => Number(xy.split(',')[0]));
        assert.ok(lines.includes(0) && lines.includes(room.worldWidth / 64 - 1), 'the avenue leaves town at both edges');
        for (const key of ['road-lane-left_0_0', 'road-lane-right_0_0', 'road-corner-nw_0_0', 'road-corner-ne_0_0', 'road-corner-sw_0_0']) {
            assert.ok(key in cfg.spriteMetadata && fs.existsSync(path.join(GV2, 'assets', 'sprites', key + '.png')), `${key} is loadable`);
        }
    });

    test('a boat is picked to fit the water left in view, and is cut off at a bridge deck', () => {
        // #62: the north moat shows a 32px lane above the palace wall - skiff only; #61: `under` spans hide the boat
        load('AmbientBoats.js');
        const boats = game('Object.create(AmbientBoats.prototype)');
        const run = (width, length) => boats.fit({ axis: 'h', from: 0, to: length, band0: 100, band1: 100 + width });
        assert.deepStrictEqual(Array.from(run(50, 400).hulls), ['punt', 'skiff']);
        assert.deepStrictEqual(Array.from(run(32, 400).hulls), ['skiff'], 'a narrow lane takes the skiff');
        assert.strictEqual(run(24, 400), null, 'no boat is squeezed into less water than its beam');
        assert.strictEqual(run(50, 150), null, 'nor into a run it could not travel along');
        for (const livery of Object.keys(game('AmbientBoats.LIVERIES'))) {
            assert.ok(game('AmbientBoats.HULLS')[game('AmbientBoats.hullOf')(livery)], `${livery} is painted on a known hull`);
        }
        const boat = { width: 116, height: 44, visible: true, crop: null,
            setVisible(v) { this.visible = v; }, setCrop(x, y, w, h) { this.crop = [x, y, w, h]; } };
        const deck = { axis: 'h', under: [[1000, 1500]] };
        boats.hideUnder(boat, deck, 500, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [0, 0, 116, 44]], 'clear of the bridge: drawn whole');
        boats.hideUnder(boat, deck, 990, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [0, 0, 68, 44]], 'bow under the deck: cut at its edge');
        boats.hideUnder(boat, deck, 1250, 116);
        assert.strictEqual(boat.visible, false, 'wholly under the deck: not drawn');
        boats.hideUnder(boat, deck, 1520, 116);
        assert.deepStrictEqual([boat.visible, boat.crop], [true, [38, 0, 78, 44]], 'stern still under the deck');
    });

    test('Tokyo west gate: the lane to Machi is paved, clear of lanterns, and meets the dirt path square', () => {
        // #147: the lantern's top used to hang over the lane and the asphalt butted into Machi's rounded path end
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
        const tiles = (room, n) => (cfg.rooms[room].layers.find((l) => l.name === n) || {}).tiles || {};
        const seam = cfg.rooms.Tokyo.transporters.filter((t) => t.targetRoom === 'Machi');
        assert.deepStrictEqual(seam.map((t) => [t.gridX, t.gridY]), [[0, 41], [0, 42]]);
        for (const y of [41, 42]) {
            for (const x of [0, 1, 2]) {
                for (const n of ['Tops', 'Collidables', 'Other', 'Colliders']) {
                    assert.ok(!(`${x},${y}` in tiles('Tokyo', n)), `Tokyo ${x},${y}: ${n} tile on the lane`);
                }
                // a sprite one cell down whose top row lands on the lane (the lantern head)
                assert.ok(!name(tiles('Tokyo', 'Tops')[`${x},${y}`]).startsWith('red-lanterns'), `lantern head over ${x},${y}`);
            }
            assert.ok(name(tiles('Tokyo', 'Floor')[`0,${y}`]).startsWith('flat-grey-brick'), 'the gate is a paved apron');
            assert.ok(name(tiles('Tokyo', 'Floor')[`2,${y}`]).startsWith('road-edge-left'), 'the road keeps its kerb past the gate');
            assert.ok(/^gravel-autotile_edge-[ns]$/.test(name(tiles('Machi', 'Floor')[`47,${y - 21}`])), 'the path runs out through the gate');
        }
        assert.strictEqual(name(tiles('Tokyo', 'Floor')['2,43']), 'road-corner-sw_0_0', 'the junction box has its corner');
    });

    test('road junctions are plain boxes: no kerb across a joining road, no centre line through one (#179)', () => {
        const { world } = worldWith(true);
        const city = world.roomManager.rooms.TokyoCity;
        const road = {};
        for (const layer of city.layers) {
            if (layer.z >= 2 || layer.collision) continue;
            for (const [xy, key] of Object.entries(layer.tiles)) if (/^road-/.test(key)) road[xy] = key.replace(/_0_0$/, '');
        }
        const at = (x, y) => road[`${x},${y}`] || '';
        const bad = [];
        let lines = 0;
        for (const xy of Object.keys(road)) {
            const [x, y] = xy.split(',').map(Number), t = road[xy];
            if (t === 'road-div-vertical') {
                lines++;
                for (const ny of [y - 1, y + 1]) {
                    if (/^road-(edge-(top|bottom)|div-horizontal)$/.test(at(x, ny))) bad.push(`${xy}: the line meets ${at(x, ny)} at ${x},${ny}`);
                }
            }
            if (t === 'road-div-horizontal') {
                lines++;
                for (const nx of [x - 1, x + 1]) {
                    if (/^road-(edge-(left|right)|div-vertical)$/.test(at(nx, y))) bad.push(`${xy}: the line meets ${at(nx, y)} at ${nx},${y}`);
                }
            }
        }
        assert.ok(lines > 500, `the city's roads were read (${lines} centre-line cells)`);
        assert.deepStrictEqual(bad, []);
        // a bend has its mitred outer corner: Tokyo's north-west one, and Park's south-west one,
        // whose west kerb and corner stand in the woods (cities.backdrop.edges)
        const rm = world.roomManager;
        const nw = rm.resolve('Tokyo', 2, 2), sw = rm.resolve('Park', 0, 41);
        assert.strictEqual(at(nw.x, nw.y), 'road-corner-nw');
        assert.strictEqual(at(nw.x + 1, nw.y + 1), 'road-plain');
        assert.strictEqual(at(sw.x - 1, sw.y), 'road-corner-sw');
        assert.strictEqual(at(sw.x - 1, sw.y - 1), 'road-edge-left');
        // on its own (?stitch=0) Park's top row is the far kerb of a T-junction; stitched, Palace's
        // roads run into it and the patch opens it
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const park = cfg.rooms.Park.layers.find((l) => l.name === 'Floor').tiles;
        for (const x of [0, 1, 54, 55, 56]) {
            assert.strictEqual(cfg.tilePalette[park[`${x},0`]], 'road-edge-top_0_0', `Park ${x},0`);
            const c = rm.resolve('Park', x, 0);
            assert.strictEqual(at(c.x, c.y), 'road-plain', `stitched Park ${x},0`);
        }
    });

    test('the avenue runs up to the Tokyo/Market crossroads as road, not a strip of pavement (#194)', () => {
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const rows = ['road-edge-top_0_0', 'road-div-horizontal_0_0', 'road-edge-bottom_0_0'];
        for (const [room, xs, y0] of [['Tokyo', [54, 55, 56], 41], ['Market', [2, 3, 4], 42], ['Market', [52, 53, 57, 58], 42]]) {
            const floor = cfg.rooms[room].layers.find((l) => l.name === 'Floor').tiles;
            for (const x of xs) {
                rows.forEach((want, dy) => assert.strictEqual(cfg.tilePalette[floor[`${x},${y0 + dy}`]], want, `${room} ${x},${y0 + dy}`));
            }
        }
    });
};
