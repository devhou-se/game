// Issue #342: Sendai's six ground families (tools/generate_sendai_town_art.py) in the GuttyKreum house look:
// pixel-doubled, every colour one of the sheets', no colour on half a tile, and each role joining the others,
// so a kerb runs on round its corners and the body meets its neighbour with no seam.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const png = require(path.join(GV2, 'tools', 'png'));
    const SPR = path.join(GV2, 'assets', 'sprites');
    const KERB = { plaza: 3, jozenji: 4, 'arcade-floor': 3, 'samurai-lane': 3, 'brick-yard': 4, boardwalk: 3 };
    const ROLES = ['center', 'edge-n', 'edge-s', 'edge-e', 'edge-w', 'corner-ne', 'corner-nw', 'corner-se', 'corner-sw'];
    const hex = (d, i) => [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
    const file = (fam, role) => path.join(SPR, `sendai-${fam}-autotile_${role}.png`);
    const tile = (fam, role) => {
        const im = png.decode(fs.readFileSync(file(fam, role)));
        return { ...im, at: (x, y) => hex(im.data, (y * im.width + x) * 4) };     // x, y in drawn pixels (0..31)
    };
    const tiles = (fam) => Object.fromEntries(ROLES.map((r) => [r, tile(fam, r)]));
    // the drawn pixels of a role inside its kerb on side `s` (n, s, e or w)
    const inKerb = (s, kw, x, y) => ({ n: y < kw, s: y >= 32 - kw, w: x < kw, e: x >= 32 - kw })[s];

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

    test('Sendai ground: the six families keep their 54 files, 64 px, opaque and pixel-doubled (#342)', () => {
        for (const fam of Object.keys(KERB)) for (const role of ROLES) {
            const { width: w, height: h, data } = png.decode(fs.readFileSync(file(fam, role)));
            assert.deepStrictEqual([w, h], [64, 64], `${fam} ${role}`);
            for (let i = 3; i < data.length; i += 4) assert.strictEqual(data[i], 255, `${fam} ${role}: not opaque`);
            for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
                const c = data.readUInt32BE((y * w + x) * 4);
                assert.ok([[1, 0], [0, 1], [1, 1]].every(([dx, dy]) => data.readUInt32BE(((y + dy) * w + x + dx) * 4) === c),
                    `${fam} ${role}: (${x},${y}) is not a 2x2 block`);
            }
        }
    });

    test('Sendai ground: every colour is the sheets\', at most 16 a tile, none on half of one (#342)', () => {
        const ok = sheets();
        for (const fam of Object.keys(KERB)) for (const role of ROLES) {
            const t = tile(fam, role), n = {};
            for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) n[t.at(x * 2, y * 2)] = (n[t.at(x * 2, y * 2)] || 0) + 1;
            const off = Object.keys(n).filter((c) => !ok.has(c));
            assert.deepStrictEqual(off, [], `${fam} ${role}: colours not on the GuttyKreum sheets`);
            assert.ok(Object.keys(n).length <= 16, `${fam} ${role}: ${Object.keys(n).length} colours`);
            const [top, most] = Object.entries(n).sort((a, b) => b[1] - a[1])[0];
            assert.ok(most <= 512, `${fam} ${role}: ${top} covers ${most} of 1024 pixels`);
        }
    });

    test('Sendai ground: each role is the centre outside its kerb, and a corner\'s arms are its edges\' kerbs (#342)', () => {
        for (const [fam, kw] of Object.entries(KERB)) {
            const t = tiles(fam);
            for (const role of ROLES.slice(1)) {
                const sides = role.split('-')[1].split('');
                for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) {
                    const hit = sides.filter((s) => inKerb(s, kw, x, y));
                    let want;
                    if (hit.length === 0) want = t.center;
                    else if (hit.length === 1 && sides.length === 2) want = t[`edge-${hit[0]}`];
                    else continue;                                  // an edge's own kerb, or a corner's square
                    assert.strictEqual(t[role].at(x * 2, y * 2), want.at(x * 2, y * 2), `${fam} ${role}: (${x},${y}) does not join`);
                }
            }
        }
    });
};
