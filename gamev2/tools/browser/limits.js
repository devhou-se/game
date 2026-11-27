// How long regress.js may take: the whole run and any one check. Both are there to stop a stalled browser
// hanging the queue, not to judge the game, so a slow machine may stretch them:
//
//   REGRESS_TIME_SCALE=2 PORT=<port> node regress.js     # twice as long for the run and for each check
//
// Nothing else changes: every assertion, and every wait on game state inside a check, is as written.
// No dependencies, so the unit tests can load it without playwright-core.
const DEADLINE_MS = 80000;   // a normal run is ~25s (~30s with the browser busy)
const CHECK_MS = 25000;
const MAX_SCALE = 100;       // a run that needs more than this is not slow, it is stuck

/** { scale, deadlineMs, checkMs } for an environment; throws on a REGRESS_TIME_SCALE that is not a number from 1 to 100. */
function limits(env = process.env) {
    const raw = env.REGRESS_TIME_SCALE;
    let scale = 1;
    if (raw !== undefined && raw !== '') {
        scale = /^\d+(\.\d+)?$/.test(raw) ? Number(raw) : NaN;
        // below 1 would only shorten the limits; a plain number is asked for so a typo cannot pass as one
        if (!(scale >= 1 && scale <= MAX_SCALE)) {
            throw new Error(`REGRESS_TIME_SCALE must be a number from 1 to ${MAX_SCALE} (1 is the usual limits), not ${JSON.stringify(raw)}`);
        }
    }
    return { scale, deadlineMs: Math.round(DEADLINE_MS * scale), checkMs: Math.round(CHECK_MS * scale) };
}

module.exports = { limits, DEADLINE_MS, CHECK_MS, MAX_SCALE };
