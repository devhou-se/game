/**
 * Hints - the one place that words "which button does what" lines.
 *
 * Overlays write their hint for the keyboard, exactly as it reads on a
 * desktop, and pass it through `Hints.text(scene, ...)`. With touch controls
 * on, the keys are renamed to the on-screen buttons that synthesize them
 * (see TouchControls), so every overlay words touch the same way:
 *
 *   SPACE, ENTER   -> A            ESC       -> B
 *   ↑/↓, W/S       -> d-pad        SHIFT     -> sprint  (SHIFT+ENTER -> hold sprint + A)
 *   click          -> tap          WASD / arrows, arrows -> d-pad
 *   ←/→            -> ◀ ▶          (the d-pad's own left / right glyphs, so a line
 *                                   with both axes never reads "d-pad ... d-pad")
 *
 * `{ tap: true }` is for overlays where a tap anywhere does what SPACE /
 * ENTER does (dialogue, intro): their confirm key reads "TAP or A".
 *
 * Without touch controls the text comes back untouched.
 *
 * The controls come and go with the input in use (a touchscreen laptop is a
 * keyboard until its screen is touched — see TouchControls), so every hint
 * handed out is remembered: `Hints.refresh(scene)` rewords the ones on
 * screen when the input changes, and `Hints.isHint(text)` lets UIScale keep
 * hint lines above a minimum size on small screens. Neither needs anything
 * from the overlay that asked for the hint.
 */
class Hints {
    /** Are the on-screen touch controls in use? */
    static touch(scene) {
        return !!(scene && scene.touchControls && scene.touchControls.enabled);
    }

    static text(scene, keyboardText, opts) {
        const touch = Hints.word(keyboardText, opts);
        const source = { keyboard: keyboardText, opts };
        Hints.issued.set(keyboardText, source);
        Hints.issued.set(touch, source);
        return Hints.touch(scene) ? touch : keyboardText;
    }

    /** The touch wording of a keyboard hint. */
    static word(keyboardText, opts) {
        const a = opts && opts.tap ? 'TAP or A' : 'A';
        return Hints.RULES.reduce(
            (text, [pattern, to]) => text.replace(pattern, to.replace('{A}', a)),
            keyboardText
        );
    }

    /** Is this string a hint line (in either wording) that `text()` handed out? */
    static isHint(text) {
        return Hints.issued.has(text);
    }

    /** Reword every hint on screen for the input now in use. */
    static refresh(scene) {
        if (!scene || !scene.children) return;
        const visit = (o) => {
            if (o.type === 'Container') return o.list.forEach(visit);
            if (o.type !== 'Text') return;
            const source = Hints.issued.get(o.text);
            if (!source) return;
            const now = Hints.text(scene, source.keyboard, source.opts);
            if (now !== o.text) o.setText(now);
        };
        scene.children.list.forEach(visit);
    }
}

/** Every hint handed out, under both of its wordings -> { keyboard, opts }. */
Hints.issued = new Map();

/** Applied in order: the combined spellings first, single keys last. */
Hints.RULES = [
    [/\bSHIFT\s*\+\s*(?:ENTER|SPACE)\b/g, 'hold sprint + A'],
    [/\bhold SHIFT\b/g, 'hold sprint'],
    [/\b(?:SPACE\s*\/\s*ENTER|ENTER\s*\/\s*SPACE)\b/g, '{A}'],
    [/\bENTER\s*\/\s*ESC\b/g, 'A/B'],
    [/\b(?:ENTER|SPACE)\b/g, '{A}'],
    [/\bESC\b/g, 'B'],
    [/\bSHIFT\b/g, 'sprint'],
    [/\b(?:WASD\s*\/\s*arrows|arrows\s*\/\s*WASD)\b/g, 'd-pad'],
    [/↑\s*\/\s*↓|\bW\s*\/\s*S\b|\barrows\b/g, 'd-pad'],
    [/←\s*\/\s*→/g, '◀ ▶'],
    [/\bclick\b/g, 'tap'],
    [/\bClick\b/g, 'Tap'],
];

if (typeof window !== 'undefined') window.Hints = Hints;
