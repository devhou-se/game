/**
 * AmbientTrains - trains that periodically pass through on the tracks (issue #29).
 *
 * Any room whose Tiled map contains train-track tiles gets an ambient train:
 * every so often one enters off-screen, runs the full track, and leaves the
 * far side. Station rooms are excluded — their track hosts the parked
 * TrainTravel train, and a passer-by would drive straight through it.
 *
 * Same conventions as the parked train: livery from config `stations`,
 * origin (0,0), bottom edge sitting on the track bed, depth 48 (lower when the
 * track row is above row 4, so a player on a level crossing stays on top).
 *
 * A track normally runs off both edges of its room and the train comes in
 * from, and leaves to, off-screen. In a stitched city (issues #40/#41) the
 * Palace track ends inside the map, in the woods south of Tokyo: at an end
 * like that the train fades in / out standing on the last of the track.
 */
class AmbientTrains {
    constructor(scene) {
        this.scene = scene;
        this.active = null;
        this.tween = null;
        this.timer = null;
        this.onRoomChange(scene.roomManager.currentRoom);
    }

    /**
     * The topmost track in the room: { row, x0, x1 (cells), lift }, or null
     * (no tracks / is a station). `lift` is how many rows the track's district
     * sits below the room's top — 0 except in a stitched city — so the fixed
     * depth 48 can follow the district down the map.
     */
    track(roomKey) {
        if ((this.scene.config.stations || {})[roomKey]) return null;
        const rm = this.scene.roomManager;
        let t = null;
        for (const layer of (rm.rooms[roomKey].layers || [])) {
            for (const xy in (layer.tiles || {})) {
                if (!/^train-track/.test(layer.tiles[xy])) continue;
                const [x, y] = xy.split(',').map(Number);
                if (!t || y < t.row) t = { row: y, x0: x, x1: x, lift: 0 };
                else if (y === t.row) { t.x0 = Math.min(t.x0, x); t.x1 = Math.max(t.x1, x); }
                else continue;
                const district = rm.districtsAt(x, y, roomKey)[0];
                if (district) t.lift = y - district.y;
            }
        }
        return t;
    }

    /** Topmost track-tile row in the room, or null (no tracks / is a station). */
    trackRow(roomKey) {
        const t = this.track(roomKey);
        return t ? t.row : null;
    }

    onRoomChange(roomKey) {
        this.clear();
        this.span = this.track(roomKey);
        this.row = this.span ? this.span.row : null;
        // first pass comes fairly quickly so the room feels alive on arrival
        if (this.row !== null) this.schedule(3000 + Math.random() * 7000);
    }

    schedule(delay) {
        this.timer = this.scene.time.delayedCall(delay, () => this.cross());
    }

    /** One train, off-screen edge to off-screen edge along the track row. */
    cross() {
        const scene = this.scene;
        if (this.row === null) return;   // no track here (or a station room)
        const room = scene.roomManager.rooms[scene.roomManager.currentRoom];
        const GS = scene.GRID_SIZE;

        const liveries = [...new Set(Object.values(scene.config.stations || {}).map(s => s.train))];
        const key = liveries.length ? liveries[Math.floor(Math.random() * liveries.length)] : 'train-green';
        if (!scene.textures.exists(key)) return;

        const tex = scene.textures.get(key).getSourceImage();
        const ww = room.worldWidth || scene.WORLD_WIDTH;
        const dir = Math.random() < 0.5 ? 1 : -1;
        // an end of the track at the room's edge is "open": the train runs
        // off-screen there. A "closed" end stops inside the room, so the
        // train stays on the track and fades instead.
        const left = this.span.x0 * GS, right = (this.span.x1 + 1) * GS;
        const openLeft = left <= 0, openRight = right >= ww;
        const westX = openLeft ? -tex.width : left;
        const eastX = openRight ? ww : right - tex.width;
        const fromX = dir > 0 ? westX : eastX;
        const toX = dir > 0 ? eastX : westX;
        const fade = tex.width / 2;

        this.active = scene.add.image(fromX, (this.row + 1) * GS - tex.height, key);
        this.active.setOrigin(0, 0);
        // over the tracks, under nearby standing objects - and under a player standing on the
        // track row (a level crossing), whose depth is (row + 1) * 10 + 5. 48 everywhere the
        // track is on row 4 or lower; Palace's is row 3 (issue #63), so 44 there. Rows are the
        // district's own (`lift` moves the result down with the district in a stitched city).
        const localRow = this.row - this.span.lift;
        this.active.setDepth(scene.roomManager.yDepth(Math.min(48, (localRow + 1) * 10 + 4) + this.span.lift * 10));
        const setAlpha = () => {
            if (!this.active) return;
            const a = Math.min(openLeft ? 1 : (this.active.x - westX) / fade,
                               openRight ? 1 : (eastX - this.active.x) / fade);
            this.active.setAlpha(Math.max(0, Math.min(1, a)));
        };
        setAlpha();

        this.tween = scene.tweens.add({
            targets: this.active, x: toX,
            duration: Math.abs(toX - fromX) / 0.7,   // ~0.7 px/ms — an express clip
            ease: 'Linear',
            onUpdate: setAlpha,
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
