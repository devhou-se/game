// Issue #307 (part 2 of #290): Kanazawa's ten building fronts of tools/generate_kanazawa_art.py are drawn in
// the GuttyKreum house look (docs/generators-and-checks.md): pixel-doubled, only the sheets' colours (at most
// 24, none on half the sprite), an ink or navy silhouette, no lit window, rectangles and pixels only. The tool
// is not in check_generators.ART_TOOLS yet, so the last test is the guard that it rebuilds them.
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

    test('kanazawa art: generate_kanazawa_art.py rebuilds the ten committed fronts (#307)', () => {
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
        const run = spawnSync('python3', ['-c', snippet, JSON.stringify(Object.keys(FRONTS))], { cwd: GV2, encoding: 'utf8',
            timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout.trim().split('\n').pop());
        if (!out.pillow) return;            // no Pillow here: check_generators.py lists the art tools as skip too
        assert.deepStrictEqual(out.differ, [], 'the committed PNGs are what the tool draws');
    });
};
