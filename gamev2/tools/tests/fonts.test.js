module.exports = ({ test, assert, fs, path, GV2, game }) => {
    /** Just enough of a TrueType file: the characters it maps, and the outline points and advance of one. */
    const openFont = (file) => {
        const b = fs.readFileSync(file), tables = {};
        for (let i = 0; i < b.readUInt16BE(4); i++) tables[b.toString('latin1', 12 + i * 16, 16 + i * 16)] = b.readUInt32BE(20 + i * 16);
        const { cmap, head, hhea, hmtx, loca, glyf } = tables, glyphs = new Map();
        for (let i = 0; i < b.readUInt16BE(cmap + 2); i++) {
            const sub = cmap + b.readUInt32BE(cmap + 8 + i * 8);
            if (b.readUInt16BE(sub) !== 4) continue;
            const n = b.readUInt16BE(sub + 6) / 2, ends = sub + 14, starts = ends + n * 2 + 2, deltas = starts + n * 2, offsets = deltas + n * 2;
            for (let k = 0; k < n; k++) {
                const start = b.readUInt16BE(starts + k * 2), end = b.readUInt16BE(ends + k * 2), offset = b.readUInt16BE(offsets + k * 2);
                for (let cp = start; cp <= end && cp < 0xFFFF; cp++) {
                    let g = offset ? b.readUInt16BE(offsets + k * 2 + offset + (cp - start) * 2) : cp;
                    if (g || !offset) g = (g + b.readInt16BE(deltas + k * 2)) & 0xFFFF;
                    if (g) glyphs.set(cp, g);
                }
            }
        }
        const long = b.readInt16BE(head + 50), at = (g) => (long ? b.readUInt32BE(loca + g * 4) : b.readUInt16BE(loca + g * 2) * 2);
        const points = (cp) => {
            const g = glyphs.get(cp), xs = [], ys = [];
            let p = glyf + at(g);
            if (at(g + 1) === at(g)) return { xs, ys };          // a blank glyph
            const contours = b.readInt16BE(p);
            assert.ok(contours > 0, 'a simple outline');
            const count = b.readUInt16BE(p + 10 + (contours - 1) * 2) + 1, flags = [];
            p += 10 + contours * 2;
            p += 2 + b.readUInt16BE(p);
            while (flags.length < count) {
                const f = b[p++];
                flags.push(f);
                if (f & 8) for (let r = b[p++]; r > 0; r--) flags.push(f);
            }
            for (const [out, short, same] of [[xs, 2, 16], [ys, 4, 32]]) {
                let v = 0;
                for (const f of flags) {
                    if (f & short) v += (f & same) ? b[p++] : -b[p++];
                    else if (!(f & same)) { v += b.readInt16BE(p); p += 2; }
                    out.push(v);
                }
            }
            return { xs, ys };
        };
        const advance = (cp) => b.readUInt16BE(hmtx + Math.min(glyphs.get(cp), b.readUInt16BE(hhea + 34) - 1) * 4);
        return { has: (cp) => glyphs.has(cp), points, advance, unitsPerEm: b.readUInt16BE(head + 18) };
    };

    test('the Japanese pixel font covers every family the game loads and every Japanese character it shows', () => {
        const families = game('JapaneseFont.FAMILIES'), covers = game('JapaneseFont.covers');
        // every family GameScene.preload loads gets the Japanese face, and the font + its licence ship
        const loaded = Array.from(fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8')
            .matchAll(/this\.load\.font\('([^']+)'/g), (m) => m[1]);
        assert.deepStrictEqual(Array.from(families).sort(), loaded.sort());
        const font = fs.readFileSync(path.join(GV2, game('JapaneseFont.URL')));
        assert.strictEqual(font.readUInt32BE(0), 0x00010000, 'a TrueType file');
        assert.ok(/with\s+or without modification/.test(fs.readFileSync(path.join(GV2, 'fonts', 'PixelMplus12-LICENSE.txt'), 'utf8')), 'the M+ licence ships beside the font');
        // fonts/README.md says which file this is (tools/regrid_pixelmplus.py prints the hash after a rebuild)
        const sha = require('crypto').createHash('sha256').update(font).digest('hex');
        assert.ok(fs.readFileSync(path.join(GV2, 'fonts', 'README.md'), 'utf8').includes('`' + sha + '`'), `fonts/README.md names ${sha}`);
        assert.strictEqual(game('JapaneseFont.unicodeRange()').split(', ')[1], 'U+3000-30FF');
        // Latin, digits, arrows and the d-pad glyphs stay with the Latin fonts
        for (const s of ['Kanpai!', '¥1,200', '←/→ ◀ ▶ ↑/↓', '…', '', null]) assert.strictEqual(covers(s), false, String(s));
        for (const s of ['あ', 'カ', '郷', '、', '「', '！', 'ＡＢ', 'ｶﾞ', 'from: 富山から白川郷まで']) assert.strictEqual(covers(s), true, s);
        // whatever the dialogue wrapper treats as Japanese, the font's unicode-range takes
        const CJK = game('DialogueManager.CJK');
        const walk = (v) => {
            if (typeof v === 'string') { for (const ch of v) if (CJK.test(ch)) assert.ok(covers(ch), `${ch} in ${v}`); }
            else if (v && typeof v === 'object') Object.values(v).forEach(walk);
        };
        walk(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms);
        // the studio page has its own families (CSS, not JapaneseFont.load): each Latin face has a Japanese twin
        const faces = Array.from(fs.readFileSync(path.join(GV2, 'studio', 'index.html'), 'utf8').matchAll(/@font-face\s*{([^}]*)}/g), (m) => ({
            key: /font-family:\s*'([^']+)'/.exec(m[1])[1] + (/font-weight:\s*bold/.test(m[1]) ? ' bold' : ''),
            japanese: m[1].includes(path.basename(game('JapaneseFont.URL'))),
            range: (/unicode-range:\s*([^;]+);/.exec(m[1]) || [])[1],
        }));
        const latin = faces.filter((f) => !f.japanese).map((f) => f.key).sort();
        assert.ok(latin.length > 0, 'the studio declares its fonts');
        assert.deepStrictEqual(faces.filter((f) => f.japanese).map((f) => f.key).sort(), latin);
        for (const f of faces) assert.strictEqual(f.range, f.japanese ? game('JapaneseFont.unicodeRange()') : undefined, f.key);
        // retry() only acts after a failed load (loading === null), never before the first one
        assert.strictEqual(game('JapaneseFont.loading'), undefined);
        assert.strictEqual(game('JapaneseFont.retry({})'), undefined);
    });

    test('the Japanese font has every Japanese character the game ships and sits on a 12px grid (#153)', () => {
        const font = openFont(path.join(GV2, game('JapaneseFont.URL'))), covers = game('JapaneseFont.covers');
        // 100 units a pixel, 12 pixels an em: pixel-exact at 12px and at the dialogue's 24px
        const PIXEL = 100;
        assert.strictEqual(font.unitsPerEm, 12 * PIXEL);
        assert.strictEqual(game('DialogueManager.TEXT_FONT').size % 12, 0, 'the dialogue size is a whole multiple of the grid');
        // every Japanese character in the shipped config (dialogue, post titles) and in the source
        const used = new Set();
        const collect = (str) => { for (const ch of str) if (covers(ch)) used.add(ch); };
        collect(JSON.stringify(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'))));   // the file escapes them
        const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
            if (e.isDirectory()) walk(path.join(dir, e.name));
            else if (e.name.endsWith('.js')) collect(fs.readFileSync(path.join(dir, e.name), 'utf8'));
        });
        walk(path.join(GV2, 'src'));
        assert.ok(used.size > 200, `the config has Japanese in it (${used.size})`);
        // the line-breaking sets list a few brackets and small kana no JIS font has; nothing shows them
        const rules = new Set([...game('DialogueManager.NO_LINE_START'), ...game('DialogueManager.NO_LINE_END')]);
        const missing = Array.from(used).filter((ch) => !font.has(ch.codePointAt(0)));
        assert.deepStrictEqual(missing.filter((ch) => !rules.has(ch)), [], 'characters the font lacks');
        assert.deepStrictEqual(missing.sort(), ['〖', '〗', '〘', '〙', 'ゕ', 'ゖ']);
        for (const ch of used) {
            const cp = ch.codePointAt(0);
            if (!font.has(cp)) continue;
            const { xs, ys } = font.points(cp);
            assert.ok(xs.concat(ys).every((v) => v % PIXEL === 0), `${ch} is on the pixel grid`);
            // the cell: 12 columns (6 for a half-width form), 11 rows above the baseline and 2 below
            const half = cp >= 0xFF61 && cp <= 0xFF9F;
            assert.strictEqual(font.advance(cp), (half ? 6 : 12) * PIXEL, `${ch} advance`);
            assert.ok(Math.min(0, ...xs) >= 0 && Math.max(0, ...xs) <= font.advance(cp), `${ch} stays in its cell`);
            assert.ok(Math.min(0, ...ys) >= -2 * PIXEL && Math.max(0, ...ys) <= 11 * PIXEL, `${ch} stays in its rows`);
        }
        // padRows() is those rows: 11/12 em over the PixelOperator ascent (3/4 em), 2/12 em under PressStart2P's box
        const rows = game('JapaneseFont.padRows');
        for (const size of [12, 14, 16, 20, 24, 32]) {
            assert.ok(rows(size) >= size * (11 / 12 - 3 / 4) && rows(size) >= size * 2 / 12, `${size}px`);
            assert.ok(rows(size) < size / 6 + 1, `${size}px is not padded more than it needs`);
        }
        // the dialogue text pads itself: the same rows above, and below the 1/8 em descent Phaser measures
        const size = game('DialogueManager.TEXT_FONT').size;
        assert.ok(game('DialogueManager.TEXT_PAD_TOP') >= size * (11 / 12 - 3 / 4));
        assert.ok(game('DialogueManager.TEXT_PAD_BOTTOM') >= size * (2 / 12 - 1 / 8));
        const dialogue = fs.readFileSync(path.join(GV2, 'src', 'DialogueManager.js'), 'utf8');
        assert.ok(dialogue.includes('padding: { top: DialogueManager.TEXT_PAD_TOP, bottom: DialogueManager.TEXT_PAD_BOTTOM }'));
        assert.ok(dialogue.includes('this.lineBase = one - this.lineHeight - DialogueManager.TEXT_PAD_BOTTOM;'), 'the bottom row is not counted as text height');
    });

    test('a Text showing Japanese gets rows above and below its Latin line box, Latin text none', () => {
        const fit = game('JapaneseFont.fit'), rows = game('JapaneseFont.padRows');
        // 4px over the 18px ascent of 24px PixelOperatorMono, 2.7px under PressStart2P's 16px box: a sixth of an em covers both
        assert.deepStrictEqual(['12px', '16px', '24px', '32px', 20].map(rows), [2, 3, 4, 6, 4]);
        const text = (str, fontSize, padding) => ({
            text: str, style: { fontSize }, padding: { left: 0, right: 0, top: 0, bottom: 0, ...padding }, sets: 0,
            setText(v) { this.text = v; return this; },
            setPadding(left, top, right, bottom) { this.padding = { left, top, right, bottom }; this.sets++; return this; },
        });
        const name = text('グミ', '16px', { left: 5, right: 7 });
        assert.strictEqual(fit(name), name, 'chains');
        assert.deepStrictEqual({ ...name.padding }, { left: 5, top: 3, right: 7, bottom: 3 }, 'same above and below, sides kept');
        fit(name);
        assert.strictEqual(name.sets, 1, 'no redraw when nothing changes');
        assert.deepStrictEqual({ ...fit(name.setText('Gumi')).padding }, { left: 5, top: 0, right: 7, bottom: 0 }, 'gone with the Japanese');
        const latin = fit(text('devhou.se | Shibuya | ', '16px'));
        assert.strictEqual(latin.sets, 0, 'Latin text is never touched');
        assert.strictEqual(fit(text('Kanpai 東京 ✦', '24px')).padding.top, 4);
        // a bottom-anchored label pads the top only, so its baseline stays put
        const label = fit(text('グミ東京', '16px'), { below: false });
        assert.deepStrictEqual([label.padding.top, label.padding.bottom, label.sets], [3, 0, 1]);
        assert.deepStrictEqual([fit(label, { below: false }).sets, fit(label.setText('Gumi'), { below: false }).padding.top], [1, 0]);
        // the places that show a typed name or a room name ask for it
        const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
        assert.ok(/playerNameLabel\.setText\(name\), \{ below: false \}\)/.test(src('GameScene.js')) && /JapaneseFont\.fit\(this\.hudText\.setText/.test(src('GameScene.js')));
        assert.ok(/JapaneseFont\.fit\(o\)/.test(src('CharacterSelect.js')));
    });
};
