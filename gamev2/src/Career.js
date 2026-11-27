/**
 * Career — a software job in the office towers (issue #226): a way to earn
 * that is not fishing.
 *
 *   bump the reception desk  you are signed on (the saved `career` in the shop's
 *                            blob is the staff pass); afterwards the desk reads
 *                            your title back. A toast, nothing else.
 *   bump a lift              without the pass, a line pointing at the desk; with
 *                            it, a shift opens.
 *
 * A shift is Career.TICKETS tickets against a clock. Each ticket is a commit
 * line and a row of arrows: press them in order (arrows / WASD / the d-pad). A
 * wrong press fails the build and the row starts again, which costs time and
 * nothing else. Every ticket merged pays the level's `pay`; all of them before
 * the clock runs out is a clean shift, which ends there and pays the level's
 * `bonus` on top. The money reaches the wallet once, when the shift ends, and
 * nothing is saved while it runs.
 *
 * Lifetime tickets merged decide the title (Career.LEVELS): a higher one has
 * longer rows and better pay. The clock is one second an arrow, never under
 * twenty (Career.clockMs), so every level asks the same pace and what gets
 * harder is how much a miss throws away. The level is locked in as a shift
 * starts, as are the seconds a coffee adds (the `focus` effect kind).
 *
 * One go is a "shift", never a sprint: SHIFT sprints.
 *
 * Presses are judged as directions, not keys, by Career.press. All the keys
 * are read in one place (Career.read), every frame the overlay is up, so no
 * press outlives its frame (#220): an arrow tapped on the ready screen is not
 * the first press of the shift.
 *
 * The desk and the lift are rules in the Interactions table (group 'career').
 * One answer per bump: a key held against the desk is the same bump until it
 * is let go, by the rule the offering box uses (ShrineVisit.fresh / .carried).
 *
 * To take it out: delete this file and its line in index.html, the two 'career'
 * rules in Interactions.js (give the lift its `flavour` line back), the lines in
 * GameScene (constructor, checkNPCInteraction, update, showCareer), the line in
 * InputHandler's overlay list, the Career row in MenuManager, careerProgress in
 * AchievementManager, the `career` field in Shop.load / Shop.save, Shop.careerOf
 * and the `focus` effect kind (Canned Coffee has it).
 */
class Career {
    constructor(scene) {
        this.scene = scene;
        this.state = 'idle';        // idle | ready | playing | result
        this.objs = [];
        this.bump = null;           // the last bump { cell, at, dx, dy }: a held key bumps every frame
        this.clockEvent = null;
        this.finishEvent = null;
        this.level = Career.LEVELS[0];
        this.merged = 0;            // tickets merged in the shift in play
        this.names = [];            // the shift's ticket names
        this.seq = [];              // the row being typed
        this.at = 0;                // how far along it
        this.flashUntil = 0;        // when BUILD FAILED / MERGED comes down
        this.outcome = null;        // the result screen's lines

        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({
            w: K.W, a: K.A, s: K.S, d: K.D,
            up: K.UP, down: K.DOWN, left: K.LEFT, right: K.RIGHT,
            space: K.SPACE, enter: K.ENTER, esc: K.ESC,
        });
    }

    isActive() { return this.state !== 'idle'; }

    /** Every key, read once: what went down since the last read. The only reader of the keys. */
    read() { return Career.read(this.keys, this.justDown); }

    money(n) { return this.scene.shop ? this.scene.shop.fmt(n) : `¥${n}`; }

    /** Pay into the persistent wallet and return the actual delta. */
    adjustWallet(delta) {
        if (!this.scene.shop) return 0;
        const before = this.scene.shop.money;
        this.scene.shop.money = Math.max(0, before + delta);
        this.scene.shop.save();
        this.scene.updateHUD();
        return this.scene.shop.money - before;
    }

    /** Every frame, with the direction held right now: a bump whose key is still down is still that bump. */
    hold(heading) {
        if (this.bump) this.bump = ShrineVisit.carried(this.bump, this.scene.time.now, heading);
    }

