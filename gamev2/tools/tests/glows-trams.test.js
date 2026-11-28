// Night glow spots of placed sprites (src/utils/Glows.js) and the streetcar mover (src/AmbientTrams.js), issue #219.
module.exports = ({ test, assert, fs, path, vm, GV2, ctx, game }) => {
    const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
    const plain = (v) => JSON.parse(JSON.stringify(v === undefined ? null : v));   // out of the vm's realm
    const glows = () => {
        if (!game('typeof Glows !== "undefined"')) vm.runInContext(src('utils/Glows.js'), ctx, { filename: 'Glows.js' });
        return game('Glows');
    };
    const trams = () => {
        if (!game('typeof AmbientTrams !== "undefined"')) vm.runInContext(src('AmbientTrams.js'), ctx, { filename: 'AmbientTrams.js' });
        return game('AmbientTrams');
    };
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));

    test('a sprite lights at night only what it declares, and data beats the table', () => {
        const G = glows();
        // nothing declared, nothing lit: a lamp post is the tile-key rule's, not this table's
        assert.deepStrictEqual(plain(G.spotsFor('blue-lamp-post_0_0', { anchorX: 0.5 })), []);
        assert.deepStrictEqual(plain(G.spotsFor('no-such-sprite', undefined)), []);
        const table = G.spotsFor('susukino-neon-corner_0_0', undefined);
        assert.ok(table.length >= 4, 'the neon corner has its boards');
        // spriteMetadata's `glow` wins over the table, an empty list turns the sprite off, a broken spot is dropped
        const own = [{ x: 1, y: 1, r: 1, color: 0x00ff00 }, { x: 1, y: 'a', r: 1 }, { x: 1, y: 1, r: 0 }];
        assert.deepStrictEqual(plain(G.spotsFor('susukino-neon-corner_0_0', { glow: own })), [own[0]]);
        assert.deepStrictEqual(plain(G.spotsFor('susukino-neon-corner_0_0', { glow: [] })), []);
        // a spot is in cells from the art's corner: placed at the record's corner, in pixels
        const [halo, plainHalo] = plain(G.place(640, 320, 64, [
            { x: 1.5, y: 2, r: 2, ry: 0.5, color: 0xff00ff, a: 0.5, pulse: { period: 2000, depth: 0.4 } }, { x: 0, y: 0, r: 1 }]));
        assert.deepStrictEqual([halo.x, halo.y, halo.rx, halo.ry, halo.color, halo.alpha], [736, 448, 128, 32, 0xff00ff, 0.5]);
        assert.deepStrictEqual([plainHalo.rx, plainHalo.ry, plainHalo.color, plainHalo.alpha, plainHalo.pulse, plainHalo.flicker],
            [64, 64, G.DEFAULT, 1, null, false], 'defaults: round, the lamps\' colour, full strength, steady');
        assert.ok(G.animated(halo) && !G.animated(plainHalo));
        // a half-scale sprite's cell is half a grid cell
        assert.deepStrictEqual(plain(G.place(0, 0, 32, [{ x: 2, y: 2, r: 1 }])).map((h) => [h.x, h.y, h.rx]), [[64, 64, 32]]);
    });

    test('a glow pulses gently and a tube only dips now and then', () => {
        const G = glows();
        const steady = G.place(0, 0, 64, [{ x: 1, y: 1, r: 1 }])[0];
        const pulse = G.place(0, 0, 64, [{ x: 1, y: 1, r: 1, pulse: { period: 2000, depth: 0.4 } }])[0];
        const tube = G.place(0, 0, 64, [{ x: 1, y: 1, r: 1, flicker: true }])[0];
        let lo = 1, hi = 0, dips = 0, steps = 0;
        for (let ms = 0; ms < 60000; ms += 10) {
            assert.strictEqual(G.level(steady, ms), 1);
            const p = G.level(pulse, ms);
            lo = Math.min(lo, p); hi = Math.max(hi, p);
            const f = G.level(tube, ms);
            assert.ok(f === 1 || f === G.FLICKER_DIP, 'a tube is on or sagging, never off');
            if (ms % G.FLICKER_STEP === 0) { steps++; if (f < 1) dips++; }
        }
        assert.ok(hi > 0.999 && Math.abs(lo - 0.6) < 0.001, `a pulse swells between 1 and 1 - depth (${lo}..${hi})`);
        assert.ok(Math.abs(G.level(pulse, 123) - G.level(pulse, 2123)) < 1e-9, 'and repeats every period');
        assert.ok(dips > 0 && dips / steps < 0.15, `a tube dips in ${dips} of ${steps} steps`);
        assert.strictEqual(G.level(tube, 5000), G.level(tube, 5000), 'the same at the same time');
        // two copies of one sprite are out of step
        const other = G.place(640, 0, 64, [{ x: 1, y: 1, r: 1, pulse: { period: 2000, depth: 0.4 } }])[0];
        assert.notStrictEqual(G.level(pulse, 500), G.level(other, 500));
    });

    // Every sprite with glow spots (a row of the table, or a `glow` list in spriteMetadata) has art and
    // spots that are on it and small enough to cull. True of any config, placed or not.
    const checkGlows = (G, c) => {
        const size = (file) => { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
        const meta = c.spriteMetadata || {};
        const declared = Object.keys(meta).filter((k) => meta[k] && meta[k].glow !== undefined);
        for (const key of new Set([...Object.keys(G.SPRITES), ...declared])) {
            const own = meta[key] && meta[key].glow;
            assert.ok(own === undefined || Array.isArray(own), `${key}: spriteMetadata glow is a list`);
            const spots = own === undefined ? G.SPRITES[key] : own;
            const file = path.join(GV2, 'assets', 'sprites', key + '.png');
            assert.ok(fs.existsSync(file), `${key} has art`);
            assert.ok(!/lamp-post|-lanterns/.test(key), `${key} is not lit twice (the lamp rule already lights it)`);
            const [w, h] = size(file);
            // an empty list in spriteMetadata turns a sprite off; a table row must light something
            assert.ok((own !== undefined || spots.length) && spots.every(G.valid), `${key}: every spot has a place and a size`);
            for (const s of spots) {
                assert.ok(s.x >= 0 && s.x <= w / 64 && s.y >= 0 && s.y <= h / 64, `${key}: spot ${s.x},${s.y} is on the ${w / 64}x${h / 64} sprite`);
                assert.ok(s.r <= 2.5 && (s.ry || s.r) <= 2.5, `${key}: a halo stays within DayNight.cullGlows' four-cell margin`);
            }
        }
    };

    test('every glowing sprite has art and spots inside it, in the table or in spriteMetadata', () => {
        const G = glows(), c = cfg();
        checkGlows(G, c);
        // registering or placing a table sprite is the map's business, not a failure here
        const key = Object.keys(G.SPRITES)[0];
        checkGlows(G, { tilePalette: [...c.tilePalette, key], spriteMetadata: { ...c.spriteMetadata, [key]: { glow: G.SPRITES[key] } } });
        checkGlows(G, { spriteMetadata: { [key]: { glow: [] } } });
        // what would not draw right is
        const bad = (glow, why) => assert.throws(() => checkGlows(G, { spriteMetadata: { [key]: { glow } } }), assert.AssertionError, why);
        bad([{ x: 999, y: 1, r: 1 }], 'a spot off the sprite');
        bad([{ x: 1, y: 1, r: 3 }], 'a halo wider than the cull margin');
        bad([{ x: 1, y: 1 }], 'a spot with no size');
        bad({ x: 1, y: 1, r: 1 }, 'not a list');
        assert.throws(() => checkGlows(G, { spriteMetadata: { 'no-such-art_0_0': { glow: [{ x: 0, y: 0, r: 1 }] } } }), assert.AssertionError);
        // DayNight builds them from the room's tile records and re-lights the animated ones as it culls
        const dn = src('DayNight.js');
        assert.ok(/Glows\.spotsFor\(rec\.key, meta\[rec\.key\]\)/.test(dn) && /Glows\.level\(g\.halo, now\)/.test(dn));
    });

    test('a building faded because somebody is behind it takes its own glow down with it; a lamp post stays lit (#220)', () => {
        const G = glows();
        if (!game('typeof Occlusion !== "undefined"')) vm.runInContext(src('systems/Occlusion.js'), ctx, { filename: 'Occlusion.js' });
        const ALPHA = game('Occlusion.ALPHA');
        // at full strength (no fade on the record) nothing changes: strength x level
        assert.strictEqual(G.shown(0.8, 1, undefined), 0.8);
        assert.strictEqual(G.shown(0.8, 0.5, undefined), 0.4);
        // faded with the building, in step with it all the way down and back
        assert.ok(Math.abs(G.shown(0.8, 1, ALPHA) - 0.8 * ALPHA) < 1e-9);
        assert.ok(Math.abs(G.shown(1, G.FLICKER_DIP, ALPHA) - G.FLICKER_DIP * ALPHA) < 1e-9, 'a dipping tube on a ghosted building');
        let prev = 1;
        for (let fade = 1; fade >= ALPHA; fade -= 0.05) { const a = G.shown(1, 1, fade); assert.ok(a <= prev); prev = a; }
        assert.deepStrictEqual([G.shown(1, 1, 0), G.shown(1, 1, 7), G.shown(1, 1, -1), G.shown(1, 1, NaN)], [0, 1, 0, 1], 'kept in 0..1; junk is full strength');
        // DayNight: each sprite glow knows its record and is re-lit every frame it is in view; a lamp's
        // Graphics halo is given no record, so it is never touched
        const dn = src('DayNight.js');
        assert.ok(dn.includes('img.rec = rec;') && dn.includes('img.strength = halo.alpha;'));
        assert.ok(dn.includes('if (g.rec && g.visible) g.setAlpha(Glows.shown(g.strength, g.halo ? Glows.level(g.halo, now) : 1, g.rec.fade));'));
        const lamps = dn.slice(dn.indexOf('    buildGlows(roomKey) {'), dn.indexOf('    buildSpriteGlows() {'));
        assert.ok(lamps.includes('lamp-post|-lanterns') && !/\.rec\b/.test(lamps), 'a lamp halo belongs to no building');
        // the fade it reads is the one Occlusion keeps on the record
        assert.ok(src('systems/Occlusion.js').includes('rec.fade = next;'));
    });

    test('a streetcar at night: a warm glow along its windows and a headlight on the end it is heading for (#220)', () => {
        const T = trams(), GS = 64;
        for (const [width, height] of [[320, 192], [256, 128]]) {
            const east = plain(T.lights(width, height, 1, GS)), west = plain(T.lights(width, height, -1, GS));
            assert.strictEqual(east.length, 2);
            const [glowE, headE] = east, [glowW, headW] = west;
            // the windows: on the centre line, the car's length, the same both ways
            assert.deepStrictEqual(glowE, glowW);
            assert.deepStrictEqual([glowE.x, glowE.rx * 2], [width / 2, width]);
            assert.ok(glowE.y > height * 0.3 && glowE.y < height * 0.7 && glowE.alpha < 0.7, 'soft, over the body');
            // the headlight: just ahead of the nose going east, and mirrored about the centre line going west
            assert.ok(headE.x > width && headE.x - headE.rx < width, 'it sits on the leading end');
            assert.ok(Math.abs(headW.x - (width - headE.x)) < 1e-9 && headW.x < 0, 'mirrored with the car');
            assert.deepStrictEqual([headW.y, headW.rx, headW.ry, headW.color, headW.alpha], [headE.y, headE.rx, headE.ry, headE.color, headE.alpha]);
            assert.ok(headE.y > glowE.y && headE.y < height, 'low on the car');
            assert.ok(headE.rx <= GS && headE.rx < glowE.rx / 2, 'small');
            // everything stays inside the four cells DayNight culls halos by, measured from the car
            for (const l of [...east, ...west]) assert.ok(l.x + l.rx <= width + GS * 4 && l.x - l.rx >= -GS * 4 && l.ry <= GS * 2.5);
        }
        // only at night, only while the car is seen, following it, faded with it, destroyed with it
        const code = src('AmbientTrams.js');
        assert.ok(code.includes("const lit = seen && typeof Glows !== 'undefined' && !!(scene.dayNight && scene.dayNight.lights);"));
        assert.ok(code.includes('this.light(state, seen, at.alpha);'));
        assert.ok(code.includes('g.setPosition(img.x + s.x, img.y + s.y);') && code.includes('g.setAlpha(s.alpha * alpha);'));
        assert.ok(code.includes('Glows.texture(scene)') && !/load\.image|textures\.addCanvas/.test(code), 'the lamps\' halo texture: no new art');
        assert.ok(/retire\(state\) \{[\s\S]{0,200}g\.destroy\(\)/.test(code));
        const dn = src('DayNight.js');
        assert.ok(dn.includes('this.lights = !!(grade && grade.lights);'));
        if (!game('typeof DayNight !== "undefined"')) vm.runInContext(dn, ctx, { filename: 'DayNight.js' });
        const grade = game('DayNight.gradeFor');
        assert.deepStrictEqual(['dawn', 'day', 'dusk', 'night'].map((p) => !!((grade({}, p) || {}).lights)), [false, false, false, true]);
    });

    // Every declared tramway is a line that can run: AmbientTrams.line accepts it, it is inside its room,
    // and its cars are registered sprites (GameScene loads textures from spriteMetadata, and a car with
    // no texture never departs). No two lines of a room share cells of a row. True of any config, with or
    // without tramways.
    //
    // A shuttle (#245) stands in the street, is solid while it stands and is got off on either side, so
    // more is asked of one: nothing solid on the cells it runs over, every halt (its stops and both
    // termini, on the way out and the way back) on whole cells, and beside every halt a cell to step
    // onto on the north side and one on the south - a side is never swapped for the other. The tests
    // have no textures: a car's size in cells is its spriteMetadata anchors', as the game places a tile.
    const checkTramways = (T, c) => {
        for (const [key, room] of Object.entries(c.rooms)) {
            if (room.tramways === undefined) continue;
            assert.ok(Array.isArray(room.tramways), `${key}: tramways is a list`);
            const cols = Math.round(room.worldWidth / 64), rows = Math.round(room.worldHeight / 64);
            // layers as the game sees them: sprite names, not palette indices
            const layers = (room.layers || []).map((l) => ({
                tiles: Object.fromEntries(Object.entries(l.tiles || {}).map(([xy, v]) => [xy, typeof v === 'number' ? c.tilePalette[v] : v])),
            }));
            const solid = ((room.layers || []).find((l) => l.name === 'Colliders') || {}).tiles || {};
            const walkable = (x, y) => x >= 0 && x < cols && y >= 0 && y < rows && !(`${x},${y}` in solid);
            const lines = [];
            room.tramways.forEach((def, i) => {
                const line = T.line(def, layers, null, cols);
                assert.ok(line, `${key} tramway ${i} is a line that can run (a row, rails or from / to, a sprite)`);
                assert.ok(line.row >= 0 && line.row < rows, `${key} tramway ${i}: row ${line.row} is in the room`);
                assert.ok(line.from >= 0 && line.to < cols, `${key} tramway ${i}: ${line.from}..${line.to} is in the room`);
                for (const sprite of line.sprites) assert.ok((c.spriteMetadata || {})[sprite], `${key} tramway ${i}: ${sprite} is in spriteMetadata, so it is loaded`);
                assert.strictEqual(line.shuttle, def.shuttle === true, `${key} tramway ${i}: a shuttle only when it says so`);
                for (const other of lines) {
                    assert.ok(other.row !== line.row || other.to < line.from || other.from > line.to, `${key} tramway ${i} shares cells of row ${line.row} with another line`);
                }
                lines.push(line);
                if (!line.shuttle) return;
                const meta = c.spriteMetadata[line.sprites[0]];
                const w = Math.round(0.5 / (meta.anchorX || 0.5)), h = Math.round(0.5 / (meta.anchorY || 0.5));
                for (let x = line.from; x <= line.to; x++) for (let y = line.row - h + 1; y <= line.row; y++) {
                    assert.ok(walkable(x, y), `${key} tramway ${i}: the car runs over ${x},${y}, which is solid or off the map`);
                }
                for (const dir of [1, -1]) {
                    const plan = T.plan(line, { GS: 64, width: w * 64, worldWidth: room.worldWidth, dir });
                    const halts = plan.legs.filter((l) => l.x0 === l.x1);
                    assert.ok(halts.length >= 1, `${key} tramway ${i}: a shuttle stands somewhere`);
                    for (const halt of halts) {
                        assert.strictEqual(halt.x0 % 64, 0, `${key} tramway ${i}: a halt at ${halt.x0}px is not on whole cells`);
                        const f = T.footprint(line.row, halt.x0, 64, w * 64, h * 64);
                        assert.ok(f.x0 >= line.from && f.x1 <= line.to, `${key} tramway ${i}: halted on ${f.x0}..${f.x1}, off its line`);
                        for (const [side, y] of [['north', f.y0 - 1], ['south', f.y1 + 1]]) {
                            let free = false;
                            for (let x = f.x0; x <= f.x1; x++) free = free || walkable(x, y);
                            assert.ok(free, `${key} tramway ${i}: no cell to get off on the ${side} side of the halt on ${f.x0}..${f.x1}`);
                        }
                    }
                }
            });
        }
    };

    test('a tramway is declared data: its row, its rails, its stops', () => {
        const T = trams();
        const rails = (row, from, to) => {
            const tiles = {};
            for (let x = from; x <= to; x++) tiles[`${x},${row}`] = x === 10 ? 'tram-rail-cross_0_0' : 'tram-rail-h_0_0';
            tiles[`3,${row + 1}`] = 'tram-rail-v_0_0';   // a crossing line is not this row's rail
            return [{ tiles: { '0,0': 'road-plain_0_0' } }, { tiles }];
        };
        // from / to left out: the row's rails
        const line = plain(T.line({ row: 21, sprite: 'sapporo-streetcar_0_0', stops: [12, { x: 40, dwell: 6 }, 99] }, rails(21, 0, 55), null, 56));
        assert.deepStrictEqual([line.row, line.from, line.to, line.sprites, line.speed, line.headway, line.dwell],
            [21, 0, 55, ['sapporo-streetcar_0_0'], T.SPEED, T.HEADWAY, T.DWELL]);
        assert.deepStrictEqual(line.stops, [{ x: 12, dwell: T.DWELL }, { x: 40, dwell: 6 }], 'a stop off the line is dropped');
        assert.deepStrictEqual(line.open, [true, true], 'rails to both edges of the room: the car comes from off the map');
        // explicit cells need no rail tiles; an end inside the room is a terminus; a list of cars takes turns
        const closed = plain(T.line({ row: 16, from: 5, to: 40, sprite: ['sfb-cable-car_0_0', 'sfb-tram_0_0'], speed: 96, headway: 20, dwell: 2 }, [], null, 60));
        assert.deepStrictEqual([closed.from, closed.to, closed.open, closed.sprites.length, closed.speed, closed.headway, closed.dwell],
            [5, 40, [false, false], 2, 96, 20, 2]);
        // in a stitched city the line moves with its district
        const moved = plain(T.line({ row: 21, from: 0, to: 55, sprite: 's', stops: [12] }, [], { x: 58, y: 47 }, 200));
        assert.deepStrictEqual([moved.row, moved.from, moved.to, moved.stops[0].x, moved.open], [68, 58, 113, 70, [false, false]]);
        // what cannot run is no line
        assert.strictEqual(T.line({ row: 21, sprite: 's' }, rails(20, 0, 55), null, 56), null, 'no rails on the row');
        assert.strictEqual(T.line({ row: 21, from: 4, to: 5, sprite: 's' }, [], null, 56), null, 'too short');
        assert.strictEqual(T.line({ row: 21, from: 0, to: 55 }, [], null, 56), null, 'no sprite');
        assert.strictEqual(T.line({ from: 0, to: 55, sprite: 's' }, [], null, 56), null, 'no row');
        // whatever the rooms declare can run (none has to)
        const c = cfg();
        checkTramways(T, c);
        const car = Object.keys(c.spriteMetadata)[0];
        const room = (tramways, tiles) => ({ rooms: { R: { worldWidth: 56 * 64, worldHeight: 30 * 64, tramways, layers: [{ tiles: tiles || {} }] } },
            tilePalette: ['tram-rail-h_0_0'], spriteMetadata: c.spriteMetadata });
        checkTramways(T, room([{ row: 21, from: 4, to: 55, sprite: car, stops: [14] }]));
        checkTramways(T, room([{ row: 21, sprite: car }], { '0,21': 0, '55,21': 0 }));   // rails stored as palette indices are found
        checkTramways(T, room([]));
        const bad = (def, why) => assert.throws(() => checkTramways(T, room(Array.isArray(def) || typeof def !== 'object' ? def : [def])), assert.AssertionError, why);
        bad({ row: 21, sprite: car }, 'no rails and no from / to');
        bad({ row: 21, from: 4, to: 55, sprite: 'not-registered_0_0' }, 'a car that is never loaded');
        bad({ row: 30, from: 4, to: 55, sprite: car }, 'a row under the room');
        bad({ row: 21, from: 4, to: 56, sprite: car }, 'past the east edge');
        bad({ row: 21, from: -1, to: 55, sprite: car }, 'past the west edge');
        bad('Sapporo', 'not a list');
        // drawn with what stands on the rail row, just under a character on it and over one a row behind
        assert.strictEqual(T.depthAt(21), 224);
        assert.ok(T.depthAt(21) < (21 + 1) * 10 + 5 && T.depthAt(21) > 21 * 10 + 5);
    });

    test('a streetcar keeps its timetable: stops, dwells, the way back, the ends', () => {
        const T = trams();
        const GS = 64, width = 320, worldWidth = 56 * GS;
        const line = T.line({ row: 21, from: 0, to: 55, sprite: 's', speed: 160, stops: [12, { x: 40, dwell: 6 }] }, [], null, 56);
        const east = T.plan(line, { GS, width, worldWidth, dir: 1 });
        // in from off the map, out off the map
        assert.deepStrictEqual([east.fromX, east.toX], [-width, worldWidth]);
        const stopX = (cell) => (cell + 0.5) * GS - width / 2;
        const dwells = east.legs.filter((l) => l.x0 === l.x1);
        assert.deepStrictEqual(plain(dwells.map((l) => [l.x0, l.t1 - l.t0])), [[stopX(12), 4000], [stopX(40), 6000]], 'centred on each stop, for its dwell');
        // a leg into a stop takes a quarter longer than at full speed (it slows down), one between stops half as long again
        const [first, , second] = east.legs;
        assert.ok(Math.abs((first.t1 - first.t0) - (stopX(12) + width) / 160 * 1000 * 1.25) < 1e-6);
        assert.ok(Math.abs((second.t1 - second.t0) - (stopX(40) - stopX(12)) / 160 * 1000 * 1.5) < 1e-6);
        // position: continuous, never backwards, standing still for the whole dwell, never faster than 1.5x speed
        let prev = T.at(east, 0);
        assert.deepStrictEqual([prev.x, prev.alpha, prev.done], [-width, 1, false]);
        for (let ms = 50; ms <= east.duration; ms += 50) {
            const at = T.at(east, ms);
            assert.ok(at.x >= prev.x - 1e-9 && at.x - prev.x <= 160 * 0.05 * 1.5 + 1e-6, `at ${ms}ms: ${prev.x} -> ${at.x}`);
            assert.strictEqual(at.alpha, 1, 'open ends: no fade');
            prev = at;
        }
        const mid = dwells[0].t0 + 2000;
        assert.deepStrictEqual([T.at(east, mid).x, T.at(east, mid).stopped], [stopX(12), true]);
        assert.deepStrictEqual([T.at(east, east.duration).x, T.at(east, east.duration + 5000).done], [worldWidth, true]);
        // the way back: the other end first, the far stop first, the same length of trip
        const west = T.plan(line, { GS, width, worldWidth, dir: -1 });
        assert.deepStrictEqual([west.dir, west.fromX, west.toX], [-1, worldWidth, -width]);
        assert.deepStrictEqual(plain(west.legs.filter((l) => l.x0 === l.x1).map((l) => l.x0)), [stopX(40), stopX(12)]);
        assert.ok(Math.abs(west.duration - east.duration) < 1e-6);
        assert.deepStrictEqual([0, 1, 2, 3].map(T.direction), [1, -1, 1, -1], 'trips alternate');
        // a terminus inside the room: the car stays on its rails and fades in and out there
        const shuttle = T.line({ row: 16, from: 5, to: 40, sprite: 's', stops: [5, 22] }, [], null, 60);
        const trip = T.plan(shuttle, { GS, width, worldWidth: 60 * GS, dir: 1 });
        assert.deepStrictEqual([trip.fromX, trip.toX], [5 * GS, 41 * GS - width], 'never past the last rail');
        assert.strictEqual(trip.legs.filter((l) => l.x0 === l.x1).length, 1, 'a stop at the terminus itself is not a second stop');
        assert.strictEqual(T.at(trip, 0).alpha, 0);
        assert.strictEqual(T.at(trip, trip.duration).alpha, 0);
        const half = T.at(trip, trip.duration / 2);
        assert.ok(half.alpha === 1 && half.x > trip.fromX && half.x < trip.toX);
        for (let ms = 0; ms <= trip.duration; ms += 100) {
            const at = T.at(trip, ms);
            assert.ok(at.x >= trip.fromX - 1e-9 && at.x <= trip.toX + 1e-9 && at.alpha >= 0 && at.alpha <= 1);
        }
    });

    test('a shuttle is one car that never leaves: whole-cell stops, a layover at each end, no fade (#245)', () => {
        const T = trams();
        const GS = 64;
        const def = { row: 16, from: 4, to: 27, sprite: 'c', shuttle: true, name: 'cable car', stops: [11, 20], speed: 192, dwell: 5, headway: 8 };
        const line = T.line(def, [], null, 60);
        assert.deepStrictEqual([line.shuttle, line.name, line.faces, plain(line.open)], [true, 'cable car', 1, [false, false]]);
        // what the keys default to: not a shuttle, "tram", art heading east
        const dflt = T.line({ row: 16, from: 4, to: 27, sprite: 'c' }, [], null, 60);
        assert.deepStrictEqual([dflt.shuttle, dflt.name, dflt.faces], [false, 'tram', 1]);
        assert.deepStrictEqual(['west', 'east', 'north', undefined, -1].map((faces) => T.line({ ...def, faces }, [], null, 60).faces), [-1, 1, 1, 1, 1]);
        assert.strictEqual(T.line({ ...def, shuttle: 'yes' }, [], null, 60).shuttle, false, 'only `true` is a shuttle');
        assert.strictEqual(T.line({ ...def, name: '' }, [], null, 60).name, 'tram');
        // a shuttle cannot leave the map, and is one car
        assert.strictEqual(T.line({ ...def, from: 0 }, [], null, 60), null, 'a west end on the room\'s edge');
        assert.strictEqual(T.line({ ...def, to: 59 }, [], null, 60), null, 'an east end on the room\'s edge');
        assert.strictEqual(T.line({ ...def, sprite: ['c', 'd'] }, [], null, 60), null, 'two cars taking turns');
        assert.ok(T.line({ ...def, shuttle: false, to: 59, sprite: ['c', 'd'] }, [], null, 60), 'either is fine on a line that is not one');

        // stops on whole cells, the car's middle as near the stop's as cells allow: cars 3, 4 and 5 cells long
        const halts = (plan) => plan.legs.filter((l) => l.x0 === l.x1);
        const stopCells = (width, stops, dir) => plain(halts(T.plan(T.line({ ...def, stops }, [], null, 60), { GS, width, worldWidth: 60 * GS, dir: dir || 1 }))
            .slice(0, -1).map((l) => l.x0 / GS));
        assert.deepStrictEqual(stopCells(192, [11, 20]), [10, 19], 'three cells: 10-12 about 11, 19-21 about 20');
        assert.deepStrictEqual(stopCells(256, [11, 20]), [10, 19], 'four cells: 10-13, not ten and a half');
        assert.deepStrictEqual(stopCells(320, [11, 20]), [9, 18], 'five cells: 9-13 about 11');
        assert.deepStrictEqual(stopCells(192, [11, 20], -1), [19, 10], 'the way back: the far stop first');
        // a line that is not a shuttle keeps its half cells (the existing timetable tests hold the rest of it)
        const loose = T.plan(T.line({ ...def, shuttle: false }, [], null, 60), { GS, width: 256, worldWidth: 60 * GS, dir: 1 });
        assert.deepStrictEqual(plain(halts(loose).map((l) => l.x0 / GS)), [9.5, 18.5]);
        assert.ok(!loose.shuttle && T.at(loose, 0).alpha === 0 && halts(loose).length === 2, 'and still fades in at its terminus, with no layover');

        // the trip ends standing at the terminus it ran to, for `headway`, and the car is never faded
        for (const dir of [1, -1]) {
            const plan = T.plan(line, { GS, width: 192, worldWidth: 60 * GS, dir });
            assert.strictEqual(plan.shuttle, true);
            assert.deepStrictEqual([plan.fromX, plan.toX], dir > 0 ? [4 * GS, 25 * GS] : [25 * GS, 4 * GS], 'terminus to terminus, on the rails');
            const last = plan.legs[plan.legs.length - 1];
            assert.deepStrictEqual([last.x0, last.x1, last.t1 - last.t0, last.t1], [plan.toX, plan.toX, 8000, plan.duration], 'a layover of the headway');
            assert.deepStrictEqual(plain(halts(plan).map((l) => l.t1 - l.t0)), [5000, 5000, 8000]);
            let prev = T.at(plan, 0);
            assert.deepStrictEqual([prev.x, prev.alpha, prev.stopped], [plan.fromX, 1, false]);
            for (let ms = 50; ms <= plan.duration; ms += 50) {
                const at = T.at(plan, ms);
                assert.strictEqual(at.alpha, 1, `faded at ${ms}ms`);
                assert.ok((at.x - prev.x) * dir >= -1e-9 && Math.abs(at.x - prev.x) <= 192 * 0.05 * 1.5 + 1e-6, `at ${ms}ms: ${prev.x} -> ${at.x}`);
                prev = at;
            }
            const end = T.at(plan, plan.duration - 1);
            assert.deepStrictEqual([end.x, end.stopped, end.alpha], [plan.toX, true, 1], 'standing at the far terminus');
        }

        // the car enters the room standing at its first stop: the same cells whichever way it then sets off
        const one = T.line({ ...def, stops: [11] }, [], null, 60);
        const [e, w] = [1, -1].map((dir) => T.plan(one, { GS, width: 192, worldWidth: 60 * GS, dir }));
        for (const plan of [e, w]) {
            const first = T.at(plan, T.firstHalt(plan));
            assert.deepStrictEqual([first.x, first.stopped], [10 * GS, true]);
            assert.ok(T.firstHalt(plan) > 0 && !T.at(plan, T.firstHalt(plan) - 1).stopped, 'the first instant of the halt');
        }
        // no stop: the first halt is the layover; a plan that never stands (not a shuttle, no stops) starts at 0
        const bare = T.plan(T.line({ ...def, stops: [] }, [], null, 60), { GS, width: 192, worldWidth: 60 * GS, dir: 1 });
        assert.strictEqual(T.firstHalt(bare), bare.legs[bare.legs.length - 1].t0);
        assert.strictEqual(T.firstHalt(T.plan(T.line({ ...def, shuttle: false, stops: [] }, [], null, 60), { GS, width: 192, worldWidth: 60 * GS, dir: 1 })), 0);
    });

    test('a car is mirrored only against the way its art heads, and the cells under it are its footprint (#245)', () => {
        const T = trams();
        // art heading east (the default, and every line before #245): mirrored going west, first trip east
        assert.deepStrictEqual([T.flipped(1), T.flipped(-1), T.flipped(1, 1), T.flipped(-1, 1)], [false, true, false, true]);
        assert.deepStrictEqual([0, 1, 2, 3].map((trip) => T.direction(trip)), [1, -1, 1, -1]);
        assert.deepStrictEqual([0, 1, 2, 3].map((trip) => T.direction(trip, 1)), [1, -1, 1, -1]);
        // art heading west: the first trip is west and unmirrored (the head lamp leads), mirrored on the way back
        assert.deepStrictEqual([0, 1, 2, 3].map((trip) => T.direction(trip, -1)), [-1, 1, -1, 1]);
        assert.deepStrictEqual([T.flipped(-1, -1), T.flipped(1, -1)], [false, true]);
        for (const faces of [1, -1]) assert.strictEqual(T.flipped(T.direction(0, faces), faces), false, 'a car sets off as it is drawn');
        // the headlight is on the leading end either way: the lights follow the direction, not the art
        const [, headE] = T.lights(320, 128, 1, 64), [, headW] = T.lights(320, 128, -1, 64);
        assert.ok(headE.x > 160 && headW.x < 160 && headE.x + headW.x === 320);

        // the cells under a car: its art's width from its left edge, its height up from the rail row
        assert.deepStrictEqual(plain(T.footprint(21, 19 * 64, 64, 320, 128)), { x0: 19, x1: 23, y0: 20, y1: 21 });
        assert.deepStrictEqual(plain(T.footprint(16, 10 * 64, 64, 192, 128)), { x0: 10, x1: 12, y0: 15, y1: 16 });
        assert.deepStrictEqual(plain(T.footprint(16, 47 * 64, 64, 256, 128)), { x0: 47, x1: 50, y0: 15, y1: 16 });
        assert.deepStrictEqual(plain(T.footprint(5, 0, 64, 64, 64)), { x0: 0, x1: 0, y0: 5, y1: 5 });
    });

    test('a standing shuttle is solid over its cells; a moving car, and any other line\'s, is nobody\'s obstacle (#245)', () => {
        const T = trams();
        const GS = 64, image = { width: 192, height: 128 };
        const def = { row: 16, from: 4, to: 27, sprite: 'c', shuttle: true, stops: [11] };
        const state = (d, ms) => {
            const line = T.line(d, [], null, 60), plan = T.plan(line, { GS, width: 192, worldWidth: 60 * GS, dir: 1 });
            return { line, plan, image, t: ms === 'halt' ? T.firstHalt(plan) + 100 : ms };
        };
        const mover = (...lines) => Object.assign(Object.create(T.prototype), { scene: { GRID_SIZE: GS }, lines });
        const cellsOf = (m) => {
            const out = [];
            for (let y = 13; y <= 18; y++) for (let x = 0; x < 60; x++) if (m.carAt(x, y)) out.push(`${x},${y}`);
            return out;
        };
        const standing = state(def, 'halt');
        assert.deepStrictEqual(cellsOf(mover(standing)), ['10,15', '11,15', '12,15', '10,16', '11,16', '12,16'], 'the cells of its art, at its stop');
        assert.strictEqual(mover(standing).carAt(11, 16), standing, 'the answer is the line\'s state: what a rider keeps');
        // at the terminus it ran to (the layover) it is as solid
        const end = state(def, 0);
        end.t = end.plan.duration - 100;
        assert.deepStrictEqual(cellsOf(mover(end)), ['25,15', '26,15', '27,15', '25,16', '26,16', '27,16']);
        // moving: nothing
        assert.deepStrictEqual(cellsOf(mover(state(def, 500))), []);
        // a line that is not a shuttle is decoration even while it stands at a stop
        const loose = state({ ...def, shuttle: false }, 'halt');
        assert.ok(T.at(loose.plan, loose.t).stopped);
        assert.deepStrictEqual(cellsOf(mover(loose)), []);
        // a line whose car is not in the street (its texture was not loaded, or it was cleared) has none
        assert.deepStrictEqual(cellsOf(mover({ ...standing, image: null })), []);
        assert.deepStrictEqual(cellsOf(mover({ ...standing, plan: null })), []);
        assert.deepStrictEqual(cellsOf(mover()), []);
        // two lines: each answers for its own car
        const east = state({ ...def, from: 33, to: 55, stops: [48] }, 'halt');
        assert.strictEqual(mover(standing, east).carAt(48, 15), east);
        assert.strictEqual(mover(standing, east).carAt(11, 15), standing);
    });

    test('the towns\' cars are shuttles on their rails, clear of everything, with a way off on both sides of every halt (#245)', () => {
        const T = trams(), c = cfg();
        checkTramways(T, c);
        // the three that used to be tiles: where each first stands is where its tile stood
        const first = (roomKey, sprite) => {
            const room = c.rooms[roomKey], def = room.tramways.find((t) => t.sprite === sprite);
            assert.ok(def && def.shuttle === true, `${roomKey} has no shuttle ${sprite}`);
            const meta = c.spriteMetadata[sprite], w = Math.round(0.5 / meta.anchorX), h = Math.round(0.5 / meta.anchorY);
            const line = T.line(def, [], null, room.worldWidth / 64);
            const plan = T.plan(line, { GS: 64, width: w * 64, worldWidth: room.worldWidth, dir: T.direction(0, line.faces) });
            assert.strictEqual(T.flipped(plan.dir, line.faces), false, `${sprite} first stands as it is drawn`);
            return [plain(T.footprint(line.row, T.at(plan, T.firstHalt(plan)).x, 64, w * 64, h * 64)), line];
        };
        const [toyama, toyamaLine] = first('Toyama', 'toyama-tram_0_0');
        assert.deepStrictEqual(toyama, { x0: 19, x1: 23, y0: 20, y1: 21 });
        assert.deepStrictEqual([toyamaLine.faces, toyamaLine.name], [-1, 'tram'], 'drawn heading west');
        const [cable, cableLine] = first('SanFranbourne', 'sfb-cable-car_0_0');
        assert.deepStrictEqual(cable, { x0: 10, x1: 12, y0: 15, y1: 16 });
        assert.deepStrictEqual([cableLine.faces, cableLine.name, cableLine.stops.length], [1, 'cable car', 2]);
        const [tram, tramLine] = first('SanFranbourne', 'sfb-tram_0_0');
        assert.deepStrictEqual(tram, { x0: 47, x1: 50, y0: 15, y1: 16 });
        assert.deepStrictEqual([tramLine.faces, tramLine.name], [-1, 'tram']);

        // the check bites: each thing it asks of a shuttle, broken
        const car = 'sfb-cable-car_0_0';     // 3 x 2 cells
        const room = (tramways, solid) => ({ rooms: { R: { worldWidth: 40 * 64, worldHeight: 30 * 64, tramways,
            layers: [{ name: 'Colliders', tiles: Object.fromEntries((solid || []).map((xy) => [xy, 0])) }] } },
            tilePalette: ['collider'], spriteMetadata: c.spriteMetadata });
        const ok = { row: 16, from: 4, to: 27, sprite: car, shuttle: true, stops: [11] };
        const rowOf = (y, from, to) => { const out = []; for (let x = from; x <= to; x++) out.push(`${x},${y}`); return out; };
        checkTramways(T, room([ok]));
        checkTramways(T, room([ok, { ...ok, from: 28, to: 36, stops: [] }]));     // two lines end to end on one row
        // one free cell beside each halt, on each side, is enough
        checkTramways(T, room([ok], [...rowOf(14, 4, 27).filter((xy) => !['5,14', '11,14', '26,14'].includes(xy)),
            ...rowOf(17, 4, 27).filter((xy) => !['4,17', '12,17', '27,17'].includes(xy))]));
        const bad = (tramways, solid, said, why) => assert.throws(() => checkTramways(T, room(tramways, solid)),
            (e) => e instanceof assert.AssertionError && said.test(e.message), why);
        bad([ok, { ...ok, from: 27, to: 36, stops: [] }], [], /tramway 1 shares cells of row 16/, 'two lines sharing a cell of the row');
        bad([{ ...ok, shuttle: false }, { ...ok, sprite: 'sfb-tram_0_0' }], [], /tramway 1 shares cells/, 'a shuttle under another line');
        bad([{ ...ok, from: 0 }], [], /is a line that can run/, 'a shuttle that runs off the map is no line');
        bad([ok], ['18,16'], /runs over 18,16/, 'something solid on the rails');
        bad([ok], ['18,15'], /runs over 18,15/, 'something solid on the car\'s upper row');
        bad([ok], rowOf(14, 10, 12), /north side of the halt on 10\.\.12/, 'the stop walled in on the north side');
        bad([ok], rowOf(17, 10, 12), /south side of the halt on 10\.\.12/, 'the stop walled in on the south side');
        bad([ok], rowOf(17, 4, 6), /south side of the halt on 4\.\.6/, 'the west terminus walled in on the south side');
        bad([ok], rowOf(14, 25, 27), /north side of the halt on 25\.\.27/, 'the east terminus walled in on the north side');
        bad([{ ...ok, row: 1 }], [], /north side of the halt/, 'against the top of the map: no north side');
    });

    test('the streetcar and the glow table are loaded and hooked up', () => {
        const html = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        for (const f of ['src/utils/Glows.js', 'src/AmbientTrams.js']) assert.ok(html.includes(`'${f}'`), `${f} is in index.html`);
        assert.ok(html.indexOf('src/utils/Glows.js') < html.indexOf('src/DayNight.js'));
        assert.ok(/ambientTrams\.onRoomChange\(newRoom\)/.test(src('systems/RoomManager.js')));
        assert.ok(/ambientTrams\.update\(/.test(src('GameScene.js')));
    });
};
