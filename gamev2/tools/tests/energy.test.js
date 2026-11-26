// Energy and the konbini stamp card (issue #209): the rules in src/Energy.js and what the Shop does with them.
module.exports = ({ test, assert, game, realConfig, shopWith }) => {
    const E = () => game('Energy'), S = () => game('Stamps');
    // shopWith, plus what Shop.use() pokes for its little "gulp"
    const eater = (saved) => {
        const s = shopWith(saved);
        s.shop.scene.player = { sprite: { setTint() {}, clearTint() {}, setScale() {}, scale: 1 } };
        s.shop.scene.tweens = { add: () => ({ stop() {} }) };
        return s;
    };

    test('energy: a full meter lasts 4-6 minutes of walking and never goes below zero', () => {
        const En = E();
        let e = En.MAX, cells = 0;
        while (e > 0) { e = En.afterStep(e); cells++; assert.ok(cells < 1e5); }
        const minutes = cells / 5 / 60;                 // a walked cell is 200ms (DEFAULT_MOVE_DURATION)
        assert.ok(minutes >= 4 && minutes <= 6.01, `${minutes} min`);
        assert.ok(Math.abs(cells - En.CELLS) <= 1);
        assert.strictEqual(En.afterStep(0), 0);
        assert.strictEqual(En.afterStep(0.01), 0);
        assert.ok(Math.abs(En.stepCost(En.DEBUG_FACTOR) - En.stepCost() * En.DEBUG_FACTOR) < 1e-12);
    });

    test('energy: only the sprint depends on it — off when peckish, a little faster when well fed', () => {
        const En = E();
        assert.strictEqual(En.sprintMultiplier(0), 1);
        assert.strictEqual(En.sprintMultiplier(0.5), En.SPRINT);
        assert.strictEqual(En.sprintMultiplier(En.WELL_FED - 0.1), 2);
        assert.strictEqual(En.sprintMultiplier(En.WELL_FED), En.WELL_FED_SPRINT);
        assert.ok(En.WELL_FED_SPRINT > En.SPRINT && En.WELL_FED_SPRINT <= 2.5);
        assert.deepStrictEqual([0, 1, En.LOW, En.LOW + 1, En.WELL_FED, 100].map(En.level),
            ['peckish', 'low', 'low', 'ok', 'fed', 'fed']);
        assert.deepStrictEqual([0, 0.1, 10, 30, 50, 70, 90, 100].map(En.segments), [0, 1, 1, 2, 3, 4, 5, 5]);
        assert.notStrictEqual(En.color(0), En.color(10));
        assert.notStrictEqual(En.color(50), En.color(90));
    });

    test('energy: every food and drink restores something sensible, gear nothing', () => {
        const En = E(), items = Array.from(game('Shop.DEFAULT_ITEMS.concat(Shop.fishItems())'));
        const v = (id) => En.valueOf(items.find(i => i.id === id));
        for (const i of items) {
            if (i.permanent) assert.strictEqual(En.valueOf(i), 0, i.id);
            else assert.ok(En.valueOf(i) > 0 && En.valueOf(i) <= En.MAX, i.id);
        }
        assert.ok(v('onigiri') > v('green-tea') * 2, 'an onigiri is worth more than a tea');
        assert.ok(v('nikuman') > v('onigiri'), 'the hot snack fills most');
        for (const id of ['highball', 'nama-beer', 'vodka-redbull']) assert.ok(v(id) <= 10, `${id}: alcohol gives little`);
        const foods = items.filter(i => i.category === 'food'), drinks = items.filter(i => i.category === 'drink');
        assert.ok(Math.min(...foods.map(En.valueOf)) >= Math.max(...drinks.map(En.valueOf)), 'any food beats any drink');
        assert.strictEqual(v('koi'), En.DEFAULTS.fish, 'a grilled fish is a meal');
        // a config catalogue that says nothing gets its category's value
        assert.strictEqual(En.valueOf({ id: 'x', category: 'food' }), En.DEFAULTS.food);
        assert.strictEqual(En.valueOf({ id: 'x', effect: {} }), En.DEFAULTS.drink);
        assert.strictEqual(En.valueOf(null), 0);
        assert.strictEqual(En.afterEating(80, { energy: 45 }), 100);
        assert.strictEqual(En.afterEating(0, { energy: 45 }), 45);
    });

    test('energy: water is free, brings the sprint back and never makes you well fed', () => {
        const En = E();
        assert.strictEqual(En.afterWater(0), En.WATER);
        assert.ok(En.sprintMultiplier(En.afterWater(0)) === En.SPRINT);
        let e = 0;
        for (let i = 0; i < 20; i++) e = En.afterWater(e);
        assert.strictEqual(e, En.WATER_CAP);
        assert.ok(En.WATER_CAP < En.WELL_FED);
        assert.strictEqual(En.afterWater(90), 90, 'it never lowers a fuller meter');
        // the wallet's side of the safety net: the cheapest thing a machine sells is a small part of a new wallet
        const vending = Array.from(game('Shop.DEFAULT_ITEMS')).filter(i => i.where === 'vending');
        assert.ok(Math.min(...vending.map(i => i.price)) <= 200);
    });

    test('energy: the hint is said once, the peckish line every time the meter empties', () => {
        const En = E();
        assert.strictEqual(En.notice(60, 59.9, false), null);
        assert.strictEqual(En.notice(En.LOW + 0.01, En.LOW, false).kind, 'low');
        assert.strictEqual(En.notice(En.LOW + 0.01, En.LOW, true), null);
        assert.strictEqual(En.notice(0.01, 0, true).kind, 'peckish');
        assert.strictEqual(En.notice(0, 0, true), null);
        // sprint held on an empty meter says it again, at most once per REMIND_MS, and only when empty
        assert.strictEqual(En.remind(0, 5000, undefined), true);
        assert.strictEqual(En.remind(0, 5000 + En.REMIND_MS - 1, 5000), false);
        assert.strictEqual(En.remind(0, 5000 + En.REMIND_MS, 5000), true);
        assert.strictEqual(En.remind(0.5, 5000, undefined), false);
        assert.ok(En.REMIND_MS >= 5000);
        // a save loaded at zero: holding sprint queues the line once, not once a frame; none with energy
        const z = shopWith({ v: 4, money: 100, items: {}, energy: 0 });
        z.shop.sprintHeld(); z.shop.sprintHeld();
        assert.deepStrictEqual(Array.from(z.shop.notices), [En.PECKISH]);
        const f = shopWith({ v: 4, money: 100, items: {}, energy: 50 });
        f.shop.sprintHeld();
        assert.deepStrictEqual(Array.from(f.shop.notices), []);
        assert.ok(/konbini/.test(En.HINT) && /vending/.test(En.HINT));
        for (const line of [En.HINT, En.PECKISH]) assert.ok(line.length <= 90, 'one line: ' + line);
    });

    test('energy: an old save loads full, the level is saved, and walking, eating and water move it', () => {
        const En = E();
        for (const old of [null, { money: 300, items: {} }, { v: 3, money: 300, items: {} }, { v: 4, money: 1, energy: 'x' }]) {
            const s = shopWith(old);
            assert.strictEqual(s.shop.energy, En.MAX);
            assert.deepStrictEqual({ ...s.shop.stamps }, {});
            if (old && old.money === 300) assert.strictEqual(s.shop.money, 300, 'the wallet is never changed by loading');
        }
        let s = eater({ v: 4, money: 500, items: { onigiri: 1, 'green-tea': 1 }, energy: 26, stamps: { KonbiniPark1: 1 } });
        assert.strictEqual(s.shop.energy, 26);
        assert.strictEqual(s.shop.sprintMultiplier(), 2);
        // walk it down: the hint is queued once, then the peckish line, and it stops at zero
        for (let i = 0; i < 600; i++) s.shop.walked();
        assert.strictEqual(s.shop.energy, 0);
        assert.strictEqual(s.shop.sprintMultiplier(), 1);
        assert.deepStrictEqual(Array.from(s.shop.notices), [En.HINT, En.PECKISH]);
        assert.strictEqual(s.saved().energy, 0);
        assert.strictEqual(s.saved().hints.low, 1);
        assert.strictEqual(s.saved().v, 4);
        // tea, then the onigiri: the toast says what it gave and the stale lines are dropped
        s.shop.use('green-tea');
        assert.strictEqual(s.shop.energy, 15);
        assert.ok(/energy \+15/.test(s.toasts.pop()));
        assert.deepStrictEqual(Array.from(s.shop.notices), []);
        assert.strictEqual(s.shop.sprintMultiplier(), 2);
        s.shop.use('onigiri');
        assert.strictEqual(s.shop.energy, 60);
        assert.strictEqual(s.saved().energy, 60);
        // the hint is not said a second time
        for (let i = 0; i < 2000; i++) s.shop.walked();
        assert.deepStrictEqual(Array.from(s.shop.notices), [En.PECKISH]);
        // free water
        s.shop.drinkWater();
        assert.strictEqual(s.shop.energy, En.WATER);
        assert.ok(/on the house/.test(s.toasts.pop()));
        assert.deepStrictEqual(Array.from(s.shop.notices), []);
        s.shop.drinkWater(); s.shop.drinkWater();
        assert.strictEqual(s.shop.energy, En.WATER_CAP);
        assert.strictEqual(s.shop.money, 500, 'water costs nothing');
        // a reload keeps it
        s = shopWith(s.saved());
        assert.strictEqual(s.shop.energy, En.WATER_CAP);
        assert.strictEqual(s.shop.hints.low, 1);
        // a full meter is not topped past the top
        s = eater({ v: 4, money: 0, items: { nikuman: 1 }, energy: 90 });
        s.shop.use('nikuman');
        assert.strictEqual(s.shop.energy, 100);
        assert.ok(/energy \+10/.test(s.toasts.pop()));
    });

    test('stamp card: every store in config is on it, and a purchase stamps the place once', () => {
        const St = S(), config = realConfig();
        const stores = Array.from(St.stores(config));
        const expected = Object.keys(config.rooms).filter(k => config.rooms[k].interior && config.rooms[k].shopEnabled !== false);
        assert.deepStrictEqual(stores.map(s => s.id), expected);
        assert.ok(stores.length >= 14, 'the konbini and Don Takote stores');
        assert.ok(stores.some(s => s.id === 'KonbiniSendai1') && stores.some(s => s.id === 'DonTakoteOsaka'));
        assert.ok(!stores.some(s => s.id === 'Izakaya'), 'the izakaya is no store');
        for (const s of stores) assert.ok(s.name && s.name !== s.id, `${s.id} has a display name`);
        // a new town's konbini counts by itself
        const more = { rooms: Object.assign({}, config.rooms, { KonbiniTestTown1: { interior: true, name: '7-Eleven · Test Town' } }) };
        assert.strictEqual(St.stores(more).length, stores.length + 1);
        assert.strictEqual(St.progress(more, Object.fromEntries(stores.map(s => [s.id, 1]))).complete, false);

        const konbini = config.rooms.KonbiniPark1, izakaya = config.rooms.Izakaya, street = config.rooms.Market;
        assert.strictEqual(St.placeFor('counter', 'KonbiniPark1', konbini), 'KonbiniPark1');
        assert.strictEqual(St.placeFor('snacks', 'KonbiniPark1', konbini), 'KonbiniPark1');
        assert.strictEqual(St.placeFor('vending', 'Market', street), 'vending:Market');
        assert.strictEqual(St.placeFor('izakaya', 'Izakaya', izakaya), null);
        assert.strictEqual(St.placeFor('vending', null, undefined), null);
    });

    test('stamp card: milestones pay once as the count reaches them, and the achievement needs every store', () => {
        const St = S(), config = realConfig();
        const ats = Array.from(St.MILESTONES, m => m.at);
        assert.deepStrictEqual(ats, ats.slice().sort((a, b) => a - b));
        assert.ok(ats[0] <= 3, 'the first reward comes early');
        const items = Array.from(game('Shop.DEFAULT_ITEMS'));
        for (const m of St.MILESTONES) {
            assert.ok(m.yen > 0 || m.item, 'a milestone gives something');
            if (m.item) assert.ok(items.some(i => i.id === m.item), m.item);
        }
        assert.deepStrictEqual(Array.from(St.rewards(1, 2), m => m.at), [2]);
        assert.deepStrictEqual(Array.from(St.rewards(2, 3)), []);
        assert.deepStrictEqual(Array.from(St.rewards(2, 2)), [], 'the same count pays nothing again');
        assert.strictEqual(St.next(0).at, 2);
        assert.strictEqual(St.next(ats[ats.length - 1]), null);
        assert.strictEqual(St.describe({ yen: 200 }, x => x, n => '¥' + n), '¥200 back');
        assert.strictEqual(St.describe({ yen: 1000, item: 'nikuman' }, () => 'Nikuman', n => '¥' + n), '¥1000 back and a free Nikuman');
        assert.deepStrictEqual({ ...St.clean({ a: 1, b: 0, c: true }) }, { a: 1, c: 1 });
        assert.strictEqual(St.count(St.clean('junk')), 0);

        const stores = Array.from(St.stores(config));
        const all = Object.fromEntries(stores.map(s => [s.id, 1]));
        assert.strictEqual(St.progress(config, {}).value, 0);
        assert.strictEqual(St.progress(config, { 'vending:Market': 1, 'vending:Park': 1 }).value, 0, 'machines are not stores');
        const but = Object.assign({}, all); delete but[stores[0].id];
        assert.strictEqual(St.progress(config, but).complete, false);
        assert.deepStrictEqual({ ...St.progress(config, all) }, { name: 'Konbini Pilgrim',
            desc: 'Buy something at every konbini and discount store', value: stores.length, total: stores.length, complete: true });
    });

    test('stamp card: buying in the shop stamps, pays the reward into the wallet and says so', () => {
        const config = realConfig();
        const at = (s, room, district) => {
            s.shop.scene.config = config;
            s.shop.scene.roomManager = { currentRoom: room, currentDistrict: () => district || room };
        };
        const buy = (s, kind, id) => {
            Object.assign(s.shop, { visible: true, mode: 'buy', kind, selected: 0, qty: 1 });
            s.shop.refreshStock();
            s.shop.selected = s.shop.stock.findIndex(i => i.id === id);
            s.shop.buy(false);
            return s.toasts.pop();
        };
        const s = shopWith({ v: 4, money: 2000, items: {}, energy: 50 });
        at(s, 'KonbiniPark1');
        assert.ok(/stamp 1 on your card$/.test(buy(s, 'counter', 'onigiri')));
        assert.strictEqual(s.shop.money, 1820);
        assert.ok(!/stamp/.test(buy(s, 'snacks', 'onigiri')), 'the same store stamps once');
        assert.strictEqual(s.shop.energy, 50, 'buying is not eating');
        at(s, 'TokyoCity', 'Market');
        const second = buy(s, 'vending', 'green-tea');
        assert.ok(/stamp 2 on your card: ¥200 back!$/.test(second), second);
        assert.strictEqual(s.shop.money, 1820 - 180 - 160 + 200);
        assert.deepStrictEqual({ ...s.saved().stamps }, { KonbiniPark1: 1, 'vending:Market': 1 });
        at(s, 'Izakaya');
        assert.ok(!/stamp/.test(buy(s, 'izakaya', 'edamame')), 'the izakaya has no stamp');
        // the fifth stamp is a free onigiri
        Object.assign(s.shop.stamps, { a: 1, b: 1 });
        at(s, 'KonbiniSendai1');
        const had = s.shop.items.onigiri;
        assert.ok(/stamp 5 on your card: a free Onigiri!$/.test(buy(s, 'counter', 'green-tea')));
        assert.strictEqual(s.shop.items.onigiri, had + 1);
        // every store stamped: the achievement is announced once the screen is free
        for (const st of game('Stamps.stores')(config)) if (st.id !== 'DonTakoteOsaka') s.shop.stamps[st.id] = 1;
        s.shop.money = 5000;
        at(s, 'DonTakoteOsaka');
        buy(s, 'counter', 'green-tea');
        assert.ok(Array.from(s.shop.notices).includes('★ achievement: Konbini Pilgrim'));
        assert.ok(s.shop.scene.achievementManager.stampProgress()[0].complete);
    });
};
