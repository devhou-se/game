// PORT=<port> node regress.js
//
// The browser regression suite the merge queue runs before every landing. Exit 0 only when every
// check passes; one `FAIL <name> <evidence>` line per failure; the last line is `N/N checks passed`.
// Any console error or page error, on any page, is a failure (the `no-errors` check).
// A run that has not finished after 80s (a stalled browser) fails what was in flight and exits 1.
//
// Rules this file keeps (keep them when you add a check):
//  - expectations come from the game's own data in the page (config, Trips, roomManager, Occlusion),
//    never from a cell, a date or an NPC name written here;
//  - a check gets to its place through the game's own API (roomManager.switchRoomInstant) and does
//    the last steps with real keys / real touches, held until the game has seen them (hold());
//  - no fixed long waits: wait on game state;
//  - a check that cannot find what it needs FAILS with what it looked for; it never passes empty.
const path = require('path');
const { open, ready, hold } = require('./browser');

const SHOTS = process.env.SHOTS || path.join(require('os').tmpdir(), 'gamev2-regress-shots');
const QUIET = '?notitle=1&nointro=1';
const results = [];          // { name, ok, evidence }
const allErrors = [];        // [where, message]
const T0 = Date.now();
const DEADLINE_MS = 80000;   // a normal run is ~25s (~30s with the browser busy); a stalled browser must not hang the queue
const running = new Set();   // names of the checks in flight

// ------------------------------------------------------------------ in-page helpers (window.__t)

/* eslint-disable no-undef */
function install() {
    const s = window.game.scene.keys.GameScene, rm = s.roomManager;
    const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    const T = window.__t = {
        s, rm, DIRS,
        room: () => rm.rooms[rm.currentRoom],
        npcs: () => rm.rooms[rm.currentRoom].npcs,
        at: (x, y) => s.player.gridX === x && s.player.gridY === y,
        pos: () => ({ room: rm.currentRoom, district: rm.currentDistrict(), x: s.player.gridX, y: s.player.gridY }),
        idle: () => !s.player.isMoving && !rm.isTransitioning && !(s.trainTravel && s.trainTravel.riding),
        // what the game's own collision says about a cell of the current room (characters aside)
        free: (x, y) => rm.checkBoundary(x, y) && !rm.isBlocked(x, y) &&
            !rm.objectSprites.some(o => o.gridX === x && o.gridY === y),
        portal: (x, y) => T.room().transporters.some(t => t.gridX === x && t.gridY === y) ||
            (((s.config.stations || {})[rm.currentRoom] || {}).board || []).some(([bx, by]) => bx === x && by === y),
        // nobody on the cell, nobody near enough to wander onto it
        quiet: (x, y, r = 4) => !T.npcs().some(n => {
            const t = n.getTargetPosition();
            return Math.max(Math.abs(n.gridX - x), Math.abs(n.gridY - y)) <= r ||
                Math.max(Math.abs(t.x - x), Math.abs(t.y - y)) <= r;
        }),
        open: (x, y) => T.free(x, y) && !T.portal(x, y),
        size: () => ({ w: Math.round(T.room().worldWidth / s.GRID_SIZE), h: Math.round(T.room().worldHeight / s.GRID_SIZE) }),
        place: (room, x, y) => { rm.switchRoomInstant(room, x, y); return T.pos(); },
        // back to where this page booted (the world outside), so a check never starts from wherever
        // the one before it happened to stop — or to fail
        home: () => T.place(T.start.room, T.start.x, T.start.y),
        // frames, since the last clear, on which a room transition / a camera fade was running
        seen: { transition: 0, fade: 0 },
        unsee: () => { T.seen.transition = 0; T.seen.fade = 0; },
        // game frames from a movement key going down to the first overlay being up (arm() before the key);
        // counted in frames, so a slow machine does not change the answer
        frames: 0, lag: null,
        arm: () => { T.lag = { key: null, open: null }; },
        lagFrames: () => (T.lag && T.lag.key !== null && T.lag.open !== null ? T.lag.open - T.lag.key : null),
        roomName: (key) => (s.config.rooms[key] && s.config.rooms[key].name) || key,
        hud: () => ({ room: s.hudText.text, date: s.hudDateText.text, money: s.hudMoneyText.text,
            oneRow: s.hudDateText.y === s.hudText.y, shown: s.hudText.visible && s.hudDateText.visible && s.menuButton.visible }),
        overlays: () => {
            const o = [];
            if (s.titleScreen.isVisible()) o.push('title');
            if (s.dialogueManager.isVisible()) o.push('dialogue');
            if (s.menuManager.isVisible()) o.push('menu');
            if (s.shop.isVisible()) o.push('shop');
            if (s.datePicker.isVisible()) o.push('datePicker');
            if (s.stationPicker.isVisible()) o.push('stationPicker');
            if (s.characterCreator.isVisible()) o.push('creator');
            if (s.characterSelect.isVisible()) o.push('characterSelect');
            if (s.intro.isVisible()) o.push('intro');
            if (s.mapVisible) o.push('map');
            if (s.creditsVisible) o.push('credits');
            if (s.achievementsVisible) o.push('achievements');
            if (s.fishing.isActive()) o.push('fishing');
            if (s.drinkingGame.isActive()) o.push('drinkingGame');
            return o;
        },
        // test hygiene between checks, not a thing under test: take down whatever a failed check left up
        reset: () => {
            if (s.dialogueManager.isVisible()) s.dialogueManager.close();
            if (s.menuManager.isVisible()) s.menuManager.hide();
            if (s.shop.isVisible()) s.shop.hide();
            if (s.datePicker.isVisible()) s.datePicker.hide();
            if (s.stationPicker.isVisible()) s.stationPicker.hide();
            if (s.characterCreator.isVisible()) s.characterCreator.hide();
            if (s.intro.isVisible()) s.intro.hide();
            if (s.mapCloseCallback) s.mapCloseCallback();
        },
        // is the player drawn inside the browser window (canvas px -> CSS px)?
        onScreen: () => {
            const cam = s.cameras.main, v = cam.worldView, p = s.player.sprite;
            const r = window.game.canvas.getBoundingClientRect(), k = r.width / window.game.canvas.width;
            const cx = r.left + (cam.x + (p.x - v.x) * cam.zoom) * k, cy = r.top + (cam.y + (p.y - v.y) * cam.zoom) * k;
            return { cx: Math.round(cx), cy: Math.round(cy), inView: p.x >= v.x && p.x <= v.right && p.y >= v.y && p.y <= v.bottom,
                inWindow: cx >= 0 && cx <= window.innerWidth && cy >= 0 && cy <= window.innerHeight,
                visible: p.visible && p.alpha === 1, win: [window.innerWidth, window.innerHeight] };
        },
        // a direction the player can take one step in right now: { dx, dy } or null
        wayOut: () => {
            const p = s.player;
            for (const r of [3, 2, 1, 0]) {   // away from everyone if possible; never onto somebody
                for (const [dx, dy] of DIRS) {
                    if (T.open(p.gridX + dx, p.gridY + dy) && T.quiet(p.gridX + dx, p.gridY + dy, r)) return { dx, dy };
                }
            }
            return null;
        },
    };
    T.start = T.pos();
    s.events.on('postupdate', () => {
        if (rm.isTransitioning) T.seen.transition++;
        const cams = s.cameras.cameras.slice();
        if (s.uiScale && s.uiScale.camera && !cams.includes(s.uiScale.camera)) cams.push(s.uiScale.camera);
        if (cams.some(c => c.fadeEffect && c.fadeEffect.isRunning)) T.seen.fade++;
        T.frames++;
        if (T.lag) {
            const i = s.inputHandler, c = i.cursors;
            if (T.lag.key === null && [c.up, c.down, c.left, c.right, i.wKey, i.aKey, i.sKey, i.dKey].some(k => k.isDown)) T.lag.key = T.frames;
            if (T.lag.open === null && T.overlays().length) T.lag.open = T.frames;
        }
    });
    // count the fading room switches (and whether a camera fade really started)
    rm.__sw = 0; rm.__fade = 0;
    const real = rm.switchRoom.bind(rm);
    rm.switchRoom = (...a) => {
        const out = real(...a);
        rm.__sw++;
        const ui = s.uiScale, cam = ui && ui.active && ui.camera ? ui.camera : s.cameras.main;
        if (cam.fadeEffect && cam.fadeEffect.isRunning) rm.__fade++;
        return out;
    };
    return true;
}
/* eslint-enable no-undef */

// ------------------------------------------------------------------ node-side helpers

const KEYS = { '1,0': ['ArrowRight', 'd'], '-1,0': ['ArrowLeft', 'a'], '0,1': ['ArrowDown', 's'], '0,-1': ['ArrowUp', 'w'] };
let keyTurn = 0;
const keyFor = (dx, dy) => KEYS[`${dx},${dy}`][keyTurn++ % 2];   // arrows and WASD take turns

const need = (cond, evidence) => { if (!cond) throw new Error(typeof evidence === 'string' ? evidence : JSON.stringify(evidence)); };
const idle = (page, ms = 5000) => page.waitForFunction('__t.idle()', null, { timeout: ms });
const until = async (page, expr, ms = 3000) => {
    try { await page.waitForFunction(expr, null, { timeout: ms }); return true; } catch (e) { return false; }
};

