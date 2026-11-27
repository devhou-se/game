/**
 * Shop — money, inventory, food & drink (issues #12, #46).
 *
 * The player has a yen wallet and an inventory, both persisted in
 * localStorage. Everything starts with a bump:
 *   - a vending machine (any map)            -> canned drinks
 *   - a konbini counter                       -> the whole store
 *   - a konbini drinks shelf/fridge/freezer   -> just the drinks
 *   - a konbini snack shelf                   -> just the food
 *   - the bar in a room with `shopMenu`       -> that venue's menu (izakaya)
 * Bought items live in the inventory (menu → Items, or click the ¥ in the
 * HUD) and are used from there, or straight from the buy list with
 * SHIFT+ENTER ("buy & use now").
 *
 * Fish caught at a pond are inventory items too (issue #83): a konbini
 * counter and the izakaya bar buy them — the last row of their list switches
 * the panel to SELL and back — and the izakaya will also grill one for a
 * food effect (SHIFT+ENTER there).
 *
 * Every row, and every active-effect chip, carries the item's icon
 * (ItemIcons, issue #82).
 *
 * Every consumable has an effect. Effects are additive buffs only — nothing
 * here ever slows or gates the player (the energy meter, issue #209, takes
 * away only the sprint, and only when it is empty: Energy.js). One DRINK effect and one FOOD effect
 * can be active at once: using the same item again refreshes its timer, a
 * different item in the same slot replaces it (the toast says what it
 * replaced). Active effects show as chips under the HUD with the time left,
 * and are saved with an absolute expiry so a reload keeps them.
 *
 * Same overlay idiom as the station picker: arrows/WASD + ENTER/SPACE, ESC,
 * rows clickable. No extra key bindings: ←/→ picks a quantity, SHIFT is the
 * modifier.
 */
