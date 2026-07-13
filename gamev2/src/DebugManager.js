/**
 * DebugManager - hidden debug menu + in-game debug overlay + issue flagging.
 *
 * Everything here is deliberately undocumented in the controls overlay.
 * Triple-press the backtick key ( ``` within a second ) to open the debug
 * menu: W/S select, SPACE toggles, ESC closes. Toggles (persisted in
 * localStorage, so they survive the frequent date-travel reloads):
 *  - grid view + inspector: stats panel (FPS, player cell + depth, room),
 *    collidable cells tinted red, clicking any cell lists every tile there
 *  - flag keys N/E/X: with the grid view on, click a cell then press N to
 *    add/edit a note (flagged cells tint yellow and persist), E to export
 *    all flags as CSV, X to clear them
 *  - map click travel: clicking the menu's Map overlay teleports to the
 *    nearest walkable cell (off by default — the map is a viewer otherwise)
 *  - time of day: pin the day/night cycle to day/dusk/night/dawn (same as
 *    the ?tod= URL override, which wins on load), or AUTO for the real clock
 *  - wallet: set the shop wallet to an exact yen amount (prompt)
 *  - noclip: the player walks through tiles/objects/NPCs (room bounds still
 *    apply); bump interactions can't fire while it's on
 */
class DebugManager {
    constructor(scene) {
        this.scene = scene;
        this.settings = this.loadSettings();  // { grid, flagKeys, mapTravel }
        this.visible = !!this.settings.grid;
        this.info = '(click a tile to inspect)';
        this.lastCell = null;                 // {x, y, room, tiles:[...]}
        this.flags = this.loadFlags();        // [{room, x, y, note, tiles:[...]}]

        // World-space overlay (collision tint + flag markers); scrolls with camera
        this.overlay = scene.add.graphics();
        this.overlay.setDepth(4000);

        // Per-flag note labels (world space); rebuilt when flags/room change
        this.flagLabels = [];
        this.labelsDirty = true;

        // Screen-space stats panel (fixed to camera)
        this.text = scene.add.text(8, 48, '', {
            fontSize: '14px',
            fill: '#00ff66',
            fontFamily: 'monospace',
            backgroundColor: 'rgba(0,0,0,0.7)',
            padding: { x: 6, y: 6 }
        });
        this.text.setScrollFactor(0);
        this.text.setDepth(4001);
        this.text.setResolution(1);
        this.text.setVisible(this.visible);

        // Hidden debug menu state
        this.menuVisible = false;
        this.menuObjs = [];
        this.menuRows = [];
        this.menuIndex = 0;
        this._backtickTimes = [];
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.menuKeys = scene.input.keyboard.addKeys({
            up: K.W, down: K.S, up2: K.UP, down2: K.DOWN,
            confirm: K.SPACE, confirm2: K.ENTER, esc: K.ESC,
        });

        scene.input.keyboard.on('keydown-BACKTICK', () => this.onBacktick());
        scene.input.keyboard.on('keydown-N', () => { if (this.flagKeysActive()) this.addNote(); });
        scene.input.keyboard.on('keydown-E', () => { if (this.flagKeysActive()) this.exportCSV(); });
        scene.input.keyboard.on('keydown-X', () => { if (this.flagKeysActive()) this.clearFlags(); });
        scene.input.on('pointerdown', (pointer) => {
            if (this.visible && !this.menuVisible) this.inspect(pointer);
        });

        // re-apply a persisted time-of-day pin (an explicit ?tod= URL
        // override wins for this load; DayNight is created just before us)
        if (this.settings.tod && scene.dayNight && !scene.dayNight.forced) {
            scene.dayNight.forced = this.settings.tod;
            scene.dayNight.apply();
        }
    }

    flagKeysActive() {
        return this.visible && this.settings.flagKeys && !this.menuVisible;
    }

    setGrid(on) {
        this.settings.grid = !!on;
        this.saveSettings();
        this.visible = this.settings.grid;
        this.text.setVisible(this.visible);
        this.labelsDirty = true;
        if (!this.visible) {
            this.overlay.clear();
            this.flagLabels.forEach(l => l.destroy());
            this.flagLabels = [];
        }
    }

