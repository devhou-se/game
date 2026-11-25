/**
 * TrafficLights - makes the street signals cycle (issue #19).
 *
 * Purely decorative: nothing waits for a green man and no cell is ever gated.
 * A signal is one `traffic-light_0_0` sprite on a room's Collidables layer (the
 * `traffic-light` prefab: vehicle head, pedestrian head and pole in one piece).
 * Its four frames are separate textures drawn by tools/extract_street.py, and
 * this class swaps the texture of every signal on screen through one shared
 * cycle - the pedestrian lamps run opposite the vehicle lamps:
 *
 *   go      vehicles green, pedestrians red
 *   amber   vehicles amber, pedestrians red
 *   stop    vehicles red,   pedestrians green
 *   blink   vehicles red,   the green man flashing (about to change)
 *
 * It keeps no per-room state and needs no room-change hook: on every tick it
 * looks at whatever tile sprites RoomManager currently has loaded, so it keeps
 * working however rooms are loaded or stitched together. Maps place the green
 * frame, so freshly loaded tiles are also noticed every frame (before render)
 * and put on the current phase at once - a room never opens on a wrong green.
 *
 * At night the DayNight grade darkens every tile, lamps included, so the lit
 * lamps are re-lit: one additive Graphics above the grade (like DayNight's
 * lantern halos) paints each lit lamp and a small halo around it.
 */
class TrafficLights {
    constructor(scene) {
        this.scene = scene;
        this.clockOffset = 0;     // test hook: ms added to the clock, to jump to a phase
        this.source = null;       // the floorSprites array the signal list was built from
        this.count = -1;
        this.signals = [];
        this.glow = scene.add.graphics();     // the lit lamps at night, over the night grade
        this.glow.setBlendMode(Phaser.BlendModes.ADD).setDepth(955);
        this.glowState = '';
        this.timer = scene.time.addEvent({
            delay: TrafficLights.TICK, loop: true, callback: () => this.tick(),
        });
        // newly loaded tiles get the right frame before they are first drawn
        this.onUpdate = () => { if (this.stale()) this.tick(); };
        scene.events.on('update', this.onUpdate);
        scene.events.once('shutdown', () => scene.events.off('update', this.onUpdate));
        this.tick();
    }

    /** Has RoomManager (re)loaded tiles since the signal list was built? */
    stale() {
        const sprites = this.scene.roomManager.floorSprites || [];
        return sprites !== this.source || sprites.length !== this.count;
    }

    /** Where the shared cycle is now: { name, key } of the frame to show. */
    phase(now = Date.now() + this.clockOffset) {
        let t = now % TrafficLights.CYCLE;
        for (const p of TrafficLights.PHASES) {
            if (t < p.ms) {
                if (p.name !== 'blink') return { name: p.name, key: p.key };
                // the green man flashes: lit and dark alternate every BLINK ms
                const lit = Math.floor(t / TrafficLights.BLINK) % 2 === 1;
                return { name: p.name, key: lit ? TrafficLights.KEYS.stop : p.key };
            }
            t -= p.ms;
        }
        return TrafficLights.PHASES[0];
    }

    /** The signal sprites of the room(s) on screen (re-read when the tiles are reloaded). */
    current() {
        const sprites = this.scene.roomManager.floorSprites || [];
        if (this.stale()) {
            this.source = sprites;
            this.count = sprites.length;
            this.signals = sprites.filter(s => s.texture && TrafficLights.FRAME.test(s.texture.key));
        }
        return this.signals;
    }

    tick() {
        const key = this.phase().key;
        if (!this.scene.textures.exists(key)) return;
        const fresh = this.stale();
        for (const s of this.current()) {
            if (s.active && s.texture.key !== key) s.setTexture(key);
        }
        this.drawGlow(key, fresh);
    }

    /** Is the night grade (the one that turns lamps on) over the world right now? */
    dark() {
        const dn = this.scene.dayNight;
        if (!dn || !dn.grade || !dn.grade.visible) return false;
        const grade = DayNight.GRADES[dn.period()];
        return !!(grade && grade.lights);
    }

    /** Re-light the lit lamps of every signal over the night grade (redrawn only on a change). */
    drawGlow(key, fresh) {
        const dark = this.dark();
        const state = `${dark}|${key}`;
        if (!fresh && state === this.glowState) return;
        this.glowState = state;
        this.glow.clear();
        if (!dark) return;
        for (const s of this.signals) {
            if (!s.active) continue;
            const o = s.getTopLeft();
            for (const [x, y, w, h, color] of TrafficLights.LAMPS[key] || []) {
                const cx = o.x + x + w / 2, cy = o.y + y + h / 2;
                this.glow.fillStyle(color, 0.06);
                this.glow.fillCircle(cx, cy, 30);
                this.glow.fillCircle(cx, cy, 20);
                this.glow.fillStyle(color, 0.5);
                this.glow.fillRect(o.x + x, o.y + y, w, h);
            }
        }
    }
}

TrafficLights.TICK = 200;      // ms between looks at the clock
TrafficLights.BLINK = 400;     // ms per half of the green man's flash
TrafficLights.KEYS = {
    go: 'traffic-light_0_0',
    amber: 'traffic-light-amber_0_0',
    stop: 'traffic-light-stop_0_0',
    blink: 'traffic-light-stop-blink_0_0',
};
// any frame of a signal (so a sprite is still recognised after its texture was swapped)
TrafficLights.FRAME = /^traffic-light(-amber|-stop|-stop-blink)?_0_0$/;
TrafficLights.PHASES = [
    { name: 'go', key: TrafficLights.KEYS.go, ms: 6000 },
    { name: 'amber', key: TrafficLights.KEYS.amber, ms: 1600 },
    { name: 'stop', key: TrafficLights.KEYS.stop, ms: 5200 },
    { name: 'blink', key: TrafficLights.KEYS.blink, ms: 2400 },
];
// the lit lamps of each frame, in sprite pixels from its top-left: [x, y, w, h, colour]
// (the lamp rectangles and colours of tools/extract_street.py's traffic_light(), at 2x)
(() => {
    const GREEN = 0x54c4a0, AMBER = 0xf0be54, RED = 0xe25442;
    const vehicle = (i, c) => [8 + i * 18, 16, 12, 14, c];
    const MAN_RED = [22, 56, 20, 20, RED], MAN_GREEN = [22, 80, 20, 20, GREEN];
    TrafficLights.LAMPS = {
        [TrafficLights.KEYS.go]: [vehicle(0, GREEN), MAN_RED],
        [TrafficLights.KEYS.amber]: [vehicle(1, AMBER), MAN_RED],
        [TrafficLights.KEYS.stop]: [vehicle(2, RED), MAN_GREEN],
        [TrafficLights.KEYS.blink]: [vehicle(2, RED)],
    };
})();
TrafficLights.CYCLE = TrafficLights.PHASES.reduce((sum, p) => sum + p.ms, 0);

if (typeof window !== 'undefined') window.TrafficLights = TrafficLights;