    /** The player bumped a cell: sign on at the desk / take the lift up to a shift. True when there was something. */
    check(gridX, gridY) {
        const scene = this.scene, shop = scene.shop;
        if (this.isActive() || scene.roomManager.isTransitioning) return false;
        if (scene.dialogueManager.isVisible() || (shop && shop.isVisible())) return false;
        const hit = scene.roomManager.interactionAt(gridX, gridY, 'career');
        if (!hit || !shop) return false;
        const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell, scene.time.now);
        const from = scene.player || {};
        this.bump = { cell, at: scene.time.now, dx: Math.sign(gridX - from.gridX), dy: Math.sign(gridY - from.gridY) };
        if (!fresh) return true;
        if (hit.kind === 'desk') {
            const out = Career.signOn(shop.career);
            if (out.fresh) {
                shop.career = out.career;
                shop.save();
            }
            shop.toast(out.line);
            return true;
        }
        if (!shop.career) {
            shop.toast('the lift wants a pass. the reception desk hands them out');
            return true;
        }
        this.read();    // the key held to bump the lift is not a press in the overlay
        this.state = 'ready';
        this.render();
        return true;
    }

    begin() {
        const shop = this.scene.shop;
        this.clearTimers();
        // the title and the coffee are locked in as the shift starts
        this.level = Career.levelOf(shop.career.merged);
        this.clockMs = Career.clockMs(this.level.len, shop.buff('focus'));
        this.merged = 0;
        this.names = Career.names(Math.random);
        this.seq = Career.sequence(this.level.len, Math.random);
        this.at = 0;
        this.state = 'playing';
        this.deadline = this.scene.time.now + this.clockMs;
        this.clockEvent = this.scene.time.addEvent({
            delay: 100,
            loop: true,
            callback: () => this.updateClock(),
        });
        this.finishEvent = this.scene.time.delayedCall(this.clockMs, () => this.finish(false));
        this.paint();
    }

    updateClock() {
        if (this.state !== 'playing') return;
        const remainingMs = Math.max(0, this.deadline - this.scene.time.now);
        this.clockText.setText(`${(remainingMs / 1000).toFixed(1)}s`);
        if (this.flashUntil && this.scene.time.now >= this.flashUntil) {
            this.flashUntil = 0;
            this.statusText.setText('');
        }
    }

    /** BUILD FAILED / MERGED under the clock, for a moment. */
    flash(value, color) {
        this.flashUntil = this.scene.time.now + Career.FLASH_MS;
        this.statusText.setText(value);
        this.statusText.setFill(color);
    }

    /** The shift is over: by the fifth merge (`clean`), the clock, or ESC (`quit`). Pays once. */
    finish(clean, quit) {
        if (this.state !== 'playing') return;
        const shop = this.scene.shop, achievements = this.scene.achievementManager;
        this.clearTimers();
        const done = () => (achievements ? achievements.careerProgress() : []).filter(a => a.complete).map(a => a.name);
        const before = done();
        const out = Career.settle(shop.career, this.level, this.merged, clean);
        shop.career = out.career;
        this.adjustWallet(out.pay + out.bonus);
        this.outcome = {
            head: clean ? 'SHIFT COMPLETE' : quit ? 'CLOCKED OFF' : 'TIME\'S UP',
            merged: this.merged, pay: out.pay, bonus: out.bonus, promoted: out.promoted,
        };
        this.state = 'result';
        this.paint();
        const fresh = done().filter(name => !before.includes(name));
        if (fresh.length) shop.toast('★ achievement: ' + fresh.join(' + '));
    }

    clearTimers() {
        for (const event of [this.clockEvent, this.finishEvent]) {
            if (event) event.remove();
        }
        this.clockEvent = null;
        this.finishEvent = null;
    }

    /** Close the overlay. A shift still running is dropped unpaid (only a reset does that: ESC clocks off first). */
    leave() {
        this.clearTimers();
        this.state = 'idle';
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.row = null;
        this.read();    // the key that closed it is not a press in the world
        // a direction still held against the lift is the bump that opened this, not a new one
        if (this.bump) this.bump.at = this.scene.time.now;
    }

    handleInput() { this.act(this.read()); }

    /** One frame of input, as Career.read hands it over: { dirs, held, confirm, esc }. */
    act({ dirs, held, confirm, esc }) {
        if (this.state === 'ready') {
            if (esc) return this.leave();
            if (confirm) return this.begin();
            return;
        }
        if (this.state === 'result') {
            if (esc) return this.leave();
            if (confirm) {
                this.state = 'ready';
                this.paint();
            }
            return;
        }
        if (this.state !== 'playing') return;
        if (esc) return this.finish(false, true);
        const out = Career.press(this.seq, this.at, dirs, held);
        if (!out) return;
        if (out === 'step') {
            this.at++;
            return this.paintRow();
        }
        if (out === 'miss') {
            this.at = 0;
            this.flash('BUILD FAILED', '#ff6b6b');
            return this.paintRow();
        }
        this.merged++;
        if (this.merged >= Career.TICKETS) return this.finish(true);
        this.seq = Career.sequence(this.level.len, Math.random);
        this.at = 0;
        this.paint();
        this.flash('MERGED', '#5fd38d');
    }

    /** Build the overlay: the dimmer, the panel and every line a screen can show. `paint` fills them in. */
    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const pw = 760, ph = 490, px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = this.objs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.82); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x10161c, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(3, 0x5fd38d, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (y, size, bold, color) => {
            const o = scene.add.text(W / 2, py + y, '', {
                fontSize: size,
                fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono',
                align: 'center',
            });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };

        this.headText = text(44, '32px', true, '#5fd38d');
        this.nameText = text(100, '26px', true);
        // the ready screen
        this.termsText = text(176, '20px', false, '#dddddd');
        this.rulesText = text(222, '16px', false, '#9aa7b0');
        this.coffeeText = text(274, '18px', true, '#ffd700');
        // a shift: the row of arrows, the clock, BUILD FAILED / MERGED
        this.row = scene.add.graphics();
        this.row.setScrollFactor(0); this.row.setDepth(2002); objs.push(this.row);
        this.rowGeometry = { x: W / 2, y: py + 196 };
        this.clockText = text(296, '30px', true);
        this.statusText = text(356, '26px', true);
        // the result
        this.payText = text(180, '34px', true, '#ffd700');
        this.bonusText = text(232, '22px', true, '#5fd38d');
        this.nextText = text(310, '22px', true);
        // each screen's hint is its own line
        this.hintText = text(ph - 26, '16px', false, '#999999');
        this.paint();
    }

    /** Fill the overlay in for the state it is in. */
    paint() {
        const scene = this.scene, shop = scene.shop, state = this.state;
        const put = (o, value, color) => {
            o.setText(value || '');
            o.setVisible(!!value);
            if (color) o.setFill(color);
        };
        const ready = state === 'ready', playing = state === 'playing', result = state === 'result';
        const level = playing ? this.level : Career.levelOf(shop.career.merged);
        const focus = ready ? shop.buff('focus') : 0;

        put(this.headText, ready ? 'ENGINEERING' : playing ? `TICKET ${this.merged + 1}/${Career.TICKETS}` : this.outcome.head);
        put(this.nameText, ready ? level.title : playing ? this.names[this.merged] : `${this.outcome.merged}/${Career.TICKETS} merged`);
        put(this.termsText, ready && Career.terms(level, focus, n => this.money(n)));
        put(this.rulesText, ready && 'press the arrows in order. a wrong one fails the build and the ticket starts again');
        put(this.coffeeText, ready && focus > 0 && `coffee: +${focus}s on the clock`);
        put(this.clockText, playing && `${(this.clockMs / 1000).toFixed(1)}s`);
        this.flashUntil = 0;
        this.statusText.setText('');
        this.statusText.setVisible(playing);
        put(this.payText, result && `+${this.money(this.outcome.pay)}`);
        put(this.bonusText, result && this.outcome.bonus > 0 && `clean shift +${this.money(this.outcome.bonus)}`);
        const next = result && Career.next(shop.career.merged);
        put(this.nextText, result && (this.outcome.promoted ? `PROMOTED: ${this.outcome.promoted}`
            : next ? `${next.left} more to ${next.title}` : ''), result && this.outcome.promoted ? '#ffd700' : '#9aa7b0');
        put(this.hintText, Hints.text(scene, ready ? 'SPACE to start    ESC to leave'
            : playing ? 'arrows to type    ESC to clock off' : 'SPACE for another shift    ESC to leave'));
        this.paintRow();
        if (playing) this.updateClock();
    }

    /** The row of arrows: typed ones green, the one wanted white in a box, the rest grey. Empty off shift. */
    paintRow() {
        const g = this.row;
        if (!g) return;
        g.clear();
        if (this.state !== 'playing') return;
        const cell = Career.CELL, n = this.seq.length, left = this.rowGeometry.x - (n * cell) / 2, top = this.rowGeometry.y - cell / 2;
        this.seq.forEach((dir, i) => {
            const cx = left + i * cell + cell / 2, cy = top + cell / 2;
            g.fillStyle(i < this.at ? 0x5fd38d : i === this.at ? 0xffffff : 0x4a5560, 1);
            const [head, stem] = Career.arrow(dir, cx, cy);
            g.fillTriangle(...head);
            g.fillRect(...stem);
            if (i === this.at) {
                g.lineStyle(2, 0xffffff, 1);
                g.strokeRect(left + i * cell + 3, top + 3, cell - 6, cell - 6);
            }
        });
    }
}

