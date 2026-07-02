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

    /** The riding cutscene: dark world rushing past, player in a window. */
    buildCutscene(trainKey, dir) {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const c = scene.add.container(0, 0);
        c.setDepth(3000);
        c.setScrollFactor(0);

        const bg = scene.add.rectangle(0, 0, W, H, 0x0a0a12).setOrigin(0, 0);
        c.add(bg);

        this._cutTweens = [];
        for (let i = 0; i < 7; i++) {
            const y = H * 0.18 + (i * 97) % Math.round(H * 0.64);
            const streak = scene.add.rectangle(W + (i * 233) % 900, y, 130, 4, 0x445566).setOrigin(0, 0.5);
            if (dir < 0) streak.setX(-((i * 233) % 900) - 130);
            c.add(streak);
            this._cutTweens.push(scene.tweens.add({
                targets: streak, x: dir > 0 ? -160 : W + 160,
                duration: 420 + (i % 3) * 140, repeat: -1,
                onRepeat: () => streak.setX(dir > 0 ? W + 60 : -190),
            }));
        }

        const train = scene.add.image(W / 2, H / 2, trainKey).setScale(1.7);
        c.add(train);

        // the player, seated at a window (upper body only). The window band
        // sits a little below the sprite's vertical centre.
        const rider = scene.add.image(W / 2 + 30, H / 2 + train.displayHeight * 0.15, scene.player.sprite.texture.key);
        rider.setScale(1.7);
        rider.setOrigin(0.5, 0.5);
        rider.setCrop(14, 8, 36, 26);   // head + shoulders in the window
        c.add(rider);

        this._cutTweens.push(scene.tweens.add({
            targets: [train, rider], y: '+=3', duration: 130, yoyo: true, repeat: -1,
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

    /** The ride. */
    go(fromKey, toKey) {
        if (this.riding) return;
        const scene = this.scene;
        const from = this.stationOf(fromKey), to = this.stationOf(toKey);
        if (!from || !to) return;
        this.riding = true;
        scene.roomManager.isTransitioning = true;

        const player = scene.player;
        const setPlayerVisible = (v) => {
            player.sprite.setVisible(v);
            if (player.nameLabel) player.nameLabel.setVisible(v);
        };

        // board: the player steps out of sight, the train pulls away toward
        // the destination (east -> right, west -> left)
        const dir = this.dirTo(from, to);
        setPlayerVisible(false);
        scene.tweens.add({
            targets: this.sprite,
            x: this.sprite.x + dir * (scene.cameras.main.width + this.sprite.width),
            duration: 1100, ease: 'Cubic.easeIn',
            onComplete: () => {
                // riding cutscene covers the screen while the rooms switch behind it
                const cut = this.buildCutscene(this.livery, dir);
                scene.roomManager.switchRoom(toKey, to.arrive[0], to.arrive[1]);
                setPlayerVisible(false);   // stay aboard until the train stops
                scene.time.delayedCall(1600, () => {
                    scene.tweens.add({
                        targets: cut, alpha: 0, duration: 350,
                        onComplete: () => {
                            this.destroyCutscene(cut);
                            // arrival: the destination's train pulls in
                            // still moving the same way: entering from behind
                            const parked = this.parkedX(to);
                            this.sprite.setX(parked - dir * (scene.cameras.main.width + this.sprite.width));
                            scene.tweens.add({
                                targets: this.sprite, x: parked,
                                duration: 1100, ease: 'Cubic.easeOut',
                                onComplete: () => {
                                    setPlayerVisible(true);   // step off
                                    this.riding = false;
                                    scene.roomManager.isTransitioning = false;
                                },
                            });
                        },
                    });
                });
            },
        });
    }
}
