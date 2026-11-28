// Issue #343 (part 1 of #339, under #288): Sendai's seven downtown pieces of tools/generate_sendai_town_art.py
// (the two keyaki, the Jozenji bronze, the gyutan grill, the zunda shop, the izakaya and the mid-rise) are
// drawn in the GuttyKreum house look (docs/generators-and-checks.md): pixel-doubled, only the sheets'
// colours, an ink silhouette, dark glass, gold only as the pack's dim c6a663, rectangles and pixels only.
// Their manifest rows (PIECES) are unchanged. The tool is not in check_generators.ART_TOOLS, so the last test
// is the guard that it still draws every committed PNG it owns.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPR = path.join(GV2, 'assets', 'sprites');
    const TOOL = path.join(GV2, 'tools', 'generate_sendai_town_art.py');
    const PIECES = {                        // key -> size in cells
        'sendai-zelkova-a_0_0': [3, 4], 'sendai-zelkova-b_0_0': [3, 4], 'sendai-jozenji-statue_0_0': [2, 3],
        'sendai-gyutan_0_0': [4, 4], 'sendai-zunda_0_0': [3, 3], 'sendai-izakaya_0_0': [3, 4],
        'sendai-midrise_0_0': [4, 6],
    };
    const SHADED = ['sendai-zelkova-a_0_0', 'sendai-zelkova-b_0_0', 'sendai-jozenji-statue_0_0'];
    const BUILDERS = ['zelkova', 'jozenji_statue', 'gyutan', 'zunda', 'izakaya', 'midrise',
        'bough', 'kawara', 'slab_roof', 'on_shade', 'akachochin', 'edamame', 'chochin', 'roundel'];
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const load = (key) => png.decode(fs.readFileSync(path.join(SPR, `${key}.png`)));
    const counts = (key) => {
        const { data } = load(key);
        const n = new Map();
        let opaque = 0;
        for (let i = 0; i < data.length; i += 4) {
            if (data[i + 3] !== 255) continue;
            opaque++;
            n.set(hex(data, i), (n.get(hex(data, i)) || 0) + 1);
        }
        return { n, opaque };
    };

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

    test('sendai town art: the seven downtown pieces keep their sizes, pixel-doubled, alpha 0 or 255 but the shade (#343)', () => {
        for (const [key, [cw, ch]] of Object.entries(PIECES)) {
            const { width: w, height: h, data } = load(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
                const a = data[at(x, y) + 3];
                if (a === 0 || a === 255) continue;
                assert.ok(SHADED.includes(key) && a === 90 && hex(data, at(x, y)) === '2a3151', `${key}: (${x},${y}) is half clear`);
            }
        }
    });

    test('sendai town art: the seven use sheet colours only, 16 a tree or the statue and 24 a building, none on half (#343)', () => {
        const known = sheets();
        for (const key of Object.keys(PIECES)) {
            const { n, opaque } = counts(key);
            assert.ok(n.size <= (SHADED.includes(key) ? 16 : 24), `${key}: ${n.size} colours`);
            for (const [c, k] of n) {
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
                assert.ok(k * 2 <= opaque, `${key}: ${c} covers ${k} of ${opaque} pixels`);
            }
            for (const bad of ['f6dc8c', 'f2c66a', 'f9c22e', '2b373c', '000000', 'ffffff']) assert.ok(!n.has(bad), `${key}: ${bad}`);
            if (!key.includes('zelkova')) {      // on the trees f3d890 is the lit top of the gold ramp
                assert.ok((n.get('f3d890') || 0) < opaque * 0.03, `${key}: f3d890 on ${n.get('f3d890')} of ${opaque}`);
            }
        }
    });

    test('sendai town art: the seven are edged in ink (#343)', () => {
        for (const key of Object.keys(PIECES)) {
            const { width: w, height: h, data } = load(key);
            const clear = (x, y) => x >= 0 && y >= 0 && x < w && y < h && data[(y * w + x) * 4 + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (data[(y * w + x) * 4 + 3] !== 255 || ![[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) continue;
                const c = hex(data, (y * w + x) * 4);
                assert.strictEqual(c, '0a1627', `${key}: (${x},${y}) is on the silhouette and ${c}`);
            }
        }
    });

    test('sendai town art: dark glass, dim gold, and the keyaki ramps run into teal and purple (#343)', () => {
        const glass = { 'sendai-zunda_0_0': [3000, 200], 'sendai-izakaya_0_0': [2000, 150], 'sendai-midrise_0_0': [10000, 800] };
        for (const [key, [g, glare]] of Object.entries(glass)) {
            const { n } = counts(key);
            assert.ok((n.get('2c2d51') || 0) >= g, `${key}: 2c2d51 on ${n.get('2c2d51')}`);
            assert.ok((n.get('4b6396') || 0) >= glare, `${key}: 4b6396 on ${n.get('4b6396')}`);
        }
        for (const key of ['sendai-gyutan_0_0', 'sendai-izakaya_0_0', 'sendai-midrise_0_0']) {
            assert.ok(counts(key).n.has('c6a663'), `${key}: no c6a663`);
        }
        const a = counts('sendai-zelkova-a_0_0').n, b = counts('sendai-zelkova-b_0_0').n;
        for (const [tree, n] of [['-a', a], ['-b', b]]) {
            for (const c of ['3c396d', '508582']) assert.ok(n.has(c), `zelkova${tree}: no ${c}`);
        }
        assert.ok(a.has('c6a663'), 'zelkova-a is gold');
        assert.ok(b.has('ce6a42'), 'zelkova-b is russet');
    });

    test('sendai town art: the downtown builders draw with rectangles and pixels only (#343)', () => {
        const src = fs.readFileSync(TOOL, 'utf8').split('\n');
        for (const name of BUILDERS) {
            const start = src.findIndex((l) => l.startsWith(`def ${name}(`));
            assert.ok(start >= 0, `def ${name}`);
            const end = src.findIndex((l, i) => i > start && /^(def |[A-Z_]+ = |# ==)/.test(l));
            const body = src.slice(start, end < 0 ? undefined : end).join('\n');
            for (const call of ['.polygon(', '.ellipse(', '.arc(', '.pieslice(', '.chord(', '.line(', 'blob(', 'puff(', 'grounded(']) {
                assert.ok(!body.includes(call), `${name} calls ${call}`);
            }
            assert.ok(!/(^|[^_\w])roof\(/m.test(body), `${name} calls roof()`);
        }
    });

    const py = (lines, args = []) => {      // runs a snippet in gamev2/ with tools/ on the path; null without Pillow
        const run = spawnSync('python3', ['-c', lines.join('\n'), ...args], { cwd: GV2, encoding: 'utf8',
            timeout: 180000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout.trim().split('\n').pop());
        return out.pillow ? out : null;     // no Pillow here: check_generators.py lists the art tools as skip too
    };
    const PILLOW = ['import json, sys', 'try:', '    from PIL import Image', 'except ImportError:',
        '    print(json.dumps({"pillow": False})); sys.exit(0)', 'import generate_sendai_town_art as s'];

    test('sendai town art: PIECES still gives the seven their size, door, solid and glow spots (#343)', () => {
        const out = py([...PILLOW,
            'keys = json.loads(sys.argv[1])',
            'rows = {k: {"size": list(size), "door": m.get("door"), "solid": m.get("solid"), "lit": m.get("lit")}',
            '        for k, _fn, size, _dist, m, _desc in s.PIECES if k in keys}',
            'print(json.dumps({"pillow": True, "rows": rows}))'], [JSON.stringify(Object.keys(PIECES))]);
        if (!out) return;
        const W = '#f6dc8c', R = '#d16b56';
        const rows = (w, r0, r1) => { const o = []; for (let r = r0; r <= r1; r++) for (let c = 0; c < w; c++) o.push([c, r]); return o; };
        const want = {
            'sendai-zelkova-a_0_0': { size: [3, 4], door: null, solid: [[1, 3]], lit: null },
            'sendai-zelkova-b_0_0': { size: [3, 4], door: null, solid: [[1, 3]], lit: null },
            'sendai-jozenji-statue_0_0': { size: [2, 3], door: null, solid: rows(2, 2, 2), lit: null },
            'sendai-gyutan_0_0': { size: [4, 4], door: [[2, 3]], solid: rows(4, 2, 3),
                lit: [[1.1, 3.45, '#f0903a', 1.0, 0.6], [2.45, 3.3, W, 0.7], [3.2, 2.95, R, 0.6, 0.6], [1.6, 1.45, '#f0d98c', 1.0, 0.3]] },
            'sendai-zunda_0_0': { size: [3, 3], door: [[2, 2]], solid: rows(3, 1, 2), lit: [[1.0, 2.1, W, 1.0]] },
            'sendai-izakaya_0_0': { size: [3, 4], door: [[1, 3]], solid: rows(3, 2, 3),
                lit: [[0.8, 1.35, W, 0.9], [2.1, 1.35, W, 0.9], [1.5, 2.6, '#ffd9a0', 1.5, 0.45], [0.7, 3.2, W, 0.8], [2.2, 3.05, R, 0.6, 0.6]] },
            'sendai-midrise_0_0': { size: [4, 6], door: [[1, 5], [2, 5]], solid: rows(4, 4, 5),
                lit: [[2.0, 0.3, '#ffd24a', 1.4, 0.5], [0.6, 5.4, W, 0.9], [3.4, 5.4, W, 0.9], [2.0, 5.0, '#f9c22e', 1.2, 0.5], [3.25, 2.5, '#ff6a5a', 1.0, 0.3]] },
        };
        assert.deepStrictEqual(out.rows, want);
    });

    test('sendai town art: generate_sendai_town_art.py draws every committed PNG it owns (#343)', () => {
        const out = py([...PILLOW,
            'differ = []',
            'for key, fn in s.SPRITES.items():',
            '    im = fn()',
            '    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)',
            '    if im.tobytes() != Image.open("assets/sprites/%s.png" % key).convert("RGBA").tobytes():',
            '        differ.append(key)',
            'print(json.dumps({"pillow": True, "n": len(s.SPRITES), "differ": differ}))']);
        if (!out) return;
        assert.strictEqual(out.n, 102, 'the tool owns 102 PNGs');
        assert.deepStrictEqual(out.differ, [], 'the committed PNGs are what the tool draws');
    });
};
