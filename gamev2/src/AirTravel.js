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
     * How far the sky has slid past the windows, px: 0..`travel`. Flying out
     * it runs from the day end to the dusk end; flying back, the other way
     * (night first, landing in the morning).
     */
    static skyShift(progress, dir, travel) {
        const p = Math.max(0, Math.min(1, progress));
        return travel * (dir >= 0 ? p : 1 - p);
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

        // the sky slides slowly behind the windows for the whole flight
        const bandY = carTop + carH * AirTravel.WINDOW_BAND;
        const sky = scene.add.image(carLeft, bandY, 'plane-sky').setOrigin(0, 0.5).setScale(2 * k);
        const travel = Math.max(0, sky.displayWidth - carW);
        sky.setX(carLeft - AirTravel.skyShift(0, dir, travel));
        c.add(sky);
        this._cutTweens = [scene.tweens.add({
            targets: sky, x: carLeft - AirTravel.skyShift(1, dir, travel),
            duration: AirTravel.DURATION, ease: 'Linear',
        })];
        // near cloud, quicker than the sky, going the other way to the flight
        for (let i = 0; i < 4; i++) {
            const y = bandY - carH * 0.06 + (i % 3) * carH * 0.05;
            const puff = scene.add.ellipse(0, y, (150 + i * 40) * k, 22 * k, 0xffffff, 0.5);
            const off = 200 * k;
            puff.setX(dir > 0 ? W + off : -off);
            c.add(puff);
            this._cutTweens.push(scene.tweens.add({
                targets: puff, x: dir > 0 ? -off : W + off,
                duration: 2600 + i * 700, repeat: -1, delay: i * 900,
            }));
        }
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
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.space) || JD(k.enter) || JD(k.esc)) this.skip();
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
        const JD = Phaser.Input.Keyboard.JustDown;
        [this.keys.enter, this.keys.space, this.keys.esc].forEach(JD);   // the press that boarded is not a skip

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
AirTravel.SEAT_LINE = 84 / 120;

if (typeof window !== 'undefined') window.AirTravel = AirTravel;
