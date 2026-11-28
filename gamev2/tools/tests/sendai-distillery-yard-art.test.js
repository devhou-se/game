// Issue #344 (part 2 of #339): Sendai's distillery-yard pieces of tools/generate_sendai_town_art.py (the still
// house, the cask rack, the red maple and Yamadera) are drawn in the GuttyKreum house look
// (docs/generators-and-checks.md): pixel-doubled, only the sheets' colours, an ink silhouette, no lit window,
// rectangles and pixels only, 2a3151 at alpha 90 the one translucent colour (the rack's and the maple's ground
// shade). Their placement data is pinned as it was, and the tool is not in check_generators.ART_TOOLS, so the
// last test is the guard that it rebuilds them.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPR = path.join(GV2, 'assets', 'sprites');
    const TOOL = path.join(GV2, 'tools', 'generate_sendai_town_art.py');
    const YARD = {                          // key -> size in cells
        'sendai-distillery-warehouse_0_0': [6, 4], 'sendai-cask-rack_0_0': [3, 2],
        'sendai-red-maple_0_0': [3, 4], 'sendai-yamadera_0_0': [6, 6],
    };
    const SHADED = ['sendai-cask-rack_0_0', 'sendai-red-maple_0_0'];     // the two with a ground shade
    const BUILDERS = ['dy_disc', 'dy_arch', 'dy_glazed', 'cask_end', 'pot_still', 'dy_stack', 'distillery_warehouse',
        'cask_rack', 'red_maple', 'dy_top', 'dy_hill_roof', 'yamadera'];
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

    const python = (snippet, args = []) => {     // the snippet's last line of JSON
        const run = spawnSync('python3', ['-c', snippet, ...args], { cwd: GV2, encoding: 'utf8',
            timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        return JSON.parse(run.stdout.trim().split('\n').pop());
    };

    test('sendai yard art: the four keep their sizes, pixel-doubled, alpha 0 or 255 but the ground shade (#344)', () => {
        for (const [key, [cw, ch]] of Object.entries(YARD)) {
            const { width: w, height: h, data } = load(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
                const a = data[at(x, y) + 3];
                if (a === 0 || a === 255) continue;
                assert.ok(SHADED.includes(key) && a === 90 && hex(data, at(x, y)) === '2a3151',
                    `${key}: (${x},${y}) is ${hex(data, at(x, y))} at alpha ${a}`);
            }
        }
    });

    test('sendai yard art: the four use sheet colours only, none on half, no lit window (#344)', () => {
        const known = sheets();
        for (const key of Object.keys(YARD)) {
            const { data } = load(key);
            const counts = new Map();
            let opaque = 0;
            for (let i = 0; i < data.length; i += 4) {
                if (data[i + 3] !== 255) continue;
                opaque++;
                counts.set(hex(data, i), (counts.get(hex(data, i)) || 0) + 1);
            }
            assert.ok(counts.size <= (SHADED.includes(key) ? 16 : 24), `${key}: ${counts.size} colours`);
            for (const [c, n] of counts) {
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
                assert.ok(n * 2 <= opaque, `${key}: ${c} covers ${n} of ${opaque} pixels`);
            }
            for (const c of ['f6dc8c', 'f2c66a', 'f9c22e', '2b373c', '000000']) assert.ok(!counts.has(c), `${key}: ${c}`);
            assert.ok((counts.get('f3d890') || 0) < opaque * 0.03, `${key}: f3d890 on ${counts.get('f3d890')} of ${opaque}`);
        }
    });

    test('sendai yard art: the four are edged in ink (#344)', () => {
        for (const key of Object.keys(YARD)) {
            const { width: w, height: h, data } = load(key);
            const clear = (x, y) => data[(y * w + x) * 4 + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (clear(x, y)) continue;
                const edge = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => {
                    const nx = x + dx, ny = y + dy;
                    return nx >= 0 && ny >= 0 && nx < w && ny < h && clear(nx, ny);
                });
                if (!edge) continue;
                const i = (y * w + x) * 4;
                assert.ok(data[i + 3] === 255 && hex(data, i) === '0a1627',
                    `${key}: (${x},${y}) is on the silhouette and ${hex(data, i)} at alpha ${data[i + 3]}`);
            }
        }
    });

    test('sendai yard art: the yard builders draw with rectangles, pixels and whole numbers only (#344)', () => {
        const src = fs.readFileSync(TOOL, 'utf8').split('\n');
        for (const name of BUILDERS) {
            const start = src.findIndex((l) => l.startsWith(`def ${name}(`));
            assert.ok(start >= 0, `def ${name}`);
            const end = src.findIndex((l, i) => i > start && /^(def |[A-Z_]+ = |# ==)/.test(l));
            const body = src.slice(start, end < 0 ? undefined : end).join('\n');
            for (const call of ['.polygon(', '.ellipse(', '.arc(', '.pieslice(', '.chord(', '.line(', 'shade(im', 'round(']) {
                assert.ok(!body.includes(call), `${name} calls ${call}`);
            }
            assert.ok(!/\broof\(/.test(body), `${name} calls roof()`);
            assert.ok(!/math\.(?!isqrt)/.test(body), `${name} uses math other than isqrt`);
        }
    });

    test('sendai yard art: the four keep their size, door, solid, walk, layer, halo and glow (#344)', () => {
        const out = python([
            'import json, sys',
            'try:',
            '    import PIL',
            'except ImportError:',
            '    print(json.dumps({"pillow": False})); sys.exit(0)',
            'import generate_sendai_town_art as t',
            'keys = json.loads(sys.argv[1])',
            'rows = {key: dict(size=list(size), door=m.get("door") or [], solid=m.get("solid", []), walk=m.get("walk", []),',
            '                  layer=m.get("layer", "standing"), halo=t.halo(key), glow=t.glow_spots(m))',
            '        for key, fn, size, district, m, *_ in t.PIECES if key in keys}',
            'print(json.dumps({"pillow": True, "rows": rows}))',
        ].join('\n'), [JSON.stringify(Object.keys(YARD))]);
        if (!out.pillow) return;            // no Pillow here: the tool does not import
        const cells = (r0, r1, w) => {
            const c = [];
            for (let r = r0; r <= r1; r++) for (let x = 0; x < w; x++) c.push([x, r]);
            return c;
        };
        const plain = { walk: [], layer: 'standing', halo: false };
        assert.deepStrictEqual(out.rows, {
            'sendai-distillery-warehouse_0_0': { ...plain, size: [6, 4], door: [[4, 3]], solid: cells(2, 3, 6), glow: [
                { x: 3, y: 2.9, r: 1.1, color: 16039292, a: 0.55 },
                { x: 1.5, y: 2.45, r: 0.7, color: 16178316, a: 0.5 },
                { x: 4.5, y: 2.3, r: 0.6, color: 16178316, a: 0.6 }] },
            'sendai-cask-rack_0_0': { ...plain, size: [3, 2], door: [], solid: [[0, 1], [1, 1], [2, 1]], glow: [] },
            'sendai-red-maple_0_0': { ...plain, size: [3, 4], door: [], solid: [[1, 3]], glow: [] },
            'sendai-yamadera_0_0': { ...plain, size: [6, 6], door: [], solid: cells(1, 5, 6), glow: [] },
        });
    });

    test('sendai yard art: generate_sendai_town_art.py rebuilds the four committed PNGs (#344)', () => {
        const out = python([
            'import json, sys',
            'try:',
            '    from PIL import Image',
            'except ImportError:',
            '    print(json.dumps({"pillow": False})); sys.exit(0)',
            'import generate_sendai_town_art as t',
            'keys = json.loads(sys.argv[1])',
            'differ = []',
            'for key in keys:',
            '    im = t.SPRITES[key]()',
            '    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)',
            '    if im.tobytes() != Image.open("assets/sprites/%s.png" % key).convert("RGBA").tobytes():',
            '        differ.append(key)',
            'print(json.dumps({"pillow": True, "differ": differ}))',
        ].join('\n'), [JSON.stringify(Object.keys(YARD))]);
        if (out.pillow) assert.deepStrictEqual(out.differ, [], 'the committed PNGs are what the tool draws');
    });
};
