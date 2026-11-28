// Issue #279: the ad pool is drawn in the GuttyKreum house look (tools/house_look.py, the recipe in
// docs/generators-and-checks.md): pixel-doubled, edged in ink, 8 to 16 colours with none covering half the
// board, every colour one of the sheets'. The pool keeps its shapes, names and manifest for placeSignage.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const png = require(path.join(GV2, 'tools', 'png'));
    const ADS = path.join(GV2, 'assets', 'ads');
    const manifest = () => JSON.parse(fs.readFileSync(path.join(ADS, 'manifest.json'), 'utf8')).ads;
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const ads = () => manifest().map((a) => ({ ...a, im: png.decode(fs.readFileSync(path.join(ADS, a.file))) }));

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

    test('ads: the pool keeps its shapes, keys and sizes for placeSignage (#279)', () => {
        const pool = ads(), count = (s) => pool.filter((a) => a.shape === s).length;
        assert.deepStrictEqual(['square', 'tall', 'wide', 'big'].map(count), [12, 12, 14, 6]);
        const n = {};
        for (const a of pool) {
            n[a.shape] = (n[a.shape] || 0) + 1;
            const name = `${a.shape}-${String(n[a.shape]).padStart(2, '0')}`;
            assert.deepStrictEqual([a.key, a.file], [`ad-${name}`, `${name}.png`]);
            assert.deepStrictEqual([a.im.width, a.im.height], [a.w * 64, a.h * 64], a.file);
        }
    });

    test('ads: every board is pixel-doubled, edged in ink, its corners clear (#279)', () => {
        for (const { file, im: { width: w, height: h, data } } of ads()) {
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${file}: (${x},${y}) is not a 2x2 block`);
            }
            for (const [x, y] of [[0, 0], [w - 2, 0], [0, h - 2], [w - 2, h - 2]]) assert.strictEqual(data[at(x, y) + 3], 0, `${file}: corner (${x},${y})`);
            const clear = (x, y) => x < 0 || y < 0 || x >= w || y >= h || data[at(x, y) + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (clear(x, y)) continue;
                if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) {
                    assert.strictEqual(hex(data, at(x, y)), '0a1627', `${file}: (${x},${y}) is on the silhouette and not ink`);
                }
            }
        }
    });

    test('ads: 8 to 16 colours (a big: 24), none on half the board, all of them the sheets\' (#279)', () => {
        const known = sheets();
        for (const { file, shape, im: { data } } of ads()) {
            const counts = new Map();
            let opaque = 0;
            for (let i = 0; i < data.length; i += 4) {
                if (!data[i + 3]) continue;
                assert.strictEqual(data[i + 3], 255, `${file}: a half-clear pixel`);
                opaque++;
                counts.set(hex(data, i), (counts.get(hex(data, i)) || 0) + 1);
            }
            assert.ok(counts.size >= 8 && counts.size <= (shape === 'big' ? 24 : 16), `${file}: ${counts.size} colours`);
            for (const [c, n] of counts) {
                assert.ok(n * 2 <= opaque, `${file}: ${c} covers ${n} of ${opaque} pixels`);
                assert.ok(known.has(c), `${file}: ${c} is in no GuttyKreum sheet`);
            }
        }
    });

    test('house_look: the ramps are the sheets\' colours, the helpers draw by the recipe, generate_ads rebuilds the pool (#279)', () => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'house-look-'));
        try {
            const snippet = [
                'import json, subprocess, sys',
                'try:',
                '    import house_look as hl',
                'except ImportError:',
                '    print(json.dumps({"pillow": False})); sys.exit(0)',
                'out = {"pillow": True, "palette": sorted("%02x%02x%02x" % c[:3] for c in hl.palette())}',
                'out["red"] = [list(t) for t in hl.material("red", 2)]',
                'im = hl.canvas(8, 12)',
                'hl.shade(im, (0, 0, 7, 11), hl.material("gold", 2))',
                'rows = [[im.getpixel((x, y)) for x in range(8)] for y in range(12)]',
                'out["dithered"] = [y for y, r in enumerate(rows) if len(set(r)) > 1]',
                'out["flat"] = [y for y, r in enumerate(rows) if len(set(r)) == 1]',
                'out["bar"] = list(hl.text_size("ー", vertical=True))',
                'out["across"] = list(hl.text_size("ー"))',
                'for run in (1, 2):',
                '    p = subprocess.run([sys.executable, "tools/generate_ads.py", "--out", sys.argv[1] + "/%d" % run], capture_output=True, text=True)',
                '    assert p.returncode == 0, p.stderr',
                'from PIL import Image',
                'man = json.load(open("assets/ads/manifest.json"))["ads"]',
                'same = lambda a, b: Image.open(a).convert("RGBA").tobytes() == Image.open(b).convert("RGBA").tobytes()',
                'out["differ"] = [a["file"] for a in man for run in (1, 2) if not same("assets/ads/" + a["file"], sys.argv[1] + "/%d/" % run + a["file"])]',
                'out["manifest"] = all(open(sys.argv[1] + "/%d/manifest.json" % run, "rb").read() == open("assets/ads/manifest.json", "rb").read() for run in (1, 2))',
                'print(json.dumps(out))',
            ].join('\n');
            const run = spawnSync('python3', ['-c', snippet, tmp], { cwd: GV2, encoding: 'utf8', timeout: 120000,
                env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
            assert.ok(!run.error, `python3 did not finish: ${run.error}`);
            assert.strictEqual(run.status, 0, run.stderr);
            const out = JSON.parse(run.stdout.trim().split('\n').pop());
            if (!out.pillow) return;        // no Pillow here: check_generators.py lists the art tools as skip too
            const known = sheets();
            assert.deepStrictEqual(out.palette.filter((c) => !known.has(c)), [], 'every ramp tone is a colour of a sheet');
            // (base, hi, lo, line): line_art's order
            assert.deepStrictEqual(out.red, [[0xd1, 0x6b, 0x56, 255], [0xe7, 0x8d, 0x7b, 255], [0xaa, 0x4d, 0x31, 255], [0x8a, 0x3a, 0x22, 255]]);
            assert.strictEqual(out.dithered.length, 1, 'a shaded face has one dithered row');
            assert.deepStrictEqual(out.flat.length, 11);
            assert.ok(out.bar[1] > out.bar[0] && out.across[0] > out.across[1], `ー stands upright in vertical text: ${out.bar} / ${out.across}`);
            assert.deepStrictEqual(out.differ, [], 'generate_ads.py rebuilds the committed pool, twice the same');
            assert.ok(out.manifest, 'and the same manifest.json');
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('the slate and steel roofs\' dark tone is the sheets\' 2e4040, not 2b373c (#375)', () => {
        const known = sheets();
        const colours = (key) => {
            const { data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', `${key}_0_0.png`)));
            const out = new Set();
            for (let i = 0; i < data.length; i += 4) if (data[i + 3]) out.add(hex(data, i));
            return out;
        };
        for (const key of ['canal-city', 'fukuoka-tower', 'sendai-pub', 'seven-eleven']) {
            const c = colours(key);
            assert.ok(!c.has('2b373c'), `${key} still paints 2b373c`);
            assert.ok(c.has('2e4040'), `${key}: the roof's dark tone`);
        }
        // 2b373c was the only off-pack colour of these two
        for (const key of ['sendai-pub', 'seven-eleven']) {
            assert.deepStrictEqual([...colours(key)].filter((c) => !known.has(c)), [], `${key}: every colour is a sheet's`);
        }
    });

    test('extract_city: the Don Takote sign is drawn in the house look, its colours the sheets\' (#346)', () => {
        // the sign is the store's top two cells; the facade under it is cut from the sheets as it is
        const { width: w, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', 'discount-store_0_0.png')));
        const h = 128, at = (x, y) => (y * w + x) * 4, known = sheets(), colours = new Set();
        for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
            const c = data.readUInt32BE(at(x, y));
            assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `(${x},${y}) is not a 2x2 block`);
        }
        for (const [x, y] of [[0, 0], [w - 2, 0], [0, h - 2], [w - 2, h - 2]]) assert.strictEqual(data[at(x, y) + 3], 0, `corner (${x},${y})`);
        for (let i = 0; i < w * h * 4; i += 4) if (data[i + 3]) colours.add(hex(data, i));
        assert.deepStrictEqual([...colours].filter((c) => !known.has(c)), [], 'every colour of the sign is a sheet\'s');
        assert.ok(colours.size >= 8 && colours.size <= 24, `${colours.size} colours`);
        for (let x = 2; x < w - 2; x++) assert.strictEqual(hex(data, at(x, 0)), '0a1627', `(${x},0) is on the silhouette and not ink`);
    });
};
