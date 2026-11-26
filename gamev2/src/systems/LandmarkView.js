/**
 * LandmarkView - the camera looks up at a landmark you stand in front of
 * (issues #176 / #90).
 *
 * The view is 15 cells tall and the camera trails the player by its follow
 * deadzone, so walking north leaves about five rows above them: the roof of
 * an eight-row shrine hall, or most of a tower, is off the top of the screen
 * from where you would stop to look at it.
 *
 * Only landmarks marked as data do this - config `game.lookUp.sprites`, a
 * short list of sprite families (shrine halls, pagodas, torii, the towers,
 * Tokyo Station...) - never every tall sprite: a high-rise, a tree or a
 * house changes nothing.
 *
 * In front of one (within `cells` cells south of its foot, fading out over
 * `fade` more, and over `side` cells either side of it) the world camera
 * gets a vertical follow offset and a narrower follow deadzone, so that its
 * top comes to sit just under the HUD bar - or as near as the view allows:
 * the player always keeps FOOT cells of view below them, so on a phone
 * (7.5 cells tall at 2x) or under a tower taller than the screen the camera
 * shows as much as fits and no more. What to do is a pure function of where
 * the player is (`LandmarkView.aim`), continuous in their position, and it
 * is eased in time on top (EASE_MS), so nothing jumps at the edge of a
 * landmark's reach; a room change settles it at once, under the fade.
 *
 * It is cheap: a room's landmarks are indexed once per room load
 * (`RoomManager.landmarks`, from the tile records) and there are a dozen at
 * most, so a frame costs a short loop. Chunk streaming follows by itself -
 * `RoomManager.streamRect` covers the point the camera is following.
 */
class LandmarkView {
    constructor(scene) {
        this.scene = scene;
        this.weight = 0;    // 0..1: how much of the follow deadzone's height is taken away
        this.offset = 0;    // world px the camera follows above the player
        this.fresh = true;  // settle without easing on the next update (boot, room change)
    }

    /** 'shrine-top_0_0' -> 'shrine-top': the family a tile key belongs to. */
    static family(key) {
        return key.replace(/_\d+_\d+$/, '');
    }

    /**
     * A room's landmarks, from its tile records: one {left, right, top, feet}
     * (world px) per record whose family is in `sprites` - {family: rows},
     * where rows is how many cells of the building stand below the marked
     * sprite (a shrine's roof sprite ends two rows above its steps, a torii's
     * beam two rows above its feet; 0 for a landmark that is one sprite).
     */
    static index(records, sprites, grid) {
        const out = [], rows = new Map();
        if (!sprites) return out;
        for (const rec of records) {
            let below = rows.get(rec.key);
            if (below === undefined) {
                const marked = sprites[LandmarkView.family(rec.key)];
                rows.set(rec.key, below = typeof marked === 'number' ? marked : -1);
            }
            if (below < 0) continue;
            out.push({ key: rec.key, left: rec.left, right: rec.left + rec.width, top: rec.top,
                       feet: rec.top + rec.height + below * grid });
        }
        return out;
    }

    /**
     * How much a landmark has hold of a player at (x, y), 0..1: all of it up
     * to `cells` cells south of its foot and anywhere across its width, less
     * over the next `fade` cells south and `side` cells to either side, and
     * nothing a cell behind its foot (walking round the back of it).
     */
    static reach(mark, o) {
        const south = (o.y - mark.feet) / o.grid;
        const down = south >= 0 ? (o.cells + o.fade - south) / o.fade : 1 + south;
        const across = 1 - Math.max(mark.left - o.x, o.x - mark.right, 0) / o.grid / o.side;
        return Math.max(0, Math.min(1, down, across));
    }

