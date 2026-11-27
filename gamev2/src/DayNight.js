/**
 * DayNight - real-time day/night cycle (issue #2).
 *
 * Time of day follows the real clock in Tokyo (JST, UTC+9) with four periods:
 * Dawn 5-7, Day 7-19, Dusk 19-21, Night 21-5. Day renders untouched; dawn and
 * dusk get a warm colour grade; night gets a dark blue grade plus warm glow
 * halos on every lamp post / lantern already placed in the room's Tiled map,
 * and the glow spots a placed sprite declares (src/utils/Glows.js: neon
 * boards, lit shop fronts).
 *
 * The grade is a camera-fixed MULTIPLY rectangle at depth 950 — above the
 * whole world and its labels (<= 900), below the HUD (1000) and the train-ride
 * cutscene (~3000). Glows sit just above the grade so they cut through the
 * darkness. Interior rooms ("interior": true in config) are never graded -
 * except one lit by lanterns ("lanternLight": true, a shrine's worship hall):
 * at night it dims a little and its lanterns glow; by day it is untouched -
 * and one whose light is the sky's ("daylight": true, the observation deck up
 * Fukuoka Tower, all window): it is graded by the hour exactly as the street is.
 *
 * ?tod=dawn|day|dusk|night pins the period for testing.
 */
class DayNight {
    constructor(scene) {
        this.scene = scene;
        this.glows = [];
        this.lights = false;

        const forced = new URLSearchParams(window.location.search).get('tod');
        this.forced = ['dawn', 'day', 'dusk', 'night'].includes(forced) ? forced : null;

        const cam = scene.cameras.main;
        this.grade = scene.add.rectangle(0, 0, cam.width, cam.height, 0xffffff, 1);
        this.grade.setOrigin(0, 0);
        this.grade.setScrollFactor(0);
        this.grade.setDepth(950);
        this.grade.setBlendMode(Phaser.BlendModes.MULTIPLY);
        this.grade.setVisible(false);

        this.apply();
        // the period only changes on real-world hours — a minute tick is plenty
        scene.time.addEvent({ delay: 60000, loop: true, callback: () => this.apply() });
    }

    /** Current period name in Tokyo (or the ?tod= override). */
    period() {
        if (this.forced) return this.forced;
        const now = new Date();
        const h = (now.getUTCHours() + 9) % 24;   // JST
        if (h >= 5 && h < 7) return 'dawn';
        if (h >= 7 && h < 19) return 'day';
        if (h >= 19 && h < 21) return 'dusk';
        return 'night';
    }

    /** Re-grade for the current room + period. Called on init, room change, minute tick. */
    apply() {
        const roomKey = this.scene.roomManager.currentRoom;
        const roomCfg = this.scene.config.rooms[roomKey] || {};
        const grade = DayNight.gradeFor(roomCfg, this.period());

        if (!grade) {
            this.grade.setVisible(false);
        } else {
            this.grade.setFillStyle(grade.color, grade.alpha);
            this.grade.setVisible(true);
        }

        // are the room's lights on (night outdoors, a lantern-lit hall at night)? Read by
        // whatever else lights up with the lamps (AmbientTrams: a car's windows and headlight)
        this.lights = !!(grade && grade.lights);
        this.clearGlows();
        if (this.lights) this.buildGlows(roomKey);
    }

    onRoomChange() {
        this.apply();
    }