/**
 * The ladder: the title held from `at` lifetime tickets merged, the length of
 * its rows, what a merged ticket pays and what a clean shift adds. Pay per key
 * press rises with every step, with and without the bonus, so a promotion is
 * never a pay cut (career.test.js holds it to that, and pins the two ends of
 * the balance table in docs/shop-and-economy.md).
 */
Career.LEVELS = [
    { title: 'Intern',             at: 0,   len: 3, pay: 10,  bonus: 30 },
    { title: 'Junior Engineer',    at: 10,  len: 4, pay: 20,  bonus: 50 },
    { title: 'Engineer',           at: 25,  len: 5, pay: 35,  bonus: 75 },
    { title: 'Senior Engineer',    at: 50,  len: 6, pay: 55,  bonus: 100 },
    { title: 'Staff Engineer',     at: 90,  len: 7, pay: 80,  bonus: 125 },
    { title: 'Principal Engineer', at: 150, len: 8, pay: 110, bonus: 200 },
];

/** Tickets in a shift. */
Career.TICKETS = 5;
/** The clock: this long for every arrow in the shift... */
Career.ARROW_MS = 1000;
/** ...and never less than this. */
Career.MIN_CLOCK_MS = 20000;
/** How long BUILD FAILED / MERGED stays up. */
Career.FLASH_MS = 600;
/** The side of one arrow's cell in the row, canvas px (8 arrows = 448 of the panel's 760). */
Career.CELL = 56;

