/**
 * NpcStates — dated NPC state snapshots.
 *
 * An NPC in config.json may carry a `states` object keyed by ISO date:
 *
 *   "states": {
 *     "2026-06-30": { "dialogue": ["..."] },
 *     "2026-07-02": { "dialogue": ["..."], "gridX": 26, "gridY": 34 }
 *   }
 *
 * At load, the states dated on-or-before the game date are applied to the
 * base NPC in chronological order — each one is an UPDATE overlaying only the
 * fields it names (so a later dialogue change keeps an earlier position
 * change, and anything never named falls back to the base definition).
 * Viewing "2026-07-01" above shows the 06-30 dialogue at the base position.
 *
 * The game date is ?date=YYYY-MM-DD when given (time travel). Otherwise it is
 * today (device local time) while today is inside the trip — the span of the
 * dated content, first state date to last — and, once the trip is over (or
 * before it starts), the trip day that today cycles onto: see
 * defaultGameDate. A state of {"present": false} removes the NPC from that
 * date until a later state sets it back.
 *
 * A state may also carry "photo": <post id> — a blog-post photo imported to
 * assets/photos/<id>.png by tools/blog_to_npc.py, hung in a frame beside the
 * author in the dialogue box. The pipeline writes photo on every placement
 * (null when the post had none) so an older photo never bleeds forward.
 *
 * Likewise "voice": <voice id> — spoken clips for that state's dialogue, one
 * per line at assets/voice/<id>/<line index>.mp3 (tools/post_voice.py, played
 * by src/Voice.js). Clips belong to the exact dialogue they were generated
 * from, so a state that changes the dialogue without naming a voice clears
 * it rather than inheriting clips for lines that are no longer said.
 */
/** Today's real date, device local time, as YYYY-MM-DD. */
function todayIso() {
    const d = new Date();
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

// The days of the trip: every date with dated content, sorted. Set once the
// config has loaded (see setTripDates); empty until then, and for a config
// with no dated content.
let tripDates = [];
// The real date when the config loaded. NPCs are resolved once, at boot, so
// the default game date must not move on at midnight in a session left open
// (the HUD would name a day whose stories are not the ones showing).
let bootToday = null;

/**
 * Tell the date functions which days the trip covers — the sorted
 * contentChangeDates(config). GameScene calls this as soon as config.json is
 * decoded, before anything asks for the game date.
 */
function setTripDates(config) {
    tripDates = [...contentChangeDates(config)].sort();
    bootToday = todayIso();
}

/**
 * The game date when the URL names none (issue #54).
 *
 * During the trip — from the first dated day to the last — that is simply
 * today. Outside it, today would be a date with no connection to the trip
 * (everyone frozen on their last post), so today is mapped onto a trip day
 * instead: count the days since the trip ended and wrap at the number of
 * trip days, so the day after the last day is day one again. Only days that
 * have content are in the cycle, so quiet stretches between posts are
 * skipped. A visitor therefore always lands on a day of the trip, everyone
 * has that day's story, and coming back tomorrow shows the next one.
 *
 * `today` defaults to the real date as it was when the config loaded (the
 * world is resolved once, so the date holds for the session) and `dates` to
 * the loaded trip days; both are parameters so the mapping can be checked
 * without a clock.
 */
function defaultGameDate(today = bootToday || todayIso(), dates = tripDates) {
    if (!dates.length) return today;
    const first = dates[0], last = dates[dates.length - 1];
    if (today >= first && today <= last) return today;
    // whole days since the epoch; UTC so daylight saving never skews a count
    const dayNumber = (iso) => {
        const [y, m, d] = iso.split('-').map(Number);
        return Math.round(Date.UTC(y, m - 1, d) / 86400000);
    };
    const n = dates.length;
    return dates[(((dayNumber(today) - dayNumber(last) - 1) % n) + n) % n];
}

function gameDate() {
    const p = new URLSearchParams(location.search).get('date');
    if (p && /^\d{4}-\d{2}-\d{2}$/.test(p)) return p;
    return defaultGameDate();
}

function resolveNpc(npcConfig, date) {
    if (!npcConfig.states) return npcConfig;
    const merged = Object.assign({}, npcConfig);
    delete merged.states;
    // ISO dates compare correctly as strings
    for (const d of Object.keys(npcConfig.states).sort()) {
        if (d > date) continue;
        const state = npcConfig.states[d];
        Object.assign(merged, state);
        if ('dialogue' in state && !('voice' in state)) merged.voice = null;
    }
    if (merged.present === false) return null;
    return merged;
}

/**
 * Dates on which NPC content changes. The blog pipeline records each accepted
 * post as one or more dated NPC states, so de-duplicating their keys gives the
 * calendar the days that have associated blog content.
 */
function contentChangeDates(config) {
    const dates = new Set();
    for (const room of Object.values((config && config.rooms) || {})) {
        for (const npc of room.npcs || []) {
            for (const date of Object.keys(npc.states || {})) {
                if (/^\d{4}-\d{2}-\d{2}$/.test(date)) dates.add(date);
            }
        }
    }
    return dates;
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-07-02" -> "July 2 2026" (the HUD display format). */
function formatGameDate(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    return `${MONTHS[m - 1]} ${d} ${y}`;
}

/**
 * Navigate to the given game date. The date a clean URL already gives
 * (defaultGameDate) drops the param; any other date — including today's real
 * date once the trip is over — is an explicit choice and goes in ?date=.
 * This reloads, so the comparison uses the real date now, not the boot one.
 */
function setGameDate(iso) {
    const params = new URLSearchParams(location.search);
    if (!iso || iso === defaultGameDate(todayIso())) params.delete('date'); else params.set('date', iso);
    const qs = params.toString();
    // a date hop is an in-game action that happens to reload the page: don't
    // drop the player back on the title screen (one-shot, consumed by
    // TitleScreen.shouldShow on the next load)
    try { sessionStorage.setItem('gamev2_skip_title', '1'); } catch (e) { /* storage blocked */ }
    location.href = location.pathname + (qs ? '?' + qs : '');
}

if (typeof window !== 'undefined') {
    window.gameDate = gameDate;
    window.defaultGameDate = defaultGameDate;
    window.setTripDates = setTripDates;
    window.resolveNpc = resolveNpc;
    window.contentChangeDates = contentChangeDates;
    window.formatGameDate = formatGameDate;
    window.setGameDate = setGameDate;
}
