/**
 * TempleVisit — the three things to do inside a temple's main hall (issue #213).
 *
 *   bump the incense burner   you waft the smoke over yourself: free, one of a few lines
 *   bump the offering box     a coin from the wallet, as at a shrine (ShrineVisit.OFFERING),
 *                             but nobody rings a bell in here: palms together
 *   bump the fortune drawers  you shake the cylinder and a numbered stick slides out. It is
 *                             the SAME omikuji as a shrine's: ShrineVisit.fortune decides
 *                             it, with the same price, the same odds and the same save
 *                             field, so there is one fortune a game day across every shrine
 *                             and the temple. Only the wording is the temple's.
 *
 * All three are rules in the Interactions table (group 'temple') and answer with
 * the shop's toast: no overlay, no new key, nothing to learn — a bump works the
 * same from the keyboard and from the touch pad. The charm counter, the drum,
 * the bowl bell, the candles, the tied fortunes and the sanctum only say a
 * line: they are `flavour` rules and need nothing from here.
 *
 * One answer per bump: a key held against the burner is the same bump until it
 * is let go, by the rule the offering box uses (ShrineVisit.fresh / .carried).
 *
 * To take it out: delete this file and its line in index.html, the three
 * 'temple' rules in Interactions.js and the three lines in GameScene
 * (constructor, checkNPCInteraction, update). Nothing of its own is saved.
 */
class TempleVisit {
    constructor(scene) {
        this.scene = scene;
        this.bump = null;           // the last bump { cell, at, dx, dy }: a held key bumps every frame
        this.wafted = 0;            // times the smoke was wafted this session: the lines come round in turn
    }

    /** Every frame, with the direction held right now: a bump whose key is still down is still that bump. */
    hold(heading) {
        if (this.bump) this.bump = ShrineVisit.carried(this.bump, this.scene.time.now, heading);
    }

    /** The player bumped a cell: waft the smoke / make the offering / draw the fortune there. True when there was something. */
    check(gridX, gridY) {
        const scene = this.scene, shop = scene.shop;
        const hit = scene.roomManager.interactionAt(gridX, gridY, 'temple');
        if (!hit || !shop) return false;
        const cell = `${gridX},${gridY}`, fresh = ShrineVisit.fresh(this.bump, cell, scene.time.now);
        const from = scene.player || {};
        this.bump = { cell, at: scene.time.now, dx: Math.sign(gridX - from.gridX), dy: Math.sign(gridY - from.gridY) };
        if (!fresh) return true;
        if (hit.kind === 'incense') {
            shop.toast(TempleVisit.waft(this.wafted++));
            return true;
        }
        const out = hit.kind === 'offering'
            ? TempleVisit.offer(shop.money, Math.random())
            : TempleVisit.fortune(shop.omikuji, gameDate(), shop.money, Math.random());
        shop.money = out.money;
        if (out.omikuji) shop.omikuji = out.omikuji;
        shop.save();
        scene.updateHUD();
        shop.toast(out.line);
        return true;
    }
}

/** What the smoke is good for, they say. */
TempleVisit.WAFTS = [
    'You waft the smoke over your head. It is said to make you cleverer. We shall see.',
    'You waft the smoke over your shoulders. The backpack feels lighter. A little.',
    'You waft the smoke over your knees, for the stairs still to come.',
    'You waft the smoke over your wallet. It cannot hurt.',
    'You waft the smoke over your head. Your hair will smell of it until Osaka.',
];

/** The line for the `n`th waft (0, 1, 2 ...): each in turn, then round again. */
TempleVisit.waft = (n) => {
    const list = TempleVisit.WAFTS, i = Math.floor(Number(n)) || 0;
    return list[((i % list.length) + list.length) % list.length];
};

/**
 * An offering from a wallet of `money`: { ok, money, line }. The shrine's
 * rule and price (ShrineVisit.offer, OFFERING yen) and its blessings; with too
 * little, nothing is taken. Only the manner differs: no bell, no clap.
 */
TempleVisit.offer = (money, roll) => {
    const out = ShrineVisit.offer(money, roll);
    const line = out.ok
        ? `¥${ShrineVisit.OFFERING} in the box. Palms together, no clap. ` + ShrineVisit.pick(ShrineVisit.BLESSINGS, roll || 0)
        : `No coin for the box (an offering is ¥${ShrineVisit.OFFERING}). You put your palms together anyway.`;
    return { ok: out.ok, money: out.money, line };
};

/** The number on the stick that falls out for a `roll` in [0, 1): 1 to 100, as the drawers are numbered. */
TempleVisit.stick = (roll) => 1 + Math.min(99, Math.max(0, Math.floor((roll || 0) * 100)));

/**
 * Draw the fortune for game day `date`: { fresh, i, money, omikuji, line },
 * exactly as ShrineVisit.fortune decides it (one a game day wherever it was
 * drawn, FORTUNE_PRICE for a fresh one, the same weights), told the temple's
 * way: the cylinder is shaken, a numbered stick slides out, and the slip is in
 * the drawer with that number. A toast is one line: the wording is kept as
 * short as the shrine's.
 */
TempleVisit.fortune = (saved, date, money, roll) => {
    const out = ShrineVisit.fortune(saved, date, money, roll);
    const words = (i) => { const f = ShrineVisit.FORTUNES[i]; return `${f.rank} (${f.means}). ${f.text}`; };
    let line;
    if (out.fresh) {
        line = `Shake, ¥${ShrineVisit.FORTUNE_PRICE}, stick ${TempleVisit.stick(roll)}: ${words(out.i)}`;
    } else if (out.i >= 0) {
        line = `The drawer stays shut: ${words(out.i)}`;
    } else {
        line = `A fortune is ¥${ShrineVisit.FORTUNE_PRICE}. The cylinder stays on the counter.`;
    }
    return Object.assign({}, out, { line });
};

if (typeof window !== 'undefined') window.TempleVisit = TempleVisit;