async function boot(page, url) {
    await page.goto(url);
    await ready(page);
    // the loading screen covers the page (and the touch controls) until it has faded and gone
    await page.waitForFunction('!document.getElementById("loader")', null, { timeout: 5000 });
    await page.evaluate(install);
}

/** Exactly one step with a real key: the key goes up as soon as the game has started the move. */
async function step(page, dx, dy) {
    await idle(page);
    const from = await page.evaluate('__t.pos()');
    await hold(page, keyFor(dx, dy), '__t.s.player.isMoving || __t.rm.isTransitioning', 1500);
    await idle(page);
    return from;
}

/** A real key press on an overlay: held until `expr` is true. Returns whether it became true. */
async function press(page, key, expr, ms = 1500) {
    await hold(page, key, expr, ms);
    return page.evaluate(expr);
}

async function check(name, fn) {
    const t = Date.now();
    let timer;
    running.add(name);
    try {
        await Promise.race([
            fn(),
            new Promise((_, rej) => { timer = setTimeout(() => rej(new Error('timed out after 25s')), 25000); }),
        ]);
        results.push({ name, ok: true });
        console.log(`ok   ${name} (${Date.now() - t}ms)`);
    } catch (e) {
        const evidence = String(e && e.message || e).replace(/\s+/g, ' ').slice(0, 600);
        results.push({ name, ok: false, evidence });
        console.log(`FAIL ${name} ${evidence}`);
    } finally { clearTimeout(timer); running.delete(name); }
}

/** One browser context (a profile); its console / page errors are collected under `label`. */
async function profile(label, opts, body) {
    let ctx;
    try {
        ctx = await open(opts);
        await body(ctx);
    } catch (e) {
        results.push({ name: `${label}-profile`, ok: false, evidence: String(e && e.message || e).slice(0, 400) });
        console.log(`FAIL ${label}-profile ${String(e && e.message || e).replace(/\s+/g, ' ').slice(0, 400)}`);
    } finally {
        if (ctx) {
            for (const m of ctx.errors) allErrors.push([label, m]);
            try { await ctx.close(); } catch (e) { /* the browser is shared: nothing else to do */ }
        }
    }
}

// ------------------------------------------------------------------ the returning desktop player

