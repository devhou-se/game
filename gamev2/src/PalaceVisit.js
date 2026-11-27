/**
 * PalaceVisit — the two things to do inside the palace's audience hall (issue #215).
 *
 *   bump the dais           you request an audience; one of a handful of dry answers
 *   bump the visitors' book you sign it: once a game day, kept in the shop's save
 *                           blob beside the omikuji, so a second bump that day only
 *                           reads your name back (Time Travel counts as another day)
 *
 * Both are rules in the Interactions table (group 'palace') and both answer with
 * the shop's toast: no overlay, no new key, nothing to learn — a bump works the
 * same from the keyboard and from the touch pad. Nothing costs anything. The
 * armour, the sword rack and the guard's post only say a line: they are
 * `flavour` rules and need nothing from here.
 *
 * One answer per bump: a key held against the dais is the same bump until it is
 * let go, by the rule the offering box uses (ShrineVisit.fresh / .held).
 *
 * To take it out: delete this file and its line in index.html, the two 'palace'
 * rules in Interactions.js, the three lines in GameScene (constructor,
 * checkNPCInteraction, update), the `guestbook` field in Shop.load / Shop.save
 * and Shop.guestbookOf.
 */
class PalaceVisit {
    constructor(scene) {
        this.scene = scene;
        this.bump = null;           // the last bump { cell, dx, dy }, while its key is still down: a held key bumps every frame
        this.asked = 0;             // audiences requested this session: the answers come round in turn
    }

    /** Every frame, with the direction held right now: a bump whose key is still down is still that bump. */
    hold(heading) {
        this.bump = ShrineVisit.held(this.bump, heading);
    }

    /** The player bumped a cell: ask for an audience / sign the book there. True when there was something. */
    check(gridX, gridY) {
        const scene = this.scene, shop = scene.shop;
        const hit = scene.roomManager.interactionAt(gridX, gridY, 'palace');
        if (!hit || !shop) return false;
        const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell);
        const from = scene.player || {};
        this.bump = { cell, dx: Math.sign(gridX - from.gridX), dy: Math.sign(gridY - from.gridY) };
        if (!fresh) return true;
        if (hit.kind === 'audience') {
            shop.toast(PalaceVisit.audience(this.asked++));
            return true;
        }
        const out = PalaceVisit.sign(shop.guestbook, gameDate());
        if (out.guestbook) {
            shop.guestbook = out.guestbook;
            shop.save();
        }
        shop.toast(out.line);
        return true;
    }
}

/** What comes of asking. The seat has been empty for a while. */
PalaceVisit.AUDIENCES = [
    'You request an audience. The seat is empty. It has been since 1868.',
    'You request an audience. A crane on the wall looks at you. That is all.',
    'You request an audience. Somewhere a door slides shut, politely.',
    'You request an audience. You are asked, by nobody, to wait. You wait.',
    'You request an audience. The cushion considers it and declines.',
    'You request an audience. Granted: you may go on standing there.',
];

/** The answer to the `n`th request (0, 1, 2 ...): each in turn, then round again. */
PalaceVisit.audience = (n) => {
    const list = PalaceVisit.AUDIENCES, i = Math.floor(Number(n)) || 0;
    return list[((i % list.length) + list.length) % list.length];
};

/**
 * Sign the visitors' book on game day `date`: { fresh, n, guestbook, line }.
 * `saved` is the book as the shop keeps it ({ date, n }: the day last signed
 * and how many times in all; null when never). Once a day: signed already
 * today, nothing changes and `guestbook` is absent.
 */
PalaceVisit.sign = (saved, date) => {
    const kept = Shop.guestbookOf(saved);
    if (kept && kept.date === date) {
        return { fresh: false, n: kept.n, line: 'You signed the book today already. The ink is dry; your name is still the last in it.' };
    }
    const n = (kept ? kept.n : 0) + 1;
    return {
        fresh: true, n, guestbook: { date, n },
        line: n === 1
            ? 'You sign the visitors\' book. The name above yours is three hundred years old.'
            : `You sign the visitors' book again: visit ${n}. Nobody has signed since you did.`,
    };
};

if (typeof window !== 'undefined') window.PalaceVisit = PalaceVisit;
