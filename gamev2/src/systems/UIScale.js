/**
 * UIScale - keeps overlay text readable when the canvas is scaled down.
 *
 * Every overlay (menu, dialogue, shop, intro, pickers, ...) is drawn in fixed
 * pixels on the 1280x960 canvas. On a phone that canvas is shown at 0.3-0.4x,
 * so 18px text ends up 6-7 CSS px tall. Rather than give each overlay a
 * second layout, the overlays are magnified as a whole:
 *
 *  - Anything at depth >= UIScale.MIN_DEPTH is "overlay" (world and HUD sit
 *    below 2000, every overlay at 2000 or above).
 *  - While the canvas is shown smaller than 1:1 and an overlay is up, the
 *    overlay objects are drawn by a second camera that zooms in on them. The
 *    zoom is what undoes the canvas downscale (so text is as big as on a
 *    desktop), capped so the overlay's content — its panel, portrait, photo,
 *    everything except full-screen dimmers — still fits on the canvas with a
 *    margin. It zooms about the canvas centre and only slides when the
 *    content would otherwise leave the canvas.
 *  - At 1:1 or larger (any desktop-sized window) nothing happens: there is no
 *    second camera and overlays render exactly as they are authored.
 *
 * Two opt-outs, set as a property on the game object:
 *  - `uiScaleSkip`  not an overlay at all despite its depth: it stays on the
 *    main camera, unmagnified (the debug grid, flag labels and stats text,
 *    which must line up with the world).
 *  - `uiFloat`      magnified with the overlays but not part of anyone's
 *    content (the toast): it never moves or shrinks the overlay it appears
 *    over, and is kept where it was authored on the canvas — unless that
 *    is on top of the overlay's content and there is room beside it, in
 *    which case it slides just off the panel (see `clearOf`).
 *
 * Overlays otherwise need no code for this. Phaser hit-tests through the zoomed
 * camera, so clicks and taps on overlay rows keep working. The two things
 * that must know about the zoom are anything positioning DOM over an overlay
 * (`project()` / the 'uiscalechange' scene event — see the character
 * creator's name input) and anything reading raw pointer.x / pointer.y
 * against overlay coordinates (use the handler's localX / localY instead).
 *
 * Content size comes from each object's bounds. Phaser's Graphics has no
 * bounds, so the shape calls the overlays use are wrapped (trackGraphics) to
 * remember the box they drew.
 */
class UIScale {
    constructor(scene) {
        this.scene = scene;
        this.camera = null;     // created the first time it is needed
        this.active = false;
        this.zoom = 1;
        this.offsetX = 0;       // canvas x of overlay x: offsetX + x * zoom
        this.offsetY = 0;
        this.box = null;        // content box the current zoom was fitted to
        this.cover = null;      // the dimmer that box belongs to
        this.floats = [];       // uiFloat objects currently placed by us
        scene.events.on('prerender', this.update, this);
    }

    /** Overlay coords -> canvas coords, through the current zoom. */
    project(x, y) {
        return { x: this.offsetX + x * this.zoom, y: this.offsetY + y * this.zoom };
    }

    /** The zoom that would show overlays at their authored size on screen. */
    wanted() {
        const down = this.scene.scale.displayScale.x; // canvas px per CSS px
        return down > 1.02 ? Math.min(UIScale.MAX_ZOOM, down) : 1;
    }

    /**
     * For an overlay that already fills the canvas and so cannot be magnified
     * (the map): a font size grown part of the way back to its desktop size
     * on screen. The same size on a desktop-sized window.
     */
    textSize(size) {
        return `${Math.round(parseFloat(size) * Math.min(UIScale.MAX_TEXT_GROWTH, this.wanted()))}px`;
    }