class Shop {
    constructor(scene) {
        this.scene = scene;
        this.STORE_KEY = 'gamev2_shop';
        this.visible = false;      // buy / sell overlay
        this.mode = 'buy';         // which list that overlay shows: 'buy' | 'sell'
        this.invVisible = false;   // inventory overlay
        this.objs = [];
        this.rows = [];
        this.selected = 0;
        this.qty = 1;
        this.effects = {};         // slot ('drink' | 'food') -> active effect
        this.woreOff = [];         // names of expired effects still to be announced
        this.notices = [];         // other lines waiting for a free screen (energy, stamps)
        this.energyDrain = 1;      // the debug menu's "fast hunger" raises it
        this.clockOffset = 0;      // ms added to the clock — tests fast-forward buffs with it

        const cfg = scene.config.shop || {};
        // the fish are always in the catalogue, whatever config sells
        const sold = cfg.items || Shop.DEFAULT_ITEMS;
        this.catalogue = sold.concat(Shop.fishItems().filter(f => !sold.some(i => i.id === f.id)));
        this.startingMoney = cfg.startingMoney != null ? cfg.startingMoney : 5000;

        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ up: K.UP, down: K.DOWN, left: K.LEFT, right: K.RIGHT,
            w: K.W, s: K.S, a: K.A, d: K.D,
            enter: K.ENTER, space: K.SPACE, shift: K.SHIFT, esc: K.ESC });

        this.load();

        // active-effect chips, stacked under the right end of the HUD bar:
        // one per slot, each with the item's icon and a live countdown
        const chip = (color) => {
            const t = scene.add.text(scene.cameras.main.width - 12, 0, '', {
                fontSize: '14px', fill: color, fontFamily: 'PressStart2P',
                backgroundColor: 'rgba(0,0,0,0.6)',
                padding: { left: Shop.CHIP_PAD + ItemIcons.SLOT, right: Shop.CHIP_PAD, y: 12 },
            });
            t.setOrigin(1, 0);
            t.setScrollFactor(0);
            t.setDepth(1001);
            t.setResolution(1);
            t.setVisible(false);
            return t;
        };
        this.effectChips = { drink: chip('#66ff88'), food: chip('#ffcc66') };
        this.chipIcons = {};       // slot -> [slot square, icon] drawn inside that chip
        // the energy meter (issue #209): an onigiri and a row of segments,
        // first in that stack — tap it for the Items screen, like the wallet
        this.meter = scene.add.graphics();
        this.meter.setScrollFactor(0).setDepth(1001);
        this.meterIcon = scene.add.image(0, 0, ItemIcons.ensure(scene, this.itemById('onigiri') || { id: 'energy', category: 'food' }));
        this.meterIcon.setDisplaySize(Shop.METER.icon, Shop.METER.icon).setScrollFactor(0).setDepth(1002);
        this.meterIcon.setInteractive({ useHandCursor: true });
        this.meterIcon.on('pointerdown', () => this.showInventory());
        scene.time.addEvent({ delay: 250, loop: true, callback: () => this.updateEffectChip() });
        this.updateEffectChip();
    }

    updateEffectChip() {
        this.expireEffects();
        this.announceWoreOff();
        // the touch sprint pill is dimmed while sprint is off (an open list still uses it as SHIFT)
        const tc = this.scene.touchControls;
        if (tc && tc.root) tc.root.classList.toggle('tc-nosprint', this.energy <= 0 && !this.isVisible());
        // just under the HUD bar, at its right end (40px tall and the canvas
        // wide, unless the bar is magnified — GameScene.layoutHUD)
        const scene = this.scene;
        let y = (scene.hudBarHeight || UI.HUD_HEIGHT) + 8;
        y = this.drawMeter((scene.hudWidth || scene.cameras.main.width) - 12, y) + 4;
        for (const slot of Shop.SLOTS) {
            const chip = this.effectChips[slot], fx = this.effects[slot];
            let icon = this.chipIcons[slot];
            if (icon) icon.forEach(o => o.setVisible(!!fx));
            if (!fx) { chip.setVisible(false); continue; }
            chip.setText(`${fx.name} ${this.fmtTime(fx.until - this.now())}`);
            chip.setPosition((scene.hudWidth || scene.cameras.main.width) - 12, y);
            chip.setVisible(true);
            // the icon fills the chip's left padding
            const item = this.itemById(fx.id) || fx;
            if (!icon) icon = this.chipIcons[slot] = ItemIcons.add(this.scene, item, 0, 0, 1002);
            const key = ItemIcons.ensure(this.scene, item);
            if (icon[1].texture.key !== key) icon[1].setTexture(key).setDisplaySize(ItemIcons.DISPLAY, ItemIcons.DISPLAY);
            icon.forEach(o => o.setPosition(chip.x - chip.width + chip.height / 2, y + chip.height / 2));
            y += chip.height + 4;
        }
    }

    /**
     * The energy meter, its right edge at `right` and its top at `y`: a dark
     * backdrop, the onigiri and Energy.SEGMENTS segments, lit from the left
     * in the level's colour. Returns the y under it.
     */
    drawMeter(right, y) {
        const M = Shop.METER, g = this.meter;
        if (!g) return y;
        const lit = Energy.segments(this.energy);
        const w = M.pad + M.icon + M.gap + Energy.SEGMENTS * (M.segW + M.segGap) - M.segGap + M.pad;
        const x = right - w;
        g.clear();
        g.fillStyle(0x000000, 0.6);
        g.fillRect(x, y, w, M.height);
        const sx = x + M.pad + M.icon + M.gap, sy = y + (M.height - M.segH) / 2;
        for (let i = 0; i < Energy.SEGMENTS; i++) {
            g.fillStyle(i < lit ? Energy.color(this.energy) : 0x444444, 1);
            g.fillRect(sx + i * (M.segW + M.segGap), sy, M.segW, M.segH);
        }
        this.meterIcon.setPosition(x + M.pad + M.icon / 2, y + M.height / 2);
        this.meterIcon.setAlpha(this.energy > 0 ? 1 : 0.45);
        return y + M.height;
    }

    // ---------------- state ----------------

    /** The shop's clock. Effects expire against this, not a frame timer. */
    now() { return Date.now() + this.clockOffset; }

    /**
     * Read the save blob. Tolerates every older shape: the issue #12 blob was
     * just `{money, items}`, v2 added effects and the consumption counters,
     * v3 the fish (they are plain `items`) and the `caught` counters, v4 the
     * energy meter, the stamp card and the hints already given. Whatever
     * is missing defaults to empty and the wallet is never touched, unknown
     * item ids are kept (the catalogue may bring them back) and junk counts
     * are dropped.
     */
    load() {
        let raw = {};
        try { raw = JSON.parse(localStorage.getItem(this.STORE_KEY) || '{}') || {}; } catch (e) { raw = {}; }
        if (typeof raw !== 'object') raw = {};
        const counts = (obj) => {
            const out = {};
            if (obj && typeof obj === 'object') {
                for (const id in obj) {
                    const n = Math.floor(Number(obj[id]));
                    if (n > 0) out[id] = n;
                }
            }
            return out;
        };
        this.money = typeof raw.money === 'number' && isFinite(raw.money) ? Math.max(0, raw.money) : this.startingMoney;
        this.items = counts(raw.items);   // id -> count owned
        this.used = counts(raw.used);     // id -> times consumed (achievements)
        this.caught = counts(raw.caught); // fish id -> times landed (achievements)
        // issue #209: a save from before the meter (and a new player) starts full
        this.energy = Energy.clamp(raw.energy);
        this.stamps = Stamps.clean(raw.stamps);     // place id -> 1 (the stamp card)
        this.hints = Stamps.clean(raw.hints);       // one-time hints already given
        // the day's omikuji, {date, i}, when one has been drawn (ShrineVisit; absent in older blobs)
        this.omikuji = Shop.omikujiOf(raw.omikuji);
        // the palace's visitors' book, {date, n}, once it has been signed (PalaceVisit; absent in older blobs)
        this.guestbook = Shop.guestbookOf(raw.guestbook);
        // the job in the towers, {merged, shifts, earned}, once signed on at a reception desk (Career; absent in older blobs)
        this.career = Shop.careerOf(raw.career);

        // effects are saved as {id, until}; the numbers come back from the
        // catalogue, and an expiry can never be further off than the item lasts
        this.effects = {};
        const saved = raw.effects && typeof raw.effects === 'object' ? raw.effects : {};
        const now = this.now();
        for (const slot of Shop.SLOTS) {
            const e = saved[slot], item = e && this.itemById(e.id);
            if (!item || !item.effect || Shop.slotOf(item) !== slot || !(e.until > now)) continue;
            this.effects[slot] = this.makeEffect(item, Math.min(e.until, now + (item.effect.secs || 0) * 1000));
        }
    }

    save() {
        const effects = {};
        for (const slot in this.effects) effects[slot] = { id: this.effects[slot].id, until: this.effects[slot].until };
        try {
            const blob = {
                v: 4, money: this.money, items: this.items, effects, used: this.used, caught: this.caught,
                energy: Math.round(this.energy * 100) / 100, stamps: this.stamps, hints: this.hints };
            if (this.omikuji) blob.omikuji = this.omikuji;   // only once a fortune has been drawn
            if (this.guestbook) blob.guestbook = this.guestbook;   // only once the palace's book has been signed
            if (this.career) blob.career = this.career;   // only once hired: having one is the staff pass
            localStorage.setItem(this.STORE_KEY, JSON.stringify(blob));
        } catch (e) { /* private mode etc — play on without persistence */ }
    }

    fmt(n) { return '¥' + n.toLocaleString(); }

    /** 45s / 1:30 — for chips, toasts and the items screen. */
    fmtTime(ms) {
        const secs = Math.max(0, Math.ceil(ms / 1000));
        return secs < 60 ? `${secs}s` : `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
    }

    itemById(id) { return this.catalogue.find(i => i.id === id); }

    /** Everything that can be eaten or drunk (the achievement denominator). */
    consumables() { return this.catalogue.filter(i => ['drink', 'food'].includes(Shop.categoryOf(i))); }

    /** What the player holds that a shop will pay for (the fish). */
    sellable() { return this.catalogue.filter(i => i.sell > 0 && this.items[i.id]); }

    /**
     * A landed catch (a Fishing.CATCHES row) goes into the bag — junk worth
     * nothing does not. Returns the names of any achievements it completed.
     */
    addCatch(c) {
        if (!(c.value > 0) || !this.itemById(c.id)) return [];
        const achievements = this.scene.achievementManager;
        const done = () => achievements ? achievements.fishingProgress().filter(a => a.complete).map(a => a.name) : [];
        const before = done();
        this.items[c.id] = (this.items[c.id] || 0) + 1;
        this.caught[c.id] = (this.caught[c.id] || 0) + 1;
        this.save();
        return done().filter(name => !before.includes(name));
    }

    // ---------------- world interaction ----------------

    /**
     * The player bumped a blocked cell — if it's a vending machine (anywhere),
     * konbini furniture (counter, shelves, fridges, freezers) or a venue's
     * bar, open the matching list. Matching is footprint-aware: a multi-cell
     * sprite (the 3-wide counter, the 2-tall fridge, a machine whose art
     * extends past its anchor cell) opens from ANY of its cells, so every
     * side works.
     */
    checkShopInteraction(gridX, gridY) {
        if (this.visible || this.invVisible) return;
        const hit = this.scene.roomManager.interactionAt(gridX, gridY, 'shop');
        if (hit) return this.showShop(hit.kind);
    }

    // ---------------- effects ----------------

    makeEffect(item, until) {
        return Object.assign({}, item.effect,
            { id: item.id, name: item.effectName || item.name, slot: Shop.slotOf(item), until });
    }

    /**
     * Drop effects that have run out. Whoever notices first (the chip timer,
     * a step, a mini-game asking for a buff) only queues the name — the
     * "wore off" toast is said by announceWoreOff once the screen is free.
     */
    expireEffects() {
        const now = this.now();
        let changed = false;
        for (const slot of Shop.SLOTS) {
            const fx = this.effects[slot];
            if (!fx || now <= fx.until) continue;
            delete this.effects[slot];
            changed = true;
            this.woreOff.push(fx.name);
        }
        if (changed) this.save();
    }

    /** Say what wore off, then any waiting notice — never over another toast or an open list. */
    announceWoreOff() {
        if (this._toast || this.isVisible()) return;
        if (this.woreOff.length) {
            this.toast(`${this.woreOff.join(' and ')} wore off`);
            this.woreOff = [];
        } else if (this.notices.length) {
            this.toast(this.notices.shift());
        }
    }

    // ---------------- energy and the stamp card (issue #209; the rules are in Energy.js) ----------------

    /**
     * The player walked one cell. The meter drops a little; the first time
     * it runs low a hint is queued (once ever), and a line every time it
     * runs out. Written to the save once per whole point, not every step.
     */
    walked() {
        const before = this.energy;
        if (before <= 0) return;
        this.energy = Energy.afterStep(before, this.energyDrain);
        const note = Energy.notice(before, this.energy, this.hints.low);
        if (note) {
            if (note.kind === 'low') this.hints.low = 1;
            this.notices.push(note.text);
        }
        if (note || Math.floor(before) !== Math.floor(this.energy)) this.save();
        if (note || Energy.segments(before) !== Energy.segments(this.energy) ||
            Energy.level(before) !== Energy.level(this.energy)) this.updateEffectChip();
    }

    /** What holding sprint multiplies a step's speed by right now (1 when peckish). */
    sprintMultiplier() { return Energy.sprintMultiplier(this.energy); }

    /**
     * Sprint is held while walking. On an empty meter it does nothing, so the
     * peckish line is said again (queued like any notice, at most once per
     * Energy.REMIND_MS) — a save loaded at zero never saw the first one.
     */
    sprintHeld() {
        if (!Energy.remind(this.energy, Date.now(), this._reminded)) return;
        this._reminded = Date.now();
        if (!this.notices.includes(Energy.PECKISH)) this.notices.push(Energy.PECKISH);
    }

    /** A free cup from a konbini's water cooler. */
    drinkWater() {
        if (this.isVisible()) return;
        const before = this.energy;
        this.energy = Energy.afterWater(before);
        if (this.energy > before) {
            this.notices = this.notices.filter(n => n !== Energy.PECKISH);
            this.toast(`a cup of water, on the house: energy +${Math.round(this.energy - before)}`);
            this.save();
            this.updateEffectChip();
        } else {
            this.toast('a cup of water. you are not that thirsty: something from the shelves would do more');
        }
    }

    /**
     * Stamp the card for a purchase at the open venue, if the place is new.
     * Returns the line to add to the purchase toast ('' when nothing new);
     * a milestone's reward (Stamps.MILESTONES) is paid here.
     */
    stampPurchase() {
        const scene = this.scene, rm = scene.roomManager;
        if (!rm) return '';
        const place = Stamps.placeFor(this.kind, rm.currentDistrict(), scene.config.rooms[rm.currentRoom]);
        if (!place || this.stamps[place]) return '';
        const achievements = scene.achievementManager;
        const wasDone = achievements && achievements.stampProgress()[0].complete;
        const before = Stamps.count(this.stamps);
        this.stamps[place] = 1;
        let line = ` · stamp ${before + 1} on your card`;
        for (const m of Stamps.rewards(before, before + 1)) {
            if (m.yen) this.money += m.yen;
            if (m.item && this.itemById(m.item)) this.items[m.item] = (this.items[m.item] || 0) + 1;
            line += `: ${Stamps.describe(m, id => (this.itemById(id) || { name: id }).name, n => this.fmt(n))}!`;
        }
        if (achievements && !wasDone && achievements.stampProgress()[0].complete) {
            this.notices.push(`★ achievement: ${Stamps.ACHIEVEMENT}`);
        }
        return line;
    }

    /** Active effects, drink first. */
    activeEffects() {
        this.expireEffects();
        return Shop.SLOTS.map(slot => this.effects[slot]).filter(Boolean);
    }

    /**
     * Combined movement effect, or null. Applied by InputHandler on each
     * step: speeds multiply, and a `steady` effect cancels any wobble.
     */
    movementModifier() {
        const fx = this.activeEffects();
        if (!fx.length) return null;
        const steady = fx.some(e => e.steady);
        return {
            speed: fx.reduce((m, e) => m * (e.speed || 1), 1),
            scramble: steady ? 0 : Math.max(...fx.map(e => e.scramble || 0)),
        };
    }

    /**
     * A mini-game buff from the active effects: the product of every active
     * value for `key` (1 when nothing is active), or the sum for the additive
     * kinds. Fishing and the drinking game ask for theirs by name.
     */
    buff(key) {
        const kind = Shop.EFFECT_KINDS[key] || {};
        return this.activeEffects().reduce(
            (acc, e) => e[key] == null ? acc : (kind.additive ? acc + e[key] : acc * e[key]),
            kind.additive ? 0 : 1);
    }

    /** "speed +50% for 30s" — the numbers, straight from the item's data. */
    effectSummary(item) {
        if (!item.effect) return item.desc;
        const parts = [];
        for (const key in Shop.EFFECT_KINDS) {
            if (item.effect[key]) parts.push(Shop.EFFECT_KINDS[key].describe(item.effect[key]));
        }
        return `${parts.join(', ')} for ${this.fmtTime((item.effect.secs || 0) * 1000)}`;
    }

    /** Use one of an item. A fish is only eaten `grilled` (the izakaya's sell list). */
    use(id, opts) {
        if (!this.items[id]) return;
        const item = this.itemById(id);
        if (!item) return;
        if (item.permanent) return this.toast(`${item.name}: ${item.desc}`);
        if (Shop.categoryOf(item) === 'fish' && !(opts && opts.grilled)) {
            return this.toast(`${item.name}: sell it at a konbini counter or the izakaya (${this.fmt(item.sell)}) — the izakaya grills it too`);
        }
        this.items[id]--;
        if (!this.items[id]) delete this.items[id];

        const achievements = this.scene.achievementManager;
        const doneBefore = achievements ? achievements.consumptionProgress().filter(a => a.complete).map(a => a.name) : [];
        this.used[id] = (this.used[id] || 0) + 1;

        let note = '';
        const gain = Math.round(Energy.afterEating(this.energy, item) - this.energy);
        this.energy = Energy.afterEating(this.energy, item);
        this.notices = this.notices.filter(n => n !== Energy.PECKISH && n !== Energy.HINT);
        if (item.effect) {
            const slot = Shop.slotOf(item);
            const old = this.activeEffects().find(e => e.slot === slot);
            if (old) note = old.id === id ? ' (timer refreshed)' : ` (replaces ${old.name})`;
            this.effects[slot] = this.makeEffect(item, this.now() + (item.effect.secs || 0) * 1000);
        }
        this.updateEffectChip();
        this.toast(`${item.effectName || item.name}: ${this.effectSummary(item)}${note}${gain > 0 ? ` · energy +${gain}` : ''}`);
        this.save();

        if (achievements) {
            const fresh = achievements.consumptionProgress()
                .filter(a => a.complete && !doneBefore.includes(a.name)).map(a => a.name);
            if (fresh.length) {
                // let the use toast land first, then celebrate (all of them)
                this.scene.time.delayedCall(1500, () => this.toast(
                    `★ achievement${fresh.length > 1 ? 's' : ''}: ${fresh.join(' + ')}`));
            }
        }

        // a little "gulp": the player pops and glows for a beat
        const p = this.scene.player.sprite;
        if (this._gulp) { this._gulp.stop(); p.setScale(this._gulpScale); }
        this._gulpScale = p.scale;
        p.setTint(Shop.slotOf(item) === 'food' ? 0xffe0a0 : 0xaaffcc);
        this._gulp = this.scene.tweens.add({
            targets: p, scale: { from: this._gulpScale * 1.35, to: this._gulpScale },
            duration: 280, ease: 'Back.easeOut',
            onComplete: () => { p.clearTint(); this._gulp = null; },
        });
    }

    // ---------------- buy overlay ----------------

    isVisible() { return this.visible || this.invVisible; }

    showShop(kind) {
        if (this.isVisible()) return;
        const venue = Shop.VENUES[kind];
        if (!venue) return;
        if (!this.catalogue.some(venue.sells)) return;
        this.kind = kind;
        this.mode = 'buy';
        this.selected = 0;
        this.qty = 1;
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        // swallow the bump keypress (a held direction must not change the quantity)
        [k.enter, k.space, k.esc, k.left, k.right, k.a, k.d, k.up, k.down, k.w, k.s].forEach(JD);
        this.visible = true;
        this.refreshStock();
        this.render();
    }

    selling() { return this.visible && this.mode === 'sell'; }

    /**
     * What the open list holds: the venue's menu, the player's fish (sell
     * mode) or everything owned (Items). A venue that buys gets one more row
     * under its items — `switchRow` — that flips the panel between the two.
     */
    refreshStock() {
        const venue = Shop.VENUES[this.kind];
        const onItem = this.selected < (this.stock || []).length;
        if (this.invVisible) this.stock = Object.keys(this.items).map(id => this.itemById(id)).filter(Boolean);
        else this.stock = this.selling() ? this.sellable() : this.catalogue.filter(venue.sells);
        this.switchRow = this.invVisible || !venue.buys ? null : (this.selling()
            ? { label: '‹ back to the menu', desc: 'buy something instead' }
            : { label: 'sell your catch ›', desc: venue.grills ? 'the bar buys fish — and grills them' : 'the counter buys fish' });
        // a row that went (the last of a fish sold) leaves the selection on an
        // item while there is one, not on the switch row under them
        const last = onItem && this.stock.length ? this.stock.length - 1 : this.rowCount() - 1;
        this.selected = Math.max(0, Math.min(this.selected, last));
    }

    /** Selectable rows: the items, then the buy/sell switch. */
    rowCount() { return this.stock.length + (this.switchRow ? 1 : 0); }

    setMode(mode) {
        this.mode = mode;
        this.selected = 0;
        this.qty = 1;
        this.repaint();
    }

    /** Most of the selected item the wallet (and the 9 cap) allows — or, selling, all you hold. */
    maxQty(item) {
        if (!item) return 1;
        if (this.selling()) return Math.max(1, this.items[item.id] || 0);
        if (item.permanent) return 1;
        return Math.max(1, Math.min(9, Math.floor(this.money / item.price)));
    }

    setQty(n) {
        const item = this.stock[this.selected];
        this.qty = Math.max(1, Math.min(this.maxQty(item), n));
        this.paint();
    }

    /** Buy `qty` of the selected item; with useNow, consume one on the spot. */
    buy(useNow) {
        const item = this.stock[this.selected];
        if (!item) return;
        if (item.permanent && this.items[item.id]) return this.toast('you already have one');
        const qty = item.permanent ? 1 : this.qty;
        const cost = item.price * qty;
        if (this.money < cost) return this.toast(`not enough yen — that's ${this.fmt(cost)}`);
        this.money -= cost;
        this.items[item.id] = (this.items[item.id] || 0) + qty;
        const stamp = this.stampPurchase();
        this.save();
        this.scene.updateHUD();
        if (useNow && !item.permanent) {
            this.use(item.id);
            // the use toast has the screen: the stamp is said after it
            if (stamp) this.notices.push(stamp.replace(/^ · /, ''));
        } else this.toast(`bought ${qty > 1 ? qty + '× ' : ''}${item.name} — it's in your items (menu)${stamp}`);
        this.qty = 1;
        this.repaint();
    }

    // ---------------- selling (issue #83) ----------------

    /** Sell `qty` of the selected fish to the venue. */
    sell() {
        const item = this.stock[this.selected];
        const qty = item ? Math.min(this.qty, this.items[item.id] || 0) : 0;
        if (!qty) return;
        const gain = Shop.sellValue(item, qty);
        this.money += gain;
        this.items[item.id] -= qty;
        if (!this.items[item.id]) delete this.items[item.id];
        this.save();
        this.scene.updateHUD();
        this.toast(`sold ${qty > 1 ? qty + '× ' : ''}${item.name} for ${this.fmt(gain)}`);
        this.qty = 1;
        this.repaint();
    }

    /** Have the venue grill one of the selected fish, and eat it. */
    grill() {
        const item = this.stock[this.selected];
        if (!item || !Shop.VENUES[this.kind].grills) return;
        this.use(item.id, { grilled: true });
        this.qty = 1;
        this.repaint();
    }

    /** ENTER / SPACE in the buy or sell list (SHIFT held: the second action). */
    confirm(shift) {
        if (this.selected >= this.stock.length) {
            return this.switchRow ? this.setMode(this.selling() ? 'buy' : 'sell') : undefined;
        }
        if (!this.selling()) return this.buy(shift);
        return shift && Shop.VENUES[this.kind].grills ? this.grill() : this.sell();
    }

    // ---------------- inventory overlay ----------------

    showInventory() {
        if (this.isVisible()) return;
        this.selected = 0;
        InputHandler.swallow(this.keys);   // the menu's ENTER, and the W / S that stepped to "Items"
        this.invVisible = true;
        this.refreshStock();
        this.render();
    }

    useSelected() {
        const item = this.stock[this.selected];
        if (!item) return;
        // using an item drops you straight back into the game — no menu
        // layers left to unwind (the use-flash + toast show it worked)
        this.hide();
        this.use(item.id);
    }

    // ---------------- shared overlay plumbing ----------------

    hide() {
        this.visible = false;
        this.invVisible = false;
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.rows = [];
        this.descText = this.qtyText = this.totalText = this.useNowText = this.titleText = null;
        this.stepper = [];
    }

    select(i) {
        if (i !== this.selected) this.qty = 1;
        this.selected = i;
        this.paint();
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        // both confirm keys must be consumed, or a held one fires next frame
        const enter = JD(k.enter), space = JD(k.space);
        if (enter || space) return this.visible ? this.confirm(k.shift.isDown) : this.useSelected();
        const n = this.rowCount();
        if (!n) return;
        if (JD(k.up) || JD(k.w)) this.select((this.selected - 1 + n) % n);
        if (JD(k.down) || JD(k.s)) this.select((this.selected + 1) % n);
        if (this.visible) {
            if (JD(k.left) || JD(k.a)) this.setQty(this.qty - 1);
            if (JD(k.right) || JD(k.d)) this.setQty(this.qty + 1);
        }
    }

    repaint() {
        // cheap full re-render: money, counts and the stock list all shift
        const wasShop = this.visible, wasInv = this.invVisible;
        this.hide();
        this.visible = wasShop;
        this.invVisible = wasInv;
        this.refreshStock();
        this.render();
    }

    paint() {
        this.rows.forEach((r, i) => r.setFill(i === this.selected ? '#ffff00' : (r.restFill || '#ffffff')));
        const item = this.stock[this.selected];
        // the quantity stepper and buttons belong to an item, not the switch row
        (this.stepper || []).forEach(o => o.setVisible(!!item));
        if (!item) {
            if (this.descText && this.switchRow && this.rowCount()) this.descText.setText(this.switchRow.desc);
            return;
        }
        if (this.descText) this.descText.setText(item.desc);
        if (!this.qtyText) return;
        if (this.selling()) {
            this.qtyText.setText(`×${this.qty}`);
            this.totalText.setText(`total +${this.fmt(Shop.sellValue(item, this.qty))}`);
            this.totalText.setFill('#ffd700');
            this.useNowText.setText(Shop.VENUES[this.kind].grills ? '[ grill & eat ]' : '');
        } else {
            const cost = item.price * (item.permanent ? 1 : this.qty);
            this.qtyText.setText(item.permanent ? '×1' : `×${this.qty}`);
            this.totalText.setText(`total ${this.fmt(cost)}`);
            this.totalText.setFill(this.money >= cost ? '#ffd700' : '#aa6666');
            this.useNowText.setText(item.permanent ? '' : '[ buy & use now ]');
        }
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const inv = this.invVisible, selling = this.selling(), venue = Shop.VENUES[this.kind];
        // an empty list says so on its first line; the switch row goes under it
        const lead = this.stock.length ? 0 : 1;
        const n = Math.max(1, lead + this.rowCount());
        const active = inv ? this.activeEffects() : [];
        // rows are 44px until the list would run off the screen (the Items
        // screen with nearly every item and every fish), then they close up
        const chrome = inv ? 210 + (active.length ? 30 : 0) : 250;
        const rowH = Math.max(ItemIcons.SLOT + 2, Math.min(44, Math.floor((H - 16 - chrome) / n)));
        const pw = 640, ph = chrome + n * rowH;
        const px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = this.objs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.75); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.hide());
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (x, y, t, size, bold, color, originX) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(originX != null ? originX : 0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };
        const button = (o, fn) => {
            o.setInteractive({ useHandCursor: true });
            o.on('pointerdown', fn);
            return o;
        };

        const roomConfig = this.scene.config.rooms[this.scene.roomManager.currentRoom];
        this.titleText = text(W / 2, py + 34, inv ? 'ITEMS' : Shop.titleFor(this.kind, roomConfig) + (selling ? ' · SELL' : ''), '32px', true);
        text(px + pw - 18, py + 34, this.fmt(this.money), '24px', true, '#ffd700', 1);

        if (!this.stock.length) {
            text(W / 2, py + (inv ? 108 : 92), inv ? 'nothing yet — find a vending machine'
                : 'nothing to sell — catch a fish at a pond', '20px', false, '#888888');
        }

        const nameX = px + 30 + ItemIcons.SLOT + 10;
        this.rows = this.stock.map((item, i) => {
            const y = py + 92 + i * rowH;
            const owned = this.items[item.id] || 0;
            objs.push(...ItemIcons.add(scene, item, px + 30 + ItemIcons.SLOT / 2, y, 2002));
            const row = text(nameX, y, inv ? `${item.name}  ×${owned}` : item.name, '24px', true, '#ffffff', 0);
            if (selling) {
                text(px + pw - 150, y, `have ×${owned}`, '20px', false, '#88aa88', 1);
                text(px + pw - 30, y, this.fmt(item.sell), '24px', false, '#ffd700', 1);
            } else if (inv) {
                if (item.sell > 0) text(px + pw - 30, y, `sells ${this.fmt(item.sell)}`, '20px', false, '#88aa88', 1);
                else if (Energy.valueOf(item)) text(px + pw - 30, y, `energy +${Energy.valueOf(item)}`, '20px', false, '#ffcc66', 1);
            } else {
                // what you already carry, and whether the wallet stretches to it
                const soldOut = item.permanent && owned;
                if (Energy.valueOf(item)) text(px + pw - 240, y, `energy +${Energy.valueOf(item)}`, '18px', false, '#ffcc66', 1);
                if (owned) text(px + pw - 150, y, item.permanent ? 'owned' : `have ×${owned}`, '20px', false, '#88aa88', 1);
                text(px + pw - 30, y, this.fmt(item.price), '24px', false,
                     soldOut ? '#555555' : (this.money >= item.price ? '#ffffff' : '#aa6666'), 1);
            }
            row.setInteractive({ useHandCursor: true });
            if (inv) {
                row.on('pointerover', () => this.select(i));
                row.on('pointerdown', () => { this.select(i); this.useSelected(); });
            } else {
                // the buy list does NOT select on hover: the quantity stepper
                // and buttons sit under the rows, and a mouse travelling down
                // to them would drag the selection to the last row. Click
                // picks a row; clicking the picked row (or [ buy ]) buys it.
                // The sell list works the same way.
                row.on('pointerdown', () => (i === this.selected ? this.confirm(false) : this.select(i)));
            }
            return row;
        });
        if (this.switchRow) {
            const i = this.stock.length;
            const row = text(px + 30, py + 92 + (lead + i) * rowH, this.switchRow.label, '24px', true, '#66ddff', 0);
            row.restFill = '#66ddff';
            row.setInteractive({ useHandCursor: true });
            row.on('pointerdown', () => { this.selected = i; this.confirm(false); });
            this.rows.push(row);
        }

        let y = py + 92 + n * rowH + 6;
        this.descText = text(W / 2, y, '', '18px', false, '#9999aa');
        if (inv) {
            if (active.length) {
                y += 30;
                text(W / 2, y, 'active: ' + active.map(e => `${e.name} ${this.fmtTime(e.until - this.now())}`).join(' · '),
                     '18px', false, '#66ff88');
            }
            text(W / 2, py + ph - 28, Hints.text(scene, '↑/↓ + ENTER: use · ESC: close'), '16px', false, '#888888');
        } else {
            // quantity stepper + total, and the mouse/touch route to "buy & use now"
            // (in the sell list the same widgets sell, and grill at the izakaya)
            y += 40;
            this.stepper = [
                button(text(px + 30, y, '‹', '28px', true, '#ffffff', 0), () => this.setQty(this.qty - 1)),
                this.qtyText = text(px + 74, y, '', '24px', true, '#ffffff'),
                button(text(px + 104, y, '›', '28px', true, '#ffffff', 0), () => this.setQty(this.qty + 1)),
                this.totalText = text(px + 140, y, '', '20px', false, '#ffd700', 0),
                this.useNowText = button(text(px + pw - 30, y, '', '20px', true, '#66ff88', 1), () => this.confirm(true)),
                button(text(px + pw - 222, y, selling ? '[ sell ]' : '[ buy ]', '20px', true, '#ffffff', 1), () => this.confirm(false)),
            ];
            if (!this.stock.length) {
                // nothing to sell: the only row is the way back
                text(W / 2, py + ph - 28, Hints.text(scene, 'ENTER back to the menu · ESC step away'), '16px', false, '#888888');
            } else {
                text(W / 2, py + ph - 52, Hints.text(scene, '↑/↓ pick · ←/→ quantity · ESC step away'), '16px', false, '#888888');
                text(W / 2, py + ph - 28, Hints.text(scene, !selling ? 'ENTER buy · SHIFT+ENTER buy & use now'
                    : venue.grills ? 'ENTER sell · SHIFT+ENTER grill & eat one' : 'ENTER sell'), '16px', false, '#888888');
            }
        }
        this.paint();
    }

    // ---------------- toast ----------------

    /** What the toast on screen says, or null when there is none. */
    toastText() {
        return this._toast && this._toast.active ? this._toast.text : null;
    }

    toast(msg) {
        if (this._toast) this._toast.destroy();
        const cam = this.scene.cameras.main;
        const o = this.scene.add.text(cam.width / 2, cam.height - 80, msg, {
            fontSize: '20px', fill: '#ffffff', fontFamily: 'PixelOperatorMonoBold',
            backgroundColor: 'rgba(0,0,0,0.75)', padding: { x: 10, y: 6 },
        });
        o.setOrigin(0.5, 0.5); o.setResolution(1);
        o.setScrollFactor(0); o.setDepth(3500);
        o.uiFloat = true;   // UIScale: magnified, but never moves the overlay it appears over
        this._toast = o;
        this.scene.tweens.add({
            targets: o, alpha: 0, delay: Shop.toastMs(msg), duration: 400,
            onComplete: () => { if (this._toast === o) this._toast = null; o.destroy(); },
        });
    }
}