async function desktop(shared) {
    await profile('desktop', {}, async ({ page, url, errors }) => {
        const cleanly = async (name, fn) => {
            const before = errors.length;
            await check(name, async () => {
                await fn();
                need(errors.length === before, { errors: errors.slice(before) });
            });
            // never let one check's leftovers into the next
            await page.evaluate('window.__t && (__t.reset(), true)').catch(() => {});
            await idle(page).catch(() => {});
        };

        // 1 ---------------------------------------------------------------- boot, returning player
        await cleanly('boot-returning', async () => {
            await boot(page, url(QUIET));
            await until(page, '__t.s.cameras.main.worldView.contains(__t.s.player.sprite.x, __t.s.player.sprite.y)', 2000);
            const st = await page.evaluate(() => {
                const { s, rm } = __t, p = s.player;
                const start = Trips.startFor(s.config, gameDate(), { played: Trips.baseOf(s.config.player.sprite) });
                const at = rm.resolve(start.room, start.x, start.y);
                const cities = Object.keys(s.config.cities || {});
                return {
                    pos: __t.pos(), hud: __t.hud(), free: __t.free(p.gridX, p.gridY), screen: __t.onScreen(),
                    overlays: __t.overlays(), date: gameDate(), dateText: formatGameDate(gameDate()),
                    name: __t.roomName(rm.currentDistrict()), startsAt: at,
                    cities, stitched: cities.filter(c => rm.rooms[c] && rm.rooms[c].stitched),
                    inCity: !!(s.config.cities && Object.values(s.config.cities).some(c => c.rooms.some(r => r.room === start.room))),
                    isCity: !!rm.rooms[rm.currentRoom].city, tiles: rm.liveTiles.size,
                    canvas: !!window.game.canvas && window.game.canvas.width > 0,
                    isContentDay: [...contentChangeDates(s.config)].includes(gameDate()) || !!Trips.during(Trips.forDate(Trips.of(s.config), gameDate()), gameDate()),
                    trips: Trips.of(s.config), today: (() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })(),
                };
            });
            shared.trips = st.trips;
            need(st.canvas && st.tiles > 0, { noScene: st });
            need(st.cities.length > 0 && st.stitched.length === st.cities.length, { citiesNotStitched: st.cities, stitched: st.stitched });
            need(st.inCity === st.isCity, { startDistrictInCity: st.inCity, currentRoomIsCity: st.isCity, pos: st.pos });
            need(st.free, { playerOnBlockedCell: st.pos });
            need(st.pos.room === st.startsAt.room && st.pos.x === st.startsAt.x && st.pos.y === st.startsAt.y, { pos: st.pos, tripStart: st.startsAt });
            need(st.screen.inView && st.screen.inWindow && st.screen.visible, { playerNotOnScreen: st.screen });
            need(st.overlays.length === 0, { overlaysUp: st.overlays });
            need(st.hud.shown && st.hud.room.includes(st.name), { hudRoom: st.hud.room, expected: st.name });
            need(st.hud.date.includes(st.dateText), { hudDate: st.hud.date, expected: st.dateText });
            need(st.hud.money.trim().length > 2, { hudWallet: st.hud.money });
            need(st.isContentDay, { defaultDateHasNoContent: st.date });
            await page.screenshot({ path: path.join(SHOTS, 'regress_boot.png') });
        });

        // 3 ---------------------------------------------------------------- walk, and a wall
        await cleanly('walk-and-wall', async () => {
            // a straight run of 4+ open cells that ends at a plain collider, away from everyone
            const run = await page.evaluate(() => {
                const { s, rm } = __t, { w, h } = __t.size(), p = s.player;
                let best = null;
                for (let y = 0; y < h; y++) {
                    for (let x = 0; x < w - 6; x++) {
                        let n = 0;
                        while (n < 6 && __t.open(x + n, y)) n++;
                        if (n < 4 || n > 5) continue;
                        const wx = x + n;
                        if (__t.free(wx, y) || __t.portal(wx, y) || rm.interactionAt(wx, y)) continue;   // a wall, not a door or a shop
                        if (!rm.isBlocked(wx, y)) continue;
                        let clear = true;
                        for (let i = 0; i <= n; i++) if (!__t.quiet(x + i, y, 5)) clear = false;
                        if (!clear) continue;
                        const d = Math.abs(x - p.gridX) + Math.abs(y - p.gridY);
                        if (!best || d < best.d) best = { x, y, n, wx, d };
                    }
                }
                return best;
            });
            need(run, 'no straight run of 4 open cells ending at a wall in ' + JSON.stringify(await page.evaluate('__t.pos()')));
            await page.evaluate(([x, y]) => __t.place(__t.rm.currentRoom, x, y), [run.x, run.y]);
            await idle(page);
            const end = run.wx - 1;
            await hold(page, 'ArrowRight', `__t.at(${end}, ${run.y}) && !__t.s.player.isMoving`, 400 * run.n + 2500);
            const walked = await page.evaluate('__t.pos()');
            need(walked.x === end && walked.y === run.y && end - run.x >= 3, { walkedTo: walked, from: run });
            // keep pushing at the wall with the other key set: the player stays, nothing opens
            await hold(page, 'd', 'false', 450);
            await idle(page);
            const after = await page.evaluate('({ pos: __t.pos(), overlays: __t.overlays(), sw: __t.rm.__sw })');
            need(after.pos.x === end && after.pos.y === run.y, { wallDidNotStop: after.pos, wall: run });
            need(after.overlays.length === 0 && after.sw === 0, { afterWall: after });
        });

        // 4 ---------------------------------------------------------------- a district seam, stitched
        await cleanly('seam-stitched', async () => {
            const seam = await page.evaluate(() => {
                const { s, rm } = __t;
                // open in the district's OWN map (what ?stitch=0 plays): floor, no collider, in bounds, not a door
                const districtOpen = (key, x, y) => {
                    const r = rm.rooms[key]; let floor = false, blocked = false;
                    for (const L of r.layers) {
                        if (!((x + ',' + y) in (L.tiles || {}))) continue;
                        if (L.collision) blocked = true; else if (L.name === 'Floor') floor = true;
                    }
                    return floor && !blocked && rm.checkBoundary(x, y, key) &&
                        !r.transporters.some(t => t.gridX === x && t.gridY === y);
                };
                for (const city of Object.values(rm.cities)) {
                    for (const m of city.members) {
                        const A = m.key;
                        for (const t of rm.rooms[A].transporters) {
                            const B = t.targetRoom, sib = rm.memberOf[B];
                            if (!sib || sib.city !== city || B === A) continue;
                            for (const [dx, dy] of __t.DIRS) {
                                const n = { x: t.gridX - dx, y: t.gridY - dy };
                                if (!districtOpen(A, n.x, n.y) || !districtOpen(B, t.targetX, t.targetY)) continue;
                                const c = rm.resolve(A, n.x, n.y);
                                __t.place(A, n.x, n.y);          // collision is the current room's: be in the city
                                if (rm.localize(c.x, c.y).room !== A || !__t.open(c.x, c.y) || !__t.quiet(c.x, c.y, 6)) continue;
                                let steps = 0;
                                for (let k = 1; k <= 4 && !steps; k++) {
                                    const x = c.x + dx * k, y = c.y + dy * k;
                                    if (!__t.open(x, y)) break;
                                    if (rm.localize(x, y).room === B) steps = k;
                                }
                                if (steps) return { city: city.key, A, B, n, dx, dy, steps, target: { x: t.targetX, y: t.targetY }, from: __t.pos(), hud: __t.hud() };
                            }
                        }
                    }
                }
                return null;
            });
            need(seam, 'no seam transporter between two districts of a stitched city can be walked across');
            shared.seam = seam;
            need(seam.from.room === seam.city && seam.from.district === seam.A, { placed: seam.from, seam });
            need(seam.hud.room.includes(await page.evaluate(a => __t.roomName(a), seam.A)), { hudBefore: seam.hud.room, district: seam.A });
            await idle(page);
            await page.evaluate('__t.rm.__sw = 0, __t.rm.__fade = 0, window.__sawTransition = false, __t.unsee()');
            await hold(page, keyFor(seam.dx, seam.dy),
                `(window.__sawTransition = window.__sawTransition || __t.rm.isTransitioning, __t.rm.currentDistrict() === ${JSON.stringify(seam.B)})`,
                400 * seam.steps + 2500);
            await idle(page);
            const st = await page.evaluate(() => {
                const { s, rm } = __t, p = s.player, cam = s.cameras.main;
                const live = new Set();
                for (const rec of rm.liveTiles) if (rec.sprite && rec.sprite.visible && rec.sprite.alpha > 0 && rec.sprite.displayList) live.add(rec.gridX + ',' + rec.gridY);
                const missing = [];
                for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) if (!live.has((p.gridX + dx) + ',' + (p.gridY + dy))) missing.push([p.gridX + dx, p.gridY + dy]);
                return { pos: __t.pos(), hud: __t.hud(), sw: rm.__sw, fade: rm.__fade, saw: window.__sawTransition, seen: Object.assign({}, __t.seen),
                    fading: !!(cam.fadeEffect && cam.fadeEffect.isRunning), missing, screen: __t.onScreen() };
            });
            const nameB = await page.evaluate(b => __t.roomName(b), seam.B);
            need(st.pos.district === seam.B && st.pos.room === seam.city, { didNotCross: st.pos, seam });
            need(st.sw === 0 && st.fade === 0 && !st.saw && !st.fading, { fadedInStitchedCity: st });
            need(st.seen.transition === 0 && st.seen.fade === 0, { transitionOrFadeFramesWhileCrossing: st.seen, seam });
            need(st.hud.room.includes(nameB) && !st.hud.room.includes(seam.hud.room.split(' | ').slice(-2)[0] + ' |'), { hudAfter: st.hud.room, expected: nameB, before: seam.hud.room });
            need(st.missing.length === 0, { cellsWithNoTileSprite: st.missing.slice(0, 8), around: st.pos });
            need(st.screen.inView && st.screen.visible, { screen: st.screen });
        });

        // 5 ---------------------------------------------------------------- a konbini, by its door
        let shopDoor = null;
        await cleanly('konbini-enter', async () => {
            const door = await page.evaluate(() => {
                const { s, rm } = __t;
                for (const t of __t.room().transporters) {
                    const cfg = s.config.rooms[t.targetRoom];
                    if (!cfg || !cfg.interior || !rm.rooms[t.targetRoom]) continue;
                    // a konbini: an interior whose fixtures open the konbini's shop lists
                    const kinds = Interactions.all(rm.rooms[t.targetRoom], cfg, { venues: Shop.VENUES, group: 'shop' }).map(i => i.kind);
                    if (!kinds.includes('counter') || !kinds.some(k => k === 'drinks' || k === 'snacks')) continue;
                    for (const [dx, dy] of __t.DIRS) {
                        const n = { x: t.gridX - dx, y: t.gridY - dy };
                        if (!__t.open(n.x, n.y) || !__t.quiet(n.x, n.y, 4) || !__t.quiet(t.gridX, t.gridY, 4)) continue;
                        return { outside: rm.currentRoom, door: { x: t.gridX, y: t.gridY }, n, dx, dy,
                            room: t.targetRoom, target: { x: t.targetX, y: t.targetY }, name: __t.roomName(t.targetRoom) };
                    }
                }
                return null;
            });
            need(door, 'no konbini door with a free cell in front of it in ' + JSON.stringify(await page.evaluate('__t.pos()')));
            await page.evaluate(d => { __t.place(d.outside, d.n.x, d.n.y); __t.rm.__sw = 0; __t.rm.__fade = 0; }, door);
            await idle(page);
            await page.evaluate('__t.unsee()');
            await step(page, door.dx, door.dy);
            const st = await page.evaluate('({ pos: __t.pos(), hud: __t.hud(), sw: __t.rm.__sw, fade: __t.rm.__fade, seen: Object.assign({}, __t.seen), screen: __t.onScreen(), free: __t.free(__t.s.player.gridX, __t.s.player.gridY) })');
            need(st.pos.room === door.room && st.pos.x === door.target.x && st.pos.y === door.target.y, { notInside: st.pos, door });
            need(st.sw === 1 && st.fade === 1 && st.seen.fade > 0 && st.seen.transition > 0, { noFadeThroughDoor: st });
            need(st.hud.room.includes(door.name), { hud: st.hud.room, expected: door.name });
            need(st.free && st.screen.inView && st.screen.visible, { inside: st });
            shopDoor = door;
        });

        await cleanly('konbini-shop', async () => {
            need(shopDoor, 'needs konbini-enter');
            const fx = await page.evaluate(() => {
                const { s, rm } = __t, { w, h } = __t.size();
                for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
                    const hit = rm.interactionAt(x, y, 'shop');
                    if (!hit || __t.free(x, y)) continue;
                    for (const [dx, dy] of __t.DIRS) {
                        const n = { x: x - dx, y: y - dy };
                        if (__t.open(n.x, n.y) && __t.quiet(n.x, n.y, 0)) return { x, y, n, dx, dy, kind: hit.kind };
                    }
                }
                return null;
            });
            need(fx, 'no shop fixture with a free cell beside it in ' + shopDoor.room);
            await page.evaluate(f => __t.place(__t.rm.currentRoom, f.n.x, f.n.y), fx);
            await idle(page);
            await page.evaluate('__t.arm()');
            const opened = await press(page, keyFor(fx.dx, fx.dy), '__t.s.shop.visible');
            const shop = await page.evaluate('({ kind: __t.s.shop.kind, rows: __t.s.shop.rowCount(), pos: __t.pos(), overlays: __t.overlays(), lag: __t.lagFrames() })');
            need(opened && shop.kind === fx.kind && shop.rows > 0, { shopDidNotOpen: shop, fixture: fx });
            // the bump itself opens the list, not a second or two of leaning on the counter
            need(shop.lag !== null && shop.lag <= 2, { shopOpenedFramesAfterTheBump: shop.lag });
            need(shop.pos.x === fx.n.x && shop.pos.y === fx.n.y, { movedIntoFixture: shop.pos, fixture: fx });
            // a second real key moves the cursor down the list (when there is more than one row)
            if (shop.rows > 1) {
                const moved = await press(page, 'ArrowDown', '__t.s.shop.selected === 1');
                need(moved, { listCursorDidNotMove: await page.evaluate('__t.s.shop.selected') });
            }
            await page.screenshot({ path: path.join(SHOTS, 'regress_konbini.png') });
            const closed = await press(page, 'Escape', '!__t.s.shop.isVisible()');
            // the ESC that closed the list must not open the menu on the next frames
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r)))));
            const after = await page.evaluate('({ overlays: __t.overlays(), pos: __t.pos() })');
            need(closed && after.overlays.length === 0, { afterEsc: after });
        });

        await cleanly('konbini-exit', async () => {
            need(shopDoor, 'needs konbini-enter');
            const exit = await page.evaluate((door) => {
                const { rm } = __t;
                if (rm.currentRoom !== door.room) __t.place(door.room, door.target.x, door.target.y);
                for (const t of __t.room().transporters) {
                    for (const [dx, dy] of __t.DIRS) {
                        const n = { x: t.gridX - dx, y: t.gridY - dy };
                        if (!__t.open(n.x, n.y) || !__t.quiet(n.x, n.y, 0)) continue;
                        const to = rm.resolve(t.targetRoom, t.targetX, t.targetY);
                        return { n, dx, dy, to, district: t.targetRoom };
                    }
                }
                return null;
            }, shopDoor);
            need(exit, 'no exit transporter with a free cell beside it in ' + shopDoor.room);
            await page.evaluate(e => { __t.place(__t.rm.currentRoom, e.n.x, e.n.y); __t.rm.__sw = 0; }, exit);
            await step(page, exit.dx, exit.dy);
            const st = await page.evaluate('({ pos: __t.pos(), hud: __t.hud(), sw: __t.rm.__sw, free: __t.free(__t.s.player.gridX, __t.s.player.gridY), portal: __t.portal(__t.s.player.gridX, __t.s.player.gridY), screen: __t.onScreen() })');
            need(st.pos.room === shopDoor.outside && st.pos.x === exit.to.x && st.pos.y === exit.to.y && st.sw === 1, { didNotComeOut: st.pos, exit });
            const gap = Math.max(Math.abs(st.pos.x - shopDoor.door.x), Math.abs(st.pos.y - shopDoor.door.y));
            need(gap >= 1 && gap <= 2, { cameOutAwayFromTheDoor: st.pos, door: shopDoor.door });
            need(st.free && !st.portal && st.screen.inView && st.screen.visible, { outside: st });
            need(st.hud.room.includes(await page.evaluate(d => __t.roomName(d), st.pos.district)), { hud: st.hud.room, district: st.pos.district });
        });

        // 12 --------------------------------------------------------------- scenery that hides the player fades
        await cleanly('occlusion-fade', async () => {
            const spot = await page.evaluate(() => {
                __t.home();
                const { s, rm } = __t, GS = s.GRID_SIZE, occ = s.occlusion, p = s.player;
                // what Occlusion itself would find for somebody standing on a cell
                const memo = new Map();
                const hits = (x, y) => {
                    const k = x + ',' + y;
                    if (!memo.has(k)) {
                        const py = y * GS + GS / 2;
                        memo.set(k, occ.look({ sprite: { x: x * GS + GS / 2, y: py, depth: rm.yDepth(((py + GS / 2) / GS) * 10 + 5) } }).hits);
                    }
                    return memo.get(k);
                };
                const recs = rm.tileRecords.filter(r => r.layer.z >= 2 && r.height > GS)
                    .sort((a, b) => (Math.abs(a.gridX - p.gridX) + Math.abs(a.gridY - p.gridY)) - (Math.abs(b.gridX - p.gridX) + Math.abs(b.gridY - p.gridY)));
                let looked = 0;
                for (const rec of recs) {
                    const x0 = Math.floor(rec.left / GS), x1 = Math.floor((rec.left + rec.width - 1) / GS);
                    const y0 = Math.floor(rec.top / GS), y1 = Math.floor((rec.top + rec.height - 1) / GS);
                    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
                        if (!__t.open(x, y) || !__t.quiet(x, y, 6)) continue;
                        looked++;
                        const h = hits(x, y);
                        if (!h.length) continue;
                        for (const [dx, dy] of __t.DIRS) {
                            const o = { x: x - dx, y: y - dy };
                            if (!__t.open(o.x, o.y) || hits(o.x, o.y).length) continue;
                            return { hid: { x, y }, out: o, dx, dy, art: h[0].key, pieces: h.length, looked };
                        }
                    }
                }
                return { looked, none: true, standing: recs.length };
            });
            need(spot && !spot.none, { noCellBehindScenery: spot, room: await page.evaluate('__t.pos()') });
            // placing reloads the room's tile records: ask Occlusion again for the pieces that will hide the cell
            const pieces = await page.evaluate((o) => {
                const { s, rm } = __t, GS = s.GRID_SIZE, py = o.hid.y * GS + GS / 2;
                __t.place(rm.currentRoom, o.out.x, o.out.y);
                window.__occ = s.occlusion.look({ sprite: { x: o.hid.x * GS + GS / 2, y: py, depth: rm.yDepth(((py + GS / 2) / GS) * 10 + 5) } }).hits;
                return window.__occ.length;
            }, spot);
            need(pieces === spot.pieces, { piecesChangedAfterPlacing: pieces, spot });
            await idle(page);
            const ALPHA = await page.evaluate('Occlusion.ALPHA');
            need(ALPHA > 0 && ALPHA < 1, { occlusionAlphaIsNotAFade: ALPHA });
            const solid = await until(page, 'window.__occ.every(r => r.fade === undefined && (!r.sprite || r.sprite.alpha === 1))', 2000);
            need(solid, { artNotSolidBeforeSteppingBehind: spot });
            await step(page, spot.dx, spot.dy);
            const faded = await until(page, `__t.at(${spot.hid.x}, ${spot.hid.y}) && window.__occ.every(r => r.fade !== undefined && r.fade <= Occlusion.ALPHA + 0.001 && (!r.sprite || Math.abs(r.sprite.alpha - r.fade) < 0.001)) && window.__occ.some(r => r.sprite)`, 2500);
            const mid = await page.evaluate('({ pos: __t.pos(), fades: window.__occ.slice(0, 6).map(r => [r.key, r.fade, r.sprite ? r.sprite.alpha : null]), player: __t.onScreen() })');
            need(faded, { didNotFade: mid, spot, want: ALPHA });
            need(mid.player.visible && mid.player.inView, { player: mid.player });
            await page.screenshot({ path: path.join(SHOTS, 'regress_occlusion.png') });
            await step(page, -spot.dx, -spot.dy);
            const back = await until(page, `__t.at(${spot.out.x}, ${spot.out.y}) && window.__occ.every(r => r.fade === undefined && (!r.sprite || r.sprite.alpha === 1))`, 2500);
            need(back, { didNotRestore: await page.evaluate('({ pos: __t.pos(), fades: window.__occ.slice(0, 6).map(r => [r.key, r.fade, r.sprite ? r.sprite.alpha : null]) })'), spot });
        });

        // 7 ---------------------------------------------------------------- the ESC menu
        await cleanly('menu-entries', async () => {
            const before = await page.evaluate('__t.home()');
            await idle(page);
            need(await press(page, 'Escape', '__t.s.menuManager.isVisible()'), 'ESC did not open the menu');
            const labels = await page.evaluate('__t.s.menuManager.options.map(o => o.textObject.text)');
            need(labels.length >= 5 && await page.evaluate('__t.s.menuManager.selectedIndex === 0'), { labels });
            const lit = 'ix => { const m = __t.s.menuManager, c = m.options.map(o => o.textObject.style.color); return m.selectedIndex === ix && c.filter(x => x === c[ix]).length === 1 && m.options.every(o => o.textObject.visible); }';
            for (let i = 1; i < labels.length; i++) {
                const ok = await press(page, i % 2 ? 'ArrowDown' : 's', `(${lit})(${i})`);
                need(ok, { couldNotReach: labels[i], selected: await page.evaluate('__t.s.menuManager.selectedIndex') });
            }
            need(await press(page, 'ArrowDown', `(${lit})(0)`), 'down from the last entry did not wrap to the first');
            need(await press(page, 'w', `(${lit})(${labels.length - 1})`), 'up from the first entry did not wrap to the last');
            need(await press(page, 'Escape', '!__t.s.menuManager.isVisible()'), 'ESC did not close the menu');
            const after = await page.evaluate('({ pos: __t.pos(), overlays: __t.overlays() })');
            need(after.overlays.length === 0 && after.pos.x === before.x && after.pos.y === before.y, { movedOrLeftOpen: after, before });
        });

        /** Open the menu and activate the entry called `label`, with real keys. */
        const menuTo = async (label) => {
            need(await press(page, 'Escape', '__t.s.menuManager.isVisible()'), 'ESC did not open the menu');
            const ix = await page.evaluate(l => __t.s.menuManager.options.findIndex(o => o.textObject.text === l), label);
            need(ix >= 0, `the menu has no "${label}" entry`);
            const n = await page.evaluate('__t.s.menuManager.options.length');
            // the short way round
            const down = ix <= n - ix;
            for (let i = 0; i < (down ? ix : n - ix); i++) {
                const want = down ? i + 1 : n - 1 - i;
                need(await press(page, down ? 's' : 'ArrowUp', `__t.s.menuManager.selectedIndex === ${want}`), `could not move the menu cursor to ${want}`);
            }
        };

        await cleanly('menu-map', async () => {
            await page.evaluate('__t.home()');
            await idle(page);
            await menuTo('Map');
            need(await press(page, 'Enter', '__t.s.mapVisible'), 'ENTER on Map did not open the map');
            const st = await page.evaluate(() => {
                const { s, rm } = __t;
                const texts = s.children.list.filter(o => o.type === 'Text' && o.depth >= 2000 && o.visible).map(o => o.text);
                const meta = s.cache.json.get('worldMap');
                return { menu: s.menuManager.isVisible(), texts, here: rm.currentDistrict(), rooms: Object.keys(meta.rooms),
                    image: s.children.list.some(o => o.type === 'Image' && o.texture.key === 'world-map' && o.visible) };
            });
            need(!st.menu && st.image, { mapNotDrawn: st });
            need(st.texts.includes('You') && st.texts.includes(st.here) && st.rooms.every(r => st.texts.includes(r)), { mapLabels: st.texts.slice(0, 30), here: st.here });
            await page.screenshot({ path: path.join(SHOTS, 'regress_map.png') });
            need(await press(page, 'Escape', '!__t.s.mapVisible'), 'ESC did not close the map');
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r)))));
            need((await page.evaluate('__t.overlays()')).length === 0, { afterMap: await page.evaluate('__t.overlays()') });
        });

        await cleanly('menu-time-travel', async () => {
            const href = page.url();
            await page.evaluate('__t.home()');
            await idle(page);
            await menuTo('Time Travel');
            need(await press(page, 'Enter', '__t.s.datePicker.isVisible()'), 'ENTER on Time Travel did not open the picker');
            const d0 = await page.evaluate('({ sel: __t.s.datePicker.iso(__t.s.datePicker.sel), game: gameDate(), menu: __t.s.menuManager.isVisible(), cells: __t.s.datePicker.dayCells.length })');
            need(d0.sel === d0.game && !d0.menu && d0.cells >= 28, { pickerOpenedOn: d0 });
            const next = await page.evaluate(d => Trips.addDays(d, 1), d0.sel);
            need(await press(page, 'ArrowRight', `__t.s.datePicker.iso(__t.s.datePicker.sel) === ${JSON.stringify(next)}`),
                { rightDidNotMoveADay: await page.evaluate('__t.s.datePicker.iso(__t.s.datePicker.sel)'), want: next });
            const week = await page.evaluate(d => Trips.addDays(d, 7), next);
            need(await press(page, 's', `__t.s.datePicker.iso(__t.s.datePicker.sel) === ${JSON.stringify(week)}`),
                { downDidNotMoveAWeek: await page.evaluate('__t.s.datePicker.iso(__t.s.datePicker.sel)'), want: week });
            need(await press(page, 'Escape', '!__t.s.datePicker.isVisible()'), 'ESC did not close the picker');
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r)))));
            const after = await page.evaluate('({ overlays: __t.overlays(), game: gameDate() })');
            need(after.overlays.length === 0 && after.game === d0.game && page.url() === href, { afterPicker: after, url: page.url() });
        });

        // 8 ---------------------------------------------------------------- the train
        await cleanly('train-ride', async () => {
            const board = await page.evaluate(() => {
                const { s, rm } = __t, stations = s.config.stations || {};
                const keys = Object.keys(stations).sort((a, b) => (stations[a].order ?? 99) - (stations[b].order ?? 99));
                for (const key of keys) {
                    const st = stations[key];
                    __t.place(key, st.arrive[0], st.arrive[1]);
                    for (const [bx, by] of st.board) {
                        for (const [dx, dy] of __t.DIRS) {
                            const n = { x: bx - dx, y: by - dy };
                            if (!__t.open(n.x, n.y) || !__t.free(bx, by) || !__t.quiet(n.x, n.y, 1) || !__t.quiet(bx, by, 1)) continue;
                            __t.place(key, n.x, n.y);
                            return { from: key, cell: { x: bx, y: by }, n, dx, dy, stations: keys.length, name: __t.roomName(key), hud: __t.hud() };
                        }
                    }
                }
                return null;
            });
            need(board, 'no station has a board cell that can be stepped onto from the platform');
            need(board.hud.room.includes(board.name), { hud: board.hud.room, station: board.name });
            await step(page, board.dx, board.dy);
            need(await until(page, '__t.s.stationPicker.isVisible()', 1500), { boardDidNotOpen: await page.evaluate('__t.pos()'), board });
            const b0 = await page.evaluate('({ rows: __t.s.stationPicker.rows, selected: __t.s.stationPicker.selected })');
            const choices = b0.rows.filter(r => !r.here);
            need(choices.length === board.stations - 1 && !b0.rows[b0.selected].here, { board: b0, stations: board.stations });
            // move down the board with a real key, then board whatever is selected
            if (choices.length > 1) {
                need(await press(page, 'ArrowDown', `__t.s.stationPicker.selected !== ${b0.selected}`), 'DOWN did not move the departures board');
            }
            const dest = await page.evaluate('(p => p.rows[p.selected])(__t.s.stationPicker)');
            need(dest && !dest.here && dest.key !== board.from, { dest });
            await page.screenshot({ path: path.join(SHOTS, 'regress_departures.png') });
            need(await press(page, 'Enter', '__t.s.trainTravel.riding'), 'ENTER did not start the ride');
            const locked = await page.evaluate('({ picker: __t.s.stationPicker.isVisible(), transitioning: __t.rm.isTransitioning })');
            need(!locked.picker && locked.transitioning, { duringRide: locked });
            // a key pressed mid-ride does nothing
            await hold(page, 'ArrowDown', 'false', 200);
            need(await until(page, '!__t.s.trainTravel.riding && !__t.rm.isTransitioning', 12000), { rideNeverEnded: await page.evaluate('({ pos: __t.pos(), riding: __t.s.trainTravel.riding })') });
            const st = await page.evaluate((key) => {
                const { s, rm } = __t, to = s.config.stations[key], p = s.player;
                return { pos: __t.pos(), hud: __t.hud(), row: to.trainCell[1], overlays: __t.overlays(), screen: __t.onScreen(),
                    free: __t.free(p.gridX, p.gridY), name: __t.roomName(key), cutscene: (s.trainTravel._cutTweens || []).length,
                    curtain: s.children.list.filter(o => o.depth >= 2999 && o.depth <= 3000 && o.visible && o.alpha > 0).length,
                    train: !!(s.trainTravel.sprite && s.trainTravel.sprite.visible), lastRide: s.trainTravel.lastRide, way: __t.wayOut() };
            }, dest.key);
            need(st.pos.room === dest.key && st.pos.y === st.row && st.pos.x === board.cell.x && st.free, { notOnTheDestinationPlatform: st.pos, dest: dest.key, row: st.row });
            need(st.overlays.length === 0 && st.cutscene === 0 && st.curtain === 0 && st.train, { cutsceneLeftBehind: st });
            need(st.screen.visible && st.screen.inView, { player: st.screen });
            need(st.hud.room.includes(st.name), { hud: st.hud.room, expected: st.name });
            need(st.lastRide && st.lastRide.from === board.from && st.lastRide.to === dest.key, { lastRide: st.lastRide });
            // input is unlocked: one real step
            need(st.way, { nowhereToStepAt: st.pos });
            await step(page, st.way.dx, st.way.dy);
            const moved = await page.evaluate('__t.pos()');
            need(moved.x === st.pos.x + st.way.dx && moved.y === st.pos.y + st.way.dy && moved.room === dest.key, { inputStillLocked: moved, from: st.pos, way: st.way });
        });

        // 6 ---------------------------------------------------------------- an NPC on a fixed content day
        await cleanly('npc-dialogue', async () => {
            // the first content day on which the player starts in a room with somebody who has 2+ lines
            const date = await page.evaluate(() => {
                const { s } = __t, played = Trips.baseOf(s.config.player.sprite);
                for (const d of [...contentChangeDates(s.config)].sort()) {
                    const start = Trips.startFor(s.config, d, { played });
                    const here = (s.config.rooms[start.room].npcs || []).map(n => resolveNpc(n, d))
                        .filter(n => n && Trips.baseOf(n.sprite) !== played && (n.dialogue || []).length >= 2 && !n.drinkingGameOpponent);
                    if (here.length) return d;
                }
                return null;
            });
            need(date, 'no content day in config has an NPC with two lines where the player starts');
            await boot(page, url(`${QUIET}&date=${date}`));
            need(await page.evaluate('gameDate()') === date, { gameDate: await page.evaluate('gameDate()'), want: date });
            // Walk up to somebody and bump into them. A bump that opens nothing is excused only when
            // that NPC was seen moving (or gone from the cell) while the key was down: they wander.
            const talkTo = async () => {
                for (let attempt = 0; attempt < 4; attempt++) {
                    await page.waitForFunction('__t.idle() && __t.npcs().every(n => !n.isMoving)', null, { timeout: 4000 });
                    const plan = await page.evaluate(() => {
                        const { s, rm } = __t, p = s.player;
                        const list = __t.npcs().filter(n => n.canInteract && (n.dialogue || []).length >= 2 && n.sprite.visible)
                            .sort((a, b) => (Math.abs(a.gridX - p.gridX) + Math.abs(a.gridY - p.gridY)) - (Math.abs(b.gridX - p.gridX) + Math.abs(b.gridY - p.gridY)));
                        for (const n of list) {
                            for (const [dx, dy] of __t.DIRS) {
                                const c = { x: n.gridX - dx, y: n.gridY - dy };
                                if (!__t.open(c.x, c.y) || __t.npcs().some(o => o.gridX === c.x && o.gridY === c.y)) continue;
                                if (!__t.at(c.x, c.y)) __t.place(rm.currentRoom, c.x, c.y);
                                window.__npc = n; window.__npcMoved = false; __t.arm();
                                return { name: n.name, lines: n.dialogue.length, c, dx, dy, npc: { x: n.gridX, y: n.gridY }, onDate: gameDate() };
                            }
                        }
                        return null;
                    });
                    need(plan, { nobodyToTalkTo: await page.evaluate('({ pos: __t.pos(), npcs: __t.npcs().map(n => [n.name, n.gridX, n.gridY, (n.dialogue || []).length]) })'), date });
                    const opened = await press(page, keyFor(plan.dx, plan.dy),
                        `(n => { const open = __t.s.dialogueManager.isVisible(); if (!open && (n.isMoving || n.gridX !== ${plan.npc.x} || n.gridY !== ${plan.npc.y})) window.__npcMoved = true; return open; })(window.__npc)`, 900);
                    if (opened) {
                        // the bump itself opens the dialogue, not a second of leaning on them
                        const lag = await page.evaluate('__t.lagFrames()');
                        need(lag !== null && lag <= 2, { dialogueOpenedFramesAfterTheBump: lag, plan });
                        return plan;
                    }
                    const why = await page.evaluate('({ npcMoved: window.__npcMoved, npc: [window.__npc.gridX, window.__npc.gridY, window.__npc.isMoving], pos: __t.pos() })');
                    need(why.npcMoved, { bumpedSomebodyStandingStillAndNothingOpened: why, plan });
                    await idle(page);   // they wandered off as we arrived: go again
                }
                return null;
            };
            const talk = await talkTo();
            need(talk, 'bumping an NPC never opened dialogue in 4 tries on ' + date);
            const dlg = () => page.evaluate(() => {
                const d = __t.s.dialogueManager;
                return { open: d.isVisible(), who: d.currentNPC && d.currentNPC.name, at: d.currentDialogueIndex + ':' + d.currentPage,
                    text: d.dialogueText.text, name: d.npcNameText.text, shown: d.dialogueText.visible && d.panel.visible, pos: __t.pos() };
            });
            const d0 = await dlg();
            need(d0.open && d0.who === talk.name && d0.shown && d0.text.trim().length > 0 && d0.name.includes(talk.name), { dialogue: d0, talk });
            need(d0.pos.x === talk.c.x && d0.pos.y === talk.c.y, { playerMoved: d0.pos, talk });
            await page.screenshot({ path: path.join(SHOTS, 'regress_dialogue.png') });
            // SPACE advances (the NPC has two lines or more, so it is still open), a movement key does nothing
            await press(page, 'Space', `!__t.s.dialogueManager.isVisible() || (__t.s.dialogueManager.currentDialogueIndex + ':' + __t.s.dialogueManager.currentPage) !== ${JSON.stringify(d0.at)}`);
            const d1 = await dlg();
            need(d1.open && d1.at !== d0.at && d1.text !== d0.text && d1.text.trim().length > 0, { spaceDidNotAdvance: d1, was: d0 });
            await hold(page, keyFor(-talk.dx, -talk.dy), 'false', 200);
            const d2 = await dlg();
            need(d2.open && d2.at === d1.at && d2.pos.x === talk.c.x && d2.pos.y === talk.c.y, { movedDuringDialogue: d2 });
            // ENTER advances too, to the end: the last line closes it
            let d = d2, presses = 0;
            while (d.open && presses < 60) {
                await press(page, 'Enter', `!__t.s.dialogueManager.isVisible() || (__t.s.dialogueManager.currentDialogueIndex + ':' + __t.s.dialogueManager.currentPage) !== ${JSON.stringify(d.at)}`);
                const n = await dlg();
                need(!n.open || n.at !== d.at, { enterDidNotAdvance: n });
                d = n; presses++;
            }
            need(!d.open && presses >= 1, { neverClosed: d, presses });
            // and ESC closes it from the first line, without opening the menu
            need(await talkTo(), 'could not talk to anybody a second time');
            need(await press(page, 'Escape', '!__t.s.dialogueManager.isVisible()'), 'ESC did not close the dialogue');
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r)))));
            need((await page.evaluate('__t.overlays()')).length === 0, { afterEsc: await page.evaluate('__t.overlays()') });
        });

        // 4b --------------------------------------------------------------- the same seam with ?stitch=0
        await cleanly('seam-unstitched', async () => {
            const seam = shared.seam;
            need(seam, 'needs seam-stitched');
            await boot(page, url(`${QUIET}&stitch=0`));
            const st0 = await page.evaluate((m) => {
                const { rm } = __t;
                const cities = Object.keys(rm.cities).length;
                const placed = __t.place(m.A, m.n.x, m.n.y);
                const t = __t.room().transporters.find(t => t.gridX === m.n.x + m.dx && t.gridY === m.n.y + m.dy);
                return { cities, placed, open: __t.open(m.n.x, m.n.y), quiet: __t.quiet(m.n.x, m.n.y, 1), t, hud: __t.hud(), nameA: __t.roomName(m.A), nameB: __t.roomName(m.B) };
            }, seam);
            need(st0.cities === 0 && st0.placed.room === seam.A && st0.placed.district === seam.A, { stillStitched: st0 });
            need(st0.open && st0.t && st0.t.targetRoom === seam.B, { seamTransporterMissing: st0, seam });
            need(st0.hud.room.includes(st0.nameA), { hud: st0.hud.room, expected: st0.nameA });
            await idle(page);
            await step(page, seam.dx, seam.dy);
            const st = await page.evaluate('({ pos: __t.pos(), hud: __t.hud(), sw: __t.rm.__sw, fade: __t.rm.__fade, free: __t.free(__t.s.player.gridX, __t.s.player.gridY), screen: __t.onScreen(), tiles: __t.rm.liveTiles.size })');
            need(st.pos.room === seam.B && st.pos.x === seam.target.x && st.pos.y === seam.target.y, { didNotArrive: st.pos, seam });
            need(st.sw === 1 && st.fade === 1, { noFadeBetweenRooms: st });
            need(st.hud.room.includes(st0.nameB) && st.free && st.screen.inView && st.screen.visible && st.tiles > 0, { arrived: st, expected: st0.nameB });
        });

        // 11 --------------------------------------------------------------- night
        await cleanly('night', async () => {
            await boot(page, url(`${QUIET}&tod=night`));
            await until(page, '__t.s.cameras.main.worldView.contains(__t.s.player.sprite.x, __t.s.player.sprite.y)', 2000);
            const st = await page.evaluate(() => {
                const { s, rm } = __t, dn = s.dayNight, g = dn.grade, p = s.player;
                const day = DayNight.GRADES.day, night = DayNight.GRADES.night;
                return { period: dn.period(), graded: g.visible, alpha: g.fillAlpha, color: g.fillColor, night, day: day || null,
                    interior: !!(s.config.rooms[rm.currentRoom] || {}).interior, glows: dn.glows.length, lights: !!night.lights,
                    screen: __t.onScreen(), depth: [p.sprite.depth, g.depth], hud: __t.hud(), free: __t.free(p.gridX, p.gridY), pos: __t.pos(), way: __t.wayOut() };
            });
            need(st.period === 'night' && !st.interior && st.graded && st.color === st.night.color && st.alpha === st.night.alpha, { notNight: st });
            need(!st.lights || st.glows > 0, { noLampGlows: st.glows });
            need(st.screen.visible && st.screen.inView && st.screen.inWindow && st.free && st.hud.shown, { player: st.screen, pos: st.pos });
            await page.screenshot({ path: path.join(SHOTS, 'regress_night.png') });
            // and the night world still plays: one real step
            need(st.way, { nowhereToStep: st.pos });
            await step(page, st.way.dx, st.way.dy);
            const moved = await page.evaluate('__t.pos()');
            need(moved.x === st.pos.x + st.way.dx && moved.y === st.pos.y + st.way.dy, { didNotStep: moved, from: st.pos });
        });
    });
}

