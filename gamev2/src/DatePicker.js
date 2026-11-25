/**
 * DatePicker — in-game pixel-style calendar for time travel.
 *
 * The world renders as of a chosen date (NPC dated states — see
 * src/utils/NpcStates.js). This overlay lets the player pick that date
 * without leaving the game: open it from the menu ("Time Travel") or by
 * clicking the HUD date. Picking a day reloads at ?date=YYYY-MM-DD
 * (picking the day a clean URL already shows returns to the clean URL).
 *
 * Keys while open: arrows/WASD move a day (left-right) or a week (up-down),
 * ENTER/SPACE travels, ESC closes. Everything is also clickable (day cells,
 * month arrows).
 *
 * Trips (config.trips, src/utils/Trips.js): a trip's own days are underlined
 * in the grid, the row under the grid names each trip — the one the
 * selected day is on is lit — and a click on a name, or SHIFT with
 * left/right, jumps the selection to that trip's first day with posts
 * (Trips.jump), so two trips fifteen months apart are one press away.
 *
 * Three days are marked, and they are rarely the same one: the real today
 * (gold), the day the game is on (blue — outside a trip that is a trip
 * day, a year or more of months away from today; see defaultGameDate) and
 * the cursor (green box). The legend (DatePicker.legend) only names a colour
 * that is on the month being shown, and the jump row under the selected date — each button
 * in the colour of its day — moves the cursor straight to today or to the
 * game's day: click / tap one, or SHIFT with up (today) / down (the game's
 * day) (issue #98).
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
            a: K.A, d: K.D, w: K.W, s: K.S,
            enter: K.ENTER, space: K.SPACE, esc: K.ESC, shift: K.SHIFT,
        });
    }

    isVisible() { return this.visible; }

    show() {
        if (this.visible || this.scene.isTransitioning) return;
        // swallow the keypress that opened us (menu ENTER/SPACE) so it
        // doesn't immediately confirm inside the picker
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.space); JD(this.keys.esc);
        const [y, m, d] = gameDate().split('-').map(Number);
        this.sel = new Date(y, m - 1, d);
        this.contentDates = contentChangeDates(this.scene.config);
        this.trips = Trips.of(this.scene.config);
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

    /** Select a day by ISO date. */
    select(iso) {
        const [y, m, d] = iso.split('-').map(Number);
        this.sel = new Date(y, m - 1, d);
        this.rerender();
    }

    /** Jump to the next (1) / previous (-1) trip's landing day, if there is one that way. */
    jumpTrip(dir) {
        const to = Trips.jump(this.trips, this.iso(this.sel), dir, [...this.contentDates]);
        if (to) this.select(to);
    }

    /**
     * The jump row's days, as [label, iso, colour]: the real today, and the
     * day the game is on when that is another day.
     */
    jumps() {
        const today = this.iso(new Date()), live = gameDate();
        const jumps = [['today', today, DatePicker.TODAY]];
        if (live !== today) jumps.push(['you are here', live, DatePicker.LIVE]);
        return jumps;
    }

    /** Jump to the first (0: today) or second (1: the game's day) of the jump row's days. */
    jumpTo(i) {
        const jumps = this.jumps();
        this.select((jumps[i] || jumps[0])[1]);
    }

    confirm() {
        const target = this.iso(this.sel);
        this.hide();
        setGameDate(target);   // navigates; the default date -> clean URL
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
        if (JD(k.enter) || JD(k.space)) return this.confirm();
        const left = JD(k.left) || JD(k.a), right = JD(k.right) || JD(k.d);
        const up = JD(k.up) || JD(k.w), down = JD(k.down) || JD(k.s);
        if (k.shift.isDown && (left || right)) return this.jumpTrip(left ? -1 : 1);
        if (k.shift.isDown && (up || down)) return this.jumpTo(up ? 0 : 1);
        if (left) return this.moveDays(-1);
        if (right) return this.moveDays(1);
        if (up) return this.moveDays(-7);
        if (down) return this.moveDays(7);
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        // the trips row (when the config has trips) makes the panel one row taller
        const tripRow = this.trips.length ? 34 : 0;
        const pw = 480, ph = 500 + tripRow, px = (W - pw) / 2, py = (H - ph) / 2;
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
            if (this.trips.some(t => Trips.during(t, dIso))) {
                // a trip day: underlined, post or no post
                marks.fillStyle(0x4d79a8, 1);
                marks.fillRect(cxp - cw / 2 + 6, cyp + ch / 2 - 3, cw - 12, 2);
            }
            if (this.contentDates.has(dIso)) {
                marks.fillStyle(0x33cc66, 1);
                marks.fillRect(cxp - 2, cyp + 13, 4, 4);
            }
            let color = '#ffffff';
            if (dIso === todayIso) color = DatePicker.TODAY;
            else if (dIso === liveIso) color = DatePicker.LIVE;
            const t = text(cxp, cyp, String(day), '18px', dIso === todayIso || dIso === liveIso, color);
            t.setInteractive({ useHandCursor: true });
            t.on('pointerdown', () => { this.sel = new Date(year, month, day); this.confirm(); });
            this.dayCells.push(t);
        }

        if (tripRow) this.renderTrips(text, cx, py + ph - 108 - tripRow, selIso);
        text(cx, py + ph - 108, `viewing: ${formatGameDate(selIso)}`, '18px', true, '#33cc66');

        // jump row: each button wears the colour its day has on the grid
        const row = this.jumps().map(([label, iso, color]) => {
            const b = text(0, py + ph - 80, `[ ${label} ]`, '16px', true, color, 0);
            b.setInteractive({ useHandCursor: true });
            b.on('pointerdown', () => this.select(iso));
            return b;
        });
        row.push(text(0, py + ph - 80, Hints.text(scene, 'SHIFT + ↑/↓'), '16px', false, '#888888', 0));
        const gap = 10;
        let x = cx - (row.reduce((w, o) => w + o.width, 0) + gap * (row.length - 1)) / 2;
        for (const o of row) { o.setX(Math.round(x)); x += o.width + gap; }

        // the legend names only the colours that are on this month
        const inView = (iso) => iso.slice(0, 7) === selIso.slice(0, 7);
        const [marksLine, keysLine] = DatePicker.legend(this.trips.length > 0,
            { today: inView(todayIso), live: liveIso !== todayIso && inView(liveIso) });
        text(cx, py + ph - 52, marksLine, '16px', false, '#888888');
        text(cx, py + ph - 26, Hints.text(scene, keysLine), '16px', false, '#888888');
    }

    /**
     * The two legend lines under the grid: what the marks on a day mean
     * (the underline only when the config has trips to underline), then the
     * keys. Each has to fit the 480px panel — 52 characters at 16px.
     *
     * `shown` says which coloured days are on the month in view — `today`
     * (gold) and `live` (blue: the day the game is on, when that is not
     * today) — and only those are named: "gold = today" under a month a
     * year away from today explains nothing (issue #98). Left out, today is
     * taken to be in view. A line that would be too long is worded shorter.
     */
    static legend(hasTrips, shown) {
        const { today, live } = shown || { today: true, live: false };
        const marks = (dot, underline, blue) => [dot]
            .concat(hasTrips ? [underline] : [], live ? [blue] : [], today ? ['gold = today'] : [])
            .join(' · ');
        const wordings = [
            ['dot = blog post', 'underline = trip', 'blue = you are here'],
            ['dot = post', 'underline = trip', 'blue = you are here'],
            ['dot = post', 'underline = trip', 'blue = you'],
            ['dot = post', 'line = trip', 'blue = you'],
        ].map(w => marks(...w));
        return [
            wordings.find(line => line.length <= DatePicker.LEGEND_CHARS) || wordings[wordings.length - 1],
            'arrows: day/week · ENTER/click: travel · ESC: close',
        ];
    }

    /**
     * The trips row: every trip by name, underlined like its days in the
     * grid, the one the selected day belongs to lit (gold on one of its own
     * days, white on the days after it). A click / tap on a name jumps to
     * that trip; the hint at the end is the keyboard / touch way to do the
     * same.
     */
    renderTrips(text, cx, y, selIso) {
        const mine = Trips.forDate(this.trips, selIso);
        const labels = this.trips.map(t => t.name);
        const hint = Hints.text(this.scene, 'SHIFT + ←/→');
        // monospace: lay the row out by character count, centred
        const cw = 9.9, gap = 3;
        const total = labels.reduce((n, l) => n + l.length + gap, 0) + hint.length;
        let x = cx - (total * cw) / 2;
        const rule = this.scene.add.graphics();
        rule.setScrollFactor(0); rule.setDepth(2002); this.objs.push(rule);
        rule.fillStyle(0x4d79a8, 1);
        this.trips.forEach((trip, i) => {
            const on = trip === mine;
            const color = !on ? '#88ccff' : Trips.during(trip, selIso) ? '#ffd700' : '#ffffff';
            const t = text(x, y, labels[i], '18px', on, color, 0);
            t.setInteractive({ useHandCursor: true });
            t.on('pointerdown', () => this.select(
                trip === Trips.forDate(this.trips, gameDate()) && Trips.during(trip, gameDate())
                    ? gameDate() : Trips.landing(this.trips, trip, [...this.contentDates])));
            rule.fillRect(Math.round(x), y + 12, Math.round(t.width), 2);
            x += (labels[i].length + gap) * cw;
        });
        text(x, y, hint, '16px', false, '#888888', 0);
    }
}

/** Day-number colours: the real today, and the day the game is on. */
DatePicker.TODAY = '#ffd700';
DatePicker.LIVE = '#88ccff';
/** Characters of 16px PixelOperatorMono (8.8px each) that fit the 480px panel with a margin. */
DatePicker.LEGEND_CHARS = 52;
