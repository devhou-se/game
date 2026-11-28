// The placeholders for Tokyo Tower, Tokyo Station and Tsutenkaku (issues #70, #271): the team's line drawings
// (../art-source/line-art/), painted by rule (tools/line_art.py through tools/generate_tokyo_art.py and
// tools/generate_tsutenkaku.py) until the team's own art arrives. A sprite is its drawing with colour laid on,
// outline and lines unchanged; the map, the prefabs and config.json are as they were, so the pictures have to
// fit them. These are the rules that keep them fitting, for this art and for what replaces it.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const png = require(path.join(GV2, 'tools', 'png'));
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const CELL = 64;
    const images = {};
    const image = (key) => images[key] || (images[key] = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png'))));
    const alpha = (im, x, y) => im.data[(y * im.width + x) * 4 + 3];
    // how much of a box of the picture is drawn, 0..1
    const drawn = (im, x0, y0, x1, y1) => {
        let n = 0;
        for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) if (alpha(im, x, y)) n++;
        return n / ((x1 - x0) * (y1 - y0));
    };
    const cell = (im, cx, cy) => drawn(im, cx * CELL, cy * CELL, (cx + 1) * CELL, (cy + 1) * CELL);
    const colours = (im) => {
        const seen = new Set();
        for (let i = 0; i < im.data.length; i += 4) {
            if (im.data[i + 3] === 255) seen.add((im.data[i] << 16) | (im.data[i + 1] << 8) | im.data[i + 2]);
        }
        return seen.size;
    };
    const SIZES = { 'tokyo-tower_0_0': [512, 960], 'tokyo-tower-feet': [512, 192], 'tokyo-station_0_0': [2624, 512], 'tsutenkaku_0_0': [512, 832] };

    test('landmark placeholders: the four pictures keep their sizes and their anchors (#70)', () => {
        for (const [key, [w, h]] of Object.entries(SIZES)) {
            const im = image(key), m = cfg.spriteMetadata[key];
            assert.deepStrictEqual([im.width, im.height], [w, h], `${key} is ${im.width}x${im.height}, the map places it as ${w}x${h}`);
            assert.ok(m, `${key} has no spriteMetadata`);
            assert.strictEqual(m.anchorX, +(32 / w).toFixed(4), `${key}: anchorX is the centre of its top-left cell`);
            assert.strictEqual(m.anchorY, +(32 / h).toFixed(4), `${key}: anchorY is the centre of its top-left cell`);
        }
    });

    test('landmark placeholders: each sprite is its line drawing, painted (#271)', () => {
        const luma = (im, i) => 0.299 * im.data[i] + 0.587 * im.data[i + 1] + 0.114 * im.data[i + 2];
        for (const key of ['tokyo-station_0_0', 'tokyo-tower_0_0', 'tsutenkaku_0_0']) {
            const im = image(key);
            const art = png.decode(fs.readFileSync(path.join(GV2, '..', 'art-source', 'line-art', key + '.png')));
            assert.deepStrictEqual([im.width, im.height], [art.width, art.height], `${key} is not the size of its line drawing`);
            // the outline is the drawing's: not a pixel added, not a pixel cut away
            let differ = 0;
            const line = { sum: 0, n: 0 }, fill = { sum: 0, n: 0 };
            for (let i = 0; i < art.data.length; i += 4) {
                if (art.data[i + 3] !== im.data[i + 3]) differ++;
                if (!art.data[i + 3]) continue;
                const on = art.data[i] + art.data[i + 1] + art.data[i + 2] === 0 ? line : fill;
                on.sum += luma(im, i);
                on.n++;
            }
            assert.strictEqual(differ, 0, `${key}: ${differ} pixels are drawn where the line drawing is clear, or clear where it is drawn`);
            // and its lines are still lines: darker than what they enclose
            const lines = line.sum / line.n, fills = fill.sum / fill.n;
            assert.ok(lines <= fills - 30, `${key}: the drawing's lines average luma ${lines.toFixed(0)} and its fills ${fills.toFixed(0)}: the lines are lost`);
        }
    });

    test('landmark placeholders: Park\'s copy of Tokyo Tower\'s feet is the bottom three rows of the tower (#70)', () => {
        const tower = image('tokyo-tower_0_0'), feet = image('tokyo-tower-feet');
        const from = (tower.height - feet.height) * tower.width * 4;
        assert.ok(Buffer.from(feet.data).equals(Buffer.from(tower.data).subarray(from)), 'tokyo-tower-feet.png is not the bottom 192 rows of tokyo-tower_0_0.png: run tools/generate_tokyo_art.py');
    });

    test('landmark placeholders: none of them is line art (#70)', () => {
        for (const key of Object.keys(SIZES)) {
            const n = colours(image(key));
            assert.ok(n >= 12, `${key} has ${n} opaque colours: shaded art has a dozen or more`);
        }
    });

    test('landmark placeholders: you can see yourself between Tokyo Tower\'s feet and under Tsutenkaku\'s archway (#70)', () => {
        // the tower's open cells are the ones Palace leaves without a collider in its bottom two rows
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'tiled', 'palace.tmj'), 'utf8'));
        const solid = map.layers.find((l) => l.name === 'Colliders').data;
        const placed = map.layers.filter((l) => l.objects).flatMap((l) => l.objects).find((o) => o.name === 'tokyo-tower_0_0');
        assert.ok(placed, 'Palace places tokyo-tower_0_0');
        const ox = placed.x / CELL, oy = placed.y / CELL;
        assert.deepStrictEqual([ox, oy, placed.width / CELL, placed.height / CELL], [8, 6, 8, 15]);
        const tower = image('tokyo-tower_0_0');
        const open = [];
        for (const cy of [13, 14]) {
            for (let cx = 0; cx < 8; cx++) if (!solid[(oy + cy) * map.width + ox + cx]) open.push([cx, cy]);
        }
        assert.deepStrictEqual(open, [[2, 13], [3, 13], [4, 13], [5, 13], [1, 14], [2, 14], [3, 14], [4, 14], [5, 14], [6, 14]]);
        for (const [cx, cy] of open) {
            assert.ok(cell(tower, cx, cy) < 0.5, `tokyo-tower_0_0: cell (${cx},${cy}) is walked through and is ${Math.round(cell(tower, cx, cy) * 100)}% drawn`);
        }
        // and above its row of legs the tower is a narrow thing: most of the picture is clear to either side of it
        assert.ok(drawn(tower, 0, 0, tower.width, 12 * CELL) < 0.5);
        const tsutenkaku = image('tsutenkaku_0_0');
        for (const [cx, cy] of [[3, 12], [4, 12]]) {
            assert.ok(cell(tsutenkaku, cx, cy) < 0.5, `tsutenkaku_0_0: the archway cell (${cx},${cy}) is ${Math.round(cell(tsutenkaku, cx, cy) * 100)}% drawn`);
        }
    });

    test('landmark placeholders: Tokyo Station leaves the train behind its roof in view (#70, #63)', () => {
        // rows 0 and 1 hold only what stands above the roof: the end turrets, the two domes, the centre gable
        const station = image('tokyo-station_0_0');
        const tall = new Set([0, 4, 5, 6, 18, 19, 20, 21, 22, 34, 35, 36, 40]);
        for (let cx = 0; cx < 41; cx++) {
            if (tall.has(cx)) continue;
            for (const cy of [0, 1]) assert.strictEqual(cell(station, cx, cy), 0, `tokyo-station_0_0: cell (${cx},${cy}) would hide Palace's passing train`);
        }
    });

    test('landmark placeholders: Tokyo Station\'s forecourt is clear and its one door is drawn (#70)', () => {
        const station = image('tokyo-station_0_0');
        // Palace's shrub gardens, lamp posts and a vending machine stand inside the footprint, either side of the porch
        for (const cx of [16, 17, 18, 22, 23, 24]) {
            assert.strictEqual(cell(station, cx, 7), 0, `tokyo-station_0_0: forecourt cell (${cx},7) is drawn over`);
        }
        // the drawing's wing ends at the ground line, 40px into row 6: the gardens' upper halves show below it. (The small
        // towers either side of the centre block, columns 17..18 and 22..23, come down to the foot of row 6.)
        for (const cx of [16, 24]) {
            assert.strictEqual(drawn(station, cx * CELL, 6 * CELL + 40, (cx + 1) * CELL, 7 * CELL), 0, `tokyo-station_0_0: column ${cx} comes below the ground line`);
        }
        assert.ok(cell(station, 20, 7) > 0.5, 'tokyo-station_0_0: cell (20,7) is the door (Palace 27,9) and is not drawn');
        // Palace keeps the bottom row solid under the pavilions, columns 3..7 and 33..37 (#259): their feet are as wide as that
        for (const cx of [3, 7, 33, 37]) {
            assert.ok(cell(station, cx, 7) > 0.2, `tokyo-station_0_0: cell (${cx},7) is solid in Palace and next to nothing stands on it`);
        }
    });

    test('landmark placeholders: check_generators runs the tools that draw them (#70)', () => {
        const check = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/ART_TOOLS \+= \['generate_tokyo_art'\]/.test(check), 'generate_tokyo_art is not in ART_TOOLS');
        assert.ok(/'generate_tsutenkaku'/.test(check), 'generate_tsutenkaku is not in ART_TOOLS');
    });
};
