/**
 * UIScale - keeps the game readable when the canvas is scaled down, and
 * keeps overlays out from under the touch controls.
 *
 * Everything is drawn in fixed pixels on the 1280x960 canvas. On a phone
 * that canvas is shown at 0.3-0.4x, so a 64px cell is 20-26 CSS px and 16px
 * text is 5-6. Rather than give anything a second layout, the picture is
 * split into three layers, each drawn by its own camera and magnified as a
 * whole by as much as it can take:
 *
 *  - WORLD (everything else): on a phone or tablet the main camera zooms in
 *    (`worldScale()`, up to 2x in quarter steps), so you see fewer cells,
 *    each about as big on screen as on a small laptop. The follow deadzone
 *    shrinks to match. A mouse / keyboard window is never zoomed.
 *  - HUD (depth 1000-1999, fixed to the screen): drawn at `hudScale()` from
 *    the top-left corner. GameScene.layoutHUD lays the bar out for the
 *    narrower width that leaves it (scene event 'hudscalechange').
 *  - OVERLAYS (depth >= UIScale.MIN_DEPTH: menu, dialogue, shop, intro,
 *    pickers, ...): zoomed in on their content — the panel, portrait, photo,
 *    everything except full-screen dimmers — until it is as big as on a
 *    desktop or fills the space it has, whichever comes first. That space is
 *    the canvas less a margin, and less whatever the touch controls cover
 *    (`Viewport.current.insets`): an overlay is fitted beside the controls
 *    or above them, whichever shows it bigger, and is shrunk to fit if it
 *    has to be. Full-screen dimmers are stretched back over the whole
 *    canvas whatever the zoom.
 *  - Hint lines (anything worded by Hints.text) never go below
 *    UIScale.MIN_HINT CSS px: they are scaled up in place when their panel
 *    could not be magnified enough. So is any other single line of overlay
 *    text under UIScale.MIN_TEXT CSS px, by at most a quarter, and a float.
 *
 * On a portrait phone the window shows only a tall slice of the canvas
 * (`Viewport.current.crop`). All three cameras are given that slice as their
 * viewport, so `cameras.main.width` IS the visible width: the world follows
 * the player inside it, the HUD is laid out across it, and anything built
 * while it is in force centres itself in it. Overlays built for another
 * width (the persistent menu and dialogue, or one left up while the phone is
 * turned) are fitted into it like any other content.
 *
 * At 1:1 or larger with nothing over the canvas (any desktop-sized window)
 * none of this happens: there is one camera and everything renders exactly
 * as it is authored.
 *
 * Two opt-outs, set as a property on the game object:
 *  - `uiScaleSkip`  not an overlay at all despite its depth: it stays with
 *    the world or the HUD (the debug grid, flag labels and stats text, which
 *    must line up with the world).
 *  - `uiFloat`      magnified with the overlays but not part of anyone's
 *    content (the toast): it is kept where it was authored on the canvas
 *    — unless that is on top of the overlay's content: then it slides into
 *    the strip under or over the panel when one is tall enough (see
 *    `clearOf`), and otherwise the panel gives up a strip under itself.
 *
 * Overlays otherwise need no code for this. Phaser hit-tests through the
 * cameras, so clicks and taps on overlay rows and HUD buttons keep working.
 * The two things that must know about the zoom are anything positioning DOM
 * over an overlay (`project()` / the 'uiscalechange' scene event — see the
 * character creator's name input) and anything reading raw pointer.x /
 * pointer.y against overlay coordinates (use the handler's localX / localY
 * instead).
 *
 * Content size comes from each object's bounds. Phaser's Graphics has no
 * bounds, so the shape calls the overlays use are wrapped (trackGraphics) to
 * remember the box they drew.
 */
