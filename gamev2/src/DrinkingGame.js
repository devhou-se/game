/**
 * DrinkingGame — 60-second space-bar mash at the Izakaya table.
 *
 * Bump the configured table to open the challenge, then press SPACE as many
 * times as possible before the clock reaches zero. Damian plays at a steady
 * simulated cadence. If the player is Damian, Bailey takes his place and his
 * score is always exactly ten higher than the player's — the house gimmick.
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
        });
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

    isActive() { return this.state !== 'idle'; }

    /** Open the game only when the player bumps a configured trigger cell. */
    checkStart(gridX, gridY) {
        if (this.isActive() || this.scene.roomManager.isTransitioning) return false;
        const roomKey = this.scene.roomManager.currentRoom;
        const settings = (this.scene.config.rooms[roomKey] || {}).drinkingGame;
        if (!settings || !(settings.triggerCells || [])
            .some(([x, y]) => x === gridX && y === gridY)) return false;

        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.space); JD(this.keys.enter); JD(this.keys.esc);
        this.durationMs = settings.durationMs || DrinkingGame.ROUND_MS;
        this.opponent = DrinkingGame.opponentFor(this.currentPlayer());
        this.resetScores();
        this.state = 'ready';
        this.render();
        return true;
    }

    resetScores() {
        this.playerScore = 0;
        this.opponentScore = this.opponent === 'bailey' ? 10 : 0;
    }

    begin() {
        this.clearTimers();
        this.resetScores();
        this.state = 'playing';
        this.deadline = this.scene.time.now + this.durationMs;
        this.statusText.setText('MASH SPACE!');
        this.hintText.setText('SPACE: drink · ESC: give up');
        this.updateClock();
        this.paintScores();

        this.clockEvent = this.scene.time.addEvent({
            delay: 100,
            loop: true,
            callback: () => this.updateClock(),
        });
        this.finishEvent = this.scene.time.delayedCall(this.durationMs, () => this.finish());
        if (this.opponent === 'damian') this.scheduleDamianPress();
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

    updateClock() {
        if (this.state !== 'playing') return;
        const remainingMs = Math.max(0, this.deadline - this.scene.time.now);
        this.timerText.setText(`${(remainingMs / 1000).toFixed(1)}s`);
    }

    press() {
        if (this.state !== 'playing') return;
        this.playerScore++;
        if (this.opponent === 'bailey') this.opponentScore = this.playerScore + 10;
        this.paintScores();
    }

    finish() {
        if (this.state !== 'playing') return;
        if (this.opponent === 'bailey') this.opponentScore = this.playerScore + 10;
        this.clearTimers();
        this.state = 'result';
        this.timerText.setText('TIME!');
        this.paintScores();

        if (this.playerScore > this.opponentScore) {
            this.statusText.setText(`YOU WIN BY ${this.playerScore - this.opponentScore}!`);
        } else if (this.playerScore === this.opponentScore) {
            this.statusText.setText('A DRAW — KANPAI!');
        } else if (this.opponent === 'bailey') {
            this.statusText.setText('BAILEY SOMEHOW FINDS TEN MORE.');
        } else {
            this.statusText.setText(`${this.displayName(this.opponent).toUpperCase()} WINS BY ${this.opponentScore - this.playerScore}.`);
        }
        this.hintText.setText('SPACE/ENTER: rematch · ESC: leave');
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
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        const space = JD(k.space);
        const enter = JD(k.enter);
        if (this.state === 'ready' && (space || enter)) return this.begin();
        if (this.state === 'playing' && space) return this.press();
        if (this.state === 'result' && (space || enter)) return this.begin();
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const pw = 760, ph = 440, px = (W - pw) / 2, py = (H - ph) / 2;
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
        this.timerText = text(W / 2, py + 88, '60.0s', '30px', true, '#ffffff');

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

        this.statusText = text(W / 2, py + 334, 'PRESS SPACE TO START', '26px', true, '#ffd27f');
        text(W / 2, py + 374, 'Press SPACE as many times as you can in 60 seconds.', '18px', false, '#dddddd');
        this.hintText = text(W / 2, py + 412, 'SPACE/ENTER: start · ESC: leave', '16px', false, '#999999');
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

DrinkingGame.ROUND_MS = 60_000;
DrinkingGame.DAMIAN_PRESS_PATTERN = [170, 230, 150, 210, 185, 255, 145, 200];

if (typeof window !== 'undefined') window.DrinkingGame = DrinkingGame;
