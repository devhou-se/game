module.exports = ({ test, assert, fs, path, GV2, game }) => {
    test('the Japanese pixel font covers every family the game loads and every Japanese character it shows', () => {
        const families = game('JapaneseFont.FAMILIES'), covers = game('JapaneseFont.covers');
        // every family GameScene.preload loads gets the Japanese face, and the font + its licence ship
        const loaded = Array.from(fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8')
            .matchAll(/this\.load\.font\('([^']+)'/g), (m) => m[1]);
        assert.deepStrictEqual(Array.from(families).sort(), loaded.sort());
        const font = fs.readFileSync(path.join(GV2, game('JapaneseFont.URL')));
        assert.strictEqual(font.readUInt32BE(0), 0x00010000, 'a TrueType file');
        assert.ok(fs.existsSync(path.join(GV2, 'fonts', 'DotGothic16-OFL.txt')), 'the OFL text ships beside the font');
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

    test('a Text showing Japanese gets rows above and below its Latin line box, Latin text none', () => {
        const fit = game('JapaneseFont.fit'), rows = game('JapaneseFont.padRows');
        // 2.4px over the 24px ascent, 1.4px under PressStart2P's 16px box: an eighth of an em covers both
        assert.deepStrictEqual(['16px', '24px', '32px', 20].map(rows), [2, 3, 4, 3]);
        const text = (str, fontSize, padding) => ({
            text: str, style: { fontSize }, padding: { left: 0, right: 0, top: 0, bottom: 0, ...padding }, sets: 0,
            setText(v) { this.text = v; return this; },
            setPadding(left, top, right, bottom) { this.padding = { left, top, right, bottom }; this.sets++; return this; },
        });
        const name = text('グミ', '16px', { left: 5, right: 7 });
        assert.strictEqual(fit(name), name, 'chains');
        assert.deepStrictEqual({ ...name.padding }, { left: 5, top: 2, right: 7, bottom: 2 }, 'same above and below, sides kept');
        fit(name);
        assert.strictEqual(name.sets, 1, 'no redraw when nothing changes');
        assert.deepStrictEqual({ ...fit(name.setText('Gumi')).padding }, { left: 5, top: 0, right: 7, bottom: 0 }, 'gone with the Japanese');
        const latin = fit(text('devhou.se | Shibuya | ', '16px'));
        assert.strictEqual(latin.sets, 0, 'Latin text is never touched');
        assert.strictEqual(fit(text('Kanpai 東京 ✦', '24px')).padding.top, 3);
        // a bottom-anchored label pads the top only, so its baseline stays put
        const label = fit(text('グミ東京', '16px'), { below: false });
        assert.deepStrictEqual([label.padding.top, label.padding.bottom, label.sets], [2, 0, 1]);
        assert.deepStrictEqual([fit(label, { below: false }).sets, fit(label.setText('Gumi'), { below: false }).padding.top], [1, 0]);
        // the places that show a typed name or a room name ask for it
        const src = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
        assert.ok(/playerNameLabel\.setText\(name\), \{ below: false \}\)/.test(src('GameScene.js')) && /JapaneseFont\.fit\(this\.hudText\.setText/.test(src('GameScene.js')));
        assert.ok(/JapaneseFont\.fit\(o\)/.test(src('CharacterSelect.js')));
    });
};