/** The saved omikuji as {date, i}, or null for anything that is not one (which fortune `i` is: ShrineVisit). */
Shop.omikujiOf = (raw) => {
    if (!raw || typeof raw !== 'object' || !/^\d{4}-\d{2}-\d{2}$/.test(String(raw.date))) return null;
    const i = Math.floor(Number(raw.i));
    return i >= 0 ? { date: raw.date, i } : null;
};

/** The saved visitors' book as {date, n} (the day last signed, signatures in all), or null for anything else. */
Shop.guestbookOf = (raw) => {
    if (!raw || typeof raw !== 'object' || !/^\d{4}-\d{2}-\d{2}$/.test(String(raw.date))) return null;
    const n = Math.floor(Number(raw.n));
    return n >= 1 ? { date: raw.date, n } : null;
};

/**
 * The saved career as {merged, shifts, earned} (lifetime tickets, shifts worked, yen paid), or null for
 * anything without a usable `merged`. `merged` is the title: a damaged counter beside it reads as 0 and
 * does not cost the player the ladder.
 */
Shop.careerOf = (raw) => {
    const count = (v) => (typeof v === 'number' && isFinite(v) && v >= 0 ? Math.floor(v) : null);
    if (!raw || typeof raw !== 'object' || count(raw.merged) == null) return null;
    return { merged: count(raw.merged), shifts: count(raw.shifts) || 0, earned: count(raw.earned) || 0 };
};

