/**
 * Viewport - where the game canvas sits in the browser window, and where and
 * how big the on-screen touch controls are.
 *
 * The game always renders 1280x960 and the canvas is scaled to fit by CSS:
 * the largest whole-integer scale when the window is big enough (crisp pixel
 * art), the exact fractional scale when it is not (phones, small laptops).
 * It is centred in the window both ways.
 *
 * Touch controls never cost the canvas any size: the canvas is at least as
 * big with them as without. The controls sit in the bottom corners of the
 * window and are placed, in order of preference:
 *
 *   portrait  under the canvas, which GROWS to fill the height above them
 *             and lets the window crop its sides (portrait phones and
 *             tablets): a tall slice of the picture at up to twice the size
 *             instead of the whole 4:3 picture across a narrow screen
 *   side      in the black bars left and right of the canvas (landscape phones)
 *   bottom    in the black bar under the canvas, which moves up to make room
 *   over      translucent over the canvas's bottom corners, when the bars
 *             are too small to hold them (4:3 tablets, small landscape
 *             phones, touchscreen laptops)
 *
 * shrinking (down to the floor in `controlFloor`) when that is what it takes
 * to stay off the canvas. Two things about the result are reported in
 * canvas px for UIScale, which makes the game fit them:
 *
 *   crop    how much of the canvas is off each side of the window
 *           (`portrait`): every camera draws into what is left
 *   insets  how far the controls reach in over the canvas (`over`): every
 *           overlay is kept out of that, so only the corners of the world
 *           are ever under a control
 *
 * `Viewport.apply(game)` is the single place the canvas style is written
 * (src/game.js calls it on boot and on every window resize, TouchControls
 * whenever its controls appear or go away).
 */
class Viewport {
    /**
     * Pure layout: window size + whether touch controls are shown -> canvas
     * rectangle (CSS px), its scale, and the controls' mode, scale and insets.
     */
    static layout(winW, winH, touch) {
        const exact = Math.max(0, Math.min(winW / Viewport.WIDTH, winH / Viewport.HEIGHT));
        const scale = exact >= 1 ? Math.floor(exact) : exact;
        const width = Viewport.WIDTH * scale, height = Viewport.HEIGHT * scale;
        const barX = (winW - width) / 2, barY = winH - height;
        const l = {
            mode: 'none', controls: 1, scale, width, height,
            left: Math.floor(barX), top: Math.floor(barY / 2),
            crop: { left: 0, right: 0 },
            insets: { left: 0, right: 0, bottom: 0 },
        };
        if (!touch) return l;

        const C = Viewport.CONTROLS;
        // the d-pad and the button cluster share the bottom edge: on a window
        // too narrow for both at full size they shrink (below the usual
        // floor if need be) rather than overlap each other
        const room = (winW - C.padLeft - C.clusterRight - C.gap) / (C.pad + C.clusterW);
        const top = Math.max(30, Math.min(100, Math.floor(room * 20) * 5));
        const floor = Math.min(top, Viewport.controlFloor(winW, winH) * 100);
        // what a control cluster needs at scale c, with its screen-edge
        // margin and a gap to the canvas: beside the canvas, and under it
        const padW = (c) => C.padLeft + C.pad * c + C.gap;
        const clusterW = (c) => C.clusterRight + C.clusterW * c + C.gap;
        const strip = (c) => C.bottom + Math.max(C.pad, C.clusterH) * c + C.gap;

        const px = (css, by) => (by > 0 ? Math.max(0, Math.round(css / by)) : 0);

        // portrait: the canvas is as wide as the window lets it be and most
        // of the height goes spare. Fill the height instead and crop the
        // sides, while a useful width of picture is still in view.
        if (winH > winW) {
            const c = top / 100;
            const tall = Math.min(1, (winH - strip(c)) / Viewport.HEIGHT, winW / Viewport.MIN_VISIBLE);
            if (tall > scale) {
                const w = Viewport.WIDTH * tall, h = Viewport.HEIGHT * tall;
                const cropLeft = px((w - winW) / 2, tall);
                return Object.assign(l, {
                    mode: 'portrait', controls: c, scale: tall, width: w, height: h,
                    left: -cropLeft * tall, top: Math.floor((winH - strip(c) - h) / 2),
                    crop: { left: cropLeft, right: Viewport.WIDTH - cropLeft - Math.min(Viewport.WIDTH - cropLeft, px(winW, tall)) },
                });
            }
        }

        // the biggest controls that stay off the canvas; side before bottom
        for (let pct = top; pct >= floor; pct -= 5) {
            const c = pct / 100;
            if (Math.max(padW(c), clusterW(c)) <= barX) return Object.assign(l, { mode: 'side', controls: c });
            if (strip(c) <= barY) {
                // centred in the space above the controls
                l.top = Math.floor((barY - strip(c)) / 2);
                return Object.assign(l, { mode: 'bottom', controls: c });
            }
        }

        // no bar holds them: smallest controls, over the bottom corners. The
        // canvas gives up whatever spare height it has to get out from under.
        const c = floor / 100;
        l.top = Math.max(0, Math.min(l.top, Math.floor(barY - strip(c))));
        return Object.assign(l, {
            mode: 'over', controls: c,
            insets: {
                left: px(padW(c) - l.left, scale),
                right: px(clusterW(c) - (winW - l.left - width), scale),
                bottom: px(strip(c) - (winH - l.top - height), scale),
            },
        });
    }

    /**
     * The smallest the controls may get to stay off the canvas. Phones too
     * short for a comfortable d-pad anyway (under 400 CSS px on the short
     * side) go further, since every pixel of control is a pixel of game.
     */
    static controlFloor(winW, winH) {
        return Math.min(winW, winH) < Viewport.SMALL_PHONE ? Viewport.MIN_CONTROL_SCALE_SMALL : Viewport.MIN_CONTROL_SCALE;
    }

    /** Lay the canvas (and the touch controls) out for the current window. */
    static apply(game) {
        const canvas = game && game.canvas;
        if (!canvas) return null; // Phaser creates the canvas asynchronously after boot.

        const root = document.getElementById('touch-controls');
        const controls = root && root.style.display !== 'none' ? root : null;
        const l = Viewport.layout(window.innerWidth, window.innerHeight, !!controls);
        const isInteger = Math.abs(l.scale - Math.round(l.scale)) < 0.001;

        const style = canvas.style;
        style.display = 'block'; // an inline canvas leaves a text-descender gap under itself
        // out of the page flow: a 1280px-wide canvas in flow makes a phone
        // browser widen its layout viewport to fit it, and window.innerWidth
        // then reports that instead of the screen
        style.position = 'fixed';
        style.width = l.width + 'px';
        style.height = l.height + 'px';
        style.left = l.left + 'px';
        style.top = l.top + 'px';
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
 * and the gap kept between a control and the canvas. The cluster's box is
 * read from here, and TouchControls.CLUSTER places the three buttons in it.
 */
Viewport.CONTROLS = { pad: 174, padLeft: 16, clusterW: 150, clusterH: 210, clusterRight: 20, bottom: 16, gap: 6 };
Viewport.MIN_CONTROL_SCALE = 0.75;
Viewport.MIN_CONTROL_SCALE_SMALL = 0.6;
/** Short side, in CSS px, under which a window is a small phone (iPhone SE landscape is 375). */
Viewport.SMALL_PHONE = 400;
/** Least of the canvas's width, in canvas px, a cropped portrait window shows (8.75 cells). */
Viewport.MIN_VISIBLE = 560;

/** The layout last applied (null until the canvas exists). */
Viewport.current = null;

if (typeof window !== 'undefined') window.Viewport = Viewport;