    // ---- settings persistence ----
    loadSettings() {
        const defaults = { grid: false, flagKeys: false, mapTravel: false,
                           tod: null, noclip: false };
        try {
            return Object.assign(defaults,
                JSON.parse(localStorage.getItem('gamev2_debug_settings') || '{}'));
        } catch (e) { return defaults; }
    }
    saveSettings() {
        try { localStorage.setItem('gamev2_debug_settings', JSON.stringify(this.settings)); }
        catch (e) { /* ignore quota/availability */ }
    }

    // ---- the hidden debug menu (triple-backtick) ----
    onBacktick() {
        const now = Date.now();
        this._backtickTimes = this._backtickTimes.filter(t => now - t < 900);
        this._backtickTimes.push(now);
        if (this._backtickTimes.length >= 3) {
            this._backtickTimes = [];
            this.menuVisible ? this.closeMenu() : this.openMenu();
        }
    }

    menuItems() {
        const onOff = (v) => v ? 'ON' : 'OFF';
        const flip = (key) => () => { this.settings[key] = !this.settings[key]; this.saveSettings(); };
        return [
            { label: 'grid view + inspector',
              value: () => onOff(this.settings.grid),
              lit: () => this.settings.grid,
              activate: () => this.setGrid(!this.settings.grid) },
            { label: 'flag keys N/E/X',
              value: () => onOff(this.settings.flagKeys),
              lit: () => this.settings.flagKeys,
              activate: flip('flagKeys') },
            { label: 'map click travel',
              value: () => onOff(this.settings.mapTravel),
              lit: () => this.settings.mapTravel,
              activate: flip('mapTravel') },
            { label: 'time of day',
              value: () => (this.settings.tod || 'auto').toUpperCase(),
              lit: () => !!this.settings.tod,
              activate: () => this.cycleTod() },
            { label: 'wallet',
              value: () => this.scene.shop ? this.scene.shop.fmt(this.scene.shop.money) : '-',
              lit: () => false,
              activate: () => this.setWallet() },
            { label: 'noclip',
              value: () => onOff(this.settings.noclip),
              lit: () => this.settings.noclip,
              activate: flip('noclip') },
        ];
    }

    /** AUTO (real Tokyo clock) -> day -> dusk -> night -> dawn -> AUTO. */
    cycleTod() {
        const order = [null, 'day', 'dusk', 'night', 'dawn'];
        const next = order[(order.indexOf(this.settings.tod || null) + 1) % order.length];
        this.settings.tod = next;
        this.saveSettings();
        if (this.scene.dayNight) {
            this.scene.dayNight.forced = next;
            this.scene.dayNight.apply();
        }
    }

    /** Set the shop wallet to an exact amount via prompt. */
    setWallet() {
        const shop = this.scene.shop;
        if (!shop) return;
        const raw = window.prompt('Set wallet (¥):', shop.money);
        // the blocking prompt can swallow keyup events — unstick everything
        if (this.scene.input.keyboard.resetKeys) this.scene.input.keyboard.resetKeys();
        if (raw === null) return;
        const amount = parseInt(String(raw).replace(/[^\d]/g, ''), 10);
        if (isNaN(amount)) return;
        shop.money = Math.max(0, amount);
        shop.save();
        this.scene.updateHUD();
    }

