/**
 * DatePicker — in-game pixel-style calendar for time travel.
 *
 * The world renders as of a chosen date (NPC dated states — see
 * src/utils/NpcStates.js). This overlay lets the player pick that date
 * without leaving the game: open it from the menu ("Time Travel"), the T key,
 * or by clicking the HUD date. Picking a day reloads at ?date=YYYY-MM-DD
 * (picking today returns to the clean live URL).
 *
 * Keys while open: arrows move a day/week, , / . change month, T jumps to
 * today, ENTER travels, ESC closes. Everything is also clickable.
 */
class DatePicker {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.dayCells = [];
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({
            left: K.LEFT, right: K.RIGHT, up: K.UP, down: K.DOWN,
            enter: K.ENTER, esc: K.ESC, t: K.T,
            prevMonth: K.COMMA, nextMonth: K.PERIOD,
        });
    }

    isVisible() { return this.visible; }

    show() {
        if (this.visible || this.scene.isTransitioning) return;
        // swallow the keypress that opened us (menu ENTER / gameplay T) so it
        // doesn't immediately confirm or jump inside the picker
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.t); JD(this.keys.esc);
        const [y, m, d] = gameDate().split('-').map(Number);
        this.sel = new Date(y, m - 1, d);
        this.contentDates = contentChangeDates(this.scene.config);
        this.visible = true;
        this.render();
    }

    hide() {
        this.visible = false;
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.dayCells = [];
    }

    iso(date) {
        return date.getFullYear() + '-' +
            String(date.getMonth() + 1).padStart(2, '0') + '-' +
            String(date.getDate()).padStart(2, '0');
    }

    moveDays(n) {
        this.sel = new Date(this.sel.getFullYear(), this.sel.getMonth(), this.sel.getDate() + n);
        this.rerender();
    }

    moveMonth(n) {
        const day = this.sel.getDate();
        const first = new Date(this.sel.getFullYear(), this.sel.getMonth() + n, 1);
        const last = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
        this.sel = new Date(first.getFullYear(), first.getMonth(), Math.min(day, last));
        this.rerender();
    }

    confirm() {
        const target = this.iso(this.sel);
        this.hide();
        setGameDate(target);   // navigates; today -> clean URL
    }

    rerender() {
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.dayCells = [];
        this.render();
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter)) return this.confirm();
        if (JD(k.t)) { this.sel = new Date(); this.rerender(); return; }
        if (JD(k.left)) return this.moveDays(-1);
        if (JD(k.right)) return this.moveDays(1);
        if (JD(k.up)) return this.moveDays(-7);
        if (JD(k.down)) return this.moveDays(7);
        if (JD(k.prevMonth)) return this.moveMonth(-1);
        if (JD(k.nextMonth)) return this.moveMonth(1);
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const pw = 480, ph = 470, px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = this.objs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.85); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.hide());
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001);
        // swallow clicks on the panel so they don't hit the close-overlay
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (x, yy, t, size, bold, color, origin) => {
            const o = scene.add.text(x, yy, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(origin != null ? origin : 0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };

        const cx = W / 2;
        text(cx, py + 30, 'TIME TRAVEL', '32px', true);

        // month header with clickable arrows
        const monthName = this.sel.toLocaleString('en', { month: 'long' });
        text(cx, py + 72, `${monthName} ${this.sel.getFullYear()}`, '24px', true);
        const mkArrow = (x, label, n) => {
            const a = text(x, py + 72, label, '26px', true, '#88ccff');
            a.setInteractive({ useHandCursor: true });
            a.on('pointerdown', () => this.moveMonth(n));
        };
        mkArrow(px + 60, '<', -1);
        mkArrow(px + pw - 60, '>', 1);

        // weekday header
        const gridX = px + 44, gridY = py + 108, cw = 56, ch = 42;
        ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].forEach((wd, i) =>
            text(gridX + i * cw + cw / 2, gridY, wd, '16px', true, '#bbbbbb'));

        // day grid
        const year = this.sel.getFullYear(), month = this.sel.getMonth();
        const firstDow = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const todayIso = this.iso(new Date());
        const selIso = this.iso(this.sel);
        const liveIso = gameDate();
        const marks = scene.add.graphics();
        marks.setScrollFactor(0); marks.setDepth(2001); objs.push(marks);
        for (let day = 1; day <= daysInMonth; day++) {
            const cell = firstDow + day - 1;
            const cxp = gridX + (cell % 7) * cw + cw / 2;
            const cyp = gridY + 26 + Math.floor(cell / 7) * ch + ch / 2;
            const dIso = this.iso(new Date(year, month, day));
            if (dIso === selIso) {
                marks.fillStyle(0x2a4d2a, 1);
                marks.fillRect(cxp - cw / 2 + 3, cyp - ch / 2 + 3, cw - 6, ch - 6);
                marks.lineStyle(2, 0x33cc66, 1);
                marks.strokeRect(cxp - cw / 2 + 3, cyp - ch / 2 + 3, cw - 6, ch - 6);
            }
            if (this.contentDates.has(dIso)) {
                marks.fillStyle(0x33cc66, 1);
                marks.fillRect(cxp - 2, cyp + 13, 4, 4);
            }
            let color = '#ffffff';
            if (dIso === todayIso) color = '#ffd700';
            else if (dIso === liveIso) color = '#88ccff';
            const t = text(cxp, cyp, String(day), '18px', dIso === todayIso, color);
            t.setInteractive({ useHandCursor: true });
            t.on('pointerdown', () => { this.sel = new Date(year, month, day); this.confirm(); });
            this.dayCells.push(t);
        }

        text(cx, py + ph - 78, `viewing: ${formatGameDate(selIso)}`, '18px', true, '#33cc66');
        text(cx, py + ph - 50, 'dot = blog post · gold = today · arrows: day/week', '16px', false, '#888888');
        text(cx, py + ph - 26, 'ENTER/click: travel · T: today · ESC: close', '16px', false, '#888888');
    }
}
