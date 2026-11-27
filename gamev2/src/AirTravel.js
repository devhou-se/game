/**
 * AirTravel — the flights (issue #218).
 *
 * The home city is overseas: no train reaches it. Each end has an airport
 * room (config `airports`, written by tools/generate_airports.py). Bumping
 * the gate or the departures board beside it (Interactions `flights`) opens
 * the departures board in flight mode (StationPicker); picking a destination
 * runs go(): the screen fades, the cabin cutscene plays — the inside of the
 * plane, the player in a window seat, the day going by outside and turning
 * to sunset — and the player is standing in front of the other airport's
 * gate when it lifts.
 *
 * Input is locked for the flight like a train ride, with one difference: a
 * flight is long enough to want skipping, so SPACE / ENTER / ESC (A / B on
 * touch) or a tap ends it once it has been on screen for SKIP_AFTER ms.
 *
 * The rules are static functions of the config (tools/tests/airports.test.js
 * runs them); the instance only draws.
 */
class AirTravel {
    constructor(scene) {
        this.scene = scene;
        this.flying = false;
        this.lastFlight = null;   // { from, to } airport keys of the last flight taken
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ enter: K.ENTER, space: K.SPACE, esc: K.ESC });
    }

    /**
     * The airports, as the departures board wants them: config `airports`
     * with every `label` filled in. An airport without one is called by the
     * name of the room it serves, so a city's name is written once
     * (rooms.<city>.name). Airports whose room or city is missing are left out.
     */
    static registry(config) {
        const out = {}, rooms = (config && config.rooms) || {};
        for (const [key, a] of Object.entries((config && config.airports) || {})) {
            if (!a || !rooms[key] || !rooms[a.serves]) continue;
            out[key] = Object.assign({}, a, { label: a.label || rooms[a.serves].name || a.serves });
        }
        return out;
    }

    /** Where you can fly from `from`: every other airport, in board order. Nowhere from a room that is no airport. */
    static destinations(config, from) {
        const all = AirTravel.registry(config);
        if (!all[from]) return [];
        return Object.keys(all).filter(k => k !== from)
            .sort((a, b) => (all[a].order || 0) - (all[b].order || 0) || (a < b ? -1 : 1));
    }

    static canFly(config, from, to) {
        return AirTravel.destinations(config, from).includes(to);
    }

    /** +1 flying down the board (out, away from the first airport), -1 flying back up it. */
    static direction(config, from, to) {
        const all = AirTravel.registry(config);
        return ((all[to] || {}).order || 0) >= ((all[from] || {}).order || 0) ? 1 : -1;
    }

    /** "Tokyo to San Franbourne" */
    static routeText(config, from, to) {
        const all = AirTravel.registry(config);
        return `${(all[from] || {}).label || from} to ${(all[to] || {}).label || to}`;
    }

    /** May the flight be skipped `elapsed` ms after the cabin came up? Not at once (the press that boarded), not once it is ending. */
    static canSkip(elapsed) {
        return elapsed >= AirTravel.SKIP_AFTER && elapsed < AirTravel.DURATION;
    }

    /** How far through the flight, 0..1. */
    static progress(elapsed) {
        return Math.max(0, Math.min(1, elapsed / AirTravel.DURATION));
    }

    /**
     * The time of day outside, 0 (bright day) .. 1 (night), `progress` of the
     * way through the flight. Flying out it runs from day to dusk; flying
     * back, the other way (night first, landing in the morning).
     */
    static skyTime(progress, dir) {
        const p = Math.max(0, Math.min(1, progress));
        return dir >= 0 ? p : 1 - p;
    }

    /**
     * The sky at time of day `f` (skyTime): { bands, sea, cloud, cloudAlpha,
     * stars } - SKY_BANDS flat colours from the top of the sky down to the
     * horizon (banded, not smooth: pixel art), the sea under it, the tint
     * and strength of the cloud, and how bright the stars are (0..1).
     *
     * It has no x: the whole window band is ONE sky, so every window shows the
     * same hour. (The first cabin slid one long day-to-dusk picture behind the
     * windows, and the front of the plane was in daylight while the back was
     * in the dark, issue #220.) The colours are the stops plane-sky.png was
     * painted from (tools/generate_sanfranbourne_art.py plane_sky).
     */
    static skyAt(f) {
        const t = Math.max(0, Math.min(1, f)), S = AirTravel.SKY;
        let i = 0;
        while (i < S.length - 2 && t > S[i + 1].f) i++;
        const a = S[i], b = S[i + 1], u = (t - a.f) / (b.f - a.f);
        const mix = (p, q, w) => p.map((v, j) => Math.trunc(v + (q[j] - v) * w));
        const hex = (c) => (c[0] << 16) | (c[1] << 8) | c[2];
        const top = mix(a.top, b.top, u), horizon = mix(a.horizon, b.horizon, u);
        const bands = [];
        for (let n = 0; n < AirTravel.SKY_BANDS; n++) bands.push(hex(mix(top, horizon, n / AirTravel.SKY_BANDS)));
        const ramp = (lo, hi) => Math.max(0, Math.min(1, (t - lo) / (hi - lo)));
        // cloud: white by day, lit pink near the sunset, dusky after it, gone by night
        const day = [255, 255, 255], lit = [255, 214, 190], dusk = [190, 130, 160];
        const cloud = t < 0.65 ? mix(day, lit, ramp(0.5, 0.65)) : mix(lit, dusk, ramp(0.65, 0.8));
        return { bands, sea: hex(mix(a.sea, b.sea, u)), cloud: hex(cloud), cloudAlpha: 0.85 * (1 - ramp(0.82, 0.95)), stars: ramp(0.84, 0.94) };
    }

    /**
     * Where the clouds are `elapsed` ms into a flight: [{ x, y, w, h }] in the
     * cabin picture's own px (x from its left edge, y from the middle of the
     * window band; x is the cloud's centre). Each drifts at its own speed the
     * other way to the flight and comes round again, so it passes one window
     * after another: at any moment the windows share a sky and differ only in
     * which cloud is going by.
     */
    static clouds(elapsed, dir) {
        const span = AirTravel.CABIN_W + 2 * AirTravel.CLOUD_MARGIN, out = [];
        for (let i = 0; i < AirTravel.CLOUDS; i++) {
            const start = ((i * 0.618034) % 1) * span, speed = 26 + (i * 17) % 30;       // px a second
            const moved = start - (dir >= 0 ? 1 : -1) * speed * elapsed / 1000;
            out.push({
                x: (((moved % span) + span) % span) - AirTravel.CLOUD_MARGIN,
                y: -10 + (i * 5) % 13, w: 22 + (i * 11) % 20, h: 5,
            });
        }
        return out;
    }

    /** The x of the middle of each window, in the cabin picture's own px. */
    static windows() {
        const out = [];
        for (let x = AirTravel.WINDOW_FIRST; x < AirTravel.CABIN_W - 14; x += AirTravel.WINDOW_STEP) out.push(x);
        return out;
    }

    /** The airport the player last flew into `roomKey` from, or null. */
    cameFrom(roomKey) {
        return this.lastFlight && this.lastFlight.to === roomKey ? this.lastFlight.from : null;
    }

    /** The cabin: sky behind, clouds passing, the cabin wall with its windows cut through, the player seated. */
    buildCutscene(fromKey, toKey, dir) {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const c = scene.add.container(0, 0);
        c.setDepth(3000);
        c.setScrollFactor(0);
        // To UIScale the picture is a backdrop exactly the size of the view, whatever runs
        // off its sides (the cabin and the sky are wider than the view): it is drawn 1:1 on
        // the canvas at any overlay zoom, and never squeezed to fit like a dimmer built for
        // another size.
        c.getBounds = (out) => (out || new Phaser.Geom.Rectangle()).setTo(0, 0, W, H);
        c.add(scene.add.rectangle(0, 0, W, H, 0x05060a).setOrigin(0, 0));

        // the cabin picture is the train interiors' size and is shown the same way: at 2x,
        // magnified as much as the world is on a phone, never taller than the view
        // (TrainTravel.cutsceneScale, #201)
        const cabin = scene.add.image(W / 2, H / 2, 'plane-interior').setOrigin(0.5, 0.5);
        const k = TrainTravel.cutsceneScale(scene.uiScale && scene.uiScale.worldZoom, H, cabin.height * 2);
        cabin.setScale(2 * k);
        const carW = cabin.displayWidth, carH = cabin.displayHeight;
        const carLeft = W / 2 - carW / 2, carTop = H / 2 - carH / 2;

        // one sky behind the whole window band, so every window shows the same hour: it is
        // repainted as the flight goes (skyAt), day to dusk flying out and dusk to day flying
        // home, with the cloud drifting past window after window (clouds)
        const u = 4 * k;                                   // one px of the cabin art on screen: the picture is saved at 2x and shown at 2k
        const bandY = carTop + carH * AirTravel.WINDOW_BAND;
        const skyTop = bandY - AirTravel.SKY_H / 2 * u, bandH = AirTravel.SKY_HORIZON / AirTravel.SKY_BANDS * u;
        // plain shapes, not a Graphics: UIScale measures what a Graphics draws, and one wider
        // than the view would have the whole picture squeezed to fit a phone
        const shape = (o) => { c.add(o); return o; };
        const bands = [];
        for (let n = 0; n < AirTravel.SKY_BANDS; n++) {
            bands.push(shape(scene.add.rectangle(carLeft, skyTop + n * bandH, carW, bandH + 1, 0xffffff).setOrigin(0, 0)));
        }
        // the same few stars in every window: they are too far off to pass by
        const stars = [];
        for (const wx of AirTravel.windows()) {
            for (const [sx, sy] of AirTravel.STARS) {
                stars.push(shape(scene.add.rectangle(carLeft + (wx + sx) * u, bandY + sy * u, u, u, 0xffffe6).setOrigin(0, 0)));
            }
        }
        const puffs = AirTravel.clouds(0, dir).map((cloud) => shape(scene.add.ellipse(0, bandY + cloud.y * u, cloud.w * u, cloud.h * u, 0xffffff)));
        const sea = shape(scene.add.rectangle(carLeft, skyTop + AirTravel.SKY_HORIZON * u, carW,
            (AirTravel.SKY_H - AirTravel.SKY_HORIZON) * u, 0xffffff).setOrigin(0, 0));
        const paint = (progress) => {
            const now = AirTravel.skyAt(AirTravel.skyTime(progress, dir));
            now.bands.forEach((color, n) => bands[n].setFillStyle(color, 1));
            sea.setFillStyle(now.sea, 1);
            for (const star of stars) star.setAlpha(now.stars);
            AirTravel.clouds(progress * AirTravel.DURATION, dir).forEach((cloud, i) => {
                puffs[i].setX(carLeft + cloud.x * u);
                puffs[i].setFillStyle(now.cloud, now.cloudAlpha);
            });
        };
        paint(0);
        this._cutTweens = [scene.tweens.addCounter({
            from: 0, to: 1, duration: AirTravel.DURATION, ease: 'Linear',
            onUpdate: (tween) => paint(tween.getValue()),
        })];
        c.add(cabin);

        // the player in a window seat: the standing front frame, legs cropped at the cushion
        const downKey = scene.getDirectionalSpriteKey(scene.player.baseSpriteKey, 'down')
            || scene.player.baseSpriteKey;
        const standKey = scene.textures.exists(`${downKey}_frame_0`) ? `${downKey}_frame_0` : downKey;
        const rider = scene.add.image(W / 2, carTop + carH * AirTravel.SEAT_LINE, standKey)
            .setOrigin(0.5, 1).setScale(1.5 * k);
        rider.setCrop(0, 0, rider.frame.width, rider.frame.height * 0.72);
        c.add(rider);

        // the cabin barely moves: a slow bob, not a train's rumble
        this._cutTweens.push(scene.tweens.add({
            targets: [cabin, rider], y: `+=${2 * k}`, duration: 1100, yoyo: true, repeat: -1, ease: 'Sine.easeInOut',
        }));

        // the route and the skip hint are ordinary overlay text (UIScale keeps them readable
        // on a phone), and a tap anywhere is a skip: a zone over everything
        this._cutExtras = [];
        const text = (y, t, size, color) => {
            const o = scene.add.text(W / 2, y, t, { fontSize: size, fill: color, fontFamily: 'PixelOperatorMonoBold',
                backgroundColor: '#05060a', padding: { x: 10, y: 4 } });
            o.setOrigin(0.5, 0.5); o.setResolution(1); o.setScrollFactor(0); o.setDepth(3001); o.setAlpha(0);
            this._cutExtras.push(o);
            return o;
        };
        text(H / 2 - 270, AirTravel.routeText(scene.config, fromKey, toKey), '24px', '#ffffff');
        text(H / 2 + 270, Hints.text(scene, 'SPACE: skip the flight', { tap: true }), '16px', '#aaaaaa');
        const tap = scene.add.zone(0, 0, W, H).setOrigin(0, 0).setScrollFactor(0).setDepth(3005);
        tap.setInteractive();
        tap.on('pointerdown', () => this.skip());
        this._cutExtras.push(tap);

        c.setAlpha(0);
        scene.tweens.add({ targets: [c].concat(this._cutExtras.filter(o => o.type === 'Text')), alpha: 1, duration: 220 });
        return c;
    }

    destroyCutscene(c) {
        (this._cutTweens || []).forEach(t => t.stop());
        this._cutTweens = [];
        (this._cutExtras || []).forEach(o => o.destroy());
        this._cutExtras = [];
        c.destroy(true);
    }

    /** Called every frame by InputHandler while flying (all other input is off). */
    handleInput() {
        // through the handler's latch: a tap that is down and up again inside one frame is a press too (#253)
        if (this.scene.inputHandler.pressed(this.keys)) this.skip();
    }

    /** End the flight early, if it may be (canSkip). */
    skip() {
        if (!this.flying || !this._land || !AirTravel.canSkip(this.scene.time.now - this._started)) return;
        this.skipped = true;
        this._land();
    }

    /** The flight. */
    go(fromKey, toKey) {
        const scene = this.scene;
        if (this.flying || !AirTravel.canFly(scene.config, fromKey, toKey)) return;
        const to = AirTravel.registry(scene.config)[toKey];
        const cam = scene.cameras.main, W = cam.width, H = cam.height;
        const dir = AirTravel.direction(scene.config, fromKey, toKey);
        this.flying = true;
        this.skipped = false;
        this._land = null;
        this.lastFlight = { from: fromKey, to: toKey };
        scene.roomManager.isTransitioning = true;
        scene.inputHandler.forget(this.keys);   // the press that boarded is not a skip

        const player = scene.player;
        // black curtain under the cutscene: the room is swapped behind it
        const curtain = scene.add.rectangle(0, 0, W, H, 0x000000)
            .setOrigin(0, 0).setScrollFactor(0).setDepth(2999).setAlpha(0);
        scene.tweens.add({
            targets: curtain, alpha: 1, duration: AirTravel.FADE,
            onComplete: () => {
                scene.roomManager.switchRoomInstant(toKey, to.arrive[0], to.arrive[1]);
                player.updateDirectionSprite(0, 1);       // step off facing the lounge
                player.setIdleFrame();
                const cut = this.buildCutscene(fromKey, toKey, dir);
                this._started = scene.time.now;
                let landed = false;
                const timer = scene.time.delayedCall(AirTravel.DURATION, () => this._land && this._land());
                this._land = () => {
                    if (landed) return;
                    landed = true;
                    this._land = null;
                    timer.remove(false);
                    scene.tweens.add({
                        targets: [cut].concat((this._cutExtras || []).filter(o => o.type === 'Text')), alpha: 0, duration: AirTravel.FADE,
                        onComplete: () => {
                            this.destroyCutscene(cut);
                            scene.tweens.add({
                                targets: curtain, alpha: 0, duration: 300,
                                onComplete: () => {
                                    curtain.destroy();
                                    this.flying = false;
                                    scene.roomManager.isTransitioning = false;
                                },
                            });
                        },
                    });
                };
            },
        });
    }
}