/** How long a toast stays up before it fades — longer lines get longer. */
Shop.toastMs = (msg) => Math.max(1800, String(msg).length * 45);

/** Effect slots: one drink and one food effect can be active at a time. */
Shop.SLOTS = ['drink', 'food'];

/** Category of an item — older catalogues (config `shop.items`) may omit it. */
Shop.categoryOf = (item) => item.category || (item.permanent ? 'gear' : (item.effect ? 'drink' : 'food'));

/** The slot an item's effect occupies (a grilled fish is food). */
Shop.slotOf = (item) => ['food', 'fish'].includes(Shop.categoryOf(item)) ? 'food' : 'drink';

/** The HUD energy meter's measurements (HUD px): it is as tall as an effect chip. */
Shop.METER = { height: 38, pad: 6, icon: 32, gap: 6, segW: 10, segH: 14, segGap: 3 };

/** Gap between a HUD effect chip's icon slot, its text and its right edge. */
Shop.CHIP_PAD = 8;

/** What a shop pays for `qty` of an item — nothing for one it does not buy. */
Shop.sellValue = (item, qty) => Math.max(0, Math.floor((item && item.sell) || 0)) * Math.max(0, Math.floor(qty || 0));

/**
 * The fish as catalogue items, one per species worth anything, straight from
 * Fishing.CATCHES (the one value table): `sell` is the catch's value and the
 * `effect` is what it does grilled. They are sold nowhere (no `where`).
 */
