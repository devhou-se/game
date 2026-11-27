/**
 * Seating - how the player looks on furniture (issue #227).
 *
 * Which furniture, and the pose on each piece, is the table in
 * src/utils/Seats.js; getting on it is the seat step in CollisionSystem.
 * This is only the picture, redone every frame after the characters' depths
 * are set, with no new art:
 *
 *   lift    the sprite is drawn `pose.dy` pixels off its cell (Character.
 *           setLift), sliding from the old cell's lift to the new one's
 *           during a step;
 *   facing  at rest, the player is turned the way the furniture faces;
 *   sort    on solid furniture the player sorts at ITS foot row, so they are
 *           drawn in front of the bed they lie in rather than under it;
 *   cover   `pose.cover` - a bed's blanket, the back of a chair seen from
 *           behind - is that piece of the furniture's own sprite, drawn
 *           again one depth step above the player.
 *
 * During a step both the seat being entered and the seat being left count,
 * so the player slides under a blanket rather than popping through it. A
 * line the furniture has to say (Interactions' `flavour`: the bunk, the
 * bath) is said when the player settles on it, since walking into it no
 * longer bumps.
 */
class Seating {
    constructor(scene) {
        this.scene = scene;
        this.covers = [];       // up to two images (seat entered, seat left), made on first use
        this.on = null;         // the furniture the player last settled on, so its line is said once
    }

    /** Every frame, after the characters' depths are set and before Occlusion looks. */
    update() {
        const scene = this.scene, player = scene.player, rm = scene.roomManager;
        if (!player) return;
        // TrainTravel owns the player's sprite while riding
        if (scene.trainTravel && scene.trainTravel.riding) {
            player.setLift(0);
            return this.showCovers([]);
        }
        const GS = scene.GRID_SIZE, sprite = player.sprite;
        const from = player.isMoving ? { x: player.startGridX, y: player.startGridY } : { x: player.gridX, y: player.gridY };
        const to = player.getTargetPosition();
        const a = rm.seatAt(from.x, from.y), b = rm.seatAt(to.x, to.y);
        const t = Math.max(Math.abs(sprite.x - (from.x + 0.5) * GS), Math.abs(sprite.y - (from.y + 0.5) * GS)) / GS;
        player.setLift(Seats.dyAt(a, b, t));

        if (!player.isMoving) this.settle(b, to.x, to.y);

        const solid = [b, a].filter((c, i, both) => c && c.solid && both.indexOf(c) === i);
        if (!solid.length) return this.showCovers([]);
        const row = Seats.footRow(solid, (sprite.y + GS / 2) / GS);
        sprite.setDepth(rm.yDepth(row * 10 + 5));
        this.showCovers(solid.filter(c => c.pose.cover), rm.yDepth(row * 10 + 6));
    }

    /** At rest: face the way the seat does, and say its line the first time. */
    settle(seat, gridX, gridY) {
        const scene = this.scene, player = scene.player;
        if (!seat) { this.on = null; return; }
        const face = Seating.FACE[seat.pose.face];
        if (face && (player.facingX !== face[0] || player.facingY !== face[1])) {
            player.facingX = face[0];
            player.facingY = face[1];
            player.updateDirectionSprite(face[0], face[1]);
            player.setIdleFrame();
        }
        const furniture = `${seat.key}@${seat.x},${seat.y}`;
        if (this.on === furniture) return;
        this.on = furniture;
        // its line, as a bump on furniture says one (GameScene.checkNPCInteraction), under the same guards
        if (scene.shop && !scene.dialogueManager.isVisible() && !scene.shop.isVisible() &&
            !(scene.datePicker && scene.datePicker.isVisible())) {
            const flavour = scene.roomManager.interactionAt(gridX, gridY, 'flavour');
            if (flavour && flavour.say && scene.shop.toastText() !== flavour.say) scene.shop.toast(flavour.say);
        }
    }

    /** Draw the cover of each of these seat cells at `depth`, and hide the images not needed. */
    showCovers(cells, depth) {
        const GS = this.scene.GRID_SIZE;
        cells.forEach((cell, i) => {
            let image = this.covers[i];
            if (!image) image = this.covers[i] = this.scene.add.image(0, 0, cell.key).setOrigin(0, 0);
            const cut = cell.key + ':' + cell.pose.cover.join(',');
            if (image.seatCut !== cut) {
                image.seatCut = cut;
                image.setTexture(cell.key);
                image.setCrop(...cell.pose.cover);      // after setTexture: the crop is the frame's
            }
            image.setPosition(cell.x * GS, cell.y * GS);
            image.setDepth(depth);
            image.setVisible(true);
        });
        for (let i = cells.length; i < this.covers.length; i++) this.covers[i].setVisible(false);
    }

    /** Another room: nothing of the last one's furniture is on the player. */
    onRoomChange() {
        this.showCovers([]);
        this.on = null;
        if (this.scene.player) this.scene.player.setLift(0);
    }
}

/** A pose's `face` as the player's facing, [x, y]. */
Seating.FACE = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };

if (typeof window !== 'undefined') window.Seating = Seating;
