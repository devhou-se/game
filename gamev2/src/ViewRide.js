/**
 * ViewRide — a ride with a view (issue #242): the lift up Fukuoka Tower, and
 * a turn on the Dotonbori wheel.
 *
 * A door into a room that is an observation deck is a lift
 * (RoomManager.liftFor): walking onto it runs lift(): the screen fades, the
 * ride plays — the inside of the glass lift, the player seen from behind, the
 * town dropping away outside as the counter on the panel climbs to 123 m — and
 * the player is standing on the deck when it lifts. The way down is the same
 * ride run backwards.
 *
 * The gondola at the foot of Osaka's wheel is bumped (check(), the `ride`
 * group of src/utils/Interactions.js): wheel() is the same sequence with no
 * room behind it — the inside of a gondola, Dotonbori sinking below its window
 * and drifting sideways as the wheel carries you over the top and back down —
 * and you step off on the cell you boarded from.
 *
 * A ride is a picture of where you are (a frame with a hole for its window)
 * over a view that pans as you rise: two tall pictures, `far` and `near`, each
 * bottom-aligned in the window on the ground and top-aligned at the top. `far`
 * is the shorter, so it moves less. `far` is opaque and carries the day sky;
 * the hour is the game's own grade: both are tinted with what the street
 * outside is multiplied by (DayNight.GRADES), and when that grade has lights a
 * third picture, the lit windows and lamps of `near`, is drawn over it
 * untinted. The deck's windows are the same pictures and the deck is graded
 * the same way, so what you rode up to is what you step out to. The art and
 * its sizes are tools/generate_tower_deck_art.py's (the lift) and
 * tools/generate_wheel_art.py's (the wheel).
 *
 * Input is locked for the ride like a flight, and like a flight it can be
 * skipped: SPACE / ENTER / ESC (A / B on touch) or a tap ends it once it has
 * been on screen for SKIP_AFTER ms.
 *
 * The rules are static functions (tools/tests/views.test.js runs them); the
 * instance only draws.
 */
