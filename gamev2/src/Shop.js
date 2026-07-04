/**
 * Shop — money + inventory (issue #12).
 *
 * The player has a yen wallet and an inventory, both persisted in
 * localStorage. Bumping into a vending machine (any map) opens its drink
 * menu; bumping the counter inside a konbini opens the full store. Bought
 * items live in the inventory (menu → Items, or click the ¥ in the HUD) and
 * are used from there — drinks give temporary movement effects, food is
 * flavour. Same overlay idiom as the station picker: arrows + ENTER, ESC,
 * rows clickable.
 */
class Shop {
    constructor(scene) {
        this.scene = scene;
        this.STORE_KEY = 'gamev2_shop';
        this.visible = false;      // buy overlay
        this.invVisible = false;   // inventory overlay
        this.objs = [];
        this.rows = [];
        this.selected = 0;
        this.effect = null;        // { speed, scramble, until }

        const cfg = scene.config.shop || {};
        this.catalogue = cfg.items || Shop.DEFAULT_ITEMS;
        this.startingMoney = cfg.startingMoney != null ? cfg.startingMoney : 5000;

        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ up: K.UP, down: K.DOWN, enter: K.ENTER, esc: K.ESC });

        this.load();

        // active-effect chip in the HUD (left of the menu button), with a
        // live countdown while a drink is working
        this.effectText = scene.add.text(scene.cameras.main.width - 100, 20, '', {
            fontSize: '16px', fill: '#66ff88', fontFamily: 'PressStart2P',
        });
        this.effectText.setOrigin(1, 0.5);
        this.effectText.setScrollFactor(0);
        this.effectText.setDepth(1001);
        this.effectText.setResolution(1);
        this.effectText.setVisible(false);
        scene.time.addEvent({ delay: 250, loop: true, callback: () => this.updateEffectChip() });
    }

    updateEffectChip() {
        const fx = this.movementModifier();
        if (!fx) { this.effectText.setVisible(false); return; }
        const secs = Math.max(0, Math.ceil((fx.until - Date.now()) / 1000));
        this.effectText.setText(`${fx.name} ${secs}s`);
        this.effectText.setVisible(true);
    }

    // ---------------- state ----------------

    load() {
        let raw = {};
        try { raw = JSON.parse(localStorage.getItem(this.STORE_KEY) || '{}'); } catch (e) { /* fresh */ }
        this.money = typeof raw.money === 'number' ? raw.money : this.startingMoney;
        this.items = raw.items || {};   // id -> count
    }

    save() {
        try { localStorage.setItem(this.STORE_KEY, JSON.stringify({ money: this.money, items: this.items })); }
        catch (e) { /* private mode etc — play on without persistence */ }
    }

    fmt(n) { return '¥' + n.toLocaleString(); }

    itemById(id) { return this.catalogue.find(i => i.id === id); }

    // ---------------- world interaction ----------------

    /**
     * The player bumped a blocked cell — if it's a vending machine (anywhere)
     * or a counter (konbini interiors), open the matching store. Matching is
     * footprint-aware: a multi-cell sprite (the 3-wide counter, a machine
     * whose art extends past its anchor cell) opens from ANY of its cells,
     * so every side of the desk works.
     */
    checkShopInteraction(gridX, gridY) {
        if (this.visible || this.invVisible) return;
        const roomKey = this.scene.roomManager.currentRoom;
        const room = this.scene.roomManager.rooms[roomKey];
        const interior = !!(this.scene.config.rooms[roomKey] || {}).interior;
        for (const layer of (room.layers || [])) {
            for (const xy in (layer.tiles || {})) {
                const key = layer.tiles[xy];
                const vending = /vending-machine/.test(key);
                const counter = interior && /^(blue-shrine-platform-base|office-counter)/.test(key);
                if (!vending && !counter) continue;
                const [tx, ty] = xy.split(',').map(Number);
                const tex = this.scene.textures.exists(key)
                    ? this.scene.textures.get(key).getSourceImage() : null;
                const w = tex ? Math.max(1, Math.round(tex.width / 64)) : 1;
                const h = tex ? Math.max(1, Math.round(tex.height / 64)) : 1;
                if (gridX >= tx && gridX < tx + w && gridY >= ty && gridY < ty + h) {
                    return this.showShop(vending ? 'vending' : 'counter');
                }
            }
        }
    }

    // ---------------- movement effects ----------------

    /** Active drink effect, or null. Applied by InputHandler on each step. */
    movementModifier() {
        if (this.effect && Date.now() > this.effect.until) this.effect = null;
        return this.effect;
    }

    use(id) {
        if (!this.items[id]) return;
        const item = this.itemById(id);
        if (!item) return;
        if (item.permanent) return this.toast(`${item.name}: ${item.desc}`);
        this.items[id]--;
        if (!this.items[id]) delete this.items[id];
        if (item.effect) {
            this.effect = {
                name: item.name,
                speed: item.effect.speed || 1,
                scramble: item.effect.scramble || 0,
                until: Date.now() + (item.effect.secs || 0) * 1000,
            };
            this.updateEffectChip();
        }
        this.toast(`${item.name}: ${item.desc}`);
        this.save();

        // a little "gulp": the player pops and glows for a beat
        const p = this.scene.player.sprite;
        const baseScale = p.scale;
        p.setTint(0xaaffcc);
        this.scene.tweens.add({
            targets: p, scale: { from: baseScale * 1.35, to: baseScale },
            duration: 280, ease: 'Back.easeOut',
            onComplete: () => p.clearTint(),
        });
    }

    // ---------------- buy overlay ----------------

    isVisible() { return this.visible || this.invVisible; }

    showShop(kind) {
        if (this.isVisible()) return;
        this.kind = kind;
        this.stock = kind === 'vending'
            ? this.catalogue.filter(i => i.where === 'vending')
            : this.catalogue;   // the konbini counter sells everything
        if (!this.stock.length) return;
        this.selected = 0;
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.esc);   // swallow the bump keypress
        this.visible = true;
        this.render();
    }

    buy() {
        const item = this.stock[this.selected];
        if (!item) return;
        if (item.permanent && this.items[item.id]) return this.toast('you already have one');
        if (this.money < item.price) return this.toast('not enough yen...');
        this.money -= item.price;
        this.items[item.id] = (this.items[item.id] || 0) + 1;
        this.save();
        this.scene.updateHUD();
        this.toast(`bought ${item.name} — it's in your items (menu)`);
        this.repaint();
    }

    // ---------------- inventory overlay ----------------

    showInventory() {
        if (this.isVisible()) return;
        this.stock = Object.keys(this.items).map(id => this.itemById(id)).filter(Boolean);
        this.selected = 0;
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.esc);
        this.invVisible = true;
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
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter)) return this.visible ? this.buy() : this.useSelected();
        if (!this.stock.length) return;
        if (JD(k.up)) { this.selected = (this.selected - 1 + this.stock.length) % this.stock.length; this.paint(); }
        if (JD(k.down)) { this.selected = (this.selected + 1) % this.stock.length; this.paint(); }
    }

    repaint() {
        // cheap full re-render: money, counts and the stock list all shift
        const wasShop = this.visible, wasInv = this.invVisible;
        this.hide();
        this.visible = wasShop;
        this.invVisible = wasInv;
        this.render();
    }

    paint() {
        this.rows.forEach((r, i) => r.setFill(i === this.selected ? '#ffff00' : '#ffffff'));
        if (this.descText && this.stock[this.selected]) this.descText.setText(this.stock[this.selected].desc);
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const inv = this.invVisible;
        const n = Math.max(1, this.stock.length);
        const pw = 600, ph = 210 + n * 44;
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

        const title = inv ? 'ITEMS' : (this.kind === 'vending' ? 'VENDING MACHINE' : 'KONBINI');
        text(W / 2, py + 34, title, '32px', true);
        text(px + pw - 18, py + 34, this.fmt(this.money), '24px', true, '#ffd700', 1);

        if (!this.stock.length) {
            text(W / 2, py + 108, 'nothing yet — find a vending machine', '20px', false, '#888888');
        }

        this.rows = this.stock.map((item, i) => {
            const y = py + 92 + i * 44;
            const label = inv
                ? `${item.name}  ×${this.items[item.id] || 0}`
                : `${item.name}`;
            const row = text(px + 30, y, label, '24px', true, '#ffffff', 0);
            if (!inv) text(px + pw - 30, y, this.fmt(item.price), '24px', false,
                           this.money >= item.price ? '#ffffff' : '#886666', 1);
            row.setInteractive({ useHandCursor: true });
            row.on('pointerover', () => { this.selected = i; this.paint(); });
            row.on('pointerdown', () => { this.selected = i; inv ? this.useSelected() : this.buy(); });
            return row;
        });

        this.descText = text(W / 2, py + ph - 62, '', '18px', false, '#9999aa');
        this.paint();
        const hint = inv ? '↑/↓ + ENTER: use · ESC: close'
                         : '↑/↓ + ENTER: buy · ESC: step away';
        text(W / 2, py + ph - 28, hint, '16px', false, '#888888');
    }

    // ---------------- toast ----------------

    toast(msg) {
        if (this._toast) this._toast.destroy();
        const cam = this.scene.cameras.main;
        const o = this.scene.add.text(cam.width / 2, cam.height - 80, msg, {
            fontSize: '20px', fill: '#ffffff', fontFamily: 'PixelOperatorMonoBold',
            backgroundColor: 'rgba(0,0,0,0.75)', padding: { x: 10, y: 6 },
        });
        o.setOrigin(0.5, 0.5); o.setResolution(1);
        o.setScrollFactor(0); o.setDepth(3500);
        this._toast = o;
        this.scene.tweens.add({
            targets: o, alpha: 0, delay: 1800, duration: 400,
            onComplete: () => { if (this._toast === o) this._toast = null; o.destroy(); },
        });
    }
}

/** Starter catalogue (issue #12's examples). config.json `shop.items` overrides. */
Shop.DEFAULT_ITEMS = [
    { id: 'zone-energy',   name: 'Zone Energy',   price: 300, where: 'vending',
      desc: 'speed +50% for 30s', effect: { speed: 1.5, secs: 30 } },
    { id: 'vodka-redbull', name: 'Vodka Redbull', price: 800, where: 'vending',
      desc: 'speed +100% for 20s. direction: negotiable.', effect: { speed: 2, secs: 20, scramble: 0.2 } },
    { id: 'green-tea',     name: 'Green Tea',     price: 160, where: 'vending',
      desc: 'calm. refreshing. does absolutely nothing.' },
    { id: 'onigiri',       name: 'Onigiri',       price: 180, where: 'counter',
      desc: 'tuna mayo. restores the will to keep walking.' },
    { id: 'melon-pan',     name: 'Melon Pan',     price: 250, where: 'counter',
      desc: 'neither melon nor pan. perfect.' },
    { id: 'fishing-rod',   name: 'Fishing Rod',   price: 1200, where: 'counter',
      desc: 'bump into any pond to cast. reusable forever.', permanent: true },
];

if (typeof window !== 'undefined') window.Shop = Shop;