    /**
     * What the camera should do for a player at (o.x, o.y) among
     * o.landmarks: { weight, offset } - the share (0..1) of the follow
     * deadzone's height to take away, and how far above the player to follow
     * (world px). {0, 0} is the ordinary camera.
     *
     * o.viewH is the world view's height, o.bar how much of its top the HUD
     * bar covers, o.deadzone the full deadzone height (all world px at the
     * current zoom), o.foot the view to keep below the player's centre.
     *
     * With all of the weight the deadzone is gone and the camera sits at
     * exactly y - offset: the landmark's top LandmarkView.MARGIN cells under
     * the bar. With less, the offset is what still shows the top when the
     * camera trails by all the deadzone that is left; a landmark whose top
     * the ordinary camera always shows has no weight at all. The offset never
     * exceeds what keeps o.foot of view below the player.
     */
    static aim(o) {
        const half = o.viewH / 2, dz = o.deadzone;
        let weight = 0, offset = 0;
        for (const mark of o.landmarks) {
            const reach = LandmarkView.reach(mark, o);
            if (!reach) continue;
            // how far above the view its top can be today: the camera as far
            // south of the player as the deadzone lets it trail
            const need = o.y + dz / 2 - (mark.top - o.bar - LandmarkView.MARGIN * o.grid + half);
            if (need <= 0) continue;
            const k = reach * Math.min(1, need / Math.min(o.grid, dz / 2));
            weight = Math.max(weight, k);
            offset = Math.max(offset, k * Math.max(0, need - dz / 2));
        }
        const cap = Math.max(0, half - o.foot - dz * (1 - weight) / 2);
        return { weight, offset: Math.min(offset, cap) };
    }

    /** The answer for where the player is now. */
    want() {
        const scene = this.scene, cam = scene.cameras.main, p = scene.player.sprite;
        const marks = scene.roomManager.landmarks, look = scene.config.game.lookUp;
        if (!marks || !marks.length || !look || !cam.deadzone) return LandmarkView.NONE;
        const grid = scene.GRID_SIZE, ui = scene.uiScale;
        return LandmarkView.aim({
            x: p.x, y: p.y, landmarks: marks, grid,
            cells: look.cells, fade: look.fade, side: look.side,
            viewH: cam.height / cam.zoom,
            bar: scene.hudCover(),
            deadzone: ui.deadzoneHeight(),
            // the player's own cell and a free row under it, clear of touch controls over the canvas
            foot: LandmarkView.FOOT * grid + UIScale.insets().bottom / cam.zoom,
        });
    }

    /** A room change: start again from the ordinary camera, and settle on the next frame. */
    reset() {
        this.fresh = true;
    }

    /** Every frame (GameScene.update): ease towards what the player's place asks for. */
    update() {
        const scene = this.scene, cam = scene.cameras.main, ui = scene.uiScale;
        if (!scene.player || !ui || !cam.deadzone) return;
        const want = this.want();
        if (this.fresh) {
            // no easing across a room change (it is under the fade): be there
            this.fresh = false;
            this.weight = want.weight;
            this.offset = want.offset;
            this.apply();
            if (this.offset) cam.centerOn(scene.player.sprite.x, scene.player.sprite.y - this.offset);
            return;
        }
        if (this.weight === want.weight && this.offset === want.offset) return;
        const t = 1 - Math.exp(-scene.game.loop.delta / LandmarkView.EASE_MS);
        this.weight += (want.weight - this.weight) * t;
        this.offset += (want.offset - this.offset) * t;
        if (Math.abs(want.weight - this.weight) < 0.002) this.weight = want.weight;
        if (Math.abs(want.offset - this.offset) < 0.25) this.offset = want.offset;
        this.apply();
    }

    /** Hand the eased state to the camera. */
    apply() {
        this.scene.cameras.main.followOffset.y = this.offset;
        this.scene.uiScale.setDeadzoneShare(1 - this.weight);
    }
}

LandmarkView.NONE = { weight: 0, offset: 0 };
LandmarkView.MARGIN = 0.25;   // cells of sky between the HUD bar and a landmark's top
LandmarkView.FOOT = 2;        // cells of view kept below the player's centre
LandmarkView.EASE_MS = 140;   // time constant of the ease
