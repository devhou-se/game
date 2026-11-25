/**
 * DrinkingGame — 15-second space-bar mash at the Izakaya table.
 *
 * Bump the configured table to open the challenge, then press SPACE as many
 * times as possible before the clock reaches zero. Damian plays at a steady
 * simulated cadence. If the player is Damian, Bailey takes his place and his
 * score is always exactly ten higher than the player's — the house gimmick.
 *
 * Before the round the player picks a stake (issue #84) with ←/→ from
 * DrinkingGame.STAKES: a friendly round for nothing, or a tab they put money
 * on. The stake leaves the wallet as the round starts; the winner takes the
 * pool (the stake back plus the winnings, which is where Karaage's bonus
 * goes), a draw hands the stake back and a loss — or walking out mid-round —
 * costs exactly the stake. Leaving before the round starts costs nothing.
 */
class DrinkingGame {
    constructor(scene) {
        this.scene = scene;
        this.state = 'idle';       // idle | ready | playing | result
        this.objs = [];
        this.playerScore = 0;
        this.opponentScore = 0;
        this.clockEvent = null;
        this.finishEvent = null;
        this.opponentEvent = null;

        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({
            space: K.SPACE, enter: K.ENTER, esc: K.ESC,
            left: K.LEFT, right: K.RIGHT, a: K.A, d: K.D,
        });
        this.stakeIndex = 0;       // which of DrinkingGame.STAKES is picked
        this.staked = 0;           // yen of the player's riding on the round in play
    }

    static opponentFor(playerName) {
        return playerName === 'damian' ? 'bailey' : 'damian';
    }

    currentPlayer() {
        return (this.scene.player.baseSpriteKey || '').replace(/_(front|back|side)$/, '');
    }

    displayName(name) {
        return name.charAt(0).toUpperCase() + name.slice(1);
    }

    wallet() { return this.scene.shop ? this.scene.shop.money : 0; }

    /** The stake option picked on the ready screen. */
    stake() { return DrinkingGame.STAKES[this.stakeIndex]; }

    /** What a win pays right now — karaage (issue #46) fattens the pot. */
    winPrize() {
        const bonus = this.scene.shop ? this.scene.shop.buff('prizeBonus') : 1;
        return DrinkingGame.pool(this.stake(), bonus);
    }

    prizeLabel(amount = this.winPrize()) {
        return this.scene.shop ? this.scene.shop.fmt(amount) : `¥${amount}`;
    }

    /** Apply a result to the persistent wallet and return the actual delta. */
    adjustWallet(delta) {
        if (!this.scene.shop) return 0;
        const before = this.scene.shop.money;
        this.scene.shop.money = Math.max(0, before + delta);
        this.scene.shop.save();
        this.scene.updateHUD();
        return this.scene.shop.money - before;
    }

    isActive() { return this.state !== 'idle'; }

    /** Open the game only when the player bumps a configured trigger cell. */
    checkStart(gridX, gridY) {
        if (this.isActive() || this.scene.roomManager.isTransitioning) return false;
        const roomKey = this.scene.roomManager.currentRoom;
        const roomConfig = this.scene.config.rooms[roomKey] || {};
        const settings = roomConfig.drinkingGame;
        if (!Interactions.find({}, roomConfig, gridX, gridY, { group: 'drinking-game' })) return false;

        const JD = Phaser.Input.Keyboard.JustDown;
        Object.values(this.keys).forEach(JD);   // a held direction must not move the stake
        this.durationMs = settings.durationMs || DrinkingGame.ROUND_MS;
        this.opponent = DrinkingGame.opponentFor(this.currentPlayer());
        this.resetScores();
        // last time's stake stays picked while the wallet still covers it
        if (!DrinkingGame.affordable(this.stake(), this.wallet())) this.stakeIndex = 0;
        this.staked = 0;
        this.state = 'ready';
        this.render();
        return true;
    }

    resetScores() {
        this.playerScore = 0;
        this.opponentScore = 0;
        this.baileyBonus = 0;
    }

    /** Pick a stake on the ready screen (only one the wallet covers). */
    setStake(index) {
        if (this.state !== 'ready') return;
        if (!DrinkingGame.affordable(DrinkingGame.STAKES[index], this.wallet())) return this.explainStake(index);
        this.stakeIndex = index;
        this.paintStakes();
    }

    /** Say why a greyed-out stake cannot be picked. */
    explainStake(index) {
        const option = DrinkingGame.STAKES[index];
        if (!option || !this.scene.shop) return;
        this.scene.shop.toast(`${option.label} needs ${this.prizeLabel(option.stake)} — you have ${this.prizeLabel(this.wallet())}`);
    }

