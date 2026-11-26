/**
 * ShrineVisit — the two things to do inside a shrine's worship hall (issue #212).
 *
 *   bump the offering box   a coin from the wallet, the bell rings, a blessing
 *   bump the fortune stand  draws an omikuji: one a game day, kept in the shop's
 *                           save blob, so the same slip is read back until the
 *                           date changes (Time Travel counts)
 *
 * Both are rules in the Interactions table (group 'shrine') and both answer
 * with the shop's toast: there is no overlay, no new key and nothing to learn —
 * a bump works the same from the keyboard and from the touch pad. The game has
 * no sound effects, so the bell is written out.
 *
 * Proposed by the agent that built the interiors and not yet confirmed by the
 * owner. To take it out: delete this file and its line in index.html, the two
 * 'shrine' rules in Interactions.js, the call in GameScene.checkNPCInteraction
 * and the `omikuji` field in Shop.load / Shop.save.
 */
class ShrineVisit {
    constructor(scene) {
        this.scene = scene;
        this.bump = null;           // the last bump { cell, at, dx, dy }: a held key bumps every frame
    }

    /**
     * Every frame (GameScene.update), with the direction held right now
     * (InputHandler.heading): a bump whose key is still down is still that
     * bump, whoever has the input meanwhile (ShrineVisit.carried).
     */
    hold(heading) {
        if (this.bump) this.bump = ShrineVisit.carried(this.bump, this.scene.time.now, heading);
    }

    /** The player bumped a cell: make the offering / draw the fortune there. True when it did. */
    check(gridX, gridY) {
        const scene = this.scene, shop = scene.shop;
        const hit = scene.roomManager.interactionAt(gridX, gridY, 'shrine');
        if (!hit || !shop) return false;
        // one visit per bump: a key held against the box is the same bump until it is let go
        const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell, scene.time.now);
        const from = scene.player || {};
        this.bump = { cell, at: scene.time.now, dx: Math.sign(gridX - from.gridX), dy: Math.sign(gridY - from.gridY) };
        if (!fresh) return true;
        const out = hit.kind === 'offering'
            ? ShrineVisit.offer(shop.money, Math.random())
            : ShrineVisit.fortune(shop.omikuji, gameDate(), shop.money, Math.random());
        shop.money = out.money;
        if (out.omikuji) shop.omikuji = out.omikuji;
        shop.save();
        scene.updateHUD();
        shop.toast(out.line);
        return true;
    }
}

/**
 * A blocked step bumps on every frame its key is held (Character.startMovement),
 * so bumps of one cell less than this apart are one bump, still held.
 */
ShrineVisit.HELD_MS = 250;
/**
 * Is a bump of `cell` at `now` (ms) a new one, given the bump before it
 * (`last`: { cell, at }, or null)? Yes for the first, for another cell, and
 * once the key has been let go: no bump for HELD_MS. A key that stays down
 * keeps bumping, so it never is - one offering however long it is held
 * (issue #220; it paid every 1.5 s).
 */
ShrineVisit.fresh = (last, cell, now) => !last || last.cell !== cell || now - last.at > ShrineVisit.HELD_MS;
/**
 * The last bump (`last`: { cell, at, dx, dy }) a frame later, at `now`, with
 * `heading` ({ x, y }, -1 / 0 / 1 each) held: while the direction that made it
 * is still down it is the same bump, so its time moves on with the clock.
 * Without this a held key was only known by the bumps it kept making, and
 * nothing bumps while the menu (or any overlay) has the input: opening and
 * closing it with the key still down left a gap longer than HELD_MS and the
 * box was paid a second time (issue #220). Let go, or turn another way, and
 * the bump is left to age as before - and once it is HELD_MS old it is over,
 * so a key let go and pressed again inside the menu is a new bump.
 */
ShrineVisit.carried = (last, now, heading) => {
    if (!last || !heading || !(last.dx || last.dy)) return last;
    // let go for longer than HELD_MS it is over: pressing again, in the menu or out of it, is a new bump
    if (now - last.at > ShrineVisit.HELD_MS) return last;
    return heading.x === last.dx && heading.y === last.dy ? Object.assign({}, last, { at: now }) : last;
};
/** Five yen: go-en, which also means a good connection. */
ShrineVisit.OFFERING = 5;
ShrineVisit.FORTUNE_PRICE = 100;