// ------------------------------------------------------------------ the first-time player

async function firstTime() {
    await profile('first-time', { fresh: true }, async ({ page, url, errors }) => {
        await check('first-time-title-creator-intro', async () => {
            await boot(page, url(''));
            need(await until(page, '__t.s.titleScreen.isVisible()', 3000), { noTitleScreen: await page.evaluate('__t.overlays()') });
            const t0 = await page.evaluate('({ overlays: __t.overlays(), pos: __t.pos(), stored: Object.keys(localStorage).filter(k => /seen/.test(k)), cast: __t.s.titleScreen.cast().length })');
            need(t0.overlays.join() === 'title' && t0.cast > 0, { title: t0 });
            await page.screenshot({ path: path.join(SHOTS, 'regress_title.png') });
            // a movement key does not start the game or move the player under the title
            await hold(page, 'ArrowDown', 'false', 200);
            const t1 = await page.evaluate('({ overlays: __t.overlays(), pos: __t.pos() })');
            need(t1.overlays.join() === 'title' && t1.pos.x === t0.pos.x && t1.pos.y === t0.pos.y, { titleLeaked: t1 });

            need(await press(page, 'Space', '!__t.s.titleScreen.isVisible()'), 'SPACE did not start the game from the title');
            need(await until(page, '__t.s.characterCreator.isVisible()', 2000), { noCreator: await page.evaluate('__t.overlays()') });
            const c0 = await page.evaluate('({ overlays: __t.overlays(), row: __t.s.characterCreator.selectedRow, rows: __t.s.characterCreator.rowDefs.length, look: JSON.stringify([__t.s.characterCreator.data.parts, __t.s.characterCreator.data.colors]), sprite: __t.s.player.baseSpriteKey })');
            need(c0.overlays.join() === 'creator' && c0.rows >= 3, { creator: c0 });
            // up/down pick a row, left/right change the look
            need(await press(page, 'ArrowDown', `__t.s.characterCreator.selectedRow !== ${c0.row}`), 'DOWN did not move the creator row');
            await press(page, 'ArrowRight', `JSON.stringify([__t.s.characterCreator.data.parts, __t.s.characterCreator.data.colors]) !== ${JSON.stringify(c0.look)}`);
            const look = await page.evaluate('JSON.stringify([__t.s.characterCreator.data.parts, __t.s.characterCreator.data.colors])');
            need(look !== c0.look, { rightDidNotChangeTheLook: look });
            await page.screenshot({ path: path.join(SHOTS, 'regress_creator.png') });
            need(await press(page, 'Enter', '!__t.s.characterCreator.isVisible()'), 'ENTER did not confirm the character');
            need(await until(page, '__t.s.intro.isVisible()', 2000), { noIntro: await page.evaluate('__t.overlays()') });
            const made = await page.evaluate('({ sprite: __t.s.player.baseSpriteKey, saved: !!localStorage.getItem("gamev2_character"), overlays: __t.overlays(), pages: __t.s.intro.pages.length, page: __t.s.intro.page })');
            need(made.saved && made.sprite !== c0.sprite && made.overlays.join() === 'intro' && made.pages >= 2 && made.page === 0, { afterCreator: made, was: c0.sprite });
            // turn every page with a real key (SPACE and ENTER take turns); the last one closes it
            for (let i = 0; i < made.pages; i++) {
                const last = i === made.pages - 1;
                if (i === 1) await page.screenshot({ path: path.join(SHOTS, 'regress_intro.png') });
                const texts = await page.evaluate('__t.s.intro.objs.filter(o => o.type === "Text" && o.visible && o.text.trim()).length');
                need(texts > 0, { emptyIntroPage: i });
                const ok = await press(page, i % 2 ? 'Enter' : 'Space', last ? '!__t.s.intro.isVisible()' : `__t.s.intro.page === ${i + 1}`);
                need(ok, { introStuckOnPage: i, state: await page.evaluate('({ page: __t.s.intro.page, overlays: __t.overlays() })') });
            }
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r)))));
            const w = await page.evaluate('({ overlays: __t.overlays(), pos: __t.pos(), seen: localStorage.getItem(Intro.SEEN_KEY), hud: __t.hud(), screen: __t.onScreen(), way: __t.wayOut(), free: __t.free(__t.s.player.gridX, __t.s.player.gridY) })');
            need(w.overlays.length === 0 && w.seen === '1', { notInTheWorld: w });
            need(w.pos.x === t0.pos.x && w.pos.y === t0.pos.y && w.pos.room === t0.pos.room, { movedUnderTheOverlays: w.pos, started: t0.pos });
            need(w.hud.shown && w.screen.visible && w.screen.inView && w.free, { world: w });
            need(w.way, { nowhereToStep: w.pos });
            await step(page, w.way.dx, w.way.dy);
            const moved = await page.evaluate('__t.pos()');
            need(moved.x === w.pos.x + w.way.dx && moved.y === w.pos.y + w.way.dy, { cannotWalkAfterIntro: moved, from: w.pos });
            // and the next visit goes straight to the world after the title
            await boot(page, url(''));
            need(await until(page, '__t.s.titleScreen.isVisible()', 3000), 'no title screen on the second visit');
            need(await press(page, 'Enter', '!__t.s.titleScreen.isVisible()'), 'ENTER did not start the game from the title');
            await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
            const again = await page.evaluate('({ overlays: __t.overlays(), sprite: __t.s.player.baseSpriteKey })');
            need(again.overlays.length === 0 && again.sprite === made.sprite, { secondVisit: again, made: made.sprite });
            need(errors.length === 0, { errors });
        });
    });
}