/** How long the cabin is on screen, ms, unless skipped. */
AirTravel.DURATION = 9000;
/** The earliest a press may skip it, ms after the cabin came up. */
AirTravel.SKIP_AFTER = 700;
/** Fade to and from black, ms. */
AirTravel.FADE = 350;
/** The middle of the cabin's window band, and the seat cushion the rider sits on, as fractions of its height (tools/generate_sanfranbourne_art.py plane_interior). */
AirTravel.WINDOW_BAND = 33 / 120;
/** The cabin picture at 1x: its width, and the middles of its windows (the first, and one every WINDOW_STEP). */
AirTravel.CABIN_W = 364;
AirTravel.WINDOW_FIRST = 13;
AirTravel.WINDOW_STEP = 26;
/** The sky behind the window band, in the cabin picture's px: its height, the row of the horizon, the colour bands above it. */
AirTravel.SKY_H = 44;
AirTravel.SKY_HORIZON = 31;
AirTravel.SKY_BANDS = 6;
/** The day outside, bright day to night: at time `f`, the colour at the top of the sky, at the horizon, and of the sea. */
AirTravel.SKY = [
    { f: 0.00, top: [86, 150, 232], horizon: [170, 214, 250], sea: [58, 104, 176] },
    { f: 0.45, top: [92, 150, 226], horizon: [190, 220, 246], sea: [60, 100, 168] },
    { f: 0.62, top: [110, 120, 190], horizon: [250, 190, 120], sea: [86, 86, 140] },
    { f: 0.74, top: [96, 70, 140], horizon: [248, 140, 80], sea: [90, 60, 100] },
    { f: 0.88, top: [40, 36, 90], horizon: [150, 80, 110], sea: [40, 36, 80] },
    { f: 1.00, top: [16, 18, 48], horizon: [50, 44, 96], sea: [18, 20, 52] },
];
/** How many clouds are in the air, and how far past each end of the cabin one goes before it comes round. */
AirTravel.CLOUDS = 7;
AirTravel.CLOUD_MARGIN = 40;
/** The stars in a window, px from the middle of the window and of the band. */
AirTravel.STARS = [[-4, -9], [2, -5], [-1, 1], [4, -11]];
AirTravel.SEAT_LINE = 84 / 120;

if (typeof window !== 'undefined') window.AirTravel = AirTravel;