    /** The ready screen's stake row and the line that says what is at risk. */
    paintStakes() {
        const ready = this.state === 'ready', money = this.wallet();
        (this.stakeTexts || []).forEach((t, i) => {
            const option = DrinkingGame.STAKES[i], picked = i === this.stakeIndex;
            t.setVisible(ready);
            t.setText(picked ? `[ ${DrinkingGame.stakeLabel(option, this.prizeLabel(option.stake))} ]`
                             : DrinkingGame.stakeLabel(option, this.prizeLabel(option.stake)));
            t.setFill(picked ? '#ffff00' : (DrinkingGame.affordable(option, money) ? '#ffffff' : '#6b5a4c'));
        });
        if (!ready || !this.prizeText) return;
        const option = this.stake(), pool = this.prizeLabel();
        const helping = this.scene.shop
            ? this.scene.shop.activeEffects().filter(e => e.prizeBonus).map(e => ` · ${e.name} bonus`).join('') : '';
        this.prizeText.setText((option.stake
            ? `YOUR STAKE ${this.prizeLabel(option.stake)} · WINNER TAKES THE POOL ${pool}`
            : `FRIENDLY ROUND · NOTHING TO LOSE · WIN ${pool}`) + helping);
    }

    begin() {
        this.clearTimers();
        this.resetScores();
        // the stake goes on the table as the round starts
        this.staked = Math.abs(this.adjustWallet(-this.stake().stake));
        // food & drink buffs (issue #46) are locked in as the round starts:
        // a head start in gulps (Bailey, as ever, matches it) and the pot
        const headStart = this.scene.shop ? this.scene.shop.buff('headStart') : 0;
        this.playerScore = headStart;
        if (this.opponent === 'bailey') this.opponentScore = headStart;
        this.prize = this.winPrize();
        this.state = 'playing';
        this.startedAt = this.scene.time.now;
        this.deadline = this.startedAt + this.durationMs;
        // against Bailey the head start buys nothing — say so rather than brag
        this.statusText.setText(Hints.text(this.scene, !headStart ? 'MASH SPACE!'
            : this.opponent === 'bailey' ? 'MASH SPACE!  BAILEY MATCHES YOUR HEAD START'
            : `MASH SPACE!  +${headStart} HEAD START`));
        this.hintText.setText(Hints.text(this.scene,
            this.staked ? 'SPACE: drink · ESC: give up (the stake is lost)' : 'SPACE: drink · ESC: give up'));
        this.paintStakes();
        this.prizeText.setText(`PRIZE POOL: ${this.prizeLabel(this.prize)}` +
            (this.staked ? ` · YOUR STAKE ${this.prizeLabel(this.staked)}` : ''));
        this.updateClock();
        this.paintScores();

        this.clockEvent = this.scene.time.addEvent({
            delay: 100,
            loop: true,
            callback: () => this.updateClock(),
        });
        this.finishEvent = this.scene.time.delayedCall(this.durationMs, () => this.finish());
        if (this.opponent === 'damian') this.scheduleDamianPress();
        else if (this.opponent === 'bailey') this.scheduleBaileyBonus();
    }

    /** Damian's varied but deterministic cadence averages about 5 presses/s. */
    scheduleDamianPress() {
        if (this.state !== 'playing' || this.opponent !== 'damian') return;
        const pattern = DrinkingGame.DAMIAN_PRESS_PATTERN;
        const delay = pattern[this.opponentScore % pattern.length];
        this.opponentEvent = this.scene.time.delayedCall(delay, () => {
            if (this.state !== 'playing') return;
            this.opponentScore++;
            this.paintScores();
            this.scheduleDamianPress();
        });
    }

    /** Bailey mirrors every player press and earns up to ten timed bonuses. */
    scheduleBaileyBonus() {
        if (this.state !== 'playing' || this.opponent !== 'bailey' ||
            this.baileyBonus >= DrinkingGame.BAILEY_MAX_BONUS) return;
        this.opponentEvent = this.scene.time.delayedCall(DrinkingGame.BAILEY_BONUS_MS, () => {
            if (this.state !== 'playing') return;
            this.baileyBonus++;
            this.opponentScore++;
            this.paintScores();
            this.scheduleBaileyBonus();
        });
    }

    updateClock() {
        if (this.state !== 'playing') return;
        const remainingMs = Math.max(0, this.deadline - this.scene.time.now);
        this.timerText.setText(`${(remainingMs / 1000).toFixed(1)}s`);
    }

    press() {
        if (this.state !== 'playing') return;
        this.playerScore++;
        if (this.opponent === 'bailey') this.opponentScore++;
        this.paintScores();
    }

