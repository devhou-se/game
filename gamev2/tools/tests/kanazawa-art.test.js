// Issue #307 (part 2 of #290): Kanazawa's ten building fronts of tools/generate_kanazawa_art.py are drawn in
// the GuttyKreum house look (docs/generators-and-checks.md): pixel-doubled, only the sheets' colours (at most
// 24, none on half the sprite), an ink or navy silhouette, no lit window, rectangles and pixels only. The tool
// is not in check_generators.ART_TOOLS yet, so the last test is the guard that it rebuilds them.
// Issue #385 (part 1 of #312): the castle's gate, turret, storehouse and five wall pieces and the Tsuzumi-mon
// are held to the same recipe, their wall pieces to their joins, and castle_wall() leaves nagamachi-wall* alone.
// Issue #386 (part 2 of #312): Kenrokuen's lanterns, pines, tea house, bridge, moss and nine path tiles are held
// to the recipe too, with 2a3151 at alpha 90 their one translucent colour, and the path tiles to their joins.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPR = path.join(GV2, 'assets', 'sprites');
    const TOOL = path.join(GV2, 'tools', 'generate_kanazawa_art.py');
    const FRONTS = {                        // key -> size in cells
        'chaya-front-a_0_0': [3, 4], 'chaya-front-b_0_0': [3, 4], 'chaya-front-c_0_0': [3, 4],
        'chaya-gold-leaf-shop_0_0': [4, 4], 'chaya-phono-museum_0_0': [3, 4],
        'katamachi-whisky-bar_0_0': [3, 5], 'katamachi-izakaya_0_0': [4, 4], 'katamachi-kissaten_0_0': [3, 4],
        'katamachi-yakitori_0_0': [3, 3], 'nagamachi-samurai-house_0_0': [5, 4],
    };
    const BUILDERS = ['chaya', 'gold_shop', 'phono_museum', 'whisky_bar', 'izakaya', 'kissaten', 'yakitori', 'samurai_house'];
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const load = (key) => png.decode(fs.readFileSync(path.join(SPR, `${key}.png`)));

    let sheetColours = null;                // every opaque colour of the GuttyKreum sheets (not the previews)
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

    test('kanazawa art: the ten fronts keep their sizes and are pixel-doubled, alpha 0 or 255 (#307)', () => {
        for (const [key, [cw, ch]] of Object.entries(FRONTS)) {
            const { width: w, height: h, data } = load(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
                assert.ok([0, 255].includes(data[at(x, y) + 3]), `${key}: (${x},${y}) is half clear`);
            }
        }
    });

    test('kanazawa art: the ten fronts use sheet colours only, at most 24, none on half, no lit window (#307)', () => {
        const known = sheets();
        for (const key of Object.keys(FRONTS)) {
            const { data } = load(key);
            const counts = new Map();
            let opaque = 0;
            for (let i = 0; i < data.length; i += 4) {
                if (!data[i + 3]) continue;
                opaque++;
                counts.set(hex(data, i), (counts.get(hex(data, i)) || 0) + 1);
            }
            assert.ok(counts.size <= 24, `${key}: ${counts.size} colours`);
            for (const [c, n] of counts) {
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
                assert.ok(n * 2 <= opaque, `${key}: ${c} covers ${n} of ${opaque} pixels`);
            }
            for (const lit of ['f6dc8c', 'f2c66a', 'f9c22e']) assert.ok(!counts.has(lit), `${key}: lit yellow ${lit}`);
            if (key !== 'chaya-gold-leaf-shop_0_0') {     // its wall is leaf; elsewhere f3d890 is a lamp's core
                assert.ok((counts.get('f3d890') || 0) < opaque * 0.03, `${key}: f3d890 on ${counts.get('f3d890')} of ${opaque}`);
            }
        }
    });

    test('kanazawa art: the ten fronts are edged in ink or navy above their stone foot (#307)', () => {
        for (const key of Object.keys(FRONTS)) {
            const { width: w, height: h, data } = load(key);
            const clear = (x, y) => x < 0 || y < 0 || x >= w || y >= h || data[(y * w + x) * 4 + 3] === 0;
            for (let y = 0; y < h - 8; y++) for (let x = 0; x < w; x++) {
                if (clear(x, y) || ![[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) continue;
                const c = hex(data, (y * w + x) * 4);
                assert.ok(['0a1627', '172459'].includes(c), `${key}: (${x},${y}) is on the silhouette and ${c}`);
            }
        }
    });

    test('kanazawa art: the eight builders draw with rectangles and pixels only (#307)', () => {
        const src = fs.readFileSync(TOOL, 'utf8').split('\n');
        for (const name of BUILDERS) {
            const start = src.findIndex((l) => l.startsWith(`def ${name}(`));
            assert.ok(start >= 0, `def ${name}`);
            let end = src.findIndex((l, i) => i > start && /^(def |[A-Z_]+ = |# ==)/.test(l));
            const body = src.slice(start, end < 0 ? undefined : end).join('\n');
            for (const call of ['.polygon(', '.ellipse(', '.arc(', '.pieslice(', '.chord(', 'shade(im']) {
                assert.ok(!body.includes(call), `${name} calls ${call}`);
            }
        }
    });

    const CASTLE = {                        // key -> size in cells
        'kanazawa-castle-gate_0_0': [4, 4], 'kanazawa-castle-turret_0_0': [4, 5],
        'kanazawa-castle-storehouse_0_0': [6, 3], 'kanazawa-tsuzumi-gate_0_0': [6, 5],
        'kanazawa-castle-wall_0_0': [1, 2], 'kanazawa-castle-wall-corner-e_0_0': [1, 2],
        'kanazawa-castle-wall-corner-w_0_0': [1, 2], 'kanazawa-castle-wall-v_0_0': [1, 2],
        'kanazawa-castle-wall-end_0_0': [1, 2],
    };
    const WALLS = Object.keys(CASTLE).filter((k) => k.startsWith('kanazawa-castle-wall'));
    const NAGA = ['', '-bare', '-corner-e', '-corner-w', '-v', '-end', '-gate'].map((s) => `nagamachi-wall${s}_0_0`);
    const CASTLE_BUILDERS = ['castle_gate', 'castle_turret', 'castle_storehouse', 'castle_wall', 'tsuzumi_gate',
        'drum_pillar', 'lead_band', 'lead_hip', 'plaster', 'musha', 'namako', 'stonework'];

    test('kanazawa art: the castle pieces keep their sizes and are pixel-doubled, alpha 0 or 255 (#385)', () => {
        for (const [key, [cw, ch]] of Object.entries(CASTLE)) {
            const { width: w, height: h, data } = load(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
                assert.ok([0, 255].includes(data[at(x, y) + 3]), `${key}: (${x},${y}) is half clear`);
            }
        }
    });

    test('kanazawa art: the castle pieces use sheet colours only, 16 a wall piece and 24 else, none on half (#385)', () => {
        const known = sheets();
        for (const key of Object.keys(CASTLE)) {
            const { data } = load(key);
            const counts = new Map();
            let opaque = 0;
            for (let i = 0; i < data.length; i += 4) {
                if (!data[i + 3]) continue;
                opaque++;
                counts.set(hex(data, i), (counts.get(hex(data, i)) || 0) + 1);
            }
            assert.ok(counts.size <= (WALLS.includes(key) ? 16 : 24), `${key}: ${counts.size} colours`);
            for (const [c, n] of counts) {
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
                assert.ok(n * 2 <= opaque, `${key}: ${c} covers ${n} of ${opaque} pixels`);
            }
            for (const bad of ['f6dc8c', 'f2c66a', 'f9c22e', '2b373c', '000000']) assert.ok(!counts.has(bad), `${key}: ${bad}`);
            assert.ok((counts.get('f3d890') || 0) < opaque * 0.03, `${key}: f3d890 on ${counts.get('f3d890')} of ${opaque}`);
        }
    });

    test('kanazawa art: the castle pieces are edged in ink, the canvas edge aside (#385)', () => {
        for (const key of Object.keys(CASTLE)) {
            const { width: w, height: h, data } = load(key);
            const clear = (x, y) => x >= 0 && y >= 0 && x < w && y < h && data[(y * w + x) * 4 + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (!data[(y * w + x) * 4 + 3] || ![[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) continue;
                const c = hex(data, (y * w + x) * 4);
                assert.strictEqual(c, '0a1627', `${key}: (${x},${y}) is on the silhouette and ${c}`);
            }
        }
    });

    test('kanazawa art: the castle wall pieces join each other (#385)', () => {
        const px = (key) => {
            const { width: w, data } = load(key);
            return { col: (x, y0, y1) => Array.from({ length: y1 - y0 + 1 }, (_, i) => data.readUInt32BE(((y0 + i) * w + x) * 4)),
                rows: (y0, y1) => data.subarray(y0 * w * 4, (y1 + 1) * w * 4) };
        };
        const k = (s) => `kanazawa-castle-wall${s}_0_0`;
        const h = px(k('')), v = px(k('-v')), end = px(k('-end')), ce = px(k('-corner-e')), cw = px(k('-corner-w'));
        assert.deepStrictEqual(ce.col(0, 22, 127), h.col(0, 22, 127), '-corner-e column 0 is the h piece\'s');
        assert.deepStrictEqual(cw.col(63, 22, 127), h.col(63, 22, 127), '-corner-w column 63 is the h piece\'s');
        assert.ok(end.rows(0, 35).equals(v.rows(0, 35)), '-end rows 0-35 are -v\'s');
        assert.ok(end.rows(64, 127).equals(v.rows(64, 127)), '-end rows 64-127 are -v\'s');
        assert.ok(ce.rows(0, 21).equals(v.rows(0, 21)), '-corner-e rows 0-21 are -v\'s');
        assert.ok(cw.rows(0, 21).equals(v.rows(0, 21)), '-corner-w rows 0-21 are -v\'s');
    });

    test('kanazawa art: the castle builders draw with rectangles and pixels only (#385)', () => {
        const src = fs.readFileSync(TOOL, 'utf8').split('\n');
        for (const name of CASTLE_BUILDERS) {
            const start = src.findIndex((l) => l.startsWith(`def ${name}(`));
            assert.ok(start >= 0, `def ${name}`);
            let end = src.findIndex((l, i) => i > start && /^(def |[A-Z_]+ = |# ==)/.test(l));
            const body = src.slice(start, end < 0 ? undefined : end).join('\n');
            for (const call of ['.polygon(', '.ellipse(', '.arc(', '.pieslice(', '.chord(', '.line(', 'shade(im']) {
                assert.ok(!body.includes(call), `${name} calls ${call}`);
            }
            assert.ok(!/\broof\(/.test(body), `${name} calls roof()`);
        }
    });

    const GARDEN = {                        // key -> size in cells
        'kenrokuen-kotoji_0_0': [2, 3], 'kenrokuen-kotoji-water_0_0': [2, 3],
        'kenrokuen-yukitsuri_0_0': [3, 4], 'kenrokuen-yukitsuri-small_0_0': [2, 3],
        'kenrokuen-teahouse_0_0': [4, 3], 'kenrokuen-bridge_0_0': [3, 1], 'garden-moss_0_0': [1, 1],
    };
    const PATH_ROLES = ['center', 'edge-n', 'edge-s', 'edge-e', 'edge-w', 'corner-nw', 'corner-ne', 'corner-sw', 'corner-se'];
    for (const r of PATH_ROLES) GARDEN[`garden-path-autotile_${r}`] = [1, 1];
    const STANDING = ['kenrokuen-kotoji_0_0', 'kenrokuen-kotoji-water_0_0', 'kenrokuen-yukitsuri_0_0',
        'kenrokuen-yukitsuri-small_0_0', 'kenrokuen-teahouse_0_0'];
    const FLAT = Object.keys(GARDEN).filter((k) => !STANDING.includes(k));   // the bridge and the ten ground tiles
    const GARDEN_BUILDERS = ['kotoji', 'g_rope', 'yukitsuri', 'teahouse', 'stone_bridge', 'moss_px', 'garden_moss',
        '_path_part', 'garden_path', 'spans', 'lerp_rows', 'cast', 'dots'];

    test('kanazawa art: the garden pieces keep their sizes and are pixel-doubled, clear, opaque or the shade (#386)', () => {
        for (const [key, [cw, ch]] of Object.entries(GARDEN)) {
            const { width: w, height: h, data } = load(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y)), a = data[at(x, y) + 3];
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
                assert.ok(a === 0 || a === 255 || (a === 90 && hex(data, at(x, y)) === '2a3151'), `${key}: (${x},${y}) alpha ${a}`);
                if (FLAT.includes(key)) assert.strictEqual(a, 255, `${key}: (${x},${y}) is not opaque`);
            }
        }
    });

    test('kanazawa art: the garden pieces use sheet colours only, 24 the tea house and 16 else, no lit yellow (#386)', () => {
        const known = sheets();
        for (const key of Object.keys(GARDEN)) {
            const { data } = load(key);
            const counts = new Map();
            let opaque = 0;
            for (let i = 0; i < data.length; i += 4) {
                if (data[i + 3] !== 255) continue;
                opaque++;
                counts.set(hex(data, i), (counts.get(hex(data, i)) || 0) + 1);
            }
            assert.ok(counts.size <= (key === 'kenrokuen-teahouse_0_0' ? 24 : 16), `${key}: ${counts.size} colours`);
            for (const [c, n] of counts) {
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
                // the ground tiles are one floor colour, as the pack's grass is
                if (STANDING.includes(key) || key === 'kenrokuen-bridge_0_0') assert.ok(n * 2 <= opaque, `${key}: ${c} covers ${n} of ${opaque} pixels`);
            }
            for (const bad of ['f6dc8c', 'f2c66a', 'f9c22e', '2b373c', '000000']) assert.ok(!counts.has(bad), `${key}: ${bad}`);
            assert.ok((counts.get('f3d890') || 0) < opaque * 0.03, `${key}: f3d890 on ${counts.get('f3d890')} of ${opaque}`);
        }
    });

    test('kanazawa art: the standing garden pieces are edged in ink or a water mark, the bridge inked along its sides (#386)', () => {
        for (const key of STANDING) {
            const { width: w, height: h, data } = load(key);
            const notOpaque = (x, y) => x >= 0 && y >= 0 && x < w && y < h && data[(y * w + x) * 4 + 3] !== 255;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (data[(y * w + x) * 4 + 3] !== 255 || ![[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => notOpaque(x + dx, y + dy))) continue;
                const c = hex(data, (y * w + x) * 4);
                assert.ok(['0a1627', '8ec2fa'].includes(c), `${key}: (${x},${y}) is on the silhouette and ${c}`);
            }
        }
        const { width: w, data } = load('kenrokuen-bridge_0_0');
        for (const y of [0, 1, 62, 63]) for (let x = 0; x < w; x++) {
            assert.strictEqual(hex(data, (y * w + x) * 4), '0a1627', `kenrokuen-bridge: (${x},${y})`);
        }
    });

    test('kanazawa art: the garden path tiles join the moss and each other (#386)', () => {
        const moss = load('garden-moss_0_0');
        const tile = (role) => load(`garden-path-autotile_${role}`);
        const at = (img, x, y) => img.data.readUInt32BE((y * img.width + x) * 4);
        const MOSS = ['357570', '488582', '6c8e7f', '2e4040'], GRAVEL = ['d7d0ba', 'eae9e8', 'cdc8c5', 'b3aaa0'];
        const kind = (img, x, y) => {
            const c = hex(img.data, (y * img.width + x) * 4);
            return MOSS.includes(c) ? 'moss' : (GRAVEL.includes(c) ? 'gravel' : 'stone');
        };
        for (const role of PATH_ROLES) {
            const t = tile(role), sides = role === 'center' ? '' : role.split('-')[1];
            for (let i = 0; i < 6; i++) for (let j = 0; j < 64; j++) {
                const pts = { n: [j, i], s: [j, 63 - i], w: [i, j], e: [63 - i, j] };
                for (const s of sides) {
                    const [x, y] = pts[s];
                    assert.strictEqual(at(t, x, y), at(moss, x, y), `${role}: (${x},${y}) on its ${s} side is not garden-moss's`);
                }
            }
        }
        const across = [['corner-nw', 'edge-n'], ['edge-n', 'edge-n'], ['edge-n', 'corner-ne'], ['corner-sw', 'edge-s'],
            ['edge-s', 'edge-s'], ['edge-s', 'corner-se'], ['edge-w', 'center'], ['center', 'edge-e']];
        for (const [a, b] of across) {
            const A = tile(a), B = tile(b);
            for (let y = 0; y < 64; y++) assert.strictEqual(kind(A, 63, y), kind(B, 0, y), `${a}|${b}: row ${y}`);
        }
        const down = [['corner-nw', 'edge-w'], ['edge-w', 'edge-w'], ['edge-w', 'corner-sw'], ['corner-ne', 'edge-e'],
            ['edge-e', 'edge-e'], ['edge-e', 'corner-se'], ['edge-n', 'center'], ['center', 'edge-s']];
        for (const [a, b] of down) {
            const A = tile(a), B = tile(b);
            for (let x = 0; x < 64; x++) assert.strictEqual(kind(A, x, 63), kind(B, x, 0), `${a}/${b}: column ${x}`);
        }
    });

    test('kanazawa art: the garden builders draw with rectangles and pixels only (#386)', () => {
        const src = fs.readFileSync(TOOL, 'utf8').split('\n');
        for (const name of GARDEN_BUILDERS) {
            const start = src.findIndex((l) => l.startsWith(`def ${name}(`));
            assert.ok(start >= 0, `def ${name}`);
            let end = src.findIndex((l, i) => i > start && /^(def |[A-Z_]+ = |# ==)/.test(l));
            const body = src.slice(start, end < 0 ? undefined : end).join('\n');
            for (const call of ['.polygon(', '.ellipse(', '.arc(', '.pieslice(', '.chord(', '.line(', 'shade(im',
                'blob(', 'math.sin', 'math.cos']) {
                assert.ok(!body.includes(call), `${name} calls ${call}`);
            }
            assert.ok(!/\broof\(/.test(body), `${name} calls roof()`);
        }
    });

    const rebuild = (keys) => {             // the keys the tool draws differently from the committed PNGs, or null without Pillow
        const snippet = [
            'import json, sys',
            'try:',
            '    from PIL import Image',
            'except ImportError:',
            '    print(json.dumps({"pillow": False})); sys.exit(0)',
            'import generate_kanazawa_art as k',
            'keys = json.loads(sys.argv[1])',
            'differ = []',
            'for key in keys:',
            '    im = k.SPRITES[key]()',
            '    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)',
            '    if im.tobytes() != Image.open("assets/sprites/%s.png" % key).convert("RGBA").tobytes():',
            '        differ.append(key)',
            'print(json.dumps({"pillow": True, "differ": differ}))',
        ].join('\n');
        const run = spawnSync('python3', ['-c', snippet, JSON.stringify(keys)], { cwd: GV2, encoding: 'utf8',
            timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout.trim().split('\n').pop());
        return out.pillow ? out.differ : null;  // no Pillow here: check_generators.py lists the art tools as skip too
    };

    test('kanazawa art: generate_kanazawa_art.py rebuilds the ten committed fronts (#307)', () => {
        const differ = rebuild(Object.keys(FRONTS));
        if (differ) assert.deepStrictEqual(differ, [], 'the committed PNGs are what the tool draws');
    });

    test('kanazawa art: generate_kanazawa_art.py rebuilds the castle pieces and leaves nagamachi-wall* alone (#385)', () => {
        const differ = rebuild([...Object.keys(CASTLE), ...NAGA]);
        if (differ) assert.deepStrictEqual(differ, [], 'the committed PNGs are what the tool draws');
    });

    test('kanazawa art: generate_kanazawa_art.py rebuilds the committed garden pieces (#386)', () => {
        const differ = rebuild(Object.keys(GARDEN));
        if (differ) assert.deepStrictEqual(differ, [], 'the committed PNGs are what the tool draws');
    });

    test('kanazawa art: a rerun of generate_kanazawa_art.py leaves the committed PNGs byte for byte (#384)', () => {
        // Into a copy of the committed sprites: every file whose pixels are unchanged is left as it is, even when
        // Pillow would encode it differently; a missing file is written and a file with other pixels rewritten.
        const snippet = [
            'import contextlib, io, json, os, shutil, sys, tempfile',
            'try:',
            '    from PIL import Image',
            'except ImportError:',
            '    print(json.dumps({"pillow": False})); sys.exit(0)',
            'import generate_kanazawa_art as k',
            'keys = sorted(k.SPRITES)',
            'tmp = tempfile.mkdtemp()',
            'try:',
            '    for key in keys:',
            '        shutil.copy("assets/sprites/%s.png" % key, tmp)',
            '    p = lambda key: os.path.join(tmp, key + ".png")',
            '    gone, other, reenc = keys[0], keys[1], keys[2]',
            '    os.remove(p(gone))',
            '    Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(p(other))',
            '    Image.open(p(reenc)).convert("RGBA").save(p(reenc), compress_level=0)',
            '    stamp = open(p(reenc), "rb").read()',
            '    k.SPR, sys.argv = tmp, ["generate_kanazawa_art.py"]',
            '    with contextlib.redirect_stdout(io.StringIO()):',
            '        k.main()',
            '    rewritten = [key for key in keys if key != reenc and open(p(key), "rb").read() != open("assets/sprites/%s.png" % key, "rb").read()]',
            '    print(json.dumps({"pillow": True, "rewritten": rewritten, "reenc_kept": open(p(reenc), "rb").read() == stamp}))',
            'finally:',
            '    shutil.rmtree(tmp)',
        ].join('\n');
        const run = spawnSync('python3', ['-c', snippet], { cwd: GV2, encoding: 'utf8',
            timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout.trim().split('\n').pop());
        if (!out.pillow) return;
        assert.ok(out.reenc_kept, 'a file with the same pixels in another encoding was rewritten');
        assert.deepStrictEqual(out.rewritten, [], 'files differ from the committed ones after a run');
    });
};
