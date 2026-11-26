/**
 * JapaneseFont - pixel glyphs for Japanese text in every font the game draws with.
 *
 * The game's pixel fonts (PressStart2P, PixelOperatorMono, PixelOperatorMonoBold)
 * have no kana or kanji, so Japanese — blog-derived dialogue, post captions,
 * anything a future post brings — used to fall back to whatever smooth
 * system font the device had. PixelMplus12 (fonts/PixelMplus12-Grid.ttf, M+
 * FONT LICENSE — see fonts/README.md) is the M+ 12px bitmap gothic as
 * outlines, with every JIS level 1 and level 2 kanji. It is drawn on a 12px
 * grid, so it is pixel-exact at 12px and at the dialogue's 24px (#153); the
 * file is the original moved onto an exact grid by tools/regrid_pixelmplus.py.
 *
 * It is registered as a second face of each of those three families,
 * limited by `unicode-range` to the Japanese blocks. The browser then picks
 * it per character, so every existing `fontFamily: 'PixelOperatorMono'`
 * (Phaser text, canvas measuring, the creator's DOM input) gets Japanese
 * glyphs with no change at the call site, Latin text keeps its own font and
 * metrics, and a character PixelMplus12 lacks still falls back to the system
 * font as before.
 *
 * The file is 1.3 MB, so it is not in the boot queue: GameScene starts the
 * download once the loader has finished, it is fetched once (one buffer
 * shared by the three faces), and any text already on screen with Japanese
 * in it is redrawn when the font arrives.
 */
class JapaneseFont {
    static URL = 'fonts/PixelMplus12-Grid.ttf';

    /** Every font family the game draws text with (GameScene.preload loads them). */
    static FAMILIES = ['PressStart2P', 'PixelOperatorMono', 'PixelOperatorMonoBold'];

    /**
     * The blocks PixelMplus12 takes over: CJK radicals, CJK punctuation +
     * hiragana + katakana, han (extension A, unified, compatibility) and
     * the full-width / half-width forms. Latin, arrows and symbols stay
     * with the Latin fonts and their existing fallbacks.
     */
    static RANGES = [[0x2E80, 0x2FDF], [0x3000, 0x30FF], [0x3400, 0x4DBF], [0x4E00, 0x9FFF],
        [0xF900, 0xFAFF], [0xFF00, 0xFFEF]];

    /** RANGES as a CSS unicode-range descriptor. */
    static unicodeRange() {
        const hex = (n) => n.toString(16).toUpperCase();
        return JapaneseFont.RANGES.map(([lo, hi]) => `U+${hex(lo)}-${hex(hi)}`).join(', ');
    }

    /** Does the string have a character the Japanese face draws? */
    static covers(str) {
        for (const ch of String(str == null ? '' : str)) {
            const cp = ch.codePointAt(0);
            if (JapaneseFont.RANGES.some(([lo, hi]) => cp >= lo && cp <= hi)) return true;
        }
        return false;
    }

    /**
     * Blank rows a Text of this font size needs above and below a line with
     * Japanese in it. Phaser sizes the canvas from the Latin font's ascent
     * and descent; PixelMplus12's cell is 11 of its 12 rows above the
     * baseline and 2 below. That is two rows (4px at 24px) over the 3/4 em
     * ascent of the PixelOperator faces and, in PressStart2P, two rows
     * below a box that has no descent — so a sixth of an em, rounded up to
     * whole pixels.
     */
    static padRows(fontSize) {
        return Math.ceil(parseFloat(fontSize) / 6);
    }

    /**
     * Give a Text object room for the Japanese it is showing, so the glyphs
     * are not cut off at the top (or bottom) of its canvas: padRows() above
     * and below when the text has Japanese in it, none when it has not, so
     * Latin text is drawn exactly as before. The padding is the same on both
     * sides, so a Text anchored at its vertical centre does not move. A Text
     * anchored at its bottom edge in a PixelOperator face (whose descent
     * holds the Japanese glyphs, all but the lowest row of a full-width
     * bracket) passes `{ below: false }` to pad the top only, so its
     * baseline stays where a Latin line has it. Call it
     * after the text is set, and again after a setText() that may change the
     * answer. A Text that already has vertical padding (name plate, toasts)
     * or handles this itself (the dialogue text) does not need it.
     */
    static fit(text, { below = true } = {}) {
        const top = JapaneseFont.covers(text.text) ? JapaneseFont.padRows(text.style.fontSize) : 0;
        const bottom = below ? top : 0;
        if (text.padding.top !== top || text.padding.bottom !== bottom) {
            text.setPadding(text.padding.left, top, text.padding.right, bottom);
        }
        return text;
    }

    /**
     * Fetch the font (once) and add it to all three families, then redraw
     * the Japanese text already on screen. Resolves true when the font is
     * in use, false when it could not be loaded — the game carries on with
     * the system fallback, as it did before the font was bundled. A failed
     * fetch is not remembered (`loading` goes back to null), and retry()
     * — called each time a dialogue opens — tries again, so one dropped
     * request on a flaky connection does not cost the whole session its
     * pixel kana.
     */
    static load(game) {
        if (!JapaneseFont.loading) {
            const attempt = JapaneseFont.loading = fetch(JapaneseFont.URL)
                .then((res) => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.arrayBuffer();
                })
                .then((data) => Promise.all(JapaneseFont.FAMILIES.map((family) =>
                    new FontFace(family, data, { unicodeRange: JapaneseFont.unicodeRange() }).load())))
                .then((faces) => {
                    faces.forEach((face) => document.fonts.add(face));
                    // the font is in use from here on: a redraw problem is not a load failure
                    try {
                        JapaneseFont.refresh(game);
                    } catch (e) {
                        console.warn('Japanese pixel font loaded, but redrawing text failed:', e.message);
                    }
                    return true;
                })
                .catch((e) => {
                    console.warn('Japanese pixel font not loaded, using the system font:', e.message);
                    if (JapaneseFont.loading === attempt) JapaneseFont.loading = null;
                    return false;
                });
        }
        return JapaneseFont.loading;
    }

    /** Try again after a failed load; does nothing before the first load or once one is under way or done. */
    static retry(game) {
        return JapaneseFont.loading === null ? JapaneseFont.load(game) : JapaneseFont.loading;
    }

    /** Redraw every Text object, in any scene, that has Japanese in it. */
    static refresh(game) {
        const visit = (obj) => {
            if (obj.type === 'Text' && JapaneseFont.covers(obj.text)) obj.updateText();
            if (Array.isArray(obj.list)) obj.list.forEach(visit);
        };
        game.scene.getScenes(false).forEach((scene) => {
            // a scene that is registered but not booted yet has no display list
            if (scene.children && scene.children.list) scene.children.list.forEach(visit);
        });
    }
}
