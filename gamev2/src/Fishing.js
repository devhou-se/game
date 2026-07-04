/**
 * Fishing — the pond mini game.
 *
 * Buy the fishing rod at any konbini counter, then bump into any pond edge
 * to cast: the bobber plops in, ripples... and when the "!" flashes you have
 * a beat to press SPACE. Catches pay out on the spot — boots pay nothing.
 * ESC (or a miss) ends the session; bump the pond again to recast.
 *
 * No new art: the bobber and ripples are drawn Graphics, the "!" is text.
 */
class Fishing {
    constructor(scene) {
        this.scene = scene;
        this.state = 'idle';       // idle | waiting | strike | landing
        this.objs = [];
        this.timer = null;
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ space: K.SPACE, esc: K.ESC });
    }

    isActive() { return this.state !== 'idle'; }

    /**
     * The player bumped a blocked cell — if it's pond water, start fishing
     * (rod required; the konbini counter sells one).
     */
    checkStart(gridX, gridY) {
        if (this.isActive()) return;
        const room = this.scene.roomManager.rooms[this.scene.roomManager.currentRoom];
        const xy = `${gridX},${gridY}`;
        const isPond = (room.layers || []).some(l => /^pond-autotile/.test((l.tiles || {})[xy] || ''));
        if (!isPond) return;

        if (!this.scene.shop.items['fishing-rod']) {
            this.scene.shop.toast('you need a fishing rod — the konbini sells them');
            return;
        }

        // swallow the keys that got us here
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.space); JD(this.keys.esc);

        this.state = 'waiting';
        const GS = this.scene.GRID_SIZE;
        const bx = gridX * GS + GS / 2, by = gridY * GS + GS / 2;

        // the bobber: a red-capped float, plus a looping ripple ring
        const bob = this.scene.add.graphics();
        bob.fillStyle(0xdd3333, 1); bob.fillCircle(0, -3, 5);
        bob.fillStyle(0xffffff, 1); bob.fillCircle(0, 3, 5);
        bob.lineStyle(1, 0x222222, 1); bob.strokeCircle(0, 0, 6);
        bob.setPosition(bx, by); bob.setDepth(900);
        this.bobber = bob; this.objs.push(bob);

        const ripple = this.scene.add.graphics();
        ripple.lineStyle(2, 0xcfe4ff, 0.7); ripple.strokeCircle(0, 0, 8);
        ripple.setPosition(bx, by); ripple.setDepth(899);
        this.objs.push(ripple);
        this.rippleTween = this.scene.tweens.add({
            targets: ripple, scale: 2.2, alpha: 0, duration: 1100, repeat: -1,
        });

        this.scene.shop.toast('...');
        this.timer = this.scene.time.delayedCall(1200 + Math.random() * 3300, () => this.bite());
    }

    /** Something's on the line — a short window to strike. */
    bite() {
        if (this.state !== 'waiting') return;
        this.state = 'strike';
        const p = this.scene.player.sprite;
        this.alert = this.scene.add.text(p.x, p.y - 56, '!', {
            fontSize: '32px', fill: '#ffd700', fontFamily: 'PressStart2P',
        });
        this.alert.setOrigin(0.5, 1); this.alert.setResolution(1); this.alert.setDepth(901);
        this.objs.push(this.alert);
        this.scene.tweens.add({ targets: this.bobber, y: '+=5', duration: 90, yoyo: true, repeat: 3 });
        this.timer = this.scene.time.delayedCall(700, () => this.finish(false, 'too slow — it got away...'));
    }

    /** SPACE during the strike window lands whatever bit. */
    strike() {
        if (this.state === 'waiting') return this.finish(false, 'nothing on the line yet — it swam off');
        if (this.state !== 'strike') return;
        const roll = Math.random();
        let acc = 0;
        const c = Fishing.CATCHES.find(f => (acc += f.odds) > roll) || Fishing.CATCHES[0];
        if (c.value > 0) {
            this.scene.shop.money += c.value;
            this.scene.shop.save();
            this.scene.updateHUD();
        }
        this.finish(true, c.value > 0 ? `${c.name}! the fishmonger pays ${this.scene.shop.fmt(c.value)}`
                                      : `${c.name}... worthless.`);
    }

    finish(caught, message) {
        this.scene.shop.toast(message);
        if (caught && this.bobber) {
            // the catch pops out of the water
            this.scene.tweens.add({ targets: this.bobber, y: '-=26', alpha: 0, duration: 260 });
        }
        this.clear(!caught);
    }

    clear(instant) {
        if (this.timer) { this.timer.remove(); this.timer = null; }
        if (this.rippleTween) { this.rippleTween.stop(); this.rippleTween = null; }
        const objs = this.objs;
        this.objs = [];
        if (instant) objs.forEach(o => o.destroy());
        else this.scene.time.delayedCall(300, () => objs.forEach(o => o.destroy()));
        this.bobber = null;
        this.alert = null;
        this.state = 'idle';
    }

    /** Owns input while a line is in the water. */
    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) { this.scene.shop.toast('reeled in'); return this.clear(true); }
        if (JD(k.space)) return this.strike();
    }
}

/** The catch table — odds sum to 1. */
Fishing.CATCHES = [
    { name: 'an old boot', odds: 0.12, value: 0 },
    { name: 'Funa',        odds: 0.45, value: 80 },
    { name: 'Koi',         odds: 0.30, value: 240 },
    { name: 'Unagi',       odds: 0.10, value: 520 },
    { name: 'GOLDEN KOI',  odds: 0.03, value: 1500 },
];

if (typeof window !== 'undefined') window.Fishing = Fishing;
