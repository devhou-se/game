// PORT=8131 node smoke.js ['?notitle=1&nointro=1'] [shot.png] — boots the game, fails on any console/page error
const { open, ready } = require('./browser');
(async () => {
    const { page, errors, close, url } = await open();
    let code = 0;
    try {
        await page.goto(url(process.argv[2] || '?notitle=1&nointro=1'));
        await ready(page);
        await page.waitForTimeout(800);
        const st = await page.evaluate(() => {
            const s = window.game.scene.keys.GameScene;
            return { room: s.roomManager.currentRoom, rooms: Object.keys(s.config.rooms).length, x: s.player.gridX, y: s.player.gridY, fps: Math.round(window.game.loop.actualFps) };
        });
        console.log(JSON.stringify(st));
        if (process.argv[3]) await page.screenshot({ path: process.argv[3] });
        if (errors.length) { console.log('ERRORS', errors.join('\n')); code = 1; } else console.log('no errors');
    } catch (e) { console.log('FAILED', e.message, errors.join('\n')); code = 1; } finally { await close(); }
    process.exit(code);
})();
