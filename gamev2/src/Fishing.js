/**
 * Fishing — the pond mini game.
 *
 * Buy the fishing rod at any konbini counter, then bump into any pond edge
 * to cast: the bobber plops in, ripples... and when the "!" flashes you have
 * a beat to press SPACE. A fish goes into the bag (menu → Items) as an item,
 * one per species (issue #83): sell it at a konbini counter or the izakaya
 * bar, or have the izakaya grill it. An old boot is thrown straight back.
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
        this.keys = scene.input.keyboard.addKeys({ space: K.SPACE, enter: K.ENTER, esc: K.ESC });
    }

    isActive() { return this.state !== 'idle'; }

    /**
     * The player bumped a blocked cell — if it's pond water, start fishing
     * (rod required; the konbini counter sells one).
     */
    checkStart(gridX, gridY) {
        if (this.isActive()) return;
        if (!this.scene.roomManager.interactionAt(gridX, gridY, 'pond')) return;

        if (!this.scene.shop.items['fishing-rod']) {
            this.scene.shop.toast('you need a fishing rod — the konbini sells them');
            return;
        }

        // swallow the keys that got us here
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.space); JD(this.keys.enter); JD(this.keys.esc);

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

        // food & drink buffs (issue #46): quicker bites, a longer strike
        // window, luckier catches — say which ones are helping this cast
        const shop = this.scene.shop;
        const helping = shop.activeEffects().filter(e => e.fishBite || e.fishWindow || e.fishLuck).map(e => e.name);
        shop.toast(helping.length ? `... (${helping.join(' + ')} helping)` : '...');
        this.timer = this.scene.time.delayedCall(
            (1200 + Math.random() * 3300) * shop.buff('fishBite'), () => this.bite());
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
        this.timer = this.scene.time.delayedCall(1100 * this.scene.shop.buff('fishWindow'),
            () => this.finish(false, 'too slow — it got away...'));
    }

    /** SPACE during the strike window lands whatever bit. */
    strike() {
        if (this.state === 'waiting') return this.finish(false, 'nothing on the line yet — it swam off');
        if (this.state !== 'strike') return;
        const roll = Math.random();
        let acc = 0;
        const table = Fishing.catchTable(this.scene.shop.buff('fishLuck'));
        const c = table.find(f => (acc += f.odds) > roll) || table[0];
        const shop = this.scene.shop;
        const message = Fishing.catchMessage(c, shop.fmt(c.value));
        this.finish(true, message);
        const fresh = shop.addCatch(c);
        if (fresh.length) {
            // let the catch toast be read in full first, then celebrate
            this.scene.time.delayedCall(Shop.toastMs(message), () => shop.toast(`★ achievement: ${fresh.join(' + ')}`));
        }
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
        if (JD(k.space) || JD(k.enter)) return this.strike();
    }
}

/**
 * The catch table — odds sum to 1. `value` is what a shop pays for one; a
 * catch worth nothing is junk and never reaches the bag. Everything else
 * becomes an inventory item (Shop.fishItems): `id` is its save-file key —
 * don't rename — `desc` and `icon` show in the lists, and `grilled` is the
 * food-slot effect the izakaya's grill gives it (same keys as any item's
 * `effect`, see Shop.EFFECT_KINDS).
 */
Fishing.CATCHES = [
    { id: 'old-boot',   name: 'an old boot', odds: 0.12, value: 0 },
    { id: 'funa',       name: 'Funa',        odds: 0.45, value: 80,
      desc: 'a small pond carp. grilled: speed +10% for 2 min.',
      grilled: { speed: 1.1, secs: 120 },
      icon: { shape: 'fish', colors: { a: '#9fb2c4', b: '#6f8499', c: '#cfdbe6' } } },
    { id: 'koi',        name: 'Koi',         odds: 0.30, value: 240,
      desc: 'a handsome one. grilled: speed +20% for 3 min.',
      grilled: { speed: 1.2, secs: 180 },
      icon: { shape: 'fish', colors: { a: '#fff4ea', b: '#e2cdbd', c: '#f0642d' } } },
    { id: 'unagi',      name: 'Unagi',       odds: 0.10, value: 520,
      desc: 'a fat eel. grilled: speed +40% for 3 min.',
      grilled: { speed: 1.4, secs: 180 },
      icon: { shape: 'eel', colors: { a: '#7fa36a', b: '#f2e6a8' } } },
    { id: 'golden-koi', name: 'Golden Koi',  odds: 0.03, value: 1500,
      desc: 'it glitters. grilled: showdown winnings +100%, speed +30%. 5 min.',
      grilled: { speed: 1.3, prizeBonus: 2, secs: 300 },
      icon: { shape: 'fish-rare', colors: { a: '#ffd23a', b: '#d99a12', c: '#fff3a8' } } },
];

/** A catch worth this much or more is a rare one (luck favours them; the Big Catch achievement). */
Fishing.RARE_VALUE = 500;

Fishing.isRare = (c) => c.value >= Fishing.RARE_VALUE;

/** What the toast says about a landed catch: what it is and where it went. */
Fishing.catchMessage = (c, price) => c.value > 0
    ? `${c.name}! it's in your bag — sells for ${price} at a konbini counter or the izakaya`
    : `${c.name}... you throw it back.`;

/**
 * The catch table for a luck multiplier (1 = plain). Luck above 1 takes the
 * worthless catches off the table and multiplies the odds of the rare ones
 * (Fishing.isRare), then renormalizes so the odds still sum to 1.
 */
Fishing.catchTable = (luck) => {
    if (!(luck > 1)) return Fishing.CATCHES;
    const lucky = Fishing.CATCHES.filter(f => f.value > 0)
        .map(f => Object.assign({}, f, { odds: f.odds * (Fishing.isRare(f) ? luck : 1) }));
    const total = lucky.reduce((sum, f) => sum + f.odds, 0);
    return lucky.map(f => Object.assign({}, f, { odds: f.odds / total }));
};

if (typeof window !== 'undefined') window.Fishing = Fishing;