    finish() {
        if (this.state !== 'playing') return;
        if (this.opponent === 'bailey') {
            // The finish event is registered before Bailey's final timed bonus.
            // Reconcile bonuses earned by elapsed time so a 15-second round
            // reliably awards the tenth bonus at the buzzer.
            const elapsed = this.scene.time.now >= this.deadline
                ? this.durationMs
                : Math.max(0, this.scene.time.now - this.startedAt);
            const earned = Math.min(DrinkingGame.BAILEY_MAX_BONUS,
                Math.floor(elapsed / DrinkingGame.BAILEY_BONUS_MS));
            const missing = Math.max(0, earned - this.baileyBonus);
            this.baileyBonus += missing;
            this.opponentScore += missing;
        }
        this.clearTimers();
        this.state = 'result';
        this.resultAt = this.scene.time.now;
        this.timerText.setText('TIME!');
        this.rulesText.setText('FINAL SCORES · THE ROUND IS OVER');
        this.paintScores();

        if (this.playerScore > this.opponentScore) {
            this.statusText.setText(`YOU WIN BY ${this.playerScore - this.opponentScore}!`);
            const won = this.adjustWallet(this.prize);
            this.prizeText.setText(`YOU TAKE THE POOL  +${this.prizeLabel(won)}`);
        } else if (this.playerScore === this.opponentScore) {
            this.statusText.setText('A DRAW — KANPAI!');
            this.adjustWallet(this.staked);
            this.prizeText.setText(this.staked ? 'DRAW  STAKE RETURNED' : 'DRAW  NO WALLET CHANGE');
        } else {
            this.statusText.setText(this.opponent === 'bailey' ? 'BAILEY SOMEHOW FINDS TEN MORE.'
                : `${this.displayName(this.opponent).toUpperCase()} WINS BY ${this.opponentScore - this.playerScore}.`);
            // the stake left the wallet when the round began: nothing more to pay
            this.prizeText.setText(this.staked ? `STAKE LOST  -${this.prizeLabel(this.staked)}`
                                               : 'FRIENDLY ROUND  NOTHING LOST');
        }
        this.staked = 0;
        this.hintText.setText(Hints.text(this.scene, 'ENTER/ESC: leave'));
    }

    clearTimers() {
        for (const event of [this.clockEvent, this.finishEvent, this.opponentEvent]) {
            if (event) event.remove();
        }
        this.clockEvent = null;
        this.finishEvent = null;
        this.opponentEvent = null;
    }

    hide() {
        this.clearTimers();
        this.state = 'idle';
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.playerBar = null;
        this.opponentBar = null;
        this.stakeTexts = null;
        this.prizeText = null;
    }

