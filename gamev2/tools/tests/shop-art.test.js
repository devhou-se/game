// The Don Takote signage (tools/generate_discount_art.py) and the konbini drinks cooler
// (tools/generate_cooler_art.py) in the house look (issue #295): the same keys, sizes and anchors,
// every colour one the GuttyKreum sheets use, and shading, not a recolour.
module.exports = ({ test, assert, fs, path, GV2, require }) => {
    test('the Don Takote signage and the drinks cooler keep their sizes and draw in the pack palette', () => {
        const png = require('./png');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const PALETTE = new Set([
            '0a1627', '172459', 'fafcfd', 'dae2e4',
            'f3d890', 'e3c587', 'c6a663', 'a7843b', 'd1e2eb', 'a4b0b5', '94a2a8', '575c6d',
            'e78d7b', 'd16b56', 'aa4d31', '8a3a22', '5b6c79', '444f5e',
            '7db9fa', '588cc6', '425faa', '314b8e', '83af6f', '678e57', '508582', '4a6262',
            '2c2d51', '2a3151', '4b6396', '8689a6',
        ]);
        const OLD = ['ffffff', '000000', 'f9c22e', '1155a8', '1c1c22', 'c62828', 'b3e5fc', '039be5'];
        const GOLD = ['f3d890', 'e3c587', 'c6a663', 'a7843b'], RED = ['e78d7b', 'd16b56', 'aa4d31', '8a3a22'];
        const STEEL = ['d1e2eb', 'a4b0b5', '94a2a8', '575c6d'];
        const SPRITES = {
            'don-takote-sign': [320, 128, 0.1, 0.25, 1], 'don-takote-wall': [64, 64, 0.5, 0.5, undefined],
            'don-takote-wall-top': [64, 64, 0.5, 0.5, undefined], 'don-takote-pop-yen': [64, 64, 0.5, 0.5, 1],
            'don-takote-pop-sale': [64, 64, 0.5, 0.5, 1], 'office-fridge': [64, 128, 0.5, 0.25, undefined],
        };
        const hex = (im, x, y) => {
            const i = (y * im.width + x) * 4;
            return [im.data.slice(i, i + 3).toString('hex'), im.data[i + 3]];
        };
        // the colours inside a box, opaque pixels only
        const colours = (im, x0 = 0, y0 = 0, x1 = im.width, y1 = im.height) => {
            const seen = new Set();
            for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
                const [c, a] = hex(im, x, y);
                if (a === 255) seen.add(c);
            }
            return seen;
        };
        const ims = {};
        for (const [name, [w, h, ax, ay, bias]] of Object.entries(SPRITES)) {
            const key = `${name}_0_0`, im = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
            ims[name] = im;
            assert.deepStrictEqual([im.width, im.height], [w, h], key);
            const meta = cfg.spriteMetadata[key];
            assert.deepStrictEqual([meta.frameCount, meta.anchorX, meta.anchorY, meta.depthBias], [1, ax, ay, bias], key);
            if (name !== 'office-fridge') assert.strictEqual(cfg.tileNames[key], name, key);   // the cooler is the office kit's key
            const card = name.startsWith('don-takote-pop');
            for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                const [c, a] = hex(im, x, y);
                if (a === 0) { assert.ok(card, `${key} (${x},${y}) is see-through`); continue; }
                if (a < 255) { assert.ok(card && c === '2a3151' && a === 90, `${key} (${x},${y}) ${c}/${a}`); continue; }
                assert.ok(PALETTE.has(c), `${key} (${x},${y}) ${c} is not a pack colour`);
                assert.ok(!OLD.includes(c), `${key} (${x},${y}) ${c}`);
            }
        }
        assert.deepStrictEqual(hex(ims['don-takote-sign'], 0, 0), ['172459', 255]);
        assert.deepStrictEqual(hex(ims['office-fridge'], 0, 0), ['172459', 255]);
        // shaded, not recoloured: a ramp of each piece's colour
        const has = (set, ramp, n, what) => assert.ok(ramp.filter((c) => set.has(c)).length >= n, what);
        has(colours(ims['don-takote-sign']), GOLD, 3, 'the sign board is lit and shaded');
        has(colours(ims['don-takote-sign'], 12, 20, 70, 90), RED, 4, 'the octopus on the sign is lit and shaded');
        has(colours(ims['don-takote-pop-sale'], 14, 14, 50, 50), RED, 4, 'the octopus on the card is lit and shaded');
        for (const wall of ['don-takote-wall', 'don-takote-wall-top']) has(colours(ims[wall]), GOLD, 3, `${wall}: a lit and a shaded edge`);
        has(colours(ims['office-fridge']), STEEL, 4, 'the cooler is lit and shaded steel');
    });
};