class UIScale {
    constructor(scene) {
        this.scene = scene;
        this.camera = null;     // overlays; created with hudCamera the first time they are needed
        this.hudCamera = null;
        this.active = false;    // are the three cameras in use?
        this.zoom = 1;          // overlays
        this.offsetX = 0;       // canvas x of overlay x: offsetX + x * zoom
        this.offsetY = 0;
        this.worldZoom = 1;
        this.deadzoneShare = 1; // of the deadzone's height (LandmarkView narrows it to look up)
        this.hudZoom = 1;
        this.viewX = 0;         // left edge of the slice of canvas the cameras draw into
        this.hudWidth = 0;      // canvas px the HUD layer has across
        this.box = null;        // content box the current zoom was fitted to
        this.cover = null;      // the dimmer that box belongs to
        this.reserve = null;    // canvas y the overlay stays above, once a float has shown under it
        scene.events.on('prerender', this.update, this);
        // before anything is laid out against the camera's width (the HUD,
        // the title screen): on a portrait phone that is the visible slice
        this.hudWidth = this.applyView();
        this.hudZoom = this.hudScale();
    }

    /** Overlay coords -> canvas coords, through the current zoom. */
    project(x, y) {
        return { x: this.viewX + this.offsetX + x * this.zoom, y: this.offsetY + y * this.zoom };
    }

    /**
     * Point every camera at the part of the canvas the window shows: all of
     * it, except on a portrait phone, where the sides are cropped.
     */
    applyView() {
        const scene = this.scene, crop = UIScale.crop();
        const x = crop.left, width = scene.scale.width - crop.left - crop.right, height = scene.scale.height;
        for (const cam of [scene.cameras.main, this.hudCamera, this.camera]) {
            if (cam && (cam.x !== x || cam.width !== width)) cam.setViewport(x, 0, width, height);
        }
        this.viewX = x;
        return width;
    }

    /** Canvas px per CSS px (1 on a desktop-sized window, 2.5 on a landscape phone). */
    down() {
        return this.scene.scale.displayScale.x;
    }

    /**
     * Is this a phone or tablet (a finger is its main pointer), or the touch
     * controls forced on with ?touch=1? Only those get the world zoomed: a
     * small desktop window keeps the whole 20 x 15 cells in view, as it
     * always has. Fixed for the session, so the view does not jump when a
     * touchscreen laptop is touched.
     */
    handheld() {
        if (this._handheld === undefined) {
            const tc = this.scene.touchControls;
            if (!tc || typeof TouchControls === 'undefined') return false;   // not built yet: ask again
            this._handheld = tc.forced || TouchControls.touchFirst();
        }
        return this._handheld;
    }

    /** The zoom that would show overlays at their authored size on screen. */
    wanted() {
        const down = this.down();
        return down > 1.02 ? Math.min(UIScale.MAX_ZOOM, down) : 1;
    }

    /**
     * How far the world camera zooms in: enough, in quarter steps (every
     * sprite pixel stays a whole number of canvas pixels), to show the world
     * at about UIScale.WORLD_TARGET of its authored size.
     */
    worldScale() {
        const down = this.down();
        if (down <= 1.02 || !this.handheld()) return 1;
        // never so far that fewer than MIN_CELLS cells fit across the view
        const cells = this.scene.cameras.main.width / (this.scene.GRID_SIZE || 64);
        const most = Math.min(UIScale.MAX_WORLD_ZOOM, Math.floor(cells / UIScale.MIN_CELLS * 4) / 4);
        return Math.max(1, Math.min(most, Math.round(UIScale.WORLD_TARGET * down * 4) / 4));
    }

