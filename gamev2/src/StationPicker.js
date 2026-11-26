/**
 * StationPicker — the destination board. Opens when the player walks up to
 * the train (a board cell in a station room, see config `stations`); pick a
 * station and TrainTravel runs the ride. Same overlay idiom as the menu /
 * date picker: arrows/WASD + ENTER/SPACE, ESC steps away, rows are clickable.
 *
 * The board is laid out from data, not from the registry's key order (which
 * is alphabetical): `stations.<key>.order` places a station on the board and
 * `stations.<key>.parent` makes it a day trip, listed indented under its
 * parent city (both written by tools/generate_stations.py). `StationPicker
 * .board()` turns the registry into rows and picks the row to start on.
 *
 * At most MAX_VISIBLE rows show at once. A longer board scrolls: the
 * selection pulls the window along, the mouse wheel and the arrows at the top
 * and bottom of the list move it, and so does dragging the list (touch).
 * A pointer scroll that would leave the selection off screen moves it to the
 * nearest row in view. The unselectable "you are here" heading is a row like
 * any other, so it counts toward MAX_VISIBLE.
 */
class StationPicker {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.rows = [];      // the whole board, see board()
        this.slots = [];     // the MAX_VISIBLE-or-fewer rows on screen
        this.selected = 0;   // index into rows
        this.top = 0;        // index of the row in the first slot
        this.press = null;   // a press on a row: a tap picks it, a drag scrolls
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ up: K.UP, down: K.DOWN, w: K.W, s: K.S,
            enter: K.ENTER, space: K.SPACE, esc: K.ESC });
    }

    /**
     * The departures board at `fromKey`, as rows in display order:
     * `{ key, label, indent, here }`.
     *
     *  - cities (no `parent`) in `order`, each followed by its day trips, also
     *    in `order`, at indent 1. No `order` sorts last, then by label, so a
     *    registry without the fields still gives a stable board.
     *  - the station you are at is not a destination. It is left out, unless
     *    it has day trips: then it stays as their heading (`here: true`),
     *    which cannot be selected.
     *  - a `parent` that is unknown, itself, or itself a day trip is ignored
     *    (the station is listed as a city), so bad data cannot hide a station.
     *
     * `selected` is the row to start on: where you last arrived from
     * (`cameFrom`) if it is on the board, else the parent city of a day-trip
     * station, else the first destination. -1 when there is nowhere to go.
     */
    static board(stations, fromKey, cameFrom) {
        stations = stations || {};
        const keys = Object.keys(stations);
        const parentOf = (k) => {
            const p = stations[k].parent;
            return p && p !== k && stations[p] && !stations[p].parent ? p : null;
        };
        const rank = (k) => (Number.isFinite(stations[k].order) ? stations[k].order : Infinity);
        const label = (k) => String(stations[k].label || k);
        const byOrder = (a, b) => (rank(a) === rank(b) ? 0 : rank(a) - rank(b)) || label(a).localeCompare(label(b));

        const rows = [];
        for (const city of keys.filter(k => !parentOf(k)).sort(byOrder)) {
            const trips = keys.filter(k => parentOf(k) === city && k !== fromKey).sort(byOrder);
            if (city !== fromKey) rows.push({ key: city, label: label(city), indent: 0, here: false });
            else if (trips.length) rows.push({ key: city, label: label(city), indent: 0, here: true });
            for (const k of trips) rows.push({ key: k, label: label(k), indent: 1, here: false });
        }

        const at = (key) => (key ? rows.findIndex(r => r.key === key && !r.here) : -1);
        let selected = at(cameFrom);
        if (selected < 0 && stations[fromKey]) selected = at(parentOf(fromKey));
        if (selected < 0) selected = rows.findIndex(r => !r.here);
        return { rows, selected };
    }

    /** The next row that can be selected from `selected`, going `dir` (+1 / -1) and wrapping. */
    static step(rows, selected, dir) {
        for (let n = 1; n <= rows.length; n++) {
            const i = ((selected + dir * n) % rows.length + rows.length) % rows.length;
            if (!rows[i].here) return i;
        }
        return selected;
    }

    /**
     * The first row to show so that row `selected` is on screen, moving the
     * window as little as possible from `top`. A day trip that would be the
     * first row shown brings its city along (the row it is indented under,
     * however many sibling trips sit between), when both fit.
     */
    static scrollTop(top, selected, count, visible, rows) {
        const max = Math.max(0, count - visible);
        let t = Math.max(0, Math.min(top, max));
        if (selected <= t) {
            t = selected;
            let city = selected;
            while (rows && city > 0 && rows[city] && rows[city].indent) city--;
            if (selected - city < visible) t = city;
        }
        if (selected >= t + visible) t = selected - visible + 1;
        return Math.max(0, Math.min(t, max));
    }

    /**
     * The selection after the list was scrolled by pointer (wheel, arrows,
     * drag) to show rows `top`..`top + visible - 1`: unchanged if it is still
     * on screen, else the nearest row in view that can be selected - so the
     * cursor is never off screen and ENTER / A never boards a hidden row.
     */
    static clampSelection(rows, selected, top, visible) {
        const end = Math.min(rows.length, top + visible);
        if (selected >= top && selected < end) return selected;
        const dir = selected < top ? 1 : -1;
        for (let i = dir > 0 ? top : end - 1; i >= top && i < end; i += dir) {
            if (!rows[i].here) return i;
        }
        return selected;
    }

    isVisible() { return this.visible; }

    /** The registry the open board lists: the stations, or the airports (flight mode). */
    registry() {
        return this.flights ? AirTravel.registry(this.scene.config) : this.scene.config.stations;
    }

    /**
     * Open the board at `fromKey`. `opts.flights` makes it the airport's
     * board (issue #218): the same list and rules over config `airports`,
     * and picking a row flies (AirTravel) instead of riding.
     */
    show(fromKey, opts) {
        if (this.visible) return;
        const scene = this.scene;
        this.flights = !!(opts && opts.flights);
        const travel = this.flights ? scene.airTravel : scene.trainTravel;
        const cameFrom = travel ? travel.cameFrom(fromKey) : null;
        const board = StationPicker.board(this.registry(), fromKey, cameFrom);
        if (board.selected < 0) return;
        this.fromKey = fromKey;
        this.rows = board.rows;
        this.selected = board.selected;
        this.shown = Math.min(this.rows.length, StationPicker.MAX_VISIBLE);
        this.top = StationPicker.scrollTop(0, this.selected, this.rows.length, this.shown, this.rows);
        this.press = null;
        this.hover = null;
        // swallow the keypress that got us here
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.space); JD(this.keys.esc);
        this.visible = true;
        this.render();
        scene.input.on('wheel', this.onWheel, this);
        scene.input.on('pointermove', this.onDrag, this);
        scene.input.on('pointerup', this.onRelease, this);
        scene.input.on('pointerupoutside', this.onRelease, this);
    }

    hide() {
        this.visible = false;
        this.scene.input.off('wheel', this.onWheel, this);
        this.scene.input.off('pointermove', this.onDrag, this);
        this.scene.input.off('pointerup', this.onRelease, this);
        this.scene.input.off('pointerupoutside', this.onRelease, this);
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.slots = [];
        this.press = null;
        this.hover = null;
    }

    confirm() {
        const row = this.rows[this.selected];
        if (!row || row.here) return;
        this.hide();
        (this.flights ? this.scene.airTravel : this.scene.trainTravel).go(this.fromKey, row.key);
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter) || JD(k.space)) return this.confirm();
        if (JD(k.up) || JD(k.w)) this.select(StationPicker.step(this.rows, this.selected, -1));
        if (JD(k.down) || JD(k.s)) this.select(StationPicker.step(this.rows, this.selected, 1));
    }

    /** Move the selection, scrolling the list to keep it on screen. */
    select(index) {
        this.selected = index;
        this.top = StationPicker.scrollTop(this.top, index, this.rows.length, this.shown, this.rows);
        this.paint();
    }

    /**
     * Scroll the list by `rows`. The selection stays put while it is still in
     * view and otherwise follows the window (clampSelection). A row that is
     * being pressed is no longer a tap: the row under the finger has changed.
     */
    scroll(rows) {
        const max = this.rows.length - this.shown;
        this.scrollTo(Math.max(0, Math.min(max, this.top + rows)));
        if (this.press) { this.press.moved = true; this.press.top = this.top; this.press.y = this.press.lastY; }
    }

    scrollTo(top) {
        if (top === this.top) return false;
        this.top = top;
        this.selected = StationPicker.clampSelection(this.rows, this.selected, top, this.shown);
        this.paint();
        return true;
    }

    onWheel(pointer, over, dx, dy) {
        if (!dy) return;
        this.scroll(Math.sign(dy));
        // the row under a resting mouse has changed: it is the one to light up
        const index = this.hover === null ? -1 : this.top + this.hover;
        if (!this.press && this.rows[index] && !this.rows[index].here && index !== this.selected) {
            this.selected = index;
            this.paint();
        }
    }

    /** Any release, on a row or not, ends the press (a row's own pointerup has already run). */
    onRelease() {
        this.press = null;
    }

    /** A press that started on a row and travels scrolls the list instead of picking the row. */
    onDrag(pointer) {
        const press = this.press;
        if (!press) return;
        if (!pointer.isDown) { this.press = null; return; }   // released off the list
        // pointer.y is in canvas pixels; the overlay may be magnified (UIScale)
        const zoom = (this.scene.uiScale && this.scene.uiScale.zoom) || 1;
        press.lastY = pointer.y;
        const dy = (pointer.y - press.y) / zoom;
        if (Math.abs(dy) > StationPicker.DRAG_SLOP) press.moved = true;
        if (!press.moved) return;
        const max = this.rows.length - this.shown;
        const top = Math.max(0, Math.min(max, press.top - Math.round(dy / StationPicker.ROW_H)));
        this.scrollTo(top);
    }

    /** Fill the on-screen slots from the rows in view. */
    paint() {
        let cursorY = null;
        this.slots.forEach((slot, i) => {
            const index = this.top + i, row = this.rows[index];
            const sel = index === this.selected;
            slot.label.setText(row.label);
            slot.label.setX(this.listX + row.indent * StationPicker.INDENT);
            slot.label.setFill(row.here ? '#888888' : sel ? '#ffff00' : '#ffffff');
            slot.tag.setText(row.here ? 'you are here' : row.indent ? 'day trip' : this.flights ? 'flight' : '');
            slot.hit.setFillStyle(0xffffff, sel ? 0.08 : 0);
            if (sel) cursorY = slot.label.y;
        });
        this.cursor.setVisible(cursorY !== null);
        if (cursorY !== null) this.cursor.setY(cursorY);
        if (this.more) {
            this.more.up.setVisible(this.top > 0);
            this.more.down.setVisible(this.top + this.shown < this.rows.length);
        }
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const stations = this.registry();
        const ROW_H = StationPicker.ROW_H, MORE_H = StationPicker.MORE_H;
        const scrolls = this.rows.length > this.shown;
        const listH = this.shown * ROW_H + (scrolls ? 2 * MORE_H : 0);
        const ph = 165 + listH, pw = 560;
        const px = Math.round((W - pw) / 2), py = Math.round((H - ph) / 2);   // whole pixels: crisp text
        const listY = py + 88 + (scrolls ? MORE_H : 0);   // top of the first row
        const objs = this.objs;
        const keep = (o, depth) => { o.setScrollFactor(0); o.setDepth(depth); objs.push(o); return o; };

        const overlay = keep(scene.add.graphics(), 2000);
        overlay.fillStyle(0x000000, 0.75); overlay.fillRect(0, 0, W, H);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.hide());

        const panel = keep(scene.add.graphics(), 2001);
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        panel.on('pointerdown', () => { this.press = null; });

        const text = (x, y, t, size, bold, color, originX) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(originX === undefined ? 0.5 : originX, 0.5); o.setResolution(1);
            return keep(o, 2003);
        };
        text(W / 2, py + 34, this.flights ? 'FLIGHTS' : 'DEPARTURES', '32px', true);
        text(W / 2, py + 66, `from ${stations[this.fromKey].label}`, '16px', false, '#888888');

        // the rows: a full-width strip takes the pointer, so the whole row is
        // the target (a tap picks it, a drag that starts on it scrolls)
        this.listX = px + 78;
        this.slots = [];
        for (let i = 0; i < this.shown; i++) {
            const y = listY + i * ROW_H + ROW_H / 2;
            const hit = keep(scene.add.rectangle(W / 2, y, pw - 24, ROW_H - 4, 0xffffff, 0), 2002);
            hit.setInteractive({ useHandCursor: true });
            hit.on('pointerdown', (pointer) => {
                this.press = { slot: i, y: pointer.y, lastY: pointer.y, top: this.top, moved: false };
            });
            hit.on('pointerout', () => { if (this.hover === i) this.hover = null; });
            hit.on('pointerover', () => {
                this.hover = i;
                const index = this.top + i;
                if (this.press || this.rows[index].here || index === this.selected) return;
                this.selected = index;
                this.paint();
            });
            hit.on('pointerup', () => {
                const press = this.press;
                this.press = null;
                if (!press || press.moved || press.slot !== i) return;
                const index = this.top + i;
                if (this.rows[index].here) return;
                this.selected = index;
                this.confirm();
            });
            this.slots.push({
                hit,
                label: text(this.listX, y, '', '24px', true, '#ffffff', 0),
                tag: text(px + pw - 36, y, '', '16px', false, '#888888', 1),
            });
        }
        this.cursor = text(px + 50, listY, '▶', '24px', true, '#ffff00');

        // "there is more" arrows above and below a list that scrolls; a click
        // or tap on one moves the list most of a screenful
        this.more = null;
        if (scrolls) {
            const arrow = (y, dir) => {
                const g = keep(scene.add.graphics(), 2003);
                g.fillStyle(0xaaaaaa, 1);
                g.fillTriangle(W / 2 - 12, y - dir * 5, W / 2 + 12, y - dir * 5, W / 2, y + dir * 6);
                const hit = new Phaser.Geom.Rectangle(px + 12, y - MORE_H / 2, pw - 24, MORE_H);
                g.setInteractive({ hitArea: hit, hitAreaCallback: Phaser.Geom.Rectangle.Contains, useHandCursor: true });
                g.on('pointerdown', () => { this.press = null; this.scroll(dir * (this.shown - 1)); });
                return g;
            };
            this.more = {
                up: arrow(listY - MORE_H / 2, -1),
                down: arrow(listY + this.shown * ROW_H + MORE_H / 2, 1),
            };
        }

        this.paint();
        text(W / 2, py + ph - 26, Hints.text(scene, '↑/↓ + ENTER: board · ESC: step back'), '16px', false, '#888888');
    }
}

/** Rows on screen at once; a longer board scrolls. */
StationPicker.MAX_VISIBLE = 7;
StationPicker.ROW_H = 46;
/** How far a day trip is indented under its city. */
StationPicker.INDENT = 36;
/** Height of the "more above / below" arrow strips of a scrolling list. */
StationPicker.MORE_H = 22;
/** Overlay px a press may wander and still count as a tap. */
StationPicker.DRAG_SLOP = 10;

if (typeof window !== 'undefined') window.StationPicker = StationPicker;
