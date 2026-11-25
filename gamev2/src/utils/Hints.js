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
 */
class Hints {
    /** Are the on-screen touch controls in use? */
    static touch(scene) {
        return !!(scene && scene.touchControls && scene.touchControls.enabled);
    }

    static text(scene, keyboardText, opts) {
        if (!Hints.touch(scene)) return keyboardText;
        const a = opts && opts.tap ? 'TAP or A' : 'A';
        return Hints.RULES.reduce(
            (text, [pattern, to]) => text.replace(pattern, to.replace('{A}', a)),
            keyboardText
        );
    }
}

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
