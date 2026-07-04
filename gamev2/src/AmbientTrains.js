/**
 * AmbientTrains - trains that periodically pass through on the tracks (issue #29).
 *
 * Any room whose Tiled map contains train-track tiles gets an ambient train:
 * every so often one enters off-screen, runs the full track, and leaves the
 * far side. Station rooms are excluded — their track hosts the parked
 * TrainTravel train, and a passer-by would drive straight through it.
 *
 * Same conventions as the parked train: livery from config `stations`,
 * origin (0,0), bottom edge sitting on the track bed, depth 48.
 */
class AmbientTrains {
    constructor(scene) {
        this.scene = scene;
        this.active = null;
        this.tween = null;
        this.timer = null;
        this.onRoomChange(scene.roomManager.currentRoom);
    }

    /** Topmost track-tile row in the room, or null (no tracks / is a station). */
    trackRow(roomKey) {
        if ((this.scene.config.stations || {})[roomKey]) return null;
        let row = null;
        for (const layer of (this.scene.roomManager.rooms[roomKey].layers || [])) {
            for (const xy in (layer.tiles || {})) {
                if (!/^train-track/.test(layer.tiles[xy])) continue;
                const y = Number(xy.split(',')[1]);
                if (row === null || y < row) row = y;
            }
        }
        return row;
    }

    onRoomChange(roomKey) {
        this.clear();
        this.row = this.trackRow(roomKey);
        // first pass comes fairly quickly so the room feels alive on arrival
        if (this.row !== null) this.schedule(3000 + Math.random() * 7000);
    }

    schedule(delay) {
        this.timer = this.scene.time.delayedCall(delay, () => this.cross());
    }

    /** One train, off-screen edge to off-screen edge along the track row. */
    cross() {
        const scene = this.scene;
        const room = scene.roomManager.rooms[scene.roomManager.currentRoom];
        const GS = scene.GRID_SIZE;

        const liveries = [...new Set(Object.values(scene.config.stations || {}).map(s => s.train))];
        const key = liveries.length ? liveries[Math.floor(Math.random() * liveries.length)] : 'train-green';
        if (!scene.textures.exists(key)) return;

        const tex = scene.textures.get(key).getSourceImage();
        const ww = room.worldWidth || scene.WORLD_WIDTH;
        const dir = Math.random() < 0.5 ? 1 : -1;
        const fromX = dir > 0 ? -tex.width : ww;
        const toX = dir > 0 ? ww : -tex.width;

        this.active = scene.add.image(fromX, (this.row + 1) * GS - tex.height, key);
        this.active.setOrigin(0, 0);
        this.active.setDepth(48);   // over the tracks, under nearby standing objects

        this.tween = scene.tweens.add({
            targets: this.active, x: toX,
            duration: Math.abs(toX - fromX) / 0.7,   // ~0.7 px/ms — an express clip
            ease: 'Linear',
            onComplete: () => {
                if (this.active) this.active.destroy();
                this.active = null;
                this.tween = null;
                this.schedule(15000 + Math.random() * 25000);
            },
        });
    }

    clear() {
        if (this.timer) { this.timer.remove(); this.timer = null; }
        if (this.tween) { this.tween.stop(); this.tween = null; }
        if (this.active) { this.active.destroy(); this.active = null; }
    }
}

if (typeof window !== 'undefined') window.AmbientTrains = AmbientTrains;