Shop.fishItems = () => (typeof Fishing === 'undefined' ? [] : Fishing.CATCHES)
    .filter(c => c.value > 0)
    .map(c => ({ id: c.id, name: c.name, category: 'fish', sell: c.value, desc: c.desc,
                 effect: c.grilled, effectName: `Grilled ${c.name}`, icon: c.icon }));

/**
 * What each bump opens: a title and a filter over the catalogue. Items say
 * where they are sold with `where`: 'vending' (machines + konbini),
 * 'counter' (konbini only) or a venue id such as 'izakaya' (that bar only).
 * A venue with `buys` also pays for the player's fish (the SELL list), and
 * one with `grills` will cook one on the spot.
 */
Shop.VENUES = {
    vending: { title: 'VENDING MACHINE', sells: i => i.where === 'vending' },
    counter: { title: 'KONBINI',         sells: i => i.where === 'vending' || i.where === 'counter', buys: true },
    drinks:  { title: 'DRINKS',          sells: i => (i.where === 'vending' || i.where === 'counter') && Shop.categoryOf(i) === 'drink' },
    snacks:  { title: 'SNACKS',          sells: i => (i.where === 'vending' || i.where === 'counter') && Shop.categoryOf(i) === 'food' },
    izakaya: { title: 'IZAKAYA',         sells: i => i.where === 'izakaya', buys: true, grills: true },
    // Odori Park's hot-drinks tent (issue #219): the two warm ones off the machine's list
    stall:   { title: 'HOT DRINKS',      sells: i => i.id === 'canned-coffee' || i.id === 'green-tea' },
    // Tanukikoji's three shops (issue #219; a Shop<Town><n> room's `shopMenu`, tools/generate_houses.py
    // --shops): a short list each off the existing catalogue, over the counter; no stamp, no fish bought
    souvenirs: { title: 'OMIYAGE',    sells: i => ['melon-pan', 'ramune', 'green-tea'].includes(i.id) },
    crab:      { title: 'CRAB SHOP',  sells: i => ['onigiri', 'nikuman'].includes(i.id) },
    drugstore: { title: 'DRUGSTORE',  sells: i => ['zone-energy', 'canned-coffee', 'green-tea'].includes(i.id) },
    // an underground arcade's three counters (tools/generate_chikagai.py): short lists off the catalogue; no stamp, no fish bought
    bakery:   { title: 'BAKERY',    sells: i => ['melon-pan', 'nikuman', 'canned-coffee'].includes(i.id) },
    kissa:    { title: 'KISSATEN',  sells: i => ['canned-coffee', 'green-tea', 'melon-pan'].includes(i.id) },
    standbar: { title: 'STAND BAR', sells: i => ['highball', 'nama-beer', 'edamame', 'karaage'].includes(i.id) },
    // the airport pub (issue #218): the izakaya's drinks and food, over the bar; it buys no fish
    pub:     { title: 'AIRPORT PUB',     sells: i => i.where === 'izakaya' },
};

