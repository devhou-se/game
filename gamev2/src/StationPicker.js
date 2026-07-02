/**
 * StationPicker — the destination board. Opens when the player walks up to
 * the train (a board cell in a station room, see config `stations`); pick a
 * station and TrainTravel runs the ride. Same overlay idiom as the menu /
 * date picker: arrows + ENTER, ESC steps away, rows are clickable.
 */
class StationPicker {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.rows = [];
        this.selected = 0;
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ up: K.UP, down: K.DOWN, enter: K.ENTER, esc: K.ESC });
    }

    isVisible() { return this.visible; }

    show(fromKey) {
        if (this.visible) return;
        const stations = this.scene.config.stations || {};
        this.dests = Object.keys(stations).filter(k => k !== fromKey);
        if (!this.dests.length) return;
        this.fromKey = fromKey;
        this.selected = 0;
        // swallow the keypress that got us here
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.esc);
        this.visible = true;
        this.render();
    }

    hide() {
        this.visible = false;
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.rows = [];
    }

    confirm() {
        const dest = this.dests[this.selected];
        this.hide();
        this.scene.trainTravel.go(this.fromKey, dest);
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter)) return this.confirm();
        if (JD(k.up)) { this.selected = (this.selected - 1 + this.dests.length) % this.dests.length; this.paint(); }
        if (JD(k.down)) { this.selected = (this.selected + 1) % this.dests.length; this.paint(); }
    }

    paint() {
        this.rows.forEach((r, i) => r.setFill(i === this.selected ? '#ffff00' : '#ffffff'));
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const stations = scene.config.stations;
        const ph = 150 + this.dests.length * 40, pw = 460;
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

        const text = (x, y, t, size, bold, color) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };
        text(W / 2, py + 32, 'DEPARTURES', '26px', true);
        text(W / 2, py + 62, `from ${stations[this.fromKey].label}`, '14px', false, '#888888');

        this.rows = this.dests.map((key, i) => {
            const row = text(W / 2, py + 100 + i * 40, `▶ ${stations[key].label}`, '20px', true);
            row.setInteractive({ useHandCursor: true });
            row.on('pointerdown', () => { this.selected = i; this.confirm(); });
            return row;
        });
        this.paint();
        text(W / 2, py + ph - 24, '↑/↓ + ENTER: board · ESC: step back', '12px', false, '#888888');
    }
}