Career.DIRS = ['up', 'down', 'left', 'right'];
Career.OPPOSITE = { up: 'down', down: 'up', left: 'right', right: 'left' };
/** A direction is its arrow key or its WASD key: the names of `keys` as the constructor adds them. */
Career.KEYS = { up: ['up', 'w'], down: ['down', 's'], left: ['left', 'a'], right: ['right', 'd'] };

/** What the tickets are called. Lower case, ASCII, 40 characters at most; nobody's name. */
Career.TICKET_NAMES = [
    'fix: the login button does nothing',
    'chore: bump left-pad',
    'revert: "fix: the login button"',
    'fix: off by one in the pager',
    'feat: dark mode, again',
    'fix: typo in the readme',
    'chore: delete the commented-out code',
    'fix: it works on my machine now',
    'test: skip the flaky one',
    'refactor: rename utils to helpers',
    'fix: timezones',
    'feat: add a loading spinner',
    'chore: update the lockfile',
    'fix: null check the null check',
    'docs: explain what this even does',
    'perf: cache it and hope',
    'fix: the cache',
    'style: tabs to spaces',
    'ci: retry until green',
    'feat: a button that says ok',
];

/** The LEVELS row for `merged` lifetime tickets: the last one whose `at` it has reached. */
Career.levelOf = (merged) => {
    const n = Number(merged) || 0;
    return Career.LEVELS.reduce((best, level) => (level.at <= n ? level : best), Career.LEVELS[0]);
};

