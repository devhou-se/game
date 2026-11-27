/**
 * Intro — the new-player introduction (issue #39).
 *
 * A short paged overlay in the usual panel style:
 *   1. who devhouse is, what the trip is, and how the blog and the HUD date
 *      drive what people say
 *   2. the basic controls, drawn as keycaps (or as the on-screen buttons when
 *      touch controls are active)
 *   3. where to start — there is no quest system, so it points at real
 *      things: where the friends are today, exploring, and Paint the Board
 * Fishing controls and map travel are deliberately absent (the first is
 * taught when a rod is bought, the second is a debug feature).
 *
 * SPACE / ENTER (touch A) or a tap anywhere turns the page, the last page
 * closes it; ESC (touch B) skips the lot. While it is up it owns all input
 * (it is in InputHandler's overlay list), so nothing moves or opens
 * underneath.
 *
 * Shown automatically once, on a first visit, after the first-run character
 * creator closes — see shouldAutoShow(). `?nointro=1` suppresses the
 * automatic showing (tests / development). 'How to Play' in the ESC menu
 * replays it at any time — it is also the game's only controls reference
 * (the separate Controls overlay was folded into page 2, issue #55).
 */
class Intro {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.page = 0;
        this.objs = [];
        this.onClose = null;
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ enter: K.ENTER, space: K.SPACE, esc: K.ESC });
        this.pages = [
            { title: 'WELCOME TO DEVHOUSE', draw: (l) => this.drawWelcome(l) },
            { title: 'HOW TO PLAY', draw: (l) => this.drawControls(l) },
            { title: 'WHERE TO START', draw: (l) => this.drawObjective(l) },
        ];
    }

    /**
     * localStorage gate. Absent: never offered. 'pending': a first visit has
     * begun but the intro has not been finished (so a reload half way through
     * the creator or the intro still gets it). '1': completed or skipped.
     */
    static SEEN_KEY = 'gamev2_intro_seen';

    /**
     * Should the intro run by itself on this boot? Only for a first visit
     * (`firstVisit` = the first-run character creator is about to show) or
     * one that was interrupted; a returning player never gets it unasked.
     * `?nointro=1` always says no, and leaves the gate untouched.
     */
    static shouldAutoShow(firstVisit) {
        if (new URLSearchParams(location.search).get('nointro') === '1') return false;
        try {
            const seen = localStorage.getItem(Intro.SEEN_KEY);
            if (seen === '1') return false;
            if (!firstVisit && seen !== 'pending') return false;
            localStorage.setItem(Intro.SEEN_KEY, 'pending');
            return true;
        } catch (e) { return false; }
    }

    /**
     * Is this a new player — one the intro has been (or is about to be)
     * offered to and who has not finished it? Same test as shouldAutoShow,
     * without `?nointro` and without touching the gate. GameScene keeps
     * the answer as `scene.newPlayer`; where a player starts no longer
     * depends on it (issue #166: everyone starts beside the cast).
     */
    static isNewPlayer() {
        try {
            const seen = localStorage.getItem(Intro.SEEN_KEY);
            return seen !== '1' && (seen === 'pending' || CharacterCreator.shouldAutoShow());
        } catch (e) { return false; }
    }

    isVisible() { return this.visible; }

    show(opts = {}) {
        if (this.visible) return;
        this.onClose = opts.onClose || null;
        this.firstRun = !!opts.firstRun; // only changes the last page's prompt
        const JD = Phaser.Input.Keyboard.JustDown;
        Object.values(this.keys).forEach(k => JD(k)); // swallow stale presses
        this.visible = true;
        this.page = 0;
        this.render();
    }

    /** Close it — finished or skipped, either way it counts as seen. */
    hide() {
        if (!this.visible) return;
        this.visible = false;
        try { localStorage.setItem(Intro.SEEN_KEY, '1'); } catch (e) { /* fine */ }
        this.clear();
        const onClose = this.onClose;
        this.onClose = null;
        if (onClose) onClose();
    }

    next() {
        if (this.page >= this.pages.length - 1) { this.hide(); return; }
        this.page++;
        this.render();
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        // evaluate all three so none is left "just down" for the next frame
        const esc = JD(k.esc), space = JD(k.space), enter = JD(k.enter);
        if (esc) this.hide();
        else if (space || enter) this.next();
    }

    clear() {
        this.objs.forEach(o => o.destroy());
        this.objs = [];
    }

    /**
     * The friends on `date`, as sprite base names: CharacterSelect.lineup()
     * of that date's trip (config.members when there are no trips) —
     * alphabetical, only names with a sprite set, never James. The cast row
     * draws these and the sentence under it names them, so the two agree.
     */
    static cast(config, date) {
        const trip = Trips.forDate(Trips.of(config), date);
        return CharacterSelect.lineup(config, trip ? trip.members : undefined);
    }

    /**
     * Page 1's copy for a config, a game date and the real date: who
     * devhouse is — the members of the game date's trip (issue #130;
     * Intro.cast, the same people the cast row draws) — then tripCopy's two
     * sentences, then how the date works.
     */
    static welcomeCopy(config, date, today) {
        const trips = Trips.of(config);
        const trip = Trips.forDate(trips, date);
        const names = Trips.list(Intro.cast(config, date).map(Trips.displayName));
        const live = Trips.live(trips, today);
        const lead = Trips.leadIn(trips, date);
        const [about, lines] = Intro.tripCopy(trip,
            !!trip && !!live && live.id === trip.id && Trips.during(trip, date),
            !trip || Trips.daysOf(trips, trip, [...contentChangeDates(config)]).length > 0,
            lead ? Trips.dayText(trip.start) : null);
        // a visitor in the days before a trip is shown a day of the one
        // before (defaultGameDate): say that the next is about to start
        const next = Trips.upcoming(trips, today);
        return [
            `devhouse is a group of friends${names ? `: ${names}` : ''}.`,
            next && next !== trip ? `${about} ${next.name} starts on ${Trips.dayText(next.start)}.` : about,
            lines,
            // the game always opens on a day of a trip (today's, or the one
            // today cycles onto — NpcStates.defaultGameDate), so Time Travel
            // is for visiting ANOTHER day, or another trip
            `The date at the top of the screen picks the day. Use Time Travel in the menu to visit another day${trips.length > 1 ? ' or another trip' : ' of the trip'}, and everyone has a new story.`,
        ];
    }

    /**
     * Page 1's sentences about the trip, from data: which trip the game
     * date is on, where it went, and whether anyone has posted from it yet.
     * `starts` ("February 18") is given on a lead-in day (issue #164): the
     * trip has not started and nobody is there yet.
     */
    static tripCopy(trip, live, posted, starts) {
        const about = !trip ? 'Their trip to Japan is now a little world you can walk around.'
            : starts ? `${trip.name}${trip.where ? `, their trip to ${trip.where},` : ''} starts on ${starts}. This is the little world they will be walking around.`
            : live ? `They are on ${trip.name} right now${trip.where ? `, in ${trip.where}` : ''}, and it is a little world you can walk around.`
            : `This is ${trip.name}${trip.where ? `, their trip to ${trip.where}` : ''}: a little world you can walk around.`;
        const lines = posted
            ? 'The people you meet will tell you about their day. Their lines come from the blog posts they wrote on the road.'
            : 'The people you meet will tell you about their day, once they start writing blog posts on the road.';
        return [about, lines];
    }

    // --------------------------------------------------------------- drawing

    render() {
        this.clear();
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const objs = this.objs;
        const add = (o, depth) => { o.setScrollFactor(0); o.setDepth(depth); objs.push(o); return o; };
        const pw = 920, ph = 600, px = Math.round((W - pw) / 2), py = Math.round((H - ph) / 2);
        const touch = Hints.touch(scene);

        // dimmer: the tap target, and it swallows clicks meant for the world/HUD
        const overlay = add(scene.add.graphics(), 2000);
        overlay.fillStyle(0x000000, 0.85); overlay.fillRect(0, 0, W, H);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.next());

        const panel = add(scene.add.graphics(), 2001);
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);

        const g = add(scene.add.graphics(), 2002);
        const text = (x, y, t, size, bold, color, originX, originY) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(originX != null ? originX : 0.5, originY != null ? originY : 0.5);
            o.setResolution(1);
            return add(o, 2003);
        };
        const image = (x, y, key, scale) => {
            const o = scene.add.image(x, y, key);
            o.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);
            o.setScale(scale || 1);
            return add(o, 2002);
        };
        const layout = { W, H, px, py, pw, ph, cx: W / 2, g, text, image, touch };

        const page = this.pages[this.page];
        text(W / 2, py + 44, page.title, '32px', true);
        page.draw(layout);

        // page dots
        const n = this.pages.length, gap = 26, dot = 10;
        for (let i = 0; i < n; i++) {
            const x = Math.round(W / 2 + (i - (n - 1) / 2) * gap - dot / 2), y = py + ph - 66;
            g.fillStyle(i === this.page ? 0xffd700 : 0x555555, 1);
            g.fillRect(x, y, dot, dot);
        }

        const last = this.page === n - 1;
        const go = last ? (this.firstRun ? 'start' : 'close') : 'next';
        const hint = Hints.text(scene, `SPACE  ${go}` + (last ? '' : '   ·   ESC  skip'), { tap: true });
        text(W / 2, py + ph - 28, hint, '18px', false, '#888888');
    }

    /** Page 1: who, what, and why people say what they say. */
    drawWelcome(l) {
        const scene = this.scene;
        // the cast, small, along the top
        const cast = Intro.cast(scene.config, gameDate())
            .map(name => `${name}_front`)
            .map(key => scene.textures.exists(`${key}_frame_0`) ? `${key}_frame_0` : key)
            .filter(key => scene.textures.exists(key));
        // however many of us there are, the row stays inside the panel: the
        // figures close up first, then drop to 1x (a body is 42px wide)
        const spacing = Math.min(104, Math.floor((l.pw - 120) / Math.max(1, cast.length)));
        const scale = spacing >= 88 ? 2 : 1;
        cast.forEach((key, i) => {
            const x = Math.round(l.cx + (i - (cast.length - 1) / 2) * spacing);
            const img = l.image(x, l.py + 196, key, scale);
            img.setOrigin(31 / 64, 54 / 64); // feet (see TitleScreen)
        });

        const paras = Intro.welcomeCopy(scene.config, gameDate(), todayIso())
            .map((copy, i) => [copy, i ? '#dddddd' : '#ffffff']);
        let y = l.py + 232;
        paras.forEach(([copy, color]) => {
            const t = l.text(l.cx, y, copy, '22px', false, color, 0.5, 0);
            t.setWordWrapWidth(l.pw - 140);
            t.setAlign('center');
            t.setLineSpacing(4);
            y += t.height + 18;
        });
    }

    /** Page 2: the basic controls as keycaps (or touch buttons). */
    drawControls(l) {
        const g = l.g;
        const labelX = l.px + 196, artX = l.px + 232, whatX = l.px + 552;
        const rowY = (i) => l.py + 128 + i * 84;

        // a keyboard key: dark lip under a light face, label (or arrow) on top
        const keycap = (x, y, w, h, label, arrow) => {
            g.fillStyle(0x111111, 1); g.fillRect(x - 2, y - 2, w + 4, h + 8);
            g.fillStyle(0x8a8a8a, 1); g.fillRect(x, y + 4, w, h);
            g.fillStyle(0xe6e6e6, 1); g.fillRect(x, y, w, h);
            const cx = x + w / 2, cy = y + h / 2;
            if (arrow) {
                const r = 8;
                const pts = {
                    up: [cx, cy - r, cx - r, cy + r - 2, cx + r, cy + r - 2],
                    down: [cx, cy + r, cx - r, cy - r + 2, cx + r, cy - r + 2],
                    left: [cx - r, cy, cx + r - 2, cy - r, cx + r - 2, cy + r],
                    right: [cx + r, cy, cx - r + 2, cy - r, cx - r + 2, cy + r],
                }[arrow];
                g.fillStyle(0x1a1a1a, 1); g.fillTriangle(...pts);
            } else {
                l.text(cx, cy, label, label.length > 1 ? '18px' : '22px', true, '#1a1a1a');
            }
            return x + w;
        };
        // inverted-T cluster, vertically centred on cy; returns its right edge
        const cluster = (x, cy, caps) => {
            const k = 34, s = 6;
            const top = cy - (k * 2 + s + 4) / 2;
            keycap(x + k + s, top, k, k, caps[0].label, caps[0].arrow);
            caps.slice(1).forEach((c, i) => keycap(x + i * (k + s), top + k + s + 4, k, k, c.label, c.arrow));
            return x + 3 * k + 2 * s;
        };
        // an on-screen touch button, drawn like TouchControls draws them (and
        // in its proportions: a big sprint pill, a big A, a small B)
        const touchButton = (cx, cy, w, h, label, color, size) => {
            g.fillStyle(0x0c0c12, 1); g.fillRoundedRect(cx - w / 2, cy - h / 2, w, h, Math.min(w, h) / 2);
            g.lineStyle(2, color, 1); g.strokeRoundedRect(cx - w / 2, cy - h / 2, w, h, Math.min(w, h) / 2);
            l.text(cx, cy, label, size || '24px', true, '#' + color.toString(16).padStart(6, '0'));
        };

        const rows = [];
        if (l.touch) {
            rows.push(['MOVE', 'the d-pad, slide for diagonals', (x, cy) => {
                const k = 24;
                g.fillStyle(0x0c0c12, 1); g.fillRoundedRect(x, cy - k * 1.5, k * 3, k * 3, 8);
                g.lineStyle(2, 0x777777, 1); g.strokeRoundedRect(x, cy - k * 1.5, k * 3, k * 3, 8);
                const c = x + k * 1.5, r = 7, o = k;
                g.fillStyle(0xffffff, 1);
                g.fillTriangle(c, cy - o - r, c - r, cy - o + r - 2, c + r, cy - o + r - 2);
                g.fillTriangle(c, cy + o + r, c - r, cy + o - r + 2, c + r, cy + o - r + 2);
                g.fillTriangle(c - o - r, cy, c - o + r - 2, cy - r, c - o + r - 2, cy + r);
                g.fillTriangle(c + o + r, cy, c + o - r + 2, cy - r, c + o - r + 2, cy + r);
            }]);
            rows.push(['SPRINT', 'hold while moving', (x, cy) => touchButton(x + 42, cy, 84, 56, '>>', 0xdddddd, '24px')]);
        } else {
            rows.push(['MOVE', 'diagonals work too', (x, cy) => {
                const right = cluster(x, cy, [{ label: 'W' }, { label: 'A' }, { label: 'S' }, { label: 'D' }]);
                l.text(right + 30, cy, 'or', '20px', false, '#888888');
                cluster(right + 60, cy, [{ arrow: 'up' }, { arrow: 'left' }, { arrow: 'down' }, { arrow: 'right' }]);
            }]);
            rows.push(['SPRINT', 'hold while moving', (x, cy) => keycap(x, cy - 20, 110, 36, 'SHIFT')]);
        }
        // the one rule behind everything contextual; the second line is the
        // list the old Controls overlay carried (minus ponds — see the header)
        rows.push(['INTERACT', 'walk into people and things:\nshops, trains, the izakaya', (x, cy) => this.drawBump(l, x, cy)]);
        if (l.touch) {
            rows.push(['TALK', 'next line of dialogue', (x, cy) => touchButton(x + 28, cy, 56, 56, 'A', 0xffd700)]);
            rows.push(['MENU', 'opens the menu, closes anything', (x, cy) => touchButton(x + 28, cy, 46, 46, 'B', 0xff9c9c, '20px')]);
        } else {
            rows.push(['TALK', 'next line of dialogue', (x, cy) => {
                const right = keycap(x, cy - 20, 150, 36, 'SPACE');
                keycap(right + 12, cy - 20, 96, 36, 'ENTER');
            }]);
            rows.push(['MENU', 'opens the menu, closes anything', (x, cy) => keycap(x, cy - 20, 64, 36, 'ESC')]);
        }

        rows.forEach(([label, what, art], i) => {
            const cy = rowY(i);
            l.text(labelX, cy, label, '22px', true, '#ffd700', 1);
            art(artX, cy);
            l.text(whatX, cy, what, '20px', false, '#dddddd', 0);
        });
        // touch controls are on for touchscreen laptops and tablets with a
        // keyboard too, where the keys still work — say so in one line
        if (l.touch) {
            l.text(l.cx, l.py + l.ph - 90, 'Got a keyboard?  WASD / arrows  ·  SHIFT  ·  SPACE / ENTER  ·  ESC', '18px', false, '#888888');
        }
    }

    /** "Walk into someone": you, an arrow, them, and a speech mark. */
    drawBump(l, x, cy) {
        const scene = this.scene, g = l.g;
        const cast = CharacterSelect.available(scene.config);
        const frame = (name) => {
            const key = `${name}_front`;
            if (scene.textures.exists(`${key}_frame_0`)) return `${key}_frame_0`;
            return scene.textures.exists(key) ? key : null;
        };
        // "you" is whoever the player is playing as (the default sprite, a
        // member or a created character); "them" is a devhouse member who is
        // not you
        const mine = ((scene.player && scene.player.baseSpriteKey) || scene.config.player.sprite || '')
            .replace(/_(front|back|side)$/, '');
        const other = Intro.cast(scene.config, gameDate()).find(n => n !== mine) || cast.find(n => n !== mine);
        const me = frame(mine) || (cast.length ? frame(cast[0]) : null);
        const them = other ? frame(other) : null;
        if (me) l.image(x + 26, cy, me, 1);
        // arrow
        g.fillStyle(0xffffff, 1);
        g.fillRect(x + 62, cy - 3, 34, 6);
        g.fillTriangle(x + 108, cy, x + 94, cy - 11, x + 94, cy + 11);
        if (them) l.image(x + 146, cy, them, 1);
        // speech bubble
        const bx = x + 178, by = cy - 30;
        g.fillStyle(0xe6e6e6, 1);
        g.fillRect(bx, by, 52, 30);
        g.fillTriangle(bx + 6, by + 30, bx + 18, by + 30, bx + 4, by + 40);
        g.fillStyle(0x1a1a1a, 1);
        [12, 23, 34].forEach(dx => g.fillRect(bx + dx, by + 12, 6, 6));
    }

    /**
     * Where the friends are on the game date, for page 3 (Trips.whereText):
     * the ones in the room the player is standing in are named, the other
     * rooms are listed by their display names (the HUD shows those). Whoever
     * the player is playing as is not one of "them". On a lead-in day
     * (issue #164) it says when and where the trip starts, and with nobody
     * to walk into yet the invitation is to look around.
     */
    whereFriendsAre() {
        const s = this.scene;
        const played = Trips.baseOf((s.player && s.player.baseSpriteKey) || s.config.player.sprite);
        // "here" is the district the player stands in: config rooms are the
        // districts, a stitched city is only where they are drawn
        const here = s.roomManager ? s.roomManager.currentDistrict() : null;
        return Intro.meetCopy(Trips.membersByRoom(s.config, gameDate(), { played }), here,
            Trips.arrivalText(s.config, gameDate(), here));
    }

    /** Page 3's "Meet the friends" body: where they are, and what to do about it. */
    static meetCopy(groups, here, arrival) {
        const where = Trips.whereText(groups, here, arrival);
        const members = groups.reduce((all, g) => all.concat(g.members), []);
        // one person is walked into by name, and nobody at all has to be found first
        const invite = !members.length ? (arrival ? 'Have a look around before they get here.' : 'Go and find one to say hello.')
            : members.length === 1 ? `Walk into ${members[0].name} to say hello.`
            : 'Walk into one to say hello.';
        return `${where} ${invite}`;
    }

    /** Page 3: something to go and do. */
    drawObjective(l) {
        const g = l.g;
        const left = l.px + 150;
        const p = this.scene.achievementManager ? this.scene.achievementManager.paintProgress() : null;
        const items = [
            ['Meet the friends',
                this.whereFriendsAre()],
            ['Have a wander',
                'Streets, shops, stations, the countryside. See what is out there.'],
            ['Paint the Board',
                'Step on every tile in the world. Your progress is under Achievements in the menu.'],
        ];
        let y = l.py + 128;
        items.forEach(([head, body], i) => {
            // numbered gold tile
            g.fillStyle(0xffd700, 1); g.fillRect(left - 62, y, 40, 40);
            l.text(left - 42, y + 20, String(i + 1), '26px', true, '#1a1a1a');
            l.text(left, y + 20, head, '26px', true, '#ffffff', 0);
            const t = l.text(left, y + 46, body, '20px', false, '#bbbbbb', 0, 0);
            t.setWordWrapWidth(l.pw - 150 - 80);
            t.setLineSpacing(4);
            y += 46 + t.height + 30;
        });
        if (p) {
            // the real progress bar, same colours as the Achievements overlay
            const barW = l.pw - 150 - 80 - 110, barH = 20, barY = y - 16;
            g.fillStyle(0x333333, 1); g.fillRect(left, barY, barW, barH);
            g.fillStyle(p.complete ? 0xffd700 : 0x33cc66, 1);
            g.fillRect(left, barY, barW * (p.total ? Math.min(1, p.painted / p.total) : 0), barH);
            g.lineStyle(2, 0x666666, 1); g.strokeRect(left, barY, barW, barH);
            l.text(left + barW + 16, barY + barH / 2, `${p.percent}%`, '20px', true, '#ffffff', 0);
        }
    }
}

if (typeof window !== 'undefined') window.Intro = Intro;