ShrineVisit.BLESSINGS = [
    'Safe travels, wherever the next train goes.',
    'May the weather hold for the walk home.',
    'Good company, and a seat on the train.',
    'May the next bowl of ramen be the best one.',
    'May nothing be left behind on the platform.',
];

/** The fortunes, best to worst. `weight` is its share of a hundred draws. */
ShrineVisit.FORTUNES = [
    { rank: 'Dai-kichi', means: 'great blessing', weight: 16, text: 'What you wait for comes early. Go.' },
    { rank: 'Kichi', means: 'blessing', weight: 22, text: 'A good day to walk somewhere new.' },
    { rank: 'Chu-kichi', means: 'middle blessing', weight: 20, text: 'Small plans go well. Eat something warm.' },
    { rank: 'Sho-kichi', means: 'small blessing', weight: 18, text: 'Luck in small things. Try a vending machine.' },
    { rank: 'Sue-kichi', means: 'blessing to come', weight: 12, text: 'Not yet, but soon. Be patient with trains.' },
    { rank: 'Kyo', means: 'curse', weight: 9, text: 'Mind your step. Tie this to the rail and go.' },
    { rank: 'Dai-kyo', means: 'great curse', weight: 3, text: 'Tie this to the rail. Tomorrow is a new day.' },
];

/** Pick one of `list` with `roll` in [0, 1). */
ShrineVisit.pick = (list, roll) => list[Math.min(list.length - 1, Math.max(0, Math.floor(roll * list.length)))];

/**
 * An offering from a wallet of `money`: { ok, money, line }. It costs
 * OFFERING yen; with less than that nothing is taken and the box is only
 * bowed to.
 */
ShrineVisit.offer = (money, roll) => {
    if (!(money >= ShrineVisit.OFFERING)) {
        return { ok: false, money, line: `No coin for the box (an offering is ¥${ShrineVisit.OFFERING}). You bow anyway.` };
    }
    return {
        ok: true, money: money - ShrineVisit.OFFERING,
        line: `¥${ShrineVisit.OFFERING} in the box. The bell rings: garan, garan. ` + ShrineVisit.pick(ShrineVisit.BLESSINGS, roll || 0),
    };
};

/** Index into FORTUNES for a `roll` in [0, 1), by weight. */
ShrineVisit.rankFor = (roll) => {
    const total = ShrineVisit.FORTUNES.reduce((n, f) => n + f.weight, 0);
    let at = Math.min(Math.max(roll, 0), 0.999999) * total;
    for (let i = 0; i < ShrineVisit.FORTUNES.length; i++) {
        at -= ShrineVisit.FORTUNES[i].weight;
        if (at < 0) return i;
    }
    return ShrineVisit.FORTUNES.length - 1;
};

/** A saved fortune as the game trusts it: {date, i} naming one of FORTUNES, else null. */
ShrineVisit.saved = (raw) => {
    const kept = Shop.omikujiOf(raw);
    return kept && kept.i < ShrineVisit.FORTUNES.length ? kept : null;
};

/**
 * Draw the fortune for game day `date`: { fresh, i, money, omikuji, line }.
 * One a day: when `saved` is already that day's, it is read back and costs
 * nothing. A fresh one costs FORTUNE_PRICE; without it nothing is drawn.
 */
ShrineVisit.fortune = (saved, date, money, roll) => {
    const kept = ShrineVisit.saved(saved);
    const words = (f) => `${f.rank} (${f.means}). ${f.text}`;
    if (kept && kept.date === date) {
        return { fresh: false, i: kept.i, money, line: `Drawn already today: ${words(ShrineVisit.FORTUNES[kept.i])}` };
    }
    if (!(money >= ShrineVisit.FORTUNE_PRICE)) {
        return { fresh: false, i: -1, money, line: `A fortune is ¥${ShrineVisit.FORTUNE_PRICE}. Not today.` };
    }
    const i = ShrineVisit.rankFor(roll || 0);
    return {
        fresh: true, i, money: money - ShrineVisit.FORTUNE_PRICE, omikuji: { date, i },
        line: `Omikuji, ¥${ShrineVisit.FORTUNE_PRICE}: ${words(ShrineVisit.FORTUNES[i])}`,
    };
};

if (typeof window !== 'undefined') window.ShrineVisit = ShrineVisit;
