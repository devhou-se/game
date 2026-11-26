// const { open } = require('./browser');
// const { page, errors, close, url } = await open({ storage: {k: 'v'}, touch: false, width: 1280, height: 960 });
// Each open() is its own isolated context on the ONE shared browser. ALWAYS close() (try/finally).
const { chromium } = require('playwright-core');
const PORT = process.env.PORT || 8123;
const BASE = `http://127.0.0.1:${PORT}/`;
// a returning player: no creator, no intro
const SEEN = { gamev2_creator_seen: '1', gamev2_intro_seen: '1' };

async function open(opts = {}) {
    const browser = await chromium.connect('ws://127.0.0.1:9333/pw');
    const width = opts.width || 1280, height = opts.height || 960;
    const context = await browser.newContext({
        viewport: { width, height }, hasTouch: !!opts.touch, isMobile: !!opts.mobile,
        deviceScaleFactor: 1,
    });
    const storage = opts.fresh ? (opts.storage || {}) : { ...SEEN, ...(opts.storage || {}) };
    await context.addInitScript((s) => { for (const [k, v] of Object.entries(s)) if (localStorage.getItem(k) === null) localStorage.setItem(k, v); }, storage);
    if (opts.now) {   // stub the real clock: opts.now = '2027-02-20T12:00:00'
        await context.addInitScript((iso) => {
            const t0 = new Date(iso).getTime(), real = Date, start = real.now();
            class D extends real { constructor(...a) { if (a.length) super(...a); else super(t0 + (real.now() - start)); } static now() { return t0 + (real.now() - start); } }
            window.Date = D;
        }, opts.now);
    }
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    const url = (q = '?notitle=1&nointro=1') => BASE + q;
    const close = async () => { await context.close(); await browser.close(); };
    return { page, context, errors, close, url, BASE };
}

// wait until the game scene has a player and the room is loaded
async function ready(page) {
    await page.waitForFunction(() => {
        const s = window.game && window.game.scene && window.game.scene.keys.GameScene;
        return s && s.player && s.roomManager && s.roomManager.currentRoom && !s.roomManager.isTransitioning;
    }, null, { timeout: 30000 });
}

// hold a key until `done()` (evaluated in the page) is true, at most `ms`; a short tap can be
// dropped when the frame rate dips, so never rely on a fixed 80ms press
async function hold(page, key, done, ms = 1500) {
    await page.keyboard.down(key);
    try { await page.waitForFunction(done, null, { timeout: ms }); } catch (e) { /* caller asserts */ }
    await page.keyboard.up(key);
    await page.waitForTimeout(120);
}

module.exports = { open, ready, hold, BASE, PORT };
