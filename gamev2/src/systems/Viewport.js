/**
 * Viewport - where the game canvas sits in the browser window, and how big
 * the on-screen touch controls are.
 *
 * The game always renders 1280x960 and the canvas is scaled to fit by CSS:
 * the largest whole-integer scale when the window is big enough (crisp pixel
 * art), the exact fractional scale when it is not (phones, small laptops).
 *
 * Without touch controls the canvas has the whole window (centred
 * horizontally, at the top). With them (`#touch-controls` exists — see
 * TouchControls) the controls get a strip of the window to themselves, so
 * they never sit on top of the canvas, and the canvas is centred in the rest:
 *
 *   side    a gutter each side of the canvas   (landscape phones)
 *   bottom  a strip under the canvas           (portrait phones, 4:3 tablets)
 *
 * Whichever leaves the canvas bigger wins, and the controls shrink (down to
 * MIN_CONTROL_SCALE) when that buys the canvas more room. Wide windows have
 * gutters to spare, so there the canvas is the size it would be without
 * touch controls.
 *
 * `Viewport.apply(game)` is the single place the canvas style is written
 * (src/game.js calls it on boot and on every window resize, TouchControls
 * once its controls exist).
 */
class Viewport {
    /**
     * Pure layout: window size + whether touch controls are shown -> canvas
     * rectangle (CSS px), its scale, and the controls' scale.
     */
    static layout(winW, winH, touch) {
        const fit = (x, y, w, h, mode, controls) => {
            const exact = Math.max(0, Math.min(w / Viewport.WIDTH, h / Viewport.HEIGHT));
            const scale = exact >= 1 ? Math.floor(exact) : exact;
            const width = Viewport.WIDTH * scale, height = Viewport.HEIGHT * scale;
            return {
                mode, controls, scale, width, height,
                left: Math.floor(x + (w - width) / 2),
                // without touch controls the canvas hangs from the top of the
                // window, as it always has; beside / above the controls it is
                // centred in its space
                top: mode === 'none' ? y : Math.floor(y + (h - height) / 2),
            };
        };
        if (!touch) return fit(0, 0, winW, winH, 'none', 1);

        const C = Viewport.CONTROLS;
        // the d-pad and the button cluster share the bottom edge: on a window
        // too narrow for both at full size they shrink (below the usual
        // floor if need be) rather than overlap each other
        const room = (winW - C.padLeft - C.clusterRight - C.gap) / (C.pad + C.clusterW);
        const top = Math.max(30, Math.min(100, Math.floor(room * 20) * 5));
        let best = null;
        for (let pct = top; pct >= Math.min(top, Viewport.MIN_CONTROL_SCALE * 100); pct -= 5) {
            const c = pct / 100;
            // the widest / tallest control cluster at this scale, with its
            // screen-edge margin and a gap to the canvas
            const gutter = Math.max(C.padLeft + C.pad * c, C.clusterRight + C.clusterW * c) + C.gap;
            const strip = C.bottom + Math.max(C.pad, C.clusterH) * c + C.gap;
            for (const l of [
                fit(gutter, 0, winW - 2 * gutter, winH, 'side', c),
                fit(0, 0, winW, winH - strip, 'bottom', c),
            ]) {
                // bigger canvas first; among equals the bigger controls
                // (visited first), and side before bottom
                if (!best || l.scale > best.scale + 1e-6) best = l;
            }
        }
        return best;
    }

    /** Lay the canvas (and the touch controls' size) out for the current window. */
    static apply(game) {
        const canvas = game && game.canvas;
        if (!canvas) return null; // Phaser creates the canvas asynchronously after boot.

        const controls = document.getElementById('touch-controls');
        const l = Viewport.layout(window.innerWidth, window.innerHeight, !!controls);
        const isInteger = Math.abs(l.scale - Math.round(l.scale)) < 0.001;

        const style = canvas.style;
        style.display = 'block'; // an inline canvas leaves a text-descender gap under itself
        style.width = l.width + 'px';
        style.height = l.height + 'px';
        style.marginLeft = l.left + 'px';
        style.marginTop = l.top + 'px';
        // crisp nearest for whole-integer scales; smooth+uniform for fractional
        // (nearest-neighbour at a fractional factor gives uneven pixel widths
        // and jagged text). Sprites stay crisp internally (pixelArt:true);
        // only the final framebuffer->screen downscale is softened.
        style.imageRendering = isInteger ? 'pixelated' : 'auto';

        if (controls) controls.style.setProperty('--tc-scale', l.controls);

        // the canvas moved under Phaser's feet: re-read its bounds so pointer
        // coordinates keep mapping onto the game
        if (game.scale && game.scale.canvas) game.scale.refresh();

        Viewport.current = l;
        return l;
    }
}

Viewport.WIDTH = 1280;
Viewport.HEIGHT = 960;

/**
 * The touch controls' footprint at scale 1, in CSS px (keep in step with the
 * stylesheet in TouchControls._build): the d-pad square and its left margin,
 * the A / B / sprint cluster and its right margin, the shared bottom margin,
 * and the gap kept between a control and the canvas.
 */
Viewport.CONTROLS = { pad: 174, padLeft: 16, clusterW: 150, clusterH: 210, clusterRight: 20, bottom: 16, gap: 6 };
Viewport.MIN_CONTROL_SCALE = 0.75;

/** The layout last applied (null until the canvas exists). */
Viewport.current = null;

if (typeof window !== 'undefined') window.Viewport = Viewport;
