/**
 * Occlusion - nobody is lost behind the scenery (issues #76 / #93).
 *
 * Standing art is Y-sorted, so a character north of a roof, a tower, a torii
 * top or a tree crown is drawn under it — and used to vanish there, with the
 * name label (depth 900) floating over the art on its own. One rule covers
 * every room:
 *
 *   a character counts as HIDDEN when art drawn over them (higher depth)
 *   covers most of their body with opaque pixels; the pieces doing the
 *   covering fade to ALPHA so the character shows through, and the
 *   character's name label fades to LABEL_ALPHA with them. Both come back
 *   when the character steps out.
 *
 * A building that is one sprite fades whole. So does a roof laid from tiles
 * (issue #172): a tile of it brings the rest of that roof with it (roof()).
 *
 * It is cheap: only the player and the NPCs on camera are tested, only when
 * one has moved, and only against the art of the 4-cell chunks they stand in
 * (RoomManager.artNear — the same buckets tile streaming uses) plus the
 * room's few wall signs. Coverage is read from a 1/4-size alpha mask per
 * texture, built the first time that texture is in the way, so the gap under
 * a torii or between a tower's legs does not count as cover.
 *
 * The fade lives on the tile RECORD (`rec.fade`), not the sprite: a streamed
 * sprite that is retired and re-made keeps it (RoomManager.spawnTile).
 */
class Occlusion {
    constructor(scene) {
        this.scene = scene;
        this.enabled = true;
        this.fading = new Set();        // records that are not at full strength
        this.dimmed = new Set();        // name labels that are not at full strength
        this.seen = new WeakMap();      // character -> what was found where they last stood
        this.masks = {};                // texture key -> { w, h, bits } | null
        this.source = null;             // the tileRecords array the above belongs to
    }

    /** Every frame, after the characters' depths are set. */
    update() {
        const scene = this.scene, rm = scene.roomManager;
        if (rm.tileRecords !== this.source) {
            // another room: its sprites are gone and its records with them
            this.source = rm.tileRecords;
            this.fading.clear();
        }
        const step = Math.min(1, scene.game.loop.delta / Occlusion.FADE_MS);
        const toward = (now, target, range) =>
            now < target ? Math.min(target, now + step * range) : Math.max(target, now - step * range);

        const cover = new Set();
        const driven = new Set();
        for (const [character, label] of this.characters()) {
            const hits = this.enabled ? this.look(character).hits : [];
            for (const rec of hits) cover.add(rec);
            if (label) {
                label.setAlpha(toward(label.alpha, hits.length ? Occlusion.LABEL_ALPHA : 1,
                    1 - Occlusion.LABEL_ALPHA));
                if (label.alpha < 1) driven.add(label);
            }
        }
        // a label whose character is no longer tested (an NPC that walked off
        // camera, or was left in another room) is not left part-faded
        for (const label of this.dimmed) if (!driven.has(label) && label.active !== false) label.setAlpha(1);
        this.dimmed = driven;
        for (const rec of cover) this.fading.add(rec);
        for (const rec of this.fading) {
            const now = rec.fade === undefined ? 1 : rec.fade;
            const next = toward(now, cover.has(rec) ? Occlusion.ALPHA : 1, 1 - Occlusion.ALPHA);
            if (next >= 1) {
                delete rec.fade;
                this.fading.delete(rec);
            } else {
                rec.fade = next;
            }
            if (rec.sprite) rec.sprite.setAlpha(next);
        }
    }

    /** [character, name label] for the player and every NPC on camera. */
    characters() {
        const scene = this.scene, rm = scene.roomManager, GS = scene.GRID_SIZE;
        const list = [];
        const player = scene.player;
        // on a train ride TrainTravel draws the player in the doorway itself
        if (player && player.sprite.visible && !(scene.trainTravel && scene.trainTravel.riding)) {
            list.push([player, scene.playerNameLabel]);
        }
        const view = scene.cameras.main.worldView;
        for (const npc of rm.rooms[rm.currentRoom].npcs) {
            const s = npc.sprite;
            if (!s.visible) continue;
            if (s.x < view.x - GS || s.x > view.right + GS || s.y < view.y - GS || s.y > view.bottom + GS) continue;
            list.push([npc, npc.nameLabel]);
        }
        return list;
    }

    /**
     * What hides a character where they stand: { hits: [record...] }, empty
     * unless most of the body is covered. Remembered until they move.
     */
    look(character) {
        const s = character.sprite;
        let found = this.seen.get(character);
        if (found && found.x === s.x && found.y === s.y && found.depth === s.depth &&
            found.source === this.source) return found;
        found = { x: s.x, y: s.y, depth: s.depth, source: this.source, hits: [] };
        this.seen.set(character, found);

        const rm = this.scene.roomManager;
        const xs = Occlusion.SAMPLE_X, ys = Occlusion.SAMPLE_Y;
        const left = s.x + xs[0], right = s.x + xs[xs.length - 1];
        const top = s.y + ys[0], bottom = s.y + ys[ys.length - 1];

        // art drawn over the character whose rectangle reaches the body
        const over = new Set();
        const consider = (rec) => {
            if (rec.depth <= s.depth) return;
            if (rec.left > right || rec.left + rec.width <= left ||
                rec.top > bottom || rec.top + rec.height <= top) return;
            over.add(rec);
        };
        rm.artNear(left, top, right, bottom).forEach(consider);
        rm.signArt.forEach(consider);
        if (!over.size) return found;

        const points = xs.length * ys.length;
        const covered = new Uint8Array(points);
        const counts = new Map();
        for (const rec of over) {
            let n = 0;
            for (let j = 0; j < ys.length; j++) {
                for (let i = 0; i < xs.length; i++) {
                    if (!this.opaque(rec, s.x + xs[i], s.y + ys[j])) continue;
                    covered[j * xs.length + i] = 1;
                    n++;
                }
            }
            if (n) counts.set(rec, n);
        }
        let total = 0;
        for (let i = 0; i < points; i++) total += covered[i];
        if (total / points <= Occlusion.HIDDEN) return found;
        // the pieces that matter fade; one that clips a corner stays solid.
        // A piece of a tile-laid roof brings the rest of that roof with it.
        const hits = new Set();
        for (const [rec, n] of counts) {
            if (n < 2) continue;
            const roof = this.roof(rec);
            if (roof) for (const part of roof) hits.add(part);
            else hits.add(rec);
        }
        found.hits = [...hits];
        return found;
    }

