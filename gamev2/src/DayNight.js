/**
 * DayNight - real-time day/night cycle (issue #2).
 *
 * Time of day follows the real clock in Tokyo (JST, UTC+9) with four periods:
 * Dawn 5-7, Day 7-19, Dusk 19-21, Night 21-5. Day renders untouched; dawn and
 * dusk get a warm colour grade; night gets a dark blue grade plus warm glow
 * halos on every lamp post / lantern already placed in the room's Tiled map.
 *
 * The grade is a camera-fixed MULTIPLY rectangle at depth 950 — above the
 * whole world and its labels (<= 900), below the HUD (1000) and the train-ride
 * cutscene (~3000). Glows sit just above the grade so they cut through the
 * darkness. Interior rooms ("interior": true in config) are never graded.
 *
 * ?tod=dawn|day|dusk|night pins the period for testing.
 */
class DayNight {
    constructor(scene) {
        this.scene = scene;
        this.glows = [];

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
        const grade = roomCfg.interior ? null : DayNight.GRADES[this.period()];

        if (!grade) {
            this.grade.setVisible(false);
        } else {
            this.grade.setFillStyle(grade.color, grade.alpha);
            this.grade.setVisible(true);
        }

        this.clearGlows();
        if (grade && grade.lights) this.buildGlows(roomKey);
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
        for (const layer of (this.scene.roomManager.rooms[roomKey].layers || [])) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (/lamp-post|-lanterns/.test(key)) cells.add(xy);
            }
        }
        for (const xy of cells) {
            const [gx, gy] = xy.split(',').map(Number);
            if (cells.has(`${gx},${gy - 1}`)) continue;   // lower half of a stack

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
    }

    clearGlows() {
        this.glows.forEach(g => g.destroy());
        this.glows = [];
    }
}

/** Colour grades per period (MULTIPLY): day is untouched, night turns lights on. */
DayNight.GRADES = {
    dawn:  { color: 0xffd9c2, alpha: 0.85, lights: false },
    day:   null,
    dusk:  { color: 0xffbe94, alpha: 0.85, lights: false },
    night: { color: 0x7480c0, alpha: 1.0,  lights: true },
};

if (typeof window !== 'undefined') window.DayNight = DayNight;