    openMenu() {
        if (this.menuVisible) return;
        this.menuVisible = true;
        this.menuIndex = 0;
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const items = this.menuItems();
        const pw = 480, ph = 132 + items.length * 40, px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = this.menuObjs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.75); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(4100);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.closeMenu());
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x101418, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x00ff66, 0.8); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(4101);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (x, y, t, size, color) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: 'monospace' });
            o.setOrigin(0, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(4102); objs.push(o); return o;
        };
        const title = text(px + 24, py + 30, 'DEBUG MENU', '22px', '#00ff66');
        title.setFontStyle('bold');

        this.menuRows = items.map((item, i) => {
            const row = text(px + 24, py + 76 + i * 40, '', '18px');
            row.setInteractive({ useHandCursor: true });
            row.on('pointerover', () => { this.menuIndex = i; this.paintMenu(); });
            row.on('pointerdown', () => {
                this.menuIndex = i;
                item.activate();
                this.paintMenu();
            });
            return row;
        });
        text(px + 24, py + ph - 28, 'W/S select · SPACE change · ESC close', '14px', '#888888');
        this.paintMenu();
    }

    closeMenu() {
        this.menuVisible = false;
        this.menuObjs.forEach(o => o.destroy());
        this.menuObjs = [];
        this.menuRows = [];
    }

    paintMenu() {
        const items = this.menuItems();
        this.menuRows.forEach((row, i) => {
            const it = items[i];
            const sel = i === this.menuIndex;
            row.setText(`${sel ? '>' : ' '} ${it.label.padEnd(24)} [${it.value()}]`);
            row.setFill(sel ? '#ffff00' : (it.lit() ? '#00ff66' : '#dddddd'));
        });
    }

    /** Polled by InputHandler while the menu is open — it owns all input. */
    handleMenuInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.menuKeys;
        const items = this.menuItems();
        if (JD(k.esc)) return this.closeMenu();
        if (JD(k.confirm) || JD(k.confirm2)) {
            items[this.menuIndex].activate();
            return this.paintMenu();
        }
        if (JD(k.up) || JD(k.up2)) { this.menuIndex = (this.menuIndex - 1 + items.length) % items.length; this.paintMenu(); }
        if (JD(k.down) || JD(k.down2)) { this.menuIndex = (this.menuIndex + 1) % items.length; this.paintMenu(); }
    }

    // ---- flag persistence (localStorage so flags survive the frequent reloads) ----
    loadFlags() {
        try { return JSON.parse(localStorage.getItem('gamev2_debug_flags') || '[]'); }
        catch (e) { return []; }
    }
    saveFlags() {
        try { localStorage.setItem('gamev2_debug_flags', JSON.stringify(this.flags)); }
        catch (e) { /* ignore quota/availability */ }
        this.labelsDirty = true;
    }
    findFlag(room, x, y) {
        return this.flags.find(f => f.room === room && f.x === x && f.y === y);
    }

    /** List every tile occupying a cell, formatted like the inspector. */
    tilesAt(gx, gy) {
        const GS = this.scene.GRID_SIZE;
        const names = (this.scene.config && this.scene.config.tileNames) || {};
        const hits = [];
        this.scene.roomManager.floorSprites.forEach(t => {
            const tx = t.getData('gridX'), ty = t.getData('gridY');
            const fw = Math.max(1, Math.round(t.width / GS));
            const fh = Math.max(1, Math.round(t.height / GS));
            if (gx >= tx && gx < tx + fw && gy >= ty && gy < ty + fh) {
                const label = names[t.texture.key] || t.texture.key;
                const anchor = (tx === gx && ty === gy) ? '' : ` (@${tx},${ty})`;
                hits.push(`${label} z${t.getData('layerZ')} d${Math.round(t.depth)}${t.getData('layerCollision') ? ' [COLL]' : ''}${anchor}`);
            }
        });
        return hits;
    }

    /** List every tile occupying the clicked cell + remember it for flagging. */
    inspect(pointer) {
        const GS = this.scene.GRID_SIZE;
        const gx = Math.floor(pointer.worldX / GS);
        const gy = Math.floor(pointer.worldY / GS);
        const room = this.scene.roomManager.currentRoom;
        const hits = this.tilesAt(gx, gy);
        this.lastCell = { x: gx, y: gy, room, tiles: hits };
        const flag = this.findFlag(room, gx, gy);
        const noteLine = flag ? `\n>> NOTE: ${flag.note || '(flagged)'}` : '';
        this.info = `cell (${gx},${gy})\n` + (hits.length ? hits.join('\n') : '(empty)') + noteLine;
        console.log('[debug] cell', gx, gy, hits);
    }

    /** Add/edit a note on the last-inspected cell (turns it into a flag). */
    addNote() {
        if (!this.lastCell) { this.info = 'click a cell first, then press N'; return; }
        const { x, y, room, tiles } = this.lastCell;
        const existing = this.findFlag(room, x, y);
        const note = window.prompt(`Note for ${room} (${x},${y}):`, existing ? existing.note : '');
        if (note === null) return;   // cancelled
        if (existing) { existing.note = note; existing.tiles = tiles; }
        else { this.flags.push({ room, x, y, note, tiles }); }
        this.saveFlags();
        this.info = `flagged (${x},${y}): ${note || '(no note)'}`;
    }

    clearFlags() {
        if (!this.flags.length) return;
        if (!window.confirm(`Clear all ${this.flags.length} flags?`)) return;
        this.flags = [];
        this.saveFlags();
        this.info = 'flags cleared';
    }

    /** Export every flag as CSV and download it. */
    exportCSV() {
        if (!this.flags.length) { this.info = 'no flags to export'; return; }
        const esc = (v) => `"${String(v).replace(/"/g, '""')}"`;
        const rows = [['room', 'x', 'y', 'note', 'tiles'].join(',')];
        this.flags.forEach(f => {
            rows.push([esc(f.room), f.x, f.y, esc(f.note || ''), esc((f.tiles || []).join(' ; '))].join(','));
        });
        const csv = rows.join('\n');
        try {
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `gamev2_debug_flags_${Date.now()}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            this.info = `exported ${this.flags.length} flags to CSV`;
        } catch (e) {
            console.log('[debug] CSV:\n' + csv);
            this.info = 'export failed; CSV dumped to console';
        }
    }

    rebuildLabels() {
        this.flagLabels.forEach(l => l.destroy());
        this.flagLabels = [];
        if (!this.visible) return;
        const GS = this.scene.GRID_SIZE, room = this.scene.roomManager.currentRoom;
        this.flags.filter(f => f.room === room).forEach(f => {
            const label = this.scene.add.text(f.x * GS + 2, f.y * GS - 2, f.note || '(flag)', {
                fontSize: '12px', fill: '#ffff00', fontFamily: 'monospace',
                backgroundColor: 'rgba(0,0,0,0.75)', padding: { x: 2, y: 1 }
            });
            label.setOrigin(0, 1);
            label.setDepth(4002);
            label.setResolution(1);
            this.flagLabels.push(label);
        });
        this.labelsDirty = false;
    }

    update() {
        if (!this.visible) return;
        const s = this.scene, GS = s.GRID_SIZE, cam = s.cameras.main, p = s.player;
        const room = s.roomManager.currentRoom;
        const roomFlags = this.flags.filter(f => f.room === room).length;
        const recent = this.flags.slice(-4).map(f => `  ${f.room} ${f.x},${f.y}: ${f.note || '(flag)'}`).join('\n');
        this.text.setText([
            'DEBUG  ( ``` = menu | click = inspect )',
            this.settings.flagKeys ? 'N add/edit note   E export CSV   X clear'
                                   : '(flag keys off — enable in ``` menu)',
            `fps ${Math.round(s.game.loop.actualFps)}   room ${room}`,
            `player ${p.gridX},${p.gridY}  depth ${Math.round(p.sprite.depth)}`,
            `flags ${this.flags.length} total (${roomFlags} here)`,
            '',
            this.info,
            this.flags.length ? '\nrecent flags:\n' + recent : ''
        ].join('\n'));

        if (this.labelsDirty) this.rebuildLabels();

        // Redraw overlay: red = collidable cells, yellow = flagged cells.
        this.overlay.clear();
        const x0 = cam.scrollX, y0 = cam.scrollY, x1 = x0 + cam.width, y1 = y0 + cam.height;
        this.overlay.fillStyle(0xff0000, 0.3);
        this.overlay.lineStyle(1, 0xff0000, 0.5);
        s.roomManager.floorSprites.forEach(t => {
            if (!t.getData('layerCollision')) return;
            const px = t.getData('gridX') * GS, py = t.getData('gridY') * GS;
            if (px < x1 && px + GS > x0 && py < y1 && py + GS > y0) {
                this.overlay.fillRect(px, py, GS, GS);
                this.overlay.strokeRect(px, py, GS, GS);
            }
        });
        this.overlay.fillStyle(0xffff00, 0.35);
        this.overlay.lineStyle(2, 0xffff00, 0.9);
        this.flags.forEach(f => {
            if (f.room !== room) return;
            const px = f.x * GS, py = f.y * GS;
            if (px < x1 && px + GS > x0 && py < y1 && py + GS > y0) {
                this.overlay.fillRect(px, py, GS, GS);
                this.overlay.strokeRect(px, py, GS, GS);
            }
        });
    }
}
