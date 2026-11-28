// Issue #380: Lake Biwa's own art (tools/generate_lakebiwa_art.py) is drawn in the GuttyKreum house look, and the
// room keeps to the sheets' palette: every opaque colour of every biwa-* sprite, and of every other sprite
// rooms.LakeBiwa's layers use, is a colour of the sheets under art-source/GuttyKreum.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPRITES = path.join(GV2, 'assets', 'sprites');
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const decode = (key) => {
        const file = path.join(SPRITES, `${key}.png`);
        assert.ok(fs.existsSync(file), `${key} has no PNG`);
        return png.decode(fs.readFileSync(file));
    };
    // cells of each biwa-* sprite (the table in the design and generate_lakebiwa_art.py's docstring)
    const ART = {
        'biwa-hikone-keep_0_0': [6, 6], 'biwa-torii_0_0': [2, 3], 'biwa-tunnel_0_0': [4, 3], 'biwa-monkey_0_0': [1, 1],
        'biwa-cycle-sign_0_0': [1, 2], 'biwa-paddy_0_0': [1, 1], 'biwa-station-sign_0_0': [2, 2], 'biwa-fingerpost_0_0': [1, 2],
    };

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

    test('Lake Biwa art: each biwa-* sprite is 64px a cell at its size, pixel-doubled, and the paddy is opaque ground (#380)', () => {
        const files = fs.readdirSync(SPRITES).filter((f) => /^biwa-/.test(f)).map((f) => f.replace(/\.png$/, '')).sort();
        assert.deepStrictEqual(files, Object.keys(ART).sort(), 'the biwa-* sprites');
        for (const [key, [cw, ch]] of Object.entries(ART)) {
            const { width: w, height: h, data } = decode(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === c), `${key}: (${x},${y}) is not a 2x2 block`);
            }
            for (let i = 0; i < data.length; i += 4) assert.ok(data[i + 3] === 0 || data[i + 3] === 255, `${key}: a half-clear pixel`);
        }
        const { data } = decode('biwa-paddy_0_0');
        for (let i = 3; i < data.length; i += 4) assert.strictEqual(data[i], 255, 'biwa-paddy has a clear pixel: it is ground');
    });

    test('Lake Biwa art: every colour of the biwa-* sprites and of every sprite the room uses is a GuttyKreum sheet colour (#380)', () => {
        const known = sheets();
        assert.ok(known.size > 400, 'the GuttyKreum sheets are not under art-source');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const used = new Set(Object.keys(ART));
        for (const l of cfg.rooms.LakeBiwa.layers) for (const t of Object.values(l.tiles || {})) used.add(cfg.tilePalette[t]);
        used.delete('gk_blank');                              // the Colliders layer's marker: never drawn
        for (const key of [...used].sort()) {
            const { data } = decode(key);
            const off = new Set();
            for (let i = 0; i < data.length; i += 4) if (data[i + 3] && !known.has(hex(data, i))) off.add(hex(data, i));
            assert.deepStrictEqual([...off], [], `${key}: colours in no GuttyKreum sheet`);
        }
    });

    test('Lake Biwa art: check_distinct.py counts the seven landmarks as Kansai\'s own art, and not the paddy (#380)', () => {
        const py = fs.readFileSync(path.join(GV2, 'tools', 'check_distinct.py'), 'utf8');
        const body = py.match(/LANDMARK_ART = re\.compile\(\n([\s\S]*?)\)\nTEMPLE_KIT/)[1];
        const source = [...body.matchAll(/r'([^']*)'/g)].map((m) => m[1]).join('');
        const re = new RegExp(source);
        for (const key of Object.keys(ART)) {
            assert.strictEqual(re.test(key) && key.search(re) === 0, key !== 'biwa-paddy_0_0', `LANDMARK_ART and ${key}`);
        }
    });
};