class ViewRide {
    constructor(scene) {
        this.scene = scene;
        this.riding = false;
        this.picture = null;
        this.bump = null;           // the bump that boarded the gondola { cell, dx, dy }, while its key is still down
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ enter: K.ENTER, space: K.SPACE, esc: K.ESC });
    }

    /** How far through a ride, 0..1. */
    static progress(ride, elapsed) {
        return Math.max(0, Math.min(1, elapsed / ride.ms));
    }

    /**
     * How high you are, 0 (the ground) .. 1 (the top), `elapsed` ms into a
     * ride. A lift going 'up' eases away from the ground and into the top;
     * 'down' is the same ride backwards. A ride that is a `turn` (the wheel)
     * is at the top half-way through and back on the ground at the end, slow
     * at both as a wheel is, whichever way it is asked for.
     */
    static height(ride, dir, elapsed) {
        const t = ViewRide.progress(ride, elapsed);
        if (ride.turn) return (1 - Math.cos(2 * Math.PI * t)) / 2;
        const h = (1 - Math.cos(Math.PI * t)) / 2;
        return dir === 'down' ? 1 - h : h;
    }

    /**
     * How far sideways the view has slid, px, `elapsed` ms into a ride: a
     * wheel carries you across as well as up - out one way on the way up, back
     * through the middle at the top, out the other way coming down, 0 at both
     * ends - by up to ride.drift px (none for a lift). `share` is how much of
     * it a layer takes: all of it for `near`, a third for `far`.
     */
    static drift(ride, elapsed, share = 1) {
        return Math.round((ride.drift || 0) * share * Math.sin(2 * Math.PI * ViewRide.progress(ride, elapsed))) || 0;
    }

    /** What the counter reads at height `h`: whole metres. */
    static metres(ride, h) {
        return Math.round(h * ride.top);
    }

    /**
     * How far down a layer `layerH` px tall has moved behind a window `winH`
     * px tall at height `h`: 0 on the ground (its bottom edge on the window's)
     * and all of what it has to spare at the top (its top edge on the window's).
     */
    static pan(h, layerH, winH) {
        return Math.round(h * (layerH - winH));
    }

    /**
     * The beams of the tower passing the lift's window at height `h`: [{ y0, y1 }],
     * px down from the top of a window `winH` px tall, already cut to it. A beam is
     * BEAM_H thick; they are fixed to the tower at BEAMS (heights 0..1) and pass
     * BEAM_SPEED times faster than you rise, against the travel: none is in the
     * window on the ground or at the top.
     */
    static beams(h, winH) {
        const out = [];
        for (const at of ViewRide.BEAMS) {
            const y = winH / 2 + (h - at) * ViewRide.BEAM_SPEED * winH - ViewRide.BEAM_H / 2;
            const y0 = Math.max(0, Math.round(y)), y1 = Math.min(winH, Math.round(y) + ViewRide.BEAM_H);
            if (y1 > y0) out.push({ y0, y1 });
        }
        return out;
    }

    /** May the ride be skipped `elapsed` ms after it came up? Not at once (the step that boarded), not once it is ending. */
    static canSkip(ride, elapsed) {
        return elapsed >= ViewRide.SKIP_AFTER && elapsed < ride.ms;
    }

    /**
     * What the hour does to the view: { tint, lights }. `tint` is what the
     * period's grade (DayNight.GRADES) multiplies the street by - its colour at
     * its alpha over white, 0xffffff by day - and `lights` whether the lit
     * windows show. The same grade the deck gets (DayNight.gradeFor).
     */
    static tint(period) {
        const g = DayNight.GRADES[period];
        if (!g) return { tint: 0xffffff, lights: false };
        const ch = (shift) => Math.round(255 - (255 - ((g.color >> shift) & 255)) * g.alpha);
        return { tint: (ch(16) << 16) | (ch(8) << 8) | ch(0), lights: !!g.lights };
    }

    /**
     * How much the picture is magnified: as much as the world is on a phone
     * (`worldZoom`), never taller or wider than the view, never under 1. (The
     * train's and the plane's cabins only mind the height, TrainTravel.cutsceneScale:
     * a portrait phone's view is narrower than this frame, and at 1 it still
     * overhangs - so a ride's window and panel keep to its middle, SAFE_W.)
     */
    static scale(worldZoom, viewW, viewH, frameW, frameH) {
        return Math.max(1, Math.min(worldZoom || 1, viewH / frameH, viewW / frameW));
    }

    /**
     * The room kept under the picture for the skip hint, canvas px: HINT_ROOM, or
     * what a line `lineH` px tall takes once the overlays are magnified `zoom`
     * times (UIScale.wanted: on a phone the hint is drawn as big on the screen as
     * on a desktop, so in canvas px it is taller) with UIScale's margin above
     * and below it, whichever is more.
     */
    static hintRoom(lineH, zoom) {
        return Math.max(ViewRide.HINT_ROOM, Math.ceil(lineH * Math.max(1, zoom || 1)) + 2 * ViewRide.HINT_MARGIN);
    }

    /**
     * Where the picture goes in a view `W` x `H`: { k, left, top, bottom, hintY }.
     * As big as the world is drawn (scale) less the `room` the skip hint needs
     * beneath it; across the middle of the view; half-way down it, or as far up
     * as leaves that room. `hintY` is the middle of the room under it.
     */
    static layout(worldZoom, W, H, frameW, frameH, room) {
        const k = ViewRide.scale(worldZoom, W, H - room, frameW, frameH);
        const left = Math.round(W / 2 - frameW * k / 2);
        const top = Math.max(0, Math.round(Math.min((H - frameH * k) / 2, H - room - frameH * k)));
        return { k, left, top, bottom: top + frameH * k, hintY: top + frameH * k + room / 2 };
    }

    /** The lift, the picture and the swap: called by RoomManager.checkTransporter with the door stepped on. */
    lift(dir, trans) {
        const rooms = this.scene.roomManager;
        this.run(ViewRide.RIDES.lift, dir, () => rooms.switchRoomInstant(trans.targetRoom, trans.targetX, trans.targetY));
    }

    /**
     * A bump ({ cell, dx, dy }) a frame later, with `heading` ({ x, y }) held:
     * still that bump while the way it was made is down, over (null) once it is
     * let go or turned about. By what is held and not by the clock (the
     * offering box's rule, ShrineVisit.carried, ages a bump): a frame that
     * takes a quarter of a second, as the one that clears the ride's pictures
     * can on a slow phone, must not be a second 14 s turn.
     */
    static held(bump, heading) {
        if (!bump || !heading) return null;
        return (!bump.dx || heading.x === bump.dx) && (!bump.dy || heading.y === bump.dy) ? bump : null;
    }

    /** Every frame, with the direction held right now (GameScene.update): a bump whose key is still down is still that bump. */
    hold(heading) {
        this.bump = ViewRide.held(this.bump, heading);
    }

    /**
     * The player bumped a cell: board what is there to ride (the gondola at the
     * foot of the wheel). True when there was something. One ride per bump: a
     * key held against the gondola is the same bump until it is let go, so
     * stepping off with it still down is not boarding again.
     */
    check(gridX, gridY) {
        const scene = this.scene;
        const hit = scene.roomManager.interactionAt(gridX, gridY, 'ride');
        if (!hit) return false;
        const cell = `${gridX},${gridY}`, fresh = !this.bump || this.bump.cell !== cell;
        const from = scene.player || {};
        this.bump = { cell, dx: Math.sign(gridX - from.gridX) || 0, dy: Math.sign(gridY - from.gridY) || 0 };
        if (fresh && !this.riding) this.wheel();
        return true;
    }

    /** One turn of the wheel: the lift's sequence with no room behind the curtain. You get off where you got on. */
    wheel() {
        this.run(ViewRide.RIDES.wheel, 'up', null);
    }

    /** The picture: the view behind, the frame with its window cut through, the player from behind, the lift's counter. */
    buildCutscene(ride, dir) {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const c = scene.add.container(0, 0);
        c.setDepth(3000);
        c.setScrollFactor(0);
        // To UIScale the picture is a backdrop exactly the size of the view (as the plane's
        // cabin is, AirTravel.buildCutscene): drawn 1:1 on the canvas at any overlay zoom
        c.getBounds = (out) => (out || new Phaser.Geom.Rectangle()).setTo(0, 0, W, H);
        c.add(scene.add.rectangle(0, 0, W, H, 0x05060a).setOrigin(0, 0));

        const frame = scene.add.image(W / 2, H / 2, ride.frame).setOrigin(0.5, 0.5);
        // the skip hint is ordinary overlay text (UIScale keeps it readable on a phone): the
        // picture leaves it the room it will take under it
        const hint = scene.add.text(0, 0, Hints.text(scene, 'SPACE: skip the ride', { tap: true }), { fontSize: '16px', fill: '#aaaaaa',
            fontFamily: 'PixelOperatorMonoBold', backgroundColor: '#05060a', padding: { x: 10, y: 4 } });
        hint.setOrigin(0.5, 0.5); hint.setResolution(1); hint.setScrollFactor(0); hint.setDepth(3001); hint.setAlpha(0);
        const room = ViewRide.hintRoom(hint.height, scene.uiScale ? scene.uiScale.wanted() : 1);
        const { k, left, top, bottom, hintY } = ViewRide.layout(scene.uiScale && scene.uiScale.worldZoom, W, H, frame.width, frame.height, room);
        hint.setPosition(W / 2, hintY);
        frame.setScale(k);
        frame.setPosition(left + frame.displayWidth / 2, top + frame.displayHeight / 2);
        const win = ride.window, winX = left + win.x * k, winY = top + win.y * k;

        // the view: far, near, and near's lights when the hour has them. Each is cut to the
        // window every frame, so nothing shows outside the frame
        const hour = ViewRide.tint(scene.dayNight ? scene.dayNight.period() : 'day');
        const layer = (name, tint) => {
            const o = scene.add.image(0, 0, `${ride.view}-${name}`).setOrigin(0, 0).setScale(k);
            if (tint !== 0xffffff) o.setTint(tint);
            c.add(o);
            return o;
        };
        const layers = [layer('far', hour.tint), layer('near', hour.tint)];
        if (hour.lights) layers.push(layer('lights', 0xffffff));
        // the tower's beams going by (a ride with a `top`, the lift): plain shapes, not a Graphics
        // (UIScale measures what a Graphics draws). One px tall, stretched to what the window shows of each
        const beams = !ride.top ? [] : ViewRide.BEAMS.map(() => {
            const o = scene.add.rectangle(winX, winY, win.w * k, 1, ViewRide.BEAM_COLOR).setOrigin(0, 0);
            c.add(o);
            return o;
        });
        c.add(frame);

        // the player, standing at the glass with their back to you
        const upKey = scene.getDirectionalSpriteKey(scene.player.baseSpriteKey, 'up') || scene.player.baseSpriteKey;
        const standKey = scene.textures.exists(`${upKey}_frame_0`) ? `${upKey}_frame_0` : upKey;
        c.add(scene.add.image(W / 2, bottom, standKey).setOrigin(0.5, 1).setScale(2 * k));

        // the counter on its panel (a ride that has one, the lift): which way, and how high. Part
        // of the picture (it is the lift's own display, and must stay on its panel at any size), so sized with it
        let counter = null;
        if (ride.panel) {
            const panel = ride.panel, midX = left + (panel.x + panel.w / 2) * k, midY = top + (panel.y + panel.h / 2) * k;
            const s = 9 * k, ax = midX - 76 * k, tip = dir === 'down' ? s : -s;
            c.add(scene.add.triangle(0, 0, ax - s, midY - tip, ax + s, midY - tip, ax, midY + tip, ViewRide.COUNTER_COLOR).setOrigin(0, 0));
            counter = scene.add.text(midX + 14 * k, midY, '', { fontSize: `${Math.round(28 * k)}px`,
                fill: ViewRide.COUNTER_TEXT, fontFamily: 'PixelOperatorMonoBold' });
            counter.setOrigin(0.5, 0.5); counter.setResolution(1);
            c.add(counter);
        }

        let shown = null;
        const paint = (elapsed) => {
            this._elapsed = elapsed;
            const h = ViewRide.height(ride, dir, elapsed);
            layers.forEach((o, i) => {
                // `far` (the first) slides a third as far as `near` and its lights
                const cx = Math.round((o.width - win.w) / 2) + ViewRide.drift(ride, elapsed, i ? 1 : ViewRide.FAR_DRIFT);
                const cy = o.height - win.h - ViewRide.pan(h, o.height, win.h);
                o.setCrop(cx, cy, win.w, win.h);
                o.setPosition(winX - cx * k, winY - cy * k);
            });
            if (beams.length) {
                const passing = ViewRide.beams(h, win.h);
                beams.forEach((o, i) => {
                    const b = passing[i];
                    o.setVisible(!!b);
                    if (b) { o.setY(winY + b.y0 * k); o.setScale(1, (b.y1 - b.y0) * k); }
                });
            }
            if (counter) {
                const m = ViewRide.metres(ride, h);
                if (m !== shown) { shown = m; counter.setText(`${m} m`); }
            }
        };
        paint(0);
        this._cutTweens = [scene.tweens.addCounter({
            from: 0, to: ride.ms, duration: ride.ms, ease: 'Linear',
            onUpdate: (tween) => paint(tween.getValue()),
            onComplete: () => this._end && this._end(),
        })];

        // a tap anywhere is a skip: a zone over everything
        this._cutExtras = [hint];
        const tap = scene.add.zone(0, 0, W, H).setOrigin(0, 0).setScrollFactor(0).setDepth(3005);
        tap.setInteractive();
        tap.on('pointerdown', () => this.skip());
        this._cutExtras.push(tap);

        // what is on screen, for whoever measures it (tools/browser/regress.js); `counter` is null on the wheel
        this.picture = { frame, counter, hint, k, layers };

        c.setAlpha(0);
        scene.tweens.add({ targets: [c, hint], alpha: 1, duration: 220 });
        return c;
    }

    destroyCutscene(c) {
        (this._cutTweens || []).forEach(t => t.stop());
        this._cutTweens = [];
        (this._cutExtras || []).forEach(o => o.destroy());
        this._cutExtras = [];
        this.picture = null;
        c.destroy(true);
    }

    /** Called every frame by InputHandler while riding (all other input is off). */
    handleInput() {
        // through the handler's latch: a tap that is down and up again inside one frame is a press too (#253)
        if (this.scene.inputHandler.pressed(this.keys)) this.skip();
    }

    /** End the ride early, if it may be (canSkip). */
    skip() {
        if (!this.riding || !this._end || !ViewRide.canSkip(this._ride, this._elapsed)) return;
        this.skipped = true;
        this._end();
    }

    /** A ride: the curtain, `behind` it whatever changes rooms (nothing, on the wheel), the picture for ride.ms or until skipped, the curtain up. */
    run(ride, dir, behind) {
        const scene = this.scene;
        if (this.riding) return;
        const cam = scene.cameras.main, W = cam.width, H = cam.height;
        this.riding = true;
        this.skipped = false;
        this._end = null;
        this._ride = ride;
        this._elapsed = 0;
        scene.roomManager.isTransitioning = true;
        scene.inputHandler.forget(this.keys);   // a press from before the ride is not a skip

        // black curtain under the picture: the room is swapped behind it
        const curtain = scene.add.rectangle(0, 0, W, H, 0x000000)
            .setOrigin(0, 0).setScrollFactor(0).setDepth(2999).setAlpha(0);
        scene.tweens.add({
            targets: curtain, alpha: 1, duration: ViewRide.FADE,
            onComplete: () => {
                if (behind) behind();
                let ended = false;
                let cut = null;
                // the picture's own clock ends the ride (buildCutscene), or a skip does: once
                this._end = () => {
                    if (ended) return;
                    ended = true;
                    this._end = null;
                    scene.tweens.add({
                        targets: [cut].concat((this._cutExtras || []).filter(o => o.type === 'Text')), alpha: 0, duration: ViewRide.FADE,
                        onComplete: () => {
                            this.destroyCutscene(cut);
                            scene.tweens.add({
                                targets: curtain, alpha: 0, duration: 300,
                                onComplete: () => {
                                    curtain.destroy();
                                    this.riding = false;
                                    scene.roomManager.isTransitioning = false;
                                },
                            });
                        },
                    });
                };
                cut = this.buildCutscene(ride, dir);
            },
        });
    }
}