    /** Once a frame, after the display list is depth-sorted and before it is drawn. */
    update() {
        const want = this.wanted();
        if (want <= 1) return this.release();

        const scene = this.scene, main = scene.cameras.main, W = main.width, H = main.height;
        const list = scene.children.list;

        // overlay objects are the tail of the depth-sorted list
        let box = null, cover = null, floatBox = null;
        const floats = [];
        for (let i = list.length - 1; i >= 0 && list[i].depth >= UIScale.MIN_DEPTH; i--) {
            const o = list[i];
            if (!o.visible || o.uiScaleSkip) continue;
            if (o.uiFloat) {
                // measured where and as it was authored, not where we last put it
                if (!o._uiHome) o._uiHome = { x: o.x, y: o.y };
                o.setPosition(o._uiHome.x, o._uiHome.y).setScale(1);
                const f = UIScale.bounds(o, main);
                if (f) { floats.push(o); o._uiHome.box = f; floatBox = floatBox ? UIScale.union(floatBox, f) : f; }
                continue;
            }
            const b = UIScale.bounds(o, main);
            if (!b) continue;
            if (b.x0 <= 1 && b.y0 <= 1 && b.x1 >= W - 1 && b.y1 >= H - 1) {
                cover = o;  // a full-screen dimmer / backdrop is not content
                continue;
            }
            box = box ? UIScale.union(box, b) : b;
        }
        // a float decides the zoom only when it is all there is
        const alone = !box;
        if (alone) box = floatBox;
        this.floats = floats;
        if (!box) return this.release();

        // While one overlay is up (same dimmer) its box only grows, so a
        // blinking prompt or a row that comes and goes does not make it pulse.
        if (!alone && this.active && cover === this.cover && this.box) box = UIScale.union(box, this.box);
        this.box = alone ? null : box;
        this.cover = cover;

        const fit = UIScale.fit(box, want, W, H);
        if (!this.camera) {
            this.camera = scene.cameras.add(0, 0, W, H, false, 'ui');
        }
        const cam = this.camera;
        cam.setVisible(true);
        cam.setScroll(main.scrollX, main.scrollY);
        cam.setZoom(fit.zoom);
        cam.setOrigin(fit.originX / W, fit.originY / H);

        // overlays on the zoomed camera only, everything else on the main one
        for (let i = 0; i < list.length; i++) {
            const o = list[i];
            o.cameraFilter = o.depth >= UIScale.MIN_DEPTH && !o.uiScaleSkip ? main.id : cam.id;
        }

        // floats stay where they were authored on the canvas, at the overlay's
        // zoom (less if that would make them wider than the canvas) — moved
        // off the overlay's content when they would cover it and there is room
        const panel = alone ? null : {
            x0: fit.offsetX + box.x0 * fit.zoom, y0: fit.offsetY + box.y0 * fit.zoom,
            x1: fit.offsetX + box.x1 * fit.zoom, y1: fit.offsetY + box.y1 * fit.zoom,
        };
        for (const o of floats) {
            const home = o._uiHome, s = Math.min(1, (W - 2 * UIScale.MARGIN) / (o.width * fit.zoom));
            const k = s * fit.zoom, f = home.box;    // the float's own canvas box, grown about its home
            const dy = panel ? UIScale.clearOf({
                x0: home.x + (f.x0 - home.x) * k, y0: home.y + (f.y0 - home.y) * k,
                x1: home.x + (f.x1 - home.x) * k, y1: home.y + (f.y1 - home.y) * k,
            }, panel, H) : 0;
            o.setScale(s).setPosition((home.x - fit.offsetX) / fit.zoom, (home.y + dy - fit.offsetY) / fit.zoom);
        }

        const changed = !this.active || fit.zoom !== this.zoom ||
            fit.offsetX !== this.offsetX || fit.offsetY !== this.offsetY;
        this.active = true;
        this.zoom = fit.zoom;
        this.offsetX = fit.offsetX;
        this.offsetY = fit.offsetY;
        if (changed) scene.events.emit('uiscalechange', this);
    }

    /** Back to the plain single-camera picture. */
    release() {
        if (!this.active) return;
        this.active = false;
        this.zoom = 1;
        this.offsetX = this.offsetY = 0;
        this.box = this.cover = null;
        for (const o of this.floats) if (o.scene && o._uiHome) o.setPosition(o._uiHome.x, o._uiHome.y).setScale(1);
        this.floats = [];
        this.camera.setVisible(false);
        const list = this.scene.children.list;
        for (let i = 0; i < list.length; i++) list[i].cameraFilter = 0;
        this.scene.events.emit('uiscalechange', this);
    }

    /**
     * The zoom (1..want) and zoom origin that show `box` as large as allowed
     * inside the W x H canvas, keeping UIScale.MARGIN clear on every side.
     */
    static fit(box, want, W, H) {
        const m = UIScale.MARGIN;
        const raw = Math.min(want, (W - 2 * m) / (box.x1 - box.x0), (H - 2 * m) / (box.y1 - box.y0));
        const zoom = Math.max(1, Math.floor(raw * 100) / 100);
        // per axis: x maps to offset + x * zoom. Start from "zoom about the
        // centre", slide just enough to keep the box inside the margins, and
        // never so far that a full-screen dimmer would stop covering the canvas.
        const axis = (lo, hi, size) => {
            const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
            let offset = (size / 2) * (1 - zoom);
            const min = m - lo * zoom, max = size - m - hi * zoom;
            offset = min <= max ? clamp(offset, min, max) : (min + max) / 2;
            offset = clamp(offset, size * (1 - zoom), 0);
            return { offset, origin: zoom > 1 ? offset / (1 - zoom) : size / 2 };
        };
        const x = axis(box.x0, box.x1, W), y = axis(box.y0, box.y1, H);
        return { zoom, offsetX: x.offset, offsetY: y.offset, originX: x.origin, originY: y.origin };
    }