/**
 * The title over a venue's list. A room's `shopTitle` renames its counter
 * list (the Don Takote stores sell by the konbini rules but are no konbini);
 * its shelves and machines keep their own.
 */
Shop.titleFor = (kind, roomConfig) =>
    (kind === 'counter' && roomConfig && roomConfig.shopTitle) || Shop.VENUES[kind].title;

/**
 * Everything an item's `effect` can do (besides `secs`, how long it lasts).
 * `describe` words the number for toasts; `additive` kinds sum across the
 * two slots, the rest multiply. Who reads them:
 *   speed, scramble, steady  -> InputHandler (via movementModifier)
 *   fishBite, fishWindow, fishLuck -> Fishing
 *   headStart, prizeBonus    -> DrinkingGame
 *   focus                    -> Career (seconds on a shift's clock)
 */
Shop.EFFECT_KINDS = {
    speed:      { describe: v => `speed +${Math.round((v - 1) * 100)}%` },
    scramble:   { describe: v => `${Math.round(v * 100)}% wobble` },
    steady:     { describe: () => 'drinks cannot make you wobble' },
    fishBite:   { describe: v => `fish bite ${+(1 / v).toFixed(1)}× faster` },
    fishWindow: { describe: v => `fishing strike window +${Math.round((v - 1) * 100)}%` },
    fishLuck:   { describe: v => `no old boots, rare fish ×${v}` },
    headStart:  { describe: v => `${v} gulps head start in the nomikai showdown`, additive: true },
    prizeBonus: { describe: v => `nomikai showdown winnings +${Math.round((v - 1) * 100)}%` },
    focus:      { describe: v => `work clock +${v}s`, additive: true },
};

