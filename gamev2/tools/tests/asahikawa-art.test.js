// Issue #310 (part of #289): Asahikawa's own art (tools/generate_asahikawa_art.py) is drawn in the GuttyKreum
// house look by one finisher: sheet colours only, the pack's dark glass lit only by the glow spots at night,
// lamps the pack's dim gold, snow shaded in the pack's blues, flat roofs seen from above on the shop row. The
// 52 keys keep their sizes, so no map changes.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPR = path.join(GV2, 'assets', 'sprites');
    const load = (key) => png.decode(fs.readFileSync(path.join(SPR, `${key}.png`)));
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const colours = ({ data }) => {
        const n = new Map();
        for (let i = 0; i < data.length; i += 4) if (data[i + 3]) n.set(hex(data, i), (n.get(hex(data, i)) || 0) + 1);
        return n;
    };
    // the 34 pieces and their sizes in cells, as PIECES has them
    const PIECES = {
        'asahikawa-station-front_0_0': [10, 5], 'heiwa-shop-sake_0_0': [3, 4], 'heiwa-shop-woodcraft_0_0': [4, 3],
        'heiwa-shop-bakery_0_0': [3, 4], 'heiwa-shop-books_0_0': [3, 3], 'ice-sculpture-crane_0_0': [2, 2],
        'ice-sculpture-owl_0_0': [1, 2], 'heiwa-bench_0_0': [2, 1], 'heiwa-lamp-post_0_0': [1, 2],
        'ramen-shoyu-front_0_0': [4, 4], 'ramen-narrow-front_0_0': [2, 4], 'ramen-miso-front_0_0': [3, 4],
        'asahikawa-ramen-lanterns_0_0': [1, 2], 'asahikawa-ramen-gate_0_0': [3, 3], 'ramen-crates_0_0': [1, 2],
        'ramen-stockpot_0_0': [1, 2], 'asahibashi-deck_0_0': [2, 5], 'asahibashi-arch-w_0_0': [1, 5],
        'asahibashi-arch-e_0_0': [1, 5], 'asahibashi-brace_0_0': [4, 1], 'hokkaido-house-red_0_0': [3, 4],
        'hokkaido-house-blue_0_0': [3, 4], 'snow-fence-h_0_0': [1, 2], 'ice-crack-a_0_0': [1, 1],
        'ice-crack-b_0_0': [1, 1], 'ice-fishing-hole_0_0': [1, 1], 'ice-fishing-tent_0_0': [2, 2],
        'zoo-gate_0_0': [5, 4], 'zoo-fence-h_0_0': [1, 2], 'zoo-fence-end_0_0': [1, 2], 'zoo-ticket-booth_0_0': [2, 3],
        'penguin-walk-a_0_0': [2, 1], 'penguin-walk-b_0_0': [2, 1], 'zoo-seal-statue_0_0': [2, 2],
    };
    const ROLES = ['center', 'edge-n', 'edge-s', 'edge-e', 'edge-w', 'corner-ne', 'corner-nw', 'corner-se', 'corner-sw'];
    const GROUND = ['heiwa-paving-autotile', 'ramen-alley-autotile'];
    const SNOW_RAMP = ['fafcfd', 'ecfaff', 'd1e2eb', 'b7c3e3', '99a1ca', '8085b1'];

    // every opaque colour of the GuttyKreum sheets (the previews are screenshots, not the art)
    let sheetColours = null;
    const sheets = () => {
        if (sheetColours) return sheetColours;
        sheetColours = new Set();
        const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
            const p = path.join(dir, e.name);
            if (e.isDirectory()) walk(p);
            else if (e.name.endsWith('.png') && !e.name.startsWith('preview')) {
                const { data } = png.decode(fs.readFileSync(p));
                for (let i = 0; i < data.length; i += 4) if (data[i + 3] === 255) sheetColours.add(hex(data, i));
            }
        });
        walk(path.join(GV2, '..', 'art-source', 'GuttyKreum'));
        return sheetColours;
    };

    test('asahikawa art: the 34 pieces keep their sizes and are pixel-doubled, the ground tiles are 64x64 (#310)', () => {
        for (const [key, [w, h]] of Object.entries(PIECES)) {
            const im = load(key);
            assert.deepStrictEqual([im.width, im.height], [w * 64, h * 64], key);
            const at = (x, y) => (y * im.width + x) * 4;
            for (let y = 0; y < im.height; y += 2) for (let x = 0; x < im.width; x += 2) {
                const c = im.data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => im.data.readUInt32BE(at(x + dx, y + dy)) === c),
                    `${key}: (${x},${y}) is not a 2x2 block`);
            }
        }
        for (const fam of GROUND) for (const r of ROLES) {
            const im = load(`${fam}_${r}`);
            assert.deepStrictEqual([im.width, im.height], [64, 64], `${fam}_${r}`);
        }
    });

    test('asahikawa art: every colour is a sheet colour; an edge tile may also hold the snow tile\'s own (#310)', () => {
        const known = sheets();
        const snow = colours(load('snow-autotile_center'));
        for (const key of Object.keys(PIECES).concat(GROUND.map((f) => `${f}_center`))) {
            for (const c of colours(load(key)).keys()) assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
        }
        for (const fam of GROUND) for (const r of ROLES.filter((r) => r !== 'center')) {
            for (const c of colours(load(`${fam}_${r}`)).keys()) {
                assert.ok(known.has(c) || snow.has(c), `${fam}_${r}: ${c} is in no sheet and not the snow tile's`);
            }
        }
    });

    test('asahikawa art: at most 32 colours a piece, none covering half of it (#310)', () => {
        for (const key of Object.keys(PIECES)) {
            const n = colours(load(key));
            const opaque = [...n.values()].reduce((a, b) => a + b, 0);
            assert.ok(n.size <= 32, `${key}: ${n.size} colours`);
            for (const [c, k] of n) assert.ok(k * 2 <= opaque, `${key}: ${c} covers ${k} of ${opaque} pixels`);
        }
    });

    test('asahikawa art: no lit yellow or plain white, the lamp is dim gold, the two flat roofs are slate under shaded snow (#310)', () => {
        for (const key of Object.keys(PIECES)) {
            const n = colours(load(key));
            for (const c of ['f6dc8c', 'f9c22e', 'ffffff', 'f2f5fb', 'c9d6ea']) assert.ok(!n.has(c), `${key} holds ${c}`);
        }
        assert.ok(colours(load('heiwa-lamp-post_0_0')).has('c6a663'), 'the lamp is the pack\'s dim gold');
        for (const key of ['heiwa-shop-books_0_0', 'heiwa-shop-woodcraft_0_0']) {
            const im = load(key);
            const top = colours({ data: im.data.subarray(0, im.width * 32 * 4) });
            assert.ok(top.has('5b6c79'), `${key}: no slate roof above row 32`);
            assert.ok(SNOW_RAMP.filter((c) => top.has(c)).length >= 4, `${key}: the snow on its roof is not shaded`);
        }
    });

    test('asahikawa art: the tool blends no colours and leaves the shared Hokkaido modules alone (#310)', () => {
        const src = fs.readFileSync(path.join(GV2, 'tools', 'generate_asahikawa_art.py'), 'utf8');
        assert.ok(!/\bmix\(/.test(src), 'a mix() call is left');
        assert.ok(!/\bgenerate_(hokkaido|sapporo_art)\.\w+\s*=[^=]/.test(src), 'it assigns into a shared module');
        assert.ok(/form\(im, A_SNOW, A_SNOW_OLD\); glaze\(im\); repaint\(im, A_SWAP\); settle\(im\)/.test(src), 'the finisher');
    });
};