    /**
     * How far down (+) or up (-) the canvas box `f` must move so it no longer
     * covers `panel`: into the strip under or over the panel, centred in it,
     * whichever is the shorter trip. 0 when it covers nothing, or when
     * neither strip of the H-tall canvas is tall enough to hold it.
     */
    static clearOf(f, panel, H) {
        if (f.x1 <= panel.x0 || f.x0 >= panel.x1 || f.y1 <= panel.y0 || f.y0 >= panel.y1) return 0;
        const h = f.y1 - f.y0, mid = (f.y0 + f.y1) / 2;
        const moves = [[panel.y1, H], [0, panel.y0]]
            .filter(([lo, hi]) => hi - lo >= h)
            .map(([lo, hi]) => (lo + hi) / 2 - mid);
        return moves.length ? moves.reduce((a, b) => (Math.abs(b) < Math.abs(a) ? b : a)) : 0;
    }

    static union(a, b) {
        return {
            x0: Math.min(a.x0, b.x0), y0: Math.min(a.y0, b.y0),
            x1: Math.max(a.x1, b.x1), y1: Math.max(a.y1, b.y1),
        };
    }

    /**
     * Screen-space box of a game object at zoom 1 ({x0, y0, x1, y1}), or null
     * when it has no measurable extent.
     */
    static bounds(o, camera) {
        let b = null;
        const drawn = (g) => g._uiBounds && {
            x0: g.x + g._uiBounds.x0 * g.scaleX, y0: g.y + g._uiBounds.y0 * g.scaleY,
            x1: g.x + g._uiBounds.x1 * g.scaleX, y1: g.y + g._uiBounds.y1 * g.scaleY,
        };
        if (o.type === 'Graphics') {
            b = drawn(o);
        } else if (typeof o.getBounds === 'function') {
            const r = o.getBounds(UIScale._rect);
            if (r.width > 0 && r.height > 0) b = { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom };
            if (o.type === 'Container') {
                // Container.getBounds skips its Graphics children
                for (const child of o.list) {
                    const c = child.type === 'Graphics' && child.visible && drawn(child);
                    if (!c) continue;
                    const placed = {
                        x0: o.x + c.x0 * o.scaleX, y0: o.y + c.y0 * o.scaleY,
                        x1: o.x + c.x1 * o.scaleX, y1: o.y + c.y1 * o.scaleY,
                    };
                    b = b ? UIScale.union(b, placed) : placed;
                }
            }
        }
        if (b && camera && (o.scrollFactorX || o.scrollFactorY)) {
            const dx = camera.scrollX * o.scrollFactorX, dy = camera.scrollY * o.scrollFactorY;
            b = { x0: b.x0 - dx, y0: b.y0 - dy, x1: b.x1 - dx, y1: b.y1 - dy };
        }
        return b;
    }

    /**
     * Make Graphics remember the box of what was drawn into it (in its own
     * coordinates, as `_uiBounds`) for the shape calls the game uses. Purely
     * bookkeeping: drawing is unchanged.
     */
    static trackGraphics() {
        if (UIScale._tracking) return;
        UIScale._tracking = true;
        const proto = Phaser.GameObjects.Graphics.prototype;
        const wrap = (name, box) => {
            const original = proto[name];
            proto[name] = function (...args) {
                const [x0, y0, x1, y1] = box(args);
                const b = { x0: Math.min(x0, x1), y0: Math.min(y0, y1), x1: Math.max(x0, x1), y1: Math.max(y0, y1) };
                this._uiBounds = this._uiBounds ? UIScale.union(this._uiBounds, b) : b;
                return original.apply(this, args);
            };
        };
        const rect = ([x, y, w, h]) => [x, y, x + w, y + h];
        const circle = ([x, y, r]) => [x - r, y - r, x + r, y + r];
        const triangle = ([ax, ay, bx, by, cx, cy]) =>
            [Math.min(ax, bx, cx), Math.min(ay, by, cy), Math.max(ax, bx, cx), Math.max(ay, by, cy)];
        ['fillRect', 'strokeRect', 'fillRoundedRect', 'strokeRoundedRect'].forEach(n => wrap(n, rect));
        ['fillCircle', 'strokeCircle'].forEach(n => wrap(n, circle));
        ['fillTriangle', 'strokeTriangle'].forEach(n => wrap(n, triangle));
        const clear = proto.clear;
        proto.clear = function () {
            this._uiBounds = null;
            return clear.call(this);
        };
    }
}

/** Depth at which overlays start (the HUD tops out at 1001). */
UIScale.MIN_DEPTH = 2000;
/** Canvas px kept clear around the magnified content. */
UIScale.MARGIN = 12;
UIScale.MAX_ZOOM = 3;
/** Most a full-canvas overlay's text grows (see textSize): more would bury the picture under labels. */
UIScale.MAX_TEXT_GROWTH = 1.6;

if (typeof window !== 'undefined') {
    window.UIScale = UIScale;
    // before any overlay draws its panel
    if (typeof Phaser !== 'undefined') {
        UIScale._rect = new Phaser.Geom.Rectangle();
        UIScale.trackGraphics();
    }
}