    /**
     * The whole roof a record is a tile of (issue #172), or null: every
     * roof-part record (Occlusion.ROOF_PARTS, on an overhead layer) that
     * touches it directly or through other parts — Market's hall, its gate
     * and each wing are one roof each, as a house roof is one sprite. Worked
     * out the first time one of its tiles hides somebody, by walking outward
     * through the chunk buckets (RoomManager.artNear), and kept on the
     * records, which last as long as the room does: no room scan, ever.
     */
    roof(rec) {
        if (rec.roof !== undefined) return rec.roof;
        if (!Occlusion.isRoofPart(rec)) return (rec.roof = null);
        const rm = this.scene.roomManager;
        const roof = rec.roof = [rec];
        for (let i = 0; i < roof.length; i++) {
            const a = roof[i];
            for (const b of rm.artNear(a.left - 1, a.top - 1, a.left + a.width, a.top + a.height)) {
                if (b.roof !== undefined || !Occlusion.isRoofPart(b) || !Occlusion.touching(a, b)) continue;
                b.roof = roof;
                roof.push(b);
            }
        }
        return roof;
    }

    /** Is a record one tile of a roof that is laid from several? */
    static isRoofPart(rec) {
        return !!rec.layer && rec.layer.z >= 7 && Occlusion.ROOF_PARTS.test(rec.key);
    }

    /** Do two records' rectangles overlap or share a length of edge (a corner alone is not enough)? */
    static touching(a, b) {
        const dx = Math.min(a.left + a.width, b.left + b.width) - Math.max(a.left, b.left);
        const dy = Math.min(a.top + a.height, b.top + b.height) - Math.max(a.top, b.top);
        return (dx > 0 && dy >= 0) || (dy > 0 && dx >= 0);
    }

    /** Is a record's art opaque at a world pixel? */
    opaque(rec, wx, wy) {
        if (wx < rec.left || wx >= rec.left + rec.width || wy < rec.top || wy >= rec.top + rec.height) return false;
        const mask = this.mask(rec.key);
        if (!mask) return false;
        const mx = Math.floor((wx - rec.left) / rec.width * mask.w);
        const my = Math.floor((wy - rec.top) / rec.height * mask.h);
        return mask.bits[my * mask.w + mx] === 1;
    }

    /** A texture's alpha at 1/4 size (the art's own pixel grid): { w, h, bits }. */
    mask(key) {
        if (key in this.masks) return this.masks[key];
        let mask = null;
        try {
            const image = this.scene.textures.get(key).getSourceImage();
            const w = Math.max(1, Math.round(image.width / 4)), h = Math.max(1, Math.round(image.height / 4));
            const canvas = document.createElement('canvas');
            canvas.width = w;
            canvas.height = h;
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(image, 0, 0, w, h);
            const data = ctx.getImageData(0, 0, w, h).data;
            const bits = new Uint8Array(w * h);
            for (let i = 0; i < bits.length; i++) bits[i] = data[i * 4 + 3] > 127 ? 1 : 0;
            mask = { w, h, bits };
        } catch (e) {
            mask = null;
        }
        return (this.masks[key] = mask);
    }
}

/** How see-through a piece of scenery goes while it hides someone, and their name label with it. */
Occlusion.ALPHA = 0.4;
/** The label matches how much of its character shows through the faded art (1 - ALPHA). */
Occlusion.LABEL_ALPHA = 0.6;
/** Milliseconds for a full fade out or back. */
Occlusion.FADE_MS = 160;
/** Hidden = more than this share of the body's sample points is covered. */
Occlusion.HIDDEN = 0.5;
/**
 * The sprite families roofs are LAID from, a tile at a time (the Market hall,
 * gate and wings; the Tokyo shrine hall with its hallways and end pagodas).
 * Their touching tiles fade as one roof. Roofs that are a single sprite
 * (house roofs, a lone shrine roof) already do, and tree crowns never group.
 */
Occlusion.ROOF_PARTS = /^(red-centre-roof|red-pagoda-roofs|red-small-pagoda-top|red-shrine-top-parts|temple-hallway|pagoda-roof|shrine-top)_\d+_\d+$/;
/** Body sample points, in pixels from the sprite's centre (a character fills one 64px cell). */
Occlusion.SAMPLE_X = [-14, 0, 14];
Occlusion.SAMPLE_Y = [-20, -6, 8, 22];

if (typeof window !== 'undefined') window.Occlusion = Occlusion;