    /** ESC: free before the round and after it; mid-round the stake stays on the table. */
    leave() {
        const forfeit = this.state === 'playing' ? this.staked : 0;
        this.staked = 0;
        this.hide();
        if (forfeit && this.scene.shop) this.scene.shop.toast(`you walked out mid-round — stake lost (-${this.prizeLabel(forfeit)})`);
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.leave();
        const space = JD(k.space);
        const enter = JD(k.enter);
        const left = JD(k.left) || JD(k.a), right = JD(k.right) || JD(k.d);
        if (this.state === 'ready' && left !== right) {
            const dir = left ? -1 : 1, next = DrinkingGame.nextStake(this.stakeIndex, dir, this.wallet());
            // nowhere to go that way: if a dearer stake is there, say why not
            return next === this.stakeIndex ? this.explainStake(this.stakeIndex + dir) : this.setStake(next);
        }
        if (this.state === 'ready' && (space || enter)) return this.begin();
        if (this.state === 'playing' && space) return this.press();
        // SPACE leaves too (it is the touch A button) — but only after a beat,
        // so the last mashes of the round do not dismiss the result unread
        if (this.state === 'result' && (enter ||
            (space && this.scene.time.now - this.resultAt >= DrinkingGame.RESULT_GRACE_MS))) return this.hide();
    }

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
        panel.fillStyle(0x1b120d, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(3, 0xd49345, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (x, y, value, size, bold, color) => {
            const o = scene.add.text(x, y, value, {
                fontSize: size,
                fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono',
                align: 'center',
            });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };

        text(W / 2, py + 38, 'NOMIKAI SHOWDOWN', '32px', true, '#ffd27f');
        this.timerText = text(W / 2, py + 88,
            `${(this.durationMs / 1000).toFixed(1)}s`, '30px', true, '#ffffff');

        const leftX = px + 205, rightX = px + pw - 205;
        text(leftX, py + 142, this.displayName(this.currentPlayer()), '24px', true, '#66ddff');
        text(rightX, py + 142, this.displayName(this.opponent), '24px', true, '#ff9966');
        this.playerScoreText = text(leftX, py + 208, '0', '64px', true, '#66ddff');
        this.opponentScoreText = text(rightX, py + 208, '0', '64px', true, '#ff9966');

        const barY = py + 264, barW = 250, barH = 24;
        const barBg = scene.add.graphics();
        barBg.fillStyle(0x30251f, 1);
        barBg.fillRect(leftX - barW / 2, barY, barW, barH);
        barBg.fillRect(rightX - barW / 2, barY, barW, barH);
        barBg.lineStyle(2, 0x8c6b4b, 1);
        barBg.strokeRect(leftX - barW / 2, barY, barW, barH);
        barBg.strokeRect(rightX - barW / 2, barY, barW, barH);
        barBg.setScrollFactor(0); barBg.setDepth(2002); objs.push(barBg);

        this.playerBar = scene.add.graphics();
        this.opponentBar = scene.add.graphics();
        for (const bar of [this.playerBar, this.opponentBar]) {
            bar.setScrollFactor(0); bar.setDepth(2003); objs.push(bar);
        }
        this.barGeometry = { leftX, rightX, y: barY, width: barW, height: barH };

        this.statusText = text(W / 2, py + 326, Hints.text(scene, 'PRESS SPACE TO START'), '26px', true, '#ffd27f');
        this.rulesText = text(W / 2, py + 360,
            Hints.text(scene, 'Press SPACE as many times as you can before time runs out.'), '18px', false, '#dddddd');
        // the stake picker: ←/→ or a click, only what the wallet covers
        this.stakeTexts = DrinkingGame.STAKES.map((option, i) => {
            const t = text(W / 2 + (i - (DrinkingGame.STAKES.length - 1) / 2) * 240, py + 400, '', '20px', true);
            t.setInteractive({ useHandCursor: true });
            t.on('pointerdown', () => this.setStake(i));
            return t;
        });
        this.prizeText = text(W / 2, py + 436, '', '18px', true, '#ffd700');
        this.hintText = text(W / 2, py + 466,
            Hints.text(scene, '←/→: stake · SPACE/ENTER: start · ESC: leave'), '16px', false, '#999999');
        this.paintStakes();
        this.paintScores();
    }

    paintScores() {
        if (!this.playerScoreText || !this.opponentScoreText) return;
        this.playerScoreText.setText(String(this.playerScore));
        this.opponentScoreText.setText(String(this.opponentScore));

        const g = this.barGeometry;
        const scaleMax = Math.max(50, Math.ceil(Math.max(this.playerScore, this.opponentScore) / 25) * 25);
        const innerH = g.height - 6;
        this.playerBar.clear();
        this.playerBar.fillStyle(0x44bddd, 1);
        this.playerBar.fillRect(g.leftX - g.width / 2 + 3, g.y + 3,
            (g.width - 6) * this.playerScore / scaleMax, innerH);
        this.opponentBar.clear();
        this.opponentBar.fillStyle(0xee7744, 1);
        this.opponentBar.fillRect(g.rightX - g.width / 2 + 3, g.y + 3,
            (g.width - 6) * this.opponentScore / scaleMax, innerH);
    }
}

DrinkingGame.ROUND_MS = 15_000;
/** How long after the buzzer SPACE is ignored on the result screen. */
DrinkingGame.RESULT_GRACE_MS = 1_500;
/**
 * What can ride on a round. `stake` is what the player puts in (and loses),
 * `winnings` what a win adds on top of getting it back: the opponent matches
 * a tab, and a friendly round is a small one on the house.
 */
DrinkingGame.STAKES = [
    { id: 'free',  label: 'FRIENDLY',  stake: 0,    winnings: 100 },
    { id: 'small', label: 'SMALL TAB', stake: 500,  winnings: 500 },
    { id: 'large', label: 'BIG TAB',   stake: 2000, winnings: 2000 },
];

/** What the winner is paid: the stake back plus the winnings, times any prizeBonus. */
DrinkingGame.pool = (option, bonus) => option.stake + Math.round(option.winnings * (bonus > 0 ? bonus : 1));

/** A stake is on offer only when the wallet holds all of it. */
DrinkingGame.affordable = (option, money) => option.stake <= money;

/** The option `dir` (-1 / +1) along from `index` that `money` covers; `index` itself when there is none. */
DrinkingGame.nextStake = (index, dir, money) => {
    for (let i = index + dir; i >= 0 && i < DrinkingGame.STAKES.length; i += dir) {
        if (DrinkingGame.affordable(DrinkingGame.STAKES[i], money)) return i;
    }
    return index;
};

DrinkingGame.stakeLabel = (option, price) => option.stake ? `${option.label} ${price}` : option.label;
DrinkingGame.BAILEY_BONUS_MS = 1_500;
DrinkingGame.BAILEY_MAX_BONUS = 10;
DrinkingGame.DAMIAN_PRESS_PATTERN = [170, 230, 150, 210, 185, 255, 145, 200];

if (typeof window !== 'undefined') window.DrinkingGame = DrinkingGame;