/** The next promotion as { title, left } (tickets still to merge), or null at the top. */
Career.next = (merged) => {
    const up = Career.LEVELS[Career.LEVELS.indexOf(Career.levelOf(merged)) + 1];
    return up ? { title: up.title, left: up.at - (Number(merged) || 0) } : null;
};

/** A shift's clock in ms for rows of `len`: one ARROW_MS an arrow, never under MIN_CLOCK_MS, plus `focus` seconds. */
Career.clockMs = (len, focus) => Math.max(Career.MIN_CLOCK_MS, Career.TICKETS * len * Career.ARROW_MS) + 1000 * (focus || 0);

/** The ready screen's line of terms for a level, with `focus` seconds on the clock; `fmt` words the yen. */
Career.terms = (level, focus, fmt) =>
    `${Career.TICKETS} tickets · ${Math.round(Career.clockMs(level.len, focus) / 1000)}s · ${fmt(level.pay)} a ticket · +${fmt(level.bonus)} for a clean shift`;

/** A row of `len` directions from `rand` (0..1): never three the same in a row. */
Career.sequence = (len, rand) => {
    const seq = [];
    while (seq.length < len) {
        const n = seq.length;
        const pool = n >= 2 && seq[n - 1] === seq[n - 2] ? Career.DIRS.filter(d => d !== seq[n - 1]) : Career.DIRS;
        seq.push(pool[Math.min(pool.length - 1, Math.floor(rand() * pool.length))]);
    }
    return seq;
};

/** A shift's ticket names from `rand`: TICKETS of TICKET_NAMES, no two the same. */
Career.names = (rand) => {
    const left = Career.TICKET_NAMES.slice(), out = [];
    while (out.length < Career.TICKETS) {
        out.push(left.splice(Math.min(left.length - 1, Math.floor(rand() * left.length)), 1)[0]);
    }
    return out;
};

/**
 * Read every key once: { dirs, held, confirm, esc }. `dirs` is the directions
 * with a key that went down since the last read, `held` the ones with a key
 * down that did not, `confirm` SPACE or ENTER just down, `esc` ESC just down.
 * JustDown stays raised until it is read (#220), so every key is read on every
 * call and nothing short-circuits: W and ↑ pressed together are one `up` now
 * and nothing on the next read.
 */
Career.read = (keys, justDown = Phaser.Input.Keyboard.JustDown) => {
    const dirs = [], held = [];
    for (const dir of Career.DIRS) {
        const pair = Career.KEYS[dir].map(name => keys[name]);
        const went = pair.map(key => justDown(key));
        if (went.some(Boolean)) dirs.push(dir);
        else if (pair.some(key => key.isDown)) held.push(dir);
    }
    const space = justDown(keys.space), enter = justDown(keys.enter);
    return { dirs, held, confirm: space || enter, esc: justDown(keys.esc) };
};

/**
 * Judge one frame's presses against `seq` at index `at`: null (nothing),
 * 'step', 'merged' (the step that finishes the row) or 'miss'. `dirs` went
 * down this frame, `held` were down already (omit it and nothing is forgiven).
 *
 *   1. no direction: nothing.
 *   2. more than two, or two opposite ones: a miss. Slapping every key is not
 *      an answer; a perpendicular pair is what the d-pad sends for a touch on
 *      a diagonal.
 *   3. the one wanted is among them: a step.
 *   4. the arrow just typed is still held and every direction is across it:
 *      nothing. That is a thumb rolling off the arrow it pressed into the
 *      next diagonal, or sliding round the pad's rim; the d-pad sends a
 *      keydown for it and it was never a press.
 *   5. anything else: a miss.
 */