    /** How much the HUD bar is magnified: enough to show it at UIScale.HUD_TARGET of its authored size. */
    hudScale() {
        const down = this.down();
        if (down <= 1.02) return 1;
        return Math.max(1, Math.min(UIScale.MAX_ZOOM, Math.round(UIScale.HUD_TARGET * down * 100) / 100));
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
        const scene = this.scene, main = scene.cameras.main, list = scene.children.list;
        const W = this.applyView(), H = main.height, cropped = W < scene.scale.width;
        const want = this.wanted(), world = this.worldScale(), hud = this.hudScale();
        const insets = UIScale.insets();
        if (want <= 1 && world === 1 && hud === 1 && !cropped && !insets.left && !insets.right) return this.release();

        if (!this.camera) {
            // drawn in this order: world, then HUD, then overlays
            this.hudCamera = scene.cameras.add(0, 0, W, H, false, 'hud');
            this.camera = scene.cameras.add(0, 0, W, H, false, 'ui');
            this.applyView();
        }
        const cam = this.camera, hudCam = this.hudCamera;

        this.setWorldZoom(world);
        hudCam.setVisible(true);
        hudCam.setOrigin(0, 0);
        hudCam.setZoom(hud);
        this.setHud(hud, W);

        // overlay objects are the tail of the depth-sorted list
        let box = null, cover = null, floatBox = null;
        const floats = [], covers = [], texts = [];
        for (let i = list.length - 1; i >= 0 && list[i].depth >= UIScale.MIN_DEPTH; i--) {
            const o = list[i];
            // measured where and as it was authored, not where we last put it
            UIScale.home(o);
            if (!o.visible || o.uiScaleSkip) continue;
            const b = UIScale.bounds(o, main);
            if (!b) continue;
            if (o.uiFloat) {
                floats.push(o);
                o._uiBox = b;
                floatBox = floatBox ? UIScale.union(floatBox, b) : b;
                continue;
            }
            // a full-screen dimmer / backdrop is not content. It is one for
            // good: a dimmer built for a narrower or wider view (the phone
            // was turned) still is, and is stretched over this one
            const full = o._uiCover || { width: W, height: H };
            if (b.x0 <= 1 && b.y0 <= 1 && b.x1 >= full.width - 1 && b.y1 >= full.height - 1) {
                o._uiCover = full;
                cover = o;
                covers.push([o, b]);
                continue;
            }
            box = box ? UIScale.union(box, b) : b;
            if (o.type === 'Text' && o.scaleX === 1 && o.scaleY === 1) texts.push({ o, box: b });
        }
        // a float decides the zoom only when it is all there is
        const alone = !box;
        if (alone) box = floatBox;

        // While one overlay is up (same dimmer) its box only grows, so a
        // blinking prompt or a row that comes and goes does not make it pulse.
        if (box && !alone && cover === this.cover && this.box) box = UIScale.union(box, this.box);
        this.box = alone ? null : box;
        this.cover = cover;

        // A float over an overlay (the shop's purchase toast) must not sit on
        // the panel's last lines. When there is a strip under or over the
        // panel tall enough to hold it, it slides there (clearOf) and the
        // panel is left alone. Otherwise the panel gives up a strip under
        // itself, and keeps it until the overlay closes, so it makes room
        // once, at the first toast, and does not pulse after.
        if (alone || !box) this.reserve = null;
        let fit = box ? UIScale.fit(box, want, W, H, insets, cropped, this.reserve, cover && cover._uiCover) : UIScale.IDENTITY;
        // floats are magnified like the overlay they are over (never shrunk
        // with it), less if that would make them wider than the canvas — or
        // than the gap between the touch controls, down where those are
        // (a line of text, in a whole view, at least as big as UIScale.MIN_TEXT)
        const down = this.down();
        const floatScale = (o) => {
            const low = o.y > H - insets.bottom - UIScale.MARGIN;
            const room = W - 2 * UIScale.MARGIN - (low ? insets.left + insets.right : 0);
            const least = o.type === 'Text' && !cropped ? UIScale.MIN_TEXT * down / parseFloat(o.style.fontSize) : 1;
            return Math.min(Math.max(1, fit.zoom, least), room / o.width);
        };
        for (const o of floats) o._uiSlide = 0;
        if (!alone && floats.length) {
            // is a float on the panel with no strip to slide into?
            const stuck = () => {
                const panel = {
                    x0: fit.offsetX + box.x0 * fit.zoom, y0: fit.offsetY + box.y0 * fit.zoom,
                    x1: fit.offsetX + box.x1 * fit.zoom, y1: fit.offsetY + box.y1 * fit.zoom,
                };
                let any = false;
                for (const o of floats) {
                    const k = floatScale(o), b = o._uiBox;      // its canvas box, grown about where it sits
                    const f = {
                        x0: o.x + (b.x0 - o.x) * k, y0: o.y + (b.y0 - o.y) * k,
                        x1: o.x + (b.x1 - o.x) * k, y1: o.y + (b.y1 - o.y) * k,
                    };
                    o._uiSlide = UIScale.clearOf(f, panel, H);
                    if (!o._uiSlide && f.x1 > panel.x0 && f.x0 < panel.x1 && f.y1 > panel.y0 && f.y0 < panel.y1) any = true;
                }
                return any;
            };
            if (this.reserve !== null || stuck()) {
                const reserve = () => {
                    const top = Math.min(...floats.map(o => o.y - o.displayOriginY * floatScale(o)));
                    return Math.min(this.reserve === null ? H : this.reserve, Math.floor(top - UIScale.MARGIN));
                };
                // twice: the float is magnified with the panel, which the strip shrinks
                for (let pass = 0; pass < 2; pass++) {
                    this.reserve = reserve();
                    fit = UIScale.fit(box, want, W, H, insets, cropped, this.reserve, cover && cover._uiCover);
                }
                for (const o of floats) o._uiSlide = 0;
            }
        }
        cam.setVisible(true);
        cam.setScroll(main.scrollX, main.scrollY);
        cam.setZoom(fit.zoom);
        cam.setOrigin(fit.originX / W, fit.originY / H);

        // one camera each: overlays, the screen-fixed HUD layer, the world
        const only = { ui: main.id | hudCam.id, hud: main.id | cam.id, world: hudCam.id | cam.id };
        for (let i = 0; i < list.length; i++) {
            const o = list[i];
            if (o.depth >= UIScale.MIN_DEPTH && !o.uiScaleSkip) o.cameraFilter = only.ui;
            else if (o.depth >= UIScale.HUD_DEPTH && !o.scrollFactorX && !o.scrollFactorY) o.cameraFilter = only.hud;
            else o.cameraFilter = only.world;
        }

        // dimmers keep covering the whole view, whatever the overlay's zoom
        // and whatever size they were built for
        for (const [o, b] of covers) {
            const sx = W / (b.x1 - b.x0), sy = H / (b.y1 - b.y0);
            if (fit === UIScale.IDENTITY && sx === 1 && sy === 1 && !b.x0 && !b.y0) continue;
            UIScale.put(o,
                ((o.x - b.x0) * sx - fit.offsetX) / fit.zoom, ((o.y - b.y0) * sy - fit.offsetY) / fit.zoom,
                o.scaleX * sx / fit.zoom, o.scaleY * sy / fit.zoom);
        }

        for (const o of floats) {
            const scale = floatScale(o);
            UIScale.put(o, (o.x - fit.offsetX) / fit.zoom, (o.y + o._uiSlide - fit.offsetY) / fit.zoom,
                o.scaleX * scale / fit.zoom, o.scaleY * scale / fit.zoom);
        }

        // text its panel could not magnify enough grows in place, as far as
        // the panel is wide: hint lines always, any other single line of
        // text where the whole canvas is in view (see textGrowth)
        for (const t of texts) {
            const o = t.o, hint = typeof Hints !== 'undefined' && Hints.isHint(o.text);
            t.hint = hint;
            t.grow = 1;
            // the point it grows about
            t.x = t.box.x0 + o.originX * (t.box.x1 - t.box.x0);
            t.y = t.box.y0 + o.originY * (t.box.y1 - t.box.y0);
            if (!hint && (cropped || o.style.wordWrapWidth || o.text.indexOf('\n') >= 0)) continue;
            const room = (box.x1 - box.x0 - 2 * UIScale.MARGIN) / o.width;
            t.grow = UIScale.textGrowth(parseFloat(o.style.fontSize), fit.zoom, down, room, hint);
        }
        for (const t of texts) {
            // a hint line stands alone; anything else stops short of the text beside it
            const grow = t.hint || t.grow <= 1.01 ? t.grow : UIScale.clearGrowth(t, texts);
            if (grow > 1.01) UIScale.put(t.o, t.o.x, t.o.y, grow, grow);
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
        this.box = this.cover = this.reserve = null;
        this.camera.setVisible(false);
        this.hudCamera.setVisible(false);
        const list = this.scene.children.list;
        for (let i = 0; i < list.length; i++) {
            UIScale.home(list[i]);
            list[i].cameraFilter = 0;
        }
        this.setWorldZoom(1);
        this.setHud(1, this.applyView());
        this.scene.events.emit('uiscalechange', this);
    }

    /** The follow deadzone's full height at the current zoom (world px), before any narrowing. */
    deadzoneHeight() {
        const dz = this.scene.cameras.main.deadzone;
        if (this._deadzoneHome) return this._deadzoneHome.height / this.worldZoom;
        return dz ? dz.height : 0;
    }

    /**
     * Keep only `share` (0..1) of the follow deadzone's height: LandmarkView
     * narrows it while the camera looks up at a landmark, every frame of the
     * ease. The rectangle is resized in place - Camera.setDeadzone would
     * re-centre the camera on the player, a jump - and stays ours, so
     * setWorldZoom does not take the narrowed height for a new size.
     * That holds for the first narrowing too: a desktop window never zooms,
     * so setWorldZoom has not sized the deadzone before the first look-up of
     * the session, and taking it over through setWorldZoom re-centred the
     * camera by however far it was trailing the player (issue #220).
     */
    setDeadzoneShare(share) {
        if (share === this.deadzoneShare) return;
        this.deadzoneShare = share;
        this.sizeDeadzone(this.worldZoom, false);
    }

    /**
     * Size the follow deadzone for `zoom`, the view's width and the share of
     * its height LandmarkView leaves it. The deadzone is whatever its owner
     * last set: a size that is not ours is taken as the new full size.
     * `recentre` true goes through Camera.setDeadzone, which puts the camera
     * back on the player (a zoom or view change redraws everything anyway);
     * false resizes the rectangle about its own centre and moves nothing.
     */
    sizeDeadzone(zoom, recentre) {
        const main = this.scene.cameras.main, dz = main.deadzone;
        if (!dz) return;
        const ours = this._deadzone;
        if (!ours || dz.width !== ours.width || dz.height !== ours.height) {
            this._deadzoneHome = { width: dz.width, height: dz.height };
        }
        // across, the same share of a cropped (portrait) view as of the whole canvas
        const share = main.width / this.scene.scale.width;
        const width = this._deadzoneHome.width * share / zoom;
        const height = this._deadzoneHome.height / zoom * this.deadzoneShare;
        if (recentre) {
            if (dz.width !== width || dz.height !== height) main.setDeadzone(width, height);
        } else {
            // it is centred on the view once a frame: keep it so
            dz.x += (dz.width - width) / 2;
            dz.y += (dz.height - height) / 2;
            dz.width = width;
            dz.height = height;
        }
        this._deadzone = { width, height };
    }

    /**
     * Zoom the world camera, and scale its follow deadzone to match (and to
     * the width of a cropped view) so the player keeps the same share of the
     * view ahead of them (sizeDeadzone).
     */
    setWorldZoom(zoom) {
        const main = this.scene.cameras.main;
        if (main.zoom !== zoom) main.setZoom(zoom);
        this.sizeDeadzone(zoom, true);
        this.worldZoom = zoom;
        const view = `${zoom}:${main.width}`;
        if (view !== this._worldView) {
            this._worldView = view;
            this.scene.events.emit('worldviewchange', this);
        }
    }

    /** The HUD layer's magnification and the canvas px it has across; tells the HUD when either changes. */
    setHud(zoom, width) {
        if (zoom === this.hudZoom && width === this.hudWidth) return;
        this.hudZoom = zoom;
        this.hudWidth = width;
        this.scene.events.emit('hudscalechange', zoom);
    }

    /**
     * How much an overlay Text of `font` px is scaled up in place so it is
     * not shown under the floor (UIScale.MIN_HINT / MIN_TEXT CSS px), when
     * the overlay camera is at `zoom` and the canvas is shown at 1 / `down`.
     * Never past `room` (panel width over the text's width), and never more
     * than the cap: a hint line stands alone under its panel and may grow
     * 1.6x; any other line has neighbours, so it grows only a quarter (and
     * stops short of them: clearGrowth) — enough for every panel on a
     * 667x375 phone, most of the way on a 568x320.
     * 1 when the text is already big enough.
     */
    static textGrowth(font, zoom, down, room, hint) {
        const css = font * zoom / down;
        const floor = hint ? UIScale.MIN_HINT : UIScale.MIN_TEXT;
        const most = hint ? UIScale.MAX_HINT_GROWTH : UIScale.MAX_TEXT_FLOOR_GROWTH;
        return Math.max(1, Math.min(most, floor / css, Math.max(1, room)));
    }

    /**
     * The most (up to `me.grow`, in steps of 0.05 down to 1) that `me` can
     * grow about its point without running into another text of `all`, each
     * of which grows too, as far as it wants and no further than `me`. Each
     * is `{ box: {x0, y0, x1, y1}, x, y, grow }`: its box, the point in it
     * that stays put, the growth it wants. Texts that already touch (a label
     * on its plate) are not in each other's way.
     */
    static clearGrowth(me, all) {
        const grown = (t, g) => ({
            x0: t.x + (t.box.x0 - t.x) * g, y0: t.y + (t.box.y0 - t.y) * g,
            x1: t.x + (t.box.x1 - t.x) * g, y1: t.y + (t.box.y1 - t.y) * g,
        });
        const hit = (a, b) => a.x1 > b.x0 && a.x0 < b.x1 && a.y1 > b.y0 && a.y0 < b.y1;
        const others = all.filter(t => t !== me && !hit(me.box, t.box));
        for (let g = me.grow; g > 1.01; g = Math.round((g - 0.05) * 100) / 100) {
            const mine = grown(me, g);
            if (!others.some(t => hit(mine, grown(t, Math.min(g, t.grow))))) return g;
        }
        return 1;
    }

    /**
     * The scale the Map overlay draws its picture at: the largest that
     * leaves room for the title above and the footer below, never past `max`
     * (1:1 unless said), and in half steps from 2 up so that pixel art keeps
     * even pixels. The side margin is what limits it where the view
     * is cropped (a portrait phone), so there it is only enough to clear the
     * frame.
     */
    static mapFit(W, H, mapW, mapH, cropped, max = 1) {
        const s = Math.min((W - (cropped ? UIScale.MAP_MARGIN_CROPPED : UIScale.MAP_MARGIN)) / mapW, (H - 170) / mapH, max);
        return s >= 2 ? Math.floor(s * 2) / 2 : s;
    }

    /** The part of the canvas the touch controls cover (canvas px in from each edge). */
    static insets() {
        const l = typeof Viewport !== 'undefined' && Viewport.current;
        return (l && l.insets) || UIScale.NO_INSETS;
    }

    /** How much of the canvas is off each side of the window (canvas px). */
    static crop() {
        const l = typeof Viewport !== 'undefined' && Viewport.current;
        return (l && l.crop) || UIScale.NO_CROP;
    }

    /**
     * Put an object back where its owner had it (if it is still where we
     * put it — otherwise the owner has moved it, and that is where it lives).
     */
    static home(o) {
        const p = o._uiPut;
        if (!p) return;
        o._uiPut = null;
        if (o.x !== p.x || o.y !== p.y || o.scaleX !== p.scaleX || o.scaleY !== p.scaleY) return;
        o.setPosition(p.home.x, p.home.y);
        o.setScale(p.home.scaleX, p.home.scaleY);
    }

    /** Move / scale an object for this frame, remembering where it came from. */
    static put(o, x, y, scaleX, scaleY) {
        const home = { x: o.x, y: o.y, scaleX: o.scaleX, scaleY: o.scaleY };
        o.setPosition(x, y);
        o.setScale(scaleX, scaleY);
        o._uiPut = { x: o.x, y: o.y, scaleX: o.scaleX, scaleY: o.scaleY, home };
    }

    /**
     * The zoom (up to `want`) and zoom origin that show `box` as large as
     * allowed inside the W x H canvas, keeping UIScale.MARGIN clear on every
     * side. With `insets` (touch controls over the bottom corners) the box
     * goes between them or above them, whichever shows it bigger. A box too
     * big for its space is shrunk to fit when something is in the way
     * (controls, room kept for a float, or `shrink`: the sides of a cropped
     * portrait view), and
     * otherwise left as authored. `below` is a canvas y the box must stay
     * above (room kept for a float), when it leaves a usable space.
     * `built` is the view size the overlay was laid out for when that is
     * not this one (the phone was turned with it up): what was centred
     * there is centred here.
     */
    static fit(box, want, W, H, insets, shrink, below, built) {
        const m = UIScale.MARGIN, ins = insets || UIScale.NO_INSETS;
        const covered = ins.left > 0 || ins.right > 0;
        const bw = box.x1 - box.x0, bh = box.y1 - box.y0;
        const floor = below && below > H / 2 ? Math.min(H - m, below) : H - m;
        const spaces = [{ x0: Math.max(m, ins.left), x1: W - Math.max(m, ins.right), y0: m, y1: floor }];
        if (covered) spaces.push({ x0: m, x1: W - m, y0: m, y1: Math.min(floor, H - Math.max(m, ins.bottom)) });
        let space = null, raw = 0;
        for (const s of spaces) {
            const z = Math.min(want, (s.x1 - s.x0) / bw, (s.y1 - s.y0) / bh);
            if (!space || z > raw + 1e-6) { space = s; raw = z; }
        }
        let zoom = Math.floor(raw * 100) / 100;
        // something is in the way: controls, the sides of a cropped view, a float's strip
        const tight = covered || shrink || floor < H - m;
        if (!tight) zoom = Math.max(1, zoom);
        // per axis: x maps to offset + x * zoom. Start from "zoom about the
        // centre" (the centre it was built around, put on this one) and slide
        // just enough to keep the box inside its space.
        const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
        const axis = (lo, hi, size, s0, s1, builtSize) => {
            const min = s0 - lo * zoom, max = s1 - hi * zoom;
            const offset = min <= max ? clamp(size / 2 - zoom * builtSize / 2, min, max) : (min + max) / 2;
            return { offset, origin: zoom !== 1 ? offset / (1 - zoom) : size / 2 };
        };
        const bW = built ? built.width : W, bH = built ? built.height : H;
        let x = axis(box.x0, box.x1, W, space.x0, space.x1, bW), y = axis(box.y0, box.y1, H, space.y0, space.y1, bH);
        if (zoom === 1 && (x.offset || y.offset)) {
            // a camera can only slide what it also scales. Out from under a
            // control is worth a hair of size; otherwise stay put
            if (!tight && bW === W) return UIScale.IDENTITY;
            zoom = 0.99;
            x = axis(box.x0, box.x1, W, space.x0, space.x1, bW);
            y = axis(box.y0, box.y1, H, space.y0, space.y1, bH);
        }
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
/** Depth at which the screen-fixed HUD layer starts (DEPTH.HUD_BACKGROUND). */
UIScale.HUD_DEPTH = 1000;
/** Canvas px kept clear around the magnified content. */
UIScale.MARGIN = 12;
UIScale.MAX_ZOOM = 3;
/** Most a full-canvas overlay's text grows (see textSize): more would bury the picture under labels. */
UIScale.MAX_TEXT_GROWTH = 1.6;
/** Share of its authored size the world is zoomed towards on a small screen (a 64px cell -> about 51 CSS px). */
UIScale.WORLD_TARGET = 0.8;
/** Past 2x there are too few cells in view (10 x 7.5 at 2x) to see where you are going. */
UIScale.MAX_WORLD_ZOOM = 2;
/** Share of its authored size the HUD bar is magnified to (16px text -> about 11 CSS px). */
UIScale.HUD_TARGET = 0.7;
/** Smallest a hint line is ever shown, in CSS px, and the most one grows to get there. */
UIScale.MIN_HINT = 10;
UIScale.MAX_HINT_GROWTH = 1.6;
/**
 * Smallest any other single line of overlay text is shown, in CSS px (#200: under it the glyphs
 * break up when the canvas is scaled down), and the most one grows in place to get there.
 */
UIScale.MIN_TEXT = 10;
UIScale.MAX_TEXT_FLOOR_GROWTH = 1.25;
/** Fewest cells across the view the world zoom will leave. */
UIScale.MIN_CELLS = 8;
/** Canvas px the Map overlay keeps clear at the sides of the overworld image, both sides together: full view, cropped view. */
UIScale.MAP_MARGIN = 120;
UIScale.MAP_MARGIN_CROPPED = 24;
/** Most the Map's picture of Japan is magnified, and how near a dot (canvas px) a debug map-click must land. */
UIScale.MAP_MAX_SCALE = 4;
UIScale.MAP_CLICK_REACH = 28;
UIScale.NO_INSETS = { left: 0, right: 0, bottom: 0 };
UIScale.NO_CROP = { left: 0, right: 0 };
UIScale.IDENTITY = { zoom: 1, offsetX: 0, offsetY: 0, originX: 0, originY: 0 };

if (typeof window !== 'undefined') {
    window.UIScale = UIScale;
    // before any overlay draws its panel
    if (typeof Phaser !== 'undefined') {
        UIScale._rect = new Phaser.Geom.Rectangle();
        UIScale.trackGraphics();
    }
}
