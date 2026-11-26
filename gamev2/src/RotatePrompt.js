/**
 * RotatePrompt - "Rotate your phone for a better experience" (issues #111, #199).
 *
 * A phone held upright shows a tall slice of the canvas, and the panels that
 * are bound by width (intro, character creator, photo caption, the drinking
 * games) come out small there. They are not given a portrait layout; the
 * player is told once, briefly, that the other way round is better. The game
 * stays fully playable in portrait underneath.
 *
 * It is a toast, not an overlay: one Text at overlay depth marked `uiFloat`
 * (magnified by UIScale like the shop's toast), not interactive and not in
 * InputHandler's overlay list, so it never owns or swallows input.
 *
 *  - Who: a touch-first device (`uiScale.handheld()`: a finger is the main
 *    pointer, or ?touch=1) held in portrait whose short side is a phone's
 *    (`RotatePrompt.wanted`). Never a desktop, a tablet, or a touchscreen
 *    laptop.
 *  - When: over the title screen — the first thing on every load, and before
 *    the creator and the intro, which are what portrait shows worst — or over
 *    the plain world. Never over anything else at overlay depth: it waits for
 *    the world to be free, and goes if an overlay opens under it. Title,
 *    creator and intro are strictly one at a time and the intro is already
 *    shrunk to the slice; a float over them would cost them a strip.
 *  - How long: `SHOW_MS`, or until a tap anywhere (the tap still does
 *    whatever it does: on the title it also starts the game), or at once when
 *    the phone is turned to landscape.
 *  - How often: once per turn into portrait, `MAX` times a session. It is not
 *    shown again until the phone has been in landscape and come back. Kept in
 *    sessionStorage (`gamev2_rotate_prompt`), so a Time Travel reload does not
 *    replay it.
 */
class RotatePrompt {
    constructor(scene) {
        this.scene = scene;
        this.text = null;
        this.timer = null;
        this.state = RotatePrompt.parse(RotatePrompt.read());
        // after the frame's input (an overlay opened this frame is seen) and
        // before UIScale lays the frame out on 'prerender'
        scene.events.on('postupdate', this.update, this);
        scene.input.on('pointerdown', () => this.hide());
    }

    /** Is this window a touch-first phone held in portrait? (CSS px) */
    static wanted(winW, winH, handheld) {
        return !!handheld && winH > winW && winW < RotatePrompt.PHONE;
    }

    /** The session's record, from its stored string (anything else: never shown, ready). */
    static parse(stored) {
        let s = null;
        try { s = JSON.parse(stored); } catch (e) { /* not ours */ }
        const shown = s && Number.isInteger(s.shown) && s.shown > 0 ? s.shown : 0;
        return { shown, armed: !s || s.armed !== false };
    }

    /**
     * One step: `portrait` is `wanted()` now, `free` is "nothing but the title
     * or the world is on screen". Returns the record to keep and whether to
     * put the prompt up now. Landscape re-arms it; showing it spends the turn.
     */
    static next(state, portrait, free) {
        if (!portrait) return { state: state.armed ? state : { shown: state.shown, armed: true }, show: false };
        if (!state.armed || state.shown >= RotatePrompt.MAX || !free) return { state, show: false };
        return { state: { shown: state.shown + 1, armed: false }, show: true };
    }

    /** Is an overlay (anything UIScale would treat as one, floats aside) on screen? */
    static overlayUp(list) {
        for (let i = list.length - 1; i >= 0; i--) {
            const o = list[i];
            if (o.depth >= RotatePrompt.OVERLAY_DEPTH && o.visible && !o.uiScaleSkip && !o.uiFloat) return true;
        }
        return false;
    }

    static read() {
        try { return sessionStorage.getItem(RotatePrompt.KEY); } catch (e) { return null; }
    }

    isVisible() { return !!this.text; }

    update() {
        const scene = this.scene, ui = scene.uiScale;
        const portrait = RotatePrompt.wanted(window.innerWidth, window.innerHeight, ui && ui.handheld());
        let free = true;
        if (portrait) {
            // the display list is only walked while the prompt is up or due
            if (!this.text && !(this.state.armed && this.state.shown < RotatePrompt.MAX)) return;
            free = (scene.titleScreen && scene.titleScreen.isVisible()) || !RotatePrompt.overlayUp(scene.children.list);
        }
        if (this.text && !(portrait && free)) this.hide();
        const { state, show } = RotatePrompt.next(this.state, portrait, free);
        if (state !== this.state) {
            this.state = state;
            try { sessionStorage.setItem(RotatePrompt.KEY, JSON.stringify(state)); } catch (e) { /* storage blocked */ }
        }
        if (show) this.show();
    }

    show() {
        this.hide();
        const scene = this.scene, cam = scene.cameras.main;
        // where the shop's toast goes: under the title's start line, clear of the HUD bar
        const o = scene.add.text(cam.width / 2, cam.height - 80, RotatePrompt.TEXT, {
            fontSize: '22px', fill: '#ffffff', fontFamily: 'PixelOperatorMonoBold', align: 'center',
            backgroundColor: 'rgba(0,0,0,0.8)', padding: { x: 14, y: 8 },
        });
        o.setOrigin(0.5, 0.5); o.setResolution(1);
        o.setScrollFactor(0); o.setDepth(RotatePrompt.DEPTH);
        o.uiFloat = true;   // UIScale: magnified, moves no overlay
        this.text = o;
        this.timer = scene.tweens.add({
            targets: o, alpha: 0, delay: RotatePrompt.SHOW_MS, duration: 400,
            onComplete: () => { if (this.text === o) this.hide(); },
        });
    }

    /** Take it down now (tap, landscape, an overlay opening, or its time is up). */
    hide() {
        if (!this.text) return;
        if (this.timer) this.timer.remove();
        this.text.destroy();
        this.text = this.timer = null;
    }
}

RotatePrompt.TEXT = 'Rotate your phone\nfor a better experience';
RotatePrompt.KEY = 'gamev2_rotate_prompt';
/** Times it may be shown in one browser session. */
RotatePrompt.MAX = 2;
RotatePrompt.SHOW_MS = 6000;
/** Short side, in CSS px, under which a touch device is a phone (the widest phones are about 430-480, the narrowest tablets 600). */
RotatePrompt.PHONE = 600;
/** Overlays start here (UIScale.MIN_DEPTH). */
RotatePrompt.OVERLAY_DEPTH = 2000;
/** Above the title screen (9000). */
RotatePrompt.DEPTH = 9500;

if (typeof window !== 'undefined') window.RotatePrompt = RotatePrompt;
