// Issue #330: the Japanese home kit and the tower lobby (tools/generate_house_art.py) are in the house look:
// every colour a GuttyKreum sheet colour (through SWAP), the standing pieces edged in navy, the windows the
// pack's dark glass, nothing lit yellow. Keys, sizes, anchors and labels are the ones the rooms place.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPRITES = path.join(GV2, 'assets', 'sprites');
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const cfg = () => JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));

    // key: [cells wide, cells high, tileNames label]
    const KIT = {
        'home-tatami-green_w': [1, 1, 'home-tatami'], 'home-tatami-green_e': [1, 1, 'home-tatami'],
        'home-tatami-gold_w': [1, 1, 'home-tatami'], 'home-tatami-gold_e': [1, 1, 'home-tatami'],
        'home-genkan_0_0': [1, 1, 'home-genkan'], 'home-agari_0_0': [1, 1, 'home-agari'],
        'home-wall-sand_0_0': [1, 2, 'home-wall'], 'home-wall-moss_0_0': [1, 2, 'home-wall'],
        'home-wall-shoji_0_0': [1, 2, 'home-wall-shoji'], 'home-wall-fusuma_0_0': [1, 2, 'home-wall-fusuma'],
        'home-wall-window-sand_0_0': [1, 2, 'home-wall-window'], 'home-wall-window-moss_0_0': [1, 2, 'home-wall-window'],
        'home-tokonoma_0_0': [2, 2, 'home-tokonoma'], 'home-tansu_0_0': [1, 2, 'home-tansu'],
        'home-bookshelf_0_0': [1, 2, 'home-bookshelf'], 'home-tv_0_0': [1, 2, 'home-tv'],
        'home-fridge_0_0': [1, 2, 'home-fridge'], 'home-kitchen_0_0': [2, 2, 'home-kitchen'],
        'home-kotatsu-red_0_0': [2, 2, 'home-kotatsu'], 'home-kotatsu-indigo_0_0': [2, 2, 'home-kotatsu'],
        'home-table_0_0': [2, 1, 'home-table'], 'home-irori_0_0': [2, 2, 'home-irori'],
        'home-futon-blue_0_0': [1, 2, 'home-futon'], 'home-futon-rose_0_0': [1, 2, 'home-futon'],
        'home-bed_0_0': [1, 2, 'home-bed'], 'home-stove_0_0': [1, 1, 'home-stove'],
        'home-andon_0_0': [1, 1, 'home-andon'], 'home-getabako_0_0': [1, 1, 'home-getabako'],
        'home-zabuton-red_0_0': [1, 1, 'home-zabuton'], 'home-zabuton-indigo_0_0': [1, 1, 'home-zabuton'],
        'home-zabuton-green_0_0': [1, 1, 'home-zabuton'], 'home-shoes-a_0_0': [1, 1, 'home-shoes'],
        'home-shoes-b_0_0': [1, 1, 'home-shoes'], 'home-doormat_0_0': [1, 1, 'home-doormat'],
        'lobby-floor_a': [1, 1, 'lobby-floor'], 'lobby-floor_b': [1, 1, 'lobby-floor'],
        'lobby-mat_0_0': [1, 1, 'lobby-mat'], 'lobby-wall_0_0': [1, 2, 'lobby-wall'],
        'lobby-lift_0_0': [2, 2, 'lobby-lift'], 'lobby-directory_0_0': [1, 2, 'lobby-directory'],
        'lobby-desk_0_0': [3, 1, 'lobby-desk'], 'lobby-sofa_0_0': [2, 1, 'lobby-sofa'],
        'lobby-sofa-back_0_0': [2, 1, 'lobby-sofa'], 'lobby-table_0_0': [2, 1, 'lobby-table'],
        'lobby-plant_0_0': [1, 1, 'lobby-plant'],
    };
    // the flat and tiling pieces, which have no outline
    const UNEDGED = new Set(['home-tatami-green_w', 'home-tatami-green_e', 'home-tatami-gold_w', 'home-tatami-gold_e',
        'home-genkan_0_0', 'home-agari_0_0', 'home-wall-sand_0_0', 'home-wall-moss_0_0', 'home-wall-shoji_0_0',
        'home-wall-fusuma_0_0', 'home-wall-window-sand_0_0', 'home-wall-window-moss_0_0', 'home-tokonoma_0_0',
        'home-doormat_0_0', 'lobby-floor_a', 'lobby-floor_b', 'lobby-mat_0_0', 'lobby-wall_0_0', 'lobby-lift_0_0',
        'lobby-directory_0_0']);
    const sprite = (key) => png.decode(fs.readFileSync(path.join(SPRITES, `${key}.png`)));

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

    test('house art: the 45 home and lobby sprites keep their sizes, anchors and labels, pixel-doubled (#330)', () => {
        const c = cfg();
        assert.strictEqual(Object.keys(KIT).length, 45);
        for (const [key, [cw, ch, label]] of Object.entries(KIT)) {
            const { width: w, height: h, data } = sprite(key);
            assert.deepStrictEqual([w, h], [cw * 64, ch * 64], key);
            assert.deepStrictEqual(c.spriteMetadata[key], { frameCount: 1, anchorX: 32 / w, anchorY: 32 / h }, key);
            assert.strictEqual(c.tileNames[key], label, key);
            const at = (x, y) => (y * w + x) * 4;
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const v = data.readUInt32BE(at(x, y));
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(at(x + dx, y + dy)) === v), `${key}: (${x},${y}) is not a 2x2 block`);
            }
            for (let i = 3; i < data.length; i += 4) assert.ok(data[i] === 0 || data[i] === 255, `${key}: a half-clear pixel`);
        }
    });

    test('house art: every colour is a sheet colour and none is lit yellow (#330)', () => {
        const known = sheets(), lit = new Set(['f2c66a', 'fbe6a4', 'f9c22e', 'f0943a', 'e8623a']);
        for (const key of Object.keys(KIT)) {
            const { data } = sprite(key);
            for (let i = 0; i < data.length; i += 4) {
                if (!data[i + 3]) continue;
                const c = hex(data, i);
                assert.ok(!lit.has(c), `${key}: ${c} is lit yellow`);
                assert.ok(known.has(c), `${key}: ${c} is in no GuttyKreum sheet`);
            }
        }
    });

    test('house art: what stands is edged in navy, and the windows are the pack\'s dark glass (#330)', () => {
        for (const key of Object.keys(KIT).filter((k) => !UNEDGED.has(k))) {
            const { width: w, height: h, data } = sprite(key);
            // a clear pixel inside the canvas: outline() cannot draw past the edge (the kitchen's hood reaches it)
            const clear = (x, y) => x >= 0 && y >= 0 && x < w && y < h && data[(y * w + x) * 4 + 3] === 0;
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                if (clear(x, y) || ![[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => clear(x + dx, y + dy))) continue;
                assert.strictEqual(hex(data, (y * w + x) * 4), '172459', `${key}: (${x},${y}) is on the silhouette and not navy`);
            }
        }
        for (const key of ['home-wall-window-sand_0_0', 'home-wall-window-moss_0_0']) {
            const { data } = sprite(key), seen = new Set();
            for (let i = 0; i < data.length; i += 4) seen.add(hex(data, i));
            for (const c of ['2c2d51', '4b6396']) assert.ok(seen.has(c), `${key}: no ${c} in the glass`);
        }
    });

    test('house art: generate_house_art.py still defines every name generate_devhouse_art.py imports (#330)', () => {
        const src = fs.readFileSync(path.join(GV2, 'tools', 'generate_house_art.py'), 'utf8');
        const dev = fs.readFileSync(path.join(GV2, 'tools', 'generate_devhouse_art.py'), 'utf8');
        const m = dev.match(/from generate_house_art import \(([^)]*)\)/);
        assert.ok(m, 'generate_devhouse_art.py imports from generate_house_art');
        const names = m[1].split(',').map((n) => n.trim()).filter(Boolean);
        assert.ok(names.length > 20);
        for (const n of names) {
            assert.ok(new RegExp(`(^|[\\s,(])${n}(\\s*,[^\\n=]*)?\\s*=[^=]|def ${n}\\(`, 'm').test(src), `${n} is not defined in generate_house_art.py`);
        }
    });
};