/**
 * The catalogue. config.json `shop.items` overrides it wholesale. Ids are
 * save-file keys — rename one and saved inventories lose it. `icon` picks a
 * pixel map and its colours (ItemIcons.SHAPES); without one the item gets its
 * category's default. The fish are added to whichever catalogue is in use
 * (Shop.fishItems). `energy` is what one restores on the meter (issue #209,
 * Energy.valueOf: food fills, a soft drink tops up, alcohol hardly counts).
 */
Shop.DEFAULT_ITEMS = [
    // --- drinks ---
    { id: 'zone-energy',   name: 'Zone Energy',   price: 300, where: 'vending', category: 'drink', energy: 30,
      icon: { shape: 'can', colors: { a: '#7b4dff', b: '#4a2bb0', c: '#35218a', d: '#ffe14a' } },
      desc: 'speed +50% for 30s', effect: { speed: 1.5, secs: 30 } },
    { id: 'vodka-redbull', name: 'Vodka Redbull', price: 800, where: 'vending', category: 'drink', energy: 10,
      icon: { shape: 'can', colors: { a: '#2f5fc4', b: '#1f3f8a', c: '#d8dde6', d: '#e23a3a' } },
      desc: 'speed +100% for 20s. direction: negotiable.', effect: { speed: 2, secs: 20, scramble: 0.2 } },
    { id: 'green-tea',     name: 'Green Tea',     price: 160, where: 'vending', category: 'drink', energy: 15,
      icon: { shape: 'bottle', colors: { a: '#8fcf5a', b: '#5f9a35', c: '#f3f7e6', d: '#2f7a2f' } },
      desc: 'calm. speed +20% for 60s, and it settles a wobbly drink.', effect: { speed: 1.2, secs: 60 } },
    { id: 'canned-coffee', name: 'Canned Coffee', price: 220, where: 'vending', category: 'drink', energy: 20,
      icon: { shape: 'can-short', colors: { a: '#8a5630', b: '#5c371d', c: '#f1dfb0', d: '#8a5630' } },
      desc: 'the long haul: speed +30% and 5s more on the work clock, for 90s.', effect: { speed: 1.3, secs: 90, focus: 5 } },
    { id: 'ramune',        name: 'Ramune',        price: 240, where: 'counter', category: 'drink', energy: 20,
      icon: { shape: 'ramune', colors: { a: '#9fe3f2', b: '#5fb5cc', c: '#2a7fd0', d: '#ffffff' } },
      desc: 'steady hands: fishing strike window +80% for 2 min.', effect: { fishWindow: 1.8, secs: 120 } },
    { id: 'highball',      name: 'Highball',      price: 500, where: 'izakaya', category: 'drink', energy: 5,
      icon: { shape: 'glass', colors: { a: '#e9b44c', b: '#c48a2a', c: '#fff6da', d: '#f5e04a' } },
      desc: 'speed +60% for 40s. a little wobbly.', effect: { speed: 1.6, secs: 40, scramble: 0.1 } },
    { id: 'nama-beer',     name: 'Nama Beer',     price: 600, where: 'izakaya', category: 'drink', energy: 5,
      icon: { shape: 'mug', colors: { a: '#f2b632', b: '#c98a14' } },
      desc: 'start the nomikai showdown 8 gulps ahead (Bailey keeps pace). 90s.', effect: { headStart: 8, secs: 90 } },
    // --- food ---
    { id: 'onigiri',       name: 'Onigiri',       price: 180, where: 'counter', category: 'food', energy: 45,
      icon: { shape: 'onigiri', colors: { a: '#1f3327' } },
      desc: 'tuna mayo. fish bite twice as fast for 2 min.', effect: { fishBite: 0.5, secs: 120 } },
    { id: 'melon-pan',     name: 'Melon Pan',     price: 250, where: 'counter', category: 'food', energy: 40,
      icon: { shape: 'bun', colors: { a: '#f0d27a', b: '#c99a3c', d: '#b5802c' } },
      desc: 'lucky crumbs: no old boots, double the rare fish. 2 min.', effect: { fishLuck: 2, secs: 120 } },
    { id: 'nikuman',       name: 'Nikuman',       price: 320, where: 'counter', category: 'food', energy: 60,
      icon: { shape: 'nikuman', colors: { a: '#e6dcc8', b: '#cbbfa8' } },
      desc: 'warm and filling: speed +15% for 2 min, on top of any drink.', effect: { speed: 1.15, secs: 120 } },
    { id: 'edamame',       name: 'Edamame',       price: 280, where: 'izakaya', category: 'food', energy: 30,
      icon: { shape: 'pods', colors: { a: '#7cc24a', b: '#4f8a2c' } },
      desc: 'soaks it up: drinks cannot make you wobble for 2 min.', effect: { steady: true, secs: 120 } },
    { id: 'karaage',       name: 'Karaage',       price: 450, where: 'izakaya', category: 'food', energy: 60,
      icon: { shape: 'nuggets', colors: { a: '#c9772e', b: '#8f4d1a', c: '#eaa85a' } },
      desc: 'fried courage: nomikai showdown winnings +50% for 3 min.', effect: { prizeBonus: 1.5, secs: 180 } },
    // --- gear ---
    { id: 'fishing-rod',   name: 'Fishing Rod',   price: 1200, where: 'counter', category: 'gear',
      icon: { shape: 'rod', colors: { a: '#c98f4a', b: '#7a4a22', d: '#e23a3a' } },
      desc: 'bump into any pond to cast. reusable forever.', permanent: true },
];

if (typeof window !== 'undefined') window.Shop = Shop;