// ------------------------------------------------------------------ trips, with the clock stubbed

function tripDates(trips) {
    // the latest trip: a day inside it, and a day in its lead-in (it opens `lead` days early, default 14)
    const trip = trips.slice().sort((a, b) => (a.start < b.start ? -1 : 1)).pop();
    const add = (iso, n) => { const d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
    const span = Math.round((new Date(trip.end) - new Date(trip.start)) / 864e5);
    const lead = trip.lead != null ? trip.lead : 14;
    return { trip, during: add(trip.start, Math.min(2, span)), before: add(trip.start, -Math.min(8, lead)) };
}

async function trips(shared) {
    if (!shared.trips || !shared.trips.length) {
        for (const name of ['trip-in-progress', 'trip-lead-in']) await check(name, async () => need(false, 'config has no trips (or boot-returning never read them)'));
        return;
    }
    const { trip, during, before } = tripDates(shared.trips);

    await profile('trip-during', { now: `${during}T12:00:00`, fresh: true }, async ({ page, url, errors }) => {
        await check('trip-in-progress', async () => {
            await boot(page, url(QUIET));
            const st = await page.evaluate((id) => {
                const { s, rm } = __t, trips = Trips.of(s.config), date = gameDate(), p = s.player;
                const t = Trips.forDate(trips, date), stay = Trips.stayFor(t, date) || t.home;
                const played = Trips.baseOf(p.baseSpriteKey);
                const groups = Trips.membersByRoom(s.config, date, { played });
                const here = groups.find(g => g.room === rm.currentDistrict());
                const live = __t.npcs().filter(n => t.members.includes(Trips.baseOf(n.baseSpriteKey)));
                const gap = live.map(n => Math.max(Math.abs(n.gridX - p.gridX), Math.abs(n.gridY - p.gridY)));
                return { date, bare: formatGameDate(date), trip: t.id, name: t.name, during: Trips.during(t, date), base: stay.room, pos: __t.pos(), hud: __t.hud(),
                    newPlayer: s.newPlayer, overlays: __t.overlays(), members: t.members.length,
                    groups: groups.map(g => [g.room, g.members.length]), here: here ? here.members.map(m => m.name).sort() : null,
                    live: live.map(n => n.name).sort(), nearest: Math.min(...gap), near: Trips.NEAR,
                    free: __t.free(p.gridX, p.gridY), onNpc: live.some(n => n.gridX === p.gridX && n.gridY === p.gridY), want: id };
            }, trip.id);
            need(st.date === during && st.trip === trip.id && st.during, { clockNotStubbedOrWrongTrip: st, during });
            need(st.newPlayer && st.overlays.includes('creator'), { notANewPlayer: st.overlays, newPlayer: st.newPlayer });
            need(st.pos.district === st.base, { startedIn: st.pos, base: st.base });
            need(st.here && st.here.length >= 1 && st.groups.every(g => g[1] <= st.here.length), { notWithTheLargestGroup: st.groups, pos: st.pos });
            need(st.live.length === st.here.length && st.here.every(n => st.live.includes(n)), { castInTheRoom: st.live, shouldBe: st.here });
            need(st.nearest >= 1 && st.nearest <= st.near && st.free && !st.onNpc, { notBesideTheCast: st.nearest, near: st.near, pos: st.pos });
            // a trip's own day shows the bare date: the HUD never names the trip (issue #163)
            need(st.hud.date === st.bare && !st.hud.date.includes(st.name), { hudDate: st.hud.date, shouldBeExactly: st.bare, mustNotName: st.name });
            // leave the creator with a real ESC: the world is there behind it
            need(await press(page, 'Escape', '!__t.s.characterCreator.isVisible()'), 'ESC did not close the creator');
            await page.screenshot({ path: path.join(SHOTS, 'regress_trip.png') });
            need(errors.length === 0, { errors });
        });
    });

    await profile('trip-before', { now: `${before}T12:00:00` }, async ({ page, url, errors }) => {
        await check('trip-lead-in', async () => {
            // The countdown belongs to the GAME date. With only the clock on a lead-in day a visitor is
            // still shown a day of the trip before (until somebody posts from the road), so the day is
            // asked for by name as well; the clock-only load must at least boot into a playable world.
            await boot(page, url(QUIET));
            const plain = await page.evaluate('({ date: gameDate(), pos: __t.pos(), free: __t.free(__t.s.player.gridX, __t.s.player.gridY), hud: __t.hud(), overlays: __t.overlays(), npcs: __t.npcs().length })');
            need(plain.free && plain.hud.shown && plain.overlays.length === 0 && plain.hud.date.includes(await page.evaluate('formatGameDate(gameDate())')), { clockOnlyBoot: plain });
            if (plain.date !== before) await boot(page, url(`${QUIET}&date=${before}`));
            const st = await page.evaluate(() => {
                const { s, rm } = __t, trips = Trips.of(s.config), date = gameDate(), p = s.player;
                const lead = Trips.leadIn(trips, date);
                if (!lead) return { date, lead: null };
                const t = lead.trip, base = (lead.stay || t.home).room;
                const groups = Trips.membersByRoom(s.config, date, { played: Trips.baseOf(p.baseSpriteKey) });
                const inBase = rm.npcsIn(base).filter(({ npc }) => t.members.includes(Trips.baseOf(npc.baseSpriteKey))).map(({ npc }) => npc.name);
                const today = new Date();
                return { date, today: today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0'),
                    lead: { trip: t.id, name: t.name, days: lead.days }, base, groups: groups.map(g => [g.room, g.members.length]),
                    labels: [Trips.inDays(lead.days), `in ${lead.days}d`], inBase, members: t.members.length,
                    pos: __t.pos(), hud: __t.hud(), overlays: __t.overlays(), free: __t.free(p.gridX, p.gridY) };
            });
            need(st.lead && st.date === before && st.today === before, { notALeadInDay: st, before });
            need(st.lead.trip === trip.id && st.lead.days >= 1, { lead: st.lead });
            need(st.hud.date.includes(st.lead.name) && st.labels.some(l => st.hud.date.includes(`${st.lead.name} ${l} · `)), { hudDoesNotCountDown: st.hud.date, want: st.labels });
            const expected = st.groups.filter(g => g[0] === st.base).reduce((n, g) => n + g[1], 0);
            need(st.inBase.length === expected && st.inBase.length < st.members, { castAtTheBaseBeforeTheTrip: st.inBase, data: st.groups });
            // nobody has posted from the road: the player waits at the base the trip will arrive at
            if (!st.groups.length) need(st.pos.district === st.base, { nobodyAnywhereButStartedIn: st.pos, base: st.base });
            need(st.overlays.length === 0 && st.free, { world: st });
            await page.screenshot({ path: path.join(SHOTS, 'regress_leadin.png') });
            need(errors.length === 0, { errors });
        });
    });
}

// ------------------------------------------------------------------ phones

async function phones() {
    await profile('phone-landscape', { touch: true, mobile: true, width: 844, height: 390 }, async ({ page, context, url, errors }) => {
        await check('phone-landscape-touch', async () => {
            await boot(page, url(`${QUIET}&touch=1`));
            await until(page, '__t.s.cameras.main.worldView.contains(__t.s.player.sprite.x, __t.s.player.sprite.y)', 2000);
            const st = await page.evaluate(() => {
                const { s } = __t, r = window.game.canvas.getBoundingClientRect();
                const pad = document.querySelector('#touch-controls .tc-padzone'), pr = pad && pad.getBoundingClientRect();
                const arrows = pad ? [...pad.querySelectorAll('.tc-pad')].map(b => { const q = b.getBoundingClientRect(); return { label: b.textContent, x: q.left + q.width / 2, y: q.top + q.height / 2 }; }) : [];
                const a = document.querySelector('#touch-controls .tc-a'), ar = a && a.getBoundingClientRect();
                return { win: [window.innerWidth, window.innerHeight], doc: document.documentElement.scrollWidth,
                    canvas: [r.left, r.top, r.right, r.bottom].map(v => Math.round(v * 10) / 10),
                    controls: s.touchControls.enabled, pad: pr && [pr.left, pr.top, pr.right, pr.bottom], a: ar && [ar.left, ar.top, ar.right, ar.bottom], arrows,
                    hud: __t.hud(), bar: s.hudBarHeight, row: UI.HUD_HEIGHT, zoom: [s.cameras.main.zoom, s.uiScale.hudZoom], screen: __t.onScreen(), pos: __t.pos(),
                    menuRight: (s.menuButton.x) * s.uiScale.hudZoom, wallet: (s.hudMoneyText.x + s.hudMoneyText.width), menuLeft: s.menuButton.x - s.menuButton.width,
                    view: s.cameras.main.width };
            });
            need(st.win[0] === 844 && st.win[1] === 390 && st.doc <= 844, { layoutViewportWidened: st.win, doc: st.doc });
            need(st.canvas[0] >= -0.5 && st.canvas[1] >= -0.5 && st.canvas[2] <= st.win[0] + 0.5 && st.canvas[3] <= st.win[1] + 0.5 && st.canvas[3] - st.canvas[1] >= st.win[1] - 1, { canvasDoesNotFit: st.canvas, win: st.win });
            need(st.controls && st.pad && st.a && st.arrows.length === 4, { noTouchControls: st });
            const inWin = (b) => b[0] >= 0 && b[1] >= 0 && b[2] <= st.win[0] && b[3] <= st.win[1];
            need(inWin(st.pad) && inWin(st.a), { controlsOffScreen: [st.pad, st.a], win: st.win });
            need(st.hud.oneRow && st.bar === st.row && st.hud.shown, { hudNotOneRow: st.hud, bar: st.bar, row: st.row });
            need(st.wallet <= st.menuLeft, { walletUnderMenuButton: [st.wallet, st.menuLeft] });
            need(st.screen.visible && st.screen.inView && st.screen.inWindow, { playerOffScreen: st.screen });
            await page.screenshot({ path: path.join(SHOTS, 'regress_phone.png') });

            // a real, held touch on the d-pad arrow that points somewhere the player can go
            const way = await page.evaluate('__t.wayOut()');
            need(way, { nowhereToStep: st.pos });
            const glyph = { '1,0': '▶', '-1,0': '◀', '0,1': '▼', '0,-1': '▲' }[`${way.dx},${way.dy}`];
            const arrow = st.arrows.find(a => a.label === glyph);
            need(arrow, { noArrow: glyph, arrows: st.arrows });
            const cdp = await context.newCDPSession(page);
            await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: Math.round(arrow.x), y: Math.round(arrow.y) }] });
            const going = await until(page, '__t.s.player.isMoving', 2000);
            const held = await page.evaluate('({ state: Object.assign({}, __t.s.touchControls.state), pressed: [...document.querySelectorAll("#touch-controls .tc-pressed")].map(b => b.textContent) })');
            await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
            await idle(page);
            const moved = await page.evaluate('({ pos: __t.pos(), state: Object.assign({}, __t.s.touchControls.state), overlays: __t.overlays(), controls: __t.s.touchControls.enabled })');
            const steps = (moved.pos.x - st.pos.x) * way.dx + (moved.pos.y - st.pos.y) * way.dy;
            need(going && held.pressed.join() === glyph, { dpadDidNotTakeTheTouch: held, glyph });
            need(steps >= 1 && steps <= 2 && (way.dx ? moved.pos.y === st.pos.y : moved.pos.x === st.pos.x), { dpadDidNotMoveThePlayer: moved.pos, from: st.pos, way });
            need(!Object.values(moved.state).some(Boolean) && moved.overlays.length === 0 && moved.controls, { afterTouch: moved });
            // the A / B buttons are real touches too: B opens the menu and closes it again
            const b = await page.evaluate('(r => ({ x: r.left + r.width / 2, y: r.top + r.height / 2 }))(document.querySelector("#touch-controls .tc-b").getBoundingClientRect())');
            await page.touchscreen.tap(b.x, b.y);
            need(await until(page, '__t.s.menuManager.isVisible()', 1500), 'a tap on B did not open the menu');
            await page.waitForTimeout(150);   // B's key-up is sent 90ms after a quick tap
            await page.touchscreen.tap(b.x, b.y);
            need(await until(page, '!__t.s.menuManager.isVisible()', 1500), 'a second tap on B did not close the menu');
            need(errors.length === 0, { errors });
        });
    });

    await profile('phone-portrait', { touch: true, mobile: true, width: 390, height: 844 }, async ({ page, url, errors }) => {
        await check('phone-portrait-boot', async () => {
            await boot(page, url(`${QUIET}&touch=1`));
            await until(page, '__t.s.cameras.main.worldView.contains(__t.s.player.sprite.x, __t.s.player.sprite.y)', 2000);
            const st = await page.evaluate(() => {
                const { s } = __t, r = window.game.canvas.getBoundingClientRect(), p = s.player;
                const pad = document.querySelector('#touch-controls .tc-padzone'), pr = pad && pad.getBoundingClientRect();
                return { win: [window.innerWidth, window.innerHeight], doc: document.documentElement.scrollWidth,
                    canvas: [r.left, r.top, r.right, r.bottom].map(Math.round), controls: s.touchControls.enabled,
                    pad: pr && [pr.left, pr.top, pr.right, pr.bottom].map(Math.round), screen: __t.onScreen(), hud: __t.hud(),
                    free: __t.free(p.gridX, p.gridY), pos: __t.pos(), overlays: __t.overlays(),
                    hudRight: (s.menuButton.x) * s.uiScale.hudZoom, view: s.cameras.main.width, tiles: __t.rm.liveTiles.size };
            });
            need(st.win[0] === 390 && st.win[1] === 844 && st.doc <= 390, { layoutViewportWidened: st.win, doc: st.doc });
            need(st.screen.visible && st.screen.inView && st.screen.inWindow, { playerOffScreen: st.screen, canvas: st.canvas });
            need(st.canvas[1] >= 0 && st.canvas[3] <= st.win[1] && st.canvas[0] <= 0 && st.canvas[2] >= st.win[0], { canvasDoesNotCoverTheWidth: st.canvas, win: st.win });
            need(st.controls && st.pad && st.pad[1] >= st.canvas[3] - 1 && st.pad[3] <= st.win[1] && st.pad[0] >= 0, { controlsNotUnderTheCanvas: st.pad, canvas: st.canvas });
            need(st.screen.cy < st.pad[1], { playerUnderTheControls: st.screen, pad: st.pad });
            need(st.hud.shown && st.free && st.overlays.length === 0 && st.tiles > 0, { world: st });
            await page.screenshot({ path: path.join(SHOTS, 'regress_portrait.png') });
            need(errors.length === 0, { errors });
        });
    });
}