/**
 * The rides. `frame` is the picture you sit in, `view` the prefix of its three
 * layers (-far, -near, -lights), `ms` how long it is on screen unless skipped.
 * `window` is the hole in the frame, in the frame picture's own px and inside
 * its middle SAFE_W columns.
 *
 * The lift goes up and stays: `top` is the metres its counter reads at the
 * top (and what has the tower's beams pass the glass) and `panel` the plain
 * plate the counter is drawn on, as `window` is given
 * (tools/generate_tower_deck_art.py LIFT_WIN / LIFT_PANEL, doubled).
 *
 * The wheel is a `turn`: up, over and down again (height), with the view
 * sliding up to `drift` px either way as it goes (drift) - its layers are
 * that much wider than the window on each side. A gondola has no counter
 * (tools/generate_wheel_art.py WIN, doubled).
 */
ViewRide.RIDES = {
    lift: { frame: 'view-lift', view: 'view-fukuoka', ms: 4500, top: 123,
        window: { x: 128, y: 128, w: 384, h: 448 }, panel: { x: 200, y: 36, w: 240, h: 64 } },
    wheel: { frame: 'view-gondola', view: 'view-dotonbori', ms: 14000, turn: true, drift: 32,
        window: { x: 64, y: 224, w: 512, h: 320 } },
};
/** How much of a ride's drift its `far` layer takes: what is further off slides less. */
ViewRide.FAR_DRIFT = 1 / 3;
/** The columns of a frame that are in view on the narrowest portrait phone (Viewport.MIN_VISIBLE). */
ViewRide.SAFE_W = 560;
/** The earliest a press may skip a ride, ms after it came up. */
ViewRide.SKIP_AFTER = 700;
/** The least room kept under the picture for the skip hint, canvas px, and the margin UIScale keeps round an overlay (UIScale.MARGIN). */
ViewRide.HINT_ROOM = 64;
ViewRide.HINT_MARGIN = 12;
/** Fade to and from black, ms. */
ViewRide.FADE = 350;
/** The tower's beams past the lift's window: where they are (heights 0..1), how thick (frame px), how fast against the travel, their colour. */
ViewRide.BEAMS = [0.14, 0.26, 0.38, 0.5, 0.62, 0.74, 0.86];
ViewRide.BEAM_H = 20;
ViewRide.BEAM_SPEED = 5;
ViewRide.BEAM_COLOR = 0x1c1e30;
/** The counter: its arrow, its digits. */
ViewRide.COUNTER_COLOR = 0xffd27a;
ViewRide.COUNTER_TEXT = '#ffd27a';

if (typeof window !== 'undefined') window.ViewRide = ViewRide;