Career.press = (seq, at, dirs, held) => {
    if (!dirs || !dirs.length) return null;
    if (dirs.length > 2 || (dirs.length === 2 && Career.OPPOSITE[dirs[0]] === dirs[1])) return 'miss';
    if (dirs.includes(seq[at])) return at + 1 >= seq.length ? 'merged' : 'step';
    const last = at > 0 ? seq[at - 1] : null;
    const across = (dir) => dir !== last && dir !== Career.OPPOSITE[last];
    if (last && held && held.includes(last) && dirs.every(across)) return null;
    return 'miss';
};

/** "12 tickets merged". */
Career.count = (merged) => `${merged} ${merged === 1 ? 'ticket' : 'tickets'} merged`;

/** A career in one line: the title, the tickets, what is left to the next one. */
Career.status = (career) => {
    const level = Career.levelOf(career.merged), next = Career.next(career.merged);
    return `${level.title} · ${Career.count(career.merged)} · ` +
        (next ? `${next.left} more to ${next.title}` : 'nowhere left to go but meetings');
};

/**
 * The reception desk: { fresh, career, line }. `career` is the saved one (null
 * when never hired). Hired once: after that nothing changes, `career` is
 * absent and the line is the status.
 */
Career.signOn = (career) => {
    if (career) return { fresh: false, line: Career.status(career) };
    return {
        fresh: true, career: { merged: 0, shifts: 0, earned: 0 },
        line: 'You fill in a form. Staff pass: Intern. The lifts go up to engineering now.',
    };
};

/**
 * Close a shift played at `level` with `merged` tickets: { career, pay, bonus,
 * promoted }. `career` is a new object with the shift added, `pay` the tickets'
 * money, `bonus` the level's when the shift was `clean`, `promoted` the new
 * title when the tickets crossed a threshold (else null).
 */
Career.settle = (career, level, merged, clean) => {
    const pay = merged * level.pay, bonus = clean ? level.bonus : 0;
    const after = { merged: career.merged + merged, shifts: career.shifts + 1, earned: career.earned + pay + bonus };
    const title = Career.levelOf(after.merged).title;
    return { career: after, pay, bonus, promoted: title !== Career.levelOf(career.merged).title ? title : null };
};

/**
 * Who is hiring: [{ room, name }] for every room with a `lobby`, sorted by
 * room. `name` is the town the tower stands in, as the HUD shows it.
 */
Career.where = (config) => Object.keys((config && config.rooms) || {})
    .filter(room => config.rooms[room].lobby)
    .sort()
    .map(room => {
        const host = config.rooms[room].lobby.host, town = config.rooms[host];
        const name = (town && town.name) || host;
        return { room, name: typeof hudName === 'function' ? hudName(name) : name };
    });

/** One arrow at (cx, cy) as [triangle, rect]: the head's six coordinates and the stem's x, y, w, h. */
Career.arrow = (dir, cx, cy) => {
    const h = 16, s = 6, l = 14;    // the head's half-width (and length), the stem's half-width and length
    if (dir === 'up') return [[cx, cy - h, cx - h, cy, cx + h, cy], [cx - s, cy, 2 * s, l]];
    if (dir === 'down') return [[cx, cy + h, cx - h, cy, cx + h, cy], [cx - s, cy - l, 2 * s, l]];
    if (dir === 'left') return [[cx - h, cy, cx, cy - h, cx, cy + h], [cx, cy - s, l, 2 * s]];
    return [[cx + h, cy, cx, cy - h, cx, cy + h], [cx - l, cy - s, l, 2 * s]];
};

if (typeof window !== 'undefined') window.Career = Career;