// ------------------------------------------------------------------ run

const summary = () => {
    const passed = results.filter(r => r.ok).length;
    console.log(`${((Date.now() - T0) / 1000).toFixed(1)}s`);
    console.log(`${passed}/${results.length} checks passed`);
    return passed === results.length ? 0 : 1;
};

setTimeout(() => {
    // whatever was in flight (and everything after it) did not run to an answer: that is a failure
    const stuck = [...running], done = results.length;
    for (const name of stuck.length ? stuck : ['deadline']) {
        results.push({ name, ok: false });
        console.log(`FAIL ${name} the suite did not finish within ${DEADLINE_MS / 1000}s (still running: ${stuck.join(', ') || 'nothing'}; ${done} checks had finished)`);
    }
    summary();
    process.exit(1);
}, DEADLINE_MS).unref();

(async () => {
    const shared = {};
    // the long desktop walk-through runs beside the short profiles: two pages at a time, never more
    const side = (async () => { await firstTime(); await phones(); })();
    await desktop(shared);
    await side;
    await trips(shared);

    await check('no-errors', async () => need(allErrors.length === 0, { errors: allErrors.slice(0, 10), count: allErrors.length }));

    process.exit(summary());
})().catch((e) => {
    console.log(`FAIL harness ${String(e && e.stack || e).replace(/\s+/g, ' ').slice(0, 600)}`);
    console.log(`0/${results.length || 1} checks passed`);
    process.exit(1);
});
