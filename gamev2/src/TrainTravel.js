/**
 * TrainTravel — the trains themselves.
 *
 * Every station room (config `stations`) has a train parked at its platform.
 * go(from, to) plays the ride: the player boards (disappears), the train
 * pulls out, then a riding cutscene — the car rumbling along with the player
 * visible in a window and motion streaks flying past — then the destination
 * station is revealed as its train pulls in and the player steps off.
 * Input is locked for the duration (InputHandler checks `riding`).
 */
class TrainTravel {
    constructor(scene) {
        this.scene = scene;
        this.riding = false;
        this.sprite = null;   // one train image, re-dressed per ride
        this.livery = null;   // rolled when entering a station, persists until
                              // the player leaves the station system — so the
                              // train you board is the train you arrive in
    }

    stationOf(roomKey) {
        return (this.scene.config.stations || {})[roomKey] || null;
    }

    parkedX(st) { return st.trainCell[0] * this.scene.GRID_SIZE; }

    /** +1 when the destination town lies east of the departure town, else -1
     *  (world geometry from the map metadata) — trains move the way they're
     *  actually going. */
    dirTo(fromSt, toSt) {
        const meta = this.scene.cache.json.get('worldMap');
        const cx = (town) => {
            const r = meta && meta.rooms && meta.rooms[town];
            return r ? r.x + r.w / 2 : 0;
        };
        return cx(toSt.town) >= cx(fromSt.town) ? 1 : -1;
    }
    parkedY(st) {
        // feet on the platform-edge row: bottom of the sprite sits at trainCell[1]*GS
        const tex = this.scene.textures.get(this.livery).getSourceImage();
        return st.trainCell[1] * this.scene.GRID_SIZE - tex.height;
    }

    /** Park (or hide) the train for the room we just switched into. */
    onRoomChange(roomKey) {
        const st = this.stationOf(roomKey);
        if (!st) {
            this.livery = null;   // left the station system
            if (this.sprite) this.sprite.setVisible(false);
            return;
        }
        if (!this.livery) {
            const all = [...new Set(Object.values(this.scene.config.stations).map(s => s.train))];
            this.livery = all[Math.floor(Math.random() * all.length)];
        }
        if (!this.sprite) {
            this.sprite = this.scene.add.image(0, 0, this.livery);
            this.sprite.setOrigin(0, 0);
        }
        this.sprite.setTexture(this.livery);
        this.sprite.setPosition(this.parkedX(st), this.parkedY(st));
        this.sprite.setDepth(48);   // over the tracks, under the platform players
        this.sprite.setVisible(true);
    }

    /** Interior art that matches the livery you're riding. */
    interiorKeyFor(trainKey) {
        return trainKey === 'train-green' ? 'train-interior-wood' : 'train-interior-metro';
    }

    /** The riding cutscene: the inside of the car (GuttyKreum Train Interiors),
     *  the player riding in the aisle, scenery streaking past the windows. */
    buildCutscene(trainKey, dir) {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const c = scene.add.container(0, 0);
        c.setDepth(3000);
        c.setScrollFactor(0);

        // dark surround behind/around the car
        c.add(scene.add.rectangle(0, 0, W, H, 0x05060a).setOrigin(0, 0));

        // the car interior, matched to the livery, at 2x. That keeps it in
        // proportion with the world: the exterior train's doors render ~108px
        // tall, and the interior's doors at 2x are ~112px — so the character
        // (unchanged size) reads as person-height inside the car instead of
        // ankle-height under 4x furniture. The car is wider than the screen,
        // so we frame the middle of it against the dark surround.
        const interior = scene.add.image(W / 2, H / 2, this.interiorKeyFor(trainKey)).setOrigin(0.5, 0.5);
        interior.setScale(2);
        c.add(interior);
        const carTop = H / 2 - interior.displayHeight / 2, carH = interior.displayHeight;

        this._cutTweens = [];
        // scenery whipping past the windows (the top band of the car)
        const bandTop = carTop + carH * 0.03, bandH = carH * 0.10;
        for (let i = 0; i < 6; i++) {
            const y = bandTop + (i / 5) * bandH;
            const streak = scene.add.rectangle(0, y, 120, 3, 0xcfe4ff, 0.45).setOrigin(0, 0.5);
            streak.setX(dir > 0 ? -140 : W + 140);
            c.add(streak);
            this._cutTweens.push(scene.tweens.add({
                targets: streak, x: dir > 0 ? W + 140 : -140,
                duration: 260 + (i % 3) * 110, repeat: -1, delay: i * 70,
                onRepeat: () => streak.setX(dir > 0 ? -140 : W + 140),
            }));
        }

        // the player, riding seated: raised so his lower body lines up with
        // the car's bench seats instead of standing in the aisle. Pinned to
        // the front-facing STANDING frame (frame 0 of the 'down' sprite) —
        // the live sprite's texture could be any mid-walk frame.
        const downKey = scene.getDirectionalSpriteKey(scene.player.baseSpriteKey, 'down')
            || scene.player.baseSpriteKey;
        const standKey = scene.textures.exists(`${downKey}_frame_0`)
            ? `${downKey}_frame_0` : downKey;
        const rider = scene.add.image(W / 2, carTop + carH * 0.52, standKey)
            .setOrigin(0.5, 1).setScale(1.5);
        // legs cropped away below the bench line — reads as sitting on the seat
        rider.setCrop(0, 0, rider.frame.width, rider.frame.height * 0.72);
        c.add(rider);

        // gentle rumble of the whole car
        this._cutTweens.push(scene.tweens.add({
            targets: [interior, rider], y: '+=3', duration: 130, yoyo: true, repeat: -1,
        }));

        c.setAlpha(0);
        scene.tweens.add({ targets: c, alpha: 1, duration: 220 });
        return c;
    }