    /**
     * A warm additive halo on every lamp/lantern tile in the room's layers.
     * Lanterns are 2-cell stacks — a cell with a matching cell directly above
     * it is a stack's lower half and gets no halo of its own.
     */
    buildGlows(roomKey) {
        const GS = this.scene.GRID_SIZE;
        const cells = new Set();
        const rm = this.scene.roomManager;
        const owner = (x, y) => (rm.districtsAt(x, y, roomKey)[0] || {}).room;
        for (const layer of (rm.rooms[roomKey].layers || [])) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (/lamp-post|-lanterns/.test(key)) cells.add(xy);
            }
        }
        for (const xy of cells) {
            const [gx, gy] = xy.split(',').map(Number);
            // lower half of a stack — unless the cell above belongs to another
            // district of a stitched city: that is the foot of the neighbour's
            // lantern, standing right above this one's top
            if (cells.has(`${gx},${gy - 1}`) && owner(gx, gy - 1) === owner(gx, gy)) continue;

            const g = this.scene.add.graphics();
            // stepped radial falloff — reads as a soft halo in the pixel look
            for (let i = 6; i >= 1; i--) {
                g.fillStyle(0xffb366, 0.028 * (7 - i));
                g.fillCircle(0, 0, (GS * 1.6 * i) / 6);
            }
            g.setPosition(gx * GS + GS / 2, gy * GS + GS / 2 - GS * 0.15);
            g.setBlendMode(Phaser.BlendModes.ADD);
            g.setDepth(955);   // over the night grade, under the HUD
            this.glows.push(g);
        }
        this.buildSpriteGlows();
        this.cullGlows();
    }

    /**
     * The glow spots of the placed sprites that declare some (Glows: a neon
     * board, a lit shop front), each a tinted copy of one halo texture. A room
     * with no such sprite gets nothing, and not even the texture is made.
     */
    buildSpriteGlows() {
        const scene = this.scene, GS = scene.GRID_SIZE;
        if (typeof Glows === 'undefined') return;
        const meta = (scene.config && scene.config.spriteMetadata) || {};
        const byKey = new Map();
        for (const rec of (scene.roomManager.tileRecords || [])) {
            let spots = byKey.get(rec.key);
            if (spots === undefined) byKey.set(rec.key, spots = Glows.spotsFor(rec.key, meta[rec.key]));
            if (!spots.length) continue;
            for (const halo of Glows.place(rec.left, rec.top, GS * ((rec.config && rec.config.scale) || 1), spots)) {
                const img = scene.add.image(halo.x, halo.y, Glows.texture(scene));
                img.setDisplaySize(halo.rx * 2, halo.ry * 2);
                img.setTint(halo.color);
                img.setAlpha(halo.alpha);
                img.setBlendMode(Phaser.BlendModes.ADD);
                img.setDepth(955);
                if (Glows.animated(halo)) img.halo = halo;
                // the glow belongs to this copy of the sprite: it fades with it (Occlusion, rec.fade)
                img.rec = rec;
                img.strength = halo.alpha;
                this.glows.push(img);
            }
        }
    }

    /**
     * Only the halos near the camera are drawn (called every frame from
     * GameScene.update). A halo is a Graphics object, re-tessellated on every
     * frame it is visible, and a stitched city has a few hundred lamps.
     */
    cullGlows() {
        if (!this.glows.length) return;
        const cam = this.scene.cameras.main, pad = this.scene.GRID_SIZE * 4;
        const hw = cam.width / 2 / cam.zoom + pad, hh = cam.height / 2 / cam.zoom + pad;
        const cx = cam.scrollX + cam.width / 2, cy = cam.scrollY + cam.height / 2;
        const now = this.scene.time.now;
        for (const g of this.glows) {
            g.setVisible(Math.abs(g.x - cx) < hw && Math.abs(g.y - cy) < hh);
            // a sprite's glow (Glows) is re-lit while it is in view: its pulse or flicker, and the
            // fade of its building while somebody stands behind it (a lamp's halo has no `rec`:
            // a post is not part of the building beside it, and stays lit)
            if (g.rec && g.visible) g.setAlpha(Glows.shown(g.strength, g.halo ? Glows.level(g.halo, now) : 1, g.rec.fade));
        }
    }

    clearGlows() {
        this.glows.forEach(g => g.destroy());
        this.glows = [];
    }
}

/**
 * The grade for a room in a period, or null for none. An interior is lit from
 * inside and ignores the hour, unless its light is lanterns: then night (and
 * only night) dims it warm and turns the halos on. An interior whose light is
 * the sky's ("daylight": a room that is all window) is graded as the street is.
 */
DayNight.gradeFor = (roomCfg, period) => {
    if (!(roomCfg && roomCfg.interior) || roomCfg.daylight) return DayNight.GRADES[period] || null;
    return roomCfg.lanternLight && period === 'night' ? DayNight.LANTERN_NIGHT : null;
};

/** Colour grades per period (MULTIPLY): day is untouched, night turns lights on. */
DayNight.GRADES = {
    dawn:  { color: 0xffd9c2, alpha: 0.85, lights: false },
    day:   null,
    dusk:  { color: 0xffbe94, alpha: 0.85, lights: false },
    night: { color: 0x7480c0, alpha: 1.0,  lights: true },
};

/** A lantern-lit interior at night: dimmer and warmer than the street outside. */
DayNight.LANTERN_NIGHT = { color: 0xa890a8, alpha: 1.0, lights: true };

if (typeof window !== 'undefined') window.DayNight = DayNight;
