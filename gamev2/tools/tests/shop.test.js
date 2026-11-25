module.exports = ({ test, assert, fs, path, GV2, ctx, game, shopWith, showdownWith }) => {
    test('every catalogue item and every fish has an icon that draws', () => {
        const SHAPES = game('ItemIcons.SHAPES'), pixels = game('ItemIcons.pixels'), specFor = game('ItemIcons.specFor');
        for (const [name, rows] of Object.entries(SHAPES)) {
            assert.strictEqual(rows.length, 16, name);
            for (const row of rows) assert.ok(/^[.oweakbcd]{16}$/.test(row), `${name}: "${row}"`);
        }
        const items = Array.from(game('Shop.DEFAULT_ITEMS.concat(Shop.fishItems())'));
        const drawn = new Set();
        for (const item of items) {
            assert.ok(item.icon && SHAPES[item.icon.shape], `${item.id} names no icon shape`);
            const px = Array.from(pixels(item), row => Array.from(row));
            assert.ok(px.flat().filter(Boolean).length > 40, `${item.id} icon is nearly empty`);
            for (const c of px.flat()) assert.ok(c === null || /^#[0-9a-f]{6}$/.test(c), `${item.id}: ${c}`);
            drawn.add(JSON.stringify(px));
        }
        assert.strictEqual(drawn.size, items.length, 'two items share an identical icon');
        // an item from a config catalogue with no icon gets its category's default
        assert.strictEqual(specFor({ id: 'x', category: 'food' }).shape, game('ItemIcons.DEFAULTS.food.shape'));
        assert.strictEqual(specFor({ id: 'x', effect: {} }).shape, game('ItemIcons.DEFAULTS.drink.shape'));
        assert.strictEqual(specFor({ id: 'x', permanent: true }).shape, game('ItemIcons.DEFAULTS.gear.shape'));
        assert.strictEqual(specFor({ id: 'x', category: 'fish', icon: { shape: 'nope' } }).shape, 'fish');
        assert.strictEqual(specFor({ id: 'x', category: 'mystery' }).shape, game('ItemIcons.DEFAULTS.gear.shape'));
        assert.strictEqual(game('ItemIcons.key')({ id: 'koi' }), 'item-koi');
    });

    test('a catch goes into the bag, sells for its value, and a boot is thrown back', () => {
        const CATCHES = Array.from(game('Fishing.CATCHES')), sellValue = game('Shop.sellValue');
        const byId = (id) => CATCHES.find(c => c.id === id);
        assert.ok(Math.abs(CATCHES.reduce((s, c) => s + c.odds, 0) - 1) < 1e-9, 'odds sum to 1');
        // the value table is the one from before fish were items
        assert.deepStrictEqual(CATCHES.map(c => [c.name, c.value]),
            [['an old boot', 0], ['Funa', 80], ['Koi', 240], ['Unagi', 520], ['Golden Koi', 1500]]);

        const { shop, toasts, saved } = shopWith({ v: 2, money: 1000, items: { 'fishing-rod': 1 }, effects: {}, used: {} });
        assert.deepStrictEqual(Array.from(shop.addCatch(byId('old-boot'))), []);
        assert.deepStrictEqual(Object.keys(shop.items), ['fishing-rod'], 'the boot never reaches the bag');
        shop.addCatch(byId('koi')); shop.addCatch(byId('koi')); shop.addCatch(byId('funa'));
        assert.strictEqual(shop.money, 1000, 'catching pays nothing by itself');
        assert.deepStrictEqual({ ...shop.items }, { 'fishing-rod': 1, koi: 2, funa: 1 });
        assert.deepStrictEqual({ ...saved().items }, { 'fishing-rod': 1, koi: 2, funa: 1 });
        assert.strictEqual(saved().v, 3);
        assert.deepStrictEqual(Array.from(shop.sellable(), i => i.id), ['funa', 'koi'], 'only fish sell');

        for (const c of CATCHES.filter(c => c.value > 0)) assert.strictEqual(sellValue(shop.itemById(c.id), 1), c.value);
        assert.strictEqual(sellValue(shop.itemById('koi'), 3), 720);
        assert.strictEqual(sellValue(shop.itemById('onigiri'), 2), 0, 'shops do not buy their own stock back');
        assert.strictEqual(sellValue(undefined, 2), 0);

        // sell both koi at a counter: the wallet gains exactly their value
        Object.assign(shop, { visible: true, mode: 'sell', kind: 'counter', selected: 0, qty: 1 });
        shop.refreshStock();
        shop.selected = shop.stock.findIndex(i => i.id === 'koi');
        shop.qty = 5;                                  // more than held: clamped
        shop.sell();
        assert.strictEqual(shop.money, 1480);
        assert.strictEqual(shop.items.koi, undefined);
        assert.strictEqual(saved().money, 1480);
        assert.ok(toasts.pop().includes('sold 2× Koi for ¥480'));
        shop.sell(); shop.sell();                      // funa, then nothing left to sell
        assert.strictEqual(shop.money, 1560);
        assert.deepStrictEqual({ ...shop.items }, { 'fishing-rod': 1 });

        // the toast says what it was and where it went
        const msg = game('Fishing.catchMessage');
        assert.ok(/Koi!.*in your bag.*¥240/.test(msg(byId('koi'), '¥240')));
        assert.ok(/old boot.*throw it back/.test(msg(byId('old-boot'), '¥0')));
    });

    test("a room's shopTitle renames its counter list: the Don Takote tills say DON TAKOTE, konbinis KONBINI (#136)", () => {
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const titleFor = game('Shop.titleFor');
        const stores = Object.keys(rooms).filter(k => k.startsWith('DonTakote'));
        assert.ok(stores.length >= 3);
        for (const k of stores) {
            assert.strictEqual(titleFor('counter', rooms[k]), 'DON TAKOTE', k);
            assert.strictEqual(titleFor('drinks', rooms[k]), 'DRINKS', 'shelves keep their own title');
            assert.strictEqual(titleFor('vending', rooms[k]), 'VENDING MACHINE');
        }
        const konbini = Object.keys(rooms).find(k => k.startsWith('Konbini'));
        assert.strictEqual(titleFor('counter', rooms[konbini]), 'KONBINI');
        assert.strictEqual(titleFor('izakaya', rooms.Izakaya), 'IZAKAYA');
        assert.strictEqual(titleFor('counter', undefined), 'KONBINI');
    });

    test('a fish is only eaten grilled, as a food effect, and the first rare one is an achievement', () => {
        const CATCHES = Array.from(game('Fishing.CATCHES'));
        const { shop, toasts } = shopWith({ money: 200, items: {} });
        shop.scene.player = { sprite: { setTint() {}, clearTint() {}, setScale() {}, scale: 1 } };
        shop.scene.tweens = { add: () => ({ stop() {} }) };
        shop.scene.time = { delayedCall() {} };
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'funa'))), []);
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'unagi'))), ['Big Catch']);
        assert.deepStrictEqual(Array.from(shop.addCatch(CATCHES.find(c => c.id === 'golden-koi'))), [], 'only the first time');
        const progress = Array.from(shop.scene.achievementManager.itemProgress(), a => a.name);
        assert.deepStrictEqual(progress, ['Taste Tester', 'Regular Customer', 'Big Catch']);

        shop.use('unagi');                               // from the Items screen: raw
        assert.strictEqual(shop.items.unagi, 1);
        assert.ok(/sell it/.test(toasts.pop()));
        assert.deepStrictEqual(Object.keys(shop.effects), []);
        shop.use('unagi', { grilled: true });
        assert.strictEqual(shop.items.unagi, undefined);
        assert.strictEqual(shop.effects.food.name, 'Grilled Unagi');
        assert.strictEqual(shop.buff('speed'), 1.4);
        assert.ok(/Grilled Unagi: speed \+40% for 3:00/.test(toasts.pop()));
        // fish are not part of "try every food and drink"
        assert.strictEqual(shop.consumables().length, 12);
        assert.ok(shop.consumables().every(i => !i.sell));
    });

    test('saves from before fish load untouched, and nobody loses money', () => {
        // issue #12 blob
        let s = shopWith({ money: 1234, items: { 'zone-energy': 2 } });
        assert.strictEqual(s.shop.money, 1234);
        assert.deepStrictEqual({ ...s.shop.items }, { 'zone-energy': 2 });
        assert.deepStrictEqual({ ...s.shop.caught }, {});
        // issue #46 blob, with a running effect and counters
        const until = Date.now() + 20000;
        s = shopWith({ v: 2, money: 77, items: { 'fishing-rod': 1, onigiri: 3 }, used: { onigiri: 4 },
            effects: { food: { id: 'onigiri', until } } });
        assert.strictEqual(s.shop.money, 77);
        assert.deepStrictEqual({ ...s.shop.items }, { 'fishing-rod': 1, onigiri: 3 });
        assert.deepStrictEqual({ ...s.shop.used }, { onigiri: 4 });
        assert.strictEqual(s.shop.effects.food.until, until);
        assert.deepStrictEqual(Array.from(s.shop.sellable()), []);
        s.shop.save();
        assert.deepStrictEqual({ ...s.saved() }.money, 77);
        // v3 round trip, including a grilled-fish effect
        s = shopWith({ v: 3, money: 10, items: { koi: 2 }, caught: { koi: 5, unagi: 1 },
            effects: { food: { id: 'koi', until } } });
        assert.deepStrictEqual({ ...s.shop.caught }, { koi: 5, unagi: 1 });
        assert.strictEqual(s.shop.effects.food.name, 'Grilled Koi');
        assert.ok(s.shop.scene.achievementManager.fishingProgress()[0].complete);
        // no save at all, and a corrupt one: the starting wallet
        assert.strictEqual(shopWith(null).shop.money, 5000);
        assert.strictEqual(shopWith('{not json').shop.money, 5000);
    });

    test('the showdown stake: the pool scales, and only what the wallet covers is on offer', () => {
        const STAKES = Array.from(game('DrinkingGame.STAKES')), pool = game('DrinkingGame.pool');
        const next = game('DrinkingGame.nextStake'), affordable = game('DrinkingGame.affordable');
        assert.deepStrictEqual(STAKES.map(o => o.stake), [0, 500, 2000]);
        assert.deepStrictEqual(STAKES.map(o => pool(o, 1)), [100, 1000, 4000]);
        assert.deepStrictEqual(STAKES.map(o => pool(o, 1.5)), [150, 1250, 5000], 'Karaage adds to the winnings, not the stake');
        for (const o of STAKES) assert.ok(pool(o, 1) > o.stake, 'a win always beats getting the stake back');
        assert.deepStrictEqual(STAKES.map(o => affordable(o, 499)), [true, false, false]);
        assert.deepStrictEqual(STAKES.map(o => affordable(o, 500)), [true, true, false]);
        assert.strictEqual(next(0, 1, 5000), 1);
        assert.strictEqual(next(1, 1, 5000), 2);
        assert.strictEqual(next(2, 1, 5000), 2, 'no wrap');
        assert.strictEqual(next(0, -1, 5000), 0);
        assert.strictEqual(next(0, 1, 499), 0, 'nothing affordable to the right');
        assert.strictEqual(next(1, 1, 1999), 1);
        assert.strictEqual(next(2, -1, 5000), 1);
    });

    test('the showdown: losing costs exactly the stake, winning pays the pool, leaving first is free', () => {
        const STAKES = Array.from(game('DrinkingGame.STAKES'));
        const round = (stakeIndex, money, how, opts = {}) => {
            const { g, shop } = showdownWith(money, opts.player || 'bailey', opts.bonus);
            g.setStake(stakeIndex);
            if (how === 'leave-first') { g.leave(); return shop.money - money; }
            g.begin();
            if (how === 'walk-out') { g.leave(); return shop.money - money; }
            const presses = { win: 200, lose: 0 }[how];
            if (how === 'draw') g.playerScore = g.opponentScore = 7;
            else for (let i = 0; i < presses; i++) g.press();
            if (how !== 'draw' && g.opponent === 'damian') g.opponentScore = 75;
            g.scene.time.now = g.deadline;             // the buzzer
            g.finish();
            assert.strictEqual(g.staked, 0);
            return shop.money - money;
        };
        STAKES.forEach((o, i) => {
            assert.strictEqual(round(i, 5000, 'win'), o.winnings, `${o.id} win`);
            assert.strictEqual(round(i, 5000, 'win', { bonus: 1.5 }), o.winnings * 1.5, `${o.id} win with Karaage`);
            assert.strictEqual(round(i, 5000, 'lose'), 0 - o.stake, `${o.id} loss`);
            assert.strictEqual(round(i, 5000, 'draw'), 0, `${o.id} draw`);
            assert.strictEqual(round(i, 5000, 'walk-out'), 0 - o.stake, `${o.id} walked out mid-round`);
            assert.strictEqual(round(i, 5000, 'leave-first'), 0, `${o.id} left before the round`);
            // the Bailey mirror: as Damian you always lose by ten, and it costs the stake
            assert.strictEqual(round(i, 5000, 'win', { player: 'damian' }), 0 - o.stake, `${o.id} vs Bailey`);
        });
        // the buzzer can ring with the clock a hair short of the deadline: Bailey still finds all ten (#132)
        const early = showdownWith(5000, 'damian').g;
        early.begin();
        for (let i = 0; i < 40; i++) early.press();
        early.scene.time.now = early.deadline - 3;
        early.finish();
        assert.deepStrictEqual([early.playerScore, early.opponentScore, early.baileyBonus], [40, 50, 10]);
        // a stake the wallet cannot cover is never taken: the pick stays on the friendly round
        assert.strictEqual(round(2, 1999, 'lose'), 0);
        assert.strictEqual(round(1, 499, 'win'), 100);
        assert.strictEqual(round(1, 500, 'lose'), -500, 'the whole wallet can ride on it');
        // picking a stake the wallet cannot cover says why, and changes nothing
        const { g, shop } = showdownWith(1500, 'bailey');
        const said = [];
        shop.toast = (m) => said.push(m);
        g.setStake(2);
        assert.strictEqual(g.stakeIndex, 0);
        assert.ok(/BIG TAB needs .*2,?000.*1,?500/.test(said[0]), said[0]);
        // the result screen: ENTER leaves at once, SPACE (the touch A button) only after a beat
        g.begin(); g.scene.time.now = g.deadline; g.finish();
        g.keys = { space: {}, enter: {}, esc: {}, left: {}, right: {}, a: {}, d: {} };
        ctx.Phaser = { Input: { Keyboard: { JustDown: (k) => k === g.keys.space } } };
        try {
            g.handleInput();
            assert.strictEqual(g.state, 'result', 'a late mash does not dismiss the result');
            g.scene.time.now += game('DrinkingGame.RESULT_GRACE_MS');
            g.handleInput();
            assert.strictEqual(g.state, 'idle');
        } finally { delete ctx.Phaser; }
        // a toast stays up long enough to read: the achievement waits for the whole catch line
        const toastMs = game('Shop.toastMs');
        assert.strictEqual(toastMs('ok'), 1800);
        assert.ok(toastMs(game('Fishing.catchMessage')({ name: 'Unagi', value: 520 }, '¥520')) > 3000);
    });
};