    destroyCutscene(c) {
        (this._cutTweens || []).forEach(t => t.stop());
        this._cutTweens = [];
        c.destroy(true);
    }

    /** The player steps off the train once it has stopped: appear on the train's
     *  bottom row — in the same doorway he boarded from (enterX) — facing down so
     *  we see his face, then take a single step down onto the platform, as if
     *  stepping off. Rendered above the train (depth) so he's visible standing in
     *  the door; the depth sort is suspended while `riding` so it doesn't sink him
     *  behind the train. A plain tween (not grid movement) so the boarding trigger
     *  can't re-fire; the looping walk animation reads as walking. */
    stepOff(to, enterX) {
        const scene = this.scene, player = scene.player, GS = scene.GRID_SIZE;
        const onTrainY = to.trainCell[1] - 1;   // the train's bottom row (the doorway)
        const platformY = to.trainCell[1];      // one step down, onto the platform
        player.gridX = enterX; player.gridY = onTrainY;
        player.sprite.setPosition(enterX * GS + GS / 2, onTrainY * GS + GS / 2);
        player.sprite.setDepth(60);            // over the train (depth 48) — in the door
        player.updateDirectionSprite(0, 1);    // face down before he's revealed
        player.playWalkAnim();                 // the step-off reads as walking
        player.sprite.setVisible(true);
        if (player.nameLabel) player.nameLabel.setVisible(true);
        scene.tweens.add({
            targets: player.sprite,
            y: platformY * GS + GS / 2,
            duration: scene.MOVE_DURATION,
            ease: 'Linear',
            onComplete: () => {
                player.gridX = enterX; player.gridY = platformY;
                player.setIdleFrame();
                this.riding = false;   // depth sort resumes now he's off the train
                scene.roomManager.isTransitioning = false;
            },
        });
    }

    /** The ride. */
    go(fromKey, toKey) {
        if (this.riding) return;
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const from = this.stationOf(fromKey), to = this.stationOf(toKey);
        if (!from || !to) return;
        this.riding = true;
        scene.roomManager.isTransitioning = true;

        const player = scene.player;
        const setPlayerVisible = (v) => {
            player.sprite.setVisible(v);
            if (player.nameLabel) player.nameLabel.setVisible(v);
        };

        // the door the player boarded from — he steps back out of the same one
        const enterX = player.getGridPosition().x;
        // face down now (while hidden), so he faces the camera both in the ride
        // cutscene window and when he steps off — not moon-walking on his back
        player.updateDirectionSprite(0, 1);

        // board: the player steps out of sight, the train pulls away toward the
        // destination (east -> right, west -> left)
        const dir = this.dirTo(from, to);
        const offset = dir * (W + this.sprite.width);
        setPlayerVisible(false);

        // A full-screen black curtain we fade by hand. The camera's own fade is
        // NOT used for the ride, so the room can be swapped invisibly underneath
        // and the train never flashes onto either platform. Sits just below the
        // cutscene (depth 3000).
        const curtain = scene.add.rectangle(0, 0, W, H, 0x000000)
            .setOrigin(0, 0).setScrollFactor(0).setDepth(2999).setAlpha(0);

        // PHASE 1 — depart: the train pulls out of the platform...
        scene.tweens.add({
            targets: this.sprite, x: this.sprite.x + offset,
            duration: 1100, ease: 'Cubic.easeIn',
        });
        // ...and the screen fades to black over the tail of that pull-out, so
        // there's no empty-platform beat and no hard cut into the cutscene.
        scene.tweens.add({
            targets: curtain, alpha: 1, duration: 550, delay: 550,
            onComplete: () => {
                // Swap to the destination room under the black curtain (its own
                // camera fade is skipped). onRoomChange parks the dest train at
                // the platform; move it off-screen immediately so it's not in
                // frame when the curtain lifts — it arrives by pulling in.
                scene.roomManager.switchRoomInstant(toKey, enterX, to.trainCell[1]);
                setPlayerVisible(false);              // stay aboard until we arrive
                this.sprite.setX(this.parkedX(to) - offset);   // waiting off-screen
                this.sprite.setVisible(true);

                // PHASE 2 — the riding cutscene, fading up over the black curtain.
                const cut = this.buildCutscene(this.livery, dir);

                scene.time.delayedCall(1800, () => {
                    // PHASE 3 — fade the cutscene back to black (curtain still
                    // solid behind it).
                    scene.tweens.add({
                        targets: cut, alpha: 0, duration: 350,
                        onComplete: () => {
                            this.destroyCutscene(cut);
                            // PHASE 4 — lift the curtain onto the dest interior
                            // (the train is still off-screen, not yet in frame).
                            scene.tweens.add({
                                targets: curtain, alpha: 0, duration: 300,
                                onComplete: () => {
                                    curtain.destroy();
                                    // PHASE 5 — the train pulls in, still moving
                                    // the same way, and stops at the platform.
                                    scene.tweens.add({
                                        targets: this.sprite, x: this.parkedX(to),
                                        duration: 1100, ease: 'Cubic.easeOut',
                                        // PHASE 6 — the player steps off the train.
                                        onComplete: () => this.stepOff(to, enterX),
                                    });
                                },
                            });
                        },
                    });
                });
            },
        });
    }
}
